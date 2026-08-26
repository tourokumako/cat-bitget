#!/bin/bash
# check_chat_draft.sh — 長い返信の下書きを、書き込みの瞬間に検査する（PreToolUse・2026-08-26 新設）
#
# なぜ要るか（まこさんの問い 2026-08-26・逐語「１文の長さは書く前にどうにかできないのか？」）:
#   チャットの文章の検査（Stop hook）は、私の文章が まこさんの画面に出た「後」にしか走らない。
#   だから止めると、書き直した文章がもう一度 並ぶ＝同じ文章が連続で出る（実測 179回）。
#   道具を使う「前」なら止められる。だから長い返信は下書き（.claude/state/chat_draft.md）に一度 書く。
#   その書き込みの瞬間にここが走る。ここで止まっても、まこさんの画面には何も出ていない。
#
# 判定の中身は enforce_chat_writing.py と同じ関数を呼ぶ（二重に作らない＝検査がずれない）。
# safety hook: fast-mode で無効にしない。
#
# 限界（正直に）: 下書きを作らずに直接チャットへ出す道は塞げない。
exec python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/enforce_chat_writing.py --pretool
