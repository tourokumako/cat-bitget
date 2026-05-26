# 工程 [1.5] regime ensemble 詳細設計 CP1 監査結果

- 監査日: 2026-05-27
- 監査区分: CP1 (= 工程 [1.5] 詳細設計 第 1 回監査・実装着手前)
- 監査対象: ml_pipeline_baseline_v1.md §6.1.1-6.1.6 (= 評価方法 4 段階 / HMM 再調整 / 固定ルール scoring / k-means / soft voting ensemble / 出力 6 列仕様)
- auditor session: cold start Plan サブエージェント (= メインセッション CC の判断 context を引き継がない第三者視点・依頼書 §着手前必読 10 件 + 外部検索 7+ トピックで独立 verify)
- 依頼書: `.claude/audits/inputs/2026-05-27_step15_regime_ensemble_design_cp1_audit_request.md`

---

## Step -1: 監査対象の型宣言

監査対象 = **詳細設計レビュー** (= 文書型・実装スクリプトはない段階)。

- 対象ファイル: `ml_pipeline_baseline_v1.md` §6.1.1-6.1.6 (= v2.7 として 2026-05-27 セッションで都度追記された 6 サブセクション)
- 対象範囲: 評価方法 4 段階 / HMM 再調整 / 固定ルール scoring / k-means 4 特徴量 / soft voting ensemble / 出力 6 列仕様
- 監査区分: CP1 (= 第 1 回詳細設計監査・実装着手前)
- 結果出力: 業界整合性 + cat-bitget 制約整合性 + 内部一貫性 verify (= 月次 NET 達成可能性判定および実装品質判定は本監査対象外)

---

## Step 0: 指摘前提確認 (機械的証跡)

### 0.1 依頼書本文 view 証跡

| ファイル | wc -l | 0% (L1) | 25% (L64) | 50% (L128) | 75% (L192) | 100% (L256) | 1 行要約 |
|---|---|---|---|---|---|---|---|
| 監査依頼書 | 256 | `# 【監査依頼】工程 [1.5] regime ensemble 詳細設計 ... CP1 監査` | `~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_cat_v9_no_modification.md` + ... | `### Q1 — 評価方法 4 段階 (§6.1.1) の業界整合性` | `   - クエリ案: "k-means regime detection feature selection cryptocurrency 5-minute return volatility"` | `→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。` | CP1 監査依頼書・auditor 宣言 + 着手前必読 10 件 + Q1-Q7 + 7 トピック外部検索要請 |

### 0.2 着手前必読 10 件 view 証跡

| # | ファイル | wc -l | 1 行要約 |
|---|---|---|---|
| 1+2+3 | ml_pipeline_baseline_v1.md (= 監査対象本体・§6.1.1-6.1.6 + §1 [1.5] + §3.4) | 576 | 8 工程フロー (= [1] 特徴量 → [1.5] regime ensemble → [2] Entry ML → [2.5] cluster → [3] Sizing → [4] Exit → [5] Risk → [6] 監視)・§6.1.1-6.1.6 で regime ensemble 詳細決着・3 判定器 soft voting + 出力 6 列 |
| 4 | ml_pipeline_baseline_v1.md §2.2 | 上に含む | 5 レバー寄与: Entry 1.4× / Exit 1.7× / 戦略並立 1.5× / regime 1.3× / Sizing 1.2× = 5.57× 中央値・[1.5] 担当 1.3× |
| 5 | step1_regime_design.md v2.2 | 277 | HMM v2.2 仕様 = 1h 判定 / 2h ヒステリシス / k=3 / diag / 84 次元 (= 14 指標 × 6 TF) / RobustScaler / Purged K-Fold 5 fold + purge 24h + embargo 24h / DI 差中央値ラベル付け / オンライン Viterbi 100h window |
| 6 | hmm_summary_train_2021_2024.json (v15 HMM 学習結果) | 180 | 5 fold 全 converge・mean log_likelihood_test = -597,630・mean avg_dwell_test = 7.892h・state 切替 670-956 回・状態分布 49.94% / 26.45% / 23.61%・sanity check PASS (= レンジ ADX 23.59 < 上昇 31.56 < 下降 32.75) |
| 7 | industry_benchmark_knowledge_base.md §2.4 | 420 | regime filter 業界実証 1.1-1.6× (= 200日MA / HMM Sharpe 1.76 vs 1.16 / Jump model +1-4% / LuxAlgo +10-30%)・「OOS で lag 問題あり」明記 |
| 8 | technical_analysis_knowledge_base.md §A.3-A.5 | 1691 | ADX 業界閾値: < 20 弱 / 20-25 emerging / > 25 強・ATR Multiplier 1.0-3.0・BB Squeeze BW < 10% / Band Walk = 順張り継続シグナル・cat_v9 経験値 ADX 22/30, BB slope ±10〜±50, ATR 60/100/150/250 |
| 9 | lessons_active.md L-230/L-231/L-232 | 2858 | L-230: 工程 1 視認「精度微妙」+ 業界フレーム逃避 / L-231: cat_v9 改造発想再演 + KB 未読断言・破綻判定 / L-232: regime ensemble 設計セッションで雑な言い切り癖 + 文章わかりづらい指摘 4 回連続 |
| 10 | feedback_cat_v9_no_modification.md + feedback_priority_starting_line_only.md | 33+67=100 | cat_v9 = ML スタートライン参照素材であり改造対象ではない・旧 Priority P1-P25 はテクニカル全体の 5-10% 最小単位・「素材転用」「ハイブリッド」「経験則ベース」禁止 |

### 0.3 v15 HMM 実数値 verify (依頼書本文 vs hmm_summary_train_2021_2024.json 照合)

| 依頼書本文記載 | json 実数値 | 一致 |
|---|---|---|
| 5 fold Walk-Forward 全 converge | 5 fold すべて `hmm_converged=true` | OK |
| mean log_likelihood_test = -597,630 | (-776,565.79 -662,298.21 -511,326.97 -514,675.45 -523,285.17)/5 = **-597,630.32** | OK |
| mean avg_dwell_hours_test = 7.89 | (6.626 +7.053 +9.450 +9.493 +6.840)/5 = **7.892** | OK |
| 状態切替 670-956 回 | 956/898/670/667/926 → min=667 / max=956 | 微差 (依頼書「670」は四捨五入・実値 min=667) |
| レンジ ADX 23.59 < 上昇 31.56 < 下降 32.75 | range_adx=23.589 / state1 (上昇) =31.556 / state0 (下落) =32.753 | OK |
| DI 差中央値: 上昇 +13.9 / 下降 -15.7 / レンジ -0.94 | +13.895 / -15.686 / -0.939 | OK |
| 状態分布: レンジ 51% / 上昇 26% / 下降 23% | counts 15833/8386/7486 → **49.94% / 26.45% / 23.61%** | レンジ実値 49.94% (依頼書「51%」は概数) |

依頼書記載は概ね v15 実数値と一致・微差はすべて四捨五入レベル・**判断材料として有効**。

---

## Step 1: 観点 (1)-(7) + Q1-Q7 の所見 (= 14 観点)

### 観点 (1) 統計学的妥当性 — **判定: FAIL (Major)**

**所見 (= 数値根拠ある断言)**:

1. **§6.1.5 soft voting の確率変換に統計的整合性欠陥が 2 件**:
   - **k-means cluster 中心からの距離 → softmax 確率変換 (= §6.1.5)**: softmax(-distance) は「同一スケールの logit」に変換する操作だが、距離の絶対値スケールが特徴量数 (4 次元) と RobustScaler 後の単位に依存し、3 cluster の確率分布が**人工的に sharp / flat になる方向にバイアス**する。業界では k-means の確率化は通常 `1/(1+distance^2)` (= Gaussian kernel) または「distance ratio 正規化」が使われる。**softmax 直接適用は確率としてキャリブレートされていない** (= scikit-learn calibration doc「Tree-based ensembles ... probabilities that rarely approach zero or one」と同型問題)。
   - **固定ルール scoring 点数 → 確率変換 (= §6.1.5 「各カテゴリ点数 ÷ 合計点数」)**: 6 指標 × 最大 1.5 重み = 最大合計 6.5 点を「3 カテゴリの和で除す」と各カテゴリ確率は 0-1 範囲だが、「各カテゴリの加点が独立事象」かのように扱う点で**点数の独立性仮定**が成立しない (= 同じ ADX が「上昇に加点 OR 下降に加点」で排他)。Brier score 評価すれば確率としての品質劣化が検出される構造。

2. **§6.1.1 Stage 1 内部スコア指標の併用に学術的不整合**: log-likelihood (HMM 用) / BIC (HMM 用) / silhouette score (k-means 用) を併記しているが、**3 判定器をまとめて評価する内部スコアは未定義**。HMM の log-likelihood と k-means の silhouette は単位が異なり、ensemble 全体の評価軸として直接使えない。**ensemble に対する統計評価指標** (= 業界では Brier score / log-loss / ECE = Expected Calibration Error が standard) の指定がない。

3. **§6.1.1 Stage 3 NET 比率合格基準の数値根拠**: 1.3x マル / 1.1x 三角 / 1.0x バツ は §2.2 「regime 1.3x 中央値」+ KB §2.4 「1.1-1.6x 業界実証」と整合・**数値根拠あり**。

4. **§6.1.3 不明確閾値 3.0 の数値根拠**: 「6 指標 × 平均 0.5 点として暫定値・実装後 verify 必要」と明記・**暫定値であることが透明・受け入れ可** (が、実装着手前にデータ駆動で決めるべき要 verify 項目)。

5. **§6.1.5 不明確閾値 0.4 の数値根拠**: 「6 指標 scoring 閾値 3.0 と整合・実装後 verify 必要」と明記・上に同じ。

**結論 PASS/FAIL**: **FAIL (Major)**。確率キャリブレーション設計の不備 (= 1 + 2) が ensemble の信頼性を直接損なう。soft voting は mcpanalytics whitepaper で「assumes well-calibrated probabilities」と明記されており、キャリブレーション欠陥のままでは soft voting の前提が成立しない。

### 観点 (2) リスク管理 — **判定: PASS**

**所見 (= 数値根拠ある断言)**:

1. **§6.1.6 「フィルタ強制適用しない」決着整合**: 出力 6 列 (label + 3 prob + confidence + vol_level) は後段 [2]/[2.5]/[3]/[4] への**入力特徴量として渡すのみ**で、明示的なフィルタロジックを含まない。**§1 [1.5] 元決着「フィルタとして強制適用しない」と完全整合** ([§6.1.6 設計判断の根拠] 明記)。

2. **不明確時のヒステリシス挙動**: §6.1.3 / §6.1.5 で「不明確 → 直前判定維持」(= ヒステリシス・連続 2 回切替) を採用。これは KB §2.4 で warned された **regime filter の「OOS で lag 問題」を逆方向で増幅しかねない設計だが、「フィルタ強制適用しない」原則と組み合わさることで、lag の害が直接的損失に転化しない**構造になっている (= 後段 ML が lag した regime を入力として「使うか使わないか」を学習する形)。

3. **0.12 BTC 上限への抵触**: 本工程は regime ラベル出力工程・ポジション発注は工程 [3]/[5] が担当。本工程単体では §0-2 違反リスクなし。

**結論 PASS/FAIL**: **PASS**。リスク管理上の構造的欠陥なし。

### 観点 (3) 認知バイアス — **判定: FAIL (Major)**

**所見 (= L-230 / L-231 / L-232 同型再演検出)**:

1. **業界フレーム逃避癖 (= L-230)**: §6.1.3 / §6.1.4 / §6.1.5 / §6.1.6 はすべて「業界 standard verify (= 本セッション 2026-05-27 WebSearch N 回)」を判断根拠の柱にしている。これは L-230「業界整合性 verify 済を判断根拠化する逆効果」と同型構造。**cat-bitget 固有制約 (= 5 分足 / 月 275 件 / 1 取引 2-3 時間 / cat_v9 改造禁止) からの逆算**が §6.1.3-6.1.6 に登場するのは §6.1.3 ATR 排除理由 (= 値動き幅は方向判別不能) 1 箇所のみ。他は全て業界実証引用に依拠。

2. **項目数並列による網羅性偽装 (= L-230 改善 1)**: §6.1.3 で「6 指標 × scoring」「5 ポイント修正」、§6.1.4 で「4 特徴量」、§6.1.5 で「業界 standard verify 4 件」、§6.1.6 で「6 列」のように**機械的な項目数並列**で網羅性を担保している外形。**指標選定の根拠が「業界 default だから」止まりで、cat-bitget 5 分足取引での発火頻度 / 単価寄与の試算が欠落**。

3. **視点低い・視野狭い (= feedback_cc_low_perspective_narrow_view)**: §6.1.4 で「k-means の 4 特徴量は HMM 84 次元との差別化 = シンプル + 解釈性」と表現しているが、**「同じ regime を 3 つの判定器で多角的に見る」根拠は提示されていない**。3 判定器の入力情報がすべて「1h トレンド + ボラ」系で**情報源として重複度が高い** (= HMM 84 次元の主要情報も「1h adx/di/macd/atr/bb_width」・k-means は「log_returns_1h + vol + sma + adx14_1h」・固定ルールは「adx + di + bb + ma + ichimoku」)。**ensemble の前提条件である「判定器間の予測誤差が無相関」が verify されていない**。

4. **L-232 改善 1 違反 (= 雑な言い切り癖)**: §6.1.5 「soft voting は業界推奨」「キャリブレーション済みモデルなら soft voting がほぼ常に好まれる」→ **k-means の softmax 確率変換・固定ルールの点数比確率はキャリブレーション保証なし**で、前提条件が成立していないのに業界推奨をそのまま採用している (= L-232 改善 1「cat-bitget 過去事例 verify」と同型違反)。

**結論 PASS/FAIL**: **FAIL (Major)**。L-230 / L-232 同型バイアスが §6.1.1-6.1.6 設計全体に再演している。

### 観点 (4) ソフトウェア工学 — **判定: PASS (Minor 改善余地)**

**所見**:

1. **出力 6 列の型・スキーマ**: §6.1.6 で型明示 (= category / float)・値域明示 (= 0.0-1.0)・派生列指定 (= one-hot encoded)。**スキーマ設計として明確**。

2. **MTF forward fill 実装の look-ahead リスク**: §6.1.6 「1h 判定を 5m bar に forward fill」は **1h bar の close 時刻 (= 14:00 bar の close = 15:00) と 5m bar の coverage 期間の整合**が verify されていない。Medium kjones2 Data Leakage doc では「forward fill can extend price history before first trading date」「Naive calendar alignment can suppress return volatility by 20%」と警告。本設計では `merge_asof(direction="backward")` 等の causal alignment 手法が指定されていない (= Minor)。**実装時に明示必要**。

3. **保存場所 results/regime_step1/**: 既存 v15 HMM artifact と同フォルダ・整合済。

**結論 PASS/FAIL**: **PASS (Minor)**。設計レベルでは大きな欠陥なし・実装時に causal alignment 明示が必要 (Minor)。

### 観点 (5) 再現性 — **判定: PASS**

**所見**:

1. **学習データ範囲統一**: §6.1.2 (HMM) / §6.1.4 (k-means) で「train_2021_2024」統一・**[step1_regime_design.md §2.6]** Walk-Forward Purged K-Fold 5 fold + purge 24h + embargo 24h と整合 (= AFML 業界標準・Lopez de Prado 整合)。

2. **artifact 命名**: §6.1.6 で `regime_predictions_train_2021_2024.parquet` / `test_2025.parquet` / `test_2026_q1.parquet`・**[phase_compliance_checklist §4a.4]** 「test 文字列禁止・train 含む」と整合 (= L-183 再演防止)。

3. **random_state 固定**: [step1_regime_design §2.4] で random_state=42 固定済 (= HMM 既存設計)。固定ルール / k-means についても random_state 固定が暗黙的に必要 (実装時 verify)。

**結論 PASS/FAIL**: **PASS**。再現性確保の構造的欠陥なし。

### 観点 (6) 実行プロセス — **判定: PASS (Minor)**

**所見**:

1. **段階的検証 Stage 1-4 の妥当性**: Stage 1 (= 統計) → Stage 2 (= 視認 + 統計検定) → Stage 3 (= [4] 完成後 PnL 早期判定) → Stage 4 (= 8 工程合算 PnL) の 4 段階は **[arxiv 2401.05337]** 「statistical metrics と financial metrics は並行評価」と整合・**業界整合**。

2. **Stage 3 タイミング ([4] Exit 完成後) の妥当性**: 早すぎる/遅すぎるリスクは **「最短経路の中で妥当」**。理由: [1.5] 単独で PnL 評価不可能 (= 戦略がないと NET 出ない・cat_v9 改造禁止)・[2]+[2.5]+[3] までだと Exit が暫定で正確な NET 比率が出ない・[4] 完成で初めて regime あり/なしの公正比較が可能。**早めの中間判定として妥当**。

3. **Stage 2 視認チェック**: [feedback_regime_visual_check] 「最低 10 回調整覚悟」と整合・**L-230 工程 1 視認「精度微妙」で保留**の経験を踏まえた設計。

**結論 PASS/FAIL**: **PASS (Minor)**。Stage 3 の合格基準数値 (1.3x マル / 1.1x 三角) を v15 HMM 既存実装の lift 実測と対比した sanity check (= 「単独 HMM 既に何倍出ているか」) を Stage 3 前に追加すると、ensemble 効果の純増分判定が明確になる (Minor 改善余地)。

### 観点 (7) 主エージェントバイアス — **判定: FAIL (Critical)**

**所見**:

CC は「業界 standard だから OK」を判断根拠化している (= §1.4.6.1 違反の典型・本セッション L-232 で再演)。具体例:

1. **§6.1.5 soft voting 採用根拠**: 「キャリブレーション済みモデルなら soft voting がほぼ常に好まれる」 (= 業界引用) → **でも本設計は cluster 距離 softmax + scoring 点数比でキャリブレーション保証なし**で前提条件未確認。

2. **§6.1.4 k-means k=3 採用根拠**: 「業界 default + HMM と同じで整合」 → [step1_regime_design §2.6] では「elbow method + silhouette score で k=3 妥当性 verify」と書かれているが、§6.1.4 では事前に k=3 と決め打つ形になっている (= データ駆動判定の経路が形骸化のリスク)。

3. **§6.1.3 一目均衡表 + MTF 整合 重み 1.5 採用根拠**: 「上位足重視の業界実証 [Multi-Timeframe Adaptive Regime FMZQuant]」 → cat-bitget の 5 分足取引で **上位足の重み 1.5x が NET 改善に寄与するかの cat-bitget 固有 verify ゼロ**。

4. **§6.1.1 NET 比率 1.3x 合格基準**: 「§2.2 業界中央値 + KB §2.4 業界実証」 → cat-bitget v15 HMM が単独で既に何倍出ているかの sanity check なしに、ensemble 追加で 1.3x を目指す形になっている (= base line 不明)。

**結論 PASS/FAIL**: **FAIL (Critical)**。業界 standard を判断根拠化する癖が §6.1.1-6.1.6 全体に貫通している。これは依頼書 §経緯 #2 (= 本セッション中 L-232 違反 9-10 回再演) と整合する所見。

---

### Q1 評価方法 4 段階 (§6.1.1) — **業界整合 / 改善余地 2 件**

業界整合あり ([arxiv 2401.05337]「statistical + financial metrics 並行評価」+ [bluechipalgos]「silhouette + log-likelihood」+ KB §2.4 + §3.1 と整合)。

改善余地:
1. **Stage 1 内部スコアに ensemble 全体評価指標 (= Brier score / ECE) が欠落**。HMM の log-likelihood と k-means の silhouette は単位異質で ensemble 全体評価できない。**追加: Brier score / log-loss / ECE for ensemble probabilities** (= mcpanalytics 「Brier score below 0.15」基準・scikit-learn calibration) を Stage 1 に追加。
2. **Stage 3 NET 比率の base line 未定義**。v15 HMM 単独で既に出ている lift をまず実測し、ensemble 追加で **純増分 1.3x = 「v15 単独 X 倍 → ensemble Y = X x 1.3 倍」**の形に書き直すべき。

### Q2 HMM 再調整方針 (§6.1.2) — **業界整合 / 改善余地 2 件**

業界整合あり ([Preprints 202603.0831 Bitcoin HMM 3 状態]・[QuantStart QSTrader Sharpe 1.76]・[KB §2.4 HMM Sharpe 1.76 vs 1.16] と整合)。「教師なし HMM 単独限界 = ensemble 補強」も [aimspress 2025 ensemble HMM Sharpe 1.68] と整合。

改善余地:
1. **7.89h 平均切替間隔 vs 5 分足取引の整合性 verify が不足**。[step1_regime_design §2.6] では特に問題視されていないが、5 分足取引 (= 1 取引 2-3 時間想定) に対して regime が 7.89h で切り替わる = **1 取引の中で regime が切替変動するリスクは低い**・むしろ「regime が長すぎて中間で意味ある変化を見逃す」リスクの方が大きい。Stage 3 NET 比率で verify される構造ではあるが、Stage 1 で「dwell hours が短い fold (= fold 0 で 6.63h・fold 4 で 6.84h) と長い fold (= fold 2/3 で 9.45-9.49h) の差」を見て fold 別 lift 安定性を pre check する余地。
2. **「v15 を大幅変更なし」の単独調整代替案検討が形骸**。状態数 k=2 (= up/down のみ) / k=4 (= up/down/range/high-vol) / covariance_type=full 復活 等を **データで verify せずに排除**している。[step1_regime_design §2.4] で「Phase 5 Replay 結果で diag が不足と判明したら full に戻す可逆性あり」と明記されているのに、§6.1.2 で「diag 維持」とだけ書かれているのは矛盾ではないが verify 経路が不明確。

### Q3 固定ルール判定器 (§6.1.3) — **業界整合 / 改善余地 3 件**

業界整合あり ([pyquantlab Regime Filtered Trend Strategy]・[macrosynergy 2025]・[AIMS 2025 ensemble-HMM voting]・[dev.to crypto regime AI agent 「10 indicators with confidence scoring」]・[Ichimoku Regime Classifier] と整合・全部 AND 否定 + scoring + weighted vote = 業界主流確認)。

改善余地:
1. **重み 1.5 の MTF 整合 + 重み 1.0 の他 5 指標は cat-bitget 固有 verify ゼロ**。「上位足重視の業界実証 [FMZQuant]」だけが根拠で、cat-bitget の 5 分足取引で「1h + 4h 整合が NET に効くか」のデータ駆動 verify がない。**初期等重み (= 全部 1.0) + Walk-Forward 重み調整**の方が業界 standard ([scikit-learn VotingClassifier「GridSearchCV」]) と整合。
2. **ATR を方向判定から外す変更の妥当性は OK だが、ボラ別フラグ (250/100) の数値根拠が cat_v9 経験値のみ**。[KB §A.4.5] で cat_v9 ATR 閾値群が記載されているが、本設計の「高 250 / 中 100 / 低 < 100」は **特定 Priority (= P3 ATR_MIN=250 / P1 ATR_MIN=60 等) と整合しない簡略化**で、本来は ATR_pct (= ATR / close x 100) 化が必要 (= [phase_compliance §-1] 価格非依存性 #4 で USD 絶対値系 blacklist と整合)。**ATR 絶対値 250/100 は BTC 価格 $30k と $150k で意味が異なる**ため、ATR_pct への変更が必須 (= L-179 価格非依存性違反リスク)。
3. **一目均衡表の追加根拠が業界実証 1 件のみ ([Ichimoku Regime Classifier OSS])・cat-bitget 過去事例なし**。Ichimoku は 9-26-52 期間で 5 分足だと[3commas guide]「shorter periods should be used for cryptocurrencies」と推奨されているが、本設計では 1h ベースで標準期間 9-26-52 を使う前提・**5 分足ノイズに対するロバスト性 verify なし**。

### Q4 k-means 判定器 (§6.1.4) — **業界整合 / 改善余地 3 件**

業界整合あり ([JDMDC k-means + HMM Bitcoin 2025]・[datadave1 Medium]・[LSEG 2023 HMM+GMM+k-means]・[arxiv 2310.01285 sliced Wasserstein k-means] と整合)。

改善余地:
1. **k=3 事前決め打ちのリスク**: [step1_regime_design §2.6] で「elbow + silhouette で k 妥当性 verify」と書かれているのに、§6.1.4 で k=3 事前決定。**elbow / silhouette で k=2 or k=4 がベターと判定された場合の経路が未定義**。「HMM と同じ k=3 で整合」が根拠だが、k-means と HMM は異なるアルゴで最適 k が異なって自然。
2. **4 特徴量の選定根拠が業界 default 引用のみ**: [JDMDC 2025] では「log returns + rolling volatility」の 2 特徴量・本設計の「+ close_vs_sma20_pct + adx14_1h」追加は cat-bitget 固有 verify なし。**HMM 84 次元との情報重複度が高い** (= sma20 + adx14 は HMM 入力にも含まれる) → 「シンプルさで差別化」根拠と矛盾。
3. **rolling_volatility(20) の window 20 期間の根拠が[step1_regime_design §3.1]で「未確定・議論未経由」**。§6.1.4 で「rolling_volatility(20)」と書かれているが、step1 設計書では window 期間は議論未経由項目。**§6.1.4 の確定値と step1 設計書の議論未経由が矛盾**。

### Q5 ensemble 機構 (§6.1.5) — **業界整合 / 改善余地 3 件**

業界整合あり ([aimspress 2025 ensemble HMM voting Sharpe 1.68]・[mcpanalytics「キャリブレーション済みなら soft voting」]・[Hudson & Thames Pairs Trading Markov Regime Switching]・[Raschka Weighted Majority] と整合)。

改善余地:
1. **確率変換のキャリブレーション欠陥 (Critical)**: k-means cluster 距離 → softmax / 固定ルール scoring → 点数比はキャリブレーション保証なし。[scikit-learn calibration]「Tree-based ensembles ... probabilities rarely approach 0 or 1」と同型問題。**isotonic regression / Platt scaling で calibrate** してから soft voting に投入する必要 ([trainindata blog]「reliability diagram + Brier score evaluation」)。
2. **初期等重み (= 全部 1.0) は L-232 改善 1「cat-bitget 過去事例 verify」違反**: v15 HMM が単独で出している lift と、固定ルール / k-means が単独で出す予想 lift が事前見積もりされていないため、等重みが最適である根拠なし。[scikit-learn VotingClassifier]「GridSearchCV with CV」で重み調整が業界 standard。**Walk-Forward CV で初期重みも調整**すべき (= [aimspress 2025 hybrid voting 実装と整合])。
3. **不明確閾値 0.4 の数値根拠が「scoring 閾値 3.0 と整合」で循環論証**。3.0 自体が暫定値 (= 6 指標 × 平均 0.5)。両方 data-driven で決めるべき (= 不明確閾値 = 全 fold の最高確率分布 25th percentile 等)。

### Q6 出力仕様 (§6.1.6) — **業界整合 / 改善余地 2 件**

業界整合あり ([akash-kumar5 CryptoMarket Regime Classifier HMM+LSTM]・[Live-Market-Regime-Classifier merge_asof]・[MDPI 2025 Regime-Aware LightGBM] と整合)。

改善余地:
1. **MTF forward fill の look-ahead leak リスク (Critical 寄り Major)**: 「1h 判定を 5m bar に forward fill」は **1h bar の close 時刻 = 当該 1h の終了時点**だから、`14:00-14:59` の 1h bar の判定は **15:00 時点で初めて使用可能**。`merge_asof(direction="backward")` でないと「14:00 の判定値を 14:00-14:55 の 5m bar に充てる = look-ahead leak」になる。本設計では `forward fill` という表現で **causal alignment が明示されていない** (= [arxiv 2603.20237 「Naive calendar alignment can suppress return volatility by 20%」]同型問題)。**実装時に明示必要**。[Live-Market-Regime-Classifier]「merge_asof で異なる時間軸を統合」と整合化させる必要。
2. **one-hot encoded 派生列 + 確率値併用の冗長性**: LightGBM は連続値分割が効率的 (= §6.1.6 本文記載と整合) だが、`regime_is_uptrend` (= bool 0/1) と `regime_prob_up` (= 0-1 連続) は **完全に従属関係** (= bool は確率の閾値化)。**LightGBM は冗長特徴量に対して L1 正則化 / feature_importance で自動的に冗長を弾く**ので大きな害はないが、Phase -1 blacklist と整合させて **bool 派生列を blacklist 候補に入れる**か、確率値だけ残す方が clean。

### Q7 全体一貫性 + cat-bitget 制約整合性 — **業界整合 / 改善余地 3 件**

業界整合あり (3 判定器 ensemble + 1h 判定 + ヒステリシス + フィルタ強制適用しない の構造は L-230 学習を反映した妥当設計)。

改善余地:
1. **3 判定器の役割分担「補完関係」の verify がゼロ**: §6.1.4「3 判定器の役割分担」表で「HMM = 多角性 / k-means = 簡潔性 / 固定ルール = 明示性」と書かれているが、**3 判定器の予測誤差の相関 verify がない**。ensemble の業界実証 (= [KB §2.3 戦略並立 「Sharpe ∞ for uncorrelated portfolios」]) は **判定器間の予測誤差が無相関** が前提。本設計では 3 判定器すべて「1h adx / di / sma / bb / log_returns」系で**入力情報が高度に重複**しているため、予測誤差も相関が高いリスク (= 戦略並立効果の前提崩壊)。
2. **判定間隔 1h + ヒステリシス 2h の 3 判定器統一の妥当性**: 「3 判定器すべて 1h + 2h ヒステリシス」と統一されているが、k-means は時系列依存なし (§6.1.4 表)・HMM は時系列依存ありで本質が異なる。**k-means の判定が hour 単位で離散ノイズを拾うリスク**。判定器ごとに最適粒度が異なる可能性は実装時 verify 必要。
3. **cat-bitget 制約整合性**: 5 分足 / 0.12 BTC / 月 275 件 / 1 取引 2-3 時間 / cat_v9 改造禁止 は **本工程設計と整合** (= 本工程は出力工程・直接抵触なし)。1 取引 2-3 時間 vs regime 切替 7.89h は「regime が安定して 1 取引内で切替らない」方向で整合。**ただし上記 ATR 絶対値 250/100 の価格非依存性違反は cat-bitget 制約 (= train 期間 $30k-$60k vs 本番 $100k-$150k 価格レンジ) と矛盾** (Major)。

---

## Step 2: 外部検索結果サマリー

実施したクエリ 8 件と主要発見:

### 検索 1: regime detection evaluation statistical financial metrics walk-forward 2025
- **主要発見**: rolling-origin walk-forward 評価で「point accuracy + directional metrics + distributional scores + VaR + ES backtest」を **複層的に評価**するのが 2025 業界標準。Bitcoin 15min walk-forward 2021-2025 で「Sharpe + drawdown 改善」を確認。本設計 Stage 1-4 はこの方向と整合。
- 出典: arxiv 2605.17117 Geometric Observables / arxiv 2510.10807 MARCD CVaR Portfolio / ResearchGate 395401021 Adaptive Regime-Based Trading on Bitcoin

### 検索 2: HMM regime detection single method limitation ensemble improvement crypto 2025
- **主要発見**: HMM の constant transition probabilities + strict Markovian assumption は high-frequency crypto の「abrupt / non-sequential / overlapping regime shifts」に対し**構造的限界**。Ensemble-HMM Voting (= XGBoost / Bagging + HMM) で**Sharpe 1.68 / drawdown 削減 / false signal 削減**。本設計 §6.1.2「教師なし単一手法構造的限界」と整合・ensemble 採用根拠は強い。
- 出典: AIMS 2025 ensemble-HMM voting framework / Preprints Bitcoin HMM 2024-2026 / PickMyTrade 2026 Guide

### 検索 3: rule-based regime classification scoring weighted vote multi-indicator crypto 2025
- **主要発見**: real-time crypto regime detection で「10 independent indicators + confidence scoring」が 2025 業界実装パターン。Multi-indicator (= EMA + ADX + RSI + BB + volume) + weighted scoring が standard。本設計 §6.1.3 6 指標 scoring は業界主流と整合・**ただし全部 AND を避けた scoring 構造は確認済**。
- 出典: dev.to Crypto Regime Detection Local AI Agent / getregime.com API / TradingView Regime Scripts

### 検索 4: k-means regime detection feature selection cryptocurrency 5-minute return volatility
- **主要発見**: Bitcoin minute-level で「log returns + rolling volatility」が k-means 入力の業界 default・**2 特徴量** (本設計 4 特徴量より少ない)。k=3 (bullish / bearish / sideways) も business default。**JDMDC 2025 k-means + HMM hybrid が単独より低 BIC + 高 log-likelihood**で本設計 ensemble 方向性と整合。
- 出典: JDMDC k-means + HMM Bitcoin 2025 / datadave1 Medium K-Means Regime / arxiv 2310.01285 Wasserstein k-means

### 検索 5: soft voting weighted ensemble financial regime classifier initial weights cross validation
- **主要発見**: scikit-learn / mlxtend / Raschka すべてで「soft voting = argmax of summed predicted probabilities」「**well-calibrated classifiers 前提**」と明記。**重みは GridSearchCV + cross-validation で決定**が業界 standard。**初期等重みは「事前情報なし」のときのみ妥当**で、本設計のように HMM v15 が既に学習済みで lift がある状態では等重みは optimal ではない。
- 出典: mcpanalytics Voting Ensemble Practical Guide / Raschka Weighted Majority Rule / scikit-learn VotingClassifier

### 検索 6: multi-timeframe forward fill look-ahead leak regime feature 1h to 5m
- **主要発見**: forward fill は **higher TF 値の causal alignment が不明確だと look-ahead leak** が発生する典型パターン。TradingView の `request.security() with lookahead_off` で fetch するのが正解。**Naive calendar alignment で return volatility が 20% suppress される**実証あり。本設計 §6.1.6 は forward fill のみ明示で causal alignment が暗黙 → 実装時明示必要 (Major)。
- 出典: arxiv 2603.20237 Temporal Coverage Bias / Medium kyle-t-jones Data Leakage Lookahead Bias

### 検索 7: Ichimoku cloud regime detection trading rule cryptocurrency
- **主要発見**: Ichimoku Regime Classifier OSS が存在し「TREND UP / TREND DOWN / VOLATILE」3 ラベル分類で多条件 (= price vs cloud + Tenkan vs Kijun + Chikou vs price + Chikou vs cloud + cloud direction + cloud stability) を集約。**Crypto では 9-26-52 標準期間より短い期間推奨**。本設計 §6.1.3 で「価格 > 雲上限 / < 雲下限 / 雲内」のみ採用は **Ichimoku の情報量を相当に削いだ簡略版**で、cat-bitget 5 分足での寄与 verify が必要。
- 出典: QuantifiedStrategies Ichimoku Backtest / LuxAlgo Ichimoku Five Line / 3commas Ichimoku Guide 2025

### 検索 8: probability calibration tree model regime soft voting ensemble Brier score
- **主要発見**: Brier score = strictly proper scoring rule で「forecast uncertainty + resolution + reliability」を分解評価。**soft voting の前提条件: 「Brier score < 0.15 + reliability curve diagonal」**。Tree-based ensemble は probabilities が 0/1 から離れる傾向で **calibration が必要**。本設計 §6.1.5 で calibration step が欠落 (Critical)。
- 出典: scikit-learn Probability Calibration / emergentmind Brier Score / arxiv 1808.00111 Probability Calibration Trees

---

## Step 3: 総合判定

### Verdict: **PIVOT** (= 一部修正で着手可)

### 根拠

**1. 業界整合性は概ね確保されている**: 8 検索すべてで「3 判定器 ensemble + soft voting + scoring + k-means + Ichimoku + walk-forward + 1.1-1.6x lift」のいずれかに対応する業界実証あり。設計の骨格は[aimspress 2025]・[JDMDC 2025]・[KB §2.4]・[step1_regime_design v2.2] と整合。

**2. ただし「業界 standard 採用」だけが判断根拠の構造的問題**: 観点 (3) 認知バイアス FAIL (Major) + 観点 (7) 主エージェントバイアス FAIL (Critical) = 本セッション L-230 / L-232 同型再演が §6.1.1-6.1.6 全体に貫通。CC は依頼書経緯 #2 で自認している L-232 違反 9-10 回再演を、本設計でも構造的に再演している。

**3. 実装着手前に修正必須の Critical 欠陥が 2 件**:
   - C1: ensemble 確率変換のキャリブレーション欠陥 (= 観点 (1) / Q5 改善 1)・soft voting 前提条件未充足
   - C2: §6.1.3 ATR ボラ別フラグの絶対値 250/100 (= 価格非依存性違反・L-179 同型・[phase_compliance §-1] 既存ルール違反)

**4. 月次 NET >= $1,900 達成可能性判定は本監査スコープ外** (= 依頼書 §大目的 明記)・本判定は **詳細設計の業界整合性 + cat-bitget 制約整合性 + 内部一貫性** の verify。

**5. NO-GO (= 重大欠陥・再設計必要) ではない理由**: 設計骨格 (= 3 判定器 + soft voting + 1h + ヒステリシス + フィルタ強制適用しない + 出力 6 列) は妥当・実装着手前の修正 3-5 件で GO 可能。

**6. GO (= 修正なし実装着手可) ではない理由**: Critical 欠陥 C1 (キャリブレーション) を実装後に発見すると、ensemble 全体の再設計が必要になる。実装着手前に修正する方が労力ずっと少ない。

---

## Step 4: 改善方向性 (= 具体提案 7 件・優先度明示)

### Critical-1: ensemble 確率変換のキャリブレーション設計を §6.1.5 に追加
- 修正対象: §6.1.5「各判定器の確率変換」表
- 修正内容:
  - HMM `predict_proba` 出力は理論上キャリブレート済だが、isotonic regression で fold 別に re-calibrate
  - k-means cluster 距離 → **softmax 直接適用を廃止**し、`exp(-d^2 / 2σ^2)` (= Gaussian kernel) で確率化後 isotonic calibration
  - 固定ルール scoring 点数比 → isotonic regression で calibration
  - Stage 1 評価に **Brier score + reliability diagram + ECE** を追加 (= 業界 standard)
- 出典: scikit-learn Probability Calibration / emergentmind Brier Score

### Critical-2: §6.1.3 ATR ボラ別フラグを ATR_pct (= ATR / close x 100) に変更
- 修正対象: §6.1.3「ATR (= ボラ大きさ) は方向判定から外して別フラグ並列出力」
- 修正内容: 「高ボラ ATR(14) >= 250 / 中ボラ 100 <= ATR(14) < 250 / 低ボラ < 100」 → 「**ATR_pct (= ATR/close x 100)** で閾値設定」に変更。train_2021_2024 期間 BTC $30k-$60k vs 本番 $100k-$150k の価格レンジで絶対値 250 USD の意味が変わる (= L-179 価格非依存性違反・[phase_compliance §-1] 既存 blacklist と整合)
- 閾値の決め方: train 期間で `atr14_pct` の 25th / 75th percentile を採用し fold 別 verify (= data-driven 判定)

### Major-1: Stage 3 NET 比率 base line を v15 単独実測で再定義
- 修正対象: §6.1.1 Stage 3 合格基準
- 修正内容: 現「ensemble あり / なし」 → **「v15 HMM 単独 / なし」と「ensemble (= v15 + 固定 + k-means) / なし」の 2 段階比較**。ensemble の純増分は「ensemble 値 / v15 単独値」で評価。これで「v15 単独で既に何倍出ているか」が見え、ensemble 追加の意義 verify が明確化

### Major-2: §6.1.5 初期等重みを Walk-Forward CV データ駆動に変更
- 修正対象: §6.1.5「重み: 初期は等重み」
- 修正内容: **Walk-Forward Purged K-Fold 5 fold で GridSearchCV** により初期重みを決定。等重みは grid 上の 1 点として比較対象に残す (scikit-learn VotingClassifier GridSearchCV / aimspress 2025 hybrid voting 実装と整合)
- 探索空間: 各判定器の重み in {0.5, 1.0, 1.5, 2.0} の grid (= 4^3 = 64 通り) + 等重み (1.0, 1.0, 1.0)

### Major-3: §6.1.6 MTF forward fill の causal alignment を明示
- 修正対象: §6.1.6「MTF 接続」
- 修正内容: `forward fill` の表現を **「`merge_asof(direction="backward")` で 1h bar close 時刻 = 当該 1h 終了時点 = 次 1h 開始時刻に判定を 5m bar へ充当」**と明示。1h bar `14:00-14:59` の判定値は **15:00 以降の 5m bar にのみ充当可能** (= 14:00-14:55 の 5m bar には充当不可・causal violation)。実装スクリプトに `assert no look-ahead in regime forward fill` を追加
- 出典: arxiv 2603.20237 Temporal Coverage Bias / Live-Market-Regime-Classifier merge_asof 実装例

### Minor-1: 3 判定器の予測誤差相関 verify を Stage 1 に追加
- 修正対象: §6.1.1 Stage 1
- 修正内容: 3 判定器の予測誤差 (= 各 fold の test 誤分類率 or log-loss residual) の **pairwise Pearson 相関**を計算し、「相関 < 0.5 → ensemble 効果あり / 相関 > 0.7 → 判定器選び直し」の sanity check 追加。ensemble の前提 (= 判定器間の予測誤差が無相関) を verify する経路

### Minor-2: §6.1.4 k=3 事前決め打ちを elbow + silhouette data-driven に変更
- 修正対象: §6.1.4「クラスタ数 k=3」
- 修正内容: **k in {2, 3, 4, 5} で elbow method + silhouette score を fold 別評価**し、最頻 k を採用。step1_regime_design §2.6 「elbow + silhouette で verify」と整合させる

---

## Step 5: CC プロセス欠陥対策 (= cc_role §1.4.6 改訂提案)

### 該当発見: 本セッションでの L-232 違反 9-10 回再演対策が **構造的に効いていない** 証拠

L-232「雑な言い切り癖 (= 業界実証だけを根拠) 9 回 / 文章わかりづらい指摘 10 回」を本セッション中に CC 自身が認めているが、§6.1.1-6.1.6 の設計プロセス自体が同型バイアス (= 業界 standard 引用を判断根拠化) で進められた。これは cc_role §1.4.6.1 (= ML pipeline 業界整合 verify 9 項目) が **「業界整合性を出すゲート」**になっており、**「業界 standard が cat-bitget 固有制約と矛盾しないか verify するゲート」**になっていない構造的問題。

### 提案: cc_role §1.4.6.1 に「Anti-業界フレーム逃避ゲート」を追加

現行 §1.4.6.1 の 9 項目に、以下 3 項目を追加:

10. **cat-bitget 固有 verify**: 業界 standard を採用する各設計判断について、「cat-bitget 過去事例 (= cat_v9 経験値 / v15 HMM 実測 / 過去 Phase 5 Replay) で類似条件の lift を 1 行 verify」。verify できない場合「業界 standard 採用根拠なし → data-driven で決める」と書く。
11. **判定器/レバーの予測誤差相関 verify**: ensemble / multi-strategy / multi-indicator scoring を提案する場合、「各構成要素の予測誤差が無相関か」の verify (= [KB §2.3 Square Root Rule 前提]) を必ず添える。相関 > 0.5 ならレバー寄与は減じる方向に試算。
12. **暫定値・閾値の data-driven 経路宣言**: 「暫定 3.0」「暫定 0.4」のような数値を設計に含める場合、**実装着手時にどの fold データ / どの統計値 (= 25th percentile 等) で決定するか**の経路を併記。「実装後 verify 必要」だけでは経路として弱い。

### 提案: 本依頼書経緯 #2 (= L-232 違反 9-10 回再演) を lessons L-233 として記録

本セッションで CC が L-232 を「9-10 回再演」と自認しているが、lessons_active.md には L-233 として明記されていない (= L-232 に含まれている状態)。**L-232 違反 9-10 回再演という別パターン**として L-233 を立て、cc_role §1.4.6.1 改訂 (= 上記 Critical-1) と紐付ける必要。

### 提案: 本監査結果反映時の機械的反映禁止 (= L-213 + L-214 再演防止)

cc_role §1.5.5 「機械的反映表現の使用条件厳格化」と整合し、本監査結果 (= Critical 2 + Major 3 + Minor 2 件) の反映は **「設計判断を含む反映」**として CC 独立評価プロセス (= 1 件ずつ採用支持/要再評価/拒否 + 根拠提示) を必ず通す。「監査結果 7 件 100% 反映 = 機械的反映」と称してスキップする L-213 / L-214 再演リスクあり (= 本監査 cold start で発見した独立第三者所見・依頼書経緯 §3 まこさん「自分でわからない部分が多い・信じて任せて大丈夫か」懸念の根本対策)。

---

## Sources (= 本監査で参照した外部 URL)

- arxiv 2605.17117 Geometric Observables for Financial Regime Detection
- arxiv 2510.10807 MARCD CVaR Portfolio
- ResearchGate 395401021 Adaptive Regime-Based Trading on Bitcoin
- aimspress 2025 ensemble-HMM voting framework
- Preprints 202603.0831 Markov/Hidden Markov Models for Regime Detection in Cryptocurrency Markets
- PickMyTrade Regime Detection 2026 Guide
- dev.to Crypto Regime Detection with Local AI Agent
- getregime.com Real-Time Crypto Regime Detection API
- TradingView Regime Scripts
- JDMDC k-means + HMM Bitcoin 2025
- datadave1 Medium Detecting Market Regimes K-Means
- arxiv 2310.01285 Wasserstein k-means clustering
- mcpanalytics Voting Ensemble Hard vs Soft
- Raschka Weighted Majority Rule Ensemble
- scikit-learn VotingClassifier
- scikit-learn Probability Calibration
- arxiv 2603.20237 Temporal Coverage Bias in Financial Panel Data
- Medium kyle-t-jones Data Leakage Lookahead Bias Causality
- QuantifiedStrategies Ichimoku Backtest
- LuxAlgo Ichimoku Five Line Trend System
- 3commas Ichimoku Guide 2025
- bluechipalgos Unsupervised Learning Market Regime Detection
- Two Sigma Machine Learning Approach to Regime Modeling
- emergentmind Brier Score
- arxiv 1808.00111 Probability Calibration Trees
- trainindata Probability Calibration in Machine Learning

---

監査結果ファイル終わり。

戻り報告 (= 依頼書 §即実行 #4):
- 結果ファイルパス: `/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md`
- Verdict: **PIVOT** (= 一部修正で着手可)
- Critical 件数: **2 件** (C1 ensemble 確率変換キャリブレーション欠陥 / C2 §6.1.3 ATR 絶対値 250/100 = 価格非依存性違反)
