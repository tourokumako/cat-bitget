#!/bin/bash
# EXPECT_RC: 1
# MEANS: 読む口の column_sets が、組ごとの計算の登録の名前を返さない形にする＝読む口の自己テストが落ちる
# EXPECT_MSG: ❌ 列を作る組は、組ごとに計算の登録の名前も返す
# b224_reader_sets_no_reg — 列を作る組に計算の登録の名前が無いと、読む口の自己テストが落ちる（工事 m2c15-catalog-redirect-20261101・やることの表 7-6 の F-2）
#   守っているもの＝7-6 の F-2（測るコマンドは、完成の条件と同じ＝indicators.py --selftest）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicators/indicators.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '                                "登録の名前": reg})\n'
new = '                                })\n'
if s.count(old) != 1:
    raise SystemExit("[b224_reader_sets_no_reg] 壊す対象（列を作る組に登録の名前を入れる行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$F" --selftest
finish
