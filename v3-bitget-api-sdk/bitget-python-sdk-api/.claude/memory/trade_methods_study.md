# trade_methods_study.md — トレード手法 → ML設計ノート（最低限・都度深掘り前提）

作成: 2026-06-04
**方針（まこさん×CC 合意・2026-06-04）**: 本ノートは**ML設計の意思決定に効く知識に絞る**。トレーダー向けの辞書的網羅（全パターン・計算式の細部・信頼度ランキング）は載せない。理由＝CC は都度 WebSearch で深掘りできる構造で、細部を静的に抱えると technical KB のように死蔵して活かせない（今日それで失敗）。**個別手法の細部は、ML 設計でその手法を実装する段になったら都度検索する**。本ノートは「どこを深掘りすべきか」の地図。

絞る4点: ①大分岐（regime最上位） ②各手法の役割と効く局面 ③確認の原則 ④★ML設計への落とし方。

---

## 1. 最上位の大分岐：トレンド か レンジ か（＝regime）

- テクニカルは大きく **順張り（トレンド系）** と **逆張り（オシレーター系）** に二分。**効く局面が正反対**：順張り＝トレンドで効きレンジでダマシ／逆張り＝レンジで効きトレンドでダマシ。
- **同じ指標でも局面で意味が逆転**：BB のバンド端タッチ＝レンジなら反転/トレンドなら継続。Stoch の売られすぎ＝レンジなら反転/上昇トレンドなら健全な押し目。
- → **ML設計の最上位に「トレンド/レンジ＋方向の判定（regime）」を置き、局面別に手法・閾値を切り替える**。これが全ての土台。（v1 はこれが無く全bar無差別＝負けの根本）

---

## 2. 各手法の役割と効く局面（一覧・細部は都度検索）

| 手法 | 系統 | 何を見る | 効く局面 | 主なダマシ |
|---|---|---|---|---|
| ローソク足 | 中立(素材) | 1本の勢い・反転の形（実体符号/サイズ・上下ヒゲ） | サポレジ＋トレンド文脈で | 単独・レンジ中央では無意味 |
| 移動平均(MA) | 順張り | トレンド方向・動的S/R・クロス | トレンド | レンジで whipsaw |
| ボリンジャーバンド | 両用 | ボラ拡縮・バンド内位置(%B) | レンジ＝逆張り/トレンド＝順張り | バンドウォークを反転と誤認 |
| 一目均衡表 | 順張り | 雲＝動的S/R＋方向（3要素確認） | トレンド・高時間足 | レンジ・価格が雲の中 |
| RSI | 逆張り | 買われ/売られすぎ・ダイバージェンス | レンジ | 強トレンドで70/30に張り付き |
| MACD | 順張り寄り | トレンド＋モメンタム（クロス/ヒスト/ダイバージェンス） | トレンド | 遅行・レンジでダマシ |
| ストキャス | 逆張り | レンジ内位置(%K/%D)・クロス | レンジ／トレンドの押し目 | トレンドで張り付き |
| フォーメーション | 反転/継続 | チャートの形・ネックライン/ブレイク | 出来高確認が伴う時 | 出来高なきブレイク |

各手法の裏取りソース（深掘りの入口）: MA=[Granville/MA crossover](https://www.luxalgo.com/blog/2-moving-average-crossover-strategies-explained/) / BB=[FXEmpire](https://www.fxempire.com/education/article/bollinger-bands-trading-strategies-how-to-read-volatility-identify-market-regimes-and-trade-with-a-statistical-edge-1585260) / 一目=[Investing.com](https://www.investing.com/academy/analysis/using-ichimoku-cloud-for-trend-analysis/) / RSI=[Changelly](https://changelly.com/blog/rsi-relative-strength-index-in-crypto/) / MACD=[MindMathMoney](https://www.mindmathmoney.com/articles/understanding-the-macd-indicator-macd-line-signal-line-histogram-crossover-and-zero-line) / Stoch=[OANDA](https://www.oanda.com/us-en/trade-tap-blog/trading-knowledge/mastering-stochastic-oscillator-trading-strategies/) / 辞典=[StockCharts](https://chartschool.stockcharts.com/) / 信頼度統計=[Bulkowski](https://www.thepatternsite.com/CandlePerformers.html)

---

## 3. 確認の原則（どの手法も単独では弱い）

- **コンフルエンス**＝複数の根拠（手法）が同じ価格で重なると確度が跳ね上がる。
- 確認材料：**場所（サポレジ）・上位足の一致（MTF）・出来高・他指標・終値でのブレイク**。
- 実戦ルール：3つ以上の green flag が揃って入る／形だけで入らず**価格の確認（高安ブレイク）を待つ**。

---

## 4. ★ML設計への落とし方（このノートの核心）

トレード手法の知識を、ML pipeline（8工程・段構造）のどこに・どう落とすか：

| トレード手法の知識 | ML設計への落とし方（工程・形） |
|---|---|
| ①大分岐（トレンド/レンジ） | **工程1 regime判定を最上位**に。トレンド/レンジ＋方向を出力し、後段が局面別に切り替える |
| 各手法の役割（方向/勢い/位置/形） | **特徴量**。既に parquet にある（MA乖離・RSI・Stoch・BB・MACD・wick/body比・streak）。複数期間×MTF で渡す |
| 順張り/逆張りの局面依存 | regime を特徴量に入れ、木が「局面×手法」を枝で学ぶ／さらに局面別に別モデル分割（ratchet候補） |
| ③確認・コンフルエンス | **工程2 候補生成（cascade段1）**：複数手法が揃った所だけ候補化（高recallで絞る）→ML段。v1 に欠けていた段 |
| 終値ブレイク・出来高確認 | エントリー条件＋特徴量（ブレイクフラグ・出来高 z-score） |
| ダイバージェンス | 特徴量（価格と指標の逆行フラグ・既に div_* あり） |
| フォーメーションのターゲット(measured move) | **Exit/TP 設定**の参考（後段レバー・将来） |
| 個別パターンの信頼度（Bulkowski等） | 採用時に都度検索（本ノートに抱えない） |

**今日の結論と一致**：v1 は工程1（regime）・工程2（候補生成）・確認を飛ばし、全bar無差別に工程3だけをやった＝8軸欠落。次の戦略は **regime最上位 → 局面別の手法で候補生成（コンフルエンス）→ 確認 → ML判定 → Exit** の段構造で組む。

---

## 5. 細部が必要になったら（都度深掘りの作法）

個別手法を実装する段で、**その手法だけ** WebSearch で深掘りする：計算式の厳密版・パラメータの選び方・信頼度統計・cat-bitget 5m での実例。本ノートは静的辞書ではなく、「次に何をどこまで調べるか」を決める地図として使う。
