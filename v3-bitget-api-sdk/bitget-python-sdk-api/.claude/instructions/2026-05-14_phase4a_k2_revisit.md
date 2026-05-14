# 【タスク】Phase 4-a 再検討: k=2 vs k=3 比較評価

(監査結果反映・Web Claude レビュー済・まこさん GO 済 2026-05-14)

## 構造化ルール準拠

- 保存先: .claude/instructions/2026-05-14_phase4a_k2_revisit.md
- 完了報告: .claude/instructions/2026-05-14_phase4a_k2_revisit_completion.md

## 着手前必読 (省略禁止・L-179/L-180/L-181)

1. WORKFLOW.md §🔴次のタスク
2. phase_compliance_checklist.md §4a (4a.1〜4a.5)
3. .claude/instructions/2026-05-14_phase4a_clustering_completion.md (Phase 4-a 完了報告)
4. results/priority_rebuild/leak_incident_20260513.md (背景)

## Step 0-1: 必読ファイル引用 (読んだフリ防止)

a. Phase 4-a 完了報告 Step 1 silhouette 評価表 (k=2〜8) 全文引用
b. Phase 4-a 完了報告 Step 5 test 2025 apply 結果 (cluster 別 share) 引用
c. phase_compliance_checklist.md §4a.1〜4a.5 全文貼り付け

各引用が期待値と一致しない/省略 → STOP

## 背景 (監査結果・見落とし J)

Phase 4-b 指示書監査で以下が指摘された:

- k=3 採用時、cluster 1 が train 48.7% → test 2025 4.5% に激減 (10 分の 1 以下)
- これは「Phase 4-a のクラスタリングが train 期間の regime に過適応した」可能性
- silhouette は k=2 (0.5075) と k=3 (0.5100) でほぼ同じ (差 0.0025)
- → k=2 縮退で cluster の train/test 安定性が向上するか検証する価値あり

本タスクは「k=2 vs k=3 のどちらが train/test 安定性が高いか」をデータで判定する。
実装はほぼゼロ (kmeans 再 fit のみ)。

## Step 1: k=2 で k-means 再 fit

Phase 4-a と同じ手順で k=2 のみ実行:

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd, joblib

df_train = pd.read_parquet('results/priority_rebuild/ml_phase1_k12long_refit/predictions_train_2021_2024_k12long_refit.parquet')
pred_cols = [c for c in df_train.columns if c.startswith('pred_')]
X_train = df_train[pred_cols].values

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

km2 = KMeans(n_clusters=2, random_state=42, n_init=10)
km2.fit(X_train_scaled)
df_train['cluster_k2'] = km2.labels_

# joblib 保存 (artifact 名 "train" 含む・"test" 禁止 = §4a.2/4a.4)
joblib.dump(scaler, 'results/priority_rebuild/ml_phase4_a_k2/scaler_train_2021_2024.joblib')
joblib.dump(km2, 'results/priority_rebuild/ml_phase4_a_k2/kmeans_k2_train_2021_2024.joblib')
```

## Step 2: k=2 を test 2025 に apply (transform/predict のみ・再 fit 禁止)

```python
df_test = pd.read_parquet('results/priority_rebuild/ml_phase1/predictions_test2025_k12long_refit.parquet')
# (refit 版 test predictions が無い場合は predictions_test2025.parquet を使用・その旨明記)
X_test = df_test[pred_cols].values
X_test_scaled = scaler.transform(X_test)
df_test['cluster_k2'] = km2.predict(X_test_scaled)
```

## Step 3: k=2 vs k=3 の train/test 安定性比較

### 3-A. cluster share の train/test 比較

| | k=3 (現行) | k=2 (新規) |
|---|---|---|
| cluster share train | (Phase 4-a 完了報告から) | (Step 1 結果) |
| cluster share test | (Phase 4-a 完了報告から) | (Step 2 結果) |
| 最大乖離 (train→test の share 変化) | cluster 1: 48.7%→4.5% (Δ-44.2pp) | (算出) |

### 3-B. 安定性スコア算出

各 k で「train share と test share の乖離」を定量化:

```python
# 各 cluster の |train_share - test_share| の合計 or 最大値
def stability_score(train_shares, test_shares):
    diffs = [abs(tr - te) for tr, te in zip(train_shares, test_shares)]
    return {'max_diff': max(diffs), 'sum_diff': sum(diffs)}

# k=3: max_diff, sum_diff
# k=2: max_diff, sum_diff
```

判定: max_diff / sum_diff が小さいほど train/test 安定

### 3-C. silhouette 比較 (再掲)

| k | silhouette | 安定性 max_diff | 安定性 sum_diff |
|---|---|---|---|
| 2 | 0.5075 | (Step 3-B) | (Step 3-B) |
| 3 | 0.5100 | 44.2pp (既知) | (算出) |

### 3-D. K12 LONG q99 / K96 SHORT q99 のサンプル数 (k=2 版)

k=2 で各 cluster の K12 LONG q99 / K96 SHORT q99 サンプル数を算出:

- 監査 #2 基準 (≥100 で統計的有意) を k=2 でも満たすか
- k=3 で問題だった「K96 SHORT q99 が train cluster 1 → test cluster 0 移動」が k=2 でどうなるか

## Step 4: 推奨判定

以下を CC が提案 (Web Claude が独立評価する):

| 判定軸 | k=2 | k=3 | 優位 |
|---|---|---|---|
| silhouette | 0.5075 | 0.5100 | k=3 (僅差) |
| train/test 安定性 (max_diff) | XX | 44.2pp | ? |
| K12 LONG q99 サンプル数 (全 cluster ≥100) | ? | ✅ | ? |
| K96 SHORT q99 の cluster 移動問題 | ? | ❌ (44 件→1000 件) | ? |
| cluster 数の少なさ (Exit 設計組合せ数) | 2×4×2=16 | 3×4×2=24 | k=2 (シンプル) |

CC 推奨 (k=2 採用 / k=3 維持) + 根拠を完了報告に記載。

## 物理証跡

1. 入力ファイル整合性 (predictions train/test refit 版 sha256)
2. k=2 fit プロセス (inertia / n_iter / silhouette)
3. 出力ファイル証跡 (k=2 joblib の sha256・"test" 文字列不在)
4. 第三者再読み出し検証 (joblib.load → k=2 / cluster_centers_ shape (2,16))
5. データ sanity (k=2 両 cluster にサンプル存在)
6. stderr / Python warning 全件
7. 同コマンド bit-exact 再現性確認 (random_state=42 固定で 2 回実行 → labels 一致)
   ※ Phase 4-a で省略された項目・今回は必須実施
8. k=2 vs k=3 安定性比較 (Step 3) + サンプル数チェック (Step 3-D)

## 完了報告必須証跡 5 点

1. **コード総点検 grep 結果**
   - `ls results/priority_rebuild/ml_phase4_a_k2/*.joblib | grep -i test` (ゼロ件)
2. **数値の二重提示**
   - k=2 vs k=3 比較表 (silhouette / 安定性 / サンプル数 / cluster 移動)
3. **成果物ファイル実体** (sha256 + 行数 + 更新時刻)
   - scaler_train_2021_2024.joblib (k=2 版)
   - kmeans_k2_train_2021_2024.joblib
   - k2_vs_k3_comparison.csv
4. **実行ログ** (所要・終了コード・Python warnings 全件)
5. **絞り込み示唆語彙 自己 grep 結果** (no matches 含む)

## 完了後の状態

- k=2 クラスタリング完了 (train fit + test apply)
- k=2 vs k=3 の train/test 安定性が定量比較済
- K12 LONG q99 / K96 SHORT q99 のサンプル数が k=2 でも判明
- 「k=2 採用 or k=3 維持」の判断材料が揃う

## 次のステップ

完了報告受領 → Web Claude が独立評価 (CC 完了報告の留意事項は後で読む・先に独自分析する手順を採用) →
まこさん最終 GO で k 確定 → Phase 4-b 指示書を全面改訂 (監査 13 件 + K×2 中立化 + 確定 k 反映)
