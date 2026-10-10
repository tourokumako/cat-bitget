#!/bin/bash
# EXPECT_RC: 1
# MEANS: THERMO原作% を絶対値（ライブラリの版）に戻すと、観察の道具の自己テスト（内はらみ足の既知答え）が落ちる
# EXPECT_MSG: THERMO原作%: 手計算の既知答えと不一致
# b161_thermo_orig_abs — THERMO原作% を絶対値（ライブラリの版）に戻すと、観察の道具の自己テスト（内はらみ足の既知答え）が落ちる（工事 m2c15-formula-textbook-20261011・2026-10-11）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「THERMO原作%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    return np.maximum((d.high - d.high.shift(1)).clip(lower=0), (d.low.shift(1) - d.low).clip(lower=0))\n'
new = '    return np.maximum((d.high - d.high.shift(1)).abs(), (d.low.shift(1) - d.low).abs())\n'
if s.count(old) != 1:
    raise SystemExit("[b161_thermo_orig_abs] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish
