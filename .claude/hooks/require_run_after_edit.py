#!/usr/bin/env python3
"""require_run_after_edit — 直したプログラムが走るかの見張り（Stop）。

役割＝CC が直した .py・.sh を、直した後に走らせて成功させるまで、返信を終えさせない。
  直したプログラムを、壊したまま まこさんに渡さないため。

★2026-10-15（182回目・まこさん「『直したプログラムが走るかの見張り』として残すので、すべて書き換え」「１と２は停止」）
  元＝require_confirm_before_act（2026-10-01 新設）。元の hook は「確認（これからやることが正しいと、根拠をもって確かめること）を
  させる」と名乗っていたが、見ていたのは 1 直す行を開いたか 2 直す前に走らせたか 3 直した後に走らせて成功したか、の3つの操作だけで、
  確認そのものは見ていなかった。1 と 2 は止め、3 だけを、この名前と役割で残した。
  あわせて、数える範囲を「まこさんの最後の発言の後」から「このセッションの全部」に広げた
  （直す前は、作業の途中にまこさんの発言が届くと、その前に直して走らせていないファイルが見張りから外れた）。

止める物＝このセッションで Write・Edit・MultiEdit・NotebookEdit した .py・.sh のうち、最後に直した後に、
  それを走らせて成功した記録（python3・bash・sh の直後にそのファイルの名前・結果が失敗でない）が無い物が1つでも在るとき。
  1つのターンで止めるのは1回だけ（stop_hook_active）。
見ない物＝置き場・worklog・計画・memory・下書き（FREE）／.py・.sh 以外。
限界＝走らせ方が確かめとして十分かは見ない（--help でも成功なら通る）。Bash（sed など）で書き替えたファイルは見ない。
  .claude/hooks の .sh は CC が走らせられないので、bash -n（文法の確かめ）で成功させる。

使い方: （hook）標準入力に JSON ／ --selftest ／ --replay <日数>（直近の記録に流して数える・何も止めない）
"""
import json
import pathlib
import re
import sys
import time

FREE = ("/.claude/state/sessions/", "session_worklog_", "/.claude/plans/", "/memory/", "chat_draft.md")
NOT_USER = ("Stop hook feedback", "<task-notification>", "<system-reminder>", "This session is being continued")
RUN_EXT = (".py", ".sh")
EDIT = ("Write", "Edit", "MultiEdit", "NotebookEdit")
RUN = re.compile(r"(?:^|[;&|(\s])(?:python3?|bash|sh)\s+(?:-\S+\s+)*([^\s;&|]+\.(?:py|sh))\b")


def user_text(o) -> str:
    """まこさんの発言の文（hook の差し戻しや知らせは数えない）。（require_read_used も使う）"""
    c = (o.get("message") or {}).get("content")
    if isinstance(c, str):
        return c if c.strip() and not c.lstrip().startswith(NOT_USER) else ""
    if isinstance(c, list):
        ts = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
        return "\n".join(t for t in ts if t.strip() and not t.lstrip().startswith(NOT_USER))
    return ""


def run_target(cmd: str):
    """Bash のコマンドが走らせる .py・.sh のパス（python3・bash・sh の直後に書いた物）。無ければ None。"""
    m = RUN.search(re.sub(r"'[^']*'|\"[^\"]*\"", "", str(cmd or "")))
    return m.group(1) if m else None


def _load(path) -> list:
    objs = []
    for ln in pathlib.Path(path).open(encoding="utf-8", errors="replace"):
        try:
            objs.append(json.loads(ln))
        except Exception:
            continue
    return objs


def events(objs) -> list:
    """並び＝[("user",) | ("use", id, 名前, 入力) | ("result", id, 失敗か)]。
    会話の本物の行（type が user か assistant）だけを読み、同じ uuid は1回だけ数える（API の控えの行で二重に数えない）。"""
    ev, seen = [], set()
    for o in objs:
        if o.get("type") not in ("user", "assistant"):
            continue
        u = o.get("uuid")
        if u:
            if u in seen:
                continue
            seen.add(u)
        if o.get("type") == "user" and user_text(o):
            ev.append(("user",))
            continue
        for b in (o.get("message") or {}).get("content") or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                ev.append(("use", b.get("id"), b.get("name"), b.get("input") or {}))
            elif b.get("type") == "tool_result":
                ev.append(("result", b.get("tool_use_id"), bool(b.get("is_error"))))
    return ev


def _norm(p: str) -> str:
    try:
        return str(pathlib.Path(p).expanduser().resolve())
    except Exception:
        return str(p)


def _ran_ok(ev: list, path: str, start: int) -> bool:
    failed = {e[1] for e in ev if e[0] == "result" and e[2]}
    base = pathlib.Path(path).name
    for e in ev[start:]:
        if e[0] == "use" and e[2] == "Bash":
            t = run_target(e[3].get("command"))
            if t and pathlib.Path(t).name == base and e[1] not in failed:
                return True
    return False


def check_stop(ev: list) -> list:
    """止める理由（空なら通す）。ev はこのセッションの全部の並び。"""
    last: dict = {}
    failed = {e[1] for e in ev if e[0] == "result" and e[2]}   # ★2026-10-20＝別の hook に止められて失敗した Edit・Write は、書き替わっていないので数えない
    for i, e in enumerate(ev):
        if e[0] == "use" and e[2] in EDIT and e[1] not in failed:
            fp = str(e[3].get("file_path") or e[3].get("notebook_path") or "")
            if fp.endswith(RUN_EXT) and not any(k in fp for k in FREE):
                last[_norm(fp)] = i
    return [f"{pathlib.Path(fp).name} を直した後に、走らせて成功した記録が無い（{fp}）"
            for fp, i in last.items() if not _ran_ok(ev, fp, i + 1)]


def hook() -> int:
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    if d.get("agent_type") or d.get("stop_hook_active"):
        return 0                                           # サブエージェントは見ない・1つのターンで止めるのは1回だけ
    tp = d.get("transcript_path")
    if not tp or not pathlib.Path(tp).exists():
        return 0
    ng = check_stop(events(_load(tp)))
    if not ng:
        return 0
    print("🔒 [直したプログラムが走るか] 直した .py・.sh を、直した後に走らせて成功させてから終える"
          "（.claude/hooks の .sh は bash -n で文法を確かめる）", file=sys.stderr)
    for x in ng:
        print("   ・" + x, file=sys.stderr)
    return 2


def selftest() -> int:
    me = _norm(__file__)
    sh = me[:-3] + ".sh"
    ed = ("use", "e1", "Edit", {"file_path": me})
    ed2 = ("use", "e2", "Edit", {"file_path": me})
    run = ("use", "r1", "Bash", {"command": f"python3 {me} --selftest"})
    cases = [
        ("S1 直した後に走らせていない → 止まる", [ed], False),
        ("S2 直した後に走らせて成功 → 通る", [ed, run, ("result", "r1", False)], True),
        ("S3 直した後に走らせて失敗だけ → 止まる", [ed, run, ("result", "r1", True)], False),
        ("S4 直した後に まこさんの発言が挟まり、走らせていない → 止まる", [ed, ("user",)], False),
        ("S5 走らせて成功した後に、また直して走らせていない → 止まる", [ed, run, ("result", "r1", False), ed2], False),
        ("S6 直す前に走らせただけ → 止まる", [run, ("result", "r1", False), ed], False),
        ("S7 .md を直した → 通る", [("use", "e3", "Edit", {"file_path": me[:-3] + ".md"})], True),
        ("S8 .sh を直して bash -n で成功 → 通る",
         [("use", "e4", "Write", {"file_path": sh}), ("use", "r2", "Bash", {"command": f"bash -n {sh}"}),
          ("result", "r2", False)], True),
        ("S9 置き場（sessions）の .py は見ない → 通る",
         [("use", "e5", "Write", {"file_path": "/x/.claude/state/sessions/a/b.py"})], True),
        ("S10 直そうとした Edit が失敗した（別の hook に止められた）→ 通る",
         [("use", "e6", "Edit", {"file_path": me}), ("result", "e6", True)], True),
    ]
    bad = 0
    for nm, ev, want in cases:
        ok = (not check_stop(ev)) == want
        bad += not ok
        print(f"  {'✅' if ok else '❌'} {nm}")
    dup = [{"type": "user", "uuid": "u1", "message": {"content": "直して"}},
           {"type": "user", "uuid": "u1", "message": {"content": "直して"}},
           {"type": "api-request-blob", "message": {"content": [{"type": "tool_use", "id": "z", "name": "Edit",
                                                                   "input": {"file_path": me}}]}}]
    ok = events(dup) == [("user",)]
    bad += not ok
    print(f"  {'✅' if ok else '❌'} E1 同じ uuid は1回・API の控えの行は数えない")
    print(f"自己テスト {11 - bad}/11")
    return 1 if bad else 0


def replay(days: int) -> int:
    """直近の記録に流して、まこさんの発言の直前（ターンの終わり）で止まる回数を数える（何も止めない）。"""
    proj = pathlib.Path.home() / ".claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget"
    cut = time.time() - days * 86400
    n_turn = n_stop = 0
    for f in [p for p in proj.glob("*.jsonl") if p.stat().st_mtime >= cut]:
        ev = events(_load(f))
        for i, e in enumerate(ev + [("user",)]):
            if e[0] == "user" and i > 0:
                n_turn += 1
                n_stop += bool(check_stop(ev[:i]))
    print(f"直近 {days} 日＝ターン {n_turn} 回のうち、終わりで止まる {n_stop} 回")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--replay" in sys.argv:
        sys.exit(replay(int(sys.argv[sys.argv.index("--replay") + 1])))
    sys.exit(hook())
