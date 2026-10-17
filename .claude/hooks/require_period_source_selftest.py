#!/usr/bin/env python3
"""require_period_source_selftest.py — 期間正本ゲート（require_period_source.sh）の自己テスト
（★2026-10-17・185回目・まこさん「要」「修正をして」）。

何をするか＝一時の置き場（名前に priority_rebuild を含むフォルダ）に見本の .py を作り、
  それを走らせるコマンドを hook に渡して、終了コードを見る。本物のファイルは何も書かない（一時の置き場は消す）。
使い方: python3 .claude/hooks/require_period_source_selftest.py --selftest
"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/require_period_source.sh"


def run(cmd: str) -> int:
    inp = json.dumps({"session_id": "selftest", "tool_name": "Bash", "tool_input": {"command": cmd}}, ensure_ascii=False)
    return subprocess.run(["bash", HOOK], input=inp, capture_output=True, text=True, timeout=60).returncode


def selftest() -> int:
    with tempfile.TemporaryDirectory() as d:
        pr = os.path.join(d, "priority_rebuild")
        os.makedirs(pr)
        files = {
            "ok.py": "import periods\nSCORE_START = periods.SCORE_START\n",
            "hand.py": 'import pandas as pd\nTRAIN_END = pd.Timestamp("2025-01-01")\n',
            "hand_search.py": 'import pandas as pd\nSEARCH_START = pd.Timestamp("2024-03-01")\n',
            "ok_search.py": "import periods\nSEARCH_START = periods.SEARCH_START\n",
            "periods.py": 'import pandas as pd\nTRAIN_END = pd.Timestamp("2025-03-01")\n',
        }
        for name, body in files.items():
            with open(os.path.join(pr, name), "w", encoding="utf-8") as f:
                f.write(body)
        p = lambda n: os.path.join(pr, n)                     # noqa: E731
        cases = [
            ("S1 1本目に期間を手で書いた .py は止まる", f"python3 {p('hand.py')}", 2),
            ("S2 2本目に期間を手で書いた .py も止まる", f"python3 {p('ok.py')} && python3 {p('hand.py')}", 2),
            ("S3 値決めの窓 SEARCH_START を手で書くと止まる", f"python3 {p('hand_search.py')}", 2),
            ("S4 periods から読む形は通る", f"python3 {p('ok_search.py')}", 0),
            ("S5 periods.py そのものは通る", f"python3 {p('periods.py')}", 0),
            ("S6 python を走らせないコマンドは通る", f"grep -n TRAIN_END {p('hand.py')}", 0),
            ("S7 試しの道具の引用符の中の .py は走らせる形と見ない",
             f"python3 .claude/tools/try_hooks.py --session s --bash \"python3 {p('hand.py')}\"", 0),
            ("S8 cd の後ろで走らせる形は止まる", f"cd {pr} && python3 {p('hand.py')}", 2),
        ]
        ng = 0
        for name, cmd, want in cases:
            got = run(cmd)
            print(f"{'✅' if got == want else '❌'} {name}（期待 rc={want}・結果 rc={got}）")
            ng += int(got != want)
    print(f"selftest {len(cases) - ng}/{len(cases)}")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 2)
