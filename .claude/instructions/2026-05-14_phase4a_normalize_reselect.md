# 【タスク】Phase 4-a 入力正規化 + k 再選定 (監査#5 全 16 件反映)

(監査エージェント審査済・Web Claude レビュー済・まこさん GO 済 2026-05-14)

## 構造化ルール準拠

- 保存先: .claude/instructions/2026-05-14_phase4a_normalize_reselect.md
- 完了報告: .claude/instructions/2026-05-14_phase4a_normalize_reselect_completion.md

## 着手前必読 (省略禁止・L-179/L-180/L-181)

1. WORKFLOW.md §🔴次のタスク
2. phase_compliance_checklist.md §4a (4a.1〜4a.5)
3. cc_ml_design_spec.md §3 Exit 設計
4. .claude/instructions/2026-05-14_phase4a_clustering_completion.md (元 Phase 4-a)
5. .claude/instructions/2026-05-14_phase4a_k2_revisit_completion.md (k=2 vs k=3)
6. results/priority_rebuild/leak_incident_20260513.md (背景)

## Step 0-1: 必読ファイル引用 (読んだフリ防止)

a. phase_compliance_checklist.md §4a.1〜4a.5 全文貼り付け
b. 元 Phase 4-a 完了報告 Step 1 silhouette 評価表 (k=2〜8) 引用
c. k=2 vs k=3 完了報告の stability 比較表引用

各引用が期待値と一致しない/省略 → STOP

## 背景 (監査#5 結果)

Phase 4-a の k=2/k=3 はどちらも train/test cluster share 乖離が 35pp+ で
「clustering が外挿に失敗している危険水域」(統計常識は 10pp 以内)。

根本原因 (監査#5 懸念 2): k-means 入力の 16 予測値が USD 絶対額。
BTC 価格が train (2021-2024 / 約$58k→$94k) と test (2025 / 約$100k+) で変化したため、
同じ予測値の絶対量が異なる relative 意味を持ち cluster 境界がドリフトする
(non-stationary input space の典型的失敗パターン)。

本タスク: 入力を close 価格比 % に正規化して再 fit・stability 改善を検証・
改善後に k を再選定する。監査#5 全 16 件の対応を本指示書に組み込む。

---

## Step 1: 入力正規化 (監査#5 懸念 2 — 根本対応)

16 予測値を close 価格比 % に変換:

```python
import pandas as pd
df_train = pd.read_parquet('results/priority_rebuild/ml_phase1_k12long_refit/predictions_train_2021_2024_k12long_refit.parquet')
pred_cols = [c for c in df_train.columns if c.startswith('pred_')]

# 各予測値を close で除算して % 化
for c in pred_cols:
    df_train[c + '_pct'] = df_train[c] / df_train['close'] * 100

pct_cols = [c + '_pct' for c in pred_cols]
# 正規化版を保存
df_train.to_parquet('results/priority_rebuild/ml_phase4_a_norm/predictions_train_normalized.parquet')
```

test 2025 / 2026 Q1 も同じ変換 (それぞれの close で除算)。

注意: 正規化は「予測値 ÷ その足の close」。train の close で test を割らない (各期間の実 close を使う)。

---

## Step 2: 正規化版で k=2〜6 を stability 込みで再評価 (監査#5 懸念 5・見落とし A/B 対応)

旧 Phase 4-a は silhouette だけで k≥4 を棄却したが、今回は stability も評価軸に入れる。
k=2,3,4,5,6 の全てで以下を測定:

### 2-A. 各 k の評価指標 (監査#5 懸念 8 — stability 定義拡張)

| 指標 | 定義 |
|---|---|
| silhouette | 従来通り |
| share_max_diff | max(\|train_share[c] - test_share[c]\|) |
| share_sum_diff | Σ\|train_share[c] - test_share[c]\| |
| **centroid_drift** | 各 cluster で ‖center_train - center_test‖ / ‖center_train‖ ※監査#5 懸念 8 |
| **within_cluster_pred_std_diff** | cluster 内予測値 std の train/test 差 ※監査#5 懸念 8 |

### 2-B. robustness 確認 (監査#5 見落とし B)

各 k について random_state を 42 以外に 3 つ (例: 0, 1, 100) でも fit し、
cluster 構造が安定するか (share・centroid が大きく変わらないか) 確認。

### 2-C. bit-exact 再現性 (監査#5 見落とし A)

採用候補 k について random_state=42 で 2 回 fit → labels 完全一致を確認。
k=3 で前回未測定だった分も今回測定。

出力: results/priority_rebuild/ml_phase4_a_norm/k_evaluation_normalized.csv

---

## Step 3: 正規化の効果判定 (監査#5 懸念 1 — 危険水域脱却の判定)

正規化前 (USD 絶対額) と正規化後 (% 換算) で stability を比較:

| | 正規化前 | 正規化後 |
|---|---|---|
| k=2 share_max_diff | 35.49pp | XX |
| k=3 share_max_diff | 44.18pp | XX |
| (k=4,5,6 も) | - | XX |

判定基準 (監査#5 統計常識):

- share_max_diff ≤ 10pp → ✅ 安定 (clustering 機能)
- 10〜20pp → ⚠️ 要警戒
- 20pp 超 → ❌ clustering 失敗水準

---

## Step 4: 分岐判定

### 分岐 A: 正規化で改善 (どれかの k で share_max_diff ≤ 20pp)

→ その k を採用候補とし、Step 5 (詳細検証) へ進む

### 分岐 B: 正規化しても全 k で 20pp 超 (監査#5 見落とし D/I/J — plan B)

→ Step 5 をスキップし、以下 3 選択肢を CC が評価してレポート:

- 選択肢 1: clustering 廃止・per-entry prediction-based Exit (§4b.4-b 拡張) で代替
- 選択肢 2: k=2 と k=3 を Phase 4-b で並走させ Phase 5 実 PnL で比較
- 選択肢 3: regime 特徴量 (1d ichimoku 等) を k-means 入力に追加
- → Web Claude + まこさん協議で選択

---

## Step 5: 採用候補 k の詳細検証 (分岐 A の場合のみ)

### 5-A. train 内 前半/後半 split 安定性 (監査#5 見落とし E)

train (2021-2024) を前半 (2021-2022) / 後半 (2023-2024) に分け、
前半 fit → 後半 apply で share_max_diff を測定。時系列ドリフト耐性の確認。

### 5-B. cluster 移動の train→test 一致率 (監査#5 懸念 4)

K96 SHORT q99・K12 LONG q99 等の主要 Entry が
train で属した cluster と test で属する cluster の一致率を測定。
不一致率 > 50% の組合せは「cluster_best_exit が逆 cluster で選定」リスク → リストアップ。

### 5-C. 新規 cluster (外挿) 検知 (監査#5 見落とし F)

test 2025 の各 entry の per-sample inertia (最近接 centroid との距離) を算出。
train の inertia 分布から大きく外れる entry (外挿) の割合を報告。

### 5-D. cluster が市場性質を捉えているか検証 (監査#5 見落とし H)

各 cluster 内で LONG/SHORT の実 PnL profitability に有意差があるか
(cluster ごとに性質が異なることの確認)。

### 5-E. 各 k で「失う性質」の定量化 (監査#5 懸念 6)

k を下げると統合される cluster の性質 (例: k=3 cluster 2 = 高ボラ LONG 強) について、
その性質グループの月次楽観 PnL 寄与を見積もり。
「k を下げて失う額」を定量化。

### 5-F. K12 LONG refit 混在影響 (監査#5 見落とし C)

K12 LONG のみ num_leaves=15・他 15 ラベル num_leaves=31 の混在モデルである事実を明記。
混在が clustering 安定性に与える影響を観察 (定量化できる範囲で)。

---

## Step 6: 採用根拠の整理 (監査#5 懸念 3 — 原則違反排除)

k 採用根拠から以下を除外:

- 「Exit 設計組合せ数が少ない (シンプル)」= 効率・実装コストは判断根拠にしない

採用根拠は以下の定量指標のみ:

- silhouette / share_max_diff / centroid_drift / 一致率 / 失う性質の定量額

---

## 監査#5 全 16 件 対応マッピング (本指示書での行き先・取りこぼし防止)

| 監査項目 | 本指示書での対応 |
|---|---|
| 懸念 1 (危険水域) | Step 3 判定基準 (10/20pp) |
| 懸念 2 (USD 絶対額) | Step 1 正規化本体 |
| 懸念 3 (シンプル化を根拠) | Step 6 採用根拠から除外 |
| 懸念 4 (cluster 移動) | Step 5-B 一致率測定 |
| 懸念 5 (k≥4 棄却) | Step 2 k=2〜6 評価 |
| 懸念 6 (失う性質 未定量) | Step 5-E 定量化 |
| 懸念 7 (Web Claude 独立性) | Web Claude 側手順変更 (下記) |
| 懸念 8 (stability 定義限定) | Step 2-A centroid_drift 追加 |
| 見落とし A (bit-exact k=3) | Step 2-C |
| 見落とし B (n_init ランダム性) | Step 2-B robustness |
| 見落とし C (refit 混在影響) | Step 5-F |
| 見落とし D (clustering 必要性) | Step 4 分岐 B 選択肢 1 |
| 見落とし E (train 内 split) | Step 5-A |
| 見落とし F (新規 cluster 検知) | Step 5-C |
| 見落とし G (2026 Q1 安定性) | **Phase 6-b 着手前タスクとして申し送り (本タスクでは実施しない)** |
| 見落とし H (市場性質を捉えるか) | Step 5-D |
| 見落とし I (plan B なし) | Step 4 分岐 B |
| 見落とし J (k=2/k=3 並走) | Step 4 分岐 B 選択肢 2 |

## 物理証跡

1. 入力ファイル整合性 (正規化前後の sha256・行数)
2. 正規化プロセス (16 列の close 除算・正規化後の値域確認)
3. 出力ファイル証跡 (正規化版 parquet・k_evaluation_normalized.csv の sha256)
4. 第三者再読み出し検証 (joblib.load → 採用 k の cluster_centers_ 形状)
5. データ sanity (正規化後の null 率・無限大値がないか close=0 除算チェック)
6. stderr / Python warning 全件
7. 同コマンド bit-exact 再現性確認 (Step 2-C)
8. 監査#5 全 16 件マッピングの各項目が完了報告で言及されているか

## 完了報告必須証跡 5 点

1. **コード総点検 grep 結果**
   - `ls results/priority_rebuild/ml_phase4_a_norm/*.joblib | grep -i test` (ゼロ件)
2. **数値の二重提示**
   - 正規化前後の stability 比較表 + k=2〜6 評価表
3. **成果物ファイル実体** (sha256 + 行数 + 更新時刻)
   - predictions_train_normalized.parquet
   - k_evaluation_normalized.csv
   - 採用候補 k の joblib (分岐 A の場合)
4. **実行ログ** (所要・終了コード・Python warnings 全件)
5. **絞り込み示唆語彙 自己 grep 結果** (no matches 含む)

## 完了後の状態

- 入力正規化の効果が判明 (stability 改善したか)
- 分岐 A: 採用候補 k 確定 + 詳細検証完了
- 分岐 B: clustering 廃止 / 並走 / regime 特徴量追加 の 3 選択肢が評価済
- 監査#5 全 16 件のうち G 以外が対応済 (G は Phase 6-b 申し送り)

## 次のステップ

完了報告受領 → **Web Claude が生データ (joblib/parquet/数値ログ) から独立分析**
(CC 完了報告の整形済み表を最初に見ない・監査#5 懸念 7 対応) →
独立分析後に CC 完了報告と差分照合 → まこさん最終 GO →
分岐 A なら Phase 4-b 指示書全面改訂 / 分岐 B なら選択肢協議
