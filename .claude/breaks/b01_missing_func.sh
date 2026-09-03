#!/bin/bash
# b01 — 凍結に在る関数を実装から消すと、照合が止まるか（完成の条件 #1）
#   相手＝run_breaks.py（この設計で新しく作ったので、impl_functions に必ず在る）
source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/tools/run_breaks.py"
guard "$T"

# 壊す＝凍結に在る関数 parse_table を丸ごと消す
python3 - "$T" <<'PYEOF'
import re, sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
s = re.sub(r'\ndef parse_table\(.*?(?=\ndef )', '\n', s, count=1, flags=re.S)
open(p, 'w', encoding='utf-8').write(s)
PYEOF

measure python3 "$VERIFY" --diff "$ROOT/.claude/state/acceptance.md"
finish
