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
[ -z "$HIT" ] && exit 0

# exhaustion_check.md の充足を確認（.claude/state/ 直下を直に見る）
EC="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/exhaustion_check.md"
OK=0
if [ -f "$EC" ]; then
  if grep -q "## 試した分析角度" "$EC" && grep -q "## 未試行の分析角度" "$EC" \
     && grep -qE "未試行[:：][ 　]*なし" "$EC"; then
    OK=1
  fi
fi

if [ "$OK" -ne 1 ]; then
  echo "🔒 [打ち止め禁止ゲート・中身版] 事前却下/打ち止め語 検出: $HIT（まこさん 2026-06-28「ちゃんと強制して」）" >&2
  echo "  ＝CC は『やらない理由』で 分析・改善を潰して止まる癖がある（評論家・受け身・案が浅い）。" >&2
  echo "  ＝改善に全力コミット＝『思いつく限りの分析をしつくした上でのみ \"これ以上できない\" と言ってよい』。" >&2
  echo "" >&2
  echo "  → 打ち止め/却下を書く前に .claude/state/exhaustion_check.md を埋めよ（全部必要）:" >&2
  echo "     ## 試した分析角度   … 実データ/実エンジンで見た角度を列挙（最低3つ・出典つき）" >&2
  echo "     ## 未試行の分析角度  … 思いつく限り列挙。残るうちは打ち止め不可＝先に潰せ" >&2
  echo "     未試行: なし        … 未試行ゼロを明示宣言する行" >&2
  echo "  ⛔ 注意: 『まこさんの案を全部 検証したか』は問わない（機嫌取りは侮辱）。問うのは『分析をしつくしたか』のみ。" >&2
  exit 2
fi
exit 0
