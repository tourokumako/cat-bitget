# indicator_thresholds_outline.md — A-2 閾値辞書 骨格（ターン A 成果物）

最終更新: 2026-05-12
ステータス: **骨格のみ・閾値値は未記入**（ターン B 以降で順次埋める）

---

## §0 目的

A-2 探索で使う 145 ファミリー × ロング/ショート閾値辞書を作成する前段階として、ファミリーを **信頼度区分** に分類し、各ファミリーの **調査方針** を決める。閾値の具体値はターン B 以降で埋める。

---

## §1 信頼度区分の定義

| 区分 | 定義 | 調査方針 |
|---|---|---|
| **高** | 業界標準閾値が明確（教科書レベル）| Claude 既知知識で即記入・出典明記 |
| **中** | 概念は一般的だが BTC 5m での具体閾値は文脈依存 | WebSearch 1-2 回で BTC/暗号通貨文脈確認 |
| **低** | 業界標準なし or カスタム指標 | WebSearch + 元実装コード読み・分位点採用判定 |

---

## §2 145 ファミリー 信頼度区分

### §2.1 集計

| カテゴリ | 高 | 中 | 低 | 計 |
|---|---:|---:|---:|---:|
| 1-A | 59 | 6 | 1 | 66 |
| 1-B | 0 | 0 | 20 | 20 |
| 1-C | 0 | 47 | 12 | 59 |
| **合計** | **59** | **53** | **33** | **145** |

### §2.2 1-A（66 ファミリー）

**高信頼度（59 件）**

| ファミリー | 期待閾値タイプ | メモ |
|---|---|---|
| adx14 | 意味的: 20/25/40/50 | トレンド強度の業界標準 |
| atr14_pct | 分位点 P25/P50/P75 | ボラ高低の標準 |
| bb_pct_b | 意味的: 0/0.5/1 | バンド位置 |
| bb_width_pct | 分位点 | ボラ拡張 |
| bb_width_rank_50b | 分位点（ランクなので 0-1）| |
| bearish_engulfing | binary 0/1 | |
| bearish_streak | 連続本数: 0/3/5/7 | |
| bullish_engulfing | binary 0/1 | |
| bullish_streak | 連続本数: 0/3/5/7 | |
| close_above_cloud | binary | 一目均衡表 |
| close_below_cloud | binary | |
| close_vs_ema200_pct | 0%跨ぎ + ±数% | |
| close_vs_ema20_pct | 0%跨ぎ | |
| close_vs_ema50_pct | 0%跨ぎ | |
| close_vs_keltner_lower_pct | 0%跨ぎ | Keltner Channel |
| close_vs_keltner_upper_pct | 0%跨ぎ | |
| close_vs_kijun_pct | 0%跨ぎ | 基準線 |
| close_vs_sma20_pct | 0%跨ぎ | |
| close_vs_sma50_pct | 0%跨ぎ | |
| close_vs_st_lower_pct | 0%跨ぎ | SuperTrend 下限 |
| close_vs_st_upper_pct | 0%跨ぎ | |
| close_vs_vwap20_pct | 0%跨ぎ | |
| cmf_20 | 意味的: 0/±0.05/±0.1/±0.25 | Chaikin Money Flow |
| di_diff | 0跨ぎ | DI+ - DI- |
| di_minus | 意味的: 20/25/30 | |
| di_plus | 同上 | |
| donchian_position_20 | 0-1 範囲・0.2/0.5/0.8 | |
| donchian_width_pct_20 | 分位点 | |
| ichimoku_kijun | close との関係（参考値）| |
| ichimoku_tenkan | 同上 | |
| macd_hist | 意味的: 0 跨ぎ | |
| macd_hist_change | 意味的: 0 跨ぎ | ヒストグラム変化 |
| macd_line | 意味的: 0 跨ぎ | |
| macd_signal | 意味的: 0 跨ぎ | |
| mfi_14 | 意味的: 20/80 | Money Flow Index |
| momentum_10b | 0 跨ぎ | |
| new_high_streak_5b | 連続本数 0/3/5 | |
| new_low_streak_5b | 連続本数 0/3/5 | |
| obv_slope_10b | 0 跨ぎ | OBV slope |
| pinbar_bottom | binary | |
| pinbar_top | binary | |
| pivot_position_100b | 0-1 範囲・0.2/0.5/0.8 | |
| pivot_position_50b | 同上 | |
| realized_vol_20b | 分位点 | |
| realized_vol_rank_50b | 分位点（ランクなので 0-1）| |
| roc_10 | 意味的: 0 跨ぎ + ±数% | |
| roc_20 | 同上 | |
| rsi14 | 意味的: 30/50/70 | 教科書 |
| rsi7 | 意味的: 30/50/70 | 短期版 |
| sma_20 | close との関係 | |
| sma_50 | close との関係 | |
| stoch_k | 意味的: 20/80 | |
| volume_rank_50b | 分位点 | |
| volume_ratio_20b | 意味的: 1.0/1.5/2.0 | 平均比 |
| williams_r | 意味的: -20/-80 | |
| zscore_return_20b | 意味的: ±1/±2 | |
| zscore_return_50b | 同上 | |
| abs_return_3sigma_20b | binary or ±1/±2/±3 | 3σ 超え判定 |

**中信頼度（6 件）**

| ファミリー | 不明点 | 調査方針 |
|---|---|---|
| body_ratio | ろうそく足実体率の具体閾値（0.3 / 0.5 / 0.7?）| WebSearch + 分位点 |
| close_to_high_pct | 「高値接近」判定の閾値（< 0.1%? < 0.5%?）| WebSearch + 分位点 |
| close_to_low_pct | 同上 | 同上 |
| div_macd_14b | ダイバージェンス検出の出力形式（binary or 強度値?）| コード確認 + WebSearch |
| div_rsi14_14b | 同上 | 同上 |
| lower_wick_ratio | 下ヒゲ率の意味的閾値（pinbar 系との関係）| WebSearch |

**低信頼度（1 件）**

| ファミリー | 不明点 | 調査方針 |
|---|---|---|
| upper_wick_ratio | lower_wick_ratio と同じ扱いだが分位点採用が無難 | shape_features.py コード読み + 分位点 |
| mtf_slope_align_3way | カスタム派生指標（slope の符号一致度）| shape_features.py コード読み |

> 注: `upper_wick_ratio` も中扱いに近いが、`mtf_slope_align_3way` と同じくカテゴリ落ちで管理しやすくするため低に寄せる。ターン D で再検討。

### §2.3 1-B（20 ファミリー・全件 低信頼度）

カスタム集約指標群（W=10/20/50 ウィンドウ集約）。業界標準閾値なし。

| ファミリー | 内容予想 |
|---|---|
| avg_body_ratio_W | W バー平均の実体率 |
| avg_lower_wick_ratio_W | W バー平均の下ヒゲ率 |
| avg_upper_wick_ratio_W | W バー平均の上ヒゲ率 |
| bars_since_new_high_W | 直近高値からの経過本数 |
| bars_since_new_low_W | 直近安値からの経過本数 |
| bars_since_swing_high_W | スイング高値からの経過本数 |
| bars_since_swing_low_W | スイング安値からの経過本数 |
| body_direction_flips_W | 実体方向の反転回数 |
| direction_flips_W | 方向反転回数 |
| inverted_v_in_W | 逆 V 字検出 binary |
| m_shape_in_W | M 字検出 binary |
| max_consecutive_new_highs_W | 連続高値更新回数 |
| max_consecutive_new_lows_W | 連続安値更新回数 |
| new_high_in_W | W 内 新高値 binary |
| new_low_in_W | W 内 新安値 binary |
| significant_wick_count_W | 大ヒゲ本数 |
| swing_high_dist_pct_W | スイング高値からの距離率 |
| swing_low_dist_pct_W | スイング安値からの距離率 |
| v_shape_in_W | V 字検出 binary |
| w_shape_in_W | W 字検出 binary |

**調査方針（全 20 件共通）**: shape_features.py を読んで実装ロジック把握 → 出力形式（binary / 整数 / 連続値）に応じて閾値設計。binary は閾値なし（0/1 そのまま使う）。連続値は分位点 P25/P50/P75。

### §2.4 1-C（59 ファミリー）

**中信頼度（47 件）**

Volume Profile / Fibonacci / Pivot 系。概念はメジャーだが「距離 < X%」の具体閾値は BTC 5m 文脈で要確認。

| ファミリーグループ | 件数 | 内容 |
|---|---:|---|
| dist_to_POC_pct | 1 | Volume Profile POC からの距離率 |
| dist_to_PP_pct | 1 | Pivot Point からの距離率 |
| dist_to_R1/R2_pct | 2 | レジスタンス 1/2 からの距離率 |
| dist_to_S1/S2_pct | 2 | サポート 1/2 からの距離率 |
| dist_to_VAH_pct_N*_b* | 9 | Value Area High（N×b パラメータ違い）|
| dist_to_VAL_pct_N*_b* | 9 | Value Area Low（同上）|
| dist_to_fib_*_pct | 4 | Fibonacci retracement 382/500/618/786 |
| dist_to_fib_v2_*_pct | 4 | Fibonacci v2（別計算方式）|
| inside_value_area_N*_b* | 9 | Value Area 内外 binary |
| nearest_fib_distance_pct | 1 | 最近接 Fib レベル距離 |
| nearest_fib_v2_distance_pct | 1 | 最近接 Fib v2 距離 |
| nearest_level_distance_pct | 1 | 最近接サポレジ距離 |
| pivot_zone | 1 | Pivot ゾーン（categorical?）|
| resistance_distance_pct | 1 | レジスタンス距離 |
| support_distance_pct | 1 | サポート距離 |

**調査方針**: 「価格がこれらレベルに **接近** している」判定の業界標準閾値を WebSearch（"trader price proximity to support resistance threshold" 等）。BTC 5m に当てはまる閾値（< 0.1% / 0.2% / 0.5% 等）を選定。

**低信頼度（12 件）**

| ファミリーグループ | 件数 | 内容 |
|---|---:|---|
| nearest_level_touch_count_N*_t* | 12 | サポレジへの接触回数（カスタム）|

**調査方針**: 元コード（regime/ 配下）を読んで「タッチ回数」の意味把握。整数値（0, 3, 5 等）で閾値設計。

---

## §3 ターン別作業計画

| ターン | 対象 | 件数 | 推定作業時間 |
|---|---|---:|---|
| **B** | 高信頼度 1-A 全件 | 59 | 1 ターン内（既知知識）|
| **C** | 中信頼度 1-A + 1-C 全件 | 6 + 47 = 53 | 1-2 ターン（WebSearch）|
| **D** | 低信頼度 1-A + 1-B + 1-C 全件 | 1 + 20 + 12 = 33 | 1-2 ターン（WebSearch + コード）|
| **E** | 4 ファイル統合 + priority_rebuild.md §2.4/§2.5 書き換え | — | 1 ターン |

---

## §4 残課題・気になる点

1. **「ロング向け」「ショート向け」の閾値が同じ指標もある**
   - 例: ADX > 25 はロング・ショート両方で「トレンド有」フィルター
   - 例: 出来高急増（vol_ratio > 2.0）も方向問わず
   - これらは「ロング/ショート共通候補閾値」として 1 つ書き、ターン B 以降で「方向別の効き」を train で測る

2. **同一ファミリー内のパラメータ違いの扱い**
   - 例: `dist_to_VAH_pct_N100_b020` と `dist_to_VAH_pct_N100_b050` は同じ意味（パラメータ違い）
   - 閾値辞書は **ファミリー単位（パラメータ抜き）** で書き、N/b 違いは全列に同じ閾値を適用

3. **TF（5m〜1d）による閾値の違い**
   - 例: RSI 14 の OB 閾値は TF が長くなるほど 70 → 80 に上げるべきか
   - 一般論として TF 違いで閾値を変える慣習はあまりない（RSI 14 はどの TF も 30/70）
   - **同じファミリーは全 TF で同じ閾値**を採用（複雑化を避ける）

4. **連続値 vs binary の扱い差異**
   - binary（engulfing 等）: 閾値なし・そのまま 0/1 使用
   - 連続値: 閾値による絞り込み
   - これも辞書に明記

5. **div_* 系の出力形式**
   - ダイバージェンス検出は実装次第で binary or 強度値 or +/-/0 categorical
   - コード確認必須

---

## §5 ファイル成果物（最終形・ターン E で完成）

| ファイル | 内容 | 役割 |
|---|---|---|
| `priority_rebuild_a2_spec.md` | A-2 フロー全体仕様（Step 1-7・残論点・所要時間）| 仕様書 |
| `indicator_thresholds.md` | 145 ファミリー × ロング/ショート閾値（人間可読・出典付き）| レビュー用 |
| `indicator_thresholds.json` | 機械可読版（実装が読む）| 実装入力 |
| `a2_progress.md` | Step 別実行状況・結果サマリー・次アクション | 進捗管理 |

これらを `.claude/memory/` 配下に配置（priority_rebuild.md から参照）。
