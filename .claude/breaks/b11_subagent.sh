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

# 土台は止まる（2）／戦略の .py は通る（0）＝両方 満たしたときだけ「効いた」
if [ "$RC_BASE" -eq 2 ] && [ "$RC_PY" -eq 0 ]; then MEASURED=1; else MEASURED=0; fi
finish
