#!/bin/bash
# EXPECT_RC: 1
# MEANS: 捉えた割合の正解の向きを逆にすると、番人⑥が「正解レンジが0本なのに nan でない」で落ちた
# EXPECT_MSG: ❌ ⑥
# b113 — r9_catch_share の分母（正解がレンジ＝強さが偽 ∧ 使える）から否定を外すと、⑥が落ちるか（M2-F-2・2026-09-27）
#   守っているもの＝完成の条件 #1（捉えた割合の式＝正解がレンジのバーのうち判定が真・正解0本なら nan）
#   壊し方＝`    m = (~np.asarray(strong, bool)) & np.asarray(usable, bool)` の否定（~）を外す。
#   期待＝regime_r9_diag.py --selftest の⑥が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    m = (~np.asarray(strong, bool)) & np.asarray(usable, bool)\n'
if s.count(old) != 1:
    raise SystemExit("[b113] 壊す対象の行が1か所でない: " + old.strip())
new = '    m = np.asarray(strong, bool) & np.asarray(usable, bool)  # b113 が壊した（正解の向きを逆にする）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
finish
