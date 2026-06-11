#!/bin/bash
# Stop: PDCA 未閉じならターン終了をブロック（analysis_playbook §4 物理強制・2026-06-05 まこさん矯正指示）
# score.py 採点後に report.py 分析 と ledger.md 記録 が無ければ exit 2 で終了を拒否し、
# CC に未済項目を返す（report.py 実行 / ledger.md 編集で旗が下りれば次の Stop で通過）。
STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
MISS=""
[ -f "$STATE/pdca_need_report" ] && MISS="${MISS}・report.py 分析(結果一覧 A〜L)が未実行\n"
[ -f "$STATE/pdca_need_analyze" ] && MISS="${MISS}・analyze.py 深掘り(N1時間構造/N2交差/N3系列/N4ドリフト/N5bootstrap/N6個別読み)が未実行\n"
[ -f "$STATE/pdca_need_ledger" ] && MISS="${MISS}・ledger.md への記録(結果+原因3分類+改善)が未実行\n"
if [ -n "$MISS" ]; then
  printf "⛔ PDCA未閉じ(analysis_playbook §4)。score.py 採点後は必ず以下を実行してから終了せよ:\n%b結果表示・原因分析ログ・経過ログは絶対に飛ばさない(まこさん矯正指示 2026-06-05)。\n" "$MISS" >&2
  exit 2
fi
exit 0
