#!/bin/bash
# enforce_checked_edit.sh — PreToolUse on Write／Edit／MultiEdit（2026-09-14 まこさん指示・新設）
#
# 目的: あらゆるファイルを直すとき、①書き足す行番号（拡張子を問わない）を実物で開いたか ②消す数・行番号と同じ文字が
#   ほかに残っていないか、をやらせる（まこさん逐語「実物を開いて確かめていない直しは、書きません。
#   直したら、同じ事実を書いている場所を全部 grep して揃えてから出します。」「上記のやり方をやるようにしろ」
#   「設計書の元データと監査の依頼書を直すとき限定ではない。あらゆる修正対応のとき」）。
#
# ★判定は python の本体（同名の .py）に置く（-c 埋め込みの引用符で無言死した教訓・pdca_flow.md §5）。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で全廃）。

BASE="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
BODY="$BASE/.claude/hooks/enforce_checked_edit.py"

# 本体が無いときは止めない（fail-open）＝この hook 自身の不具合で作業を止めない
[ -f "$BODY" ] || exit 0

python3 "$BODY"
exit $?
