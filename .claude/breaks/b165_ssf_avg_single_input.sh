#!/bin/bash
# EXPECT_RC: 1
# MEANS: close vs SSF平均% の入力を1本（今の版）に戻すと、観察の道具の自己テスト（教科書の独立実装）が落ちる
# EXPECT_MSG: close vs SSF平均%20: 教科書の独立実装と不一致
# b165_ssf_avg_single_input — close vs SSF平均% の入力を1本（今の版）に戻すと、観察の道具の自己テスト（教科書の独立実装）が落ちる（工事 m2c15-formula-textbook-20261011・2026-10-11）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「close vs SSF平均%20: 教科書の独立実装と不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        out[i] = c1 * (v[i] + v[i - 1]) / 2.0 + c2 * out[i - 1] + c3 * out[i - 2]\n'
new = '        out[i] = c1 * v[i] + c2 * out[i - 1] + c3 * out[i - 2]\n'
if s.count(old) != 1:
    raise SystemExit("[b165_ssf_avg_single_input] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish
