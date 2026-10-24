# 【タスク】Step 2: trailing exit / fixed_tp を本番再現可能な実装に修正し Phase 4-b / Phase 5 再実行

発行日: 2026-05-15
承認: まこさん（明示的 GO）
本ルート: WORKFLOW.md 改訂11 §🔴現在のフェーズ「次のタスク」Step 2
前提: Prime Directive 5箇所埋め込み完了（commit fe41b8e）

## 構造化ルール準拠

- 保存先: `.claude/instructions/2026-05-15_phase4b_phase5_rerun.md`
- 完了報告: `.claude/instructions/2026-05-15_phase4b_phase5_rerun_completion.md`

## 修正内容サマリー

1. trailing exit → bar-by-bar 時系列実装（MFE スカラー直接使用禁止）
2. fixed_tp → train-A/B 分離方式（fit by construction 解消）
3. Phase 4-b / Phase 5 再実行（出力 v2 ファイル）

詳細は指示書本文参照。
