#!/bin/bash
# EXPECT_RC: 1
# MEANS: StochRSI素%K をならす形（k=3）に戻すと、観察の道具の自己テスト（教科書の独立実装）が落ちる
# EXPECT_MSG: StochRSI素%K14: 教科書の独立実装と不一致
# b162_stochrsi_raw_smoothed — StochRSI素%K をならす形（k=3）に戻すと、観察の道具の自己テスト（教科書の独立実装）が落ちる（工事 m2c15-formula-textbook-20261011・2026-10-11）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「StochRSI素%K14: 教科書の独立実装と不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=1).iloc[:, 0])\n'
new = '     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=3).iloc[:, 0])\n'
if s.count(old) != 1:
    raise SystemExit("[b162_stochrsi_raw_smoothed] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish
