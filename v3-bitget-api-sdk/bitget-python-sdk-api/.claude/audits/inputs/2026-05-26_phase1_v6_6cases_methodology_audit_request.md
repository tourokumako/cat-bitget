# 【監査依頼】Phase 1 v6 — 6 案実施 (5 完走 + 1 smoke) 方法論監査

依頼日: 2026-05-26
依頼者: CC (cc_role.md v1・ML 設計担当兼務)
監査区分: **方法論監査 (CP6 想定・別 Claude Code セッション起動・cc_role §1.4.5 改善 9)**
監査依頼の経緯:
1. 案 f smoke 完了直後にまこさん指摘 1「6 案完了が目的ではなく目標 (月次 NET ≥ $1,900) 達成手段として適切か」
2. CC が「現時点で目標達成可能性監査」と書いた初版を まこさん指摘 2 で却下「Phase 1 段階で目標可能性判定すべきでない・Exit ML (Phase 4-b) 後の話」
3. 監査スコープを **Phase 1 v6 設計フロー通りに実施されたかの方法論監査** に再定義
4. まこさん追加要請: 不正チェック + 23 軸考慮 + 学習方法チェック + 外部検索による業界知見取得

## 構造化ルール準拠

- 保存先 (本依頼書): `.claude/audits/inputs/2026-05-26_phase1_v6_6cases_methodology_audit_request.md`
- 結果ファイル保存先: `.claude/audits/2026-05-26_phase1_v6_6cases_methodology_audit_report.md`
- 別 Claude Code セッションで Plan サブエージェント起動 (= 同型バイアス回避)
- メインセッション内 `/audit` 起動禁止

## 着手前必読 (省略禁止・auditor 用)

1. `cc_role.md` §1.0 (目標) / §1.4 (構造的バイアス) / §1.4.6 (目的整合性ゲート・L-215) / §1.5 (デザイン責任) / §1.6 (23 軸の存在理由)
2. `CLAUDE.md` §目標 (月次 NET ≥ $1,900 全月クリア・Phase 5 で判定・Phase 1 では未測定)
3. `phase_flow_v4_with_recovery.md` §2 Phase 1 (6 案並列の根拠・L146-326) / §1 用語集 / §5.4 CP2 監査内容
4. `cc_ml_design_spec.md` §1.5.1 Phase 1 合格基準 (L83-107) / §1.6 撤退ライン
5. `archive/learning_design_v4_20260526.md` (6 案並列確定経緯・本書は phase_flow_v4 v5/v6 統合前の原本)
6. `lessons_active.md` L-217 (Phase 1 評価軸 Exit 非依存 3 指標化) / L-215 (5 セッション設計逸脱) / L-216 (handoff 廃止) / L-179 (fractal leak 教訓)
7. `false_positive_incident_policy.md` §0-1 Prime Directive / §0-2 ポジション上限 / §2 類型 A-H / §5 関所 A-G
8. `phase_compliance_checklist.md` §Phase -1 (USD 絶対値 blacklist 64 列) / §Phase 1 (verify 義務 1.1-1.6)
9. `auditor_template.md` 全文 (監査観点 ①〜⑦ + Step -1/0)
10. `technical_analysis_knowledge_base.md` (本プロジェクト製テクニカル辞典・1691 行・§A-D 個別 + §I 閾値設計論)
11. `CAT−指標マトリックス - 一覧.csv` (23 軸構成要素カタログ + 各軸絞り込み戦略・1962 行)

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ **本監査スコープ** = **Phase 1 v6 内に限定**。目標達成可能性判定は対象外 (Phase 4-b + Phase 5 完了後の別監査)。

## 監査対象の事実データ

### 6 案実施記録 (2026-05-22 確定 → 2026-05-26 案 b/c/d/e 完走・案 f smoke のみ)

| 案 | 実装ファイル | 行数 | 学習方法 | 主指標 | 実施 |
|---|---|---|---|---|---|
| a (比較用) | `run_lgbm_phase1_v5_case_a_v2_v3.py` | 629 | 14 ラベル独立 RMSE | Simulated PnL | 完走済 (過去 Step F-I・5 セッション) |
| b (Entry Binary) | `run_lgbm_phase1_v5_case_b_binary.py` | 501 | binary objective + entry_label=`MFE>=|MAE|` | entropy_lift + tp_precision | **完走** (本セッション) |
| c (Direction Multiclass) | `run_lgbm_phase1_v5_case_c_multiclass.py` | 660 | multiclass num_class=3 (LONG/SHORT/Flat) + label `MFE>0.5%` (smoke v1 で fix) | + Direction Accuracy | **完走** (本セッション) |
| d (Ranking LambdaRank) | `run_lgbm_phase1_v5_case_d_lambdarank.py` | 547 | lambdarank objective + 日次グループ (smoke v1 で 10000 row limit 回避修正) + label `qcut(MFE,q=5)` | tp_precision @ top 10% | **完走** (本セッション) |
| e (Triple Barrier multiclass) | `run_lgbm_phase1_v5_case_e_triple_barrier.py` | 525 | multiclass num_class=3 (SL/TIME/TP) + label `triple_barrier_label_{side}_K{K}` (Phase 0 v3.1 生成済 14 列) | entropy_lift + tp_precision | **完走** (本セッション) |
| f (Meta-Labeling 2 段階) | `run_lgbm_phase1_v5_case_f_meta_labeling.py` | 672 | Primary (案 e) + Secondary binary (label `meta_label_{side}_K{K}`・Phase 0 v3.1 生成済 14 列) | final_tp_precision (lift) | **smoke のみ**・full 未実行 |

全案共通設定:
- データ: train_2021_2024.parquet (394,561 行 × 2,724 列・blacklist 64 列 + label 56 列 drop 後 X=2,604 列)
- LightGBM ハイパラ: num_leaves=31 / max_depth=-1 / learning_rate=0.05 / n_estimators=1000 / early_stopping=50 / random_state=42
- Walk-forward Purged K-Fold: timeseriescv.PurgedWalkForwardCV (n_splits=5 + n_test_splits=1 + min_train_splits=2 → 実 3 test fold)
- 末尾 10% を valid (early stopping 用・train_inner と分離)

### 5 案結果サマリー (full・8 組合せ × 3 fold)

| 案 | entropy_lift mean | entropy_lift PASS (> 0.10) | TP Precision best | TP PASS (> 0.5) | pass_all (3 指標) |
|---|---|---|---|---|---|
| a (Step F-I) | ~0.06 | 0/8 | (未測定) | — | 0/8 |
| b (Binary) | -0.003 | 0/8 | 0.43 (K=48 LONG) | 0/8 | 0/8 |
| c (Multiclass) | 0.084 | 4/8 (K=12/24 のみ) | 0.43 (K=96 LONG) | 0/8 | 0/8 |
| d (LambdaRank) | N/A (確率非変換) | — | 0.42-0.44 (K=96・top 1%) | 0/8 | 0/8 |
| **e (Triple Barrier)** | **0.234** | **6/8 ★最良** | 0.44 (K=96 LONG) | 0/8 | 0/8 |
| f (smoke only) | (K12 LONG only・lift ≈ 0) | — | 0.33 | — | — |

結果ファイル (各 case directory 配下):
- `results/priority_rebuild/ml_phase1_v5/_case_b_binary/case_b_binary_summary_labels_mfe_mae_pct_train_2021_2024.json`
- `results/priority_rebuild/ml_phase1_v5/_case_c_multiclass/case_c_multiclass_summary_labels_mfe_mae_pct_train_2021_2024.json`
- `results/priority_rebuild/ml_phase1_v5/_case_d_lambdarank/case_d_lambdarank_summary_labels_mfe_mae_pct_train_2021_2024.json`
- `results/priority_rebuild/ml_phase1_v5/_case_e_triple_barrier/case_e_triple_barrier_summary_labels_mfe_mae_pct_train_2021_2024.json`
- `results/priority_rebuild/ml_phase1_v5/_case_f_meta_labeling/case_f_meta_labeling_summary_labels_mfe_mae_pct_sample.json` (smoke のみ)

### 本セッションでの CC の挙動 (自己申告)

1. 案 b 着手前に cc_role §1.4.6 目的整合性ゲート 5 項目を書き出した (1 回のみ・案 c/d/e/f 着手前は書き忘れ)
2. 案 b/c/d/e 完走時に 5 案累積結果から「方法論健全性」の中間判断ゲートを設けなかった
3. 案 c smoke v1 で Flat=0% + column index swap bug 発生 → 修正後再走 (label 定義を CC 独自比率基準 → spec L194 通り `MFE > 0.5%` に変更)
4. 案 d smoke v1 で 10000 row/query hard limit エラー → 日次グループ修正
5. 案 d smoke v2 を **GO 待ちなし**で起動 (process 違反・自己申告済)
6. 案 f smoke で Secondary が primary in-sample overfit に乗って形骸化 (precision_lift ≈ 0)
7. まこさん指摘で「6 案 sweep 完了が目的化」を自己発見 (L-215 同型再演)

## 監査スコープ (Phase 1 内に明示限定)

### 監査対象 (Phase 1 v6 内の方法論)
- 6 案実装が `learning_design_v4 (archive)` + `phase_flow_v4 §2` 設計フロー通りに行われたか
- 各案の実装方法論は業界基準 (Lopez de Prado AFML / Stefan Jansen MLfAT 等) 整合か
- 不正チェック (未来参照 leak / 計算式 / 絶対値 / ポジション上限)
- 23 軸考慮 (B-15 目的関数軸の網羅性・他軸との関係)
- 学習方法 (Purged K-Fold / valid split / ハイパラ / encoding 選択)
- CC のプロセス欠陥構造的防止策

### 監査対象外 (現時点で判定不可能)
- 月次 NET ≥ $1,900 達成可能性 → Phase 4-b (Exit ML) + Phase 5 (Replay) 完了後の別監査
- Layer 3 投入の本判断 → Phase 1 内の TP Precision 天井のみでは判定不能
- Phase 2 以降のハイパラ最適化効果

## 監査観点 (一般・auditor_template ①〜⑦)

- ①統計学的妥当性 (5 案結果の TP Precision 天井 ~0.45 は真の限界か・過学習由来か・正規化由来か)
- ②リスク管理 (Phase 1 評価式に position sizing 漏れていないか・将来 Phase 5 接続時の整合性)
- ③認知バイアス (CC の「6 案 sweep 完了」自己目的化・spec の枠内バイアス)
- ④ソフトウェア工学 (案 b/c/d/e/f 実装品質・edge case handling・bug pattern)
- ⑤再現性 (random_state 統一・データ snooping ゼロ・artifact "test" 文字列禁止)
- ⑥実行プロセス (中間判断ゲート欠落・PM 視点累積結果検算なし)
- ⑦主エージェントバイアス (CC が L-215 同型を再演した構造)

## 監査観点 (本監査固有・8 項目)

**Q1 — Phase 1 v6 設計フロー整合性**:
phase_flow_v4 §2 (L146-326) + learning_design_v4 (archive) で「6 案並列 + Walk-forward Purged K-Fold 5 fold + 3 指標 Exit 非依存」が確定。5 案実施は設計通りか? smoke v1 修正 (案 c label / 案 d group) は spec から逸脱していないか?

**Q2 — 各案の実装方法論の業界基準整合性**:
- 案 b (binary + entry_label `MFE>=|MAE|`): class imbalance が ~50/50 で scale_pos_weight ≈ 1 = spec L195「50:1〜100:1 想定」と乖離。CC が独自 label 定義した判断は業界基準で正当か?
- 案 c (multiclass LONG/SHORT/Flat + label `MFE>0.5%`): K-invariant 固定閾値で K=96 で Flat 比率激減 (0.5% > 8h MFE が稀)。spec L194 通りだが K 別調整なしの設計は妥当か?
- 案 d (lambdarank + 日次グループ): LightGBM 10000 row/query hard limit 回避で日次グループ採用 (288 bar/group)。「ランキング上位 N%」spec L170 を「日内ランキング上位 N%」と解釈変更したが、業界基準で妥当か?
- 案 e (Triple Barrier multiclass): Phase 0 v3.1 で pre-built triple_barrier_label を直接 1 model = 8 (K, side) × 3 fold で学習。AFML Ch.3 推奨形式整合か?
- 案 f (Meta-Labeling): Primary 案 e を full train で fit + 同 train で in-sample predict → secondary 学習 → in-sample overfit で secondary 形骸化。AFML Ch.3 の Meta-Labeling 推奨は cross-validated primary predictions のはずだが、簡素版で評価した本実装は方法論的に欠陥か?

**Q3 — 評価指標算出式の正当性**:
- entropy_lift = `1 - logloss / log(num_classes)` (run_phase1_v5_purged_kfold.py L264-290): num_classes は実 unique class 数 (case c で Flat 欠落時 2)・case e で K=96 TIME=0.05% 時 2 となる可能性。この動的調整は業界基準整合か?
- TP Precision = `(pred_entry & (triple_barrier_label == +1)).sum() / pred_entry.sum()`: 案 b/c は外部 ground truth (triple_barrier) vs case e は学習 label = 同じ列 = 自己評価。混在は妥当か?
- 案 d top N% precision = `(score > quantile(score, 1 - N%)).sum() で TB == +1 率`: top 10% を主指標化したが、業界 ranking 評価 (NDCG / MAP) との関係は?

**Q4 — 案 e (entropy_lift 6/8 PASS ★最良) を Phase 2 ハイパラ最適化に進めて良いか? (Phase 1 内判断)**:
- 案 e の K=24/48/96 で entropy_lift 0.20-0.35 = 信号抽出確認
- ただし TP Precision 0.44 が頭打ち = predictive value 不足
- spec L96「6 案いずれか × 8 組合せで 6+ 組合せ 3 指標 ALL PASS」未達 → spec L98「即 Layer 3 投入」
- spec 厳格適用判定 vs 案 e 採用で Phase 2 進行判定はどちらが業界基準整合か? (Phase 4-b/5 未完で Phase 2 進行可否判定なので Phase 1 内に閉じる)

**Q5 — CC のプロセス欠陥構造的防止策**:
- cc_role §1.4.6 目的整合性ゲート (L-215 対策) は「セッション開始時 + 新タスク着手前」と明文化されているが、本セッションで CC は **5 回連続で書き忘れた** (案 b/c/d/e/f 着手時)
- 形式チェック (= 書き出し義務) では止まらない構造的欠陥か?
- 業界 / 認知科学的に「タスク階層化による大目的喪失」を防ぐ追加メカニズムは何か? (cc_role §1.4.6 改訂提案)

**Q6 — 不正チェック (4 項目・false_positive_incident_policy 整合)**:

**Q6.1 未来参照 leak (類型 A・§0-1 Prime Directive)**:
案 b/c/d/e/f 全 6 case の特徴量・ラベル・評価式で `.shift(-N)` / `j+1, j+2` / `center=True` / 期間全体集計 / test 期間結果使用 が混入していないか grep verify + 算出式列挙。
特に:
- 案 b: `entry_label = (MFE >= |MAE|).astype(int)` の MFE/MAE は Phase 0 で生成 = 未来 K bar の集計値だが、ラベルなので合法 (推論時の X に含めない)・ただし学習スクリプトが y を X に流入させていないか
- 案 c/d: 同様 (MFE_pct を y に使用)
- 案 e: triple_barrier_label を y に使用 (Phase 0 v3.1 生成・確認: build_labels_pct.py L219-220 の `.shift(-N)` はラベル側で合法)
- 案 f: meta_label を y に使用 (同上)

**Q6.2 計算方法 (類型 E・関所 C NET 実体 verify)**:
- entropy_lift / TP precision / direction accuracy / NDCG@10 算出式が業界標準か (sklearn 等の reference 実装と一致か)
- _safe_logloss / _safe_logloss_multiclass の clip(eps=1e-15) は妥当か (under/overflow リスク)
- 案 d の qcut(q=5) で同値多発時 `duplicates='drop'` で bin 数減少する仕様は妥当か
- 案 f の Secondary の scale_pos_weight = neg/max(pos,1) で max(...,1) ガードは妥当か

**Q6.3 絶対値 (Phase -1 blacklist 64 列・USD 絶対値特徴量)**:
- load_parquet_with_blacklist で 8 family × 8 TF = 64 列を drop しているか (実測 confirm)
- feature_importance top20 に sma_20 / sma_50 / ichimoku_kijun / ichimoku_tenkan / macd_line / macd_signal / macd_hist / macd_hist_change のいずれかが混入していないか (各案の fi_top20 csv 確認)
- pct 化追加 30 列 (close_vs_tenkan_pct / macd_line_pct 等) が正しく追加されているか

**Q6.4 ポジション上限 0.12 BTC 合計厳守 (類型 H・§0-2)**:
- Phase 1 v6 は entry signal 学習のみで Simulated PnL を Phase 5 に移動済 (L-217)
- 案 b/c/d/e/f の評価式に position sizing が混入していないか (本来 Phase 4-b/5 領域)
- 案 a (Step F-I) の Simulated PnL 評価式 `compute_simulated_pnl_v2` で `position_size_btc=0.024 / btc_price_avg=50000` を使用 = 0.12 BTC 合計上限を 1 ポジ 0.024 BTC × cap_5 想定の暫定値。これは Phase 1 v6 では Phase 5 へ移動済なので案 b/c/d/e/f には影響しないが、案 a 既存 artifact との比較解釈時に注意

**Q7 — 学習項目が 23 軸を考慮しているか**:

23 軸 (CAT_指標マトリックス__一覧.csv) の構造:
- カテゴリ I シグナル定義: A-1 (Entry 指標) / A-2 (Exit 指標) / A-3 (パラメータ)
- カテゴリ II 時間設計: A-4 (K) / A-5 (TF) / D-α (発火頻度)
- カテゴリ III ポジション設計: A-6 (MAX_ADDS) / A-7 (サイズ) / B-8 (cap) / D-ζ (マルチサイド)
- カテゴリ IV フィルタ: D-γ (位置) / D-δ (時間帯) / D-ε (regime)
- カテゴリ V 学習設計: **B-9 (組合せ深さ) / B-10 (アルゴ) / B-11 (cluster) / B-12 (特徴量変換) / B-13 (Entry 閾値) / B-14 (データ範囲) / B-15 (目的関数)**
- カテゴリ VI 執行設計: D-η (手数料) / D-θ (発注タイプ)

Q7.1 — 6 案 (案 a regression / 案 b binary / 案 c multiclass / 案 d ranking / 案 e TB multiclass / 案 f meta-labeling) は **B-15 (目的関数)** 軸の探索。これは B-15 を網羅的にカバーしたか? AFML / Stefan Jansen で他に Phase 1 で取り得る objective (例: quantile regression / Bayesian classification / ordinal regression / cost-sensitive learning) を見落としていないか?

Q7.2 — Phase 1 では他軸 (A-1 / A-3 / A-5 / B-9 / B-10 / B-11 / B-12 / B-13) が並列扱われず Phase 順送り (Phase 2 = B-9 / Phase 3-a = B-10 / Phase 3-b = B-11 / Phase 0 改修済 = B-12 / Phase 4-b-2 = B-13)。Phase 1 で B-15 だけ並列 6 案 = TP Precision 0.45 天井 = 「他軸を Phase 1 で並列実装しないと信号抽出限界が見えない」という業界批判は成り立つか?

Q7.3 — Phase 0 改修済 (1,432 指標 → 2,604 列・B-12 Fractional / PCA / MTF 拡張済) で TP Precision 0.45 天井 = **特徴量の predictive power 限界** vs **目的関数選定限界** どちらが支配的か業界基準で診断せよ。

**Q8 — 学習方法のチェック (業界標準整合)**:

Q8.1 — Walk-forward Purged K-Fold: `timeseriescv.PurgedWalkForwardCV(n_splits=5, n_test_splits=1, min_train_splits=2)` で実 3 test fold。Lopez de Prado AFML Ch.7 推奨 (CPCV vs Walk-forward) 整合か? n_splits=5 は十分か?

Q8.2 — 末尾 10% を valid 切り出し (early stopping 用): time-series で末尾 10% を valid に使う方式は標準だが、Purged K-Fold 内部で valid 切るのが本来正しいのではないか? (現実装は train_inner = train - 末尾 10%・valid = 末尾 10%・test = 別 fold)

Q8.3 — LightGBM ハイパラ: num_leaves=31 / max_depth=-1 / learning_rate=0.05 / n_estimators=1000 / early_stopping=50 / random_state=42 / feature_fraction=0.9 / bagging_fraction=0.9 / bagging_freq=5 / min_child_samples=20。デフォルト寄りだが過学習防止に適切か? K=48/96 で train_ll/test_ll 乖離 (案 c K=96: 0.27 vs 1.78) は過学習サイン・early_stopping が機能していない可能性。

Q8.4 — class encoding 選択: 案 e `{-1, 0, +1} → {0, 1, 2}` (SL=0/TIME=1/TP=2) で 0-indexed 整数。`class_to_col = {int(c): i for i, c in enumerate(model.classes_)}` で動的解決 (案 c smoke v1 fix)。業界標準整合か?

Q8.5 — 評価式構造: TP Precision = `(pred_entry & TB==+1).sum() / pred_entry.sum()`。threshold (proba > 0.5 案 b / > 0.4 案 c/e / > 0.4 + 0.6 案 f / top N% 案 d) の選定は spec L86 通りだが、業界標準 (例: ROC AUC / PR AUC) との関係は?

## 外部検索要請 (本監査の必須要件・新規追加)

`technical_analysis_knowledge_base.md` (本プロジェクト製テクニカル辞典・1691 行) だけでは内部知識に閉じる。auditor は以下の **外部検索を必ず実施** すること:

### 検索対象 (例・auditor は適宜拡張)

1. **BTC futures 5m bar Entry signal ML の業界相場**:
   - 「BTC/USDT 5min bar LightGBM Entry signal TP precision benchmark」
   - 「Crypto futures algo trading 5-minute Entry classifier accuracy」
   - 業界相場として TP precision 0.45 は天井か・もっと出るはずか の外部判定
2. **Lopez de Prado AFML Ch.3 Meta-Labeling 推奨実装**:
   - cross-validated primary predictions vs in-sample predictions の業界推奨
   - 案 f smoke で発覚した primary in-sample overfit → secondary 形骸化は AFML 既知問題か
3. **Phase 1 (Entry AI) と Phase 4-b (Exit ML) を階層分離する業界アプローチ**:
   - cc_ml_design_spec §1.5.1 L102-105「Phase 別評価軸の階層分離」が業界標準か
   - L-217 (Exit 非依存 3 指標化) 改訂が業界標準整合か
4. **23 軸並列実装 vs Phase 順送り** の業界比較:
   - 6 案 (B-15) を Phase 1 で並列実装するアプローチは AutoML / NAS (Neural Architecture Search) 文脈で標準か
   - 他軸 (A-1 特徴量 / B-10 アルゴ / B-12 特徴量変換) を Phase 1 で並列せず Phase 順送り設計は業界標準か
5. **Walk-forward Purged K-Fold (n_splits=5) vs CPCV (Combinatorial Purged CV)**:
   - 本案で n_splits=5 + min_train_splits=2 = 実 3 fold が業界標準か
   - CPCV (Lopez de Prado AFML Ch.7 推奨) 投入の現実性
6. **LightGBM デフォルトハイパラ vs 業界推奨**:
   - num_leaves=31 / learning_rate=0.05 / random_state=42 は LightGBM 公式デフォルト範囲か
   - Crypto / 時系列 ML で過学習防止により厳しい設定 (例: num_leaves=15 / regularization 強化) が推奨されないか

### 検索ツール

- **WebSearch** ツール (Anthropic 標準): 業界相場・論文・OSS 実装の最新情報
- **WebFetch** ツール: 具体 URL の内容取得 (Lopez de Prado SSRN / Hudson & Thames blog / Kaggle solutions 等)
- **ChatGPT 等の外部 AI 使用不可** (auditor_template L11 / まこさん課金外)
- 「トレードについての認知を理解」した上で判断 = Crypto futures algo trading の業界実情を踏まえる

## 結果ファイルフォーマット (auditor 用)

`.claude/audits/2026-05-26_phase1_v6_6cases_methodology_audit_report.md` に以下を出力:

1. **Step -1 監査対象の型宣言** (混合型: 数値型 + コード型 + 文書型)
2. **Step 0 指摘前提確認** (5 案結果 + spec 文言 + Phase 1 vs Phase 4-b/5 の境界)
3. **観点 ①〜⑦ + Q1-Q8 の所見** (各観点・各 Q に対し「数値根拠ある断言」or「データ不足 (理由)」)
   - 特に Q6 不正チェック (4 項目) は **PASS / FAIL** を明示
   - Q7 23 軸考慮は **網羅性 PASS / 見落とし指摘 N 件** を明示
   - Q8 学習方法は **業界整合 / 改善余地 N 件** を明示
4. **外部検索結果サマリー** (検索クエリ + 主要発見 5-10 件・URL or 論文出典)
5. **総合判定**:
   - Verdict: GO (案 e で Phase 2 進行) / NO-GO (Phase 1 やり直し or Phase 0 改修) / PIVOT (他軸 Phase 1 並列実施) / OTHER
   - 業界基準・学術根拠を伴う根拠
6. **改善方向性** (まこさん + CC に対する具体提案・3-7 件)
7. **CC プロセス欠陥対策** (cc_role §1.4.6 改訂提案・5 案連続書き忘れの構造的防止策)

## 必ず守ること (auditor 守則)

- **目標 ($1,900/月) 達成可能性判定は本監査の対象外** (Phase 4-b/5 完了後の別監査)・本監査で言及する場合は「Phase 1 内方法論監査の範囲外」と明示
- 月次 NET ≥ $1,900 を下げる方向の提案禁止 (cc_role §1.0 / auditor_template L15)
- 「可能性がある」「かもしれない」「検討の余地」は禁止 (auditor_template L20)
- 数値根拠の断言 or 「データ不足 (理由: 〇〇)」で答える
- 同型バイアス警告: 同一訓練ベース AI として CC の論理に共感しすぎないこと (auditor_template L24-30)
- ChatGPT 等の外部 AI 使用不可
- **外部検索は WebSearch / WebFetch ツールで必ず実施** (技術的相場・業界基準・最新研究の引用)
- spec / cc_role / phase_flow / lessons / false_positive の内部文書だけでなく、トレードについての外部認知 (Crypto futures algo trading の業界実情) を理解した上で判断

---

依頼書終わり。

まこさんへの依頼: 別 Claude Code セッションを開いて本ファイルパス `.claude/audits/inputs/2026-05-26_phase1_v6_6cases_methodology_audit_request.md` を読ませ Plan サブエージェント `/audit` を起動してください。結果ファイル `.claude/audits/2026-05-26_phase1_v6_6cases_methodology_audit_report.md` 生成後、メインセッションに戻って報告してください。
