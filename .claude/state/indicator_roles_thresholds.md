<!-- INDICATOR_ROLES_THRESHOLDS build_role_threshold_table.py が自動生成＝手で書き換えない -->
# 指標の役割と閾値（出どころと、今の役割を並べた表）

- 出どころ＝調べる係の結果（封つき・逐語をページで照らして一致したものだけ）と、出どころのページから語の決まりで抜いた文。CC は値も文も書いていない。
- 「今の答える問いの区分」＝系統ごとに1つ付けている答える問い（トレンド＝向き・オシレーター＝行き過ぎ・ボラ＝値動きの幅・出来高＝出来高・構造位置＝位置）。
- 役割の印＝「食い違い」は係の調べで確かめた役割に今の区分が無いもの。「食い違いの疑い」は語の数だけで見たもの（確かめは弱い）。
- 閾値の数字は、その数字が逐語に数字で書いてあるものだけ（文から数字への読み替えは使わない）。

| 数 | 件数 |
|---|---|
| 役割が出どころで確かめられた | 89 |
| 役割が食い違う | 30 |
| 役割が食い違う疑い（語の数だけ） | 34 |
| 閾値が数字で確かめられた | 14 |
| 閾値は文だけ | 119 |
| 閾値が無い | 52 |

| 種類 | 今の系統（答える問いの区分） | 今の向き | 出どころの役割 | 役割の印 | 閾値 |
|---|---|---|---|---|---|
| ADX | トレンド（向き） | 状態量＝大きいほどトレンドが強い（向きは持たない） | 出どころのページの語の数：強さ17・向き8・位置5・出来高3・値動きの幅1・勢い1 | 食い違いの疑い | 文 24 件（例＝the calculation example below is based on a 14-period indicator setting, as recommended by wilder.） |
| DI差 | トレンド（向き） | 順張り値＝プラスで上昇方向が優勢 | 出どころのページの語の数：強さ17・向き8・位置5・出来高3・値動きの幅1・勢い1 | 食い違いの疑い | 文 24 件（例＝a general interpretation would be that during a strong trend (adx above 25 but dependent on the analyst's interpretation） |
| MACD線% | トレンド（向き） | 順張り値＝プラスで上昇の勢い | 出どころのページの語の数：勢い27・向き10・行き過ぎ5・位置5・強さ4・値動きの幅1 | 食い違いの疑い | 文 15 件（例＝these crossovers signal that the 12-day ema has crossed the 26-day ema.） |
| MACDヒスト% | トレンド（向き） | 順張り値＝プラスで勢いが加速 | 出どころのページの語の数：勢い27・向き10・行き過ぎ5・位置5・強さ4・値動きの幅1 | 食い違いの疑い | 文 15 件（例＝these crossovers signal that the 12-day ema has crossed the 26-day ema.） |
| MACDシグナル線% | トレンド（向き） | 順張り値＝プラスで上昇の勢いが持続 | 出どころのページの語の数：勢い27・向き10・行き過ぎ5・位置5・強さ4・値動きの幅1 | 食い違いの疑い | 文 15 件（例＝these crossovers signal that the 12-day ema has crossed the 26-day ema.） |
| 転換線 | トレンド（向き） | 順張り値 | 出どころのページの語の数：向き27・位置14・勢い4・行き過ぎ4・出来高2・強さ1 |  | 文 5 件（例＝leading span b on the daily chart, this line is the midpoint of the 52-day high-low range, which is a little less than t） |
| 基準線 | トレンド（向き） | 順張り値 | 出どころのページの語の数：向き27・位置14・勢い4・行き過ぎ4・出来高2・強さ1 |  | 文 5 件（例＝leading span b on the daily chart, this line is the midpoint of the 52-day high-low range, which is a little less than t） |
| EMA傾き | トレンド（向き） | 順張り値 | 出どころのページの語の数：位置15・向き11・出来高7・強さ5・行き過ぎ1 |  | 文 32 件（例＝ema = closing price x multiplier + ema (previous day) x (1-multiplier) takeaways similar to other moving averages, the e） |
| AO% | トレンド（向き） | 順張り値＝プラスで上昇の勢い | 出どころのページの語の数：勢い8 | 食い違いの疑い | 文 1 件（例＝calculation lengthao1=input(5, minval=1) //5 periods lengthao2=input(34, minval=1) //34 periods ao = sma((high+low)/2, l） |
| KST | トレンド（向き） | 順張り値 | 係の調べ（逐語✅）：勢い | 食い違い | 文 6 件（例＝chart 1 the formula box below shows the four different combinations with their default settings.） |
| KSTシグナル | トレンド（向き） | 順張り値 | 係の調べ（逐語✅）：勢い | 食い違い | 文 6 件（例＝chart 1 the formula box below shows the four different combinations with their default settings.） |
| PPO | トレンド（向き） | 順張り値 | 係の調べ（逐語✅）：勢い | 食い違い | 文 10 件（例＝the table below shows intel (intc) with values for the 12-day ema, 26-day ema, macd and ppo.） |
| PPOシグナル | トレンド（向き） | 順張り値 | 係の調べ（逐語✅）：勢い | 食い違い | 文 10 件（例＝the table below shows intel (intc) with values for the 12-day ema, 26-day ema, macd and ppo.） |
| PPOヒスト | トレンド（向き） | 順張り値＝プラスで勢いが加速 | 係の調べ（逐語✅）：勢い | 食い違い | 文 10 件（例＝the table below shows intel (intc) with values for the 12-day ema, 26-day ema, macd and ppo.） |
| STC | トレンド（向き） | 順張り値 | 係の調べ（逐語✅）：向き |  | 既定：[25, 75]（25 の下から上へ向けば bullish・75 の上から下へ向けば bearish）［順位3］<br>既定：[25, 75]（25 を上へ＝buy・75 を下へ＝sell）［順位4］<br>スキャル：[25, 75]（Scalping（5M crypto）の Signal Levels 25/75）［順位4］<br>デイトレ：[25]（15分足で 25 が cycle bottom）［順位4］ |
| STCstoch | トレンド（向き） | 順張り値 | 係の調べ（逐語✅）：勢い | 食い違い | 文 1 件（例＝bounded 0 to 100, read against 25 and 75: turning up from below 25 is bullish, turning down from above 75 bearish.） |
| TRIX | トレンド（向き） | 順張り値 | 出どころのページの語の数：勢い21・位置6・向き5・出来高3・値動きの幅1 | 食い違いの疑い | 文 10 件（例＝single-smoothed ema = 15-period ema of the closing price double-smoothed ema = 15-period ema of single-smoothed ema trip） |
| TRIXシグナル | トレンド（向き） | 順張り値 | 出どころのページの語の数：勢い12・向き5・位置5・出来高3・値動きの幅1 | 食い違いの疑い | 文 10 件（例＝single-smoothed ema = 15-period ema of the closing price double-smoothed ema = 15-period ema of single-smoothed ema trip） |
| TRIXヒスト | トレンド（向き） | 状態量＝加速（向きを持たない） | 出どころのページの語の数：勢い12・向き5・位置5・出来高3・値動きの幅1 | 食い違いの疑い | 文 10 件（例＝single-smoothed ema = 15-period ema of the closing price double-smoothed ema = 15-period ema of single-smoothed ema trip） |
| TSI | トレンド（向き） | 順張り値 | 出どころのページの語の数：勢い18・行き過ぎ10・位置9・強さ4・値動きの幅3・向き1 | 食い違いの疑い | 文 10 件（例＝the example below shows nike (nke) turning bullish in september 2011 as tsi moved into positive territory (green line).） |
| TSIシグナル | トレンド（向き） | 順張り値 | 出どころのページの語の数：勢い8・強さ3・行き過ぎ1 | 食い違いの疑い | 文 1 件（例＝dividing the smoothed signed momentum by the smoothed absolute momentum normalises the reading, so the result is bounded） |
| TSIヒスト | トレンド（向き） | 状態量＝加速（向きを持たない） | 係の調べ（逐語✅）：勢い | 食い違い | 無い |
| KAMA傾き% | トレンド（向き） | 順張り値 | 出どころのページの語の数：向き6・値動きの幅4・位置3・出来高2 |  | 文 9 件（例＝the kroger example below shows kama(10,5,30) with a steep uptrend from december to march and a less-steep uptrend from m） |
| WMA傾き% | トレンド（向き） | 順張り値 | 係の調べ（逐語✅）：向き |  | 無い |
| AROONU | トレンド（向き） | 順張り値 | 出どころのページの語の数：向き13・強さ6・位置6・出来高5・勢い3・行き過ぎ2 |  | 文 48 件（例＝the default parameter setting in sharpcharts is 25 and the example below is based on 25 days.） |
| AROOND | トレンド（向き） | 状態量＝大きいほど直近で安値を付けた | 出どころのページの語の数：向き10・位置3・強さ2・勢い2・行き過ぎ1・出来高1 |  | 文 35 件（例＝the default parameter setting in sharpcharts is 25 and the example below is based on 25 days.） |
| AROONOSC | トレンド（向き） | 順張り値 | 出どころのページの語の数：強さ4・出来高4・向き3・位置3・行き過ぎ1・勢い1 |  | 文 13 件（例＝the sharpcharts default parameter is 25, and the example below is based on the 25-day aroon oscillator.） |
| PSAR加速 | トレンド（向き） | 状態量 | 出どころのページの語の数：向き17・位置3・出来高3 |  | 文 2 件（例＝break above falling sar this scan starts with stocks that have an average price of $10 or greater over the last three mo） |
| VTXP | トレンド（向き） | 順張り値 | 出どころのページの語の数：向き16・位置4・出来高3・値動きの幅2 |  | 文 20 件（例＝every source (the original tasc article, stockcharts, wikipedia, tradingview) states the identical formula; the only cro） |
| VTXM | トレンド（向き） | 状態量＝大きいほど下落方向が強い | 出どころのページの語の数：向き16・位置4・出来高3・値動きの幅2 |  | 文 20 件（例＝every source (the original tasc article, stockcharts, wikipedia, tradingview) states the identical formula; the only cro） |
| RSI | オシレーター（行き過ぎ） | 順張り値＝大きいほど上昇の勢い | 出どころのページの語の数：行き過ぎ40・勢い25・向き15・位置9・値動きの幅3・強さ3・出来高1 |  | 文 36 件（例＝when the rsi is above 70, it generally indicates overbought conditions; when the rsi is below 30, it indicates oversold ） |
| ROC | オシレーター（行き過ぎ） | 順張り値 | 出どころのページの語の数：行き過ぎ34・勢い10・向き9・値動きの幅5・位置5 |  | 文 27 件（例＝rate of change calculation roc - spreadsheet 1 click below to download this spreadsheet example.） |
| Stoch%K | オシレーター（行き過ぎ） | 順張り値 | 出どころのページの語の数：行き過ぎ38・勢い25・向き15・位置15・出来高2・値動きの幅1 |  | 文 48 件（例＝cs-soo.xls 19kb download open stochastics - chart 1 interpreting the stochastic oscillator the stochastic oscillator mea） |
| Stoch%D | オシレーター（行き過ぎ） | 順張り値 | 出どころのページの語の数：行き過ぎ38・勢い25・向き15・位置15・出来高2・値動きの幅1 |  | 文 48 件（例＝cs-soo.xls 19kb download open stochastics - chart 1 interpreting the stochastic oscillator the stochastic oscillator mea） |
| MFI | オシレーター（行き過ぎ） | 順張り値 | 出どころのページの語の数：行き過ぎ30・出来高20・勢い12・位置6・向き4・強さ1 |  | 文 24 件（例＝the example below is based on a 14-period mfi, which is the default setting in sharpcharts and the setting recommended b） |
| CMF | 出来高（出来高） | 順張り値＝プラスで買い圧 | 出どころのページの語の数：出来高22・位置3・向き2・勢い2 |  | 文 18 件（例＝chart with 20-day and 60-day cmf indicators, to assess money flow in multiple timeframes chartists weigh the balance of ） |
| OBV傾き | 出来高（出来高） | 順張り値 | 出どころのページの語の数：出来高37・位置11・向き4・勢い1 |  | 文 4 件（例＝on balance volume calculation example in the table above, volume figures were rounded off and are shown in 1000's.） |
| BB%b | オシレーター（行き過ぎ） | 順張り値 | 出どころのページの語の数：向き36・行き過ぎ24・位置13・勢い7・値動きの幅7・強さ4・出来高3 |  | 文 36 件（例＝the bands are set two standard deviations above and below the 20-day simple moving average , which is also the middle ba） |
| volume_ratio | 出来高（出来高） | 状態量＝大きいほど商いが厚い | 出どころのページの語の数：出来高38・向き6・位置3・行き過ぎ1 |  | 文 10 件（例＝rvol thresholds an rvol value of 1.0 indicates that the current value is exactly the same as the average volume; anythin） |
| CCI | オシレーター（行き過ぎ） | 順張り値 | 出どころのページの語の数：行き過ぎ32・勢い14・向き9・位置7・値動きの幅2・出来高2・強さ1 |  | 文 25 件（例＝calculating cci the example below is based on a 20-period commodity channel index (cci) calculation.） |
| PVO | 出来高（出来高） | 状態量＝出来高の増減（方向は持たない） | 出どころのページの語の数：出来高48・位置13・勢い4 |  | 文 18 件（例＝this means the pvo is positive when the 12-day volume ema moves above the 26-day volume ema.） |
| PVOシグナル | 出来高（出来高） | 状態量 | 出どころのページの語の数：出来高48・位置13・勢い4 |  | 文 18 件（例＝this means the pvo is positive when the 12-day volume ema moves above the 26-day volume ema.） |
| PVOヒスト | 出来高（出来高） | 状態量 | 出どころのページの語の数：出来高48・位置13・勢い4 |  | 文 18 件（例＝this means the pvo is positive when the 12-day volume ema moves above the 26-day volume ema.） |
| StochRSI%K | オシレーター（行き過ぎ） | 順張り値 | 係の調べ（逐語✅）：行き過ぎ |  | スキャル：[0.8, 0.2]（5-Minute：0.8/0.2 levels）［順位4］<br>デイトレ：[0.7, 0.3]（15-Minute：0.7/0.3 levels）［順位4］<br>デイトレ：[0.8, 0.2]（1-Hour：0.8/0.2 levels）［順位4］ |
| StochRSI%D | オシレーター（行き過ぎ） | 順張り値 | 係の調べ（逐語✅）：行き過ぎ |  | スキャル：[0.8, 0.2]（5-Minute：0.8/0.2 levels）［順位4］<br>デイトレ：[0.7, 0.3]（15-Minute：0.7/0.3 levels）［順位4］<br>デイトレ：[0.8, 0.2]（1-Hour：0.8/0.2 levels）［順位4］ |
| UO | オシレーター（行き過ぎ） | 順張り値 | 出どころのページの語の数：勢い14・行き過ぎ13・位置6・値動きの幅3・出来高1 |  | 文 16 件（例＝developed by larry williams in 1976 and featured in stocks & commodities magazine in 1985, the ultimate oscillator is a ） |
| DPO% | オシレーター（行き過ぎ） | 反転サイン | 出どころのページの語の数：勢い4・行き過ぎ3・位置3 |  | 文 8 件（例＝the chart below shows the s&p 500 etf (spy) with a 20-day sma (green dotted line) and a 20-day sma offset 11 days to the） |
| EFI比 | 出来高（出来高） | 順張り値＝プラスで買いの勢力が優勢 | 出どころのページの語の数：出来高22・向き12・位置7・行き過ぎ7 |  | 文 13 件（例＝table 1 - force index the chart above shows the force index in action.） |
| EOM比 | 出来高（出来高） | 順張り値＝プラスで少ない出来高でも上に動きやすい | 出どころのページの語の数：出来高27・位置4・行き過ぎ2・勢い1・向き1 |  | 文 9 件（例＝the example below shows the nasdaq 100 etf (qqq) with the one-period emv in the lower indicator window.） |
| NVI傾き | 出来高（出来高） | 順張り値＝プラスで、商いの薄い足で上げている | 出どころのページの語の数：出来高34・向き2・位置2 |  | 文 10 件（例＝spreadsheet 1 click below to download this spreadsheet example.） |
| PVT傾き | 出来高（出来高） | 順張り値＝プラスで出来高を伴って上げている | 係の調べ（逐語✅）：出来高 |  | 無い |
| ATR% | ボラ（値動きの幅） | ボラ量＝大きいほど荒い | 出どころのページの語の数：値動きの幅29・位置6・強さ2・向き2・出来高1 |  | 文 3 件（例＝the image below shows examples of when methods 2 and 3 are appropriate.） |
| BB幅 | ボラ（値動きの幅） | ボラ量 | 出どころのページの語の数：値動きの幅30・向き13・位置13・勢い7・出来高5・行き過ぎ5・強さ2 |  | 文 25 件（例＝the rules below covering the use of bollinger bands were assembled in response to questions often asked by users and our） |
| realized_vol | ボラ（値動きの幅） | ボラ量 | 係の調べ（逐語✅）：値動きの幅 |  | 無い |
| Donchian幅 | ボラ（値動きの幅） | ボラ量 | 出どころのページの語の数：行き過ぎ37・向き25・値動きの幅7・位置3・出来高2 | 食い違いの疑い | 文 17 件（例＝calculating price channels copy upper channel line: 20-day high lower channel line: 20-day low centerline: (20-day high ） |
| MMI | ボラ（値動きの幅） | 状態量＝方向は持たない（原典の逐語『向きは測りません』） | 出どころのページの語の数：勢い1 |  | 文 11 件（例＝the system does not pass the wrc at the required 95% confidence level.） |
| ER | ボラ（値動きの幅） | 状態量＝方向は持たない | 係の調べ（逐語✅）：強さ | 食い違い | 既定：[30, -30]（100 倍した目盛りで、30 より上は uptrend・-30 より下は downtrend）［順位4］ |
| SQZ_ON | ボラ（値動きの幅） | 状態量 | 係の調べ（逐語✅）：値動きの幅 |  | 無い |
| CHOP | ボラ（値動きの幅） | 状態量＝大きいほどもみ合い（向きは持たない） | 係の調べ（逐語✅）：強さ | 食い違い | 既定：[61.8, 38.2]（61.8 が上の閾値（choppiness territory）・38.2 が下の閾値（trending territory））［順位2］ |
| VHF | ボラ（値動きの幅） | 状態量＝大きいほど一方向（向きは持たない） | 係の調べ（逐語✅）：強さ | 食い違い | 無い |
| MAD比 | ボラ（値動きの幅） | ボラ量 | 係の調べ（逐語✅）：値動きの幅 |  | 無い |
| stdev% | ボラ（値動きの幅） | ボラ量 | 出どころのページの語の数：値動きの幅12・位置2・勢い1・向き1 |  | 文 11 件（例＝standard deviation excel spreadsheet the spreadsheet above shows an example for a 10-period standard deviation using qqq） |
| HWC幅% | ボラ（値動きの幅） | ボラ量 | 係の調べ（逐語✅）：値動きの幅 |  | 無い |
| MASSI | ボラ（値動きの幅） | 状態量＝大きいほど値幅が広がった（向きは持たない） | 係の調べ（逐語✅）：値動きの幅 |  | 既定：[27]（27 を上回ると bulge）［順位2］<br>既定：[27, 26.5]（27 を上回り 26.5 へ下がると方向が変わる用意）［順位2］ |
| THERMO% | ボラ（値動きの幅） | ボラ量 | 係の調べ（逐語✅）：値動きの幅 |  | 既定：[3]（Explosive Move threshold（Thermometer がその EMA の何倍か）の既定 3）［順位4］ |
| TR% | ボラ（値動きの幅） | ボラ量 | 係の調べ（逐語✅）：値動きの幅 |  | 無い |
| UI | ボラ（値動きの幅） | ボラ量 | 出どころのページの語の数：値動きの幅7・位置2・向き1 |  | 文 4 件（例＝the first chart below shows weekly closes for the fidelity select technology fund (fsptx) with the 9-period ulcer index ） |
| swing高値距離 | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 無い |
| swing安値距離 | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 無い |
| 高値からの経過バー | 構造・位置（位置） | 状態量＝経過の量（★一方向に動き続ける相場では向きが出る＝2026-08-06 材料検査の実測。普通の相場では向きの差は四分位幅の半分以下。型の表で向きの材料に使わない・まこさん OK） | 出どころのページの語の数：向き9・位置3・勢い2・強さ1・行き過ぎ1・出来高1 | 食い違いの疑い | 文 35 件（例＝the default parameter setting in sharpcharts is 25 and the example below is based on 25 days.） |
| 安値からの経過バー | 構造・位置（位置） | 状態量＝経過の量（★一方向に動き続ける相場では向きが出る＝2026-08-06 材料検査の実測。普通の相場では向きの差は四分位幅の半分以下。型の表で向きの材料に使わない・まこさん OK） | 出どころのページの語の数：向き9・位置3・勢い2・強さ1・行き過ぎ1・出来高1 | 食い違いの疑い | 文 35 件（例＝the default parameter setting in sharpcharts is 25 and the example below is based on 25 days.） |
| 形スコア | 構造・位置（位置） | 反転サイン | 無い |  | 無い |
| W字 | 構造・位置（位置） | 反転サイン＝1 は買い転換（ダブルボトム完成）の示唆 | 出どころのページの語の数：向き31・出来高25・位置22・強さ4・値動きの幅1 |  | 文 11 件（例＝there were two days when volume on a decline exceeded the 60-day exponential moving average (ema) of volume, and cmf dip） |
| fractal高値距離% | 構造・位置（位置） | 順張り値＝0 に近いほど直近の山に近い | 係の調べ（逐語✅）：位置 |  | 無い |
| fractal安値距離% | 構造・位置（位置） | 順張り値＝0 に近いほど直近の谷に近い | 係の調べ（逐語✅）：位置 |  | 無い |
| 高値切り上げ幅% | 構造・位置（位置） | 順張り値＝プラスで上昇の構造 | 係の調べ（逐語✅）：位置 |  | 無い |
| 安値切り上げ幅% | 構造・位置（位置） | 順張り値＝プラスで上昇の構造・マイナスで下降の構造 | 係の調べ（逐語✅）：位置 |  | 無い |
| 構造破断距離% | 構造・位置（位置） | 順張り値＝マイナスで上げの構造が壊れた | 係の調べ（逐語✅）：位置 |  | 無い |
| close vs EMA | 構造・位置（位置） | 順張り値 | 出どころのページの語の数：位置15・向き11・出来高7・強さ5・行き過ぎ1 |  | 文 32 件（例＝ema = closing price x multiplier + ema (previous day) x (1-multiplier) takeaways similar to other moving averages, the e） |
| close vs SMA | 構造・位置（位置） | 順張り値 | 出どころのページの語の数：位置20・向き11・出来高8・強さ7・勢い1・行き過ぎ1 |  | 文 34 件（例＝for example a 50 day simple moving average (medium-term) and a 200 day simple moving average (long-term) the signals or ） |
| close vs VWAP | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置・向き |  | 文 1 件（例＝the spreadsheet example below shows one-minute vwap for the first 30 minutes of trading in ibm.） |
| Keltner上 | 構造・位置（位置） | 順張り値 | 出どころのページの語の数：行き過ぎ18・向き17・位置7・強さ6・勢い5・値動きの幅4 | 食い違いの疑い | 文 16 件（例＝the channels are typically set two average true range values above and below the 20-day ema.） |
| Keltner下 | 構造・位置（位置） | 順張り値 | 出どころのページの語の数：行き過ぎ18・向き17・位置7・強さ6・勢い5・値動きの幅4 | 食い違いの疑い | 文 16 件（例＝the channels are typically set two average true range values above and below the 20-day ema.） |
| n本高値 | 構造・位置（位置） | 順張り値 | 出どころのページの語の数：行き過ぎ37・向き25・値動きの幅7・位置3・出来高2 | 食い違いの疑い | 文 17 件（例＝calculating price channels copy upper channel line: 20-day high lower channel line: 20-day low centerline: (20-day high ） |
| n本安値 | 構造・位置（位置） | 順張り値 | 出どころのページの語の数：行き過ぎ37・向き25・値動きの幅7・位置3・出来高2 | 食い違いの疑い | 文 17 件（例＝calculating price channels copy upper channel line: 20-day high lower channel line: 20-day low centerline: (20-day high ） |
| pivotPP | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 文 5 件（例＝the "auto" setting selects the following pivot timeframes: 1d for chart resolutions up to and including 15 min 1w for ch） |
| pivotR1 | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 文 5 件（例＝the "auto" setting selects the following pivot timeframes: 1d for chart resolutions up to and including 15 min 1w for ch） |
| pivotS1 | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 文 5 件（例＝the "auto" setting selects the following pivot timeframes: 1d for chart resolutions up to and including 15 min 1w for ch） |
| fib位置 | 構造・位置（位置） | 順張り値 | 出どころのページの語の数：行き過ぎ28・位置13・勢い12・向き6・出来高4 | 食い違いの疑い | 文 48 件（例＝the chart below shows home depot retracing around 50% of its prior advance.） |
| POC | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置・出来高 |  | 文 1 件（例＝for example, to calculate the volume profile for one daily session, the system loads all 1-minute bars that were traded ） |
| VAH | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 文 1 件（例＝for example, to calculate the volume profile for one daily session, the system loads all 1-minute bars that were traded ） |
| VAL | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 文 1 件（例＝for example, to calculate the volume profile for one daily session, the system loads all 1-minute bars that were traded ） |
| S-Rタッチ1時間ATR | 構造・位置（位置） | 状態量＝多いほど節が固い | 出どころのページの語の数：値動きの幅14・位置3・強さ2・向き1 | 食い違いの疑い | 文 2 件（例＝the image below shows examples of when methods 2 and 3 are appropriate.） |
| S-Rタッチ数 | 構造・位置（位置） | 状態量＝多いほど節が固い | 係の調べ（逐語✅）：位置 |  | 無い |
| SMC_SWEEP | 構造・位置（位置） | 反転サイン | 無い |  | 無い |
| close vs ALMA% | 構造・位置（位置） | 反転サイン | 無い |  | 文 2 件（例＝at periods below about 5 this puts it on an older bar: at period 2 the line is almost entirely the previous bar.） |
| close vs DEMA% | 構造・位置（位置） | 反転サイン | 出どころのページの語の数：位置5・出来高2・向き1 |  | 文 7 件（例＝for example, the 20-day dema crossing above the 50-day dema would be a bullish signal.） |
| close vs FWMA% | 構造・位置（位置） | 反転サイン | 無い |  | 無い |
| close vs HILO% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| close vs HMA% | 構造・位置（位置） | 反転サイン | 出どころのページの語の数：向き5・位置3・出来高2 |  | 文 7 件（例＝16 period sma(16 period sma(price)) the bad news is that it causes a huge increase in lag as seen below.） |
| close vs HT_TRENDLINE% | 構造・位置（位置） | 反転サイン | 無い |  | 無い |
| close vs HWMA% | 構造・位置（位置） | 反転サイン | 無い |  | 無い |
| close vs JMA% | 構造・位置（位置） | 反転サイン | 出どころのページの語の数：勢い11・値動きの幅7・位置6・向き4・強さ2・出来高1 |  | 文 9 件（例＝note that jma's crossovers are 15 and 18 days earlier!） |
| close vs KAMA% | 構造・位置（位置） | 反転サイン | 出どころのページの語の数：向き6・値動きの幅5・位置3・出来高2 | 食い違いの疑い | 文 9 件（例＝the kroger example below shows kama(10,5,30) with a steep uptrend from december to march and a less-steep uptrend from m） |
| close vs LINREG% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| close vs LRb% | 構造・位置（位置） | 反転サイン | 出どころのページの語の数：向き2・位置1 | 食い違いの疑い | 無い |
| close vs MAMA% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| close vs FAMA% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| close vs MCGD% | 構造・位置（位置） | 反転サイン | 無い |  | 文 2 件（例＝each bar closes a fraction 1 / (n * (x/md)^4) of the gap to the price: less than rma 's 1/n while the price is above the） |
| close vs MIDPOINT% | 構造・位置（位置） | 反転サイン | 無い |  | 無い |
| close vs MIDPRICE% | 構造・位置（位置） | 反転サイン | 出どころのページの語の数：位置1 |  | 無い |
| close vs MMAR% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| close vs PWMA% | 構造・位置（位置） | 反転サイン | 無い |  | 無い |
| close vs RAINBOW% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| close vs RMA% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 文 1 件（例＝seeding on iloc[0:length] averaged whatever valid values the nan # prefix left (chained input: dx, the dm series), so ev） |
| close vs SINWMA% | 構造・位置（位置） | 反転サイン | 無い |  | 無い |
| close vs SSF% | 構造・位置（位置） | 反転サイン | 無い |  | 文 1 件（例＝sources: http://www.stockspotter.com/files/predictiveindicators.pdf https://www.tradingview.com/script/vdjy0ybj-ehlers-s） |
| close vs SWMA% | 構造・位置（位置） | 反転サイン | 無い |  | 無い |
| close vs T3% | 構造・位置（位置） | 反転サイン | 無い |  | 無い |
| close vs TEMA% | 構造・位置（位置） | 反転サイン | 出どころのページの語の数：出来高4・位置2 | 食い違いの疑い | 文 8 件（例＝for example, a 20-day tema crossing above the 50-day tema would be a bullish signal.） |
| close vs TRIMA% | 構造・位置（位置） | 反転サイン | 出どころのページの語の数：出来高2・位置1 | 食い違いの疑い | 文 1 件（例＝further flags continue from the low end, where all * 24 remaining bits are free (the ta_in_/ta_optin_/ta_out_ flags belo） |
| close vs TSF% | 構造・位置（位置） | 反転サイン＝プラスで予測より高い（順張り値ではない） | 出どころのページの語の数：出来高2・向き1・勢い1・位置1 | 食い違いの疑い | 文 1 件（例＝further flags continue from the low end, where all * 24 remaining bits are free (the ta_in_/ta_optin_/ta_out_ flags belo） |
| close vs VIDYA% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| close vs VWMA% | 構造・位置（位置） | 反転サイン | 出どころのページの語の数：出来高2・位置1 | 食い違いの疑い | 文 1 件（例＝further flags continue from the low end, where all * 24 remaining bits are free (the ta_in_/ta_optin_/ta_out_ flags belo） |
| close vs WMA% | 構造・位置（位置） | 反転サイン | 出どころのページの語の数：位置6・出来高3・強さ2・勢い1・向き1 |  | 文 4 件（例＝for example a 50 day simple moving average (medium-term) and a 200 day simple moving average (long-term) the signals or ） |
| close vs ZLMA% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| close vs CKSPl% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| close vs CKSPs% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| close vs PMAX% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 文 1 件（例＝in this example atr multiplier set to 5000 from 3 different charts will need different unique levels.） |
| close vs PSAR% | 構造・位置（位置） | 反転サイン | 出どころのページの語の数：向き15・出来高3 | 食い違いの疑い | 文 2 件（例＝### break above falling sar this scan starts with stocks that have an average price of $10 or greater over the last thre） |
| PSAR反転 | 構造・位置（位置） | 状態量 | 出どころのページの語の数：向き15・出来高3 | 食い違いの疑い | 文 2 件（例＝### break above falling sar this scan starts with stocks that have an average price of $10 or greater over the last thre） |
| close vs SAREXT% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| close vs MEDIAN% | 構造・位置（位置） | 順張り値 | 無い |  | 無い |
| close vs ABER_ZG% | 構造・位置（位置） | 順張り値＝プラスで中心線より上 | 係の調べ（逐語✅）：値動きの幅 | 食い違い | 文 5 件（例＝notably, quantica has maintained its relatively low volatility with great consistency over the past 20 years (as shown i） |
| ABER位置 | 構造・位置（位置） | 順張り値＝大きいほど帯の上側 | 係の調べ（逐語✅）：値動きの幅 | 食い違い | 文 5 件（例＝notably, quantica has maintained its relatively low volatility with great consistency over the past 20 years (as shown i） |
| close vs ACCBL% | 構造・位置（位置） | 順張り値＝大きいほど下の帯から離れて上にいる | 出どころのページの語の数：位置4・値動きの幅2・向き1 |  | 文 4 件（例＝the upper and lower acceleration bands are plotted equidistant from the simple 20-period simple moving average (the midd） |
| close vs ACCBU% | 構造・位置（位置） | 順張り値＝大きいほど上の帯に近い（0 を超えると帯の外） | 出どころのページの語の数：位置4・値動きの幅2・向き1 |  | 文 4 件（例＝the upper and lower acceleration bands are plotted equidistant from the simple 20-period simple moving average (the midd） |
| close vs CE_L% | 構造・位置（位置） | 順張り値＝大きいほど直近高値から見た余裕がある | 出どころのページの語の数：向き15・値動きの幅10・行き過ぎ4・勢い3・出来高3・強さ2・位置1 | 食い違いの疑い | 文 10 件（例＝``` chandelier exit (long) = 22-day high - atr(22) x 3 chandelier exit (short) = 22-day low + atr(22) x 3 ``` as shown i） |
| close vs CE_S% | 構造・位置（位置） | 順張り値＝大きいほど売り側の線より上 | 出どころのページの語の数：向き15・値動きの幅10・行き過ぎ4・勢い3・出来高3・強さ2・位置1 | 食い違いの疑い | 文 10 件（例＝``` chandelier exit (long) = 22-day high - atr(22) x 3 chandelier exit (short) = 22-day low + atr(22) x 3 ``` as shown i） |
| HWC位置 | 構造・位置（位置） | 状態量＝大きいほど水路の上側（向きは持たない） | 係の調べ（逐語✅）：位置 |  | 無い |
| HT_DCPHASE | 構造・位置（位置） | 状態量＝サイクルの中の居場所（向きは持たない） | 係の調べ（逐語✅）：その他 | 食い違い | 既定：[90, 270]（90° is the modeled cycle's high, 270° its low）［順位3］ |
| RCI | オシレーター（行き過ぎ） | 順張り値＝+100 で一貫した上昇 | 係の調べ（逐語✅）：勢い・向き・強さ・行き過ぎ |  | 既定：[-80, 0, 80]（-80・0・+80 に水平線。範囲の外は期間を通した強い上げ・下げの一貫性）［順位2］<br>既定：[-80, 0, 80]（-80・0・+80 の水準に水平線）［順位2］<br>既定：[80, -80]（+80%以上は買われすぎ・-80%以下は売られすぎ）［順位4］<br>既定：[0, 80, -80]（0より上は上昇基調・下は下落基調、80超は買いの過熱・-80割れは売りの過熱）［順位4］<br>既定：[80, -80]（+80以上は買われすぎ・-80以下は売られすぎ）［順位4］<br>既定：[80, 100, -80, -100]（+80〜+100 は買われすぎ・-80〜-100 は売られすぎ）［順位4］<br>既定：[80, -80]（Upper Band +80（買われすぎ）・Lower Band -80（売られすぎ））［順位4］<br>既定：[80, -80]（+80より上は強い上げの並び（買われすぎ）・-80より下は強い下げの並び（売られすぎ））［順位4］<br>スキャル：[85, -75]（1時間足より下の足では +85/-75 に広げる）［順位4］<br>スキャル：[80]（5分足〜15分足の RCI-9 で ±80）［順位4］<br>デイトレ：[85, -75]（1時間足より下の足では +85/-75 に広げる）［順位4］<br>デイトレ：[80]（5分足〜15分足の RCI-9 で ±80）［順位4］ |
| 前期間pivotPP | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置・向き |  | 文 5 件（例＝the chart below shows the nasdaq 100 etf (qqq) with standard pivot points on a 15-minute chart.） |
| 前期間pivotR1 | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 文 5 件（例＝the chart below shows the nasdaq 100 etf (qqq) with standard pivot points on a 15-minute chart.） |
| 前期間pivotS1 | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 文 5 件（例＝the chart below shows the nasdaq 100 etf (qqq) with standard pivot points on a 15-minute chart.） |
| close vs VWAP典型 | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置・向き |  | 文 1 件（例＝the spreadsheet example below shows one-minute vwap for the first 30 minutes of trading in ibm.） |
| 前日POC | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置・出来高 |  | 文 1 件（例＝for example, to calculate the volume profile for one daily session, the system loads all 1-minute bars that were traded ） |
| 前日VAH | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 文 1 件（例＝for example, to calculate the volume profile for one daily session, the system loads all 1-minute bars that were traded ） |
| 前日VAL | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 文 1 件（例＝for example, to calculate the volume profile for one daily session, the system loads all 1-minute bars that were traded ） |
| 前週pivotPP | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置・向き |  | 文 5 件（例＝the chart below shows the nasdaq 100 etf (qqq) with standard pivot points on a 15-minute chart.） |
| 前週pivotR1 | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 文 5 件（例＝the chart below shows the nasdaq 100 etf (qqq) with standard pivot points on a 15-minute chart.） |
| 前週pivotS1 | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 文 5 件（例＝the chart below shows the nasdaq 100 etf (qqq) with standard pivot points on a 15-minute chart.） |
| 当日POC | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置・出来高 |  | 文 1 件（例＝for example, to calculate the volume profile for one daily session, the system loads all 1-minute bars that were traded ） |
| 当日VAH | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 文 1 件（例＝for example, to calculate the volume profile for one daily session, the system loads all 1-minute bars that were traded ） |
| 当日VAL | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置 |  | 文 1 件（例＝for example, to calculate the volume profile for one daily session, the system loads all 1-minute bars that were traded ） |
| 当日VWAP | 構造・位置（位置） | 順張り値 | 係の調べ（逐語✅）：位置・向き |  | 文 1 件（例＝the spreadsheet example below shows one-minute vwap for the first 30 minutes of trading in ibm.） |
| W字確定谷 | 構造・位置（位置） | 反転サイン＝1 は買い転換（ダブルボトム完成）の示唆 | 出どころのページの語の数：向き31・出来高25・位置22・強さ4・値動きの幅1 |  | 文 11 件（例＝there were two days when volume on a decline exceeded the 60-day exponential moving average (ema) of volume, and cmf dip） |
| S-Rタッチ確定数 | 構造・位置（位置） | 状態量＝多いほど節が固い | 係の調べ（逐語✅）：位置 |  | 無い |
| S-Rタッチ確定1時間ATR | 構造・位置（位置） | 状態量＝多いほど節が固い | 出どころのページの語の数：値動きの幅14・位置3・強さ2・向き1 | 食い違いの疑い | 文 2 件（例＝the image below shows examples of when methods 2 and 3 are appropriate.） |
| SMC_SWEEP確定 | 構造・位置（位置） | 反転サイン | 無い |  | 無い |
| DPO教科書% | オシレーター（行き過ぎ） | 反転サイン | 出どころのページの語の数：勢い4・行き過ぎ3・位置3 |  | 文 8 件（例＝the chart below shows the s&p 500 etf (spy) with a 20-day sma (green dotted line) and a 20-day sma offset 11 days to the） |
| ABER原作位置 | 構造・位置（位置） | 順張り値＝大きいほど帯の上側 | 係の調べ（逐語✅）：値動きの幅 | 食い違い | 文 5 件（例＝notably, quantica has maintained its relatively low volatility with great consistency over the past 20 years (as shown i） |
| THERMO原作% | ボラ（値動きの幅） | ボラ量 | 係の調べ（逐語✅）：値動きの幅 |  | 既定：[3]（Explosive Move threshold（Thermometer がその EMA の何倍か）の既定 3）［順位4］ |
| THERMO_EMA% | ボラ（値動きの幅） | ボラ量 | 係の調べ（逐語✅）：値動きの幅 |  | 既定：[3]（Explosive Move threshold（Thermometer がその EMA の何倍か）の既定 3）［順位4］ |
| SQZ_ON_Carter | ボラ（値動きの幅） | 状態量 | 係の調べ（逐語✅）：値動きの幅 |  | 無い |
| StochRSI素%K | オシレーター（行き過ぎ） | 順張り値 | 係の調べ（逐語✅）：行き過ぎ |  | スキャル：[0.8, 0.2]（5-Minute：0.8/0.2 levels）［順位4］<br>デイトレ：[0.7, 0.3]（15-Minute：0.7/0.3 levels）［順位4］<br>デイトレ：[0.8, 0.2]（1-Hour：0.8/0.2 levels）［順位4］ |
| TRIX_EMAシグナル | トレンド（向き） | 順張り値 | 出どころのページの語の数：勢い12・向き5・位置5・出来高3・値動きの幅1 | 食い違いの疑い | 文 10 件（例＝single-smoothed ema = 15-period ema of the closing price double-smoothed ema = 15-period ema of single-smoothed ema trip） |
| TRIX_EMAヒスト | トレンド（向き） | 状態量＝加速（向きを持たない） | 出どころのページの語の数：勢い12・向き5・位置5・出来高3・値動きの幅1 | 食い違いの疑い | 文 10 件（例＝single-smoothed ema = 15-period ema of the closing price double-smoothed ema = 15-period ema of single-smoothed ema trip） |
| realized_vol_rv | ボラ（値動きの幅） | ボラ量 | 係の調べ（逐語✅）：値動きの幅 |  | 無い |
| close vs SSF平均% | 構造・位置（位置） | 反転サイン | 無い |  | 文 1 件（例＝sources: http://www.stockspotter.com/files/predictiveindicators.pdf https://www.tradingview.com/script/vdjy0ybj-ehlers-s） |
| close vs TRIMA_TA% | 構造・位置（位置） | 反転サイン | 出どころのページの語の数：出来高2・位置1 | 食い違いの疑い | 文 1 件（例＝further flags continue from the low end, where all * 24 remaining bits are free (the ta_in_/ta_optin_/ta_out_ flags belo） |
| close vs VIDYA_CMO% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| close vs HT_TRENDLINE_HL% | 構造・位置（位置） | 反転サイン | 無い |  | 無い |
| close vs MAMA_HL% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| close vs FAMA_HL% | 構造・位置（位置） | 反転サイン | 係の調べ（逐語✅）：向き | 食い違い | 無い |
| LeeMykland | ボラ（値動きの幅） | 向きつき＝大きいほど統計的にありえない上げ・小さいほど下げ | 係の調べ（逐語✅）：値動きの幅 |  | 既定：[1]（棄却の境目を決める有意水準の例として 1%）［順位4］<br>既定：[4.6001]（有意水準 1% のときの境目 β*。標準化した ／L(i)／ がこれを超えると「jump が無い」を棄却する）［順位4］<br>既定：[5]（論文のシミュレーションで使った有意水準 5%）［順位4］ |
| 帯スイング | 構造・位置（位置） | 状態量＝1 はレンジの帯の中 | 係の調べ（逐語✅）：位置 |  | 無い |
| 帯pivot | 構造・位置（位置） | 状態量＝1 は前の日の R1 と S1 の間 | 係の調べ（逐語✅）：位置 |  | 文 5 件（例＝the chart below shows the nasdaq 100 etf (qqq) with standard pivot points on a 15-minute chart.） |
| 帯VA | 構造・位置（位置） | 状態量＝1 は前の日の VAL と VAH の間 | 係の調べ（逐語✅）：位置 |  | 文 1 件（例＝for example, to calculate the volume profile for one daily session, the system loads all 1-minute bars that were traded ） |
| 帯スイング1時間ATR | 構造・位置（位置） | 状態量＝1 はレンジの帯の中 | 係の調べ（逐語✅）：位置 |  | 無い |
| 帯pivot1時間ATR | 構造・位置（位置） | 状態量＝1 は前の日の R1 と S1 の間 | 係の調べ（逐語✅）：位置 |  | 文 5 件（例＝the chart below shows the nasdaq 100 etf (qqq) with standard pivot points on a 15-minute chart.） |
| 帯VA1時間ATR | 構造・位置（位置） | 状態量＝1 は前の日の VAL と VAH の間 | 係の調べ（逐語✅）：位置 |  | 文 1 件（例＝for example, to calculate the volume profile for one daily session, the system loads all 1-minute bars that were traded ） |
| 帯pivot前週 | 構造・位置（位置） | 状態量＝1 は前の週の R1 と S1 の間 | 係の調べ（逐語✅）：位置 |  | 文 5 件（例＝the chart below shows the nasdaq 100 etf (qqq) with standard pivot points on a 15-minute chart.） |
| 帯pivot前週1時間ATR | 構造・位置（位置） | 状態量＝1 は前の週の R1 と S1 の間 | 係の調べ（逐語✅）：位置 |  | 文 5 件（例＝the chart below shows the nasdaq 100 etf (qqq) with standard pivot points on a 15-minute chart.） |
| LeeMykland_E36版 | ボラ（値動きの幅） | 向きつき＝大きいほど統計的にありえない上げ・小さいほど下げ | 係の調べ（逐語✅）：値動きの幅 |  | 既定：[1]（棄却の境目を決める有意水準の例として 1%）［順位4］<br>既定：[4.6001]（有意水準 1% のときの境目 β*。標準化した ／L(i)／ がこれを超えると「jump が無い」を棄却する）［順位4］<br>既定：[5]（論文のシミュレーションで使った有意水準 5%）［順位4］ |
