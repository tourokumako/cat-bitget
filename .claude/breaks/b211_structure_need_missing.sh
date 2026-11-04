#!/bin/bash
# EXPECT_RC: 1
# MEANS: 要素の定義表の要素「出力」（②-3）の根拠から構造に要ること16を消すと、構造に要ること1〜30 のうち16の受け先が無くなり、完成の条件2が落ちる
# EXPECT_MSG: false
# b211_structure_need_missing — 構造に要ることの受け先が1件でも欠けると、完成の条件2が落ちる（工事 m2c15-indicator-structure-20261031・2026-10-31）
#   守っているもの＝7-6 の F-1 の条件2（測るコマンドは、条件2のコマンドと同じ）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
o = json.load(open(p, encoding='utf-8'))
hit = [e for e in o["要素の定義表"]["要素"] if e["番号"] == "②-3" and 16 in e["根拠"]["構造に要ること"]]
if len(hit) != 1:
    raise SystemExit("[b211_structure_need_missing] 壊す対象（②-3 の根拠の16）が1か所でない")
hit[0]["根拠"]["構造に要ること"].remove(16)
json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
PYEOF

measure jq -e --slurpfile l "$PR/laws/laws.json" '((reduce range(1;31) as $i ([]; . + ["\($i)"])) - (reduce (.["要素の定義表"]["要素"][]["根拠"]["構造に要ること"][], $l[0]["要素の定義表"]["要素"][]["根拠"]["構造に要ること"][]?) as $n ([]; . + ["\($n)"])) - (reduce path(.["要素の定義表"]["この表で受けない要ること"][]) as $p ([]; . + [$p[2]]))) == []' "$F"
finish
