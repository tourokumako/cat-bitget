#!/bin/bash
# EXPECT_RC: 1
# MEANS: 段の候補が列の数字の範囲を見ない形に戻すと、軽い口の⑭が落ちる
# EXPECT_MSG: ❌ 修正1:
# b140_group_range_ignored — 段の候補が列の数字の範囲を見ない形に戻すと、軽い口の⑭が落ちる（工事 m2c15-param-values-fix-20261007・2026-10-07）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）
#   壊し方＝scripts/priority_rebuild/engine_tuner_gen.py の中の、下の old を new に置き換える（r4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ 修正1:」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/engine_tuner_gen.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    if not param_in_range(family, m["param"], ranges)[0]:\n        return False\n'
new = '    if False and not param_in_range(family, m["param"], ranges)[0]:\n        return False\n'
if s.count(old) != 1:
    raise SystemExit("[b140_group_range_ignored] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish
