#!/bin/bash
# EXPECT_RC: 1
# MEANS: T3 の範囲の上限を、カタログの数字 50・200 を含まない 34 に戻すと、範囲の番人（⑬）が落ちる
# EXPECT_MSG: ❌ P-2: close vs T3%
# b141_catalog_out_of_range — T3 の範囲の上限を、カタログの数字 50・200 を含まない 34 に戻すと、範囲の番人（⑬）が落ちる（工事 m2c15-param-values-fix-20261007・2026-10-07）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）
#   壊し方＝scripts/priority_rebuild/recipes/search_limits.json の中の、下の old を new に置き換える（r4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ P-2: close vs T3%」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/recipes/search_limits.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "close vs T3%": [{"kind": "int", "lo": 8, "hi": 200}],\n'
new = '    "close vs T3%": [{"kind": "int", "lo": 8, "hi": 34}],\n'
if s.count(old) != 1:
    raise SystemExit("[b141_catalog_out_of_range] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish
