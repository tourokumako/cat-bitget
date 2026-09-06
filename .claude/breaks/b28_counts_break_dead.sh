#!/bin/bash
# b28 — COUNTS の食い違いを見る判定を殺すと、番人 B3 が落ちるか（完成の条件 #2）
#   守っているもの＝監査 cp22 の N-3 で足した COUNTS の差し込みに、番人が付いていること
source "$(dirname "$0")/lib.sh"

T="$PR/gen_materials.py"
guard "$T"

# 壊す＝COUNTS が実物と食い違っても鳴らないようにする
python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
s = s.replace('if _cur2 != bans_count_block("counts"):', 'if False:')
open(p, 'w', encoding='utf-8').write(s)
PYEOF

measure python3 "$PR/gen_materials.py" --selftest
finish
