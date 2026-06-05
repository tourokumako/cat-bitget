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

---

## 6. Entry と Exit は連動する（独立に最適化しない）★2026-06-05 核心

出典: まこさん検索（Binance Academy / FOREX.com 要旨）＋ WebSearch（[Triple Barrier de Prado](https://deepwiki.com/quantopian/mlfinlab/6.3-triple-barrier-method) / [MTF pullback](https://tradeciety.com/how-to-perform-a-multiple-time-frame-analysis) / [joint entry-exit](https://www.quantifiedstrategies.com/entry-and-exit-rules-trading-plan/)）

- **Entry と Exit は強い相関。独立に最適化しない**。勝率とリスクリワード(RR)はトレードオフ：**期待値 = 勝率 × 平均利益 − 敗率 × 平均損失**。Entry 精度が上がると損切りを狭くでき RR↑／Entry 精度が低いと損切り広く→TP 遠く→勝率低下。
- **順張り（P23＝戻り売り）**: Exit は「トレンド終了まで引っ張る」（伸びを待つ）。Entry が遅れる（ダマシ回避）と利幅が狭まり RR が変わる。
- **逆張り（レンジ）**: Exit は反対端で即決済・損切りタイト（コツコツドカン回避）。
- **★ ラベル（"伸びた／勝ち" の定義）＝ Exit が決める**（Triple Barrier・de Prado）: TP・SL・時間 の3バリアのどれに先に当たるかでラベル化。**Exit 設定（TP/SL/時間）を変えるとラベルが変わる → 入口判別の学習結果も変わる**。＝入口判別は Exit を決めて初めて学習できる＝**Entry/Exit はセット**（これが「セットで調整」の数学的な意味）。
- **入口判別（戻り売りが "伸びる" か）に効く材料**: ① **MTF コンフルエンス**（上位足 15m/30m/1h/4h の下降の揃い・揃うと質↑/件数↓＝最有力・V9 は 5m 単独で欠落＝伸びしろ） ② トレンド強度（ADX・bb傾き） ③ 戻りの深さ・位置（stoch・RSI・バンド内位置） ④ ボラ（ATR%） ⑤ モメンタム（ret_5・rsi_slope）。
- **検証順序**: **Entry/Exit をセットで調整して土台を固める → その後 add（増し玉）を検証**。add は土台の上の増し玉なので、土台が動くと評価できない（まこさん 2026-06-05）。

### 6.1 ML化のアプローチ 2路線（まこさん 2026-06-05 共有・読込）

- **B 教師あり（＝現方針・ratchet で採用中）**: Entry 条件から「次の逆シグナル／損切りまでの**最大利益幅**（例 ATR の N 倍）」をラベルに XGBoost/LightGBM（時系列は LSTM 等）。＝我々の **MFE/payoff 予測・Triple Barrier と同一路線**。データ量に合い 1 手ずつ ratchet で回せる。
- **A 強化学習（RL）**: 市場=環境／AI=エージェントで、状態(価格・SMA・RSI・ボラ)→行動(Buy/Sell/Hold)→**報酬(実損益 or Sharpe・コスト/DD はペナルティ)** を直接最適化（PPO・Stable-Baselines3・OpenAI Gym）。**Entry/Exit/add を統合最適化する本命**だが、**小データ過学習リスク大**（純 net 報酬は少数大勝ちに過剰適合 → Sharpe 等リスク調整報酬で緩和）→ **将来候補**（土台が固まり統合最適化したくなったら）。
- **共通の必須設計**: ① MTF 特徴量（1h/日足のマクロトレンドでダマシ減）② **取引コスト（手数料/slippage/funding）を報酬・シミュに必ず組込み**（高頻度の手数料負け防止）③ regime（ボラ）切分けを状態変数に入れ過学習防止。出典: まこさん検索（OpenAI Gym/Stable-Baselines3/PPO）＋ [RL trading](https://blog.quantinsti.com/reinforcement-learning-trading/) / [Sharpe報酬 arXiv2506.04358](https://arxiv.org/pdf/2506.04358)。
