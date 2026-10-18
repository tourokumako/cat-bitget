#!/bin/bash
# require_read_plan_before_design.sh — 読むもの宣言ゲート（入口）
# まこさん指示 2026-09-09「設計書書く前に読むものを私に宣言するというフローを入れろ」。
# 何をするか＝設計書の元（.claude/state/verbatim/<工事名>/やることの表.md）を Write/Edit する瞬間に（2026-10-17 に設計書から移した）、
#   読むもの宣言（.claude/state/design_read_plan.md）が在り、宣言の「設計書:」が工事のフォルダの名前と同じで、まこさんの OK の逐語が在り、
#   チャットに貼った印が一致するかを見る（宣言した読むものを Read tool で開いたかは、2026-10-01 に外した）。
# 本体は .py（hook の python を -c で埋め込まない決まり・pdca_flow §5）。合言葉は無い。
PY="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/require_read_plan_before_design.py"
LOGERR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/require_read_plan_error.log"
if [ ! -f "$PY" ]; then
  echo "🔒 [読むもの宣言ゲート] 本体が見つかりません: $PY" >&2
  exit 2
fi
input=$(cat)
out=$(printf '%s' "$input" | python3 "$PY" 2>"$LOGERR")
rc=$?
if [ -s "$LOGERR" ]; then
  cat "$LOGERR" >&2
  # ★2026-10-18（監査 CP80）＝止めた（2）・通した（0）ときの文は、実行時のエラーではない。残すと、次のセッションの始めに
  #   hook_health_check.sh の③が「実行時エラーあり（fail-open で素通りした可能性）」と誤って出す＝落ちたときだけ残す。
  if [ "$rc" = "0" ] || [ "$rc" = "2" ]; then : > "$LOGERR"; fi
fi
if [ -n "$out" ]; then
  echo "$out"
fi
exit $rc
