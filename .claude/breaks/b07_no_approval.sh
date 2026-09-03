#!/bin/bash
# b07 — 承認の印を消すと、.py の書き込みが止まるか（完成の条件 #6）
source "$(dirname "$0")/lib.sh"

AP="$ROOT/.claude/state/acceptance.approved"
guard "$AP"
rm -f "$AP"

IN='{"tool_input":{"file_path":"'"$PR"'/verify_design_contract.py","content":"x"}}'
measure_hook "$ROOT/.claude/hooks/require_acceptance_before_impl.sh" "$IN"
finish
