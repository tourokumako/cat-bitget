#!/bin/bash
# EXPECT_RC: 1
# MEANS: 乱数を使う行を道具に戻すと、番人⑦が「乱数の道が残っている: default_rng」で落ちた
# EXPECT_MSG: ❌ ⑦
# b114 — main に default_rng を使う行を戻すと、⑦（構文木の見張り）が落ちるか（M2-F-2・恒久67番・2026-09-27）
#   守っているもの＝完成の条件 #2（乱数がこの道具に残っていない）
#   壊し方＝`    ad = et.load_adapter(a.strategy)` の直後に `_rng = np.random.default_rng(0)` を足す。
#   期待＝regime_r9_diag.py --selftest の⑦が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    ad = et.load_adapter(a.strategy)\n'
if s.count(old) != 1:
    raise SystemExit("[b114] 壊す対象の行が1か所でない: " + old.strip())
new = '    ad = et.load_adapter(a.strategy)\n    _rng = np.random.default_rng(0)  # b114 が壊した（乱数の道を戻す）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
finish
