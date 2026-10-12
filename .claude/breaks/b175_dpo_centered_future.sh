#!/bin/bash
# EXPECT_RC: 1
# MEANS: DPO% を未来を見る版（centered=True）に戻すと、1本ごとに 1 上げる足の既知答えで検査3 が落ちる
# EXPECT_MSG: DPO%20: 手計算の既知答えと不一致
# b175_dpo_centered_future — DPO% を未来を見る版（centered=True）に戻すと、1本ごとに 1 上げる足の既知答えで検査3 が落ちる（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「DPO%20: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '     _pta6.dpo(close=d.close, length=n, centered=False) / d.close * 100)\n'
new = '     _pta6.dpo(close=d.close, length=n, centered=True) / d.close * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b175_dpo_centered_future] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish
