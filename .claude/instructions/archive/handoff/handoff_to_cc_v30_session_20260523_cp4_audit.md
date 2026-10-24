# handoff_to_cc_v30_session_20260523_cp4_audit.md

(起案者・CC・2026-05-23 22:30 / 宛先・CC = 次セッション・明日 fresh head)
**版**: v30 (CP4 監査 CONDITIONAL NO-GO 中継・案 W+V+Critical 修正 1 週間並列 vs 案 X 直行のまこさん cold head 判断待ち)
**前身**: handoff v29 (Step I-2.8 unit test + I-2.6/2.7 §8 + I-3.2 + merge スクリプト + I-3.1 ハング → kill)

---

## §0 セッション要約 (1 行)

Step I-3.1 (tp_hit_classifier --full) を 3 並列起動 → swap 42GB thrashing で全 UN → 1 並列に切替で完走 (10 時間 13 分) → I-3.3 case_a_v2 完走 → I-3.4 §4.1 v5.1 判定で **全 8 組合せ 0/16 ALL PASS** ❌ → I-3.5 CP4 監査で **CONDITIONAL NO-GO** (Critical-1 time_exit naive baseline + Critical-2 DSR 役割誤認・案 W+V+Critical 修正 1 週間並列を推奨) → CC は今夜 lessons L-212a/b/c + WORKFLOW 改訂29 + 本 handoff + git commit のみ実施・**明日 fresh head でまこさん判断**。

---

## §1 完了済事項 (本セッション・触らない)

### 1.1 Step I-3.1 tp_hit_classifier --full 完走 (1 並列順次・10 時間 13 分)

- P1 (K=12,24) 308 分 / P2 (K=48) 149 分 / P3 (K=96) 151 分・累計 608 分
- スクリプト判定 5/8 PASS (K12_SHORT + K24_LONG + K48_LONG + K48_SHORT + K96_LONG)
- AUC 0.78-0.88 全件大幅クリア / Brier 0.07-0.20 全件クリア / Calib 0.13-0.21 で SHORT 側に集中
- 公式 source: `results/priority_rebuild/ml_phase1_v5/_tp_hit_classifier_p{1,2,3}/tp_hit_classifier_summary_train_2021_2024.json`

### 1.2 Step I-3.3 case_a_v2 完走 (順次・計約 3 分)

- P1 54 秒 / P2 42 秒 / P3 89 秒
- P1+P2 (K=12/24/48): 関所 A セーフ (anomaly_smell False)
- **P3 (K=96)**: 関所 A ② ヒット 2 件 (K96_LONG/SHORT fixed_tp で月次相当 $18-21K = 合格ライン 9-11 倍)
- L-208 Step H (6/8 ヒット 44 倍) → 2/8 ヒット 11 倍に **大幅改善**
- 公式 source: `results/priority_rebuild/ml_phase1_v5/_case_a_v2_p{1,2,3}/case_a_v2_summary_*.json`

### 1.3 Step I-3.4 §4.1 v5.1 判定 (0/16 ALL PASS)

- **fixed_tp 0/8** / **time_exit 0/8** / `meets_6plus_any_method: False`
- 撤退ライン文言「6+ 未達 → 案 X or 案 Z — まこさんレビュー必須」適用
- 全 fold で Sim PnL 赤字 ($-200K 〜 $-300K/年・time_exit でも $-22K 〜 $-41K)
- dsr.py 9 件 warning (`sigma_SR denominator non-positive`・L-207 同型・L-212b)
- 公式 source: [phase1_v5_step_i_summary_merged.json](../../results/priority_rebuild/ml_phase1_v5/_step_i_merged/phase1_v5_step_i_summary_merged.json)

### 1.4 Step I-3.5 CP4 監査 (Plan サブエージェント) 完了

- **結論: CONDITIONAL NO-GO** (Critical 2 件修正してから次フェーズ判断)
- **Critical-1 (新発覚・本監査独自指摘)**: time_exit 評価設計が予測装置になっていない・naive baseline (`merge_step_i_summaries.py` L162-176 で全 trade に train 中央値由来の単一定数を割り当て) → 24 fold で time_exit returns 完全同一値 → 16 fold 中 8 fold が構造的 PASS 不可能
- **Critical-2**: DSR bug は「設計階層の役割誤認」(まこさん仮説のガード追加で不十分・定数 returns で auto-PASS は統計理論として誤り)
- **原因切り分け寄与率**:
  - ① 学習不良: 10-15%
  - (2a) fixed_tp 評価式暫定: 40-50%
  - (2b) time_exit naive baseline: 25-30%
  - ③ データ regime 過依存: 10-15%
- **推奨次アクション**: 案 W (SL_PCT grid 拡張 1-2 日) + 案 V (K96 除外 0.5 日) + Critical-1 (case_a_v2_v3 time_exit 予測装置化 1-2 日) + Critical-2 (dsr.py ガード + 判定階層整理 0.5 日) を **1 週間並列**実施 → それでも 0/16 なら案 Z の e (meta-labeling) → **案 X 単独直行は時期尚早**
- CC 同型バイアス健全に機能した証跡: 監査が CC 整理と異なる結論を 3 件出している (Critical-1 / Critical-2 / 案 W+V+Critical 修正先行)
- L-212 候補 3 件 (a/b/c) を監査が提案 → 本 handoff §1.5 で active 追加済

### 1.5 lessons L-212a/b/c 新規追加

- **L-212a**: 16GB マシン並列受け入れ能力限界 (3 並列で swap 42GB thrashing 再発・L-211 別側面)
  - 並列度上限 = (RAM × 0.5) / 1 プロセス推定 RSS の機械的算出ルール
  - smoke 段階で RSS ピーク verify を必須化
  - 起動後 30 秒で ps + vm_stat + sysctl 4 点 verify
- **L-212b**: dsr.py × merge time_exit 定数化の相互作用 edge case (L-207 同型・統合 test 階層化義務)
  - dsr.py input contract 明文化 + `std < 1e-12` ガード + `DSRResult(nan, ...)` + auto-PASS 禁止
  - test_dsr.py に `test_sigma_sr_constant_returns_case` 追加
  - 複数 script interaction test (integration test) 階層化
- **L-212c**: time_exit naive baseline で 0/16 出すまで気付かなかった (関所 B 拡張)
  - 関所 B「変数の因果性宣言」→「評価式の予測装置性宣言」拡張
  - phase_compliance §4b に「予測装置性 verify 項目」追加
  - CP X.5 監査経路を本走前に必須化

### 1.6 WORKFLOW.md 改訂29 active ブロック追加

- 改訂28 (Step I-3.1 再起動待ち) を 🧊 履歴ブロックに移動
- 改訂29 (Step I-3.1〜I-3.5 完走 + CP4 監査 + 0/16 ALL PASS) を新規 active として追加

---

## §2 明日 fresh head での最優先タスク

### Step 0: 新セッション Step 0 プロトコル

1. CLAUDE.md / WORKFLOW.md (改訂29 active ブロック) / 本ファイル (handoff v30) / lessons_active.md L-212c〜L-208 を Read tool で全文読了
2. 機械的証跡 (wc -l + 0/25/50/75/100% 引用 + 1 行要約) をチャットに出す
3. CP4 監査結果 (本ファイル §1.4) を再読・Critical-1/Critical-2/案 W/V/X/Z の選択肢を整理
4. 「読了ゲート通過: 2026-05-24 (コア5本)」を宣言

### 最優先: まこさん判断 (CC 単独判定不可・cold head 必須)

**判断対象**: §4.1 v5.1 で 0/16 ALL PASS 出た後の次アクション

#### 案 A (CP4 監査推奨・1 週間並列)

1. **Critical-1 修正 (1-2 日)**: time_exit 予測装置化 (case_a_v2_v3)
   - 仮想 PnL = `Σ (TP 約定確率 × TP_return + (1 - TP 約定確率) × time_exit 期間期待 return) - cost`
   - tp_hit Classifier の予測値を time_exit 期間期待 return 算出に使用 (train 中央値固定からの脱却)
2. **Critical-2 修正 (0.5 日)**: dsr.py ガード + 判定階層整理
   - `if r.std(ddof=1) < 1e-12: return DSRResult(nan, ...) + [info] log`
   - auto-PASS 禁止明文化
   - test_dsr.py に `test_sigma_sr_constant_returns_case` 追加
   - merge_step_i_summaries.py の `dsr_pass` ロジックを Sortino / 月次黒字率代替判定に変更
3. **案 W (1-2 日)**: SL_PCT grid 拡張 (0.3-0.8 → 0.3-1.5%) + TP 上限拡張 (2.5 → 3.5%)
4. **案 V (0.5 日)**: K96 を §4.1 から除外 + 6 組合せで再判定 (5m ボット運用要件と 8 時間予測ホライズン乖離評価)

→ 1 週間で全部終わってから Step I-3 再走 → §4.1 v5.1 判定再評価 → 6+ ALL PASS 達成なら Phase 2 進行 / 未達なら案 Z の e (meta-labeling) 投入

#### 案 B (案 X 単独直行・2-3 週間)

- Layer 3 投入: CPCV + Focal loss + アルゴ多様化 (XGBoost / CatBoost / Random Forest 等)
- 監査推奨は「**案 X 単独直行は時期尚早**」 — 評価式 (time_exit naive baseline + fixed_tp 暫定 grid) を放置したまま学習側だけ Layer 3 化しても、Critical-1 (2a)(2b) 50-80% 寄与の改善が見込めず投資対効果が低い

#### 案 C (CC が見落とした選択肢・まこさん発案)

- ボトムアップ視点 / 他角度の選択肢があれば

### 判断後の進行

- 案 A 採用: Critical-1 → Critical-2 → 案 W → 案 V の順 (or 並列) で実装 → Step I-3 再走
- 案 B 採用: Layer 3 設計仕様書作成 (CP X.5 監査必須) → 実装 → Step I-3 再走
- 案 C 採用: まこさん発案を CC が整理 → CP4.5 監査 → 実装

---

## §3 残タスク順序 (案 A 採用時の例)

### Step I-4.1 Critical-1 修正 (1-2 日)
```bash
# case_a_v2_v3 設計仕様書を CC 起案 (200-300 行)
# CP5 監査 (Plan サブエージェント・Critical-1 修正設計妥当性 verify)
# 実装: merge_step_i_summaries.py L162-176 を予測装置化
```

### Step I-4.2 Critical-2 修正 (0.5 日)
```bash
# dsr.py L115-134 に input contract + ガード追加
# test_dsr.py に test_sigma_sr_constant_returns_case 追加 (回帰検出)
# merge_step_i_summaries.py の dsr_pass ロジック改修
```

### Step I-4.3 案 W 実装 (1-2 日)
```bash
# run_lgbm_phase1_v5_case_a_v2.py の SL_PCT grid 拡張 (0.3-0.8 → 0.3-1.5%)
# TP_PCT grid 上限拡張 (2.5 → 3.5%)
# smoke + 関所 A verify
```

### Step I-4.4 案 V 実装 (0.5 日)
```bash
# merge_step_i_summaries.py の判定対象を 6 組合せ (K=12,24,48) に限定
# K=96 LONG/SHORT を別レンズ評価 (Secondary Filter 候補)
```

### Step I-4.5 Step I-3 再走 (約 1-2 時間・1 並列順次)

```bash
# 修正後 case_a_v2_v3 で 8 組合せ × 2 method を再評価
# §4.1 v5.1 判定再実行
```

### Step I-4.6 CP5 監査 (30 分・関所 D 必須)
- 修正後 0/16 から改善幅と Phase 2 進行可否判定

### Step I-4.7 セッション終了処理
- lessons L-213+
- WORKFLOW 改訂30
- handoff v31

---

## §4 §4.1 再走後の分岐 (案 A 採用時)

### 6+ 組合せ ALL PASS 達成
- **Phase 2 進行可** (まこさんレビュー必須)
- Phase 2: Optuna ハイパラ調整 (3-5 日)

### 4-5 組合せ ALL PASS
- Step G Major M2 + M3 統合 → 再 smoke
- 案 Z の e (meta-labeling) を Secondary Filter として K96 fold0 部分成功活用

### 0-3 組合せ ALL PASS
- 案 Z (案 b-f 順次) or 案 X (Layer 3) — まこさんレビュー必須

---

## §5 CC 同型バイアス警戒 (累積 50+ 件・本セッション +3)

### 本セッションで新規発覚した同型バイアス (CP4 監査で発見)

- **L-212a**: 16GB マシン物理 RAM 制約 (16 GB) で 3 並列 (各 8 GB) 推奨 → swap 42 GB thrashing → OS 物理リソース制約の事前推定 + 機械的算出ルール不在
  - L-211 (process detach) を踏まえたが「OS 物理メモリ制約」という別側面を独立検討せず
  - cc_role §1.0 業界知見能動活用を「OS / hardware / 並列化制約」に拡張必須
- **L-212b**: dsr.py × merge time_exit 定数化の相互作用 edge case を merge 実行まで未検出
  - L-207 (test カバレッジ穴) を踏まえたが「複数 script interaction の edge case」は単一 script test では検出不可
  - 統合 test 階層化義務を新規ルール化必須
- **L-212c**: time_exit naive baseline (予測装置でなく) を 0/16 出すまで気付かなかった
  - cc_role §1.4 #2「spec の枠内でしか動かない」+ #4「現状把握スキップ」の合成
  - 関所 B「変数の因果性宣言」→「評価式の予測装置性宣言」拡張必須

### 次セッション CC への命令

- **L-212a を Step I-4 着手時に再読**: 並列度 = (RAM × 0.5) / 1 プロセス推定 RSS で機械的算出 / smoke で RSS ピーク事前 verify
- **L-212b を Critical-2 修正時に再読**: dsr.py に input contract + ガード追加・integration test 階層化
- **L-212c を Critical-1 修正時に再読**: time_exit を予測装置化する設計を CP5 監査で本走前 verify
- **L-211 を継続警戒**: nohup + disown + python -u + > log 2>&1 の起動コマンド必須
- **L-210 / L-208 / L-209 を継続警戒**: smoke 赤字 ≠ 設計欠陥・原因切り分け順序・Major 後送り警戒
- **cc_role §1.2**: 重大判断は監査経路を本走前に必ず通す (CP X.5 監査経路)

---

## §6 メタ反省

### 本セッションで建設的成果

- Step I-3.1〜I-3.5 完走 (10 時間越え長丁場・順次実行に切替で完走) — 物理制約を学習しつつ全 pipeline を走り切った
- CP4 監査が CC 整理と異なる結論を 3 件出した — CC 同型バイアス検出経路として機能した実証
- L-212a/b/c 3 件の lessons を本セッション内で記録 — 関所 G「すり抜けるたびに穴を塞ぐ」整合
- Step H (6/8 ヒット 44 倍) → Step I (2/8 ヒット 11 倍) で異常値スメル振幅 4 倍縮小 — 3 重楽観仮定除去の効果実証
- まこさんとの plain language コミュニケーション (例え話・選択肢提示・推奨断言) を全セッション通じて維持

### CC 改善方向

- **OS 物理リソース制約の事前推定**: 学習タスク起動前に推定 RSS × 並列数 ≤ RAM × 0.5 を verify する手続きを cc_role §1.0 に統合
- **評価式の予測装置性 verify**: 各 method の評価式が「予測モデルの出力を直接消費する経路を持つか」を本走前に CP X.5 監査で independent verify する手続きを phase_compliance §4b に追加
- **判定階層の整理**: §4.1 v5.1 で「DSR=nan で auto-PASS」を「DSR 適用不可 → Sortino / 月次黒字率代替判定」に変更
- **重大判断の cold head 必須**: 10 時間越え長丁場後の重大判断 (案 A vs B 等) は判断品質低下リスクで明日 fresh head に持ち越し (本セッションで実践済)

### まこさん向けコミュニケーション

- plain language 励行 (例え話・専門用語回避・選択肢提示)
- まこさん「よくわからない」発言時は CC が断言する責任 (cc_role §3.4 + feedback_design_judgment_owner)
- 重大判断は cold head 必須 (徹夜判断回避)

---

## §7 引き継ぎ補足

### Layer 1 必読

1. CLAUDE.md (改訂22 ベース・約 261 行)
2. WORKFLOW.md 改訂29 active ブロック (L302-373 周辺)
3. 本ファイル handoff v30
4. lessons_active.md 直近 5 件: L-212c → L-212b → L-212a → L-211 → L-210

### Layer 2 (案採用後の実装着手時)

- CP4 監査結果: 本ファイル §1.4 + Plan サブエージェント出力チャット (本セッション末)
- Step I-1 仕様書 v2.1: `.claude/instructions/2026-05-23_phase4b_forward_design_spec.md` (612 行)
- 実装 6 ファイル (触らない・改修対象は案採用後に確定):
  - `scripts/priority_rebuild/run_tp_hit_classifier.py` (684 行)
  - `scripts/priority_rebuild/compute_phase4b_train_constants.py` (458 行)
  - `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` (873 行)
  - `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_v2.py` (597 行)
  - `scripts/priority_rebuild/test_aggregate_grid_idxmax.py` (270 行)
  - `scripts/priority_rebuild/merge_step_i_summaries.py` (453 行)
- 案採用後の改修対象ファイル:
  - **Critical-1**: `merge_step_i_summaries.py` L162-176 (time_exit returns 再構成式 予測装置化)
  - **Critical-2**: `scripts/priority_rebuild/dsr.py` L115-134 (sigma_sr_estimate input contract + ガード)
  - **案 W**: `run_lgbm_phase1_v5_case_a_v2.py` (TP_PCT grid / SL_PCT grid 拡張)
  - **案 V**: `merge_step_i_summaries.py` (K=96 除外 + 6 組合せで再判定)

### データ・環境

- parquet 3 種 + .venv311 (mlfinpy 0.1.2 / sklearn 1.8.0 / lightgbm 4.6.0 / scipy 1.17.1)
- Step I-3.1 artifact (済・案 W/V 改修対象外): `_tp_hit_classifier_p{1,2,3}/tp_hit_classifier_predictions_train_2021_2024.parquet` (P1=76MB / P2=33MB / P3=28MB)
- Step I-3.2 artifact (済): `_phase4b_train_constants/time_exit_return_median_*.json` (16 個 + INDEX 2)
- Step I-3.3 artifact (済・Critical-1 改修で書き換え予定): `_case_a_v2_p{1,2,3}/case_a_v2_summary_*.json`
- Step I-3.4 artifact (済・公式 source): `_step_i_merged/phase1_v5_step_i_summary_merged.json`

---

以上。
