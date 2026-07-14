#!/bin/bash
[ -f "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode" ] && exit 0  # [fast-mode] process hook を一時無効化（touch/rm pdca_fast_mode で切替・safety hook には入れない・2026-07-16）
# enforce_ml_wiring.sh — PreToolUse on Bash（2026-07-13 まこさん指示・機械学習の不正防止の2枚目＝実行前コード照合）
# ML を名乗る戦略を python で実行する前に、acceptance.md の ML_CONTRACT（fenced json）を読み、
# 自己申告『本物のML』なら ML 予測が決定に配線されているか（飾りでないか）を AST で照合し、飾りなら実行ブロック。
# 本体は enforce_ml_wiring.py（hook の python は -c 埋め込み禁止＝別ファイル化の規約）。
PY="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/enforce_ml_wiring.py"
INPUT=$(cat)
OUT=$(printf '%s' "$INPUT" | python3 "$PY" 2>&1)
RC=$?
if [ "$RC" -eq 2 ]; then
  echo "$OUT" >&2
  exit 2
fi
exit 0
