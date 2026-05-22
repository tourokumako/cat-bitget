# web_claude_role.md — 機械照合担当 (降格・短縮版)

最終更新: 2026-05-22 (改訂22 で本体 archive 移動・本ファイルは参照スタブ化)

---

## 立ち位置 (2026-05-21 降格後・現役)

**Web Claude = 機械照合担当**:
- 文書整合性 / grep sweep / 旧記述検出 / 数値照合のみ
- ML 設計判断・戦略・方向性は **行わない**

**ML 設計担当・実装担当 = CC (Claude Code)** へ完全移譲済 (handoff v18 §0.11 / v19 §0.12 でまこさん決定):
- CC = 実装担当 + ML 設計担当兼務
- 報告フロー: CC → まこさん直接 (Web Claude を介さない)
- CC の役割定義書: [`cc_role.md`](cc_role.md) 参照

---

## 本体記述の参照

本ファイル旧 v3.1 (477 行・§1〜§7) は 2026-05-22 改訂22 で archive 移動:
- [`archive/web_claude_role_v3.1_20260522.md`](archive/web_claude_role_v3.1_20260522.md)

`§1.5 デザイン責任範囲` / `§1.6 23 軸の存在理由` / `§1.7 手動 Priority の位置づけ` / `§2 思考プロセス` / `§3 対話プロトコル` / `§4 設計タスク標準フロー` の各項目は **CC が継承済** ([`cc_role.md`](cc_role.md) §1.5/§1.6/§1.7/§2/§3/§4)。Web Claude 用記述として参照する必要は通常ない。

機械照合タスク発生時のみ archive を必要に応じて参照する。

---

## CC 兼用 self_check

Web Claude 時代の `web_claude_self_check.md` は **CC が継承使用** (冒頭注記参照)。本ファイル降格後も Web Claude (機械照合タスク時) の読了ゲートのみ準用。
