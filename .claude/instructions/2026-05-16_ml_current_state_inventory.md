# 【タスク】現状 ML 学習内容の完全棚卸し（Layer 1+2 計画書ドラフト前提）

(Web Claude レビュー済・まこさん GO 待ち 2026-05-16)

## 構造化ルール準拠

- 保存先: `.claude/instructions/2026-05-16_ml_current_state_inventory.md`
- 完了報告: `.claude/instructions/2026-05-16_ml_current_state_inventory_completion.md`
- **本指示書を上記パスに保存し commit すること**（対話ルール19・指示書のファイル保管義務）

---

## 着手前必読（省略禁止・L-179/L-180/L-181）

1. WORKFLOW.md §🛑 2大絶対規定 / §🔴 現在のフェーズ（改訂12・Phase 4-b/5 v3 不合格）
2. CLAUDE.md §⛔ 絶対禁止 / §目標 / §現在の方針
3. cc_ml_design_spec.md §1.1〜§1.6.2 / §3 / §4 / §8
4. handoff_to_web_claude_v7_session_20260515.md §最重要1〜3 / §A-1〜A-5 / §D-8
5. lessons_active.md L-179（leak）/ L-183（§8違反 test fit）/ L-188（部分採用 bit-exact）/ L-189（ハイパラ限界）/ L-190（spec改訂メタルール）/ L-192（類型H違反）
6. results/priority_rebuild/leak_incident_20260513.md（leak 全14件記録）
7. .claude/rules/false_positive_incident_policy.md §0-1 / §0-2 / §2 類型A〜H / §5 関所A〜G
8. .claude/instructions/2026-05-15_priority_vs_ml_stocktake_completion.md（前回 CC 棚卸し報告・本タスクの拡張版）

---

## Step 0-1: 必読ファイル引用（読んだフリ防止）

完了報告の冒頭に、以下を**逐語引用**で貼り付けること（要約禁止）：

a. cc_ml_design_spec.md §1.1「ラベル」全文（16 ラベル定義）
b. cc_ml_design_spec.md §1.2「特徴量」全文（1432 指標の根拠）
c. cc_ml_design_spec.md §3.1「Exit 候補（第1弾）」全文
d. cc_ml_design_spec.md §3.3「Exit 選択方法」全文
e. handoff_to_web_claude_v7_session_20260515.md §A-4「ML が手動 Priority より狭い範囲しか学習していない（CC 棚卸し定量確定）」全文
f. handoff_to_web_claude_v7_session_20260515.md §最重要3 まこさん発言全文
g. WORKFLOW.md §🔴現在のフェーズ §「次のタスク」全文
h. 前回 CC 棚卸し報告（2026-05-15_priority_vs_ml_stocktake_completion.md）の §「カバレッジ集計」全文

各引用が期待値と一致しない / 省略 → STOP

---

## 背景

Layer 1+2 改訂版計画書（Web Claude が作成中）の前提として、**現状の ML が実際に何をどう学習しているか**を実データレベルで棚卸しする必要がある。

これまで Web Claude は仕様書レベルの数字（1432 指標・16 ラベル・k=3 等）で議論してきたが、実データ（cluster_profile / feature_importance / training_summary / monthly_pnl 19combo 別 等）の中身を把握していない。これが前任 §D-8（手動 Priority vs ML 学習範囲の突合せ verify を一度もせずに ML 議論）の構造的再演となっており、本タスクで解消する。

**handoff §最重要3 まこさん発言**:
> 「現状の Priority の Entry/Exit ロジックには指標と閾値が組み込まれている。せっかく ML で大量なパターンを勉強できるなら、最低限ここで使ってる閾値は使ってほしい。手動のロジックより狭い範囲しか勉強してなかったら、目標達成できるわけない。」

本タスクは「ML が現在何を学習しているか」を**指標 + 閾値 + 組み合わせ深さ + クラスタ + Exit 選定結果 + 月次 PnL 分布 まですべて**棚卸しし、Web Claude が Layer 1+2 計画書を書ける状態にすることが目的。

---

## 前提（動かさない・前セッション確定事項）

- K12 LONG refit 維持（num_leaves=15 部分採用・commit d9d322c）
- Phase 2 = 改訂後 spec 4 指標 ALL PASS（cc_ml_design_spec §1.6 案G）
- 絶対閾値 drift 対処 = rolling 365日（2026-05-15 改訂11）
- Phase 4-a k=3 採用（silhouette 0.510・全 cluster K12 LONG q99 サンプル ≥100）
- Phase 4-b/5 v3 = leak フリー実行済・ただし Phase 5 不合格（合計 -$985.35・全12ヶ月マイナス）
- 道 B（Layer 1+2 完走 → Layer 3 は本番運用後）採用済
- 第一/第二絶対規定（Prime Directive / ポジ上限 0.12 BTC 合計厳守）

本タスクのスコープは「棚卸し」のみ。改善案・推奨判断・新規実装は本タスクで一切行わない。

---

## 棚卸し対象（10 項目）

### 項目 1: Phase 0 ラベルデータ実態

- ラベル parquet 3 ファイル（train_2021_2024 / test_2025 / test_2026_q1）について報告：
  - sha256（先頭 12 桁）
  - 行数・列数・期間（min/max timestamp）
  - ファイルサイズ
- ラベル 16 個それぞれの統計値（train 期間のみ）：
  - mean / std / p50 / p90 / p99 / max
  - NaN 件数 / Inf 件数 / 負値件数（MFE/MAE は非負想定）
- ラベル間相関行列 16×16（LONG/SHORT 別 + K 窓別の構造を見るため）

### 項目 2: Phase 1 v2 LightGBM モデル実態（leak フリー再学習版）

- 16 モデルそれぞれの実際のハイパラ（K12 LONG refit 含む）：
  - learning_rate / n_estimators / num_leaves / max_depth / min_data_in_leaf
  - feature_fraction / bagging_fraction / bagging_freq / reg_lambda
  - bagging_seed / data_random_seed / feature_fraction_seed
  - best_iteration（early stopping 結果）
- 16 ラベルの train RMSE / valid RMSE / 乖離率
- 16 ラベルの label_std と RMSE/label_std 比率（cc_ml_design_spec §1.6 指標 3 評価軸）

### 項目 3: Phase 1 feature_importance top20（全 16 ラベル）

- 16 ラベル × top20 = 320 行の表：
  - ラベル名 / rank / 特徴量名 / importance 値（importance_type='split' か 'gain' か明示）
  - 特徴量カテゴリ（1-A / 1-B / 1-C のどれか）
  - 時間軸（5m / 15m / 30m / 1h / 4h / 1d）
- ブラックリスト top20 ヒット件数（dist_to_fib_v2_* / resistance_distance_* / support_distance_* / nearest_level_*）
- 1 ラベル内で importance > 50% を占める単一列があるか（leak 兆候判定）

### 項目 4: Phase 2 改訂後 spec の 4 指標実数値

- phase2_summary.json の overall_pass / 4 指標 PASS/FAIL 個別
- 指標 1: q99 net_quality 加重平均 + 8 組合せ別内訳
- 指標 2: net_quality 最小値（8 組合せ中の min）
- 指標 3: valid_rmse / label_std 比率（16 ラベル個別 + < 1.5 該当数）
- 指標 4: mean_real_MFE / mean_real_MAE 比率（8 組合せ個別 + > 1.0 該当数）

### 項目 5: Phase 3 trial 結果

- K 窓別 num_leaves 試行結果（パターン B = 案 G）
- 各 K × side の改善幅（24 組合せ加重・q99 加重）
- K12 LONG refit 採用判定の根拠（+0.70pp 上方修正の出典）

### 項目 6: Phase 4-a クラスタ実態（k=3）

- cluster_profile.csv の中身（cluster × 16 予測値平均・全 3 cluster）
- 各 cluster の train サンプル数・test 2025 サンプル数
- 各 cluster の性質言語化（cluster 0 / 1 / 2 がどんな Entry 性質か）
- silhouette score（採用根拠）
- size_ratio（min/max・L-186 退化分割排除確認）

### 項目 7: Phase 4-b v3 cluster_best_exit 19 行内訳

- cluster_best_exit_option5_v3.csv の全 19 行：
  - combo 名（cluster × K × side × q-level）
  - 選定された exit_type（time_exit / fixed_tp / trailing）
  - exit_type 別の選定パラメータ（time_exit_N / fixed_tp_pct / trailing_ratio）
  - train PnL（idxmax 採用の根拠数値）
- exit_type 別集計：
  - time_exit: 何 combo / train 合計 PnL / test 合計 PnL
  - fixed_tp: 何 combo / 同上
  - trailing: 何 combo

### 項目 8: Phase 5 v3 月次 PnL 分布（19 combo 別）

- monthly_pnl_option5_v3.csv の中身：
  - 12 ヶ月 × 19 combo マトリクス（合計 228 セル + 月次合計 12 + combo 合計 19）
  - 合格セル数（月次 NET ≥ $1,900 / セル）
- combo 別の全期間合計 PnL（昇順ソート）
- no_trade 内訳（87% の内訳）

### 項目 9: CC 棚卸し詳細（2026-05-15 報告の数値展開）

前回報告の「カバレッジ集計」で示された 16 指標 × 4 カテゴリについて、個別指標名と判定根拠を全件展開

### 項目 10: 1432 指標カタログ全ファミリーリスト

- indicator_catalogue.csv の全 1432 行から、ファミリー単位で全列挙
- 各ファミリーの簡易説明
- 1w / 1M 軸の現状未投入確認

---

## 報告フォーマット指定

| 項目 | 出力ファイル |
|---|---|
| 項目 1 | `results/priority_rebuild/inventory_2026_05_16/01_phase0_labels.md` |
| 項目 2 | `results/priority_rebuild/inventory_2026_05_16/02_phase1_models.csv` |
| 項目 3 | `results/priority_rebuild/inventory_2026_05_16/03_feature_importance_top20.csv` |
| 項目 4 | `results/priority_rebuild/inventory_2026_05_16/04_phase2_4indicators.md` |
| 項目 5 | `results/priority_rebuild/inventory_2026_05_16/05_phase3_trial.md` |
| 項目 6 | `results/priority_rebuild/inventory_2026_05_16/06_phase4a_clusters.md` |
| 項目 7 | `results/priority_rebuild/inventory_2026_05_16/07_phase4b_exits.csv` |
| 項目 8 | `results/priority_rebuild/inventory_2026_05_16/08_phase5_monthly_combo.csv` |
| 項目 9 | `results/priority_rebuild/inventory_2026_05_16/09_stocktake_detail_16indicators.md` |
| 項目 10 | `results/priority_rebuild/inventory_2026_05_16/10_indicator_families.md` |
| サマリー | `results/priority_rebuild/inventory_2026_05_16/SUMMARY.md` |

---

## ガード A〜H（本指示書に組み込まれた防止ルール）

ガード A: fit/transform系処理なし（棚卸しのみ）
ガード B: 手計算で PASS 主張禁止（出典ファイル引用必須）
ガード C: 未来値 leak なし
ガード D: 絞り込み示唆語彙禁止（SUMMARY.md）
ガード E: やったフリ禁止（grep 結果含む）
ガード F: 実測値のみ（推測なし）
ガード G: CSV 本体を完了報告に整形禁止（11ファイルのsha256+行数+更新時刻のみ）
ガード H: 10項目すべての出力ファイル必須

---

*保存日時: 2026-05-16*
*保管義務: 対話ルール19*
