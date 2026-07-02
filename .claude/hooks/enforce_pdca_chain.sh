#!/bin/bash
# enforce_pdca_chain.sh — PreToolUse on Write|Edit（2026-07-02 まこさん指示「PDCAとすべての思考がつながる仕組みを入れて」）
#
# 目的（全戦略共通）: PDCA の各段階(Check=analysis_block → Action=improvement_plan → Plan=acceptance)の"継ぎ目"を物理照合し、
#   前段の結論を引き継がずに次へ進めなくする＝「思考が繋がらない(分析を踏まえず別の思いつきで設計)」を構造で塞ぐ。
#   これが最深刻(まこさん)＝ここが繋がらないと PDCA が回らず永遠に改善しない。
#
# 共通強制（会話ログ由来・2026-07-02・戦略を問わない普遍原則）:
#   ■ Check(analysis_block.md): 件数(トレード数)を per-trade より先に(trade_analysis_kb §0①)・前後比較・原因3分類
#   ■ Action(improvement_plan.md): STEP1に件数＋前後比較 / 多角的な異手法比較2種以上(一手法固執防止) / 過去失敗(next_step)読了 /
#        末尾に【動かすレバー】を1つ確定＝機械可読マーカー <!-- LEVER: X -->
#   ■ 接続②(acceptance.md): improvement_plan の LEVER X を"逐語で"引き継ぐ（無ければブロック＝分析→設計の連結・10）
#
# ★E37 スキャル特有(手数料の壁7 / スキャル定義9 / 5分足設定12 / 件数がスキャル役割)は enforce_e37_pdca.sh（別 hook）。
# ★Entry/Exit セット(11)は「一つの戦術」＝常時強制しない（まこさん 2026-07-02）。
# 限界: hook は「継ぎ目で前段の結論を引き継いだか」までを守る。連結が本物かは score.py の数字＋まこさんの目。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
IMP="$STATE_DIR/improvement_plan.md"
READ_LOG="$STATE_DIR/read_log.txt"

INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

FILE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)
BASE=$(basename "$FILE")
case "$BASE" in
  analysis_block.md|improvement_plan.md|acceptance.md) : ;;
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

export PC_CONTENT="$CONTENT" PC_BASE="$BASE" PC_IMP="$IMP" PC_READLOG="$READ_LOG"
VIOL=$(python3 <<'PY'
import os, re
c=os.environ.get('PC_CONTENT',''); base=os.environ.get('PC_BASE','')
v=[]

if base=='analysis_block.md':
    cnt=re.search(r'件数|件/日|トレード数|取引数', c)
    per=re.search(r'勝率|gross|グロス|期待値|プロフィット|PF|平均勝ち|平均負け|出口効率|MFE|MAE|Sharpe|シャープ', c)
    if not cnt:
        v.append('[Check] 件数(トレード数)が無い＝まず件数を見る(trade_analysis_methods_kb §0①)')
    elif per and per.start()<cnt.start():
        v.append('[Check] 件数より先に per-trade「%s」を語っている＝件数を最初に見る' % c[per.start():per.start()+8].strip())
    if not re.search(r'前回|今回|vs|前後|激変|前後比較', c):
        v.append('[Check] 前後比較(前回vs今回)が無い(§0①・件数の激変が最大の発見)')
    if not re.search(r'戦略欠陥|執行|regime|レジーム|3分類|原因3', c):
        v.append('[Check] 原因3分類(戦略欠陥/執行/regime)が無い(§7)')

elif base=='improvement_plan.md':
    if not re.search(r'件数|トレード数', c):
        v.append('[Action-STEP1] 観察に件数(トレード数)が無い＝件数を起点に(§0①)')
    if not re.search(r'前回|今回|vs|前後|激変', c):
        v.append('[Action-STEP1] 前後比較(前回vs今回)が無い')
    n=len(set(re.findall(r'逆張り|順張り|ブレイク|ブレイクアウト|トレンド|マーケットメイク|MM|プルバック|戻り売り', c)))
    if n<2:
        v.append('[Action-STEP3.5] 多角的な異手法比較(逆張り/順張り/ブレイク/戻り売り 等 2種以上)が無い=一手法固執')
    if not re.search(r'<!--\s*LEVER:\s*\S', c):
        v.append('[Action-STEP4] 【動かすレバー】が1つに確定していない＝末尾に <!-- LEVER: 動かす値 --> を書く(接続②の引き継ぎ元)')
    rl=os.environ.get('PC_READLOG','')
    try: logged=open(rl).read()
    except Exception: logged=''
    if 'next_step' not in logged:
        v.append('[循環/過去失敗] 提案の前に next_step.md(過去iterの失敗=改善アーク)を Read していない＝同型再演防止(8)')

elif base=='acceptance.md':
    # 接続②: improvement_plan の LEVER を逐語で引き継いでいるか
    imp=os.environ.get('PC_IMP','')
    lever=None
    try:
        m=re.search(r'<!--\s*LEVER:\s*(.+?)\s*-->', open(imp).read())
        if m: lever=m.group(1).strip()
    except Exception: pass
    if not lever:
        v.append('[接続②] improvement_plan.md に確定レバー(<!-- LEVER: X -->)が無い＝先に Action(改善案収束)でレバーを1つ確定する')
    elif lever not in c:
        v.append('[接続②] improvement_plan の確定レバー「%s」を acceptance が逐語で引き継いでいない＝分析→設計が繋がっていない(10)' % lever)

print('\n'.join(v))
PY
)

if [ -n "$VIOL" ]; then
  echo "🔒 [PDCA連結ゲート: ${BASE}] PDCA の継ぎ目で前段の結論を引き継いでいません（思考が繋がらない＝永遠に改善しない・まこさん 2026-07-02）。" >&2
  printf '%s\n' "$VIOL" >&2
  echo "  → 流れ: Check(analysis_block:件数を先に→原因)→Action(improvement_plan:多角発散→レバーX確定<!--LEVER:X-->)→Plan(acceptance:レバーXを逐語で引き継ぎ設計)。継ぎ目を満たしてから書いてください。" >&2
  exit 2
fi
exit 0
