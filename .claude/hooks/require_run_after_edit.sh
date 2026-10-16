#!/bin/bash
# require_run_after_edit.sh — Stop（2026-10-15・182回目。元＝require_confirm_before_act.sh の stop の口）
#
# 中身は require_run_after_edit.py（hook の python は別ファイル化の規約）。
# 役割＝直したプログラムが走るかの見張り。CC が直した .py・.sh を、直した後に走らせて成功させるまで、返信を終えさせない。

exec python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/require_run_after_edit.py" "$@"
