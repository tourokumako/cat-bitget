# 正本修正 + Phase 4-a k-means クラスタリング実行 指示書

| 項目 | 値 |
|---|---|
| 発行日 | 2026-05-14 |
| 作成者 | Web Claude (PMエージェント) |
| 承認 | まこさん |
| 関連 commit | d9d322c (K12 LONG refit 完了) / b620011 (K12 LONG refit 指示書) |
| 監査経由 | あり (Web Claude レビュー) |
| 関連必読 | WORKFLOW.md §🔴次のタスク / cc_ml_design_spec.md §3 §4 §8 / .claude/rules/phase_compliance_checklist.md §4a / .claude/instructions/2026-05-14_phase1_k12long_refit_completion.md / handoff_to_web_claude_v4_phase1_7a.md §2 / results/priority_rebuild/leak_incident_20260513.md |

## 本文 (CC への指示)

【複合タスク】正本修正 + Phase 4-a k-means クラスタリング実行
(Web Claudeレビュー済・まこさんGO済 2026-05-14)

## 構造化ルール準拠
- 保存先: .claude/instructions/2026-05-14_phase4a_clustering.md
- 完了報告: .claude/instructions/2026-05-14_phase4a_clustering_completion.md

## 着手前必読 (省略禁止・L-179/L-180/L-181)
1. WORKFLOW.md §🔴次のタスク
2. cc_ml_design_spec.md §3 Exit 設計 / §4 Position 設計 / §8 制約禁止事項
3. phase_compliance_checklist.md §4a (4a.1〜4a.5 全項目)
4. .claude/instructions/2026-05-14_phase1_k12long_refit_completion.md (K12 LONG refit 完了)
5. handoff_to_web_claude_v4_phase1_7a.md §2 (旧 leak Phase 4-a 実績・参考)
6. results/priority_rebuild/leak_incident_20260513.md (背景)

## Step 0-1: 必読ファイル引用 (読んだフリ防止)

a. phase_compliance_checklist.md §4a.1〜4a.5 全文貼り付け
b. cc_ml_design_spec.md §3.3 Exit 選択方法 全文貼り付け
c. handoff_to_web_claude_v4_phase1_7a.md の旧 Phase 4-a 結果 (k=4 / silhouette 0.212 / C0-C3 性質) 引用
d. K12 LONG refit 完了報告から「n_fire 1,660 → 342」の記述引用

各引用が期待値と一致しない/省略 → STOP

---

## タスク 1: 正本の整合性修正 (2 件・Phase 4-a 着手前)

### 1-A. 行数修正 (394,573 → 394,753)

以下 2 ファイルの「394,573 行」記述を実測値「394,753 行」に修正:

- phase_compliance_checklist.md §9 (利用データファイル) labels_mfe_mae_train_2021_2024.parquet
- cc_ml_design_spec.md §1.1 ラベルデータファイル / §1.4 期間分割 / §9 利用データファイル

grep verify:
```bash
grep -rn "394,573\|394573" phase_compliance_checklist.md cc_ml_design_spec.md
```
期待: 修正後は 0 件 (全て 394,753 に置換済)

理由: Phase 0 完了報告・Phase 1 完了報告で実測 394,753 行確認済。正本の数値が古い。

### 1-B. Phase 4-a 入力ファイル名を refit 版に修正

phase_compliance_checklist.md §4a.1 を修正:

旧:
```
| 4a.1 | **fit は train 2021-04〜2024-12 のみ** (test 2025 禁止) | `PREDICTIONS = predictions_train_2021_2024.parquet` |
```

新:
```
| 4a.1 | **fit は train 2021-04〜2024-12 のみ** (test 2025 禁止) | `PREDICTIONS = predictions_train_2021_2024_k12long_refit.parquet` (K12 LONG num_leaves=15 部分採用版・2026-05-14) |
```

理由: K12 LONG refit 採用済 (低ボラ選好問題を入力段階で構造的解消)。旧 predictions を読むと refit が無効化される。

---

## タスク 2: Phase 4-a k-means クラスタリング実行

### Step 0-2. 入力ファイル整合性 verify

```bash
echo "=====Step 0-2 START $(date) ====="
sha256sum results/priority_rebuild/ml_phase1_k12long_refit/predictions_train_2021_2024_k12long_refit.parquet
ls -la results/priority_rebuild/ml_phase1_k12long_refit/predictions_train_2021_2024_k12long_refit.parquet
python3 -c "
import pandas as pd
df = pd.read_parquet('results/priority_rebuild/ml_phase1_k12long_refit/predictions_train_2021_2024_k12long_refit.parquet')
print(f'rows={len(df)} cols={len(df.columns)}')
print(f'columns: {df.columns.tolist()}')
"
```

期待:
- rows = 394,753
- cols = 17 (16 予測値 + close)
- period: 2021-04-01 07:55 〜 2024-12-31 23:55

不一致 → STOP

注: 実 parquet 列名は `LONG_MFE_K12` 等 prefix なし。指示書中の `pred_LONG_MFE_K12` 等は概念表記・実装は列名そのまま使用。

### Step 1: k 値の決定 (silhouette 再評価・データ駆動)

k=2〜8 で silhouette score を再評価:

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

# クラスタリング対象 = 16 予測値列 (close 除く)
pred_cols = [c for c in df.columns if c != 'close']
X = df[pred_cols].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

for k in range(2, 9):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    sil = silhouette_score(X_scaled, labels, sample_size=20000, random_state=42)
    print(f'k={k}: silhouette={sil:.4f}, cluster sizes={...}')
```

判定:
- silhouette 最大の k を採用候補
- cluster サイズ偏り (1 cluster が極端に小さい等) も考慮
- 旧 leak k=4 (silhouette 0.212) との比較も記録

### Step 2: 採用 k で k-means fit (train のみ)

```python
km = KMeans(n_clusters=採用k, random_state=42, n_init=10)
km.fit(X_scaled)
joblib.dump(scaler, 'results/priority_rebuild/ml_phase4_a/scaler_train_2021_2024.joblib')
joblib.dump(km, 'results/priority_rebuild/ml_phase4_a/kmeans_k{採用k}_train_2021_2024.joblib')
```

phase_compliance §4a.4: artifact 名に "test" 含まない。

### Step 3: cluster 性質分析 + サンプル数チェック

```python
df['cluster'] = km.labels_
cluster_profile = df.groupby('cluster')[pred_cols].mean()
cluster_sizes = df['cluster'].value_counts().sort_index()
```

#### K12 LONG サンプル数チェック (2026-05-14 まこさん確定・A案)

K12 LONG refit は n_fire が 1,660 → 342 に激減。各 cluster での K12 LONG q99 発火足のサンプル数:

```python
ratio_k12_long = df['LONG_MFE_K12'] / df['LONG_MAE_K12']
q99_thr = ratio_k12_long.quantile(0.99)
k12_long_q99_mask = ratio_k12_long >= q99_thr
k12_long_q99_by_cluster = df[k12_long_q99_mask]['cluster'].value_counts().sort_index()
```

監査 #2 基準:
- 各 cluster の K12 LONG q99 サンプル数 ≥ 100 → 統計的に有意
- 30〜99 → 仮説レベル (⚠️ 記録・Phase 4-b で注意)
- < 30 → 根拠不足 (❌ Phase 4-b Exit 設計で該当 cluster の K12 LONG 扱いに注意)

### Step 4: K96 SHORT q99 フォールバック判定 (phase_compliance §4a.5)

```python
ratio_k96_short = df['SHORT_MFE_K96'] / df['SHORT_MAE_K96']
q99_thr_k96 = ratio_k96_short.quantile(0.99)
k96_short_q99_mask = ratio_k96_short >= q99_thr_k96
# 各 cluster の実 MFE/MAE 比 (K96 SHORT q99 発火足のみ)
labels_train = pd.read_parquet('results/priority_rebuild/labels_mfe_mae_train_2021_2024.parquet')
for cl in sorted(df['cluster'].unique()):
    cl_mask = k96_short_q99_mask & (df['cluster'] == cl)
    if cl_mask.sum() > 0:
        real_mfe = labels_train.loc[cl_mask, 'SHORT_MFE_K96'].mean()
        real_mae = labels_train.loc[cl_mask, 'SHORT_MAE_K96'].mean()
        ...
```

§4a.5 判定:
- K96 SHORT q99 が独立 cluster に分離 → その cluster を no-trade 候補としてマーク
- 混在 cluster で実 MFE/MAE 比 < 1.0 → その cluster を no-trade 候補としてマーク
- フォールバック発動時の年損失見込み $169,400 (9.6%)・全12ヶ月 $1,900 確保継続

### Step 5: valid / test 2025 への apply (transform/predict のみ・再 fit 禁止)

phase_compliance 4a.3 準拠:

```python
df_test = pd.read_parquet('results/priority_rebuild/ml_phase1/predictions_test2025.parquet')
X_test = df_test[pred_cols].values
X_test_scaled = scaler.transform(X_test)
df_test['cluster'] = km.predict(X_test_scaled)
df_test.to_parquet('results/priority_rebuild/ml_phase4_a/predictions_test2025_clustered.parquet')
```

注: predictions_test2025_k12long_refit.parquet があればそちらを apply 対象とする。

## 物理証跡 8 点

1. 入力ファイル整合性 (Step 0-2・refit 版 sha256・394,753 行)
2. silhouette 評価プロセス (k=2〜8 全 score + cluster sizes)
3. 出力ファイル証跡 (scaler/km joblib の sha256・"test" 文字列不在確認)
4. 第三者再読み出し検証 (joblib.load → km.n_clusters / cluster_centers_ 形状確認)
5. データ sanity (cluster ラベルの分布・全 cluster にサンプルが入っているか)
6. stderr / Python warning 全件
7. 同コマンド bit-exact 再現性確認 (random_state=42 固定で 2 回実行 → labels 一致)
8. K12 LONG サンプル数チェック (Step 3) + K96 SHORT q99 フォールバック判定 (Step 4)

## 完了報告必須証跡 5 点

1. **コード総点検 grep 結果**
   - `grep -rn "394,573\|394573" phase_compliance_checklist.md cc_ml_design_spec.md` (修正後 0 件)
   - `grep -n "k12long_refit" phase_compliance_checklist.md` (§4a.1 修正確認)
   - `ls results/priority_rebuild/ml_phase4_a/*.joblib | grep -i test` (ゼロ件・phase_compliance 4a.4)
2. **数値の二重提示**
   - silhouette 評価表 (k=2〜8) + 採用 k の根拠
   - cluster 性質プロファイル (16 予測値平均)
   - K12 LONG q99 / K96 SHORT q99 の cluster 別分散
3. **成果物ファイル実体** (sha256 + 行数 + 更新時刻)
   - scaler_train_2021_2024.joblib
   - kmeans_k{採用k}_train_2021_2024.joblib
   - silhouette_evaluation.csv
   - predictions_test2025_clustered.parquet
4. **実行ログ** (所要・終了コード・Python warnings 全件)
5. **絞り込み示唆語彙 自己 grep 結果** (no matches 含む)

## 完了後の状態

- 正本 2 ファイルの行数・入力ファイル名が修正済
- silhouette 再評価で leak フリー最適 k 確定
- k-means fit 完了 (train のみ・joblib 保存・"test" 文字列不在)
- cluster 性質プロファイル判明
- K12 LONG サンプル数チェック完了 (監査 #2 基準で判定)
- K96 SHORT q99 フォールバック判定完了 (§4a.5)
- test 2025 への apply 完了
- Phase 4-b (Exit 設計) 着手準備完了

## 次のステップ

完了報告受領 → Web Claude が silhouette 評価・cluster 性質・サンプル数チェックを独立評価 →
まこさん最終 GO → Phase 4-b (Exit 設計) 着手指示書発行
