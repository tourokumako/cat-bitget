#!/bin/bash
# EXPECT_RC: 1
# MEANS: ADX の札をトレンドに戻すと、R-1 の確かめ（R1）が落ちる
# EXPECT_MSG: R1: ADX の札が トレンド
# b199_adx_back_to_trend — ADX の札をトレンドに戻すと、R-1 の確かめ（R1）が落ちる（工事 m2c15-roles-r1-20261021・2026-10-22）
#   守っているもの＝完成の条件のR-1 の確かめ（R1〜R5）（python3 .claude/state/indicator_review/roles_r1_check.py）
#   壊し方＝scripts/priority_rebuild/indicator_reference_diag.py の中の、下の old を new に置き換える（roles_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 .claude/state/indicator_review/roles_r1_check.py が「R1: ADX の札が トレンド」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
#   ★2026-10-22（工事 m2c15-single-source-20261022）＝札の辞書（FAMILY_LINEAGE）が INDICATOR_TABLE から作る形になったので、壊す文字を表の ADX の行（'札' の欄）にした（壊し方と測る物は同じ）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicator_reference_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = "    'ADX': {'役割': {'区分': ['強さ'], '出どころ': 'R-1（封つき r1_role_map.json・CC の調べ（cc_ans04・照らし一致））'}, '札': '強さ'"
new = "    'ADX': {'役割': {'区分': ['強さ'], '出どころ': 'R-1（封つき r1_role_map.json・CC の調べ（cc_ans04・照らし一致））'}, '札': 'トレンド'"
if s.count(old) != 1:
    raise SystemExit("[b199_adx_back_to_trend] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$ROOT/.claude/state/indicator_review/roles_r1_check.py"
finish
