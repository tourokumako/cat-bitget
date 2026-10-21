#!/bin/bash
# EXPECT_RC: 1
# MEANS: E36 が Lee-Mykland の式を自前で持つ（材料の表の関数を呼ばない）と、軽い口の T-B4 が落ちる
# EXPECT_MSG: T-B4: E36 の Lee-Mykland の式が
# b194_e36_own_spike_stat — E36 が Lee-Mykland の式を自前で持つ（材料の表の関数を呼ばない）と、軽い口の T-B4 が落ちる（工事 m2c15-band-s1-20261020・2026-10-20）
#   守っているもの＝完成の条件の軽い口（T-B1〜T-B4）（observe_diag.py --selftest-band）
#   壊し方＝scripts/priority_rebuild/e36_short_oscillation.py の中の、下の old を new に置き換える（b1s1_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-band が「T-B4: E36 の Lee-Mykland の式が」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/e36_short_oscillation.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'from observe_diag import spike_threshold, spike_stat   # noqa: E402\n'
new = 'from observe_diag import spike_threshold   # noqa: E402\nspike_stat = lambda c, K: np.zeros(len(c))   # noqa: E731\n'
if s.count(old) != 1:
    raise SystemExit("[b194_e36_own_spike_stat] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-band
finish
