#!/bin/bash
LOG=/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/logs/cron.log
STATE=/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/state/monitor_pos.txt
NTFY=ntfy.sh/cat-bitget-alerts

# ログファイルが存在しない場合はスキップ
if [ ! -f "$LOG" ]; then
    exit 0
fi

# 現在の行数と前回チェック位置を取得
CURRENT=$(wc -l < "$LOG")
LAST=$(cat "$STATE" 2>/dev/null || echo 0)

# 新しい行をチェック
if [ "$CURRENT" -gt "$LAST" ]; then
    HIT=$(tail -n +$((LAST + 1)) "$LOG" | grep -m1 '"STOP\|"ERROR')
    if [ -n "$HIT" ]; then
        curl -s -d "⚠️ BOT異常: $HIT" $NTFY
    fi
fi

# チェック位置を更新
echo "$CURRENT" > "$STATE"