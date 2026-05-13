# Web Claude 引き継ぎ資料 v3 — Phase 1 + Phase 3-a 完了報告 (⛔ leak 由来・数値無効)

> # ⛔ **このファイル内の数値・合格判定は全て無効 (2026-05-13)**
>
> 本文中の Phase 1 / Phase 3-a 達成数値は fractal j±2 leak 由来 (L-179)。
> leak 修正コミット `3f64543` (2026-05-13) でコードは修正済だが、本ファイルの数値は再学習が完了するまで無効。
> 新セッションでこのファイルの数値を「達成済み」として引用しない (L-180)。
>
> 詳細: [leak_incident_20260513.md](../../results/priority_rebuild/leak_incident_20260513.md)
> 現方針: [../../WORKFLOW.md](../../WORKFLOW.md) Phase 0 から再開

作成日: 2026-05-13 (⛔ leak 無効マーク: 2026-05-13 同日)
前回引き継ぎ: [handoff_to_web_claude_v2.md](handoff_to_web_claude_v2.md) — A-2 大枠ドラフト確定 (🧊 凍結)
今回の位置付け: v2 で確定した ML 主軸方針に基づき、指示書 [cc_ml_design_spec.md](../../cc_ml_design_spec.md) §5 Phase 1 + Phase 3 の 1 サイクル目を CC が完了したと当時報告したが、**leak 発覚で全数値無効化**。

---

## §1 実施した作業

### 1.1 環境セットアップ

- `pip install --break-system-packages lightgbm` (4.6.0)
- `brew install libomp` (OpenMP 依存)

### 1.2 Phase 1 — デフォルトハイパラ

スクリプト: [run_lgbm_phase1.py](../../scripts/priority_rebuild/run_lgbm_phase1.py)
出力先: [results/priority_rebuild/ml_phase1/](../../results/priority_rebuild/ml_phase1/)

LightGBM × 16 ラベル (K=12/24/48/96 × LONG/SHORT × MFE/MAE) を以下の構成で学習・予測:

| 項目 | 値 |
|---|---|
| train | 2021-04 〜 2024-08 (355,116 行) |
| valid | 2024-08 〜 2024-12 (39,457 行) ← 末尾 10% |
| test  | 2025-01 〜 2025-12 (105,120 行) |
| 特徴量 | 1,432 列全投入 (絞り込みなし) |
| ハイパラ | `learning_rate=0.05, num_leaves=31, n_estimators=2000` (LGBM デフォルト) |
| early_stop | rounds=50 |
| random_state | 42 |

所要 51.8 分・エラー 0。

### 1.3 Phase 3-a — 仮説駆動の 1 セットハイパラ調整

スクリプト: [run_lgbm_phase3_a.py](../../scripts/priority_rebuild/run_lgbm_phase3_a.py)
出力先: [results/priority_rebuild/ml_phase3_a/](../../results/priority_rebuild/ml_phase3_a/)

Phase 1 の弱点 (MAE 系 best_iter=7〜16 = 過学習境界) を狙ったハイパラ変更:

| パラメータ | Phase 1 | Phase 3-a | 狙い |
|---|---|---|---|
| `num_leaves` | 31 | **15** | 木の複雑度抑制 |
| `min_data_in_leaf` | 20 | **100** | 葉最小サンプル増・ノイズ吸収 |
| `learning_rate` | 0.05 | **0.02** | 細かい収束で best_iter 余裕 |
| `feature_fraction` | 1.0 | **0.7** | 1432 指標から木ごと 70%・過剰依存抑制 |
| `bagging_fraction` | 1.0 | **0.8 (freq=5)** | 行サブサンプリング |
| `reg_lambda` | 0 | **0.1** | L2 正則化 |
| `n_estimators` | 2000 | **5000** | early_stop 任せ |

所要 65.2 分・エラー 0。

---

## §2 主要数値（Phase 1 vs Phase 3-a）

### 2.1 best_iter の改善（最大の狙い）✅ 達成

MAE 系（指示書 §1.1 ラベル定義: 最大ドローダウン幅）の学習が成立:

| ラベル系 | Phase 1 | Phase 3-a |
|---|---|---|
| K12 MAE | **31** | **909** |
| K24 MAE | **11** | **322** |
| K48 MAE | **7** | **142** |
| K96 MAE | **16** | **91** |

MFE 系も伸び:

| ラベル系 | Phase 1 | Phase 3-a |
|---|---|---|
| K12 MFE | 662 | 995 |
| K48 MFE | 175 | 611 |
| K96 MFE | 135 | 236 |

### 2.2 valid_rmse 改善%

| ラベル系 | 改善% |
|---|---|
| K12 MAE | **+8.35%** |
| K24 MAE | **+6.39%** |
| K48 MAE | +1.52% |
| K96 MAE | +1.86% |
| MFE 系全般 | -1.8% 〜 +1.0%（ほぼ横ばい）|

→ **狙い通り MAE 改善・MFE 維持**

### 2.3 ML 優位性（vs ランダム発火・net_quality 平均）

`net_quality = MFE_lift% − MAE_lift%` = ML がランダム発火と比べてどれだけ「MFE 高くて MAE 低い」足を選べたか:

| 閾値 | Phase 1 平均 | Phase 3-a 平均 | Δ |
|---|---|---|---|
| q90 | 42.75 | **64.72** | +21.97 |
| q95 | 52.89 | **76.52** | +23.62 |
| q99 | 80.65 | **99.91** | +19.26 |

24 組合せ中 **20 組で改善 / 4 組で後退**:
- 改善大: K12 LONG q99 (+111.78)、K24 全般
- 後退: K48 LONG q99 (−42.37)、K96 LONG q99 (−21.29)、K96 SHORT 系の一部

長期予測 (K48/K96) で **num_leaves=15 が単純すぎた可能性**。

### 2.4 楽観月次 PnL（Exit 未設計・上限値）

| 月 | Phase 1 max | Phase 3-a max | Δ% |
|---|---|---|---|
| 2025-01 | $290,785 | $330,635 | +13.7% |
| 2025-02 | $176,809 | $107,040 | -39.5% |
| 2025-03 | $390,309 | $180,636 | -53.7% |
| 2025-04 | $221,270 | $207,749 | -6.1% |
| 2025-05 | $105,877 | $207,763 | +96.2% |
| 2025-06 | $231,910 | $180,949 | -22.0% |
| 2025-07 | $178,602 | $155,804 | -12.8% |
| 2025-08 | $125,671 | $109,499 | -12.9% |
| 2025-09 | $118,098 | $130,153 | +10.2% |
| 2025-10 | $267,298 | $391,935 | +46.6% |
| 2025-11 | $495,834 | $182,945 | -63.1% |
| 2025-12 | $138,713 | $159,149 | +14.7% |

- 12 ヶ月中 5 改善 / 7 悪化（月別ノイズ大きい・発火件数依存）
- **全月 $100k+ で月次合格ライン $1,900 を 50〜250 倍上回る構造は維持**
- ⚠️ Exit 未設計の上限値。実 NET は Phase 4 後に確定（指示書 §1.6 撤退判定もそこで）

### 2.5 §7 怠け防止チェック

| 項目 | Phase 1 | Phase 3-a |
|---|---|---|
| top1 importance 最大 share | 0.106 (atr14_pct__5m) | **0.027** (atr14_pct__5m) |
| 予測値 std=0 のラベル | 0 | 0 |
| Entry 発火率レンジ | 1.0% 〜 19.3% | 1.0% 〜 19.4% |

→ 偏り減・degenerate なし・極端な発火率なし。**全項目健全**

---

## §3 CC の解釈・断言

**A. ハイパラ調整の方向性は正しい**
- 狙い (MAE 系学習不成立の解消) は明確に達成
- 正則化 + サブサンプリング で過学習対策が機能 (top1 偏り 0.106→0.027)

**B. 一律 num_leaves=15 は短期に最適・長期に厳しすぎ**
- 短期 (K12/K24): net_quality 大幅改善
- 長期 (K48/K96): num_leaves=15 が単純すぎ、K48/K96 LONG q99 で後退

**C. 楽観 PnL の月別変動は本質情報ではない**
- 発火件数 × 月のボラに依存するノイズ
- 12 ヶ月通年の構造的余裕 ($1,900 の 50-250 倍) が維持されてる方が重要

**D. 改善頭打ちには到達してない**
- 指示書 §5 Phase 3「改善が頭打ちになったら Phase 4 へ」→ まだ伸び代

---

## §4 Web Claude にレビューしてほしい論点

1. **次の選択**: Phase 3-b (もう 1 サイクル) vs Phase 4 (Exit 仕立て) のどちらが妥当か
   - CC 推奨: **Phase 3-b**（頭打ち未確認・K48/K96 後退対策で MAE 学習効率はさらに伸びる見込み）
   - 反対意見の余地: 楽観 PnL が既に $1,900 を 50 倍超 → Exit 設計の方が現実 NET に直結する
2. **Phase 3-b の調整方向**（CC 推奨案）:
   - K48/K96 系だけ num_leaves=31 維持・短期は 15 のまま
   - または K 窓ごとにハイパラを別個に持つ（実装的にはモデルごとの param dict）
3. **§7.3 ダッシュボードタブ統合**は Phase 4 後でいいか・それとも Phase 3 完了時にやるか
4. **§1.6 撤退ライン判定**は Phase 4 後の現実 PnL で行う認識で合っているか（楽観 PnL は無視）
5. **本テスト (2026 Q1) のタイミング**: Phase 3-b で頭打ち → Phase 4 Exit → Phase 5 統合 Replay → Phase 6 本テスト、の順で動く理解で合うか

---

## §5 成果物ファイル一覧

### Phase 1
- [results/priority_rebuild/ml_phase1/summary.md](../../results/priority_rebuild/ml_phase1/summary.md)
- [results/priority_rebuild/ml_phase1/lgbm_log_20260512T161516Z.txt](../../results/priority_rebuild/ml_phase1/lgbm_log_20260512T161516Z.txt)
- [results/priority_rebuild/ml_phase1/predictions_test2025.parquet](../../results/priority_rebuild/ml_phase1/predictions_test2025.parquet) (10.8 MB)
- [results/priority_rebuild/ml_phase1/feature_importance_top20.csv](../../results/priority_rebuild/ml_phase1/feature_importance_top20.csv)
- [results/priority_rebuild/ml_phase1/entry_thresholds.json](../../results/priority_rebuild/ml_phase1/entry_thresholds.json)
- [results/priority_rebuild/ml_phase1/entry_firing_rate.csv](../../results/priority_rebuild/ml_phase1/entry_firing_rate.csv)
- [results/priority_rebuild/ml_phase1/random_baseline_comparison.csv](../../results/priority_rebuild/ml_phase1/random_baseline_comparison.csv)
- [results/priority_rebuild/ml_phase1/monthly_pnl_optimistic.csv](../../results/priority_rebuild/ml_phase1/monthly_pnl_optimistic.csv)
- [results/priority_rebuild/ml_phase1/prediction_histograms.png](../../results/priority_rebuild/ml_phase1/prediction_histograms.png)
- [results/priority_rebuild/ml_phase1/pred_vs_real_scatter.png](../../results/priority_rebuild/ml_phase1/pred_vs_real_scatter.png)
- [results/priority_rebuild/ml_phase1/models/](../../results/priority_rebuild/ml_phase1/models/) (lgbm × 16)

### Phase 3-a
- 同構造で [results/priority_rebuild/ml_phase3_a/](../../results/priority_rebuild/ml_phase3_a/)

### スクリプト
- [scripts/priority_rebuild/run_lgbm_phase1.py](../../scripts/priority_rebuild/run_lgbm_phase1.py)
- [scripts/priority_rebuild/run_lgbm_phase3_a.py](../../scripts/priority_rebuild/run_lgbm_phase3_a.py)

### 技術要件（指示書 §1.5 / §7 の意図を満たす標準実装）
- 時系列 valid split (train 末尾 10%) … リーク防止
- early_stopping_rounds=50 … 過学習防止
- random_state=42 … 再現性

以上。
