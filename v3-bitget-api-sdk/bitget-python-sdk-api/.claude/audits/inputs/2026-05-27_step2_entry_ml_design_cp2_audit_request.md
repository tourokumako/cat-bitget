# 【監査依頼】工程 [2] Entry ML 詳細設計 §6.2.1〜§6.2.8 全 8 サブセクション (CP2 監査)

---

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 8 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (= 同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (= 機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-Q7 + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて結果ファイル `.claude/audits/2026-05-27_step2_entry_ml_design_cp2_audit_report.md` を Write
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (= GO / NO-GO / PIVOT / OTHER)
   - 最優先指摘 (= Critical) 件数

### 禁止

- 依頼書起案者 (= メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (= 本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)

---

## 監査依頼メタ情報

- 依頼日: 2026-05-27
- 依頼者: CC (= 起案者・メインセッション)
- 監査区分: **CP2 (= 工程 [2] Entry ML 詳細設計 監査)**
- 監査対象タスク: ml_pipeline_baseline_v1.md §6.2.1〜§6.2.8 全 8 サブセクション (= 本セッション完成)
- 結果ファイル保存先: `.claude/audits/2026-05-27_step2_entry_ml_design_cp2_audit_report.md`
- 入力ファイル保存先 (= 本依頼書): `.claude/audits/inputs/2026-05-27_step2_entry_ml_design_cp2_audit_request.md`

---

## 監査依頼の経緯

1. 2026-05-27 本セッションで工程 [2] Entry ML 詳細設計 §6.2.1〜§6.2.8 全 8 サブセクション完成 (= ml_pipeline_baseline v3.0 → v3.6)
2. regime ensemble §6.1.1〜§6.1.6 と同型構造で完成・CP1 監査経路 (= 2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md) と同型の独立監査経路で同型バイアス回避必要
3. 次工程 = §6.2.X 完成 + CP2 監査結果反映後に実装着手 → 8 工程通し Stage 3 で「旧 Priority v9 月 $370 vs ML パイプライン月次 NET」純増分 (b)/(a) ≥ 5.1× で目標達成判定
4. Phase 1 v6 (= 過去 6 案全滅) の教訓 4 件 (= regime 不在 / LONG-SHORT 並列 / MTF 欠落 / ボラ予測逃げ) を §6.2.X 設計で構造的解消する経路にあるかの独立 verify が必須

---

## 着手前必読 (省略禁止・auditor 用・8 件)

1. `.claude/memory/ml_pipeline_baseline_v1.md` v3.6 §6.2.1〜§6.2.8 (= 本監査対象・約 700 行)
2. `.claude/memory/ml_pipeline_baseline_v1.md` §1 / §4 (= 工程概要 + 決着事項一覧)
3. `.claude/memory/ml_pipeline_baseline_v1.md` §6.1.1〜§6.1.6 (= regime ensemble 同型構造参照)
4. `.claude/memory/industry_benchmark_knowledge_base.md` (= 業界相場 + 5 レバー定量根拠・420 行)
5. `.claude/memory/cc_entry_logic_self_study.md` §13.1 / §13.5 / §14.1 / §14.2 (= ML カタログ Entry ML 関連節)
6. `.claude/rules/false_positive_incident_policy.md` §0-1 (= Prime Directive・本番再現性)
7. `.claude/rules/phase_compliance_checklist.md` §-1 / §0 / §1 (= USD 絶対値 blacklist / Phase 0 leak verify / Phase 1 学習)
8. `.claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md` (= CP1 監査結果・規範参照)

---

## 大目的 (= 不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (= cc_role §1.0)

⚠️ 本監査スコープ = §6.2.1〜§6.2.8 詳細設計の業界整合 + cat-bitget 固有制約整合 + leak 防止 + Phase 1 v6 教訓反映。月次 NET ≥ $1,900 達成可能性判定は対象外 (= Stage 3 PnL 早期判定 + Stage 4 最終 PnL で実証する)。

---

## 監査対象の事実データ

### §6.2.1 評価方法 (= 4 段階構造)

- **Stage 1 内部スコア** ([2] 完成直後・統計のみ): 揺れ幅 28 RMSE/R² + Triple Barrier 14 multiclass logloss/F1/accuracy + meta_label 14 AUC/Precision/Recall + feature_importance top 20 review + 56 ラベル間予測相関
- **Stage 2 視認 + Exit 抜き PnL proxy** ([2] 完成直後): まこさん視認 + 旧 Priority v9 overlap 分析 + entry 件数 verify + `TP_Precision × TP_gain - (1-TP) × SL_loss - fee` proxy
- **Stage 3 PnL 早期判定** ([4] Exit 完成後): base line = 旧 Priority v9 月 $370・純増分 (b)/(a) ≥ 5.1× で目標達成
- **Stage 4 最終 PnL** (= 8 工程合算後): Phase 5 全 12 ヶ月 + Phase 6-b 全 3 ヶ月

### §6.2.2 アルゴリズム選定

- 第一段階 = **LightGBM 56 個独立並列学習** (= scikit-learn MultiOutputRegressor encapsulate)
- 第二段階 = Stage 3 NET 純増分 (b)/(a) ≥ 1.3× で **LightGBM + XGBoost stacking** 検討
- LightGBM native multi-output 非対応のため MultiOutputRegressor 必須

### §6.2.3 ラベル設計詳細 (= 5 論点決着)

- 論点 1: K 重み付けなし (= 全 7 ホライズン並列)
- 論点 2: LONG/SHORT ラベル定義レベルで既分離
- 論点 3 (= まこさん判断「案 C」): **K 別 multiplier data-driven**
  - K=6/12 (= 30 分/1h・短期): TP × 1.5 / SL × 2.0 (= cat_v9 流・SL > TP)
  - K=24 (= 2h): TP × 2.0 / SL × 2.0 (= 中間)
  - K=48 (= 4h): TP × 2.5 / SL × 1.5 (= 中間)
  - K=96/144/288 (= 8-24h・長期): TP × 3.0 / SL × 1.5 (= AFML 流・TP > SL)
  - 価格非依存化 = ATR → ATR_pct (= ATR / entry × 100)
- 論点 4 (= まこさん判断「CC 推奨」): TripleBarrier class_weight="balanced" 第一段階 + Stage 1 recall<0.3 で SMOTE/focal loss / meta_label scale_pos_weight
- 論点 5: meta_label 14 並列学習のみ・接続は §6.2.7

### §6.2.4 入力特徴量設計 (= 6 論点決着)

- 論点 1 (= まこさん判断「案 A 統合」): **1 LightGBM + regime 6 列入力**・第二段階で regime 間 accuracy 差 > 30% なら案 B (= regime 別 model 分離 4 倍化) 検討
- 論点 2: 全投入 (= 2,604 + regime 6 = 2,610 列) + Stage 1 feature_importance post-pruning
- 論点 3: MTF 8 TF integrated 維持
- 論点 4: §6.1.6 既決着維持 (= one-hot + 確率値併用)
- 論点 5: 前処理なし (= LightGBM default 機能)
- 論点 6: 第一段階既存 1,462 維持 + Stage 3 で TSFresh 追加検討 (= leak チェック必須)

### §6.2.5 CV 設計

- fold 数 = **5 fold** (= regime ensemble §6.1.4 と同型)
- train/test 期間 = train_2021_2024 / test_2025 / test_2026_q1 (= phase_compliance §0 既決着)
- embargo = **K_max 288 bar + buffer 1 day = 2 day** (= AFML Ch.7)
- Purged 範囲 = ラベル生成期間 K_max 288 bar を train から除外
- CPCV (= 27h 計算コスト) は第一段階保留・第二段階 (= Stage 3 NET 純増分 < 2.0×) で発動

### §6.2.6 ハイパラ探索

- 探索方法 = **Optuna 20-50 trials + TPE sampler + MedianPruner**
- 探索範囲 = num_leaves 15-127 / learning_rate 0.01-0.1 / min_child_samples 20-100 / early_stopping 50-200 / max_depth -1 or 3-10 / **reg_alpha (L1) 0.0-1.0** / **reg_lambda (L2) 0.0-1.0**
- 個別 vs 共通 = **3 系統別 tune** (= 揺れ幅 28 regression / TripleBarrier 14 multiclass + class_weight=balanced / meta_label 14 binary + scale_pos_weight)
- 計算コスト = 約 11 時間 (= CPU only 1 日以内実用範囲)
- stacking ハイパラ = 第一段階 LightGBM のみ・第二段階 meta-learner 別 tune

### §6.2.7 出力 → entry 判定 (= 6 論点決着・全 CC 推奨採用)

- 論点 1 (= 段階的): 第一段階 ルール集約 (= `LONG_score = TP_prob × 0.4 + MFE_pct × 0.3 + meta_yes_prob × 0.3`) + 短期 K 重視 (= K=12/24 重み 0.5 / 他 0.1) / 第二段階 meta-learner
- 論点 2 (= 排他): score 高い方を採用・hedging は [2.5] cluster で吸収
- 論点 3 (= CC 決着): confidence = |LONG_score - SHORT_score| / max(LONG/SHORT_score)
- 論点 4 (= 第一段階固定): 暫定 0.6 + fold 別 calibrate (= 月 < 200 件で 0.5 / 月 > 400 件で 0.7) + 即死 reject (= 危険度 > 0.9)
- 論点 5 (= CC 決着): primary (= TripleBarrier 3 class) + secondary (= meta_label binary) → 集約 → [3] Sizing Half-Kelly
- 論点 6 (= §6.2.2 第二段階): stacking 採用時 LightGBM 56 + XGBoost 56 → meta-learner (= Logistic Regression / Random Forest / Ridge)

### §6.2.8 leak 防止

- 4 点 verify (= [[feedback_ml_leak_mandatory_check]]): 特徴量 grep / 使用箇所 verify / timestamp range / feature_importance 即時 review
- regime 6 列 causal alignment (= §6.1.6 既決着引継ぎ・merge_asof backward + assert no look-ahead)
- ラベル shift(-K) verify (= phase_compliance §0 Step 5 既決着引継ぎ)
- CV embargo 2 day (= §6.2.5 既決着引継ぎ)
- feature_importance top 20 自動 monitoring + 怪しい列名検出 (= fractal/pivot/resistance/support/future)
- blacklist 64 列除外 verify (= phase_compliance §-1 既決着引継ぎ・assert len(X.columns) == 2610)

---

## 監査スコープ

### 監査対象 (= 本監査内)

- 業界 standard 整合 (= WebSearch + 学術引用で独立 verify)
- cat-bitget 固有制約整合 (= スタートライン / 0.12 BTC / 価格非依存性 / 5m 取引)
- Phase 1 v6 教訓反映 (= 失敗主因 4 件の構造的解消)
- leak 防止経路の十分性 (= L-179 / L-128 同型予防)
- 段階的アプローチの妥当性 (= 第一段階 + 第二段階出口設計)
- 設計判断の論理整合性 (= 8 サブセクション間の連携 + 矛盾なし)

### 監査対象外 (= 現時点で判定不可能 or 別監査スコープ)

- 月次 NET ≥ $1,900 達成可能性判定 → Stage 3 / Stage 4 PnL で実証する
- 工程 [2.5] / [3] / [4] / [5] / [6] の詳細設計 → 別 CP 監査スコープ (= CP3 以降)
- 実装 (Python コード) の正しさ → 実装後の verify スコープ

---

## 監査観点 (= 一般・auditor_template ①〜⑦)

- ①統計学的妥当性
- ②リスク管理
- ③認知バイアス
- ④ソフトウェア工学
- ⑤再現性
- ⑥実行プロセス
- ⑦主エージェントバイアス (= CC 同型バイアス verify)

---

## 監査観点 (= 本監査固有・Q1-Q7)

### Q1 — Triple Barrier K 別 multiplier の業界整合 (§6.2.3 論点 3)

短期 K (= 30 分/1h) で「cat_v9 流 = TP × 1.5 / SL × 2.0」・長期 K (= 8-24h) で「AFML 流 = TP × 3.0 / SL × 1.5」を採用。中間遷移 K=24/48 は線形補間。

verify 事項:
- K 別 multiplier 使い分けは業界実証あるか / cat-bitget 固有設計として妥当か
- 中間遷移 K=24/48 の multiplier (= TP × 2.0/SL × 2.0 / TP × 2.5/SL × 1.5) の合理性
- 短期 K で「SL > TP」設計と長期 K で「TP > SL」設計の混在によるラベル分布の不整合リスク
- ATR_pct × multiplier の price-agnostic 整合性 (= L-179 同型予防)

### Q2 — 案 A 統合 (= regime 6 列入力) の妥当性 (§6.2.4 論点 1)

regime 別 model 分離 (= 案 B・224 モデル化) ではなく、1 LightGBM 56 個 + regime 6 列入力統合を採用。

verify 事項:
- regime-aware が単一より優位 ([arxiv 2509.09751]) との整合確認
- 案 A 統合で「regime × signal」の組合せパターンが decision tree で自動学習される実証
- 第二段階出口判定「regime 間 accuracy 差 > 30% で案 B」の閾値 30% の妥当性
- データ量 1/4 過学習リスクと予測精度差のトレードオフ

### Q3 — Optuna 探索範囲 + L1/L2 正則化の妥当性 (§6.2.6)

num_leaves 15-127 / learning_rate 0.01-0.1 / min_child_samples 20-100 / early_stopping 50-200 + L1/L2 正則化 0.0-1.0 を 30 trials で探索。

verify 事項:
- 業界 standard ([cc_entry_logic_self_study §13.1]) との整合
- 30 trials は Bayesian Optimization で最適近傍到達に十分か / 50 / 100 trials との差
- L1/L2 正則化追加は 2,610 列 over-fitting 抑制として有効か
- 3 系統別 tune (= 56 モデル個別 vs 共通) のトレードオフ

### Q4 — ルール集約 + 短期 K 重視 の妥当性 (§6.2.7 論点 1)

`LONG_score = TP_prob × 0.4 + MFE_pct × 0.3 + meta_yes_prob × 0.3`・K=12/24 重み 0.5 / 他 K 重み 0.1。

verify 事項:
- 重み 0.4/0.3/0.3 は業界実証 (= NN 0.4 + LSTM 0.3 + GRU 0.3) と整合か
- 短期 K 重視 0.5/0.1 で長期 K (= K=144/288 = 12-24h) の情報を 1/5 に圧縮するリスク
- ルール集約 (= 案 A) の precision 0.85 業界実証は cat-bitget 5m bar BTC 取引でも成立するか
- 段階的アプローチ (= 第二段階 meta-learner) 出口判定「Stage 3 純増分 < 1.5×」の閾値妥当性

### Q5 — threshold 0.6 固定の妥当性 (§6.2.7 論点 4)

第一段階固定 threshold 0.6 + fold 別 calibrate (= 月 < 200 件で 0.5 / 月 > 400 件で 0.7)。

verify 事項:
- 業界実証 ([arxiv 2501.10709] threshold 0.6 buy) は cat-bitget 5m bar BTC 取引でも整合か
- 月 275 件確保ラインとの整合 (= entry_score 分布が threshold 0.6 で月 275 件出るか暫定試算なし)
- 第二段階動的 threshold (= regime / 時間帯 / cluster 別) の出口判定「Stage 3 regime 別 NET 偏り > 30%」の閾値妥当性
- 即死 reject (= 危険度 > 0.9) の定義の具体化が必要か

### Q6 — leak 防止経路の十分性 (§6.2.8)

4 点 verify + regime 6 列 causal alignment + ラベル shift(-K) + CV embargo + feature_importance + blacklist の 6 項目。

verify 事項:
- L-179 (= fractal j+2 leak が Phase 1-7a 全段素通り) 同型予防として十分か
- L-128 (= MA70 look-ahead leak) 同型予防として十分か
- 56 モデル × feature_importance top 20 自動 monitoring の実装現実性
- TSFresh 第二段階追加時の leak チェック経路の具体性

### Q7 — Phase 1 v6 教訓反映の構造的解消

Phase 1 v6 失敗主因 4 件:
1. regime context 不在 → §6.1.6 regime 6 列 + §6.2.4 案 A 統合で構造解消
2. LONG-SHORT 並列学習 → §6.2.3 論点 2 ラベル定義レベルで分離で構造解消
3. MTF 欠落 → §6.2.4 論点 3 MTF 8 TF integrated で構造解消
4. ボラ予測逃げ → §6.2.3 §6.0.2 56 ラベル並列 (= 揺れ幅 28 + 決着 28) で構造解消

verify 事項:
- 4 件全部が構造的に解消されているか / 残存リスクはないか
- 「§6.2.4 論点 1 案 A 統合 (= regime 6 列入力)」で regime 別パターンが LightGBM decision tree で自動学習される根拠の十分性
- 56 ラベル並列学習で「決着系の予測逃げ」(= 揺れ幅予測の代わりに決着系予測に逃げる) 新規発生リスク

---

## 外部検索要請 (= 必須・WebSearch / WebFetch ツール使用)

`.claude/memory/` の内部知識に閉じない。auditor は以下の **外部検索を必ず実施** すること。ChatGPT 等の外部 AI 使用不可 (= まこさん課金外)。

### 検索対象 (= 5-8 件・auditor 適宜拡張)

1. **Triple Barrier ATR multiplier K 別使い分け業界実証 2025**:
   - クエリ案: "Triple Barrier ATR multiplier horizon K specific crypto Bitcoin 2025"
   - 期待発見: K 別 multiplier 採用事例 / 短期 vs 長期 multiplier 差の業界相場
2. **LightGBM regime-aware single vs separate models crypto 2025**:
   - クエリ案: "regime-aware single model vs regime-specific separate models LightGBM crypto Bitcoin trading 2025"
   - 期待発見: 統合 vs 分離の精度差実証 / accuracy 差 30% 閾値の妥当性
3. **Optuna LightGBM hyperparameter trials sufficiency trading 2025**:
   - クエリ案: "Optuna LightGBM hyperparameter trials sufficiency 30 50 100 trading financial 2025"
   - 期待発見: trials 数による Bayesian Optimization 収束実証
4. **Multi-output ensemble aggregation rule-based vs meta-learner 2025**:
   - クエリ案: "multi-output ensemble aggregation rule-based vs meta-learner stacking crypto trading 2025"
   - 期待発見: ルール集約 vs meta-learner の精度差実証 / 段階的採用パターン
5. **Look-ahead bias prevention crypto MTF causal alignment 2025**:
   - クエリ案: "look-ahead bias prevention crypto multi-timeframe MTF causal alignment merge_asof 2025"
   - 期待発見: MTF causal alignment 業界 standard / assert verify 実装パターン
6. **LightGBM L1 L2 regularization high-dimensional features over-fitting 2025**:
   - クエリ案: "LightGBM L1 L2 regularization high-dimensional 2000+ features over-fitting crypto trading 2025"
   - 期待発見: 2,610 列 over-fitting 抑制への正則化効果実証

---

## 結果ファイルフォーマット (= auditor 用)

`.claude/audits/2026-05-27_step2_entry_ml_design_cp2_audit_report.md` に以下 7 セクションを出力:

1. **Step -1 監査対象の型宣言** (= 設計文書型・約 700 行)
2. **Step 0 指摘前提確認** (= 事実データ verify + spec 文言 verify)
3. **観点 ①〜⑦ + Q1-Q7 の所見** (= 各観点・各 Q に対し「数値根拠ある断言」or「データ不足 (= 理由)」)
   - 観点 = PASS / FAIL 明示
   - Q = 業界整合 / 改善余地 N 件 明示
4. **外部検索結果サマリー** (= 検索クエリ + 主要発見 5-10 件・URL or 論文出典)
5. **総合判定**:
   - Verdict: GO / NO-GO / PIVOT / OTHER
   - 業界基準・学術根拠を伴う根拠
6. **改善方向性** (= 具体提案 3-7 件・優先度明示 Critical/Major/Minor)
7. **CC プロセス欠陥対策** (= cc_role §1.4.6 改訂提案・該当があれば)

---

## 必ず守ること (= auditor 守則)

- **目標 ($1,900/月) 達成可能性判定は対象外** (= 本監査スコープ外・Stage 3/4 で実証)
- 月次 NET ≥ $1,900 を下げる方向の提案禁止 (= cc_role §1.0 / auditor_template L15)
- 「可能性がある」「かもしれない」「検討の余地」は禁止 (= auditor_template L20)
- 数値根拠の断言 or 「データ不足 (= 理由: 〇〇)」で答える
- 同型バイアス警告: 同一訓練ベース AI として CC の論理に共感しすぎないこと (= auditor_template L24-30)
- ChatGPT 等の外部 AI 使用不可
- **外部検索は WebSearch / WebFetch ツールで必ず実施**
- 内部文書だけでなく、トレードについての外部認知 (= Crypto futures algo trading の業界実情) を踏まえる

---

依頼書終わり。

## まこさん向け呼びかけ例文 (= 新規セッション起動時)

別 Claude Code セッションを開き、本依頼書のフルパスを明示して以下のように依頼:

```
監査してほしい
.claude/audits/inputs/2026-05-27_step2_entry_ml_design_cp2_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。
