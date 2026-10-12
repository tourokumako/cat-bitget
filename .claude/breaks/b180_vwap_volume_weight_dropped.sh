#!/bin/bash
# EXPECT_RC: 1
# MEANS: VWAP の分子の出来高の重みを外すと、最後の1本だけ出来高 9 の既知答えで検査3 が落ちる（出来高が全部 1 の足では見分けられない）
# EXPECT_MSG: close vs VWAP%288: 手計算の既知答えと不一致
# b180_vwap_volume_weight_dropped — VWAP の分子の出来高の重みを外すと、最後の1本だけ出来高 9 の既知答えで検査3 が落ちる（出来高が全部 1 の足では見分けられない）（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「close vs VWAP%288: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '_reg("close vs VWAP%", "close vs VWAP%{}", True, lambda d, n: (d.close / ((d.close * d.volume).rolling(n).sum()\n     / d.volume.rolling(n).sum().replace(0, np.nan)) - 1) * 100)\n'
new = '_reg("close vs VWAP%", "close vs VWAP%{}", True, lambda d, n: (d.close / ((d.close * (d.volume * 0 + 1.0)).rolling(n).sum()\n     / d.volume.rolling(n).sum().replace(0, np.nan)) - 1) * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b180_vwap_volume_weight_dropped] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish
