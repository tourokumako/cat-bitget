#!/usr/bin/env python3
"""require_try_before_act.py — 書く・走らせる前に、試しの道具（try_hooks.py）で hook 全部に先に試し、
止める物が0本だった記録が無ければ止める。

★2026-10-06（まこさん「じゃあ入れる」「OK」・案 A・恒久75番）
  なぜ要るか＝CC が確かめずに書き・走らせ、hook に1つずつ当たって止まり、原因を確かめずに出し直す往復を繰り返した（155回目）。
  先に試せば、止める物が1回で全部 分かる。
相手＝コード・設定・設計書・hook・道具・壊すプログラムを書く前（Write・Edit・MultiEdit）と、
  .py を走らせる・python3 を変数で走らせる・.claude の hooks／tools／breaks のパスや承認のプログラムの名前が入る Bash の前。
  ★2026-10-15（181回目）＝本物で打つのと同じ入力（Edit＝ファイル・直す前と後の文字／Bash＝コマンドの文字）を試した印が
  30分以内に無ければ止める（直す前は相手のファイルごとの記録で、試した後に文字を変えても通った）。
限界＝Write は中身を見ない（ファイルだけ）。ターンの終わりの検査は試せない。
  この hook と試しの道具を書き換えれば無効にできる（git diff には出る）。
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

sys.path.insert(0, "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools")
import try_hooks as th  # noqa: E402

WINDOW = 1800
WRITE_PARTS = ("/scripts/priority_rebuild/", "/.claude/hooks/", "/.claude/tools/", "/.claude/breaks/")
WRITE_FILES = ("/.claude/state/acceptance.md", "/.claude/settings.json")
BASH_PARTS = (".claude/hooks/", ".claude/tools/", ".claude/breaks/", "approve_impl", "approve_design")   # ★2026-10-15
PY_VAR = re.compile(r"\bpython3?\s+\$")                    # ★2026-10-15＝.py のパスを変数に入れた走らせ方


def guarded(tool: str, tin: dict) -> list:
    """止める相手の、生のパス（記録の鍵は realpath）。"""
    if tool in ("Write", "Edit", "MultiEdit"):
        p = os.path.abspath(tin.get("file_path") or "")
        return [p] if any(s in p for s in WRITE_PARTS) or p.endswith(WRITE_FILES) else []
    cmd = tin.get("command") or ""
    if "try_hooks.py" in cmd:                      # 試しの道具そのもの（--bash の中に走らせる .py の文字が入る）は止めない
        return []
    # ★2026-10-15（181回目・まこさん「強制で解決できないの？」「じゃあ、先に直して」）＝Bash の相手を広げた。
    #   直す前＝scripts/priority_rebuild の .py を走らせるときだけ。この日 CC は、ほかの Bash（.claude/hooks のパスの grep・
    #   承認のプログラムの名前・.py のパスを変数に入れた走らせ方）を試さずに打ち、土台・承認・設計↔実装のゲートに止められた。
    #   直した後＝.py を走らせる Bash・python3 を変数で走らせる Bash・.claude の hooks／tools／breaks のパスや
    #   承認のプログラムの名前が入る Bash を、全部 相手にする。
    if th.PY_RE.search(cmd) or PY_VAR.search(cmd) or any(s in cmd for s in BASH_PARTS):
        return [cmd[:80]]
    return []


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:                                        # noqa: BLE001
        return 0
    tool = data.get("tool_name", "")
    tin = data.get("tool_input") or {}
    if tool not in ("Write", "Edit", "MultiEdit", "Bash") or not guarded(tool, tin):
        return 0
    try:
        rec = json.load(open(th.RECORD, encoding="utf-8"))
    except Exception:                                        # noqa: BLE001
        rec = {}
    now = time.time()
    # ★2026-10-15（181回目）＝相手（ファイル）ごとの30分の記録ではなく、本物で打つのと同じ入力を試した印（try_hooks.input_key）を見る。
    #   直す前＝同じファイルなら、試した後に直す文字を変えても通った＝試していない入力で打ち、止められた。
    key = th.input_key(tool, tin)
    miss = [] if now - (rec.get(key) or {}).get("t", 0) <= WINDOW else [f"{tool} {guarded(tool, tin)[0]}"]
    if not miss:
        return 0
    if not data.get("session_id"):
        # ★2026-10-06（156回目）＝承認のプログラムの中の門（pre_audit_check.py --check-design）は session_id を渡さない
        #   （本物の書き込みではない）。この文で止めると、門は見送りに数える（_input_shape_miss）。本物の書き込みには必ず在る。
        sys.stderr.write("🔒 [先に試す] セッションの id が hook の入力に無い（承認の前の門の試し＝本物の書き込みではない）\n")
        return 2
    sid = data.get("session_id", "<SESSION>")
    how = (f'python3 .claude/tools/try_hooks.py --session {sid} --bash "<同じコマンド>"' if tool == "Bash" else
           f"python3 .claude/tools/try_hooks.py --session {sid} --edit <パス> --old <直す前の文字> --new <直した後の文字>"
           "（Write なら --write <パス>）")
    sys.stderr.write(
        "🔒 [先に試す] 書く・走らせる前に、hook 全部へ同じ入力を先に試して、止める物が0本の記録を作ってください"
        "（まこさん決定 2026-10-06「じゃあ入れる」・恒久75番）。\n"
        f"   同じ入力を試した記録が無い（30分以内・直す文字やコマンドを1文字でも変えたら試し直す）: {miss}\n"
        f"   試す: {how}\n"
        "   ★止める hook が在れば、試しの道具が全部 一度に出します＝1つずつ当たって出し直さない。\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
