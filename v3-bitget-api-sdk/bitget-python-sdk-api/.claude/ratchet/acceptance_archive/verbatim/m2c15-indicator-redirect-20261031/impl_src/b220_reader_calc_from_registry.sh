#!/bin/bash
# EXPECT_RC: 1
# MEANS: 読む口の計算の口が、計算の登録から関数を取らない形にする＝calc が関数を返さず、読む口の自己テストが落ちる
# EXPECT_MSG: ❌ 計算: 記録の登録の名前で、計算の登録から関数を取る（F-1）
# b220_reader_calc_from_registry — 読む口が計算の関数を登録から返さないと、自己テストが落ちる（工事 m2c15-indicator-redirect-20261031・やることの表 7-6 の F-1 の3行目）
#   守っているもの＝7-6 の F-1 の3行目（測るコマンドは、完成の条件と同じ＝読む口の --selftest）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        tpl, directional, fn = mf[reg]\n'
new = '        tpl, directional, fn = mf[reg][0], mf[reg][1], None\n'
if s.count(old) != 1:
    raise SystemExit("[b220_reader_calc_from_registry] 壊す対象（計算の登録から関数を取る行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/indicators/indicators.py" --selftest
finish
