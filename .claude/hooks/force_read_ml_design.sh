#!/usr/bin/env bash
# SessionStart hook: 必読の「警告・宣言義務」と、auto-load 対象外の小片だけを注入する。
# ⚠️ 2026-06-13 軽量化（まこさん承認）: cat_requirements.md と entry_fix_6axis_gate.md は
#    `.claude/rules/` 配下＝VSCode 拡張が毎セッション全文 auto-load する。ここで再 cat すると二重ロード。
#    ml_pipeline_execlog.md は旧8工程フロー＝廃止・参照のみ（cat_requirements §8.1）。
#    → フル cat は全廃し、ポインタ＋警告＋ auto-load されない analysis_playbook §3.1 のみ残す。
SDK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api"
GATE6="$SDK/.claude/rules/entry_fix_6axis_gate.md"
PLAYBOOK="$SDK/.claude/ratchet/analysis_playbook.md"

echo "=================================================="
echo "🔒 設計/実装の前チェック（要件・6軸ゲートは rules/ で auto-load 済＝ここでは再掲しない）"
echo "=================================================="
echo ""
echo "⚠️ 全設計/実装は cat_requirements.md §4.6 ハード制約（H1〜H16）に1項目ずつ照合してから着手する（要件は auto-load 済）。"
echo "⚠️ Entry 関連の設計/実装を出す前に、必ず「軸 N を閉じる・entry_fix_6axis_gate §18.5 逐語『…』(file:line)」と宣言する。"
echo "   引用なし・軸に紐づかない手は却下対象。6軸すべて ✅(証跡つき) まで『Entry 修正完了』禁止。（6軸ゲートは auto-load 済）"
[ -f "$GATE6" ] || echo "❌ 欠落: $GATE6"
echo ""
echo "--- analysis_playbook.md §3.1（保管運用ルール・ratchet直下を散らかさない・成果物のE番号命名・auto-load 対象外なのでここで注入）---"
if [ -f "$PLAYBOOK" ]; then
  awk '/^### §3\.1/{f=1} f&&/^## /{exit} f{print}' "$PLAYBOOK"
else
  echo "❌ 欠落: $PLAYBOOK"
fi
echo ""
echo "⚠️ 実験の出力CSV/記録は E番号(ledger の実験番号)を名前に入れる → report も自動で E番号付き。過去実験の出力は results/priority_rebuild/ratchet/archive/ へ退避。直下=現役のみ。新実験前に前実験の出力を archive へ move（§3.1）。"
echo ""
