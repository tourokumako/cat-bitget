#!/bin/bash
# EXPECT_RC: 1
# MEANS: 段2c の候補に動く線を作る分岐を止めると、T47 が「段2c の候補に動く線が1本も無い」で落ちた
# EXPECT_MSG: ❌ T47
# b109 — build_stage_candidates が窓つきの前処理（pre_win）から動く線の候補を作る分岐を止めると、T47 が落ちるか（M2-E-4e・2026-09-27）
#   守っているもの＝完成の条件 #1（段2c の候補に、BB幅 の固定の線と同じ本数の動く線が在る）
#   壊し方＝`            if _pw:` を `            if False and _pw:` にする。
#   期待＝組む側の自己テスト T47 の③が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            if _pw:\n'
if s.count(old) != 1:
    raise SystemExit("[b109] 壊す対象の行が1か所でない: " + old.strip())
new = '            if False and _pw:  # b109 が壊した（動く線を作らない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$GEN" --selftest
finish

