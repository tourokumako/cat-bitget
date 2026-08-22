#!/bin/bash
# forbid_interpretation_file.sh — PreToolUse on Write|Edit|MultiEdit|Bash（2026-08-22 まこさん承認・新設・safety hook）
#
# 中身は forbid_interpretation_file.py（hook の python は -c 埋め込み禁止・別ファイル化の規約）。
# 解釈の記録ファイル（.claude/state/interpretation.md ／ interpretation_posted）への書き込みを止める。
# 削除（rm）と読み取り（cat・grep・git）は通す。
# 解除: 無し（合言葉は 2026-08-16 に全廃）。

exec python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/forbid_interpretation_file.py" "$@"
