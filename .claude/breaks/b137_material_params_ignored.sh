#!/bin/bash
# EXPECT_RC: 1
# MEANS: build_catalog が指標ごとの一覧を読まず、ほかの指標の期間の一覧で作ると、カタログを作る所が止まる（軽い口が落ちる）
# EXPECT_MSG: [材料カタログ] 指標ごとの一覧 material_params の種類が、カタログを作る所で1度も出てこない
# b137_material_params_ignored — build_catalog が指標ごとの一覧を読まず、ほかの指標の期間の一覧で作ると、カタログを作る所が止まる（軽い口が落ちる）（工事 m2c15-param-values-20261006・2026-10-06）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r3_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「[材料カタログ] 指標ごとの一覧 material_params の種類が、カタログを作る所で1度も出てこない」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        if family in _per:\n'
new = '        if False and family in _per:\n'
if s.count(old) != 1:
    raise SystemExit("[b137_material_params_ignored] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish
