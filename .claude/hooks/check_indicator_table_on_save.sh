#!/bin/bash
# check_indicator_table_on_save.sh — 定義表（indicator_reference_diag.py）を保存する瞬間に、INDICATOR_TABLE の照らしを掛ける
#   （PreToolUse Write|Edit|MultiEdit・本体は .py・工事 m2c15-single-source-20261022・2026-10-22）
set -u
ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
exec python3 "$ROOT/.claude/hooks/check_indicator_table_on_save.py"
