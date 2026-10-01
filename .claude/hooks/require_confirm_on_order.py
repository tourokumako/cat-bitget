#!/usr/bin/env python3
"""require_confirm_on_order — まこさんが「確認しろ」と言ったら、確かめた相手を実際に開くまで書き込み・実行をさせない（2026-10-01 新設）。

まこさん（逐語 2026-10-01）＝「私が確認しろといったら確認をするようにできない？」「確認しろって言っても確認しないんだ。」

決まり
  まこさんの最後の発言（user の行の文の塊・hook の差し戻しは数えない）に、言い付けの形
  （確認しろ・確認して・確認をしろ・確認をして・確認せよ・確認しなさい・確認すること）が在れば、
  その発言の後に次の2つがそろうまで、書き込み・実行（読む操作でないもの）を止める。
    ①.claude/state/sessions/<セッション>/confirm.md を、その発言より後に書く。中身＝確かめた相手を1行に1つ
      「確認: <ファイル名>:<行番号>」か「確認: <URL>」で書く（1つ以上）。
    ②書いた相手を、その発言の後に実際に開いている（Read・読むだけの Bash に そのファイル名／WebFetch に その URL）。
  止めないもの＝読む操作／セッションの置き場・worklog・計画・memory への書き込み。
限界＝開いた相手が正しいか・読んだ中身を正しく理解したかは見ない。

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

ROOT = pathlib.Path(__file__).resolve().parents[2]
SESS = ROOT / ".claude/state/sessions"
FREE = ("/.claude/state/sessions/", "session_worklog_", "/.claude/plans/", "/memory/", "chat_draft.md")
NOT_USER = ("Stop hook feedback", "<task-notification>", "<system-reminder>", "This session is being continued")
ORDER = re.compile(r"確認(?:を)?(?:しろ|して(?!る|い|た)|せよ|しなさい|すること)")
ITEM = re.compile(r"^\s*確認[:：]\s*(\S+)")


def user_text(o) -> str:
    c = (o.get("message") or {}).get("content")
    if isinstance(c, str):
        return c if not c.lstrip().startswith(NOT_USER) else ""
    if isinstance(c, list):
        ts = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
        ts = [t for t in ts if t.strip() and not t.lstrip().startswith(NOT_USER)]
        return "\n".join(ts)
    return ""


def load(path: pathlib.Path):
    """戻り＝[("user", 文, 時刻) | ("call", 道具, 入力)]。"""
    ev = []
    for line in path.open(encoding="utf-8", errors="replace"):
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("type") == "user":
            t = user_text(o)
            if t:
                ev.append(("user", t, o.get("timestamp") or ""))
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


def opened_after(ev, start: int, item: str) -> bool:
    is_url = item.startswith("http")
    base = pathlib.Path(item.split(":")[0]).name if not is_url else item
    for kind, nm, inp in ev[start:]:
        if kind != "call":
            continue
        if is_url and nm == "WebFetch" and str(inp.get("url", "")).rstrip("/") == item.rstrip("/"):
            return True
        if not is_url and nm == "Read" and pathlib.Path(str(inp.get("file_path", ""))).name == base:
            return True
        if not is_url and nm in ("Bash", "Grep") and is_read(nm, inp) and base in json.dumps(inp, ensure_ascii=False):
            return True
    return False


def missing(ev, session: str):
    """言い付けが在り、確認がそろっていなければ、足りない理由の文を返す。そろっていれば None。"""
    last = max((i for i, e in enumerate(ev) if e[0] == "user"), default=-1)
    if last < 0 or not ORDER.search(ev[last][1]):
        return None
    p = SESS / session / "confirm.md"
    if not p.exists() or p.stat().st_mtime < _ts(ev[last][2]):
        return "確認の記録（confirm.md）が、まこさんの言い付けより後に書かれていない"
    items = [m.group(1) for ln in p.read_text(encoding="utf-8").splitlines() if (m := ITEM.match(ln))]
    if not items:
        return "確認の記録に「確認: <ファイル名>:<行番号>」か「確認: <URL>」の行が1つも無い"
    bad = [it for it in items if not opened_after(ev, last + 1, it)]
    if bad:
        return "言い付けの後に開いていない相手が在る: " + " ／ ".join(bad[:5])
    return None


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
    why = missing(load(pathlib.Path(tp)), sid)
    if not why:
        return 0
    print(f"🔒 [確認しろと言われた] まこさんが「確認しろ」と言っています。確かめる前に書き込み・実行はできません。\n"
          f"   足りないもの＝{why}\n"
          f"   やること＝確かめる相手を Read・読むだけのコマンド・WebFetch で開き、"
          f".claude/state/sessions/{sid}/confirm.md に「確認: <ファイル名>:<行番号>」か「確認: <URL>」を1行に1つ書く。\n"
          "   まこさん（逐語 2026-10-01）「私が確認しろといったら確認をするようにできない？」", file=sys.stderr)
    return 2


def replay(days: int) -> int:
    proj = pathlib.Path.home() / ".claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget"
    cut = time.time() - days * 86400
    files = [p for p in proj.glob("*.jsonl") if p.stat().st_mtime >= cut]
    n_order = n_noread = n_block = 0
    for p in files:
        ev = load(p)
        for i, e in enumerate(ev):
            if e[0] != "user" or not ORDER.search(e[1]):
                continue
            n_order += 1
            nxt = [x for x in ev[i + 1:] if x[0] == "user"]
            end = ev.index(nxt[0]) if nxt else len(ev)
            first_act = next((x for x in ev[i + 1:end] if x[0] == "call" and x[1] in ACT_TOOLS
                              and not is_read(x[1], x[2]) and not free_write(x[1], x[2])), None)
            if first_act is None:
                continue
            n_block += 1                                   # 確認の記録が無いので、最初の書き込み・実行で必ず1回 止まる
            k = ev.index(first_act)
            if not any(x[0] == "call" and is_read(x[1], x[2]) for x in ev[i + 1:k]):
                n_noread += 1
    print(f"記録 {len(files)} 本（直近 {days} 日）／まこさんの「確認しろ」の言い付け {n_order} 回")
    print(f"この強制が止める回数 {n_block} 回 ／ そのうち、言い付けの後に何も開かずに書き込み・実行に入っていた回数 {n_noread} 回")
    return 0


if __name__ == "__main__":
    if "--replay" in sys.argv:
        sys.exit(replay(int(sys.argv[sys.argv.index("--replay") + 1])))
    sys.exit(hook())
