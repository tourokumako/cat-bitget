#!/bin/bash
# forbid_guess_retry.sh — 確かめずに当てずっぽうで検査に当たるまで直し続けるやり方を禁じる（本体は .py・引数 post／pre）
# まこさん指示（2026-09-30・逐語）＝「確認をせずに、当てずっぽうで当たるまでやり続けるような修正方法は禁じる。」
set -u
ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
exec python3 "$ROOT/.claude/hooks/forbid_guess_retry.py" "${1:-}"
