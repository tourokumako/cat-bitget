#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b54 — 0-2 の表の「終わった行」を移す処理を消すと、番人が落ちるか
#
#   守っているもの＝設計書 iter="insp5-frame-and-table-tidy-20260908" の完成の条件 #4
#     （監査 cp26 の §6-7＝並走した2つのセッションが、同じ Stop hook で同時に止まった）。
#   何を守るか＝tidy_next_step.py の書き替えの口が、0-2 の表の「✅済」と取り消し線の行を
#     控えへ移して表から消す。直す前は、移す手段が節にしか無く、表の行は人が手で消すしかなかった。
#   壊し方＝move_done_rows の「移す行の見分け方」を、1行も当たらない形にする。
#   測るもの＝`tidy_next_step.py --selftest`（番人 T10a・T10b が 移ることを試す）。
#   期待＝壊すと T10a と T10b が落ちて 1 になる（T10c＝説明の文は移さない、は通ったまま＝緩めていない）。
#
# ★時間について＝承認のときの打ち切りは 120秒。実測（2026-09-08）＝1秒 未満。
#
# 限界（正直に書く）
#   ①壊すのは見分け方の1行だけ（書き替えの口から呼び出しを消す壊し方は、この1本では測れない）
#   ②移した中身が正しいかは見ない（印の数の照合は check_marks が別に守る）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

TIDY="$ROOT/.claude/tools/tidy_next_step.py"
guard "$TIDY"

python3 - "$TIDY" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
new = '        if s2 <= k < end and ln.lstrip().startswith("|") and (DONE_MARK in ln or STRIKE_RE.search(ln)):\n'
old = '        if False:\n'
if new not in s:
    raise SystemExit("壊す対象の行が見つからない（b54 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s.replace(new, old, 1))
PYEOF

measure python3 "$TIDY" --selftest
finish
