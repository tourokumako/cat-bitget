#!/usr/bin/env python3
"""enforce_observe_diag_only_selftest.py — 検証は observe_diag だけ（enforce_observe_diag_only.sh）の自己テスト
（★2026-10-17・185回目・まこさん「必要。CCの案で修正してよい」）。

何をするか＝コマンドを1つずつ入れた入力を hook に渡し、終了コードを見る。
  作業場のパスは名前だけ（ファイルは作らない）。本物のファイルは何も書かない。
使い方: python3 .claude/hooks/enforce_observe_diag_only_selftest.py --selftest
"""
import json
import subprocess
import sys

HOOK = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/enforce_observe_diag_only.sh"
S = "/private/tmp/claude-501/selftest/scratchpad/a.py"

CASES = [
    ("S1 作業場の .py を直接 走らせると止まる", f"python3 {S}", 2),
    ("S2 作業場の .py を写して走らせると止まる（回り込み）",
     f"cp {S} .claude/state/a.py && python3 .claude/state/a.py", 2),
    ("S3 time で包んで走らせても止まる", f"time python3 {S}", 2),
    ("S4 ヒアドキュメントで書いて走らせると止まる", f"cat > {S} <<'EOF'\nprint(1)\nEOF\npython3 {S}", 2),
    ("S5 rm で消すだけなら通る", f"rm {S} && python3 .claude/tools/try_hooks.py --selftest", 0),
    ("S6 試しの道具の引数なら通る", f"python3 .claude/tools/try_hooks.py --session s --write {S}", 0),
    ("S7 正本の道具は通る", "python3 .claude/tools/try_hooks.py --selftest", 0),
]


def run(cmd: str) -> int:
    inp = json.dumps({"session_id": "selftest", "tool_name": "Bash", "tool_input": {"command": cmd}}, ensure_ascii=False)
    return subprocess.run(["bash", HOOK], input=inp, capture_output=True, text=True, timeout=60).returncode


def selftest() -> int:
    ng = 0
    for name, cmd, want in CASES:
        got = run(cmd)
        print(f"{'✅' if got == want else '❌'} {name}（期待 rc={want}・結果 rc={got}）")
        ng += int(got != want)
    print(f"selftest {len(CASES) - ng}/{len(CASES)}")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 2)
