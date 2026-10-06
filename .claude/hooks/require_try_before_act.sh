#!/bin/bash
# require_try_before_act.sh — 書く・走らせる前に、試しの道具（try_hooks.py）で hook 全部に先に試した記録を求める
#   （まこさん決定 2026-10-06「じゃあ入れる」「OK」・恒久75番）。本体＝require_try_before_act.py
input=$(cat)
printf '%s' "$input" | python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/require_try_before_act.py"
exit $?
