#!/bin/bash
# require_acceptance_before_impl.sh — PreToolUse on Write|Edit
# 戦略実装(scripts/priority_rebuild/*.py)を編集する前に、受け入れ条件リスト(acceptance.md)が在り・
# 対象が一致し・まこさんが承認済(内容指紋一致)であることを確認。無ければ exit 2 でブロック。
#
# 目的（まこさん命令 2026-06-15）:
#   会話の指示も含め「指示→受け入れ条件リスト→合意→実装→照合」を物理強制する。
#   リスト＋まこさんの承認が無いと実装に入れない＝CC が指示を勝手に解釈して別物を作る/部品を抜くを止める。
#
# 正直な限界: 承認は approve_impl.sh の実行で立つ。CC がそれを勝手に実行すれば通せる（完全物理化は
#   まこさんの承認操作が要る）。運用＝承認コマンドはまこさんが打つ。実行はログに残る。中身の骨抜きは
#   score.py の数字＋独立レビューで見る。

STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
LIST="$STATE/acceptance.md"
APPROVED="$STATE/acceptance.approved"

INPUT=$(cat)

# 1) サブエージェント(Workflow/Agent 内)は通す（デッドロック回避・require_workflow_for_impl と同型）
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

# 2) 編集対象を取得。戦略実装(scripts/priority_rebuild/*.py)だけ対象（hook/設計書/state は対象外）
FILE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)
# 表示専用ツールは対象外（2026-06-21 まこさん承認）: report.py / plot_trades.py は read-only の集計表示で
#   net 判定も戦略実装もしない＝戦略設計用 acceptance ゲートは過剰。判定器(score.py/eval_engine・H13改造禁止)・
#   チェック(precheck.py/analyze.py)・戦略ファイルは下の case で従来どおり gate される。
case "$FILE" in
  */report.py|*/plot_trades.py) exit 0 ;;
esac
case "$FILE" in
  *scripts/priority_rebuild/*.py) ;;
  *) exit 0 ;;
esac

GUIDE="流れ: ①CC が $LIST に「TARGET: <対象.py>」と受け入れ条件(やること)を書く ②チャットで提示 ③まこさんが内容OKなら『bash .claude/hooks/approve_impl.sh』を実行 ④実装"

# 3) リスト存在
if [ ! -f "$LIST" ]; then
  echo "🔒 [受け入れ条件ゲート] 実装の前に受け入れ条件リストがありません: $LIST" >&2
  echo "$GUIDE" >&2
  exit 2
fi

# 4) TARGET 一致（複数 TARGET 行 or カンマ区切りを許可・2026-06-22 まこさん承認＝
#    1 acceptance で複数ファイルをまとめて承認できる＝承認の往復を減らす。各 TARGET いずれかに一致すれば通す）
TARGETS=$(grep -E '^TARGET:' "$LIST" | sed 's/^TARGET:[[:space:]]*//' | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v '^$')
if [ -z "$TARGETS" ]; then
  echo "🔒 [受け入れ条件ゲート] $LIST に『TARGET: <対象.py>』がありません。" >&2
  echo "$GUIDE" >&2
  exit 2
fi
MATCH=0
while IFS= read -r tgt; do
  [ -z "$tgt" ] && continue
  case "$FILE" in *"$tgt") MATCH=1; break ;; esac
done <<EOF
$TARGETS
EOF
if [ "$MATCH" -ne 1 ]; then
  echo "🔒 [受け入れ条件ゲート] 編集対象($FILE)がリストの TARGET($(echo "$TARGETS" | tr '\n' ' '))のいずれとも一致しません。" >&2
  echo "$GUIDE" >&2
  exit 2
fi

# 5) 機械照合用の部品リスト(DESIGN_CONTRACT)が在るか（書き忘れ防止＝明文化できる範囲を機械で漏れなく）
if ! grep -q "DESIGN_CONTRACT" "$LIST"; then
  echo "🔒 [受け入れ条件ゲート] $LIST に機械照合用の部品リスト(DESIGN_CONTRACT ブロック)がありません。" >&2
  echo "やること(自然言語)に加え、実装と機械照合できる部品リスト(DESIGN_CONTRACT の json: impl_file / self_check_calls / must_combine)を必ず書いてください。" >&2
  exit 2
fi

# 5.5) 深い分析＋ベースアップの必須化（まこさん命令 2026-06-15「分析と改善のフローが一番重要・深掘りしてから改善案」）
#   難しい問題に最易パッチを当てる前に、損の真因・期待値のどれを動かすか・root か symptom か・参照KB を書かせる。
#   ＝雑な分析のまま改善案を実装するのを物理ブロック。中身の質はまこさん30秒チェックが担保。
MISS_KW=""
for kw in "真因" "期待値" "symptom" "ベースアップ"; do
  grep -q "$kw" "$LIST" || MISS_KW="$MISS_KW $kw"
done
if [ -n "$MISS_KW" ]; then
  echo "🔒 [深い分析ゲート] $LIST に深掘り4点の見出しがありません（不足:$MISS_KW）。改善案の前に必須:" >&2
  echo "   ①真因(root cause・損/不足の構造的原因) ②期待値分解(勝率/平均利益/敗率/平均損失 のどれを動かすか)" >&2
  echo "   ③root を直すか symptom か(Y/N+理由・symptom 患い＝最易パッチを防ぐ) ④ベースアップ(参照した KB/検索の証跡・記憶ベース禁止)" >&2
  exit 2
fi

# 6) 承認(内容指紋一致)確認
if [ ! -f "$APPROVED" ]; then
  echo "🔒 [受け入れ条件ゲート] 未承認です。リストを提示し、まこさんに『bash .claude/hooks/approve_impl.sh』を実行してもらってください。" >&2
  echo "$GUIDE" >&2
  exit 2
fi
CUR=$(shasum -a 256 "$LIST" | awk '{print $1}')
OKD=$(cat "$APPROVED" 2>/dev/null)
if [ "$CUR" != "$OKD" ]; then
  echo "🔒 [受け入れ条件ゲート] リストが承認後に変更されています(内容指紋が不一致)。再承認が必要: bash .claude/hooks/approve_impl.sh" >&2
  exit 2
fi
exit 0
