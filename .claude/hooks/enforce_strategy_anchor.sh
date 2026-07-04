#!/bin/bash
# enforce_strategy_anchor.sh — PreToolUse on Write|Edit（2026-07-04 まこさん承認で新設）
# 戦略係留ゲート: acceptance.md を書く瞬間に、TARGET 戦略の担当局面・方向（台帳 STRATEGY_ANCHOR マーカー
# ＝cat_requirements §1.2.1 の機械可読形）との照合を物理強制する。ロジック本体は enforce_strategy_anchor.py
# （hook の python は -c 埋め込み禁止＝別ファイル化・pdca_mark 無言死事案 2026-07-03 の規約）。
PY="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/enforce_strategy_anchor.py"
OUT=$(python3 "$PY" 2>&1)
RC=$?
if [ "$RC" -eq 2 ]; then
  echo "$OUT" >&2
  exit 2
fi
exit 0
