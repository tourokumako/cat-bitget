# Phase 2 精度判定 実行指示書

| 項目 | 値 |
|---|---|
| 発行日 | 2026-05-14 |
| 作成者 | Web Claude (PMエージェント) |
| 承認 | まこさん |
| 関連 commit | b14be88 (cc_ml_design_spec.md §1.6/§Phase 2 確定版) |
| 監査経由 | あり (2026-05-14 監査・13件全反映済) |
| 関連必読 | WORKFLOW.md / cc_ml_design_spec.md §1.6 §5 / exchange_spec.md / phase_compliance_checklist.md / leak_incident_20260513.md / handoff_to_web_claude_v3_phase1_phase3a.md §2.3 / .claude/auditor_template.md |

## 着手前必読 (省略禁止・L-179/L-180/L-181)

1. WORKFLOW.md §🔴次のタスク (改訂22)
2. cc_ml_design_spec.md §1.6 / §5 Phase 2 (2026-05-14 確定版・commit b14be88)
3. .claude/rules/phase_compliance_checklist.md
4. .claude/rules/exchange_spec.md
5. results/priority_rebuild/leak_incident_20260513.md
6. handoff_to_web_claude_v3_phase1_phase3a.md §2.3 (net_quality 定義) / §2.4 (楽観PnL定義)
7. .claude/auditor_template.md

## Step 0: 着手前準備 (5サブステップ・全件 PASS で Step 1 着手可)

### Step 0-1. 必読ファイル引用 (読んだフリ防止)

以下を CC が逐次貼り付け:

a. cc_ml_design_spec.md §1.6 撤退ライン (新規・commit b14be88) 全文貼り付け
b. cc_ml_design_spec.md §5 Phase 2 (新規) 全文貼り付け
c. WORKFLOW.md §🔴次のタスク (改訂22) 全文貼り付け
d. handoff_to_web_claude_v3_phase1_phase3a.md §2.3 net_quality 計算式の行 引用

各引用が「期待値」と一致しない/省略されている場合 → STOP

### Step 0-2. Phase 1 valid leak 非汚染 verify (監査見落とし D 対応)

```bash
python3 -c "
import pandas as pd
df = pd.read_parquet('results/priority_rebuild/labels_mfe_mae_train_2021_2024.parquet')
ts_col = 'timestamp' if 'timestamp' in df.columns else df.columns[0]
df = df.sort_values(ts_col).reset_index(drop=True)
n = len(df)
train_end = int(n * 0.9)
valid_start = train_end
print(f'train rows: 0 to {train_end-1}')
print(f'valid rows: {valid_start} to {n-1}')
print(f'train末 timestamp: {df.iloc[train_end-1][ts_col]}')
print(f'valid始 timestamp: {df.iloc[valid_start][ts_col]}')
gap_min = (df.iloc[valid_start][ts_col] - df.iloc[train_end-1][ts_col]).total_seconds() / 60
print(f'gap (min): {gap_min}')
assert gap_min == 5.0, f'CRITICAL: train末/valid始 が 5min 連続でない (gap={gap_min}min)'
print('valid leak non-contamination: OK')
"
```

期待: gap = 5.0 min (= 連続5min足で完全分離)
不一致 → STOP (Phase 1 学習方法に leak リスク)

### Step 0-3. 重要定義の明文化 (監査見落とし B/C 対応)

Phase 2 計算スクリプト冒頭に以下のコメントブロックを必ず埋め込む:

```python
# === Phase 2 計算定義 (cc_ml_design_spec §1.6 commit b14be88 準拠) ===
#
# 1. lift% 計算:
#    分母 = 全 5min足 (test 2025) の MFE/MAE 平均
#    分子 = q90/q95/q99 フィルタ後 5min足の MFE/MAE 平均
#    lift% = (分子 - 分母) / 分母 * 100
#
# 2. net_quality = MFE_lift% - MAE_lift% (lift%差分)
#
# 3. 24組合せの重み付け = q90/q95/q99 の Entry件数加重平均
#    weighted_avg = Σ(net_quality[i] × Entry_count[i]) / Σ(Entry_count[i])
#
# 4. 計算対象期間 = 仮テスト 2025-01-01 〜 2025-12-31 (105,120 行)
#
# 5. Entry threshold = entry_thresholds.json (Phase 1 で生成済) を使用
```

### Step 0-4. 入力ファイル整合性 verify

```bash
echo "=====Step 0-4 START $(date) ====="
sha256sum results/priority_rebuild/labels_mfe_mae_test_2025.parquet
sha256sum results/priority_rebuild/ml_phase1/predictions_test2025.parquet
sha256sum results/priority_rebuild/ml_phase1/entry_thresholds.json
sha256sum results/priority_rebuild/ml_phase1/label_distribution_stats.json
sha256sum results/priority_rebuild/ml_phase1/training_summary.csv
ls -la results/priority_rebuild/labels_mfe_mae_test_2025.parquet
python3 -c "
import pandas as pd
df_labels = pd.read_parquet('results/priority_rebuild/labels_mfe_mae_test_2025.parquet')
df_preds = pd.read_parquet('results/priority_rebuild/ml_phase1/predictions_test2025.parquet')
print(f'labels: rows={len(df_labels)} cols={len(df_labels.columns)}')
print(f'preds: rows={len(df_preds)} cols={len(df_preds.columns)}')
ts_col_l = 'timestamp' if 'timestamp' in df_labels.columns else df_labels.columns[0]
ts_col_p = 'timestamp' if 'timestamp' in df_preds.columns else df_preds.columns[0]
print(f'labels period: {df_labels[ts_col_l].min()} 〜 {df_labels[ts_col_l].max()}')
print(f'preds  period: {df_preds[ts_col_p].min()} 〜 {df_preds[ts_col_p].max()}')
"
```

期待:
- labels: rows=105,120
- preds: rows=105,120 (16 ラベル列 + meta)
- 期間 2025-01-01 00:00 〜 2025-12-31 23:55

不一致 → STOP

### Step 0-5. 旧 leak 由来実績の参照値 (監査見落とし G 対応・参考のみ・目標値ではない)

| 指標 | 旧 leak 由来実績 | 用途 |
|---|---|---|
| q99 net_quality 24組合せ平均 | +80.65pp | 大幅乖離フラグ参考 |
| top1 importance share | 0.106 (Phase 1) / 0.027 (Phase 3-a) | 単一指標依存参考 |
| K96 SHORT q99 MFE/MAE 比 | 0.986 (逆行・旧監査懸念3) | 逆行構造の継承確認 |

Phase 2 結果が旧実績から大幅乖離 (差 > 50pp 等) なら「追加調査フラグ」立てる。

## Step 1: Phase 2 計算スクリプト実装

scripts/priority_rebuild/run_phase2_precision.py を新規作成 (既存なら確認・更新)。

### Step 1-A. 計算ロジック (4指標)

#### 1. 主指標: q99 net_quality

[計算式は Step 0-3 のコメントブロック準拠]

24組合せ = K12/24/48/96 × LONG/SHORT × q90/q95/q99

#### 2. 24組合せ件数加重平均

```python
weighted_avg = sum(nq * cnt for nq, cnt in zip(net_qualities, entry_counts)) / sum(entry_counts)
```

#### 3. RMSE sanity (16ラベル)

Phase 1 training_summary.csv の valid_rmse と label_distribution_stats.json の std から比率算出:
```python
rmse_ratio = valid_rmse / label_std
```

#### 4. 厳しいフィルタ MFE/MAE 比 (24組合せ)

```python
mfe_mae_ratio = real_filtered_MFE_mean / real_filtered_MAE_mean
```

### Step 1-B. 出力ファイル

| ファイル | 内容 |
|---|---|
| results/priority_rebuild/ml_phase2/phase2_summary.json | 4指標の合格/不合格 + 確定値 |
| results/priority_rebuild/ml_phase2/net_quality_24combinations.csv | 24組合せ別 net_quality + Entry件数 |
| results/priority_rebuild/ml_phase2/rmse_sanity_16labels.csv | 16ラベル別 valid_rmse/std 比率 |
| results/priority_rebuild/ml_phase2/mfe_mae_ratio_24combinations.csv | 24組合せ別 mean_real_MFE/MAE 比 |
| results/priority_rebuild/ml_phase2/old_leak_comparison.csv | 旧 leak 実績 vs 新実測 比較 |
| logs/phase2_<timestamp>.log | 実行ログ (tee) |

### Step 1-C. 実行コマンド (stderr キャプチャ含む)

```bash
echo "=====🚀 Phase 2 RUN START $(date) ====="
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api
python3 scripts/priority_rebuild/run_phase2_precision.py 2>&1 | tee logs/phase2_$(date +%Y%m%d_%H%M%S).log
```

## Step 2: 4指標判定 + K96 SHORT q99 個別チェック (監査見落とし E 対応)

### 4指標判定マトリクス

| # | 合格基準 | 計算結果 | PASS/FAIL |
|---|---|---|---|
| 1 | q99 net_quality 24組合せ件数加重平均 > +10pp **かつ** 24組合せ中20以上で > 0 | XXpp / XX組合せ | ? |
| 2 | net_quality 最小値 > -50pp | XXpp (組合せ: XX) | ? |
| 3 | 16ラベル中14以上で valid_rmse/label_std < 1.5 | XX/16 | ? |
| 4 | 24組合せ中20以上で mean_real_MFE / mean_real_MAE > 1.0 | XX/24 | ? |

判定:
- 全 PASS → Phase 3 進める
- 1件以上 FAIL → まこさん協議 (k=2 切替 / ML+k=2 / Phase 3 着手継続を決定)

### K96 SHORT q99 個別レポート (監査懸念3対応)

旧 leak 由来実測で MFE=880.32 < MAE=892.80 (逆行) だった組合せが新 leak-free でどうなったか:

````
K96 SHORT q99:
  mean_real_MFE = XXX
  mean_real_MAE = XXX
  net_quality   = XXpp
  判定: ✅維持 / ⚠️逆行 / ❌大幅悪化
````

## Step 3: 旧 leak 由来実績との比較 (監査見落とし G 対応)

| 指標 | 旧 leak 由来 | 新 leak-free | 乖離 | フラグ |
|---|---|---|---|---|
| q99 net_quality 24組合せ平均 | +80.65pp | XX pp | XX pp | ✅/⚠️ |
| top1 importance share | 0.106 | XX | XX | ✅/⚠️ |
| K96 SHORT q99 MFE/MAE | 0.986 (逆行) | XX | XX | ✅/⚠️ |

乖離 > 50pp なら追加調査フラグ・レポートに明示。

## 完了報告必須証跡 5 点 + 物理証跡 8 点

### 完了報告必須証跡 5 点 (WORKFLOW.md 規定)

1. **コード総点検 grep 結果**
   - `grep -n "0.0002\|月次平均\|月次500" scripts/priority_rebuild/run_phase2_precision.py`
   - `grep -n "lift_pct\|net_quality" scripts/priority_rebuild/run_phase2_precision.py`

2. **数値の二重提示**
   - チャットサマリー: 4指標判定 + K96 SHORT q99 + 旧leak比較
   - 出典: 各 CSV/JSON ファイル名 + 該当行

3. **成果物ファイル実体** (sha256 + 行数 + 更新時刻)
   - phase2_summary.json / net_quality_24combinations.csv / rmse_sanity_16labels.csv
   - mfe_mae_ratio_24combinations.csv / old_leak_comparison.csv / phase2_<timestamp>.log

4. **実行ログ**
   - 開始/終了/所要/終了コード
   - Python warnings 全件 (no warnings の場合も明示)

5. **絞り込み示唆語彙 自己 grep 結果** (全件 no matches 含む)

### 物理証跡 8 点

1. 入力ファイル証跡 (Step 0-4 引用)
2. 計算プロセス内部証跡 (lift% 分母分子・24組合せ Entry件数)
3. 出力ファイル証跡 (sha256/バイト数・1KB未満は警告)
4. 第三者再計算検証 (1組合せ独立計算で bit-exact 一致)
5. 入力データ sanity (各列 null率 上位10件)
6. stderr / Python warning 全件
7. 同コマンド bit-exact 再現性確認
8. K96 SHORT q99 逆行検知

## 完了後の状態

- 4指標判定結果が phase2_summary.json に保存
- 24組合せ × 16ラベルの全数値が CSV 出力
- 旧 leak 実績との比較表が保存
- まこさんが「Phase 3 進む / 協議」を判断する材料が揃う
- bit-exact 再現性確認済

## 次のステップ (Phase 2 完了後)

- 全 4指標 PASS → Phase 3 (ハイパラ調整) 着手指示書作成
- 1件以上 FAIL → まこさん協議 → 原因切り分け → 対応決定
  - 協議時に必要ならダッシュボード作成 (今回は最初から作らない)

## 完了報告先

`.claude/instructions/2026-05-14_phase2_execute_completion.md` (別ファイル) に
全証跡を記載し commit。
