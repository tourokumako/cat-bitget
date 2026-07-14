#!/bin/bash
[ -f "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode" ] && exit 0  # [fast-mode] process hook を一時無効化（touch/rm pdca_fast_mode で切替・safety hook には入れない・2026-07-16）
# show_budget_before_design.sh — PreToolUse on Write|Edit
# 設計/改善案を書く瞬間（acceptance.md / *_design.md）に、予算 0.12 BTC は【全採用戦略の共有枠】を
# 1セッション1回だけ表示（exit 2 でブロック→再実行で通す＝確実に目に入る・毎回ブロックは煩いので1回）。
#
# 経緯: CC が 0.12 を単一戦略の枠に矮小化（CLAUDE §0-2 / cat_requirements §6.1 明記でも auto-load では
#   錨が下りない）。まこさん「強制表示は SessionStart でなく改善案/設計の提案の瞬間に出せ・SessionStart は
#   効果ない」（2026-06-20・memory feedback_enforcement_at_proposal_time）。just-in-time 強制。
# マーカーは reset_read_log.sh が SessionStart で消す（セッションごとに1回）。

STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
MARK="$STATE/budget_rule_shown"
REG="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/adopted_strategies.md"

INPUT=$(cat)

# サブエージェント（Workflow/Agent 内）は通す（デッドロック回避）
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

FILE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)

# 設計/改善案ファイルだけ対象（acceptance.md / *_design.md）
case "$FILE" in
  *acceptance.md|*_design.md) ;;
  *) exit 0 ;;
esac

# 既にこのセッションで表示済みなら通す（1セッション1回）
[ -f "$MARK" ] && exit 0
touch "$MARK"

{
echo "=================================================================="
echo "💰 設計/改善案の前に確認（予算ルール・CC が繰り返し誤解・1回表示）"
echo "=================================================================="
echo "⚠️ 0.12 BTC は【全採用戦略の共有枠】＝単一戦略（この戦略）の枠ではない。"
echo "   任意の時点 t で、採用済み全戦略の全建玉 size を合計して ≤0.12 BTC"
echo "   （CLAUDE §0-2「1ポジあたりでなく合計上限」／ cat_requirements §6.1 / H1）。"
echo "   配分は戦略間で柔軟・合計のみが絶対制約。"
echo "⛔ 「この戦略の cap 0.12」と矮小化しない。既存採用戦略と同じ 0.12 を奪い合う＝"
echo "   合算で測り、同方向は上乗せ(additive)か食い合いかを必ず確認。"
echo "--- 採用済み戦略 台帳（adopted_strategies.md・全採用戦略がこの 0.12 を共有）---"
if [ -f "$REG" ]; then
  grep -E '^\| ' "$REG" | grep -vE '^\| 戦略|^\| レバー|^\| 構成|---' | head -8
fi
echo "→ 全文: .claude/ratchet/adopted_strategies.md"
echo "（このメッセージは1セッション1回・確認したら同じ Write を再実行すれば通ります）"
echo "=================================================================="
} >&2
exit 2
