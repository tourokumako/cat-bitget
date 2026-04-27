# regime_research.md — レジーム判定研究 唯一の正本

> このファイルは **regime 判定研究の全集約** です。
> WORKFLOW.md / phase8_supervised_tool_survey.md / lessons_active.md L-126〜135 / signal_ledger.md / CLAUDE.md
> に分散していた regime 関連情報をここに集約。**矛盾を見つけたらこのファイルを更新**して、他は参照リンクに留める。
>
> 段階1〜8 の表記は廃止。**判定軸マトリクスと試行ログ**で進捗管理する。

最終更新: 2026-04-27（レシピ型設計に方針転換・L-137）

---

## §0 現フェーズ

**フェーズ: レシピ型 grid search 設計（草案 → レビュー → harness 実装）**
**Priority個別最適化: regime確定まで全停止（CLAUDE.md・WORKFLOW.md 共通）**

- 試行単位 = **完全レシピ**（時間軸セット × 指標セット × 粒度内集約 × 指標間集約 × 閾値）
- 部品単独評価（指標単体・粒度単独）は L-137 で否定済 → 設計探索の試行単位として採用しない
- 並行作業: まこさんが 1826日肉眼ラベル付け中（現在 365/1826）。ラベル進捗 70%+ 到達後に本走査
- 365日ラベル充足部のみで一次スコアは出せる設計にする

> 過去フェーズ（段階1〜8）は §3 試行履歴を参照。

---

## §1 経緯タイムライン

| 日付 | 出来事 | 結果 |
|------|-------|------|
| 2026-04-21 | 設計思想確定: 日足MA70で3レジーム切替 | CLAUDE.md 採用 |
| 2026-04-25 | look-ahead バグ発覚（_build_regime_map 系3関数）| L-128 / 既採用パラメータは look-ahead プレミアム前提と判明 |
| 2026-04-25 | 月単位粒度誤認 | L-126 / 月単位支配 regime が本丸と確定 |
| 2026-04-25 | 教師あり試行（週ラベル+RF/GB・特徴50）| L-129 / 30-40% 天井 |
| 2026-04-25 | 経緯未把握での退路提案 | L-127 / 過去却下方針への退路禁止 |
| 2026-04-26 | HMM研究プロジェクト開始（Day 1〜3）| L-131〜135 / Day 3 で 2割合致・実質不合格 |
| 2026-04-26 | データ駆動原則（閾値）| L-130 / mean±0.3σ で候補B確定 |
| 2026-04-26 | HMM 異種特徴混合の罠 | L-134 / 方向系のみが原則 |
| 2026-04-27 | Mom 1h(10) ルール試行 | 候補B数値合格・継続性ダメ（5日刻み張り付き） |
| 2026-04-27 | 段階6 変化点検知（PELT）試行 | 失敗（5日刻み張り付き） |
| 2026-04-27 | 教師あり再挑戦の議論（B案・1825日ラベル）| まこさん「前回失敗と同じことやっても前進しない」で停止 |
| 2026-04-27 | **判定軸マトリクスのヌケモレ発覚** | **時間粒度・指標カテゴリ・集約方法の大半が未試行** |
| 2026-04-27 | feedback_exhaustive_search 確立 | 「全パターンやり尽くせ」memory 化 |
| 2026-04-27 | regime_research.md 正本化 | このファイル |
| 2026-04-27 | **レシピ型設計に方針転換**（L-137）| 試行単位 = 完全レシピ（時間軸×指標×集約×閾値）。部品単独評価は廃止 |
| 2026-04-27 | 1826日肉眼ラベル付けUI 完成（commit 419f419）| まこさん作業中・現在 365/1826 |

---

## §2 判定軸 網羅マトリクス

「全パターンやり尽くせ」原則（feedback_exhaustive_search）に基づき、**未試行セルを片っ端から潰す**。
`✅` = 試行済（合否は §3 参照）／ `❌` = 試行済不採用／ `🔲` = 未試行／ `△` = 部分試行

### 軸A: 時間粒度

| 粒度 | 状態 | メモ |
|------|------|------|
| 5m | 🔲 | **5m足BOTのスケールに最も近い・最優先候補** |
| 15m | 🔲 | |
| 1h | ❌ | _build_regime_map_hourly + ヒステリシス・L-126で実NET悪化 |
| 4h | 🔲 | |
| 日 | ✅ | 現行採用（_build_regime_map・MA70/slope/ADX）|
| 週 | 🔲 | |
| 月（支配） | △ | まこさん肉眼判定365日のみ・機械化未試行（L-126 月単位本丸）|

### 軸B: 指標カテゴリ（regime判定主軸）

| カテゴリ | 状態 | メモ |
|---------|------|------|
| MA系（MA70/200・傾き）| ✅ | 採用中 |
| ADX系（ADX/DI）| ✅ | 採用中 |
| モメンタム系（RSI/MACD/Stoch）| 🔲 | regime判定としては**未試行** |
| ボラ系（ATR/BB幅）| 🔲 | 単独主軸では**未試行**（L-134 で方向系混合は禁止） |
| 出来高系（Volume/OBV）| 🔲 | **未試行** |
| Funding/OI | △ | L-134で異種混合禁止確認・**単独軸では未試行** |
| Ichimoku | △ | ground truth 用に部分使用・regime本体は未試行 |

### 軸C: 集約方法

| 方法 | 状態 | メモ |
|------|------|------|
| 単一時間軸 | ✅ | 現行（日足のみ）|
| マルチ時間軸合議（日+1h+4h 多数決）| 🔲 | **未試行** |
| 階層型（月支配＞日内補正＞5m発火条件）| 🔲 | **未試行**・L-126整合性最強候補 |
| スコアリング合議（v3）| ❌ | _build_regime_map_v3・L-126で実NET悪化 |
| モデル合議（ルール+HMM+PELT 多数決）| 🔲 | **未試行** |

### 軸D: 判定主体

| 主体 | 状態 | メモ |
|------|------|------|
| ルール | ✅ | 採用中（MA70/slope/ADX）|
| Gaussian HMM | ❌ | hmm_1h_K3_frozen.pkl・2割合致で不合格（L-135）|
| GMM-HMM | 🔲 | pomegranate 未インストール |
| HSMM | 🔲 | hsmmlearn 要対応 |
| MS-GARCH/MS-AR | 🔲 | statsmodels 導入済 |
| 変化点検知（PELT/BOCPD/Window）| ❌ | 段階6 / 5日刻み張り付き |
| UMAP+HDBSCAN | 🔲 | llvmlite ビルド失敗 |
| 教師あり ML（古典 RF/GB）| ❌ | L-129 / 30-40% 天井 |
| 教師あり ML（時系列分類専用 ROCKET/MiniROCKET）| 🔲 | **未試行** |
| 半教師あり（TS2Vec/TF-C）| 🔲 | **未試行** |
| LSTM/Transformer | 🔲 | L-129 過学習リスク |

---

## §3 既試行履歴（時系列）

### 1. 日足ルール判定（現行・採用中）
- ファイル: `runner/replay_csv.py::_build_regime_map`
- 入力: MA70 / MA70_slope(5d) / ADX_14
- 結果: look-ahead プレミアム前提で稼働中。look-ahead 剥離後 SAFE 値は L-128 参照
- 既知欠陥: 5m足BOT のスケールに合わない・日内 regime 切替不可

### 2. 1時間足ルール判定 + ヒステリシス
- ファイル: `_build_regime_map_hourly`
- 結果: L-126 で実NET悪化・**不採用**

### 3. スコアリング型 v3
- ファイル: `_build_regime_map_v3`
- 結果: L-126 で実NET悪化・**不採用**

### 4. Gaussian HMM（段階1）
- ファイル: `models/hmm_1h_K3_frozen.pkl` / `scripts/phase3_hmm_*.py`
- 入力: ma20_dev / ma50_slope / di_diff（1h・5年）
- 結果: 視認2割合致・**不合格**（L-135）

### 5. Mom 1h(10) ルール
- ファイル: `scripts/regime_mom_1h.py` / `results/regime_mom_1h_states.csv`
- 結果: 候補B数値合格・継続性ダメ（5日刻み張り付き）・**不採用**

### 6. 変化点検知 PELT
- ファイル: `scripts/phase6_changepoint_pelt.py` / `results/phase6_pelt_segments.csv`
- 入力: 日足 log_return・rbf model・auto penalty=0.009
- 結果: 数値表面合格だが全 segment が均一5日刻み・**不採用**

### 7. 教師あり ML（週52本ラベル + RF/GB・50特徴）
- 結果: 学習98-100% / 検証31-32%・**過学習で不合格**（L-129）

---

## §4 評価基準（候補B・固定）

`results/phase0_return_distribution.json` のBTC日次リターン分布から導出（L-130 データ駆動）。

| 指標 | 閾値 | 由来 |
|------|------|------|
| UPTREND 平均日次リターン | > +1.22% | mean+0.3σ |
| DOWNTREND 平均日次リターン | < -0.82% | mean-0.3σ |
| RANGE \|平均日次リターン\| | < 0.34% | 0.1σ |
| 状態継続中央値 | ∈ [3, 30]日 | |
| 補助 | t検定 p<0.05 | |
| 月単位視認合致率 | ≥ 60-70%（手法ごとに設定）| L-126 月単位本丸 |

評価本丸は **月単位の支配 regime が肉眼判定と一致するか**（L-126）。机上数値合格でも視認チェック不合格なら不採用。

---

## §5 凍結リソース

- `models/hmm_1h_K3_frozen.pkl` — 段階1 凍結モデル
- `results/phase3_hmm_1h_K3_states.csv` — 状態CSV（43,758行・1h単位・5年）
- `results/phase3_hmm_1h_K3_summary.json`
- `dashboard/data/phase3_hmm.json` — ダッシュボード ⑨タブ
- `data/funding_rate_BTCUSDT_5y.csv` — 5481件・Binance（L-134 用後処理素材）
- `results/phase3_grid_search_summary.csv` — 27パターン探索
- `results/phase1_features_daily.csv` — Day 2 特徴量（1778行×8）
- `data/BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv` — 5年5m足
- `data/regime_ground_truth_daily_human.csv` — まこさん日単位ラベル365日（2025-04-01〜2026-03-31）
- `data/regime_ground_truth.csv` — まこさん週単位ラベル52週
- `results/regime_mom_1h_states.csv` — Mom 1h(10) 試行
- `results/phase6_pelt_segments.csv` — PELT試行
- `results/phase0_return_distribution.json` — 候補B 閾値根拠

---

## §6 既知リスク（L-126〜L-135 要点・必読）

- **L-126**: 月単位支配 regime が本丸・日内regime切替は5m足BOTでは不要
- **L-127**: 過去却下方針への退路提案禁止
- **L-128**: replay_csv.py 3関数すべてに look-ahead バグ・SAFE 値で再評価必要
- **L-129**: 教師あり完全フィット狙いは 30-40% 天井
- **L-130**: 閾値はデータ駆動・mean/std を必ず先に提示
- **L-131**: 単体検証は5-7回・最大15-21回（**設計探索フェーズには適用しない** by feedback_exhaustive_search）
- **L-132**: 特徴量設計は冗長確認後に拡張
- **L-133**: WORKFLOW 既定タスク盲従禁止・上流前提を毎回疑う
- **L-134**: 異種特徴混合は HMM を支配する・方向系のみが原則
- **L-135**: HMM 安定性(ARI)と分離度はトレードオフ・K=2 は候補B不合格

---

## §7 試行禁止リスト（regime研究関連）

- ❌ HMM 特徴量に Funding Rate / OI / L-S Ratio を直接追加（L-134・5回試行で全失敗）
- ❌ HMM 特徴量にボラ系（ATR/BB幅）を方向系と混合（L-134・分離度ゼロ）
- ❌ K=2 採択（候補B不合格・上昇バイアス問題）
- ❌ ARI 全体値だけで凍結可否判断（L-135）
- ❌ 教師あり学習で ground truth に完全フィット狙い（L-129 で 30-40% 天井）
- ❌ ground truth との完全一致を目標にする
- ❌ 段階1合格後に段階2/3に進む過剰最適化（合格時のみ即Replay移行）
- ❌ 根拠なき閾値提示（L-130）
- ❌ 設計判断を感覚で進める（feedback_quantitative_comparison）
- ❌ ユーザーの感覚発言を採用根拠化する
- ❌ WORKFLOW フェーズと照合せず脇道に逸れた提案を出す（L-133）
- ❌ **判定軸マトリクスの未試行セルを残したまま「もう手は無い」と撤退する**（feedback_exhaustive_search）

---

## §8 探索戦略（レシピ型・L-137 で書き換え）

部品単独評価は廃止。試行単位 = **完全レシピ**で、軸AとBの 🔲 セルはレシピ内の構成要素として横断的に消化する。

### 探索ステージ

| ステージ | 内容 | 完了基準 |
|---------|------|---------|
| S1: テンプレ起案 | 30〜50 のレシピ・テンプレートをハンドピックで設計（原理駆動）| §10.4 のテンプレ表 30件以上 |
| S2: 閾値前向き選択 | テンプレごとに閾値のみ grid（5×5 程度）→ ベスト閾値版を確定 | 各テンプレに best_score 付与 |
| S3: 上位N抽出 | best_score 上位 N=10 を抽出 | ランキング表 |
| S4: クロス世代 | 上位N同士で「指標差し替え／集約方法差し替え」→ 第二世代テンプレを生成 | 新テンプレ ≥ 20件 |
| S5: 最終OOS | 第二世代上位を Replay（regime_switch=ON）で OOS 評価 | $/regime-day がベースライン超過 |

### 軸A/軸B/軸C/軸D との対応

- **軸A 時間粒度**: レシピの「時間軸セット」要素として消化（単一・複合・階層）
- **軸B 指標カテゴリ**: レシピの「指標セット」要素として消化（カテゴリから1つ以上選ぶ）
- **軸C 集約方法**: レシピの「粒度内集約」「指標間集約」要素として消化
- **軸D 判定主体**: レシピは原則ルール集約。HMM/PELT 等は「指標部品」として再利用可（出力をレシピに食わせる）

> 軸単独で 🔲 を消すのではなく、**レシピを試行することでレシピ内の構成要素セルが ✅/❌ になる**。マトリクスはレシピ評価結果から逆算して更新する。

---

---

## §10 レシピ型設計仕様（草案・レビュー対象）

### §10.1 試行単位の定義

```
レシピ = (時間軸セット, 指標セット, 粒度内集約, 指標間集約, 閾値ベクトル)
```

各要素は以下の値域から1つ以上選ぶ。**1レシピ = 完成品**として扱い、部品単独で評価しない。

#### 時間軸セット
| 種別 | 例 |
|------|-----|
| 単一 | {5m} / {15m} / {1h} / {4h} / {日} / {週} |
| 複合（フラット）| {日, 4h} / {日, 4h, 1h} / {週, 日} |
| 階層 | {月支配, 日} / {月支配, 日, 5m} / {週, 日, 1h} |

#### 指標セット（カテゴリから1つ以上）
| カテゴリ | 候補指標 |
|---------|---------|
| MA系 | MA70傾き(5d) / MA20-50乖離 / MA200位置 / 価格-MA70乖離 |
| ADX系 | ADX14 / DI+ / DI- / DI差 / ADX傾き |
| モメンタム | RSI14 / MACD hist / MACD signal cross / Stoch %K-%D / ROC10 |
| ボラ | ATR14% / BB幅(20,2) / BB位置 / Donchian幅 |
| 出来高 | Volume z-score(20) / OBV傾き / 出来高/ATR比 |
| 外生 | Funding 24h sum / Funding zscore(30d) / OI変化率 |
| 月支配ラベル | まこさん肉眼判定（部品として直接利用可・「自己ラベル直流」は禁止） |

#### 粒度内集約（同一時間粒度の複数指標 → 1スコア）
- `vote`（多数決・各指標の方向 ±1 を集計）
- `weighted_sum`（重み付け線形和）
- `and_chain`（全指標が同方向のときのみ発火）
- `or_chain`（いずれかが発火）
- `score_sum`（連続値スコアを足す）

#### 指標間集約（時間粒度をまたぐ集約）
- `hierarchical`（上位粒度が下位を支配・例: 月支配が DT/UT を確定 / 日が補正）
- `multi_vote`（各粒度の出力 1票として多数決）
- `weighted_sum`（粒度ごとに重み）
- `and_chain`（全粒度が同方向のときのみ）

#### 閾値ベクトル
各指標に1つの cut-off。例: ADX14_min=20 / RSI14_range=[40,60] / MA70_slope_min=0.0 等。
**閾値は S2 で grid 5×5 探索する**（テンプレ起案時は中央値1点を仮置き）。

### §10.2 評価フロー

入力: レシピ → 1日ごとに predict label ∈ {downtrend, range, uptrend}

| 指標 | 計算 | 合格閾値（暫定）|
|------|------|---------------|
| 日次合致率 | (predict == 視認).mean() / ラベル充足日のみ | ≥ 70% |
| 月単位支配合致率 | 月内最頻 predict vs 月内最頻 視認 | ≥ 80% |
| 候補B数値 | DT平均日次<-0.82% / UT>+1.22% / RANGE \|±\| <0.34% | 全カテゴリ通過 |
| 状態継続中央値 | predict の連続日数の中央値 | ∈ [3, 30]日 |
| 5日刻み張り付き | 連続区間長の最頻値 = 5 でない | 必須 |
| **R01比NET方向チェック**（任意・S3で実施）| regime_switch=ON Replay の合計NET差分 ΔNET = NET(候補) − NET(R01) | ΔNET ≥ 0 を期待（ソフト基準・タイブレーク用）|

> **ラベル部分対応**: 365日ラベル充足部のみで一次スコアを出す（1826日完了を待たない）。各レシピのスコアに「ラベル充足月のみで集計」と注記。1826日完了後に最終評価で再走。
>
> **R01比NET方向チェック**: S2（閾値前向き選択）まではラベル合致率と候補B数値で絞る。S3（上位N抽出）で同点・僅差が並んだとき、R01ベースラインを下回るものをタイブレークで落とす。**S5最終OOSの代替ではない**（最終GO/NOは依然 365d Replay）。
>
> **365日データの構造的限界**（2026-04-27 smoke test で判明）:
> - 365日肉眼ラベルは downtrend 102日(27.9%)含むが、**月内で連続せず散発するため月支配 DT 月が0件**（month-mode は range 8月 / uptrend 4月 / DT 0月）
> - hierarchical で M_dom を上位に置くレシピ（R03/R13〜R18）は、365日データだと **DT 予測が一度も出ず dt_mean_pct=nan** になる
> - これはバグではなくデータの性質。1826日完了後に DT 連続局面が含まれた状態で再評価が必要
> - 365日スコアでの判定では、`coverage_months` と各 regime の出現有無を必ず確認してから順位付けする

### §10.3 既存資産の扱い

| 資産 | 扱い |
|------|------|
| `cat/indicators.py`（ATR/RSI/MACD/ADX/Stoch）| **流用**: レシピの指標部品として使う |
| `data/BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv` | **流用**: 入力 5m OHLCV |
| `data/regime_ground_truth_daily_human.csv` | **流用**: 評価ラベル（365→1826へ拡張中）|
| `results/phase0_return_distribution.json` | **流用**: 候補B閾値の根拠 |
| `models/hmm_1h_K3_frozen.pkl` | **指標部品としては再評価から**（レシピ内に組み込むなら出力を1指標扱い）|
| `scripts/regime_mom_1h.py` / `phase6_pelt_segments.csv` | **指標部品扱いのみ**（単独主軸では再採用しない）|
| `runner/replay_csv.py::_build_regime_map_*` | **流用**: ベースラインレシピ（現行ルール）として S2 のリファレンス |

### §10.4 初期テンプレート例（30件目標・草案12件先出し）

> 凡例: **TF**=時間軸 / **IND**=指標 / **AGG_in**=粒度内集約 / **AGG_cross**=指標間集約 / **TH**=閾値中央値（仮）

| ID | TF | IND | AGG_in | AGG_cross | TH（仮）| 狙い |
|----|----|-----|--------|-----------|--------|------|
| R01 | 日 | MA70傾き / ADX14 | weighted_sum | — | slope=0, ADX=20 | 現行ルール再現（ベースライン）|
| R02 | 日, 1h | MA70傾き / ADX14 | weighted_sum | multi_vote | 同上 | 1h ヒステリシスを多数決で取り込む |
| R03 | 月支配, 日 | 月=肉眼ラベル / 日=ADX14 | — / score | hierarchical | ADX=25 | L-126 月支配＞日補正 |
| R04 | 4h | MACD hist / ADX / DI差 | vote | — | hist=0, ADX=25, DI=5 | 4h単独・モメンタム主軸 |
| R05 | 週, 日 | 週=MA20傾き / 日=RSI14 | — / vote | hierarchical | slope=0, RSI=[40,60] | 週支配＞日補正 |
| R06 | 日, 1h | 日=RSI14 / 1h=Stoch %K(14,3,3) | vote (粒度内) | multi_vote | RSI=[40,60], %K=[20,80] | レンジ判定特化（日トレンド + 1h オシレータ）|
| R07 | 日 | ATR14% / BB幅 | weighted_sum | — | ATR%=2.0, BB=4.0 | ボラ主軸（L-134 単独なら可）|
| R08 | 日, 4h, 1h | MA70傾き（全粒度）| — | multi_vote | slope=0 | マルチ時間軸合議 |
| R09 | 日, 4h | 日=MA70 / 4h=MACD hist + ADX | weighted / score | hierarchical | slope=0, ADX=25 | 階層 + 4hモメンタム補正 |
| R10 | 日 | MA70傾き / ADX / RSI / ATR% | weighted_sum | — | 4軸統合 | 全カテゴリ統合スコア |
| R11 | 日 | OBV傾き / Volume zscore | vote | — | OBV>0, vz=±1 | 出来高主軸（カテゴリ網羅）|
| R12 | 日 | Funding zscore(30d) / MA70傾き | weighted | — | fz=±1, slope=0 | 外生×方向系（L-134 ルール集約なら可）|

#### 優先1: 月支配変種（6件）

| ID | TF | IND | AGG_in | AGG_cross | TH（仮）| 狙い |
|----|----|-----|--------|-----------|--------|------|
| R13 | 月支配, 日 | 月=肉眼ラベル / 日=MA70傾き(5d) | — / score | hierarchical | slope=0 | R03 の ADX 版を MA70 に差し替え。月不確定領域を日 MA70 で補正 |
| R14 | 月支配, 日, 4h | 月=肉眼 / 日=ADX14 / 4h=MACD hist | — / score / score | hierarchical (3層) | ADX=25, hist=0 | 月支配＞日強度＞4hモメンタム（最も階層が深い）|
| R15 | 月支配, 日 | 月=肉眼 / 日=RSI14 + Stoch %K | — / vote | hierarchical | RSI=[40,60], %K=[20,80] | 月レンジ寄り月の日内オシレータ補正 |
| R16 | 月支配, 4h | 月=肉眼 / 4h=ADX14 + DI差 | — / vote | hierarchical | ADX=25, DI=5 | 月確定月のみ採用・不確定月は4h判定 |
| R17 | 月支配, 日 | 月=肉眼 / 日=BB位置 + ATR14% | — / weighted_sum | hierarchical | BB=±1σ, ATR%=2.0 | 月支配＋日ボラ補正（変動レジーム判定）|
| R18 | 月支配, 日 | 月=肉眼 / 日=Funding zscore + MA70傾き | — / weighted | hierarchical | fz=±1, slope=0 | 月支配＋日外生補正 |

#### 優先2: 4h変種（5件）

| ID | TF | IND | AGG_in | AGG_cross | TH（仮）| 狙い |
|----|----|-----|--------|-----------|--------|------|
| R19 | 日, 4h | 日=MA70傾き / 4h=ADX14 + DI差 | — / vote | hierarchical | slope=0, ADX=25, DI=5 | 日方向＞4h強度確認 |
| R20 | 4h | 4h=MA50傾き + ADX14 + RSI14 | weighted_sum | — | slope=0, ADX=25, RSI=[40,60] | 4h単独・3カテゴリ統合 |
| R21 | 4h, 1h | 4h=MACD hist + ADX / 1h=DI差 | score / score | multi_vote | hist=0, ADX=25, DI=3 | 4hメイン1h補正 |
| R22 | 日, 4h, 1h | 全粒度 ADX14 | — | multi_vote | ADX=25 | 同一指標マルチ時間軸合議 |
| R23 | 4h | 4h=BB位置 + ATR14% + Volume zscore(20) | weighted_sum | — | BB=±1σ, ATR%=2.0, vz=±1 | 4hボラ＋出来高（カテゴリ網羅）|

#### 優先3: 5m変種（3件）

| ID | TF | IND | AGG_in | AGG_cross | TH（仮）| 狙い |
|----|----|-----|--------|-----------|--------|------|
| R24 | 5m, 日 | 5m=ATR14% + RSI14 / 日=MA70傾き | vote / score | hierarchical | ATR%=0.5, RSI=[40,60], slope=0 | 日方向＞5m発火条件（誤検知抑制）|
| R25 | 5m, 4h | 5m=ATR14% / 4h=MACD hist + ADX14 | score / score | hierarchical | ATR%=0.5, hist=0, ADX=25 | 4hメイン・5m参考 |
| R26 | 5m | 5m=ATR14% + RSI14 + Volume zscore(20) | weighted_sum | — | ATR%=0.5, RSI=[40,60], vz=±1 | 5m単独（誤検知過多リスク高・リファレンス）|

#### 優先4: その他カテゴリ網羅（6件）

| ID | TF | IND | AGG_in | AGG_cross | TH（仮）| 狙い |
|----|----|-----|--------|-----------|--------|------|
| R27 | 日 | OBV傾き / Volume zscore(20) / 出来高/ATR比 / MA70傾き | weighted_sum | — | OBV>0, vz=±1, vol/atr=1.0, slope=0 | 出来高主軸2件目（R11補強）|
| R28 | 日 | Funding 24h sum / Funding zscore(30d) / OI変化率 | weighted_sum | — | f24h=0, fz=±1, oi=±1% | 外生主軸2件目（R12補強）|
| R29 | 日 | Ichimoku（雲位置 + 転換vs基準 + 遅行スパン） | vote | — | 標準値 | Ichimoku 単独主軸 |
| R30 | 日, 1h | 日=Ichimoku雲位置 / 1h=ADX14 | — / score | hierarchical | 雲上下, ADX=25 | Ichimoku 副軸 + 1h強度 |
| R31 | 週 | 週=MA20傾き + ADX14 | weighted_sum | — | slope=0, ADX=20 | 週単独 |
| R32 | 月 | 月=リターン符号 + ADX14 | vote | — | ret>0, ADX=20 | 月単独 |

#### 優先5: and_chain 系（3件・厳格低発火）

| ID | TF | IND | AGG_in | AGG_cross | TH（仮）| 狙い |
|----|----|-----|--------|-----------|--------|------|
| R33 | 日, 4h | 日=MA70傾き / 4h=MACD hist | — | and_chain | slope=0, hist=0 | 多時間軸 AND（同方向のみ確定）|
| R34 | 日, 4h, 1h | 全粒度 MA70傾き同方向 | — | and_chain | slope=0 | 3時間軸 AND |
| R35 | 日 | MA70傾き + ADX14 + RSI14 全部同方向 | and_chain | — | slope=0, ADX=25, RSI=[40,60] | 単粒度 4軸 AND |

> **合計 35件**（R01〜R35）。30件目標を達成。
>
> **🔒 凍結: 2026-04-27**（事前判断で絞らず全件採用。L-137 部品単独評価バイアス回避と整合）。重複・冗長は S2/S3 結果から逆算してクロス世代（S4）で整理する。閾値中央値（仮）は S2 grid で本確定する。

### §10.5 残テンプレ起案の方針

優先順（上から順に枠を埋める）:

1. **月支配変種**（最優先・L-126 月単位本丸と整合）
   - 月支配ラベル × 日補正 × 各指標カテゴリ で最低 6件
   - 集約は hierarchical 中心。月支配の確定領域 / 不確定領域での日補正の分け方を変える
2. **4h変種**（次優先・5m足BOTスケールと月支配の中間粒度）
   - {4h単独} / {日, 4h} / {4h, 1h} / {日, 4h, 1h} を各カテゴリ主軸で最低 5件
   - hierarchical / multi_vote / weighted_sum を各1件以上
3. **5m変種**（5m足BOTスケール最近接）
   - 5m単独・5m+4h・5m+日 で最低 3件
   - 5m単独は誤検知過多リスク高 → 上位粒度との合議を優先
4. **その他カテゴリ網羅**
   - 出来高 / 外生 / Ichimoku を主軸または副軸に含むレシピを各2件
   - 週・月足単独 を最低各1件
   - and_chain（厳格・低発火）系を最低3件で複雑度バランス確保

各優先帯を埋めた段階で 30件目標に到達する見込み。30件未満なら優先1から追加起案する。

### §10.6 harness 実装イメージ

新規スクリプト: `scripts/recipe_grid_search.py`

```
入力:
  - configs/recipes.yaml         # テンプレ定義（30〜50件）
  - data/BTCUSDT-5m-...-5y.csv   # 5m OHLCV
  - data/regime_ground_truth_daily_human.csv  # ラベル
出力:
  - results/recipe_scores.csv
    (recipe_id, threshold_combo, daily_acc, monthly_acc,
     dt_mean, ut_mean, range_abs_mean, run_median_days,
     mode_run_len, candidate_b_pass, label_coverage)
```

処理:
1. レシピ定義を読み、指標を全粒度で precompute（cat/indicators.py 流用）
2. 各レシピ × 各閾値組合せで日次 predict label を生成
3. 視認ラベルと突合 → §10.2 の指標を全部計算
4. CSV 出力 → 上位ランキングを ranked json に保存
5. ベースライン R01 との差分も同時出力

#### トップ10サマリ出力仕様

`results/recipe_scores.csv` とは別に、人間レビュー用に `results/recipe_top10.md` を自動生成する。

```
入力: recipe_scores.csv 全件
ソート: 月単位支配合致率 desc → 日次合致率 desc → ΔNET（R01比）desc
抽出: 上位10件
```

Markdown フォーマット（1レシピ = 1ブロック）:

```markdown
## #1 R03 月支配＋日補正  [score 0.83 / 0.74 / +$1.2/dt-day]

- TF: 月支配, 日 / IND: 月=肉眼ラベル / 日=ADX14
- AGG: hierarchical (月→日)
- TH: ADX14_min=25
- 月単位支配合致率: 83% (29/35月)  日次合致率: 74% (271/365日)
- 候補B: ✅ DT=-1.05% / UT=+1.45% / RANGE=±0.22%
- 状態継続中央値: 8日 / 5日刻み張り付き: なし
- ΔNET (R01比): +$1.2/dt-day  ← S3 タイブレーク参考値
- ラベル充足: 35/35月（365日完全充足）
- 不一致月トップ3: 2025-08(D→R) / 2025-12(U→R) / 2026-02(R→D)
```

末尾に R01 ベースラインと「上位10で共通する構成要素」（時間軸/指標/集約のヒストグラム）を追加。

> 出力スコープ: スコア表（CSV）はマシン処理用、上位10サマリ（MD）は人間レビュー用。CSV を都度grepする運用にしないこと。

### §10.7 レビュー観点（まこさん向け）

1. レシピの構成要素定義（§10.1）に過不足はないか
2. 評価指標の合格閾値（§10.2）は妥当か
3. 初期テンプレ12件（§10.4）に「これは試したい」「これは却下」の意見
4. 残18件起案方針（§10.5）の優先カテゴリ
5. harness スコープ（§10.6）— 最初から CSV 全部出すか段階的か

---

## §9 関連ファイル

- **CLAUDE.md** — 設計思想（日足MA70・3レジーム切替）
- **WORKFLOW.md** — 現フェーズ・次タスク。regime詳細はこのファイル参照
- **lessons_active.md L-126〜135** — 経緯詳細
- **signal_ledger.md** — シグナル候補とPriorityマッピング
- **archive/workflow/WORKFLOW_20260427.md** — 段階1〜3 完了報告（参考）
- **.claude/memory/phase8_supervised_tool_survey.md** — 教師あり手法詳細リスト（参考）
- **memory/feedback_exhaustive_search.md**（プロジェクト外）— 全パターンやり尽くせ原則
- **memory/feedback_question_patterns.md**（プロジェクト外）— 前提揺さぶり質問パターン

---

## 更新ルール

- 新しい軸セルを試行したら §2 マトリクスのセルを更新（✅/❌）
- 試行詳細は §3 履歴に1行追加
- 経緯転換点があれば §1 タイムラインに1行追加
- WORKFLOW.md / lessons_active.md / signal_ledger.md と矛盾を見つけたらこのファイルを正本として他を直す
