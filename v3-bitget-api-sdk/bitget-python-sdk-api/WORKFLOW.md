# WORKFLOW.md — V9 改善フロー（2026-04-03 更新）

## セッション開始時の確認事項（最優先）

| 項目 | 状態 |
|------|------|
| 現在のフェーズ | **Phase 5（常時稼働）— BOT 停止中** |
| 本番ポジション | なし（BOT 停止中） |
| 次のタスク | **add=3 復活 + TP/SL 設計の最適化**。L-23/L-24 参照。まず bar-by-bar グリッドサーチ（L-22）で add=3 時の edge を確認してから Replay 実走。 |
| ALLOW_LIVE_ORDERS | True（Claudeは変更しない） |
| open_position_long.json | なし |
| open_position_short.json | なし |
| paper_trading | false |
| MAX_ADDS_BY_PRIORITY | `{"2": 1, "4": 1, "22": 1, "23": 1, "24": 1}`（全Priority add=1 ← 次セッションで add=3 に戻す） |
| LONG_TP_PCT / SHORT_TP_PCT | 0.020（旧: 0.0056） |
| LONG_SL_PCT / SHORT_SL_PCT | 0.010（旧: 0.05） |
| LONG_TIME_EXIT_MIN / SHORT_TIME_EXIT_MIN / P2_TIME_EXIT_MIN | 9999（実質廃止） |
| TP_ADX_BOOST_ENABLE | 0（無効化） |
| TP_PCT_CLAMP_ENABLE | 0（無効化） |
| FEAT_SHORT_RSI_REVERSE_EXIT | false（無効化） |
| LONG_PROFIT_LOCK_ENABLE | 0（無効化） |
| P23_SHORT_PROFIT_LOCK_ENABLE | 0（無効化） |
| P2_ADX_MIN | 30.0 |
| P2_RSI_MIN | 45.0 |
| P4_RSI_MAX | 60.0 |
| P23_BB_MID_SLOPE_MAX | -10.0 |
| P23_ADX_MIN | 30.0 |
| P23_ADX_MAX | 50.0 |
| Replay 現在値 | NET -$372 / 90日（**-$4.1/day**）318件。`results/replay_BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv` |
| Replay 用 CSV | `/Users/tachiharamasako/Documents/GitHub/cat-swing-sniper/data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv` |
| replay_csv.py 修正済み | SL add=1 でも設定・TP/SL 判定を high/low ベースに変更（L-21）|

---

## 改善フロー（Phase 5）

**このフローを必ず順番通りに実行する。前のステップが完了するまで次に進まない。**

```
Step 1. パラメータ変更  — cat_params_v9.json を変更（GO後のみ）
Step 2. Replay 実走     — 90日CSVで実行・エントリーポイント確定 ← STOP
Step 3. グリッドサーチ  — Replayのエントリー固定でbar-by-bar TP/SL先着確率を計算
                         理論値（SL/(TP+SL)）と実測を比較してedge確認（L-22手法）
                         TP%/SL%の組み合わせで90日EVを試算
Step 4. 候補提示        — EVが最大の組み合わせを提案・件数・EV/trade・90d NET を明示 ← STOP
Step 5. ユーザー承認    — GO サインが出るまでコードを変更しない ← STOP
Step 6. パラメータ適用  — cat_params_v9.json を最良値に更新
Step 7. Replay 実走     — 実際のNETを確認・グリッドサーチ理論値と照合 ← STOP
Step 8. 採用 or 却下    — 却下なら即巻き戻し
Step 9. 本番反映        — run_once_v9.py / cat_params_v9.json への反映確認 ← STOP
Step 10. Git コミット   — 確認後コミット ← STOP
```

**設計原則（2026-04-03 確定）:**
- TIME_EXIT 廃止: TP か SL のどちらかに当たるまで待つ
- add=3 設計: 逆行時に平均エントリーを改善しTP率を高める（L-23）
- SL 幅は ATR の 2〜3倍 を目安に設定（狭すぎると即死連発・L-24）
- `replay_csv.py` と `run_once_v9.py` の `_check_exits` は常に同期を保つこと

---

## Replay 実行コマンド

```bash
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
echo "=====🚀 RUN START $(date) =====" && \
.venv/bin/python3 runner/replay_csv.py \
  /Users/tachiharamasako/Documents/GitHub/cat-swing-sniper/data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv
```

---

## ツール一覧

### tools/trade_summary.py — 本番ログ集計レポート

本番の `logs/cron.log` からトレード集計を出力する。

```bash
.venv/bin/python3 tools/trade_summary.py
.venv/bin/python3 tools/trade_summary.py --since "2026-03-24"
```

---

## 過去作業記録（Phase 0-4）

Phase 0-4（移植・デモ・本番切り替え）の詳細記録。現フェーズでは参照不要。

### Phase 0〜4 完了サマリー
- Phase 0（2026-03-20）: cat/パッケージ・cat_v9_decider.py・cat_params_v9.json 作成
- Phase 1（2026-03-21）: run_once_v9.py 作成・H-0〜H-5 通過
- Phase 2（2026-03-21〜24）: Logic Parity 200/200 MATCH・Param Parity・Demo Run 完了
- Phase 3（2026-03-24）: Safety/Observability 完了
- Phase 4（2026-03-25）: 本番切り替え完了・cron 稼働開始
- Phase 5（2026-03-26〜）: MAX_SIDES=2 実装・本番稼働中

### 主なバグ修正記録（参照用）
- 45135バグ（2026-03-31）: SHORT TP設定時にstate未作成 → reconciliation STOP → 修正済み
- 429リトライ（2026-03-26）: get_candles() 即STOP → 最大3回リトライに変更
- PARTIAL_FILL_TP_SET 誤発火（L-12）: TTLキャンセル後の既存ポジション誤検知 → 修正済み
- SL_PCT 極小時の 40917 無限STOPループ（L-13）: _place_sl で即クローズに変更
- Bitget デモ口座 SL 非発動バグ（L-14）: fill-history 照合（Change A/B）で対処済み
