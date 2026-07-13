#!/bin/bash
# enforce_optimization_honesty.sh — PreToolUse on Write|Edit（2026-07-13 まこさん指示「学習による最適化詐欺を今後働けないようにしろ」）
# 最適化 正直ゲート: acceptance.md / improvement_plan.md / *_design.md を書く瞬間、「最適化/ML最適化/optuna/
# グリッドサーチ/greedy 選定」等を名乗るなら、正直な宣言ブロック OPT_DECL（6項目）を要求し、手置きメニューの
# greedy を「最適化」と肯定的に呼ぶのをブロックする。ロジック本体は enforce_optimization_honesty.py
# （hook の python は -c 埋め込み禁止＝別ファイル化・pdca_mark 無言死事案 2026-07-03 の規約）。
PY="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/enforce_optimization_honesty.py"
INPUT=$(cat)
OUT=$(printf '%s' "$INPUT" | python3 "$PY" 2>&1)
RC=$?
if [ "$RC" -eq 2 ]; then
  echo "$OUT" >&2
  exit 2
fi
exit 0
