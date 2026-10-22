#!/bin/bash
# EXPECT_RC: 1
# MEANS: 型の表の環境から勢いを外すと、MACD などが環境の役割を失い、R-1 の確かめ（R3）が落ちる
# EXPECT_MSG: R3: MACD線%（トレンド→勢い）が使えなくなる役割
# b200_env_no_momentum — 型の表の環境から勢いを外すと、MACD などが環境の役割を失い、R-1 の確かめ（R3）が落ちる（工事 m2c15-roles-r1-20261021・2026-10-22）
#   守っているもの＝完成の条件のR-1 の確かめ（R1〜R5）（python3 .claude/state/indicator_review/roles_r1_check.py）
#   壊し方＝scripts/priority_rebuild/gen_signal_families.py の中の、下の old を new に置き換える（roles_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 .claude/state/indicator_review/roles_r1_check.py が「R3: MACD線%（トレンド→勢い）が使えなくなる役割」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/gen_signal_families.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '                    lineages=["トレンド", "ボラ", "時間帯", "強さ", "勢い"], tfs="all",\n'
new = '                    lineages=["トレンド", "ボラ", "時間帯", "強さ"], tfs="all",\n'
if s.count(old) != 1:
    raise SystemExit("[b200_env_no_momentum] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$ROOT/.claude/state/indicator_review/roles_r1_check.py"
finish
