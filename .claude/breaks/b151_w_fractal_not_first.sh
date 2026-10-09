#!/bin/bash
# EXPECT_RC: 1
# MEANS: W字確定谷の「ネックを最初に上抜けた足だけ 1」を外す（条件が続く間ずっと1）と、観察の道具の自己テスト（手計算の既知答え）が落ちる
# EXPECT_MSG: W字確定谷(24,0.003): 手計算の既知答えと不一致
# b151_w_fractal_not_first — W字確定谷の「ネックを最初に上抜けた足だけ 1」を外す（条件が続く間ずっと1）と、観察の道具の自己テスト（手計算の既知答え）が落ちる（工事 m2c15-shape-structure-20261009・2026-10-09）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「W字確定谷(24,0.003): 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        if ca[i] > neck and not (ca[j2 + 1:i] > neck).any():\n'
new = '        if ca[i] > neck:\n'
if s.count(old) != 1:
    raise SystemExit("[b151_w_fractal_not_first] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish
