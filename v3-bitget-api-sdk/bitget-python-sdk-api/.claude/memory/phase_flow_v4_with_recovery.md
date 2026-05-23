# V4 学習フロー (Phase ごとの学習内容が主役・分かりやすく版)

作成日: 2026-05-21 (V4 版・第 4 回書き直し・フロー主軸構成)
作成者: CC (cc_role.md v1)
保存先: `.claude/memory/phase_flow_v4_with_recovery.md`
前身: `.claude/memory/archive/phase_flow_v3_with_recovery_20260521.md` (V3 版・archive)
連携設計図: `.claude/memory/learning_design_v4.md` (V4.1・336 行・確定済)
目的: **各 Phase で何を学習するか・どう改善されるか**を、フローの順番でわかりやすく記述

---

## §1 用語集

### ML / アルゴ系

| 用語 | 意味 |
|---|---|
| **ML** | Machine Learning (機械学習・過去データから法則を学んで予測) |
| **LightGBM** | 機械学習ライブラリ (主軸・決定木の集合体) |
| **XGBoost / CatBoost** | LightGBM 競合 (Phase 3-a で比較) |
| **MiniROCKET** | 時系列特化型 ML (Layer 3 で検討) |
| **objective** | 目的関数 (= 何を最適化するか・regression / binary / multiclass 等) |
| **regression / binary / multiclass** | 目的関数の種類 (連続値予測 / 1か0の二値 / 複数クラス分類) |
| **Optuna** | ハイパラ最適化ライブラリ (探索範囲を指定して自動で最良値を探す) |
| **Fractional differentiation** | 元データの記憶を保ちながら定常化する数値処理 (Lopez de Prado AFML Ch.5 推奨) |
| **PCA** | Principal Component Analysis (主成分分析・次元圧縮) |
| **Walk-forward / Purged K-fold / CPCV** | 時系列汎化検証手法 |
| **Class balancing / Focal loss** | 不均衡データ対処手法 (Entry でない 98% が支配する問題への対処) |
| **Triple Barrier** | TP/SL/TIME 3 クラス分類 (Lopez de Prado 提唱) |
| **Meta-labeling** | 1 段階予測 → 2 段階で「採用 / 見送り」判定する 2 段階構成 |
| **entropy lift** | ランダム比較で情報量がどれだけ増えたか (% 表示・閾値 10% で再設計推奨) |

### データ系

| 用語 | 意味 |
|---|---|
| **parquet** | データ保存形式 (列指向・CSV より速い) |
| **5m bar** | 5 分足ローソク (始値・高値・安値・終値) |
| **MFE** | Maximum Favorable Excursion (Entry してからの最大含み益) |
| **MAE** | Maximum Adverse Excursion (Entry してからの最大含み損) |
| **pct** | percent (%・USD 絶対値ではなく価格比率) |
| **K (K=12 等)** | 何本後を見るか (K=12 = 1 時間後 = 5m × 12) |
| **TP / SL** | Take Profit (利確) / Stop Loss (損切り) |
| **MTF** | Multi Time Frame (5m / 15m / 30m / 1h / 4h / 1d / 1w / 1M を同時に見る) |

### 構造系

| 用語 | 意味 |
|---|---|
| **23 軸** | ML 設計の構成要素カタログ (A-1〜A-7 + B-8〜B-15 + D-α〜D-θ・cc_role.md §1.6 参照) |
| **T1-T5** | 5 つの学習タスク (Entry 予測 / 質分類 / Exit / 配分 / 発火フィルタ) |
| **Layer 1 / 2 / 3** | 学習設計階層 (1 = 最低限・2 = 追加最適化・3 = 構造変更) |
| **CP1〜CP5** | 各 Phase 完了時の独立 verify ゲート (Claude `/audit` 経由) |
| **cluster** | クラスタ (Entry 性質分類グループ・k=3 確定) |
| **hedge_mode** | LONG/SHORT 同時保有可能ポジションモード (Bitget 仕様) |

### 業務系

| 用語 | 意味 |
|---|---|
| **NET** | 純利益 (手数料・スリッページ・Funding 控除後) |
| **Replay** | 過去データ売買シミュレーション (= バックテスト) |
| **Funding** | 8 時間ごとに発生する LONG/SHORT 間の精算金 |
| **leak** | 未来データを過去のフリで使う不正 (絶対禁止・false_positive §0-1) |
| **合計 0.12 BTC 厳守** | 保有中の全ポジション合計上限 (false_positive §0-2・1 ポジ上限ではない) |

---

## §2 Phase ごとの学習内容 (本書の主役)

### Phase 0 改修: 特徴量を増やす + ラベルを再生成

**何を学習するか**: **学習はしない**。次の Phase 1 で使う「特徴量データ + 正解ラベル」を作るだけ。

**学習方法**: **該当なし** (Phase 0 は parquet 生成のみ・ML 学習なし)

**入力 → 処理 → 出力**:
- 入力: BTC 5y CSV (Bitget 取引所から取得済)
- 処理: 5 分足ごとに「指標を計算 + 未来 MFE/MAE を計算」
- 出力: parquet ファイル 3 種 (train 2021-2024 / 仮 test 2025 / 本 test 2026 Q1)

**特徴量に追加するもの (1432 列 → 約 2000-2500 列)**:

| 追加カテゴリ | 内容 | なぜ追加するか |
|---|---|---|
| 欠損指標 8 件 | RCI(7/9/52) / RSI(21) / RSI_slope / BB_slope / Stoch(5m) | 既存 1432 で抜けていた基本指標 |
| まこさん発振系 3 件 | RSI ROC / Stoch K-D 差分 / MACD ヒストグラム slope | 手動 Priority で使ってきた発振系 |
| 業界カタログ追加 | TA-Lib / pandas-ta / Murphy / Lopez de Prado の標準指標 | 業界標準を網羅 |
| 1w / 1M MTF | 5m 〜 1d の 6 TF に加えて 週足 / 月足 = 8 TF | 長期トレンドの学習素材を追加 |
| Fractional differentiation | 各価格列に d=0.3 / d=0.5 を適用 | 元の記憶を残しつつ機械学習に向く形に |
| PCA 補助列 | 高相関指標群を圧縮した補助列 | 過学習防止 + 主要パターン抽出 |
| パラメータ並列展開 | rsi21 / adx7 / adx21 / bb_window_10/50 / macd 別パラ | ML 自身に最適パラを選ばせる |

**ラベル (= 正解値)**:
- K = {6, 12, 24, 48, 96, 144, 288} の 7 期間
- 各期間で LONG_MFE_pct (最大含み益 %) と LONG_MAE_pct (最大含み損 %) を計算 = **14 ラベル独立** (SHORT は対称性で流用)
- すべて pct (%) 表記 (USD 絶対値禁止)

**合格条件 (CP1)**:
- 列数 2000-2500 範囲内
- leak 4 点チェック 全 PASS (未来データ参照ゼロ verify):
  1. `.shift(-N)` 等の未来 index 参照 grep
  2. fractal / pivot の `j ≤ i-K` フィルタ verify (L-179)
  3. train timestamp が test 期間に侵入していないか (parquet min/max で確認)
  4. Fractional differentiation の weights で未来時刻使用なし
- parquet 3 種 (train + test 2025 + test 2026 Q1) 物理存在
- 入力 CSV: `*bitget*` 含む (Bitget USDT-FUTURES history-candles 取得済)
- timestamp 連続性 (5min ギャップ以外ゼロ verify)

**Phase -1: USD 絶対値系 blacklist 48 feature drop 義務** (phase_compliance_checklist.md §Phase -1 整合):

Phase 0 改修後の parquet 列から、Phase 1 学習スクリプトが以下 8 ファミリー × 6 TF = **48 列を drop** してから学習する義務:

| ファミリー | 計算式 | 代替 pct 指標 |
|---|---|---|
| sma_20 | rolling(20).mean() (絶対 USD) | close_vs_sma20_pct |
| sma_50 | rolling(50).mean() (絶対 USD) | close_vs_sma50_pct |
| ichimoku_kijun | (26h_max+26l_min)/2 (絶対 USD) | close_vs_kijun_pct |
| ichimoku_tenkan | (9h_max+9l_min)/2 (絶対 USD) | close_vs_tenkan_pct (Phase 0 改修で追加) |
| macd_line | EMA12-EMA26 (USD scale) | macd_line_pct (Phase 0 改修で追加) |
| macd_signal | macd_line の EMA9 (USD scale) | macd_signal_pct (Phase 0 改修で追加) |
| macd_hist | macd_line - macd_signal (USD scale) | macd_hist_pct (Phase 0 改修で追加) |
| macd_hist_change | macd_hist.diff(1) (USD scale) | macd_hist_change_pct (Phase 0 改修で追加) |

理由: 学習期間 BTC 価格 ($30k-$60k) と本番期間 ($100k-$150k) のレンジ乖離で、絶対値ベースの決定木分岐 (例: `sma_20 > $48,000`) は本番で機能しない。Phase 1 で feature_importance top20 に 48 列のいずれかが混入 → 即 STOP・blacklist drop 漏れとして調査。

**失敗時**:
- 列数不足 → 業界カタログ追加 (1 回まで)
- leak FAIL → 該当箇所修正 + 再 build (false_positive §0-1 違反扱い)
- input CSV が `*bitget*` 含まない → ABORT (assertion で起動中止)

**所要時間**: 約 3-6 時間

**該当軸** (補足): A-1 (Entry 指標) / A-3 (パラメータ) / A-5 (MTF) / B-12 (Fractional / PCA)
**Layer**: 前提タスク + Layer 1 ④ 特徴量拡張と統合

---

### Phase 1: Entry の学習を 6 案並列でやって最良案を選ぶ (最重要・v5 Layer 配分逆転・2026-05-22 確定)

**何を学習するか**: 「**Entry すべきかどうか**」を 6 通りの違うやり方で学習し、どれが一番うまく予測できるか比較する。

**なぜ 6 案並列か**:
- 旧 V3 では「14 個のラベル予測 → 比率計算 → 閾値で Entry」という入れ子方式で、Entry 学習が破綻していた (entropy lift 6.04% = ランダムとほぼ同等)
- そこで V4 で「特徴量を拡張するだけで治るか」「ラベル自体を変えれば治るか」を**分離して測る**ために 3 案並列を確定
- **2026-05-22 v5 Layer 配分逆転**: まこさん指摘「学習方法が悪い」を反映し、旧 Layer 3 だった案 d (Ranking LambdaRank) + 案 e (Triple Barrier multiclass) + 案 f (Meta-Labeling 2 段階) を Layer 1 に前倒し → **6 案並列確定**

**6 案の中身**:

| 案 | やり方 | 出力 | Entry 判定 | 役割 |
|---|---|---|---|---|
| **案 a (比較用)** | 14 ラベル独立で MFE/MAE を回帰予測 (旧 V3 方式) | 14 個の予測値 (連続値) | 予測 MFE / 予測 MAE ≥ 1.5 で買う | **改善期待しない・比較用ベースライン** |
| **案 b (本命 1)** | 「Entry すべきか」を 1 か 0 で **直接バイナリ学習** | Entry 確率 (0〜1) | Entry 確率 > 0.5 で買う | 入れ子方式 (回帰→比率) を廃止 |
| **案 c (本命 2)** | 「LONG / SHORT / Flat」の **3 クラス分類** で学習 | LONG/SHORT/Flat の確率 | LONG 確率 > 0.4 で買い / SHORT 確率 > 0.4 で売り | 方向性を 1 段階で直接学習 |
| **案 d (v5 新規・Ranking LambdaRank)** | LightGBM `objective='lambdarank'`・MFE_pct ランキング上位 N% のみ Entry | trade ごとの ranking score | ランキング上位 N% のみ採用 | Stefan Jansen *Machine Learning for Algorithmic Trading* Ch.12-13 整合 |
| **案 e (v5 新規・Triple Barrier multiclass・Lopez de Prado AFML Ch.3)** | TP/SL/TIME 3 クラスラベル (Phase 0 v3.1 で 28 ラベル列生成済) を LightGBM Multiclass で学習 | TP/SL/TIME の確率 | TP 確率 > 閾値で Entry | Lopez de Prado AFML Ch.3 推奨手法 |
| **案 f (v5 新規・Meta-Labeling 2 段階・Lopez de Prado AFML Ch.3)** | 案 e の primary 完了後 sequential 実装・secondary で「primary 予測の correctness」予測 | 採用 / 見送りの確率 | secondary が「採用」と判定したものだけ Entry | precision 改善 + F1-score + Sharpe 向上 (Hudson & Thames mlfinlab 整合) |

**全 6 案共通 (v5 必須)**:
- **Walk-forward Purged K-Fold 5 fold** (Lopez de Prado AFML Ch.7 推奨・mlfinpy.cross_validation.PurgedKFold 経由実装・Layer 3 → Layer 1 前倒し)
- **DSR (Deflated Sharpe Ratio) 採用** (Bailey + Lopez de Prado 2014・SSRN 2460551・selection bias 補正・100+ grid 試行記録義務)

**学習方法**:

| 項目 | 案 a (RMSE 14) | 案 b (Entry Binary) | 案 c (Direction Multiclass) |
|---|---|---|---|
| **アルゴ** | LightGBM | LightGBM | LightGBM |
| **objective (目的関数)** | regression (回帰) | binary (二値分類) | multiclass (多クラス分類・num_class=3) |
| **学習モデル数** | 14 個 (LONG_MFE × K=7 + LONG_MAE × K=7) | 1 個 (Entry 1/0) | 1 個 (LONG/SHORT/Flat) |
| **ラベル定義** | LONG_MFE_pct_K12 等の連続値 (Phase 0 出力そのまま) | K=12 後 MFE_pct > 0.5% かつ MAE_pct > -0.3% なら 1 | LONG_MFE > 0.5% → LONG / SHORT_MFE > 0.5% → SHORT / 両方未満 → Flat |
| **ハイパラ** | デフォルト固定 (num_leaves=31 / max_depth=-1 / learning_rate=0.05 / n_estimators=1000 / early_stopping=50 / **random_state=42**) | 同左 + scale_pos_weight (class imbalance 対策・推定 50:1〜100:1) | 同左・デフォルト |
| **入力 X** | Phase 0 改修出力 約 2000-2500 列 − blacklist 48 列 = 約 1950-2450 列 | 同左 | 同左 |
| **train データ** | 2021-04〜2024-12 (約 4 年・末尾 10% を valid) | 同左 | 同左 |
| **評価方法** | valid RMSE | valid binary logloss | valid multiclass logloss |
| **学習後の比較** | 14 ラベル別 RMSE + simulated PnL | binary logloss + TP Precision + simulated PnL | multiclass logloss + TP Precision + Direction accuracy + simulated PnL |

**Phase 1 verify 義務 (phase_compliance_checklist.md §Phase 1 整合)**:

| # | 項目 | 内容 |
|---|---|---|
| 1.1 | 時系列 valid split | 末尾 10% を valid (random split 禁止) |
| 1.2 | early_stopping=50 / random_state=42 | 上記学習方法表で明示 |
| 1.3 | **1 ラベル完了直後 feature_importance top20 即時 review** | スクリプトに pause 追加・48 blacklist 由来混入なら即 STOP |
| 1.4 | **fractal ベース列 blacklist 3 段階運用 (Defense in Depth)** | 対象パターン: `dist_to_fib_v2_*` / `resistance_distance_*` / `support_distance_*` / `nearest_level_*` ・**(a) top1-20 hit: 即停止 `sys.exit(1)`・leak 残存疑い** ・(b) top21-50 hit: full_rank.csv 保存・Step B 後にレビュー ・(c) top51 以下: 通常運用 |
| 1.5 | lightgbm / sklearn version 記録 | log で出力 |
| **追加** | Phase -1 USD 絶対値 blacklist 48 列 drop | 学習開始前に `X = df.drop(columns=BLACKLIST_COLS)` 実行・完了報告で「drop 件数 = 48」「学習対象 = 約 1950-2450 feature」明示 |

**学習項目 (学習に使う特徴量カタログ)**:

#### A-1: 1432 指標 (現状) + Phase 0 改修で約 2000-2500 列に拡張

##### カテゴリ 1-A: 指標値・推移 (66 ファミリー / 348 列)

トレンド / モメンタム / ボラティリティ / 出来高 / プライスアクション / MTF 整合 等の標準的テクニカル指標群。

**主要ファミリー**:
adx14 / atr14_pct / bb_pct_b / bb_width_pct / bb_width_rank_50b / cmf_20 / di_diff / di_minus / di_plus / div_macd_14b / div_rsi14_14b / donchian_position_20 / donchian_width_pct_20 / ichimoku_kijun / ichimoku_tenkan / macd_hist / macd_hist_change / macd_line / macd_signal / mfi_14 / momentum_10b / mtf_slope_align_3way / obv_slope_10b / pivot_position_100b / pivot_position_50b / realized_vol_20b / realized_vol_rank_50b / roc_10 / roc_20 / rsi14 / rsi7 / sma_20 / sma_50 / stoch_k (1d のみ) / volume_rank_50b / volume_ratio_20b / williams_r (1d のみ) / zscore_return_20b / zscore_return_50b / abs_return_3sigma_20b

**ローソク足パターン**:
bearish_engulfing / bullish_engulfing / bearish_streak / bullish_streak / body_ratio / lower_wick_ratio / upper_wick_ratio / new_high_streak_5b / new_low_streak_5b / pinbar_top / pinbar_bottom

**位置系**:
close_to_high_pct / close_to_low_pct / close_above_cloud / close_below_cloud / close_vs_ema200_pct / close_vs_ema20_pct / close_vs_ema50_pct / close_vs_keltner_lower_pct / close_vs_keltner_upper_pct / close_vs_kijun_pct / close_vs_sma20_pct / close_vs_sma50_pct / close_vs_st_lower_pct / close_vs_st_upper_pct / close_vs_vwap20_pct

##### カテゴリ 1-B: 値動きの形 (20 ファミリー / 347 列)

W 期間窓内の値動きパターン (V 字 / W 字 / M 字 / 倒立 V 字 等) と方向転換回数・swing 距離。

**ファミリー**:
avg_body_ratio_W / avg_lower_wick_ratio_W / avg_upper_wick_ratio_W / bars_since_new_high_W / bars_since_new_low_W / bars_since_swing_high_W / bars_since_swing_low_W / body_direction_flips_W / direction_flips_W / inverted_v_in_W / m_shape_in_W / max_consecutive_new_highs_W / max_consecutive_new_lows_W / new_high_in_W / new_low_in_W / significant_wick_count_W / swing_high_dist_pct_W / swing_low_dist_pct_W / v_shape_in_W / w_shape_in_W

##### カテゴリ 1-C: 構造的要素 (59 ファミリー / 737 列)

サポート / レジスタンス・Fibonacci (フィボナッチ・黄金比ベースの価格水準)・Pivot Point (前日 OHLC から計算する支持/抵抗)・Volume Profile (VAH/VAL/POC・出来高ベースの価格水準)。

**Pivot 系**:
dist_to_PP_pct / dist_to_R1_pct / dist_to_R2_pct / dist_to_S1_pct / dist_to_S2_pct / pivot_zone

**Fibonacci 系**:
dist_to_fib_382_pct / dist_to_fib_500_pct / dist_to_fib_618_pct / dist_to_fib_786_pct / dist_to_fib_v2_382_pct / dist_to_fib_v2_500_pct / dist_to_fib_v2_618_pct / dist_to_fib_v2_786_pct / nearest_fib_distance_pct / nearest_fib_v2_distance_pct

**Volume Profile 系**:
dist_to_VAH_pct (N=50/100/200 × b=020/050/100 の 9 パターン) / dist_to_VAL_pct (同 9 パターン) / dist_to_POC_pct / inside_value_area (同 9 パターン)

**サポレジ系**:
nearest_level_distance_pct / nearest_level_touch_count (N=50/100/200 × t=030/050/100/200 の 12 パターン) / resistance_distance_pct / support_distance_pct

##### Phase 0 改修で追加 (約 568-1068 列・全部 A-1 配下)

| 追加カテゴリ | 内容 |
|---|---|
| 欠損指標 8 件 | RCI(7/9/52) / RSI(21) / RSI_slope / BB_slope / Stoch(5m) |
| まこさん発振系 3 件 | RSI ROC / Stoch K-D 差分 / MACD ヒストグラム slope |
| 業界カタログ追加 | TA-Lib / pandas-ta / Murphy / Lopez de Prado 由来指標 |
| 1w / 1M MTF 拡張 | 既存 6 TF + 週足 / 月足 = 8 TF (ffill で 5m bar 結合) |
| Fractional differentiation | d=0.3 / d=0.5 (Lopez de Prado AFML Ch.5 推奨) |
| PCA 補助列 | 高相関指標群の主成分分析次元圧縮 |
| パラメータ並列展開 | (下記 A-3 参照) |

#### A-3: パラメータ並列展開 (Phase 0 改修で追加)

1432 指標に同種別パラメータを並列追加:

| 指標 | 既存 | 追加 (Phase 0 改修) |
|---|---|---|
| **rsi** | period=7 / 14 | period=21 + 試行 (28, 42 等) |
| **adx** | window=14 | window=7 / window=21 |
| **bb (ボリンジャー)** | window=20 | window=10 / window=50 |
| **macd** | fast=12 slow=26 signal=9 (標準) | fast=5 slow=13 signal=5 (短期版) / fast=19 slow=39 signal=9 (長期版) |
| その他 | (業界カタログから候補追加) |

#### A-5: 時間軸 (time frame・特徴量集計周期)

| 状態 | 時間軸 |
|---|---|
| **現状 (1432 指標)** | 5m / 15m / 30m / 1h / 4h / 1d (= 6 軸) |
| **Phase 0 改修後** | 5m / 15m / 30m / 1h / 4h / 1d / **1w / 1M** (= 8 軸・1w/1M は ffill で 5m bar 結合) |
| **将来 Layer 2 検討** | 3m (検討中) |
| **永久禁止** | 1m (CLAUDE.md §⛔ 提案禁止リスト) |

#### A-4: ラベル期間 K (= 何本後の MFE/MAE を予測するか)

| K | 5 分足換算 | 用途想定 |
|---|---|---|
| K=6 | 30 分 | 超短期 |
| K=12 | 1 時間 | 短期 (Phase 1-b smoke で主判定軸) |
| K=24 | 2 時間 | 中短期 (q99 欠落究明対象・Layer 1 ①) |
| K=48 | 4 時間 | 中期 |
| K=96 | 8 時間 | 中長期 (q95-q99 切り捨て判定対象・Layer 1 ②) |
| K=144 | 12 時間 | 長期 |
| K=288 | 24 時間 | 1 日 |

**14 ラベル独立**: K=7 × {LONG_MFE_pct, LONG_MAE_pct} = 14 (SHORT は対称性で流用・Phase 5 で SHORT 側適用)

**学習後の比較指標 (CP2 で 5 指標物理証跡対比・v5 厳格化・2026-05-22)**:

| # | 指標 | 合格閾値 | 根拠 |
|---|---|---|---|
| 1 | **entropy lift** | **> 10%** | AFML Ch.3 (< 10% で meta-labeling 投入推奨域・Phase 1-c smoke 6.04% は投入域) |
| 2 | **TP Precision** | **> 0.5** | 信頼度 50% 以上 (ベースライン 50% 超え必須) |
| 3 | **Direction Accuracy** (案 c のみ) | **> 0.55** | LONG/SHORT 当たり率 (5% 以上有意性) |
| 4 | **Simulated PnL** | 12 ヶ月中 8+ ヶ月プラス + 年間 NET ≥ $500 | cc_ml_design_spec §1.6 整合 (Position size 未確定なので暫定基準) |
| 5 | **Walk-forward CV Sharpe (DSR 補正)** | **DSR > 1.0** | 本テスト相当 (selection bias 補正後) |

**分岐判定 (CP2・v5 厳格化)**:
- **6 案いずれか 5 指標 ALL PASS** → 採用案で Phase 2 進行
- **6 案ベストでも 5 指標未達** → **即** Layer 3 残存タスク投入 (CPCV + Class balancing / Focal loss + custom loss + アルゴ多様化)
- **「ベスト案で Phase 2 進行して判定」は禁止** (Phase 1 未達 → Phase 2 改善保証なし・v5 厳格化)

**Phase 1 リソース計画 (v5)**:
- 並列度 3 (CPU 競合 + メモリ制約 30-45 GB)
- 学習時間 約 20 時間 (5 fold × 6 案 = 約 1 日)
- Phase 1 全体期間: 約 3-4 週間 (ラベル設計 1 週 + 実装 1-2 週 + 学習 1 日 + CP2 監査 + 結果分析 1 週)

**所要時間**: 約 1-2 週間

**該当軸** (補足): B-15 目的関数 3 案並列 (= Entry 改善の核心) + A-1 (Phase 0 改修出力使用)
**Layer**: Layer 1 ④ + 監査 #20 追加 (Entry Binary / Direction Multiclass の Layer 3 → Layer 1 昇格)

---

### Phase 2: ハイパラ最適化

**何を学習するか**: Phase 1 で採用した案 (a or b or c) のハイパラ (= LightGBM の調整パラメータ) を Optuna で最適化する。

**入力**: Phase 1 採用案のモデル + 学習データ
**処理**: Optuna で **数百 trial** 試して最良ハイパラを探す
**出力**: 最適化後のモデル

**学習方法**:
- **アルゴ**: Phase 1 採用案と同じ (LightGBM・objective = Phase 1 で確定)
- **探索手法**: Optuna TPE (Tree-structured Parzen Estimator・効率的なハイパラ探索)
- **trial 数**: 数百 trial (100 grid × 連続パラ・約 200-500 試行で収束)
- **学習データ**: Phase 1 と同じ (train 2021-2024 / valid 末尾 10%)
- **評価方法**: valid データでの目的関数値 (案 a = RMSE / 案 b = binary logloss / 案 c = multiclass logloss) を最小化
- **early_stopping**: 50 (改善が 50 回続かなければ停止)

**探索するハイパラ**:

| ハイパラ | 探索範囲 | 役割 |
|---|---|---|
| num_leaves | {7, 15, 31, 63, 127} | 木の葉数 (大きいほど複雑だが過学習リスク) |
| max_depth | {3, 5, 7, 10, -1} | 木の深さ (-1 = 無制限) |
| min_data_in_leaf | {50, 100, 200, 500} | 葉の最小サンプル数 (過学習防止) |
| learning_rate | 0.01〜0.1 (連続) | 学習率 |
| reg_alpha / reg_lambda | 0〜0.5 (連続) | L1/L2 正則化 |

**合格条件 (cc_ml_design_spec §1.6 の 4 指標)**:
- q99 net_quality 平均 > +10pp かつ 8 組合せ中 6+ で > 0
- net_quality 最小値 > -50pp
- valid_rmse / label_std (案 a) or logloss lift > 10% (案 b/c)
- mean_real_MFE / mean_real_MAE 比 > 1.0 が 8 組合せ中 6+

**失敗時**: 探索範囲狭い → 拡張 (1 回まで) / 全 FAIL → Phase 1 へ戻る

**所要時間**: 約 3-5 日

**該当軸** (補足): B-9 組み合わせ深さ
**Layer**: Layer 3 タスクを Layer 1 ④ 完了後に前倒し

---

### Phase 3-a: アルゴ比較 (LightGBM vs XGBoost vs CatBoost)

**何を学習するか**: LightGBM 以外のアルゴが優位かどうかを同条件で比較する。

**入力**: Phase 2 のハイパラ確定後のデータ
**処理**: XGBoost / CatBoost を同じ grid・同じ objective で再学習
**出力**: アルゴ別の予測精度比較表

**学習方法**:

| アルゴ | objective | ハイパラ | 評価方法 |
|---|---|---|---|
| LightGBM (主軸・Phase 2 のもの) | Phase 1 採用案と同じ | Phase 2 で確定 | valid logloss / RMSE |
| XGBoost | 同左 (xgb.XGBRegressor / xgb.XGBClassifier) | 同 grid (XGBoost 流に変換・max_depth / n_estimators / learning_rate 等) | 同左 |
| CatBoost | 同左 (catboost.CatBoostRegressor / CatBoostClassifier) | 同 grid (CatBoost 流に変換・depth / iterations / learning_rate 等) | 同左 |
| MiniROCKET | (Phase 5 不合格時のみ・Layer 3 投入) | デフォルト + ridge_classifier 後段 | 同左 |

**train データ**: Phase 1/2 と同じ (train 2021-2024 / valid 末尾 10%・**全アルゴ同条件**で比較)
**比較指標**: valid データでの目的関数値 + simulated PnL (Phase 1 と同じ簡易 Replay)

**合格条件**: LightGBM が最良 → Phase 3-b 進行 / XGBoost or CatBoost が優位 → 主軸変更協議

**失敗時**: 3 アルゴとも低性能 → Phase 1 へ戻る (採用案再選定 or Layer 3 投入)

**所要時間**: 約 2-3 日

**該当軸** (補足): B-10 学習アルゴ
**Layer**: Layer 3 第 1 弾を前倒し

---

### Phase 3-b: クラスタリング (T2 Entry の質分類)

**何を学習するか**: T1 の Entry 予測値を **性質別 3 グループ** (cluster) に分類する。

**入力**: Phase 1 採用案の予測値 + 既存ボラ系特徴量 + **LONG/SHORT 差分 4 個** = **20 次元入力**
**処理**: KMeans (k=3) で 3 グループに分類 + GMM / HDBSCAN とも比較
**出力**: 各 5 分足の cluster ID (0 / 1 / 2)

**学習方法**:

| 手法 | アルゴ | パラメータ | 学習方法 |
|---|---|---|---|
| KMeans (主軸・k=3 確定) | sklearn.cluster.KMeans | n_clusters=3 / random_state=42 / n_init=10 / max_iter=300 | fit() は train 期間のみ・test 期間は transform() のみ (再 fit 禁止・L-183 教訓) |
| GMM (比較) | sklearn.mixture.GaussianMixture | n_components=3 / covariance_type='full' / random_state=42 | 同左 |
| HDBSCAN (比較) | hdbscan.HDBSCAN | min_cluster_size=100 / min_samples=10 | 同左 (密度ベース・k 固定なし) |

**学習データ**: Phase 1 採用案の predictions_train_2021_2024.parquet (約 380k 行)
**評価方法**:
- cluster 間で実 MFE/MAE 比に明確差があるか (cluster A < cluster B < cluster C 等)
- train/test で cluster 分布が一致するか (cluster_movement_match > 50%)
- silhouette score (cluster 分離度の数値指標)

**前処理**: 入力 20 次元を pct ベースに標準化 (Phase 4-a normalize_reselect 既存対応の継承)

**artifact 名 verify 義務 (phase_compliance_checklist.md §Phase 4-a 整合)**:

| # | 項目 | 内容 |
|---|---|---|
| 4a.1 | **fit は train 2021-04〜2024-12 のみ** | test 2025 / 2026 Q1 で fit() 呼ばない |
| 4a.2 | scaler / km の **joblib 保存** (artifact 名に "train" 含む) | 例: `scaler_train_2021_2024.joblib` / `km_train_2021_2024.joblib` |
| 4a.3 | valid / test への apply は **transform / predict のみ** (再 fit 禁止) | コード review |
| 4a.4 | **artifact 名禁止: `*test*` 含むファイル名禁止** | `ls *.joblib \| grep -i test` がゼロ件 |
| 4a.5 | **K96 SHORT q99 フォールバック処理** | 以下のいずれかで cluster / 組合せを no-trade 除外: ① cluster 分離されない / ② 混在 cluster の実 MFE/MAE 比 < 1.0 / ③ test 発火が 0 件 |

**LONG/SHORT 差分 4 個 (cluster B 案・V4 の追加点)**:
- LONG_MFE_K12 - SHORT_MFE_K12
- LONG_MAE_K12 - SHORT_MAE_K12
- 同 K24
- 同 K48

→ 旧 V3 cluster は方向性を分類できていなかった (cluster 0 = 39% LONG / cluster 1 = 65% LONG・全部 LONG 寄り) ので、B 案で方向性差分を追加して改善

**期待される cluster の性質**:
- cluster A = 短時間で取れる Entry (高速 TP・小 SL)
- cluster B = 長く保有する Entry (大 TP・大 SL)
- cluster C = 高ボラ Entry (タイトな SL 必須)

**合格条件 (CP3)**:
- cluster 間で Entry 性質が分離 (= cluster 別の実 MFE/MAE 比に明確差)
- train/test で cluster 分布が乖離しない (一致率 > 50%)

**失敗時**: 分離弱 → 入力次元を 4 → 8 拡張 / 分布乖離 → rolling 365 日 cluster fit / k=3 性能低 → cluster なし設計協議

**所要時間**: 約 1-2 日

**該当軸** (補足): B-11 cluster (B 案最優先)
**Layer**: Layer 1

---

### Phase 4-b-1: Exit 設計 (T3・cluster 別最適 Exit)

**何を学習するか**: 各 cluster に対する **最適 Exit 方式** をデータから選ぶ。LightGBM の fit() は使わず、**組合せ最適化**で全試行する。

**入力**: 学習データ (2021-2024) + Phase 3-b の cluster ID
**処理**: 各 cluster × 各 Exit の組合せを **全試行 (数百通り)** → 各組合せで Replay → 最適 Exit を選定
**出力**: cluster 別の最適 Exit (TP_PCT / SL_PCT / TIME_EXIT / trailing 等の確定パラ)

**学習方法**: **ML 学習なし・組合せ最適化** (= Replay 大量試行 + 採用ルール適用)

**学習項目 (Exit カタログ 20+ 種・cluster 別最適選定)**:

##### A-2 標準 Exit 12 種

| # | Exit 種別 | パラメータ展開 | 想定 cluster |
|---|---|---|---|
| 1 | **固定 TP** | 予測 MFE × {50%, 80%, 100%} = 3 候補 | 短時間 cluster |
| 2 | **トレーリング (反転 X%)** | X = {0.1%, 0.2%, 0.3%} = 3 候補 | トレンド系 cluster |
| 3 | **時間 Exit (N bar 経過で強制決済)** | **N = {K//2, K} のみ** (K×2 禁止・phase_compliance §4b.3) | 全 cluster 共通 |
| 4 | **ATR 連動 SL** | ATR × {1.0, 1.5, 2.0} = 3 候補 | 高ボラ cluster |
| 5 | **MFE 比例 Exit (ピーク × X%)** | X = {50%, 70%} = 2 候補 | 短時間 cluster |
| 6 | **Stale 検知 (動きなし)** | 30 / 60 / 90 分 = 3 候補 | 横ばい cluster |
| 7 | **Triple Barrier (上下 + 時間)** | TP_pct = 予測 MFE × 80% / SL_pct = 予測 MAE / TIME = K bar | 検証用 |
| 8 | **cluster 別最適 Exit** | Phase 3-b cluster 結果使用 (動的選択) | 動的選択 |
| 9 | **パラボリック SAR** | 加速 0.02 / 最大 0.2 | トレンド系 |
| 10 | **Chandelier Exit (ATR ベース trailing)** | ATR × 3 | トレンド系 |
| 11 | **Mark/IFC 系** | ボリンジャー上下バンド | レンジ系 |
| 12 | **Composite (複数組合せ)** | 固定 TP + トレーリング併用等 | 複合 |

##### 手動 Priority Exit 8+ 種 (cc_role.md §1.7 スタートライン)

| # | Exit パラ | 意味 | 由来 |
|---|---|---|---|
| 13 | **TP_PCT** | 固定 TP 価格比率 | cat_v9 手動 Priority |
| 14 | **SL_PCT** | 固定 SL 価格比率 | 同上 |
| 15 | **TIME_EXIT** | 時間切れ決済 (分単位) | 同上 |
| 16 | **TIME_EXIT_DOWN** | 含み損時の時間切れ決済 | 同上 |
| 17 | **MFE_STALE** | MFE が停滞したら決済 | 同上 |
| 18 | **MFE_GATE** | MFE 閾値超えたら trailing 発動 | 同上 |
| 19 | **TRAIL_RATIO** | trailing の反転比率 | 同上 |
| 20 | **PROFIT_LOCK_PCT** | 含み益が一定 % 超えたら SL を建値以上にロック | 同上 |
| 21 | **STOCH_REVERSE** | Stochastic 反転で決済 | 同上 |
| 22 | **RSI_REVERSE** | RSI 反転で決済 | 同上 |
| 23 | **TP_BB_RATIO** | ボリンジャーバンド比率で TP 設定 | 同上 |
| 24 | **TP_FEE_FLOOR** | 手数料分の TP 上乗せ (BTC 価格動的計算) | 同上 |

**試行空間**: 3 cluster × 24 種 Exit × 各種パラメータ展開 = 数百通り
- **Replay 環境**: train データ 2021-2024 で全組合せ Replay (Entry は Phase 1 採用案の予測値・閾値は Phase 4-b-2 で確定する暫定値)
- **採用ルール (V4 改善・train のみ複合採用)**:
  - 旧 V3: train PnL idxmax 単独 (= train PnL が最大の Exit を選ぶ) → trailing 0 件採用問題発生
  - V4: **train PnL + train Sharpe の複合** で採用 (**train のみ・test PnL 不使用**)
    - train PnL: 利益額の絶対値
    - train Sharpe: PnL ÷ PnL 標準偏差 (リスク調整後リターン)
- **採用方式の重み**: train PnL 60% + train Sharpe 40% (暫定・調整可)
- **leak 防止**: Phase 4-a / 4-b の fit / 採用判断は **train のみ** (test 2025 / test 2026 Q1 は apply のみ・phase_compliance_checklist 4a.1 / 4b.1 / 4b.2 整合・false_positive §0-1 「test 期間の結果を見てから決めたパラメータ」禁止)

**Phase 4-b 約定モデル verify 義務 (phase_compliance_checklist.md §Phase 4-b 整合)**:

| # | 項目 | 内容 |
|---|---|---|
| 4b.3 | **time_exit グリッドを K まで制限 (K×2 禁止)** | `TIME_EXIT_GRID = (K//2, K)` のみ・K×2 (例: K=12 で 24 bar) 禁止 |
| 4b.4 | **TP 約定モデル (固定 TP)**: bar high >= tp_price + 0.01% buffer | `simulate_fixed_tp` で実装 |
| 4b.4-b | **TP 約定モデル (予測 MFE 中央値ベース)**: cluster ごとに pred_MFE 中央値 × X% を TP_PCT 候補に追加 | `simulate_predicted_mfe_tp` 新規実装 |
| 4b.5 | **Trailing**: bar 内 low 先・high 後 想定 (悲観的約定モデル) | `simulate_trailing` で実装 |
| 4b.6 | **entry_price = bar i+1 open ± 0.005%** | bar 内 close ではなく 次 bar open + slippage |
| 4b.7 | **slippage 0.005% 全約定加算** | entry + exit 両方に加算 |

**月別 Exit 約定率必達ライン** (phase_compliance_checklist.md §Phase 4-b):
- 2025-12 が年最弱月 (楽観 PnL $16,933・8.9 倍)
- Phase 6-b $1,900 死守には Exit 約定率 ≥ **12%** が必達
- TP 約定 + トレーリング + 時間 Exit の合計で 12% を確保すること
- 12% 未達なら Phase 4-b cluster_best_exit 再選定 or Exit type 拡張要

**Exit カタログ (12 種以上 + 手動 Priority 8+ 種)**:

| # | Exit 種別 | パラメータ例 |
|---|---|---|
| 1 | 固定 TP | 予測 MFE × {50%, 80%, 100%} |
| 2 | トレーリング (反転 X%) | X = {0.1%, 0.2%, 0.3%} |
| 3 | 時間 Exit (N bar 経過) | N = {K//2, K} のみ (K×2 禁止) |
| 4 | ATR 連動 SL | ATR × {1.0, 1.5, 2.0} |
| 5 | MFE 比例 (ピーク × X%) | X = {50%, 70%} |
| 6 | Stale 検知 (動きなし) | 30/60/90 分 |
| 7 | Triple Barrier | TP/SL/TIME 同時 |
| 8 | cluster 別最適 Exit | Phase 3-b 結果 |
| 9 | パラボリック SAR | 加速 0.02/0.2 |
| 10 | Chandelier Exit | ATR × 3 |
| 11 | Mark/IFC 系 | ボリンジャー上下 |
| 12 | Composite | 複数組合せ |
| 13-20 | 手動 Priority (TP_PCT / SL_PCT / TIME_EXIT / TIME_EXIT_DOWN / MFE_STALE / MFE_GATE / TRAIL_RATIO / PROFIT_LOCK_PCT / STOCH_REVERSE / RSI_REVERSE / TP_BB_RATIO / TP_FEE_FLOOR) | 手動 cat_v9 パラ |

**採用方式 (V4 改善ポイント)**:
- 旧 V3 は「train PnL idxmax 単独」採用 → trailing exit が 0 件採用される問題発生
- V4 では **train PnL + train Sharpe + test 期間一部 verify の複合採用** に変更

**合格条件**:
- cluster 別最良 Exit が次点と差 ≥ 10%
- 採用 Exit 多様性 ≥ 3 種 (前回 0 件採用問題回避)

**失敗時**: 最良 Exit と次点僅差 → Phase 3-b へ / 全 cluster で低性能 → Phase 1 へ / Exit 採用 1-2 種集中 → Exit カタログ拡張

**所要時間**: 約 3-5 日

**該当軸** (補足): A-2 Exit 指標 + A-3 Exit 側
**Layer**: Layer 1 ① 最優先 (trailing 不採用問題究明 + 採用方式複合化)

---

### Phase 4-b-2: Entry 閾値 (= どの予測値強度で Entry するか)

**何を学習するか**: Entry を発火させる閾値を **3 方式並列** で試して最良を選ぶ。

**入力**: Phase 1 採用案の予測値 + Phase 3-b の cluster ID
**処理**: 3 方式で閾値を計算 → 各方式で Replay → 最良方式を選定
**出力**: 最終 Entry 閾値

**学習方法**: **ML 学習なし・閾値計算 + Replay 比較**

| 方式 | 閾値計算方法 | 学習データ |
|---|---|---|
| rolling 365 日 q90/q95/q99 | 直近 365 日の予測値分布から `numpy.quantile(preds, q=0.99)` で動的に閾値設定 | train + 直近 365 日 rolling |
| cluster 別独立 quantile | cluster 0/1/2 ごとに独立 `numpy.quantile()` | train cluster 別 |
| Triple Barrier (Layer 3 投入時のみ) | TP/SL/TIME 比率を 2 段階 Meta-labeling で確定 | (Phase 1 で 3 案とも未達のとき適用) |

**評価方法**: 3 方式で仮 test 2025 を Replay → 月次 net_quality 中央値 + 発火頻度 で比較

**3 方式**:

| 方式 | 内容 |
|---|---|
| rolling 365 日 q90/q95/q99 | 直近 365 日の予測値分布から quantile で閾値設定 |
| cluster 別独立 quantile | cluster ごとに独立 quantile |
| Triple Barrier | (Layer 3 投入時のみ・Phase 1 で 3 案とも未達のとき) |

**並行: 欠落 combo 究明**:
- K=24 LONG/SHORT q99 欠落原因の verify + 救出判定 (Layer 1 ①)
- K=96 LONG q95-q99 切り捨て判定 (Layer 1 ②・no_trade 86.2% 主因解消)

**合格条件**:
- 仮 test 2025 で発火頻度 ≥ 10 件/日
- net_quality > 0

**失敗時**: 3 方式とも net_quality ≤ 0 → Phase 3-b へ / 発火頻度 < 10 件/日 → quantile 緩和 (q99 → q95)

**所要時間**: 約 2-3 日

**該当軸** (補足): B-13 Entry ratio 閾値 + D-α 発火頻度
**Layer**: Layer 1 ① + Layer 1 ②

---

### ★ Phase 4-b 完了ゲート: Entry-Exit 整合性 review (CP4)

**何をするか**: **学習はしない**。Phase 5 着手前に「Entry 予測と Exit 設計が整合しているか」を独立 verify する。

**学習方法**: **該当なし** (verify のみ・Claude `/audit` 経由)

**なぜ必要か**: 前回 Phase 5 v3 で -$985 になった核心が「Entry-Exit 不整合」だった。再発検知のためゲートを設置。

**verify 内容 (5 項目)**:

1. cluster 別 Exit 性能が次点と差 ≥ 10% ある
2. 採用 Exit の多様性 ≥ 3 種
3. cluster 方向性 (LONG/SHORT) と Exit 整合 (例: LONG cluster で trailing-up 採用)
4. Entry 予測値パターンと Exit パラメータの相関 (高予測 MFE cluster で TP 高め設定等)
5. **Claude `/audit`** 独立 review (同型バイアス警告下で外部基準評価)

**NG 時の戻り先**:
- Exit 1-2 種集中 → Phase 4-b-1 へ
- LONG cluster で trailing-down 採用等 → Phase 3-b へ
- Entry 予測値と Exit 不相関 → Phase 1 へ

**所要時間**: 約 1 日

---

### Phase 5: ポジション設計 (T4・本丸第 1 段・サブ 7 つ)

**何を学習するか**: ポジションサイズ・cap・配分・Funding・削除類型を **組合せ最適化** で確定する。仮 test 2025 で月次 NET ≥ $1,900 全 12 ヶ月クリアが本丸の合格判定。

**入力**: Phase 4-b 確定モデル + パラメータ
**処理**: サブ 5-a〜5-g を順次実施・最終的に数千通りを Replay → 月次 NET 中央値最大の組合せを 1 つ選択
**出力**: 確定パラメータ (Phase 6 で適用するだけ)

**学習方法**: **ML 学習なし・組合せ最適化 (Replay 大量試行)**

- **試行空間**: MAX_ADDS 6 種 × per-position サイズ 8 方式 × cap 3 方式 × LONG/SHORT 比率 (3-5 通り) × add トリガ (3-5 通り) = **数千通り**
- **Replay 環境**: train 2021-2024 で全組合せ Replay (Entry = Phase 4-b-2 確定閾値・Exit = Phase 4-b-1 確定 Exit)
- **採用ルール**: 月次 NET 中央値 (= 12 ヶ月分の月次 NET の中央値) が最大の組合せを 1 つ選択
- **leak 防止**: train でのみ組合せ選定・test 2025 は holdout (Phase 6 でも使わず Phase 5 評価のみ)
- **時系列処理**: 採用ループは時系列順 (entry_ts 昇順・L-182 教訓・過去の判断を後から覆さない)・同 timestamp 内のみ pred_ratio で優先順位付け

**Phase 5 verify 義務 (phase_compliance_checklist.md §Phase 5 + false_positive §5 関所 整合)**:

| # | 項目 | 内容 |
|---|---|---|
| 5.1 | **採用ループ時系列順** (entry_ts 昇順・L-182) | 過去の判断を後から覆さない |
| 5.4 | **Maker fee = 0.00014 (適用確定) / 0.0002 (剥落復帰時)** | **両値で stress test 実施**・剥落時月次 NET ≥ $1,900 全月クリアを verify |
| 5.5 | **wick 乖離 vs TP_PCT レンジ重ね合わせ分析** | p95 ≤ 0.05% 確認 (約定モデル妥当性) |
| **§5 関所 A 異常値自動 STOP** | 完了報告で以下いずれか該当 → **「合格」と書かず「異常値・要調査」** | ① 勝率 > 70% / ② 月次 NET > $3,800 (合格ライン 2 倍) / ③ IS-OOS Sharpe 比 > 3 倍乖離 / ④ 最大 DD < 月次 NET の 10% |
| **§5 関所 B 全工程未来参照 verify** | PnL 計算式の入力変数を列挙 + 各変数の因果性宣言 | 変数名 grep だけでは名前変更で素通り (例: `mfe_te[i]` が test_MFE_K12 参照していないか) |
| **§5 関所 C NET 実体 verify** | `net_pnl` 列が **本当にコスト控除後か実装で verify** | 列名を信用せず・手数料 0.00014 / Funding median +0.0002 / slippage 0.005% が控除されているか確認 |
| **§5 関所 E 報告先行** | インシデント疑い発生時は **調べる前にまず報告** | CC が「自分で解決してから報告」しようとする動きを禁止 |

**学習項目 (サブ 5-a〜5-g 各軸の詳細パラメータ)**:

##### 5-a: A-6 MAX_ADDS / add トリガ条件

**MAX_ADDS 6 通り**:

| MAX_ADDS | 意味 | 想定戦略 |
|---|---|---|
| **1** | スキャル系 (1 entry のみ・add なし) | 短時間 cluster |
| **2** | 軽い add | 短〜中時間 cluster |
| **3** | 中程度 add | 中時間 cluster |
| **5** | 平均建値型 (cat_v9 手動 Priority 同等) | 長時間 cluster (cc_role §1.7 スタートライン) |
| **8** | 大量 add | 高ボラ反発系 |
| **10** | 最大 add | 極端反発系 (上限・cap=150 制約内) |

**add トリガ条件 (V4 制約セット遵守)**:

| 条件 | 内容 | 由来 |
|---|---|---|
| 前回 add 約定確認 | 前 add が約定確認できてから次 add | core_rules.md TTL 3 本制約 |
| 時間経過 ≥ 15 分 | exchange_spec.md Maker 指値 TTL 3 本 (5m × 3 = 15 分) | exchange_spec.md |
| 価格逆行幅 X% | 価格が逆行 (LONG なら下落) で X% を超えたら add | A-6.9 |
| 含み益 / 含み損閾値 | 含み損 -X% で add (反発期待) or 含み益 +X% で add (トレンド乗り) | A-6.9 探索 |

##### 5-b: A-7 per-position サイジング 8 方式

| # | 方式 | 計算式 | 想定 cluster |
|---|---|---|---|
| **1** | **固定** | **0.12 / (cap_N × MAX_ADDS) BTC** (例: cap=6 / MAX_ADDS=5 で 0.004 BTC = 1 トレード合計 0.02 BTC × 6 = 0.12 BTC ✅) | 全 cluster 共通 |
| **2** | **予測強度比例** | Entry 確率 × 基準サイズ (案 b/c のとき) | 全 cluster |
| **3** | **cluster 別** | cluster A=0.04 / cluster B=0.02 / cluster C=0.01 BTC 等 | cluster 別最適 |
| **4** | **volatility 連動 (逆比例)** | 基準サイズ × (median ATR / 現 ATR) | 高ボラ時 cluster |
| **5** | **Kelly 基準** | 期待リターン × 勝率 / リスク (Kelly criterion) | 高確信 entry |
| **6** | **half-Kelly (安全側)** | Kelly の半分 | 中確信 entry |
| **7** | **リスク等価** | 想定損失額 (SL_pct × size) が一定 | 全 cluster (SL 設定済) |
| **8** | **動的 (複合)** | cluster × volatility × 予測強度の重み付き合成 | 統合配分 |

**絶対制約 (実装義務・false_positive §0-2 第二絶対規定)**:
- per-position ≥ 0.0001 BTC (Bitget minTradeNum)
- per-position × BTC 価格 ≥ 5 USDT (Bitget minTradeUSDT・BTC=$30k stress test)
- per-position ≥ 0.000167 BTC (BTC=$30k で 5 USDT 充足)
- **per-position × MAX_ADDS × cap_N ≤ 0.12 BTC** (合計上限・前回見落とし指摘訂正済)
- **sum(active_position_btc) ≤ 0.12 BTC** (任意の時点 t で verify・違反検知 → 即実装停止)
- cap × 0.12/N BTC × price ≤ 必要証拠金 (leverage 確認・exchange_spec.md max 150x)

##### 5-c: B-8 cap 3 方式

| 方式 | 内容 | メリット |
|---|---|---|
| **静的 cap** | 全期間で固定値 (例: cap=12 = 同時保有 12 まで) | 実装シンプル |
| **combo 別 cap** | combo (cluster × K × side) ごとに独立 cap (例: K12 LONG = 5・K96 SHORT = 2) | combo 別最適 |
| **動的 cap** | 期間ごとに quantile で変動 (rolling 30 日・直近の発火頻度に応じて調整) | レジーム適応 |

**cap カウント方法**: **合算カウント** (false_positive §0-2 確定・LONG + SHORT を合計 0.12 BTC で 1 つの枠として管理)

**Phase 5-d 必須義務 (phase_compliance_checklist.md §Phase 5-d 整合)**:
- 5d.4 **fee/funding 込みで cap 別 best Exit 再選定** (= Phase 4-b-1 の Exit を 1/cap 線形使い回さない・cap が変わると最適 Exit も変わる)

##### 5-d: D-ζ マルチサイド (hedge_mode)

- hedge_mode 許可 (LONG/SHORT 同時保有可)
- 合計 0.12 BTC 内で LONG/SHORT 動的配分 (ML 学習対象)
- 例: LONG 0.08 BTC + SHORT 0.04 BTC = 合計 0.12 BTC OK

##### 5-e: D-η Funding

| 項目 | 値 |
|---|---|
| **合格判定 baseline** | median +0.0002%/8h (audit#19 確定・history-fund-rate API 91 intervals 2026-04〜05) |
| **stress test 参考** | p95 0.01%/8h |
| 精算時刻 (UTC) | 00:00 / 08:00 / 16:00 |
| 精算時刻 (JST) | 09:00 / 17:00 / 翌 01:00 |
| LONG/SHORT 適用 | LONG = -funding / SHORT = +funding (median 正値 → LONG 払い) |

##### 5-f: 削除類型 10 種 (v3 から継承)

**注記**: 削除類型 10 種の具体内容は learning_design_v3 (archive・174 行) §「削除類型 (Phase 5 必須・10 種)」に記録。本書では「v3 そのまま継承・変更なし」と明示 (learning_design_v4 §10 修正履歴 #15 整合)。

該当 combo (cluster × K × side) を Phase 5 で全削除する 10 類型 (例: K96 SHORT q99 偽陽性集中 / K24 q99 欠落 / 月次 NET 大幅マイナス combo 等)。詳細は archive 参照。

##### 5-g: D-α 発火頻度

| 制約 | 内容 |
|---|---|
| **per-day ≥ 10 件制約** | 1 日 10 件未満の signal はノイズ扱いで除外 (L-117 教訓・件数少ないとフィルタ効果が消える) |
| **発火頻度実態可視化** | combo (cluster × K × side) ごとに発火頻度を全 12 ヶ月で可視化 |

**サブフェーズ 7 つ**:

| サブ | 内容 |
|---|---|
| **5-a** | MAX_ADDS = {1, 2, 3, 5, 8, 10} の 6 通り × add トリガ条件 (前回 add 約定 + 時間経過 ≥ 15 分必須) 並列試行 |
| **5-b** | per-position サイズ **8 方式並列** (固定 / 予測強度比例 / cluster 別 / volatility 連動 等) + per-position ≥ 0.000167 BTC (BTC=$30k stress test 通過) |
| **5-c** | cap **3 方式並列** (静的 / combo 別 / 動的・**合算カウント** で合計 0.12 BTC 厳守) |
| **5-d** | hedge_mode で LONG/SHORT 動的配分 (合計 0.12 BTC 内・ML 学習対象) |
| **5-e** | Funding 適用 (median +0.0002%/8h を合格判定 baseline + p95 0.01%/8h を stress test として参考) |
| **5-f** | 削除類型 10 種に該当する combo を全削除 |
| **5-g** | per-day ≥ 10 件制約適用 (件数少ない signal はノイズ・L-117 教訓) |

**組合せ空間**: MAX_ADDS 6 × 配分 8 × cap 3 × LONG/SHORT 比率 × add トリガ = **数千通り**

**絶対制約 (false_positive §0-2 第二絶対規定)**:
全エントリー時点で `sum(active_position_btc) ≤ 0.12` を実装で verify。違反検知 → 即実装停止。

**合格条件 (本丸第 1 段)**:
仮 test 2025 で月次 NET ≥ $1,900 **全 12 ヶ月クリア** (実行前確定・実行後緩和禁止)

**失敗時**:
- 1-3 ヶ月未達 → 削除類型強化 (1 回まで) → Layer 2 投入 (D-δ 時間帯 / D-ε regime / Exit 第 2 弾 / Calibration)
- 4+ ヶ月未達 → Phase 4-b へ戻る
- 大幅未達 → Phase 1 まで戻る or Layer 3 投入

**所要時間**: 約 1-2 週間

**該当軸** (補足): A-6 / A-7 / B-8 / D-ζ / D-α + 削除類型 10 種
**Layer**: Layer 2 ② / ③ + Layer 2 統合フェーズ

---

### Phase 6: 本テスト (本丸第 2 段・1 回限り・チューニング禁止)

**何を学習するか**: **学習はしない**。Phase 5 で確定した全パラメータをそのまま 2026 Q1 (25,631 行) に **1 回だけ** 適用して、汎化性能を最終確認。

**学習方法**: **該当なし** (適用のみ・新規学習禁止・scaler/km の再 fit 禁止・L-183 教訓)

**Phase 6-b verify 義務 (phase_compliance_checklist.md §Phase 6-b 整合)**:

| # | 項目 | 内容 |
|---|---|---|
| 6b.1 | scaler/km の **再 fit 禁止** (Phase 4-a artifact をロード) | L-183 教訓 |
| 6b.2 | 月次 NET ≥ $1,900 **全 3 月クリア** | 1 ヶ月でも未達 → 不合格 |
| 6b.3 | Phase 4-b best Exit (train fit) を **apply のみ** | コード review |
| 6b.4 | **artifact ファイル名が `*train_2021_2024*` パターン起動時 assertion** | `assert "train" in artifact_path and "test" not in artifact_path` |

**絶対禁止**:
- チューニング (結果を見てからパラメータ変更すると Phase 6 やり直し = 仮テスト期間追加が必要)
- CP5 前監査で「削除類型 10 種 + per-day 制約 + サイジング 8 方式」の妥当性を独立検証してから着手

**合格条件**:
月次 NET ≥ $1,900 **全 3 ヶ月クリア** (2026-01 / 02 / 03)・1 ヶ月でも未達なら不合格

**失敗時**:
- 1 ヶ月だけ僅差未達 ($1,800 等) → 仮 test 期間追加 (2026 Q2 待ち)
- 2+ ヶ月未達 → Phase 4-b へ戻る → Layer 2 投入
- 全月大幅未達 → Layer 3 投入 (Triple Barrier + Meta-labeling 等)

**所要時間**: 半日

---

### Phase 7-a〜e: Bot 統合 → デモ → 本番

**何を学習するか**: 学習はしない。実装と検証のみ (a〜e で段階実施)。

**学習方法**: **該当なし (a〜e は実装・検証フェーズ)**。ただし「本番運用後」に **B-10 第 4 弾 X2 強化学習** を本格検討対象として明示 (env 設計含めて 1-3 ヶ月)。

| サブ | 内容 |
|---|---|
| **7-a** | 推論再現性検証 (offline 推論 = online 推論を bit-exact で verify) |
| **7-b** | ML Decider 実装 (strategies/cat_ml_decider.py) |
| **7-c** | run_once_ml.py 統合 (**ALLOW_LIVE_ORDERS = False 維持** / paper_trading フラグ伝搬・min order 0.0001 BTC assertion・hedge_mode・rate limit 10 req/s 制御・TP/SL ペア整合・**起動時に artifact 名 log 出力 → "test" 文字列含むなら `sys.exit("ABORT: test-named artifact detected")`** / offline 推論 = online 推論 (verify_ml_inference.py)) |
| **7-d** | paper trading (デモ) 検証 + maxMarketOrderQty 単位 confirm (220 BTC vs lots 確定) |
| **7-e** | 本番投入 (まこさん最終決裁) |

**本番運用後**: B-10 第 4 弾 X2 強化学習を本格検討 (env 設計含めて 1-3 ヶ月)

---

## §3 失敗時の改善フロー (どの Phase 不合格でどこに戻るか)

```
                    [Phase 1 立て直し]
                            ↑
                            │ (採用案再選定 or Layer 3 投入)
                            │
            ┌───────────────┼───────────────┐
            │               │               │
        [Phase 1]    [Phase 0 改修]      [k=2 切替]
                       (特徴量見直し)    (cc_ml_design_spec §6)
            ↑               ↑               ↑
   Phase 2/3-a/4-b/5/6  1 全敗 / leak    6 大幅未達
            │
   (Entry 学習根本問題)
            │
            └──→ [Layer 2 投入] (Calibration / D-δ / D-ε / Exit 第 2 弾)
                    ↑
                    │ Phase 5 / 6 で月次 NET 僅差未達

[Phase 3-b 戻る] ← Phase 4-b-1 cluster 不整合
[Phase 4-b 戻る] ← Phase 5 / 6 不合格 (Exit 再設計)
[Layer 3 投入] ← Phase 1 で 3 案とも未達 / Phase 6 全月大幅未達
```

### Layer 1 / 2 / 3 の役割

| Layer | 役割 | 投入条件 |
|---|---|---|
| **Layer 1** | まず動かす最低限 (Phase 0 改修 + Phase 1 並列 3 案 + cluster B 案 + Exit 採用見直し) | デフォルト着手 |
| **Layer 2** | 目標未達時の追加最適化 (A-6 / A-7 / B-8 / D-δ / D-ε / Exit 第 2 弾 / Calibration) | Phase 5 / 6 で月次 NET 僅差未達 |
| **Layer 3** | 構造変更を伴う再設計 (Triple Barrier + Meta-labeling 2 段階 / Walk-forward / Class balancing / custom loss / MiniROCKET / X2 強化学習) | CP2 で 3 案とも未達 or Layer 2 でも未達 |

### Layer 3 投入の意味 (Entry 学習で 3 案とも合格未達のとき)

Phase 1 で案 a/b/c 全て不合格なら、Entry 学習を 2 段階構成に変更する:

```
1 段階目: Triple Barrier multiclass で「TP / SL / TIME のどれが先に起きるか」を 3 クラス分類
   ↓
2 段階目 (Meta-labeling): 1 段階目の予測結果に対して「Entry を採用するか / 見送るか」を判定
```

これは Lopez de Prado AFML Ch.3 で推奨される手法 (primary model lift < 10% のとき投入推奨)。

---

## §4 全体フロー俯瞰 (1 ページ)

```
[前提タスク] cc_ml_design_spec §4 改訂 ✅ 2026-05-21 完了
   ↓
[Phase 0 改修] build_labels_pct.py 改修 (1432 → 約 2000-2500 列)
   ↓ 約 3-6 時間
   ↓ CP1 監査 (列数 + leak 4 点)
   ↓
[Phase 1] 並列学習 6 案 (案 a + 案 b + 案 c + 案 d + 案 e + 案 f・v5)
          + Walk-forward Purged K-Fold 5 fold + DSR 補正
   ↓ 約 3-4 週間 (5 fold × 6 案 = 約 20 時間学習 + CP2 監査 + 分析)
   ↓ CP2 監査 (5 指標で 6 案比較 → 分岐)
   ↓
   ┌─────分岐─────┐
   │              │
   6 案いずれか      6 案ベストでも
   5 指標 ALL PASS   5 指標未達
   ↓              ↓
   採用案で進行       即 Layer 3 残存タスク投入
                  (CPCV + Class balancing
                  + custom loss + アルゴ多様化)
   ↓              ↓
   └──────合流──────┘
   ↓
[Phase 2] ハイパラ最適化 (Optuna)
   ↓ 3-5 日
   ↓
[Phase 3-a] アルゴ比較 (LightGBM vs XGBoost vs CatBoost)
[Phase 3-b] クラスタリング (k=3・20 次元入力)
   ↓ CP3 監査
   ↓
[Phase 4-b-1] Exit 設計 (12+ 種 × cluster 別最適化)
[Phase 4-b-2] Entry 閾値 (3 方式並列)
   ↓
[★ CP4 ゲート] Entry-Exit 整合性 review
   ↓
[Phase 5] ポジション設計 (5-a〜5-g)
   ↓ 1-2 週間
   ↓ 仮 test 2025 月次 NET ≥ $1,900 全 12 ヶ月
   ↓ CP5 監査
   ↓
[Phase 6] 本テスト 2026 Q1 (1 回限り)
   ↓ 月次 NET ≥ $1,900 全 3 ヶ月
   ↓
[Phase 7-a〜e] Bot 統合 → デモ → 本番投入
```

---

## §5 補足 (23 軸 × T1-T5 × Layer の対応)

### §5.1 T1-T5 学習タスク

| タスク | 何を予測 | 該当 Phase |
|---|---|---|
| **T1 Entry タイミング予測** | 「Entry すべきか・どっち側か・どの強さか」 | Phase 1 / Phase 2 / Phase 3-a |
| **T2 Entry の質分類** | T1 出力を性質別 cluster 化 | Phase 3-b |
| **T3 Exit タイミング予測** | cluster 別に最適 Exit を決める | Phase 4-b-1 |
| **T4 ポジション配分** | 合計 0.12 BTC 内で combo・cluster 別配分 | Phase 5 |
| **T5 発火フィルタ** | Entry 出ても見送る条件 | Phase 5 統合フェーズ (Layer 2) |

### §5.2 23 軸 × Phase 対応 (主に学習する軸のみ)

| 軸 | 内容 | 主に登場する Phase |
|---|---|---|
| **A-1** Entry 指標 | 1432 → 約 2000-2500 列 | Phase 0 改修 |
| **A-2** Exit 指標 | 12+ 種 + 手動 Priority 8+ 種 | Phase 4-b-1 |
| **A-3** 閾値・パラメータ | パラメータ並列 + 閾値 LightGBM 自動 | Phase 0 改修 / Phase 4-b-1 |
| **A-4** 時間軸 K | K = {6, 12, 24, 48, 96, 144, 288} | Phase 0 改修 |
| **A-5** 時間足 bar | 6 TF + 1w/1M = 8 TF | Phase 0 改修 |
| **A-6** MAX_ADDS / 配分 | MAX_ADDS 6 通り | Phase 5-a |
| **A-7** サイジング | per-position 8 方式 + 合計 0.12 BTC 上限 | Phase 5-b |
| **B-8** cap | 3 方式並列・合算カウント | Phase 5-c |
| **B-9** 組合せ深さ | num_leaves / max_depth 等 | Phase 2 |
| **B-10** 学習アルゴ | LightGBM 主軸 + XGBoost / CatBoost / MiniROCKET | Phase 3-a |
| **B-11** cluster | k=3 + B 案 (LONG/SHORT 差分追加) | Phase 3-b |
| **B-12** 特徴量変換 | Fractional / PCA / MTF 4 方式 | Phase 0 改修 |
| **B-13** Entry ratio 閾値 | rolling + cluster 別 quantile | Phase 4-b-2 |
| **B-14** 学習データ範囲 | train 2021-2024 / 仮 test 2025 / 本 test 2026 Q1 (固定) | 全 Phase 制約 |
| **B-15** 目的関数 | **3 案並列 (RMSE / Binary / Multiclass)** + custom loss (Layer 3) | **Phase 1 (Entry 改善の核心)** |
| **D-α** 発火頻度 | per-day ≥ 10 件制約 | Phase 4-b-2 / Phase 5-g |
| **D-γ** Entry 位置 | A-3 統合 (location_prev / risk_score) | A-3 内 |
| **D-δ** 時間帯曜日 | 統合フェーズで時間帯フィルタ | Phase 5 統合 (Layer 2) |
| **D-ε** regime | 凍結解除判定 | Layer 2 以降 |
| **D-ζ** マルチサイド | hedge_mode・合計 0.12 BTC 内動的配分 | Phase 5-d |
| **D-η** 手数料 | Maker 0.014% (適用) + Funding median | D 固定 |
| **D-θ** 発注タイプ | Maker 指値前提 + 不約定モデル化 | D 固定 + Phase 7 |

### §5.3 Entry 学習問題 5 件への対応マップ (v5 Layer 配分逆転反映・2026-05-22)

Phase 1-a/1-b/1-c smoke で観察された 5 件の問題 → V4 v5 でどう対応するか:

| 問題 | V4 v5 第一弾 (Layer 1) | 残存 Layer 3 |
|---|---|---|
| top1 atr14 が 33-65% 支配 | Phase 0 で特徴量拡張 + Phase 3-b cluster B 案 (LONG/SHORT 差分) + **案 c Direction Multiclass** | アルゴ多様化 (XGBoost/CatBoost/MiniROCKET) / Asymmetric loss |
| SL hit が TP の 1.78 倍 | Phase 4-b-1 Exit 採用方式見直し + Phase 4-b-2 K96 切り捨て + **案 e Triple Barrier multiclass + 案 f Meta-Labeling** | (Layer 1 で前倒し済) |
| entropy lift 6.04% (閾値 10% 未満) | **Phase 1 で案 b Entry Binary + 案 c Direction Multiclass + 案 d Ranking LambdaRank + 案 e Triple Barrier + 案 f Meta-Labeling 並列実装** (Layer 3 → Layer 1 前倒し) | custom loss / SHAP / Conformal prediction (前半) + 高信頼度 only Entry (後半) |
| class imbalance (98% 負例) | 案 b で scale_pos_weight + **案 e/f で Triple Barrier 3 クラス分類により実質緩和** | Class balancing / Focal loss / regime-based stratified サンプリング |
| 末尾 10% valid のみ | **Walk-forward Purged K-Fold 5 fold (mlfinpy.cross_validation.PurgedKFold) を全 6 案で必須** (Layer 3 → Layer 1 前倒し) | CPCV (Combinatorial Purged CV) |

### §5.4 CP1〜CP5 (Claude 監査モード `/audit` 連携)

| CP | 着手前 | 監査内容 |
|---|---|---|
| **CP1** | Phase 1 着手前 | Phase 0 改修出力 (列数 + leak 4 点) |
| **CP2** | Phase 2 着手前 | Phase 1 並列 **6 案** × Purged K-Fold 5 fold 物理証跡対比 + **5 指標** (entropy lift / TP Precision / Direction Accuracy / Simulated PnL / DSR) 判定・Layer 3 投入条件厳格化 (v5) |
| **CP3** | Phase 3-b 着手前 | KMeans vs GMM vs HDBSCAN の本プロジェクト適合性 |
| **CP4** | Phase 5 着手前 | Entry-Exit 整合性 review (前回 -$985 同型再発検知) |
| **CP5** | Phase 6 着手前 | 削除類型 10 種 + per-day 制約 + サイジング 8 方式の妥当性 |

**同型バイアス警告**: CC と監査エージェントは同じ Claude 訓練ベース → 同型バイアス共有可能性あり (cc_role.md §1.4 #3)。それでも CC + まこさんの 2 者で確定するより独立性が増すため、重大判断は監査経路を通す。

---

## §6 改訂履歴

| Date | Ver | 内容 |
|---|---|---|
| 2026-05-21 | v3 v1 | 初版 (Web Claude 起案・V3 設計図ベース・archive 移動) |
| 2026-05-21 | v4 試作 #1 (破棄) | V4.1 反映 622 行・難解 |
| 2026-05-21 | v4 試作 #2 (破棄) | 簡略 358 行・学習内容薄い |
| 2026-05-21 | v4 試作 #3 (破棄) | 詳細化版・23 軸全反映なし |
| 2026-05-21 | v4 試作 #4 (破棄) | 23 軸完全反映 866 行・§3 以降ごちゃごちゃ |
| 2026-05-21 | v4 試作 #5 (破棄) | フロー主役 604 行・学習方法明示なし |
| 2026-05-21 | v4 試作 #6 (破棄) | フロー主役 + 学習方法 682 行・各 Phase の学習項目 (指標カタログ等) なし |
| 2026-05-21 | v4 試作 #7 (本版・前バージョン 888 行) | §2 各 Phase に学習方法 + 学習項目セクション追加・145 ファミリー詳述 / Exit 24 種 / MAX_ADDS 6 / per-position 8 方式 / cap 3 方式 / Funding / 削除類型 / 発火頻度 |
| 2026-05-21 | **v4 v1 (確定版・約 960 行)** | **phase_compliance_checklist.md (222 行) + false_positive_incident_policy.md (225 行) 全文 view → 整合性総点検 → A 案修正反映**: ① Phase -1 USD 絶対値 blacklist 48 列 drop 義務明示 / ② Phase 1 verify (random_state=42 + feature_importance top20 即時 review + fractal blacklist 3 段階) / ③ Phase 3-b artifact 名 verify ("train" 含む / `*test*` 禁止) + K96 SHORT q99 フォールバック / ④ Phase 4-b-1 採用方式修正 (test 期間使用削除・train のみ) + time_exit K 制限 + TP 約定モデル (固定 + pred_MFE 中央値) + Trailing 順序 + entry/slippage 0.005% + 月別 Exit 約定率 ≥ 12% / ⑤ Phase 5 false_positive §5 関所 A/B/C/E 統合 + Maker 剥落 stress (0.02%) + wick 乖離分析 / ⑥ Phase 5-b 計算式 MAX_ADDS 反映 `per-position = 0.12 / (cap × MAX_ADDS)` / Phase 5-d cap 別 best Exit 再選定 / ⑦ Phase 6-b artifact assertion ("train" 含み "test" 含まず) / ⑧ Phase 7-c ALLOW_LIVE_ORDERS = False 維持 + "test" artifact 起動中止 + verify_ml_inference.py |
| 2026-05-26 | **v5 整合更新 (本プロジェクトの正本一本化反映)** | learning_design_v4 §10 #19/#20 + handoff v22 で 2026-05-22 確定済の **v5 Layer 配分逆転** を本書に反映: ① §2 Phase 1 を 3 案並列 → **6 案並列** (案 a/b/c + 案 d Ranking LambdaRank + 案 e Triple Barrier multiclass + 案 f Meta-Labeling 2 段階) に拡張・Walk-forward Purged K-Fold 5 fold + DSR 必須化 / ② 学習後比較指標 4 → **5 指標** (entropy lift > 10% / TP Precision > 0.5 / Direction Accuracy > 0.55 / Simulated PnL / DSR > 1.0) + Layer 3 投入条件厳格化 / ③ §4 全体フロー俯瞰 (案 a+b+c → 6 案) / ④ §5.3 Entry 学習問題対応マップ (Layer 3 → Layer 1 前倒し済) / ⑤ §5.4 CP2 監査内容 (5 指標 + Purged K-Fold) / **handoff_to_cc_v* 廃止と並行で本書を正本に一本化** (learning_design_v4 は archive 移動) |

---

## §7 関連ファイル

本ファイルは **本プロジェクトの学習フロー正本** (2026-05-26 一本化・handoff_to_cc_v* 廃止と並行)。詳細な設計仕様 / 役割 / 関所は以下を参照:

- **cc_ml_design_spec.md**: ML pipeline 仕様・合否基準
- **cc_role.md**: CC 役割定義・23 軸 First Principles
- **false_positive_incident_policy.md**: leak 防止・ポジション上限厳守 / 関所 A-G
- **phase_compliance_checklist.md**: Phase 別 verify 義務
- **WORKFLOW.md**: 現フェーズ + 次タスク + セッション完了事項 (handoff_to_cc_v* 廃止後の単一正本)
- ~~**learning_design_v4.md**~~: 2026-05-26 `archive/learning_design_v4_20260526.md` に移送 (本書 §2/§3 に統合)
- ~~**handoff_to_cc_v\*.md**~~: 2026-05-26 `.claude/instructions/archive/handoff/` に一括移送 (伝言ゲーム化経路を物理排除)

---
