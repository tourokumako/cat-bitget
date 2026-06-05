# entry_exit_relationship_kb.md — トレードにおける Entry と Exit の関係性 ナレッジ

作成: 2026-06-05 (CC・設計統合担当)
位置付け: **Entry（入口）と Exit（出口）が NET（純益）に対してどう連動するかの知識正本**。cat-bitget（BTC 5m 先物・P23=下降トレンドの戻り売り SHORT・期待値ベースで add数/ポジ数/TP幅/TimeExit/SL を動的に変えて NET 最大化する方針）の設計判断に直結する。`trade_analysis_methods_kb.md`（結果データの読み方）と対をなし、本書は「Entry/Exit/サイズをどう一つの設計として組むか（原理）」を担当する。
出典: WebSearch + 一次文献（Lopez de Prado AFML / Hudson & Thames / 各トレード教育ソース）で検証済みの 65 要点を統合。confidence は元検証どおり high / medium を明記し、medium は弱い扱いとして但し書きを付す。

> ⚠️ **読み方の約束**: confidence high = 複数独立ソースで逐語〜数値レベル一致。confidence medium = 方向性は支持されるが特定数値・特定 framing が単一ソース依存、または非対称の向き等で反証あり。**medium の主張は設計判断の主柱にせず、補助・要再検証として扱う**。

---

## §1 NET を決めるのは期待値 — Entry も Exit も単独では足りない

**核心**: 1トレードあたりの利益は `Expectancy（期待値）= (勝率 × 平均利益) − (負け率 × 平均損失)`。Entry（勝率）と Exit/サイズ（平均利益・平均損失の幅）の**積**で決まり、どちらか一方だけでは NET は決まらない。

- この式は複数の独立ソースで逐語一致（Orbex / TradeZella / Babypips / Trademetria / PineConnector）。実例も整合（勝率50%・$200/$100 で +$50/trade、勝率40%・$450/$200 で +$60/trade）。**confidence high**。
- 勝率（Entry 側）を上げても、金額差（Exit/サイズ側）を広げても NET は伸びるが、**両者を「組」で評価する**のが正しい（win rate alone より両方を見よ）。
- 期待値が負なら、Entry の精度がいくら高くても利益は出ない。だから**予測対象は勝率でなく net 金額**（勝率と R:R の両方を内包する量）に置くのが整合的。
- ⚠️ プロジェクト内推論（外部裏取り対象外）: 「手動が net 黒字なら ML net マイナスは枠組み側の不具合」。期待値式が正なら論理は成立するが、これはソース由来ではなくプロジェクト前提（cc_role §1.7 / entry_fix_6axis_gate と同旨）。

出典:
- https://www.tradezella.com/blog/trading-expectancy
- https://journalplus.co/learn/guides/win-rate-vs-risk-reward/
- https://protraderdashboard.com/blog/expectancy-formula-trading/

---

## §2 必要勝率は R:R で機械的に決まる — Exit 幅が必要勝率を動かす

**核心**: 損益分岐の必要勝率は `1 / (1 + R:R)`。1:1=50%、1:2=33.3%（端数切上げ 34%）、1:3=25%。**Exit の取り幅（利確/損切）を変えると、同じ Entry でも必要勝率が連動して変わる**。

- 公式・具体数値とも LuxAlgo / TradeZella / 各 calculator で完全一致。**confidence high**。
- 「普遍的に良い勝率」は存在せず、平均 R:R 次第。40%勝率×1:3 が 80%勝率×1:0.5 に勝つ。
- 利確幅を広げると R:R は上がるが勝率は下がる、狭めると勝率は上がるが平均勝ちが縮む = **勝率と R:R は逆相関**。どちらが優れるかは expectancy だけが判定する（40%@3:1 が 60%@1:1 に勝つ算術は独立再現済み）。

出典:
- https://www.luxalgo.com/blog/risk-reward-ratio-vs-win-rate-key-differences-2/
- https://journalplus.co/learn/guides/win-rate-vs-risk-reward/
- https://www.goatfundedtrader.com/blog/take-profit-vs-stop-loss

---

## §3 効くのは「計画 R:R」でなく「実現 R:R」 — 出口の実約定が利益を直接動かす

**核心**: 期待値に入るのは事前に計画した R:R ではなく、**実際に達成した R:R（R-multiple）だけ**。出口の実約定が Entry 配置と同等に1トレード利益を直接動かす。

- JournalPlus が「R:R = 事前計画 / R-multiple = 事後実績で、realized の数字が収益性を決める」と明示。realized-to-planned 比 0.8 以上が良好・0.6 未満は execution に深刻な問題、という定量 benchmark あり。**confidence high**。
- 含み益（MFE ピーク）でなく**実約定で測る**のが正しい。予測対象を net 金額（実現 R）に置くべき理由でもある。
- ⛔ cat-bitget の Prime Directive と整合: MFE 等の保有期間中最大値は本番推論時 t で取得不能。ラベル・評価は**実出口**で作る（trade_analysis_methods_kb §3 / false_positive §0-1）。

出典:
- https://journalplus.co/metrics/average-rr/

---

## §4 出口効率（MFE 捕捉率）の改善は Entry を変えずに NET を伸ばす

**核心**: 「利益が確定するのは出口であって入口ではない」。同じ Entry のまま MFE 捕捉率（実現益 ÷ 含み益ピーク）を上げるだけで NET が大きく動く。**Entry を変えず Exit 側で稼ぐのが最も費用対効果が高い**。

- 方向性・機序は **high**（tradesviz / traderssecondbrain / journalplus / trademetria が独立確認）。リテールの多くは勝ちトレードの MFE の 40-55% しか取れておらず、捕捉率を 60-75% へ上げると戦略・頻度・追加リスクなしで NET 改善。良好戦略の出口効率ベンチは 65-80%、60% 未満は「早すぎる利確で利益を失っている」診断。
- ⚠️ **数値は弱め扱い**: 「40%→65% で NET P/L 50-80% 改善」という具体パーセンテージは引用元（traderssecondbrain）固有で、独立ソースが示す改善幅は 30-60%。方向は high だが**上限 80% は楽観なので過度な期待をしない**（この具体数値部分のみ medium 相当）。
- 出口は「昨日決めた固定 TP/SL」でなく「今市場が何をしているか」に応答すべき（ATR・出来高・価格構造）。1.5R で明確な反転サインが出ているのに「ルールだから」2R まで持つのは勝ちを負けに変える行為。

出典:
- https://www.tradesviz.com/blog/trade-exit-strategy/
- https://traderssecondbrain.com/guides/mae-mfe-analysis

---

## §5 Entry の質は MFE/MAE 比で測れ、その質に応じて Exit を変える

**核心**: Entry タイミングの質は MFE/MAE 比で定量化できる。**強い Entry ほど Exit を遠くに置いて伸ばし、弱い（順行しない）Entry は早く切る**条件分岐が NET を最大化する。

- **confidence high**（tradewink / quantifiedstrategies / optimusfutures が独立確認）。MFE/MAE 比が継続 2:1 超で良好、3:1 で強セットアップ、1:1 未満は悪い Entry / 誤った仮説。
- 中核の非対称性: **勝ちは低 MAE（クリーンな Entry）・負けは高 MAE（遅延 Entry / 不適切な無効化）**。効くときは本当に効き（高 MFE）、効かないときは一度も順行しない（低 MFE）。
- 統計的有意性には設定あたり最低 30-40 件、恒久変更には 80-100 件が必要（§13 と整合）。
- ⛔ cat-bitget 注記: MFE/MAE は**出口較正の診断材料**には使えるが、**ラベルそのものには使わない**（実出口 = Triple Barrier で作る・§9 参照）。

出典:
- https://traderssecondbrain.com/guides/mae-mfe-analysis

---

## §6 勝ちは伸ばし負けは切る（非対称） — リテールは逆をやっている

**核心**: NET 最大化には「勝ちを伸ばし負けを早く切る」非対称設計が必要。リテールはこの逆（勝ちを早く確定し負けを引っ張る）をやり、MFE 捕捉率を 30-45% に押し下げている。

- **機序・方向性は high**。Disposition Effect（勝ちを早く売り負けを長く持つ）は学術的に確立（Shefrin & Statman 1985 / Odean 1998 が 1万口座で実証・勝ちを負けより約1.5倍売りやすい・年率 3-5% リターン低下）。原因は損失回避。Wikipedia / Decision Lab / Princeton(Xiong) が独立確認。
- ⚠️ **特定数値は弱め扱い**: 「MFE 捕捉 30-45%」という具体%は実務ブログ系の推定で peer-reviewed でない。機序と方向性は high だが**特定%はやや弱い**。
- Paul Tudor Jones は勝率 20% でも 5:1 RR で損益分岐に達する。非対称 RR がエッジそのもので、高勝率は前提条件でない。

出典:
- https://medium.com/@netpicks/run-the-winners-and-cut-the-losers-like-smart-traders-163632c29f42
- https://www.orbex.com/blog/en/2026/03/why-you-cut-winners-early-and-let-losers-run-rewiring-the-traders-paradox

---

## §7 Entry の性質ごとに Exit 哲学を変える — トレンド型は伸ばす・回帰型は早く確定

**核心**: Exit ルールは普遍でなく、Entry の edge 構造に合わせる。**高 edge のトレンド Entry は利を伸ばし、低 edge の平均回帰 Entry は素早く確定する**。

- **confidence high**（quantifiedstrategies / algohubb / robottraders / heygotrade が独立確認）。トレンドフォロー = 損切り早く + 利を伸ばす（トレーリング・保有は週〜月）。平均回帰 = 平均/レンジ中央で素早く利確（保有は時間〜日）。
- 非対称が一貫: 平均回帰 ≈ 勝率 60-85% で小さい勝ち + 稀な大負け / トレンドフォロー = 低勝率（30-45%）で外れ値主導の利益。
- スキャル/平均回帰型は高勝率が必要、トレンドフォロー型は勝率が低くても勝ちが数倍なら成立（35%勝率でも R:R 5 なら黒字）。**cat-bitget の Priority 別スタイル（MAX_ADDS=1 スキャル小勝ち vs 平均建値ポジ大勝ち）を Entry 性質に合わせて Exit 設計するのは定量的に裏付け**。

出典:
- https://www.quantifiedstrategies.com/mean-reversion-vs-trend-following/
- https://www.quantifiedstrategies.com/trading-exit-strategies/

---

## §8 出口ルールはレジームで使い分ける — トレンドはトレーリング、レンジは固定ターゲット

**核心**: 同じ出口でもレジームで最適解が反転する。**トレンドはトレーリングストップ、チョッピー/レンジは固定ターゲット**。Entry のレジーム判定が Exit 選択を規定する = Entry（レジーム）と Exit はセット設計。

- **confidence high**（BuildAlpha のバックテスト結果が明示・MarketsManners / TradeZella / LuxAlgo SuperTrend が独立確認）。**トレーリングは平均回帰/レンジ regime では単に弱いのでなく負の期待値**（Hurst > ~0.55 のトレンドでのみ有効）。だから出口を選ぶ前のレジーム分類が必須。
- 固定ターゲットは強トレンドで頭打ち、トレーリングはレンジ往復で早すぎる利確を誘発。
- ⚠️ 「混在は逆効果」は「不適合な出口を当てると逆効果」の意なら正しいが、「分割併用そのものが逆効果」と読むと反証あり（ハイブリッド = 一部固定 + 残りトレーリングは有効・§10 参照）。前者の意図で読む。

出典:
- https://www.buildalpha.com/stop-losses-complete-guide/
- https://www.quantifiedstrategies.com/trading-exit-strategies/
- https://propfirmplus.com/trend-following-vs-mean-reversion-trading-style/

> 補足（**medium・弱め扱い**）: 「トレンドフォロー=高ボラ / 平均回帰=低ボラ」というボラ軸の対応付けは、トレンド↔レンジの対応より弱い。一部ソースは逆（momentum=stable / mean-reversion=volatile）を述べ、ボラとトレンドは常には一致しない（チョッピー高ボラレンジが存在）。**ボラ軸での Exit 切替は主柱にしない**。出典: https://propfirmplus.com/trend-following-vs-mean-reversion-trading-style/

---

## §9 Triple Barrier — Exit 設定がラベル（予測対象）そのものになる

**核心**: Triple Barrier labeling では、ラベルは「利確・損切・時間の3バリアのうち最初に触れたもの」で決まる。**選んだ Exit 設定（TP/SL/time）が、Entry モデルが学習する予測対象そのものを規定する**。Exit 設定を変えるとラベルが変わる = Entry と Exit は分離できない。

- Lopez de Prado『Advances in Financial Machine Learning』(2018) 由来。上 = +1、下 = −1、時間バリア先着なら出口リターンの符号（または 0）。**confidence high**（mlfinlab / paperswithbacktest / quantreo / AXLFI が独立確認・「実トレード機構をミラーする」framing も一致）。
- **バリアはボラティリティ（k×σ）でサイズすべき**で固定%でない。`上 = Entry×(1+k×σ)、下 = Entry×(1−k×σ)、σ = 過去リターン標準偏差、k は通常 1-3`。較正不良のバリアは不均衡/ノイズだらけのラベルを生み NET を劣化させる。高ボラ Entry は出口を広く。**confidence high**（quantinsti / waylandz が公式逐語一致、De Prado は EWMA ボラ推奨）。
- **Exit は非対称に組める**: 利確と損切で別の倍率を使うのは Entry の質/期待値を Exit に埋め込む正当な方法。mlfinlab の `pt_sl=(2.0,1.0)` 等が「利益に余地を与えつつ損失を厳しく管理」と明示。高 EV Entry は SL に対し TP を広く正当化できる。**confidence high**。

出典:
- https://grokipedia.com/page/Triple-barrier_labeling （※直接 fetch 不可だが mlfinlab 等で robust に裏取り済）
- https://blog.quantinsti.com/triple-barrier-method-gpu-python/
- https://paperswithbacktest.com/course/triple-barrier-method

---

## §10 分割利確 + 残りトレーリングのハイブリッド — 「確実性」と「伸び」の両立

**核心**: 単一 TP でなく複数価格で段階的に利確（scale out）し、残りをトレーリングで伸ばすハイブリッドが、安全性と伸びを両立する NET 最大化の実務標準。

- **confidence high**（finveroo / chartingpark / FTMO / mindmathmoney / Kraken / IBKR が独立確認）。典型フレーム: 1:1 で初期リスク分を回収、主目標(1:2/1:3)で第2弾、残り 25-30% をトレーリングで延長捕捉。bracket order（Entry 時に SL+TP 同時設定）が professional standard。
- 早期確定が「勝ちポジを見る不安」を減らし残りを冷静に保持できる心理効果も複数ソースが明示。
- **トレードオフを意識する（重要 nuance）**: 部分利確は心理的安定・一貫性を生むが、満額がターゲットまで到達した場合に比べ EV を数学的に下げる（50%を1:1+残り2:1 = blended 1.5R vs 満額 2.0R）。ただし late-reversal stop-out を回避できれば実約定では partial が勝つこともある（EV 低下は無条件でなく満額到達前提）。**confidence high**。
- 拡張（論理的に妥当・claim 独自）: **入口の質が高いほど残し玉を厚く・トレーリング寄りに、低いほど早期固定利確に寄せる**連続調整。

出典:
- https://www.altrady.com/blog/crypto-trading-strategies/trailing-stop-loss-vs-take-profit
- https://www.metriclan.com/blog/partial-profit-taking
- https://www.marketdash.com/blog/trading-exit-strategies

---

## §11 出口は静的でなくトレンド健全性のサインで動的に締める/緩める

**核心**: 出口は Entry 時点の期待値だけで固定せず、保有中に更新される期待値（トレンド健全性）に応じて連続変更する。好調なうちは伸ばし、勢い枯渇の兆候でターゲットを締める = Entry-Exit 連動を保有期間中も継続。

- **confidence high**（複数の trend-exhaustion 系ソースが一致）。締めの兆候: 20日 EMA 割れ、MACD ベア転換、上昇日の出来高減退、RSI 50 割れ、ダイバージェンス。トレーリング 2×ATR は勢いが落ちたとき利益を守る。
- **ADX を「入口フィルタ」兼「出口モニタ」として両用**: ADX>25 でトレンド強 = 保有/add 延長、ADX が高位(40-50)からピークアウトして下向き = 参加者を失い勢い減衰の先行サインで利確/ストップ引き締め。**confidence high**（Fidelity / chartguys / capital.com 等が広く確認）。cat-bitget の results CSV は `adx_at_entry` を保持しており「伸びるか」判定に使える。
- ⚠️ 重要な但し書き: 健全なトレンドでも短期 pullback は普通。**単一兆候での過早な締めはノイズ。複数 confirm を前提にする**。

出典:
- https://zforex.com/blog/general-trading/what-are-exit-strategies/
- https://www.thinkmarkets.com/en/trading-academy/indicators-and-patterns/adx-indicator-how-it-works-trend-strength-signals-and-trading-strategies/

---

## §12 サイズは Entry の質（エッジ）から数学的に決める — Kelly と fractional Kelly

**核心**: ポジションサイズは勘でなく Entry の推定エッジ（期待値）から決める。**高エッジ Entry は大きく、低エッジは小さく、負期待値なら 0（見送り）**。実務では full でなく fractional Kelly（25-50%）。

- **confidence high**（AvaTrade / JournalPlus / TradersPost / astuteinvestorscalculus / matthewdowney 等が独立確認）。Kelly `f* = (bp − q)/b` は勝率 W とペイオフ比 R の両方を入力に、期待 log 富（幾何成長率）を最大化。エッジが消えたら f*≤0 = 「やめる合図」（見送り出力）。
- **fractional Kelly の根拠（数学的性質・rule of thumb でない）**: Half-Kelly は full の約 75% の複利成長を維持しつつドローダウン・分散を約半減。Full Kelly は DD 50-80%・約1/3の確率で資産半減で非現実的。実務標準は 25-50%（Quarter〜Half）。
- **非対称性も織り込む**: 同じ勝率でも対称ベットと非対称ベット（限定ダウンサイド・大アップサイド）では正解サイズが違う。確信が真に高く下方が限定されているとき「小さく張る」のが本当の誤り（ただし無謀に大きくでなく確信に応じ校正・過剰露出回避）。**confidence high**。
- ⚠️ **エッジ推定の誤差感度（特定数値は medium）**: 「勝率 5pt 下落で Kelly fraction 25%→8% へ約3倍スイング」「50-100 トレード必要」は方向・桁感は正しいが具体数値は出典依存。**fractional で抑える理由として使い、生数値は鵜呑みにしない**。

出典:
- https://journalplus.co/metrics/kelly-criterion/
- https://en.wikipedia.org/wiki/Kelly_criterion
- https://astuteinvestorscalculus.com/the-kelly-criterion/
- https://nycif.org/asymmetric-returns/

---

## §13 確信度（予測確率）に応じてサイズを連続的に変える — Meta-Labeling

**核心**: 方向予測（side）とサイズ決定（size）を分離し、二次モデルが「その Entry が成功する確率（confidence score）」を出力 → サイズに連続マッピングする。51% 予測と 91% 予測を同じサイズで扱う固定比率は確信度情報を捨てており非最適。

- **confidence high**（Wikipedia / Hudson & Thames / QuantConnect / MQL5 が独立確認）。Meta-labeling（別名 corrective AI）は Lopez de Prado (2017) 発。primary（方向・高 recall で訓練）と secondary（primary の予測が正しいかを予測）を分離。「動的にサイズ調整し false positive を抑制」。
- 標準マッピング: 符号付きベットサイズは p=0.5（base rate）で 0、極値で ±1 に飽和する線形。`Position = Confidence × Max Position`。高確信→大、低確信→縮小/見送り。
- ⚠️ **校正を挟む（重要補強）**: confidence 確率を生サイズに直接使わず、**結果分布で校正（calibration）してからサイズ化すべき**（pm-research 論文 "Calibration and Position Sizing"）。校正は固定サイジング法に特に効く。サイジング法（SOPS 等）は Sharpe / max drawdown で選ぶ = Entry→size マッピングを**リスク調整後 NET で評価**する。
- ⚠️ 微 nuance（medium）: 「precision を recall を犠牲にせず改善」は厳密には recall→precision のトレードオフが通常あり（言い回しのみやや不正確・主旨は high）。「secondary 確率が 0.55-0.70 にクラスタ」という具体値は illustrative 扱い。

出典:
- https://en.wikipedia.org/wiki/Meta-Labeling
- https://www.pm-research.com/content/iijjfds/5/2/23

---

## §14 add（ピラミッディング）の原則 — 勝ちにのみ・初回最大・逓減・都度 earn

**核心**: 勝ちポジへの add（ピラミッディング = anti-Martingale）は数学的期待値をプラスに動かす。**負けへの add（ナンピン/averaging down = Martingale）とは破壊的に別物で厳禁**。

- **confidence high**（luxalgo / heygotrade / traderssecondbrain / protraderdashboard / quantstrategy / turtletrader 等多数で完全裏取り）。
- **初回が最大・追加ほど逓減（逆ピラミッド）**: 典型 50%→30%→20%（または 1.0R/0.5R/0.25R/0.125R = 半減）。理由 = 初回が最も R:R 良好（stop が最も近く upside 最大）、追加ごとに stop が遠く upside が縮む。プロは 3-4 レベルまでに制限（超えるとトレンド枯渇）。
- **各 add は新たな確認シグナルで earn する（前提にしない）**: 価格が初期 thesis を検証してから・より優位な条件下でのみ。turtletrader「Average Up, Never Down」。
- **add ごとに全体ストップを引き上げ（SHORT なら引き下げ）**: 新規追加のリスクは既存ポジの含み益で全額カバー（初回を建値以上に動かしてから）。stop を後ろに戻さない。
- ⚠️ **用語の揺れ注記**: 業界で「inverted pyramid」は逆に「等サイズ追加=より危険」を指す呼び方もある。本書が指すのは**初回最大・後続縮小**の standard/decreasing-size pyramid。

出典:
- https://www.luxalgo.com/blog/pyramiding-strategies-scaling-into-trades-to-boost-returns/
- https://www.heygotrade.com/en/blog/what-is-pyramiding-in-trading/
- https://traderssecondbrain.com/guides/pyramiding-strategy
- https://protraderdashboard.com/blog/pyramiding-positions/
- https://quantstrategy.io/blog/the-3-golden-rules-for-pyramiding-success-entry-points/

---

## §15 add が機能するのはレジーム依存 — 強トレンド+出来高のみ、チョッピーは裏目

**核心**: add は明確な方向性トレンド（高値切上げ/安値切下げ）+ 強い出来高でのみ機能。**チョッピー/レンジ/高ボラでは false breakout・急反転で追加分が帳消し**になる。レジーム判定の質が成否を規定する。

- **confidence high**（heygotrade「choppy markets chop the pyramid mercilessly」が逐語、FXOpen/TradingView / LuxAlgo / Wright Research が独立確認）。「a reversal after multiple entries can erase all accumulated gains and more」。
- 出来高確認（institutional participation）がトレンド継続確率を上げる。
- **cat-bitget への直結**: DOWNTREND（最重要レジーム）/トレンドのみ add 有効化、RANGE は add 抑制。レジーム品質が低い局面では add を絞る。regime 切替で Priority 別スタイルを分けるのはこの知見と一致。

出典:
- https://www.heygotrade.com/en/blog/what-is-pyramiding-in-trading/
- https://www.luxalgo.com/blog/pyramiding-strategies-scaling-into-trades-to-boost-returns/
- https://blog.traderspost.io/article/pyramiding-trading-strategies-guide

---

## §16 add は「偽装された過剰レバレッジ」になりやすい — 集約リスク上限を先に決める

**核心**: add の最大の落とし穴は account レベルのリスクが add ごとに倍増すること。**事前にトータルのリスク上限を決め、それを超えて add しない**。

- **confidence high**（quantstrategy 複数記事 / luxalgo / heygotrade / tradingview / tradingsim が裏取り）。等サイズ pyramiding は account リスクを 2-4倍にしながら規律的に見える = disguised over-leveraging で大半のリテールが失敗。
- 集約上限 1.5-2% は non-negotiable で、トレンドがいくら強くても add を止める。明示的な集約上限がないと自信主導サイジングが規律を 3-5倍 violate。
- 例: 1% + 0.5% + 0.25% なら 3 add で合計 ~1.75%。2-3 add で 3-4% リスクに達すると通常の押し目で利益ごと吹き飛ぶ。
- **cat-bitget 直結**: ハード制約 H1（任意 t で `sum(active_btc) ≤ 0.12 BTC` 合計上限）はまさにこの集約リスク上限の物理 enforce。add ごとに合計を再 verify し、stop を引き上げて合計リスクが初期リスクを超えないようにする。

出典:
- https://traderssecondbrain.com/guides/pyramiding-strategy

---

## §17 add が NET を増やしているか定期監査する — 単独建てと expectancy 比較

**核心**: pyramiding が価値を生んでいるかを定期監査する。**同セットアップの単独建てより expectancy が高いときだけ add は価値を生む。同等/悪化なら add は価値破壊**。

- 原則（add の効果は単独建てと expectancy 比較で監査・positive expectancy が判定基準・大きな勝者に依存）は trendfollowing / newtraderu 等の独立ソースとも整合し妥当。
- ⚠️ **具体プロトコルは medium・弱め扱い**: 「四半期(quarterly)」「60+ トレード」「単独 vs pyramided 比較フレーム」という定式化は引用元（traderssecondbrain）の独自記述で、他独立ソースで同一の定式化は未確認。**原則は健全だが、cadence（四半期）やサンプル閾値は固定値として鵜呑みにせず、cat-bitget では「add 有無で net を実測比較して採否」する形で運用**（trade_analysis_methods_kb §0 前後比較と同旨）。

出典:
- https://traderssecondbrain.com/guides/pyramiding-strategy

---

## §18 SL/TP は Entry 時に同時設定（ブラケット）し、SL 幅はボラ（ATR）で決める

**核心**: Entry/SL/TP の3値を Entry 時点で同時設定し「ブラケット（枠）」を作るのがプロの標準。**SL 幅は固定%でなくボラティリティ（ATR）から決める** — 凪なら狭く、高ボラなら広く。Entry を取り巻くボラ regime が正しい Exit 距離を規定する。

- ブラケット設定は **high**（goatfundedtrader / luxalgo / vtmarkets / bullsonwallstreet が独立確認）。ポジションが生きる前に R:R を確定させる。
- ATR ベース SL も **high**（QuantVPS / AlphaEx Capital / Pineify / ProTraderDashboard が独立確認）。目安: ~1.5-2×ATR で凪、2.5-3×ATR で高ボラ（timeframe 依存）。固定 SL を高 ATR Entry に当てるとノイズで stop out される。
- **cat-bitget 直結**: V9 は既に `atr_14` / `adx_at_entry` を entry 時点で記録している。この測定済みボラ context を正しい Exit 距離に接続できる（§9 のボラサイズ・バリアと同根）。

出典:
- https://www.goatfundedtrader.com/blog/take-profit-vs-stop-loss
- https://www.quantvps.com/blog/using-average-true-range-for-stop-loss-placement

---

## §19 時間ストップ（time-exit）— 統計的な収益窓が過ぎたら手仕舞う

**核心**: 勝ちセットアップが通常 X 分/本で最大収益に達するなら、それを大幅に超えて持つのは無利益のまま反転リスクに資本を晒すだけ。**所定時間経過で「統計的な収益窓が切れた」として閉じる time-stop**。Entry の性質（スキャル/ポジション）ごとに保有時間も変える。

- Triple Barrier の垂直バリア（時間）は正統な手法で **high**（quantjourney / De Prado 系）。MFE/MAE の duration 分析（勝ちが 2-3 分で最大益なら 2 時間保持は無益に反転リスク）も複数ソース確認。
- ⚠️ **framing は medium・弱め扱い**: 「time-stop は機関投資家の概念でリテールはほぼ語らない」という色付けは TradesViz / Medium 1系統の framing で、広く正典化された表現でない。**手法自体は健全だが「機関限定の秘訣」という色付けは割り引く**。
- **cat-bitget 直結**: Priority 別スタイル（スキャル = 短い time-exit / 平均建値ポジ = 長い time-exit）に保有時間・Exit 条件を変える設計を支持。V9 の TIME_EXIT / TIME_EXIT_DOWN がこれに対応。

出典:
- https://medium.com/@jpolec_72972/stop-loss-take-profit-triple-barrier-time-exit-advanced-strategies-for-backtesting-8b51836ec5a2

---

## §20 高品質シグナルは confluence で作る — 入口の質が出口設計を規定する

**核心**: 複数指標の同方向合流（confluence）が勝率を上げ false setup を減らす。confluence が SL/TP をより正確にし不要なリスクを減らす = 入口の質が出口設計を規定する。

- confluence → 勝率向上・quality over quantity・risk 管理向上は **high 相当**（XS / Colibri / Babypips / AbleWayTech が広く確認・「false signals 最大50%削減」「合流で 65-80% 帯」の backtest 言及）。
- ⚠️ **定義の核心は medium・弱め扱い**: 「高品質シグナル = R:R 2x 以上であること自体で定義」「入口の質が出口設計を規定」という**直接的因果は別ソースで逐語裏取りできず推論的**。confluence=勝率向上は強いが、定義部分が弱いため全体 medium。**「合流で勝率が上がる」は採用、「R:R で定義」は補助扱い**。
- **cat-bitget 直結**: エッジは単一指標でなく confluence から出る（cat_requirements §6）。決定木に生値を渡し AND の枝で側別の切れ目を学ばせる。

出典:
- https://www.xs.com/en/blog/confluence-in-trading/

---

## §21 Entry の優位を先に確認 → 然る後に Exit/サイズを最適化（順序とコスト）

**核心**: まず Entry シグナルが統計的に有意なリターンを生むことを確認（event study / backtest）し、**その確認済みエッジの周りで stop/target/size を最適化する**。順序を守る。

- 順序（エッジ確認 → 出口チューニング → グリッドサーチ網羅 → out-of-sample 検証）は **high**（TradeZella / QuantStart / backtesting.py / 統計的有意性ガイドが独立確認）。
- ⚠️ ガードレール: 出口グリッドサーチは**過剰最適化のリスク**があり out-of-sample テストが必須（cat-bitget の封印期間 2026Q1・DSR>0.95/PBO<0.5 と整合）。「最適 stop は直感と違う場所にある」という sub-claim はやや anecdotal（medium 寄り）。
- **評価は net（コスト控除後）で**: 手数料・スリッページ控除後に期待値が崩れることが多い。Profit Factor の目安 1.5 以上（先物で 1.2-2.0 が現実的、3.0 超は過最適化疑い）。
- ⚠️ **コスト倍率は medium・弱め扱い**: 「net 期待値 > 平均コストの 1.5倍」という具体倍率は単一ソース寄り。他ソースは「平均利益はコストの 2-3倍であるべき」が主流。**閾値の存在は確実だが 1.5倍は最も緩いライン。cat-bitget では maker 優先 + add のコスト増を織り込んで net で検算**（CLAUDE.md TP_FEE_FLOOR / L-40）。

出典:
- https://www.tradezella.com/blog/backtesting-trading-strategies
- https://protraderdashboard.com/blog/expectancy-formula-trading/

---

## §22 エッジ推定にはサンプルが要る — 過剰セグメント化の警告

**核心**: 勝率・ペイオフ比の推定が統計的に意味を持つには **50-100+ トレード**必要。少ないと推定がノイズだらけで Kelly/expectancy ベースのサイジングが危険に over-size する。

- **confidence high**（JournalPlus が逐語: 「at least 50-100 trades... fewer means noisy estimates and inaccurate Kelly, potentially dangerous over-sizing」。pipup / traderssecondbrain / medium が ~30 を rough minimum、100+ を solid と補強）。2×Kelly で成長ゼロも確認。
- 一部ソースは ~30 を rough minimum とするので、**per-style edge には 100+ を安全な bar とする**。
- **cat-bitget 直結（過剰セグメント化の歯止め）**: NET 予測器を per-Priority × per-regime で細かく分けすぎると各バケットが薄くなり推定が不安定。**バケットを切る前にサンプル数を確認**する（trade_analysis_methods_kb §6 ブートストラップ信頼区間とも整合）。

出典:
- https://journalplus.co/metrics/kelly-criterion/
- https://journalplus.co/learn/guides/kelly-criterion-guide/

---

## §23 入口と出口の非対称性 — 「どちらが重要か」より「セットで評価」

**核心**: Entry と Exit はセットで評価する。両輪論（入口が土台・出口が結果を作る）は妥当。ただし「どちらがより重要か」の断定は研究間で割れる。

- ⚠️ **この主張は medium・弱め扱い（向きが業界研究と逆）**: 元主張「良い入口はランダム出口でも利益、ランダム入口は良い出口でも利益にならない」の**非対称の向きは業界研究と逆**。Tom Basso（コイントス入口）実験・Van Tharp は「ランダム入口 + 良い出口/サイジング = 利益が出る」が定説（tradingheroes / learntotradethemarket / quantifiedstrategies / jigsaw が一致）。
- ただし learntotrade は「ランダム入口に固定 2:1 だと手数料控除後ゼロ」とも述べ、出口ルールの質次第という条件付き。
- **設計に使える結論（high 部分のみ）**: 「Entry/Exit はセットで評価」「出口が結果を作る」の両輪論は妥当。**「非対称の向き」を断定文として引用するのは不可**。cat-bitget では Entry をスタートライン参照に固定し、Exit/サイズで設計する方針（cat_requirements §6）と整合 — ただし「Entry はどうでもいい」とは読まない（Entry がコスト勝ち >1.0× の土台でないと後段レバーが乗らない・industry §2.6）。

出典:
- https://ftmo.com/en/are-market-exits-more-important-than-entries/

---

## §24 エッジベースのポジションサイジング（confluence が重なるほど大きく）

**核心**: 入口の期待値（エッジ）が高いほどサイズを上げる。エッジ（根拠 = confluence）が重なるほど価格が想定方向に進む確率が上がるので、投入資本も比例して増やす。

- 一次ソース TraderLion を別ページ横断で裏取り（base 10%、複数エッジで最大 20% まで）。「より多くのエッジ = より高い確信 = より大きいサイズ」。Kelly とも整合し、エッジ比例サイジングは学術的にも裏付けあり。**confidence high**。
- ⚠️ 出所留意: TraderLion は単一機関の教育コンテンツ（プロップ流派の運用則）。具体%（10%/20%）は流派固有なので、cat-bitget では H1（0.12 BTC 合計上限）の中で予測 net 強度に比例配分する形に翻訳する。

出典:
- https://traderlion.com/lesson/lesson-5-edge-based-position-sizing/

---

## §25 cat-bitget への適用 takeaways

> Entry（V9 をスタートライン参照）/ Exit（TP幅/TimeExit/SL/トレーリング）/ サイズ（add数/ポジ数/配分）を**一つの期待値最大化問題**として設計するための要点。各 takeaway は本書の節に紐づく。

- **[§1/§12 high] 予測対象は勝率でなく net 金額**。期待値 = (勝率×平均勝ち) − (負け率×平均負け) を最大化する。Entry の精度だけでも Exit 幅だけでも NET は決まらない。手動が net 黒字な以上、ML net マイナスは枠組み側の不具合として 6 軸（entry_fix_6axis_gate）で疑う。

- **[§9 high・最重要] Exit 設定 = ラベル**。Triple Barrier では TP/SL/time を変えるとラベル（予測対象）自体が変わる。Entry モデルと Exit を**別々に最適化せず、セットで設計**する。バリアはボラ（k×σ）でサイズし固定%にしない。利確と損切で別倍率（非対称）にして Entry の質を Exit に埋め込める。

- **[§5/§9/§14 high] 入口の質（MFE/MAE 比・予測 net 強度）に応じて Exit とサイズと add 数を条件分岐**。強い Entry = TP を遠く・残し玉厚く・add 可・サイズ大。弱い Entry = 早く確定・小さく・見送り。これが Priority 別スタイル（MAX_ADDS=1 スキャル小勝ち vs 平均建値ポジ大勝ち）の定量的根拠。

- **[§8/§15/§11 high] レジームが Entry も Exit も add も規定する**。DOWNTREND（最重要）/トレンドではトレーリング・add 有効、RANGE/チョッピーでは固定ターゲット・add 抑制。トレーリングはレンジで**負の期待値**なので regime 分類を出口選択の前に置く。ADX を入口フィルタ兼出口モニタに両用（results CSV の `adx_at_entry` 活用）。

- **[§4/§3 high] Entry を変えず Exit 効率（MFE 捕捉率）を上げる余地を先に探る**。P23 の実現益÷含み益ピーク（MFE capture）を計測指標に持つ。ただし NET 改善幅は 30-60% が現実線（80% は楽観・§4 medium 部分）。ラベル・評価は MFE ピークでなく実出口で作る（Prime Directive）。

- **[§14/§16 high + H1] add は逆ピラミッド（初回最大・逓減）・勝ちにのみ・都度 earn・add ごとに合計ストップ前進**。集約リスク上限を先に決める = ハード制約 H1（任意 t で sum ≤ 0.12 BTC 合計上限）を物理 enforce。負けへの add（ナンピン）は絶対禁止。

- **[§12/§13/§24 high] サイズは Kelly 構造（エッジ×非対称性）から・fractional（25-50%）で抑える**。予測確率（meta-labeling）を**校正してから**サイズに連続マッピングし、リスク調整後 NET（Sharpe/maxDD）で評価。0.12 BTC 内で予測 net 強度に比例配分（負期待値は size 0 = 見送り）。

- **[§18 high] Entry 時に Entry/SL/TP をブラケットで同時設定し、SL 幅は ATR ベース**。V9 が記録済みの `atr_14`/`adx_at_entry` を Exit 距離に接続（maker 優先・手数料負け回避は cat 根幹）。

- **[§21/§22 high] エッジ確認 → 出口/サイズ最適化の順序を守り、net（コスト控除後）で検算**。封印期間 2026Q1 で out-of-sample 検証（DSR>0.95/PBO<0.5）。per-Priority×per-regime に細分しすぎない（各バケット 50-100+ トレード確保・薄いバケットは Kelly が over-size する）。add のコスト増を織り込んで net で判定。

- **[§17/§23 medium・弱め扱い] add の価値は「add 有無で net 実測比較」して採否**（四半期/60件という固定 cadence は鵜呑みにしない）。「出口が入口より重要」「入口がどうでもいい」とは読まない — Entry がコスト勝ち >1.0× の土台でないと後段レバー（Exit/並立/サイジング）が乗らない（industry §2.6）。Entry/Exit はあくまでセット評価。

---

## §26 出典 URL 一覧

- https://www.tradezella.com/blog/trading-expectancy
- https://www.tradezella.com/blog/backtesting-trading-strategies
- https://journalplus.co/learn/guides/win-rate-vs-risk-reward/
- https://journalplus.co/metrics/average-rr/
- https://journalplus.co/metrics/kelly-criterion/
- https://journalplus.co/learn/guides/kelly-criterion-guide/
- https://www.luxalgo.com/blog/risk-reward-ratio-vs-win-rate-key-differences-2/
- https://www.luxalgo.com/blog/pyramiding-strategies-scaling-into-trades-to-boost-returns/
- https://www.goatfundedtrader.com/blog/take-profit-vs-stop-loss
- https://protraderdashboard.com/blog/expectancy-formula-trading/
- https://protraderdashboard.com/blog/pyramiding-positions/
- https://www.tradesviz.com/blog/trade-exit-strategy/
- https://traderssecondbrain.com/guides/mae-mfe-analysis
- https://traderssecondbrain.com/guides/pyramiding-strategy
- https://medium.com/@netpicks/run-the-winners-and-cut-the-losers-like-smart-traders-163632c29f42
- https://www.orbex.com/blog/en/2026/03/why-you-cut-winners-early-and-let-losers-run-rewiring-the-traders-paradox
- https://www.quantifiedstrategies.com/mean-reversion-vs-trend-following/
- https://www.quantifiedstrategies.com/trading-exit-strategies/
- https://www.buildalpha.com/stop-losses-complete-guide/
- https://propfirmplus.com/trend-following-vs-mean-reversion-trading-style/
- https://grokipedia.com/page/Triple-barrier_labeling
- https://blog.quantinsti.com/triple-barrier-method-gpu-python/
- https://paperswithbacktest.com/course/triple-barrier-method
- https://www.altrady.com/blog/crypto-trading-strategies/trailing-stop-loss-vs-take-profit
- https://www.metriclan.com/blog/partial-profit-taking
- https://www.marketdash.com/blog/trading-exit-strategies
- https://zforex.com/blog/general-trading/what-are-exit-strategies/
- https://www.thinkmarkets.com/en/trading-academy/indicators-and-patterns/adx-indicator-how-it-works-trend-strength-signals-and-trading-strategies/
- https://en.wikipedia.org/wiki/Kelly_criterion
- https://astuteinvestorscalculus.com/the-kelly-criterion/
- https://astuteinvestorscalculus.com/kelly-criterion-position-sizing/
- https://nycif.org/asymmetric-returns/
- https://en.wikipedia.org/wiki/Meta-Labeling
- https://www.pm-research.com/content/iijjfds/5/2/23
- https://www.xs.com/en/blog/confluence-in-trading/
- https://blog.traderspost.io/article/pyramiding-trading-strategies-guide
- https://quantstrategy.io/blog/the-3-golden-rules-for-pyramiding-success-entry-points/
- https://quantstrategy.io/blog/the-ultimate-guide-to-pyramiding-strategy-in-trading/
- https://www.heygotrade.com/en/blog/what-is-pyramiding-in-trading/
- https://www.quantvps.com/blog/using-average-true-range-for-stop-loss-placement
- https://traderlion.com/lesson/lesson-5-edge-based-position-sizing/
- https://www.financial-spread-betting.com/strategies/adding-winning-positions.html
- https://ftmo.com/en/are-market-exits-more-important-than-entries/
- https://medium.com/@jpolec_72972/stop-loss-take-profit-triple-barrier-time-exit-advanced-strategies-for-backtesting-8b51836ec5a2
- https://proficient-project.eu/the-kelly-criterion-optimal-bet-sizing-for-investing-and-gambling/
- https://experts.deriv.com/insights/kelly-criterion-position-sizing
- https://www.avatrade.com/education/technical-analysis-indicators-strategies/the-kelly-criterion
- https://medium.com/@tmapendembe_28659/the-dangers-of-full-kelly-criterion-why-most-traders-should-use-fractional-kelly-criterion-instead-0338e3bcc705
