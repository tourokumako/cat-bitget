#!/bin/bash
# require_leak_annotation.sh — PreToolUse on Write|Edit（2026-07-04 まこさん承認で新設）
# H2 leak パターン（.shift(- / center=True）を scripts/priority_rebuild/*.py に書く瞬間、
# 行内の「# H2OK: <理由>」アノテーションが無ければブロック。本体は require_leak_annotation.py
#（hook の python は -c 埋め込み禁止＝別ファイル化・pdca_mark 無言死事案 2026-07-03 の規約）。
PY="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/require_leak_annotation.py"
OUT=$(python3 "$PY" 2>&1)
RC=$?
if [ "$RC" -eq 2 ]; then
  echo "$OUT" >&2
  exit 2
fi
exit 0
