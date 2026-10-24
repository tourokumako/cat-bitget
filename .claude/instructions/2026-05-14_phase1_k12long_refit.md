# Phase 3 trial 部分採用: K12 LONG のみ num_leaves=15 で再学習 + 再評価

| 項目 | 値 |
|---|---|
| 発行日 | 2026-05-14 |
| 作成者 | Web Claude (PMエージェント) |
| 承認 | まこさん |
| 関連 commit | a5dad18 (Phase 3 trial 完了) / fc1f7f8 (Phase 3 試行指示書) / bae7a0c (案G残務) |
| 監査経由 | あり (Web Claude 評価・K12 LONG MFE_lift +56pp 改善発見) |
| 関連必読 | WORKFLOW.md §🔴次のタスク / cc_ml_design_spec.md §1.6 / §1.6.1 (改訂版) / .claude/instructions/2026-05-14_phase3_short_trial_completion.md / handoff_to_web_claude_v3_phase1_phase3a.md §2.3 |
| 目的 | K12 LONG 2 モデルのみ部分採用で監査懸念1 を入力段階で構造的解消 |

## 本文 (CC への指示)

【タスク】Phase 3 trial 部分採用: K12 LONG のみ num_leaves=15 で再学習 + 再評価
(Web Claude評価・まこさんGO済 2026-05-14)

## 構造化ルール準拠
- 保存先: .claude/instructions/2026-05-14_phase1_k12long_refit.md
- 完了報告: .claude/instructions/2026-05-14_phase1_k12long_refit_completion.md

## 着手前必読
1. WORKFLOW.md §🔴次のタスク
2. cc_ml_design_spec.md §1.6 / §1.6.1 (改訂版・q99 加重 + メタルール)
3. .claude/instructions/2026-05-14_phase3_short_trial_completion.md (Phase 3 試行結果)
4. handoff_to_web_claude_v3_phase1_phase3a.md §2.3 (旧 leak 実績・参考)

## 背景

Phase 3 短期試行で「K12 LONG のみ num_leaves=15 で MFE_lift -9.99 → +46.07 (+56pp 改善)」
が判明。監査 #2 懸念1 (K12 LONG 低ボラ選好) の構造的解決策が手中にある。

Phase 4-a 着手前に K12 LONG のみ 部分採用し、入力段階で監査懸念1 を解消する。

## メタルール照合 (重要)

cc_ml_design_spec §1.6.1 メタルール:
「各 Phase の合格基準は当該 Phase 実行前に確定し、実行結果確定後の基準変更は
当該 Phase の合否判定に適用しない」

本タスクは:
- **合格基準の変更ではない** (Phase 2 改訂後 spec PASS は維持)
- **学習方法の改善** (Phase 1 内のラベル別ハイパラ調整)
- Phase 2 合格判定は q99 加重 +20.58pp で PASS 済・本タスク後の再評価は上方修正のみ想定
- → **メタルール抵触なし**

## タスク 1: K12 LONG MFE / K12 LONG MAE の 2 モデルのみ再学習

scripts/priority_rebuild/run_lgbm_phase1.py の num_leaves を K12 LONG のみ 15 に:

```python
def get_num_leaves(K, side, label_type):
    """K12 LONG のみ部分採用 (2026-05-14)"""
    if K == 12 and side == 'LONG':
        return 15  # Phase 3 trial で MFE_lift +56pp 改善判明
    else:
        return 31  # 他ラベルは現行維持 (Phase 1 完了状態)
```

または K12 LONG MFE / MAE の 2 モデルのみ単独再学習スクリプト作成。

### 再学習対象 (2 モデル)
- K12_LONG_MFE
- K12_LONG_MAE

他の 14 モデルは Phase 1 完了状態を維持 (再学習しない・既存 .txt ファイル流用)。

### bit-exact 再現性
- random_state=42 / bagging_seed=42 / data_random_seed=42 / feature_fraction_seed=42 / num_threads=1 維持
- 同コマンド 2 回実行で sha256 一致確認

## タスク 2: predictions_test2025.parquet / predictions_train_2021_2024.parquet 部分更新

K12 LONG MFE / K12 LONG MAE の 2 列のみ新モデル予測値で上書き:

```python
# 既存 predictions ファイル読み込み
preds_test = pd.read_parquet('results/priority_rebuild/ml_phase1/predictions_test2025.parquet')
preds_train = pd.read_parquet('results/priority_rebuild/ml_phase1/predictions_train_2021_2024.parquet')

# K12 LONG MFE / MAE 2 列のみ新モデル予測値で上書き
preds_test['pred_LONG_MFE_K12'] = new_model_mfe.predict(test_features)
preds_test['pred_LONG_MAE_K12'] = new_model_mae.predict(test_features)
# 同様に train

# 保存先 (Phase 1 出力を上書きしない・新ファイル)
preds_test.to_parquet('results/priority_rebuild/ml_phase1/predictions_test2025_k12long_refit.parquet')
preds_train.to_parquet('results/priority_rebuild/ml_phase1/predictions_train_2021_2024_k12long_refit.parquet')
```

## タスク 3: 改訂後 spec で Phase 2 再評価

```bash
python3 scripts/priority_rebuild/run_phase2_precision.py \
  --predictions results/priority_rebuild/ml_phase1/predictions_test2025_k12long_refit.parquet \
  --output results/priority_rebuild/ml_phase2_k12long_refit/ \
  2>&1 | tee logs/phase2_k12long_refit_$(date +%Y%m%d_%H%M%S).log
```

(--引数対応していない場合は path をハードコード変更)

期待:
- q99 加重 (改訂後 spec 指標1) ≥ +20.58pp (上方修正・悪化はない想定)
- 8 組合せ中 positive 7+ 維持
- K12 LONG q99 net_quality 大幅改善

## タスク 4: 比較レポート

| 指標 | Phase 1 (現行) | K12 LONG refit |
|---|---|---|
| q99 加重 (改訂後 spec) | +20.58pp | XX pp |
| 24組合せ加重 (参考) | +8.72pp | XX pp |
| K12 LONG q99 net_quality | -3.91pp (推定) | XX pp |
| K12 LONG MFE_lift% | -9.99% | XX % |
| K12 LONG MAE_lift% | -26.05% | XX % |
| K12 LONG MFE/MAE 比 | 0.74 (推定) | XX |
| 他 15 ラベル | (Phase 1 維持・変化なし) | (同上) |

## タスク 5: 採用判定

### 採用条件 (全項目クリア)
1. q99 加重 (改訂後 spec) が Phase 1 値以上 (+20.58pp 以上)
2. 8 組合せ中 positive が 7/8 以上維持
3. K12 LONG q99 net_quality > 0 (低ボラ選好問題解消確認)
4. 他 14 ラベルの予測値が完全同一 (bit-exact 一致)

全クリア → K12 LONG refit 版を Phase 4-a 入力として正式採用
未クリア → Web Claude 評価で対応決定

## 物理証跡 (Phase 1 同形式・8点)
1. 入力ファイル整合性
2. 学習プロセス内部証跡 (K12 LONG MFE/MAE の iteration log)
3. 出力ファイル証跡 (新モデル 2 つ・新 predictions 2 つ)
4. 第三者再読み出し検証 (lgb.Booster で feature_importance 再表示)
5. データ sanity (predictions の null 率・他 14 ラベル列の bit-exact 確認)
6. stderr / Python warning 全件
7. 同コマンド bit-exact 再現性確認
8. K12 LONG MFE_lift% 改善確認 (Phase 3 trial 値 +46.07% と整合か)

## 完了報告必須証跡 5 点

1. **コード総点検 grep 結果**
   - `grep -n "num_leaves" scripts/priority_rebuild/run_lgbm_phase1.py`
   - `grep -n "K12.*LONG\|get_num_leaves" scripts/priority_rebuild/run_lgbm_phase1.py`

2. **数値の二重提示**
   - 比較レポート (Phase 1 vs K12 LONG refit の全指標)

3. **成果物ファイル実体** (sha256 + 行数 + 更新時刻)
   - lgbm_K12_LONG_MFE.txt (新) / lgbm_K12_LONG_MAE.txt (新)
   - predictions_test2025_k12long_refit.parquet
   - predictions_train_2021_2024_k12long_refit.parquet
   - phase2_k12long_refit 評価結果

4. **実行ログ** (所要・終了コード)

5. **絞り込み示唆語彙 自己 grep 結果**

## 完了後の状態

- K12 LONG num_leaves=15 で再学習完了
- predictions 部分更新版が Phase 4-a 入力として利用可能
- 改訂後 spec PASS が上方修正で再確認
- 監査懸念1 (K12 LONG 低ボラ選好) が入力段階で構造的解消
- Phase 4-a 着手指示書発行 準備完了

## 採用判定後の次のステップ

採用 → Phase 4-a (k-means クラスタリング) 着手指示書発行 (predictions_train_2021_2024_k12long_refit.parquet を入力に指定)
