#!/bin/bash
# EXPECT_RC: 1
# MEANS: 1時間足の値を始まりの時刻から使う（閉じる前の1時間足を使う）と、切り詰めの番人 T-A4 が落ちた
# EXPECT_MSG: ❌ T-A4
# b105 — 1時間足の ATR% の時刻を「閉じた時刻」から「始まりの時刻」に変えると、T-A4 が落ちるか（M2-E-4c・束2・2026-09-26）
#   守っているもの＝完成の条件 #2（1時間足の値は、その1時間足が閉じた時刻から使う＝未来を見ない）
#   壊し方＝`_atr_pct_1h_on` の `a.index = h1.index + pd.Timedelta("1h")` を `a.index = h1.index` にする。
#   期待＝毎時30分で切り詰めて計算し直すと、切った時点の1時間足の ATR% が全部で計算した値と違い、T-A4 が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    a.index = h1.index + pd.Timedelta("1h")'
if s.count(old) != 1:
    raise SystemExit("[b105] 壊す対象の行が1か所でない: " + old.strip())
new = '    a.index = h1.index  # b105 が壊した（始まりの時刻＝閉じる前の1時間足を使う）'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$OBS" --selftest-atr1h
finish
