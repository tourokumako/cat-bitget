#!/bin/bash
# require_analysis_before_proposal.sh — PreToolUse on Write|Edit（2026-06-24 まこさん承認で新設）
# 目的: 改善提案・設計（acceptance.md / *_design.md）を書く瞬間に「分析フェーズ」を物理強制する。
#   既存の pdca_gate は score.py で採点した後にしか分析を強制しない＝採点しない既存データ分析には
#   強制が一切起動しない（穴1）。本 hook は「提案を書く瞬間」をトリガにし、採点の有無に依存しない。
#   他フェーズ（設計=require_spec_read／実装=require_acceptance／実行=require_precheck）と同じ just-in-time。
#
# 塞ぐ3穴（2026-06-24 事案＝CC が経緯/関連データ/分析KB を読まず適当な分析・提案を出し、まこさんが3回是正）:
#   穴1: 採点しない既存データ分析には強制が一切起動しない → 提案を書く瞬間にトリガ（採点非依存）
#   穴2: 読了ゲートは「開いたか」だけ＝中身/関連データを飛ばしても通る → 分析KB/report/analysis を read_log で確認
#   穴3: 較正・fat-tail・経緯照合が CC 判断頼み（☐のまま）→ 分析ブロックの必須8見出しで物理化
#
# 正直な限界: チャットへの適当コメントは hook で止められない（ツール呼び出しでない）。だが改善提案を
#   正式に出す（acceptance/design を書く）瞬間には必ず止まる。中身の数字が正しいかは最後はまこさんの目。
#   過剰強制回避のため §2.0 の19項目全部でなく、今回すり抜けた3穴に対応する最小8項目に絞る。

STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
LOG="$STATE/read_log.txt"
BLOCK="$STATE/analysis_block.md"

INPUT=$(cat)

# サブエージェント（Workflow/Agent 内）は通す（デッドロック回避・require_acceptance と同型）
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

FILE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)
BASE=$(basename "$FILE")

# 対象＝分析ブロック（分析の着手）＋改善提案・設計の成果物（提案）。それ以外は通す（最小強制）。
#   A 着手ゲート（分析KB/playbook/対象 report・analysis 読了）は「分析を始める瞬間＝analysis_block.md を書く時」に効かせる
#     （2026-06-27 まこさん指摘＝分析KB読了は分析の前提なので、分析の後に出す提案 acceptance を書く瞬間では順序が遅い）。
#   B 完了ゲート（9見出し）は提案 acceptance/design を書く瞬間に効かせる（A も保険で再掲＝二重に守る）。
is_block=0; is_target=0
case "$BASE" in
  analysis_block.md) is_block=1 ;;
  acceptance.md|*_design.md) is_target=1 ;;
esac
[ "$is_block" -eq 0 ] && [ "$is_target" -eq 0 ] && exit 0

GUIDE="→ 分析フェーズの手順: ①対象戦略の ledger 経緯＋関連 report_/analysis_（base＋直近実験）＋分析KB(trade_analysis_methods_kb)＋analysis_playbook §2 を Read tool で開く ②$BLOCK に10見出しを数字つきで埋める（⑨巻き込み検証＝切る/Exit 系は勝ち玉/fat-tail への当たり量を数字で／⑩戦略整合＝戦術が対象戦略の役割[デイトレ/スキャル/トレンド・局面]に妥当か）③改善提案($BASE)を書く"

# ── A. 着手ゲート（Read 証跡＝穴2を塞ぐ・record_read.sh が read_log に記録）──
amiss=()
grep -q "trade_analysis_methods_kb" "$LOG" 2>/dev/null || amiss+=("trade_analysis_methods_kb.md（分析KB＝前後比較/fat-tail/MAE/較正/3分類 の型）")
grep -q "analysis_playbook" "$LOG" 2>/dev/null || amiss+=("analysis_playbook.md（分析バッテリー §2）")
grep -q "/report_" "$LOG" 2>/dev/null || amiss+=("対象の report_*.txt（結果一覧 A〜L＝base＋直近実験の両方）")
grep -q "/analysis_" "$LOG" 2>/dev/null || amiss+=("対象の analysis_*.txt（深掘り N1〜N12）")
if [ ${#amiss[@]} -gt 0 ]; then
  echo "🔒 [分析フェーズ 着手ゲート] 改善提案（$BASE）の前に、分析の必読を Read してください（穴2＝中身/関連データを読まず提案した事案・2026-06-24）。" >&2
  echo "" >&2
  echo "未読（Read tool で開いていない）:" >&2
  for m in "${amiss[@]}"; do echo "  - $m" >&2; done
  echo "" >&2
  echo "$GUIDE" >&2
  exit 2
fi

# analysis_block.md を書く瞬間は A 着手ゲートのみで通す（B 完了＝分析ブロック自身なのでスキップ・2026-06-27）
[ "$is_block" -eq 1 ] && exit 0

# ── B. 完了ゲート（分析ブロックの必須9見出し＝穴3を塞ぐ・採点非依存＝穴1）──
if [ ! -f "$BLOCK" ]; then
  echo "🔒 [分析フェーズ 完了ゲート] 分析ブロックがありません: $BLOCK" >&2
  echo "改善提案の前に、分析ブロックに下記10見出しを数字つきで埋めてください（採点の有無に関わらず必須＝穴1）。" >&2
  echo "$GUIDE" >&2
  exit 2
fi
miss=""
grep -q "前後比較"   "$BLOCK" || miss="$miss\n  - ①前後比較（前回ベースライン vs 今回の 件数/net/avg/勝率・degenerate 点検・KB §0）"
grep -q "両窓"       "$BLOCK" || miss="$miss\n  - ②両窓（学習窓と採点窓の両方で再現するか・片窓だけ=過剰適合・H8/L-289）"
grep -q "fat-tail"   "$BLOCK" || miss="$miss\n  - ③fat-tail（上位数件を除いても黒字が残るか・少数大勝ち依存・KB §2）"
grep -q "MAE"        "$BLOCK" || miss="$miss\n  - ④MAE/MFE 較正（勝ち玉 MAE 80%ile=SL基準／MFE中央60-70%=TP基準・KB §3）"
grep -q "予測確率"   "$BLOCK" || miss="$miss\n  - ⑤較正（判別器の予測確率×実net・逆較正は致命・判別器なしなら『該当なし』と明記・KB §5）"
grep -q "3分類"      "$BLOCK" || miss="$miss\n  - ⑥原因3分類（戦略欠陥／執行／regime依存・直す前に1つ・§2.4）"
grep -q "問5"        "$BLOCK" || miss="$miss\n  - ⑦5つの問い（問0前後比較〜問5次仮説・数字でなく構造で）"
grep -q "経緯照合"   "$BLOCK" || miss="$miss\n  - ⑧経緯照合（過去 iteration で潰した手の再演でないか）"
# ⑧は飛ばし読み防止のため過去実験の E番号/iter番号 の引用を必須にする
if grep -q "経緯照合" "$BLOCK"; then
  grep -Eq "E[0-9]|iter[0-9]|iteration-[0-9]" "$BLOCK" || miss="$miss\n  - ⑧経緯照合に過去実験の E番号/iter番号 引用がありません（飛ばし読み防止＝直近の採用 iteration を引用せよ）"
fi
# ⑨巻き込み検証（2026-06-26 まこさん指示・本丸）: 切る/早切り/Exit 系レバーは、そのルールが勝ち玉（特に fat-tail）に
#   当たる量を必ず数字で出す。背景: 2026-06-26 に時間切れ損玉だけを切り出して「取り逃し +$2,624 改善余地」と
#   結論しかけたが、同じ含み益シグナルが勝ち玉に大量に当たる（MFE≥$5 で勝ち282玉 +$3,401 を巻き込む）ことを
#   突き合わせていなかった＝損玉だけ見て天井を語る分析手法の欠陥（iter10/DYING_CUT 再演）。Exit/切る レバーでない
#   提案は「該当なし（Exit/切る レバーでない）」と1行明記すれば可（⑤較正と同型）。
grep -q "巻き込み" "$BLOCK" || miss="$miss\n  - ⑨巻き込み検証（切る/早切り/Exit 系レバーは、そのルールが勝ち玉・fat-tail に当たる量を数字で。損玉だけ見て天井を語らない＝2026-06-26 取り逃し誤推定事案。Exit/切る でないなら『該当なし』と明記）"
# ⑩戦略整合（2026-06-27 まこさん提案）: 改善レバー＝戦術が対象戦略の役割（局面・デイトレ/スキャル/トレンド型）に妥当か。
#   背景: E36（デイトレ型レンジ柱）に早期固定TP＝スキャル化を当てようとした戦略ミスマッチ（スキャルは E37 の領域）。
#   戦術が戦略の役割を壊す提案を分析の段で物理的に止める。cat_requirements §1.2.1 全体戦略と照合。
grep -q "戦略整合" "$BLOCK" || miss="$miss\n  - ⑩戦略整合（改善レバー＝戦術が対象戦略の役割[局面・デイトレ/スキャル/トレンド型]に妥当か・ミスマッチでないか・cat_requirements §1.2.1）"

# ── 改善案生成ルール STEP3/3.5/4（2026-06-28 まこさん承認・improvement_plan.md・しょぼさ/近視眼/消去法 を封じる）──
#   STEP1(観察)/STEP2(要因) は probe前ゲートA(require_probe_naming.sh)で先に強制済。ここでは収束側を強制。
PLAN="$STATE/improvement_plan.md"
if [ ! -f "$PLAN" ]; then
  miss="$miss\n  - improvement_plan.md が無い（STEP1〜4＝改善案生成ルールを埋める・probe前ゲートAで STEP1 は強制済）"
else
  # STEP3 タグ付け＆重なり（軸B=N10両窓再現の分離指標を必ず使う＝『知ってる犯人だけ追う近視眼』封じ＝2026-06-28 事案の核）
  grep -q "STEP3"           "$PLAN" || miss="$miss\n  - STEP3 タグ付け＆重なり（軸A出血容疑＋軸B=分離指標 を全負け玉にタグ→クロス集計）"
  grep -Eq "分離指標|N10"   "$PLAN" || miss="$miss\n  - STEP3 軸B＝分離指標（N10 両窓再現・データが指した軸を必ずタグに含む＝近視眼封じ）"
  grep -q "重なり"          "$PLAN" || miss="$miss\n  - STEP3 重なり判定の結論（1点突き か / 別問題で金額最大優先 か）"
  # STEP3.5 発散（切り口5つ以上・各に出典）＝無難な1案への早期収束封じ
  grep -Eq "STEP3.5|発散"   "$PLAN" || miss="$miss\n  - STEP3.5 発散（改善の切り口5つ以上・各に N番号出典・この段では判定しない）"
  kiri=$(awk '/STEP3.5|発散/{f=1;next} /STEP4|収束/{f=0} f&&/出典/{c++} END{print c+0}' "$PLAN")
  [ "${kiri:-0}" -ge 5 ] || miss="$miss\n  - STEP3.5 切り口が ${kiri:-0} 件（各行に『出典: N番号』を付けて5つ以上＝発散）"
  # STEP4 収束（3案＝守り/攻め/構造・各に 玉数/net学習窓/犠牲）＝守りの消去案だけへの逃げ封じ
  grep -q "守り"           "$PLAN" || miss="$miss\n  - STEP4 ①守り（負け縮小）"
  grep -q "攻め"           "$PLAN" || miss="$miss\n  - STEP4 ②攻め（STEP1-1 の最も黒字の条件を増産）"
  grep -q "構造"           "$PLAN" || miss="$miss\n  - STEP4 ③構造（add ラダー等 玉の構成ロジックを引き直す）"
  grep -q "玉数"           "$PLAN" || miss="$miss\n  - STEP4 各案に〔玉数増減〕（件数が増えるか減るか）"
  grep -q "学習窓" "$PLAN" || miss="$miss\n  - STEP4 各案に〔net増減(学習窓)〕（採点窓を見て決めない＝L-267・『学習窓』の語を明記）"
  grep -q "犠牲"           "$PLAN" || miss="$miss\n  - STEP4 各案に〔何を犠牲にするか〕（トレードオフ1行）"
  # ⛔ 禁止形式: 「閾値 X→Y」「○帯を除外」＝分離指標を木に渡す形に直す（L-267・生成段階で阻止）
  if grep -Eq "閾値.*→|→[[:space:]]*[0-9.]+(%|$|[[:space:]])|帯.*除外|を除外" "$PLAN"; then
    miss="$miss\n  - ⛔禁止形式（『閾値 X→Y』『○帯を除外』）を検出＝線引きはモデルに学習させる＝分離指標を木(LightGBM)に特徴量として渡す形で書き直す（L-267）"
  fi
fi

if [ -n "$miss" ]; then
  echo "🔒 [分析フェーズ 完了ゲート] 分析ブロック（$BLOCK）に必須見出しが未記入（穴3・2026-06-24）:" >&2
  printf "%b\n" "$miss" >&2
  echo "" >&2
  echo "中身の数字は report_/analysis_ から引く（思いつき禁止）。8見出しを埋めてから改善提案を書いてください。" >&2
  echo "限界: hook は『見出しが埋まり E番号を引用したか』までを守る。数字の正しさは最後はまこさんの目。" >&2
  exit 2
fi
exit 0
