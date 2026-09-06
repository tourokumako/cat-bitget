#!/bin/bash
# b32 — 承認の印を消すと、監査に出す前のチェックが止まるか（完成の条件 #1）
#   守っているもの＝「まこさんが --approve を打ったか」を、印のファイルで確かめること。
#   直す前は、打っても打たなくても「承認が済んでいない」を返していた（2026-09-06 に実測）。
source "$(dirname "$0")/lib.sh"

T="$SDK/.claude/ratchet/signal_families_approved.txt"
guard "$T"

# 壊す＝承認の印を消す
rm -f "$T"

measure python3 "$ROOT/.claude/tools/pre_audit_check.py" --verify
finish
