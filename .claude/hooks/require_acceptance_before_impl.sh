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

# 4) TARGET 一致（リストの対象と編集対象が同じか）
TARGET=$(grep -E '^TARGET:' "$LIST" | head -1 | sed 's/^TARGET:[[:space:]]*//')
if [ -z "$TARGET" ]; then
  echo "🔒 [受け入れ条件ゲート] $LIST に『TARGET: <対象.py>』がありません。" >&2
  echo "$GUIDE" >&2
  exit 2
fi
case "$FILE" in
  *"$TARGET") ;;
  *) echo "🔒 [受け入れ条件ゲート] 編集対象($FILE)がリストの TARGET($TARGET)と一致しません。" >&2
     echo "$GUIDE" >&2
     exit 2 ;;
esac

# 5) 承認(内容指紋一致)確認
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
