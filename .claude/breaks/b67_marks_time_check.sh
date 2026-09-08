#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b67 — 印の時刻を照らす検査を消すと、足した番人が落ちるか
#
#   守っているもの＝設計書 iter="tm-scope-and-g2-fingerprint-20260908" の完成の条件 #5。
#   何を守るか＝next_step の (0-b-2) に書いてある印の**時刻**が、json と合っていること。
#     直す前＝検査 (c) は指紋の値だけを照らしていたので、印を取り直した後に `--write` を
#     走らせ忘れると、時刻だけが古いまま残った（監査 cp32 の別枠 E が実測した）。
#     ★この工事の最中に、足した検査が本物の食い違いを1件 見つけた（H2 と G2 の時刻）。
#   壊し方＝時刻を照らす2行を消す。
#   測るもの＝tidy_next_step.py --selftest（足した番人 T4b）。
#   期待＝消すと T4b が落ちて 1 になる。
#
# 限界（正直に書く）
#   ①時刻の文字が (0-b-2) の中に在るかしか見ない（意味の正しさは見ない）
#   ②このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

TIDY="$ROOT/.claude/tools/tidy_next_step.py"
guard "$TIDY"

python3 - "$TIDY" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
new = '''        if h2["when"] not in body:
            ng.append(f"(c) (0-b-2) の H2 の時刻が json（{h2['when']}）と違う → `--write`")
        if g2["when"] not in body:
            ng.append(f"(c) (0-b-2) の G2 の時刻が json（{g2['when']}）と違う → `--write`")
'''
old = '''        pass  # ★b67 が、印の時刻を照らす検査を消した
'''
if new not in s:
    raise SystemExit("壊す対象の行が見つからない（b67 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s.replace(new, old, 1))
PYEOF

measure python3 "$TIDY" --selftest
finish
