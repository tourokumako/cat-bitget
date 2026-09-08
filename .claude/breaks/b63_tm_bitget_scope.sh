#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b63 — 「Binance Spot 系列だけを見る」判定を消すと、番人 T-n が落ちるか
#
#   守っているもの＝設計書 iter="tm-scope-and-g2-fingerprint-20260908" の完成の条件 #1。
#   何を守るか＝番人 T-m が指す5分足を、Binance Spot 系列だけにすること。
#     要件定義書 §8.2.1.1 の②の逐語＝「採点に使うのは Binance Spot 系列だけ」。
#     直す前＝`data/BTCUSDT-5m-*.csv` という名前で見分けていたので、Bitget 先物の足
#     （`BTCUSDT-5m-bitget-…`）まで当たり、「BARS_CSV の指し先を直す」と言っていた。
#     ＝読んだ人を、禁じられている方へ導く形だった（監査 cp32 の Major）。
#   壊し方＝名前に bitget を含むものを飛ばす判定を消す。
#   測るもの＝observe_diag.py --selftest-insp5（番人 T-n が、一時のフォルダで試す）。
#   期待＝消すと T-n が落ちて 1 になる。
#
# ★時間について＝承認のときの打ち切りは 120秒。軽い口だけを走らせる。
#
# 限界（正直に書く）
#   ①T-n は「名前に bitget を含むか」だけを見る＝別の名前の系列は見分けられない
#   ②このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
new = '''        if "bitget" in p.name.lower():                     # ★A＝Binance Spot 系列だけを見る
            continue
'''
old = '''        pass  # ★b63 が、Binance Spot 系列だけを見る判定を消した
'''
if new not in s:
    raise SystemExit("壊す対象の行が見つからない（b63 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s.replace(new, old, 1))
PYEOF

measure python3 "$OBS" --selftest-insp5
finish
