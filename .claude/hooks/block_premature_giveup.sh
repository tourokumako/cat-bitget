#!/bin/bash
# block_premature_giveup.sh — PreToolUse on Write|Edit
# 「中身の打ち切り＝やらない理由で潰して止まる」を物理禁止（まこさん 2026-06-28 命令「ちゃんと強制して」）。
#
# 背景（恥・固定）:
#   block_uchikiri.sh は「破棄/打ち止め」等の【表面語】を止めるが、CC は語を使わず【中身】で諦める＝
#   「期待値が低い」「効果は小さい」「筋が悪い」「やる意味が薄い」「これ以上は無理」「family が同じだから」等で
#   分析・改善を事前却下して何も検証せず止まる（評論家・受け身・案が浅い）。まこさん激怒。
#   ＝CC の存在意義（目標への全力コミット）の真逆。memory feedback_execute_dont_critique_commit / L-309。
#
# ★この hook が強制するのは「思いつく限りの分析をしつくしたか」だけ（まこさん 2026-06-28 訂正）:
#   ⛔ 「まこさんの案を全部 実エンジンで検証したか」は強制しない＝それは機嫌取りの侮辱（まこさんが明確に却下）。
#   ✅ 「分析をしつくした上でのみ "これ以上改善できない" と言ってよい」を物理化する（しつくす前の却下は怠惰）。
#
# 強制内容:
#   decision artifact（ledger.md / next_step.md / forward_action.md / acceptance.md）に【中身の打ち切り/事前却下】語を
#   書く時、.claude/state/exhaustion_check.md が「思いつく限りの分析をしつくした証跡」で埋まっていなければ block。
#
# 解除（exhaustion_check.md の必須見出し・全部必要）:
#   ## 試した分析角度   … 実データ/実エンジンで見た角度を列挙（最低3つ・出典つき）
#   ## 未試行の分析角度  … 思いつく限り列挙。残っているうちは打ち止め不可＝先に潰せ
#   未試行: なし        … 未試行ゼロを明示宣言する行（嘘は まこさんが30秒監査）
#
# 限界（正直に）: CC が exhaustion_check に嘘（未試行ゼロと書くが実は残っている）を書けばすり抜ける（同型バイアス）。
#   だが「試した角度／未試行角度」を列挙させること自体が CC に網羅を迫り、まこさんが監査できる。

INPUT=$(cat)

# サブエージェントは通す（デッドロック回避・他hookと同型）
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

FILE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)
case "$FILE" in
  *ledger.md|*next_step.md|*forward_action.md|*acceptance.md) ;;
  *) exit 0 ;;
esac

NEW=$(printf '%s' "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin); ti = d.get('tool_input', {}) or {}
s = (ti.get('content', '') or '') + (ti.get('new_string', '') or '')
for e in (ti.get('edits', []) or []):
    s += e.get('new_string', '') or ''
print(s)" 2>/dev/null)

# 【中身の打ち切り/事前却下】語（やらない理由で潰す／しつくす前に閉じる）。正当な honest 結論も対象＝網羅証跡を要求する。
HIT=$(printf '%s' "$NEW" | grep -oE "期待値が低い|期待値は低い|効果が小さいので|効果は小さいので|筋が悪い|やる意味が薄い|試す意味が薄い|試す価値が(低い|薄い)|試すまでもない|これ以上(の)?(改善|止血|削減|工夫)は(難しい|無理|できない|不可能|乏しい)|構造的に(閉じた|無理|不可能)|望み薄|見込み薄|採用に至らない見込み|やっても無駄|改善の余地は(乏しい|小さい|ない)" | sort -u | tr '\n' ' ')

# 【戦略レベルの打ち切り/no-edge】語（2026-06-30 まこさん指示＝probe で no-edge 断定を物理禁止・L-277/L-278）。
#   背景: CC は crude な probe（毎バー固定時間・対称固定バリア・ML/メタ無し）を8通り＝同じ方法の変種でやり「やり尽くした風」に見せ
#   「入口にエッジ無し/死に枠」と戦略を打ち切った。block_uchikiri は「打ち切り」を誤爆回避で除外・本 hook は怠惰語のみ＝隙間。
#   ＝戦略を「エッジ無し/no-edge/死に枠/打ち切り」と結論する時は、probe でなく ① score.py 両窓 MVP の数字 ② 方法軸が複数（同じ
#   crude 方法の変種でない＝データ源/ラベリング/特徴/horizon/モデルのうち複数を跨ぐ）の証跡を exhaustion_check に要求する。
DEADEND=$(printf '%s' "$NEW" | grep -oE "エッジ(が|は)?(無|な)い|エッジ無し|エッジなし|no-edge|no edge|死に枠|入口(路線|探し)?.{0,8}(打ち切|死に|閉じ|無し)|(戦略|入口).{0,6}(エッジ(が|は)?(無|な)い|無し)" | sort -u | tr '\n' ' ')

[ -z "$HIT" ] && [ -z "$DEADEND" ] && exit 0

# exhaustion_check.md の充足を確認（.claude/state/ 直下を直に見る）
EC="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/exhaustion_check.md"
OK=0
if [ -f "$EC" ]; then
  if grep -q "## 試した分析角度" "$EC" && grep -q "## 未試行の分析角度" "$EC" \
     && grep -qE "未試行[:：][ 　]*なし" "$EC"; then
    OK=1
  fi
fi

# ② いい面/活かし方の併記チェック（駄目な面だけで即却下・握りつぶしを禁止・まこさん 2026-06-28）
#   ＝アイデアを却下する時は「いい面・活かせる点・部分採用・別用途・転用・次にどう活かすか」も必ず書く。
UPSIDE=$(printf '%s' "$NEW" | grep -oE "いい面|良い面|良い点|長所|活かせる|活かし方|活かす|転用|部分採用|別用途|次に活かす|横展開|次の一手|配分に転用|サイジングに" | head -1)

# ③ 戦略 no-edge/打ち切り 専用ゲート（2026-06-30）: probe でなく score.py 両窓 MVP ＋ 方法軸が複数 を exhaustion_check に要求。
#   ＝同じ crude 方法の変種を並べた「擬似網羅」では戦略を打ち切れない。score.py 両窓の数字 と 方法軸セクションが要る。
DEADEND_OK=1
if [ -n "$DEADEND" ]; then
  DEADEND_OK=0
  if [ -f "$EC" ] \
     && grep -q "score.py" "$EC" \
     && grep -qE "両窓|学習窓.*採点窓|採点窓.*学習窓" "$EC" \
     && grep -q "## 方法軸" "$EC"; then
    DEADEND_OK=1
  fi
fi

if [ "$OK" -ne 1 ] || [ -z "$UPSIDE" ] || [ "$DEADEND_OK" -ne 1 ]; then
  echo "🔒 [打ち止め禁止ゲート] 事前却下/打ち止め語 検出: ${HIT}${DEADEND}（まこさん 2026-06-28/06-30）" >&2
  if [ "$OK" -ne 1 ]; then
    echo "  ① 分析をしつくした証跡なし＝『思いつく限りの分析をしつくした上でのみ \"これ以上できない\" と言ってよい』。" >&2
    echo "     → .claude/state/exhaustion_check.md を埋めよ: ## 試した分析角度 ／ ## 未試行の分析角度 ／『未試行: なし』宣言。" >&2
    echo "     ⛔ 『まこさんの案を全部 検証したか』は問わない（機嫌取りは侮辱）。問うのは『分析をしつくしたか』のみ。" >&2
  fi
  if [ -z "$UPSIDE" ]; then
    echo "  ② いい面/活かし方の併記なし＝駄目な面だけ見て即却下・握りつぶしている（まこさん 2026-06-28）。" >&2
    echo "     → 却下/不採用にする時は必ず『いい面・活かせる点・部分採用・別用途・転用・次にどう活かすか』を併記せよ。" >&2
    echo "     ＝ダメ出し(懸念)は必要だが、いい面も見出す。潰した案は next_step に『次に実エンジンで数字を出す対象』として残す。" >&2
  fi
  if [ "$DEADEND_OK" -ne 1 ]; then
    echo "  ③ 戦略を『エッジ無し/no-edge/死に枠/打ち切り』と結論するなら、probe でなく実エンジンの数字＋方法の多様性が要る（まこさん 2026-06-30・L-277/L-278）。" >&2
    echo "     → exhaustion_check.md に: (a)『score.py』＋『両窓』の MVP 採点数字（probe のあたり付けでなく実エンジン判定）。" >&2
    echo "        (b)『## 方法軸』セクション＝試した角度が同じ crude 方法の変種でなく データ源/ラベリング/特徴/horizon/モデル のうち複数を跨ぐ証跡。" >&2
    echo "     ＝crude な probe を8通り＝同じ方法の変種で『やり尽くした風』に戦略を打ち切るのを物理禁止（2026-06-30 事案）。" >&2
  fi
  exit 2
fi
exit 0
