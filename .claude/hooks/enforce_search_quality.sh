#!/bin/bash
# enforce_search_quality.sh — PreToolUse on WebSearch
# 「程よい検索」の物理強制（まこさん 2026-06-14・検索精度が低い＝Gemini に聞いた方がマシ事案）。
# CC は (a) キーワードサラダの広い検索で retail SEO を掴む (b) スニペット要約で済ませ精読しない、で
# 設計のベースアップが浅くなる。意思に頼らず以下を物理ゲートする:
#   ①1意図に絞る: query ≤ 12 語（超過＝キーワードサラダ→ブロック）
#   ②厳密ソースを狙う: allowed_domains 必須（未指定＝retail を弾けない→ブロック・推奨ドメイン提示）
#   ③精読: WebFetch なしで WebSearch を 4 回連投したらブロック（良いソースを WebFetch で読んでから次へ）
# 注: deep-research（Workflow 内の検索）は別経路＝本ゲートは CC 直接の WebSearch のみ対象。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
CNT_FILE="$STATE_DIR/websearch_since_fetch"

INPUT=$(cat)
PARSED=$(printf '%s' "$INPUT" | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
except Exception:
    print('0 1'); sys.exit(0)
ti=(d.get('tool_input',{}) or {})
q=(ti.get('query') or '').strip()
ad=ti.get('allowed_domains') or []
print(len(q.split()), 1 if ad else 0)
" 2>/dev/null)
WORDS=$(printf '%s' "$PARSED" | awk '{print $1}')
HASDOM=$(printf '%s' "$PARSED" | awk '{print $2}')

# ① 1意図（語数）
if [ "${WORDS:-0}" -gt 12 ]; then
  echo "🔒 [検索精度ゲート①] クエリ ${WORDS}語＝キーワードサラダ。1意図に絞れ（≤12語）。詰め込むと retail SEO/マーケ記事を掴む（まこさん 2026-06-14）。" >&2
  exit 2
fi

# ② 厳密ソース（allowed_domains 必須）
if [ "${HASDOM:-0}" != "1" ]; then
  echo "🔒 [検索精度ゲート②] allowed_domains 未指定。厳密ソースを狙え（retail TAブログ/インジ販売を弾く）。" >&2
  echo "   推奨: arxiv.org papers.ssrn.com escholarship.org ncbi.nlm.nih.gov quantstart.com quantinsti.com hudsonthames.org github.com" >&2
  echo "   広い探索が要る時も最低1ドメインを指定（探索後に絞る）。" >&2
  exit 2
fi

# ③ 精読（WebFetch なしの連投を止める）
CNT=$(cat "$CNT_FILE" 2>/dev/null || echo 0)
if [ "${CNT:-0}" -ge 4 ]; then
  echo "🔒 [検索精度ゲート③] WebFetch なしで WebSearch を ${CNT} 回連投。良いソースを WebFetch で精読してから次の検索へ（スニペット要約で済ませない・まこさん 2026-06-14）。" >&2
  exit 2
fi

exit 0
