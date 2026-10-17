#!/usr/bin/env python3
"""enforce_flow_declaration_selftest.py — フロー宣言ゲート（enforce_flow_declaration.sh）の自己テスト
（★2026-10-17・186回目・まこさん「要。CCの案で修正する」）。

何をするか＝コマンドを1つずつ入れた入力を hook に渡し、hook が「走らせる対象」と読んだ .py の名前を見る。
  名前の読み方は2通り＝hook の --print-targets の出力（直した後）／止めの文の「対象:」の行（直す前・宣言が古いとき）。
  宣言のファイル（flow_declaration.md）と貼った印は、読みも書きもしない＝本物のファイルは何も書かない。
  ★宣言の中身を見る判定（鮮度・時間の見込み・過去の実測・数え方）は、この自己テストの外（今回の直しで触っていない）。
使い方: python3 .claude/hooks/enforce_flow_declaration_selftest.py --selftest
"""
import json
import re
import subprocess
import sys

HOOK = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/enforce_flow_declaration.sh"
PR = "scripts/priority_rebuild"

CASES = [
    ("S1 score.py を走らせると対象になる", f"python3 {PR}/score.py results/x.csv", "score.py"),
    ("S2 cd と time と -u で包んだ observe_diag.py も対象になる",
     f"cd /x && time python3 -u {PR}/observe_diag.py --rank-regime d.csv 2>&1 | tail -5", "observe_diag.py"),
    ("S3 engine_tuner.py の本走は対象になる", f"python3 {PR}/engine_tuner.py --purpose search", "engine_tuner.py"),
    ("S4 e36_ で始まる戦略も対象になる", f"python3 {PR}/e36_short_oscillation.py", "e36_short_oscillation.py"),
    ("S5 区切りの後ろの report.py も対象になる", f"python3 scripts/a.py; python3 {PR}/report.py x", "report.py"),
    ("S6 試しの道具の引数に名前があるだけなら対象にしない（10月6日の誤報の形）",
     f"python3 .claude/tools/try_hooks.py --session s --write {PR}/observe_diag.py", ""),
    ("S7 名前の末尾だけが同じ .py は対象にしない（enforce_no_false_report.py）",
     "python3 .claude/hooks/enforce_no_false_report.py --check", ""),
    ("S8 grep で名前を数えるだけなら対象にしない", "grep -c score.py .claude/state/next_step.md", ""),
    ("S9 --help は対象にしない", f"python3 {PR}/score.py --help", ""),
    ("S10 grep と python が同じコマンドに在っても、python が対象を走らせなければ対象にしない",
     "grep -c regime engine_tuner_gen.py ; python3 - ", ""),
    ("S11 引用符の中の言及は対象にしない", 'echo "python3 score.py"', ""),
    ("S12 パスつきの python で走らせても対象になる（直す前は見落とした）", f".venv/bin/python {PR}/score.py x.csv", "score.py"),
    ("S13 nohup で包んで裏で走らせても対象になる", f"nohup python3 {PR}/observe_diag.py --rank-regime d.csv &", "observe_diag.py"),
]


def targets(cmd: str) -> str:
    inp = json.dumps({"session_id": "selftest", "tool_name": "Bash", "tool_input": {"command": cmd}}, ensure_ascii=False)
    p = subprocess.run(["bash", HOOK, "--print-targets"], input=inp, capture_output=True, text=True, timeout=60)
    out = p.stdout.strip()
    if not out:
        m = re.search(r"^対象: (.*)$", p.stderr, re.M)
        out = m.group(1).strip() if m else ""
    return " ".join(sorted(out.split()))


def selftest() -> int:
    ng = 0
    for name, cmd, want in CASES:
        got = targets(cmd)
        print(f"{'✅' if got == want else '❌'} {name}（期待「{want}」・結果「{got}」）")
        ng += int(got != want)
    print(f"selftest {len(CASES) - ng}/{len(CASES)}")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 2)
