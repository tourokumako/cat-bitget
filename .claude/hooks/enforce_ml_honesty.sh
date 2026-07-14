#!/bin/bash
[ -f "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode" ] && exit 0  # [fast-mode] process hook を一時無効化（touch/rm pdca_fast_mode で切替・safety hook には入れない・2026-07-16）
# enforce_ml_honesty.sh — PreToolUse on Write|Edit（2026-07-13 まこさん指示・機械学習の不正防止の1枚目=doc 層）
# 機械学習 正直ゲート: acceptance.md / improvement_plan.md / *_design.md を書く瞬間、機械学習(ML/教師/分類器/
# LightGBM 等)を名乗るなら正直な宣言ブロック ML_DECL（目的/教師/学習内容/学習方法/自己申告）を要求し、
# 疑似ML/インチキ設計 P0〜P4（宣言欠落/目的↔教師ズレ/ML飾り/疑似最適化詐称/教師leak）を弾く。
# 本体は enforce_ml_honesty.py（hook の python は -c 埋め込み禁止＝別ファイル化の規約）。
PY="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/enforce_ml_honesty.py"
INPUT=$(cat)
OUT=$(printf '%s' "$INPUT" | python3 "$PY" 2>&1)
RC=$?
if [ "$RC" -eq 2 ]; then
  echo "$OUT" >&2
  exit 2
fi
exit 0
