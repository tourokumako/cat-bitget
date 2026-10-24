# 【監査タスク #19】Bitget USDT-FUTURES 取引所スペック全項目 verify (L-196 同型再発防止)

(Web Claude レビュー前・まこさん GO 待ち 2026-05-20)

## 保存先・完了報告パス

- 保存先: `.claude/instructions/2026-05-20_audit19_exchange_spec_full_verify.md`
- 完了報告: `.claude/instructions/2026-05-20_audit19_exchange_spec_full_verify_completion.md`
- 監査報告: `.claude/audits/2026-05-20_audit19_exchange_spec_full_verify.md`

## 背景

2026-05-20 セッションで `exchange_spec.md` L35「定期メンテ 火/水/木 05:00-08:00 UTC」が出典のない Claude 想定値だったことが発覚 (lessons_active.md L-196)。
⚠️ マーク 9 項目を体系的に verify し、全項目を ✅ または ⛔ に確定化する。

## verify 対象 (⚠️ 9 項目)

| # | 項目 | 現値 | verify 手段 |
|---|---|---|---|
| 1 | Maker 標準値 | 0.02% | contracts API + まこさんスクショ |
| 2 | Taker 標準値 | 0.06% | 同上 |
| 3 | 最小注文サイズ | 0.0001 BTC | contracts API |
| 4 | 最小注文額 | 5 USDT | contracts API |
| 5 | Tick size | 0.1 USDT | contracts API |
| 6 | 最大レバ | 125x | contracts API |
| 7 | マージンモード | isolated | contracts API |
| 8 | 最大同時保有数 | 200 | contracts API |
| 9 | Funding rate | 0.01%/8h 暫定 | funding-history API 30 日実測 |

## Step 1: contracts API (Items 3-8)

```bash
curl -sS 'https://api.bitget.com/api/v2/mix/market/contracts?productType=USDT-FUTURES&symbol=BTCUSDT'
```

## Step 2: funding-history API (Item 9 → 運用分布記録)

```bash
curl -sS 'https://api.bitget.com/api/v2/mix/market/history-fund-rate?symbol=BTCUSDT&productType=USDT-FUTURES&pageSize=100'
```

## Step 3: まこさん発注画面スクショ (Items 1-2)

CC は実行不能。まこさん側で取得 (README.md を `results/exchange_api/screenshots/` に生成し取得待ち状態とする)。

## ガード A-G

- ガード A: API response / スクショから取得した値だけを ✅ にする。出典なき ✅ 昇格禁止
- ガード B: contracts API response の生 JSON を保存 + sha256 + field 名→値→解釈の 3 段明示
- ガード C: Funding 30 日窓は audit 実行日 t から t-30 日まで固定。事後変更禁止
- ガード D: スクショの真正性 (BGB 残高表示・撮影日時・sha256)
- ガード E: exchange_spec.md の全 ⚠️ を ✅ または ⛔ に確定化
- ガード F: CC → Web Claude → 監査エージェント → まこさん GO の 4 段構造
- ガード G: 生データ独立再集計 (CC はパス・sha256・行数のみ報告)

## 出力成果物

1. `results/exchange_api/bitget_contracts_btcusdt_20260520.json`
2. `results/exchange_api/bitget_funding_history_30d_raw.json`
3. `results/exchange_api/bitget_funding_history_30d.csv`
4. `results/exchange_api/bitget_funding_history_30d_stats.json`
5. `results/exchange_api/screenshots/README.md`
6. `exchange_spec.md` (更新版)
7. 完了報告 md

発行日: 2026-05-20
