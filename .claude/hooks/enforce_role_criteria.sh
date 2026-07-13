#!/bin/bash
# enforce_role_criteria.sh — PreToolUse on Write|Edit（2026-06-29 まこさん承認で新設）
# 目的: 改善提案（acceptance.md）を書く瞬間に「対象戦略の役割（スキャル/デイトレ…）に反する案」を物理的に止める。
#   背景＝CC が E37=スキャル（件数を上げて小さく多数取る）の役割を忘れ、件数±0 の floor 単独案を出し、
#   ⑩戦略整合に矛盾を自分で書きながら「頻度は次 iter」と尻すぼみ容認した（2026-06-29 事案・E34 iter0/3 再演）。
#   ＝役割は §1.2.1 散文 auto-load では提案の瞬間に錨が下りない（feedback_enforcement_at_proposal_time）。
#
# 汎用設計（E37 限定でない・PORTFOLIO_CHECK と同じマーカー追従）:
#   adopted_strategies.md の <!-- ROLE_CHECK: e37=scalp ; e36=daytrade ; ... --> を読み、
#   acceptance の TARGET スクリプト token（e3N）の役割を引いて、役割ごとのルールを当てる。
#   hook に戦略名を焼かない＝戦略が増えたらマーカー1行追加で自動追従。役割未定義の戦略はスルー（誤発火しない）。
#
# 役割ルール:
#   scalp    : F 受け入れに「件数/日が増える（高頻度＝役割）」基準が必須＋『件数±0/減・頻度は次 iter』の尻すぼみ容認文言を禁止。
#   daytrade : 「スキャル化/高頻度化」など役割（デイトレ＝1ポジを伸ばす）を壊す文言を禁止（§1.2.1 役割固定）。
#   その他   : 当面ルールなし（役割が固まったら本 case に足す＝拡張可）。
#
# 限界: チャットの口頭コメントは止められない（ツール呼び出しでない）。acceptance を正式に書く瞬間には必ず止まる。
#   役割の妥当性そのもの（scalp で良いか）はまこさんが決める＝本 hook は「役割に反する案を書けなくする」だけ。

ADOPTED="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/adopted_strategies.md"

INPUT=$(cat)

# サブエージェント（Workflow/Agent 内）は通す（デッドロック回避・他 hook と同型）
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

FILE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)
BASE=$(basename "$FILE")
# 対象は acceptance.md のみ（最小強制）
[ "$BASE" = "acceptance.md" ] || exit 0

# 効果的な acceptance 内容を得る（Write=content / Edit=現ファイルに old→new 適用）
CONTENT=$(printf '%s' "$INPUT" | python3 -c "
import sys,json
d=json.load(sys.stdin); ti=d.get('tool_input',{}) or {}
fp=ti.get('file_path',''); c=ti.get('content')
if c is None:
    old=ti.get('old_string'); new=ti.get('new_string') or ''
    try:
        cur=open(fp).read()
    except Exception:
        cur=''
    c = cur.replace(old,new) if old else (cur+new)
sys.stdout.write(c or '')
" 2>/dev/null)
[ -z "$CONTENT" ] && exit 0

# TARGET スクリプトの token（e3N）を取る
TOKEN=$(printf '%s' "$CONTENT" | grep -m1 -oE 'e3[0-9]+' | head -1)
[ -z "$TOKEN" ] && exit 0

# ROLE_CHECK マーカーから token の役割を引く
marker=$(grep -m1 "ROLE_CHECK:" "$ADOPTED" 2>/dev/null)
[ -z "$marker" ] && exit 0
ROLE=$(printf '%s' "$marker" | sed -n "s/.*[^a-z]${TOKEN}=\([a-z_]*\).*/\1/p")
[ -z "$ROLE" ] && ROLE=$(printf '%s' "$marker" | sed -n "s/.*${TOKEN}=\([a-z_]*\).*/\1/p")
[ -z "$ROLE" ] && exit 0   # 役割未定義＝スルー（誤発火しない）

case "$ROLE" in
  scalp)
    # ① 尻すぼみ容認文言の禁止（件数を上げない/後回しを成功扱い）
    bad=$(printf '%s' "$CONTENT" | grep -oE '件数±0|件数は不変|件数は増やさ|件数を増やさ|頻度は次|頻度は iter|頻度は後|低頻度でも' | head -1)
    if [ -n "$bad" ]; then
      echo "🔒 [役割ゲート: ${TOKEN}=scalp] スキャル戦略の acceptance に『件数を上げない/頻度を後回し』を成功扱いする文言があります（尻すぼみ容認＝役割違反）。" >&2
      echo "  検出: 「$bad」" >&2
      echo "  → スキャル(${TOKEN})は『件数を上げて小さく多数取る』が役割（cat_requirements §1.2.1）。件数/日を上げる設計に直してください（feedback_scalp_daytrade_frequency_floor）。" >&2
      exit 2
    fi
    # ② 件数/日の増加基準が在ること（F 受け入れに高頻度の合格条件）
    if ! printf '%s' "$CONTENT" | grep -qE '件数/日|件数.{0,24}(増|上回|高頻度|スキャル頻度)'; then
      echo "🔒 [役割ゲート: ${TOKEN}=scalp] スキャル戦略の acceptance に『件数/日が増える（高頻度＝役割）』の合格基準がありません。" >&2
      echo "  → F 受け入れ判定に『件数/日が現状を明確に上回る（スキャル頻度）こと・増えなければ不採用』を一級基準として入れてください（§1.2.1・feedback_scalp_daytrade_frequency_floor）。" >&2
      exit 2
    fi
    ;;
  daytrade)
    bad=$(printf '%s' "$CONTENT" | grep -oE 'スキャル化|高頻度化|件数を数倍|件数を大幅に増' | head -1)
    if [ -n "$bad" ]; then
      echo "🔒 [役割ゲート: ${TOKEN}=daytrade] デイトレ戦略の acceptance に役割（1ポジを伸ばすデイトレ）を壊す文言があります。" >&2
      echo "  検出: 「$bad」" >&2
      echo "  → ${TOKEN} はデイトレ型（§1.2.1 役割固定）。スキャル化は別戦略（E37）の役割です。" >&2
      exit 2
    fi
    ;;
  *) : ;;  # 役割ルール未定義＝スルー
esac
exit 0
