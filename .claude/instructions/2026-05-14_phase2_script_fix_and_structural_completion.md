# Phase 2 スクリプト改修 + refit 影響測定 + 構造改善 完了報告

公式 source: `results/priority_rebuild/ml_phase2_rerun_{prerefit,postrefit}/phase2_summary.json`

| 項目 | 値 |
|---|---|
| 完了日時 | 2026-05-14T18:52 JST |
| 関連指示書 | [2026-05-14_phase2_script_fix_and_structural.md](2026-05-14_phase2_script_fix_and_structural.md) |
| **改修後 script の自動判定** | refit 前 / refit 後 とも **4 指標 ALL PASS** |
| **refit 影響パターン** | **パターン 1**: refit 前後とも PASS・K12 LONG q99 大幅改善 (+16.06 → +36.21pp)・他 7 組合せ bit-exact 不変 |

## 1. 結果サマリー (Step 2-C)

| 指標 | refit 前 | refit 後 | 差分 |
|---|---:|---:|---:|
| q99 8 組合せ加重 net_quality | **+20.58pp** | **+21.28pp** | +0.70 |
| q99 positive (>0) 数 | 7/8 | 7/8 | ±0 |
| K12 LONG q99 net_quality | +16.06pp | **+36.21pp** | **+20.15** |
| K12 LONG q99 n_fire | 1,660 | 342 | 1/5 厳選 |
| K12 LONG q99 MFE_lift_pct | -9.99% | +46.07% | +56.06pp 反転 |
| 指標 2 最小値 (K96 SHORT q99) | -8.22pp | -8.22pp | ±0 |
| 指標 3 RMSE sanity | 16/16 | 16/16 | ±0 |
| 指標 4 (q99 中 MFE/MAE > 1.0) | 7/8 | 7/8 | ±0 |
| **4 指標 総合判定 (script 自動)** | **✅ ALL PASS** | **✅ ALL PASS** | 不変 |

出典:
- `ml_phase2_rerun_prerefit/phase2_summary.json` sha256 7e980f078d5e
- `ml_phase2_rerun_postrefit/phase2_summary.json` sha256 4245de8bc9e1

## 2. Step 別実施結果

### Step 1: run_phase2_precision.py 改修 (案 A・implementation gap 補完)

改修内容:
- `CRITERION_1_POSITIVE_MIN = 20 → 6` (改訂後 spec 準拠)
- `CRITERION_4_PASS_COUNT = 20 → 6` (同)
- `judge_criteria` を `df_q99 = df_nq[df_nq["q"] == "q99"]` で q99 8 組合せ抽出に変更
- コードコメント「q99 only」を実装と一致

改修コミットメッセージ予定:
> 案 G (commit b14be88) implementation gap 補完。新たな基準変更ではない。
> 監査#8 が §1.6.1 メタルール違反ではないと判定済。
> ただし結果 (案 Z) を見てから着手した timing の悪さは事実として記録。

script sha256: 472993b4aa0c

### Step 1-C: 案 G 完了報告訂正

[plan_g_pre_phase4_completion.md](2026-05-14_plan_g_pre_phase4_completion.md) 末尾に「2026-05-14 追記: 実装漏れ訂正 (監査#8 発覚)」セクション追加済。

### Step 2: 改修後 script で Phase 2 を 2 回判定

両方 4 指標 ALL PASS (§1)。K12 LONG q99 以外の 7 組合せは bit-exact 不変 (refit は K12 LONG だけに影響限定)。

### Step 3: 公式判定 source 明文化

- WORKFLOW.md 「公式判定 source の定義」セクション追記
- cc_ml_design_spec.md §1.6.1 末尾に「公式判定 source ルール」追記

### Step 4: spec / script consistency check

[results/priority_rebuild/spec_script_consistency_20260514.md](../../results/priority_rebuild/spec_script_consistency_20260514.md) に 7 項目チェック保存:

| 項目 | status |
|---|---|
| §4a.4 / §4a.5 / §4b.3 / Phase 1 hyperparam / §1.6 改訂 (本日改修) | ✅ 実装済・一致 (5 件) |
| §4b.4-b simulate_predicted_mfe_tp | ❌ 未実装 (Phase 4-b 着手時に実装) |
| §1.6.1 メタルール guard | ❌ scriptレベル guard なし (将来検討) |

### Step 5: web_claude_self_check.md 作成

[.claude/rules/web_claude_self_check.md](../rules/web_claude_self_check.md) 新規作成。チェック A (指示書発行前) + チェック B (完了報告受領時) を機械的に通す形式。

### Step 6: L-179 教訓拡張

[.claude/memory/lessons_active.md](../memory/lessons_active.md) L-179 末尾に「2026-05-14 拡張 (監査#8 必須 5)」追記。ML leak 限定 → spec/実装一般整合性に拡張。

## 3. 必須証跡 5 点 (コンパクト版)

| # | 項目 | 内容 |
|---|---|---|
| 1 | grep | `CRITERION_1_POSITIVE_MIN = 6` / `df_q99 = df_nq[df_nq["q"] == "q99"]` を改修後 script で確認済 |
| 2 | 数値の二重提示 | §1 比較表 + summary.json sha256 |
| 3 | 成果物実体 | script (472993b4aa0c) / prerefit summary (7e980f078d5e) / postrefit summary (4245de8bc9e1) / consistency.md / web_claude_self_check.md |
| 4 | 実行ログ | 2 回実行・各 2.5s・RC=0・Python warning 0 件 |
| 5 | 絞り込み示唆語彙 | 本報告に substantive 使用なし |

## 4. 次のステップ

1. Web Claude が独立評価 (self_check チェック B 適用) — 推奨独自再計算: `ml_phase2_rerun_postrefit/net_quality_24combinations.csv` の q99 8 組合せから加重平均を独自に計算 (期待値 +21.28pp / positive 7/8)
2. Step 2-C 比較表をまこさんに提示 → K12 LONG refit 維持/撤回判断
3. 判断確定後、セッション工程の retain/redo 範囲確定 → Phase 4-b 方針

## 5. 残課題 (本タスクスコープ外・申し送り)

- §4b.4-b `simulate_predicted_mfe_tp` 実装 → Phase 4-b 着手時
- §1.6.1 メタルール スクリプト guard → 将来検討
- 本日 spec/script consistency check の対象 7 項目以外の潜在乖離 → 必要に応じ拡張
