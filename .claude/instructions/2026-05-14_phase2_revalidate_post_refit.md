# 【タスク】案 Z: K12 LONG refit 後データで Phase 2 再判定 (§8 違反の影響範囲測定)

(監査#7 審査済・Web Claude レビュー済・まこさん GO 済 2026-05-14)

## 構造化ルール準拠

- 保存先: .claude/instructions/2026-05-14_phase2_revalidate_post_refit.md
- 完了報告: .claude/instructions/2026-05-14_phase2_revalidate_post_refit_completion.md

## 着手前必読 (省略禁止・L-179/L-180/L-181)

1. WORKFLOW.md §🔴次のタスク
2. cc_ml_design_spec.md §1.6 / §1.6.1 メタルール / §8 制約禁止事項
3. .claude/instructions/2026-05-14_phase1_k12long_refit_completion.md (refit・commit d9d322c)
4. .claude/instructions/2026-05-14_phase2_execute_completion.md (元の Phase 2 結果)
5. results/priority_rebuild/leak_incident_20260513.md (背景)

## Step 0-1: 必読ファイル引用 (読んだフリ防止)

a. cc_ml_design_spec.md §8 全文貼り付け (特に「テスト結果を見てから学習データで
   再学習する際、テスト結果を直接参照しない」の行)
b. cc_ml_design_spec.md §1.6 / §1.6.1 全文貼り付け
c. 元の Phase 2 完了報告から「q99 加重 +20.58pp / 7-8 positive」の判定結果引用
d. K12 LONG refit 完了報告から「refit の動機」が記載された箇所を引用

各引用が期待値と一致しない/省略 → STOP

## 背景 (監査#7 結果)

監査#7 が以下を確定:

- commit d9d322c (K12 LONG num_leaves=15 refit) は §8 違反
  - audit#3 の「K12 LONG MFE_lift マイナス」指摘は test 2025 の数値
    (net_quality_24combinations.csv 由来)
  - train では K12 LONG MFE_lift = +364.97% で正反対
  - = test 結果を見て学習データ (K12 LONG モデル) を変更した = §8 抵触
- 監査推奨 = 案 Z: §8 違反を認め・refit 後データで Phase 2 を再判定して影響範囲を測る

## 本タスクの目的

§8 違反が「どれだけ Phase 2 判定を汚染したか」を事実で測定する。

- refit 後データで Phase 2 を判定し直す
- 元の Phase 2 結果 (refit 前) と比較
- PASS が維持されるか・崩れるか・どちらに動いたかを確認

## 重要な前提整理 (CC が混乱しないため)

元の Phase 2 (commit 0ffd326) は **refit 前の predictions** で実施された。

- 元 Phase 2 入力: predictions_test2025.parquet (Phase 1・refit 前)
- 元 Phase 2 結果: q99 加重 +20.58pp / 7-8 positive / PASS

K12 LONG refit (commit d9d322c) 後、predictions_test2025_k12long_refit.parquet が
生成されたが、**Phase 2 はこの refit 後データでは判定し直されていない**。

本タスクは「refit 後データで Phase 2 を判定」する。

## Step 1: refit 後データで Phase 2 4 指標を判定

scripts/priority_rebuild/run_phase2_precision.py を refit 後データに対して実行:

```bash
python3 scripts/priority_rebuild/run_phase2_precision.py \
  --predictions results/priority_rebuild/ml_phase1_k12long_refit/predictions_test2025_k12long_refit.parquet \
  --output results/priority_rebuild/ml_phase2_post_refit/ \
  2>&1 | tee logs/phase2_post_refit_$(date +%Y%m%d_%H%M%S).log
```

(--引数未対応なら path をハードコード変更)

cc_ml_design_spec §1.6 の 4 指標を全て判定:

1. q99 net_quality (q99 8 組合せ件数加重平均) > +10pp かつ 8 組合せ中 6 以上 positive
2. net_quality 最小値 > -50pp
3. valid_rmse / label_std (16 ラベル) 16 中 14 以上で < 1.5
4. mean_real_MFE / mean_real_MAE (q99 後 8 組合せ) 6 以上で > 1.0

## Step 2: 元の Phase 2 (refit 前) との比較

| 指標 | 元 Phase 2 (refit 前) | 案 Z (refit 後) | 差分 |
|---|---|---|---|
| q99 加重 net_quality | +20.58pp | XX | XX |
| 8 組合せ positive 数 | 7/8 | XX | XX |
| K12 LONG q99 net_quality | (元の値) | XX | XX |
| 16 ラベル RMSE sanity | 16/16 | XX | XX |
| 4 指標 総合判定 | PASS | XX | XX |

特に K12 LONG q99 の数値が refit でどう変わったかを明示。

## Step 3: §8 違反の影響範囲の判定

| パターン | 意味 | 含意 |
|---|---|---|
| パターン 1: refit 後も PASS・K12 LONG が大きく改善 | refit は Phase 2 判定を「良い方向」に汚染 | refit が結果を底上げした疑い・要協議 |
| パターン 2: refit 後も PASS・K12 LONG ほぼ不変 | refit の Phase 2 への影響は軽微 | 違反だが実害小・refit 残置の議論可能 |
| パターン 3: refit 後は FAIL | refit が判定を覆していた | 重大・refit 撤回 (案 X) を検討 |

判定結果がどのパターンか明示。

## Step 4: メタルール §1.6.1 との関係整理

監査#7 見落とし K の指摘:

- メタルール §1.6.1 = 「結果確定後の基準変更は当該 Phase の合否判定に適用しない」
- 案 G 当時は「spec 改訂」の話だったが、refit も「結果を見て学習データ変更」で同類
- K12 LONG refit にメタルール §1.6.1 が適用されるか整理

本タスクでは「整理」のみ (CC が論点を書き出す)。判断は Web Claude + まこさん。

## 物理証跡 8 点

1. 入力ファイル整合性 (refit 後 predictions の sha256・元 Phase 2 入力との別物確認)
2. 計算プロセス内部証跡 (4 指標の計算過程・lift% 分母分子)
3. 出力ファイル証跡 (phase2_post_refit の全成果物 sha256)
4. 第三者再計算検証 (1 組合せの net_quality を独立再計算で一致確認)
5. データ sanity (refit 後 predictions の null 率・K12 LONG 列が refit 版か確認)
6. stderr / Python warning 全件
7. 同コマンド bit-exact 再現性確認
8. 元 Phase 2 との差分が全指標で明示されているか

## 完了報告必須証跡 5 点

1. **コード総点検 grep 結果**
   - `grep -n "k12long_refit\|predictions_test2025" scripts/priority_rebuild/run_phase2_precision.py`
2. **数値の二重提示**
   - Step 2 比較表 (元 Phase 2 vs 案 Z) + 出典
3. **成果物ファイル実体** (sha256 + 行数 + 更新時刻)
   - phase2_post_refit/ の全 CSV/JSON
4. **実行ログ** (所要・終了コード・Python warnings 全件)
5. **絞り込み示唆語彙 自己 grep 結果** (no matches 含む)

## 完了後の状態

- refit 後データでの Phase 2 判定結果が判明
- 元 Phase 2 (refit 前) との差分が判明
- §8 違反の影響範囲が 3 パターンのどれか判明
- メタルール §1.6.1 との関係が論点整理済
- K12 LONG refit を「残置」「撤回」のどちらにすべきかの判断材料が揃う

## 次のステップ

完了報告受領 → Web Claude が生データから独立評価 (CC サマリーを見る前に生 CSV から
独自集計・監査#6/#7 懸念対応) → まこさん最終 GO →
refit 残置/撤回を確定 → その後で残る緊急対応 (絶対閾値 drift 対処・rolling 検討) へ

## Web Claude 独立評価の手順 (監査#6/#7 懸念対応)

完了報告受領時、Web Claude は:

- CC 完了報告の判定・推奨を見る前に、phase2_post_refit の生 CSV から 4 指標を独自集計
- 独自集計と CC 集計を差分照合
- 特に「数値の出所 (train か test か)」を毎回確認する
  (今回の §8 違反は Web Claude が test 由来数値を train 問題と誤認したことが原因)
