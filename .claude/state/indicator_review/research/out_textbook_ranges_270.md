# 閾値の範囲とパラメータの範囲を教科書で探した結果（ToDo 270番＝222番の材料）

この文書は `out_textbook_ranges_270.json` を、人が読む形にまとめた物です。値を決めていません。範囲を作っていません。文から1つを選んでいません。データ・プログラム・文書は直していません。

- ページは、curl と Chromium（この環境に入っている、Chrome と同じ中身のブラウザ）の両方で開きました。逐語は、開いた本文から切り出し、空白の数だけをそろえて照らしました。
- 両方で開けなかったページは、WebFetch でも試しました。過去のページの保存（web.archive.org）は、このセッションでは接続が切られ、開けませんでした（下の4章）。
- 新しいページの検索は、全部の件で行いました（WebSearch を21回。Investopedia は検索の道具が受け付けなかったので、Investopedia を外して検索し直した）。

## 1. 8件の結果

| 番号 | 指標 | 探す物 | 結果 | 文に両端が在る文の数 | 文の数 | 開いたページの数 | 両端の文が何の両端か |
|---|---|---|---|---|---|---|---|
| 1 | RSI | 閾値の範囲（形＝値） | 両端の文が在る | 1 | 11 | 12 | Cardwell の弱気の反転の形で RSI が来る所（50-70）。閾値を探す幅とは書いてない |

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

開いたページは、件ごとに数えて 12 本（同じ URL を除くと 12 本）です。開けなかったページは、件ごとに 3 本（同じ URL を除くと 3 本）です。

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
- 終えた時刻：（終えたときに書く）
