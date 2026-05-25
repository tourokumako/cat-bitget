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

## §11 改訂履歴

| 版 | 日付 | 内容 |
|---|---|---|
| v1 | 2026-05-25 | 初版・WebSearch 8 件 + 旧 Priority 実装 verify による分析 |

---

## §12 関連 memory / 正本

- [feedback_priority_starting_line_only.md](../../../../../.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_priority_starting_line_only.md) (= 旧 Priority はスタートライン参照のみ・ベースにしない)
- [technical_analysis_knowledge_base.md](technical_analysis_knowledge_base.md) (= 既存・指標辞典 + 閾値理論 + MTF 理論)
- [feedback_trade_ml_knowledge_gap.md](../../../../../.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_trade_ml_knowledge_gap.md) (= CC のトレード ML 業界標準理解不足)
- cc_role §1.7 (= 手動 Priority の位置づけ・絶対遵守)
- 旧 Priority 実装: [strategies/cat_v9_decider.py](../../strategies/cat_v9_decider.py) L240-587 + [config/cat_params_v9.json](../../config/cat_params_v9.json)
