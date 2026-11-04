#!/bin/bash
# EXPECT_RC: 1
# MEANS: 決済の枝の行を1行消すと、完成の条件 F-1 が落ちる
# EXPECT_MSG: false
# b234_laws_row_missing — 決済の枝の行を1行消すと、完成の条件 F-1 が落ちる（工事 m2c15-laws-rows-20261103）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/laws/laws.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
o = json.load(open(p, encoding='utf-8'))
n = len(o['法則の行'])
o['法則の行'] = [r for r in o['法則の行'] if r['番号'] != '枝型-TIME_DOWN']
if len(o['法則の行']) != n - 1:
    raise SystemExit('[b234_laws_row_missing] 壊す対象（枝型-TIME_DOWN）が1か所でない')
json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
PYEOF

measure jq -e '(reduce .["法則の行"][] as $r (0; .+1))==40 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="決済の枝" then .+1 else . end))==31 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="売り方" then .+1 else . end))==5 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="建てる前の確認" then .+1 else . end))==1 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="玉全体の決済" then .+1 else . end))==2 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="玉の持ち方" then .+1 else . end))==1' "$F"
finish
