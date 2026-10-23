#!/bin/bash
# EXPECT_RC: 1
# MEANS: 監査に出す前のチェックから表の照らしを外すと、番人 P8 が落ちる
# EXPECT_MSG: P8: 監査の前に走らせる一覧から外されている
# b207_table_check_dropped — 監査に出す前のチェックから表の照らしを外すと、番人 P8 が落ちる（工事 m2c15-single-source-20261022・2026-10-22）
#   守っているもの＝完成の条件の監査に出す前のチェックの番人 P8（--selftest-p8）（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --selftest-p8）
#   壊し方＝.claude/tools/pre_audit_check.py の中の、下の old を new に置き換える（ss_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --selftest-p8 が「P8: 監査の前に走らせる一覧から外されている」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$ROOT/.claude/tools/pre_audit_check.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "gen_indicator_table.py --verify",\n'
new = ''
if s.count(old) != 1:
    raise SystemExit("[b207_table_check_dropped] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$ROOT/.claude/tools/pre_audit_check.py" --selftest-p8
finish
