#!/bin/bash
# enforce_flow_declaration.sh — PreToolUse on Bash（2026-07-25 まこさん指示・新設・safety hook＝両モードで有効）
#
# 目的: 実行系コマンド（エンジン・探索・観察・採点）を打つ前に、「フローのどの工程をやっているのか」の
#   宣言を物理強制する。CC が工程を宣言せずに実行を重ね、まこさんが「今何をやっているのか」を
#   見失う事態（2026-07-25「毎回意味不明なことをしだすので私が混乱する」）を塞ぐ。
#
# 強制: 対象スクリプトを python 実行する前に、.claude/state/flow_declaration.md に
#   ①「段」の行 ②「工程」の行 ③実行するスクリプト名 が書かれていて、④宣言が24時間以内に
#   更新されていることを要求。満たさなければブロック（exit 2）。同じ工程で同じスクリプトを
#   回し直す間は宣言は1回でよい（工程が変わったら書き直す）。チャットにも同内容を出す（運用）。
#
# 宣言の型（4行・チャットと flow_declaration.md の両方）:
#   【フロー宣言】
#   段: E38 段3 Entry 策定
#   工程: 3️⃣層3 候補選定
#   実行: engine_search_e38.py --logic S2
#   目的: 時間系候補の是正後の再探索
#
# 対象（実行系のみ）: e38_priority_stack / engine_search_e38 / engine_search_e37 / observe_diag /
#   slot_opportunity_diag / e37_scalp / e35_* / e36_* / score.py / precheck.py / report.py / analyze.py / plot_trades
# 対象外（通す）: --selftest・py_compile・--help・読み取り系（grep/ls/cat 等）・引用符/ヒアドキュメント内の言及・
#   サブエージェント（デッドロック回避・他 hook と同型）。
# safety hook: fast-mode 無効化行を入れない（宣言なし実行は fast-mode 中に起きた＝fast-mode でこそ要る）。
# 解除: FLOW_DECL_OK=1（まこさんの明示 OK 時のみ・乱用禁止）。
# 限界: 宣言の中身が工程と一致しているかの意味判定はできない（まこさんの目と併用）。

INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0   # サブエージェントは通す（デッドロック回避）

printf '%s' "$INPUT" | grep -qE 'FLOW_DECL_OK=1' && exit 0

CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)

# 引用符・ヒアドキュメントの中身を除去（文章での言及では誤発火させない・enforce_observe_diag_only と同型）
CMD_X=$(printf '%s' "$CMD" | python3 -c "
import sys, re
s = sys.stdin.read()
s = re.sub(r'<<\s*[\"\x27]?(\w+)[\"\x27]?.*?^\1', ' ', s, flags=re.S | re.M)  # ヒアドキュメント本文を除去
s = re.sub(r'\"[^\"]*\"', ' ', s); s = re.sub(r\"'[^']*'\", ' ', s)             # 引用符の中身を除去
print(s)" 2>/dev/null)
[ -z "$CMD_X" ] && CMD_X="$CMD"

# python 実行の時だけ判定
printf '%s' "$CMD_X" | grep -qE 'python[0-9.]*[[:space:]]' || exit 0

# 検査でない実行は通す（自己検査・コンパイル確認・ヘルプ・改変検出）
printf '%s' "$CMD_X" | grep -qE -- '--selftest|py_compile|--help|--verify' && exit 0

# 実行系スクリプトの抽出（読み取り系・文書生成は対象外）
TARGETS=$(printf '%s' "$CMD_X" | grep -oE '(e38_priority_stack|engine_search_e3[78]|observe_diag|slot_opportunity_diag|e37_scalp|e3[56]_[a-z_]+|score|precheck|report|analyze|plot_trades)\.py' | sort -u)
[ -z "$TARGETS" ] && exit 0

DECL="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/flow_declaration.md"

fail() {
  echo "🔒 [フロー宣言ゲート・safety hook] 実行の前にフロー宣言を書いてください（まこさん指示 2026-07-25「毎回なにか実行するまえに、フローのなにをやってるのか宣言するように強制」）。" >&2
  echo "" >&2
  echo "不足: $1" >&2
  echo "対象: $(printf '%s' "$TARGETS" | tr '\n' ' ')" >&2
  echo "" >&2
  echo "対処: .claude/state/flow_declaration.md に次の4行の型で書き、同内容をチャットにも出してから実行する。" >&2
  echo "  【フロー宣言】" >&2
  echo "  段: <e38_flow.md の段（例 E38 段3 Entry 策定）>" >&2
  echo "  工程: <策定4段のどれ（例 3️⃣層3 候補選定）>" >&2
  echo "  実行: <スクリプト名と主な引数>" >&2
  echo "  目的: <1行>" >&2
  echo "（同じ工程で同じスクリプトを回し直す間は宣言1回でよい・工程が変わったら書き直す・FLOW_DECL_OK=1 はまこさん明示 OK 時のみ）" >&2
  exit 2
}

[ -f "$DECL" ] || fail "宣言ファイルが無い（$DECL）"

# 鮮度: 24時間以内の更新（古い宣言の使い回し＝工程が変わっても素通り、を防ぐ下限）
NOW=$(date +%s)
MT=$(stat -f %m "$DECL" 2>/dev/null || stat -c %Y "$DECL" 2>/dev/null)
[ -n "$MT" ] && [ $((NOW - MT)) -gt 86400 ] && fail "宣言が24時間より古い（工程を確認して書き直す）"

grep -q "段" "$DECL" || fail "「段:」の行が無い"
grep -q "工程" "$DECL" || fail "「工程:」の行が無い"

for t in $TARGETS; do
  grep -q "$t" "$DECL" || fail "宣言に $t が書かれていない（このスクリプトの実行を宣言していない）"
done

exit 0
