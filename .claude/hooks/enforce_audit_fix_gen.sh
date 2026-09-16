#!/bin/bash
# enforce_audit_fix_gen.sh — hook 12・PreToolUse on Write|Edit|MultiEdit（2026-09-16 まこさん承認・新設）
#
# 目的: 監査結果の修正を、当てる道具（.claude/tools/apply_audit_fix.py）以外では書けないようにする。
#   まこさん逐語 2026-09-14「今後はそのテンプレ以外では監査結果を書けないように強制してほしい」
#   （流れの強制 hook 3本のうちの3本目）。
#
# まこさんが決めた線引き（2026-09-16・逐語「１の線引は提案のものでOK」）
#   その修正を当て終わるまでの間だけ、そのファイルへの手書きを止める。当て終わったら普通に直せる。
#
# ★判定は python の本体（enforce_audit_fix.py）に置く（-c 埋め込みの引用符で無言死した教訓・pdca_flow.md §5）。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で全廃）。

BASE="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
BODY="$BASE/.claude/hooks/enforce_audit_fix.py"

# 本体が無いときは止めない（fail-open）＝この hook 自身の不具合で作業を止めない
[ -f "$BODY" ] || exit 0

python3 "$BODY"
exit $?
