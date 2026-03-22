# WORKFLOW.md — V9 移植 作業手順

## セッション開始時の確認事項（最優先）

| 項目 | 状態 |
|------|------|
| 現在のフェーズ | Phase 2（V9判断ロジック移植・実動作確認中） |
| デモポジション | なし（S-13完了・TP約定でクローズ済み） |
| 次のタスク | S-1③⑤ / S-3（保留） / H-2型チェック / H-3 EXIT参照値 / H-TPX旧TP cancel順 |
| ALLOW_LIVE_ORDERS | True（テスト実行中。Claudeは変更しない） |
| open_position.json | なし（削除済み） |

---

## フェーズ一覧

| Phase | 名称 | ゲート条件（全て満たしてから次へ） |
|-------|------|----------------------------------|
| 0 | 環境準備 | cat/パッケージ import OK / params全キー揃い |
| 1 | デモ配線確認 | 指値発注→照会→キャンセル→TP設定→外部約定検知 疎通 |
| 2 | V9判断ロジック移植 | 同一スナップショットで V9 と decider の priority 一致 |
| 3 | E2E デモ通し | 全 Exit 条件（11種）がデモで動作確認済み |
| 4 | 本番切り替え | Phase 3 完了後、ユーザーが手動で実施 |
| 5 | 常時稼働 | cron 設定・ログ監視 |

## Phase 3 完了後にやること（忘れずに）

- `test_checklist.md` に以下3章を追加する（本番運用チェックリスト）
  - **Pre-Run Checklist**: live宣言・API疎通・孤児注文残骸確認・state vs 取引所一致確認
  - **Live Monitoring**: TP未設定監視・state乖離監視・孤児注文監視・連続API失敗監視
  - **Emergency Stop / Recovery**: 停止条件（E-1）・停止時動作（E-2）・復旧条件（E-3）

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
| S-5 ポジション整合（取引所照会） | ✅ | — |
| S-6 TP実在（取引所照会） | ✅ | — |
| S-1 pending作成・TTL切れ・約定後削除 | ❌ | 実発注・実キャンセルが必要 |
| S-2/S-3 add状態遷移・上限制御 | ❌ | 実ADD発注が必要 |
| S-4 SL発動タイミング | ❌ | 実SL設定が必要 |
| S-6 TP_VERIFY ログ | ❌ | run開始時の実照会が必要 |
| S-7 Exit判定 | ❌ | 実TP/SL約定が必要 |
| S-8 能動クローズ完結 | ❌ | 実クローズAPIが必要 |
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
| S-3 | 保留 | add_count=5→NOOP確認前にTP約定。コードレビュー確認済みで保留 |
| S-7 TP_FILLED EXIT | ✅ | EXIT_EXTERNAL(TP_OR_SL_HIT) 発火・open_position.json削除確認（2026-03-22 セッション8） |
| S-8 能動クローズ | ✅ | close-positions エンドポイントでCLOSE_SEND code=00000 / EXIT_COMPLETE確認（2026-03-22 セッション10） |
| S-9 | 未 | 異常系（設計検討中）|

### 判明した設計メモ（セッション6）
- decision_override パス: `state/decision_override.json`
- runner は1サイド1ポジション設計（MAX_SIDES=2 は decider 側）
- `same_side_pending_exists`（L759）は dead code → S-1④ は `pending_waiting` で担保

### PARAM Parity Harness 結果（2026-03-21）

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

### 現在の状態（2026-03-22 セッション13終了時更新）
- デモ口座: ポジションなし（TP約定でクローズ済み）
- `ALLOW_LIVE_ORDERS = True`
- `open_position.json`: なし
- 次の確認待ち: S-1③⑤ / S-3（保留） / H-2型チェック / H-3 EXIT参照値 / H-TPX旧TP cancel順

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

### セッション8 バグ修正
- `ordersPlanPending` の `planType` を `pos_profit` → `profit_loss` に修正（40812エラー解消）
- S-6 `tp_order_missing` STOP を「ポジション残存時のみ STOP」に修正（S-7フロー到達を確保）
- `TP_ORDER_VERIFIED` が `TP_ORDER_MISSING_POS_GONE` 後に誤発火していたバグを修正（`else:` 追加）

### セッション9〜10 バグ修正
- `decision_override.json` が ENTER消費後も残存してしまうバグ → `_OVERRIDE_PATH.unlink(missing_ok=True)` 追加
- `bitget_adapter.close_market_order`: `place-order + tradeSide=close` (one-way mode用) → `closePositions` エンドポイントに変更（22002エラー解消）