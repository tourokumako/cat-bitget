# 9種の指標を教科書で確かめた記録（ToDo 222番の材料）

- 作った日：2026-11-03
- 目的：engine_tuner を9種の指標で最後まで通すための材料（まこさんの決定 2026-11-02）。この文書は「どのページに何と書いてあるか」だけを書く。値は決めない。値を決めるのは 222番の設計書と監査。
- 先に通す条件：レンジの場面・スキャル・ショート。銘柄は BTC、売買の足は5分足。
- 照らした相手（refactor/e35-e36-split-strat-base の 1f6f5ff の時点）
  - `.claude/state/indicator_params_review.json`
  - `.claude/state/indicator_params_by_strategy.json`
  - `.claude/state/indicator_roles_thresholds.json`
  - `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json`

## 読み方

- 逐語は、ページの本文を取り、そのページの文を写したもの。訳は付けない。
- 確かめの強さは2つだけ。
  - **✅ ページの文で確かめた**＝本文を開いて、その文が在ることを見た。
  - **✗ 見つからなかった**＝開いたページに書いてない、またはページを開けなかった。
- 語の数を数えただけのものは、この文書に入れていない。
- 時間足は、ページの文に書いてある足を書く。書いてなければ「時間足は書いてない」と書く。
- 読んだ日は、どれも **2026-11-03**。

## 出どころの一覧

| 記号 | 出どころ | 質 | URL |
|---|---|---|---|
| SC-RSI | StockCharts ChartSchool「Relative Strength Index (RSI)」 | 定番の教育サイト | https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi |
| SC-ADX | StockCharts ChartSchool「Average Directional Index (ADX)」 | 定番の教育サイト | https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx |
| SC-BB | StockCharts ChartSchool「Bollinger Bands」 | 定番の教育サイト | https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/bollinger-bands |
| SC-BBW | StockCharts ChartSchool「Bollinger BandWidth」 | 定番の教育サイト | https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth |
| SC-PB | StockCharts ChartSchool「%B Indicator」 | 定番の教育サイト | https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator |
| SC-ATR | StockCharts ChartSchool「Average True Range (ATR)」 | 定番の教育サイト | https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-true-range-atr |
| SC-ATRP | StockCharts ChartSchool「Average True Range Percent (ATRP)」 | 定番の教育サイト | https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-true-range-percent-atrp |
| SC-ICHI | StockCharts ChartSchool「Ichimoku Cloud」 | 定番の教育サイト | https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/ichimoku-cloud |
| SC-PIV | StockCharts ChartSchool「Pivot Points」（式は同じページの Markdown 版 `pivot-points.md` で読んだ） | 定番の教育サイト | https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/pivot-points |
| SC-CBU | StockCharts ChartSchool「Candlestick Bullish Reversal Patterns」 | 定番の教育サイト | https://chartschool.stockcharts.com/table-of-contents/chart-analysis/candlestick-charts/candlestick-bullish-reversal-patterns |
| SC-CBE | StockCharts ChartSchool「Candlestick Bearish Reversal Patterns」 | 定番の教育サイト | https://chartschool.stockcharts.com/table-of-contents/chart-analysis/candlestick-charts/candlestick-bearish-reversal-patterns |
| SC-CDD | StockCharts ChartSchool「Candlestick Pattern Dictionary」 | 定番の教育サイト | https://chartschool.stockcharts.com/table-of-contents/chart-analysis/candlestick-charts/candlestick-pattern-dictionary |
| TV-RSI | TradingView ヘルプ「Relative Strength Index (RSI)」 | 定番の教育サイト | https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/ |
| TV-DMI | TradingView ヘルプ「Directional Movement (DMI)」 | 定番の教育サイト | https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ |
| TV-ADX | TradingView ヘルプ「Average Directional Index (ADX)」 | 定番の教育サイト | https://www.tradingview.com/support/solutions/43000589099-average-directional-index-adx/ |
| TV-ATR | TradingView ヘルプ「Average True Range (ATR)」 | 定番の教育サイト | https://www.tradingview.com/support/solutions/43000501823-average-true-range-atr/ |
| TV-BBW | TradingView ヘルプ「Bollinger BandWidth (BBW)」 | 定番の教育サイト | https://www.tradingview.com/support/solutions/43000501972-bollinger-bandwidth-bbw/ |
| TV-PB | TradingView ヘルプ「Bollinger Bands %b」 | 定番の教育サイト | https://www.tradingview.com/support/solutions/43000501971-bollinger-bands-b-b/ |
| TV-ICHI | TradingView ヘルプ「Ichimoku Cloud」 | 定番の教育サイト | https://www.tradingview.com/support/solutions/43000589152-ichimoku-cloud/ |
| TV-PIV | TradingView ヘルプ「Pivot Points Standard」 | 定番の教育サイト | https://www.tradingview.com/support/solutions/43000521824-pivot-points-standard/ |
| BB-R | John Bollinger「Bollinger Band Rules」 | 開発者の原典 | https://www.bollingerbands.com/bollinger-band-rules |
| BB-E | John Bollinger「Bollinger Bands」（What are Bollinger Bands?） | 開発者の原典 | https://www.bollingerbands.com/bollinger-bands |
| PS-BU | Thomas Bulkowski「Bullish Engulfing」 | 定番の教育サイト（Encyclopedia of Candlestick Charts の著者のサイト） | https://thepatternsite.com/BullEngulfing.html |
| PS-BE | Thomas Bulkowski「Bearish Engulfing」 | 同上 | https://thepatternsite.com/BearEngulfing.html |
| TALIB | TA-Lib の C のソース `ta_CDLENGULFING.c`（main ブランチ） | ライブラリの原典 | https://raw.githubusercontent.com/TA-Lib/ta-lib/main/src/ta_func/ta_CDLENGULFING.c |
| RL-ADX | RegimeLab「Best ADX settings」（2026-07-21 の日付あり・暗号資産向けのサイト） | ブログ | https://regimelab.io/blog/best-adx-settings |
| TRT-ADX | The Right Trader「Best ADX settings」（Updated October 13, 2026） | ブログ | https://therighttrader.com/learn/indicator-strategies/best-adx-settings |
| TRT-RSI | The Right Trader「Best RSI settings」（Updated September 26, 2026） | ブログ | https://therighttrader.com/learn/indicator-strategies/best-rsi-settings |
| TRT-BB | The Right Trader「Best Bollinger Bands settings」（Updated October 13, 2026） | ブログ | https://therighttrader.com/learn/indicator-strategies/best-bollinger-bands-settings |
| TRT-ATR | The Right Trader「Best ATR settings」（Updated October 13, 2026） | ブログ | https://therighttrader.com/learn/indicator-strategies/best-atr-settings |
| BLX | Bullynx「Best RSI Settings: 5-Minute, Day and Swing Charts」（Last updated October 15, 2026） | 証券会社・ブログ | https://bullynx.com/blog/best-rsi-settings |
| EPB | eplanetbrokers「Mastering the Best RSI Settings for 5-Minute Charts」（Updated at September 10, 2026） | 証券会社・ブログ | https://eplanetbrokers.com/training/best-rsi-settings-for-5-minute-charts/ |
| MC2 | MC² Finance「Best RSI for Scalping (2025 Guide)」 | ブログ | https://www.mc2.fi/blog/best-rsi-for-scalping |
| WT | WunderTrading「RSI vs Stochastic RSI」（暗号資産の記事） | ブログ | https://wundertrading.com/journal/en/rsi-vs-stochastic-rsi-crypto-trading |
| LF-ICHI | LiteFinance「Ichimoku Cloud Indicator in Forex Explained」（25 Sep. 2026 の日付あり） | 証券会社の解説 | https://www.litefinance.org/blog/for-beginners/best-technical-indicators/ichimoku-cloud-indicator-in-forex-explained/ |
| RS-ICHI | forex.in.rs「Ichimoku settings 7-22-44」（Updated September 2026） | ブログ | https://www.forex.in.rs/ichimoku-settings-7-22-44/ |
| OX | OptionX「Best Bollinger Bands Scalping Strategy for Indian F&O」 | ブログ | https://optionx.trade/blogs/bollinger-bands-scalping-strategy-indian-fno |

- 開発者の原典を直に読めたのは、Bollinger（BB-R・BB-E）と TA-Lib のソースだけ。Wilder（RSI・ADX・DMI・ATR）と細田悟一（一目均衡表）の本は、Web に本文が無いので読んでいない。SC と TV が「Wilder は〜と書いた」と引くところは、引いたページの文として書く。
- 1つのサイトにしか無い値には「（1サイトだけ）」と書いた。

---

## 1. RSI

### Q1 何を見ているか

答え：**勢い**（モメンタム）。0〜100 の中で **行き過ぎ** を見る使い方も書いてある。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| "The RSI, a momentum oscillator developed by J. Welles Wilder, measures the speed and change of price movements." | SC-RSI | 時間足は書いてない | ✅ |
| "When the RSI is above 70, it generally indicates overbought conditions; when the RSI is below 30, it indicates oversold conditions." | SC-RSI | 時間足は書いてない | ✅ |
| "The Relative Strength Index (RSI) is a well versed momentum based oscillator which is used to measure the speed (velocity) as well as the change (magnitude) of directional price movements." | TV-RSI | 時間足は書いてない | ✅ |

### Q2 レンジとショートでの使い方

答え：レンジでは、70／30 の行き過ぎの読みがいちばん効く、と書いてある。ショート側は「上側（70 超え）」を使う、と書いてある。下げ相場では RSI が 10〜60 に収まり、50〜60 が抵抗になる、とも書いてある。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| "Like many momentum oscillators, overbought and oversold readings for RSI work best when prices move sideways within a range ." | SC-RSI | 日足の例（"While many of the examples in this article use daily charts"） | ✅ |
| "The chart below shows MEMC Electronics (WFR) trading between 13.5 and 21 from April to September 2009. The stock peaked soon after RSI reached 70 and bottomed soon after the stock reached 30." | SC-RSI | 日足 | ✅ |
| （ショート）"This scan reveals stocks that are in a downtrend with overbought RSI turning down. First, stocks must be below their 200-day moving average to be in an overall downtrend. Second, RSI must cross above 70 to become overbought." | SC-RSI | 日足（200-day） | ✅ |
| （ショート）"A bearish failure swing forms when RSI moves above 70, pulls back, bounces, fails to exceed 70, and then breaks its prior low." | SC-RSI | 時間足は書いてない | ✅ |
| （ショート）"On the flip side, RSI tends to fluctuate between 10 and 60 in a bear market (downtrend) with the 50-60 zone acting as resistance." | SC-RSI | 日足（14-day RSI の例） | ✅ |
| （ショート）"A short candidate is RSI crossing back below 70 after a print above 70. The first poke of 30 on a 5 minute chart is noise." | TRT-RSI（1サイトだけ） | 5分足 | ✅ |
| （レンジ）"In a range-bound market , tighter levels like 60/40 can catch more of the smaller swings." | BLX（1サイトだけ） | 時間足は書いてない | ✅ |
| （レンジ・5分足）"Default 14 70/30 70 minutes Ranging sessions only; trends pin it at the band" | BLX（表の行） | 5分足 | ✅ |
| （レンジ）"In ranging markets: Tighten RSI to 7 periods, use 75/25 levels" | WT（1サイトだけ・暗号資産の記事） | 時間足は書いてない（デイトレの節） | ✅ |

### Q3 パラメータ

答え：既定は **14**。短い足では 7〜9 がよく使われる、と複数のページが書く。5分足のスキャルは 5〜7、1分足は 2〜3 と書くページもある。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 既定 14 | "This RSI calculation is based on 14 periods, the default Wilder suggested in his book." | SC-RSI | 時間足は書いてない | ✅ |
| 既定 14 | "The number of bars to be used in calculating the RSI. 14 bars is the default." | TV-RSI | 時間足は書いてない | ✅ |
| 下げると敏感 | "The default look-back period for RSI is 14, but you can lower it to increase sensitivity or raise it to decrease sensitivity. A 10-day RSI is more likely to reach overbought or oversold levels than a 20-day RSI." | SC-RSI | 日足 | ✅ |
| 2（短期の売買） | "Short-term traders sometimes use 2-period RSI to look for overbought readings above 80 and oversold readings below 20." | SC-RSI | 時間足は書いてない | ✅ |
| 時間足を選ばない | "the RSI can be added to many timeframes - daily, weekly, hourly, and minute charts." | SC-RSI | 日足・週足・時間足・分足 | ✅ |
| 7〜9（デイトレ）・21（スイング） | "Day traders commonly shorten the period to 7 to 9 on intraday charts, swing traders commonly keep 14 or stretch it to 21 on the daily" | BLX | 日中の足／日足 | ✅ |
| 5分足 9（または 14） | "The best RSI settings for a 5-minute chart are a 9-period RSI with bands at 75/25 for a faster read, or the 14-period default with bands widened to 80/20 if you want fewer signals." | BLX | 5分足 | ✅ |
| 5分足のスキャル 7〜9 | "Faster 7 to 9 75/25 or 80/20 35 to 45 minutes Scalps and quick mean-reversion fades" | BLX（表の行） | 5分足 | ✅ |
| デイトレ 7 か 9 | "Day traders often use 7 or 9 on 5 minute and 15 minute charts and still wait for a cross back through 30 or 70." | TRT-RSI | 5分足・15分足 | ✅ |
| 5分足のスキャル 7 | "For 5-minute scalping, the 7-period RSI is usually the best choice." | MC2 | 5分足 | ✅ |
| 1分足 2〜3 | "When trading on a 1-minute chart, the best RSI setting is typically RSI 2 or 3." | MC2（1サイトだけ） | 1分足 | ✅ |
| スキャル 5〜7・デイトレ 9〜10 | "Scalpers should use RSI(5-7) with 80/20 levels, while day traders benefit from RSI(9-10) with 75/25 levels." | EPB | 5分足のページ | ✅ |
| デイトレ 9（15分足） | "a good place to start is a 9-period RSI on 15-minute charts." | WT | 15分足 | ✅ |
| 1時間足 14 | "On the 1-hour, the classic 14-period works well with standard 70/30 levels." | WT | 1時間足 | ✅ |
| 5分足のスキャル 5 | "Use a 5-period RSI with 80/20 thresholds to match the faster pace." | WT（1サイトだけ） | 5分足 | ✅ |
| 範囲（数の範囲） | 「2〜21」のような範囲を1つの文で書いたページ | — | — | ✗ 見つからなかった（いちばん短い 2 は SC-RSI と MC2、いちばん長い 21 は BLX のスイング） |

### Q4 閾値

答え：形は **値**。代表は **70／30**（Wilder）。80／20 に広げる使い方、50 を中心線とする読み、トレンドで帯が動く読み（Brown）も書いてある。5分足では 75／25 と 80／20 が書いてある。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 70／30 | "Wilder considered RSI overbought above 70 and oversold below 30." | SC-RSI | 日足の例 | ✅ |
| 70／30 | "According to Wilder, any number above 70 should be considered overbought and any number below 30 should be considered oversold." | TV-RSI | 時間足は書いてない | ✅ |
| 50（向きなし） | "An RSI between 30 and 70 was to be considered neutral and an RSI around 50 signified “no trend”." | TV-RSI | 時間足は書いてない | ✅ |
| 80／20 | "Raising the overbought threshold to 80 or lowering the oversold threshold to 20 could reduce the number of overbought/oversold readings." | SC-RSI | 時間足は書いてない | ✅ |
| 80／20 | "For example, someone might consider any number above 80 as overbought and anything below 20 as oversold. This is entirely at the trader’s discretion." | TV-RSI | 時間足は書いてない | ✅ |
| 上げ相場 40〜90・下げ相場 10〜60（前提つき） | "RSI tends to fluctuate between 40 and 90 in a bull market (uptrend) with the 40–50 zones acting as support." / "RSI tends to fluctuate between 10 and 60 in a bear market (downtrend) with the 50-60 zone acting as resistance." | SC-RSI（Brown の本として） | 週足・日足の例 | ✅ |
| 上げ相場 40〜80・下げ相場 20〜60（前提つき） | "Constance Brown discussed a range shift in Technical Analysis for the Trading Professional (1999): bull markets often hold RSI between 40 and 80, and bear markets between 20 and 60." | TRT-RSI | 時間足は書いてない | ✅（SC-RSI と値が違う。下の「違う所」を見る） |
| 30〜50・50〜70（反転の形） | "This lower low is not at oversold levels but is usually between 30 and 50." / "the higher high is usually just below overbought levels in the 50-70 area." | SC-RSI（Cardwell の読み） | 時間足は書いてない | ✅ |
| 5分足 75／25 か 80／20 | 上の Q3 の BLX の行と同じ文 | BLX | 5分足 | ✅ |
| 5分足 75／25 | "Using 75 for overbought and 25 for oversold conditions filters out market noise while maintaining sensitivity to genuine momentum changes." | EPB | 5分足 | ✅ |
| 5分足 30／70 から始め、20／80 へ | "Keep 30 and 70 at first. If 7 tags 70 on every small push, you can move the lines to 20 and 80." | TRT-RSI | 5分足・15分足 | ✅ |
| 閾値の範囲 | 閾値の範囲を1つの文で書いたページ | — | — | ✗ 見つからなかった（書いてある値は 60/40〜80/20） |

---

## 2. ADX

### Q1 何を見ているか

答え：**強さ**（トレンドの強さ）。向きは見ない。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| "it measures the strength of the trend (regardless of direction) over time." | SC-ADX | 時間足は書いてない | ✅ |
| "The Average Directional Index (ADX) is used to measure the strength or weakness of a trend, not the actual direction." | SC-ADX | 時間足は書いてない | ✅ |
| "ADX's purposes is to define whether or not there is a trend present. It does not take direction into account at all." | TV-DMI | 時間足は書いてない | ✅ |

### Q2 レンジとショートでの使い方

答え：ADX はトレンドが在るか無いかを分け、トレンド向けの手法と、トレンドでない手法のどちらを使うかを決める、と書いてある。ADX が 20 より下なら「トレンドが無い」。ショートは ADX でなく −DI と +DI の交差で決め、ADX は「トレンドが在る」という前提に使う。ADX の値にショート用の側は無い。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| "At its most basic, the Average Directional Index (ADX) can be used to determine if a security is trending or not. This determination helps traders choose between a trend-following system or a non-trend-following system." | SC-ADX | 時間足は書いてない | ✅ |
| （ショート）"A sell signal triggers when -DI crosses above +DI. The high on the day of the sell signal becomes the initial stop-loss." | SC-ADX | 日足（"the day of the sell signal"） | ✅ |
| （ショート）"ADX must be over 25 (strong trend. The value is determined by trader) " / "The -DI crosses above the +DI." | TV-DMI | 時間足は書いてない | ✅ |
| （ADX は下げでも高い）"ADX at 40 with minus DI on top is a strong downtrend." | TRT-ADX（1サイトだけ） | 時間足は書いてない | ✅ |
| ショートで ADX の値のどちら側を使うか | ADX の値をショート用に上と下で分けて書いたページ | — | ✗ 見つからなかった（どのページも、ADX は向きを持たないと書く） |

### Q3 パラメータ

答え：既定は **14**（Wilder）。短い足では 7〜10 にする、と書くページがある。**スキャルをデイトレより長くする、と書いたページは見つからなかった。**

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 既定 14 | "The calculation example below is based on a 14-period indicator setting, as recommended by Wilder." | SC-ADX | 時間足は書いてない | ✅ |
| 既定 14 | "The time period to be used in calculating the ADX which has a smoothing component (14 is the Default)." | TV-DMI | 時間足は書いてない | ✅ |
| Wilder の前提 | "Although Wilder designed his Directional Movement System with commodities and daily prices in mind, these indicators can also be applied to stocks." | SC-ADX | 日足 | ✅ |
| 範囲 7〜21 | "The practical range for most systematic traders is 7 to 21, with 14 as the default starting point." | RL-ADX（1サイトだけ） | 時間足は書いてない | ✅ |
| 7 より下は乱れる | "Below period 7, ADX readings typically become too erratic to serve as a reliable regime classifier." | RL-ADX | 時間足は書いてない | ✅ |
| 15分足 7〜14 | "15-minute charts: 7 to 14. At 14 periods, 15-minute ADX covers 3.5 hours of price data. Shorter periods (7 to 10) are common at this resolution because the full-cycle logic breaks down for intraday timeframes." | RL-ADX | 15分足 | ✅ |
| 1時間足 10〜14 | "1-hour charts: 10 to 14." | RL-ADX | 1時間足 | ✅ |
| デイトレ 7〜14 | "For day trading on 15-minute to 1-hour charts, periods of 7 to 14 are most common. Shorter periods (7 to 10) react faster to intraday trend development. Longer periods (12 to 14) produce smoother signals with less noise." | RL-ADX | 15分足〜1時間足 | ✅ |
| デイトレ 14・5分足 7 か 10 | "Day traders keep 14 on a 15 minute or 1 hour chart. Period 7 or 10 on a 5 minute chart reacts faster and spikes more." | TRT-ADX | 15分足・1時間足／5分足 | ✅ |
| 5分足で 14 は 70分 | "On a 5 minute chart, period 14 is 70 minutes. That can work as a filter. If you need strength to show up inside a half hour, try period 10 or 7 and keep the 20 and 25 marks." | TRT-ADX | 5分足 | ✅ |
| 1分足で 14 は遅い | "14 Daily, 15 minute, 1 hour Wilder's default Late on a 1 minute chart" | TRT-ADX（表の行） | 日足・15分足・1時間足／1分足 | ✅ |
| スキャル（5分足以下）の値 | 「スキャル」と名指しした ADX の期間 | — | — | ✗ 見つからなかった（5分足の値は TRT-ADX の 7・10・14 だけ） |

### Q4 閾値

答え：形は **値**。**25 より上で強いトレンド、20 より下でトレンドなし**（Wilder）。20〜25 は灰色。20 を使う人も多い。短い足や暗号資産では 25 を確かめ直すように書くページがある。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 25／20 | "Wilder suggests that a strong trend is present when ADX is above 25 and no trend is present when ADX is below 20. There appears to be a gray zone between 20 and 25." | SC-ADX | 時間足は書いてない | ✅ |
| 20 | "Many technical analysts use 20 as the key level for ADX." | SC-ADX | 時間足は書いてない | ✅ |
| 25／20 | "Wilder believed that a DMI reading above 25 indicated a strong trend, while a reading below 20 indicated a weak or non-existent trend." | TV-DMI | 時間足は書いてない | ✅ |
| 銘柄で変わる | "What is truly a strong trend or a weak trend depends on the financial instrument being examined." | TV-DMI | 時間足は書いてない | ✅ |
| 15分足では 25 を直す | "The 25 threshold may also need recalibration: brief intraday directional moves can produce ADX readings above 25 that do not represent genuine trend conditions in the way a daily chart reading does." | RL-ADX（1サイトだけ） | 15分足 | ✅ |
| 25 は日足から | "Wilder’s 25 level was derived from empirical observation of daily commodity charts using a 14-period calculation." | RL-ADX | 日足 | ✅ |
| 5分足でも 20 と 25 | 上の Q3 の TRT-ADX の文（"keep the 20 and 25 marks"） | TRT-ADX | 5分足 | ✅ |
| 閾値の範囲 | 閾値の範囲を書いたページ | — | — | ✗ 見つからなかった（書いてある値は 15〜30。TRT-ADX は 15 と 30 を「動かすときの例」として書く） |

---

## 3. DI差（+DI と −DI）

### Q1 何を見ているか

答え：**向き**（トレンドの向き）。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| "The Plus Directional Indicator (+DI) and Minus Directional Indicator (-DI) ... are derived from smoothed averages of these differences and measure trend direction over time. When +DI is above -DI, the trend is up; when +DI is below -DI, the trend is down." | SC-ADX（途中の "shown in green and red in the chart above," を「...」にした） | 時間足は書いてない | ✅ |
| "The other two indicators (+DI and -DI) are used to compliment the ADX. They serve the purpose of determining trend direction." | TV-DMI | 時間足は書いてない | ✅ |

### Q2 レンジとショートでの使い方

答え：ショートは **−DI が +DI を上に抜けたとき**（DI差がマイナスへ変わるとき）。ADX が 25（または 20）より上という前提つき。レンジ（もみ合い）では交差のだましが多い、と書いてある。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| （ショート）"In general, the bulls have the edge when +DI is greater than -DI, while the bears have the edge when -DI is greater." | SC-ADX | 時間足は書いてない | ✅ |
| （ショート）"Overall Downtrend with -DI Crossing above +DI ... A downtrend is present when trading below the 50-day SMA. A sell signal is possible when ADX is above 20. This signal materializes when -DI moves above +DI." | SC-ADX（題と本文の間の1文を「...」にした） | 日足（50-day SMA） | ✅ |
| （ショート）"When -DI is above +DI, then a Bearish Market is at hand." | TV-DMI | 時間足は書いてない | ✅ |
| （レンジ）"For example, the first group of whipsaws in September 2009 occurred during a consolidation." | SC-ADX | 日足の例 | ✅ |
| （レンジ）"These moments in question are known as “false signals” and are most common when ADX is calculated below 25." | TV-ADX | 時間足は書いてない | ✅ |

### Q3 パラメータ

答え：既定は **14**。DI の期間だけを、スキャルやデイトレ向けに書いたページは見つからなかった。DI の期間と ADX の平滑化の期間を別にすると Wilder の道具ではなくなる、と書くページがある。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 既定 14 | "The time period to be used in calculating the DI (14 is Default)." | TV-DMI | 時間足は書いてない | ✅ |
| 既定 14 | "DI length 14 Wilder smooth of plus DM, minus DM, and true range" | TRT-ADX（表の行） | 時間足は書いてない | ✅ |
| 別にしない | "If you set DI length to 10 and ADX smoothing to 20, you no longer have Wilder's tool and you cannot tell which length mattered." | TRT-ADX（1サイトだけ） | 時間足は書いてない | ✅ |
| スキャル・デイトレ・範囲 | DI の期間だけの値 | — | — | ✗ 見つからなかった |

### Q4 閾値

答え：DI差そのものの数の閾値は **持たない**。形は「**交差**（+DI と −DI の上下＝DI差の 0）」で、「ADX が 25（または 20）より上」という**前提つき**。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 交差＋前提 | "The first requirement is for ADX to be trading above 25. This ensures that prices are trending. Many traders, however, use 20 as the key level. A buy signal occurs when +DI crosses above -DI." | SC-ADX | 時間足は書いてない | ✅ |
| 交差＋前提 | "A general interpretation would be that during a strong trend (ADX above 25 but dependent on the analyst's interpretation), when the +DI is above the -DI, then a Bullish Market is defined." | TV-DMI | 時間足は書いてない | ✅ |
| DI差の大きさの閾値 | DI差の大きさ（例＝差が 10 より大きい）を書いたページ | — | — | ✗ 見つからなかった |

---

## 4. BB幅（Bollinger BandWidth）

### Q1 何を見ているか

答え：**値動きの幅**（ボラティリティ）。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| "Because Bollinger Bands are based on the standard deviation, falling BandWidth reflects decreasing volatility and rising BandWidth reflects increasing volatility." | SC-BBW | 時間足は書いてない | ✅ |
| "BandWidth tells us how wide the Bollinger Bands are. The raw width is normalized using the middle band. Using the default parameters BandWidth is four times the coefficient of variation." | BB-R（ルール18） | 時間足は書いてない | ✅ |

### Q2 レンジとショートでの使い方

答え：レンジ（値の狭い横ばい）では幅が狭くなる（スクイーズ）。スクイーズの後、**下のバンドを割ったらショート側の合図**。幅だけでは向きは決まらない。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| （レンジ）"The bands narrow as price flattens or moves within a relatively narrow range." | SC-BBW | 時間足は書いてない | ✅ |
| （ショート）"A new decline starts with a Squeeze and subsequent break below the lower band." | SC-BBW | 時間足は書いてない | ✅ |
| （向きは別）"The direction depends on the subsequent band break." | SC-BBW | 時間足は書いてない | ✅ |
| （レンジ→ショート）"The chart below shows Honeywell (HON) with an extended trading range in the $50–$55 area. ... HON clearly broke below the lower band to trigger a bearish signal in June 2007." | SC-BBW（間の1文を「...」にした） | 日足の例 | ✅ |
| （ショート）"Price falls below the Lower Band which starts a new downward trend. Volatility also increases." | TV-BBW | 時間足は書いてない | ✅ |

### Q3 パラメータ

答え：既定は **(20, 2)**。期間を変えるときは倍率も変える（10 なら 1.9、50 なら 2.1）と、開発者が書いている。5分足で (10, 1.9) と書くページ、スキャルで (10〜14, 1.5〜2) と書くページがある。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 既定 (20, 2) | "The default parameters of 20 periods for the moving average and standard deviation calculations, and two standard deviations for the width of the bands are just that, defaults. The actual parameters needed for any given market/task may be different." | BB-R（ルール9） | 時間足は書いてない | ✅ |
| 既定 (20, 2) | "The default parameters (20,2) are based on the default parameters for Bollinger Bands." | SC-BBW | 時間足は書いてない | ✅ |
| 既定 20・2 | "20 days is the default." / "The number of Standard Deviations away from the SMA that the Upper and Lower Bands should be. 2 is the default." | TV-BBW | 日足（"20 days"） | ✅ |
| 組 (10, 1.9)〜(50, 2.1) | "If the average is lengthened the number of standard deviations needs to be increased; from 2 at 20 periods, to 2.1 at 50 periods. Likewise, if the average is shortened the number of standard deviations should be reduced; from 2 at 20 periods, to 1.9 at 10 periods." | BB-R（ルール11） | 時間足は書いてない | ✅ |
| 同じ組 | "Bollinger suggests increasing the standard deviation multiplier to 2.1 for a 50-period SMA and decreasing the standard deviation multiplier to 1.9 for a 10-period SMA." | SC-BB | 時間足は書いてない | ✅ |
| 5分足にも使える | "Bollinger Bands can be used on bars of any length, 5 minutes, one hour, daily, weekly, etc." | BB-R（ルール21） | 5分足・1時間足・日足・週足 | ✅ |
| 5分足 (10, 1.9) | "Day traders who leave 20 and 2 often put them on a 15-minute chart, or use 10 and 1.9 on a 5-minute chart." | TRT-BB | 15分足／5分足 | ✅ |
| 5分足で (20, 2) は遅い | "20 and 2 Daily default, or 15-minute Bollinger's reference Late on a 5-minute scalp" | TRT-BB（表の行） | 日足・15分足／5分足 | ✅ |
| スキャル (10〜14, 1.5〜2) | "Period for SMA: Reduce to 10-14 periods." / "Standard Deviations: Use 1.5 to 2." | OX（1サイトだけ・インドの先物とオプション） | 1分足・5分足 | ✅ |
| スイング 2.5 | "Swing traders who want fewer outside closes can keep length 20 and raise the multiplier to 2.5." | TRT-BB（1サイトだけ） | 時間足は書いてない | ✅ |

### Q4 閾値

答え：決まった数の閾値は **持たない**。形は「**その銘柄の過去の幅と比べる**」（分位に近い形・前提つき）。過去を見る長さとして 8〜12か月の例がある。例として出てくる 10・8・9% は、どれも1つの銘柄の例。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 過去と比べる | "Narrow BandWidth is relative. BandWidth values should be gauged relative to prior BandWidth values over a period of time." | SC-BBW | 時間足は書いてない | ✅ |
| 8〜12か月の範囲の下端 | "For example, an eight- to 12-month chart will show BandWidth highs and lows over a significant timeframe. BandWidth is considered narrow as it approaches the lows of this range and wide as it approaches the high end." | SC-BBW | 日足（8〜12か月の図） | ✅ |
| 銘柄ごとに違う（例 9%） | "BBW drops. (In the example below, the threshold is 9% however this changes from security to security and timeframe to timeframe)." | TV-BBW | 時間足で変わると書く | ✅ |
| 例 10・8 | "BandWidth dipped below 10 to put the Squeeze play on in mid-June." / "This line marks 8, which is deemed relatively low based on the historical range." | SC-BBW（ALK と ARO の例） | 日足の例 | ✅ |
| 回数（5日以上） | "This scan reveals stocks whose Bollinger Bands just expanded rapidly after being contracted for 5 or more days." | SC-BBW（検索の例） | 日足（"days"） | ✅ |
| 短い足の値 | 5分足や暗号資産の BB幅の閾値 | — | — | ✗ 見つからなかった |

---

## 5. BB%b（Bollinger %B）

### Q1 何を見ているか

答え：**位置**（バンドの中のどこに値段が在るか）。行き過ぎとトレンドの強さを見る使い方も書いてある。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| "%b tells us where we are in relation to the Bollinger Bands." | BB-R（ルール15） | 時間足は書いてない | ✅ |
| "The %B Indicator measures a security's price in relation to the upper and lower Bollinger Bands. You can use it to identify overbought or oversold conditions and gauge trend strength." | SC-PB | 時間足は書いてない | ✅ |

### Q2 レンジとショートでの使い方

答え：ショートは「**中くらいの長さのトレンドが下向きのときに、短い買われ過ぎ（%B が 1 に近い・1 を超える）を探す**」と書いてある。下げの判定は %B が 0.20 より下で MFI(10) が 20 より下。**レンジでどう使うかは書いてない。**

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| （ショート）"As with most momentum oscillators, it is best to look for short-term oversold situations when the medium-term trend is up and short-term overbought situations when the medium-term trend is down." | SC-PB | 時間足は書いてない | ✅ |
| （ショート）"In a strong downtrend, %B can be considered overbought when it approaches or exceeds 1." | SC-PB（よくある問い） | 時間足は書いてない | ✅ |
| （ショート）"Downtrends are identified when %B is below 0.20 and MFI(10) is below 20." | SC-PB（Bollinger の手法として） | 時間足は書いてない | ✅ |
| （注意）"A tag of the upper Bollinger Band is NOT in-and-of-itself a sell signal." | BB-R（ルール6） | 時間足は書いてない | ✅ |
| （注意）"Closes outside the Bollinger Bands are initially continuation signals, not reversal signals." | BB-R（ルール8） | 時間足は書いてない | ✅ |
| （レンジ） | %B をレンジの相場でどう使うか | — | ✗ 見つからなかった（SC-PB・TV-PB・BB-R のどれにも書いてない。TV-PB は "It is typically best to look for trading signals generated by the %b during strong or clearly defined uptrends or downtrends." と書く） |

### Q3 パラメータ

答え：BB幅と同じ。既定 **(20, 2)**、組は (10, 1.9)〜(50, 2.1)。短い足の値は、BB幅の Q3 と同じページの値（%B だけを名指ししたものは無い）。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 既定 (20, 2) | "The default setting for %B is based on the default setting for Bollinger Bands (20,2)." | SC-PB | 時間足は書いてない | ✅ |
| 既定 20・2 | "20 days is the default." / "2 is the default." | TV-PB | 日足（"20 days"） | ✅ |
| 組 | BB幅の Q3 の BB-R ルール11 と同じ文 | BB-R | 時間足は書いてない | ✅ |
| %B だけの短い足の値 | %B を名指しした 5分足・スキャルの値 | — | ✗ 見つからなかった |

### Q4 閾値

答え：形は **値**。**1・0・0.5**（バンドの上・下・真ん中）と、**0.80／0.20**（バンドに近い）。Bollinger の手法では 0.80／0.20 を MFI(10) の 80／20 と組む（前提つき）。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 1・0・0.5 | "%B equals 1 when price is at the upper band" / "%B equals 0 when price is at the lower band" / "%B is between 0 and .50 when price is between the lower and middle band (20-day SMA)" | SC-PB | 日足（20-day SMA） | ✅ |
| 0.80／0.20 | "Generally speaking .80 and .20 are also relevant levels." | TV-PB | 時間足は書いてない | ✅ |
| 0.80／0.20 | "Readings above .80 indicate that price is near the upper band. Readings below .20 indicate that price is near the lower band." | SC-PB | 時間足は書いてない | ✅ |
| 0.80＋MFI 80（前提つき） | "An uptrend begins when %B is above .80 and MFI(10) is above 80." | SC-PB（Bollinger の手法として） | 時間足は書いてない | ✅ |
| 固定の閾値を無くす使い方 | "Indicators can be normalized with %b, eliminating fixed thresholds in the process. To do this plot 50-period or longer Bollinger Bands on an indicator and then calculate %b of the indicator." | BB-R（ルール17） | 時間足は書いてない | ✅ |
| 短い足の値 | 5分足や暗号資産の %B の閾値 | — | ✗ 見つからなかった |

---

## 6. ATR%（ATR と、ATR を価格で割った形）

### Q1 何を見ているか

答え：**値動きの幅**（ボラティリティ）。向きは見ない。% にすると、値段の違う銘柄どうしを比べられる。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| "It is important to remember that ATR doesn't indicate price direction, just volatility." | SC-ATR | 時間足は書いてない | ✅ |
| "The Average True Range Percent (ATRP) is an indicator that measures the volatility of a security." | SC-ATRP | 時間足は書いてない | ✅ |
| "The ATRP is calculated by dividing the ATR value by the closing price and multiplying the result by 100." | SC-ATRP | 時間足は書いてない | ✅ |
| "ATRP seeks to overcome this limitation by expressing the ATR value as a percentage of the price." | SC-ATRP | 時間足は書いてない | ✅ |

### Q2 レンジとショートでの使い方

答え：レンジでは **低い**、と書いてある。ショートでは「**支えを割るときに ATR が増えていれば、売りの圧力が強い**」と書いてある。ATR% の値に、ショート用の側は無い。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| （レンジ）"The ATRP is lower when the security is in a trading range, and moves higher during dramatic price changes in either direction." | SC-ATRP | 時間足は書いてない | ✅ |
| （レンジ）"On the other hand, during periods of sustained sideways movement, volatility is frequently low. This could assist in the discovery of trading ranges." | TV-ATR | 時間足は書いてない | ✅ |
| （ショート）"A bearish support break with increased ATR would show strong selling pressure and reinforce the support break." | SC-ATR | 時間足は書いてない | ✅ |

### Q3 パラメータ

答え：既定は **14**。5分足でも 14 か、速くしたいなら 10。7 は1本の大きな足で跳ねる、と書くページがある。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 既定 14 | "Typically, the Average True Range (ATR) is based on 14 periods and can be calculated on an intraday, daily, weekly or monthly basis." | SC-ATR | 日中・日足・週足・月足 | ✅ |
| 既定 14（ATRP） | "By default, the indicator is calculated using 14 periods." | SC-ATRP | 時間足は書いてない | ✅ |
| 既定 14 | "The time period to be used in calculating the Average True Range. 14 days is the default." | TV-ATR | 日足（"14 days"） | ✅ |
| 日足がふつう | "ATR can be used with varying periods (daily, weekly, intraday etc.) however daily is typically the period used." | TV-ATR | 日足 | ✅ |
| 5分足・15分足 14、または 10 | "Day traders can use 14 on a 5 minute or 15 minute chart. Use 10 only when 14 feels like yesterday's range." | TRT-ATR（1サイトだけ） | 5分足・15分足 | ✅ |
| 7 は跳ねる | "If one news bar blows the distance out and you need it to fade faster, try period 10 and keep the multiple unchanged. Period 7 reacts even faster and will jump on a single spike." | TRT-ATR | 5分足・15分足 | ✅ |
| 範囲 5〜21 | 資料の表の出どころ（marketclutch.com） | — | ✗ 見つからなかった（URL を開くと 404。確かめ直せなかった） |

### Q4 閾値

答え：ATR% の閾値は **持たない**（どのページも、決まった数の閾値を書いていない）。例として「去年の平均の ATRP が 4% より大きい株を外す」という検索の例がある（日足の株）。ATR は止めの幅に倍率（1.5 か 2）で使う、と書くページがある。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 例 4%（検索の例） | "The final scan clause excludes high-volatility stocks (those with average ATRP of more than 4% over the last year) from the results." | SC-ATRP | 日足（"over the last year"）・株 | ✅ |
| 倍率 1.5 か 2（止めの幅） | "A common same day distance is 1.5 or 2 times the 5 minute ATR, placed beyond the swing that got you in." | TRT-ATR（1サイトだけ） | 5分足 | ✅ |
| 値の閾値 | ATR% の決まった数の閾値 | — | ✗ 見つからなかった |

---

## 7. 基準線（一目均衡表の基準線）

### Q1 何を見ているか

答え：ページで違う。SC-ICHI は、値段と基準線の交差を **勢い**（momentum）の合図と書く。LiteFinance は、基準線を中くらいの長さの **向き**（トレンド）と書く。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| "The default setting for the Base Line is 26 periods and can be adjusted. On a daily chart, this line is the midpoint of the 26-day high-low range, which is almost one month." | SC-ICHI | 日足 | ✅ |
| "Price Moves above the Base Line (momentum)" / "Price Moves below Base Line (momentum)" | SC-ICHI（合図のまとめ） | 時間足は書いてない | ✅ |
| "The trend-following signals focus on the cloud, while the momentum signals focus on the Conversion and Base Lines." | SC-ICHI | 時間足は書いてない | ✅ |
| "It serves as a slower indicator and reflects the medium-term market trend." | LF-ICHI | 時間足は書いてない | ✅ |
| "If the market price is above the Kijun-sen, this confirms an uptrend. And if it is below the Kijun-sen, it confirms a downtrend." | LF-ICHI | 時間足は書いてない | ✅ |

### Q2 レンジとショートでの使い方

答え：ショートは「**下げのトレンドの中で、値段が基準線の上に戻ってから、また下へ割ったとき**」。レンジ（雲の中・平らな雲・もみ合い）では使わない、と書くページがある。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| （ショート）"During an uptrend, a bullish signal is triggered when price crosses above the Base Line. Similarly, price crossing below the Base Line during a downtrend is a bearish signal." | SC-ICHI | 時間足は書いてない | ✅ |
| （ショート）"With the stock trading below the red cloud, prices bounced above the Base Line (red) to enable the setup. This move created a short-term overbought situation within a bigger downtrend. The bounce ended when prices moved back below the Base Line to trigger the bearish signal." | SC-ICHI | 日足の例 | ✅ |
| （レンジ）"First, the trend is up when prices are above the cloud, down when prices are below the cloud, and flat when prices are in the cloud." | SC-ICHI | 時間足は書いてない | ✅ |
| （レンジ・5分足）"Avoid relying on Ichimoku for scalping or in tight, choppy ranges — on very short timeframes the indicator is often whipsawed and produces many low‑quality signals. If price is inside a flat, narrow cloud or the market shows no directional momentum, stand aside or switch to oscillators better suited for range trading." | RS-ICHI（1サイトだけ） | 5分足のページ | ✅ |
| （レンジ）"In sideways markets, though, the line often gives false signals, which is why traders use the cloud to filter them out." | LF-ICHI（転換線についての文） | 時間足は書いてない | ✅ |

### Q3 パラメータ

答え：既定は **(9, 26, 52)**。基準線は **26**。スキャルは (5, 13, 26)（基準線 13）と書くページ、5分足でも既定 (9, 26, 52) と書くページ、1分足は (12, 24, 120)（基準線 24）と書くページがある。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 既定 (9, 26, 52) | "Default settings are 9 for the Conversion Line, 26 for the Base Line and 52 for the Leading Span B." | SC-ICHI | 時間足は書いてない | ✅ |
| 変えてよい | "These numbers can be adjusted to suit individual trading and investing styles." | SC-ICHI | 時間足は書いてない | ✅ |
| スキャル (5, 13, 26) | "Scalping. Shorter periods like 5, 13, and 26 produce more signals, but also more false ones. They are best suited to 15-minute or even 5-minute charts." | LF-ICHI（1サイトだけ） | 15分足・5分足 | ✅ |
| 1時間足より上が向く | "Best settings. Classic: 9, 26, 52. Scalping: 5, 13, 26. Swing trading: 9, 26, 52. The indicator works best on 1-hour time frames and above." | LF-ICHI | 1時間足より上 | ✅ |
| 5分足 (9, 26, 52) | "The best settings for the Ichimoku 5 min chart are standard default settings 9-26-52" | RS-ICHI（1サイトだけ） | 5分足 | ✅ |
| 1分足 (12, 24, 120) | "The best Ichimoku settings for scalping and 1-minute chart are 12-24-120" | RS-ICHI（1サイトだけ） | 1分足 | ✅ |
| 5分足の成績は悪い | "However, we saw that performance was worse on the 5-minute chart than on H4 or daily." | RS-ICHI | 5分足／4時間足・日足 | ✅ |
| デイトレの値・範囲 | 「デイトレ」と名指しした値と、基準線の期間の範囲 | — | ✗ 見つからなかった（資料の表の「デイトレ (5,13,26)・15分足」は、LF-ICHI の今のページには「day trading」の語が無く、「Scalping」の行として書かれている） |

### Q4 閾値

答え：数の閾値は **持たない**。形は「**値段と基準線の交差**」と「**転換線と基準線の交差**」で、どちらも「**トレンドの向き（雲の上か下か）**」という前提つき。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 交差（前提つき） | "Conversion-Base Line Crossovers During an uptrend, a bullish signal is triggered when the Conversion Line crosses above the Base Line. Similarly, the Conversion Line crossing below the Base Line during a downtrend is a bearish signal." | SC-ICHI（見出しと本文） | 時間足は書いてない | ✅ |
| 前提 | "Bearish signals are reinforced when prices are below the cloud, and the cloud is red." | SC-ICHI | 時間足は書いてない | ✅ |
| 乖離の大きさの閾値 | 値段と基準線の離れ具合（%）の閾値 | — | ✗ 見つからなかった（LF-ICHI は "When the price moves far away from this line, it is likely to return to this level." と書くが、数は書いてない） |

---

## 8. 包み足（Engulfing）

### Q1 何を見ているか

答え：**向きの反転**（2本の足でできる反転の形）。教科書の7つの区分のどれかに当てはめた文は無い。いちばん近いのは「向き」（反転）。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| "A reversal pattern that can be bearish or bullish, depending upon whether it appears at the end of an uptrend (bearish engulfing pattern) or a downtrend (bullish engulfing pattern)." | SC-CDD | 日足（"The first day"） | ✅ |
| "The bullish engulfing candlestick acts as a bullish reversal 63% of the time" | PS-BU | 日足の検証 | ✅ |
| "It works very well as a bearish reversal, performing that way 79% of the time" | PS-BE | 日足の検証 | ✅ |

### 形の条件

| 条件 | 逐語 | 出どころ | 確かめ |
|---|---|---|---|
| 陽の包み足：1本目が陰、2本目が陽で、2本目の実体が1本目の実体を包む。ひげは見ない | "The first is a black candle followed by a taller white one. The white candle should have a close above the prior open and an open below the prior close. In other words, the body of the white candle should engulf or overlap the body of the black candle. Ignore the shadows." | PS-BU | ✅ |
| 陰の包み足：1本目が陽、2本目が陰で、2本目の始値は前の終値より上、終値は前の始値より下 | "By overlaps , I mean the body of the black candle has an open above the prior close and a close below the prior open." | PS-BE | ✅ |
| 1本目は十字線でない。2本目は長い。ひげまで包むのは、要らない | "The size of the white candlestick is relatively unimportant, but it should not be a doji, which would be relatively easy to engulf. The second should be a long black candlestick. The bigger it is, the more bearish the reversal. The black body must totally engulf the body of the first white candlestick. Ideally, the black body should engulf the shadows as well, but this is not a requirement." | SC-CBE | ✅ |
| 前にトレンドが要る（陽は下げの後、陰は上げの後） | "Price trend leading to the pattern Downward." / "Price trend leading to the pattern Upward." | PS-BU／PS-BE | ✅ |
| 始値と終値だけを包む（高値と安値は要らない） | "This pattern is similar to the outside reversal chart pattern, but does not require the entire range (high and low) to be engulfed, just the open and close." | SC-CDD（リンクの記号を外した） | ✅ |
| TA-Lib：片方の端が等しくてもよい（そのときは 80、両端とも越えれば 100） | "* Must have:" / "* - first: black (white) real body" / "* - second: white (black) real body that engulfs the prior real body"（式は `(inClose[i] >= inOpen[i - 1]) & (inOpen[i] < inClose[i - 1])) \| ((inClose[i] > inOpen[i - 1]) & (inOpen[i] <= inClose[i - 1])`） | TALIB | ✅ |
| 確かめの足が要る | "Further weakness is required for bearish confirmation of this reversal pattern." | SC-CBE | ✅ |

### Q2 レンジとショートでの使い方

答え：ショートは **陰の包み足**（上げの後）。Bulkowski は「下げのトレンドの中の、上への戻りで売る」と書く。**レンジでの使い方は書いてない。**

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| （ショート）"Trade upward retracements in a downward price trend -- page 313." | PS-BE | 日足の検証 | ✅ |
| （ショート）"Thus, even though price will often reverse, the bearish engulfing candlestick does not imply a lasting reversal." | PS-BE | 日足の検証 | ✅ |
| （ショート）"After meeting resistance around $30 in mid-January, Ford (F) formed a bearish engulfing pattern (red oval). It was immediately confirmed with a decline and subsequent support break." | SC-CBE（リンクの記号を外した） | 日足の例 | ✅ |
| （レンジ） | 包み足をレンジでどう使うか | — | ✗ 見つからなかった（どのページも、前にトレンドが在ることを条件にしている） |

### Q3 パラメータ

答え：**持たない**（形の条件だけ）。TA-Lib の関数も、期間の引数を持たない（見る足は2本）。

| 値 | 逐語 | 出どころ | 確かめ |
|---|---|---|---|
| 2本を見る | "TA_LIB_API int TA_CDLENGULFING_Lookback( void ) { return 2; }"（改行を詰めた） | TALIB | ✅ |
| スキャル・デイトレの値 | 包み足の短い足向けの条件 | — | ✗ 見つからなかった |

### Q4 閾値

答え：数の閾値は **持たない**。形は「**形が在るか無いか**」（TA-Lib は ±100 と ±80 を返す）。実体の大きさの「長い」に数は書いてない。

| 値 | 逐語 | 出どころ | 確かめ |
|---|---|---|---|
| 長い足を選ぶ（数なし） | "Select tall candles -- page 311." | PS-BE | ✅ |
| 実体の大きさの数 | 「長い」の数（例＝ATR の何倍） | — | ✗ 見つからなかった |

---

## 9. 帯pivot（もとのピボットの R1 と S1）

帯pivot はこのリポジトリで作った部品で、教科書に同じ名前は無い。ここでは元の Standard（Traditional・Floor）Pivot Points の R1 と S1 を調べた。

### 式と、どの期間から作るか

| 項目 | 逐語 | 出どころ | 確かめ |
|---|---|---|---|
| P・R1・S1 の式 | "Pivot Point (P) = (High + Low + Close)/3" / "Support 1 (S1) = (P x 2) - High" / "Resistance 1 (R1) = (P x 2) - Low" | SC-PIV（Markdown 版） | ✅ |
| 前の期間の値 | "Keep in mind that the high, low and close are all from the prior period." | SC-PIV | ✅ |
| 同じ式（Traditional） | "R1 = P * 2 - prevLow" / "S1 = P * 2 - prevHigh" | TV-PIV | ✅ |
| 1〜15分足は前の日 | "Pivot Points for 1-, 5-, 10-, and 15-minute charts use the prior day's high, low, and close. ... Once Pivot Points are set, they do not change and remain in play throughout the day." | SC-PIV（間の1文を「...」にした） | ✅ |
| 30〜120分足は前の週 | "Pivot Points for 30-, 60-, and 120-minute charts use the prior week's high, low, and close." | SC-PIV | ✅ |
| 日足は前の月 | "Pivot Points for daily charts use the prior month's data." | SC-PIV | ✅ |
| TradingView の Auto | "1D for chart resolutions up to and including 15 min" / "1W for chart resolutions greater than 15 min and less than 1 day" / "1M for chart resolutions from 1 day and above" | TV-PIV | ✅ |
| 暗号資産の「日」の区切り（UTC か NY か） | 暗号資産で前の日をいつで切るか | — | ✗ 見つからなかった（検索に出た blockspot.io は 403、bitget.com の wiki は 404 で開けなかった） |

### Q1 何を見ているか

答え：**位置**（前もって推した支えと抵抗の線）。P より上か下かで向きを見る使い方も書いてある。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| "Pivot Points use the prior period's high, low, and close to estimate future support and resistance levels. In this regard, Pivot Points are predictive or leading indicators." | SC-PIV | 時間足は書いてない | ✅ |
| "Pivot Points are significant levels on a chart that traders and investors can use to determine directional movement and potential support/resistance levels." | SC-PIV | 時間足は書いてない | ✅ |

### Q2 レンジとショートでの使い方

答え：ショートは「**抵抗（R1）まで上がって止まったら、抵抗での失敗と下げを探す**」と「**P を下に割ったら、S1 を目標にする**」。「レンジ」という語では書いてない。

| 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|
| （ショート）"Similarly, if prices advance to resistance and stall, traders can look for a failure at resistance and decline. Again, look for a bearish chart pattern or indicator signal to confirm a downturn from resistance." | SC-PIV | 時間足は書いてない（同じページの例は 15分足） | ✅ |
| （ショート）"A move below the Pivot Point suggests weakness with a target to the first support level. A break below the first support level shows even more weakness with a target to the second support level." | SC-PIV | 時間足は書いてない | ✅ |
| （支えと抵抗）"Support and resistance levels based on Pivot Points can be used like traditional support and resistance levels." | SC-PIV | 時間足は書いてない | ✅ |
| （行き過ぎは R2・S2）"A move above the second resistance level would show strength but also indicate an overbought situation that could lead to a pullback." | SC-PIV | 時間足は書いてない | ✅ |
| （レンジ） | 「range」「sideways」の語でピボットの使い方を書いた文 | — | ✗ 見つからなかった |

### Q3 パラメータ

答え：式の中の数は **持たない**。選ぶのは「どの期間から作るか」だけ（5分足なら前の日）。TradingView は表示の本数（既定 15）を持つが、これは線の数で、式のパラメータではない。

| 値 | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|
| 5分足は前の日 | 上の「1〜15分足は前の日」の文 | SC-PIV／TV-PIV | 1〜15分足 | ✅ |
| 表示の本数 15 | "the default “Number of Pivots Back” value of 15 means that the indicator displays pivots for each of the last 15 weeks." | TV-PIV | 時間足は書いてない | ✅ |
| 帯の幅（このリポジトリの t） | 線のまわりの幅 t の値 | — | ✗ 見つからなかった（教科書のピボットの式に幅は無い） |

### Q4 閾値

答え：数の閾値は **持たない**。形は「**線そのもの**（R1・S1）に値段が触れる・越える」で、確かめの形や指標と組む（前提つき）。

| 値 | 逐語 | 出どころ | 確かめ |
|---|---|---|---|
| 線で確かめる | "As with all indicators, confirming Pivot Point signals with other aspects of technical analysis is important. A bearish candlestick reversal pattern could confirm a reversal at second resistance." | SC-PIV | ✅ |
| 数の閾値 | R1・S1 からの距離の数 | — | ✗ 見つからなかった |

---

## BTC・暗号資産について書いた資料（一般の資料と分けた）

| 指標 | 答え | 逐語 | 出どころ | 時間足 | 確かめ |
|---|---|---|---|---|---|
| ADX | 暗号資産の 1時間足・15分足は 10〜12 を試す | "For intraday crypto on 1-hour and 15-minute charts, test shorter periods (10 to 12) because the 14-period lookback covers a short window at those resolutions." | RL-ADX | 1時間足・15分足 | ✅ |
| ADX | 暗号資産は ADX の値が高めに出る | "The 25 threshold still functions as a reasonable trend confirmation level, but ADX values in confirmed trending conditions tend to run higher in crypto than in equities." | RL-ADX | 日足の比較 | ✅ |
| ADX | 4時間足で 14 を使っている | "The 14-period default is what RegimeLab uses on the 4-hour timeframe across all tracked pairs." | RL-ADX | 4時間足 | ✅ |
| ADX | 暗号資産の日足は 14・20・25 のまま | "Crypto daily ADX 14 includes Saturday and Sunday. ... Keep 14, 20, and 25." | TRT-ADX（間の1文を「...」にした） | 日足 | ✅ |
| RSI | 暗号資産の 5分足は 7〜9、80／20 | "For crypto trading on 5-minute charts, consider: RSI Period: 7 to 9 Overbought Level: 80 Oversold Level: 20"（行を詰めた） | EPB（1サイトだけ） | 5分足 | ✅ |
| RSI | 暗号資産の 5分足のスキャルは 5、80／20 | 上の RSI の Q3 の WT の文 | WT（1サイトだけ） | 5分足 | ✅ |
| RSI | 暗号資産の日足は 14・70・30 のまま | "Crypto daily bars include weekends. RSI 14 on BTC or ETH is fourteen calendar days, not fourteen weekday sessions." | TRT-RSI | 日足 | ✅ |
| BB | 暗号資産の日足は 20・2 のまま | "Bands of 20 and 2 on BTC or ETH cover twenty calendar days, not twenty weekday sessions. Strong trends can ride a band, so fading every tag is often early. Keep 20 and 2, and wait for the close back inside." | TRT-BB | 日足 | ✅ |
| ATR | 暗号資産の ATR は値段の単位で、週末を含む | "Crypto ATR is in price units and includes weekend bars. Compare ATR to price, not to a stock's ATR." | TRT-ATR | 時間足は書いてない | ✅ |
| DI差・基準線・包み足・ピボット | 暗号資産について書いた文 | — | — | — | ✗ 見つからなかった |
| 9種すべて | **BTC の 5分足**を名指しした文 | — | — | — | ✗ 見つからなかった（いちばん近いのは EPB の「crypto 5-minute」の RSI の値） |

---

## いまの値と違う所

どちらが正しいかは決めない。違いだけを書く。

### ADX の代表の値（スキャル 14／デイトレ 7）

- いまの値：スキャル **14**、デイトレ **7**（indicators.json の「代表の値」と、by_strategy の「最初の値」）。by_strategy の出どころの欄は、スキャルが「既定」、デイトレが「デイトレ」。review の「スキャル」の欄は「無い」。
- 教科書：**スキャルをデイトレより長くする、と書いたページは見つからなかった。** 書いてあることは次のとおり。
  - TRT-ADX：デイトレは 15分足か1時間足で **14**、5分足は速くしたいときに **7 か 10**（"Day traders keep 14 on a 15 minute or 1 hour chart. Period 7 or 10 on a 5 minute chart reacts faster and spikes more."）。5分足で 14 のままでもフィルターにはなる、とも書く。
  - RL-ADX：15分足〜1時間足のデイトレは **7〜14**、15分足では短い 7〜10 がよく使われる。
  - SC-ADX・TV-DMI：既定 14 だけ。足やスタイルの値は書いてない。
- つまり、ページの並びは「短い足ほど短く（または同じ 14）」で、いまの値の「スキャル（5分足）14 ＞ デイトレ 7」とは向きが逆。デイトレの 7 は RL-ADX の「7〜14」の下の端にあたる。TRT-ADX の「デイトレは 14」とは違う。
- 資料の表（review）の ADX「デイトレ」の行にある EBC（ebc.com）の「7〜10（day traders）」は、今回は開いていない。

### RSI

- いまの範囲 n＝2〜21、代表 7／14。
- 範囲の端の 2 は SC-RSI（短期の売買の 2-period）と MC2（1分足）、21 は BLX（日足のスイング）。1つの文で「2〜21」と書いたページは無い。
- デイトレの代表 **14** について：BLX・TRT-RSI は、デイトレは日中の足（5分足・15分足）で **7〜9**、EPB は **9〜10**、WT は 15分足で **9**、1時間足で 14 と書く。デイトレで 14 と書くのは、1時間足（WT）と「既定」としてだけ。
- Brown の上げ相場と下げ相場の帯は、ページで値が違う：SC-RSI は **40〜90／10〜60**、TRT-RSI は **40〜80／20〜60**。
- indicators.json の「使い方の記録」の RSI の 70／30 の出どころは、engine_tuner_gen.py の定数と書いてある。教科書（SC-RSI・TV-RSI）にも 70／30 は在る。5分足では 75／25 や 80／20 を書くページ（BLX・EPB・WT・TRT-RSI）がある。

### BB幅・BB%b

- いまの範囲 n＝10〜50、s＝1.9〜2.1 は、n と s を別々に動かせる形。Bollinger（BB-R ルール11・SC-BB）は **組** で書く：(10, 1.9)・(20, 2)・(50, 2.1)。
- いまの組 (50, 2.0) は、Bollinger の (50, 2.1) と倍率が違う（review のメモにも同じことが在る）。
- スキャルの代表 (20, 2) について：TRT-BB は 5分足のスキャルでは (20, 2) は「遅い」と書き、(10, 1.9) を挙げる。OX はスキャル（1分足・5分足）で 10〜14 と 1.5〜2 と書く。1.5 は、いまの s の範囲（1.9〜2.1）の外。
- review の BB幅「スキャル」の出どころ（litefinance.org の Bollinger の記事）は、今回開くと **404**。pocketoption.com は本文を取れなかった。この2つの値（2.2 など）は確かめ直せていない。
- BB%b の役割：roles の「今の答える問いの区分」は **行き過ぎ**、indicators.json の札は「オシレーター」。BB-R ルール15 は「where we are in relation to the Bollinger Bands」（**位置**）と書く。SC-PB は位置・行き過ぎ・トレンドの強さの3つを書く。

### ATR%

- いまの範囲 n＝5〜21、代表 14／14。代表の 14 は SC-ATR・TV-ATR・TRT-ATR（5分足・15分足でも 14）と同じ。
- 範囲 5〜21 の出どころ（marketclutch.com）は、今回開くと **404**。確かめ直せていない。TRT-ATR は 10 と 7 を書くが、範囲は書いてない。

### 基準線

- いまの範囲 k＝13〜26、代表は決めていない。13 は LF-ICHI のスキャル (5, 13, 26) の基準線、26 は既定。RS-ICHI は 5分足でも既定の 26、1分足は 24 と書く。
- review の基準線「デイトレ」の行（LF-ICHI・(5, 13, 26)・15分足（day trading））について：今回開いた LF-ICHI の本文では、(5, 13, 26) は「Scalping」の行で、「day trading」の語は見つからなかった。ページが書き換わった可能性がある（2026-09-25 の日付あり）。
- 役割：roles の区分は **向き**、indicators.json の札は「トレンド」。SC-ICHI は、値段と基準線の交差を **momentum** の合図と書く。LF-ICHI はトレンド（向き）と書く。2つのページで違う。
- indicators.json の計算は「close と基準線の乖離%」。乖離の大きさに閾値を書いた教科書は見つからなかった。

### 包み足

- いまの計算（indicators.json の式）：1本目が陰（close < open）、2本目の open < 1本目の close、2本目の close > 1本目の open（陽の包み足）。陰の包み足は逆。等しいときは数えない。
- 教科書との違い：
  1. **前のトレンドを見ていない。** PS-BU・PS-BE・SC-CDD は、陽の包み足は下げの後、陰の包み足は上げの後と書く。
  2. **1本目が十字線でないこと、2本目が長いことを見ていない**（SC-CBU・SC-CBE）。
  3. **等しいときの扱いが TA-Lib と違う。** TA-Lib は片方の端が等しくても包み足とし、80 を返す。いまの式は両方とも等しくないことを求める（PS-BU・PS-BE の文の形には合う）。
  4. いまの式は2本目の色を見ていない。ただし、包む条件を満たせば2本目の色は決まる（陽の包み足なら close > 前の open > 前の close > open）。
- 資料の表（review・roles・by_strategy）に包み足の行は無い。indicators.json の「教科書の出どころ」は null。

### 帯pivot

- いまの計算（observe_diag.py の `_pivot_prev_period`）：日中の足は「前の UTC の日」の高値・安値・終値から P・R1・S1 を作り、その日のあいだ動かさない。R1＝2P−L、S1＝2P−H。
- 教科書との照らし：5分足で前の日から作るのは SC-PIV・TV-PIV（Auto＝1D）と同じ。式も同じ。
- 日の区切りを UTC にした根拠は、教科書では見つからなかった（暗号資産の日の区切りを書いたページを開けなかった）。
- 帯の幅 t（0.0015〜0.006）は、教科書のピボットには無い数。

### DI差

- いまの範囲 n＝7〜21、代表 14／14。既定 14（TV-DMI・TRT-ADX）と同じ。DI の期間だけをスタイル別に書いたページは無い。review のメモと同じ。

---

## 分からなかったこと

1. **開発者の本を直に読めなかった。** Wilder の『New Concepts in Technical Trading Systems』（RSI・ADX・DMI・ATR）と、細田悟一の一目均衡表の本は、Web に本文が無い。SC と TV が引く文だけで書いた。
2. **ADX のスキャルの値。** 「スキャル」と名指しした ADX の期間を、開いたページの文では見つけられなかった。5分足の値は TRT-ADX の 7・10・14 だけ。検索の要約には「1分足で期間を上げないと乱れる」という主張が出たが、どのページの文かを開いて確かめられなかった（tradingbrokers.com は curl では応答が空、WebFetch では名前が引けなかった）。
3. **暗号資産のピボットの日の区切り。** UTC 0時か、NY の16時か。blockspot.io（403）と bitget.com の wiki（404）を開けず、確かめられなかった。
4. **BTC の 5分足を名指しした資料。** 9種のどれにも見つからなかった。暗号資産の 5分足の値は、RSI の EPB と WT だけ。
5. **開けなかったページ。** 資料の表の出どころのうち、marketclutch.com（ATR の範囲 5〜21・404）、litefinance.org の Bollinger の記事（404）、pocketoption.com（本文が取れない）。検索に出た Investopedia（402）、gate.com と forextester.com（403）。この5つの値は確かめ直せていない。
6. **レンジでの使い方が書いてない指標。** BB%b・包み足・ピボット（R1・S1）は、レンジでの使い方を書いたページが見つからなかった。
7. **数の範囲が書いてない値。** RSI と ADX の閾値の範囲、DI の期間の範囲、基準線の期間の範囲は、1つの文で範囲を書いたページが見つからなかった（いくつかのページの値を並べると幅は出るが、この文書では作らない）。
8. **包み足の「長い足」の数。** 実体の大きさを数（例＝ATR の何倍）で書いたページは見つからなかった。
