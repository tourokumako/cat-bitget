# 案 Z: K12 LONG refit 後データで Phase 2 再判定 完了報告

| 項目 | 値 |
|---|---|
| 完了日時 | 2026-05-14T17:51:08 JST (Phase 2 script 所要 2.6s) |
| 実行者 | CC (Claude Opus 4.7 1M context・本セッション) |
| 関連指示書 | [2026-05-14_phase2_revalidate_post_refit.md](2026-05-14_phase2_revalidate_post_refit.md) |
| 関連完了報告 | [phase1_k12long_refit_completion.md](2026-05-14_phase1_k12long_refit_completion.md) / [phase2_execute_completion.md](2026-05-14_phase2_execute_completion.md) |
| **§8 違反の影響範囲 判定** | **パターン 1: refit 後も PASS (改訂後 spec)・K12 LONG q99 net_quality が +16.06pp → +36.21pp (+20.15pp 大幅改善)** |
| **Phase 2 総合判定 (refit 後)** | 旧 spec 24 組合せ加重: FAIL (+9.18pp) / **改訂後 spec q99 加重: PASS (+21.28pp)** ← 元 Phase 2 と同一の総合判定 |
| **メタルール §1.6.1 関係** | §1.6.1 は「合格基準 (spec)」が対象・K12 LONG refit は「学習データ (モデル)」変更で §1.6.1 直接対象外・§8 違反は別途確定 (Step 4 整理) |

---

## 0. 結論サマリー

| 観点 | 結果 |
|---|---|
| Phase 2 4 指標 PASS/FAIL の総合判定変化 | **変化なし** (改訂後 spec で両方 PASS / 旧 spec で両方 FAIL) |
| K12 LONG q99 個別 net_quality | **+16.06pp → +36.21pp (+20.15pp 大幅改善)** |
| K12 LONG q99 n_fire | 1,660 → 342 (1/5 厳選) |
| K12 LONG q99 MFE_lift_pct | -9.99% → +46.07% (+56pp 反転) |
| その他 7 組合せ (K12 SHORT・K24/48/96 LONG/SHORT) | **bit-exact 完全同値** (refit が K12 LONG モデルのみ変更したため副作用なし) |
| §8 違反の影響 | refit は Phase 2「総合判定」を覆していない / K12 LONG q99 個別数値を「良い方向」に底上げ |
| 3 パターン判定 | **パターン 1** (refit 後も PASS・K12 LONG が大きく改善 = 結果を底上げした疑い・要協議) |

---

## 1. Step 0-1: 必読ファイル引用

### (a) cc_ml_design_spec.md §8 (全文)

出典: `cc_ml_design_spec.md` L281-288

```
## §8 制約・禁止事項

- ポジションサイズ 0.12 BTC/trade 上限厳守
- 未来情報（MFE/MAE ラベル）を入力特徴量に含めない（リーク）
- 本テスト（2026）データを Phase 6 以前に使わない
- 特徴量の事前絞り込み禁止（1,432 指標全部投入）
- 「暫定値」「経験的に」「定番だから」でパラメータを決めない（データ駆動原則）
- テスト結果を見てから学習データで再学習する際、テスト結果を直接参照しない
```

**該当行**: 最後の「テスト結果を見てから学習データで再学習する際、テスト結果を直接参照しない」

### (b) cc_ml_design_spec.md §1.6 / §1.6.1 全文

出典: `cc_ml_design_spec.md` L76-110 (要約抜粋)

§1.6 撤退ライン:
```
仮テスト（2025 年）で以下 4 指標を判定し、1 件以上 FAIL → ML 単独要協議

| # | 指標 | 合格基準 |
| 1 | q99 net_quality (q99 のみ 8 組合せ件数加重平均) | 平均 > +10pp かつ 8 組合せ中 6 組以上で > 0 |
| 2 | net_quality 最小値 (8 組合せ) | > -50pp |
| 3 | valid_rmse / label_std (16 ラベル) | 16 ラベル中 14 以上で < 1.5 |
| 4 | mean_real_MFE / mean_real_MAE (q99 後・8 組合せ) | 8 組合せ中 6 以上で > 1.0 |

注: q90/q95 は補助 lens として記録 (合格条件には算入しない・2026-05-14 案 G で改訂)
```

§1.6.1 合格基準変更ルール:
```
**原則**: 各 Phase の合格基準は当該 Phase 実行前に確定し、実行結果確定後の基準変更は
当該 Phase の合否判定に適用しない (構造的欠陥が判明した場合は次 Phase 以降に適用)。

**今回の例外**: 2026-05-14 の §1.6 指標1 改訂 (24 組合せ加重 → q99 加重) は、
audit#2 (Phase 2 実行前監査) で指摘されていた spec 欠陥への対応であり、
本来 Phase 2 実行前に行うべきだった補正の遅延取り込みとして処理する。
**これを最後の例外とし、今後この種の遅延補正は許容しない**。
```

### (c) 元 Phase 2 (refit 前) 判定

出典: `2026-05-14_phase2_execute_completion.md` L9-20 + L46-53

| 指標 | 値 |
|---|---|
| 旧 spec 24 組合せ加重 | +8.72pp (FAIL・+10pp 未達) |
| **改訂後 spec q99 加重** | **+20.58pp** (PASS) |
| q99 positive 件数 | 7/8 (PASS) |
| 指標 2 最小値 | -8.22pp (K96 SHORT q99) (PASS) |
| 指標 3 RMSE | 16/16 (PASS) |
| 指標 4 MFE/MAE > 1.0 | 23/24 (PASS) |
| 全体判定 | 旧 spec で 1 件 FAIL → 改訂後 spec で全 4 指標 PASS |

### (d) K12 LONG refit の動機

出典: `2026-05-14_phase1_k12long_refit.md` L30

> Phase 3 短期試行で「K12 LONG のみ num_leaves=15 で MFE_lift -9.99 → +46.07 (+56pp 改善)」

→ MFE_lift -9.99 は test 2025 数値 (`net_quality_24combinations.csv` L2・filtered_mean_real_MFE 273.03 / global_mean_real_MFE 303.34 → -9.99%) を見て学習データ (K12 LONG モデル num_leaves) を変更 → §8 抵触確定。

4 引用全件確認・期待値一致 ✅

---

## 2. Step 1 詳細: refit 後データで Phase 2 4 指標を判定

### 実行コマンド

```bash
python3 scripts/priority_rebuild/run_phase2_precision.py \
  --phase-dir results/priority_rebuild/ml_phase1_k12long_refit \
  --output-dir results/priority_rebuild/ml_phase2_post_refit \
  2>&1 | tee logs/phase2_post_refit_20260514_175104.log
```

Phase 2 script は `--phase-dir` 引数を受けるので、refit dir を渡せば自動的に refit dir 内の `predictions_test2025.parquet`・`entry_thresholds.json`・`training_summary.csv` を使用 (script 本体に追加変更コミットなし)。

### 入力検証 (sanity)

| 項目 | 値 |
|---|---|
| predictions sha256 | 4e4e6bfc32d9 (refit 適用済) |
| Phase 1 base sha256 (比較用) | da55fbd7e849 (refit dir のものとは別) |
| LONG_MFE_K12 mean | **209.1905** (refit) ← Phase 1 base: 212.9587 |
| LONG_MFE_K24 mean | 320.3600 (refit・Phase 1 base 共通) |
| null cells | 0 |
| inf cells | 0 |
| 行数 | 105,120 (test 2025 全期間) |

→ refit 版 predictions を使用していることを K12 LONG MFE 平均値で verify ✅

### refit 後 Phase 2 4 指標判定結果

(出典: `phase2_summary.json` + `net_quality_24combinations.csv`)

| # | 合格基準 | refit 後 | PASS/FAIL |
|---|---|---|---|
| 1 (旧 spec 24 組合せ加重) | > +10pp かつ 20+ positive | **+9.18pp** / 23/24 | **❌ FAIL** (+0.82pp 不足) |
| 1 (改訂後 spec q99 加重 8 組合せ) | > +10pp かつ 6+ positive | **+21.28pp** / 7/8 | **✅ PASS** |
| 2 (net_quality 最小値) | > -50pp | -8.22pp (K96 SHORT q99) | ✅ PASS |
| 3 (16 ラベル RMSE) | 14+ で < 1.5 | 16/16 | ✅ PASS |
| 4 (MFE/MAE > 1.0) | 20+ (旧) / 6+ (新) | 23/24 (旧 spec 単位) | ✅ PASS |

注: スクリプト本体は旧 spec の閾値 (CRITERION_1_WEIGHTED_AVG_MIN=10.0 / CRITERION_1_POSITIVE_MIN=20) を使用しているため出力は「FAIL」表記だが、これは旧 spec ベース。改訂後 spec (q99 加重・8 組合せ) を独立計算した結果 PASS。

---

## 3. Step 2: 元 Phase 2 (refit 前) との比較

### 3-1. 4 指標 + K12 LONG q99 個別 比較表

| 指標 | 元 Phase 2 (refit 前) | 案 Z (refit 後) | 差分 |
|---|---:|---:|---:|
| 旧 spec 24 組合せ加重 | +8.7226pp | **+9.1801pp** | **+0.4575pp** |
| 24 組合せ positive 件数 | 23/24 | 23/24 | ±0 |
| **改訂後 spec q99 加重 (8 組合せ)** | **+20.5821pp** | **+21.2817pp** | **+0.6996pp** |
| q99 positive 件数 (8 中) | 7/8 | 7/8 | ±0 |
| **K12 LONG q99 net_quality** | **+16.0594pp** | **+36.2111pp** | **+20.1517pp** ← 大幅改善 |
| K12 LONG q99 MFE_lift_pct | -9.9918% | **+46.0723%** | **+56.06pp** ← 反転 |
| K12 LONG q99 MAE_lift_pct | -26.0512% | +9.8613% | +35.91pp |
| K12 LONG q99 n_fire | 1,660 | **342** | -1,318 (1/5 厳選) |
| 16 ラベル RMSE sanity 通過数 | 16/16 | 16/16 | ±0 |
| MFE/MAE > 1.0 件数 (24 組合せ単位) | 23/24 | 23/24 | ±0 |
| 指標 2 最小値 (K96 SHORT q99) | -8.222303 | -8.222303 | ±0 (構造的) |
| **4 指標 総合判定 (旧 spec)** | FAIL (指標 1) | **FAIL (指標 1)** | 不変 |
| **4 指標 総合判定 (改訂後 spec)** | PASS | **PASS** | 不変 |

### 3-2. q99 各組合せ別 net_quality 比較

(出典: 元 `ml_phase2/net_quality_24combinations.csv` vs 新 `ml_phase2_post_refit/net_quality_24combinations.csv`)

| K | side | 元 net_quality | refit net_quality | Δ |
|---:|---|---:|---:|---:|
| 12 | LONG | +16.0594 | **+36.2111** | **+20.1517** |
| 12 | SHORT | +10.9670 | +10.9670 | ±0 |
| 24 | LONG | +6.0244 | +6.0244 | ±0 |
| 24 | SHORT | +28.6314 | +28.6314 | ±0 |
| 48 | LONG | +33.7153 | +33.7153 | ±0 |
| 48 | SHORT | +27.7116 | +27.7116 | ±0 |
| 96 | LONG | +23.3742 | +23.3742 | ±0 |
| 96 | SHORT | -8.2223 | -8.2223 | ±0 |

→ K12 LONG q99 のみが変化・他 7 組合せは bit-exact 完全同値 (refit が K12 LONG モデルのみ変更・他ラベル predictions は手を加えていないため自然な結果)。

---

## 4. Step 3: §8 違反の影響範囲 パターン判定

| パターン | 該当判定 | 判定根拠 |
|---|:---:|---|
| パターン 1: refit 後も PASS・K12 LONG が大きく改善 | **✅ 該当** | 改訂後 spec で PASS 維持 (+20.58 → +21.28・+0.70 改善) / K12 LONG q99 net_quality が +16.06 → +36.21 (+20.15pp 大幅改善) / MFE_lift_pct が -9.99 → +46.07 で反転 |
| パターン 2: refit 後も PASS・K12 LONG ほぼ不変 | ✗ 不該当 | K12 LONG q99 net_quality は +20.15pp の大幅変化があり「ほぼ不変」ではない |
| パターン 3: refit 後は FAIL | ✗ 不該当 | 改訂後 spec で PASS 維持 (旧 spec では元から FAIL のままで変化なし) |

### パターン 1 含意の整理

- refit は Phase 2「総合判定」を覆していない (改訂後 spec で元から PASS・refit 後も PASS)
- しかし K12 LONG q99 個別 net_quality は **+20.15pp 大幅改善** (約 2.3 倍)
- 改訂後 spec q99 加重も +0.70pp 上方修正 (refit 完了報告と一致)
- 「refit が結果を底上げした疑い」= K12 LONG q99 個別数値は明確に底上げ・8 組合せ加重も 0.70pp 底上げ
- 「要協議」の対象: 後段 Phase (4-a/4-b/5) で K12 LONG q99 net_quality を根拠とする設計判断があれば、その判断が refit 由来の底上げに依存している可能性

---

## 5. Step 4: メタルール §1.6.1 との関係整理 (論点書き出しのみ)

### 5-1. §1.6.1 の対象範囲

§1.6.1 原則 (cc_ml_design_spec.md L100-102):
> 各 Phase の合格基準は当該 Phase 実行前に確定し、実行結果確定後の基準変更は当該 Phase の合否判定に適用しない (構造的欠陥が判明した場合は次 Phase 以降に適用)

**§1.6.1 が直接対象とするもの**: 「合格基準 (spec)」の変更
- 例: 24 組合せ加重 → q99 加重 (合格基準の定義の変更)

**§1.6.1 が直接対象としないもの**: 「学習データ・モデル」の変更
- K12 LONG refit (num_leaves=31 → 15) は学習データ生成過程の変更
- 合格基準 (spec) は変更していない

### 5-2. §8 違反との関係

§8 (cc_ml_design_spec.md L288):
> テスト結果を見てから学習データで再学習する際、テスト結果を直接参照しない

K12 LONG refit は audit#3 の test 2025 数値 (MFE_lift_pct -9.99%) を直接参照して num_leaves を変更 → **§8 直接違反**

### 5-3. §1.6.1 を refit に「準用」すべきかの論点

**準用するメリット**:
- §1.6.1 は「結果を見て後出しで変える」精神を禁じている
- refit も「test 結果を見て後出しで学習データ変更」で同じ精神に反する
- 「これを最後の例外とし、今後この種の遅延補正は許容しない」を refit にも拡張解釈すれば、refit 撤回 (案 X) の根拠になる

**準用しないメリット**:
- §1.6.1 は「合格基準」を対象としており、文言を拡張解釈すると射程が広がりすぎる
- §8 違反として独立に処理すれば足りる
- 「学習データ変更」は §8 / 「合格基準変更」は §1.6.1 と分業した方が spec の明確性が保たれる

**論点**: K12 LONG refit にメタルール §1.6.1 を準用するか・§8 違反として独立処理するか・両方適用するか → Web Claude + まこさん判断

### 5-4. 監査#7 見落とし K の指摘 (再掲)

> メタルール §1.6.1 = 「結果確定後の基準変更は当該 Phase の合否判定に適用しない」
> 案 G 当時は「spec 改訂」の話だったが、refit も「結果を見て学習データ変更」で同類

監査#7 は「同類」と指摘・本タスクでは「同類か別類か」を明確に整理 (Step 5-1/5-2/5-3)。

---

## 6. CC 整理: refit 残置/撤回 の判断材料

### 6-1. 残置の論拠

- 改訂後 spec で PASS 維持 (refit 前後とも PASS)
- K12 LONG q99 個別の改善 (+20.15pp) は Phase 4-a / 4-b の入力品質向上に寄与
- 他 7 組合せは bit-exact 不変 (副作用なし)
- 8 組合せ加重 +0.70pp 改善は小さく、改訂後 spec PASS 判定には致命的影響を与えていない

### 6-2. 撤回の論拠

- §8 直接違反 (test 結果を見て学習データ変更) は spec 上禁じられている
- §1.6.1 の精神 (「最後の例外とし、今後この種の遅延補正は許容しない」) を準用すれば撤回根拠
- refit の動機 = audit#3 の test 数値 (MFE_lift -9.99%) → 「test 結果を見て学習データ変更」の構図そのもの
- 後段 Phase で K12 LONG q99 数値 (+36.21pp) を根拠にする判断は refit 由来底上げに依存

### 6-3. CC の整理結論

CC は推奨を一本化せず、判断材料を提示するに留める (Step 4 で論点整理した通り)。
最終判断はまこさん + Web Claude。

---

## 7. 完了報告必須証跡 5 点

### 証跡 1. コード総点検 grep 結果

```
$ grep -n "k12long_refit\|predictions_test2025" scripts/priority_rebuild/run_phase2_precision.py
6:  - results/priority_rebuild/ml_phase1/predictions_test2025.parquet (予測値 16 ラベル × 105,120 行)
58:PREDS_TEST = PHASE_DIR / "predictions_test2025.parquet"
```

→ スクリプト本体は `predictions_test2025.parquet` 名をハードコード参照だが、`PHASE_DIR` を `--phase-dir` で切り替えられるため refit dir 内の `predictions_test2025.parquet` (実体は refit 後・sha256 4e4e6bfc32d9) を読み込む。コード変更なしで refit データに対応。

### 証跡 2. 数値の二重提示

- チャットサマリー: §1〜§6 各セクション
- 出典 (sha256 付き):
  - `results/priority_rebuild/ml_phase2_post_refit/net_quality_24combinations.csv` sha256 3107d6094e7c
  - `results/priority_rebuild/ml_phase2_post_refit/phase2_summary.json` sha256 53a017f4545f
  - 元 Phase 2 (refit 前): `results/priority_rebuild/ml_phase2/net_quality_24combinations.csv` (元 commit 0ffd326)
  - K12 LONG refit 完了報告: `2026-05-14_phase1_k12long_refit_completion.md` L26-29 で同じ数値 (+21.28pp / +36.21pp) が報告済 → bit-exact 一致確認

### 証跡 3. 成果物ファイル実体 (sha256 + 行数 + 更新時刻)

| ファイル | サイズ | sha256 (12 桁) | 更新時刻 |
|---|---:|---|---|
| [phase2_summary.json](../../results/priority_rebuild/ml_phase2_post_refit/phase2_summary.json) | - | 53a017f4545f | 2026-05-14 17:51 |
| [net_quality_24combinations.csv](../../results/priority_rebuild/ml_phase2_post_refit/net_quality_24combinations.csv) | - | 3107d6094e7c | 2026-05-14 17:51 |
| [mfe_mae_ratio_24combinations.csv](../../results/priority_rebuild/ml_phase2_post_refit/mfe_mae_ratio_24combinations.csv) | - | 1288f40e99be | 2026-05-14 17:51 |
| [rmse_sanity_16labels.csv](../../results/priority_rebuild/ml_phase2_post_refit/rmse_sanity_16labels.csv) | - | cc30aa9ad005 | 2026-05-14 17:51 |
| [old_leak_comparison.csv](../../results/priority_rebuild/ml_phase2_post_refit/old_leak_comparison.csv) | - | efcdfb0e8a8b | 2026-05-14 17:51 |
| logs/phase2_post_refit_20260514_175104.log | - | - | 2026-05-14 17:51 |

### 証跡 4. 実行ログ

| 項目 | 値 |
|---|---|
| コマンド | `python3 scripts/priority_rebuild/run_phase2_precision.py --phase-dir results/priority_rebuild/ml_phase1_k12long_refit --output-dir results/priority_rebuild/ml_phase2_post_refit` |
| 開始 | 2026-05-14T17:51:05 JST |
| 終了 | 2026-05-14T17:51:07 JST |
| 所要 | **2.6 秒** |
| 終了コード | **0** |
| Python warning | **0 件** |

### 証跡 5. 絞り込み示唆語彙 自己 grep 結果

本完了報告に対し 12 語彙を grep:

| 語彙 | substantive 件数 |
|---|---:|
| 採用候補 | 0 (本タスクは判定整理で採用候補語彙不使用) |
| 効く | 0 |
| 効かない | 0 |
| 重要 | 0 |
| 優先 | 0 |
| 不要 | 0 |
| 切れる | 0 |
| 残せる | 0 |
| 除外して良い | 0 |
| 使える | 0 |
| 意味がある | 0 |
| 意味がない | 0 |

substantive 使用なし (§7-5 grep listing 行のみ各 1 件)。

---

## 8. 物理証跡 8 点

| # | 項目 | 結果 |
|---|---|---|
| 1 | 入力ファイル整合性 | ✅ refit predictions sha256 4e4e6bfc32d9・Phase 1 base sha256 da55fbd7e849 で別物確認 / LONG_MFE_K12 mean=209.19 (refit) vs 212.96 (base) で K12 LONG 列が refit 版である verify |
| 2 | 計算プロセス内部証跡 | ✅ K12 LONG q99 net_quality を独立 Python で再計算 → 36.2111pp (script 出力と完全一致) |
| 3 | 出力ファイル証跡 | ✅ 全 5 出力ファイル (CSV/JSON) sha256 取得 |
| 4 | 第三者再計算検証 | ✅ K12 LONG q99 を Python で独立再計算: threshold=1.366959 / n_fire=342 / MFE_lift=46.0723pp / MAE_lift=9.8613pp / net_quality=36.2111pp ← script と完全一致 |
| 5 | データ sanity | ✅ null 0 件 / inf 0 件 / 行数 105,120 / K12 LONG が refit 版 (mean 209.19) |
| 6 | stderr / Python warning | ✅ 0 件 |
| 7 | bit-exact 再現性確認 | ✅ 同コマンドを 2 回実行 → 全 4 CSV (net_quality / rmse_sanity / mfe_mae_ratio / old_leak) sha256 完全一致 |
| 8 | 元 Phase 2 との差分が全指標で明示されているか | ✅ §3-1 比較表で全 4 指標 + K12 LONG q99 個別 + 8 組合せ別 net_quality を全件記載 |

---

## 9. 完了後の状態

- ✅ refit 後データでの Phase 2 判定結果が判明 (旧 spec FAIL / 改訂後 spec PASS)
- ✅ 元 Phase 2 (refit 前) との差分が判明 (K12 LONG q99 +20.15pp 大幅改善・他 7 組合せ bit-exact 同値)
- ✅ §8 違反の影響範囲が判明 = **パターン 1** (refit 後も PASS・K12 LONG が大きく改善)
- ✅ メタルール §1.6.1 との関係が論点整理済 (§1.6.1 直接対象は「合格基準」・refit は「学習データ」・準用するか §8 単独違反として処理するかは未確定)
- ✅ refit 残置/撤回の判断材料が揃った (§6・両論記載・CC は推奨一本化せず)

---

## 10. 次のステップ

1. **Web Claude が生 CSV から独立評価** (CC サマリーを見る前に・監査#6/#7 懸念対応)
   - 推奨独自再計算: `ml_phase2_post_refit/net_quality_24combinations.csv` の q99 8 組合せから加重平均を独自に計算 → CC 集計 +21.28pp と差分照合
   - K12 LONG q99 を `labels_mfe_mae_test_2025.parquet` + `ml_phase1_k12long_refit/predictions_test2025.parquet` から独立再計算 → CC 値 +36.21pp と一致確認
   - 元 `ml_phase2/net_quality_24combinations.csv` と新 `ml_phase2_post_refit/net_quality_24combinations.csv` の差分 (K12 LONG のみが変化していること) を独自 diff
2. 独立評価と CC 集計を差分照合
3. まこさん最終 GO で refit 残置/撤回を確定
4. その後で残る緊急対応 (絶対閾値 drift 対処・rolling 検討) へ

### 「数値の出所 (train か test か)」確認 (監査#6/#7 懸念対応)

本タスクで使用した数値の出所:

| 数値 | 出所 |
|---|---|
| K12 LONG MFE_lift -9.99% (audit#3 / refit 動機) | **test 2025** (`ml_phase2/net_quality_24combinations.csv` L2・filtered_mean_real_MFE 273.03 / global_mean_real_MFE 303.34) |
| K12 LONG MFE lift +364.97% (前タスク §3-B) | **train 2021-2024** (`labels_mfe_mae_train_2021_2024.parquet` から q99 fire 3,948 件の実 MFE 計算) |
| K12 LONG MFE_lift +46.07% (本タスク refit 後) | **test 2025** (`ml_phase2_post_refit/net_quality_24combinations.csv` L2・refit predictions で q99 fire 342 件・filtered MFE 443.10 / global 303.34) |
| K12 LONG q99 net_quality +36.21pp (本タスク) | **test 2025** |
| K12 LONG q99 net_quality +16.06pp (元 Phase 2) | **test 2025** (refit 前 predictions・1,660 件) |

これらは全て **test 2025 由来の数値** (train 由来は前タスク §3-B のみ)。
監査#7 の指摘「Web Claude が test 由来数値を train 問題と誤認」は前タスク Step 3-B で発生・本タスクでは test 由来であることを明示済。
