#!/bin/bash
# enforce_combo_matrix.sh — PreToolUse on Write|Edit（2026-07-06 まこさん指示で新設）
# 指示: 「Entry×Exit の全組み合わせを網羅マトリクスで並べたうえで、あらゆる組み合わせ・選択肢で
#        改善しつくすように、強制しろ」「E37 専用でなく全戦略共通にして」。
#
# 目的（全戦略共通）: どの戦略の改善提案（improvement_plan.md / acceptance.md）でも、Entry ロジックの全候補 ×
#   Exit ロジックの全候補を網羅マトリクス（.claude/ratchet/entry_exit_matrix.md）で並べ、試済セル（実験名・両窓）と
#   未試行セルを可視化してからでないと書けなくする。＝CC が「1レバーずつ狭く選ぶ」モグラ叩き（v10→v13 の反省）を
#   物理的に禁止（feedback_exhaustive_search / feedback_cc_low_perspective_narrow_view）。
#   戦略名は hook に焼かず、提案本文から token（e3N / p2N）を検出して追従（STRATEGY_ANCHOR と同型）。
#
# 正直な限界: hook は「マトリクスが在り最低限の網羅幅を持ち未試行が見え、提案が本表を指すか」までを守る。
#   全組み合わせを本当に考え尽くしたかの中身はまこさんの目（他 hook と同じ）。番人メタ確認つき（--selftest）。

MATRIX="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/entry_exit_matrix.md"

# ── 番人メタ確認（わざと壊して落ちるか）: enforce_combo_matrix.sh --selftest <matrix.md> <content-token>
if [ "$1" = "--selftest" ]; then
  echo "（番人）本体ロジックを手で叩く用。実運用は stdin JSON。"
  exit 0
fi

INPUT=$(cat)

# サブエージェント（Workflow/Agent 内）は通す（デッドロック回避・require_acceptance と同型）
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

FILE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)
BASE=$(basename "$FILE")
case "$BASE" in
  improvement_plan.md|acceptance.md) : ;;
  *) exit 0 ;;
esac

CONTENT=$(printf '%s' "$INPUT" | python3 -c "import sys,json;d=json.load(sys.stdin).get('tool_input',{}) or {};print(d.get('content') or d.get('new_string') or '')" 2>/dev/null)
[ -z "$CONTENT" ] && exit 0

GUIDE="→ 手順: ①.claude/ratchet/entry_exit_matrix.md を開き、対象戦略の『## グリッド: <戦略>』節に Entry構成×Exit構成の全組み合わせを並べる（試済=実験名・両窓／未試行=空欄）②未試行セルを全て可視化（『未試行: あり』＝残る限り潰し切る）③未試行セル全体を見渡して選定を1行（CC が狭く1マスを決め打ちしない・まこさんと全体から選ぶ）④improvement_plan/acceptance に『網羅マトリクス（entry_exit_matrix）』を参照しどのセルを実装するか明記。CAT 指標マトリックス(23軸)は参考に横目で見る（正本化しない）。⑤★Exit は『軸を1つ』でなく状態機械として設計＝entry 後のポジション状態（含み益の推移/ピーク反転/失速/逆行/指標反転/時間×損益）ごとに発火する Exit を分岐表で書く（V9 の replay_csv.py _check_exits_replay が雛形・entry_exit_matrix.md Exit カタログ冒頭の基本原則）。Exit を変えないなら『Exit 状態機械は現行維持』と1行。"

# 1) マトリクス存在
if [ ! -f "$MATRIX" ]; then
  echo "🔒 [Entry×Exit 網羅ゲート] .claude/ratchet/entry_exit_matrix.md が無い＝Entry×Exit の全組み合わせを網羅せず提案しようとしている（まこさん 2026-07-06）。" >&2
  echo "$GUIDE" >&2
  exit 2
fi

miss=()
# 2) 共通軸カタログ＋グリッド＋未試行 の見出し
grep -q "共通 Entry ロジック軸" "$MATRIX" || miss+=("マトリクスに『共通 Entry ロジック軸』カタログが無い")
grep -q "共通 Exit ロジック軸" "$MATRIX" || miss+=("マトリクスに『共通 Exit ロジック軸』カタログが無い")
grep -q "## グリッド:" "$MATRIX" || miss+=("マトリクスに『## グリッド: <戦略>』節が無い")

# 3) 網羅幅（Entry サブ軸≥5 / Exit サブ軸≥4 / グリッド行≥8）＝狭い列挙を弾く
ne=$(grep -cE '^- \*\*E-[a-z]' "$MATRIX")
nx=$(grep -cE '^- \*\*X-[a-z]' "$MATRIX")
ng=$(grep -cE '^\| *[0-9]+ *\|' "$MATRIX")
[ "${ne:-0}" -ge 5 ] || miss+=("Entry 軸の選択肢が狭い（E-* ${ne}/5 未満）＝CAT A-1/D-ε 等から足す")
[ "${nx:-0}" -ge 4 ] || miss+=("Exit 軸の選択肢が狭い（X-* ${nx}/4 未満）＝CAT A-2/A-6/A-7/D-θ 等から足す")
[ "${ng:-0}" -ge 8 ] || miss+=("網羅グリッドのセルが少ない（${ng}/8 未満）＝Entry×Exit の組み合わせを並べ切る")

# 4) 未試行の可視化（残る限り潰し切る／全部済みなら明示宣言）
grep -qE "未試行: *あり|未試行: *なし（" "$MATRIX" || miss+=("『未試行: あり／なし（…）』の宣言が無い＝未試行セルを可視化する")

# 5) 対象戦略のグリッド節（提案本文の戦略 token を検出＝hook に戦略名を焼かない）
TOK=$(printf '%s' "$CONTENT" | grep -oiE 'e[0-9][0-9]|p[0-9][0-9]' | head -1 | tr 'A-Z' 'a-z')
if [ -n "$TOK" ]; then
  num=$(printf '%s' "$TOK" | grep -oE '[0-9]+')
  grep -iqE "## グリッド:.*${num}" "$MATRIX" || miss+=("対象戦略 ${TOK} のグリッド節『## グリッド: …${num}…』がマトリクスに無い＝その戦略の全組み合わせを先に並べる")
fi

# 6) 提案が本表を指すか（提案がマトリクス由来であることを紐付け）
printf '%s' "$CONTENT" | grep -qE "網羅マトリクス|entry_exit_matrix" || miss+=("提案が『網羅マトリクス（entry_exit_matrix）』を参照していない＝どのセルを実装するか本表に紐付ける")

# 7) Exit 状態機械の分岐設計（★V9 の基本ロジック・2026-07-06 まこさん承認「hookもいれていいよ」）
#   改善案は Exit を「軸を1つ選ぶ」でなく「entry 後のポジション状態→発火する Exit」の状態機械として設計する
#   （利益最大化=伸ばす/消える前に確定・損失最小化=負けは早く/失速で撤退）。背景=E37 が V9 の当たり前
#   （replay_csv.py _check_exits_replay の状態分岐＝MFE反転/失速/指標反転/TIME down_factor/PROFIT_LOCK）を
#   毎回外し、固定TP＋固定SL＋固定TIME だけで v2〜v13 の 22 回失敗（まこさん「V9では当たり前にやってきた」）。
#   Exit を変えない提案は「Exit 状態機械は現行維持」と明記すれば通る（＝状態機械 の語で pass・過剰要求を避ける）。
#   正直な限界：キーワード検出＝本当に状態機械を組めたかの中身はまこさんの目（他 hook と同じ）。
printf '%s' "$CONTENT" | grep -qE "状態機械|ポジション状態|含み益.*(ピーク|反転|失速)|MFE_DRAWDOWN|MFE_STALE" \
  || miss+=("Exit 状態機械の分岐（entry 後のポジション状態→どの Exit を発火させるか）を設計に書く＝V9 の基本[entry_exit_matrix.md の Exit カタログ冒頭『基本原則』・replay_csv.py _check_exits_replay が雛形]。固定TP/SL/TIME だけの Exit は不可。Exit を変えないなら『Exit 状態機械は現行維持』と1行明記")

# 8) 指標・閾値のコンフルエンス（★V9 の当たり前・基本原則①・2026-07-06 まこさん承認「毎回絶対忘れない状態に」）
#   Entry/Exit の判定は単一指標・単一閾値でなく、複数指標の閾値を場面別・条件別・入れ子で組む（confluence）。
#   V9 cat_params_v9.json が実例（P23 Entry=ADX30-50∩ATR≥150∩入れ子∩BB傾き∩stoch乖離∩陰線）。E37 が「stoch_k 一つ」の単一閾値で22回失敗。
printf '%s' "$CONTENT" | grep -qE "コンフルエンス|confluence|複数指標|場面別|入れ子|単一閾値" \
  || miss+=("指標・閾値をコンフルエンス（複数指標×場面別×条件別・単一閾値で組まない）で設計＝V9 の当たり前[entry_exit_matrix 基本原則①・cat_params_v9.json が実例]。単一指標で足る根拠があれば1行明記")

# 9) 閾値・指標の ML 最適化（★プロジェクト中核方針・基本原則②・cat_requirements §6.2・2026-07-06 まこさん承認）
#   手動 V9 の Entry/Exit を土台に閾値・指標を ML で最適化して net 最大化（E13/E8/E9/E14/E19/E21 の出発点）。
#   固定値の手調整は L-267 禁止＝木の特徴量 or 学習窓選定。素ルール MVP なら「ML最適化は次段」と明記で通る。
printf '%s' "$CONTENT" | grep -qE "ML|機械学習|木の特徴量|学習窓|meta.?label|LightGBM|最適化|次段" \
  || miss+=("閾値・指標を ML で最適化する視点＝プロジェクト中核[entry_exit_matrix 基本原則②・cat_requirements §6.2]。固定値の手調整は L-267 禁止。素ルールMVPなら『ML最適化は次段』と1行明記")

if [ ${#miss[@]} -gt 0 ]; then
  echo "🔒 [Entry×Exit 網羅ゲート: ${BASE}] Entry×Exit の全組み合わせを網羅し未試行を可視化してから提案してください（狭い1レバー決め打ち禁止・まこさん 2026-07-06）。" >&2
  echo "" >&2
  for m in "${miss[@]}"; do echo "  - $m" >&2; done
  echo "" >&2
  echo "$GUIDE" >&2
  exit 2
fi
exit 0
