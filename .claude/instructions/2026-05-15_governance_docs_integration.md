# 【タスク】ガバナンス文書の正本組み込み

発行日: 2026-05-15
承認: まこさん（明示的 GO）
self_check (A) 通過: 2026-05-15

---

## 背景

- false_positive_incident_policy.md（新規制定・audit#12 trailing exit leak + audit#14 読んだふり事案を契機）
- web_claude_self_check.md（140 行版・audit#12/#14 反映・旧 40 行版を置換）

上記 2 文書を CC/Web Claude 共通正本として `.claude/rules/` に配置し、既存の必読リスト・チェックリスト・完了報告テンプレに組み込む。

---

## 実施内容

### Step 1: 読了確認（機械的証跡必須）
- false_positive_incident_policy.md: 150 行 / L1, L38, L75, L113, L150 引用済
- web_claude_self_check.md: 140 行 / L1, L35, L70, L105, L140 引用済

### Step 2: ファイル配置
- `Downloads/false_positive_incident_policy.md` → `.claude/rules/` に配置（150 行）
- `Downloads/web_claude_self_check.md` → `.claude/rules/` に置換（140 行・旧 40 行版を上書き）

### Step 3: 参照追加
- WORKFLOW.md §Step 0 セッション開始時に必読 に項目 11・12 を追加
- WORKFLOW.md 完了報告必須証跡を「5点」→「8点」に更新（項目 7: 異常値スメルテスト / 項目 8: 全工程未来参照 verify）
- CLAUDE.md §セッション開始時に必ず読むこと 表に 2 行追加

### Step 4: CC 側 feedback への恒久転記
- feedback_pre_execution_premise_check.md に追加ルール 5〜8 を永続転記：
  5. 異常値 4 条件 → 「合格」でなく「異常値・要調査」
  6. PnL 計算式の入力変数を因果性で 1 行ずつ宣言
  7. 「読んだ」「確認した」「完了した」は機械的証跡を伴わせる
  8. インシデントの疑い → 報告先行

---

## 完了条件
- `.claude/rules/false_positive_incident_policy.md` 実在 (150 行) ✅
- `.claude/rules/web_claude_self_check.md` 実在 (140 行) ✅
- WORKFLOW.md 必読 11・12 追加 ✅
- WORKFLOW.md 完了報告 7・8 追加 ✅
- CLAUDE.md 必読表 2 行追加 ✅
- feedback_pre_execution_premise_check.md 追加ルール 5〜8 転記 ✅
- commit 済 ✅
