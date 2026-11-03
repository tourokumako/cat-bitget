#!/bin/bash
# EXPECT_RC: 1
# MEANS: 読む口の、代表の値の鍵を売買スタイルと照らす判定を外すと、読む口の自己テストが落ちる
# EXPECT_MSG: ❌ 決まり④: 売買スタイルに無い値で止まる
# b232_reader_style_check — 売買スタイルに無い代表の値の鍵で止まらないと、読む口の自己テストが落ちる（工事 m2c15-outside-record-20261102）
#   守っているもの＝7-6 の F-4（測るコマンドは、完成の条件と同じ＝読む口の --selftest）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'if k not in allowed:                         # ★売買スタイルの照らし'
new = 'if False:                                    # ★売買スタイルの照らし'
if s.count(old) != 1:
    raise SystemExit("[b232_reader_style_check] 壊す対象（売買スタイルの照らしの行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/indicators/indicators.py" --selftest
finish
