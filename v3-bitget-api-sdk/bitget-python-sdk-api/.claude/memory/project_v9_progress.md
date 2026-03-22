# project_v9_progress.md — V9実装進捗

## 完了済み（サマリー）

- Phase 0: V8削除・cat/パッケージ・cat_v9_decider.py・cat_params_v9.json 作成完了
- Phase 1: run_once_v9.py 作成・デモ実弾発注成功・H-0〜H-5 通過（2026-03-21）
- Phase 2 コードレビュー: S-0〜S-9 Safety Loop 8件修正済み（詳細はgit履歴参照）
- Phase 2 実API確認済み:
  - S-1① ENTRY_SEND code=00000・pending_entry.json作成
  - S-1② ADD約定後のpending削除（PENDING_CLEARED: filled）
  - S-1⑦ post_only拒否 → PENDING_CLEARED:externally_canceled 確認（2026-03-22）
  - S-4 add_count=2でSL_SET code=00000（sl_order_id=1419232714410180608）
  - S-5 取引所 ⇔ open_position.json 整合確認
  - S-6 TP実在確認（takeProfitId実在）
  - S-6 TP_VERIFY ログ: TP消滅+ポジション消滅 → TP_ORDER_MISSING_POS_GONE 確認（2026-03-22）
  - S-7 EXIT_EXTERNAL: TP約定後にEXIT_EXTERNAL(TP_OR_SL_HIT)発火・open_position.json削除確認（2026-03-22）
  - S-8 能動クローズ: EXIT_TRIGGERED→CLOSE_SEND code=00000→TP/SLキャンセル→CLOSE_VERIFY:complete→open_position.json削除（2026-03-22）
  - H-4 CLOSE_SEND/VERIFY: CLOSE_SEND code=00000 / CLOSE_VERIFY:complete 確認（2026-03-22）
  - H-TPX ADD後TP再計算・再設定（position_size=0.048、code=00000）
  - S-RC① stateなし+exchangeあり → STOP（2026-03-22 セッション11）
  - S-RC② stateあり+exchangeなし → STOP（2026-03-22 セッション11）
  - S-TP0 tp_order_id欠損 → STOP（2026-03-22 セッション11）
  - H-HM1〜5 hedge_mode固有テスト全件（2026-03-22 セッション11）
  - S-1④ NOOP:pending_waiting 確認（2026-03-22 セッション13）
  - S-2 ADD_CONFIRMED add_count=2〜4 確認済み（2026-03-22 セッション13）
  - H-TPX cancel→send順（TP_CANCELLED→TP_LIMIT_SEND）確認（2026-03-22 セッション13）
  - SL cancel→send順（SL_CANCELLED→SL_SET）確認（2026-03-22 セッション13）

## 設計メモ（重要）

- **能動クローズ API**: `place-order + tradeSide=close` は one-way mode 専用。hedge_mode では `/api/v2/mix/order/close-positions`（`holdSide: long/short`）を使う
- **decision_override のパス**: `state/decision_override.json`
- **runner は1サイド1ポジション設計**: LONG保有中にSHORT決定 → `pos_side_mismatch` NOOP
- **`same_side_pending_exists`（run_once_v9.py L759）は dead code**: S-1④は`pending_waiting`で担保
- **Bitget pos_profit TP**: 新規送信で既存TPを上書き（同一orderId維持）。cancelスキップでも上書き可
- **ordersPlanPending の planType**: place時は `pos_profit`/`pos_loss` だが、query時は `profit_loss`（両方込み）を使う。`pos_profit` 単体はクエリ不可（40812エラー）
- **S-7 EXIT reason**: TP約定後にmark_priceが戻っていた場合は `TP_FILLED` でなく `TP_OR_SL_HIT` になる（後追い断定不可。設計通り）

---

## 未完了（次セッションでやること）

### 優先度: 高

0. ~~**S-RC 実動作確認**~~ → 2026-03-22 セッション11 完了

1. **S-1 残項目**
   - ③ TTL切れキャンセル（実APIキャンセルで再実施）
   - ④ pending_waiting フロー確認
   - ⑤ API失敗時にpending_entry.jsonが中途半端に残らない

2. **S-3** add_limit_reached NOOP（保留。コードレビュー確認済みで先行）

### 優先度: 中（hedge_mode 固有テスト項目 — チェックリスト追加・実API確認が必要）

4. ~~**hedge_mode 固有テスト項目（H-HM1〜5）**~~ → 2026-03-22 セッション11 チェックリスト追加・実API確認完了

### 優先度: 低
- S-9: 連続API失敗カウンター（設計値N回を決めてから実装）

### Phase 3 完了後（本番切り替え前）
- 別セッションClaudeによるチェックリスト追加監査

---

## 参照すべき正本ファイル

- **パラメータ**: `cat-swing-sniper/strategies/CAT_v9_regime.py` L2830-2935
- **Exit全ロジック**: `cat-swing-sniper/strategies/CAT_v9_regime.py` `run_backtest()` L610以降
- **API仕様**: `.claude/rules/exchange_spec.md`
- **テスト基準**: `.claude/context/test_checklist.md`