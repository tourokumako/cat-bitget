#!/bin/bash
# EXPECT_RC: 1
# MEANS: 許容幅を上下限 0.15%〜0.6% で挟まないと、既知答えの番人 T-A1 が落ちた
# EXPECT_MSG: ❌ T-A1
# b106 — S-Rタッチ1時間ATR の許容幅を上下限で挟む行を外すと、T-A1 が落ちるか（M2-E-4c・束2・2026-09-26）
#   守っているもの＝完成の条件 #3（許容幅を 0.15%〜0.6% に収める）
#   壊し方＝`_sr_touch_atr` の `tol = (k * atr_pct).clip(lower=_SR_ATR_TOL_LO, upper=_SR_ATR_TOL_HI)` を
#          `tol = k * atr_pct` にする。
#   期待＝参照表の既知答えの見本1（下端に張り付く）と見本2（上端に張り付く）が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    tol = (k * atr_pct).clip(lower=_SR_ATR_TOL_LO, upper=_SR_ATR_TOL_HI)\n'
if s.count(old) != 1:
    raise SystemExit("[b106] 壊す対象の行が1か所でない: " + old.strip())
new = '    tol = k * atr_pct  # b106 が壊した（上下限で挟まない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$OBS" --selftest-atr1h
finish
