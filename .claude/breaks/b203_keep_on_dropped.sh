#!/bin/bash
# EXPECT_RC: 1
# MEANS: 決定アの源4（mako の欄）を入れないと、札が構造・位置から外れた種類が印で「使わない」になり、R-1 の確かめ（R5）が落ちる
# EXPECT_MSG: R5: 印を作り直すと「使わない」になる種類が
# b203_keep_on_dropped — 決定アの源4（mako の欄）を入れないと、札が構造・位置から外れた種類が印で「使わない」になり、R-1 の確かめ（R5）が落ちる（工事 m2c15-roles-r1-20261021・2026-10-22）
#   守っているもの＝完成の条件のR-1 の確かめ（R1〜R5）（python3 .claude/state/indicator_review/roles_r1_check.py）
#   壊し方＝scripts/priority_rebuild/indicator_reference_diag.py の中の、下の old を new に置き換える（roles_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 .claude/state/indicator_review/roles_r1_check.py が「R5: 印を作り直すと「使わない」になる種類が」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicator_reference_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        _e["mako"] = MAKO_R1\n'
new = '        pass\n'
if s.count(old) != 1:
    raise SystemExit("[b203_keep_on_dropped] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$ROOT/.claude/state/indicator_review/roles_r1_check.py"
finish
