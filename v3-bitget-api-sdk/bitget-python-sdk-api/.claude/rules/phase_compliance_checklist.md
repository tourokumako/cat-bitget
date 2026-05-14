# phase_compliance_checklist.md — Phase 別現実整合性チェックリスト

最終更新: 2026-05-13
参照: WORKFLOW.md / CLAUDE.md / core_rules.md / exchange_spec.md / lessons_active.md L-179/L-182/L-183

各 Phase 着手前に全項目を verify。1 件でも NG なら GO 不可。

## 未確定項目 (暫定値で正本化・確定後置換)

| 項目 | 確定方法 | 確定値 / 暫定値 | 確定後タスク |
|---|---|---|---|
| ~~Maker fee 実値~~ | ~~まこさん Bitget 管理画面確認~~ | **✅ 確定: 0.00014 (適用) / 0.0002 (標準・剥落復帰時)** 出典: exchange_spec.md L7 (2026-05-13) | ~~ML pipeline 全スクリプト一斉置換~~ → Phase 1〜6-b スクリプトは既に 0.00014 実装済 |
| Funding rate 動的化 | Bitget API funding-history endpoint | 0.0001 (0.01%/8h 固定) | Phase 5-e 改修 |
| Slippage 一般 | 実運用ログから推定 | 0.005% 全約定加算 | Phase 7-e デモ結果から実測値置換 |

## Phase 0 (build_labels.py)

| # | チェック項目 | verify 方法 |
|---|---|---|
| 0.1 | 入力 CSV が Bitget USDT-FUTURES history-candles で取得済み | OUT_CSV ファイル名に "bitget" 含む |
| 0.2 | look-ahead 防止 (fractal): pivot_high[j+2]=h[j] | `grep -n 'pivot_high\|j+2' structure_features.py` |
| 0.3 | look-ahead 防止 (4 種 grep): critical 0 件 | `scan_leak.py` 実行・shift_neg/center_true alert=0 |
| 0.4 | timestamp range 分離 | train 末 < test 始 を parquet min/max で確認 |
| 0.5 | オンライン再現性 (1-A/B/C) ±1e-9 内一致 | inline test 実施済 |
| 0.6 | 入力 CSV のソース取引所を commit msg / README に明記 | git log で "Bitget USDT-FUTURES" 文字列確認 |
| 0.7 | 取得元 = `/api/v2/mix/market/history-candles` | download_bitget_5y.py の ENDPOINT 確認 |
| 0.8 | timestamp 連続性 verify (5min ギャップ以外ゼロ) | download_bitget_5y.py の verify_integrity 通過 |
| 0.9 | ML pipeline (build_labels.py / run_phase*) の INPUT_CSV が Bitget 新 CSV (`*-bitget-*`) を指していることを起動時 assertion で verify | `assert "bitget" in str(INPUT_CSV)` 例: build_labels.py L57 |

## Phase 1 (LightGBM × 16 label)

| # | チェック項目 | verify 方法 |
|---|---|---|
| 1.1 | 時系列 valid split (末尾 10%) | run_lgbm_phase1.py L151-158 |
| 1.2 | early_stopping=50 / random_state=42 | 同 L63-64 |
| 1.3 | 1 ラベル完了直後 feature_importance top20 review (停止) | スクリプトに pause 追加 |
| 1.4 | fractal ベース列ブラックリスト 3段階運用 (Defense in Depth・2026-05-14 監査反映) | 対象パターン: `dist_to_fib_v2_*` / `resistance_distance_*` / `support_distance_*` / `nearest_level_*` ／ **(a) top1-20 hit: 即停止 sys.exit(1)・leak 残存疑い・調査必須** ／ (b) top21-50 hit: 記録継続・full_rank.csv に保存・Step B 後にレビュー ／ (c) top51以下: 通常運用 ／ ブラックリスト緩和は実施しない (将来回帰検出機能維持) |
| 1.5 | lightgbm / sklearn version 記録 | log で出力 |

## Phase 4-a (k-means)

| # | チェック項目 | verify 方法 |
|---|---|---|
| 4a.1 | **fit は train 2021-04〜2024-12 のみ** (test 2025 禁止) | `PREDICTIONS = predictions_train_2021_2024_k12long_refit.parquet` (K12 LONG num_leaves=15 部分採用版・2026-05-14) |
| 4a.2 | scaler / km の joblib 保存 (artifact 名に "train" 含む) | `scaler_train_2021_2024.joblib` 等 |
| 4a.3 | valid / test 2025 / test 2026 Q1 への apply は transform/predict のみ (再 fit 禁止) | コード review |
| 4a.4 | **artifact 名禁止: `*test2025*` / `*test_2025*` / `*test*` 含むファイル名禁止** | `ls ml_phase4_a/*.joblib \| grep -i test` がゼロ件 |
| 4a.5 | **K96 SHORT q99 フォールバック処理** (2026-05-14 案G で追加・audit#9 で発動条件拡張) | 以下のいずれかで当該 cluster / 組合せを no-trade 除外: ① Phase 4-a クラスタリングで K96 SHORT q99 (1,660件) が独立 cluster に分離されない / ② 混在 cluster の実 MFE/MAE 比 < 1.0 / **③ test 発火が 0 件 (2026-05-14 audit#9 見落とし F 追加・K96 SHORT q99 で MFE/MAE 比未定義時の漏れを補完)** / フォールバック発動時の年損失見込み: $169,400 (q99 全体の 9.6%)・全12ヶ月で $1,900 確保継続 (Web Claude 独立評価 2026-05-14) / 出典: results/priority_rebuild/ml_phase2/k96_short_q99_exclusion_scenario.csv + cc_ml_design_spec.md §1.6.2 |

## Phase 4-b (Exit シミュレーション)

| # | チェック項目 | verify 方法 |
|---|---|---|
| 4b.1 | **cluster_best_exit 選定は train PnL のみ** (test 2025 PnL 禁止) | `PREDICTIONS = predictions_train.parquet` |
| 4b.2 | test 2025 / 2026 Q1 は apply のみ (best 選定なし) | コード review |
| 4b.3 | time_exit グリッドを K まで制限 (K×2 禁止) | `TIME_EXIT_GRID = (K//2, K)` |
| 4b.4 | TP 約定モデル (固定 TP): bar high >= tp_price + 0.01% buffer | `simulate_fixed_tp` 改修 |
| 4b.4-b | TP 約定モデル (予測 MFE 中央値ベース): cluster ごとに pred_MFE 中央値 × X% を TP_PCT 候補に追加 (audit#3 懸念4 / K12 LONG mechanism 対応・2026-05-14 案G で追加) | `simulate_predicted_mfe_tp` 新規実装 |

**月別 Exit 約定率必達ライン (2026-05-14 Web Claude 評価)**:
- 2025-12 が年最弱月 (楽観 PnL $16,933・8.9 倍)
- Phase 6-b $1,900 死守には Exit 約定率 ≥ **12%** が必達
- TP 約定 + トレーリング + 時間 Exit の合計で 12% を確保すること
- 12% 未達なら Phase 4-b cluster_best_exit 再選定または Exit type 拡張要
| 4b.5 | Trailing: bar 内 low 先・high 後 想定 | `simulate_trailing` 改修 |
| 4b.6 | entry_price = bar i+1 open ± 0.005% | `extract_entries` 改修 |
| 4b.7 | slippage 0.005% 全約定加算 | `compute_pnl` 改修 |

## Phase 5 / 5-b / 5-c (Replay)

| # | チェック項目 | verify 方法 |
|---|---|---|
| 5.1 | **採用ループは時系列順 (entry_ts 昇順)** | run_phase5_c.py 改修・5-d/5-e に伝播 (L-182) |
| 5.2 | 同 timestamp 内のみ pred_ratio 優先順位付け | コード review |
| 5.3 | 過去の判断を後から覆さない | コード review |
| 5.4 | Maker fee = **0.00014 (適用確定) / 0.0002 (標準・剥落復帰時)** ・出典 exchange_spec.md L7 | Phase 1〜6-b スクリプト全て 0.00014 実装済 (grep 確認済 2026-05-13) |
| 5.5 | **wick 乖離 vs TP_PCT レンジ重ね合わせ分析実施** | 補正 1 の inline 分析・p95 ≤ 0.05% 確認 |

## Phase 5-d (Position size 再計算)

| # | チェック項目 | verify 方法 |
|---|---|---|
| 5d.1 | 0.12 BTC = 合計上限・cap=N で 1 pos = 0.12/N | コード review |
| 5d.2 | 1 pos 最小 ≥ 0.0001 BTC (Bitget min order size) | cap × 0.12/cap ≥ 0.0001 → cap ≤ 1200 (OK) |
| 5d.3 | cap × 0.12/N BTC × price ≤ 必要証拠金 (要 leverage 確認) | exchange_spec.md 参照 |
| 5d.4 | **fee/funding 込みで cap 別 best Exit 再選定** | run_phase5_d 改修 (5-c の Exit を 1/cap 線形使い回さない) |

## Phase 5-e (Funding)

| # | チェック項目 | verify 方法 |
|---|---|---|
| 5e.1 | Funding 8h 境界判定 (entry_ts, exit_ts] | `count_funding_events` L75-95 |
| 5e.2 | LONG = -funding / SHORT = +funding | `apply_funding` L127-128 |
| 5e.3 | 0.01%/8h 固定が許容 (未確定項目) | Bitget funding-history 取得後置換 |

## Phase 6-b (本テスト 2026 Q1)

| # | チェック項目 | verify 方法 |
|---|---|---|
| 6b.1 | **scaler/km の再 fit 禁止** (Phase 4-a artifact をロード) | run_phase6_b L125-127 改修 (L-183 #13) |
| 6b.2 | 月次 NET ≥ $1,900 全 3 月クリア | monthly_pnl |
| 6b.3 | Phase 4-b best Exit (train fit) を apply のみ | コード review |
| 6b.4 | **artifact ファイル名が `*train_2021_2024*` パターンのみ起動時 assertion** | `assert "train" in artifact_path and "test" not in artifact_path` |

## Phase 7-c (run_once_ml.py)

| # | チェック項目 | verify 方法 |
|---|---|---|
| 7c.1 | ALLOW_LIVE_ORDERS = False 維持 | grep 実装 |
| 7c.2 | paper_trading フラグ伝搬 | bitget_adapter.py 検証 |
| 7c.3 | API key 引き出し権限なし | Bitget 管理画面 + bitget_keys.json |
| 7c.4 | hedge_mode 有効 (LONG/SHORT 同時保有) | adapter テスト発注 |
| 7c.5 | min order 0.0001 BTC・cap × size BTC ≥ min | コード assertion |
| 7c.6 | API rate limit 10 req/s 未満 (cap × 推論頻度) | bot 起動時 throttle |
| 7c.7 | placePosTpsl TP/SL ペア整合性 | exchange_spec.md |
| 7c.8 | offline 推論 = online 推論 (artifact deterministic) | verify_ml_inference.py |
| 7c.9 | **起動時に artifact 名を log 出力 → "test" 文字列含むなら起動中止** | `if "test" in artifact_filename: sys.exit("ABORT: test-named artifact detected")` |
