#!/bin/bash
# b06 — 照合の道具を1文字 変えると、止まるか（完成の条件 #5）
source "$(dirname "$0")/lib.sh"

guard "$VERIFY"

printf '\n# break test\n' >> "$VERIFY"

measure python3 "$VERIFY" --diff "$ROOT/.claude/state/acceptance.md"
finish
