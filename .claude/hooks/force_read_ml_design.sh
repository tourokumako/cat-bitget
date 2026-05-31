#!/usr/bin/env bash
# SessionStart hook: ML設計書2ファイルを強制読込（L-242 読んだフリ防止）
# - execlog（小・正本）は全文 cat してコンテキストに強制注入
# - baseline（大）は Read tool 全文 + 機械的証跡を強制（cat は出力肥大のため非現実的）
SDK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api"
EXECLOG="$SDK/.claude/memory/ml_pipeline_execlog.md"
BASELINE="$SDK/.claude/memory/ml_pipeline_baseline_v1.md"
GATE6="$SDK/.claude/rules/entry_fix_6axis_gate.md"

echo "=================================================="
echo "🔒 ML設計書 強制読込 (L-242 読んだフリ防止)"
echo "=================================================="
echo ""
echo "--- ① ml_pipeline_execlog.md（経緯ログ・全文・新セッション最初に読む正本）---"
if [ -f "$EXECLOG" ]; then
  cat "$EXECLOG"
else
  echo "❌ 欠落: $EXECLOG"
fi
echo ""
echo "--- ② ml_pipeline_baseline_v1.md（ML設計書・$(wc -l < "$BASELINE" 2>/dev/null || echo "?")行）---"
echo "⚠️ baseline は大きいため cat しない。**Read tool で全文読み、機械的証跡（wc -l + 0/25/50/75/100% 行引用 + 1行要約）を出すまで作業着手禁止**。"
echo "   auto-load / 「表示された=読んだ」で済ませるのは L-200 / L-204 / L-242 違反（読んだフリ＝類型G）。"
echo "   パス: $BASELINE"
echo ""
echo "--- ③ entry_fix_6axis_gate.md（Entry 修正 6軸ゲート・全文・§18.5 由来・Entry 作業はこれに照合）---"
if [ -f "$GATE6" ]; then
  cat "$GATE6"
else
  echo "❌ 欠落: $GATE6"
fi
echo ""
echo "⚠️ Entry 関連の設計/実装を出す前に、必ず「軸 N を閉じる・§18.5 逐語『…』(file:line)」と宣言する。"
echo "   引用なし・軸に紐づかない手は却下対象。6軸すべて ✅(証跡つき) まで『Entry 修正完了』禁止。"
echo ""
