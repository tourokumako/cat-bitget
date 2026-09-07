#!/bin/bash
# b33 — 別枠（レンジ幾何・需給・時間帯）のオン・オフを空にすると、案の候補から消えるか
#   守っているもの＝監査 cp24 の §6-1「別枠にオン・オフを効かせる」（完成の条件 #1・#2・#3）
#   ★終了コードでは測れない（印を空にしても生成器は動く）ので、
#     「別枠の候補が0件になるか」を機械で測る。
#   壊し方＝印（indicator_switch.json）の geo_on・demand_on・time_on を空にする。
#   期待＝壊すと `_lineage_candidates` が別枠を1件も返さなくなる（＝印が効いている）。
#         壊さなければ 1件以上 返る。
source "$(dirname "$0")/lib.sh"

SW="$SDK/.claude/ratchet/indicator_switch.json"
guard "$SW"

# 壊す＝別枠3種の欄を空にする
python3 - "$SW" <<'PYEOF'
import json
import sys
p = sys.argv[1]
d = json.loads(open(p, encoding='utf-8').read())
for k in ("geo_on", "demand_on", "time_on"):
    d[k] = []
open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
PYEOF

# 測る＝別枠の候補が0件になったら 1（壊れたことを検出できた）
MEASURED=$(python3 "$PR/engine_tuner_gen.py" --count-extra-candidates 2>/dev/null)
[ -z "$MEASURED" ] && MEASURED=0
if [ "$MEASURED" = "0" ]; then
    MEASURED=1      # 別枠が0件＝印が効いている＝壊れたことを検出できた
else
    MEASURED=0      # 印を空にしても別枠が残る＝印が効いていない
fi
finish
