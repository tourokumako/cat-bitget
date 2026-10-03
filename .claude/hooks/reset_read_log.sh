#!/bin/bash
# reset_read_log.sh — SessionStart
# 新セッション開始時に read_log をリセット（前セッションの読了を引き継がない）。
# これで毎セッション、必読を Read tool で読み直すまで作業ツールが block される。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
mkdir -p "$STATE_DIR"
: > "$STATE_DIR/read_log.txt"
rm -f "$STATE_DIR/budget_rule_shown"   # 予算バナーを新セッションで1回出すため（show_budget_before_design.sh・2026-06-20）
rm -f "$STATE_DIR/banned_words_checked" # 禁止語チェックの事前実行を新セッションで1回強制（require_banned_words_check.sh・2026-07-11 まこさん指示）
rm -f "$STATE_DIR/analysis_block.md"   # 分析ブロックを新セッションでリセット（前セッションの分析を持ち越さない＝require_analysis_before_proposal.sh・2026-06-24）
rm -f "$STATE_DIR/improvement_plan.md" # 改善案生成(STEP1〜5)を新セッションでリセット（probe前ゲートA＋提案ゲートB＝require_probe_naming/require_analysis_before_proposal・2026-06-28）
rm -f "$STATE_DIR/fastmode_trades_seen" "$STATE_DIR/fastmode_e37_seen" "$STATE_DIR/fastmode_ledger_seen" "$STATE_DIR/worklog_ok" "$STATE_DIR/fastmode_record_pending"  # fast-mode ガード(改善前データ必読[trades/e37/ledger ARC]/引き継ぎ記録/分析後記録)のマーカーを新セッションでリセット（2026-07-16）
rm -f "$STATE_DIR/comprehension_check.md"   # 理解確認テストの回答を新セッションでリセット＝毎セッション再回答を強制（require_comprehension_check.sh・2026-07-16 まこさん指示）
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
  rm -f "$SESS_DIR/session_todo_posted" "$SESS_DIR/session_todo_shown"
  echo "=== [ToDo ゲート] このセッションの ToDo の置き場＝$SESS_DIR/session_todo.md（印と表示の記録は消した・ToDo を書いて貼って印を作るまで Bash/Edit/Write は止まる）==="
else
  echo "⚠️ [ToDo ゲート] セッションの id が読めない（stdin の json に session_id も transcript_path も無い）＝ToDo ゲートは最初の操作で止まる（fail-closed）。まこさんに報告する。"
fi
# 目標逆算ゲート（ゲート2）リセット: 前セッションの逆算ブロックは引き継がないが、
# 引き継ぎ前提（本筋・やってはいけないこと）は残す。必須見出しの語は入れないので
# ゲートは維持され、新セッションは前提を見てから自分で目標逆算を Write し直す（2026-06-12 まこさん指示）。
cat > "$STATE_DIR/goal_block.md" <<'EOF'
# 目標逆算（新セッションが本欄を Write し直す）

> ⚠️ 下は前セッションの引き継ぎ前提。新セッションはこれを踏まえ、本欄に目標逆算ブロックを Write し直すこと
> （必須見出しが揃うまで Bash/Edit/Write はブロックされる＝前提を読んでから自分で逆算する）。

## 引き継ぎ前提
- 本筋・今セッションの確定・やってはいけないこと・数字の出典は **next_step.md（SessionStart で全文表示）が正本**。
  そちらを起点に、本欄へ目標逆算ブロック（大目標/器の現在値/ギャップ/候補/天井/選定/3行ゲート/届く構成/戦略照合）を Write し直す。
- ⚠️ ここに前セッション固有の handoff を焼き込まない（hook に焼くと古くなって誤誘導する＝2026-06-13 P4 stale 事案）。最新は常に next_step.md。
EOF

echo "=== [読了強制ゲート 有効] ==="
echo "必読を Read tool で実際に開くまで、Bash/Edit/Write は block されます（読んだふり防止・require_read_before_work と一致）:"
echo "  1. next_step.md（★唯一の起点＝§0 次にやること・§6 あとで直すこと。2026-08-25 まこさん指示で WORKFLOW.md を必読から外した）"
echo "  2. adopted_strategies.md（採用ポートフォリオ台帳）"
echo "  3. permanent_rules.md（恒久の決まり・リポジトリ直下 .claude/rules/・自動で読み込まれるが Read も要る）"
# ★2026-10-04 まこさん指示（「新セッションでお前が大量のトークンつかって作った資料をCCが面倒だから確認しないんだけど」）
#   ＝「いま必ず読むもの」の一覧（.claude/state/must_read_now.txt）も出す。require_read_before_work.sh が同じ一覧で止める。
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
echo "→ grep や表示だけでは解除されません。Read tool で開いてください。"
echo "（ledger.md 本体＝特定の過去実験を深掘りする時に読む参照資料。毎回の必読からは外した）"
echo "★ cat_requirements.md / exchange_spec.md（決済方法）は『設計書を書く瞬間』に強制 read（just-in-time・require_spec_read_before_design.sh）。"
echo "   理由: セッション開始時に読んでもインプットされない実証（まこさん 2026-06-13・add/決済を毎回誤解）。"
echo "（補助＝必要時のみ: 設計=strat_v9ml_design / 分析手順=analysis_playbook / 教訓=lessons_active を grep 参照）"
echo ""
exit 0
