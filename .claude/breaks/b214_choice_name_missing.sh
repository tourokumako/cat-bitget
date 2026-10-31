#!/bin/bash
# EXPECT_RC: 1
# MEANS: 要素 ②-7 の「選べる値の名前」を「役割の区分2」に書き替えると、選べる値に無い名前を指す要素ができ、完成の条件5が落ちる
# EXPECT_MSG: false
# b214_choice_name_missing — 要素が指す選べる値の名前が選べる値に無いと、完成の条件5が落ちる（工事 m2c15-indicator-structure-20261031・監査 CP93 の修正6）
#   守っているもの＝7-6 の F-1 の条件5（測るコマンドは、監査 CP93 の修正3 を当てた条件5のコマンドと同じ）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
o = json.load(open(p, encoding='utf-8'))
hit = [e for e in o["要素の定義表"]["要素"] if e["番号"] == "②-7" and e["形の決まり"]["選べる値の名前"] == "役割の区分"]
if len(hit) != 1:
    raise SystemExit("[b214_choice_name_missing] 壊す対象（②-7 の選べる値の名前）が1か所でない")
hit[0]["形の決まり"]["選べる値の名前"] = "役割の区分2"
json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
PYEOF

measure jq -e '((([.["要素の定義表"]["要素"][]["形の決まり"]["選べる値の名前"]] - [null]) - (reduce path(.["要素の定義表"]["選べる値"][]) as $p ([]; . + [$p[2]]))) == []) and ((reduce (reduce .["要素の定義表"]["要素"][]["番号"] as $n ([]; if any(.[]; . == $n) then . else . + [$n] end))[] as $x (0; . + 1)) == 40) and ((reduce .["要素の定義表"]["要素"][] as $x (0; . + 1)) == 40) and has("役割の区分の表") and has("方向から性質への対応の表")' "$F"
finish
