#!/bin/bash
# require_spec_read_before_design.sh — PreToolUse on Write|Edit（2026-06-13 まこさん指示で新設）
# 目的: 設計書（*_design.md / strat_v9ml_design.md）を書く瞬間に、決済方法・ポジションの持ち方の
#   正本 exchange_spec.md（★決済方法）と cat_requirements.md（§6.1/§6.1.1 ポジション・§4.6 H制約）を
#   Read tool で読んでいなければ exit 2 で block する。
#   背景: CC は決済方法を読まず設計し、同サイド merge・部分決済(scale out)・add(cap0.12) を誤解する事案を
#   L-255(2026-06-09)・E34(2026-06-13) と2回再演。セッション開始時の cat_requirements 強制 read は
#   「読んでもインプットされない」と実証（まこさん 2026-06-13）→ just-in-time（設計の瞬間に読む）へ移す。
# 方針: 毎セッション必読には足さない（読む量を増やすと効かない実証）。設計書を書く瞬間だけ強制（最小強制）。
#   require_instrument_read_before_impl.sh（実装スクリプト前に eval_engine 強制）と同型。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
LOG="$STATE_DIR/read_log.txt"

input=$(cat)

fp=$(printf '%s' "$input" | python3 -c "import sys,json
try:
    d=json.load(sys.stdin)
    print(d.get('tool_input',{}).get('file_path',''))
except Exception:
    print('')" 2>/dev/null)

base=$(basename "$fp")

# 対象: 設計書のみ（*_design.md / strat_v9ml_design.md）
is_design=0
case "$base" in
  *_design.md|strat_v9ml_design.md) is_design=1 ;;
esac
[ "$is_design" -eq 0 ] && exit 0

# exchange_spec(決済方法) と cat_requirements(ポジション/H制約) を Read 済みか（record_read.sh が read_log に記録）
missing=()
grep -q "exchange_spec" "$LOG" 2>/dev/null || missing+=("exchange_spec.md（★決済方法＝同サイドmerge・平均建値・部分決済scale out・add cap0.12）")
grep -q "cat_requirements" "$LOG" 2>/dev/null || missing+=("cat_requirements.md（§6.1/§6.1.1 ポジションの持ち方・§4.6 H制約）")

if [ ${#missing[@]} -gt 0 ]; then
  echo "🔒 [設計書 決済方法ゲート] 設計書（$base）を書く前に決済方法・ポジションの持ち方の正本を Read してください。" >&2
  echo "" >&2
  echo "未読（Read tool で開いていない）:" >&2
  for m in "${missing[@]}"; do echo "  - $m" >&2; done
  echo "" >&2
  echo "理由: CC は決済方法を読まず設計し、同サイド merge・部分決済(scale out)・add(cap0.12) を誤解（L-255 / E34 で2回再演）。" >&2
  echo "  正しい仕様: 同サイドは1ポジに統合・平均建値／決済は全体も部分も可（複数TPで段階利確 scale out・最大20個）／予算0.12は全建玉の合計。" >&2
  echo "→ 上記を Read tool で開いてから設計書を書いてください（just-in-time＝設計の瞬間に読む・セッション開始時に読んでもインプットされない実証 2026-06-13）。" >&2
  exit 2
fi
exit 0
