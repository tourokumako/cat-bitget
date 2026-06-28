#!/bin/bash
# require_probe_naming.sh — PreToolUse on Bash（2026-06-26 まこさん承認で新設）
# 目的: read-only 分析スクリプトを /tmp・scratchpad から走らせる時、命名を *_probe.py / *_deep_analysis.py に物理強制。
#   背景: 2026-06-26 に分析 probe を _probe 接尾辞なし（e36_winner_vs_te_overlap.py）で命名し、pdca_mark が
#   「e36 実験」と誤検知して need_score 旗を誤発火させた（pdca_mark は *_probe/*_deep_analysis のみ実験から除外）。
#   命名規約（pdca_flow §5）を物理化し、誤発火・命名漏れを根から断つ。
# 判別: 実戦略は scripts/priority_rebuild/ 配下、read-only 分析は /tmp・scratchpad 配下＝置き場所で判別できる。
#   /tmp・scratchpad から python で走らせる .py が *_probe / *_deep_analysis でなければ block（改名を促す）。

INPUT=$(cat)
# サブエージェント（Workflow/Agent 内）は通す（デッドロック回避・他 hook と同型）
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)

# python 実行コマンドの時だけ判定（ls/mv/rm/cat で mention しただけでは止めない＝改名・削除はできるように）
has_python=$(printf '%s' "$CMD" | grep -cE 'python[0-9.]*[[:space:]]')
# /tmp・/private/tmp 配下の .py パスを抽出 → そのうち *_probe.py / *_deep_analysis.py で終わらないものが規約外
bad=$(printf '%s' "$CMD" | grep -oE '(/private/tmp|/tmp)/[^ "'"'"';|&]*\.py' | grep -vE '(_probe|_deep_analysis)\.py$')

if [ "$has_python" -gt 0 ] && [ -n "$bad" ]; then
  echo "🔒 [probe 命名ゲート] /tmp・scratchpad から走らせる分析スクリプトは *_probe.py または *_deep_analysis.py 命名にしてください（pdca_flow §5・2026-06-26 まこさん承認）。" >&2
  echo "" >&2
  echo "規約外（改名して再実行）:" >&2
  printf '%s\n' "$bad" | sed 's/^/  - /' >&2
  echo "" >&2
  echo "理由: 接尾辞なしの e3N_*.py 等は pdca_mark が『実験』と誤検知し need_score 旗を誤発火させる（2026-06-26 事案）。_probe 命名で物理除外する。" >&2
  exit 2
fi

# 正しい命名で probe を走らせる時は、疑似シミュの位置づけを必ず表示（2026-06-26 まこさん承認・疑似シミュ値の設計焼き込み防止）
#   背景: 2026-06-26 add ゲート設計で probe(疑似シミュ)の AUC0.83/θ≤0.4/段数3 を「クリア」扱いし acceptance に固定値で焼き込み→まこさん指摘。
#   probe は あたりを付ける参考ツール＝決定的根拠でない。使う瞬間に錨を下ろす（SessionStart でなく実行時＝feedback_enforcement_at_proposal_time）。
good=$(printf '%s' "$CMD" | grep -oE '(/private/tmp|/tmp)/[^ "'"'"';|&]*(_probe|_deep_analysis)\.py')

# ── ゲートA（2026-06-28 まこさん承認）: probe を走らせる前に「前回データ全文読了 ＋ STEP1 観察」を物理強制 ──
#   背景: require_analysis_before_proposal の着手ゲートは acceptance/analysis_block を書く瞬間にしか発火せず、
#   probe(Bash)から始めると前回データ未読のまま分析できた（2026-06-28 事案＝report/analyze を読まず probe 量産・N10 を再発見）。
#   probe 実行(Bash)で発火する本 hook に「対象 report_/analysis_ 読了 ＋ improvement_plan STEP1(良い点3/最も黒字/問題点3・各$)」を要求。
if [ "$has_python" -gt 0 ] && [ -n "$good" ]; then
  STATE_A="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
  LOG_A="$STATE_A/read_log.txt"; PLAN_A="$STATE_A/improvement_plan.md"
  gaps=()
  grep -q "/report_"   "$LOG_A" 2>/dev/null || gaps+=("対象の report_*.txt を Read tool で全文開く（結果一覧 A〜L）")
  grep -q "/analysis_" "$LOG_A" 2>/dev/null || gaps+=("対象の analysis_*.txt を Read tool で全文開く（深掘り N0〜N12）")
  if [ -f "$PLAN_A" ]; then
    good_n=$(awk '/良い点/{f=1;next} /問題点/{f=0} f&&/\$/{c++} END{print c+0}' "$PLAN_A")
    prob_n=$(awk '/問題点/{f=1;next} /STEP2/{f=0} f&&/\$/{c++} END{print c+0}' "$PLAN_A")
    grep -q "最も黒字" "$PLAN_A" || gaps+=("STEP1-1 に『最も黒字の条件』を1行（攻め案の種・STEP1-1 必須）")
    [ "${good_n:-0}" -ge 3 ] || gaps+=("STEP1-1 良い点が ${good_n:-0} 件＝3件以上にする（各 net\$/件数/条件）")
    [ "${prob_n:-0}" -ge 3 ] || gaps+=("STEP1-2 問題点が ${prob_n:-0} 件＝3件以上にする（金額の大きい順・各 net\$/件数/条件）")
  else
    gaps+=("$PLAN_A が無い＝STEP1 観察を書く（### 良い点 3つ以上[各\$]・『最も黒字』1行・### 問題点 3つ以上[各\$・金額順]）")
  fi
  if [ ${#gaps[@]} -gt 0 ]; then
    echo "🔒 [probe前ゲートA] probe を走らせる前に『前回データ全文読了 ＋ STEP1 観察』を済ませてください（2026-06-28 まこさん承認・今日の隙間=前回データ未読でprobe量産 を物理的に塞ぐ）。" >&2
    echo "" >&2
    for g in "${gaps[@]}"; do echo "  - $g" >&2; done
    echo "" >&2
    echo "→ 手順: ①対象の report_*.txt と analysis_*.txt を Read tool で全文開く（くまなく）②$PLAN_A に STEP1（良い点3+/最も黒字/問題点3+・各\$数字・憶測禁止）を書く ③probe 実行。中身の質は最後はまこさんの目。" >&2
    exit 2
  fi
  echo "⚠️ [疑似シミュの位置づけ] これは probe＝あたりを付ける専用の参考ツールです（2026-06-26 まこさん）。" >&2
  echo "   ・出た数値（θ・閾値・段数・AUC 等）を設計の固定値や採否の根拠にしない。" >&2
  echo "   ・採否は必ず実エンジン再走＋両窓 score.py の数字だけ（STRUCT_SL 近似 +\$895 が実エンジンで消失した轍）。" >&2
  echo "   ・設計の閾値/段数は実エンジンの学習窓で選定 or 分析の構造由来の a-priori にする（probe 値を焼かない）。" >&2
fi
exit 0
