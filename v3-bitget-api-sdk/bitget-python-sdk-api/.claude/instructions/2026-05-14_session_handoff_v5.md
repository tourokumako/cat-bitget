# 【タスク】セッション引き継ぎメモ作成 + drift 確定の spec 明文化

(セッション区切り処理・Web Claude レビュー済・まこさん GO 済 2026-05-14)

## 構造化ルール準拠

- 保存先: .claude/instructions/2026-05-14_session_handoff_v5.md
- 完了報告: .claude/instructions/2026-05-14_session_handoff_v5_completion.md
- 成果物ごとに commit 分割可

## 背景

本セッションで重い確定が 4 件・新規の仕組みが複数導入されたが、「drift 対処 = 固定維持 + K96 SHORT q99 除外」が現状どの正本にも明文化されていない。次セッションの Web Claude が経緯・次の本題・監査の宿題を引き継げるよう、handoff メモと spec 明文化を行う。

## Step 1: cc_ml_design_spec.md に drift 確定を明文化

「絶対閾値 drift 対処方針 (2026-05-14 audit#9 確定)」を §1.6.1 直後 (適切な箇所) に新セクションとして追加:
- rolling 却下 (§1.6.1 抵触疑い + 信号品質全面低下)
- ハイブリッド却下 (selection bias)
- K96 SHORT q99 除外 (年 $169,400 損失・全 12 月 $1,900 維持)
- spec 追記のみ・実装側無変更

## Step 2: §4a.5 フォールバック発動条件に「test 発火 0 件」を追加 (audit#9 改善提案)

`.claude/rules/phase_compliance_checklist.md` §4a.5 発動条件に追加:
「または当該組合せの test 発火が 0 件の場合は自動 no-trade 除外」

## Step 3: handoff メモ作成

`.claude/instructions/handoff_to_web_claude_v5_session_20260514.md` を新規作成。7 セクション:
1. 本セッションの確定事項 4 件
2. 本セッションで導入した仕組み
3. 次セッションの本題 (選択肢 5 vs 7 の再評価)
4. 監査が出した未処理の宿題
5. 次セッション着手手順
6. 本セッションで繰り返された Web Claude のミスと対策
7. 本セッション成果物一覧

## Step 4: WORKFLOW.md §🔴次のタスク更新

「選択肢 5 vs 7 の再評価 (固定維持 + K96 SHORT 除外を前提・監査経路を通す)」に更新。

## 完了後の状態

- drift 確定が cc_ml_design_spec.md に明文化
- §4a.5 が「test 発火 0 件」を発動条件に含む
- handoff メモ作成
- WORKFLOW.md §🔴次のタスク更新

## 次のステップ

完了報告受領 → Web Claude が self_check.md チェック B で確認 → セッション完全終了 → 次セッション: handoff メモから再開・選択肢 5 vs 7 再評価へ
