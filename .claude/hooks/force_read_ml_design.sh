#!/usr/bin/env bash
# SessionStart hook: 必読文書を強制読込（L-242 読んだフリ防止）
# - 小さい正本（要件定義書 / execlog / 6軸ゲート）は全文 cat してコンテキストに強制注入
# - baseline（大）は Read tool 全文 + 機械的証跡を強制（cat は出力肥大のため非現実的）
SDK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api"
CATREQ="$SDK/.claude/rules/cat_requirements.md"
EXECLOG="$SDK/.claude/memory/ml_pipeline_execlog.md"
BASELINE="$SDK/.claude/memory/ml_pipeline_baseline_v1.md"
GATE6="$SDK/.claude/rules/entry_fix_6axis_gate.md"

echo "=================================================="
echo "🔒 必読文書 強制読込 (要件定義書 + ML設計書・L-242 読んだフリ防止)"
echo "=================================================="
echo ""
echo "--- ① cat_requirements.md（要件定義書・全文・最初に読む：立ち位置/業務/機能/非機能/制約14/運用ガイド）---"
if [ -f "$CATREQ" ]; then
  cat "$CATREQ"
else
  echo "❌ 欠落: $CATREQ"
fi
echo ""
echo "--- ② ml_pipeline_execlog.md（経緯ログ・全文・§2 現在地に「今どこ/次に何を」）---"
if [ -f "$EXECLOG" ]; then
  cat "$EXECLOG"
else
  echo "❌ 欠落: $EXECLOG"
fi
echo ""
echo "--- ③ ml_pipeline_baseline_v1.md（ML設計書・$(wc -l < "$BASELINE" 2>/dev/null || echo "?")行）---"
echo "⚠️ baseline は大きいため cat しない。**Read tool で全文読み、機械的証跡（wc -l + 0/25/50/75/100% 行引用 + 1行要約）を出すまで作業着手禁止**。"
echo "   auto-load / 「表示された=読んだ」で済ませるのは L-200 / L-204 / L-242 違反（読んだフリ＝類型G）。"
echo "   パス: $BASELINE"
echo ""
echo "--- ④ entry_fix_6axis_gate.md（Entry 修正 6軸ゲート・全文・§18.5 由来・Entry 作業はこれに照合）---"
if [ -f "$GATE6" ]; then
  cat "$GATE6"
else
  echo "❌ 欠落: $GATE6"
fi
echo ""
echo "⚠️ Entry 関連の設計/実装を出す前に、必ず「軸 N を閉じる・§18.5 逐語『…』(file:line)」と宣言する。"
echo "   引用なし・軸に紐づかない手は却下対象。6軸すべて ✅(証跡つき) まで『Entry 修正完了』禁止。"
echo ""
echo "⚠️ 全設計/実装は cat_requirements.md §4.6 ハード制約（H1〜H14）に1項目ずつ照合してから着手する。"
echo ""
echo "--- ⑤ analysis_playbook.md §3.1（保管運用ルール・ratchet直下を散らかさない・成果物のE番号命名）---"
PLAYBOOK="$SDK/.claude/ratchet/analysis_playbook.md"
if [ -f "$PLAYBOOK" ]; then
  awk '/^### §3\.1/{f=1} f&&/^## /{exit} f{print}' "$PLAYBOOK"
else
  echo "❌ 欠落: $PLAYBOOK"
fi
echo ""
echo "⚠️ 実験の出力CSV/記録は E番号(ledger の実験番号)を名前に入れる → report も自動で E番号付き。過去実験の出力は results/priority_rebuild/ratchet/archive/ へ退避。直下=現役のみ。新実験前に前実験の出力を archive へ move（§3.1）。"
echo ""
