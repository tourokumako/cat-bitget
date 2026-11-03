#!/bin/bash
# EXPECT_RC: 1
# MEANS: laws.json の ⑤-3 の中身を1文字変えると、指標データから移す前の行と違うので、完成の条件 F-2 が落ちる
# EXPECT_MSG: false
# b229_laws_row_changed — 法則の10行が移す前と1文字でも違うと、完成の条件 F-2 が落ちる（工事 m2c15-outside-record-20261102）
#   守っているもの＝7-6 の F-2（測るコマンドは、完成の条件と同じ）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/laws/laws.json"
I="$PR/indicators/indicators.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
o = json.load(open(p, encoding='utf-8'))
hit = [e for e in o["要素の定義表"]["要素"] if e["番号"] == "⑤-3"]
if len(hit) != 1:
    raise SystemExit("[b229_laws_row_changed] 壊す対象（⑤-3）が1か所でない")
hit[0]["中身"] += "。"
json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
PYEOF

measure jq -e --slurpfile o <(git -C "$ROOT" show 1f6f5ff9:v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json) --slurpfile n "$F" '$o[0]["要素の定義表"]["要素"][37:47]==$n[0]["要素の定義表"]["要素"][0:10] and (reduce .["要素の定義表"]["要素"][] as $r (0; if $r["置く記録"]=="法則の記録" then .+1 else . end))==0 and .["要素の定義表"]["選べる値"]["法則の種類"]==null and .["要素の定義表"]["選べる値"]["判定の型"]==null and .["要素の定義表"]["選べる値"]["法則が指せる物"]==null and .["要素の定義表"]["法則の記録の置き場"]=="scripts/priority_rebuild/laws/laws.json" and $o[0]["要素の定義表"]["要素"][0:37]==.["要素の定義表"]["要素"][0:37] and $o[0]["要素の定義表"]["選べる値"]["法則の種類"]==$n[0]["要素の定義表"]["選べる値"]["法則の種類"] and $o[0]["要素の定義表"]["選べる値"]["判定の型"]==$n[0]["要素の定義表"]["選べる値"]["判定の型"] and $o[0]["要素の定義表"]["選べる値"]["法則が指せる物"]==$n[0]["要素の定義表"]["選べる値"]["法則が指せる物"]' "$I"
finish
