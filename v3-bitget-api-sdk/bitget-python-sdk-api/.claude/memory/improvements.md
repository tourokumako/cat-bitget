---
name: 改善候補メモ
description: runnerの既知設計ギャップ・将来改善候補の一覧
type: project
---

## G-Runner-1: ~~1サイド1ポジション制限~~ → **✅ 実装済み（2026-03-26）**

- **対応内容**: run_once_v9.py を全面書き直し。MAX_SIDES=2（LONG/SHORT同時保有）対応完了。
- **変更ファイル**:
  - `runner/run_once_v9.py`: per-side state files / reconciliation / S-5/6 / pending / exit 全分岐
  - `runner/bitget_adapter.py`: `get_position_by_side()` / `wait_open_price_avg(hold_side)` 追加
- **state ファイル**: `open_position_long.json` / `open_position_short.json` / `pending_entry_long.json` / `pending_entry_short.json`
- **旧 `open_position.json` 移行**: `_migrate_legacy_state_files()` で起動時に自動移行
- **デモ動作確認（2026-03-26）**: LONG+SHORT同時保有 → STATE_DECLARED: open_long=true, open_short=true ✅
- **バックテスト根拠**: oneway比でDaily約120USD → 約60USD（半減）。早急対応と判断。

## G-Runner-2: ログローテーション未実装

- **現状**: `logs/cron.log` / `logs/live_run.log` / `logs/live_decision.log` / `logs/live_trades.csv` はすべて追記のみで上限なし
- **影響**: 長期稼働でファイルが肥大化する（1ヶ月 ≈ 8,640 run。当面は問題なし）
- **実装案**: `logrotate` または cron で週次リネーム（例: `live_run.log.YYYYMMDD`）
- **判断方針**: 本番稼働後、ファイルサイズが 100MB を超えたら対応する

**Why:** Phase 2c-bis で後回し判断（2026-03-25）。緊急度低。
**How to apply:** `ls -lh logs/` を定期確認し、100MB 超えたら logrotate 設定を議論する。

## G-Runner-3: バックテスト確認待ち事項（2026-03-26）

本番稼働後の観察から生まれた検証課題。バックテスト結果が出たら実装判断する。

### BT-1: P2_BB_MID_SLOPE_MIN を実際にP2判定に組み込む

- **現状**: `P2_BB_MID_SLOPE_MIN=8.0` はparamsに定義済みだが、P2ロジック本体で未使用（死んだパラメータ）
- **観察**: slope=-19.8でP2 LONG → STAGNATION_CUT (-9.25 USD) / slope=-29.1でP2 LONG → TP利確
- **検証内容**: `P2_BB_MID_SLOPE_MIN` を `-10 / 0 / +8` に変えたとき勝率・損益がどう変わるか
- **判断基準**: フィルターによる機会損失より損失削減が大きければ実装する

### BT-1: P2_BB_MID_SLOPE_MIN を実際にP2判定に組み込む → **NO-GO（2026-03-26）**

- **結果**: バックテストで悪化 → 実装しない

### BT-2: LONG/SHORT同時保有（MAX_SIDES=2）の効果 → **✅ 実装済み（G-Runner-1参照）**

- **バックテスト結果**: onewayにするとほぼ半減。Daily 120USD → 60USD。
- **対応**: 2026-03-26 に G-Runner-1 として実装完了。デモ動作確認済み。

## G-Runner-4: 本番ログ蓄積後に全エントリー品質を検証

- **内容**: P2/P22/P23/P24/P4 全priorityの勝率・損益・保有時間を `live_trades.csv` で集計・分析
- **検証観点**: priorityごとの勝率・平均損益・stagnation_cut率・add効果
- **判断基準**: 負けパターンに共通するフィルタ条件が見つかれば改善案をバックテストで検証
- **タイミング**: 本番トレード20〜30件程度溜まったら着手

**Why:** 本番観察でP2が中値圏クロスで天井を掴むケースが気になった（2026-03-26）。P2に限らず全priorityの実績を確認してから改善判断する。
**How to apply:** `live_trades.csv` が20〜30件になったら `trade_summary.py` で集計し、priority別の勝率・損益を確認する。

### 追加検証項目（2026-03-26）
- **曜日別・月末別の勝率集計**: 月末・週末に下げやすい傾向があるかを定量確認
- **仮説**: 月末・週末はLONGを抑制しSHORT優先に切り替えると成績改善する可能性
- **検証手順**: ① 本番ログで曜日・月末フラグ別の勝率を集計 → ② 効果が有意ならCAT_v9_regime.pyにフラグ追加してバックテスト比較 → ③ 改善確認後に実装
- **実装案（検証後）**: `BLOCK_LONG_WEEKENDS=true` / `BLOCK_LONG_MONTH_END=true` 等のパラメータ化
