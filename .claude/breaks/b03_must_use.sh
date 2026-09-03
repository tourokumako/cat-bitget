#!/bin/bash
# b03 — must_use の名前を関数の中から消すと、照合が止まるか（完成の条件 #3）
#   設計書の must_use が「check_frozen は FROZEN を使う」と書いているので、それを消す。
source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/tools/run_breaks.py"
guard "$T"

python3 - "$T" <<'PYEOF'
import re, sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
m = re.search(r'\ndef check_frozen\(.*?(?=\ndef )', s, flags=re.S)
if m:
    body = m.group(0).replace('FROZEN', 'None')
    s = s[:m.start()] + body + s[m.end():]
open(p, 'w', encoding='utf-8').write(s)
PYEOF

measure python3 "$VERIFY" --diff "$ROOT/.claude/state/acceptance.md"
finish
