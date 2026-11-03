#!/bin/bash
# EXPECT_RC: 1
# MEANS: 選べる値の売買スタイルを消すと、完成の条件 F-3 の2行目が落ちる
# EXPECT_MSG: false
# b231_style_missing — 売買スタイルが定義表に無いと、完成の条件 F-3 が落ちる（工事 m2c15-outside-record-20261102）
#   守っているもの＝7-6 の F-3 の2行目（測るコマンドは、完成の条件と同じ）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
o = json.load(open(p, encoding='utf-8'))
if "売買スタイル" not in o["要素の定義表"]["選べる値"]:
    raise SystemExit("[b231_style_missing] 壊す対象（選べる値の売買スタイル）が無い")
del o["要素の定義表"]["選べる値"]["売買スタイル"]
json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
PYEOF

measure jq -e '.["要素の定義表"]["選べる値"]["売買スタイル"]==["スキャル","デイトレ"] and .["要素の定義表"]["選べる値"]["場面"]==["レンジ","上げ","下げ","スパイク"] and (reduce .["要素の定義表"]["要素"][] as $r (0; if $r["要素の名前"]=="確かめの強さ" or $r["要素の名前"]=="使える条件の形" or $r["要素の名前"]=="上位足の写し方" then .+1 else . end))==3' "$F"
finish
