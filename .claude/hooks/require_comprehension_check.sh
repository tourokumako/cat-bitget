#!/bin/bash
# require_comprehension_check.sh — PreToolUse on Bash|Edit|Write（2026-07-16 まこさん指示・新設）
# 目的: 「next_step に詳細に書いても新セッションCCは絶対読まず同じミスを繰り返す」対策。
#   新セッションCCが next_step の【理解確認テスト】Q1〜Q5 に自分の言葉で回答（.claude/state/comprehension_check.md）
#   するまで、e37 戦略の編集・本走をブロック＝「読んで理解した」ことを物理で担保（keyword 通過≠理解＝最終判断はまこさんの目）。
# 判別: e37_scalp.py / e37_range_scalp.py の Write|Edit、または python での e37 本走（出力モード）の時だけ発火。
#   comprehension_check.md に Q1〜Q5 の要点キーワードが揃っていなければブロック。marker は reset_read_log が SessionStart で消す。
#   解除は 2026-08-16 に廃止（まこさん指示）。
MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode"
[ ! -f "$MARK" ] && exit 0   # fast-mode 限定（ML復帰時は別運用）

INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0   # サブエージェントは通す（デッドロック回避・他 hook と同型）

# ★解除（合言葉）は 2026-08-16 に廃止＝まこさん指示「じゃあ強制解除できない状態にしろ」。通す道は無い。

# 発火対象か判定: e37 の編集（file_path）or e37 の python 本走（command・出力モード）
FP=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)
CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)
fire=0
printf '%s' "$FP"  | grep -qE 'e37_(range_)?scalp\.py$' && fire=1
# python での e37 本走（selftest/probe/deep_analysis/judgeは除外）
if printf '%s' "$CMD" | grep -qE 'python[0-9.]*[[:space:]]' && printf '%s' "$CMD" | grep -qE 'e37_(range_)?scalp\.py'; then
  printf '%s' "$CMD" | grep -qvE '(_probe|_deep_analysis)\.py' && \
  printf '%s' "$CMD" | grep -qvE '(--smoke|--selftest|-selftest|--param-schema-selftest|py_compile|--help)' && fire=1
fi
[ "$fire" -eq 0 ] && exit 0

CC="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/comprehension_check.md"
miss=""
if [ ! -f "$CC" ]; then
  miss="ファイルが無い"
else
  # Q1: 早切り/損切りは TP(勝ち玉)も切る＝不可能
  grep -qE '早切り|損切り|時間切れ' "$CC" && grep -qE 'TP|勝ち' "$CC" && grep -qE '不可能|巻き込|同時' "$CC" || miss="$miss Q1"
  # Q2: 前CCの結論は思い込み/嘘＝信用しない
  grep -qE '思い込み|嘘|間違' "$CC" && grep -qE '信用|引き継が|前提にし' "$CC" || miss="$miss Q2"
  # Q3: まこさんに相談・CCは提案しない/まこさんが導く
  { grep -qE 'まこさん' "$CC" && grep -qE '相談|導く|提案しない' "$CC"; } || miss="$miss Q3"
  # Q4: 6ヶ月(採点窓)だけ・全5年で走らせない
  { grep -qE '6ヶ月|採点窓' "$CC" && grep -qE '5年' "$CC"; } || miss="$miss Q4"
  # Q5: 実データ/コードを読んでから・思い込みで結論しない
  grep -qE '読' "$CC" && grep -qE '思い込み|考え' "$CC" || miss="$miss Q5"
  # Q6: 次タスク＝入口2パターン(down型/flat_up)の entry後の建玉の動きを詳細分析・entry_exit_matrix 必読
  { grep -qE 'down型|下落系' "$CC" && grep -qE 'flat_up|res_hi' "$CC" && grep -qE 'entry後|建玉|軌跡|動' "$CC" && grep -qE 'entry_exit_matrix' "$CC"; } || miss="$miss Q6"
fi

[ -z "$miss" ] && exit 0

echo "🔒 [理解確認ゲート・fast-mode] 新セッションCC は next_step の【理解確認テスト】Q1〜Q5 に回答してから e37 を触ってください（2026-07-16 まこさん指示）。" >&2
echo "" >&2
echo "未達: $miss" >&2
echo "" >&2
echo "背景: next_step に詳細に書いても CC は読まず同じミス（早切りで悪化・思い込み断言・無断変更・全5年走行）を繰り返す。" >&2
echo "対処: .claude/state/comprehension_check.md に Q1〜Q5 を【自分の言葉で】回答し、チャットにも出す（まこさんが理解を判断）。next_step の【理解確認テスト】に各問の正答の要点あり。" >&2
echo "  Q1=早切り/損切りは TP(勝ち玉)も同時に切る＝負けだけ切るのは原理的に不可能／Q2=前CCの Exit 結論は思い込み・嘘＝信用しない／Q3=CCは損切り提案せずまこさんに相談・まこさんが導く／Q4=fast-modeは6ヶ月(採点窓)だけ・全5年で走らせない／Q5=実データ/コード/ledgerを読み思い込みで結論しない／Q6=次タスク＝入口2パターン(down型:天井直近高値/flat_up:天井res_hi)の entry後の建玉の動きをパターン別に詳細分析・entry_exit_matrix.md 必読。" >&2
echo "（解除は 2026-08-16 に廃止＝合言葉では通りません）" >&2
exit 2
