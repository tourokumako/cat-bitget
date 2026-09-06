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
- **★ここが重要です。**書いた本人が「これで次の値段は当てられない」と書いています。**MMI は建てる合図ではなく、場面の入ってはいけない場面を除く条件です。**

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

## 4-3｜レジーム判定は「建てる合図」ではなく「入ってはいけない場面を除く仕組み」

MMI を作った人の逐語（上の A-4）＝ "Predicting the next price with the MMI would work as well as flipping a coin."
HMM の使い方の逐語（上の B-1）＝ "Long entry trades will only be carried out in regime 0"。

**＝レジーム判定は、建てる合図そのものではありません。「この場面では建てる／建てない」を決める入ってはいけない場面を除く条件です。**
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

## 4-5｜場面の判定が必ず効くとは限らない

検索結果の要約に、次の指摘が在りました（**本文は未読**）。

- トレンド追随の戦略に場面の判定で入口を絞ると、その判定が「本当の状態」ではなく「値動きの外れ値」を拾ってしまうことがある。
- 平均回帰の戦略の方が、場面の判定と相性が良い。

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
| 4 | 場面の判定がトレンド追随で効きにくいという指摘（SSRN 6621520）の中身 | 本文を開いていない |
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

- ②＝いまレンジか（建てる前に、入ってはいけない場面を除く判定）。
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
| ChatGPT | ①レンジ判定重視／②ブレイク予兆重視／③両方 のどれを優先するか | **③両方です。**ただし作る順番は ① → ② です。①はマイルストーン②（建てる前に、入ってはいけない場面を除く判定）、②はマイルストーン④（建てたあとの降りる枝）に入ります |
| Gemini | 使っている時間足 | **5分足が標準です**（要件定義書 H7）。材料としては1分足から1日足まで持ちます（要件 R15） |
| Gemini | 使っている環境 | **Python です。**バックテストの採点は `score.py`（改造禁止）で行います |

**★この答えは私が決めました**（恒久の決まり49番＝技術のやり方は CC が決める）。まこさんに選ばせません。

---

<!-- KB_LAWS_START hash=c5f8ef9061079c78 gen_regime_kb.py が自動生成＝手で書き換えない -->
# §11 場面ごとの相場の法則の一覧（★この節は機械が作ります・手で書き換えない）

**何のための一覧か**＝M2 のフローの工程表に足す「相場の法則の欄」を作る元。まこさん GO（2026-08-20・逐語「まずは上記リスト作成をしてみて」）。

**使い方**＝フローの工程・読み込ませる法則は、必ずこの一覧のどれか（または新しく足した行）を根拠にする。この一覧に無い工程は書けない＝当てずっぽうが混ざれない。

**元データ**＝`.claude/ratchet/regime_laws.json` ／ **作り方**＝`python3 .claude/tools/gen_regime_kb.py --write（書く） ／ --verify（手で書き換えられていないかの検出）`

**整理した日**＝2026-08-29｜**整理の形**＝1件を2段に分ける。上＝一覧の表（相場の法則を1文・60字まで）／下＝1件ずつの説明（長さの制限なし）。★相場の法則の中身は1文字も消さず、置き場所を変えただけ。

## 11-0 何件あるか（機械が数えます）

| 場面 | 件数 | 相場の法則の番号 |
|---|---|---|
| 場面に共通の相場の法則（組み立ての作法） | 10 | C1・C2・C3・C4・C5・C6・C7・C8・C9・C10 |
| レンジの相場の法則 | 11 | R1・R2・R3・R4・R5・R6・R7・R8・R9・R10・R11 |
| 上げの相場の法則 | 10 | U1・U2・U3・U4・U5・U6・U7・U8・U9・U10 |
| 下げの相場の法則 | 9 | D1・D2・D3・D4・D5・D6・D7・D8・D9 |
| スパイクの相場の法則 | 6 | S1・S2・S3・S4・S5・S6 |
| 変わり始め（transition）の相場の法則 | 5 | T1・T2・T3・T4・T5 |
| **合計** | **51** | |

**出どころの印（5つ）**

| 印 | 意味 |
|---|---|
| 【本文】 | 記事・論文の本文を開いて原文を写した |
| 【要約】 | 検索結果の要約のみ。単独では設計の根拠に使わない |
| 【別AI】 | まこさんが貼った ChatGPT・Gemini の回答。裏取りするまで根拠に使わない |
| 【実装】 | このプロジェクトで実際に動いている（または archive の）コード |
| 【正本】 | このプロジェクトの正本文書（まこさん承認済み・または既存 KB） |

**★この一覧に名前が出ていない指標が「レジーム判定に向かない」という意味ではありません**

1. この一覧は「文献と実装が、レジーム判定用として名指ししたもの」を集めた。名指しされなかった指標が向かない、という証明ではない。
2. 名指しされた指標は代表例。相場の法則が本当に言っているのは「レジーム判定に使えるのは、強さ・向き・ばらつき・構造の実績 のどれかを測る指標」（C1・R1・R10）ということ。materials.md の指標は全部この物差しで仕分けできる。同じ物差しを測る別の指標（例＝VHF は ER・CHOP と同型／Keltner の幅は BB 幅と同型／EMA の傾きは SMA の傾きと同型）も、同じ相場の法則の下で候補になる。
3. 同じ指標でも、パラメータと使い方を変えれば両方に使える（C8）。RSI は期間14なら入口の過熱、期間100〜200ならレジーム判定。BB は幅で場面・タッチで入口。＝向き不向きは「指標そのもの」でなく「役割 × パラメータ × 閾値の意味」で決まる。
4. 最終の選抜は engine_tuner がやる。materials.md の指標を「場面を分ける力」の実データの順位で並べ、採否は net で決める。文献に出てこない指標も、順位づけの対象から外さない（恒久の決まり42番＝CC が先に候補を限定しない）。
<!-- BANS_COUNT_START gen_materials.py --write が型の表から書き出す＝手で書き換えない -->
5. 逆に、仕分けで消えるものは在る＝向きを持たない部品**130件**（型の表の bans）は「向き」の物差しには使えない。内訳は `direction_stateful`（状態量・ボラ量）**124件** ＋ `direction_note`（カタログ注記）**6件**、重なり **0件**。
<!-- BANS_COUNT_END -->

> **★この行は機械が書きます（2026-09-05・監査 cp21 の C1）。**手で書き換えないでください。`gen_materials.py --verify` が改変と陳腐化を検出します。
> **なぜ機械にしたか**＝2026-09-05 に、私（CC）が手で「126件」と書いた**15分後**に型の表を作り直したところ、実物は **148件** になっていました。**手で書いた数字は、次の再生成で必ず古くなります。**（直す前の「115件」も同じ理由で古いままでした）

**調べ方と打ち切り**

- 入口5つ＝①社内の正本（indicator_combination_kb §7・technical KB・step1_regime_design・この KB）②社内の実装（RG-v5/v6・archive/regime_rule_classifier・e36 の Lee-Mykland・ml_regime_classifier）③教科書系サイトの本文（StockCharts・TradingView・LuxAlgo・QuantMonitor・mathandmarkets）④学術（arXiv 2402.05272 ほか）⑤別 AI の回答との突き合わせ（§9・§10）。
- 打ち切りの基準＝新しい調べ方をしても、新しい相場の法則の型が2回 連続で出なくなったら打ち切り。
- 実績＝2026-08-20 の Web の3ラウンド目（本文の取得）と4ラウンド目（下げ・暗号資産の検索）で、新しい相場の法則の型が0件＝基準を満たして打ち切り。★「この世のすべて」の証明ではない。穴は 11-7 に書いた。

## 11-1 場面に共通の相場の法則（組み立ての作法）｜10件

| # | 相場の法則（1文） | **どの段で使うか** | 級 |
|---|---|---|---|
| **C1** | トレンドの強さと、向きは、別の物差しで測る | **M2-D** | 【本文】 |
| **C2** | 同じ問いに答える指標を、重ねて使わない | **M2-G** | 【本文】 |
| **C3** | 実データで動きがほぼ同じ指標は、片方を外す | **M2-G** | 【本文】 |
| **C4** | 上位足が許可を出し、下位足が入る瞬間を決める | **M2-E** | 【本文】 |
| **C5** | 場面の判定は「入る合図」ではなく、入口を通すか止めるかを決めるもの | **M2-L** | 【本文】 |
| **C6** | 判定を安定させる仕組みは2つあり、別のものとして扱う | **M2-E** | 【本文】 |
| **C7** | 判定が続く長さは、相場の法則で決めず、engine_tuner が探す値にする | **M2-K** | 【本文】 |
| **C8** | パラメータは、場面の判定では長め・入口では短めにする | **M2-K** | 【要約】 |
| **C9** | 数値は相場の法則で決めない。範囲で探す | **M2-K** | 【正本】 |
| **C10** | 未来のデータを使ってしまう作り方が5つある。全部 避ける | **M2-I** | 【本文】 |

### 11-1 の1件ずつの説明

**C1｜トレンドの強さと、向きは、別の物差しで測る**

- **中身**＝トレンドか否か（強さ）と、上か下か（向き）は別の指標。3つに分けるには2本 要る。
- **どの段で使うか**＝**M2-D**（場面を分ける材料の順位を作るとき、強さと向きを別の物差しとして扱う）
- **出どころ**＝【本文】StockCharts ADX（この KB §2）＝逐語 "measures the strength of the trend (regardless of direction)"

**C2｜同じ問いに答える指標を、重ねて使わない**

- **中身**＝同系統2本は「雑音が2倍」。強さの指標（CHOP・ER・VHF）は中身がほぼ同じ。
- **どの段で使うか**＝**M2-G**（組み合わせる相手を選ぶときの読み込ませる法則。M2-G の「見ているものが違う相手を選ぶ」そのもの）
- **出どころ**＝【本文】excavo・LiteFinance（`indicator_combination_kb.md` 相場の法則1・2）＋この KB §4-2

**C3｜実データで動きがほぼ同じ指標は、片方を外す**

- **中身**＝「トレンド系」「オシレーター系」という系統の札だけで重複を判定すると粗い。同じ系統でも見ているものが違うことがあり（ADX は強さ・DI差は向き）、系統が違っても動きがほぼ同じことがある。だから実際の値動きデータで、2つの指標の動きがどれだけ重なるかを計算し、ほぼ同じ動きなら片方を外す。
- **どの段で使うか**＝**M2-G**（M2-G の「実データで間違い方の重なりを測って落とす」そのもの）
- ★計算に使うのは値決め窓のデータだけ（採点窓を使うと未来参照になる）。
- **出どころ**＝【本文】apxml（`indicator_combination_kb.md` 相場の法則6）

**C4｜上位足が許可を出し、下位足が入る瞬間を決める**

- **中身**＝逐語＝"Entries come from below; permission comes from above."。時間足の比は4〜6倍。
- **どの段で使うか**＝**M2-E**（1本の束を組むときの読み込ませる法則。K-2 が既に持っている）
- **出どころ**＝【本文】LuxAlgo HTF（`engine_tuner_milestones2.md` §3.5（6））＋NinjaTrader（`indicator_combination_kb.md` 相場の法則4）＋RG-3

**C5｜場面の判定は「入る合図」ではなく、入口を通すか止めるかを決めるもの**

- **中身**＝場面の判定がやるのは「いまはレンジだから、レンジ用の入口を動かしてよい」「いまは下げトレンドだから、レンジ用の入口を止める」という許可と停止だけ。建てるタイミングは、場面の判定を通ったあとに、入口の条件が別に決める。
- **どの段で使うか**＝**M2-L**（この相場の法則が成り立つから、建玉の Entry と Exit を固定したまま判定だけ差し替えられる）
- 出どころの逐語＝"Predicting the next price with the MMI would work as well as flipping a coin."（MMI を作った人 自身が「これで次の値段は当てられない」と書いている）
- **出どころ**＝【本文】MMI・HMM（この KB §4-3）

**C6｜判定を安定させる仕組みは2つあり、別のものとして扱う**

- **中身**＝①何本 続いたら成立 ②入る線と出る線を別にする（状態を保つ）。
- **どの段で使うか**＝**M2-E**（1本の束を組むときの読み込ませる法則。K-3 が既に持っている）
- **出どころ**＝【本文】mathandmarkets・traderssecondbrain（この KB §4-6）

**C7｜判定が続く長さは、相場の法則で決めず、engine_tuner が探す値にする**

- **中身**＝判定が続く長さ（数時間か・丸1日か）は、相場の法則では決まらない。切替の慣性を強くすれば長く、弱くすれば短くなる。E38 は数分で回すスキャルなので、判定が丸1日 変わらないと粗すぎ、5分ごとに切り替わると使えない。
- **どの段で使うか**＝**M2-K**（値を範囲で調整する段）
- ★過去に14版を凍結した理由の3つ目（ラベルは16〜28時間 続くのに取引は中央値15分）は、この長さを調整する仕組みが無かったこと。だから長さを探す値にする。
- 出どころの逐語＝"As lambda increases, state transitions become less frequent."（罰を強くするほど切替が減る＝長さをつまみ1つで調整できる）
- **出どころ**＝【本文】arXiv 2402.05272・Label Horizon Paradox（この KB §4-4）

**C8｜パラメータは、場面の判定では長め・入口では短めにする**

- **中身**＝場面の判定にオシレーターを使うなら期間を大きく（RSI 100〜200 の例）。
- **どの段で使うか**＝**M2-K**（値を範囲で調整する段）
- **出どころ**＝【要約】Better System Trader（`engine_tuner_milestones2.md` §3.5（6）の5番）＋【別AI】Gemini の4要素の表

**C9｜数値は相場の法則で決めない。範囲で探す**

- **中身**＝文献の数字（ADX 25・20 ほか）は目安。うちの正解は engine_tuner が範囲から探す。
- **どの段で使うか**＝**M2-K**（値を範囲で調整する段）
- **出どころ**＝【正本】恒久の決まり47番・L-267・この KB の各所の注意書き

**C10｜未来のデータを使ってしまう作り方が5つある。全部 避ける**

- **中身**＝避けるべき5つを、1つずつ書く。
- **どの段で使うか**＝**M2-I**（未来参照の検査を走らせる段）
- ①閾値を「全期間の分位」で決めると、未来のデータが閾値に混ざる → その時点までの過去だけで分位を出す。
- ②山と谷は、確定に数本あとの値動きが要る → 確定するまで待ってから使う（実例の「j+2 確定」がこの形）。
- ③HMM という統計モデルには、全期間を見てから過去の状態を出し直す使い方（smoothed）がある＝未来参照 → その時点までのデータだけで出す使い方（filtered）にする。
- ④データをかたまりに分ける手法で、全期間を使って分け方を決めると採点窓の情報が入る → 分け方は値決め窓だけで決める。
- ⑤走らせる途中でモデルを学習し直すと、それ以降のデータが混ざる → 途中で学習し直さない。
- **出どころ**＝【本文】この KB §5

## 11-2 レンジの相場の法則（E38 の主戦場）｜11件

| # | 相場の法則（1文） | 相場の何を見ているか | 級 | engine_tuner で書けるか |
|---|---|---|---|---|
| **R1** | レンジかどうかは、価格が何回も跳ね返された線が上下に在るかで決める | 基準になる値幅（帯） | 【正本】 | ○ 判定あり（部品を数える） |
| **R2** | 補助（トレンドの強さ・値動きの幅・出来高）は、違う系統から選ぶ | 組み合わせの読み込ませる法則 | 【正本】 | ○ 判定あり（系統を重ねない） |
| **R3** | 上位足でゾーンを作り、5分足で執行する | 多時間軸の一致 | 【正本】 | ○ 判定あり（部品を数える） |
| **R4** | 何本 続いているかを条件に入れる | 判定の安定 | 【正本】 | ○ 判定あり（形を持つ） |
| **R5** | トレンドの強さを測る指標が「弱い」と出ていたら、レンジ寄り | トレンドの強さ | 【本文】 | ○ 判定あり（部品を数える） |
| **R6** | BB 幅の縮小（スクイーズ）は、低ボラ＝レンジ寄り | ばらつきの水準 | 【本文】 | ○ 判定あり（部品を数える） |
| **R7** | 帯の幅が、往復の手数料を超えていること | 基準になる値幅（帯） | 【正本】 | ○ 判定あり（部品を数える） |
| **R8** | 非トレンド（上げ・下げの否定）を条件に含める | 場面と場面の関係 | 【実装】 | ○ 判定あり（形を持つ） |
| **R9** | 測るもの3つ（判定した時間の割合・その中の玉の成績・実はトレンドだった割合） | 測る側の物差し | 【正本】 | — 置き場＝regime_r9_diag.py（M2-5-4・まこさん承認 327e7f80…）＝束の審査ではなく、判定の結果（測るもの3つ）を出す診断。束1つの審査の形にならないので「機械が読む判定」は持たせない |
| **R10** | 静かなレンジと荒いレンジを分ける | トレンドの強さ／ばらつきの水準 | 【本文】 | ○ 判定あり（部品を数える） |
| **R11** | レンジ判定の頻度と閾値は、時間帯（欧米株式市場の取引時間）と曜日（平日/週末）で水準が変わる前提で扱う | 時間帯・曜日の周期性 | 【本文】 | — 置き場＝M2-C で UTC の時刻・曜日の列を足した後に決める（閾値の探索を時間帯別に扱う＝探索の側。束1つの審査の形にならないので、部品が入るまで「機械が読む判定」は持たせない） |

### 11-2 の1件ずつの説明

**R1｜レンジかどうかは、価格が何回も跳ね返された線が上下に在るかで決める**

- **中身**＝ADX などの「横ばい度の統計」で決めるのではない。実際に価格が跳ね返された実績（タッチ）が最低3回ある線だけを、本物のサポート・レジスタンスと認める。その線が close の上下に揃っていたらレンジ。
- 正本の逐語＝「統計量（横ばい度・ADX 等）ではなく、機能しているレベルの実績で認識する」
- ★「最低3回」の数字は目安＝範囲で探す（C9）。外部の幅＝StockCharts Rectangle は片側2（逐語 "At least two equivalent reaction highs are required to form the upper resistance line and two equivalent reaction lows to form the lower support line."）／LuxAlgo ≥3／自前実装 `V11_ZONE_TOUCH`＝2（`e37_scalp.py:123`）＝穴7の材料（監査 CP11 改善5・2026-09-01）。
- **出どころ**＝【正本】RG-1（`range_scalping_kb.md` §2・`indicator_combination_kb.md` §7）

**R2｜補助（トレンドの強さ・値動きの幅・出来高）は、違う系統から選ぶ**

- **中身**＝RG-2。
- **出どころ**＝【正本】`range_scalping_kb.md` §2・`indicator_combination_kb.md` §7

**R3｜上位足でゾーンを作り、5分足で執行する**

- **中身**＝RG-3＝多時間軸の黄金律。
- ★C4（執行足より上の部品1本）とは別物＝C4 は部品C（強さ×上位足）で常に満たす。R3 は構造・位置の部品が上位足に在ることを求める。実測＝組む側の30案のうち12案は C4 を通るのに R3 を破る（worklog 20260830 §7（4）・監査 CP11 Q3）。
- **出どころ**＝【正本】`range_scalping_kb.md` §2・`indicator_combination_kb.md` §7

**R4｜何本 続いているかを条件に入れる**

- **中身**＝RG-4＝1本だけ成立してもレンジと言わない。
- ★レンジ中は帯の外へのヒゲ抜け（だまし）が頻発する＝帯の外の1タッチでレンジ終了と判定せず、終値と確認本数で見る（LuxAlgo・逐語 "False breakouts are common in sideways markets."・https://www.luxalgo.com/blog/neutral-trading-profit-in-sideways-markets/・2026-09-01 に本文を開いた・監査 CP11 N2）。
- ★C6①（何本 続いたら成立）のレンジ適用＝同じ機構。統合はしない（C6 は共通の法則・R4 はレンジへの要求）＝相互参照だけ（監査 CP11 Q3・まこさん確認 2026-09-01）。
- **出どころ**＝【正本】`range_scalping_kb.md` §2・`indicator_combination_kb.md` §7

**R5｜トレンドの強さを測る指標が「弱い」と出ていたら、レンジ寄り**

- **中身**＝具体的には4つ。①ADX が 20 未満（トレンドなし）②CHOP が 61.8 超（CHOP＝値動きのゴチャゴチャ度。1本ずつの値動きの合計 ÷ n本ぜんぶで動いた幅（最高値−最安値）。高いほど行ったり来たり＝横ばい）③ER が低い（ER＝まっすぐ進んだ距離 ÷ 実際に歩いた距離。低いほど行ったり来たり）④MMI が高い（MMI＝値動きがランダムに近いかの割合。高いほどレンジ寄り）。
- ★数字は目安＝範囲で探す（C9）。
- **出どころ**＝【本文】この KB §3-A

**R6｜BB 幅の縮小（スクイーズ）は、低ボラ＝レンジ寄り**

- **中身**＝幅が過去より狭い状態。抜けの向きは教えない。
- 逐語＝"A Bollinger Band Squeeze is a condition that occurs when the Bollinger Bands narrow due to decreased volatility."／"Note that narrowing bands do not provide any directional clues."（2026-09-01 に本文を開いた）。
- ★スクイーズは大きな動きの前触れでもある（逐語 "can foreshadow a significant advance or decline"）＝レンジの終わりの接近と同じ現象。
- ★役割＝レンジ検出の入力（低ボラ＝レンジ寄り）。R10（検出の後の下位分類）とは役割が違う（監査 CP11 Q3）。
- **出どころ**＝【本文】StockCharts Squeeze（この KB A-7・https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/bollinger-band-squeeze・2026-09-01 に本文を開いた＝【要約】から【本文】へ昇格・監査 CP11 改善4）

**R7｜帯の幅が、往復の手数料を超えていること**

- **中身**＝往復の手数料を超える値動きが取れる幅（十分性）。
- ★数字は相場の法則で決めない＝範囲で探す（C9）。
- ★出どころの数字の訂正（2026-08-27・監査 第4要素 Q3-3 の指摘）＝手数料の床 `SCALP_FLOOR` は 0.08%（`e38_logic_parts.py:23`＝`e37.SCALP_FLOOR`）。一例の「幅≥0.4%」の実体は `V11_ZONE_MIN_W = 0.004`（`e37_scalp.py:124`・a-priori の値）で、0.08% の5倍。直す前は「SCALP_FLOOR が 0.4% の根拠」と読める書き方だったが、数字が合わない。
- ★もう1つの穴＝「幅」の測り方が2つ在る（判定＝帯の内側の隙間が `V11_ZONE_MIN_W` 以上（`e37_scalp.py:479`）／engine_tuner の条件＝全幅 (res_hi−sup_lo)/close＝W%＝`wpct_arr`（`engine_tuner_exec.py:2464`））。この相場の法則はどちらを指すかを定めていない（11-7 の穴6）。★行参照の直し（監査 CP11 E2・2026-09-01）＝直す前は 2247行 を指していたが、行ドリフトで W% の式ではない行になっていた。
- **出どころ**＝【正本】SCALP_FLOOR（`e38_logic_parts.py:23`）・十分性の考え方

**R8｜非トレンド（上げ・下げの否定）を条件に含める**

- **中身**＝レンジ＝帯あり ∩ 帯内 ∩ 非 uptrend。
- **出どころ**＝【実装】RG-v5 `_rg5_frames`（`e37_scalp.py:517`）・`_apply_rg5_to_5m`（`e37_scalp.py:548`）＝正本。`_rg5_frames` は `e37_range_scalp.py:1588` で import（2026-08-20 の一本化）。★行参照の直し（監査 CP11 E1・2026-09-01）＝直す前は e37_range_scalp.py の 1615行 を指していたが、行ドリフトで R:R 検査（tp_ge_sl_check_v11）の中になっていた

**R9｜測るもの3つ（判定した時間の割合・その中の玉の成績・実はトレンドだった割合）**

- **中身**＝判定した時間の割合／その中の玉の成績／実はトレンドだった割合（E37 の失敗の本体）。
- **出どころ**＝【正本】`indicator_combination_kb.md` §7

**R10｜静かなレンジと荒いレンジを分ける**

- **中身**＝トレンド性 × ばらつき の2軸で4分類。
- ★役割＝検出の後の下位分類（静かなレンジと荒いレンジを分けて、出口とサイズに効かせる）。R6（検出の入力）とは役割が違う。動きがほぼ同じ2本を重ねる件は C3 が別に見る（監査 CP11 Q3）。
- **出どころ**＝【本文】QuantMonitor（`engine_tuner_milestones2.md` §3.5（6））＋【別AI】ChatGPT の4分類（この KB §10-4）

**R11｜レンジ判定の頻度と閾値は、時間帯（欧米株式市場の取引時間）と曜日（平日/週末）で水準が変わる前提で扱う**

- **中身**＝BTC は24時間 動くが、値動きの密度は一様ではない。出来高とボラティリティは1日の中で逆V字（欧米株式市場の昼の時間帯に高く）、平日が週末より はっきり高い。だからレンジ判定の頻度と閾値の水準は、時間帯と曜日で変わる前提で扱う（固定の1つの水準を全時間に当てない）。
- ★数字は目安＝範囲で探す（C9）。
- ★測る部品（UTC の時刻・曜日の列・時間帯別のボラ・出来高の分位）は いまの材料に0件＝部品を足すのは M2-C（監査 CP11 N1・2026-09-01 追加）。
- **出どころ**＝【本文】Wang, Jying-Nan／Liu, Hung-Chun／Hsu, Yuan-Teng（2020）「Time-of-day periodicities of trading volume and volatility in Bitcoin exchange」Finance Research Letters 34（https://ideas.repec.org/a/eee/finlet/v34y2020ics1544612319301904.html・2026-09-01 に要旨を開いた・逐語＝"the trading activity resembles a reverse V-shaped pattern throughout the day"／"noticeably higher trading volume and volatility during hours that coincide with the daytime trading hours of European and US stock exchanges"／"Both variables are substantially higher on weekdays than weekends."）

## 11-3 上げの相場の法則｜10件

| # | 相場の法則（1文） | 相場の何を見ているか | 級 | engine_tuner で書けるか |
|---|---|---|---|---|
| **U1** | 高値を切り上げ、かつ 安値も切り上げている | スイングの並び | 【正本】 | （元の表に無い） |
| **U2** | トレンドが強く、かつ +DI が -DI より大きい | トレンドの強さ／向き | 【本文】 | （元の表に無い） |
| **U3** | 終値が長期移動平均の上に在り、移動平均の傾きも上を向いている | 向き | 【要約】 | （元の表に無い） |
| **U4** | 直近N本の終値に直線を当てはめ、その傾きがプラスなら上げ | 向き | 【本文】 | （元の表に無い） |
| **U5** | Supertrend の札が「上げ」を出しているあいだは上げ | 向き | 【要約】 | （元の表に無い） |
| **U6** | 終値が「直近N本の最高値の線」を上に抜けたら、上げの始まりの合図 | チャネルの抜け | 【本文】 | （元の表に無い） |
| **U7** | 前回の高値を更新したら、上げが続いていると見る | スイングの並び | 【正本】 | （元の表に無い） |
| **U8** | 上昇の半値まで戻したら、上げを解除する | 基準になる値幅の中の位置 | 【正本】 | （元の表に無い） |
| **U9** | 高値と安値の並びが壊れたら、上げを疑う | スイングの並び | 【本文】 | （元の表に無い） |
| **U10** | 一度「上げ」と判定したら、解除の条件が成立するまで「上げ」のままにする | 判定の安定 | 【実装】 | （元の表に無い） |

### 11-3 の1件ずつの説明

**U1｜高値を切り上げ、かつ 安値も切り上げている**

- **中身**＝Higher Highs + Higher Lows ＝上昇トレンドの定義（ダウ理論）。
- **出どころ**＝【正本】`technical_analysis_knowledge_base.md`:926 ＋ この KB A-9【要約】

**U2｜トレンドが強く、かつ +DI が -DI より大きい**

- **中身**＝ADX≥25（強い）と向きの掛け合わせ。
- **出どころ**＝【本文】StockCharts（この KB §2・A-1）

**U3｜終値が長期移動平均の上に在り、移動平均の傾きも上を向いている**

- **中身**＝MA200 の上＝強気の地合い。EMA50>EMA200 の2段確認。
- **出どころ**＝【要約】quantifiedstrategies・arXiv 2603.15848（本文はボット遮断で開けず）

**U4｜直近N本の終値に直線を当てはめ、その傾きがプラスなら上げ**

- **中身**＝「回帰直線」＝直近N本の終値に一番よく当てはまる直線。傾きプラス＝上げ／マイナス＝下げ／ほぼ0＝横ばい。
- ★傾きの値をそのまま使うと BTC の値段の水準（6万ドルか10万ドルか）で大きさが変わるので、ATR か % で割って、値段の水準に左右されない数字にする（＝「正規化」。うちの読み込ませる法則 H6＝ドルの絶対値を使わない、にそのまま合う）。
- 逐語＝"often normalized by ATR or expressed as a percentage so thresholds transfer across symbols and timeframes"
- **出どころ**＝【本文】LuxAlgo Linear Regression（2026-08-20 に本文を開いた）

**U5｜Supertrend の札が「上げ」を出しているあいだは上げ**

- **中身**＝Supertrend は「上げか下げか」の札を直接 出す指標。作り＝(高値+安値)÷2 から ATR の倍数だけ離れた線を引き、終値がその線を反対側に抜けたら、札が「上げ」⇔「下げ」に切り替わる。
- **出どころ**＝【要約】TradingView（この KB A-8）

**U6｜終値が「直近N本の最高値の線」を上に抜けたら、上げの始まりの合図**

- **中身**＝Donchian チャネル＝直近N本（既定20本）の最高値の線と最安値の線。終値が最高値の線を上に抜けたら上げの合図。
- ★注意＝本文に「明確なトレンドの中で一番よく効く」と書いてある＝レンジの中ではダマシの抜けが増える。
- 逐語＝"Upper Channel = 20 Day High" ／ "Donchian Channels primarily work best within a clearly defined trend."
- **出どころ**＝【本文】TradingView DC（2026-08-20 に本文を開いた）

**U7｜前回の高値を更新したら、上げが続いていると見る**

- **中身**＝トレンド継続の確認（実例の「前回高値+0.3%超えで再成立」の骨格）。
- **出どころ**＝【正本】ダウ理論（`technical_analysis_knowledge_base.md`）＋まこさんの実例

**U8｜上昇の半値まで戻したら、上げを解除する**

- **中身**＝上昇の 38.2〜61.8%（50% 含む）は反転高確率ゾーン。
- **出どころ**＝【正本】`technical_analysis_knowledge_base.md`:672-677

**U9｜高値と安値の並びが壊れたら、上げを疑う**

- **中身**＝「構造」＝高値と安値の並び（上げなら、高値も安値も切り上がっている並び）。「破断」＝その並びが壊れること＝終値が直近の安値を割ったら、上げの構造が壊れたと見る。実例の「close < 直近2本の確定15分安値」がまさにこれ。
- 外の資料での呼び名＝CHoCH（並びの性格が変わった＝反転の可能性）・BoS（並びどおりに抜けた＝継続）。
- **出どころ**＝【本文】LuxAlgo Market Regimes（2026-08-20 に本文を開いた）

**U10｜一度「上げ」と判定したら、解除の条件が成立するまで「上げ」のままにする**

- **中身**＝①入る条件（複数の経路のどれか1つが成立したらスイッチが入る）②入っているあいだは毎バー測り直さず「上げ」を保つ ③切る条件（半値戻し 等）が成立したらスイッチが切れる。
- 「入る線と出る線を別にする」＝入る基準と出る基準をずらす（例＝0.6 を超えたら入り、0.4 を割るまで出ない）＝小さな揺れで判定がパタパタ変わるのを防ぐ。
- まこさんの実例の②（成立4経路・継続・解除3条件）と、うちの RG-v5 がこの形。
- **出どころ**＝【実装】RG-v5 `_uptrend_state_5m` ＋【本文】hysteresis（この KB §4-6）

## 11-4 下げの相場の法則｜9件

| # | 相場の法則（1文） | 相場の何を見ているか | 級 | engine_tuner で書けるか |
|---|---|---|---|---|
| **D1** | 安値を切り下げ、かつ 高値も切り下げている | スイングの並び | 【正本】 | （元の表に無い） |
| **D2** | トレンドが強く、かつ -DI が +DI より大きい | トレンドの強さ／向き | 【本文】 | （元の表に無い） |
| **D3** | 終値が複数の移動平均の下に在り、移動平均の傾きも下を向いている | 向き | 【実装】 | （元の表に無い） |
| **D4** | 上位足の向きが一致していたら、重みを大きくする | 多時間軸の一致 | 【実装】 | （元の表に無い） |
| **D5** | 「下に動いた分だけ」のばらつきで測る | ばらつきの水準 | 【本文】 | （元の表に無い） |
| **D6** | 直近N本の終値に当てはめた直線の傾きがマイナスなら下げ | 向き | 【本文】 | （元の表に無い） |
| **D7** | 終値が「直近N本の最安値の線」を下に抜けたら、下げの始まりの合図 | チャネルの抜け | 【本文】 | （元の表に無い） |
| **D8** | 連続2回 同じ判定が出たら切り替える（慣性） | 判定の安定 | 【正本】 | （元の表に無い） |
| **D9** | 3つに分けたかたまりに「上昇・下落・レンジ」の名前を付ける手順 | 名付けの手順（判定ではない） | 【正本】 | （元の表に無い） |

### 11-4 の1件ずつの説明

**D1｜安値を切り下げ、かつ 高値も切り下げている**

- **中身**＝Lower Lows + Lower Highs（U1 の鏡像）。
- **出どころ**＝【正本】`technical_analysis_knowledge_base.md`:926

**D2｜トレンドが強く、かつ -DI が +DI より大きい**

- **中身**＝前提＝ADX>25。
- 逐語＝"A sell signal triggers when -DI crosses above +DI. The high on the day of the sell signal becomes the initial stop-loss."
- **出どころ**＝【本文】StockCharts（この KB A-1）

**D3｜終値が複数の移動平均の下に在り、移動平均の傾きも下を向いている**

- **中身**＝終値が SMA20・SMA50・EMA200 の全部より下→下げ／BB 中央線の傾き<-10%→下げ／基準線より-0.5%下→下げ。
- **出どころ**＝【実装】`archive/regime_rule_classifier.py`:133-250

**D4｜上位足の向きが一致していたら、重みを大きくする**

- **中身**＝1時間足と4時間足の向きの一致＝重み1.5（6指標中 最大）。
- **出どころ**＝【実装】`archive/regime_rule_classifier.py`:61-66

**D5｜「下に動いた分だけ」のばらつきで測る**

- **中身**＝ふつうのばらつき（ATR・標準偏差）は上下の動きを混ぜて測る。それを「下に動いた分だけ」で測り直す物差しが downside deviation（下方偏差）。下げ相場の検出には、上下混ぜたばらつきより、下だけのばらつきの方が向くという相場の法則。Sortino も同じ発想（利益 ÷ 下だけのばらつき）。
- 逐語＝"EWM downside deviation (DD) with a halflife of 10 trading days..."
- **出どころ**＝【本文】arXiv 2402.05272 §3.4.1（この KB §2.7.2）

**D6｜直近N本の終値に当てはめた直線の傾きがマイナスなら下げ**

- **中身**＝U4 の向きを逆にしただけ（「鏡像」＝上げの相場の法則の上下を入れ替えたもの、の意味）。ATR か % で割る正規化も同じ。
- **出どころ**＝【本文】LuxAlgo Linear Regression

**D7｜終値が「直近N本の最安値の線」を下に抜けたら、下げの始まりの合図**

- **中身**＝U6 の向きを逆にしただけ。レンジの中ではダマシが増える注意も同じ。
- **出どころ**＝【本文】TradingView DC

**D8｜連続2回 同じ判定が出たら切り替える（慣性）**

- **中身**＝2時間相当。1回の判定で切り替えない。
- **出どころ**＝【正本】`step1_regime_design.md` §2.1（まこさん確定）

**D9｜3つに分けたかたまりに「上昇・下落・レンジ」の名前を付ける手順**

- **中身**＝判定で3つのかたまりに分けたあと、どれが上昇でどれが下落かを決める手順＝各かたまりの中の DI差（+DI − -DI・1時間足）の中央値を出し、一番大きいかたまり＝上昇／一番小さい＝下落／残り＝レンジ と名付ける。
- 名付けが妥当かの確かめ方＝レンジと名付けたかたまりの ADX 平均が、他の2つより低いこと。
- ★11-4 の末尾の注記＝最後の検索（下げ・暗号資産）で新しい型は出なかった。下げは「上げの鏡像＋D5（下向きのばらつき）」で、下げ特有の別系統は見つからなかった。
- **出どころ**＝【正本】`step1_regime_design.md` §2.7（まこさん確定）

## 11-5 スパイクの相場の法則｜6件

| # | 相場の法則（1文） | 相場の何を見ているか | 級 | engine_tuner で書けるか |
|---|---|---|---|---|
| **S1** | いまの1本の値動きが、ふだんの揺れと比べて統計的にありえないほど大きいかを測る | 1本の動き ÷ ふだんの動き | 【実装】 | ○ 判定あり（部品を数える） |
| **S2** | 1本の値幅を、ATR の倍数と比べる | 1本の動き ÷ ふだんの動き | 【要約】 | （元の表に無い） |
| **S3** | 出来高のスパイクと、価格のブレイクを組み合わせる | 出来高 | 【本文】 | （元の表に無い） |
| **S4** | 一定の幅を超えた本数を数える | 1本の動き ÷ ふだんの動き | 【実装】 | （元の表に無い） |
| **S5** | ニュース由来の出来高は短命なので、ダマシになりやすい | 出来高 | 【本文】 | （元の表に無い） |
| **S6** | BB 幅が急に広がったら、スパイク寄り | ばらつきの変化 | 【要約】 | （元の表に無い） |

### 11-5 の1件ずつの説明

**S1｜いまの1本の値動きが、ふだんの揺れと比べて統計的にありえないほど大きいかを測る**

- **中身**＝Lee-Mykland 2008 の検定。分子＝いまの1本の値動き（終値の変化率）。分母＝ふだんの揺れの大きさ（直近K本から出す）。分子÷分母が閾値を超えたらスパイク。K=270（5分足で約1日）で実装済み・E36 の急騰 Exit で実際に動いている。
- ★分母の計算には bipower という方法（隣り合う2本の値動きの積）を使う。こうすると、スパイク自身が「ふだんの揺れ」の計算を汚さない。
- ★閾値は「K本と、誤検出をどこまで許すか（α）」から数式で先に決める＝データを見て後から選ばない＝過剰適合しない。
- **出どころ**＝【実装】`e36_short_oscillation.py`:372-382・:1232。`score.py`:64 に `SPIKE_SL` 登録済み

**S2｜1本の値幅を、ATR の倍数と比べる**

- **中身**＝1本の値幅（高値-安値）を ATR の倍数と比べる。bull/bear は close と open の大小で分ける。
- **出どころ**＝【要約】TradingView Auto-ATR Volatility Spike（本文は未読）

**S3｜出来高のスパイクと、価格のブレイクを組み合わせる**

- **中身**＝出来高の急増と価格の抜けを重ねて確かめる。
- 逐語＝"Absolute Volume: 200% of 20-day average" ／ "Relative Volume: 150% of the previous hour" ／ "Volume spike + price breakout: Confirm high-probability signals"
- ★うちは需給・出来高の材料が0件＝いまは書けない。
- **出どころ**＝【本文】LuxAlgo Volume Spikes（2026-08-20 に本文を開いた）

**S4｜一定の幅を超えた本数を数える**

- **中身**＝直近24時間で、1時間足のリターンが±1%を超えた本数。
- **出どころ**＝【実装】`ml_regime_classifier.py`:259-267

**S5｜ニュース由来の出来高は短命なので、ダマシになりやすい**

- **中身**＝ニュースで急に増えた出来高は、長く続かない。
- 逐語＝"News-Driven Volume: Can trigger short-lived, unstable movements"
- **出どころ**＝【本文】LuxAlgo Volume Spikes

**S6｜BB 幅が急に広がったら、スパイク寄り**

- **中身**＝幅の「変化」を見る（水準でなく）。
- **出どころ**＝【要約】StockCharts ＋【別AI】ChatGPT・Gemini（裏取りは幅の変化の部品を数えてから）

## 11-6 変わり始め（transition）の相場の法則（★M4＝出口にもつながる）｜5件

| # | 相場の法則（1文） | 相場の何を見ているか | 級 | engine_tuner で書けるか |
|---|---|---|---|---|
| **T1** | 高値と安値の並びの性格が変わったか、並びどおりに抜けたかを見る | スイングの並び | 【本文】 | （元の表に無い） |
| **T2** | 複数の指標が同じ向きに動き始めたら、移り変わりと見る | 変化を見る | 【別AI】 | （元の表に無い） |
| **T3** | 多時間軸を見ると、早い段階で兆候が出る | 多時間軸の一致 | 【本文】 | （元の表に無い） |
| **T4** | 「いまどれか」と「変わり始めたか」は、別の判定として持つ | 場面をまたぐ作法 | 【別AI】 | （元の表に無い） |
| **T5** | 分布が変わった時刻を検定で出す（変化点の検出） | 変化を見る | 【要約】 | （元の表に無い） |

### 11-6 の1件ずつの説明

**T1｜高値と安値の並びの性格が変わったか、並びどおりに抜けたかを見る**

- **中身**＝CHoCH＝構造の性格の変化＝反転の可能性／BoS＝構造の破断＝継続。
- **出どころ**＝【本文】LuxAlgo Market Regimes

**T2｜複数の指標が同じ向きに動き始めたら、移り変わりと見る**

- **中身**＝「ER上昇 ＋ ADX上昇 ＋ BB Width急拡大 → レンジ終了リスク上昇」。
- ★裏取りまだ＝根拠に使う前に本文を探す。
- **出どころ**＝【別AI】【別AI】ChatGPT（この KB §10-3）

**T3｜多時間軸を見ると、早い段階で兆候が出る**

- **中身**＝上位足と下位足を合わせて見ると、場面が変わる前ぶれが見える。
- 逐語＝"Multi-timeframe analysis can reveal early signs of regime changes"
- **出どころ**＝【本文】LuxAlgo Market Regimes

**T4｜「いまどれか」と「変わり始めたか」は、別の判定として持つ**

- **中身**＝Static Regime 判定 と Regime Transition 判定の2段。
- **出どころ**＝【別AI】【別AI】ChatGPT（この KB §10-3）

**T5｜分布が変わった時刻を検定で出す（変化点の検出）**

- **中身**＝分布が変わった時刻を検定で出す。条件の形にするなら T2 の形に落とす。
- **出どころ**＝【要約】この KB §3-D

## 11-7 未収載・穴（9件・正直に書く）

| # | 穴 | 中身 |
|---|---|---|
| 1 | **出来高・需給の材料が0件** | S3（出来高スパイク）が書けない。既存の「あとで直すこと」26番と同じ。★逆向きの警告（監査 CP11・2026-09-01）＝出来高の材料を足すとき「低出来高＝レンジ」を法則として焼かない。StockCharts Rectangle の逐語＝"Unlike symmetrical triangles, rectangles don't exhibit standard volume patterns."（レンジの原型パターンの資料自身が、標準の型は無いと書いている） |
| 2 | **「窓×幅の対を2本 置く」構成** | 実例の成立(c)(d)（90分で+1.0%／6hで+2.0%）。正本にも Web にも相場の法則として見つからなかった＝まこさんの設計。速い立ち上がりと遅い立ち上がりの2経路 |
| 3 | **quantifiedstrategies の本文** | ボットの遮断で開けず。U3（MA200）は【要約】のまま |
| 4 | **Directional Change・ボラ構造（短期÷長期）** | 本文が未読のまま（この KB §6 の既存の穴） |
| 5 | **暗号資産特有（funding・清算の連鎖）** | 材料が無いので調べていない |
| 6 | **「幅」の測り方の定義が無い（2026-08-27・監査 第4要素 Q3-3）** | R7 は「コストを超える」だけで、内側の隙間（res_lo−sup_hi）か全幅（res_hi−sup_lo）かを定めていない。実物は判定＝内側（`e37_scalp.py:479`）・条件の材料＝全幅 W%（`engine_tuner_exec.py:2247`）で使い分けている＝K-6 が別の量を測っても違反にならない |
| 7 | **「タッチ」と「スイング」の数え分けの相場の法則が無い（同 Q3-2）** | R1 は「タッチ最低3回」。実物は S-Rタッチ数（バーの重なりを数える・`observe_diag.py:363`）と fractal スイングの束ね（`build_regime_gate_rg.py:_zones_1h_rg`）の2通りの測り方が併存。どちらをどの場面で数えるかが相場の法則に無い |
| 8 | **帯の「対」の選び方の相場の法則が無い（同 Q3-1）** | R1 は「線が close の上下に揃っていたらレンジ」まで。上下に候補が複数あるときにどう選ぶか（実物は近い順・幅を満たす最初の対）が相場の法則に無い。外の資料はタッチ数・鮮度で格付けしている（監査 §4 の 2・6＝本文は未読・裏取りまだ） |
| 9 | **コストの床を絶対値で書く相場の法則が無い（同 Q3-4）** | C9（範囲で探す）と R7（コスト超え）は衝突しうる＝値決め窓の幅の分布が丸ごとコスト未満の区間では、どの分位を選んでも R7 に反する束が「読み込ませる法則を満たす」。実行器には名前つき定数（`const`）の書き方が在るが、生成器の場面の束は分位しか引かない（`engine_tuner_gen.py` `_thr_drawn`）。外の資料は幅と往復コストを絶対値で比べる（監査 §4 の 7＝本文は未読・裏取りまだ） |

## 11-8 出どころ（2026-08-20 に新しく開いたもの・7件）

- 【本文】[LuxAlgo・Linear Regression（Library）](https://www.luxalgo.com/library/concept/linear-regression/)
- 【本文】[TradingView・Donchian Channels (DC)](https://www.tradingview.com/support/solutions/43000502253-donchian-channels-dc/)
- 【本文】[LuxAlgo・Volume Spikes: Timing Trades with Precision](https://www.luxalgo.com/blog/volume-spikes-timing-trades-with-precision/)
- 【本文】[LuxAlgo・Market Regimes Explained](https://www.luxalgo.com/blog/market-regimes-explained-build-winning-trading-strategies/)
- 【要約】[TradingView・Auto-ATR Volatility Spike & Trend Tracker](https://www.tradingview.com/script/KTsZMbtk-Auto-ATR-Volatility-Spike-Trend-Tracker-BigBeluga/)
- 【要約】[QuantifiedStrategies・200 Day Moving Average](https://quantifiedstrategies.com/200-day-moving-average)
- 【要約】[StockCharts・Donchian Trading Guidelines](https://chartschool.stockcharts.com/table-of-contents/overview/donchian-trading-guidelines)
<!-- KB_LAWS_END -->

---

<!-- KB_FINDINGS_START hash=184dde880edfe99a gen_regime_kb.py が自動生成＝手で書き換えない -->
# §12 2026-08-29 に調べた結果（★この節は機械が作ります・手で書き換えない）

**調べた日**＝2026-08-29

**調べた理由**＝まこさんの指示（逐語 2026-08-29）＝「この定義の方法は系統ごとで良いのかというところから、WEBResearchして調べてほしい。調べて根拠のある状態で法則を定義したい」／「そもそも分類する必要や M2-G での複数ロジックの組み合わせ方は、分類したもの別が良いのかなど、根拠が薄い状態なので、調べたい。」

**調べ方の読み込ませる法則（3つ）**
1. 一次ページを開いて逐語を取る。検索の要約は根拠にしない（恒久の決まり43番）。
2. 開けなかったものは「開けなかった」と書く。
3. 外の数字はそのまま持ち込まない。採るのは考え方だけ（違反の記録 #23）。

**元データ**＝`.claude/ratchet/regime_kb_findings.json` ／ **作り方**＝`python3 .claude/tools/gen_regime_kb_findings.py --write（書く） ／ --verify（手で書き換えられていないかの検出）`

---

## 12-1 外は指標をどう整理しているか（問い4つ）

**調べた問い**
1. 外は指標を、どういう単位で整理しているか。
2. 「同じ系統を重ねない」に、外の根拠はあるか。
3. 指標の「系統」の分類は、何を基準に決まっているか。
4. 場面ごとに法則を分けるのは、外でも同じか。

### 答え

| 問い | 答え |
|---|---|
| 外は指標を、どういう単位で整理しているか | 1つの単位ではない。少なくとも3通りが併存する＝①価格と同じ目盛りか（Overlay）②先行か遅行か ③計算の種類（TA-Lib の10群）。 |
| 「同じ系統を重ねない」に、外の根拠はあるか | ある。ただし「何本まで」という上限は、開けたどのページにも書かれていない。 |
| 分類の基準は何か | 唯一の標準は無い。情報源ごとに切り方が違う。教科書サイトの一覧はカテゴリ分けすらしていない。 |
| 場面ごとに分けるのは外でも同じか | 同じ。教科書サイトも論文も、場面ごとに使う道具を替える。 |

### 一次ページを開いて取った逐語（12件）

| # | 出どころ | 級 | 答える問い | 逐語（英語のまま） | うちにとっての意味 |
|---|---|---|---|---|---|
| 1 | [StockCharts ChartSchool「Introduction to Technical Indicators and Oscillators」](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/introduction-to-technical-indicators-and-oscillators) | 【本文】 | 1 | Indicators that use the same scale as prices are typically plotted on top of the price bars and are therefore referred to as 'Overlays.' | 整理の単位の1つ目＝価格と同じ目盛りで描くかどうか。 |
| 2 | [同上](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/introduction-to-technical-indicators-and-oscillators) | 【本文】 | 1 | Leading indicators are designed to lead price movements / lagging indicators follow the price action and are commonly referred to as trend-following indicators. | 整理の単位の2つ目＝先行か遅行か。 |
| 3 | [同上](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/introduction-to-technical-indicators-and-oscillators) | 【本文】 | 2 | it would be redundant to use two indicators that are good for showing overbought and oversold levels, such as Stochastics and RSI. Both of these indicators measure momentum and both have overbought/oversold levels. | ★同じものを測る指標を重ねるなという根拠。ただし「何本まで」という上限は書かれていない。 |
| 4 | [同上](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/introduction-to-technical-indicators-and-oscillators) | 【本文】 | 2 | Try to choose indicators that complement each other, instead of those that move in unison and generate the same signals. | 選び方の基準＝補い合うもの。同じ動きをして同じ合図を出すものを避ける。 |
| 5 | [同上](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/introduction-to-technical-indicators-and-oscillators) | 【本文】 | 4 | Trend-following indicators work best when markets or securities develop strong trends / are not effective in trading or sideways markets. | ★場面ごとに使い分けるという根拠。うちの法則 C5（場面の判定は、入口を通すか止めるかを決めるもの）と同じ向き。 |
| 6 | [同上](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/introduction-to-technical-indicators-and-oscillators) | 【本文】 | 4 | These indicators can be used in trending markets, but usually with the major trend, not against it | 先行の指標をトレンド中に使うときは、大きな流れの向きに合わせる。うちの法則 C4・R8 と同じ向き。 |
| 7 | [StockCharts ChartSchool「Technical Indicators」の一覧ページ](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators) | 【本文】 | 3 | （実測＝カテゴリの見出しが無く、アルファベット順の1つの一覧だった） | ★教科書サイトの指標の一覧は、系統でカテゴリ分けされていない。 |
| 8 | [TA-Lib「Functions」](https://ta-lib.org/functions/) | 【本文】 | 3 | Cycle Indicators / Math Operators / Math Transform / Momentum Indicators / Overlap Studies / Pattern Recognition / Price Transform / Statistic Functions / Volatility Indicators / Volume Indicators | ★整理の単位の3つ目＝計算の種類で10群。「トレンド」という群が無く、移動平均は Overlap Studies に入る。10群のうち3群（Math Operators・Math Transform・Statistic Functions）はそもそも相場の指標ではない。 |
| 9 | [arXiv 2508.11338「RegimeNAS」§III-E](https://arxiv.org/html/2508.11338v1) | 【本文】 | 4 | Central to RegimeNAS is the concept of specialized neural blocks, each designed to effectively model distinct market characteristics. | ★場面ごとに専用の部品を持つという設計。うちの「場面ごとに法則を分ける」と同じ向き。 |
| 10 | [同 §III-C](https://arxiv.org/html/2508.11338v1) | 【本文】 | 4 | The framework dynamically combines or selects the specialized blocks based on the regime probabilities | 場面の確からしさで、専用の部品を選ぶか混ぜるかを切り替える。 |
| 11 | [同 §V-D](https://arxiv.org/html/2508.11338v1) | 【本文】 | 4 | Periods with ADX>25 were classified as 'Trend', periods with high ATR (>75th percentile) and low ADX were 'High Volatility', and remaining periods were 'Range'. | ★この数字は持ち込まない。論文自身が「あとから分けるための線であって、運用時の判定ではない」と書いている（違反の記録 #23 の再演を避ける）。 |
| 12 | [Fidelity「What is an indicator?」](https://www.fidelity.com/learning-center/trading-investing/what-is-an-indicator) | 【本文】 | 3 | （実測＝指標を3つ挙げるだけで、分類の記述が無かった） | 開けたが、この問いには使えなかった。 |

### 開けなかったもの（5件・正直に残す）

| # | 出どころ | 理由 |
|---|---|---|
| 1 | [Charles Schwab「Choosing Technical Indicators to Analyze Stocks」](https://www.schwab.com/learn/story/choosing-technical-indicators-to-analyze-stocks) | 認証エラーの画面が返る |
| 2 | [CMT Association「Technically Speaking, December 2011」](https://cmtassociation.org/technically_speaking/technically-speaking-december-2011/) | HTTP 403 |
| 3 | [arXiv 2509.14401（LSTM・指標の相関）](https://arxiv.org/pdf/2509.14401) | PDF の本文が取り出せない |
| 4 | [pandas-ta（カテゴリの一覧）](https://github.com/twopirllc/pandas-ta) | GitHub が 404・PyPI にカテゴリの記載なし・公式サイトは名前が引けない |
| 5 | [Investopedia](https://www.investopedia.com/) | ★この道具からは検索できない（提供元が拒否） |

## 12-2 複数の判定を組み合わせると精度が上がるのか（問い3つ）

**調べた問い**
1. 複数の判定ロジックを組み合わせると、1本より精度が上がるのか。上がるとしたら何が効いているのか。
2. 組み合わせる相手を「分類が違うもの」から選ぶと精度が上がる、という根拠はあるか。
3. 分類は、何を基準に切ると効くのか。

### 答え

| 問い | 答え |
|---|---|
| 組み合わせると精度が上がるか | 上がる。効いているのは「間違い方がずれていること」。ずれているから、平均すると間違いが打ち消し合う。 |
| 分類が違う相手を選ぶ根拠はあるか | ある。ただし本体は「分類が違うこと」ではなく「間違い方が重ならないこと」。分類はその代理でしかない。 |
| 分類は何を基準に切ると効くか | ★社内の正本に既に答えが在った＝人が付けた系統の札は粗い。最後は実データで動きの重なりを測る（法則6）。切るなら「系統」より「相場の何を見ているか」のほうが正確（§2）。 |

### 一次ページを開いて取った逐語（6件）

| # | 出どころ | 級 | 答える問い | 逐語（英語のまま） | うちにとっての意味 |
|---|---|---|---|---|---|
| 1 | [Hyndman・Athanasopoulos『Forecasting: Principles and Practice』3rd ed. 13.4 Forecast combinations](https://otexts.com/fpp3/combinations.html) | 【本文】 | 1 | John Bates and Clive Granger wrote a famous paper (Bates & Granger, 1969), showing that combining forecasts often leads to better forecast accuracy. | ★組み合わせると精度が上がることの、いちばん古い根拠（1969年）。 |
| 2 | [同上](https://otexts.com/fpp3/combinations.html) | 【本文】 | 1 | using a simple average has proven hard to beat | ★重みを凝った付け方より、単純な平均のほうが強いことが多い。うちの束ね方に「K本以上が真」（多数決）を足すことの後押しになる。 |
| 3 | [scikit-learn ユーザーガイド「Ensemble methods」](https://scikit-learn.org/stable/modules/ensemble.html) | 【本文】 | 1 | The injected randomness in forests yield decision trees with somewhat decoupled prediction errors. By taking an average of those predictions, some errors can cancel out. | ★何が効いているかの答え＝間違い方がずれていると、平均したとき間違いが打ち消し合う。 |
| 4 | [同 「Voting Classifier」](https://scikit-learn.org/stable/modules/ensemble.html) | 【本文】 | 2 | The idea behind the VotingClassifier is to combine conceptually different machine learning classifiers and use a majority vote or the average predicted probabilities (soft vote) to predict the class labels. Such a classifier can be useful for a set of equally well performing models in order to balance out their individual weaknesses. | ★「作りが違うものを組み合わせて、弱点を打ち消し合う」という考え方の根拠。 |
| 5 | [スタンフォード哲学百科事典「Jury Theorems」（コンドルセの陪審定理）](https://plato.stanford.edu/entries/jury-theorems/) | 【本文】 | 2 | Unconditional Independence (UI): The individual correctness events R1, R2, ... are (unconditionally) independent. / Unconditional Competence (UC): The (unconditional) individual correctness probability P(Ri) - the general competence - exceeds 1/2 and is the same for all individuals i. | ★多数決が効く条件は2つ＝①1本ずつが半分より当たる ②間違い方が独立している。 |
| 6 | [同上](https://plato.stanford.edu/entries/jury-theorems/) | 【本文】 | 2 | Common causes create correlations. / undermine diversity and reinforce tendencies and errors | ★条件が崩れると何が起きるか＝共通の原因があると多様性が損なわれ、間違いを強め合う。同じものを測る判定を並べて多数決を取ると、精度は上がらず悪くなる。 |

### 開けなかったもの（1件）

| # | 出どころ | 理由 |
|---|---|---|
| 1 | [arXiv 2205.04216「Forecast combinations: an over 50-year review」](https://arxiv.org/abs/2205.04216) | PDF の本文が取り出せない（要旨だけ取れた） |

## 12-3 社内の正本に既に在った答え（3件）

**★2026-08-29 の調べで分かったこと＝分類の切り方の答えは、外を調べる前から社内に在った。**

| # | 出どころ | 級 | 逐語 | うちにとっての意味 |
|---|---|---|---|---|
| 1 | indicator_combination_kb.md 法則1（20-29行） | 【正本】 | Every indicator belongs to one of four categories: trend, momentum, volume, or volatility. Combining two indicators from the same category doubles the noise, not the signal.（excavo） | 相場の指標でも「同じ系統を重ねると雑音が増える」と書かれている。 |
| 2 | indicator_combination_kb.md 法則6（90-103行） | 【正本】 | 法則1と2は「人が付けた系統の札」で重複を防ぎます。粗いです。／ ADX と DI差 は同じトレンド系ですが、見ているものが違います（強さと向き）。／ RSI9 と RSI21 は同じオシレーター系ですが、動きが違います（反応の速さ）。／ 実データで動きの重なりを測れば、札に頼らずに重複を落とせます。系統の札は最初のおおまかな仕分け、実データの相関が本番です。 | ★分類の切り方の答え。系統の札だけで重複を決めない。最後は実データで測る。★測る期間は値決め窓だけ（H2・H8）。 |
| 3 | indicator_combination_kb.md §2（109-121行） | 【正本】 | ★ADX は「トレンド」にも「相場の状態」にも答えます。系統で分けると、この違いが消えます。 | ★1つの指標が2つのことを見ていることがある。系統の札1枚では、その違いが消える。 |

## 12-4 場面ごとの相場の法則40件を、共通の型に畳めるか

**§11 の場面ごとの法則40件（レンジ10・上げ10・下げ9・スパイク6・変わり始め5）が、場面をまたぐ共通の骨格に畳めるかを1件ずつ照らした。★これは CC の分類であって、外の文献がそう言っているのではない。**

**結果＝40件のうち 33件が10の型に畳めた。畳めなかったのは 7件。**

★正本自身が3か所で「鏡像」と書いている＝D1「（U1 の鏡像）」／D6「U4 の向きを逆にしただけ」／D7「U6 の向きを逆にしただけ」／11-4 の末尾「下げは『上げの鏡像＋D5』で、下げ特有の別系統は見つからなかった」（743・748・749・753行）。

| 型 | 骨格（何を測るか） | 畳める相場の法則 | 場面ごとに変わるもの |
|---|---|---|---|
| 1 | トレンドの強さの水準 | U2前半・D2前半・R5・R10の1軸目 | 上か下か（上げ下げ＝上／レンジ＝下） |
| 2 | 向き（DI差の符号・傾きの符号・終値と移動平均の上下・Supertrend の札） | U2後半・D2後半・U3・D3・U4・D6・U5 | 符号（プラスかマイナスか） |
| 3 | スイングの並び（切り上げ・更新・破断） | U1・D1・U7・U9・T1 | 向き（切り上げか切り下げか）と使い方（成立か解除か） |
| 4 | チャネルの抜け（直近N本の最高値・最安値） | U6・D7 | 上抜けか下抜けか |
| 5 | 基準になる値幅と、その中の位置 | R1・R7・U8 | 何を基準の幅にするか（帯か、直前の上昇か） |
| 6 | ばらつきの水準（BB 幅・ATR% の広い狭い） | R6・S6・R10の2軸目 | 狭い側か広い側か |
| 7 | 1本の動き ÷ ふだんの動き | S1・S2・S4 | 閾値の高さ |
| 8 | 多時間軸の一致 | R3・D4・T3（共通 C4 と同じ） | どの足の組か・重み |
| 9 | 判定の安定（連続本数・入る線と出る線を別に） | R4・U10・D8（共通 C6 と同じ） | 本数・線の間隔 |
| 10 | 変化を見る（水準でなく傾き・急拡大） | T2・T5・S6 | どの指標の変化か |

### 畳めなかった7件（理由つき）

| 相場の法則 | 中身 | 畳めない理由 |
|---|---|---|
| D5 | 下向きのばらつきで測る | 下げ特有の物差し。上げ側に鏡像が無い |
| D9 | かたまりに名前を付ける手順 | 判定の法則ではなく、分けた後の名付けの手順 |
| R9 | 測るもの3つ | 測る側の物差し。判定を組み立てる法則ではない |
| S3 | 出来高スパイク | 材料が0件で、いまは書けない（§11-7 の穴1） |
| S5 | ニュース由来の出来高は短命 | 同上 |
| R8 | レンジ＝上げの否定を含める | 場面と場面の関係。型ではなく、場面どうしのつながり |
| T4 | 「いまどれか」と「変わり始めたか」は別の判定 | 場面をまたぐ作法。型に畳むのではなく、共通の法則へ昇格させるべき |

## 12-5 数の実測（9件・全部 プログラムで数えた）

| # | 何を数えたか | 結果 | 出どころ |
|---|---|---|---|
| 1 | regime_detection_kb.md §11 の法則 | 50件（共通10・レンジ10・上げ10・下げ9・スパイク6・変わり始め5） | 665-788行を機械で数えた |
| 2 | そのうち engine_tuner の設定ファイル composition_rules_src.json に入っているもの | 7件（scene_rules の K-1〜K-7）。入っていないのは43件 | 実測 |
| 3 | 法則の根拠の級 | 本文23・正本13・要約8・実装6・別AI 5（1件に複数付くことがある） | 694-775行を機械で数えた |
| 4 | 「相場の何を見ているか」の一覧 | 8件（question_map）。★付いているのは部品だけで、法則には付いていない | composition_rules_src.json |
<!-- COUNTS_START gen_materials.py --write が実物から書き出す＝手で書き換えない -->
| 5 | 指標の種類 | **257種類**（engine_tuner が選べる **139**／選べない **118**） | materials.md の「engine_tuner が選べる指標の種類」の行 |
| 6 | 材料の一覧の行 | **262件**（在る。ほかに「入れない」45件） | materials.md の一覧 |
| 7 | パラメータまで展開した部品 | **555件**（＋別枠 7件＝**562**） | signal_families.json の parts と extra_parts |
| 8 | ★562 に膨らむ理由 | ADX7・ADX14・ADX21 のように、同じ指標のパラメータ違いを別々に数えているため | 部品の名前の実測 |
<!-- COUNTS_END -->
| 9 | ta の43種に限ったとき残るもの | 種類64・部品135。法則が名指しする分を足して、目安 約70種類（部品 約150） | session_worklog_20260827.md §59 |

## 12-6 「実際にレンジだったか」の正解の作り方（外の実例）

**調べた日**＝2026-08-29（71回目・M2-A-1）

**調べた理由**＝「実際にレンジだったか」の正解の印（ラベル）を、外はどう作っているかを確かめるため。まこさんの承認＝12478b53a6d9abfa。

**調べた問い**
1. レンジをどう定義しているか。
2. 正解のラベルをどう作っているか。
3. 正解が目に見えないものを、どう採点しているか。
4. 先を見る本数（ホライズン）をどう決めているか。

### 一次ページを開いて取った逐語（10件）

| # | まとまり | 読み込ませる法則（何をしているか） | 級 | 逐語（英語のまま） | 開けた場所 |
|---|---|---|---|---|---|
| 1 | レンジは「トレンドの否定」として定義されている | [連続トレンド＝隣り合う山と谷の変動幅が閾値 ω を超えたとき。超えなければ「通常の変動」＝トレンドなし。レンジを直接 定義せず、トレンドの否定として置く](https://pmc.ncbi.nlm.nih.gov/articles/PMC7597331/) | 【本文】 | the continuous trend was defined as the fluctuation amplitude between the two adjacent peak and trough points exceeding the given threshold parameter omega, otherwise the fluctuation was considered a normal fluctuation without a continuous trend. | Section 2.3 |
| 2 | レンジは「トレンドの否定」として定義されている | [横ばい＝上げでも下げでもない、残り全部（VIX の分位と3ヶ月のトレンドの向きで上げ下げを決め、それ以外を横ばいにする）](https://arxiv.org/html/2506.06356v1) | 【本文】 | Market regimes are defined based on volatility levels and trend directions: Bull Market (Low Vol): VIX < 20th percentile, positive 3-month trend; ... Sideways Market: All other periods | Section V-C |
| 3 | 正解ラベルの作り方 | [閾値は絶対の数字で置く（中央値で半分に切らない）。omega=0.15＝15% 動いたらトレンド。試した範囲は 0.05〜0.25。窓の長さ lambda=11](https://pmc.ncbi.nlm.nih.gov/articles/PMC7597331/) | 【本文】 | a suboptimal parameter value omega = 0.15 was chosen instead and the average value ranged from 0.05 to 0.25. Therefore, if the price rose or fell by more than 15%, it would be regarded as an upward or downward trend / The sliding window parameter lambda was set to 11 in this paper | Section 4.1・2.2.1 |
| 4 | 正解ラベルの作り方 | [短い先を見て今と比べるやり方は、短期のでたらめさを拾う＝この論文が「連続トレンド」を作った理由](https://pmc.ncbi.nlm.nih.gov/articles/PMC7597331/) | 【本文】 | financial time series data are typically non-linear with obvious short-term randomness. Therefore, these labeling methods have not captured the continuous trend features of financial time series data | Section 1 |
| 5 | 正解ラベルの作り方 | [3つに分けるとき、真ん中に「どちらでもない」の帯を置く（0.4〜0.6 が Neutral）。★先の本数 n の選び方は書いていない](https://ar5iv.labs.arxiv.org/html/1907.03010) | 【本文】 | Class 0: %Q>=0.6 means Up; Class 1: 0.4<%Q<0.6 means Neutral; Class 2: %Q<=0.4 means Down / N bars Up/Down: Classifier on Ct+n>Ct | Section 6 |
| 6 | 正解が目に見えないものを、どう採点しているか | [場面は目に見えないものなので、①期間を分けて確かめる ②正解が既知の合成データを作って混同行列で測る。合成の作り方＝AR(1) 係数0.9・正規化して 0〜1・0.7 超を高ボラ・高ボラ期は誤差項を3倍。★誤りのコストは左右で違う](https://ar5iv.labs.arxiv.org/html/2104.03667) | 【本文】 | Since market regimes are latent unobservable processes, the detected regimes should be validated in an out-of-sample framework. / classifying a highly volatile regime as a calm one is a more costly misclassification compared to classifying a calm regime as a highly volatile one. | Section 4 |
| 7 | 正解が目に見えないものを、どう採点しているか | [正解ラベルの付いたデータで先に確かめてから、ラベルの無い実データへ移る。窓の選び方はデータの性質しだい](https://ar5iv.labs.arxiv.org/html/2306.15835) | 【本文】 | In Section 5, we evaluate our clustering methodology on labelled data so as to verify our class assignments before moving onto unlabelled data. / The choice of h = (h1, h2) is largely dependent on the characteristics of the data one is working with. | Section 1.4・Remark 3.4 |
| 8 | 先を見る本数（ホライズン）の決め方 | [★推論したい先の本数と、教える先の本数は、一致させるのが最適とは限らない。中間の本数がいちばん効く場合がある。推奨＝本数を学習で決めさせる](https://arxiv.org/html/2602.03395v1) | 【本文】 | Minimizing training error on the canonical target horizon t+Delta does not guarantee optimal generalization on t+Delta. Contrary to intuition, the most effective supervision signal is often misaligned with the inference target, residing at an intermediate horizon t+delta (where delta != Delta). | Introduction・Section 3.4・4 |
| 9 | 先を見る本数（ホライズン）の決め方 | [本数と閾値を、ラベルの割合が釣り合うように探索して選ぶ（5〜29日 × 7〜15%）。★保有期間と結びつける記述は無い（開いて確かめた）](https://arxiv.org/html/2504.02249v2) | 【本文】 | To ensure balanced label proportions during training, we optimized the labeling parameters by testing various combinations of time horizons (5-29 days with a step size of 1 day) / percentage thresholds (7%-15% with a step size of 1%) | Section III-B |
| 10 | 先を見る本数（ホライズン）の決め方 | [本数は「短い揺れを構造の変化と見なさない」長さに合わせる（この論文は月次を選んだ）](https://ar5iv.labs.arxiv.org/html/2104.03667) | 【本文】 | We choose to detect regime switches at monthly frequency to allow the underlying mean-reverting data generating processes to have deviations that are not regarded as structural breaks. | Section 3 |

### 開けなかったもの（2件）

| # | 出どころ | 理由 |
|---|---|---|
| 1 | [Poterba & Summers「Mean Reversion in Stock Prices」（分散比の定義とホライズンの選び方）](https://papers.ssrn.com/sol3/delivery.cfm/nber_w2343.pdf?abstractid=227278) | HTTP 403 |
| 2 | [同じ arXiv 論文2本の PDF 版（2104.03667 と 1907.03010）](https://arxiv.org/pdf/2104.03667) | PDF を文字に直す道具が この環境に無い（pdftoppm is not installed）。★HTML 版（ar5iv）で開き直して逐語を取った |

### ★検索の要約が、本文と違っていた1件（恒久の決まり43番の実例）

**検索の要約に出た文**＝dynamic volatility threshold ／ square root of time rule ／ sideways conditions are identified when the absolute value of cumulative returns over k days does not exceed the threshold

**本文を開いた結果**＝その式は書いていなかった。本文の定義は「Sideways Market: All other periods」＝残りもの。

★検索の要約だけで表を書いていたら、実在しない定義を1件 載せていた。恒久の決まり43番（検索結果の要約で設計を書かない）が要る理由の実例。

### いまの印と、外の作り方の違い

| # | いまの印 | 外 | 何が変わるか |
|---|---|---|---|
| 1 | 窓の中央値で切る（er >= er.median()） | 絶対の数字で切る（omega=0.15＝15%） | 中央値だと、どの期間でも必ず半分がトレンド・半分がレンジになる。「トレンドばかりの月」「レンジばかりの月」を区別できない。絶対値なら区別できるが、でたらめな判定の基準線が 50% に決まらなくなる（いまの長所が消える） |
| 2 | 真ん中の「どちらでもない」帯が無い（中央値のすぐ上と、すぐ下が、別の札になる） | 真ん中に帯を置く（0.4〜0.6 は Neutral） | 帯を置くと、境目のすれすれの所を採点から外せる。いまは境目のすれすれも「外した」と数える |
| 3 | 正解の印そのものが正しいかを確かめる仕組みが無かった | 正解が既知の合成データを作って、混同行列で確かめてから実データへ移る | ★2026-08-29 に足した＝合成データの検査 N1〜N4（observe_diag.py）。実測＝正しい版は3つの札とも一致率 1.000／わざと壊した版は 0.000 |

### うちが決めたこと

**まこさん決定**＝2026-08-29・逐語「１と２は今のままでOK」

**中身**＝①正解データの作り方＝変えない（先の本数を見て、まっすぐ進んだ割合が窓の中央値以上なら「トレンド」）②先を見る本数＝変えない（24本＝2時間・288本＝24時間）

**判断の材料**＝レンジの札とトレンドの札の中央値が 0.218 対 0.612（差 +0.393）。言葉の意味と食い違う区間（比 0.5 以上）はレンジの札の 2.3%、0.9 以上は 0本。24本と288本で中央値が同じ。

M2-A-1 で CC が立てた見立て（中央値で切るのが弱点／本数の下限を下げるべき）は、どちらも数字で支持されなかった。

## 12-7 この調べで見つかった穴（2件・正直に書く）

### 穴1｜G3 の「同じ役割に、同じ系統の指標は1本まで」の『1本』に、外の根拠が無い

**中身**＝engine_tuner_exec.py:513 の決まり。2026-08-29 に外を4件 開いて調べたが、『同じものを測る指標を重ねるな』という考え方は在っても、本数の上限を書いたページは1件も無かった。社内の法則3 も『2〜4本』と『3〜5本』で出典が食い違い、2〜5本を探索の範囲にすると決めてある。

**どうするか**＝★本数を1に固定する根拠が無い。範囲で探す形にすべきか（恒久の決まり42番）は まこさんが決める。next_step.md §5 の11番と同じ件。

### 穴2｜予測の組み合わせと機械学習の資料は「モデル」の話で、相場の場面判定のロジックを組み合わせた実証ではない

**中身**＝B の一次ページ3件は、予測モデルや分類器を組み合わせた話。場面の判定ロジックを束ねた実証は、2026-08-29 の調べでは一次で見つけていない。

**どうするか**＝考え方の裏づけとして使う。うちのデータでの証明ではないので、M2-G で実データの重なりを測って確かめる。
<!-- KB_FINDINGS_END -->
