#!/bin/bash
# require_precheck_before_score.sh — PreToolUse on Bash
# score.py を「実際に python(3) で実行」する前に、対象CSVが採点前ゲート（precheck.py）を
# PASS しているか（marker precheck_pass_<csv名> の有無）を確認。無ければ exit 2 でブロック。
#
# 目的（まこさん命令 2026-06-12「手数料負けする設計を事前に止めろ・すべての抜け穴を塞げ」）:
#   E21 は手数料負け確定（追加玉 breakeven 0.55）とドリフト 26pt が学習期間データだけで
#   事前に分かったのに採点 1 回を浪費した。L-40（TP_PCT 事前手数料計算義務）を全出口・
#   入口選別変更に拡張した precheck.py を、採点の前提として物理強制する。
#
# marker ライフサイクル:
#   precheck.py <train_csv> が PASS → .claude/state/precheck_pass_<採点csv名> 作成
#   score.py <csv> 実行時に precheck_pass_<csv名> が無い → ブロック
#   （既採点アーティファクトの再採点は precheck.py --already-scored で marker 発行）

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"

INPUT=$(cat)
CSV=$(printf '%s' "$INPUT" | python3 -c "import sys,json,re,os
try:
    d=json.load(sys.stdin)
except Exception:
    print(''); sys.exit(0)
cmd=(d.get('tool_input',{}) or {}).get('command','') or ''
m=re.search(r'python[0-9.]*[ \t]+[^|&;\n]*score\.py[ \t]+([^ \t|&;\n]+\.csv)', cmd)
print(os.path.basename(m.group(1)) if m else '')" 2>/dev/null)

if [ -z "$CSV" ]; then
  exit 0
fi

if [ ! -f "$STATE_DIR/precheck_pass_$CSV" ]; then
  echo "🔒 [採点前ゲート] $CSV は precheck.py を通っていません（まこさん命令 2026-06-12・手数料負け/ドリフトの事前検査）。" >&2
  echo "実行: python3 scripts/priority_rebuild/precheck.py <学習期間trades.csv> [--vs <地面train>] [--target <採点候補csv>] --authorize $CSV" >&2
  echo "FAIL（breakeven<1.0 / ドリフト≥20pt）の場合は設計を直す。採点1回を浪費しない。既採点物の再採点のみ --already-scored 可。" >&2
  exit 2
fi
exit 0
