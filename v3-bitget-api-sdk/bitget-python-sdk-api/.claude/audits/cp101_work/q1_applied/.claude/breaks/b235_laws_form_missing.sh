#!/bin/bash
# EXPECT_RC: 1
# MEANS: 条件の書き方を1行消すと、完成の条件 F-2 が落ちる
# EXPECT_MSG: false
# b235_laws_form_missing — 条件の書き方を1行消すと、完成の条件 F-2 が落ちる（工事 m2c15-laws-rows-20261103）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/laws/laws.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
o = json.load(open(p, encoding='utf-8'))
if len(o['条件の書き方']) != 13:
    raise SystemExit('[b235_laws_form_missing] 壊す対象（条件の書き方の13行）が無い')
o['条件の書き方'].pop()
json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
PYEOF

measure jq -e '(reduce .["条件の書き方"][] as $r (0; .+1))==13 and (reduce .["玉の状態"][] as $r (0; .+1))==9 and (reduce .["法則の中の数"][] as $r (0; .+1))==50' "$F"
finish
