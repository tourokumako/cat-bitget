#!/bin/bash
# EXPECT_RC: 1
# MEANS: 指標の記録 RSI の名前を書き替えると、完成の条件 F-6 が落ちる
# EXPECT_MSG: false
# b239_records_changed_rows — 指標の記録 RSI の名前を書き替えると、完成の条件 F-6 が落ちる（工事 m2c15-laws-rows-20261103）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
o = json.load(open(p, encoding='utf-8'))
if 'RSI' not in o['指標の記録']:
    raise SystemExit('[b239_records_changed_rows] 壊す対象（記録 RSI）が無い')
o['指標の記録']['RSI']['名前'] = 'RSIの見本'
json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
PYEOF

T=$(mktemp) && git -C "$ROOT" show cbde6ab2:v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json > "$T"
measure jq -e --slurpfile o "$T" '(reduce .["使い方の記録"][] as $r (0; .+1))==20 and $o[0]["使い方の記録"]==.["使い方の記録"][0:16] and $o[0]["指標の記録"]==.["指標の記録"] and $o[0]["部品の記録"]==.["部品の記録"]' "$F"
finish
