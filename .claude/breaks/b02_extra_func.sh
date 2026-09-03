#!/bin/bash
# b02 — 凍結に無い関数を実装に足すと、照合が止まるか（完成の条件 #2）
source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/tools/run_breaks.py"
guard "$T"

printf '\n\ndef sneaky_extra_for_break_test():\n    return 1\n' >> "$T"

measure python3 "$VERIFY" --diff "$ROOT/.claude/state/acceptance.md"
finish
