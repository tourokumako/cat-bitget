#!/bin/bash
# EXPECT_RC: 1
# MEANS: 指標の記録 RSI の名前を書き替えると、直す前の記録と違うので、完成の条件 F-3 の1行目が落ちる
# EXPECT_MSG: false
# b230_records_changed_laws — 3種類の記録が直す前と違うと、完成の条件 F-3 が落ちる（工事 m2c15-outside-record-20261102）
#   守っているもの＝7-6 の F-3 の1行目（測るコマンドは、完成の条件と同じ）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
o = json.load(open(p, encoding='utf-8'))
if o["指標の記録"].get("RSI", {}).get("名前") != "RSI":
    raise SystemExit("[b230_records_changed_laws] 壊す対象（記録 RSI の名前）が在るはずの形でない")
o["指標の記録"]["RSI"]["名前"] = "RSI見本"
json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
PYEOF

measure jq -e --slurpfile o <(git -C "$ROOT" show 1f6f5ff9:v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json) '$o[0]["指標の記録"]==.["指標の記録"] and $o[0]["使い方の記録"]==.["使い方の記録"] and $o[0]["部品の記録"]==.["部品の記録"]' "$F"
finish
