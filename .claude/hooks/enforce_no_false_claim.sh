#!/bin/bash
# enforce_no_false_claim.sh — 作った引用・開いていない行の引用を止める（Stop hook・2026-09-28 新設）
# まこさん指示（逐語）「とにかく、虚偽発言できないようにしろ」。本体は同名の .py（hook の python を -c で埋め込まない規約）。
# safety hook: fast-mode で無効にしない。
exec python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/enforce_no_false_claim.py
