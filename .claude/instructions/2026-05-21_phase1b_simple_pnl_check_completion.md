# Phase 1-b: 簡易 PnL チェック — 完了報告 (light 枠)

完了日: 2026-05-21
担当: CC
指示書: [.claude/instructions/2026-05-21_phase1b_simple_pnl_check.md](2026-05-21_phase1b_simple_pnl_check.md)
出力先: [results/priority_rebuild/ml_phase1b_simple_pnl/](../../results/priority_rebuild/ml_phase1b_simple_pnl/)
所要時間: **1.6 秒** (Phase 1-a 67 分から大幅短縮)

---

## §0 総合判定

**NO-GO → Phase 1-c へ進む**

| 軸 | 結果 |
|---|---|
| K=12 主判定 | **FAIL** (plus_months=1/12 + annual_net=-$825・freq 6.10/日 ✅) |
| K=6 補助 | FAIL (plus_months=0/12 + annual_net=-$995) |
| K=24 補助 | FAIL (plus_months=6/12 ✅ + annual_net=-$364) |
| ATR dominance X | **0.9920** (OK・X ≤ 1.5・観察 2 払拭) |
| ポジション上限 max | **0.12 BTC** (= 上限・違反なし) |
| recovery path | **Phase 1-c へ進む** (RMSE → PnL/Sharpe custom objective で改善見込み) |

---

## §1 Prime Directive 事前宣言 4 項目 (指示書 §2)

| # | 変数 | 因果性 | 根拠 |
|---|---|---|---|
| 1 | Phase 1-a 予測値 | **YES** | bar t の確定特徴量から Phase 1-a 学習済モデル ([commit 9d99dbb](commit/9d99dbb)) 生成・本番再現可 |
| 2 | BTC OHLC (5y CSV) | **YES** | bar t 確定値・Phase 0 で同 CSV 使用 |
| 3 | Maker 手数料 0.014% | **YES** | [exchange_spec.md L9](../rules/exchange_spec.md) 確定 (audit#19) |
| 4 | Funding | **適用しない** | Phase 5-e で正式適用・本タスクは簡易 |

Entry timing は **bar[i] の close 時に判定 → bar[i+1] の open で fill** で leak 防止。

---

## §2 ポジション上限 verify 結果 (指示書 §3)

| 項目 | 実測 |
|---|---|
| **position_sum_btc_global_max** | **0.12 BTC** (上限と完全一致・違反なし ✅) |
| active_count_global_max | 12 (K=12 / K=24 で hit) |
| 違反検知 | **0 件** (sim 内 assertion `sum_btc ≤ 0.12 + 1e-9` 通過) |

K=12 / K=24 で常時 12 ポジ満員に達した = active 制約が binding。Phase 1-c で発火頻度を絞り込み軸変える余地あり。

---

## §3 K=12 主判定結果 (指示書 §5.1)

| # | 指標 | 基準 | 実測 | 判定 |
|---|---|---|---:|---|
| 1 | 12 ヶ月中プラス月数 | ≥ 6 | **1** (2025-05 のみ +$9.90) | ❌ |
| 2 | 年間 NET (USD) | プラス | **-$825.13** | ❌ |
| 3 | 発火頻度 (件/日) | 5-50 | **6.10** | ✅ |

→ 主判定 **FAIL** (条件 1 + 2 が不合格・条件 3 は合格)

### §3.1 K=12 月次内訳 ([monthly_pnl_K12.csv](../../results/priority_rebuild/ml_phase1b_simple_pnl/monthly_pnl_K12.csv))

| month | n_trades | net_pnl_usd | win_rate | avg_pnl_usd |
|---|---:|---:|---:|---:|
| 2025-01 | 167 | -140.67 | 0.365 | -0.84 |
| 2025-02 | 33 | -19.92 | 0.455 | -0.60 |
| 2025-03 | 95 | -50.73 | 0.432 | -0.53 |
| 2025-04 | 74 | -32.02 | 0.446 | -0.43 |
| **2025-05** | **154** | **+9.90** | **0.500** | **+0.06** |
| 2025-06 | 330 | -93.96 | 0.442 | -0.28 |
| 2025-07 | 239 | -80.70 | 0.406 | -0.34 |
| 2025-08 | 231 | -32.11 | 0.390 | -0.14 |
| 2025-09 | 373 | -310.63 | 0.338 | -0.83 |
| 2025-10 | 412 | -1.50 | 0.473 | -0.00 |
| 2025-11 | 51 | -59.42 | 0.353 | -1.17 |
| 2025-12 | 48 | -13.37 | 0.375 | -0.28 |
| **合計** | **2,207** | **-825.13** | **0.408** | **-0.37** |

### §3.2 K=12 exit_reason 内訳 (構造的問題)

| exit_reason | n | sum_usd | avg_pct | win_rate |
|---|---:|---:|---:|---:|
| **SL** | 826 (37%) | **-$2,788** | -0.31% | 0.000 |
| TIME | 918 (42%) | +$141 | +0.01% | 0.495 |
| **TP** | 463 (21%) | **+$1,822** | +0.36% | 1.000 |

- **SL hit が 826 件 / TP の 1.78 倍** → MAE 予測が過小評価 + ratio>=1.5 でも実際は SL 先触れが多い
- TP は 463 件と少ないが利益は +$1,822 (per-trade avg 0.36%) で機能している
- TIME exit (K=12 bars=1h 経過) が 42% 占める → 多くの trade は決着つかず時間切れ
- RMSE 目的では「SL/TP のうちどっちが先か」を学習できていない

---

## §4 K=6 / K=24 補助判定

### §4.1 K=6 ([monthly_pnl_K6.csv](../../results/priority_rebuild/ml_phase1b_simple_pnl/monthly_pnl_K6.csv))

| 軸 | 実測 | 判定 |
|---|---:|---|
| plus_months | **0/12** | ❌ (全月マイナス) |
| annual_net_usd | -$994.69 | ❌ |
| entries/day | 7.12 | ✅ |
| active_count_max | 7 | (上限 12 未満) |

K=12 より悪い (短期では TP/SL ratio がきつすぎる)。

### §4.2 K=24 ([monthly_pnl_K24.csv](../../results/priority_rebuild/ml_phase1b_simple_pnl/monthly_pnl_K24.csv))

| 軸 | 実測 | 判定 |
|---|---:|---|
| plus_months | **6/12** | ✅ |
| annual_net_usd | -$364.33 | ❌ |
| entries/day | 5.08 | ✅ |
| active_count_max | 12 | (上限 hit) |

唯一 plus_months 合格・annual_net も他 K より浅いマイナス。**長期 K の方が予測値が PnL に近い**示唆。

### §4.3 3 K 横断

K=6 → K=12 → K=24 で順に annual_net が改善 (-995 → -825 → -364)。「予測ホライズン拡大で改善する trend」あり。**Phase 1-c で K=24 を主軸に・PnL maximizing で K=12 改善余地大**。

---

## §5 ATR dominance X (指示書 §5.3 + observation 2 対応)

| 項目 | 値 |
|---|---:|
| atr14_pct__5m 全 ts median | 0.136197 |
| atr14_pct__5m K=12 発火 ts median | 0.135113 |
| **X = entry / all** | **0.9920** |
| 判定 | **OK (X ≤ 1.5)** ✅ |

X ≒ 1.0 ⇒ 「ATR 高 ts でしか発火していない」現象は **観測されず**・Entry は ATR_pct とほぼ独立。Phase 1-a observation 2 (atr14_pct dominance) の懸念は **発火頻度ベースでは払拭された**。

→ ATR_pct を blacklist 入れて再学習する立て直しは **不要**。Phase 1-c で目的関数差し替えのみで進める。

---

## §6 GO/NO-GO + 不合格時の戻り先 (指示書 §6)

| 不合格パターン | 該当? | 戻り先 |
|---|---|---|
| K=12 で 12 ヶ月全マイナス | ❌ (2025-05 が +$9.90 で 1 ヶ月プラス) | 該当せず |
| K=12 で 6 ヶ月未満プラス + 年間 NET マイナス | **✅** | **Phase 1-c へ進む** |
| 発火頻度 < 5 件/日 | ❌ (6.10/日) | 該当せず |
| 発火頻度 > 50 件/日 | ❌ | 該当せず |
| ATR dominance X > 2.0 | ❌ (X=0.992) | 該当せず |
| ポジション上限 0.12 BTC 超過 | ❌ (max 0.12 完全一致) | 該当せず |

**戻り先確定: Phase 1-c へ進む (PnL/Sharpe custom objective で改善見込み)。**

### §6.1 Phase 1-c 設計への引き継ぎ

| 引き継ぎ事項 | 内容 |
|---|---|
| 目的関数 | RMSE → 直接 PnL (NET_PnL_pct) maximizing + Sharpe maximizing を並列実装 (学習内容 v3 §B-15) |
| 学習対象 K | K=24 主軸 + K=12 並列 (K=6 は per_trade 利益見込みが薄く優先度低) |
| audit#18 | custom objective grad/hess 数式 verify (Phase 1-c 着手前) |
| 構造観察 | SL hit が TP の 1.78 倍 = MAE 予測過小評価 → custom obj に「SL 先触れ confidence」を組み込む候補 |
| ATR 心配 | 払拭 (X=0.992)・ATR_pct を blacklist 入れる必要なし |

---

## §7 再現コマンド + 実行ログ + 必須証跡

### 再現コマンド (1 行)

```bash
cd v3-bitget-api-sdk/bitget-python-sdk-api && \
python3 scripts/priority_rebuild/run_phase1b_simple_pnl.py
```

### 実行ログ

公式 source: [execution_log.txt](../../results/priority_rebuild/ml_phase1b_simple_pnl/execution_log.txt)
- 開始: 2026-05-21T02:54:11 UTC
- 終了: 2026-05-21T02:54:13 UTC
- 所要: 1.6 秒
- 終了コード: 0

### §7.1 完了報告必須証跡 5 点 (指示書 §7)

| # | 証跡 | 状態 |
|---|---|---|
| 1 | monthly_pnl_K12.csv (12 行) | ✅ (本報 §3.1) |
| 2 | summary_judgment.json | ✅ ([本報 §6 引用](../../results/priority_rebuild/ml_phase1b_simple_pnl/summary_judgment.json)) |
| 3 | execution_log.txt | ✅ |
| 4 | 完了報告 md (本ファイル) | ✅ |
| 5 | 再現コマンド | ✅ (§7) |

### §7.2 出力ファイル全件 ([results/priority_rebuild/ml_phase1b_simple_pnl/](../../results/priority_rebuild/ml_phase1b_simple_pnl/))

```
monthly_pnl_K6.csv / monthly_pnl_K12.csv / monthly_pnl_K24.csv      × 3
trade_log_K6.parquet / trade_log_K12.parquet / trade_log_K24.parquet × 3
entry_frequency_K6.csv / entry_frequency_K12.csv / entry_frequency_K24.csv × 3
summary_judgment.json
execution_log.txt
                                                          = 全 11 ファイル
```

---

## §8 終了条件

- ✅ 3 K simulation 完了・成果物 11/11 揃う
- ✅ Prime Directive 4 項目宣言済
- ✅ ポジション上限 max 0.12 BTC・違反 0 件
- ✅ 合格判定軸 (K=12 主判定 + ATR dominance) 全評価完了
- ✅ NO-GO 確定 + recovery path 確定 (Phase 1-c へ進む)
- ⏭ 次タスク: Web Claude 独立 verify → Phase 1-c 指示書 (full 枠) 発注 + audit#18 経路設定
