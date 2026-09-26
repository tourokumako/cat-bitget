#!/bin/bash
# EXPECT_RC: 1
# MEANS: 許容幅の ATR% を直す前の形（渡された足の ATR%）に戻すと、既知答えの番人 T-A1 が落ちた
# EXPECT_MSG: ❌ T-A1
# b104 — S-Rタッチ1時間ATR の許容幅を、2026-09-06 に外した形（渡された足の ATR%）に戻すと、T-A1 が落ちるか（M2-E-4c・束2・2026-09-26）
#   守っているもの＝完成の条件 #1（許容幅は1時間足の値動きの幅で決める・next_step §6 の136番）
#   壊し方＝`_sr_touch_atr` の `atr_pct = pd.Series(_atr_pct_1h_on(d, atr_n), index=d.index)` を
#          `atr_pct = _atr(d.high, d.low, d.close, atr_n) / d.close`（直す前の形）に戻す。
#   期待＝参照表の既知答えの見本3（1時間足と5分足で答えが割れる見本）が、倍率 1.5 の登録で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    atr_pct = pd.Series(_atr_pct_1h_on(d, atr_n), index=d.index)\n'
if s.count(old) != 1:
    raise SystemExit("[b104] 壊す対象の行が1か所でない: " + old.strip())
new = '    atr_pct = _atr(d.high, d.low, d.close, atr_n) / d.close  # b104 が壊した（直す前の形）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$OBS" --selftest-atr1h
finish
