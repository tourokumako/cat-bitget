# exchange_spec.md — Bitget 発注仕様・安全基準

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