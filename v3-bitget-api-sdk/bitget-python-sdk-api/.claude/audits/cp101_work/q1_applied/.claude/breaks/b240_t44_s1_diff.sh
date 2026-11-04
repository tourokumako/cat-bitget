#!/bin/bash
# EXPECT_RC: 1
# MEANS: S1 の法則の中の数を1つ変えると、T44 が落ちる
# EXPECT_MSG: 通らない
# b240_t44_s1_diff — S1 の法則の中の数を1つ変えると、T44 が落ちる（工事 m2c15-laws-rows-20261103）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/laws/laws.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
o = json.load(open(p, encoding='utf-8'))
hit = [n for n in o['法則の中の数'] if n['名前'] == 'S1_直近の安値の本数']
if len(hit) != 1:
    raise SystemExit('[b240_t44_s1_diff] 壊す対象（S1_直近の安値の本数）が1か所でない')
hit[0]['代表の値']['スキャル'] = 12
json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
PYEOF

measure python3 "$ROOT/.claude/tools/check_one_path.py" --test T44
finish
