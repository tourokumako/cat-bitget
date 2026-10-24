# 【タスク】成果物ファイル名の一意化ルール追加 + Phase 2 rerun 成果物のリネーム提示

(まこさん指摘・Web Claude レビュー済・まこさん GO 済 2026-05-14)

## 構造化ルール準拠

- 保存先: .claude/instructions/2026-05-14_filename_uniqueness_rule.md
- 完了報告: .claude/instructions/2026-05-14_filename_uniqueness_rule_completion.md

## 背景

同名ファイルがフォルダ違いで複数存在し、チャット添付時に取り違え多発:
- ml_phase2_rerun_prerefit/net_quality_24combinations.csv vs ml_phase2_rerun_postrefit/同名 (今回 3 回取り違え)

フォルダ階層はチャット添付時に失われるため、ファイル名だけで識別できる必要がある。

## Step 1: 命名ルールを WORKFLOW.md に追記

NG: フォルダ違い同名 / OK: 識別子をファイル名末尾に付与 (例: `_PREREFIT.csv` / `_POSTREFIT.csv`)

## Step 2: 今回の Phase 2 rerun 成果物を識別子付きでリネーム提示

### 2-A: 事前確認 (n_fire 期待値)

- postrefit K12 LONG q99: 期待 342
- prerefit K12 LONG q99: 期待 1660

異常時はリネーム中断・調査。

### 2-B: リネームコピー (元残置)

postrefit: net_quality / mfe_mae_ratio / rmse_sanity / phase2_summary に `_POSTREFIT` 付与
prerefit: net_quality / phase2_summary に `_PREREFIT` 付与

### 2-C: チャット貼り付け

6 ファイル全文 + sha256 + n_fire 値併記
