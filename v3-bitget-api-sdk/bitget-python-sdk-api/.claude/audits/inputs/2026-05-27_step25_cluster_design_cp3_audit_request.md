# 【監査依頼】工程 [2.5] cluster 分類 詳細設計 CP3 監査

---

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 N 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-Q7 + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて結果ファイル `.claude/audits/2026-05-27_step25_cluster_design_cp3_audit_report.md` を Write
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / NO-GO / PIVOT / OTHER)
   - 最優先指摘 (Critical) 件数

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)

---

## 監査依頼メタ情報

- 依頼日: 2026-05-27
- 依頼者: CC (起案者・メインセッション)
- 監査区分: CP3 (= 工程 [2.5] cluster 分類 詳細設計監査)
- 監査対象タスク: `ml_pipeline_baseline_v1.md` v3.8 §6.3.0〜§6.3.7 全 7 サブセクション + 既存 §6.3 廃止 17 行
- 結果ファイル保存先: `.claude/audits/2026-05-27_step25_cluster_design_cp3_audit_report.md`
- 入力ファイル保存先 (本依頼書): `.claude/audits/inputs/2026-05-27_step25_cluster_design_cp3_audit_request.md`

---

## 監査依頼の経緯

1. 2026-05-27 セッションで工程 [2] Entry ML 詳細設計 §6.2.1〜§6.2.8 完成 + CP2 監査 PIVOT 全 6 件採用反映完遂後、まこさんから「[2.5] cluster 分類詳細設計を [2] Entry ML 実装着手より先にやりたい」と方針転換指示。
2. ベースアップ (= KB 3 件 Read + WebSearch 5 件) 後、議論順序 = §6.3.3 → §6.3.2 → §6.3.4 → §6.3.1 → §6.3.5 → §6.3.6 → §6.3.7 でフル詰めし、`ml_pipeline_baseline_v1.md` v3.7 → v3.8 に書き起こした (= +755 行・約 500 行が §6.3 新規)。
3. CP1 (regime ensemble) / CP2 (Entry ML) 両方とも PIVOT Verdict + 全件採用支持で重要指摘発見の実績あり。本工程も同型監査経路で同型バイアス検出 + 設計欠陥洗い出しが必要 (= cc_role §1.4 #3 同型バイアス対策)。
4. 本セッション L-232/L-233/L-235 で「わかりやすく解説」指摘 6 回連続違反 + §6.2 設計が CP1 監査同型問題を完全再演 (= 機械的フォーマット化検出メタガード追加) の構造的問題あり。CC 単独で完璧な設計は実証的に困難なため独立監査経路必須。

---

## 着手前必読 (省略禁止・auditor 用・7 件)

1. `bitget-python-sdk-api/.claude/memory/ml_pipeline_baseline_v1.md` v3.8 §6.3.0〜§6.3.7 (= L1571〜L2120 相当・本監査の主要対象・約 750 行) — 本依頼書で監査対象として指定
2. `bitget-python-sdk-api/.claude/memory/ml_pipeline_baseline_v1.md` v2.8 §6.1.1〜§6.1.6 — 同型構造比較対象 (= 工程 [1.5] regime ensemble 詳細設計 + CP1 監査反映後)
3. `bitget-python-sdk-api/.claude/memory/ml_pipeline_baseline_v1.md` v3.7 §6.2.1〜§6.2.8 — 同型構造比較対象 (= 工程 [2] Entry ML 詳細設計 + CP2 監査反映後)
4. `bitget-python-sdk-api/.claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md` — CP1 監査 PIVOT 結果 (= 同型バイアス検出パターン参考)
5. `bitget-python-sdk-api/.claude/audits/2026-05-27_step2_entry_ml_design_cp2_audit_report.md` — CP2 監査 PIVOT 結果 (= メタガード追加根拠)
6. `bitget-python-sdk-api/.claude/memory/industry_benchmark_knowledge_base.md` §2.3 — 戦略並立 1.5× レバー業界実証根拠
7. `bitget-python-sdk-api/.claude/rules/phase_compliance_checklist.md` §4a.1〜§4a.5 — Phase 4-a 旧実装 leak 防止規律 (= §6.3.7 整合対象)

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = 工程 [2.5] cluster 分類 詳細設計の業界整合性 + leak 防止網羅性 + 5.1× 積算経路整合性 + 同型バイアス検出。実装着手後の Stage 1〜4 実測値判定は対象外 (= 別監査スコープ)。

---

## 監査対象の事実データ

### §6.3.0 概要 (= L1571〜L1577 相当)

- 工程 [2] Entry ML 後段に独立工程として配置
- 教師なし学習 (= 正解ラベルなし) で Entry trade の質を自動分類
- グループ別 [3] Sizing / [4] Exit で戦略並立 1.5× レバー寄与 ([industry_benchmark §2.3] 業界実証 1.2-1.8× 中央値)
- 詳細議論順序: §6.3.3 → §6.3.2 → §6.3.4 → §6.3.1 → §6.3.5 → §6.3.6 → §6.3.7

### §6.3.1 評価方法

4 段階構造 (= §6.1.1 / §6.2.1 と同型):

| 段階 | 何を見る | 合否ライン |
|---|---|---|
| Stage 1 | グループ分けの統計的質 | silhouette score > 0.3 + inertia + 偏り + regime 相関 + 旧 14 列版比較 |
| Stage 2 | まこさん視認 + 分布チェック | グループ別予測値分布が見て区別がつく + Exit 抜き PnL proxy |
| Stage 3 | [3]/[4] 完成後の PnL 早期判定 | 純増分 (b)/(a) ≥ 1.5× (= cluster あり vs なしの倍率) |
| Stage 4 | Phase 5 全 12 ヶ月 Replay 最終 PnL | 月次 NET ≥ $1,900 全月クリア |

Stage 1 詳細:
- silhouette score > 0.3 (= scikit-learn 業界 minimum)
- cluster 別 trade 数の偏り最小 ≥ 5%
- regime cluster との予測誤差相関 Pearson < 0.5 (= KB §2.3 Square Root Rule 前提)
- 旧 14 列版 (= Phase 4-a) との比較で新 PCA 版 silhouette 改善

### §6.3.2 アルゴリズム選定

- **採用 = k-means 単体 + Gaussian kernel 確率変換** (= σ = cluster median 距離)
- 距離計算 = Euclidean (= scikit-learn default)
- 初期化 = k-means++ (= scikit-learn default)
- 不採用 = GMM / HDBSCAN / ensemble
- 第二段階保留 = Stage 1 silhouette < 0.3 で GMM / HDBSCAN / ensemble 検討経路

### §6.3.3 入力特徴量設計

- **採用 = 案 b 全投入 (= 2,666 列)** + PCA 50-100 主成分 + RobustScaler fold 別 fit + regime 6 列統合
- 内訳: Entry ML 56 ラベル予測値 + 元特徴量 2,604 列 + regime 6 列 = 2,666 列
- 不採用 = 案 a (= 予測値のみ 56) / 案 c (= 厳選数十列) / 案 d (= 予測値 + regime + ボラ厳選)
- 第二段階保留 = Stage 1 で cluster 効果薄ければ Clustered MDA で 20-50 列に絞り込み

### §6.3.4 k (グループ数) 決定方法

- **採用 = k ∈ {3, 4, 5} 並列試行 + silhouette 最大採用 + elbow 確認 + 偏り ≥ 5% + 業界経験則 (= 3-5 cluster で 1.5× レバー)**
- フォールバック = k=6 検討 (= 最後手段・統計弱体化リスク許容)

### §6.3.5 ラベル付け

- **採用 = train 期間で 4 軸 (TP_prob / MFE / SL_prob / 保有時間) の cluster 別統計値で post-hoc 命名**
- test には mapping 適用のみ (= leak 防止)
- 命名形式 = snake_case 英語 (= scalp / long_term / risky / avg)
- 名前は dashboard / デバッグ用で後段戦略は数値ベース実装

### §6.3.6 出力 → 後段接続

- **採用 = 主要 7 列 + 派生 one-hot 列 + parquet 保存 + entry_id ベース merge + causal alignment**
- 主要列: cluster_id / cluster_prob_X / cluster_label / cluster_confidence / cluster_silhouette
- 派生列: is_scalp / is_long_term / is_risky / is_avg
- 保存場所: `results/priority_rebuild/cluster_step1/cluster_predictions_{train,test_2025,test_2026_q1}.parquet`
- joblib artifact: `cluster_kmeans_train_2021_2024.joblib` / `pca_train_2021_2024.joblib` / `scaler_train_2021_2024.joblib`

### §6.3.7 leak 防止

leak 経路 6 項目:

| # | 経路 | 防止策 |
|---|---|---|
| 1 | k-means の fit に test 期間データを含める | fit は train 期間のみ |
| 2 | PCA の fit を test 期間で行う | PCA fit も train 期間のみ |
| 3 | RobustScaler の fit を test 期間で行う | scaler fit も train 期間のみ |
| 4 | Entry ML 出力が leak 含む | §6.2.8 leak 防止整合 |
| 5 | k 数決定 (= silhouette 計算) を test 期間で行う | k 探索も train 期間のみ |
| 6 | cluster label (= post-hoc 命名) を test 期間で決定 | 命名も train 期間のみ |

artifact 命名規律 = `*test*` 含む joblib 禁止 + 起動時 assertion

---

## 監査スコープ

### 監査対象 (本監査内)

- §6.3.1 評価方法 4 段階 (= silhouette > 0.3 / 純増分 1.5× の業界整合性 + cat-bitget 固有値の整合)
- §6.3.2 アルゴリズム k-means 単体採用根拠 (= GMM / HDBSCAN / ensemble 不採用の業界整合)
- §6.3.3 入力特徴量 2,666 列全投入 + PCA 50-100 (= cluster-then-predict 業界 standard 整合)
- §6.3.4 k ∈ {3, 4, 5} data-driven (= 業界経験則 3-5 cluster との整合)
- §6.3.5 ラベル付け 4 軸命名 (= TP_prob / MFE / SL_prob / 保有時間)
- §6.3.6 出力 7 主要列 + 派生 one-hot (= AFML Ch.16 / scikit-learn 業界 standard)
- §6.3.7 leak 防止 6 経路網羅性 (= 教師なし学習 leak 経路漏れ検出)
- §6.1.4 regime k-means と §6.3.2 entry cluster k-means の役割分離整合性 (= 同型構造で目的軸の違い)
- 5.1× レバー積算経路 (= ケース B 中央値) で戦略並立 1.5× を本工程担当の整合性
- cc_role §1.4.6.1 メタガード 13/14/15 機械運用の本工程設計への適用品質

### 監査対象外 (現時点で判定不可能 or 別監査スコープ)

- 実装着手後の Stage 1〜4 実測値判定 → Stage 1 完了後別監査
- [3] Sizing / [4] Exit との接続実装品質 → [3]/[4] 詳細設計完了後別監査
- Phase 5 / 6-b Replay 月次 NET 達成判定 → Phase 5 完了後別監査

---

## 監査観点 (一般・auditor_template ①〜⑦)

- ①統計学的妥当性 — silhouette > 0.3 / 純増分 1.5× 等の合格ライン値が統計的に妥当か
- ②リスク管理 — cluster 別 [3] Sizing で過大ポジション化リスクがないか・0.12 BTC 合計上限規律と整合か
- ③認知バイアス — CC が「k-means 業界 standard だから」を判断根拠化していないか (= 業界フレーム逃避癖・L-230 同型)
- ④ソフトウェア工学 — artifact 命名規律 + 起動時 assertion + Pipeline 化が実装可能か
- ⑤再現性 — fold 別 fit + joblib 保存 + assert no look-ahead で再現性確保されているか
- ⑥実行プロセス — §6.3.0〜§6.3.7 の論点が機械的フォーマット化されただけで本質的に効いていない CP2 同型問題が再演していないか
- ⑦主エージェントバイアス — メインセッション CC が議論で生成した新規工程である [2.5] cluster の存在自体が局所判断に偏っていないか

---

## 監査観点 (本監査固有・Q1-Q7)

### Q1 — 入力特徴量設計 §6.3.3 案 b 全投入 (= 2,666 列) + PCA 50-100 主成分の業界整合性

(a) cluster-then-predict 業界 standard で「予測値 + 元特徴量全投入 + PCA」経路は妥当か? 業界実装事例 (= Crypto / 5min bar / 2026 標準) の typical 範囲を WebSearch で verify。
(b) PCA 主成分数 50-100 暫定は「分散 95% 説明」前提だが、cluster 用途で 50-100 範囲は業界 standard か? Crypto / 高頻度 5m bar での実装例調査。
(c) 案 b (= 全投入) vs 案 c (= 厳選) のどちらが silhouette 改善に寄与するか業界実証ある?

### Q2 — アルゴリズム選定 §6.3.2 k-means 単体 + Gaussian kernel 確率変換の業界整合性

(a) 2025 crypto cluster 業界 standard は K-Means / DBSCAN / GMM の **ensemble** だが、§6.3.2 で第一段階 k-means 単体採用は業界後退ではないか? cluster ensemble の crypto 5m bar 実装で純増分実証ある?
(b) Gaussian kernel σ = cluster median 距離は §6.1.5 regime ensemble と同型運用だが、cluster 用途で適切な σ 設定の業界 standard は他にあるか? (= adaptive σ / per-cluster σ 等)
(c) HDBSCAN 不採用根拠「k 数が不安定 → 後段固定戦略と相性悪い」は妥当か? HDBSCAN の cluster 数固定化技法 (= min_cluster_size 等) で対応可能ではないか?

### Q3 — k 数決定 §6.3.4 k ∈ {3, 4, 5} data-driven の業界経験則整合

(a) industry_benchmark §2.3 で「3-5 cluster で 1.5-2× Sharpe 改善」だが、5min bar の Entry trade clustering で k=3,4,5 が業界 typical 範囲か? Crypto / 5m bar / 56 万行 dataset での実装例調査。
(b) Phase 4-a 旧実装 k=12 が「過剰」と判定された根拠は「分離不十分」だが、k=12 を 3-5 に絞ることで「異なる戦略タイプの取りこぼし」リスクはないか? 業界経験則と Phase 4-a 失敗事例の整合性 verify。
(c) elbow method と silhouette score が食い違った場合の業界 standard 決定方法 (= gap statistic / BIC / ONC algorithm) を §6.3.4 は採用していないが、追加検討必要か?

### Q4 — 評価方法 §6.3.1 Stage 1 silhouette > 0.3 / Stage 3 純増分 1.5× の合格ライン妥当性

(a) silhouette > 0.3 業界 minimum の出典は scikit-learn 公式だが、crypto / 高次元 (= PCA 50-100) cluster 用途で 0.3 は適切か? 業界実装で typical silhouette 値の調査。
(b) Stage 3 純増分 (b)/(a) ≥ 1.5× の根拠は industry_benchmark §2.3 中央値だが、cat-bitget 旧 Priority $370/月 base line から純増分 1.5× = $555/月で 5.1× 積算経路の中央値 $2,060/月 ($1,900 合格 + 8% マージン) に届く論点整合は妥当か?
(c) Stage 1 「旧 14 列版との比較」を合格基準に入れているが、Phase 4-a 14 列版の実測 silhouette が「0.15-0.20」と推定されているのみで実測値ではない。実装着手前に推定値を確定すべきではないか?

### Q5 — leak 防止 §6.3.7 6 経路の網羅性

(a) 教師なし学習 leak 経路として §6.3.7 が網羅した 6 項目 (= k-means fit / PCA fit / scaler fit / Entry ML 出力 leak / k 探索 / 命名) 以外の経路はないか? 業界事例 (= AFML Ch.7 + scikit-learn) の漏れ verify。
(b) §6.3.6 出力で entry_id ベース merge を採用しているが、entry_id 自体の生成タイミングが leak 経路にならないか? entry_id 生成時に未来情報を含む列を使っていないか verify。
(c) cluster label の post-hoc 命名で「Stage 2 視認で再命名」が許容されているが、train fold 内での再命名と test fold 反映の境界が曖昧。命名再変更プロトコルの厳格化必要か?

### Q6 — 出力 → 後段接続 §6.3.6 設計の業界整合性

(a) 出力 7 主要列 + 派生 one-hot 列の構造は AFML Ch.16 / §6.1.6 regime と同型だが、cluster_silhouette (= 各 trade の はみ出し度) を出力列に含む業界事例ある? 後段 [3]/[4] が cluster_silhouette をどう活用するか業界実装例調査。
(b) 派生 one-hot 列の k=4 想定だが、k=3 / k=5 の場合の列数調整プロトコルが明示されていない。k 数確定後の列数決定経路を詳細化必要か?
(c) cluster_id を直接食う vs one-hot 列を食う の比較で「業界 practice として one-hot 推奨」と書かれているが、LightGBM 4.0+ では native categorical support で one-hot 不要の慣行に変わっている。最新 LightGBM 業界実装の整合性 verify。

### Q7 — §6.1.4 regime k-means と §6.3.2 entry cluster k-means の役割分離整合性

(a) 同じ k-means を 2 工程で並行使用する設計だが、§6.1.4 regime は「市場局面判定 (大局)」・§6.3.2 entry cluster は「trade 質分類 (局所)」と論点軸を分離している。業界実装で同型構造 (= regime + entry cluster の 2 段 k-means) の事例ある? 重複 vs 補完の判定。
(b) regime k-means 出力 (= 6 列) を entry cluster k-means の入力 (= 案 b の一部) に含む設計だが、predicting outcome (= entry cluster の cluster_id) が input (= regime 6 列) の関数になる構造で「regime と entry cluster の予測誤差相関 Pearson > 0.5」リスクの定量的予測必要か?
(c) Stage 1 で「regime cluster との予測誤差相関 Pearson < 0.5」verify を入れているが、相関が > 0.5 となった場合の対応経路「入力 §6.3.3 で regime 6 列除外検討」は妥当か? regime 6 列除外で cluster の市場文脈情報が失われるリスクとのトレードオフ verify。

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

`.claude/memory/technical_analysis_knowledge_base.md` 等の内部知識に閉じない。auditor は以下の **外部検索を必ず実施** すること。ChatGPT 等の外部 AI 使用不可 (まこさん課金外)。

### 検索対象

1. **Crypto 5m bar Entry trade post-prediction clustering 業界実装**:
   - クエリ案: `crypto 5min bar entry signal post-prediction k-means clustering 2025 2026`
   - 期待発見: 業界 typical k 範囲・silhouette 実測値・cluster-then-predict 純増分実証
2. **cluster ensemble (K-Means + DBSCAN + GMM) の crypto 純増分実証**:
   - クエリ案: `cluster ensemble crypto trading robustness improvement K-Means DBSCAN GMM 2025`
   - 期待発見: ensemble vs 単体の純増分倍率
3. **HDBSCAN cluster 数固定化 (min_cluster_size) crypto 実装**:
   - クエリ案: `HDBSCAN fixed cluster count crypto trading min_cluster_size 2025`
   - 期待発見: HDBSCAN 不採用根拠の業界反証
4. **LightGBM 4.0+ native categorical support vs one-hot encoding 業界 best practice**:
   - クエリ案: `LightGBM native categorical feature support vs one-hot encoding 2025 2026`
   - 期待発見: LightGBM 4.0+ で one-hot 不要慣行の業界実装
5. **教師なし学習 leak 経路網羅 (AFML Ch.7 / scikit-learn Pipeline)**:
   - クエリ案: `unsupervised learning data leakage prevention scikit-learn Pipeline fold AFML Lopez de Prado`
   - 期待発見: §6.3.7 6 経路以外の leak 経路漏れ
6. **PCA 主成分数 cluster 用途業界 standard (分散 95% 説明 vs Kaiser criterion)**:
   - クエリ案: `PCA principal components number selection k-means clustering 50 100 trading 2025`
   - 期待発見: PCA 主成分数 50-100 業界 typical 範囲
7. **silhouette score 業界 minimum crypto high-dimensional clustering**:
   - クエリ案: `silhouette score minimum threshold crypto high-dimensional k-means clustering 2025`
   - 期待発見: silhouette > 0.3 業界 minimum の crypto / 高次元用途整合性

---

## 結果ファイルフォーマット (auditor 用)

`.claude/audits/2026-05-27_step25_cluster_design_cp3_audit_report.md` に以下 7 セクションを出力:

1. **Step -1 監査対象の型宣言** (混合型: 文書型 + 数値型 + アルゴリズム型 / 該当する型を明示)
2. **Step 0 指摘前提確認** (事実データ verify + spec 文言 verify)
3. **観点 ①〜⑦ + Q1-Q7 の所見** (各観点・各 Q に対し「数値根拠ある断言」or「データ不足 (理由)」)
   - 観点 = PASS / FAIL 明示
   - Q = 業界整合 / 改善余地 N 件 明示
4. **外部検索結果サマリー** (検索クエリ + 主要発見 5-10 件・URL or 論文出典)
5. **総合判定**:
   - Verdict: GO / NO-GO / PIVOT / OTHER
   - 業界基準・学術根拠を伴う根拠
6. **改善方向性** (具体提案 3-7 件・優先度明示 Critical/Major/Minor)
7. **CC プロセス欠陥対策** (cc_role §1.4.6 改訂提案・該当があれば)

---

## 必ず守ること (auditor 守則)

- **目標 ($1,900/月) 達成可能性判定は対象外**の場合は明示
- 月次 NET ≥ $1,900 を下げる方向の提案禁止 (cc_role §1.0 / auditor_template L15)
- 「可能性がある」「かもしれない」「検討の余地」は禁止 (auditor_template L20)
- 数値根拠の断言 or 「データ不足 (理由: 〇〇)」で答える
- 同型バイアス警告: 同一訓練ベース AI として CC の論理に共感しすぎないこと (auditor_template L24-30)
- ChatGPT 等の外部 AI 使用不可
- **外部検索は WebSearch / WebFetch ツールで必ず実施**
- 内部文書だけでなく、トレードについての外部認知 (Crypto futures algo trading の業界実情) を踏まえる
- **本セッションで L-232/L-233/L-235 改善 2 違反「わかりやすく解説」指摘 6 回連続 + CP1 監査同型問題 §6.2 設計再演 (= 機械的フォーマット化検出メタガード追加) の構造的問題ありの認識を持つ**・本工程 §6.3 にも同型再演がないか厳格 verify

---

依頼書終わり。

## まこさん向け呼びかけ例文 (新規セッション起動時)

別 Claude Code セッションを開き、本依頼書のフルパスを明示して以下のように依頼:

```
監査してほしい
.claude/audits/inputs/2026-05-27_step25_cluster_design_cp3_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。
