#!/bin/bash
# b11 — サブエージェントでも土台6ファイルを書けないか（完成の条件 #9・E-11）
#   ★あわせて「戦略の .py は開けたまま」も測る（開けていなければ、行き過ぎ）。
source "$(dirname "$0")/lib.sh"

H="$ROOT/.claude/hooks/require_acceptance_before_impl.sh"
F="$SDK/.claude/ratchet/spec_lists.json"

IN_BASE='{"agent_type":"general-purpose","tool_input":{"file_path":"'"$F"'","content":"x"}}'
printf '%s' "$IN_BASE" | bash "$H" >/dev/null 2>&1
RC_BASE=$?

IN_PY='{"agent_type":"general-purpose","tool_input":{"file_path":"'"$PR"'/e36_short_oscillation.py","content":"x"}}'
printf '%s' "$IN_PY" | bash "$H" >/dev/null 2>&1
RC_PY=$?

# ★2026-09-04（監査 cp18 の J-3・まこさん決定 9・11・承認 926459e54ff9eba9）
#   ＝後半の期待値を 0 から 2 へ変えた。前半（土台のファイル）は1文字も変えていない。
#   なぜ変えたか＝監査 cp16 の E-11 は「戦略の .py は開けたまま」と決めたが、
#     監査 cp18 の J-3 が「scripts/priority_rebuild/*.py にも広げる」と求めた。
#     ＝2つの監査の決定が食い違い、新しい cp18 を採った（設計書 §3.3・§3.5・§9.1b）。
#   ★これは「テストを通すために期待値を変える」形に見える。
#     そう見えないように、覆したことを設計書に明記し、
#     監査の作業に支障が出ないかを監査に確かめてもらう欄を作った（完成の条件 24番）。
# 土台は止まる（2）／戦略の .py も止まる（2）＝両方 満たしたときだけ「効いた」
if [ "$RC_BASE" -eq 2 ] && [ "$RC_PY" -eq 2 ]; then MEASURED=1; else MEASURED=0; fi
finish
