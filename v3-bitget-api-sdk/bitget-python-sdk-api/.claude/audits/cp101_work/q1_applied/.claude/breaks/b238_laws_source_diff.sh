#!/bin/bash
# EXPECT_RC: 1
# MEANS: 法則の中の数の範囲を1つ変えると、写す元との照らしが落ちる
# EXPECT_MSG: 写す元と違う
# b238_laws_source_diff — 法則の中の数の範囲を1つ変えると、写す元との照らしが落ちる（工事 m2c15-laws-rows-20261103）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/laws/laws.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
o = json.load(open(p, encoding='utf-8'))
hit = [n for n in o['法則の中の数'] if n['名前'] == 'state_mult_range']
if len(hit) != 1:
    raise SystemExit('[b238_laws_source_diff] 壊す対象（state_mult_range）が1か所でない')
hit[0]['範囲']['hi'] = 9.0
json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
PYEOF

measure python3 "$PR/laws/laws.py" --check-sources
finish
