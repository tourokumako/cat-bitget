# cc_entry_logic_self_study.md — CC エントリーロジック自己学習資料 v1

作成: 2026-05-25 (CC)
位置付け: まこさん命令 (2026-05-25) 「指標、閾値、時間の使い方を勉強しなおして」を受けた CC の学習資料。
状態: v1 (WebSearch 8 件 + 旧 Priority 実装 verify による初版・追加学習で改訂継続)

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

### 15.2 残り 5 領域 (= 次セッション以降 WORKFLOW 改訂 35 active 優先 2 残り)

- **領域 3 (ML 特徴量設計)**: Fractional Differentiation (AFML Ch.5) / スケーリング / 特徴量選択 / 出来高系 / 板情報系
- **領域 4 (ML 評価方法)**: Walk-Forward / Purged K-Fold (AFML Ch.7) / CPCV / Embargo / DSR (AFML Ch.14) / 過学習検出
- **領域 5 (ML 組合せ手法)**: §13.5 で部分網羅・残り = 階層 / Cascade / 多段 stacking 詳細
- **領域 6 (リスク管理)**: §14.5 で Kelly 網羅・残り = Volatility targeting 詳細 / Stop-loss / Drawdown control の業界標準
- **領域 7 (監視・運用)**: Concept drift / Online learning / A/B testing — 業界標準は KL divergence / Wasserstein / Page-Hinkley test 等

### 15.3 次セッションの推奨着手順位

1. **領域 3-4 (特徴量 + 評価方法)** を先行: 工程 3 (Entry ML) の再設計に直結する基礎知識
2. **領域 5 (組合せ)** はその後: §13.5 で半分カバー済
3. **領域 6-7** は工程 4-7 の詳細詰めと並行可能

### 15.4 cat-bitget 設計判断の確定事項 (v2 学習成果から)

> ⚠️ 以下は **学習資料の調査ノート位置付け**。実際の設計確定は WORKFLOW 改訂 35 active の優先 3 (= 工程 2-7 詳細詰め) で別途実施 (cc_role §1.5 デザイン責任)。

- **工程 3 (Entry ML) ベース**: Triple Barrier multiclass (= 案 e 構造) + LightGBM / XGBoost stacking + Meta-Labeling 二段化 + regime 入力 + LONG/SHORT 分離 + MTF
- **工程 4 (Position Sizing)**: phase_flow_v4 v7 改善 4 動的合成方式 8 (= Half-Kelly + Vol target + cluster 強度別配分) を維持
- **工程 5 (Exit ML)**: PPO (= RL) 主軸 + XGBoost (= scale-out 確率) サブ
- **工程 1 (regime)**: 固定ルール (= ADX + DI 差) で MVP・後段で HMM ML 化検討

---

## §11 改訂履歴

| 版 | 日付 | 内容 |
|---|---|---|
| v1 | 2026-05-25 | 初版・WebSearch 8 件 + 旧 Priority 実装 verify による分析 |
| v2 | 2026-05-27 | §13 ML 学習方法 (6 章) + §14 ML 学習項目 (8 章) + §15 総合所見 追加・WebSearch 14 件 + AFML Ch.3/6 + Oxford-Man + Hudson & Thames mlfinlab + arxiv 8 件 引用 |

---

## §12 関連 memory / 正本

- [feedback_priority_starting_line_only.md](../../../../../.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_priority_starting_line_only.md) (= 旧 Priority はスタートライン参照のみ・ベースにしない)
- [technical_analysis_knowledge_base.md](technical_analysis_knowledge_base.md) (= 既存・指標辞典 + 閾値理論 + MTF 理論)
- [feedback_trade_ml_knowledge_gap.md](../../../../../.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_trade_ml_knowledge_gap.md) (= CC のトレード ML 業界標準理解不足)
- cc_role §1.7 (= 手動 Priority の位置づけ・絶対遵守)
- 旧 Priority 実装: [strategies/cat_v9_decider.py](../../strategies/cat_v9_decider.py) L240-587 + [config/cat_params_v9.json](../../config/cat_params_v9.json)
