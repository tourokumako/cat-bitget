#!/bin/bash
# EXPECT_RC: 1
# MEANS: 実行器のレンジ幾何の印の照らしを消すと、T-g-2（印から外したレンジ幾何が通ってしまう）が落ちた
# EXPECT_MSG: ❌ T-g-2
# b103 — 実行器の `_material_name` からレンジ幾何の印（geo_on）の照らしを消すと、T-g が落ちるか（M2-E-5b・束1・2026-09-25）
#   守っているもの＝完成の条件 #5（印から外れたレンジ幾何・時間帯を実行器が G6 で拒否する＝148番）
#   壊し方＝`if not geo_enabled(g):` を常に偽にする（b35 と同じ型＝印を見る行を消す）。
#   期待＝`engine_tuner_exec.py --selftest` の T-g-2 が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
#   限界＝壊すのはレンジ幾何の枝だけ（時間帯の枝を消しても落ちるかは、これでは測れない）／このプログラム自身を
#        書き換えれば無効にできる（承認のときに凍結される）
source "$(dirname "$0")/lib.sh"

EXE="$PR/engine_tuner_exec.py"
guard "$EXE"

python3 - "$EXE" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        if not geo_enabled(g):'
new = '        if False:  # b103 が壊した（geo_enabled を見ない）'
if s.count(old) != 1:
    raise SystemExit("[b103] 壊す対象の行が1か所でない: " + old)
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_exec.py" --selftest
finish
