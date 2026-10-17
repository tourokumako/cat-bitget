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
    # ★2026-10-18（191回目・まこさん「hookの不具合はすぐに修正して」）＝確かめの旗の免除で開く .py の起点のフォルダ。
    #   直す前は、hook が動いているフォルダから相対パスを開き、シェルが別のフォルダに居ると --selftest も止まった。
    #   （名前, コマンド, 期待, 入力の cwd, hook を動かすフォルダ）
    ("S11 シェルが別のフォルダでも、cd の後の相対パスの --selftest は通る",
     f"cd {ROOT} && python3 .claude/tools/gen_acceptance.py --selftest", "通る", "/tmp", "/tmp"),
    ("S12 入力の cwd が根なら、hook が別のフォルダで動いても、相対パスの --selftest は通る",
     "python3 .claude/tools/gen_acceptance.py --selftest", "通る", ROOT, "/tmp"),
    ("S13 cd をたどっても、旗を持たない engine_tuner.py は今までどおり止まる",
     f"cd {ROOT}/{SDK} && python3 scripts/priority_rebuild/engine_tuner.py --selftest", NO_ET, "/tmp", "/tmp"),
]


def run(cmd: str, in_cwd: str = None, proc_cwd: str = ROOT) -> tuple:
    inp = {"session_id": "selftest", "tool_name": "Bash", "tool_input": {"command": cmd}}
    if in_cwd:
        inp["cwd"] = in_cwd
    r = subprocess.run(["bash", HOOK], input=json.dumps(inp, ensure_ascii=False), capture_output=True, text=True,
                       timeout=120, cwd=proc_cwd)
    return r.returncode, r.stderr


def selftest() -> int:
    ng = 0
    for name, cmd, want, *where in CASES:
        rc, err = run(cmd, *where)
        ok = (rc == 0) if want == "通る" else (rc == 2 and want in err)
        got = "通る" if rc == 0 else f"止まる（rc={rc}）"
        print(f"{'✅' if ok else '❌'} {name}（期待 {want}・結果 {got}）")
        ng += int(not ok)
    print(f"selftest {len(CASES) - ng}/{len(CASES)}")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 2)
