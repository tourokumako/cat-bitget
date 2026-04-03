# WORKFLOW.md — V9 改善フロー（2026-04-03 更新）

## セッション開始時の確認事項（最優先）

| 項目 | 状態 |
|------|------|
| 現在のフェーズ | **Phase 5（常時稼働）— BOT 停止中** |
| 本番ポジション | なし（BOT 停止中） |
| 次のタスク | **エントリーを taker に変更（最優先）**→ L-25 参照。post_only maker 指値の fill rate が 33% しかなく、これが根本問題。run_once_v9.py と replay_csv.py の両方を修正してから Replay で効果確認。その後 TP=3%/SL=0.5% に変更。 |
| ALLOW_LIVE_ORDERS | True（Claudeは変更しない） |
| open_position_long.json | なし |
| open_position_short.json | なし |
| paper_trading | false |
| MAX_ADDS_BY_PRIORITY | `{"2": 1, "4": 1, "22": 1, "23": 1, "24": 1}`（変更なし） |
| LONG_TP_PCT / SHORT_TP_PCT | 0.020（→ 次セッションで 0.030 に変更予定） |
| LONG_SL_PCT / SHORT_SL_PCT | 0.010（→ 次セッションで 0.005 に変更予定） |
| LONG_POSITION_SIZE_BTC / SHORT_POSITION_SIZE_BTC | 0.024（変更なし） |
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
| グリッドサーチ結果 | `results/grid_search_results.csv`（2026-04-03 実施済み） |
| 目標 NET/day | **$60/day**（0.12 BTC 制約内の現実的上限として合意済み） |

---

## 改善フロー（Phase 5）

**このフローを必ず順番通りに実行する。前のステップが完了するまで次に進まない。**

```
Step 1. 現状把握
  — Replay 実走・結果CSV確認
  — exit reason別・Priority別・LONG/SHORT別に集計

Step 2. 問題特定
  — どの Priority・どの Exit reason が損失源か特定
  — 損失トレードのエントリー時指標分布を確認（集計だけからの仮説立案禁止）

Step 3. 改善手段の選択（以下から最も効果が大きいものを1つ選ぶ）
  A. エントリー条件の改善
     — 勝ち vs 負けのエントリー時指標分布を比較
     — 差が大きい指標を根拠にフィルターを追加・変更
     — 「何件が影響を受けるか」を事前に計算して明示
  B. TP/SL 幅の最適化
     — Replay エントリー固定 → bar-by-bar グリッドサーチ（L-22）
     — TP%/SL% 組み合わせで edge・EV/trade・90d NET を試算
  C. add設計の変更
     — MAX_ADDS_BY_PRIORITY を変更
     — Replay で件数・TP率・EV への影響を確認
  D. Exit ロジックの変更
     — TIME_EXIT・PROFIT_LOCK 等の変更
     — 両ファイル（replay_csv.py / run_once_v9.py）同時更新必須

Step 4. 提案 → ユーザー承認
  — 手段・変更内容・期待値を明示してGO待ち ← STOP

Step 5. 最小差分修正（1回につき1箇所のみ）

Step 6. Replay 実走 → 結果確認 ← STOP

Step 7. 採用 or 却下
  — 採用: 次のステップへ
  — 却下: 即巻き戻し（cat_params_v9.json / コード）← Step 1 に戻る

Step 8. WORKFLOW.md 更新 ← STOP
  — セッション開始時の確認事項テーブルを最新状態に更新:
    ・現在のパラメータ（cat_params_v9.json と一致させる）
    ・Replay 現在値（NET・件数）
    ・次のタスク

Step 9. 本番反映
  — run_once_v9.py / cat_params_v9.json への反映確認 ← STOP

Step 10. Git コミット ← STOP
```

**現在の設計原則（2026-04-03 確定）:**
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
