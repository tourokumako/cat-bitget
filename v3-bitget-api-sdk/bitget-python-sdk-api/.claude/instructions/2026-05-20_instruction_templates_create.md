# 【指示書サイズ規律 3 経路固定】テンプレ正本化 + role 追記 + L-198 追加

(Web Claude 起案・2026-05-20)

## 保存先

- 指示書: `.claude/instructions/2026-05-20_instruction_templates_create.md`
- 完了報告: `.claude/instructions/2026-05-20_instruction_templates_create_completion.md`
- 作成 / 修正対象:
  - 新規: `.claude/templates/instruction_template_light.md`
  - 新規: `.claude/templates/instruction_template_full.md`
  - 修正: `.claude/rules/web_claude_role.md` (§1.5.5 新規セクション追加)
  - 修正: `.claude/memory/lessons_active.md` (L-198 新規追加 + ヘッダ更新)

## Steps

- Step 1: `.claude/templates/` ディレクトリ作成
- Step 2: `instruction_template_light.md` 作成 (80-120 行)
- Step 3: `instruction_template_full.md` 作成 (option5v7h_reeval.md コピー + 一般化)
- Step 4: `web_claude_role.md` §1.5.5 挿入 (§1.5 と §1.6 の間)
- Step 5: `lessons_active.md` L-198 追加 + ヘッダ L-196〜L-103 → L-198〜L-105
