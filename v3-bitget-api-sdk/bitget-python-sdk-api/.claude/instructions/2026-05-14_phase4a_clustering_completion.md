# Phase 4-a k-means クラスタリング 完了報告

| 項目 | 値 |
|---|---|
| 完了日時 | 2026-05-14T14:33:40 JST (所要 1.45 min) |
| 実行者 | CC (Claude Opus 4.7 1M context・本セッション) |
| 関連指示書 | [2026-05-14_phase4a_clustering.md](2026-05-14_phase4a_clustering.md) |
| 関連 commit | 7aa4ad7 (正本修正) / 9e5a304 (本指示書) / d9d322c (K12 LONG refit) |
| **採用 k** | **k=3** (silhouette=0.5100) |
| **結論** | **Phase 4-b 着手準備完了** (K12 LONG/K96 SHORT サンプル数チェック ✅ / フォールバック発動なし) |

## 判定サマリー

| 項目 | 結果 |
|---|---|
| 採用 k | **3** (silhouette 0.5100 で最大・size ratio 0.159 で許容範囲) |
| 旧 leak k=4 silhouette 0.212 との比較 | **2.4 倍向上** |
| cluster sizes (train) | 172,091 / 192,065 / 30,597 |
| K12 LONG q99 サンプル数チェック | ✅ **全 cluster ≥ 100** (1,415 / 817 / 1,716) |
| K96 SHORT q99 フォールバック | ✅ **全 cluster trade 可** (発動なし・MFE/MAE > 1.0) |
| test 2025 apply | ✅ 完了 (71k / 4.7k / 29k) |
| artifact 名 "test" 不在 (§4a.4) | ✅ 確認済 |

## Step 1: silhouette score 評価 (k=2〜8)

| k | silhouette | cluster sizes | min/max ratio | 判定 |
|---:|---:|---|---:|---|
| 2 | 0.5075 | 133k / 261k | 0.511 | 候補 (size 良) |
| **3** | **0.5100** | **172k / 192k / 30k** | **0.159** | **採用** (silhouette 最大) |
| 4 | 0.4833 | 173k / 56k / 10k / 154k | 0.062 | ✗ silhouette 後退・size 偏り |
| 5 | 0.4672 | 138k / 164k / 5k / 74k / 11k | 0.036 | ✗ |
| 6 | 0.4611 | 158k / 15k / 81k / 7k / 933 / 131k | 0.006 | ✗ size 偏り極端 |
| 7 | 0.4329 | 113k / 3k / 90k / 145k / 13k / 852 / 27k | 0.006 | ✗ |
| 8 | 0.3966 | 1k / 101k / 120k / 57k / 818 / 13k / 10k / 89k | 0.007 | ✗ |

採用判断: k=2 と k=3 は silhouette 近接 (0.5075 vs 0.5100) だが、k=3 で sub-structure を分離できるため採用。k≥4 では silhouette 単調減少。

**旧 leak 比較**: 旧 leak k=4 silhouette 0.212 (handoff_v4 §2) → 新 leak-free k=3 silhouette 0.510 で **2.4 倍向上**。leak 由来データでは構造が劣化していた。

## Step 2: k-means fit (採用 k=3)

| 項目 | 値 |
|---|---|
| 採用 k | 3 |
| random_state | 42 |
| n_init | 10 |
| inertia | 2,391,555.80 |
| n_iter (収束まで) | 19 |
| 学習対象 | train 2021-04〜2024-12 (394,753 行) |
| 出力 | scaler_train_2021_2024.joblib (967 B) / kmeans_k3_train_2021_2024.joblib (1.58 MB) |

artifact 名 verify (§4a.4 準拠):
- `scaler_train_2021_2024.joblib` ← "train" 含む / "test" 不在 ✅
- `kmeans_k3_train_2021_2024.joblib` ← "train" 含む / "test" 不在 ✅
- `ls *.joblib | grep -i test` → [no matches] ✅

## Step 3: cluster 性質分析

### cluster サイズ + 性質プロファイル

| cluster | n_rows | share | 性質要約 |
|---:|---:|---:|---|
| 0 | 172,091 | 43.6% | 中ボラ・LONG/SHORT バランス (K12 LONG MFE 226 / MAE 233) |
| 1 | 192,065 | 48.7% (最大) | 低ボラ・**SHORT 有利** (K96 SHORT MFE 451 / MAE 289) |
| 2 | 30,597 | 7.7% (最小) | 高ボラ・**LONG 強上昇** (K96 LONG MFE 1101 / MAE 919) |

### 16 予測値平均 (主要列抜粋)

| 列 | cluster 0 | cluster 1 | cluster 2 |
|---|---:|---:|---:|
| LONG_MFE_K12 | 225.5 | 85.9 | **404.3** |
| LONG_MAE_K12 | 232.6 | 91.4 | **477.2** |
| LONG_MFE_K96 | 667.8 | 288.5 | **1,100.8** |
| LONG_MAE_K96 | 604.8 | 451.2 | 919.5 |
| SHORT_MFE_K96 | 604.8 | **451.2** | 919.5 |
| SHORT_MAE_K96 | 667.8 | **288.5** | 1,100.8 |

(出典: results/priority_rebuild/ml_phase4_a/cluster_profile.csv)

### K12 LONG q99 サンプル数チェック (監査 #2 基準 A 案)

K12 LONG refit で n_fire が test 2025 で 1,660 → 342 に激減 (1/5 厳選) → train ベースでサンプル数確認。

| cluster | K12 LONG q99 n | 判定 |
|---:|---:|---|
| 0 | 1,415 | ✅ 統計的有意 (≥ 100) |
| 1 | 817 | ✅ 統計的有意 (≥ 100) |
| 2 | 1,716 | ✅ 統計的有意 (≥ 100) |

**全 cluster で監査 #2 基準 A 案 (≥ 100) クリア** → K12 LONG refit + cluster 別 Exit 設計が統計的に有効。

注: train set q99 threshold = 1.5621 / total fire = 3,948 (≒ 1%)。test set q99 threshold = 1.367 / total fire = 342 (≒ 0.3%) なので閾値が異なる (train と test で予測分布が違うため)。

## Step 4: K96 SHORT q99 フォールバック判定 (§4a.5)

旧監査懸念3 + Step 1-1 分析で K96 SHORT q99 は test 2025 で MFE/MAE=0.986 (逆行) だったが、train ベースで cluster 別判定:

| cluster | n_k96short_q99 | real MFE | real MAE | MFE/MAE | flag |
|---:|---:|---:|---:|---:|---|
| 0 | 44 | 4,416.12 | 230.61 | **19.15** | ✅ trade 可 |
| 1 | 3,344 | 120.77 | 65.01 | **1.86** | ✅ trade 可 |
| 2 | 560 | 8,505.26 | 253.83 | **33.51** | ✅ trade 可 |

→ **全 cluster で MFE/MAE > 1.0** → §4a.5 **フォールバック発動なし** (train ベース)

注: cluster 1 が K96 SHORT q99 fire の主流 (3,344 件 / 全 3,948 件中 85%)。
注: train set では K96 SHORT が機能・test 2025 で逆行は 2025-01/09 暴騰局面の特殊性 (Step 1-1 既発見) → Phase 4-b で cluster 別ではなく時期別の対処が必要かも。

## Step 5: test 2025 への apply

| cluster | n_rows (test 2025) | share |
|---:|---:|---:|
| 0 | 71,030 | 67.6% |
| 1 | 4,707 | 4.5% (大きく縮小) |
| 2 | 29,383 | 28.0% |

**重要観察**: cluster 1 が train で 48.7% → test で 4.5% に大幅縮小。
- 解釈: 2025 年は低ボラ SHORT 有利局面が train 期間 (2021-2024) に比べて稀
- 含意: cluster 1 ベース SHORT 戦略は test 2025 で発火頻度が少ない (= n_fire 制約・Phase 5 月次合計に影響)
- Phase 4-b 設計時に cluster 1 の test 不均衡を考慮

(出典: results/priority_rebuild/ml_phase4_a/predictions_test2025_clustered.parquet・適用入力 = predictions_test2025_k12long_refit.parquet)

## 完了報告必須証跡 5 点

### 証跡 1. コード総点検 grep 結果

```
$ grep -rn "394,573\|394573" .claude/rules/phase_compliance_checklist.md cc_ml_design_spec.md
[no matches] ✅

$ grep -n "k12long_refit" .claude/rules/phase_compliance_checklist.md
44:| 4a.1 | **fit は train 2021-04〜2024-12 のみ** (test 2025 禁止) | `PREDICTIONS = predictions_train_2021_2024_k12long_refit.parquet` (K12 LONG num_leaves=15 部分採用版・2026-05-14) |

$ ls results/priority_rebuild/ml_phase4_a/*.joblib | grep -i test
[no matches] ✅ (§4a.4 準拠)
```

### 証跡 2. 数値の二重提示

- チャットサマリー: 上記 Step 1〜5 各セクション
- 出典:
  - results/priority_rebuild/ml_phase4_a/silhouette_evaluation.csv (k=2〜8)
  - results/priority_rebuild/ml_phase4_a/cluster_profile.csv (16 予測値平均)
  - results/priority_rebuild/ml_phase4_a/k12long_q99_sample_check.csv
  - results/priority_rebuild/ml_phase4_a/k96short_q99_fallback_check.csv
  - results/priority_rebuild/ml_phase4_a/phase4a_summary.json

### 証跡 3. 成果物ファイル実体

| ファイル | サイズ | sha256 (先頭12桁) | 更新時刻 |
|---|---:|---|---|
| scaler_train_2021_2024.joblib | 967 B | 2f29af8dc18c | 2026-05-14 14:33 |
| kmeans_k3_train_2021_2024.joblib | 1,580 KB | 5c10c6f86dec | 2026-05-14 14:33 |
| silhouette_evaluation.csv | 960 B | 36fea7260da8 | 2026-05-14 14:33 |
| cluster_profile.csv | 1,106 B | e9d55cc4c548 | 2026-05-14 14:33 |
| k12long_q99_sample_check.csv | 110 B | 98af21587d94 | 2026-05-14 14:33 |
| k96short_q99_fallback_check.csv | 307 B | 04475b62aeb0 | 2026-05-14 14:33 |
| phase4a_summary.json | 969 B | aedbefbf9557 | 2026-05-14 14:33 |
| predictions_test2025_clustered.parquet | 12,101 KB | dd07d3d90bb0 | 2026-05-14 14:33 |
| logs/phase4a_clustering_20260514_143209.log | - | - | 2026-05-14 14:33 |

### 証跡 4. 実行ログ

| 項目 | 値 |
|---|---|
| 開始 | 2026-05-14T14:32:13 |
| 終了 | 2026-05-14T14:33:40 |
| 所要 | **1.45 分** |
| 終了コード | 0 |
| Python warning | 0 件 |

### 証跡 5. 絞り込み示唆語彙 自己 grep 結果

```
[no matches] 採用候補
[no matches] 効く
[no matches] 効かない
[no matches] 優先
[no matches] 不要
[no matches] 切れる
[no matches] 残せる
[no matches] 除外して良い
[no matches] 使える
[no matches] 意味がある
[no matches] 意味がない
```

(「重要」は本報告書本文中の section header で使用するが、絞り込み示唆ではなく分析の重要観察を示す中立語彙として使用)

## 物理証跡 8 点

| # | 項目 | 結果 |
|---|---|---|
| 1 | 入力ファイル整合性 | ✅ refit 版 sha256 2ee206431c37 / 394,753 行 |
| 2 | silhouette 評価プロセス | ✅ k=2〜8 全 score + cluster sizes 保存 |
| 3 | 出力ファイル証跡 | ✅ scaler/km joblib sha256 取得・"test" 文字列不在確認 |
| 4 | 第三者再読み出し検証 | ✅ joblib.load 可能 (k=3 / cluster_centers_ shape (3, 16)) |
| 5 | データ sanity | ✅ 全 3 cluster にサンプル存在 (172k / 192k / 30k) |
| 6 | stderr / Python warning | ✅ 0 件 |
| 7 | 同コマンド bit-exact 再現性 | △ random_state=42 / n_init=10 で固定 (実測 1 回・bit-exact 確認は本タスクでは省略・seed 設定で deterministic 想定) |
| 8 | K12 LONG / K96 SHORT サンプル数 + フォールバック判定 | ✅ K12 LONG 全 cluster ≥ 100 / K96 SHORT 全 cluster trade 可 |

## 完了後の状態

| 項目 | 確認 |
|---|---|
| 正本 2 ファイルの行数・入力ファイル名修正 | ✅ commit 7aa4ad7 |
| silhouette 再評価で leak フリー最適 k=3 確定 | ✅ |
| k-means fit 完了 (train のみ・joblib 保存・"test" 文字列不在) | ✅ |
| cluster 性質プロファイル判明 | ✅ (cluster 0 中ボラ / 1 低ボラ SHORT 有利 / 2 高ボラ LONG 強) |
| K12 LONG サンプル数チェック完了 (監査 #2 A 案 ≥ 100) | ✅ 全 cluster クリア |
| K96 SHORT q99 フォールバック判定完了 (§4a.5) | ✅ 全 cluster trade 可 (発動なし) |
| test 2025 への apply 完了 | ✅ (71k/4.7k/29k) |
| Phase 4-b (Exit 設計) 着手準備完了 | ✅ |

## 次のステップ

1. Web Claude が本完了報告を独立評価 (silhouette 評価・cluster 性質・サンプル数チェック)
2. まこさん最終 GO
3. **Phase 4-b (Exit 設計) 着手指示書発行**
   - cluster × K × side ごとの最適 Exit (固定 TP / トレーリング / 時間 Exit) をデータ駆動で選択
   - phase_compliance §4b.4-b 拡張 (Exit 約定率 ≥ 12% 必達ライン) 適用
   - K12 LONG cluster 別 TP 設計 (低ボラ選好解消で MFE 絶対値増・短小 TP 候補)

### 留意事項 (Phase 4-b へ申し送り)

1. **cluster 1 の test 不均衡**: train 48.7% → test 4.5% で大幅縮小 → cluster 1 ベース戦略の Phase 5 月次合計影響を要監視
2. **K96 SHORT 構造的問題**: train ベース cluster ではフォールバック不要だが test 2025 で逆行確認済 (2025-01/09 集中) → 時期別 no-trade を検討
3. **K12 LONG num_leaves=15 効果**: 全 cluster で q99 サンプル ≥ 100 確保・refit の効果が cluster 設計レベルで保たれている
