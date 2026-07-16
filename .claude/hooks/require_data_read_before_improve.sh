#!/bin/bash
# require_data_read_before_improve.sh — PreToolUse on Write|Edit（2026-07-16 まこさん指示・fast-mode 専用ガード）
# 目的: fast-mode で改善案を出す(=戦略実装 e37_range_scalp.py を編集する)瞬間、
#   「CSVデータ(trades_*.csv)と実装(e37_range_scalp.py)を必読」を物理強制＝推測で実装するのを防ぐ
#   （memory feedback_fastmode_read_history_code_data＝実装を読まず推測して二度外し激怒された事案の再発防止）。
# 判別: fast-mode ON かつ 編集対象が e37_range_scalp.py の時だけ発火。
#   このセッションで trades_*.csv と e37 を読んだ証跡（track_fastmode_data_read のマーカー or read_log の Read）が
#   両方無ければブロック。マーカーは reset_read_log が SessionStart でクリア（前セッション持ち越さない）。
#   ML に戻る(fast-mode OFF)時は黙る。明示解除 DATAREAD_OK=1。
MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode"
[ ! -f "$MARK" ] && exit 0   # fast-mode 限定（OFF では普段の require_instrument_read_before_impl 等に任せる）

STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
LOG="$STATE/read_log.txt"
INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

FP=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)
# 戦略実装 e37 の編集の時だけ発火（worklog/docs 等の編集は対象外）
printf '%s' "$FP" | grep -qE 'e37_range_scalp\.py$' || exit 0

printf '%s' "$INPUT" | grep -qE 'DATAREAD_OK=1' && exit 0   # 明示オーバーライド

# データ(trades CSV) を読んだ証跡: マーカー or read_log
trades_ok=0
[ -f "$STATE/fastmode_trades_seen" ] && trades_ok=1
grep -qE 'trades_[A-Za-z0-9_]*\.csv' "$LOG" 2>/dev/null && trades_ok=1
# 実装(e37) を読んだ証跡: マーカー or read_log
e37_ok=0
[ -f "$STATE/fastmode_e37_seen" ] && e37_ok=1
grep -qE 'e37_range_scalp\.py' "$LOG" 2>/dev/null && e37_ok=1
# ledger 該当 ARC（過去にやったこと）を読んだ証跡: マーカー or read_log（2026-07-16 まこさん承認・退行の物理防止）
#   ＝タッチ3回(ARC24→v11でタッチ2回に差替済)を確認せず退行させた事案（next_step 失敗(c)）の再発防止。
ledger_ok=0
[ -f "$STATE/fastmode_ledger_seen" ] && ledger_ok=1
grep -qE 'ledger\.md' "$LOG" 2>/dev/null && ledger_ok=1

[ "$trades_ok" -eq 1 ] && [ "$e37_ok" -eq 1 ] && [ "$ledger_ok" -eq 1 ] && exit 0   # 3つとも読んでいれば通す

echo "🔒 [改善前データ必読ゲート・fast-mode] 戦略実装(e37_range_scalp.py)を編集する前に、CSVデータ・実装・ledger の ARC 履歴を読んでください。" >&2
echo "" >&2
[ "$trades_ok" -eq 0 ] && echo "  ❌ trades_*.csv（実データ）を今セッションで読んだ証跡なし（python/pandas で開く or Read tool）" >&2
[ "$e37_ok" -eq 0 ] && echo "  ❌ e37_range_scalp.py（実装）を今セッションで読んだ証跡なし（sed/grep/cat or Read tool）" >&2
[ "$ledger_ok" -eq 0 ] && echo "  ❌ ledger.md（e37 の ARC 履歴＝過去にやったこと）を今セッションで読んだ証跡なし（grep/sed で該当 ARC 群 or Read tool）" >&2
echo "" >&2
echo "理由: ①実装・データを読まず推測して二度外し激怒（memory feedback_fastmode_read_history_code_data）②過去にやったこと(ARC)を確認せず退行（next_step 失敗(c)＝タッチ3回は ARC24 でやって v11 でタッチ2回に差替済なのに戻そうとした）。" >&2
echo "対処: 該当 trades CSV・e37・ledger の該当 ARC 群 を実際に開いてから編集を再実行。ML 復帰時など正当な時は DATAREAD_OK=1。" >&2
exit 2
