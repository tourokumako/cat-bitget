#!/bin/bash
# b48 — 囲みの中を読み飛ばす処理を消すと、番人が落ちるか
#
#   守っているもの＝next_step §6 の113番（設計書 iter="approval-audit-plumbing-20260907" の
#     完成の条件 #9）。
#   何を守るか＝必読ゲートは、行の頭が TARGET: かどうかだけを見て、囲みの中かどうかを
#     見ていなかった。だから設計書に「書き方の見本」を載せると、その見本のパスまで
#     「開いたか」を確かめられて止まった（2026-08-27 に実際に止まり、見本の行の頭に
#     空白を2つ入れて回り道した）。
#   壊し方＝_line_values が囲みを読み飛ばすのをやめる（outside_fence を使わない形に戻す）。
#   測るもの＝`require_source_read_before_acceptance.py --selftest`（番人 F1 が この形を試す）。
#   期待＝壊すと F1 が落ちて終了コードが 1 になる。
#
# ★時間について（b35 の事故の教訓）＝承認のときの打ち切りは 120秒。実測（2026-09-07）＝1秒未満。
#
# 限界（正直に書く）
#   ①壊すのは1か所だけ（claimed_files の側を消す壊し方は、この1本では測れない＝番人 F2 が見る）
#   ②番人のほかの枝は見ない（終了コードだけを見る）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/hooks/require_source_read_before_acceptance.py"
guard "$T"

python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = s.replace(
    '    for ln in outside_fence(text):\n'
    '        if not ln.startswith(prefix):\n',
    '    for ln in text.splitlines():\n'
    '        if not ln.startswith(prefix):\n',
    1)
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b48 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

measure python3 "$T" --selftest
finish
