#!/bin/bash
# EXPECT_RC: 1
# MEANS: 部品 ts_pos の最小からいまのバーを外すと、T47 が「既知答えと違う」で落ちた
# EXPECT_MSG: ❌ T47
# b111 — 実行器の _apply_pre の ts_pos で、最小を直前 n本（いまのバーを含めない）に変えると、T47 が落ちるか（M2-E-4e・2026-09-27）
#   守っているもの＝完成の条件 #3（直近 n本はいまのバーを含める＝いまの値の位置を出す）
#   壊し方＝`        lo = s.rolling(n).min()` を `        lo = s.shift(1).rolling(n).min()` にする。
#   期待＝組む側の自己テスト T47 の②（既知答え）が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

EXE="$PR/engine_tuner_exec.py"
GEN="$PR/engine_tuner_gen.py"
guard "$EXE"

python3 - "$EXE" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        lo = s.rolling(n).min()\n'
if s.count(old) != 1:
    raise SystemExit("[b111] 壊す対象の行が1か所でない: " + old.strip())
new = '        lo = s.shift(1).rolling(n).min()  # b111 が壊した（いまのバーを最小から外す）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$GEN" --selftest
finish

