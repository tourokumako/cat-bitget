# ML 学習デザイン v3 完成版 (2026-05-20 まこさん承認・exchange_spec.md 準拠版)

## 設計提案前 verify (1 行ずつ提示・memory ルール 23 + 価格非依存性 + 23 軸 First Principles)

### 本番再現性 7 項目

1. 最小注文サイズ 0.0001 BTC → per-position サイズ verify (下記)
2. 最小注文額 5 USDT → BTC 価格 stress test ($30k-$150k 全域・下記)
3. Tick size 0.1 USDT → Exit 指値で適用
4. Maker 指値 TTL 3 本 + 同一 side pending 禁止 → add トリガ「前回 add 約定確認 + 時間経過 ≥ 15 分」必須
5. SL 設定 add_count ≥ 2 のみ → MAX_ADDS=1 combo は time_exit/TP のみ運用
6. **メンテはナシ (24/7 取引・exchange_spec.md L37・公式ガイド確認済)**
7. Maker 剥落 0.014% / 0.02% stress test → Phase 5 NET 計算で両値

### 価格非依存性 6 項目

1. ラベル MFE/MAE は pct ベース (USD 絶対値禁止)
2. Exit パラメータ % / 比率 / 分単位 (PROFIT_LOCK_USD → PROFIT_LOCK_PCT に置換)
3. cluster 入力 pct 化
4. feature_importance 上位の USD 絶対値系 blacklist
5. add トリガ % 表現
6. TP_FEE_FLOOR は BTC 価格動的計算

### 23 軸 First Principles

web_claude_role §1.5 / §1.6 / §1.7 準拠・デザイン責任 / 23 軸の存在理由 / 手動 Priority スタートライン

---

## 23 軸の振り分け (修正版・まこさん判断)

| 軸 | 戦略 | 内容 |
|---|---|---|
| A-1 Entry 指標 | A 全投入 | 1432 指標 + 業界カタログ拡張 (TA-Lib / pandas-ta / Murphy / Lopez de Prado) |
| A-2 Exit 指標 | A 全投入 + B 探索 | 業界カタログ 16 サブカテゴリから 12 種以上 (手動 Priority Exit 12 種をスタートライン到達確認用に参照のみ) |
| A-3 閾値・パラメータ | A 全投入 + C 学習 | パラメータ違い並列展開 + 閾値は LightGBM 自動分割 + D-γ 統合 (location_prev / entry_risk_score を特徴量化) |
| A-4 時間軸 K | B 探索 | K = {6, 12, 24, 48, 96, 144, 288} 並列 = **14 ラベル** (対称性活用・LONG_MFE_pct_K ≡ SHORT_MAE_pct_K / LONG_MAE_pct_K ≡ SHORT_MFE_pct_K の数学的恒等式・Phase 0 v3 §3.2 bit-exact 一致確認済・保有時間上限 1 日内) |
| A-5 時間足 bar | A 全投入 | 6 TF (5m/15m/30m/1h/4h/1d) + 1w/1M 追加 = 8 TF (3m は Layer 2 検討・1m は禁止) |
| A-6 MAX_ADDS / 配分 | B + C 学習 + 制約セット | 下記 verify 済バリエーション |
| A-7 サイジング | D 上限固定 + B + C | 合計 0.12 BTC 固定・per-position は BTC=$30k stress test で 0.000167 BTC 以上 + 配分 8 方式並列 |
| B-8 cap | B 探索 | 静的 cap + combo 別 cap + 動的 cap 並列 (**いずれも MAX_ADDS × n_sim ≤ 150 取引所物理上限を絶対遵守**・Layer 1 ② 損 combo 切り捨て後に再評価) |
| B-9 組み合わせ深さ | C 学習 | num_leaves={7,15,31,63,127} × max_depth={3,5,7,10,-1} × min_data_in_leaf={50,100,200,500} Optuna 探索 |
| B-10 学習アルゴ | B 探索 (Layer 3) | LightGBM 主軸 + XGBoost / CatBoost 比較・MiniROCKET は Phase 5 不合格時に投入 |
| B-11 cluster | B 探索 | KMeans k=3/k=4 並列 + 入力 B 案 (LONG/SHORT 差分 4 個追加・16 次元 → 20 次元) |
| B-12 特徴量変換 | A 全投入 + B 探索 | Fractional diff (d=0.3/0.5) + PCA + Wavelet 追加 + MTF 4 方式 (ffill / 5m rolling / アンカー補間 / 複数特徴量分解) を監査経路で比較 |
| B-13 Entry ratio 閾値 | B + C 学習 | rolling 365日 q90/95/99 (現状) + cluster 別独立 quantile 並列 + Triple Barrier (Layer 3) |
| B-14 学習データ範囲 | D 期間固定 + B 探索 | 期間分割は固定 (train 2021-04〜2024-12 / 仮 test 2025 / 本 test 2026 Q1) + Walk-forward / Purged K-fold / CPCV を Layer 3 で探索 |
| B-15 目的関数 | D 主目的固定 + B 探索 | 合格 = 月次 NET ≥ $1,900 全月固定 / train 目的関数は RMSE + Triple Barrier 3 クラス multiclass + EV フィルタを並列実装 (Sharpe maximizing は Phase 2 以降に延期・barrier hit non-smooth で grad/hess 未定義のため・audit#18 2026-05-21) |
| D-α 発火頻度 | C 学習 | 他軸従属変数・per-day 最低限ライン ≥ 10 件制約 (L-117 教訓) |
| D-γ Entry 位置 | A-3 統合 | location_prev / entry_risk_score を A-3 内で特徴量化 |
| D-δ 時間帯曜日 | B 探索 (Layer 2 統合フェーズ) | 統合フェーズで時間帯発火分布可視化 → フィルタ探索 (個別 Priority 最適化禁止・WORKFLOW §設計思想 L230 遵守) |
| D-ε regime | B 探索 (Layer 2) | B-11 B 案結果次第・凍結解除判定 |
| D-ζ マルチサイド | D 許可固定 + C 学習 | hedge_mode 許可・合計 0.12 BTC 内で LONG/SHORT 動的配分 ML 学習 |
| D-η 手数料 | D 固定 | Maker 0.014% (適用) / 0.02% (剥落 stress) / Taker 0.042% / **Funding median +0.0002%/8h baseline (月次 NET 合格判定基準) / p95 0.01%/8h stress (参考値・合格条件には含めない) / LONG 払い・SHORT 受取** (exchange_spec.md L27-28 audit#19 確定) |
| D-θ 発注タイプ | D 固定 + Layer 3 探索 | Maker 指値前提・不約定モデル化は Layer 3 / Phase 7 |

---

## A-6 MAX_ADDS バリエーション (本番再現性 7 項目 verify 通過・exchange_spec.md maxPositionNum=150 反映版)

| MAX_ADDS | n_sim 上限 | per-position サイズ範囲 | BTC=$30k stress | SL 設定 |
|---|---|---|---|---|
| 1 | n_sim ≤ **150** | 0.000167 〜 0.12 BTC | ✅ | なし (MAX_ADDS=1 規定) |
| 2 | n_sim ≤ **75** | 0.000167 〜 0.06 BTC | ✅ | あり |
| 3 | n_sim ≤ **50** | 0.000167 〜 0.04 BTC | ✅ | あり |
| 5 | n_sim ≤ **30** | 0.000167 〜 0.024 BTC | ✅ | あり |
| 8 | n_sim ≤ **18** | 0.000167 〜 0.015 BTC | ✅ | あり |
| 10 | n_sim ≤ **15** | 0.000167 〜 0.012 BTC | ✅ | あり |

n_sim 上限の根拠: exchange_spec.md L36 `maxPositionNum=150`（取引所物理上限・audit#19 確定）。総ポジション数 = MAX_ADDS × n_sim が 150 を超えると物理的に発注不可。

---

## 制約セット (設計時組み込み)

- per-position サイズ ≥ 0.000167 BTC (BTC=$30k stress test 通過)
- **MAX_ADDS × n_sim ≤ 150** (exchange_spec.md maxPositionNum 物理上限・audit#19 確定・厳しい方を採用)
- add トリガは「前回 add 約定確認 + 時間経過 ≥ 15 分」必須 (Maker 指値 TTL 3 本 + 同一 side pending 禁止と整合)
- MAX_ADDS=1 combo は SL なし運用 (time_exit / TP のみ)
- per-position × current_BTC_price ≥ 5 USDT を発注時 verify (価格下落時は no_trade 計上)

---

## per-add 配分パターン (6 方式並列)

| # | 方式 | 構造 |
|---|---|---|
| 1 | 等分 | 全 add 同サイズ |
| 2 | 逓増 (Anti-Martingale・Tharp 系) | add 回数増で大きく |
| 3 | 逓減 (Martingale・破滅リスク stress test 必須) | add 回数増で小さく |
| 4 | 予測強度依存 | 各 add 時点の pred MFE/MAE 比に比例 |
| 5 | Kelly fractional | f* × {0.25, 0.5} |
| 6 | Turtle ピラミッディング | Faith 系 N=20 ATR トリガ |

---

## add トリガ条件 (D-β-1 統合・ML 学習対象)

- 価格逆行幅: {0.3%, 0.5%, 1.0%} (pct 表現・価格非依存)
- 時間経過: {15, 30, 60, 120 分} (TTL 15 分以上必須)
- 指標再発火 (元 Entry 指標再 GC/DC)
- 含み益確認: {0.5%, 1.0%} (pct 表現)
- 複合 (AND/OR)

---

## Phase 別優先順位 (修正版)

| Phase | 着手軸 | 目的 |
|---|---|---|
| Phase 0-1 | A-1 / A-3 / A-4 / A-5 / B-12 / B-14 / B-15 (RMSE 完了 + Triple Barrier multiclass + EV フィルタ Phase 1-c 着手) | 組み合わせ探索空間の確立 + ラベル pct 化 + leak verify 機械化 |
| Phase 2 | B-9 (基本ハイパラ・Optuna 主導) | LightGBM 基本ハイパラ確定 |
| Phase 3 | B-10 / B-11 (cluster k=3/k=4 並列 + 入力 B 案) | アルゴ主軸 + cluster 入力拡張 |
| Phase 4-b | A-2 (Exit 12 種) / B-13 (rolling + cluster 別 quantile 並列) | Exit 候補拡張 + ratio 閾値探索 |
| Phase 5 | A-6 (verify 済 MAX_ADDS) / A-7 (8 方式並列) / B-8 (cap 方式並列) / D-ζ (LONG/SHORT 動的配分) / D-α (発火頻度制約) | ポジション設計完成・月次 NET 評価 |
| Phase 6-7 (Bot 統合) | D-δ / D-ε / D-θ | フィルタ・regime・執行最適化 |

---

## 削除類型 (Phase 5 必須・10 種)

1. 物理枠独占 (占有時間 > 30%)
2. leak 由来 (feature_importance top20 blacklist)
3. 構造的逆行 (実 MFE/MAE 比 < 1.0)
4. train/test 反転 (cluster_movement_match < 50%)
5. 手数料負け (期待 PnL < 手数料 × 2)
6. 最小単位違反 (per-position < 0.000167 BTC・BTC=$30k stress)
7. 最小注文額違反 (per-position × BTC_price < 5 USDT)
8. TTL 整合違反 (add 速度が TTL 制約破る)
9. SL 設定違反 (MAX_ADDS=1 combo で SL 前提 Exit)
10. 価格依存違反 (USD 絶対値ラベル / Exit パラメータ)

※ 旧 #10「メンテ時間帯混入」は exchange_spec.md L37 メンテなし (24/7) のため該当事象なし・削除済。

---

## 手動 Priority スタートライン到達 verify

| 要素 | 手動 Priority | v3 設計 | 到達 |
|---|---|---|---|
| AND 段数 | 3-7 | B-9 num_leaves 7-127 Optuna 探索 (経路長 7 段以上学習可) | ✅ |
| 指標多様性 | 8-10 種 | 1432 + パラメータ違い拡張 + 業界カタログ | ✅ |
| Exit 多様性 | 12 種 | 業界カタログ 16 サブカテゴリから 12 種以上 | ✅ |
| MAX_ADDS | 1 と 5 | {1, 2, 3, 5, 8, 10} verify 通過 | ✅ |
| 共通事前フィルタ | location / risk | A-3 内に特徴量化 (D-γ 統合) | ✅ |

= スタートライン全項目クリア。ここから先が本題 (組み合わせ探索で手動を超える Entry/Exit タイミング発見)。

---

## v2 → v3 修正履歴 (exchange_spec.md 準拠化・2026-05-20)

| # | 修正箇所 | 旧 | 新 | 根拠 |
|---|---|---|---|---|
| 1 | 本番再現性 #6 | メンテ時間帯 火/水/木 05-08 UTC | メンテなし (24/7) | exchange_spec.md L37・L-196 |
| 2 | D-η Funding | 8h 毎 0.01% | median +0.0002%/8h baseline / p95 0.01%/8h stress | exchange_spec.md L27-28・audit#19 |
| 3 | A-6 MAX_ADDS=1 n_sim | ≤ 718 | ≤ 150 | exchange_spec.md L36 maxPositionNum |
| 4 | A-6 MAX_ADDS=2 n_sim | ≤ 359 | ≤ 75 | 同上 (150/2) |
| 5 | A-6 MAX_ADDS=3 n_sim | ≤ 239 | ≤ 50 | 同上 (150/3) |
| 6 | A-6 MAX_ADDS=5 n_sim | ≤ 143 | ≤ 30 | 同上 (150/5) |
| 7 | A-6 MAX_ADDS=8 n_sim | ≤ 89 | ≤ 18 | 同上 (150/8) |
| 8 | A-6 MAX_ADDS=10 n_sim | ≤ 71 | ≤ 15 | 同上 (150/10) |
| 9 | 制約セット | MAX_ADDS × n_sim ≤ 718 | MAX_ADDS × n_sim ≤ 150 | 同上 |
| 10 | B-8 cap | (物理上限言及なし) | MAX_ADDS × n_sim ≤ 150 絶対遵守を追記 | 同上 |
| 11 | 削除類型 | 11 種 (#10 メンテ時間帯混入 / #11 価格依存違反) | 10 種 (旧 #10 削除・旧 #11 を #10 に繰り上げ) | exchange_spec.md L37 |
| 12 | A-4 ラベル数 | 28 ラベル独立学習 | **14 ラベル独立学習** (対称性活用) | Phase 0 v3 §3.2 bit-exact 一致確認・2026-05-20 まこさん承認 |
| 13 | B-15 目的関数 | RMSE + 直接 PnL + Sharpe custom objective 並列 | **RMSE 回帰 + Triple Barrier 3 クラス multiclass + EV フィルタ並列** (Sharpe は Phase 2 以降に延期) | audit#18 (2026-05-21・barrier hit non-smooth で grad/hess 未定義) + ChatGPT 独立検証で同結論・まこさん 2026-05-21 再承認 |

23 軸振り分け表の構造・MAX_ADDS バリエーション表構造・per-add 配分 6 方式・add トリガ条件・Phase 別優先順位・スタートライン到達 verify は変更なし。

**ラベル数の補足 (2026-05-20 まこさん承認・14 ラベル採用)**:
- v3 提示時点では「28 ラベル」と書かれていたが、Phase 0 v3 §3.2 で対称性 (LONG_MFE_pct_K ≡ SHORT_MAE_pct_K / LONG_MAE_pct_K ≡ SHORT_MFE_pct_K) が bit-exact 確認され、14 ラベル独立学習で同情報量・学習時間半減が判明。
- 採用方針: **14 ラベル独立回帰モデル**（LONG_MFE / LONG_MAE × K=7 = 14 個・SHORT 側は LONG 側の予測値を流用）
- Phase 5 Replay 時に Funding 非対称性 (median +0.0002%/8h・LONG 払い・SHORT 受取) を方向別に適用 (ラベル予測段階では関係なし)
