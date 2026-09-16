#!/bin/bash
# EXPECT_RC: 1
# MEANS: 持続（streak）を掛ける行を消すと、法則の審査が束を落として T24② が落ちた
# EXPECT_MSG: ❌ T24②
# b77 — 持続（streak）を掛ける行を消すと、束が法則の審査を通らなくなるか
#   守っているもの＝完成の条件 条件6・AUDIT-4（100本 組んで審査を通る束が1本以上）
#   壊し方＝`sample_regime_build` の「法則に streak が在れば持続を掛ける」行を、常に偽にする。
#   期待＝自己テスト T24 が落ちる（終了コード 1）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'if "streak" in laws["forms"]:'
if old not in s:
    raise SystemExit("[b77] 壊す対象の行が見つからない: " + old)
open(p, 'w', encoding='utf-8').write(s.replace(old, 'if False:  # b77 が壊した', 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
