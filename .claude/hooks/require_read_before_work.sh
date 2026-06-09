#!/bin/bash
# require_read_before_work.sh — PreToolUse on Bash|Edit|Write|MultiEdit
# 必読6本を Read tool で実際に開く（record_read.sh が read_log に記録）まで、
# 作業ツール(Bash/Edit/Write/MultiEdit)を exit 2 で物理 block する。
# 目的: 新セッションで CC が必読を読まずに動く（読んだふり・勝手な値・暴走）を仕組みで防ぐ。
#   まこさん指示 2026-06-10:「読まないと手が動かない仕組みにしてほしい」。
# CC の決意では止まらない（session_log_20260609 §9）→ 物理強制。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
LOG="$STATE_DIR/read_log.txt"

# 必読6本（部分一致キーワード・session_log は最新の日付を含むので "session_log" でマッチ）
REQUIRED=("cat_requirements" "WORKFLOW" "session_log" "analysis_playbook" "ledger.md" "strat_v9ml_design")
LABEL=("cat_requirements.md(要件)" "WORKFLOW.md(現在地)" "session_log_最新(前回経緯)" "analysis_playbook.md(PDCA分析手順)" "ledger.md(PDCA実験記録)" "strat_v9ml_design.md(設計正本)")

missing=()
for idx in "${!REQUIRED[@]}"; do
  if ! grep -q "${REQUIRED[$idx]}" "$LOG" 2>/dev/null; then
    missing+=("${LABEL[$idx]}")
  fi
done

if [ ${#missing[@]} -gt 0 ]; then
  echo "🔒 [読了強制ゲート] 必読を Read tool で実際に読むまで Bash/Edit/Write は使えません。" >&2
  echo "未読（Read tool で開いていない）:" >&2
  for m in "${missing[@]}"; do echo "  - $m" >&2; done
  echo "" >&2
  echo "→ 上記を Read tool で開いてから作業してください。表示されているだけ/grep だけは読了になりません（読んだふり防止・まこさん指示・session_log §9）。" >&2
  exit 2
fi
exit 0
