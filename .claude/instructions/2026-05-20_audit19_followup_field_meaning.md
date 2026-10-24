# 【監査タスク #19 follow-up】contracts API 見落とし 8 field の意味確定 + 設計影響評価

作成日: 2026-05-20  
担当: CC (Claude Code)  
状態: 完了 → completion report 参照

---

## 背景

audit#19 main task で contracts API (`GET /api/v2/mix/market/contracts?productType=USDT-FUTURES&symbol=BTCUSDT`) の全⚠️9項目を verify 完了。
その際、API レスポンスに含まれていた下記 8 フィールドが「観測済・意味未確定」のまま残っていた。
本 follow-up タスクでこれらの公式定義・単位・設計影響を確定する。

---

## 対象 8 フィールド（contracts API 実測値）

| ID | フィールド名 | 実測値 | 重要度 |
|---|---|---|---|
| F1 | posLimit | "0.2" | 最重要（Phase 7-d 判定に関与） |
| F2 | maxMarketOrderQty | "220" | 高 |
| F3 | maxOrderQty | "1200" | 高 |
| F4 | maxSymbolOrderNum | "200" | 中 |
| F5 | maxProductOrderNum | "1000" | 中 |
| F6 | buyLimitPriceRatio | "0.05" | 中 |
| F7 | sellLimitPriceRatio | "0.05" | 中 |
| F8 | feeRateUpRatio / openCostUpRatio | "0.005" / "0.01" | 低 |

---

## タスク内容

### Step 1: ドキュメントから公式定義を取得

各フィールドの公式説明文・単位を以下ソースから確認:
- Bitget v1 GitHub Pages docs: `https://bitgetlimited.github.io/apidoc/en/mix/#get-all-symbols`
- Cloudflare 非保護の v1 HTML をローカル保存済: `results/exchange_api/api_docs/bitget_v1_mix_all_symbols.html`

### Step 2: 設計影響評価

F1 posLimit が最重要 — 単位確定が必須:
- 「0.2 BTC」なのか「OI の 20%」なのか「その他の ratio」なのかを確定
- false_positive_incident_policy.md §0-2 の 0.12 BTC 上限との関係を明確化
- Phase 7-d 着手前判定として: posLimit が我々の 0.12 BTC を制約する物理上限か否か

### Step 3: 成果物作成

1. `results/exchange_api/api_docs/field_meaning_verify.md` — 8 フィールド分析レポート
2. `exchange_spec.md` — F1-F8 セクション追記
3. 本 completion report: `2026-05-20_audit19_followup_field_meaning_completion.md`

---

## Guards (anti-false-positive)

- Guard A: 定義の出所 URL を明記（"Bitget 公式" では不十分・ページ名 + URL 必須）
- Guard B: v1 docs に存在しないフィールドは「v2 専用・出典は API レスポンスの型推論」と明記
- Guard C: posLimit の単位は推測でなく公式テキストを引用
- Guard D: 設計影響評価は数値根拠を添える（「余裕がある」は根拠なしで書かない）

