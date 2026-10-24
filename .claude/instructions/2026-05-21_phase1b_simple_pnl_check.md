# Phase 1-b: 簡易 PnL チェック (light 枠)

作成日: 2026-05-21
発注者: Web Claude (PM) → CC
種別: 機械的タスク (新規学習なし・naive 売買シミュレーション + 月次集計のみ)
規模: light 枠 80-120 行 (L-198 / memory ルール 24 準拠)
保存先: `.claude/instructions/2026-05-21_phase1b_simple_pnl_check.md`

---

## §0 背景・スコープ

Phase 1-a 完了 (commit 22e75a9 想定・rmse_ratio 14/14・leak 全 PASS・lift 14/14)。次工程 Phase 1-c (PnL/Sharpe custom objective・audit#18 経由・2-3 日) に進む前の **破綻フィルタ** として、Phase 1-a 予測値が現実の売買 PnL に変換可能かを最速で判定する。

### §0.1 Phase 1-a observation 反映 (Web Claude verify 2026-05-21)

完了報告 §X observation 1-3 を踏まえ、本指示書は以下を採用:
- 短期 K (K=6/K=12/K=24) を主検証対象 (学習成功明確・pred_std/label_std ratio ≥ 0.27)
- 長期 K (K=288 / K=48 LONG_MFE) は補助 lens (定数寄り・破綻判定に使わない)
- ATR_pct dominance を踏まえ、Entry 判定が「ATR=ボラ高」だけになっていないか発火頻度で検知

---

## §1 着手前必読 (4 件)

1. `.claude/memory/phase_flow_v3_with_recovery.md` §1 (Phase 1-b 詳細・recovery 経路)
2. `.claude/instructions/2026-05-21_phase1a_lgbm_rmse_completion.md` §X observation
3. `cc_ml_design_spec.md` §1.6 不合格時の対応 / §8 Prime Directive
4. `.claude/rules/false_positive_incident_policy.md` §0-2 ポジション上限

---

## §2 Prime Directive 事前宣言 (cc_ml_design_spec §8)

| # | 変数 | 因果性 | 根拠 |
|---|---|---|---|
| 1 | Phase 1-a 予測値 (predictions_test_2025.parquet) | YES | 推論時点 t の特徴量から学習済モデルで生成・本番再現可 |
| 2 | BTC OHLC (5y CSV) | YES | 時点 t の bar 確定値 |
| 3 | Maker 手数料 0.014% | YES | exchange_spec.md L23 確定 |
| 4 | Funding | 適用しない | Phase 5-e で正式適用・本タスクは簡易 |

## §3 ポジション上限 verify

simulation 中の各時点 t で `sum(active_position_btc) ≤ 0.12` を実測・max を完了報告に明示。違反検知時は STOP。

---

## §4 simulation 仕様

### §4.1 入力

- `results/priority_rebuild/ml_phase1a_rmse/predictions_test_2025.parquet` (105,120 行 × 14 列)
- `data/BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv` (2025 期間のみ使用)

### §4.2 Entry 条件 (3 K 並列で評価・主判定は K=12)

| K | 用途 | Entry 条件 (LONG のみ) |
|---|---|---|
| K=6 (30min) | 補助 | `pred_LONG_MFE_K6 / pred_LONG_MAE_K6 ≥ 1.5` |
| **K=12 (1h)** | **主判定** | `pred_LONG_MFE_K12 / pred_LONG_MAE_K12 ≥ 1.5` |
| K=24 (2h) | 補助 | `pred_LONG_MFE_K24 / pred_LONG_MAE_K24 ≥ 1.5` |

K=288 / K=48 LONG_MFE は使用しない (observation 1・定数寄りで判定不可)。

### §4.3 Exit 条件 (naive)

`min(K bars 経過 (保有期間上限), pred_MFE × 80% 到達, pred_MAE 絶対値到達)` のいずれか早い方。

### §4.4 ポジション

| 項目 | 値 |
|---|---|
| 1 ポジション | 固定 0.01 BTC |
| 同時保有上限 | 12 (合計 0.12 BTC) |
| Side | LONG のみ (SHORT は Phase 5 で対称性流用) |
| 手数料 | Maker 0.014% × 2 (entry + exit) |
| Funding | 適用しない |

### §4.5 出力

```
results/priority_rebuild/ml_phase1b_simple_pnl/
  monthly_pnl_K{K}.csv         × 3  (各 K の月次 PnL 12 行)
  trade_log_K{K}.parquet       × 3  (全 trade の entry/exit/pnl_pct)
  entry_frequency_K{K}.csv     × 3  (日別発火頻度)
  summary_judgment.json             (合格判定結果)
  execution_log.txt
```

---

## §5 合格判定 (3 K 並列・主判定は K=12)

### §5.1 K=12 主判定 (Phase 1-c 進行可否)

| # | 指標 | 基準 |
|---|---|---|
| 1 | 12 ヶ月中プラス月数 | **6 ヶ月以上** |
| 2 | 年間 NET (USD・BTC=$60k 換算) | **プラス** (絶対額不問) |
| 3 | 発火頻度 | **1 日 5-50 件** |

### §5.2 K=6 / K=24 補助判定

K=12 と方向が一致するか確認 (3 K 全てで「プラス月 ≥ 6」なら強い兆し / K=12 のみ合格なら K=12 ratio 閾値の敏感度を確認)。

### §5.3 ATR dominance 検知 (observation 2 対応)

K=12 発火 ts の atr14_pct__5m 値分布を出力:
- 発火 ts の atr14_pct 中央値 / 全 ts 中央値 = X
- **X > 1.5** なら「高ボラ ts でしか発火していない」= ATR ボラ予測のまま・Phase 1-c で改善余地あり
- **X ≤ 1.2** なら「ATR 以外の特徴量も使えている」= 良いシグナル

完了報告に X 値を明示。

---

## §6 不合格時の改善フロー (phase_flow_v3_with_recovery §1.6 準拠)

| 不合格パターン | 戻り先 |
|---|---|
| K=12 で 12 ヶ月全てマイナス | **Phase 1-a 立て直し協議** (特徴量見直し / 学習データ範囲再検討) |
| K=12 で 6 ヶ月未満プラス + 年間 NET マイナス | **Phase 1-c へ進む** (PnL/Sharpe で改善見込み) |
| 発火頻度 < 5 件/日 | 閾値 1.5 → 1.3 で 1 回再 simulation |
| 発火頻度 > 50 件/日 | 閾値 1.5 → 2.0 で 1 回再 simulation |
| ATR dominance X > 2.0 | **Phase 1-a 立て直し協議** (ATR_pct を blacklist 入りで再学習検討) |
| ポジション上限 0.12 BTC 超過 | **即時 STOP・実装 bug 報告** (Prime Directive 違反) |

---

## §7 完了報告必須証跡 (light 枠・5 点)

1. monthly_pnl_K12.csv (12 行・月次 NET PnL)
2. summary_judgment.json (3 K 別判定結果 + ATR dominance X 値 + ポジション上限 max)
3. execution_log.txt (開始/終了時刻・終了コード)
4. 完了報告 md (`.claude/instructions/2026-05-21_phase1b_simple_pnl_check_completion.md`):
   - §1 Prime Directive 4 項目宣言
   - §2 ポジション上限 max 実測値
   - §3 K=12 主判定 3 指標結果
   - §4 K=6/K=24 補助判定
   - §5 ATR dominance X 値
   - §6 GO/NO-GO + 不合格時の戻り先 (§6 テーブル該当行)
5. 再現コマンド 1 行

---

## §8 保管 & 終了条件

- 本指示書: `.claude/instructions/2026-05-21_phase1b_simple_pnl_check.md` + git commit
- 完了報告: 上記 §7 #4 + git commit
- 完了 → Web Claude 独立 verify (monthly_pnl_K12.csv 物理 view + summary_judgment.json) → GO/NO-GO 判定 → Phase 1-c 指示書 (full 枠) or 立て直し協議
