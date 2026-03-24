# WORKFLOW.md — V9 移植 作業手順

## セッション開始時の確認事項（最優先）

| 項目 | 状態 |
|------|------|
| 現在のフェーズ | **Phase 2c-bis（デモ連続稼働テスト）— 進行中** |
| デモポジション | なし（クリーン）|
| 次のタスク | 24時間稼働確認 → trade_summary.py で集計確認 → Phase 4 へ |
| ALLOW_LIVE_ORDERS | True（テスト実行中。Claudeは変更しない） |
| open_position.json | なし（削除済み） |

---

## フェーズ一覧（2026-03-24 改訂）

> ⚠️ 旧フローは Logic Parity 未確認のまま Demo Run を進めていた。
> MFE_EXIT 未実装・MFE_STALE_CUT 条件逆転が発覚したため、下記順序に改訂。

| Phase | 名称 | ゲート条件（全て満たしてから次へ） |
|-------|------|----------------------------------|
| 0 | 環境準備 | ✅ 完了（2026-03-20） |
| 1 | デモ配線確認 | ✅ 完了（2026-03-21） |
| 2a | **Logic Parity** | A.関数呼び出し確認 + B.同一スナップショットで原本と移植版の判断一致 |
| 2b | Param Parity | 設定値が判断結果に実際に反映されていること（H-0〜H-5） |
| 2c | Demo Run | 全 Exit 条件（SL_FILLED 以外）がデモで動作確認済み |
| 3 | Safety / Observability | チェックリスト・異常系・監視設計 |
| 4 | 本番切り替え | Phase 3 完了後、ユーザーが手動で実施 |
| 5 | 常時稼働 | cron 設定・ログ監視 |

## 本番リリースフロー 設計方針

### なぜこの順序か

| ステップ | 目的 | スキップした場合のリスク |
|---------|------|------------------------|
| Logic Parity（2a） | 「一致してるか」の確認 | 間違ったロジックで本番を動かす |
| Param Parity（2b） | 「設定が効いてるか」の確認 | 設定値が判断に反映されない |
| Demo Run（2c） | 「発注・state変化」の確認 | 実発注フローの不具合を見逃す |
| Safety/Obs（3） | 「品質」の確認 | 異常時に止まれない |

### Logic Parity（Phase 2a）の具体的作業

1. **A. 関数呼び出し確認**（静的・コードレビューのみ）
   - `run_once_v9.py` が `cat_v9_decider.decide()` を実際に呼んでいるか
   - exit 判定が `cat_v9_decider` の関数を使っているか（ハードコードで代替していないか）

2. **B. 同一スナップショット比較**（動的・スクリプト作成）
   - 同じ OHLCV データを原本（CAT_v9_regime.py）と移植版（cat_v9_decider.py）に与える
   - entry 有無 / side / priority / exit 理由 が一致するか確認
   - 1 件でもズレたら修正してから次フェーズへ

### Exit Parity（Phase 2a-Exit）の具体的作業

Entry（check_entry_priority）は snapshot_compare.py で動的比較済み（200/200 MATCH）。
Exit（_check_exits）は状態累積・発動順序・保有時間でズレやすいため、以下の手順で別途確認する。

#### ステップ1: 目視再確認
- `run_once_v9.py _check_exits` と `cat_v9_regime_map.md` 原本18件を1件ずつ照合
- 明らかな条件ズレ・欠落を先に修正してからステップ2へ

#### ステップ2: Exit 動的比較スクリプト（tools/exit_compare.py）
- 固定OHLCV（fetch_snapshot.pyで取得済みデータ）+ 固定初期ポジションを使用
- 原本 run_backtest の exit ループ vs 移植版 _check_exits を逐次比較
- 各バーで mfe_max_usd を更新しながら exit_reason / 発動bar を記録・照合

**ケース設計方針:**
- Exit 種別ごとに「その条件を狙った固定ケース」を1件用意（1ケース1目的）
- 対象条件以外の Exit が先発動しないよう、価格・時間・状態を調整する
- 複数条件が競合するデータは使わない

**比較出力フォーマット（最低限）:**

| 項目 | 説明 |
|------|------|
| timestamp | 発動バーの timestamp |
| exit_reason | 原本 / 移植版それぞれの exit_reason |
| 発動bar | entry からの経過バー数 |
| mfe_max_usd | 発動時点の mfe_max_usd |
| holding_minutes | entry からの保有時間（分） |

#### ゲート条件（全て MATCH で Phase 2c へ）
- BREAKOUT_CUT（P22/P23 SHORT）
- MFE_STALE_CUT（P22 SHORT）
- MAE_CUT（P23 SHORT）
- PROFIT_LOCK（P22/P23 SHORT、LONG）
- TIME_EXIT（LONG / SHORT）
- STAGNATION_CUT

#### スコープ外
- SL_FILLED: 原本はバー終値判定、移植版は fill-history 照合（設計上の差異）
- EXIT_GUARD_FORCED: バックテスト専用フォールバック（原本 L1659）

---

### Logic Parity で原本と完全一致��ない既知の差異

| 項目 | 原本（バックテスト） | 移植版（Live） | 確認方針 |
|------|---------------------|--------------|---------|
| MFE 追跡 | bar-by-bar 最大値 | run 間で `mfe_max_usd` を累積 | 累積ロジックの単体確認 |
| エントリー判断 | 同一 bar 上で完結 | リアルタイム OHLCV で再現 | スナップショット比較で確認 |
| SL_FILLED 検知 | バー終値で判定 | fill-history 照合（Change A） | 本番のみ確認可（デモ不可） |

## Phase 3 完了後にやること（忘れずに）

- ~~`test_checklist.md` に以下3章を追加する（本番運用チェックリスト）~~ → ✅ 2026-03-24 追加済み
  - ~~**Pre-Run Checklist**: live宣言・API疎通・孤児注文残骸確認・state vs 取引所一致確認~~ ✅
  - ~~**Live Monitoring**: TP未設定監視・state乖離監視・孤児注文監視・連続API失敗監視~~ ✅
  - ~~**Emergency Stop / Recovery**: 停止条件（E-1）・停止時動作（E-2）・復旧条件（E-3）~~ ✅

---

## Phase 2 テスト開始前ゲート（実動作確認）

**目的: 本番稼働で誤発注・状態破綻・想定外の損失が起きないよう、デモで実際の動作を確認する。**

### セッション開始時の必須確認

S-x 実動作確認を始める前に Claude は必ず以下を確認し、ユーザーの GO を得てから進む：

1. テスト対象の項目が「ALLOW_LIVE_ORDERS=True 必須」かどうかを明示する
2. True が必要な場合は「True に切り替えますか？」とユーザーに確認する
3. ユーザーが True に切り替えるまで、該当テストを開始しない

**ALLOW_LIVE_ORDERS=False のまま進めた場合、発注・キャンセル・TP設定はすべてスキップされ、取引所での動作は一切確認できない。**

### テスト項目別の必要モード

| 項目 | DRY_RUN で可 | ALLOW_LIVE_ORDERS=True 必須 |
|------|:-----------:|:--------------------------:|
| S-0 PARAMS確認 | ✅ | — |
| S-5 ポジション整合���取引所照会） | ✅ | — |
| S-6 TP実在（取引所照会） | ✅ | — |
| S-1 pending作成・TTL切れ・約定後削除 | ❌ | 実発注・実キャンセルが必要 |
| S-2/S-3 add状態遷移・上限制御 | ❌ | 実ADD発注が必要 |
| S-4 SL発動タイミング | ❌ | 実SL設定が必要 |
| S-6 TP_VERIFY ログ | ❌ | run開始時の実照会が必要 |
| S-7 Exit判定 | ❌ | 実TP/SL約定が必要 |
| S-8 能動��ローズ完結 | ❌ | 実クローズAPIが必要 |
| S-9 異常系 | 一部△ | API失敗誘発が必要 |

---

## ステップゲートのルール

- 各 Phase のテストリストは `.claude/context/project_spec.md` に記載
- テスト合格前に次フェーズのコードを書かない
- Phase 4（本番切り替え）は **Claude は実施しない**

## コード変更の手順

1. 差分をここに提示
2. ユーザーの GO を待つ
3. 1箇所だけ変更
4. デモで動作確認

## 現在の状態

Phase: **2（V9判断ロジック移植）**

### Phase 0 完了済み（2026-03-20）
- `cat/__init__.py` / `cat/const.py` / `cat/indicators.py` 作成
- `strategies/cat_v9_decider.py` 作成・スモークテスト済み（decide() → ENTER/SHORT/P23 確認）
- `config/cat_params_v9.json` 作成（CAT_v9_regime.py mainブロックから抽出）
- V8ファイル全削除（run_once.py / cat_live_decider.py / bak / backup）

### Phase 1 完了済み（2026-03-21）
- [x] `runner/run_once_v9.py` 作成・修正済み
- [x] `runner/strategy_stub.py` 更新済み
- [x] test_checklist.md H-0〜H-5 全通過

### Phase 1 で発見・修正したバグ
- `from __future__` の位置バグ（構文エラー）→ 修正済み
- `tradeSide: "open"` パラメータ不足（40774エラー）→ 修正済み
- TP/SL エンドポイント誤り（`place-pos-tpsl` → `place-tpsl-order`）→ 修正済み

### Phase 2 進行中（2026-03-21）
- [x] `test_checklist.md` を指値TP対応に改訂（H-4/H-TPX/S-5/S-6/S-7 更新）
- [x] PARAM Parity Harness（H-0〜H-TPX）再テスト（下記参照）
- [x] exchange_spec.md の修正（posMode: one-way→hedge_mode 3箇所）
- [x] S-0〜S-9 Safety Loop コードレビュー完了・指摘8件を修正済み（セッション5）

### S-0〜S-9 コードレビュー修正内容（2026-03-21 セッション5）

| # | 変更内容 | 対応項目 |
|---|---------|---------|
| 1 | EXIT_EXTERNAL で TP_FILLED/SL_FILLED/TP_OR_SL_HIT を区別（mark_price比較） | S-7 |
| 2 | 能動クローズ完結後に tp_order_id をキャンセル | S-8 |
| 3 | `_confirm_entry` 呼び出しを try/except で囲みSTOP | S-9 |
| 4 | `_place_sl` に sl_order_id 戻り値追加（tuple化） | S-4/S-8 |
| 5 | ADD時に旧SLキャンセル→新SL送信、sl_order_id を open_position.json に保存 | S-4/S-8 |
| 6 | 能動ク���ーズ完結後に sl_order_id もキャンセル | S-8 |
| 7 | run開始時�� tp_order_id 実在確認（ALLOW_LIVE_ORDERS=True 時のみ） | S-5/S-6 |
| 8 | 部分約定TTL切れ後の残存ポジションにTP自動設定 → open_position.json 新規作成 | S-1 |

### S-0〜S-9 残課題（実動作で確認）
- S-7: tp_order_id 実在確認のレスポンスキー（entrustedList/orderList）を実弾で確認
- S-9: 連続API失敗カウンター未実装（設計値要確定）
- 上記以外は全てコードレビューで対処済み

### Phase 2: S-0〜S-9 実動作確認（2026-03-21 セッション6）

| 項目 | 状態 | 備考 |
|------|------|------|
| S-0 全項目 | 未 | DRY_RUNのため無効化。ALLOW_LIVE_ORDERS=Trueで再実施 |
| S-1 ① | ✅ | 実API: ENTRY_SEND code=00000 / PENDING_WRITTEN / pending_entry.json作成確認（2026-03-21 セッション7） |
| S-1 ② | ✅ | 実API: PENDING_STATUS filled / ADD_CONFIRMED / PENDING_CLEARED / pending_entry.json消滅確認（2026-03-21 セッション7） |
| S-1 ③ | 未 | DRY_RUNのため無効化。実APIキャンセルで再実施 |
| S-1 ④ | ✅ | pending live 中に run → NOOP:pending_waiting 確認（2026-03-22 セッション13） |
| S-1 ⑤⑥⑦ | 未 | API失敗・部分約定・post_only拒否（実弾待ち）|
| S-1 ⑦ | ✅ | post_only拒否 → PENDING_CLEARED:externally_canceled 確認（2026-03-22 セッション9） |
| S-4 SL設定 | ✅ | 実API: add_count=2でSL_SET code=00000 / sl_order_id=1419232714410180608 / 取引所一致（2026-03-21 セッション7） |
| S-5 整合性 | ✅ | 取引所 GET照会のため有効（ALLOW_LIVE_ORDERS非依存） |
| S-6 TP実在（取引所直接） | ✅ | 取引所 GET照会のため有効（ALLOW_LIVE_ORDERS非依存） |
| S-6 TP_VERIFY ログ | ✅ | TP消滅+ポジション消滅 → TP_ORDER_MISSING_POS_GONE ログ確認（2026-03-22 セッション8） |
| H-TPX TP再設定 | ✅ | 実API: TP_LIMIT_SEND position_size=0.048 code=00000 / 取引所takeProfit=70911.7一致（2026-03-21 セッション7） |
| H-TPX cancel→send順 | ✅ | ADD_CONFIRMED後 TP_CANCELLED→TP_LIMIT_SEND 順を実API確認（2026-03-22 セッション13） |
| S-2 | ✅ | ADD_CONFIRMED add_count=2〜4 確認済み（2026-03-22 セッション13） |
| S-3 | ✅ | add_count=5 max=5 → NOOP:add_limit_reached（P23 override、2026-03-23 セッション22） |
| S-7 TP_FILLED EXIT | ✅ | EXIT_EXTERNAL(TP_OR_SL_HIT) 発火・open_position.json削除確認（2026-03-22 セッション8） |
| S-8 能動クローズ | ✅ | close-positions エンドポイントでCLOSE_SEND code=00000 / EXIT_COMPLETE確認（2026-03-22 セッション10） |
| S-9 | 未 | 異常系（設計検討中）|

### 判明した設計メモ（セッション6）
- decision_override パス: `state/decision_override.json`
- runner は1サイド1ポジション設計（MAX_SIDES=2 は decider 側）
- `same_side_pending_exists`（L759）は dead code → S-1④ は `pending_waiting` で担保

### PARAM Parity Harness 結���（2026-03-21）

| 項目 | 状態 | 備考 |
|------|------|------|
| H-0 全項目 | ✅ | STATE_DECLARED/OVERRIDE_STATUS でログ確認 |
| H-1 全項目 | ✅ | PARAMS_LOADED イベント確認 |
| H-2 キー存在 | ✅ | PARAMS_LOADED 成功 |
| H-2 型・停止動作 | 未 | EXIT発火時に確認 |
| H-3 ENTER参照値 | ✅ | ENTRY_DECISION: priority/adx/material |
| H-3 EXIT参照値 | 未 | EXIT発火時に確認 |
| H-4 ENTRY_SEND | ✅ | limit_price/size 確認 |
| H-4 TP_LIMIT_SEND | ✅ | triggerPrice/executePrice/position_size/planType 確認 |
| H-4 CLOSE_SEND/VERIFY | ✅ | CLOSE_SEND code=00000 / CLOSE_VERIFY:complete 確認（2026-03-22 セッション10） |
| H-5 全項目 | ✅ | TPSL_CTX: effective_tp_pct/fee_applied/boost_applied |
| H-TPX TP再計算 | ✅ | ADD_CONFIRMED: 新tp/position_size |
| H-TPX 旧TP cancel順 | 未 | Bitget pos_profit 上書き前提。実動作で確認 |

### コード修正（2026-03-21 セッション3）
- `run_once_v9.py`: `TP_LIMIT_SEND` ログ追加（_place_tp 内、ガード前）
- `run_once_v9.py`: `_place_tp` に `position_size` パラメータ追加
- `exchange_spec.md`: posMode を one-way-mode → hedge_mode に修正（3箇所）

### 現在の状態（2026-03-24 セッション25更新）
- デモ口座: ポジションなし（クリーン）
- `ALLOW_LIVE_ORDERS = True`
- `open_position.json`: なし（削除済み）
- `LONG_SL_PCT = SHORT_SL_PCT = 0.05`
- **Phase 2a 完全完了**（Logic Parity A + G-1〜G-5 + B スナップショット比較 200/200 MATCH ✅）
- 次のタスク: **Phase 2b（Param Parity）H-0〜H-TPX ゲート確認**

### セッション23 変更内容（2026-03-24）
- `run_once_v9.py`: `_check_exits` に `MFE_EXIT` ブロック追加（#2: P22 SHORT + hold≥TIME_EXIT×0.6 + mfe_max≥20USD）
- `run_once_v9.py`: `MFE_STALE_CUT` 条件を正本に合わせ修正（`mfe_usd >= 15 and unreal <= 20` → `mfe_usd < P22_SHORT_MFE_STALE_GATE_USD(12.0)`）

### セッション20 変更内容（2026-03-23）
- **Change B** 実装: `run_once_v9.py` reconciliation ② の TP_ORDER_VERIFIED ブロックに SL_ORDER_VERIFIED チェック追加（SL plan order が entrustedList から消えている + ポジション残存 → STOP）
- **Change A** 実装: `run_once_v9.py` reconciliation ② の SL_FILLED 検知を plan history 直接照合から fill-history executeOrderId 照合に変更
  - plan hist で `orderId==sl_order_id` → `executeOrderId` 取得
  - `get_fill_history(order_id=executeOrderId)` で close fill 照合
  - NOTE: 本番専用の暫定実装 / デモ口座では fillList=null のため未検証
- **bitget_adapter.py** `get_fill_history()` に `order_id` オプションパラメータ追加（Change A の前提）

### セッション18 変更内容（2026-03-22）
- S-7② を試みたが SL_FILLED 到達できず（BTC レンジ相場で SL 圏内まで下落しなかった）
- SL_PCT=0.0003 で 40917バグ発見: SL価格 ≥ mark_price → confirm_entry 無限STOPループ
  - 原因: SL_PCT が小さすぎてADD約定後数秒で価格がSL圏内に入る
  - 本番では SL_PCT=0.05 なので通常発生しないが極端な急落時は起きうる
  - 修正方針: _place_sl が 40917 → 即クローズ（次セッションで実装）
- `LONG_SL_PCT / SHORT_SL_PCT` テスト用変更（0.005→0.001→0.0003）→ 0.05 に復元

### セッション17 変更内容（2026-03-22）
- `bitget_adapter.py`: `get_fill_history()` / `get_plan_order_history()` 追加（証拠ベースEXIT_EXTERNAL用）
- `run_once_v9.py`: reconciliation ②（stateあり+exchangeなし）を修正: plan order履歴で証拠確認 → EXIT_EXTERNAL(source=startup_reconciliation) / 証拠なし → 従来通りSTOP
- `EXIT_EXTERNAL(reason=TP_FILLED, source=startup_reconciliation)` 実API確認 ✅
- `LONG_SL_PCT` / `SHORT_SL_PCT` テスト用変更→復元（最終値=0.05）

### セッション16 変更内容（2026-03-22）
- `run_once_v9.py`: `_cancel_plan_order` に `event` パラメータ追加 → SLキャンセル時は `SL_CANCELLED` イベント出力
- `test_checklist.md`: S-8 plan order残骸ゼロ確認 [◯]（TP_CANCELLED+SL_CANCELLED 確認）

### セッション15 変更内容（2026-03-22）
- `test_checklist.md`: H-3 EXIT参照値 [◯]（STAGNATION_CUT: exit_ctx出力確認）
- `test_checklist.md`: H-4 CLOSE_SEND/VERIFY [◯]（セッション15確認）
- `test_checklist.md`: S-8 CLOSE_SEND/VERIFY/open_position削除 [◯]（セッション15+10確認）

### セッション14 変更内容（2026-03-22）
- `test_checklist.md`: H-2 全項目 [◯]（型チェック目視・Fail-fast STOP実確認）
- `test_checklist.md`: S-1④・H-TPX cancel→send順 を [◯] に更新（セッション13確認分）
- `run_once_v9.py`: EXIT_TRIGGERED に `exit_ctx` 追加（H-3 EXIT: reason別スレッショルド値をログ出力）

### セッション11 変更内容（2026-03-22）
- startup reconciliation 両方向実装（`run_once_v9.py`）:
  ① stateなし + exchangeあり → STOP / ② stateあり + exchangeなし → STOP
  ※ pending存在時は① をスキップ（pending約定フローを妨げないよう修正）
- S-TP0 実装: tp_order_id欠損 → STOP
- `test_checklist.md` に S-RC①②・S-TP0・H-HM1〜5 追加
- H-HM1〜5（hedge_mode固有テスト）実API確認済み
- L-11 追記: 特定・実装・記録の分離フロー（再発防止）
- posMode 整合確認: CAT_v9_regime.py はバックテスト専用でposMode記述なし。
  本質的課題は state欠損時の二重ポジションリスク → startup reconciliation で対処済み

---

## ツール一覧

### tools/trade_summary.py — 取引集計レポート

デモ・本番の `logs/cron.log` からバックテスト相当の集計を出力する。
24時間稼働テスト後や定期確認で使う。

```bash
# 全ログを集計
.venv/bin/python3 tools/trade_summary.py

# 開始日時を指定（それ以降のトレードのみ）
.venv/bin/python3 tools/trade_summary.py --since "2026-03-24"
.venv/bin/python3 tools/trade_summary.py --since "2026-03-24T06:00"

# 別ログファイルを指定
.venv/bin/python3 tools/trade_summary.py logs/cron.log --since "2026-03-24"
```

**出力セクション:**

| セクション | 内容 |
|-----------|------|
| 損益サマリー | gross / 手数料 / net / 手数料比率 |
| トレード統計 | TP数 / SL数 / 浅利確数 / TIME_EXIT数 / 勝率 / 平均保持時間 |
| Priority別集計 | P別 gross / fee / net / mean_net |
| Priority別 Exit理由（件数） | P × exit_label のクロス集計 |
| Priority別 Exit理由（net合計） | 同上の損益版 |
| pos_size_btcごとのadd | add回数 / net損益 の cnt/sum/mean |

**Exit ラベル定義:**

| ラベル | 対象 |
|--------|------|
| TP利確 | EXIT_EXTERNAL(TP_FILLED / TP_OR_SL_HIT) |
| SL損切 | EXIT_EXTERNAL(SL_FILLED) |
| TP浅利確_EFF | PROFIT_LOCK / MFE_EXIT / active close で gross > 0 |
| TIME_EXIT | TIME_EXIT |
| その他 | STAGNATION_CUT / MAE_CUT / BREAKOUT_CUT / MFE_STALE_CUT など |

**手数料計算の注意:**
- maker = 0.00014 / taker = 0.00042（`cat_params_v9.json` 準拠）
- TP/SL 約定: `size × exit_price × maker × 2`（往復maker近似）
- active close: `size × exit_price × (maker + taker)`
- ADD がある場合の entry 手数料は avg_price × final_size で近似

---

### セッション8 バグ修正
- `ordersPlanPending` の `planType` を `pos_profit` → `profit_loss` に修正（40812エラー解消）
- S-6 `tp_order_missing` STOP を「ポジション残存時のみ STOP」に修正（S-7フロー到達を確保）
- `TP_ORDER_VERIFIED` が `TP_ORDER_MISSING_POS_GONE` 後に誤発火していたバグを修正（`else:` 追加）

### セッション9〜10 バグ修正
- `decision_override.json` が ENTER消費後も残存してしまうバグ → `_OVERRIDE_PATH.unlink(missing_ok=True)` 追加
- `bitget_adapter.close_market_order`: `place-order + tradeSide=close` (one-way mode用) → `closePositions` エンドポイントに変更（22002エラー解消）