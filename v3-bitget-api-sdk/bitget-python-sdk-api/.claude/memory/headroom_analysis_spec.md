# headroom_analysis_spec.md — 頭打ち原因分析 仕様書

作成日: 2026-05-12
位置付け: 段階 A-2 大枠ドラフト確定の前提作業（新項目 0-α）
背景: auditor 指摘 5-1（頭打ち原因未分離）・1-1（5.1倍楽観）への対応

---

## §1 目的

旧 P1-P24 が月次 $370 で頭打ちした原因を、以下の4候補のどれかに特定する:
- Entry規則の精度不足
- Exit設計の損益取りこぼし
- Position管理の機会損失
- 構造的限界（市場効率性が高く ML でも届かない）

結果次第で、A-2 大枠ドラフトの方向（ML をどこに入れるか）を決定する。

---

## §2 入力データ

| データ | 場所 |
|---|---|
| 旧 P1-P24 365日 Replay 結果（1,157 trade）| `results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv` |
| 5y × 5m × 1,432 指標 + MFE/MAE ラベル | `results/priority_rebuild/labels_mfe_mae_train_2021_2024.parquet` |
| 同上 test 期間 | `results/priority_rebuild/labels_mfe_mae_test_2025.parquet` |
| 旧 P1-P24 パラメータ | `config/cat_params_v9.json` |

---

## §3 着手前3項目チェック（L-166）対応

| 項目 | 状態 | 対応 |
|---|---|---|
| ①データ粒度 | 〇 | 対応不要 |
| ②カバレッジ | △ | 6 priority × 2 side × 3 regime = 36セル 平均32 trade。P21-SHORT 等分布偏りあり。**各セルの trade 数を明示し、N=10未満のセルは集計表示のみ・結論判定には使わない** |
| ③直接性 | 〇（前提注記要）| 手順4は CSV 既存 mfe_usd/mae_usd を使った**近似計算**。実 Replay 再実行ではない。**実 Replay との若干の乖離前提を結果報告に明記する** |

---

## §4 分析手順

### 手順1: trade レベルの分解

1,157 trade を以下の軸で集計し、分布・偏りを可視化:

| 軸 | 集計内容 |
|---|---|
| Entry時 MFE/MAE 分布 | `mfe_usd` / `mae_usd` の中央値・四分位・分布図 |
| MFE 取りこぼし | `mfe_usd - net_usd` を trade ごとに計算 |
| MAE 食らい度 | `mae_usd` と `net_usd` の関係 |
| 保有時間 vs MFE 到達時間 | `hold_min` と MFE 到達タイミング（K=12/24/48/96 ラベルで比較）|
| 方向別性能 | LONG / SHORT 別 net_usd 中央値・分布 |
| 時間帯別性能 | `entry_hour` × `entry_weekday` 集計 |
| 市場局面別性能 | `adx_at_entry` / `bb_width_at_entry` / `atr_14` 別性能比較 |

セル別 trade 数を必ず併記。N<10 セルは集計のみ。

### 手順2: Entry 質の評価

旧 P1-P24 Entry 1,157 時刻の MFE/MAE をベンチマーク比較:

| 比較対象 | 中身 |
|---|---|
| ランダム Entry | 5年間からランダムに1,157時刻取った MFE/MAE 分布と比較 |
| 全 bar 平均 | 525,708 bar 全体の MFE/MAE 中央値と比較 |
| 上位 N% bar | 各 K窓で MFE 上位 5% / 10% / 20% の中央値と比較 |

統計検定: Mann-Whitney U test または同等の非パラメトリック検定。

判定:
- 旧 P1-P24 MFE/MAE がランダムより**有意に良い** → Entry規則は機能している
- ランダム並み → Entry規則が機能していない

### 手順3: Position レベルの分解

| 軸 | 集計内容 |
|---|---|
| 1日 trade 数分布 | 365日 × 日ごとの trade 数（最大/最小/中央値）|
| 同時保有数 | bar ごとの保有 Priority 数（最大/中央値）|
| 撃ち損ね回数 | Entry 条件成立だがポジ持ってて撃てなかった回数（Replay ログから抽出・要 CC 確認）|
| Priority 別サイズ配分 | 各 Priority の `size_btc` 平均・合計 net_usd |

判定:
- 撃ち損ね多い → Position管理が原因
- 配分偏り大きい → サイズ配分が原因

### 手順4: 仮想 Exit シミュレーション

旧 P1-P24 Entry 1,157 時刻に対して **Exit パラメータだけ変えて再計算**:

| Exit パターン | 仮想 NET の計算方法 |
|---|---|
| 完璧 Exit（理論上限）| 各 trade の K窓内 MFE をそのまま net_usd（理論最大）|
| TP/SL を MFE/MAE 統計から最適化 | 全 trade の MFE/MAE 中央値 × 0.5 / 0.7 / 0.9 で TP/SL 設定 |
| トレーリング比率変更 | TRAIL_RATIO = 0.5 / 0.7 / 0.9 で再計算 |
| 時間Exit 変更 | TIME_EXIT_MIN = K=12/24/48/96 で再計算 |
| MFE 50% / 70% / 90% 到達 Exit | MFE が指定%到達時点で Exit と仮定 |
| MAE 早期 SL | MAE が ATR × 2 拡大時点で SL と仮定 |

**前提注記**: CSV の mfe_usd/mae_usd を使った近似計算であり、実 Replay 再実行ではない。実際の bar 単位の動きを完全に再現するものではなく、若干の乖離前提。

判定:
- 完璧 Exit で月次 $1,900 超え → Exit 改善だけで合格ライン到達可能
- 完璧 Exit でも月次 $1,900 届かない → Entry規則自体に伸びしろ要
- Exit パラメータ変更で大幅改善 → Exit 設計が現状非最適

---

## §5 結論パターンと次のアクション

| 手順1-4の結果パターン | 結論 | A-2 大枠ドラフトへの影響 |
|---|---|---|
| 手順2 Entry質OK + 手順4 Exit改善余地大 | Exit が原因 | ML を Exit 設計に入れる方針に切替 |
| 手順2 Entry質低 + 手順4 Exit改善余地大 | 両方原因 | ML を Entry/Exit 両方に入れる |
| 手順2 Entry質低 + 手順4 完璧Exitでも届かない | 構造的限界 | 目標$1,900 再考 or 別アプローチ |
| 手順3 撃ち損ね大 | Position が原因 | Priority追加・制御ロジック改善優先 |
| 時間帯/方向/局面偏り大 | 発火偏りが原因 | 補完 Priority 追加で伸びる |

---

## §6 成果物

| ファイル | 内容 |
|---|---|
| `results/priority_rebuild/headroom_analysis_summary.md` | 4手順の結果サマリー + 結論パターン判定 |
| `results/priority_rebuild/headroom_step1_trade_decomp.csv` | 手順1の集計 |
| `results/priority_rebuild/headroom_step2_entry_quality.csv` | 手順2の比較 |
| `results/priority_rebuild/headroom_step3_position.csv` | 手順3の集計 |
| `results/priority_rebuild/headroom_step4_virtual_exit.csv` | 手順4の仮想Exit結果 |
| ダッシュボードタブ追加 | 「頭打ち原因分析」タブ（手順1-4の主要グラフ表示）|

ダッシュボード視覚確認原則準拠: 数値だけの md/csv 単独報告は不可・必ずダッシュボードで視認可能にする。

---

## §7 所要時間目安（コンピューター時間）

| 内訳 | 時間 |
|---|---|
| 手順1 集計 | 数分 |
| 手順2 統計検定 | 数十分 |
| 手順3 Position 集計 | 数分 |
| 手順4 仮想 Exit シミュレーション（10-50 パターン）| 数時間 |
| ダッシュボード反映 | 数十分 |
| **合計** | **半日〜1日** |

---

## §8 完了報告必須証跡 5点（WORKFLOW.md §役割+行動原則 準拠）

1. コード総点検 grep 結果（全件・"no matches"含む）
2. 数値の二重提示（サマリー + 出典ファイル引用・行番号付き）
3. 成果物ファイルの実体（パス + 行数 + 更新時刻）
4. 実行ログ（コマンド・開始時刻・終了時刻・所要時間・終了コード）
5. 絞り込み示唆語彙の自己 grep 結果

1つでも欠けたら完了とみなさない。
