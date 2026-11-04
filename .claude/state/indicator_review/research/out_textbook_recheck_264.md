# 9種の教科書の調べの確かめ直しと、入れる値の候補の表（ToDo 264番＝222番の材料）

この文書は `out_textbook_recheck_264.json` を、人が読む形にまとめた物です。値は決めていません。候補から1つを選んでいません。データ・プログラム・調べの結果のファイルは直していません。

- 指標データ＝`refactor/e35-e36-split-strat-base` の `455f540` の `SDK/scripts/priority_rebuild/indicators/indicators.json`（前の照らしが使った `83b392f` と、このファイルの差は無い＝`git diff` で確かめた）。
- 前の照らしの結果＝`research/textbook-compare-222` の `e3cd00a`。9種の文書＝`research/textbook-9-kinds` の `826334b`。全指標の調べ＝`research/textbook-all-6` の `54a075c` と `research/textbook-all-5` の `3d0f9b2`。
- 先に通す条件＝レンジ・スキャル・ショート・BTC・売買の足は5分足。デイトレの値とロングの行は、候補に入れていない。
- ページを開いた道具＝curl（54本の URL。HTTP の番号は行ごとに書いた）。HTML から本文の文字を取り出し、逐語と照らした。照らすとき、空白の数と句読点の前の空白だけをそろえた。そろえ方を広げた行（引用符・ダッシュ・大文字小文字）は、行の注に書いた。
- WebFetch は使っていない。理由＝54本とも curl で開けた（依頼書の「WebFetch で開けないときは、curl でも試す」の、開けない場合に当たらなかった）。WebFetch は本文を要約して返すので、1文字ずつの照らしに使えないため、curl の本文で照らした。

## 1. 確かめ直しの結果ごとの件数と、調べの結果の誤りと分かった物

確かめ直した行は **32 件**です（依頼書の 27＋5＝32 件と同じ）。

| 結果 | 逐語と値が合わない | 調べの結果どうしの違い | 合計 |
|---|---|---|---|
| ページに在る | 26 | 5 | 31 |
| ページに無い | 1 | 0 | 1 |
| 開けない | 0 | 0 | 0 |
| 合計 | 27 | 5 | 32 |

### 調べの結果の誤りと分かった物（ページの本文で確かめた分だけ）

| # | 調べの結果のファイルと場所 | 誤りの中身 | ページの本文で分かったこと |
|---|---|---|---|
| 1 | 全指標の調べ out_c6_08.json の 基準線 の 教科書の役割.0 | 基準線の行の値「向き」の逐語が、転換線（Tenkan Sen）の文 | Wikipedia の本文で、この文は Tenkan-sen の節に在る |
| 2 | 全指標の調べ out_c6_08.json の 基準線 の 教科書の役割.1 | 基準線の行の値「勢い」の逐語が、転換線（Tenkan-sen）の文 | LiteFinance の本文で、この文は Tenkan-sen の説明の文 |
| 3 | 全指標の調べ out_c6_08.json の 基準線 の 教科書の役割.2 | 基準線の行の値「位置」の逐語が、転換線（conversion line）の文 | Wikipedia の本文で、この文は Tenkan-sen の節に在る |
| 4 | 全指標の調べ out_c6_08.json の 基準線 の 値の読み方.0 | 基準線の行の読み方の逐語が、転換線（blue line）の文 | Wikipedia の本文で、この文は Tenkan-sen の節に在る |
| 5 | 全指標の調べ out_c6_08.json の 基準線 の 値の単位と値域.0 | 基準線の行の値域の逐語が、転換線の計算の文 | Wikipedia の本文で、この文は Tenkan-sen の節に在る（基準線は次の Kijun-sen の節） |
| 6 | 全指標の調べ out_c6_08.json の 基準線 の 計算の式 | 基準線の行の式の逐語が、TenkanSen（転換線）の式 | Fidelity の本文で、基準線の式は次の行「KijunSen (Base Line): (High + Low) / 2 default period = 26」 |
| 7 | 全指標の調べ out_c6_08.json の 基準線 の パラメータの軸.1.既定.0 | 軸 t_ の既定 9 の逐語は、転換線の既定。指標データの基準線の軸は k_ | Fidelity の本文で、9 は TenkanSen の行の値 |
| 8 | 全指標の調べ out_c6_01.json の DI差 の 値の単位と値域.1 | DI差の値域 0〜100 の逐語が、DMI 全体の文 | TradingView の本文で、文は DMI を名指しし、+DI と -DI は向きを測ると次の文に書く。DI差の値域はページに無い |
| 9 | 全指標の調べ out_c6_01.json の BB%b の 値の単位と値域.1 | 値の下限 0・上限 1 の逐語が「between .50 and 1」の文 | StockCharts の本文で、同じ並びに 0 より下と 1 より上の文が在る |
| 10 | 全指標の調べ out_c6_01.json の BB幅 の パラメータの軸.0.既定.5 | 値 [5, 2.0] の逐語に 2.0 が無い | pandas_ta の bbands.py で、2.0 は次の行（lower_std・upper_std の Default）に在る |
| 11 | 全指標の調べ out_c6_01.json の ATR% の パラメータの軸.0.範囲.0 | 値 5〜21 を範囲として書いたが、逐語は値を挙げた文 | marketclutch の本文で、文は「5 or 7-period」と「20 or 21-period」を挙げる |
| 12 | 全指標の調べ out_c6_02.json の RSI の パラメータの軸.0.デイトレ.0 | 逐語と同じ文がページに無い（確かめの強さは「ページの文で確かめた」） | bullynx の本文は「... leave in place: 14 bars cover three and a half hours, roughly half a stock session.」で、文が「:」の後に続く |
| 13 | 全指標の調べ out_c6_02.json の RSI の パラメータの軸.0.スキャル.0・スキャル.1・デイトレ.0・デイトレ.1・デイトレ.2・範囲.2（6件） | 時間足の欄が「書いてない」だが、逐語に足が書いてある | 本文の文に 1-minute chart・5-minute chart・15-minute chart・1-hour・intraday charts・daily が在る |
| 14 | 全指標の調べ out_c6_01.json の BB幅 の スキャル.1、BB%b の スキャル.0・スキャル.1、ATR% の スキャル.0・スキャル.1・デイトレ.0（6件） | 時間足の欄が「書いてない」だが、逐語に足が書いてある | 本文の文に 1-minute or 5-minute charts・1-minute chart・1 minute・5-minute charts・15-minute to 1-hour timeframes が在る |
| 15 | 全指標の調べ out_c6_08.json の 基準線 の パラメータの軸.0.既定.0 | 時間足の欄が「書いてない」だが、逐語に足が書いてある | 本文の文に daily chart が在る |
| 16 | 全指標の調べ out_c6_07.json の 前期間pivotR1 の パラメータの軸.0.スキャル.0・スキャル.1・デイトレ.1（3件） | 時間足の欄が「書いてない」だが、逐語に足が書いてある | 本文の文に 1-, 5-, 10-, and 15-minute charts・up to and including 15 min・30-, 60-, and 120-minute charts が在る |
| 17 | 9種の文書 7 Q3（440行目） | LF-ICHI の今のページには「day trading」の語が無い、と書く | 今日のページには「Is the Ichimoku 15-minute strategy good for day trading?」の文が在る（本文に day trading が2か所）。9種の文書が読んだ日のページは、今日は確かめられない |

### 今日のページでは当たらない書き込み（誤りかは分からない物）

- 9種の文書 6 Q3（387行目）の「marketclutch.com は URL を開くと 404」＝今日は HTTP 200 で開け、全指標の調べの逐語は本文に在った。9種の文書が開いた日に 404 だったかは、今日は確かめられない。
- 9種の文書の「いまの値と違う所」の BB幅・BB%b（613行目）の「litefinance.org の Bollinger の記事は、今回開くと 404」＝今日は HTTP 200 で開け、全指標の調べの逐語は本文に在った。9種の文書が開いた日に 404 だったかは、今日は確かめられない。

### 確かめ直しの全行

| # | 元の一覧 | 指標 | 欄 | 結果 | ページの本文から分かったこと（注の頭） | URL |
|---|---|---|---|---|---|---|
| 1 | 逐語と値が合わない | 基準線 | 教科書の役割（向き） | ページに在る | 転換線の文：「The Tenkan Sen is an indicator of the market trend.」（Tenkan Sen＝転換線を名指し）。基準線の文：同じページの Kijun-sen の節に在る（足した逐語）。足は書いてない | https://en.wikipedia.org/wiki/Ichimoku_Kink%C5%8D_Hy%C5%8D |
| 2 | 逐語と値が合わない | 基準線 | 教科書の役割（勢い） | ページに在る | 転換線の文：「The Tenkan-sen mainly shows short-term bullish or bearish momentum.」（Tenkan-sen＝転換線を名指し）。基準線の文：同じページの Kijun Sen (Base Line) の節に在る（足した逐語）。足は書いてない | https://www.litefinance.org/blog/for-beginners/best-technical-indicators/ichimoku-cloud-indicator-in-forex-explained/ |
| 3 | 逐語と値が合わない | 基準線 | 教科書の役割（位置） | ページに在る | 転換線の文：「Also called the conversion line (blue line), it is primarily used as a signal line and a minor support/resistance line.」（Tenkan-sen の節の文。conversion line＝転換線）。基準線の文：Kijun-sen の節の「a confirmation line, a support/resistance line」（足した逐語）。足は書いてない | https://en.wikipedia.org/wiki/Ichimoku_Kink%C5%8D_Hy%C5%8D |
| 4 | 逐語と値が合わない | 基準線 | 値の読み方 | ページに在る | 転換線の文：「If the blue line is moving up or down, it indicates that the market is trending. If it moves horizontally, it signals that the market is ranging.」（Tenkan-sen の節の文。直前の文は「The Tenkan Sen is an indicator of the market trend.」）。基準線の文：Kijun-sen の節にも「blue line」の語が在る（「If the price is higher than the blue line, it could continue to climb higher.」）。足は書いてない | https://en.wikipedia.org/wiki/Ichimoku_Kink%C5%8D_Hy%C5%8D |
| 5 | 逐語と値が合わない | 基準線 | 値の単位と値域 | ページに在る | 転換線の文：「Tenkan-sen (転換線) calculation: (highest high + lowest low)/2 for the last 9 periods.」（9本の高値と安値の中点）。基準線の文：「Kijun-sen (基準線) calculation: (highest high + lowest low)/2 for the past 26 periods.」（26本）。どちらも値段の単位の線だが、単位の語はページに書いてない | https://en.wikipedia.org/wiki/Ichimoku_Kink%C5%8D_Hy%C5%8D |
| 6 | 逐語と値が合わない | 基準線 | 計算の式 | ページに在る | 転換線の文：「TenkanSen (Conversion Line): (High + Low) / 2 default period = 9」。基準線の文：同じ並びの次の行「KijunSen (Base Line): (High + Low) / 2 default period = 26」（足した逐語） | https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/ichimoku-cloud |
| 7 | 逐語と値が合わない | 基準線 | パラメータの軸 t_ の既定 | ページに在る | 転換線の文：「TenkanSen (Conversion Line): (High + Low) / 2 default period = 9」＝転換線の既定 9。基準線の文：「KijunSen (Base Line): (High + Low) / 2 default period = 26」＝基準線の既定 26（足した逐語） | https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/ichimoku-cloud |
| 8 | 逐語と値が合わない | DI差 | 値の単位と値域 | ページに在る | 文は DMI（指標の組全体）を名指しし「value between 0 and 100」と書く。次の文は「+DI and -DI are then used to measure direction.」。DI差（+DI と −DI の差）の値域は、このページに書いてない | https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ |
| 9 | 逐語と値が合わない | BB%b | 値の単位と値域 | ページに在る | 文は「%B is between .50 and 1 when price is between the upper and middle band (20-day SMA)」で、6つの水準の1つ。同じ並びに「%B is below 0 when price is below the lower band」「%B is above 1 when price is above the upper band」が在る＝ページは 0 より下と 1 より上の値も書いている。下限 0・上限 1 を値域として書いた文は、このページに無い | https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator |
| 10 | 逐語と値が合わない | BB幅 | パラメータの軸の既定（pandas_ta） | ページに在る | 逐語の行は「length (int): The period. Default: ```5```」で、length の既定 5 だけを書く。2.0 は同じファイルの次の行「lower_std (IntFloat): Lower standard deviation. Default: ```2.0```」と「upper_std (IntFloat): Upper standard deviation. Default: ```2.0```」に在る（逐語の行には無い） | https://files.pythonhosted.org/packages/be/2f/c67d49afd31c3b02a02ecb5dd07399ed35298042e1b50d166efe2068bb0e/pandas_ta-0.4.71b0-py3-none-any.whl#pandas_ta/volatility/bbands.py |
| 11 | 逐語と値が合わない | ATR% | パラメータの軸の範囲 | ページに在る | 文は「5 or 7-period」（スキャル）と「20 or 21-period」（trend traders）を挙げる。範囲の両端を1つの文で書いた形ではない（値を挙げただけ）。足は書いてない（同じページの別の文「Scalpers operate on the shortest timeframes, such as the 1-minute or 5-minute charts.」は足を書く） | https://marketclutch.com/the-volatility-compass-optimizing-average-true-range-atr-settings-for-intraday-traders/ |
| 12 | 逐語と値が合わない | RSI | 時間足（パラメータの軸.0.スキャル.0） | ページに在る | 足：「1-minute chart」（1分足）。指標：RSI 2 か 3 | https://www.mc2.fi/blog/best-rsi-for-scalping |
| 13 | 逐語と値が合わない | RSI | 時間足（パラメータの軸.0.スキャル.1） | ページに在る | 足：「5-minute chart」（5分足）。指標：RSI の期間 7〜9、または 14 のまま帯を 80/20 | https://bullynx.com/blog/best-rsi-settings |
| 14 | 逐語と値が合わない | RSI | 時間足（パラメータの軸.0.デイトレ.0） | ページに無い | 逐語と同じ文はページに無い。ページの文は「On a 15-minute chart the 14-period default holds up well and is what most platforms leave in place: 14 bars cover three and a half hours, roughly half a stock session.」で、逐語の末尾の「.」がページでは「:」で、その後に文が続く。足：「15-minute chart」（15分足）。指標：RSI 14。同じページの問いと答えの節にも「The 14-period default holds up well on a 15-minute chart, which is why most platforms leave it there.」が在る | https://bullynx.com/blog/best-rsi-settings |
| 15 | 逐語と値が合わない | RSI | 時間足（パラメータの軸.0.デイトレ.1） | ページに在る | 足：「15-minute charts」（15分足）と「1-hour」（1時間足）。指標：15分足は RSI 9 と 75/25、1時間足は RSI 14 と 70/30 | https://wundertrading.com/journal/en/rsi-vs-stochastic-rsi-crypto-trading |
| 16 | 逐語と値が合わない | RSI | 時間足（パラメータの軸.0.デイトレ.2） | ページに在る | 足：「15‑minute charts」（15分足）。指標：RSI 14 と 70/30 | https://eplanetbrokers.com/training/best-rsi-settings-for-15-minute-chart/ |
| 17 | 逐語と値が合わない | RSI | 時間足（パラメータの軸.0.範囲.2） | ページに在る | 足：「intraday charts」（日中の足）と「the daily」（日足）。指標：デイトレは 7〜9、スイングは 14 か 21 | https://bullynx.com/blog/best-rsi-settings |
| 18 | 逐語と値が合わない | BB幅 | 時間足（パラメータの軸.0.スキャル.1） | ページに在る | 足：「1-minute or 5-minute charts」（1分足・5分足）。指標：ボリンジャーバンドの SMA 10〜14 と標準偏差 1.5〜2（BB幅 を名指しはしていない） | https://blog.opofinance.com/en/bollinger-bands-scalping-secrets/ |
| 19 | 逐語と値が合わない | BB%b | 時間足（パラメータの軸.0.スキャル.0） | ページに在る | 足：「1-minute chart」（1分足）。指標：ボリンジャーバンドの 20 本の SMA と標準偏差 2（%B を名指しはしていない） | https://fxopen.com/blog/en/1-minute-scalping-trading-strategies-with-examples/ |
| 20 | 逐語と値が合わない | BB%b | 時間足（パラメータの軸.0.スキャル.1） | ページに在る | 足：「1 minute」（1分足）。指標：Bollinger Bands (20, 2)（%B を名指しはしていない） | https://www.mc2.fi/blog/best-rsi-for-scalping |
| 21 | 逐語と値が合わない | ATR% | 時間足（パラメータの軸.0.スキャル.0） | ページに在る | 足：「1-minute or 5-minute charts」（1分足・5分足）。指標：ATR の設定 5〜7（見出し「Optimization for Scalpers: Settings 5 to 7」） | https://marketclutch.com/the-volatility-compass-optimizing-average-true-range-atr-settings-for-intraday-traders/ |
| 22 | 逐語と値が合わない | ATR% | 時間足（パラメータの軸.0.スキャル.1） | ページに在る | 足：「5-minute charts」（5分足）。指標：ATR の期間 7（見出し「Standard Scalp (Period 7)」） | https://marketclutch.com/the-volatility-compass-optimizing-average-true-range-atr-settings-for-intraday-traders/ |
| 23 | 逐語と値が合わない | ATR% | 時間足（パラメータの軸.0.デイトレ.0） | ページに在る | 足：「15-minute to 1-hour timeframes」（15分足〜1時間足）。指標：ATR 14 | https://marketclutch.com/the-volatility-compass-optimizing-average-true-range-atr-settings-for-intraday-traders/ |
| 24 | 逐語と値が合わない | 基準線 | 時間足（パラメータの軸.0.既定.0） | ページに在る | 足：「daily chart」（日足）。指標：基準線（Base Line）の既定 26。この文は基準線そのものの文 | https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/ichimoku-cloud |
| 25 | 逐語と値が合わない | 帯pivot | 時間足（前期間pivotR1 と前期間pivotS1 のパラメータの軸.0.スキャル.0） | ページに在る | 足：「1-, 5-, 10-, and 15-minute charts」（1分足・5分足・10分足・15分足）。指標：Pivot Points は前の日の高値・安値・終値を使う | https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/pivot-points |
| 26 | 逐語と値が合わない | 帯pivot | 時間足（前期間pivotR1 と前期間pivotS1 のパラメータの軸.0.スキャル.1） | ページに在る | 足：「chart resolutions up to and including 15 min」（15分足まで）。指標：Pivot Points の「Auto」の設定は 1D（日）の pivot を使う | https://www.tradingview.com/support/solutions/43000521824-pivot-points-standard/ |
| 27 | 逐語と値が合わない | 帯pivot | 時間足（前期間pivotR1 と前期間pivotS1 のパラメータの軸.0.デイトレ.1） | ページに在る | 足：「30-, 60-, and 120-minute charts」（30分足・60分足・120分足）。指標：Pivot Points は前の週の高値・安値・終値を使う | https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/pivot-points |
| 28 | 調べの結果どうしの違い | ATR% | n の範囲・n のスキャルの値（marketclutch のページ） | ページに在る | 今日は HTTP 200 で開け、ページの題は「The Volatility Compass: Optimizing Average True Range (ATR) Settings for Intraday Traders」。9種の文書の「404 で開けない」は、今日は当たらない（9種の文書が開いた日の様子は、今日は確かめられない）。全指標の調べの逐語3つ（範囲・スキャル 5〜7・スキャル 7）は、今日の本文に在る。デイトレの値の文は照らしたが、候補には入れない | https://marketclutch.com/the-volatility-compass-optimizing-average-true-range-atr-settings-for-intraday-traders/ |
| 29 | 調べの結果どうしの違い | BB幅 | n と s のスキャルの値（litefinance.org の Bollinger の記事） | ページに在る | 今日は HTTP 200 で開け、ページの題は「Bollinger Bands Explained: Settings and Trading Strategies \| LiteFinance」。9種の文書の「今回開くと 404」は、今日は当たらない。全指標の調べの逐語2つは、今日の本文に在る。スキャルの文は「short time frames」と書き、足の名前は書いてない。指標はボリンジャーバンド（BB幅 を名指ししてはいない） | https://www.litefinance.org/blog/for-beginners/best-technical-indicators/bollinger-bands/ |
| 30 | 調べの結果どうしの違い | BB%b | n と s のスキャルの値 | ページに在る | 全指標の調べの逐語2つは、どちらも本文に在る（fxopen と MC2）。2つの文はボリンジャーバンドを名指しし、%B（%b）の語はどちらのページの本文にも無い（本文の中の「%B」「%b」を探して0件）。足は2つとも1分足。9種の文書の「%B を名指しした 5分足・スキャルの値は見つからなかった」と、全指標の調べの「スキャル [20, 2]」は、名指しする物（%B かボリンジャーバンドか）が違う | https://fxopen.com/blog/en/1-minute-scalping-trading-strategies-with-examples/ / https://www.mc2.fi/blog/best-rsi-for-scalping |
| 31 | 調べの結果どうしの違い | 基準線 | デイトレの値（LF-ICHI の (5, 13, 26)） | ページに在る | 今日のページには、両方の文が在る。①問いと答えの節に「good for day trading?」の文（5, 13, 26 を day trading に）②設定の並び「Scalping: 5, 13, 26」と、Scalping の節の「best suited to 15-minute or even 5-minute charts」。9種の文書の「今のページには day trading の語が無い」は、今日のページには当たらない（本文に「day trading」が2か所）。デイトレの値は候補に入れない。Scalping の文は、基準線の候補（スキャル）として載せる | https://www.litefinance.org/blog/for-beginners/best-technical-indicators/ichimoku-cloud-indicator-in-forex-explained/ |
| 32 | 調べの結果どうしの違い | DI差 | n の範囲 | ページに在る | 逐語は本文の表の1行（Parameter・Type・Default・Accepted values・Description の欄）。1–100000 は「Accepted values」（入力として受ける値）の欄の値。9種の文書の「DI の期間だけのスキャル・デイトレ・範囲は見つからなかった」は、勧める値の話。全指標の調べも注に「入力できる範囲。勧める範囲ではない」と書く。2つは、指す物が違う | https://ta-lib.org/functions/plus_di.html |

逐語・ページの本文から写した文・足した逐語・開いた道具と結果は、JSON の「確かめ直し」の各行に在ります。

## 2. 調べの結果どうしの違い5件の、確かめ直した結果

### ATR%｜n の範囲・n のスキャルの値（marketclutch のページ）

- 結果：ページに在る（https://marketclutch.com/the-volatility-compass-optimizing-average-true-range-atr-settings-for-intraday-traders/）
- 分かったこと：今日は HTTP 200 で開け、ページの題は「The Volatility Compass: Optimizing Average True Range (ATR) Settings for Intraday Traders」。9種の文書の「404 で開けない」は、今日は当たらない（9種の文書が開いた日の様子は、今日は確かめられない）。全指標の調べの逐語3つ（範囲・スキャル 5〜7・スキャル 7）は、今日の本文に在る。デイトレの値の文は照らしたが、候補には入れない
- 前の照らしの書き込み：9種の文書＝範囲 5〜21：資料の表の出どころ（marketclutch.com）は「✗ 見つからなかった（URL を開くと 404。確かめ直せなかった）」（6 Q3・387行目）／全指標の調べ＝同じ marketclutch.com のページを「ページの文で確かめた」とし、範囲「5〜21（スキャル 5・7／トレンド狙い 20・21）」、スキャル [5, 7]・[7]、デイトレ [14]・[20, 22] を逐語つきで書く（out_c6_01.json の ATR% のパラメータの軸）

### BB幅｜n と s のスキャルの値（litefinance.org の Bollinger の記事）

- 結果：ページに在る（https://www.litefinance.org/blog/for-beginners/best-technical-indicators/bollinger-bands/）
- 分かったこと：今日は HTTP 200 で開け、ページの題は「Bollinger Bands Explained: Settings and Trading Strategies | LiteFinance」。9種の文書の「今回開くと 404」は、今日は当たらない。全指標の調べの逐語2つは、今日の本文に在る。スキャルの文は「short time frames」と書き、足の名前は書いてない。指標はボリンジャーバンド（BB幅 を名指ししてはいない）
- 前の照らしの書き込み：9種の文書＝review の BB幅「スキャル」の出どころ（litefinance.org の Bollinger の記事）は、今回開くと 404（「いまの値と違う所」の BB幅・BB%b・613行目）／全指標の調べ＝同じ litefinance.org の記事を「ページの文で確かめた」とし、スキャル「10〜14」「1.5〜2」と、範囲「期間 50・倍率 2.5（スイング・長期）」を逐語つきで書く（out_c6_01.json の BB幅のパラメータの軸）

### BB%b｜n と s のスキャルの値

- 結果：ページに在る（https://fxopen.com/blog/en/1-minute-scalping-trading-strategies-with-examples/ / https://www.mc2.fi/blog/best-rsi-for-scalping）
- 分かったこと：全指標の調べの逐語2つは、どちらも本文に在る（fxopen と MC2）。2つの文はボリンジャーバンドを名指しし、%B（%b）の語はどちらのページの本文にも無い（本文の中の「%B」「%b」を探して0件）。足は2つとも1分足。9種の文書の「%B を名指しした 5分足・スキャルの値は見つからなかった」と、全指標の調べの「スキャル [20, 2]」は、名指しする物（%B かボリンジャーバンドか）が違う
- 前の照らしの書き込み：9種の文書＝%B を名指しした 5分足・スキャルの値は「✗ 見つからなかった」（5 Q3・335行目）／全指標の調べ＝スキャル [20, 2]（fxopen の 1分足の文・MC2 の 1分足の文）を「ページの文で確かめた」で書く（out_c6_01.json の BB%b のパラメータの軸）

### 基準線｜デイトレの値（LF-ICHI の (5, 13, 26)）

- 結果：ページに在る（https://www.litefinance.org/blog/for-beginners/best-technical-indicators/ichimoku-cloud-indicator-in-forex-explained/）
- 分かったこと：今日のページには、両方の文が在る。①問いと答えの節に「good for day trading?」の文（5, 13, 26 を day trading に）②設定の並び「Scalping: 5, 13, 26」と、Scalping の節の「best suited to 15-minute or even 5-minute charts」。9種の文書の「今のページには day trading の語が無い」は、今日のページには当たらない（本文に「day trading」が2か所）。デイトレの値は候補に入れない。Scalping の文は、基準線の候補（スキャル）として載せる
- 前の照らしの書き込み：9種の文書＝資料の表の「デイトレ (5,13,26)・15分足」は、LF-ICHI の今のページには「day trading」の語が無く、「Scalping」の行として書かれている（7 Q3・440行目）／全指標の調べ＝同じ LF-ICHI のページの逐語「Is the Ichimoku 15-minute strategy good for day trading? … Use faster settings (5, 13, 26) …」を「ページの文で確かめた」でデイトレに書く（out_c6_08.json の基準線のパラメータの軸）。★デイトレの値は今回 照らさない

### DI差｜n の範囲

- 結果：ページに在る（https://ta-lib.org/functions/plus_di.html）
- 分かったこと：逐語は本文の表の1行（Parameter・Type・Default・Accepted values・Description の欄）。1–100000 は「Accepted values」（入力として受ける値）の欄の値。9種の文書の「DI の期間だけのスキャル・デイトレ・範囲は見つからなかった」は、勧める値の話。全指標の調べも注に「入力できる範囲。勧める範囲ではない」と書く。2つは、指す物が違う
- 前の照らしの書き込み：9種の文書＝DI の期間だけのスキャル・デイトレ・範囲は「✗ 見つからなかった」（3 Q3・233行目）／全指標の調べ＝範囲「1〜100000（入力できる範囲）」を TA-Lib の逐語つきで「ページの文で確かめた」で書く（注＝入力できる範囲。勧める範囲ではない）（out_c6_01.json の DI差のパラメータの軸 1）

## 3. 9種ごとの候補の表

表の読み方と、作り方の決まりです。

- 候補の出どころは、9種の文書（`textbook_9kinds_kb.md`）と全指標の調べ（`out_c5.json`・`out_c6_*.json`）と、前の照らしの「指標データに行が無い使い方」です。並びは、9種の文書の行の順、次に全指標の調べの行の順です（前の照らしの16件は、どちらにも同じ種類で無いときだけ最後に足した）。候補から1つを選んでいません。
- **値**は、9種の文書の「値」の欄か、全指標の調べの「値」の欄を、そのまま写しました。9種の文書の Q1 の行には値の欄が無いので「値の欄は無い」と書きました。
- **逐語**は、9種の文書の逐語の「"…"」の中と、全指標の調べの逐語です。全部、今日 curl で開いた本文と照らしました。9種の文書の逐語の前の書き込み（「（ショート）」など）は、逐語から外して注に移しました。
- **ページの確かめ**は、全部の候補が「ページに在る」でした。照らすときに引用符・ダッシュをそろえた物、逐語が文の途中で切れている物、2つ以上の断片の物は、注に書きました。
- **時間足**は、逐語の中の足の語（`5-minute chart`・`daily` など）を、そのまま写しました。足の語が無い逐語は「時間足は書いてない」です。9種の文書の時間足の欄（ページの別の所から読んだ足）は使っていません。
- **名指し**は、逐語の中の語だけで決めました（scalp・scalping・scalpers／5分足の語／1時間足より短い足の語／range・ranging・range-bound・sideways・consolidation／short・bearish・sell）。語の意味は見ていません。たとえば「true range」の range や「short-term」の short も、語として当たります。
- **範囲の形**は、範囲の欄だけに書きました。1つの文に「X to Y」「X–Y」「between X and Y」の形が在れば「文に両端が在る」、無ければ「値を挙げただけ」です。
- 欄の名前に「欄の外」と書いた欄（②-4 の既定・スキャルと範囲と既定のどれとも書いてない値）は、依頼書の欄の一覧に無い欄です。要件の「教科書に無ければ既定の値」の材料として並べました。
- 使い方の種類が「書いてない」の欄は、調べの結果に使い方の種類が書いてない逐語（全指標の調べの「閾値」「合図の形のパラメータ」と、9種の文書の Q2・Q4 で種類が分からない行）です。
- 使い方の記録の ③-5 と ③-6 の「逐語の数」「逐語の期間」は、逐語の中の数をそのまま写した物です。閾値かどうかの読みは入れていません（足の長さ・年・ページの番号・ドルの数は除いた）。
- 使い方の記録の「いまの値」は、指標データの使い方の記録のうち、玉の向きが LONG でない行の値です。

**外した物**：デイトレの値（全指標の調べの「デイトレ」の行 20 件・9種の文書の Q3・Q4 でデイトレだけを名指しした行 4 件）、ロングの行（全指標の調べの使い方で玉の向きが LONG の行 7 件）、基準線の候補に入れない転換線の文 13 件。転換線の文として外した物は、下の表です。

| 出どころ | 外した理由 | 逐語 |
|---|---|---|
| 全指標の調べ out_c6_08.json の 基準線 の パラメータの軸.1.既定.0 | 軸 t_（転換線の本数）の値。基準線の候補に転換線の値を入れないため外した | TenkanSen (Conversion Line): (High + Low) / 2 default period = 9 |
| 全指標の調べ out_c6_08.json の 基準線 の パラメータの軸.1.既定.1 | 軸 t_（転換線の本数）の値。基準線の候補に転換線の値を入れないため外した | Tenkan-sen (転換線) calculation: (highest high + lowest low)/2 for the last 9 periods. |
| 全指標の調べ out_c6_08.json の 基準線 の パラメータの軸.1.既定.2 | 軸 t_（転換線の本数）の値。基準線の候補に転換線の値を入れないため外した | Best settings. Classic: 9, 26, 52. Scalping: 5, 13, 26. Swing trading: 9, 26, 52. |
| 全指標の調べ out_c6_08.json の 基準線 の パラメータの軸.1.スキャル.0 | 軸 t_（転換線の本数）の値。基準線の候補に転換線の値を入れないため外した | Scalping. Shorter periods like 5, 13, and 26 produce more signals, but also more false ones. They are best suited to 15-minute or even 5-minute charts. |
| 全指標の調べ out_c6_08.json の 基準線 の パラメータの軸.1.スキャル.1 | 軸 t_（転換線の本数）の値。基準線の候補に転換線の値を入れないため外した | The best Ichimoku settings for scalping and 1-minute chart are 12-24-120, where 12 is for the Conversion Line ( Tenkan-sen), 24 for the Base Line (Kyun-sen ), and 120 for the Leading Span B (Senkou Span B). |
| 全指標の調べ out_c6_08.json の 基準線 の パラメータの軸.1.スキャル.2 | 軸 t_（転換線の本数）の値。基準線の候補に転換線の値を入れないため外した | The best settings for the Ichimoku 5 min chart are standard default settings 9-26-52, where nine is for the Conversion Line ( Tenkan-sen), 26 for the Base Line (Kyun-sen ), and 52 for the Leading Span B (Senkou Span B). |
| 全指標の調べ out_c6_08.json の 基準線 の パラメータの軸.1.範囲.0 | 軸 t_（転換線の本数）の値。基準線の候補に転換線の値を入れないため外した | The indicator works best on 1-hour time frames and above. |
| 全指標の調べ out_c6_08.json の 基準線 の 値の単位と値域.0 | 逐語が転換線だけの文（基準線の語が無い）。基準線の候補に転換線の文を入れないため外した（欄：②-5 値の単位と値域） | Tenkan-sen (転換線) calculation: (highest high + lowest low)/2 for the last 9 periods. |
| 全指標の調べ out_c6_08.json の 基準線 の 値の読み方.0 | 逐語が転換線だけの文（基準線の語が無い）。基準線の候補に転換線の文を入れないため外した（欄：②-6 値の読み方） | If the blue line is moving up or down, it indicates that the market is trending. If it moves horizontally, it signals that the market is ranging. |
| 全指標の調べ out_c6_08.json の 基準線 の 値の読み方.2 | 逐語が転換線だけの文（基準線の語が無い）。基準線の候補に転換線の文を入れないため外した（欄：②-6 値の読み方） | The Tenkan-sen also acts as short-term support, and in an uptrend, the price often bounces off it. |
| 全指標の調べ out_c6_08.json の 基準線 の 教科書の役割.0 | 逐語が転換線だけの文（基準線の語が無い）。基準線の候補に転換線の文を入れないため外した（欄：②-7 教科書の役割） | The Tenkan Sen is an indicator of the market trend. |
| 全指標の調べ out_c6_08.json の 基準線 の 教科書の役割.1 | 逐語が転換線だけの文（基準線の語が無い）。基準線の候補に転換線の文を入れないため外した（欄：②-7 教科書の役割） | The Tenkan-sen mainly shows short-term bullish or bearish momentum. |
| 全指標の調べ out_c6_08.json の 基準線 の 教科書の役割.2 | 逐語が転換線だけの文（基準線の語が無い）。基準線の候補に転換線の文を入れないため外した（欄：②-7 教科書の役割） | Also called the conversion line (blue line), it is primarily used as a signal line and a minor support/resistance line. |

### RSI（欄 35・候補 62・候補が無い欄 19）

#### 指標の記録｜—｜②-4 パラメータの軸 n のスキャルの代表の値

- いまの値：`[7]`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 5分足 9（または 14） | "The best RSI settings for a 5-minute chart are a 9-period RSI with bands at 75/25 for a faster read, or the 14-period default with bands widened to 80/20 if you want fewer signals."<br>https://bullynx.com/blog/best-rsi-settings | ページに在る | 5-minute chart | 5分足 |  | 9種の文書 1 Q3（109行目） |  |
| 2 | 5分足のスキャル 7〜9 | "Faster 7 to 9 75/25 or 80/20 35 to 45 minutes Scalps and quick mean-reversion fades"<br>https://bullynx.com/blog/best-rsi-settings | ページに在る | 時間足は書いてない | スキャル |  | 9種の文書 1 Q3（110行目） |  |
| 3 | 5分足のスキャル 7 | "For 5-minute scalping, the 7-period RSI is usually the best choice."<br>https://www.mc2.fi/blog/best-rsi-for-scalping | ページに在る | 5-minute scalping | スキャル・5分足 |  | 9種の文書 1 Q3（112行目） |  |
| 4 | 1分足 2〜3 | "When trading on a 1-minute chart, the best RSI setting is typically RSI 2 or 3."<br>https://www.mc2.fi/blog/best-rsi-for-scalping | ページに在る | 1-minute chart | 短い足 |  | 9種の文書 1 Q3（113行目） |  |
| 5 | スキャル 5〜7・デイトレ 9〜10 | "Scalpers should use RSI(5-7) with 80/20 levels, while day traders benefit from RSI(9-10) with 75/25 levels."<br>https://eplanetbrokers.com/training/best-rsi-settings-for-5-minute-charts/ | ページに在る | 時間足は書いてない | スキャル |  | 9種の文書 1 Q3（114行目） |  |
| 6 | 5分足のスキャル 5 | "Use a 5-period RSI with 80/20 thresholds to match the faster pace."<br>https://wundertrading.com/journal/en/rsi-vs-stochastic-rsi-crypto-trading | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q3（117行目） |  |
| 7 | [2, 3] | When trading on a 1-minute chart, the best RSI setting is typically RSI 2 or 3.<br>https://www.mc2.fi/blog/best-rsi-for-scalping | ページに在る | 1-minute chart | 短い足 |  | 全指標の調べ out_c6_02.json の RSI の パラメータの軸.0.スキャル.0 | 調べの軸の名前：n（期間）。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |
| 8 | 7〜9（5分足。または 14 のまま水準を 80/20 に広げる） | Most intraday traders run 7 to 9 periods on a 5-minute chart, or stay on 14 and widen the bands to 80/20.<br>https://bullynx.com/blog/best-rsi-settings | ページに在る | intraday・5-minute chart | 5分足 |  | 全指標の調べ out_c6_02.json の RSI の パラメータの軸.0.スキャル.1 | 調べの軸の名前：n（期間）。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |
| 9 | [5] | RSI should be equally nimble here. Use a 5-period RSI with 80/20 thresholds to match the faster pace.<br>https://wundertrading.com/journal/en/rsi-vs-stochastic-rsi-crypto-trading | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_02.json の RSI の パラメータの軸.0.スキャル.2 | 調べの軸の名前：n（期間）。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |
| 10 | 5〜7（スキャル）／9〜10（デイトレ）。どちらも 5分足のページ | Scalpers should use RSI(5-7) with 80/20 levels, while day traders benefit from RSI(9-10) with 75/25 levels.<br>https://eplanetbrokers.com/training/best-rsi-settings-for-5-minute-charts/ | ページに在る | 時間足は書いてない | スキャル |  | 全指標の調べ out_c6_02.json の RSI の パラメータの軸.0.スキャル.3 | 調べの軸の名前：n（期間）。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |

#### 指標の記録｜—｜②-4 パラメータの軸 n の既定（スキャルの値が教科書に無いときに使う値・欄の外）

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 既定 14 | "This RSI calculation is based on 14 periods, the default Wilder suggested in his book."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q3（103行目） |  |
| 2 | 既定 14 | "The number of bars to be used in calculating the RSI. 14 bars is the default."<br>https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q3（104行目） |  |
| 3 | [14] | This RSI calculation is based on 14 periods, the default Wilder suggested in his book.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_02.json の RSI の パラメータの軸.0.既定.0 | 調べの軸の名前：n（期間）。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 4 | [14] | The number of bars to be used in calculating the RSI. 14 bars is the default.<br>https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_02.json の RSI の パラメータの軸.0.既定.1 | 調べの軸の名前：n（期間）。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 5 | [14] | real = RSI(close, timeperiod=14)<br>https://ta-lib.github.io/ta-lib-python/func_groups/momentum_indicators.html | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_02.json の RSI の パラメータの軸.0.既定.2 | 調べの軸の名前：n（期間）。調べの注：資料の表の値と逐語。ページの本文で照らした |

#### 指標の記録｜—｜②-4 パラメータの軸 n の範囲

- いまの値：`{"kind": "int", "lo": 2, "hi": 21}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 2（短期のトレーダー。時間足の指定なし） | Short-term traders sometimes use 2-period RSI to look for overbought readings above 80 and oversold readings below 20.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | ショート | 値を挙げただけ | 全指標の調べ out_c6_02.json の RSI の パラメータの軸.0.範囲.0 | 調べの軸の名前：n（期間）。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |
| 2 | 14 から下げると敏感・上げると鈍感（数の範囲は書いていない） | The default look-back period for RSI is 14, but you can lower it to increase sensitivity or raise it to decrease sensitivity.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 | 値を挙げただけ | 全指標の調べ out_c6_02.json の RSI の パラメータの軸.0.範囲.1 | 調べの軸の名前：n（期間）。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |
| 3 | 7〜9（日中の足のデイトレ）〜21（日足のスイング） | Day traders commonly shorten the period to 7 to 9 on intraday charts, swing traders commonly keep 14 or stretch it to 21 on the daily, and traders in a strong trend commonly widen the bands to 80/20.<br>https://bullynx.com/blog/best-rsi-settings | ページに在る | intraday charts・the daily | 一般 | 文に両端が在る | 全指標の調べ out_c6_02.json の RSI の パラメータの軸.0.範囲.2 | 調べの軸の名前：n（期間）。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |

#### 指標の記録｜—｜②-4 パラメータの軸 n（スキャル・範囲・既定と書いていない値）

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 下げると敏感 | "The default look-back period for RSI is 14, but you can lower it to increase sensitivity or raise it to decrease sensitivity. A 10-day RSI is more likely to reach overbought or oversold levels than a 20-day RSI."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 10-day・20-day | 一般 |  | 9種の文書 1 Q3（105行目） |  |
| 2 | 2（短期の売買） | "Short-term traders sometimes use 2-period RSI to look for overbought readings above 80 and oversold readings below 20."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | ショート |  | 9種の文書 1 Q3（106行目） |  |
| 3 | 時間足を選ばない | "the RSI can be added to many timeframes - daily, weekly, hourly, and minute charts."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | daily・weekly・hourly・minute charts | 一般 |  | 9種の文書 1 Q3（107行目） |  |
| 4 | 1時間足 14 | "On the 1-hour, the classic 14-period works well with standard 70/30 levels."<br>https://wundertrading.com/journal/en/rsi-vs-stochastic-rsi-crypto-trading | ページに在る | the 1-hour | 一般 |  | 9種の文書 1 Q3（116行目） |  |

#### 指標の記録｜—｜②-5 値の単位と値域

- いまの値：`{"値域": {"有界": [0.0, 100.0], "分位": null}}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | {"単位": "0〜100", "下限": 0, "上限": 100} | The RSI moves up and down (oscillates) between zero and 100.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_02.json の RSI の 値の単位と値域.0 |  |

#### 指標の記録｜—｜②-6 値の読み方

- いまの値：`{"区分": "順張り値", "読み方": "大きいほど上昇の勢い", "向きを持つ": true, "性質": ["trend"]}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | （9種の文書の Q1 の行。値の欄は無い） | "The RSI, a momentum oscillator developed by J. Welles Wilder, measures the speed and change of price movements."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q1（77行目） |  |
| 2 | （9種の文書の Q1 の行。値の欄は無い） | "When the RSI is above 70, it generally indicates overbought conditions; when the RSI is below 30, it indicates oversold conditions."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q1（78行目） |  |
| 3 | （9種の文書の Q1 の行。値の欄は無い） | "The Relative Strength Index (RSI) is a well versed momentum based oscillator which is used to measure the speed (velocity) as well as the change (magnitude) of directional price movements."<br>https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q1（79行目） |  |
| 4 | {"読み方": "70 より上は買われ過ぎ、30 より下は売られ過ぎ", "向きを持つ": "書いてない"} | When the RSI is above 70, it generally indicates overbought conditions; when the RSI is below 30, it indicates oversold conditi<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_02.json の RSI の 値の読み方.0 | 逐語は文の途中で切れている（ページでは同じ語の続きが在る） |

#### 指標の記録｜—｜②-7 教科書の役割

- いまの値：`{"区分": null, "出どころ": "語の数だけ（弱い）", "札": "オシレーター"}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | （9種の文書の Q1 の行。値の欄は無い） | "The RSI, a momentum oscillator developed by J. Welles Wilder, measures the speed and change of price movements."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q1（77行目） |  |
| 2 | （9種の文書の Q1 の行。値の欄は無い） | "When the RSI is above 70, it generally indicates overbought conditions; when the RSI is below 30, it indicates oversold conditions."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q1（78行目） |  |
| 3 | （9種の文書の Q1 の行。値の欄は無い） | "The Relative Strength Index (RSI) is a well versed momentum based oscillator which is used to measure the speed (velocity) as well as the change (magnitude) of directional price movements."<br>https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q1（79行目） |  |
| 4 | 勢い | The RSI, a momentum oscillator developed by J. Welles Wilder, measures the speed and change of price movements.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_02.json の RSI の 教科書の役割.0 |  |

#### 指標の記録｜—｜②-11 閾値の範囲

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 1 Q4（137行目））＝「閾値の範囲｜閾値の範囲を1つの文で書いたページ｜—｜—｜✗ 見つからなかった（書いてある値は 60/40〜80/20）」

#### 使い方の記録｜入る合図｜③-2 使い方の種類

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 入る合図 | "Like many momentum oscillators, overbought and oversold readings for RSI work best when prices move sideways within a range ."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 1 Q2（87行目） | 前の照らしの「指標データに行が無い使い方」に在る逐語 |
| 2 | 入る合図 | "A bearish failure swing forms when RSI moves above 70, pulls back, bounces, fails to exceed 70, and then breaks its prior low."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | ショート |  | 9種の文書 1 Q2（90行目） | 前の照らしの「指標データに行が無い使い方」に在る逐語。9種の文書の書き込み「ショート」 |
| 3 | 入る合図 | "A short candidate is RSI crossing back below 70 after a print above 70. The first poke of 30 on a 5 minute chart is noise."<br>https://therighttrader.com/learn/indicator-strategies/best-rsi-settings | ページに在る | 5 minute chart | 5分足・ショート |  | 9種の文書 1 Q2（92行目） | 前の照らしの「指標データに行が無い使い方」に在る逐語。9種の文書の書き込み「ショート」 |
| 4 | 入る合図 | Like many momentum oscillators, overbought and oversold readings for RSI work best when prices move sideways within a range.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | レンジ |  | 全指標の調べ out_c6_02.json の RSI の 使い方.0 | 前の照らしの「指標データに行が無い使い方」に在る逐語 |

#### 使い方の記録｜入る合図｜③-3 場面と型

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | レンジ | Like many momentum oscillators, overbought and oversold readings for RSI work best when prices move sideways within a range.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | レンジ |  | 全指標の調べ out_c6_02.json の RSI の 使い方.0 |  |

#### 使い方の記録｜入る合図｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-5 閾値

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 逐語の数：70・70 | "A bearish failure swing forms when RSI moves above 70, pulls back, bounces, fails to exceed 70, and then breaks its prior low."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | ショート |  | 9種の文書 1 Q2（90行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない）。9種の文書の書き込み「ショート」 |
| 2 | 逐語の数：70・70・30 | "A short candidate is RSI crossing back below 70 after a print above 70. The first poke of 30 on a 5 minute chart is noise."<br>https://therighttrader.com/learn/indicator-strategies/best-rsi-settings | ページに在る | 5 minute chart | 5分足・ショート |  | 9種の文書 1 Q2（92行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない）。9種の文書の書き込み「ショート」 |

#### 使い方の記録｜入る合図｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-7 時間足

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 5 minute chart | "A short candidate is RSI crossing back below 70 after a print above 70. The first poke of 30 on a 5 minute chart is noise."<br>https://therighttrader.com/learn/indicator-strategies/best-rsi-settings | ページに在る | 5 minute chart | 5分足・ショート |  | 9種の文書 1 Q2（92行目） | 9種の文書の書き込み「ショート」 |

#### 使い方の記録｜入る合図｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-2 使い方の種類

- いまの値：`["出口の反転"]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方を書いた逐語が無い（指標データの行は、教科書でない出どころから写した物）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-3 場面と型

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-4 向き

- いまの値：`["下側"]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-5 閾値

- いまの値：`[[{"形": "値", "代表の値": {"スキャル": 30.0, "デイトレ": 30.0}, "出どころ": "CONST_REGISTRY の RSI_OS（Wilder 1978（technical KB §4）・RSI の売られ過ぎ水準）", "単位": "0〜100"}]]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-2 使い方の種類

- いまの値：`["前提崩れの印", "前提崩れの印"]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方を書いた逐語が無い（指標データの行は、教科書でない出どころから写した物）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-3 場面と型

- いまの値：`[{"場面": "レンジ", "型": "flat_up"}]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-4 向き

- いまの値：`["上側", "上側"]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-5 閾値

- いまの値：`[[{"形": "値", "代表の値": {"スキャル": 70.0, "デイトレ": 70.0}, "出どころ": "CONST_REGISTRY の RSI_OB（Wilder 1978（technical KB §4）・RSI の買われ過ぎ水準）", "単位": "0〜100"}], [{"形": "値", "代表の値": {"スキャル": 75.0}, "出どころ": "identity_s1_legacy.json:48", "単位": "0〜100"}]]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-6 パラメータの代表の値

- いまの値：`[{"n": {"スキャル": [9]}}]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-7 時間足

- いまの値：`[["15m"]]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-3 場面と型

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | レンジ（9種の文書の書き込み「レンジ」） | "In a range-bound market , tighter levels like 60/40 can catch more of the smaller swings."<br>https://bullynx.com/blog/best-rsi-settings | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 1 Q2（93行目） | 9種の文書の書き込み「レンジ」 |
| 2 | レンジ（9種の文書の書き込み「レンジ・5分足」） | "Default 14 70/30 70 minutes Ranging sessions only; trends pin it at the band"<br>https://bullynx.com/blog/best-rsi-settings | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 1 Q2（94行目） | 9種の文書の書き込み「レンジ・5分足」 |
| 3 | レンジ（9種の文書の書き込み「レンジ」） | "In ranging markets: Tighten RSI to 7 periods, use 75/25 levels"<br>https://wundertrading.com/journal/en/rsi-vs-stochastic-rsi-crypto-trading | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 1 Q2（95行目） | 9種の文書の書き込み「レンジ」 |

#### 使い方の記録｜書いてない｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-5 閾値

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 逐語の数：13.5・21・70・30 | "The chart below shows MEMC Electronics (WFR) trading between 13.5 and 21 from April to September 2009. The stock peaked soon after RSI reached 70 and bottomed soon after the stock reached 30."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q2（88行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない） |
| 2 | 逐語の数：20・70 | "This scan reveals stocks that are in a downtrend with overbought RSI turning down. First, stocks must be below their 200-day moving average to be in an overall downtrend. Second, RSI must cross above 70 to become overbought."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 200-day | 一般 |  | 9種の文書 1 Q2（89行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない）。9種の文書の書き込み「ショート」 |
| 3 | 逐語の数：10・60・50・60 | "On the flip side, RSI tends to fluctuate between 10 and 60 in a bear market (downtrend) with the 50-60 zone acting as resistance."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q2（91行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない）。9種の文書の書き込み「ショート」 |
| 4 | 逐語の数：60・40 | "In a range-bound market , tighter levels like 60/40 can catch more of the smaller swings."<br>https://bullynx.com/blog/best-rsi-settings | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 1 Q2（93行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない）。9種の文書の書き込み「レンジ」 |
| 5 | 逐語の数：14・70・30・7 | "Default 14 70/30 70 minutes Ranging sessions only; trends pin it at the band"<br>https://bullynx.com/blog/best-rsi-settings | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 1 Q2（94行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない）。9種の文書の書き込み「レンジ・5分足」 |
| 6 | 逐語の数：75・25 | "In ranging markets: Tighten RSI to 7 periods, use 75/25 levels"<br>https://wundertrading.com/journal/en/rsi-vs-stochastic-rsi-crypto-trading | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 1 Q2（95行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない）。9種の文書の書き込み「レンジ」 |
| 7 | 70／30 | "Wilder considered RSI overbought above 70 and oversold below 30."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q4（126行目） |  |
| 8 | 70／30 | "According to Wilder, any number above 70 should be considered overbought and any number below 30 should be considered oversold."<br>https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q4（127行目） |  |
| 9 | 50（向きなし） | "An RSI between 30 and 70 was to be considered neutral and an RSI around 50 signified “no trend”."<br>https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q4（128行目） |  |
| 10 | 80／20 | "Raising the overbought threshold to 80 or lowering the oversold threshold to 20 could reduce the number of overbought/oversold readings."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q4（129行目） |  |
| 11 | 80／20 | "For example, someone might consider any number above 80 as overbought and anything below 20 as oversold. This is entirely at the trader’s discretion."<br>https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q4（130行目） |  |
| 12 | 上げ相場 40〜90・下げ相場 10〜60（前提つき） | "RSI tends to fluctuate between 40 and 90 in a bull market (uptrend) with the 40–50 zones acting as support." / "RSI tends to fluctuate between 10 and 60 in a bear market (downtrend) with the 50-60 zone acting as resistance."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q4（131行目） | 逐語は2つの断片（「…」か複数の引用）。断片ごとに本文に在る |
| 13 | 上げ相場 40〜80・下げ相場 20〜60（前提つき） | "Constance Brown discussed a range shift in Technical Analysis for the Trading Professional (1999): bull markets often hold RSI between 40 and 80, and bear markets between 20 and 60."<br>https://therighttrader.com/learn/indicator-strategies/best-rsi-settings | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 1 Q4（132行目） |  |
| 14 | 30〜50・50〜70（反転の形） | "This lower low is not at oversold levels but is usually between 30 and 50." / "the higher high is usually just below overbought levels in the 50-70 area."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q4（133行目） | 逐語は2つの断片（「…」か複数の引用）。断片ごとに本文に在る |
| 15 | 5分足 75／25 | "Using 75 for overbought and 25 for oversold conditions filters out market noise while maintaining sensitivity to genuine momentum changes."<br>https://eplanetbrokers.com/training/best-rsi-settings-for-5-minute-charts/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q4（135行目） |  |
| 16 | 5分足 30／70 から始め、20／80 へ | "Keep 30 and 70 at first. If 7 tags 70 on every small push, you can move the lines to 20 and 80."<br>https://therighttrader.com/learn/indicator-strategies/best-rsi-settings | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 1 Q4（136行目） |  |
| 17 | {"形": "値", "値": [70, 30], "意味": "上が買われ過ぎ、下が売られ過ぎ"} | When the RSI is above 70, it generally indicates overbought conditions; when the RSI is below 30, it indicates oversold conditi<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_02.json の RSI の 閾値.0 | 逐語は文の途中で切れている（ページでは同じ語の続きが在る） |

#### 使い方の記録｜書いてない｜③-6 パラメータの代表の値

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 逐語の期間：7 | "In ranging markets: Tighten RSI to 7 periods, use 75/25 levels"<br>https://wundertrading.com/journal/en/rsi-vs-stochastic-rsi-crypto-trading | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 1 Q2（95行目） | 9種の文書の書き込み「レンジ」 |

#### 使い方の記録｜書いてない｜③-7 時間足

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 200-day | "This scan reveals stocks that are in a downtrend with overbought RSI turning down. First, stocks must be below their 200-day moving average to be in an overall downtrend. Second, RSI must cross above 70 to become overbought."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 200-day | 一般 |  | 9種の文書 1 Q2（89行目） | 9種の文書の書き込み「ショート」 |

#### 使い方の記録｜書いてない｜③-9 合図の形のパラメータ

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | {"形": "上へ抜ける", "値": 70} | Second, RSI must cross above 70 to become overbought.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_02.json の RSI の 合図の形のパラメータ.0 |  |

### ADX（欄 42・候補 39・候補が無い欄 31）

#### 指標の記録｜—｜②-4 パラメータの軸 n のスキャルの代表の値

- いまの値：`[14]`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | デイトレ 14・5分足 7 か 10 | "Day traders keep 14 on a 15 minute or 1 hour chart. Period 7 or 10 on a 5 minute chart reacts faster and spikes more."<br>https://therighttrader.com/learn/indicator-strategies/best-adx-settings | ページに在る | 15 minute・5 minute chart | 5分足・短い足 |  | 9種の文書 2 Q3（179行目） |  |
| 2 | 5分足で 14 は 70分 | "On a 5 minute chart, period 14 is 70 minutes. That can work as a filter. If you need strength to show up inside a half hour, try period 10 or 7 and keep the 20 and 25 marks."<br>https://therighttrader.com/learn/indicator-strategies/best-adx-settings | ページに在る | 5 minute chart | 5分足 |  | 9種の文書 2 Q3（180行目） |  |
| 3 | 1分足で 14 は遅い | "14 Daily, 15 minute, 1 hour Wilder's default Late on a 1 minute chart"<br>https://therighttrader.com/learn/indicator-strategies/best-adx-settings | ページに在る | Daily・15 minute・1 minute chart | 短い足 |  | 9種の文書 2 Q3（181行目） |  |

#### 指標の記録｜—｜②-4 パラメータの軸 n の既定（スキャルの値が教科書に無いときに使う値・欄の外）

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 既定 14 | "The calculation example below is based on a 14-period indicator setting, as recommended by Wilder."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q3（171行目） |  |
| 2 | 既定 14 | "The time period to be used in calculating the ADX which has a smoothing component (14 is the Default)."<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q3（172行目） |  |
| 3 | [14] | The calculation example below is based on a 14-period indicator setting, as recommended by Wilder.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の ADX の パラメータの軸.0.既定.0 | 調べの軸の名前：period。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 4 | [14] | The time period to be used in calculating the ADX which has a smoothing component (14 is the Default).<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の ADX の パラメータの軸.0.既定.1 | 調べの軸の名前：period。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 5 | [14] | optInTimePeriod integer 14 2–100000 Smoothing/averaging period for DM, TR, and ADX<br>https://ta-lib.org/functions/adx.html | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の ADX の パラメータの軸.0.既定.2 | 調べの軸の名前：period。調べの注：資料の表の値と逐語。ページの本文で照らした |

#### 指標の記録｜—｜②-4 パラメータの軸 n の範囲

- いまの値：`{"kind": "int", "lo": 7, "hi": 21}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 範囲 7〜21 | "The practical range for most systematic traders is 7 to 21, with 14 as the default starting point."<br>https://regimelab.io/blog/best-adx-settings | ページに在る | 時間足は書いてない | レンジ | 文に両端が在る | 9種の文書 2 Q3（174行目） |  |
| 2 | 7〜21 | The practical range for most systematic traders is 7 to 21, with 14 as the default starting point.<br>https://regimelab.io/blog/best-adx-settings | ページに在る | 時間足は書いてない | レンジ | 文に両端が在る | 全指標の調べ out_c6_01.json の ADX の パラメータの軸.0.範囲.0 | 調べの軸の名前：period。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |

#### 指標の記録｜—｜②-4 パラメータの軸 n（スキャル・範囲・既定と書いていない値）

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | Wilder の前提 | "Although Wilder designed his Directional Movement System with commodities and daily prices in mind, these indicators can also be applied to stocks."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | daily | 一般 |  | 9種の文書 2 Q3（173行目） |  |
| 2 | 7 より下は乱れる | "Below period 7, ADX readings typically become too erratic to serve as a reliable regime classifier."<br>https://regimelab.io/blog/best-adx-settings | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q3（175行目） |  |
| 3 | 15分足 7〜14 | "15-minute charts: 7 to 14. At 14 periods, 15-minute ADX covers 3.5 hours of price data. Shorter periods (7 to 10) are common at this resolution because the full-cycle logic breaks down for intraday timeframes."<br>https://regimelab.io/blog/best-adx-settings | ページに在る | 15-minute charts・15-minute・intraday timeframes | 短い足 |  | 9種の文書 2 Q3（176行目） |  |
| 4 | 1時間足 10〜14 | "1-hour charts: 10 to 14."<br>https://regimelab.io/blog/best-adx-settings | ページに在る | 1-hour | 一般 |  | 9種の文書 2 Q3（177行目） |  |

#### 指標の記録｜—｜②-5 値の単位と値域

- いまの値：`{"値域": {"有界": null, "分位": null}}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | {"単位": "0〜100", "下限": 0, "上限": 100} | DMI has a value between 0 and 100 and is used to measure the strength of the current trend.<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の ADX の 値の単位と値域.0 |  |

#### 指標の記録｜—｜②-6 値の読み方

- いまの値：`{"区分": "状態量", "読み方": "大きいほどトレンドが強い（向きは持たない）", "向きを持つ": false, "性質": ["none"]}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | （9種の文書の Q1 の行。値の欄は無い） | "it measures the strength of the trend (regardless of direction) over time."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q1（149行目） |  |
| 2 | （9種の文書の Q1 の行。値の欄は無い） | "The Average Directional Index (ADX) is used to measure the strength or weakness of a trend, not the actual direction."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q1（150行目） |  |
| 3 | （9種の文書の Q1 の行。値の欄は無い） | "ADX's purposes is to define whether or not there is a trend present. It does not take direction into account at all."<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q1（151行目） |  |
| 4 | {"読み方": "大きいほどトレンドが強い。向きは見ない", "向きを持つ": "書いてない"} | Higher values indicate a stronger trend (a common convention treats >25 as trending); says nothing about direction.<br>https://ta-lib.org/functions/adx.html | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の ADX の 値の読み方.0 |  |

#### 指標の記録｜—｜②-7 教科書の役割

- いまの値：`{"区分": ["強さ"], "出どころ": "R-1（封つき r1_role_map.json・CC の調べ（cc_ans04・照らし一致））", "札": "強さ"}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | （9種の文書の Q1 の行。値の欄は無い） | "it measures the strength of the trend (regardless of direction) over time."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q1（149行目） |  |
| 2 | （9種の文書の Q1 の行。値の欄は無い） | "The Average Directional Index (ADX) is used to measure the strength or weakness of a trend, not the actual direction."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q1（150行目） |  |
| 3 | （9種の文書の Q1 の行。値の欄は無い） | "ADX's purposes is to define whether or not there is a trend present. It does not take direction into account at all."<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q1（151行目） |  |
| 4 | 強さ | The Average Directional Index (ADX), shown in black in the chart above, is in turn derived from the smoothed averages of the difference between +DI and -DI; it measures the strength of the trend (regardless of direction) over time.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の ADX の 教科書の役割.0 |  |

#### 指標の記録｜—｜②-11 閾値の範囲

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 2 Q4（197行目））＝「閾値の範囲｜閾値の範囲を書いたページ｜—｜—｜✗ 見つからなかった（書いてある値は 15〜30。TRT-ADX は 15 と 30 を「動かすときの例」として書く）」

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-2 使い方の種類

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 入ってはいけない場面を除く条件 | "ADX must be over 25 (strong trend. The value is determined by trader) " / "The -DI crosses above the +DI."<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q2（161行目） | 9種の文書の書き込み「ショート」。逐語は2つの断片（「…」か複数の引用）。断片ごとに本文に在る |
| 2 | 入ってはいけない場面を除く条件 | ADX must be over 25 (strong trend. The value is determined by trader)<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の ADX の 使い方.1 |  |

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-3 場面と型

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-5 閾値

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 逐語の数：25 | "ADX must be over 25 (strong trend. The value is determined by trader) " / "The -DI crosses above the +DI."<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q2（161行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない）。9種の文書の書き込み「ショート」。逐語は2つの断片（「…」か複数の引用）。断片ごとに本文に在る |
| 2 | 逐語の数：25 | ADX must be over 25 (strong trend. The value is determined by trader)<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の ADX の 使い方.1 | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない） |

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-2 使い方の種類

- いまの値：`["出口の反転"]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方を書いた逐語が無い（指標データの行は、教科書でない出どころから写した物）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-3 場面と型

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-4 向き

- いまの値：`["下側"]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-5 閾値

- いまの値：`[[{"形": "値", "代表の値": {"スキャル": 25.0, "デイトレ": 25.0}, "出どころ": "CONST_REGISTRY の ADX_TREND（Wilder 1978（technical KB §4）・ADX のトレンド成立の目安）"}]]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜出口の反転｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-2 使い方の種類

- いまの値：`["前提崩れの印"]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方を書いた逐語が無い（指標データの行は、教科書でない出どころから写した物）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-3 場面と型

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-4 向き

- いまの値：`["上側"]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-5 閾値

- いまの値：`[[{"形": "値", "代表の値": {"スキャル": 25.0, "デイトレ": 25.0}, "出どころ": "CONST_REGISTRY の ADX_TREND（Wilder 1978（technical KB §4）・ADX のトレンド成立の目安）"}]]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-2 使い方の種類

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 場面の判定 | "At its most basic, the Average Directional Index (ADX) can be used to determine if a security is trending or not. This determination helps traders choose between a trend-following system or a non-trend-following system."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q2（159行目） | 前の照らしの「指標データに行が無い使い方」に在る逐語 |
| 2 | 場面の判定 | The Average Directional Index (ADX) is used to measure the strength or weakness of a trend, not the actual direction.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の ADX の 使い方.0 |  |

#### 使い方の記録｜場面の判定｜③-3 場面と型

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-5 閾値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-3 場面と型

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 2 Q2（163行目））＝「ショートで ADX の値のどちら側を使うか｜ADX の値をショート用に上と下で分けて書いたページ｜—｜✗ 見つからなかった（どのページも、ADX は向きを持たないと書く）」

#### 使い方の記録｜書いてない｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-5 閾値

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 逐語の数：40 | "ADX at 40 with minus DI on top is a strong downtrend."<br>https://therighttrader.com/learn/indicator-strategies/best-adx-settings | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q2（162行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない）。9種の文書の書き込み「ADX は下げでも高い」 |
| 2 | 25／20 | "Wilder suggests that a strong trend is present when ADX is above 25 and no trend is present when ADX is below 20. There appears to be a gray zone between 20 and 25."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q4（190行目） |  |
| 3 | 20 | "Many technical analysts use 20 as the key level for ADX."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q4（191行目） |  |
| 4 | 25／20 | "Wilder believed that a DMI reading above 25 indicated a strong trend, while a reading below 20 indicated a weak or non-existent trend."<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q4（192行目） |  |
| 5 | 銘柄で変わる | "What is truly a strong trend or a weak trend depends on the financial instrument being examined."<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q4（193行目） |  |
| 6 | 15分足では 25 を直す | "The 25 threshold may also need recalibration: brief intraday directional moves can produce ADX readings above 25 that do not represent genuine trend conditions in the way a daily chart reading does."<br>https://regimelab.io/blog/best-adx-settings | ページに在る | intraday・daily chart | 一般 |  | 9種の文書 2 Q4（194行目） |  |
| 7 | 25 は日足から | "Wilder’s 25 level was derived from empirical observation of daily commodity charts using a 14-period calculation."<br>https://regimelab.io/blog/best-adx-settings | ページに在る | daily | 一般 |  | 9種の文書 2 Q4（195行目） |  |
| 8 | 5分足でも 20 と 25 | "keep the 20 and 25 marks"<br>https://therighttrader.com/learn/indicator-strategies/best-adx-settings | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 2 Q4（196行目） |  |
| 9 | {"形": "値", "値": 25, "意味": "25 より上はトレンドとみなす"} | Higher values indicate a stronger trend (a common convention treats >25 as trending); says nothing about direction.<br>https://ta-lib.org/functions/adx.html | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の ADX の 閾値.0 |  |
| 10 | {"形": "前提つき", "値": 25, "意味": "DI のクロスは ADX が 25 より上のときだけ"} | ADX must be over 25 (strong trend. The value is determined by trader)<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の ADX の 閾値.1 |  |

#### 使い方の記録｜書いてない｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

### DI差（欄 42・候補 30・候補が無い欄 27）

#### 指標の記録｜—｜②-4 パラメータの軸 n のスキャルの代表の値

- いまの値：`[14]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 3 Q3（233行目））＝「スキャル・デイトレ・範囲｜DI の期間だけの値｜—｜—｜✗ 見つからなかった」

#### 指標の記録｜—｜②-4 パラメータの軸 n の既定（スキャルの値が教科書に無いときに使う値・欄の外）

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 既定 14 | "The time period to be used in calculating the DI (14 is Default)."<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 3 Q3（230行目） |  |
| 2 | 既定 14 | "DI length 14 Wilder smooth of plus DM, minus DM, and true range"<br>https://therighttrader.com/learn/indicator-strategies/best-adx-settings | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 3 Q3（231行目） |  |
| 3 | [14] | The time period to be used in calculating the DI (14 is Default).<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の パラメータの軸.0.既定.0 | 調べの軸の名前：period。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 4 | [14] | optInTimePeriod integer 14 2–100000 Smoothing/averaging period for DM, TR, and ADX<br>https://ta-lib.org/functions/adx.html | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の パラメータの軸.0.既定.1 | 調べの軸の名前：period。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 5 | [14] | The calculation example below is based on a 14-period indicator setting, as recommended by Wilder.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の パラメータの軸.0.既定.2 | 調べの軸の名前：period。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 6 | 14 | optInTimePeriod integer 14 1–100000 Wilder smoothing period<br>https://ta-lib.org/functions/plus_di.html | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の パラメータの軸.1.既定.0 |  |
| 7 | 14 | The time period to be used in calculating the DI (14 is Default).<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の パラメータの軸.1.既定.1 |  |

#### 指標の記録｜—｜②-4 パラメータの軸 n の範囲

- いまの値：`{"kind": "int", "lo": 7, "hi": 21}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 1〜100000（入力できる範囲） | optInTimePeriod integer 14 1–100000 Wilder smoothing period<br>https://ta-lib.org/functions/plus_di.html | ページに在る | 時間足は書いてない | 一般 | 文に両端が在る | 全指標の調べ out_c6_01.json の DI差 の パラメータの軸.1.範囲.0 | 調べの注：入力できる範囲。勧める範囲ではない。1サイトだけ |

#### 指標の記録｜—｜②-4 パラメータの軸 n（スキャル・範囲・既定と書いていない値）

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 別にしない | "If you set DI length to 10 and ADX smoothing to 20, you no longer have Wilder's tool and you cannot tell which length mattered."<br>https://therighttrader.com/learn/indicator-strategies/best-adx-settings | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 3 Q3（232行目） |  |

#### 指標の記録｜—｜②-5 値の単位と値域

- いまの値：`{"値域": {"有界": null, "分位": null}}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | {"単位": "0〜100", "下限": 0, "上限": 100} | DMI has a value between 0 and 100 and is used to measure the strength of the current trend.<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の 値の単位と値域.1 |  |

#### 指標の記録｜—｜②-6 値の読み方

- いまの値：`{"区分": "順張り値", "読み方": "プラスで上昇方向が優勢", "向きを持つ": true, "性質": ["trend"]}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | （9種の文書の Q1 の行。値の欄は無い） | "The Plus Directional Indicator (+DI) and Minus Directional Indicator (-DI) ... are derived from smoothed averages of these differences and measure trend direction over time. When +DI is above -DI, the trend is up; when +DI is below -DI, the trend is down."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 3 Q1（209行目） | 逐語は2つの断片（「…」か複数の引用）。断片ごとに本文に在る |
| 2 | （9種の文書の Q1 の行。値の欄は無い） | "The other two indicators (+DI and -DI) are used to compliment the ADX. They serve the purpose of determining trend direction."<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 3 Q1（210行目） |  |
| 3 | {"読み方": "+DI が −DI より上なら上げ、下なら下げ", "向きを持つ": "持つ"} | When +DI is above -DI, the trend is up; when +DI is below -DI, the trend is down.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の 値の読み方.0 |  |

#### 指標の記録｜—｜②-7 教科書の役割

- いまの値：`{"区分": ["向き"], "出どころ": "R-1（封つき r1_role_map.json・CC の調べ（cc_ans04・照らし一致））", "札": "トレンド"}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | （9種の文書の Q1 の行。値の欄は無い） | "The Plus Directional Indicator (+DI) and Minus Directional Indicator (-DI) ... are derived from smoothed averages of these differences and measure trend direction over time. When +DI is above -DI, the trend is up; when +DI is below -DI, the trend is down."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 3 Q1（209行目） | 逐語は2つの断片（「…」か複数の引用）。断片ごとに本文に在る |
| 2 | （9種の文書の Q1 の行。値の欄は無い） | "The other two indicators (+DI and -DI) are used to compliment the ADX. They serve the purpose of determining trend direction."<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 3 Q1（210行目） |  |
| 3 | 向き | Measures the strength of upward price movement. Rising +DI signals strengthening upward direction; compared against MINUS_DI to judge trend direction.<br>https://ta-lib.org/functions/plus_di.html | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の 教科書の役割.0 |  |

#### 指標の記録｜—｜②-11 閾値の範囲

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 3 Q4（243行目））＝「DI差の大きさの閾値｜DI差の大きさ（例＝差が 10 より大きい）を書いたページ｜—｜—｜✗ 見つからなかった」

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-2 使い方の種類

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 入ってはいけない場面を除く条件 | ADX must be over 25 (strong trend. The value is determined by trader)<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の 使い方.2 |  |

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-3 場面と型

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-5 閾値

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 逐語の数：25 | ADX must be over 25 (strong trend. The value is determined by trader)<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の 使い方.2 | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない） |

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入ってはいけない場面を除く条件｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-2 使い方の種類

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 入る合図 | DI Crossovers are the significant trading signal generated by the DMI.<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の 使い方.1 |  |

#### 使い方の記録｜入る合図｜③-3 場面と型

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-5 閾値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-2 使い方の種類

- いまの値：`["前提崩れの印"]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方を書いた逐語が無い（指標データの行は、教科書でない出どころから写した物）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-3 場面と型

- いまの値：`[{"場面": "レンジ", "型": "down"}]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-4 向き

- いまの値：`["上側"]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-5 閾値

- いまの値：`[[{"形": "値", "代表の値": {"スキャル": 28.102910192963172}, "出どころ": "identity_s1_legacy.json:70"}]]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-6 パラメータの代表の値

- いまの値：`[{"n": {"スキャル": [14]}}]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-7 時間足

- いまの値：`[["5m"]]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-2 使い方の種類

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 場面の判定 | The Average Directional Index projects market price and it is clearly seen when prices move up (when +DI is above -DI), and when the prices move down (when -DI is above +DI).<br>https://www.tradingview.com/support/solutions/43000589099-average-directional-index-adx/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の 使い方.4 |  |

#### 使い方の記録｜場面の判定｜③-3 場面と型

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 上げ | The Average Directional Index projects market price and it is clearly seen when prices move up (when +DI is above -DI), and when the prices move down (when -DI is above +DI).<br>https://www.tradingview.com/support/solutions/43000589099-average-directional-index-adx/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の 使い方.4 |  |

#### 使い方の記録｜場面の判定｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-5 閾値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-3 場面と型

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | レンジ（9種の文書の書き込み「レンジ」） | "For example, the first group of whipsaws in September 2009 occurred during a consolidation."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 3 Q2（221行目） | 9種の文書の書き込み「レンジ」 |
| 2 | レンジ（9種の文書の書き込み「レンジ」） | "These moments in question are known as “false signals” and are most common when ADX is calculated below 25."<br>https://www.tradingview.com/support/solutions/43000589099-average-directional-index-adx/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 3 Q2（222行目） | 9種の文書の書き込み「レンジ」 |

#### 使い方の記録｜書いてない｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-5 閾値

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 逐語の数：5・20 | "Overall Downtrend with -DI Crossing above +DI ... A downtrend is present when trading below the 50-day SMA. A sell signal is possible when ADX is above 20. This signal materializes when -DI moves above +DI."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 50-day | ショート |  | 9種の文書 3 Q2（219行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない）。9種の文書の書き込み「ショート」。逐語は2つの断片（「…」か複数の引用）。断片ごとに本文に在る |
| 2 | 逐語の数：25 | "These moments in question are known as “false signals” and are most common when ADX is calculated below 25."<br>https://www.tradingview.com/support/solutions/43000589099-average-directional-index-adx/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 3 Q2（222行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない）。9種の文書の書き込み「レンジ」 |
| 3 | 交差＋前提 | "The first requirement is for ADX to be trading above 25. This ensures that prices are trending. Many traders, however, use 20 as the key level. A buy signal occurs when +DI crosses above -DI."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 3 Q4（241行目） |  |
| 4 | 交差＋前提 | "A general interpretation would be that during a strong trend (ADX above 25 but dependent on the analyst's interpretation), when the +DI is above the -DI, then a Bullish Market is defined."<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 3 Q4（242行目） |  |
| 5 | {"形": "前提つき", "値": 25, "意味": "ADX が 25 より上のときに DI のクロスを使う"} | ADX must be over 25 (strong trend. The value is determined by trader)<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の 閾値.0 |  |

#### 使い方の記録｜書いてない｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-7 時間足

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 50-day | "Overall Downtrend with -DI Crossing above +DI ... A downtrend is present when trading below the 50-day SMA. A sell signal is possible when ADX is above 20. This signal materializes when -DI moves above +DI."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | ページに在る | 50-day | ショート |  | 9種の文書 3 Q2（219行目） | 9種の文書の書き込み「ショート」。逐語は2つの断片（「…」か複数の引用）。断片ごとに本文に在る |

#### 使い方の記録｜書いてない｜③-9 合図の形のパラメータ

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | {"形": "クロスの相手", "値": "−DI（DI差なら 0）"} | DI Crossovers are the significant trading signal generated by the DMI.<br>https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の DI差 の 合図の形のパラメータ.0 |  |

### BB幅（欄 32・候補 41・候補が無い欄 19）

#### 指標の記録｜—｜②-4 パラメータの軸 n と s のスキャルの代表の値

- いまの値：`{"n": [20], "s": [2]}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 5分足にも使える | "Bollinger Bands can be used on bars of any length, 5 minutes, one hour, daily, weekly, etc."<br>https://www.bollingerbands.com/bollinger-band-rules | ページに在る | daily・weekly | 一般 |  | 9種の文書 4 Q3（281行目） | 9種の文書の値は軸を分けずに書いてある（組の値か、どちらか1つの軸の値） |
| 2 | 5分足 (10, 1.9) | "Day traders who leave 20 and 2 often put them on a 15-minute chart, or use 10 and 1.9 on a 5-minute chart."<br>https://therighttrader.com/learn/indicator-strategies/best-bollinger-bands-settings | ページに在る | 15-minute chart・5-minute chart | 5分足・短い足 |  | 9種の文書 4 Q3（282行目） | 9種の文書の値は軸を分けずに書いてある（組の値か、どちらか1つの軸の値） |
| 3 | 5分足で (20, 2) は遅い | "20 and 2 Daily default, or 15-minute Bollinger's reference Late on a 5-minute scalp"<br>https://therighttrader.com/learn/indicator-strategies/best-bollinger-bands-settings | ページに在る | Daily・15-minute・5-minute | スキャル・5分足・短い足 |  | 9種の文書 4 Q3（283行目） | 9種の文書の値は軸を分けずに書いてある（組の値か、どちらか1つの軸の値） |
| 4 | スキャル (10〜14, 1.5〜2) | "Period for SMA: Reduce to 10-14 periods." / "Standard Deviations: Use 1.5 to 2."<br>https://optionx.trade/blogs/bollinger-bands-scalping-strategy-indian-fno | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q3（284行目） | 9種の文書の値は軸を分けずに書いてある（組の値か、どちらか1つの軸の値）。逐語は2つの断片（「…」か複数の引用）。断片ごとに本文に在る |
| 5 | ["10〜14", "1.5〜2"] | For scalping on short time frames, you can reduce the period to 10–14, with a multiplier of 1.5–2.<br>https://www.litefinance.org/blog/for-beginners/best-technical-indicators/bollinger-bands/ | ページに在る | short time frames | スキャル・ショート |  | 全指標の調べ out_c6_01.json の BB幅 の パラメータの軸.0.スキャル.0 | 調べの軸の名前：period・stdev_mult。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 6 | ["10〜14", "1.5〜2"] | When applied to scalping, traders often adjust these settings to suit shorter timeframes, such as using a 10-14 period SMA and 1.5-2 standard deviations on 1-minute or 5-minute charts.<br>https://blog.opofinance.com/en/bollinger-bands-scalping-secrets/ | ページに在る | shorter timeframes・1-minute・5-minute charts | スキャル・5分足・短い足 |  | 全指標の調べ out_c6_01.json の BB幅 の パラメータの軸.0.スキャル.1 | 調べの軸の名前：period・stdev_mult。調べの注：資料の表の値と逐語。ページの本文で照らした |

#### 指標の記録｜—｜②-4 パラメータの軸 n と s の既定（スキャルの値が教科書に無いときに使う値・欄の外）

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 既定 (20, 2) | "The default parameters of 20 periods for the moving average and standard deviation calculations, and two standard deviations for the width of the bands are just that, defaults. The actual parameters needed for any given market/task may be different."<br>https://www.bollingerbands.com/bollinger-band-rules | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q3（276行目） | 9種の文書の値は軸を分けずに書いてある（組の値か、どちらか1つの軸の値） |
| 2 | 既定 (20, 2) | "The default parameters (20,2) are based on the default parameters for Bollinger Bands."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q3（277行目） | 9種の文書の値は軸を分けずに書いてある（組の値か、どちらか1つの軸の値） |
| 3 | 既定 20・2 | "20 days is the default." / "The number of Standard Deviations away from the SMA that the Upper and Lower Bands should be. 2 is the default."<br>https://www.tradingview.com/support/solutions/43000501972-bollinger-bandwidth-bbw/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q3（278行目） | 9種の文書の値は軸を分けずに書いてある（組の値か、どちらか1つの軸の値）。逐語は2つの断片（「…」か複数の引用）。断片ごとに本文に在る |
| 4 | [20, 2] | The default parameters of 20 periods for the moving average and standard deviation calculations, and two standard deviations for the width of the bands are just that, defaults. The actual parameters needed for any given market/task may be different.<br>https://www.bollingerbands.com/bollinger-band-rules | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB幅 の パラメータの軸.0.既定.0 | 調べの軸の名前：period・stdev_mult。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 5 | [20, 2] | The defaults today are the same as they were 35 years ago, 20 periods for the moving average with the bands set at plus and minus two standard deviations of the same data used for the average.<br>https://www.bollingerbands.com/bollinger-bands | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB幅 の パラメータの軸.0.既定.1 | 調べの軸の名前：period・stdev_mult。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 6 | [20, 2] | The default parameters (20,2) are based on the default parameters for Bollinger Bands.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB幅 の パラメータの軸.0.既定.2 | 調べの軸の名前：period・stdev_mult。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 7 | [20, 2] | The time period to be used in calculating the SMA which creates the base for the Upper and Lower Bands. 20 days is the default.<br>https://www.tradingview.com/support/solutions/43000501972-bollinger-bandwidth-bbw/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB幅 の パラメータの軸.0.既定.3 | 調べの軸の名前：period・stdev_mult。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 8 | [20, 2] | upperband, middleband, lowerband = BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)<br>https://ta-lib.github.io/ta-lib-python/func_groups/overlap_studies.html | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB幅 の パラメータの軸.0.既定.4 | 調べの軸の名前：period・stdev_mult。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 9 | [5, 2.0] | length (int): The period. Default: ```5```<br>https://files.pythonhosted.org/packages/be/2f/c67d49afd31c3b02a02ecb5dd07399ed35298042e1b50d166efe2068bb0e/pandas_ta-0.4.71b0-py3-none-any.whl#pandas_ta/volatility/bbands.py | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB幅 の パラメータの軸.0.既定.5 | 調べの軸の名前：period・stdev_mult。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |

#### 指標の記録｜—｜②-4 パラメータの軸 n と s の範囲

- いまの値：`{"n": {"kind": "int", "lo": 10, "hi": 50}, "s": {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | (10,1.9)〜(50,2.1) | For consistent price containment: If the average is lengthened the number of standard deviations needs to be increased; from 2 at 20 periods, to 2.1 at 50 periods. Likewise, if the average is shortened the number of standard deviations should be reduced; from 2 at 20 periods, to 1.9 at 10 periods.<br>https://www.bollingerbands.com/bollinger-band-rules | ページに在る | 時間足は書いてない | 一般 | 値を挙げただけ | 全指標の調べ out_c6_01.json の BB幅 の パラメータの軸.0.範囲.0 | 調べの軸の名前：period・stdev_mult。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 2 | (10,1.9)〜(50,2.1) | A Bollinger Band overlay can be set at (50,2.1) for a longer timeframe or at (10,1.9) for a shorter timeframe.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/bollinger-bands | ページに在る | longer timeframe・shorter timeframe | 一般 | 値を挙げただけ | 全指標の調べ out_c6_01.json の BB幅 の パラメータの軸.0.範囲.1 | 調べの軸の名前：period・stdev_mult。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 3 | 期間 50・倍率 2.5（スイング・長期） | For swing or long-term trading, the period can be increased—for example, to 50—and the multiplier to 2.5.<br>https://www.litefinance.org/blog/for-beginners/best-technical-indicators/bollinger-bands/ | ページに在る | 時間足は書いてない | 一般 | 値を挙げただけ | 全指標の調べ out_c6_01.json の BB幅 の パラメータの軸.0.範囲.2 | 調べの軸の名前：period・stdev_mult。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |

#### 指標の記録｜—｜②-4 パラメータの軸 n と s（スキャル・範囲・既定と書いていない値）

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 組 (10, 1.9)〜(50, 2.1) | "If the average is lengthened the number of standard deviations needs to be increased; from 2 at 20 periods, to 2.1 at 50 periods. Likewise, if the average is shortened the number of standard deviations should be reduced; from 2 at 20 periods, to 1.9 at 10 periods."<br>https://www.bollingerbands.com/bollinger-band-rules | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q3（279行目） | 9種の文書の値は軸を分けずに書いてある（組の値か、どちらか1つの軸の値） |
| 2 | 同じ組 | "Bollinger suggests increasing the standard deviation multiplier to 2.1 for a 50-period SMA and decreasing the standard deviation multiplier to 1.9 for a 10-period SMA."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/bollinger-bands | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q3（280行目） | 9種の文書の値は軸を分けずに書いてある（組の値か、どちらか1つの軸の値） |
| 3 | スイング 2.5 | "Swing traders who want fewer outside closes can keep length 20 and raise the multiplier to 2.5."<br>https://therighttrader.com/learn/indicator-strategies/best-bollinger-bands-settings | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q3（285行目） | 9種の文書の値は軸を分けずに書いてある（組の値か、どちらか1つの軸の値） |

#### 指標の記録｜—｜②-4 パラメータの軸 n のスキャルの代表の値

- いまの値：`[20]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 指標の記録｜—｜②-4 パラメータの軸 n の範囲

- いまの値：`{"kind": "int", "lo": 10, "hi": 50}`
- 候補：無い。理由＝9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 指標の記録｜—｜②-4 パラメータの軸 s のスキャルの代表の値

- いまの値：`[2]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 指標の記録｜—｜②-4 パラメータの軸 s の範囲

- いまの値：`{"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}`
- 候補：無い。理由＝9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 指標の記録｜—｜②-5 値の単位と値域

- いまの値：`{"値域": {"有界": null, "分位": null}}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | {"単位": "%", "下限": null, "上限": null} | Bollinger BandWidth = (Upper Band - Lower Band) / Middle Band * 100<br>https://www.tradingview.com/support/solutions/43000501972-bollinger-bandwidth-bbw/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB幅 の 値の単位と値域.0 |  |

#### 指標の記録｜—｜②-6 値の読み方

- いまの値：`{"区分": "ボラ量", "読み方": "", "向きを持つ": false, "性質": ["vol"]}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | （9種の文書の Q1 の行。値の欄は無い） | "Because Bollinger Bands are based on the standard deviation, falling BandWidth reflects decreasing volatility and rising BandWidth reflects increasing volatility."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q1（255行目） |  |
| 2 | （9種の文書の Q1 の行。値の欄は無い） | "BandWidth tells us how wide the Bollinger Bands are. The raw width is normalized using the middle band. Using the default parameters BandWidth is four times the coefficient of variation."<br>https://www.bollingerbands.com/bollinger-band-rules | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q1（256行目） |  |
| 3 | {"読み方": "帯が狭まると小さく、広がると大きい", "向きを持つ": "書いてない"} | BandWidth decreases as Bollinger Bands narrow and increases as Bollinger Bands widen.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB幅 の 値の読み方.0 |  |

#### 指標の記録｜—｜②-7 教科書の役割

- いまの値：`{"区分": null, "出どころ": "語の数だけ（弱い）", "札": "ボラ"}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | （9種の文書の Q1 の行。値の欄は無い） | "Because Bollinger Bands are based on the standard deviation, falling BandWidth reflects decreasing volatility and rising BandWidth reflects increasing volatility."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q1（255行目） |  |
| 2 | （9種の文書の Q1 の行。値の欄は無い） | "BandWidth tells us how wide the Bollinger Bands are. The raw width is normalized using the middle band. Using the default parameters BandWidth is four times the coefficient of variation."<br>https://www.bollingerbands.com/bollinger-band-rules | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q1（256行目） |  |
| 3 | 値動きの幅 | Because Bollinger Bands are based on the standard deviation, falling BandWidth reflects decreasing volatility and risi<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB幅 の 教科書の役割.0 | 逐語は文の途中で切れている（ページでは同じ語の続きが在る） |

#### 指標の記録｜—｜②-11 閾値の範囲

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 8〜12か月の範囲の下端 | "For example, an eight- to 12-month chart will show BandWidth highs and lows over a significant timeframe. BandWidth is considered narrow as it approaches the lows of this range and wide as it approaches the high end."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | レンジ | 値を挙げただけ | 9種の文書 4 Q4（294行目） |  |

#### 使い方の記録｜入る合図｜③-2 使い方の種類

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 入る合図 | "A new decline starts with a Squeeze and subsequent break below the lower band."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q2（265行目） | 前の照らしの「指標データに行が無い使い方」に在る逐語。9種の文書の書き込み「ショート」 |

#### 使い方の記録｜入る合図｜③-3 場面と型

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-5 閾値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-2 使い方の種類

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 場面の判定 | "The bands narrow as price flattens or moves within a relatively narrow range."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 4 Q2（264行目） | 前の照らしの「指標データに行が無い使い方」に在る逐語。9種の文書の書き込み「レンジ」 |
| 2 | 場面の判定 | With this in mind, the major trading signal generated by Bollinger BandWidth is known as The Squeeze.<br>https://www.tradingview.com/support/solutions/43000501972-bollinger-bandwidth-bbw/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB幅 の 使い方.0 | 前の照らしの「指標データに行が無い使い方」に在る逐語 |

#### 使い方の記録｜場面の判定｜③-3 場面と型

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | レンジ（9種の文書の書き込み「レンジ」） | "The bands narrow as price flattens or moves within a relatively narrow range."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 4 Q2（264行目） | 9種の文書の書き込み「レンジ」 |
| 2 | レンジ | With this in mind, the major trading signal generated by Bollinger BandWidth is known as The Squeeze.<br>https://www.tradingview.com/support/solutions/43000501972-bollinger-bandwidth-bbw/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB幅 の 使い方.0 |  |

#### 使い方の記録｜場面の判定｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-5 閾値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-3 場面と型

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | レンジ（9種の文書の書き込み「レンジ→ショート」） | "The chart below shows Honeywell (HON) with an extended trading range in the $50–$55 area. ... HON clearly broke below the lower band to trigger a bearish signal in June 2007."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | レンジ・ショート |  | 9種の文書 4 Q2（267行目） | 9種の文書の書き込み「レンジ→ショート」。逐語は2つの断片（「…」か複数の引用）。断片ごとに本文に在る |

#### 使い方の記録｜書いてない｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-5 閾値

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 過去と比べる | "Narrow BandWidth is relative. BandWidth values should be gauged relative to prior BandWidth values over a period of time."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q4（293行目） |  |
| 2 | 銘柄ごとに違う（例 9%） | "BBW drops. (In the example below, the threshold is 9% however this changes from security to security and timeframe to timeframe)."<br>https://www.tradingview.com/support/solutions/43000501972-bollinger-bandwidth-bbw/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q4（295行目） |  |
| 3 | 例 10・8 | "BandWidth dipped below 10 to put the Squeeze play on in mid-June." / "This line marks 8, which is deemed relatively low based on the historical range."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | レンジ |  | 9種の文書 4 Q4（296行目） | 逐語は2つの断片（「…」か複数の引用）。断片ごとに本文に在る |
| 4 | 回数（5日以上） | "This scan reveals stocks whose Bollinger Bands just expanded rapidly after being contracted for 5 or more days."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 4 Q4（297行目） |  |
| 5 | {"形": "前提つき", "値": 9, "意味": "締まり（Squeeze）の線。銘柄と時間足で変わる"} | BBW drops. (In the example below, the threshold is 9% however this changes from security to security and timeframe to timeframe).<br>https://www.tradingview.com/support/solutions/43000501972-bollinger-bandwidth-bbw/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB幅 の 閾値.0 |  |
| 6 | {"形": "前提つき", "値": null, "意味": "狭さはその銘柄の過去の値と比べて決める"} | Narrow BandWidth is relative. BandWidth values should be gauged relative to prior BandWidth values over a period of time.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB幅 の 閾値.1 |  |

#### 使い方の記録｜書いてない｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

### BB%b（欄 38・候補 30・候補が無い欄 28）

#### 指標の記録｜—｜②-4 パラメータの軸 n と s のスキャルの代表の値

- いまの値：`{"n": [20], "s": [2]}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | [20, 2] | Bollinger Bands settings for a 1-minute chart are a 20-period simple moving average (middle band) and two outer bands set at a standard deviation level of 2 from the middle band.<br>https://fxopen.com/blog/en/1-minute-scalping-trading-strategies-with-examples/ | ページに在る | 1-minute chart | 短い足 |  | 全指標の調べ out_c6_01.json の BB%b の パラメータの軸.0.スキャル.0 | 調べの軸の名前：n（移動平均と標準偏差の本数）・k（標準偏差の倍率）。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 2 | [20, 2] | RSI (2 or 3), EMA 9, and Bollinger Bands (20, 2) for scalping at 1 minute.<br>https://www.mc2.fi/blog/best-rsi-for-scalping | ページに在る | 1 minute | スキャル・短い足 |  | 全指標の調べ out_c6_01.json の BB%b の パラメータの軸.0.スキャル.1 | 調べの軸の名前：n（移動平均と標準偏差の本数）・k（標準偏差の倍率）。調べの注：資料の表の値と逐語。ページの本文で照らした |

#### 指標の記録｜—｜②-4 パラメータの軸 n と s の既定（スキャルの値が教科書に無いときに使う値・欄の外）

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 既定 (20, 2) | "The default setting for %B is based on the default setting for Bollinger Bands (20,2)."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 5 Q3（332行目） | 9種の文書の値は軸を分けずに書いてある（組の値か、どちらか1つの軸の値） |
| 2 | 既定 20・2 | "20 days is the default." / "2 is the default."<br>https://www.tradingview.com/support/solutions/43000501971-bollinger-bands-b-b/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 5 Q3（333行目） | 9種の文書の値は軸を分けずに書いてある（組の値か、どちらか1つの軸の値）。逐語は2つの断片（「…」か複数の引用）。断片ごとに本文に在る |
| 3 | [20, 2] | The default setting for %B is based on the default setting for Bollinger Bands (20,2).<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB%b の パラメータの軸.0.既定.0 | 調べの軸の名前：n（移動平均と標準偏差の本数）・k（標準偏差の倍率）。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 4 | [20, 2] | 9. The default parameters of 20 periods for the moving average and standard deviation calculations, and two standard deviations for the width of the bands are just that, defaults. The actual parameters needed for any given market/task may be different.<br>https://www.bollingerbands.com/bollinger-band-rules | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB%b の パラメータの軸.0.既定.1 | 調べの軸の名前：n（移動平均と標準偏差の本数）・k（標準偏差の倍率）。調べの注：資料の表の値と逐語。ページの本文で照らした |
| 5 | n 20 | The time period to be used in calculating the SMA which creates the base for the Upper and Lower Bands. 20 days is the default.<br>https://www.tradingview.com/support/solutions/43000501971-bollinger-bands-b-b/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB%b の パラメータの軸.0.既定.2 | 調べの軸の名前：n（移動平均と標準偏差の本数）・k（標準偏差の倍率）。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |
| 6 | k 2 | The number of Standard Deviations away from the SMA that the Upper and Lower Bands should be. 2 is the default.<br>https://www.tradingview.com/support/solutions/43000501971-bollinger-bands-b-b/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB%b の パラメータの軸.0.既定.3 | 調べの軸の名前：n（移動平均と標準偏差の本数）・k（標準偏差の倍率）。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |
| 7 | [20, 2] | upperband, middleband, lowerband = BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)<br>https://ta-lib.github.io/ta-lib-python/func_groups/overlap_studies.html | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB%b の パラメータの軸.0.既定.4 | 調べの軸の名前：n（移動平均と標準偏差の本数）・k（標準偏差の倍率）。調べの注：資料の表の値と逐語。ページの本文で照らした |

#### 指標の記録｜—｜②-4 パラメータの軸 n と s の範囲

- いまの値：`{"n": {"kind": "int", "lo": 10, "hi": 50}, "s": {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | (10, 1.9)〜(20, 2)〜(50, 2.1) | 11. For consistent price containment: If the average is lengthened the number of standard deviations needs to be increased; from 2 at 20 periods, to 2.1 at 50 periods. Likewise, if the average is shortened the number of standard deviations should be reduced; from 2 at 20 periods, to 1.9 at 10 periods.<br>https://www.bollingerbands.com/bollinger-band-rules | ページに在る | 時間足は書いてない | 一般 | 値を挙げただけ | 全指標の調べ out_c6_01.json の BB%b の パラメータの軸.0.範囲.0 | 調べの軸の名前：n（移動平均と標準偏差の本数）・k（標準偏差の倍率）。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |
| 2 | (50, 2.1)（長い時間枠）・(10, 1.9)（短い時間枠） | A Bollinger Band overlay can be set at (50,2.1) for a longer timeframe or at (10,1.9) for a shorter timeframe.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/bollinger-bands | ページに在る | longer timeframe・shorter timeframe | 一般 | 値を挙げただけ | 全指標の調べ out_c6_01.json の BB%b の パラメータの軸.0.範囲.1 | 調べの軸の名前：n（移動平均と標準偏差の本数）・k（標準偏差の倍率）。調べの注：資料の表の値と逐語。ページの本文で照らした。1サイトだけ |

#### 指標の記録｜—｜②-4 パラメータの軸 n のスキャルの代表の値

- いまの値：`[20]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 5 Q3（335行目））＝「%B だけの短い足の値｜%B を名指しした 5分足・スキャルの値｜—｜✗ 見つからなかった」

#### 指標の記録｜—｜②-4 パラメータの軸 n の範囲

- いまの値：`{"kind": "int", "lo": 10, "hi": 50}`
- 候補：無い。理由＝9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 指標の記録｜—｜②-4 パラメータの軸 s のスキャルの代表の値

- いまの値：`[2]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 5 Q3（335行目））＝「%B だけの短い足の値｜%B を名指しした 5分足・スキャルの値｜—｜✗ 見つからなかった」

#### 指標の記録｜—｜②-4 パラメータの軸 s の範囲

- いまの値：`{"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}`
- 候補：無い。理由＝9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 指標の記録｜—｜②-5 値の単位と値域

- いまの値：`{"値域": {"有界": null, "分位": [0.0, 1.0]}}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | {"単位": "書いてない", "下限": 0, "上限": 1} | %B is between .50 and 1 when price is between the upper and middle band (20-day SMA)<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | ページに在る | 20-day | 一般 |  | 全指標の調べ out_c6_01.json の BB%b の 値の単位と値域.1 |  |

#### 指標の記録｜—｜②-6 値の読み方

- いまの値：`{"区分": "順張り値", "読み方": "", "向きを持つ": true, "性質": ["trend"]}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | （9種の文書の Q1 の行。値の欄は無い） | "%b tells us where we are in relation to the Bollinger Bands."<br>https://www.bollingerbands.com/bollinger-band-rules | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 5 Q1（310行目） |  |
| 2 | （9種の文書の Q1 の行。値の欄は無い） | "The %B Indicator measures a security's price in relation to the upper and lower Bollinger Bands. You can use it to identify overbought or oversold conditions and gauge trend strength."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 5 Q1（311行目） |  |
| 3 | {"読み方": "1 より上は上の帯より上、0 より下は下の帯より下、0.5 が中央", "向きを持つ": "持つ"} | %b Above 1 = Price is Above the Upper Band / %b Below 0 = Price is Below the Lower Band<br>https://www.tradingview.com/support/solutions/43000501971-bollinger-bands-b-b/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB%b の 値の読み方.0 | 逐語は「 / 」でつないだ2つ以上の行。行ごとに本文に在る（1つの文としては無い） |

#### 指標の記録｜—｜②-7 教科書の役割

- いまの値：`{"区分": null, "出どころ": "語の数だけ（弱い）", "札": "オシレーター"}`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | （9種の文書の Q1 の行。値の欄は無い） | "%b tells us where we are in relation to the Bollinger Bands."<br>https://www.bollingerbands.com/bollinger-band-rules | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 5 Q1（310行目） |  |
| 2 | （9種の文書の Q1 の行。値の欄は無い） | "The %B Indicator measures a security's price in relation to the upper and lower Bollinger Bands. You can use it to identify overbought or oversold conditions and gauge trend strength."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 5 Q1（311行目） |  |
| 3 | 位置 | The %B Indicator measures a security's price in relation to the upper and lower Bollinger Bands.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB%b の 教科書の役割.0 |  |

#### 指標の記録｜—｜②-11 閾値の範囲

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 5 Q4（348行目））＝「短い足の値｜5分足や暗号資産の %B の閾値｜—｜✗ 見つからなかった」

#### 使い方の記録｜入る合図｜③-2 使い方の種類

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 入る合図 | You can use it to identify overbought or oversold conditions and gauge trend strength.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB%b の 使い方.0 |  |

#### 使い方の記録｜入る合図｜③-3 場面と型

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-5 閾値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜入る合図｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-2 使い方の種類

- いまの値：`["前提崩れの印"]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方を書いた逐語が無い（指標データの行は、教科書でない出どころから写した物）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-3 場面と型

- いまの値：`[{"場面": "レンジ", "型": "flat_up"}]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-4 向き

- いまの値：`["上側"]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-5 閾値

- いまの値：`[[{"形": "値", "代表の値": {"スキャル": 1.0129892}, "出どころ": "identity_s1_legacy.json:51"}]]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-6 パラメータの代表の値

- いまの値：`[{"n": {"スキャル": [20]}, "s": {"スキャル": [2.0]}}]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-7 時間足

- いまの値：`[["5m"]]`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜前提崩れの印｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-2 使い方の種類

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 場面の判定 | The strength of the trend can also be determined by how closely prices follow the upper Bollinger Band in a strong uptrend, or the lower Bollinger Band in a strong downtrend.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/bollinger-bands | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB%b の 使い方.1 |  |

#### 使い方の記録｜場面の判定｜③-3 場面と型

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 上げ | The strength of the trend can also be determined by how closely prices follow the upper Bollinger Band in a strong uptrend, or the lower Bollinger Band in a strong downtrend.<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/bollinger-bands | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB%b の 使い方.1 |  |

#### 使い方の記録｜場面の判定｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-5 閾値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜場面の判定｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-3 場面と型

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 5 Q2（324行目））＝「（レンジ）｜%B をレンジの相場でどう使うか｜—｜✗ 見つからなかった（SC-PB・TV-PB・BB-R のどれにも書いてない。TV-PB は "It is typically best to look for trading signals generated by the %b during strong or clearly defined uptrends or downtrends." と書く）」

#### 使い方の記録｜書いてない｜③-4 向き

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-5 閾値

- いまの値：`null`

| # | 値 | 逐語 | ページの確かめ | 時間足 | 名指し | 範囲の形 | 出どころ | 注 |
|---|---|---|---|---|---|---|---|---|
| 1 | 逐語の数：1 | "In a strong downtrend, %B can be considered overbought when it approaches or exceeds 1."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 5 Q2（320行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない）。9種の文書の書き込み「ショート」 |
| 2 | 逐語の数：0.20・10・20 | "Downtrends are identified when %B is below 0.20 and MFI(10) is below 20."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 5 Q2（321行目） | 値は逐語に在る数を写した（閾値かどうかの読みは入れていない）。9種の文書の書き込み「ショート」 |
| 3 | 1・0・0.5 | "%B equals 1 when price is at the upper band" / "%B equals 0 when price is at the lower band" / "%B is between 0 and .50 when price is between the lower and middle band (20-day SMA)"<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | ページに在る | 20-day | 一般 |  | 9種の文書 5 Q4（343行目） | 逐語は3つの断片（「…」か複数の引用）。断片ごとに本文に在る |
| 4 | 0.80／0.20 | "Generally speaking .80 and .20 are also relevant levels."<br>https://www.tradingview.com/support/solutions/43000501971-bollinger-bands-b-b/ | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 5 Q4（344行目） |  |
| 5 | 0.80／0.20 | "Readings above .80 indicate that price is near the upper band. Readings below .20 indicate that price is near the lower band."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 5 Q4（345行目） |  |
| 6 | 0.80＋MFI 80（前提つき） | "An uptrend begins when %B is above .80 and MFI(10) is above 80."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 5 Q4（346行目） |  |
| 7 | 固定の閾値を無くす使い方 | "Indicators can be normalized with %b, eliminating fixed thresholds in the process. To do this plot 50-period or longer Bollinger Bands on an indicator and then calculate %b of the indicator."<br>https://www.bollingerbands.com/bollinger-band-rules | ページに在る | 時間足は書いてない | 一般 |  | 9種の文書 5 Q4（347行目） |  |
| 8 | {"形": "値", "値": [1, 0], "意味": "上の帯・下の帯"} | %b Above 1 = Price is Above the Upper Band / %b Below 0 = Price is Below the Lower Band<br>https://www.tradingview.com/support/solutions/43000501971-bollinger-bands-b-b/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB%b の 閾値.0 | 逐語は「 / 」でつないだ2つ以上の行。行ごとに本文に在る（1つの文としては無い） |
| 9 | {"形": "値", "値": 0.5, "意味": "中央の線"} | %b Above .50 = Price is Above the Middle Line<br>https://www.tradingview.com/support/solutions/43000501971-bollinger-bands-b-b/ | ページに在る | 時間足は書いてない | 一般 |  | 全指標の調べ out_c6_01.json の BB%b の 閾値.1 |  |

#### 使い方の記録｜書いてない｜③-6 パラメータの代表の値

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-7 時間足

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

#### 使い方の記録｜書いてない｜③-9 合図の形のパラメータ

- いまの値：`null`
- 候補：無い。理由＝9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）

## 4. 候補が1つも無い欄の一覧

124 欄です。

| 指標 | 記録 | 使い方の種類 | 欄 | 理由 |
|---|---|---|---|---|
| RSI | 指標の記録 | — | ②-11 閾値の範囲 | 9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 1 Q4（137行目））＝「閾値の範囲｜閾値の範囲を1つの文で書いたページ｜—｜—｜✗ 見つからなかった（書いてある値は 60/40〜80/20）」 |
| RSI | 使い方の記録 | 入る合図 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 入る合図 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 入る合図 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 出口の反転 | ③-2 使い方の種類 | 9種の文書と全指標の調べに、この使い方を書いた逐語が無い（指標データの行は、教科書でない出どころから写した物）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 出口の反転 | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 出口の反転 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 出口の反転 | ③-5 閾値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 出口の反転 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 出口の反転 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 出口の反転 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 前提崩れの印 | ③-2 使い方の種類 | 9種の文書と全指標の調べに、この使い方を書いた逐語が無い（指標データの行は、教科書でない出どころから写した物）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 前提崩れの印 | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 前提崩れの印 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 前提崩れの印 | ③-5 閾値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 前提崩れの印 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 前提崩れの印 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 前提崩れの印 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| RSI | 使い方の記録 | 書いてない | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 指標の記録 | — | ②-11 閾値の範囲 | 9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 2 Q4（197行目））＝「閾値の範囲｜閾値の範囲を書いたページ｜—｜—｜✗ 見つからなかった（書いてある値は 15〜30。TRT-ADX は 15 と 30 を「動かすときの例」として書く）」 |
| ADX | 使い方の記録 | 入ってはいけない場面を除く条件 | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 入ってはいけない場面を除く条件 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 入ってはいけない場面を除く条件 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 入ってはいけない場面を除く条件 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 入ってはいけない場面を除く条件 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 出口の反転 | ③-2 使い方の種類 | 9種の文書と全指標の調べに、この使い方を書いた逐語が無い（指標データの行は、教科書でない出どころから写した物）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 出口の反転 | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 出口の反転 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 出口の反転 | ③-5 閾値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 出口の反転 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 出口の反転 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 出口の反転 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 前提崩れの印 | ③-2 使い方の種類 | 9種の文書と全指標の調べに、この使い方を書いた逐語が無い（指標データの行は、教科書でない出どころから写した物）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 前提崩れの印 | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 前提崩れの印 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 前提崩れの印 | ③-5 閾値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 前提崩れの印 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 前提崩れの印 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 前提崩れの印 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 場面の判定 | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 場面の判定 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 場面の判定 | ③-5 閾値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 場面の判定 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 場面の判定 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 場面の判定 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 書いてない | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 2 Q2（163行目））＝「ショートで ADX の値のどちら側を使うか｜ADX の値をショート用に上と下で分けて書いたページ｜—｜✗ 見つからなかった（どのページも、ADX は向きを持たないと書く）」 |
| ADX | 使い方の記録 | 書いてない | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 書いてない | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 書いてない | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| ADX | 使い方の記録 | 書いてない | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 指標の記録 | — | ②-4 パラメータの軸 n のスキャルの代表の値 | 9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 3 Q3（233行目））＝「スキャル・デイトレ・範囲｜DI の期間だけの値｜—｜—｜✗ 見つからなかった」 |
| DI差 | 指標の記録 | — | ②-11 閾値の範囲 | 9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 3 Q4（243行目））＝「DI差の大きさの閾値｜DI差の大きさ（例＝差が 10 より大きい）を書いたページ｜—｜—｜✗ 見つからなかった」 |
| DI差 | 使い方の記録 | 入ってはいけない場面を除く条件 | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 入ってはいけない場面を除く条件 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 入ってはいけない場面を除く条件 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 入ってはいけない場面を除く条件 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 入ってはいけない場面を除く条件 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 入る合図 | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 入る合図 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 入る合図 | ③-5 閾値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 入る合図 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 入る合図 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 入る合図 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 前提崩れの印 | ③-2 使い方の種類 | 9種の文書と全指標の調べに、この使い方を書いた逐語が無い（指標データの行は、教科書でない出どころから写した物）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 前提崩れの印 | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 前提崩れの印 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 前提崩れの印 | ③-5 閾値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 前提崩れの印 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 前提崩れの印 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 前提崩れの印 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 場面の判定 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 場面の判定 | ③-5 閾値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 場面の判定 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 場面の判定 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 場面の判定 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 書いてない | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| DI差 | 使い方の記録 | 書いてない | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 指標の記録 | — | ②-4 パラメータの軸 n のスキャルの代表の値 | 9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 指標の記録 | — | ②-4 パラメータの軸 n の範囲 | 9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 指標の記録 | — | ②-4 パラメータの軸 s のスキャルの代表の値 | 9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 指標の記録 | — | ②-4 パラメータの軸 s の範囲 | 9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 入る合図 | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 入る合図 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 入る合図 | ③-5 閾値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 入る合図 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 入る合図 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 入る合図 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 場面の判定 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 場面の判定 | ③-5 閾値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 場面の判定 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 場面の判定 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 場面の判定 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 書いてない | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 書いてない | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 書いてない | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB幅 | 使い方の記録 | 書いてない | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 指標の記録 | — | ②-4 パラメータの軸 n のスキャルの代表の値 | 9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 5 Q3（335行目））＝「%B だけの短い足の値｜%B を名指しした 5分足・スキャルの値｜—｜✗ 見つからなかった」 |
| BB%b | 指標の記録 | — | ②-4 パラメータの軸 n の範囲 | 9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 指標の記録 | — | ②-4 パラメータの軸 s のスキャルの代表の値 | 9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 5 Q3（335行目））＝「%B だけの短い足の値｜%B を名指しした 5分足・スキャルの値｜—｜✗ 見つからなかった」 |
| BB%b | 指標の記録 | — | ②-4 パラメータの軸 s の範囲 | 9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 指標の記録 | — | ②-11 閾値の範囲 | 9種の文書と全指標の調べに、この欄の値を書いた逐語が無い（「見つからなかった」と書いた行だけが在る物を含む）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 5 Q4（348行目））＝「短い足の値｜5分足や暗号資産の %B の閾値｜—｜✗ 見つからなかった」 |
| BB%b | 使い方の記録 | 入る合図 | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 入る合図 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 入る合図 | ③-5 閾値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 入る合図 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 入る合図 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 入る合図 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 前提崩れの印 | ③-2 使い方の種類 | 9種の文書と全指標の調べに、この使い方を書いた逐語が無い（指標データの行は、教科書でない出どころから写した物）。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 前提崩れの印 | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 前提崩れの印 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 前提崩れの印 | ③-5 閾値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 前提崩れの印 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 前提崩れの印 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 前提崩れの印 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 場面の判定 | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 場面の判定 | ③-5 閾値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（閾値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 場面の判定 | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 場面の判定 | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 場面の判定 | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 書いてない | ③-3 場面と型 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（場面と型）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった）。9種の文書の行（9種の文書 5 Q2（324行目））＝「（レンジ）｜%B をレンジの相場でどう使うか｜—｜✗ 見つからなかった（SC-PB・TV-PB・BB-R のどれにも書いてない。TV-PB は "It is typically best to look for trading signals generated by the %b during strong or clearly defined uptrends or downtrends." と書く）」 |
| BB%b | 使い方の記録 | 書いてない | ③-4 向き | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（向き）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 書いてない | ③-6 パラメータの代表の値 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（パラメータの代表の値）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 書いてない | ③-7 時間足 | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（時間足）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |
| BB%b | 使い方の記録 | 書いてない | ③-9 合図の形のパラメータ | 9種の文書と全指標の調べに、この使い方の種類の逐語でこの欄の値（合図の形のパラメータ）を書いた文が無い。新しいページは探していない（依頼書は「探してかまいません」で、探すことは決まりではないため。時間の都合で探さなかった） |

## 5. 確かめられなかった物と、その理由

- WebFetch では開いていない。54本とも curl で HTTP 200 を返したため、curl の本文だけで照らした（https://www.bollingerbands.com/bollinger-bands は1回目が 429 で、20秒おいた2回目に 200）。
- 9種の文書が「404 で開けない」と書いた2ページ（marketclutch.com の ATR の記事・litefinance.org の Bollinger の記事）が、9種の文書が開いた日に 404 だったかは、確かめられない。今日は2本とも開け、全指標の調べの逐語は本文に在った。
- 9種の文書 7 Q3（440行目）の「LF-ICHI の今のページには day trading の語が無い」も、9種の文書が開いた日のページは確かめられない。今日のページには在る。
- 9種の文書の行のうち、逐語が無い 25 行（「見つからなかった」の記録と、「上の行と同じ文」の参照）は、ページで照らす文が無いので照らしていない。「見つからなかった」の記録は、候補が無い欄の理由に写した。
- 候補が1つも無い欄で、新しいページは探していない。依頼書は「探してかまいません」で、探すことは決まりではない。時間の都合で探さなかった。
- ページは curl で取った HTML の文字で照らした。ブラウザで画面に出る文と、HTML の中の文が違うページ（あとから文を書き替える作りのページ）が在れば、その違いは見ていない。
- 名指しと時間足は、逐語の中の語を探して決めた。語の意味（たとえば true range の range）は見ていない。

## 6. 始めた時刻と終えた時刻

- 始めた時刻：2026-11-04 08:57:15 UTC（date -u）。この時刻のあと、プッシュが 403 で止まり、いったん作業を終えた。リポジトリに書き込みの権限が付いた後、2026-11-04 08:59:44 UTC（date -u）に、ブランチを作ってプッシュできることを確かめてから、調べを始めた
- 終えた時刻：（終えたときに書く）
