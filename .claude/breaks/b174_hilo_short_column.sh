#!/bin/bash
# EXPECT_RC: 1
# MEANS: HILO の線を売り側の列に差し替えると、1本ごとに 1 上げる足の既知答え（終値 − 11 の線）で検査3 が落ちる
# EXPECT_MSG: close vs HILO%: 手計算の既知答えと不一致
# b174_hilo_short_column — HILO の線を売り側の列に差し替えると、1本ごとに 1 上げる足の既知答え（終値 − 11 の線）で検査3 が落ちる（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「close vs HILO%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '                                                                              close=d.close, high_length=high_length, low_length=low_length).iloc[:, 0] - 1) * 100)\n'
new = '                                                                              close=d.close, high_length=high_length, low_length=low_length).iloc[:, 2] - 1) * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b174_hilo_short_column] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish
