# Phase 1 LightGBM × 16 ラベル 学習 実行指示書 (leak フリー再構築・監査反映版)

| 項目 | 値 |
|---|---|
| 発行日 | 2026-05-13 |
| 作成者 | Web Claude (PMエージェント) |
| 承認 | まこさん |
| 関連 commit | ff39c4a (Bitget スペック正本化 + ハイパラ更新) / 42d1c21 (Phase 1 学習完了) |
| 監査経由 | あり (監査エージェント審査済 11件全反映) |
| 関連必読 | WORKFLOW.md / CLAUDE.md / .claude/rules/exchange_spec.md / .claude/rules/phase_compliance_checklist.md / ~/.claude/projects/.../memory/feedback_ml_leak_mandatory_check.md / results/priority_rebuild/leak_incident_20260513.md / .claude/memory/lessons_active.md (L-179/L-182/L-183) / .claude/auditor_template.md |
| 遡及保存メモ | 2026-05-14 に `.claude/instructions/` 構造化ルール適用時に遡及保存。原本は 2026-05-13 セッションでチャット投げ。Phase 1 は本指示書に従い 2026-05-14 完了 (16 モデル / 141 分 / leak フリー / bit-exact 再現性 ✅)。成果物: [results/priority_rebuild/ml_phase1/](../../results/priority_rebuild/ml_phase1/)。完了報告: [2026-05-13_phase1_lgbm_completion.md](2026-05-13_phase1_lgbm_completion.md) |

## 本文 (CC への指示)

【タスク】Phase 1 LightGBM × 16 ラベル 学習 (leak フリー再構築・監査反映版)
(Web Claudeレビュー済 + 監査エージェント審査済・まこさんGO済 2026-05-13)

## 着手前必読 (省略禁止・L-179/L-180/L-181)

以下のファイルを順に view した後、Step 0-1 で各ファイルから指定箇所を引用する。
「読んだ」報告のみは不可。引用なしの場合 STOP。

1. WORKFLOW.md (全文)
2. CLAUDE.md (全文)
3. .claude/rules/exchange_spec.md (全文)
4. .claude/rules/phase_compliance_checklist.md (Phase 1 セクション + §未確定項目)
5. ~/.claude/projects/.../memory/feedback_ml_leak_mandatory_check.md
6. results/priority_rebuild/leak_incident_20260513.md (全文)
7. .claude/memory/lessons_active.md L-179/L-182/L-183
8. .claude/auditor_template.md 観点⑥⑦ (今回監査の根拠)

## Step 0: 着手前準備 (6サブステップ・全件 PASS で Step A 着手可)

### Step 0-1. 必読ファイル引用 (読んだフリ防止)

以下を CC が逐次貼り付け:

a. exchange_spec.md より Maker fee 確定値の行を引用
   期待: "Maker fee | 0.014% (0.00014)"
b. phase_compliance_checklist.md Phase 1 セクション (1.1〜1.5) を全文貼り付け
c. WORKFLOW.md §🔴次のタスク「次セッション最初にやること」を全文貼り付け
d. leak_incident_20260513.md §修正完了 / §4種grep結果 を全文貼り付け
e. lessons_active.md (or memory feedback_ml_leak_mandatory_check.md) L-179 の
   「4点チェック」項目を全文貼り付け

各引用が「期待値」と一致しない/省略されている場合 → STOP

### Step 0-2. 入力ファイル整合性 verify (Phase 0 出力が leak修正後と確認)

```bash
echo "=====Step 0-2 START $(date) ====="
sha256sum results/priority_rebuild/labels_mfe_mae_train_2021_2024.parquet
ls -la results/priority_rebuild/labels_mfe_mae_train_2021_2024.parquet
python3 -c "
import pandas as pd
df = pd.read_parquet('results/priority_rebuild/labels_mfe_mae_train_2021_2024.parquet')
print(f'rows={len(df)}')
print(f'cols={len(df.columns)}')
ts_col = 'timestamp' if 'timestamp' in df.columns else df.columns[0]
print(f'period min={df[ts_col].min()} max={df[ts_col].max()}')
"
```

期待値 (WORKFLOW.md §Phase 0達成サマリーと突合):
- 行数: 394,753
- 列数: 1,449 (1,432 features + meta)
- 期間 min: 2021-04-01 07:55:00
- 期間 max: 2024-12-31 23:55:00

1件でも不一致 → STOP (古いleak由来ファイル混入の可能性)

archive/leak_invalid_20260513/ に旧版が退避済か確認:
```bash
ls archive/leak_invalid_20260513/labels_mfe_mae_*.parquet 2>/dev/null || echo "no_archive_or_not_yet_moved"
```

### Step 0-3. scan_leak.py 事前実行 (4種grep alert=0 確認)

懸念6 (fractal 過剰適応) 対策:

```bash
echo "=====Step 0-3 START $(date) ====="
python3 scripts/priority_rebuild/scan_leak.py 2>&1 | tee logs/scan_leak_step0_$(date +%Y%m%d_%H%M%S).log
```

期待: shift_neg / center_true / future_forward / j_plus_n の 4 alert すべて 0 件
1件でも alert > 0 → STOP (Phase 0 完了報告と不整合)

scan_leak.py がリポジトリにない場合、以下を実行:
```bash
echo "=== A. shift(-N) negative shift ==="
grep -rn "\.shift(-" scripts/priority_rebuild/ scripts/regime/ 2>/dev/null
echo "=== B. center=True ==="
grep -rn "center=True\|center = True" scripts/priority_rebuild/ scripts/regime/ 2>/dev/null
echo "=== C. j+1/j+2/i+1/i+2 ==="
grep -rn "j+1\|j+2\|i+1\|i+2" scripts/regime/structure_features.py scripts/regime/shape_features.py 2>/dev/null
echo "=== D. future/forward/lead/next_ ==="
grep -rn "future\|forward\|^lead\|next_" scripts/priority_rebuild/ scripts/regime/ 2>/dev/null | grep -v "from __future__"
```

A/B が 0 件・C は fractal 4箇所のみ (leak_incident_20260513.md §4種grep結果と一致)・D は 0 件
1件でも追加ヒット → STOP

### Step 0-4. phase_compliance_checklist.md §未確定項目 と §5.4 更新 (懸念5)

現状: §未確定項目テーブルに「Maker fee 実値 | 暫定 0.0002」が残存・§5.4 にも暫定記述
更新内容:

- §未確定項目テーブル: Maker fee 行を削除
  (理由: exchange_spec.md L7 で 0.00014 確定済・2026-05-13)
- §5.4: "Maker fee = **0.0002 暫定**" を
  "Maker fee = **0.00014 (適用) / 0.0002 (標準・剥落復帰時)** ・出典 exchange_spec.md L7" に置換
- §5.6: 削除 (§5.4 に集約)

更新後 grep verify:
```bash
grep -n "0.0002\|Maker fee" .claude/rules/phase_compliance_checklist.md
```
期待: "0.0002" は標準値の括弧内のみに残存

### Step 0-5. ラベル分布事前算出 (懸念9: RMSE 基準のラベルスケール依存解消)

16ラベルそれぞれの mean/std/min/max/p50/p90/p99 を Phase 0 出力から算出:

```bash
echo "=====Step 0-5 START $(date) ====="
python3 -c "
import pandas as pd
import json
df = pd.read_parquet('results/priority_rebuild/labels_mfe_mae_train_2021_2024.parquet')
label_cols = [c for c in df.columns if any(k in c for k in ['K12','K24','K48','K96']) and ('mfe' in c.lower() or 'mae' in c.lower())]
stats = {}
for c in label_cols:
    s = df[c].dropna()
    stats[c] = {
        'mean': float(s.mean()), 'std': float(s.std()),
        'min': float(s.min()), 'max': float(s.max()),
        'p50': float(s.quantile(0.50)), 'p90': float(s.quantile(0.90)),
        'p99': float(s.quantile(0.99)), 'n_valid': int(s.shape[0]),
        'rmse_threshold_warn': float(s.std() * 0.5),
        'rmse_threshold_critical': float(s.std() * 1.0)
    }
print(json.dumps(stats, indent=2))
with open('results/priority_rebuild/ml_phase1/label_distribution_stats.json','w') as f:
    json.dump(stats, f, indent=2)
"
```

成果物: results/priority_rebuild/ml_phase1/label_distribution_stats.json
チャット出力: 16ラベル × 8統計値の表 (mean/std/p50/p90/p99/n_valid/rmse_threshold_warn/critical)

### Step 0-6. dry-run (leak pause機能性 verify・懸念8)

並行タスク1 (1ラベル目で自動停止) の機能を、本番起動前に verify:

```bash
echo "=====Step 0-6 START $(date) ====="
# ALLOW_PHASE1_CONTINUE 未設定 (=空) で起動 → 1ラベル目完了で自動停止することを確認
python3 scripts/priority_rebuild/run_lgbm_phase1.py 2>&1 | tee logs/phase1_dry_run_$(date +%Y%m%d_%H%M%S).log &
PHASE1_PID=$!
sleep 600  # 10分待つ (1ラベル目の学習所要 ~3分想定)
# 停止状態確認
if kill -0 $PHASE1_PID 2>/dev/null; then
    echo "STILL RUNNING after 10min - leak pause may not work"
    kill $PHASE1_PID
    exit 1
fi
ls -la results/priority_rebuild/ml_phase1/feature_importance_top20.csv
# 16モデル全部できていたら leak pause 機能していない
N_MODELS=$(ls results/priority_rebuild/ml_phase1/lgbm_*.txt 2>/dev/null | wc -l)
if [ $N_MODELS -gt 1 ]; then
    echo "ERROR: $N_MODELS models created (expected 1) - leak pause NOT working"
    exit 1
fi
echo "leak pause OK: 1 model + 1 feature_importance_top20.csv created"
```

このdry-runの出力が Step A の出力を兼ねる。dry-run 後に追加実行は不要。
(= Step 0-6 完了時点で Step A の出力が出揃う)

dry-run 不合格 → STOP (run_lgbm_phase1.py の leak pause 実装を要修正)

## Step 1: 学習設計・確定前提 (引用・再認識ズレ防止)

### Phase 0 完了状態 (Step 0-2 で実測 verify 済み・引用)
- labels_mfe_mae_train_2021_2024.parquet: 394,753 行
- 期間: 2021-04-01 07:55 〜 2024-12-31 23:55
- 指標列: 1,432 (fractal +2 シフト修正済)

### Phase 1 学習設計 (phase_compliance_checklist 1.1〜1.5 準拠)
- ラベル: 16 = K12/K24/K48/K96 × LONG/SHORT × MFE/MAE
- 時系列 valid split: 末尾 10% (chronological・shuffle禁止)
- 入力: labels_mfe_mae_train_2021_2024.parquet
- 出力先: results/priority_rebuild/ml_phase1/

### LightGBM ハイパラ (再現性確保・懸念10対応)

```python
params = {
    'objective': 'regression',
    'metric': 'rmse',
    'learning_rate': 0.02,
    'min_data_in_leaf': 100,
    'feature_fraction': 0.7,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'reg_lambda': 0.1,
    'n_estimators': 5000,
    'random_state': 42,
    'bagging_seed': 42,           # 懸念10追加
    'data_random_seed': 42,       # 懸念10追加
    'feature_fraction_seed': 42,  # 懸念10追加
    'num_threads': 1,             # 懸念10追加 (再現性最優先・速度より優先)
    # early_stopping=50 はコールバック側
}
```

⚠️ num_threads=1 で学習速度は数倍遅くなる。所要時間が長くても再現性優先。
速度を優先したい場合、num_threads=N (N≥2) で実行し
「同じコマンド2回実行で bit-exact 一致しない可能性」を許容する旨を完了報告に明記。

## Step 0 leak 4 点チェック (L-179 必須・物理化)

| # | 項目 | 状態 |
|---|---|---|
| ① | 特徴量 grep 静的検査 (4種) | Step 0-3 で実施・alert=0 確認済 |
| ② | データ流入経路 verify (j≤i-2) | Phase 0 結果引用 (leak_incident §修正完了) |
| ③ | timestamp range 分離 | Step 0-2 で実測 verify 済 |
| ④ | 1ラベル目完了 feature_importance review (拡張版下記) | **Step A レビューで実施** |

## Step A. 1ラベル目学習 (Step 0-6 dry-run が兼ねる)

Step 0-6 完了時点で以下の出力が揃っている前提:
- results/priority_rebuild/ml_phase1/lgbm_<label1>.txt (1モデル)
- results/priority_rebuild/ml_phase1/feature_importance_top20.csv
- logs/phase1_dry_run_*.log

### Step A 完了後のチャット出力 (物理証跡 8 点・必須全件)

#### 証跡1. 入力ファイル整合性 (Step 0-2 引用)
- sha256sum / バイト数 / 行数 / 列数 / 期間 min/max
- WORKFLOW.md §Phase 0達成サマリーとの一致 確認

#### 証跡2. 学習プロセス内部
- 1ラベル目のラベル名 (例: K12_LONG_MFE)
- LightGBM iteration log: results/priority_rebuild/ml_phase1/lgbm_<label>_iteration_log.csv
  形式: iter, train_rmse, valid_rmse
- best_iteration / best_score
- early_stopping=50 発火確認: best_iteration < n_estimators(5000) ならOK
- 訓練所要時間 (秒)

#### 証跡3. 出力ファイル
- lgbm_<label>.txt: sha256sum / バイト数 / 「1KB未満なら異常停止」
- feature_importance_top20.csv: sha256sum / バイト数 / 全20行貼り付け
- 0バイト or <1KB → 即停止

#### 証跡4. 第三者再読み出し検証 (懸念1対応・joblib→Booster修正)

```bash
python3 -c "
import lightgbm as lgb
m = lgb.Booster(model_file='results/priority_rebuild/ml_phase1/lgbm_<label>.txt')
imp = m.feature_importance(importance_type='gain')
names = m.feature_name()
import pandas as pd
df = pd.DataFrame({'feature': names, 'importance': imp}).sort_values('importance', ascending=False).head(20)
print(df.to_csv(index=False))
"
```

出力値と feature_importance_top20.csv の値が **完全一致** することを confirm
(順序・数値・列名すべて bit-exact)

#### 証跡5. predictions_train_2021_2024.parquet 保存確認 (懸念2対応)

```bash
ls -la results/priority_rebuild/ml_phase1/predictions_train_2021_2024.parquet 2>/dev/null
python3 -c "
import pandas as pd
df = pd.read_parquet('results/priority_rebuild/ml_phase1/predictions_train_2021_2024.parquet')
print(f'rows={len(df)} cols={len(df.columns)}')
print(f'columns: {df.columns.tolist()}')
"
```

期待: 行数 394,753 (Phase 4-a 入力として整合)
ファイル存在しない場合: run_lgbm_phase1.py のコード側で .to_parquet 実装漏れ → STOP

ただし Step A (1ラベル目のみ) では 1 列分のみ書かれている可能性あり。Step B 完了時に 16 列で再 verify。

#### 証跡6. データ sanity
- 入力 parquet 各列 null率 上位10件
- 1%超は警告・5%超は停止

#### 証跡7. stderr / Python warning 全件 (懸念3対応)
- 実行コマンドは `python3 ... 2>&1 | tee log.txt` で stderr 含む
- warnings は logs/phase1_dry_run_*.log の "Warning" / "WARNING" grep 結果
- 0件の場合 "no warnings" 明示

#### 証跡8. 同コマンド bit-exact 再現性確認 (懸念10対応)

Step 0-6 dry-run を **もう一度** 同じパラメータで実行し、iteration_log.csv が bit-exact 一致するか確認:

```bash
# 1回目 (Step 0-6 で実行済)
sha256sum results/priority_rebuild/ml_phase1/lgbm_<label>_iteration_log.csv > /tmp/sha_run1.txt

# 2回目 (Step A 検証用)
mv results/priority_rebuild/ml_phase1 results/priority_rebuild/ml_phase1_run1
python3 scripts/priority_rebuild/run_lgbm_phase1.py 2>&1 | tee logs/phase1_run2_$(date +%Y%m%d_%H%M%S).log
sha256sum results/priority_rebuild/ml_phase1/lgbm_<label>_iteration_log.csv > /tmp/sha_run2.txt

# 一致確認
diff /tmp/sha_run1.txt /tmp/sha_run2.txt && echo "bit-exact OK" || echo "REPRODUCIBILITY FAIL"
```

不一致時: num_threads=1 でも乱数源が残っていることを示す → STOP・seed 追加調査

(計算リソース節約のため、num_threads=1 でなく N>1 で実行する場合は本証跡8をスキップ可。
ただし「bit-exact 再現性は不保証」と完了報告に明記)

### Step A レビュー基準 (Web Claude判定 → まこさん最終GO)

#### (a) ブラックリスト top50 不在 (懸念6: 過剰適応対策)
top50 で grep:
- dist_to_fib_v2_*
- resistance_distance_*
- support_distance_*
- nearest_level_*

1個でも含まれていたら **即停止** + leak 残存疑い

#### (b) RMSE 動的閾値 (懸念9: ラベルスケール対応)

Step 0-5 で算出した label_distribution_stats.json から該当ラベルの std を取得:
- train RMSE < std × 0.1 → 警告 (過剰適合疑い)
- valid RMSE / train RMSE > 3.0 → 警告 (過学習)
- valid RMSE > std × 1.5 → 警告 (学習が進んでいない)

警告ヒット時 → 停止して Web Claude レビュー

#### (c) top10 意味解説 (人間レビュー対応)
top10 の各 feature について
"なぜこの指標が高 importance か" を 1 文で説明。
腑に落ちない説明・物理的に説明不能な特徴量があれば停止。

## Step B. 残り 15 ラベル学習 (Step A レビュー clean + まこさん GO 後)

```bash
echo "=====🚀 Step B START $(date) ====="
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api
ALLOW_PHASE1_CONTINUE=1 python3 scripts/priority_rebuild/run_lgbm_phase1.py 2>&1 | tee logs/phase1_step_b_$(date +%Y%m%d_%H%M%S).log
```

完了後の出力:
- 16 LightGBM model: lgbm_K{12,24,48,96}_{LONG,SHORT}_{MFE,MAE}.txt
- predictions_train_2021_2024.parquet (16列+ meta)
- feature_importance_top20_<label>.csv × 16
- training_summary.csv (16ラベル × {train_rmse, valid_rmse, best_iter, time})

### Step B 完了後の異常検査 (懸念11対応・基準明文化)

| 検査項目 | 異常基準 | 異常時アクション |
|---|---|---|
| MFE/MAE の valid RMSE 差 | 同K窓・同side で 5倍以上 | 報告して Phase 2 着手前にレビュー |
| LONG/SHORT の valid RMSE 比 | 同K窓・同label種 で 3倍以上 | 同上 |
| 個別ラベル train RMSE | label_distribution_stats.json の std × 0.1 未満 | 即停止 |
| 個別ラベル valid/train 乖離 | 3.0倍以上 | 即停止 |
| best_iteration | n_estimators=5000 到達 (= early_stopping 未発火) | 報告・要レビュー |

検査結果を表形式で提示:

| K | side | label | train_rmse | valid_rmse | 乖離率 | std | 判定 |
|---|------|-------|-----------|-----------|--------|-----|------|
| 12 | LONG | MFE | XX | XX | XX% | XX | ✅/⚠️/❌ |
| 12 | LONG | MAE | ... | ... | ... | ... | ... |
| ... (全16ラベル) |

⚠️ or ❌ が1件でもあれば Phase 2 着手前に Web Claude レビュー必須

## 完了報告必須証跡 5 点 (WORKFLOW.md 規定)

1. **コード総点検 grep 結果** (4種 + ブラックリスト4種 + 暫定値0.0002 + n_jobs=-1/num_threads + random_state grep)
2. **数値の二重提示** (16モデル training_summary.csv 引用 + チャットサマリー表)
3. **成果物ファイル実体**
   - 16 LightGBM model ファイル一覧 (各 sha256/バイト数)
   - feature_importance_top20_<label>.csv × 16
   - predictions_train_2021_2024.parquet (sha256/行数/列数)
   - label_distribution_stats.json
   - training_summary.csv
   - 全ログファイル (Step 0-6 dry-run / Step A bit-exact / Step B)
4. **実行ログ**
   - Step 0-6 開始/終了/所要/終了コード
   - Step A 検証 (bit-exact 再現性) 開始/終了/所要
   - Step B 開始/終了/所要/終了コード
   - lightgbm / sklearn / numpy / pandas version (phase_compliance 1.5)
5. **絞り込み示唆語彙 自己 grep 結果** (全件 no matches 含む)
   - 対象語彙: 「採用候補」「効く/効かない」「重要」「優先」「不要」「切れる」「残せる」「除外して良い」「使える」「意味がある/ない」

## Phase 5 以降への申し送り (リマインダー・今回着手しない)

- POS_SIZE_BTC = 0.12 は **合計上限** (1ポジ上限ではない)
- cap=N で 1pos = 0.12/N BTC (cap=5 → 0.024 / cap=20 → 0.006)
- 最小注文 0.0001 BTC (cap≤1200 までクリア)
- Funding 8h 境界 UTC 0/8/16時 (exchange_spec.md)
- Maker 0.00014 / Taker 0.00042 適用値 (確定済・exchange_spec.md・暫定値 0.0002 ハードコード残存があれば置換要)

## 完了後の状態

- phase_compliance_checklist.md §未確定項目から Maker fee 行が消えている
- §5.4 が 0.00014 (適用) に更新済
- 16 LightGBM モデル学習完了 (leak フリー保証・top50ブラックリスト不在)
- predictions_train_2021_2024.parquet 出力 (Phase 4-a 入力・16列+meta)
- label_distribution_stats.json 出力 (Phase 2/3 の動的閾値基準)
- 全モデル training_summary.csv で異常検査済
- bit-exact 再現性確認済 (num_threads=1 採用の場合)
- Phase 2 (精度判定・仮テスト 2025 月次 $500 以上か) 着手待ち
