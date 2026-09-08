#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b56 — 1分足の元データの指し先を、古い（期間の足りない）ファイルに戻すと、番人が落ちるか
#
#   守っているもの＝設計書 iter="insp5-frame-and-table-tidy-20260908" の完成の条件 #3。
#   何を守るか＝1分足の元データが、値決め窓の助走ぶん前（2023-06-25）から採点窓の末まで覆っていること。
#     直す前の指し先は 2023-11-01 からで、約4か月 足りなかった（2026-09-08 に取り足した）。
#   壊し方＝ONE_MIN_CSV を、古いファイル（2023-11-01 から）に戻す。★古いファイルは消していない。
#   測るもの＝`observe_diag.py --selftest-insp5`（番人 T-i が 覆っているかを試す）。
#   期待＝壊すと T-i（元データが要る期間を覆っていない）が落ちて 1 になる。
#
# ★時間について＝承認のときの打ち切りは 120秒。軽い口だけを走らせる。
#
# 限界（正直に書く）
#   ①T-g と T-j も道連れで落ちる（元データを読む所で止まるため）＝3つとも「元データが足りない」
#     という同じ原因で落ちる。どの番人が落ちたかまでは終了コードから分からない
#   ②古いファイルが消されていたら、この壊し方は成り立たない（そのときは下の確認で止まる）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
OLD_CSV="$SDK/data/BTCUSDT-1m-binance-taker-2023-11-01_2026-06-30.csv"
if [ ! -f "$OLD_CSV" ]; then
    echo "❌ 戻す先の古いファイルが無い: $OLD_CSV（b56 の前提が変わった）" >&2
    exit 98
fi
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
new = 'ONE_MIN_CSV = "data/BTCUSDT-1m-binance-taker-2023-06-01_2026-06-30.csv"'
old = 'ONE_MIN_CSV = "data/BTCUSDT-1m-binance-taker-2023-11-01_2026-06-30.csv"'
if new not in s:
    raise SystemExit("壊す対象の行が見つからない（b56 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s.replace(new, old, 1))
PYEOF

measure python3 "$OBS" --selftest-insp5
finish
