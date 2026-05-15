# 完了報告：Phase 4-b trailing exit 実装 verify（audit#12 波及範囲確認）

完了日時: 2026-05-15
対応指示書: `.claude/instructions/2026-05-15_phase4b_trailing_exit_verify.md`
このタスクではコミットなし（verify のみ・コード修正なし）

---

## 異常値スメルテスト

**該当なし（実装読解 verify のみ・新規数値生成なし）**

---

## Step 0-1: 必読ファイル引用

### a. `false_positive_incident_policy.md` §5 関所B 全文

> **関所 B: 全工程の未来参照 verify（変数名でなく因果性で見る）**
> leak チェックを「ML 特徴量」に限定しない。**Entry / Exit / Replay / PnL 計算のすべて**で「未来データ・未来ラベルを参照していないか」を verify し、完了報告必須証跡に含める。
> 変数名 grep（`mfe_te[i]` 等）だけでは名前変更で素通りするため、**PnL・判定の計算式の入力変数を列挙させ、各変数が推論時点 t で因果的に存在するかを1行ずつ宣言させる**。

### b. handoff v6 §3 audit#12 発覚内容

> `- **発覚内容**: trailing exit が MFE スカラーを直接 PnL に流用 → $6,499/day・勝率 90.4%（目標の 108 倍）`
> `- **波及範囲**: Phase 5 月次 PnL 全数値が無効。Phase 4-b の trailing exit シミュレーションも同様の漏れの可能性（要確認）`

（出典: `.claude/instructions/handoff_to_web_claude_v6_session_20260515.md` L63-64）

### c. `cc_ml_design_spec.md` §3.1 トレーリング定義行

> `| 第 1 弾 | トレーリング | 高値追従・反転で利確 |`

（出典: cc_ml_design_spec.md L168）

### d. `lessons_active.md` L-179 コメント信用禁止行

> `- コードコメントの「look-ahead 防止」表記を信頼しない。実装で守られているか`
> `  を必ず verify`

（出典: lessons_active.md L308-309）

---

## V1: スクリプト総行数

```
429行
$ wc -l scripts/priority_rebuild/run_phase4b_phase5_rolling_option5.py
429 scripts/priority_rebuild/run_phase4b_phase5_rolling_option5.py
```

---

## V2: trailing exit PnL 計算部分の行番号付き現物引用

### Phase 4-b 側（Exit 選定・train データ）

```python
# L207-249 より抜粋（該当部）

fired_idx = fire_tr.index[fire_tr]
mfe_vals  = df_tr_lab.loc[fired_idx, mfe_col].values.astype(float)   # L208-209
mae_vals  = df_tr_lab.loc[fired_idx, mae_col].values.astype(float)   # L209
close_e   = df_tr_lab.loc[fired_idx, 'close'].values.astype(float)   # L210

# ...

for exit_type in ('fixed_tp', 'time_exit', 'trailing'):              # L228
    pnls = []
    for i in range(n_tr):
        ce, mfe, mae, fc = close_e[i], mfe_vals[i], mae_vals[i], fc_vals[i]  # L231
        ...
        mfe_frac = mfe / ce                                           # L235
        mae_frac = mae / ce                                           # L236

        ...
        else:  # trailing 50% of MFE                                 # L247
            raw = ce * (mfe_frac * 0.50) * POSITION_BTC             # L248
```

### Phase 5 側（Replay・test データ）

```python
# L320-351 より抜粋（該当部）

mfe_te  = df_te_lab.loc[fired_idx, mfe_col].values.astype(float)    # L322
mae_te  = df_te_lab.loc[fired_idx, mae_col].values.astype(float)    # L323
close_e = df_te_lab.loc[fired_idx, 'close'].values.astype(float)    # L324

for i in range(len(fired_idx)):
    ce, mfe, mae, fc = close_e[i], mfe_te[i], mae_te[i], fc_vals[i] # L329
    ...
    mfe_frac = mfe / ce                                               # L332
    ...
    entry = ce * (1 + SLIPPAGE) if side == 'LONG' else ...           # L335

    ...
    else:  # trailing 50%                                             # L350
        raw = entry * (mfe_frac * 0.50) * POSITION_BTC              # L351
```

---

## V3: PnL 入力変数の全列挙と因果性宣言

### trailing exit（Phase 4-b 側・L248: `raw = ce * (mfe_frac * 0.50) * POSITION_BTC`）

| 変数名 | 何を表すか | 推論時点 t で確定済みか | 根拠 |
|---|---|---|---|
| `ce` | エントリー時の close 価格 | **YES** | `close_e = df_tr_lab.loc[fired_idx, 'close']`。エントリーバー i の close = 発注基準価格。因果的に確定済み |
| `mfe_frac` | `mfe / ce` = 保有期間 K バーの MFE をエントリー価格で正規化した値 | **NO** | `mfe_vals = df_tr_lab.loc[fired_idx, mfe_col]`。`mfe_col = f"{side}_MFE_K{k}"`。これは**ラベルファイル（ground truth）から取得した実際の未来 K バー内最大有利価格変動**（Maximum Favorable Excursion）。推論時点 t では不明。**look-ahead leak** |
| `POSITION_BTC` | ポジションサイズ 0.12 BTC | **YES** | 定数。確定済み |

**→ `mfe_frac` が t 時点で因果的に存在しない。trailing exit の PnL 計算は look-ahead leak。**

### trailing exit（Phase 5 側・L351: `raw = entry * (mfe_frac * 0.50) * POSITION_BTC`）

| 変数名 | 何を表すか | 推論時点 t で確定済みか | 根拠 |
|---|---|---|---|
| `entry` | スリッページ込みエントリー価格（`ce * (1 + SLIPPAGE)`） | **YES** | close（エントリーバー）×(1+0.005%)。エントリー確定済み |
| `mfe_frac` | `mfe_te[i] / close_e[i]` = 実際の未来 K バー MFE / close | **NO** | `mfe_te = df_te_lab.loc[fired_idx, mfe_col]`。test ラベルの ground truth MFE。推論時点 t では不明。**look-ahead leak（Phase 4-b 側と同一構造）** |
| `POSITION_BTC` | 0.12 BTC | **YES** | 定数 |

---

## V4: trailing exit 以外の未来参照チェック

### 固定 TP（fixed_tp）

**Phase 4-b 側（L237-244）:**
```python
if exit_type == 'fixed_tp':
    if mfe_frac >= tp_pct:            # L238: TP ヒット判定
        raw = ce * tp_pct * POSITION_BTC     # L239: 固定 TP 価格で exit
    elif mae_frac >= sl_pct:          # L240: SL ヒット判定
        raw = -ce * sl_pct * POSITION_BTC   # L241
    else:
        raw = ((fc - ce) if side == 'LONG' else (ce - fc)) * POSITION_BTC  # L243-244
```

`tp_pct`（train 中央値から算出・L217-220）は train データのみで確定。  
`mfe_frac >= tp_pct` の判定は「保有期間 K バー中に TP レベルに到達したか」のバイナリ判定であり、exit 価格は固定 TP（train 由来）。実際の MFE を exit 価格に直接使用していない。  
**→ 標準バックテスト手法。leak ではない。**

### 時間 Exit（time_exit）

```python
elif exit_type == 'time_exit':
    raw = ((fc - ce) if side == 'LONG' else (ce - fc)) * POSITION_BTC  # L246
```

`fc_vals = future_close_k.loc[fired_idx]`（L214）。`future_close_k = close_tr.shift(-k)`（L213）。  
K バー後の close（固定期間・`shift(-k)`）を使う標準時間 Exit。  
**→ 標準バックテスト手法。leak ではない。**

### Entry 判定（rolling q99 閾値）

```python
def rolling_qn(series, window, min_periods, q):      # L84-86
    return series.shift(1).rolling(window=window, min_periods=min_periods).quantile(q)
```

`shift(1)` により t 時点では t-1 以前の 365 日分の history のみ参照。現在バーのデータは含まない。  
`ratio_all = df_all_pred[mfe_col] / df_all_pred[mae_col]`（L142-143）は LightGBM の**予測値**（`df_te_pred` = `predictions_test2025_k12long_refit.parquet`）。実際の未来ラベルではない。  
**→ look-ahead フリー。**

### Phase 5 月次集計（L-182 チェック・期間全体ソートによる未来情報 leak）

```python
monthly = (df_replay.groupby('month')          # L369-372
           .agg(n_fires=('net_pnl','count'), net_pnl=('net_pnl','sum'))
           .reset_index()
           .sort_values('month'))
```

月ごとに集計のみ。`sort_values('month')` は表示用ソートであり選択判定ではない。  
Phase 4-b の best_exit_type 選定（L256-259）は train データ内のみで閉じており、test データの月次 PnL を参照していない。  
**→ 期間全体ソートによる未来 leak なし（L-182 該当なし）。**

---

## V5: net_pnl のコスト控除 verify

### Phase 4-b 側（train 評価・選定用 PnL）

```python
fee_tot  = n_valid * 2 * MAKER_FEE * POSITION_BTC * close_avg  # L252
net_pnl  = sum(pnls) - fee_tot                                  # L253
```

- `MAKER_FEE = 0.00014`（L42）= exchange_spec.md 確定値（0.014%）✅
- 往復：`2 * MAKER_FEE` ✅
- Funding：未控除（Phase 5-e で別途実施・想定通り）
- Slippage：train 評価では未適用（選定用の比較計算のため許容範囲）

### Phase 5 側（test Replay・実 PnL 計算）

```python
entry = ce * (1 + SLIPPAGE) if side == 'LONG' else ce * (1 - SLIPPAGE)  # L335-336
fee = 2 * MAKER_FEE * POSITION_BTC * entry                               # L353
net = raw - fee                                                            # L354
```

- `MAKER_FEE = 0.00014` ✅（L42）
- `SLIPPAGE = 0.00005`（L43）= 0.005% ✅（entry 価格に反映）
- 往復：`2 * MAKER_FEE` ✅
- Funding：未控除（Phase 5-e で別途・想定通り）

**→ 手数料・スリッページの控除は正しく実装されている。`net_pnl` はコスト控除後の値（Funding 除く）。**

---

## V6: 結論

### Phase 4-b 側の trailing exit シミュレーション

**look-ahead leak あり。audit#12 と同一構造。**

- L208-209: `mfe_vals = df_tr_lab.loc[fired_idx, mfe_col]` — 実際の未来 K バー MFE（ground truth）を train ラベルから取得
- L248: `raw = ce * (mfe_frac * 0.50) * POSITION_BTC` — その MFE スカラーを exit 価格に直接流用
- これは「50% の位置で必ず exit できる」という実際には不可能な前提であり、経路情報（どのバーで反転するか）が不要になっている。`MFE * 0.5` は保有期間全体の最大値を事前に知らなければ到達できない exit 価格

### 波及範囲

19 有効組合せ中 **13 件が trailing を best_exit_type として選定**（`cluster_best_exit_option5.csv` 確認）。

trailing が選ばれた理由は、「実際の MFE × 50%」が `fixed_tp`（固定 TP に達しなければ time exit fallback）や `time_exit`（close 価格）よりも高い PnL を示したため。leak によってアップワード・バイアスが乗った train PnL で選定が行われている。

影響を受けている組合せ（trailing 選定・以下 13 件）：
- K12_LONG_q95-q99, K12_LONG_q90-q95
- K12_SHORT_q99, K12_SHORT_q95-q99, K12_SHORT_q90-q95
- K24_LONG_q90-q95
- K24_SHORT_q95-q99, K24_SHORT_q90-q95
- K48_LONG_q90-q95
- K48_SHORT_q95-q99, K48_SHORT_q90-q95
- K96_LONG_q90-q95
- K96_SHORT_q90-q95

**trailing 以外（固定TP・時間Exit・Entry・Replay集計・NET控除）に別問題なし。**

### 修正が必要な範囲

- Phase 4-b の `best_exit_type` 選定：`trailing` を候補から除外し、`('fixed_tp', 'time_exit')` のみで再選定
- Phase 5 Replay：trailing 分岐（L350-351）を削除し、再実行
- Phase 4-b / Phase 5 の全成果物（`cluster_best_exit_option5.csv` / `monthly_pnl_option5.csv` / `phase5_summary.json` 等）は leak 由来につき無効
- 修正は Step 2 別タスクとして実施（このタスクはコード修正なし）

---

## 完了報告必須証跡 確認

1. ✅ Step 0-1 必読引用 a-d（上記）
2. ✅ V1: 総行数 429 行
3. ✅ V2: trailing exit PnL 計算 行番号付き現物引用（Phase 4-b L248・Phase 5 L351）
4. ✅ V3: PnL 入力変数全列挙表（変数名/意味/確定済みか/根拠）
5. ✅ V4: 固定TP・時間Exit・Entry・Replay集計 各チェック結果
6. ✅ V5: net_pnl コスト控除 verify（手数料 L252-253・L353-354・スリッページ L335）
7. ✅ V6: 結論（leak あり / 19件中13件が trailing 選定 / 別問題なし）
8. ✅ 異常値スメルテスト: 該当なし（実装読解 verify のみ・新規数値生成なし）
