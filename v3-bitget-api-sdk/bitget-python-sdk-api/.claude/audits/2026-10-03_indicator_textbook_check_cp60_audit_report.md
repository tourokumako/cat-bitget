# 監査結果 cp60 — M2-C でオンにした指標が、教科書どおりの作りかを照らす・CP60

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-03_m2_law_faithful_range_20261003_plan_cp60_audit_request.md`（291行・`wc -l` で確認）
- 依頼書のハッシュ値: 634fd5221ea55ec3230597a86ca821ac72a9e1f135923c9de0d0452a66258e4c
- 監査の相手と版（依頼書に書いてあるもの）:
  - `.claude/ratchet/indicator_switch.json`／b0080a8752e85d2a
  - `scripts/priority_rebuild/indicator_reference_diag.py`／d4f13163ebc7574d
  - `scripts/priority_rebuild/observe_diag.py`／3d33634067900696
- 監査が照らしたハッシュ値（`shasum -a 256` の頭16文字）: 3本とも依頼書と一致した（b0080a8752e85d2a／d4f13163ebc7574d／3d33634067900696）。監査の終わりに測り直しても同じだった。
- 実施日: 2026-10-03（18:5x〜）
- 監査のやり方: 監査役の CC が依頼書を読み、Plan サブエージェントを6つ cold start で起動した（担当＝A 古典21件・B 構造と価格帯28件・C 勢い24件・D 移動平均33件・E トレンドと量と統計35件・F geo_on 2件と全体の作り）。返ってきた所見は、監査役が全部の行を実物で開いて照らした。サブエージェントは hook に止められて python を走らせられなかったため、値で確かめられるものは監査役が作業場（`.claude/audits/cp60_work/`）の写しの道具で走らせた（10節）。
- ★実際に読み込まれるライブラリ: `python3` は `/usr/local/bin/python3`・`pandas_ta_classic` は `/usr/local/lib/python3.13/site-packages` の **0.6.52**。`.venv` に 0.6.20 が別に在るが、走らせる道具は使っていない。ライブラリ由来の所見は全部 0.6.52 の行で確かめ直した。


## 2. 監査対象の型宣言

- 型＝材料の照合（指標の作りが教科書どおりか・変えた中身が engine_tuner の目的に貢献するか反するか・未来のデータを使っていないか）。
- 範囲＝`indicator_switch.json` の on 141種＋geo_on 2つ＝143件。オフの117種・法則の判定・帯の新しい部品・段・フローは対象外（依頼書の「監査対象外」）。
- 判定の基準＝engine_tuner の目的（permanent_rules.md:161「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的」）だけ。教科書どおりかどうかは基準にしない。指標の用途はレンジに限らず、上げ・下げ・急な値動きの判定と Entry・Exit の全部で考えた。
- ★決め打ちの数字の判定の決まり（全担当でそろえた）＝**教科書が利用者に任せている数字、または教科書と大きく違う数字を、名前にも設定にも出さずに固定し、engine_tuner が教科書の作りに届かないもの**は「反する」とした。根拠は目的の逐語の「パラメータ」と、engine_tuner_requirements.md:52「探す値を、CC が先に「点の一覧」で限定するもの」。**固定した値が教科書の既定と同じもの**（例＝T3 の 0.7・PSAR の 0.02/0.2・CKSP の 10/3/20）は教科書からの変更ではないので「該当なし」とし、探させるかは まこさんが決める項目（修正 64）に回した。教科書の値と差が小さいことを実測で確かめたもの（Keltner の ATR 10→14）は「残す」にした。


## 3. 監査対象の事実データの確認

### 数（起案者が数えた）

| 項目 | 起案者の数 | 監査が数えた数 | 合っているか |
|---|---|---|---|
| 参照表の登録 | 258 | 258（`grep -c '^_r('`） | 合う |
| オン（on） | 141 | 141（`jq '.on|length'`） | 合う |
| オフ（off） | 117 | 117（`jq '.off|length'`） | 合う |
| geo_on | 2（W%・帯内位置%） | 2 | 合う |
| ta と照らしている行 | 26（`grep -c 'ext=_ext'`） | **登録の単位で28**（`_r(` の塊ごとに ext= を数えた。差の2件＝Keltner上・下は `ext=lambda`） | 起案者の数は行の数で、登録は28。28件とも on |

- on の141件の源（jq で集計）＝ta だけ 46・ta と法則 17・法則だけ 74・法則とまこさんの個別の決定 2（MMI・S-Rタッチ1時間ATR）・恒等レシピだけ 1（volume_ratio）・ta と恒等レシピ 1（ROC）。
- ★「源＝ta」と「ta と値を照らした」は別物。sources.ta の64件のうち36件は TA_CLASS_MAP（indicator_reference_diag.py:4337-4362）でクラスの名前を当てただけで、値は照らしていない。そのうち close vs VWAP・DPO%・NVI傾き・PPO 3本・STC 2本は ta と作りが違う（4節）。

### 起案者が見つけた、教科書と違う作り（§38・§39・語で探しただけ）

| 起案者の行 | 起案者の判定 | 監査の判定 | 正しいか |
|---|---|---|---|
| 値段で割って%にした（MACD線%・ATR% ほか多数） | 貢献する | 貢献する。%化した on の列で向き・大小の意味が変わったものは0件（F が全列を確かめた。もともと0〜100や比の指標を値段で割っているものも0件） | 正しい |
| ダウ理論の3つ（高値切り上げ幅%・安値切り上げ幅%・構造破断距離%） | 貢献する | 貢献する（0 を閾値にすれば教科書の HH・HL の真偽がそのまま書け、幅の情報も持つ） | 正しい |
| pivotPP・R1・S1（移動窓） | 反する | 反する。ただし理由は「帯の候補になれない」ではなく、教科書の情報（前の日の値で1日動かない線）が材料に無く、移動窓版は「288本の範囲の中の位置と幅」の関数に縮んでいること | 結論は正しい・理由は不正確 |
| POC・VAH・VAL（移動窓・近似） | 反する | **VAH・VAL＝反する**（POC から隣を足す作りでなく、多い区画を場所に関係なく70%まで選ぶので帯がつながらない。作り直すと VAH は25.06%・VAL は23.32%の足でしか今の値と一致しない＝10節）。**POC＝分からない**（POC は一番厚い区画で、近似の影響を受けない＝作り直しても100%同じ。残る違いは期間だけ） | POC は誤り |
| EMA傾き・KAMA傾き%・WMA傾き%（5本の決め打ち） | 反する | 反する（比べる本数は教科書でも利用者が決めるパラメータ。5本だと close vs X% とほぼ同じ列＝EMA200 で相関 0.9871・WMA200 で 0.9457） | 正しい |
| close vs VWAP（移動窓＋終値） | 分からない | 分からない | 正しい |
| S-Rタッチ数（近似） | 分からない | 分からない。ただし理由の「強度の近似」は不正確＝数えているのは「今の値段の帯に掛かった足の本数」（滞在時間）で、強度ではない | 結論は正しい・理由は誤り |
| W字（近似）・形スコア（自作） | 分からない | **W字＝分からない**／**形スコア＝貢献する**（「前半の向き」を持つ列はほかに無く、消すと書ける条件が減るだけ） | 形スコアは誤り |


## 4. 所見

### 一般の観点

- ①統計学的妥当性 ＝ **FAIL**（STC は5分足の63.87%で1段目が凍り中央値が0.0＝分布が壊れている・AO%(12,26) は PPO(12,26) と相関 0.9974 の重複・傾きの5本は close vs X% と相関 0.65〜0.99 の重複）
- ②リスク管理 ＝ **PASS**（未来のデータを使う作りは143件で0件。上位足は足が閉じた時刻へずらしてから当てている＝observe_diag.py:1782-1785）
- ③認知バイアス ＝ **FAIL**（起案者は語で探しただけで、ライブラリの中の誤り（SAREXT・STC・ALMA の向き）と、今の足を含む n本高安を見落とした）
- ④ソフトウェア工学 ＝ **FAIL**（参照表の「教科書の独立実装」の多くが、教科書でなくカタログやライブラリの変形を写している＝照合が「自分と同じか」しか確かめていない。修正 59）
- ⑤再現性 ＝ **PASS**（版のハッシュ値は一致・乱数なし・同じ入力で同じ値）
- ⑥実行プロセス ＝ **FAIL**（既知答えが「値段が一定」だけの登録があり、売り側の誤りが「一致検証済み」で通った＝SAREXT。修正 60）
- ⑦主エージェントバイアス ＝ **FAIL**（参照表の「流儀」の欄とコメントに、実装や教科書と食い違う説明が在る＝修正 36〜41・54・56・58・61・66・70・71。例＝VP の「25分割」と実装の24区画・MACD の「標準の漸化式」と実装の adjust=True・HILO の「本数を持たない」と実際の high_length/low_length）

### Q1 — オンの143のうち、教科書と違う作りはどれか（優先度 A）

**答え＝143件を1件ずつ、実装のコードと教科書・原文で照らした。表の「教科書と違うか」の欄は、違う 72件・同じ 59件・同じ＋変換 12件（計算は教科書と同じで、値段や出来高で割る変換だけを足したもの）。**（数え方＝下の表の欄を awk で数えた・10節）

- 「違う」72件のうち、%化だけの違いは3件（転換線・基準線・Donchian幅）、起案者の表（依頼書の8行）に在るものは17件。
- 起案者の表の**ほかに見つけた違い**＝52件（72 − 3 − 17）。そのうち反する変更は 10件（n本高値・n本安値・AO%・STC・STCstoch・PPOヒスト・close vs SAREXT%・close vs ALMA%・close vs HILO%・close vs HWMA%）。
- ta と値を照らしている登録＝28件（ADX・DI差・MACD線%・MACDヒスト%・MACDシグナル線%・RSI・ROC・Stoch%K・Stoch%D・MFI・CMF・転換線・基準線・EMA傾き・ATR%・BB%b・BB幅・Donchian幅・close vs EMA・close vs SMA・Keltner上・Keltner下・AO%・CCI・UO・EFI比・EOM比・PVT傾き）。照らしていないもの＝115件。そのうち2つ目の照合（pandas-ta・scipy の EXT2）が付いた on は8件（realized_vol・OBV傾き・volume_ratio・swing高値距離・swing安値距離・n本高値・n本安値・fib位置）。Keltner の照合は倍率2のときだけ（indicator_reference_diag.py:836-837）。
- 未来のデータ（H2）＝0件。`center=True`・`shift(-` は実装の材料の行に無い（在るのは observe_diag.py:537 の説明文・4125 のコメント・5855-5857 のラベル側・7788-7804 の検査側だけ）。DPO は `centered=False` で呼び（1133-1134）、ライブラリの `shift(-t)` の側（dpo.py:34）は走らない。fractal は k本遅れで確定（553-560）。出来高プロファイルと S-Rタッチは [i−窓, i) で今の足を含まない（368・397）。帯（geo_on）は1時間足を label=right・closed=right で作り、確定した足だけを当てている。監査役が直し方の案8本を写しで走らせ、途中で切って計算し直しても値は全部一致した（10節）。

**143件の表**（URL の CS＝`https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/`・参照表＝indicator_reference_diag.py・実装＝observe_diag.py・lib＝pandas_ta_classic 0.6.52）

| # | 指標の名前 | 参照表の行 | 実装の行 | 教科書の出どころ（URL と原文） | 教科書と違うか | 何を変えたか | 判定 | 理由 |
|---|---|---|---|---|---|---|---|---|
| 1 | ADX | 977-980 | 766（_adx_di 277-285） | CS average-directional-index-adx「Subsequent ADX14 = ((Prior ADX14 x 13) + Current DX Value)/14」 | 同じ | 最初の値の置き方だけ | 該当なし | 助走60日（engine_tuner.py:99）で差は0 |
| 2 | DI差 | 981-983 | 767 | 同上「Divide the 14-day smoothed Plus Directional Movement (+DM) by the 14-day smoothed True Range」 | 同じ | 同上 | 該当なし | 同上 |
| 3 | MACD線% | 984-987 | 768-769 | CS macd「MACD Line: 12-day EMA - 26-day EMA」 | 違う | %化。平滑の最初の扱い（ewm の既定 adjust=True） | 貢献する（%化） | 符号は変わらない。adjust の差は助走で0。参照表の説明と食い違う＝修正 39 |
| 4 | MACDヒスト% | 988-1000 | 773-775 | 同上「MACD Histogram: MACD Line - Signal Line」 | 違う | 同上 | 貢献する（%化） | 同上 |
| 5 | MACDシグナル線% | 1001-1004 | 770-772 | 同上「Signal Line: 9-day EMA of MACD Line」 | 違う | 同上 | 貢献する（%化） | 同上 |
| 6 | RSI | 1005-1008 | 776（_rsi 263-269） | CS relative-strength-index-rsi「Average Gain = [(previous Average Gain) x 13 + current Gain] / 14」 | 同じ | 最初の値だけ | 該当なし | 助走で消える |
| 7 | ROC | 1009-1011 | 777 | CS rate-of-change-roc「ROC = [(Close - Close n periods ago) / (Close n periods ago)] * 100」 | 同じ | なし | 該当なし | 式そのもの |
| 8 | Stoch%K | 1012-1015 | 778-779 | CS stochastic-oscillator「%K = (Current Close - Lowest Low)/(Highest High - Lowest Low) * 100」 | 同じ | なし | 該当なし | — |
| 9 | Stoch%D | 1016-1018 | 780-781 | 同上「Fast %D: 3-period SMA of Fast %K」 | 同じ | なし | 該当なし | — |
| 10 | MFI | 1019-1022 | 783-786 | CS money-flow-index-mfi「Money Flow Index = 100 - 100/(1 + Money Flow Ratio)」 | 同じ | なし | 該当なし | — |
| 11 | CMF | 1023-1029 | 787-789 | CS chaikin-money-flow-cmf「20-period Sum of Money Flow Volume / 20 period Sum of Volume」 | 同じ | 高値＝安値の足を欠損にする（ta は0） | 該当なし | 該当の足は14本で全部 2023-03-24 の停止の埋め草 |
| 12 | OBV傾き | 1030-1035 | 790-791 | CS on-balance-volume-obv「If the closing prices equals the prior close price then: Current OBV = Previous OBV (no change)」「The absolute value of OBV is not important」 | 違う | 自作（OBV の n本の変化 ÷ n本の出来高の合計） | 貢献する | 出来高の水準に左右されない。向きは同じ。n は設定（10・20）で探せる |
| 13 | 転換線 | 1036-1039 | 792-793 | CS ichimoku-cloud「Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2」 | 違う | %化（線からの乖離%） | 貢献する | 符号＝線の上か下か |
| 14 | 基準線 | 1040-1043 | 794-795 | 同上「Kijun-sen (Base Line): (26-period high + 26-period low)/2」 | 違う | 同上 | 貢献する | 同上 |
| 15 | EMA傾き | 1054-1057 | 797・一覧 1297-1298 | CS slope「The number of days controls the period」／paperswithbacktest.com/course/moving-average-slope「MA Slope = (MAc - MAn) / n」 | 違う | 決め打ちの数字（比べる本数を5に固定）＋%化 | **反する** | 本数は教科書でも利用者のパラメータ。5本だと close vs EMA% と相関 EMA9 0.7835〜EMA200 0.9871。本数200なら 0.5530＝別の情報なのに engine_tuner は届かない＝修正 1〜6 |
| 16 | ATR% | 1059-1063 | 799（_atr 272-274） | CS average-true-range-percent-atrp「ATRP = (ATR / Close) * 100」 | 同じ | %化（教科書に在る ATRP） | 貢献する | 値段の高さに左右されない |
| 17 | BB%b | 1064-1067 | 801-802 | CS b-indicator「%B = (Price - Lower Band)/(Upper Band - Lower Band)」 | 同じ | なし（ddof=0＝ta と同じ） | 該当なし | — |
| 18 | BB幅 | 1068-1071 | 803-804 | CS bollinger-bandwidth「( (Upper Band - Lower Band) / Middle Band) * 100」 | 同じ | ×100 しないだけ | 該当なし | 大小の順は同じ |
| 19 | realized_vol | 1072-1074 | 805-806 | en.wikipedia.org/wiki/Realized_variance「RV(n) = ∑ r²」「the square root of the realized variance」 | 違う | 近似（平均を引いた標本の標準偏差。教科書の実現ボラは平均を引かない） | 分からない | 平均を引くと一方向の急な値動きの分が消える（n=20 で二乗の和の20%超が消える足が2.0%）＝修正 50 |
| 20 | Donchian幅 | 1075-1078 | 807-808 | tradingview.com/support/solutions/43000502253「Upper Channel = 20 Day High / Lower Channel = 20 Day Low」 | 違う | %化（幅÷終値） | 貢献する | 大小の順は同じ |
| 21 | volume_ratio | 1091-1093 | 816-817 | CS relative-volume-rvol「RVOL = current volume / average volume over the look-back period」 | 同じ | なし | 該当なし | — |
| 22 | swing高値距離 | 1132-1135 | 841（drop＝observe_config.json:173-175） | chartinglens.com/blog/support-and-resistance-levels「A swing is specifically "any candle that has higher lows on both sides"」 | 違う | 自作（中身は今の足を含む n本最高値＝n本高値と同じ式） | 該当なし | 全列が drop_columns に在り、実行器（engine_tuner_exec.py:2054-2056）が拒否＝材料に届かない。説明の直し＝修正 54 |
| 23 | swing安値距離 | 1136-1138 | 842（drop＝176-178） | 同上 | 違う | 同上 | 該当なし | 同上 |
| 24 | 高値からの経過バー | 1139-1145 | 843-844 | CS aroon「Aroon-Up = ((25 - Days Since 25-day High)/25) x 100」 | 違う | 期間（窓が n本・Aroon は n+1本） | 該当なし | 1本ずれるだけ・n は探せる |
| 25 | 安値からの経過バー | 1146-1152 | 845-846 | 同上 | 違う | 同上 | 該当なし | 同上 |
| 26 | 形スコア | 1153-1160 | 849-850 | 教科書に該当する数値の定義は無い | 違う | 自作（sign(c−c[n/2]) − sign(c[n/2]−c[n])） | 貢献する | 「前半の向き」を持つ列はほかに無い。shift は正だけ |
| 27 | W字 | 1161-1169 | 852・_w_flag 517-527 | CS（chart patterns）Double Bottom「Breaking resistance from the highest point between the troughs completes the Double Bottom Reversal.」 | 違う | 近似（ネック＝中央区間 t−3n/4+1〜t−n/4 の最高値・2つの底の窓と重なる）・決め打ち（tol=0.003 の1つ＝observe_config.json:270-272）・完成の足でなく条件が続く間ずっと1 | 分からない | 平らなもみ合いから中央の高値を抜けただけでも1になる＝修正 43 |
| 28 | fractal高値距離% | 1171-1177 | 856-857・_fractal_levels 530-563 | metatrader5.com Fractals「a series of at least five successive bars, with the highest HIGH in the middle, and two lower HIGHs on both sides」 | 同じ | %化 | 貢献する | k本遅れで確定（553-560） |
| 29 | fractal安値距離% | 1178-1182 | 858-859 | 同上（Down Fractal） | 同じ | %化 | 貢献する | 同上 |
| 30 | 高値切り上げ幅% | 1183-1188 | 860-861 | CS（dow theory）「An uptrend is defined by prices that form a series of rising peaks and rising troughs」 | 違う | 自作（法則を数字にした） | 貢献する | 0 を閾値に HH が書け、幅も持つ |
| 31 | 安値切り上げ幅% | 1189-1193 | 862-863 | 同上 | 違う | 同上 | 貢献する | 同上 |
| 32 | 構造破断距離% | 1194-1202 | 869-870 | 同上「An uptrend is considered in place until a lower low forms」 | 違う | 自作（1つ前に確定した谷との距離%） | 貢献する | fractal安値距離% と AND で「直近2つの確定安値を割った」が書ける |
| 33 | close vs EMA | 1204-1206 | 872-873 | ta utils「series.ewm(span=periods, min_periods=min_periods, adjust=False).mean()」 | 同じ | %化 | 貢献する | ext で照らしている |
| 34 | close vs SMA | 1207-1209 | 874 | ta utils「series.rolling(window=periods, min_periods=min_periods).mean()」 | 同じ | %化 | 貢献する | 同上 |
| 35 | close vs VWAP | 1210-1214 | 875-876 | CS（overlays）VWAP「VWAP calculations start fresh at the open and end at the close」「(H+L+C)/3」／tradingview.com/script/BdguQiFQ-Rolling-VWAP「particularly useful for instruments that trade 24/7 and do not have defined sessions」 | 違う | 期間（取引の始まりからの累積でなく288本の移動窓）・値段（典型価格でなく終値） | 分からない | 移動窓は24時間市場で確立した変種、日ごとの版は参加者が見る線。どちらが net に効くか測っていない＝修正 41 |
| 36 | Keltner上 | 1215-1218 | 877-878 | CS（overlays）Keltner「Upper Channel Line: 20-day EMA + (2 x ATR(10))」 | 違う | 決め打ち（ATR の本数を14に固定・名前に出ない） | 貢献する（残す） | 監査役の実測＝ATR10 版と相関 0.99816・帯の高さの差の中央値 0.0092%・上抜けの一致 99.24%＝ほぼ同じ列。説明の直し＝修正 55 |
| 37 | Keltner下 | 1219-1222 | 879-880 | 同上 | 違う | 同上 | 貢献する（残す） | 同上 |
| 38 | n本高値 | 1229-1231 | 883・一覧 1352-1354 | CS（overlays）Price Channels「Price Channels are based on prices prior to the current period.」 | 違う | 期間（今の足の高値を窓に含めた） | **反する** | 今の足の高値 ≥ 終値なので値は必ず0以下（監査役の実測＝最大 0.0000）。「前の n本の高値を上抜けた」とその幅（上げ・急な値動きの Entry の定番）が書けない。今の足を除くとプラスの足が24本で5.08%出る＝修正 15〜17 |
| 39 | n本安値 | 1232-1234 | 884 | 同上 | 違う | 同上 | **反する** | 下抜けが書けない |
| 40 | pivotPP | 1236-1240 | 886-887・一覧 1356-1359 | CS（overlays）Pivot Points「the prior day's high, low, and close」「do not change and remain in play throughout the day」 | 違う | 期間（前の期間で固定の線でなく、288本の移動窓の高安＋1本前の終値） | **反する** | 教科書の情報が材料に無い。移動窓版は ≒(2c−HH−LL)/(3·PP)＝範囲の中の位置と幅の関数に縮む＝修正 18〜21 |
| 41 | pivotR1 | 1241-1246 | 889-890 | 同上「Resistance 1 (R1) = (P x 2) - Low」 | 違う | 同上 | **反する** | 同上 |
| 42 | pivotS1 | 1247-1252 | 891-892 | 同上「Support 1 (S1) = (P x 2) - High」 | 違う | 同上 | **反する** | 同上 |
| 43 | fib位置 | 1253-1255 | 893-894 | CS（chart annotation）Fibonacci「After an advance, chartists apply Fibonacci ratios to define retracement levels」 | 違う | 近似（前の動きの山谷でなく n本の高安・比率を使わない連続の値＝Stochastic の素の %K÷100） | 貢献する | 0.382・0.618 は閾値で書ける。説明の直し＝修正 56 |
| 44 | POC | 1256-1263 | 895-896・_vp_levels 361-377 | luxalgo.com/library/concept/value-area「the completed value area is carried forward as a reference for later sessions」 | 違う | 期間（その日でなく直前288本の移動窓）・近似（足の出来高を終値の区画に全部置く・24区画） | 分からない | 一番厚い区画なので VA の近似の影響は無い（作り直しても100%同じ）。期間の違いだけが残る＝修正 42 |
| 45 | VAH | 1264-1270 | 897-898・373-376 | help.cqg.com MPVA「The value area begins calculating at the POC. The system expands the value area one price at a time in either direction until the value area represents 70%」 | 違う | 近似（POC から隣を足すのでなく、多い区画を場所に関係なく70%まで選ぶ） | **反する** | 出来高の山が2つあると間の薄い区画をまたいで広がり、「POC を中心につながった70%の帯」という定義が崩れる。作り直すと今の値と25.06%の足でしか一致しない＝修正 22・23 |
| 46 | VAL | 1271-1276 | 899-900 | 同上 | 違う | 同上 | **反する** | 同上（一致 23.32%） |
| 47 | MMI | 1288-1310 | 905・_mmi 473-514 | financial-hacker.com/the-market-meanness-index「if(Data[i] > m && Data[i] > Data[i-1]) nl++; … return 100.*(nl+nh)/(Length-1);」 | 同じ | なし | 該当なし | 原典の C と一致 |
| 48 | S-Rタッチ1時間ATR | 1313-1321 | 909-910・442-470・380-398 | chartinglens「You need to see price react at approximately the same price point at least twice」 | 違う | 自作と近似（はね返された山谷の回数でなく、直前 n本のうち今の終値±許容幅に掛かった足の本数） | 分からない | 滞在時間としては意味がある。教科書のタッチ数とは別物＝修正 44 |
| 49 | S-Rタッチ数 | 1322-1332 | 901・380-398 | 同上 | 違う | 同上（許容幅は固定） | 分からない | 同上 |
| 50 | AO% | 2484-2487 | 943・一覧 1397-1398 | tradingview.com/support/solutions/43000501826「lengthAO1=input(5…)」「lengthAO2=input(34…)」 | 違う | %化・決め打ち（5/34 を MACD の 12/26 で置き換え。material_param_ranges が空なので12と26の1点ずつ） | **反する**（期間）／貢献する（%化） | AO%(12,26) は PPO(12,26)（on）と相関 0.9974＝ほぼ同じ材料。教科書の 5/34 は 0.9274＝別の情報なのに届かない＝修正 13・14 |
| 51 | CCI | 2504-2506 | 922 | CS commodity-channel-index-cci「CCI = (Typical Price - 20-period SMA of TP) / (.015 x Mean Deviation)」 | 同じ | なし | 該当なし | 20本も範囲7〜21に入る |
| 52 | ER | 2531-2533 | 929 | trendspider.com/learning-center/kaufman-efficiency-ratio「ER = Change / Volatility」 | 同じ | なし | 該当なし | — |
| 53 | KST | 2558-2563 | 942 | CS prings-know-sure-thing-kst「KST = (RCMA1 x 1) + (RCMA2 x 2) + (RCMA3 x 3) + (RCMA4 x 4)」 | 違う | 決め打ち（教科書の100倍＝kst.py の 100 * (…)） | 貢献する（残す・影響なし） | 閾値は分位で切るので定数倍は効かない |
| 54 | KSTシグナル | 2564-2566 | 950 | 同上「Signal Line = 9-period SMA of KST」 | 違う | 同上 | 貢献する（残す・影響なし） | 同上 |
| 55 | PPO | 2597-2599 | 971-972 | CS percentage-price-oscillator-ppo「{(12-day EMA - 26-day EMA)/26-day EMA} x 100」 | 違う | 平滑のしかた（lib の mamode 既定で EMA→SMA） | 貢献する | 教科書の EMA 版は MACD線%（on）と相関 0.9998＝同じ材料。SMA 版は 0.9082＝別の材料として残る。説明の直し＝修正 57 |
| 56 | PPOシグナル | 2600-2601 | 975-976 | 同上「9-day EMA of PPO」 | 違う | PPO の SMA を受け継ぐ | 貢献する | 同上 |
| 57 | PPOヒスト | 2602-2604 | 973-974 | 同上「The histogram is positive when PPO is above its 9-day EMA and negative when PPO is below its 9-day EMA.」 | 違う | 符号や向き（参照表で「状態量＝加速（向きを持たない）」/none） | **反する** | gen_signal_families.py:122-123 が状態量を向きの材料から外す。起案者自身の実測（参照表:997「PPOヒスト 加速上げ +0.0001571／加速下げ −0.007139」＝符号が分かれる＝順張り値の側）が在るのに直していない。実装は directional=True で食い違う＝修正 27 |
| 58 | PVO | 2605-2607 | 977-978 | CS percentage-volume-oscillator-pvo「((12-day EMA of Volume - 26-day EMA of Volume)/26-day EMA of Volume) x 100」 | 同じ | なし | 該当なし | — |
| 59 | PVOシグナル | 2608-2609 | 981-982 | 同上「9-day EMA of PVO」 | 同じ | なし | 該当なし | — |
| 60 | PVOヒスト | 2610-2611 | 979-980 | 同上「PVO - Signal Line」 | 同じ | なし | 該当なし | 出来高の勢い＝状態量で正しい |
| 61 | SMC_SWEEP | 2630-2633 | 986（lib momentum/smc_sweep.py） | luxalgo.com/library/concept/liquidity-sweep「The classic anatomy is a wick through a prior swing high or low…followed by a close back inside the old range.」 | 違う | 近似（確定した山谷でなく直前15本の高安）・自作（陽線陰線の条件・ヒゲが実体の1.5倍）・決め打ち 15/1.5 | 分からない | 買い側の刈り取りの62.07%は1本前の安値を割っただけ（C の awk 実測）＝修正 46 |
| 62 | SQZ_ON | 2641-2644 | 991（lib squeeze） | CS（overlays）TTM Squeeze「Carter uses 20 periods for the moving average and ATR, and 1.5 for the ATR multiplier」 | 違う | 平滑のしかた（Keltner の中心を終値の SMA・幅を真の値幅の SMA） | 分からない | Carter の作りとの一致率 92.07%（C の awk 実測）＝修正 47 |
| 63 | STC | 2652-2655 | 1000（lib momentum/stc.py:180） | ta-lib.org/functions/stc.html「When a range is zero, the fraction keeps its previous value」「Fast period: 23 / Slow period: 50」 | 違う | **符号や向き（ライブラリの誤り）**＝1段目を「MACD の窓の最小値 > 0」のときだけ計算する（stc.py:180。2段目の :197 は「範囲 > 0」）・期間 12/26（原典 23/50） | **反する** | 監査役の実測＝直近10万本の63.87%で1段目が凍り、STC の中央値が0.0。教科書の式に直すと中央値50.00・今の値との相関 0.1569＝下げの間の周期が消えている＝修正 25・26 |
| 64 | STCstoch | 2656-2658 | 1001 | 同上（1段目） | 違う | 同上の誤りがこの列そのもの | **反する** | 同上 |
| 65 | StochRSI%K | 2664-2666 | 1005-1006 | CS stochrsi「StochRSI = (RSI - Lowest Low RSI) / (Highest High RSI - Lowest Low RSI)」 | 違う | 平滑のしかた（SMA3 でならした。原式はならさない） | 分からない | ならさない値との相関 0.8795（C の awk 実測）・ならさない値はカタログに無い＝修正 48 |
| 66 | StochRSI%D | 2667-2668 | 1007-1008 | 同上（原式に %D は無い） | 違う | %K をさらに SMA3 | 分からない | 同上 |
| 67 | TRIX | 2673-2678 | 1009-1010 | CS trix「TRIX = 1-period percent change in Triple-Smoothed EMA」 | 同じ | なし | 該当なし | — |
| 68 | TRIXシグナル | 2679-2680 | 1011-1012 | 同上「The signal line is a 9-day EMA of the TRIX.」 | 違う | 平滑のしかた（lib trix.py:45 の rolling(signal).mean()＝SMA） | 分からない | EMA 版とヒストの符号の一致 94.42%＝修正 49 |
| 69 | TRIXヒスト | 2681-2683 | 1013-1014 | 同上 | 違う | SMA を受け継ぐ・符号や向き（状態量/none・directional=False） | 分からない | PPOヒスト と同じ形だが、加速の柱をまだ測っていない＝修正 49 |
| 70 | TSI | 2684-2686 | 1018-1019 | CS true-strength-index「First Smoothing = 25-period EMA of PC. Second Smoothing = 13-period EMA」 | 違う | 決め打ち（25/13 を MACD の 26/12 で置き換え） | 貢献する（残す・差1本） | 差は1本ずつで情報は同じ |
| 71 | TSIシグナル | 2687-2688 | 1020-1021 | 同上「an exponential moving average of TSI」 | 同じ | なし | 該当なし | — |
| 72 | TSIヒスト | 2689-2691 | 1022-1024 | 同上 | 違う | 符号や向き（状態量/none） | 分からない | TRIXヒスト と同じ＝修正 49 |
| 73 | UO | 2692-2695 | 1017 | CS ultimate-oscillator「UO = 100 x [(4 x Average7)+(2 x Average14)+Average28]/(4+2+1)」 | 同じ | なし | 該当なし | — |
| 74 | close vs ALMA% | 2712-2714 | 1040・1068-1070（lib overlap/alma.py:37） | tradingview.com/support/solutions/43000594683「by setting it to 1, you can make it align fully to the current price」 | 違う | **符号や向き（ライブラリ）**＝重みを w_norm[::-1] で逆に当て、山が古い側に来る | **反する** | 監査役の実測＝一番新しい足の重み 0.0000・山は新しい側から7本目。9本で6.44本・20本で15.20本遅れる（SMA より遅い）。教科書の向きなら1.56本・3.80本。遅れの小さい ALMA が材料に無い＝修正 28・29 |
| 75 | close vs DEMA% | 2715-2719 | 1041 | ta-lib.org/functions/dema.html「DEMA = 2*EMA1 - EMA2」 | 同じ | %化 | 貢献する | — |
| 76 | close vs FWMA% | 2720-2724 | 1066 | ライブラリ固有（外部の教科書なし） | 同じ | %化 | 貢献する | 重みは新しい足ほど大きい |
| 77 | close vs HILO% | 2727-2730 | 1080-1081・一覧 1454 | luxalgo.com/library/concept/gann-hilo-activator「n = 3」「HiAvg_t = average of the previous 3 highs」 | 違う | 決め打ち（高値13本・安値21本＝教科書の3本と違い、名前に出ないので探せない）・平滑（描く線が今の足を含む平均） | **反する**（本数）／分からない（線の作り） | 教科書の3本に届かない。observe_diag.py:1038 の理由「本数を持たない指標」は事実と違う（hilo.py:15-16 に high_length・low_length が在る）＝修正 30〜32 |
| 78 | close vs HMA% | 2731-2733 | 1042 | alanhull.com/the-hull-moving-average「Integer(SquareRoot(Period)) WMA [2 x Integer(Period/2) WMA(Price) – Period WMA(Price)]」 | 同じ | %化 | 貢献する | — |
| 79 | close vs HT_TRENDLINE% | 2734-2740 | 1082-1083 | ta-lib.org/functions/ht_trendline.html（Ehlers の入力は (H+L)/2） | 違う | 近似（入力を終値に） | 分からない | 修正 53 |
| 80 | close vs HWMA% | 2741-2744 | 1084・一覧 1456 | mql5.com/en/code/20856「HWMA[i] = F[i] + V[i] + 0.5 * A[i]」（3つの係数は利用者の入力） | 違う | 決め打ち（0.2・0.1・0.1 に固定・名前に出ない） | **反する** | 出どころでは利用者の値なのに1点に限っている。理由は1038行の事実と違う説明だけ＝修正 33〜35 |
| 81 | close vs JMA% | 2745-2749 | 1043 | 原式は非公開（Jurik Research） | 違う | 近似（復元式） | 分からない | データ不足（理由＝原式が公開されていない） |
| 82 | close vs KAMA% | 2750-2752 | 1044 | CS kaufmans-adaptive-moving-average-kama「Current KAMA = Prior KAMA + SC x (Price - Prior KAMA)」 | 違う | 初期値だけ（n本目の終値・教科書は SMA） | 該当なし | 助走60日で差は e^−72 |
| 83 | KAMA傾き% | 2753-2754 | 1044・1071-1073・一覧 1438-1441 | luxalgo.com/library/indicator/tSPnFR8g-moving-average-slope「Slope_t = (MA_t − MA_{t−k}) / k」「Slope lookback (k) – commonly between 1 and 10」 | 違う | 決め打ち（k=5） | **反する** | 監査役の実測＝close vs KAMA% との相関 KAMA20 0.6518〜KAMA200 0.8174。k を変えると 0.11〜0.73 で別の情報＝修正 7〜11 |
| 84 | close vs LINREG% | 2755-2757 | 1045 | ta-lib.org/functions/tsf.html「Fit y=b+m_x over window」 | 同じ | %化 | 貢献する | — |
| 85 | close vs LRb% | 2775-2777 | 1046 | 同上「b = (SumY - m_SumX)/N」 | 同じ | %化 | 貢献する | — |
| 86 | close vs MAMA% | 2783-2787 | 1085・627-628 | ta-lib.org/functions/mama.html「optInFastLimit: 0.5」（Ehlers の入力は (H+L)/2） | 違う | 近似（入力が終値） | 分からない | 修正 53 |
| 87 | close vs FAMA% | 2788-2791 | 1086 | 同上 | 違う | 同上 | 分からない | 同上 |
| 88 | close vs MCGD% | 2792-2794 | 1047 | capital.com mcginley-dynamic-indicator「MD = MD1 + (Price – MD1) / (N * (Price/MD1)^4)」 | 同じ | %化 | 貢献する | — |
| 89 | close vs MIDPOINT% | 2795-2798 | 1048 | ta-lib MIDPOINT（ライブラリの出典） | 同じ | %化 | 貢献する | — |
| 90 | close vs MIDPRICE% | 2799-2802 | 1049 | ta-lib.org/functions/midprice.html「MIDPRICE = (Highest(High, N) + Lowest(Low, N)) / 2」 | 同じ | %化 | 貢献する | — |
| 91 | close vs MMAR% | 2803-2806 | 1094-1095 | tradingview.com/script/a87v7d4L-Madrid-Moving-Average-Ribbon「multiple EMAs with incrementally increasing periods」 | 違う | 自作（帯を1本の EMA(k) に縮めた） | 貢献する | k は範囲で探せる。助走の後は close vs EMA と同じ値＝重複（修正 63） |
| 92 | close vs PWMA% | 2807-2810 | 1050 | ライブラリ固有（二項係数の重み） | 同じ | %化 | 貢献する | — |
| 93 | close vs RAINBOW% | 2814-2816 | 1105-1107 | investopedia（Widner・ライブラリの出典） | 同じ | L と k を名前に出して探せる | 貢献する | — |
| 94 | close vs RMA% | 2817-2821 | 1051 | incrediblecharts（Wilder・ライブラリの出典） | 同じ | %化 | 貢献する | — |
| 95 | close vs SINWMA% | 2827-2829 | 1052 | tradingview.com/script/6MWFvnPO-Sine-Weighted-Moving-Average | 同じ | %化 | 貢献する | — |
| 96 | close vs SSF% | 2830-2833 | 1053（lib overlap/ssf.py:15） | linnsoft.com/topic/super-smoother-and-roofing-filter「Filt = c1*(Close + Close[1]) / 2 + c2*Filt[1] + c3*Filt[2];」 | 違う | 平滑のしかた（入力を2本の平均にしていない） | 分からない | 修正 51 |
| 97 | close vs SWMA% | 2834-2837 | 1054 | TradingView ta.swma（4本固定 1,2,2,1・ライブラリの出典） | 違う | 期間（4本固定を n本に広げた） | 貢献する | n=4 で教科書と一致し、n を探せる |
| 98 | close vs T3% | 2838-2841 | 1057-1058 | ta-lib.org/functions/t3.html「T3 = c1_e6 + c2_e5 + c3_e4 + c4_e3」「default … 0.7」 | 同じ | %化 | 貢献する | — |
| 99 | close vs TEMA% | 2842-2845 | 1059 | ta-lib.org/functions/tema.html「TEMA = 3_EMA1 - 3_EMA2 + EMA3」 | 同じ | %化 | 貢献する | — |
| 100 | close vs TRIMA% | 2846-2849 | 1060（lib trima.py:32-35） | ta-lib.org/functions/trima.html「even: SMA(SMA(x,period/2),period/2+1)」 | 違う | 期間（n が偶数のとき窓が n+1本） | 分からない | 修正 52 |
| 101 | close vs TSF% | 2850-2855 | 1061 | ta-lib.org/functions/tsf.html「output = b + m_N」 | 同じ | %化 | 貢献する | — |
| 102 | close vs VIDYA% | 2856-2859 | 1062（lib vidya.py:50） | ta-lib.org/functions/vidya.html「n = optInTimePeriod, m = optInCMOPeriod」 | 違う | 決め打ち（CMO の本数 m を n と同じに） | 分からない | 公開版の一つの作り。修正 52 |
| 103 | close vs VWMA% | 2860-2863 | 1063 | motivewave（ライブラリの出典） | 同じ | %化 | 貢献する | — |
| 104 | close vs WMA% | 2864-2867 | 1064 | 標準の WMA（重み 1..n） | 同じ | %化 | 貢献する | — |
| 105 | WMA傾き% | 2868 | 1064・1071-1073・一覧 1483-1486 | #83 と同じ LuxAlgo | 違う | 決め打ち（k=5） | **反する** | 監査役の実測＝close vs WMA% との相関 WMA20 0.7719〜WMA200 0.9457＝修正 7〜12 |
| 106 | close vs ZLMA% | 2869-2871 | 1065 | ta-lib.org/functions/zlema.html「Lag = [Period – 1] / 2」 | 同じ | %化 | 貢献する | — |
| 107 | AROONU | 2896 | 1122 | CS aroon「((25 - Days Since 25-day High)/25) x 100」 | 同じ | なし | 該当なし | — |
| 108 | AROOND | 2899 | 1123 | 同上「((25 - Days Since 25-day Low)/25) x 100」 | 同じ | なし | 該当なし | — |
| 109 | AROONOSC | 2902 | 1124 | 同上（Up − Down） | 同じ | なし | 該当なし | — |
| 110 | CHOP | 2904 | 1125 | incrediblecharts.com/indicators/choppiness-index.php「Choppiness Index = 100 * Log10 { Sum(TrueRange,n) / [ Maximum(TrueHigh,n) - Minimum(TrueLow,n) ] } / Log10(n)」 | 同じ | なし | 該当なし | — |
| 111 | close vs CKSPl% | 2908 | 1139・_ck 632-633 | ta-lib.org/functions/cksp.html「FirstHighStop = MAX(High, TimePeriod) - Multiplier * ATR(TimePeriod)」「a multiplier of 3 and a stop period of 20」 | 同じ | %化 | 貢献する（%化） | 本の数字どおり。説明の直し＝修正 66 |
| 112 | close vs CKSPs% | 2913 | 1140 | 同上「FirstLowStop = MIN(Low, TimePeriod) + Multiplier * ATR(TimePeriod)」 | 同じ | %化 | 貢献する（%化） | 同上 |
| 113 | DPO% | 2916 | 1133-1134（lib dpo.py:32） | CS detrended-price-oscillator-dpo「Price - X-period SMA from {X/2 + 1} periods in the future」 | 違う | 期間（教科書を時点 t で作れる形は「k本前の終値 − いまの SMA」。実装は「いまの終値 − k本前の SMA」）・%化。未来は使っていない | 分からない | 修正 37・45 |
| 114 | close vs PMAX% | 2922 | 1141-1142（lib pmax.py:30・34） | github.com/fmzquant/strategies/blob/master/Profit-Maximizer-PMax.md「dir := dir == -1 and MAvg > shortStopPrev ? 1 : …」 | 違う | 自作（ライブラリ）＝原作は移動平均を逆指値と比べるが、lib は終値と比べる（SuperTrend の型） | 分からない | 修正 45 |
| 115 | close vs PSAR% | 2926 | 1143-1144・_ps 636-637 | CS parabolic-sar「Current SAR = Prior SAR + Prior AF(Prior EP - Prior SAR)」 | 同じ | %化 | 貢献する（%化） | 売り側でマイナス＝向きが一貫 |
| 116 | PSAR加速 | 2931 | 1145 | 同上「Starting at .02, AF increases by .02」「maximum of .20」 | 同じ | なし | 該当なし | — |
| 117 | PSAR反転 | 2935 | 1146 | 同上 | 同じ | なし | 該当なし | — |
| 118 | close vs SAREXT% | 2943 | 1147-1148（lib trend/sarext.py:137） | raw.githubusercontent.com/TA-Lib/ta-lib/main/src/ta_func/ta_SAREXT.c「TA_SAREXT returns negative values when the position is short」 | 違う | **符号や向き**＝売り側の SAR が負の数で返り、そのまま終値で割る | **反する** | 監査役の実測＝下げの列で close vs SAREXT% が −191.89%（PSAR は −8.11%）。売り側の中では SAR から下に離れるほど値が大きくなる＝向きが逆。参照表の「何%離れているか」とも食い違う＝修正 24・36 |
| 119 | VHF | 2950 | 1126 | docs.motivewave.com/studies/u-v「vhf = (highest - lowest) / sumD;」 | 同じ | なし | 該当なし | — |
| 120 | VTXP | 2953 | 1127-1128 | CS vortex-indicator「+VI14 = +VM14/TR14」 | 同じ | なし | 該当なし | — |
| 121 | VTXM | 2956 | 1129-1130 | 同上「-VI14 = -VM14/TR14」 | 同じ | なし | 該当なし | — |
| 122 | EFI比 | 3181 | 1152-1153 | CS force-index「Force Index(13) = 13-period EMA of Force Index(1)」 | 同じ＋変換 | 無次元化（終値×平均出来高で割る） | 貢献する | 符号を保つ |
| 123 | EOM比 | 3186 | 1155-1157 | CS ease-of-movement-emv「14-period simple moving average of 1-period EMV」 | 同じ＋変換 | 無次元化 | 貢献する | 符号を保つ |
| 124 | NVI傾き | 3199 | 1160（lib volume/nvi.py:37-40） | CS negative-volume-index-nvi「Add the Percentage Price Change to Cumulative NVI when Volume Decreases」／en.wikipedia.org/wiki/Negative_volume_index（Fosback の掛け算） | 違う | NVI は StockCharts の足し算の流儀（Fosback と ta は掛け算）・自作（n本の差。n は obv_slope_periods で探せる） | 貢献する | 足し算の差は起点や積み上げた水準に左右されない。説明の直し＝修正 38 |
| 125 | PVT傾き | 3216 | 1164-1165 | tradingview.com/support/solutions/43000502345「PVT = [((CurrentClose - PreviousClose) / PreviousClose) x Volume] + PreviousPVT」 | 同じ＋変換 | 自作（n本の差 ÷ n本の出来高の合計） | 貢献する | 符号を保つ・ta と照らしている |
| 126 | MAD比 | 3393 | 1183 | en.wikipedia.org/wiki/Average_absolute_deviation「the mean of the data's absolute deviations around the data's mean」 | 同じ＋変換 | %化 | 貢献する | — |
| 127 | stdev% | 3399 | 1184 | 統計の一般定義 | 同じ＋変換 | %化 | 貢献する | — |
| 128 | close vs MEDIAN% | 3404 | 1185-1186 | 統計の一般定義 | 同じ＋変換 | %化 | 貢献する | — |
| 129 | close vs ABER_ZG% | 3609 | 1191・_ab 644-645 | georgepruitt.com「a breakout system based on Bollinger bands with a period length of 80 days and two standard deviations」／lib の説明「Few internet resources on definitive definition」 | 違う | 自作（ライブラリ）＝中心線が HLC3 の5本 SMA | 分からない | 修正 71・45 |
| 130 | ABER位置 | 3615 | 1192-1193 | 同上 | 違う | 自作（ライブラリ）＝帯が ±ATR15（原作は ±2σ・80本） | 分からない | 同上 |
| 131 | close vs ACCBL% | 3620 | 1194 | ta-lib.org/functions/accbands.html「Lower = SMA(lowerRaw, N)」 | 同じ＋変換 | %化 | 貢献する | — |
| 132 | close vs ACCBU% | 3626 | 1195 | 同上「Upper = SMA(upperRaw, N)」 | 同じ＋変換 | %化 | 貢献する | — |
| 133 | close vs CE_L% | 3632 | 1196 | CS chandelier-exit「Chandelier Exit (long) = 22-day High - ATR(22) x 3」 | 同じ＋変換 | %化 | 貢献する | — |
| 134 | close vs CE_S% | 3637 | 1197 | 同上「Chandelier Exit (short) = 22-day Low + ATR(22) x 3」 | 同じ＋変換 | %化 | 貢献する | — |
| 135 | HWC位置 | 3647 | 1198 | mql5.com/en/code/20857「StDt[i] = Sqrt(Var[i-1])」 | 同じ | なし | 該当なし | 1本前の分散を使う |
| 136 | HWC幅% | 3653 | 1199 | 同上 | 同じ＋変換 | %化 | 貢献する | — |
| 137 | MASSI | 3657 | 1200 | CS mass-index「25-period sum of the EMA Ratio」 | 同じ | なし | 該当なし | — |
| 138 | THERMO% | 3676 | 1204（lib volatility/thermo.py:41-42） | tradingview.com/script/aBEEE6Y5-Elder-s-Thermometer-ETHERM「T = max( max(High − PrevHigh, 0), max(PrevLow − Low, 0) )」「Inside bars: Both protrusions clamp to zero」 | 違う | 符号や向き（ライブラリ）＝外へはみ出した幅でなく絶対値 | 分からない | 内はらみ足も0にならない＝修正 45・58 |
| 139 | TR% | 3691 | 1203 | CS average-true-range-atr「Current High less the current Low」 | 同じ＋変換 | %化 | 貢献する | — |
| 140 | UI | 3695 | 1208 | CS ulcer-index「Squared Average = (14-period Sum of Percent-Drawdown Squared)/14」 | 同じ | なし | 該当なし | — |
| 141 | HT_DCPHASE | 3929 | 1213-1214・_cyc 575-589 | ta-lib.org/functions/ht_dcphase.html「the instantaneous phase (in degrees)」 | 同じ | なし | 該当なし | ループは過去だけを参照 |
| 142 | W% | 4263-4264（RANGE_GEO_REF） | 1841（engine_tuner は engine_tuner_exec.py:2687） | 帯の材料＝metatrader5.com Fractals（上と同じ）・帯の束ね方＝luxalgo.com/library/indicator/support-resistance-zones-strength-classifier「Pivot highs and lows landing near the same price are clustered into a single S/R zone」 | 違う | 自作（帯そのものに教科書の定義が無い）・決め打ち（RG-v6 の tol=clamp(0.5×ATR%_1h,0.15%,0.6%)）・平滑（その ATR は TR の14本単純平均）・%化 | 貢献する（%化）／分からない（帯の作り） | 帯の上下はその時点で確定（fractal は j+2 で確定・1時間足は確定した足だけを当てる）。説明の食い違い＝修正 61 |
| 143 | 帯内位置% | 4265-4267 | 1837-1840（engine_tuner は 2683-2686） | tradingview.com/support/solutions/43000501971「%b = (Current Price - Lower Band) / (Upper Band - Lower Band)」 | 違う | 自作（W% と同じ帯）・尺度（上半分の幅を1にとる。下半分もレジスタンス側の幅で割る） | 貢献する（上半分）／分からない（下半分） | 下半分は足ごとに同じ値が違う場所を指す（sup_lo で −(Ts+G/2)/(Tr+G/2)）＝修正 65 |

行の数＝143。

修正の番号＝36・37・38・39・40・41・42・43・44・45・46・47・48・49・50・51・52・53・54・55・56・57・58・59・60・61・62・63・64・65・66・67・68・69・70・71

### Q2 — 見つけたそれぞれの変更は、engine_tuner の目的に貢献するか・反するか（優先度 A）

**答え＝143件の全部に判定を付けた（表の「判定」の欄の先頭の語で数えた）。反する 18件・分からない 25件・貢献する（残す）62件・該当なし（教科書と同じで変更が無い）38件。**

- **反する（18件・全部 Critical）**
  - 傾きの本数5の決め打ち＝EMA傾き・KAMA傾き%・WMA傾き%（3件）
  - 期間の決め打ちで教科書に届かない＝AO%（1件）・close vs HILO%（1件）・close vs HWMA%（1件）
  - 今の足を窓に含めた＝n本高値・n本安値（2件）
  - 移動窓で教科書の情報が無い＝pivotPP・pivotR1・pivotS1（3件）
  - 帯がつながらない近似＝VAH・VAL（2件）
  - ライブラリの中の誤りをそのまま使った＝close vs SAREXT%（符号）・STC・STCstoch（式）・close vs ALMA%（重みの向き）（4件）
  - 向きを持つのに状態量にした＝PPOヒスト（1件）
- 「反する」の理由は、どれも「engine_tuner がどう組んでも、その情報を材料から取り出せない」か「材料の値そのものが壊れている」のどちらか。目的の逐語「条件（指標、閾値、時間、パラメータ）の組み合わせを見つける」に照らして、探せる組み合わせを減らすか、壊れた材料を混ぜる。
- **分からない（25件＋重ねて持つもの3件）**＝realized_vol・W字・close vs VWAP・POC（期間）・S-Rタッチ1時間ATR・S-Rタッチ数・SMC_SWEEP・SQZ_ON・StochRSI%K・StochRSI%D・TRIXシグナル・TRIXヒスト・TSIヒスト・close vs HILO%（線の作り）・close vs HT_TRENDLINE%・close vs JMA%・close vs MAMA%・close vs FAMA%・close vs SSF%・close vs TRIMA%・close vs VIDYA%・DPO%・close vs PMAX%・close vs ABER_ZG%・ABER位置・THERMO%・W%（帯の作り）・帯内位置%（下半分）。比べ方は修正 41〜53・65 に「未決」で書いた（数え方＝指標の単位。close vs HILO% の線の作り・W% の帯の作り・帯内位置% の下半分の3件は、先頭の判定が「反する」か「貢献する」で、「分からない」を重ねて持つ）。
- **貢献する（残す）**＝%化だけの違い・ダウ理論の3つ・形スコア・OBV傾き・NVI傾き・PVT傾き・PPO 3本（SMA にしたことで MACD線% と別の材料になる）・MMAR・SWMA・Keltner（実測で差が小さい）・KST 2本と TSI（影響なし）ほか。
- **起案者の判定の正誤**（3節の表）＝8行のうち、結論が正しいもの5行・誤りが2行（POC・形スコア）・理由が誤り2行（pivot・S-Rタッチ数）。
- **未来のデータ**＝0件（Critical の H2 は無い）。

修正の番号＝1・2・3・4・5・6・7・8・9・10・11・12・13・14・15・16・17・18・19・20・21・22・23・24・25・26・27・28・29・30・31・32・33・34・35・41・42・43・44・45・46・47・48・49・50・51・52・53・65


## 5. 外部検索

依頼書の6件に1つずつ答える（全部 WebSearch / WebFetch で開いた。逐語は原文のまま）。

1. **ピボットポイントの教科書の定義**＝https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/pivot-points
   - 逐語「Pivot Point (P) = (High + Low + Close)/3」「Support 1 (S1) = (P x 2) - High」「Resistance 1 (R1) = (P x 2) - Low」
   - 逐語（日中の足）「the prior day's high, low, and close」・その線は「do not change and remain in play throughout the day」
   - 確かめたこと＝教科書のピボットは前の期間で固定の線。カタログの移動窓版は違う（#40〜42）。
2. **バリューエリア（POC・VAH・VAL）の計算**＝https://help.cqg.com/cqgic/25/Documents/marketprofilevalueareasmpva.htm
   - 逐語「The value area begins calculating at the POC. The system expands the value area one price at a time in either direction until the value area represents 70% of the TPOs, choosing the direction on each iteration on the basis of the number of TPOs the two prices adjacent to the current value area have.」
   - 補足＝https://www.tradingview.com/support/solutions/43000502040「Take the next row above the POC and the next row below the POC」「choose the row closer to the POC」・https://www.luxalgo.com/library/concept/value-area「The value area is the price band containing a set share of a period's trade, 70% by convention.」
   - 確かめたこと＝教科書は POC から隣を足していく（帯がつながる）。カタログは多い区画を選ぶ近似（#45・46）。
3. **VWAP の教科書の定義と、24時間市場での区切り**＝https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/volume-weighted-average-price-vwap
   - 逐語「VWAP calculations start fresh at the open and end at the close」「Cumulative(Volume x Typical Price)/Cumulative(Volume)」
   - 24時間市場＝https://www.tradingview.com/script/BdguQiFQ-Rolling-VWAP/「particularly useful for instruments that trade 24/7 and do not have defined sessions, such as cryptocurrencies」・https://www.tradingview.com/support/solutions/43000502018「by default, the source is hlc3」（Anchor の選択肢 Session・Week・Month）
   - ta＝https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html「class ta.volume.VolumeWeightedAveragePrice(high, low, close, volume, window: int = 14, fillna: bool = False)」
   - 確かめたこと＝教科書はセッション起点の累積＋典型価格。移動窓は24時間市場の変種。カタログは移動窓＋終値で、ta（移動窓＋典型価格）とも値段が違う（#35）。
4. **移動平均の傾き（slope）の測り方**＝https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/slope
   - 逐語「A 20-day Slope would be the rise-over-run of a 20-day linear regression」「The number of days controls the period」
   - 補足＝https://www.luxalgo.com/library/indicator/tSPnFR8g-moving-average-slope/「Slope_t = (MA_t − MA_{t−k}) / k」「Slope lookback (k) – commonly between 1 and 10 … default of 1 bar」・https://paperswithbacktest.com/course/moving-average-slope「MA Slope = (MAc - MAn) / n」
   - 確かめたこと＝比べる本数は利用者が決めるパラメータで、5 の出どころは無い（#15・83・105）。
5. **サポート・レジスタンスのタッチの数え方・ダブルボトムのネックライン**
   - タッチ＝https://chartinglens.com/blog/support-and-resistance-levels「You need to see price react at approximately the same price point at least twice — ideally three or more times.」
   - 帯の束ね方＝https://www.luxalgo.com/library/indicator/support-resistance-zones-strength-classifier/「Pivot highs and lows landing near the same price are clustered into a single S/R zone」「every zone is graded by how many times price has respected it」
   - ネックライン＝StockCharts の Double Bottom「two consecutive troughs that are roughly equal, with a moderate peak in between」「Breaking resistance from the highest point between the troughs completes the Double Bottom Reversal.」
   - 確かめたこと＝タッチはね返された回数を数える（カタログは滞在した足の本数＝#48・49）。ネックは2つの底の「間」の最高値（カタログは中央区間の最高値で、底の窓と重なる＝#27）。
6. **Q1 で見つけた、起案者の表に無い指標の教科書の定義**（指標ごとに1件）
   - n本高値・n本安値＝StockCharts Price Channels「Price Channels are based on prices prior to the current period.」
   - Keltner＝StockCharts「Upper Channel Line: 20-day EMA + (2 x ATR(10))」
   - AO＝https://www.tradingview.com/support/solutions/43000501826「lengthAO1=input(5…」「lengthAO2=input(34…」
   - STC＝https://ta-lib.org/functions/stc.html「When a range is zero, the fraction keeps its previous value (0 before any).」「Fast period: 23 / Slow period: 50 / Cycle period: 10」
   - PPO＝StockCharts「{(12-day EMA - 26-day EMA)/26-day EMA} x 100」「The histogram is positive when PPO is above its 9-day EMA」
   - TRIX＝StockCharts「The signal line is a 9-day EMA of the TRIX.」
   - TSI＝StockCharts「First Smoothing = 25-period EMA of PC. Second Smoothing = 13-period EMA」
   - StochRSI＝StockCharts「StochRSI = (RSI - Lowest Low RSI) / (Highest High RSI - Lowest Low RSI)」
   - KST＝StockCharts「KST = (RCMA1 x 1) + (RCMA2 x 2) + (RCMA3 x 3) + (RCMA4 x 4)」（×100 の記載なし）
   - TTM Squeeze＝StockCharts「Carter uses 20 periods for the moving average and ATR, and 1.5 for the ATR multiplier」
   - Liquidity Sweep＝https://www.luxalgo.com/library/concept/liquidity-sweep「The classic anatomy is a wick through a prior swing high or low…followed by a close back inside the old range.」
   - ALMA＝https://www.tradingview.com/support/solutions/43000594683「by setting it to 1, you can make it align fully to the current price」
   - HILO＝https://www.luxalgo.com/library/concept/gann-hilo-activator/「n = 3」「HiAvg_t = average of the previous 3 highs」
   - HWMA＝https://www.mql5.com/en/code/20856「HWMA[i] = F[i] + V[i] + 0.5 * A[i]」
   - SSF＝https://www.linnsoft.com/topic/super-smoother-and-roofing-filter「Filt = c1*(Close + Close[1]) / 2 + c2*Filt[1] + c3*Filt[2];」
   - TRIMA＝https://ta-lib.org/functions/trima.html「even: SMA(SMA(x,period/2),period/2+1)」
   - VIDYA＝https://ta-lib.org/functions/vidya.html「n = optInTimePeriod, m = optInCMOPeriod」
   - SAREXT＝https://raw.githubusercontent.com/TA-Lib/ta-lib/main/src/ta_func/ta_SAREXT.c「TA_SAREXT returns negative values when the position is short」
   - DPO＝StockCharts「Price - X-period SMA from {X/2 + 1} periods in the future」
   - PMax＝https://github.com/fmzquant/strategies/blob/master/Profit-Maximizer-PMax.md「dir := dir == -1 and MAvg > shortStopPrev ? 1 : dir == 1 and MAvg < longStopPrev ? -1 : dir」
   - NVI＝StockCharts「Add the Percentage Price Change to Cumulative NVI when Volume Decreases」・https://en.wikipedia.org/wiki/Negative_volume_index「adding NVIyesterday (Ct - Cy) / Cy to yesterday's NVI」
   - Aberration＝https://georgepruitt.com/check-out-my-interview-in-traders-magazine-germany/「a breakout system based on Bollinger bands with a period length of 80 days and two standard deviations」
   - Elder Thermometer＝https://www.tradingview.com/script/aBEEE6Y5-Elder-s-Thermometer-ETHERM/「T = max( max(High − PrevHigh, 0), max(PrevLow − Low, 0) )」「Inside bars: Both protrusions clamp to zero, producing Temperature = 0」
   - 実現ボラ＝https://en.wikipedia.org/wiki/Realized_variance「RV(n) = ∑ i=1 n r i,n 2」
   - 開けなかったもの＝ChartSchool の Donchian の頁（404・TradingView で代えた）・quantifiedstrategies.com（ボットの確認画面）・investopedia（取得拒否）・davenewberg・traders.com・mesasoftware の PDF（証明書切れか403）・HILO の 13/21 の出どころ（KivancOzbilgic の本文が取れない＝データ不足）。


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

「参照表を語で探しただけで、143を1件ずつ照らしていない」＝**事実だった。**監査が1件ずつ照らすと、語で探した8行のほかに違いが52件あり（%化だけの違いは除く）、そのうち10件が反する変更だった（n本高値・n本安値・AO%・STC・STCstoch・PPOヒスト・close vs SAREXT%・close vs ALMA%・close vs HILO%・close vs HWMA%）。とくにライブラリの中の誤り（SAREXT の符号・STC の式・ALMA の重みの向き）は、参照表に「流儀」の注記が無いので、語で探しても見つからない種類だった。

### 自己申告 2

「表の判定は起案者の考えで、どれも測っていない」＝**事実だった。**8行のうち結論の誤りは2行（POC＝分からない、形スコア＝貢献する）・理由の誤りは2行（pivot・S-Rタッチ数）。補足＝n本高安は起案者の表に無いが、worklog §37（562行）は「どれも移動窓」として帯の候補から外している。移動窓そのものは教科書の Price Channel どおりで、教科書と違うのは今の足を窓に含めていること（#38・39）。

### 自己申告 3

「ta と照らしている数（26）は grep の行数」＝**登録の単位では28件**（Keltner上・下が `ext=lambda` で grep に入らない）。28件とも on。143件では照らしているもの28・照らしていないもの115。さらに、sources.ta の64件のうち36件は名前の対応だけで、値は照らしていない。

### 自己申告 4

「傾き5本の決め打ちは on では EMA傾き・KAMA傾き%・WMA傾き% の3つ。OBV傾き・NVI傾き・PVT傾き は照らしていない」＝**3つは正しい。**OBV傾き・NVI傾き・PVT傾き の本数 n は `obv_slope_periods`（10・20）から来るので、決め打ちではなく範囲で探せる。3つとも、n本の差を出来高の合計で割る（OBV・PVT）か、足し算の NVI の差を取る作りで、出来高の水準や起点に左右されない＝貢献する。ただし NVI は StockCharts の足し算の流儀で、Fosback の原著と ta（掛け算）と値が違う。参照表の説明の直し＝修正 38。

### 自己申告 5

「%化で意味が変わった指標が無いかは確かめていない」＝**監査が確かめた。0件。**%化している on の列（MACD 3本・ATR%・Donchian幅・AO%・DPO%・MAD比・stdev%・HWC幅%・THERMO%・TR%・EFI比・EOM比・W% と close vs X% 全部）は、どれも値段の単位の量を正の数で割っているだけで、符号と大小の順は変わらない。もともと0〜100や比の指標（RSI・Stoch・MFI・CCI・PPO・PVO・TSI・TRIX・STC・UO・KST・AROON・CHOP・VHF・VTX・MASSI・UI・ER・MMI・CMF ほか）を値段で割っているものは無い。close vs SAREXT% は壊れているが、原因は%化の前の符号（ライブラリが売り側を負の数で返す）で、%化のせいではない。

### 自己申告 6

「外部の原文を開いたのは pivot と VAH/VAL だけ」＝**監査は143件の全部について、教科書・原文・ライブラリの出典を開いた**（5節）。原文が非公開のもの（JMA）と、出どころが取れなかったもの（HILO の 13/21）は「データ不足」と書いた。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ YES（根拠＝143件を1件1行の表（4節）で、参照表の行・実装の行・教科書の原文と照らした。教科書と違う作りは72件（ほかに変換だけの12件）。起案者の表に無い違いを52件見つけた。未来のデータは0件で、直し方の案8本を写しで走らせて切り詰め再計算の不一致0を確かめた）
- 問い2 ＝ YES（根拠＝143件の全部を「反する18・分からない25・貢献する62・該当なし38」に分けて理由を書いた。分からないものは比べる数字を修正 41〜53・65 に「未決」で書いた。起案者の8行の判定の正誤を3節に書いた）

### 結論と件数

- 結論＝CONDITIONAL-GO
- 結論の理由＝目的に反する変更が18件在る。直し方を8節に書いた。カタログの作り全体が反しているのではない＝143件のうち38件は教科書と同じで変更が無く、62件は貢献する変更。
- Critical＝35（反する変更18件の直し。1件の指標に複数のファイルの直しが要るので、修正の数で数えた。未来のデータは0）
- Major＝20（参照表の説明と実装の食い違い 6＝修正 36〜40・58、分からないものの比べ方 14＝修正 41〜53・65）
- Minor＝12（修正 54〜57・63・64・66〜71）
- Process＝4（修正 59〜62）
- 修正の番号は、見つけた順に振ったあと重さの見出しへ移したので、見出しの中で連番になっていない所がある（Major に 58・65、Minor に 63・64・66〜71）。件数は7節のとおり＝Critical 35・Major 20・Minor 12・Process 4。


## 8. 修正の指示

### Critical

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 797
直す前の文字:
~~~
_reg("EMA傾き", "EMA{}傾き%", True, lambda d, n: d.close.ewm(span=n, adjust=False).mean().pct_change(5) * 100)
~~~
直した後の文字:
~~~
_reg("EMA傾き", "EMA{}傾き%({})", True, lambda d, n, k: d.close.ewm(span=n, adjust=False).mean().pct_change(k) * 100)
~~~
根拠の抜き書き: indicator_reference_diag.py:1055「   "EMA の5本前からの変化率%", "EMA は標準・傾きの5本は本プロジェクトの流儀",」
状態: 未決
補足: 案が2つ在り、どちらにするかは まこさんが決める（未決）。案A＝この名前の変更。列の名前 `EMA{n}傾き%` を使う所（signal_families.json・exit_families.json・regime_laws.json・materials.json ほか16ファイル）を `EMA{n}傾き%(5)` に置き換える作業が別に要る。案B＝今の `EMA{}傾き%` を残し、別の種類 `EMA{}傾き%k{}` を足す。どちらでも修正 2〜6 を組で当てる

#### 修正 2
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1297-1298
直す前の文字:
~~~
    for n in cfg["ema_periods"]:
        addf("EMA傾き", n)
~~~
直した後の文字:
~~~
    for n in cfg["ema_periods"]:
        for k in cfg["ema_slope_lookbacks"]:
            addf("EMA傾き", n, k)
~~~
根拠の抜き書き: observe_diag.py:797「_reg("EMA傾き", "EMA{}傾き%", True, lambda d, n: d.close.ewm(span=n, adjust=False).mean().pct_change(5) * 100)」
状態: 未決
補足: 修正 1 と同じ

#### 修正 3
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_config.json
直す箇所: 130-135
直す前の文字:
~~~
 "ema_periods": [
  9,
  20,
  50,
  200
 ],
~~~
直した後の文字:
~~~
 "ema_periods": [
  9,
  20,
  50,
  200
 ],
 "ema_slope_lookbacks": [
  5
 ],
 "_ema_slope_lookbacks": "傾き（EMA・ほかの移動平均）を何本前と比べるか（監査 CP60）。5 は直す前の決め打ちと同じ値＝列の値は変わらない。広げるのは まこさんが recipes/search_limits.json の material_param_ranges に書く（CC は数字を作らない）。",
~~~
根拠の抜き書き: recipes/search_limits.json:44「  "material_param_ranges": {},」
状態: 未決
補足: 修正 1 と同じ

#### 修正 4
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1054-1057
直す前の文字:
~~~
_r(r"EMA(\d+)傾き%", "EMA傾き",
   "EMA の5本前からの変化率%", "EMA は標準・傾きの5本は本プロジェクトの流儀",
   "順張り値", "trend", tb=_tb_ema_slope, ext=_ext_ema_slope,
   known=lambda p: [(_flat(max(60, p[0] * 4)), [(-1, 0.0, 1e-9)])])
~~~
直した後の文字:
~~~
_r(r"EMA(\d+)傾き%\((\d+)\)", "EMA傾き",
   "EMA の k 本前からの変化率%（k は設定ファイル ema_slope_lookbacks・engine_tuner が探すパラメータ）",
   "EMA は標準の漸化式。比べる本数は教科書でも利用者が決めるパラメータ（ChartSchool Slope「The number of days controls the period」）＝決め打ちしない（監査 CP60）",
   "順張り値", "trend", tb=_tb_ema_slope, ext=_ext_ema_slope,
   known=lambda p: [(_flat(max(60, p[0] * 4, p[1] + 10)), [(-1, 0.0, 1e-9)])])
~~~
根拠の抜き書き: indicator_reference_diag.py:1055「   "EMA の5本前からの変化率%", "EMA は標準・傾きの5本は本プロジェクトの流儀",」
状態: 未決
補足: 修正 1 と同じ

#### 修正 5
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 317-321
直す前の文字:
~~~
def _tb_ema_slope(d, p):
    e = _ema_rec(d.close.to_numpy(float), p[0])
    out = np.full(len(e), np.nan)
    out[5:] = (e[5:] - e[:-5]) / e[:-5] * 100
    return _S(out, d)
~~~
直した後の文字:
~~~
def _tb_ema_slope(d, p):
    k = int(p[1])
    e = _ema_rec(d.close.to_numpy(float), p[0])
    out = np.full(len(e), np.nan)
    out[k:] = (e[k:] - e[:-k]) / e[:-k] * 100
    return _S(out, d)
~~~
根拠の抜き書き: indicator_reference_diag.py:320「    out[5:] = (e[5:] - e[:-5]) / e[:-5] * 100」
状態: 未決
補足: 修正 1 と同じ

#### 修正 6
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 823-825
直す前の文字:
~~~
def _ext_ema_slope(d, p):
    e = _ta.trend.EMAIndicator(d.close, p[0]).ema_indicator()
    return e.pct_change(5) * 100
~~~
直した後の文字:
~~~
def _ext_ema_slope(d, p):
    e = _ta.trend.EMAIndicator(d.close, p[0]).ema_indicator()
    return e.pct_change(int(p[1])) * 100
~~~
根拠の抜き書き: indicator_reference_diag.py:825「    return e.pct_change(5) * 100」
状態: 未決
補足: 修正 1 と同じ

#### 修正 7
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1071-1073
直す前の文字:
~~~
    if _nm not in ("JMA",):        # JMA は独立実装を書いていない＝傾きも作らない
        _reg(f"{_nm}傾き", f"{_nm}{{}}傾き%", True,
             lambda d, n, f=_mafn: f(d, n).pct_change(5) * 100)
~~~
直した後の文字:
~~~
    if _nm not in ("JMA",):        # JMA は独立実装を書いていない＝傾きも作らない
        # ★傾きの本数 k を名前に出す（監査 CP60）＝何本前と比べるかを engine_tuner が探す。
        #   例＝KAMA(20,5)傾き%＝KAMA20 の 5本前からの変化率%（直す前の KAMA20傾き% と同じ値）。
        _reg(f"{_nm}傾き", f"{_nm}({{}},{{}})傾き%", True,
             lambda d, n, k, f=_mafn: f(d, n).pct_change(k) * 100)
~~~
根拠の抜き書き: observe_diag.py:1073「             lambda d, n, f=_mafn: f(d, n).pct_change(5) * 100)」
状態: 未決
補足: 案が2つ在り、どちらにするかは まこさんが決める（未決）。案A＝上の書き換え＝ループの22系統の名前が全部 変わる。材料の一覧の addf（1441・1453・1462・1486 行の `addf(f"{_nm}傾き", n)` と `addf("FWMA傾き", n)`）を `for k in cfg["ema_slope_lookbacks"]: addf(..., n, k)` に直すのと組。案B＝今の名前を残し、k を持つ系統を別に足す。修正 8〜12 を組で当てる

#### 修正 8
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1881-1882
直す前の文字:
~~~
def _slope(ma: np.ndarray, d):
    return _S(ma, d).pct_change(5) * 100.0
~~~
直した後の文字:
~~~
def _slope(ma: np.ndarray, d, k: int = 5):
    return _S(ma, d).pct_change(k) * 100.0
~~~
根拠の抜き書き: indicator_reference_diag.py:1882「    return _S(ma, d).pct_change(5) * 100.0」
状態: 未決
補足: 修正 7 と同じ

#### 修正 9
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1926-1927
直す前の文字:
~~~
def _tb_slp_kama(d, p):
    return _slope(_kama(d.close.to_numpy(float), int(p[0])), d)
~~~
直した後の文字:
~~~
def _tb_slp_kama(d, p):
    return _slope(_kama(d.close.to_numpy(float), int(p[0])), d, int(p[1]))
~~~
根拠の抜き書き: indicator_reference_diag.py:1927「    return _slope(_kama(d.close.to_numpy(float), int(p[0])), d)」
状態: 未決
補足: 修正 7 と同じ

#### 修正 10
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2230-2231
直す前の文字:
~~~
def _tb_slp_wma(d, p):
    return _slope(_wma(d.close.to_numpy(float), int(p[0])), d)
~~~
直した後の文字:
~~~
def _tb_slp_wma(d, p):
    return _slope(_wma(d.close.to_numpy(float), int(p[0])), d, int(p[1]))
~~~
根拠の抜き書き: indicator_reference_diag.py:2231「    return _slope(_wma(d.close.to_numpy(float), int(p[0])), d)」
状態: 未決
補足: 修正 7 と同じ。off の21系統の _tb_slp_* も同じ形に直す

#### 修正 11
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2753-2754
直す前の文字:
~~~
_r(r"KAMA(\d+)傾き%", "KAMA傾き%",
   "KAMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_kama)
~~~
直した後の文字:
~~~
_r(r"KAMA\((\d+),(\d+)\)傾き%", "KAMA傾き%",
   "KAMA の k 本前からの変化率%（名前の2つ目の数字が k）", "同上。k は engine_tuner が探す（監査 CP60）", "順張り値", "trend", tb=_tb_slp_kama)
~~~
根拠の抜き書き: indicator_reference_diag.py:2754「   "KAMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_kama)」
状態: 未決
補足: 修正 7 と同じ

#### 修正 12
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2868
直す前の文字:
~~~
_r(r"WMA(\d+)傾き%", "WMA傾き%", "WMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_wma)
~~~
直した後の文字:
~~~
_r(r"WMA\((\d+),(\d+)\)傾き%", "WMA傾き%", "WMA の k 本前からの変化率%（名前の2つ目の数字が k）", "同上。k は engine_tuner が探す（監査 CP60）", "順張り値", "trend", tb=_tb_slp_wma)
~~~
根拠の抜き書き: indicator_reference_diag.py:2868「_r(r"WMA(\d+)傾き%", "WMA傾き%", "WMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_wma)」
状態: 未決
補足: 修正 7 と同じ

#### 修正 13
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1397-1399
直す前の文字:
~~~
    for (f_, s_, g_) in cfg["macd_params"]:
        addf("AO%", f_, s_)
        addf("APO%", f_, s_)
~~~
直した後の文字:
~~~
    for (f_, s_, g_) in cfg["macd_params"]:
        addf("AO%", f_, s_)
        addf("APO%", f_, s_)
    # ★AO の教科書の期間（Bill Williams・TradingView の逐語 lengthAO1=5・lengthAO2=34・監査 CP60）。
    #   macd_params の 12/26 だけだと AO% は PPO と相関 0.9974 の重複になる。
    for (f_, s_) in cfg.get("ao_params", []):
        addf("AO%", f_, s_)
~~~
根拠の抜き書き: recipes/search_limits.json:44「  "material_param_ranges": {},」
状態: 未決
補足: 案が2つ在り、どちらにするかは まこさんが決める（未決）。案A＝上と修正 14 を組で当てる。案B＝まこさんが search_limits.json の material_param_ranges に AO% の範囲を書く

#### 修正 14
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_config.json
直す箇所: 148-154
直す前の文字:
~~~
 "macd_params": [
  [
   12,
   26,
   9
  ]
 ],
~~~
直した後の文字:
~~~
 "macd_params": [
  [
   12,
   26,
   9
  ]
 ],
 "ao_params": [
  [
   5,
   34
  ]
 ],
 "_ao_params": "AO% の教科書の期間（TradingView の逐語 lengthAO1=input(5…)・lengthAO2=input(34…)・監査 CP60）。",
~~~
根拠の抜き書き: observe_diag.py:943「_reg("AO%", "AO%({},{})", True, lambda d, f_, s_: _pta6.ao(high=d.high, low=d.low, fast=f_, slow=s_) / d.close * 100)」
状態: 未決
補足: 修正 13 と同じ

#### 修正 15
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 883-884
直す前の文字:
~~~
_reg("close vs 本高値%", "close vs {}本高値%", True, lambda d, n: (d.close / d.high.rolling(n).max() - 1) * 100)
_reg("close vs 本安値%", "close vs {}本安値%", True, lambda d, n: (d.close / d.low.rolling(n).min() - 1) * 100)
~~~
直した後の文字:
~~~
# 教科書（StockCharts Price Channels）の逐語「Price Channels are based on prices prior to the current period.」＝今の足を含まない。
# 今の足を含むと close ≤ 高値 なので値は 0 で頭打ちになり、前 n 本の高値の上抜けとその幅が書けない（監査 CP60）。
_reg("close vs 本高値%", "close vs {}本高値%", True, lambda d, n: (d.close / d.high.rolling(n).max().shift(1) - 1) * 100)
_reg("close vs 本安値%", "close vs {}本安値%", True, lambda d, n: (d.close / d.low.rolling(n).min().shift(1) - 1) * 100)
~~~
根拠の抜き書き: observe_diag.py:883「_reg("close vs 本高値%", "close vs {}本高値%", True, lambda d, n: (d.close / d.high.rolling(n).max() - 1) * 100)」
状態: 未決
補足: 案が2つ在り、どちらにするかは まこさんが決める（未決）。案A＝上＝名前はそのままで今の足を外す。法則（regime_laws.json）でこの列の閾値を使っている所は意味が変わる。案B＝名前を変えて足し、今の列は残す。監査役が写しで走らせた＝24本で欠損でない 19,976本・切り詰め再計算の不一致 0/3。修正 16・17 を組で当てる

#### 修正 16
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1229-1234
直す前の文字:
~~~
_r(r"close vs (\d+)本高値%", "n本高値",
   "n 本最高値からの乖離%", "標準。swing高値距離% と同一の式＝重複列", "順張り値", "trend", tb=_tb_dist_high,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, (105.0 / 110.0 - 1) * 100, 1e-9)])])
_r(r"close vs (\d+)本安値%", "n本安値",
   "n 本最安値からの乖離%", "標準。swing安値距離% と同一の式＝重複列", "順張り値", "trend", tb=_tb_dist_low,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, 5.0, 1e-9)])])
~~~
直した後の文字:
~~~
def _tb_dist_high_prev(d, p):
    o, h, l, c, v = _arr(d)
    return _S((c / _S(_roll(h, p[0], "max"), d).shift(1).to_numpy(float) - 1) * 100, d)


def _tb_dist_low_prev(d, p):
    o, h, l, c, v = _arr(d)
    return _S((c / _S(_roll(l, p[0], "min"), d).shift(1).to_numpy(float) - 1) * 100, d)


_r(r"close vs (\d+)本高値%", "n本高値",
   "前の n 本（今の足を含まない）の最高値からの乖離%",
   "StockCharts Price Channels の逐語「Price Channels are based on prices prior to the current period.」＝今の足を含まない（監査 CP60）",
   "順張り値", "trend", tb=_tb_dist_high_prev,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, (105.0 / 110.0 - 1) * 100, 1e-9)])])
_r(r"close vs (\d+)本安値%", "n本安値",
   "前の n 本（今の足を含まない）の最安値からの乖離%",
   "同上（監査 CP60）", "順張り値", "trend", tb=_tb_dist_low_prev,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, 5.0, 1e-9)])])
~~~
根拠の抜き書き: indicator_reference_diag.py:1230「   "n 本最高値からの乖離%", "標準。swing高値距離% と同一の式＝重複列", "順張り値", "trend", tb=_tb_dist_high,」
状態: 未決
補足: 修正 15 と同じ。既知答え `_range_case` は山と谷が末尾から8本目と5本目に在るので、1本ずらしても答えは同じ（B の手の追跡・走らせていない＝承認の後の検査3で確かめる）

#### 修正 17
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 913-914
直す前の文字:
~~~
    "n本高値": (lambda d, p: _x2_donch(d, p, +1), "pandas-ta"),
    "n本安値": (lambda d, p: _x2_donch(d, p, -1), "pandas-ta"),
~~~
直した後の文字:
~~~
    "n本高値": (lambda d, p: (d.close / _pta.donchian(d.high, d.low, lower_length=int(p[0]), upper_length=int(p[0])).iloc[:, 2].shift(1) - 1) * 100, "pandas-ta"),
    "n本安値": (lambda d, p: (d.close / _pta.donchian(d.high, d.low, lower_length=int(p[0]), upper_length=int(p[0])).iloc[:, 0].shift(1) - 1) * 100, "pandas-ta"),
~~~
根拠の抜き書き: indicator_reference_diag.py:874「    dc = _pta.donchian(d.high, d.low, lower_length=n, upper_length=n)」
状態: 未決
補足: 修正 15 と同じ。swing の2行（911-912）は drop の列なので触らない

#### 修正 18
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 892（この行の後ろに足す）
直す前の文字:
~~~
_reg("close vs pivotS1%", "close vs pivotS1%{}", True, lambda d, n: (d.close / (2 * ((d.high.rolling(n).max()
     + d.low.rolling(n).min() + d.close.shift(1)) / 3) - d.high.rolling(n).max()) - 1) * 100)
~~~
直した後の文字:
~~~
_reg("close vs pivotS1%", "close vs pivotS1%{}", True, lambda d, n: (d.close / (2 * ((d.high.rolling(n).max()
     + d.low.rolling(n).min() + d.close.shift(1)) / 3) - d.high.rolling(n).max()) - 1) * 100)


def _pivot_prev_period(d):
    """教科書のピボット（StockCharts「Pivot Points」）＝前の期間の高値・安値・終値から作り、その期間のあいだ動かない線。
    逐語「the prior day's high, low, and close」「do not change and remain in play throughout the day」。
    日中の足＝前の UTC の日・日足＝前の月・それより長い足＝前の年（監査 CP60）。
    ★未来を見ない＝前の期間が閉じてから使う（shift(1) で1つ前の期間の値だけを当てる）。"""
    step = pd.Series(d.index).diff().median()
    if pd.isna(step) or step < pd.Timedelta("1D"):
        key = d.index.floor("D")
    elif step < pd.Timedelta("7D"):
        key = d.index.to_period("M").to_timestamp()
    else:
        key = d.index.to_period("Y").to_timestamp()
    per = d.groupby(key).agg(high=("high", "max"), low=("low", "min"), close=("close", "last")).shift(1)
    m = per.reindex(key)
    m.index = d.index
    pp = (m["high"] + m["low"] + m["close"]) / 3
    return pp, 2 * pp - m["low"], 2 * pp - m["high"]


_reg("close vs 前期間pivotPP%", "close vs 前期間pivotPP%", True, lambda d: (d.close / _pivot_prev_period(d)[0] - 1) * 100)
_reg("close vs 前期間pivotR1%", "close vs 前期間pivotR1%", True, lambda d: (d.close / _pivot_prev_period(d)[1] - 1) * 100)
_reg("close vs 前期間pivotS1%", "close vs 前期間pivotS1%", True, lambda d: (d.close / _pivot_prev_period(d)[2] - 1) * 100)
~~~
根拠の抜き書き: indicator_reference_diag.py:1238「   "★流儀に注意＝教科書の PP は前の期間の高値・安値・終値。本カタログは移動窓の高安＋前バー終値の変形",」
状態: 未決
補足: 案B＝上＝教科書の版を足し、移動窓版は残す。案A＝移動窓版を置き換える（名前の {} が使われなくなるので名前の変更も要る）。どちらにするかは まこさんが決める。監査役が写しで走らせた＝5分足2万本で欠損でない 19,872本・切り詰め再計算の不一致 0/3・PP の乖離の分位 10/50/90% ＝ −2.13/−0.155/1.281。修正 19〜21 を組で当てる

#### 修正 19
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1356-1359
直す前の文字:
~~~
    for n in cfg["pivot_windows"]:
        addf("close vs pivotPP%", n)
        addf("close vs pivotR1%", n)
        addf("close vs pivotS1%", n)
~~~
直した後の文字:
~~~
    for n in cfg["pivot_windows"]:
        addf("close vs pivotPP%", n)
        addf("close vs pivotR1%", n)
        addf("close vs pivotS1%", n)
    # 教科書のピボット（前の期間で固定の線・監査 CP60）
    addf("close vs 前期間pivotPP%")
    addf("close vs 前期間pivotR1%")
    addf("close vs 前期間pivotS1%")
~~~
根拠の抜き書き: observe_diag.py:1454「    addf("close vs HILO%")」（数字を持たない材料の足し方の前例）
状態: 未決
補足: 修正 18 で案B を選んだときだけ当てる

#### 修正 20
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1251-1252（この2行の後ろに足す）
直す前の文字:
~~~
   known=lambda p: [(_flat(p[0] + 20), [(-1, 0.0, 1e-9)]),
                    (_range_case(n=max(300, p[0] + 60)), [(-1, 5.0, 1e-6)])])
~~~
直した後の文字:
~~~
   known=lambda p: [(_flat(p[0] + 20), [(-1, 0.0, 1e-9)]),
                    (_range_case(n=max(300, p[0] + 60)), [(-1, 5.0, 1e-6)])])


def _pivot_day_case():
    """前期間ピボットの手計算用（監査 CP60）。1日目（288本）＝終値105・高値110 が1本・安値100 が1本、2日目＝終値105 が3本。
    PP=(110+100+105)/3=105・R1=2×105−100=110・S1=2×105−110=100。"""
    c = np.full(291, 105.0)
    h = c.copy()
    l = c.copy()
    h[100] = 110.0
    l[200] = 100.0
    return _mk(c, o=c, h=h, l=l)


_r(r"close vs 前期間pivotPP%", "前期間pivotPP",
   "教科書のピボット PP＝前の期間（日中の足は前の UTC の日・日足は前の月・それより長い足は前の年）の（高値＋安値＋終値）÷3 からの乖離%。期間のあいだ線は動かない",
   "StockCharts「Pivot Points」の逐語「the prior day's high, low, and close」「do not change and remain in play throughout the day」。%化は H6",
   "順張り値", "trend", known=lambda p: [(_pivot_day_case(), [(-1, 0.0, 1e-9)])])
_r(r"close vs 前期間pivotR1%", "前期間pivotR1",
   "教科書の R1＝2×PP − 前の期間の安値 からの乖離%", "StockCharts の逐語「Resistance 1 (R1) = (P x 2) - Low」",
   "順張り値", "trend", known=lambda p: [(_pivot_day_case(), [(-1, (105.0 / 110.0 - 1) * 100, 1e-9)])])
_r(r"close vs 前期間pivotS1%", "前期間pivotS1",
   "教科書の S1＝2×PP − 前の期間の高値 からの乖離%", "StockCharts の逐語「Support 1 (S1) = (P x 2) - High」",
   "順張り値", "trend", known=lambda p: [(_pivot_day_case(), [(-1, 5.0, 1e-9)])])
~~~
根拠の抜き書き: indicator_reference_diag.py:1250「_r(r"close vs pivotS1%(\d+)", "pivotS1",」
状態: 未決
補足: 修正 18 と同じ。`_mk` の合成のバーの時刻が UTC の日をまたぐ作りか（288本で1日）は、承認の後の検査3で確かめる＝監査では走らせていない。走らせていない理由＝参照表の部品を import すると検査の全体が動き、作業場の写しで閉じない

#### 修正 21
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 4547
直す前の文字:
~~~
    "pivotPP": dict(k="構造・位置"), "pivotR1": dict(k="構造・位置"), "pivotS1": dict(k="構造・位置"),
~~~
直した後の文字:
~~~
    "pivotPP": dict(k="構造・位置"), "pivotR1": dict(k="構造・位置"), "pivotS1": dict(k="構造・位置"),
    "前期間pivotPP": dict(k="構造・位置"), "前期間pivotR1": dict(k="構造・位置"), "前期間pivotS1": dict(k="構造・位置"),
~~~
根拠の抜き書き: indicator_reference_diag.py:4547「    "pivotPP": dict(k="構造・位置"), "pivotR1": dict(k="構造・位置"), "pivotS1": dict(k="構造・位置"),」
状態: 未決
補足: 修正 18 と同じ。当てた後に indicator_switch.json を gen_indicator_switch.py で作り直す＝手で書かない

#### 修正 22
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 361-377
直す前の文字:
~~~
def _vp_levels(c, v, win=288):
    """出来高プロファイル。窓内で出来高が最も厚い価格＝POC、上下 70% 帯＝VAH/VAL の近似。"""
    poc, vah, val = [], [], []
    ca, va = c.to_numpy(), v.to_numpy()
    for i in range(len(ca)):
        if i < win:
            poc.append(np.nan); vah.append(np.nan); val.append(np.nan); continue
        cw, vw = ca[i - win:i], va[i - win:i]
        bins = np.linspace(cw.min(), cw.max(), 25)
        idx = np.clip(np.digitize(cw, bins) - 1, 0, len(bins) - 2)
        agg = np.bincount(idx, weights=vw, minlength=len(bins) - 1)
        centers = (bins[:-1] + bins[1:]) / 2
        order = np.argsort(agg)[::-1]
        cum = np.cumsum(agg[order]) / max(agg.sum(), 1e-9)
        keep = centers[order[:max(1, int(np.searchsorted(cum, 0.7)) + 1)]]
        poc.append(centers[order[0]]); vah.append(keep.max()); val.append(keep.min())
    return (pd.Series(poc, index=c.index), pd.Series(vah, index=c.index), pd.Series(val, index=c.index))
~~~
直した後の文字:
~~~
def _vp_levels(c, v, win=288):
    """出来高プロファイル。窓内で出来高が最も厚い区画＝POC。VAH/VAL＝POC から始めて、上と下の隣の区画のうち
    出来高の多い方を1つずつ足し、窓の出来高の70%に届いた所の上端・下端（監査 CP60）。
    出どころ＝CQG の逐語「The value area begins calculating at the POC. The system expands the value area one price
    at a time in either direction until the value area represents 70% ...」。同量なら POC に近い側・距離も同じなら上
    （TradingView の逐語「choose the row closer to the POC」）。区画は24（端が25個）。"""
    poc, vah, val = [], [], []
    ca, va = c.to_numpy(), v.to_numpy()
    for i in range(len(ca)):
        if i < win:
            poc.append(np.nan); vah.append(np.nan); val.append(np.nan); continue
        cw, vw = ca[i - win:i], va[i - win:i]
        bins = np.linspace(cw.min(), cw.max(), 25)
        idx = np.clip(np.digitize(cw, bins) - 1, 0, len(bins) - 2)
        agg = np.bincount(idx, weights=vw, minlength=len(bins) - 1)
        centers = (bins[:-1] + bins[1:]) / 2
        p = int(np.argsort(agg)[::-1][0])
        last = len(agg) - 1
        tot = max(agg.sum(), 1e-9)
        lo, hi, acc = p, p, agg[p]
        while acc / tot < 0.7 and (lo > 0 or hi < last):
            up = agg[hi + 1] if hi < last else -1.0
            dn = agg[lo - 1] if lo > 0 else -1.0
            if up > dn or (up == dn and (hi + 1 - p) <= (p - lo + 1)):
                hi += 1
                acc += agg[hi]
            else:
                lo -= 1
                acc += agg[lo]
        poc.append(centers[p]); vah.append(centers[hi]); val.append(centers[lo])
    return (pd.Series(poc, index=c.index), pd.Series(vah, index=c.index), pd.Series(val, index=c.index))
~~~
根拠の抜き書き: observe_diag.py:375「        keep = centers[order[:max(1, int(np.searchsorted(cum, 0.7)) + 1)]]」
状態: 確定
補足: 監査役が写しで走らせた＝5分足2万本で POC は直す前と100.00%同じ・VAL≤POC≤VAH が100.00%・切り詰め再計算の不一致 0/3・VAH は直す前と25.06%・VAL は23.32%の足でしか一致しない。修正 23 と同時に当てる。期間（移動窓）は修正 42 で別に決める

#### 修正 23
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 646-651
直す前の文字:
~~~
        order = np.argsort(agg)[::-1]        # 同量の帯は価格の高い側を採る（カタログの決めに合わせる）
        cum = np.cumsum(agg[order]) / max(agg.sum(), 1e-9)
        keep = centers[order[:max(1, int(np.searchsorted(cum, 0.7)) + 1)]]
        poc[i] = centers[order[0]]
        vah[i] = keep.max()
        val[i] = keep.min()
~~~
直した後の文字:
~~~
        p = int(np.argsort(agg)[::-1][0])     # 同量の帯は価格の高い側を採る（カタログの決めに合わせる）
        tot = max(agg.sum(), 1e-9)
        lo, hi, acc = p, p, agg[p]
        # POC から隣の区画のうち多い方を1つずつ足す（CQG・TradingView の作り・監査 CP60）
        while acc / tot < 0.7 and (lo > 0 or hi < 23):
            up = agg[hi + 1] if hi < 23 else -1.0
            dn = agg[lo - 1] if lo > 0 else -1.0
            if up > dn or (up == dn and (hi + 1 - p) <= (p - lo + 1)):
                hi += 1
                acc += agg[hi]
            else:
                lo -= 1
                acc += agg[lo]
        poc[i] = centers[p]
        vah[i] = centers[hi]
        val[i] = centers[lo]
~~~
根拠の抜き書き: indicator_reference_diag.py:648「        keep = centers[order[:max(1, int(np.searchsorted(cum, 0.7)) + 1)]]」
状態: 確定
補足: 修正 22 と同時に当てる。片方だけ当てると検査3が不一致で止まる

#### 修正 24
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1147-1148
直す前の文字:
~~~
_reg("close vs SAREXT%", "close vs SAREXT%", True,
     lambda d: (d.close / _pta6.sarext(high=d.high, low=d.low, close=d.close) - 1) * 100)
~~~
直した後の文字:
~~~
# ★ライブラリは売り側の SAR を負の数で返す（pandas_ta_classic 0.6.52 trend/sarext.py:137・TA-Lib の逐語
#   「TA_SAREXT returns negative values when the position is short」）＝絶対値に直してから割る（監査 CP60）。
_reg("close vs SAREXT%", "close vs SAREXT%", True,
     lambda d: (d.close / _pta6.sarext(high=d.high, low=d.low).abs() - 1) * 100)
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/trend/sarext.py:137「        np.where(~np.isnan(short_arr), -short_arr, np.nan),」
状態: 未決
補足: 案が2つ在り、どちらにするかは まこさんが決める（未決）。案A＝上＝符号と向きが直る。監査役が写しで走らせた＝分位 10/50/90% ＝ −0.335/−0.002/0.313・最小 −4.24%（直す前は売り側で約 −192%）・切り詰め再計算の不一致 0/3・PSAR との相関 0.7570＝ライブラリの反転時の作りの違い（TA-Lib の `sar = ep` が無い）は残る。案B＝この列を外す（既定の数字が PSAR と同じで、close vs PSAR% が既に在る）。外すなら gen_indicator_switch.py の源の側で外す

#### 修正 25
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1000-1001
直す前の文字:
~~~
_reg("STC", "STC", True, lambda d: _pta6.stc(close=d.close).iloc[:, 0])
_reg("STCstoch", "STCstoch", True, lambda d: _pta6.stc(close=d.close).iloc[:, 2])
~~~
直した後の文字:
~~~
def _stc_textbook(close, tcl=10, f_=12, s_=26, fac=0.5):
    """Schaff Trend Cycle（教科書＝TA-Lib stc の式・Schaff 2008）。戻り＝(STC, 1段目をならした値)。
    ★範囲（窓の最大−最小）が 0 か欠損のときだけ、前の値を持ち越す（TA-Lib の逐語
      「When a range is zero, the fraction keeps its previous value (0 before any).」）。
    ★pandas_ta_classic の stc は1段目を「MACD の窓の最小値 > 0」のときだけ計算する（momentum/stc.py:180）＝
      MACD が窓の中で1回でも 0 以下なら値が凍る（監査 CP60 の実測＝直近10万本の63.87%で凍る・STC の中央値 0.0）。
      だからライブラリの stc を呼ばない。期間 12/26 は直す前と同じ（23/50 にするかは修正 49 で比べる）。"""
    xm = (_pta6.ema(close, length=f_) - _pta6.ema(close, length=s_)).to_numpy(float)
    m = len(xm)

    def stage(x):
        s = pd.Series(x)
        lo = s.rolling(tcl).min().to_numpy(float)
        rng = s.rolling(tcl).max().to_numpy(float) - lo
        st = np.zeros(m)
        sm = np.zeros(m)
        for i in range(1, m):
            st[i] = 100.0 * (x[i] - lo[i]) / rng[i] if rng[i] > 0 else st[i - 1]
            sm[i] = sm[i - 1] + fac * (st[i] - sm[i - 1])
        return sm

    pf = stage(xm)
    return pd.Series(stage(pf), index=close.index), pd.Series(pf, index=close.index)


_reg("STC", "STC", True, lambda d: _stc_textbook(d.close)[0])
_reg("STCstoch", "STCstoch", True, lambda d: _stc_textbook(d.close)[1])
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/momentum/stc.py:180「        if lowest_xmacd.iloc[i] > 0:」
状態: 確定
補足: 監査役が写しで走らせた＝5分足2万本で中央値 49.999・分位 10/90% ＝ 0.168/99.864・直す前との相関 0.1569・切り詰め再計算の不一致 0/3。修正 26 と同時に当てる

#### 修正 26
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2345-2365
直す前の文字:
~~~
def _stc_parts(d, tcl=10, f_=12, s_=26, fac=0.5):
    """Schaff のトレンド周期。★実物の流儀＝1段目は「MACD の最小値が 0 より大きいとき」だけ計算し、
    そうでなければ前の値を持ち越す。ならしは pf ← pf ＋ 係数×(stoch − pf) で、8桁に丸める。"""
    c = d.close.to_numpy(float)
    xm = _ema_seed(c, f_) - _ema_seed(c, s_)
    m = len(xm)

    def stage(x, use_range):
        lo, hi = _roll(x, tcl, "min"), _roll(x, tcl, "max")
        rng = hi - lo
        rng = np.where(rng == 0, np.finfo(float).eps, rng)
        st = np.zeros(m)
        sm = np.zeros(m)
        for i in range(1, m):
            gate = rng[i] > 0 if use_range else (not np.isnan(lo[i]) and lo[i] > 0)
            st[i] = 100.0 * (x[i] - lo[i]) / rng[i] if gate else st[i - 1]
            sm[i] = round(sm[i - 1] + fac * (st[i] - sm[i - 1]), 8)
        return sm

    pf = stage(xm, False)
    return stage(pf, True), pf
~~~
直した後の文字:
~~~
def _stc_parts(d, tcl=10, f_=12, s_=26, fac=0.5):
    """Schaff のトレンド周期（教科書＝TA-Lib stc の式）。★2段とも「範囲（最大−最小）が 0 か欠損のときだけ
    前の値を持ち越す」。ならしは pf ← pf ＋ 係数×(stoch − pf)。
    ★監査 CP60＝直す前は pandas_ta_classic の誤り（1段目を「MACD の最小値が 0 より大きいとき」だけ計算する）を
    そのまま写していた＝照合が通っても教科書と同じとは言えなかった。"""
    c = d.close.to_numpy(float)
    xm = _ema_seed(c, f_) - _ema_seed(c, s_)
    m = len(xm)

    def stage(x):
        lo, hi = _roll(x, tcl, "min"), _roll(x, tcl, "max")
        rng = hi - lo
        st = np.zeros(m)
        sm = np.zeros(m)
        for i in range(1, m):
            st[i] = 100.0 * (x[i] - lo[i]) / rng[i] if rng[i] > 0 else st[i - 1]
            sm[i] = sm[i - 1] + fac * (st[i] - sm[i - 1])
        return sm

    pf = stage(xm)
    return stage(pf), pf
~~~
根拠の抜き書き: indicator_reference_diag.py:2359「            gate = rng[i] > 0 if use_range else (not np.isnan(lo[i]) and lo[i] > 0)」
状態: 確定
補足: 修正 25 と同時に当てる。EMA の種の作り（_ema_seed とライブラリの ema）の違いで検査3の許容幅に入るかは、承認の後の検査3で確かめる

#### 修正 27
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2602-2604
直す前の文字:
~~~
_r(r"PPOヒスト\((\d+),(\d+),(\d+)\)", "PPOヒスト",
   "PPO とシグナルの差", "同上。★これは『勢いが加速しているか』を測るもので、上げ下げの向きを表さない",
   "状態量＝加速（向きを持たない）", "none", tb=_tb_ppo_h)
~~~
直した後の文字:
~~~
_r(r"PPOヒスト\((\d+),(\d+),(\d+)\)", "PPOヒスト",
   "PPO とシグナルの差", "同上。StockCharts の逐語「The histogram is positive when PPO is above its 9-day EMA and "
   "negative when PPO is below its 9-day EMA.」。加速の柱の実測（MACDヒスト% の流儀の欄に記録）＝"
   "加速上げ +0.0001571／加速下げ −0.007139 で符号が分かれる＝順張り値の側（監査 CP60 で直した）",
   "順張り値＝プラスで勢いが加速", "trend", tb=_tb_ppo_h)
~~~
根拠の抜き書き: indicator_reference_diag.py:997「   "実測で決める（PPOヒスト 加速上げ +0.0001571／加速下げ −0.007139・RVGIヒスト +0.002105／−0.003796 は"」
状態: 確定
補足: 当てると型の表 signal_families.json の指紋が変わるので、まこさんの承認がもう一度 要る。on/off は変わらない

#### 修正 28
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1040
直す前の文字:
~~~
    ("ALMA", lambda d, n: _pta6.alma(close=d.close, length=n)),
~~~
直した後の文字:
~~~
    # ★ALMA（監査 CP60）＝ライブラリは重みを w_norm[::-1] で逆向きに当てる（overlap/alma.py:37）。
    #   ずらし 0.85 を渡すと山が古い側に来る＝Legoux の定義と逆。0.15 を渡すと、教科書の offset 0.85
    #   （山が新しい側）と同じ重みになる（ガウスの重みは左右対称なので、0.15 の逆向き＝0.85 の正向き）。
    ("ALMA", lambda d, n: _pta6.alma(close=d.close, length=n, distribution_offset=0.15)),
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/overlap/alma.py:37「    alma = _sliding_weighted_ma(close, length, w_norm[::-1])」
状態: 確定
補足: 監査役が実物で走らせた＝遅れ 9本で 6.44→1.56・20本で 15.20→3.80・切り詰め再計算の不一致 0/3。ALMA傾き%（off）も同じ関数なので一緒に変わる。修正 29 と同時に当てる

#### 修正 29
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1842-1847
直す前の文字:
~~~
def _alma(c: np.ndarray, n: int, sigma: float = 6.0, off: float = 0.85) -> np.ndarray:
    m = off * (n - 1)
    s = n / sigma
    i = np.arange(n, dtype=float)
    # ★重みは逆順にしてから当てる（ライブラリの実物の逐語＝w_norm[::-1]）
    return _wma_w(c, np.exp(-((i - m) ** 2) / (2 * s * s))[::-1])
~~~
直した後の文字:
~~~
def _alma(c: np.ndarray, n: int, sigma: float = 6.0, off: float = 0.85) -> np.ndarray:
    m = off * (n - 1)
    s = n / sigma
    i = np.arange(n, dtype=float)
    # ★重み i は窓の古い側から数える（Legoux／TradingView＝山が新しい側）。
    #   監査 CP60 で、ライブラリの逆順（w_norm[::-1]）の写しをやめた。
    return _wma_w(c, np.exp(-((i - m) ** 2) / (2 * s * s)))
~~~
根拠の抜き書き: indicator_reference_diag.py:1846「    # ★重みは逆順にしてから当てる（ライブラリの実物の逐語＝w_norm[::-1]）」
状態: 確定
補足: `_wma_w` が重みを窓の古い側から当てる作りかは、承認の後の検査3で確かめる＝監査では走らせていない

#### 修正 30
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1080-1081
直す前の文字:
~~~
_reg("close vs HILO%", "close vs HILO%", True, lambda d: (d.close / _pta6.hilo(high=d.high, low=d.low,
                                                                              close=d.close).iloc[:, 0] - 1) * 100)
~~~
直した後の文字:
~~~
# ★HILO（監査 CP60）＝高値の平均の本数・安値の平均の本数を名前に出す。
#   Krausz の教科書は3本（LuxAlgo）。ライブラリの既定 13・21 に固定すると engine_tuner が届かない。
_reg("close vs HILO%", "close vs HILO%({},{})", True, lambda d, h_, l_: (d.close / _pta6.hilo(
     high=d.high, low=d.low, close=d.close, high_length=h_, low_length=l_).iloc[:, 0] - 1) * 100)
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/overlap/hilo.py:23「    high_length = int(high_length) if high_length and high_length > 0 else 13」
状態: 未決
補足: 案が2つ在り、どちらにするかは まこさんが決める（未決）。案A＝上＝2つの数字。材料の一覧 observe_diag.py:1454 の `addf("close vs HILO%")` を `for (h_, l_) in cfg["hilo_lengths"]: addf("close vs HILO%", h_, l_)` に、observe_config.json に `"hilo_lengths": [[13, 21], [3, 3]]`（13/21 は今の値・3/3 は教科書）を足すのと組。案B＝教科書どおり1つの n を両方に渡す。修正 31・32 を組で当てる

#### 修正 31
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2727-2730
直す前の文字:
~~~
_r(r"close vs HILO%", "close vs HILO%",
   "終値が Gann の高安切替線から何%離れているか",
   "Gann HiLo Activator。高値13本平均・安値21本平均を、終値の上抜け／下抜けで切り替える（ライブラリの既定）",
   "反転サイン", "none", tb=_tb_pos_hilo)
~~~
直した後の文字:
~~~
_r(r"close vs HILO%\((\d+),(\d+)\)", "close vs HILO%",
   "終値が Gann の高安切替線から何%離れているか",
   "Gann HiLo Activator。高値 h 本平均・安値 l 本平均を、終値の上抜け／下抜けで切り替える。教科書（Krausz・LuxAlgo）は3本。"
   "本数は名前の2つの数字（監査 CP60）",
   "反転サイン", "none", tb=_tb_pos_hilo)
~~~
根拠の抜き書き: indicator_reference_diag.py:2729「   "Gann HiLo Activator。高値13本平均・安値21本平均を、終値の上抜け／下抜けで切り替える（ライブラリの既定）",」
状態: 未決
補足: 修正 30 と同じ

#### 修正 32
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2252-2253
直す前の文字:
~~~
    hm = _roll(d.high.to_numpy(float), 13, "mean")
    lm = _roll(d.low.to_numpy(float), 21, "mean")
~~~
直した後の文字:
~~~
    hm = _roll(d.high.to_numpy(float), int(p[0]), "mean")
    lm = _roll(d.low.to_numpy(float), int(p[1]), "mean")
~~~
根拠の抜き書き: indicator_reference_diag.py:2252「    hm = _roll(d.high.to_numpy(float), 13, "mean")」
状態: 未決
補足: 修正 30 と同じ

#### 修正 33
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1084
直す前の文字:
~~~
_reg("close vs HWMA%", "close vs HWMA%", True, lambda d: (d.close / _pta6.hwma(close=d.close) - 1) * 100)
~~~
直した後の文字:
~~~
# ★HWMA（監査 CP60）＝3つの係数（0〜1 の開区間）を名前に出す。出どころ（mql5 code 20856）は利用者の入力で既定の値を持たない。
#   ★ライブラリは 0 以下・1 以上を黙って既定（0.2・0.1・0.1）に戻す（overlap/hwma.py:36-38）。探す範囲は 0 と 1 を含めない。
_reg("close vs HWMA%", "close vs HWMA%({},{},{})", True, lambda d, a_, b_, c_: (d.close / _pta6.hwma(
     close=d.close, na=a_, nb=b_, nc=c_) - 1) * 100)
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/overlap/hwma.py:36「    na = float(na) if na and na > 0 and na < 1 else 0.2」
状態: 未決
補足: 材料の一覧 observe_diag.py:1456 の `addf("close vs HWMA%")` を `for (a_, b_, c_) in cfg["hwma_coefs"]: addf("close vs HWMA%", a_, b_, c_)` に、observe_config.json に `"hwma_coefs": [[0.2, 0.1, 0.1]]` を足すのと組。広げる範囲は まこさんが material_param_ranges に書く。修正 34 を組で当てる

#### 修正 34
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2741-2744
直す前の文字:
~~~
_r(r"close vs HWMA%", "close vs HWMA%",
   "終値が Holt-Winters の移動平均から何%離れているか",
   "Holt-Winters（3つの係数の指数平滑）。★既知答えで検証する＝値段が一定なら ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])])
~~~
直した後の文字:
~~~
_r(r"close vs HWMA%\(([\d.]+),([\d.]+),([\d.]+)\)", "close vs HWMA%",
   "終値が Holt-Winters の移動平均から何%離れているか",
   "Holt-Winters（3つの係数 na・nb・nc の指数平滑・名前の3つの数字・監査 CP60）。★既知答えで検証する＝値段が一定なら ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])])
~~~
根拠の抜き書き: indicator_reference_diag.py:2743「   "Holt-Winters（3つの係数の指数平滑）。★既知答えで検証する＝値段が一定なら ぴったり 0",」
状態: 未決
補足: 修正 33 と同じ

#### 修正 35
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1038
直す前の文字:
~~~
#   本数を持たない指標（HILO・HT_TRENDLINE・HWMA）はライブラリの既定をそのまま使う。
~~~
直した後の文字:
~~~
#   数字を持たない指標（HT_TRENDLINE）はそのまま使う。HILO・HWMA は数字を持つので名前に出す（監査 CP60）。
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/overlap/hilo.py:15「    high_length: Optional[int] = None,」
状態: 確定
補足: 修正 30・33 の理由の行。HILO・HWMA を固定した理由がこの事実と違う説明だけだった

### Major

#### 修正 36
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2943-2946
直す前の文字:
~~~
_r(r"close vs SAREXT%", "close vs SAREXT%",
   "終値が 拡張パラボリック SAR から何%離れているか",
   "TA-Lib（SAREXT）。★定義から導ける既知答えで検証する＝値段が一定なら逆指値も その値に張り付くので"
   "この列は ぴったり 0", "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
~~~
直した後の文字:
~~~
_r(r"close vs SAREXT%", "close vs SAREXT%",
   "終値が 拡張パラボリック SAR から何%離れているか",
   "TA-Lib（SAREXT）。★ライブラリは売り側の SAR を負の数で返す（TA-Lib の逐語＝returns negative values"
   " when the position is short）ので、絶対値に直してから割る（監査 CP60）。★既知答え＝値段が一定なら ぴったり 0。"
   "売り側の既知答えは値段一定では試せないので、下げ続ける合成のバーの答えを承認の後に手で出して足す",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
~~~
根拠の抜き書き: observe_diag.py:1148「     lambda d: (d.close / _pta6.sarext(high=d.high, low=d.low, close=d.close) - 1) * 100)」
状態: 確定
補足: 修正 24 で案A を選んだとき。E が出した下げの既知答え −500/56 は手で導いた値で、監査役の実測（下げ 150本で −191.89%＝直す前）とは別の合成のバーなので、ここには入れない

#### 修正 37
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2916-2921
直す前の文字:
~~~
_r(r"DPO%(\d+)", "DPO%",
   "デトレンド振動子。終値から「n本平均を (n/2+1) 本ずらしたもの」を引き、終値で割って%化",
   "標準（Detrended Price Oscillator）。★ライブラリの既定 centered=True は未来を見る"
   "（値を未来の足の方へずらす書き方を使う・2026-08-09 実測）ので、必ず centered=False で呼ぶ。"
   "%化は H6 のための本プロジェクトの流儀",
   "反転サイン", "none", tb=_tb_dpo)
~~~
直した後の文字:
~~~
_r(r"DPO%(\d+)", "DPO%",
   "デトレンド振動子。終値から「n本平均を (n/2+1) 本ずらしたもの」を引き、終値で割って%化",
   "★教科書の形ではない＝TradingView の中心化しない版（いまの終値 − k本前の n本平均・k=n/2+1）。"
   "教科書（StockCharts の逐語＝Price - X-period SMA from {X/2 + 1} periods in the future）を時点 t で"
   "計算できる形に書くと『k本前の終値 − いまの n本平均』で、ta の DPOIndicator もこの形＝値が違う。"
   "★ライブラリの既定 centered=True は未来を見るので、必ず centered=False で呼ぶ。%化は H6 のための流儀",
   "反転サイン", "none", tb=_tb_dpo)
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/trend/dpo.py:32「    dpo = close - ma.shift(t)」
状態: 確定
補足: TA_CLASS_MAP の「DPOIndicator → DPO%」は値の違うものを対応づけている。対応を外すかは まこさんが決める

#### 修正 38
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3199-3205
直す前の文字:
~~~
_r(r"NVI傾き(\d+)", "NVI傾き",
   "出来高が減った足の変化率だけを積み上げた指数（NVI）の n 本の増分",
   "Paul Dysart / Norman Fosback。積み上げの値そのものは意味を持たない（起点が 1000 の定数）ので"
   "増分を見る。変化率%の足し算なので、そのままで無次元",
   "順張り値＝プラスで、商いの薄い足で上げている", "trend", tb=_tb_nvi_slope,
   known=lambda p: [(_bar_vslope(p[0] + 40, True), [(-1, 0.0, 1e-9)]),
                    (_bar_vslope(p[0] + 40, False), [(-1, "+", 0.0)])])
~~~
直した後の文字:
~~~
_r(r"NVI傾き(\d+)", "NVI傾き",
   "出来高が減った足の変化率だけを積み上げた指数（NVI）の n 本の増分",
   "StockCharts の足し算の流儀（逐語＝Add the Percentage Price Change to Cumulative NVI when Volume"
   " Decreases）。★Fosback の原著と ta の NegativeVolumeIndexIndicator は掛け算（前の NVI ×(1+変化率)）で値が違う。"
   "足し算にすると n 本の増分が起点や積み上げた水準に左右されない（掛け算の増分は水準に比例して大きさが変わる）。"
   "変化率%の足し算なので、そのままで無次元",
   "順張り値＝プラスで、商いの薄い足で上げている", "trend", tb=_tb_nvi_slope,
   known=lambda p: [(_bar_vslope(p[0] + 40, True), [(-1, 0.0, 1e-9)]),
                    (_bar_vslope(p[0] + 40, False), [(-1, "+", 0.0)])])
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/volume/nvi.py:37「    nvi = signed_volume[signed_volume < 0].abs() * roc_」
状態: 確定

#### 修正 39
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 768-775
直す前の文字:
~~~
_reg("MACD線%", "MACD線%({},{})", True, lambda d, f_, s_:
     (d.close.ewm(span=f_).mean() - d.close.ewm(span=s_).mean()) / d.close * 100)
_reg("MACDシグナル線%", "MACDシグナル線%({},{},{})", True, lambda d, f_, s_, g_:
     (d.close.ewm(span=f_).mean() - d.close.ewm(span=s_).mean())
     .ewm(span=g_).mean() / d.close * 100)
_reg("MACDヒスト%", "MACDヒスト%({},{},{})", True, lambda d, f_, s_, g_:
     (lambda m: (m - m.ewm(span=g_).mean()) / d.close * 100)(
         d.close.ewm(span=f_).mean() - d.close.ewm(span=s_).mean()))
~~~
直した後の文字:
~~~
_reg("MACD線%", "MACD線%({},{})", True, lambda d, f_, s_:
     (d.close.ewm(span=f_, adjust=False).mean() - d.close.ewm(span=s_, adjust=False).mean()) / d.close * 100)
_reg("MACDシグナル線%", "MACDシグナル線%({},{},{})", True, lambda d, f_, s_, g_:
     (d.close.ewm(span=f_, adjust=False).mean() - d.close.ewm(span=s_, adjust=False).mean())
     .ewm(span=g_, adjust=False).mean() / d.close * 100)
_reg("MACDヒスト%", "MACDヒスト%({},{},{})", True, lambda d, f_, s_, g_:
     (lambda m: (m - m.ewm(span=g_, adjust=False).mean()) / d.close * 100)(
         d.close.ewm(span=f_, adjust=False).mean() - d.close.ewm(span=s_, adjust=False).mean()))
~~~
根拠の抜き書き: indicator_reference_diag.py:985「   "短期 EMA − 長期 EMA を終値で割って%化", "Appel。EMA は標準の漸化式・%化は価格非依存 H6 のための本プロジェクトの流儀",」
状態: 確定
補足: 差は (1−2/27)^本数 で減り、助走17,280本の後は数値として0。データの先頭の数百本と番人の指紋だけが変わる。同じファイルの 797・873 行の EMA は既に adjust=False

#### 修正 40
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1258
直す前の文字:
~~~
   "Market Profile。窓 n 本・25分割の近似。同量の帯が並んだら価格の高い側を採る（実装の決め）",
~~~
直した後の文字:
~~~
   "Market Profile。窓 n 本・24区画（端が25個）。同量の帯が並んだら価格の高い側を採る（実装の決め）",
~~~
根拠の抜き書き: observe_diag.py:369「        bins = np.linspace(cw.min(), cw.max(), 25)」（参照表自身の177行「★実装は窓の最安値〜最高値を24等分する。」とも食い違う）
状態: 確定
補足: 1265・1272 行の「Market Profile。25分割の近似」も「Market Profile。24区画（端が25個）・POC から隣を足す作り（監査 CP60）」に直す＝修正 22 を当てた後の説明

#### 修正 41（close vs VWAP の比べ方）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1212
直す前の文字:
~~~
   "★流儀に注意＝世界標準の VWAP はセッション起点＋典型価格。本カタログは n 本の移動窓＋終値で、24時間市場向けの本プロジェクトの流儀。外部照合は定義が違うため対象外",
~~~
直した後の文字:
~~~
   "★流儀に注意＝教科書（StockCharts）の VWAP はセッション起点の累積＋典型価格。ta の VolumeWeightedAveragePrice は n 本の移動窓＋典型価格。本カタログは n 本の移動窓＋終値＝ta とは値段（終値か典型価格か）だけが違う。外部照合はこの違いのため対象外（indicator_switch では ta 由来として on・TA_CLASS_MAP）",
~~~
根拠の抜き書き: indicator_reference_diag.py:1212（直す前の文字と同じ行）
状態: 未決
補足: 説明の直しは確定。作りは比べて決める＝同じ値決め窓・同じ engine_tuner のレシピで材料の列だけ差し替えて、(a) 今の作り（終値・288本の移動窓）(b) 典型価格・288本の移動窓（ta の作り）(c) UTC 0時に始まる典型価格の累積、の3本について ①順位の相関 ②UTC の時刻ごとの標準偏差の最大÷最小 ③月次 net を並べる。(b) と (a) の相関が 0.999 以上なら値段の違いは無視してよい。(c) の net が上回れば (c) を足す

#### 修正 42（POC の期間の比べ方）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 895-896
直す前の文字:
~~~
_reg("close vs POC%", "close vs POC%{}", True, lambda d, n:
     (d.close / _vp_levels(d.close, d.volume, n)[0] - 1) * 100)
~~~
直した後の文字:
~~~
（比べた後で決める。比べる3本＝288本の移動窓（今）／前の UTC の日で固定（教科書の「前のセッションの値を後のセッションの参照にする」）／その日の0時から育つ版）
~~~
根拠の抜き書き: observe_diag.py:368「        cw, vw = ca[i - win:i], va[i - win:i]」
状態: 未決
補足: 並べる数字＝3本それぞれの月次 net と、線に触れた後 K本以内にはね返された割合。VAH・VAL の期間も同じ比べ方で決める

#### 修正 43（W字の比べ方）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 525
直す前の文字:
~~~
    neck = h.shift(q).rolling(half).max()
~~~
直した後の文字:
~~~
（比べた後で決める。教科書の作り＝2つの底＝窓の中の確定した谷（_fractal_levels）・ネック＝2つの谷の間の最高値・完成＝ネックを最初に上抜けた足）
~~~
根拠の抜き書き: observe_diag.py:525「    neck = h.shift(q).rolling(half).max()」
状態: 未決
補足: 並べる数字＝立った件数・立った後 K本の騰落の中央値・月次 net。許容幅 w_tol が [0.003] の1つだけ（observe_config.json:270-272）なのも同時に比べる

#### 修正 44（S-Rタッチの比べ方）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 397
直す前の文字:
~~~
        out[i] = int(((ha[i - win:i] >= lvl - band) & (la[i - win:i] <= lvl + band)).sum())
~~~
直した後の文字:
~~~
（比べた後で決める。教科書の数え方＝窓の中の確定した山・谷のうち、今の値段の帯に入る数）
~~~
根拠の抜き書き: observe_diag.py:397（直す前の文字と同じ行）
状態: 未決
補足: 並べる数字＝2つの数え方の相関と月次 net。参照表 1323 行の「強度の近似」は「今の値段の帯に掛かった足の本数（滞在時間）」に直す＝説明は確定

#### 修正 45（ライブラリ独自の作り4件の比べ方＝DPO・PMAX・Aberration・THERMO）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1133-1134・1141-1142・1191-1193・1204 の後ろに、教科書の版を並べる列を足す
直す前の文字:
~~~
_reg("THERMO%", "THERMO%", False, lambda d: _th(d).iloc[:, 0] / d.close * 100)
~~~
直した後の文字:
~~~
_reg("THERMO%", "THERMO%", False, lambda d: _th(d).iloc[:, 0] / d.close * 100)
_reg("THERMO教科書%", "THERMO教科書%", False,
     lambda d: np.maximum((d.high - d.high.shift(1)).clip(lower=0),
                          (d.low.shift(1) - d.low).clip(lower=0)) / d.close * 100)
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/volatility/thermo.py:41「    thermoL = (low.shift(drift) - low).abs()」
状態: 未決
補足: 同じ形で、DPO 教科書版＝`(d.close.shift(int(0.5 * n) + 1) - _pta6.sma(d.close, length=n)) / d.close * 100`・PMAX 原作版（移動平均で向きを決める）・Aberration 原作版（BB%b(80,2.0) と同じ）を並べる。並べる数字＝material_ranking の強さ・向き・大きさ（12本・120本）と、engine_tuner を同じ予算・同じ期間で走らせたときの月次 net の最良値。PMAX は向きが切り替わった回数（1日あたり）も並べる

#### 修正 46（SMC_SWEEP の比べ方）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 986
直す前の文字:
~~~
_reg("SMC_SWEEP", "SMC_SWEEP", False, lambda d: _pta6.smc_sweep(open_=d.open, high=d.high, low=d.low, close=d.close))
~~~
直した後の文字:
~~~
（比べた後で決める。教科書の作り＝確定した山谷（_fractal_levels の k）をヒゲで割って、終値で戻した足）
~~~
根拠の抜き書き: observe_diag.py:986（直す前の文字と同じ行）
状態: 未決
補足: 並べる数字＝発火の回数（今は1本あたり 0.0130回）と、発火の後の net。15/1.5 を名前に出して engine_tuner が動かせるようにするかも まこさんが決める。値が ±1 の向き付きなのに directional=False なのは修正 67

#### 修正 47（SQZ_ON の比べ方）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 991
直す前の文字:
~~~
_reg("SQZ_ON", "SQZ_ON", False, lambda d: _pta6.squeeze(high=d.high, low=d.low, close=d.close).iloc[:, 1])
~~~
直した後の文字:
~~~
（比べた後で決める。Carter の作り＝Keltner の中心を代表値段の SMA・幅を ATR）
~~~
根拠の抜き書き: observe_diag.py:991（直す前の文字と同じ行）
状態: 未決
補足: 並べる数字＝オンの割合（今 20.96%・Carter の作り 23.39%）・オンからオフへ変わった後の値動きと net

#### 修正 48（StochRSI の比べ方）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1005-1008
直す前の文字:
~~~
_reg("StochRSI%K", "StochRSI%K{}", True, lambda d, n:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n).iloc[:, 0])
_reg("StochRSI%D", "StochRSI%D{}", True, lambda d, n:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n).iloc[:, 1])
~~~
直した後の文字:
~~~
（未決＝比べた後で決める。原式＝ならさない値（0〜100）を並べる列として足す）
~~~
根拠の抜き書き: observe_diag.py:1006「     _pta6.stochrsi(close=d.close, length=n, rsi_length=n).iloc[:, 0])」
状態: 未決
補足: 並べる数字＝ならさない値と SMA3 の値の相関（C の実測 0.8795）・分位の条件の net

#### 修正 49（TRIXシグナル・TRIXヒスト・TSIヒスト・STC の期間の比べ方）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2681-2683
直す前の文字:
~~~
_r(r"TRIXヒスト\((\d+),(\d+)\)", "TRIXヒスト",
   "TRIX とシグナルの差", "同上。★これは『勢いが加速しているか』を測るもので、上げ下げの向きを表さない",
   "状態量＝加速（向きを持たない）", "none", tb=_tb_trix_h)
~~~
直した後の文字:
~~~
（比べた後で決める。observe_diag の材料検査の加速の柱（合成の「加速した上げ／加速した下げ」の中央値）と実データの柱（上げた日／下げた日の中央値と四分位幅）を、TRIXヒスト・TSIヒスト・MACDヒスト% で並べる。符号が分かれれば修正 27 と同じ形（"順張り値＝プラスで勢いが加速", "trend"）にして、observe_diag.py:1013・1022 の directional を True にする）
~~~
根拠の抜き書き: indicator_reference_diag.py:997「   "実測で決める（PPOヒスト 加速上げ +0.0001571／加速下げ −0.007139・RVGIヒスト +0.002105／−0.003796 は"」
状態: 未決
補足: TRIXシグナル＝SMA9 と EMA9 でヒストの符号が違う 5.58% の足の net を並べる。STC の期間＝修正 25 を当てた後に STC(10,12,26) と STC(10,23,50) の net を並べる

#### 修正 50（realized_vol の比べ方）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 805-806
直す前の文字:
~~~
_reg("realized_vol", "realized_vol{}", False, lambda d, n:
     np.log(d.close / d.close.shift()).rolling(n).std() * 100)
~~~
直した後の文字:
~~~
_reg("realized_vol", "realized_vol{}", False, lambda d, n:
     np.log(d.close / d.close.shift()).rolling(n).std() * 100)
_reg("realized_vol_rv", "realized_vol_rv{}", False, lambda d, n:
     np.sqrt((np.log(d.close / d.close.shift()) ** 2).rolling(n).sum() / n) * 100)
~~~
根拠の抜き書き: indicator_reference_diag.py:1073「   "対数リターンの n 本標準偏差×100", "標準（標本標準偏差 ddof=1）", "ボラ量", "vol", tb=_tb_rvol,」
状態: 未決
補足: 並べる数字＝①同じ組み立てに入れ替えて入れたときの月ごとの net（n=20・50）②平均を引くと二乗の和の20%超が消える足（n=20 で2.0%）だけの、K本先までの |値動き%| の中央値を2つの列の分位ごとに ③順位の相関（0.99999 以上なら同じ列なので省く）

#### 修正 51（SSF の比べ方）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1053
直す前の文字:
~~~
    ("SSF", lambda d, n: _pta6.ssf(close=d.close, length=n)),
~~~
直した後の文字:
~~~
（未決＝比べた後で決める。Ehlers の式＝入力 c1×(c+c[1])/2）
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/overlap/ssf.py（D の読み＝15行の `c1 * c_arr[i]`）
状態: 未決
補足: 並べる数字＝①順位の相関 ②平均の遅れ（本数）③同じ案での月ごとの net

#### 修正 52（TRIMA・VIDYA の比べ方）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1060-1062
直す前の文字:
~~~
    ("TRIMA", lambda d, n: _pta6.trima(close=d.close, length=n)),
    ("TSF", lambda d, n: _pta6.tsf(close=d.close, length=n)),
    ("VIDYA", lambda d, n: _pta6.vidya(close=d.close, length=n)),
~~~
直した後の文字:
~~~
（未決＝比べた後で決める。TRIMA＝偶数の n について TA-Lib の TRIMA(n)・VIDYA＝CMO の本数 m を n と別に持つ版）
~~~
根拠の抜き書き: ta-lib.org/functions/trima.html「even: SMA(SMA(x,period/2),period/2+1)」
状態: 未決
補足: 並べる数字＝TRIMA は差の最大%と月ごとの net・VIDYA は m=n と m=(3n+2)//4 の相関と月ごとの net

#### 修正 53（MAMA・FAMA・HT_TRENDLINE の入力の比べ方）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1082-1083（MAMA・FAMA は 1085-1086 の同じ形）
直す前の文字:
~~~
_reg("close vs HT_TRENDLINE%", "close vs HT_TRENDLINE%", True,
     lambda d: (d.close / _pta6.ht_trendline(close=d.close) - 1) * 100)
~~~
直した後の文字:
~~~
（比べた後で決める。Ehlers の入力＝(高値＋安値)/2）
~~~
根拠の抜き書き: observe_diag.py:1083「     lambda d: (d.close / _pta6.ht_trendline(close=d.close) - 1) * 100)」
状態: 未決
補足: 並べる数字＝入力を終値にした場合と (H+L)/2 にした場合の相関と月ごとの net

#### 修正 58（THERMO% の説明が実装と食い違う）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3676-3679
直す前の文字:
~~~
_r(r"THERMO%", "THERMO%",
   "エルダーの温度計＝安値の下げ幅と高値の上げ幅の大きい方を、終値で割って%化",
   "Alexander Elder（ライブラリの既定 length=20）。値段の単位なので終値で割る（H6）", "ボラ量", "vol",
   tb=_tb_thermo_pct, known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)])])
~~~
直した後の文字:
~~~
_r(r"THERMO%", "THERMO%",
   "前の足からの高値の動きの絶対値と安値の動きの絶対値の大きい方を、終値で割って%化",
   "ライブラリの作り（絶対値を取る）。★Elder の原作は外へはみ出した幅だけ（内はらみ足は 0・"
   "Come Into My Trading Room 2002 p.162）で、値が違う（監査 CP60）。ライブラリの既定 length=20。値段の単位なので終値で割る（H6）",
   "ボラ量", "vol",
   tb=_tb_thermo_pct, known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)])])
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/volatility/thermo.py:42「    thermoH = (high - high.shift(drift)).abs()」
状態: 確定
補足: 作りを教科書に寄せるかは修正 45 で比べる

#### 修正 65（帯内位置% の下半分の尺度の比べ方）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 4265-4267（RANGE_GEO_REF の後ろに、比べる候補の列を1つ足す案）
直す前の文字:
~~~
    "帯内位置%": dict(kind="ratio", teigi="上半分の帯内位置＝(close − mid) / (res_hi − mid)。mid=0・res_hi=1",
                  ryugi="S2 入口の pos と同式（e38_logic_parts._pullback_short L95-99）。分母≤0 は欠損",
                  houkou="順張り値＝1 に近いほど上端（戻り売りの場所）"),
~~~
直した後の文字:
~~~
    "帯内位置%": dict(kind="ratio", teigi="上半分の帯内位置＝(close − mid) / (res_hi − mid)。mid=0・res_hi=1",
                  ryugi="S2 入口の pos と同式（e38_logic_parts._pullback_short L95-99）。分母≤0 は欠損",
                  houkou="順張り値＝1 に近いほど上端（戻り売りの場所）"),
    "下半分位置": dict(kind="ratio", teigi="下半分の帯内位置＝(close − mid) / (mid − sup_lo)。mid=0・sup_lo=−1",
                   ryugi="帯内位置% の下半分の対（%b と同じく、その半分の幅で割る・監査 CP60）。分母≤0 は欠損",
                   houkou="順張り値＝−1 に近いほど下端（押し目買いの場所）"),
~~~
根拠の抜き書き: observe_diag.py:1840「        pos = np.where(np.isfinite(span) & (span > 0), (c - mid) / span, np.nan)」（span＝res_hi − mid。下半分も上半分の幅で割っている）
状態: 未決
補足: 並べる数字＝(1) sup_lo に触れた5分足の帯内位置% の分布（中央値・四分位）が −1 からどれだけ散るか (2) Long 側のレシピで帯内位置% を使った案と下半分位置を使った案の net（同じ探索回数）。足すと決めたら、列を作る observe_diag.py:1837-1843 と engine_tuner_exec.py:2683-2689 も直す

### Minor

#### 修正 54
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1133
直す前の文字:
~~~
   "n 本最高値からの乖離%（0に近いほど高値圏）", "標準。close vs n本高値% と同一の式＝重複列（歩2 の同系統制限の対象）",
~~~
直した後の文字:
~~~
   "n 本最高値からの乖離%（0に近いほど高値圏）", "n 本最高値（Donchian 上限）。教科書の swing（前後が下がった山）ではない＝それは fractal高値距離%。全列が drop_columns に在る（監査 CP60）",
~~~
根拠の抜き書き: observe_config.json:173「  ["swing高値距離%24", "close vs 24本高値%"],」
状態: 確定
補足: 1137 行の swing安値距離 も同じ形に直す

#### 修正 55
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1216
直す前の文字:
~~~
   "ケルトナーチャネル上バンド（EMA + k×ATR14）からの乖離%", "Keltner（ATR は Wilder 14）",
~~~
直した後の文字:
~~~
   "ケルトナーチャネル上バンド（EMA + k×ATR14）からの乖離%", "Keltner（ATR は Wilder 14・教科書の StockCharts は ATR(10)。監査 CP60 の実測で ATR10 版と相関 0.99816・上抜けの一致 99.24%＝決め打ちのまま残す）",
~~~
根拠の抜き書き: observe_diag.py:878「     (d.close / (d.close.ewm(span=n, adjust=False).mean() + k * _atr(d.high, d.low, d.close)) - 1) * 100)」
状態: 確定
補足: 1220 行の Keltner下 も同じ

#### 修正 56
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1254
直す前の文字:
~~~
   "n 本の高安レンジの中の位置 0〜1", "フィボナッチ・リトレースメントの位置測定", "順張り値", "trend", tb=_tb_fib,
~~~
直した後の文字:
~~~
   "n 本の高安レンジの中の位置 0〜1", "Stoch の素の %K÷100 と同じ式。フィボナッチの比率（0.382・0.618）は閾値で書く（監査 CP60）", "順張り値", "trend", tb=_tb_fib,
~~~
根拠の抜き書き: observe_diag.py:893「_reg("fib位置", "fib位置{}", True, lambda d, n: (d.close - d.low.rolling(n).min())」
状態: 確定
補足: 説明だけ

#### 修正 57
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2599
直す前の文字:
~~~
   "標準（PPO）。★平均は単純移動平均（ライブラリの既定）。シグナルは EMA", "順張り値", "trend", tb=_tb_ppo)
~~~
直した後の文字:
~~~
   "PPO の形。★平均は単純移動平均（ライブラリの既定）＝StockCharts の標準は EMA。教科書の EMA 版は MACD線% と相関 0.9998 の重複になるので SMA のまま残す（監査 CP60）。シグナルは EMA", "順張り値", "trend", tb=_tb_ppo)
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/momentum/ppo.py:27「        fastma = ma(mamode, close, length=fast)」
状態: 確定
補足: 説明だけ。TA_CLASS_MAP 4346-4348 の PPO・STC の行にも「名前の対応だけ・値は違う」の注記を足す

#### 修正 63（MMAR の重複）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1094-1095
直す前の文字:
~~~
_reg("close vs MMAR%", "close vs MMAR%{}", True,
     lambda d, k: (d.close / _pta6.mmar(close=d.close, length=k, num_ribbons=1)[f"MMAR_{k}"] - 1) * 100)
~~~
直した後の文字:
~~~
（未決＝帯を1本の EMA(k) に縮めた作りで、助走の後は close vs EMA と同じ値になる。重複の一覧（observe_config.json の drop_columns）に載せるかを まこさんが決める）
~~~
根拠の抜き書き: observe_diag.py:1095「     lambda d, k: (d.close / _pta6.mmar(close=d.close, length=k, num_ribbons=1)[f"MMAR_{k}"] - 1) * 100)」
状態: 未決
補足: 並べる数字＝close vs MMAR%k と close vs EMAk% の相関（助走の後）

#### 修正 64（教科書の既定と同じ値で固定している数字を探させるか）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 44
直す前の文字:
~~~
  "material_param_ranges": {},
~~~
直した後の文字:
~~~
（未決＝まこさんが範囲を書く。対象＝ALMA の σ・offset・KAMA の 2/30・T3 の 0.7・MAMA の 0.5/0.05・JMA の phase・SSF の poles・PSAR の 0.02/0.2・CKSP の 10/3/20。どれも教科書の既定と同じ値なので、教科書からの変更ではない＝反するにはしていない）
~~~
根拠の抜き書き: recipes/search_limits.json:45「…★ここに書くのは まこさんが決めた範囲だけ。…」
状態: 未決

#### 修正 66（CKSP の説明）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2908-2912
直す前の文字:
~~~
_r(r"close vs CKSPl%", "close vs CKSPl%",
   "終値が Chande Kroll の買い側の逆指値から何%離れているか",
   "Chande & Kroll。★独立実装は書いていないが、定義から導ける既知答えで検証する＝"
   "値段が一定なら逆指値も その値に張り付くので、この列は ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
~~~
直した後の文字:
~~~
_r(r"close vs CKSPl%", "close vs CKSPl%",
   "終値が Chande Kroll の買い側の逆指値（10本高値 − 3×ATR10 の 20本最高値）から何%離れているか",
   "Chande & Kroll（本の数字 p=10・x=3・q=20・ATR は Wilder 平滑＝ライブラリの既定）。★TradingView はこの線を"
   "short stop と呼ぶ（名前が逆・値は同じ）。★独立実装は書いていないが、定義から導ける既知答えで検証する＝"
   "値段が一定なら逆指値も その値に張り付くので、この列は ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
~~~
根拠の抜き書き: ta-lib.org/functions/cksp.html「a multiplier of 3 and a stop period of 20」
状態: 確定
補足: 説明だけ

#### 修正 67（SMC_SWEEP の向きの印）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 986
直す前の文字:
~~~
_reg("SMC_SWEEP", "SMC_SWEEP", False, lambda d: _pta6.smc_sweep(open_=d.open, high=d.high, low=d.low, close=d.close))
~~~
直した後の文字:
~~~
_reg("SMC_SWEEP", "SMC_SWEEP", True, lambda d: _pta6.smc_sweep(open_=d.open, high=d.high, low=d.low, close=d.close))
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/momentum/smc_sweep.py（値は +1＝上向きの刈り取り・−1＝下向き。F と C の報告）
状態: 確定
補足: engine_tuner は参照表の houkou「反転サイン」を読むので、効くのは observe_diag の出口の調べ（2296行）だけ

#### 修正 68（上位足の値が5分足1本ぶん遅れて届く）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1784
直す前の文字:
~~~
                    s.index = src.index + pd.Timedelta(TF_RULE[tf])
~~~
直した後の文字:
~~~
                    s.index = src.index + pd.Timedelta(TF_RULE[tf]) - (bars.index[1] - bars.index[0])
~~~
根拠の抜き書き: observe_diag.py:1605「    return df.resample(rule, label="left", closed="left").agg(」
状態: 未決
補足: 未来は使っていない＝遅れる向き。直した後も、5分足の行 R は R+5分に閉じるので、閉じた時刻 ≤ R+5分 の上位足だけが当たる。並べる数字＝15m・1h・4h の材料を使う案の値決め窓の net を、今と直した後で。直すなら検査 _insp_close_leak（3779-3797）と e38_logic_parts.py:66-69 の `_al` もそろえる

#### 修正 69（帯の1時間足の区切りの説明）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 4253
直す前の文字:
~~~
RANGE_GEO_TF = "5m（1h ゾーンを足が閉じた時刻から ffill・状態機械は過去 close の逐次更新）"
~~~
直した後の文字:
~~~
RANGE_GEO_TF = "5m（1h ゾーンは label=right・closed=right で5分足の始まりの時刻を束ねる＝1時間足の区切りは正時から5分ずれる（例 10:05〜11:05）。5分足の行 T（11:00）へ ffill＝その行が閉じた時に確定済み・状態機械は過去 close の逐次更新）"
~~~
根拠の抜き書き: observe_diag.py:189「時刻はバーの始まりの時刻」
状態: 確定
補足: 説明の文。作りを正時にそろえるかは未決＝そろえると S2 の恒等と labels_v17.csv の一致が崩れる（F の報告）

#### 修正 70（PMAX の説明）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2922-2925
直す前の文字:
~~~
_r(r"close vs PMAX%", "close vs PMAX%",
   "終値が PMAX（移動平均に値動きの荒さを足した追従線）から何%離れているか",
   "ライブラリの計算式。★定義から導ける既知答えで検証する＝値段が一定なら ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
~~~
直した後の文字:
~~~
_r(r"close vs PMAX%", "close vs PMAX%",
   "終値が PMAX（移動平均に値動きの荒さを足した追従線）から何%離れているか",
   "ライブラリの計算式（EMA10・ATR10・倍率3）。★原作（KivancOzbilgic）は移動平均を逆指値と比べて向きを決めるが、"
   "ライブラリは終値と比べる＝SuperTrend の型で、原作と値が違う（監査 CP60）。★定義から導ける既知答えで検証する＝値段が一定なら ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
~~~
根拠の抜き書き: /usr/local/lib/python3.13/site-packages/pandas_ta_classic/trend/pmax.py:30「        if close_arr[i - 1] > pmax_up_arr[i - 1]:」
状態: 確定
補足: 説明だけ。作りは修正 45 で比べる

#### 修正 71（Aberration の説明）
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3609-3619
直す前の文字:
~~~
_r(r"close vs ABER_ZG%", "close vs ABER_ZG%",
   "終値が、アバレーションの中心線（高値・安値・終値の平均の5本単純移動平均）から何%離れているか",
   "標準（ライブラリの既定 length=5・atr_length=15）。値段そのものなので終値との距離%にする"
   "（H6・close vs SMA% と同じ流儀）",
   "順張り値＝プラスで中心線より上", "trend", tb=_tb_aber_zg,
   known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)])])
_r(r"ABER位置", "ABER位置",
   "終値がアバレーションの帯（中心線 ± ATR15）の中のどこにあるか。0 で下の帯・1 で上の帯",
   "標準。帯の幅そのものは 2×ATR15 ＝ うちの ATR% の定数倍なので入れない（重複）。"
   "位置だけを入れる＝BB%b と同じ流儀",
   "順張り値＝大きいほど帯の上側", "trend", tb=_tb_aber_pos)
~~~
直した後の文字:
~~~
_r(r"close vs ABER_ZG%", "close vs ABER_ZG%",
   "終値が、アバレーションの中心線（高値・安値・終値の平均の5本単純移動平均）から何%離れているか",
   "★教科書ではない＝ライブラリ独自の作り（pandas-ta の説明の逐語＝Few internet resources on definitive"
   " definition）。Keith Fitschen の Aberration は『80本・標準偏差2倍のボリンジャーバンド』で別物（監査 CP60）。"
   "ライブラリの既定 length=5・atr_length=15。値段そのものなので終値との距離%にする"
   "（H6・close vs SMA% と同じ流儀）",
   "順張り値＝プラスで中心線より上", "trend", tb=_tb_aber_zg,
   known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)])])
_r(r"ABER位置", "ABER位置",
   "終値がアバレーションの帯（中心線 ± ATR15）の中のどこにあるか。0 で下の帯・1 で上の帯",
   "★教科書ではない＝ライブラリ独自の作り（上と同じ）。Fitschen の原作の帯は 80本 ± 標準偏差2倍＝BB%b(80,2.0)。"
   "帯の幅そのものは 2×ATR15 ＝ うちの ATR% の定数倍なので入れない（重複）。位置だけを入れる＝BB%b と同じ流儀",
   "順張り値＝大きいほど帯の上側", "trend", tb=_tb_aber_pos)
~~~
根拠の抜き書き: indicator_reference_diag.py:3611「   "標準（ライブラリの既定 length=5・atr_length=15）。値段そのものなので終値との距離%にする"」
状態: 確定
補足: 説明だけ。作りは修正 45 で比べる


## 9. CC プロセス欠陥対策

### Process

#### 修正 59
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 193（この行の後ろに足す）
直す前の文字:
~~~
# ══ 教科書の独立実装（③）════════════════════════════════════════════════
~~~
足す文字:
~~~
# ★CP60：下の独立実装のうち _tb_vs_pivot・_vp_ref・_tb_vs_vwap・_tb_wpat・_tb_sr_touch・_alma・_stc_parts・_tb_pos_hilo・
#   _tb_thermo_pct・_tb_dpo は、教科書の作りではなく、カタログかライブラリと同じ変形を別の書き方で写したもの＝
#   照合は「自分と同じか」しか確かめていない（ALMA の向き・STC の式・SAREXT の符号の誤りが検査3を通った理由）。
~~~
根拠の抜き書き: indicator_reference_diag.py:1846「    # ★重みは逆順にしてから当てる（ライブラリの実物の逐語＝w_norm[::-1]）」
状態: 確定
補足: 欠陥＝起案者は「独立実装と一致した」を「教科書どおり」と読み替えていた。直し方＝独立実装に「教科書から書いたか・ライブラリの写しか」の印を付け、写しのものには教科書の既知答え（例＝ALMA9 の新しい3本の重みの合計）を known= に足す

#### 修正 60
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2946（SAREXT の known=。CKSP 2912・PMAX 2925・PSAR の known= も同じ形）
直す前の文字:
~~~
   "この列は ぴったり 0", "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
~~~
足す文字:
~~~
（既知答えに「下げ続ける合成のバー」を足し、売り側を試す。値段一定の答えだけでは売り側を一度も通らない）
~~~
根拠の抜き書き: indicator_reference_diag.py:2946「   "この列は ぴったり 0", "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])」
状態: 未決
補足: 欠陥＝SAREXT の符号の誤りが「一致検証済み」で通った（observe_inspect の記録）。答えの値は手で出してから足す＝監査では走らせていない

#### 修正 61
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 4256
直す前の文字:
~~~
                   ryugi="RG ゾーンビルダー（build_regime_gate_rg._zones_1h_rg・fractal j+2 確定＝L-179 型の確定遅延）",
~~~
直した後の文字:
~~~
                   ryugi="RG ゾーンビルダー（build_regime_gate_rg._zones_1h_rg・fractal j+2 確定＝L-179 型の確定遅延）。"
                         "★engine_tuner（e38_logics.json の global.regime.v25_adaptive_band=true）は RG-v6＝束ね幅 "
                         "tol=clamp(0.5×ATR%_1h,0.15%,0.6%)（build_regime_gate_rg._adaptive_tol_1h・ATR は TR の14本単純平均）の帯を使う。"
                         "既知答え（range_geo_known_check）は固定 tol（RG-v5・adaptive_k=None）の帯",
~~~
根拠の抜き書き: observe_diag.py:1829「    adaptive_k=None（既定）＝RG-v5 固定束ね幅。エンジン E38 は RG-v6（e37.V25_K）を渡す＝流儀の違いは」（定義表 4255-4267 のどこにも RG-v6 の記載は無い。tuner_adapters/e38.py:301 が adaptive_k を渡す）
状態: 確定
補足: 欠陥＝コメントが「定義表に記載」と書いているのに、定義表に無い

#### 修正 62
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 1859-1872
直す前の文字:
~~~
    span = bars.loc[bars.index.max() - pd.Timedelta(days=int(cfg["warmup_days"]) + 3):]
    geo_full = build_range_geometry(span)
    picks = [span.index[-1], span.index[-100], span.index[-400]]
    suspects: dict = {}
    for t in picks:
        geo_tr = build_range_geometry(span.loc[:t])
        a, b = geo_full.loc[t], geo_tr.loc[t]
        for col in geo_full.columns:
            x, y = a.get(col), b.get(col)
            if pd.isna(x) and pd.isna(y):
                continue
            if pd.isna(x) != pd.isna(y) or abs(float(x) - float(y)) > 1e-9 * max(1.0, abs(float(x))):
                suspects.setdefault(col, []).append(str(t))
    print(f"  切り詰め再計算: サンプル時点 {len(picks)}点 × {geo_full.shape[1]} 列 → 不一致 {len(suspects)} 列")
~~~
直した後の文字:
~~~
    span = bars.loc[bars.index.max() - pd.Timedelta(days=int(cfg["warmup_days"]) + 3):]
    import e37_scalp as _e37g                   # engine_tuner は RG-v6（adaptive_k=V25_K）の帯を使う＝そちらも切り詰めで確かめる（監査 CP60）
    picks = [span.index[-1], span.index[-100], span.index[-400]]
    suspects: dict = {}
    for _ak in (None, _e37g.V25_K):
        geo_full = build_range_geometry(span, _ak)
        for t in picks:
            geo_tr = build_range_geometry(span.loc[:t], _ak)
            a, b = geo_full.loc[t], geo_tr.loc[t]
            for col in geo_full.columns:
                x, y = a.get(col), b.get(col)
                if pd.isna(x) and pd.isna(y):
                    continue
                if pd.isna(x) != pd.isna(y) or abs(float(x) - float(y)) > 1e-9 * max(1.0, abs(float(x))):
                    suspects.setdefault(f"{col}(adaptive_k={_ak})", []).append(str(t))
    print(f"  切り詰め再計算: サンプル時点 {len(picks)}点 × {geo_full.shape[1]} 列 × 帯2種（RG-v5・RG-v6） → 不一致 {len(suspects)} 列")
~~~
根拠の抜き書き: observe_diag.py:1860「    geo_full = build_range_geometry(span)」（adaptive_k を渡していない＝engine_tuner が使う RG-v6 の帯は未来参照の検査を通っていない）
状態: 確定
補足: 欠陥＝未来のデータの機械検査が、engine_tuner が実際に使う帯を見ていない。監査は RG-v6 の行を読み、未来を見る行は無かった＝値での確かめは承認の後の検査8で



## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

### 道具が止まったこと
- `python3 .claude/tools/gen_audit_docs.py result <依頼書> <作業場>/cp60_result.md` は rc=1「❌ 依頼書に道具の目印が無い（道具で作った依頼書ではない）」で止まった（依頼書は まこさんの決定で手で書いたもの）。ただし11節の骨組みは作業場に書き出していたので、それを埋めた。骨組みの5節に「該当なし（依頼書のとおり）」と入っていたが、依頼書は外部検索6件を求めているので、5節は書き直した。

### 開いたファイルと行（監査役が自分で開いたもの）
- 依頼書（全291行）・permanent_rules.md:155-174・next_step.md:1-80・adopted_strategies.md:1-40・cat_requirements.md:545-560・591-605・session_worklog_20261003.md:566-580
- indicator_switch.json（jq で on・off・geo_on・counts・time_on・ta_unresolved）
- observe_diag.py：355-400・517-527・605-620・766-808・836-912・1036-1044・1066-1086・1147-1148・1295-1299・1350-1360・1396-1399・1436-1442・1448-1460・1481-1490・1604-1606・1780-1786・1826-1843・1858-1862 と、所見に出た行（943・973・986・991・1000・1001・1013・1022・1133・1141・1160・1204）
- indicator_reference_diag.py：177・317-321・420-431・632-652・823-825・868-877・905-920・931-939・977-1004・1054-1057・1132-1138・1210-1222・1229-1235・1247-1276・1842-1847・1881-1882・1926-1927・2230-2231・2248-2253・2345-2366・2602-2604・2727-2730・2741-2744・2753-2754・2868・4250-4268・4547
- observe_config.json:130-138・148-154・170-179・268-272／recipes/search_limits.json:44-45／engine_tuner_exec.py:2052-2057／engine_tuner.py:99／gen_signal_families.py:118-125／tuner_adapters/e38.py:301／e38_logics.json:12
- pandas_ta_classic 0.6.52（/usr/local）：trend/sarext.py:134-139・overlap/alma.py:25-45・utils/_core.py:197-216・overlap/hilo.py:15-23・overlap/hwma.py:34-40・momentum/stc.py:165-205・momentum/ppo.py:15-27・momentum/trix.py:45・trend/pmax.py:30・34・volatility/thermo.py:41-42・volume/nvi.py:35-40・trend/dpo.py:11-34・volatility/aberration.py:15-33。版は METADATA の「Version: 0.6.52」（.venv は 0.6.20）
- サブエージェント6つが開いた行は、それぞれの報告の6節（作業場には残していない）

### 走らせたコマンドと結果と秒数
| コマンド | 結果 | 秒数 |
|---|---|---|
| `wc -l` 依頼書 | 291行 | 1未満 |
| `shasum -a 256` 3本（初めと終わりの2回） | b0080a8752e85d2a／d4f13163ebc7574d／3d33634067900696＝依頼書と一致 | 1未満 |
| `jq` で on・off・geo_on の数 | 141・117・2 | 1未満 |
| `python3 map_on.py`（作業場） | 143件の参照表の行と実装の行の手がかりの表 on143_map.tsv（語で拾っただけ・誤りは F・C・D が指摘＝W% の 1105 は RAINBOW・KAMA傾き% の「-」は 1071 に在る） | 1未満 |
| awk で `_r(` の塊ごとの ext= を数えた | 28件（最初の数え方は区切りを誤って29と出た＝直して28） | 1未満 |
| `python3 check_lib.py`（作業場・ライブラリ 0.6.52） | ALMA9 の一番新しい足の重み 0.0000・遅れ 9本 6.44（offset 0.15 で 1.56）・20本 15.20（3.80）／SAREXT の下げで close vs SAREXT% −191.89%（PSAR −8.1081%）／STC の1段目が凍る足 63.87%・STC の分位 10/50/90% ＝ 0.0/0.0/89.65（直近10万本）／close vs 24・48・96本高値% の最大 0.0000・今の足を除くとプラスの足 5.08%・3.17%・1.97% | 6.6 |
| `python3 check_lib2.py`（作業場） | 傾き%(k) と close vs X% の相関：KAMA20 k=5 0.6518・k=200 0.1124／KAMA200 k=5 0.8174・k=200 0.2182／WMA20 k=5 0.7719／WMA200 k=5 0.9457・k=200 0.3401／Keltner上%(20,2.0) の ATR14 と ATR10＝相関 0.99816・帯の高さの差の中央値 0.0092%・上抜けの一致 99.24% | 15.0 |
| `python3 check_fixes.py`（作業場・修正の「直した後の文字」の写し） | VAH新・VAL新・前期間PP・前期間R1・STC教科書・ALMA0.15・SAREXT絶対値・24本高値前の8本とも、切り詰め再計算の不一致 0/3／POC 新旧の一致 100.00%・VAH 25.06%・VAL 23.32%・VAL≤POC≤VAH 100.00%／STC 旧の中央値 0.00・新 50.00・相関 0.1569／SAREXT（絶対値）と PSAR の相関 0.7570・最小 −4.24% | 19.9 |
| awk で4節の143行の表の「教科書と違うか」「判定」の欄を数えた | 143行・違う 72・同じ 59・同じ＋変換 12／判定の先頭＝反する 18・分からない 25・貢献する 62・該当なし 38 | 1未満 |
| awk で8節・9節の修正の見出しを数えた | 71件・番号の抜け無し・Critical 35・Major 20・Minor 12・Process 4 | 1未満 |
| `shasum -a 256` 3本（19:35:37・監査の終わり） | 依頼書と同じ | 1未満 |
| `git status --short`（11節） | 下のとおり | 1未満 |

- データ＝`data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv`（読むだけ。check_lib・check_lib2 は直近10万本・check_fixes は直近2万本）。
- サブエージェントの awk の実測（監査役は走らせ直していない・各報告の数字）＝EMA傾きと close vs EMA の相関（A）・realized_vol の消える割合（A）・AO と PPO の相関 0.9974（C）・STC の凍り方 63.28%（C・全期間）・SQZ の一致率 92.07%（C）・SMC_SWEEP の割合（C）・StochRSI の相関 0.8795（C）・TRIX の符号の一致 94.42%（C）。

### 走らせられなかったもの・理由
- サブエージェント6つとも、`python3 -c` と `python3 - <<'EOF'` が hook `require_design_contract_before_run.sh`（走らせる .py を1つに決められない形を止める）に止められた。監査役は作業場に .py を書いて走らせたので、値で確かめられるものは上の3本で確かめた。
- 参照表の部品（`_mk`・`_wma_w`・`_range_case`・`_ema_seed`）を使う既知答えと検査3は、参照表を import すると検査の全体が動き作業場の写しで閉じないので、走らせていない（修正 16・20・26・29 に「承認の後の検査3で確かめる」と書いた）。
- 修正 1〜14・30〜34 の名前を変える案は、列の名前を使う16ファイルへの響きが大きく、写しで閉じないので走らせていない（案が複数）。
- サブエージェント F が、集計の途中で scratchpad（リポジトリの外の作業用の場所）に一時ファイル refs.tsv を1つ作った（本物ではない）。


## 11. 本物のファイルを書き替えていないこと

`git status --short`（監査の相手と、その周りに限った出力）:

~~~
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_L1.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_v59.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e38_S2.log
~~~

- 上の4つは監査の前から在った未追跡のファイル（サブエージェント F が監査の初めに同じ4つを報告している）。監査の相手（observe_diag.py・indicator_reference_diag.py・indicator_switch.json）・observe_config.json・rules・next_step.md に変更は無い（`git status --short -- <パス>` の出力が上の4行だけ）。ハッシュ値も監査の終わりに測り直して依頼書と同じ。
- リポジトリ全体の `git status --short` で変更（M）と出るのは `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md` だけ。更新時刻は 18:54:10 で、このセッションの開始のころ（監査役が最初に ToDo を書いたのは 18:55:44）。ファイルの1行目は「まこさんが決めたこと（gen_decisions.py が自動生成＝手書き禁止）」で、セッション開始の hook が作り直したもの。監査役とサブエージェントは書いていない。
- 監査役が書いたもの＝作業場 `.claude/audits/cp60_work/` の6本（map_on.py・on143_map.tsv・agent_prompt_common.md・check_lib.py・check_lib2.py・check_fixes.py）と骨組みを埋めた cp60_result.md、このセッションの ToDo の置き場（`.claude/state/sessions/ea52c303-…/session_todo.md`・`session_todo_posted`＝ToDo ゲートが求めるもの）、そしてこの結果ファイル。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-03_m2_law_faithful_range_20261003_plan_cp60_audit_request.md request_sha256=634fd5221ea55ec3230597a86ca821ac72a9e1f135923c9de0d0452a66258e4c -->
