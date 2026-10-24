# 2026-05-20 Phase 0 v3 完了報告 訂正タスク

作成: Web Claude 2026-05-20
保存先: `.claude/instructions/2026-05-20_phase0_v3_completion_report_fix.md`
タスク種別: 機械的訂正 4 件 + 追加 verify 2 件 (中間枠・150-200 行)

---

## §0. 背景

Phase 0 v3 完了報告 (`2026-05-19_ml_implementation_phase0_1_completion_phase0.md`) を Web Claude が公式 source (`label_stats.csv` / `build_labels_pct.py` / `sample_rows_K*.csv`) と照合してレビューした結果、5 点の不整合を検出。Web Claude PM 判断でラベル数 14 採用が確定したので、§7.2 にも反映する。

本タスクの目的: 完了報告を公式 source と一致させ、Phase 1 着手指示書発行の前提を整える。

---

## §1. 着手前必読 (3 件)

1. `.claude/instructions/2026-05-19_ml_implementation_phase0_1_completion_phase0.md` (訂正対象本体)
2. `results/priority_rebuild/phase0_v3_stats/label_stats.csv` (公式 source・全 84 行 view)
3. `.claude/memory/lessons_active.md` L-196 (メンテ時間出典 verify 義務)

参考 (1 行確認):
- `WORKFLOW.md` L343 (is_maintenance 列 Phase 5 Replay 以降不使用)
- `scripts/priority_rebuild/build_labels_pct.py` L96-101 / L228-238 / L323-324 (期間定義・メンテ flag 実装・末尾 K=288 drop)

---

## §2. 訂正項目 (5 件・機械的反映 + 追加 verify 2 件)

### Step 1: §0 サマリ修正 (機械的訂正)

L22 現状: `**Phase 0 v3 全条件クリア。Phase 1 着手判定を Web Claude に持ち越す。**`

訂正後: `**Phase 0 v3 主要条件クリア。§3.3 に留意点 2 件 (異常値スメル ⚠️) あり・反映済。Phase 1 着手判定を Web Claude に持ち越す。**`

理由: §3.3 で ⚠️ マーク 2 件残置のまま「全条件クリア」は self_check B「不利情報の末尾配置」違反候補 (`web_claude_self_check.md` L150)。

---

### Step 2: §3.3 数値訂正 (機械的訂正・最重要)

L114 現状: `| max 値が非現実的でないか (例: > 100%) | ⚠️ train K288 LONG_MFE max = 35.8% (2024 上昇相場での 24h 最大上昇・現実的範囲内) / SHORT_MAE max = 40.7% (同) |`

訂正後 (label_stats.csv L8/L15/L22/L29 から直接引用・小数 2 桁丸め): 

```
| max 値が非現実的でないか (例: > 100%) | ⚠️ train K288 全 4 ラベル max 値:
LONG_MFE = 40.70% / LONG_MAE = 34.01% / SHORT_MFE = 34.01% / SHORT_MAE = 40.70%
(対称性で LONG_MFE = SHORT_MAE / LONG_MAE = SHORT_MFE 一致)
該当日付特定は §3.3.1 (本タスク新規追加) 参照 |
```

検証: label_stats.csv 該当行の値を grep で 1 行ずつ確認:
```bash
grep "train_2021_2024,LONG_MFE_pct_K288\|train_2021_2024,LONG_MAE_pct_K288\|train_2021_2024,SHORT_MFE_pct_K288\|train_2021_2024,SHORT_MAE_pct_K288" results/priority_rebuild/phase0_v3_stats/label_stats.csv
```
4 行が出ること。max 列が上記値と一致すること。

旧記述の「35.8%」は K48/K96/K144 の LONG_MFE max 値 (label_stats.csv L5/L6/L7 = 35.82877...) を K288 の値と混同したと推測。要因記録不要 (CC の理解と合っているか確認したい場合は完了報告に 1 行)。

---

### Step 3: §3.3.1 新規追加 — K288 max 40.70% 該当日付特定 (追加 verify)

§3.3 末尾に新規セクション §3.3.1 を追加。内容:

train_2021_2024.parquet を 1 回読み込み、以下を抽出して report に書く:

```python
import pandas as pd
df = pd.read_parquet("results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet")

# LONG_MFE_K288 max 行
idx_long_mfe = df["LONG_MFE_pct_K288"].idxmax()
row_long_mfe = df.loc[idx_long_mfe, ["close", "LONG_MFE_pct_K288"]]

# LONG_MAE_K288 max 行
idx_long_mae = df["LONG_MAE_pct_K288"].idxmax()
row_long_mae = df.loc[idx_long_mae, ["close", "LONG_MAE_pct_K288"]]

# 当該 timestamp の 24h 後の high/low 確認
for label, idx in [("LONG_MFE", idx_long_mfe), ("LONG_MAE", idx_long_mae)]:
    end_ts = idx + pd.Timedelta(hours=24)
    window = df.loc[idx:end_ts, ["close"]]  # ※ high/low は parquet に無いので close で代替
    print(label, idx, "→", end_ts)
    print(window.head(3))
    print(window.tail(3))
```

完了報告 §3.3.1 に書く内容 (フォーマット):

```
### §3.3.1 K288 max 該当日付特定 (本タスク 2026-05-20 追加)

| ラベル | max 値 | 該当 timestamp | close[t] | 24h 後 close | 24h 価格変動 |
|---|---:|---|---:|---:|---:|
| LONG_MFE_K288 | 40.70% | YYYY-MM-DD HH:MM | $XX,XXX | $YY,YYY | +Z.Z% |
| LONG_MAE_K288 | 34.01% | YYYY-MM-DD HH:MM | $XX,XXX | $YY,YYY | -Z.Z% |

判定 (CC 自己評価): 
- 当該日付が既知の BTC 大変動日 (例: 2020-03-12 / 2021-05-19 / 2022-11 FTX / 2024-03 / 2024-11 等) と一致するか web 確認・1 行記述
- 一致しない場合は「データ品質懸念・Phase 1 着手前に Web Claude へ報告」と明記
```

加えて、当該日付が train 期間 (2021-04-01 〜 2024-12-31) の **既知の BTC 大変動日**と一致するかを web 検索で確認 (1 行・「2021-04-XX (BTC 半減期前ラリー) と一致」等)。

合致しない場合 = データ品質懸念 → Phase 1 着手前に Web Claude へ報告。

---

### Step 4: §2 メンテ flag L-196 注記 (機械的訂正)

L56-58 現状: 
```
期待値 5.35% (火水木 05-07 UTC = 3 hours × 3 days / 7 days / 24 hours = 5.36%) と全期間でほぼ一致。**実装正常**。

メンテ flag は **行 drop ではなく `is_maintenance` 列フラグ** として保存。Phase 5 Replay 時に flag=True 行をエントリー除外する設計（学習時には除外しない・特徴量として活用可能）。
```

訂正後:
```
期待値 5.35% (火水木 05-07 UTC = 3 hours × 3 days / 7 days / 24 hours = 5.36%) と全期間でほぼ一致。**実装は仕様通り動作**。

⚠️ ただし「火水木 05-07 UTC」のメンテ時間自体が出典なき Claude 想定値だったことが 2026-05-20 に発覚 (L-196 / `exchange_spec.md` 2026-05-20 訂正)。Bitget は 24/7 取引で定期メンテなし (公式ガイド「中断のない年中無休の取引」確認済)。
→ `is_maintenance` 列は **Phase 5 Replay 以降では使用しない** (WORKFLOW.md L343 確定・架空仕様との一致は valid な検証ではない)。parquet 内に残置は再生成コスト 2h40m 回避のため。
個別アナウンスは Support > Maintenance を Bot 起動時に都度確認 (Phase 7-c 要件)。
```

---

### Step 5: §1 起点 23:55 verify (追加 verify)

L38 現状: `train 期間: 2021-04-01 23:55 〜 2024-12-31 23:55 = **1,370 日 × 288 bars + 起点 1 − 末尾 K=288 drop = 394,561** ✅ 数学的に正`

問題: `build_labels_pct.py` L96 で TRAIN_START = `pd.Timestamp("2021-04-01")` (= 00:00:00) と設定されている。コード上で起点が 23:55 にシフトする処理は dropna(subset=[LONG_MFE_K288]) のみで、K=288 は **末尾** drop。起点 +16h shift がコードから直接説明できない。

verify 手順:
```python
import pandas as pd
df = pd.read_parquet("results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet")
print("index.min():", df.index.min())
print("index.max():", df.index.max())
print("rows where 1d feature NaN:", df.filter(regex="__1d$").isna().any(axis=1).sum())

# 起点 287 行 (= 2021-04-01 00:00 〜 23:50) の状態確認
head_287 = df.iloc[:287] if df.index.min() < pd.Timestamp("2021-04-01 23:55") else None
if head_287 is None:
    # 既に 23:55 起点 → どこかで dropna されている
    print("CONFIRMED: parquet 起点 = 23:55 = build_labels_pct.py 以外の経路で 287 行が drop されている")
```

完了報告 §1 に 1 行追記:
```
※ 起点 23:55 の原因: [CC が verify で特定した実装上の理由を 1 行]
例: 「1d MTF feature の merge_asof backward attach (build_labels_pct.py L142-162) で 1d feature が NaN になる先頭 287 行が dropna で除外された」
or 「parquet に NaN 行を含めて書き出しており、min(index) は最初に全列値を持つ行 (= 23:55)」
```

実装行番号を引用すること (`build_labels_pct.py:LXX-LYY`)。

---

### Step 6: §7.2 ラベル数確定 (機械的反映)

L196-203 現状:
```
| 案 | ラベル数 | 学習モデル数 | 根拠 |
|---|---:|---:|---|
| A. 元定義通り 28 ラベル | 28 | 28 | 指示書 §3-2 通り (LONG/SHORT × MFE/MAE × 7K) |
| B. 対称性活用 14 ラベル | 14 | 14 | §3.2 の対称性発見・学習時間半減 |

CC は両案とも実装可能。**Phase 1 指示書発注前に Web Claude 決定を待つ**。
```

訂正後:
```
| 案 | ラベル数 | 学習モデル数 | 状態 |
|---|---:|---:|---|
| A. 元定義通り 28 ラベル | 28 | 28 | 却下 (冗長) |
| **B. 対称性活用 14 ラベル** | **14** | **14** | **採用 (Web Claude PM 2026-05-20 確定)** |

**確定根拠**: §3.2 の対称性 (`LONG_MFE_pct_K{K} == SHORT_MAE_pct_K{K}` / `LONG_MAE_pct_K{K} == SHORT_MFE_pct_K{K}`) が公式 source `label_stats.csv` 全 84 行 (3 期間 × 全 7 K × 全統計値 mean/std/min/max/p50/p99) で完全一致確認済。数学的恒等式 (max_high − close = SHORT エントリーの最大逆行) の実装が正確に保存されていることを物理 view で verify。Phase 1 は 14 LightGBM モデルで実装。
```

---

## §3. ガード

- **G1**: 数値は `label_stats.csv` から直接引用 (grep で公式 source の行を引用すること・手計算禁止・L-184「公式判定 source = phaseX_summary.json 系のみ」遵守)
- **G2**: K288 max 該当日付は実 parquet クエリで抽出 (`df.loc[df['LONG_MFE_pct_K288'].idxmax()]`・推測禁止)

---

## §4. 完了報告必須証跡 (4 点)

1. **訂正前後の diff** (該当 5 セクション・git diff フォーマットでチャットに出力)
2. **公式 source 一致 grep 結果** (Step 2 の grep 4 行の出力)
3. **K288 max 該当日付 + 当時 BTC 価格変動の妥当性評価** (Step 3 の table + web 確認 1 行)
4. **起点 23:55 の実装上理由** (Step 5 の python 出力 + build_labels_pct.py 行番号引用)

異常値スメル該当なし (本タスクは PnL/勝率なしの訂正タスク・関所 A 適用外)。

---

## §5. 保存・commit

```bash
# 1. 本指示書を保存
git add .claude/instructions/2026-05-20_phase0_v3_completion_report_fix.md

# 2. 訂正後の Phase 0 完了報告を保存
git add .claude/instructions/2026-05-19_ml_implementation_phase0_1_completion_phase0.md

# 3. 完了報告 (本タスクの完了報告) を新規作成・保存
git add .claude/instructions/2026-05-20_phase0_v3_completion_report_fix_completion.md

# 4. commit
git commit -m "fix: Phase 0 v3 完了報告 5 点訂正 + ラベル数 14 確定 + K288 max 日付特定"
```

---

## §6. 後続タスク (Phase 1 指示書発行・本タスク完了後)

CC は本タスク完了後、Phase 1 指示書を待つ (Web Claude が次セッションで発行)。Phase 1 確定パラメータ:
- ラベル数 14 / feature 数 1,414 (1,462 − 48 blacklist)
- learning_rate=0.02 / n_estimators=5000 / min_data_in_leaf=100 / feature_fraction=0.7 / bagging_fraction=0.8 / bagging_freq=5 / reg_lambda=0.1 / random_state=42 (Phase 1 旧版踏襲・WORKFLOW.md L546-560)

以上。
