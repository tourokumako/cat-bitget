# 【監査 follow-up】audit#19 監査結論 3 条件対応 (auditor_template L213 + spec 注記 + L-196 補追)

(Web Claude 起案・まこさん GO 待ち 2026-05-20)

## 構造化ルール準拠

- 保存先: `.claude/instructions/2026-05-20_audit19_audit_followup.md`
- 完了報告: `.claude/instructions/2026-05-20_audit19_audit_followup_completion.md`

## 背景

audit#19 監査エージェント (claude-sonnet-4-6・別セッション) が以下 3 件を発見:

1. **条件 1 (必須・まこさん GO 前)**: `auditor_template.md` L213 に旧値「125x」残存
2. **条件 2 (推奨・低優先)**: `exchange_spec.md` posLimit 行に Cloudflare 注記追加
3. **条件 3 (Phase 7-d 要件)**: maxMarketOrderQty 単位 confirm 要件追加

加えて L-196 How to apply 補追 (L-197 新設は over-classification として見送り)。

## 実行 Steps

- Step 1: auditor_template.md L213「125x → 150x」修正
- Step 2: exchange_spec.md posLimit 行に Cloudflare 注記追加
- Step 3: lessons_active.md L-196 How to apply 補追
- Step 4: _pending_phase7d_requirements.md 新規作成

## Guards

- Guard A: 自動 ✅ 昇格禁止 (Step 2 posLimit マーク判定は両案提示)
- Guard C: hypothesis ベース推定禁止 (L-196 補追は監査報告 §F 準拠)
- Guard E: ✅/⚠️/⛔ マーク管理 (出典項目別表も同時更新)
- Guard H: grep sweep 対象範囲明示義務 (L-181 同型対策)
