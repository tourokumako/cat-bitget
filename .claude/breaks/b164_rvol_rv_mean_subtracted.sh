#!/bin/bash
# EXPECT_RC: 1
# MEANS: realized_vol_rv を平均を引く形に戻すと、観察の道具の自己テスト（一定の割合で増える足の既知答え）が落ちる
# EXPECT_MSG: realized_vol_rv20: 手計算の既知答えと不一致
# b164_rvol_rv_mean_subtracted — realized_vol_rv を平均を引く形に戻すと、観察の道具の自己テスト（一定の割合で増える足の既知答え）が落ちる（工事 m2c15-formula-textbook-20261011・2026-10-11）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「realized_vol_rv20: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '     np.sqrt((np.log(d.close / d.close.shift()) ** 2).rolling(n).sum() / n) * 100)\n'
new = '     np.log(d.close / d.close.shift()).rolling(n).std(ddof=0) * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b164_rvol_rv_mean_subtracted] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish
