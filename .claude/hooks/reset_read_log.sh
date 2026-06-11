#!/bin/bash
# reset_read_log.sh — SessionStart
# 新セッション開始時に read_log をリセット（前セッションの読了を引き継がない）。
# これで毎セッション、必読を Read tool で読み直すまで作業ツールが block される。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
mkdir -p "$STATE_DIR"
: > "$STATE_DIR/read_log.txt"
# 目標逆算ゲート（ゲート2）もリセット: 前セッションの逆算ブロックを引き継がない
rm -f "$STATE_DIR/goal_block.md"

echo "=== [読了強制ゲート 有効] ==="
echo "必読6本を Read tool で実際に開くまで、Bash/Edit/Write は block されます（読んだふり防止）:"
echo "  1. cat_requirements.md（要件・制約・PDCA）"
echo "  2. WORKFLOW.md（現在地・次タスク）"
echo "  3. session_log_最新.md（前回の経緯・失敗）"
echo "  4. analysis_playbook.md（PDCA 分析手順）"
echo "  5. ledger.md（PDCA 実験記録）"
echo "  6. strat_v9ml_design.md（設計の正本）"
echo "  7. lessons_active.md（教訓・直近 L-259＝今日の失敗 を必ず読む）"
echo "→ grep や表示だけでは解除されません。Read tool で開いてください。"
echo ""
echo "=== [目標逆算ゲート 有効・WORKFLOW Step 0 ④] ==="
echo "必読後、目標逆算ブロック（5行+3行ゲート）を .claude/state/goal_block.md に Write し、"
echo "同内容をチャットに出してまこさんの GO を得るまで、Bash/Edit/Write は block されます。"
echo "（届かない候補を単体ミッションにしない・導出の向き＝届く構成から逆算・2026-06-12）"
exit 0
