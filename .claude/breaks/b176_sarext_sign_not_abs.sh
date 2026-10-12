#!/bin/bash
# EXPECT_RC: 1
# MEANS: SAREXT の絶対値を外す（売り側が負の数のまま）と、下げ続ける足の既知答えで検査3 が落ちる＝監査 CP60 の符号の誤りを捕まえる（直す前は値段が一定の足だけで通った）
# EXPECT_MSG: close vs SAREXT%: 手計算の既知答えと不一致
# b176_sarext_sign_not_abs — SAREXT の絶対値を外す（売り側が負の数のまま）と、下げ続ける足の既知答えで検査3 が落ちる＝監査 CP60 の符号の誤りを捕まえる（直す前は値段が一定の足だけで通った）（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「close vs SAREXT%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'accelerationmaxshort=accelerationmaxshort).abs() - 1) * 100)\n'
new = 'accelerationmaxshort=accelerationmaxshort) - 1) * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b176_sarext_sign_not_abs] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish
