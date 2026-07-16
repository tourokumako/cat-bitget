#!/bin/bash
# enforce_worklog_on_experiment.sh — Stop（2026-07-16 まこさん指示・fast-mode 専用ガード／2026-07-17 まこさん承認で B/C 拡張）
# 目的: fast-mode は改善アーク自動生成(gen_improvement_arc)が使えない→都度ログ(session_worklog)で
#   引き継ぎの「改善内容・経緯」に誤解/ヌケモレが無い状態を保つ。さらに「report/analyze を出さずに結論を言う」
#   「型別（down/flat_up）に分けずに合計値だけで判断する」を物理で止める（experiment_result_procedure.md と対）。
# 判定は enforce_worklog_on_experiment.py（別ファイル＝pdca_mark の -c 埋め込み無言死の教訓）:
#   exit 7 = 実験/分析後に worklog 未更新（従来 A）
#   exit 8 = 最新採点 CSV の report_/analysis_ ファイルが無い（B・2026-07-17）
#   exit 9 = worklog に タグ_番号＋「型別」の分析記録が無い（C・2026-07-17）
# ★正直な限界: 中身の正しさ（分析の質）は機械では保証できない → 手順は experiment_result_procedure.md・中身はまこさんの目。
MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode"
[ ! -f "$MARK" ] && exit 0   # fast-mode 限定（OFF では pdca_gate 等の普段の記録強制に任せる）

STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
[ -f "$STATE/worklog_ok" ] && exit 0   # 明示オーバーライド（正当に記録不要な時・稀）

RATCHET="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/results/priority_rebuild/ratchet"
WLDIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/state"
HOOKS="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks"

python3 "$HOOKS/enforce_worklog_on_experiment.py" "$RATCHET" "$WLDIR" "$STATE" 2>>"$STATE/enforce_worklog_error.log"
rc=$?
[ "$rc" -eq 0 ] && exit 0

if [ "$rc" -eq 8 ]; then
  echo "🔒 [結果後手順ゲート・fast-mode] 最新の採点CSVに対応する report / analysis ファイルがありません＝report.py / analyze.py を出す前に結論を言おうとしています。" >&2
  echo "対処: report.py <score.csv> --vs <前回base> と analyze.py <score.csv> --vs <前回base> を実行してから、型別の分析を worklog に書いてターンを終える（experiment_result_procedure.md の固定手順 2〜3）。" >&2
  exit 2
fi
if [ "$rc" -eq 9 ]; then
  echo "🔒 [結果後手順ゲート・fast-mode] worklog に最新実験（タグ_番号）の記録と「型別」の分析がありません＝合計値だけで判断しようとしています。" >&2
  echo "対処: session_worklog に タグ_番号（例 fix6m_095）を明記し、down / flat_up の型別に分けた結果（C2節・増減した玉の位置とタイミング）を書いてからターンを終える（experiment_result_procedure.md の固定手順 4〜5）。net 合計の悪化だけで「不採用」と言わない。" >&2
  exit 2
fi

echo "🔒 [引き継ぎ記録ゲート・fast-mode] 実験(新 trades_*.csv) または 分析(report/analyze/score/probe) を回したのに session_worklog が未更新です。" >&2
echo "" >&2
echo "fast-mode は改善アーク自動生成が使えない＝都度ログで引き継ぎの「改善内容・経緯（＝なぜそうしたか）」に誤解/ヌケモレを残さない（next_step 運転方式2・cat_requirements §8.5）。実験だけでなく分析の結論・方針判断も記録する（今回たまたま書けただけ＝再現性がないので強制・まこさん 2026-07-16）。" >&2
echo "対処: session_worklog_<日付>.md に追記してからターンを終える。記載＝①何を変えた/何を分析した ②結論（採点窓 score.py の net・学習窓を持ち込まない）③merit/demerit ④次の一手（なぜ）。" >&2
echo "  誤解防止チェック: 采否は採点窓 score.py の数字か／学習窓・precheck・L-320 を持ち込んでいないか／crude の数字を采否に使っていないか／E37 は件数/日≥5(スキャル)か。" >&2
echo "（正当に記録不要な時のみ touch .claude/state/worklog_ok）" >&2
exit 2
