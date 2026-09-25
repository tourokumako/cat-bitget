#!/bin/bash
# EXPECT_RC: 1
# MEANS: 組む側の持続の内側を帯の条件1つに戻すと、T46（持続の内側が成立の全体）が落ちた
# EXPECT_MSG: ❌ T46
# b99 — 組む側の持続（streak）の内側を帯 B の条件1つに戻すと、T46 が落ちるか（M2-E-4d・束1・2026-09-25）
#   守っているもの＝完成の条件 #1（組んだ束の持続の内側が成立の全体）
#   壊し方＝`sample_regime_build` の `"inner": {"all": json.loads(json.dumps(on_core))}` を
#          `"inner": json.loads(json.dumps(cond_b))`（直す前の形）に戻す。
#   期待＝`engine_tuner_gen.py --selftest` の T46 が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
#   限界＝T46 以外の検査は見ない／このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '"inner": {"all": json.loads(json.dumps(on_core))}}'
new = '"inner": json.loads(json.dumps(cond_b))}'
if s.count(old) != 1:
    raise SystemExit("[b99] 壊す対象の行が1か所でない: " + old)
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
