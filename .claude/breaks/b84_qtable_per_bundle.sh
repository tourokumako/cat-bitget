#!/bin/bash
# EXPECT_RC: 1
# MEANS: 解決表を束ごとに作り直す形に戻すと、T38① が「くり返しの中で作っている」で落ちた
# EXPECT_MSG: T38
# b84 — 解決表を束ごとに作り直す形に戻すと、検査が落ちるか
#   守っているもの＝完成の条件 条件10（分位の解決表を、束の本数によらず1回だけ作る）
#   壊し方＝くり返しの外で1回 作った表を使い回す行を、くり返しの中で作り直す形に戻す。
#   期待＝自己テスト T38 が落ちる（終了コード 1）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        qt = qt_all'
if old not in s:
    raise SystemExit("[b84] 壊す対象の行が見つからない: " + old)
new = '        qt = _qtable(df, geo, [rec], start, end)  # b84 が壊した（束ごとに作り直す）'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
