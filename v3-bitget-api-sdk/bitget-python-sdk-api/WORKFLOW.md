# WORKFLOW.md — V9 改善フロー（2026-04-03 更新）

## セッション開始時の確認事項（最優先）

| 項目 | 状態 |
|------|------|
| 現在のフェーズ | **Phase 5（常時稼働）— BOT 停止中** |
| 本番ポジション | なし（BOT 停止中） |
| 次のタスク | **G: エントリー精度改善**（Replay を唯一の指標として使用） |
| ALLOW_LIVE_ORDERS | True（Claudeは変更しない） |
| open_position_long.json | なし |
| open_position_short.json | なし |
| paper_trading | false |
| MAX_ADDS_BY_PRIORITY | `{"2": 1, "4": 1, "22": 1, "23": 1, "24": 1}`（全Priority add=1） |
| Replay 基準値 | NET -$3,531 / 90日（-$39.3/day）。`results/replay_BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv` |
| Replay 用 CSV | `/Users/tachiharamasako/Documents/GitHub/cat-swing-sniper/data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv` |

---

## 改善フロー（Phase 5）

**このフローを必ず順番通りに実行する。前のステップが完了するまで次に進まない。**

```
Step 1. 現状把握      — replay_csv.py を実行・結果CSV確認
Step 2. 集計分析      — exit reason別・priority別・LONG/SHORT別に数値把握
Step 2.5. 個別分析   — 損失トレードのエントリー時インジケータ値を直接確認
                       （集計だけからの仮説立案禁止）
Step 3. 改善案提示    — Step 2.5 の共通パターンを根拠として仮説を立てる
                       複数案があればスコアリングして最優先の1つだけ提案する
                       「この変更で何件が影響を受けるか」を事前に計算して明示する
Step 4. ユーザー承認  — GO サインが出るまでコードを変更しない ← STOP
Step 5. 最小差分修正  — 1つの仮説に基づく最小変更のみ実施する
Step 6. Replay 実行   — 90日CSVで実行・結果提示・ユーザー確認 ← STOP
Step 7. 回帰確認      — Priority別 net が劣化していないか確認
                       「採用しますか？」と確認を取る ← STOP
Step 8. 採用 or 却下  — 却下なら即巻き戻し（cat_params_v9.json / コード）
Step 9. 本番反映      — run_once_v9.py / cat_params_v9.json への反映確認 ← STOP
Step 10. Git コミット  — 確認後コミット ← STOP
```

**注意:**
- `replay_csv.py` と `run_once_v9.py` の `_check_exits` は常に同期を保つこと
- Exit ロジックを変更したときは必ず両ファイルを同時に更新する

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
