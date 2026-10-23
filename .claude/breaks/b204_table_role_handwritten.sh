#!/bin/bash
# EXPECT_RC: 1
# MEANS: 表の役割を手で書き替えると、資料から作り直した物と違い、表の照らしが落ちる
# EXPECT_MSG: ④表の中身が、資料から作り直した物と違う
# b204_table_role_handwritten — 表の役割を手で書き替えると、資料から作り直した物と違い、表の照らしが落ちる（工事 m2c15-single-source-20261022・2026-10-22）
#   守っているもの＝完成の条件の表の照らし（①〜⑥）（python3 scripts/priority_rebuild/gen_indicator_table.py --verify）
#   壊し方＝scripts/priority_rebuild/indicator_reference_diag.py の中の、下の old を new に置き換える（ss_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 scripts/priority_rebuild/gen_indicator_table.py --verify が「④表の中身が、資料から作り直した物と違う」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicator_reference_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = "    'ADX': {'役割': {'区分': ['強さ']"
new = "    'ADX': {'役割': {'区分': ['向き']"
if s.count(old) != 1:
    raise SystemExit("[b204_table_role_handwritten] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/gen_indicator_table.py" --verify
finish
