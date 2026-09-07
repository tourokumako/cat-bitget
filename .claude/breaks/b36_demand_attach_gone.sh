#!/bin/bash
# b36 — 共通の道から需給を載せる呼び出しを消すと、実行器の自己検査が落ちるか
#
#   守っているもの＝next_step §6 の139番（設計書 iter="demand-attach-shared-path-20260907" の
#     完成の条件 #1）。
#   壊し方＝engine_tuner_exec.attach_recipe_columns の末尾から、需給の列を載せる3行を消す
#          （`_dem = demand_cols_in(recipe)` から `attach_demand_columns(...)` まで）。
#   測るもの＝`engine_tuner_exec.py --selftest`（8.7秒・番人139番の枝を含む）。
#   期待＝壊すと ❌ が出て終了コードが 1 になる。
#
# ★時間について（b35 の事故の教訓・2026-09-07）
#   承認のときの打ち切りは 120秒（run_breaks.py の TIMEOUT_SEC）。打ち切りは強制終了なので、
#   掛かると trap の「元に戻す」処理が走らず、壊した実物がそのまま残る。
#   だから測る相手は、実測で 120秒 に収まるものだけにする。
#   実測（2026-09-07）＝`python3 scripts/priority_rebuild/engine_tuner_exec.py --selftest` は 8.7秒。
#
# 限界（正直に書く）
#   ①壊すのは共通の道の呼び出し1か所だけ（部品 demand_cols_in・attach_demand_columns や、
#     生成器の側の呼び出しを壊しても落ちるかは、この1本では測れない）
#   ②自己検査のほかの枝は見ない（終了コードだけを見る）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

T="$PR/engine_tuner_exec.py"
guard "$T"

# 壊す＝共通の道から、需給の列を載せる3行を消す
python3 - "$T" <<'PYEOF'
import re
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = re.sub(
    r'\n *_dem = demand_cols_in\(recipe\)'
    r'\n *if _dem:'
    r'\n *out = attach_demand_columns\(out, sorted\(_dem\)\)',
    '', s)
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b36 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

# 測る＝実行器の自己検査。番人139番の枝が ❌ を出せば 1 になる
measure python3 "$PR/engine_tuner_exec.py" --selftest
finish
