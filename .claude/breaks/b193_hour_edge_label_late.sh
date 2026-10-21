#!/bin/bash
# EXPECT_RC: 1
# MEANS: 正時の区切りの1時間足を、区切りの最後の5分足の時刻でなく次の正時に置くと、軽い口の T-B3 が落ちる
# EXPECT_MSG: T-B3: 正時の区切りの1時間足が
# b193_hour_edge_label_late — 正時の区切りの1時間足を、区切りの最後の5分足の時刻でなく次の正時に置くと、軽い口の T-B3 が落ちる（工事 m2c15-band-s1-20261020・2026-10-20）
#   守っているもの＝完成の条件の軽い口（T-B1〜T-B4）（observe_diag.py --selftest-band）
#   壊し方＝scripts/dashboard/build_range_gate_dashboard.py の中の、下の old を new に置き換える（b1s1_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-band が「T-B3: 正時の区切りの1時間足が」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/dashboard/build_range_gate_dashboard.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    out.index = out.index + pd.Timedelta(rule) - step\n'
new = '    out.index = out.index + pd.Timedelta(rule)\n'
if s.count(old) != 1:
    raise SystemExit("[b193_hour_edge_label_late] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-band
finish
