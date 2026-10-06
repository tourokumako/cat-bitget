#!/bin/bash
# EXPECT_RC: 1
# MEANS: CKSP を引数なしの呼び方（値は本の形・ならし方は TradingView の形の、混ざった組）に戻すと、CKSP の番人が落ちる
# EXPECT_MSG: ❌ CKSP:
# b133_cksp_mixed_set — CKSP を引数なしの呼び方（値は本の形・ならし方は TradingView の形の、混ざった組）に戻すと、CKSP の番人が落ちる（工事 m2c15-hidden-params-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r2_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ CKSP:」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'close=d.close, tvmode=True, **kw)'
new = 'close=d.close, **kw)'
if s.count(old) != 1:
    raise SystemExit("[b133_cksp_mixed_set] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish
