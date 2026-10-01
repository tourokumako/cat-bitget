#!/bin/bash
# EXPECT_RC: 1
# MEANS: 帯の版の「続く」（次のバーから続く本数の終値が全部 帯の中）を見なくすると、自己検査 T10 が「レンジが終わる直前のバーが レンジだった になった」で落ちた
# EXPECT_MSG: ❌ T10
# b118 — regime_label.band_range の「続く」の判定を外すと、T10 が落ちるか（M2-F-6d・2026-09-29）
#   守っているもの＝完成の条件 #1（札の部品の自己検査が、帯・幅・続く の3つを全部 見ている）
#   壊し方＝`        if fmax[t] <= top and fmin[t] >= bot:` を `        if True:` にする（続くを見ない）。
#   期待＝regime_label.py --selftest の T10 が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

RL="$PR/regime_label.py"
guard "$RL"

python3 - "$RL" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        if fmax[t] <= top and fmin[t] >= bot:\n'
if s.count(old) != 1:
    raise SystemExit("[b118] 壊す対象の行が1か所でない: " + old.strip())
new = '        if True:  # b118 が壊した（続くを見ない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$RL" --selftest
finish
