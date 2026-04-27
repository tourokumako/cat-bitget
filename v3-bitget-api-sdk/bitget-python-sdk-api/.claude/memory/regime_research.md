# regime_research.md — レジーム判定研究 唯一の正本

> このファイルは **regime 判定研究の全集約** です。
> WORKFLOW.md / phase8_supervised_tool_survey.md / lessons_active.md L-126〜135 / signal_ledger.md / CLAUDE.md
> に分散していた regime 関連情報をここに集約。**矛盾を見つけたらこのファイルを更新**して、他は参照リンクに留める。
>
> 段階1〜8 の表記は廃止。**判定軸マトリクスと試行ログ**で進捗管理する。

最終更新: 2026-04-27

---

## §0 現フェーズ

**フェーズ: 判定軸 網羅マトリクスやり直し**
**Priority個別最適化: regime確定まで全停止（CLAUDE.md・WORKFLOW.md 共通）**

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

## §8 次の優先未試行セル

判定軸マトリクスの 🔲 セルから「5m足BOTスケール整合 × 実装コスト低 × L-126整合」で優先順位付け。

| 優先 | 軸 | 内容 | 根拠 |
|------|----|------|------|
| 1 | 軸C 階層型 | 月支配（まこさんラベル365日）＞日内補正（日足MA70）＞5m発火条件 | L-126 月単位本丸と整合・既存データのみで実装可・コスト低 |
| 2 | 軸A 5m | 5m足直接判定（5m ATR/RSI/MACD で都度判定）| 5m足BOTのスケールに最も近い |
| 3 | 軸C マルチ時間軸合議 | 日 + 4h + 1h の多数決 | 既存 _build_regime_map_hourly 流用可 |
| 4 | 軸B モメンタム系（RSI/Stoch を主軸）| RSI レンジ判定 + Stoch クロス | 未試行カテゴリ |
| 5 | 軸D MiniROCKET（教師あり時系列分類）| 365日ラベルで時系列分類専用手法 | L-129 とは手法が違う |
| 6 | 軸D 半教師あり（TS2Vec）| 5年無ラベル + 1年ラベル | ラベル不足を構造的に補う |
| 7 | 軸C モデル合議 | ルール+HMM+PELT 多数決 | 既存試行済モデルの再利用 |
| 8 | 軸A 週・月 | 週/月足の単独判定 | L-126整合 |
| 9 | 軸B ボラ系単独 | ATR を主軸（L-134 単独なら可）| カテゴリ網羅 |
| 10 | 軸D HSMM/MS-GARCH | hsmmlearn 等の追加導入 | 実装コスト中 |

> 着手順は議論で確定する。マトリクスの全 🔲 セルを潰し切るまで撤退禁止。

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
