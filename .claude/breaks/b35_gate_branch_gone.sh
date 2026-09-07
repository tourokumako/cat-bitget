#!/bin/bash
# b35 — 案の審査から別枠の枝を1本 消すと、T33-g（別枠3種の審査のテスト）が落ちるか
#
#   守っているもの＝監査 cp25 の §5-2「別枠の審査のテスト」（完成の条件 #1）
#   壊し方＝assert_provenance の需給の枝から、印を見る行を消す
#          （`elif not ex.demand_enabled(...)` の2行）。
#   測るもの＝`engine_tuner_gen.py --selftest-extra-gate`（T33-g だけを走らせる口）。
#   期待＝壊すと ❌ が出て終了コードが 1 になる。
#
#   ★b33 では代わりにならない（監査 cp25 の §5-2 の実測）＝b33 が測るのは候補の側
#     （--count-extra-candidates）で、審査の枝を消しても同じ結果を返す。
#
# ★2026-09-07＝測る相手を `--selftest`（全体）から `--selftest-extra-gate` に変えた。
#   なぜ（実測）＝`--selftest` の全体は **6分23秒（383秒）** かかる。承認のときに機械が
#   このプログラムを走らせる打ち切りは **120秒**（run_breaks.py の TIMEOUT_SEC）。
#   同日の承認で実際に打ち切られ、打ち切りは強制終了なので **trap の戻す処理が走らず、
#   需給の枝が消えたまま engine_tuner_gen.py に残った**
#   （記録の逐語＝「時間切れ（120秒）: b35_gate_branch_gone.sh」）。
#   `--selftest-extra-gate` は同じ判定（_check_extra_gate）を数秒で走らせるので、
#   打ち切りに掛からない＝壊したまま残る道を塞いだ。
#
# 限界（正直に書く）
#   ①壊すのは需給の枝1本だけ（レンジ幾何・時間帯の枝を消しても落ちるかは、これでは測れない）
#   ②T33-g 以外の検査は見ない
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

T="$PR/engine_tuner_gen.py"
guard "$T"

# 壊す＝審査の需給の枝から、印を見る2行を消す
python3 - "$T" <<'PYEOF'
import re
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = re.sub(
    r'\n *elif not ex\.demand_enabled\(str\(m\["demand"\]\)\):'
    r'\n *bad\(f"印が「使わない」の需給の列[^\n]*\)',
    '', s)
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b35 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

# 測る＝T33-g だけを走らせる口。壊れていれば ❌ が出て 1 になる
measure python3 "$PR/engine_tuner_gen.py" --selftest-extra-gate
finish
