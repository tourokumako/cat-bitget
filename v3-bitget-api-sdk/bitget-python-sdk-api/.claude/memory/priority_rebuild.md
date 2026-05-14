# priority_rebuild.md — Priority ゼロから再構築フェーズ (🧊 凍結・旧 framework)

> # 🧊 **このファイルは凍結 (2026-05-13・参照のみ)**
>
> このファイルは段階 A-1〜D framework 時代の正本 (2026-05-11 作成)。
> 2026-05-13 に ML pipeline (Phase 0〜7) へ切替済で、A-1〜D framework 自体が廃止。
> 新セッションでこのファイルを「現在の前提」として引用しない (L-180)。
>
> **現方針の正本**:
> - [../../WORKFLOW.md](../../WORKFLOW.md) — 現フェーズ + 次のタスク (唯一の正本)
> - [../../../CLAUDE.md](../../../CLAUDE.md) — 設計思想 + Phase 0〜7 骨格
> - [../../cc_ml_design_spec.md](../../cc_ml_design_spec.md) — ML pipeline 仕様書
>
> 中長期的に本ファイルを Phase 0〜7 体系で再構築するかは leak フリー再学習後に判断。

最終更新: 2026-05-11 (凍結マーク: 2026-05-13)
詳細・履歴は git history および [archive/](../../archive/) 配下を参照。

---

## §0 現フェーズ・次のタスク

**フェーズ**: 段階 A-1 **完了**（2026-05-12 02:12）/ 段階 A-2 **Web Claude 分業設計待ち**（2026-05-12 末切替）

**段階別ステータス**:

| 段階 | 内容 | ステータス |
|---|---|---|
| A-1 | 学習データ生成（5m bar × 1,432 指標 × 未来 MFE/MAE ラベル）| **完了**（train 394,573 / test 105,120 / 段階B温存 25,824 行）|
| **0-α** | **頭打ち原因分析**（auditor 指摘対応・A-2 大枠ドラフト確定の前提）| **完了**（2026-05-12 / 5 ファイル + ⑮ ダッシュボードタブ）|
| **0-β** | **頭打ち原因分析 追加分析**（構造的限界 vs Entry網羅性不足の切り分け）| **完了**（2026-05-12 / step5-8 CSV + addendum summary md）|
| A-2 | 大枠 Web Claude 分業中（**0-α/0-β 結果を Web Claude に渡して大枠確定**）| Web Claude 結論待ち |
| A-3 | 結果視認 + Entry 規則設計 | 未着手 |
| B | 新 Entry 規則 × Exit で 365d Replay 検証 | 未着手・**Exit 設計も Web Claude 議論対象** |
| C | ML 回帰モデル（B 頭打ち時のみ）| 未着手・条件付き |
| D | 最終 Replay + 採否判定 | 未着手 |

**Web Claude 分業切替の経緯（2026-05-12 セッション末）**:
- Claude Code 側で A-2 設計議論を 1 セッション中に 6 回撤回（中央値固定 / k=2固定 / 信頼度区分 / 月次$1,900判定軸 等）
- 既存フレーム流用癖・bottom-up 思考・段階間役割混同 が L-169/L-170/L-171 として教訓記録
- 大枠（L2 戦略骨格 / L3 Priority 枠組み / L4 A-2フロー / L5 段階 B Exit）を Web Claude で詰める分業に切替

**引き継ぎ資料**:
- [handoff_to_web_claude.md](handoff_to_web_claude.md) — Web Claude 用 self-contained 引き継ぎ資料（§0-§14）
- §8 に Web Claude に詰めてほしい優先質問 10 個

**次セッション最初にやること**:
1. このファイル §0 を再読
2. [handoff_to_web_claude.md](handoff_to_web_claude.md) を再読
3. lessons_active.md **L-168 〜 L-171** を再読（今セッションの手戻り教訓）
4. **Web Claude の議論結果を確認** → §2 に反映 → 実装フェーズへ
5. 実装着手前に Step 0 を改めて実行（目的整合性チェック L-166・着手前 3 項目）

**頭打ち原因分析の結果（2026-05-12 完了）**:
- 仕様書: [headroom_analysis_spec.md](headroom_analysis_spec.md)
- 成果物: [results/priority_rebuild/headroom_analysis_summary.md](../../results/priority_rebuild/headroom_analysis_summary.md) + step1-4 CSV + ⑮ ダッシュボードタブ
- データ前提: replay 1,157 trade のうち 733 (63.4%) が parquet test (2025) とマッチ。2026-Q1 の 424 trade は parquet 未生成のため仮想 Exit 分析から除外
- 判定マトリクス（仕様書 §5）の結果:
  - Entry 質 random より良い: **YES**（p_mfe_median=0.0032）
  - 完璧 K=96 Exit で全月 $1,900 達成: **NO**（worst_month=$40.41）
  - いずれかの仮想 Exit (57パターン) で全月 $1,900 達成: **NO**（0/57）
- **暫定判定: 構造的限界の可能性** — 完璧 K=96 Exit でも全月 $1,900 不達。Entry 規則そのものの再設計が必要
- 月次内訳で見えた構造ボトルネック: **2025-09 は matched 4 trade のみ・完璧 Exit でも $40**。月次 Entry 発火数の極端な偏り（4-240 trade/月）が構造的ボトルネック
- → A-2 大枠ドラフトには **ML を Exit に入れるだけでは届かない** ことを Web Claude に伝達必要。Entry 発火頻度の月次安定化 / 新 Priority 並立 / MTF 組合せ最適化 が必要

**頭打ち原因分析 追加分析 0-β の結果（2026-05-12 完了）**:
- 仕様書: [headroom_analysis_addendum_spec.md](headroom_analysis_addendum_spec.md)
- 成果物: [results/priority_rebuild/headroom_analysis_addendum_summary.md](../../results/priority_rebuild/headroom_analysis_addendum_summary.md) + step5-8 CSV
- 判定マトリクス（仕様書 §3）の結果:
  - worst month の trade 数が極端に少ない: **YES**（worst 2025-09 = 4 trade / matched median = 48 trade）
  - LONG 完璧 K=96 Exit でも合格ライン未達: **YES**（LONG-only monthly_mean=$1,715 < $1,900 / 月 ≥$1,900 = 3/9 ヶ月）
  - missed_fire: **判定不能**（Option A 抽出不可明示）
- **暫定判定: 構造的限界 + LONG Entry 規則の質低（両方該当）**
- 具体的な失敗構造:
  - worst month (2025-09) は P4-LONG / regime=range のみ 4 trade（downtrend Priority が一切発火していない）
  - best month (2025-11) は全 240 trade が regime=downtrend（急落相場依存）
  - LONG TIME_EXIT 100 trade / -$1,972 / 取りこぼし中央値 $16.77（時間切れ損切で取りこぼし大）
- → A-2 大枠ドラフトへの追加示唆:
  - 単純な ML Exit では届かない（worst month の発火数自体が極端に少ない）
  - **regime=range / uptrend で発火する新 Priority の追加**が必須
  - **LONG Entry 規則の質改善**（取りこぼし削減のための時間管理 + Entry 条件再設計）

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

### 合格ライン（本番投入可判定）

**月次 NET ≥ $1,900/月**（一次ソース: MEMORY/project_goal.md）
- 段階 B Replay で 365d 全 12 ヶ月が月次 $1,900 以上
- 単月でも未達なら不合格
- デイリー $60/day は参考値・日次絶対下限ではない

### 凍結ベースライン

- 旧 Priority (P1/P2/P4/P21/P23/P24) の 365d Replay 結果: **NET $4,506 / 月次平均 $370/月**
- 合格ラインまで **5.1 倍ギャップ**
- CSV: [results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv](../../results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv)

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

**合格条件: 全 12 ヶ月で月次 NET ≥ $1,900/月**（単月でも未達なら不合格）

| 設計 | 365d NET | 月次平均 | 最低月 NET | 月次合格 | 未達月数 | trade 件数 |
|---|---|---|---|:---:|---:|---|
| 凍結ベースライン（旧 P1-P24）| $4,506 | $370 | — | ❌ | 12/12 | 1,157 |
| 段階 B 設計 v1 | — | — | — | — | — | — |

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

- ~~このファイル（priority_rebuild.md）~~ — 🧊 旧 A-1〜D framework・凍結・参照のみ
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
