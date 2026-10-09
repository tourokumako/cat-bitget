#!/bin/bash
# EXPECT_RC: 1
# MEANS: SMC_SWEEP確定で、終値で谷の上に戻した条件を外すと、観察の道具の自己テスト（手計算の既知答え）が落ちる
# EXPECT_MSG: SMC_SWEEP確定: 手計算の既知答えと不一致
# b153_smc_fractal_no_close_back — SMC_SWEEP確定で、終値で谷の上に戻した条件を外すと、観察の道具の自己テスト（手計算の既知答え）が落ちる（工事 m2c15-shape-structure-20261009・2026-10-09）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「SMC_SWEEP確定: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    bull = ((d.low < lo) & (d.close > lo)).astype(float)\n'
new = '    bull = (d.low < lo).astype(float)\n'
if s.count(old) != 1:
    raise SystemExit("[b153_smc_fractal_no_close_back] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish
