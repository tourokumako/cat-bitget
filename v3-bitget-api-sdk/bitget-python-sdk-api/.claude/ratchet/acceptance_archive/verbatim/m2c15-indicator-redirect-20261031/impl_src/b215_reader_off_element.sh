#!/bin/bash
# EXPECT_RC: 1
# MEANS: 読む口の決まり③（オフの要素は返さない）の判定を外す＝record がオフの要素を返し、読む口の自己テストが落ちる
# EXPECT_MSG: ❌ 決まり③: record はオフの要素を返さない
# b215_reader_off_element — 読む口がオフの要素を返すと、自己テストが落ちる（工事 m2c15-indicator-redirect-20261031・やることの表 7-6 の F-1）
#   守っているもの＝7-6 の F-1 の1行目（測るコマンドは、完成の条件と同じ＝読む口の --selftest）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'on = self.rows_on.get(kind) or {}                      # ★決まり③'
new = 'on = self.rows.get(kind) or {}                         # ★決まり③'
if s.count(old) != 1:
    raise SystemExit("[b215_reader_off_element] 壊す対象（record の決まり③の行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/indicators/indicators.py" --selftest
finish
