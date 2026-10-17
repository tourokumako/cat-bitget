#!/usr/bin/env python3
"""require_design_contract_before_run_selftest.py — 設計↔実装ゲート（require_design_contract_before_run.sh）の自己テスト
（★2026-10-17・185回目・まこさん「OK」）。

なぜ別のファイルか＝hook の判定は bash の中の埋め込みの python に在り、hook 自身に --selftest の口を足すと
  入力（標準入力の JSON）の読み方まで変わる。ここから hook を外から呼び、終了コードと止めの文だけを見る。
何をするか＝コマンドを1つずつ入れた入力を hook に渡す。本物のファイルは何も書かない
  （止まる側の試しは、hook が止めた記録 design_gate_fires.log に1行ずつ残る）。
使い方: python3 .claude/hooks/require_design_contract_before_run_selftest.py --selftest
"""
import json
import subprocess
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
HOOK = ROOT + "/.claude/hooks/require_design_contract_before_run.sh"
SDK = "v3-bitget-api-sdk/bitget-python-sdk-api"
NO_PY = "確定できない"
NO_ET = "1本もありません"

CASES = [
    # (名前, コマンド, 期待＝"通る" か 止めの文の一部)
    ("S1 python3 --version は通る", "python3 --version", "通る"),
    ("S2 ls …/python3 は通る", "ls -la /usr/bin/python3 2>/dev/null", "通る"),
    ("S3 grep -i python は通る", "grep -i python notes.txt", "通る"),
    ("S4 代入の F=…engine_tuner_gen.py と grep は通る",
     f"F={SDK}/scripts/priority_rebuild/engine_tuner_gen.py && grep -n run_generation $F", "通る"),
    ("S5 python3 -c は止まる", "python3 -c 'print(1)'", NO_PY),
    ("S6 ヒアドキュメントの python3 - は止まる", "python3 - <<'EOF'\nprint(1)\nEOF", NO_PY),
    ("S7 sh -c で .py を包むと止まる", "sh -c 'python3 x.py'", NO_PY),
    ("S8 変数で .py を渡すと止まる", "F=x.py; python3 $F", NO_PY),
    ("S9 find -exec python3 は止まる（find は読むだけの命令に入れない）", "find . -name a -exec python3 {} ;", NO_PY),
    ("S10 engine_tuner.py は止まる（設計書が1本も無い）",
     f"cd {SDK} && python3 scripts/priority_rebuild/engine_tuner.py --selftest", NO_ET),
]


def run(cmd: str) -> tuple:
    inp = json.dumps({"session_id": "selftest", "tool_name": "Bash", "tool_input": {"command": cmd}}, ensure_ascii=False)
    r = subprocess.run(["bash", HOOK], input=inp, capture_output=True, text=True, timeout=120, cwd=ROOT)
    return r.returncode, r.stderr


def selftest() -> int:
    ng = 0
    for name, cmd, want in CASES:
        rc, err = run(cmd)
        ok = (rc == 0) if want == "通る" else (rc == 2 and want in err)
        got = "通る" if rc == 0 else f"止まる（rc={rc}）"
        print(f"{'✅' if ok else '❌'} {name}（期待 {want}・結果 {got}）")
        ng += int(not ok)
    print(f"selftest {len(CASES) - ng}/{len(CASES)}")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 2)
