# ファイル名一意化ルール追加 + Phase 2 rerun リネーム提示 完了報告

公式 source: WORKFLOW.md 追記 + 6 ファイルリネームコピー

## 1. Step 2-A 事前確認 (正常)

| 期待 vs 実測 | postrefit | prerefit |
|---|---|---|
| K12 LONG q99 n_fire | 期待 342 → **実測 342 ✅** | 期待 1660 → **実測 1660 ✅** |
| threshold | 1.3670 (refit 後 thresholds.json) | 1.4282 (refit 前) |
| MFE_lift_pct | +46.07% | -9.99% |
| net_quality_pp | +36.21pp | +16.06pp |

両ファイルとも期待入力 (refit 後/前) から正しく生成されていることを確認。リネーム実施可。

## 2. Step 1: WORKFLOW.md への命名ルール追記

WORKFLOW.md L22 直前に「成果物ファイル名の一意化ルール」セクション追加 (NG/OK 例 + 理由 + 適用範囲)。

## 3. Step 2-B: リネームコピー対応表

| 元 | リネーム後 | sha256 |
|---|---|---|
| ml_phase2_rerun_postrefit/net_quality_24combinations.csv | net_quality_24combinations_POSTREFIT.csv | 3107d6094e7c |
| ml_phase2_rerun_postrefit/mfe_mae_ratio_24combinations.csv | mfe_mae_ratio_24combinations_POSTREFIT.csv | 1288f40e99be |
| ml_phase2_rerun_postrefit/rmse_sanity_16labels.csv | rmse_sanity_16labels_POSTREFIT.csv | cc30aa9ad005 |
| ml_phase2_rerun_postrefit/phase2_summary.json | phase2_summary_POSTREFIT.json | 4245de8bc9e1 |
| ml_phase2_rerun_prerefit/net_quality_24combinations.csv | net_quality_24combinations_PREREFIT.csv | dbe2aaadaaf1 |
| ml_phase2_rerun_prerefit/phase2_summary.json | phase2_summary_PREREFIT.json | 7e980f078d5e |

元ファイルは残置 (sha256 維持・参照履歴を破壊しない)。

## 4. Step 2-C: チャット貼り付け

本ターン親メッセージで 6 ファイル全文を貼り付け済。各ファイルに sha256 + K12 LONG q99 n_fire 値を併記。

## 5. 完了後の状態

- WORKFLOW.md に一意化ルール明文化済 → 今後の成果物は識別子付き
- Phase 2 rerun 6 ファイル識別子付きリネームコピー完了
- postrefit が refit 後データから正常に生成されていることを n_fire=342 で確認 (取り違えなし)

## 6. 次のステップ

Web Claude が postrefit 生 CSV (`_POSTREFIT.csv`) から q99 8 組合せ加重を独立再計算 → 期待 +21.28pp / positive 7/8 → CC 値と差分照合 → まこさん K12 LONG refit 維持/撤回判断。
