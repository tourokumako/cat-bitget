#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b60 — 検査5 を走らせる条件を直す前へ戻すと、番人が落ちるか
#
#   守っているもの＝設計書 iter="insp5-path-and-tidy-head-20260908" の完成の条件 #3。
#   何を守るか＝検査5 とほかの検査を一緒に名指ししても、検査5 が走ること。
#     直す前＝検査5 が走る道は2つだけだった（①検査5 だけを名指ししたとき ②検査6 の直前）。
#     `--only 5,7` は走らせる段が「検査7」だけになるので、どちらにも当たらず、
#     検査5 は黙って走らなかった。それなのに、まとめには検査5 の行が出た（監査 cp31 の Major 2）。
#   壊し方＝`_insp_stage_plan` の戻りを、直す前の形（ほかの検査が無いときだけ検査5 を走らせる）へ戻す。
#   測るもの＝observe_diag.py --selftest-insp5（番人 T-k が見る）。
#   期待＝戻すと T-k が落ちて 1 になる。
#
# ★時間について＝承認のときの打ち切りは 120秒。軽い口だけを走らせる。
#
# 限界（正直に書く）
#   ①T-k は「検査5 を走らせるか」の判定だけを見る（検査5 が最後まで走ることは見ない）
#   ②このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
new = '    return [k for k in stage_keys if k in want], ("検査5" in want)\n'
old = ('    _sel = [k for k in stage_keys if k in want]\n'
       '    return _sel, ("検査5" in want and not _sel)\n')
if new not in s:
    raise SystemExit("壊す対象の行が見つからない（b60 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s.replace(new, old, 1))
PYEOF

measure python3 "$OBS" --selftest-insp5
finish
