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
  - S-6 TP実在確認（takeProfitId実���）
  - S-6 TP_VERIFY ログ: TP消滅+ポジション消滅 → TP_ORDER_MISSING_POS_GONE 確認（2026-03-22）
  - S-7 EXIT_EXTERNAL: TP約定後にEXIT_EXTERNAL(TP_OR_SL_HIT)発火・open_position.json削除確認（2026-03-22）
  - S-8 能動クローズ: EXIT_TRIGGERED→CLOSE_SEND code=00000→TP/SLキャンセル→CLOSE_VERIFY:complete→open_position.json削除（2026-03-22）
  - H-4 CLOSE_SEND/VERIFY: CLOSE_SEND code=00000 / CLOSE_VERIFY:complete 確認（2026-03-22）
  - H-TPX ADD後TP再計算・再設定（position_size=0.048、code=00000）
  - S-RC① stateなし+exchangeあり → STOP（2026-03-22 セッション11）
  - S-RC② stateあり+exchangeなし → STOP（2026-03-22 セッション11）
  - S-TP0 tp_order_id欠損 → STOP（2026-03-22 セッション11）
  - H-HM1〜5 hedge_mode固有テスト全件（2026-03-22 セッション11）
  - S-1④ NOOP:pending_waiting 確認（2026-03-22 セッ���ョン13）
  - S-2 ADD_CONFIRMED add_count=2〜4 確認済み（2026-03-22 セッション13）
  - H-TPX cancel→send順（TP_CANCELLED→TP_LIMIT_SEND）確認（2026-03-22 セッション13）
  - SL cancel→send順（SL_CANCELLED→SL_SET）確認（2026-03-22 セッション13）
- セッション22（2026-03-23）:
  - **バグ修正**: EXIT_EXTERNAL(startup_recon)時のpending未キャンセル → cancel_order()+unlink()追加 ✅
  - **LONG_SL_PCT / SHORT_SL_PCT**: 0.005 → 0.05 に復元（正本CAT_v9_regime.py L2851/2873に一致）✅
  - **S-0** 実API確認: PARAMS_LOADED sample に SHORT_POSITION_SIZE_BTC=0.024 / MAX_ADDS_BY_PRIORITY={"2":4} 出力確認 ✅
  - **H-4 holdSide**: TP_LIMIT_SEND hold_side=short / open_position.side=SHORT 一致（複数run確認）✅
  - **S-2** 実API確認: ADD_CONFIRMED時のみadd_count+1（add_count=2〜5確認）/ コードレビュー全4項目 ✅
  - **S-3** 実API確認: add_count=5 max=5 → NOOP:add_limit_reached（P23 SHORT override）✅
  - **S-4 add_count≥3**: add_count=2〜5 毎回 SL_CANCELLED→SL_SET���cancel→resend）実API確認 ✅
  - **S-7①**: EXIT_EXTERNAL(TP_FILLED, source=startup_reconciliation) — bot停止中にTP(70096.9)約定 → 翌朝起動時に検知・open_position.json削除 ✅
  - デモポジション解消済み（クリーン状態）
  - **コードレビュー追加確認**（2026-03-24）:
    - S-1 post_only拒否: [◯]（S-1⑦と同一パス、チェック漏れ修正）
    - S-1⑤ 部分約定: [△] コード正常（L795-835）、実API未確認
    - S-5 中途半端state/二重EXIT/��起動後整合: [◯]
    - S-7 優先順位: [◯]（_check_exits L302-353で順序確認）
    - S-7 MFE_EXIT: ~~コード上に独立実装なし~~ → ✅ セッション23 実装完了
    - S-9 アトミック更新3件: [◯]（write_jsonは全API後のみ）
- セッション29（2026-03-24）:
  - **チェックリスト監査完了（別セッション Claude）** → Phase 3 完全完了 ✅
    - 発見1: MFE_EXIT `[×]`→`[◯]` + injection_runner.py に mfe_exit シナリオ追加（9/9 PASS）
    - 発見2: S-7 Exit items（BREAKOUT_CUT/MFE_STALE_CUT/MAE_CUT/PROFIT_LOCK/RSI逆行/TIME_EXIT）→ `[◯]` 化（injection+S-8代表確認）
    - 発見3: **S-7②-A 実API確認** — Bitget UI で SL 手動キャンセル → `STOP(sl_order_missing_pos_exists)` 確認 ✅
    - 発見4: S-5 二項目 `[◯]` 化（S-TP0/TP_ORDER_VERIFIED で担保済みと確認）
    - 発見5: P/M/G セクションに「運用チェックリスト。本番リリースのゲート条件ではない」と明記
  - **デモポジション**: クリーン（SHORT 0.048 手動決済 + open_position.json 削除済み）
  - **Phase 4（本番切り替え）へ移行**

- セッション26（2026-03-24）:
  - **Phase 2b ゲート通過確認**: H-0〜H-TPX 全項目 [◯] → Phase 2b 完了 ✅
  - **Exit Parity フロー確定**: WORKFLOW.md に Exit Parity（Phase 2a-Exit）セクション追加
    - ステップ1: 目視再確認 → ステップ2: tools/exit_compare.py 動的比較 → ゲート通過で Phase 2c へ
    - 出力フォーマット: timestamp / exit_reason / 発動bar / mfe_max_usd / holding_minutes
    - 1ケース1目的設計
  - **目視再確認完了**: _check_exits vs 原本18件 照合
    - W-1 🔴 PROFIT_LOCK(P23/P22_SHORT add==5) trigger 方向逆転 → **修正済み**（`>=` → `<=`、mfe条件削除）
    - W-2 🟡 PROFIT_LOCK P22_SHORT_V2 bar high vs mark_price → 許容範囲
    - W-3 🟡 STAGNATION_CUT P4 general条件漏れ → **exit_compare.py で差異確認後に判断**
    - W-4 ✅ TIME_EXIT P4延長 → 原本で無効化済み（問題なし）
  - **次のタスク**: tools/exit_compare.py 作成（設計合意済み）
- セッション28（2026-03-24）:
  - **W-3修正**: run_once_v9.py STAGNATION_CUT P4パスを外側ゲート(STAG_MIN_M=30)から独立させた ✅
    - 修正前: P4(hold=20-29m) が外側ゲートに阻まれてNone → 修正後: P4独立分岐で発動
  - **exit_compare.py T01〜T11 全MATCH（11/11）** ✅ → **Exit Parity ゲート通過**
  - **Phase 2a-Exit 完了 → Phase 2c（Demo Run）へ**
  - **run_once_v9.py**: TEST_INJECTION サポート追加（CAT_TEST_INJECTION env var）
    - _OPEN_POS_PATH → test_injection_position.json / ログに [TEST_INJECTION] プレフィックス
  - **tools/injection_runner.py 作成**: 8シナリオ全PASS ✅
    - stagnation_p4 / stagnation_general / time_exit_long / time_exit_short
    - mfe_stale_cut / mae_cut / profit_lock_p22 / breakout_cut（snapshot preprocess）
  - **Phase 2c 完了**: SL_FILLED 以外の全 Exit 条件を injection テストで確認
  - **Phase 3 Safety / Observability へ**
- セッション27（2026-03-24）:
  - **tools/exit_compare.py 作成完了** ✅
    - T01〜T11 全11ケース実装（1ケース1目的設計）
    - T04 が W-3（STAGNATION_CUT P4 hold=20-30m 漏れ）を確認するキーケース
    - T11 は snapshot.csv から bb_width≥0.03 AND rsi_short≥70 バーを自動検索

- セッション25（2026-03-24）:
  - **Phase 2a Logic Parity B 完了**: `tools/snapshot_compare.py` / `tools/fetch_snapshot.py` 作成
  - BTCUSDT 5m 足 300本でテスト（bar 100〜299、200バー）
  - 原本 `CAT_v9_regime.check_entry_priority` vs 移植版 `cat_v9_decider.check_entry_priority` **200/200 MATCH（100.0%）** ✅
  - **Phase 2a 完全完了 → Phase 2b（Param Parity）へ移行**

- セッション24（2026-03-24）:
  - **本番リリースフロー改訂**: WORKFLOW.md のフェーズ一覧を Logic Parity → Param Parity → Demo Run → Safety の順に改訂
  - **cat_v9_regime_map.md 新規作成**: 原本 Exit 条件18件・ギャップ G-1〜G-5 を記録
  - **Phase 2a Logic Parity A 完了**: run_once_v9.py が v9_decide()/preprocess() を呼んでいること確認。Exit は _check_exits で独自実装（設計上やむを得ない）
  - **G-1 修正**: BREAKOUT_CUT P22/P23 を `add==3` + bb_width/rsi 条件に統一（`>=3` + 無条件発動のバグを修正）
  - **G-2 修正**: MAE_CUT に `mark_price >= entry + 50/size` の価格条件を追加
  - **G-3 実装**: PROFIT_LOCK(P23_SHORT) / PROFIT_LOCK(P22_SHORT) add==5版を追加（mfe_usd で armed 相当を代替）
  - **G-4 実装**: P4_BREAK_EXIT を TIME_EXIT 直前に追加（hold≒P4_BREAK_HOLD_MIN ±5min + bb_mid_slope条件）
  - **G-5 修正**: STAG_MIN_M を 20.0 → 30.0 に修正（原本コードのハードコード値と一致。ユーザーが config 編集）
- セッション23（2026-03-24）:
  - **MFE_EXIT 追加**: `_check_exits` #2 に追加（P22 SHORT + hold≥TIME_EXIT×0.6 + mfe_usd≥20USD → `"MFE_EXIT"`）✅
  - **MFE_STALE_CUT 条件修正**: `mfe_usd >= 15 and unreal <= 20` → `mfe_usd < P22_SHORT_MFE_STALE_GATE_USD(12.0)` ✅
    - 正本: `mfe_max_usd < 12.0`（add=5まで積んで儲からなかったポジを強制カット）
    - 旧コードは rescue profit ロジックで条件が逆だった
- セッション21（2026-03-23）:
  - S-1①② 実API確認: ENTRY_SEND(code=00000)/PENDING_WRITTEN → ENTRY_CONFIRMED/PENDING_CLEARED(reason=filled) ✅
  - TP_ORDER_VERIFIED: 毎run startup で tp_order_id をプラン照会 ✅
  - EXIT_EXTERNAL(TP_FILLED, source=startup_reconciliation): TP約定をstartup_reconciliationで検知 ✅（再確認）
  - **設計ギャップ発見**: startup_reconciliation で EXIT_EXTERNAL 発火時、pending_entry.json（ADD指値）が残存したままになる
    - open_position.json削除後も ADD指値がキャンセルされず、次runでpending_waiting→TTL切れのループになる
    - 最悪ケース: ADD指値が後で刺さると意図しない新規ポジションが add_count=1 で作られる
    - 修正案: EXIT_EXTERNAL(startup_recon)時に pending_entry.json 存在チェック → cancel_order() + unlink() 追加
  - S-0: PARAMS_LOADED で size=0.024 確認、ただし MAX_ADDS_BY_PRIORITY が sample に未出力（コード側のsampleキーリスト問題）
  - H-4 holdSide: grepフィルタで除外されたため未確認（次回フルログで確認要）
  - SHORT_SL_PCT = 0.005（現在値）でSL到達ライン = entry × 1.005 ≈ $354上昇 → ADD前にTP(70733.2)が先着した
- セッション20（2026-03-23）:
  - **Change B** 実装: `run_once_v9.py` の TP_ORDER_VERIFIED ブロック内に SL_ORDER_VERIFIED チェック追加
    - entrustedList から sl_order_id が消えている + ポジション残存 → `STOP(sl_order_missing_pos_exists)`
    - Bitget デモ口座の SL plan order 非発動バグ（SL消滅だがポジション残存）を検知する
  - **Change A** 実装: `run_once_v9.py` reconciliation ② の SL_FILLED 検知ロジック変更
    - 旧: plan history の orderId を sl_order_id と直接照合 → SL_FILLED
    - 新: plan history で executeOrderId を取得 → fill-history で close fill 照合 → SL_FILLED
    - NOTE: 本番専用の暫定実装 / デモでは fillList=null のため未検証（デモ→STOP）
  - **bitget_adapter.py** `get_fill_history()` に `order_id` パラメータ追加（Change A 前提）
- セッション19（2026-03-23）:
  - **40917バグ修正** 完了（3ターン）:
    1. `filled` + `_confirm_entry` 例外時に `pending_entry.json` を必ずクリア（STOPループ防止）
    2. `_place_sl` で 40917 を `SL_PRICE_INVALID:40917` プレフィックスで識別
    3. 呼び出し元で 40917 検知 → 即クローズ → `EXIT_COMPLETE(exit_reason=SL_PRICE_INVALID)`
  - S-7②: LONG で試みたが TP_FILLED が先到達（SL未確認）→ SHORT で再挑戦予定
  - add_count=5 まで積み上げ・SL更新動作確認 ✅（各 ADD で SL 再設定 code=00000）
- セッション17（2026-03-22）:
  - `bitget_adapter.py`: `get_fill_history()` / `get_plan_order_history()` 追加
  - `run_once_v9.py`: reconciliation ②修正 — plan order履歴でplanStatus="executed"のorderId照合 → EXIT_EXTERNAL(source=startup_reconciliation) / 証拠なし → STOP（従来通り）
  - `EXIT_EXTERNAL(reason=TP_FILLED, source=startup_reconciliation)` 実API確認 ✅
  - fill-historyはデモ口座では fillList=null → 使えない（第二証拠=plan order historiesのみ）
  - S-7② SL_FILLED: 未確認（SL_PCT=0.005で再テスト要）
- セッション16（2026-03-22）:
  - SL_CANCELLED イベント追加: _cancel_plan_order に event パラメータ追加、SLキャンセル時はSL_CANCELLEDを出力
  - S-8 plan order残骸ゼロ確認: TP_CANCELLED+SL_CANCELLED code=00000 確認済み
- セッション15（2026-03-22）:
  - H-3 EXIT: STAGNATION_CUT → EXIT_TRIGGERED に exit_ctx:{stag_min_m:20.0,stag_mfe_usd:1.0} 出力確認
  - H-4 CLOSE_SEND/VERIFY: CLOSE_SEND size=0.024 code=00000 / CLOSE_VERIFY:complete 確認
  - S-8 能動クローズ主要3項目確認: CLOSE_SEND/VERIFY/TP_CANCELLED (open_position削除はセッション10確認済み)
- セッション14（2026-03-22）:
  - H-2 全項目完了: 型チェック目視確認・Fail-fast STOP実動作確認（LONG_POSITION_SIZE_BTC削除→config_load_failed）
  - H-3 EXIT: EXIT_TRIGGERED に exit_ctx 追加実装（reason別スレッショルド値ログ）。実API証跡は次回EXIT発火時
  - S-1⑤ API失敗時pending未作成: size=0.0 → 40017エラー → STOP:place_limit_order_failed / pending_entry.json 未作成確認

## 設計メモ（重要）

- **EXIT_EXTERNAL 証拠ルール（セッション17確定）**: 推測でのEXIT_EXTERNAL禁止。`planStatus="executed"` かつ `orderId == tp_order_id or sl_order_id` の一致が唯一の証拠
- **fill-historyはデモ口座で使えない**: `fillList: null` が返る。証拠は plan order history のみ
- **reconciliation ②の設計**: stateあり+exchangeなし → 証拠確認 → EXIT_EXTERNAL（TP_FILLED/SL_FILLED）or STOP。run間にTP/SL約定が起きた場合の正常処理パス

- **能動クローズ API**: `place-order + tradeSide=close` は one-way mode 専用。hedge_mode では `/api/v2/mix/order/close-positions`（`holdSide: long/short`）を使う
- **decision_override のパス**: `state/decision_override.json`
- **runner は1サイド1ポジション設計**: LONG保有中にSHORT決定 → `pos_side_mismatch` NOOP
- **`same_side_pending_exists`（run_once_v9.py L759）は dead code**: S-1④は`pending_waiting`で担保
- **Bitget pos_profit TP**: 新規送信で既存TPを上書き（同一orderId維持）。cancelスキップでも上書き可
- **ordersPlanPending の planType**: place時は `pos_profit`/`pos_loss` だが、query時は `profit_loss`（両方込み）を使う。`pos_profit` 単体はクエリ不可（40812エラー）
- **S-7 EXIT reason**: TP約定後にmark_priceが戻っていた場合は `TP_FILLED` でなく `TP_OR_SL_HIT` になる（後追い断定不可。設計通り）

---

## 未完了（次セッションでやること）

### 優先度: 最高

~~**Phase 2a-Exit: Exit Parity（exit_compare.py T01〜T11全MATCH）**~~ → ✅ 2026-03-24 セッション28 完了

~~**Phase 2c Demo Run**~~ → ✅ 2026-03-24 セッション28 完了（injection テスト 8シナリオ全PASS）

**Phase 3 Safety / Observability 進行中**:
  - ~~E-1 停止手順~~ → ✅ 2026-03-24 手順書作成完了（チャッピー監修）
  - ~~E-2 停止時の取引所整理~~ → ✅ 2026-03-24 手順書作成完了（チャッピー監修）
  - ~~E-3 復旧条件~~ → ✅ 2026-03-24 手順書作成完了（チャッピー監修）
  - ~~O-1〜O-5 Observability~~ → ✅ 2026-03-24 完了
    - EXIT_EXTERNAL(startup_reconciliation) に priority 追加
    - test_checklist.md O-1〜O-5 全項目 [◯] 更新
  - ~~Pre-Run Checklist / Live Monitoring (P-1〜P-4 / M-1〜M-4)~~ → ✅ 2026-03-24 test_checklist.md に追加
  - ~~S-9 連続API失敗カウンター~~ → ✅ 2026-03-24 実装完了
    - state/api_failure_count.json で管理、N=3、1run最大+1
    - market/candle/pos 全成功でリセット、DRY_RUNは pos=True 扱い
    - E-3 復旧手順にステップ0（api_failure_count.json 削除）追加
  - ~~**次: 別セッション Claude によるチェックリスト監査**（本番切り替え前）~~ → ✅ 2026-03-24 セッション29 完了

**Phase 2c-bis（デモ連続稼働テスト）— 進行中**

- crontab: `.venv/bin/python3` に修正済み ✅
- `tools/monitor.sh` 作成: STOP/ERROR → ntfy iPhone通知 ✅
- 24時間稼働テスト 開始済み（2026-03-24）
- 監視方針確定: エラー通知（STOP/ERROR）のみ。ENTRY等の個別通知は不要と判断 ✅
- `tools/trade_summary.py` 作成: 24時間後に取引集計レポートを生成するツール ✅
  - 実行: `.venv/bin/python3 tools/trade_summary.py --since "2026-03-24"`
  - 出力: 損益サマリー / TP・SL・浅利確数 / Priority別集計 / pos_size別add分布
  - 使い方は WORKFLOW.md「ツール一覧」セクション参照

**Phase 4（本番切り替え）— Phase 2c-bis 完了後、ユーザーが手動実施。Claude は実施しない。**

~~0. **Phase 2a Logic Parity B: スナップショット比較スクリプト**~~ → ✅ 2026-03-24 セッション25 完了
   - `tools/snapshot_compare.py` + `tools/fetch_snapshot.py` 作成
   - 200バー全一致（100.0%）確認 — Logic Parity B 合格

### 優先度: 高（Logic Parity コード修正 → 完了）

~~**Phase 2a Logic Parity A + G-1〜G-5 修正**~~ → ✅ 2026-03-24 セッション24 完了

### 完了済み（旧: 優先度最高）

~~**バグ修正: EXIT_EXTERNAL(startup_recon)時のpending未キャンセル**~~ → ✅ 2026-03-23 セッション22 修正完了

1. ~~**40917バグ修正**~~ → ✅ 2026-03-23 修正完了
   - `filled` + 例外時の pending 未クリア（STOPループ）→ except 先頭に unlink 追加
   - `_place_sl` 40917 → `SL_PRICE_INVALID:40917` で識別 → 即クローズ → EXIT_COMPLETE

### 優先度: 高

1. **S-7��** SL外部約定EXIT検知（`SL_FILLED`）
   - Change A/B 実装済み。SL_PCT=0.05 で SHORT → SL到達待ち
   - デモ口座では SL plan order が非発動（消滅するだけでポジション残存）バグあり
     → Change B で STOP 検知。Change A の SL_FILLED 確認は本番でのみ可能
   - SL��動まで時間がかかる（本番値では5%下落が必要）
   - 別セッションで粘り強く待つ必要あり

2. ~~**lessons.md 追記** — Bitget デモ口座 SL plan order 非発動バグ（Change B/A の背景）~~ → ✅ L-14 追記済み（2026-03-23）

3. ~~**MFE_EXIT 未実装 / MFE_STALE_CUT 条件不一致**~~ → ✅ 2026-03-24 セッション23 修正完了

4. **S-1 残項目**
   - ~~③ TTL切れキャンセル~~ → 2026-03-22 セッション12 完了
   - ~~④ pending_waiting フロー確認~~ → 2026-03-22 セッション13 完了
   - ⑤ API失敗時にpending_entry.jsonが中途半端に残らない

3. ~~**S-3** add_limit_reached NOOP~~ → ✅ 2026-03-23 セッション22 実API確認（P23 override add_count=5 max=5 → NOOP）

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