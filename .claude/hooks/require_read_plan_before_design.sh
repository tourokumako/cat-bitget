#!/bin/bash
# require_read_plan_before_design.sh — 読むもの宣言ゲート（入口）
# まこさん指示 2026-09-09「設計書書く前に読むものを私に宣言するというフローを入れろ」。
# 何をするか＝設計書（.claude/state/acceptance.md・*_design.md）を Write/Edit する瞬間に、
#   読むもの宣言（.claude/state/design_read_plan.md）が在り、まこさんの OK の逐語が在り、
#   チャットに貼った印が一致し、宣言した読むものを全部 Read tool で開いているかを見る。
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
fi
if [ -n "$out" ]; then
  echo "$out"
fi
exit $rc
