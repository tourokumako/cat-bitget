#!/bin/bash
# EXPECT_RC: 1
# MEANS: 分位を1段ずつ計算する形に戻すと、T34② が「まとめて渡す形になっていない」で落ちた
# EXPECT_MSG: T34
# b80 — 分位を1段ずつ計算する形に戻すと、まとめ計算の検査が落ちるか
#   守っているもの＝完成の条件 条件7（分位を1回でまとめて計算し、1段ずつの結果と一致する）
#   壊し方＝まとめて渡す1行を、1段ずつ呼ぶ形に戻す。
#   期待＝自己テスト T34 が落ちる（終了コード 1）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        table[key] = {q: float(v) for q, v in zip(grid, np.quantile(s, _ps))}'
if old not in s:
    raise SystemExit("[b80] 壊す対象の行が見つからない: " + old)
new = ('        table[key] = {q: float(np.quantile(s, int(q.lstrip("q")) / 100.0)) for q in grid}'
       '  # b80 が壊した（1段ずつ）')
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
