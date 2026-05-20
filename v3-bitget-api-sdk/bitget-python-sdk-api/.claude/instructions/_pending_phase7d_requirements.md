# Phase 7-d 着手前 / 着手時の要件 (pending)

作成: 2026-05-20 (audit#19 監査結論由来)

---

## audit#19 監査結論由来 (2026-05-20)

### 要件 1: maxMarketOrderQty 単位 confirm

- **確認内容**: 0.024 BTC の market close 発注が Bitget に受け付けられるかを paper trading で実発注テスト
- **背景**: contracts API `maxMarketOrderQty=220` の単位 (lots vs BTC) が確定不能
  - BTC 単位なら 220 BTC >> 我々の規模・非バインディング ✅
  - lots 単位なら 220 lots × 0.0001 = 0.022 BTC < 0.024 BTC → 緊急 close 時 reject リスク ❌
- **出典**: audit#19 監査報告 スコープ D + 監査結論 条件 3 (2026-05-20)
- **確認方法**: paper trading (Demo API) で `close_market_order(size=0.024)` を一度実行し、API が受け付けるか確認。reject される場合は size を 0.022 BTC 以下に下げて再試行し、単位を推定。
- **担当**: Phase 7-d 着手指示書で具体化
- **状態**: ⏳ pending

---

## 追記ルール

このファイルに Phase 7-d 要件が追加される場合は末尾に追記する (上書きしない)。
各要件に「出典・確認方法・状態 (pending / done)」を明記すること。
