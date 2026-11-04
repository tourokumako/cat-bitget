#!/bin/bash
# EXPECT_RC: 1
# MEANS: 指している法則の中の数の照らしを外すと、読む口の自己テストが落ちる
# EXPECT_MSG: ❌ 決まり⑩: 法則の中の数の名前が無いと止まる
# b236_laws_reader_ref — 指している法則の中の数の照らしを外すと、読む口の自己テストが落ちる（工事 m2c15-laws-rows-20261103）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/laws/laws.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '_stop(f"指している名前が無い: {where} の法則の中の数 {name!r}")'
if s.count(old) != 1:
    raise SystemExit('[b236_laws_reader_ref] 壊す対象（数の照らし）が1か所でない')
open(p, 'w', encoding='utf-8').write(s.replace(old, 'return None'))
PYEOF

measure python3 "$F" --selftest
finish
