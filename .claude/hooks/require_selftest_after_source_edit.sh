#!/bin/bash
# require_selftest_after_source_edit.sh — PostToolUse on Write／Edit／MultiEdit（引数 post）＋ Stop（引数 stop）
#   （2026-09-16 まこさん指示「この３つのミスを繰り返さない仕組みを作れ」・新設・L-604・next_step §0-2 の仕組み2）
#
# 目的: テンプレや元データを書き替えたら、それを読む道具の自己テストを走らせるまでターンを終われなくする。
#
# ★判定は python の本体（同名の .py）に置く（-c 埋め込みの引用符で無言死した教訓・pdca_flow.md §5）。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で全廃）。

BASE="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
BODY="$BASE/.claude/hooks/require_selftest_after_source_edit.py"

# 本体が無いときは止めない（fail-open）＝この hook 自身の不具合で作業を止めない
[ -f "$BODY" ] || exit 0

python3 "$BODY" "${1:-stop}"
exit $?
