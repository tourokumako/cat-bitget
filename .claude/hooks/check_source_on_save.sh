#!/bin/bash
# check_source_on_save.sh — 「元」（監査依頼の手書きの文書）を保存する瞬間に、作るプログラムと同じ検査を掛ける
#   （PreToolUse Write|Edit|MultiEdit・本体は .py・2026-10-10 まこさん指示「この強制は作って」）
set -u
ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
exec python3 "$ROOT/.claude/hooks/check_source_on_save.py"
