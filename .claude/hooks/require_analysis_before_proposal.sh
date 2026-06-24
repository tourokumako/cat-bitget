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

# 対象＝改善提案・設計の成果物（acceptance.md / *_design.md）。それ以外は通す（最小強制）。
is_target=0
case "$BASE" in
  acceptance.md|*_design.md) is_target=1 ;;
esac
[ "$is_target" -eq 0 ] && exit 0

GUIDE="→ 分析フェーズの手順: ①対象戦略の ledger 経緯＋関連 report_/analysis_（base＋直近実験）＋分析KB(trade_analysis_methods_kb)＋analysis_playbook §2 を Read tool で開く ②$BLOCK に8見出しを数字つきで埋める ③改善提案($BASE)を書く"

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

# ── B. 完了ゲート（分析ブロックの必須8見出し＝穴3を塞ぐ・採点非依存＝穴1）──
if [ ! -f "$BLOCK" ]; then
  echo "🔒 [分析フェーズ 完了ゲート] 分析ブロックがありません: $BLOCK" >&2
  echo "改善提案の前に、分析ブロックに下記8見出しを数字つきで埋めてください（採点の有無に関わらず必須＝穴1）。" >&2
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
if [ -n "$miss" ]; then
  echo "🔒 [分析フェーズ 完了ゲート] 分析ブロック（$BLOCK）に必須見出しが未記入（穴3・2026-06-24）:" >&2
  printf "%b\n" "$miss" >&2
  echo "" >&2
  echo "中身の数字は report_/analysis_ から引く（思いつき禁止）。8見出しを埋めてから改善提案を書いてください。" >&2
  echo "限界: hook は『見出しが埋まり E番号を引用したか』までを守る。数字の正しさは最後はまこさんの目。" >&2
  exit 2
fi
exit 0
