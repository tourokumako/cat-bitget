#!/bin/bash
# track_fastmode_data_read.sh — PostToolUse on Bash（2026-07-16 まこさん指示・require_data_read_before_improve と対）
# 目的: fast-mode で改善案(=e37 編集)を出す前に「CSVデータ(trades_*.csv)と実装(e37_range_scalp.py)を読んだか」を
#   物理判定するための材料マーカーを立てる。CC はコードを Bash(sed/grep/cat/python)、データを python(pandas)で読むので
#   Read tool の read_log だけでは捉えられない → Bash コマンドの中身から実データ/実装への access を検知してマーカー touch。
#   マーカーは reset_read_log.sh が SessionStart でクリア（前セッションの読了を持ち越さない）。
STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)
# trades_*.csv に触れた（pandas read_csv / probe / report / analyze 等）＝データを読んだ
printf '%s' "$CMD" | grep -qE 'trades_[A-Za-z0-9_]*\.csv' && touch "$STATE/fastmode_trades_seen"
# e37_range_scalp.py に触れた（sed/grep/cat/python いずれでも）＝実装を読んだ
printf '%s' "$CMD" | grep -qE 'e37_range_scalp\.py' && touch "$STATE/fastmode_e37_seen"
# ledger.md に触れた（grep/sed/cat/less いずれでも）＝ARC 履歴（過去にやったこと）を読んだ
#   → require_data_read_before_improve の3つ目のゲート（改善前 ledger 読了）が参照（退行の物理防止・2026-07-16 まこさん承認）
printf '%s' "$CMD" | grep -qE 'ledger\.md' && touch "$STATE/fastmode_ledger_seen"
# 分析/採点（report/analyze/score/probe/deep_analysis）を走らせた＝結論を worklog に記録すべき（enforce_worklog_on_experiment が Stop で照合）
printf '%s' "$CMD" | grep -qE 'report\.py|analyze\.py|score\.py|_probe\.py|_deep_analysis\.py' && touch "$STATE/fastmode_record_pending"
exit 0
