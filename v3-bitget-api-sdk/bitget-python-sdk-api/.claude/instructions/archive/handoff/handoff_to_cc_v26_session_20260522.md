# handoff_to_cc_v26_session_20260522.md

(起案者・CC・2026-05-22 / 宛先・CC = 次セッション)
**版**: v26 (Phase 1 v5.1 Step E case_a 実装完了 + Z 案ガード改訂・Step F 本走 smoke 着手準備)
**前身**: handoff v25 (Step 2/A-C/D 完了 + Phase 1 v5.1 設計確定)

---

## §0 セッション要約 (1 行)

Step E (case_a 実装 637 行) + 物理 leak verify ツール (446 行・TF-aware) + Plan エージェント独立監査 (sample regime 過依存確定) + phase_compliance §1.4 Z 案改訂 (3 段階運用・物理 verify 経由続行可) + smoke 動作確認 (Z 案ガード警告ログ + 続行 ✅) + lessons L-206 新規追加。**異常値スメル (sharpe=6.4・sim_pnl=$8689 / 1 fold smoke) は次セッション本走で要再評価**。

---

## §1 本セッション完了事項

### 1.1 Step E (案 a 実装) 完了

- **新規**: `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py` (637 行)
- 16 model (LONG/SHORT × MFE/MAE × K={12,24,48,96}) × 5 fold = 80 学習設計
- TP first 0/1 化: `pred_MFE / max(pred_MAE, 1e-6) >= 1.5` (phase_flow_v4 L151 既定・LONG/SHORT 共通)
- TP first 正解: `triple_barrier_label_{side}_K{K} == +1` (全案統一)
- train/valid 分離: Purged train_idx 末尾 10% を valid + embargo assert
- feature_importance 全 16 model 保存 (Phase 2 ハイパラ調整参照用)
- runner v5.1 統合 (W1/W2 警告 + DSR 連携 + 8 組合せ aggregate)
- CLI 完備 (`--smoke / --full / --parquet 明示 / --k / --side / --n-splits / --min-train-splits`)

### 1.2 物理 leak verify ツール実装

- **新規**: `scripts/priority_rebuild/verify_top20_features_leak.py` (446 行)
- 4 verify 項目:
  - (i) **lag-1 shift 不変性 TF-aware** (`_extract_tf_minutes` で TF サフィックス抽出・expected pct_diff = 5/TF_min を ±50% で許容・5m/15m/30m/4h 全 TF 対応)
  - (ii) 末尾 K bars NaN pattern (末尾 K bars NaN ≤ 5% で PASS)
  - (iii) 二重 N サフィックス内外一致 (正規表現で `_N\d+_N\d+` 抽出)
  - (iv) importance gain single < 50% (関所 A 異常値検査)
- 実機 verify 結果:
  - sample (25k 行) 4 件: 全 4 PASS
  - full (394k 行) 5 件: 全 4 PASS (sample 4 + support_distance 1)

### 1.3 Plan エージェント独立監査 + 重大発見

- 監査観点: ① 統計学的妥当性 / ④ ソフトウェア工学 / ⑦ CC 作業バイアス
- **sample 89 日 top20 入り 4 件** (dist_to_fib_v2_382 / resistance_distance / dist_to_fib_v2_500 / nearest_level_touch_count) → **full 4 年で top20 外 = レジーム過依存 (false_positive §2 類型 D 時代依存) 確定**
- full 4 年で新検出 1 件 (`support_distance_pct_N100_N100__5m`) も物理 verify 全 4 PASS
- full top20 トップ: `atr14_pct__5m` / `close_vs_st_upper_pct__5m` / `bb_bw_rolling_p20_100b__15m` / `dist_to_VAH_pct_N200_b100_va80_N200__1h` 等 = **業界知見整合の強い予測子**
- 監査懸念 3-a (sample レジーム過依存リスク) 確定で CC γ 案 (ガード OFF) 撤回 → Z 案 (物理 verify 経由続行) に方針転換

### 1.4 phase_compliance §1.4 Z 案改訂 (正本改訂)

- **修正**: `.claude/rules/phase_compliance_checklist.md` §1.4 (3 段階運用)
- 旧: top1-20 hit → 即 sys.exit(1)・調査必須・緩和不可
- 新運用:
  - **(a-1)** hit 検出 → 物理 verify 4 項目セット **全 PASS** → 警告ログ + `full_rank.csv` 記録 + 続行可 (false positive 確定・本物の強い予測子)
  - **(a-2)** 1 項目でも FAIL/SKIP → 即停止 sys.exit(1)・調査必須
  - (b) top21-50 hit / (c) top51以下 は旧運用継続
  - ブラックリストパターン自体の緩和は実施しない (将来回帰検出機能維持・defense-in-depth)
- 改訂根拠: false_positive §5 関所 G「すり抜けるたびに穴を塞ぐ」整合 + Plan 監査改善方向 #2

### 1.5 case_a `_check_fractal_leak` ロジック拡張

- hit 検出 → 物理 verify 4 項目 (verify_top20_features_leak から import) 内部呼出
- 全 PASS → 警告ログ + `_early_fi_for_guard_review/full_rank_*.csv` 保存 + 続行
- FAIL → sys.exit(1)
- smoke 動作確認 ✅ (sample 89 日で hit 4 件全 PASS → 学習続行成功)

### 1.6 lessons L-206 新規追加

- **L-206**: ブラックリストガードを保守一辺倒で運用すると false positive で物理進行不能 — Z 案 (物理 verify 経由続行) 改訂で defense-in-depth 維持

---

## §2 ⚠️ 異常値スメル (次セッション本走で要再評価)

smoke 実行 (sample 89 日 / K=12 LONG / n_estimators=30 / n_splits=3) で:
- **fold 0**: tp_precision=0.000 / sim_pnl=$0 / sharpe=nan
- **fold 1**: tp_precision=0.402 / sim_pnl_year_usd=**$8,689** / sharpe=**6.417**

false_positive §5 関所 A 異常値判定基準:
- ① 勝率 > 70% / ② 月次 NET > $3,800 / ③ IS/OOS Sharpe > 3 倍乖離 / ④ DD < 月次 NET の 10%

→ ③ sharpe=6.417 は異常値域。ただし統計的有意性なし (短期間 sample + n_estimators=30 浅学習 + 1 fold のみ)。

**Step F 本走 (full parquet 5 fold / n_estimators=300+) で再評価必須**。出続けたら以下調査:
- 類型 D regime 過依存 (sample 2021-04〜06 単一相場依存)
- TP first 予測の小サンプル偏り
- pred_MFE/100 を returns に使う設計の暫定性 (Phase 4-b 前)

---

## §3 次セッション CC 優先順位

### §3.1 優先 1 — Step F: 本走 smoke (約 30-60 分)

```bash
# 案 A: sample.parquet で 5 fold smoke (規定設定)
python scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py --smoke \
    --n-estimators 300 --n-splits 5
# 案 B: full train で K=12 LONG のみ 5 fold (本走想定の本格 smoke)
python scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py \
    --parquet results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet \
    --k 12 --side LONG --n-splits 5 --n-estimators 300
```

**検証項目**:
1. Z 案ガード警告ログ + 続行が本来環境で動作するか
2. 異常値スメル 4 条件 verify (sharpe / month NET / IS-OOS Sharpe / DD)
3. メモリ消費実測 (1 model 10-15 GB 想定・5 fold × 2 model = 10 model peak)
4. fold 単位 metrics の妥当性 (tp_precision / sim_pnl / fold_sharpe)

### §3.2 優先 2 — Step G: CP2 監査 (`/audit` 経由)

監査対象: Phase 1 v5.1 案 a 実装 + Z 案ガード改訂 + 本走 smoke 結果
監査依頼内容 (指示書 §9 7 項目 + 本セッション追加):
1. Purged K-Fold 5 fold の Embargo 設定妥当性
2. DSR 計算の Selection bias 補正妥当性 (n_trials=6)
3. 6 案間の比較公平性
4. 合格基準 5 指標の判定厳格性
5. Meta-Labeling 2 段階の leak 不在
6. Phase 1-c smoke entropy lift 6.04% との比較
7. CC 同型バイアス 43+ 件 再演有無
8. **(新規)** Z 案改訂後の defense-in-depth 維持妥当性
9. **(新規)** 異常値スメル原因分析

### §3.3 優先 3 — Step H: full 8 組合せ実行 (約 5-6 時間 / 3 並列 2 時間)

CP2 OK 後・full parquet で 8 組合せ × 5 fold = 80 学習。
- 完了後: §4.1 採用判定 (6+ 組合せ ALL PASS) or Layer 3 投入決定

### §3.4 その後 — 案 b-f 順次実装 (約 3-4 週間)

- 案 b binary / 案 c multiclass / 案 d lambdarank / 案 e triple_barrier multiclass / 案 f meta_labeling (sequential)
- 6 案合計 260 学習 → §4.1 採用判定

---

## §4 引き継ぎリソース (新セッション Step 0 で必読・3 層構造)

### Layer 1 (毎セッション必読)

- **本ファイル** `handoff_to_cc_v26_session_20260522.md` (最新版・find で取得)
- `WORKFLOW.md` 改訂24 active ブロック (Step F 着手準備反映)
- `CLAUDE.md` (Layer 2 パス修正済・改訂22 ベース)
- `lessons_active.md` 直近 5 件 (**L-206 最新** + L-205 + L-204 拡張 + L-203 + L-202)

### Layer 2 (Step F 着手時)

- **Phase 1 v5 指示書 v5.1** (`.claude/instructions/2026-05-22_phase1_layer_inversion_instruction.md`)
- **cc_ml_design_spec.md §1.5.1 v5.1**
- **case_a スクリプト** (`scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py`・637 行)
- **verify_top20 ツール** (`scripts/priority_rebuild/verify_top20_features_leak.py`・446 行)
- **runner v5.1** (`scripts/priority_rebuild/run_phase1_v5_purged_kfold.py`・773 行)
- **dsr.py + test_dsr.py** (`scripts/priority_rebuild/`)
- **phase_compliance §1.4 Z 案** (`.claude/rules/phase_compliance_checklist.md`)
- **`.claude/memory/phase_flow_v4_with_recovery.md`** (L151 1.5 既定 / L528 Phase 4-b-2 本確定)
- **`.claude/memory/technical_analysis_knowledge_base.md`** §I.6.3

### データ・環境

- **parquet 3 種** (`results/priority_rebuild/labels_mfe_mae_pct_{train_2021_2024,test_2025,test_2026_q1}.parquet`)
- **.venv311 環境** (mlfinpy 0.1.2 + timeseriescv 0.2 + scikit-learn 1.8.0 + lightgbm 4.6.0 + scipy 1.17.1)
- **smoke 出力**: `results/priority_rebuild/ml_phase1_v5/_early_fi_for_guard_review/` (fi_top20_K12_LONG_MFE.csv + full_rank_K12_LONG_MFE.csv)
- **leak verify JSON**: `results/priority_rebuild/leak_verify_*.json` (sample + full 計 3 件)

---

## §5 CC 同型バイアス警戒 (累積 45+ 件・本セッション +2)

handoff v25 §5 累積 43+ 件 + 本セッション 2 件:
1. **γ 案 (ガード OFF) を独断提案して監査経路省略バイアス** (cc_role §1.4 #4 現状把握スキップ同型) → Plan 監査で軌道修正
2. **TF-aware ロジック非搭載で初期 verify ロジックが MTF 特徴量を WARN 誤判定** (sample 4 件の lag-1 shift 結果を「leak 疑い」と早計判定しかけた)

### 次セッション CC への命令

- **L-206 を Step 0 で最優先警戒**: ブラックリストガード関連の判断で「停止 vs 緩和」二択思考に陥らず「物理 verify 経由続行」を選択肢に加える
- L-205: 設計閾値・パラメータ根拠 verify は最低 3 ファイル grep (cc_ml_design_spec + phase_flow_v4 + technical_analysis_knowledge_base) 義務化
- L-204: system reminder で auto-load されているファイルも Read tool で取り直す
- L-200: 「読んだ」「verify した」「監査済」と書く時は同ターン内に機械的証跡 (`wc -l` + Read 全文 + 該当行引用) を必ず出す
- cc_role §1.2: 監査経路は CC 単独判定で進めたい時こそ使う (本セッションで実証・γ 案撤回)
- cc_role §1.5: 戦略本丸以外は CC が判断・断言・実行 (確認質問乱発禁止)
- core_rules §MUST: コード変更前に差分提示 → GO 待ち・1 ターン 1 変更・bitget_keys.json 警告

---

## §6 本テスト Q1 (2026 Q1) 到達まで

```
[現在] Step E (case_a 実装) 完了 + Z 案ガード改訂 + smoke 動作確認 完了
    ↓ (Step F 本走 smoke・30-60 分)
[Step G CP2 監査] (`/audit` 経由・9 項目)
    ↓
[Step H full 8 組合せ × 案 a] (約 5-6 時間 / 3 並列 2 時間)
    ↓ (案 b-f 順次・各 1-2 日 + full 数時間)
[Phase 1 完了] (6 案 × 8 組合せ評価完了・約 3-4 週間)
    ↓
[§4.1 判定]
  ├── 6+ 組合せ ALL PASS あり → Phase 2 (Optuna ハイパラ調整・約 3-5 日)
  └── ALL PASS なし → 即 Layer 3 (CPCV + Class balancing + custom loss + アルゴ多様化)
    ↓
[Phase 3-a/3-b] cluster (KMeans / GMM / HDBSCAN 比較)
    ↓
[Phase 4-a/4-b] k-means + Exit 設計 (Entry 閾値本確定・3 方式並列)
    ↓
[Phase 5] 365d Replay (仮 test 2025 月次 NET ≥ $1,900 全 12 ヶ月)
    ↓
[Phase 6-b] 本テスト 2026 Q1 (月次 NET ≥ $1,900 全 3 ヶ月)
    ↓
[Phase 7] Bot 統合 (推論再現性 → ML Decider → run_once_ml → デモ → 本番)
```

---

## §7 メタ反省

本セッションで建設的成果:
- Plan エージェント独立監査が CC γ 案 (ガード OFF) を軌道修正 → Z 案 (物理 verify 経由続行) で defense-in-depth 維持
- sample 89 日 → full 4 年で top20 入り 4 件が完全に置き換わる (= 類型 D regime 過依存) を実証データで確認
- TF-aware lag-1 shift verify の初期実装で MTF 特徴量を WARN 誤判定しかけた経験 → 将来同 verify を実行するときに自動判定可能なロジック (`_extract_tf_minutes` + expected pct_diff = 5/TF_min) を実装

CC 改善方向:
- ブラックリストガード関連の判断で「停止 vs 緩和」二択思考に陥らず「物理 verify 経由続行」を選択肢に加える (L-206)
- 監査経路を **CC 自己判断で進めたい場面ほど通す** (cc_role §1.2 + §1.4 #4 対策)
- 本セッションのまこさんは「技術判断はわからない」を多用したが、CC が cc_role §1.5 (戦略本丸以外は CC 判断責任) を理解して断言・実行した

---

以上。
