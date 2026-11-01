#!/bin/bash
# EXPECT_RC: 1
# MEANS: 読む口の決まり④（選べる値に無い値は止まる）の照らしを外す＝選べる値に無い値が通り、読む口の自己テストが落ちる
# EXPECT_MSG: ❌ 決まり④: 名前で指す表（役割の区分の表）に無い値で止まる
# b216_reader_choice_check — 読む口が選べる値に無い値を通すと、自己テストが落ちる（工事 m2c15-indicator-redirect-20261031・やることの表 7-6 の F-1）
#   守っているもの＝7-6 の F-1 の2行目（測るコマンドは、完成の条件と同じ＝読む口の --selftest）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        allowed = set(self.choices(cname))\n'
new = '        allowed = set(self.choices(cname))\n        return\n'
if s.count(old) != 1:
    raise SystemExit("[b216_reader_choice_check] 壊す対象（決まり④の照らしの行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/indicators/indicators.py" --selftest
finish
