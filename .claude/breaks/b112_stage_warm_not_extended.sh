#!/bin/bash
# EXPECT_RC: 1
# MEANS: 動く線を使う走行の余白を延ばさない形にすると、T47 が「余白が 60日＋6か月にならない」で落ちた
# EXPECT_MSG: ❌ T47
# b112 — stage_warm が余白を延ばさず、いまの余白をそのまま返す形にすると、T47 が落ちるか（M2-E-4e・2026-09-27）
#   守っているもの＝完成の条件 #4（動く線を使う走行の余白＝いまの余白＋6か月・まこさん決定「余白の直し方→C」）
#   壊し方＝`stage_warm` の最後の return を `    return base_warm` にする。
#   期待＝組む側の自己テスト T47 の⑤が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    return base_warm + pd.Timedelta(minutes=pre_win_bars({"months": max(months)}) * _EXEC_BAR_MIN)\n'
if s.count(old) != 1:
    raise SystemExit("[b112] 壊す対象の行が1か所でない: " + old.strip())
new = '    return base_warm  # b112 が壊した（余白を延ばさない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$GEN" --selftest
finish

