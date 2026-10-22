#!/bin/bash
# EXPECT_RC: 1
# MEANS: 系統の区分から強さを外すと、札が強さの指標が区分の外になり、軽い口が落ちる
# EXPECT_MSG: T-L1: 系統マップに、系統の区分
# b197_lineage_kinds_no_strength — 系統の区分から強さを外すと、札が強さの指標が区分の外になり、軽い口が落ちる（工事 m2c15-roles-r1-20261021・2026-10-22）
#   守っているもの＝完成の条件の軽い口（T-L1・T-L2）（python3 scripts/priority_rebuild/observe_diag.py --selftest-lineage）
#   壊し方＝scripts/priority_rebuild/indicator_reference_diag.py の中の、下の old を new に置き換える（roles_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 scripts/priority_rebuild/observe_diag.py --selftest-lineage が「T-L1: 系統マップに、系統の区分」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicator_reference_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'LINEAGE_KINDS = ("トレンド", "強さ", "勢い", "オシレーター",'
new = 'LINEAGE_KINDS = ("トレンド", "勢い", "オシレーター",'
if s.count(old) != 1:
    raise SystemExit("[b197_lineage_kinds_no_strength] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-lineage
finish
