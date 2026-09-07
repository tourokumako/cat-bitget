#!/bin/bash
# b38 — 順位を読む側の需給の枝を消すと、生成器の自己検査（T23-demand）が落ちるか
#
#   守っているもの＝設計書 iter="demand-in-ranking-20260907" の完成の条件 #3
#     （生成器の順位読みで需給3列が sufficiency に出て、demand_on から外すと消え、戻すと出る）。
#   壊し方＝engine_tuner_gen.ranked_materials に足した需給の枝（`if nm in iref.DEMAND_REF:` から
#          その中の `continue` まで＝5行）を消す。消すと需給の列は indicator_enabled（必ず False）で落ちる。
#   測るもの＝`engine_tuner_gen.py --selftest-rank-demand`（数秒・T23-demand の①③が ❌ になる）。
#   期待＝壊すと ❌ が出て終了コードが 1 になる。
#
# ★時間について（b35 の事故の教訓・2026-09-07）
#   承認のときの打ち切りは 120秒（run_breaks.py の TIMEOUT_SEC）。測る相手は数秒の口だけにする。
#
# 限界（正直に書く）
#   ①壊すのは ranked_materials の枝1か所だけ（_family_tf_from_col の枝を壊しても落ちるかは、この1本では測れない）
#   ②自己検査のほかの枝は見ない（終了コードだけを見る）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

T="$PR/engine_tuner_gen.py"
guard "$T"

# 壊す＝ranked_materials の需給の枝（5行）を消す
python3 - "$T" <<'PYEOF'
import re
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = re.sub(
    r'\n *if nm in iref\.DEMAND_REF:'
    r'\n *if not ex\.demand_enabled\(nm\):'
    r'\n *continue'
    r'\n *rows\.append\(\(abs\(float\(acc\) - 0\.5\), str\(col\), float\(acc\), lab, str\(hor\)\)\)'
    r'\n *continue',
    '', s, count=1)
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b38 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

# 測る＝T23-demand だけを走らせる口。①③が ❌ を出せば 1 になる
measure python3 "$PR/engine_tuner_gen.py" --selftest-rank-demand
finish
