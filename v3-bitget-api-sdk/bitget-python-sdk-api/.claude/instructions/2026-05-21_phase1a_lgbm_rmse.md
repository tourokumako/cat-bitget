# Phase 1-a: 14 ラベル LightGBM RMSE 学習 (full 枠)

作成日: 2026-05-21
発注者: Web Claude (PM) → CC
種別: 大規模新規実装 (学習スクリプト新規 + 学習実行 + leak 4 点チェック + 必須報告)
規模: full 枠 300-400 行 (L-198 / memory ルール 24 準拠)
保存先: `.claude/instructions/2026-05-21_phase1a_lgbm_rmse.md`

---

## §0 背景・スコープ

### §0.1 背景

Phase 0 v3 完了レビュー 5 観点 ALL ✅ (2026-05-21・commit 4df8924) + spec sweep (commit 22e75a9) 完了。次工程として Phase 1 (14 ラベル LightGBM 学習) に着手する。

学習内容 v3 § B-15「Phase 1 から RMSE + 直接 PnL + Sharpe 並列実装」を、まこさん承認 (2026-05-21) で **段階分割** に変更:

- **Phase 1-a (本指示書)**: RMSE 単独・14 ラベル独立・デフォルトハイパラ → 数時間
- Phase 1-b (別指示書・Phase 1-a 完了後): 簡易 PnL チェック (naive 閾値売買で月次 NET 兆し判定)
- Phase 1-c (別指示書・Phase 1-b 通過 + audit#18 通過後): 直接 PnL / Sharpe custom objective 追加
- Phase 2 (別指示書): B-9 Optuna ハイパラ探索

**Phase 1-a の目的**: 標準実装 (LightGBM regression + RMSE) でバグリスク最小化しつつ、14 ラベル予測値の品質・leak 不在を早期確認する。

### §0.2 Phase 1-a スコープ (この指示書の範囲)

| 項目 | 値 |
|---|---|
| 学習対象 | **14 ラベル独立** (LONG_MFE_pct × K=7 + LONG_MAE_pct × K=7) |
| 目的関数 | **RMSE のみ** (LightGBM `regression` 標準・custom objective なし) |
| ハイパラ | **デフォルト** (Phase 2 で Optuna 探索) |
| 学習データ | `labels_mfe_mae_pct_train_2021_2024.parquet` (394,561 行) |
| 仮 test | `labels_mfe_mae_pct_test_2025.parquet` (105,120 行) で予測値出力 |
| 本 test | **触らない** (Phase 6 で 1 回限り) |

### §0.3 スコープ外 (本指示書では実施しない)

- 直接 PnL / Sharpe custom objective (Phase 1-c)
- 簡易 PnL チェック・Replay 試行 (Phase 1-b)
- Optuna ハイパラ探索 (Phase 2)
- Exit 仕立て (Phase 4-b)
- SHORT 側モデル (対称性活用で LONG 予測値を Phase 5 Replay で流用・本指示書では予測値出力もしない)

---

## §1 着手前必読 (6 件・順番厳守)

1. `.claude/rules/false_positive_incident_policy.md` §0-1 Prime Directive / §0-2 ポジション上限 / Type C (leak) / Type H (price-dependent)
2. `.claude/memory/learning_design_v3.md` §A-4 / §B-12 / §B-14 / §B-15 / v2→v3 修正履歴 #12
3. `cc_ml_design_spec.md` (commit 22e75a9 反映後) §1.1 / §1.3 / §1.5 / §1.6 / §5 Phase 1 / §7 / §8
4. `.claude/instructions/handoff_to_web_claude_v16_session_20260520.md` §3.3
5. `.claude/instructions/2026-05-19_ml_implementation_phase0_1_completion_phase0.md` §7.2 (14 ラベル B 案採用根拠) / §3.2 (対称性 bit-exact)
6. `.claude/rules/lessons_active.md` L-179 (look-ahead leak 4 点) / L-180 (引用前 verify) / L-189 (Phase 4-b 必須) / L-196 (外部仕様出典)

着手前 verify 必須:
- L-179 4 点チェック内容を 1 行ずつ書き出して理解確認 (完了報告に含める)
- §1 で読んだ各ファイルの該当行番号を完了報告に列挙

---

## §2 Prime Directive 事前宣言 (実装前ゲート・cc_ml_design_spec.md §8)

実装着手**前に**、以下 8 項目の入力変数について「本番運用の推論時点 t で因果的に取得可能か YES/NO」を 1 行ずつ宣言する。宣言なしの実装着手禁止。完了報告に含める。

| # | 変数カテゴリ | 期待宣言 |
|---|---|---|
| 1 | 特徴量 (1,414 個・blacklist 後) | YES (時点 t 以前の OHLCV から計算・shift(1) ガード適用) |
| 2 | LONG_MFE_pct_K{K} ラベル (学習対象) | YES (target side・t+1 から t+K の high で計算・学習データのみで使用・推論時は予測値) |
| 3 | LONG_MAE_pct_K{K} ラベル (学習対象) | 同上 |
| 4 | SHORT_MFE_pct_K{K} (学習不要・drop 必須) | drop_cols で除外 (対称性で LONG_MAE と等価・含めると leak 同等の冗長情報) |
| 5 | SHORT_MAE_pct_K{K} (学習不要・drop 必須) | 同上 |
| 6 | close 列 | YES (時点 t の確定値・ただし学習対象外なら drop) |
| 7 | is_maintenance 列 | drop (Phase 0 v3 で保存・Phase 5 まで参照しない・本指示書でも drop) |
| 8 | timestamp (index) | YES (時点 t そのもの・特徴量化しないが split キーに使用) |

drop_cols リストを明示してから fit() を呼ぶ実装にすること。

---

## §3 ポジション上限 事前 verify (cc_ml_design_spec.md §8)

Phase 1-a では **学習のみ・Replay なし** のため active position が発生しない。よってポジション上限 0.12 BTC の verify 対象なし。Phase 1-b (簡易 PnL Replay) で初発生・別指示書で別 verify。

本指示書では「Phase 1-a スコープではポジションサイズ決定ロジックを含まない・sum(active_position_btc) は常に 0」を完了報告に 1 行明記すること。

---

## §4 実装仕様

### §4.1 ファイル構成

```
scripts/priority_rebuild/
  run_lgbm_phase1a_rmse.py        # 新規・本タスクのメイン
  utils/leak_check.py             # 新規・L-179 4 点チェック関数 (再利用)

configs/
  phase1a_rmse.yaml               # 新規・デフォルトハイパラ + drop_cols リスト

results/priority_rebuild/ml_phase1a_rmse/
  models/
    LONG_MFE_pct_K{K}.txt × 7     # LightGBM Booster save_model 形式
    LONG_MAE_pct_K{K}.txt × 7
  feature_importance_top20.csv    # 14 ラベル × top20 = 280 行
  training_summary.csv            # 14 行 (label / best_iter / train_rmse / valid_rmse / label_std / rmse_ratio)
  predictions_test_2025.parquet   # 105,120 行 × 14 列 (LONG_MFE/MAE × K=7 予測値)
  prediction_value_distribution.png × 14
  random_baseline_comparison.csv  # 14 行 (label / ML_RMSE / random_RMSE / lift_pct)
  execution_log.txt               # 開始/終了時刻・終了コード・各ラベル所要時間
  leak_check_report.json          # L-179 4 点チェック結果
```

### §4.2 LightGBM ハイパラ (デフォルト・configs/phase1a_rmse.yaml)

```yaml
objective: regression          # RMSE (LightGBM 標準・bug リスク最小)
metric: rmse
boosting_type: gbdt
num_leaves: 31                 # デフォルト
max_depth: -1                  # デフォルト (無制限)
min_data_in_leaf: 20           # デフォルト
learning_rate: 0.05            # デフォルト (sklearn API より速め)
feature_fraction: 0.9
bagging_fraction: 0.8
bagging_freq: 5
n_estimators: 1000
early_stopping_rounds: 50
random_state: 42               # 再現性確保
verbose: -1
```

Phase 2 (Optuna) でこれら全てを探索対象にする。Phase 1-a は固定。

### §4.3 入力データ load (look-ahead leak 防止)

```python
import pandas as pd

PARQ_TRAIN = 'results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet'
PARQ_TEST  = 'results/priority_rebuild/labels_mfe_mae_pct_test_2025.parquet'

train = pd.read_parquet(PARQ_TRAIN)
test  = pd.read_parquet(PARQ_TEST)

# index = timestamp (datetime64・Phase 0 v3 §1 確定)
assert train.index.name == 'timestamp'
assert test.index.name == 'timestamp'

# 期間境界 verify (重要・leak 防止)
assert train.index.max() < test.index.min(), \
    f"train_max={train.index.max()} >= test_min={test.index.min()} → leak リスク"
```

### §4.4 drop_cols (学習対象外列・leak 防止)

```python
# 学習対象 14 ラベル
LABEL_COLS_LEARN = (
    [f'LONG_MFE_pct_K{K}' for K in [6,12,24,48,96,144,288]] +
    [f'LONG_MAE_pct_K{K}' for K in [6,12,24,48,96,144,288]]
)

# drop 必須列 (特徴量化禁止)
DROP_COLS_ALWAYS = (
    # SHORT 側 14 ラベル (対称性で LONG と等価・冗長 leak)
    [f'SHORT_MFE_pct_K{K}' for K in [6,12,24,48,96,144,288]] +
    [f'SHORT_MAE_pct_K{K}' for K in [6,12,24,48,96,144,288]] +
    # その他
    ['close', 'is_maintenance']
)

# blacklist 48 個 (Phase 0 v3 完了報告 §7.1 で確定済)
BLACKLIST_PATH = 'configs/feature_blacklist_v3.txt'
with open(BLACKLIST_PATH) as f:
    DROP_COLS_BLACKLIST = [line.strip() for line in f if line.strip()]
assert len(DROP_COLS_BLACKLIST) == 48, f"blacklist 個数異常: {len(DROP_COLS_BLACKLIST)}"

DROP_COLS = list(set(DROP_COLS_ALWAYS + DROP_COLS_BLACKLIST))

# 学習特徴量 = 全列 - LABEL_COLS_LEARN - DROP_COLS
FEATURE_COLS = [c for c in train.columns if c not in LABEL_COLS_LEARN + DROP_COLS]
assert len(FEATURE_COLS) == 1414, f"feature 個数異常: {len(FEATURE_COLS)} ≠ 1414"
```

### §4.5 train / valid split (時系列・look-ahead leak 防止)

```python
# train_2021_2024 を時系列で 80/20 split
# 末尾 20% を valid (= 2024 年後半・実装後 test 2025 への汎化を見る代理)
n = len(train)
split_idx = int(n * 0.8)
train_df = train.iloc[:split_idx]
valid_df = train.iloc[split_idx:]

# 境界 leak 防止: valid 開始時点で train の K=288 (24h) ラベルが未来参照していないか確認
# train.iloc[split_idx-1] の LONG_MFE_pct_K288 は ts + 288 bars (24h) 先まで参照済
# → valid_df の先頭 288 bars と train_df 末尾の時間軸が重複 → train_df 末尾 288 bars drop
PURGE_BARS = 288  # 最大 K
train_df = train_df.iloc[:-PURGE_BARS]
print(f"train rows after purge: {len(train_df)} (purged {PURGE_BARS} bars)")
print(f"valid rows: {len(valid_df)}")
```

このパージは **B-14 Walk-forward / Purged K-fold (Phase 1 では簡易版)** の最小実装。Phase 2 以降でちゃんとした Purged CPCV に拡張する。

### §4.6 14 ラベル独立学習ループ

```python
import lightgbm as lgb
from pathlib import Path
import json, time

MODELS_DIR = Path('results/priority_rebuild/ml_phase1a_rmse/models')
MODELS_DIR.mkdir(parents=True, exist_ok=True)

summary_rows = []
pred_test = pd.DataFrame(index=test.index)
fi_rows = []

for label in LABEL_COLS_LEARN:
    t0 = time.time()

    # NaN drop (K=288 末尾 288 bars 等)
    mask_tr = train_df[label].notna()
    mask_va = valid_df[label].notna()
    X_tr = train_df.loc[mask_tr, FEATURE_COLS]
    y_tr = train_df.loc[mask_tr, label]
    X_va = valid_df.loc[mask_va, FEATURE_COLS]
    y_va = valid_df.loc[mask_va, label]
    X_te = test[FEATURE_COLS]

    model = lgb.LGBMRegressor(**hparams_from_yaml)
    model.fit(
        X_tr, y_tr,
        eval_set=[(X_tr, y_tr), (X_va, y_va)],
        eval_names=['train', 'valid'],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)],
    )

    model.booster_.save_model(str(MODELS_DIR / f'{label}.txt'))

    # 予測 (test 2025)
    pred_test[label] = model.predict(X_te)

    # サマリ
    train_rmse = model.best_score_['train']['rmse']
    valid_rmse = model.best_score_['valid']['rmse']
    label_std = float(y_va.std())
    rmse_ratio = valid_rmse / label_std if label_std > 0 else float('inf')

    summary_rows.append({
        'label': label, 'best_iter': model.best_iteration_,
        'train_rmse': train_rmse, 'valid_rmse': valid_rmse,
        'label_std': label_std, 'rmse_ratio': rmse_ratio,
        'elapsed_sec': time.time() - t0,
    })

    # feature importance top20
    fi = pd.DataFrame({
        'feature': model.booster_.feature_name(),
        'importance_gain': model.booster_.feature_importance(importance_type='gain'),
    }).sort_values('importance_gain', ascending=False).head(20)
    fi['label'] = label
    fi['rank'] = range(1, 21)
    fi_rows.append(fi)

pd.DataFrame(summary_rows).to_csv('.../training_summary.csv', index=False)
pred_test.to_parquet('.../predictions_test_2025.parquet')
pd.concat(fi_rows).to_csv('.../feature_importance_top20.csv', index=False)
```

### §4.7 leak 4 点チェック (L-179 必須)

`utils/leak_check.py` に以下 4 関数を実装し、各ラベル学習完了直後に呼ぶ:

1. **未来参照特徴量検知**: feature_importance top20 に「`_future`」「`_lookahead`」「`_K{K}`」(K∈学習対象 K) を含む列名がないか
2. **shift(1) ガード verify**: 全特徴量列について「`shift(1)` または `lag(N)` (N≥1) または `rolling().shift(1)`」が build_labels_pct.py / 特徴量計算スクリプトで適用済か grep
3. **重要度トップ偏り検知**: top1 が全体 importance の 30% 以上ある場合 ⚠️ (単一指標依存 = leak シグナル)
4. **ラベル間相関 verify**: 学習対象 14 ラベル間の相関を計算し、|相関| > 0.99 のペアが存在しないか (対称性は除外しているが念のため)

結果を `leak_check_report.json` に書き出し:
```json
{
  "check_1_future_ref": {"status": "PASS|FAIL", "violations": [...]},
  "check_2_shift1_guard": {"status": "PASS|FAIL", "violations": [...]},
  "check_3_top1_dominance": {"status": "PASS|WARN", "max_pct": ...},
  "check_4_label_correlation": {"status": "PASS|FAIL", "violations": [...]}
}
```

1 件でも FAIL なら **学習結果無効・Web Claude に STOP 報告**。WARN は継続可だが完了報告で明示。

### §4.8 ランダム比較 (cc_ml_design_spec.md §7.5)

各ラベルについて、`valid` の y_va を numpy.random.shuffle した値を予測値として RMSE を計算 (= ランダム予測の RMSE)。
ML_RMSE が random_RMSE より 10% 以上低ければ「ML が学習している」エビデンス。`random_baseline_comparison.csv` に 14 行で記録。

### §4.9 予測値分布ヒストグラム (cc_ml_design_spec.md §7.6)

各ラベルについて test 2025 予測値のヒストグラムを png 出力。
- 全部同じ値 (分散 < 1e-6) → ⚠️ 学習失敗シグナル
- 双峰分布 → 学習が異常 / leak の可能性

---

## §5 完了報告必須証跡

### §5.1 必須出力ファイル (12 種・1 つでも欠落で受理しない)

1. `models/LONG_MFE_pct_K{K}.txt` × 7
2. `models/LONG_MAE_pct_K{K}.txt` × 7
3. `feature_importance_top20.csv` (280 行)
4. `training_summary.csv` (14 行)
5. `predictions_test_2025.parquet` (105,120 行 × 14 列)
6. `prediction_value_distribution.png` × 14
7. `random_baseline_comparison.csv` (14 行)
8. `execution_log.txt`
9. `leak_check_report.json`
10. ダッシュボード新規タブ (cc_ml_design_spec.md §7.3 準拠・特徴量重要度 / 散布図 / 月次損益 (簡易) / Entry 発火分布)
11. 再現コマンド 1 行 (cc_ml_design_spec.md §7.4)
12. 完了報告 md (`.claude/instructions/2026-05-21_phase1a_lgbm_rmse_completion.md`)

### §5.2 完了報告 md 必須セクション

| § | 内容 |
|---|---|
| §0 | Prime Directive 事前宣言 8 項目 (本指示書 §2 に従う) |
| §1 | ポジション上限 verify 1 行宣言 (本指示書 §3) |
| §2 | 学習結果サマリ (14 ラベル別 train/valid RMSE / rmse_ratio・rmse_ratio < 1.5 が 14 ラベル中何個 / 14 か明示) |
| §3 | leak 4 点チェック結果 (全 4 件 PASS であること) |
| §4 | feature_importance top20 × 14 ラベル の Web Claude review 用抜粋 (人手で見て leak シグナル検知できる形式) |
| §5 | ランダム比較結果 (14 ラベル別 lift_pct) |
| §6 | 予測値分布健全性 (全 14 ラベルで分散 > 1e-6 + 単峰確認) |
| §7 | ダッシュボード URL + 必須要件 §7.3 反映済 |
| §8 | 再現コマンド + 実行ログパス + 所要時間 |

### §5.3 STOP 条件 (1 つでも該当で CC は実装中断・Web Claude へ報告)

- leak 4 点チェックで 1 件以上 FAIL
- いずれかのラベルで学習失敗 (NaN / Inf / 異常終了)
- いずれかのラベルで予測値分散 < 1e-6
- rmse_ratio < 1.5 のラベルが 14 中 9 未満 (= 14/14 中 5 ラベル以上で学習が崩壊)

---

## §6 Phase 1-a 完了後の Web Claude 判定軸

CC 完了報告受領後、Web Claude が独立 verify する内容:

1. **training_summary.csv 物理 view**: 14 ラベル全件・rmse_ratio < 1.5 が何個か
2. **feature_importance_top20.csv 全件 view**: 280 行を Web Claude が human review (USD 絶対値系・未来参照系・単一指標偏り)
3. **leak_check_report.json 物理 view**: 全 4 件 PASS の確認
4. **predictions_test_2025.parquet サンプル view**: 予測値分布の健全性
5. **random_baseline_comparison.csv**: 14 ラベル中 lift > 10% が何個か (Phase 1-b 進行判定の主指標)

判定結果:
- **GO**: rmse_ratio < 1.5 が 12+/14 ラベル + leak 全 PASS + lift > 10% が 8+/14 ラベル → Phase 1-b 指示書 (light 枠) 発注
- **NO-GO (要協議)**: 上記 1 つでも欠ければまこさん協議 (cc_ml_design_spec.md §1.6 不合格時の対応)

---

## §7 保管 & 終了条件

- 本指示書: `.claude/instructions/2026-05-21_phase1a_lgbm_rmse.md` 保存 + git commit (memory ルール 19)
- 完了報告: `.claude/instructions/2026-05-21_phase1a_lgbm_rmse_completion.md` 保存 + git commit (memory ルール 21 では handoff だが指示書完了報告も同等)
- 完了 → Web Claude §6 判定 → Phase 1-b 指示書発注 or まこさん協議

---

## §8 次工程 (本指示書の範囲外・参考)

- **Phase 1-b**: 簡易 PnL チェック (light 枠) — Phase 1-a 予測値で naive 閾値売買シミュレーション → 月次 NET 兆し判定
- **Phase 1-c**: 直接 PnL / Sharpe custom objective 追加 (full 枠 + audit#18 経由) — Phase 1-b 通過後
- **Phase 2**: B-9 Optuna ハイパラ探索 (full 枠) — Phase 1-c 完了後
- **Phase 3**: B-10 / B-11 cluster
- **Phase 4-b**: A-2 Exit / B-13 ratio 閾値
- **Phase 5**: A-6 / A-7 / B-8 / D-ζ / D-α ポジション設計
- **Phase 6**: 本テスト (2026 Q1) 1 回限り
