# 2026-05-20 Phase 0 v3 完了報告 訂正タスク — 完了報告

完了日: 2026-05-20
対応指示書: [.claude/instructions/2026-05-20_phase0_v3_completion_report_fix.md](2026-05-20_phase0_v3_completion_report_fix.md)
訂正対象: [.claude/instructions/2026-05-19_ml_implementation_phase0_1_completion_phase0.md](2026-05-19_ml_implementation_phase0_1_completion_phase0.md)

---

## §0. 完了サマリー

| 項目 | 結果 |
|---|---|
| Step 1: §0 サマリ修正 | ✅ 完了 (1 行訂正) |
| Step 2: §3.3 K288 max 数値訂正 | ✅ 完了 (公式 source label_stats.csv 直接引用) |
| Step 3: §3.3.1 新規追加 (K288 max 該当日付特定) | ✅ 完了 (parquet 実クエリで 2021-05-19 BTC 大暴落と完全一致確認) |
| Step 4: §2 メンテ flag L-196 注記追加 | ✅ 完了 |
| Step 5: §1 起点 23:55 verify | ✅ 完了 (build_labels_pct.py L208-225 + L323-324 で原因特定) |
| Step 6: §7.2 ラベル数 14 確定反映 | ✅ 完了 (Web Claude PM 採用確定を表に反映) |
| ガード G1 (公式 source grep 直接引用) | ✅ 通過 |
| ガード G2 (parquet 実クエリで日付抽出) | ✅ 通過 |

5 セクション機械的訂正 + 2 件追加 verify いずれも完了。Phase 1 着手指示書発行の前提が整った。

---

## §1. 完了報告必須証跡 4 点

### 証跡 1: 訂正前後の diff (5 セクション)

訂正対象ファイルは untracked 状態 (前セッションで新規作成) のため `git diff` 出力なし。指示書 §2 で記述された旧記述 (before) と訂正後の new_string (after) を以下に列挙する。

#### Step 1: §0 サマリ (L22)

**Before**:
```
**Phase 0 v3 全条件クリア。Phase 1 着手判定を Web Claude に持ち越す。**
```

**After**:
```
**Phase 0 v3 主要条件クリア。§3.3 に留意点 2 件 (異常値スメル ⚠️) あり・反映済。Phase 1 着手判定を Web Claude に持ち越す。**
```

#### Step 2: §3.3 max 値 (L114)

**Before**:
```
| max 値が非現実的でないか (例: > 100%) | ⚠️ train K288 LONG_MFE max = 35.8% (2024 上昇相場での 24h 最大上昇・現実的範囲内) / SHORT_MAE max = 40.7% (同) |
```

**After**:
```
| max 値が非現実的でないか (例: > 100%) | ⚠️ train K288 全 4 ラベル max 値: LONG_MFE = 40.70% / LONG_MAE = 34.01% / SHORT_MFE = 34.01% / SHORT_MAE = 40.70% (対称性で LONG_MFE = SHORT_MAE / LONG_MAE = SHORT_MFE 一致)。該当日付特定は §3.3.1 (本タスク 2026-05-20 追加) 参照 |
```

#### Step 3: §3.3.1 新規追加 (§3.3 末尾)

**Before**: (該当セクション存在せず)

**After**: 新規セクション §3.3.1 を追加。内容:
```
### §3.3.1 K288 max 該当日付特定 (本タスク 2026-05-20 追加)

train_2021_2024.parquet を `df["LONG_MFE_pct_K288"].idxmax()` / `df["LONG_MAE_pct_K288"].idxmax()` で抽出:

| ラベル | max 値 | 該当 timestamp (UTC) | close[t] | t+24h close | 24h close 変動 | 24h close 最高/最低 |
|---|---:|---|---:|---:|---:|---|
| LONG_MFE_pct_K288 | 40.70% | 2021-05-19 13:05 | $29,821 | $41,848 | +40.33% | 最高 $41,884 (+40.45%) |
| LONG_MAE_pct_K288 | 34.01% | 2021-05-18 13:40 | $43,925 | $37,119 | -15.49% | 最低 $29,821 (-32.11%) |

**判定 (CC 自己評価)**:
- 両 max とも **2021-05-19 BTC 大暴落 (Elon Musk Tesla 中断 + 中国マイニング禁止 FUD・$43k → $29k)** の前後に集中
- 既知の歴史的大変動 (2021-05-19 ≈ "Bitcoin Black Wednesday") と完全一致 → **データ品質懸念なし・ラベル計算正常**
```
(原文は完了報告に保存済)

#### Step 4: §2 メンテ flag (L56-58)

**Before**:
```
期待値 5.35% (火水木 05-07 UTC = 3 hours × 3 days / 7 days / 24 hours = 5.36%) と全期間でほぼ一致。**実装正常**。

メンテ flag は **行 drop ではなく `is_maintenance` 列フラグ** として保存。Phase 5 Replay 時に flag=True 行をエントリー除外する設計（学習時には除外しない・特徴量として活用可能）。
```

**After**:
```
期待値 5.35% (火水木 05-07 UTC = 3 hours × 3 days / 7 days / 24 hours = 5.36%) と全期間でほぼ一致。**実装は仕様通り動作**。

⚠️ ただし「火水木 05-07 UTC」のメンテ時間自体が出典なき Claude 想定値だったことが 2026-05-20 に発覚 (L-196 / `exchange_spec.md` 2026-05-20 訂正)。Bitget は 24/7 取引で定期メンテなし (公式ガイド「中断のない年中無休の取引」確認済)。
→ `is_maintenance` 列は **Phase 5 Replay 以降では使用しない** (WORKFLOW.md L343 確定・架空仕様との一致は valid な検証ではない)。parquet 内に残置は再生成コスト 2h40m 回避のため。
個別アナウンスは Support > Maintenance を Bot 起動時に都度確認 (Phase 7-c 要件)。
```

#### Step 5: §1 起点 23:55 verify (L38 後)

**Before**: (該当注記なし)

**After**: §1 の bullet list 末尾に注記を追加:
```
※ **起点 23:55 の実装上理由 (本タスク 2026-05-20 追加 verify)**: TRAIN_START = `pd.Timestamp("2021-04-01")` (= 00:00:00) で開始するが、parquet 実測 `index.min() = 2021-04-01 23:55:00`。原因は `compute_mfe_mae_labels_pct` ([build_labels_pct.py:208-225](../../scripts/priority_rebuild/build_labels_pct.py#L208-L225)) の `fut_max_high = h.shift(-K).rolling(K).max()` で K=288 (最大 K) の rolling(288) が 288 個の valid 値を要求 → shift(-288) 後の系列で先頭 287 行が NaN 化 → [L323-324](../../scripts/priority_rebuild/build_labels_pct.py#L323-L324) `full.dropna(subset=[LONG_MFE_pct_K288])` で先頭 287 行 (= 287 × 5min = 23h55min) が削除され、最初に valid な行が `2021-04-01 23:55:00` となる。実測 verify: `parquet.index.min() = 2021-04-01 23:55:00`, `parquet.index.max() = 2024-12-31 23:55:00`, total = 394,561 行。
```

#### Step 6: §7.2 ラベル数 (L196-203)

**Before**:
```
| 案 | ラベル数 | 学習モデル数 | 根拠 |
|---|---:|---:|---|
| A. 元定義通り 28 ラベル | 28 | 28 | 指示書 §3-2 通り (LONG/SHORT × MFE/MAE × 7K) |
| B. 対称性活用 14 ラベル | 14 | 14 | §3.2 の対称性発見・学習時間半減 |

CC は両案とも実装可能。**Phase 1 指示書発注前に Web Claude 決定を待つ**。
```

**After**:
```
| 案 | ラベル数 | 学習モデル数 | 状態 |
|---|---:|---:|---|
| A. 元定義通り 28 ラベル | 28 | 28 | 却下 (冗長) |
| **B. 対称性活用 14 ラベル** | **14** | **14** | **採用 (Web Claude PM 2026-05-20 確定)** |

**確定根拠**: §3.2 の対称性 (`LONG_MFE_pct_K{K} == SHORT_MAE_pct_K{K}` / `LONG_MAE_pct_K{K} == SHORT_MFE_pct_K{K}`) が公式 source label_stats.csv 全 84 行 (3 期間 × 全 7 K × 全統計値) で完全一致確認済。Phase 1 は 14 LightGBM モデルで実装。
```

---

### 証跡 2: 公式 source 一致 grep 結果 (G1 通過)

```bash
$ grep "train_2021_2024,LONG_MFE_pct_K288\|train_2021_2024,LONG_MAE_pct_K288\|train_2021_2024,SHORT_MFE_pct_K288\|train_2021_2024,SHORT_MAE_pct_K288" \
    results/priority_rebuild/phase0_v3_stats/label_stats.csv
```

出力 (4 行・label_stats.csv L8/L15/L22/L29 に対応):
```
train_2021_2024,LONG_MFE_pct_K288,394561,2.2455069148145004,2.299115338389765,-0.23704792931661745,40.704537071191446,1.5421337139915288,11.024088316466722
train_2021_2024,LONG_MAE_pct_K288,394561,2.3024854298889452,2.6322259067433382,-1.0897809831892666,34.01024473534434,1.5285748287625949,12.799981373027368
train_2021_2024,SHORT_MFE_pct_K288,394561,2.3024854298889452,2.6322259067433382,-1.0897809831892666,34.01024473534434,1.5285748287625949,12.799981373027368
train_2021_2024,SHORT_MAE_pct_K288,394561,2.2455069148145004,2.299115338389765,-0.23704792931661745,40.704537071191446,1.5421337139915288,11.024088316466722
```

CSV 列順 = `period,label,count,mean,std,min,max,p50,p99`。**max 列 (第 7 列)**:
- LONG_MFE_pct_K288: `40.704537071191446` → 訂正後表記 `40.70%` ✅
- LONG_MAE_pct_K288: `34.01024473534434` → 訂正後表記 `34.01%` ✅
- SHORT_MFE_pct_K288: `34.01024473534434` → 訂正後表記 `34.01%` ✅
- SHORT_MAE_pct_K288: `40.704537071191446` → 訂正後表記 `40.70%` ✅

対称性 `LONG_MFE == SHORT_MAE` / `LONG_MAE == SHORT_MFE` は全 6 統計値 (count/mean/std/min/max/p50/p99) で完全一致 (浮動小数末尾まで同一) → §3.2 既述の対称性が K288 でも維持されていることを直接 verify。

旧記述「35.8%」の出所は推測通り label_stats.csv L5/L6/L7 (K48/K96/K144 LONG_MFE max = `35.82877837765333`) を K288 と混同したもの。grep で 4 行を直接引用したので再混同リスクなし。

---

### 証跡 3: K288 max 該当日付 + 当時 BTC 価格変動の妥当性評価 (G2 通過)

実 parquet クエリ (`results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet`・1.13 GB):

```python
import pandas as pd
df = pd.read_parquet("results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet")

# LONG_MFE_K288 max
idx_long_mfe = df["LONG_MFE_pct_K288"].idxmax()
# → 2021-05-19 13:05:00, max=40.7045%, close[t]=$29,821

# LONG_MAE_K288 max  
idx_long_mae = df["LONG_MAE_pct_K288"].idxmax()
# → 2021-05-18 13:40:00, max=34.0102%, close[t]=$43,925
```

| ラベル | max 値 | 該当 timestamp (UTC) | close[t] | t+24h close | 24h close 変動 | 24h close 最高/最低 |
|---|---:|---|---:|---:|---:|---|
| LONG_MFE_pct_K288 | 40.7045% | 2021-05-19 13:05 | $29,821 | $41,848 | +40.33% | 最高 $41,884 (+40.45%) |
| LONG_MAE_pct_K288 | 34.0102% | 2021-05-18 13:40 | $43,925 | $37,119 | -15.49% | 最低 $29,821 (-32.11%) |

**既知 BTC 大変動日との照合 (1 行)**:
両 max とも **2021-05-19 BTC 大暴落** (通称 "Bitcoin Black Wednesday" / Elon Musk Tesla の BTC 決済中断発言 + 中国マイニング規制 FUD で BTC が $43k → $29k に急落) の前後 24 時間に該当 → **既知の歴史的最大級単日変動と完全一致**。データ品質懸念なし。

整合性検証:
- LONG_MFE_K288 の起点 (2021-05-19 13:05) の close = $29,821 はクラッシュ底値付近 → 24h で +40.7% リバウンドは妥当 (実際の暴落底値からの V 字回復と整合)
- LONG_MAE_K288 の起点 (2021-05-18 13:40) の close = $43,925 はクラッシュ前ピーク付近 → 24h で -34.0% の最大逆行は実 BTC データ (最低 $29,821・-32.11%) + 5min バーの low (close < low) で 34% に到達する妥当性あり

---

### 証跡 4: 起点 23:55 の実装上理由

python 出力 (実 parquet query):
```
index.min(): 2021-04-01 23:55:00
index.max(): 2024-12-31 23:55:00
rows where 1d feature NaN: 97632  (※ 別問題・1d MTF lookback の影響)
total rows: 394561
```

実装上理由 (build_labels_pct.py 行番号引用):

1. **TRAIN_START 設定** ([build_labels_pct.py:96](../../scripts/priority_rebuild/build_labels_pct.py#L96)):
   ```python
   TRAIN_START = pd.Timestamp("2021-04-01")  # = 2021-04-01 00:00:00
   ```

2. **ラベル計算で先頭 287 行が NaN** ([build_labels_pct.py:208-225](../../scripts/priority_rebuild/build_labels_pct.py#L208-L225)):
   ```python
   def compute_mfe_mae_labels_pct(df5m: pd.DataFrame) -> pd.DataFrame:
       ...
       for K in K_BARS:  # K_BARS = [6, 12, 24, 48, 96, 144, 288]
           fut_max_high = h.shift(-K).rolling(K).max()
           ...
           out[f"LONG_MFE_pct_K{K}"] = (fut_max_high - c) / c * 100
   ```
   - K=288 (最大) で `h.shift(-288).rolling(288).max()` を計算
   - `shift(-288)`: 末尾 288 行が NaN 化 (h[t+288] 不在)
   - `rolling(288).max()`: 288 個の valid 値を必要とするため、shift 後の系列で先頭 287 行も valid 値不足で NaN 化
   - 結果: K=288 ラベルは先頭 287 行 + 末尾 288 行が NaN

3. **末尾 K=288 dropna** ([build_labels_pct.py:323-324](../../scripts/priority_rebuild/build_labels_pct.py#L323-L324)):
   ```python
   n_before = len(full)
   full = full.dropna(subset=[f"LONG_MFE_pct_K{K_BARS[-1]}"])  # K_BARS[-1]=288
   print(f"  末尾ラベル欠損行 drop: {n_before - len(full)} 行 (K={K_BARS[-1]} 末尾 24h)")
   ```
   - subset=K288_LONG_MFE で NaN 行を drop → **先頭 287 行 + 末尾 288 行が削除**
   - log メッセージは「末尾 24h」だが実際は先頭 287 行も同時 drop されている (実装挙動として正しいが log 表現が片側のみ言及)

4. **train split** ([build_labels_pct.py:331](../../scripts/priority_rebuild/build_labels_pct.py#L331)):
   ```python
   train = full.loc[(full.index >= TRAIN_START) & (full.index <= TRAIN_END)]
   ```
   - 既に先頭 287 行が drop 済の `full` から `>= 2021-04-01 00:00` をフィルタ → 最初に残る行が 2021-04-01 23:55:00 (= 287 × 5min = 23h55min 後)

**結論**: 起点 23:55 は `compute_mfe_mae_labels_pct` の `shift(-K).rolling(K)` 構造が必然的に発生させる先頭 287 行 NaN と、L324 dropna が両側を削る挙動の組み合わせ。バグではなく実装の数学的帰結。L324 のコメント (`末尾 24h`) は片側のみ言及で誤解を招く可能性あるが訂正は本タスクスコープ外 (本完了報告に記録のみ)。

---

## §2. ガード通過状況

- **G1 (公式 source grep 直接引用)**: ✅ 通過 — 証跡 2 の grep 4 行を直接引用、手計算なし
- **G2 (parquet 実クエリで日付抽出)**: ✅ 通過 — 証跡 3 で `df["..."].idxmax()` を実行、推測なし

異常値スメル該当なし (本タスクは PnL/勝率なしの訂正タスク・関所 A 適用外)。

---

## §3. 次のアクション (Phase 1 指示書発行待ち)

CC 側の本タスクは完了。Phase 1 確定パラメータ (指示書 §6 既述):
- ラベル数 14 / feature 数 1,414 (1,462 − 48 blacklist)
- learning_rate=0.02 / n_estimators=5000 / min_data_in_leaf=100 / feature_fraction=0.7 / bagging_fraction=0.8 / bagging_freq=5 / reg_lambda=0.1 / random_state=42 (Phase 1 旧版踏襲・WORKFLOW.md L546-560)

Web Claude が次セッションで Phase 1 指示書を発行する待ち状態。

---

## §4. commit 準備

以下 3 ファイルを add → 指示書 §5 のメッセージで commit:

```bash
git add v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_phase0_v3_completion_report_fix.md
git add v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-19_ml_implementation_phase0_1_completion_phase0.md
git add v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_phase0_v3_completion_report_fix_completion.md
git commit -m "fix: Phase 0 v3 完了報告 5 点訂正 + ラベル数 14 確定 + K288 max 日付特定"
```

以上。
