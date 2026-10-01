#!/usr/bin/env python3
"""block_repeat_kind — 同じ種類の失敗を同じセッションで2回 起こしたら、決まりを書き出すまで先に進ませない（2026-10-01 新設）。

まこさん指示（逐語 2026-10-01）＝「確認せずに動けば一発で修正できるのに、その確認をせずに、適当に当てずっぽうな対処を
当たるまで続けることをやめろ」「以下ができる状態になるまでこのセッションは終了しない」。
根拠の実測（2026-10-01・直近7日の記録41本）＝書き込み・実行の失敗 1,043回のうち 710回が、同じセッションで既に起きた
種類の失敗の2回目以降（一番多いのは土台ゲートの止め 186回）。止める回数 159回で、3回目以降 551回を防げる見込み。

決まり
  種類＝hook の止め（hook のファイル名＋止めの文の【】や［］の見出し）／Edit の失敗（直す前の文字が無い ほか）／例外の名前。
       終了コードだけの失敗・種類の分からない失敗・この強制と block_repeat_failure 自身の止めは数えない。
  同じ種類が同じセッションで2回 起きたら、書き込み・実行（読む操作でないもの）を全部 止める。
  外す＝.claude/state/sessions/<セッション>/lessons.md に「種類: <種類>」の行と「次から確かめること:」で始まる行を書く
       （その種類の最後の失敗より後に書くこと＝決まりを書いた後にまた同じ種類が起きたら、書き直すまで もう一度 止める）。
  止めないもの＝読む操作／セッションの置き場・worklog・計画・memory への書き込み。

使い方: （hook）標準入力に PreToolUse の JSON ／ --replay <日数> 直近の記録に流して数える（何も止めない）
"""
import collections
import datetime
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from require_check_after_failure import ACT_TOOLS, is_read  # 読むだけの判定を同じものにする

ROOT = pathlib.Path(__file__).resolve().parents[2]
SESS = ROOT / ".claude/state/sessions"
FREE = ("/.claude/state/sessions/", "session_worklog_", "/.claude/plans/", "/memory/", "chat_draft.md")
# ★2026-10-01（143回目）＝止めの文に出る名前は .sh（登録は block_repeat_kind.sh）。.py だけだと自分の止めを数えて止め続けた。
SELF = ("block_repeat_kind.py", "block_repeat_failure.py", "block_repeat_kind.sh", "block_repeat_failure.sh")
# ★2026-10-01（143回目・まこさん「直せ」）＝名前の後ろの引数（例「require_confirm_before_act.sh pre」）を読み飛ばす。
#   直す前は名前の直後に「]」が来る形しか拾わず、確認の強制の止めを種類として数えていなかった。
HOOK = re.compile(r"hook (?:error|feedback)[^\[]*\[(?:bash |python3 )?([^\]\s]+)(?: [^\]]*)?\]:\s*([^\n]*)")
TAG = re.compile(r"[【\[]([^】\]]{1,30})[】\]]")
STOP_SEG = re.compile(r"\[(?:bash |python3 )?[^\]\s]+(?: [^\]]*)?\]:[^\n]*")   # Stop hook の差し戻しの1件（[hook の名前]: 止めの文）


def kind_of(text: str):
    m = HOOK.search(text)
    if m:
        name = pathlib.Path(m.group(1)).name
        if name in SELF:
            return None
        t = TAG.search(m.group(2))
        return f"{name} {t.group(0) if t else ''}".strip()
    for k in ("String to replace not found", "File has not been read", "modified since"):
        if k in text:
            return "Edit: " + k
    if re.search(r"Found \d+ matches", text):
        return "Edit: Found N matches"
    e = re.findall(r"\b(\w+(?:Error|Exception))\b", text)
    if e and "Traceback" in text:
        return "例外: " + e[-1]
    return None


def load(path: pathlib.Path):
    """戻り＝[(道具, 入力, 失敗の文 or None, 結果の時刻)]。"""
    calls, res, stops = [], {}, []
    for line in path.open(encoding="utf-8", errors="replace"):
        try:
            o = json.loads(line)
        except Exception:
            continue
        c = (o.get("message") or {}).get("content")
        # ★2026-10-01（143回目・まこさん「ちゃんと改善しろ」）＝Stop hook の差し戻しも hook ごとに失敗として数える。
        #   差し戻しは記録に「まこさんの発言」の形（本文が「Stop hook feedback:」で始まる文字列）で残るので、
        #   直す前は道具の失敗の結果だけを読み、同じ差し戻しを何回 受けても止めなかった。
        if o.get("type") == "user":
            txt = c if isinstance(c, str) else " ".join(x for x in (c or []) if isinstance(x, str))
            if "Stop hook feedback" in txt:
                for seg in STOP_SEG.findall(txt):
                    stops.append(("Stop", {}, "Stop hook feedback: " + seg, o.get("timestamp")))
        if not isinstance(c, list):
            continue
        for b in c:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                calls.append((b.get("id"), b.get("name"), b.get("input") or {}))
            elif b.get("type") == "tool_result" and b.get("is_error"):
                t = b.get("content")
                if isinstance(t, list):
                    t = " ".join(x.get("text", "") for x in t if isinstance(x, dict))
                res[b.get("tool_use_id")] = (str(t or ""), o.get("timestamp"))
    return [(n, x, res.get(i, (None, None))[0], res.get(i, (None, None))[1]) for i, n, x in calls] + stops


def open_repeats(rows):
    """2回 起きた種類と、その2回目の時刻。戻り＝{種類: 時刻}。"""
    n, when = collections.Counter(), {}
    for nm, inp, err, ts in rows:
        if err is None or (nm != "Stop" and (nm not in ACT_TOOLS or is_read(nm, inp))):
            continue
        k = kind_of(err)
        if not k:
            continue
        n[k] += 1
        if n[k] >= 2:
            # ★2回目だけでなく、3回目以降も時刻を上書きする（2026-10-01・まこさん「直す」）＝決まりを書いた後に
            #   また同じ種類が起きたら、決まりの書き直し（lessons.md の更新）までもう一度 止める
            when[k] = ts or ""
    return when


def _ts(s: str) -> float:
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def unlearned(session: str, when: dict) -> list:
    p = SESS / session / "lessons.md"
    txt = p.read_text(encoding="utf-8") if p.exists() else ""
    mt = p.stat().st_mtime if p.exists() else 0
    lines = txt.splitlines()
    ok = any(ln.strip().startswith("次から確かめること") for ln in lines)
    return [k for k, ts in when.items() if not (ok and f"種類: {k}" in txt and mt >= _ts(ts))]


def free_write(name, inp) -> bool:
    p = str((inp or {}).get("file_path") or "")
    return name in ("Write", "Edit", "MultiEdit") and any(k in p for k in FREE)


def hook() -> int:
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    name, inp = d.get("tool_name"), d.get("tool_input") or {}
    if name not in ACT_TOOLS or is_read(name, inp) or free_write(name, inp):
        return 0
    tp = d.get("transcript_path")
    if not tp or not pathlib.Path(tp).exists():
        return 0
    sid = str(d.get("session_id") or pathlib.Path(tp).stem)
    bad = unlearned(sid, open_repeats(load(pathlib.Path(tp))))
    if not bad:
        return 0
    lst = "\n".join(f"     種類: {k}" for k in bad)
    print(f"🔒 [同じ種類の失敗を2回] このセッションで、同じ種類の失敗を2回 起こしています。3回目を起こさないために、先に決まりを書き出してください。\n"
          f"{lst}\n"
          f"   書く先＝.claude/state/sessions/{sid}/lessons.md。上の「種類: …」の行をそのまま写し、"
          "「次から確かめること:」で始まる行に、なぜ止められたか・次の一手の前に何を確かめるかを書く（書いた後に先へ進めます）。\n"
          "   まこさん指示 2026-10-01「確認せずに…適当に当てずっぽうな対処を当たるまで続けることをやめろ」", file=sys.stderr)
    return 2


def replay(days: int) -> int:
    proj = pathlib.Path.home() / ".claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget"
    cut = time.time() - days * 86400
    files = [p for p in proj.glob("*.jsonl") if p.stat().st_mtime >= cut]
    n_fail = n_block = n_later = 0
    for p in files:
        rows = load(p)
        cnt = collections.Counter()
        for nm, inp, err, _ts in rows:
            if err is None or (nm != "Stop" and (nm not in ACT_TOOLS or is_read(nm, inp))):
                continue
            n_fail += 1
            k = kind_of(err)
            if not k:
                continue
            cnt[k] += 1
        n_block += sum(v - 1 for v in cnt.values() if v >= 2)        # 2回目以降は毎回 止める
        n_later += sum(v - 2 for v in cnt.values() if v >= 2)
    print(f"記録 {len(files)} 本（直近 {days} 日）／書き込み・実行の失敗 {n_fail} 回")
    print(f"この強制が止める回数 {n_block} 回 ／ 止めた後に決まりを守れば防げた見込みの失敗（3回目以降） {n_later} 回")
    return 0


if __name__ == "__main__":
    if "--replay" in sys.argv:
        sys.exit(replay(int(sys.argv[sys.argv.index("--replay") + 1])))
    sys.exit(hook())
