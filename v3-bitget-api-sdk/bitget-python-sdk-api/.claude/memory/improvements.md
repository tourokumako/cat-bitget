---
name: 改善候補メモ
description: runnerの既知設計ギャップ・将来改善候補の一覧
type: project
---

## G-Runner-1: 1サイド1ポジション制限（原本はMAX_SIDES=2）

- **原本**: `CAT_v9_regime.py` L2359 `max_sides = int(params.get("MAX_SIDES", 2))` / params L2831 `"MAX_SIDES": 2`
  → LONG/SHORT同時保有を前提に設計
- **runner現状**: `pos_side_mismatch → NOOP`（1サイドのみ）。ポーティング時の簡略化。
- **影響**: LONGポジション保有中にSHORTシグナルが出ても無視される。
- **現時点の緊急度**: 低（2026-03-25 の24時間テストでは pos_side_mismatch = 0件）
- **実装コスト**: open_position.json の2ファイル化 + TP/SL/ADD/reconciliation の全サイド分岐が必要
- **判断方針**: 本番データが溜まってSHORT機会損失が顕在化してから検討する

**Why:** ポーティング時に実装コスト優先で簡略化。原本はLONG/SHORT同時前提。
**How to apply:** 本番稼働後に trade_summary.py で pos_side_mismatch 件数を定期確認し、顕在化したら設計を議論する。

## G-Runner-2: ログローテーション未実装

- **現状**: `logs/cron.log` / `logs/live_run.log` / `logs/live_decision.log` / `logs/live_trades.csv` はすべて追記のみで上限なし
- **影響**: 長期稼働でファイルが肥大化する（1ヶ月 ≈ 8,640 run。当面は問題なし）
- **実装案**: `logrotate` または cron で週次リネーム（例: `live_run.log.YYYYMMDD`）
- **判断方針**: 本番稼働後、ファイルサイズが 100MB を超えたら対応する

**Why:** Phase 2c-bis で後回し判断（2026-03-25）。緊急度低。
**How to apply:** `ls -lh logs/` を定期確認し、100MB 超えたら logrotate 設定を議論する。
