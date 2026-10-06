#!/bin/bash
# EXPECT_RC: 1
# MEANS: 設定の範囲を、残す名前 ROC24 を含まない形（上限 14）に戻すと、範囲の番人（⑬）が落ちる
# EXPECT_MSG: ❌ P-2:
# b139_range_excludes_keep — 設定の範囲を、残す名前 ROC24 を含まない形（上限 14）に戻すと、範囲の番人（⑬）が落ちる（工事 m2c15-param-values-20261006・2026-10-06）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）
#   壊し方＝scripts/priority_rebuild/recipes/search_limits.json の中の、下の old を new に置き換える（r3_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ P-2:」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/recipes/search_limits.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "ROC": [{"kind": "int", "lo": 9, "hi": 24}],\n'
new = '    "ROC": [{"kind": "int", "lo": 9, "hi": 14}],\n'
if s.count(old) != 1:
    raise SystemExit("[b139_range_excludes_keep] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish
