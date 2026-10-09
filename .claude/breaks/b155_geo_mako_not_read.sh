#!/bin/bash
# EXPECT_RC: 1
# MEANS: geo_on が源4 のレンジ幾何（mako の欄）を読まない形に戻すと、印を作る道具の自己テスト T12 が落ちる
# EXPECT_MSG: T12 まこさんが個別に決めたレンジ幾何の列は必ず使う → ng
# b155_geo_mako_not_read — geo_on が源4 のレンジ幾何（mako の欄）を読まない形に戻すと、印を作る道具の自己テスト T12 が落ちる（工事 m2c15-shape-structure-20261009・2026-10-09）
#   守っているもの＝完成の条件の印を作る道具の自己テスト（gen_indicator_switch.py --selftest）
#   壊し方＝scripts/priority_rebuild/gen_indicator_switch.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝gen_indicator_switch.py --selftest が「T12 まこさんが個別に決めたレンジ幾何の列は必ず使う → ng」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/gen_indicator_switch.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        "geo_on": sorted(law_g | id_g | mako_g),\n'
new = '        "geo_on": sorted(law_g | id_g),\n'
if s.count(old) != 1:
    raise SystemExit("[b155_geo_mako_not_read] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/gen_indicator_switch.py" --selftest
finish
