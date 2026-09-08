#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b06 — 照合の道具を1文字 変えると、止まるか
#
#   守っているもの＝next_step §6 の131番（設計書 iter="approval-audit-plumbing-20260907" の
#     完成の条件 #6）。
#   壊し方＝照合の道具（verify_design_contract.py）の末尾にコメントを1行 足す。
#   測るもの＝本物の照合（check の道）。道具の指紋は check_impl_functions（928-942行）が
#     .claude/state/verify_tool.approved と照らす。
#   期待＝壊すと「照合の道具が承認のときから変わっている」で終了コードが 0 以外になる。
#
# ★2026-09-07（131番）に測る道を直した。
#   直す前＝`--diff <設計書>` を測っていた。--diff は SPEC（関数の名前と呼ぶ名前）の
#     突き合わせだけで、**道具の指紋を1度も見ない**。
#   実測（2026-09-07 の承認のとき）＝b06 は rc=1 と出たが、それは道具の書き換えを
#     見つけたからではなく、いまの設計書に SPEC の節が無くて
#     「SPEC が設計書に無い（対象外）」で止まっただけだった＝**測れていなかった**。
#
# 限界（正直に書く）
#   ①壊すのはコメント1行だけ（中身を変える壊し方は、この1本では測れない）
#   ②指紋の印（verify_tool.approved）を手で書き換える道は、これでは止められない
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

guard "$VERIFY"

printf '\n# break test\n' >> "$VERIFY"

measure python3 "$VERIFY" "$ROOT/.claude/state/acceptance.md"
finish
