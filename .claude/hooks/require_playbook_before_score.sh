#!/bin/bash
# require_playbook_before_score.sh — PreToolUse on Bash
# score.py を「実際に python(3) で実行」する前に、その採点サイクルで analysis_playbook.md を
# Read tool で開いたか（marker playbook_fresh の有無）を確認。読んでいなければ exit 2 でブロック。
#
# 目的（まこさん指示 2026-06-10・②score.py起点）:
#   セッション冒頭の1回読了（require_read_before_work.sh）では、PDCA 採点段で
#   analysis_playbook §3.1（E番号命名・archive退避）等を守れなかった実証（E10）。
#   → 採点（score.py）ごとに分析手順を再読させる。
#
# marker ライフサイクル:
#   analysis_playbook を Read  → marker 作成（record_read.sh）
#   score.py を実行            → marker 削除（pdca_mark.sh）
#   = 次の score.py の前に marker が無い → 再読するまでブロック。
#
# 解除: .claude/ratchet/analysis_playbook.md を Read tool で開く（read_log と違い Read は常に
#   可能なのでデッドロックしない）。grep/表示だけは不可（marker は Read tool のみで立つ）。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
MARKER="$STATE_DIR/playbook_fresh"

INPUT=$(cat)
# score.py を「実際に python(3) で実行する形」のみ検知（grep/echo/別行言及では誤爆しない
#   = pdca_mark.sh と同一の正規表現で score.py 実行を判定）
IS_SCORE=$(printf '%s' "$INPUT" | python3 -c "import sys,json,re
try:
    d=json.load(sys.stdin)
except Exception:
    print('0'); sys.exit(0)
cmd=(d.get('tool_input',{}) or {}).get('command','') or ''
print('1' if re.search(r'python[0-9.]*[ \t]+[^|&;\n]*score\.py', cmd) else '0')" 2>/dev/null)

if [ "$IS_SCORE" != "1" ]; then
  exit 0
fi

if [ ! -f "$MARKER" ]; then
  echo "🔒 [analysis_playbook 再読ゲート] score.py 採点の前に analysis_playbook.md を Read tool で開いてください（②score.py起点・まこさん指示 2026-06-10）。" >&2
  echo "理由: セッション冒頭の1回読了では採点段で §3.1（E番号命名・archive退避）/ §2.4 ドローダウン3分類 等を守れなかった（E10）。採点ごとに分析手順を再読する。" >&2
  echo "解除: .claude/ratchet/analysis_playbook.md を Read tool で開く（grep/表示だけは不可）。" >&2
  exit 2
fi
exit 0
