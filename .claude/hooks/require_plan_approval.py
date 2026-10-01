#!/usr/bin/env python3
"""require_plan_approval — まこさんの指示の後は、承認された計画が無ければ書き込み・実行をさせない（2026-10-01 新設）。

まこさん指示（逐語 2026-10-01）＝「だから確認してから動くようにしろよ。。。なんで徹底的に回避するわけ？」
出どころ（外）＝Anthropic 公式 Best practices「Explore first, then plan, then code」・計画モード
（"edits stay blocked until you approve the plan"）。計画モードは会話の始めにしか掛からないので、指示ごとに掛ける。

決まり
  まこさんの最後の発言（user の行の文の塊。hook の差し戻しの文・途中で届いた発言は数えない）より後に、
  ExitPlanMode の結果「User has approved your plan」が無ければ、書き込み・実行（Write・Edit・MultiEdit・
  NotebookEdit・Agent・読むだけでない Bash）を止める。
  止めないもの＝読む操作／計画のファイル・worklog・セッションの置き場・memory・下書きへの書き込み。

使い方: （hook）標準入力に PreToolUse の JSON ／ --replay <日数> 直近の記録に流して数える（何も止めない）
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from require_check_after_failure import ACT_TOOLS, is_read  # 読むだけの判定を同じものにする

FREE = ("/.claude/plans/", "session_worklog_", "/.claude/state/sessions/", "/memory/", "chat_draft.md")
NOT_USER = ("Stop hook feedback", "<task-notification>", "<system-reminder>", "This session is being continued")
APPROVED = "User has approved your plan"


def free_write(name, inp) -> bool:
    p = str((inp or {}).get("file_path") or (inp or {}).get("notebook_path") or "")
    return name in ("Write", "Edit", "MultiEdit", "NotebookEdit") and any(k in p for k in FREE)


def events(path: pathlib.Path):
    """戻り＝[("user"|"approve"|"call", 道具, 入力)] を記録の順に。"""
    out = []
    for line in path.open(encoding="utf-8", errors="replace"):
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("type") == "user":
            c = (o.get("message") or {}).get("content")
            if isinstance(c, str):
                if c.strip() and not c.lstrip().startswith(NOT_USER):
                    out.append(("user", None, None))
                continue
            if not isinstance(c, list):
                continue
            texts = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
            if any(t.strip() and not t.lstrip().startswith(NOT_USER) for t in texts):
                out.append(("user", None, None))
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    t = b.get("content")
                    if isinstance(t, list):
                        t = " ".join(x.get("text", "") for x in t if isinstance(x, dict))
                    if str(t or "").startswith(APPROVED):
                        out.append(("approve", None, None))
        elif o.get("type") == "assistant":
            for b in (o.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    out.append(("call", b.get("name"), b.get("input")))
    return out


def needs_plan(ev) -> bool:
    """最後のまこさんの発言より後に、承認された計画が無いか。"""
    last_user = max((i for i, e in enumerate(ev) if e[0] == "user"), default=-1)
    if last_user < 0:
        return False
    return not any(e[0] == "approve" for e in ev[last_user + 1:])


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
    if not needs_plan(events(pathlib.Path(tp))):
        return 0
    print("🔒 [計画の承認が無い] まこさんの最後の指示の後に、承認された計画がありません。\n"
          "   先に、確かめたこと（開いたファイルの行・URL）と、触るファイルと、やることを計画に書き、"
          "計画モード（EnterPlanMode → ExitPlanMode）で まこさんの承認をもらってから書き込み・実行してください。\n"
          "   読む操作は止めません。\n"
          "   まこさん指示 2026-10-01「だから確認してから動くようにしろよ」", file=sys.stderr)
    return 2


def replay(days: int) -> int:
    proj = pathlib.Path.home() / ".claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget"
    cut = time.time() - days * 86400
    files = [p for p in proj.glob("*.jsonl") if p.stat().st_mtime >= cut]
    n_user = n_turn_block = n_act = n_free = 0
    for p in files:
        ev = events(p)
        blocked_turn = -1
        for k, (kind, nm, inp) in enumerate(ev):
            if kind == "user":
                n_user += 1
                continue
            if kind != "call" or nm not in ACT_TOOLS or is_read(nm, inp):
                continue
            if free_write(nm, inp):
                n_free += 1
                continue
            n_act += 1
            last_user = max((i for i in range(k) if ev[i][0] == "user"), default=-1)
            if last_user >= 0 and needs_plan(ev[:k]) and last_user != blocked_turn:
                blocked_turn = last_user                       # 本物では1回止まって計画を承認すれば外れる＝指示ごとに1回
                n_turn_block += 1
    print(f"記録 {len(files)} 本（直近 {days} 日）／まこさんの発言 {n_user} 回／書き込み・実行 {n_act} 回（止めない書き込み {n_free} 回）")
    print(f"この強制が止める回数（指示ごとに1回）＝{n_turn_block} 回")
    return 0


if __name__ == "__main__":
    if "--replay" in sys.argv:
        sys.exit(replay(int(sys.argv[sys.argv.index("--replay") + 1])))
    sys.exit(hook())
