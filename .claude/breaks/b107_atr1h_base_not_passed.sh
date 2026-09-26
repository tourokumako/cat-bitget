#!/bin/bash
# EXPECT_RC: 1
# MEANS: build_features が1時間足の元の5分足を置き場に入れないと、4時間足の列が作れず番人 T-A3 が落ちた
# EXPECT_MSG: ❌ T-A3
# b107 — build_features が置き場 _H1_BASE に5分足を入れる行を消すと、T-A3 が落ちるか（M2-E-4c・束2・2026-09-26）
#   守っているもの＝完成の条件 #4（1時間足より長い足でも、新しい部品の列が作れる＝まこさん決定 B）
#   壊し方＝`build_features` の置き場に5分足を入れる行を `pass` にする。
#   期待＝番人 T-A3 が置き場を空にしてから4時間足の列を作ると、部品が止まって列が作られず、T-A3 が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    _H1_BASE["bars"] = bars\n'
if s.count(old) != 1:
    raise SystemExit("[b107] 壊す対象の行が1か所でない: " + old.strip())
new = '    pass  # b107 が壊した（1時間足の元の5分足を部品へ渡さない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$OBS" --selftest-atr1h
finish
