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
# 2026-06-13 まこさん指示: cat_requirements を必読から外す（セッション開始時に読んでもインプットされない実証）。
#   → just-in-time（設計書を書く瞬間に exchange_spec ★決済方法 + cat_requirements を強制）に移管＝require_spec_read_before_design.sh。
# adopted_strategies.md（採用台帳）追加: 2026-06-22 まこさん指示。器の現在値を「最新の1実験」でなく
#   「採用ポートフォリオの積み上げ」で見るため、goal_block を書く前に台帳を Read 強制（ゲート3 と対）。
REQUIRED=("WORKFLOW" "ledger.md" "adopted_strategies")
LABEL=("WORKFLOW.md(現在地)" "ledger.md(PDCA実験記録の正本)" "adopted_strategies.md(採用ポートフォリオ台帳)")

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
# 「戦略照合」(2026-06-12 まこさん指示): この議論/実験が §6.2 のどの Priority の特性
#   （狙う値動き・スタイル）× どのレバー（Entry 閾値/Exit 値/サイズ配分）の net 最大化かを1行で書く。
#   背景: CC が「LONG が柱になるか」に視点をすり替え §6.2（全 Priority をそれぞれ最適化）を外した事案。
#   「届く構成から逆算」を部品単体の桁に誤適用する穴は8見出しでは検出されないため追加。
# 「改善の経緯」(2026-06-26 まこさん指示): 対象戦略の直近イテレーション系譜を ledger から箇条書きで再構成し、
#   各 iter に「前提フラグ（nofloor ON/OFF 等・どの base の上か）」を必ず書く。最新1実験の局所結論を起点に
#   改善議論へ走る穴（cc_role §1.4 #4）を塞ぐ。背景: (A)DYING_CUT が nofloor OFF（base）に当てられていたのに、
#   本筋(a) は nofloor ON 前提だった対比を CC が見落とし「切る方向は頭打ち」を本筋に誤適用した事案（2026-06-26）。
#   ledger を Read tool で開いても流れを再構成しない＝開封チェックの穴を、アークの明示的な記述で物理化する。
MARKERS=("大目標" "器の現在値" "ギャップ" "候補" "天井" "選定" "3行ゲート" "届く構成" "戦略照合" "改善の経緯")
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
  echo "   戦略照合: この議論/実験が §6.2 のどの Priority の特性 × どのレバー（Entry/Exit/サイズ）の" >&2
  echo "   net 最大化かを1行で書く。器=全 Priority の合算であり、部品単体に \$1,900 の桁を要求して" >&2
  echo "   Priority 改善を切り捨てるのは誤適用（2026-06-12 LONG 柱すり替え事案）。" >&2
  echo "   改善の経緯: 対象戦略の直近イテレーション系譜を ledger から箇条書きで再構成し、各 iter に" >&2
  echo "   前提フラグ（nofloor ON/OFF 等・どの base の上か）を必ず書く。最新1実験の局所結論を起点に" >&2
  echo "   改善議論へ走らない（2026-06-26 (A)DYING_CUT を base=nofloor OFF に当てた前提を見落とした事案）。" >&2
  echo "" >&2
  echo "★次セッションの本筋・今セッションの確定・やってはいけないことは next_step.md（SessionStart で全文表示）が正本。" >&2
  echo "   それを起点に goal_block の候補/天井/戦略照合を書く（前セッション固有の handoff をここ/hook に焼き込まない＝古くなって誤誘導する・2026-06-13）。" >&2
  exit 2
fi

# --- 改善アーク 列ゲート（2026-06-26 まこさん指示）: 「改善の経緯」は 狙い(目的) だけでなく 内容・方法 も列に持つ ---
# 背景: 狙い(目的)だけだと過去 iter が「何をして（内容＝動かしたレバー/機構）・どう検証してなぜ不採用か（方法＝失敗の型）」が
#   見えず、同型の手を再提案する。2026-06-26 に「含み益キーの早切り Exit」を、(A)DYING_CUT/E35 iter10 が
#   勝ち玉刈りで不採用だった失敗の型を踏まずに検討しかけた。内容・方法を列で並べ再演を物理的に見えやすくする。
arc=$(awk '/^##[[:space:]]*改善の経緯/{f=1;next} /^## /{f=0} f' "$GOAL" 2>/dev/null)
arc_miss=()
printf '%s' "$arc" | grep -q "狙い" || arc_miss+=("狙い（目的＝ledger 方針引用）")
printf '%s' "$arc" | grep -q "内容" || arc_miss+=("内容（動かしたレバー/機構）")
printf '%s' "$arc" | grep -q "方法" || arc_miss+=("方法（どう検証・採否理由＝失敗の型）")
if [ ${#arc_miss[@]} -gt 0 ]; then
  echo "🔒 [改善アーク 列ゲート] goal_block「改善の経緯」は 狙い だけでなく 内容・方法 も列に持つ（2026-06-26 まこさん指示）。" >&2
  echo "不足列:" >&2
  for m in "${arc_miss[@]}"; do echo "  - $m" >&2; done
  echo "" >&2
  echo "理由: 狙い(目的)だけだと過去 iter の『何をして・どう検証して・なぜ不採用か（失敗の型）』が見えず、同型の手を再提案する（2026-06-26 含み益キー早切り Exit を DYING_CUT/iter10 の勝ち玉刈り型と気づかず検討しかけた事案）。" >&2
  exit 2
fi

# --- ゲート3: 器の現在値＝採用ポートフォリオの積み上げ照合（近視眼防止・2026-06-22 まこさん指示） ---
# 採用台帳のマーカー <!-- PORTFOLIO_CHECK: BASE_MAX=... ; PILLARS=...,... --> を読み、
# goal_block の「## 器の現在値」セクションに「最大 deployable 地面」＋採用柱 計2本以上が
# 書かれているか照合する。最新の1実験だけを現在値にする近視眼（2026-06-22 E36 単独事案）を物理的に弾く。
# hook に戦略名を焼かず台帳マーカーから動的に読む＝採用が変われば台帳1行更新で hook が自動追従。
ADOPTED="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/adopted_strategies.md"
marker=$(grep -m1 "PORTFOLIO_CHECK:" "$ADOPTED" 2>/dev/null)
base_max=$(printf '%s' "$marker" | sed -n 's/.*BASE_MAX=\([A-Za-z0-9]*\).*/\1/p')
pillars=$(printf '%s' "$marker" | sed -n 's/.*PILLARS=\([A-Za-z0-9,]*\).*/\1/p')

if [ -n "$base_max" ] && [ -n "$pillars" ]; then
  # goal_block の「## 器の現在値」見出し配下（次の「## 」まで）を抽出
  section=$(awk '/^##[[:space:]]*器の現在値/{f=1;next} /^## /{f=0} f' "$GOAL" 2>/dev/null)

  miss_base=0
  printf '%s' "$section" | grep -q "$base_max" || miss_base=1

  count=0
  IFS=',' read -ra arr <<< "$pillars"
  for p in "${arr[@]}"; do
    [ -n "$p" ] && printf '%s' "$section" | grep -q "$p" && count=$((count+1))
  done

  if [ "$miss_base" -eq 1 ] || [ "$count" -lt 2 ]; then
    echo "🔒 [器の現在値ゲート] goal_block の「器の現在値」が採用ポートフォリオの積み上げになっていません。" >&2
    echo "近視眼防止（2026-06-22 E36 単独事案）: 最新の1実験だけを現在値にするのを物理的に止めます。" >&2
    echo "" >&2
    echo "必須（採用台帳 adopted_strategies.md のマーカーが正・hook はそれに追従）:" >&2
    echo "  - 最大 deployable 地面「$base_max」を器の現在値に必ず書く" >&2
    echo "  - 採用柱（$pillars のうち）を計2本以上書く（現在 $count 本）" >&2
    [ "$miss_base" -eq 1 ] && echo "  → 不足: 最大地面「$base_max」が器の現在値に無い" >&2
    [ "$count" -lt 2 ] && echo "  → 不足: 採用柱が $count 本（2本以上必要）" >&2
    echo "" >&2
    echo "→ adopted_strategies.md（採用台帳）を見て、器の現在値を「積み上げ」で書き直してください。" >&2
    echo "   器の現在値は最新の1実験でなく、今ポートフォリオに入っている全採用戦略の合算で見る。" >&2
    exit 2
  fi
fi
exit 0
