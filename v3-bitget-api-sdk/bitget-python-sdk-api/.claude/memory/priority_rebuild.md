# priority_rebuild.md — Priority ゼロから再構築フェーズ 唯一の正本

最終更新: 2026-05-11
詳細・履歴は git history および [archive/](../../archive/) 配下を参照。

---

## §0 現フェーズ・次のタスク

**フェーズ**: 段階 A-1 **完了**（2026-05-12 02:12）/ 段階 A-2 未着手

**段階別ステータス**:

| 段階 | 内容 | ステータス |
|---|---|---|
| A-1 | 学習データ生成（5m bar × 1,432 指標 × 未来 MFE/MAE ラベル）| **完了**（train 394,573 / test 105,120 / 段階B温存 25,824 行）|
| A-2 | k=2 全探索（1,024,696 組）+ 単純 split 1 回 評価 | 未着手（次タスク）|
| A-3 | 結果視認 + Entry 規則設計 | 未着手 |
| B | 新 Entry 規則で 365d Replay 検証 | 未着手 |
| C | ML 回帰モデル（B 頭打ち時のみ）| 未着手・条件付き |
| D | 最終 Replay + 採否判定 | 未着手 |

**次セッション最初にやること**:
1. このファイル §0 / §3.0 / §4 を再読
2. lessons_active.md L-159 〜 L-167 を再読
3. **段階 A-2 k=2 全探索の設計案** を提示 → GO 待ち
4. GO 後に実装 → 実行 → 完了報告（5 点証跡）

---

## §1 最終目的・新方針

### 最終目的

**5m bot で $60/day（NET）を達成するため、MTF × 多指標の組合せで Entry タイミング精度を上げる**。

階層:
```
$60/day 達成
  ↑
Priority 群（再構築済・複数並立でリスク分散）
  ↑
高精度 Entry 規則（MTF × k=2 以上の組合せ）← いまここ
  ↑
MFE/MAE ラベル付き 5m bar × 1,432 指標素材
```

### 凍結ベースライン

- 旧 Priority (P1/P2/P4/P21/P23/P24) の 365d Replay 結果: **NET $4,506 / $12.34/day**
- 目標まで **5 倍ギャップ**
- 凍結ベースライン CSV: [results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv](../../results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv)

### 旧方針（regime 先行）からの転換理由

- regime 判定精度天井（v14 56% / stage3 33%）
- regime label の情報密度が低い（同 regime 内の trade 質ばらつきを弁別できない）
- 持続 16-28h vs trade median 15min の時間軸ズレ
- → regime 研究で蓄積した 1,432 指標素材を Priority Entry 規則に転用

---

## §2 設計マトリクス（軸全体の可視化）

### §2.1 入力データ

| 項目 | 値 |
|---|---|
| 期間 | 5 年（2021-04-01 〜 2026-03-31・1,826 日）|
| 単位 | 5m bar（525,708 行）|
| ファイル | [data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv](../../data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv) |

### §2.2 指標素材（1,432 列・剪定済）

正本（機械可読 JSON）: [results/regime_label_analysis/pruned_column_list.json](../../results/regime_label_analysis/pruned_column_list.json)
人間可読カタログ:
- [results/priority_rebuild/indicator_catalogue.md](../../results/priority_rebuild/indicator_catalogue.md)（ファミリー集約 + 完全一覧）
- [results/priority_rebuild/indicator_catalogue.csv](../../results/priority_rebuild/indicator_catalogue.csv)（機械可読 1,432 行）

| カテゴリ | 5m | 15m | 30m | 1h | 4h | 1d | 小計 | ファミリー数 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1-A 指標値・推移 | 55 | 56 | 62 | 63 | 58 | 54 | **348** | 66 |
| 1-B 値動きの形 | 58 | 58 | 58 | 58 | 58 | 57 | **347** | 20 |
| 1-C 構造的要素 | 134 | 140 | 137 | 132 | 113 | 81 | **737** | 59 |
| **合計** | **247** | **254** | **257** | **253** | **229** | **192** | **1,432** | **145** |

ファミリー = パラメータ（W, N, b, va, c）を畳んだベース名。例:
- 1-A: `rsi14`（5m〜1d）/ `adx14`（5m〜1h）/ `macd_hist`（全 TF）
- 1-B: `avg_body_ratio_W`（W=10/20/50 × 6 TF）
- 1-C: `dist_to_POC_pct`（N=50/100/200 × b=020/050/100 × 6 TF）

### §2.3 出力ラベル（未来 MFE/MAE）

K 窓 × 方向 × MFE/MAE = 4 × 2 × 2 = **16 ラベル/bar**

| K 窓（バー数）| 時間 |
|---|---|
| 12 | 1h |
| 24 | 2h |
| 48 | 4h |
| 96 | 8h |

ラベル定義:
- `LONG_MFE(K)` = max(high[t+1..t+K]) − close[t]
- `LONG_MAE(K)` = close[t] − min(low[t+1..t+K])
- `SHORT_MFE(K)` = close[t] − min(low[t+1..t+K])
- `SHORT_MAE(K)` = max(high[t+1..t+K]) − close[t]

### §2.4 探索空間

| 項目 | 値 |
|---|---|
| k=2 組合せ数 | 1,432C2 = **1,024,696 組** |
| 信号定義 | `(指標 A > threshold_A) AND (指標 B > threshold_B)` |
| threshold | train fold の中央値（look-ahead 防止）|
| k=3 以上 | **対象外**（爆発するため。stage 2 と同じ判断）|

### §2.5 検証設計

| 項目 | 値 |
|---|---|
| 分割 | 単純 split 1 回（fold 分割なし・2026-05-11 改訂）|
| train | 2021-04-01 〜 2024-12-31（3 年 9 ヶ月・全レジーム含む）|
| test | 2025-01-01 〜 2025-12-31（1 年）|
| 段階 B 用予備 | 2026-01-01 〜 2026-03-31（A-1/A-2 では未使用・段階 B 365d Replay の out-of-sample 用に温存）|
| 学習に使う期間 | train のみ（threshold 中央値）|
| 評価期間 | test のみ（look-ahead 完全防止）|

**改訂理由**: BTC 4 年周期 + 2024 ETF 構造変化を踏まえ、全レジームを含む 4 年通しで学習・1 年でテストするのが最適と判断。「学習 / 探索評価 / Replay 最終検証」の 3 層構造で 2026-Q1 を段階 B out-of-sample に温存。詳細は `review_lens.md` 2026-05-11 方針転換マトリクス参照。

### §2.6 評価指標

各組合せの発火点における未来 MFE/MAE 分布を以下 2 指標で評価:

| 指標 | 定義 | 意図 |
|---|---|---|
| **中央値** | 発火点 MFE / MAE の P50 | 典型例の質（外れ値耐性）|
| **MFE/MAE 比** | median(MFE) / median(MAE) | 利幅 / リスク比 |

平均（mean）は外れ値に引っ張られるため使用しない。上位 10% も偏り過ぎるため使用しない。

---

## §3 k=2 全探索 進捗管理表

実行前のテンプレ。実行後にこのセクションを更新する。

### §3.0 A-1 実行手順（3 段階・2026-05-12 追加）

「半日走らせて結果ゴミ」を回避するため、以下の順で動作確認してからフル実行する:

| 順 | コマンド | 期待時間 | 検証内容 | 出力 |
|---|---|---|---|---|
| 1 | `python3 scripts/priority_rebuild/build_labels.py --dry-run` | 数秒 | pruned_column_list.json 構造 + カテゴリ × TF 内訳 + 関数 import + 期待集合 1,432 確認（指標計算スキップ）| なし |
| 2 | `python3 scripts/priority_rebuild/build_labels.py --sample-days 7` | 数分 | 先頭 7 日 (2,016 行) で全処理通過 + 列集合 assert + MTF attach look-ahead 動作確認 | `labels_mfe_mae_sample.parquet` |
| 3 | `python3 scripts/priority_rebuild/build_labels.py` （引数なし）| 数時間〜半日 | フル 5y 処理 + train/test 2 parquet 出力 | `labels_mfe_mae_train_2021_2024.parquet` + `labels_mfe_mae_test_2025.parquet` |

各段階で失敗があれば次に進まない。1 → 2 → 3 の順を厳守する。

### §3.1 段階別進捗

| 段階 | 開始日 | 完了日 | 出力ファイル | ステータス |
|---|---|---|---|---|
| A-1 ラベル生成 | 2026-05-12 | 2026-05-12 | `labels_mfe_mae_train_2021_2024.parquet` (1.05 GB) + `labels_mfe_mae_test_2025.parquet` (0.30 GB) | **完了** |
| A-2 k=2 全探索 | — | — | `results/priority_rebuild/k2_search_results.json` | 未着手 |
| A-3 Entry 規則設計 | — | — | `results/priority_rebuild/entry_rules_draft.md` | 未着手 |
| B Replay 検証 | — | — | `results/replay/replay_priority_rebuild_*.csv` | 未着手 |
| C ML 学習 | — | — | （条件付き）| 未着手 |
| D 採否判定 | — | — | — | 未着手 |

### §3.2 k=2 探索の網羅マトリクス（試行/残）

| 方向 | K=12 (1h) | K=24 (2h) | K=48 (4h) | K=96 (8h) |
|---|:---:|:---:|:---:|:---:|
| LONG | 未試行 (0 / 1,024,696) | 未試行 | 未試行 | 未試行 |
| SHORT | 未試行 (0 / 1,024,696) | 未試行 | 未試行 | 未試行 |

合計 8 セル × 1,024,696 組 = 約 820 万通りの評価点（実装上は 1 回の k=2 全探索で全 16 ラベルを同時評価）。

---

## §4 検証結果集計表（実行後に埋める）

### §4.1 段階 A-2 TOP N（テンプレ・未実行）

| 方向 | K | rank | 指標 A | 指標 B | 中央値 MFE | 中央値 MAE | MFE/MAE 比 | walk-fwd 平均 | walk-fwd std |
|---|---|---|---|---|---|---|---|---|---|
| LONG | 12 | 1 | — | — | — | — | — | — | — |
| LONG | 12 | 2 | — | — | — | — | — | — | — |
| ... | | | | | | | | | |

### §4.2 段階 B Replay NET 比較（テンプレ・未実行）

| 設計 | 365d NET | $/day | win 率 | avgHold | trade 件数 |
|---|---|---|---|---|---|
| 凍結ベースライン（旧 P1-P24）| $4,506 | $12.34 | — | — | 1,157 |
| 段階 B 設計 v1 | — | — | — | — | — |
| ... | | | | | |

---

## §5 教訓・原則（継続適用）

regime 研究で蓄積した教訓は **Priority 再構築フェーズでも継続適用**:

### 必読 lesson

- **L-154**: post（未来）を判定材料に使わない → MFE/MAE ラベルは「正解」であって入力 X に含めない
- **L-155**: 中央値だけで判定材料を選ばない → MFE/MAE 比を併記
- **L-159**: 集計表示で best 1 自動採用しない
- **L-160**: Claude 主導のカテゴリ抽出禁止
- **L-161**: 完了報告前にコード総点検必須（grep 4 種 + L-162 自己 grep）
- **L-162**: 絞り込み示唆語彙禁止（採用候補 / 効く / 重要 等）
- **L-163**: 学習目的 vs 検証目的の整合性 → 学習も検証も MFE/MAE で統一
- **L-165**: 詳細な仕様が来ても目的整合性確認を省略しない
- **L-166**: 着手前の 3 項目チェック（粒度・カバレッジ・直接性）

### feedback 必読

- [feedback_early_objection.md](../../../../.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_early_objection.md) — 着手前の目的整合性チェック
- [feedback_design_judgment_owner.md](../../../../.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_design_judgment_owner.md) — 設計探索で推奨方針を断言
- [feedback_exhaustive_search.md](../../../../.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_exhaustive_search.md) — 網羅マトリクスで未試行セル可視化

---

## §6 試行禁止リスト

### 設計関連

- ❌ 既存 Priority(P1-P24) を改修して使う（ゼロから再構築方針）
- ❌ k=3 以上の組合せを最初から試行（k=2 完走後に検討）
- ❌ MFE/MAE ラベル（未来情報）を入力 X に含める（リーク）
- ❌ 全 fold 共通中央値で二値化（stage 2 で発覚した leak。fold 別に厳密化）
- ❌ 平均（mean）を主評価指標にする（外れ値耐性なし・中央値使用）
- ❌ 上位 10% のみで評価（cherry-picking）

### regime 研究関連

- ❌ regime 判定の新規試作（v15, v16, ...）
- ❌ 思考フレーム自己点検の regime 文脈での起動
- ❌ §13 v3 段階1〜段階3 フローの新規実行
- ❌ 「regime → Priority 振り分け」アーキテクチャの復活

### 行動ルール関連

- ❌ 仕様詳細度が高いと目的整合性チェックを省略する（L-165）
- ❌ 着手前 3 項目チェック（粒度・カバレッジ・直接性）を省略（L-166）
- ❌ 完了報告前のコード総点検 grep を省略（L-161）

---

## §7 引き継ぎリソース

### 必読（現フェーズ）

- このファイル（priority_rebuild.md）— Priority 再構築の唯一の正本
- [WORKFLOW.md](../../WORKFLOW.md) — 現フェーズ + 次のタスクのポインタ
- [CLAUDE.md](../../../CLAUDE.md) — 設計思想・現方針
- [lessons_active.md](lessons_active.md) — L-159〜L-166 重点

### 素材（regime 研究からの転用）

- [pruned_column_list.json](../../results/regime_label_analysis/pruned_column_list.json) — 1,432 指標の正本
- [stage2_combination_search.py](../../scripts/regime/stage2_combination_search.py) — k=2 全探索フレーム（評価関数のみ MFE/MAE に差し替え予定）
- [analyze_regime_label_features.py](../../scripts/regime/analyze_regime_label_features.py) — 指標計算ロジック
- [shape_features.py](../../scripts/regime/shape_features.py) — shape features（1-B）
- MTF resample / attach ロジック（stage1*_meta.py 内）

### 参照のみ（凍結中）

- [regime_research.md](regime_research.md) — 🧊 凍結・素材転用元
- [regime_trial_log.md](regime_trial_log.md) — 🧊 凍結・履歴
- ダッシュボード タブ⑬ レジーム持続分布 / タブ⑭ trade×境界 整合性検証（参考表示）
