#!/bin/bash
# EXPECT_RC: 1
# MEANS: 検査2 から、上位足のずらし bar_close の形の確かめを外すと、検査2 の番人が落ちる
# EXPECT_MSG: ❌ 検査2:
# b136_insp2_bar_close_dropped — 検査2 から、上位足のずらし bar_close の形の確かめを外すと、検査2 の番人が落ちる（工事 m2c15-hidden-params-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r2_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ 検査2:」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    leak = _insp_close_leak(shift=True) + _insp_close_leak(shift=True, mode="bar_close")   # ★K-8＝ずらし2種\n'
new = '    leak = _insp_close_leak(shift=True)\n'
if s.count(old) != 1:
    raise SystemExit("[b136_insp2_bar_close_dropped] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish
