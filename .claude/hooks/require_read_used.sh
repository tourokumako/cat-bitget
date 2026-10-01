#!/bin/bash
# require_read_used.sh — Stop（2026-10-01・142回目 新設）
#
# 中身は require_read_used.py（hook の python は別ファイル化の規約）。
# そのターンで読んだファイルごとに、どの行を判断の根拠にしたか（か、使わなかったか）を返信に示すまで終わらせない。

exec python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/require_read_used.py" "$@"
