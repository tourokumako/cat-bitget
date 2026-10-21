#!/bin/bash
# EXPECT_RC: 1
# MEANS: 帯pivot・帯VA で、終値が上の線より下という条件を外すと、軽い口の既知答え（終値が R1 より上）が落ちる
# EXPECT_MSG: T-B1: 帯pivot(0.0015): 手計算の既知答えと不一致
# b191_band_lines_no_top — 帯pivot・帯VA で、終値が上の線より下という条件を外すと、軽い口の既知答え（終値が R1 より上）が落ちる（工事 m2c15-band-s1-20261020・2026-10-20）
#   守っているもの＝完成の条件の軽い口（T-B1〜T-B4）（observe_diag.py --selftest-band）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（b1s1_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-band が「T-B1: 帯pivot(0.0015): 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        ok = (bot < ca) & (ca < top) & ((top - bot) / ca >= floor)\n'
new = '        ok = (bot < ca) & ((top - bot) / ca >= floor)\n'
if s.count(old) != 1:
    raise SystemExit("[b191_band_lines_no_top] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-band
finish
