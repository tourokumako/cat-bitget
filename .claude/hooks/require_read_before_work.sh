#!/bin/bash
# require_read_before_work.sh — PreToolUse on Bash|Edit|Write|MultiEdit
# ゲート1（読了強制）: 必読を Read tool で実際に開く（record_read.sh が read_log に記録）まで、
#   作業ツール(Bash/Edit/Write/MultiEdit)を exit 2 で物理 block する。
#   目的: 新セッションで CC が必読を読まずに動く（読んだふり・勝手な値・暴走）を仕組みで防ぐ。
#   まこさん指示 2026-06-10:「読まないと手が動かない仕組みにしてほしい」。
# ゲート2（目標逆算ゲート）: WORKFLOW Step 0 ④ の目標逆算ブロック（5行+3行ゲート）を
#   .claude/state/goal_block.md に Write するまで、作業ツールを exit 2 で物理 block する。
#   目的: 結論先行（次タスクを読んで後付けの導出を書く）・届かない候補の単体選定・
#   導出を出さず作業開始する違反を仕組みで防ぐ。まこさん指示 2026-06-12:
#   「決まった項目を正確に実行できる状態にしろ」。goal_block.md 自体への Write/Edit のみ許可。
# CC の決意では止まらない（session_log_20260609 §9）→ 物理強制。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
LOG="$STATE_DIR/read_log.txt"
GOAL="$STATE_DIR/goal_block.md"

input=$(cat)

# 必読3本（2026-06-12 まこさん指示「読ませても効果の無い文書は削除」で 7本→3本にスリム化）
#   外した4本と理由（読了強制に効果なしの実証・内容は道具/hook に物理化済み or 重複）:
#   - lessons_active(4118行・最大の浪費): 教訓は hook/ツールで物理強制する方針が正(L-236)・読んでも再演の実証多数。必要時 grep 参照
#   - analysis_playbook: 分析手順は report.py A〜L / analyze.py N1〜N6 / precheck.py P0〜P3 + pdca_gate に物理化済み。
#     E21 のしょぼい分析は再読ゲート通過後に起きた＝読ませても効かない実証（採点前再読ゲートも同時撤去）
#   - session_log: WORKFLOW 現在地5行 + ledger と重複（時短④でスリム化済み）
#   - strat_v9ml_design: 設計作業の時だけ読む(Layer 2)。設計書照合は複数 CC チェック(cc_role §1.4.6.3)が物理担当
REQUIRED=("cat_requirements" "WORKFLOW" "ledger.md")
LABEL=("cat_requirements.md(要件・H制約)" "WORKFLOW.md(現在地)" "ledger.md(PDCA実験記録の正本)")

missing=()
for idx in "${!REQUIRED[@]}"; do
  if ! grep -q "${REQUIRED[$idx]}" "$LOG" 2>/dev/null; then
    missing+=("${LABEL[$idx]}")
  fi
done

if [ ${#missing[@]} -gt 0 ]; then
  echo "🔒 [読了強制ゲート] 必読を Read tool で実際に読むまで Bash/Edit/Write は使えません。" >&2
  echo "未読（Read tool で開いていない）:" >&2
  for m in "${missing[@]}"; do echo "  - $m" >&2; done
  echo "" >&2
  echo "→ 上記を Read tool で開いてから作業してください。表示されているだけ/grep だけは読了になりません（読んだふり防止・まこさん指示・session_log §9）。" >&2
  exit 2
fi

# --- ゲート2: 目標逆算ブロック（WORKFLOW Step 0 ④・2026-06-12 まこさん指示で物理化） ---

# goal_block.md 自体への Write/Edit は許可（これを書けないとゲートを解除できないため）
fp=$(printf '%s' "$input" | python3 -c "import sys,json
try:
    d=json.load(sys.stdin)
    print(d.get('tool_input',{}).get('file_path',''))
except Exception:
    print('')" 2>/dev/null)
if [ "$fp" = "$GOAL" ]; then
  exit 0
fi

# 必須見出し（形式の機械チェック・中身の質はまこさんの30秒チェックが担保）
MARKERS=("大目標" "器の現在値" "ギャップ" "候補" "天井" "選定" "3行ゲート" "届く構成")
missing2=()
for m in "${MARKERS[@]}"; do
  if ! grep -q "$m" "$GOAL" 2>/dev/null; then
    missing2+=("$m")
  fi
done

if [ ${#missing2[@]} -gt 0 ]; then
  echo "🔒 [目標逆算ゲート] WORKFLOW Step 0 ④ の目標逆算ブロックを書くまで Bash/Edit/Write は使えません。" >&2
  echo "手順: ① $GOAL に Write（5行+3行ゲート・この Write だけは許可）② 同内容をチャットに出す ③ まこさんの GO 後に作業。" >&2
  echo "未記入の必須見出し:" >&2
  for m in "${missing2[@]}"; do echo "  - $m" >&2; done
  echo "" >&2
  echo "⚠️ 導出の向き: \$1,900 に届く構成を先に出し、今回ミッションをその部品として位置づける。" >&2
  echo "   各候補に天井の暗算を書く。桁が届かない候補を単体ミッションとして選定しない（Step 0 ④-4）。" >&2
  echo "   結論（WORKFLOW 次タスク）を読んでから後付けで導出を書くのは違反（2026-06-12 違反事案）。" >&2
  exit 2
fi
exit 0
