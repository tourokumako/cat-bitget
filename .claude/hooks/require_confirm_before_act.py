#!/usr/bin/env python3
"""require_confirm_before_act — 書き込み・実行の前に、その相手について根拠と「なぜ正しく機能するか」を書かせる（2026-10-01 新設）。

まこさんの「確認」の定義（逐語 2026-10-01）＝「確認とは これからやることが正しいと、根拠をもって確かめること
そのために該当箇所を開いて、内容を把握、理解をし、正しく機能をする対処方法であるか、証拠をつかんでから対応する」。
まこさん（逐語・同日）「強制をしろっていってんだけど。なんで徹底的に回避するんだよ」。

決まり
  まこさんの最後の指示（user の行の文の塊・hook の差し戻しは数えない）の後、相手に初めて書き込み・実行する前に、
  .claude/state/sessions/<セッション>/confirm.md に、その指示より後に書いた次の3行のまとまりが要る。
    対象: <相手>
    根拠: <ファイル名:行番号 ／ URL ／ コマンド: …>（1つ以上）
    なぜ正しく機能するか: <文>
  根拠は、その指示の後に実際に開いた（Read・読むだけの Bash・Grep・WebFetch）か走らせた（Bash）記録が要る。
  相手＝直すファイルの名前／走らせる .py・.sh の名前（無ければコマンドの頭の2語）／Agent。
  同じ指示の中で一度そろえた相手は、続けて触っても止めない。
  止めないもの＝読む操作／セッションの置き場・worklog・計画・memory・下書きへの書き込み。
限界＝書いた「なぜ正しく機能するか」が正しいか・中身を理解したかは見ない（まこさんが confirm.md を読める）。

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
from block_repeat_failure import target_of                 # 相手の決め方を同じものにする

ROOT = pathlib.Path(__file__).resolve().parents[2]
SESS = ROOT / ".claude/state/sessions"
FREE = ("/.claude/state/sessions/", "session_worklog_", "/.claude/plans/", "/memory/", "chat_draft.md")
NOT_USER = ("Stop hook feedback", "<task-notification>", "<system-reminder>", "This session is being continued")


def short(t: str) -> str:
    return pathlib.Path(t).name if "/" in t else t


RUN = re.compile(r"(?:^|[;&|(\s])(?:python3?|bash|sh)\s+(?:-\S+\s+)*([^\s;&|]+\.(?:py|sh))\b")


def tgt_of(name, inp) -> str:
    """相手の名前。Bash は「python3・python・bash・sh の直後に書いた .py・.sh」だけを走らせる相手とし、
    それ以外は まとめて「Bash」1つ（頭の2語ごとに分けると確認の記録が増えすぎる）。

    ★2026-10-01（本物で見つけた誤り）＝直す前は target_of（コマンドに出てくる最初の .py・.sh）で決めていたので、
      git add に .py の名前を並べただけで「その .py を走らせる」と読み、走らせていない相手の記録を求めた。
    """
    if name == "Bash":
        cmd = re.sub(r"'[^']*'|\"[^\"]*\"", "", str((inp or {}).get("command", "")))
        m = RUN.search(cmd)
        return pathlib.Path(m.group(1)).name if m else "Bash"
    return short(target_of(name, inp))


def user_text(o) -> str:
    c = (o.get("message") or {}).get("content")
    if isinstance(c, str):
        return c if c.strip() and not c.lstrip().startswith(NOT_USER) else ""
    if isinstance(c, list):
        ts = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
        return "\n".join(t for t in ts if t.strip() and not t.lstrip().startswith(NOT_USER))
    return ""


def load(path: pathlib.Path):
    ev = []
    for line in path.open(encoding="utf-8", errors="replace"):
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("type") == "user" and user_text(o):
            ev.append(("user", None, o.get("timestamp") or ""))
        elif o.get("type") == "assistant":
            for b in (o.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    ev.append(("call", b.get("name"), b.get("input") or {}))
    return ev


def _ts(s: str) -> float:
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def blocks(txt: str):
    """confirm.md を「対象:」ごとのまとまりに分ける。戻り＝[(対象, [根拠], なぜの文)]。"""
    out, cur = [], None
    for ln in txt.splitlines():
        s = ln.strip()
        if s.startswith("対象:") or s.startswith("対象："):
            cur = [s.split(":", 1)[-1].split("：", 1)[-1].strip(), [], ""]
            out.append(cur)
        elif cur and (s.startswith("根拠:") or s.startswith("根拠：")):
            cur[1].append(s.split(":", 1)[-1].split("：", 1)[-1].strip())
        elif cur and s.startswith("なぜ正しく機能するか"):
            cur[2] = s.split(":", 1)[-1].split("：", 1)[-1].strip()
    return [tuple(b) for b in out]


def evidenced(item: str, turn) -> bool:
    if item.startswith("コマンド"):
        cmd = item.split(":", 1)[-1].split("：", 1)[-1].strip()
        return bool(cmd) and any(nm == "Bash" and cmd in str(inp.get("command", "")) for _k, nm, inp in turn)
    if item.startswith("http"):
        return any(nm == "WebFetch" and str(inp.get("url", "")).rstrip("/") == item.rstrip("/") for _k, nm, inp in turn)
    base = pathlib.Path(item.split(":")[0]).name
    for _k, nm, inp in turn:
        if nm == "Read" and pathlib.Path(str(inp.get("file_path", ""))).name == base:
            return True
        if nm in ("Bash", "Grep") and is_read(nm, inp) and base and base in json.dumps(inp, ensure_ascii=False):
            return True
    return False


CODE_EXT = (".py", ".sh", ".json")


def free_write(name, inp) -> bool:
    """確認の記録を求めない書き込み＝置き場・worklog 等と、プログラムでも設定でもない文書（.md ほか）。

    ★2026-10-01（まこさん「多すぎるなら適切な量にしてほしい」）＝7日の記録で、失敗は実行（土台ゲート 257回・
      設計↔実装ゲート 86回・終了コード 61回）に集まり、文書の書き換えの失敗はわずかだった＝文書は外す。
    """
    p = str((inp or {}).get("file_path") or (inp or {}).get("notebook_path") or "")
    if name not in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        return False
    return any(k in p for k in FREE) or not p.endswith(CODE_EXT)


def check(ev, session: str, name, inp):
    """戻り＝止める理由の文 か None。"""
    last = max((i for i, e in enumerate(ev) if e[0] == "user"), default=-1)
    if last < 0:
        return None
    tgt = tgt_of(name, inp)
    turn = [e for e in ev[last + 1:] if e[0] == "call"]
    p = SESS / session / "confirm.md"
    if not p.exists() or p.stat().st_mtime < _ts(ev[last][2]):
        return f"確認の記録（confirm.md）が、まこさんの最後の指示より後に書かれていない（相手＝{tgt}）"
    for t, ev_items, why in blocks(p.read_text(encoding="utf-8")):
        if short(t) != tgt:
            continue
        if not ev_items or not why:
            return f"「対象: {tgt}」のまとまりに、根拠か「なぜ正しく機能するか」が無い"
        bad = [x for x in ev_items if not evidenced(x, turn)]
        if bad:
            return f"根拠を、まこさんの最後の指示の後に開いて（走らせて）いない: " + " ／ ".join(bad[:4])
        return None
    return f"確認の記録に「対象: {tgt}」のまとまりが無い"


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
    why = check(load(pathlib.Path(tp)), sid, name, inp)
    if not why:
        return 0
    tgt = tgt_of(name, inp)
    print(f"🔒 [確認してから動く] {why}\n"
          f"   .claude/state/sessions/{sid}/confirm.md に、次の形で書いてから動いてください（根拠は先に開く・走らせる）:\n"
          f"     対象: {tgt}\n     根拠: <ファイル名:行番号 ／ URL ／ コマンド: …>\n     なぜ正しく機能するか: <文>\n"
          "   まこさんの定義（2026-10-01）「これからやることが正しいと、根拠をもって確かめること…証拠をつかんでから対応する」",
          file=sys.stderr)
    return 2


def replay(days: int) -> int:
    proj = pathlib.Path.home() / ".claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget"
    cut = time.time() - days * 86400
    files = [p for p in proj.glob("*.jsonl") if p.stat().st_mtime >= cut]
    per_session = "--per-session" in sys.argv                # 試しの数え方だけ＝セッションの中で相手ごとに1回
    n_turn = n_pairs = n_act = 0
    for p in files:
        seen = set()
        for kind, nm, inp in load(p):
            if kind == "user":
                n_turn += 1
                if not per_session:
                    seen = set()
                continue
            if nm not in ACT_TOOLS or is_read(nm, inp) or free_write(nm, inp):
                continue
            n_act += 1
            t = tgt_of(nm, inp)
            if t not in seen:
                seen.add(t)
                n_pairs += 1
    print(f"記録 {len(files)} 本（直近 {days} 日）／まこさんの指示 {n_turn} 回／書き込み・実行 {n_act} 回")
    print(f"確認の記録が要る回数（指示ごと・相手ごとに1回）＝{n_pairs} 回")
    return 0


if __name__ == "__main__":
    if "--replay" in sys.argv:
        sys.exit(replay(int(sys.argv[sys.argv.index("--replay") + 1])))
    sys.exit(hook())
