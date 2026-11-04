# 閾値の範囲とパラメータの範囲を教科書で探した結果（ToDo 270番＝222番の材料）

この文書は `out_textbook_ranges_270.json` を、人が読む形にまとめた物です。値を決めていません。範囲を作っていません。文から1つを選んでいません。データ・プログラム・文書は直していません。

- ページは、curl と Chromium（この環境に入っている、Chrome と同じ中身のブラウザ）の両方で開きました。逐語は、開いた本文から切り出し、空白の数だけをそろえて照らしました。
- 両方で開けなかったページは、WebFetch でも試しました。過去のページの保存（web.archive.org）は、このセッションでは接続が切られ、開けませんでした（下の4章）。
- 新しいページの検索は、全部の件で行いました（WebSearch が通ったのは27回。ほかに、Investopedia を絞り込みの先に入れた8回は、検索の道具が受け付けなかった。その8回は Investopedia を外して検索し直した）。

## 1. 8件の結果

| 番号 | 指標 | 探す物 | 結果 | 文に両端が在る文の数 | 文の数 | 開いたページの数 | 両端の文が何の両端か |
|---|---|---|---|---|---|---|---|
| 1 | RSI | 閾値の範囲（形＝値） | 両端の文が在る | 1 | 11 | 12 | Cardwell の弱気の反転の形で RSI が来る所（50-70）。閾値を探す幅とは書いてない |
| 2 | ADX | 閾値の範囲（形＝値） | 両端の文が在る | 2 | 12 | 14 | 掲示板の条件の帯（25〜40）と、ブログの「20-25 より上」。探す幅とは書いてない |
| 3 | DI差 | 閾値の範囲（形＝値） | 値を挙げた文だけ在る | 0 | 5 | 12 | — |
| 4 | BB%b | 閾値の範囲（形＝値） | 両端の文が在る | 3 | 9 | 11 | StockSharp の戦略の例のコードの最適化の範囲（0.1〜0.3・0.7〜0.9・0.3〜0.7）。うち2つはロングだけの戦略 |
| 5 | ATR% | 閾値の範囲（形＝値か倍率） | 両端の文が在る | 2 | 5 | 14 | 損切りの幅の ATR の倍率（1.5〜3.0・スキャル 1.0〜1.5）。ATR% の値の閾値の両端の文ではない |
| 6 | 基準線 | 閾値の範囲（形＝値） | 値を挙げた文だけ在る | 0 | 4 | 10 | — |
| 7 | DI差 | パラメータ n の範囲 | 両端の文が在る | 4 | 8 | 10 | DMI の期間の両端（5〜7・10〜14・20〜30・7〜10） |
| 8 | 基準線 | パラメータ k の範囲 | 値を挙げた文だけ在る | 0 | 15 | 17 | — |

「両端の文が在る」は、範囲の形が「文に両端が在る」の文が1つでも在ることを指します。その両端が、閾値やパラメータを探す幅として書かれているとは限りません。何の両端かは、右の欄と、2章の各行の注に書きました。

## 2. 8件ごとの文

### 1. RSI｜閾値の範囲（形＝値）（結果：両端の文が在る）

使った検索の語：
- RSI overbought threshold range adjust between 70 and 80 scalping
- RSI overbought level optimization range 65 to 85 backtest
- RSI overbought oversold levels adjust 80 20 90 10（schwab・fidelity・babypips・stockcharts・tradingview・cmegroup に絞った）
- RSI overbought level tested from 60 to 90 backtest results thresholds quantified
- crypto bitcoin RSI 5 minute scalping overbought 75 85 levels short

| # | 逐語 | 範囲の形 | 下の端 | 上の端 | 閾値の形 | 単位 | 話の相手 | 時間足 | 出どころの質 | 注 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | For example, if a security is repeatedly reaching the overbought level of 70 you may want to adjust this level to 80.<br>https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/RSI | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | 定番の教育サイト（Fidelity の学習の頁） | 70 を 80 に動かす例。本文で照らした道具：curl（空白の数だけそろえた） |
| 2 | Raising the overbought threshold to 80 or lowering the oversold threshold to 20 could reduce the number of overbought/oversold readings.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | 定番の教育サイト（StockCharts ChartSchool） | 264番でも見つかった文。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 3 | Again, the higher high is usually just below overbought levels in the 50-70 area.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | 文に両端が在る | 50 | 70 | 前提つき | 0〜100 | ショート | 時間足は書いてない | 定番の教育サイト（StockCharts ChartSchool） | Cardwell の弱気の反転の形の中で、RSI の高値が来る所。閾値を探す幅とは書いてない。「ショート」は弱気の反転の形の話であるため（文に short の語は無い）。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 4 | For example, someone might consider any number above 80 as overbought and anything below 20 as oversold.<br>https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/ | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | 定番の教育サイト（TradingView のヘルプ） | 本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 5 | In a falling market they shift down, so a market is only really oversold near 10 and can be considered overbought as early as 60.<br>https://www.mql5.com/en/blogs/post/774746 | 値を挙げただけ | None | None | 前提つき | 0〜100 | 一般 | 時間足は書いてない | ブログ（MQL5 の投稿・2026-08-25） | 前提＝下げ相場。下げ相場では 60 で買われ過ぎと見てよい、と書く。Constance Brown の本の読みとして書いている。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 6 | In a rising market the useful thresholds shift up, toward roughly 40 and 90.<br>https://www.mql5.com/en/blogs/post/774746 | 値を挙げただけ | None | None | 前提つき | 0〜100 | 一般 | 時間足は書いてない | ブログ（MQL5 の投稿・2026-08-25） | 前提＝上げ相場。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 7 | An overbought reading during a downtrend is also much lower than 70.<br>https://www.investopedia.com/terms/r/rsi.asp | 値を挙げただけ | None | None | 前提つき | 0〜100 | 一般 | 時間足は書いてない | 定番の教育サイト（Investopedia） | curl は 402 で開けず、Chromium で開いた本文の文。前の文は Constance Brown の読みを紹介している。本文で照らした道具：Chromium（空白の数だけそろえた） |
| 8 | Although the experimental group RSI trades were profitable at the most extreme levels (90 short, 10 long), they were substantially less profitable at the 70 and 30 levels most commonly used by traders, with a mean profit of 0.4% and 1.6%, respectively.<br>https://github.com/toobrien/rsi | 値を挙げただけ | None | None | 値 | 0〜100 | ショート | 時間足は書いてない | ブログ（GitHub の個人の調べ toobrien/rsi） | curl は 403、Chromium で開いた本文の文。ショートで 70・80・90 を試した結果の文。数の範囲で探した文ではない。本文で照らした道具：Chromium（空白の数だけそろえた） |
| 9 | When using 75 RSI as the overbought level to short SPY, the strategy actually has a positive return despite shorting into uptrends.<br>https://stockbros.substack.com/p/does-the-relative-strength-index | 値を挙げただけ | None | None | 値 | 0〜100 | ショート | 時間足は書いてない | ブログ（StockBros の Substack） | 同じページで 70・75・80 の3つを試している（Timeframe: Daily と書いた節）。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 10 | The first condition will be met when the asset has an RSI of greater than 65, and is around the overbought region, in a 5-minute timeframe.<br>https://help.coinrule.com/articles/376756-rsi-top-scalper | 値を挙げただけ | None | None | 値 | 0〜100 | 5分足・ショート | 5-minute timeframe | ボットの説明書（Coinrule のヘルプ。暗号資産の取引の道具） | ショートは、同じページの「In this strategy, we focus on short selling, the process of selling and buying back lower.」から読んだ。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 11 | The default settings are: * RSI Length: 14; * Overbought Level: 80; * Oversold Level: 20; * Midpoint: 50.<br>https://www.tradingview.com/script/ImVAOTyf-Modern-RSI/ | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | TradingView の公開スクリプト（Modern RSI） | 既定の値の列挙。本文で照らした道具：curlとChromium（空白の数だけそろえた） |

### 2. ADX｜閾値の範囲（形＝値）（結果：両端の文が在る）

使った検索の語：
- ADX threshold range 20 to 30 trend strength levels 0-25 25-50 50-75
- ADX threshold optimize between 15 and 30 scalping 5-minute
- ADX values 0-25 absent weak trend 25-50 strong 50-75 very strong 75-100（tradingview・fidelity・babypips・stockcharts・schwab に絞った）
- ADX threshold backtest optimization range values tested 15 20 25 30 35 40

| # | 逐語 | 範囲の形 | 下の端 | 上の端 | 閾値の形 | 単位 | 話の相手 | 時間足 | 出どころの質 | 注 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Wilder suggests that a strong trend is present when ADX is above 25 and no trend is present when ADX is below 20.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | 定番の教育サイト（StockCharts ChartSchool） | Wilder の値として紹介。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 2 | In practice, most chart analysts believe a reading above 25 typically indicates a strong trend, and a reading below 20 usually suggests there is no trend—with no clear signal interpretation existing between 20 and 25.<br>https://www.fidelity.com/viewpoints/active-investor/average-directional-index-ADX | 強さの区切り | 20 | 25 | 値 | 0〜100 | 一般 | 時間足は書いてない | 定番の教育サイト（Fidelity） | 20〜25 は「はっきりした読みが無い間」と書く。探す幅とは書いてない。本文で照らした道具：curl（空白の数だけそろえた） |
| 3 | Value Interpretation: 0-25: Weak trend or sideways market 25-50: Moderate to strong trend 50-75: Very strong trend 75-100: Extremely strong trend (rare)<br>https://in.tradingview.com/script/FstitqUD/ | 強さの区切り | 0 | 100 | 値 | 0〜100 | レンジ | 時間足は書いてない | TradingView の公開スクリプト（Average Directional Index info） | 4つの区切り（0-25・25-50・50-75・75-100）。「レンジ」は 0-25 の「sideways market」から。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 4 | Below 20 = no trend, the market is chopping.<br>https://crosstrade.io/learn/technical-indicators/adx | 強さの区切り | None | 20 | 値 | 0〜100 | 一般 | 時間足は書いてない | 証券会社の解説（CrossTrade） | 同じページに「20–40 = trend is developing or in place.」「Above 40 = strong trend (rare, don't expect it often).」が続く。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 5 | 20–40 = trend is developing or in place.<br>https://crosstrade.io/learn/technical-indicators/adx | 強さの区切り | 20 | 40 | 値 | 0〜100 | 一般 | 時間足は書いてない | 証券会社の解説（CrossTrade） | 本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 6 | Waiting for ADX > 30 on intraday charts will filter out most valid trends.<br>https://crosstrade.io/learn/technical-indicators/adx | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | intraday charts | 証券会社の解説（CrossTrade） | 日中の足で 30 を待つと、多くのトレンドを落とす、と書く。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 7 | 20 is the common threshold — 25 if you want to be stricter.<br>https://crosstrade.io/learn/technical-indicators/adx | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | 証券会社の解説（CrossTrade） | 本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 8 | A trend shows the most strength when the Average Directional Index is above 25 (potential signal to buy), and a trend is weak or the price is considered trendless if the ADX reaches below 20 - according to the concept creator, Wilder.<br>https://www.tradingview.com/support/solutions/43000589099-average-directional-index-adx/ | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | 定番の教育サイト（TradingView のヘルプ） | curl は応答なし、Chromium で開いた本文の文。本文で照らした道具：Chromium（空白の数だけそろえた） |
| 9 | Moving 25 to 30 is a threshold test, not a period test.<br>https://therighttrader.com/learn/indicator-strategies/best-adx-settings | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | ブログ（The Right Trader） | 同じページに「A mark at 30 lets fewer trends through and will skip some real DI crosses.」も在る。本文で照らした道具：curl（空白の数だけそろえた） |
| 10 | The most commonly regarded levels, above which a stock may be said to be trending, are 20 and 25.<br>https://www.incrediblecharts.com/stock_screener/stock_screener_directional_movement.php | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | 証券会社の解説（Incredible Charts の銘柄選びの道具の説明） | 本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 11 | Dovrebbe darmi solo i valori compresi tra 25 e 40 e non tutti quelli sopra 25 e tutti quelli sotto 40.<br>https://www.prorealcode.com/topic/adx-compreso-tra-due-valori/ | 文に両端が在る | 25 | 40 | 値 | 0〜100 | 一般 | 時間足は書いてない | 掲示板（ProRealCode の投稿・イタリア語・2017-10-02） | ADX が 25 から 40 の間のときだけを取る条件を書いた投稿。探す幅とは書いてない。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 12 | To reduce the likelihood of false signals, look for the ADX line above a certain threshold; commonly, a value above 20-25 suggests a stronger trend.<br>https://www.liberatedstocktrader.com/adx-indicator/ | 文に両端が在る | 20 | 25 | 値 | 0〜100 | 一般 | 時間足は書いてない | ブログ（Liberated Stock Trader） | curl は 403、Chromium で開いた本文の文。「a value above 20-25」＝閾値を 20〜25 のどこかに置く、という書き方。本文で照らした道具：Chromium（空白の数だけそろえた） |

### 3. DI差｜閾値の範囲（形＝値）（結果：値を挙げた文だけ在る）

使った検索の語：
- DI difference threshold +DI minus -DI spread value filter
- +DI -DI spread difference threshold strong directional trend value（fidelity・stockcharts・schwab・tradingview・babypips に絞った）
- "DI+" "DI-" difference greater than 5 10 20 points trend filter

| # | 逐語 | 範囲の形 | 下の端 | 上の端 | 閾値の形 | 単位 | 話の相手 | 時間足 | 出どころの質 | 注 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Adjust the minimum value for DI Difference depending on whether large or small cap stocks: At least 20 for the S&P 500 or ASX 200 At least 30 for the broader Russell 3000 or ASX<br>https://www.incrediblecharts.com/stock_screener/screen-filters-to-identify-momentum-trends.php | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | 証券会社の解説（Incredible Charts） | DI Difference＝DI+ − DI−（同じページの「Calculates the difference between current DI+ and DI- values.」）。同じページの初めに「a time period of 13 weeks」と書く＝週足の13本の話。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 2 | We ran a higher Minimum of 40 (on DI Difference) for the Russell 3000 to reduce the number of stocks returned:<br>https://www.incrediblecharts.com/stock_screener/screen-filters-to-identify-momentum-trends.php | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | 証券会社の解説（Incredible Charts） | 銘柄を減らすために 40 を使った、と書く。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 3 | Try the following values: A Minimum of 20 or 25 for the S&P 500 or ASX 200 A higher Minimum of 30 or 40 for faster-moving small caps in the Russell 3000 or ASX.<br>https://www.incrediblecharts.com/stock_screener/screen-filters-to-identify-momentum-trends.php | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | 証券会社の解説（Incredible Charts の銘柄選びの道具の説明） | DI Difference の最小値として 20 か 25、30 か 40。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 4 | Long when \|+DI - ADX\| ≥ LongDifference and \|-DI - ADX\| ≥ LongDifference with ADX between +DI and -DI.<br>https://doc.stocksharp.com/en/api-examples/1072_Monthly_Performance_Table | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | ライブラリの説明書（StockSharp の戦略の例） | DI と ADX の差の閾値で、DI差（+DI − −DI）ではない。既定は「LongDifference = 10 ShortDifference = 10」（同じページ）。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 5 | A general interpretation would be that during a strong trend (ADX above 25 but dependent on the analyst's interpretation), when the +DI is above the -DI, then a Bullish Market is defined.<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | 値を挙げただけ | None | None | 前提つき | 0〜100 | 一般 | 時間足は書いてない | 定番の教育サイト（TradingView のヘルプ） | 数は ADX の 25 だけ。DI差の数の閾値は書いてない（+DI と −DI の上下だけ）。264番でも見つかった文。本文で照らした道具：curlとChromium（空白の数だけそろえた） |

### 4. BB%b｜閾値の範囲（形＝値）（結果：両端の文が在る）

使った検索の語：
- Bollinger %B threshold 0.8 0.2 overbought oversold range adjust 0.9 0.1
- Bollinger %b overbought oversold levels 0.8 0.2 1.0（fidelity・stockcharts・bollingerbands・schwab・tradingview に絞った）
- %b Bollinger strategy entry threshold 0.05 0.1 0.95 optimize short

| # | 逐語 | 範囲の形 | 下の端 | 上の端 | 閾値の形 | 単位 | 話の相手 | 時間足 | 出どころの質 | 注 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | _lowPercentB = Param(nameof(LowPercentB), 0.2m) .SetDisplay("Low %B", "Lower threshold for %B", "Signals") .SetOptimize(0.1m, 0.3m, 0.05m);<br>https://doc.stocksharp.com/en/api-examples/0968_Larry_Connors_Bollinger_PercentB | 文に両端が在る | 0.1 | 0.3 | 値 | 当てはまる語が無い（%B の値・0〜1 の目盛り） | 一般 | 時間足は書いてない | ライブラリの説明書（StockSharp の戦略の例・Larry Connors %B） | コードの中の最適化の範囲（SetOptimize の両端と刻み 0.05）。この戦略は「Long/Short: Long only.」で、ロングの入る閾値（探さない物に当たるが、両端の書き方の例として残した）。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 2 | _highPercentB = Param(nameof(HighPercentB), 0.8m) .SetDisplay("High %B", "Upper threshold for %B to exit", "Signals") .SetOptimize(0.7m, 0.9m, 0.05m);<br>https://doc.stocksharp.com/en/api-examples/0968_Larry_Connors_Bollinger_PercentB | 文に両端が在る | 0.7 | 0.9 | 値 | 当てはまる語が無い（%B の値・0〜1 の目盛り） | 一般 | 時間足は書いてない | ライブラリの説明書（StockSharp の戦略の例・Larry Connors %B） | ロングの決済の閾値（上と同じ注）。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 3 | Param(nameof(ExitValue), 0.5m).SetRange(0m, 1m) .SetDisplay("Exit %B Value", "Exit threshold for %B", "Exit") .SetOptimize(0.3m, 0.7m, 0.1m);<br>https://doc.stocksharp.com/en/api-examples/0035_Bollinger_B_Reversion | 文に両端が在る | 0.3 | 0.7 | 値 | 当てはまる語が無い（%B の値・0〜1 の目盛り） | 一般 | 時間足は書いてない | ライブラリの説明書（StockSharp の戦略の例・Bollinger Percent B Reversion） | 決済の閾値の最適化の範囲 0.3〜0.7（刻み 0.1）。同じ行の SetRange(0m, 1m) は入力できる範囲。この戦略は「Direction: Both」「CandleType = TimeSpan.FromMinutes(5)」（同じページ）＝両方の向き・既定は5分足。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 4 | Buys when %B < 0 (below lower band), sells when %B > 1 (above upper band).<br>https://doc.stocksharp.com/en/api-examples/0035_Bollinger_B_Reversion | 値を挙げただけ | None | None | 値 | 当てはまる語が無い（%B の値・0〜1 の目盛り） | ショート | 時間足は書いてない | ライブラリの説明書（StockSharp の戦略の例・Bollinger Percent B Reversion） | 売りは %B が 1 より上。本文で照らした道具：curl（空白の数だけそろえた） |
| 5 | In a strong downtrend, %B can be considered overbought when it approaches or exceeds 1.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | 値を挙げただけ | None | None | 前提つき | 当てはまる語が無い（%B の値・0〜1 の目盛り） | 一般 | 時間足は書いてない | 定番の教育サイト（StockCharts ChartSchool） | 前提＝強い下げトレンド。264番でも見つかった文。本文で照らした道具：curl（空白の数だけそろえた） |
| 6 | Downtrends are identified when %B is below 0.20 and MFI(10) is below 20.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | 値を挙げただけ | None | None | 前提つき | 当てはまる語が無い（%B の値・0〜1 の目盛り） | 一般 | 時間足は書いてない | 定番の教育サイト（StockCharts ChartSchool） | Bollinger の %B と MFI の組。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 7 | Use %B crossovers of 0.5 or custom thresholds (e.g., 0.8 / 0.2) to filter trend strength.<br>https://fxreplay.com/indicators/bollinger-bands-b-25fa9 | 値を挙げただけ | None | None | 値 | 当てはまる語が無い（%B の値・0〜1 の目盛り） | 一般 | 時間足は書いてない | 証券会社の解説（FX Replay） | 。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 8 | Exit Signal: Exit the position when the %b value closes above 0.8, signaling an overbought condition where the price is near the upper Bollinger Band.<br>https://www.tradingview.com/script/yXkWPSlU/ | 値を挙げただけ | None | None | 値 | 当てはまる語が無い（%B の値・0〜1 の目盛り） | 一般 | 時間足は書いてない | TradingView の公開スクリプト（Larry Connors %b Strategy） | ロングの決済（探さない物に当たるが残した）。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 9 | Sell: When %b crosses above 80 (approaching the upper band, signaling stretched conditions).<br>https://sentimentrader.com/education/technical-indicators/bollinger-b | 値を挙げただけ | None | None | 値 | 0〜100 | 一般 | 時間足は書いてない | 証券会社の解説（SentimenTrader） | %b を 0〜100 の数で書いている（同じページの別の文は 0〜1 で書く）。ロングの決済の文。本文で照らした道具：curlとChromium（空白の数だけそろえた） |

### 5. ATR%｜閾値の範囲（形＝値か倍率）（結果：両端の文が在る）

使った検索の語：
- ATR percent threshold low volatility filter ATRP range value
- ATR multiplier range 1.5 to 3 stop loss scalping
- ATR percent of price volatility threshold screen（fidelity・stockcharts・schwab・tradingview に絞った）
- NATR normalized ATR percent threshold minimum volatility filter crypto 0.5% 1%

| # | 逐語 | 範囲の形 | 下の端 | 上の端 | 閾値の形 | 単位 | 話の相手 | 時間足 | 出どころの質 | 注 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | The final scan clause excludes high-volatility stocks (those with average ATRP of more than 4% over the last year) from the results.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-true-range-percent-atrp | 値を挙げただけ | None | None | 値 | % | 一般 | over the last year | 定番の教育サイト（StockCharts ChartSchool の ATRP） | 検索の例の 4%。264番でも見つかった文。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 2 | A good ATR multiplier for stop losses typically ranges between 1.5x and 3.0x the current ATR value.<br>https://tradersagency.com/blog/atr-position-sizing-stop-loss-placement | 文に両端が在る | 1.5 | 3.0 | 倍率 | ATR の倍数 | 一般 | 時間足は書いてない | 証券会社の解説（Traders Agency） | 損切りの幅の倍率。ATR% の値の閾値ではない。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 3 | Aggressive Scalper 5 - 7 1.0x to 1.5x Exiting at the first sign of volatility reversal.<br>https://marketclutch.com/the-volatility-compass-optimizing-average-true-range-atr-settings-for-intraday-traders/ | 文に両端が在る | 1.0 | 1.5 | 倍率 | ATR の倍数 | スキャル | 時間足は書いてない | ブログ（marketclutch） | 表の1行（Trader Profile・ATR Period・Multiplier・Logic の欄）。損切りの幅の倍率。同じ表に「Conservative Trend Follower 20 - 22 2.5x to 3.0x」が在る。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 4 | Professional traders often switch to a higher multiplier (e.g., from 2x to 3x) in low-volatility environments to avoid being stopped out by random, low-volume "noise."<br>https://marketclutch.com/the-volatility-compass-optimizing-average-true-range-atr-settings-for-intraday-traders/ | 値を挙げただけ | None | None | 倍率 | ATR の倍数 | 一般 | 時間足は書いてない | ブログ（marketclutch） | 前提＝値動きの小さい場面。本文で照らした道具：curl（空白の数だけそろえた） |
| 5 | A common same day distance is 1.5 or 2 times the 5 minute ATR, placed beyond the swing that got you in.<br>https://therighttrader.com/learn/indicator-strategies/best-atr-settings | 値を挙げただけ | None | None | 倍率 | ATR の倍数 | 5分足 | 5 minute ATR | ブログ（The Right Trader） | 損切りの幅。264番でも見つかった文。本文で照らした道具：curlとChromium（空白の数だけそろえた） |

### 6. 基準線｜閾値の範囲（形＝値）（結果：値を挙げた文だけ在る）

使った検索の語：
- Kijun-sen distance percentage price far from kijun mean reversion threshold
- price distance from kijun sen percent overextended ichimoku（fidelity・stockcharts・schwab・tradingview・babypips・litefinance に絞った）
- price within percent of kijun sen bounce ichimoku grading 2%

| # | 逐語 | 範囲の形 | 下の端 | 上の端 | 閾値の形 | 単位 | 話の相手 | 時間足 | 出どころの質 | 注 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | The price within 2% of the Kijun can be used to evaluate potential bounces off of this line<br>https://ru.tradingview.com/script/5b7gDP18-Ichimoku-Signals-Table | 値を挙げただけ | None | None | 値 | % | 一般 | 時間足は書いてない | TradingView の公開スクリプト（Ichimoku Signals Table・ロシア語の画面） | 終値と基準線の離れが 2% の内か。文の終わりに句点が無い（ページのまま）。同じページの「Price ±2% Kijun – Shows if price is trading within 2% of the Kijun-sen」も同じ数。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 2 | The variable prox is set to 3, which represents the proximity threshold in percentage.<br>https://www.prorealcode.com/snippet/proximity-in-of-2-lines-kijun-ma20/ | 値を挙げただけ | None | None | 値 | % | 一般 | 時間足は書いてない | 掲示板のコードの断片（ProRealCode） | 基準線と 20本の移動平均の離れの %。終値と基準線の離れではない。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 3 | MaFilterPips 6 Minimum LWMA-to-Kijun distance in pips.<br>https://doc.stocksharp.com/en/api-examples/2527_Kijun_Sen_Robot | 値を挙げただけ | None | None | 値 | 値段 | 一般 | 時間足は書いてない | ライブラリの説明書（StockSharp の戦略の例・Kijun Sen Robot） | 単位が値段かドル（pips）。線形加重の移動平均と基準線の離れで、終値と基準線の離れではない。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 4 | When the price moves far away from this line, it is likely to return to this level.<br>https://www.litefinance.org/blog/for-beginners/best-technical-indicators/ichimoku-cloud-indicator-in-forex-explained/ | 書いてない | None | None | 値 | % | 一般 | 時間足は書いてない | 証券会社の解説（LiteFinance） | 数が書いてない。264番でも見つかった文。本文で照らした道具：curlとChromium（空白の数だけそろえた） |

### 7. DI差｜パラメータ n の範囲（結果：両端の文が在る）

使った検索の語：
- DMI period setting range 7 to 21 short-term traders directional movement index length
- DMI directional movement index period length shorter longer settings（fidelity・stockcharts・schwab・tradingview・babypips に絞った）

| # | 逐語 | 範囲の形 | 下の端 | 上の端 | 閾値の形 | 単位 | 話の相手 | 時間足 | 出どころの質 | 注 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Optimal Period for DMI: A shorter period, like 5 to 7 days, is more responsive to price movements.<br>https://www.brokercheck.co.za/?p=17435 | 文に両端が在る | 5 | 7 | 値 | 当てはまらない（パラメータの本数） | 一般 | days | ブログ（brokercheck.co.za） | DMI の期間。同じページに 10〜14 と 20〜30 の文が在る（下の2行）。本文で照らした道具：Chromium（空白の数だけそろえた） |
| 2 | Optimal Period for DMI: A moderate period, such as 10 to 14 days, balances responsiveness with reliability.<br>https://www.brokercheck.co.za/?p=17435 | 文に両端が在る | 10 | 14 | 値 | 当てはまらない（パラメータの本数） | 一般 | days | ブログ（brokercheck.co.za） | 本文で照らした道具：Chromium（空白の数だけそろえた） |
| 3 | Optimal Period for DMI: A longer period, like 20 to 30 days, reduces sensitivity to short-term price fluctuations.<br>https://www.brokercheck.co.za/?p=17435 | 文に両端が在る | 20 | 30 | 値 | 当てはまらない（パラメータの本数） | 一般 | days | ブログ（brokercheck.co.za） | 本文で照らした道具：Chromium（空白の数だけそろえた） |
| 4 | Shorter Periods (like 7-10): Using a shorter lookback makes the DMI much more sensitive to recent price swings.<br>https://chartswatcher.com/pages/blog/mastering-the-dmi-directional-movement-index | 文に両端が在る | 7 | 10 | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | ブログ（ChartsWatcher） | 同じページに「A longer period, like 21 or 28, smooths everything out」が在る（値を挙げただけ）。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 5 | A longer period, like 21 or 28, smooths everything out, giving you more reliable signals but getting you into trends a bit later.<br>https://chartswatcher.com/pages/blog/mastering-the-dmi-directional-movement-index | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | ブログ（ChartsWatcher） | 本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 6 | optInTimePeriod integer 14 1–100000 Wilder smoothing period<br>https://ta-lib.org/functions/plus_di.html | 入力できる範囲 | 1 | 100000 | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | ライブラリの説明書（TA-Lib の PLUS_DI） | 264番でも見つかった文。MINUS_DI の頁にも同じ行が在る。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 7 | Lower values (e.g., 7): more sensitive, more signals Higher values (e.g., 21): more stable, less noise<br>https://in.tradingview.com/script/FstitqUD/ | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | TradingView の公開スクリプト（Average Directional Index info） | ADX の平滑化の期間（Smoothing）の文。DI の長さ（Indicator Length）の既定は同じ行の後ろの 14。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 8 | Period 21 is the slower alternative when one day dominates the reading.<br>https://therighttrader.com/learn/indicator-strategies/best-adx-settings | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | ブログ（The Right Trader） | DI と ADX の期間の話（同じページの「set both to 14」）。同じページに「Dropping the period to 7 on daily crypto makes ADX shout on one wide day.」が在る。本文で照らした道具：curl（空白の数だけそろえた） |

### 8. 基準線｜パラメータ k の範囲（結果：値を挙げた文だけ在る）

使った検索の語：
- Ichimoku Kijun-sen period settings range crypto 20 30 60 scalping
- Ichimoku settings adjust kijun period 26 30 crypto shorter timeframe（fidelity・stockcharts・schwab・tradingview・babypips に絞った）
- Ichimoku kijun period optimization range tested crypto intraday 5 minute settings study

| # | 逐語 | 範囲の形 | 下の端 | 上の端 | 閾値の形 | 単位 | 話の相手 | 時間足 | 出どころの質 | 注 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ⏱️ 1 Minute (1m) Tenkan / Kijun / Span B: 5 / 15 / 45 Use: Scalping fast price action.<br>https://www.tradingview.com/script/LQpN9Nae-Ichimoku-Cloud-Auto-TF/ | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | スキャル・短い足 | 1 Minute (1m) | TradingView の公開スクリプト（Ichimoku Cloud Auto TF） | 基準線 15。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 2 | ⏱️ 5 Minutes (5m) Tenkan / Kijun / Span B: 8 / 24 / 72 Use: Intraday setups, quick trend capture.<br>https://www.tradingview.com/script/LQpN9Nae-Ichimoku-Cloud-Auto-TF/ | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 5分足 | 5 Minutes (5m) | TradingView の公開スクリプト（Ichimoku Cloud Auto TF） | 基準線 24。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 3 | ⏱️ 15 Minutes (15m) Tenkan / Kijun / Span B: 9 / 27 / 81 Use: Short-term swing and intraday entries with higher reliability.<br>https://www.tradingview.com/script/LQpN9Nae-Ichimoku-Cloud-Auto-TF/ | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 短い足 | 15 Minutes (15m) | TradingView の公開スクリプト（Ichimoku Cloud Auto TF） | 基準線 27。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 4 | Intraday (All Markets) 20 60 120 5-min, 15-min For faster timeframes, traders often double or triple the standard inputs to reduce noise.<br>https://chartswatcher.com/pages/blog/ichimoku-cloud-strategy-trading-secrets-that-actually-work | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 5分足・短い足 | 5-min, 15-min | ブログ（ChartsWatcher） | 表の1行。基準線の欄は 60。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 5 | Cryptocurrencies 10 30 60 6-Hour, Daily The 24/7 market often benefits from slightly longer periods to smooth out weekend volatility.<br>https://chartswatcher.com/pages/blog/ichimoku-cloud-strategy-trading-secrets-that-actually-work | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 一般 | 6-Hour, Daily | ブログ（ChartsWatcher） | 表の1行。基準線の欄は 30。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 6 | Crypto-Adjusted Settings: While the classic 9-26-52 settings remain the standard, many pros in 2026 utilize 10-30-60 to account for the 24/7 crypto market cycle.<br>https://www.kucoin.com/en-au/blog/ichimoku-cloud-for-next-bitcoin-cycle | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | 暗号資産の取引所の解説（KuCoin） | 10-30-60。どれが基準線の本数かは、この文には書いてない。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 7 | Crypto traders generally adjust this setting to 30 periods.<br>https://woox.io/blog/the-ultimate-guide-to-ichimoku-kinko-hyo | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | 暗号資産の取引所の解説（WOO X） | 直前の文「The Kijun-Sen and Chikou-Span used 26 periods to represent the business days in a given month.」を受けた文。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 8 | Many crypto traders, therefore, use (10, 30 and 60) instead of the original settings to reflect the 24/7 nature of crypto markets.<br>https://coinmarketcap.com/academy/article/what-is-the-ichimoku-cloud-and-how-to-use-it-in-crypto-trading | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | 暗号資産の解説（CoinMarketCap Academy） | どれが基準線の本数かは、この文には書いてない。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 9 | Base Line: 60 instead of 26.<br>https://fxopen.com/blog/en/what-is-the-ichimoku-cloud-and-how-can-it-be-used-in-crypto-trading | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | 証券会社の解説（FXOpen） | 暗号資産の設定として。直前に「To match up with crypto’s trading hours, many change the indicator periods from 9, 26, 52, and 26 to 20, 60, 120, and 30.」。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 10 | Of course, Ichimoku settings can be adjusted to suit a 5-day week at 7-22-44, then 9-30-60, or 12-24-120 for trending markets.<br>https://www.forex.in.rs/ichimoku-settings-7-22-44/ | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | ブログ（forex.in.rs） | 7-22-44・9-30-60・12-24-120。どれが基準線の本数かは、この文には書いてない。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 11 | FOR CRYPTO YOU'D BETTER USE: 10,30,30,60,30 OR 20,60,60,120,60 THE TRICKY THING IS THAT KEEPING THE 1-3-3-6-3 RATIO CONSTANT IS NECESSARY<br>https://www.tradingview.com/script/X4pwbIqa/ | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | TradingView の公開スクリプト（ICHIMOKU Kinko Hyo by KIVANC） | 5つの数の並び。同じ文の前の「DEAFULT LENGTHS (9,26,26,52,26)」から、2つ目が基準線と読める。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 12 | TENKAN: 11 - a week and a half KIJUN: 30 - one month SENKOU: 61 - two months<br>https://jp.tradingview.com/script/emYrxwRL | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | TradingView の公開スクリプト（Ichimoku Crypto Cloud 11-30-61・日本語の画面） | 基準線 30。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 13 | The default setting for the Base Line is 26 periods and can be adjusted.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/ichimoku-cloud | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | 定番の教育サイト（StockCharts ChartSchool） | 変えてよい、とだけ書く。本文で照らした道具：curlとChromium（空白の数だけそろえた） |
| 14 | For cryptocurrency markets, traders often adjust default settings (9/26/52) to crypto-optimized parameters like 10/30/60 or 20/60/120 to account for 24/7 trading.<br>https://www.binance.com/en/academy/articles/ichimoku-clouds-explained | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | 一般 | 時間足は書いてない | 暗号資産の取引所の解説（Binance Academy） | curl は応答の中身が空（202）、Chromium で開いた本文の文。本文で照らした道具：Chromium（空白の数だけそろえた） |
| 15 | Best settings. Classic: 9, 26, 52. Scalping: 5, 13, 26. Swing trading: 9, 26, 52.<br>https://www.litefinance.org/blog/for-beginners/best-technical-indicators/ichimoku-cloud-indicator-in-forex-explained/ | 値を挙げただけ | None | None | 値 | 当てはまらない（パラメータの本数） | スキャル | 時間足は書いてない | 証券会社の解説（LiteFinance） | 264番でも見つかった文。基準線は 13（スキャル）。本文で照らした道具：curlとChromium（空白の数だけそろえた） |

## 3. 開いたページ

### 1. RSI｜閾値の範囲（形＝値）

| URL | 当たる文 | 道具と結果 |
|---|---|---|
| https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/RSI | 在る | curl＝HTTP 200／Chromium＝HTTP 502（本文 23 文字） |
| https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 19847 文字） |
| https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/ | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 10370 文字） |
| https://www.tradingview.com/chart/BTCUSD/Mw0R8uur-RSI-MasterClass-Part-1-The-Overbought-Oversold-Trading-Strateg/ | 開けない | curl＝HTTP 404／Chromium＝HTTP 404（本文 1772 文字）／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://www.mql5.com/en/blogs/post/774746 | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 5484 文字） |
| https://www.investopedia.com/terms/r/rsi.asp | 在る | curl＝HTTP 402／Chromium＝HTTP 200（本文 20331 文字） |
| https://www.babypips.com/learn/forex/relative-strength-index | 開けない | curl＝HTTP 403／Chromium＝HTTP 403（本文 264 文字）／WebFetch も 403／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://www.tradingview.com/script/ImVAOTyf-Modern-RSI/ | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 21624 文字） |
| https://github.com/toobrien/rsi | 在る | curl＝HTTP 403／Chromium＝HTTP 200（本文 9276 文字） |
| https://stockbros.substack.com/p/does-the-relative-strength-index | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 9079 文字） |
| https://help.coinrule.com/articles/376756-rsi-top-scalper | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 4775 文字） |
| https://forums.babypips.com/t/rsi-scalping/35996 | 開けない | curl＝HTTP 403／Chromium＝HTTP 403（本文 267 文字）／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |

### 2. ADX｜閾値の範囲（形＝値）

| URL | 当たる文 | 道具と結果 |
|---|---|---|
| https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 19259 文字） |
| https://www.babypips.com/learn/forex/average-directional-index | 開けない | curl＝HTTP 403／Chromium＝HTTP 403（本文 264 文字）／WebFetch も 403／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://www.fidelity.com/viewpoints/active-investor/average-directional-index-ADX | 在る | curl＝HTTP 200／Chromium＝HTTP 502（本文 23 文字） |
| https://www.tradingview.com/support/solutions/43000589099-average-directional-index-adx/ | 在る | curl＝HTTP 応答なし／Chromium＝HTTP 200（本文 6540 文字） |
| https://in.tradingview.com/script/FstitqUD/ | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 4248 文字） |
| https://ungeracademy.com/blog/trading-with-adx-discover-the-levels-that-really-work-and-why | 開けない | curl＝HTTP 520／Chromium＝HTTP 520（本文 967 文字）／WebFetch は本文が空／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://www.investopedia.com/terms/a/adx.asp | 開けない | curl＝HTTP 402／Chromium＝HTTP 403（本文 0 文字）／過去のページの保存（web.archive.org）は、curl では接続が切れ、WebFetch では使えないと返った |
| https://crosstrade.io/learn/technical-indicators/adx | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 4080 文字） |
| https://br.tradingview.com/script/WkSTQiKr-ADX-w-15-and-30-Lines | 開けない | curl＝HTTP 404／Chromium＝HTTP 404（本文 2068 文字）／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://therighttrader.com/learn/indicator-strategies/best-adx-settings | 在る | curl＝HTTP 200／Chromium＝HTTP 503（本文 0 文字） |
| https://ungeracademy.com/?p=6948 | 開けない | curl＝HTTP 520／Chromium＝HTTP 520（本文 967 文字）／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://www.liberatedstocktrader.com/adx-indicator/ | 在る | curl＝HTTP 403／Chromium＝HTTP 200（本文 20317 文字） |
| https://landing-page-2ml.pages.dev/docs/indicators/adx/strategy-templates | 開けない | curl＝HTTP 404／Chromium＝HTTP 404（本文 140 文字）／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://www.prorealcode.com/topic/adx-compreso-tra-due-valori/ | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 2319 文字） |

### 3. DI差｜閾値の範囲（形＝値）

| URL | 当たる文 | 道具と結果 |
|---|---|---|
| https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 8433 文字） |
| https://doc.stocksharp.com/en/api-examples/1072_Monthly_Performance_Table | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 4390 文字） |
| https://doc.stocksharp.com/en/designer-gallery/Adx_Di_Crossover | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 3188 文字） |
| https://sites.google.com/view/indicatorsoftrades/adx-with-di-crossover-filter-rules | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 3778 文字） |
| https://www.tradingview.com/script/EEF5Zj7D/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 9162 文字） |
| https://in.tradingview.com/script/6uSfABUE-ADX-DI | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 3359 文字） |
| https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/dmi | 無い | curl＝HTTP 200／Chromium＝HTTP 502（本文 23 文字） |
| https://www.investopedia.com/terms/d/dmi.asp | 開けない | curl＝HTTP 402／Chromium＝HTTP 403（本文 0 文字）／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://deepvue.com/?p=12526 | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 6485 文字） |
| https://madbomber.github.io/sqa-tai/indicators/momentum/adx | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 25178 文字） |
| https://www.incrediblecharts.com/stock_screener/stock_screener_directional_movement.php | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 5664 文字） |
| https://www.incrediblecharts.com/stock_screener/screen-filters-to-identify-momentum-trends.php | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 3637 文字） |

### 4. BB%b｜閾値の範囲（形＝値）

| URL | 当たる文 | 道具と結果 |
|---|---|---|
| https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 9006 文字） |
| https://www.tradingview.com/support/solutions/43000501971-bollinger-bands-b-b/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 5670 文字） |
| https://fxreplay.com/indicators/bollinger-bands-b-25fa9 | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 5092 文字） |
| https://www.luxalgo.com/library/indicator/percent-b/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 7421 文字） |
| https://www.barchart.com/education/technical-indicators/bollinger_bands_percent | 無い | curl＝HTTP 202／Chromium＝HTTP 202（本文 13959 文字） |
| https://sentimentrader.com/education/technical-indicators/bollinger-b | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 7046 文字） |
| https://www.tradingview.com/script/yXkWPSlU/ | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 7267 文字） |
| https://www.bollingerbands.com/bollinger-band-rules | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 5572 文字） |
| https://www.investopedia.com/terms/p/percentb.asp | 開けない | curl＝HTTP 402／Chromium＝HTTP 404（本文 576 文字）／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://doc.stocksharp.com/en/api-examples/0968_Larry_Connors_Bollinger_PercentB | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 7970 文字） |
| https://doc.stocksharp.com/en/api-examples/0035_Bollinger_B_Reversion | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 6784 文字） |

### 5. ATR%｜閾値の範囲（形＝値か倍率）

| URL | 当たる文 | 道具と結果 |
|---|---|---|
| https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-true-range-percent-atrp | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 7453 文字） |
| https://in.tradingview.com/scripts/atrpercentage/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 5655 文字） |
| https://www.tradingview.com/script/6aZViQvI-Volatility-Regime-Classifier-ATRP-Percentile-Zones/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 4011 文字） |
| https://www.tradingview.com/script/IoGZmM1D-ATR-Volatility-Regime/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 6782 文字） |
| https://www.luxalgo.com/blog/how-to-use-atr-for-volatility-based-stop-losses/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 13386 文字） |
| https://tradersagency.com/blog/atr-position-sizing-stop-loss-placement | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 19875 文字） |
| https://therighttrader.com/learn/indicator-strategies/best-atr-settings | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 13443 文字） |
| https://www.tradingview.com/support/solutions/43000501823-average-true-range-atr/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 7130 文字） |
| https://marketclutch.com/the-volatility-compass-optimizing-average-true-range-atr-settings-for-intraday-traders/ | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 10281 文字） |
| https://therighttrader.com/learn/indicators/normalized-atr | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 13889 文字） |
| https://www.macroption.com/normalized-atr | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 6260 文字） |
| https://docs.skyrexio.com/strategy-builder/built-in-conditions/volatility-indicators/normalized-average-true-range-14 | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 12707 文字） |
| https://www.tradingview.com/script/358ZxT4e-NATR-Normalized-ATR-Oscillator/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 4750 文字） |
| https://ta-lib.org/functions/natr.html | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 1974 文字） |

### 6. 基準線｜閾値の範囲（形＝値）

| URL | 当たる文 | 道具と結果 |
|---|---|---|
| https://www.tradingview.com/script/PqxNdJrc/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 6852 文字） |
| https://www.luxalgo.com/library/indicator/qLUm6JRg-kijun-bands/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 11475 文字） |
| https://www.prorealcode.com/snippet/proximity-in-of-2-lines-kijun-ma20/ | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 4157 文字） |
| https://doc.stocksharp.com/en/api-examples/2527_Kijun_Sen_Robot | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 23863 文字） |
| https://www.litefinance.org/blog/for-beginners/best-technical-indicators/ichimoku-cloud-indicator-in-forex-explained/ | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 25315 文字） |
| https://in.tradingview.com/scripts/kijun-sen/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 8517 文字） |
| https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/ichimoku-cloud | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 18747 文字） |
| https://ru.tradingview.com/script/5b7gDP18-Ichimoku-Signals-Table | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 4084 文字） |
| https://articles.stockcharts.com/article/stockcharts-insider-a-practical-guide-to-the-ichimoku-kijun-sen-pullback/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 9228 文字） |
| https://www.tradingview.com/script/9FGkF2Pq-Ichimoku-With-Grading/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 6212 文字） |

### 7. DI差｜パラメータ n の範囲

| URL | 当たる文 | 道具と結果 |
|---|---|---|
| https://chartswatcher.com/pages/blog/mastering-the-dmi-directional-movement-index | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 25897 文字） |
| https://trendspider.com/learning-center/a-comprehensive-guide-to-the-directional-movement-index-dmi-for-traders/ | 開けない | curl＝HTTP 応答なし／Chromium＝HTTP 502（本文 23 文字）／WebFetch は本文が空／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://tabtrader.com/helpcenter/ios/technical-analysis-and-indicators/dmi | 開けない | curl＝HTTP 応答なし／Chromium＝error: page.goto: net::ERR_TUNNEL_CONNECTION_FAILED at https://tabtrader.com/helpcenter（本文 0 文字）／WebFetch はこのセッションで名前を引けない（ENOTFOUND）／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://tradersunion.com/interesting-articles/forex-indicators-for-traders/dmi-indicator | 無い | curl＝HTTP 403／Chromium＝HTTP 403（本文 22121 文字） |
| https://www.brokercheck.co.za/?p=17435 | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 20069 文字） |
| https://ta-lib.org/functions/plus_di.html | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 2103 文字） |
| https://ta-lib.org/functions/minus_di.html | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 2095 文字） |
| https://www.babypips.com/learn/forex/average-directional-index | 開けない | curl＝HTTP 403／Chromium＝HTTP 403（本文 264 文字）／WebFetch も 403／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/dmi | 無い | curl＝HTTP 200／Chromium＝HTTP 502（本文 23 文字） |
| https://therighttrader.com/learn/indicator-strategies/best-adx-settings | 在る | curl＝HTTP 200／Chromium＝HTTP 503（本文 0 文字） |

### 8. 基準線｜パラメータ k の範囲

| URL | 当たる文 | 道具と結果 |
|---|---|---|
| https://www.kucoin.com/en-au/blog/ichimoku-cloud-for-next-bitcoin-cycle | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 15106 文字） |
| https://www.forex.in.rs/ichimoku-settings-7-22-44/ | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 11026 文字） |
| https://woox.io/blog/the-ultimate-guide-to-ichimoku-kinko-hyo | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 10127 文字） |
| https://tabtrader.com/academy/articles/what-is-ichimoku-cloud-trading-strategy | 開けない | curl＝HTTP 応答なし／Chromium＝error: page.goto: net::ERR_TUNNEL_CONNECTION_FAILED at https://tabtrader.com/academy/ar（本文 0 文字）／WebFetch はこのセッションで名前を引けない（ENOTFOUND）／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://www.coinex.com/en/academy/detail/2464-what-is-ichimoku-cloud-in-crypto-trading | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 349 文字） |
| https://coinmarketcap.com/academy/article/what-is-the-ichimoku-cloud-and-how-to-use-it-in-crypto-trading | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 8638 文字） |
| https://www.tradingview.com/script/X4pwbIqa/ | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 4286 文字） |
| https://www.tradingview.com/script/LQpN9Nae-Ichimoku-Cloud-Auto-TF/ | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 4476 文字） |
| https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/ichimoku-cloud | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 18747 文字） |
| https://www.tradingview.com/support/solutions/43000589152-ichimoku-cloud/ | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 6760 文字） |
| https://gunthy.gitbook.io/wiki/trading-strategy-options/margin-trading-strategies/ichimoku | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 103 文字） |
| https://my.tradingview.com/script/cGaJjq2f-Ichimoku-Kijun-OPTIMISED-FOR-15MIN-EURUSD | 開けない | curl＝HTTP 404／Chromium＝HTTP 404（本文 1895 文字）／過去のページの保存（web.archive.org）は、このセッションでは接続が切れて開けない |
| https://www.binance.com/en/academy/articles/ichimoku-clouds-explained | 在る | curl＝HTTP 202／Chromium＝HTTP 202（本文 14090 文字） |
| https://therighttrader.com/learn/indicator-strategies/best-ichimoku-settings | 無い | curl＝HTTP 200／Chromium＝HTTP 200（本文 13513 文字） |
| https://chartswatcher.com/pages/blog/ichimoku-cloud-strategy-trading-secrets-that-actually-work | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 28507 文字） |
| https://fxopen.com/blog/en/what-is-the-ichimoku-cloud-and-how-can-it-be-used-in-crypto-trading | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 15970 文字） |
| https://jp.tradingview.com/script/emYrxwRL | 在る | curl＝HTTP 200／Chromium＝HTTP 200（本文 1732 文字） |

開いたページは、件ごとに数えて 100 本（同じ URL を除くと 96 本）です。開けなかったページは、件ごとに 16 本（同じ URL を除くと 15 本）です。

## 4. 確かめられなかった物と、その理由

- 開けなかったページ（curl と Chromium の両方）は3章の「開けない」の行です。理由は、404（ページが無い）、403（ロボットを止める確かめの画面）、402（Investopedia）、520（ungeracademy の側の不具合）、tabtrader.com はこのセッションの道筋で名前を引けない、の5つです。
- babypips.com の2本は WebFetch でも 403 でした。trendspider.com と ungeracademy.com は、WebFetch では本文が空でした。tabtrader.com は、WebFetch もこのセッションでは名前を引けませんでした（このセッションの通信の設定で許されていない場所の可能性があります）。
- 過去のページの保存（web.archive.org）は、curl では接続が10秒ほどで切られ（プロキシの記録で確かめた）、WebFetch は「このサイトからは取れない」と返しました。開けなかったページの過去の版は、確かめられていません。
- ungeracademy.com の記事（ADX の閾値を 10〜100 で最適化した、と検索の要約に出た）は、本文を開けていません。検索の要約だけでは書かない決まりなので、文に載せていません。
- Wilder の本（RSI・ADX・DMI・ATR）と細田悟一の一目均衡表の本は、Web に本文が無く、読んでいません。
- Chromium の本文は、ページを開いてから最大10秒ほど待って読みました。それより後に文を出すページは、見ていない可能性があります。
- 文の分け方（範囲の形・話の相手）は、私が文の意味を読んで決めました。決め方の根拠は各行の注に書きました。

## 5. 始めた時刻と終えた時刻

- 始めた時刻：2026-11-04 10:38:27 UTC（date -u）
- 終えた時刻：2026-11-04 11:06:06 UTC（date -u）
