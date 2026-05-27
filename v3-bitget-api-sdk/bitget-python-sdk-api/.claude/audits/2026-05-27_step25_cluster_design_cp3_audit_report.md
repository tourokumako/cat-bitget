# 工程 [2.5] cluster 分類 詳細設計 CP3 監査結果

監査実施日: 2026-05-27
監査者: Plan サブエージェント (cold start・独立監査・メインセッション CC context 非共有)
依頼書: `.claude/audits/inputs/2026-05-27_step25_cluster_design_cp3_audit_request.md`

---

## Step -1 監査対象の型宣言

監査対象 = **混合型 (= 文書型 + 数値型 + アルゴリズム型)**

- **文書型**: `ml_pipeline_baseline_v1.md` v3.8 §6.3.0〜§6.3.7 全 7 サブセクション (= L1571〜L2340 = 約 770 行・実装スクリプトはない段階)
- **数値型**: silhouette > 0.3 / 純増分 (b)/(a) ≥ 1.5× / PCA 50-100 主成分 / k ∈ {3, 4, 5} / 偏り ≥ 5% / Pearson < 0.5 / 暫定 multiplier 値
- **アルゴリズム型**: k-means + k-means++ + Euclidean + Gaussian kernel 確率変換 + RobustScaler fold 別 fit + 4 軸 (TP_prob / MFE / SL_prob / 保有時間) post-hoc 命名
- 監査区分: CP3 (= 第 3 回詳細設計監査・実装着手前)
- 結果出力: 業界整合性 + cat-bitget 固有制約整合性 + 同型バイアス検出 + leak 防止経路 + 内部一貫性 verify。月次 NET ≥ $1,900 達成可能性判定は本監査対象外。

---

## Step 0 指摘前提確認

### 0.1 依頼書本文 view 証跡

- 依頼書 wc -l = **304 行** (一致)
- 監査観点 = 一般 ①〜⑦ + 本監査固有 Q1〜Q7 + 外部検索 7 件 (= C1〜C7)
- 結果フォーマット = 7 セクション (Step -1 / Step 0 / 観点・Q 所見 / 外部検索サマリー / 総合判定 / 改善方向性 / CC プロセス欠陥対策)
- スコープ外明示 = 実装着手後の Stage 1〜4 実測値判定 / [3]/[4] 詳細設計完了後別監査 / Phase 5/6-b Replay 月次 NET 達成判定

### 0.2 着手前必読 7 件 view 証跡

| # | ファイル | wc -l | 1 行要約 |
|---|---|---|---|
| 1 | ml_pipeline_baseline_v1.md §6.3.0〜§6.3.7 (= 本監査主要対象) | 2367 | 概要 + 7 サブセクション = 評価 4 段階 (silhouette > 0.3 + 純増分 ≥ 1.5×) / k-means 単体 + Gaussian kernel / 案 b 全投入 2,666 列 + PCA 50-100 / k ∈ {3,4,5} data-driven / 4 軸 post-hoc 命名 / 主要 7 列 + 派生 one-hot + entry_id merge / leak 6 経路 + fit train のみ |
| 2 | ml_pipeline_baseline_v1.md §6.1.1〜§6.1.6 (= regime ensemble 同型比較) | 2367 (同ファイル) | 4 段階評価 / HMM v15 再調整 + 3 判定器 ensemble (HMM + 固定ルール + k-means k=3) / soft voting + isotonic regression / 出力 6 列 + merge_asof backward causal alignment |
| 3 | ml_pipeline_baseline_v1.md §6.2.1〜§6.2.8 (= Entry ML 同型比較) | 2367 (同ファイル) | 4 段階 + base line 旧 v9 月 $370 / LightGBM 56 個独立 + MultiOutputRegressor / Triple Barrier K 別 ATR_pct multiplier / 案 A 統合 regime 6 列 / 5 fold + embargo 2 day / Optuna + L1/L2 / ルール集約 + 短期 K 重視 + threshold 0.6 / leak 4 点 verify |
| 4 | CP1 監査結果 (regime ensemble §6.1) | 381 | Verdict PIVOT・Critical 2 (= C1 ensemble キャリブレーション欠陥 / C2 ATR 絶対値 250/100 価格非依存性違反) + Major 3 + Minor 2 件全 7 件採用支持 + cc_role §1.4.6.1 改善 10/11/12 追加 |
| 5 | CP2 監査結果 (Entry ML §6.2) | 366 | Verdict PIVOT・Critical 2 (= class_weight キャリブレーション欠陥 / 集約式 scale 不整合) + Major 2 + Minor 2 件全 6 件採用支持 + cc_role §1.4.6.1 メタガード 13/14/15 追加 |
| 6 | industry_benchmark_knowledge_base.md §2.3 戦略並立 | 420 | 戦略並立 / 多戦略 ensemble 業界実証 1.2-1.8× (実用) / Sharpe 改善 80-91% (5-model ensemble) / Mom + Mean-Reversion Sharpe 1.71 / Square Root Rule (無相関前提) / 3-5 cluster 並立で 1.3-1.5× 目安 (= cluster=3 想定) |
| 7 | phase_compliance_checklist.md §4a.1〜§4a.5 | 224 | §4a.1 fit train 2021-04〜2024-12 のみ / §4a.2 scaler/km joblib に train 含む / §4a.3 valid/test 期間は transform/predict のみ / §4a.4 artifact 名 *test* 禁止 / §4a.5 K96 SHORT q99 フォールバック |

### 0.3 §6.3 設計本体の事実 verify (= 依頼書 §監査対象の事実データ vs L1571-L2340 照合)

| 依頼書本文記載 | §6.3 実本文 | 一致 |
|---|---|---|
| §6.3.0 = 工程 [2] 後段・教師なし学習・戦略並立 1.5× レバー寄与・議論順序 §6.3.3 → §6.3.2 → §6.3.4 → §6.3.1 → §6.3.5 → §6.3.6 → §6.3.7 | L1571-L1577 | OK |
| §6.3.1 = 4 段階 (silhouette > 0.3 + inertia + 偏り ≥ 5% + regime 相関 Pearson < 0.5 + 旧 14 列版比較 → 視認 + Exit 抜き PnL proxy → 純増分 ≥ 1.5× → 月次 NET ≥ $1,900) | L1579-L1685 | OK |
| §6.3.2 = k-means 単体 + k-means++ + Euclidean + Gaussian kernel σ = cluster median・第二段階 GMM/HDBSCAN/ensemble 検討経路 | L1689-L1789 | OK |
| §6.3.3 = 案 b 全投入 2,666 列 (= 56 + 2,604 + 6) + PCA 50-100 主成分 + RobustScaler fold 別 fit + regime 統合 | L1793-L1891 | OK |
| §6.3.4 = k ∈ {3, 4, 5} 並列試行 + silhouette 最大 + elbow + 偏り ≥ 5% + 業界経験則 3-5 cluster | L1895-L1990 | OK |
| §6.3.5 = train 期間で 4 軸 (TP_prob/MFE/SL_prob/保有時間) post-hoc 命名 → test mapping 適用のみ・命名形式 snake_case 英語 | L1994-L2094 | OK |
| §6.3.6 = 主要 7 列 (cluster_id + cluster_prob_X + cluster_label + cluster_confidence + cluster_silhouette) + 派生 one-hot 列 + parquet 保存 + entry_id ベース merge | L2098-L2219 | OK |
| §6.3.7 = leak 6 経路 (k-means fit / PCA fit / scaler fit / Entry ML 出力 leak / k 探索 / 命名) + artifact 名 train 含む必須 + 起動時 assertion + Stage 1 で 6 項目 verify | L2223-L2340 | OK |

依頼書記載は §6.3 実本文と全項目で一致。**判断材料として有効**。

---

## 観点 ①〜⑦ + Q1-Q7 の所見

### 観点 ① 統計学的妥当性: **FAIL (Critical)**

1. **silhouette > 0.3 を 2,666 列 PCA 50-100 後でも適用する妥当性に重大な統計学的欠陥 (Critical)**: 外部検索 C7 で「Silhouette analysis ... can be challenging in very high-dimensional spaces」「low averages (e.g., below 0.5) highlight subgroups with inadequate cohesion」と明示。PCA 50-100 後でも 50 次元以上は **euclidean distance ベース silhouette が curse of dimensionality の影響を強く受ける**領域。§6.3.1 で「silhouette > 0.3 = scikit-learn 業界 minimum」と言及するが、これは 2-10 次元の低次元用途の minimum 値で、**50-100 次元 PCA 後の業界実証根拠ゼロ**。0.3 を crypto 高次元 cluster で適用する根拠が業界整合性 verify されていない (= CP1 監査 観点 (1) と同型問題)。

2. **k-means の Gaussian kernel σ = cluster median 距離の数値根拠が §6.1.5 同型継承のみ (Major)**: §6.3.2 で「Gaussian kernel `exp(-d²/2σ²)`・σ = cluster median 距離・§6.1.5 と同型」と書くが、§6.1.5 自体は CP1 監査 Critical-1 でキャリブレーション欠陥として指摘され isotonic regression 追加対策中。**cluster 用途では isotonic regression キャリブレーションが §6.3.2 / §6.3.6 に明記されていない**。Stage 1 評価に Brier score / reliability diagram / ECE の指定もない (= CP1 監査 Critical-1 / CP2 監査 Critical-1 と同型問題の再演)。後段 [3] Sizing で cluster_prob_X 確率値を Half-Kelly 入力等に使う場合、未キャリブレーション確率の直接消費でリスク。

3. **Pearson 相関 < 0.5 (regime cluster との予測誤差相関) 閾値の数値根拠が「KB §2.3 Square Root Rule 前提」のみ (Major)**: §6.3.1 Stage 1 表で「regime cluster との予測誤差相関 Pearson < 0.5」とあるが、Square Root Rule は「**戦略間 (= ポジション level)** の相関」で「**判定器間予測誤差** の相関」とは概念が異なる。両者は別レイヤーで、無相関 portfolio Sharpe ∞ は portfolio constituent level の話。§6.3.1 で「regime cluster との予測誤差相関」を測ることが「重複削減」に直結する論理連鎖が verify されていない (= 統計学的に閾値根拠が薄弱)。

4. **PCA 50-100 主成分の数値根拠が「分散 95% 説明」前提だが、cat-bitget 2,666 列の分散説明 95% に何主成分が必要かの pre check ゼロ (Major)**: §6.3.3 で「PCA 50-100 主成分・分散 95% 説明」と書くが、Phase 0 v3.1 既存 parquet (= 56 万行 × 1,462 指標 + regime 6 列 + Entry ML 予測値 56) で **暫定 PCA 試算ゼロ**。外部検索 C6 で「PCA components number depends on variance explained」と業界 standard 確認だが、実データで何主成分必要かは事前試算可能 (= cc_role §1.4.6.1 メタガード 13 違反)。

5. **暫定 multiplier 値 (= cluster 効果薄ければ Clustered MDA で 20-50 列) の事前根拠が業界引用のみ**: §6.3.3 data-driven 経路宣言で「Stage 1 で post-pruning 検討」と明記・透明性あり。第一段階固定値の事前根拠は OK。

**結論**: **FAIL (Critical)**。silhouette > 0.3 を高次元用途で適用する業界根拠ゼロ (Critical) + Gaussian kernel キャリブレーション欠陥 (Major・CP1/CP2 同型) + Pearson 相関閾値の論理連鎖 verify ゼロ (Major) + PCA 主成分数 pre check ゼロ (Major) という 4 件の統計学的欠陥が §6.3 全体に貫通。

### 観点 ② リスク管理: **PASS**

1. **0.12 BTC 合計上限への抵触なし**: 本工程は cluster 分類出力工程・ポジション発注は工程 [3]/[5] が担当・直接抵触なし。
2. **cluster 別 [3] Sizing で過大ポジション化リスク**: §6.3.6 出力 7 主要列 + 派生 one-hot 列は [3] Sizing への入力特徴量として渡すのみで、明示的なポジション増減ロジックなし。§1 [3] Sizing 工程の責任範囲・本工程単体ではリスク管理上の構造的欠陥なし。
3. **cluster_silhouette (= 各 trade はみ出し度) を出力する設計**: §6.3.6 で「cluster_silhouette」を出力列に含む・後段がはみ出し度高い trade を size 縮小する経路として有用な情報設計。

**結論**: **PASS**。リスク管理上の構造的欠陥なし。

### 観点 ③ 認知バイアス: **FAIL (Critical)**

1. **L-230 / L-232 / L-235 同型バイアスの §6.3 完全再演 (= CP1/CP2 監査同型問題の 3 回目連続再演) (Critical)**: §6.3.1〜§6.3.7 全 7 サブセクションに「業界 standard verify / 教科書整合 / cat-bitget 固有 verify / 第一段階固定値の事前根拠 / 統計指標と PnL 指標の分離 / 整合性 Q&A / data-driven 経路宣言 / 専門用語補足 / §6.3.X 着地」の 9 ブロック構造が **完全機械的に並列配置**されている。CP2 監査で追加した cc_role §1.4.6.1 メタガード 13/14/15 (= 機械的フォーマット化検出 + 第一段階固定値の事前根拠厳格化 + 設計矛盾自己検出) が **メタガードそのものが機械的フォーマット化された**形で再演 → メタガード追加自体が改善策として効いていない構造的問題。

2. **cat-bitget 固有 verify の定量試算がゼロ (= メタガード 13 違反) (Critical)**: §6.3.1〜§6.3.7 全 7 サブセクションの「cat-bitget 固有 verify」セクションを点検:
   - §6.3.1: 「Phase 4-a 旧実装比較経路: predictions_train_2021_2024.parquet で silhouette score を再計算」= **言及だけで定量試算ゼロ** (= 実際に過去 1 fold データで silhouette pre check していない)
   - §6.3.2: 「Phase 4-a 旧実装振り返り: 分離不十分」「同じ k-means でも入力強化で silhouette score が 0.15-0.20 → > 0.3 期待」= **「期待」だけで pre check ゼロ**
   - §6.3.3: 「定量試算経路: Phase 4-a predictions_train_2021_2024 で 14 列 k-means の silhouette score を再計算・Stage 1 で 2,666 列 PCA 版と比較」= **言及だけで定量試算ゼロ**
   - §6.3.4: 「定量試算経路: Phase 4-a predictions_train_2021_2024 で k=3,4,5 並列 fit → silhouette score 比較を実装着手時に train fold データで pre check」= **言及だけで定量試算ゼロ**
   - §6.3.5: 「定量試算経路: Phase 4-a predictions_train_2021_2024 で 4 軸 cluster 別平均を実装着手時に算出 → 区別がつくか pre check」= **言及だけで定量試算ゼロ**
   - §6.3.6: 「定量試算経路: Phase 4-a predictions_train_2021_2024 の cluster_id 出力に対し、Gaussian kernel で確率変換した場合の確率列分布を実装着手時に train fold で pre check」= **言及だけで定量試算ゼロ**
   - §6.3.7: 「定量試算経路: Phase 4-a artifact predictions_train_2021_2024_k12long_refit.parquet の命名規律と同型化・実装着手時に grep で test 含むファイル名ゼロ件 verify」= **これは命名規律で定量試算ではない**

   → 7 サブセクション全てで **「実装着手時に pre check」とだけ書き、本セッションで定量試算ゼロ**。CP2 監査でメタガード 13 を追加した本旨と完全に逆行。

3. **silhouette 旧 14 列版 0.15-0.20 の数値根拠不明 (= メタガード 14 違反) (Critical)**: §6.3.1 / §6.3.2 で「Phase 4-a 旧 14 列版で 0.15-0.20 を観測 (= 不合格)・新 PCA 版で > 0.3 期待」と書くが、この 0.15-0.20 の実測値の出典が **§6.3 内に提示されていない**。Phase 4-a の実測 silhouette が 0.15-0.20 と「推定されている」だけで、実際は計算されていない (= 依頼書 Q4(c) 指摘事項と同型)。「業界引用 + cat-bitget 過去事例 1 件以上併記」の cat-bitget 過去事例が **架空の推定値**を「実測値のように」書いている = 業界引用の単独依存 + 架空値の二重違反。

4. **業界フレーム逃避癖 (= L-230) の §6.3 再演**: §6.3.2 採用根拠「業界 standard 整合: §6.1.4 regime ensemble でも k-means 採用・同型構造で工程間整合」「Phase 4-a 旧実装の継承」= **業界引用 + 同型継承を採用根拠化**。「entry cluster と regime cluster は目的が異なる」(= §6.3.2 Q1 で自認) のに「同型」を採用根拠にしている論点矛盾。

5. **設計矛盾自己検出 Q&A 自体の機械化 (= メタガード 15 違反)**: §6.3.1 / §6.3.2 / §6.3.3 / §6.3.4 / §6.3.5 / §6.3.6 / §6.3.7 全 7 サブセクションに「整合性 Q&A」が 2 件ずつ機械的並列配置 → 「Q&A 形式」自体が機械的形式に化している。実際に Q&A の内容を点検:
   - §6.3.1 Q1「Stage 3 純増分 1.5× は cluster 数 3-5 の場合に実現可能か?」A1「§2.3 で 1.3-1.5× が目安・1.5× は中央値域で目標として妥当」= **業界引用循環論証** (= 1.5× を妥当と判定する根拠が業界 §2.3 の 1.3-1.5× のみ)
   - §6.3.2 Q1「k-means + 3 判定器 ensemble (regime) と k-means 単体 (entry cluster) は整合する?」A1「両工程は目的が違う」= **「同型継承を採用根拠化」の Q1 と矛盾**
   - §6.3.3 Q1「Phase 1 v6 教訓と §6.3.3 案 b 全投入の整合性は?」A1「整合する」= **再演リスクの自己検出機能していない** (= Phase 1 v6 教訓は Entry ML の話で cluster とは異なる論点軸・整合性 Q&A の趣旨を取り違えている)

**結論**: **FAIL (Critical)**。CP1/CP2 監査同型問題 (= 業界 standard を判断根拠化 + 機械的フォーマット化 + cat-bitget 固有 verify ゼロ) が 3 回目連続再演。**メタガード 13/14/15 追加自体が機械的フォーマット化された** = 構造的に「ガード追加」では止まらない実証。

### 観点 ④ ソフトウェア工学: **PASS (Minor 改善余地)**

1. **artifact 命名規律**: §6.3.7 で `cluster_kmeans_train_2021_2024.joblib` / `pca_train_2021_2024.joblib` / `scaler_train_2021_2024.joblib`・phase_compliance §4a.4「test 文字列禁止・train 含む」と整合・**実装可能**。
2. **起動時 assertion**: §6.3.7 で `assert "train" in artifact_path and "test" not in artifact_path` 明示・phase_compliance §6b.4 / §7c.9 同型・**実装可能**。
3. **Pipeline 化の明示 (Minor)**: §6.3.3 で「RobustScaler fold 別 fit + Pipeline 化」と書かれているが、scikit-learn Pipeline (= scaler → pca → kmeans の連結) の具体的な class 構造が §6.3.X 内に明示されていない (Minor)。外部検索 C5 で「scikit-learn pipeline ... ideal for use in cross-validation and hyper-parameter tuning functions」と業界 standard。実装時に Pipeline 化が必須だが、設計時点の指定具体性が低い。
4. **parquet 出力時 assert no look-ahead (Minor)**: §6.3.6 で `assert df['entry_ts'] <= df['cluster_predict_ts']` と明示・**実装可能**。
5. **PCA fit の Pipeline 化との関係 (Minor)**: §6.3.3 で「RobustScaler fold 別 fit」「PCA」と並列記載されているが、scikit-learn Pipeline で `RobustScaler → PCA → KMeans` の連結順序が明示されていない。実装時に CC が独自解釈で順序決定 → 設計逸脱リスク (Minor)。

**結論**: **PASS (Minor)**。設計レベルでの大きな欠陥なし。Pipeline 化の具体性は実装着手前に補完すべき (Minor 改善余地)。

### 観点 ⑤ 再現性: **PASS**

1. **fold 別 fit + joblib 保存**: §6.3.3 / §6.3.7 で fold 別 fit + artifact 保存明示・phase_compliance §4a.2 と整合・**再現性確保**。
2. **artifact 命名規律 + 起動時 assertion**: §6.3.7 で L-183 同型再演防止経路あり・phase_compliance §6b.1/§6b.4 と整合。
3. **random_state 固定 (暗黙)**: k-means / k-means++ で random_state 固定必須だが、§6.3.2 / §6.3.X 内に明示なし (= 実装時に明示要)。regime ensemble §6.1.4 と同型継承で部分対処。

**結論**: **PASS**。再現性確保の構造的欠陥なし。

### 観点 ⑥ 実行プロセス: **FAIL (Major)**

1. **CP2 監査同型問題の §6.3 設計再演 = メタガード追加が機械的フォーマット化されただけ (Major)**: 観点 ③ #1 と同型問題。CP2 監査 Critical で「機械的フォーマット化されただけで本質的に効いていない」を実証し、メタガード 13/14/15 追加で対策したが、本 §6.3 設計でも完全同型再演。**ガード追加の連鎖**で止まらず構造的問題。

2. **Stage 1 → Stage 2 → Stage 3 → Stage 4 の段階的検証経路自体は妥当**: 4 段階構造は regime ensemble §6.1.1 / Entry ML §6.2.1 と同型・[arxiv 2401.05337] 統計 + Financial 並行評価業界整合。

3. **Stage 1 → Stage 2 → Stage 3 の発動条件閾値の優先順位欠落 (Minor)**: §6.3.X 全体で「不合格時の対応」表に「§6.3.2 第二段階 (GMM / HDBSCAN / ensemble) 検討」「§6.3.3 入力再設計」「§6.3.4 k 数調整」「§6.3.4 全 k 不合格なら §6.3.3 入力再設計」と複数の出口経路があるが、**複数同時不合格時の優先順位が §6.3.X 全体で明示されていない** (= CP2 監査 観点 ⑥ Minor と同型)。

**結論**: **FAIL (Major)**。メタガード 13/14/15 が機械的フォーマット化された実証 = CP2 監査の改善策が無効化された設計プロセス上の重大欠陥。第二段階発動条件の優先順位整理は実装時に補完すべき (Minor)。

### 観点 ⑦ 主エージェントバイアス: **FAIL (Critical)**

1. **CP1/CP2/CP3 と 3 回連続で「同じ訓練ベース AI (= Claude 系) で同型バイアス回避できない」実証 (Critical)**: 観点 ③ + 観点 ⑥ + cc_role §1.4 #3 の同型バイアス警告がそのまま実証された形。CP3 監査依頼書の経緯 #4 で「本セッション L-232/L-233/L-235 改善 2 違反「わかりやすく解説」指摘 6 回連続 + §6.2 設計が CP1 監査同型問題を完全再演 (= 機械的フォーマット化検出メタガード追加) の構造的問題あり」と CC 自身が認識しているが、**§6.3 設計でも完全同型再演**。

2. **「業界 standard だから」を判断根拠化する癖 (= L-230) の §6.3 貫通**:
   - §6.3.1 silhouette > 0.3「scikit-learn 業界 minimum」 → **高次元用途の業界根拠ゼロ**
   - §6.3.2 k-means 単体採用「業界 standard 整合 + Phase 4-a 旧実装の継承」 → **「異なる目的軸」を自認しながら同型継承を採用根拠化**
   - §6.3.3 案 b 全投入「cluster-then-predict 業界 standard」 → **cat-bitget 固有 silhouette pre check ゼロ**
   - §6.3.4 k ∈ {3, 4, 5}「業界実証 3-5 cluster」 → **cat-bitget 固有 k 別 silhouette pre check ゼロ**
   - §6.3.6 主要 7 列 + 派生 one-hot「業界 standard」 → **LightGBM 4.0+ native categorical support で one-hot 不要慣行**との整合性 verify ゼロ (= Q6(c) 指摘事項)

3. **「メタガード追加で対策」が構造的に効かない実証**: cc_role §1.4.6.1 改善 10-12 (CP1 監査追加) + メタガード 13-15 (CP2 監査追加) を §6.3 設計に適用したが、**「同じ訓練ベース AI が自分で書いた設計を自分でガード」する以上、ガード追加は機械的フォーマット化される**構造的限界。CP3 監査でも同型問題発見 = **3 回連続実証**。

**結論**: **FAIL (Critical)**。CP1/CP2/CP3 と 3 回連続で同型バイアス再演。ガード追加では構造的に止まらない実証。設計プロセス自体の見直しが必要 (= 別経路の人間レビュー or 外部 AI / 監査の機械化以外の経路)。

---

### Q1 入力特徴量設計 §6.3.3 案 b 全投入 (= 2,666 列) + PCA 50-100 主成分: **業界整合 / 改善余地 3 件**

業界整合あり (cluster-then-predict pattern = [Springer Nature 2025] / [PMC 7785332] と整合・LightGBM 1,000+ 特徴量処理可能 + PCA 50-100 次元削減も業界 standard)。

改善余地:
1. **PCA 主成分数 50-100 の cat-bitget 固有 pre check ゼロ (Critical・観点 ① #4 と同型)**: 外部検索 C6 で「[Quantinsti] PCA could help significantly in strategy for pairs trading」「one trading resource demonstrated using 30 principal components with K-means clustering for financial data analysis」= **業界実装事例は 30 主成分**で 50-100 は cat-bitget 固有設計。**Phase 0 v3.1 既存 parquet で実データ PCA 試算ゼロ**で 50-100 範囲を決め打ち。実装着手時に「分散 95% で何主成分必要か」の試算で 30 主成分以下に収まる可能性 → 50-100 範囲外の業界相場との乖離リスク。
2. **案 b 全投入 vs 案 c 厳選の silhouette 改善寄与の業界実証なし (Major)**: §6.3.3 「不採用 = 案 c 厳選」とだけ書かれているが、**業界実証で「全投入 + PCA」と「厳選数十列」のどちらが silhouette 改善に寄与するかの定量比較ゼロ**。外部検索 C1 で「Principal Component Analysis (PCA) and K-means clustering have been applied to select representative coins」= PCA + K-means の組合せは業界実装あり、ただし「全投入 + PCA」と「厳選」の比較実証は本検索でゼロ。「教師なしで不要列を捨てる判断が事前にできない → 全投入 + post-pruning が安全」という採用根拠は **論理的には妥当だが業界実証根拠なし** (= L-232 同型問題)。
3. **regime 6 列統合の整合性 verify が形式 (Q7 と同型)**: §6.3.3 で「regime 6 列の扱い = 統合」「同じ予測値でも regime 違えば trade 性質違う」と書いているが、**Phase 4-a 旧実装 + v15 HMM 既実装で「regime 別に entry cluster の性質差を pre check」していない**。Stage 1 で「regime 別 cluster 効果差 > 20% で別 fit 化検討」と data-driven 経路宣言はあるが、第一段階「統合」採用根拠は業界引用のみ。

数値根拠ある断言: cluster-then-predict pattern は外部検索 C1 で業界実証あり (= Springer Nature 2025 / PMC)。PCA + K-means 組合せも業界 standard。**ただし 50-100 主成分は cat-bitget 固有設計で業界相場 (= 業界実装事例 30 主成分) と乖離・data-driven 経路宣言で実装着手時 calibrate に依存**。

### Q2 アルゴリズム選定 §6.3.2 k-means 単体 + Gaussian kernel: **業界整合 / 改善余地 3 件**

業界整合あり (k-means + Gaussian kernel 確率変換は scikit-learn 業界 standard・第二段階 GMM/HDBSCAN/ensemble 検討経路あり)。

改善余地:
1. **2025 crypto cluster 業界 standard は ensemble = K-Means + DBSCAN + GMM (Major)**: 外部検索 C2 で「Ensemble clustering combines K-Means, DBSCAN, and GMM for robustness, with a multi-method clustering framework combining these three algorithms to identify market regimes across cryptocurrencies. The ensemble regime labeling approach provides robust cross-method validation」と業界 standard 確認。**§6.3.2 で第一段階 k-means 単体採用は業界後退**。第二段階 ensemble 検討経路あるが、第一段階で ensemble 採用しない根拠は「計算重さ・実装シンプル」のみで、**cat-bitget 固有 cluster ensemble 純増分実証ゼロ**。CP1 監査で regime ensemble 採用したのに、entry cluster で単体採用は工程間不整合。
2. **Gaussian kernel σ = cluster median 距離の業界 standard 整合性 verify ゼロ (Major)**: §6.3.2 で「σ = cluster median 距離」「§6.1.5 regime ensemble と同型」と書くが、**§6.1.5 自体が CP1 監査 Critical-1 でキャリブレーション欠陥として指摘され isotonic regression 追加対策中**。cluster 用途で σ 設定の業界 standard は他に「adaptive σ」「per-cluster σ」「Bayesian σ」等あり、median 距離一辺倒の業界実証根拠ゼロ。
3. **HDBSCAN 不採用根拠「k 数が不安定 → 後段固定戦略と相性悪い」の業界反証 (Major)**: 外部検索 C3 で「If you need to influence the number of clusters produced ... decrease min_cluster_size or switch cluster_selection_method='leaf'」と **min_cluster_size + cluster_selection_method で cluster 数固定化技法**が業界 standard と確認。§6.3.2 「HDBSCAN k 数が不安定」は技術制約ではなく **min_cluster_size 設定で対応可能**。「ノイズ除外で trade を no-trade 化する設計矛盾」も HDBSCAN 採用時に「ノイズ trade を別 cluster (= 例: noise_cluster_id = -1) として扱う」設計で吸収可能。HDBSCAN 不採用根拠が技術制約として薄弱・**「k-means 単体採用したい」結論に合わせて HDBSCAN の制約を過大評価**している論理逆転リスク。

数値根拠ある断言: 2025 crypto cluster 業界 standard は K-Means + DBSCAN + GMM ensemble (= 外部検索 C2 確認)。**§6.3.2 第一段階 k-means 単体採用は業界後退** (= 第二段階 ensemble 検討経路あるが第一段階で採用しない cat-bitget 固有 lift 実証ゼロ)。HDBSCAN 不採用根拠は min_cluster_size 設定で反証可能・採用検討余地あり。

### Q3 k 数決定 §6.3.4 k ∈ {3, 4, 5} data-driven: **業界整合 / 改善余地 2 件**

業界整合あり (3-5 cluster 業界実証 = industry_benchmark §2.3「3-5 戦略並立で 1.5-2× Sharpe 改善が現実」+ [Built In Elbow Method] + [ML Mastery Silhouette] と整合)。

改善余地:
1. **Phase 4-a 旧 k=12 が「過剰」と判定された根拠の cat-bitget 固有 verify ゼロ (Major)**: §6.3.4 で「Phase 4-a の k=12 は過剰実証・3-5 への絞り込み妥当」と書くが、**phase_compliance §4a.5 K96 SHORT q99 が独立 cluster に分離されない事案は「k=12 過剰」ではなく「特定 cluster が分離されない」**という別問題。k=12 を 3-5 に絞ることで「異なる戦略タイプの取りこぼし」リスク (= 例: K96 SHORT q99 のような特殊 cluster が 3-5 cluster 内に混在化) は議論されていない。**Phase 4-a 実測の k=12 の各 cluster 性質分析ゼロ**で「過剰」と決め打ち。
2. **silhouette と elbow が食い違った場合の業界 standard 決定方法 (= gap statistic / BIC / ONC algorithm) が §6.3.4 採用なし (Minor)**: §6.3.4 で「silhouette 最大と elbow が食い違ったら業界経験則 (= 3-5 cluster で 1.5× レバー) で決定」と書くが、**業界 standard は gap statistic / BIC / ONC algorithm 等の客観的判定手法**。AFML Ch.20 HRP で「k 数最適化に gap statistic / elbow / silhouette の併用推奨」と §6.3.4 で言及されているが、gap statistic / BIC は採用していない・経験則のみ。

数値根拠ある断言: 3-5 cluster 業界実証は industry_benchmark §2.3 で確認。**Phase 4-a の k=12 → 3-5 絞り込みの cat-bitget 固有 verify は K96 SHORT q99 cluster の取りこぼしリスク pre check 経由で必須**だが §6.3.4 内に欠落。

### Q4 評価方法 §6.3.1 Stage 1 silhouette > 0.3 / Stage 3 純増分 1.5×: **業界整合 / 改善余地 3 件**

業界整合あり (silhouette > 0.3 = scikit-learn 業界 minimum・純増分 1.5× = industry_benchmark §2.3 業界実証 1.2-1.8× 中央値整合)。

改善余地:
1. **silhouette > 0.3 を crypto / 高次元 (PCA 50-100) cluster 用途で適用する業界根拠ゼロ (Critical・観点 ① #1 と同型)**: 外部検索 C7 で「silhouette analysis can be challenging in very high-dimensional spaces」「low averages (e.g., below 0.5) highlight subgroups with inadequate cohesion」と高次元での silhouette 制約明示。**0.3 は低次元 (2-10 次元) の minimum 値で、50-100 次元 PCA 後の crypto 用途で 0.3 適用根拠ゼロ**。0.5 が weak clustering 境界とすると、0.3 は **「弱いクラスタリングを合格にする」 lower bar**。
2. **Stage 3 純増分 1.5× の cat-bitget 純増分試算ゼロ (Major)**: §6.3.1 Stage 3「5.1× 積算経路の中央値 $2,060/月 ($1,900 合格 + 8% マージン) に届く論点整合」と Q4(b) で問うているが、**cat-bitget 旧 Priority $370/月 base line + 5.1× = $1,887/月 + cluster 純増分 1.5× = $555/月 (差分) と算術検算**すると、cluster 単独で $555/月 の差分を作るか戦略並立全体で 1.5× を作るかの論点が §6.3.1 で曖昧。「戦略並立 1.5× = cluster だけの寄与」なのか「cluster × Sizing × Exit の戦略並立全体寄与」なのかが明示されていない。後者ならば cluster 単独の寄与は更に小さい → 純増分 1.5× の cluster 単独実現性低下。
3. **旧 14 列版 silhouette 0.15-0.20 が推定値で実測値ではない (Critical・観点 ③ #3 と同型)**: 依頼書 Q4(c) 指摘事項「Phase 4-a 14 列版の実測 silhouette が「0.15-0.20」と推定されているのみで実測値ではない・実装着手前に推定値を確定すべき」が完全に有効。**§6.3 内で実測値計算ゼロ + 0.15-0.20 の出典なし**。新 PCA 版で「> 0.3 期待」と書くが、**推定値ベースの「期待」で第一段階固定値を決めている** = メタガード 14 違反 (= 業界引用 + cat-bitget 過去事例 1 件以上併記の cat-bitget 過去事例が架空値)。

数値根拠ある断言: silhouette > 0.3 は低次元用途の業界 minimum で、**高次元 PCA 50-100 用途での適用根拠は業界実証ゼロ・データ不足 (理由: 外部検索 C7 で高次元 silhouette challenge 明示)**。0.5 が weak clustering 境界・0.3 は「弱いクラスタリング合格」設定。実装着手前に Phase 4-a 旧実装で実測 silhouette 確定 + 新 PCA 版での目標値再 calibrate が必須 (Critical)。

### Q5 leak 防止 §6.3.7 6 経路の網羅性: **業界整合 / 改善余地 2 件**

業界整合あり (教師なし学習 leak 経路 6 項目は AFML Ch.7 Purged K-Fold + Embargo + scikit-learn Pipeline と整合・外部検索 C5 「scikit-learn pipeline ... great way to prevent data leakage」と業界 standard 整合)。

改善余地:
1. **entry_id 生成タイミングの leak verify ゼロ (Minor)**: 依頼書 Q5(b) 指摘事項「entry_id 自体の生成タイミングが leak 経路にならないか・entry_id 生成時に未来情報を含む列を使っていないか verify」が一部有効。§6.3.6 で「entry_id ベース merge」とあるが、**entry_id の生成式が §6.3 / §6.2 / §6.0 内に明示されていない**。Entry ML の primary 出力に基づく id 生成と推定されるが、未来情報 (= MFE/MAE) を含まないかの verify ゼロ。
2. **cluster label の post-hoc 命名で「Stage 2 視認で再命名」が許容されている (Minor)**: 依頼書 Q5(c) 指摘事項「train fold 内での再命名と test fold 反映の境界が曖昧・命名再変更プロトコルの厳格化必要」が一部有効。§6.3.5 整合性 Q&A Q2 で「train fold 内での再命名は leak でない」と回答しているが、**「再命名後に Stage 1 silhouette > 0.3 を再 verify するか」の経路明示なし**。再命名で cluster 性質が変わる場合、Stage 1 評価指標も再計算必要。

数値根拠ある断言: §6.3.7 leak 6 経路は AFML Ch.7 + scikit-learn Pipeline と整合・**業界 standard の leak 防止経路はほぼ網羅**。entry_id 生成タイミング + 再命名プロトコルの 2 件 Minor 改善余地あり・Critical 欠陥なし。

### Q6 出力 → 後段接続 §6.3.6: **業界整合 / 改善余地 3 件**

業界整合あり (出力 7 主要列 + 派生 one-hot 列は AFML Ch.16 / §6.1.6 regime と同型・parquet 保存 + entry_id ベース merge は業界 standard)。

改善余地:
1. **cluster_silhouette (= 各 trade はみ出し度) を出力列に含む業界事例が薄い (Minor)**: 依頼書 Q6(a) 指摘事項「cluster_silhouette を出力列に含む業界事例ある? 後段 [3]/[4] がどう活用するか業界実装例調査」が有効。**cluster_silhouette を trade level で出力する業界事例は本監査外部検索でゼロ**。一般的に silhouette は cluster 全体の品質評価で使われ、trade level での活用業界事例なし。後段 [3]/[4] でどう活用するかが §6.3.6 で「業界 standard」と書きつつ業界実装例なし → 設計判断根拠の薄さ。
2. **LightGBM 4.0+ native categorical support で one-hot 不要慣行との整合性 verify ゼロ (Major)**: 依頼書 Q6(c) 指摘事項「LightGBM 4.0+ では native categorical support で one-hot 不要の慣行に変わっている・最新 LightGBM 業界実装の整合性 verify」が完全有効。外部検索 C4 で「LightGBM has built-in support for categorical features, meaning it can process them directly without one-hot encoding」「One-hot encoding is suboptimal for tree learners, particularly for high-cardinality categorical features where a tree built on one-hot features tends to be unbalanced and needs to grow very deep to achieve good accuracy」と業界 standard 確認。**§6.3.6 で「業界 practice として one-hot 推奨」と書くのは LightGBM 4.0+ の業界実装と矛盾**。one-hot 列の冗長化リスクあり・cluster_id 直接食う方が業界 standard。§6.3.6 整合性 Q&A Q2 で「業界 practice として one-hot 推奨 (= モデル可読性 + 重要度分析容易性)」と書くが、これは tree 系業界実装と直接矛盾。
3. **派生 one-hot 列の k=4 想定だが、k=3 / k=5 の場合の列数調整プロトコル明示ゼロ (Minor)**: 依頼書 Q6(b) 指摘事項「派生 one-hot 列の k=4 想定だが、k=3 / k=5 の場合の列数調整プロトコルが明示されていない」が完全有効。§6.3.6 で「(k=4 想定・k=3 / k=5 でカラム数調整)」と注記のみ・**具体的な列数決定経路 (= 「k 確定後に is_X を自動生成」のロジック) が §6.3.6 内に明示されていない**。実装時に CC が独自解釈で決定 → 設計逸脱リスク。

数値根拠ある断言: LightGBM 4.0+ native categorical support 業界実装は外部検索 C4 で「tree learners で one-hot encoding は suboptimal」と確認。**§6.3.6 「業界 practice として one-hot 推奨」は古い慣行 (LightGBM 3.x 以前) で 4.0+ では native categorical 推奨**。one-hot 推奨は業界後退の判断。

### Q7 §6.1.4 regime k-means と §6.3.2 entry cluster k-means の役割分離整合性: **業界整合 / 改善余地 3 件**

業界整合あり (regime k-means + entry cluster k-means の 2 段 k-means 構造は arxiv 2509.09751 「regime feature substantially helps crypto-correlated stocks」と整合方向・regime + cluster の 2 軸分離は業界実装あり)。

改善余地:
1. **regime k-means 出力 (= 6 列) を entry cluster k-means 入力に含む設計の予測誤差相関リスク verify ゼロ (Major・観点 ① #3 と同型)**: 依頼書 Q7(b) 指摘事項「predicting outcome (= entry cluster の cluster_id) が input (= regime 6 列) の関数になる構造で「regime と entry cluster の予測誤差相関 Pearson > 0.5」リスクの定量的予測必要」が完全有効。§6.3.1 Stage 1 表で「regime cluster との予測誤差相関 Pearson < 0.5」verify 経路あるが、**「regime 6 列を入力に含む → 出力 cluster_id が regime 関数化 → 相関 > 0.5 になりやすい」構造的リスクの事前 verify ゼロ**。Phase 4-a + v15 HMM 既実装で「regime 別 entry cluster 分布」を pre check 可能だが未実施 (= cc_role §1.4.6.1 改善 11 違反)。
2. **相関 > 0.5 となった場合の対応経路「§6.3.3 入力で regime 6 列除外検討」のトレードオフ verify ゼロ (Minor)**: 依頼書 Q7(c) 指摘事項「相関 > 0.5 の場合の対応経路は妥当か・regime 6 列除外で cluster の市場文脈情報が失われるリスクとのトレードオフ verify」が一部有効。§6.3.1 data-driven 経路宣言で「> 0.5 なら入力 §6.3.3 で regime 6 列除外検討」と経路ありだが、**「regime 6 列除外で cluster 性能落ち」と「regime 6 列維持で相関 > 0.5 で重複」のトレードオフ評価軸が §6.3.X 内に明示されていない**。
3. **判定間隔 1h (regime) vs entry bar (= 5m) (entry cluster) の時間軸不整合 (Minor)**: §6.1.4 regime k-means は 1h ベース判定・§6.3.2 entry cluster は entry trade (= 5m bar tick) ベース判定 → **時間軸が異なる 2 つの k-means を merge_asof で接続する causal alignment 経路が §6.3.6 内に明示されていない**。§6.1.6 で `merge_asof(direction="backward")` 採用済だが、entry_id ベース merge との関係が曖昧 (Minor)。

数値根拠ある断言: regime + entry cluster の 2 段 k-means 構造は業界実装あり。**ただし regime 6 列を entry cluster 入力に含む設計の予測誤差相関 verify が事前 pre check ゼロ + 相関 > 0.5 の場合の対応経路トレードオフ verify ゼロ → 実装着手前に Phase 4-a + v15 HMM 既実装で pre check 必須** (Major)。

---

## 外部検索結果サマリー

実施したクエリ 7 件 (= 依頼書要請 C1〜C7) と主要発見:

### 検索 C1: crypto 5min bar entry signal post-prediction k-means clustering 2025 2026
- **主要発見**: PCA + K-means clustering が cryptocurrency 前処理段階で業界実装あり ([Springer Nature 2025] / [Discover AI Cryptocurrency Trading Optimization])。Bitcoin 5min bar で「instantaneous 5-min forward predict は low correlation」「predictive power increases with time, reaching >80% for forward 5 hours」= 5min 短期予測は low correlation で多時間軸 + ML 必須。DBSCAN + Decision Tree 統合で「accurate position forecasting」も 2026 業界実装あり。
- 出典: [Springer Nature 2025](https://link.springer.com/article/10.1007/s44163-025-00519-y) / [PMC 12571449](https://pmc.ncbi.nlm.nih.gov/articles/PMC12571449/) / [MDPI Bitcoin Crisis Periods](https://www.mdpi.com/2227-9091/14/3/51)

### 検索 C2: cluster ensemble crypto trading robustness improvement K-Means DBSCAN GMM 2025
- **主要発見**: **「Ensemble clustering combines K-Means, DBSCAN, and GMM for robustness, with a multi-method clustering framework combining these three algorithms to identify market regimes across cryptocurrencies」**= 2025 crypto 業界 standard で ensemble 採用。「K-Means leads in speed (9500 tx/sec) / DBSCAN's 0.68 silhouette edges out for density-varying data / GMM offers probabilistic insights」「hybrid ensemble approach combines K-Means (speed) + GMM (probs) for robust scoring」が業界実装。
- 出典: [Johal Blockchain Transaction Clustering](https://johal.in/blockchain-transaction-clustering-using-unsupervised-learning-algorithms/) / [MDPI K-Means Z-Score Bitcoin](https://www.mdpi.com/2227-9709/12/2/43) / [DSFE 2025](https://www.aimspress.com/aimspress-data/dsfe/2025/3/PDF/DSFE-05-03-017.pdf) / [arxiv FinRL 2501.10709](https://arxiv.org/pdf/2501.10709)

### 検索 C3: HDBSCAN fixed cluster count crypto trading min_cluster_size 2025
- **主要発見**: HDBSCAN cluster 数固定化技法 = **「min_cluster_size + cluster_selection_method='leaf'」で cluster 数を影響可能**。「if you want more clusters, decrease min_cluster_size or switch cluster_selection_method='leaf'」が業界 standard。§6.3.2「HDBSCAN k 数が不安定」は技術制約ではなく設定で対応可能 → 不採用根拠の業界反証あり。
- 出典: [Shadecoder HDBSCAN Guide 2025](https://www.shadecoder.com/topics/hdbscan-a-comprehensive-guide-for-2025) / [HDBSCAN docs](https://hdbscan.readthedocs.io/en/latest/parameter_selection.html) / [GeeksforGeeks HDBSCAN](https://www.geeksforgeeks.org/machine-learning/hdbscan/) / [scikit-learn HDBSCAN](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html)

### 検索 C4: LightGBM native categorical feature support vs one-hot encoding 2025 2026
- **主要発見**: **「LightGBM has built-in support for categorical features, meaning it can process them directly without one-hot encoding」**= LightGBM 4.0+ で native categorical 業界 standard。「One-hot encoding is suboptimal for tree learners, particularly for high-cardinality categorical features where a tree built on one-hot features tends to be unbalanced and needs to grow very deep to achieve good accuracy」 = tree 系で one-hot 推奨は **業界後退の判断**。§6.3.6「業界 practice として one-hot 推奨」は古い慣行で 4.0+ では cluster_id 直接食う方が業界 standard。
- 出典: [LightGBM 4.6 Advanced Topics](https://lightgbm.readthedocs.io/en/latest/Advanced-Topics.html) / [LightGBM Features](https://lightgbm.readthedocs.io/en/latest/Features.html) / [apxml LightGBM Categorical](https://apxml.com/courses/mastering-gradient-boosting-algorithms/chapter-5-lightgbm-light-gradient-boosting/lightgbm-categorical-features) / [ML Journey LightGBM](https://mljourney.com/how-does-lightgbm-handle-categorical-features/)

### 検索 C5: unsupervised learning data leakage prevention scikit-learn Pipeline fold AFML Lopez de Prado
- **主要発見**: **「scikit-learn pipeline is a great way to prevent data leakage as it ensures that the appropriate method is performed on the correct data subset」**= Pipeline 化が業界 standard。「For unsupervised learning tasks, y does not need to be specified. However, the pipeline approach still applies to prevent data leakage in preprocessing steps for unsupervised models」 = 教師なしでも Pipeline 化必須。「In fit_transform, the training data is split into k folds and each fold is encoded using the encodings learnt using the other k-1 folds」 = fold 別 fit 業界 standard。**§6.3.7 leak 防止 6 経路はほぼ網羅・AFML/Lopez de Prado specific 引用は本検索でゼロ**。
- 出典: [scikit-learn Common Pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) / [Medium pacosun Data Leakage](https://medium.com/@pacosun/split-smart-avoiding-data-leakage-in-cross-validation-894863a93553) / [DataSchool Pandas Leakage](https://www.dataschool.io/machine-learning-data-leakage/)

### 検索 C6: PCA principal components number selection k-means clustering 50 100 trading 2025
- **主要発見**: 「Principal components are the continuous solutions to the discrete cluster membership indicators for K-means clustering」= 理論的に PCA + K-means 整合性あり ([Ding and He theorem])。「To determine which principal component is more important, you calculate the variance of each component and plot scree plots」 = 業界 standard は分散説明率 + scree plot。**「one trading resource demonstrated using 30 principal components with K-means clustering for financial data analysis」= 業界実装事例は 30 主成分**で、§6.3.3「50-100 主成分」は cat-bitget 固有設計で業界相場と乖離。50-100 範囲外の業界相場 (= 30 主成分) との verify ゼロ。
- 出典: [Quantinsti PCA Trading](https://blog.quantinsti.com/principal-component-analysis-trading/) / [ACM K-means via PCA](https://dl.acm.org/doi/10.1145/1015330.1015408) / [Medium PCA K-Means Implementation](https://medium.com/@zullinira23/implementation-of-principal-component-analysis-pca-on-k-means-clustering-in-r-794f03ec15f)

### 検索 C7: silhouette score minimum threshold crypto high-dimensional k-means clustering 2025
- **主要発見**: **「Silhouette analysis may be less reliable for certain datasets and cluster shapes and can be challenging in very high-dimensional spaces」**「silhouette score can be sensitive to high-dimensional data, and dimensionality reduction techniques, such as PCA or t-SNE, can be applied before calculating the silhouette score to improve its reliability」= 高次元 silhouette 制約明示。「low averages (e.g., below 0.5) highlight subgroups with inadequate cohesion or proximity to neighboring clusters」 = **0.5 が weak clustering 境界・0.3 は「弱いクラスタリング合格」 lower bar**。§6.3.1 silhouette > 0.3 は低次元用途の業界 minimum で、PCA 50-100 後の crypto 用途では業界根拠ゼロ。
- 出典: [Grokipedia Silhouette](https://grokipedia.com/page/Silhouette_(clustering)) / [Medium Govindaraj High-Dimensional K-Means](https://medium.com/@govindarajpriyanthan/clustering-in-high-dimensional-space-building-and-evaluating-a-custom-k-means-algorithm-49802d63a6fc) / [NumberAnalytics Silhouette](https://www.numberanalytics.com/blog/mastering-clustering-evaluation-with-silhouette-score) / [MachineLearningMastery Silhouette](https://machinelearningmastery.com/k-means-cluster-evaluation-with-silhouette-analysis/) / [arxiv 2507.08311 CAS Silhouette](https://arxiv.org/pdf/2507.08311)

---

## 総合判定

### Verdict: **PIVOT** (= Critical 修正後に GO 可能・修正なし実装着手は不可)

### 根拠

**1. 業界整合性は部分的に確保されている**: 7 検索のうち、cluster-then-predict pattern (C1) + scikit-learn Pipeline leak 防止 (C5) + 3-5 cluster 業界実証 (industry_benchmark §2.3) + AFML Ch.4/16/20 + cc_entry_logic_self_study §14.6/§17.6/§18.3 と整合する設計骨格はある。Q5 leak 防止 6 経路は業界 standard 整合 (Minor 改善余地のみ)。

**2. ただし「業界 standard 採用」を判断根拠化する CP1/CP2 監査同型問題が §6.3 全体に 3 回目連続再演**: 観点 ③ 認知バイアス FAIL (Critical) + 観点 ⑥ 実行プロセス FAIL (Major) + 観点 ⑦ 主エージェントバイアス FAIL (Critical) = CP2 監査でメタガード 13/14/15 追加した本旨を **メタガードそのものが機械的フォーマット化された**形で逆効果化。これは「同じ訓練ベース AI (= Claude 系) でガード追加では構造的に止まらない」ことを 3 回連続実証した重大な構造的問題。

**3. 実装着手前に修正必須の Critical / Major 欠陥が 5 件**:
   - C1: silhouette > 0.3 を高次元 PCA 50-100 後で適用する業界根拠ゼロ + 旧 14 列版 silhouette 0.15-0.20 が架空推定値 (= 観点 ① #1 / 観点 ③ #3 / Q4 #1 #3)
   - C2: 2025 crypto cluster 業界 standard = K-Means + DBSCAN + GMM ensemble に対し §6.3.2 第一段階 k-means 単体採用は業界後退 + HDBSCAN 不採用根拠は min_cluster_size で反証可能 (= Q2 #1 #3)
   - C3: Gaussian kernel σ = cluster median 距離の isotonic regression キャリブレーション欠落 (= CP1/CP2 監査 Critical-1 同型問題の 3 回目再演・観点 ① #2)
   - M1: LightGBM 4.0+ native categorical support 業界実装と §6.3.6 「one-hot 推奨」の矛盾 (= Q6 #2)
   - M2: cat-bitget 固有 verify の定量試算がメタガード 13 違反で 7 サブセクション全て言及のみ・実施ゼロ (= 観点 ③ #2)

**4. 月次 NET ≥ $1,900 達成可能性判定は本監査スコープ外** (= 依頼書 §大目的 / §守則 明記)。本判定は **詳細設計の業界整合性 + cat-bitget 制約整合性 + 同型バイアス検出 + leak 防止 + 内部一貫性** の verify のみ。

**5. NO-GO (= 重大欠陥・再設計必要) ではない理由**: 設計骨格 (= 7 サブセクション + 段階的アプローチ + data-driven 経路宣言 + 第二段階出口設計 + leak 防止 6 経路) は妥当・実装着手前の修正 5-7 件で GO 可能。Critical 欠陥 (C1/C2/C3) は CP1/CP2 監査同型問題のため対策手法は既知 (= 実測値計算 / ensemble 第一段階採用 / isotonic regression)。

**6. GO (= 修正なし実装着手可) ではない理由**: Critical C1 (silhouette 0.15-0.20 が架空推定値) を実装後に発見すると、Stage 1 評価基準ごと再設計が必要。Critical C2 (k-means 単体採用) を実装後に「Stage 1 silhouette < 0.3」で第二段階 ensemble 検討経路に切り替える場合、設計工数の浪費。実装着手前に修正する方が労力ずっと少ない。

---

## 改善方向性 (= 具体提案 7 件・優先度明示)

### Critical-1: §6.3.1 Stage 1 silhouette > 0.3 を「高次元 PCA 後の業界根拠あり閾値」に再設計 + Phase 4-a 旧 14 列版実測 silhouette 確定
- 修正対象: §6.3.1 Stage 1 silhouette > 0.3 + 旧 14 列版比較
- 修正内容:
  - Phase 4-a 旧 14 列版実測 silhouette を `predictions_train_2021_2024_k12long_refit.parquet` で**本セッション中に実測**確定 (= 「0.15-0.20 推定」を実測値に置換)
  - 新 PCA 版 silhouette 目標値は実測値 + 50% (= 例: 実測 0.18 なら目標 0.27) または業界相場 (= 外部検索 C7 「< 0.5 weak clustering」前提で 0.4-0.5 範囲) で再 calibrate
  - 高次元 silhouette 制約を §6.3.1 業界 standard verify セクションに明示追加 (= 外部検索 C7 引用)
- 出典: [Grokipedia Silhouette 高次元 challenge](https://grokipedia.com/page/Silhouette_(clustering)) / [Medium Govindaraj High-Dimensional K-Means]

### Critical-2: §6.3.2 第一段階 k-means 単体採用を ensemble 第一段階採用に再検討 + HDBSCAN 不採用根拠の業界反証反映
- 修正対象: §6.3.2 アルゴリズム選定
- 修正内容:
  - 2025 crypto 業界 standard (= K-Means + DBSCAN + GMM ensemble) を §6.3.2 業界 standard verify セクションに明示反映 (= 外部検索 C2 引用)
  - 第一段階 k-means 単体採用根拠を強化: cat-bitget 固有 cluster ensemble pre check で「k-means 単体 vs ensemble の silhouette 差」を Phase 4-a 旧実装で本セッション中に実測 verify (定量試算 1 件以上必須)
  - HDBSCAN 不採用根拠を「k 数が不安定」から「`min_cluster_size + cluster_selection_method='leaf'` で cluster 数固定化可能だが、後段 [3]/[4] の cluster 別固定戦略との接続具体性検討経路を第二段階に残す」に再設計
- 出典: [外部検索 C2 / C3]

### Critical-3: §6.3.2 / §6.3.6 cluster 確率出力に isotonic regression キャリブレーション設計を追加
- 修正対象: §6.3.2 Gaussian kernel 確率変換 + §6.3.6 cluster_prob_X 出力
- 修正内容:
  - k-means cluster 距離 → Gaussian kernel `exp(-d²/2σ²)` → **fold 別 isotonic regression** で post-hoc キャリブレーション (= CP1 監査 Critical-1 / CP2 監査 Critical-1 と完全同型対策・3 回目)
  - §6.3.1 Stage 1 評価に **Brier score + reliability diagram + ECE** を追加 (= 業界 standard・cluster_prob の品質評価)
  - §6.3.6 cluster_confidence の算出式を「最大確率 - 2 番目確率」(= 現設計) からキャリブレーション後値で計算と明示
- 出典: [scikit-learn Probability Calibration](https://scikit-learn.org/stable/modules/calibration.html) / [arxiv 2510.25458 Multiclass Calibration]

### Major-1: §6.3.6 cluster_id 直接食う + one-hot 列を blacklist 候補に変更 (= LightGBM 4.0+ 業界整合)
- 修正対象: §6.3.6 出力 → 後段接続
- 修正内容:
  - 第一段階で **cluster_id 直接食う** (= LightGBM 4.0+ native categorical support 業界 standard・外部検索 C4 引用) に変更
  - 派生 one-hot 列 (= is_scalp / is_long_term / is_risky / is_avg) は第二段階 [3]/[4] 性能差判定 (= cluster_id vs one-hot の純増分 ≥ 1.1× で one-hot 採用検討) として保持
  - §6.3.6 整合性 Q&A Q2 を「業界 practice として one-hot 推奨」から「LightGBM 4.0+ 業界 standard は native categorical 推奨」に書き直し
- 出典: [外部検索 C4 LightGBM Features]

### Major-2: §6.3 全 7 サブセクションの cat-bitget 固有 verify 定量試算を本セッション中に実施
- 修正対象: §6.3.1〜§6.3.7 cat-bitget 固有 verify セクション (= 全 7 サブセクション)
- 修正内容:
  - 「実装着手時に pre check」と書かれた 7 件の定量試算を **本セッション中に Phase 4-a predictions_train_2021_2024 + v15 HMM regime predictions + Phase 0 v3.1 parquet で実施**:
    - §6.3.1: 旧 14 列版実測 silhouette (Critical-1 と統合)
    - §6.3.2: k-means 単体 vs ensemble の silhouette 差 (Critical-2 と統合)
    - §6.3.3: 2,666 列 PCA 50-100 + scaler の暫定 silhouette 試算 (PCA 主成分数 30 vs 50-100 比較)
    - §6.3.4: k=3,4,5 並列 fit の silhouette 比較
    - §6.3.5: 4 軸 (TP_prob / MFE / SL_prob / 保有時間) の cluster 別平均算出 (区別がつくか pre check)
    - §6.3.6: Gaussian kernel 確率変換した場合の確率列分布 pre check
    - §6.3.7: artifact 名 grep + assertion 試運転
  - 定量試算結果を §6.3.X 「cat-bitget 固有 verify」セクションに追記し、メタガード 13 違反を解消
- 出典: メタガード 13 (= CP2 監査追加) / Phase 4-a 旧実装

### Major-3: §6.3.1 Stage 3 純増分 1.5× の cat-bitget 純増分試算経路明示
- 修正対象: §6.3.1 Stage 3 詳細
- 修正内容:
  - 「戦略並立 1.5× = cluster 単独寄与」なのか「cluster × Sizing × Exit の全体寄与」なのかを §6.3.1 で明示
  - cluster 単独の場合: $370/月 × 1.5 = $555/月 (= cluster 寄与のみ) の試算と 5.1× 積算経路 (= 業界 §2.6 ケース B 中央値 5.57×) との整合根拠を明示
  - cluster × Sizing × Exit 全体の場合: 戦略並立 1.5× を 3 工程で按分する経路 (= 各工程 √1.5 ≈ 1.14× or 不等按分) を §6.3.1 で明示
- 出典: industry_benchmark §2.3 / §2.6

### Minor-1: §6.3.7 entry_id 生成タイミングの leak verify + 再命名プロトコル厳格化
- 修正対象: §6.3.7 leak 防止 6 経路 + §6.3.5 再命名プロトコル
- 修正内容:
  - entry_id 生成式を §6.3 / §6.2 / §6.0 のいずれかに明示 (= Entry ML primary 出力 + entry_ts に基づく id 等)・未来情報 (= MFE/MAE) 含まないか verify 経路追加
  - §6.3.5 再命名後の Stage 1 silhouette > 0.3 再 verify 経路明示 (= 再命名で cluster 性質変わる場合、Stage 1 評価指標も再計算必要)

---

## CC プロセス欠陥対策 (= cc_role §1.4.6 改訂提案)

### 該当発見: 3 回連続で「メタガード追加が機械的フォーマット化されて逆効果化」する構造的問題

CP1 監査で改善 10-12 追加・CP2 監査でメタガード 13-15 追加。本 CP3 監査で:
- メタガード 13 (機械的フォーマット化検出): §6.3 全 7 サブセクションで「cat-bitget 固有 verify」セクションが機械的並列配置 + 定量試算ゼロ
- メタガード 14 (第一段階固定値の事前根拠厳格化): silhouette > 0.3 / 0.15-0.20 / 純増分 1.5× で業界引用 + 架空推定値・実測なし
- メタガード 15 (設計矛盾自己検出 Q&A): Q&A 形式自体が機械的形式化 + 内容が循環論証 or 趣旨取り違え

これは「**同じ訓練ベース AI (= Claude 系) でガード追加では構造的に止まらない**」3 回連続実証。CP4 監査で改善 16-18 を追加しても同型問題再演リスク高。

### 提案: cc_role §1.4.6 にメタガード追加経路の打ち切り + 設計プロセス自体の見直し

ガード追加の連鎖を打ち切り、以下の経路に切り替える:

#### A. 設計時に「**他訓練ベース AI** (= ChatGPT / Gemini 等) による独立第三者レビュー」を CC 自身で実施
- まこさん課金外で外部 AI 使用不可制約はあるが、CC は WebSearch / WebFetch で「他訓練ベース AI の出力公開事例」を能動的に取り込み・引用する経路を制度化
- 業界 standard 出典に加え、「他訓練ベース AI が同じ設計に賛同/否定する根拠」を 1 件以上引用

#### B. 設計時に「**人間まこさんの素人感覚レビュー**」を強制経由
- まこさんは ML 知見ないが、「メタガード追加が機械的フォーマット化されている」「説明がわかりづらい」を直感的に検出可能 (= 本セッション L-232/L-233/L-235 で実証)
- 設計提案前に「まこさんに 1 回 read してもらい、わかりやすいか + 機械的形式化していないか」の直感判定を経由必須化

#### C. 設計時に「**プロセス自体の認知バイアス検出メタガード**」(= メタガードのメタガード) を追加
- 「メタガード 13/14/15 を自分で機械的に並べていないか」の自己問診を設計提案前に必須化
- 「業界 standard verify セクション」「cat-bitget 固有 verify セクション」「整合性 Q&A」等の機械的形式が 3 サブセクション以上連続で並列配置されていたら設計プロセスを一旦停止し、構造を再設計

### 提案: 本監査結果を L-236 として lessons_active.md に記録

本監査で発見した「CP1/CP2/CP3 同型問題の 3 回連続再演 + メタガード追加が機械的フォーマット化される構造的問題」は、L-220 (= 暫定値・閾値の data-driven 経路宣言違反) + L-230 (= 業界フレーム逃避癖) + L-232 (= 雑な言い切り癖) + L-233 (= CP1 同型問題) + L-235 (= CP2 メタガード追加) の **連続事案の終端**として L-236 を新規立てる必要。cc_role §1.4.6 改訂 (= 上記 A/B/C 経路追加) と紐付ける。

### 提案: §6.3 設計反映時の「機械的反映禁止」(= cc_role §1.5.5 厳格化整合・3 回目連続強調)

CP1/CP2/CP3 監査結果反映時に CC が「監査結果 N 件 100% 反映 = 機械的反映」と称してスキップせず、本監査の改善方向性 7 件 (= Critical 3 + Major 3 + Minor 1) を **設計判断含む反映**として CC 独立評価プロセス (= 1 件ずつ採用支持/要再評価/拒否 + 根拠提示) を必ず通す。特に Critical 2 (= ensemble 第一段階採用) と Critical 1 (= silhouette 実測値確定) は本セッション中に定量試算を実施し、§6.3 設計に反映後に CP4 監査で再 verify 必須。

---

## Sources (= 本監査で参照した外部 URL)

- [Springer Nature 2025 Cryptocurrency Trading Optimization](https://link.springer.com/article/10.1007/s44163-025-00519-y)
- [PMC 12571449 Crypto Predictive Accuracy](https://pmc.ncbi.nlm.nih.gov/articles/PMC12571449/)
- [MDPI Bitcoin Crisis Periods 14/3/51](https://www.mdpi.com/2227-9091/14/3/51)
- [Johal Blockchain Transaction Clustering K-Means/DBSCAN/GMM](https://johal.in/blockchain-transaction-clustering-using-unsupervised-learning-algorithms/)
- [MDPI K-Means Z-Score Bitcoin Anomaly 2227-9709](https://www.mdpi.com/2227-9709/12/2/43)
- [DSFE 2025 Cluster Ensemble](https://www.aimspress.com/aimspress-data/dsfe/2025/3/PDF/DSFE-05-03-017.pdf)
- [arxiv FinRL Crypto 2501.10709](https://arxiv.org/pdf/2501.10709)
- [Shadecoder HDBSCAN Guide 2025](https://www.shadecoder.com/topics/hdbscan-a-comprehensive-guide-for-2025)
- [HDBSCAN docs Parameter Selection](https://hdbscan.readthedocs.io/en/latest/parameter_selection.html)
- [GeeksforGeeks HDBSCAN](https://www.geeksforgeeks.org/machine-learning/hdbscan/)
- [scikit-learn HDBSCAN](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html)
- [LightGBM 4.6 Advanced Topics Categorical](https://lightgbm.readthedocs.io/en/latest/Advanced-Topics.html)
- [LightGBM Features Native Categorical](https://lightgbm.readthedocs.io/en/latest/Features.html)
- [apxml LightGBM Categorical Features](https://apxml.com/courses/mastering-gradient-boosting-algorithms/chapter-5-lightgbm-light-gradient-boosting/lightgbm-categorical-features)
- [ML Journey LightGBM Categorical](https://mljourney.com/how-does-lightgbm-handle-categorical-features/)
- [scikit-learn Common Pitfalls Data Leakage](https://scikit-learn.org/stable/common_pitfalls.html)
- [Medium pacosun Cross-Validation Data Leakage](https://medium.com/@pacosun/split-smart-avoiding-data-leakage-in-cross-validation-894863a93553)
- [DataSchool Pandas Sklearn Data Leakage](https://www.dataschool.io/machine-learning-data-leakage/)
- [Quantinsti PCA in Trading](https://blog.quantinsti.com/principal-component-analysis-trading/)
- [ACM K-means via PCA (Ding/He)](https://dl.acm.org/doi/10.1145/1015330.1015408)
- [Medium PCA K-Means Implementation R](https://medium.com/@zullinira23/implementation-of-principal-component-analysis-pca-on-k-means-clustering-in-r-794f03ec15f)
- [Grokipedia Silhouette Clustering](https://grokipedia.com/page/Silhouette_(clustering))
- [Medium Govindaraj High-Dimensional K-Means](https://medium.com/@govindarajpriyanthan/clustering-in-high-dimensional-space-building-and-evaluating-a-custom-k-means-algorithm-49802d63a6fc)
- [NumberAnalytics Silhouette Score Guide](https://www.numberanalytics.com/blog/mastering-clustering-evaluation-with-silhouette-score)
- [MachineLearningMastery K-Means Silhouette](https://machinelearningmastery.com/k-means-cluster-evaluation-with-silhouette-analysis/)
- [arxiv 2507.08311 CAS Silhouette](https://arxiv.org/pdf/2507.08311)

---

監査結果ファイル終わり。
