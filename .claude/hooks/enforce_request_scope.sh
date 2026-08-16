#!/bin/bash
# enforce_request_scope.sh — PreToolUse on Bash（2026-07-20 まこさん指示・fast-mode 限定）
# 目的: 「CC が私の依頼した内容を対応するようにしてほしい」＝依頼の空白（値の水準・対象）を
#   CC が勝手に埋めて別の実験を走らせるのを物理で止める。
# 事案: 依頼「切り方を％にしろ／エントリー価格からの％」に対し、CC が水準 1.5% を無断で決めて本走
#   （slpct15_155・月−$41.30）。しかも 1.5% の根拠はショートの実績値をロングへ流用したもので測定していなかった。
# 判定は enforce_request_scope.py（別ファイル＝pdca_mark の -c 埋め込み無言死の教訓）:
#   exit 3 = current_request.md が無い / exit 4 = 依頼に無い数値を戦略フラグに渡している
# ★正直な限界: current_request.md は CC が書く＝捏造しうる。捏造はまこさんが読めば分かる（逐語記録）。
#   機械が保証するのは「依頼に無い値では走れない」まで。
MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode"
[ ! -f "$MARK" ] && exit 0   # fast-mode 限定（OFF では require_acceptance_before_impl 等が担当）

INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0   # サブエージェントは通す（デッドロック回避・他 hook と同型）

# ★解除（合言葉）は 2026-08-16 に廃止＝まこさん指示「じゃあ強制解除できない状態にしろ」。通す道は無い。

CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)

# 発火対象＝戦略の python 実行（出力モード）。判定器/自己テスト/コンパイルは対象外。
printf '%s' "$CMD" | grep -qE 'python[0-9.]*[[:space:]]' || exit 0
printf '%s' "$CMD" | grep -qE 'e[0-9][0-9]_[a-z_]*\.py' || exit 0
printf '%s' "$CMD" | grep -qE '(--smoke|--selftest|-selftest|py_compile|--help|--no-score)' && exit 0

STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
HOOKS="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks"
REQ="$STATE/current_request.md"

ERR=$(python3 "$HOOKS/enforce_request_scope.py" "$REQ" "$CMD" 2>&1 >/dev/null)
rc=$?
[ "$rc" -eq 0 ] && exit 0

echo "🔒 [依頼スコープゲート・fast-mode] まこさんの依頼に無い内容で実験を走らせようとしています。" >&2
echo "" >&2
if [ "$rc" -eq 3 ]; then
  echo "未達: $STATE/current_request.md がありません（依頼を書き取っていない）。" >&2
  echo "対処: まこさんの依頼を【逐語で】current_request.md に写してから実行する。要約・言い換えをしない。" >&2
  echo "      書く内容＝①まこさんの発言そのまま ②その依頼で決まっている値・対象・範囲 ③決まっていない空白（＝まこさんに聞く項目）" >&2
else
  echo "未達: $ERR" >&2
  echo "対処: この数値はまこさんの依頼に出てきません。**値の水準・対象・範囲はまこさんが決める領域**です。" >&2
  echo "      CC が空白を埋めて走らせない＝チャットで値を確認し、current_request.md に追記してから実行する。" >&2
fi
echo "" >&2
echo "背景（2026-07-20）: 依頼「切り方を％にしろ」に対し CC が水準 1.5% を無断で決めて本走（月−$41.30）。" >&2
echo "  さらにその 1.5% はショート側の実績値をロングへ流用したもので、ロング側は測定していなかった。" >&2
echo "  ＝値を勝手に決めた時点で、実験そのものが依頼と別物になる。" >&2
echo "（解除は 2026-08-16 に廃止＝合言葉では通りません）" >&2
exit 2
