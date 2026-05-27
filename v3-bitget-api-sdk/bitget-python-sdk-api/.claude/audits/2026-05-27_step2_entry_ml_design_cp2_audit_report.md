# 工程 [2] Entry ML 詳細設計 §6.2.1〜§6.2.8 CP2 監査結果

監査実施日: 2026-05-27
監査者: Plan サブエージェント (cold start・独立監査・メインセッション CC context 非共有)
依頼書: `.claude/audits/inputs/2026-05-27_step2_entry_ml_design_cp2_audit_request.md`

## Step -1 監査対象の型宣言

監査対象 = **詳細設計レビュー** (= 文書型・実装スクリプトはない段階)。

- 対象ファイル: `ml_pipeline_baseline_v1.md` §6.2.1〜§6.2.8 (= v3.0 → v3.6 の 8 サブセクション・約 1,029 行 = L555-L1542 = 該当範囲約 988 行・「約 700 行」表記は WebSearch / 教科書整合 + 業界差分 + 設計判断根拠 + 懸念 + data-driven 経路宣言 を含む本体記述行ベース)
- 対象範囲: 評価方法 4 段階 / アルゴリズム選定 / ラベル設計詳細 / 入力特徴量設計 / CV 設計 / ハイパラ探索 / 出力 → entry 判定 / leak 防止 の 8 サブセクション
- 監査区分: CP2 (= 第 2 回詳細設計監査・実装着手前)
- 結果出力: 業界整合性 + cat-bitget 固有制約整合性 + Phase 1 v6 教訓反映 + leak 防止経路 + 内部一貫性 verify (= 月次 NET ≥ $1,900 達成可能性判定は本監査対象外・Stage 3/4 で実証)

## Step 0 指摘前提確認

### 0.1 依頼書本文 view 証跡

- 依頼書 wc -l = **323 行** (一致)
- 監査観点 = 一般 ①〜⑦ + 本監査固有 Q1〜Q7 + 外部検索 6 件以上
- 結果フォーマット = 7 セクション (Step -1 / Step 0 / 観点・Q 所見 / 外部検索サマリー / 総合判定 / 改善方向性 / CC プロセス欠陥対策)
- スコープ外明示 = 月次 NET ≥ $1,900 達成可能性判定 (Stage 3/4 で実証)

### 0.2 着手前必読 8 件 view 証跡

| # | ファイル | wc -l | 1 行要約 |
|---|---|---|---|
| 1+2+3 | ml_pipeline_baseline_v1.md (=本体) | 1584 | §6.2.1〜§6.2.8 = 4 段階評価 / LightGBM 56 個独立並列 (MultiOutputRegressor) / K 別 ATR multiplier / 案 A 統合 regime 6 列 / Walk-Forward Purged K-Fold 5 fold + embargo 2 day / Optuna 30 trials + L1/L2 / ルール集約 + 短期 K 重視 + threshold 0.6 / 4 点 leak verify。§1 [2] 1 行スキーマ + §4 決着表 [2] 行と整合 |
| 4 | industry_benchmark_knowledge_base.md | 420 | 5 レバー寄与中央値ケース B = Entry 1.4× × Exit 1.7× × 並立 1.5× × regime 1.3× × Sizing 1.2× = 5.57× → 月 $2,060。Square Root Rule (= 戦略並立効果は無相関前提) + DSR (= IS→OOS degradation 30-70%) |
| 5 | cc_entry_logic_self_study.md §13.1/13.5/14.1/14.2 | 2485 | §13.1 LightGBM/XGBoost/CatBoost 業界 range (num_leaves 15-127 等)・案 a-f LightGBM 単独で多様性ゼロを Phase 1 v6 失敗主因の 1 つに同定 / §13.5 Bagging/Boosting/Stacking + AFML Ch.3 Meta-Labeling 「primary が悪いと meta も救えない」 / §14.1 Triple Barrier (TP/SL/Time 3 barrier multiclass)・ATR-based dynamic barrier の業界拡張 / §14.2 Meta-Labeling Half-Kelly 接続 |
| 6 | false_positive_incident_policy.md §0-1 | 225 | §0-1 Prime Directive (= t 時点で因果的に取得可能な変数のみ使用)・MFE/MAE 等の保有期間中最大値は本番取得不可・proxy 偽装 = 類型 F |
| 7 | phase_compliance_checklist.md §-1/§0/§1 | 224 | §-1 USD 絶対値系 64 列 blacklist (= 8 family × 8 TF) / §0 Phase 0 leak verify 5 段階通過済 / §1 Phase 1 fractal blacklist 3 段階運用 (top1-20 hit 時の物理 leak verify 4 項目セット) |
| 8 | 2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md | 381 | Verdict PIVOT・Critical 2 件 (= C1 ensemble キャリブレーション欠陥 / C2 ATR 絶対値 250/100 価格非依存性違反) + Major 3 件 (= base line 再定義 / 重み GridSearchCV / merge_asof causal alignment 明示) + Minor 2 件 + cc_role §1.4.6.1 改善 10/11/12 追加提案。本 §6.2 設計は v2.8 で全 7 件採用済 |

### 0.3 §6.2 設計本体の事実 verify (= 依頼書 §監査対象の事実データ vs L555-L1542 照合)

| 依頼書本文記載 | §6.2 実本文 | 一致 |
|---|---|---|
| §6.2.1 = 4 段階 Stage 1-4 + base line 旧 Priority v9 月 $370・純増分 ≥ 5.1× で目標達成 | L575-647 (Stage 1: RMSE/R²/logloss/F1/AUC/Precision/Recall + 56 ラベル間予測相関 / Stage 2: 視認 + 旧 v9 overlap + 件数 + Exit 抜き PnL proxy / Stage 3: 5.1× / 2.0× / 1.0× 階段 / Stage 4: Phase 5+6-b) | OK |
| §6.2.2 = LightGBM 56 個独立並列 + MultiOutputRegressor + 第二段階 stacking ≥ 1.3× | L649-696 (第一段階 LightGBM 単独 + 第二段階 ≥ 1.3× で stacking 採用 + 計算コスト 2 倍 / DL 10 倍以上 verify) | OK |
| §6.2.3 = 案 C 採用 (K 別 multiplier・短期 K cat_v9 流 / 長期 K AFML 流) + ATR_pct 化 + class_weight balanced + 不足時 SMOTE/focal loss | L698-819 (K=6/12: TP×1.5/SL×2.0 / K=24: TP×2.0/SL×2.0 / K=48: TP×2.5/SL×1.5 / K=96-288: TP×3.0/SL×1.5・ATR_pct ベース・第一段階 class_weight=balanced・Stage 1 recall<0.3 で SMOTE/focal loss) | OK |
| §6.2.4 = 案 A 統合 + 全投入 2,610 列 + MTF 8 TF + regime 6 列 one-hot + 前処理なし + TSFresh 第二段階 | L821-960 (1 LightGBM + regime 6 列・第二段階 regime 間 accuracy 差 > 30% で案 B / 全投入 2,604 + 6 = 2,610 / MTF integrated / one-hot + 確率併用 / Stage 3 < 1.5× で TSFresh) | OK |
| §6.2.5 = 5 fold + train_2021_2024/test_2025/test_2026_q1 + embargo K_max 288 + buffer 1 day = 2 day + Purged K-Fold + CPCV 第二段階保留 | L961-1066 | OK |
| §6.2.6 = Optuna 20-50 trials + TPE + MedianPruner + num_leaves 15-127 / lr 0.01-0.1 / min_child_samples 20-100 / early_stop 50-200 / max_depth -1 or 3-10 / reg_alpha 0-1 / reg_lambda 0-1・3 系統別 tune・計算約 11 時間 | L1068-1216 | OK |
| §6.2.7 = 段階的 (= 第一段階ルール集約 + 第二段階 meta-learner) + 排他 + threshold 0.6 + 即死 reject 危険度 > 0.9 + Meta-Labeling primary/secondary + Half-Kelly | L1218-1391 (LONG_score = TP×0.4 + MFE×0.3 + meta_yes×0.3 / K=12/24 重み 0.5 / 他 K 0.1 / confidence = |LONG-SHORT|/max / 月 < 200 件で 0.5 / 月 > 400 件で 0.7) | OK |
| §6.2.8 = 4 点 verify + regime 6 列 causal alignment + ラベル shift(-K) + CV embargo + feature_importance top 20 + blacklist 64 列除外 + assert len == 2610 | L1393-1541 | OK |

依頼書記載は §6.2 実本文と全項目で一致・**判断材料として有効**。

---

## 観点 ①〜⑦ + Q1-Q7 の所見

### 観点 ① 統計学的妥当性: **FAIL (Major)**

1. **class_weight='balanced' の確率推定悪化を §6.2.7 集約式が無対策で消費している (Major)**: §6.2.3 論点 4 で `class_weight='balanced'` 採用 + ⚠️注記 ([LightGBM Issue #3167] / 本監査 WebSearch [LightGBM docs])「Using these class weighting parameters will result in poor estimates of individual class probabilities, and you may want to consider performing probability calibration」 → §6.2.7 集約式 `LONG_score = LONG_TP_prob × 0.4 + LONG_MFE_pct × 0.3 + LONG_meta_yes_prob × 0.3` は **キャリブレーションされていない確率を直接係数 0.4/0.3/0.3 で線形結合**している。これは CP1 監査 Critical-1 (= ensemble soft voting キャリブレーション欠陥) と完全同型問題。Stage 1 にキャリブレーション評価 (= Brier score / reliability diagram / ECE) が定義されていない。
2. **56 ラベル間予測相関 > 0.95 で「冗長」とする閾値の数値根拠が暫定**: §6.2.1 末尾 data-driven 経路宣言で「本セッション暫定・1 fold 結果で再 calibrate」と明示・透明だが、揺れ幅 28 (LONG_MFE_K=6 と LONG_MFE_K=12 は **構造的に同じシグナルの時間幅違い** = 自然相関 > 0.95 になりやすい) の場合に「冗長として削る」と「短期 K 別の予測寄与情報を捨てる」が同時発生し、論点矛盾。
3. **MFE_pct を score 集約に直接投入する scale 整合性欠陥 (Major)**: §6.2.7 論点 1 `LONG_score = LONG_TP_prob × 0.4 + LONG_MFE_pct × 0.3 + LONG_meta_yes_prob × 0.3` で TP_prob (0-1) / meta_yes_prob (0-1) と MFE_pct (回帰値・例: 0.5-3.0%) の **scale が異なる**まま線形加算している。MFE_pct = 1.0% と TP_prob = 0.7 を 0.3/0.4 で重み付けすると、MFE_pct の絶対値次第で score が極端に支配される。標準化 (= z-score or min-max) の明示がない (Major)。
4. **Stage 2 (d) Exit 抜き PnL proxy の TP_gain/SL_loss/fee 固定値は Stage 1 統計指標との混同を防ぐ役割 (PASS 要素)**: §6.2.1 data-driven 経路宣言で「[[exchange_spec]] 確定値 + cat_v9 経験値で暫定」明示・透明。
5. **K=6 (= 30 分) と K=12 (= 1h) の重み統合 (= K=12 のみ重み 0.5・K=6 は 0.1) の根拠が cat_v9 整合のみ**: §6.2.7 論点 1 K 重み K=12/24 = 0.5 主役・他 K = 0.1 等分は data-driven 経路宣言で再 calibrate 経路あり・透明だが Stage 1 段階で明示的な fold 別 K 重み搜索が定義されていない。

**結論**: **FAIL (Major)**。class_weight 確率推定悪化に対するキャリブレーション設計欠落 (= CP1 監査 C1 と完全同型問題) + MFE_pct と確率値の scale 不整合という 2 件の Major 統計学的欠陥が §6.2.7 集約式に貫通している。

### 観点 ② リスク管理: **PASS (Minor 改善余地)**

1. **0.12 BTC 合計上限 (= false_positive §0-2)**: §6.2.7 論点 2「排他 (= 1 bar 1 trade)」採用 + 「0.12 BTC 合計上限制約と整合」明記。本工程は entry_score / direction / confidence 出力工程で、合計上限は [3] Sizing + [5] Risk 工程が担当・直接抵触なし。
2. **即死 reject (= 危険度 > 0.9)**: §6.2.7 論点 4 で「即死 reject (= §1 既決着)」と明示されているが、**「危険度」自体の定義 + 算出方法が §6.2.X 内に明示なし** (Minor)。§1 [2] で「即死リスク (危険度>0.9) のみ reject」と書かれているが、危険度算出式は [3] Sizing の Kelly 基準入力との関係で曖昧。
3. **threshold 0.6 + fold 別 calibrate**: §6.2.7 論点 4 で月 < 200 件で 0.5 / 月 > 400 件で 0.7 と data-driven 調整経路あり・「月 275 件確保ライン未達でも 0.5 まで下げる」明示。

**結論**: **PASS (Minor)**。リスク管理の構造的欠陥なし。「危険度」算出の具体化は実装着手前に補完すべき (Minor)。

### 観点 ③ 認知バイアス: **FAIL (Major)**

1. **業界フレーム逃避癖 (= L-230) の §6.2 再演**: 8 サブセクション全てに「業界 standard verify (= 本セッション 2026-05-27 WebSearch 3 回)」「教科書整合 (= cc_role §1.4.6.1 改善 7)」が機械的に冒頭配置されている。これは CP1 監査 観点 (3) FAIL (= 「業界 standard verify 済を判断根拠化する逆効果」) と同型構造の再演。
2. **規定の機械的フォーマット遵守による網羅性偽装 (Major)**: §6.2.1〜§6.2.8 すべてに「業界 standard verify / 教科書整合 / 業界 standard との差分 / cat-bitget 固有 verify / 統計指標と PnL 指標の分離 / 設計判断根拠 N 件 / 懸念 N 件 + 反論 / data-driven 経路宣言」の 8 ブロック構造が機械的に並列配置されている = **CP1 監査の同型バイアス対策 (= cc_role §1.4.6.1 改善 6-12) を機械フォーマット化することで網羅性を担保した外形**。CP1 監査の所見「項目数並列による網羅性偽装」が再演している。
3. **短期 K 重視 0.5/0.1 の cat_v9 整合根拠と Phase 1 v6 教訓「揺れ幅予測逃げ」の論点矛盾 (Major)**: §6.2.7 論点 1 で「K=12/24 重み 0.5 = 主役」「K=144/288 = 長期戦略向けで cat-bitget ベース案と整合しない」と書き、長期 K の予測情報を 1/5 に圧縮。一方 §6.2.3 では「Phase 1 v6 失敗主因 = 14 ラベルしか学習対象にしてなかった → AI が揺れ幅予測に逃げた」を 56 ラベル並列で構造解消したと主張。**短期 K 重視で「長期 K 予測の寄与を集約段階で人為的に圧縮」している現設計は、Phase 1 v6 教訓「予測対象を物理的に増やす」と論理整合しない**。56 ラベル並列学習で物理的に増やしても、出力集約で 5/7 のホライズン情報を 0.1 (= 14%) に圧縮するなら、「学習はしたが集約で捨てる」構造で目的の解消にならない。
4. **「業界実証 precision 0.85」を arxiv 2501.10709 から引用しているが cat-bitget 5m / 56 ラベル並列 / 短期 K 重視の組合せでの実証なし**: §6.2.7 論点 1 採用根拠 1「業界実証 rule-based precision 0.85 ([arxiv 2501.10709])」で precision 0.85 を業界トップ水準として引用しているが、arxiv 2501.10709 (= ACM ICAIF FinRL Contest 2023/2024) は **PPO 含む RL ensembles 中心の研究**で、LightGBM 56 ラベル並列学習 + ルール集約 0.4/0.3/0.3 の cat-bitget 設計と直接対応する実証ではない。**cat-bitget 過去事例 verify ゼロ** (= cc_role §1.4.6.1 改善 10 違反)。
5. **Optuna 30 trials を「業界主流」とする根拠の薄さ**: §6.2.6 「Optuna 30 trials」を業界主流と書いているが、本監査 WebSearch [Forecastegy] で「In practice, about 30 trials are enough to find a pretty good set of hyperparameters for LightGBM using Optuna」は **「pretty good」レベル**であり、56 モデル × 3 系統 × Walk-Forward 5 fold での最適化十分性は別問題。

**結論**: **FAIL (Major)**。L-230 / L-232 同型バイアスが §6.2 設計全体に貫通し、短期 K 重視と Phase 1 v6 教訓構造解消の論点矛盾が現実問題化している。

### 観点 ④ ソフトウェア工学: **PASS (Minor 改善余地)**

1. **MultiOutputRegressor encapsulate 採用根拠の妥当性**: §6.2.2 で「LightGBM native multi-output 非対応」を WebSearch [Forecastegy / GitHub Issue #524] で verify・実装制約として整合・**56 個独立並列学習であり「inter-target relationships は学習されない」**ことを §6.2.2 懸念 1 で自己認識済 (= 妥当)。
2. **計算コスト試算 (= 約 11 時間 CPU only)** : §6.2.6 論点 4 = 3 系統 × Optuna 30 trials × Walk-Forward 5 fold = 450 学習 × 1.5 分 = 11 時間。Phase 1 v6 実績 (= 14 ラベル × default × 5 fold = 約 1-2 時間) からの算術整合 OK。
3. **56 モデル × feature_importance top 20 自動 monitoring の実装現実性 (Minor)**: §6.2.8 項目 5 で「56 モデル全部について feature_importance top 20 を出力」「各モデル独立評価」と書かれている。56 モデル × top 20 = 1,120 feature row を毎 fold で自動チェック → 計算コストは軽いが、**怪しい列名 (= fractal/pivot/resistance/support/future) の検出ロジック実装が「自動 monitoring」とだけ書かれて具体化されていない** (Minor)。phase_compliance §1.4 で「fractal ベース列ブラックリスト 3 段階運用」は具体化されているが、§6.2.8 にその参照リンクなし。
4. **assert `len(X.columns) == 2610` の妥当性**: §6.2.8 項目 6「assert len(X.columns) == 2604 + 6 = 2,610」は phase_compliance §-1「学習対象 feature 数 = 2,604 (旧 1,414 から増加した版)」+ regime 6 列 = 2,610 と整合・**機械的証跡ベースのガードとして妥当**。
5. **TSFresh 追加時の leak チェック経路の具体性 (Minor)**: §6.2.4 論点 6 「TSFresh leak チェック必須」「[[feedback_ml_leak_mandatory_check]] 4 点 verify」は方針として明示されているが、**TSFresh 794 features の中で `shift(-N)` / `future_window` を含む関数群の具体的識別ロジック** (= `tsfresh.feature_extraction.feature_calculators` の `*_pre_*` 系除外等) が §6.2.X 内に欠落 (Minor)。

**結論**: **PASS (Minor)**。設計レベルでの大きな欠陥なし。自動 monitoring の具体化 + TSFresh leak チェックの具体化は実装時に補完すべき (Minor 改善余地)。

### 観点 ⑤ 再現性: **PASS**

1. **データ範囲 train_2021_2024 / test_2025 / test_2026_q1 統一**: §6.2.5 論点 2 で phase_compliance §0 既決着・regime ensemble §6.1.4 と同型・既存 Phase 0 v3.1 parquet と整合。L-183 (= scaler/km の test fit 違反) 再演防止経路あり。
2. **artifact 命名 / phase_compliance §4a.4 整合**: §6.2 で `*train_2021_2024*` パターン明示・test 文字列禁止と整合 (= 既決着引継ぎ)。
3. **random_state 固定 (暗黙)**: §6.2.6 Optuna TPE sampler default は random_state 引数で固定可能・実装時に明示必要だが本設計レベルでは regime ensemble §6.1.4 と同型継承で再現性確保可。
4. **leak verify 4 点経路 (= §6.2.8 + phase_compliance §-1/§0/§1.4 既決着引継ぎ)**: 設計レベルで重複度高く再現性確保。

**結論**: **PASS**。再現性確保の構造的欠陥なし。

### 観点 ⑥ 実行プロセス: **PASS (Minor 改善余地)**

1. **段階的検証 Stage 1-4 の妥当性**: §6.2.1 で 4 段階 (= Stage 1 統計 → Stage 2 視認 + Exit 抜き PnL proxy → Stage 3 [4] Exit 完成後 PnL 早期判定 → Stage 4 全パイプライン PnL) は CP1 監査 Stage 1-4 と同型・業界整合 (= [arxiv 2401.05337] 統計 + Financial 並行評価)。
2. **第二段階 stacking 採否判定 (= Stage 3 純増分 ≥ 1.3×)**: §6.2.2 で出口設計明確・Stage 3 PnL データ駆動判定の経路あり。
3. **第二段階 案 B (regime 別 model 分離) 採否判定 (= regime 間 accuracy 差 > 30%)**: §6.2.4 論点 1 で出口設計明確・Stage 1 統計指標で判定。
4. **第二段階 CPCV 採否判定 (= Stage 3 純増分 < 2.0× で発動)**: §6.2.5 論点 5 で出口設計明確。
5. **Minor 改善余地**: 第二段階発動条件の **数値根拠が「30%」「1.3×」「1.5×」「2.0×」と複数の異なる閾値が並列存在**しているが、これらの相互整合性 (= 例: 「Stage 3 純増分 < 1.5× で TSFresh」と「Stage 3 純増分 < 2.0× で CPCV」が同時発動する場合の優先順位) が §6.2.X 全体で明示されていない (Minor)。

**結論**: **PASS (Minor)**。実行プロセスの構造的欠陥なし。第二段階発動条件の優先順位整理は実装時に補完すべき。

### 観点 ⑦ 主エージェントバイアス: **FAIL (Critical)**

CP1 監査で発見された「業界 standard を判断根拠化する癖」が §6.2 設計でも完全に同型再演している。具体例:

1. **§6.2.2 LightGBM 56 個独立採用の根拠が「業界 standard」** ([Forecastegy LightGBM Multi-Output] + [LightGBM Issue #524]): 「LightGBM が native multi-output 非対応 → MultiOutputRegressor で encapsulate」は技術制約として正しいが、**「56 個独立学習が cat-bitget 5m / 56 ラベル並列で predict_correlation > 0.95 になるか」の cat-bitget 固有 verify ゼロ**。§6.2.1 で「相関 > 0.95 のペアは冗長」とだけ書き、現状の v15 HMM + Phase 0 v3.1 ラベル parquet で類似の予測相関 verify ができるはずだが実施なし。
2. **§6.2.3 K 別 multiplier 「cat_v9 流 + AFML 流ハイブリッド」の cat-bitget 固有 verify は形式的**: §6.2.3 cat-bitget 固有 verify で「cat_v9 P1, P3, P21, P25 = TP 0.5-1.2% / SL 1.5-2%」「P2, P4, P22, P23, P24 = TP 0.5-0.7% / SL 5%」と書いているが、**これらは cat_v9 の固定パラメータであり「ATR_pct × multiplier」設計が cat_v9 経験値と整合する実証** (= 過去 1 fold データで `ATR_pct × 1.5 = cat_v9 TP 0.5-1.2% に相当するか` の算術 verify) ゼロ。
3. **§6.2.6 Optuna 30 trials の業界主流主張**: 本監査 WebSearch [Forecastegy] で「In practice, about 30 trials are enough」「pretty good」レベルの引用だが、§6.2.6 では「業界主流 (= GridSearchCV より効率) ・56 モデル計算量制約に対応」と書き、**「pretty good」が cat-bitget 月 $1,900 達成水準で「十分」かの cat-bitget 固有 verify ゼロ**。CP1 監査 Critical-2 と同型問題。
4. **§6.2.7 threshold 0.6 採用根拠**: §6.2.7 論点 4 「業界実証値・[arxiv 2501.10709] threshold 0.6 buy 整合」と書いているが、arxiv 2501.10709 は ACM ICAIF FinRL Contest 2023/2024 で **RL ensemble 中心の研究**。cat-bitget LightGBM 56 ラベル並列 + ルール集約 score の出力分布が threshold 0.6 で月 275 件出るかの **暫定試算ゼロ** (= 依頼書 Q5 verify 事項に明示)・data-driven 経路宣言は「fold 別 calibrate」とだけ書かれているが第一段階固定 0.6 の事前根拠が業界引用のみ。

**結論**: **FAIL (Critical)**。CP1 監査で改善対策 (= cc_role §1.4.6.1 改善 6-12) を施したのに、§6.2 設計でも完全同型再演している (= 改善対策が機械的フォーマット化されただけで本質的に効いていない)。これは CP1 監査の P1「Anti-業界フレーム逃避ゲート」(= cc_role §1.4.6.1 #10「cat-bitget 固有 verify」) を導入したのに、§6.2 設計でも「cat-bitget 固有 verify」セクションが機械的に並列配置されただけで verify 内容が形式 (= cat_v9 パラメータ列挙) に留まり、定量的 verify (= 暫定試算) ゼロという構造的問題。

---

### Q1 Triple Barrier K 別 multiplier: **業界整合 / 改善余地 3 件**

業界整合あり (ATR multiplier 業界 standard ≈ SL 1.5-2.0× / TP 3+× + リスクリワード比 2:1 維持・本監査 WebSearch [Mudrex / BingX / Springer Triple Barrier 2025] と整合)。**短期 K「SL > TP」設計と長期 K「TP > SL」設計の混在によるラベル分布不整合リスクは構造的に存在するが、56 ラベル並列学習で物理的に予測対象を分離している (= K=6 TP_prob と K=288 TP_prob は別ラベルで別モデル) ため、ラベル不均衡対策 (= class_weight) が K 別 multiplier 別に独立適用される構造で一定の対処あり**。

改善余地:
1. **ATR_pct × multiplier の price-agnostic 整合性 verify が形式的**: §6.2.3 価格非依存性違反修正 (= ATR_pct ベースに修正) は phase_compliance §-1 USD 絶対値 blacklist と整合・**L-179 同型予防経路あり**。ただし K=6/12 で「TP×1.5 / SL×2.0」と K=96/144/288 で「TP×3.0 / SL×1.5」の **間遷移点 K=24/48 の multiplier (TP×2.0/SL×2.0 / TP×2.5/SL×1.5) が「中間」と書かれているだけで線形補間 or データ駆動の経路が不明**。L-232 「雑な言い切り癖」と同型問題。
2. **暫定値の data-driven 再 calibrate 経路が「atr_14_pct の 25th/75th percentile」とだけ書かれている**: §6.2.3 data-driven 経路宣言で「1 fold データから atr_14_pct の 25th/75th percentile で fold 別 calibrate」とあるが、**この percentile 値を multiplier_TP/SL のどう適用するかの数式が未定義** (= 例: TP multiplier = atr_pct_75th / atr_pct_50th = X 倍 の算式が無い)。実装時に CC が独自解釈で決定 → 設計逸脱リスク。
3. **K=6 (= 30 分) の cat_v9 整合根拠が薄い**: §6.2.3 cat-bitget 固有 verify で「cat_v9 スキャル系 (= P1, P3, P21, P25)」と書いているが、**cat_v9 P1/P3/P21/P25 の TP_PCT/SL_PCT が「30 分ホライズン」前提か「1-2 時間ホライズン」前提か未確認**。priority_v9_trade_logic_analysis.md (= Layer 1 必読) で時間特性 verify せずに「短期 K = cat_v9 流」と類推している。

数値根拠ある断言: ATR multiplier 業界 standard = SL 1.5-2.0× / TP 3+× は本監査 WebSearch [Mudrex / BingX] で実証あり (Bitget Wiki 「TP = ATR × 3 以上」)。短期 K 「SL > TP」と長期 K 「TP > SL」混在のラベル分布不整合リスクは class_weight='balanced' で部分対処されるが、K 別の class 分布偏差 verify は Stage 1 で必須。

### Q2 案 A 統合 (regime 6 列入力): **業界整合 / 改善余地 2 件**

業界整合あり (regime-aware 単一モデル + regime 情報入力 = 業界実証あり [MDPI Electronics Regime-Aware LightGBM Walk-Forward 2025] / [Harbourfront Technologies 2026] / [arxiv 2509.09751])。**「regime feature substantially helps crypto-correlated stocks (MSTR: +1257%) but hurts others (AMD: −948%)」**という資産依存性が業界実証で示されており、cat-bitget は BTCUSDT 単独 (= crypto-correlated 強) のため案 A 統合は妥当方向。

改善余地:
1. **「accuracy 差 > 30% で案 B 再検討」の閾値 30% の cat-bitget 固有根拠ゼロ**: §6.2.4 論点 1 第二段階出口判定「regime 間 accuracy 差 > 30% なら案 B」の **30% は arxiv 2509.09751 等の業界実証から導出していない**・本セッション暫定値。「accuracy 差 30%」は「regime 別 model 分離で 4 倍化計算コストを払う価値があるか」の判定基準だが、cat-bitget v15 HMM 既実装で regime 間 accuracy 差を pre check していない (= CP1 監査 Q1 と同型問題)。
2. **データ量 1/4 過学習リスクの定量試算なし**: §6.2.4 採用根拠 2「regime 別に分けると 1 regime あたりデータ量 1/4 = 過学習しやすい」と書いているが、**5y × 5m × 24h × 12 = 525,600 bar ÷ 4 regime = 131,400 bar/regime** の試算が無い。LightGBM 1,462 指標を 131,400 bar で学習する場合の overfit 危険度 (= サンプル/特徴量比 = 90:1 で一般的に十分) を verify していない。

数値根拠ある断言: 案 A 統合は arxiv 2509.09751 / MDPI Electronics 2025 / Harbourfront 2026 で実証あり。BTC trend-driven structure (= [PMC BTC ML] / [arxiv 2407.18334v1]) で ML が regime context を取り込みやすく、案 A 統合の方向性は業界整合。閾値 30% は data-driven 試算なしで「データ不足 (理由: cat-bitget v15 HMM 既実装 + Phase 0 v3.1 parquet で regime 別 accuracy pre check の暫定 verify が §6.2.4 内に欠落)」。

### Q3 Optuna 探索範囲 + L1/L2 正則化: **業界整合 / 改善余地 2 件**

業界整合あり (Optuna TPE + LightGBM ハイパラ業界 range = §13.1 / [Forecastegy] / [Towards Data Science] と整合・L1/L2 正則化追加 = [GeeksforGeeks LightGBM Regularization] / [DataScienceBase] と整合)。

改善余地:
1. **30 trials 収束十分性の cat-bitget 固有 verify ゼロ**: 本監査 WebSearch [Forecastegy]「In practice, about 30 trials are enough to find a pretty good set of hyperparameters」 + [Medium Bayesian Sorcery] で 30-100 trials が一般範囲。Optuna 公式 [hub.optuna.org] で「convergence efficiency depends on the specific problem complexity rather than prescriptive trial counts」と明示・**56 モデル × 3 系統 × Walk-Forward 5 fold の cat-bitget 固有複雑度に対する 30 trials 十分性は data-driven 試算なし**。「pretty good」 vs 「optimal」の差が cat-bitget 月 $1,900 達成判定に影響するかの verify ゼロ。第二段階 50 trials 拡張経路あり (data-driven 経路宣言) は適切だが、第一段階 30 trials を「業界主流」とする断言は L-232 同型問題。
2. **3 系統別 tune トレードオフの定量試算なし**: §6.2.6 論点 3 で「56 モデル個別 tune = 56 倍 (実用厳しい) / 共通 tune = 精度落ち / 3 系統別 tune = 3 倍で系統別最適化」と表で書いているが、**「精度落ち」「実用厳しい」が定量的にどの程度か (= 例: 5% NET 落ち / 10% NET 落ち) の試算なし**。3 系統別 tune が 56 モデル中の系統内ハイパラ多様性 (= LONG_MFE_K=6 と LONG_MFE_K=288 で num_leaves が同じで OK か) を吸収できるかの定量根拠ゼロ。

数値根拠ある断言: LightGBM L1/L2 正則化 (reg_alpha / reg_lambda) は本監査 WebSearch [GeeksforGeeks] で「L1 helps in feature selection / L2 prevents overfitting by shrinking feature weights」と業界 standard・**2,610 列 over-fitting 抑制効果は理論的に有効** ([builtin.com] LightGBM EFB + regularization)。Optuna 30 trials 業界 range 整合は [Forecastegy] + [Medium] で「pretty good」レベルとして実証あり。

### Q4 ルール集約 + 短期 K 重視: **業界整合 / 改善余地 3 件**

業界整合あり (rule-based ensemble aggregation = [arxiv 2501.10709] / [emergentmind Stacked Ensemble] と整合・「stacking explicitly learns how to compose the outputs of heterogeneous base learners via a trainable meta-learner」と本監査 WebSearch で第二段階 meta-learner 採用も整合)。

改善余地:
1. **重み 0.4/0.3/0.3 の業界実証は依頼書記載「NN 0.4 + LSTM 0.3 + GRU 0.3」と直接対応する文献なし**: 依頼書 Q4 verify 事項に「NN 0.4 + LSTM 0.3 + GRU 0.3」と書かれているが、本監査 WebSearch [arxiv 2501.10709] (= RL ensembles 中心) + [emergentmind] では具体的な重み 0.4/0.3/0.3 の業界 standard 引用なし。**§6.2.7 論点 1 が cat-bitget の TP_prob (0-1) / MFE_pct (回帰値) / meta_yes_prob (0-1) を 0.4/0.3/0.3 で線形結合する根拠が業界出典なし**。data-driven 経路宣言で「Stage 3 純増分 < 1.5× で再 calibrate」あるが、第一段階固定 0.4/0.3/0.3 の事前根拠は L-232 同型問題。
2. **短期 K 重視 0.5/0.1 で長期 K 圧縮リスク (= 観点 ③ #3 と同型)**: 5/7 のホライズン情報を 0.1 (= 14%) に圧縮することは Phase 1 v6 教訓「予測対象を物理的に増やす」と論理整合しない。Stage 1 で K 別 feature_importance verify + 第二段階 0.3/0.2 へ再 calibrate 経路あり (data-driven 経路宣言) はあるが、第一段階固定 0.5/0.1 が「月 275 件確保ライン」のためという根拠で長期 K 14% に圧縮するのは設計矛盾。
3. **ルール集約 precision 0.85 の cat-bitget 5m / BTC 取引での成立検証なし**: §6.2.7 採用根拠 1「業界実証 rule-based precision 0.85 ([arxiv 2501.10709])」が arxiv 2501.10709 (= RL ensembles 中心研究) で「rule-based precision 0.85」と直接書かれているか本監査 WebSearch で再確認不可。LightGBM 56 ラベル並列 + ルール集約での precision 0.85 の業界実証ゼロ → cat-bitget 過去事例 verify (= cat_v9 P1-P25 平均 TP precision) ゼロ。

数値根拠ある断言: ルール集約 vs meta-learner stacking の業界実証は本監査 WebSearch [emergentmind Stacked Ensemble] で「stacking explicitly learns how to compose outputs / increasing predictive performance vs simple averaging」と meta-learner 優位が示されている。**第二段階 meta-learner 採用は業界整合**だが、**第一段階ルール集約 0.4/0.3/0.3 + 短期 K 0.5/0.1 の重み set は cat-bitget 固有設計で業界実証なし** (= データ不足: cat-bitget 5m 56 ラベル並列 + ルール集約 precision 0.85 の業界実証ゼロ・data-driven 第二段階再 calibrate に依存)。

### Q5 threshold 0.6 固定: **業界整合 / 改善余地 3 件**

業界整合あり (threshold-based ensemble = §13.1 / [arxiv 2501.10709] 「threshold 0.6 buy / 0.4 sell / 中間 hold」と整合・本監査 WebSearch [arxiv 2501.10709] は RL ensembles 中心研究)。

改善余地:
1. **月 275 件確保ラインとの整合 = 暫定試算ゼロ (依頼書 Q5 verify 事項明示)**: §6.2.7 論点 4 「entry_score > 暫定 0.6 で entry (= 業界実証値)」+ 「月 275 件確保ライン未達 (月 < 200 件) → threshold 0.6 → 0.5」と data-driven 経路宣言。**しかし「entry_score 分布が threshold 0.6 で月 275 件出るか」の暫定試算が §6.2 内に皆無**。Phase 0 v3.1 既存 parquet (= labels_mfe_mae_pct_*.parquet) + v15 HMM regime predictions で TP_prob / MFE_pct / meta_yes_prob の暫定値分布を試算できる素材があるのに pre check ゼロ → L-220 (= 暫定値・閾値の data-driven 経路宣言違反) 同型問題。
2. **第二段階動的 threshold (= regime / 時間帯 / cluster 別) の出口判定「Stage 3 regime 別 NET 偏り > 30%」の閾値妥当性根拠ゼロ**: §6.2.7 data-driven 経路宣言「第二段階動的 threshold 採用判定 = Stage 3 regime 別 NET 偏り > 30%」と書かれているが、**30% は arxiv / 業界文献からの引用なし**。CP1 監査 Q2 と同型問題 (= 30% の数値根拠ゼロ)。
3. **即死 reject (= 危険度 > 0.9) 定義の具体化必要 (依頼書 Q5 verify 事項明示)**: §6.2.7 論点 4「即死 reject (= 危険度 > 0.9・§1 既決着)」と書かれているが、**「危険度」自体の定義 + 算出式が §6.2.X 内に明示なし**。§1 [2] で「即死リスク (危険度>0.9) のみ reject」と書かれているが、危険度 = ATR_pct × Position_size / capital? / SHORT_score? / volatility prediction? 等の解釈ぶれリスクあり (Major)。

数値根拠ある断言: threshold 0.6 業界実証は本監査 WebSearch [arxiv 2501.10709] で RL ensembles 中心研究に登場するが、**cat-bitget 5m bar BTC 取引 LightGBM 56 ラベル並列 + ルール集約 score での threshold 0.6 妥当性は業界実証ゼロ・データ不足 (理由: 月 275 件確保ラインとの整合の暫定試算が §6.2.X 内に皆無)**。即死 reject 危険度 > 0.9 の定義具体化は実装着手前に必須 (Major)。

### Q6 leak 防止経路: **業界整合 / 改善余地 2 件**

業界整合あり (Lopez de Prado AFML Ch.3 Look-Ahead Bias + Ch.7 Purged K-Fold + Embargo + [arxiv 2512.12924 Walk-Forward Validation Framework 2025] と整合・本監査 WebSearch [freqtrade Issue #12507] / [MDPI Adaptive Event-Driven Labeling 2025] / [arxiv 2601.13770 Look-ahead Bias Benchmark] で multi-timeframe causal alignment + merge_asof backward の業界 standard 整合)。

改善余地:
1. **56 モデル × feature_importance top 20 自動 monitoring の実装現実性 (Minor・観点 ④ #3 と同型)**: §6.2.8 項目 5 で 56 モデル × top 20 = 1,120 feature row を毎 fold で自動チェック → 計算コスト軽いが、**怪しい列名 (= fractal/pivot/resistance/support/future) の検出ロジック実装が「自動 monitoring」とだけ書かれて具体化されていない**。phase_compliance §1.4 で「fractal ベース列ブラックリスト 3 段階運用 (= top1-20 hit 時の物理 leak verify 4 項目セット)」が具体化されているが、§6.2.8 にその参照リンクなし。
2. **TSFresh 第二段階追加時の leak チェック経路具体性ゼロ (Minor)**: §6.2.4 論点 6 「TSFresh leak チェック必須 ([[feedback_ml_leak_mandatory_check]] 4 点 verify)」とだけ書き、**TSFresh 794 features 内の `shift(-N)` / future window 含む関数群 (= `cwt_coefficients` / `linear_trend` / `agg_linear_trend` 等は window 内集計で OK だが `*_pre_*` / `change_quantiles` 等は要確認) の具体的識別ロジック**が §6.2.8 内に欠落。L-179 (= fractal j+2 leak が Phase 1-7a 全 14 段階を素通り) の再発リスク (= 「leak チェック 4 点」では新規ライブラリの隠れ leak を物理的に止められない)。

数値根拠ある断言: L-179 / L-128 同型予防は §6.2.8 + phase_compliance §-1/§0/§1.4 既決着引継ぎで設計レベルで重複度高く整合。本監査 WebSearch [MDPI Adaptive Event-Driven Labeling 2025]「Studies that strictly prevent look-ahead bias in multi-timeframe data alignment show lower performance metrics than those aligning indicators using open timestamps, which inadvertently allows models to see future information. A subtle multi-timeframe look-ahead bias in higher-timeframe data alignment can inflate performance by approximately 0.20 ROC-AUC points」 = MTF causal alignment 違反で +0.20 ROC-AUC 過大評価が実証あり・**§6.2.8 + §6.1.6 merge_asof backward の設計は CP1 監査 M3 反映済で適切**。

### Q7 Phase 1 v6 教訓反映 (4 件): **業界整合 / 改善余地 3 件**

4 件の構造解消 verify:
1. **regime 不在 → §6.1.6 regime 6 列 + §6.2.4 案 A 統合**: 構造解消 OK (= regime 6 列を入力に追加・LightGBM tree depth で「regime × signal」自動学習)。
2. **LONG-SHORT 並列学習 → §6.2.3 論点 2 ラベル定義レベルで分離**: 構造解消 OK (= 56 ラベル中 LONG 28 + SHORT 28 で物理的に分離・dual-task architecture と整合 [arxiv 2508.14656])。
3. **MTF 欠落 → §6.2.4 論点 3 MTF 8 TF integrated**: 構造解消 OK (= 既存 Phase 0 v3.1 で 8 TF 計算済・[Preprints 202603.0994] と整合)。
4. **ボラ予測逃げ → §6.2.3 §6.0.2 56 ラベル並列 (= 揺れ幅 28 + 決着 28)**: 構造解消 **部分的**。物理的に予測対象を 14 → 56 に増やしたが、**§6.2.7 論点 1 集約段階で「短期 K 0.5 / 長期 K 0.1」「TP_prob 0.4 + MFE_pct 0.3 + meta_yes_prob 0.3」の重み付けで MFE_pct = 揺れ幅予測の重み 0.3 を割り当て**ている。**新規発生リスク = 「決着系 28 ラベル (Triple Barrier 14 + meta 14) の予測逃げ」リスク** (= 観点 ③ #3 と同型)。56 ラベル並列学習で AI が「決着系の予測寄与が大きいため決着系で逃げる」可能性 → Stage 1 で 56 ラベル間予測相関 verify + ラベル系統別 RMSE/F1/AUC 比較で検出経路あり (= §6.2.1 Stage 1 整合) だが、**事前 verify 経路ゼロ**。

改善余地:
1. **短期 K 重視 0.5/0.1 で長期 K 圧縮 = ボラ予測逃げ構造解消の論点矛盾 (Major・観点 ③ #3 + Q4 #2 と同型)**: 56 ラベル並列学習で物理的に増やしたのに、出力集約で 5/7 のホライズン情報を圧縮するのは Phase 1 v6 教訓「予測対象を物理的に増やす」と論理整合しない。
2. **「決着系の予測逃げ」新規発生リスクの事前 verify 経路ゼロ (Major)**: 56 ラベル並列でも、ラベル系統別 (= 揺れ幅 28 / 決着 28) の予測寄与差が極端な場合 (= 例: 揺れ幅系 RMSE 良好 / 決着系 logloss 悪化) に AI が「決着系で逃げる」リスク。Stage 1 統計指標で系統別評価あり (= §6.2.1) だが、事前リスク試算ゼロ。
3. **regime 6 列の「decision tree で自動学習される」根拠の十分性**: §6.2.4 採用根拠 3「LightGBM の自動学習力: tree (= if-then ルール) の深さで「regime × signal」の組合せパターンを自動発見可能 (= まこさん例「UPtrend + MACD GC + RSI ≥ 50 → TP 高」は案 A の決定木分岐で学習される)」と書いているが、**cat-bitget v15 HMM 既実装 + Phase 0 v3.1 1,462 指標 + Phase 1 v6 LightGBM 学習結果で「regime 6 列が feature_importance top N に入るか」の pre check ゼロ**。CP1 監査 Q1 と同型問題 (= 業界整合性 verify 済を判断根拠化する逆効果)。

数値根拠ある断言: 4 件の Phase 1 v6 失敗主因のうち 3 件 (= regime 不在 / LONG-SHORT 並列 / MTF 欠落) は構造解消 OK。1 件 (= ボラ予測逃げ) は **部分的構造解消 + 新規リスク発生** (= 短期 K 重視で長期 K 圧縮 / 決着系の予測逃げリスク)。Stage 1 統計指標で検出経路ありで対処可能だが、事前 verify 経路ゼロ → 実装着手前に Phase 0 v3.1 既存 parquet + v15 HMM 既実装で pre check 必須。

---

## 外部検索結果サマリー

実施したクエリ 8 件 (= 依頼書要請 6 件 + 補強 2 件) と主要発見:

### 検索 1: Triple Barrier ATR multiplier horizon K specific crypto Bitcoin 2025
- **主要発見**: ATR multiplier 業界 standard = SL 1.5-2.0× / TP 3+× + リスクリワード比 2:1 維持。「TP = ATR × 3 以上」がリスクリワード優位 ([Mudrex] / [BingX])。Springer Triple Barrier 2025 で crypto BTC/ETH 適用・「target variable determined on the basis of varying interval lengths, contingent on market volatility」と動的閾値設計確立。
- 出典: [Springer Financial Innovation 2025](https://link.springer.com/article/10.1186/s40854-025-00866-w) / [Mudrex ATR](https://mudrex.com/learn/average-true-range-crypto/) / [BingX Academy](https://bingx.com/en/learn/article/what-is-average-true-range-atr-volatility-indicator-in-crypto-trading)

### 検索 2: Regime-aware single model vs separate models LightGBM crypto Bitcoin 2025
- **主要発見**: 「Regime-aware LightGBM framework conditioned on market regimes detected via a rolling Hidden Markov Model eliminates look-ahead bias」「regime information as features rather than using separate models per regime」が業界主流。資産依存性 = 「regime feature substantially helps crypto-correlated stocks (MSTR: +1257%) but hurts others (AMD: −948%)」。BTC trend-driven structure では regime-aware 単一モデル + regime 入力が業界整合。
- 出典: [MDPI Electronics Regime-Aware LightGBM Walk-Forward 2025](https://www.mdpi.com/2079-9292/15/6/1334) / [Harbourfront Technologies 2026](https://harbourfronttechnologies.wordpress.com/2026/04/29/regime-aware-trading-strategies-with-machine-learning/) / [Preprints BTC HMM 2024-2026](https://www.preprints.org/manuscript/202603.0831) / [Quantinsti HMM + Random Forest Specialist](https://blog.quantinsti.com/regime-adaptive-trading-python/) / [arxiv 2508.11338 RegimeNAS](https://arxiv.org/pdf/2508.11338)

### 検索 3: Optuna LightGBM hyperparameter trials sufficiency 30/50/100 trading 2025
- **主要発見**: 「In practice, about 30 trials are enough to find a pretty good set of hyperparameters for LightGBM using Optuna」「the biggest gains usually come from the first set of trials, and you shouldn't endlessly run thousands of trials for a minuscule improvement」 = 30 trials が「pretty good」レベル業界相場。**「optimal」レベルや trading specific guidance はなし**。
- 出典: [Forecastegy Optuna LightGBM](https://forecastegy.com/posts/how-to-use-optuna-to-tune-lightgbm-hyperparameters/) / [Medium Bayesian Sorcery Optuna](https://medium.com/@becaye-balde/bayesian-sorcery-for-hyperparameter-optimization-using-optuna-1ee4517e89a) / [optuna.org](https://optuna.org/)

### 検索 4: Multi-output ensemble aggregation rule-based vs meta-learner 2025
- **主要発見**: 「Stacking explicitly learns how to compose the outputs of heterogeneous base learners via a trainable meta-learner, increasing predictive performance and reducing generalization error relative to individual models or simple averaging」 = meta-learner stacking が単純集約より優位。「ORSA」「MWRP」等の computational geometry-based meta-models も interpretable / parameterless で業界実装あり。Crypto trading で「ensemble approaches show higher win rates and lower loss rates than individual agents」。
- 出典: [emergentmind Stacked Ensemble](https://www.emergentmind.com/topics/stacking-ensemble-architecture) / [arxiv 2501.10709 Ensemble Methods FinRL 2025](https://arxiv.org/html/2501.10709v1) / [arxiv 2509.09751 Meta-Learning RL Crypto](https://arxiv.org/pdf/2509.09751) / [MDPI Stock Stacked Heterogeneous Ensemble](https://www.mdpi.com/2227-7072/13/4/201)

### 検索 5: Look-ahead bias prevention crypto MTF causal alignment merge_asof 2025
- **主要発見**: 「When using merge_asof(direction="backward") with unclosed higher timeframe candles, the method can use the close of an unclosed candle to calculate metrics, causing trading decisions to rely on unfinalized price data, which introduces lookahead bias」 = merge_asof backward でも unclosed candle 起因の leak リスクあり。「subtle multi-timeframe look-ahead bias in higher-timeframe data alignment can inflate performance by approximately 0.20 ROC-AUC points」 = MTF causal violation で +0.20 ROC-AUC 過大評価が定量実証。
- 出典: [freqtrade Issue #12507 Lookahead merge_asof](https://github.com/freqtrade/freqtrade/issues/12507) / [MDPI Adaptive Event-Driven Labeling 2025](https://www.mdpi.com/2076-3417/15/24/13204) / [doi.org/10.3390/forecast8030040 MTF Bitcoin Price-Level-Agnostic 2025](https://doi.org/10.3390/forecast8030040) / [arxiv 2601.13770 Look-ahead Bias Benchmark](https://arxiv.org/pdf/2601.13770)

### 検索 6: LightGBM L1 L2 regularization high-dimensional 2000+ features over-fitting 2025
- **主要発見**: 「L1 (reg_alpha) helps in feature selection as it can drive some feature weights to zero / L2 (reg_lambda) prevents overfitting by shrinking the feature weights towards zero」 = LightGBM L1/L2 業界 standard。「LightGBM uses Exclusive Feature Bundling (EFB), a technique to reduce the number of features when dealing with high-dimensional data」 = 高次元特徴量 robust。**2000+ 特徴量 + crypto trading 固有の 2025 実証は本検索でゼロ**。
- 出典: [GeeksforGeeks LightGBM Regularization](https://www.geeksforgeeks.org/machine-learning/lightgbm-regularization-parameters/) / [builtin.com LightGBM Guide](https://builtin.com/articles/lightgbm) / [DataScienceBase LightGBM Theory](https://www.datasciencebase.com/supervised-ml/algorithms/gradient-boosting/LightGBM/theory/)

### 検索 7 (補強): LightGBM class_weight balanced multiclass probability calibration 2025
- **主要発見**: 「class_weight should only be used for multi-class classification tasks. For binary classification tasks, you may use is_unbalance or scale_pos_weight」「Using these class weighting parameters will result in poor estimates of individual class probabilities, and you may want to consider performing probability calibration of your model」 = class_weight='balanced' / scale_pos_weight 適用後に確率推定悪化 → post-hoc キャリブレーション (= isotonic regression / Platt scaling) 推奨が業界 standard。
- 出典: [LightGBM 4.6 LGBMClassifier docs](https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMClassifier.html) / [arxiv 2510.25458 Scalable Utility-Aware Multiclass Calibration](https://arxiv.org/pdf/2510.25458)

### 検索 8 (補強): Optuna Bayesian TPE convergence trials sufficiency financial ML
- **主要発見**: 「Optuna's TPE+CMA-ES sampler was statistically as good as or better than RandomSearch, Hyperopt TPE, SMAC3, and GPyOpt」「convergence efficiency depends on the specific problem complexity rather than prescriptive trial counts」 = trials 数の最適値は問題依存・cat-bitget 固有の 30 trials 十分性は data-driven 試算が必須。
- 出典: [Optuna Hub Bayesian Optimization](https://hub.optuna.org/tags/bayesian-optimization/) / [Medium Bayesian Sorcery](https://medium.com/@becaye-balde/bayesian-sorcery-for-hyperparameter-optimization-using-optuna-1ee4517e89a)

---

## 総合判定

### Verdict: **PIVOT** (= 一部修正で実装着手可)

### 根拠

**1. 業界整合性は概ね確保されている**: 8 検索すべてで「LightGBM MultiOutputRegressor 56 個独立並列・Triple Barrier ATR multiplier・regime-aware 単一モデル + regime 入力・Walk-Forward Purged K-Fold + Embargo・Optuna TPE + L1/L2 正則化・rule-based ensemble + meta-learner stacking・merge_asof backward causal alignment・class_weight='balanced'」のいずれかに対応する業界実証あり。設計の骨格は AFML Ch.3/6/7 + 業界 WebSearch + cc_entry_logic_self_study §13/§14 と整合。

**2. ただし「業界 standard 採用」を判断根拠化する CP1 監査同型問題が §6.2 全体に貫通**: 観点 ③ 認知バイアス FAIL (Major) + 観点 ⑦ 主エージェントバイアス FAIL (Critical) = CP1 監査の同型バイアス対策 (= cc_role §1.4.6.1 改善 6-12) を機械的フォーマット化することで網羅性を担保した外形・本質的に効いていない。これは CP1 監査が指摘した「cat-bitget 過去事例 verify ゼロ」「業界 standard を採用した各設計判断について、cat-bitget 固有 lift の 1 行 verify が形式に留まっている」が §6.2 設計でも完全同型再演している。

**3. 実装着手前に修正必須の Critical / Major 欠陥が 4 件**:
   - C1: class_weight='balanced' + scale_pos_weight の確率推定悪化に対するキャリブレーション設計欠落 (= 観点 ① #1・CP1 監査 C1 と同型問題)
   - C2: §6.2.7 集約式 `TP_prob × 0.4 + MFE_pct × 0.3 + meta_yes_prob × 0.3` の scale 不整合 (= 観点 ① #3・MFE_pct と確率値の scale 異質を線形加算)
   - M1: 短期 K 重視 0.5/0.1 で長期 K 圧縮 = Phase 1 v6 教訓「ボラ予測逃げ」構造解消の論点矛盾 (= 観点 ③ #3 / Q4 #2 / Q7 #1)
   - M2: 即死 reject 「危険度 > 0.9」の定義 + 算出式 欠落 (= 観点 ② #2 / Q5 #3)

**4. 月次 NET ≥ $1,900 達成可能性判定は本監査スコープ外** (= 依頼書 §大目的 / §守則 明記)・本判定は **詳細設計の業界整合性 + cat-bitget 制約整合性 + Phase 1 v6 教訓反映 + leak 防止 + 内部一貫性** の verify のみ。

**5. NO-GO (= 重大欠陥・再設計必要) ではない理由**: 設計骨格 (= 8 サブセクション + 段階的アプローチ + data-driven 経路宣言 + 第二段階出口設計) は妥当・実装着手前の修正 4-7 件で GO 可能。Critical 2 件は CP1 監査 Critical 同型問題のため対策手法は既知 (= isotonic regression + Gaussian kernel + standardization)。

**6. GO (= 修正なし実装着手可) ではない理由**: Critical C1 (class_weight キャリブレーション欠陥) を実装後に発見すると、§6.2.7 集約式 → [3] Sizing Half-Kelly 接続まで再設計が必要。実装着手前に修正する方が労力ずっと少ない。

---

## 改善方向性 (= 具体提案 6 件・優先度明示)

### Critical-1: class_weight + scale_pos_weight の確率推定悪化に対するキャリブレーション設計を §6.2.7 集約式直前に追加
- 修正対象: §6.2.3 論点 4 (= class_weight='balanced' / scale_pos_weight) + §6.2.7 論点 1 集約式
- 修正内容:
  - LightGBM 56 個全モデルの `predict_proba` 出力に対し、**fold 別 isotonic regression** で post-hoc キャリブレーションを実装 (= 本監査 WebSearch [LightGBM docs] / [arxiv 2510.25458 Multiclass Calibration])
  - Stage 1 評価に **Brier score + reliability diagram + ECE** を追加 (= CP1 監査 Critical-1 と同型対策・[scikit-learn Probability Calibration])
  - 集約式 `LONG_score = LONG_TP_prob × 0.4 + LONG_MFE_pct × 0.3 + LONG_meta_yes_prob × 0.3` の入力 TP_prob / meta_yes_prob は **キャリブレーション後の値**を使う
- 出典: [LightGBM 4.6 docs](https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMClassifier.html) / [arxiv 2510.25458](https://arxiv.org/pdf/2510.25458)

### Critical-2: §6.2.7 集約式の scale 不整合 (= MFE_pct と確率値の scale 異質) 修正
- 修正対象: §6.2.7 論点 1 集約式
- 修正内容: MFE_pct を **z-score 標準化 or min-max scaling (= train_2021_2024 fold 別)** してから集約式に投入。具体的には `LONG_MFE_pct_normalized = (LONG_MFE_pct - LONG_MFE_pct_train_mean) / LONG_MFE_pct_train_std` (= z-score) または `(LONG_MFE_pct - 0) / LONG_MFE_pct_train_p95` (= 0-1 ratio 化)
- 閾値の決め方: 第一段階 z-score・第二段階 (= Stage 1 結果次第) で 0-1 ratio 化に切り替え検討

### Major-1: 短期 K 重視 0.5/0.1 を「Phase 1 v6 教訓反映の論点矛盾」として再設計
- 修正対象: §6.2.7 論点 1 K 重み付け
- 修正内容: 第一段階で **K 別重みも等重み (= 全 7 ホライズン 1/7 ≈ 0.143)** から出発し、Stage 1 fold 別 K 別 feature_importance + 系統別 RMSE/F1/AUC で **data-driven 調整** に変更。月 275 件確保ライン制約は threshold 0.6 + fold 別 calibrate (= 月 < 200 件で 0.5 / 月 > 400 件で 0.7) で達成し、K 重み制約は系統的に decouple。これで Phase 1 v6 教訓「予測対象を物理的に増やす」と集約段階の重み付けが論理整合する
- 出典: §6.2.3 §6.0.2 56 ラベル並列学習 + §6.2.1 Stage 1 系統別評価経路

### Major-2: 即死 reject 「危険度 > 0.9」の定義 + 算出式を §6.2.7 論点 4 に明示
- 修正対象: §6.2.7 論点 4 「即死 reject (= 危険度 > 0.9)」
- 修正内容: 危険度 = N の算出式を明示。候補:
  - (a) `危険度 = SHORT_score / (LONG_score + SHORT_score)` (= 反対方向確信度が高い場合 reject)
  - (b) `危険度 = ATR_pct × LONG_score / max_ATR_pct_train_2021_2024_p95` (= 高ボラ + 低確信時 reject)
  - (c) `危険度 = LONG_SL_prob (Triple Barrier 3 class の SL hit probability)` (= 損切確率高い時 reject)
- 第一段階 (c) `LONG_SL_prob > 0.9` を採用 (= Triple Barrier 3 class の直接出力で算出簡単・解釈性高)・第二段階 (a) (b) 検討
- 出典: §6.2.3 Triple Barrier 3 class 出力 (= LONG_SL_prob / LONG_TP_prob / LONG_TIME_prob)

### Minor-1: 56 モデル × feature_importance top 20 自動 monitoring の具体化を §6.2.8 項目 5 に追加
- 修正対象: §6.2.8 項目 5
- 修正内容: phase_compliance §1.4「fractal ベース列ブラックリスト 3 段階運用 (= top1-20 hit 時の物理 leak verify 4 項目セット)」を §6.2.8 項目 5 に参照リンク追加 + cat-bitget 固有 verify として「56 モデル全部に 3 段階運用を適用」明示
- 実装例: `verify_top20_features_leak.py` の (i) lag-1 shift 不変性・(ii) 末尾 K bars NaN pattern・(iii) 二重 N サフィックス内外一致・(iv) importance gain single<50% の 4 項目を 56 モデル × 各 fold で自動実行

### Minor-2: TSFresh 第二段階追加時の leak チェック経路具体化を §6.2.4 論点 6 / §6.2.8 に追加
- 修正対象: §6.2.4 論点 6 + §6.2.8 第一原則
- 修正内容: TSFresh 794 features の中で window 内集計のみ使う関数群 (= 例: `cwt_coefficients` / `linear_trend` / `agg_linear_trend` / `mean` / `std` / `quantile`) と将来情報を含み得る関数群 (= 例: `change_quantiles` / `partial_autocorrelation` 等は要 verify) を分類し、leak リスク高関数群を事前 blacklist 化。TSFresh `extract_features` 呼び出し時に `fc_parameters` で許可関数を whitelist 指定する設計

---

## CC プロセス欠陥対策 (= cc_role §1.4.6 改訂提案)

### 該当発見: CP1 監査の同型バイアス対策 (= cc_role §1.4.6.1 改善 6-12) が **機械的フォーマット化されただけで本質的に効いていない** 構造的問題

CP1 監査で cc_role §1.4.6.1 に「Anti-業界フレーム逃避ゲート」を追加 (= 改善 10 cat-bitget 固有 verify / 改善 11 予測誤差相関 verify / 改善 12 暫定値 data-driven 経路宣言) したが、§6.2 設計では:
- §6.2.1〜§6.2.8 全 8 サブセクションに「業界 standard verify / 教科書整合 / 業界 standard との差分 / cat-bitget 固有 verify / 統計指標と PnL 指標の分離 / 設計判断根拠 N 件 / 懸念 N 件 + 反論 / data-driven 経路宣言」の 8 ブロック構造が**機械的に並列配置**されている
- 「cat-bitget 固有 verify」セクションの内容が **cat_v9 パラメータ列挙** (= P1, P3, P21, P25 = TP 0.5-1.2% / SL 1.5-2%) で止まり、**定量的 verify (= 暫定試算 / 過去 1 fold データでの pre check)** ゼロ
- 「data-driven 経路宣言」セクションの内容が「Stage 1 で fold 別 percentile で決定」とだけ書かれ、**第一段階固定値の事前根拠**は業界引用のみ

### 提案: cc_role §1.4.6.1 に「§ 1.4.6.1.A 機械的フォーマット化検出ガード」を追加

現行 §1.4.6.1 (= 業界整合 verify 9 項目 + Anti-業界フレーム逃避 3 項目 = 計 12 項目) に、以下の **メタガード 3 項目**を追加:

13. **機械的フォーマット化検出**: 設計提案の各サブセクションで「業界 standard verify / 教科書整合 / cat-bitget 固有 verify / data-driven 経路宣言」等のブロックが機械的に並列配置されている場合、**「cat-bitget 固有 verify」セクション内に「定量試算 (= 過去 1 fold データ / Phase 0 v3.1 既存 parquet / v15 HMM 既実装での pre check) を 1 件以上含む」**ことを必須化。含まない場合は「形式的 verify (= 機械的フォーマット化)」として L-220 違反扱い
14. **第一段階固定値の事前根拠厳格化**: 暫定値 (= 例: threshold 0.6 / 重み 0.4/0.3/0.3 / K 重み 0.5/0.1 / accuracy 差 30% / 純増分 1.3× / 1.5× / 2.0×) を第一段階に固定する場合、**「業界引用 + cat-bitget 過去事例 1 件以上」**を併記必須。業界引用のみは「業界 standard を判断根拠化する逆効果」(= CP1 監査 観点 (7)) として L-232 違反扱い
15. **設計矛盾自己検出**: 同じ設計文書内で「Phase 1 v6 教訓 X を構造的に解消する」と書いた論点と、別論点で「教訓 X の解消に逆行する設計判断 (= 例: 短期 K 重視 0.5/0.1 で長期 K 圧縮 → 揺れ幅予測逃げ構造解消の論点矛盾)」を併記している場合、**自己 verify Q&A セクションを必須化**。Q&A は「教訓 X の解消経路と論点 Y の整合性を 1 行で説明」「整合しない場合は論点 Y を再設計 or 教訓 X 解消の評価軸を Stage 1 で具体化」

### 提案: 本監査結果反映時の「機械的反映禁止」(= cc_role §1.5.5 厳格化整合)

CP1 監査結果反映時に CC が「監査結果 7 件 100% 反映 = 機械的反映」と称してスキップせず、本セッションで設計判断含む反映を実施した経緯 (= L-213 / L-214 再演防止) は確認できた (= v2.8 で全 7 件採用支持)。しかし本監査 §6.2 設計が CP1 監査同型問題を再演している事実は、cc_role §1.5.5 「機械的反映表現の使用条件厳格化」が **「過去監査結果の反映」には適用されたが「新規詳細設計提案」には適用されていない**ことを示す。

新規詳細設計提案にも cc_role §1.5.5 を拡張し、「業界 standard を採用する各設計判断の cat-bitget 固有 verify は機械的反映ではなく設計判断を含む反映」として CC 独立評価プロセス (= 1 件ずつ採用支持/要再評価/拒否 + 根拠提示) を必須化する。

### 提案: 本監査結果を L-233 として lessons_active.md に記録

本監査で発見した「CP1 監査同型問題の §6.2 設計再演」は、L-232 (= 雑な言い切り癖) + L-220 (= 暫定値・閾値の data-driven 経路宣言違反) + L-230 (= 業界フレーム逃避癖) の **複合事案**として L-233 を新規立てる必要。cc_role §1.4.6.1 改訂 (= 上記 13/14/15 メタガード追加) と紐付ける。

---

## Sources (= 本監査で参照した外部 URL)

- [Springer Financial Innovation Triple Barrier 2025](https://link.springer.com/article/10.1186/s40854-025-00866-w)
- [Mudrex ATR Crypto](https://mudrex.com/learn/average-true-range-crypto/)
- [BingX Academy ATR](https://bingx.com/en/learn/article/what-is-average-true-range-atr-volatility-indicator-in-crypto-trading)
- [MDPI Electronics Regime-Aware LightGBM Walk-Forward 2025](https://www.mdpi.com/2079-9292/15/6/1334)
- [Harbourfront Technologies Regime-Aware Trading ML 2026](https://harbourfronttechnologies.wordpress.com/2026/04/29/regime-aware-trading-strategies-with-machine-learning/)
- [Preprints BTC HMM 2024-2026](https://www.preprints.org/manuscript/202603.0831)
- [arxiv 2508.11338 RegimeNAS](https://arxiv.org/pdf/2508.11338)
- [Quantinsti HMM + Random Forest Specialist](https://blog.quantinsti.com/regime-adaptive-trading-python/)
- [Forecastegy Optuna LightGBM](https://forecastegy.com/posts/how-to-use-optuna-to-tune-lightgbm-hyperparameters/)
- [Medium Bayesian Sorcery Optuna](https://medium.com/@becaye-balde/bayesian-sorcery-for-hyperparameter-optimization-using-optuna-1ee4517e89a)
- [Optuna Hub Bayesian Optimization](https://hub.optuna.org/tags/bayesian-optimization/)
- [emergentmind Stacked Ensemble Architecture](https://www.emergentmind.com/topics/stacking-ensemble-architecture)
- [arxiv 2501.10709 Ensemble Methods FinRL 2025](https://arxiv.org/html/2501.10709v1)
- [arxiv 2509.09751 Meta-Learning RL Crypto](https://arxiv.org/pdf/2509.09751)
- [MDPI Stock Stacked Heterogeneous Ensemble](https://www.mdpi.com/2227-7072/13/4/201)
- [freqtrade Issue #12507 Lookahead merge_asof](https://github.com/freqtrade/freqtrade/issues/12507)
- [MDPI Adaptive Event-Driven Labeling Multi-Scale Causal 2025](https://www.mdpi.com/2076-3417/15/24/13204)
- [doi.org/10.3390/forecast8030040 MTF Bitcoin Price-Level-Agnostic 2025](https://doi.org/10.3390/forecast8030040)
- [arxiv 2601.13770 Look-ahead Bias Benchmark](https://arxiv.org/pdf/2601.13770)
- [GeeksforGeeks LightGBM Regularization](https://www.geeksforgeeks.org/machine-learning/lightgbm-regularization-parameters/)
- [builtin.com LightGBM Guide](https://builtin.com/articles/lightgbm)
- [DataScienceBase LightGBM Theory](https://www.datasciencebase.com/supervised-ml/algorithms/gradient-boosting/LightGBM/theory/)
- [LightGBM 4.6 LGBMClassifier docs](https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMClassifier.html)
- [arxiv 2510.25458 Scalable Utility-Aware Multiclass Calibration](https://arxiv.org/pdf/2510.25458)

---

監査結果ファイル終わり。
