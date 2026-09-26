#!/bin/bash
# EXPECT_RC: 1
# MEANS: build_features が置き場に5分足でなく4時間足のバーを入れると、4時間足の突き合わせの番人 T-A3 が落ちた
# EXPECT_MSG: ❌ T-A3
# b108 — build_features が置き場 _H1_BASE に入れる中身を4時間足のバーに変えると、T-A3 が落ちるか（監査 CP45）
#   守っているもの＝完成の条件 #20（build_features が置き場に入れる中身が5分足であること）
#   壊し方＝`build_features` の `_H1_BASE["bars"] = bars` を `_H1_BASE["bars"] = _resample(bars, "4h")` にする。
#   期待＝4時間足に当てた1時間足の ATR% が4時間足のバーの ATR% になり、5分足から作った値と違って T-A3 が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    _H1_BASE["bars"] = bars\n'
if s.count(old) != 1:
    raise SystemExit("[b108] 壊す対象の行が1か所でない: " + old.strip())
new = '    _H1_BASE["bars"] = _resample(bars, "4h")  # b108 が壊した（置き場に4時間足のバーを入れる）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$OBS" --selftest-atr1h
finish
