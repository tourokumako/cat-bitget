# project_v9_progress.md — V9実装進捗（Phase 4移行時に圧縮 2026-03-25）

## 本セッション完了分（2026-03-25 セッション3）

### Phase 4 本番切り替え完了

- デモ cron 停止（`crontab -r`）
- `config/bitget_keys.json`: 本番APIキーに変更・`paper_trading=false`・`allow_paper_orders=false`
- 初回手動実行: `CONFIG_LOADED: paper_trading: false` / `STATE_DECLARED: mode=live` / `MARKET_SANITY_OK` / `RUN_SUMMARY: action=NOOP` ✅
- cron 再登録（本番用・🍎マーカー付き）
- 初回 cron 実行（23:30 JST）: デモ残留 pending_entry を PENDING_CLEARED 後 NOOP ✅ 正常動作確認

---

## 本セッション完了分（2026-03-25 セッション2）

### バグ修正2件（run_once_v9.py）

**Bug Fix 1: cancel_order メソッド不存在（L781）**
- 修正前: `adapter.cancel_order(PRODUCT_TYPE, SYMBOL, pending["order_id"])`
- 修正後: `_cancel_order(adapter, pending["order_id"])`
- 発覚経緯: デモでpendingキャンセル失敗 → 指値が残存 → 後から約定 → open_position.jsonなしのポジション発生
- 再現条件: startup_reconciliation でEXIT_EXTERNALが走りかつpending_entry.jsonが存在する時

**Bug Fix 2: SL_EXECUTE_OID_MISSING ログ追加（L759-762）**
- executeOrderIdがnullの場合に無音でSTOPしていた → `SL_EXECUTE_OID_MISSING` ログを追加
- 修正前: null時に無音STOP（原因特定に時間がかかる）
- 修正後: `SL_EXECUTE_OID_MISSING` イベントを出力してからSTOP

### デモ稼働インシデント（2026-03-25）
- Bug Fix 1 の影響でデモにTPなし・SLなし・state管理外のLONGポジション（71387.8）が発生
- ユーザーが手動決済、BOT復旧済み

### 前セッション（2026-03-25 セッション1）完了分
- project_v9_progress.md 圧縮（254行 → 42行）
- WORKFLOW.md を Phase 4 に更新
- `.claude/context/release_guide.md` 作成（チャッピー監修 4点追加済み）
- `run_once_v9.py`: 本番用ログ3系統追加（live時のみ動作）
  - `logs/live_run.log` — crontab redirect 変更のみ（ユーザーが本番切り替え時に実施）
  - `logs/live_decision.log` — 判定イベント（DECISION/ENTRY/EXIT/STOP）
  - `logs/live_trades.csv` — 1トレード1行（entry_time_jst / holding_minutes 含む）
- `improvements.md` に G-Runner-2（ログローテーション）追加

---

## フェーズ完了サマリー

- **Phase 0〜3: 完了**（2026-03-20〜2026-03-24）
  - Phase 0: V8削除・cat/パッケージ・cat_v9_decider.py・cat_params_v9.json 作成
  - Phase 1: run_once_v9.py 作成・H-0〜H-5 通過
  - Phase 2: Logic Parity（200/200 MATCH）・Param Parity・Exit Parity（T01〜T11 全MATCH）・Demo Run（injection 全PASS）
  - Phase 3: Safety/Observability 完了・チェックリスト監査（別セッション Claude）完了
  - Phase 2c-bis: デモ連続稼働テスト完了・trade_summary.py 動作確認済み

## 現在のフェーズ

**Phase 5（常時稼働）— 2026-03-25 本番切り替え完了。cron 稼働中。**

## 設計メモ（重要）

- **EXIT_EXTERNAL 証拠ルール**: 推測での EXIT_EXTERNAL 禁止。`planStatus="executed"` かつ `orderId == tp_order_id or sl_order_id` の一致が唯一の証拠
- **reconciliation ② の設計**: stateあり+exchangeなし → 証拠確認 → EXIT_EXTERNAL（TP_FILLED/SL_FILLED）or STOP。run間にTP/SL約定が起きた場合の正常処理パス
- **decision_override のパス**: `state/decision_override.json`
- **runner は1サイド1ポジション設計**: LONG保有中にSHORT決定 → `pos_side_mismatch` NOOP（詳細: improvements.md G-Runner-1）
- **Bitget pos_profit TP**: 新規送信で既存TPを上書き（同一orderId維持）。cancelスキップでも上書き可
- **ordersPlanPending の planType**: place時は `pos_profit`/`pos_loss`、query時は `profit_loss`（両方込み）を使う。`pos_profit` 単体はクエリ不可（40812エラー）
- **S-7 EXIT reason**: TP約定後に mark_price が戻っていた場合は `TP_FILLED` でなく `TP_OR_SL_HIT` になる（後追い断定不可。設計通り）

## 残タスク（本番稼働後に確認）

- **S-7② SL_FILLED**: デモ口座では SL plan order 非発動バグのため確認不可。本番でのみ確認（Change A/B 実装済み）
- **S-1⑤**: API失敗時に pending_entry.json が中途半端に残らないことの実API確認（コードは正常 L795-835、実弾未確認）
- **G-Runner-1**: LONG/SHORT同時保有（MAX_SIDES=2）— 本番データで機会損失が顕在化したら検討（→ improvements.md）

## 参照すべき正本ファイル

- **パラメータ**: `cat-swing-sniper/strategies/CAT_v9_regime.py` L2830-2935
- **Exit全ロジック**: `cat-swing-sniper/strategies/CAT_v9_regime.py` `run_backtest()` L610以降
- **API仕様**: `.claude/rules/exchange_spec.md`
- **テスト基準**: `.claude/context/test_checklist.md`