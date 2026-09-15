#!/bin/bash
# enforce_audit_request_gen.sh — hook 10・PreToolUse on Write|Edit|MultiEdit|Bash（2026-09-15 まこさん指示・新設）
#
# 目的: 監査の依頼書（SDK/.claude/audits/inputs/<名前>_audit_request.md）を、
#   .claude/tools/gen_audit_docs.py request でしか作れないようにする（手で書けない・直せない）。
#   まこさん逐語「じゃあ、監査の依頼書と結果で項目をそろえて、テンプレ以外では書かないように強制すればいいじゃん。」
#
# ★判定は python の本体（enforce_audit_docs.py）に置く（-c 埋め込みの引用符で無言死した教訓・pdca_flow.md §5）。
#   hook 11（enforce_audit_report_form.sh）と同じ本体を、mode だけ変えて呼ぶ。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で全廃）。

BASE="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
BODY="$BASE/.claude/hooks/enforce_audit_docs.py"

# 本体が無いときは止めない（fail-open）＝この hook 自身の不具合で作業を止めない
[ -f "$BODY" ] || exit 0

python3 "$BODY" request
exit $?
