#!/bin/bash
# EXPECT_RC: 1
# MEANS: 法則一覧.md を1文字書き替えると、--verify が落ちる
# EXPECT_MSG: 文書が作り直した物と違う
# b237_laws_doc_changed — 法則一覧.md を1文字書き替えると、--verify が落ちる（工事 m2c15-laws-rows-20261103）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/../../.claude/rules/法則一覧.md"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
if '# 法則一覧' not in s:
    raise SystemExit('[b237_laws_doc_changed] 壊す対象（見出し）が無い')
open(p, 'w', encoding='utf-8').write(s.replace('# 法則一覧', '# 法則の一覧', 1))
PYEOF

measure python3 "$PR/laws/laws.py" --verify
finish
