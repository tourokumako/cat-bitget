#!/bin/bash
# require_trial_before_proposal.sh — 設計書の案を出す前に、試しの設計書で全部の検査を通させる（Stop hook・本体は .py）
# まこさん指示（2026-09-30・逐語）＝「一回の確認ですべて完全に修正できるように強制しろ」
set -u
ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
exec python3 "$ROOT/.claude/hooks/require_trial_before_proposal.py"
