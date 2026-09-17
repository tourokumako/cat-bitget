#!/bin/bash
# show_breaks_on_code_edit.sh — PreToolUse on Write／Edit／MultiEdit（2026-09-16 まこさん指示・新設）
#
# 目的: コードの行を直す直前に、その行を文字で探している壊すプログラム（.claude/breaks/*.sh）を見せて1回止める
#   （まこさん逐語「この３つのミスを繰り返さない仕組みを作れ」・L-605・next_step §0-2 の仕組み1の前半）。
#
# ★判定は python の本体（同名の .py）に置く（-c 埋め込みの引用符で無言死した教訓・pdca_flow.md §5）。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で全廃）。

BASE="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
BODY="$BASE/.claude/hooks/show_breaks_on_code_edit.py"

# 本体が無いときは止めない（fail-open）＝この hook 自身の不具合で作業を止めない
[ -f "$BODY" ] || exit 0

python3 "$BODY"
exit $?
