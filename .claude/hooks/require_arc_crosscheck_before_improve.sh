#!/bin/bash
# require_arc_crosscheck_before_improve.sh — PreToolUse on Write|Edit（2026-07-16 まこさん承認・fast-mode 専用ガード）
# 目的: fast-mode で改善案(=戦略実装 e37_range_scalp.py を編集する)瞬間、
#   「この改善は過去の ARC○○ でやったか＝Yes/No＋やったなら何が違うか」を worklog に宣言済みでなければブロック。
#   ＝「新設計」と称した退行（過去にやって採用に至らなかった/差し替えた手を、確認せず戻す）を実装の前の一言宣言で止める。
#   背景（next_step 失敗(c)・2026-07-16）＝タッチ3回ゾーンは ARC24(v10) でやって v11(ARC25) でタッチ2回に差替済なのに、
#   CC は確認せず v10 のタッチ3回へ戻そうとした＝完全な退行。過去ログを読めば全部回避できた無駄。
#   Hook 1(require_data_read_before_improve の ledger 読了)は「読んだか」まで、本 hook は「読んで過去照合を宣言したか」まで縛る。
# 判別: fast-mode ON かつ 編集対象が e37_range_scalp.py の時だけ発火。
#   最新 session_worklog_*.md に「過去照合:」を含む行があり、その行が ARC番号(ARC\d+ or ARCなし=none 明記)＋
#   （Yes または No）を含めば通す。無ければブロック。解除は 2026-08-16 に廃止。
MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode"
[ ! -f "$MARK" ] && exit 0   # fast-mode 限定（OFF では enforce_pdca_chain 等の普段の連結強制に任せる）

INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0   # サブエージェントは通す（デッドロック回避・他 hook と同型）

FP=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)
# 戦略実装 e37 の編集の時だけ発火（worklog/docs 等の編集は対象外＝worklog に宣言を書く編集自体はブロックしない）
printf '%s' "$FP" | grep -qE 'e37_range_scalp\.py$' || exit 0

# ★解除（合言葉）は 2026-08-16 に廃止＝まこさん指示「じゃあ強制解除できない状態にしろ」。通す道は無い。

WLDIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/state"
# 最新の session_worklog を探し、過去照合宣言行を照合
newest_wl=$(ls -t "$WLDIR"/session_worklog_*.md 2>/dev/null | head -1)
if [ -n "$newest_wl" ]; then
  # 「過去照合:」を含む行に ARC(番号 or none) と Yes/No が在るか
  if grep -E '過去照合[:：]' "$newest_wl" 2>/dev/null | grep -qE '(ARC[0-9]+|ARCなし|none)' \
     && grep -E '過去照合[:：]' "$newest_wl" 2>/dev/null | grep -qE '(Yes|No|やった|やってない|該当なし)'; then
    exit 0
  fi
fi

echo "🔒 [過去照合宣言ゲート・fast-mode] e37_range_scalp.py を編集する前に、session_worklog に「過去照合」宣言を書いてください（2026-07-16 まこさん承認）。" >&2
echo "" >&2
echo "書く内容（1行でよい）: 「過去照合: この改善(=○○)は過去 ARC○○ でやったか＝Yes/No＋やったなら何が違うか（退行でない理由）」。" >&2
echo "  ・過去にやっていない新規なら「過去照合: ARCなし（or 該当なし）＝No・新規」と明記。" >&2
echo "  ・過去にやったが差分があるなら「過去照合: ARC24 でタッチ3回をやった=Yes・今回は○○が違う(退行でない)」。" >&2
echo "" >&2
echo "理由: 「新設計」と称した退行の再発防止（next_step 失敗(c)＝タッチ3回は ARC24 でやって v11 でタッチ2回に差替済なのに確認せず戻そうとした）。" >&2
echo "対処: 最新 session_worklog_<日付>.md に上記の「過去照合:」行を追記してから編集を再実行。解除は 2026-08-16 に廃止。" >&2
exit 2
