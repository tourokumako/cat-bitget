#!/bin/bash
# reset_read_log.sh — SessionStart
# 新セッション開始時に read_log をリセット（前セッションの読了を引き継がない）。
# ★2026-10-15＝必読を止める hook（require_read_before_work.sh）は 2026-10-01 から登録が無い＝読み直すまで止めることはしていない。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
mkdir -p "$STATE_DIR"
: > "$STATE_DIR/read_log.txt"
# ★2026-10-15（hook の見直しの4本目・まこさん「要る 不具合はすべて修正する」）＝使う hook の無い印の片づけを外した
#   （show_budget_before_design・require_banned_words_check・require_analysis_before_proposal・require_probe_naming・
#     track_fastmode_data_read・require_comprehension_check は登録が無い）。残すのは、稼働中の hook が読む印だけ。
rm -f "$STATE_DIR/worklog_ok" "$STATE_DIR/fastmode_record_pending"  # fast-mode の記録の検査（enforce_worklog_on_experiment）の印を新セッションでリセット（2026-07-16）
rm -f "$STATE_DIR/flow_declaration_posted"  # フロー宣言の「チャットに貼った」確認マーカーを新セッションでリセット＝新しいセッションでも実行前に必ずまこさんの目に入る（enforce_flow_declaration.sh・2026-07-26 まこさん指示）
# ★2026-09-06（まこさん承認・iter="todo-gate-per-session-20260906"）＝ToDo ゲートの状態ファイル3つは、
#   セッションごとの置き場（$STATE_DIR/sessions/<セッションの id>/）に在る（enforce_todo_declaration.py の paths_of）。
#   消すのは「自分のセッション」の印（session_todo_posted）と表示の記録（session_todo_shown）だけ。
#   直す前＝固定の置き場（$STATE_DIR/session_todo_posted・session_todo_shown）を消していた
#     ＝新しいセッションを開くと、動いている別のセッションの印が消え、そのセッションが次の操作で止まった
#     （85回目・並走・worklog 20260904 §37（3）・§39）。
#   id は stdin の json（session_id、無ければ transcript_path のファイル名）から読む＝hook 本体と同じ順。
#   （元の狙いは変えない＝前のセッションの ToDo を持ち越したまま作業できない・2026-08-16 まこさん承認「件２はOK」／
#     印だけ作り直してすり抜ける道を塞ぐ・2026-08-16 まこさん指示「todoフローナシで進めることは禁止にする」）
INPUT=$(cat 2>/dev/null)
SID=$(python3 - "$INPUT" <<'PYEOF'
import json, os, re, sys
raw = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    d = json.loads(raw or "{}")
except Exception:
    d = {}
if not isinstance(d, dict):
    d = {}
sid = d.get("session_id")
if not (isinstance(sid, str) and sid.strip()):
    tp = d.get("transcript_path")
    base = os.path.basename(tp.strip()) if isinstance(tp, str) and tp.strip() else ""
    sid = base[:-6] if base.endswith(".jsonl") else base
sid = re.sub(r"[^A-Za-z0-9._-]", "_", (sid or "").strip()).lstrip(".")
if not sid or set(sid) <= set("._"):
    sid = ""
print(sid)
PYEOF
)
if [ -n "$SID" ]; then
  SESS_DIR="$STATE_DIR/sessions/$SID"
  mkdir -p "$SESS_DIR"
  # ★2026-10-12（172回目）＝表示を実物に合わせた。前の ToDo の hook（enforce_todo_declaration）は 2026-10-01 から登録が無い。
  #   いま ToDo を読むのは、宣言の hook（require_work_declaration）＝「★いまここ」の1件の宣言と、まこさんの返事を求める。
  echo "=== [ToDo] このセッションの ToDo の置き場＝$SESS_DIR/session_todo.md（必読を読んだ後に書く。いまやる1件に ★いまここ を付け、その番号の宣言〔【宣言】ToDo の N番・【作業内容】【目的】【経緯】【ゴール】〕を返信に書く。まこさんの返事の後に、作業を始める）==="
else
  echo "⚠️ [ToDo] セッションの id が読めない（stdin の json に session_id も transcript_path も無い）＝ToDo の置き場を決められない。まこさんに報告する。"
fi

# ★2026-10-12（172回目・まこさん「OK」）＝表示を実物に合わせた。直す前は「読了強制ゲート 有効」「開くまで block されます」と出していたが、
#   止める hook（require_read_before_work.sh）は 2026-10-01 から settings.json に登録が無い（コミット e31d6e8）＝開かなくても止まらなかった。
#   いま作業の前に止めるのは、宣言の hook（require_work_declaration.sh）＝ToDo の1件を始める前に、宣言と まこさんの返事が
#   そろうまで、書き込みと実行を止める。
echo "=== [必読] 作業の前に、次を Read tool で開く ==="
echo "★開かなくても、ここでは止まりません（必読を止める hook は 2026-10-01 から登録が無い）。読んだ後に ToDo を書き、いまやる1件の宣言を返信に書く。宣言と まこさんの返事がそろうまで、hook require_work_declaration が、書き込みと実行を止めます:"
echo "  1. next_step.md（★唯一の起点＝毎回読む文書。あとで直すことの一覧・要件定義の全文・指標の修正の束は、控えのファイル next_step_reference.md に在る＝要るときに開く）"
echo "  2. adopted_strategies.md（採用ポートフォリオ台帳）"
echo "  3. permanent_rules.md（恒久の決まり・リポジトリ直下 .claude/rules/・自動で読み込まれるが Read も要る）"
# ★2026-10-04 まこさん指示（「新セッションでお前が大量のトークンつかって作った資料をCCが面倒だから確認しないんだけど」）
#   ＝「いま必ず読むもの」の一覧（.claude/state/must_read_now.txt）も出す。require_read_before_work.sh が同じ一覧で止める。
#   ★2026-10-12＝その hook（require_read_before_work.sh）は、2026-10-01 から settings.json に登録が無い＝止めていない。ここは表示だけ。
_MR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/must_read_now.txt"
if [ -f "$_MR" ]; then
  _i=4
  while IFS= read -r _l; do
    case "$_l" in ""|\#*) continue ;; esac
    echo "  ${_i}. ${_l}（★いま必ず読むもの＝must_read_now.txt・中身を使って進める）"
    _i=$((_i + 1))
  done < "$_MR"
fi
echo "（WORKFLOW.md＝現在地は「next_step.md §0 を見る」の1行だけ。改訂の履歴は archive/workflow/ に移した）"
echo "→ Read tool で開いてください（grep や表示だけでは、読んだことになりません）。"
echo "（ledger.md 本体＝特定の過去実験を深掘りする時に読む参照資料。毎回の必読からは外した）"
echo "（補助＝必要時のみ: 設計=strat_v9ml_design / 分析手順=analysis_playbook / 教訓=lessons_active を grep 参照）"
echo ""
exit 0
