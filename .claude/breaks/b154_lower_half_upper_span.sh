#!/bin/bash
# EXPECT_RC: 1
# MEANS: 下半分位置を上半分の幅で割る形（帯内位置% と同じ）に戻すと、観察の道具の自己テスト（レンジ幾何の既知答え）が落ちる
# EXPECT_MSG: レンジ幾何 既知答え不一致: 下半分位置
# b154_lower_half_upper_span — 下半分位置を上半分の幅で割る形（帯内位置% と同じ）に戻すと、観察の道具の自己テスト（レンジ幾何の既知答え）が落ちる（工事 m2c15-shape-structure-20261009・2026-10-09）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「レンジ幾何 既知答え不一致: 下半分位置」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        low = np.where(np.isfinite(dn) & (dn > 0), (c - mid) / dn, np.nan)\n'
new = '        low = np.where(np.isfinite(span) & (span > 0), (c - mid) / span, np.nan)\n'
if s.count(old) != 1:
    raise SystemExit("[b154_lower_half_upper_span] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish
