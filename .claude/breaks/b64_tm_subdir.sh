#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b64 — 下の階層を見る形を直す前へ戻すと、番人 T-o が落ちるか
#
#   守っているもの＝設計書 iter="tm-scope-and-g2-fingerprint-20260908" の完成の条件 #2。
#   何を守るか＝番人 T-m が、data の**下の階層**に置かれた5分足も見つけること。
#     直す前＝直下だけを見ていたので、`data/<下の階層>/BTCUSDT-5m-…csv` に置かれた
#     取り足しの5分足を見つけられなかった（監査 cp32 の別枠 A が実測した）。
#   壊し方＝下の階層まで見る形（rglob）を、直下だけを見る形（glob）へ戻す。
#   測るもの＝observe_diag.py --selftest-insp5（番人 T-o が、一時のフォルダで試す）。
#   期待＝戻すと T-o が落ちて 1 になる。
#
# ★時間について＝承認のときの打ち切りは 120秒。軽い口だけを走らせる。
#
# 限界（正直に書く）
#   ①T-o は「下の階層」と「末が読めないもの」の両方を見る＝この壊し方では前者だけが落ちる
#     （終了コードからは、どちらが落ちたかまで分からない）
#   ②このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
new = '    for p in sorted(d.rglob("BTCUSDT-5m-*.csv")):          # ★B＝下の階層も見る\n'
old = '    for p in sorted(d.glob("BTCUSDT-5m-*.csv")):           # ★b64 が、直下だけに戻した\n'
if new not in s:
    raise SystemExit("壊す対象の行が見つからない（b64 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s.replace(new, old, 1))
PYEOF

measure python3 "$OBS" --selftest-insp5
finish
