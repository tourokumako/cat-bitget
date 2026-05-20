# exchange_spec.md — Bitget 発注仕様・安全基準

## Bitget USDT-FUTURES BTCUSDT スペック (一次ソース・2026-05-13確定)

### 手数料

| 種別 | 適用値 | 標準値 | 備考 |
|---|---|---|---|
| Maker fee | 0.014% (0.00014) ✅ まこさん発注画面確認 (2026-05-20) | 0.02% (0.0002) ✅ contracts API `makerFeeRate` (2026-05-20・audit#19) | BGB割引等適用後・剥落で標準復帰 |
| Taker fee | 0.042% (0.00042) ✅ まこさん発注画面確認 (2026-05-20) | 0.06% (0.0006) ✅ contracts API `takerFeeRate` (2026-05-20・audit#19) | 同上 |

### 注文単位

| 項目 | 値 |
|---|---|
| 最小注文サイズ (quantityMultiplier) | 0.0001 BTC ✅ contracts API `minTradeNum`+`sizeMultiplier` (2026-05-20・audit#19) |
| 最小注文額 (minOrderAmount) | 5 USDT ✅ contracts API `minTradeUSDT` (2026-05-20・audit#19) |
| Tick size (priceMultiplier) | 0.1 USDT ✅ contracts API `priceEndStep`=1, `pricePlace`=1 → 10^(-1) × 1 = 0.1 USDT (2026-05-20・audit#19) |

### Funding

| 項目 | 値 |
|---|---|
| 精算間隔 (fundInterval) | 8 時間 ✅ contracts API `fundInterval`=8 + Bitget Beginner's Guide |
| 精算時刻 (UTC) | 00:00 / 08:00 / 16:00 ✅ Bitget Beginner's Guide |
| 精算時刻 (JST) | 09:00 / 17:00 / 翌01:00 |
| **Funding rate (実測 30 日 2026-04-20〜2026-05-20 UTC)** | mean=-0.000208%/8h / median=0.0002%/8h / p05=-0.0141% / p25=-0.0052% / p75=0.0063% / p95=0.0100% / min=-0.0198% / max=0.0100% / count=91 ✅ history-fund-rate API (2026-05-20・audit#19・sha256:3be5d64c) |
| Funding rate — Phase 5-e 運用設計 | **p50 (0.0002%/8h) を baseline、p95 (0.01%/8h) を stress test** (旧「0.01% 一律固定」は削除・2026-05-20 まこさん承認) |

### 制限・運用

| 項目 | 値 |
|---|---|
| マージンモード | isolated (hedge_mode 維持) ✅ contracts API `supportMarginCoins`=['USDT'] + V9 SDK `marginMode=isolated` 動作確認済 (2026-05-20・audit#19) |
| 最大レバレッジ | **150x** ✅ contracts API `maxLever`=150 (2026-05-20・audit#19) — ⚠️ 旧記述 125x は誤り・訂正済 |
| 最大同時保有数 (maxPositionNum) | **150** ✅ contracts API `maxPositionNum`=150 (2026-05-20・audit#19) — ⚠️ 旧記述 200 は誤り・訂正済 |
| 定期メンテナンス | なし (24/7 取引) ✅ 公式ガイド「中断のない年中無休の取引」(Bitget 株式無期限先物完全ガイド・2026-01-08・2026-05-20 まこさん確認) |

> 個別アナウンスは Support > Maintenance (https://www.bitget.com/support/sections/12508313404950) を都度確認。Bot 起動時は最新アナウンス取得を実装に含める (Phase 7-c 要件)。
> ⚠️ **削除した旧記述「火/水/木 05:00-08:00 UTC」は出典なき Claude 想定値だった (2026-05-20 発覚・L-196 参照)**

### 出典 (項目別)

| 項目 | 出典 | 状態 |
|---|---|---|
| Maker/Taker 適用値 | まこさん発注画面確認 (2026-05-20) | ✅ verify 済 |
| Maker/Taker 標準値 | contracts API `makerFeeRate`/`takerFeeRate` (2026-05-20・audit#19・sha256:e556b6) + まこさんスクショ取得待ち (Step 3 独立確認用) | ✅ API verify 済・スクショ取得待ち |
| 最小注文 (0.0001 BTC) | contracts API `minTradeNum`=0.0001, `sizeMultiplier`=0.0001 (2026-05-20・audit#19) | ✅ verify 済 |
| 最小注文額 (5 USDT) | contracts API `minTradeUSDT`=5 (2026-05-20・audit#19) | ✅ verify 済 |
| Tick size (0.1 USDT) | contracts API `priceEndStep`=1, `pricePlace`=1 → 0.1 USDT (2026-05-20・audit#19) | ✅ verify 済 |
| 最大レバ **150x** (旧 125x 訂正) | contracts API `maxLever`=150 (2026-05-20・audit#19) | ✅ verify 済・旧値訂正 |
| マージンモード isolated | contracts API `supportMarginCoins`=['USDT'] + V9 SDK 動作確認 (2026-05-20・audit#19) | ✅ verify 済 |
| 最大同時保有 **150** (旧 200 訂正) | contracts API `maxPositionNum`=150 (2026-05-20・audit#19) | ✅ verify 済・旧値訂正 |
| Funding 8h 間隔 | Bitget Beginner's Guide — Understanding Futures Fees / Funding Rate + contracts API `fundInterval`=8 | ✅ verify 済 |
| Funding rate 実測分布 | history-fund-rate API 91 intervals 2026-04-20〜05-20 (audit#19・sha256:3be5d64c) | ✅ verify 済 |
| 取引時間 24/7 | 公式ガイド Bitget 株式無期限先物完全ガイド (2026-01-08・2026-05-20 まこさん確認) | ✅ verify 済 |
| 定期メンテ (旧記述) | ⛔ Claude 想定値・削除済 (2026-05-20・L-196 参照) | ⛔ |
| posLimit 0.2 | v1 docs HTML: "percentage of positions by single trader" = OI 比率 (2026-05-20・audit#19 followup) / 注記: Bitget Support 記事「Platform OI × 0.5 × ratio threshold = 10%」は Cloudflare ブロックで独立 confirm 不可 (audit#19 監査報告・2026-05-20) / 我々 0.12 BTC は <<0.001% OI で完全非バインディング | ✅ verify 済 |
| buyLimitPriceRatio 0.05 | v1 docs HTML: "Buy price limit ratio" = マーク価格±5% 以内 (2026-05-20・audit#19 followup) | ✅ verify 済 |
| sellLimitPriceRatio 0.05 | v1 docs HTML: "Sell price limit ratio" = マーク価格±5% 以内 (2026-05-20・audit#19 followup) | ✅ verify 済 |
| feeRateUpRatio 0.005 | v1 docs HTML: "Rate of increase in handling fee, 0.005 means 0.5%" (2026-05-20・audit#19 followup) | ✅ verify 済 |
| openCostUpRatio 0.01 | v1 docs HTML: "Percentage of increase in opening cost, 0.01 means 1%" (2026-05-20・audit#19 followup) | ✅ verify 済 |
| maxMarketOrderQty 220 | 単一マーケット注文最大量 220 BTC (Go SDK struct + web search・2026-05-20・audit#19 followup) | ✅ verify 済 |
| maxOrderQty 1200 | 単一指値注文最大量 1200 BTC (Go SDK struct + web search・2026-05-20・audit#19 followup) | ✅ verify 済 |
| maxSymbolOrderNum 200 | BTCUSDT 同時アクティブ注文数上限 200 件 (web search Bitget FAQ・2026-05-20・audit#19 followup) | ✅ verify 済 |
| maxProductOrderNum 1000 | USDT-FUTURES 全体同時注文数上限 1000 件 (web search Bitget FAQ・2026-05-20・audit#19 followup) | ✅ verify 済 |

---

## contracts API 追加フィールド（audit#19 follow-up・2026-05-20 確定）

| フィールド | 値 | 意味 | 単位 | 設計影響 |
|---|---|---|---|---|
| posLimit | 0.2 | V1 docs: 単一トレーダーの OI 保有率上限 (20%) / 注記: Support 記事「OI×0.5×ratio=10%」は Cloudflare ブロックで独立 confirm 不可 | OI 比率 | 0.12 BTC は 20%/10% いずれでも完全非バインディング (<<0.001% OI) |
| maxMarketOrderQty | 220 | 単一マーケット注文の最大数量 | BTC | 非バインディング (close 0.12 BTC << 220 BTC) |
| maxOrderQty | 1200 | 単一指値注文の最大数量 | BTC | 非バインディング (entry 0.024 BTC << 1200 BTC) |
| maxSymbolOrderNum | 200 | BTCUSDT 同時アクティブ注文数上限 | 件数 | 非バインディング (最大 3 件程度) |
| maxProductOrderNum | 1000 | USDT-FUTURES 全体同時注文数上限 | 件数 | 非バインディング |
| buyLimitPriceRatio | 0.05 | 買い指値のマーク価格からの最大乖離 | 比率 | 非バインディング (±0.01% << 5%) |
| sellLimitPriceRatio | 0.05 | 売り指値のマーク価格からの最大乖離 | 比率 | 非バインディング (±0.01% << 5%) |
| feeRateUpRatio | 0.005 | 手数料増加係数（ペナルティ時） | 比率 (0.5%) | 通常運用で非発動 |
| openCostUpRatio | 0.01 | 開設コスト増加係数（ペナルティ時） | 比率 (1%) | 通常運用で非発動 |

> F1-F8 は全て非バインディング。Phase 7-d 着手前 posLimit 確認済 ✅  
> 詳細分析: `results/exchange_api/api_docs/field_meaning_verify.md`

---

## 安全装置（2重ガード）

| 装置 | 場所 | 制御者 |
|------|------|--------|
| `ALLOW_LIVE_ORDERS = False` | run_once_v9.py | ユーザーのみ変更可 |
| `paper_trading` フラグ | config/bitget_keys.json | ユーザーのみ変更可 |

## 指値エントリー仕様

- LONG:  `limit_price = close × (1 - 0.0001)`
- SHORT: `limit_price = close × (1 + 0.0001)`
- TTL: 3本（15分）、期限切れは必ずキャンセル API を呼ぶ
- 同一 side の pending が存在する間は追加発注しない

## TP / SL 発注仕様

- TP: `placePosTpsl`（指値・Maker）、ENTRY約定後すぐに設定
- SL: `placePosTpsl`（指値）、add_count=2 以上になった時点で設定
- TP/SL の execute_price = trigger_price（Maker 確保）

## 動的 TP 計算（V9準拠）

- `TP_FEE_FLOOR_ENABLE=1`: 手数料分を TP に上乗せ
- `TP_ADX_BOOST_ENABLE=1`: ADX が高いとき TP を拡大
- `TP_PCT_CLAMP_ENABLE=1`: TP の上限をクランプ
- 実効 tp_pct は `TPSL_CTX` イベントとして JSON ログに必ず出力する

## クローズ仕様

- 能動クローズ: `close_market_order()`（マーケット）
- CLOSE直前に pos 再照会、ゼロなら NO_POSITION で正常終了
- CLOSE後に pos 再照会、残存があれば EXIT_PENDING で終了

## Place Order API（指値エントリー用）

- Endpoint: POST /api/v2/mix/order/place-order
- Rate limit: 10 req/s/UID
- ポジションモード: hedge_mode（tradeSide: "open" 必要）

### V9 指値エントリーで使うパラメータ

| パラメータ | 値 |
|-----------|-----|
| symbol | BTCUSDT |
| productType | USDT-FUTURES |
| marginMode | isolated |
| marginCoin | USDT |
| size | 0.024 |
| price | close × (1 - 0.0001) LONG / close × (1 + 0.0001) SHORT |
| side | buy（LONG）/ sell（SHORT） |
| orderType | limit |
| force | post_only（maker保証。成行約定になる場合は自動キャンセル） |
| clientOid | 任意ID（追跡用） |

### Response
- `orderId`: キャンセル・照会に使う
- `code`: "00000" 以外はエラー → STOP

## Get Candlestick Data

- Endpoint: GET /api/v2/mix/market/candles
- Rate limit: 20 req/s（IP）
- granularity: 5m / limit: 最大1000（デフォルト100）

### Response（配列の配列）
| index | 内容 |
|-------|------|
| [0] | timestamp（ms） |
| [1] | open |
| [2] | high |
| [3] | low |
| [4] | close |
| [5] | 出来高（base coin） |
| [6] | 出来高（quote coin） |

## Get Mark/Index/Market Prices

- Endpoint: GET /api/v2/mix/market/symbol-price
- Rate limit: 20 req/s（UID）

### Response（sanity guard 用）
| フィールド | 内容 |
|-----------|------|
| price | 最終約定価格（last） |
| markPrice | マーク価格 |
| indexPrice | インデックス価格 |

- sanity guard: `markPrice` と `price` の乖離が 3% 超 → STOP

## Get Pending Orders

- Endpoint: GET /api/v2/mix/order/orders-pending
- Rate limit: 10 req/s/UID
- hedge_mode では `posSide=long`（LONG）/ `posSide=short`（SHORT）
- `status=live` でフィルタ可能（未約定のみ取得）

### pending_entry 確認用クエリ
- `orderId` または `clientOid` を指定して単一注文の生存確認
- `status=live` かつ `symbol=BTCUSDT` で一覧取得も可

## Cancel Order

- Endpoint: POST /api/v2/mix/order/cancel-order
- Rate limit: 10 req/s

### 必須パラメータ
| パラメータ | 値 |
|-----------|-----|
| symbol | BTCUSDT |
| productType | USDT-FUTURES |
| orderId | Place Order で取得した ID |

- `code` が "00000" 以外 → STOP（キャンセル失敗）

## Get Order Detail

- Endpoint: GET /api/v2/mix/order/detail
- Rate limit: 10 req/s（UID）

### 約定確認で使うフィールド
| フィールド | 内容 |
|-----------|------|
| **state** | `live` / `partially_filled` / `filled` / `canceled` |
| baseVolume | 約定済み数量 |
| priceAvg | 平均約定価格 |

- 注意: フィールド名は `state`（`status` ではない）

## Get Single Position

- Endpoint: GET /api/v2/mix/position/single-position
- Rate limit: 10 req/s/UID
- ポジションなしのとき: 空配列 `[]` が返る

### V9 で使うフィールド
| フィールド | 内容 |
|-----------|------|
| total | 総保有量（available + locked） |
| holdSide | `long` / `short` |
| openPriceAvg | 平均エントリー価格 |
| unrealizedPL | 含み損益 |
| markPrice | マーク価格 |
| takeProfit | TP価格（設定済みなら） |
| stopLoss | SL価格（設定済みなら） |
| takeProfitId | TP注文ID |
| stopLossId | SL注文ID |

- EXIT判定: `total == 0` または空配列 → ポジションなし

## Place TP/SL Order（placePosTpsl）

- Endpoint: POST /api/v2/mix/order/place-tpsl-order
- Rate limit: 10 req/s（UID）

### V9 での使い方
| パラメータ | TP | SL |
|-----------|-----|-----|
| planType | `pos_profit` | `pos_loss` |
| triggerType | `mark_price` | `mark_price` |
| triggerPrice | TP発動価格 | SL発動価格 |
| executePrice | triggerPrice と同値（limit・maker確保） |
| holdSide | `long`（LONG）/ `short`（SHORT）※hedge_mode |
| size | 不要（pos_profit/pos_loss は省略可） |

- `pos_profit` / `pos_loss`: ポジション全体に対する TP/SL（size 不要）
- executePrice = triggerPrice → 指値執行（maker確保）
- `code` が "00000" 以外 → STOP

## Demo Trading

- REST: 本番と同じエンドポイント。ヘッダーに `paptrading: 1` を追加するだけ
- Demo API Key は本番とは別に作成が必要（Demo モードの Personal Center で作成）
- `bitget_adapter.py` で `paper_trading=True` のとき、このヘッダーが付いているか確認必須

## 禁止値・異常検知

- spread > 1% または mark-last > 3% → STOP（market_sanity guard）
- bid/ask/mark がゼロ以下 → STOP
- TP/SL 設定失敗（code≠00000）→ STOP