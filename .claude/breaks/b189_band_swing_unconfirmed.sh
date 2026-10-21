#!/bin/bash
# EXPECT_RC: 1
# MEANS: 帯スイングで、確定した山・谷の代わりに全部の足の高値・安値を数える（まだ確定していない山・谷も数える）と、軽い口の既知答えが落ちる
# EXPECT_MSG: T-B1: 帯スイング(144,0.0015,2): 手計算の既知答えと不一致
# b189_band_swing_unconfirmed — 帯スイングで、確定した山・谷の代わりに全部の足の高値・安値を数える（まだ確定していない山・谷も数える）と、軽い口の既知答えが落ちる（工事 m2c15-band-s1-20261020・2026-10-20）
#   守っているもの＝完成の条件の軽い口（T-B1〜T-B4）（observe_diag.py --selftest-band）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（b1s1_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-band が「T-B1: 帯スイング(144,0.0015,2): 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    hv = _fractal_marks(d.high, k, True)[0].to_numpy(float)     # 帯の上の線＝確定した山（前後 k 本で確定してから使う）\n    lv = _fractal_marks(d.low, k, False)[0].to_numpy(float)     # 帯の下の線＝確定した谷\n'
new = '    hv = d.high.to_numpy(float)\n    lv = d.low.to_numpy(float)\n'
if s.count(old) != 1:
    raise SystemExit("[b189_band_swing_unconfirmed] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-band
finish
