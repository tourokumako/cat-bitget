# handoff_to_cc_v22_session_20260522

セッション: 2026-05-22 (handoff v21 受領後・**Layer 配分逆転 (B') 確定**・ナレッジベース v3 1691 行 + 指示書 2 本 (Phase 0 v3.1 + Phase 1 v5) 作成)
作成者: CC (本セッション末・ML 設計担当兼務・cc_role.md v1)
保存先: `.claude/instructions/handoff_to_cc_v22_session_20260522.md`
宛先: 次セッションの CC

handoff v21 (前任) からの継続。本 v22 では **Layer 配分逆転** 確定 + **業界知識統合 (WebSearch 54 件 + Gemini 2 件)** + **3 層併存閾値設計** + **6 案並列 Phase 1 学習計画** を記録 + 本セッション CC 同型バイアス再演 9 件を最優先警戒項目として記録。

---

## §0 前提認識 (handoff v14-v21 全件継承 + 本 v22 で重大追加)

### §0.30 (本セッション・最重要・絶対警戒) CC 同型バイアス再演 9 件 (累積 27+ 件 → 36+ 件)

handoff v21 §0.27 累積 18 件 + 本セッション 9 件 (TF 欠落 / A-3 閾値派生 / A-4 K=7 verify 漏れ / rci_26 漏れ / 共通フィルタ既存実装認識ゼロ / 4 ファイル同時改修見落とし / メンテフラグ L-181 違反 / CSV §A-3.6 A/B/C 案乖離・即興定義 / 設計思想欠落 (パラメータ vs 閾値・MTF コンフルエンス) / Web 調査ゼロ実行) = **累積 36+ 件**。

**まこさん指摘で発覚した重大欠陥**:
- handoff v21 §3.1 「7 項目」を機械的コピー → 設計思想欠落 (パラメータ vs 閾値の本質未理解)
- 業界経験閾値 (BB Squeeze 10% / KDJ 110/-10) を「定番だから」でハードコード → cc_ml_design_spec §1.2 + §8 違反
- Layer 配分逆転 (V4.1 監査 #20 で「Entry Binary + Direction Multiclass を Layer 3 → Layer 1」) を **「目的関数 3 案並列追加」と中途半端に解釈** → Triple Barrier + Meta-Labeling + Walk-forward CV は依然 Layer 3 のまま

**対策 (L-200 + 新規 L-201)**:
- 「読んだ」「verify した」「監査済」「総点検した」と書く前に **機械的証跡 3 点** (`wc -l` + Read 全文 view + 該当行引用) 必須
- **設計判断時に「これは何を解決するか・本質は何か」を能動的に問う** (cc_role §1.0「あらゆる手段を尽くす」+ §1.3.3「怠けた思想排除」)
- **WebSearch / WebFetch を能動的に活用** (本セッションで 54 件実行・cc_role §1.0 義務化済) + **Gemini 等外部見解を尊重** (まこさんが貼った Gemini 見解は私の即興解釈より遥かに信頼できる)
- まこさんの「分からない」「整理して」「真剣に取り組め」は **字面通り** 受け取る (cc_role §3.3 翻訳禁止)

### §0.31 (本セッション完了) Phase 0 改修指示書 v3.1 確定 (Triple Barrier ラベル同時生成・5 ファイル同時改修)

**ファイル**: `.claude/instructions/2026-05-22_phase0_v4_rebuild_instruction.md` (576 行)

**変遷**:
| 版 | 行数 | 内容 |
|---|---|---|
| v1 | 270 | 破棄 (handoff v21 箇条書きコピー・cat_v9 grep ゼロ・累積 70% 誤り) |
| v2 | 459 | cat_v9 grep + L-196 メンテフラグ + 4 ファイル同時改修・WebSearch 6 件 |
| v3 | 507 | 業界 5 系統分類 + 3 層併存設計 + 閾値 4 大分類 + WebSearch 42 件 + Gemini 2 件 |
| **v3.1** | **576** | **Triple Barrier ラベル 28 列同時生成 (mlfinlab.labeling)** + compute_triple_barrier_labels 実装 + 56 ラベル列 parquet schema + mlfinlab パッケージ依存追加 |

**改修対象 5 ファイル**:
- `pruned_column_list.json` (約 2316-3016 列の集合定義に拡張)
- `scripts/regime/analyze_regime_label_features.py` (1-A 指標カタログ + 系統別分類)
- `scripts/regime/shape_features.py` (1-B TF 補完)
- `scripts/regime/structure_features.py` (1-C SMC + Supply/Demand + Candlestick 62 種)
- `scripts/priority_rebuild/build_labels_pct.py` (TIMEFRAMES 1w/1M 追加 + メンテフラグ削除 (L-196) + **compute_triple_barrier_labels 実装** + 56 ラベル列)

**期待結果**: 1432 + 約 800-1500 特徴量 + 28 既存ラベル + **28 Triple Barrier ラベル** = **約 2316-3016 列**

### §0.32 (本セッション完了) Phase 1 学習方法再設計指示書 v1 確定 (Layer 配分逆転 (B') 確定版)

**ファイル**: `.claude/instructions/2026-05-22_phase1_layer_inversion_instruction.md` (429 行・新規)

**Layer 配分逆転の核心**: Triple Barrier + Meta-Labeling + Walk-forward Purged K-Fold + Ranking LambdaRank を **Layer 3 → Layer 1 前倒し**:

| 案 | 内容 | Layer (v4.1) | Layer (v5・確定) |
|---|---|---|---|
| a | 14 ラベル独立 RMSE (流用) | Layer 1 | Layer 1 |
| b | Entry Binary Classification | Layer 1 (V4.1 昇格) | Layer 1 |
| c | Direction Multiclass | Layer 1 (V4.1 昇格) | Layer 1 |
| **d** | **Ranking LambdaRank** (新規) | (未含) | **Layer 1** |
| **e** | **Triple Barrier multiclass** (AFML Ch.3) | Layer 3 | **Layer 1 前倒し** |
| **f** | **Meta-Labeling 2 段階** (AFML Ch.3) | Layer 3 | **Layer 1 前倒し** (案 e 完了後 sequential) |
| 全案共通 | **Walk-forward Purged K-Fold 5 fold** (mlfinlab) | Layer 3 (B-14) | **Phase 1 から導入** |

**Phase 1 合格基準 5 指標 (cc_ml_design_spec §1.5.1 整合)**:
1. entropy lift > 10% (AFML Ch.3 推奨閾値)
2. TP Precision > 0.5
3. Direction Accuracy > 0.55 (案 c のみ)
4. Simulated PnL: 12 ヶ月中 8+ プラス + 年 NET ≥ $500
5. Walk-forward CV Sharpe (DSR 補正) > 1.0 (Bailey + Lopez de Prado 2014)

**Layer 3 投入条件厳格化 (v5)**: 6 案ベストでも 5 指標 ALL PASS 未達 → **即** Layer 3 残存タスク投入 (「ベスト案で Phase 2 進行」禁止)

**リソース計画**: 3 並列 (CPU 競合 + メモリ 30-45 GB)・全 5 fold × 6 案 = 約 20 時間 (約 1 日)・Phase 1 期間 3-4 週 (実装期間主因)

### §0.33 (本セッション完了) ナレッジベース v3 確定 (1691 行・WebSearch 54 件 + Gemini 2 件統合)

**ファイル**: `.claude/memory/technical_analysis_knowledge_base.md` (1691 行・v1 450 → v2 1528 → v3 1691)

**章構成**:
- §0-§12: 基礎 (Gemini #1/#2 + 業界 5 系統 + 5 分足 + MTF + AFML + Funding + MVRV + SOPR 等)
- §A-§D: 個別辞典 (RSI/MACD/ADX/ATR/BB/Stoch/Ichimoku/Fib/VP/Pivot/RCI/Williams + キャンドル + チャートパターン + Wyckoff + SMC + ML for Trading)
- §E: Phase 0 改修 20 カテゴリ統合ガイド
- **§I: 閾値設計論** (4 大分類 + Adaptive 設計 + Multi-Threshold Ensemble + DSR + ML 閾値処理 + Phase 別データ駆動再検討フロー・本セッション追加)
- §F: 出典 54 + 15 = **69 件 URL**
- §G/§H: 改訂履歴 + 今後の追加調査候補

**閾値 4 大分類** (本セッション体系化):
- (1) 自己実現的閾値 (RSI 70/30 / Fib 61.8% / round numbers) → **維持**
- (2) 計算式由来閾値 (BB 2σ / Z-Score ±2) → 連続値で表現
- (3) 業界経験閾値 (BB 10% / KDJ 110/-10 / ADX 25) → **データ駆動再検討・段階廃止**
- (4) Adaptive/データ駆動閾値 (rolling quantile / Z-score / regime-conditional) → **推奨設計**

**3 層併存設計**: 各特徴量で (1) 連続値 + (2) Adaptive bool + (3) 自己実現的 bool の 3 層を parquet に併存・Phase 1 feature_importance で 3 層別効果測定・Phase 4-b で業界経験 bool 段階廃止

### §0.34 (本セッション完了) learning_design_v4 → v5 改訂 (Layer 配分逆転反映)

**ファイル**: `.claude/memory/learning_design_v4.md` (336 → 377 行・+41 行)

**修正箇所**:
- §3 振り分け表 B-13/B-14/B-15: Layer 1 前倒し明示
- §4 Layer 1 タスク: 「Layer 1 (Layer 配分逆転・2026-05-22 v5)」セクション新規追加 (案 d/e/f + Walk-forward + 5 指標 + Layer 3 投入条件厳格化 + リソース計画)
- §6 Layer 3 タスク縮小: B-13/B-14/B-15 の Triple Barrier 等を Layer 1 移行明示・残存タスク (CPCV / Class balancing / custom loss) 明示
- §11 着手フロー: 6 案並列 + Purged K-Fold 5 fold + CP2 分岐判定厳格化 + Phase 1 期間 2-3 週 → 3-4 週
- §12 改訂履歴: v5 追加 (7 件修正反映)

### §0.35 (本セッション完了) cc_ml_design_spec §1.5.1 追加 (Phase 1 合格基準正式化)

**ファイル**: `cc_ml_design_spec.md` (380 → 399 行・+19 行)

**§1.5.1 Phase 1 合格基準 5 指標**:
- entropy lift / TP Precision / Direction Accuracy / Simulated PnL / DSR の数値閾値正式化
- §1.6.1 メタルール整合 (実行後緩和禁止)
- Layer 3 投入条件 (6 案ベストでも 5 指標未達 → 即投入) 厳格化

---

## §1 本セッション commit 履歴 (予定)

| commit | 内容 | ファイル数 |
|---|---|---|
| (予定 1) | technical_analysis_knowledge_base.md v1 (450 行) 新規 + Phase 0 改修指示書 v1 (270 行) 新規 | 2 |
| (予定 2) | ナレッジベース v2 (1528 行・WebSearch 42 件統合) + 指示書 v2 (459 行) 改訂 | 2 |
| (予定 3) | ナレッジベース v3 (1691 行・§I 閾値設計論追加) + 指示書 v3 (507 行) 改訂 | 2 |
| (予定 4) | Layer 配分逆転 (B') 確定: learning_design_v4 → v5 (377 行) + cc_ml_design_spec §1.5.1 追加 (399 行) + 指示書 v3.1 (576 行・Triple Barrier 28 列) + Phase 1 指示書 v1 (429 行・新規) | 4 |
| (予定 5) | セッション終了処理: lessons_active L-201 追加 + WORKFLOW.md 改訂 19 + 本 handoff v22 | 3 |

合計 commit 5 件・約 13 ファイル変更

---

## §2 本セッション 未 commit 成果物 (commit 範囲判断待ち)

なし (全成果物 commit 予定 / セッション終了処理 3 件を本 v22 commit に統合予定)

ただし `results/` ディレクトリは CLAUDE.md「コミット禁止」対象で意図的に除外。

---

## §3 pending tasks (次セッション CC への優先順位)

### §3.1 (最優先) Phase 0 改修指示書 v3.1 実装着手

**内容**: Phase 0 改修指示書 v3.1 (576 行) に従って 5 ファイル同時改修 + Triple Barrier ラベル生成

**実装手順 (指示書 §6 整合)**:
1. L-196 違反 メンテフラグ削除 (Step 1)
2. 4 ファイル同時改修 (Step 2) + Triple Barrier ラベル
3. smoke test 3 ヶ月 (Step 3)
4. CP1 監査依頼 (指示書 §9・Claude `/audit` 経由)
5. full build (Step 4・約 4-6 時間)
6. 完了報告 (指示書 §8)

**期待結果**: 約 2316-3016 列の parquet 3 種 (train + 仮 test 2025 + 本 test 2026 Q1)

### §3.2 (優先 2) Phase 1 学習方法再設計指示書 v1 実装着手

**内容**: Phase 0 v3.1 完了後・Phase 1 学習方法再設計指示書 v1 (429 行) に従って 6 案並列 + Purged K-Fold + DSR

**実装手順 (指示書 §6 整合)**:
1. Phase 0 v3.1 完了確認 (Step 0-2)
2. mlfinlab + Purged K-Fold runner 実装 (Step 2)
3. 6 案個別実装 (Step 3) — 案 a → b/c → d → e → f sequential
4. smoke test Fold 0 1-2 ヶ月 (Step 4)
5. CP2 監査依頼 (指示書 §9・7 項目)
6. full 5 fold × 6 案実行 (Step 6・約 20 時間)
7. §4.1 採用判定 or Layer 3 投入

**期待結果**: 6 案 × 5 fold × 5 指標 = 30 学習結果 + DSR + 合格判定

### §3.3 (将来) Phase 4-b 設計再 audit + DSR + Adaptive 閾値最適化

ナレッジベース v3 §I.7.3 整合で DSR + walk-forward Adaptive 閾値最適化を Phase 4-b 全グリッドサーチに統合。

### §3.4 (将来継承) Phase 7-d 着手前 maxMarketOrderQty paper trading test

v15-v21 から継承。phase_compliance_checklist.md Phase 7-d セクション記録済。

---

## §4 次セッション CC への警告 (handoff v14-v21 全件継承 + 本 v22 新規)

### §4.38 (本セッション §0.30) CC 同型バイアス再演 **累積 36+ 件**・WebSearch 能動活用が唯一の打開策

handoff v19 §0.13 (5 件) + handoff v20 §0.26 (5 件) + handoff v21 §0.27 (8 件) + 本 §0.30 (9 件) = 累積 **27+ 件**:

**唯一の打開策 (本セッション学習)**:
- **WebSearch / WebFetch を能動活用** (cc_role §1.0 義務・本セッション 54 件実行で初めて業界知見統合)
- **Gemini 等外部見解をまこさんから貼ってもらう** (即興解釈より遥かに信頼できる)
- **cat_v9 / config / 既存実装を毎タスク冒頭で全 Read** (grep で済ませない)
- **設計判断時に「これは何を解決するか・本質は何か」を能動的に問う** (cc_role §1.0 + §1.3.3 整合)

### §4.39 (本セッション §0.31) Phase 0 改修指示書 v3.1 確定・Triple Barrier ラベル同時生成必須

build_labels_pct.py に **compute_triple_barrier_labels** 実装 (mlfinlab.labeling 経由・28 ラベル列追加・合計 56 ラベル列) が **Phase 1 学習方法再設計 v5 の前提**。Phase 0 で省略すると Phase 1 で Triple Barrier 案 e/f が実装不可。

### §4.40 (本セッション §0.32) Layer 配分逆転 (B') 確定・6 案並列 + Walk-forward CV

learning_design_v4 v5 + cc_ml_design_spec §1.5.1 整合で **Triple Barrier + Meta-Labeling + Walk-forward Purged K-Fold + Ranking LambdaRank を Layer 1 前倒し**。**「学習方法そのもの」を 6 案並列検証する** ことで entropy lift 6.04% (Phase 1-c smoke・AFML Ch.3 投入域) の根本解決を狙う。

**Layer 3 投入条件厳格化**: 6 案ベストでも 5 指標 ALL PASS 未達 → 即 Layer 3 投入 (CPCV + Class balancing / Focal loss + custom loss + アルゴ多様化)。

### §4.41 (本セッション §0.33) ナレッジベース v3 §I 閾値設計論・3 層併存必須

業界経験閾値 (BB 10% / KDJ 110/-10 / ADX 25) を **bool ハードコード単独 → 禁止** (cc_ml_design_spec §1.2 + §8 違反)。3 層併存 ((1) 連続値 + (2) Adaptive bool + (3) 自己実現的 bool) 必須。

**DSR (Deflated Sharpe Ratio・Bailey + Lopez de Prado 2014) 採用**: Phase 4-b/5/6 で Standard Sharpe maximizing **禁止**。mlfinlab.backtest_statistics.DSR 経由実装。

### §4.42 (本セッション総括) Phase 0 改修着手前必読リスト (機械的証跡必須・本 v22 で 13 件に拡張)

| ファイル | 行数 | 役割 |
|---|---|---|
| `WORKFLOW.md` | 約 500 行 | 現フェーズ・改訂19 ブロック・次タスク優先順位 |
| `learning_design_v4.md` **v5** | 377 行 | **Layer 配分逆転反映** (本 v22 で確定) |
| `phase_flow_v4_with_recovery.md` | 977 行 | 各 Phase 学習内容詳細 |
| `cc_ml_design_spec.md` **§1.5.1 追加版** | 399 行 | **Phase 1 合格基準 5 指標数値正式化** (本 v22 で確定) |
| `cc_role.md` | 336 行 | CC 役割定義 (§1.4 同型バイアス + §1.6 23 軸 + §3.6 専門用語) |
| `false_positive_incident_policy.md` | 225 行 | §0-1 / §0-2 + §2 類型 A〜H + §5 関所 A〜G |
| `phase_compliance_checklist.md` | 222 行 | Phase 別 verify 項目リスト |
| `auditor_template.md` | 520 行 | Claude `/audit` 監査エージェント用 (CP1〜CP5 で起動) |
| `10_indicator_families.md` | 174 行 | 1432 指標 145 ファミリーリスト |
| `lessons_active.md` | 約 1980 行 | 本 v22 で **L-201 追加** + 累積教訓 |
| **`technical_analysis_knowledge_base.md` v3** | **1691 行** | **業界知識統合 (WebSearch 54 件 + Gemini 2 件) + 閾値設計論** (本 v22 で確定) |
| **`2026-05-22_phase0_v4_rebuild_instruction.md` v3.1** | **576 行** | **Phase 0 改修指示書** (Triple Barrier ラベル同時生成・本 v22 で確定) |
| **`2026-05-22_phase1_layer_inversion_instruction.md` v1** | **429 行** | **Phase 1 学習方法再設計指示書** (6 案並列・本 v22 で新規) |
| 本 handoff v22 | (本ファイル) | 宛先 = 次セッション CC |

---

## §5 セッション履歴サマリ (本セッション 2026-05-22)

| 時刻概算 | 出来事 |
|---|---|
| 開始 | handoff v21 受領 → まこさん「続き」確認 → CC が Step 0 セッション開始プロトコル実行 |
| 序盤 | Phase 0 改修指示書 v1 (270 行) 作成 → まこさん「TF 欠落」「A-3 閾値派生」指摘 |
| 序盤 | Gemini 見解 #1 (パラメータ vs 閾値) 受領 → CC「基礎中の基礎・既知だが起動できなかった」反省 |
| 中盤 | Gemini 見解 #2 (MTF + 複数指標) 受領 → 同型反省・WebSearch 能動活用に転換 |
| 中盤 | まこさん「君が検索して知識を集積できないの？」指摘 → cc_role §1.0 違反気づき・WebSearch 6 件実行 |
| 中盤 | まこさん「指示書を書き直す前に学んだことをまとめて」指示 → ナレッジベース v1 (450 行) 作成 |
| 中盤 | まこさん「全力で調べて辞典レベルで」→ WebSearch 7 ラウンド × 6 件 = 42 件追加実行 → ナレッジベース v2 (1528 行) 作成 |
| 中盤 | Phase 0 改修指示書 v2 (459 行) → v3 (507 行・3 層併存) 改訂 |
| 後半 | まこさん「閾値ハードコード」指摘 → cc_ml_design_spec §1.2 + §8 違反気づき・WebSearch 12 件追加 |
| 後半 | ナレッジベース v3 §I 閾値設計論 追加 (1691 行) + 指示書 v3.1 (576 行・Triple Barrier ラベル) 改訂 |
| 後半 | まこさん「学習方法問題は方向性確認」指摘 (Q1-Q5) → Layer 配分逆転 (B') 確定 |
| 終盤 | learning_design_v4 → v5 (377 行) + cc_ml_design_spec §1.5.1 追加 (399 行) + Phase 1 学習方法再設計指示書 v1 (429 行) 作成 |
| 終盤 | まこさん「切る」 → セッション終了処理 3 件 (lessons_active L-201 / WORKFLOW 改訂19 / 本 handoff v22) |

---

## §6 改訂履歴

| バージョン | 日付 | 内容 |
|---|---|---|
| v14 | 2026-05-20 | Phase 0 v3 完了報告レビュー + L-196 緊急訂正 |
| v15 | 2026-05-20 | audit#19 全工程完了 + L-198 指示書サイズ規律 |
| v16 | 2026-05-20 | 学習内容 v3 確定 (exchange_spec.md 準拠化) |
| v17 | 2026-05-21 | Phase 0-1a/1b 完了 + audit#18 + v3 §B-15 書き換え + Phase 1-c 発注 |
| v18 | 2026-05-21 | Phase 1-c smoke NO-GO + Web Claude 役割降格 + Phase 0-1 軸実装監査タスク発注 |
| v19 | 2026-05-21 | ML 設計担当 Web Claude → CC 完全移譲確定 + Entry/Exit 両側学習方法改善議論 + CC 同型バイアス 5 件記録 |
| v20 | 2026-05-21 後半 | 書類整理 11 件 + WORKFLOW.md スリム化 + learning_design_v4.md 新規 + 監査 #20 で V4.1 化 |
| v21 | 2026-05-21 | §3.0 cc_ml_design_spec §4 改訂 + phase_flow_v4_with_recovery.md 確定版 977 行 + CC 同型バイアス 8 件 |
| **v22** | **2026-05-22** | **Layer 配分逆転 (B') 確定 + ナレッジベース v3 1691 行 (WebSearch 54 件 + Gemini 2 件統合) + 閾値設計論 4 大分類 + 3 層併存設計 + Phase 0 改修指示書 v3.1 (576 行・Triple Barrier ラベル同時生成) + Phase 1 学習方法再設計指示書 v1 (429 行・新規・6 案並列 + Walk-forward CV + DSR + 合格基準 5 指標) + learning_design_v4 → v5 (377 行) + cc_ml_design_spec §1.5.1 (399 行) + CC 同型バイアス 9 件記録 (累積 36+)** |

---

## §7 新セッション CC への Quick Start (= 本ファイル読了後にやること・2026-05-22 04:XX 更新版・autonomous 進捗反映)

### ★ 結論: **Step 1〜3 完了 + Step 4 9/20 カテゴリ完了 (+329 列)**・**残 11 カテゴリ + Step 5 から開始** ★

```
現セッション (2026-05-22 autonomous mode・まこさん「残りは私の確認なしで進めて」) で進めた完了内容:

Step 1 (commit e9a5822): build_triple_barrier_labels.py を archive 移動
Step 2 (commit ba627d9): L-196 メンテフラグ削除 4 ファイル一括
Step 3 (commit b080dbc): build_labels_pct.py に compute_triple_barrier_labels() 統合・28 ラベル追加
Step 4 進行中 (commit 3bc24c1 / f9aedd5 / 139dad1 / c23f7c2 / 8c90283 / 5c89d94 / 4032cce):
  - §2.1 #1 A-1 欠損指標 8 件 (+53)
  - §2.1 #2 まこさん発振系 3 件 (+18)
  - §2.1 #5 145 ファミリー TF 欠落補完 (+48)
  - §2.1 #8 A-3 パラメータ並列展開 RSI/ADX/BB/MACD (+96)
  - §2.1 #11 Divergence bool 簡略 (Regular のみ・+36)
  - §2.2 #13 BB Squeeze + Band Walk (+30)
  - §2.2 #15 Chandelier Exit (+12)
  - §2.2 #16 Fib Extension (+18)
  - §2.3 #18 KDJ J 線 (+18)
合計: pruned 1,462 → 1,791 (+329 列・約 22% 増)・parquet 1,491 → 1,848 cols (= 1 + 1791 + 56 ラベル)

新セッション CC は残 Step 4 (11 カテゴリ) + Step 5 から再開:
```

### Step 4 残 11 カテゴリ (次セッション再開対象)

| カテゴリ | 内容 | 困難度・依存 |
|---|---|---|
| §2.1 #3 | 業界カタログ pandas-ta-classic 100+ 件 (+100-300) | **要 `pandas-ta-classic` install** (PEP 668 で blocked・venv 必要) |
| §2.1 #4 | 1w/1M MTF (+290 想定・実態 +410 1d セット転用) | **要 sample-days ≥ 365**・smoke 30d では 1w/1M データ不足で動作確認不能 |
| §2.1 #6 | Fractional differentiation (+60) | **要 `mlfinlab` install** (PEP 668 で blocked・venv or 自前実装) |
| §2.1 #7 | PCA (+20-50) | sklearn PCA・train fit / test apply (Phase 0 内 train/test/Q1 別 fit) |
| §2.1 #9 | cat_v9 共通フィルタ + Priority bool + 閾値距離 (+100-150) | cat_v9_decider.py grep + 閾値再現・cat_params_v9.json 参照必要 |
| §2.1 #10 | MTF 4 方式選定 (0・選定のみ) | CP1 監査委ね |
| §2.2 #12 | Funding rate (+10-15) | **要 history-fund-rate API fetch** + Bitget API 8h 接続 |
| §2.2 #14 | SMC Order Block + FVG + BOS (+25-50) | **要 `smart-money-concepts` install** (PEP 668 で blocked) |
| §2.3 #17 | Supply/Demand Zone (+10-20) | swing 検出ベース実装・複雑 |
| §2.3 #19 | Open Interest (+5-10) | **要 Bitget API verify + fetch** |
| §2.3 #20 | Candlestick 62 種 (+62) | **要 `pandas-ta-classic` install** (PEP 668 で blocked) |

### ライブラリ install ブロッカー解決方法 (次セッション最優先)

```bash
# PEP 668 (externally-managed-environment) 回避: venv 推奨
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api
python3 -m venv .venv
source .venv/bin/activate
pip install mlfinlab pandas-ta-classic smart-money-concepts

# 以降は .venv 経由で build_labels_pct.py 実行
```

### Step 5 (Step 4 完了後) — まこさん GO 必須

```
[Step 5-a] smoke 3 ヶ月 (sample-days 90・約 5-10 分)
[Step 5-b] CP1 監査依頼 (Claude /audit・指示書 §9・7 項目)
[Step 5-c] full build (train 2021-04〜2024-12 + test 2025 + test 2026 Q1・約 8-12 時間)
[Step 5-d] 完了報告 (指示書 §8 機械的証跡 8 点 + L-200 3 点)
```

### 全体ロードマップ (シンプル版)

```
[Phase 0 改修・残り 約 3-5 時間] ← 新セッションはここから
   ファイル: 2026-05-22_phase0_v4_rebuild_instruction.md (576 行)
   ↓ Step 3: build_labels_pct.py に compute_triple_barrier_labels() 統合実装 (約 1 時間)
   ↓ Step 4: 他 4 ファイル改修 (analyze_regime_label_features.py + shape_features.py +
   ↓          structure_features.py + pruned_column_list.json・約 2-4 時間)
   ↓ Step 5: smoke 3 ヶ月 + CP1 監査 + full build
   ↓ parquet 3 種 (約 2316-3016 列 + 56 ラベル列) 生成
   ↓
[Phase 1 学習方法再設計・約 3-4 週間] ← Phase 0 完了後
   ファイル: 2026-05-22_phase1_layer_inversion_instruction.md (429 行)
   ↓ 6 案並列 + Purged K-Fold + DSR
   ↓ 採用案決定 or Layer 3 投入
```

### 新セッション 最初の 5 ターン (具体シナリオ・Step 1/2 完了済反映)

| Turn | やること | 所要 |
|---|---|---|
| **1** | Step 0 セッション開始: 本 handoff v22 (290+ 行) を Read 全文 view + `wc -l` 引用 + §7 確認 (Step 1/2 完了済) | 5 分 |
| **2** | Step 0-1 必読ファイル引用: Phase 0 指示書 v3.1 §Step 0-1 a-g + ナレッジベース v3 §I + cc_ml_design_spec §1.5.1 | 10 分 |
| **3** | Step 0-2 実装 verify: archive 確認 (`ls scripts/priority_rebuild/archive/build_triple_barrier_labels_20260521.py`) + メンテフラグ削除確認 (`grep -nE "MAINTENANCE_\|add_maintenance" scripts/priority_rebuild/build_labels_pct.py` → 0 件) + `pip install mlfinlab` | 10 分 |
| **4** | **Step 3 着手: build_labels_pct.py に `compute_triple_barrier_labels()` 統合実装** (旧 archive の numpy ロジック流用: TP_MULT=2.0/SL_MULT=1.5/SL 優先/STOP 5-80%) + smoke 1 ヶ月 で 56 ラベル列生成確認 + commit | 1 時間 |
| **5** | Step 4: 他 4 ファイル改修着手 (analyze_regime_label_features.py の `build_indicators_extended()` 拡張から開始・新規指標 8 件追加) | 1 時間 |

→ ここまで **約 2.5-3 時間** で Phase 0 改修の Step 3-4 の山を越える。残り Step 5 (smoke + CP1 監査 + full build) は別ターンで。

### 完了済タスク (現セッション 2026-05-22・autonomous + 起床後継続)

- ✅ Step 1-3 (commit `e9a5822` / `ba627d9` / `b080dbc`)
- ✅ Step 4 §2.1 #1 A-1 欠損指標 8 件 (commit `3bc24c1`・+53)
- ✅ Step 4 §2.1 #2 まこさん発振系 3 件 (commit `f9aedd5`・+18)
- ✅ Step 4 §2.1 #5 145 ファミリー TF 欠落補完 (commit `139dad1`・+48)
- ✅ Step 4 §2.1 #8 A-3 パラメータ並列 RSI/ADX/BB/MACD (commit `c23f7c2`・+96)
- ✅ Step 4 §2.1 #11 Divergence bool 簡略 (commit `8c90283`・+36)
- ✅ Step 4 §2.2 #13 BB Squeeze + Band Walk (commit `5c89d94`・+30)
- ✅ Step 4 §2.2 #15/#16 + §2.3 #18 Chandelier + Fib Ext + KDJ (commit `4032cce`・+48)
- ✅ Step 4 §2.3 #20 Candlestick 62 種 (commit `28c1b31`・+62・要 .venv pandas-ta-classic)
- ✅ Step 4 §2.1 #4 1w/1M MTF (commit `f700e84`・+510)
- ✅ Step 4 §2.1 #6 Fractional differentiation 自前実装 (commit `3e351df`・+64)
- ✅ Step 4 §2.1 #3 業界カタログ ta library 13 indicators (commit `dbacd9e`・+104)
- ✅ Step 4 §2.1 #9 cat_v9 共通フィルタ + 主要閾値距離 pct (commit `a101a3c`・+72)
- ✅ Step 4 §2.3 #17 Supply/Demand Zone 簡略 (commit `be35635`・+24)
- ✅ Step 4 §2.2 #14 SMC 手書き簡略 (commit `1bb304e`・+40)

**合計**: pruned 1,462 → **2,667** (+1,205 列・約 82% 増)・parquet 1,491 → **2,724 cols** (smoke 30d 全 commit pass)

### 残タスク 3 件 (全部 build 段階不適切 or API リスクで次セッション送り)

| カテゴリ | 理由 | 次セッション着手内容 |
|---|---|---|
| §2.1 #7 PCA | build 段階で train/test/Q1 別 fit 複雑 (leak リスク) | Phase 1 特徴量エンジニアリングとして実装 (sklearn PCA・train fit / test apply) |
| §2.2 #12 Funding rate | Bitget API fetch autonomous で外部 call リスク | Bitget history-fund-rate API endpoint 経由 fetch + parquet merge |
| §2.3 #19 Open Interest | 同 API リスク | Bitget OI API endpoint verify + fetch |
| §2.1 #10 MTF 選定 | CP1 監査委ね・実装なし | CP1 監査結果で 1 案選定 |

### ライブラリ install ブロッカー残り (Phase 1 着手前に対処)

- ✅ `pandas-ta-classic` (venv 経由 install 済)
- ❌ `mlfinlab` (Python 3.13 で PyPI に wheel なし) → **Python 3.11 venv 再構築 or 自前実装** (PurgedKFold + DSR は Lopez de Prado AFML Ch.7 数式で自前可能)
- ❌ `smart-money-concepts` (PyPI 不存在) → 手書き簡略実装で代替済 (commit `1bb304e`)

### Step 5 (Step 4 完了後) — まこさん GO 必須

```
[Step 5-a] smoke 3 ヶ月 (sample-days 90・約 5-10 分・既に部分動作確認済)
[Step 5-b] CP1 監査依頼 (Claude /audit・指示書 §9・7 項目)
[Step 5-c] full build (train 2021-04〜2024-12 + test 2025 + test 2026 Q1・約 8-12 時間)
   - .venv 経由必須: `.venv/bin/python3 scripts/priority_rebuild/build_labels_pct.py`
   - 出力 parquet 3 種・各 8-15 GB 想定 (1 行 約 30k bytes × 100k 行 / 500k 行)
[Step 5-d] 完了報告 (指示書 §8 機械的証跡 8 点 + L-200 3 点)
```

### 実装する 5 ファイル (Phase 0)

| # | ファイル | 改修内容 |
|---|---|---|
| 1 | `scripts/priority_rebuild/build_labels_pct.py` (既存・改修) | L-196 メンテフラグ削除 + TIMEFRAMES 1w/1M 追加 + **compute_triple_barrier_labels() 新規実装** |
| 2 | `scripts/regime/analyze_regime_label_features.py` (既存・改修) | `build_indicators_extended()` 拡張 (新規指標約 100 + 業界カタログ + Divergence bool + cat_v9 共通フィルタ + Funding rate 等) |
| 3 | `scripts/regime/shape_features.py` (既存・改修) | 145 ファミリー TF 欠落補完 |
| 4 | `scripts/regime/structure_features.py` (既存・改修) | SMC bool + Supply/Demand Zone + Candlestick 62 種 |
| 5 | `results/regime_label_analysis/pruned_column_list.json` (既存・改訂) | 約 2316-3016 列の集合定義に拡張 |

詳細は **Phase 0 指示書 v3.1 §6 実装手順** 参照。

### 必読ファイル優先順位 (時短版)

| 優先 | ファイル | 行数 | 役割 |
|---|---|---|---|
| **1 (最重要)** | 本 handoff v22 | 289 | 何をやるか・全体像 |
| **2** | **Phase 0 改修指示書 v3.1** | **576** | **実装する手順・最初に読む** |
| **3** | ナレッジベース v3 §I (閾値設計論) | 約 200 | 業界知見・3 層併存設計 |
| **4** | cc_ml_design_spec §1.5.1 | 約 30 | Phase 1 合格基準 (Phase 0 完了後に使う) |
| **5 (Phase 0 完了後)** | Phase 1 指示書 v1 | 429 | Phase 1 学習方法 (Phase 0 完了後に読む・**今は不要**) |
| 補助 | learning_design_v4 v5 | 377 | 設計図 (Layer 配分逆転反映済) |
| 補助 | lessons_active L-201 | (1 件分) | WebSearch 能動活用義務 |

### 「迷子」防止 FAQ

| Q | A |
|---|---|
| 次セッションは Phase 0 と Phase 1 のどっち? | **Phase 0 から**。Phase 0 で生成する 56 ラベル列 parquet が Phase 1 の前提 |
| 最初に開くファイルは? | `2026-05-22_phase0_v4_rebuild_instruction.md` (Phase 0 改修指示書 v3.1) |
| 最初に手を入れるファイルは? | `scripts/priority_rebuild/build_labels_pct.py` (L48-50 削除) |
| ナレッジベース v3 (1691 行) は全部読むの? | **No**。§I 閾値設計論 (約 200 行) のみ Phase 0 着手前に読む。残りは設計判断時にリファレンス |
| Phase 1 指示書 (429 行) は今読む? | **No**。Phase 0 完了後に読む |
| commit はいつ? | Step 1 完了時 + Step 2 完了時 + Phase 0 全体完了時 + Phase 1 各案完了時 |
| Layer 配分逆転とは? | Triple Barrier + Meta-Labeling + Walk-forward CV を Layer 3 → Layer 1 前倒し (詳細は learning_design_v4 v5 §4 + Phase 1 指示書 §2) |

### CC 同型バイアス 36+ 件警戒 (毎ターン)

- L-200 + L-201 自己縛りルール遵守:
  - 「読んだ」「verify した」と書く前に機械的証跡 3 点 (`wc -l` + Read 全文 view + 該当行引用)
  - **設計判断前に WebSearch を最低 1 回実行** (cc_role §1.0 義務)
  - 業界経験閾値の **bool ハードコード単独 → 禁止** (3 層併存必須)
  - **Gemini 等外部見解** をまこさんから貼ってもらう (即興解釈より信頼)
- 「箇条書きをコピーで処理した気になる」を再演しない
- 「定番だから」「効率的に」を理由にしない

---

以上。

**本 handoff v22 は CC (= 次セッションの私) 宛て**。Layer 配分逆転 (B') 確定 + 業界知識統合 (WebSearch 54 件) + 3 層併存閾値設計 + 6 案並列 Phase 1 学習計画 を反映した最新版。
