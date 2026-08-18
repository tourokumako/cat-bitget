#!/bin/bash
# enforce_chat_writing.sh — チャット文章の検査の入口（Stop hook・2026-08-18 新設・まこさん指示「強制できないの？」）
# 判定の本体は同名の .py に置く（hook の python を -c で埋め込まない規約・pdca_flow.md §5）。
# safety hook: fast-mode で無効にしない。理由＝文章が伝わらない問題は fast-mode 中に起きているため。
exec python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/enforce_chat_writing.py
