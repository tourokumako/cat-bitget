# 【タスク】rolling 採用 + 選択肢5 確定 + Phase 4-b + Phase 5 Replay

発行日: 2026-05-14
承認: まこさん（明示的GO）
self_check (A) 通過: 2026-05-14

## 保存・commit 義務（最初にやること）

この指示書を `.claude/instructions/2026-05-14_rolling_phase4b_phase5.md` として保存し commit すること。

---

## 着手前必読（省略禁止）

1. WORKFLOW.md §🔴現在のフェーズ（改訂9）
2. `.claude/instructions/2026-05-14_threshold_drift_eval_completion.md`（rolling 365の数値根拠）
3. cc_ml_design_spec.md §4b（Phase 4-b Exit設計仕様）
4. phase_compliance_checklist.md §4b

---

## 背景・方針転換

まこさん明示承認により以下を確定する：

- **rolling却下（audit#9）を撤回**。理由：BTC価格がtrain→test で2.4倍になり、固定閾値では2025年に発注がほぼゼロになることが実証された。月次$1,900達成のために市場適応が必須。
- **rolling 365日採用**（`shift(1).rolling(365*288).quantile(0.99)`・look-ahead leak verify済み）
- **選択肢5採用**（K × side × q-level・19有効組合せ）

WORKFLOW.mdの「固定維持 + K96 SHORT q99除外 確定」は本タスクで上書きする。

---

## Step 0: WORKFLOW.md 更新

§🔴現在のフェーズを以下に改訂してcommit：

```
- 絶対閾値 drift 対処 = rolling 365日採用（まこさん承認・2026-05-14）
- 選択肢5（K × side × q-level）採用確定
- Phase 4-b 着手中
```

---

## Step 1: rolling 365 を予測値適用スクリプトに組み込む

### 1-1. 閾値計算の変更

train 期間（2021-04〜2024-12）の固定q99 → 各時点t-1以前365日のrolling q99に変更。

```python
def calc_rolling_threshold(series, window_days=365, bars_per_day=288):
    """Look-ahead leak free: shift(1)でt-1以前のみ参照"""
    window = window_days * bars_per_day
    return series.shift(1).rolling(window, min_periods=window//4).quantile(0.99)
```

### 1-2. 適用対象

`predictions_test2025_k12long_refit.parquet` の各K×side組合せ（8系列）にrolling閾値を適用し、新たな発火フラグを生成。

保存先: `results/priority_rebuild/ml_phase4_a_norm/predictions_test2025_rolling365.parquet`

### 1-3. 発火数確認（期待値）

threshold_drift_eval_completion.mdの数値と一致するか確認：
- K12 LONG: 552件
- K12 SHORT: 1,574件
- K96 SHORT: 1,230件
- 全8組合せで ≥ 541件

一致しない場合はSTOP。

---

## Step 2: Phase 4-b（Exit設計）

選択肢5の構造（K × side × q-level、クラスタなし）でExit設計を実行。

### 2-1. 評価対象

active 19組合せ（option5_eval_REEVAL.csvのcutoff_status=activeのみ）。

### 2-2. Exit候補

各組合せについてtrain期間のMFE/MAEから最適Exitを選択：

| Exit種別 | 内容 |
|---|---|
| 固定TP | train MFE q50をTP、train MAE q50をSL |
| 時間Exit | K×2本後に強制決済 |
| トレーリング | peak MFEの50%戻りで決済 |

### 2-3. 選択基準

train期間で `net_pnl = n_fire × (MFE_avg × TP_hit_rate - MAE_avg × SL_hit_rate)` を最大化するExitを各組合せに割り当て。

phase_compliance §4b「Exit約定率 ≥ 12%」を必ずチェック。

### 2-4. 成果物

`results/priority_rebuild/ml_phase4_b/cluster_best_exit_option5.csv`

形式: `K, side, q_band, exit_type, tp_pct, sl_pct, time_bars, train_hit_rate, train_net_quality`

---

## Step 3: Phase 5 Replay

### 3-1. 入力

- 発火: `predictions_test2025_rolling365.parquet`（Step 1成果物）
- Exit: `cluster_best_exit_option5.csv`（Step 2成果物）
- 期間: 2025年全年（1月〜12月）
- ポジションサイズ: 0.12 BTC/trade（上限・WORKFLOW.md §設計思想）

### 3-2. 出力（必須）

```
月次PnL一覧（2025年1月〜12月）
合計PnL
月次平均PnL
月次 ≥ $1,900 達成月数（12ヶ月中）
$60/day 換算値（合計 ÷ 365）
```

### 3-3. 合格基準

月次 ≥ $1,900 が 12/12 → Phase 6へ
未達 → 数字をそのままWeb Claudeに報告（改善議論はその後）

---

## 完了報告必須証跡（WORKFLOW.md 6点準拠）

1. rolling実装のgrep結果（`shift(1)` look-ahead防止確認）
2. 発火数の二重提示（threshold_drift_eval期待値との照合）
3. 成果物ファイル実体（sha256 + 行数）
4. 実行ログ（コマンド・時刻・終了コード）
5. 絞り込み示唆語彙 自己grep結果
6. 月次PnL変化表（月 / 発火数 / PnL）

**月次PnLの実数値を必ず完了報告に含めること。これが最優先の成果物。**

---

## 完了後

Web Claudeが月次PnL数値を受け取り、$60/day達成可否を判断する。
