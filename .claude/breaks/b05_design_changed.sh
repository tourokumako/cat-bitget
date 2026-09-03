#!/bin/bash
# b05 — 承認の後に設計書を1文字 変えると、止まるか（完成の条件 #4）
source "$(dirname "$0")/lib.sh"

MD="$ROOT/.claude/state/acceptance.md"
guard "$MD"

printf '\n<!-- break test -->\n' >> "$MD"

measure python3 "$VERIFY" --check-approval "$MD"
finish
