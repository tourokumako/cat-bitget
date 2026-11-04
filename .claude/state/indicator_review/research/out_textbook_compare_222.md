# 9種の指標の教科書の調べと、指標データを欄ごとに照らした結果（ToDo 222番の材料）

この文書は、`out_textbook_compare_222.json` の中身を、人が読む形にまとめた物です。値は決めていません。データとプログラムは直していません。

- 照らした条件＝レンジ・スキャル・ショート・BTC・5分足。
- 指標データ＝`refactor/e35-e36-split-strat-base` の `83b392f` の `SDK/scripts/priority_rebuild/indicators/indicators.json`。
- 9種の文書＝`research/textbook-9-kinds` の `826334b` の `textbook_9kinds_kb.md`。
- 全指標の調べ＝`research/textbook-all-6` の `54a075c`（out_c6_01・02・07・08）と `research/textbook-all-5` の `3d0f9b2`（out_c5）。

## 1. 判定ごとの件数と、指標ごとの件数

照らした欄は全部で **154 件**です。

| 判定 | 件数 |
|---|---|
| 合う | 49 |
| 違う | 12 |
| 教科書に無い | 36 |
| 指標データが空 | 11 |
| 指標データに欄が無い | 38 |
| 両方に無い | 8 |
| 合計 | 154 |

| 指標 | 合う | 違う | 教科書に無い | 指標データが空 | 指標データに欄が無い | 両方に無い | 合計 |
|---|---|---|---|---|---|---|---|
| RSI | 9 | 4 | 8 | 1 | 11 | 0 | 33 |
| ADX | 5 | 1 | 8 | 1 | 10 | 0 | 25 |
| DI差 | 5 | 2 | 7 | 0 | 3 | 1 | 18 |
| BB幅 | 5 | 1 | 0 | 2 | 2 | 1 | 11 |
| BB%b | 11 | 0 | 4 | 2 | 3 | 0 | 20 |
| ATR% | 4 | 1 | 0 | 1 | 2 | 1 | 9 |
| 基準線 | 4 | 2 | 5 | 3 | 3 | 1 | 18 |
| 包み足 | 3 | 1 | 0 | 1 | 2 | 2 | 9 |
| 帯pivot | 3 | 0 | 4 | 0 | 2 | 2 | 11 |

判定の決め方（この照らしで決めた読み方）は、次の5つです。

1. 教科書の値が2つ以上あるときは、指標データの値と同じ値が、確かめの強さ「ページの文で確かめた」の逐語に1つでも在れば「合う」にしました。違う値の文は、行の「教科書」と「注」に全部 残しました。
2. 教科書の値が「7 to 9」のような幅で書いてあるときは、指標データの値が端の数（7 か 9）と同じなら「合う」にしました。端でない中の数は「合う」にしていません。
3. 範囲の欄は、指標データの下の端と上の端の両方が、同じ1つの逐語に書いてあるときだけ「合う」にしました。
4. スキャルの代表の値は、逐語がスキャル（scalp・scalping・scalpers）を名指ししている文と比べました。5分足の文でも、デイトレ（day traders）の文はスキャルの値として数えていません。
5. 確かめの強さが「見つからなかった」の行は、値の根拠にしていません。「無い」ことの記録として、行の「教科書」に残しました。

## 2. 「違う」の一覧

| 指標 | 記録 | 欄 | 指標データの値 | 教科書の値と逐語 | 注 |
|---|---|---|---|---|---|
| RSI | 指標の記録 | ②-4 パラメータの軸・n の範囲 | {"kind": "int", "lo": 2, "hi": 21} | 2（短期のトレーダー。時間足の指定なし）：Short-term traders sometimes use 2-period RSI to look for overbought readings above 80 and oversold readings below 20.（全指標の調べ textbook-all-6 out_c6_02.json の RSI の パラメータの軸.0.範囲.0）<br>7〜9（日中の足のデイトレ）〜21（日足のスイング）：Day traders commonly shorten the period to 7 to 9 on intraday charts, swing traders commonly keep 14 or stretch it to 21 on the daily, and traders in a strong trend commonly widen the bands to 80/20.（全指標の調べ textbook-all-6 out_c6_02.json の RSI の パラメータの軸.0.範囲.2）<br>2（短期の売買）："Short-term traders sometimes use 2-period RSI to look for overbought readings above 80 and oversold readings below 20."（9種の文書 1 Q3（106行目）） | 範囲を1つの文で書いた教科書は無い（9種の文書の118行目は見つからなかった）。全指標の調べの範囲の値は「2」と「7〜9〜21」で、2〜21 と同じ値の文は無い。下の端の 2 は SC-RSI の 2-period、上の端の 21 は BLX の日足のスイング。 |
| RSI | 指標の記録 | ②-6 値の読み方・読み方（区分と読み方） | {"区分": "順張り値", "読み方": "大きいほど上昇の勢い"} | 70 より上は買われ過ぎ、30 より下は売られ過ぎ：When the RSI is above 70, it generally indicates overbought conditions; when the RSI is below 30, it indicates oversold conditi（全指標の調べ textbook-all-6 out_c6_02.json の RSI の 値の読み方.0）<br>："When the RSI is above 70, it generally indicates overbought conditions; when the RSI is below 30, it indicates oversold conditions."（9種の文書 1 Q1（78行目））<br>50（向きなし）："An RSI between 30 and 70 was to be considered neutral and an RSI around 50 signified “no trend”."（9種の文書 1 Q4（128行目）） | 教科書は 70 より上を買われ過ぎ、30 より下を売られ過ぎと読む（行き過ぎの読み）。指標データは「大きいほど上昇の勢い」（順張り値）。全指標の調べの逐語は末尾が「conditi」で切れている（9種の文書の78行目に全文が在る）。 |
| ADX | 指標の記録 | ②-2 計算の関数・式の文が指す関数の本体（_adx_di の1つ目の戻り値） | {"式の文": "_reg(\"ADX\", \"ADX{}\", False, lambda d, n: _adx_di(d.high, d.low, d.close, n)[0])", "関数の本体（observe_diag.py:277-285）": "up, dn = h.diff(), -l.diff(); p = (up > dn) & (up > 0) のとき up、他は 0; m = (dn > up) & (dn > 0) のとき dn、他は 0; a = _atr(h, l, c, n)（TR の ewm(alpha=1/n, adjust=False)）; pdi = 100 * p.ewm(alpha=1/n, adjust=False).mean() / a; mdi 同じ; dx = 100 * \|pdi - mdi\| / (pdi + mdi); ADX = dx.ewm(alpha=1/n, adjust=False).mean()"} | ：["+DI = 100*(+DM_p/TR_p), -DI = 100*(-DM_p/TR_p); DX = 100*\|(-DI)-(+DI)\| / ((-DI)+(+DI)); first ADX = mean of the first period DX; then ADX = (prevADX*(period-1) + DX)/period."]（全指標の調べ textbook-all-6 out_c6_01.json の ADX の 計算の式） | 式の形（+DI・−DI・DX・ADX の漸化式 (前の値×(n−1)+DX)/n）は同じ。違うのは最初の値だけ。教科書は「first ADX = mean of the first period DX」、関数は ewm(adjust=False) なので最初の DX の値から始まる。+DM と TR の平滑も、同じく最初の値の作り方が TA-Lib の和の形と違う。 |
| DI差 | 指標の記録 | ②-4 パラメータの軸・n の範囲 | {"kind": "int", "lo": 7, "hi": 21} | 1〜100000（入力できる範囲）：optInTimePeriod integer 14 1–100000 Wilder smoothing period（全指標の調べ textbook-all-6 out_c6_01.json の DI差 の パラメータの軸.1.範囲.0） | 9種の文書は DI の期間の範囲を見つからなかった。全指標の調べは TA-Lib の入力できる範囲 1〜100000 を書く（注＝勧める範囲ではない）。7〜21 と同じ値の文は無い。 |
| BB幅 | 指標の記録 | ②-4 パラメータの軸・n のスキャルの代表の値 | [20] | スキャル (10〜14, 1.5〜2)："Period for SMA: Reduce to 10-14 periods." / "Standard Deviations: Use 1.5 to 2."（9種の文書 4 Q3（284行目））<br>5分足で (20, 2) は遅い："20 and 2 Daily default, or 15-minute Bollinger's reference Late on a 5-minute scalp"（9種の文書 4 Q3（283行目））<br>5分足 (10, 1.9)："Day traders who leave 20 and 2 often put them on a 15-minute chart, or use 10 and 1.9 on a 5-minute chart."（9種の文書 4 Q3（282行目））<br>["10〜14", "1.5〜2"]：For scalping on short time frames, you can reduce the period to 10–14, with a multiplier of 1.5–2.（全指標の調べ textbook-all-6 out_c6_01.json の BB幅 の パラメータの軸.0.スキャル.0）<br>["10〜14", "1.5〜2"]：When applied to scalping, traders often adjust these settings to suit shorter timeframes, such as using a 10-14 period SMA and 1.5-2 standard deviations on 1-minute or 5-minute charts.（全指標の調べ textbook-all-6 out_c6_01.json の BB幅 の パラメータの軸.0.スキャル.1） | スキャルの文の期間は 10〜14（OX・litefinance・opofinance）。TRT-BB は 5分足のスキャルで (20, 2) は「Late」と書く。20 と同じ値をスキャルとして書いた文は無い。OX の行は、逐語の中に足が無いので「時間足は書いてない」とした（9種の文書の時間足の欄は「1分足・5分足」）。 |
| ATR% | 指標の記録 | ②-4 パラメータの軸・n のスキャルの代表の値 | [14] | [5, 7]：Optimization for Scalpers: Settings 5 to 7  Scalpers operate on the shortest timeframes, such as the 1-minute or 5-minute charts.（全指標の調べ textbook-all-6 out_c6_01.json の ATR% の パラメータの軸.0.スキャル.0）<br>[7]：Standard Scalp (Period 7)  Primary Use: General intraday price action on 5-minute charts.（全指標の調べ textbook-all-6 out_c6_01.json の ATR% の パラメータの軸.0.スキャル.1）<br>5分足・15分足 14、または 10："Day traders can use 14 on a 5 minute or 15 minute chart. Use 10 only when 14 feels like yesterday's range."（9種の文書 6 Q3（385行目））<br>7 は跳ねる："If one news bar blows the distance out and you need it to fade faster, try period 10 and keep the multiple unchanged. Period 7 reacts even faster and will jump on a single spike."（9種の文書 6 Q3（386行目）） | スキャルと名指しした文（marketclutch）は 5〜7・7 で、14 と違う。TRT-ATR は 5分足でも 14 と書くが、デイトレの文（Day traders …）。marketclutch は9種の文書では 404 だった。 |
| 包み足 | 指標の記録 | ②-2 計算の関数・形の前提（前のトレンド・1本目が十字線でない・2本目が長い） | （式の文に無い） | 前にトレンドが要る（陽は下げの後、陰は上げの後）："Price trend leading to the pattern Downward." / "Price trend leading to the pattern Upward."（9種の文書 8 形の条件（473行目））<br>1本目は十字線でない。2本目は長い。ひげまで包むのは、要らない："The size of the white candlestick is relatively unimportant, but it should not be a doji, which would be relatively easy to engulf. The second should be a long black candlestick. The bigger it is, the more bearish the reversal. The black body must totally engulf the body of the first white candlestick. Ideally, the black body should engulf the shadows as well, but this is not a requirement."（9種の文書 8 形の条件（472行目））<br>確かめの足が要る："Further weakness is required for bearish confirmation of this reversal pattern."（9種の文書 8 形の条件（476行目））<br>：To be considered a bullish reversal, there should be an existing downtrend to reverse. A bullish engulfing at new highs can hardly be considered a bullish reversal pattern.（全指標の調べ textbook-all-5 out_c5.json の 包み足 の 使い方.2） | 教科書は、陽の包み足は下げの後・陰の包み足は上げの後に出ること、1本目が十字線でないこと、2本目が長いことを書く。式はどれも見ていない。 |
| RSI | 使い方の記録（行 4） | ③-5 閾値・閾値のスキャルの代表の値 | 30.0 | スキャル 5〜7・デイトレ 9〜10："Scalpers should use RSI(5-7) with 80/20 levels, while day traders benefit from RSI(9-10) with 75/25 levels."（9種の文書 1 Q3（114行目））<br>5分足のスキャル 5："Use a 5-period RSI with 80/20 thresholds to match the faster pace."（9種の文書 1 Q3（117行目））<br>5分足のスキャル 7〜9："Faster 7 to 9 75/25 or 80/20 35 to 45 minutes Scalps and quick mean-reversion fades"（9種の文書 1 Q3（110行目））<br>70／30："Wilder considered RSI overbought above 70 and oversold below 30."（9種の文書 1 Q4（126行目））<br>70／30："According to Wilder, any number above 70 should be considered overbought and any number below 30 should be considered oversold."（9種の文書 1 Q4（127行目））<br>[70, 30]：When the RSI is above 70, it generally indicates overbought conditions; when the RSI is below 30, it indicates oversold conditi（全指標の調べ textbook-all-6 out_c6_02.json の RSI の 閾値.0）<br>5分足 30／70 から始め、20／80 へ："Keep 30 and 70 at first. If 7 tags 70 on every small push, you can move the lines to 20 and 80."（9種の文書 1 Q4（136行目）） | スキャルと名指しした文の線は 80／20（EPB「Scalpers should use RSI(5-7) with 80/20 levels」・WT）と、75／25 か 80／20（BLX の表の行・Scalps）で、30 と同じ値は無い。足もスタイルも書いてない一般の線は 70／30（Wilder）で、指標データと同じ。TRT-RSI は 5分足でも 30 と 70 から始めると書く（デイトレの文）。 |
| RSI | 使い方の記録（行 6） | ③-5 閾値・閾値のスキャルの代表の値 | 70.0 | スキャル 5〜7・デイトレ 9〜10："Scalpers should use RSI(5-7) with 80/20 levels, while day traders benefit from RSI(9-10) with 75/25 levels."（9種の文書 1 Q3（114行目））<br>5分足のスキャル 5："Use a 5-period RSI with 80/20 thresholds to match the faster pace."（9種の文書 1 Q3（117行目））<br>5分足のスキャル 7〜9："Faster 7 to 9 75/25 or 80/20 35 to 45 minutes Scalps and quick mean-reversion fades"（9種の文書 1 Q3（110行目））<br>70／30："Wilder considered RSI overbought above 70 and oversold below 30."（9種の文書 1 Q4（126行目））<br>70／30："According to Wilder, any number above 70 should be considered overbought and any number below 30 should be considered oversold."（9種の文書 1 Q4（127行目））<br>[70, 30]：When the RSI is above 70, it generally indicates overbought conditions; when the RSI is below 30, it indicates oversold conditi（全指標の調べ textbook-all-6 out_c6_02.json の RSI の 閾値.0）<br>5分足 30／70 から始め、20／80 へ："Keep 30 and 70 at first. If 7 tags 70 on every small push, you can move the lines to 20 and 80."（9種の文書 1 Q4（136行目）） | スキャルと名指しした文の線は 80／20（EPB「Scalpers should use RSI(5-7) with 80/20 levels」・WT）と、75／25 か 80／20（BLX の表の行・Scalps）で、70 と同じ値は無い。足もスタイルも書いてない一般の線は 70／30（Wilder）で、指標データと同じ。TRT-RSI は 5分足でも 30 と 70 から始めると書く（デイトレの文）。 |
| DI差 | 使い方の記録（行 18） | ③-3 場面と型・場面と型 | {"場面": "レンジ", "型": "down"} | ："For example, the first group of whipsaws in September 2009 occurred during a consolidation."（9種の文書 3 Q2（221行目））<br>："These moments in question are known as “false signals” and are most common when ADX is calculated below 25."（9種の文書 3 Q2（222行目）） | 教科書のレンジ（consolidation）の文は、DI のクロスのだまし（whipsaws・false signals）がレンジで多いと書く。レンジで使う文ではない。型 down は教科書に無い。 |
| 基準線 | 使い方の記録（行 19） | ③-3 場面と型・場面と型 | {"場面": "レンジ", "型": "flat_up"} | ："Avoid relying on Ichimoku for scalping or in tight, choppy ranges — on very short timeframes the indicator is often whipsawed and produces many low‑quality signals. If price is inside a flat, narrow cloud or the market shows no directional momentum, stand aside or switch to oscillators better suited for range trading."（9種の文書 7 Q2（424行目））<br>："First, the trend is up when prices are above the cloud, down when prices are below the cloud, and flat when prices are in the cloud."（9種の文書 7 Q2（423行目））<br>：In sideways markets, though, the line often gives false signals, which is why traders use the cloud to filter them out.（全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の 使い方.3） | RS-ICHI は「tight, choppy ranges」では一目均衡表に頼らないと書く。LF-ICHI の横ばいの文（転換線の文）は、だましが多いと書く。レンジで使う文ではない。型 flat_up は教科書に無い。 |
| 基準線 | 使い方の記録（行 19） | ③-6 パラメータの代表の値・k_ のスキャルの代表の値 | [26] | スキャル (5, 13, 26)："Scalping. Shorter periods like 5, 13, and 26 produce more signals, but also more false ones. They are best suited to 15-minute or even 5-minute charts."（9種の文書 7 Q3（435行目））<br>1分足 (12, 24, 120)："The best Ichimoku settings for scalping and 1-minute chart are 12-24-120"（9種の文書 7 Q3（438行目））<br>5分足 (9, 26, 52)："The best settings for the Ichimoku 5 min chart are standard default settings 9-26-52"（9種の文書 7 Q3（437行目）） | スキャルと名指しした文の基準線は 13（LF-ICHI）と 24（RS-ICHI・1分足）で、26 と違う。RS-ICHI は 5分足では既定の 26 と書くが、スキャルとは名指ししていない。 |

## 3. 「指標データが空」と「指標データに欄が無い」の一覧

### 3-1. 指標データが空（教科書に文が在り、指標データの欄が空）

| 指標 | 記録 | 欄 | 指標データの値 | 教科書の値 | 注 |
|---|---|---|---|---|---|
| RSI | 指標の記録 | ②-7 教科書の役割・区分 | {"区分": null, "出どころ": "語の数だけ（弱い）", "札": "オシレーター"} | 勢い（全指標の調べ textbook-all-6 out_c6_02.json の RSI の 教科書の役割.0）<br>勢い（9種の文書 1 Q1（77行目））<br>行き過ぎ（9種の文書 1 Q1（78行目）） | 指標データの区分は null（札はオシレーター・出どころ「語の数だけ（弱い）」）。教科書は勢い（momentum oscillator）。9種の文書は行き過ぎの使い方も書く。 |
| ADX | 指標の記録 | ②-5 値の単位と値域・値域 | {"有界": null, "分位": null} | 0〜100（全指標の調べ textbook-all-6 out_c6_01.json の ADX の 値の単位と値域.0） | 指標データの有界は null。教科書は 0〜100（TradingView の DMI のページ）。 |
| BB幅 | 指標の記録 | ②-6 値の読み方・読み方（区分と読み方） | {"区分": "ボラ量", "読み方": ""} | 帯が狭まると小さく、広がると大きい（全指標の調べ textbook-all-6 out_c6_01.json の BB幅 の 値の読み方.0）<br>（9種の文書 4 Q1（255行目）） | 指標データの読み方は空の文字列。教科書は「帯が狭まると小さく、広がると大きい」。 |
| BB幅 | 指標の記録 | ②-7 教科書の役割・区分 | {"区分": null, "出どころ": "語の数だけ（弱い）", "札": "ボラ"} | 値動きの幅（全指標の調べ textbook-all-6 out_c6_01.json の BB幅 の 教科書の役割.0）<br>値動きの幅（9種の文書 4 Q1（255行目）） | 指標データの区分は null（札はボラ）。教科書は値動きの幅。 |
| BB%b | 指標の記録 | ②-6 値の読み方・読み方（区分と読み方） | {"区分": "順張り値", "読み方": ""} | 1 より上は上の帯より上、0 より下は下の帯より下、0.5 が中央（全指標の調べ textbook-all-6 out_c6_01.json の BB%b の 値の読み方.0）<br>1・0・0.5（9種の文書 5 Q4（343行目）） | 指標データの読み方は空の文字列。 |
| BB%b | 指標の記録 | ②-7 教科書の役割・区分 | {"区分": null, "出どころ": "語の数だけ（弱い）", "札": "オシレーター"} | 位置（全指標の調べ textbook-all-6 out_c6_01.json の BB%b の 教科書の役割.0）<br>位置（9種の文書 5 Q1（310行目））<br>位置・行き過ぎ・強さ（9種の文書 5 Q1（311行目）） | 指標データの区分は null（札はオシレーター）。教科書は位置。SC-PB は行き過ぎとトレンドの強さを見る使い方も書く。 |
| ATR% | 指標の記録 | ②-7 教科書の役割・区分 | {"区分": null, "出どころ": "語の数だけ（弱い）", "札": "ボラ"} | 値動きの幅（全指標の調べ textbook-all-6 out_c6_01.json の ATR% の 教科書の役割.0）<br>値動きの幅（9種の文書 6 Q1（361行目）） | 指標データの区分は null（札はボラ）。教科書は値動きの幅。 |
| 基準線 | 指標の記録 | ②-4 パラメータの軸・k_ のスキャルの代表の値 | まだ決めていない | スキャル (5, 13, 26)（9種の文書 7 Q3（435行目））<br>1分足 (12, 24, 120)（9種の文書 7 Q3（438行目））<br>5分足 (9, 26, 52)（9種の文書 7 Q3（437行目））<br>[5, 13, 26]（全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の パラメータの軸.0.スキャル.0）<br>[12, 24, 120]（全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の パラメータの軸.0.スキャル.1）<br>[9, 26, 52]（全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の パラメータの軸.0.スキャル.2） | 指標データは「まだ決めていない」。スキャルと名指しした文の基準線は 13（LF-ICHI・15分足か5分足）と 24（RS-ICHI・1分足）。RS-ICHI は 5分足では既定 26 と書く（スキャルとは名指ししていない）。 |
| 基準線 | 指標の記録 | ②-6 値の読み方・読み方（区分と読み方） | {"区分": "順張り値", "読み方": ""} | （9種の文書 7 Q1（413行目））<br>（9種の文書 7 Q1（410行目）） | 指標データの読み方は空の文字列。教科書は、値段が基準線より上なら上げ、下なら下げと読む（LF-ICHI）。SC-ICHI は値段と基準線の交差を勢いの合図と書く。 |
| 基準線 | 指標の記録 | ②-7 教科書の役割・区分 | {"区分": null, "出どころ": "語の数だけ（弱い）", "札": "トレンド"} | 勢い（9種の文書 7 Q1（411行目））<br>向き（9種の文書 7 Q1（412行目））<br>向き（全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の 教科書の役割.0）<br>勢い（全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の 教科書の役割.1）<br>位置（全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の 教科書の役割.2） | 指標データの区分は null（札はトレンド）。9種の文書は SC-ICHI＝勢い、LF-ICHI＝向き（ページで違う）。全指標の調べの3行は転換線の文（逐語と値が合わないに書いた）。 |
| 包み足 | 指標の記録 | ②-5 値の単位と値域・値域 | {"有界": null, "分位": null} | 書いてない（全指標の調べ textbook-all-5 out_c5.json の 包み足 の 値の単位と値域.0） | 指標データの有界は null。教科書（TA-Lib）は −100〜100（±100・±80・0）。式の出す値は +1／−1／0 で、TA-Lib の値とは数え方が違う。 |

### 3-2. 指標データに欄が無い（記録にその鍵が無い）

| 要素・欄 | 件数 | 指標（使い方の記録は行の番号） |
|---|---|---|
| ②-5 値の単位と値域・単位 | 8 | RSI、ADX、DI差、BB幅、BB%b、ATR%、基準線、包み足 |
| ②-11 閾値の範囲・閾値の範囲 | 8 | RSI、ADX、DI差、BB幅、BB%b、ATR%、基準線、包み足 |
| ③-3 場面と型・場面と型 | 4 | ADX（行 0）、ADX（行 2）、RSI（行 4）、RSI（行 6） |
| ③-6 パラメータの代表の値・パラメータの代表の値 | 4 | ADX（行 0）、ADX（行 2）、RSI（行 4）、RSI（行 6） |
| ③-7 時間足・時間足 | 4 | ADX（行 0）、ADX（行 2）、RSI（行 4）、RSI（行 6） |
| ③-9 合図の形のパラメータ・合図の形のパラメータ | 8 | ADX（行 0）、ADX（行 2）、RSI（行 4）、RSI（行 6）、RSI（行 16）、BB%b（行 17）、DI差（行 18）、基準線（行 19） |
| ④-5 閾値・閾値 | 1 | 帯pivot |
| ④-10 値の単位と値域・単位 | 1 | 帯pivot |

- 指標の記録の8種は、どれも「閾値の範囲」（②-11）の鍵を持っていません。「値の単位と値域」（②-5）の中に「単位」の鍵も持っていません（中は「値域」だけ）。
- 帯pivot の部品の記録は、「閾値」（④-5）の鍵と、「値の単位と値域」（④-10）の中の「単位」の鍵を持っていません。
- 使い方の記録の行 0・2・4・6（出口の反転と前提崩れの印の写し）は、場面と型・パラメータの代表の値・時間足・合図の形のパラメータの鍵を持っていません。行 16〜19 は、合図の形のパラメータの鍵を持っていません。

## 4. 指標データに行が無い使い方の一覧

使い方の記録に行が無く、逐語にレンジ・ショート・5分足のどれかの語が在る文だけを挙げました。トレンド（downtrend・bear market・200-day moving average など）を前提にしたショートの文は、レンジの条件と合わないので挙げていません。

| 指標 | 使い方の種類 | 逐語 | 時間足 | 挙げた理由（逐語の語） |
|---|---|---|---|---|
| RSI | 入る合図 | "Like many momentum oscillators, overbought and oversold readings for RSI work best when prices move sideways within a range ."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | 時間足は書いてない | レンジ（sideways within a range）で行き過ぎの読みがいちばん効く、と書く。使い方の記録の RSI の行は、出口の反転と前提崩れの印だけ。 |
| RSI | 入る合図 | "A short candidate is RSI crossing back below 70 after a print above 70. The first poke of 30 on a 5 minute chart is noise."<br>https://therighttrader.com/learn/indicator-strategies/best-rsi-settings | 5分足（5 minute chart） | ショートの入る合図（70 より上の後に 70 を下へ戻る）を書く。5分足の文。 |
| RSI | 入る合図 | "A bearish failure swing forms when RSI moves above 70, pulls back, bounces, fails to exceed 70, and then breaks its prior low."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi | 時間足は書いてない | ショートの入る合図（bearish failure swing）を書く。 |
| ADX | 場面の判定 | "At its most basic, the Average Directional Index (ADX) can be used to determine if a security is trending or not. This determination helps traders choose between a trend-following system or a non-trend-following system."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx | 時間足は書いてない | ADX でトレンドが在るか無いかを分け、トレンドでない手法を選ぶ、と書く（レンジの判定）。使い方の記録に ADX の場面の判定の行は無い。 |
| BB幅 | 場面の判定 | "The bands narrow as price flattens or moves within a relatively narrow range."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | 時間足は書いてない | 帯が狭まるのは値段が横ばい・狭い範囲で動くとき、と書く（レンジの判定）。使い方の記録に BB幅 の行は無い。 |
| BB幅 | 場面の判定 | With this in mind, the major trading signal generated by Bollinger BandWidth is known as The Squeeze.<br>https://www.tradingview.com/support/solutions/43000501972-bollinger-bandwidth-bbw/ | 時間足は書いてない | BB幅 の主な合図は締まり（The Squeeze）と書く。全指標の調べは場面＝レンジの場面の判定と読む。 |
| BB幅 | 入る合図 | "A new decline starts with a Squeeze and subsequent break below the lower band."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth | 時間足は書いてない | 締まりの後に下の帯を割ると新しい下げが始まる、と書く（レンジの後のショート）。 |
| ATR% | 場面の判定 | "The ATRP is lower when the security is in a trading range, and moves higher during dramatic price changes in either direction."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-true-range-percent-atrp | 時間足は書いてない | ATRP はレンジで低い、と書く（レンジの判定）。使い方の記録に ATR% の行は無い。 |
| ATR% | 場面の判定 | "On the other hand, during periods of sustained sideways movement, volatility is frequently low. This could assist in the discovery of trading ranges."<br>https://www.tradingview.com/support/solutions/43000501823-average-true-range-atr/ | 時間足は書いてない | 横ばいでは値動きの幅が低く、レンジを見つける助けになる、と書く。 |
| ATR% | 合図が本物かを確かめる条件 | "A bearish support break with increased ATR would show strong selling pressure and reinforce the support break."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-true-range-atr | 時間足は書いてない | 支えを割るときに ATR が増えていれば売りの圧力が強い、と書く（ショートの確かめる条件）。 |
| ATR% | 出口の水準を作る材料 | "A common same day distance is 1.5 or 2 times the 5 minute ATR, placed beyond the swing that got you in."<br>https://therighttrader.com/learn/indicator-strategies/best-atr-settings | 5分足（5 minute ATR） | 5分足の ATR の 1.5 か 2 倍を損切りの距離にする、と書く（玉の向きは書いてない）。 |
| 基準線 | 出口の反転 | Use a clear exit rule: opposite Tenkan/Kijun cross, price closing inside the cloud, or your volatility‑based target being hit.<br>https://www.forex.in.rs/ichimoku-settings-7-22-44/ | 時間足は書いてない | 転換線と基準線の逆の交差などを出口の決まりにする、と書く（全指標の調べの時間足の欄は 5分足・逐語に足は無い）。使い方の記録の基準線の行は前提崩れの印だけ。 |
| 包み足 | 入る合図 | Engulfing Bearish Line Consists of a small white body that is contained within the following large black candlestick. When it appears at the top it is considered a major reversal signal.<br>https://en.wikipedia.org/wiki/Candlestick_pattern | 時間足は書いてない | 陰の包み足が上（at the top）に出ると反転の合図、と書く（ショート）。使い方の記録に包み足の行は無い。 |
| 包み足 | 入る合図 | "After meeting resistance around $30 in mid-January, Ford (F) formed a bearish engulfing pattern (red oval). It was immediately confirmed with a decline and subsequent support break."<br>https://chartschool.stockcharts.com/table-of-contents/chart-analysis/candlestick-charts/candlestick-bearish-reversal-patterns | 時間足は書いてない | 抵抗に当たった後の陰の包み足を、下げと支えの割れで確かめた例（ショート）。 |
| 帯pivot | 入る合図 | "Similarly, if prices advance to resistance and stall, traders can look for a failure at resistance and decline. Again, look for a bearish chart pattern or indicator signal to confirm a downturn from resistance."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/pivot-points | 時間足は書いてない | 値段が抵抗まで上がって止まったら、抵抗での失敗と下げを探す、と書く（R1 でのショート）。使い方の記録に帯pivot の行は無い。 |
| 帯pivot | 出口の水準を作る材料 | "A move below the Pivot Point suggests weakness with a target to the first support level. A break below the first support level shows even more weakness with a target to the second support level."<br>https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/pivot-points | 時間足は書いてない | P を下に割ったら S1 を目標にする、と書く（ショートの利確の水準）。 |

件数＝16 件。

## 5. 調べの結果どうしの違いの一覧

どちらが正しいかは書いていません。

| 指標 | 欄 | 9種の文書 | 全指標の調べ |
|---|---|---|---|
| ATR% | n の範囲・n のスキャルの値（marketclutch のページ） | 範囲 5〜21：資料の表の出どころ（marketclutch.com）は「✗ 見つからなかった（URL を開くと 404。確かめ直せなかった）」（6 Q3・387行目） | 同じ marketclutch.com のページを「ページの文で確かめた」とし、範囲「5〜21（スキャル 5・7／トレンド狙い 20・21）」、スキャル [5, 7]・[7]、デイトレ [14]・[20, 22] を逐語つきで書く（out_c6_01.json の ATR% のパラメータの軸） |
| BB幅 | n と s のスキャルの値（litefinance.org の Bollinger の記事） | review の BB幅「スキャル」の出どころ（litefinance.org の Bollinger の記事）は、今回開くと 404（「いまの値と違う所」の BB幅・BB%b・613行目） | 同じ litefinance.org の記事を「ページの文で確かめた」とし、スキャル「10〜14」「1.5〜2」と、範囲「期間 50・倍率 2.5（スイング・長期）」を逐語つきで書く（out_c6_01.json の BB幅のパラメータの軸） |
| BB%b | n と s のスキャルの値 | %B を名指しした 5分足・スキャルの値は「✗ 見つからなかった」（5 Q3・335行目） | スキャル [20, 2]（fxopen の 1分足の文・MC2 の 1分足の文）を「ページの文で確かめた」で書く（out_c6_01.json の BB%b のパラメータの軸） |
| 基準線 | デイトレの値（LF-ICHI の (5, 13, 26)） | 資料の表の「デイトレ (5,13,26)・15分足」は、LF-ICHI の今のページには「day trading」の語が無く、「Scalping」の行として書かれている（7 Q3・440行目） | 同じ LF-ICHI のページの逐語「Is the Ichimoku 15-minute strategy good for day trading? … Use faster settings (5, 13, 26) …」を「ページの文で確かめた」でデイトレに書く（out_c6_08.json の基準線のパラメータの軸）。★デイトレの値は今回 照らさない |
| DI差 | n の範囲 | DI の期間だけのスキャル・デイトレ・範囲は「✗ 見つからなかった」（3 Q3・233行目） | 範囲「1〜100000（入力できる範囲）」を TA-Lib の逐語つきで「ページの文で確かめた」で書く（注＝入力できる範囲。勧める範囲ではない）（out_c6_01.json の DI差のパラメータの軸 1） |

## 6. 逐語と値が合わない物の一覧

全部 全指標の調べの中の物です。前半は値と逐語が合わない物、後半は「時間足」の欄が「書いてない」なのに逐語に足が書いてある物（依頼書の決まり6）です。

| 指標 | 欄 | 値 | 逐語 | どこの何が合わないか |
|---|---|---|---|---|
| 基準線 | 教科書の役割（向き） | 向き | The Tenkan Sen is an indicator of the market trend. | 全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の 教科書の役割.0｜基準線の行の値なのに、逐語は Tenkan Sen（転換線）の文 |
| 基準線 | 教科書の役割（勢い） | 勢い | The Tenkan-sen mainly shows short-term bullish or bearish momentum. | 全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の 教科書の役割.1｜基準線の行の値なのに、逐語は Tenkan-sen（転換線）の文 |
| 基準線 | 教科書の役割（位置） | 位置 | Also called the conversion line (blue line), it is primarily used as a signal line and a minor support/resistance line. | 全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の 教科書の役割.2｜基準線の行の値なのに、逐語は conversion line（転換線）の文 |
| 基準線 | 値の読み方 | 線が上か下へ動けばトレンド、横ならレンジ | If the blue line is moving up or down, it indicates that the market is trending. If it moves horizontally, it signals that the market is ranging. | 全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の 値の読み方.0｜基準線の行の値なのに、逐語は blue line（転換線）の文 |
| 基準線 | 値の単位と値域 | 値段 | Tenkan-sen (転換線) calculation: (highest high + lowest low)/2 for the last 9 periods. | 全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の 値の単位と値域.0｜基準線の行の値なのに、逐語は Tenkan-sen（転換線）の計算の文 |
| 基準線 | 計算の式 | （逐語だけの欄） | ["TenkanSen (Conversion Line): (High + Low) / 2 default period = 9"] | 全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の 計算の式｜基準線の行の式なのに、逐語は TenkanSen（転換線）の式（default period = 9） |
| 基準線 | パラメータの軸 t_ の既定 | 9 | TenkanSen (Conversion Line): (High + Low) / 2 default period = 9 | 全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の パラメータの軸.1.既定.0｜基準線の行の軸の名前が t_（転換線の本数）で、逐語は転換線の既定 9。指標データの軸は k_（基準線の本数） |
| DI差 | 値の単位と値域 | 0〜100 | DMI has a value between 0 and 100 and is used to measure the strength of the current trend. | 全指標の調べ textbook-all-6 out_c6_01.json の DI差 の 値の単位と値域.1｜DI差の行の値 0〜100 なのに、逐語は DMI 全体の文（全指標の調べの注にも同じことが書いてある） |
| BB%b | 値の単位と値域 | 書いてない | %B is between .50 and 1 when price is between the upper and middle band (20-day SMA) | 全指標の調べ textbook-all-6 out_c6_01.json の BB%b の 値の単位と値域.1｜値は下限 0・上限 1 だが、逐語は「between .50 and 1」（上の帯と中央の間の文） |
| BB幅 | パラメータの軸の既定（pandas_ta） | [5, 2.0] | length (int): The period. Default: ```5``` | 全指標の調べ textbook-all-6 out_c6_01.json の BB幅 の パラメータの軸.0.既定.5｜値は [5, 2.0] だが、逐語には length の 5 だけが在り、2.0 は書いてない |
| ATR% | パラメータの軸の範囲 | 5〜21（スキャル 5・7／トレンド狙い 20・21） | Scalpers require the rapid response of a 5 or 7-period setting, while trend traders benefit from the smoothing of a 20 or 21-period lookback. | 全指標の調べ textbook-all-6 out_c6_01.json の ATR% の パラメータの軸.0.範囲.0｜値は 5〜21 の範囲だが、逐語は「5 or 7」と「20 or 21」を挙げる文で、範囲としては書いていない |
| RSI | 時間足（パラメータの軸.0.スキャル.0） | 時間足の欄＝書いてない | When trading on a 1-minute chart, the best RSI setting is typically RSI 2 or 3. | 全指標の調べ textbook-all-6 out_c6_02.json の RSI の パラメータの軸.0.スキャル.0｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝1分足（1-minute chart） |
| RSI | 時間足（パラメータの軸.0.スキャル.1） | 時間足の欄＝書いてない | Most intraday traders run 7 to 9 periods on a 5-minute chart, or stay on 14 and widen the bands to 80/20. | 全指標の調べ textbook-all-6 out_c6_02.json の RSI の パラメータの軸.0.スキャル.1｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝5分足（5-minute chart） |
| RSI | 時間足（パラメータの軸.0.デイトレ.0） | 時間足の欄＝書いてない | On a 15-minute chart the 14-period default holds up well and is what most platforms leave in place. | 全指標の調べ textbook-all-6 out_c6_02.json の RSI の パラメータの軸.0.デイトレ.0｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝15分足（15-minute chart） |
| RSI | 時間足（パラメータの軸.0.デイトレ.1） | 時間足の欄＝書いてない | For 15-minute charts, try a 9-period RSI with 75/25 thresholds. On the 1-hour, the classic 14-period works well with standard 70/30 levels. | 全指標の調べ textbook-all-6 out_c6_02.json の RSI の パラメータの軸.0.デイトレ.1｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝15分足・1時間足（15-minute charts・1-hour） |
| RSI | 時間足（パラメータの軸.0.デイトレ.2） | 時間足の欄＝書いてない | Use a 14‑period RSI with 70/30 overbought/oversold levels to balance sensitivity and reliability on 15‑minute charts, catching momentum shifts early without excessive false signals. | 全指標の調べ textbook-all-6 out_c6_02.json の RSI の パラメータの軸.0.デイトレ.2｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝15分足（15‑minute charts） |
| RSI | 時間足（パラメータの軸.0.範囲.2） | 時間足の欄＝書いてない | Day traders commonly shorten the period to 7 to 9 on intraday charts, swing traders commonly keep 14 or stretch it to 21 on the daily, and traders in a strong trend commonly widen the bands to 80/20. | 全指標の調べ textbook-all-6 out_c6_02.json の RSI の パラメータの軸.0.範囲.2｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝日中の足・日足（intraday charts・daily） |
| BB幅 | 時間足（パラメータの軸.0.スキャル.1） | 時間足の欄＝書いてない | When applied to scalping, traders often adjust these settings to suit shorter timeframes, such as using a 10-14 period SMA and 1.5-2 standard deviations on 1-minute or 5-minute charts. | 全指標の調べ textbook-all-6 out_c6_01.json の BB幅 の パラメータの軸.0.スキャル.1｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝1分足・5分足（1-minute or 5-minute charts） |
| BB%b | 時間足（パラメータの軸.0.スキャル.0） | 時間足の欄＝書いてない | Bollinger Bands settings for a 1-minute chart are a 20-period simple moving average (middle band) and two outer bands set at a standard deviation level of 2 from the middle band. | 全指標の調べ textbook-all-6 out_c6_01.json の BB%b の パラメータの軸.0.スキャル.0｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝1分足（1-minute chart） |
| BB%b | 時間足（パラメータの軸.0.スキャル.1） | 時間足の欄＝書いてない | RSI (2 or 3), EMA 9, and Bollinger Bands (20, 2) for scalping at 1 minute. | 全指標の調べ textbook-all-6 out_c6_01.json の BB%b の パラメータの軸.0.スキャル.1｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝1分足（1 minute） |
| ATR% | 時間足（パラメータの軸.0.スキャル.0） | 時間足の欄＝書いてない | Optimization for Scalpers: Settings 5 to 7  Scalpers operate on the shortest timeframes, such as the 1-minute or 5-minute charts. | 全指標の調べ textbook-all-6 out_c6_01.json の ATR% の パラメータの軸.0.スキャル.0｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝1分足・5分足（1-minute or 5-minute charts） |
| ATR% | 時間足（パラメータの軸.0.スキャル.1） | 時間足の欄＝書いてない | Standard Scalp (Period 7)  Primary Use: General intraday price action on 5-minute charts. | 全指標の調べ textbook-all-6 out_c6_01.json の ATR% の パラメータの軸.0.スキャル.1｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝5分足（5-minute charts） |
| ATR% | 時間足（パラメータの軸.0.デイトレ.0） | 時間足の欄＝書いてない | For most day traders targeting 15-minute to 1-hour timeframes, the 14-period setting offers the best trade-off between smoothing and reactivity. | 全指標の調べ textbook-all-6 out_c6_01.json の ATR% の パラメータの軸.0.デイトレ.0｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝15分足〜1時間足（15-minute to 1-hour timeframes） |
| 基準線 | 時間足（パラメータの軸.0.既定.0） | 時間足の欄＝書いてない | The default setting for the Base Line is 26 periods and can be adjusted. On a daily chart, this line is the midpoint of the 26-day high-low range, which is almost one month. | 全指標の調べ textbook-all-6 out_c6_08.json の 基準線 の パラメータの軸.0.既定.0｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝日足（daily chart） |
| 帯pivot | 時間足（前期間pivotR1 と前期間pivotS1 のパラメータの軸.0.スキャル.0） | 時間足の欄＝書いてない | Pivot Points for 1-, 5-, 10-, and 15-minute charts use the prior day's high, low, and close. | 全指標の調べ textbook-all-6 out_c6_07.json の 前期間pivotR1 の パラメータの軸.0.スキャル.0｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝1分足・5分足・10分足・15分足（1-, 5-, 10-, and 15-minute charts） |
| 帯pivot | 時間足（前期間pivotR1 と前期間pivotS1 のパラメータの軸.0.スキャル.1） | 時間足の欄＝書いてない | 1D for chart resolutions up to and including 15 min | 全指標の調べ textbook-all-6 out_c6_07.json の 前期間pivotR1 の パラメータの軸.0.スキャル.1｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝15分足まで（up to and including 15 min） |
| 帯pivot | 時間足（前期間pivotR1 と前期間pivotS1 のパラメータの軸.0.デイトレ.1） | 時間足の欄＝書いてない | Pivot Points for 30-, 60-, and 120-minute charts use the prior week's high, low, and close. | 全指標の調べ textbook-all-6 out_c6_07.json の 前期間pivotR1 の パラメータの軸.0.デイトレ.1｜時間足の欄は「書いてない」だが、逐語には足が書いてある＝30分足・60分足・120分足（30-, 60-, and 120-minute charts） |

件数＝27 件（値と逐語 11 件・時間足 16 件）。

## 7. 確かめられなかった物と、その理由

1. **教科書のページは開いていません。**依頼書の決まり3のとおりです。逐語が本当にページに在るかは、調べの結果の「確かめの強さ」をそのまま写しました。調べの結果どうしで確かめの強さが違う URL（marketclutch.com・litefinance.org の Bollinger の記事）は、5 に書きました。
2. **関数の本体は読みましたが、走らせていません。**②-2 と ④-3 は、observe_diag.py の `_rsi`（263〜269行）・`_atr`（272〜274行）・`_adx_di`（277〜285行）・`_band_lines`（755〜769行）・`_pivot_prev_period`（1219〜1241行）と、式の文の lambda を読んで照らしました。ADX の最初の値の違いが、どれだけの本数に効くかは数えていません。
3. **「違う」の ADX の計算の関数は、最初の値の作り方だけの違いです。**漸化式は同じです。
4. **使い方の記録の「使い方の種類」は、9種の全部で「教科書に無い」です。**照らした8行は、出口の反転と前提崩れの印です。どちらの調べにも、この2つの使い方を名指しした文はありませんでした。
5. **場面の欄（③-3）は、教科書がその場面で使う・使わないと書いているかで読みました。**DI差と基準線は、教科書がレンジでだましが多い・頼らないと書くので「違う」にしました。
6. **全指標の調べの基準線の行は、転換線の文を多く使っています**（全指標の調べ自身の注にも書いてある）。その行の値は、基準線の照らしには使わず、6 に書きました。
7. **9種の文書の逐語は、文書の表のとおり引用符（"）ごと写しました。**全指標の調べの逐語は、json の文字列をそのまま写しました（計算の式は json の並びのまま）。
8. **9種の文書の「いまの値と違う所」は、照らしの結果として写していません**（依頼書のとおり。前の版 1f6f5ff の指標データと照らした文のため）。
9. **デイトレの値とロングの行は照らしていません。**数は json の「照らさなかった行の数」に在ります。デイトレの値は、指標の記録の軸ごとのデイトレの代表の値と、照らしたショートの行のデイトレの閾値を数えました。

| 指標 | デイトレの値 | ロングの行 |
|---|---|---|
| RSI | 3 | 2 |
| ADX | 3 | 2 |
| DI差 | 1 | 0 |
| BB幅 | 2 | 0 |
| BB%b | 2 | 0 |
| ATR% | 1 | 0 |
| 基準線 | 1 | 0 |
| 包み足 | 0 | 0 |
| 帯pivot | 1 | 0 |

## 8. 始めた時刻と終えた時刻

- 始めた時刻＝Wed Nov  4 07:21:55 UTC 2026（date -u）
- 終えた時刻＝Wed Nov  4 07:37:07 UTC 2026（date -u）
