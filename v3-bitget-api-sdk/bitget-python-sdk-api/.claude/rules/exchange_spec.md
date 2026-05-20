# exchange_spec.md — Bitget 発注仕様・安全基準

## Bitget USDT-FUTURES BTCUSDT スペック (一次ソース・2026-05-13確定)

### 手数料

| 種別 | 適用値 | 標準値 | 備考 |
|---|---|---|---|
| Maker fee | 0.014% (0.00014) ✅ まこさん発注画面確認 (2026-05-20) | ⚠️ 0.02% (0.0002) — 出典未確認・Claude 想定値・stress test 用暫定使用・audit#19 対象 | BGB割引等適用後・剥落で標準復帰 |
| Taker fee | 0.042% (0.00042) ✅ まこさん発注画面確認 (2026-05-20) | ⚠️ 0.06% (0.0006) — 出典未確認・Claude 想定値・stress test 用暫定使用・audit#19 対象 | 同上 |

### 注文単位

| 項目 | 値 |
|---|---|
| 最小注文サイズ (quantityMultiplier) | 0.0001 BTC |
| 最小注文額 (minOrderAmount) | 5 USDT |
| Tick size (priceMultiplier) | 0.1 USDT |

### Funding

| 項目 | 値 |
|---|---|
| 精算間隔 (fundInterval) | 8 時間 |
| 精算時刻 (UTC) | 00:00 / 08:00 / 16:00 |
| 精算時刻 (JST) | 09:00 / 17:00 / 翌01:00 |

### 制限・運用

| 項目 | 値 |
|---|---|
| マージンモード | isolated (hedge_mode 維持) |
| 最大レバレッジ | 125x (v2 API) |
| 最大同時保有数 (maxPositionNum) | 200 |
| 定期メンテナンス | なし (24/7 取引) ✅ 公式ガイド「中断のない年中無休の取引」(Bitget 株式無期限先物完全ガイド・2026-01-08・2026-05-20 まこさん確認) |

> 個別アナウンスは Support > Maintenance (https://www.bitget.com/support/sections/12508313404950) を都度確認。Bot 起動時は最新アナウンス取得を実装に含める (Phase 7-c 要件)。
> ⚠️ **削除した旧記述「火/水/木 05:00-08:00 UTC」は出典なき Claude 想定値だった (2026-05-20 発覚・L-196 参照)**

### 出典 (項目別)

| 項目 | 出典 | 状態 |
|---|---|---|
| Maker/Taker 適用値 | まこさん発注画面確認 (2026-05-20) | ✅ verify 済 |
| Maker/Taker 標準値 | ⚠️ 出典なし・Claude 想定値 | ⚠️ audit#19 対象 |
| 最小注文 / 最小注文額 / Tick size / 最大レバ / マージンモード / 最大同時保有 | 公式 API `GET /api/v2/mix/market/contracts` (response 例保存未実施) | ⚠️ audit#19 対象 |
| Funding 8h 間隔 | Bitget Beginner's Guide — Understanding Futures Fees / Funding Rate | ✅ verify 済 |
| Funding 0.01% rate | ⚠️ phase_compliance L13 暫定値・出典なし | ⚠️ audit#19 対象 |
| 取引時間 24/7 | 公式ガイド Bitget 株式無期限先物完全ガイド (2026-01-08・2026-05-20 まこさん確認) | ✅ verify 済 |
| 定期メンテ (旧記述) | ⛔ Claude 想定値・削除済 (2026-05-20・L-196 参照) | ⛔ |

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