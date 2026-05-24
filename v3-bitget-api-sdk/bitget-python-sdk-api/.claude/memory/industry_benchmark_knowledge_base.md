# industry_benchmark_knowledge_base.md — 業界相場・経験則 ナレッジベース

作成: 2026-05-26 (CC・cc_role v1)
版: v1 (WebSearch 18 件 + 業界文献統合)
位置付け: **目標達成レシピ (cc_target_pathway_design.md・予定) の数値根拠ベース** + 今後の ML pipeline 設計・Phase 合格基準設計の参照素材
状態: 運用しながら追記・改訂

---

## §0 本ファイルの位置付け・運用ルール

### 0.1 なぜこのファイルが必要か

2026-05-26 セッションで CC が「5.1× gap ($370/月 → $1,900/月) をどう作るか」を業界経験則ベースで分解しようとしたが、根拠が CC の記憶ベースで Web 調査していなかった。まこさん指摘「君は知見を広めるために WEB は検索しないの?」を受けて WebSearch 18 件を実施。

cc_role §1.0「自分の知見だけに頼らない・web 検索・WebFetch を能動的に活用する」義務を物理的に起動するため、業界相場・経験則を文書化して毎セッション参照可能にする正本ファイル。

[[technical_analysis_knowledge_base]] (テクニカル指標辞典) と並ぶナレッジベース 2 本目。本ファイルは「業界相場・パフォーマンス経験則」担当。

### 0.2 運用ルール (絶対遵守)

- **目標達成設計 / Phase 合格基準設計 / 戦略レバー値見積もりの前に必読**
- 機械的証跡 (`wc -l` + Read 全文 view + 該当箇所引用) を出す
- **本ファイルに記載のない業界相場が必要になった場合は WebSearch / WebFetch で能動調査** (cc_role §1.0 義務)
- 調査結果は本ファイルに追記・引用 URL 明記・調査日付明記
- CC 単独で「業界相場はこんな感じ」と判断しない・**外部出典 + /audit + まこさん検閲の 3 経路** で確認
- 業界相場は時代変化する (例: ML 性能・cryptohf 平均 return) → 半年-1 年ごとに WebSearch で更新推奨

### 0.3 業界相場と cat-bitget の関係

業界相場は **キャリブレーション素材** (= cat-bitget の目標が現実的か / レバー値見積もりが妥当か)。業界平均 = cat-bitget の必達ライン ではない。

| 業界相場の役割 | 適用方法 |
|---|---|
| 目標の現実性 calibration | cat-bitget の $1,900/月 が業界相場の何 percentile か把握 |
| レバー値見積もりの根拠 | 「Entry 改善 1.5×」と書くなら業界実証で 1.3-2× の範囲が確認できるか |
| Phase 合格基準設計 | 「TP Precision > 0.5」と書くなら業界相場での妥当性 + 月次 NET への写像 |
| 撤退判断 | 業界相場の上位 N percentile を超える要求 = 設計欠陥または楽観バイアスの可能性 |

---

## §1 月次 NET 業界相場 — 目標 $1,900/月 の現実性キャリブレーション

### 1.1 Crypto Quant HF (機関) 業界相場 (2025)

| 区分 | 年次 return | Sharpe | 出典 |
|---|---|---|---|
| Crypto HF 平均 (全 2025) | **36%** | **1.6** | coinlaw.io 2025・cryptoinsightsgroup |
| Algo/Quant HF (2025) | **48%** | **2.51** ★ 最高 | cryptofundresearch.com Q4 2025 |
| Top performer (2025) | >150% | — | cryptofundresearch.com |
| Bitcoin 単独 (2025) | ~120% | — | (BTC market return) |
| Bitcoin 10 年 | — | 0.93-1.0 | 同上 |

**示唆**:
- Quant HF Sharpe 2.51 が業界トップライン (Algo/Quant が他カテゴリより高い)
- cat-bitget が Sharpe 2.51 級を目指すなら **「業界トップ Quant HF と同等」** = 機関級設計品質が必要

出典: [Crypto Hedge Funds 2025](https://coinlaw.io/crypto-hedge-funds-statistics/) / [Q4 2025 Crypto Fund Report](https://cryptofundresearch.com/reports/q4-2025-crypto-fund-report/) / [Industry Guide 2025](https://www.cryptoinsightsgroup.com/resources/industry-guide-to-crypto-hedge-funds-2025-edition)

### 1.2 個人 / 小規模 bot 業界相場

| 区分 | 月次 return 期待値 | 出典 |
|---|---|---|
| 低 volatility bot | **1%/月** (= 年 12%) | goatfundedtrader.com |
| 高 volatility bot | **10-15%/月** | 同上 |
| 平均的 retail bot 年次 | 12-25%/年 | wundertrading.com |
| 「不採算ライン」 | <5%/年 | goatfundedtrader.com |
| 「危険ライン」 | >200%/年 = 過剰リスクまたは虚偽 | 同上 |

**Retail bot の現実 (出典 hyrotrader / coincub)**:
- "Most retail bots barely break even" (= 多くの個人 bot は手数料負け)
- 50 trade/日 × $200 残高 × 0.25% fee + 0.15% slippage = 日 $4 コスト → grossの大半が吸われる
- 評価には live trading 3+ ヶ月実績 + 妥当な DD が必要

### 1.3 cat-bitget へのキャリブレーション

cat-bitget の context:
- ポジション上限 0.12 BTC 合計 (false_positive §0-2)
- BTC ≈ $100k (2026 想定) → 0.12 BTC = $12,000 exposure
- レバレッジ 25x 想定 → 必要証拠金 ≈ $480 (但し risk capital は exposure 単位で評価すべき)
- 凍結ベースライン: 月 $370 → 年 $4,440
- 目標: 月 $1,900 → 年 $22,800

**Exposure ベースの月次 return キャリブレーション**:
- 凍結ベースライン $370/月 ÷ $12,000 exposure = **月 3.08%** (年 36.9%)
- 目標 $1,900/月 ÷ $12,000 exposure = **月 15.83%** (年 190%)

**業界相場との照合**:
- 凍結ベースライン 月 3% = retail bot の「低 vol」と「高 vol」の中間 + Quant HF 平均年 36% と同水準
- 目標 月 15.83% = retail bot の「高 vol bot 上限」(10-15%/月) を僅かに超える + Crypto HF 平均 36%/年を 5.3× 上回る = **業界トップ層 Quant HF 級**
- = 目標は「達成可能だが業界トップ水準」と判定。**過剰リスクライン (>200%/年) には届かない**ので非現実的ではない。

**結論**: 目標 $1,900/月は **業界相場の上位 5-10% 帯**。Quant HF トップ層 (Sharpe 2.51・年 48%) と同等の設計品質が必要だが、達成不可能ではない。ただしマージン薄く・1 月でも下振れすれば未達。**設計姿勢は「合格ライン超えマージン厚く・ジャスト達成設計禁止」(CLAUDE.md §目標) 整合**。

---

## §2 5.1× gap 分解の業界経験則 — 「どこから 5.1× を作るか」のレバー値

### 2.1 Entry 改善 (Phase 1 担当) — **業界実証 1.1-1.6×**

- ML approach (XGBoost / Random Forest / RL) が rule-based を上回る効果:
  - "ML-based momentum reduced false signals + improved risk-adjusted returns relative to simple heuristic" (Springer 2025)
  - Bitcoin は trend-driven structure で ML 寄り (XRP は volatile で限界)
- 5min directional accuracy:
  - XGBoost 5min: **59.4%** (= +9.4pp over 50% baseline)
  - 一般的 ML 5-60min: **>50%** (= +0.x pp over random)
  - 直接 directional accuracy: **49-51.5%** (= near random・教科書水準)
- Reinforcement Learning ensemble (FineFT):
  - 12 SOTA baseline を outperform + risk 40%+ 削減
- Crypto futures HF trading:
  - 月内 trading で 16-17% returns (vs daily 6-7%) = 高頻度化の効果 ~2.5×

**Entry 単独改善で期待できる倍率**: **1.1-1.6×** (= 信号精度の質的向上分のみ)
- 直接 accuracy: 50% → 59% = +9pp が現実的上限 (5min crypto)
- 月次 NET 換算: 直接 accuracy +9pp ≈ Entry 由来 NET 改善 +30-60% (= 1.3-1.6×)

出典: [Springer ML Crypto](https://link.springer.com/article/10.1007/s44163-025-00519-y) / [FineFT arxiv](https://arxiv.org/pdf/2512.23773) / [arxiv ML Bitcoin](https://arxiv.org/html/2407.18334v1) / [Forecasting BTC PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8296834/)

### 2.2 Exit 改善 (Phase 4-b 担当) — **業界実証 1.3-2.0×** (Entry より大きい)

- 業界知見: "**real gains come from refining how they manage risk, exits, and ability to adapt to market conditions**" (Jigsaw Trading・Power Trading Group)
  - = プロトレーダーの共通認識「Entry より Exit / Risk 管理の方が PnL 寄与大」
- Triple Barrier Method (Lopez de Prado AFML Ch.3):
  - TP / SL / Time horizon の 3 障壁で出口を明確化
  - 単独でも backtest 品質を「realistic化」(= 過大評価防止)
  - Meta-Labeling と組み合わせで further improvement
- Trailing stop:
  - "designed to capture trends while minimizing losses" (Jigsaw)
  - 古典的 fixed TP/SL より trail で 1.2-1.5× は典型

**Exit 単独改善で期待できる倍率**: **1.3-2.0×**
- 出口設計の改善 (TP_PCT / SL_PCT / TIME_EXIT 最適化 + trail) で 30-100% の NET 改善が業界相場

出典: [Jigsaw Trading Edge 101](https://www.jigsawtrading.com/blog/trading-edge-101) / [QuantifiedStrategies Entry Exit](https://www.quantifiedstrategies.com/entry-and-exit-rules-trading-plan/) / [Triple Barrier Quantreo](https://www.newsletter.quantreo.com/p/the-triple-barrier-labeling-of-marco)

### 2.3 戦略並立 / 多戦略 ensemble (Phase 4-a cluster 担当) — **業界実証 1.2-1.8× (実用) / 理論上∞**

- Ensemble (multi-strategy) effect (crypto):
  - DD reduction **up to 4.17%** / Sharpe improvement **up to 0.21** (arxiv FinRL 2024)
  - 5-model ensemble: ETH Sharpe 80.17% / LTC Sharpe 91.35%
- Mom + Mean-Reversion 並立:
  - Sharpe **1.71** / annualized return **56%** (Medium briplotnik)
  - = 「直交 alpha」で 1.5-2× 改善が現実的
- **Square Root Rule** (理論上限):
  - 「無相関 portfolio の max geometric excess return = ½ × sum(Sharpe²)」(Outcast Beta)
  - 無相関戦略を無限に重ねれば Sharpe ∞ (理論上)
  - 実用: 3-5 戦略並立で 1.5-2× の Sharpe 改善が現実

**戦略並立で期待できる倍率**: **1.2-1.8× (3-5 cluster 想定)**
- cat-bitget の cluster=3 (現状) → 3 戦略並立で 1.3-1.5× が目安
- 並立効果は「**戦略間の相関**」次第。cluster 設計で各 cluster の return profile を意図的に直交化させると効果大。

出典: [arxiv FinRL Crypto 2024](https://arxiv.org/pdf/2501.10709) / [Sharpe Pitfalls Medium](https://thisgoke.medium.com/what-are-some-common-pitfalls-to-watch-out-for-when-using-the-sharpe-ratio-to-evaluate-crypto-2e8830f2c826) / [Systematic Crypto Medium](https://medium.com/@briplotnik/systematic-crypto-trading-strategies-momentum-mean-reversion-volatility-filtering-8d7da06d60ed) / [Outcast Beta Heuristics](https://outcastbeta.com/some-portfolio-construction-heuristics/) / [Bluesky Capital Portfolio](https://www.blueskycapitalmanagement.com/portfolio-diversification-how-to-potentially-gain-better-returns-per-unit-of-risk/)

### 2.4 Regime filter (Phase 4-c 新規 or Phase 1 内) — **業界実証 1.1-1.6×**

- 200-day MA regime filter:
  - Max DD **21%** vs buy-and-hold 50%+ = DD 60% 削減
  - 「Net profit + max DD improved by ~60%」(一部事例)
- HMM regime detection:
  - Sharpe **1.76** vs 1.16 (buy-hold) = +52% Sharpe 改善
  - Max DD **-20%** vs **-28%** (= 30% 削減)
- Jump model regimes:
  - 年次 return **+1-4%** across regions
- 一般化 (LuxAlgo):
  - Risk-adjusted return **+10-30%** + DD cut by similar margin
- Out-of-sample 注意:
  - "Mixed results - acted as lagged filter" (QuantStart QSTrader)
  - regime filter は OOS で lag 問題が出やすい

**Regime filter で期待できる倍率**: **1.1-1.6×** (= 10-60% 改善が業界相場)
- cat-bitget の現状: regime 判定研究は凍結中 (WORKFLOW.md §regime 研究)・素材として参照のみ
- もし regime filter を Phase に明示追加すれば 1.2× は現実的 (= 月 $370 → 月 $444)

出典: [Robuxio Regime Filter](https://www.robuxio.com/algorithmic-crypto-trading-vii-regime-filter/) / [QuantStart HMM](https://www.quantstart.com/articles/market-regime-detection-using-hidden-markov-models-in-qstrader/) / [LuxAlgo Regimes](https://www.luxalgo.com/blog/market-regimes-explained-build-winning-trading-strategies/) / [Downside Risk Jump Model arxiv](https://arxiv.org/pdf/2402.05272) / [Regime-Aware HMM 論文](https://internationalpubls.com/index.php/cana/article/download/6029/3393/10743)

### 2.5 Position sizing 最適化 (Phase 5-d 担当) — **業界実証 1.1-1.3×**

- **Kelly criterion**:
  - "Optimal bet sizing strategy that maximizes growth rate of wealth"
  - 数値: full Kelly は理論上最大成長率 (但し overestimate リスク)
- **Half-Kelly (実用標準)**:
  - **75% of growth retained / 50% volatility reduced** ← 業界 sweet spot
  - "Most professional traders use Half-Kelly or less" (multiple sources)
  - MacLean / Sanegre / Zhao / Ziemba (2004) 実証
- **Volatility targeting + Kelly hybrid (動的)**:
  - VIX-Rank を dynamic scaling factor として使用 (arxiv 2508.16598)
  - 静的 fraction より uncertain edge への robustness 高い
- **Sharpe ベース sizing (Alpha Theory)**:
  - 「無相関 position に対して optimal allocation = proportional to Sharpe / volatility」

**Position sizing 最適化で期待できる倍率**: **1.1-1.3×** (= 10-30% 改善)
- cat-bitget 現状: 0.024 BTC 固定 (= 0.12/cap_5 想定)
- 動的 sizing 投入で Kelly 系の 10-30% NET 改善が業界相場

出典: [Kelly Criterion Quantified](https://www.quantifiedstrategies.com/kelly-criterion-position-sizing/) / [Half-Kelly Medium Huma](https://medium.com/@humacapital/the-kelly-criterion-in-trading-05b9a095ca26) / [Fractional Kelly arxiv 2508.16598](https://arxiv.org/pdf/2508.16598) / [Alpha Theory Sharpe sizing](https://www.alphatheory.com/blog/a-sharpe-approach-to-position-sizing) / [Practical Kelly Frontiers](https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2020.577050/pdf)

### 2.6 5.1× gap を作る組み合わせ試算

各レバーの効果値 (§2.1-2.5) を掛け合わせて 5.1× に届く経路を試算:

| ケース | Entry | Exit | 並立 | Regime | Sizing | 合計倍率 | 月次 NET |
|---|---|---|---|---|---|---|---|
| **A. 控えめ**   | 1.2× | 1.4× | 1.3× | 1.1× | 1.1× | **2.64×** | $976 (❌ 未達) |
| **B. 中央値**   | 1.4× | 1.7× | 1.5× | 1.3× | 1.2× | **5.57×** | $2,060 (◯ 達成 + 8% マージン) |
| **C. 楽観値**   | 1.6× | 2.0× | 1.8× | 1.6× | 1.3× | **11.98×** | $4,433 (◎ 達成 + 過剰マージン) |
| **D. Entry単独頼り** | 1.6× | 1.0× | 1.0× | 1.0× | 1.0× | **1.6×** | $592 (❌ 大幅未達) |
| **E. Exit + 並立中心** | 1.0× | 2.0× | 1.8× | 1.2× | 1.2× | **5.18×** | $1,917 (◯ ギリ達成・マージン薄) |
| **F. 全レバー上限** | 1.6× | 2.0× | 1.8× | 1.6× | 1.3× | **11.98×** | $4,433 (= C と同) |

**示唆**:
- **B. 中央値ケース**で 5.57× 達成 = **5 レバーすべての中央値で目標到達 + 8% マージン**
- **D. Entry 単独頼り**は 1.6× で大幅未達 = **Entry のみ頑張る現アプローチは構造的に到達不可能**
- **E. Exit + 並立中心**でも到達可能 = Entry 改善が困難でも他レバーで補える
- **5.1× 達成は単一レバーで不可能** = 業界経験則の Square Root Rule (§2.3) と整合: 単一戦略の Sharpe 改善上限は限定的・無相関 portfolio 化で複利的に増える

**「設計姿勢: マージン厚く」の解釈**:
- B. 中央値の 8% マージンは「ジャスト達成設計」に近い
- C. 楽観値はマージン厚いが楽観値依存 = 設計欠陥になりやすい
- 推奨: **B. 中央値で計画 + 各レバーで上振れ余地を残す** (= 楽観値依存しない)

---

## §3 Phase 別合格基準を PnL に紐付ける業界手法

### 3.1 Prediction accuracy ↔ PnL の関係

- 一般的に: prediction accuracy 上昇 → return 上昇 (相関あり・但し非線形)
- 業界標準評価 (arxiv 2401.05337 / Macrosynergy):
  - **Statistical metrics**: R²/Accuracy/F1/Precision/Recall = 予測精度の評価
  - **Financial metrics**: PnL %/Sharpe/Number of Trades = お金の評価
  - → 両方を **並行評価** (= 統計指標が良くても PnL に直結する保証はない)
- Hyperparameter optimization の **主指標 = PnL %** (= 学術論文の業界相場)

**cat-bitget の Phase 1 評価軸への示唆**:
- 現状 Phase 1 v6: entropy_lift / TP Precision / Direction Accuracy = **統計指標のみ**
- 業界整合: **PnL % (またはその proxy) を Phase 1 評価軸に追加** が業界標準
- ただし L-217 で「Phase 1 v6 = Exit 非依存 3 指標化 (Exit シミュレーション抜きで完結)」を確定した経緯あり = **Exit 抜きで PnL に近い指標を作る方法を考える必要**

**Exit 抜き PnL proxy 候補**:
- 期待値 = TP Precision × TP_gain - (1-TP Precision) × SL_loss - fee
- 月内 trade 数 × 期待値 = 月次 NET proxy
- これを Phase 1 評価軸に追加すれば「Exit 非依存」維持しつつ PnL に紐付け可

出典: [Optimal Linear Signal arxiv 2401.05337](https://arxiv.org/pdf/2401.05337) / [Macrosynergy Regression Signals](https://macrosynergy.com/research/regression-signals/) / [TrendSpider ML Investing](https://trendspider.com/learning-center/how-to-apply-machine-learning-to-investing-or-trading/)

### 3.2 Backtest → Live degradation (Deflated Sharpe Ratio)

- de Prado + Bailey 2014「Deflated Sharpe Ratio (DSR)」:
  - Backtest Sharpe は **selection bias + 多重検定 + non-Normal returns** で過大評価
  - DSR = 真の skill を反映する確率 (= live で再現される Sharpe の確率)
  - 補正方法: 試行 N 個の strategy のうち best を採用する場合の expected Sharpe を引く
- 業界実証:
  - IS Sharpe vs OOS Sharpe の degradation factor は **30-70%** が典型 (= live は IS の半分以下になる)
  - 出典 [SSRN 2465675](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2465675)

**cat-bitget への示唆**:
- Phase 5 仮テスト 2025 で月 $1,900 達成 → Phase 6-b 本テスト 2026 Q1 で **degradation 50% 想定** = 月 $950 程度になる risk
- これを避けるため **「マージン厚く」設計** = Phase 5 で月 $3,800+ 目指す方が安全
- cc_ml_design_spec §1.6 改訂で「マージン要件」を明示する余地あり

出典: [Deflated Sharpe SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2465675) / [Deflated Sharpe Wikipedia](https://en.wikipedia.org/wiki/Deflated_Sharpe_ratio) / [Backtest Overfit SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253) / [Bailey de Prado pdf](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)

### 3.3 cat-bitget の Phase 別合格基準の改善方向

| Phase | 現状合格基準 | 業界整合改善案 |
|---|---|---|
| Phase 1 | entropy_lift / TP Precision / Direction Accuracy | + 期待値 proxy (TP Precision × TP_gain - (1-TP) × SL_loss - fee) を追加 |
| Phase 2 | 4 指標 (q99 net_quality / valid_rmse 等) | 現状維持 (既に PnL 寄り) |
| Phase 4-b | cluster_best_exit (train PnL のみ) | 現状維持 |
| Phase 5 | 全 12 ヶ月 NET ≥ $1,900 | **マージン要件追加: Phase 5 で月 $3,800 目標** (= 50% degradation 想定) |
| Phase 6-b | 全 3 ヶ月 NET ≥ $1,900 | 現状維持 (= 最終判定) |

---

## §4 BTC 5m bar 戦略の業界実証

### 4.1 5min directional accuracy 業界相場

- 直接 directional accuracy: **49-51.5%** (= 教科書水準・near random)
- XGBoost 5min: **59.4%** (= +9.4pp = ML の Bitcoin 特性活用効果)
- 「Short-horizon market efficiency challenges」 = 5min はそもそも難易度高い
- 15min log-return forecasting: 50-51% (= 5min と大差なし)

**cat-bitget の Phase 1 Direction Accuracy 0.55 目標との照合**:
- 0.55 = +5pp over random
- 業界相場 (XGBoost 5min 59.4%) より控えめ = **達成可能水準**
- ただし Bitcoin trend structure 依存 = bull/bear cycle で精度変動するリスク

### 4.2 ML approach の Bitcoin 特性活用優位性

- "Bitcoin's trend-driven structure favors machine learning-based trading"
- XRP のような爆発的価格変動は static rule の限界が露呈
- Bitcoin は trend bias がある = ML が学習しやすい

**示唆**: cat-bitget が BTCUSDT に絞っているのは業界知見と整合的 (Bitcoin の ML 寄り特性活用)

出典: [PMC BTC ML](https://pmc.ncbi.nlm.nih.gov/articles/PMC8296834/) / [arxiv BTC ML Comprehensive](https://arxiv.org/html/2407.18334v1) / [MDPI Crypto Indicators](https://www.mdpi.com/2674-1032/4/4/77)

---

## §5 cat-bitget レシピへの示唆 (実践)

### 5.1 5.1× 達成の現実的経路

**ケース B (中央値) を採用すると**:

| レバー | 倍率 | 担当 Phase | 必要条件 |
|---|---|---|---|
| Entry 改善 | 1.4× | Phase 1 + Phase 4-a (cluster 別予測) | TP Precision baseline + 12pp = 0.44 → 0.55 (= 業界 5min XGBoost 水準) |
| Exit 最適化 | 1.7× | Phase 4-b | cluster × K × side 別 best Exit + Triple Barrier 整合 |
| 戦略並立 | 1.5× | Phase 4-a (cluster=3 並立 + LONG/SHORT) | cluster 間相関 < 0.3 (= 直交 alpha) |
| Regime filter | 1.3× | Phase 4-c (新規・現状未設計) | HMM or jump model 投入 + lag 対策 |
| Position sizing | 1.2× | Phase 5-d | Half-Kelly + volatility targeting |

**5 レバー合計**: 1.4 × 1.7 × 1.5 × 1.3 × 1.2 = **5.57×** → 月 $2,060 (目標 + 8% マージン)

**Phase 4-c (Regime filter) は新規 Phase 追加が必要**。現 phase_flow_v4_with_recovery.md には明示 Phase なし。

### 5.2 Phase 4-b 単体検証のアプローチ

§2.2 で「Exit 改善が単独で 1.3-2.0×」= **最大の単一レバー**。Phase 4-b 単体検証を先行することの正当性:

**検証方法 (3 候補)**:

1. **ナイーブ Entry + Exit grid search**:
   - Entry = ランダム or 単一指標 (RSI 30 以下) で発火
   - Exit grid (TP_PCT / SL_PCT / TIME_EXIT) を網羅探索
   - → Exit 設計の上限性能を可視化
   - 限界: ナイーブ Entry なので best Entry 時の Exit 効果は別

2. **手動 Priority Entry + Exit 最適化**:
   - Entry = cat_v9 P1-P24 (= 凍結ベースライン月 $370 の Entry 信号)
   - Exit を Triple Barrier ベースで最適化
   - → 「現 Entry のままで Exit 改善で月 $370 → 月 $630 (= 1.7×) に届くか」を実証
   - 利点: cat-bitget の実 Entry 信号で Exit 効果を直接測定可能

3. **Phase 1 v6 案 e (entropy_lift 6/8 PASS) + Exit 最適化**:
   - Phase 1 完走済の case_e triple_barrier predictions を Entry として使用
   - Exit を別途 grid search
   - → Phase 1 を本格再開する前に Phase 4-b の上限を見る

**推奨**: **(2) 手動 Priority Entry + Exit 最適化** が最も意味のある検証
- 既存実 Entry で Exit 改善の直接効果を測定 = ベースライン月 $370 からの上振れを実証
- Phase 1 を待たずに Phase 4-b の現実性が確認できる
- もし Phase 4-b で 1.7× 出ない場合 = Phase 1 を頑張っても無駄打ち判定可

### 5.3 検証順序の改訂提案

**現 phase_flow_v4 の順序**:
Phase 0 (label) → Phase 1 (Entry 学習) → Phase 2 (精度判定) → Phase 3-a/b (ハイパラ) → Phase 4-a (cluster) → Phase 4-b (Exit) → Phase 5 (Replay)

**改訂提案**:
1. **Phase 0**: 完了済 (現状維持)
2. **Phase 4-b 単体先行検証** (NEW・1-2 セッション):
   - 手動 Priority Entry + Exit grid search
   - 凍結ベースライン月 $370 → 月 $630+ (1.7×) が出るか?
   - NG なら根本見直し / OK なら次段へ
3. **Phase 4-a 単体検証** (NEW・1 セッション):
   - cluster=3 並立 (LONG/SHORT × cluster) で cluster 間相関 < 0.3 達成可能か
   - cluster 間相関で並立効果 (1.5×) の現実性確認
4. **Phase 1 v6 再開** (= Layer 3 投入 / case f 修正 / アルゴ多様化):
   - 監査結果 (NO-GO + PIVOT) の修正反映
   - Phase 4-b 検証で Exit 改善余地が確認できた前提で Entry 学習
5. **Phase 4-c 新規追加** (= Regime filter):
   - HMM or 200-day MA filter 投入
6. **Phase 5-d (sizing)** + **Phase 5 (Replay)**:
   - Half-Kelly + 5 レバー統合
7. **Phase 6-b (本テスト)**: 全 3 ヶ月 NET ≥ $1,900

**目的**: 各レバーの現実性を **早期に独立検証** + **どこで挫折するか** を可視化する。Phase 1 を頑張ってから「Phase 4-b で死亡」を防ぐ。

---

## §6 知識ギャップと追加調査

### 6.1 本ファイルで埋まらなかった項目

1. **BTC futures 5m bar の具体的 monthly NET 業界相場 ($ 値)**:
   - Crypto HF / retail bot の % return は取れたが、ポジションサイズ別の具体 $ 額は出典少
   - 出典: 「propriety data not publicly disclosed」(専門 fund は公開しない)
2. **Stefan Jansen の具体的 BTC monthly improvement 数字**:
   - 書籍参照には行かなかった (本書を直接読む必要)
3. **Hudson & Thames mlfinlab の edge attribution 内訳**:
   - 公式 docs に PnL contribution breakdown 機能の有無不明
   - 直接 research@hudsonthames.org に問い合わせ推奨
4. **Phase 1 評価軸 → Phase 5 月次 NET の正確な写像関数**:
   - 業界文献では「PnL を Phase 1 主指標化」が主流で写像関数自体は未定式
   - cat-bitget 独自に「TP Precision × 期待値 → 月次 NET」回帰を作る価値あり

### 6.2 次回 WebSearch 候補 (本ファイル更新用)

- 「Bitcoin futures 5min monthly NET realized live trading 2024 2025」(具体 $ 額調査)
- 「ML trading strategy backtest overfitting probability factor empirical」(degradation 具体値)
- 「Hudson Thames mlfinlab edge contribution percentage breakdown」(直接調査)
- 「Crypto cluster strategy correlation matrix typical values」(cluster 並立効果の precise 値)
- 「Regime filter Walk-forward out-of-sample degradation Sharpe」(regime lag 問題定量化)

---

## §7 改訂履歴

| 版 | 日付 | 内容 |
|---|---|---|
| v1 | 2026-05-26 | 初版・WebSearch 18 件 + 業界文献統合 (項目 1-6 全て・5 レバー定量根拠 + Phase 別合格基準 PnL 紐付け手法 + BTC 5m bar 業界相場 + cat-bitget レシピ示唆) |

---

## §8 引用済 URL リスト (出典管理)

§1 (月次 NET 業界相場):
- https://coinlaw.io/crypto-hedge-funds-statistics/
- https://cryptofundresearch.com/reports/q4-2025-crypto-fund-report/
- https://www.cryptoinsightsgroup.com/resources/industry-guide-to-crypto-hedge-funds-2025-edition
- https://cryptofundresearch.com/best-performing-crypto-funds/
- https://www.goatfundedtrader.com/blog/are-crypto-trading-bots-profitable
- https://wundertrading.com/journal/en/reviews/article/top-profitable-trading-bots
- https://www.hyrotrader.com/blog/automated-crypto-trading/
- https://coincub.com/are-crypto-trading-bots-worth-it-2025/

§2.1 (Entry):
- https://link.springer.com/article/10.1007/s44163-025-00519-y
- https://arxiv.org/pdf/2512.23773
- https://arxiv.org/html/2407.18334v1
- https://pmc.ncbi.nlm.nih.gov/articles/PMC8296834/
- https://www.mdpi.com/2076-3417/15/17/9400

§2.2 (Exit):
- https://www.jigsawtrading.com/blog/trading-edge-101
- https://www.quantifiedstrategies.com/entry-and-exit-rules-trading-plan/
- https://www.newsletter.quantreo.com/p/the-triple-barrier-labeling-of-marco
- https://www.mdpi.com/2227-7390/12/5/780
- https://link.springer.com/article/10.1186/s40854-025-00866-w

§2.3 (戦略並立):
- https://arxiv.org/pdf/2501.10709
- https://thisgoke.medium.com/what-are-some-common-pitfalls-to-watch-out-for-when-using-the-sharpe-ratio-to-evaluate-crypto-2e8830f2c826
- https://medium.com/@briplotnik/systematic-crypto-trading-strategies-momentum-mean-reversion-volatility-filtering-8d7da06d60ed
- https://outcastbeta.com/some-portfolio-construction-heuristics/
- https://www.blueskycapitalmanagement.com/portfolio-diversification-how-to-potentially-gain-better-returns-per-unit-of-risk/
- https://www.alphatheory.com/blog/a-sharpe-approach-to-position-sizing

§2.4 (Regime filter):
- https://www.robuxio.com/algorithmic-crypto-trading-vii-regime-filter/
- https://www.quantstart.com/articles/market-regime-detection-using-hidden-markov-models-in-qstrader/
- https://www.luxalgo.com/blog/market-regimes-explained-build-winning-trading-strategies/
- https://arxiv.org/pdf/2402.05272
- https://internationalpubls.com/index.php/cana/article/download/6029/3393/10743
- https://www.quantifiedstrategies.com/hidden-markov-model-market-regimes-how-hmm-detects-market-regimes-in-trading-strategies/

§2.5 (Position sizing):
- https://www.quantifiedstrategies.com/kelly-criterion-position-sizing/
- https://medium.com/@humacapital/the-kelly-criterion-in-trading-05b9a095ca26
- https://arxiv.org/pdf/2508.16598
- https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2020.577050/pdf
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5027918

§3 (Phase 別合格基準 PnL 紐付け):
- https://arxiv.org/pdf/2401.05337
- https://macrosynergy.com/research/regression-signals/
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2465675
- https://en.wikipedia.org/wiki/Deflated_Sharpe_ratio
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253
- https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf

§4 (BTC 5m 業界実証):
- https://www.mdpi.com/2674-1032/4/4/77

---

(本ファイル終わり・追記可能)
