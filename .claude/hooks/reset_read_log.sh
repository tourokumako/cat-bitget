#!/bin/bash
# reset_read_log.sh — SessionStart
# 新セッション開始時に read_log をリセット（前セッションの読了を引き継がない）。
# これで毎セッション、必読を Read tool で読み直すまで作業ツールが block される。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
mkdir -p "$STATE_DIR"
: > "$STATE_DIR/read_log.txt"

echo "=== [読了強制ゲート 有効] ==="
echo "必読6本を Read tool で実際に開くまで、Bash/Edit/Write は block されます（読んだふり防止）:"
echo "  1. cat_requirements.md（要件・制約・PDCA）"
echo "  2. WORKFLOW.md（現在地・次タスク）"
echo "  3. session_log_最新.md（前回の経緯・失敗）"
echo "  4. analysis_playbook.md（PDCA 分析手順）"
echo "  5. ledger.md（PDCA 実験記録）"
echo "  6. strat_v9ml_design.md（設計の正本）"
echo "→ grep や表示だけでは解除されません。Read tool で開いてください。"
exit 0
