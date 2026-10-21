#!/bin/bash
# EXPECT_RC: 1
# MEANS: S1 の部品（論文の版）で、ふだんの揺れに今の1本を入れる（Lee-Mykland 2008 の式(8)と違う作り）と、軽い口の既知答え（最後の1本だけ大きく動く足）が落ちる
# EXPECT_MSG: T-B1: LeeMykland16: 手計算の既知答えと不一致
# b195_lee_mykland_paper_window — S1 の部品（論文の版）で、ふだんの揺れに今の1本を入れる（Lee-Mykland 2008 の式(8)と違う作り）と、軽い口の既知答え（最後の1本だけ大きく動く足）が落ちる（工事 m2c15-band-s1-20261020・2026-10-20）
#   守っているもの＝完成の条件の軽い口（T-B1〜T-B4）（observe_diag.py --selftest-band）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（b1s1_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-band が「T-B1: LeeMykland16: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    bp_prev = pd.Series(bpv).rolling(K - 2).sum().shift(1).to_numpy()   # Σ_{j=i−K+2}^{i−1}（K−2 項・今の1本の項を入れない）\n    V_lm = (math.pi / (2.0 * (K - 2))) * bp_prev\n'
new = '    bp_prev = pd.Series(bpv).rolling(K - 1).sum().to_numpy()\n    V_lm = (math.pi / (2.0 * (K - 1))) * bp_prev\n'
if s.count(old) != 1:
    raise SystemExit("[b195_lee_mykland_paper_window] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-band
finish
