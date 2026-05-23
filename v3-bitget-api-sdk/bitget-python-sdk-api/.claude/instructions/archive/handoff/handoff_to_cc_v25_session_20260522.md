# handoff_to_cc_v25_session_20260522.md

(起案者・CC・2026-05-22 / 宛先・CC = 次セッション)
**版**: v25 (Phase 1 v5.1 設計確定 + Step 2/A-C/D 完了・Step E 着手準備)
**前身**: handoff v24 (Step D 優先 1 完了 + 必読リスト 3 層構造化 + L-204)

---

## §0 セッション要約 (1 行)

Phase 1 v5 §6 Step 2 (runner 初版 529 行) → まこさん Q1/Q2/Q3 議論で **Phase 1 v5.1 厳格化** (8 組合せ評価 + TP first 正解統一 + W1/W2 警告) 確定 → Step A-C (spec/指示書/CLAUDE.md 修正) + Step D (runner v5.1 拡張 773 行) 完了 + lessons L-205 新規 + L-204 拡張 (CLAUDE.md パス hardcode 不整合追加事案)。

---

## §1 本セッション完了事項

### 1.1 Step 2 完了 (commit `6412cf1`・共通 Purged K-Fold runner 初版・529 行)

- `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` 新規
- timeseriescv.PurgedWalkForwardCV ラッパ (pred_times = index / eval_times = t1 vertical barrier)
- t1 は parquet 未保存のため runtime 算出 (`index + K * 5min`・leak フリー)
- Phase -1 blacklist 64 列 (8 family × 8 TF) + 56 ラベル列を物理 drop (Prime Directive §0-1)
- dsr.py 統合 (5 fold aggregate で DSR 算出・sr_variance = fold_sharpe variance ddof=1)
- 公開 API (旧版): `load_parquet_with_blacklist` / `prepare_purged_cv` / `split_with_purging` / `compute_t1_vertical_barrier` / `compute_fold_metrics` (旧) / `save_fold_results` / `aggregate_to_summary` (旧)
- sample parquet 実機 verify: blacklist drop 64 ✅ / label drop 56 ✅ / X (25345, 2604) ✅ / 3 fold 生成 (sample 上限) + Purging gap (1h) 確認

### 1.2 Phase 1 v5.1 設計確定 + Step A-C 完了 (commit `eff0aff`)

まこさん指摘で 3 ファイル (`learning_design_v4` / `phase_flow_v4_with_recovery` / `technical_analysis_knowledge_base`) を Read 後、Phase 1 v5 → v5.1 厳格化が確定:

#### Q1: Entry 閾値 1.5 の根拠

- **CC 早計自己申告訂正**: 1.5 は CC 独断値ではなく `phase_flow_v4_with_recovery.md` L151「予測 MFE / 予測 MAE ≥ 1.5 で買う・改善期待しない・比較用ベースライン」と明示
- 本確定は **Phase 4-b-2** (phase_flow_v4 L528「3 方式並列」: 固定 / cluster 別 quantile / rolling 365 日 q90/q95/q99)
- **TP first 正解全案統一**: `triple_barrier_label_{LONG,SHORT}_K{K}` == +1 (Phase 0 v3.1 生成済)
- §I.6.3 整合: Phase 1 = feature_importance 評価 / Phase 4-b = DSR + walk-forward 閾値最適化

#### Q2: train/valid 乖離 warning 追加

- W1: `train_rmse / label_std < 0.10` → leak 疑い (L-179 fractal leak 教訓補完)
- W2: `valid_rmse > train_rmse × 3.0` → overfit/leak 疑い
- 倍率 3.0 採用 (1.5 は regression false positive 多発・3.0 は明らかな leak のみ検出)
- top50 blacklist は phase_compliance §1.4 既定済・構造系 1 個ずつ照合は L-179 修正後不要

#### Q3: 評価単位 8 組合せ厳格化

- K=12 LONG 単独 → **K=12/24/48/96 × LONG/SHORT = 8 組合せ** (cc_ml_design_spec §1.6 撤退ライン同構造)
- **合格判定**: 6 案いずれか × **6+ 組合せで 5 指標 ALL PASS**
- 「K=12 LONG 1 組合せだけ合格扱い」禁止 (Phase 5 8 組合せ Replay の全月 $1,900 クリア要件と整合)
- 計算負荷: 20h → **28-30h** (3 並列で 10-13h)・260 学習想定 (旧 30 学習を 1.5-2x 化)

#### 修正 3 ファイル

| ファイル | 変更 |
|---|---|
| `cc_ml_design_spec.md` §1.5.1 | v5.1 (8 組合せ + 6+ 合格 + TP first 正解統一・§1.6.1 メタルール例外承認内) |
| Phase 1 v5 指示書 §2-§5 | 全面修正 (16/8 model × 5 fold = 260 学習・1.5 = phase_flow_v4 既定明示・W1/W2 警告追加・8 組合せ評価) |
| CLAUDE.md L142/146/147 | パス hardcode 不整合修正 (`bitget-python-sdk-api/` 直下 → `.claude/memory/` 配下) + CSV ファイル名訂正 (`__一覧` → ` - 一覧`) |

### 1.3 Step D 完了 (commit `06dd10d`・runner v5.1 拡張・+244 行)

- `run_phase1_v5_purged_kfold.py` 529 → 773 行
- 定数追加: `K_DEFAULT_LIST = (12,24,48,96)` / `SIDES_DEFAULT = ("LONG","SHORT")` / `COMBINATION_PASS_COUNT_REQUIRED = 6`
- 定数追加: `WARN_TRAIN_RMSE_LABEL_STD_RATIO = 0.10` / `WARN_VALID_TRAIN_RATIO = 3.0`
- `FoldMetrics` 拡張: `side` / `train_rmse` / `valid_rmse` / `label_std` / `warnings: List[str]`
- `CombinationSummary` dataclass 新規 (1 組合せ K × side 5 fold 統合 + DSR + pass 判定)
- `CaseSummary` 全面再設計 (8 組合せ統合 + 6+ ALL PASS 判定 + `meets_6plus_criteria`)
- `compute_fold_metrics` 拡張: `y_true_tp_first` / `y_pred_tp_first` 引数 (caller 責務で 0/1 化済) + `direction_y_true/pred` 別 array (案 c のみ) + W1/W2 警告検出
- `aggregate_combination_to_summary` + `aggregate_8_combinations_to_summary` 新規 (旧 `aggregate_to_summary` 廃止)
- `_self_check` v5.1 拡張: timeseriescv split / compute_fold_metrics / W1/W2 警告 (両方 trigger 確認) / 2 組合せ aggregate (n_all_pass=0 / meets_6plus=False) 全 PASS

### 1.4 lessons L-205 新規 + L-204 拡張

- **L-205**: ドキュメント引用前 実装 verify 漏れ + 早計自己申告 — L-180 同型再演 (2026-05-22)
  - 1.5 を CC 独断値と即時自己申告したが phase_flow_v4 L151 既定値だった
  - 対策: 設計閾値根拠 verify は最低 3 ファイル grep 義務化 (cc_ml_design_spec + phase_flow_v4 + technical_analysis_knowledge_base)
- **L-204 拡張**: CLAUDE.md L142/146/147 Layer 2 パス hardcode 不整合事案を追加 (handoff バージョン hardcode と同型「文書間参照リンク切れ」)

---

## §2 自己申告 (cc_role §1.3.4 義務)

### 2.1 L-205 同型 早計自己申告

Q1「Entry 閾値 1.5 の根拠」に対し cc_ml_design_spec §2 のみ確認で「CC 独断値・修正必要」と即時自己申告。まこさん指示で 3 ファイル Read 後 phase_flow_v4 L151 既定値と判明・訂正報告。**cc_role §1.3.4 発見時自己申告義務 ↔ 早計自己申告防止の両立が必要**。今後は 3 ファイル grep 後に発動する。

### 2.2 L-204 拡張 CLAUDE.md パス hardcode 不整合

L142/146/147 で 3 件のパス hardcode 不整合 (実体 `.claude/memory/` 配下を `bitget-python-sdk-api/` 直下と誤記 + CSV ファイル名 `__一覧` を ` - 一覧` と誤記)。本セッションで修正済 (commit `eff0aff`) だが、handoff v24 で改訂22 にて hardcode 撤廃宣言したのに **同型残存**を発見できなかった構造的問題。L-181「設計転換時 旧記述 全 grep sweep」命令の繰り返し違反 (handoff バージョン 1 件 + パス hardcode 3 件 = 4 件)。

### 2.3 まこさんの 3 ファイル指示で初めて気付いた

両件とも本セッション中盤でまこさん「念のため learning_design_v4 / phase_flow_v4_with_recovery / technical_analysis_knowledge_base を読んでみて」指示まで CC は構造的違反を自覚できなかった。**Step 0 セルフチェック (Layer 2 必読 3 ファイル grep) が形式的・実質的に守れていなかった実証**。

---

## §3 次セッション CC 優先順位 (Step E 着手)

### §3.1 優先 1 — Step E: 案 a 実装 (約 1-2 日)

`scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py` 新規 (約 320-380 行)。

```
[Step E.1] 着手前 verify (新セッション Step 0 直後・1 度のみ)
  - parquet K 値抽出 (LONG_MFE_pct_K{X} の K=12/24/48/96 確認)
  - LightGBM LGBMRegressor API 署名 verify
  - runner v5.1 import smoke (case_a 用関数 access 確認)

[Step E.2] 実装本体 (約 320-380 行)
  - 公開 API: `train_case_a(parquet_path, k_values, smoke_mode, n_estimators, out_base)`
  - 内部 loop: 16 model (LONG/SHORT × MFE/MAE × K={12,24,48,96}) × 5 fold = 80 学習
  - LightGBM hyperparams: num_leaves=31 / lr=0.05 / n_estimators=1000 / early_stopping_rounds=50 / random_state=42 / n_jobs=-1
  - 各 fold で:
    - train/valid split (Purged K-Fold が tr/te 出力 → 末尾 10% を valid に分離)
    - 16 model 学習 (LightGBM Regressor)
    - train_rmse / valid_rmse / label_std 算出
    - 各 K × side について MFE/MAE pair で予測 → MFE/|MAE| 比 ≥ 1.5 で TP first 0/1 化
    - triple_barrier_label_{LONG,SHORT}_K{K} == +1 で正解 0/1 化
    - returns_per_trade = predicted_MFE/100 (TP first 予測 trade のみ)
    - runner v5.1 `compute_fold_metrics(... y_true_tp_first, y_pred_tp_first, train_rmse, valid_rmse, label_std ...)` 呼び出し
  - 1 ラベル目 (K=12 LONG_MFE) 学習完了直後に feature_importance top20 review
    - phase_compliance_checklist §1.4 ガード: top1-20 hit (fractal/level/fib 系) → sys.exit(1)
  - 8 組合せ aggregate: `aggregate_8_combinations_to_summary(case_name="a_rmse", combination_results, n_trials=6)`
  - case_summary.meets_6plus_criteria で合格判定

[Step E.3] CLI (argparse)
  - `--smoke`: Fold 0 + K=12 LONG のみ (2 model 学習・約 30-60 分・1-2 ヶ月の sample parquet)
  - `--full`: 全 5 fold × 16 model = 80 学習 (実 parquet train_2021_2024.parquet・約 5-6 時間)

[Step E.4] syntax check + smoke 実行 (Step F に直結)
```

### §3.2 優先 2 — Step F: smoke test (約 1-2 時間)

- Fold 0 + K=12 LONG のみで動作確認
- メモリ消費実測 (1 model あたり 10-15 GB 想定・full では 3 並列 = 30-45 GB)
- runner v5.1 と case_a の連携動作確認
- W1/W2 警告ログが正しく出るか確認 (smoke では出ない想定だが構造 verify)

### §3.3 優先 3 — Step G: CP2 監査依頼 (`/audit` 経由・7 項目・指示書 §9)

監査対象:
- Phase 1 v5.1 設計 (8 組合せ + TP first 正解統一 + 6+ 合格判定)
- Purged K-Fold 5 fold の Embargo 設定妥当性 (K=12 vertical barrier との整合)
- DSR 計算の selection bias 補正妥当性 (n_trials=6・Phase 4-b-2 で grid 拡張時の追加方針)
- 6 案間比較公平性 (triple_barrier_label 正解統一 + 同じ Purged K-Fold split)
- case_a smoke 結果

### §3.4 優先 4 — Step H: full 8 組合せ実行 (約 28-30 時間)

CP2 OK 後・3 並列で 10-13 時間。

### §3.5 その後 — 案 b-f 順次実装 → §4.1 採用判定 or Layer 3 投入

- 案 b (binary K={12,24,48,96} × LONG/SHORT = 8 model × 5 fold = 40 学習)
- 案 c (multiclass K={12,24,48,96} × 1 model = 4 × 5 fold = 20 学習)
- 案 d (lambdarank K={12,24,48,96} × LONG/SHORT = 8 × 5 = 40)
- 案 e (Triple Barrier multiclass K={12,24,48,96} × LONG/SHORT = 8 × 5 = 40)
- 案 f (Meta-Labeling・案 e 後 sequential = 8 × 5 = 40)
- 6 案合計 260 学習 → §4.1 採用判定 (6+ 組合せ ALL PASS) or Layer 3 投入

---

## §4 引き継ぎリソース (新セッション Step 0 で必読・3 層構造)

### Layer 1 (毎セッション必読)

- **本ファイル** `handoff_to_cc_v25_session_20260522.md` (最新版・find で取得)
- `WORKFLOW.md` 改訂23 active ブロック (Step E 着手準備反映)
- `CLAUDE.md` (Layer 2 パス hardcode 修正済・改訂22 ベース)
- `lessons_active.md` 直近 5 件 (**L-205 最新** + L-204 拡張 + L-203 / L-202 / L-201)

### Layer 2 (Step E 着手時)

- **Phase 1 v5 指示書 v5.1** (`.claude/instructions/2026-05-22_phase1_layer_inversion_instruction.md`・約 510 行・8 組合せ + W1/W2 + 260 学習版・commit `eff0aff`)
- **cc_ml_design_spec.md §1.5.1 v5.1** (commit `eff0aff`)
- **learning_design_v4.md** (377 行・v5 化済・Layer 1 タスク確定リスト)
- **`.claude/memory/phase_flow_v4_with_recovery.md`** (977 行・L151 案 a 1.5 明示 / L528 Phase 4-b-2 本確定)
- **`.claude/memory/technical_analysis_knowledge_base.md`** §I 閾値設計論 (4 大分類 + §I.6.3 Phase 別データ駆動再検討フロー)
- **runner v5.1** (`scripts/priority_rebuild/run_phase1_v5_purged_kfold.py`・773 行・commit `06dd10d`)
- **dsr.py + test_dsr.py** (`scripts/priority_rebuild/`・commit `5918456`)
- **phase_compliance_checklist.md §Phase -1 / §1.1-1.5** (blacklist 64 列 / Phase 1 着手前 checklist)
- **feedback_ml_leak_mandatory_check.md** (`~/.claude/projects/.../memory/`)
- **leak_incident_20260513.md** (`results/priority_rebuild/`・L-179 全 14 件ミス記録)

### データ・環境

- **parquet 3 種** (`results/priority_rebuild/labels_mfe_mae_pct_{train_2021_2024,test_2025,test_2026_q1}.parquet`)
- **.venv311 環境** (Step C 完了・mlfinpy 0.1.2 + timeseriescv 0.2 + scikit-learn 1.8.0 + lightgbm 4.6.0 + scipy 1.17.1 + numpy 1.26.4 + pandas 2.3.3)

---

## §5 CC 同型バイアス警戒 (累積 43+ 件)

handoff v24 §5 累積 41 件 + 本セッション 2 件 (早計自己申告・CLAUDE.md パス hardcode 不整合見落とし) = **累積 43+ 件**。

### 次セッション CC への命令

- **本ブロックを Step 0 で最優先警戒**
- L-205: 設計閾値・パラメータの根拠 verify は最低 3 ファイル grep (cc_ml_design_spec + phase_flow_v4 + technical_analysis_knowledge_base) 義務化・1 ファイルだけで「矛盾あり」と早計自己申告しない
- L-204: system reminder で auto-load されているファイルも Read tool で取り直す + CLAUDE.md Layer 2 パスは実体確認
- L-200: 「読んだ」「verify した」「監査済」「総点検した」と書く時は同ターン内に機械的証跡 (`wc -l` + Read 全文 + 該当行引用) を必ず出す
- L-201 / L-203: 外部ライブラリ / 業界知識を引用する前に WebSearch + WebFetch で実態 verify
- cc_role §1.5: 戦略本丸以外は CC が判断・断言・実行 (確認質問乱発禁止)
- core_rules §MUST: コード変更前に差分提示 → GO 待ち・1 ターン 1 変更・bitget_keys.json 警告

---

## §6 本テスト Q1 (2026 Q1) 到達まで

```
[現在] Step 2/A-C/D 完了 + Step E (case_a) 着手準備
    ↓ (Step E 案 a・1-2 日)
[Step F smoke test (1-2 時間)]
    ↓
[Step G CP2 監査] (`/audit` 経由・7 項目)
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

## §7 メタ反省 (handoff v25 起案 CC からの記録)

本セッションで L-205 が新規発火 (ドキュメント引用前 verify 漏れ + 早計自己申告)・L-204 が拡張 (CLAUDE.md Layer 2 パス hardcode 不整合)。L-180 (2026-05-13) から 9 日後、L-181 (2026-05-13) から 9 日後の同型再演。「ルール追加だけでは効かない」実証ループは累積 5 件目 (L-201 / L-202 / L-203 / L-204 / L-205)。

ただし**本セッションの建設的成果**:
- まこさんが「3 ファイル読んでみて」指示で **3 ファイル grep + Read** を発動 → phase_flow_v4 L151 既定値発見 → CC 早計自己申告訂正 → Phase 1 v5.1 設計改善 (8 組合せ厳格化)
- まこさん指摘 + 3 ファイル参照経由で CLAUDE.md パス hardcode 不整合 3 件発覚 → 即修正
- v5.1 厳格化により Phase 5 8 組合せ Replay 整合性が Phase 1 で先取り検証可能に (目標達成への前進)

**唯一効くのは構造変更 + まこさん監視 + 監査経路の併用**:
- ファイルを物理的に減らす (archive 移送・3 層構造化) — handoff v24 で実施
- hardcode を撤廃する (find で動的取得) — handoff v24 で実施・本セッションで Layer 2 パス hardcode 追加修正
- 機械的証跡を物理的に出さないと次に進めない関所 (web_claude_self_check 読了ゲート)
- まこさんが「3 ファイル読んで」と具体指示 — 本セッションで効力発揮 (CC が forget するファイルを思い出させる)

次セッション CC は本ブロックを Step 0 で必ず読み、「ルールに書いてあるから守れる」と思わず、3 ファイル grep + 機械的証跡 + まこさん監視併用で違反を物理的に起こせなくする方向で動くこと。

---

以上。
