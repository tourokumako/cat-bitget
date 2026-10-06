#!/bin/bash
# EXPECT_RC: 1
# MEANS: AO の名前に値を入れると（AO%(5,34)）、名前の番人が落ちる
# EXPECT_MSG: ❌ 名前: AO%
# b134_ao_name_with_value — AO の名前に値を入れると（AO%(5,34)）、名前の番人が落ちる（工事 m2c15-hidden-params-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r2_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ 名前: AO%」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '_reg("AO%", "AO%", True,'
new = '_reg("AO%", "AO%(5,34)", True,'
if s.count(old) != 1:
    raise SystemExit("[b134_ao_name_with_value] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish
