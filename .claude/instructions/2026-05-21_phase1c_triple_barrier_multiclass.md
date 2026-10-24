# Phase 1-c: Triple Barrier multiclass + EV フィルタ (full 枠)

作成日: 2026-05-21
発注者: Web Claude (PM) → CC
種別: 大規模新規実装 (Triple Barrier ラベル新規生成 + multiclass 学習 7 モデル + EV フィルタ + simulated PnL)
規模: full 枠 300-400 行 (L-198 / memory ルール 24 準拠)
保存先: `.claude/instructions/2026-05-21_phase1c_triple_barrier_multiclass.md`

---

## §0 背景・スコープ

### §0.1 経緯

Phase 1-b (commit 2f01a98) で「Phase 1-a RMSE 学習では SL hit が TP hit の 1.78 倍・SL/TP 時間順序を学習していない」と物理証跡で判定 (NO-GO)。

audit#18 (2026-05-21) + ChatGPT 独立検証で、当初計画の「直接 PnL maximizing + Sharpe maximizing custom objective」は **barrier hit の non-smooth により grad/hess 未定義** で数学的に成立しないと判明。

A 案 (Triple Barrier 3-class multiclass + EV フィルタ) に切替・まこさん 2026-05-21 再承認。learning_design_v3.md §B-15 + phase_flow_v3_with_recovery.md §2 を同期書き換え済 (commit 5890622)。

### §0.2 本タスクスコープ

| 項目 | 値 |
|---|---|
| 学習対象 | **Triple Barrier 3-class multiclass × K=7** (新規 7 モデル) |
| 流用 | Phase 1-a RMSE 14 モデル (新規学習なし・参照のみ) |
| barrier 閾値 | **ATR ベース動的** (詳細 §4.2) |
| 目的関数 | LightGBM **multiclass** (softmax-cross-entropy・標準実装・bug 余地ゼロ) |
| 仮想 Exit シミュレーション | EV フィルタ後の simulated PnL を K=12 主判定で評価 |
| ハイパラ | デフォルト (Optuna は Phase 2) |
| Sharpe maximizing | **本タスクでは扱わない** (Phase 2 以降・smoothing 設計後) |

### §0.3 スコープ外

- Sharpe maximizing custom objective
- Optuna ハイパラ探索
- Exit 12 種本格設計 (Phase 4-b)
- SHORT 側モデル (対称性で LONG 予測値を Phase 5 Replay で流用)
- Triple Barrier ラベル定義の barrier 閾値最適化 (本タスクは固定 multiplier・最適化は Phase 2 以降)

---

## §1 着手前必読 (6 件・順番厳守)

1. `.claude/memory/learning_design_v3.md` §B-15 + 修正履歴 #13 (本タスクの根拠・commit 5890622 後の確定文)
2. `.claude/memory/phase_flow_v3_with_recovery.md` §2 全体 (本タスク詳細・barrier 閾値だけ §4.2 で ATR ベース確定)
3. `.claude/instructions/2026-05-21_audit18_phase1c_custom_objective_output.md` (audit 出力・3 懸念詳細) — **物理ファイル不在確認・要旨は §0.1 + #1 修正履歴 #13 + #2 §2.1 で代替 (まこさん 2026-05-21 案 α 承認)**
4. `cc_ml_design_spec.md` §1 / §1.6 / §8 (Phase 1 関連 spec・Prime Directive)
5. `.claude/rules/false_positive_incident_policy.md` §0-1 Prime Directive / §0-2 ポジション上限 / Type C (leak) / Type H (price-dependent)
6. `.claude/memory/lessons_active.md` L-179 (leak 4 点) / L-180 (引用前 verify) / L-189 (Phase 4-b 必須) / L-198 (指示書サイズ)

着手前 verify:
- L-179 4 点チェック内容を 1 行ずつ書き出して理解確認 (完了報告に含める)
- §1 で読んだ各ファイルの該当行番号を完了報告に列挙

---

## §2 Prime Directive 事前宣言 (cc_ml_design_spec §8)

実装着手前に以下 9 項目を「本番運用の推論時点 t で因果的に取得可能か YES/NO」1 行ずつ宣言:

| # | 変数 | 期待宣言 |
|---|---|---|
| 1 | 特徴量 1,414 個 (Phase 1-a 流用・blacklist 後) | YES |
| 2 | Phase 1-a 予測値 (predictions_test_2025.parquet) | YES (本番では学習済モデルから生成可) |
| 3 | atr14_pct__{TF} × 5 TF (barrier 閾値計算入力) | YES (時点 t で確定・shift(1) ガード適用済) |
| 4 | close[t] (entry 価格) | YES |
| 5 | high[t+1..t+K] / low[t+1..t+K] (Triple Barrier ラベル計算) | YES (学習データ・本番推論時は予測値で代替) |
| 6 | TP/SL 閾値 = ATR × multiplier (固定 multiplier・本タスク §4.2) | YES |
| 7 | EV フィルタ計算 (P_TP × TP_USD_est − P_SL × SL_USD_est) | YES (TP_USD_est / SL_USD_est は train 過去 N trade の avg・shift(1) で leak ガード) |
| 8 | 14 ラベル MFE/MAE pct 列 (drop 必須・Triple Barrier ラベル定義に直接使わない) | drop_cols 入り (Phase 1-a 同様) |
| 9 | is_maintenance 列 | drop (Phase 5 で参照しない設計) |

drop_cols リストを明示してから fit() を呼ぶこと。

---

## §3 ポジション上限 事前 verify (cc_ml_design_spec §8)

Phase 1-c では:
- 学習段階: 学習のみ・ポジションなし → sum(active_position_btc) = 0 ✅
- simulated PnL 段階: Phase 1-b と同じ naive Replay → 0.01 BTC × 同時保有上限 12 = 0.12 BTC max

simulated PnL ループ内で `assert sum(active_position_btc) <= 0.12` を各時点 t で verify・違反検知時は即 STOP + 報告。

---

## §4 実装仕様

### §4.1 ファイル構成

```
scripts/priority_rebuild/
  build_triple_barrier_labels.py    # 新規・Triple Barrier ラベル生成
  run_lgbm_phase1c_multiclass.py    # 新規・LightGBM multiclass 学習
  run_phase1c_ev_simulation.py      # 新規・EV フィルタ + simulated PnL
  utils/leak_check.py               # Phase 1-a 流用 + multiclass 用拡張

configs/
  phase1c_multiclass.yaml           # 新規・multiclass ハイパラ + barrier multiplier

results/priority_rebuild/ml_phase1c_triple_barrier/
  labels_triple_barrier_train_2021_2024.parquet   # 394,561 行 × K=7 × 3-class
  labels_triple_barrier_test_2025.parquet         # 105,120 行 × 同上
  label_distribution.csv                          # 7 K × 3-class %
  models/
    triple_barrier_K{K}.txt × 7                   # multiclass モデル
  predictions_multiclass_test_2025.parquet        # 105,120 行 × 7 K × 3 確率 (21 列)
  training_summary.csv                            # 7 行 (K / logloss train/valid / iter)
  feature_importance_top20_multiclass.csv         # 7 K × top20 = 140 行
  ev_filter_simulated_pnl_K{K}.csv × 7
  precision_recall_K{K}.csv × 7
  leak_check_report.json
  execution_log.txt
```

### §4.2 Triple Barrier ラベル定義 (ATR ベース動的閾値)

各 5m bar t について、K bars 以内に以下のどれが先に起きるかを 3 クラスで分類:

- **TP** (label=2): high が `close[t] × (1 + ATR_pct × TP_MULT / 100)` 到達
- **SL** (label=0): low が `close[t] × (1 - ATR_pct × SL_MULT / 100)` 到達
- **TIME** (label=1): K bars 経過まで両 barrier 未到達
- 同 bar 内で両 hit 時は SL 優先 (保守的・Phase 1-b と同方針)

multiplier 候補 (まこさん 2026-05-21 確定):

| ラウンド | TP_MULT | SL_MULT | RR比 |
|---|---:|---:|---:|
| 初期 | 2.0 | 1.5 | 4:3 |
| 代替 A | 1.5 | 1.0 | 3:2 |
| 代替 B | 1.0 | 0.8 | 5:4 |

K=288 で TIME < 5% 発動なら代替 A → B の順で再試行 (Web Claude へ STOP 報告 + GO 待ち)。

**設計参考**: Lopez de Prado AFML §3 Triple Barrier 標準実装に準拠。ATR ベースで低ボラ期は狭い barrier・高ボラ期は広い barrier (レジーム適応)。

### §4.3 ラベル分布の確認 (Triple Barrier 生成直後・必須)

各 K で 3 クラス分布を `label_distribution.csv` に出力 → **まこさん確認ゲート** (Stage 1 終了)。

**STOP 条件**: いずれかの K で 1 クラスが 80% 超または 5% 未満 → barrier multiplier 不適切 → 代替 A / B で再試行 + Web Claude に STOP 報告。

### §4.4 LightGBM multiclass ハイパラ

```yaml
objective: multiclass
num_class: 3
metric: multi_logloss
boosting_type: gbdt
num_leaves: 31
max_depth: -1
min_data_in_leaf: 20
learning_rate: 0.05
feature_fraction: 0.9
bagging_fraction: 0.8
bagging_freq: 5
n_estimators: 1000
early_stopping_rounds: 50
random_state: 42
n_jobs: 1                 # bit-exact 再現性
verbose: -1
```

Phase 1-a と同一 (Optuna 探索は Phase 2)。

### §4.5 train/valid split (Phase 1-a と同一・purge_bars=288)

```
split_idx = int(n * 0.8)
valid_df = train.iloc[split_idx:]
train_df = train.iloc[:split_idx - 288]   # 末尾 288 bars purge で valid leak 防止
```

### §4.6 7 K 独立学習ループ

各 K について `triple_barrier_K{K}` ラベルで LGBMClassifier (multiclass・num_class=3) 学習・softmax 確率を test 2025 で予測 (3 列出力: P_SL / P_TIME / P_TP)。

### §4.7 leak 4 点チェック (L-179・Phase 1-a と同様 + multiclass 拡張)

1. **未来参照特徴量検知**: top20 列名に `_future`/`_lookahead`/`_K{K}` (学習対象) 0 件
2. **shift(1) ガード verify**: Phase 0 v3 Step 5 (commit 34777ef) 引用 + 着手時点まで特徴量計算スクリプト差分ゼロ verify
3. **重要度トップ偏り**: top1 が全 importance の 30% 以上 → WARN
4. **Triple Barrier ラベル間相関 verify**: 7 K のラベル間で |相関| > 0.99 のペア検出 (K=6 と K=12 完全一致なら barrier 設計不適切)

### §4.8 EV フィルタ + simulated PnL (K=12 主判定)

#### EV (期待値) 計算

```
EV[t] = P_TP[t] × TP_USD_est[t] − P_SL[t] × SL_USD_est[t] − fee_round_trip
```

- `TP_USD_est`: 過去 200 trade のうち TP hit した実利益の avg (shift(1) で leak ガード)
- `SL_USD_est`: 過去 200 trade のうち SL hit した実損失 abs の avg (同上)
- `fee_round_trip = 0.028%` (Maker 0.014% × 2)

#### Entry / Exit

| 項目 | 値 |
|---|---|
| Entry | EV[t] > 0 で LONG (K=12 主) |
| Exit | min(K=12 bars, TP barrier touch, SL barrier touch) いずれか早い方 |
| ポジション | 0.01 BTC × 最大 12 (合計 0.12 BTC) |
| Funding | 適用しない |

---

## §5 合格判定 (4 指標)

| # | 指標 | 基準 |
|---|---|---|
| 1 | multiclass logloss (valid) | **7 K 全てで < 0.95** (uninformed baseline log(3)=1.10 の 86%) |
| 2 | TP クラス Precision (P_TP > 0.5 サブセット) | **7 K 中 5+ で > 0.4** |
| 3 | EV フィルタ後 simulated PnL (K=12 主) | **12 ヶ月中 8+ ヶ月プラス + 年間 NET プラス** |
| 4 | leak 4 点 | **全 PASS** |

ALL ✅ → Phase 2 着手 GO / 1 件でも NG → §6 戻り先

---

## §6 不合格時の改善フロー

| 不合格 | 戻り先 |
|---|---|
| logloss ≥ 0.95 (複数 K) | barrier multiplier 代替 A → B で再試行 |
| Precision > 0.4 が 5 K 未満 | barrier multiplier 代替 A → B で再試行 |
| simulated PnL < 8 ヶ月プラス | EV 閾値 (0 → 0.1%) で再 simulation (1 回) |
| leak FAIL | **Phase 0 v3 Step 5 へ戻る** |
| ラベル分布偏り (1 クラス 80% 超 / 5% 未満) | barrier multiplier 代替 A → B + STOP 報告 |
| 全指標 FAIL | **Phase 1-a 立て直し協議** |
| ポジション上限超過 | **即時 STOP・Prime Directive 違反** |
| Sharpe 系不具合 | 本タスク扱わない (Phase 2 以降 smoothing 設計後) |

---

## §7 完了報告必須証跡

### §7.1 必須出力ファイル (12 種)

1. `labels_triple_barrier_{train,test_2025}.parquet` × 2
2. `models/triple_barrier_K{K}.txt` × 7
3. `predictions_multiclass_test_2025.parquet` (21 列)
4. `training_summary.csv` (7 行)
5. `feature_importance_top20_multiclass.csv` (140 行)
6. `ev_filter_simulated_pnl_K{K}.csv` × 7
7. `precision_recall_K{K}.csv` × 7
8. `leak_check_report.json`
9. `execution_log.txt`
10. 完了報告 md
11. 再現コマンド 1 行
12. `label_distribution.csv` (7 K × 3-class %)

### §7.2 完了報告 md 必須セクション

| § | 内容 |
|---|---|
| §0 | Prime Directive 9 項目宣言 |
| §1 | ポジション上限 verify (sum max 実測) |
| §2 | Triple Barrier ラベル分布 (7 K × 3-class %) + 採用 multiplier |
| §3 | 学習結果サマリ (7 K 別 logloss / iter) |
| §4 | leak 4 点結果 |
| §5 | feature_importance top20 × 7 K (140 行) review 用抜粋 |
| §6 | Precision/Recall 7 K 別 |
| §7 | EV フィルタ simulated PnL 12 ヶ月別 (K=12 主) |
| §8 | 合格判定 4 指標 + 戻り先テーブル該当行 |
| §9 | 再現コマンド + 所要時間 |

### §7.3 STOP 条件

- leak 4 点で 1 件以上 FAIL
- ラベル分布 1 クラス 80% 超 or 5% 未満 (代替 multiplier 全て失敗時)
- いずれかの K で学習失敗 (NaN/Inf)
- ポジション上限 0.12 BTC 超過検知

STOP 時は即時 Web Claude 報告。

---

## §8 Phase 1-c 完了後の Web Claude 判定軸

1. training_summary.csv (7 K 全 logloss < 0.95)
2. feature_importance_top20_multiclass.csv 140 行 review
3. leak_check_report.json 全 4 PASS
4. ラベル分布表 (偏りなし)
5. ev_filter_simulated_pnl_K12.csv (8+ ヶ月プラス)
6. predictions 確率分布健全性

判定:
- GO → Phase 2 (B-9 Optuna) 指示書ドラフト
- NO-GO → §6 戻り先 + まこさん協議

---

## §9 保管 & 終了条件

- 本指示書 commit
- 完了報告 commit
- **同 commit で phase_flow_v3_with_recovery.md §2.2 を ATR ベース動的閾値に修正** (本タスク実装で確定する multiplier 値を逆反映)
- Web Claude §8 判定 → Phase 2 or 協議

---

## §10 次工程 (本タスク範囲外・参考)

- Phase 2: B-9 Optuna + Sharpe smoothing 再 audit
- Phase 3: B-10 アルゴ比較 / B-11 cluster
- Phase 4-b: A-2 Exit / B-13 ratio
- Phase 5: ポジション設計完成
- Phase 6: 本 test 2026 Q1 (1 回限り)
