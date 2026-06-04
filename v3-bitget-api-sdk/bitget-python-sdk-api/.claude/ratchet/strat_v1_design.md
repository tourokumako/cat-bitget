# strat_v1 詳細設計（A・ratchet E2「最初の本物の戦略」）

作成: 2026-06-04
位置付け: ratchet E2 = v1 戦略の詳細設計（A・設計パラメータ）。`score.py`（固定審判）で採点する前の設計報告。
ステータス: **設計確定・実装前（GO待ち）**。実装は本書の確認後に着手。
出典: `cat_requirements.md` §4.6 H1-H14 / 2026-06-04 まこさん×CC 設計議論 / WebSearch 裏取り（末尾§9）。

---

## §1 目的・位置付け

手動 cat_v9 の勝ち筋（複数指標のコンフルエンス）を ML（決定木）でデータから学び、正しい計器（eval_engine/score.py）で**手動の地面（採点期間 2025-04〜12 の月平均 $172）を超えるか**を測る。v1 はラチェットの「最初の本物の戦略」で、ここを基準点に v2 以降で1改修ずつ net を積む。

最終目標は月次 NET ≥ $1,900 全月クリア。v1 はその土台。

---

## §2 判定設計（2層・複合エッジに整合）

トレード損益は複合要因（コンフルエンス）から出るため、要素の効き目を単純な引き算で測ると相関要素が互いを肩代わりして見えなくなる（de Prado の substitution effect）。よって判定を2層に分ける:

1. **採用判定（一次・ratchet 正式）= 戦略まるごとの net**。`score.py`（採点期間 2025-04〜12）の月次 net が手動 $172 を超えたか。要素単位でなく**戦略単位**。「数字が上がった変更だけ残す」はここ。
2. **効いた要素の診断（二次）= ブロック単位 ablation（除去実験）**。相関する材料は同じブロックに束ねて一緒に引く（de Prado Clustered Feature Importance の発想）。regime抜き / MTF抜き / 側統合 で再採点し net 差分＝そのブロックの「居ないと困る度」。これは採用/破棄でなく「次の周でどこを伸ばすか」の方向付け。

⚠️ ablation でも交互作用込みで純粋な単独寄与は出ない（完全な因果分解は不可能）。方向付けの診断として使う。

---

## §3 構成（最初の構成・確定）

| 項目 | v1 の値 | 備考 |
|---|---|---|
| **モデル** | LONG/SHORT 別の LightGBM 2値分類 ×2本 | 手動の非対称性（SHORT5/LONG4）を継承。木の枝＝AND＝コンフルエンス |
| **ラベル** | 各bar・各sideを固定出口で simulate → **net>0 なら勝ち(1)/負け(0)** | net 直結で採用判定と一致（meta-labeling の発想） |
| **出口（固定maker）** | LONG: TP+0.6%/SL−2.0%/保有96bar(8h)　SHORT: TP+0.8%/SL−2.0%/96bar | 手動代表値が出発点。ラベルのバリア＝実出口を一致（v1単純化）。将来ML化 |
| **エントリー閾値** | 木が出す勝率 ≥ θ で入る（θ=0.5初期）。両side超なら高確率の1side | 手動の排他（先勝ち）に対応。θ はツマミ |
| **サイズ** | 1ポジ固定 0.024 BTC（比較用）。同時保有合計≤0.12 enforce | H1/H10 |
| **期間** | 学習 2021-04〜2025-03 / 採点 2025-04〜12 / 封印 2026Q1 | H8・ratchet合意 |
| **約定** | entry/出口とも指値 maker・不約定=不成立 | eval_engine が処理 |

戦略側は「bar・side・入るか」を出すだけ。maker約定・不約定・コスト・出口は `eval_engine.simulate_trade` が担当。

### §3.1 特徴量（手動材料ベース・矮小化しない・1432全投入はしない）

CLAUDE.md「1432全投入・事前絞り込み禁止」は ratchet 以前の指標矮小化グセへの矯正措置（2026-06-04 まこさん）。ratchet の今は手動材料ベースで始めてよい。ただし**矮小化しない**（手動が使う材料は使い切る）。

#### 閾値とパラメータの扱い（木の役割分担・2026-06-04 整理）
- **閾値**（ADX≥いくつ 等）: 特徴量に入れない＝**木が各列ごとにデータから自動で決める**。各足×各指標×時間軸を生値で渡せば、木が「どの足のどの指標をどの値で切るか」を見つけ、AND連鎖でコンフルエンスを構成する（要件§6「具体数値を焼き込まず木に切れ目を探させる」）。事前離散化しない（木の邪魔になる）。
- **パラメータ＝指標期間**（RSI21・MACD12/26/9 等）: 木は自動で動かせない（材料生成段階の設定）。よって**短期/中期/長期の複数期間を材料として用意 → 木が場面ごとに効く期間を選ぶ**（＝実質的なパラメータ学習）。同じ指標でも期間で別物のシグナルになり、どの期間が勝つかは相場局面依存のため。無限には増やさない（列爆発・ノイズ → 効かない期間は ablation で削る）。**V9 期間（RSI21・MACD12/26/9・Stoch14/3・RCI7/9/52・ADX14・BB20・EMA20）は必ず候補に含める**。

#### 材料の構成（3ブロック + 時間軸）

- **A. コンフルエンス材料（手動10指標 + ローソク足の形 + バンドタッチ）**
  - **指標**（パラメータを持つものは短期/中期/長期の複数期間を用意・上記方針）: ADX / ATR(pct) / BB(mid_slope・width・%b・2σ) / EMA乖離 / MACD(line/signal/hist/hist_change のpct) / RCI / RSI / Stoch(K/D) / location_prev / risk_score
  - **A-1 現在値**: 各指標の今の値
  - **A-2 時間軸**（明示的に列にする・木は時間を内蔵理解しないため）:
    - ラグ … 主要指標の t-1/t-3/t-5/t-10 の値
    - 変化量 … 差分・傾き（ADXスパイク等）
    - ローリング … 過去N足の平均/最大/最小/ばらつき（BB傾き5足平均・位置）
    - 遷移 … Stoch/RCI/MACD のクロス・N足連続フラグ
  - **A-3 ローソク足の形**（V9 が全Priで陽線/陰線を使用・2026-06-04 追加）: close/open/high/low の関係 = 実体の符号（陽線/陰線）・実体サイズ・上ヒゲ/下ヒゲの長さ（いずれも pct 表現・H6）
  - **A-4 バンドタッチ**（P22 bb_upper_touch 由来・2026-06-04 追加）: high vs BB上限 / low vs BB下限 の接触（%b は close ベースのため別に持つ）
  - 根拠: 手動も時間軸を多用（P2 2足連続 / P4 過去10足プルバック / P25 ADX3足前スパイク / BB傾き5足平均 / location_prev）
- **B. regime（相場状態）**: 方向＋確信度。`results/regime_step1/` の出力を merge。手動の最大欠陥（上げ相場で LONG が負ける）を、木が相場状態を条件分岐に使って吸収
- **C. MTF（複数時間足・5m〜4h）**: 上記主要指標の 15m/30m/1h/4h 版。手動に完全欠落（KB §5/§8）。例「MA20 が 1h・15m・5m 全部上向き」のような揃いを木が学べる。**指標期間（A）とは別軸**（「5m足のRSI14」「1h足のRSI14」「5m足のRSI50」は全部別物）

---

## §4 §4.6 ハード制約 H1-H14 照合

| # | 制約 | v1 での扱い | assert |
|---|---|---|---|
| H1 | 合計0.12BTC | 1ポジ0.024固定・同時発火時 `assert_position_cap` | ✅ eval_engine既存 |
| H2 | leak/再現性 | ラベル(未来simulate)は教師のみ＝Xに入れない。特徴量は全t時点取得可。MTFはbackward merge。**train末<採点始 を assert + embargo 96bar** | ⬜実装時追加 |
| H3 | net判定 | score.py | ✅ |
| H4 | コスト確定値 | eval_engine定数 | ✅ |
| H5 | 約定モデル(entry/出口maker・不約定) | eval_engine.simulate_trade | ✅ |
| H6 | 価格非依存 | pct化parquet使用・バリアも%・USD絶対値ラベル無し | ⬜select時に絶対値列除外確認 |
| H7 | 5m標準 | 5m基軸 + MTF上位足 | ✅ |
| H8 | 期間分割 | parquet実timestampで train<2025-04 / 採点2025-04〜12 / 封印不参照 verify | ⬜実装時追加 |
| H9 | 最小注文 | 0.024BTC ≥ 0.0001・≥5USDT | ⬜size assert |
| H10 | サイズ固定値扱い禁止 | 0.024は比較用と明記・0.12内 | check+H1 |
| H11 | 合格/地面 | 採点期間で手動$172超えるか | ✅ score.py |
| H12 | 異常値STOP | 採点後 勝率>70%/月NET>$3,800 等→該当なら「異常値・要調査」 | ⬜採点後チェック |
| H13 | judge固定 | eval_engine/score.py 改造しない | ✅ |
| H14 | 発注フラグ | run_once/replay実行しない・paper維持 | check |

---

## §5 実装で新規 / 既存流用

- **新規**: `strat_v1.py`（parquet読込→特徴量select→側別LightGBM学習(trainのみ)→採点期間推論→θ判定→`eval_engine.simulate_trade`→売買記録CSV）＋ ラベル生成（固定出口simulate→net符号）＋ assert群（H2/H6/H8/H9/H12）
- **流用（改造禁止・H13）**: `eval_engine.py` / `score.py` / `labels_mfe_mae_pct_*.parquet`（特徴量・pct化済）/ `results/regime_step1/*.parquet`（regime）

---

## §6 採点・診断手順

1. `score.py trades_v1.csv --start 2025-04-01 --end 2025-12-31` → 月次net → 手動$172比較・ledger E2 記録
2. H12 異常値チェック
3. （次の周）ブロックablation: regime抜き / MTF抜き / 側統合 で再採点し net 差分

---

## §7 実装の最初の一手で潰す不確実点（着手前に確認）

1. parquet 実timestamp range（train末 < 採点始・採点期間カバー）→ H8境界確定
2. 手動10指標の pct 列の実在列名（select対象の特定）+ MTF 各足の列名
3. `regime_step1/` のどの出力（ensemble/rule/hmm）を使うか + leak free 確認（regime研究は凍結だが出力流用可・品質低くても ablation で寄与判定）
4. ラベルの TIME決済時の勝敗（net符号で一貫）
5. embargo幅（保有96barぶん train/採点境界を空ける）
6. A-2 時間軸特徴量（ラグ/ローリング/変化/遷移）が parquet に既存か、新規生成が要るか

---

## §8 設計判断の経緯（2026-06-04 議論ログのエッセンス）

- **判定法の修正**: CC の初案「要素を1個ずつ足して切り分け」をまこさんが却下（複合エッジが死ぬ）→ 全部入りで作り引き算（ablation）で診断する2層へ（§2）
- **substitution 対策**: 引き算は最初の構成次第。相関要素は束ねて引く（CFI）。だから機能ブロック単位で構成・診断（§2/§3.1）
- **1432全投入の撤回**: ratchet 前の矯正措置（まこさん 2026-06-04）→ 手動材料ベースで開始
- **entry も maker**: CC の説明漏れ。eval_engine L128-146/L192 で entry 指値maker・不約定モデル実装済（まこさん指摘）
- **時間軸の盲点**: CC のスナップショット中心設計をまこさんが指摘 → 木は時間を内蔵理解しないため A-2 時間軸特徴量を明示追加（§3.1）
- **MTF閾値学習**: 「MA20が1h/15m/5m 全部上向きなら勝率高い」例 → 指標は渡す・閾値と揃いは木が学習・勘をデータで検証（§3.1 C）
- **V9 Entry要素 全数照合 + 材料追補（2026-06-04）**: cat_v9_decider/params 精読で §3.1 を照合 → 10指標・系列要素は網羅、ただし ①ローソク足の形(A-3) ②バンドタッチ(A-4) ③パラメータ複数期間 が明示漏れ → 追補。Entry外（MAX_ADDS/Exit/サイズ/動的TP）は v1 スコープ外と切り分け。**指標期間=パラメータは閾値と別**（木は期間を自動最適化できない → 短/中/長の複数候補を用意し木が選ぶ＝実質パラメータ学習）

---

## §9 業界裏取り（WebSearch・2026-06-04）

- Clustered Feature Importance / substitution effect（de Prado）: [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3517595) / [Medium 解説](https://medium.com/@lucasastorian/understanding-financial-feature-importance-7eeb49c2df0b)
- コンポーネント単位 ablation で marginal contribution（PnL metric）: [Regime-Aware LightGBM, MDPI](https://www.mdpi.com/2079-9292/15/6/1334) / [Bitcoin ML, arXiv](https://arxiv.org/html/2407.18334v1)
- regime: feature 同梱 vs 専用モデル分割（分割は遷移期で優位・複雑さ増）: [Two Sigma](https://www.twosigma.com/articles/a-machine-learning-approach-to-regime-modeling/)
- meta-labeling（方向と枚数を分離・primary→secondary）: [Wikipedia](https://en.wikipedia.org/wiki/Meta-Labeling) / [Hudson & Thames](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/)
- 木に時間軸を入れる標準（lag/rolling・木は時間を内蔵理解しない）: [Tree-Based Models for Time Series, MLMastery](https://machinelearningmastery.com/forecasting-the-future-with-tree-based-models-for-time-series/) / [LightGBM Time Series, GeeksforGeeks](https://www.geeksforgeeks.org/machine-learning/time-series-using-lightgbm/)
