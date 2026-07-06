# entry_exit_matrix.md — Entry×Exit ロジック 網羅マトリクス（★全戦略共通）

作成: 2026-07-06（まこさん指示「Entry×Exit の全組み合わせを網羅マトリクスで並べたうえで、あらゆる組み合わせ・選択肢で改善しつくすように、強制しろ」「E37 専用でなく全戦略共通に」「CAT−指標マトリックス - 一覧.csv を参考にして作り直せ（正本化はしない）」「足りない要素は WebResearch して網羅」）。
位置付け: **どの戦略（E35/E36/E37/P21/P23/E28/新戦略）の改善でも、CC が「1レバーずつ狭く選ぶ」モグラ叩き（E37 v10→v13 の反省）を禁止し、Entry ロジックの全候補 × Exit ロジックの全候補を並べ、試済セル（実験名・両窓 net）と未試行セルを可視化して、未試行を潰し切るまで進める**ための正本。
物理強制: `enforce_combo_matrix.sh`（improvement_plan.md / acceptance.md を書く瞬間に ①本ファイルの存在 ②共通軸カタログ ③対象戦略のグリッド節と網羅幅 ④未試行の可視化 ⑤提案が本表を指すこと を要求。戦略名は焼かず提案本文の token で追従）。
出典: CAT 指標マトリックス（参考・正本化しない）＋ WebResearch 2026-07-06（quantifiedstrategies/luxalgo/arxiv・§末）＋ ledger（各実験の両窓）。本ファイルの Entry/Exit 軸の**正本は本ファイル**（実験結果ベース）。
更新: 実験1本ごとにセルへ両窓 net を埋め未試行→試済へ。選択肢を思いついたら軸に足す。新戦略の改善時はその戦略の `## グリッド: <戦略>` 節を追加してから提案。

> ⚠️ 使い方（狭い思考の禁止・全戦略共通）: 改善案は「試済セルの隣の1マス」でなく、**未試行セル全体を見渡して、最も筋の良い組み合わせを全体から選ぶ**。Entry/Exit は**セットで net が決まる**（分割思考禁止・L-285）＝「Exit だけ」「Entry だけ」でセルを選ばない。未試行が残る限り「これ以上ない」と言わない（block_premature_giveup と対）。

> ⚠️ **CAT 指標マトリックス（`.claude/memory/CAT−指標マトリックス - 一覧.csv`）は参考＝正本化しない**（まこさん 2026-07-06／CLAUDE.md「古い情報混在・参照のみ」）。下の各軸に CAT の軸ID（A-1〜D-θ）を併記＝「選択肢を狭く忘れていないか」を広げる横目。CSV の数値・学習状況は古いので鵜呑みにしない。

---

## 共通 Entry ロジック軸（全戦略の選択肢カタログ・CAT軸ID併記・思いついたら足す）

- **E-a シグナル家族（何を取るか・WebResearch 8分類＋α）**: (1) 逆張り＝平均回帰 MR（レンジ端/行き過ぎを fade） / (2) 順張り＝モメンタム/トレンドフォロー / (3) ブレイクアウト（レンジ/ATH 超え＋出来高） / (4) 戻り売り・押し目（プルバック） / (5) グリッド（往復を仕組みで刻む） / (6) マーケットメイク（両側 maker・在庫制御＝Avellaneda-Stoikov/Cartea・スプレッド収益） / (7) order-flow/需給（Institutional Accumulation・Flow Momentum） / (8) レンジ内 value（stable range で仕込む）
- **E-b 局面判定 regime（CAT D-ε・9手法×state）**: (1) なし＝全地合い / (2) MA（close vs MA70） / (3) ADX（trend/range） / (4) ATR（高低ボラ） / (5) Hurst 指数 / (6) HMM / (7) GMM-HMM / (8) UMAP+HDBSCAN / (9) Markov regime switching / (10) change point detection / (11) タッチ実績 S/R ゾーン（E37 v10/v11） / (12) ボリュームプロファイル POC / (13) BB スクイーズ / (14) 現物先物ベーシス。state＝3状態(DT/RANGE/UT)／+ボラ／連続score
- **E-c Entry 指標（CAT A-1・145ファミリー・6TF）**: トレンド/モメンタム＝ADX/DI/MACD(line/sig/hist)/RSI(7/14/21)/ROC/Stoch(k/d)/MFI/CMF/OBV/Ichimoku/RCI/MTF傾き整合 ／ ボラ＝ATR%/BB%b/BB幅/realized_vol/donchian幅/zscore_return ／ 出来高＝volume_ratio/OBV傾き/CMF/MFI ／ ローソク＝engulfing/pinbar/streak/body_ratio/wick_ratio ／ 形(W窓)＝V/W/M/swing_dist/bars_since_high-low ／ 位置＝close vs EMA/SMA/VWAP/kijun/keltner/supertrend/high-low ／ 構造＝pivot(PP/R/S)/fib(382-786)/VP(VAH/VAL/POC)/S-R touch_count ／ 需給＝taker_ls/L-S比/CVD
- **E-d 到達・トリガ（CAT A-3）**: (1) ゾーン/バンド接触（S/R・Keltner） / (2) BB±2σ/±3σ 超え / (3) 相対分位 dev_z≥q（q90/95/99） / (4) 指標クロス（MACD/stoch/EMA） / (5) VP/POC 距離
- **E-e 確認（入る前の裏取り・CAT B-9 AND段数3-7）**: (1) なし＝到達で即 / (2) 反転ローソク（陰陽転・pinbar・engulfing・KB §3） / (3) モメンタム反転（RSI9・stoch・divergence） / (4) 出来高（exhaustion＝減少 or spike） / (5) MTF 整合（上位足の向き） / (6) AND 深さを増やす（confluence 3〜7 条件）
- **E-f 方向材料（向きの根拠）**: (1) なし＝方向を当てない・雑に多く（両側 maker） / (2) 静的テクニカル stoch_k/RSI（E37 SHORT で AUC0.61＝弱） / (3) 需給 taker_ls（E28 LONG 有効・E37 SHORT で AUC0.52＝不能） / (4) L-S比 ls_global（E29 LONG 有効） / (5) CVD 累積出来高デルタ（未・§6.7） / (6) MTF 上位足の向き
- **E-g 足・時間軸（CAT A-5/A-4）**: 足＝5m/15m/30m/1h/4h/1d（1m 禁止・3m 保留）／ MTF 展開＝ffill/5m rolling/線形補間 ／ 予測ホライズン K＝6/12/24/48/96/144/288（上限24h）
- **E-h 方向（CAT D-ζ）**: SHORT のみ / LONG のみ / 両側 / hedge(net0) / ペアトレード（§1.2.1 で戦略ごとに固定＝逸脱不可）

## 共通 Exit ロジック軸（全戦略の選択肢カタログ・CAT A-2 16サブ＋WebResearch・CAT軸ID併記）

- **X-a TP 固定目標（CAT A-2）**: (1) 固定 %/pip/dollar / (2) R:R 固定（1:2/1:3） / (3) レンジ中央 SMA/中央線 / (4) 反対ゾーン（サポート側）まで伸ばす / (5) 固定σ幅 / (6) VWAP 回帰 / (7) bracket order
- **X-b TP 段階決済 scale-out（WebResearch＝fade/scale/exit）**: (1) 部分決済（例 中央35%/1.5σ35%/反転30%） / (2) profit target ladder（段階利確） / (3) pyramiding exit / (4) 複数TP（最大20個・Bitget）
- **X-c トレーリング（CAT A-2）**: (1) %トレーリング / (2) ATR トレーリング（Chandelier） / (3) Parabolic SAR / (4) high-water mark / (5) ボラ連動トレーリング（利益で 0.25-0.40% へ締める）
- **X-d SL（CAT A-2）**: (1) 固定 % / (2) ゾーンすぐ外・浅い構造線 / (3) **遠い Chan 型＝深SL・時間切れ主体**（L-323＝平均回帰に浅SLは逆効果） / (4) SLなし＝レンジ破れ/前提崩れ検知でのみ撤退（KB §5） / (5) ATR×k 倍 / (6) swing 高安の外 / (7) MAE stop / (8) acceleration SL（早期カット） / (9) ±3σ / (10) 建値撤退（含み損戻りで損ゼロ maker・E35 iter4）
- **X-e 含み益管理（CAT A-2）**: (1) break-even（建値へ SL 移動） / (2) profit lock（利益固定） / (3) MFE-based（含み益ピーク基準） / (4) MFE stale（含み益が伸びない検知）
- **X-f 時間切れ・前提崩れ（CAT A-4）**: (1) 固定時間/バー数 成行 taker / (2) **deadline shrink＝残り時間比で建値側 maker 化**（E35 iter8-9・E37 v13） / (3) レンジ破れ（出来高∩境界外終値）で早期撤退 / (4) market close/曜日 exit / (5) なし
- **X-g 指標反転・構造・ボラ・出来高・統計 Exit（CAT A-2）**: RSI/Stoch/MACD reversal / BBタッチ / EMA cross / ADX decay / pivot反転 / trendline-channel break / vol expansion-contraction / volume spike-divergence / order-flow reversal / z-score reversion（統計的平均回帰閾値）
- **X-h ML Exit（CAT A-2/B-10）**: Triple Barrier（Lopez de Prado） / meta-labeling / 強化学習 terminal policy / exit value prediction
- **X-i add / ピラミッディング（CAT A-6）**: (1) なし単発 / (2) 順張りピラミッド（Turtle 逓減・N=20 ATR） / (3) Martingale / (4) Anti-Martingale / (5) 予測強度依存 / (6) Kelly fractional / (7) vol-targeted / (8) グリッド add / (9) add トリガ（逆行幅/時間経過/指標再発火/含み益確認）
- **X-j サイジング（CAT A-7・8方式）**: 一律 / remaining÷n / 予測強度比例 / Kelly（fractional 0.25-0.5） / risk parity / vol-targeting（ATR反比例） / cluster別固定 / 過去パフォーマンス重み（合計0.12 BTC 厳守）
- **X-k 決済方式（CAT D-θ・10種）**: 成行 taker / 指値 maker / post-only maker / stop（緊急SL taker） / stop-limit maker / trailing-stop / OCO（TP+SL 同時） / iceberg / TWAP / VWAP（§6.7＝方向を当てない戦略は maker が生命線）

---

## グリッド: E37（range, short_only, scalp）— 試済[実験名・両窓]／未試行

| # | Entry 構成 | Exit 構成 | 状態 | 学習窓 be | 採点窓 net | ledger |
|---|---|---|---|---|---|---|
| 1 | フラクタル箱・両側・雑（Ea1/Eb1） | ATR-SL・浅TP・60分taker（Xd5/Xa5/Xf1） | 試済 | 負 | 負 | v2〜v9 系 |
| 2 | タッチ実績ゾーン・上限・陰転RSI9・静的（Eb11/Ee2/Ef2） | レンジ中央TP・浅SL・60分taker・単発（Xa3/Xd2/Xf1/Xi1） | 試済 | −0.63 | 月−$20.55 | v10 |
| 3 | v17計器・上限・陰転RSI9・静的 | 複数TP2段・浅SL・60分taker・add2（Xb1/Xd2/Xf1/Xi9） | 試済 | −0.07 | −$209 | v11 |
| 4 | v17計器・上限・陰転のみ・非過熱 | 複数TP2段・浅SL・60分taker・add2 | 試済 | −0.14 | −$251 | v11oe |
| 5 | v17計器・上限・確認なし・雑（Ee1/Ef1） | 複数TP2段・浅SL・60分taker・add2 | 試済 | −0.45 | −$551 | v12 |
| 6 | v17計器・上限・確認なし・雑 | 複数TP2段・浅SL・**deadline shrink maker**・add2（Xf2） | 試済 | −0.52 | −$500 | v13 |
| 7 | v17計器・上限・確認なし・雑 | 複数TP2段・**遠SL Chan型・時間切れ主体**（Xd3/Xf1） | 未試行 | — | — | — |
| 8 | v17計器・上限・確認なし・雑 | 複数TP2段・**SLなし・レンジ破れ撤退**（Xd4/Xf3） | 未試行 | — | — | — |
| 9 | v17計器・上限・**反転ローソク確認**（Ee2） | 複数TP2段・浅SL・deadline shrink・add2 | 未試行 | — | — | — |
| 10 | v17計器・上限・確認なし・雑 | **反対ゾーンまで伸ばすTP**（Xa4）・遠SL・時間切れ主体 | 未試行 | — | — | — |
| 11 | v17計器・**MTF整合確認**（Ee5/Ef6） | 複数TP2段・浅SL・deadline shrink | 未試行 | — | — | — |
| 12 | **ボリュームプロファイル POC**（Eb12） | 反対POCまでTP・遠SL・時間切れ | 未試行 | — | — | — |
| 13 | v17計器・上限・確認なし・雑 | 複数TP2段・遠SL・**トレーリング（ATR/Chandelier）**（Xc2） | 未試行 | — | — | — |
| 14 | v17計器・上限・**需給 CVD/taker_ls 併用**（Ef5/Ef3） | 複数TP2段・浅SL・deadline shrink | 未試行 | — | — | — |
| 15 | v17計器・上限・確認なし・雑 | **建値撤退（Xd10）＋profit lock（Xe2）**・時間切れ | 未試行 | — | — | — |
| 16 | **BBスクイーズ∩±2σ（Eb13/Ed2）**・反転ローソク | 中央SMA TP・±3σ SL・scale-out | 未試行 | — | — | — |
| 17 | v17計器・上限・確認なし・雑 | 複数TP2段・浅SL・**OCO 発注（Xk OCO）**・deadline shrink | 未試行 | — | — | — |
| 18 | v17計器・上限・確認なし・雑 | **z-score reversion Exit（Xg）**・遠SL | 未試行 | — | — | — |

**試済の偏り（反省）**: v10〜v13 は Entry=「レンジ判定＋方向を当てる/雑」・Exit=「浅SL＋60分taker or shrink」に偏り＝グリッド左上ブロックだけ。**Exit の SL 軸（Xd）はずっと(2)浅い構造線のまま**なのに SL が最大出血源（v13 SL −$1905）＝遠SL/SLなし/建値撤退（Xd3/4/10）が丸ごと未試行。TP を伸ばす（Xa4）・トレーリング（Xc）・確認を戻す（Ee2）・MTF（Ee5）・需給（Ef3/5）も空。
**未試行: あり**（#7〜#18＝Exit の SL/TP/トレーリング軸・Entry の確認/MTF/需給/別局面判定が空。上の共通軸カタログの掛け合わせはさらに広大＝ここは主要18行のみ）。潰し切るまで「これ以上ない」と言わない。
**全体からの選定（次の提案が指すセル）**: （次セッションで再分析→本表を広げてから、未試行セル全体を見渡して選定を1行で書く。CC が狭く1マスを決め打ちしない＝まこさんと全体から選ぶ。）

---

## グリッド: <戦略>（他戦略はここに節を追加してから改善提案する）

> E36/E35/P21/P23/E28/新戦略 を改善する時は、上の E37 と同じ形で `## グリッド: <戦略>（<局面,方向,頻度>）` 節を作り、共通軸カタログから戦略の §1.2.1（担当局面・方向）で使える選択肢を並べ、試済（ledger の実験名・両窓）と未試行を可視化してから improvement_plan/acceptance を書く（enforce_combo_matrix が物理強制）。テンプレ＝上の E37 グリッドの表構造をコピー。

## 出典（WebResearch 2026-07-06）
- Entry シグナル8分類（Momentum/MeanReversion/Volatility/Liquidity/Technical/Breakout/Institutional Accumulation/Flow Momentum）: arxiv 2409.06289 ／ 2605.04004（OHLCV日中信号の構造的限界）。
- 平均回帰レンジ Entry/Exit（BB±2/3σ・RSI70/30・Z-score・中央回帰・scale-out・ATR/±3σ SL）: quantifiedstrategies.com/mean-reversion-trading-strategy ／ luxalgo.com/blog/mean-reversion-playbook-fade-scale-exit（中央35%/1.5σ35%/反転30%・トレーリング0.25-0.40%）。
- マーケットメイク（在庫制御・スプレッド・終端清算ペナルティ・在庫リスク回避パラメータ）: arxiv 1105.3115（Avellaneda-Stoikov）／ 1206.4810 ／ 2606.01477（AS と Cartea-Jaimungal の統一）。
- CAT 指標マトリックス 23軸カタログ（参考・正本化しない）: `.claude/memory/CAT−指標マトリックス - 一覧.csv`。
