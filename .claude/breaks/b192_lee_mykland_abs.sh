#!/bin/bash
# EXPECT_RC: 1
# MEANS: S1 の部品（E36 の版）で、値動きの向き（符号）を落とすと、軽い口の既知答え（下げの足は −√(2/π)）が落ちる
# EXPECT_MSG: T-B1: LeeMykland_E36版16: 手計算の既知答えと不一致
# b192_lee_mykland_abs — S1 の部品（E36 の版）で、値動きの向き（符号）を落とすと、軽い口の既知答え（下げの足は −√(2/π)）が落ちる（工事 m2c15-band-s1-20261020・2026-10-20）
#   守っているもの＝完成の条件の軽い口（T-B1〜T-B4）（observe_diag.py --selftest-band）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（b1s1_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-band が「T-B1: LeeMykland_E36版16: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        return r / np.sqrt(V)\n'
new = '        return np.abs(r) / np.sqrt(V)\n'
if s.count(old) != 1:
    raise SystemExit("[b192_lee_mykland_abs] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-band
finish
