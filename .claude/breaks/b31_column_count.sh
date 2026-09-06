#!/bin/bash
# b31 — 完成の条件の表に生の縦棒を1本 足すと、表を読む口が止まるか（完成の条件 #1）
#   守っているもの＝監査 cp23 の X-7「生の | を書くと、承認の機械が列をずらして読んだ」
#   ★実物の設計書は触らない（一時のコピーを壊す）。承認の印が外れないようにするため。
source "$(dirname "$0")/lib.sh"

TMPD="$(mktemp -d)"
D="$TMPD/acc_bad.md"
cp "$ROOT/.claude/state/acceptance.md" "$D"

# 壊す＝完成の条件の表の欄に、生の縦棒を1本 足す（列が1つ増える）
python3 - "$D" <<'PYEOF'
import re
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
m = re.search(r'^\| 1 \|.*$', s, re.M)
if m:
    row = m.group(0)
    s = s.replace(row, row.replace(' 実経路 ', ' 実|経路 ', 1), 1)
open(p, 'w', encoding='utf-8').write(s)
PYEOF

measure python3 "$ROOT/.claude/tools/run_breaks.py" --parse-only --design "$D"
rm -rf "$TMPD"
finish
