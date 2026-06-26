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
exit 0
