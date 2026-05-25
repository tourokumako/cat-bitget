# cc_entry_logic_self_study.md — CC エントリーロジック自己学習資料 v3

作成: 2026-05-25 (CC・v1) / 改訂 2026-05-27 (v2) / 改訂 2026-05-25 (v3)
位置付け: まこさん命令 (2026-05-25) 「指標、閾値、時間の使い方を勉強しなおして」を受けた CC の学習資料。
状態: **v3 (= 領域 1-4 完成)**。WORKFLOW 改訂36 active 優先 2 = 案 B 学習継続 = 領域 3 (特徴量設計) + 領域 4 (評価方法) を v3 §16 + §17 として追加。WebSearch 16 件 + AFML Ch.2/5/6/7/8/14 + MLfAT Ch.4 + Bailey & Lopez de Prado 2014 (DSR/PBO) + Hudson & Thames mlfinlab blog + arxiv 5 件 引用。残り = 領域 5-7 を v4 として追加予定。

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

### 15.2 残り 3 領域 (= 次セッション以降 WORKFLOW 改訂36 優先 2 残り・v3 で領域 3-4 完成)

- ~~**領域 3 (ML 特徴量設計)**~~ → **v3 §16 で完成** (Fractional Differentiation / スケーリング / 特徴量選択 / 出来高系 / 板情報系)
- ~~**領域 4 (ML 評価方法)**~~ → **v3 §17 で完成** (Walk-Forward / Purged K-Fold / CPCV / Embargo / DSR / PBO / Pipeline leak 防止 / Concept drift)
- **領域 5 (ML 組合せ手法)**: §13.5 で部分網羅・残り = 階層 stacking / Cascade / Hierarchical Risk Parity / Meta-Labeling 多段詳細
- **領域 6 (リスク管理)**: §14.5 で Kelly 網羅・残り = Volatility targeting 詳細 (= Garch-DCC / Vol Forecast) / Stop-loss 業界手法 (= ATR-based / Chandelier / Volatility-Stop) / Drawdown control (= CPPI / TIPP) / Position scaling
- **領域 7 (監視・運用)**: §17.8 で部分網羅・残り = Online learning (= incremental LightGBM / River) / A/B testing (= multi-armed bandit) / Champion-Challenger 構造 / Shadow deployment

### 15.3 次セッションの推奨着手順位 (v3 完成 → 次は領域 5-7)

1. **領域 5 (組合せ手法)** を先行: 工程 3 + 工程 4 接続 (= Meta-Labeling 多段 / Hierarchical) の業界標準確立
2. **領域 6 (リスク管理)** を並行: 工程 4 Position Sizing + 工程 5 Exit ML の損切設計確立
3. **領域 7 (監視・運用)** は最後: 工程 7 Online 監視の業界標準確立 + 全 Phase 統合監視
4. 各領域 WebSearch 10-20 件 + 教科書 chapter 引用 (cc_role §1.4.6.1) を継続

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

## §11 改訂履歴

| 版 | 日付 | 内容 |
|---|---|---|
| v1 | 2026-05-25 | 初版・WebSearch 8 件 + 旧 Priority 実装 verify による分析 |
| v2 | 2026-05-27 | §13 ML 学習方法 (6 章) + §14 ML 学習項目 (8 章) + §15 総合所見 追加・WebSearch 14 件 + AFML Ch.3/6 + Oxford-Man + Hudson & Thames mlfinlab + arxiv 8 件 引用 |
| v3 | 2026-05-25 | **§16 ML 特徴量設計 (7 節) + §17 ML 評価方法 (9 節) 追加**・§15.2-15.4 を v3 完成状態に更新 (= 残り 5 領域 → 残り 3 領域)・WebSearch 16 件 + AFML Ch.2 (情報駆動 bars) / Ch.5 (Fractional Diff) / Ch.7 (Purged K-Fold + CPCV) / Ch.8 (MDI/MDA/SFI) / Ch.14 (DSR) + Bailey & Lopez de Prado 2014 (DSR / PBO) + MLfAT Ch.4 (Alpha Factor Research) + Hudson & Thames mlfinlab + arxiv 5 件 (microstructure 2602.00776 / 2506.05764 / Frontiers 2026 / MDPI 2026 / shap-select 2410.06815) 引用 |

---

## §12 関連 memory / 正本

- [feedback_priority_starting_line_only.md](../../../../../.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_priority_starting_line_only.md) (= 旧 Priority はスタートライン参照のみ・ベースにしない)
- [technical_analysis_knowledge_base.md](technical_analysis_knowledge_base.md) (= 既存・指標辞典 + 閾値理論 + MTF 理論)
- [feedback_trade_ml_knowledge_gap.md](../../../../../.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_trade_ml_knowledge_gap.md) (= CC のトレード ML 業界標準理解不足)
- cc_role §1.7 (= 手動 Priority の位置づけ・絶対遵守)
- 旧 Priority 実装: [strategies/cat_v9_decider.py](../../strategies/cat_v9_decider.py) L240-587 + [config/cat_params_v9.json](../../config/cat_params_v9.json)
