# Phase 3 短期試行: K 窓別 num_leaves 調整 (1-2日)

| 項目 | 値 |
|---|---|
| 発行日 | 2026-05-14 |
| 作成者 | Web Claude (PMエージェント) |
| 承認 | まこさん |
| 関連 commit | bae7a0c (案G 残務処理) / e56250c (案G 残務指示) / 30839c1 (案G 実行) |
| 監査経由 | あり (audit#3 案E 推奨・spec 改訂後の事後検証として実施) |
| 関連必読 | WORKFLOW.md §🔴次のタスク / cc_ml_design_spec.md §1.6 / §1.6.1 (改訂版) / .claude/instructions/2026-05-14_plan_g_finalize_completion.md / handoff_to_web_claude_v3_phase1_phase3a.md §2.1 §2.3 / handoff_to_web_claude_v4_phase1_7a.md §2 / scripts/priority_rebuild/run_lgbm_phase1.py |

## 本文 (CC への指示)

【タスク】Phase 3 短期試行: K 窓別 num_leaves 調整 (1-2日)
(Web Claude評価 + 監査#3 案E反映・まこさんGO済 2026-05-14)

## 構造化ルール準拠
- 保存先: .claude/instructions/2026-05-14_phase3_short_trial.md
- 完了報告: .claude/instructions/2026-05-14_phase3_short_trial_completion.md

## 着手前必読 (省略禁止)
1. WORKFLOW.md §🔴次のタスク
2. cc_ml_design_spec.md §1.6 / §1.6.1 (改訂版・q99 加重 + メタルール)
3. .claude/instructions/2026-05-14_plan_g_finalize_completion.md (案 G 完了)
4. handoff_to_web_claude_v3_phase1_phase3a.md §2.1 §2.3 (旧 Phase 3-a/3-b 実績)
5. handoff_to_web_claude_v4_phase1_7a.md §2 (旧 Phase 3-b 改善実績)
6. scripts/priority_rebuild/run_lgbm_phase1.py (現実装・num_leaves 確認済 = 31)

## 背景 (監査 #3 + Web Claude 評価反映)

- 案 G 完成済 (spec 改訂 + メタルール + 残務処理)
- 監査 #3 で「num_leaves 未確認・Phase 3 余地あり」指摘
- 監査推奨 案 E (Phase 3 短期試行 → Phase 4) を案 G 完了後に実施
- 目的: 「spec 改訂が本当に最後の例外だったか」の事後検証
  - 改善あり → spec はメタルール準拠で固定維持・Phase 4 はより良い土台で着手
  - 改善なし → 案 G (spec 改訂) 正当性確定・Phase 4 直行

## spec 改訂は撤回しない (重要)

cc_ml_design_spec §1.6.1 メタルール準拠:
- §1.6 指標1 = q99 加重 (固定・撤回しない)
- 本試行で 24組合せ加重 PASS したとしても spec は元に戻さない
- 「最後の例外」は最後の例外として確定

本試行は「Phase 4 着手前の追加情報収集」であり、spec 撤回手続きではない。

## タスク 1: ハイパラ変更内容 (旧 Phase 3-b 設定の移植)

scripts/priority_rebuild/run_lgbm_phase1.py の num_leaves を K 窓別に変更:

```python
def get_num_leaves(K):
    """旧 Phase 3-b 設定の移植 (handoff_v3 §2.1 / handoff_v4 §2)"""
    if K in [12, 24]:
        return 15  # 短期は浅い木
    elif K in [48, 96]:
        return 31  # 長期は深い木 (現デフォルト維持)
    else:
        raise ValueError(f"Unexpected K: {K}")

# 学習ループ内で K を渡す
params['num_leaves'] = get_num_leaves(K)
```

他のハイパラは Phase 1 と同一 (random_state=42 / bagging_seed=42 等の seed 4 種・num_threads=1 維持)。

## タスク 2: 再学習実行

```bash
echo "=====🚀 Phase 3 短期試行 RUN START $(date) ====="
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api

# 出力先を分離 (Phase 1 出力を上書きしない)
# 既存 run_lgbm_phase1.py を改修して output_dir を指定可能にする
# または別スクリプト run_lgbm_phase3_trial.py を新規作成

python3 scripts/priority_rebuild/run_lgbm_phase3_trial.py 2>&1 | tee logs/phase3_trial_$(date +%Y%m%d_%H%M%S).log
```

出力先: results/priority_rebuild/ml_phase3_trial/
- 16 LightGBM model (lgbm_*.txt)
- training_summary.csv
- predictions_test2025.parquet
- feature_importance_top20_*.csv × 16
- bit-exact 再現性確認 (num_threads=1 維持)

## タスク 3: Phase 2 同形式の判定 (改訂後 spec で評価)

scripts/priority_rebuild/run_phase2_precision.py を Phase 3 trial 出力に対して実行:

```bash
python3 scripts/priority_rebuild/run_phase2_precision.py \
  --predictions results/priority_rebuild/ml_phase3_trial/predictions_test2025.parquet \
  --output results/priority_rebuild/ml_phase3_trial/phase2_eval/ \
  2>&1 | tee logs/phase3_trial_eval_$(date +%Y%m%d_%H%M%S).log
```

(--引数対応していない場合は path をハードコード変更)

出力:
- results/priority_rebuild/ml_phase3_trial/phase2_eval/phase2_summary.json
- 24組合せ別 net_quality / 16 ラベル別 RMSE sanity / mfe_mae_ratio_24combinations.csv

## タスク 4: 比較レポート

Phase 1 (現状) vs Phase 3 trial の比較:

| 指標 | Phase 1 | Phase 3 trial | Δ |
|---|---|---|---|
| q99 加重 (改訂後 spec) | +20.58pp | XX pp | XX pp |
| 24組合せ加重 (旧 spec・参考) | +8.72pp | XX pp | XX pp |
| 24組合せ中 positive | 23/24 | XX/24 | Δ |
| 8組合せ (q99) 中 positive | 7/8 | X/8 | Δ |
| K12 LONG q99 net_quality | +16.06pp | XX pp | XX pp |
| K24 LONG q99 net_quality | (Phase 2 値) | XX pp | XX pp |
| K48 LONG q99 net_quality | (Phase 2 値) | XX pp | XX pp |
| K96 SHORT q99 net_quality | -8.22pp | XX pp | XX pp ← 改善するか? |
| 16ラベル RMSE sanity | 16/16 PASS | X/16 | Δ |

## タスク 5: 判定 (3 パターン)

### パターン A: 改善大 (24組合せ加重 +10pp 以上達成)
- 仮の意味: 「Phase 3 で 24組合せ加重 PASS できた」= spec 改訂は遡って疑義
- 実際の判断: メタルール §1.6.1 に従い spec 改訂維持・ただし Phase 4 着手はより良い土台で
- 完了報告に「Phase 3 改善大・案 G spec 改訂は遡って疑義あるがメタルール準拠で固定維持」記録

### パターン B: 改善小 (24組合せ加重 +8〜+10pp 程度)
- 意味: Phase 3 ハイパラ調整で多少改善するが 24組合せ加重 PASS 未満
- 実際の判断: 案 G 正当性ほぼ確定・Phase 4 着手
- 完了報告に「Phase 3 改善小・案 G 正当性ほぼ確定」記録

### パターン C: 改善なし (24組合せ加重 +8.72pp 据え置き or 悪化)
- 意味: Phase 3 ハイパラ調整では解けない構造的問題
- 実際の判断: 案 G 正当性完全確定・Phase 4 直行
- 完了報告に「Phase 3 改善なし・CC 当初論証 (Phase 3 では解けない) 検証済」記録

### K96 SHORT q99 改善有無の追加判定
- 改善あり (net_quality > 0) → Phase 4-a regime 検知の前提が変わる
- 改善なし (net_quality ≤ 0) → §4a.5 フォールバック spec 維持

## 完了報告必須証跡 5 点

1. **コード総点検 grep 結果**
   - `grep -n "num_leaves" scripts/priority_rebuild/run_lgbm_phase3_trial.py`
   - `grep -n "get_num_leaves\|K in \[12, 24\]" scripts/priority_rebuild/run_lgbm_phase3_trial.py`

2. **数値の二重提示**
   - 比較レポート (Phase 1 vs Phase 3 trial の全指標)
   - 判定パターン A/B/C の明示

3. **成果物ファイル実体** (sha256 + 行数 + 更新時刻)
   - 16 LightGBM model (Phase 3 trial)
   - phase2_summary.json (Phase 3 trial 評価結果)
   - 全ログファイル

4. **実行ログ**
   - 学習所要 (Phase 1 は 141 分・Phase 3 trial も同程度予想)
   - 評価所要

5. **絞り込み示唆語彙 自己 grep 結果**

## 完了後の状態

- Phase 3 trial 結果 (改善あり/なし/中間) 確定
- 案 G 正当性の事後検証完了
- Phase 4-a 着手判断材料完全揃え
- K96 SHORT q99 が Phase 3 で改善するか判明 (Phase 4-a regime 設計の前提情報)
