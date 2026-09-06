#!/bin/bash
# b27 — 飛ばした番人を集める行を消すと、合否行から「該当なし」が消えるか（完成の条件 #1）
#   守っているもの＝監査 cp23 の X-5「『✅ 全部 pass』が『番人を全部 当てた』を意味しない」
#   ★終了コードでは測れない（飛ばしても selftest は pass のまま）ので、合否行の文字で測る。
source "$(dirname "$0")/lib.sh"

T="$PR/gen_materials.py"
guard "$T"

# 壊す＝skipped に積む行を全部 消す
python3 - "$T" <<'PYEOF'
import re
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
s = re.sub(r'\n\s*skipped\.append\([^)]*\)', '', s)
open(p, 'w', encoding='utf-8').write(s)
PYEOF

# 測る＝合否行に「該当なし」が出なくなったら 1（壊れたことを検出できた）
if python3 "$PR/gen_materials.py" --selftest 2>&1 | grep -q "該当なし"; then
    MEASURED=0
else
    MEASURED=1
fi
finish
