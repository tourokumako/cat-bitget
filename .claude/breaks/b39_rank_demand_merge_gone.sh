#!/bin/bash
# b39 — 成績表に需給を「足す」処理を消すと、観察の道具の自己検査（T-f）が落ちるか
#
#   守っているもの＝設計書 iter="demand-in-ranking-20260907" の完成の条件 #1
#     （成績表に需給3列が順位に載る）。
#   壊し方＝observe_diag.merge_demand_into_ranking の「足す」1行
#          `merged = [list(x) for x in kept] + [[c, float(a)] for c, a in new]` から
#          `+ [[c, float(a)] for c, a in new]` を消す＝古い行を残すだけで、需給の行を足さなくなる。
#   測るもの＝`observe_diag.py --selftest-rank-demand`（数秒・T-f の②「sufficiency に3列」が ❌ になる）。
#   期待＝壊すと ❌ が出て終了コードが 1 になる。
#
# ★時間について（b35 の事故の教訓・2026-09-07）
#   承認のときの打ち切りは 120秒。測る相手は数秒の口だけにする（T-f の実測＝3秒・2026-09-07）。
#
# 限界（正直に書く）
#   ①壊すのは「足す」1行だけ（採点の側 rank_demand_for_regime を壊しても落ちるかは、この1本では測れない）
#   ②自己検査のほかの枝は見ない（終了コードだけを見る）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

T="$PR/observe_diag.py"
guard "$T"

# 壊す＝「足す」の部分を消す
python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
target = 'merged = [list(x) for x in kept] + [[c, float(a)] for c, a in new]'
if target not in s:
    raise SystemExit("壊す対象の行が見つからない（b39 の前提が変わった）")
s = s.replace(target, 'merged = [list(x) for x in kept]', 1)
open(p, 'w', encoding='utf-8').write(s)
PYEOF

# 測る＝T-f だけを走らせる口。②が ❌ を出せば 1 になる
measure python3 "$PR/observe_diag.py" --selftest-rank-demand
finish
