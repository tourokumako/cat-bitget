# Phase 1 学習方法再設計指示書 v1 — Layer 配分逆転確定版 (6 案並列 + Walk-forward Purged K-Fold + DSR)

(起案者・CC・2026-05-22 / 宛先・CC = 実装担当兼務)
**版**: v1 (まこさん指摘「学習方法が悪い」最終反映・Layer 配分逆転 (B') 確定)
**前身**: learning_design_v4 v5 §4 Layer 1 (Layer 配分逆転) + cc_ml_design_spec §1.5.1 (Phase 1 合格基準 5 指標) + ナレッジベース v3 §D ML for Trading

## 構造化ルール準拠

- 保存先: `.claude/instructions/2026-05-22_phase1_layer_inversion_instruction.md`
- 完了報告: `.claude/instructions/2026-05-22_phase1_layer_inversion_completion.md`
- **本指示書を上記パスに保存し commit すること** (WORKFLOW.md §指示書のファイル保管義務)

> **full フォーマット (約 450 行)**: 6 案並列実装 + Walk-forward CV + DSR 採用 + Layer 3 投入条件厳格化を含むため (cc_role §1.5.5 + L-198 整合)。

## Layer 配分逆転の背景

handoff v20 §0.26 #5 で「Entry 学習駄目 → 特徴量拡張」と CC が翻訳した問題に対し、handoff v19 §0.14 でまこさんが「学習方法が悪い」と指摘。CC「撤回・Layer 配分逆転」で合意済だが、現行 learning_design_v4 V4.1 (3 案 RMSE/Binary/Multiclass 並列) は **目的関数 3 案並列追加** であって **学習方法そのものの逆転** ではなかった。

2026-05-22 まこさん再指摘で根本問題判明:
- Triple Barrier + Meta-Labeling + Walk-forward CV が依然 Layer 3 に配置
- entropy lift 6.04% (Phase 1-c smoke・AFML Ch.3 推奨閾値 < 10% 投入域) の根本解決保証なし

→ **本指示書で真の Layer 配分逆転確定**: Triple Barrier + Meta-Labeling + Walk-forward CV + Ranking LambdaRank を Layer 3 → Layer 1 前倒し・**6 案並列実装**。

## 読了ゲート通過証跡 (L-200 機械的証跡)

- handoff v21 (301 行) / WORKFLOW.md (500 行) / **learning_design_v4 v5** (約 360 行・本セッションで Layer 配分逆転反映) / phase_flow_v4_with_recovery.md (977 行) / **cc_ml_design_spec.md §1.5.1 追加版** (約 410 行) / cc_role.md (336 行) / false_positive_incident_policy.md (225 行) / phase_compliance_checklist.md (222 行) / auditor_template.md (520 行) / 10_indicator_families.md (174 行) / lessons_active.md (1964 行・直近 300 行重点) ✅
- **technical_analysis_knowledge_base.md v3 (1691 行・特に §D ML for Trading + §I 閾値設計論)** ✅
- **Phase 0 改修指示書 v3.1** (本セッションで作成・Triple Barrier ラベル 28 列同時生成) ✅

## 着手前必読 (省略禁止・L-179/L-180/L-181)

1. **`technical_analysis_knowledge_base.md` v3 §D ML for Trading** (Triple Barrier / Meta-Labeling / Fractional Diff / Sample Weights / CPCV / mlfinlab / Stefan Jansen)
2. **`learning_design_v4.md` v5 §4 Layer 1 (Layer 配分逆転)** (案 a/b/c/d/e/f + Walk-forward + 合格基準 5 指標 + Layer 3 投入条件)
3. **`cc_ml_design_spec.md` §1.5.1** (Phase 1 合格基準 5 指標数値)
4. **Phase 0 改修指示書 v3.1** (Triple Barrier ラベル生成仕様 + 56 ラベル列 parquet schema)
5. handoff v19 §0.14 Entry 学習問題 5 件 + handoff v20 §0.26 CC 同型バイアス
6. cc_role.md §1.4 (CC 同型バイアス警告) + §1.7 (手動 Priority スタートライン)
7. false_positive_incident_policy.md §0-1 / §0-2 / §2 類型 A〜H / §5 関所 A〜G
8. ~/.claude/projects/.../memory/feedback_ml_leak_mandatory_check.md (L-179)

## Step 0-1: 必読ファイル引用 (読んだフリ防止)

着手前に以下をチャットに出力:

a. **ナレッジベース v3 §D.1 Triple Barrier Method 全文引用**
b. **ナレッジベース v3 §D.2 Meta-Labeling 全文引用**
c. **ナレッジベース v3 §D.5 CPCV (Purged K-Fold) 全文引用**
d. **learning_design_v4 v5 §4 「Layer 1 (Layer 配分逆転)」全文引用**
e. **cc_ml_design_spec §1.5.1 「Phase 1 合格基準 5 指標」全文引用**
f. Phase 0 改修指示書 v3.1 §3 ラベル定義 全文引用

各引用が省略 / 部分 view → STOP (false_positive §2 類型 G)。

## Step 0-2: 前提タスク完了 verify

```bash
echo "=====Step 0-2 START $(date) ====="

# (1) Phase 0 改修 v3.1 完了 verify
ls -la results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet
python -c "
import pandas as pd
df = pd.read_parquet('results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet')
# 56 ラベル列 verify
mfe_mae_cols = [c for c in df.columns if 'MFE_pct' in c or 'MAE_pct' in c]
tb_cols = [c for c in df.columns if 'triple_barrier_label' in c or 'meta_label' in c]
print(f'MFE/MAE labels: {len(mfe_mae_cols)} (expected 28)')
print(f'Triple Barrier labels: {len(tb_cols)} (expected 28)')
print(f'Total labels: {len(mfe_mae_cols) + len(tb_cols)} (expected 56)')
print(f'Total columns: {len(df.columns)} (expected ~2316-3016)')
"

# (2) mlfinlab パッケージ verify
python -c "
import mlfinlab
from mlfinlab.cross_validation import PurgedKFold
from mlfinlab.backtest_statistics import DSR
print(f'mlfinlab version: {mlfinlab.__version__}')
print('PurgedKFold + DSR import OK')
"

# (3) Phase -1 blacklist 48 列 verify (Phase 1 学習で drop 義務)
python -c "
BLACKLIST_FAMILIES = ['sma_20', 'sma_50', 'ichimoku_kijun', 'ichimoku_tenkan',
                       'macd_line', 'macd_signal', 'macd_hist', 'macd_hist_change']
import pandas as pd
df = pd.read_parquet('results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet')
blacklist_cols = [c for c in df.columns if any(c.startswith(f + '__') for f in BLACKLIST_FAMILIES)]
print(f'Blacklist columns to drop: {len(blacklist_cols)} (expected 48)')
"
```

**期待**:
- 56 ラベル列存在 (28 MFE/MAE + 28 Triple Barrier/Meta)
- 総列数 約 2316-3016
- mlfinlab 1.6.0+ インストール済
- Blacklist 48 列存在 (Phase 1 で drop)

---

## §1 タスク目的・成果物

**Phase 1 で 6 案並列学習 + Walk-forward Purged K-Fold 5 fold + DSR 評価**を実施し、cc_ml_design_spec §1.5.1 合格基準 5 指標で判定。

### 成果物

| ファイル | 内容 |
|---|---|
| `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py` | 案 a (14 ラベル RMSE) |
| `scripts/priority_rebuild/run_lgbm_phase1_v5_case_b_binary.py` | 案 b (Entry Binary) |
| `scripts/priority_rebuild/run_lgbm_phase1_v5_case_c_multiclass.py` | 案 c (Direction Multiclass) |
| `scripts/priority_rebuild/run_lgbm_phase1_v5_case_d_ranking.py` | **案 d (Ranking LambdaRank・新規)** |
| `scripts/priority_rebuild/run_lgbm_phase1_v5_case_e_triple_barrier.py` | **案 e (Triple Barrier multiclass・新規)** |
| `scripts/priority_rebuild/run_lgbm_phase1_v5_case_f_meta_labeling.py` | **案 f (Meta-Labeling 2 段階・新規・案 e 完了後 sequential)** |
| `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` | **共通 Purged K-Fold 5 fold runner** |
| `results/priority_rebuild/ml_phase1_v5/case_{a-f}_fold_{0-4}/` | 各案 × 各 fold の予測結果 + feature_importance + 学習ログ |
| `results/priority_rebuild/ml_phase1_v5/phase1_v5_summary.json` | 6 案 × 5 fold × 5 指標の集計 + DSR + 合格判定 |

## §2 6 案の詳細仕様

### §2.1 案 a (14 ラベル独立 RMSE・流用ベースライン)

| 項目 | 内容 |
|---|---|
| 目的関数 | `objective='regression'` (RMSE) |
| ラベル | LONG_MFE_pct_K{6,12,24,48,96,144,288} (7 ラベル) + LONG_MAE_pct_K{...} (7 ラベル) = 14 ラベル独立 |
| モデル数 | 14 個 |
| Entry 判定 | LONG_MFE / LONG_MAE 比 ≥ 1.5 で買う (cc_ml_design_spec §2 整合) |
| 役割 | **比較ベースライン** (Phase 1-a 既存方式の特徴量拡張版で再学習) |

### §2.2 案 b (Entry Binary Classification)

| 項目 | 内容 |
|---|---|
| 目的関数 | `objective='binary'` (LightGBM Binary) |
| ラベル | K=12 後 MFE_pct > 0.5% かつ MAE_pct > -0.3% → 1 / それ以外 → 0 (新規派生) |
| モデル数 | 1 個 |
| ハイパラ | scale_pos_weight (class imbalance 対策・推定 50:1〜100:1) |
| Entry 判定 | Entry 確率 > 0.5 で買う |

### §2.3 案 c (Direction Multiclass)

| 項目 | 内容 |
|---|---|
| 目的関数 | `objective='multiclass'` (num_class=3) |
| ラベル | LONG_MFE > 0.5% → LONG (1) / SHORT_MFE > 0.5% → SHORT (2) / どちらも未満 → Flat (0) (新規派生) |
| モデル数 | 1 個 |
| Entry 判定 | LONG 確率 > 0.4 で買い / SHORT 確率 > 0.4 で売り |

### §2.4 案 d (Ranking LambdaRank・新規)

| 項目 | 内容 |
|---|---|
| 目的関数 | `objective='lambdarank'` (LightGBM Learning to Rank) |
| ラベル | MFE_pct ランキング (高い順 0〜100) を quantile bin (5 段階) |
| モデル数 | 1 個 |
| group 設定 | 1 日 (288 bar) ごとに group_id (LambdaRank の query group) |
| Entry 判定 | **予測強度上位 N% のみ実行** (N = 5/10/20 で grid search) |
| 根拠 | Stefan Jansen *Machine Learning for Algorithmic Trading* Ch.12-13 (Learning to Rank for trading) |

### §2.5 案 e (Triple Barrier multiclass・Layer 3 → Layer 1 前倒し)

| 項目 | 内容 |
|---|---|
| 目的関数 | `objective='multiclass'` (num_class=3) |
| ラベル | **`triple_barrier_label_LONG_K{K}` × K=7** (Phase 0 改修 v3.1 で生成済・+1/-1/0) + LONG/SHORT 統合学習 |
| モデル数 | K=7 期間別 7 個 (K 別に分離学習・特徴量重要度比較用) |
| Entry 判定 | TP first 確率 (+1) > 0.4 で買う |
| 根拠 | Lopez de Prado *AFML* Ch.3 + Hudson & Thames mlfinlab |

### §2.6 案 f (Meta-Labeling 2 段階・案 e 完了後 sequential)

| 項目 | 内容 |
|---|---|
| Primary model | 案 e (Triple Barrier multiclass) の結果を流用 |
| Secondary model | **「primary 予測の correctness」予測** = `meta_label_LONG_K{K}` (Phase 0 v3.1 で生成済・1/0) |
| 目的関数 | `objective='binary'` (Secondary model) |
| Entry 判定 | Primary が +1 予測 AND Secondary が「正解」予測 > 0.6 で買う |
| 期待効果 | **Precision 改善** + F1-score + Sharpe 向上 (Lopez de Prado AFML Ch.3) |

## §3 Walk-forward Purged K-Fold 5 fold 設計 (mlfinlab.cross_validation 経由)

```python
from mlfinlab.cross_validation import PurgedKFold

# train 2021-04〜2024-12 (約 380k 行) を 5 fold に分割
# - Purged: t1 (vertical barrier 時刻) が test fold に侵入する train サンプルを除外
# - Embargo: test fold 後の N bar (= 1% = 約 3800 bar) を train から除外
cv = PurgedKFold(n_splits=5, samples_info_sets=df['t1'], pct_embargo=0.01)
for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X)):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    model = LGBMClassifier(**params)
    model.fit(X_train, y_train)
    # 評価指標計算 (entropy lift / Precision / Direction Accuracy / Simulated PnL / DSR)
```

**Embargo の意義**: Triple Barrier ラベルは vertical barrier (K bar 後) まで価格推移を見るため、test fold の最後の K bar 分は train fold の最初の K bar 情報と overlap → information leakage。Embargo で防止。

**全 6 案 × 5 fold = 30 回学習** の物理証跡を完了報告に含める。

## §4 合格基準 5 指標 (cc_ml_design_spec §1.5.1 整合)

各案について 5 fold 平均値で判定:

| # | 指標 | 合格閾値 | 計算方法 |
|---|---|---|---|
| 1 | **entropy lift** | **> 10%** | `1 - valid_logloss / log(num_classes)` (各案の num_classes に応じて計算) |
| 2 | **TP Precision** | **> 0.5** | TP first 予測の precision (案 a は MFE/MAE 比 ≥ 1.5 を TP first proxy) |
| 3 | **Direction Accuracy** (案 c) | **> 0.55** | 案 c のみ・LONG/SHORT/Flat の方向当たり率 |
| 4 | **Simulated PnL (12 ヶ月)** | 12 ヶ月中 8+ ヶ月プラス + 年間 NET ≥ $500 | naive Exit (TP 1% / SL 0.5% / TIME K bar) で簡易 Replay |
| 5 | **Walk-forward CV Sharpe (DSR 補正)** | **DSR > 1.0** | mlfinlab.backtest_statistics.DSR 経由・5 fold trial 統計補正 |

### §4.1 合格判定ルール (Layer 3 投入条件厳格化・v5)

- **6 案いずれか上記 5 指標 ALL PASS** → 採用案で Phase 2 進行
- **6 案ベストでも 5 指標未達** → **即** Layer 3 残存タスク投入 (CPCV + Class balancing / Focal loss + custom loss + アルゴ多様化)
- **「ベスト案で Phase 2 進行して判定」は禁止** (Phase 1 未達 → Phase 2 改善保証なし)
- §1.6.1 メタルール整合: 実行後の基準緩和 (entropy lift > 5% 等) 禁止

## §5 リソース計画 (3 並列・30-45 GB)

### §5.1 並列度

| 制約 | 内容 |
|---|---|
| CPU | LightGBM は n_jobs=-1 でマルチコア活用・6 案並列で CPU 競合 → **3 並列が現実的** |
| メモリ | 1 案 10-15 GB × 3 並列 = **30-45 GB** (通常 PC 32-64 GB で実現可能) |
| 依存 | 案 f (Meta-Labeling) は案 e 完了待ち sequential |

### §5.2 実行スケジュール

```
[Fold 0] 並列 3: a, b, c → 約 100 分 (a がボトルネック)
[Fold 0] 並列 3: d, e, (idle) → 約 60 分
[Fold 0] sequential: f → 約 60 分
[Fold 0 total]: 約 220 分 ≈ 4 時間

[Fold 1-4 同様] × 4 = 約 16 時間
[全 5 fold total]: 約 20 時間 (約 1 日)
```

### §5.3 Phase 1 期間 (3-4 週)

| 工程 | 期間 |
|---|---|
| ラベル設計 + データ準備 (Phase 0 v3.1 完了後) | 約 1 週 |
| 6 案実装 (run_lgbm_phase1_v5_case_*.py + purged_kfold runner) | 約 1-2 週 |
| 学習実行 (上記 20 時間) | 約 1 日 |
| CP2 監査 + 結果分析 | 約 1 週 |
| **合計** | **約 3-4 週** |

## §6 実装手順

```
[Step 1] Phase 0 改修 v3.1 完了確認 (Step 0-2 で verify)
[Step 2] mlfinlab セットアップ + Purged K-Fold runner 実装
  - run_phase1_v5_purged_kfold.py: 共通 CV runner (各案を呼び出し)
[Step 3] 6 案 (a-f) 個別実装
  - run_lgbm_phase1_v5_case_a_rmse.py
  - run_lgbm_phase1_v5_case_b_binary.py
  - run_lgbm_phase1_v5_case_c_multiclass.py
  - run_lgbm_phase1_v5_case_d_ranking.py (LambdaRank)
  - run_lgbm_phase1_v5_case_e_triple_barrier.py
  - run_lgbm_phase1_v5_case_f_meta_labeling.py (案 e 完了後)
[Step 4] smoke test (Fold 0 のみ・1-2 ヶ月のみ・1 時間以内)
  - 各案が正常実行されることを verify
  - メモリ消費・並列度を実測
[Step 5] CP2 監査依頼 (§9)
[Step 6] /audit OK 後・full 5 fold × 6 案実行
[Step 7] phase1_v5_summary.json 生成 (5 指標 × 6 案 × 5 fold + DSR + 合格判定)
[Step 8] 完了報告 (§8)
[Step 9] Layer 3 投入判定 (§4.1)
```

## §7 leak verify (Triple Barrier ラベル特有)

```bash
# (1) Triple Barrier ラベルが X (特徴量) に混入していないか
python -c "
import pandas as pd
df = pd.read_parquet('results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet')
LABEL_PREFIXES = ['LONG_MFE_pct', 'LONG_MAE_pct', 'SHORT_MFE_pct', 'SHORT_MAE_pct',
                   'triple_barrier_label', 'meta_label']
label_cols = [c for c in df.columns if any(c.startswith(p) for p in LABEL_PREFIXES)]
print(f'Label columns (must NOT be in X): {len(label_cols)} (expected 56)')
"

# (2) Purged K-Fold の Embargo verify
# Triple Barrier vertical barrier (K bar) が test fold に侵入する train サンプルを除外
# mlfinlab.cross_validation.PurgedKFold が自動処理 (パラメータ samples_info_sets で t1 渡す必要)

# (3) Phase -1 blacklist 48 列 drop verify (case_*.py 全部で実施)
grep -nE "BLACKLIST_FAMILIES|drop.*sma_20|drop.*ichimoku_kijun" scripts/priority_rebuild/run_lgbm_phase1_v5_*.py
# 期待: 全 6 案で blacklist drop コード存在
```

verify FAIL → false_positive §2 類型 A (look-ahead leak) として STOP・修正後再実装。

## §8 完了報告必須証跡

### 8.1 機械的証跡 8 点 (WORKFLOW.md L53-71)

1. コード総点検 grep 結果 (label 列が X に混入していないか + blacklist drop verify)
2. 数値の二重提示 (5 指標サマリー + 出典 phase1_v5_summary.json 引用)
3. 成果物ファイル実体 (6 案 × 5 fold の予測結果 sha256 + 行数)
4. 実行ログ (各案 × 各 fold の開始/終了時刻 + 所要時間 + Python warnings)
5. 絞り込み示唆語彙 自己 grep (no matches 含む)
6. 個別組合せ train→test 変化表 (6 案別 × 5 fold 別)
7. 異常値スメル 4 条件 (5 指標で「異常値」検出時は「合格」と書かない)
8. 全工程未来参照 verify (Triple Barrier ラベル + Meta-Labeling ラベルの因果性宣言)

### 8.2 L-200 機械的証跡 3 点

1. wc -l (本指示書 + ナレッジベース v3 + cc_ml_design_spec + 改修後 6 案スクリプト + phase1_v5_summary.json)
2. Read ツール全文 view
3. 該当箇所現物引用

### 8.3 追加報告

- 6 案 × 5 fold × 5 指標の全数値 (30 学習結果)
- 案別 feature_importance top20 (3 層 (連続値/Adaptive/自己実現的) 別効果測定・ナレッジベース v3 §I.6.3)
- DSR 計算詳細 (試行数・selection bias 補正)
- リソース実測 (メモリ peak / CPU 並列度 / 学習時間内訳)
- **§4.1 Layer 3 投入判定結果** (採用案決定 or Layer 3 投入)

## §9 CP2 監査依頼テンプレ (Claude `/audit` 経由)

```
監査対象: Phase 1 学習方法再設計 v5 (6 案並列学習 + Purged K-Fold 5 fold + DSR 評価結果)
対象の型: 混合型 (コード型 + 数値型 + 文書型)
使用観点: ① 統計学的妥当性 / ⑤ PM/CC ML 設計判断 / ⑥ 実行プロセス / ⑦ 主エージェント作業バイアス
証跡要求: grep 結果 / 行番号 / sha256 / 5 指標数値 / 逐語引用

監査依頼内容 (7 項目):
(1) Purged K-Fold 5 fold の Embargo 設定妥当性 (Triple Barrier vertical barrier との整合)
(2) DSR (Deflated Sharpe Ratio) 計算の Selection bias 補正妥当性 (試行数記録 + 100+ grid 試行)
(3) 6 案間の比較妥当性 (各案で同じ Phase -1 blacklist 48 列 drop + 同じ Purged K-Fold split)
(4) 合格基準 5 指標の判定厳格性 (5 指標 ALL PASS = 1 件でも未達 → 不合格・§1.6.1 メタルール整合)
(5) Meta-Labeling 2 段階の leak 不在 (Primary 予測を Secondary 学習に使う際の future-look 検証)
(6) Phase 1-c smoke entropy lift 6.04% との比較 (v5 で >10% 達成可能か・案別)
(7) CC 同型バイアス 27+ 件 (cc_role §1.4 + handoff v20 §0.26) 再演有無
```

監査結果 OK → §4.1 採用判定 / NG → 監査指摘事項対応 → 再 smoke → 再 /audit。

## §10 失敗時の戻り

| 失敗内容 | 対応 |
|---|---|
| Phase 0 v3.1 ラベル数 ≠ 56 | Phase 0 v3.1 再実行 (compute_triple_barrier_labels 実装漏れ) |
| mlfinlab インストール失敗 | pip install mlfinlab + 依存パッケージ (statsmodels / scikit-learn ≥ 1.0) |
| メモリ不足 (>45 GB) | 並列度 3 → 2 に削減 / Fractional Diff列削減 / PCA 強化で列数縮小 |
| Walk-forward CV 学習 timeout (> 1 日) | 並列度上げる (3 → 4) / hyperparameter 削減 / smoke で fold 1 のみで先行判定 |
| **6 案 5 指標 ALL FAIL** | **Layer 3 残存タスク即投入** (CPCV / Class balancing / Focal loss / custom loss / アルゴ多様化) |
| Triple Barrier ラベル偏り (TP first 比率 < 5% or > 95%) | TP/SL barrier 倍率調整 (Phase 0 v3.1 で 2.0×ATR 固定だが Adaptive 化検討) |

## §11 過去不正パターンのガード 8 件

### ガード A: §0-1 Prime Directive (false_positive §0-1)

Phase 1 学習で使う全変数について「本番運用の推論時点 t で因果的に取得可能か」1 行ずつ宣言:
- 特徴量 X: Phase 0 で生成された 約 2200-2900 列 - blacklist 48 = 約 2152-2852 列 (全部 t 時点で取得可能・leak フリー)
- ラベル y: 56 ラベル列のいずれか (案別に選択・**学習で X に含めない**)
- Walk-forward CV split: PurgedKFold が train_idx/test_idx を分離 + Embargo で leak 防止

### ガード B: §0-2 ポジション上限 (false_positive §0-2)

Phase 1 (parquet 学習のみ) では直接適用なし。**Simulated PnL 計算時** (合格基準 #4) に 0.024 BTC / trade で算出 (Phase 5 確定値ではないが暫定)。

### ガード C: L-179 fractal j±2 leak 同型再発検知

Phase 0 v3.1 ラベル生成 (mlfinlab Triple Barrier) が j ≤ i 構造 (vertical barrier は t+K で future) を維持していること verify。**Phase 1 学習で X には含めない** (label only)。

### ガード D: L-180 ドキュメント引用前 実装 verify

「learning_design_v4 v5 に書いてあるから」を理由にしない。各案実装前に mlfinlab API + Phase 0 v3.1 parquet schema を grep で実装 verify。

### ガード E: L-181 設計転換時 旧記述 grep sweep

```bash
# 旧 V4.1 「3 案並列」記述の grep sweep (v5 で 6 案に拡張)
grep -rn "3 案並列\|3 案 (RMSE / Binary / Multiclass)\|Triple Barrier.*Layer 3\|Walk-forward.*Layer 3" .claude/ cc_ml_design_spec.md | grep -v archive
# 期待: v5 整合の修正済記述のみ・旧記述残存なら追加 sweep
```

### ガード F: L-200 機械的証跡 3 点

完了報告に必須 (§8.2)。

### ガード G: L-194 原則違反では選択肢併置禁止

合格基準 5 指標 ALL FAIL → 「(A) Layer 3 投入 / (B) ベスト案で Phase 2 進行」選択肢併置禁止。**§4.1 厳格化ルールで (A) Layer 3 投入のみ**。

### ガード H: 閾値ハードコード禁止 + DSR 採用 (指示書 v3 ガード H 継承)

- Phase 1 では閾値ハードコードは原則発生しないが、案 d Ranking の「上位 N%」(5/10/20) は grid search で DSR 評価 (Standard Sharpe maximizing 禁止)
- 合格基準 #5 Walk-forward CV Sharpe は **DSR 補正必須** (selection bias under multiple testing)

---

## CC への注意

- **6 案実装の優先順位**: 案 a (流用ベースライン) を最初に動作確認 → 案 b/c (派生ラベル) → 案 d (LambdaRank・新規) → 案 e (Triple Barrier・mlfinlab) → 案 f (Meta-Labeling・案 e 後)
- **mlfinlab API の習熟**: ナレッジベース v3 §D.6 + GitHub hudson-and-thames/mlfinlab + AFML Ch.3/5/7 を参照 (CC 単独で実装試行錯誤しない)
- **Triple Barrier の barrier 倍率** (Phase 0 v3.1 で 2.0×ATR 固定) は Phase 4-b で Adaptive 化検討 (Phase 1 では固定値で評価)
- **5 fold 学習時間 20 時間** は中断不可ではない (各 fold 独立保存 + resume 可能設計)
- **CC 同型バイアス 27+ 件 警戒**: 「案 a 採用すれば OK」「3 案で十分」等の **学習方法そのものを軽視する翻訳** を再発させない (handoff v20 §0.26 #5 同型)

---

## 完了後の状態

- 6 案 × 5 fold = 30 学習結果 (各 fold で 5 指標数値)
- phase1_v5_summary.json (合格判定 + DSR + 採用案決定 or Layer 3 投入決定)
- CP2 監査 PASS (Claude `/audit` 経由独立検証 7 項目)
- Phase 2 (採用案 Optuna ハイパラ調整) 着手準備完了 (or Layer 3 投入時は CPCV 別途指示書)
- handoff v23 へ進捗反映

## 次のステップ

- 合格時: **Phase 2 (Optuna ハイパラ調整)** 着手 (採用案で約 3-5 日)
- 未達時: **Layer 3 残存タスク投入** (CPCV / Class balancing / Focal loss / custom loss / アルゴ多様化・別指示書発行)
- Phase 4-b 改修: ナレッジベース v3 §I.7.3 整合で **DSR + walk-forward Adaptive 閾値最適化** を Phase 4-b 全グリッドサーチに統合

---

以上。
