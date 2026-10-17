#!/bin/bash
# forbid_edit_generated_docs.sh — PreToolUse on Write／Edit／MultiEdit（2026-09-17 まこさん指示・新設）
#
# 目的: 元データから作った文書（next_step.md と next_step_reference.md の全部・acceptance.md〔生成の目印が在るとき〕の全部・pdca_flow.md の §1 の hook の一覧）を、手で直す道を止める
#   （まこさん逐語「CCは確認せずミスを繰り返すので、手書きせざるをえないもの以外は自動生成にしてほしい」・
#    設計書 docs-autogen-next-step-pdca-20260917）。
#
# ★判定は python の本体（同名の .py）に置く（-c 埋め込みの引用符で無言死した教訓・pdca_flow.md §5）。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で全廃）。

BASE="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
BODY="$BASE/.claude/hooks/forbid_edit_generated_docs.py"

# 本体が無いときは止めない（fail-open）＝この hook 自身の不具合で作業を止めない
[ -f "$BODY" ] || exit 0

python3 "$BODY"
exit $?
