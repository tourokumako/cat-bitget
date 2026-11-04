#!/bin/bash
# EXPECT_RC: 1
# MEANS: 要素の定義表の要素のうち、置く記録が「法則の記録」の行を全部消すと、置く記録が4つちょうどでなくなり、完成の条件1が落ちる
# EXPECT_MSG: false
# b213_place_missing — 置く記録（指標の記録・使い方の記録・部品の記録・法則の記録）のどれかの行が無くなると、完成の条件1が落ちる（工事 m2c15-indicator-structure-20261031・監査 CP92 の修正18・2026-10-31）
#   守っているもの＝7-6 の F-1 の条件1（測るコマンドは、条件1のコマンドと同じ）
#   ★壊す対象（置く記録が法則の記録の行）が1行も無ければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/laws/laws.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
o = json.load(open(p, encoding='utf-8'))
rows = o["要素の定義表"]["要素"]
hit = [e for e in rows if e.get("置く記録") == "法則の記録"]
if not hit:
    raise SystemExit("[b213_place_missing] 壊す対象（置く記録が法則の記録の行）が1行も無い")
o["要素の定義表"]["要素"] = [e for e in rows if e.get("置く記録") != "法則の記録"]
json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
PYEOF

measure jq -e --slurpfile l "$F" '(["使い方の記録","指標の記録","部品の記録"] - [.["要素の定義表"]["要素"][]["置く記録"]]) == [] and (reduce $l[0]["要素の定義表"]["要素"][] as $r (0; if $r["置く記録"]=="法則の記録" then .+1 else . end))==10' "$PR/indicators/indicators.json"
finish
