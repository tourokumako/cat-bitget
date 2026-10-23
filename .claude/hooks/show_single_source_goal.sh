#!/bin/bash
# show_single_source_goal.sh — UserPromptSubmit（まこさんが発言を送るたび）に、工事 m2c15-single-source のゴールの逐語を CC の文脈に出す。
# 止めない（出すだけ・終了コードは常に 0）。逐語の正本＝.claude/state/verbatim/m2c15-single-source-fix-20261023/req_goal_20261023.txt（写さない）。
# まこさん（2026-10-23）「あと何回私が目的を打てば覚える？？？」＝CC の記憶に頼らず、毎回 目の前に出す。
GOAL=/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/verbatim/m2c15-single-source-fix-20261023/req_goal_20261023.txt
if [ -f "$GOAL" ]; then
  echo "【指標の工事のゴール（まこさん逐語・req_goal_20261023.txt）】"
  cat "$GOAL"
  echo "→ 案・表・報告を出す前に、中身が ①集める ②元の場所を消す ③読む側を向け直す のどれかを1行で書く。どれにも当たらない作業はしない。完成＝表の外に指標の情報を持つ所が0件（ss_outside_probe.py で数える）。"
fi
exit 0
