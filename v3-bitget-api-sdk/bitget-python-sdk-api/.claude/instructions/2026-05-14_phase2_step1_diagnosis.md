# 案 E Step 1: Phase 2 結果の構造的原因 短期診断 実行指示書

| 項目 | 値 |
|---|---|
| 発行日 | 2026-05-14 |
| 作成者 | Web Claude (PMエージェント) |
| 承認 | まこさん |
| 関連 commit | 0ffd326 (Phase 2 精度判定 完了報告) / 8ddad27 (Phase 2 実行指示書) |
| 監査経由 | あり (監査エージェント審査・net_quality_24combinations.csv 直接精査結果反映) |
| 関連必読 | WORKFLOW.md §🔴次のタスク (改訂22) / cc_ml_design_spec.md §1.6 / §5 Phase 2 (commit b14be88) / 2026-05-14_phase2_execute_completion.md (Phase 2 完了報告) / results/priority_rebuild/ml_phase2/net_quality_24combinations.csv / mfe_mae_ratio_24combinations.csv / rmse_sanity_16labels.csv / handoff_to_web_claude_v3_phase1_phase3a.md §2.3 §2.4 |
| 目的 | 新規実装ゼロ・既存 CSV から 3 項目 4-6h で解明 → Phase 3 着手内容決定 |

## 本文 (CC への指示)

【タスク】案 E Step 1: Phase 2 結果の構造的原因 短期診断 (4-6時間・既存CSV分析)
(Web Claudeレビュー済 + 監査エージェント審査済・まこさんGO済 2026-05-14)

## 構造化ルール準拠

### 指示書保存ルール
- 保存先: `.claude/instructions/2026-05-14_phase2_step1_diagnosis.md`
- 完了報告: `.claude/instructions/2026-05-14_phase2_step1_diagnosis_completion.md`
- 1ファイル=1commit (指示書発行 = 1 commit)

### 着手前の必須対応
本指示書を上記パスに保存し commit してから実行開始。

## 着手前必読 (省略禁止・L-179/L-180/L-181)

1. WORKFLOW.md §🔴次のタスク (改訂22)
2. cc_ml_design_spec.md §1.6 / §5 Phase 2 (commit b14be88)
3. .claude/instructions/2026-05-14_phase2_execute_completion.md (Phase 2 完了報告)
4. results/priority_rebuild/ml_phase2/net_quality_24combinations.csv (CSV 本体)
5. results/priority_rebuild/ml_phase2/mfe_mae_ratio_24combinations.csv
6. results/priority_rebuild/ml_phase2/rmse_sanity_16labels.csv
7. handoff_to_web_claude_v3_phase1_phase3a.md §2.3 §2.4 (旧 leak 実績)

## 背景 (監査エージェント審査結果)

Phase 2 で 1指標 FAIL (+8.72pp / +10pp 閾値・1.28pp 不足)。
監査エージェントが net_quality_24combinations.csv 直接精査して以下発見:

1. **K12/K24 LONG で MFE_lift マイナス** = ML が動きの小さい足を選んでいる
   - K12 LONG q90: MFE_lift=-17.78% / MAE_lift=-23.86%
   - K12 LONG q95: MFE_lift=-17.23% / MAE_lift=-24.33%
   - K12 LONG q99: MFE_lift=-9.99% / MAE_lift=-26.05%
   → CC も Web Claude も気付かなかった構造的事実

2. -71pp フレーミング修正必要 (q99同士なら -60pp / 24組合せ加重 vs q99 単独 で apples-to-oranges)

3. CC 案A の「+19pp 改善」前提崩壊 (新 Phase 1 は既に旧 Phase 3-a 相当のハイパラ)

→ 案 A 直行はリスク大。案 E (Step 1 短期診断 → 計画的 Phase 3) を採用。

## Step 1 の目的

新規実装ゼロ・既存 CSV から以下 3 項目を 4-6 時間で解明:

1. K96 SHORT q99 逆行 1,660件 の時期分布
2. K12/K24 LONG MFE_lift マイナスの mechanism
3. q90/q95/q99 の発火 timestamp 重複率

Step 1 結果で「Phase 3 で何を調整するか」「q別取扱を spec 改訂するか」「no-trade フィルタを Phase 4-b に追加するか」を決める。

## Step 0: 着手前準備

### Step 0-1. 必読ファイル引用 (読んだフリ防止)

a. net_quality_24combinations.csv の K12 LONG q99 行を引用 (MFE_lift_pct / MAE_lift_pct / n_fire 含む)
b. mfe_mae_ratio_24combinations.csv の K96 SHORT q99 行を引用
c. Phase 2 完了報告 §「補足分析」全文貼り付け
d. 監査結果懸念1 (MFE_lift マイナスの数値) 引用

各引用が「期待値」と一致しない/省略されている場合 → STOP

### Step 0-2. 入力ファイル整合性 verify

```bash
echo "=====Step 0-2 START $(date) ====="
sha256sum results/priority_rebuild/ml_phase2/net_quality_24combinations.csv
sha256sum results/priority_rebuild/ml_phase2/mfe_mae_ratio_24combinations.csv
sha256sum results/priority_rebuild/ml_phase2/rmse_sanity_16labels.csv
sha256sum results/priority_rebuild/ml_phase1/predictions_test2025.parquet
sha256sum results/priority_rebuild/labels_mfe_mae_test_2025.parquet
ls -la results/priority_rebuild/ml_phase2/*.csv
```

期待: Phase 2 完了報告と同 sha256 (改竄なし)

## Step 1-1: K96 SHORT q99 逆行 1,660件の時期分布分析

### 目的
旧 leak と完全同値 (MFE/MAE=0.986) で構造的逆行。これが特定市場イベント (暴騰直前等) に集中しているか、年間通じて分散しているかを判定。

集中 → Phase 4-a で SHORT 長期 cluster を分離・期間フィルタ追加で回避可能
分散 → 構造的問題・Phase 4-b で no-trade cluster として除外

### 分析手順
```python
import pandas as pd

# K96 SHORT q99 の発火 timestamp を特定
preds = pd.read_parquet('results/priority_rebuild/ml_phase1/predictions_test2025.parquet')
labels = pd.read_parquet('results/priority_rebuild/labels_mfe_mae_test_2025.parquet')

# 発火条件: pred_SHORT_MFE_K96 / pred_SHORT_MAE_K96 ≥ q99 閾値
threshold = (preds['pred_SHORT_MFE_K96'] / preds['pred_SHORT_MAE_K96']).quantile(0.99)
fired = preds[(preds['pred_SHORT_MFE_K96'] / preds['pred_SHORT_MAE_K96']) >= threshold]

# 月別分布
ts_col = 'timestamp' if 'timestamp' in fired.columns else fired.columns[0]
fired['month'] = pd.to_datetime(fired[ts_col]).dt.to_period('M')
month_dist = fired.groupby('month').size()
print(month_dist)

# 月別の平均実 MFE/MAE
month_perf = fired.groupby('month').apply(lambda g: pd.Series({
    'n': len(g),
    'real_MFE_mean': labels.loc[g.index, 'SHORT_MFE_K96'].mean(),
    'real_MAE_mean': labels.loc[g.index, 'SHORT_MAE_K96'].mean(),
    'MFE_MAE_ratio': labels.loc[g.index, 'SHORT_MFE_K96'].mean() / labels.loc[g.index, 'SHORT_MAE_K96'].mean()
}))
print(month_perf)
```

### 出力
- results/priority_rebuild/ml_phase2/step1_1_k96_short_q99_monthly.csv
- チャット出力: 月別 n + MFE/MAE ratio 表

### 判定基準
- 1ヶ月集中 (>50%) → 特定イベント起因 → Phase 4-a 期間フィルタ案
- 3-4ヶ月集中 → 暴騰局面集中 → market regime 検知必要
- 12ヶ月均等分散 → 構造的問題 → no-trade フィルタ案

## Step 1-2: K12/K24 LONG MFE_lift マイナスの mechanism 分析

### 目的
ML が「動きの小さい LONG 足」を選んでいる原因を特定。feature_importance top 列の挙動と MAE_lift 急減との関係を見る。

### 分析手順
```python
import pandas as pd
import json

# K12 LONG q99 発火足の特徴量分布を確認
preds = pd.read_parquet('results/priority_rebuild/ml_phase1/predictions_test2025.parquet')
labels = pd.read_parquet('results/priority_rebuild/labels_mfe_mae_test_2025.parquet')

# 発火 vs 非発火の特徴量比較 (top10 importance 列)
imp_top = pd.read_csv('results/priority_rebuild/ml_phase1/feature_importance_full_rank_LONG_MFE_K12.csv').head(10)
print("Top 10 importance features for K12 LONG MFE:")
print(imp_top)

# 各 top 列で「発火足の平均」vs「全足の平均」を比較
threshold = (preds['pred_LONG_MFE_K12'] / preds['pred_LONG_MAE_K12']).quantile(0.99)
fired_mask = (preds['pred_LONG_MFE_K12'] / preds['pred_LONG_MAE_K12']) >= threshold

# (test_2025 parquet に特徴量列が含まれている前提)
# 含まれていない場合は build_labels.py の出力から再取得
test_features = pd.read_parquet('results/priority_rebuild/labels_mfe_mae_test_2025.parquet')

for feat in imp_top['feature'].head(5):
    if feat in test_features.columns:
        fired_mean = test_features.loc[fired_mask, feat].mean()
        all_mean = test_features[feat].mean()
        lift_pct = (fired_mean - all_mean) / all_mean * 100
        print(f"{feat}: fired_mean={fired_mean:.4f} all_mean={all_mean:.4f} lift={lift_pct:.2f}%")
```

### 観点
- top 重要度の指標が volatility 系 (ATR / BB幅) なら → ML は「低ボラ足を高評価」している可能性
- volume 系なら → 「低出来高足」を選んでいる
- momentum 系なら → 「停滞足」を選んでいる
- いずれにせよ MFE 自体は小さくなる構造

### 出力
- results/priority_rebuild/ml_phase2/step1_2_k12_long_mechanism.csv
- チャット出力: top5 importance 列の発火 vs 全体 lift% 表 + 仮説 (どのカテゴリの指標が原因か)

## Step 1-3: q90/q95/q99 発火 timestamp 重複率

### 目的
q99 ⊂ q95 ⊂ q90 (完全包含) か、別物混在 (独立シグナル) かを判定。
包含なら q90 = q99 + 中品質 + 低品質 の 3 層構造 → q別取扱に意味あり
独立混在なら → 案B (q99 のみ採用) は別の足を捨てることになる

### 分析手順
```python
# 同一 K 窓・同一 side で q90/q95/q99 発火 timestamp の集合演算
for K in [12, 24, 48, 96]:
    for side in ['LONG', 'SHORT']:
        ratio = preds[f'pred_{side}_MFE_K{K}'] / preds[f'pred_{side}_MAE_K{K}']
        q90_thr = ratio.quantile(0.90)
        q95_thr = ratio.quantile(0.95)
        q99_thr = ratio.quantile(0.99)

        q90_set = set(preds[ratio >= q90_thr].index)
        q95_set = set(preds[ratio >= q95_thr].index)
        q99_set = set(preds[ratio >= q99_thr].index)

        q99_in_q95 = len(q99_set & q95_set) / len(q99_set) * 100
        q99_in_q90 = len(q99_set & q90_set) / len(q99_set) * 100
        q95_in_q90 = len(q95_set & q90_set) / len(q95_set) * 100

        print(f"K{K} {side}: q99⊂q95={q99_in_q95:.1f}% / q99⊂q90={q99_in_q90:.1f}% / q95⊂q90={q95_in_q90:.1f}%")
```

### 出力
- results/priority_rebuild/ml_phase2/step1_3_q_overlap.csv
- チャット出力: 16ラベル × 3つの包含率 表

### 判定基準
- 全 100% (完全包含) → 案 B のq別取扱は単純な閾値選択
- 部分一致 (50-99%) → 案 B は別物の足を採用する判断・spec 改訂要
- 50% 未満 → q別取扱は独立シグナル混在 → 別 cluster 化が必要

## Step 2: 統合判定 + Phase 3 着手内容の提案

Step 1-1/1-2/1-3 結果から以下を CC が提案:

1. K96 SHORT q99 への対処 (期間フィルタ / no-trade / そのまま) と根拠
2. K12/K24 LONG MFE_lift マイナスへの対処 (Phase 3 K窓別ハイパラ / 用途限定 / 除外) と根拠
3. q別取扱の方針 (案B採用 / 加重平均維持 / q別 cluster 化) と根拠
4. Phase 3 で試す具体的ハイパラ変更点と各々の期待改善幅 (事前明示)

→ Web Claude + まこさんレビュー → Phase 3 着手指示書化

## 完了報告必須証跡 5 点

1. **コード総点検 grep 結果**
   - 分析スクリプトで「採用候補」「効く/効かない」等の絞り込み示唆語彙 no matches
2. **数値の二重提示**
   - Step 1-1/1-2/1-3 のチャットサマリー + 出典 CSV 引用
3. **成果物ファイル実体** (sha256 + 行数 + 更新時刻)
   - step1_1_k96_short_q99_monthly.csv
   - step1_2_k12_long_mechanism.csv
   - step1_3_q_overlap.csv
   - 分析ログ tee ファイル
4. **実行ログ**
   - 開始/終了/所要 (4-6時間想定)
   - Python warnings 全件
5. **絞り込み示唆語彙 自己 grep 結果**

## 完了後の状態

- Step 1 3項目分析完了
- Phase 3 着手内容の根拠つき提案が完成
- 完了報告 .claude/instructions/2026-05-14_phase2_step1_diagnosis_completion.md commit

## 次のステップ

Step 1 完了報告 → Web Claude が自分で CSV を view して検証 → まこさん最終 GO →
Phase 3 着手指示書 (or 別案切替) を発行
