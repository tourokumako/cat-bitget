# test_checklist.md — V9 フェーズ別テストリスト

---

## テスト大前提（最優先ルール）

**このテストの目的: 本番で事故なく安全にBOT運用するため、本番リリース前にデモ環境で実際の動作を確認する。**

- 全 S-x テストは **`ALLOW_LIVE_ORDERS=True` + `paper_trading=true`** での実API実行が必須
- `ALLOW_LIVE_ORDERS=False`（DRY_RUN）で取得したログはテスト証跡として認めない
  - DRY_RUNは発注・キャンセル・TP設定のAPIを一切叩かないため、本番安全性の証明にならない
  - ログイベントが出ていても「コードが動いた」だけで「Bitget APIが正しく動いた」の証明にはならない
- GET系（ポジション照会・価格取得）は ALLOW_LIVE_ORDERS に依らず実API。これは有効

---

## テスト証跡ルール

テスト項目の合格は以下の形式でこのファイルに記録する。**記録なしは未実施扱い。**

```
✅ [テスト番号] 実施日時
   pre:  実行前の状態（ファイル有無・orderId等）
   run:  python runner/run_once_v9.py（ALLOW_LIVE_ORDERS=True）
   log:  ターミナル出力からのコピペ（要約不可・必須）
         例: {"event":"ENTRY_CONFIRMED","orderId":"xxx","filled_size":0.024}
   post: 実行後の状態（ファイル有無・取引所残骸有無）
```

- `log:` は必ずターミナル出力からのコピペ。「ログで確認しました」という要約は不合格
- 合格定義に書かれたイベント・フィールドが全て揃っていない場合は ❌ 不合格

---

## 0) Gate（このrunは信用できるか）

H-0｜実行モード＆強制判断混入なし
- [◯] 実行モード（paper/live/decision_only等）がログで宣言されている
- [◯] decision_override の有効/無効がログで宣言されている
- [◯] override が有効なのは意図したテスト時のみ
- [◯] pending_entry.json の有無がログで宣言されている
- [◯] open_position.json の有無がログで宣言されている

---

## 1) PARAM Parity Harness

H-1｜パラメータ読み込みの証跡
- [◯] cat_params_v9.json を読み込んだ事実がログで確認できる（1runで1回）
- [◯] 読み込まれた値がログで特定できる（少なくとも重要キー群）

H-2｜必須キー欠落なし（Fail-fast）
- [◯] cat_params_v9.json の全必須キーが存在する
- [ ] 型が正しい（int/float/bool/dict）
- [ ] cat_params_v9.json から必須キーを1つ削除してrunし、STOPログが出て処理が続行されないことを確認する（黙って既定値で続行しない）

    H-3｜判定で参照した値の証跡
    - [◯] ENTER時にpriority別の参照パラメータ値が追える（ENTRY_DECISION: side/priority/adx/material）
    - [ ] EXIT時にexit_reason別の参照値が追える

    H-4｜注文で送った値の証跡
    - [◯] ENTRY_SEND に limit_price / size が出ている
    - [◯] TP_LIMIT_SEND に triggerPrice / executePrice / position_size が出ている（SLはadd_count≥2時のみ）
    - [◯] TP_LIMIT_SEND に planType=pos_profit がログで確認できる
    - [◯] TP注文の executePrice が triggerPrice と一致している（指値確保）がログで確認できる
    - [ ] TP_LIMIT_SEND に holdSide がログで出ており、open_position の side（long/short）と一致している
    - [ ] CLOSE_SEND にクローズ数量が出ている
    - [ ] CLOSE_VERIFY で完結が追える

    H-5｜動的TP計算の証跡
    - [◯] TP_FEE_FLOOR_ENABLE / TP_ADX_BOOST_ENABLE の適用がログで追える（TPSL_CTX: fee_applied/boost_applied）
    - [◯] 実効 tp_pct（boost/clamp後）がログに出ている（TPSL_CTX: effective_tp_pct）

    H-TPX｜TP再設定整合
    - [◯] ポジションサイズ変化時（add後）にTP再計算されログで追える（ADD_CONFIRMED: tp/position_size）
    - [ ] 再設定の場合、TP_CANCELLED → TP_LIMIT_SEND の順がログで確認できる（cancelのAPIレスポンスcode=00000を確認してからsendする）
    - [ ] TP_CANCELLED は成功したが TP_LIMIT_SEND が失敗した場合、STOP（TPなしポジション不可）でログにCRITICALが出る
    - [ ] cancel完了確認前に新TPを送信しない（2重pos_profit送信が起きない）

---

## 1.5) hedge_mode 固有確認

H-HM1｜ENTRY発注に `tradeSide: "open"` が含まれること
- [◯] ENTRY発注の order detail レスポンスに `tradeSide: "open"` / `posMode: "hedge_mode"` が含まれること（2026-03-22 セッション11: 実API確認）

H-HM2｜TP/SL設定の `holdSide` が open_position の side と一致すること
- [◯] TP_LIMIT_SEND ログの `hold_side` が open_position の side（long/short）と一致すること（2026-03-22 セッション11: hold_side=long / side=LONG 確認）
- [◯] 取引所の plan order レスポンスに `posSide: "long"/"short"` が含まれ、open_position の side と一致すること（2026-03-22 セッション11: posSide=long 確認）

H-HM3｜能動クローズが `close-positions` エンドポイントを使っていること
- [◯] CLOSE_SEND が `closePositions` API（`/api/v2/mix/order/close-positions`）を呼び、`holdSide` を指定していること（2026-03-22 セッション10: S-8で確認済み）

H-HM4｜取引所上で LONG/SHORT 同時保有が発生しないこと
- [◯] 毎回の取引所ポジション照会でLONG保有中にSHORTが存在しないこと（2026-03-22 セッション11: 複数run通じてLONGのみ確認）
- [◯] H-HM5: LONG保有中にSHORTシグナルが出た場合、`pos_side_mismatch` NOOP が実API で確認できること（2026-03-22 セッション11: decision_override SHORT → NOOP: pos_side_mismatch: pos=LONG dec=SHORT 確認）

---

## 2) Safety Loop

S-0｜前提固定値
- [ ] LONG/SHORT_POSITION_SIZE_BTC=0.024 で動作している
- [ ] MAX_ADDS_BY_PRIORITY（P2=4, 他=5）が設計通り使われている
- [ ] 上記前提がコード/設定/ログで矛盾していない

S-1｜pending_entry 状態遷移
- [ ] pending_entry.json は ENTRY発注時のみ作られる
- [ ] 約定確認後に pending_entry.json が削除される
- [◯] TTL切れでキャンセル → pending_entry.json が削除される（2026-03-22 セッション12: PENDING_TTL_CANCEL code=00000 / PENDING_CLEARED:ttl_expired 確認）
- [ ] 同一sideで pending 中は追加発注しない
- [ ] API失敗時に pending_entry.json が中途半端に残らない
- [ ] 部分約定（partially_filled）でTTL切れキャンセルした場合、残存ポジションに対してTPが設定されるか、またはSTOPで停止する（部分ポジションのTPなし放置は不可）
- [ ] post_only拒否（Bitgetが即時taker約定のため自動キャンセル）時に pending_entry.json が削除され、次runで新規発注できる状態になる

S-2｜add状態遷移
- [ ] add_count は state/open_position.json にのみ保持
- [ ] add_count は約定確定時のみ +1 される
- [ ] EXIT完結時に add_count がリセットされる
- [ ] API失敗時に add_count が更新されない

S-3｜add上限制御
- [ ] P2 → add上限=4（MAX_ADDS_BY_PRIORITY）
- [ ] P4/P22/P23/P24 → add上限=5
- [ ] 上限到達時は ENTRY_SEND されず NOOP で終了
- [ ] NOOP時に「add上限による抑止」が説明できる

S-4｜SL発動タイミング
- [◯] 初回ENTRY約定後 → TPのみ設定（SLなし）（セッション6/7 実API確認）
- [◯] 1回目ADD約定後（add_count=2）→ SL設定追加（セッション7: sl_order_id=1419232714410180608 / code=00000）
- [ ] add_count≥3 時のSL更新有無が設計通りか確認（更新しない場合はその旨をコードコメントで明示、更新する場合は各addでSL再送信のテスト）

S-5｜open_position 整合性
- [◯] open_position は1サイド1状態（合算）として一貫している（セッション6/7 整合確認）
- [ ] ENTER途中/EXIT途中の中途半端な state が残らない
- [ ] 二重EXIT・未EXITが発生しない
- [ ] 再起動・例外後でも open_position が破綻しない
- [◯] S-RC①: open_position.json なし + 取引所ポジション残存 → `startup_reconciliation_failed` STOP が出て処理が続行されない（2026-03-22 セッション11 実API確認）
- [◯] S-RC②: open_position.json あり + 取引所ポジションなし → `startup_reconciliation_failed` STOP が出て処理が続行されない（2026-03-22 セッション11 実API確認）
- [ ] ポジション0かつtp_order_idが記録されている場合、run開始時にキャンセルAPIを呼びTP残骸を削除するか、残骸なしが取引所plan-orders APIで確認できる
- [ ] ポジションありのとき TP未設定状態が存在しない
- [◯] S-TP0: open_position.json に tp_order_id がない状態で起動した場合 → `tp_order_id_missing` STOP が出て処理が続行されない（2026-03-22 セッション11 実API確認）

S-6｜TP/SL計算
- [◯] ENTRY後に TP_LIMIT注文が必ず送信される（セッション6/7 TP_LIMIT_SEND code=00000確認）
- [◯] TP価格が entry_price と tp_pct から計算された値と一致する（セッション6/7 H-5 TPSL_CTX確認）
- [◯] TP size が現在のポジションサイズと一致する（セッション7 position_size=0.048確認）
- [◯] TP注文成功時に orderId がログ（TP_SET）・state（tp_order_id）に記録される（セッション7 tp_order_id=1419120854935564288）
- [◯] run開始時に tp_order_id を使い取引所のplan orderリストを照会し、TP実在を確認する（tp_order_idが記録されているのに取引所に存在しない場合はSTOP）（セッション8: TP_ORDER_MISSING_POS_GONE確認・planType=profit_loss）
- [◯] SLは add_count=2 が確定したrunで place-tpsl-order（pos_loss）がAPIに送信され、code=00000のレスポンスがログに記録される（セッション7確認）
- [◯] side方向（LONG/SHORT）が正しい（セッション7 LONG確認）

S-7｜Exit判定（優先順位）
- [◯] TP外部約定（最優先）→ EXIT（検知: single-position.total==0 かつ tp_order_idが取引所上にない）（セッション8: EXIT_EXTERNAL/TP_OR_SL_HIT確認・open_position.json削除確認 ※mark_price反転時はTP_FILLED断定不可のためTP_OR_SL_HITが正常）
- [ ] SL外部約定（add_count≥2）→ EXIT（exit_reason=SL_FILLEDがログで確認でき、TP_FILLEDと区別されている）
- [ ] BREAKOUT_CUT（P22/P23 SHORT add=3）→ EXIT
- [ ] MFE_EXIT（P22 SHORT）→ EXIT
- [ ] MFE_STALE_CUT（P22 SHORT add=5）→ EXIT
- [ ] MAE_CUT（P23 SHORT add≥4）→ EXIT
- [ ] PROFIT_LOCK（LONG / P22_SHORT）→ EXIT
- [ ] RSI逆行 Exit(SHORT)→ EXIT
- [ ] TIME_EXIT は最後
- [ ] 優先順位が崩れていない

S-8｜能動クローズ完結性
- [ ] CLOSE_SEND が出る
- [ ] CLOSE_VERIFY で完結が追える
- [ ] クローズ後に open_position が削除される
- [ ] CLOSE失敗時に state が壊れない
- [ ] CLOSE完結後、取引所上のTP/SL plan orderが削除されている（plan-orders APIで残骸ゼロ確認）

S-9｜異常系（API失敗・例外・累積失敗）
- [ ] 同一足で多重発火・多重決済がない
- [ ] 例外・API失敗時に state が中途半端に更新されない（発注API失敗 → pending_entry.json未作成、state更新なし）
- [ ] TP/SL送信API失敗時に state が中途半端に更新されない（tp_order_id未記録のままSTOP）
- [ ] add_count更新API失敗時に open_position.json が更新されない（アトミック更新）
- [ ] API失敗（market_data取得含む）が連続N回（設計値: ___回）以上続いた場合、新規判断を停止しSTOPログが出る（古い価格で誤判断しない）

---

## 2.5) 各テスト合格定義（実API証跡必須）

以下の各テストは `ALLOW_LIVE_ORDERS=True` + `paper_trading=true` での実行が必須。
合格時は証跡ルールの形式でこのファイルに記録する。

---

### S-0 合格定義

| 項目 | 内容 |
|------|------|
| 実行 | `python runner/run_once_v9.py`（ALLOW_LIVE_ORDERS=True） |
| 必須ログ | `event=PARAMS_LOADED` に `size=0.024` / `MAX_ADDS_BY_PRIORITY` が含まれること |
| 合格 | ログ値が cat_params_v9.json の値と一致している |
| 不合格 | PARAMS_LOADEDイベントが出ない / 値が食い違う |

---

### S-1① 合格定義（ENTRY発注時のみpending作成）

| 項目 | 内容 |
|------|------|
| 前提 | pending_entry.json なし、ポジションなし、ENTRYシグナルが出る状態 |
| 実行 | `python runner/run_once_v9.py`（ALLOW_LIVE_ORDERS=True） |
| 必須ログ | `event=ENTRY_SEND` に `orderId` / `limit_price` / `size` が含まれること |
| 必須ログ | `event=PENDING_WRITTEN` に `orderId` が含まれること |
| 必須API | Bitget `place-order` に対して `code=00000` のレスポンスがログに記録されていること |
| 必須状態 | 実行後に pending_entry.json が作成され orderId が記録されていること |
| 不合格 | ENTRY_SENDが出ない / code≠00000 / pending_entry.json が作られない |

---

### S-1② 合格定義（約定後にpending削除）

| 項目 | 内容 |
|------|------|
| 前提 | pending_entry.json 存在、Bitget上で当該注文が `filled` 状態 |
| 実行 | `python runner/run_once_v9.py`（ALLOW_LIVE_ORDERS=True） |
| 必須ログ | `event=ENTRY_CONFIRMED` に `orderId` / `filled_size` / `avg_price` が含まれること |
| 必須状態 | 実行後に pending_entry.json が消えていること（`ls state/` で確認） |
| 必須状態 | open_position.json が作成または更新されていること |
| 不合格 | ENTRY_CONFIRMEDが出ない / pending_entry.json が残存 |

---

### S-1③ 合格定義（TTL切れキャンセル）

| 項目 | 内容 |
|------|------|
| 前提 | pending_entry.json 存在、bar_elapsed が TTL（3本）を超えている |
| 実行 | `python runner/run_once_v9.py`（ALLOW_LIVE_ORDERS=True） |
| 必須ログ | `event=PENDING_TTL_CANCEL` が出ていること |
| 必須API | Bitget `cancel-order` に対して `code=00000` のレスポンスがログに記録されていること |
| 必須状態 | 実行後に pending_entry.json が消えていること |
| 不合格 | キャンセルAPIが叩かれない / code≠00000 / pending_entry.json が残存 |

✅ S-1③ 2026-03-22 セッション12
   pre:  open_position.json(LONG/add_count=1) / pending_entry.json なし
   run:  decision_override ENTER LONG → ENTRY_SEND → placed_bar_time=0に改竄 → python runner/run_once_v9.py
   log:  {"event":"PENDING_STATUS","state":"live","bar_elapsed":5913849,"ttl":3}
         cancel-order response: {"code":"00000","data":{"orderId":"1419473873795121153"}}
         {"event":"PENDING_TTL_CANCEL","order_id":"1419473873795121153","bar_elapsed":5913849}
         {"event":"PENDING_CLEARED","reason":"ttl_expired"}
   post: pending_entry.json 消滅確認 / open_position.json 正常
   note: TTLキャンセル後にPARTIAL_FILL_TP_SETが誤発火するバグを同時発見・修正
         （remaining_sz > 0 → remaining_sz > existing_sz）

---

### S-1⑥ 合格定義（部分約定TTL切れ後のTP設定）

| 項目 | 内容 |
|------|------|
| 前提 | pending_entry.json 存在、Bitget上の注文が `partially_filled`、TTL超過 |
| 実行 | `python runner/run_once_v9.py`（ALLOW_LIVE_ORDERS=True） |
| 必須ログ | `event=PARTIAL_FILL_TP_SET` が出ていること |
| 必須API | `place-tpsl-order` に対して `code=00000` のレスポンスがログに記録されていること |
| 不合格 | TP設定なしでポジション放置 / STOP ログなしに処理継続 |

---

### S-6 TP_VERIFY 合格定義（run開始時のTP実在確認）

| 項目 | 内容 |
|------|------|
| 前提 | open_position.json に `tp_order_id` が記録済み |
| 実行 | `python runner/run_once_v9.py`（ALLOW_LIVE_ORDERS=True） |
| 必須ログ | `event=TP_ORDER_VERIFIED` に `tp_order_id` が含まれること（TP消滅＋ポジション消滅時は `event=TP_ORDER_MISSING_POS_GONE`） |
| 必須API | Bitget plan-orders 照会APIが叩かれレスポンスがログに記録されていること |
| 不合格 | TP_VERIFYイベントが出ない |

---

### S-7① 合格定義（TP外部約定 EXIT検知）

| 項目 | 内容 |
|------|------|
| 前提 | ポジション保有中、Bitget上でTP約定済み（single-position.total=0） |
| 実行 | `python runner/run_once_v9.py`（ALLOW_LIVE_ORDERS=True） |
| 必須ログ | `event=EXIT_EXTERNAL` に `exit_reason=TP_FILLED` または `TP_OR_SL_HIT` が含まれること（runner未稼働中にTP約定しmark_priceが反転した場合はTP_OR_SL_HITが正常） |
| 必須状態 | 実行後に open_position.json が削除されていること |
| 不合格 | EXIT_EXTERNALが出ない / open_position.json が残存 |

### S-7② 合格定義（SL外部約定 EXIT検知）

| 項目 | 内容 |
|------|------|
| 前提 | ポジション保有中（add_count≥2）、Bitget上でSL約定済み |
| 実行 | `python runner/run_once_v9.py`（ALLOW_LIVE_ORDERS=True） |
| 必須ログ | `event=EXIT_EXTERNAL` に `exit_reason=SL_FILLED` が含まれること（TP_FILLEDと区別） |
| 必須状態 | 実行後に open_position.json が削除されていること |
| 不合格 | exit_reason がSL_FILLEDでない / TP_FILLEDと区別されていない |

---

### S-TP0 合格定義（tp_order_id 欠損 → STOP）

| 項目 | 内容 |
|------|------|
| 前提 | open_position.json に `tp_order_id: null` または `tp_order_id` キーなしで存在する状態 |
| 実行 | `python runner/run_once_v9.py`（ALLOW_LIVE_ORDERS=True） |
| 必須ログ | `event=STOP` に `reason=tp_order_id_missing` が含まれること |
| 必須状態 | run がそこで終了し、ENTRY_SEND / CLOSE_SEND が出ないこと |
| 不合格 | STOP が出ない / TP未設定のまま続行する |

---

### S-RC 合格定義（startup reconciliation: stateと取引所ポジの整合確認）

両方向のシナリオをそれぞれ実API で確認すること。

#### S-RC① stateなし + 取引所ポジあり

| 項目 | 内容 |
|------|------|
| 前提 | open_position.json なし、かつ Bitget デモ口座に実ポジションが存在する状態 |
| 実行 | `python runner/run_once_v9.py`（ALLOW_LIVE_ORDERS=True） |
| 必須ログ | `event=STOP` に `reason=startup_reconciliation_failed` が含まれること |
| 必須ログ | reason に exchange 側の `side` / `size` が含まれること |
| 必須状態 | run がそこで終了し、ENTRY_SEND が出ないこと |
| 不合格 | STOP が出ない / ENTRY_SEND が出る / reason に side/size がない |

#### S-RC② stateあり + 取引所ポジなし

| 項目 | 内容 |
|------|------|
| 前提 | open_position.json あり、かつ Bitget デモ口座にポジションが存在しない状態 |
| 実行 | `python runner/run_once_v9.py`（ALLOW_LIVE_ORDERS=True） |
| 必須ログ | `event=STOP` に `reason=startup_reconciliation_failed` が含まれること |
| 必須ログ | reason に open_position.json の `side` / `size` が含まれること |
| 必須状態 | run がそこで終了し、ENTRY_SEND が出ないこと |
| 不合格 | STOP が出ない / ENTRY_SEND が出る / reason に side/size がない |

**備考:** DRY_RUN（ALLOW_LIVE_ORDERS=False）時はこのチェックがスキップされる設計。テストは必ず ALLOW_LIVE_ORDERS=True で実施すること。
S-RC② は bot 停止中に TP/SL 約定した場合も該当する。STOP 後はユーザーが open_position.json を確認・削除してから再起動する。

---

### S-8 合格定義（能動クローズ完結性）

| 項目 | 内容 |
|------|------|
| 前提 | 能動クローズ条件成立（BREAKOUT_CUT / TIME_EXIT 等） |
| 実行 | `python runner/run_once_v9.py`（ALLOW_LIVE_ORDERS=True） |
| 必須ログ | `event=CLOSE_SEND` にクローズ数量が含まれること |
| 必須ログ | `event=CLOSE_VERIFY` でクローズ完結が確認できること |
| 必須API | Bitget close-order に対して `code=00000` のレスポンスがログに記録されていること |
| 必須状態 | open_position.json が削除されていること |
| 必須状態 | 取引所上のTP/SL plan orderが削除されていること（plan-orders APIで残骸ゼロ確認） |
| 不合格 | CLOSE_VERIFYが出ない / open_position.jsonが残存 / plan order残骸あり |

---

## 3) Global

G-1｜優先度順エントリーの健全性
- [ ] 高priorityが成立しているのに低priorityが選ばれていない
- [ ] priority分布が極端に偏っていない（P2/P4/P22/P23/P24）

G-2｜取りこぼし検知
- [ ] entry_ok=true なのに ENTER が極端に少ない等の乖離がない

G-3｜飽和時の健全性
- [ ] add上限中は ENTER が抑止される
- [ ] EXIT後に add_count リセットされ再ENTER可能

G-4｜Entry↔Exit 対応
- [ ] ENTRY数とEXIT数が長期で釣り合う
- [ ] Exit理由の分布が極端でない（TIME_EXITばかり等）

G-5｜STOPは必ず理由つき
- [ ] STOP が出たら必ず reason が出ている

---

## 4) Observability

O-1｜priority別パフォーマンス
- [ ] priority別 ENTRY数（P2/P4/P22/P23/P24）
- [ ] priority別 ADD回数・平均保持時間・TP率・累積損益

O-2｜addの効き方
- [ ] add_count段階別（1st/2nd/…）の損益・TP率
- [ ] add上限到達後の NOOP 発生状況

O-3｜pending_entry の効率
- [ ] TTL切れ（未約定キャンセル）の発生率
- [ ] 約定までのbar数分布

O-4｜NOOPの内訳
- [ ] NOOP理由別カウント（add上限/条件未成立/Gate等）

O-5｜Entry→Exit 流れの追跡
- [ ] ENTRY時：priority / add_count / entry_time / limit_price
- [ ] EXIT時：exit_reason / holding_time
- [ ] run単位の簡易サマリが確認できる

---

## 5) Emergency Stop / Recovery

E-1｜停止手順
- [ ] 緊急停止を宣言したら、まず取引所上の open order / plan order / 実ポジション を確認する手順が文書化されている
- [ ] 手動停止後、open_position.json と取引所実ポジションの一致を確認する手順がある（乖離がある場合の対処フローも含む）

E-2｜停止時の取引所整理
- [ ] 緊急停止時、未約定のlimit orderをキャンセルするコマンド/手順が明確になっている
- [ ] 緊急停止時、残存するTP/SL plan orderをキャンセルする手順が明確になっている
- [ ] 手動キャンセル前後で、実ポジション size と open_position.json の size を照合する
- [ ] plan orderキャンセル後、bot側 state の tp_order_id / sl_order_id をどう扱うか（削除/再同期）が明確になっている
- [ ] 手動キャンセル後に孤立ポジション（TPなし）が残っていないことを確認する手順がある

E-3｜復旧条件
- [ ] 復旧前に pending_entry.json が残っていないことを確認する
- [ ] 復旧前に open order / plan order / open_position.json / pending_entry.json の4点整合を確認する
- [ ] 復旧前に open_position.json の state と取引所ポジションが一致していることを確認する
- [ ] 復旧前に孤立plan order（tp_order_idと不一致）がないことを確認する
- [ ] 復旧後の最初のrunは新規ENTRYを許可する前に整合チェックだけで終える運用が明確になっている
- [ ] 復旧後の最初のrunで、H-0〜H-2に加えて S-1 / S-5 / S-6 が通ることを確認する