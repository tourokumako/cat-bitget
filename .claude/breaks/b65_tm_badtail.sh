#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b65 — 「末の時刻が読めないものを報告する」処理を消すと、番人 T-o が落ちるか
#
#   守っているもの＝設計書 iter="tm-scope-and-g2-fingerprint-20260908" の完成の条件 #3。
#   何を守るか＝末の時刻が読めない5分足を、黙って飛ばさないこと。
#     直す前＝読めなければ何も言わずに飛ばしていたので、壊れたファイルや形の違う
#     ファイルが data に在っても、番人は何も言わなかった（監査 cp32 の別枠 B）。
#   壊し方＝読めなかった名前を集める処理を消し、今までどおり黙って飛ばす形へ戻す。
#   測るもの＝observe_diag.py --selftest-insp5（番人 T-o が、一時のフォルダで試す）。
#   期待＝戻すと T-o が落ちて 1 になる。
#
# ★時間について＝承認のときの打ち切りは 120秒。軽い口だけを走らせる。
#
# 限界（正直に書く）
#   ①T-o は「下の階層」と「末が読めないもの」の両方を見る＝この壊し方では後者だけが落ちる
#   ②このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
new = '''        if not ts:                                         # ★C＝読めないものを黙って飛ばさない
            bad.append(str(p.relative_to(d)))
            continue
'''
old = '''        if not ts:
            continue  # ★b65 が、読めないものを黙って飛ばす形へ戻した
'''
if new not in s:
    raise SystemExit("壊す対象の行が見つからない（b65 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s.replace(new, old, 1))
PYEOF

measure python3 "$OBS" --selftest-insp5
finish
