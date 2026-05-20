# 【audit#19 後続タスク統合】self_check 更新 + phase_compliance 更新 + Phase 5-e Funding 改訂

(Web Claude 起案・まこさん GO 待ち 2026-05-20)

## 構造化ルール準拠

- 保存先: `.claude/instructions/2026-05-20_audit19_downstream_integration.md`
- 完了報告: `.claude/instructions/2026-05-20_audit19_downstream_integration_completion.md`

## 背景

audit#19 全工程完了 (commit 8c75aca) により以下が確定:
- exchange_spec.md の ⚠️ 9 項目解消 / F1-F8 意味確定 / L-196 補追済
- maxMarketOrderQty 単位確定は Phase 7-d pending

本タスクは audit#19 確定値を 3 正本 + Phase 7-d 要件統合に反映する。

## 確定済み判断 (まこさん 2026-05-20 承認)

- 判断 1: median (p50) baseline で月次 $1,900 合格判定 / p95 は参考値
- 判断 2: median = +0.0002%/8h を baseline / LONG 受取は注記のみ
- 判断 3: self_check L99-107 は値更新のみ (F1-F8 追加しない)

## Steps

- Step 1: web_claude_self_check.md L99-107 更新
- Step 2: phase_compliance_checklist.md Funding 統計分布化 + Phase 7-d 統合
- Step 3: cc_ml_design_spec.md §5 Phase 5-e 改訂
- Step 4: _pending_phase7d_requirements.md 削除 (Step 2 統合後)
