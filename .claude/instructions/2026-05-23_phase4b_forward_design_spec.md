# 2026-05-23_phase4b_forward_design_spec.md — Phase 4-b 前倒し設計仕様書 (Step I-1)

**起案**: CC (2026-05-23・改訂26 続編)
**宛先**: CC 自身 (Step I-2 実装担当)
**版**: **v2** (CP3.5 監査 Critical 2 + Major 5 + Minor 4 全件反映・スコープ縮小)
**前身**: v1 (CP3.5 監査で Critical 2 件 + Major 5 件 + Minor 4 件指摘)
**目的**: Step H で発覚した「評価式の暫定過大評価」を是正するため、Phase 4-b 仕様の**最小スコープ部分** (TP 約定モデル + 固定 TP_PCT + time exit) を Phase 1 評価式に前倒し組込みする設計を確定する
**位置づけ**: cc_role.md §1.5.5 で **full 枠 (300-400 行)**・新規設計タスク・v2 でスコープ縮小により行数削減

---

## §0 目的・背景・3 重楽観仮定の数学的分解

### §0.1 本タスクが必要な理由 (CP3 監査 L-208 結論再掲)

Step H 本走 (8 組合せ × 5 fold = 80 学習) 完走後、§4.1 v5.1 統合判定で:

| 指標 | 結果 |
|---|---|
| n_combinations | 8 / 8 ✅ |
| n_combinations_all_pass | **0** ❌ |
| anomaly_smell_detected | **6 / 8 組合せ** (関所 A ② 月次 NET > $3,800) |
| 最悪: K=96 SHORT | sim_pnl 月次相当 **$84,185** (合格ライン $1,900 の **44 倍**) |

CP3 監査 (Plan サブエージェント独立評価) 結論:
- **仮説 B (評価式の暫定過大評価) が 7-8 割支配**
- 仮説 A (学習不良) は 2-3 割重畳
- leak (類型 A) ではない (train_rmse / label_std 比正常 / W1/W2 警告閾値内 / LONG/SHORT 非対称は市場期間特性で説明可)

### §0.2 3 重楽観仮定の数学的分解

現状の `compute_simulated_pnl` (`run_phase1_v5_purged_kfold.py` L295-316) + case_a (`run_lgbm_phase1_v5_case_a_rmse.py` L382-388):

```python
returns_per_trade = pred_MFE / 100.0 - TOTAL_COST_PER_TRADE  # = pred_MFE/100 - 0.00033
sim_pnl_year_usd = returns_per_trade.sum() × (0.024 × 50000)  # = returns_per_trade.sum() × $1,200
```

K=96 SHORT fold 1 で異常値が発生する数学的必然:
- 26,098 trade × 平均 3.23%/trade = return 累計 **841 倍**
- $1,200 × 841 = **$1,010,219 / 年** (= 月次 $84,185)

3 重楽観仮定の内訳:

| # | 仮定 | 現実 | v2 解消方法 |
|---|---|---|---|
| (1) | **TP 約定率 100%** | TP touch しない trade も多数 | §2 TP 約定率 Classifier で 0-1 確率化 |
| (2) | **slippage 0** | maker fee 剥落 / 大口 / spread 拡大で 0.05-0.1% 上振れ | §1.2 cost 0.033% 維持 + Phase 5 stress test |
| (3) | **TP 価格 = MFE ピーク** | TP_PCT 事前確定が必要 | **v2 改訂**: TP 価格を **固定 TP_PCT grid (定数)** に変更・pred_MFE 由来排除 |

### §0.3 本仕様書のスコープと非スコープ (v2 で大幅縮小)

**スコープ (Step I-1 で設計・I-2 で実装・v2 で削減)**:
- Phase 1 評価式の改修 (`compute_simulated_pnl` を Phase 4-b 仕様の **最小部分** で前倒し)
- TP 約定率モデル (§2) + **固定 TP_PCT grid による sim_pnl 計算** (§3) + time exit 暫定モデル (§5)
- **2 method 並列**組込みロジック (固定 TP + time exit のみ・**v2 で trailing 除外**)

**非スコープ (Phase 4-b-1 本確定で扱う)**:
- **trailing exit (v2 で除外・CP3.5 監査 C1 反映)**: 数式整合性確保には別 Classifier 必要 (`trailing_hit_prob`)・Step I スコープ過大化を避ける
- **実 TP 価格モデル (`pred_MFE × quantile`・v2 で除外・CP3.5 監査 C2 反映)**: cluster 未確定下では暫定すぎる・Phase 4-a 完了後に cluster 別最適化
- 24 種 Exit カタログの網羅探索 (phase_flow_v4 L493-509)
- DSR + walk-forward による cluster 別閾値最適化 (technical_analysis_knowledge_base §I.6.3)

---

## §1 設計原則

### §1.1 Prime Directive 適合 (false_positive §0-1)

本仕様書で導入する全変数は、**本番運用の推論時点 t で因果的に取得可能**:

| 変数 | t 時点取得可能性 | 根拠 |
|---|---|---|
| `pred_MFE` / `pred_MAE` (Phase 1 LightGBM 予測値) | ✅ 可 | t 時点 X[i] から計算 (Step E 既存) |
| `TP_hit_prob` (TP 約定率 Classifier 予測) | ✅ 可 | 同上・別 LightGBM Classifier を t 時点 X[i] で推論 |
| **`TP_PCT` (固定 grid・v2 改訂)** | ✅ 可 | Bot 起動時に事前設定する**定数**・推論時に変動なし |
| `time_exit_return_median` (K × side × N 別・train 期間定数) | ✅ 可 | train 期間 (2021-04〜2024-12) のみで計算した定数 |

### §1.2 cost-deducted return 継承 (Step G CP2 監査 C2 反映)

| 項目 | 値 |
|---|---|
| Maker fee (往復) | 0.00028 (= 0.014% × 2・exchange_spec.md 適用確定値) |
| Slippage (暫定) | 0.00005 (= 0.005%・phase_compliance §4b.7) |
| **Total cost per trade** | **0.00033 (= 0.033%)** |
| Funding (Phase 5-e で控除・Phase 1 では暫定除外) | median +0.0002%/8h |

### §1.3 leak 防止 (v2 改訂: 統計式近似前提に書き直し・CP3.5 監査 M5 反映)

本仕様書は **bar-level シミュレーションを使用せず、統計式近似のみ** で評価式を構築する (D4 採用):

- TP 約定率 Classifier の **学習は train (2021-04〜2024-12) のみ**
- `time_exit_return_median` の **算出は train のみ** (test 2025 / test 2026 Q1 は apply のみ)
- 推論時点 t では `TP_hit_prob` (Classifier 予測) と `TP_PCT` (定数) と `time_exit_return_median` (train 期間定数) のみを参照
- **t+1 以降の bar データは特徴量計算・推論に一切参照しない**
- `compute_simulated_pnl_v2` 改修後も Phase 1 評価式は **test 期間結果を見てパラメータ変更しない** (撤退ライン文言の解釈基準・L-208)

### §1.4 暫定性の明示 (技術的負債管理)

本仕様書で導入する全モデルは **Step I-3 (Step H 再走) までの暫定版**。Phase 4-b-1 本確定で:
- 案 A: 24 種 Exit カタログの網羅探索 (phase_flow_v4 L493-509)
- 案 B: cluster 別最適 Exit (Phase 4-a 完了後・k=3 cluster 想定)
- 案 C: trailing exit を別 Classifier (`trailing_hit_prob`) と統合 (v2 で除外した分の再投入)
- 案 D: DSR + walk-forward 最適化 (§I.6.3)

に置き換える。本仕様書の暫定モデルは Phase 4-b-1 着手時に **破棄前提**。

---

## §2 TP 約定率モデル (Classifier)

### §2.1 ラベル定義 (v2.1 改訂: option δ・MFE_pct ラベル流用)

**ラベル**: `tp_hit_K{K}_{side}_pct{TP_PCT}` (0/1 二値)

```
LONG:  tp_hit = 1 if LONG_MFE_pct_K{K}  >= TP_PCT else 0
SHORT: tp_hit = 1 if SHORT_MFE_pct_K{K} >= TP_PCT else 0
```

- `{side}_MFE_pct_K{K}` = build_labels_pct.py で生成済 (= `(max(high[i+1:i+K+1]) - close[i]) / close[i] × 100`)
- `TP_PCT` grid: `{0.3, 0.5, 0.8, 1.2, 1.8, 2.5}` % (6 段階・暫定 grid)
- `K` = {12, 24, 48, 96} の 4 段階
- `side` = {LONG, SHORT}

**v2.1 改訂理由 (実装段階で発見・2026-05-23)**:
parquet (build_labels_pct.py 出力) には `close` 列のみ存在し `open`/`high`/`low` 不在。v2 の `max(high[i+1:i+K+1])` 直接参照は実装不可。既存 `{side}_MFE_pct_K{K}` ラベル (= `max(high) - close` の pct 化) を流用することで **数学的等価変換** (元定義との差は entry slippage 0.005% のみ・TP_PCT 最小値 0.3% の 1/60 = 微小・暫定段階で無視可)。Phase 4-b-1 本確定で bar-level シミュレーション移行時に entry slippage を再考。

### §2.2 学習設計 (D1: 統合 model 案採用)

| 項目 | 値 |
|---|---|
| Model | LightGBM Classifier (binary objective) |
| 特徴量 | Phase 1 と完全同一 (Phase -1 blacklist 64 列 drop 後の 2,604 feature) + `TP_PCT` を特徴量化 (1 列追加 → 2,605 feature) |
| ラベル | `tp_hit_K{K}_{side}_pct{TP_PCT}` |
| Split | Purged K-Fold (5 fold・runner v5.1 流用) |
| Hyperparam | early_stopping=50 / random_state=42 / num_leaves=31 |
| 学習組合せ | 8 組合せ (K × side) × 5 fold = **40 学習** (TP_PCT は特徴量化のため別学習不要) |
| 出力 | `TP_hit_prob` (0-1 確率) |

### §2.3 評価指標

| 指標 | 受け入れ基準 |
|---|---|
| AUC (out-of-fold) | ≥ 0.55 (8 組合せ全て) |
| Brier score | ≤ 0.25 |
| Calibration max deviation | ≤ 0.1 |

### §2.4 leak verify

| # | 項目 | verify 方法 |
|---|---|---|
| (i) | 特徴量 leak: `tp_hit_*` ラベル混入なし | grep `tp_hit` X.columns で 0 件 |
| (ii) | TP_PCT 特徴量は t 時点で事前指定 (Bot 側固定設定) | コード review |
| (iii) | bar i+1 〜 i+K の参照は **ラベル側のみ** | grep `high[i+1` / `low[i+1` で feature 計算側 0 件 |
| (iv) | Purged K-Fold embargo = K + 1 | runner v5.1 既存 |
| (v) | **起動時 assertion (v2 追加・CP3.5 監査 M1 反映)** | `assert "train_2021_2024" in classifier_artifact_path and "test" not in classifier_artifact_path` |

---

## §3 固定 TP_PCT grid による sim_pnl 計算 (v2 改訂: 実 TP 価格モデル除外)

### §3.1 v1 からの変更点 (CP3.5 監査 C2 反映)

v1: `realized_tp_pct = pred_MFE × X%` (X = cluster 別 quantile 50/70/80%)
v2: **`realized_tp_pct = TP_PCT / 100` (定数)**

これにより pred_MFE 由来の楽観仮定 (3 重楽観 (3)) が物理的に消滅。TP 価格は Bot 起動時に事前設定された定数で固定される。

### §3.2 設計

| 項目 | 値 |
|---|---|
| TP_PCT grid | `{0.3, 0.5, 0.8, 1.2, 1.8, 2.5}` % (§2.1 と同一・6 段階) |
| SL_pct grid | `{0.3, 0.5, 0.8}` % (3 段階) |
| 組合せ | TP_PCT (6) × SL_pct (3) = **18 grid / 組合せ K × side** |
| 集約ルール (v2 追加・CP3.5 監査 M2 反映) | **train PnL idxmax 1 つ採用**・残り 17 grid は記録のみ (multi-grid 多重検定回避) |

### §3.3 quantile / pred_MFE 由来 artifact の不要化

v1 で計画した `realized_tp_quantile_train_2021_2024_K{K}_{side}.json` は v2 で**生成しない**。
Step I の評価式は pred_MFE 由来の値を sim_pnl 計算に流さない (Classifier の学習特徴量としては使用継続)。

---

## §4 (削除: trailing exit 暫定モデル — v2 で Step I スコープから除外)

### §4.0 v2 で削除した理由 (CP3.5 監査 C1 反映)

v1 §4 で計画した trailing 数式: `returns = tp_hit_prob × trailing_exit_return + (1 - tp_hit_prob) × time_exit_return`

監査指摘:
- `tp_hit_prob` は「固定 TP_PCT touch する確率」と定義 (§2.1)
- trailing exit は「TP_PCT touch する前に MFE ピーク経由で利確」する exit
- trailing 約定確率は **別 Classifier (`trailing_hit_prob` = MFE >= 2 × trailing_X となる確率)** で別途モデル化すべき
- v1 の数式は `tp_hit_prob × trailing_exit_return` の積が**理論的に意味不明**

**v2 採用判断**: trailing を Step I スコープから除外 (Phase 4-b-1 本確定で `trailing_hit_prob` Classifier と統合して再投入)。

---

## §5 time exit 暫定モデル (v2 微修正: median 化・CP3.5 監査 M3 反映)

### §5.1 動作仕様

**N bar 経過で強制決済** (K × 2 禁止・N ∈ {K/2, K} のみ・phase_compliance §4b.3)。

### §5.2 N bar grid

| N | 意味 |
|---|---|
| **K/2** | 早期 time exit (K=12 → N=6 bar = 30 分) |
| **K** | 標準 time exit (K=12 → N=12 bar = 60 分) |

2 並列で計算・集約は §5.4 train PnL idxmax 1 つ採用 (M2 同型)。

### §5.3 time exit return の近似式 (v2 改訂: mean → median)

```
LONG:  time_exit_return_median = median(close[i+N] - entry[i]) / entry[i] × 100  (train 期間)
SHORT: time_exit_return_median = median(entry[i] - close[i+N]) / entry[i] × 100  (train 期間)
```

**v2 変更点**: v1 は `mean` で算出していたが、train 期間が LUNA / FTX / 2024-04 SHORT 大相場を含む特殊期間のため regime 過依存 (類型 D) リスクあり。`median` (p50) に変更で regime ロバスト性を確保 (exchange_spec.md Funding baseline と同型方針)。

artifact 名: `time_exit_return_median_train_2021_2024_K{K}_{side}_N{N}.json`

### §5.4 集約ルール (M2 同型)

N = {K/2, K} のうち train PnL idxmax 1 つを採用。残り 1 grid は記録のみ。

### §5.5 close 価格と slippage

time exit は **next bar open ± 0.005% slippage** で決済 (phase_compliance §4b.6 entry_price と同様)。

### §5.6 月別歪度 verify (CP3.5 監査 M3 反映)

train 期間の月別 time_exit_return median 分布を可視化し、|skew| > 1.0 (=極端な歪度) 検出時は K × side 別に warning ログ + smoke 受け入れ基準 (§8) で再 verify。

---

## §6 2 method 並列組込み (v2 改訂: 3 method → 2 method・CP3.5 監査 B3 反映)

### §6.1 採用ロジック

1 trade につき **2 method 同時シミュレーション** → 1 trade に 2 sim_pnl 出力:

| method | return 計算式 |
|---|---|
| **(a) 固定 TP + SL** | `TP_hit_prob × (TP_PCT/100) - (1 - TP_hit_prob) × (SL_pct/100) - cost` |
| **(c) time exit のみ** | `time_exit_return_median / 100 - cost` |

各変数:
- `TP_hit_prob` = §2 Classifier 出力
- `TP_PCT` = §3 固定 grid (6 段階) — train PnL idxmax で 1 つに集約
- `SL_pct` = §3 grid (3 段階) — 同上
- `time_exit_return_median` = §5 train 期間 median (K × side × N 別)
- `cost` = §1.2 0.00033

### §6.2 grid 数 (v2 改訂で削減)

| method | grid 軸 | 組合せ数 | 集約後 |
|---|---|---|---|
| (a) 固定 TP + SL | TP_PCT (6) × SL_pct (3) | 18 | **train PnL idxmax で 1** |
| (c) time exit | N (2) | 2 | **train PnL idxmax で 1** |
| **合計 grid (1 組合せ K × side あたり・集約後)** | | **2** | |

8 組合せ × 5 fold = **40 Classifier 学習** + 8 組合せ × 5 fold × 20 grid = **800 sim_pnl 計算** (集約処理は 1 組合せあたり 1 回・低コスト)

### §6.3 §4.1 v5.1 判定指標への組込み

Step I 後の評価は **method 別に 5 指標 (tp_precision / sim_pnl / fold_sharpe / dsr_zscore / fold_count) を出力**。

採用判定:
- method (a) または (c) のいずれかで 6+ 組合せ ALL PASS → Phase 2 進行
- 全 method で ALL PASS なし → 案 X (Layer 3) or 案 Z (案 b-f 順次) 検討

DSR n_trials (selection bias 補正): 8 組合せ × 2 method = **16** (v1 の 48 から削減)

---

## §7 `compute_simulated_pnl` 改修方針

### §7.1 計算方式 (D4: 統計式近似採用)

```python
def compute_simulated_pnl_v2(
    pred_MFE: pd.Series,                  # 学習結果 (Classifier 入力特徴量・PnL 計算には未使用)
    tp_hit_prob: pd.Series,               # §2 Classifier 出力
    tp_pct: float,                        # §3 固定 grid (定数・例: 0.5)
    sl_pct: float,                        # §3 固定 grid (定数・例: 0.5)
    time_exit_return_median: float,       # §5 train 期間 median (定数)
    method: str,                          # "fixed_tp" / "time_exit"
    cost_per_trade: float = 0.00033,
    position_size_btc: float = 0.024,
    btc_price_avg: float = 50000.0,
) -> Tuple[int, float, Dict[str, float]]:
    """
    statistical approximation (bar-level シミュレーションではない).
    v2 改訂: pred_MFE は PnL 計算に流さない (Classifier 特徴量にのみ使用).

    Returns:
        months_positive: トレードがあった月のうちプラス月数
        year_usd: 年間 NET ($)
        diagnostics: TP_hit_prob 統計等
    """
    if method == "fixed_tp":
        # TP_PCT / SL_pct は事前固定定数・pred_MFE 由来なし
        returns_per_trade = (
            tp_hit_prob * (tp_pct / 100.0)
            - (1.0 - tp_hit_prob) * (sl_pct / 100.0)
            - cost_per_trade
        )
    elif method == "time_exit":
        # time_exit_return_median は train 期間定数
        returns_per_trade = pd.Series(
            time_exit_return_median / 100.0 - cost_per_trade,
            index=tp_hit_prob.index,
        )
    # 月次 NET 計算は旧式継承
    monthly = returns_per_trade.groupby(
        returns_per_trade.index.to_period("M")
    ).sum()
    months_positive = int((monthly > 0).sum())
    position_usd = position_size_btc * btc_price_avg
    year_usd = float(returns_per_trade.sum() * position_usd)
    diagnostics = {
        "tp_hit_prob_mean": float(tp_hit_prob.mean()),
        "tp_hit_prob_std": float(tp_hit_prob.std()),
        "tp_pct": tp_pct,
        "sl_pct": sl_pct,
        "time_exit_return_median": time_exit_return_median,
    }
    return months_positive, year_usd, diagnostics
```

### §7.2 v1 → v2 → 旧式 差分

| 項目 | 旧式 (Step H) | v1 想定 | **v2 最終** |
|---|---|---|---|
| TP 約定率 | 100% | TP_hit_prob (Classifier) | **TP_hit_prob (Classifier)** ✅ |
| TP 価格 | pred_MFE 全額 | pred_MFE × quantile | **TP_PCT 固定定数** ✅ (CP3.5 C2 反映) |
| trailing | なし | あり (数式破綻) | **削除** ✅ (CP3.5 C1 反映) |
| time exit | なし | あり (mean) | **あり (median)** ✅ (CP3.5 M3 反映) |
| SL | なし | 暫定 0.5% | **暫定 grid {0.3, 0.5, 0.8}%** |
| cost | 0.00033 | 0.00033 | 0.00033 (継承) |
| pred_MFE の使用箇所 | PnL 計算に直接流入 | quantile 経由で流入 | **Classifier 特徴量のみ・PnL 計算に未流入** ✅ |

### §7.3 計算量見積もり

| 項目 | 旧式 | v1 想定 | **v2** |
|---|---|---|---|
| Classifier 学習 | 0 | 40 | **40** |
| sim_pnl 計算 | 40 | 1,160 (29 grid × 40) | **800 (20 grid × 40)** |
| 所要時間 (sample 89 日 推定) | 1.3 分 | 5-10 分 | **3-5 分** |
| 所要時間 (full 4 年 推定・3 並列) | 2.2 時間 | 4-6 時間 | **3-4 時間** |

v2 スコープ縮小で計算量を v1 から 30% 削減。

### §7.4 関所 A 異常値スメル検出の継続

`_detect_anomaly_smell()` (runner v5.1) は v2 でも継続。method 別に検出。

---

## §8 smoke 受け入れ基準

### §8.1 関所 A 異常値スメル 0 件 (最重要)

| 条件 | 旧式 (Step H 実測) | **v2 目標** |
|---|---|---|
| 関所 A ② 月次 NET > $3,800 件数 | 6 / 8 ❌ | **0 / 8** ✅ |
| 関所 A ③ Sharpe > 3 倍乖離 件数 | 2 / 8 | **0 / 8** ✅ |
| K=96 SHORT 月次 NET (最悪値) | $84,185 | **$200 - $1,500 オーダー** (推定・付録 A 数式根拠) |

### §8.2 TP 約定率モデル品質

| 指標 | 受け入れ基準 |
|---|---|
| out-of-fold AUC | ≥ 0.55 (8 組合せ全て) |
| Brier score | ≤ 0.25 |
| Calibration max deviation | ≤ 0.1 |

### §8.3 月次 NET 分布の現実性

| 統計量 | 受け入れ基準 |
|---|---|
| 8 組合せ × 12 ヶ月 = 96 月次 NET の median | $100 - $500 (現実レンジ・v1 から下方修正) |
| 同 p95 | < $2,500 (関所 A 寸前) |
| 同 p05 | > -$1,000 (大損月の制限) |
| 月次 NET ≥ $1,900 達成月の割合 | 5-15% (現実的・ALL PASS は Phase 5 で詰める) |

### §8.4 leak verify (smoke 段階・v2 で項目追加)

| # | 項目 | verify |
|---|---|---|
| (i) | tp_hit Classifier の特徴量に `tp_hit_*` ラベルが混入していない | grep |
| (ii) | time_exit_return_median が train 期間のみで算出されている | artifact ファイル名に `train_2021_2024` 含む |
| (iii) | test 2025 / 2026 Q1 は apply のみ | コード review |
| (iv) | next bar open ± 0.005% slippage が entry / exit 両方で適用 | コード review |
| (v) | **起動時 assertion (v2 追加・M1 反映)** | `assert "train_2021_2024" in artifact_path and "test" not in artifact_path` |
| (vi) | **pred_MFE が PnL 計算式に未流入 (v2 追加・C2 反映)** | grep `compute_simulated_pnl_v2` で `pred_MFE` 参照が `tp_hit_prob` 算出ルートのみ |

### §8.5 smoke 不合格時のリカバリ

| 失敗パターン | リカバリ |
|---|---|
| 関所 A ② が依然 4+ 組合せでヒット | TP_PCT grid 上限を 2.5% → 1.5% に縮小・SL_pct 下限を 0.3% → 0.5% に拡大 |
| TP 約定率 Classifier AUC < 0.55 | 特徴量設計見直し・TP_PCT 別 model 化 (D1 (a) 案) +3 日 |
| time_exit_return_median の月別歪度 > 1.0 | regime ロバスト化 (cluster 別median・Phase 4-a 前倒し可否判定) |

---

## §9 実装スケジュール + 工数 (v2 改訂: 上方修正)

### §9.1 Step I-2: 実装フェーズ (約 1.6-2.0 週間・v1 から +1.5 日)

| サブ | 工数 | 内容 |
|---|---|---|
| I-2.1 | 1.5-2 日 | TP 約定率 Classifier 実装 (`run_tp_hit_classifier.py` 新規) |
| I-2.2 | 0.5 日 | time_exit_return_median artifact 生成 (`compute_phase4b_train_constants.py` 新規) |
| I-2.3 | 2-3 日 | `compute_simulated_pnl_v2` 改修 (`run_phase1_v5_purged_kfold.py` 修正・v2 シンプル化で v1 想定より工数微増せず) |
| I-2.4 | 1 日 | case_a スクリプト改修 (2 method 並列出力対応・`run_lgbm_phase1_v5_case_a_rmse.py` 修正) |
| I-2.5 | 1 日 | runner v5.2 拡張 (method 別 5 指標出力・関所 A 自動検出継続) |
| I-2.6 | 0.5 日 | smoke test (sample 89 日 / K=12 LONG・5 fold) |
| I-2.7 | 0.5 日 | smoke 受け入れ基準 §8 verify + 不合格時リカバリ判断 |
| I-2.8 | **+0.5-1 日 (v2 追加)** | **集約ロジック (train PnL idxmax) 実装 + unit test** |
| I-2.9 | **+0.5 日 (v2 追加)** | **付録 A 推定値の smoke 実測値による update + diagnostics 出力** |
| | **合計** | **約 7.5 - 10 日** (= 1.5 - 2.0 週間・v1 から +1.5 日) |

### §9.2 Step I-3: 本走 + 再判定 (約 4-5 時間 + 1 日・v2 で短縮)

| サブ | 工数 | 内容 |
|---|---|---|
| I-3.1 | 3-4 時間 (3 並列) | 8 組合せ × 5 fold = 40 Classifier 学習 + 800 sim_pnl 計算 (v2 で grid 削減) |
| I-3.2 | 1 時間 | merge script v2 (`merge_step_h_summaries.py` 流用 + method 別出力対応) |
| I-3.3 | 0.5 日 | §4.1 v5.1 判定 (8 組合せ × 2 method = 16 method×組合せ集計) |
| I-3.4 | 0.5 日 | CP4 監査依頼 (`/audit` 経由・関所 D 重大数字監査経路必須) |

### §9.3 Step I 完了後の分岐 (CP3.5 監査 B4 反映: まこさん判断項目明示)

| 結果 | 次アクション | 判断者 |
|---|---|---|
| 6+ 組合せ ALL PASS (method 別 OR 統合) | Phase 2 (Optuna ハイパラ調整) に進行 | CC + まこさんレビュー |
| 4-5 組合せ ALL PASS | Step G Major M2 + M3 統合 → 再 smoke | CC 推奨・**まこさん最終判断** |
| 0-3 組合せ ALL PASS | 案 X (Layer 3 投入) or 案 Z (案 b-f 順次) を CC が判定提示 → **まこさんレビュー必須** | まこさん |
| **「評価式信頼性回復のみで Phase 2 進行可とするか」** | CC が単独確定しない (B4 反映) | **まこさん判断** |

---

## §10 CP3.5 監査経路 (v2 改訂: §10.2 厳格化・CP3.5 監査 M4 反映)

### §10.1 監査目的

L-209 同型バイアス再演防止 + v2 改訂内容の独立 verify:

1. v2 で C1 (trailing 除外) / C2 (TP 価格固定 TP_PCT 化) が正しく反映されているか
2. Major 5 件 (M1-M5) の修正が論理整合しているか
3. v2 で削除した spec (trailing / pred_MFE × quantile) が他章に残存していないか
4. §10.2 厳格化判定基準が L-209 教訓を物理的に阻止できるか
5. 設計の論理整合性 (§0→§2-§6→§7) が v2 で維持されているか
6. leak チェック (§1.3 / §8.4) が統計式近似前提に書き直されているか
7. 暫定性 (§1.4) が Phase 4-b-1 本確定で破棄前提となっているか

### §10.2 監査結果の扱い (v2 改訂: M4 反映 + まこさん指摘で再訂正)

| 監査結果 | アクション |
|---|---|
| **Critical 0 件 + Major 0 件** | 即 Step I-2 着手 |
| **Critical 0 件 + Major 1+ 件** | 全 Major 対処後 v3 改訂 |
| **Critical 1+ 件** | v3 改訂 |

**再監査 (CP3.5 N+1 回目) の起動条件 (まこさん指摘で訂正・2026-05-23)**:
- v3 改訂で **CC が新規判断・追加設計を加えた場合のみ再監査必須** (L-209 同型バイアス再演警戒対象)
- 監査推奨を **100% そのまま採用**して v3 改訂した場合は **再監査不要・CC 自己 verify (機械的 grep) で v3 反映漏れチェックのみ** (L-209 教訓本旨「Major 後送り判断を CC 単独で確定しない」癖は監査推奨全件採用ケースでは発生しないため・再監査の追加価値なし)

判定骨抜き系の指摘 (M1 / M2 / M4 同型) は **Major でなく Critical 扱い** (L-209 教訓直接適用)。

### §10.3 監査エージェント呼出方法

```
/audit を CC が呼出
監査対象ファイル: .claude/instructions/2026-05-23_phase4b_forward_design_spec.md (v2)
監査観点: auditor_template.md §⑦ 主エージェント作業バイアス監査 を中心に・§①D regime 過依存 / §⑥ 計算ミス検出 も含む
比較対象: v1 監査結果 (本セッション内 CP3.5 1 回目)
```

---

## 付録 A: 旧式 vs v2 評価式 数値比較表 (計算式付き・CP3.5 監査 m4 反映)

### A.1 K=96 SHORT (Step H 最悪値) の v2 推定変化

| 項目 | 旧式 (Step H 実測) | **v2 推定 (method (a) 固定 TP)** |
|---|---|---|
| trade 数 (fold 1) | 26,098 | 26,098 (Entry 判定は不変) |
| 平均 return / trade | 3.23% | **計算: tp_hit_prob × TP_PCT - (1-p) × SL_pct - cost** |
| | | **数式: 0.30 × 0.5% - 0.70 × 0.5% - 0.033% = -0.233%** |
| | | (TP_hit_prob 平均 0.30 / TP_PCT=0.5% / SL_pct=0.5% を仮定) |
| | | **数式: 0.40 × 0.8% - 0.60 × 0.5% - 0.033% = -0.013%** |
| | | (TP_hit_prob 平均 0.40 / TP_PCT=0.8% / SL_pct=0.5% を仮定) |
| | | **数式: 0.50 × 1.2% - 0.50 × 0.8% - 0.033% = 0.167%** |
| | | (TP_hit_prob 平均 0.50 / TP_PCT=1.2% / SL_pct=0.8% を仮定・楽観シナリオ) |
| 年間 NET (fold 1) | $1,010,219 | **-$73,000 〜 +$52,000** (上記 3 シナリオ・$1,200 × 26,098 × return) |
| 月次 NET 換算 | $84,185 | **-$6,083 〜 +$4,333** (楽観シナリオでも合格ライン $1,900 から手堅い範囲) |
| 関所 A ② 判定 | ❌ (> $3,800) | **⚠️ 楽観シナリオは境界・通常シナリオで PASS** (smoke 実測 verify 必須) |

**重要**: TP_PCT と SL_pct は train PnL idxmax 集約後の値が採用される。極端な TP_PCT (2.5%) で TP_hit_prob 0.10 のような低確率なら return は更に小さくなる。Step I-2 smoke で実測する。

### A.2 K=12 LONG (Step H 比較的軽症) の v2 推定変化

| 項目 | 旧式 (Step H 実測) | **v2 推定** |
|---|---|---|
| 月次 NET (max) | $4,298 | **数式: tp_hit_prob 0.40 × 0.3% - 0.60 × 0.3% - 0.033% = -0.093% × trade数 × $1200** |
| | | trade 数 5,000/年 と仮定 → -$558/年 = 月次 -$47 |
| | | (短時間 K では TP_PCT を小さく設定するため return も小さい) |
| 関所 A ② 判定 | ❌ | ✅ |

### A.3 8 組合せ全体の期待変化

| 指標 | 旧式 (Step H 実測) | **v2 期待 (smoke 実測前推定)** |
|---|---|---|
| anomaly_smell_detected | 6 / 8 ❌ | **0-1 / 8** ✅ (smoke で verify) |
| 月次 NET 範囲 | $534 - $84,185 (157 倍乖離) | **$-300 - $2,500** (約 8 倍乖離以内) |
| ALL PASS 組合せ | 0 / 8 | **0-2 / 8** (Step I では合格不要・評価式信頼性回復が目的) |

**注**: 上記推定は理論計算ベース。Step I-2 smoke で実測 verify・付録 A は smoke 実測値で update する (I-2.9)。

### A.4 推定計算の前提と限界

- TP_hit_prob 平均は Classifier 学習後の実測値 (8 組合せ × 5 fold で算出)・本推定は「LONG/SHORT 5m bar の標準的 TP 約定率」を 0.3-0.5 と仮定
- train PnL idxmax の集約により、各組合せの (TP_PCT, SL_pct) ペアが train 期間内で最適化される (= return 期待値が正方向にシフト)
- v2 集約ロジックは多重検定補正後の DSR n_trials=16 で selection bias を補正

---

## 付録 B: 参照ファイル一覧 + sha256

### B.1 設計ベースファイル (2026-05-23 取得)

| ファイル | sha256 |
|---|---|
| `.claude/memory/phase_flow_v4_with_recovery.md` | `124cca8785fba44930101fbdc7a371dfc10f56f1ca72995b2625591516d6a654` |
| `.claude/rules/phase_compliance_checklist.md` | `344ce6b698549dccf1d95742063ee77fe88263179afa095536aa6485078286a7` |
| `.claude/memory/technical_analysis_knowledge_base.md` | `e969f4e4335bbde89238f21b265890ebb91c63ac9be70e094b2b6751443905ec` |
| `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` | `2e60770495bfe74f35246c22c9961bf7dc4b09e53441ff84c9b5655b83fb6559` |
| `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py` | `a3b25eb56c5a2c2b97cf30e8a87f0c01a815e1e5574bd3559a3ad375293e8f5c` |
| `.claude/auditor_template.md` | `420d3705e0955aa9467eec73d5411211ebf261508dc87f9d27fa2b476d3da35b` |

### B.2 主要参照箇所

| 引用元 | 参照節 | 引用内容 |
|---|---|---|
| phase_flow_v4 L451-464 | Phase 4-b-1 Exit カタログ | 24 種 Exit (TP_PCT / SL_PCT / TIME_EXIT 等) |
| phase_flow_v4 L476-486 | Phase 4-b 約定モデル verify 義務 | §4b.4 TP 約定モデル / §4b.6 entry_price / §4b.7 slippage |
| phase_flow_v4 L528-567 | Phase 4-b-2 Entry 閾値 3 方式 | (本仕様書では未使用・Phase 4-b-1 本確定で扱う) |
| phase_compliance §4b.3 | time_exit grid | K//2, K のみ・K×2 禁止 |
| phase_compliance §4b.4-b | TP 約定モデル (予測 MFE 中央値ベース) | (v2 で除外・C2 反映で Phase 4-b-1 移譲) |
| technical_analysis §I.6.3 | Phase 別データ駆動再検討フロー | Phase 4-b: DSR + walk-forward でデータ駆動最適化 (Phase 4-b-1 本確定で適用) |
| run_phase1_v5_purged_kfold.py L295-316 | `compute_simulated_pnl` (旧式) | 改修対象本体 |
| run_lgbm_phase1_v5_case_a_rmse.py L382-388 | returns_per_trade 計算 | cost-deducted return (Step G CP2 監査 C2) |
| auditor_template.md §⑦ | 主エージェント作業バイアス監査 | CP3.5 監査の中核観点 |

### B.3 関連 lesson / handoff

- L-208: 評価式が暫定段階で出た「異常値スメル」を学習不良と取り違える危険 (本仕様書の直接動機)
- L-209: CC 同型バイアス「Major 後送り判断」 (§10.2 厳格化の根拠)
- L-207: test カバレッジ穴 (§2.3 / §8 受け入れ基準で失敗境界 test を必須化)
- L-179: fractal j±2 leak (§2.4 leak verify 4 点で同型再発検知)
- handoff v27 §2.1 (本仕様書の起源)

---

## §11 まこさんレビュー観点 (v2 確定前)

以下 2 点を **CC が判断不能** な戦略本丸として、まこさんレビューを依頼 (v1 から 1 件削減・CP3.5 B4 反映):

1. **§9.3 Step I 完了後の分岐基準**:
   - 「6+ 組合せ ALL PASS」を Step H 再走で達成できなくても **Step I の目的 (評価式信頼性回復) は達成し得る** ことを許容するか?
   - **CC は推奨を出さない (B4 反映・結論誘導回避)**・まこさん判断
2. **§9.1 工数増加 (1.3-1.6 → 1.5-2.0 週間) と Step I-3 計算時間短縮 (4-6 → 3-4 時間 3 並列) のトレードオフ**:
   - v2 でスコープ縮小 (trailing 除外 + pred_MFE × quantile 除外) により Step I 全体は v1 想定より早期完了見込み
   - まこさん許容判断

---

## §12 v1 → v2 → v2.1 改訂サマリー

### v2.1 微修正 (I-2.1 着手前・2026-05-23)
- **§2.1 ラベル定義**: parquet に open/high/low 列なし発見 → 既存 `{side}_MFE_pct_K{K}` 流用 (option δ・数学的等価変換) → 仕様書反映 + まこさん GO 取得済

### v1 → v2 改訂 (CP3.5 監査 1 回目反映)

### Critical (2 件・全件対処)
- **C1**: §6.1 trailing 数式論理破綻 → **Step I スコープから除外** (Phase 4-b-1 本確定で別 Classifier と統合再投入)
- **C2**: §7.1 改修コードに pred_MFE 由来楽観仮定残存 → **TP 価格を固定 TP_PCT grid (定数) に変更** (pred_MFE は Classifier 特徴量にのみ使用・PnL 計算に未流入)

### Major (5 件・全件対処)
- **M1**: §3.4 表現曖昧化 → §3.3 で artifact 不要化 + §2.4 (v) / §8.4 (v) で起動時 assertion 追加
- **M2**: §6.2 grid 集約ルール未定義 → §3.2 / §5.4 で **train PnL idxmax 1 つ採用** 明示・DSR n_trials 16 で再算定
- **M3**: §5.3 time_exit_return mean → **median** に変更 (regime ロバスト化) + §5.6 月別歪度 verify 追加
- **M4**: §10.2 厳格化 → **「Major 1+ 件 → 全件対処後再監査」**・判定骨抜き系は Critical 昇格明示
- **M5**: §1.3 統計式近似前提に書き直し → bar-level シミュレーション記述削除

### Minor (4 件・全件対処)
- **m1**: §7.1 `pred_MFE.clip(lower=0.1)` → **v2 で pred_MFE が PnL 計算式から消えたため不要化**
- **m2**: §1.2 Funding 控除影響 → §1.2 で「Phase 5-e で控除・Phase 1 では暫定除外」を明示継続 (定量化は Phase 5 で扱う)
- **m3**: §9.1 工数楽観 → **+1.5 日 上方修正** (集約ロジック実装 + 付録 update)
- **m4**: §A 推定計算根拠不明 → **数式根拠付き計算表に更新** (TP_hit_prob × TP_PCT - (1-p) × SL_pct - cost の 3 シナリオ)

### B 系 (主エージェント作業バイアス検知・全件対処)
- **B1**: §10.2 Major 後送り経路 → **§10.2 厳格化 (M4 と同型)**
- **B2**: D1-D4 断言の論理的隙 → **D2 (cluster 別 quantile) を Phase 4-b-1 に移譲・D3 (3 同時) → 2 method に削減**
- **B3**: 用語衝突「3 方式並列」 → **「2 method 並列」に改名**
- **B4**: §9.3 結論誘導 → **§11.1 で CC 推奨削除・まこさん判断項目明示**

---

**以上・v2 完**
**次アクション**: CC が `/audit` 経由で **CP3.5 監査 2 回目** 依頼 → 監査結果に基づき v3 改訂 or Step I-2 着手判断 → まこさんレビュー
