#!/bin/bash
# track_fastmode_data_read.sh — PostToolUse on Bash（2026-07-16 まこさん指示・require_data_read_before_improve と対）
# 目的: fast-mode で改善案(=e37 編集)を出す前に「CSVデータ(trades_*.csv)と実装(e37_range_scalp.py)を読んだか」を
#   物理判定するための材料マーカーを立てる。CC はコードを Bash(sed/grep/cat/python)、データを python(pandas)で読むので
#   Read tool の read_log だけでは捉えられない → Bash コマンドの中身から実データ/実装への access を検知してマーカー touch。
#   マーカーは reset_read_log.sh が SessionStart でクリア（前セッションの読了を持ち越さない）。
STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)
# ★worklog への記録コマンドは「実データ/実装/分析の実行」でなく「記録行為」＝除外（2026-07-20 まこさん指示）。
#   背景: cat >> session_worklog <<EOF …本文に score.py/trades_*.csv/e37_range_scalp.py の語… EOF の
#   heredoc 本文の"言及"を実行と誤検知し、fastmode_record_pending が worklog 書込みの直後に立ち直して
#   enforce_worklog_on_experiment（Stop）が永久に exit 7 になった（worklog を書くほどブロックが続く自己矛盾）。
#   記録コマンド（session_worklog を含む Bash）は下の materialマーカーを立てない＝本文の語で誤発火しない。
printf '%s' "$CMD" | grep -qE 'session_worklog' && exit 0
# ★検知に使う形へ整える（2026-08-07 まこさん指示「21は今やれば？」・next_step §6.5 の21番）。
#   ヒアドキュメント（<<EOF … EOF）の中身と引用符の中身を空白に置き換える＝走らせていないのに
#   名前が出てくる場面（git commit のメッセージ本文・echo の中）で誤発火しない。
#   背景＝2026-08-07 に commit メッセージ本文の score.py を「分析を回した」と誤検知してターンが止まった（この日 2回）。
#   上の15行（session_worklog を除外）は同じ型のその場しのぎ（2026-07-20）。原因は同じなのでここで1本にした。
#   実装は .claude/hooks/hook_cmd.py（番人＝既知答え7件・--selftest）。失敗したら元の CMD のまま使う（fail-open）。
CMD_X=$(printf '%s' "$CMD" | python3 "$(dirname "$0")/hook_cmd.py" 2>/dev/null) || CMD_X="$CMD"
# trades_*.csv に触れた（pandas read_csv / probe / report / analyze 等）＝データを読んだ
printf '%s' "$CMD_X" | grep -qE 'trades_[A-Za-z0-9_]*\.csv' && touch "$STATE/fastmode_trades_seen"
# e37_range_scalp.py に触れた（sed/grep/cat/python いずれでも）＝実装を読んだ
printf '%s' "$CMD_X" | grep -qE 'e37_range_scalp\.py' && touch "$STATE/fastmode_e37_seen"
# ledger.md に触れた（grep/sed/cat/less いずれでも）＝ARC 履歴（過去にやったこと）を読んだ
#   → require_data_read_before_improve の3つ目のゲート（改善前 ledger 読了）が参照（退行の物理防止・2026-07-16 まこさん承認）
printf '%s' "$CMD_X" | grep -qE 'ledger\.md' && touch "$STATE/fastmode_ledger_seen"
# 分析/採点（report/analyze/score/probe/deep_analysis）を「python で走らせた」＝結論を worklog に記録すべき
#   （enforce_worklog_on_experiment が Stop で照合）。★名前がコマンドの中に在るだけでは立てない（2026-08-07・§6.5 の21番）。
printf '%s' "$CMD_X" | grep -qE 'python[0-9.]*[ \t]+[^|&;]*(report\.py|analyze\.py|score[A-Za-z0-9_]*\.py|_probe\.py|_deep_analysis\.py)' && touch "$STATE/fastmode_record_pending"
exit 0
