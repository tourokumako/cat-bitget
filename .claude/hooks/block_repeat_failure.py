#!/usr/bin/env python3
"""block_repeat_failure — 同じ相手で2回続けて失敗したら、見立てを書くまで その相手に手を出させない（2026-10-01 新設）。

まこさん指示（逐語 2026-10-01）＝「確認をしないで、正しい対処方法を確認せずに、思いつきの当てずっぽうで対処し、
あたるまで永遠に適当な対処をし続けることをやめろって言ってんの！！！！」「それでいいから」。
出どころ（外）＝DEV「five hooks」の逐語 "Two strikes on the same target usually means the approach is wrong, not that it
needs another tweak."／RegressionLedger「原因の見立てを2〜3個 書くまで直させない」。

決まり
  相手＝Edit・Write・MultiEdit・NotebookEdit は直すファイル。Bash は走らせる .py・.sh（無ければコマンドの頭の2語）。Agent は "Agent"。
  同じ相手への書き込み・実行が2回続けて失敗した（道具の結果が is_error）ら、その相手への次の操作を止める。
  外す＝2回目の失敗の後に、.claude/state/sessions/<セッション>/diagnosis.md を書く。中身＝「相手: <相手>」の行と、
        「見立て」で始まる行を2つ以上（Write で書けば、この強制は止めない）。
  読むだけの操作（Read・Grep・Glob・読むだけの Bash）は止めない。

使い方: （hook）標準入力に PreToolUse の JSON ／ --replay <日数> 直近の記録に流して数える（何も止めない）
"""
import datetime
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from require_check_after_failure import ACT_TOOLS, is_read  # 読むだけの判定を同じものにする
from transcript_rows import rows                            # 記録は会話の本物の行だけを読む（2026-10-15）

ROOT = pathlib.Path(__file__).resolve().parents[2]
SESS = ROOT / ".claude/state/sessions"
PY = re.compile(r"[\w./~-]+\.(?:py|sh)\b")


def target_of(name, inp) -> str:
    inp = inp or {}
    if name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        return str(inp.get("file_path") or inp.get("notebook_path") or "")
    if name == "Bash":
        cmd = str(inp.get("command", ""))
        m = PY.findall(re.sub(r"'[^']*'|\"[^\"]*\"", "", cmd))
        if m:
            return pathlib.Path(m[0]).name
        w = [x for x in cmd.split() if not re.match(r"^\w+=", x) and x not in ("cd", "&&")]
        return " ".join(w[:2])
    return name


def load(path: pathlib.Path):
    """戻り＝[(id, 道具, 入力, 結果が失敗か, 結果の時刻)]（結果の無い呼び出しは失敗でない扱い）。"""
    calls, res = [], {}
    # ★2026-10-15（181回目）＝記録は共通の rows() で読む（会話の本物の行だけ・同じ行は1回）。直す前は行の種類を見ず、
    #   api-request-blob の行（API に送った中身の控え・この日から記録に入った）の中の呼び出しも数え、1回の失敗を2回と数えた
    for o in rows(path):
        c = (o.get("message") or {}).get("content")
        if not isinstance(c, list):
            continue
        for b in c:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                calls.append([b.get("id"), b.get("name"), b.get("input")])
            elif b.get("type") == "tool_result":
                res[b.get("tool_use_id")] = (bool(b.get("is_error")), o.get("timestamp"))
    return [(i, n, x, res.get(i, (False, None))[0], res.get(i, (False, None))[1]) for i, n, x in calls]


def two_strikes(rows, tgt):
    """その相手への最後の2回の操作が両方 失敗なら、2回目の時刻を返す。違えば None。"""
    hits = [r for r in rows if r[1] in ACT_TOOLS and not is_read(r[1], r[2]) and target_of(r[1], r[2]) == tgt]
    if len(hits) >= 2 and hits[-1][3] and hits[-2][3]:
        return hits[-1][4] or ""
    return None


def diagnosed(session: str, tgt: str, since: str) -> bool:
    p = SESS / session / "diagnosis.md"
    if not p.exists():
        return False
    try:
        t = datetime.datetime.fromisoformat(since.replace("Z", "+00:00")).timestamp() if since else 0
    except Exception:
        t = 0
    if p.stat().st_mtime < t:
        return False
    s = p.read_text(encoding="utf-8")
    return (f"相手: {tgt}" in s) and sum(1 for ln in s.splitlines() if ln.strip().startswith("見立て")) >= 2


def hook() -> int:
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    name, inp = d.get("tool_name"), d.get("tool_input") or {}
    if name not in ACT_TOOLS or is_read(name, inp):
        return 0
    if name == "Write" and str(inp.get("file_path", "")).endswith("/diagnosis.md"):
        return 0
    tp = d.get("transcript_path")
    if not tp or not pathlib.Path(tp).exists():
        return 0
    tgt = target_of(name, inp)
    since = two_strikes(load(pathlib.Path(tp)), tgt)
    if since is None:
        return 0
    sid = str(d.get("session_id") or pathlib.Path(tp).stem)
    if diagnosed(sid, tgt, since):
        return 0
    print(f"🔒 [同じ相手で2回 失敗] 「{tgt}」への操作が2回続けて失敗しています。3回目を当てずっぽうで打たないでください。\n"
          f"   先に原因を調べ、.claude/state/sessions/{sid}/diagnosis.md に「相手: {tgt}」の行と、"
          "「見立て」で始まる行を2つ以上 書いてください（書いた後に、この相手へ手を出せます）。\n"
          "   まこさん指示 2026-10-01「思いつきの当てずっぽうで対処し、あたるまで永遠に適当な対処をし続けることをやめろ」",
          file=sys.stderr)
    return 2


def replay(days: int) -> int:
    proj = pathlib.Path.home() / ".claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget"
    cut = time.time() - days * 86400
    files = [p for p in proj.glob("*.jsonl") if p.stat().st_mtime >= cut]
    n_act = n_block = n_block_fail = n_read = 0
    for p in files:
        rows = load(p)
        cleared = set()                                  # 本物では1回止まって見立てを書けば外れる＝相手ごとに1回だけ数える
        for k, (cid, nm, inp, fail, _ts) in enumerate(rows):
            if is_read(nm, inp):
                n_read += 1
                continue
            if nm not in ACT_TOOLS:
                continue
            n_act += 1
            tgt = target_of(nm, inp)
            since = two_strikes(rows[:k], tgt)
            if since is not None and (tgt, since) not in cleared:
                cleared.add((tgt, since))
                n_block += 1
                n_block_fail += int(fail)
    print(f"記録 {len(files)} 本（直近 {days} 日）／読む操作 {n_read} 回（止めない）／書き込み・実行 {n_act} 回")
    print(f"この強制が止める回数 {n_block} 回 ／ そのうち、記録の上で3回目もまた失敗していた回数 {n_block_fail} 回")
    return 0


if __name__ == "__main__":
    if "--replay" in sys.argv:
        sys.exit(replay(int(sys.argv[sys.argv.index("--replay") + 1])))
    sys.exit(hook())
