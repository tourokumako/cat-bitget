#!/bin/bash
# EXPECT_RC: 1
# MEANS: 役割の一覧を作る道具が R-1 の区分を読まないと、食い違いが残り、R-1 の確かめ（R4）が落ちる
# EXPECT_MSG: R4: 役割の一覧の照らしが通らない
# b202_role_table_ignores_r1 — 役割の一覧を作る道具が R-1 の区分を読まないと、食い違いが残り、R-1 の確かめ（R4）が落ちる（工事 m2c15-roles-r1-20261021・2026-10-22）
#   守っているもの＝完成の条件のR-1 の確かめ（R1〜R5）（python3 .claude/state/indicator_review/roles_r1_check.py）
#   壊し方＝.claude/state/indicator_review/build_role_threshold_table.py の中の、下の old を new に置き換える（roles_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 .claude/state/indicator_review/roles_r1_check.py が「R4: 役割の一覧の照らしが通らない」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/.claude/state/indicator_review/build_role_threshold_table.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    _r1 = R1MAP.get(fam)\n'
new = '    _r1 = None\n'
if s.count(old) != 1:
    raise SystemExit("[b202_role_table_ignores_r1] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$ROOT/.claude/state/indicator_review/roles_r1_check.py"
finish
