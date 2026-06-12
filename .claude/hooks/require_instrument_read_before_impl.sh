#!/bin/bash
# require_instrument_read_before_impl.sh — PreToolUse on Write|Edit（2026-06-12 まこさん指示で新設）
# 目的: 実験スクリプト（strat_/train_/gen_/measure_/*oracle*/compose_/size_）を書く瞬間に、
#   計器の正本 eval_engine.py を Read tool で読んでいなければ exit 2 で block する。
#   背景: CC が「ラベル sim は eval_engine のみ・自作 net 計算なし」が最新標準（E25）なのに、
#   計器を読まずに実験を設計・提案した事案（2026-06-12）。net 計算の取り違え（rc の net をそのまま
#   教師にする L-268 型の穴）を実装の入口で物理的に防ぐ。
#   方針: 毎セッション必読には足さない（読む量を増やすと効かない実証・必読は3本のまま）。
#   実装に手を出す瞬間だけ計器読了を要求する（最小強制）。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
LOG="$STATE_DIR/read_log.txt"

input=$(cat)

fp=$(printf '%s' "$input" | python3 -c "import sys,json
try:
    d=json.load(sys.stdin)
    print(d.get('tool_input',{}).get('file_path',''))
except Exception:
    print('')" 2>/dev/null)

# 対象は scripts/priority_rebuild/ 配下のみ
case "$fp" in
  */scripts/priority_rebuild/*) ;;
  *) exit 0 ;;
esac

base=$(basename "$fp")

# 除外: 計器・審判・分析ツール・テスト自身（これら自体の編集は対象でない）
case "$base" in
  eval_engine.py|score.py|report.py|precheck.py|analyze.py|preload_cache.py|test_*) exit 0 ;;
esac

# 対象: 実験スクリプト系の命名のみ
is_exp=0
case "$base" in
  strat_*.py|train_*.py|gen_*.py|measure_*.py|compose_*.py|size_*.py) is_exp=1 ;;
  *oracle*.py) is_exp=1 ;;
esac
[ "$is_exp" -eq 0 ] && exit 0

# 計器 eval_engine を Read 済みか（record_read.sh が read_log に記録）
if ! grep -q "eval_engine" "$LOG" 2>/dev/null; then
  echo "🔒 [計器読了ゲート] 実験スクリプト（$base）を書く前に計器の正本 eval_engine.py を Read してください。" >&2
  echo "" >&2
  echo "理由: net 計算・約定・コスト・entry_type(maker/taker) の規約は eval_engine.py が正本。" >&2
  echo "  最新標準（E25）= ラベル sim は eval_engine のみ・自作 net 計算なし。計器を読まず実験を書くと" >&2
  echo "  rc の net をそのまま教師にする等の取り違え（L-268 型）が起きる。" >&2
  echo "→ scripts/priority_rebuild/eval_engine.py を Read tool で開いてから実装してください。" >&2
  exit 2
fi
exit 0
