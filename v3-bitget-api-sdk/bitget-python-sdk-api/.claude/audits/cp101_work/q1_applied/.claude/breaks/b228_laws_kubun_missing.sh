#!/bin/bash
# EXPECT_RC: 1
# MEANS: laws.json の選べる値の区分から1つ消すと、完成の条件 F-1 が落ちる
# EXPECT_MSG: false
# b228_laws_kubun_missing — 区分が8つそろっていないと、完成の条件 F-1 が落ちる（工事 m2c15-outside-record-20261102）
#   守っているもの＝7-6 の F-1（測るコマンドは、完成の条件と同じ）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/laws/laws.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
o = json.load(open(p, encoding='utf-8'))
k = o["要素の定義表"]["選べる値"]["区分"]
if k.count("決済の枝") != 1:
    raise SystemExit("[b228_laws_kubun_missing] 壊す対象（区分の決済の枝）が1か所でない")
k.remove("決済の枝")
json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
PYEOF

measure jq -e '.["要素の定義表"]["選べる値"]["区分"]==["相場の法則","組み合わせの法則","売り方","建てる前の確認","決済の枝","玉全体の決済","玉の持ち方","役割ごとの決まり"] and .["要素の定義表"]["表の形"]["条件の1本"]["欄"]!=null and .["要素の定義表"]["表の形"]["条件の書き方"]["欄"]!=null and .["要素の定義表"]["表の形"]["玉の状態"]["欄"]!=null and .["要素の定義表"]["表の形"]["法則の中の数"]["範囲の形"]!=null and (reduce .["要素の定義表"]["要素"][] as $r (0; .+1))==46 and (reduce .["要素の定義表"]["選べる値"]["値段の決め方の種類"][] as $r (0; .+1))==7 and (reduce .["要素の定義表"]["選べる値"]["売り方の決まりの種類"][] as $r (0; .+1))==8' "$F"
finish
