#!/bin/bash
# PreToolUse on Write|Edit — 設計書前 しっかりベースアップ ゲート（2026-06-15 まこさん承認）。
# 旧版は file_path に "ml_pipeline_baseline"（廃止8工程フロー）を含む時だけ発火＝死にフック化していた。
# → 現行設計書（*_design.md / strat_v9ml_design.md / acceptance.md）を書く瞬間に、直近 WINDOW 分の
#    「広い探索」ベースアップが無ければ block（裏取り1発・スニペット逃げ・ソース偏りを物理的に塞ぐ）:
#      WebSearch ≥ 3 ／ 跨いだソース種別 ≥ 2 ／ WebFetch ≥ 2 （search_log.txt を集計）
# 注: 「探索的か確認的か（固有名詞狙い撃ち）」は機械判定不能＝search_log の事後チェックで補完（透明化）。
INPUT=$(cat)
FILE_PATH=$(printf '%s' "$INPUT" | python3 -c "import sys,json
try: print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))
except Exception: print('')" 2>/dev/null)
BASE=$(basename "$FILE_PATH")
case "$BASE" in
  *_design.md|strat_v9ml_design.md|acceptance.md) ;;
  *) exit 0 ;;
esac

# 除外（まこさん承認 2026-06-22・環境整備サイクル）: net不変のツール acceptance
#   （命名規約／出力名／上書きガード等・戦略 net に不関与）は、クオンツ文献ベースアップの対象外。
#   report.py/plot_trades.py が require_acceptance ゲート対象外なのと同じ思想。
#   acceptance が自分で「BASEUP_EXEMPT」を宣言した時のみスキップ（戦略/改善設計は従来どおり要ベースアップ）。
#   Write の content / Edit の new_string、または既存ファイル本文に BASEUP_EXEMPT があれば通す。
CONTENT=$(printf '%s' "$INPUT" | python3 -c "import sys,json
try:
    ti=json.load(sys.stdin).get('tool_input',{}) or {}
    print(ti.get('content','') or ti.get('new_string',''))
except Exception: print('')" 2>/dev/null)
if printf '%s' "$CONTENT" | grep -q "BASEUP_EXEMPT"; then exit 0; fi
if [ -f "$FILE_PATH" ] && grep -q "BASEUP_EXEMPT" "$FILE_PATH"; then exit 0; fi

STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
LOG="$STATE/search_log.txt"
WINDOW=3600   # 直近60分のベースアップを集計

RESULT=$(LOG="$LOG" WINDOW="$WINDOW" python3 -c '
import os, time
log=os.environ["LOG"]; win=int(os.environ["WINDOW"]); now=int(time.time())
# ドメイン→カテゴリ（まこさんの5カテゴリ＝学術 / SSR系クオンツ / 有名クオンツ実戦 / 暗号資産VC・データ）
CAT={
 "academic":["arxiv.org","ar5iv.labs.arxiv.org","papers.ssrn.com","ssrn.com","escholarship.org","biorxiv.org","nber.org"],
 "ssr_quant":["hudsonthames.org","quantstart.com","quantinsti.com","quantdare.com","github.com"],
 "famous_quant":["quantocracy.com","epchan.blogspot.com","alphaarchitect.com","quantpedia.com","robotwealth.com"],
 "crypto_vc_data":["glassnode.com","kaiko.com","coinmetrics.io","messari.io","paradigm.xyz","galaxy.com","a16zcrypto.com","gauntlet.xyz"],
}
def cat_of(dom):
    dom=dom.strip().lower()
    for c,ds in CAT.items():
        for d in ds:
            if d and d in dom: return c
    return None
ns=nf=0; cats=set()
try:
    for line in open(log):
        p=line.rstrip("\n").split("\t")
        if len(p)<4: continue
        try: ts=int(p[0])
        except ValueError: continue
        if now-ts>win: continue
        tool=p[1]; doms=p[3]
        for dom in doms.split(","):
            c=cat_of(dom)
            if c: cats.add(c)
        if tool=="Search": ns+=1
        elif tool=="Fetch": nf+=1
except FileNotFoundError:
    pass
print(f"{ns} {nf} {len(cats)}")
' 2>/dev/null)
NS=$(echo "$RESULT" | awk '{print $1}'); NF=$(echo "$RESULT" | awk '{print $2}'); NC=$(echo "$RESULT" | awk '{print $3}')
NS=${NS:-0}; NF=${NF:-0}; NC=${NC:-0}

MISS=""
[ "$NS" -ge 3 ] || MISS="${MISS}  - WebSearch 回数 ${NS}/3（複数角度＝1発の確認検索を禁止）\n"
[ "$NC" -ge 2 ] || MISS="${MISS}  - 跨いだソース種別 ${NC}/2（学術／SSR系クオンツ／有名クオンツ実戦／暗号資産VC・データ のうち2種別以上）\n"
[ "$NF" -ge 2 ] || MISS="${MISS}  - WebFetch 回数 ${NF}/2（一次ソース精読＝スニペット要約で済ませない）\n"

if [ -n "$MISS" ]; then
  printf "🔒 [設計書前 しっかりベースアップ ゲート] %s を書く前に、足がかり・知見を広げる広い検索が必要（直近60分・search_log.txt 集計）。\n未達:\n%b" "$BASE" "$MISS" >&2
  printf "狙うソース（広く・複数種別を跨ぐ）: 学術=arxiv.org papers.ssrn.com escholarship.org / SSR系クオンツ=hudsonthames.org quantstart.com github.com / 有名クオンツ(実戦)=quantpedia.com epchan.blogspot.com alphaarchitect.com / 暗号資産VC・データ=glassnode.com kaiko.com coinmetrics.io\n" >&2
  printf "※裏取り(固有名詞で答えを狙い撃ち)でなく、知らない足がかりを広く探す検索を（まこさん 2026-06-15）。\n" >&2
  exit 2
fi
exit 0
