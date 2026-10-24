# 【タスク】Phase 2 スクリプト改修 + refit 影響測定 + 構造改善 (監査#8 必須 5 項目)

(監査#8 審査済・Web Claude レビュー済・まこさん GO 済 2026-05-14)

## 構造化ルール準拠

- 保存先: .claude/instructions/2026-05-14_phase2_script_fix_and_structural.md
- 完了報告: .claude/instructions/2026-05-14_phase2_script_fix_and_structural_completion.md
- このタスクは複数の成果物を含むため、commit は成果物ごとに分割可

## 着手前必読

1. WORKFLOW.md §🔴次のタスク
2. cc_ml_design_spec.md §1.6 / §1.6.1 メタルール (案 G 改訂後の現文言)
3. scripts/priority_rebuild/run_phase2_precision.py 全文 (特に L72-73, L200-215)
4. .claude/instructions/2026-05-14_plan_g_pre_phase4_completion.md (案 G 完了報告)
5. results/priority_rebuild/leak_incident_20260513.md

## Step 0-1: 必読ファイル引用

a. cc_ml_design_spec.md §1.6 の指標 1 の現文言を全文引用
b. run_phase2_precision.py L72-73 と L200-215 を引用
c. 監査#8「案 A は §1.6.1 違反ではない」判定根拠を引用

## 背景 (監査#8 結果)

- run_phase2_precision.py は改訂後 spec (案 G・commit b14be88) を実装していない
  - L72-73: CRITERION_1_POSITIVE_MIN = 20 (改訂後 spec なら 6)
  - L200-215: df_all = df_nq.dropna(...) で 24 組合せ全部 (改訂後 spec なら q99 8 組合せのみ)
- 元 Phase 2 / 案 Z とも スクリプト自動判定は FAIL・「改訂後 spec PASS」は完了報告内の手計算
- 監査#8 判定: 案 A (スクリプト改修) が正解・案 B/C は却下
  - 案 A は §1.6.1 メタルール違反ではない (基準変更でなく実装整合化・案 G の実装漏れ補完)

## Step 1: run_phase2_precision.py を改訂後 spec に改修

### 1-A. 改修内容

- CRITERION_1_POSITIVE_MIN = 20 → 6
- judge_criteria() の指標 1: df_all (24 組合せ) → q99 のみ 8 組合せに絞る
- コードコメント「q99 only」と実装を一致

### 1-B. 改修の性質明示

改修コミット msg と完了報告に明示:
「案 G implementation gap 補完・新たな基準変更ではない・監査#8 が §1.6.1 違反ではないと判定済」

### 1-C. 案 G 完了報告の訂正

.claude/instructions/2026-05-14_plan_g_pre_phase4_completion.md に追記:
「スクリプト改修が案 G タスクに含まれていなかった事実を記録」

## Step 2: 改修後スクリプトで Phase 2 を 2 回判定

### 2-A. refit 前データで判定

入力: ml_phase1/predictions_test2025.parquet
出力: ml_phase2_rerun_prerefit/

### 2-B. refit 後データで判定

入力: ml_phase1_k12long_refit/predictions_test2025_k12long_refit.parquet
出力: ml_phase2_rerun_postrefit/

### 2-C. 比較表

主要指標で refit 前/後の差分を一覧化。

### 2-D. refit 影響パターン判定 (3 通り・CC は事実提示のみ)

## Step 3: 公式判定 source の明文化

WORKFLOW.md + cc_ml_design_spec.md に追記:
「Phase X 合否の公式 source は results/.../phaseX_summary.json のみ。完了報告内の手計算は『参考』」

## Step 4: 全 phase script vs spec consistency check

監査#8 懸念 8 の乖離リスク箇所を grep verify:

- §4a.4 / §4a.5 / §4b.3 / §4b.4-b / Phase 1 hyperparam / §1.6.1 guard
- 「実装済・一致」「実装済・乖離あり」「未実装」のいずれかで判定

## Step 5: self_check.md 作成 (Web Claude 用)

.claude/rules/web_claude_self_check.md 新規作成・チェック A (指示書発行前) + チェック B (完了報告受領時)

## Step 6: L-179 教訓拡張

.claude/memory/lessons_active.md L-179 拡張: ML leak 限定 → spec/実装一般整合性

## 完了後の状態

- run_phase2_precision.py が改訂後 spec を実装
- refit 前/後の Phase 2 判定が改修後スクリプトで出る
- 公式判定 source 明文化
- 他 spec/script 乖離洗い出し
- self_check.md 作成
- L-179 一般化

## 次のステップ

完了報告 → Web Claude が独立評価 (self_check チェック B 適用) → まこさん refit 維持/撤回判断 → セッション工程 retain/redo 確定 → Phase 4-b 方針
