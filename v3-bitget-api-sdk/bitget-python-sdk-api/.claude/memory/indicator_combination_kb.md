# indicator_combination_kb.md — 指標の組み合わせ方の法則（知識の正本）

作成: 2026-08-08。まこさん指示「もっと組み合わせ方の法則を徹底的に研究してスマートな設計にしろ」＋「このセッションで学んだ以下の内容とかはちゃんとまとめておいて」。

**この文書は何か。** 売買ルールの入口の条件を「どう組み合わせるか」の法則を、出典の逐語つきでまとめた知識の正本です。

**なぜ作ったか。** 2026-08-08 の重大インシデント #14＝CC が engine_tuner の案の作り方を「くじ引き」にしていた（まこさん認定「論外」）。**くじを引く代わりに法則で組み立てるには、その法則が明文で無いといけません。** 探して、書きました。

**書くもの＝知識（辞典レベル）。書かないもの＝実験の結果（→ ledger）・engine_tuner の現在地（→ next_step）・機械の決まりの実体（→ 下の「機械の実体」）。**

**機械の実体（この知識を機械が読む形にしたもの）**
- 手で書いた元ファイル＝`scripts/priority_rebuild/recipes/composition_rules_src.json`
- 生成器＝`scripts/priority_rebuild/gen_composition_rules.py`
- 完成品＝`.claude/ratchet/composition_rules.md` ／ `.json`

---

## §1 法則（6つ・出典の逐語つき）

### 法則1：指標は系統に分かれる。組み合わせるのは違う系統どうし

> Every indicator belongs to one of four categories: trend, momentum, volume, or volatility.
> **Combining two indicators from the same category doubles the noise, not the signal.**
> （[excavo](https://excavo.com/blog/how-to-combine-trading-indicators)）

> **It is undesirable to combine several trend indicators.**
> （[LiteFinance](https://www.litefinance.org/blog/for-beginners/what-is-forex/confluence-forex-trading/)）

**＝同じ系統を2本 重ねると、増えるのは判断材料ではなく雑音です。**

### 法則2：1つの指標は1つの問いに答える。同じ問いに答える指標は片方が無駄

> **Each indicator on your chart should answer a different question. If two tools answer the same question, one of them is redundant.**
> （[excavo](https://excavo.com/blog/how-to-combine-trading-indicators)）

### 法則3：本数（出典が食い違う・両方 記録する）

> **Two to four indicators from different categories is typically the sweet spot.**
> Beyond four, each additional indicator usually adds more noise than signal.
> （[excavo](https://excavo.com/blog/how-to-combine-trading-indicators) の**記事本文**）

> Stick to 3–5 non-overlapping factors: one trend tool, one oscillator, levels, and macro context.
> Stacking three momentum oscillators does not triple your edge – it just measures the same thing.
> （同 記事の要約から取った版）

**このプロジェクトの正本（cc_entry_logic_self_study §7.1）は「3〜5本が最適・6本以上は取引機会が激減」と書いています。**

**★食い違いの扱い（決めたこと）＝どちらも数値の根拠が示されていないので、1つに決め打ちしない。2〜4本を下限側、3〜5本を上限側として、2〜5本の範囲を探索の対象にする。**

⚠️ **既存の設定ファイル `recipes/search_limits.json` の count_range は [3, 8] です。上限が食い違ったままです（まこさんの判断待ち・2026-08-08 時点）。**

### 法則4：時間足は3層。上・中・下で役割が違う

> **Higher Timeframe**: 全体の向きを決める ／ **Middle**: 仕掛けの場を見つける ／ **Lower**: 入る瞬間を決める
> **Higher timeframes help filter low-quality signals from lower timeframes.**
> （[NinjaTrader](https://ninjatrader.com/futures/blogs/top-down-analysis-trading-guide/)・[tradeciety](https://tradeciety.com/how-to-perform-a-multiple-time-frame-analysis)）

**★上位足が優先する（記事本文の逐語）**

> **the higher timeframe typically takes precedence. If the daily chart shows a downtrend, traders using this approach would only look for short setups on the 15-minute chart, not longs.**
> （[NinjaTrader](https://ninjatrader.com/futures/blogs/top-down-analysis-trading-guide/)）

**＝上位足で見た向きと逆の入口を作らない。**

**このプロジェクトの正本（technical_analysis_knowledge_base §2.1）と一致します。**

> **原則**: 「短期足の波は、長期足の波に飲み込まれる」
> **目的 1: 環境認識**: 長期足で方向性確認 + 短期足でタイミング

### 法則5：条件には役目がある

> **filters reduce noise, triggers initiate signals, confirmations validate entries**
> （[FMZQuant](https://medium.com/@FMZQuant/triple-indicator-trend-confirmation-quantitative-trading-strategy-7570977493eb)）

| 英語 | 日本語 | 何をするか |
|---|---|---|
| filter | **ふるい** | 入ってはいけない場面を先に除く |
| trigger | **合図** | 入る瞬間を決める |
| confirmation | **裏づけ** | その合図が本物かを確かめる |

**★もう1つの出典は分け方が違います（記事本文の逐語）**

> **every tool on your chart should either generate a trade, filter a trade, or size a trade. If it does none of these, it's adding noise.**
> （[excavo](https://excavo.com/blog/how-to-combine-trading-indicators)）

**＝建てる／ふるいにかける／量を決める。「どれでもない道具は雑音」。**

**扱い（決めたこと）＝両方 使う。** 「量を決める」はサイジングの軸なので入口の条件の対象外。**そして「建てる・ふるいにかける、のどちらでもない条件は入れない」を決まりに足した。**

### 法則6：同じ動きをする列は、実データで測って落とす（★機械の側の法則）

> **Highly correlated features add redundant data and can skew feature-importance scores.**
> Pairwise correlations can be computed and highly redundant features dropped.
> （[apxml](https://apxml.com/courses/intro-feature-engineering/chapter-6-feature-selection/filter-correlation-analysis)）

**★これが一番 大事だと考えます。理由です。**

**法則1と2は「人が付けた系統の札」で重複を防ぎます。粗いです。**

- ADX と DI差 は同じトレンド系ですが、見ているものが違います（強さと向き）。
- RSI9 と RSI21 は同じオシレーター系ですが、動きが違います（反応の速さ）。

**実データで動きの重なりを測れば、札に頼らずに重複を落とせます。系統の札は最初のふるい、実データの相関が本番です。**

⚠️ **測る期間は値決め窓だけ（H2・H8）。採点窓を使わない。**

---

## §2 重複の判定は「系統」より「問い」でやる方が正確

**記事は、指標を「答える問い」で5つに分けています（記事本文の逐語）。**

| 問い | 逐語 |
|---|---|
| トレンド | What's the trend? Direction and momentum |
| 水準 | Where is structure? Key levels where price is likely to react |
| 出来高 | What's the volume telling us? |
| 相場の状態 | What's the regime? Trending or ranging? High volatility or low? |
| 損切りの位置 | Where's the risk? Where should the stop-loss go? |

**★ADX は「トレンド」にも「相場の状態」にも答えます。系統で分けると、この違いが消えます。**

**このプロジェクトでの扱い＝部品ごとに「どの問いに答えるか」を、系統から機械で写して持たせる。手で付けない（ヌケモレを作らないため）。**

**いまの対応（`composition_rules.md` が機械生成）**

| 系統 | 答える問い |
|---|---|
| トレンド | トレンドはどちらか |
| 構造・位置 | どこに水準があるか |
| 出来高 | 出来高は何を言っているか |
| ボラ | いまトレンドかレンジか・ボラは高いか低いか |
| オシレーター | 行き過ぎているか |
| ローソク | 直前の1本で何が起きたか |
| 需給 | 成行と建玉はどちらに偏っているか |
| 時間帯 | いつか |

**★オシレーター・ローソク・需給・時間帯は、記事の5区分に在りません。** technical KB §3.1 の5カテゴリ（トレンド／オシレーター／ボラ／出来高／サポレジ）と range_scalping_kb §6.7（需給）・entry_exit_matrix E-j（時間帯）から補いました。

---

## §3 合図ごとの弱点と、ふるいが確かめること

**★これが「法則に則って組み立てる」の中心です。** 合図を1つ選んだら、その合図が持つ既知の弱点を見る条件を**必ず1本 足します。選択ではなく必須です。**

| 合図の型 | 弱点（出典の逐語） | ふるいが確かめること | ふるいの系統 |
|---|---|---|---|
| オシレーターのクロス | 「オシレーター系 (RSI/Stoch)｜トレンド時: **100/0 張り付き・機能停止**」（technical KB §2.2） | トレンドが出ていないこと | トレンド |
| 価格が帯の端に触れる | 「Band Walk｜Lower band に張り付き → 弱気モメンタム継続 → これは**「逆張りシグナル」ではなく「順張り継続シグナル」**」（同 §A.5.4） | 帯が拡大していないこと | ボラ |
| 高い水準からの反転 | 「**強トレンド時: extreme 値が長期間維持される (張り付き)**」（同 §A.1.3）／「強気相場の BTC｜**RSI 70 を週・月維持あり**」（自己学習 §5.1） | 実際に向きが変わったこと（傾き） | トレンド・オシレーター |
| 端を抜ける | ダマシの抜けが多い。「破れの判定3点: ①20期間平均を上回る出来高 ②境界を明確に超えた終値 ③複数時間軸での確認」（range_scalping_kb §5） | 出来高が増えたこと・終値で確定したこと | 出来高・構造・位置 |
| トレンドの強さの急上昇 | 「**ADX < 20 でクロス = 信頼度低い (40% 失敗率増・2026 研究)**」（technical KB §A.3.3） | トレンドの強さの下限 | トレンド |

**実物の裏づけ＝V9 の9本は、全部この形になっています。**

例＝V9 P3（LONG）。

```
Stoch ゴールデンクロス     ← 合図（オシレーター）
AND BB middle slope > 10    ← ふるい（トレンド系・向きの確認）
AND ADX ∈ [30, 50)          ← ふるい（トレンド系・強さの確認）
AND ATR ≥ 250               ← 物理の条件（幅が足りているか）
```

---

## §4 この法則から出る設計（機械が守る5つ）

**条件を1本 足すたびに、機械が次を守ります。**

| # | 決まり | 出どころ |
|---|---|---|
| 1 | 役目の枠を埋める＝ふるい・合図・裏づけ。**合図は1つの経路にちょうど1本** | 法則5 |
| 2 | **同じ問いに答える部品を2本 入れない** | 法則1・2 |
| 3 | **既に入っている条件と、実データの動きが重なる列を入れない** | 法則6 |
| 4 | **時間足は役目で決まる**＝ふるいは上位足・合図は下位足・裏づけは合図の足以上 | 法則4 |
| 5 | 本数は 2〜5本 | 法則3 |
| 6 | **建てる・ふるいにかける のどちらでもない条件は入れない** | 法則5（excavo 本文） |
| 7 | **上位足で見た向きと逆の入口を作らない** | 法則4（NinjaTrader 本文） |

**この決まりを守ると、組み立てた時点で法則に則っています。乱数になりません。**

---

## §5 組み合わせの数（現実的か）

**部品は105種。系統の内訳＝構造・位置42／オシレーター24／トレンド16／ボラ11／ローソク7／出来高5。時間足は9本。**

| 役目 | 使える系統 | 候補の数（2026-08-08 の機械出力） |
|---|---|---|
| 合図（下位足3つ） | オシレーター・ローソク | **93** |
| ふるい（上位足6つ） | トレンド・ボラ・時間帯・構造・位置 | **340** |
| 裏づけ | ボラ・出来高・需給・構造・位置・オシレーター | **654**（相対の絞り込みは組み立ての段で適用） |

**3本の骨格で、おおよそ60万通りです。**

**乱数で945列から引く場合の 10の24乗 と比べて、桁が18 小さくなります。探索で扱える数です。そして全部が法則に則っています。**

**水準（閾値）は、この骨格が決まってから範囲で探します。メニューにしません。**

---

## §6 いまの実装との対応（役目は2軸で持つ）

**engine_tuner の役割は4つ（建てる合図・相場の向き・値動きの大きさ・レンジの中の位置）。これは「何を見るか」の分類です。**

**業界の3つ（ふるい・合図・裏づけ）は「何のために在るか」の分類です。**

**軸が違います。両方 要ります。**

| 条件の例 | 何を見るか | 何のために在るか |
|---|---|---|
| 1時間足の ADX が 25 未満 | 相場の向き | **ふるい**（トレンド中は入らない） |
| 5分足のストキャスが上抜け | 建てる合図 | **合図** |
| 5分足が陽線 | 建てる合図 | **裏づけ**（合図が本物か） |
| ATR% が 0.15 以上 | 値動きの大きさ | **ふるい**（幅が足りない場面を除く） |

**2026-08-08 時点＝いまの実装は「何を見るか」しか持っていません。「何のために在るか」を足すのが段5 の作業です。**

---

## §7 場面の判定（レンジ判定）の組み立て

**まこさん指示 2026-08-08＝「レンジという判定ロジックも engine_tuner で組めるようにすべき」。**

**レンジ判定も条件の束です。ただし入口の合図と3つ違います。**

1. **役目が違う**＝発火するものではなく、状態を表すもの。
2. **持続が要る**＝1本だけ成立してもレンジとは言わない。
3. **測り方が違う**＝単独では成績が出ない。入口を固定して、レンジ判定だけを差し替えて比べる。

**組み立ての決まり（出典つき）**

| # | 決まり | 出典の逐語 |
|---|---|---|
| RG-1 | **構造・位置の系統を必ず1本 入れる**（ゾーンとタッチの実績） | range_scalping_kb §2「レンジ＝『価格がサポートとレジスタンスの間で繰り返し反応している状態』。**統計量（横ばい度・ADX 等）ではなく、機能しているレベルの実績で認識する**」「機能実績の基準: 最低3回のタッチ」 |
| RG-2 | 補助（トレンドの強さ・値動きの幅・出来高）は違う系統から | 法則1・2 と同じ |
| RG-3 | **上位足で作る** | 同 §2「上位足で主要ゾーンを構築 → 下位足（5分）で執行（多時間軸の黄金律）」 |
| RG-4 | **何本 続いているかを条件に入れる** | 同 §2「繰り返し反応している状態」＝1点でなく継続 |

**測るもの3つ**

| 何を測るか | なぜ |
|---|---|
| レンジと判定した時間の割合 | 狭すぎると取引の回数が出ない |
| その時間の中で建てた玉の成績 | 判定が当たっているか |
| **レンジと言った時間のうち、実際はトレンドだった割合** | 取りこぼしの量。**E37 の失敗の本体** |

---

## §8 ★訂正の記録（要約だけで書いて外した2件・消さない）

**2026-08-08 に CC が検索結果の要約だけで書き、記事本文を開いて訂正した2件です。**

| # | 要約から書いたもの | 記事本文 | 何が違ったか |
|---|---|---|---|
| 1 | 条件の本数は「3〜5本」 | **「Two to four indicators」** | 上限が1本 違う。5本目からは雑音の方が増える、と本文は言っている |
| 2 | 役目は「ふるい・合図・裏づけ」 | **「generate / filter / size」** | 「量を決める」が抜けていた。そして「どれでもない道具は雑音」という決まりも抜けていた |

**教訓＝検索結果の要約で設計を書かない。記事本文を開いて逐語を取る。**

---

## §9 出典の一覧

- [How to Combine Trading Indicators: A Professional Framework](https://excavo.com/blog/how-to-combine-trading-indicators)
- [Confluence in Forex Trading | LiteFinance](https://www.litefinance.org/blog/for-beginners/what-is-forex/confluence-forex-trading/)
- [Top-Down Analysis: Multi-Timeframe Trading | NinjaTrader](https://ninjatrader.com/futures/blogs/top-down-analysis-trading-guide/)
- [How To Perform A Multi TimeFrame Analysis | Tradeciety](https://tradeciety.com/how-to-perform-a-multiple-time-frame-analysis)
- [Triple Indicator Trend Confirmation | FMZQuant](https://medium.com/@FMZQuant/triple-indicator-trend-confirmation-quantitative-trading-strategy-7570977493eb)
- [Filter Methods: Correlation Analysis | apxml](https://apxml.com/courses/intro-feature-engineering/chapter-6-feature-selection/filter-correlation-analysis)

**プロジェクト内の正本**
- `technical_analysis_knowledge_base.md` §2.1（MTF）・§2.2（系統の得意不得意）・§2.4（V9 P3 のコンフルエンス）・§3.1（5カテゴリ）・§A.1.3・§A.3.3・§A.5.4
- `cc_entry_logic_self_study.md` §7.1（本数）・§8.2（V9 は全9本が5分足単独＝最大の構造的欠陥）・§9.1（8カテゴリ中3.5しか使っていない）
- `range_scalping_kb.md` §2（レンジの認識）・§3（到達→拒否の確認→エントリー）・§5（破れの判定）・§6.6（方向は予測しにくい）・§6.7（需給が唯一 効いたエッジ）
- `entry_exit_matrix.md`（入口8軸・出口11軸の軸カタログ）
- `v9_logic.md`（V9 の9本の実物）
