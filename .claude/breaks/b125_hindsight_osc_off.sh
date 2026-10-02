#!/bin/bash
# EXPECT_RC: 1
# MEANS: 版3（hindsight_box）の「箱の中で上下に2回ずつ行き来している所は、脚の中でもレンジに戻す」を外すと、自己検査 T15 が「階段の横ばい」で落ちた
# EXPECT_MSG: ❌ T15
# b125 — regime_label._range_on の、行き来している箱を戻す所を外すと、T15 が落ちるか（M2-F-6d の工事 D・2026-10-02）
#   守っているもの＝完成の条件 #1（札の部品の自己検査が、版3 が階段の横ばいをレンジと言えるかを見ている）
#   壊し方＝`    return lab | (_spread(ok & q, n_box) & ~stp)` を `    return lab` にする（戻さない＝前の版 label-trial-c24 と同じ）。
#   期待＝regime_label.py --selftest の T15 が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

RL="$PR/regime_label.py"
guard "$RL"

python3 - "$RL" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    return lab | (_spread(ok & q, n_box) & ~stp)\n'
if s.count(old) != 1:
    raise SystemExit("[b125] 壊す対象の行が1か所でない: " + old.strip())
new = '    return lab  # b125 が壊した（行き来している箱を戻さない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$RL" --selftest
finish
