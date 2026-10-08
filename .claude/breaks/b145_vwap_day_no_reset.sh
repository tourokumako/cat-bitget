#!/bin/bash
# EXPECT_RC: 1
# MEANS: 当日VWAP の積み上げを日で区切らない形に戻すと、観察の道具の自己テスト（参照表の手計算の既知答え）が落ちる
# EXPECT_MSG: close vs 当日VWAP%: 手計算の既知答えと不一致
# b145_vwap_day_no_reset — 当日VWAP の積み上げを日で区切らない形に戻すと、観察の道具の自己テスト（参照表の手計算の既知答え）が落ちる（工事 m2c15-period-textbook-20261007・2026-10-07）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3a_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「close vs 当日VWAP%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    return (tp * d.volume).groupby(key).cumsum() / d.volume.groupby(key).cumsum().replace(0, np.nan)\n'
new = '    return (tp * d.volume).cumsum() / d.volume.cumsum().replace(0, np.nan)\n'
if s.count(old) != 1:
    raise SystemExit("[b145_vwap_day_no_reset] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish
