# handoff_to_cc_v28_session_20260523.md

(起案者・CC・2026-05-23 / 宛先・CC = 次セッション)
**版**: v28 (Step I-1 仕様書 v2.1 確定 + CP3.5 監査 + I-2.1〜I-2.4 実装完了 + smoke 関所 A ② 0/8 達成・Step I-2.5 以降 + Step I-3 本走準備)
**前身**: handoff v27 (Step F-H + CP2/CP3 監査 + 案 Y (Phase 4-b 前倒し設計) 採用確定)

---

## §0 セッション要約 (1 行)

Step I-1 仕様書 v2 確定 (CP3.5 監査 Critical 2 + Major 5 + Minor 4 全件反映) → v2.1 微修正 (parquet open/high/low 不在発見で option δ・MFE_pct ラベル流用) → I-2.1 TP 約定率 Classifier 実装 (AUC 0.71 PASS) → I-2.2 time_exit_return_median artifact 生成 → I-2.3 compute_simulated_pnl_v2 関数追加 (unit test 5/5 PASS) → I-2.4 case_a v2 (2 method 並列・grid idxmax 集約) 実装で **smoke 関所 A ② 0/8 達成** = Step I 評価式現実化の方向性を定量実証。本セッション 1 ファイル修正 + 4 ファイル新規 (合計 2,351 行)。

---

## §1 本セッション完了事項

### 1.1 Step I-1 仕様書 v2 改訂 → CP3.5 監査 → v2.1 微修正
- v1 起案 (580 行) → CP3.5 監査 (Plan サブエージェント独立評価) で Critical 2 + Major 5 + Minor 4 + B 系 4 = 全 15 件指摘
- まこさん指摘で「監査推奨 100% 採用ケースは再監査不要」を §10.2 で明文化
- 全 15 件反映で v2 確定 (Critical 2 件中核反映):
  - C1: §6 method (b) trailing 数式論理破綻 → Step I スコープから除外
  - C2: §7.1 改修コードに pred_MFE 由来楽観仮定残存 → TP 価格を固定 TP_PCT grid (定数) に変更
- 実装段階で parquet に open/high/low 不在発見 → option δ (既存 `{side}_MFE_pct_K{K}` 流用・数学的等価変換) を v2.1 として反映
- 公式 source: [`.claude/instructions/2026-05-23_phase4b_forward_design_spec.md`](.claude/instructions/2026-05-23_phase4b_forward_design_spec.md) (612 行)

### 1.2 I-2.1: TP 約定率 Classifier 実装 + smoke 完走 (新規ファイル)
- **`scripts/priority_rebuild/run_tp_hit_classifier.py`** (新規・684 行)
- LightGBM Classifier (binary objective) で TP_PCT を特徴量化した統合学習
- TP_PCT grid 6 段階・8 組合せ × 5 fold = 40 学習設計
- smoke (sample K=12 LONG TP_PCT=(0.3, 0.5, 0.8) / 2 fold / n_estimators=50・51 秒):
  - AUC fold 0=0.7205 / fold 1=0.6920 (基準 ≥ 0.55 大幅超過 ✅)
  - Brier 0.221 PASS / Calibration max dev 0.18 (smoke 浅学習由来・full で改善見込み)
- phase_compliance §1.4 Z 案ガード正常動作 (2 件 hit → 物理 verify 全 PASS → 続行)

### 1.3 I-2.2: time_exit_return_median artifact 生成 (新規ファイル)
- **`scripts/priority_rebuild/compute_phase4b_train_constants.py`** (新規・458 行)
- N grid: (K//2, K) のみ・K×2 禁止 (phase_compliance §4b.3 整合)
- median 化採用 (M3 反映): mean 比較で regime ロバスト性確認 (K=12 LONG N=12 で mean -0.019% vs median -0.001%)
- 月別歪度 verify (§5.6・|skew| > 1.0 で warning)
- smoke 1 秒完走・artifact 2 + INDEX 1 ファイル生成

### 1.4 I-2.3: compute_simulated_pnl_v2 関数追加 (既存ファイル拡張・unit test 5/5 PASS)
- `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` (773 → 873 行・+100 行)
- 旧式 `compute_simulated_pnl` 残置 (backward compat) + 新式 `compute_simulated_pnl_v2` 追加
- method=fixed_tp: `return = tp_hit_prob × TP_PCT - (1-p) × SL_pct - cost`
- method=time_exit: `return = time_exit_return_median - cost`
- unit test 5 件 (数式 verify ×2 + 空入力 + 不正 method raise + 旧式 backward compat) 全 PASS

### 1.5 I-2.4: case_a v2 実装 + smoke で関所 A ② **0/8 達成** (新規ファイル)
- **`scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_v2.py`** (新規・597 行)
- 既存 case_a 保護 (Step F-H 動作確認済維持) のため別ファイル化
- I-2.1 predictions parquet + I-2.2 medians artifact をロードして 2 method × 各 grid で sim_pnl 計算
- train PnL idxmax で grid 集約 (M2 反映)
- smoke 結果 (sample K=12 LONG / 2 fold・約 1 秒):

| 指標 | 旧式 (Step H) | **新式 (Step I smoke)** |
|---|---:|---:|
| K=12 LONG max month_pnl | $4,298 ❌ | **$-95 〜 $-358** ✅ |
| anomaly_smell_detected | True (6/8) | **False (0/8)** ✅ |

「3 重楽観仮定除去で評価式が正直に動作」を定量実証。

### 1.6 lessons L-210 新規追加
- **L-210**: Phase 4-b 前倒し評価式実装で smoke 関所 A ② 0/8 達成 — Step I 設計が機能している定量実証
- 含む内容:
  - smoke 段階で関所 A 4 条件を初動 verify 可能
  - smoke 赤字 = 設計が機能していない、と誤読しない
  - 「異常値スメル 0/8 達成 = 合格」ではない (評価式信頼性回復の前提条件)

---

## §2 次セッション CC 優先順位 (Step I-2.5 以降 + Step I-3 本走準備)

### §2.1 優先 1 — Step I-2.5: runner v5.2 拡張 (約 0.5-1 日・任意)
- case_a v2 では method 別 sim_pnl を内蔵実装済 (`MethodFoldMetrics` dataclass)
- 必要なら正式に runner v5.2 として FoldMetrics に method 別保持を追加
- **CC 判断**: case_a v2 内蔵版で十分機能・runner は触らない方が既存 Step F-H 環境を保護できる・**優先度低**

### §2.2 優先 2 — Step I-2.6/I-2.7: 受け入れ基準 §8 verify (約 0.5 日)
- §8.1 関所 A ② 0/8: smoke で達成済 → full でも継続確認
- §8.2 TP 約定率モデル品質 (full 4 年で AUC / Brier / Calibration 再評価・smoke の Calibration 0.18 が full で 0.10 以下になるか)
- §8.3 月次 NET 分布の現実性 (median $100-500・p95 < $2,500・p05 > -$1,000)

### §2.3 優先 3 — Step I-2.8: 集約ロジック unit test (約 0.5-1 日)
- `_aggregate_grid_idxmax` (case_a v2) を単独 unit test 化
- edge case (empty grid / 同点 idxmax / 全 grid NaN) verify
- L-207「test カバレッジは合格境界と失敗境界の両方を含める」整合

### §2.4 優先 4 — Step I-3: 本走 (約 4-6 時間 3 並列 + 1 日判定)
- **Step I-3.1**: `run_tp_hit_classifier.py --full` (8 組合せ × 5 fold × 6 TP_PCT = 240 学習・推定 4-5 時間 3 並列)
- **Step I-3.2**: `compute_phase4b_train_constants.py --full` (16 artifact 生成・推定 5 分)
- **Step I-3.3**: `run_lgbm_phase1_v5_case_a_v2.py --full` (8 組合せ × 5 fold × grid 20 = 800 sim_pnl・推定 30-60 分)
- **Step I-3.4**: §4.1 v5.1 判定 (method 別 5 指標 + 6+ 組合せ ALL PASS 集計)
- **Step I-3.5**: CP4 監査依頼 (`/audit` 経由・関所 D 重大数字監査経路必須)

### §2.5 優先 5 (将来) — Step G Major M2 + M3 統合
- M2: 案 a で `entropy_lift=NaN → 自動 PASS` 修正 (Spearman 相関代替)
- M3: importance dominance 50% → 30% 厳格化 + merge_asof boundary verify ロジック追加

---

## §3 引き継ぎリソース (新セッション Step 0 で必読)

### Layer 1 (毎セッション必読・~700 行)
- **本ファイル** `handoff_to_cc_v28_session_20260523.md` (最新・find で取得)
- WORKFLOW.md 改訂27 active ブロック
- CLAUDE.md (Layer 2 パス修正済)
- lessons_active.md 直近 5 件 (**L-210 最新** + L-209 + L-208 + L-207 + L-206)

### Layer 2 (Step I-2.5+ / I-3 着手時)
- **Step I-1 仕様書 v2.1**: `.claude/instructions/2026-05-23_phase4b_forward_design_spec.md` (612 行)
- 実装 4 ファイル:
  - `scripts/priority_rebuild/run_tp_hit_classifier.py` (684 行・I-2.1)
  - `scripts/priority_rebuild/compute_phase4b_train_constants.py` (458 行・I-2.2)
  - `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` (873 行・I-2.3 で compute_simulated_pnl_v2 追加)
  - `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_v2.py` (597 行・I-2.4)
- 既存 case_a (Step F-H 動作確認済): `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py` (785 行・**触らない**・Step F-H 比較用)
- handoff v27 (前セッション末・I-2 着手前)

### データ・環境
- parquet 3 種 (`results/priority_rebuild/labels_mfe_mae_pct_{train_2021_2024,test_2025,test_2026_q1}.parquet`)
- `.venv311` (mlfinpy 0.1.2 / sklearn 1.8.0 / lightgbm 4.6.0 / scipy 1.17.1)
- smoke 出力 (本セッション・参照のみ):
  - `results/priority_rebuild/ml_phase1_v5/_tp_hit_classifier/` (I-2.1)
  - `results/priority_rebuild/ml_phase1_v5/_phase4b_train_constants/` (I-2.2)
  - `results/priority_rebuild/ml_phase1_v5/_case_a_v2/` (I-2.4)

---

## §4 CC 同型バイアス警戒 (累積 49+ 件・本セッション +0)

handoff v27 §4 累積 47+ 件 + 本セッション 0 件 (CP3.5 監査全件反映 + まこさん指摘で §10.2 訂正により L-209 同型再演を物理的に阻止):

### 本セッションで建設的に機能した事項
- **CP3.5 監査経路通過**: CC 単独で「Critical 2 + Major 5」を反映漏れなく v2 化 (L-209「Major 後送り判断」回避)
- **まこさん指摘で §10.2 訂正**: 「監査推奨 100% 採用ケースは再監査不要」を明文化 → 不要な工数 +0.5 日を回避
- **option δ 採用判断 (parquet open/high/low 不在発見)**: CC が parquet 構造確認 → 即報告 → option δ 推奨 → まこさん GO → v2.1 反映 (cc_role §3.4 結論まで出す + §3.6 専門用語説明義務 履行)
- **feedback_plain_language 反映**: 専門用語多用回避・例え話で説明・固有名詞最小化

### 次セッション CC への命令
- **L-210 を Step I-3 本走前に再読**: smoke で達成済の「関所 A ② 0/8」が full で維持されるか継続 verify
- **L-209 を継続警戒**: Step I-3 本走後の§4.1 判定で「method (a) で 0 件 ALL PASS」になっても、Major 後送りで Phase 2 進行を CC 単独決定しない (案 X / 案 Z の選択は まこさんレビュー必須)
- **L-208 を継続警戒**: full で異常値スメル再ヒット時、評価式 vs 学習不良 vs データ の原因切り分け順序 (①学習/②評価式/③データ) を必須実行
- **L-207**: I-2.8 集約ロジック unit test で失敗境界 test を必ず含める
- **cc_role §1.2**: 監査経路は CC 単独判定で進めたい時こそ使う (本セッションで CP3.5 経由で軌道修正できた・実証)

---

## §5 本テスト Q1 (2026 Q1) 到達まで (改訂27 で進捗反映)

```
[現在] Step I-2.4 完了 (smoke 関所 A ② 0/8 達成) ✅
    ↓ (Step I-2.5/2.6/2.7/2.8: 受け入れ基準 verify + unit test・1-2 日)
[Step I-3] 本走 (full 4 年・40 Classifier + 800 sim_pnl・4-6 時間 3 並列)
    ↓ (改修評価式で 6+ 組合せ ALL PASS or 未達)
[§4.1 判定]
  ├── 6+ 組合せ ALL PASS あり → Phase 2 (Optuna ハイパラ調整・3-5 日)
  └── 未達 → 案 X (Layer 3 投入) or 案 Z (案 b-f 順次・3-4 週間) → まこさんレビュー
    ↓
[Phase 3-a/3-b] cluster (KMeans / GMM / HDBSCAN 比較)
    ↓
[Phase 4-a/4-b] k-means + Exit 設計 (Step I で前倒し分の本確定 + 24 種 Exit カタログ + cluster 別最適 Exit + DSR + walk-forward)
    ↓
[Phase 5] 365d Replay (仮 test 2025 月次 NET ≥ $1,900 全 12 ヶ月)
    ↓
[Phase 6-b] 本テスト 2026 Q1 (月次 NET ≥ $1,900 全 3 ヶ月)
    ↓
[Phase 7] Bot 統合
```

---

## §6 メタ反省

本セッションで建設的成果:
- 仕様書 v2 → CP3.5 監査 1 回目で「Major 後送り経路を残している」(B1) を指摘されて即修正 → L-209 同型再演を**物理的に**阻止
- まこさん指摘 (「監査内容通りに修正するならまた監査する必要ないのでは」) で §10.2 過剰厳格化を訂正 → 監査経路の本旨 (= 新規判断を加えた時のみ) を明文化
- option δ 採用判断 (parquet 制約発見) を CC が即報告 → 1 ターンで方針確定 → cc_role §3.4 結論まで出す履行
- smoke で関所 A ② 0/8 達成 = Step I 設計の方向性が定量的に正しいことを実証 (L-208 解消の直接的証拠)

CC 改善方向:
- Step I-3 本走前にも CP4 監査必須 (重大数字監査経路・関所 D)
- 集約ロジック unit test で edge case (empty / 同点 idxmax / 全 NaN) を必ず含める
- full 4 年で smoke と異なる挙動が出た時は「smoke 想定外」と早計判断せず L-208 原因切り分け順序を実行

---

以上。
