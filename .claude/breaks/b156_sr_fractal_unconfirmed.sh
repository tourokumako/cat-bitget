#!/bin/bash
# EXPECT_RC: 1
# MEANS: S-Rタッチ確定数で、山を確定した足でなく山そのものの足に置く（まだ確定していない山を使う＝未来を見る）と、観察の道具の自己テスト（手計算の既知答え）が落ちる
# EXPECT_MSG: S-Rタッチ確定数(144,0.0015): 手計算の既知答えと不一致
# b156_sr_fractal_unconfirmed — S-Rタッチ確定数で、山を確定した足でなく山そのものの足に置く（まだ確定していない山を使う＝未来を見る）と、観察の道具の自己テスト（手計算の既知答え）が落ちる（工事 m2c15-shape-structure-20261009・2026-10-09）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「S-Rタッチ確定数(144,0.0015): 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    hv = _fractal_marks(d.high, k, True)[0].to_numpy(float)\n'
new = '    hv = _fractal_marks(d.high, k, True)[0].shift(-int(k)).to_numpy(float)\n'
if s.count(old) != 1:
    raise SystemExit("[b156_sr_fractal_unconfirmed] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish
