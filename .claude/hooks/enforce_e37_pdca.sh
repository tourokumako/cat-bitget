#!/bin/bash
# enforce_e37_pdca.sh — PreToolUse on Write|Edit（2026-07-02 まこさん指示・共通/E37専用を明確に分離）
#
# 目的（E37=スキャル 特有のみ）: 全戦略共通の PDCA 連結・分析原則は enforce_pdca_chain.sh が担当。
#   本 hook は「E37=スキャル だからこそ必要な」失敗だけを、書く瞬間に物理強制する（他戦略は誤発火しない）。
#
# E37専用に強制する失敗（会話ログ由来・2026-07-02）:
#   ■ Check(analysis_block.md・e37): 件数がスキャル頻度(役割=一級基準)を満たすか判定（失格/達成）。スキャルは件数が一級(§1.2.1)。
#   ■ Plan(acceptance.md・e37):
#       7  手数料の壁: 手数料を超える TP幅(maker 往復)の見積もり（薄利多売の本質）
#       9  スキャル定義: 短保有（分単位・数分〜十数分）＝保有4h をスキャルと称した再演防止
#       12 5分足スキャル設定: RSI9 / MTF（上位足確認）＝technical_analysis_kb §4/§5（RSI14・MTFなし の再演防止）
#
# ★共通（件数を最初に/前後比較/原因3分類/多角比較/過去失敗/定量KPI/分析→設計の逐語連結）は enforce_pdca_chain.sh。
# ★Entry/Exit セット(11)は「一つの戦術」＝常時強制しない（まこさん 2026-07-02）。
# 限界: hook は「要点を書いたか」を守る。中身の質は score.py の数字＋まこさんの目。

INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

FILE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)
BASE=$(basename "$FILE")
case "$BASE" in
  analysis_block.md|acceptance.md) : ;;
  *) exit 0 ;;
esac

CONTENT=$(printf '%s' "$INPUT" | python3 -c "
import sys,json
d=json.load(sys.stdin); ti=d.get('tool_input',{}) or {}
fp=ti.get('file_path',''); c=ti.get('content')
if c is None:
    old=ti.get('old_string'); new=ti.get('new_string') or ''
    try: cur=open(fp).read()
    except Exception: cur=''
    c = cur.replace(old,new) if old else (cur+new)
sys.stdout.write(c or '')
" 2>/dev/null)
[ -z "$CONTENT" ] && exit 0

# E37 対象か（他戦略は誤発火しない）
printf '%s' "$CONTENT" | grep -qiE 'e37|trades_e37_range_scalp' || exit 0

export E37_CONTENT="$CONTENT" E37_BASE="$BASE"
VIOL=$(python3 <<'PY'
import os, re
c=os.environ.get('E37_CONTENT',''); base=os.environ.get('E37_BASE','')
v=[]

if base=='analysis_block.md':
    # 件数がスキャル頻度(役割=一級基準)を満たすか判定（スキャル特有）
    if not (re.search(r'スキャル|件/日', c) and re.search(r'失格|達成|未達|基準|一級|役割', c)):
        v.append('[E37-Check] 件数がスキャル頻度(役割=一級基準)を満たすかの判定(失格/達成)が無い(§1.2.1)')

elif base=='acceptance.md':
    # 7 手数料の壁
    if not re.search(r'手数料.{0,16}(超|上回|breakeven|往復|maker)', c):
        v.append('[E37-Plan⑦] 手数料を超える TP幅(maker往復) の見積もりが無い＝スキャルの本質(手数料の壁)')
    # 9 スキャル定義=短保有(分単位)
    if not re.search(r'保有.{0,14}(分|短)|数分|時間切れ.{0,10}分|hold.{0,10}分', c):
        v.append('[E37-Plan⑨] スキャル定義=短保有(分単位・数分)の設計が無い＝保有4h をスキャルと称した再演防止')
    # 12 5分足スキャル設定 RSI9 / MTF
    if not re.search(r'RSI\s*9|RSI\(9\)|MTF|上位足|マルチタイムフレーム', c):
        v.append('[E37-Plan⑫] 5分足スキャル設定(RSI9 or MTF=上位足確認)が無い(technical_kb §4/§5・RSI14/MTFなし の再演防止)')

print('\n'.join(v))
PY
)

if [ -n "$VIOL" ]; then
  echo "🔒 [E37スキャル強制ゲート: ${BASE}] E37=スキャル 特有の要件を満たしていません（2026-07-02）。" >&2
  printf '%s\n' "$VIOL" >&2
  echo "  → スキャル＝短保有・高頻度・薄利で手数料を超える(§1.2.1・technical_kb §4)。上を満たしてから書いてください。共通(件数/連結等)は PDCA連結ゲートが別途強制。" >&2
  exit 2
fi
exit 0
