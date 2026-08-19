#!/bin/bash
# require_source_read_before_acceptance.sh — 受け入れ条件を書く瞬間の必読ゲート（入口）
# まこさん指示 2026-08-19「必読hookを作れ」。
#
# 何をするか
#   .claude/state/acceptance.md を Write/Edit する瞬間に、次の3つを read_log と突き合わせる。
#     A 直す対象（TARGET に書いた .py）を Read tool で開いたか
#     B その対象が自動で作る文書（.py の GENERATES の欄）を開いたか
#     C 本文で「読んだ」と書いたファイルを、本当に開いたか
#   1件でも開いていなければ exit 2 でブロックする。
#
# 本体は .py に分ける（hook の python を -c で埋め込まない決まり・pdca_flow §5）。
# 合言葉（XXX_OK=1）は作らない（2026-08-16 に全部 廃止）。

PY="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/require_source_read_before_acceptance.py"
LOGERR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/require_source_read_error.log"

if [ ! -f "$PY" ]; then
  # 本体が無いときは黙って死なない＝画面に出す（無言死の可視化）
  echo "🔒 [必読ゲート] 本体が見つかりません: $PY" >&2
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
