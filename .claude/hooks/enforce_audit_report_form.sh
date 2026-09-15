#!/bin/bash
# enforce_audit_report_form.sh — hook 11・PreToolUse on Write|Edit|MultiEdit|Bash（2026-09-15 まこさん指示・新設）
#
# 目的: 監査の結果（SDK/.claude/audits/<名前>_audit_report.md）を、テンプレの形でしか書けないようにする。
#   新しい結果の Write だけを通し、中身が gen_audit_docs.py の照らし（依頼書との1対1の対応・修正の指示の6つの欄・
#   書けないもの）を満たさなければ止める。一度出した結果は書き替えられない。
#   まこさん逐語「じゃあ、監査の依頼書と結果で項目をそろえて、テンプレ以外では書かないように強制すればいいじゃん。」
#
# ★判定は python の本体（enforce_audit_docs.py）に置く。hook 10（enforce_audit_request_gen.sh）と同じ本体を、mode だけ変えて呼ぶ。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で全廃）。

BASE="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
BODY="$BASE/.claude/hooks/enforce_audit_docs.py"

# 本体が無いときは止めない（fail-open）＝この hook 自身の不具合で作業を止めない
[ -f "$BODY" ] || exit 0

python3 "$BODY" report
exit $?
