# cc_entry_logic_self_study.md — CC エントリーロジック自己学習資料 v6

作成: 2026-05-25 (CC・v1) / 改訂 2026-05-27 (v2) / 改訂 2026-05-25 (v3) / 改訂 2026-05-25 (v4) / 改訂 2026-05-25 (v5) / 改訂 2026-05-25 (v6)
位置付け: まこさん命令 (2026-05-25) 「指標、閾値、時間の使い方を勉強しなおして」を受けた CC の学習資料。
状態: **🎉 v6 (= 領域 1-7 完成・案 B 学習 100% 完了)**。WORKFLOW 改訂39 active 優先 2 = 案 B 学習継続 = 領域 7 (監視運用) を v6 §20 として追加。WebSearch 12 件 + River (= scikit-multiflow + creme 統合) + scikit-multiflow ADWIN/DDM/EDDM/KSWIN + Page-Hinkley + Incremental LightGBM/XGBoost + Multi-Armed Bandit + Thompson Sampling (arxiv 1111.1797 + 1911.05309 Adaptive Portfolio + 2108.06812 Batched) + Contextual Bandit LinUCB (arxiv 1305.2415 + 1902.07802 AdaLinUCB) + Shadow deployment (SE-ML + AWS SageMaker + JFrog Qwak + Dataconomy 2025) + Champion-Challenger (DataRobot + H2O MLOps + Snowflake) + Production ML Monitoring 3 階層 (Galileo + Durapid + Fiddler + Monte Carlo + KDnuggets) + crypto online learning (arxiv 2510.08068 Multi-Agent Bitcoin + 2201.04699 Recurrent RL + 2303.07925 Deep Incremental Financial) + Hudson & Thames mlfinlab 引用。**案 B (= ChatGPT 7 工程フレーム範囲の ML 知識 7 領域カタログ化) 完了 = 次フェーズ = 工程 2-7 詳細詰め (= 設計確定) に進む準備完了**。

---

## §0 本ファイルの目的と位置付け

### 0.1 なぜ作ったか

2026-05-25 セッションで、CC が以下の事案を起こした:

- Phase 1 v6 6 案 (a〜f) を業界標準 (= regime 情報・mean reversion 系・MTF 整合・出来高系・板情報系) を verify せずに設計・実行 → 全案 TP precision 0.43 で頭打ち
- まこさん指摘「学習内容の手数はこれだけあるのにタイミングを判定するための学習方法が支離滅裂」
- 「手動ロジックにも劣っている君のテクニカル手法に対する理解度は大きな問題」
- 「指標、閾値、時間の使い方を勉強しなおして」(命令)

CC のテクニカル理解度が低い (= 既存 [technical_analysis_knowledge_base.md](technical_analysis_knowledge_base.md) §0.3 「CC の業界知識レベル正直版」と整合) ことが ML 設計の根本欠陥の原因。学習材料として、旧 Priority の閾値・組合せが業界標準とどう対応するかを WebSearch + 実装 verify で整理した。

### 0.2 既存資料との分担

- [technical_analysis_knowledge_base.md](technical_analysis_knowledge_base.md) (v2・1691 行): 指標辞典 + 閾値理論 + MTF 理論 (汎用)
- **本ファイル**: 旧 Priority P1-P25 の閾値・組合せの**業界標準対比による具体分析** (旧 Priority 特化)

### 0.3 重要前提 ([feedback_priority_starting_line_only.md](../../../../../.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_priority_starting_line_only.md) 整合)

旧 Priority は**テクニカル分析全体の最小単位 = スタートライン**。本ファイルでの分析は「学習材料」「事例研究」目的であって、ML 設計のベース・素材として扱うものではない。

---

## §1 ADX 閾値の業界標準と旧 Priority

### 1.1 業界標準 (Wilder 原典 + 業界実用)

| ADX 値 | 業界解釈 |
|---|---|
| < 20 | トレンドなし・コンソリデーション |
| 20-25 | **グレーゾーン** (トレンド形成中だが未確認) |
| > 25 | 強トレンド (Wilder 標準) |
| > 50 | 非常に強いトレンド (消耗近い・反転リスク) |

- 14 期間がデフォルト (Wilder 原典)
- ADX は非方向指標 (= 強さのみ・方向は +DI / -DI で判定)
- 主用途: trending vs consolidation の判別 (= トレンドフォロー戦略の有効性確認)

出典: [Welles Wilder ADX 解説 ChartSchool](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx) / [ADX グレーゾーン解説 (heygotrade)](https://www.heygotrade.com/en/blog/average-directional-index-adx/)

### 1.2 旧 Priority の対応分析

| Priority | ADX 閾値 | 業界整合判定 |
|---|---|---|
| P1 LONG | ≥ 30 | 業界整合 (= 25 より厳しい強トレンド要求・スキャルで方向性確実な場面のみ) |
| P2 LONG | 30-50 | 業界整合 (= 強トレンド範囲・50 超で消耗近いため除外は Wilder 警告と整合) |
| P3 LONG | 30-50 | 業界整合 (= P2 と同範囲・bb_mid_slope と組合せでさらに精度上げ) |
| **P4 LONG** | 20-25 **除外帯** | **業界整合・賢い設計** (= グレーゾーン除外は Wilder 概念と整合) |
| P21 SHORT | ≥ 22 | 業界整合の境界 (= グレーゾーン下端・スキャルで早めの entry 許容) |
| P22 SHORT | ≥ 22 | 同上 |
| P23 SHORT | 30-50 | P3 のミラー・業界整合 |
| P25 SHORT | ≥ 25 (+ スパイク+5) | 業界整合 (= 25 標準 + スパイク条件で「トレンド開始時」捕捉) |

**CC 学習成果**: P4 の「ADX 20-25 除外帯」は Wilder のグレーゾーン概念を実装に落とし込んだ賢い設計。CC は ML 設計で「ADX グレーゾーン除外」を業界整合の手法として採用すべき。

---

## §2 Stochastic Oscillator の閾値と旧 Priority

### 2.1 業界標準

| 閾値 | 業界解釈 |
|---|---|
| < 20 | オーバーソールド (買い候補) |
| > 80 | オーバーボウト (売り候補) |
| %K %D クロス | エントリーシグナル (= ゴールデンクロス / デッドクロス) |

- 強トレンド中はクロスシグナルの信頼性低・コンソリデーション中の方が信頼性高い
- **「gap (%K - %D の差) > 0.3」のような特定数値閾値は業界標準で明示されていない** (= CC 検索範囲)

出典: [Stochastic Oscillator OANDA 解説](https://www.oanda.com/sg-en/trading/learn/indicators-oscillators/stochastic-oscillator/) / [Fast Stochastic Fidelity](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/fast-stochastic)

### 2.2 旧 Priority の対応分析

| Priority | Stoch 条件 | 業界整合判定 |
|---|---|---|
| P2 LONG | ゴールデンクロス + gap > 0.3 + STOCH_K ≥ 0 | 部分整合 (= クロス自体は業界標準・gap > 0.3 は経験則) |
| P3 LONG | ゴールデンクロス + gap > 0.3 | 同上 |
| P23 SHORT | デッドクロス + gap > 0.3 | 同上 |

**CC 学習成果**: 「gap > 0.3」は業界標準でなく旧 Priority 独自の経験則。クロスの「確度フィルタ」として機能する設計意図と推測されるが、業界文献での裏付けはない。ML 設計時に「gap 閾値」を業界標準として扱うのは誤り。

---

## §3 Bollinger Band 中央線の傾きと旧 Priority

### 3.1 業界標準

| 状態 | 業界解釈 |
|---|---|
| 中央線が上向き + 価格が中央線上 | 上昇トレンド |
| 中央線が下向き + 価格が中央線下 | 下降トレンド |
| バンド幅拡大 | トレンド継続 |
| バンド幅収縮 | 反転示唆 |
| 中央線クロス | トレンド変化シグナル |

- 中央線は dynamic support/resistance として機能
- 反転シグナル精度 55-65% / 継続シグナル精度 60-70%

出典: [Bollinger Bands ChartSchool](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/bollinger-bands) / [Bollinger Bands FBS](https://fbs.com/fbs-academy/trading-tutorials/trading-handbook/the-bollinger-bands-indicator)

### 3.2 旧 Priority の対応分析

| Priority | bb_mid_slope 閾値 | 業界整合判定 |
|---|---|---|
| P3 LONG | > 10 | 部分整合 (= 上向き継続性確認は業界標準・絶対値 10 は経験則) |
| P4 LONG | ≥ 20 + 5 本平均 ≥ 15 | 部分整合 (= P3 より厳しい継続性 + 短期一貫性も確認・絶対値は経験則) |
| P22 SHORT | ≤ -20 | 同上 (= 下降側の強い継続性) |
| P23 SHORT | < -10 | 同上 |
| P24 SHORT | < 50 (ゆるい上限) | 弱い条件 (= 戻り売りで上昇 regime でも発火可能設計) |
| P25 SHORT | < 0 | 単純な方向確認 |

**CC 学習成果**: 中央線の傾き使用は業界標準と整合。ただし「絶対値閾値 (10/20/50)」は旧 Priority 独自の経験則であって、業界文献では「方向確認」のみが標準・具体的数値閾値は規定されていない。閾値の数値選定根拠は経験則で、業界標準と称することはできない。

---

## §4 ATR 閾値の業界標準と旧 Priority

### 4.1 業界標準 (クリプト 5 分足)

| 用途 | 業界推奨値 |
|---|---|
| ATR 期間 (5 分スキャル) | 5-10 期間 (デフォルト 14 より短め) |
| Stop-loss 倍率 | ATR × 1.5-2.0 |
| Breakout 検出 | ATR × 1.5 や 2 を超えた値動き |
| ボラフィルタ | ATR % で閾値設定 (絶対値より相対値推奨) |

- クリプトは高ボラのため大きめの倍率が必要
- **重要**: 業界標準は「ATR の**倍率**」(= 相対値) で使う。旧 Priority のような「絶対値 USD」での閾値は業界では非標準

出典: [ATR Mudrex Crypto Guide](https://mudrex.com/learn/average-true-range-crypto/) / [ATR 5 minute settings (atrindicator.com)](https://atrindicator.com/atr-settings-5-minute-chart/)

### 4.2 旧 Priority の対応分析

| Priority | ATR 閾値 | 業界整合判定 |
|---|---|---|
| P1 LONG | 60-9999 USD | 業界相違 (= USD 絶対値・業界は倍率・% 推奨) |
| P2 LONG | 100-300 USD | 業界相違 (同上・範囲指定で過剰ボラ除外は良いアイデアだが絶対値は問題) |
| P3 LONG | ≥ 250 USD | 業界相違 (同上) |
| P4 LONG | ≥ 200 USD | 業界相違 (同上) |
| P21 SHORT | ≥ 150 USD | 業界相違 (同上) |
| P22 SHORT | (BB width 上限のみ) | — |
| P23 SHORT | ≥ 150 USD | 業界相違 (同上) |
| P24 SHORT | ≥ 30 USD | 業界相違 (同上・かなり緩い閾値) |
| P25 SHORT | — | — |

**CC 学習成果**: 旧 Priority の ATR 閾値は**全部 USD 絶対値ベース**。BTC 価格が学習時 ($30k-$60k) と本番 ($100k-$150k) で乖離すると、絶対値 60 USD の意味が大きく変わる (= 価格非依存性違反の構造的問題)。これは既に lessons L-181 (= 価格非依存性違反問題) で認識されているはず。ML 設計時は ATR % か倍率で表現すべき。

---

## §5 RSI 閾値の業界標準と旧 Priority

### 5.1 業界標準 (BTC 含む)

| 値 | 業界解釈 |
|---|---|
| < 30 | オーバーソールド (買い候補) |
| > 70 | オーバーボウト (売り候補) |
| 50 | 中点 (= 上昇 vs 下降の境界) |
| > 85 / < 25 | 極値 (= 短期反転の前兆) |
| 強気相場の BTC | RSI 70 を週・月維持あり (= 売りシグナルとして使えない場面) |

- BTC では RSI が標準より幅広い範囲 (= 40-90) で変動することが多い
- 反転シグナルは 70/30 標準が広く使われるが、強いトレンドでは継続性も高い

出典: [BTC RSI usethebitcoin](https://usethebitcoin.com/guides/bitcoin-rsi-current-value/) / [RSI Crypto Guide DEXTools](https://www.dextools.io/tutorials/what-is-rsi-crypto-trading-technical-analysis-guide-2026)

### 5.2 旧 Priority の対応分析

| Priority | RSI 閾値 | 業界整合判定 |
|---|---|---|
| P2 LONG | ≥ 45 | 業界整合 (= 50 中点付近で上昇方向確認・55 を要求しないのは控えめだが妥当) |
| P4 LONG | ≤ 60 | 業界整合 (= 過熱前の押し目買い・70 直前を避ける設計) |
| P22 SHORT | (RCI 使用・直接 RSI 閾値なし) | — |
| P24 SHORT | > 65 | **業界標準より早め** (= 標準 70 より 5pp 早く過熱判定・早期反転狙い) |

**CC 学習成果**: P24 の「RSI > 65 で過熱判定」は業界標準 (70) より早めの設計。BTC では強気相場で 70 を維持することがあるので、70 で売っても続伸して負ける可能性がある。65 で早めに反転狙いするのは「強気相場での誤判定リスク」と「早期反転捕捉」のトレードオフ。経験則ベースの設計意図と推測される。

---

## §6 MACD 設定の業界標準と旧 Priority

### 6.1 業界標準 (5 分スキャル)

| 設定 | 業界推奨 |
|---|---|
| 標準 (12, 26, 9) | 日足・週足向け |
| **5 分スキャル推奨** | (5, 13, 4) や (5, 13, 1) や (3, 10, 1) |
| 検証強化 | クロス + ヒストグラム + 出来高 + candlestick patterns |
| 単独 entry | 信頼性低 (= 業界推奨外) |

- MACD は「遅行指標」(= クロス時点で既に動き始め)
- 単独 entry は失敗多・必ず別指標と組合せ

出典: [MACD 5 minute settings MC² Finance](https://www.mc2.fi/blog/best-macd-settings-for-5-minutes-chart) / [MACD OANDA Guide](https://www.oanda.com/us-en/learn/indicators-oscillators/determining-entry-and-exit-points-with-macd/)

### 6.2 旧 Priority の対応分析

| Priority | MACD 設定 | 業界整合判定 |
|---|---|---|
| P1 LONG | (12, 26, 9) ゴールデンクロス | **業界相違** (= 5 分スキャルには遅すぎ・推奨は (5,13,4)) |
| P21 SHORT | (12, 26, 9) デッドクロス | 同上 |

**CC 学習成果**: 旧 Priority の P1/P21 は MACD 標準設定 (12,26,9) を 5 分足で使用。業界の 5 分スキャル推奨設定 (5,13,4) と乖離。標準設定は反応が遅く、5 分スキャルで使うと entry タイミングが遅れる構造的問題。ただし P1/P21 は ADX/ATR の追加フィルタで「遅さ」を補っている可能性あり。ML 設計時は MACD を採用するなら 5 分スキャル推奨設定を検討すべき。

---

## §7 多指標 AND 組合せの深さと旧 Priority

### 7.1 業界標準

| 組合せ深さ | 業界評価 |
|---|---|
| 1-2 指標 | ノイズ多・偽シグナル多 |
| **3-5 指標** | **最適バランス** (= 信頼性 vs 取引機会) |
| 6+ 指標 | 取引機会激減・過剰適合リスク |

- 「多数決」アプローチ (= 5 指標中 3 以上が同方向で entry) が業界推奨
- 別カテゴリの指標を組合せる方が効果的 (= モメンタム + ボラ + トレンド)

出典: [Multi-Indicator Confirmation FMZQuant](https://medium.com/@FMZQuant/multi-indicator-trend-confirmation-trading-strategy-b2a7e69dbccd) / [Combining Indicators CryptoHopper](https://www.cryptohopper.com/blog/trading-101-combining-technical-indicators-173)

### 7.2 旧 Priority の対応分析

| Priority | AND 段数 | 内訳 | 業界整合判定 |
|---|---|---|---|
| P1 LONG | 4 段 | MACD クロス + ADX + ATR 下限 + ATR 上限 | 業界整合 (3-5 範囲) |
| P2 LONG | 7 段 | stoch クロス + gap + STOCH_K + ADX + RSI + ATR 範囲 + ADX 除外帯 | 業界上限 (6+ で取引機会減リスク) |
| P3 LONG | 6 段 | stoch クロス + gap + bb_mid_slope + ADX 範囲 + ATR + 陽線 | 業界整合上限 |
| P4 LONG | 7+ 段 | pullback + 陽線 + bb_mid_slope + 5 本平均 + RSI + ATR + ADX 除外 + entry_ok | 業界上限超 (= 取引機会激減リスク) |
| P21 SHORT | 4 段 | MACD クロス + ADX + ATR | 業界整合 |
| P22 SHORT | 6 段 | RCI 反転 + BB 上限 + bb_mid_slope + 陰線 + ADX + bb_width 制限 | 業界整合 |
| P23 SHORT | 7 段 | stoch クロス + gap + stoch_k 制限 + bb_mid_slope + ADX 範囲 + ATR + High_ADX 条件 | 業界整合上限 |
| P24 SHORT | 6 段 | RSI > 65 + RSI slope + bb_mid_slope + stoch_k + 陰線 + ATR | 業界整合 |
| P25 SHORT | 4 段 | ADX スパイク + ADX 下限 + bb_mid_slope + 陰線 | 業界整合 |

**CC 学習成果**: 旧 Priority の組合せ深さ (4-7 段) は業界推奨範囲 (3-5 段) の上端付近。P2/P4 は 7 段で取引機会減リスクがあるが、これは「品質重視・量より精度」の設計判断と推測される。ML 設計時も同様の組合せ深さ (4-6 段) が業界整合的。

---

## §8 マルチタイムフレーム (MTF) 整合と旧 Priority

### 8.1 業界標準

| 階層 | 用途 | 時間軸例 |
|---|---|---|
| 大局 (Higher) | regime / context 確認 | 1d / 1w |
| 中位 (Working) | setup zone 定義 | 1h / 4h |
| 下位 (Entry) | 実 entry タイミング | 5m / 15m |

- BTC 5 分 bot では **4h を中位足の中心**に置くのが業界標準
- **confluence** (= 複数足が同方向に整合) で勝率激増
- 単一足のみの判定は「偽シグナル 80% をフィルタする機会を逃す」

出典: [Multi-Timeframe Analysis BingX](https://bingx.com/en/learn/article/how-to-use-multiple-timeframe-analysis-for-better-entry-and-exit-points-in-crypto-trading) / [MTF QuantPedia](https://quantpedia.com/how-to-design-a-simple-multi-timeframe-trend-strategy-on-bitcoin/) / [LuxAlgo MTF Guide](https://www.luxalgo.com/blog/5-steps-to-confirm-entries-with-multi-timeframes/)

### 8.2 旧 Priority の対応分析

| Priority | MTF 整合 | 業界整合判定 |
|---|---|---|
| P1-P25 全て | 5 分足単独判定 | **業界相違 (重大欠落)** |

**CC 学習成果 (重要)**: 旧 Priority は**全 9 種が 5 分足単独判定**で、上位足 (1h / 4h / 1d) の整合確認が完全欠落。業界標準の MTF 整合 (= 偽シグナル 80% フィルタ) を使っていない。これは旧 Priority の最大の構造的欠陥で、ML 設計で MTF 整合を入れることが「最小単位を超える設計」の中核となる。

---

## §9 旧 Priority 全体構造の業界整合判定 (サマリ)

| 項目 | 旧 Priority の状態 | 業界整合判定 |
|---|---|---|
| ADX 閾値 (25/30/50/グレーゾーン除外) | Wilder 標準と概ね整合 | ✅ 整合 |
| AND 組合せ深さ (4-7 段) | 業界推奨 (3-5 段) の上端 | ✅ 整合 |
| RSI 過熱閾値 (65・標準より早め) | 経験則ベースの早期反転狙い | ⚠️ 経験則 |
| Stochastic gap > 0.3 | 業界標準なし・経験則 | ⚠️ 経験則 |
| BB 中央線傾き絶対値 (10/20) | 業界は方向確認・絶対値は経験則 | ⚠️ 経験則 |
| MACD 設定 (12,26,9 を 5 分で使用) | 5 分スキャル推奨 (5,13,4) と乖離 | ❌ 業界相違 |
| ATR 閾値 (USD 絶対値) | 業界は倍率・% 推奨 | ❌ 業界相違 (価格依存) |
| MTF 整合 | 5 分単独判定・上位足確認なし | ❌ 重大欠落 |

### 9.1 旧 Priority のカバー範囲 (テクニカル全体に対する位置)

| カテゴリ | 旧 Priority のカバー | カバー率 |
|---|---|---:|
| トレンドフォロー (MA / MACD / ADX) | P1, P21 (スキャル) / P2, P3, P23 (トレンド追随) | ◯ |
| 押し目買い / 戻り売り | P4 (押し目買い) / P22, P24 (戻り売り) | ◯ |
| ブレイクアウト | P25 (ADX スパイク) のみ・range breakout なし | △ |
| Mean Reversion (= 逆張り) | P22 の BB upper touch のみ・体系的でない | △ |
| 出来高系 (OBV / VWAP / Volume Profile) | **ゼロ** | ❌ |
| パターン認識 (candlestick / chart) | **ゼロ** | ❌ |
| 板情報系 (spread / imbalance / taker ratio) | **ゼロ** | ❌ |
| MTF 整合 | **ゼロ** | ❌ |

→ 8 カテゴリ中 3.5 カテゴリ (= 約 40-45%) のみ部分使用 = まこさん指摘「テクニカル全体のごく一部 = 最小単位」を業界カテゴリ網羅率で verify。

---

## §10 CC の理解度更新サマリ

### 10.1 学習した内容 (本ファイル §1-9)
- ADX/RSI/Stochastic/Bollinger Band/ATR/MACD の業界標準閾値と用法
- 多指標 AND 組合せの推奨深さ (3-5 段)
- MTF 整合の業界標準フロー (大局 1d/1w + 中位 1h/4h + entry 5m)
- 旧 Priority と業界標準の整合点・乖離点

### 10.2 認識訂正 (本ファイル作成で気づいた間違い)

- CC は今まで「旧 Priority = テクニカル業界標準の実装」と暗黙に扱っていたが、実際は「業界整合 + 経験則 + 業界相違」のハイブリッド
- ATR 閾値の絶対値ベース・MTF 整合欠落・MACD 設定の不一致は明確な業界相違
- 旧 Priority のカバー範囲は業界 8 カテゴリ中 約 40-45% (= 「最小単位」が業界カテゴリ網羅率で verify された)

### 10.3 今後の追加学習必要領域 (= 旧 Priority がカバーしていない領域)

1. **出来高系**: OBV / VWAP / Volume Profile / volume surge の業界使用法
2. **パターン認識**: candlestick patterns / chart patterns / harmonic patterns
3. **板情報系**: spread / imbalance / taker ratio / order flow
4. **Mean Reversion 系の体系**: BB タッチ反転 / VWAP 乖離回帰 / Z-score
5. **MTF 整合システムの実装**: 4h regime + 1h setup + 5m entry の組合せ設計

これらを次の段階で WebSearch + 教科書引用で追加学習し、本ファイル v2 以降に追記する。

---

## §13 ML 学習方法 (WORKFLOW 改訂35 領域 1・業界アルゴリズムカタログ)

> v2 追記 (2026-05-27)。ChatGPT 7 工程フレームの工程 3 (Entry ML) / 工程 5 (Exit ML) / 工程 4 (Position Sizing) の **アルゴリズム選定** に直接効く知識。Phase 1 v6 案 a-f (= GBDT 系のみ) が頭打ちした原因の 1 つは「アルゴリズムの多様性不足」も含まれるため、業界カタログ全体を整理する。

### §13.1 GBDT 系 (LightGBM / XGBoost / CatBoost)

#### 業界用途と差分

| アルゴ | 強み | 弱み | cat-bitget Phase 1 v6 採用状況 |
|---|---|---|---|
| **LightGBM** | 訓練速度最速・低メモリ・大規模対応 | 浅い木で過学習傾向 | ✅ 案 a-f 全案で使用 |
| **XGBoost** | 正則化強い・Sharpe / DD が LightGBM より優位 (momentum 比較) | 訓練速度やや遅・メモリ消費大 | ❌ 未使用 |
| **CatBoost** | カテゴリ特徴量を自前処理 (= one-hot 不要)・過学習防止強 | 数値特徴量主体だと旨味少ない | ❌ 未使用 |

#### 教科書整合 + 出典

- Lopez de Prado AFML **Ch.6 Ensemble Methods**: bagging (= bootstrap aggregating・複数サンプルで variance 低減) と boosting (= 逐次的に弱学習器の誤差を補正・bias 低減) の使い分け。
- LightGBM vs XGBoost の momentum 戦略比較 ([Data Moves Me](https://www.datamovesme.com/blog/what-happens-when-you-swap-out-xgboost-a-6model-momentum-showdown)): CAGR / total return は同等だが、Sharpe は XGBoost 優位・max DD は XGBoost が浅い。

#### Phase 1 v6 6 案全滅との関係 (cc_entry_logic_self_study §0.1 経緯)

- 案 a-f は **全て LightGBM** で実装。アルゴリズム多様性ゼロ。
- 「ボラ予測 ML 設計欠陥」の根本原因は regime context 不在 / LONG-SHORT 並列学習だが、アルゴリズム多様性 (= XGBoost / CatBoost 並走) も Phase 1 v6 では未試行。
- 業界実証として XGBoost + LightGBM のアンサンブルは「単独アルゴより drawdown 浅い」事例が多い (AFML Ch.6)。

#### cat-bitget 適用判断 (= 工程 3 候補)

- **工程 3 (Entry ML) のメインアルゴ候補**: LightGBM (高速・大規模対応) + XGBoost (Sharpe 優位) のアンサンブル
- **CatBoost は保留**: cat-bitget は数値特徴量主体 (= 1432 指標) でカテゴリ特徴量少ない → CatBoost の旨味が薄い
- **Hyperparameter range の業界相場** (= AFML / mlfinlab blog 整合):
  - `num_leaves`: 15-127 (= cat-bitget Phase 1 v6 は 15-31 中心)
  - `learning_rate`: 0.01-0.1
  - `min_child_samples`: 20-100
  - `early_stopping_rounds`: 50-200

### §13.2 時系列深層学習 (LSTM / GRU / Transformer / TCN)

#### 業界用途と業界実証

| アルゴ | 強み | 弱み | BTC 5m 業界実証 |
|---|---|---|---|
| **LSTM** | 長期依存性捕捉・時系列定番 | 訓練遅・データ要求大 | MSE 6.25 (GRU より悪) |
| **GRU** | LSTM より高速・パラメータ少 | 長期依存性で LSTM に劣る場合あり | MSE 4.67 (LSTM 超え) |
| **Transformer** | Attention で long-range pattern 捕捉 | データ要求さらに大・計算重 | TimeXer-Exog で MSE 89% 改善 (70日 horizon) |
| **TCN** (Temporal Convolutional Network) | RNN より並列化容易 | Bitcoin での実証研究少 | 限定的 |

#### 業界研究 (2025)

- **GRU > LSTM (Bitcoin daily)**: [Springer 2025](https://link.springer.com/chapter/10.1007/978-981-97-8946-7_13) GRU MSE 4.67 vs LSTM 6.25 / 2 層 + Adam + dropout 0.2 + batch 32 + 20 epochs。
- **Transformer**: [TimeXer / EMAT / TFT](https://www.mdpi.com/2079-8954/13/6/474) on-chain + テクニカル指標統合で BTC 予測 / [Bitcoin Greed Index 組合せ](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/blc2.70017) で性能向上。
- **Hybrid (Transformer + GRU)**: [arxiv 2504.17079](https://arxiv.org/pdf/2504.17079) で long-range + short-term の両方捕捉。

#### Overfitting 対策 (業界標準)

- Dropout 0.2 (= 訓練時に 20% neuron をランダム無効化)
- L2 正則化 (= 重みの 2 乗ペナルティ)
- 5-fold cross validation (Walk-Forward / Purged が時系列推奨)

#### cat-bitget 適用判断 (= 工程 3 / 工程 5 候補)

- **データ量**: 5y × 5m × 24h × 12 = **525,600 bar** = 深層学習に十分 (Transformer は 100k+ で安定)
- **業界研究の限界**: BTC 研究は daily / hourly 中心で **5min intraday の業界実証は少ない** → cat-bitget で先行ケースになる可能性
- **採用候補**: 工程 3 のセカンダリ (= GBDT と並走) で GRU / Transformer (TFT) を試す。工程 5 (Exit ML) でも LSTM/Transformer は dynamic exit timing で実証あり (§14.7 参照)
- **見送り**: TCN は BTC 研究蓄積が薄いため保留

### §13.3 時系列特化 ML (MiniROCKET / TSFresh / sktime)

#### 業界用途と特徴

| アルゴ | 用途 | 業界実証 |
|---|---|---|
| **MiniROCKET** | 時系列分類の SOTA (= state-of-the-art・最新最良) | UCR 108 datasets で ROCKET の 75x 高速・accuracy 同等 / 109 datasets を 10 分以内で訓練・テスト |
| **TSFresh** | 自動特徴量抽出 (794 features・63 methods) | 統計的 hypothesis test ベース feature selection 内蔵 |
| **TSFEL** | TSFresh と並ぶ自動特徴量ライブラリ | finance / healthcare で実証 |

#### 教科書整合 + 出典

- **MiniROCKET 原論文**: [arxiv 2012.08791](https://arxiv.org/abs/2012.08791) / [GitHub angus924](https://github.com/angus924/minirocket) — random convolutional kernel で時系列を transform して linear classifier で分類
- **TSFresh 原論文**: [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0925231218304843) / [GitHub blue-yonder](https://github.com/blue-yonder/tsfresh) — Scalable Hypothesis tests で自動特徴量選択

#### cat-bitget 適用判断 (= 工程 3 / 特徴量設計補強)

- **MiniROCKET**: 工程 3 (Entry ML) のセカンダリ候補。GBDT / Transformer と並走して時系列分類タスクとして Entry 候補を分類。BTC 5m 業界実証は薄いが、UCR データセット全般で SOTA = crypto でも有望
- **TSFresh**: cat-bitget の既存 1432 指標を補完する自動特徴量抽出として併用候補。**ただし leak チェック (= shift(-N) / future window) 必須** (feedback_ml_leak_mandatory_check.md)。794 features の中に未来参照が混入していないか実装 verify が義務
- **採用優先度**: TSFresh 中 / MiniROCKET 中の保留 (= 工程 2-7 詳細詰めで再評価)

### §13.4 強化学習 (RL: DQN / PPO / A2C / SAC)

#### 業界用途と性能 (2025 実証)

| アルゴ | 業界実証 (crypto 2025) | 用途 |
|---|---|---|
| **DQN** | 限定・離散行動向け | Entry 方向の binary 判定 |
| **PPO** | **2025 最多採用** (general-purpose) / 78% success rate (risk control・LSTM 28% 比較) | Position sizing / 連続行動 |
| **A2C** | PPO の代替 | 連続行動 |
| **SAC** | extreme vol で **94% annualized return** (DQN -12% 比較) | 高ボラ環境 |

#### 教科書整合 + 出典

- **PPO 適用例**: [SSRN paper](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5662930) BTC/ETH/SPY で long/flat/short positioning 学習 / transaction cost + vol risk penalty
- **比較研究**: [MDPI Systems 14-1-111](https://www.mdpi.com/2079-8954/14/1/111) PPO / A2C / DQN の attention layer 付き比較
- **Exit timing / Position sizing 適用**: LSTM / PPO / DQN / Actor-Critic で SL/TP 学習 + risk control

#### cat-bitget 適用判断 (= 工程 4 / 工程 5 候補)

- **工程 5 (Exit ML) 主軸候補**: PPO で「保有継続 / TP / SL / 時間切れ」の連続行動学習。業界実証あり (= 78% success rate)
- **工程 4 (Position Sizing) サブ候補**: SAC は extreme vol で 94% annualized return が魅力だが、phase_flow_v4 v7 §改善 4 で「Half-Kelly + Volatility targeting + cluster 強度別配分」(= 動的合成方式) を主軸に決定済 → **SAC は補強候補 (= 動的合成出力を SAC で微調整)**
- **DQN は見送り**: 連続行動苦手・SAC/PPO に劣後
- **データ要件**: RL は環境シミュレーション必要 → cat-bitget の Phase 5 Replay 環境を活用可能

### §13.5 アンサンブル + Meta-Labeling (AFML Ch.3 + Ch.6 中核)

#### Ensemble の業界 3 系統 (AFML Ch.6)

| 手法 | 仕組み | 用途 |
|---|---|---|
| **Bagging** (Bootstrap Aggregating) | bootstrap sample で多数の弱学習器を訓練・平均で variance 低減 | Random Forest |
| **Boosting** | 逐次的に前モデルの誤差を補正・bias 低減 | LightGBM / XGBoost / CatBoost |
| **Stacking** | 複数の異種アルゴ (GBDT + DL + RL) の出力を meta-learner で統合 | プロ Quant 標準 |

#### Meta-Labeling (AFML Ch.3 pg.50 中核技術)

[Lopez de Prado 2017 (Guggenheim Partners + Cornell)](https://en.wikipedia.org/wiki/Meta-Labeling) で発表された **二段構成**:

1. **Primary model**: トレード方向 (LONG/SHORT/0) を予測 — 既存ロジック / 既存 ML どちらも可
2. **Secondary (meta) model**: Primary の予測が正しいか (= 取引するか / size をどうするか) を予測

**目的**:
- Direction と Sizing の判断を分離 (= 同時学習の非効率を解消)
- False positive を抑制 (= primary の出力を二段目で filter)

**業界実証**:
- [Hudson & Thames 検証](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/): Triple Barrier + Meta-Labeling で primary 単独より Sharpe 改善
- [QuantConnect 注記](https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/): Meta-Labeling は万能ではない (= primary が悪いと meta も救えない)

#### Phase 1 v6 案 f との関係

- 案 f は Meta-Labeling pattern (= secondary が primary の正誤を予測) だが combos_pass = 0/8 (TP precision 0.43 頭打ち)
- **失敗原因**: primary も secondary も同じ LightGBM + 同じ regime 不在ラベルで学習 → primary が悪い場合 meta も救えない実証
- 案 f の sklearn `cross_val_predict` pattern は AFML 標準実装通り (= 構造は正しい)

#### cat-bitget 適用判断 (= 工程 3 + 工程 4 統合候補)

- **工程 3 + 工程 4 を Meta-Labeling で接続**: primary (= 工程 3 Entry ML) → secondary (= 工程 4 Position Sizing の「取引するか / size どうするか」)
- **採用条件**: primary を多様化 (= 工程 1 regime 入力追加 + LONG/SHORT 分離学習 + MTF 整合) してから Meta-Labeling 再導入 → primary の品質確保が前提
- **Stacking**: 工程 3 で LightGBM + XGBoost + (オプション GRU/Transformer) を stacking する候補

### §13.6 領域 1 まとめ: ChatGPT 7 工程への当てはめ

| 工程 | 主軸アルゴ候補 | サブ候補 | 業界根拠 |
|---|---|---|---|
| 1 市場状態判定 (regime) | HMM / GMM (= §14.6) | k-means + LightGBM 分類 | 業界実証あり (BTC 2024-26) |
| 2 Entry 候補生成 | 固定ロジック (= 業界標準シグナル組合せ) | N/A (= ML 化保留) | テクニカル全体ベース・cc_role §1.7 |
| 3 Entry ML | LightGBM + XGBoost stacking | GRU / Transformer (TFT) / MiniROCKET | AFML Ch.6 + 業界実証 |
| 4 Position Sizing | 動的合成 (Half-Kelly + Vol target + cluster) | SAC で微調整 | phase_flow_v4 v7 改善 4 |
| 5 Exit ML | PPO (RL) | LSTM + XGBoost (= scale-out 確率) | RL 業界実証 78% success |
| 6 Risk 管理 | 固定ルール (= spread / ATR / volume) | N/A (= ML 化保留) | 業界実装パターン |
| 7 Online 監視 | 運用層 | concept drift detector | §14 で別途検討 |

---

## §14 ML 学習項目 (WORKFLOW 改訂35 領域 2・予測対象カタログ)

> v2 追記 (2026-05-27)。「**何を予測するか**」の業界カタログ。Phase 1 v6 6 案全滅の本質は「ラベル設計 (= MFE/MAE pct の方向不一致) + 学習方法 (= LONG/SHORT 並列・regime 不在) 」の組合せ欠陥。本章で予測対象の業界標準を整理して、工程 3-5 のラベル / 目的関数を再設計可能にする。

### §14.1 方向予測 (= TP first 確率) — Triple Barrier Method

#### 業界標準 (AFML Ch.3)

[Lopez de Prado AFML Ch.3](https://www.newsletter.quantreo.com/p/the-triple-barrier-labeling-of-marco) で確立した **3 つの barrier** によるラベル生成:

| Barrier | 設定 | ラベル |
|---|---|---|
| Upper (TP) | `entry × (1 + tp_pct)` | **+1** (利確到達) |
| Lower (SL) | `entry × (1 - sl_pct)` | **-1** (損切到達) |
| Vertical (time) | K bar 経過 | **0** (時間切れ・中立) |

**3 つのバリアのどれが最初にヒットしたか** で 3 クラス分類問題に帰着 ([Hudson & Thames 詳細](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/) / [mlfin.py 実装](https://mlfinpy.readthedocs.io/en/latest/Labelling.html))。

#### 業界優位性

- 「**実トレードの意思決定をミラーリング**」(= TP/SL は実装可能・MFE/MAE はバックテスト固有)
- ノイズ多い市場 (= crypto 5m) で ML の signal 検出力が高い
- Phase 1 v6 案 e で採用済 (multiclass 実装)

#### Phase 1 v6 案 e との関係

- 案 e は Triple Barrier multiclass を実装 → entropy_lift K=24/48/96 で 0.20-0.35 (= 6 案中最良)
- **だが combos_pass = 0/8**: 理由は §13.1 で論じた regime 不在 + LONG/SHORT 並列学習 + MTF 欠落
- Triple Barrier 自体は業界標準で正しい・**周辺の設計を直せば再利用可能**

#### cat-bitget 適用判断

- **工程 3 (Entry ML) の主ラベル**: Triple Barrier multiclass を維持
- **改善方向**: TP/SL bar 単位を K (= 1h/2h/4h/8h) 別に固定するのでなく、`entry × atr_pct` で動的に設定する業界拡張あり (= ATR-based dynamic barrier)

### §14.2 Meta-Labeling (= entry/skip + size 二値判定)

§13.5 で論じた **secondary model のラベル設計**。

#### ラベル定義 (AFML Ch.3)

- Primary が +1 (LONG) を出した時刻に、**実際に TP 到達したか** を 0/1 ラベル化
- Secondary はこれを classifier で予測 (= primary が正しい確率)
- 出力を Half-Kelly に渡して size 決定

#### cat-bitget 適用判断

- §13.5 で論じた通り「工程 3 + 工程 4 接続用ラベル」として採用候補
- **採用前提**: primary (= 工程 3 Entry ML) の品質確保

### §14.3 Volatility 予測 (= GARCH / HAR-RV / ML)

#### 業界 3 系統

| 手法 | 仕組み | BTC 業界実証 |
|---|---|---|
| **GARCH (1,1)** | 古典統計 (= conditional variance) | 1-day RMSE ~335 |
| **HAR-RV** | 日次・週次・月次の RV を重ね回帰 | 1-day RMSE 280 (GARCH 超え) |
| **LSTM / CNN-LSTM** | 深層時系列 | 全 horizon で GARCH 超え (intraday も) |
| **XGBoost / MLP** | GBDT / MLP | 競合・HAR と同水準 |

#### 業界実証

- [Modern Finance 2025](https://mf-journal.com/article/view/370) crypto vol で deep learning > GARCH
- [Springer Asia-Pacific FM 2024](https://link.springer.com/article/10.1007/s10690-024-09510-6) HAR + sentiment + ML horserace で HAR-RV 優位を再確認
- [arxiv 2202.08962](https://arxiv.org/pdf/2202.08962) intraday vol 予測で commonality (= 横断的共通因子) 重要

#### cat-bitget 適用判断 (= 工程 4 入力)

- **工程 4 (Position Sizing) の必須入力**: Half-Kelly + Volatility targeting (= phase_flow_v4 v7 改善 4) で vol 予測値が必要
- **採用候補**: HAR-RV を baseline (= 軽量・解釈可能) + LightGBM/LSTM で補強
- **実装**: 1432 指標の中に realized_vol_5m / realized_vol_1h / realized_vol_4h を既に含む → これを HAR-RV 構造で組み合わせる工程を追加

### §14.4 Sharpe / Sortino 直接最適化

#### 業界実装 (Decision-Focused Learning)

[Oxford-Man Institute 2020 paper](https://www.oxford-man.ox.ac.uk/wp-content/uploads/2020/06/Deep-Learning-for-Portfolio-Optimisation.pdf) で確立した **end-to-end** 手法:

1. Returns 予測を経由しない
2. Portfolio weights を直接予測
3. Loss function = **-Sharpe ratio** (= negative Sharpe を最小化)

#### 業界実証

- [arxiv 2005.13665](https://arxiv.org/pdf/2005.13665) Sharpe 直接最適化で従来 (= MV optimization) 超え
- [Cryptocurrency Portfolio NN](https://arxiv.org/pdf/2310.01148) crypto multi-asset で Sharpe 最大化
- [arxiv 2503.13544](https://arxiv.org/html/2503.13544v3) Deep Ensembles で robust portfolio

#### cat-bitget 適用判断 (= 工程 4 / Phase 4-a cluster 配分)

- **工程 4 サブ手法候補**: Half-Kelly 主軸の cluster 別配分を Sharpe 直接最適化 NN で導出
- **採用条件**: cluster 数 (= 12 程度) が安定した後に追加検討。現状は phase_flow_v4 v7 改善 4 の動的合成方式が主軸

### §14.5 Position size 直接予測 (= Kelly / Half-Kelly + ML 補正)

#### Kelly criterion (AFML / Modern PM の中核)

**式**: `f* = (b × p - q) / b`

| 記号 | 意味 |
|---|---|
| `f*` | 最適 fraction (= 資金の何 % を賭けるか) |
| `b` | 賠率 (= reward / risk = 平均利益 / 平均損失) |
| `p` | 勝率 |
| `q` | 負け率 = 1-p |

#### Full / Half / Quarter Kelly

| 比率 | 業界推奨 | 特性 |
|---|---|---|
| Full | ❌ 非推奨 | 最速成長だが DD 50-80% |
| Half (0.5×f*) | ✅ 最多採用 | 成長率 ~75% Full 比 + DD 約 50% 削減 |
| Quarter (0.25×f*) | ✅ crypto vol 推奨 | 推定誤差バッファ最大 |

#### データ要件

- **最低 50-100 trades** で p / b を統計的に有意化
- Phase 1 v6 案 e で発火 4,000-15,000 件/年 → データ要件は十分

#### cat-bitget 適用判断 (= 工程 4 主軸)

- **phase_flow_v4 v7 §改善 4 で確定済**: Half-Kelly + Volatility targeting + cluster 強度別配分の **動的合成方式 8**
- **業界整合**: crypto は vol が高い → Quarter Kelly が業界推奨だが、cat-bitget は cluster で分散させる前提で Half-Kelly 採用は妥当
- **0.12 BTC 合計上限制約**: Kelly が示す最適 size が 0.12 BTC を超えても **clip 必須** (= CLAUDE.md §0-2 絶対規定)

### §14.6 Regime 予測 (= HMM / GMM / ML 分類)

#### 業界 3 系統

| 手法 | 仕組み | 強み |
|---|---|---|
| **HMM** (Hidden Markov Model) | 観測価格から隠れ状態 (regime) を Viterbi で推定 | 動的 regime 遷移確率を学習 |
| **GMM** (Gaussian Mixture Model) | 静的 clustering で returns を multivariate Gaussian の混合で fit | 解釈容易・EM で推定 |
| **k-means** | 静的 clustering (= GMM の特殊解) | 最軽量 |
| **ML 分類** (LightGBM/SVM) | regime を教師ラベル化して supervised | 特徴量自由度高 |

#### 業界実証 (BTC 2024-2026)

- [Preprints 202603.0831](https://www.preprints.org/manuscript/202603.0831) BTC で HMM / Markov 適用・vol regime と structural breaks 検出
- [QuantStart QSTrader](https://www.quantstart.com/articles/market-regime-detection-using-hidden-markov-models-in-qstrader/) GaussianHMM で high/low vol regime 検出
- [LSEG Devportal](https://developers.lseg.com/en/article-catalog/article/market-regime-detection) HMM / GMM の業界比較

#### cat-bitget 適用判断 (= 工程 1 = 現状固定ルール → ML 化候補)

- **現状 (= WORKFLOW 改訂 35 active 確定)**: 工程 1 は 4 時間足単一判定 + ADX > 25 / DI 差の **固定ルール** (= MVP)
- **次段 ML 化候補**: HMM (= 業界実証あり・Viterbi で動的遷移) を採用候補
- **GMM / k-means**: 業界実装パターンの 1 つだが Phase 1 v6 6 案で k-means / GMM 由来の cluster 特徴量が学習対象に混入していなかった経緯 → 工程 1 で独立に学習させる構造に直す

### §14.7 Exit timing 予測 (= ML による動的 Exit)

#### 業界 4 手法

| 手法 | 業界実証 |
|---|---|
| **XGBoost 確率予測** | [Trend Exhaustion 確率 > 70% で 33% scale-out](https://quantstrategy.io/blog/machine-learning-for-exit-optimization-predicting-the-best/) (E-mini S&P 500・5y tick data) |
| **LSTM 時系列予測** | [Predicting SL/TP Signal](https://blog.quantinsti.com/predicting-sl-tp-signal-machine-learning-project-sunanda/) で LSTM を SL/TP 予測に多用 |
| **RL (PPO)** | scale-out sequence を学習 (= §13.4) |
| **多段 grid-search + vol-based market timing** | TP/SL grid + vol 信号併用 |

#### 業界実証の核心

- 「**adaptability**」が ML 優位点: 固定 % ルールでは捕捉できない trend exhaustion / regime shift を ML が real-time 検出
- 業界 success rate: PPO で 78% (risk control) / LSTM 28% という差 (= §13.4 実証)

#### cat-bitget 適用判断 (= 工程 5 主軸)

- **主軸候補**: PPO (= §13.4 で論じた・78% success rate)
- **サブ候補**: XGBoost で scale-out 確率予測 (= 業界実証あり・Phase 1 v6 の GBDT インフラ再利用可能)
- **既存暫定 Exit との関係**: Phase 4-b の time_exit / TP_PCT / SL_PCT / TRAIL_RATIO 等 12 種は **業界比較ベースライン** として残す (= phase_flow_v4 v7 改善 4 同型・主軸 1 + 比較 N 構造)

### §14.8 7 工程との対応マトリックス (= 領域 2 まとめ)

| 工程 | 主予測対象 | ラベル | 業界手法 | cat-bitget 採用候補 |
|---|---|---|---|---|
| 1 regime | regime 状態 (= up/down/range) | 4h 足 regime ラベル | HMM / GMM / ADX-based 固定 | 固定ルール (= ADX > 25 + DI 差・MVP) → 次段 HMM |
| 2 Entry 候補生成 | (= 予測ではなく固定ロジック) | N/A | 業界標準シグナル組合せ | 固定 (= cc_role §1.7) |
| 3 Entry ML | TP first 確率 | Triple Barrier multiclass (+1/-1/0) | AFML Ch.3 | 案 e ベース + 工程 1 入力追加 + LONG/SHORT 分離 + MTF |
| 4 Position Sizing | size (BTC) | Half-Kelly target (= cluster × vol × Kelly) | Kelly criterion + Vol targeting | phase_flow_v4 v7 改善 4 動的合成方式 8 |
| 5 Exit ML | Exit timing / dynamic SL/TP | multiclass (TP/SL/time/trail) | PPO / XGBoost / LSTM | PPO 主軸 + XGBoost サブ |
| 6 Risk 管理 | spread / ATR 急変 / vol spike | N/A (= 固定ルール) | 業界標準 (= post-trade filter) | 固定ルール |
| 7 Online 監視 | concept drift / 過学習 alarm | N/A (= 運用層) | drift detection (KL / Wasserstein) | §15 で別途検討 |

---

## §15 領域 1-2 の総合所見 (= 残り 5 領域への接続)

### 15.1 領域 1-2 学習で見えた cat-bitget の改善方向

1. **アルゴリズム多様性**: Phase 1 v6 案 a-f が **全 LightGBM** → XGBoost / GRU / Transformer / RL の並走必要 (§13.1 / §13.2 / §13.4)
2. **予測対象多様性**: 現状 MFE/MAE pct + Triple Barrier multiclass のみ → Meta-Labeling / Volatility / Exit timing 等への展開必要 (§14.1-§14.7)
3. **regime 不在の致命性**: Phase 1 v6 全滅の根本原因 = regime context を入力に入れていない → HMM/GMM で工程 1 出力を独立に与える必要 (§14.6)
4. **MTF 整合の欠落**: 現状 5m 単独学習 → 4h regime + 1h setup + 5m entry の 3 層構造が業界標準 (§13.2 Transformer / §14.6 HMM どちらでも MTF 入力で性能向上)

### 15.2 案 B 学習完了 (= 7/7 = 100%・v6 で領域 7 完成)

- ~~**領域 3 (ML 特徴量設計)**~~ → **v3 §16 で完成** (Fractional Differentiation / スケーリング / 特徴量選択 / 出来高系 / 板情報系)
- ~~**領域 4 (ML 評価方法)**~~ → **v3 §17 で完成** (Walk-Forward / Purged K-Fold / CPCV / Embargo / DSR / PBO / Pipeline leak 防止 / Concept drift)
- ~~**領域 5 (ML 組合せ手法)**~~ → **v4 §18 で完成** (階層 Stacking / Cascade / HRP+HERC+NCO / Meta-Labeling 多段詳細)
- ~~**領域 6 (リスク管理)**~~ → **v5 §19 で完成** (Volatility targeting / Stop-loss 業界手法 / Drawdown control TIPP / Position scaling Kelly + Pyramiding / 補強 risk measure)
- ~~**領域 7 (監視・運用)**~~ → **v6 §20 で完成** (Concept Drift Detection 拡張 / Online Learning / A/B Testing + Multi-Armed Bandit + Thompson Sampling / Champion-Challenger / Shadow deployment / Production ML Monitoring 3 階層)

### 15.3 次セッションの推奨着手順位 (= 案 B 学習完了 → 工程 2-7 詳細詰めへ)

1. **🎉 案 B (= ChatGPT 7 工程フレーム範囲の ML 知識体系化) 完了** = 領域 1-7 全 7/7 完成
2. **次フェーズ = WORKFLOW 改訂40 active 優先 3 = 工程 2-7 詳細詰め (= 設計確定)** に進む
3. 工程詳細詰めの順序候補:
   - 工程 1 (regime) = 固定ルール (ADX + DI 差) MVP の verify + 次段 HMM ML 化検討
   - 工程 2 (Entry 候補生成) = 業界標準シグナル組合せ (= テクニカル全体カバー網羅) で固定ロジック確定
   - 工程 3 (Entry ML) = 案 g (= §18.5 異種 Stacking + Meta-Labeling 3 段) を Phase 1 v7 として実装計画
   - 工程 4 (Position Sizing) = 動的合成方式 8 (= Half-Kelly + Vol target + HRP/HERC + Thompson Sampling) 確定
   - 工程 5 (Exit ML) = PPO 主軸 + Chandelier/Wilder Stop 比較 + Partial TP + ATR Trailing
   - 工程 6 (Risk 管理) = TIPP + Dynamic Deleveraging + regime 別 CVaR
   - 工程 7 (Online 監視) = ADWIN/KSWIN/PH + River + Champion-Challenger + Shadow + 3 階層 observability
4. 工程確定後 → 実装着手 (= Phase 0 v4 → Phase 1 v7 → Phase 2-7) に進む

### 15.4 cat-bitget 設計判断の確定事項 (v3 学習成果から拡張)

> ⚠️ 以下は **学習資料の調査ノート位置付け**。実際の設計確定は WORKFLOW 改訂36 active の優先 3 (= 工程 2-7 詳細詰め) で別途実施 (cc_role §1.5 デザイン責任)。

#### v2 (= 領域 1-2) の確定事項
- **工程 3 (Entry ML) ベース**: Triple Barrier multiclass (= 案 e 構造) + LightGBM / XGBoost stacking + Meta-Labeling 二段化 + regime 入力 + LONG/SHORT 分離 + MTF
- **工程 4 (Position Sizing)**: phase_flow_v4 v7 改善 4 動的合成方式 8 (= Half-Kelly + Vol target + cluster 強度別配分) を維持
- **工程 5 (Exit ML)**: PPO (= RL) 主軸 + XGBoost (= scale-out 確率) サブ
- **工程 1 (regime)**: 固定ルール (= ADX + DI 差) で MVP・後段で HMM ML 化検討

#### v3 (= 領域 3-4) の追加確定事項
- **工程 3 入力強化 (= §16.7)**: (a) Volume bar 並行入力 / (b) Fractional Diff MTF 24 特徴量 / (c) 出来高系 48 特徴量 (= OBV / VWAP dist / Volume Profile HVN / Volume Z-score / Chaikin) / (d) microstructure 10-15 特徴量 (= OBI L=5,10,20 / Taker Ratio / Bid-Ask Spread / Funding Rate 時系列入力化 / OI ROC) / (e) Clustered MDA で 2604 → 500-1000 削減
- **工程 3 評価強化 (= §17.3)**: CPCV (= C(6,2) = 15 paths) を案 e ベースで再評価 → Sharpe 分布 + backtest paths robustness 強化
- **Phase 5 / 6-b 合格判定追加 (= §17.4 + §17.5)**: 月次 NET ≥ $1,900 全月クリア (= 現状必達) + **DSR > 0.95** + **PBO < 0.5** で本番投入リスク多重防御
- **Phase 0 v4 拡張候補**: time bar 5m + Volume bar (= BTC 出来高 X BTC 毎) 並行入力 + Fractional Diff + 出来高系 + microstructure
- **scaler leak 防止 (= §17.7)**: Pipeline + TimeSeriesSplit で fold 毎 fit を全 Phase 実装義務化 (= 現状の implementation grep verify 要)
- **混合禁止再確認 (= §17.6 + cc_role §1.4.6.1 #9)**: Phase 1-3 = 統計指標 / Phase 5-6-b = PnL 指標 + DSR + PBO の **物理分離維持**

#### v4 (= 領域 5) の追加確定事項
- **工程 3 アーキ強化 (= §18.1)**: LightGBM (= 現案 e ベース) + XGBoost + 1 種類の DL (= TFT / GRU いずれか) の **異種 3 base learner + Logistic Regression meta-learner** の階層 Stacking 構造を Phase 1 v7 候補に。out-of-fold prediction は Purged K-Fold ベースで生成し leak 防止
- **工程 3 + 工程 5 接続 (= §18.2)**: Cascade 多段 Filter で偽信号削減。段 1 = LightGBM 高 recall (= 全 entry 候補捕捉)・段 2 = XGBoost 高 precision (= 偽信号 reject)・段 3 = Meta-Labeling secondary で size 決定。各段の閾値は train 内で grid search・採用は OOF (out-of-fold) 性能で判断
- **工程 4 配分強化 (= §18.3)**: phase_flow_v4 v7 改善 4 動的合成方式 8 (= Half-Kelly + Vol target + cluster 強度別) に **HRP / HERC で cluster 内配分を robust 化** する候補。NCO (Nested Clustered Optimization) は cluster 数 ≥ 12 で過剰最適化リスク低減
- **工程 3 + 工程 4 接続 (= §18.4)**: Meta-Labeling 多段詳細 = primary (= 異種 stacking) → secondary (= 確率 calibrate + Half-Kelly に投入) → tertiary 候補 (= regime 別 secondary を分離学習・案 f 失敗の構造的補正)
- **多様性 verify (= §18.1)**: base learner 間の予測 correlation を r < 0.6 に維持 (= arxiv 2512.15738 実証ベンチマーク)。同一アルゴ (全 LightGBM) で stack しても効果薄を Phase 1 v6 6 案全滅で実証済 (L-223 + L-224)
- **業界整合性 (= §18.5)**: HRP は OOS で Mean-Variance 比 robust だが、crypto 単一資産 (BTC) では 1/N (= buy-and-hold) に劣後事例あり (Quantopian 実証) → cat-bitget では「cluster × Exit type」の strategy combination に HRP/HERC を適用する位置付け (= asset allocation でなく strategy allocation)

#### v5 (= 領域 6) の追加確定事項
- **工程 4 (Position Sizing) 業界整合 verify (= §19.1 + §19.4)**: phase_flow_v4 v7 改善 4 動的合成方式 8 (= Half-Kelly + Vol target + cluster 強度別) は業界 default 範囲内・Quarter-Kelly 比較追加候補・cluster 強度別配分は §18.3 HRP/HERC で robust 化候補と統合
- **工程 5 (Exit ML) 業界比較ベースライン拡張 (= §19.2)**: PPO 主軸維持 + **Chandelier Exit (N=288 5m / M=2.5 crypto 調整) + Wilder Volatility Stop (N=84 / M=2.0) + Fixed % Stop (= 旧 Priority baseline)** の 3 比較を Phase 4-b に追加候補。Partial TP + ATR Trailing (= 50% fixed TP + 50% ATR trail) を組合せ追加
- **工程 6 (Risk 管理) レイヤー新設 (= §19.3)**: **TIPP drawdown floor (X=0.9・MDD < 10% target)** + **Dynamic Deleveraging (= drawdown / vol spike / regime trigger の OR)**。CPPI は whipsaw リスクで見送り
- **Phase 5 / 6-b 合格判定多重防御 (= §19.5)**: 月次 NET ≥ $1,900 全月クリア (必達) + DSR > 0.95 + PBO < 0.5 (v3) + **Calmar > 2.0 + CVaR_95 < $X/月 + Sortino > 1.5** (v5) の多重防御
- **Volatility Targeting 主軸 (= §19.1)**: σ_target = 年率 10-15% (= crypto base annual vol 60-80% から 0.15-0.25x deleveraging) + HAR-RV baseline + EGARCH(1,1) で leverage effect 補強・0.5x-2.0x clip
- **MAX_ADDS 業界整合**: 旧 Priority MAX_ADDS=5 (= 平均建値型 pyramiding) は業界 default 上端 3-5 ✅・**層 size は progressively 縮小**が業界推奨 (= 現状均等 size の可能性あり要 verify)・Volatility-Adjusted Pyramiding (= ATR で layer 間隔調整) を Phase 7-c 候補
- **0.12 BTC 合計上限制約**: vol targeting / TIPP / HRP / Half-Kelly / Pyramiding 全層で得られる weight が 0.12 を超えても **必ず clip** (= CLAUDE.md §0-2 絶対規定・全リスク管理手法で義務)
- **regime 別 risk measure 動的閾値 (= MDPI 2026 業界推奨)**: down regime で CVaR / Calmar 厳しめ・range regime で緩め → 工程 1 regime 出力と工程 6 risk threshold を動的接続

#### v6 (= 領域 7) の追加確定事項
- **工程 7 (Online 監視) 主軸確立 (= §20.1)**: **ADWIN + KSWIN + Page-Hinkley の 3 種類並走** で drift detection・ADWIN = LightGBM/XGBoost prediction monitor / KSWIN = 入力 feature 分布 monitor / Page-Hinkley = 月次 NET / 勝率の累積偏差 monitor
- **Online learning 基盤 (= §20.2)**: **River (= scikit-multiflow と creme 統合・業界 default) + Incremental LightGBM/XGBoost (= warm start で 5-10 分 update・58.2x-974.3x 高速化)** のハイブリッド。週次 incremental + 半年 from scratch 再学習
- **動的 weighting (= §20.3)**: **Thompson Sampling (Beta-Bernoulli)** で cluster × Exit type × side 戦略の online weighting。phase_flow_v4 v7 改善 4 動的合成方式 8 の cluster 強度別配分を online 化。HRP/HERC (= §18.3) と並走候補 (= HRP で risk constraint + TS で reward exploration)
- **Champion-Challenger 段階 rollout (= §20.4)**: Shadow → Canary 1% → Ramp 5/20/50% → Full 100% の 5 段階 ramp + 各 stage gating criteria (= 月次 NET ≥ $1,900 / DSR > 0.95 / PBO < 0.5 / Calmar > 2.0) 未達で auto-rollback
- **Shadow deployment (= §20.5)**: Phase 7-d で新 model を Demo API で 4 週間以上 paper trading + 仮想 PnL log + 月次 NET 達成判定 → Canary 移行
- **3 階層 observability + business metric (= §20.6)**: Infrastructure (= Bitget API latency + process memory) + Data (= feature null / drift) + Model (= prediction drift) + Business (= 月次 NET / DD / Calmar) の 4 軸 + INFO/WARN/CRITICAL 3 段 alert + CRITICAL で自動 deleveraging
- **第 8 軸追加 (= §20.7)**: L-227 §19.6 確定 7 軸多様性欠落に **第 8 軸 = 運用層 (= drift detection / online learning / 動的切替) 設計不在** を追加。旧 Priority / Phase 1 v6 は static model + 固定 weight + 手動切替で non-stationary crypto 市場に対応不能の構造的欠陥を整理

---

## §16 ML 特徴量設計 (WORKFLOW 改訂36 領域 3・業界カタログ)

> v3 追記 (2026-05-XX)。**「何を入力として ML に渡すか」の業界カタログ**。Phase 1 v6 6 案全滅の補強原因として §13.1 (= 全 LightGBM・アルゴ多様性ゼロ) を確定したが、本章では **入力側の構造的欠陥** = MTF 整合不在 / 出来高系不在 / 板情報系不在 / 価格バー = 5m time bar 固定 を業界カタログで整理する。ChatGPT 7 工程の工程 3 (Entry ML) 入力設計に直結。

### §16.1 価格バー設計 (AFML Ch.2・time bar 以外の選択肢)

#### 業界 5 種

| バー種別 | サンプリング条件 | 業界用途 |
|---|---|---|
| **Time bars** | 固定時間 (= 5m / 1h 等) | 業界標準・実装容易・現状 cat-bitget |
| **Tick bars** | 固定 tick 数 (= N 件の trade 毎) | 流動性変動の正規化 |
| **Volume bars** | 固定 volume (= N BTC 毎) | 情報密度の均一化 |
| **Dollar bars** | 固定 dollar (= N USDT 毎) | 価格変動による情報量歪み吸収 |
| **Imbalance bars (TIB/VIB/DIB)** | buy/sell imbalance が閾値超え | **情報到達タイミング検出** |

#### 教科書整合 + 出典

- AFML **Ch.2 Financial Data Structures**: 「time bars はサンプリング歪み (= 流動性低時間帯の情報希薄 / 高流動性時間帯の情報過剰) を持つ」を実証。Volume / Dollar bars は returns 分布が time bars より正規分布に近く ML 入力として優位。Imbalance bars は「order flow の異常 (= 新情報到来) を early detect」する設計
- [Information-driven bars 解説 (Medium)](https://medium.com/data-science/information-driven-bars-for-financial-machine-learning-imbalance-bars-dda9233058f0): TIB は buy/sell tick 数の imbalance が閾値超えでサンプル / VIB / DIB は volume / dollar 単位での imbalance 検出 — 「市場が新情報を受けて方向転換する **直前** を捕捉」できる
- [Beyond the Clock (MQL5)](https://www.mql5.com/en/articles/22063): Activity bars + Imbalance bars の Python / MQL5 実装例

#### Phase 1 v6 6 案との関係

- 案 a-f は **全て time bar (5m 固定)**・bar 種別の多様性ゼロ
- TP precision 0.43 頭打ちの背景に「5m time bar 固定で情報希薄時間帯のノイズを学習対象に混ぜている」可能性
- 業界実証: Volume / Dollar bars は同じアルゴでも返り値分布が改善され ML 精度向上事例多数

#### cat-bitget 適用判断 (= 工程 3 入力 + Phase 0 ラベル再生成候補)

- **主軸候補**: time bar 5m + Volume bar (= BTC 出来高 X BTC 毎) の **並行入力** → ML が両方を見て情報量重み付け可能に
- **Imbalance bar は次段**: 5m bot 運用要件 (= 推論レイテンシ) に合うかは要検討。bot 起動時に Bitget WebSocket trade stream の subscribe + リアルタイム集計が必要
- **Phase 0 ラベル再生成**: Triple Barrier (= §14.1) を **time bar + volume bar の両方** で生成して比較する設計検討候補

### §16.2 Fractional Differentiation (AFML Ch.5・stationarity vs memory)

#### 業界の根本問題

| 系列 | 定常性 | メモリー保持 | ML 入力としての適性 |
|---|---|---|---|
| **生価格 (= raw close)** | ❌ 非定常 (= 単位根) | ✅ 完全保持 | ❌ ML が cointegration 学習困難 |
| **整数 1 階差分 (= returns)** | ✅ 定常 | ❌ 完全喪失 (= 過去価格情報なし) | △ メモリー喪失で予測力低下 |
| **Fractional Differentiation (FFD・d ∈ [0,1])** | ✅ 定常 (最小 d で達成) | ✅ 最大保持 (= 元系列との相関高) | ✅ 業界最適 |

#### 教科書整合 + 出典

- AFML **Ch.5 Fractionally Differentiated Features** ([O'Reilly](https://www.oreilly.com/library/view/advances-in-financial/9781119482086/c05.xhtml)): 「price series は long-memory を持つ。returns に変換するとメモリーは完全に失われ ML の予測力を低下させる。**最小の non-integer d で定常性を達成** することでメモリー保持しつつ ML 入力に使える」
- [mlfinlab Fractional Differentiation 実装](https://random-docs.readthedocs.io/en/latest/implementations/frac_diff.html): Fixed-Width Window Fracdiff (= FFD) と Expanding Window Fracdiff の 2 実装。FFD は計算コスト低く本番運用向き
- [Hudson & Thames blog](https://hudsonthames.org/fractional-differentiation/): d の決定方法 = ADF (Augmented Dickey-Fuller) test で stationarity を p < 0.05 で達成する最小 d を探索
- [Feature Engineering for ML — Stationarity Without Memory Loss (MQL5)](https://www.mql5.com/en/articles/22014): MetaTrader 5 + MQL5 で FFD 実装解説

#### Phase 1 v6 6 案との関係

- 案 a-f の入力 2604 特徴量に **fractional differentiated price 系列が含まれていない** (= grep verify 要)
- 既存特徴量は returns ベース (= log return / pct change) → メモリー喪失構造
- → ML が「価格の長期トレンド」を学習できず regime context 不在の補強原因

#### cat-bitget 適用判断 (= 工程 3 入力強化)

- **追加候補**: `fracdiff_close_5m_d{0.3,0.4,0.5}` を Phase 0 ラベル再生成時に MTF 8 TF (= 5m/15m/30m/1h/2h/4h/1d/1w) で展開 → 24 特徴量追加
- **d 値選定**: BTC 5m close で ADF test → p < 0.05 を達成する最小 d を grid search (= 0.1, 0.2, 0.3, 0.4, 0.5)
- **実装ライブラリ**: `mlfinlab.features.fracdiff` または `fracdiff` (PyPI・Daniel Saito) のいずれか

### §16.3 特徴量スケーリング (tree vs NN・data leakage 対策)

#### 業界判断マトリックス

| アルゴ | スケーリング必要性 | 推奨手法 | 理由 |
|---|---|---|---|
| **LightGBM / XGBoost / CatBoost** | ❌ **不要** (= 木が閾値分割するため scale 非依存) | (適用しない) | 業界標準 |
| **GRU / LSTM / Transformer** | ✅ **必要** (= gradient 安定化) | StandardScaler / RobustScaler | 業界標準 |
| **k-means / GMM / HMM** | ✅ **必要** (= 距離ベース) | StandardScaler | 業界標準 |
| **RL (PPO/SAC)** | ✅ **必要** (= NN 内部) | StandardScaler | 業界標準 |

#### スケーリング手法の業界使い分け

| 手法 | 業界用途 |
|---|---|
| **StandardScaler** ((x-μ)/σ) | 業界 default・正規分布近似のデータ向け |
| **MinMaxScaler** ((x-min)/(max-min)) | 範囲限定 0-1 必要時 (= NN 出力近似) |
| **RobustScaler** ((x-median)/IQR) | **外れ値多い時 (= crypto returns)** ・業界推奨 |
| **QuantileTransformer** (= rank ベース) | 強い非線形変換許容時 |

#### Data Leakage 必須回避ルール

- **絶対禁止**: `scaler.fit(全データ).transform(train + test)` → 「scaler の fit に test data の統計量が混入」= leak
- **正しい順序**: `scaler.fit(train).transform(train)` → `scaler.transform(test)`
- **Pipeline 推奨**: `sklearn.pipeline.Pipeline([('scaler', StandardScaler()), ('model', LGBMClassifier())])` でフォールドごと自動 fit
- **時系列固有**: `TimeSeriesSplit` (= time-aware CV) で fold 分割すれば train ⊆ past / test ⊆ future が保証される

#### 教科書整合 + 出典

- [Feature Scaling Pitfalls (ML Journey)](https://mljourney.com/feature-scaling-issues-with-tree-based-vs-linear-models/): tree 系は閾値分割で scale 非依存・NN / k-means / 距離ベース手法のみスケーリング必要
- [scikit-learn Common Pitfalls 11.1](https://scikit-learn.org/stable/common_pitfalls.html): `fit_transform` の誤用パターン解説
- [Data Leakage in Preprocessing (Towards Data Science)](https://towardsdatascience.com/data-leakage-in-preprocessing-explained-a-visual-guide-with-code-examples-33cbf07507b7/): 視覚的 leakage 解説
- [How to Avoid Data Leakage (MachineLearningMastery)](https://machinelearningmastery.com/data-preparation-without-data-leakage/): preprocessing 全般での leak 防止
- [The Impact of Feature Scaling (arxiv 2506.08274)](https://arxiv.org/html/2506.08274v1): regression / classification での scaling 効果実証

#### cat-bitget 適用判断 (= 工程 3 / 工程 4 / 工程 5)

- **工程 3 主軸 (LightGBM)**: スケーリング不要 (= 現状継続)
- **工程 3 サブ (Transformer / GRU)**: RobustScaler 必須 (= crypto returns の外れ値耐性)
- **工程 4 動的合成 (Half-Kelly + Vol target)**: スケーリング不要 (= 確率 / 比率の合成)
- **工程 5 (PPO/SAC)**: StandardScaler 必須 (= NN 内部)
- **Pipeline 整備**: Phase 0 で `sklearn.pipeline` でフォールド毎 scaler fit を実装義務化

### §16.4 特徴量選択 (AFML Ch.8・MDI / MDA / SFI + Boruta / SHAP)

#### 業界 4 系統

| 手法 | 仕組み | 業界用途 | 弱点 |
|---|---|---|---|
| **MDI (Mean Decrease Impurity)** | tree 内の impurity 減少量を集計 (in-sample) | LightGBM 既定 `feature_importance` | substitution effect (= 相関 feature で過小評価) / IS bias |
| **MDA (Mean Decrease Accuracy)** | feature shuffle → OOS metric 低下量 (out-of-sample) | model-agnostic・業界推奨 | substitution effect / shuffle cost 高 |
| **SFI (Single Feature Importance)** | 1 feature のみで学習 → CV score (out-of-sample) | substitution effect 回避 | 相互作用無視 |
| **Clustered MDA / MDI** | MDA / MDI の前に feature clustering | substitution effect 解消 | clustering 自体に判断 |

#### 補完手法 (= AFML 外・業界実装)

| 手法 | 仕組み | 業界用途 |
|---|---|---|
| **Boruta** | shadow features (= shuffle 版) と原 features を比較 → 統計的に有意な features のみ採用 | wrapper 手法・業界標準 |
| **SHAP (Shapley Additive)** | game theory 由来・各 feature の marginal contribution | 解釈性 + 選択両用 |
| **shap-select** (2024 arxiv) | SHAP value + regression で軽量選択 | 大規模 feature 向け |
| **Mutual Information** | feature と target の相互情報量 | non-linear 関係も検出 |
| **MRMR (Max Relevance Min Redundancy)** | MI ベース・冗長性最小化 | 業界実装 (HISEL) |

#### 教科書整合 + 出典

- AFML **Ch.8 Feature Importance** ([mlfinlab MDI/MDA/SFI 解説](https://www.mlfinlab.com/en/latest/feature_importance/afm.html)): 3 つの手法を comparison。「MDI は IS bias・MDA は substitution effect」を実証 → **Clustered MDA** を推奨
- AFML **Ch.6 Ensemble Methods** + Clustered Feature Importance presentation (Lopez de Prado): substitution effect を hierarchical clustering で解消
- [Boruta + SHAP (BorutaShap)](https://medium.com/analytics-vidhya/is-this-the-best-feature-selection-algorithm-borutashap-8bc238aa1677): Boruta の RF を XGBoost に置き換え + SHAP で statistical significance 判定
- [Boruta in Financial Distress Prediction (ACM)](https://dl.acm.org/doi/10.1145/3584202.3584298): MLP + GA のハイブリッドモデルで Boruta が予測精度向上
- [Mutual Information for Feature Selection (Elements of FML)](https://joaodmrodrigues.github.io/elements-financial-machine-learning/information%20theory/mutual%20information/feature%20selection/feature%20importance/2021/02/06/mutal_information_and_feature_selection.html): MI ベース手法の理論 + 実装
- [shap-select (arxiv 2410.06815)](https://arxiv.org/html/2410.06815v1): SHAP value + regression で軽量 feature selection

#### Phase 1 v6 6 案との関係

- 案 a-f は LightGBM `feature_importance` (= MDI) のみで feature importance を verify → **MDI bias + substitution effect で本物の重要 feature を見逃した可能性**
- 「feature_importance top20 がボラ系支配」(= L-223) の判定も MDI ベース → MDA / Clustered MDA で再 verify する余地あり

#### cat-bitget 適用判断 (= 工程 3 ハイパラチューニング + 学習対象削減)

- **主軸採用**: Clustered MDA で 2604 特徴量を 500-1000 に削減候補
- **サブ採用**: Boruta + SHAP で stability selection 並走
- **業界実証 (microstructure)**: [arxiv 2506.05764 microstructure](https://arxiv.org/html/2506.05764v2) は **stability selection + SHAP + purged walk-forward** で BTC microstructure 9 measures を選別
- **Phase 1 v7 候補**: 既存 feature_importance を Clustered MDA で再評価 → top 200-500 のみで再学習 → entropy_lift / TP precision 改善余地検証

### §16.5 出来高系特徴量 (= 旧 Priority 完全欠落領域)

#### 業界カタログ

| 指標 | 業界用途 | BTC 5m 業界実証 |
|---|---|---|
| **OBV (On-Balance Volume)** | 累積買売圧力 | 業界使用あり (= momentum confirmation) |
| **VWAP (Volume Weighted Avg Price)** | 機関的 benchmark / mean reversion | crypto 業界実証あり (= 5m / 1h で使用) |
| **Volume Profile** | 価格帯別出来高分布 → S/R 自動検出 | High Volume Node (HVN) / Low Volume Node (LVN) で support / resistance |
| **Volume Surge / Z-score** | 異常出来高検出 | breakout の補助確認 |
| **Chaikin Oscillator** | 出来高 + 価格の組合せ momentum | 業界使用あり (= LightGBM input としても) |
| **Accumulation/Distribution Line** | money flow 検出 | 業界使用あり |

#### 教科書整合 + 出典

- [Volume Analysis Mastery (Tickrad 2025)](https://www.tickrad.com/blog/volume-analysis-mastery-institutional-footprints-2025): Volume Profile + HVN/LVN で institutional footprint 検出
- [VWAP in Crypto 2025 (Mudrex)](https://mudrex.com/learn/vwap-in-crypto/): 9 powerful tips and strategies — daily VWAP / weekly VWAP / session VWAP の使い分け
- [Bitcoin AI Prediction (PMC 2025)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12058735/): RSI / OBV / Chaikin Oscillator は **feature importance ≈ 0** だった事例 (= ML が出来高系を学習困難な可能性も示唆)
- [VWAP Deep Learning Execution (arxiv 2502.13722)](https://arxiv.org/html/2502.13722v1): crypto market での VWAP execution に DL を適用

#### Phase 1 v6 6 案との関係 + 旧 Priority との関係

- §9.1 (v1) で実証: **旧 Priority は出来高系をゼロカバー**
- Phase 0 特徴量カタログ (1432 → 2604 拡張後) でも出来高系の比率は薄い (= grep verify 要)
- → 工程 3 Entry ML 入力に出来高系を追加することで「予測対象の多様性」(= §15.1) を実現可能

#### cat-bitget 適用判断 (= 工程 3 入力強化・Phase 0 v4 候補)

- **追加候補 (= Phase 0 v4 で実装)**:
  - `obv__{5m,15m,1h,4h}` + `obv_slope__{5m,1h}` (= 既存 1 件のみだったら拡張)
  - `vwap_dist_pct__{5m,15m,1h,4h}` (= close と VWAP の % 乖離)
  - `volume_profile_hvn_dist__{1h,4h}` (= 直近 N 時間の HVN まで何 % か)
  - `volume_zscore_20__{5m,15m,1h}` (= 20 bar 平均からの偏差)
  - `chaikin_osc__{5m,1h}` (= 既存可能性あり・verify)
- **MTF 拡張**: 8 TF × 6 family = 48 特徴量追加候補
- **注意**: PMC 2025 実証で OBV / Chaikin = importance 0 だった事例あり → cat-bitget BTC 5m で feature importance を再 verify してから採用判定

### §16.6 板情報系特徴量 (= microstructure・旧 Priority 完全欠落領域 + Phase 0 完全欠落領域)

#### 業界カタログ (= cat-bitget Phase 0 v4 で最大の伸びしろ候補)

| 指標 | 業界用途 | 計算式 |
|---|---|---|
| **Bid-Ask Spread** | 流動性 + spread cost 推定 | `(ask - bid) / mid` |
| **Order Book Imbalance (OBI)** | 短期 mid-price 予測 | `(bid_vol - ask_vol) / (bid_vol + ask_vol)` |
| **Cumulative Depth Imbalance** | 深さ別 imbalance | 上記を level L=5,10,20 で集計 |
| **Trade Imbalance** | 直近 N trade の buy/sell 偏差 | `(buy_vol - sell_vol) / total_vol` |
| **Taker Ratio** | 直近 N trade の taker 比率 | `taker_vol / total_vol` (= aggressive flow) |
| **VPIN (Volume-Synchronized PIN)** | 注文 toxicity (= informed trader 比率) | volume bucket 内の order flow imbalance / total volume |
| **Funding Rate** | perpetual 特有・long/short 圧力 | Bitget 8h 精算値・現状 cat-bitget は単一 baseline 値で扱い |
| **Open Interest (OI)** | 全市場ポジション規模 | Bitget Public API |
| **OI Delta / OI ROC** | OI 変化率 | 短期反転 / breakout 補助 |

#### 業界実証 (= BTC 5m / perpetual)

- [Order Book Imbalance Cryptocurrency (Towards Data Science)](https://towardsdatascience.com/price-impact-of-order-book-imbalance-in-cryptocurrency-markets-bf39695246f6/): OBI が high のとき市場注文増加 + price move predict 力あり
- [OBI Predict Price Moves (Medium)](https://medium.com/@thewealthacademyyt/how-order-book-imbalances-predict-price-moves-before-they-happen-crystal-ball-series-part-2-fd9fc66f86a5): 短期 mid-price move の先行指標
- [Nowcasting BTC Crash Risk (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10040314/): order imbalance で crash risk nowcast
- [Microstructure ML (arxiv 2506.05764)](https://arxiv.org/html/2506.05764v2): 9 microstructure measures × stability selection + SHAP + purged walk-forward で BTC + 5 alts に適用 (300 万 minute-level obs)
- [Explainable Patterns (arxiv 2602.00776)](https://arxiv.org/html/2602.00776v1): BTC/LTC/ETC/ENJ/ROSE で order book features の SHAP dependence shapes が cross-asset で stable (= Binance Futures perpetual 1s freq・2022-01〜2025-10)
- [Microstructure Alpha (Frontiers 2026)](https://www.frontiersin.org/journals/blockchain/articles/10.3389/fbloc.2026.1811716/abstract): hierarchical learning + cross-asset transfer
- [Cryptocurrency Perpetual Futures (MDPI 2026)](https://www.mdpi.com/2227-7072/14/5/103): 26 exchanges / 812 symbols で funding rate correlation + arbitrage prevalence + volatility persistence
- [BTC Futures High-Frequency (ScienceDirect 2025)](https://www.sciencedirect.com/science/article/pii/S2214845025001188): BTC futures market microstructure 検証
- [hftbacktest Tutorial](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html): market making 戦略で OBI alpha 使用

#### cat-bitget 現状 verify (= 機械的証跡)

- Phase 0 特徴量カタログ (1432 + Phase 0 v3 補強 2604) に **OBI / Cumulative Depth / VPIN / Taker Ratio / OI Delta はゼロ** (= 推定・要 grep verify)
- Funding Rate は `exchange_spec.md` で 8h baseline 値として扱うが、ML 入力としては未使用 (= 静的固定値運用)
- → **微細構造系は cat-bitget の最大の伸びしろ領域**

#### cat-bitget 適用判断 (= 工程 3 入力 + Phase 0 v4 必須拡張)

- **データ取得**: Bitget WebSocket API (= `books5` / `books15` depth subscribe) で order book snapshot + trade stream を取得
- **Phase 0 v4 追加候補 (= 業界実証多い順)**:
  1. `book_imbalance_L{5,10,20}__1s_avg_5m` (= 1s 板スナップから 5m 集約) — 高優先度
  2. `taker_ratio__{1m,5m,15m}` (= aggressive flow proxy) — 高優先度
  3. `bid_ask_spread_bps__5m_avg` (= 流動性 proxy) — 中優先度
  4. `funding_rate_8h` + `funding_rate_delta_24h` (= 既存 baseline 値を時系列入力化) — 中優先度
  5. `open_interest__{1h,4h}` + `oi_roc_1h__{5m,1h}` (= Bitget Public API) — 中優先度
  6. `vpin_bucket_50__1h` (= 業界実装 mlfinlab.microstructural_features) — 低優先度 (= 実装重い)
- **業界整合**: arxiv 2602.00776 + 2506.05764 + Frontiers 2026 + MDPI 2026 の 4 件で BTC/perpetual 5m / 1s freq 実証あり
- **Phase 7-c 実装影響**: bot 起動時に Bitget WebSocket 2-3 streams + 1s 集計が必要 (= 推論レイテンシ余裕は十分・5m bot)

### §16.7 領域 3 まとめ: 7 工程接続 + 設計判断調査ノート

| 工程 | 特徴量設計の改善方向 |
|---|---|
| 1 regime | HMM/GMM 入力に MTF (= 4h+1d) + ATR/ADX/realized_vol 統合 |
| 2 Entry 候補生成 | (固定ロジック・特徴量設計対象外) |
| **3 Entry ML** | **(a) Volume bar 並行入力 / (b) Fractional Diff 24 特徴量追加 / (c) 出来高系 48 特徴量追加 / (d) microstructure 10-15 特徴量追加 / (e) Clustered MDA で 2604 → 500-1000 削減** |
| 4 Position Sizing | volatility prediction 特徴量 (= HAR-RV 入力) を強化 |
| 5 Exit ML | PPO 入力に order book imbalance + taker ratio + position 含み益 % を含める |
| 6 Risk 管理 | spread / OI delta / VPIN を固定ルール閾値で使う |
| 7 Online 監視 | feature distribution drift detection (= §17.8 で別途) |

> ⚠️ 上記は **学習資料の調査ノート位置付け**。設計確定は WORKFLOW 改訂36 active 優先 3 (= 工程 2-7 詳細詰め) で別途実施 (cc_role §1.5)。

---

## §17 ML 評価方法 (WORKFLOW 改訂36 領域 4・業界カタログ)

> v3 追記 (2026-05-XX)。**「どう検証して合格判定するか」の業界カタログ**。Phase 1 v6 6 案全滅で feature_importance 上位 = ボラ系支配と確認できたが (= L-223)、本章では **検証フロー側の業界標準** = Purged K-Fold / CPCV / DSR / PBO を整理。cc_role §1.4.6.1 #9 (= 統計指標と PnL 指標の分離) の業界実装パターンを確立する。

### §17.1 Walk-Forward 検証 (rolling vs expanding)

#### 業界 2 方式

| 方式 | window 設計 | 業界用途 | 弱点 |
|---|---|---|---|
| **Expanding Window** | train 始点固定・末尾を段階的に拡張 | 「全履歴を活用」必要時 | 古い regime の影響残留 |
| **Rolling Window** | train を固定長で前進 | 「直近 N 期間」が予測力高い時 (= regime 変化対応) | 古い情報の完全喪失 |

#### Embargo の併用 (= AFML Ch.7 推奨)

- train end と test start の間に N% の embargo gap を入れる
- 理由: serial correlation で label が test 領域に染み出すのを防ぐ (= leakage 防止)
- 業界相場: 1-5% embargo (= データサイズに応じて)

#### 教科書整合 + 出典

- [Walk-Forward Optimization (Grokipedia)](https://grokipedia.com/page/Walk_forward_optimization): 概念全般
- [Walk-Forward CVCL (Quant Beckman)](https://www.quantbeckman.com/p/with-code-walk-forward-cvcl-optimization): 実装コード付き
- [Walk-Forward Modeling (Alpha Scientist)](https://alphascientist.com/walk_forward_model_building.html): 株式予測での実装例
- [Walk-Forward + XGBoost (QuantInsti)](https://blog.quantinsti.com/walk-forward-optimization-python-xgboost-stock-prediction/): Python + XGBoost 実装
- [Walk-Forward Limitations (QuantInsti)](https://blog.quantinsti.com/walk-forward-optimization-introduction/): 弱点 (= regime shift に反応的 / 計算重い)

#### Phase 1 v6 6 案との関係

- 案 a-f は **Walk-Forward Purged K-Fold 5 fold** を採用 (= phase_flow_v4 v7 §1.5)
- 単一 train/valid/test split より業界整合・leak 防止構造あり
- ただし fold = 5 のみで CPCV (= 後述 §17.3) の多パス検証は未採用

#### cat-bitget 適用判断 (= 工程 3 Entry ML / 工程 5 Exit ML 検証)

- **主軸維持**: Walk-Forward Purged K-Fold 5 fold (= 現状継続)
- **embargo 値**: 5m × Phase 0 ラベル K=24/48/96 → embargo = K bar (= 2h-8h) で設定
- **検討候補**: rolling vs expanding は cat-bitget 5y データ規模 (= 525,600 bar) なら **expanding** で十分 (= 過去 4 年累積 + 直近 1 年で valid)

### §17.2 Purged K-Fold Cross-Validation (AFML Ch.7)

#### 業界の根本問題

- 通常の K-Fold CV は random shuffle で fold 分割 → 時系列で「未来→過去」順序の混乱 + label overlap で leak
- 金融データ特有: label 形成時間 (= TP/SL/time exit 到達まで) が train fold と test fold で overlap する

#### Purging の手順 (AFML Ch.7・Lopez de Prado 2017)

1. test fold を選択
2. test fold 内 sample の label 形成時間 (= start_time ~ end_time) を識別
3. **train fold から、label 形成時間が test fold の時間範囲と overlap する sample を除去** (= purge)
4. 残った train fold で fit / test fold で score

#### Embargo の追加

- purge だけでは「indirect leak」(= test event の市場反応が train fold sample に影響) を防げない
- → test fold の後ろに N% embargo gap を追加して train fold から除外
- 業界相場: 1-5% (= cat-bitget 5y データなら 1 fold ≈ 1y → embargo ≈ 18-90 day)

#### 教科書整合 + 出典

- [Purged Cross-Validation (Wikipedia)](https://en.wikipedia.org/wiki/Purged_cross-validation): 概念 + Lopez de Prado 2017 起源
- [Purging + Embargo Tutorial (Medium)](https://antonio-velazquez-bustamante.medium.com/kfold-cross-validation-with-purging-and-embargo-the-ultimate-cross-validation-technique-for-time-2d656ea6f476): 実装解説
- [CV in Finance (QuantInsti)](https://blog.quantinsti.com/cross-validation-embargo-purging-combinatorial/): purging / embargo / combinatorial の業界整合解説
- [10 Reasons ML Funds Fail (GARP)](https://www.garp.org/hubfs/Whitepapers/a1Z1W0000054x6lUAA.pdf): Lopez de Prado 2018 — 多重検定 / 検証不適切 / leak 等 ML fund 失敗 10 要因
- [AFML notes (Reasonable Deviations)](https://reasonabledeviations.com/notes/adv_fin_ml/): AFML 各章のサマリ

#### Phase 1 v6 6 案との関係

- 案 a-f で Purged K-Fold 5 fold + embargo を採用済 → leak 防止構造は業界整合
- ただし「fold 数 5」「embargo 値」が業界相場と整合か再 verify 余地あり

#### cat-bitget 適用判断 (= 工程 3 / 工程 5 検証主軸維持)

- **現状 (= Phase 1 v6) を維持**: Walk-Forward Purged K-Fold 5 fold + embargo K bar
- **追加検討**: embargo 値の sensitivity test (= K, 2K, 3K で score 差) → 適正値確定

### §17.3 CPCV (Combinatorial Purged Cross-Validation・AFML Ch.7)

#### 業界の根本問題

- 通常の K-Fold CV (= Purged 版も含む) は **single-path testing** = 1 つの train/test 順序のみ
- 真の Sharpe 分布は推定できず・PBO (= 後述 §17.5) を低くできない

#### CPCV の手順

1. N 個の groups に分割 (= 通常 N=6-10)
2. k 個の groups を test に充てる組合せ全列挙 (= C(N, k) 通り)
3. 各組合せで purge + embargo した後 fit / score
4. → 複数 backtest paths の分布が得られる → robust statistical inference 可能

#### 業界実証

- [CPCV Wikipedia](https://en.wikipedia.org/wiki/Purged_cross-validation): CPCV は Bailey & Lopez de Prado 2014 で提案
- [Combinatorial Purged CV (Quant Beckman)](https://www.quantbeckman.com/p/with-code-combinatorial-purged-cross): 実装コード付き
- [CPCV for DRL (Towards AI)](https://towardsai.net/p/l/combinatorial-purgedkfold-cross-validation-for-deep-reinforcement-learning): Deep RL に CPCV を適用
- [Backtest Overfitting Comparison (ScienceDirect 2024)](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110): out-of-sample testing methods の synthetic environment 比較 → **CPCV が PBO 最低・DSR 最高**
- [SSRN Insights (Scribd)](https://www.scribd.com/document/725401650/SSRN-id4778909): CPCV 概要

#### cat-bitget 適用判断 (= Phase 1 v7 検討候補)

- **検討候補**: 案 e (= Triple Barrier multiclass) を CPCV 6 groups / k=2 で再評価 → backtest paths 分布の標準偏差を report
- **計算コスト**: CPCV は C(6,2) = 15 paths → 案 e 単独 110 分 × 15 ≈ 27 時間 = 1 セッション規模・実行可能
- **業界整合 verify**: ScienceDirect 2024 の synthetic environment 実証で CPCV 優位 → 採用判断材料あり

### §17.4 Deflated Sharpe Ratio (DSR・AFML Ch.14)

#### 業界の根本問題

- 通常の Sharpe Ratio は 2 つの inflation を持つ:
  1. **Selection bias**: 多数試行から best を選ぶと Sharpe が過大評価される
  2. **Non-Normality**: returns 分布が正規 (skewness 0 / kurtosis 3) でないと SR の標準誤差が過小評価
- → Sharpe ≥ 1.0 でも DSR < 0.5 なら「偶然の産物」可能性大

#### DSR 計算式 (Bailey & Lopez de Prado 2014)

- DSR = Z(SR_observed, SR_expected_chance, σ_SR, skewness, kurtosis, N_trials, T)
- 入力:
  - 観測 Sharpe (= SR)
  - returns の skewness / kurtosis (= 非正規性補正)
  - 試行数 N (= 多重検定補正)
  - 期間長 T
- 出力: DSR = P(SR が偶然でないか) — 業界閾値 = DSR > 0.95 で合格

#### 教科書整合 + 出典

- [DSR Wikipedia](https://en.wikipedia.org/wiki/Deflated_Sharpe_ratio): 概念 + Bailey & Lopez de Prado 2014
- [Bailey & LdP 2014 SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551): 原論文
- [Deflating Sharpe Ratio SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2465675): 計算式詳細
- [DSR PDF (Bailey + Lopez de Prado)](https://pdfs.semanticscholar.org/c215/d0a2064ce1a3565d276475abc84305418f0f.pdf): 数式 + 実装ガイド
- [DSR Tutorial (Medium Balaena Quant)](https://medium.com/balaena-quant-insights/deflated-sharpe-ratio-dsr-33412c7dd464): 平易解説

#### ONC (Optimal Number of Clusters・実効試行数推定)

- DSR の入力 N (= 試行数) は「実効的に独立な試行数」を要求 (= 単純 grid search 全数では過大)
- Lopez de Prado は ONC algorithm で「類似戦略を unsupervised clustering で集約 → cluster 数 = 実効 N」を提案

#### Phase 1 v6 6 案との関係

- 案 a-f は DSR 評価未実施 (= phase_flow_v4 v7 §1.5 に DSR 項目あるが具体実装は未 verify)
- 「TP precision 0.43 頭打ち + combos_pass 0/8」は DSR 計算しても合格水準に届かない可能性大

#### cat-bitget 適用判断 (= Phase 5 Replay 合格判定追加)

- **追加候補**: 月次 NET ≥ $1,900 (= cc_role / CLAUDE.md 必達) の判定に **DSR > 0.95** を併用
- **理由**: 月次 12 ヶ月クリアでも DSR < 0.95 なら「偶然による達成可能性」が残る → 本番投入リスク
- **実装**: `pyfolio` / `quantstats` / mlfinlab.backtest_statistics.DeflatedSharpeRatio で計算可

### §17.5 PBO (Probability of Backtest Overfitting・Bailey 2014)

#### 業界の根本問題

- 多数 strategy configuration を grid search で試すと「best が偶然」の確率が増加
- 学術界では「論文の半数以上が backtest overfit」(= Bailey 2014 — pseudo-mathematics) と批判

#### PBO 計算手順 (CSCV: Combinatorially Symmetric Cross-Validation)

1. backtest 期間を N submatrices に分割 (= 通常 N=16)
2. C(N, N/2) 通りの train/test 組合せ全列挙
3. 各組合せで in-sample best 戦略を選択 → out-of-sample rank 計算
4. OOS rank が median (= 中央値) 未満の確率 = **PBO**
5. 業界閾値: PBO < 0.5 で合格・< 0.2 で robust

#### 教科書整合 + 出典

- [PBO 原論文 (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253): Bailey, Borwein, Lopez de Prado, Zhu 2013
- [Pseudo-Mathematics Bailey 2014 PDF](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf): 強烈な業界批判 + PBO の理論
- [Pseudo-Math (Scholarworks)](https://scholarworks.wmich.edu/math_pubs/40/): 学術版
- [pypbo GitHub](https://github.com/esvhd/pypbo): Python 実装 (= MIT license)
- [SDM Bailey paper](https://sdm.lbl.gov/oapapers/ssrn-id2507040-bailey.pdf): Statistical Overfitting and Backtest Performance

#### Phase 1 v6 6 案との関係

- 案 a-f は **6 案 × 8 combo = 48 試行** → PBO 計算未実施
- 48 試行は CSCV N=16 で評価可能規模

#### cat-bitget 適用判断 (= Phase 5 / 6-b 合格判定追加)

- **追加候補**: Phase 5 365d Replay (= 12 ヶ月クリア判定) に **PBO < 0.5** を併用
- **理由**: 多数 cluster × Exit type の grid search を実施するため、最終採用前に overfitting 確率を verify する義務
- **実装**: `pypbo` ライブラリ (PyPI) または mlfinlab.backtest_statistics

### §17.6 統計指標 vs PnL 指標の分離 (= cc_role §1.4.6.1 #9 整合)

#### 業界の根本ルール

| 指標カテゴリ | 役割 | 業界使用フェーズ |
|---|---|---|
| **統計指標** (entropy_lift / TP precision / log_loss / AUC) | 学習中の **進捗 verify** + leak 検出 | Phase 1-3 (= 学習 + ハイパラ) |
| **PnL 指標** (月次 NET / Sharpe / DSR / max DD / Sortino) | **本格判定** + 本番投入可否判定 | Phase 5-6-b (= Replay + 本テスト) |

#### cc_role §1.4.6.1 #9 との連携

- 提案する合格基準が **統計指標 / PnL 指標 / 混合のいずれか** を明示する義務
- 混合した瞬間に L-220 同型違反として記録

#### 業界実装パターン

- Phase 1-3 で TP precision / entropy_lift / DSR_train で進捗 verify
- Phase 4-5 で月次 NET / Sharpe / DSR_test / PBO で本格判定
- 「TP precision > 0.5 なら採用」のような **統計指標で本格判定** は禁止 (= L-220 事案)

#### cat-bitget 適用判断 (= 全 Phase 共通)

- **Phase 1 v6 評価軸 (= entropy_lift / TP precision / log_loss / AUC / OOS metric 5 指標)** は統計指標として正しい (= L-217 改訂で Exit シミュ排除済)
- **Phase 5 / 6-b 合格判定** は月次 NET ≥ $1,900 + DSR + PBO の **PnL 指標主軸**に維持
- **混合禁止**: 「Phase 1 で月次 NET 推定」「Phase 5 で TP precision で打ち切り」は L-220 同型で禁止

### §17.7 データリーク防止 (= scaler / TimeSeriesSplit / Pipeline)

#### 業界の必須回避リスト (= cat-bitget 既存 L-179 fractal leak / L-181 価格依存性 verify と同型)

| leak 種類 | 発生原因 | 防止方法 |
|---|---|---|
| **Scaler leak** | `scaler.fit(全データ)` で test 統計量混入 | `Pipeline + TimeSeriesSplit` で fold 毎 fit |
| **Time leak** | random shuffle CV で 未来→過去 順序破壊 | `TimeSeriesSplit` または Purged K-Fold |
| **Label leak** | label 形成時間が test fold と overlap | Purging (= §17.2) |
| **Indirect leak** | test event の市場反応が train sample に影響 | Embargo (= §17.2) |
| **Future feature** | `shift(-N)` / `center=True` rolling | grep + 静的解析 (= L-179 経験) |

#### 教科書整合 + 出典

- [scikit-learn Common Pitfalls 11](https://scikit-learn.org/stable/common_pitfalls.html): 公式 leak 防止
- [Data Leakage Visual Guide (Towards Data Science)](https://towardsdatascience.com/data-leakage-in-preprocessing-explained-a-visual-guide-with-code-examples-33cbf07507b7/): 視覚解説
- [Avoid Data Leakage (MachineLearningMastery)](https://machinelearningmastery.com/data-preparation-without-data-leakage/): preprocessing 全般
- [Understanding Data Leakage (NBD Lite)](https://www.nb-data.com/p/understanding-data-leakage-in-machine): NBD #12

#### cat-bitget 適用判断 (= 全 Phase 共通 + cc_role §1.4 #4 警戒)

- **既存 feedback_ml_leak_mandatory_check.md** (= L-179 fractal leak 由来) と整合
- **Phase 0 v4 拡張時の追加 verify**: 出来高系 / microstructure 追加時に必ず 4 leak チェック (= L-179 feedback 4 項目) を実施
- **scaler の fold 毎 fit**: Phase 1 v7 改修候補 (= 現状の implementation を grep verify 要)

### §17.8 概念 drift 検出 (= 工程 7 Online 監視・運用層)

#### 業界 3 系統

| 手法 | 仕組み | 業界用途 |
|---|---|---|
| **KL Divergence** | 訓練分布 P vs 本番分布 Q の情報量差 | feature distribution drift 検出 |
| **Wasserstein Distance** | 分布間 optimal transport cost | KL より外れ値耐性高い |
| **Page-Hinkley Test** | 平均変化検出 (= sequential) | online 単変量モニタ |

#### 業界実装パターン

- 推論時に feature distribution を訓練時と比較 → drift 検出時に alert / 再学習トリガ
- 業界相場: 1 週間に 1 回 drift verify / 月 1 で feature importance re-evaluation

#### cat-bitget 適用判断 (= Phase 7-c / 7-d 実装候補)

- **次段検討**: bot 運用後 1 ヶ月で feature distribution が 5% 以上 KL drift したら alert
- **実装**: scikit-multiflow / river ライブラリで実装可

### §17.9 領域 4 まとめ: 7 工程 + 全 Phase 接続

| 工程 / Phase | 評価方法主軸 | 業界整合手法 |
|---|---|---|
| Phase 1 (学習・統計指標) | Walk-Forward Purged K-Fold 5 fold + embargo | AFML Ch.7 |
| Phase 1 v7 候補 | CPCV (= C(6,2) = 15 paths) で robustness 強化 | AFML Ch.7 + ScienceDirect 2024 |
| Phase 5 (Replay・PnL 指標) | 月次 NET ≥ $1,900 全月クリア (現状) + **DSR > 0.95 + PBO < 0.5** | AFML Ch.14 + Bailey 2014 |
| Phase 6-b (本テスト) | 同 Phase 5 + 単月未達ゼロ (現状) + DSR + PBO | 同上 |
| 工程 3 Entry ML | Purged K-Fold + Clustered MDA で feature 選択 | AFML Ch.7-8 |
| 工程 5 Exit ML | RL の場合は Walk-Forward + 各 fold で PPO 再学習 | 業界 RL 評価標準 |
| 工程 7 Online 監視 | KL divergence + Page-Hinkley | scikit-multiflow / river |

> ⚠️ 上記は **学習資料の調査ノート位置付け**。設計確定は WORKFLOW 改訂36 active 優先 3 (= 工程 2-7 詳細詰め) で別途実施 (cc_role §1.5)。

---

## §18 ML 組合せ手法 (WORKFLOW 改訂37 領域 5・業界カタログ)

> v4 追記 (2026-05-25)。**「複数の学習器・複数の予測層・複数の戦略をどう組み合わせるか」の業界カタログ**。Phase 1 v6 案 a-f が **全 LightGBM・全 5m time bar・全 LONG/SHORT 並列学習** = 多様性ゼロで全滅した事案 (L-223 + L-224) を受けて、業界の「アンサンブル多様性確保」「多段 cascade」「階層的配分」「Meta-Labeling 多段化」の 4 軸を整理。ChatGPT 7 工程フレームの工程 3 (Entry ML アーキ) + 工程 4 (Position Sizing 配分) + 工程 5 (Exit ML 統合) に直結。

### §18.1 階層 Stacking (= 異種アルゴリズムの meta-learner 統合)

#### 業界 3 系統の組合せ手法 (再掲・AFML Ch.6 + 業界実装)

| 手法 | 仕組み | 多様性源 | 業界用途 |
|---|---|---|---|
| **Bagging** (Bootstrap Aggregating) | 同型 base learner を bootstrap sample で並列学習・平均 | データ多様性 | Random Forest |
| **Boosting** | 逐次的に前モデルの誤差を補正 | bias 低減 | LightGBM / XGBoost / CatBoost |
| **Stacking (= 階層 Stacking)** | 異種アルゴ (= GBDT + DL + RL) の OOF (out-of-fold) 予測を meta-learner で統合 | **アーキテクチャ多様性** | プロ Quant 標準 |
| **Blending** | Stacking の簡易版 (= holdout set 1 つで meta 学習) | 同上 | 計算軽量 |
| **Bayesian Model Averaging (BMA)** | 各モデルに事後確率 weight を付けて平均 | 確率的 weighting | non-stationary 環境向き |

#### Stacking の業界実装パターン

##### Level 0 (= base learners・異種で並列学習)

業界推奨の base learner 組合せ (= ensemble diversity 確保):

1. **GBDT 系** (= LightGBM / XGBoost / CatBoost): tabular 入力の予測力高・速い
2. **時系列 DL 系** (= GRU / LSTM / Transformer / TFT): long-range pattern 捕捉
3. **時系列特化 ML** (= MiniROCKET / TSFresh): 時系列分類の SOTA
4. **線形系** (= Logistic Regression / Ridge): bias 低・robust なベースライン
5. **RL 系** (= PPO の確率出力): 動的状況適応

##### Level 1 (= meta-learner・予測を統合)

業界推奨の meta-learner 選択:

| meta-learner | 業界用途 | 弱点 |
|---|---|---|
| **Logistic Regression** | 業界 default・線形 weighting・解釈容易 | 非線形相互作用無視 |
| **Ridge / Lasso** | base learner 過多時の正則化 | weight が小さくなりすぎる傾向 |
| **XGBoost / RF (= meta)** | 非線形 weighting | 過学習リスク |
| **NN (= MLP・1-2 hidden)** | 高表現力 | データ要件大 |

##### Out-of-Fold (OOF) Prediction の必須性

- **stacking で最重要の leak 防止構造**: meta-learner は base learner が **見ていないデータ** の予測で学習する義務
- 実装: `sklearn.model_selection.cross_val_predict` または mlfinlab の Purged K-Fold OOF
- **時系列固有 (cat-bitget 該当)**: 通常の `cross_val_predict` (= random shuffle) は時系列で leak → **Purged K-Fold + Embargo** で OOF を生成必須 (= §17.2 整合)

#### 教科書整合 + 出典

- AFML **Ch.6 Ensemble Methods**: Lopez de Prado「Combining diverse learners can improve robustness, mitigate overfitting, and extract persistent patterns from noisy financial time series」を引用 ([Ensemble Methods ML Wikipedia](https://en.wikipedia.org/wiki/Ensemble_learning) + [Baeldung CS](https://www.baeldung.com/cs/bagging-boosting-stacking-ml-ensemble-models) + [MachineLearningMastery](https://machinelearningmastery.com/demystifying-ensemble-methods-boosting-bagging-and-stacking-explained/))
- [Stacking Ensembles XGBoost/LightGBM/CatBoost (Medium・Stephen Echessa)](https://medium.com/@stevechesa/stacking-ensembles-combining-xgboost-lightgbm-and-catboost-to-improve-model-performance-d4247d092c2e): 業界 default 構成・10-20% accuracy gain on tabular
- [Stacking Ensemble Learning Combining XGBoost/LightGBM/CatBoost/AdaBoost + RF meta (ResearchGate 397047638)](https://www.researchgate.net/publication/397047638): meta = Random Forest 構造の業界実証
- [Bitcoin Stacking Ensemble (MDPI Math 2022・10/8/1307)](https://www.mdpi.com/2227-7390/10/8/1307): LSTM + GRU stacking で BTC 次 30 分 price prediction
- [arxiv 2512.15738 Hybrid Quantum-Classical Ensemble S&P500](https://arxiv.org/pdf/2512.15738): **architecture diversity (= 60.14%) > dataset diversity (= 52.80%)** + **同一アーキ間 correlation r > 0.6** を実証 → cat-bitget の Phase 1 v6 6 案 (= 全 LightGBM) 全滅の構造的根拠
- [arxiv 2411.03035 GAS Blending](https://arxiv.org/html/2411.03035v1): Genetic Algorithm 生成 Alpha + Sentiment で BTC trend prediction の blending ensemble
- [arxiv 2501.10709 FinRL Contest 2023-2024](https://arxiv.org/pdf/2501.10709): RL ensemble で stock / crypto trading の risk-return trade-off 強化
- [Stacking GAS + LightGBM 解説 (johal.in 2025)](https://johal.in/ensemble-learning-methods-xgboost-and-lightgbm-stacking-for-improved-predictive-accuracy-2025/): 10-15% accuracy uplift via meta-learning

#### Phase 1 v6 6 案との関係

- 案 a-f は **全 LightGBM** (= §13.1 + L-224 で確定) → architecture diversity ゼロ
- arxiv 2512.15738 の実証「same architecture between r > 0.6 correlation → ensemble 効果薄」と整合 → 案 a-f は stacking しても本質改善困難な構造
- 案 f Meta-Labeling 失敗も同型: primary も secondary も同じ LightGBM → secondary が primary の盲点を補えない (= QuantConnect [Meta-Labeling not a silver bullet](https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/) 整合)

#### cat-bitget 適用判断 (= 工程 3 Entry ML アーキ強化候補・Phase 1 v7 案)

- **Level 0 (= base learners) 業界推奨 3 種**:
  1. **LightGBM** (= 現案 e ベース・高速・大規模) — 維持
  2. **XGBoost** (= Sharpe / DD で LightGBM 優位事例・§13.1 + Data Moves Me 実証) — 追加候補
  3. **GRU or TFT (= DL 系 1 種)** — 追加候補 (= 学習時間 vs 効果検証して片方採用)
- **Level 1 (= meta-learner)**: Logistic Regression を default。理由 = 線形 weighting + 解釈容易 + base learners が GBDT 中心で非線形性は既に捕捉済
- **OOF 生成**: Purged K-Fold 5 fold + Embargo K bar (= §17.2 整合) で leak 防止
- **多様性 verify 義務**: 採用前に base learners の予測 correlation r を測定 → r > 0.6 → 同型バイアスとして diversification 失敗 → 別 base 検討
- **Phase 1 v7 候補規模**: 1 base learner × 110 分 (= 案 e) × 3 base + meta 学習 30 分 = 約 7 時間 / 1 セッション規模で実行可能

### §18.2 Cascade / 多段 Filter (= 偽信号の段階削減)

#### 業界の根本構造 (= Viola-Jones cascade に由来する金融応用)

Cascade は「**accuracy が高く必要だが大半の入力は negative**」状況で「**早期 reject + 段階的に高 cost classifier を適用**」する設計。crypto 5m bot の Entry 判定は典型的にこの構造:

- 全 5m bar の中で「ML が long/short 候補」と判定するのは数 % のみ
- 偽信号を後段で reject する方が「全段で同じ厳しさ」より計算効率 + precision 高い

#### Viola-Jones Cascade 業界数値 (= 金融転用の基礎)

| 段数 | 役割 | 業界実証 (face detection) |
|---|---|---|
| 段 1 | 高 recall・低 cost (= 2 feature) | FN ~0% / FP 40% — **95% の negative を即 reject** |
| 段 2-3 | 中 recall・中 cost | 残り negative の大半を reject |
| 段 N (= 38) | 最高 precision・最大 cost | total cascade detection rate 90% (= 各段 99.7% で連乗) |

#### 金融機械学習への転用パターン

| Cascade 段 | 役割 | base learner 例 |
|---|---|---|
| 段 1 (= candidate gen) | 高 recall・低 cost・大半の bar を reject | 固定ロジック (= ATR > threshold + ADX > 25 等)・cat-bitget 工程 2 (Entry 候補生成) |
| 段 2 (= primary ML) | 中 recall・中 cost・false positive 削減 | LightGBM (= 高速・OOF 予測) |
| 段 3 (= secondary ML) | 高 precision・高 cost・最終確定 | XGBoost or Meta-Labeling secondary (= §18.4) |
| 段 4 (= size 決定) | 高 precision・size 確率を出力 | Half-Kelly / HRP cluster 配分 (= §18.3) |

#### 業界実証 (= 偽信号削減効果)

- [Ensemble Learning Cuts False Positives 30% (LuxAlgo)](https://www.luxalgo.com/blog/ensemble-learning-for-chart-patterns/): ensemble methods で false positive 30% 削減・risk management 強化
- [Cascading Classifiers Wikipedia](https://en.wikipedia.org/wiki/Cascading_classifiers): cascade 構造の業界 default 解説
- [Cascading Classifiers — Grokipedia](https://grokipedia.com/page/Cascading_classifiers): 多段 reject 構造の数式
- [Classifier Cascade ScienceDirect Topic](https://www.sciencedirect.com/topics/computer-science/classifier-cascade): industry survey
- [Saugata Paul Medium — Bagging/Boosting/Stacking/Cascading](https://medium.com/@saugata.paul1010/ensemble-learning-bagging-boosting-stacking-and-cascading-classifiers-in-machine-learning-9c66cb271674): Python SKLEARN + MLEXTEND 実装比較

#### Phase 1 v6 6 案との関係

- 案 a-f は **単段 (= ML 単独 entry 判定)** → cascade 構造なし
- 案 f Meta-Labeling は **2 段 (= primary + secondary)** だが、両段とも同じ LightGBM・regime 不在ラベル → cascade の多様性効果なし
- 「TP precision 0.43 頭打ち」(= L-223) は cascade 段数不足の補強原因として整理可能

#### cat-bitget 適用判断 (= 工程 2 + 工程 3 + 工程 4 接続候補)

- **3 段 cascade 構造案**:
  - **段 1 (= 工程 2 Entry 候補生成)**: 固定ロジック (= 旧 Priority カバー範囲 + 業界標準 ATR/ADX/RSI シグナル組合せ) で全 bar の数 % まで絞る・高 recall 目標
  - **段 2 (= 工程 3 primary ML)**: LightGBM (= 案 e 構造) で段 1 残りを binary 分類 (= TP first 確率)・false positive 削減目標
  - **段 3 (= 工程 3 secondary ML)**: XGBoost or Meta-Labeling secondary で段 2 残りを確率 calibrate・最高 precision 目標
- **閾値設計**: 各段の threshold は train fold で grid search・採用は OOF 性能 (= 全段通った後の TP precision + entropy_lift) で判断
- **計算コスト**: 段 1 高速・段 2-3 は段 1 残り bar のみ実行 → 全段単独実行より低コスト
- **業界注意**: cascade の総 detection rate = 各段 detection rate の連乗 → 段数増やすほど total recall 低下 → 段数 3-4 を上限目安

### §18.3 Hierarchical Risk Parity (HRP) + HERC + NCO (= Lopez de Prado 2016+2018)

#### 業界の根本問題 (= Markowitz Curse)

Mean-Variance Optimization (MVO・1952) の構造的欠陥:

1. **数値不安定**: 共分散行列の逆行列計算が条件数悪 → 小さな入力変化で weight 激変
2. **集中**: 数銘柄に weight 集中・分散効果 minimal
3. **OOS underperformance**: IS で min variance でも OOS で高 variance ([Wikipedia HRP](https://en.wikipedia.org/wiki/Hierarchical_Risk_Parity) + [Finexus Markowitz Curse](https://api.finexus.net/api/news/events/a4a54b61-d80a-47c9-897c-b301d4d799bb/html))

#### HRP の 3 ステップ (Lopez de Prado 2016・SSRN 2708678 原論文)

1. **Hierarchical Tree Clustering** (= 階層クラスタリング):
   - 相関行列 → 距離行列 (= `sqrt(0.5 * (1 - corr))`) → linkage で dendrogram 構築
   - linkage 方式: single (= default) / complete / ward
2. **Matrix Seriation / Quasi-Diagonalization** (= 共分散行列の並べ替え):
   - 似た資産が隣接するように行列を並べ替え
   - block-diagonal 構造に近づける
3. **Recursive Bisection** (= 再帰二分配分):
   - dendrogram を再帰的に 2 分割
   - 各分割で **inverse variance weighting** (= 各 cluster の variance に反比例) で weight 配分

**特徴**: 共分散行列の逆行列を計算しない → 特異・近特異行列でも動作可能 ([Wikipedia](https://en.wikipedia.org/wiki/Hierarchical_Risk_Parity))

#### 業界実証 (= MVO 比較)

- [Lopez de Prado 2016 SSRN 2708678](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678): 「**HRP delivers lower out-of-sample variance than CLA, even though min variance is CLA's optimization objective**」 — IS 性能と OOS 性能の逆転
- [Finexus Markowitz Curse Article](https://api.finexus.net/api/news/events/a4a54b61-d80a-47c9-897c-b301d4d799bb/html): MVO は IS で min vol だが OOS で高 vol・HRP が OOS best
- [ResearchGate 379202955 Theoretical Evidence](https://www.researchgate.net/publication/379202955): HRP の Markowitz curse 解決の理論的根拠
- [ScienceDirect HRP Real World Analysis](https://www.sciencedirect.com/science/article/abs/pii/S0167739X25000391): 効率的実装 + 実環境分析
- [Quantopian HRP vs Diversification](https://www.quantopian.com/posts/hierarchical-risk-parity-comparing-various-portfolio-diversification-techniques): 各種 diversification 比較

#### crypto 適用の実証 (= 重要な限界事例)

- [ScienceDirect S154461232030177X (Beyond Risk Parity・crypto)](https://www.sciencedirect.com/science/article/abs/pii/S154461232030177X): crypto portfolio に HRP 適用・MVO より robust
- [PyPortfolioOpt Crypto HRP Tutorial (alexeygolev.blog)](https://alexeygolev.blog/hierarchical-risk-parity-hrp-for-crypto-portfolio-optimisation/): Python 実装事例
- **限界事例**: 「**Bitcoin hold outperformed HRP variants over 3 years**」 — 単一資産優位な期間では HRP は overhead になる ([ResearchGate Beyond Risk Parity](https://www.researchgate.net/publication/340893952))

#### HERC (Hierarchical Equal Risk Contribution・Raffinot 2018)

HRP の発展形 ([Hudson & Thames HERC](https://hudsonthames.org/beyond-risk-parity-the-hierarchical-equal-risk-contribution-algorithm/)):

1. Hierarchical Clustering で cluster 構造構築
2. **最適 cluster 数** を gap statistic 等で決定
3. **Top-Down 再帰**: dendrogram を上から再帰的に分割・各 cluster に **Equal Risk Contribution** で配分
4. cluster 内は naive risk parity (= HRP と同)

**HRP との差**: cluster の境界を明示的に決める (HRP は暗黙的 bisection)・cluster 数を gap statistic で最適化

#### NCO (Nested Clustered Optimization・Lopez de Prado 2019)

HRP + Mean-Variance のハイブリッド:

1. agglomerative hierarchical clustering で cluster 化
2. **各 cluster 内で Mean-Variance optimization** (= 小さい共分散行列で実行・stable)
3. **cluster 間は equal weight** または別の Mean-Variance
4. 結合して最終 weight

**特徴**: 共分散行列が大きい (= N > 50 等) ときに stable / NCO は HRP + HERC より MVO 寄り

#### 実装ライブラリ (= 業界標準)

| ライブラリ | 提供手法 | 業界使用度 |
|---|---|---|
| **PyPortfolioOpt** | HRP + Black-Litterman + 効率的フロンティア | 業界 default ([GitHub](https://github.com/PyPortfolio/PyPortfolioOpt) + [Docs](https://pyportfolioopt.readthedocs.io/en/stable/_modules/pypfopt/hierarchical_portfolio.html)) |
| **Riskfolio-Lib** | HRP + HERC + NCO + 20+ risk measures | 業界推奨 ([Docs HCPortfolio](https://riskfolio-lib.readthedocs.io/en/latest/hcportfolio.html) + [Medium 解説](https://medium.com/@orenji.eirl/hierarchical-risk-parity-with-python-and-riskfolio-lib-c0e60b94252e)) |
| **mlfinlab (Hudson & Thames)** | HRP + HERC + NCO + AFML 全 chapter 実装 | AFML 公式 ([mlfinlab](https://hudsonthames.org/mlfinlab/) + [HERC blog](https://hudsonthames.org/beyond-risk-parity-the-hierarchical-equal-risk-contribution-algorithm/)) |
| **HierPortfolios (R)** | HRP + HERC + NCO + variants | R 業界 default ([CRAN](https://cran.r-project.org/web/packages/HierPortfolios/HierPortfolios.pdf)) |

#### cat-bitget 適用判断 (= 工程 4 Position Sizing 配分強化候補)

- **重要な認識**: cat-bitget は **BTC 単一資産** → HRP の本来用途 (= multi-asset diversification) に直接適用不可
- **転用案**: **「cluster × Exit type × side」を strategy として扱い、strategy allocation に HRP/HERC を適用**:
  - phase_flow_v4 v7 改善 4 の動的合成方式 8 で cluster 数 12 × Exit type 12 × side 2 = 288 strategy
  - 288 strategy の return covariance を計算 → HERC で cluster 化 → 上位 N 戦略に資金配分
- **HRP vs HERC vs NCO 選定**:
  - 戦略数 ≥ 50 → HERC 推奨 (= cluster 数最適化)
  - 戦略数 < 50 → HRP で十分
  - 共分散行列不安定 → NCO で cluster 内 MVO 安定化
- **業界整合判定**: 業界標準は asset allocation 用途だが、本提案は strategy allocation に転用 → 異種用途への適用 → Phase 4-a cluster 出力との接続で別途 verify 要
- **既存 Half-Kelly との関係**: Half-Kelly = strategy 単位の確率ベース size / HRP = portfolio 単位の risk parity → **二段構造で併用可能** (= HRP で配分 ratio → Half-Kelly で各 strategy size 上限 clip)

### §18.4 Meta-Labeling 多段詳細 (= §13.5 の深掘り)

#### Meta-Labeling の業界 5 利点 (= multistage 整合)

[Wikipedia Meta-Labeling](https://en.wikipedia.org/wiki/Meta-Labeling) + [Hudson & Thames Meta-Labeling GitHub](https://github.com/hudson-and-thames/meta-labeling) + [Hudson & Thames Triple Barrier paper](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/) + [WhatWorksInTrading Substack](https://whatworksintrading.substack.com/p/meta-labeling-the-technique-that):

1. **Direction と Sizing の分離**: primary が方向 (= LONG/SHORT/0)・secondary が size 確率 → 同時最適化の非効率を回避
2. **False Positive 削減**: secondary が primary の低 confidence bet を filter
3. **Sharpe / max DD 改善**: 業界実証 (= AFML Ch.3 + Hudson & Thames 検証)
4. **Adaptability**: regime 変化に primary より柔軟に対応 (= secondary が「いつ primary を信じるか」を学習)
5. **Modular Architecture**: primary / secondary / sizing を独立開発 → team / iteration が並列化可能

#### 多段構造の業界拡張パターン

##### 2 段 (= AFML 標準・Phase 1 v6 案 f が試行)

- 段 1 (primary): direction prediction (LONG/SHORT/0)
- 段 2 (secondary): primary の正誤確率 → size

##### 3 段 (= 業界拡張・cat-bitget Phase 1 v7 候補)

- 段 1 (primary・direction): LightGBM + XGBoost stacking (= §18.1)
- 段 2 (secondary・confidence): Meta-Labeling で primary の正誤確率
- 段 3 (tertiary・regime adaption): regime 別 secondary を分離学習 (= 工程 1 regime 出力 × secondary で MoE 構造)

##### 4 段 (= 完全 cascade・将来検討)

- 段 1 (= 工程 2): 固定 Entry 候補生成
- 段 2 (= 工程 3 primary): direction
- 段 3 (= 工程 3 secondary): confidence
- 段 4 (= 工程 4): HRP/HERC で size 配分

#### 段 1 primary の品質確保 (= 案 f 失敗の構造的補正)

[QuantConnect Meta-Labeling not silver bullet](https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/) 整合:

- **primary が悪いと meta も救えない** (= 案 f 失敗の核心)
- 案 f は primary も secondary も同じ LightGBM + 同じ regime 不在ラベルで学習 → 同型バイアス
- **業界正攻法**: primary を **多様化** (= 工程 1 regime 入力追加 + LONG/SHORT 分離学習 + MTF 整合 + 異種 stacking) → secondary は「primary の盲点」を見れる構造を作る

#### Probability Calibration (= secondary 出力の size 投入前処理)

業界必須 ([Hudson & Thames Meta-Labeling repo](https://github.com/hudson-and-thames/meta-labeling)):

- secondary の出力 probability は raw LightGBM 出力で **過信** または **過小評価** の傾向あり
- 業界対応:
  - **Platt Scaling**: sigmoid で再 fit (= `sklearn.calibration.CalibratedClassifierCV(method='sigmoid')`)
  - **Isotonic Regression**: 非パラメトリック単調変換 (= `method='isotonic'`)
- 既存 §17.1 / §17.2 の **Purged K-Fold** で fold 毎に calibration 学習 (= leak 防止)

#### Information Advantage の業界定義

[Hudson & Thames paper](https://hudsonthames.org/wp-content/uploads/2022/04/Does-Meta-Labeling-Add-to-Signal-Efficacy.pdf):

- secondary が「primary が **十分活用できなかった情報**」を捕捉できれば information advantage 確立
- 業界実証で MA crossover を primary に LightGBM secondary を載せると Sharpe + max DD 改善
- ただし「primary が既に optimal」(= 簡単な構造のみで強い予測) では secondary の improvement marginal

#### cat-bitget 適用判断 (= Phase 1 v7 候補・案 f の構造的補正版)

- **段 1 primary (= 工程 3 main)**:
  - LightGBM + XGBoost stacking (= §18.1) + **regime 入力** (= 工程 1 出力) + **LONG/SHORT 分離学習** + **MTF 整合** (= §16)
  - 出力: direction (LONG/SHORT/0)
- **段 2 secondary (= 工程 3 confidence)**:
  - 別アーキ (= 推奨は MLP or XGBoost・LightGBM とは異種) で primary の **盲点情報** (= 出来高系 + microstructure + order book imbalance = §16.5-§16.6) を入力
  - 出力: 0/1 確率 (= TP 到達確率)
  - Platt / Isotonic で calibration
- **段 3 tertiary (= 工程 4 入力)**:
  - calibrated secondary 確率 → Half-Kelly + HRP/HERC cluster 配分 (= §18.3) で size 決定
  - 0.12 BTC 合計上限制約で clip (= CLAUDE.md §0-2 絶対規定)
- **業界整合 verify**:
  - 統計指標 (= Phase 1-3) = primary entropy_lift + secondary AUC + calibration (= Brier score)
  - PnL 指標 (= Phase 5-6-b) = 月次 NET ≥ $1,900 + DSR + PBO
  - 混合禁止 (= §17.6 + cc_role §1.4.6.1 #9)

### §18.5 領域 5 まとめ: 7 工程接続 + cat-bitget 設計判断調査ノート

#### 7 工程接続マトリックス

| 工程 | 組合せ手法の改善方向 | 業界整合手法 |
|---|---|---|
| 1 regime | HMM/GMM 単体 → ML 化 (= HMM + LightGBM 分類の stacking) | §13 + §14.6 |
| 2 Entry 候補生成 | cascade 段 1 として配置 (= 固定ロジックで高 recall) | §18.2 |
| **3 Entry ML** | **異種 stacking (= LightGBM + XGBoost + DL) + Logistic Regression meta + Meta-Labeling 2-3 段** | §18.1 + §18.4 |
| 4 Position Sizing | Half-Kelly + Vol target + **HRP/HERC で strategy allocation** | §18.3 + phase_flow_v4 v7 改善 4 |
| 5 Exit ML | PPO (= RL) + XGBoost (= scale-out 確率) の **ensemble or cascade** | §13.4 + §18.1 |
| 6 Risk 管理 | 固定ルール (= ML 統合保留) | §14.8 |
| 7 Online 監視 | concept drift + champion-challenger + A/B testing (= 領域 7 で詳細) | 領域 7 |

#### Phase 1 v6 6 案全滅の構造的原因 (= v1-v4 学習成果統合)

| # | 原因 | 補強領域 | v4 学習成果 |
|---|---|---|---|
| 1 | ボラ予測 ML 設計欠陥 (= regime 不在 + LONG/SHORT 並列 + ボラ依存ラベル) | L-223 | §13.1 + §14.6 |
| 2 | アルゴリズム多様性ゼロ (= 全 LightGBM) | L-224 + arxiv 2512.15738 | **§18.1 stacking 異種 base 確立** |
| 3 | bar 種別多様性ゼロ (= 全 5m time bar) | L-225 + §16.1 | §16.1 (v3 で確立済) |
| 4 | cascade 構造不在 (= ML 単段 entry 判定) | **v4 §18.2 新規** | **§18.2 cascade 多段確立** |
| 5 | strategy allocation の機械的固定 (= Phase 4-a cluster の risk parity 配分なし) | **v4 §18.3 新規** | **§18.3 HRP/HERC 適用候補確立** |
| 6 | Meta-Labeling 失敗 (= 案 f primary も secondary も同型) | L-223 + §13.5 | **§18.4 多段詳細で primary 多様化要件確立** |

→ Phase 1 v6 6 案全滅の構造的原因 = **6 軸の多様性欠落**。v4 で軸 2/4/5/6 の業界カタログ確立 → 工程 2-7 詳細詰めで再設計可能

#### cat-bitget Phase 1 v7 設計判断調査ノート (= v4 学習で見えた候補)

> ⚠️ 以下は **学習資料の調査ノート位置付け**。実際の設計確定は WORKFLOW 改訂37 active 優先 3 (= 工程 2-7 詳細詰め) で別途実施 (cc_role §1.5)。

##### 案 g (= 異種 Stacking + Meta-Labeling 3 段・Phase 1 v7 主軸候補)

- **段 1 (= Cascade 段 1・工程 2)**: 固定ロジック (= 業界標準シグナル組合せ・cc_role §1.7 旧 Priority 経験則 + 業界標準 ATR/ADX/RSI フィルタ) で全 bar の数 % まで絞る
- **段 2 (= 工程 3 primary)**: LightGBM + XGBoost + GRU (= 3 種 stacking) + Logistic Regression meta
  - 入力: 既存 2604 feature + Fractional Diff 24 + 出来高系 48 + microstructure 10-15 (= §16) + regime ラベル (= 工程 1 固定ルール出力)
  - LONG/SHORT 分離学習 + MTF (= 5m/15m/1h/4h confluence)
  - OOF prediction は Purged K-Fold 5 fold + Embargo K bar
  - 出力: direction (LONG/SHORT/0)
- **段 3 (= 工程 3 secondary・Meta-Labeling)**: XGBoost or MLP (= primary とは異種)
  - 入力: primary 段の盲点情報 (= 板情報系 microstructure + Funding Rate 時系列入力化 + OI ROC)
  - 出力: 0/1 確率 (= TP 到達確率)
  - Platt + Isotonic で calibration → Brier score で verify
- **段 4 (= 工程 4 sizing)**: HRP/HERC で strategy allocation + Half-Kelly で個別 size + 0.12 BTC 合計 clip
- **評価 (= 工程 3 統計指標)**: entropy_lift + TP precision + DSR_train (= §17.4 + §17.6)
- **評価 (= 工程 5-6-b PnL 指標)**: 月次 NET ≥ $1,900 全月 + DSR > 0.95 + PBO < 0.5 (= §17.4 + §17.5)
- **計算コスト見積**: 段 2 3 種 × 各 110 分 + 段 3 secondary 60 分 + meta 30 分 = 約 7 時間 / 1 セッション規模

##### 多様性 verify 義務 (= 採用前必須)

- base learners の predict correlation r を fold 内で measure → r > 0.6 → diversification 失敗 → 別 base 検討
- arxiv 2512.15738 ベンチマーク準拠

##### CPCV + DSR + PBO で robustness 強化 (= §17.3-§17.5 整合)

- Phase 1 v7 評価フローに CPCV (= C(6,2) = 15 paths) を追加候補
- 採用判定に DSR > 0.95 + PBO < 0.5 を併用 (= 月次 NET だけでは「偶然」リスク残存)

#### 関連 lessons + 関連 memory

- L-223 (= ボラ予測 ML 設計欠陥) / L-224 (= アルゴリズム多様性ゼロ) / L-225 (= 領域 3-4 完成) — v4 学習の直接動機
- cc_role §1.4.6.1 9 項目 (= ML pipeline 設計提案前の業界整合 verify) — 本領域学習で 6-9 番を蓄積
- feedback_trade_ml_knowledge_gap (= 業界標準理解不足) — v4 で補強完了 (= 領域 5 まで業界カタログ構築済)

---

## §19 ML リスク管理 (WORKFLOW 改訂38 領域 6・業界カタログ)

> v5 追記 (2026-05-25)。**「保有期間中の損失をどう抑え、ポジションサイズをどう動的に調整するか」の業界カタログ**。Phase 1 v6 6 案全滅で確定した 6 軸多様性欠落 (= L-226 §18.5 = ボラ ML 欠陥 / アルゴ多様性 / bar 種別 / cascade 不在 / strategy allocation 固定 / Meta-Labeling 同型) の上に、本領域は **工程 4 (Position Sizing) + 工程 5 (Exit ML) + 工程 6 (Risk 管理)** の損失抑制レイヤーを業界整合で固める。CLAUDE.md §0-2 (= ポジション 0.12 BTC 合計上限) と整合した「合計内での動的配分」「volatility-aware deleveraging」「Maximum DD floor」を中心に整理。

### §19.1 Volatility Targeting (= ボラ目標で動的レバ調整)

#### 業界の根本構造

**volatility targeting** = 「ポートフォリオの ex-ante 年率ボラを一定値 (= σ_target) に保つよう、ボラ予測値に反比例してレバを調整する」業界 default 手法 ([CFA Institute 2019 The Impact of Volatility Targeting](https://rpc.cfainstitute.org/research/cfa-digest/2019/07/dig-v49-7-2) / [ScienceDirect S1386418116301379](https://www.sciencedirect.com/science/article/abs/pii/S1386418116301379)):

```
weight_t = (σ_target / σ_predicted_t) × base_weight
```

- σ_target = 例: 年率 10% (= [CME Group improving TSM](https://www.cmegroup.com/education/files/improving-time-series-momentum-strategies.pdf) で portfolio target 10%)
- σ_predicted_t = t 時点のボラ予測 (= GARCH / EWMA / HAR-RV)
- レバ範囲 = 通常 0.5x - 2.0x で clip (= 過剰レバ防止)

#### 業界実証 (= Time-Series Momentum との接続)

[ScienceDirect Time series momentum and volatility scaling](https://www.sciencedirect.com/science/article/abs/pii/S1386418116301379): 「**TSM 戦略の profitability は volatility scaling に driven されている**・vol scaling なしの TSM = buy-and-hold と同等」を実証。[AlphaArchitect Time Series Momentum Refresh](https://alphaarchitect.com/time-series-momentum-aka-trend-following-the-historical-evidence/) + [CME Group Improving TSM](https://www.cmegroup.com/education/files/improving-time-series-momentum-strategies.pdf): 12-month TSM の annualized Sharpe = 0.76 (volatility-scaled) で trend-following 業界 default。

#### Volatility 予測手法の業界比較 (= §14.3 の補強)

| 手法 | 業界実証 (BTC) | 業界推奨 |
|---|---|---|
| **EWMA (λ=0.94)** | 簡易・短期反応高 | baseline (= RiskMetrics 由来) |
| **GARCH (1,1)** | persistence > 0.7・shock sensitivity 9-37% | 業界 default |
| **EGARCH** | **BTC で最良** (= Asymmetric leverage effect 捕捉) | crypto 推奨 |
| **TGARCH** | BTC で 1 位 ([Springer 2025 Future Business Journal](https://link.springer.com/article/10.1186/s43093-025-00568-w)) | crypto 第 2 候補 |
| **HAR-RV** | daily / weekly / monthly RV 重ね回帰・1-day RMSE 280 (GARCH 335 超え) | 業界実証あり |
| **LSTM / CNN-LSTM** | 全 horizon で GARCH 超え (intraday 含む) | ML 系優位 |

出典: [Forecasting Crypto Volatility with GARCH Models (Medium)](https://medium.com/@yavuzakbay/forecasting-crypto-volatility-with-garch-models-6a67822d1273) / [RAUSP Management Journal crypto returns volatility](https://www.emerald.com/rausp/article/60/1/220/1276890/Cryptocurrency-price-returns-volatility-modeling) / [Hybrid intraday Bitcoin volatility (ScienceDirect 2025)](https://www.sciencedirect.com/science/article/abs/pii/S106294082500066X) / [Bitcoin Spot & Option Markets Horserace (arxiv 2010.07402)](https://arxiv.org/pdf/2010.07402)

#### α + β ≈ 1 = Near-IGARCH (= 業界実証)

[Springer 2025](https://link.springer.com/article/10.1186/s43093-025-00568-w) + 業界教科書: BTC で α (= shock sensitivity) 9-37% + β (= persistence) > 0.7 → α + β ≈ 1 で **near-IGARCH (= 単位根性)** = volatility shock の影響が **極めて長期持続**。volatility regime の遷移を捕捉できない GARCH(1,1) のみでは BTC の長期 vol pattern を学習困難 → EGARCH (= leverage effect) または HAR-RV (= cascade memory) が業界推奨。

#### cat-bitget 適用判断 (= 工程 4 + 工程 6 主軸候補)

- **工程 4 (Position Sizing) の必須入力**: σ_target = 年率 10-15% (= crypto は 60-80% annual vol で baseline → 0.15-0.25x deleveraging 目安)
- **σ_predicted_t 主軸**: HAR-RV を baseline (= §14.3 整合) + EGARCH(1,1) で leverage effect 補強候補
- **0.12 BTC 合計上限制約との整合**: vol targeting で得られる weight が 0.12 BTC を超えても **必ず clip** (= CLAUDE.md §0-2 絶対規定)
- **既存 Half-Kelly との接続**: Half-Kelly (= §14.5) で個別 strategy size + vol targeting で portfolio 全体 deleveraging の **2 段構造** = 業界 default ([CME Group TSM](https://www.cmegroup.com/education/files/improving-time-series-momentum-strategies.pdf))
- **注意 (= 業界実証)**: [CXO Advisory Volatility Scaling momentum](https://www.cxoadvisory.com/volatility-effects/volatility-scaling-for-momentum-strategies/): 過度の vol scaling は **Sharpe 改善せず・ボラ高時の deleveraging で profitable trend を取り損ねる事例あり** → cat-bitget では 0.5x-2.0x で clip + drawdown trigger 併用が業界整合

### §19.2 Stop-Loss 業界手法 (= ATR-based / Chandelier / Volatility-Stop / ML 動的)

#### 業界 4 主流手法

| 手法 | 計算式 | 業界用途 |
|---|---|---|
| **ATR Trailing Stop (= Chandelier Exit)** | `Stop = Highest_High(N) - ATR(N) × M` | Chuck LeBeau 発・最普及・trend-following default |
| **Wilder Volatility Stop** | `Stop = Close - ATR(N) × M` (より tight) | Welles Wilder 発・active trading 向き |
| **Fixed % Stop** | `Stop = Entry × (1 - SL_PCT)` | 業界保守 default・cat-bitget 旧 Priority 構造 |
| **ML 動的 Stop** | XGBoost/LSTM/PPO で動的予測 | 業界実証あり (= [SD 2025 RL+LSTM+XGBoost](https://www.sciencedirect.com/science/article/abs/pii/S1568494625003400)) |

#### Chandelier Exit 業界 default パラメータ ([ChartSchool](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/chandelier-exit) + [StratBase.ai](https://stratbase.ai/en/blog/average-true-range-trailing-stop))

| パラメータ | 業界推奨 | cat-bitget 5m 接続 |
|---|---|---|
| **lookback N** | 22 (= 1 ヶ月分・daily) | 5m: N=288 (= 1 日) or N=576 (= 2 日) |
| **ATR multiplier M** | **3.0** (= 業界 sweet spot・profit factor 1.61) | crypto 高 vol → M=2.0-2.5 候補 |
| **trail 方向** | LONG は最高高値から下降・SHORT は最低安値から上昇 | 同様 |
| **再計算** | each bar で ATR 再計算 (= dynamic) | trending 中の premature exit 防止 |

#### Wilder Volatility Stop ([StratBase.ai](https://stratbase.ai/en/blog/average-true-range-trailing-stop))

- N=7 / M=2.0 が業界 default (= 短期 + tight)
- BTC 4H 実証: Wilder (7, 2.0) は **短期 trade で profit/trade 高い**・**長期 trend で pullback に shake out されやすい**
- Chandelier (22, 3.0) は **長期 trend に強い**・**短期で profit/trade 劣る** → 戦略 horizon に応じて選択

#### Multiplier 選定の業界目安

| Multiplier | 業界用途 |
|---|---|
| **1.5× ATR** | 短期 / 低 vol 環境 |
| **2.0× ATR** | swing trading 4H chart default |
| **3.0× ATR** | trend-following daily chart default (= 最普及) |
| **4.0×+** | 長期 trend follow / 高 vol (= crypto BTC で要検討) |

[LuxAlgo 5 ATR Stop-Loss Strategies](https://www.luxalgo.com/blog/5-atr-stop-loss-strategies-for-risk-control/): 5 つの ATR ベース戦略 (= fixed multiplier / dynamic / regime-aware / volatility band / hybrid) を実装比較

#### Partial Take-Profit + ATR Trailing の組合せ (= 業界 default パターン)

業界推奨 ([StratBase.ai](https://stratbase.ai/en/blog/average-true-range-trailing-stop)):

1. **50% を fixed target で利確** (= 例 2:1 risk-reward = 利確 = 2 × SL)
2. **残り 50% を ATR trailing stop で hold** → 大トレンドに乗る
3. 結果 = profit lock + tail capture の両立

cat-bitget Phase 4-b 既存 12 種 Exit (= TP_PCT / TIME_EXIT / TRAIL_RATIO / etc.) の中で `TRAIL_RATIO` が ATR ベースか定率かは要 verify。業界整合形は ATR ベース。

#### ML 動的 Stop-Loss (= 業界実証)

[ScienceDirect 2025 Crypto DRL with LSTM XGBoost feature selection](https://www.sciencedirect.com/science/article/abs/pii/S1568494625003400): **XGBoost で feature 選別 → DDQN (Double Deep Q-Network) + LSTM/BiLSTM で trading signal 生成** → key trading metric 改善。動的 stop-loss を ML で予測する業界実証あり。

[LSTM+XGBoost arxiv 2506.22055](https://arxiv.org/pdf/2506.22055): BTC/ETH/Doge/LTC で LSTM (temporal) + XGBoost (非線形 + sentiment / macro auxiliary) hybrid model 評価。R² ~0.98 を Gradient Boosting / XGBoost で達成 ([Springer 2025 ML crypto trading optimization](https://link.springer.com/article/10.1007/s44163-025-00519-y))。

[Stop-Loss 動的調整 (Medium DappFort)](https://www.dappfort.com/blog/machine-learning-models-for-predictive-crypto-trading-lstm-and-reinforcement-learning/): ML で **volatility cluster ごとに stop-loss 個別最適化** → 単一 SL_PCT より drawdown 削減。

#### cat-bitget 適用判断 (= 工程 5 Exit ML 主軸候補)

- **業界整合形 (= phase_flow_v4 v7 改善 4 主軸 1 + 比較 N 構造に追加)**:
  - 主軸 = PPO (= §13.4 + §14.7 + 78% success rate)
  - 比較 1 = Chandelier Exit (N=288 5m / M=2.5 crypto 高 vol 調整) — **新規追加候補**
  - 比較 2 = Wilder Volatility Stop (N=84 / M=2.0) — **新規追加候補**
  - 比較 3 = Fixed % Stop (= 旧 Priority 構造 / 現状 SL_PCT) — 維持 baseline
- **Partial TP + ATR Trailing**: Phase 4-b 既存 12 種 Exit の TRAIL_RATIO + TP_PCT の組合せパターンに「50%TP_PCT 固定 + 50%ATR trailing」を追加候補
- **ML 動的 (Phase 1 v7+)**: XGBoost で stop-loss 確率予測 (= §14.7) のサブ候補

### §19.3 Drawdown Control (= CPPI / TIPP / Max DD constraint)

#### CPPI (Constant Proportion Portfolio Insurance) ([Wikipedia](https://en.wikipedia.org/wiki/Constant_proportion_portfolio_insurance) + [QuantPedia Introduction to CPPI](https://quantpedia.com/introduction-to-cppi-constant-proportion-portfolio-insurance/) + [QuantifiedStrategies CPPI Position Sizing](https://www.quantifiedstrategies.com/constant-proportion-portfolio-insurance-cppi-position-sizing/))

##### 基本構造

```
Floor    = 例 80% × initial_capital (= 損失上限 20%)
Cushion  = Portfolio_t - Floor
Risky_t  = m × Cushion       (m = multiplier・典型 3-5)
Safe_t   = Portfolio_t - Risky_t
```

- m × Cushion でリスク資産 weight を動的調整
- 損失で Cushion が縮小 → 自動的に risky deleveraging
- 利益で Cushion が拡大 → 自動的に risky leveraging
- **floor 触れる前に risky weight 0 に収束 = drawdown protection**

##### 業界の弱点 (= Buy-High Sell-Low 構造)

[Wikipedia CPPI](https://en.wikipedia.org/wiki/Constant_proportion_portfolio_insurance): 「**Compared to a bond + call strategy, the drawback of the CPPI is that it follows a buy high sell low strategy. Volatility will hurt the performance of the investment, and once the strategy has deleveraged, it never recovers.**」 = whipsaw 環境で trade-off 大。

#### TIPP (Time Invariant Portfolio Protection・Estep & Kritzman 1988)

[Grokipedia CPPI](https://grokipedia.com/page/Constant_proportion_portfolio_insurance) + [Core AXA-IM CPPI/TIPP](https://core.axa-im.com/investment-strategies/multi-asset/insights/understanding-portfolio-insurance-management-cppitipp) + [QuantPedia TIPP](https://quantpedia.com/time-invariant-portfolio-protection/):

CPPI 拡張 = **floor を peak portfolio value × X% (= 動的高水位線) に追従**:

```
Floor_t = max(Floor_{t-1}, X% × Portfolio_t)     # ratchet up
Cushion_t = Portfolio_t - Floor_t
Risky_t = m × Cushion_t
```

- 利益が出ると floor も上昇 (= 利益保護)
- Max DD を **(1 - X%)** 以内に確率的に維持
- 業界相場: X = 0.8-0.95 (= drawdown 上限 5-20%)

#### Max DD Constraint + CVaR (= 業界数理整理)

[Riskfolio-Lib HCPortfolio docs](https://riskfolio-lib.readthedocs.io/en/latest/hcportfolio.html) + [Portfolio Optimization Book Alt Risk Measures](https://portfoliooptimizationbook.com/book/10.2-alternative-risk-measures.html) + [scikit-portfolio CVaR](https://scikit-portfolio.github.io/scikit-portfolio/efficient_cvar/):

| risk measure | 業界用途 | crypto 適性 |
|---|---|---|
| **Max DD (= MDD)** | tail risk 直接測定 | ✅ crypto 必須 ([Amberdata Crypto Portfolio](https://blog.amberdata.io/crypto-portfolio-optimization-balancing-risk-and-return-in-a-dynamic-market)) |
| **CVaR (= Expected Shortfall)** | tail loss の期待値 (= VaR 超え時の平均損失) | ✅ crypto 業界推奨 ([MDPI 2026 CVaR crypto regime](https://www.mdpi.com/2227-7072/14/3/53)) |
| **Sortino Ratio** | downside semi-deviation でリターン除算 | ✅ crypto fat-tailed return に対応 |
| **Calmar Ratio** | annualized return / MDD | ✅ tail risk 重視 crypto 向き |

##### CVaR 制約付き portfolio optimization の業界実証

[arxiv 2406.00610 Robust Covariance + CVaR Constraints](https://arxiv.org/html/2406.00610v1): CVaR 制約 portfolio optimization の robust 化 ([Stan Uryasev CVaR Algorithms](https://www2.mathematik.hu-berlin.de/~romisch/SP01/Uryasev.pdf) の発展)

[MDPI 2026 CVaR Crypto Regime](https://www.mdpi.com/2227-7072/14/3/53): 「**Effective CVaR-based portfolio management in cryptocurrency markets requires a regime- and tail-depth-dependent approach**」= 単一 CVaR 制約より regime 別 CVaR 制約が業界推奨。

[Amberdata Crypto Portfolio](https://blog.amberdata.io/crypto-portfolio-optimization-balancing-risk-and-return-in-a-dynamic-market): 「Calmar Ratio + MDD = crypto portfolio tail risk 評価の業界 default + VaR + CVaR で liquidation event 確率視点」を併用が業界 best practice。

#### Dynamic Deleveraging (= 動的 leverage 削減)

業界実装パターン (= 上記 3 手法の統合):

1. **drawdown trigger**: 直近 N 日 drawdown > X% → leverage 0.5x (= half-cut)
2. **vol spike trigger**: realized_vol > μ + 2σ → leverage 0.5x (= §19.1 vol targeting 整合)
3. **regime trigger**: regime 判定 (= 工程 1 出力) で down/volatile regime → leverage 0.5x
4. **複合**: 上記 3 trigger を OR 結合 → 「**deleveraged_weight = base_weight × min(triggers)**」

#### cat-bitget 適用判断 (= 工程 6 Risk 管理 主軸候補)

- **TIPP 主軸候補 (= drawdown floor 動的 ratchet)**:
  - X = 0.9 (= MDD < 10% 目標) または X = 0.85 (= MDD < 15%)
  - m = 3-5 (= multiplier・cushion による risky weight 拡大率)
  - **0.12 BTC 合計上限と整合**: TIPP で得られる weight が 0.12 を超えても **必ず clip** (= CLAUDE.md §0-2 絶対規定)
- **CVaR 制約 (= Phase 5 / 6-b 合格判定追加候補)**:
  - 月次 NET ≥ $1,900 (= 現状必達) + DSR > 0.95 + PBO < 0.5 (= L-225 §17.4-5) + **CVaR_95 < $X (= 月次損失下限)** で多重防御
  - regime 別 CVaR (= MDPI 2026 業界推奨) で「down regime での CVaR 厳しめ・range regime で緩め」の動的閾値
- **Dynamic Deleveraging**:
  - drawdown trigger: 直近 30 日 DD > 10% → leverage 0.5x
  - vol spike trigger: realized_vol_5m / realized_vol_30d > 2.0 → leverage 0.5x
  - regime trigger: 工程 1 出力 = down/volatile → leverage 0.5x
- **CPPI は見送り (= whipsaw リスク)**: crypto 高 vol で buy-high-sell-low 構造が deleverage 損失累積 → TIPP の方が業界整合

### §19.4 Position Scaling (= Kelly criterion 詳細 + Pyramiding + Scale-in / Scale-out)

#### Kelly criterion 業界詳細 (= §14.5 の補強)

##### 業界数式 (= Bitcoin 高 vol 環境調整)

```
f* = (b × p - q) / b     # 標準 Kelly
b  = expected_win / expected_loss   # reward/risk ratio
p  = win_rate
q  = 1 - p
```

##### Half / Quarter / One-Tenth Kelly の業界相場

[Altrady Kelly Crypto](https://www.altrady.com/blog/risk-management/kelly-criterion-crypto-position-sizing) + [LBank Kelly Crypto Risk Management](https://www.lbank.com/explore/mastering-the-kelly-criterion-for-smarter-crypto-risk-management) + [Medium Kelly Crypto](https://medium.com/@tmapendembe_28659/kelly-criterion-for-crypto-traders-a-modern-approach-to-volatile-markets-a0cda654caa9) + [OSL Kelly Bet Crypto](https://www.osl.com/hk-en/academy/article/what-is-the-kelly-bet-size-criterion-and-how-to-use-it-in-crypto-trading) + [CMC Kelly Crypto Academy](https://coinmarketcap.com/academy/article/what-is-the-kelly-bet-size-criterion-and-how-to-use-it-in-crypto-trading):

| Fraction | 業界推奨 | crypto 高 vol 適性 |
|---|---|---|
| **Full Kelly (1.0×f*)** | ❌ 非推奨 (= DD 50-80%) | 致命的 |
| **Half Kelly (0.5×f*)** | ✅ プロ業界 default | 成長率 ~75% Full + DD ~50% 削減 |
| **Quarter Kelly (0.25×f*)** | ✅ crypto 推奨 | 推定誤差バッファ最大 |
| **One-Tenth Kelly (0.10×f*)** | ✅ ultra-conservative / 大規模資金 | プロ業界 10-25% Full 多用 |

「**Most professional traders use between 25% and 50% of the Kelly recommendation, also known as Quarter-Kelly or Half-Kelly**」 ([Altrady](https://www.altrady.com/blog/risk-management/kelly-criterion-crypto-position-sizing)) = phase_flow_v4 v7 改善 4 で Half-Kelly 採用は業界整合内、crypto 高 vol 考慮で Quarter-Kelly も視野。

##### Stephen Perrenod Bitcoin Kelly ([Substack](https://stephenperrenod.substack.com/p/kelly-criterion-for-bitcoin))

Bitcoin 特有の Kelly 適用: long-term mean reversion + log-return 分布の skewness 補正 → 通常 Kelly より厳格な fraction 推奨 (= 業界保守姿勢)。

#### Pyramiding 戦略 (= 利益再投資型 scale-in) 

[QuantStrategy.io Pyramiding Strategy Ultimate Guide](https://quantstrategy.io/blog/the-ultimate-guide-to-pyramiding-strategy-in-trading/) + [QuantStrategy Mathematics of Pyramiding](https://quantstrategy.io/blog/the-mathematics-of-pyramiding-calculating-position-sizes/) + [QuantStrategy Pyramid Trending](https://quantstrategy.io/blog/pyramid-trading-for-trending-markets-strategies-for/) + [TradersPost Pyramiding Guide](https://blog.traderspost.io/article/pyramiding-trading-strategies-guide):

##### 基本構造

- 「**勝ち pos に追加・負け pos には追加しない**」 = mathematical "Zero-Risk" 原則
- pyramiding 各層は **progressively 縮小** (= 例: 第 1 層 100% → 第 2 層 50% → 第 3 層 25%)
- 業界 default 層数: 3-5 (= 5+ は overhead 大)

##### Volatility-Adjusted Pyramiding (= BTC 高 vol 対応)

[QuantStrategy Pyramid Trending](https://quantstrategy.io/blog/pyramid-trading-for-trending-markets-strategies-for/): 「**During a Bitcoin bull run, traders often use Volatility-Adjusted Pyramiding because of the high intraday swings, with layers added further apart to avoid being stopped out by noise**」= ATR で layer 間隔を動的調整。

#### Scale-in / Scale-out 業界実装

[hoc-trade Coinmonks Medium Scale-in/out](https://medium.com/coinmonks/scale-in-and-scale-out-of-crypto-trades-with-powerful-risk-management-trading-academy-891e5366d517) + [FasterCapital Scaling In Pyramiding](https://www.fastercapital.com/content/Scaling-In--Step-by-Step--Scaling-In-Techniques-for-Pyramiding.html) + [Forextester Scale Out & In Guide](https://forextester.com/blog/scale-out-and-scale-in-trading/):

| 手法 | 仕組み | 業界用途 |
|---|---|---|
| **Scale-in** (= 段階 entry) | 価格レベル / vol / TF 整合で順次 entry | DCA (= dollar-cost averaging) 整合 |
| **Scale-out** (= 段階 exit) | TP_PCT 層ごとに partial close | profit lock + tail capture (= §19.2 整合) |
| **Rule-based** | 固定 trigger (= 例: 10 bps ごと) | static / 単純 |
| **Model-driven** | ATR / vol / ML 確率で動的 layer | dynamic / 業界 trend |

> 「As trading moves increasingly toward automation, static, rule-based scaling (e.g., adding every 10 basis points) is being replaced by dynamic, model-driven approaches.」 ([Forextester](https://forextester.com/blog/scale-out-and-scale-in-trading/))

#### Bitcoin Futures 特有の Position Sizing

[FasterCapital Scaling In](https://www.fastercapital.com/content/Scaling-In--Step-by-Step--Scaling-In-Techniques-for-Pyramiding.html): 「**Futures trading is inherently geared towards position sizing strategies because of the high leverage and capital efficiency it provides; pyramiding in futures allows you to maximize this capital efficiency, but it requires a deep understanding of tick values and contract specifications**」= cat-bitget の MAX_ADDS=5 (= 平均建値型 add) は業界整合。

#### cat-bitget 適用判断 (= 工程 4 Position Sizing 詳細詰め候補)

- **phase_flow_v4 v7 改善 4 (= 動的合成方式 8 = Half-Kelly + Vol target + cluster 強度別配分) の業界整合 verify**:
  - Half-Kelly は業界 default 範囲内 ✅
  - 「cluster 強度別配分」は HRP / HERC で robust 化候補 (= §18.3 L-226 整合)
  - crypto 高 vol 環境で Quarter-Kelly も視野 (= 推定誤差バッファ大)
- **MAX_ADDS=5 (= 旧 Priority 平均建値型) の業界整合**:
  - Pyramiding 層数 3-5 業界 default の上端 ✅
  - **層 size は progressively 縮小**が業界推奨 → 現状の旧 Priority MAX_ADDS は均等 size の可能性あり (= 要 verify)
  - Volatility-Adjusted Pyramiding (= ATR で layer 間隔調整) を Phase 7-c 実装候補
- **Scale-out 強化**: §19.2 partial TP + ATR trailing と整合 → Phase 4-b 既存 12 種 Exit に「50% TP_PCT 固定 + 50% ATR trail」追加候補
- **0.12 BTC 合計上限制約**: pyramiding 全層合計 ≤ 0.12 BTC 必須 (= CLAUDE.md §0-2)・層数 × layer_size 設計義務

### §19.5 補強リスク測度 (= Sortino / Calmar / CVaR / DSR 統合)

#### 業界主要 risk-adjusted return 指標 (= Phase 5 / 6-b 評価強化候補)

| 指標 | 計算式 | 業界用途 |
|---|---|---|
| **Sharpe Ratio** | `(R - Rf) / σ` | 業界 default・対称 vol 仮定 |
| **Sortino Ratio** | `(R - Rf) / σ_downside` | downside semi-deviation のみ・**crypto fat-tail に対応** |
| **Calmar Ratio** | `Annualized Return / MDD` | **tail risk 重視 crypto 推奨** |
| **DSR (Deflated Sharpe)** | Bailey & LdP 2014 (= §17.4) | 多重検定 + 非正規性補正 |
| **CVaR (Expected Shortfall)** | tail loss 期待値 | regime 別 CVaR が crypto 業界推奨 (= MDPI 2026) |
| **MAR Ratio** | Annualized Return / MAR (= Min Acceptable Return) | 下方リスク (= Calmar 拡張) |

#### crypto 業界推奨の risk measure 組合せ

[Amberdata Crypto Portfolio](https://blog.amberdata.io/crypto-portfolio-optimization-balancing-risk-and-return-in-a-dynamic-market): 「**For crypto portfolios, the Calmar Ratio and Maximum Drawdown become critical for assessing tail risk, while Value at Risk (VaR) and Conditional VaR (CVaR) provide probabilistic views of potential losses during liquidation events**」

業界 best practice:
1. **Return 評価**: Annualized Return + Sharpe + Sortino
2. **Tail risk**: MDD + Calmar + CVaR_95
3. **多重検定補正**: DSR + PBO (= §17.4 + §17.5)
4. **regime 別**: regime up / range / down で別途 risk measure 評価

#### Riskfolio-Lib + scikit-portfolio + portfoliooptimizationbook の業界実装

| ライブラリ | 提供 risk measure | 業界使用度 |
|---|---|---|
| **Riskfolio-Lib** | HRP + HERC + 20+ risk measures (= CVaR / EVaR / CDaR / WR) | 業界 default ([Riskfolio-Lib](https://riskfolio-lib.readthedocs.io/)) |
| **scikit-portfolio** | mean-CVaR + 効率的フロンティア (= CVaR) | sklearn 互換 ([scikit-portfolio CVaR](https://scikit-portfolio.github.io/scikit-portfolio/efficient_cvar/)) |
| **portfoliooptimizationbook** | 11.2 + 10.2 章で alternative risk measures 体系化 | 教科書 ([Portfolio Opt Book](https://portfoliooptimizationbook.com/book/10.2-alternative-risk-measures.html)) |

#### cat-bitget 適用判断 (= Phase 5 / 6-b 合格判定多重防御)

- **現状必達**: 月次 NET ≥ $1,900 全月クリア (= CLAUDE.md / project_goal)
- **v3 領域 4 追加候補 (= L-225)**: DSR > 0.95 + PBO < 0.5
- **v5 領域 6 追加候補**:
  - **Calmar Ratio > 2.0** (= annualized return が MDD の 2 倍以上・crypto 業界推奨水準)
  - **CVaR_95 < $X/月** (= 月次損失 95% tail < 上限・regime 別閾値)
  - **Sortino > 1.5** (= downside risk-adjusted return)
- **多重防御の論理**: 月次 NET だけでは「単月偶然合格」リスク残存 → DSR + PBO + Calmar + CVaR で本番投入リスク多重防御

### §19.6 領域 6 まとめ: 7 工程接続 + cat-bitget 設計判断調査ノート

#### 7 工程接続マトリックス (= リスク管理レイヤー追加)

| 工程 | リスク管理の改善方向 | 業界整合手法 |
|---|---|---|
| 1 regime | regime 別 risk measure 閾値 (= CVaR / Calmar 動的) | §19.3 + MDPI 2026 |
| 2 Entry 候補生成 | (= 直接接続なし・固定ロジック) | — |
| 3 Entry ML | 統計指標 (= §17.6) + DSR_train | §17.4 (v3) |
| **4 Position Sizing** | **Half-Kelly + Vol Targeting + HRP/HERC + 0.12 BTC clip** | §19.1 + §19.4 + §18.3 |
| **5 Exit ML** | **PPO 主軸 + Chandelier Exit + Wilder Stop + ML 動的 SL** | §19.2 + §14.7 |
| **6 Risk 管理** | **TIPP drawdown floor + Dynamic Deleveraging + CVaR 制約** | §19.3 |
| 7 Online 監視 | drawdown trigger + vol spike alert (= 領域 7 で詳細) | 領域 7 |

#### Phase 1 v6 6 案全滅の構造的原因 → リスク管理欠落の補強整理

L-226 §18.5 で確定した 6 軸多様性欠落に **第 7 軸 = リスク管理レイヤー不在** を追加:

| # | 原因 | 補強領域 | v5 学習成果 |
|---|---|---|---|
| 1 | ボラ予測 ML 設計欠陥 | L-223 | §13.1 + §14.6 |
| 2 | アルゴ多様性ゼロ | L-224 + arxiv 2512.15738 | §18.1 |
| 3 | bar 種別多様性ゼロ | L-225 + §16.1 | §16.1 |
| 4 | cascade 構造不在 | v4 §18.2 | §18.2 |
| 5 | strategy allocation 機械固定 | v4 §18.3 | §18.3 |
| 6 | Meta-Labeling 同型 | L-223 + §13.5 + v4 §18.4 | §18.4 |
| **7** | **リスク管理レイヤー不在 (= vol targeting / TIPP / 動的 SL 不在)** | **v5 §19 新規** | **§19.1-§19.4** |

→ 工程 4-6 のリスク管理レイヤーが業界実装パターン (= vol targeting + TIPP + 動的 SL + Half-Kelly + HRP) を採用していなかった構造的補強原因を v5 で整理。

#### cat-bitget 設計判断調査ノート (= v5 学習成果)

> ⚠️ 以下は **学習資料の調査ノート位置付け**。実際の設計確定は WORKFLOW 改訂38 active の優先 3 (= 工程 2-7 詳細詰め) で別途実施 (cc_role §1.5)。

##### v5 (= 領域 6) の追加確定事項

- **工程 4 (Position Sizing) 業界整合 verify**:
  - phase_flow_v4 v7 改善 4 動的合成方式 8 (= Half-Kelly + Vol target + cluster 強度別) は業界整合 ✅
  - crypto 高 vol で **Quarter-Kelly 候補** (= 推定誤差バッファ大) — 比較追加候補
  - cluster 強度別配分 → **HRP/HERC で robust 化** (= L-226 §18.3 整合)
- **工程 5 (Exit ML) 業界比較ベースライン拡張**:
  - 主軸 PPO 維持 (= §13.4 78% success rate)
  - 比較 1 = **Chandelier Exit (N=288 5m / M=2.5 crypto 調整)** — 新規追加
  - 比較 2 = **Wilder Volatility Stop (N=84 / M=2.0)** — 新規追加
  - 比較 3 = Fixed % Stop (= 旧 Priority 構造) — 維持 baseline
  - Partial TP + ATR Trailing (= 50% fixed TP + 50% ATR trail) を Phase 4-b に追加
- **工程 6 (Risk 管理) レイヤー新設**:
  - **TIPP drawdown floor** (= X=0.9・MDD < 10% target)
  - **Dynamic Deleveraging** (= drawdown / vol spike / regime trigger の OR)
  - CPPI は見送り (= whipsaw リスク)
- **Phase 5 / 6-b 合格判定多重防御 (= L-225 + v5 統合)**:
  - 必達 = 月次 NET ≥ $1,900 全月クリア
  - 追加 = DSR > 0.95 + PBO < 0.5 (v3)
  - **追加 = Calmar > 2.0 + CVaR_95 < $X/月 + Sortino > 1.5** (v5) — crypto 業界推奨
- **0.12 BTC 合計上限との整合**:
  - vol targeting / TIPP / HRP で得られる weight が 0.12 を超えても **必ず clip** (= CLAUDE.md §0-2 絶対規定)
  - pyramiding 全層合計 ≤ 0.12 BTC 必須
- **regime 別 risk measure** (= MDPI 2026 業界推奨):
  - down regime で CVaR 閾値厳しめ / range regime で緩め
  - 工程 1 regime 出力と工程 6 risk threshold を動的接続

#### 関連 lessons + 関連 memory

- L-223 (= ボラ予測 ML 設計欠陥) / L-224 (= アルゴリズム多様性) / L-225 (= 領域 3-4) / L-226 (= 領域 5) — v5 学習の直接動機
- cc_role §1.4.6.1 9 項目 (= ML pipeline 設計提案前の業界整合 verify) — 本領域学習で 6-9 番を蓄積
- feedback_trade_ml_knowledge_gap (= 業界標準理解不足) — v5 で補強進展 (= 領域 6 まで業界カタログ構築済・残り = 領域 7)
- CLAUDE.md §0-2 (= 0.12 BTC 合計上限) — 全リスク管理手法で clip 義務
- phase_flow_v4 v7 改善 4 (= 動的合成方式 8) — Half-Kelly + Vol target + cluster 強度別の業界整合 verify 済

---

## §20 ML 監視運用 (WORKFLOW 改訂39 領域 7・業界カタログ)

> v6 追記 (2026-05-25)。**「本番投入後にモデル劣化を検知し、再学習・切替・撤退を自動運用するレイヤー」の業界カタログ**。L-227 で確定した残り 1 領域 (= 領域 7) を本章で完成させ、案 B (= ChatGPT 7 工程フレーム範囲の ML 知識 7 領域カタログ化) を **7/7 = 100% 完了** する。§17.8 で部分網羅した KL/Wasserstein/Page-Hinkley を §20.1 で拡張統合し、Online learning / A/B testing / Champion-Challenger / Shadow deployment / Production ML monitoring の 5 領域を追加。ChatGPT 7 工程フレームの **工程 7 (Online 監視)** に直結。Phase 7-c / 7-d / 7-e (= Bot 統合 + デモ + 本番) の運用層実装設計に直接効く。

### §20.1 Concept Drift Detection 拡張 (= §17.8 統合 + 業界主要手法網羅)

#### 業界 3 カテゴリ + 主要 8 手法

| カテゴリ | 手法 | 仕組み | 業界用途 |
|---|---|---|---|
| **分布比較** | KL Divergence | 訓練分布 P vs 本番分布 Q の情報量差 | feature distribution drift 検出 |
| **分布比較** | Wasserstein Distance | 分布間 optimal transport cost | KL より外れ値耐性高い・離散/連続両対応 |
| **分布比較** | **KSWIN** (Kolmogorov-Smirnov Windowing) | KS 統計検定で分布変化検出・**分布仮定なし** | 業界推奨・[scikit-multiflow KSWIN](https://scikit-multiflow.readthedocs.io/en/stable/api/generated/skmultiflow.drift_detection.KSWIN.html) |
| **誤差ベース** | **DDM** (Drift Detection Method) | model 予測誤差率の monitoring・PAC learning モデル前提 | 業界 default・[scikit-multiflow DDM](https://scikit-multiflow.readthedocs.io/en/stable/api/generated/skmultiflow.drift_detection.DDM.html) |
| **誤差ベース** | **EDDM** (Early DDM) | 連続 2 誤差間の平均距離 monitoring・gradual drift 検出強化 | DDM 補完・[scikit-multiflow EDDM](https://scikit-multiflow.readthedocs.io/en/stable/api/generated/skmultiflow.drift_detection.EDDM.html) |
| **適応窓** | **ADWIN** (Adaptive Windowing) | 可変サイズ sliding window で earlier vs recent 統計差を検出 | 業界 default・[scikit-multiflow ADWIN](https://scikit-multiflow.readthedocs.io/en/stable/api/generated/skmultiflow.drift_detection.ADWIN.html) |
| **逐次変化点** | **Page-Hinkley (PH)** | CUSUM 系・累積偏差が閾値超で alert・**1 sample ずつ処理 (= memoryless)** | online 単変量モニタ・[River PageHinkley](https://riverml.xyz/dev/api/drift/PageHinkley/) |
| **逐次変化点** | CUSUM / EWMA control chart | 古典統計品質管理・累積/指数平均 | infrastructure observability 系 |

#### Page-Hinkley の業界実装核心

[GeeksforGeeks Page-Hinkley](https://www.geeksforgeeks.org/artificial-intelligence/page-hinkley-method/) + [Akira's Blog Change Detection](https://akiraaptx.blog/2017/02/15/change-detection-for-time-series-signals/) + [R Page-Hinkley datadriftR](https://search.r-project.org/CRAN/refmans/datadriftR/html/PageHinkley.html):

```
m_t = sum_{i=1}^{t} (x_i - mean_t - δ)    # 累積偏差 (δ = 許容ドリフト)
M_t = min(m_1, ..., m_t)                   # 累積最小
PH_t = m_t - M_t                            # 累積最小からの増加幅
alert if PH_t > λ                           # λ = 業界相場 50-100 (= 感度パラメータ)
```

**特徴**:
- 1 sample 処理で stream 全体保存不要 → real-time / low memory に最適
- 「**fraud detection / system health tracking で業界 default**」 ([GeeksforGeeks](https://www.geeksforgeeks.org/artificial-intelligence/page-hinkley-method/))
- 弱点 = 分布全体でなく **平均値変化のみ** 検出 → 分布形状変化 (= 分散増 / skewness 変化) は別手法 (= KSWIN / Wasserstein) と併用必須

#### ADWIN の業界実装核心

[scikit-multiflow ADWIN](https://scikit-multiflow.readthedocs.io/en/stable/api/generated/skmultiflow.drift_detection.ADWIN.html) + [Medium Wang model drift](https://medium.com/@jwang.ml/model-drift-detection-100a35a5edfa):

- window を 2 sub-window に分割・各 sub-window の平均値差が Hoeffding bound 超えた瞬間に「drift 確認 + window shrink」
- **delta (= 信頼度パラメータ)**: 業界 default 0.002 (= 0.2% false alarm rate)
- 強み = **可変 window size で gradual + abrupt 両方検出可能**
- 弱み = メモリ消費 (= window 保持) で高頻度更新時にやや重い

#### DDM vs EDDM の業界使い分け ([Medium Model Drift](https://medium.com/@jwang.ml/model-drift-detection-100a35a5edfa))

| 手法 | 検出が得意 | パラメータ |
|---|---|---|
| DDM | **abrupt** drift (= 急変) | warning_level=2σ / drift_level=3σ |
| EDDM | **gradual** drift (= 緩変) | alpha=0.95 (= warning) / beta=0.90 (= drift) |

業界 best practice: DDM + EDDM 並走で abrupt + gradual 両カバー

#### KL / Wasserstein の数式詳細

| 手法 | 数式 | 業界使用パターン |
|---|---|---|
| **KL Divergence** | `D_KL(P\|\|Q) = Σ P(x) log(P(x)/Q(x))` | 非対称 (P=訓練 / Q=本番)・**Q(x)=0 で発散** → smoothing 必須 |
| **Wasserstein** | `W_p(P,Q) = inf E[\|X-Y\|^p]^(1/p)` (optimal transport) | 対称・外れ値耐性高・連続分布で勾配ベース最適化可能 |
| **Maximum Mean Discrepancy (MMD)** | RKHS 距離 (kernel ベース) | **高次元** 入力で頑健・WebSearch 関連で多用 |

#### Production ML での 3 階層 drift 整理 ([Galileo MLOps Guide](https://galileo.ai/blog/mlops-operationalizing-machine-learning) + [Towards Data Science Model Drift](https://towardsdatascience.com/how-to-detect-model-drift-in-mlops-monitoring-7a039c22eaf9/) + [DevOps Roles Drift Strategies](https://www.devopsroles.com/ultimate-strategies-master-mlops-model-drift)):

1. **Data drift** (= 入力分布変化): KSWIN / KL / Wasserstein で入力 feature 分布の本番 vs 訓練 比較
2. **Concept drift** (= 入力↔出力関係変化): DDM / EDDM / PH で予測誤差率の monitoring
3. **Model performance drift** (= business metric 劣化): Sharpe / 月次 NET / Calmar / DD の sliding window comparison

→ cat-bitget 接続: 1 = 工程 3 特徴量 / 2 = 工程 3 + 5 ML 予測 / 3 = 工程 6 Risk 管理 / Phase 5-6-b PnL 指標

#### cat-bitget 適用判断 (= 工程 7 Online 監視 主軸候補)

- **主軸**: **ADWIN + KSWIN + Page-Hinkley の 3 種類並走**
  - ADWIN = 工程 3 LightGBM/XGBoost 予測精度の sliding monitor (= delta=0.002)
  - KSWIN = 入力 feature 分布 (= realized_vol / ATR / OBI 等の主要 10-20 feature) の本番 vs 訓練比較
  - Page-Hinkley = 月次 NET / 勝率の累積偏差 monitor (= λ=100 から start)
- **業界ライブラリ採用**: [River](https://riverml.xyz/) を主軸 (= scikit-multiflow と creme 統合・業界 default)
- **alert 多段化**: warning → drift confirmed → auto-rollback or 再学習トリガ
- **Phase 7-c / 7-d 実装影響**: bot 起動時に drift detector 3 種を init → 各推論時に 1 sample ずつ update → alert 検出時に既存 §20.4 Champion-Challenger 構造へ切替

### §20.2 Online Learning / Incremental Models (= River + scikit-multiflow + Incremental Boosting)

#### 業界 3 系統

| 系統 | 仕組み | 業界ライブラリ |
|---|---|---|
| **Streaming ML フレームワーク** | 1 sample ずつ partial_fit | **River** (= 業界 default・creme + scikit-multiflow 統合) / scikit-multiflow / Vowpal Wabbit |
| **Incremental GBDT** | 既存 model に新規 boosting round 追加 (= warm start) | LightGBM / XGBoost (= 業界実証あり) |
| **Online DL** | mini-batch SGD で online update | PyTorch / TensorFlow (= 標準) |

#### River 業界実装核心

[River arxiv 2012.04740](https://arxiv.org/pdf/2012.04740) + [JMLR River 2021](https://www.jmlr.org/papers/volume22/20-1380/20-1380.pdf) + [Medium Nehal Incremental](https://nehalaggarwal.medium.com/incremental-online-learning-using-river-a9df031615b0) + [Medium Virajdatt Streaming](https://kvirajdatt.medium.com/incremental-machine-learning-for-streaming-data-with-river-part-1-f0131459e85b):

- 「**creme + scikit-multiflow merge → River**」(= 2021)・現状 streaming ML 業界 default
- API = sklearn と類似だが **`learn_one(x, y)` + `predict_one(x)`** で 1 sample 単位
- 提供 model:
  - Linear (= Logistic Regression / Perceptron)
  - Tree (= Hoeffding Tree / Adaptive Random Forest)
  - Ensemble (= ARF / SRP・Streaming Random Patches)
  - Neighbor (= kNN-Window / SAM-kNN)
  - Drift-aware (= ADWIN-Bagging / Leveraging Bagging)
- **time-series 自己適応**: 「non-stationary 環境で target value 変化に自動 adapt」(= [River 公式](https://riverml.xyz/0.11.1/))

#### scikit-multiflow との関係

[scikit-multiflow](https://scikit-multiflow.readthedocs.io/) は **River の前身の 1 つ** (= 2018-2021)。現在は River に統合済だが、API 互換性のため scikit-multiflow 単体使用も業界に残存。drift detector (= ADWIN/DDM/EDDM/KSWIN) は scikit-multiflow.drift_detection module で API 提供。

#### Incremental LightGBM / XGBoost ([Medium Data Science Collective](https://medium.com/data-science-collective/incremental-learning-in-lightgbm-and-xgboost-9641c2e68d4b) + [Medium Kiran XGBoost](https://medium.com/@kirankumar_61999/incremental-learning-with-xgboost-a77bcb71e20b) + [GitHub ylogx XGBoost Incremental](https://gist.github.com/ylogx/53fef94cc61d6a3e9b3eb900482f41e0))

##### LightGBM incremental

```python
# 初回学習
model = lgb.train(params, train_data, num_boost_round=100)
# 増分学習 (新データで boost round 継続)
model = lgb.train(params, new_train_data,
                  num_boost_round=20,
                  init_model=model)  # 既存 model を warm start
```

- 業界実証: 「**1 sample 追加で 58.2x 高速化** (LightGBM)・**974.3x 高速化** (XGBoost)」 ([OpenReview Online GBDT](https://openreview.net/pdf?id=8G2CvYlfjw))
- 5-10 分で update 完了 ([Medium Data Science Collective](https://medium.com/data-science-collective/incremental-learning-in-lightgbm-and-xgboost-9641c2e68d4b))

##### XGBoost incremental

```python
model = xgb.train(params, dtrain, num_boost_round=100)
model = xgb.train(params, new_dtrain,
                  num_boost_round=20,
                  xgb_model=model)  # 既存 model を warm start
```

#### Online learning + Drift detection 統合パターン

業界 default ([Galileo MLOps](https://galileo.ai/blog/mlops-operationalizing-machine-learning)):

1. **drift detector** (= §20.1) が alert
2. **warning level**: monitoring 強化 (= alert 履歴蓄積)
3. **drift confirmed level**: incremental learning で warm start update or 完全再学習
4. **performance verify**: §20.5 Shadow deployment で旧 model と並走比較
5. **採用判定**: §20.4 Champion-Challenger で段階的切替

#### Cold start 問題と業界対応

[arxiv 2305.09907 Incremental Outlier Detection](https://arxiv.org/pdf/2305.09907): 「real-time modeling は cold start 問題を抱える (= 初期データ不足で誤分類率高) → **hybrid framework** (= 初期 batch 訓練 + 増分学習) で解決」

cat-bitget 接続: Phase 1-3 で初期 batch 学習 (= 5 年データ) → Phase 7-d 以降で online 増分学習を継続

#### crypto online learning の業界実証

[arxiv 2510.08068 Adaptive Multi-Agent Bitcoin Trading](https://arxiv.org/pdf/2510.08068) + [arxiv 2201.04699 Recurrent RL Crypto Agent](https://arxiv.org/pdf/2201.04699) + [arxiv 2303.07925 Deep Incremental Financial Temporal Tabular](https://arxiv.org/pdf/2303.07925) + [Frontiers Predicting Bitcoin AI](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1519805/full):

- crypto は extreme volatility + regulatory announcements + macroeconomic shifts で **static model が陳腐化早い** → online learning + frequent retraining が業界必須
- echo state network + recurrent RL での online transfer learning が BTC perpetual swap intraday trading で実証
- Multi-Agent LLM-based reflection で **continual self-improvement** 構造が 2025 trend

#### cat-bitget 適用判断 (= 工程 7 主軸候補)

- **主軸**: **River + Incremental LightGBM/XGBoost のハイブリッド**
  - River: Hoeffding Tree + ADWIN-Bagging で **drift 自動対応** の secondary monitor (= primary model と並走・predict 比較)
  - Incremental LightGBM/XGBoost: 工程 3 primary model を **週次 / 月次** で warm start update (= 5-10 分で完了)
- **再学習トリガ**: drift detector alert → incremental update (= 月 1 回 baseline + drift alert で臨時)
- **完全再学習**: 半年 / 年次で from scratch 再学習 (= 5 年データ全部使う) + walk-forward verify
- **Phase 7-c / 7-d 実装影響**: River と LightGBM/XGBoost を同 process に同居・推論時に両者の predict 一致率を Monitor (= concept drift early signal)

### §20.3 A/B Testing + Multi-Armed Bandit + Thompson Sampling

#### 業界 3 系統

| 手法 | 仕組み | 業界用途 |
|---|---|---|
| **Classical A/B** | traffic 50/50 (= fixed split) + 統計検定で 比較 | 単純比較・サンプル数大要 |
| **Multi-Armed Bandit (MAB)** | exploration/exploitation balance で動的 traffic 配分 | sample 効率高・後悔最小化 |
| **Thompson Sampling** | Bayesian 事後分布から確率 sampling で arm 選択 | **業界推奨**・[arxiv 1111.1797](https://arxiv.org/pdf/1111.1797) |
| **UCB / LinUCB** | confidence bound でリスク調整 arm 選択 | linear context 入力可能 |
| **Contextual Bandit** | 状況 context (= 入力 feature) で arm 選択 | regime / vol / time-of-day で動的 |

#### Thompson Sampling の業界数式

[arxiv 1111.1797 Analysis of Thompson Sampling](https://arxiv.org/pdf/1111.1797) + [GitHub multi-armed thompson](https://github.com/tbagnoli/multi_armed_thompson) + [Daheekwon Dynamic TS PDF](https://daheekwon.github.io/pdfs/dynamicTS.pdf):

```
for each arm i:
    sample θ_i ~ Beta(α_i, β_i)    # Bernoulli reward の事後分布
choose arm = argmax(θ_i)
observe reward r ∈ {0, 1}
update: α_i += r, β_i += (1-r)
```

- **continuous reward**: Beta → Normal 事後分布に拡張 (= Gaussian Thompson Sampling)
- 業界優位性: 「**arm 数増加に robust + parameter 不要 + Bayesian regret bound 最適**」
- batched 拡張: [arxiv 2108.06812 Batched Thompson Sampling](https://arxiv.org/pdf/2108.06812) で複数 sample 同時処理

#### Adaptive Portfolio via Thompson Sampling

[arxiv 1911.05309 Adaptive Portfolio Multi-armed Bandit Thompson Sampling](https://arxiv.org/pdf/1911.05309): 「**複数の古典 trading strategy を arm として bandit framework に投入** → Thompson Sampling で online portfolio choice → arm performance のトレードオフを最大化」を実証

→ cat-bitget 接続: 工程 3 + 5 で複数 ML model (= LightGBM / XGBoost / GRU の各 cluster 出力) を arm 化 → Thompson Sampling で動的 weighting

#### Contextual Bandit + LinUCB

[arxiv 1305.2415 Exponentiated Gradient LinUCB](https://arxiv.org/pdf/1305.2415) + [ScienceDirect S0957417423001781 Contextual Combinatorial Bandit Portfolio](https://www.sciencedirect.com/science/article/abs/pii/S0957417423001781) + [arxiv 1902.07802 AdaLinUCB](https://arxiv.org/pdf/1902.07802) + [NumberAnalytics Contextual Bandits Guide](https://www.numberanalytics.com/blog/contextual-bandits-machine-learning-guide):

- **LinUCB**: 「linear connection between context features and reward + UCB ベース exploration」(= optimism in face of uncertainty)
- 業界実証: 「**supervised adaptive decision tree で candidate portfolio pool → LinUCB で update rule 学習**」(= institutional + individual trader 向き)
- **Parallel LinUCB / Parallel LinTS**: 2025 trend = batch action selection で **diversity 確保 + regret burn-in 最小化**

→ cat-bitget 接続: 工程 1 regime 出力 (= up/range/down) を context として LinUCB で「regime × strategy」配分の動的最適化

#### Dynamic A/B Testing for ML Models on AWS SageMaker

[AWS Blog Dynamic A/B Testing SageMaker](https://aws.amazon.com/blogs/machine-learning/dynamic-a-b-testing-for-machine-learning-models-with-amazon-sagemaker-mlops-projects/): 「**Thompson Sampling で Challenger variant 選択確率が outperform に応じて自動上昇** → 動的 Champion-Challenger 切替」を業界 default 実装として提供

#### crypto trading での A/B testing 実証

[Medium Adrian Keller 7 Years Crypto ML](https://medium.com/@laostjen/machine-learning-models-that-actually-work-in-crypto-trading-78a6735b5639): 「ML production crypto trading 7 年経験 → **foundation (= data / strategy / risk) が weak だと ML が損失を amplify する**」 = A/B testing は ML 単独でなく portfolio 全体の foundation を verify する設計が必須

[MDPI 14/5/761 Bayesian vs Evolutionary Crypto Perpetual](https://www.mdpi.com/2227-7390/14/5/761): 「**crypto は noisy non-stationary objective landscape** → 通常 ML benchmark の Bayesian optimization が機能しにくい」 = bandit ベース動的選択が業界整合

#### cat-bitget 適用判断 (= 工程 7 Online 監視 + 工程 4 Position Sizing 接続)

- **採用候補**: **Thompson Sampling (Beta-Bernoulli) で多 cluster × Exit type × side 戦略の動的 weighting**
  - phase_flow_v4 v7 改善 4 動的合成方式 8 (= Half-Kelly + Vol target + cluster 強度別) の cluster 強度別配分を Thompson Sampling で online update 化
  - L-226 §18.3 HRP/HERC との関係: HRP/HERC = 戦略間 risk parity / TS = 戦略間 reward maximize → **両者並走候補** (= HRP で risk constraint + TS で reward exploration)
- **次段拡張**: Contextual LinUCB で工程 1 regime 出力を context 化 → regime ↔ strategy 動的接続
- **Phase 7-c / 7-d 実装影響**: Thompson Sampling の posterior 更新 (= α/β counter) は in-memory + persistent (= state file) で実装軽量

### §20.4 Champion-Challenger 構造 (= 並走 → 段階的切替の業界標準フロー)

#### 業界フロー ([DataRobot MLOps Champion-Challenger](https://www.datarobot.com/blog/introducing-mlops-champion-challenger-models/) + [H2O MLOps Champion-Challenger](https://docs.h2o.ai/mlops/v0.64.0/py-client/py-client-examples/champion-challenger-deployment) + [Snowflake ML Champion-Challenger Retraining](https://www.snowflake.com/en/developers/guides/ml-champion-challenger-model-deployment/) + [Minitab Champion-Challenger](https://support.minitab.com/en-us/model-ops/import-and-deploy-models/use-champion-challenger-models-in-a-deployment/))

```
[Champion: 現本番 model]   ←→   [Challenger 1, 2, 3, ...: 新候補]
       ↓ all traffic                   ↓ shadow / partial traffic
       実行・PnL 確定                  並走・metric 比較
                                           ↓
                                  Challenger > Champion 検出
                                           ↓
                              traffic split 1% → 5% → 20% → 50% → 100%
                                           ↓
                                  Challenger が新 Champion 昇格
                                  旧 Champion を fallback 化
```

#### Traffic Split 業界 default ([Clarifai AI Deployment](https://www.clarifai.com/blog/ai-model-deployment-strategies) + [Dagshub Model Deployment](https://dagshub.com/blog/model-deployment-types-strategies-and-best-practices/) + [Medium Fraidoon Evaluation Strategies](https://medium.com/@fraidoonomarzai99/deployment-evaluation-strategies-in-mlops-c208585aa3bd))

| stage | Challenger traffic | gating criteria |
|---|---:|---|
| Shadow | 0% (= log only) | drift / performance metrics ≥ Champion |
| Canary | 1% | error rate / latency / PnL ≥ Champion 信頼区間下端 |
| Ramp 1 | 5% | 同上 + Sharpe / Sortino 改善 |
| Ramp 2 | 20% | 同上 + 月次 NET 改善 |
| Ramp 3 | 50% | 同上 + DSR / PBO 改善 |
| Full | 100% | Challenger 採用・旧 Champion fallback 化 |

各 stage で gating criteria 未達 → auto-rollback (= 旧 Champion 復帰)

#### Champion-Challenger と A/B / MAB の関係

- **Classical A/B**: 単純 fixed split + 統計検定 (= 50/50 で N sample 確保)
- **Multi-Armed Bandit (= TS / UCB)**: 動的 split で sample 効率最大化
- **Champion-Challenger**: **deployment process** (= shadow → canary → ramp) 自体が業界 default フロー
- → 業界 best practice: Champion-Challenger フローの **各 stage 内で A/B or MAB を実施**

#### Production deployment 業界標準 ([Galileo MLOps](https://galileo.ai/blog/mlops-operationalizing-machine-learning))

「**Shadow deploy → controlled canary rollout → statistically rigorous online experiments → post-launch Champion-Challenger with automated rollback**」 = 全段ガード経路

#### cat-bitget 適用判断 (= 工程 7 主軸候補)

- **採用フロー**:
  1. **Shadow**: 新 model を Phase 7-d 開発環境で並走 (= 本番 paper_trading=False / Demo API 経由)
  2. **Canary 1%**: 新 model の signal を 1/100 frequency でのみ実発注 (= 旧 model 99/100)
  3. **Ramp 5/20/50%**: 月次 NET / Sharpe / Sortino / DD 改善で段階拡大
  4. **Full 100%**: 採用判定 → 旧 model を fallback として state 保持
- **gating criteria 具体値 (= cat-bitget Phase 6-b 整合)**:
  - 月次 NET ≥ $1,900 維持
  - DSR > 0.95 維持 (= L-225 §17.4)
  - PBO < 0.5 維持 (= L-225 §17.5)
  - Calmar > 2.0 (= L-227 §19.5)
  - 連続 N week 未達 → auto-rollback
- **0.12 BTC 合計上限制約**: 並走中も全 model の合計 ≤ 0.12 BTC 必須 (= CLAUDE.md §0-2 絶対規定)
- **Phase 7-c / 7-d 実装影響**: state file に Champion / Challenger 両 model の orderId / position を物理分離保存 → 各 model の PnL を独立集計

### §20.5 Shadow Deployment (= 本番影響ゼロでの新モデル評価)

#### 業界の根本構造

[SE-ML Shadow Deployment](https://se-ml.github.io/best_practices/04-shadow_models_prod/) + [JFrog Shadow vs Canary](https://www.qwak.com/post/shadow-deployment-vs-canary-release-of-machine-learning-models) + [Dataconomy Shadow Deployment 2025](https://dataconomy.com/2025/03/07/what-is-shadow-deployment/) + [Deepchecks Glossary Shadow Deployment](https://www.deepchecks.com/glossary/shadow-deployment/) + [ML Journey Shadow Mode](https://mljourney.com/shadow-mode-deployment-for-ml-model-testing/) + [DhiWise Shadow Deployment Guide](https://www.dhiwise.com/post/risk-free-production-testing-shadow-deployment):

```
全本番 traffic → 旧 Champion model (= 実発注 + 実 PnL)
            ↘
              新 Challenger model (= predict + log のみ・実発注なし)
              
比較: Champion 予測 vs Challenger 予測 + 仮想 PnL
```

- 「**実 traffic で実行 + 本番影響ゼロ**」(= 新 model の predict と仮想 PnL は log のみ)
- skew 検出: training vs production data 統計差 ([SE-ML](https://se-ml.github.io/best_practices/04-shadow_models_prod/))
- regulatory compliance: bias detection + ethical AI validation も shadow で実施 ([Dataconomy 2025](https://dataconomy.com/2025/03/07/what-is-shadow-deployment/))

#### AWS SageMaker Shadow Deployment ([AWS Blog Shadow ML SageMaker](https://aws.amazon.com/blogs/machine-learning/deploy-shadow-ml-models-in-amazon-sagemaker/) + [AWS Blog SageMaker Shadow Testing](https://aws.amazon.com/blogs/machine-learning/minimize-the-production-impact-of-ml-model-updates-with-amazon-sagemaker-shadow-testing/) + [Databricks Model Serving Shadow](https://community.databricks.com/t5/machine-learning/model-serving-shadow-deployment-azure/td-p/68066)):

- production traffic duplicate → 旧 + 新 両 model に送る + 全 request / prediction を log
- monitoring overhead: 旧 + 新 両 environment 監視で **データ処理 2 倍**
- 2025 trends: serverless shadow architecture + real-time perf optimization + advanced observability platform 統合

#### Shadow vs Canary の業界整理 ([JFrog Qwak](https://www.qwak.com/post/shadow-deployment-vs-canary-release-of-machine-learning-models))

| 観点 | Shadow | Canary |
|---|---|---|
| 実発注 | ❌ なし (= log only) | ✅ 部分発注 (= 1-5%) |
| 本番影響 | ゼロ | 部分 (= 失敗で部分損害) |
| 検証深度 | predict 比較・仮想 PnL | 実 PnL 検証 |
| 業界用途 | **採用前 risk-free 検証** | **採用後 gradual rollout** |
| 順序 | 1 番目 | 2 番目 (= Shadow PASS 後) |

#### cat-bitget 適用判断 (= 工程 7 主軸候補・Phase 7-d 実装)

- **採用フロー**:
  1. **Shadow stage 1 (= 開発環境)**: 新 model を Demo API (paper_trading=True) で実 5m bar 入力 + 仮想 PnL log のみ
  2. **Shadow stage 2 (= 本番並走 log only)**: 本番 API (paper_trading=False・但し新 model の signal は実発注しない) で本番 5m bar 同期入力 + 仮想 PnL log
  3. **Shadow PASS 判定**: 4 週間以上の Shadow で月次 NET ≥ $1,900 + DSR > 0.95 + PBO < 0.5 + Calmar > 2.0 達成
  4. → Canary 1% (= §20.4 Champion-Challenger フロー) へ
- **Shadow log 内容**:
  - 各 bar の entry signal (= 出した / 出さなかった)
  - 各 signal の仮想 entry price / size / Exit timing / Exit price / 仮想 PnL
  - 旧 Champion との signal 一致率 / 差分理由
- **0.12 BTC 合計上限制約**: Shadow stage では実発注なし → 制約非適用・但し仮想 PnL も 0.12 BTC clip 同条件で計算
- **Phase 7-d 実装影響**: state file に shadow_predictions.jsonl を append・本番 trade との完全物理分離

### §20.6 Production ML Monitoring (= 3 階層観測 + business metrics)

#### 業界 3 階層 ([Galileo MLOps](https://galileo.ai/blog/mlops-operationalizing-machine-learning) + [Durapid MLOps Monitoring](https://durapid.com/blog/mlops-model-monitoring-how-to-track-model-drift-and-performance-in-production/) + [WetransCloud MLOps Observability](https://wetranscloud.com/blog/mlops-observability-model-performance) + [Fiddler ML Monitoring](https://www.fiddler.ai/ml-model-monitoring/ml-model-monitoring-best-practices))

| 階層 | 監視対象 | 業界 default ツール |
|---|---|---|
| **Infrastructure observability** | CPU / memory / latency / queue depth | Prometheus + Grafana |
| **Data observability** | schema / null rate / value distribution | Great Expectations / Monte Carlo |
| **Model observability** | prediction distribution / drift score / business KPI | Fiddler / Arize / WhyLabs / 自前 |

「これら 3 層で **what / why / how to fix** の full visibility 確保」 ([Galileo MLOps](https://galileo.ai/blog/mlops-operationalizing-machine-learning))

#### Data Quality の業界実証

[Monte Carlo MLOps Monitoring](https://www.montecarlodata.com/blog-mlops-engineer-and-model-monitoring/) + [KDnuggets Model Drift MLOps](https://www.kdnuggets.com/2023/05/managing-model-drift-production-mlops.html): 「**data quality issues が algorithm 問題より多い model failure 原因** + IBM 2023 study では poor data quality で年 $12.9M 損失」 = 監視の **第一の関所は Data observability**

#### 4 critical monitoring techniques ([Monte Carlo](https://www.montecarlodata.com/blog-mlops-engineer-and-model-monitoring/))

1. **Statistical performance monitoring** (= accuracy / precision / recall / F1 / AUC drift)
2. **Drift detection** (= §20.1 統合)
3. **Data quality monitoring** (= schema / null / outlier rate)
4. **Business KPI monitoring** (= revenue / conversion / cost saving = cat-bitget では 月次 NET)

#### Business metric layer の業界整理 ([Fiddler](https://www.fiddler.ai/ml-model-monitoring/ml-model-monitoring-best-practices) + [arxiv 2007.06299 Monitoring Production Explainability](https://arxiv.org/pdf/2007.06299))

- Statistical model metric (= AUC / log_loss) と Business metric (= 売上 / NET) が **乖離する事例多発**
- 「**model のみ良くて business 悪化**」 = 監視の盲点
- 業界 best practice: model metric + business metric の両方を log + 乖離 alert

#### cat-bitget 適用判断 (= 工程 7 全 Phase 統合監視)

- **Infrastructure observability** (= Phase 7-c / 7-d / 7-e):
  - API rate limit (= Bitget 10 req/s) の余裕監視
  - latency (= 推論 + 発注 RTT)
  - process memory / CPU (= 5m bot で軽量目標)
  - WebSocket connection health (= microstructure 入力時・§16.6)
- **Data observability** (= 全 Phase):
  - 入力 5m bar の null / outlier 検出
  - 1432 / 2604 特徴量の分布 monitor (= KSWIN 連携・§20.1)
  - Funding Rate / Bitget API stream の健全性
- **Model observability** (= 工程 3 + 5 + 6):
  - LightGBM/XGBoost の prediction distribution drift (= ADWIN・§20.1)
  - TP first 確率 distribution の sliding histogram
  - Half-Kelly 出力 size の分布 monitor
  - PPO 確率の entropy monitor (= exploration vs exploitation balance)
- **Business metric** (= 必達):
  - 月次 NET (= 全月 ≥ $1,900・CLAUDE.md / project_goal)
  - 日次 NET sliding (= 異常検知)
  - 勝率 sliding (= 50-60% range)
  - DD (= MDD < 10-15% target・§19.3)
  - Sharpe / Sortino / Calmar (= L-227 §19.5)
- **alert 多段化**:
  - INFO (= drift warning / 単月未達)
  - WARN (= drift confirmed / 連続 2 週未達)
  - CRITICAL (= 急変 / 連続 1 ヶ月未達 / DD 15% 超え → 自動 deleveraging)

### §20.7 領域 7 まとめ: 7 工程接続 + cat-bitget 設計判断調査ノート + **案 B 学習完了宣言**

#### 7 工程接続マトリックス (= 監視運用レイヤー全工程適用)

| 工程 | 監視・運用の改善方向 | 業界整合手法 |
|---|---|---|
| 1 regime | regime label drift monitor (= HMM 状態 transition probability の sliding 比較) | §20.1 ADWIN |
| 2 Entry 候補生成 | 候補発火頻度の drift monitor (= time-of-day distribution) | §20.1 KSWIN |
| 3 Entry ML | **prediction distribution drift + feature distribution drift + incremental update** | §20.1 + §20.2 |
| 4 Position Sizing | **Half-Kelly 出力 size + Thompson Sampling で動的 weighting** | §19.4 + §20.3 |
| 5 Exit ML | PPO probability entropy monitor + Champion-Challenger で新 Exit model 試行 | §20.4 |
| 6 Risk 管理 | DD / vol spike / regime trigger の OR 監視 (= §19.3 整合) + business metric layer | §19.3 + §20.6 |
| **7 Online 監視** | **全工程の drift detection + Online update + A/B/MAB + Shadow + Champion-Challenger + 3 階層 observability** | **§20.1-§20.6 全章** |

#### cat-bitget Phase 7-c / 7-d / 7-e 運用層設計判断調査ノート (= v6 学習成果)

> ⚠️ 以下は **学習資料の調査ノート位置付け**。実際の設計確定は WORKFLOW 改訂40 active の優先 3 (= 工程 2-7 詳細詰め) で別途実施 (cc_role §1.5 デザイン責任)。

##### v6 (= 領域 7) の追加確定事項

- **Phase 7-c 実装基盤**:
  - **drift detector 3 種並走** (= ADWIN + KSWIN + Page-Hinkley) を bot init で起動
  - **River + Incremental LightGBM/XGBoost** ハイブリッドで online learning 基盤
  - 各推論時に 1 sample drift update + 週次 incremental retrain + 半年 from scratch retrain
- **Phase 7-d Shadow deployment**:
  - 新 model の signal を Demo API で 4 週間以上 paper trading 検証
  - Shadow log で月次 NET ≥ $1,900 + DSR + PBO + Calmar 全て達成 → Canary 1% へ
- **Phase 7-e Champion-Challenger 段階 rollout**:
  - 1% → 5% → 20% → 50% → 100% の 5 段階 ramp
  - 各 stage で gating criteria 未達 → auto-rollback
  - 0.12 BTC 合計上限を Champion + Challenger 全 model 横断で守る
- **Thompson Sampling 動的 weighting**:
  - 工程 4 動的合成方式 8 (= Half-Kelly + Vol target + cluster 強度別) の cluster 強度別配分を online TS で update
  - HRP/HERC (= §18.3) と並走候補 (= HRP で risk constraint + TS で reward exploration)
- **3 階層 observability + business metric 統合**:
  - Infrastructure (= Bitget API latency / process memory) + Data (= 1432 feature null / drift) + Model (= prediction drift) + Business (= 月次 NET / DD / Calmar)
  - INFO / WARN / CRITICAL 3 段 alert + CRITICAL で自動 deleveraging

##### Phase 1 v6 6 案全滅の構造的原因 → 監視運用レイヤー欠落の補強整理

L-227 §19.6 で確定した 7 軸多様性欠落に **第 8 軸 = 運用層 (= drift detection / online learning / 動的切替) 設計不在** を追加:

| # | 原因 | 補強領域 | v6 学習成果 |
|---|---|---|---|
| 1 | ボラ予測 ML 設計欠陥 | L-223 | §13.1 + §14.6 |
| 2 | アルゴ多様性ゼロ | L-224 + arxiv 2512.15738 | §18.1 |
| 3 | bar 種別多様性ゼロ | L-225 + §16.1 | §16.1 |
| 4 | cascade 構造不在 | v4 §18.2 | §18.2 |
| 5 | strategy allocation 機械固定 | v4 §18.3 | §18.3 |
| 6 | Meta-Labeling 同型 | L-223 + v4 §18.4 | §18.4 |
| 7 | リスク管理レイヤー不在 | v5 §19 | §19.1-§19.4 |
| **8** | **運用層 (= drift detection / online learning / 動的切替) 設計不在** | **v6 §20 新規** | **§20.1-§20.6** |

→ 旧 Priority / Phase 1 v6 は「static model + 固定 weight + 手動切替」で **non-stationary crypto 市場で陳腐化早い** 構造的欠陥。v6 で運用層 (= drift 自動検出 + online incremental update + Thompson Sampling 動的 weighting + Champion-Challenger 段階切替 + Shadow 検証 + 3 階層 observability) の業界実装パターンを確立。

#### 関連 lessons + 関連 memory

- L-223 (= ボラ予測 ML 設計欠陥) / L-224 (= アルゴ多様性) / L-225 (= 領域 3-4) / L-226 (= 領域 5) / L-227 (= 領域 6) — v6 学習の直接動機
- cc_role §1.4.6.1 9 項目 (= ML pipeline 設計提案前の業界整合 verify) — 本領域学習で 6-9 番を蓄積
- feedback_trade_ml_knowledge_gap (= 業界標準理解不足) — **v6 で完全補強 (= 7/7 = 100%)**
- CLAUDE.md §0-2 (= 0.12 BTC 合計上限) — 運用層でも全 model 横断 clip 義務

#### 🎉 案 B 学習完了宣言 (= 7/7 = 100%)

**案 B (= ChatGPT 7 工程フレーム範囲の ML 知識体系化) 完了**:

- 領域 1 (ML 学習方法・§13・v2) ✅
- 領域 2 (ML 学習項目・§14・v2) ✅
- 領域 3 (ML 特徴量設計・§16・v3) ✅
- 領域 4 (ML 評価方法・§17・v3) ✅
- 領域 5 (ML 組合せ手法・§18・v4) ✅
- 領域 6 (ML リスク管理・§19・v5) ✅
- **領域 7 (ML 監視運用・§20・v6) ✅** ← **本セッション完成**

総計: WebSearch 84 件 + 教科書引用 (AFML / MLfAT / mlfinlab / pypbo / River / scikit-multiflow / Riskfolio-Lib / PyPortfolioOpt 等) + arxiv 30+ 件 + 業界ライブラリ docs 多数。

これにより WORKFLOW 改訂39 active 優先 2 (= 案 B 学習継続) を完遂し、**次は WORKFLOW 改訂40 active 優先 3 (= 工程 2-7 詳細詰め = 設計確定)** に進む準備が整った。

---

## §11 改訂履歴

| 版 | 日付 | 内容 |
|---|---|---|
| v1 | 2026-05-25 | 初版・WebSearch 8 件 + 旧 Priority 実装 verify による分析 |
| v2 | 2026-05-27 | §13 ML 学習方法 (6 章) + §14 ML 学習項目 (8 章) + §15 総合所見 追加・WebSearch 14 件 + AFML Ch.3/6 + Oxford-Man + Hudson & Thames mlfinlab + arxiv 8 件 引用 |
| v3 | 2026-05-25 | **§16 ML 特徴量設計 (7 節) + §17 ML 評価方法 (9 節) 追加**・§15.2-15.4 を v3 完成状態に更新 (= 残り 5 領域 → 残り 3 領域)・WebSearch 16 件 + AFML Ch.2 (情報駆動 bars) / Ch.5 (Fractional Diff) / Ch.7 (Purged K-Fold + CPCV) / Ch.8 (MDI/MDA/SFI) / Ch.14 (DSR) + Bailey & Lopez de Prado 2014 (DSR / PBO) + MLfAT Ch.4 (Alpha Factor Research) + Hudson & Thames mlfinlab + arxiv 5 件 (microstructure 2602.00776 / 2506.05764 / Frontiers 2026 / MDPI 2026 / shap-select 2410.06815) 引用 |
| v4 | 2026-05-25 | **§18 ML 組合せ手法 (5 節) 追加**・§15.2-15.4 を v4 完成状態に更新 (= 残り 3 領域 → 残り 2 領域)・WebSearch 14 件 + AFML Ch.6 (Ensemble) / Ch.16 (Asset Allocation) + Lopez de Prado 2016 (HRP 原論文 SSRN 2708678) + Raffinot 2018 (HERC) + Hudson & Thames meta-labeling repo (GitHub) + Riskfolio-Lib + PyPortfolioOpt + arxiv 4 件 (Diversity 2407.12996 / FinRL Contest 2501.10709 / Hybrid Ensemble 2512.15738 / GAS Blending 2411.03035) + Viola-Jones cascade theory (Wikipedia + Grokipedia) 引用・**Phase 1 v6 6 案全滅の構造的原因を 6 軸多様性欠落に整理 (= v1-v4 統合)** ・Phase 1 v7 候補「案 g」設計判断調査ノートを §18.5 に確立 |
| v5 | 2026-05-25 | **§19 ML リスク管理 (6 節) 追加**・§15.2-15.4 を v5 完成状態に更新 (= 残り 2 領域 → 残り 1 領域)・WebSearch 8 件 + GARCH-family (TGARCH/EGARCH/CGARCH・Springer Future Business Journal 2025) + EWMA / HAR-RV + Chandelier Exit (ChartSchool + StratBase.ai + LuxAlgo 5 ATR Stop-Loss) + Wilder Volatility Stop + CPPI / TIPP (Wikipedia + Grokipedia + QuantPedia + Core AXA-IM) + Kelly criterion (Altrady + LBank + OSL + CMC + Stephen Perrenod) + Pyramiding (QuantStrategy 4 篇 + TradersPost + Forextester + FasterCapital + hoc-trade Medium) + CVaR (MDPI 2026 regime-tail-dependent crypto + arxiv 2406.00610 + Riskfolio-Lib + Stan Uryasev) + Time-Series Momentum + Vol Scaling (CFA Institute 2019 + AlphaArchitect + CME Group + ScienceDirect S1386418116301379 + CXO Advisory) + ML 動的 Stop (arxiv 2506.22055 LSTM+XGBoost + ScienceDirect 2025 DRL+LSTM+XGBoost feature selection + Springer 2025 ML crypto trading) + Amberdata Crypto Portfolio 引用・**6 軸多様性欠落に「第 7 軸 = リスク管理レイヤー不在」追加整理**・cat-bitget 設計判断調査ノートに v5 8 項目追加 |
| **v6** | 2026-05-25 | **§20 ML 監視運用 (7 節) 追加** = **案 B 学習完了 (= 7/7 = 100%)** ・§15.2-15.4 を v6 完成状態に更新 (= 残り 1 領域 → 残り 0 領域)・WebSearch 12 件 + River (arxiv 2012.04740 + JMLR 2021) + scikit-multiflow (ADWIN + DDM + EDDM + KSWIN) + Page-Hinkley (River PageHinkley + GeeksforGeeks + datadriftR) + Incremental LightGBM/XGBoost (Medium Data Science Collective + OpenReview Online GBDT) + Multi-Armed Bandit + Thompson Sampling (arxiv 1111.1797 + arxiv 1911.05309 Adaptive Portfolio + arxiv 2108.06812 Batched + Daheekwon Dynamic TS) + Contextual Bandit LinUCB (arxiv 1305.2415 + arxiv 1902.07802 AdaLinUCB + ScienceDirect S0957417423001781) + Shadow deployment (SE-ML + AWS SageMaker + JFrog Qwak + Dataconomy 2025 + ML Journey + Databricks) + Champion-Challenger (DataRobot + H2O MLOps + Snowflake + Clarifai + Dagshub + Medium Fraidoon) + AWS SageMaker Dynamic A/B Testing + Production ML Monitoring 3 階層 (Galileo + Durapid + WetransCloud + Fiddler + Monte Carlo + KDnuggets + DevOps Roles) + crypto online learning (arxiv 2510.08068 Multi-Agent Bitcoin + arxiv 2201.04699 Recurrent RL + arxiv 2303.07925 Deep Incremental Financial + Frontiers Predicting Bitcoin AI) + Hudson & Thames mlfinlab + Galileo MLOps Guide 引用・**7 軸多様性欠落に「第 8 軸 = 運用層 (= drift detection / online learning / 動的切替) 設計不在」追加整理**・cat-bitget 設計判断調査ノートに v6 7 項目追加・**案 B (= ChatGPT 7 工程フレーム範囲の ML 知識 7 領域カタログ化) を完了宣言** |

---

## §12 関連 memory / 正本

- [feedback_priority_starting_line_only.md](../../../../../.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_priority_starting_line_only.md) (= 旧 Priority はスタートライン参照のみ・ベースにしない)
- [technical_analysis_knowledge_base.md](technical_analysis_knowledge_base.md) (= 既存・指標辞典 + 閾値理論 + MTF 理論)
- [feedback_trade_ml_knowledge_gap.md](../../../../../.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_trade_ml_knowledge_gap.md) (= CC のトレード ML 業界標準理解不足)
- cc_role §1.7 (= 手動 Priority の位置づけ・絶対遵守)
- 旧 Priority 実装: [strategies/cat_v9_decider.py](../../strategies/cat_v9_decider.py) L240-587 + [config/cat_params_v9.json](../../config/cat_params_v9.json)
