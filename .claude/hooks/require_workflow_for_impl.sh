#!/bin/bash
# cc_role §1.4.6.3 物理強制: メインセッションが実装スクリプト(scripts/priority_rebuild/*.py)を
# 直接 Write/Edit するのを block し、複数CCチェック(Workflow)経由の実装を強制する。
#
# 設計根拠(実測 2026-06-07・probe で確定):
#   - 親セッションの PreToolUse hook は Workflow 内サブエージェントの tool 呼び出しにも適用される。
#   - メイン vs サブエージェントは stdin JSON の "agent_type" フィールドで見分けられる
#     (サブエージェントは "workflow-subagent" 等が付く / メインは agent_type 無し)。
#   → サブエージェント(agent_type 付き)は通す = Workflow 内の実装CCを block しない(デッドロック回避)。
INPUT=$(cat)

# 1) サブエージェント(Workflow/Agent 内)の Write/Edit は通す
AGENT_TYPE=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
if [[ -n "$AGENT_TYPE" ]]; then
  exit 0
fi

# 2) メインのみ到達。実装スクリプト(戦略 .py)への直接編集だけ block
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)
if [[ "$FILE_PATH" == *scripts/priority_rebuild/*.py ]]; then
  echo "BLOCKED: 実装スクリプト($FILE_PATH)のメイン直接編集は禁止。複数CCチェック(Workflow)経由で実装すること (cc_role §1.4.6.3・実装CC→設計書照合CC→不正チェックCC→まとめCC)。" >&2
  exit 2
fi
exit 0
