#!/bin/bash
# require_full_check_before_handoff.sh — お願い・「できた」の返信の前に、後で走る検査を全部 1回で通させる（Stop hook・本体は .py）
# まこさん指示（2026-09-30・逐語）＝「一回の確認ですべて完全に修正できるように強制しろ」「承認後に修正が発生しないように、事前にミスが無いよう確認をしろ」
set -u
ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
exec python3 "$ROOT/.claude/hooks/require_full_check_before_handoff.py"
