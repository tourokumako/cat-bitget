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

（まだ作っていない。9種の1種ごとに足す）
## 4. 候補が1つも無い欄の一覧

（候補の表を作った後に書く）

## 5. 確かめられなかった物と、その理由

- （候補の表を作った後に書く）

## 6. 始めた時刻と終えた時刻

- 始めた時刻：2026-11-04 08:57:15 UTC（date -u）。この時刻のあと、プッシュが 403 で止まり、いったん作業を終えた。リポジトリに書き込みの権限が付いた後、2026-11-04 08:59:44 UTC（date -u）に、ブランチを作ってプッシュできることを確かめてから、調べを始めた
- 終えた時刻：（終えたときに書く）
