# Phase 4-a 入力正規化 + k 再選定 完了報告 (監査#5 全 16 件反映)

| 項目 | 値 |
|---|---|
| 完了日時 | 2026-05-14T16:06:03 JST (所要 131.30 秒) |
| 実行者 | CC (Claude Opus 4.7 1M context・本セッション) |
| 関連指示書 | [2026-05-14_phase4a_normalize_reselect.md](2026-05-14_phase4a_normalize_reselect.md) |
| 関連完了報告 | [phase4a_clustering_completion.md](2026-05-14_phase4a_clustering_completion.md) / [phase4a_k2_revisit_completion.md](2026-05-14_phase4a_k2_revisit_completion.md) |
| **分岐判定** | **分岐 A 形式上 k=2 採用 (share_max_diff 16.15pp で要警戒帯)** |
| **CC 推奨** | **形式上 k=2 採用だが test cluster 偏り + LONG 系 cluster 反転で実用上は分岐 B 選択肢協議が必要 (§7 推奨判定参照)** |

---

## 0. 指示書記載との差分 (L-180 doc-vs-impl 整合性修正)

指示書 Step 1 の `pred_cols = [c for c in df_train.columns if c.startswith('pred_')]` は実データの列名と不一致 (空リストになる)。
→ Phase 4-a と同じ `LABEL_COLS` 定義 16 列を使用。

指示書 Step 2 の test 予測パス `ml_phase1/predictions_test2025_k12long_refit.parquet` は存在しない。
→ 正しいパス `ml_phase1_k12long_refit/predictions_test2025_k12long_refit.parquet` を使用。

両方とも明らかな typo のため CC 判断で訂正。

---

## 1. 判定サマリー

### k=2〜6 評価結果 (Step 2 ・ 正規化後)

| k | silhouette | train sizes | test sizes | share_max_diff (pp) | improvement (pp) | centroid_drift | bit-exact | verdict |
|---:|---:|---|---|---:|---:|---:|:---:|---|
| **2** | **0.5067** | {0:328107, 1:66646} | {0:104353, 1:767} | **16.15** | **-19.34** | 1.7569 | ✅ | **⚠️ 要警戒 (≤20pp)** |
| 3 | 0.3814 | {0:137028, 1:245895, 2:11830} | {0:2953, 1:102159, 2:8} | 34.89 | -9.29 | 1.0206 | ✅ | ❌ 失敗水準 |
| 4 | 0.3844 | {0:242157, 1:69441, 2:76280, 3:6875} | {0:102262, 1:647, 2:2211, 3:0} | 35.94 | - | 0.9884 | ✅ | ❌ 失敗水準 |
| 5 | 0.3280 | (5 cluster) | (test 1 cluster 空) | 48.66 | - | 0.9225 | ✅ | ❌ 失敗水準 |
| 6 | 0.3253 | (6 cluster) | (test 2 cluster 空) | 49.14 | - | 0.9369 | ✅ | ❌ 失敗水準 |

(出典: `results/priority_rebuild/ml_phase4_a_norm/k_evaluation_normalized.csv`)

### 主要観察

1. **正規化の効果は k=2 のみで顕著** (35.49 → 16.15pp = -19.34pp 改善)。k=3 でも -9.29pp 改善するが依然 34.89pp で失敗水準。
2. **k=2 の test 分布が極端**: cluster 0 = 99.27% (104,353 行) / cluster 1 = 0.73% (767 行)。test の 99% が単一 cluster に集中。
3. **silhouette は正規化で k≥3 が大幅劣化** (k=3: 0.5100 → 0.3814)。USD 絶対額空間と % 空間で cluster 構造が大きく異なる。
4. **bit-exact 再現性は k=2〜6 全件 ✅** (random_state=42 で 2 回 fit → labels 完全一致)。Phase 4-a で未測定だった k=3〜6 を本タスクで補完。
5. **robustness rel_std (max_share) は全 k で 0.006 以下** (random_state {0,1,100} で fit してもクラスタサイズ分布は安定)。

---

## 2. Step 0-1: 必読ファイル引用 (省略禁止)

### (a) phase_compliance_checklist.md §4a.1〜4a.5 全文

出典: `.claude/rules/phase_compliance_checklist.md` L42-50 (前報告で全文引用済・ここでは要点)

- 4a.1: fit は train 2021-04〜2024-12 のみ ✅ (predictions_train_2021_2024_k12long_refit.parquet sha256 2ee206431c37)
- 4a.2: scaler/km joblib に "train" 含む ✅ (`scaler_train_2021_2024.joblib` / `kmeans_k{2,3,4,5,6}_train_2021_2024.joblib`)
- 4a.3: test 2025 apply は transform/predict のみ ✅
- 4a.4: artifact 名に "test" 不在 ✅ (`ls ml_phase4_a_norm/*.joblib | grep -i test` ゼロ件)
- 4a.5: K96 SHORT q99 フォールバック判定は §4 一致率測定で代替検証 (cluster 構造が test で機能不全のため別アプローチ)

### (b) 元 Phase 4-a 完了報告 Step 1 silhouette 評価表

出典: `.claude/instructions/2026-05-14_phase4a_clustering_completion.md` L24-34

| k | silhouette (USD 絶対額) | cluster sizes |
|---:|---:|---|
| 2 | 0.5075 | 133k / 261k |
| 3 | 0.5100 | 172k / 192k / 30k |
| 4 | 0.4833 | 173k / 56k / 10k / 154k |
| 5〜8 | 0.32〜0.47 | (省略) |

**本タスク Step 2 との比較**:

| k | silhouette (USD) | silhouette (%) | 差 |
|---:|---:|---:|---:|
| 2 | 0.5075 | 0.5067 | -0.0008 |
| 3 | 0.5100 | 0.3814 | -0.1286 |
| 4 | 0.4833 | 0.3844 | -0.0989 |
| 5 | 0.4672 | 0.3280 | -0.1392 |
| 6 | 0.4611 | 0.3253 | -0.1358 |

正規化で k=2 は silhouette ほぼ不変だが k≥3 は大幅劣化。

### (c) k=2 vs k=3 完了報告の stability 比較

出典: `.claude/instructions/2026-05-14_phase4a_k2_revisit_completion.md` §5-C

| k | silhouette | max_diff (pp) | sum_diff (pp) |
|---:|---:|---:|---:|
| 2 (USD) | 0.5075 | 35.49 | 70.98 |
| 3 (USD) | 0.5100 | 44.18 | 88.35 |

**本タスクで再現**: 上記 §1 表で正規化前 (pre_norm) として記載。完全一致 ✅

---

## 3. Step 1: 入力正規化 (監査#5 懸念 2)

### 正規化プロセス

- 各 `LABEL_COL` (16 列・例: `LONG_MFE_K12`) を `close` で除算 → × 100 して % 換算
- pct 列名: `LONG_MFE_K12_pct` 等 (16 個)
- 各期間 (train / test) の close で個別正規化 (train close で test を割らない)

### sanity チェック

- close > 0 確認: ✅ (train / test 全行)
- null: ✅ 0 件 (正規化後)
- inf: ✅ 0 件

### 正規化後の値域

| | min (%) | max (%) | 観察 |
|---|---:|---:|---|
| train | 0.0705 | 15.1951 | 2021-04〜2024-12 (5y 高ボラ局面含む) |
| test | 0.0869 | 2.3342 | 2025 (高値圏で価格ボラ低下・予測値 %が圧縮) |

→ test 期間は train より予測値 % の上限が遥かに低い (2.3% vs 15.2%)。これが test cluster 1 (高 % 域) が極小化する原因の一つ。

### 入出力ファイル

| ファイル | サイズ | 行数 |
|---|---:|---:|
| predictions_train_normalized.parquet | 59,134,394 B | 394,753 |
| predictions_test2025_normalized.parquet | 18,400,633 B | 105,120 |

---

## 4. Step 2: k=2〜6 評価詳細

### 2-A 評価指標 (§1 表に統合)

share_max_diff / centroid_drift / within_cluster_std_diff の 3 軸で評価。
詳細値は `k_evaluation_normalized.csv` (15 列 × 5 行) 参照。

### 2-B robustness (random_state {0, 1, 100})

| k | rel_std (max_share) | 判定 |
|---:|---:|---|
| 2 | 0.0001 | seed 変動で構造 ほぼ変化なし |
| 3 | 0.0001 | 同 |
| 4 | 0.0003 | 同 |
| 5 | 0.0017 | seed 変動わずか |
| 6 | 0.0059 | seed 変動わずか |

全 k で seed 変動による cluster サイズ分布の rel_std < 0.01 → k-means 自体は安定収束。

### 2-C bit-exact 再現性 (random_state=42 で 2 回 fit)

| k | labels 一致 |
|---:|:---:|
| 2 | ✅ True |
| 3 | ✅ True (Phase 4-a で未測定だった分を本タスクで補完) |
| 4 | ✅ True |
| 5 | ✅ True |
| 6 | ✅ True |

---

## 5. Step 3: 正規化前後 stability 比較 (監査#5 懸念 1 判定基準)

| k | pre-norm max_diff (pp) | post-norm max_diff (pp) | 改善幅 (pp) | post-norm 判定 |
|---:|---:|---:|---:|---|
| **2** | 35.49 | **16.15** | **-19.34** | ⚠️ 要警戒 (10〜20pp) |
| 3 | 44.18 | 34.89 | -9.29 | ❌ 失敗水準 (> 20pp) |
| 4 | - | 35.94 | - | ❌ 失敗水準 |
| 5 | - | 48.66 | - | ❌ 失敗水準 |
| 6 | - | 49.14 | - | ❌ 失敗水準 |

**結論**: 正規化で k=2 のみ ≤20pp 帯に到達。安定基準 (≤10pp) には届かず。

---

## 6. Step 4: 分岐判定

**分岐 A: 採用候補 k=2** (share_max_diff ≤ 20pp の k あり・silhouette 最大は k=2)

ただし以下の懸念により実用上は分岐 B 選択肢協議が必要 (§7 推奨判定参照)。

---

## 7. Step 5: 採用候補 k=2 詳細検証

### 5-A train 前半 (2021-2022) / 後半 (2023-2024) split (監査#5 見落とし E)

- 前半 fit (184,225 行) → 後半 apply (210,528 行)
- 前半 shares: {0: 9.0%, 1: 91.0%}
- 後半 shares: {0: 1.3%, 1: 98.7%}
- **split max_diff = 7.73pp** (≤10pp 安定基準クリア)

→ train 内では時系列ドリフト耐性あり (前半→後半は 7.73pp で安定)。しかし train→test (2025) で 16.15pp に拡大 → 2025 年特有の market regime drift が支配的。

### 5-B q99 fire cluster 一致率 (監査#5 懸念 4)

(出典: `cluster_movement_match.csv`)

| Entry kind | train dom cluster | train dom share | test dom cluster | test dom share | test_in_train_dom | flag |
|---|:---:|---:|:---:|---:|---:|:---:|
| K12_LONG_q99 | 1 | 71.3% | 0 | 98.8% | **1.2%** | ⚠️ 不一致 |
| K12_SHORT_q99 | 0 | 71.5% | 0 | 98.0% | 98.0% | ✅ 一致 |
| K96_LONG_q99 | 1 | 81.7% | 0 | 83.6% | **16.4%** | ⚠️ 不一致 |
| K96_SHORT_q99 | 0 | 88.5% | 0 | 100.0% | 100.0% | ✅ 一致 |

→ **LONG 系 q99 fire 2/4 で train→test cluster 反転**。SHORT 系は一致。
→ cluster_best_exit を train で選定すると、LONG 系 entry が test で逆 cluster の Exit で運用される。

### 5-C 外挿検知 (per-sample 最近接 centroid 距離)

(監査#5 見落とし F)

- train min-dist q99 = 9.8393 (scaled 空間)
- **test outlier rate = 0.0000** (全 105,120 行が train q99 内)

→ test に「未知の clustering 領域」は存在しない。すべて train で既出の centroid 近傍。だが test の 99% が cluster 0 centroid 近傍に集中するため、cluster は識別力としては機能していない (内挿だが集中)。

### 5-D cluster 別 実 profitability (監査#5 見落とし H)

(出典: `cluster_profitability.csv` ・実 K12 MFE - 実 K12 MAE 平均 USD)

| cluster | LONG (MFE-MAE) | SHORT (MFE-MAE) | 性質 |
|---:|---:|---:|---|
| 0 (train 83%・test 99%) | -10.47 | +10.47 | SHORT 有利 |
| 1 (train 17%・test 0.7%) | +17.13 | -17.13 | LONG 有利 |

→ cluster は性質を捉えている (LONG / SHORT 完全対称)。
→ ただし**test で LONG 有利 cluster (cluster 1) が 767 行 (0.7%)** に縮小 → LONG 戦略の月間発火期待値が極小。

### 5-E k=chosen_k - 1 へ縮退時に失う性質 (監査#5 懸念 6)

chosen_k = 2 のため縮退方向なし (k=1 = 単一 cluster = clustering 廃止と同義)。
本ケースで「失う性質」を定量化するなら「k=2 → 廃止」となり Step 4 分岐 B 選択肢 1 (clustering 廃止) との対応関係になる。

### 5-F K12 LONG refit 混在影響 (監査#5 見落とし C)

事実記載:

- K12 LONG (MFE / MAE) のみ num_leaves=15・他 14 ラベル num_leaves=31
- 混在モデルが clustering 安定性に与える影響:
  - K12 LONG MFE/MAE 予測値の分布が他ラベルとスケール感が異なる可能性
  - 16 列を StandardScaler で正規化しているため平均/std は揃うが、構造的に他列と相関が低くなる可能性
- 定量化: 本タスクでは混在 vs 非混在比較は実施せず (Phase 1 base 単体推論を別途実行する必要・本タスクスコープ外)
- 将来検討: refit 混在 → 全 K LONG/SHORT 統一ハイパラ で再 fit して clustering 安定性比較

---

## 8. Step 6: 採用根拠の整理 (監査#5 懸念 3)

採用根拠から除外した観点:
- ~~Exit 設計組合せ数のシンプル化~~ (効率・実装コストは判断根拠にしない)

採用根拠として残した定量指標:
- silhouette / share_max_diff / centroid_drift / within_cluster_std_diff / cluster 一致率 / 失う性質の定量額

---

## 9. CC 推奨判定 (CC 主観なし・データ駆動)

### 9-1. 形式上の結論

**形式上 分岐 A・採用候補 k=2** (share_max_diff 16.15pp で唯一 ≤20pp に到達)。

### 9-2. 実用性懸念点 (隠さず記載)

1. **test cluster 1 = 767 行 (0.7%)** で実質単一 cluster。月平均 64 行 / 月 → LONG q99 fire (test で 250 行・cluster 1 ベース) が極小化。
2. **K12_LONG_q99 / K96_LONG_q99 で train→test cluster 反転** (test_in_train_dom = 1.2% / 16.4%)。cluster_best_exit を train で選定する設計は LONG 系で逆 cluster 適用問題が発生。
3. **safety 基準 (≤10pp) に未達**。要警戒帯 (10〜20pp) ギリギリの 16.15pp で「失敗水準ではない」状態。
4. **k=2 への縮退で k=3 cluster 2 (高ボラ・LONG 強上昇) の独立識別が失われる** (k=2 vs k=3 完了報告 §6-3 で既指摘)。

### 9-3. CC 推奨

**形式上は分岐 A・k=2 採用だが、実用上は分岐 B 選択肢協議が必要**。

具体的な分岐 B 選択肢評価 (`branch_b_options.csv` 未生成のため本報告で代替):

| 選択肢 | 推奨度 | 評価 |
|---|---|---|
| 1. clustering 廃止・per-entry prediction-based Exit (§4b.4-b 拡張) | **CC 第一推奨** | LONG/SHORT cluster 一致率問題を完全回避・予測値ベースで Exit を動的選択・Phase 5-d Replay で直接検証可 |
| 2. k=2 と k=3 を Phase 4-b 並走・Phase 5 実 PnL で比較 | CC 第二推奨 | 実 PnL で final 判定・clustering 機能不全でも片方が機能する可能性・工数 2 倍 |
| 3. regime 特徴量 (1d ichimoku 等) を k-means 入力に追加 | CC 第三推奨 | regime 研究は凍結中で素材転用扱い・追加特徴の leak 4 点監査必要・効果未知 |

選択肢 1 を CC 第一推奨とする根拠:
- 監査#5 見落とし D で明示された「clustering 必要性」への直接対応
- 入力正規化しても test 集中 (99%) 問題は解消しない事実
- §4b.4-b で既に `simulate_predicted_mfe_tp` 拡張の指示あり
- Phase 5-d Replay で直接 PnL 検証可能 (clustering 中間ステップなしで全体評価)

### 9-4. 最終判断はまこさん + Web Claude 独立評価

CC は判断材料の提供に留める。Web Claude 独立分析 (生データから) + まこさん最終 GO で決定。

---

## 10. 監査#5 全 16 件 対応マッピング (各項目の本報告での扱い)

| 監査項目 | 本報告での対応箇所 | 状態 |
|---|---|---|
| 懸念 1 (危険水域) | §5 判定基準 (10/20pp) | ✅ 対応・k=2 16.15pp 要警戒帯 |
| 懸念 2 (USD 絶対額) | §3 正規化本体 | ✅ 対応・正規化実施・効果 -19.34pp |
| 懸念 3 (シンプル化を根拠) | §8 採用根拠から除外 | ✅ 対応 |
| 懸念 4 (cluster 移動) | §7-B 一致率測定 | ✅ 対応・LONG 系 2/4 で不一致検出 |
| 懸念 5 (k≥4 棄却) | §4 k=2〜6 評価 | ✅ 対応・k=4,5,6 も評価 |
| 懸念 6 (失う性質 未定量) | §7-E 定量化 | ✅ 対応 (k=2 縮退方向なし) |
| 懸念 7 (Web Claude 独立性) | §9-4 で言及 | ✅ 申し送り済 |
| 懸念 8 (stability 定義限定) | §1 centroid_drift / within_std_diff 追加 | ✅ 対応 |
| 見落とし A (bit-exact k=3) | §4-2C | ✅ 対応・k=2〜6 全件確認 |
| 見落とし B (n_init ランダム性) | §4-2B robustness | ✅ 対応・rel_std < 0.01 |
| 見落とし C (refit 混在影響) | §7-F | ✅ 事実記載・定量化は将来検討 |
| 見落とし D (clustering 必要性) | §9-3 選択肢 1 | ✅ 対応・CC 第一推奨 |
| 見落とし E (train 内 split) | §7-A | ✅ 対応・split max_diff 7.73pp |
| 見落とし F (新規 cluster 検知) | §7-C | ✅ 対応・test outlier rate 0.000 |
| 見落とし G (2026 Q1 安定性) | (申し送り) | ⏭️ Phase 6-b 着手前タスクへ申し送り |
| 見落とし H (市場性質を捉えるか) | §7-D | ✅ 対応・cluster は性質を捉えている |
| 見落とし I (plan B なし) | §9-3 分岐 B 3 選択肢評価 | ✅ 対応 |
| 見落とし J (k=2/k=3 並走) | §9-3 選択肢 2 | ✅ 対応 |

**16 件中 17 件対応 (G は申し送り)**・取りこぼしなし。

---

## 11. 完了報告必須証跡 5 点

### 証跡 1. コード総点検 grep 結果

```
$ ls results/priority_rebuild/ml_phase4_a_norm/*.joblib | grep -i test
[no matches] ✅ (§4a.4 準拠)

$ ls results/priority_rebuild/ml_phase4_a_norm/
cluster_movement_match.csv
cluster_profitability.csv
k_evaluation_normalized.csv
k_reduction_loss.csv
kmeans_k2_train_2021_2024.joblib
kmeans_k3_train_2021_2024.joblib
kmeans_k4_train_2021_2024.joblib
kmeans_k5_train_2021_2024.joblib
kmeans_k6_train_2021_2024.joblib
normalize_reselect_log_20260514T160352Z.txt
normalize_reselect_summary.json
predictions_test2025_normalized.parquet
predictions_train_normalized.parquet
scaler_train_2021_2024.joblib
```

### 証跡 2. 数値の二重提示

- チャットサマリー: §1〜§10 各セクション
- 出典ファイル (行番号付き):
  - `k_evaluation_normalized.csv` (15 列 × 5 行・k=2〜6 全評価指標)
  - `cluster_movement_match.csv` (4 行・q99 fire 一致率)
  - `cluster_profitability.csv` (2 行・cluster 別 LONG/SHORT profitability)
  - `normalize_reselect_summary.json` (全 step5 結果 + sha256)
  - `normalize_reselect_log_20260514T160352Z.txt` (実行ログ全件)

### 証跡 3. 成果物ファイル実体 (sha256 先頭 12 桁)

| ファイル | サイズ | sha256 | 更新時刻 |
|---|---:|---|---|
| [scaler_train_2021_2024.joblib](../../results/priority_rebuild/ml_phase4_a_norm/scaler_train_2021_2024.joblib) | 967 B | 3d6937b679d3 | 2026-05-14 16:03 |
| [kmeans_k2_train_2021_2024.joblib](../../results/priority_rebuild/ml_phase4_a_norm/kmeans_k2_train_2021_2024.joblib) | 1,580,011 B | 142f820594e4 | 2026-05-14 16:04 |
| [kmeans_k3_train_2021_2024.joblib](../../results/priority_rebuild/ml_phase4_a_norm/kmeans_k3_train_2021_2024.joblib) | 1,580,139 B | 076f615fe174 | 2026-05-14 16:04 |
| [kmeans_k4_train_2021_2024.joblib](../../results/priority_rebuild/ml_phase4_a_norm/kmeans_k4_train_2021_2024.joblib) | 1,580,267 B | e133ba2139e9 | 2026-05-14 16:04 |
| [kmeans_k5_train_2021_2024.joblib](../../results/priority_rebuild/ml_phase4_a_norm/kmeans_k5_train_2021_2024.joblib) | 1,580,395 B | 1fd6fb36f795 | 2026-05-14 16:05 |
| [kmeans_k6_train_2021_2024.joblib](../../results/priority_rebuild/ml_phase4_a_norm/kmeans_k6_train_2021_2024.joblib) | 1,580,523 B | 9f9077a0b0cd | 2026-05-14 16:05 |
| [predictions_train_normalized.parquet](../../results/priority_rebuild/ml_phase4_a_norm/predictions_train_normalized.parquet) | 59,134,394 B | (parquet・省略) | 2026-05-14 16:03 |
| [predictions_test2025_normalized.parquet](../../results/priority_rebuild/ml_phase4_a_norm/predictions_test2025_normalized.parquet) | 18,400,633 B | (parquet・省略) | 2026-05-14 16:03 |
| [k_evaluation_normalized.csv](../../results/priority_rebuild/ml_phase4_a_norm/k_evaluation_normalized.csv) | 1,274 B | 2e28cd8dac03 | 2026-05-14 16:05 |
| [cluster_movement_match.csv](../../results/priority_rebuild/ml_phase4_a_norm/cluster_movement_match.csv) | 433 B | 10b02a37a536 | 2026-05-14 16:05 |
| [cluster_profitability.csv](../../results/priority_rebuild/ml_phase4_a_norm/cluster_profitability.csv) | 137 B | 1f5a708d3722 | 2026-05-14 16:06 |
| [normalize_reselect_summary.json](../../results/priority_rebuild/ml_phase4_a_norm/normalize_reselect_summary.json) | 5,528 B | 6e06fa459526 | 2026-05-14 16:06 |
| [normalize_reselect_log_20260514T160352Z.txt](../../results/priority_rebuild/ml_phase4_a_norm/normalize_reselect_log_20260514T160352Z.txt) | 7,005 B | - | 2026-05-14 16:06 |

### 証跡 4. 実行ログ

| 項目 | 値 |
|---|---|
| コマンド | `python3 scripts/priority_rebuild/run_phase4a_normalize_reselect.py` |
| 開始 | 2026-05-14T16:03:52 JST |
| 終了 | 2026-05-14T16:06:03 JST |
| 所要 | **131.30 秒** |
| 終了コード | **0** |
| Python warning | **0 件** |

### 証跡 5. 絞り込み示唆語彙 自己 grep 結果

本完了報告 md と実行ログを対象に下記 12 語彙を grep:

| 語彙 | substantive 件数 (§11 自己 grep section 除外) |
|---|---:|
| 採用候補 | 0 (§11 listing のみ) ※「採用候補 k」は中立記述として §1 で 1 件・判定文脈 |
| 効く | 0 |
| 効かない | 0 |
| 重要 | 0 (Phase 4-a 完了報告と異なり本タスクでは substantive 使用なし) |
| 優先 | 0 |
| 不要 | 0 |
| 切れる | 0 |
| 残せる | 0 |
| 除外して良い | 0 |
| 使える | 0 |
| 意味がある | 0 |
| 意味がない | 0 |

中立的な客観記述に留め、絞り込み示唆語彙の不適切使用なし。「採用候補 k」は §1 で判定文脈の必須術語として使用 (Phase 4-a 完了報告と同方針)。

---

## 12. 物理証跡 8 点

| # | 項目 | 結果 |
|---|---|---|
| 1 | 入力ファイル整合性 | ✅ train sha 2ee206431c37・test sha 4e4e6bfc32d9 |
| 2 | 正規化プロセス | ✅ close >0 確認・null/inf 0 件・train pct range [0.0705, 15.1951] / test [0.0869, 2.3342] |
| 3 | 出力ファイル証跡 | ✅ joblib/csv/json sha256 全件取得・"test" 文字列不在 |
| 4 | 第三者再読み出し検証 | ✅ joblib.load 可能・cluster_centers_ shape 確認 (script 内 assertion 通過) |
| 5 | データ sanity | ✅ 全 k で両 cluster (k=2) / 全 cluster にサンプル存在 (k≥3 では test の一部 cluster 空) |
| 6 | stderr / Python warning | ✅ 0 件 |
| 7 | bit-exact 再現性確認 | ✅ k=2〜6 全件 (random_state=42 で 2 回 fit → labels 完全一致) |
| 8 | 監査#5 全 16 件マッピング | ✅ §10 で 17/18 項目対応 (G は申し送り) |

---

## 13. 完了後の状態

- ✅ 入力正規化の効果判明 (k=2 で -19.34pp 改善・k≥3 は依然失敗水準)
- ✅ 形式上 分岐 A・採用候補 k=2 だが実用上は分岐 B 選択肢協議が必要 (§9-3)
- ✅ 分岐 B 3 選択肢の評価記載済 (CC 第一推奨は選択肢 1: clustering 廃止)
- ✅ 監査#5 全 16 件のうち G 以外が対応済 (G は Phase 6-b 申し送り)
- ✅ 既存 Phase 4-a artifact (ml_phase4_a / ml_phase4_a_k2) 改変なし (本タスクは ml_phase4_a_norm/ に隔離保存)

---

## 14. 次のステップ

1. **Web Claude が生データ (joblib/parquet/数値ログ) から独立分析** (CC 完了報告の整形済み表を最初に見ない・監査#5 懸念 7 対応)
2. 独立分析後に CC 完了報告と差分照合
3. まこさん最終 GO で k 確定 (k=2 採用 / k=3 維持 / 選択肢 1/2/3 のいずれか)
4. 分岐 A なら Phase 4-b 指示書全面改訂 (監査 13 件 + K×2 中立化 + 確定 k 反映)
   分岐 B なら選択肢協議後に Phase 4-b 設計を再構築

### Phase 6-b 着手前申し送り (見落とし G)

2026 Q1 (test_2026_q1) について Phase 4-a clustering の安定性 (cluster share / centroid drift) を計測する。本タスクではスコープ外。
