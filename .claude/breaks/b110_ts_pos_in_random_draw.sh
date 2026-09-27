#!/bin/bash
# EXPECT_RC: 1
# MEANS: 部品 ts_pos の「乱数の道で引かない」印を外すと、T47 が「入口の案を乱数で作る道の一覧に ts_pos が入っている」で落ちた
# EXPECT_MSG: ❌ T47
# b110 — 実行器の MATERIAL_PRE の ts_pos から gen_draw False を外すと、T47 が落ちるか（M2-E-4e・2026-09-27）
#   守っているもの＝完成の条件 #2（部品 ts_pos は入口の案を乱数で作る道の一覧に入らない・恒久67番）
#   壊し方＝`"same_unit": False, "gen_draw": False},` を `"same_unit": False},` にする。
#   期待＝組む側の自己テスト T47 の①が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

EXE="$PR/engine_tuner_exec.py"
GEN="$PR/engine_tuner_gen.py"
guard "$EXE"

python3 - "$EXE" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '               "same_unit": False, "gen_draw": False},\n'
if s.count(old) != 1:
    raise SystemExit("[b110] 壊す対象の行が1か所でない: " + old.strip())
new = '               "same_unit": False},  # b110 が壊した（乱数の道の印を外す）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$GEN" --selftest
finish

