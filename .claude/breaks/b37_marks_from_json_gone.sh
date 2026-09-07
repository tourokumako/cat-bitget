#!/bin/bash
# b37 — 目印を置き換える処理を消すと、印の値の自己検査が落ちるか
#
#   守っているもの＝next_step §6 の144番（設計書 iter="marks-from-json-20260907" の
#     完成の条件 #1）。監査 cp25 の §5-4。
#   壊し方＝gen_regime_kb.build から `apply_marks(...)` を外し、置き換えないまま返す形にする。
#   測るもの＝`gen_regime_kb.py --selftest-marks`（0.17秒・印の枝2件だけ）。
#   期待＝壊すと ❌ が出て終了コードが 1 になる。
#
# ★なぜ全体の --selftest を測らないか（実測 2026-09-07）
#   全体は T7・T9・T11 が ❌ で rc=1 のまま。中身は §11・§12 の未反映と引用の行番号のずれで、
#   どれも別の工事（M2-B）のもの。全体を測ると、この工事の完成の条件を永久に測れない。
#
# ★時間について（b35 の事故の教訓・2026-09-07）
#   承認のときの打ち切りは 120秒（run_breaks.py の TIMEOUT_SEC）。打ち切りは強制終了なので、
#   掛かると trap の「元に戻す」処理が走らず、壊した実物がそのまま残る。
#   だから測る相手は、実測で 120秒 に収まるものだけにする（この口は 0.17秒）。
#
# 限界（正直に書く）
#   ①壊すのは `build` の中の呼び出し1か所だけ（`marks_now`・`apply_marks` の中身を壊しても
#     落ちるかは、この1本では測れない）
#   ②元データ（m2_todo.json）から目印を消して生の値を書き戻す道は、これでは止められない
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/tools/gen_regime_kb.py"
guard "$T"

# 壊す＝build から apply_marks の呼び出しを外す
python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = s.replace("    return apply_marks(BUILDER[kind](d))",
              "    return BUILDER[kind](d)")
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b37 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

# 測る＝印の枝だけの口。置き換えが消えれば ❌ が出て 1 になる
measure python3 "$T" --selftest-marks
finish
