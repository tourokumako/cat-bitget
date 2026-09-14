#!/bin/bash
# limit_repeat_verification.sh — PreToolUse on Agent（2026-09-14 まこさん指示・新設）
#
# 目的: 同じ設計書・監査レポート・依頼書の照合の agent を、1つのセッションで2回目に走らせようとしたら止め、
#   先に まこさんへ報告させる（まこさん逐語「照合を「0件になるまで」繰り返す形は作りません。」
#   「上記のやり方をやるようにしろ」「トークンの無駄なので、こんな無駄なことやめてほしい」）。
#
# ★判定は python の本体（同名の .py）に置く（-c 埋め込みの引用符で無言死した教訓・pdca_flow.md §5）。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で全廃）。

BASE="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
BODY="$BASE/.claude/hooks/limit_repeat_verification.py"

# 本体が無いときは止めない（fail-open）＝この hook 自身の不具合で作業を止めない
[ -f "$BODY" ] || exit 0

python3 "$BODY"
exit $?
