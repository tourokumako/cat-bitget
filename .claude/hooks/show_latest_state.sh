#!/bin/bash
# show_latest_state.sh — SessionStart hook（現在地の機械表示・2026-06-12 まこさん指示で新設）
# 目的: 「最新の実装はどれか・最新の結果 CSV はどれか・計器はいつ更新されたか」を、
#   CC が ledger の文章から記憶・推測するのをやめ、毎セッション冒頭にファイルシステムの事実として出す。
#   背景: CC が E25 が最新標準・eval_engine が計器の正本であることを把握せず、古い E の CSV/実装を
#   読まずに提案した事案（2026-06-12）。最新がどれかは ls -t が知っている＝推測不要。

R="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api"
RATCHET="$R/results/priority_rebuild/ratchet"
SCRIPTS="$R/scripts/priority_rebuild"

echo "=== 設計の最重要前提（CC が毎回起動できず的外れになる・2026-06-12）==="
echo "  理想は Entry/Exit を一連の取引としてセットで net 最大化。分けるのは CC の都合で本来は不可分。"
echo "  ・メタラベリング = 今のラチェットの正体: 仮 Exit(TP/SL/TIME/失速)を固定 → その Exit に辿り着いて"
echo "    net+ になる Entry を二次モデル(prob)で厳選。Exit を変えるとラベルが変わり Entry 選別が変わる=セット。"
echo "  ・RL(PPO/DQN) = 理想形だが小データ過学習で土台後（設計書 §9）／ Seq2Seq = 現段階外。"
echo "  ・Exit 値を entry 時点の場面で決める型は不成立(E23 OOF 改善ゼロ)→ Exit 改善は「保有中判定」側(KB §11)。"
echo "  → 詳細: .claude/memory/entry_exit_relationship_kb.md §★（設計・分析の前に読む）"
echo ""
echo "=== 現在地（ファイルシステムの事実・記憶でなくこれを見る・2026-06-12）==="

echo "--- 計器の正本（改造禁止・H13）と更新日時 ---"
for f in eval_engine.py score.py; do
  if [ -f "$SCRIPTS/$f" ]; then
    ts=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$SCRIPTS/$f" 2>/dev/null)
    echo "  $f  ($ts)"
  fi
done

echo "--- 最新の実験スクリプト 上位7本（更新日時順・scripts/priority_rebuild/）---"
ls -t "$SCRIPTS"/strat_*.py "$SCRIPTS"/train_*.py "$SCRIPTS"/gen_*.py \
      "$SCRIPTS"/measure_*.py "$SCRIPTS"/*oracle*.py "$SCRIPTS"/compose_*.py \
      "$SCRIPTS"/size_*.py 2>/dev/null | head -7 | while read -r f; do
  ts=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$f" 2>/dev/null)
  echo "  $(basename "$f")  ($ts)"
done

echo "--- 最新の結果 CSV 上位7本（更新日時順・results/priority_rebuild/ratchet/・直下のみ）---"
ls -t "$RATCHET"/trades_*.csv 2>/dev/null | head -7 | while read -r f; do
  ts=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$f" 2>/dev/null)
  rows=$(($(wc -l < "$f" 2>/dev/null) - 1))
  echo "  $(basename "$f")  ($ts・${rows}行)"
done

echo "--- 最新の分析レポート 上位5本（report_/analysis_/precheck_）---"
ls -t "$RATCHET"/report_*.txt "$RATCHET"/analysis_*.txt "$RATCHET"/precheck_*.txt 2>/dev/null | head -5 | while read -r f; do
  ts=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$f" 2>/dev/null)
  echo "  $(basename "$f")  ($ts)"
done

echo "→ 提案・設計の前に、該当 E の 結果 CSV＋実装＋計器(eval_engine) を Read し、数字を出典つき(パス＋日時)で引用（L-270）。"
echo "=================================================================="
exit 0
