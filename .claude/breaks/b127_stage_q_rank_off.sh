#!/bin/bash
# EXPECT_RC: 1
# MEANS: 段2a の分位ごとの候補に通し番号を付ける2行を外すと、部分の自己テストが T49①「順位が1からの通し番号でない」で落ちた
# EXPECT_MSG: ❌ T49①
# b127 — engine_tuner_gen.build_stage_candidates の、分位ごとに順位を1つ進める2行を外すと、T49① が落ちるか（工事 m2f-stage-quantile-rank-20261003・2026-10-03）
#   守っているもの＝完成の条件 #1（部分の自己テスト T49① が、分位を複数 書いた段2a の候補の順位が通し番号かを見ている）
#   壊し方＝順位を進める2行（if _iq > 0: rank += 1）を消す（直す前と同じ＝同じ材料の分位の候補に同じ順位が付く）。
#   期待＝engine_tuner_gen.py --selftest-stage-q の T49① が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

G="$PR/engine_tuner_gen.py"
guard "$G"

python3 - "$G" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            if _iq > 0:\n                rank += 1\n'
if s.count(old) != 1:
    raise SystemExit("[b127] 壊す対象の行が1か所でない: " + old.strip())
open(p, 'w', encoding='utf-8').write(s.replace(old, '', 1))
PYEOF

measure python3 "$G" --selftest-stage-q
finish
