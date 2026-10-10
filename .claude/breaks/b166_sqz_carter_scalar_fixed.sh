#!/bin/bash
# EXPECT_RC: 1
# MEANS: SQZ_ON_Carter の kc_scalar を使わず 1.5 を固定で書くと、観察の道具の自己テストの軽い口（名前に出さない引数の番人⑥＝selftest_catalog）が落ちる
# EXPECT_MSG: 名前に出さない引数: SQZ_ON_Carter の kc_scalar を変えても列が変わらない
# b166_sqz_carter_scalar_fixed — SQZ_ON_Carter の kc_scalar を使わず 1.5 を固定で書くと、観察の道具の自己テストの軽い口（名前に出さない引数の番人⑥＝selftest_catalog）が落ちる（工事 m2c15-formula-textbook-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_catalog の番人⑥）（observe_diag.py --selftest-catalog）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「名前に出さない引数: SQZ_ON_Carter の kc_scalar を変えても列が変わらない」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    on = ((mid - bb_std * sd) > (km - kc_scalar * atr)) & ((mid + bb_std * sd) < (km + kc_scalar * atr))\n'
new = '    on = ((mid - bb_std * sd) > (km - 1.5 * atr)) & ((mid + bb_std * sd) < (km + 1.5 * atr))\n'
if s.count(old) != 1:
    raise SystemExit("[b166_sqz_carter_scalar_fixed] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish
