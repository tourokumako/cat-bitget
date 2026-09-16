#!/bin/bash
# EXPECT_RC: 1
# MEANS: 材料の数字を乱数で引く形に戻すと、T24⑥ が「成績表の列の数字と違う」で落ちた
# EXPECT_MSG: ❌ T24⑥
# b79 — 材料の数字を乱数で引く形に戻すと、成績表の列の数字と合わなくなるか
#   守っているもの＝完成の条件 AUDIT-5（材料の数字に乱数が無い）
#   壊し方＝候補を作る関数の `_mat_from_col(...)` を、`_mat_drawn(乱数, ...)` に戻す。
#   期待＝自己テスト T24⑥ が落ちる（終了コード 1）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        m = _mat_from_col(col, fam, tf, ranges, table=table)'
new = ('        m = _mat_drawn(np.random.default_rng([79, rank]), fam, tf, ranges, table=table)'
       '  # b79 が壊した')
# ★2026-09-12＝壊す場所を、候補を作る関数（build_stage_candidates）の中だけに絞った。
#   直す前＝`s.replace(old, new, 1)`＝**最初に見つかった1件**を壊していた。
#     同じ行は 4件 在り（`_ranked_material_at`・`build_stage_candidates`・
#     `_material_for_lineage`・`_material_for_law`）、最初の1件は
#     `_ranked_material_at`＝測る相手の検査（T24⑥）が見ない経路だった。
#   ★2026-09-12 に2回 直した。
#     1回目＝`_material_for_lineage` の中を壊す形にした。**走らせたら全部 pass**
#       ＝T24⑥ は `build_stage_candidates` が返す候補を見るので、その関数では落ちない
#       （判定の実物＝`engine_tuner_gen.py` の 6183行で `build_stage_candidates` を呼んでいる）。
#     2回目＝`build_stage_candidates` の中を壊す形にした（いまの形）。
#       その関数に在る変数は `rank`（`rank_pos` ではない＝2627行 `rank += 1`）。
#   ★関数の名前から数えて、その中の1件だけを壊す（場所が一意に定まる）。
FN = 'def build_stage_candidates'
if FN not in s:
    raise SystemExit("[b79] 壊す対象の関数が見つからない: " + FN)
i = s.index(FN)
j = s.find(old, i)
if j < 0:
    raise SystemExit("[b79] 壊す対象の行が、その関数の中に見つからない: " + old)
open(p, 'w', encoding='utf-8').write(s[:j] + new + s[j + len(old):])
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
