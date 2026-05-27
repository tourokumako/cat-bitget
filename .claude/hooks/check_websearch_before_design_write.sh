#!/bin/bash
# L-236 physical enforcement: block Write/Edit to ml_pipeline_baseline_v1.md without recent WebSearch
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('tool_input', {}).get('file_path', ''))" 2>/dev/null)

if [[ "$FILE_PATH" != *"ml_pipeline_baseline"* ]]; then
    exit 0
fi

MARKER="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/last_websearch.timestamp"

if [[ ! -f "$MARKER" ]]; then
    echo "BLOCKED: ml_pipeline_baseline への Write/Edit には直近 10 分以内の WebSearch 実行が必要 (L-236 物理強制)" >&2
    exit 2
fi

LAST=$(cat "$MARKER")
NOW=$(date +%s)
DIFF=$((NOW - LAST))

if [[ $DIFF -gt 600 ]]; then
    echo "BLOCKED: 最後の WebSearch は ${DIFF} 秒前 (= 10 分以上前)。WebSearch 再実行が必要 (L-236)" >&2
    exit 2
fi

exit 0
