#!/bin/bash
# EXPECT_RC: 1
# MEANS: 出口の枝 REVERSE_IND の使える系統から強さを外すと、ADX などが出口の枝を失い、R-1 の確かめ（R3）が落ちる
# EXPECT_MSG: R3: ADX（トレンド→強さ）が使えなくなる役割
# b201_exit_no_strength — 出口の枝 REVERSE_IND の使える系統から強さを外すと、ADX などが出口の枝を失い、R-1 の確かめ（R3）が落ちる（工事 m2c15-roles-r1-20261021・2026-10-22）
#   守っているもの＝完成の条件のR-1 の確かめ（R1〜R5）（python3 .claude/state/indicator_review/roles_r1_check.py）
#   壊し方＝.claude/ratchet/exit_families_rules.json の中の、下の old を new に置き換える（roles_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 .claude/state/indicator_review/roles_r1_check.py が「R3: ADX（トレンド→強さ）が使えなくなる役割」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/.claude/ratchet/exit_families_rules.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            "構造・位置",\n            "強さ",\n            "勢い"\n          ],\n          "reverse_of_side": true\n'
new = '            "構造・位置",\n            "勢い"\n          ],\n          "reverse_of_side": true\n'
if s.count(old) != 1:
    raise SystemExit("[b201_exit_no_strength] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$ROOT/.claude/state/indicator_review/roles_r1_check.py"
finish
