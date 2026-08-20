# regime_detection_kb.md — 相場の場面（上げ・下げ・横ばい）を判定する手法の知識

作成: 2026-08-19（40回目のセッション）。
**まこさん指示（逐語）**＝「レンジ以外の、上げ相場、下げ相場なども判定できるようにしたいんだけど、わかってる？」「まずは、レジーム判定するための手法を、ウェブリサーチで徹底的に探して学習して。」

**この文書に書くもの**＝レジーム判定の手法の知識（辞典のレベル）。
**この文書に書かないもの**＝実験の結果・engine_tuner の設計・経緯（`cat_requirements.md` §8.2 の文書の割り当て）。

---

## ★出どころの区別（先に書きます）

**この文書の各項目には、次の2つの印のどちらかが付いています。**

| 印 | 意味 |
|---|---|
| **【本文】** | **記事や論文の本文を開いて、英語の原文をそのまま写しました。**引用は原文のままです |
| **【要約】** | **検索結果の要約しか取れていません**（PDF が読めない・403 で拒否された・本文を開いていない）。**設計の根拠には使いません** |

**なぜ分けるか**＝2026-08-18 に、私は手法の名前だけを14通り並べて中身を説明できませんでした（違反の記録 #19）。**要約で設計を書かない**（教訓 L-409）。

---

# §1 用語｜レジームとは何か

**レジーム＝相場の状態。**このプロジェクトでは、要件定義書 §1.2.1 が局面を4つに分けています。

| 局面 | 中身 | 担当の戦略 |
|---|---|---|
| 1 | 下げトレンド | P21・P23（合算 E32b） |
| 2 | 上げトレンド | なし（手つかずの所） |
| 3 | レンジ（横ばい） | E36・E38 |
| 4 | スパイク（急な急騰・急落） | E28（急落側） |

**＝engine_tuner が組み立てるべき判定は「レンジかどうか」の2択ではありません。少なくとも 上げ／下げ／横ばい の3つ、スパイクを入れれば4つを分けます。**

---

# §2 ★いちばん大事な整理｜「強さ」と「向き」は別の物差しです

**調べて分かった、いちばん効く整理がこれです。**

**トレンドかレンジかを分ける物差し（強さ）と、上げか下げかを分ける物差し（向き）は、別の指標です。**片方だけでは3つに分けられません。

**【本文】ADX の説明（StockCharts ChartSchool）**

> "The **Average Directional Index (ADX)** ... measures the ***strength*** of the trend (regardless of direction) over time."
> "The **Plus Directional Indicator (+DI)** and **Minus Directional Indicator (-DI)** ... measure trend ***direction*** over time."

**＝ADX は強さだけを測り、向きを測りません。向きは +DI と -DI が測ります。**

**この2つを組み合わせると、3つに分かれます。**

| 強さ | 向き | 場面 |
|---|---|---|
| 強い | +DI > -DI | 上げトレンド |
| 強い | +DI < -DI | 下げトレンド |
| 弱い | — | レンジ（横ばい） |

**★ここに、いまの engine_tuner に足りないものが出ています。**いまの E38 の場面の判定は、できあがった列の名前を指しているだけです。**「強さ」と「向き」を別々の条件として組み立てる形になっていません。**

---

# §3 手法の系統（7つ）

**調べた手法を7つの系統に分けました。**系統ごとに「何を測るか」「入力」「うちで使えるか」を書きます。

| 系統 | 代表 | 何を測るか | 出るもの |
|---|---|---|---|
| A | 指標で測る（ADX・CHOP・ER・VHF・MMI・Hurst・BB幅・Supertrend） | 強さ／向き／ばらつき | 数値 or 上下の札 |
| B | 統計のモデル（Markov switching・HMM・SETAR・jump model） | 隠れた状態 | 状態の番号と確率 |
| C | 教師なし学習（k-means・GMM・Wasserstein k-means・階層） | 似ている時間のかたまり | かたまりの番号 |
| D | 変化点の検出（online の2標本検定・MMD・signature） | 分布が変わった時刻 | 変わった／変わらない |
| E | 事象ベース（Directional Change・intrinsic time） | 値幅の反転 | 上げ区間／下げ区間 |
| F | ばらつきの構造（実現ボラの短期÷長期） | 拡大／収縮 | 3つの札 |
| G | 教師あり学習（XGBoost で次のレジームを当てる） | 次の期間の状態 | 状態の予測 |

---

## §3-A 指標で測る系統

### A-1｜ADX と DI（Wilder）【本文】

- **測るもの**＝ADX が強さ、+DI と -DI が向き。
- **出どころ**＝StockCharts ChartSchool「Average Directional Index (ADX)」。
- **【本文】の逐語**
  > "Wilder suggests that a strong trend is present when ADX is above 25 and no trend is present when ADX is below 20."
  > "The calculation example below is based on a 14-period indicator setting, as recommended by Wilder."
- **【本文】弱点の逐語**
  > "ADX also has a fair amount of lag because of all the smoothing techniques."
  > "As with most such systems, there will be whipsaws, great signals, and bad signals."
- **うちの実物**＝V9 が既に ADX を使っています。材料の一覧にも在ります。
- **★数字（25・20・14）は目安であって、うちの正解ではありません。**engine_tuner が範囲から探します。

### A-2｜Choppiness Index（Dreiss）【本文】

- **測るもの**＝強さの裏返し（値が大きいほど横ばい）。**向きは測りません。**
- **出どころ**＝TradingView サポート「Choppiness Index (CHOP)」。
- **【本文】計算の逐語**
  > "100 * LOG10( SUM(ATR(1), n) / ( MaxHi(n) - MinLo(n) ) ) / LOG10(n)"
- **【本文】既定の期間**＝ "14 is the Default"
- **【本文】区切りの逐語**
  > "61.8 for the high threshold and 38.2 for the lower threshold"
  > "With readings above the upper threshold, continued sideways movement maybe expected."
  > "Readings below the lower threshold may indicate a continuing trend."
- **中身の読み方**＝**1本ずつの値動きの合計** ÷ **n本ぜんぶで動いた幅**。行ったり来たりしていると、合計は大きいのに幅は小さくなるので、値が大きくなります。

### A-3｜Kaufman の効率比（Efficiency Ratio・ER）【本文】

- **測るもの**＝強さ（0〜1）。**向きは測りません**（絶対値を使うため）。
- **出どころ**＝StockCharts ChartSchool「Kaufman's Adaptive Moving Average (KAMA)」。
- **【本文】計算の逐語**
  > "ER = Change/Volatility"
  > "Change = ABS(Close - Close (10 periods ago))"
  > "Volatility = Sum10(ABS(Close - Prior Close))"
- **【本文】両端の意味の逐語**
  > "ER would be 1 if prices moved up 10 consecutive periods or down 10 consecutive periods."
  > "ER would be zero if price is unchanged over the 10 periods."
- **【本文】既定**＝ "10 is the number of periods for the Efficiency Ratio (ER)."
- **★CHOP と考え方が同じです。**「まっすぐ進んだ距離 ÷ 実際に歩いた距離」です。**CHOP は高値安値の幅を使い、ER は終値の差を使う**という違いです。

### A-4｜Market Meanness Index（MMI）【本文】

- **測るもの**＝強さ（ランダムからのずれ）。**向きは測りません。**
- **出どころ**＝The Financial Hacker「The Market Meanness Index」。
- **【本文】理屈の逐語**
  > "Any series of independent random numbers reverts to the mean—or more precisely, to their median—with a probability of 75%."
  > "If the MMI function is fed with perfectly random price changes from a perfectly efficient market, it will return a value of about 75%. The less efficient and the more trending the market becomes, the more the MMI decreases."
- **【本文】計算の中身**
  > "The MMI function just counts the number of data pairs for which the condition is met, and returns their percentage."
  > 条件＝中央値より上でかつ前の値より上がった、または、中央値より下でかつ前の値より下がった。
- **【本文】★書いた人自身の注意の逐語**
  > "Predicting the next price with the MMI would work as well as flipping a coin."
  > "A rising MMI alone is no promise of profit by cycle trading systems."
  > "Trend itself is trending... when we know that MMI is rising, we assume that the market is becoming more efficient, more random, more cyclic, more reversing or whatever, but in any case bad for trend trading."
- **★ここが重要です。**書いた本人が「これで次の値段は当てられない」と書いています。**MMI は建てる合図ではなく、場面のふるいです。**

### A-5｜Hurst 指数【本文（要旨のみ）】

- **測るもの**＝強さ（トレンドが続きやすいか、戻りやすいか）。**向きは測りません。**
- **読み方**＝0.5 より大きいとトレンドが続きやすい／0.5 より小さいと戻りやすい／0.5 はランダム。
- **出どころ**＝arXiv 2205.11122「Optimizing Returns Using the Hurst Exponent and Q Learning on Momentum and Mean Reversion Strategies」の要旨。
- **【本文】要旨の逐語**
  > "Using the Hurst exponent, which classifies time series as trending or mean reverting, we attempt to trade with each strategy when it is advantageous to generate higher returns on average."
  > "Trading with the Hurst exponent can achieve higher returns, but it also comes at a higher risk."
- **★「利益は増えたが、リスクも増えた」と書いてあります。**うちの合格の条件は net なので、そのまま使えるとは言えません。

### A-6｜Vertical Horizontal Filter（VHF）【要約】

- **測るもの**＝強さ。作った人＝Adam White（1991年）。
- **計算**＝（n本の最高値 − n本の最安値）÷（終値の前の足からの差の絶対値の合計）。
- **★CHOP・ER と同じ考え方の3本目です**（進んだ幅 ÷ 歩いた距離）。
- **出どころ**＝TradingView の説明ページ（検索結果の要約のみ・本文は未読）。

### A-7｜Bollinger Band の幅（BandWidth）とスクイーズ【要約】

- **測るもの**＝ばらつきの縮み（横ばいの前触れ）。**向きは測りません。**
- **考え方**＝帯の幅が過去に比べて狭いときが「スクイーズ」。そのあと帯を抜けた向きに動く、という使い方。
- **★注意（要約から）**＝帯が狭いこと自体は向きを教えない。抜けたと見せて戻る「だまし」がある。
- **出どころ**＝StockCharts ChartSchool「Bollinger Band Squeeze」「Bollinger BandWidth」（検索結果の要約のみ・本文は未読）。
- **うちの実物**＝BB 幅は材料に既に在ります。V9 も BB を使っています。

### A-8｜Supertrend【要約】

- **測るもの**＝**向き**（上下の札を直接 出す）。
- **計算**＝(高値+安値)÷2 に ATR の倍数を足し引きして帯を作り、終値が前の帯を抜けたら向きを反転させる。
- **出どころ**＝TradingView サポート「Supertrend」（検索結果の要約のみ・本文は未読）。
- **うちの実物**＝Supertrend は材料に在ります。

### A-9｜値動きの形（ZigZag・高値切り上げ／切り下げ）【要約】

- **測るもの**＝**向き**（高値と安値の並びで上げ・下げを決める）。
- **考え方**＝谷と山を交互に拾い、高値切り上げ＋安値切り上げなら上げ、逆なら下げ。
- **★⚠️ このやり方には未来参照が入ります。**ZigZag と Williams Fractals は、山を確定させるために **その後ろの数本**を見ます（要約の逐語＝ "a 5-bar lookback and look-forward period"）。**うちの決まり H2（未来参照の禁止）に当たります。**使うなら、確定を数本 遅らせる形にします（うちの `structure_features` が既にその形です）。
- **出どころ**＝TradingView・StockCharts の ZigZag の説明（検索結果の要約のみ・本文は未読）。

---

## §3-B 統計のモデル系統

### B-1｜Markov switching（Hamilton）と HMM【本文】

- **考え方**＝目に見えない「状態」がいくつか在り、状態ごとに値動きの性質（平均・ばらつき）が違うとする。観測から、いまどの状態かを確率で当てる。
- **出どころ**＝QuantStart「Market Regime Detection using Hidden Markov Models in QSTrader」。
- **【本文】学習のしかたの逐語**
  > "The risk management filter applied here works by training a Hidden Markov Model on S&P500 data from the 29th January 1993 ... through to the 31st December 2004."
  > 入力＝ "the percentage returns"（終値の変化率）だけ。
- **【本文】使い方の逐語**
  > "Long entry trades will only be carried out in regime 0, but closing trades are allowed in regime 1."
  > "If volatility is low any long trades are let through and carried out. If volatility is high any open trades are closed out upon receipt of the closing signal, while any new potential long trades are cancelled."
- **【本文】未来参照を避ける形の逐語**
  > "The backtest of this strategy is carried out from 1st January 2005 to 31st December 2014, without retraining the Hidden Markov Model along the way. In particular this means the HMM is being used out-of-sample and not on in-sample training data."
- **★弱点（別の検索結果の要約）**＝短い動きと長い動きを同時に捉えられず、短い揺れを長いトレンドの変化と読み違えることがある。

### B-2｜★HMM の未来参照の落とし穴（filtered と smoothed）【本文】

- **filtered**＝いまの時刻までの観測だけで、いまの状態を出す。**本番で使える。**
- **smoothed**＝**最後まで全部のデータ**を使って、過去の各時刻の状態を出し直す。**未来参照です。**
- **★ここを間違えると、バックテストだけ非常に良い数字が出ます。**うちの H2（本番の推論時点 t で取れる値だけを使う）に直接 当たります。
- **出どころ**＝mathandmarkets「Filtering vs. Smoothing: Why Backtests Lie About Regime Detection」。**2026-08-19 に本文を開いて逐語を取りました。**

**【本文】の逐語**

> "This is the hindsight illusion in backtests. When you fit an HMM to historical data and plot the state probabilities, you're looking at smoothed estimates. The model 'knows' there's a regime change coming because it has seen the future data."

> "The filtered estimate is noisier and lags behind the true transitions."

**【本文】遅れの実測（この記事の数字・日足）**

| 何 | 値 |
|---|---|
| 上げ → 下げ の検出の遅れ（中央値） | 2〜3日 |
| 同（上位10%） | 7日 |
| 下げ → 上げ の検出の遅れ（中央値） | 1〜2日 |

### B-3｜閾値のモデル（SETAR ほか）【要約】

- **考え方**＝観測できる値が決めた線を越えたら、状態が切り替わる。
- **★これはテクニカル指標の使い方と同じ形です**（ADX が 25 を超えたらトレンド、など）。**engine_tuner が組み立てやすいのはこの形です。**
- **出どころ**＝arXiv の regime detection の総説の要約（本文は未読）。

### B-4｜統計的ジャンプモデル（Statistical Jump Model）【本文】★注目

- **考え方**＝時間ごとの特徴量をかたまりに分けるとき、**状態が切り替わるたびに罰を足す。**罰を大きくすると、状態が長く続くようになる。
- **出どころ**＝arXiv 2402.05272v2「Downside Risk Reduction Using Regime-Switching Signals: A Statistical Jump Model Approach」。
- **【本文】仕組みの逐語**
  > "JMs are based on the principle of clustering temporal features while simultaneously imposing penalties for each jump in the hidden state sequence."
  > "This penalization is regulated by a hyperparameter known as the _jump penalty_, which reflects our prior belief about the desired persistence of the hidden state sequence."
  > "With a zero jump penalty, the model reduces to a k-means clustering algorithm, ignoring temporal information. As λ increases, state transitions become less frequent."
- **【本文】入力の逐語**
  > "we employ a feature set outlined in Table 2, consisting of three return and risk measures derived from an excess return series."
  > "Specifically, we use an exponentially weighted moving (EWM) downside deviation (DD) with a halflife of 10 trading days, and EWM Sortino ratios with halflives of 20 and 60 days."
- **【本文】状態の数の逐語**
  > "both models employ a two-state implementation (K=2), which, despite statistical criteria often favoring more states...has proven sufficient for capturing the dynamics of a single return series."
- **【本文】HMM との比較の逐語**
  > "JMs can outperform HMMs in identification accuracy and state sequence persistence."
- **★うちにとって重要な点**＝**「状態がどれだけ長く続いてほしいか」を、つまみ1つ（jump penalty）で調整できます。**うちが過去にレジーム判定を凍結した理由の3つ目は「ラベルは16〜28時間 続くのに、取引は中央値15分＝時間の単位が合っていない」でした（`regime_trial_log.md`）。**この罰のつまみは、その時間の単位を合わせるための調整箇所になり得ます。**

---

## §3-C 教師なし学習の系統

### C-1｜k-means・GMM・階層クラスタリング【要約】

- **考え方**＝値動きから作った特徴量で、似ている時間どうしをかたまりに分ける。かたまり＝レジーム。
- **★注意**＝**かたまりを作るときに全期間を使うと、未来参照になります。**値決め窓だけで分け方を決め、採点窓には当てはめるだけにします（うちの H8 と同じ）。
- **出どころ**＝arXiv の総説の検索結果の要約（本文は未読）。

### C-2｜Wasserstein k-means【本文（要旨のみ）】

- **考え方**＝時間のかたまりを「分布そのものの距離」で分ける。値動きのモデルを仮定しない。
- **出どころ**＝arXiv 2110.11848「Clustering Market Regimes using the Wasserstein Distance」の要旨。
- **【本文】要旨の逐語**
  > "The problem of rapid and automated detection of distinct market regimes is a topic of great interest to financial mathematicians and practitioners alike."
  > "The method is robust in the sense that it does not depend on modelling assumptions of the underlying time series as our experiments with real datasets show."
- **★うちに向いているか**＝**いますぐは向きません。**engine_tuner は「条件の束」を組み立てるプログラムです。分布の距離は条件の形にできません。**将来、材料を作る側で使う余地はあります。**

---

## §3-D 変化点の検出の系統【要約】

- **考え方**＝いまの窓と少し前の窓の分布が違うかを、その場（online）で検定する。違えばレジームが変わったと判定する。
- **代表**＝arXiv 2306.15835「Non-parametric online market regime detection and regime clustering for multidimensional and path-dependent data structures」。**PDF が読み取れず、本文は未読。**
- **要約から取れたこと**＝2標本検定・MMD（分布の距離）・signature（経路の特徴）を使う。
- **★うちに向いているか**＝いますぐは向きません（条件の形にできない）。

---

## §3-E 事象ベース（Directional Change・intrinsic time）【要約】

- **考え方**＝時計の時間ではなく、**値段が決めた割合だけ反転したとき**を1つの単位にする。上げ区間と下げ区間が交互に並ぶ。
- **★うちに向いている点**＝**時間足に縛られません。**5分足で見ると横ばいでも、0.3% の反転で区切れば上げ区間・下げ区間が出ます。
- **★うちに向いていない点**＝反転の割合（しきい値）を決める必要があり、その値の選び方が新しい調整箇所になります。
- **出どころ**＝arXiv・SSRN の Directional Change の論文群（検索結果の要約のみ・本文は未読）。

---

## §3-F ばらつきの構造（実現ボラの短期÷長期）【要約】★暗号資産の直近の研究

- **考え方**＝短い期間の実現ボラと長い期間の実現ボラの比、および向きの強さで、**拡大（Expansion）／中立（Neutral）／収縮（Contraction）**の3つに分ける。
- **データ**＝BTC の高頻度データ（2024年と2025年）。
- **出どころ**＝SSRN「Detecting Volatility Regimes in Crypto Markets using Realized Volatility Structure and Normalized Momentum」（Kaustuv Banerjee）。**本文は 403 で開けず、未読。**
- **★注意**＝これは「上げ・下げ」ではなく「ばらつきが拡大か収縮か」の3分けです。**向きは別に要ります。**

---

## §3-G 教師あり学習で次のレジームを当てる【要約】

- **考え方**＝まずレジームのラベルを作り（B や C の手法で）、そのラベルを教師にして XGBoost などで**次の期間のレジーム**を当てる。
- **出どころ**＝arXiv 2406.09578 ほかの検索結果の要約（本文は未読）。
- **★うちの立ち位置**＝いまは固定ルールで進めています（要件定義書 §8.5）。ML は まこさんが解禁したときです。

---

# §4 ★手法を選ぶときの考え方（調べて分かったこと）

## 4-1｜3つに分けるには、物差しが2本 要る

**強さの物差し**（ADX・CHOP・ER・VHF・MMI・Hurst・BB幅）と、**向きの物差し**（DI の大小・Supertrend・移動平均の傾き・高値安値の並び）を**掛け合わせる**と、上げ／下げ／横ばいの3つになります。**強さだけの指標をいくつ重ねても、上げと下げは分かれません。**

## 4-2｜強さの指標は、どれも同じ形をしている

**CHOP・ER・VHF は、中身がほぼ同じ考え方です。**

| 指標 | 分子 | 分母 |
|---|---|---|
| ER | 終値の n本前との差（絶対値） | 1本ごとの終値の差の絶対値の合計 |
| VHF | n本の最高値 − n本の最安値 | 1本ごとの終値の差の合計 |
| CHOP | 1本ごとの値幅（ATR(1)）の合計 | n本の最高値 − 最安値（★分子と分母が ER・VHF と逆） |

**＝「まっすぐ進んだ距離」と「実際に歩いた距離」の比です。**
**★だから、この3つを同時に条件に入れても、情報はほとんど増えません。**組み立ての決まり（同じ系統を重ねない）が効く場所です。

## 4-3｜レジーム判定は「建てる合図」ではなく「場面のふるい」

MMI を作った人の逐語（上の A-4）＝ "Predicting the next price with the MMI would work as well as flipping a coin."
HMM の使い方の逐語（上の B-1）＝ "Long entry trades will only be carried out in regime 0"。

**＝レジーム判定は、建てる合図そのものではありません。「この場面では建てる／建てない」を決めるふるいです。**
うちの E38 でも、場面の判定は入口の条件とは別の役割です。

## 4-4｜★状態が続く長さと、玉を持つ長さを合わせる

**うちが過去にレジーム判定を凍結した理由の3つ目**＝「ラベルは16〜28時間 続くのに、取引は中央値15分＝時間の単位が合っていない」（`regime_trial_log.md`）。

**外の研究にも、同じ問題が名前つきで在りました。**

**【本文】arXiv 2602.03395v4「The Label Horizon Paradox」の逐語**
> "Minimizing training error on the canonical target horizon t+Δ does not guarantee optimal generalization on t+Δ. Contrary to intuition, the most effective supervision signal is often misaligned with the inference target, residing at an intermediate horizon t+δ (where δ≠Δ) that better balances signal realization against noise."
> "Here, the signal's effective lifespan is shorter than the target window. Initially, rapid information gain improves performance; however, once the signal saturates, the persistent noise penalty eventually dominates, resulting in a peak at an intermediate horizon (0<δ∗<Δ)."

**＝「どれだけ先を見て判定するか」は、当てたい先と同じである必要はなく、それ自体が探す値です。**

**そして、状態の続く長さを直接 調整できる手法が在ります**＝統計的ジャンプモデルの jump penalty（上の B-4・【本文】 "As λ increases, state transitions become less frequent."）。

**★＝過去に凍結した理由は「レジーム判定が使えない」ではなく「続く長さを調整する仕組みを持っていなかった」と読めます。**（これは私の読みです。実データで確かめていません。）

## 4-5｜レジームのふるいが必ず効くとは限らない

検索結果の要約に、次の指摘が在りました（**本文は未読**）。

- トレンド追随の戦略にレジームのふるいを掛けると、ふるいが「本当の状態」ではなく「値動きの外れ値」を拾ってしまうことがある。
- 平均回帰の戦略の方が、レジームのふるいと相性が良い。

**★うちの E38 はレンジ（平均回帰）のスキャルです。**この指摘が正しければ相性は良い側ですが、**本文を読んでいないので根拠としては弱いです。**

## 4-6｜★判定を安定させる仕組みは2つある（別のもの・混ぜない）【本文】

**場面の判定は、1本のバーで切り替わると使えません。**外の資料は、安定させる仕組みを2つ挙げています。**この2つは別のものです。**

| # | 仕組み | 中身 | うちで書けるか |
|---|---|---|---|
| 1 | **何本 続いたら成立とみなすか** | 3〜5本 続けて線を超えたら成立とみなす | **書けます**（条件の形 `streak`） |
| 2 | **入る線と出る線を別にする** | 0.6 を超えたら入り、0.4 を割るまで出ない | **書けません**（2026-08-19 実測＝状態を保つ形が条件の部品に0件） |

**【本文】mathandmarkets「Filtering vs. Smoothing: Why Backtests Lie About Regime Detection」の逐語**

> "Require sustained signal. Don't act on P(Bear) > 0.5 for one day. Require 3+ consecutive days above threshold."

> "Use hysteresis. Entry threshold: P(Bear) > 0.6. Exit threshold: P(Bear) < 0.4."

> "Confirmation signals. Combine HMM with other indicators (VIX level, trend breaks)."

**【本文】traderssecondbrain「Market Regime: Trending vs Ranging vs Volatile」の逐語**

> "Only switch strategies when regime signals are unambiguously confirming new regime AND have been confirming for 3-5+ bars."

> "ADX (Average Directional Index) for trend strength — above 25 indicates trending, below 20 indicates ranging."

> "Bollinger Band Width for volatility regime — expansion above historical average indicates volatile expansion, contraction below indicates compression."

**★うちの RG-v5 は 2番の形です。**上げの判定が、発火の条件4つと解除の条件3つを持ち、発火してから解除されるまで真であり続けます（`build_regime_gate_rg._uptrend_state_5m`）。
**★数字（0.6／0.4／3〜5本／ADX 25・20）は目安であって、うちの正解ではありません。**engine_tuner が範囲から探します。

---

# §5 ★未来参照（H2）に当たるもの — 使う前に必ず見る

| 手法 | 何が未来参照か | 避け方 |
|---|---|---|
| **HMM の smoothed 状態** | 最後まで全部のデータを使って、過去の状態を出し直す | **filtered（その時刻までの観測だけ）を使う** |
| **ZigZag・Williams Fractals・高値安値の並び** | 山や谷を確定させるために、その後ろの数本を見る | **確定を数本 遅らせる**（うちの `structure_features` が既にこの形） |
| **かたまりを作る（k-means・GMM・jump model）** | 全期間で分け方を決めると、採点窓の情報が入る | **値決め窓だけで分け方を決め、確認窓・採点窓には当てはめるだけ** |
| **しきい値を全期間の分位で決める** | 分位が全期間から出る | **その時刻までの過去だけで分位を出す** |
| **モデルを途中で学習し直す** | 学習し直す時点より後のデータが入りうる | QuantStart の逐語＝ "without retraining the Hidden Markov Model along the way" |

**★うちには、この検査を実際に走らせるプログラムが既に在ります**＝`leak_causality_diag.py`（データを途中で切った走行と切らない走行を突き合わせる）。**レジーム判定を足したら、この検査を走らせ直します。**

---

# §6 まだ調べていないこと（正直に書きます）

| # | 何 | なぜ取れなかったか |
|---|---|---|
| 1 | 暗号資産の3分け（Expansion／Neutral／Contraction）の具体的な計算式としきい値 | SSRN が 403 で本文を開けなかった |
| 2 | 日中（intraday）のかたまり分けの論文（arXiv 1508.04900）の中身 | PDF が読み取れなかった |
| 3 | その場で変化点を検出する手法（arXiv 2306.15835）の中身 | PDF が読み取れなかった |
| 4 | レジームのふるいがトレンド追随で効きにくいという指摘（SSRN 6621520）の中身 | 本文を開いていない |
| 5 | VHF・Supertrend・BB スクイーズ・ZigZag の本文 | 検索結果の要約だけ |
| 6 | 出来高・板の情報を使うレジーム判定 | 探していない（うちの材料に需給の部品が0件のため後回し） |

---

# §7 出どころの一覧（URL）

**本文を開いたもの**

1. [Choppiness Index (CHOP) — TradingView](https://www.tradingview.com/support/solutions/43000501980-choppiness-index-chop/)
2. [Kaufman's Adaptive Moving Average (KAMA) — StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/kaufmans-adaptive-moving-average-kama)
3. [Average Directional Index (ADX) — StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx)
4. [The Market Meanness Index — The Financial Hacker](https://financial-hacker.com/the-market-meanness-index/)
5. [Downside Risk Reduction Using Regime-Switching Signals: A Statistical Jump Model Approach — arXiv 2402.05272v2](https://arxiv.org/html/2402.05272v2)
6. [Market Regime Detection using Hidden Markov Models in QSTrader — QuantStart](https://www.quantstart.com/articles/market-regime-detection-using-hidden-markov-models-in-qstrader/)
7. [Clustering Market Regimes using the Wasserstein Distance — arXiv 2110.11848](https://arxiv.org/abs/2110.11848)
8. [Optimizing Returns Using the Hurst Exponent and Q Learning — arXiv 2205.11122](https://arxiv.org/abs/2205.11122)
9. [The Label Horizon Paradox — arXiv 2602.03395v4](https://arxiv.org/html/2602.03395v4)

**★2026-08-19（42回目）に本文を開いたもの（2本）**

- [Filtering vs. Smoothing: Why Backtests Lie About Regime Detection — mathandmarkets](https://mathandmarkets.com/p/regime-detection-part-2-the-latency)（§3-B-2 と §4-6 に逐語）
- [Market Regime: Trending vs Ranging vs Volatile — traderssecondbrain](https://traderssecondbrain.com/guides/market-regime-identification)（§4-6 に逐語）

**検索結果の要約だけのもの**

10. [Market Regime Detection via Realized Covariances — arXiv 2104.03667](https://arxiv.org/abs/2104.03667)
11. [Non-parametric online market regime detection — arXiv 2306.15835](https://arxiv.org/pdf/2306.15835)
12. [Automated regime classification using sliced Wasserstein k-means — arXiv 2310.01285](https://arxiv.org/abs/2310.01285)
13. [Detecting intraday financial market states using temporal clustering — arXiv 1508.04900](https://arxiv.org/pdf/1508.04900)
14. [Detecting Volatility Regimes in Crypto Markets — SSRN 5920642](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5920642)
15. [Dynamic Asset Allocation with Asset-Specific Regime Forecasts — arXiv 2406.09578](https://arxiv.org/html/2406.09578v1)
16. [The Matched Filter Principle for Trading Strategy Regime Detection — SSRN 6621520](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6621520)
17. [Bollinger Band Squeeze — StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/bollinger-band-squeeze)
18. [Supertrend — TradingView](https://www.tradingview.com/support/solutions/43000634738-supertrend/)
19. [Vertical Horizontal Filter — TradingView](https://in.tradingview.com/scripts/vhf/)
20. [ZigZag — StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/zigzag)
21. [Multi-Scale Markov-Switching GARCH — arXiv 2606.06190](https://arxiv.org/html/2606.06190v1)
22. [Agent-Based Model in Directional-Change Intrinsic Time — SSRN 3240456](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3240456)

---

# §8 うちの正本との突き合わせ（次にやること）

**★この節はまだ中身がありません。**次の順で埋めます。

1. `indicator_combination_kb.md` の §7（レンジ判定の組み立ての決まり RG-1〜RG-4 と、測るもの3つ）と、上の §4 を突き合わせる。
2. `regime_research.md`・`regime_trial_log.md`（過去に作った14版・2系統と、止めた理由）と、上の §4-4 を突き合わせる。
3. うちの材料の一覧（`materials.md`）に、上の指標がどれだけ在るかを実際に数える。

---

# §9 別の AI に聞いた内容（まこさんが貼ったもの・逐語）

**まこさん指示 2026-08-19・逐語**＝「別AIに聞いた内容も貼る。」

**★出どころの3つ目の印を足します。**

| 印 | 意味 |
|---|---|
| **【別AI】** | **まこさんが ChatGPT と Gemini に聞いて、その回答をチャットに貼ったもの。**★URL も、元になった記事の逐語も付いていません。**事実の根拠には使いません。意見として記録します** |

**★なぜ根拠に使わないか**＝出どころが確かめられないものを根拠にすると、恒久の決まり53番（調べて証拠がある状態になるまで発言しない）と54番（出典を付け替えない）に反します。**ただし、私が見落としていた手法や考え方が入っているので、突き合わせの相手として使います。**

## 9-1｜ChatGPT の回答（逐語・1文字も変えていません）

```
BTC先物のレジーム判定なら、単一インジケーターよりも「トレンド / レンジ / 高ボラ / 低ボラ / ブレイクアウト」を分けて考えるのが実用的です。

特に、まこさんの5分足・レンジ逆張りBOTを前提にすると、重要度はかなり変わります。

手法	判定できるもの	レンジBOTとの相性
ADX / DI	トレンド強度	★★★★★
Kaufman ER	トレンド性 vs ノイズ	★★★★★
BB Width	ボラティリティ状態	★★★★★
BB Width + その変化率	スクイーズ→拡大	★★★★★
EMA傾き / EMA乖離	トレンド方向・強度	★★★★☆
価格の傾き（Linear Regression Slope）	トレンド方向	★★★★☆
Choppiness Index	レンジ性	★★★★★
ATR / ATR%	ボラ状態	★★★★☆
Donchian Channel	ブレイク状態	★★★★☆
Hurst Exponent	平均回帰性 / 持続性	★★★☆☆
RSI / Stoch	オシレーター状態	★★★☆☆
MACD	トレンド転換	★★★☆☆
特に有力なのはこの5つ

① ADX

ADX低い → レンジ寄り
ADX高い → トレンド寄り
ただし「ADX=25以上」のような固定閾値だけでは遅れる。
ADXの値＋ADXの上昇/下降を見る方がレジーム判定には有効。

② Kaufman Efficiency Ratio（ER）

「価格がどれだけ一直線に進んでいるか」を測る。
ER低 → 行ったり来たり＝レンジ
ER高 → 一方向に進む＝トレンド
レンジ逆張りBOTにはかなり相性がいい。

③ Bollinger Band Width

BB Width低 → 低ボラ・圧縮
BB Width上昇 → ボラ拡大
BB Width高 → 高ボラ
特に**Widthそのものより「Widthの変化」**を見ると、レンジ→ブレイクの検出に使える。

④ Choppiness Index

ADXとは逆方向の発想で「どれくらいゴチャゴチャ動いているか」を見る。
高CHOP → レンジ/横ばい
低CHOP → トレンド
ADX + CHOPの組み合わせはかなり自然。

⑤ Linear Regression Slope

一定期間の価格に回帰直線を引いて、その傾きを測る。
slope ≈ 0 → 横ばい
slope > 0 → 上昇トレンド
slope < 0 → 下降トレンド
さらにATRで正規化するとBTCの価格水準に依存しにくくなる。
ただし、BTCでは「2軸」にするとかなり面白い

例えば、

                    トレンド性
                       ↑
             Trend     │     Strong Trend
                       │
        ───────────────┼──────────────→
                       │              Volatility
        Range          │     Breakout
                       │
                       ↓

実際には、

X軸 = ER / ADX / Slope → トレンド性
Y軸 = BB Width / ATR% → ボラティリティ

として分類すると、

低トレンド性 × 低ボラ → 静かなレンジ
低トレンド性 × 高ボラ → 荒いレンジ
高トレンド性 × 低ボラ → ゆっくりしたトレンド
高トレンド性 × 高ボラ → 強トレンド / ブレイク

という4レジームにできます。

そして、まこさんのBOTなら重要なのは**「現在がレンジか」だけではなく、「レンジから別レジームへ移行し始めたか」**です。

つまり、

Static Regime判定 + Regime Transition判定

の2段構成がかなり重要です。

例えば
ER低 + ADX低 + BB Width低 → レンジ
↓
ER上昇 + ADX上昇 + BB Width急拡大
↓
「レンジ終了リスク上昇」

と判定できます。

この方向なら、単純な「レンジ/トレンド」の2分類より、Time ExitやSLになる前に「このエントリーはもうレンジ逆張りとして不利になった」と検出する仕組みに繋げられます。

まこさんのBOT向けなら、次は **
「BTC 5分足で実際に使うレジーム判定を、候補10個→有力3〜5個に絞る」**のが一番有益です。
**
①レンジ判定重視 / 
②ブレイク予兆重視 / 
③両方**のどれを優先しますか？
```

## 9-2｜Gemini の回答（逐語・1文字も変えていません）

```
BTC先物取引で市場レジーム（トレンド相場・レンジ相場・高ボラティリティ等）を判定するには、ADX（平均方向性指数）やボリンジャーバンドのバンド幅（Band Width / %B）、およびHMM（隠れマルコフモデル）などの定量モデルを組み合わせる手法が効果的です。トレンドの強さを測る手法ADX（Average Directional Index）:トレンドの「方向」ではなく「強さ」を測定します。ADX > 25 の場合は強いトレンド相場と判定し、順張り（トレンドフォロー）戦略を選択します。ADX < 20〜25 の場合はレンジ相場（方向感なし）と判定し、逆張りやレンジ内での網掛け（グリッド）戦略に切り替えます。ボラティリティの変化を捉える手法ボリンジャーバンド幅（Band Width）:バンドが歴史的に収縮している状態（スクイーズ）は、低ボラティリティ・次なる大変動への移行期（レジーム転換前夜）と判定します。バンドが急拡大する局面（エクスパンション）は、ボラティリティ急上昇・トレンド発生レジームへの移行とみなします。高度な数学的・機械学習モデル隠れマルコフモデル（HMM: Hidden Markov Model）:Pythonなどのクオンツ取引でよく使われ、価格のリターンやボラティリティの時系列データから「低ボラレンジ」「高ボラ暴落」「強気トレンド」といった目に見えない隠れ状態（レジーム）を確率的に分類します。レジームの切り替わりを検知して、自動売買ボットのON/OFFを切り替えるために活用されます。もしよろしければ、次について教えてください：お使いの時間足（スキャルピング、デイトレード、スイングなど）使用しているプログラミング環境やツール（Python、TradingViewなど）適したインジケーターや具体的な実装アプローチをさらに詳しく提案できます。
```

---

# §10 突き合わせ｜私が調べたものと、別の AI の回答

## 10-1｜一致したもの（5件）

| 何 | 別の AI | 私が本文から取った逐語 |
|---|---|---|
| ADX は強さを測り、向きは DI が測る | Gemini「トレンドの『方向』ではなく『強さ』を測定します」 | StockCharts の逐語 "measures the ***strength*** of the trend (regardless of direction)" |
| ADX の 25／20 という区切り | Gemini「ADX > 25」「ADX < 20〜25」 | StockCharts の逐語 "Wilder suggests that a strong trend is present when ADX is above 25 and no trend is present when ADX is below 20." |
| ADX は遅れる | ChatGPT「固定閾値だけでは遅れる」 | StockCharts の逐語 "ADX also has a fair amount of lag because of all the smoothing techniques." |
| Kaufman 効率比＝どれだけ一直線に進んだか | ChatGPT「価格がどれだけ一直線に進んでいるか」 | StockCharts の逐語 "ER = Change/Volatility"（分子＝n本前との差／分母＝1本ごとの差の合計） |
| BB の幅が縮んだあと大きく動く | Gemini「スクイーズ」「エクスパンション」 | StockCharts「Bollinger Band Squeeze」（★私は要約のみ・本文は未読） |

**＝別の AI が言っていることのうち、私が本文で裏を取れたのは この5件です。**

## 10-2｜★別の AI にだけ在って、私が調べていなかったもの（5件）

| # | 何 | 中身 | 私の受け止め |
|---|---|---|---|
| 1 | **回帰直線の傾き（Linear Regression Slope）** | 一定期間の値段に直線を当てはめ、その傾きで 上げ／横ばい／下げ を決める。**ATR で割ると、BTC の値段の水準に左右されにくくなる** | **向きを測る指標として、私の一覧に無かったものです。**うちの決まり H6（値段の絶対額に依存しない）に、ATR で割る形がそのまま合います |
| 2 | **BB 幅の「変化」** | 幅そのものではなく、幅が広がり始めたかを見る | **私は幅の水準しか見ていませんでした。**変化を見る形は、レンジが終わる合図になります |
| 3 | **Donchian Channel** | n本の最高値・最安値の帯。抜けたかどうかでブレイクを判定 | うちの材料に「N本高値安値」は在ります。ブレイクの判定として使う発想が無かったです |
| 4 | **EMA の傾き・乖離** | 向きと強さの両方 | うちの材料に在ります（`close vs SMA%` ほか）。**ただし「移動平均そのものの向き」の部品が無い**＝これは既に「あとで直すこと」の27番に載っています |
| 5 | **2軸で4つに分ける** | 横軸＝トレンド性（効率比・ADX・傾き）／縦軸＝ばらつき（BB 幅・ATR%）。**静かなレンジ／荒いレンジ／ゆっくりしたトレンド／強トレンド** の4つ | **私は「強さ × 向き」で3つに分ける形を書きました。**別の AI は「強さ × ばらつき」で4つに分けています。**★2つは別のもので、どちらも要ります**（下の 10-4） |

## 10-3｜★いちばん大きい示唆＝「いまどれか」と「変わり始めたか」は別の判定

**ChatGPT の逐語**

```
Static Regime判定 + Regime Transition判定
の2段構成がかなり重要です。
```
```
Time ExitやSLになる前に「このエントリーはもうレンジ逆張りとして不利になった」と検出する仕組みに繋げられます。
```

**★これは、うちのマイルストーン②だけの話ではありません。④（出口）に直接つながります。**

- ②＝いまレンジか（建てる前のふるい）。
- ④＝建てたあとに、レンジが終わり始めたか（降りる合図）。

**うちの E38 の出口には、いま「時間切れ」と「損切り」が在ります。**
**この2つの判定は、「時間切れや損切りになる前に降りる枝」を作れるという話です。**

**★私が調べた範囲にも、同じ形が在りました**＝変化点の検出（§3-D）です。ただし私は「条件の形にできない」と書いて、うちには向かないと判断していました。**別の AI の言い方（指標が3つとも同じ向きに動き始めたら移り変わり）なら、条件の束として組み立てられます。**

## 10-4｜★3つに分けるのと、4つに分けるのは、別の話です

**私が §2 に書いたもの（強さ × 向き）**＝上げトレンド／下げトレンド／レンジ。
**別の AI が書いたもの（トレンド性 × ばらつき）**＝静かなレンジ／荒いレンジ／ゆっくりしたトレンド／強トレンド。

**この2つは、掛け合わせられます。**

| | ばらつきが小さい | ばらつきが大きい |
|---|---|---|
| **上げトレンド** | ゆっくりした上げ | 強い上げ |
| **下げトレンド** | ゆっくりした下げ | 強い下げ |
| **レンジ** | 静かなレンジ | 荒いレンジ |

**★E38（レンジのスキャル）にとって、この違いは効きます。**静かなレンジと荒いレンジでは、利確の幅も損切りの幅も変わるはずです。**ただし、これは私の推測です。実データで確かめていません。**

## 10-5｜★注意（根拠として弱いところ）

| # | 何 | なぜ注意が要るか |
|---|---|---|
| 1 | **ChatGPT の表の星の数（★の個数）** | **出どころがありません。**実データで測った値でもありません。**engine_tuner が net で決めます。私が星の数で候補を絞りません**（恒久の決まり42番＝先に候補を限定しない） |
| 2 | **「候補10個 → 有力3〜5個に絞る」という提案** | **CC が先に絞るのは、まこさんが禁じた形です**（違反の記録 #14＝私が先に候補を限定した件）。**絞るなら、実データで勝ち負けを分けた順に絞ります**（マイルストーンの「★②③④に共通の手順」のフェーズ2） |
| 3 | **Gemini の HMM の説明** | **未来参照（smoothed か filtered か）に1文字も触れていません。**うちの H2 では、ここを間違えると成績が嘘になります（§5） |
| 4 | **数字（ADX 25・20 など）** | 目安であって、BTC の5分足での正解ではありません。**engine_tuner が範囲から探します** |

## 10-6｜別の AI からの質問への答え

| 誰 | 質問 | 私の答え |
|---|---|---|
| ChatGPT | ①レンジ判定重視／②ブレイク予兆重視／③両方 のどれを優先するか | **③両方です。**ただし作る順番は ① → ② です。①はマイルストーン②（建てる前のふるい）、②はマイルストーン④（建てたあとの降りる枝）に入ります |
| Gemini | 使っている時間足 | **5分足が標準です**（要件定義書 H7）。材料としては1分足から1日足まで持ちます（要件 R15） |
| Gemini | 使っている環境 | **Python です。**バックテストの採点は `score.py`（改造禁止）で行います |

**★この答えは私が決めました**（恒久の決まり49番＝技術のやり方は CC が決める）。まこさんに選ばせません。

---

# §11 ★場面ごとの「使う法則」の一覧（第1版・2026-08-20・44回目）

**何のための一覧か**＝M2 のフローの工程表に足す「法則の欄」を埋める元。まこさん GO（2026-08-20・逐語「まずは上記リスト作成をしてみて」）。
**使い方**＝フローの工程・組み立ての決まりは、必ずこの一覧のどれか（または新しく足した行）を根拠にする。**この一覧に無い工程は書けない＝当てずっぽうが混ざれない。**

**★この一覧に名前が出ていない指標が「レジーム判定に向かない」という意味ではない**（まこさんの問い 2026-08-20 への答え）。

1. この一覧は「文献と実装が、レジーム判定用として名指ししたもの」を集めた。**名指しされなかった指標が向かない、という証明ではない。**
2. 名指しされた指標は**代表例**。法則が本当に言っているのは「レジーム判定に使えるのは、**強さ・向き・ばらつき・構造の実績**のどれかを測る指標」（C1・R1・R10）ということ。materials.md の指標は全部この物差しで仕分けできる。同じ物差しを測る別の指標（例＝VHF は ER・CHOP と同型／Keltner の幅は BB 幅と同型／EMA の傾きは SMA の傾きと同型）も、同じ法則の下で候補になる。
3. **同じ指標でも、パラメータと使い方を変えれば両方に使える**（C8）。RSI は期間14なら入口の過熱、期間100〜200ならレジーム判定。BB は幅で場面・タッチで入口。＝向き不向きは「指標そのもの」でなく「役割 × パラメータ × 閾値の意味」で決まる。
4. **最終の選抜は engine_tuner がやる。**M2-3 で materials.md の指標を「場面を分ける力」の実データの順位で並べ、採否は net で決める。**文献に出てこない指標も、順位づけの対象から外さない**（恒久の決まり42番＝CC が先に候補を限定しない）。
5. 逆に、仕分けで消えるものは在る＝向きを持たない部品115件（型の表の bans）は「向き」の物差しには使えない。

**出どころの印（5つ）**

| 印 | 意味 |
|---|---|
| 【本文】 | 記事・論文の本文を開いて原文を写した |
| 【要約】 | 検索結果の要約のみ。**単独では設計の根拠に使わない** |
| 【別AI】 | まこさんが貼った ChatGPT・Gemini の回答。**裏取りするまで根拠に使わない** |
| 【実装】 | このプロジェクトで実際に動いている（または archive の）コード |
| 【正本】 | このプロジェクトの正本文書（まこさん承認済み・または既存 KB） |

**調べ方と打ち切り（宣言どおり）**

- 入口5つ＝①社内の正本（indicator_combination_kb §7・technical KB・step1_regime_design・この KB）②社内の実装（RG-v5/v6・archive/regime_rule_classifier・e36 の Lee-Mykland・ml_regime_classifier）③教科書系サイトの本文（StockCharts・TradingView・LuxAlgo・QuantMonitor・mathandmarkets）④学術（arXiv 2402.05272 ほか）⑤別 AI の回答との突き合わせ（§9・§10）。
- 打ち切りの基準＝**新しい調べ方をしても、新しい法則の型が2回 連続で出なくなったら打ち切り。**
- 実績＝2026-08-20 の Web の3ラウンド目（本文の取得）と4ラウンド目（下げ・暗号資産の検索）で、**新しい法則の型が0件**＝基準を満たして打ち切り。**★「この世のすべて」の証明ではない。**穴は §11-7 に書いた。

## 11-1 場面に共通の法則（組み立ての作法・10件）

| # | 法則 | 中身 | 出どころ |
|---|---|---|---|
| C1 | **強さと向きは別の物差し** | トレンドか否か（強さ）と、上か下か（向き）は別の指標。3つに分けるには2本 要る | 【本文】StockCharts ADX（この KB §2）＝ "measures the strength of the trend (regardless of direction)" |
| C2 | **同じ問いに答える指標を重ねない** | 同系統2本は「雑音が2倍」。強さの指標（CHOP・ER・VHF）は中身がほぼ同じ | 【本文】excavo・LiteFinance（`indicator_combination_kb.md` 法則1・2）＋この KB §4-2 |
| C3 | **実データで動きがほぼ同じ指標は、片方を外す** | 「トレンド系」「オシレーター系」という系統の札だけで重複を判定すると粗い。同じ系統でも見ているものが違うことがあり（ADX は強さ・DI差は向き）、系統が違っても動きがほぼ同じことがある。だから実際の値動きデータで、2つの指標の動きがどれだけ重なるかを計算し、ほぼ同じ動きなら片方を外す。★計算に使うのは値決め窓のデータだけ（採点窓を使うと未来参照になる） | 【本文】apxml（同 法則6） |
| C4 | **多時間軸＝上位足が許可・下位足が執行** | "Entries come from below; permission comes from above."。時間足の比は4〜6倍 | 【本文】LuxAlgo HTF（`engine_tuner_milestones2.md` §3.5（6））＋NinjaTrader（同 KB 法則4）＋RG-3 |
| C5 | **場面の判定は「いま建てろ」の合図ではない。入口を通すか止めるかの、ふるい** | 場面の判定がやるのは「いまはレンジだから、レンジ用の入口を動かしてよい」「いまは下げトレンドだから、レンジ用の入口を止める」という許可と停止だけ。建てるタイミングは、ふるいを通ったあとに、入口の条件が別に決める。出どころの逐語＝ "Predicting the next price with the MMI would work as well as flipping a coin."（MMI を作った人 自身が「これで次の値段は当てられない」と書いている） | 【本文】MMI・HMM（この KB §4-3） |
| C6 | **判定を安定させる仕組みは2つ・別物** | ①何本 続いたら成立 ②入る線と出る線を別にする（状態を保つ） | 【本文】mathandmarkets・traderssecondbrain（この KB §4-6） |
| C7 | **「上げ」と判定した状態が何時間 続く作りにするかは、engine_tuner が探す値にする** | 判定が続く長さ（数時間か・丸1日か）は、法則では決まらない。切替の慣性を強くすれば長く、弱くすれば短くなる。E38 は数分で回すスキャルなので、判定が丸1日 変わらないと粗すぎ、5分ごとに切り替わると使えない。**過去に14版を凍結した理由の3つ目（ラベルは16〜28時間 続くのに取引は中央値15分）は、この長さを調整する仕組みが無かったこと。**だから長さを探す値にする。出どころの逐語＝ "As λ increases, state transitions become less frequent."（罰を強くするほど切替が減る＝長さをつまみ1つで調整できる） | 【本文】arXiv 2402.05272・Label Horizon Paradox（この KB §4-4） |
| C8 | **パラメータは、場面の判定では長め・入口では短め** | 場面の判定にオシレーターを使うなら期間を大きく（RSI 100〜200 の例） | 【要約】Better System Trader（milestones2 §3.5（6）の5番）＋【別AI】Gemini の4要素の表 |
| C9 | **数値は法則で決めない＝範囲で探す** | 文献の数字（ADX 25・20 ほか）は目安。うちの正解は engine_tuner が範囲から探す | 【正本】恒久の決まり47番・L-267・この KB の各所の注意書き |
| C10 | **未来のデータを使ってしまう作り方が5つある。全部 避ける** | ①閾値を「全期間の分位」で決めると、未来のデータが閾値に混ざる → その時点までの過去だけで分位を出す。②山と谷は、確定に数本あとの値動きが要る → 確定するまで待ってから使う（実例の「j+2 確定」がこの形）。③HMM という統計モデルには、全期間を見てから過去の状態を出し直す使い方（smoothed）がある＝未来参照 → その時点までのデータだけで出す使い方（filtered）にする。④データをかたまりに分ける手法で、全期間を使って分け方を決めると採点窓の情報が入る → 分け方は値決め窓だけで決める。⑤走らせる途中でモデルを学習し直すと、それ以降のデータが混ざる → 途中で学習し直さない | 【本文】この KB §5 |

## 11-2 レンジの法則（10件・E38 の主戦場）

| # | 法則 | 中身 | 出どころ | engine_tuner で書けるか（2026-08-19 実測） |
|---|---|---|---|---|
| R1 | **レンジかどうかは、「実際に価格が何回も跳ね返された線が上下に在るか」で決める** | ADX などの「横ばい度の統計」で決めるのではない。実際に価格が跳ね返された実績（タッチ）が最低3回ある線だけを、本物のサポート・レジスタンスと認める。その線が close の上下に揃っていたらレンジ。正本の逐語＝「統計量（横ばい度・ADX 等）ではなく、機能しているレベルの実績で認識する」 | 【正本】RG-1（`range_scalping_kb.md` §2・`indicator_combination_kb.md` §7） | ✕ 帯を作る形が無い（milestones2 §3.4） |
| R2 | 補助（強さ・幅・出来高）は違う系統から | RG-2 | 【正本】同上 | ○ |
| R3 | **上位足でゾーン・下位足（5分）で執行** | RG-3＝多時間軸の黄金律 | 【正本】同上 | △ RG-v5 の帯を読む列だけ在る |
| R4 | **何本 続いているかを条件に入れる** | RG-4＝1本だけ成立してもレンジと言わない | 【正本】同上 | ○ `streak` で書ける |
| R5 | **トレンドの強さを測る指標が「弱い」と出ていたら、レンジ寄り** | 具体的には4つ。①ADX が 20 未満（トレンドなし）②CHOP が 61.8 超（CHOP＝値動きのゴチャゴチャ度。1本ずつの値動きの合計 ÷ 全体で進んだ幅。高いほど行ったり来たり＝横ばい）③ER が低い（ER＝まっすぐ進んだ距離 ÷ 実際に歩いた距離。低いほど行ったり来たり）④MMI が高い（MMI＝値動きがランダムに近いかの割合。高いほどレンジ寄り）。★数字は目安＝範囲で探す（C9） | 【本文】この KB §3-A | ○ 材料に在る |
| R6 | BB 幅の縮小（スクイーズ）＝低ボラ・レンジ寄り | 幅が過去より狭い状態。抜けの向きは教えない | 【要約】StockCharts Squeeze（この KB A-7） | ○ BB幅は在る |
| R7 | **帯の幅がコストを超えること** | 往復の手数料を超える値動きが取れる幅（十分性）。実例の「幅≥0.4%」の根拠 | 【正本】SCALP_FLOOR（`e38_logic_parts.py:23`）・十分性の考え方 | ○ 幅の列は在る |
| R8 | **非トレンド（上げ・下げの否定）を含める** | レンジ＝帯あり ∩ 帯内 ∩ 非 uptrend | 【実装】RG-v5 `range_ok_rg5`（`e37_range_scalp.py:1615`） | ✕ 否定（not）が無い |
| R9 | **測るもの3つ** | 判定した時間の割合／その中の玉の成績／実はトレンドだった割合（E37 の失敗の本体） | 【正本】`indicator_combination_kb.md` §7 | —（測る側） |
| R10 | **静かなレンジと荒いレンジを分ける** | トレンド性 × ばらつき の2軸で4分類 | 【本文】QuantMonitor（milestones2 §3.5（6））＋【別AI】ChatGPT の4分類（この KB §10-4） | 未確認（ATR% の自分の平均との比較＝M2-2 で数える） |

## 11-3 上げの法則（10件）

| # | 法則 | 中身 | 出どころ |
|---|---|---|---|
| U1 | **高値切り上げ ∩ 安値切り上げ（ダウ理論）** | Higher Highs + Higher Lows ＝上昇トレンドの定義 | 【正本】`technical_analysis_knowledge_base.md`:926＋この KB A-9【要約】 |
| U2 | **強い ∩ +DI > -DI** | ADX≥25（強い）と向きの掛け合わせ | 【本文】StockCharts（この KB §2・A-1） |
| U3 | 終値が長期移動平均の上・MA の傾きが上 | MA200 の上＝強気の地合い。EMA50>EMA200 の2段確認 | 【要約】quantifiedstrategies・arXiv 2603.15848（本文はボット遮断で開けず） |
| U4 | **直近N本の終値に直線を1本 当てはめ、その傾きがプラスなら上げ** | 「回帰直線」＝直近N本の終値に一番よく当てはまる直線。傾きプラス＝上げ／マイナス＝下げ／ほぼ0＝横ばい。★傾きの値をそのまま使うと BTC の値段の水準（6万ドルか10万ドルか）で大きさが変わるので、ATR か % で割って、値段の水準に左右されない数字にする（＝「正規化」。うちの決まり H6＝ドルの絶対値を使わない、にそのまま合う）。逐語＝ "often normalized by ATR or expressed as a percentage so thresholds transfer across symbols and timeframes" | 【本文】LuxAlgo Linear Regression（2026-08-20 に本文を開いた） |
| U5 | Supertrend の札が「上げ」を出しているあいだは上げ | Supertrend は「上げか下げか」の札を直接 出す指標。作り＝(高値+安値)÷2 から ATR の倍数だけ離れた線を引き、終値がその線を反対側に抜けたら、札が「上げ」⇔「下げ」に切り替わる | 【要約】TradingView（この KB A-8） |
| U6 | **終値が「直近N本の最高値の線」を上に抜けたら、上げの始まりの合図** | Donchian チャネル＝直近N本（既定20本）の最高値の線と最安値の線。終値が最高値の線を上に抜けたら上げの合図。★注意＝本文に「明確なトレンドの中で一番よく効く」と書いてある＝レンジの中ではダマシの抜けが増える。逐語＝ "Upper Channel = 20 Day High"・"Donchian Channels primarily work best within a clearly defined trend." | 【本文】TradingView DC（2026-08-20 に本文を開いた） |
| U7 | **前回高値の更新＝継続** | トレンド継続の確認（実例の「前回高値+0.3%超えで再成立」の骨格） | 【正本】ダウ理論（technical KB）＋まこさんの実例 |
| U8 | **解除＝半値戻し** | 上昇の 38.2〜61.8%（50% 含む）は反転高確率ゾーン | 【正本】`technical_analysis_knowledge_base.md`:672-677 |
| U9 | **解除＝高値と安値の並びが壊れたら、上げを疑う** | 「構造」＝高値と安値の並び（上げなら、高値も安値も切り上がっている並び）。「破断」＝その並びが壊れること＝**終値が直近の安値を割ったら、上げの構造が壊れたと見る。**実例の「close < 直近2本の確定15分安値」がまさにこれ。外の資料での呼び名＝CHoCH（並びの性格が変わった＝反転の可能性）・BoS（並びどおりに抜けた＝継続） | 【本文】LuxAlgo Market Regimes（2026-08-20 に本文を開いた） |
| U10 | **一度「上げ」と判定したら、解除の条件が成立するまで「上げ」のままにする（スイッチの仕組み）** | ①入る条件（複数の経路のどれか1つが成立したらスイッチが入る）②入っているあいだは毎バー測り直さず「上げ」を保つ ③切る条件（半値戻し 等）が成立したらスイッチが切れる。**「入る線と出る線を別にする」＝入る基準と出る基準をずらす**（例＝0.6 を超えたら入り、0.4 を割るまで出ない）＝小さな揺れで判定がパタパタ変わるのを防ぐ。まこさんの実例の②（成立4経路・継続・解除3条件）と、うちの RG-v5 がこの形 | 【実装】RG-v5 `_uptrend_state_5m`＋【本文】hysteresis（この KB §4-6） |

## 11-4 下げの法則（9件）

| # | 法則 | 中身 | 出どころ |
|---|---|---|---|
| D1 | **安値切り下げ ∩ 高値切り下げ**（U1 の鏡像） | Lower Lows + Lower Highs | 【正本】`technical_analysis_knowledge_base.md`:926 |
| D2 | **強い ∩ -DI > +DI** | "A sell signal triggers when -DI crosses above +DI. The high on the day of the sell signal becomes the initial stop-loss."・前提＝ADX>25 | 【本文】StockCharts（この KB A-1） |
| D3 | **終値が移動平均の下（複数本）・MA の傾きが下** | 終値が SMA20・SMA50・EMA200 の全部より下→下げ／BB 中央線の傾き<-10%→下げ／基準線より-0.5%下→下げ | 【実装】`archive/regime_rule_classifier.py`:133-250 |
| D4 | **上位足の一致に重みを付ける** | 1時間足と4時間足の向きの一致＝重み1.5（6指標中 最大） | 【実装】同 :61-66 |
| D5 | **「下に動いた分だけ」のばらつきで測る** | ふつうのばらつき（ATR・標準偏差）は上下の動きを混ぜて測る。それを「下に動いた分だけ」で測り直す物差しが downside deviation（下方偏差）。**下げ相場の検出には、上下混ぜたばらつきより、下だけのばらつきの方が向く**という法則。Sortino も同じ発想（利益 ÷ 下だけのばらつき）。逐語＝ "EWM downside deviation (DD) with a halflife of 10 trading days..." | 【本文】arXiv 2402.05272 §3.4.1（この KB §2.7.2） |
| D6 | 直近N本の終値に当てはめた直線の傾きがマイナスなら下げ | U4 の向きを逆にしただけ（「鏡像」＝上げの法則の上下を入れ替えたもの、の意味）。ATR か % で割る正規化も同じ | 【本文】LuxAlgo Linear Regression |
| D7 | 終値が「直近N本の最安値の線」を下に抜けたら、下げの始まりの合図 | U6 の向きを逆にしただけ。レンジの中ではダマシが増える注意も同じ | 【本文】TradingView DC |
| D8 | **連続2回 同じ判定で切替（慣性）** | 2時間相当。1回の判定で切り替えない | 【正本】`step1_regime_design.md` §2.1（まこさん確定） |
| D9 | **3つに分けたかたまりに「上昇・下落・レンジ」の名前を付ける方法** | 判定で3つのかたまりに分けたあと、どれが上昇でどれが下落かを決める手順＝各かたまりの中の DI差（+DI − -DI・1時間足）の中央値を出し、**一番大きいかたまり＝上昇／一番小さい＝下落／残り＝レンジ**と名付ける。名付けが妥当かの確かめ方＝レンジと名付けたかたまりの ADX 平均が、他の2つより低いこと | 【正本】同 §2.7（まこさん確定） |

**★最後の検索（下げ・暗号資産）で新しい型は出なかった**＝下げは「上げの鏡像＋D5（下向きのばらつき）」で、下げ特有の別系統は見つからなかった。

## 11-5 スパイクの法則（6件）

| # | 法則 | 中身 | 出どころ |
|---|---|---|---|
| S1 | **「いまの1本の値動きが、ふだんの揺れと比べて統計的にありえないほど大きいか」を測る検定（Lee-Mykland 2008）** | 分子＝いまの1本の値動き（終値の変化率）。分母＝ふだんの揺れの大きさ（直近K本から出す。★計算には bipower という方法＝隣り合う2本の値動きの積を使う。こうすると、スパイク自身が「ふだんの揺れ」の計算を汚さない）。分子÷分母が閾値を超えたらスパイク。**★閾値は「K本と、誤検出をどこまで許すか（α）」から数式で先に決める＝データを見て後から選ばない＝過剰適合しない。**K=270（5分足で約1日）で実装済み・E36 の急騰 Exit で実際に動いている | 【実装】`e36_short_oscillation.py`:372-382・:1232。`score.py`:64 に `SPIKE_SL` 登録済み |
| S2 | **ローソクの大きさ vs ATR の倍数** | 1本の値幅（高値-安値）を ATR の倍数と比べる。bull/bear は close と open の大小で分ける | 【要約】TradingView Auto-ATR Volatility Spike（本文は未読） |
| S3 | **出来高スパイク＋価格のブレイクの組み合わせ** | "Absolute Volume: 200% of 20-day average"・"Relative Volume: 150% of the previous hour"・"Volume spike + price breakout: Confirm high-probability signals" | 【本文】LuxAlgo Volume Spikes（2026-08-20 に本文を開いた）。**★うちは需給・出来高の材料が0件＝いまは書けない** |
| S4 | **一定幅を超えた本数を数える** | 直近24時間で、1時間足のリターンが±1%を超えた本数 | 【実装】`ml_regime_classifier.py`:259-267 |
| S5 | ダマシ＝ニュース由来の出来高は短命 | "News-Driven Volume: Can trigger short-lived, unstable movements" | 【本文】LuxAlgo Volume Spikes |
| S6 | BB 幅の急拡大（エクスパンション） | 幅の「変化」を見る（水準でなく） | 【要約】StockCharts＋【別AI】ChatGPT・Gemini（裏取りは幅の変化の部品を数えてから） |

## 11-6 変わり始め（transition）の法則（5件・★M4＝出口にもつながる）

| # | 法則 | 中身 | 出どころ |
|---|---|---|---|
| T1 | **CHoCH／BoS** | 構造の性格の変化＝反転の可能性／構造の破断＝継続 | 【本文】LuxAlgo Market Regimes |
| T2 | **複数の指標が同じ向きに動き始めたら移り変わり** | 「ER上昇 ＋ ADX上昇 ＋ BB Width急拡大 → レンジ終了リスク上昇」 | 【別AI】ChatGPT（この KB §10-3。**裏取りまだ＝根拠に使う前に本文を探す**） |
| T3 | **多時間軸が早期の兆候を出す** | "Multi‑timeframe analysis can reveal early signs of regime changes" | 【本文】LuxAlgo Market Regimes |
| T4 | 「いまどれか」と「変わり始めたか」は別の判定 | Static Regime 判定 + Regime Transition 判定の2段 | 【別AI】ChatGPT（この KB §10-3） |
| T5 | 変化点の検出の系統 | 分布が変わった時刻を検定で出す。条件の形にするなら T2 の形に落とす | 【要約】この KB §3-D |

## 11-7 未収載・穴（正直に書く）

| # | 穴 | 中身 |
|---|---|---|
| 1 | **出来高・需給の材料が0件** | S3（出来高スパイク）が書けない。既存の「あとで直すこと」26番と同じ |
| 2 | **「窓×幅の対を2本 置く」構成** | 実例の成立(c)(d)（90分で+1.0%／6hで+2.0%）。正本にも Web にも法則として見つからなかった＝まこさんの設計。速い立ち上がりと遅い立ち上がりの2経路 |
| 3 | quantifiedstrategies の本文 | ボットの遮断で開けず。U3（MA200）は【要約】のまま |
| 4 | Directional Change・ボラ構造（短期÷長期） | 本文が未読のまま（この KB §6 の既存の穴） |
| 5 | 暗号資産特有（funding・清算の連鎖） | 材料が無いので調べていない |

## 11-8 出どころ（2026-08-20 に新しく開いたもの）

- 【本文】[LuxAlgo・Linear Regression（Library）](https://www.luxalgo.com/library/concept/linear-regression/)
- 【本文】[TradingView・Donchian Channels (DC)](https://www.tradingview.com/support/solutions/43000502253-donchian-channels-dc/)
- 【本文】[LuxAlgo・Volume Spikes: Timing Trades with Precision](https://www.luxalgo.com/blog/volume-spikes-timing-trades-with-precision/)
- 【本文】[LuxAlgo・Market Regimes Explained](https://www.luxalgo.com/blog/market-regimes-explained-build-winning-trading-strategies/)
- 【要約】[TradingView・Auto-ATR Volatility Spike & Trend Tracker](https://www.tradingview.com/script/KTsZMbtk-Auto-ATR-Volatility-Spike-Trend-Tracker-BigBeluga/)／[QuantifiedStrategies・200 Day Moving Average](https://quantifiedstrategies.com/200-day-moving-average)／[StockCharts・Donchian Trading Guidelines](https://chartschool.stockcharts.com/table-of-contents/overview/donchian-trading-guidelines)
