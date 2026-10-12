#!/bin/bash
# EXPECT_RC: 1
# MEANS: ALMA の重みを逆向き（ライブラリの元の 0.85）に戻すと、定義から導いた既知答え（1本ごとに 1 上げる足の遅れ）で検査3 が落ちる＝監査 CP60 が見つけた向きの誤りを捕まえる
# EXPECT_MSG: close vs ALMA%9: 手計算の既知答えと不一致
# b172_alma_weights_reversed — ALMA の重みを逆向き（ライブラリの元の 0.85）に戻すと、定義から導いた既知答え（1本ごとに 1 上げる足の遅れ）で検査3 が落ちる＝監査 CP60 が見つけた向きの誤りを捕まえる（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「close vs ALMA%9: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    ("ALMA", lambda d, n, distribution_offset=0.15, sigma=None: _pta6.alma(close=d.close, length=n, distribution_offset=distribution_offset, sigma=sigma)),\n'
new = '    ("ALMA", lambda d, n, distribution_offset=0.85, sigma=None: _pta6.alma(close=d.close, length=n, distribution_offset=distribution_offset, sigma=sigma)),\n'
if s.count(old) != 1:
    raise SystemExit("[b172_alma_weights_reversed] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish
