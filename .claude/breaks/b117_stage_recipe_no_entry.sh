#!/bin/bash
# EXPECT_RC: 1
# MEANS: 段の口の束から入口の木を外すと、番人⑪が「段の口の束を測る所で止まった」で落ちた
# EXPECT_MSG: ❌ ⑪
# b117 — _stage_recipe から入口の木（entry）を外すと、⑪が落ちるか（M2-F-2・監査 CP48）
#   守っているもの＝完成の条件 #7（段の口が組む束を、合成データで最後まで測れる）
#   壊し方＝_stage_recipe の入口の木の行を、閉じ括弧だけの行に替える（入口の木の無い束に戻す）。
#   期待＝regime_r9_diag.py --selftest の⑪が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            "entry": {"connective": {"all": []}}}\n'
if s.count(old) != 1:
    raise SystemExit("[b117] 壊す対象の行が1か所でない: " + old.strip())
new = '            }  # b117 が壊した（入口の木を外す）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
finish
