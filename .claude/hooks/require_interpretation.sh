#!/bin/bash
# require_interpretation.sh — PreToolUse on Write|Edit|MultiEdit|Bash（2026-07-26 まこさん指示・新設・safety hook）
#
# 目的: まこさんの指示に対する「私の解釈」を、手を動かす前に必ずチャットへ出させる。
#   CC は指示に無い空白を自分の解釈で埋め、埋めたことを言わずに実装する癖がある
#   （2026-07-26 の2件＝①「宣言を強制しろ」を誰が何のために見るか聞かずにファイル検査で実装
#     ②「observe_diag の結果を自動分析したい」を engine_search に判定節を足す案にすり替え）。
#   まこさん「勝手な予測で補完して、私の意図しないことをする」「ここで改善したい」。
#
# 強制: .claude/state/interpretation.md に3行の型が書かれ、その内容ハッシュが
#   .claude/state/interpretation_posted と一致していなければブロック（exit 2）。
#   ブロック時は宣言の全文をこの場に出す＝まこさんの画面に必ず出る。
#   マーカーは reset_interpretation.sh（UserPromptSubmit）が まこさんの発言のたびに消す
#   ＝新しい指示のあと、最初に手を動かす前に必ずやり直しになる。
#
# 宣言の型（4行・チャットと interpretation.md の両方・長い型は形骸化するので増やさない）:
#   【解釈】
#   指示: <まこさんの言葉をそのまま>
#   埋めた空白: <指示に無くて私が決めたこと。無ければ「なし」>
#   確認したいこと: <無ければ「なし」>
#   開いて読むファイル: <指示に出てくるファイル・文書。無ければ「なし」>
# ↑4行目は 2026-07-30 まこさん承認「1は強制化してほしい」＝指定された文書を読まずに返答した事案
#   （2026-07-29 監査FB対応で指定5本が未読のまま返答）の再発防止。列挙したファイルが read_log に
#   無ければブロック＝宣言だけでなく Read の実績で照合する。
#   限界: basename の部分一致＝同名の別ファイルはすり抜ける／「なし」と嘘を書けば機械では見抜けない。
#
# 対象: Write / Edit / MultiEdit ／ Bash は実行系スクリプトの python 実行のみ。
# 対象外（通す）: 読む・調べる系の Bash（grep/ls/cat/find/git 等）／--selftest・py_compile・--help・--verify／
#   宣言ファイル自身とマーカーの操作（デッドロック回避）／サブエージェント。
# safety hook: fast-mode 無効化行を入れない（勝手な補完は fast-mode 中にこそ起きた）。
# 解除: INTERP_OK=1（まこさんの明示 OK 時のみ・乱用禁止）。
# 限界: 「埋めた空白: なし」と嘘を書けば機械では見抜けない。埋めたことに CC 自身が気づいていない
#   場合も同じ。最後の関所はまこさんの目（ただし何を勝手に決めたかが手を動かす前に3行で出る）。

INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0   # サブエージェントは通す（デッドロック回避）

printf '%s' "$INPUT" | grep -qE 'INTERP_OK=1' && exit 0

TOOL=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)
FPATH=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)

DECL="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/interpretation.md"
MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/interpretation_posted"

# 宣言ファイル自身とマーカーの書き込みは通す（これを止めると宣言が書けない＝デッドロック）
case "$FPATH" in
  "$DECL"|"$MARK") exit 0 ;;
esac

case "$TOOL" in
  Write|Edit|MultiEdit)
    ;;
  Bash)
    # 引用符・ヒアドキュメントの中身を除去（文章での言及で誤発火させない・他 hook と同型）
    CMD_X=$(printf '%s' "$CMD" | python3 -c "
import sys, re
s = sys.stdin.read()
s = re.sub(r'<<\s*[\"\x27]?(\w+)[\"\x27]?.*?^\1', ' ', s, flags=re.S | re.M)
s = re.sub(r'\"[^\"]*\"', ' ', s); s = re.sub(r\"'[^']*'\", ' ', s)
print(s)" 2>/dev/null)
    [ -z "$CMD_X" ] && CMD_X="$CMD"
    # 宣言ファイル・マーカーを扱うコマンドは通す（デッドロック回避）
    printf '%s' "$CMD" | grep -qE 'interpretation(\.md|_posted)' && exit 0
    # python 実行でなければ通す（読む・調べる系は止めない＝指示を理解するために先に調べられる）
    printf '%s' "$CMD_X" | grep -qE 'python[0-9.]*[[:space:]]' || exit 0
    # 検査だけの実行は通す
    printf '%s' "$CMD_X" | grep -qE -- '--selftest|py_compile|--help|--verify' && exit 0
    # 実行系スクリプトでなければ通す
    printf '%s' "$CMD_X" | grep -qE '(e38_priority_stack|engine_tuner|engine_search_e37|observe_diag|slot_opportunity_diag|e37_scalp|e3[56]_[a-z_]+|score|precheck|report|analyze|plot_trades|gen_[a-z_]+)\.py' || exit 0
    ;;
  *)
    exit 0 ;;
esac

fail() {
  echo "🔒 [解釈ゲート・safety hook] 手を動かす前に、まこさんの指示をどう解釈したかをチャットに貼ってください。" >&2
  echo "   まこさん指示 2026-07-26「不足する要素がある場合は質問をし返すようにして、勝手な解釈で進めないように強制する」。" >&2
  echo "" >&2
  echo "不足: $1" >&2
  echo "" >&2
  if [ -f "$DECL" ]; then
    echo "───────── いまの解釈宣言（この全文をそのままチャットに貼る）─────────" >&2
    cat "$DECL" >&2
    echo "──────────────────────────────────────────────────" >&2
    echo "" >&2
  fi
  echo "対処: ①下の3行の型で $DECL を書く ②同じ内容をチャットに貼る ③下のコマンドでマーカーを作る ④再実行する" >&2
  echo "  【解釈】" >&2
  echo "  指示: <まこさんの言葉をそのまま>" >&2
  echo "  埋めた空白: <指示に無くて自分で決めたこと。無ければ「なし」>" >&2
  echo "  確認したいこと: <無ければ「なし」>" >&2
  echo "  開いて読むファイル: <指示に出てくるファイル・文書。無ければ「なし」>" >&2
  echo "" >&2
  echo "  shasum -a 256 \"$DECL\" | awk '{print \$1}' > \"$MARK\"" >&2
  echo "（まこさんが次に発言するとマーカーは消える＝指示のたびに解釈をやり直す・INTERP_OK=1 はまこさん明示 OK 時のみ）" >&2
  exit 2
}

[ -f "$DECL" ] || fail "解釈宣言のファイルが無い（$DECL）"
grep -q "【解釈】" "$DECL" || fail "「【解釈】」の行が無い"
grep -q "^指示:" "$DECL" || fail "「指示:」の行が無い（まこさんの言葉をそのまま書く）"
grep -q "^埋めた空白:" "$DECL" || fail "「埋めた空白:」の行が無い（無ければ「なし」と書く）"
grep -q "^確認したいこと:" "$DECL" || fail "「確認したいこと:」の行が無い（無ければ「なし」と書く）"
grep -q "^開いて読むファイル:" "$DECL" || fail "「開いて読むファイル:」の行が無い（指示に出てくるファイル・文書を列挙。無ければ「なし」と書く・2026-07-30 まこさん承認）"

# 列挙したファイルを Read tool で実際に開いたかを read_log で照合（2026-07-30 まこさん承認「1は強制化してほしい」
# ＝指定文書を読まずに返答した 2026-07-29 事案の再発防止）
RLOG="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/read_log.txt"
FLINE=$(grep -m1 "^開いて読むファイル:" "$DECL")
if ! printf '%s' "$FLINE" | grep -qE '^開いて読むファイル:[[:space:]]*なし'; then
  for f in $(printf '%s' "$FLINE" | grep -oE '[A-Za-z0-9_./-]+\.(md|py|json|csv|txt|sh)'); do
    b=$(basename "$f")
    grep -qF "$b" "$RLOG" 2>/dev/null || fail "宣言に挙げたファイルをまだ Read tool で開いていない: $f（読んでから作業する・2026-07-30 まこさん承認）"
  done
fi

DHASH=$(shasum -a 256 "$DECL" 2>/dev/null | awk '{print $1}')
POSTED=$(cat "$MARK" 2>/dev/null)
[ -n "$DHASH" ] && [ "$POSTED" = "$DHASH" ] || fail "解釈宣言をチャットに貼った確認マーカーが無い、または宣言を書き換えた後で貼り直していない"

exit 0
