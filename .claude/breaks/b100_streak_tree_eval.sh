#!/bin/bash
# EXPECT_RC: 1
# MEANS: 実行器の「内側が束のときの評価」を束の先頭の条件だけにすると、T-STREAK-TREE（別の式との突き合わせ）が落ちた
# EXPECT_MSG: ❌ T-STREAK-TREE
# b100 — 実行器の持続（streak）の内側が束のときの評価を壊すと、T-STREAK-TREE が落ちるか（M2-E-4d・束1・2026-09-25）
#   守っているもの＝完成の条件 #2（内側が束の持続を「束の評価の連続本数」として評価する）
#   壊し方＝`_eval_cond` の `inner = _eval_tree(c["inner"], df, geo, lane, qtable, allow_bool_col)` を、
#          束の先頭の条件だけを評価する形にする。
#   期待＝`engine_tuner_exec.py --selftest` の T-STREAK-TREE が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
#   限界＝T-STREAK-TREE 以外の検査は見ない／このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）
source "$(dirname "$0")/lib.sh"

EXE="$PR/engine_tuner_exec.py"
guard "$EXE"

python3 - "$EXE" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'inner = _eval_tree(c["inner"], df, geo, lane, qtable, allow_bool_col)'
new = 'inner = _eval_tree((c["inner"].get("all") or [c["inner"]])[0], df, geo, lane, qtable, allow_bool_col)  # b100 が壊した'
if s.count(old) != 1:
    raise SystemExit("[b100] 壊す対象の行が1か所でない: " + old)
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_exec.py" --selftest
finish
