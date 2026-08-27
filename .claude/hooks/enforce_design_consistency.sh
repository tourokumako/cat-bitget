#!/bin/bash
# enforce_design_consistency.sh — PreToolUse on Write／Edit／MultiEdit
#   （2026-08-27 まこさん承認「承認した」・設計書 29bb87e592df9053・新設・safety hook）
#
# 目的: 設計書（.claude/state/acceptance.md）の中で、同じ対象について食い違う判定が
#   2つ以上 書かれていたら、書き込みを止める（5回目の監査 cp6 の P-1・next_step §6 の94番）。
#
# ★判定は python の本体（同名の .py）に置く。
#   理由＝pdca_mark が 2026-07-03 に -c 埋め込みの引用符で無言死した教訓（pdca_flow.md §5）。
#
# safety hook: fast-mode の一時無効化の行を入れない（この hook は毎回 効く）。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で全廃）。

BASE="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
BODY="$BASE/.claude/hooks/enforce_design_consistency.py"

# 本体が無いときは止めない（fail-open）＝この hook 自身の不具合で作業を止めない
[ -f "$BODY" ] || exit 0

python3 "$BODY"
exit $?
