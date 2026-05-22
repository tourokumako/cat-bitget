# WORKFLOW_archive_20260522.md — 改訂20 / 19 / 18 / 17 / 16 / 15 履歴

2026-05-22 セッション末スリム化で WORKFLOW.md (672 行) から本ファイルに移動。
WORKFLOW.md の現役は改訂22 active ブロックのみ。

改訂15 以前の履歴は別 archive [`WORKFLOW_archive_20260521.md`](WORKFLOW_archive_20260521.md) 参照。

---

## 🧊 改訂20 ブロック (履歴・参照用)

**【旧正本ブロック・改訂20・2026-05-22 セッション末】**

### 本セッション (改訂19 セッション → 同日継続 autonomous) 完了事項

#### 1. Phase 0 改修 v3.1 全工程完了 (Step 1-5・累計 22 commit)

- **Step 1 (commit `e9a5822`)**: build_triple_barrier_labels.py archive 移動
- **Step 2 (commit `ba627d9`)**: L-196 メンテフラグ削除 4 ファイル一括
- **Step 3 (commit `b080dbc`)**: build_labels_pct.py に compute_triple_barrier_labels() 統合・28 Triple Barrier ラベル追加
- **Step 4 16/20 カテゴリ完了** (commit `3bc24c1` 〜 `1bb304e`・8 commit・pruned 1,462 → 2,667 +1,205 列):
  - §2.1: #1 A-1 欠損補完(+53) / #2 発振系(+18) / #3 業界カタログ ta library 13(+104) / #4 1w/1M MTF(+510) / #5 TF 欠落補完(+48) / #6 Fractional differentiation 自前(+64) / #8 A-3 パラメータ並列(+96) / #9 cat_v9 共通フィルタ(+72) / #11 Divergence bool(+36)
  - §2.2: #13 BB Squeeze(+30) / #14 SMC 手書き簡略(+40) / #15 Chandelier Exit(+12) / #16 Fib Extension(+18)
  - §2.3: #17 Supply/Demand(+24) / #18 KDJ J 線(+18) / #20 Candlestick 62 種(+62)
- **Step 5-a smoke 90d**: 5m26s・assert 2,667 完全一致
- **Step 5-b CP1 監査 (commit `bb29e89`)**: 条件付き合格・3 指摘対応済
- **Step 5-c full build (4h18m)**: parquet 3 種生成
  - train 2021-04〜2024-12: 394,561 行 / 1.60 GB / sha256 `e071110c...`
  - test 2025: 105,120 行 / 0.47 GB / sha256 `7f1b6b35...`
  - test 2026 Q1: 25,631 行 / 0.11 GB / sha256 `a7541917...`
- **Step 5-d 完了報告 (commit `c23af9e`)**: leak verify §7 4 点全 pass + timestamp 分離 verify pass

#### 2. Y 案確定 (commit `ae22ce1`・まこさん上位方針再確認)

ML 自体の利益創出力測定 (6 案並列効果測定) を Phase 1 で優先・Funding/OI 特徴量化スキップで Phase 1 着手早期化:
- **§2.2 #12 Funding 特徴量化: スキップ確定** (median 0.0002%/8h は予測価値限定・月 0.018% で誤差レベル)
- **§2.3 #19 OI 特徴量化: 保留** (Phase 4-b で結果次第追加検討)
- **§2.1 #7 PCA**: Phase 1 特徴量エンジニアリングで実装 (sklearn・train fit / test apply・leak フリー)
- **§2.1 #10 MTF 選定**: CP1 委ね・実装なし
- Funding PnL 控除: median +0.0002%/8h × 保有時間 (Phase 5-e で確定済方針)

#### 3. CC 自己申告 3 件 + 自己反省 (lessons L-202 追加)

- **Q1 (blacklist 48 → 64 列)**: §2.1 #4 1w/1M 追加で自動展開・指示書 §5 範囲外判断 (指示書 §5 改訂推奨)
- **Q3 (指示書 §9 フロー違反)**: CP1 監査と full build を並列実施・sequential 規定違反・結果オーライ
- **Q4 (Triple Barrier 自前実装)**: mlfinlab Python 3.13 wheel なし → 自前実装・ラベル専用設計・Phase 1 で X drop verify 義務化
- **CC 自己反省**: 前回 Q2「Funding/OI 要対応 ⚠️」は CC 保守判断・実証根拠なし・まこさん上位方針優先順位を見失った (lessons L-202)

### 次セッション CC 優先順位 (改訂20 当時)

1. **優先 1 (Step C)**: Python 3.11 venv 再構築・半日-1 日
2. **優先 2 (Step D)**: Phase 1 学習方法再設計指示書 v1 実装着手 (約 3-4 週間)
3. **優先 3 (将来)**: Phase 4-b 設計再 audit / Phase 5/6/7 統合 / OI 特徴量化

---

## 🧊 改訂19 ブロック (履歴・参照用)

**【旧正本ブロック・改訂19・2026-05-22 セッション末】**

### 本セッション (handoff v21 受領後) 完了事項

#### 1. ナレッジベース v3 確定 (technical_analysis_knowledge_base.md・1691 行)
- v1 (450 行) → v2 (1528 行) → v3 (1691 行)
- WebSearch 54 件 + Gemini 見解 2 件統合
- §A-§D 個別辞典 (RSI/MACD/ADX/ATR/BB/Stoch/Ichimoku/Fib/VP/Pivot/RCI/Williams + キャンドル + Wyckoff + SMC + AFML)
- **§I 閾値設計論** (4 大分類: 自己実現的 / 計算式由来 / 業界経験 / Adaptive + DSR + 3 層併存設計)
- §F 出典 69 件 URL

#### 2. Phase 0 改修指示書 v3.1 確定 (576 行・Triple Barrier ラベル同時生成)
- 5 ファイル同時改修 (pruned_column_list + 4 .py)
- 約 2316-3016 列 (1432 既存 + 800-1500 新規特徴量 + 28 既存ラベル + **28 Triple Barrier ラベル**)
- L-196 メンテフラグ削除 (L-181 違反訂正)
- 業界 5 系統分類 + 3 層併存閾値設計
- mlfinlab パッケージ依存追加

#### 3. Phase 1 学習方法再設計指示書 v1 新規作成 (429 行・Layer 配分逆転 (B') 確定版)
- **6 案並列**: 案 a (14 ラベル RMSE) + 案 b (Binary) + 案 c (Multiclass) + **案 d (Ranking LambdaRank)** + **案 e (Triple Barrier multiclass)** + **案 f (Meta-Labeling 2 段階)**
- **Walk-forward Purged K-Fold 5 fold** (mlfinlab.cross_validation・Layer 3 → Layer 1 前倒し)
- **DSR (Deflated Sharpe Ratio・Bailey + Lopez de Prado 2014) 採用** (selection bias 補正)
- **合格基準 5 指標数値** (entropy lift > 10% / TP Precision > 0.5 / Direction Accuracy > 0.55 / Simulated PnL 8+ 月プラス + 年 $500 / DSR > 1.0)
- **Layer 3 投入条件厳格化** (6 案ベストでも 5 指標未達 → 即 Layer 3)
- リソース計画 (3 並列・30-45 GB・約 20 時間)

#### 4. learning_design_v4 → v5 改訂 (377 行・+41 行)
- §3 振り分け表 B-13/B-14/B-15 Layer 1 前倒し明示
- §4 「Layer 1 (Layer 配分逆転・2026-05-22 v5)」セクション新規追加
- §6 Layer 3 タスク縮小
- §11 着手フロー大幅修正

#### 5. cc_ml_design_spec §1.5.1 追加 (399 行・+19 行)
- Phase 1 合格基準 5 指標数値正式化
- §1.6.1 メタルール整合 (実行後緩和禁止)

---

## 🧊 改訂18 ブロック (履歴・参照用)

**【旧正本ブロック・改訂18・2026-05-22 セッション末】**

### 本セッション (handoff v20 受領後) 完了事項

#### 1. 未 commit 整理 (handoff v19 §2 残課題)
- `6510231`: Phase 0/1-a/1-b/1-c smoke 実行ログ 7 件
- `91317c5`: priority_rebuild scripts 3 件 (Phase 0 集計 + option5 v2/v3)
- `c16005f`: 過去 audits + 指示書 一括 (audit15/16/19 + 13 指示書 + modified 3)
- `9638c26`: audit17 phase_a §0.13 #1 違反成果物 (記録として保持)

#### 2. §3.0 cc_ml_design_spec §4 改訂 (前提タスク・learning_design_v4 §8)
- `7872559`: cc_ml_design_spec.md §4 全面改訂 + pm_review_template.md L35 旧表記訂正 + handoff_to_web_claude.md (凍結) 注記追加
- 「1 回のサイズ 固定 0.12 BTC」→「合計 0.12 BTC 厳守」+ cap カウント = **合算カウント** 確定 (B-8 / D-ζ.10)
- 全エントリー時点で `sum(active_position_btc) ≤ 0.12` verify 実装義務

#### 3. phase_flow_v4_with_recovery.md 全面書き直し (試作 7 回 → 確定版)
- `6d06425`: phase_flow_v4 新規作成 (888 行) + V3 archive 移動
- `f540c1e`: A 案修正反映 (888 → 977 行・+89 行)
  - phase_compliance_checklist.md (222 行) + false_positive_incident_policy.md (225 行) 全文 view → 整合性総点検 → A 案 8 件修正

---

## 🧊 改訂17 ブロック (履歴・参照用)

**【旧正本ブロック・改訂17・2026-05-21 セッション末】**

### 本セッション後半 (handoff v19 受領後) 完了事項

#### 1. 書類整理 11 件 (handoff v20 §0.17)
- A-a/b/c: cc_ml_design_spec.md (作成者表記 + Phase 1 Step 4 + §10 報告フロー)
- A-2: `.claude/rules/cc_role.md` **新規作成 366 行** (CC 役割定義・web_claude_role v3 反転)
- A-1: web_claude_role.md v3.1 (冒頭に降格注記)
- A-d: auditor_template.md (L24 同型バイアス警告 + 14 ラベル化)
- A-e: memory/handoff_to_web_claude.md (凍結マーク追加)
- B-1: web_claude_self_check.md (CC 兼用注記)
- B-2: CLAUDE.md (必読リスト 4 件追加 + 14 ラベル化 + 目標表記 cc_role §1.0 整合)
- C-1: 本 WORKFLOW.md 改訂16
- F-1: MEMORY.md index + role_transition_20260521.md 新規 (memory 配下・git 管理外)
- C-3: phase_compliance_checklist.md verify only (旧記述 0 hit ✅)

#### 2. WORKFLOW.md スリム化 (handoff v20 §0.18)
- 887 → **373 行 (-58%)**
- 履歴 538 行を `archive/workflow/WORKFLOW_archive_20260521.md` に全文移動

#### 3. §設計思想 ML pipeline 用語化 (handoff v20 §0.19)
- L217 「Priority 構築方針 / 実装方針」(P1-P24 ゼロから再設計) → ML pipeline 用語 + **合計 0.12 BTC 厳守** (false_positive §0-2) 明示
- CLAUDE.md L88/L97 + WORKFLOW.md L124/L163 関連 3 箇所も整理

#### 4. 目標表記 cc_role §1.0 整合 (handoff v20 §0.20)
- CLAUDE.md L40/L13/L149 + WORKFLOW.md L38/L109-118/L164/L519/L839 (合計 8 箇所)
- 目標 $60/day → **月次 NET ≥ $1,900 全月クリア達成** + 「あらゆる手段」「全力でコミット」中身明記

#### 5. learning_design_v4.md 新規作成 (handoff v20 §0.21/§0.22)
- 23 軸 CSV 全文 view 完了で V3 全面再構築
- 構成: 23 軸 → 5 学習タスク (T1-T5) 分解 + Layer 1〜3 割り付け + §X.10 明示
- learning_design_v3.md → `.claude/memory/archive/learning_design_v3_20260521.md` archive
- V4 = 296 行 (初版)

#### 6. ChatGPT → Claude 監査モード `/audit` 訂正 (handoff v20 §0.23)
- まこさん明示「私チャッピーに課金してない・Claude の監査モードでやるしかない」
- 3 ファイル 11 箇所訂正 (現役 / 未来用記述のみ・過去歴史記録は保持)

#### 7. auditor_template.md 本セッション変更全反映 (handoff v20 §0.24)
- 15 箇所修正 (473 → 520 行・+47 行)
- Phase 構成更新 (14 ラベル / k=3 / Phase 2 = §1.6 4 指標 / 合計 0.12 BTC 厳守)
- 完了報告必須証跡 5 点 → 8 点 (false_positive §5A/B 整合)
- CC 同型バイアス 7 件全列挙
- 参照ファイルリスト更新 (cc_role / learning_design_v4 / CSV 1962 行 / handoff v19 等)

#### 8. 監査 #20 実施 → V4.1 へ 5 箇所修正 (handoff v20 §0.25)
- Claude 監査モード `/audit` で general-purpose subagent 起動
- 懸念 1: entropy lift 数値誤記 (旧 2.2% → 実測 **6.04%**・false_positive §2 類型 E/G リスク)
- 懸念 2: §X.10 = Layer 3 教条主義 (CSV B-13.10 両論併記・handoff v19 §0.13 #4 再演)
- 懸念 3: Entry 学習根本問題温存 (handoff v19 §0.13 #5 再演)

#### 9. handoff v20 作成 (本セッション末)
- `.claude/instructions/handoff_to_cc_v20_session_20260521.md` 新規

---

## 🧊 改訂16 ブロック (履歴・参照用)

**【現在の正本ブロック・改訂16・2026-05-21 セッション末】**

### Phase 進捗 (本セッション 2026-05-21 完了事項)
- **Phase 0 v3 spec sweep 完了** (commit `22e75a9`)
- **Phase 1-a 14 ラベル LightGBM RMSE 学習完了** (commit `9d99dbb`): 67 分・rmse_ratio 14/14 ✅・top1 = atr14_pct__5m 33-65% dominance (ボラ予測のみ機能)
- **phase_flow_v3_with_recovery 保管** (commit `57f92d1`)
- **Phase 1-b 簡易 PnL チェック → NO-GO** (commit `2f01a98`)
- **audit#18 起票 → A 案切替** (commit `5890622`)
- **Phase 1-c Triple Barrier multiclass smoke 実行 → NO-GO**: entropy lift 6.04% / TP Precision 0.2364

### ML 設計担当 Web Claude → CC 完全移譲 (handoff v18/v19 でまこさん決定)
- **2026-05-21 移譲**
- **Web Claude = 機械照合担当** (文書整合性 / grep sweep / 旧記述検出のみ)
- **CC = 実装担当 + ML 設計担当兼務**

### Entry/Exit 両側学習方法改善議論 (handoff v19 §0.14)
1. 1432 指標で **ボラ予測のみ機能** (top1 = atr14_pct__5m 33-65% dominance)
2. SL hit が TP の 1.78 倍 (Phase 1-b)
3. multiclass logloss が entropy baseline からほぼ改善なし (lift 6.04%)

→ Entry 学習問題が示唆。**新 Path A 改** (Entry Binary + Direction Multiclass + Exit Triple Barrier + Meta-labeling + Walk-forward CV) Layer 1 並行実装提案。

### 書類整理 11 件 + 役割移譲記録は改訂17 ブロック参照。

---

## 🧊 改訂15 ブロック以前 (履歴・archive 移動済・参照用)

改訂15 以前の旧現フェーズブロック (改訂13/14/15/7) / 旧次のタスク (Phase 4-a 改訂23・Phase 2 = 238 行) / 試行禁止リスト / 旧 Priority パラメータ凍結 / Replay コマンド (旧フロー) / 引き継ぎリソース (旧版) は [`WORKFLOW_archive_20260521.md`](WORKFLOW_archive_20260521.md) (538 行) に全文保存。
