#!/bin/bash
# EXPECT_RC: 1
# MEANS: 答える問いから勢いの鍵を外すと、軽い口が落ちる
# EXPECT_MSG: T-L2: 答える問いの鍵が系統の区分と違う
# b198_lineage_question_no_momentum — 答える問いから勢いの鍵を外すと、軽い口が落ちる（工事 m2c15-roles-r1-20261021・2026-10-22）
#   守っているもの＝完成の条件の軽い口（T-L1・T-L2）（python3 scripts/priority_rebuild/observe_diag.py --selftest-lineage）
#   壊し方＝scripts/priority_rebuild/indicator_reference_diag.py の中の、下の old を new に置き換える（roles_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 scripts/priority_rebuild/observe_diag.py --selftest-lineage が「T-L2: 答える問いの鍵が系統の区分と違う」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicator_reference_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "勢い": ("値動きの勢い（モメンタム）がどれくらいか",'
new = '    "勢い_": ("値動きの勢い（モメンタム）がどれくらいか",'
if s.count(old) != 1:
    raise SystemExit("[b198_lineage_question_no_momentum] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-lineage
finish
