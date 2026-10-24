# handoff_to_cc_v27_session_20260523.md

(起案者・CC・2026-05-23 / 宛先・CC = 次セッション)
**版**: v27 (Step F-H + CP2/CP3 監査 + 案 Y (Phase 4-b 前倒し設計) 採用確定・Step I 着手準備)
**前身**: handoff v26 (Step E case_a 実装完了 + Z 案ガード改訂)

---

## §0 セッション要約 (1 行)

Step F smoke 完走 (dsr.py L119 式 bug 修正含む) + Step G CP2 監査 Critical 2 件対処 + Step H 本走 80 学習完走で 8/8 ALL PASS=0 + 6/8 異常値スメル ② ヒット + CP3 監査で「仮説 B (評価式暫定過大評価) 7-8 割支配」「案 Y (Phase 4-b 前倒し設計) 採用」確定。Step I = Phase 4-b 前倒し設計仕様書作成 + 実装 + smoke + Step H 再走 (約 2-3 週間)。

---

## §1 本セッション完了事項

### 1.1 Step F smoke 完走 + dsr.py L119 式 bug 修正 (commit `0a4218b`)
- dsr.py L119: `(excess_kurt - 1.0)/4` → `(excess_kurt + 2.0)/4` (Bailey-Lopez de Prado 2014 / Mertens 2002 形式の γ₄ 解釈ミスマッチ)
- test_dsr.py 2 ケース期待値再計算 (Gaussian sigma=sqrt(1.5/100) / extreme case sigma_SR=0.14771 z=4.811)
- test 10/10 PASS 維持・smoke 1.3 分完走
- Z 案ガード本来環境で正常動作確認

### 1.2 Step G CP2 監査 Critical 2 件対処 (commit `de709a5`)
- C1: `DEFAULT_N_TRIALS` 6 → 48 (= 6 案 × 8 組合せ)
- C2 (a): cost-deducted return (`pred_MFE/100 - 0.033%` = 往復 maker fee 0.00028 + 暫定 slippage 0.00005)
- C2 (b): 関所 A 異常値検出を case_a 集計段階に追加 (`_detect_anomaly_smell()`・summary JSON flag)
- cc_ml_design_spec.md §1.5.1 v5.1 同記述更新

### 1.3 Step H 本走 3 並列実行完走 (P1 133 min / P2 101 min / P3 101 min・並列 2.2 時間)
- P1: K={12, 24} × LONG/SHORT (4 組合せ) → `ml_phase1_v5_step_h_p1/`
- P2: K=48 × LONG/SHORT (2 組合せ) → `ml_phase1_v5_step_h_p2/`
- P3: K=96 × LONG/SHORT (2 組合せ) → `ml_phase1_v5_step_h_p3/`
- merge script `scripts/priority_rebuild/merge_step_h_summaries.py` (218 行・新規) で統合 → `ml_phase1_v5_step_h_merged/phase1_v5_summary_merged.json`

### 1.4 Step H 統合判定 (§4.1 v5.1)
| 指標 | 値 |
|---|---|
| n_combinations | 8 / 8 ✅ |
| n_combinations_all_pass | **0** ❌ |
| meets_6plus_criteria | **False** |
| layer3_investigation_needed | **True** |
| anomaly_smell_detected | **True (6/8 組合せ)** |

| 組合せ | tp_precision (max) | sim_pnl 月次相当 (max) | Sharpe 倍率 | 異常値 |
|---|---:|---:|---:|---|
| K=12 LONG | 0.371 | $4,298 | 2.20 | ② |
| K=12 SHORT | 0.344 | $17,088 | 1.65 | ② |
| K=24 LONG | 0.441 | $9,002 | 1.70 | ② |
| K=24 SHORT | 0.406 | $30,572 | **3.39** | ②③ |
| K=48 LONG | 0.449 | $2,998 | 1.81 | セーフ |
| K=48 SHORT | 0.422 | $46,810 | 2.61 | ② |
| K=96 LONG | 0.511 | $534 | 2.76 | セーフ |
| **K=96 SHORT** | 0.437 | **$84,185** | **14.28** | ②③ |

合格ライン: 月次 NET $1,900。K=96 SHORT は 44 倍超過。

### 1.5 CP3 監査 (Plan サブエージェント独立評価) 完了
- **判断 1 (異常値原因)**: **仮説 B (評価式の暫定過大評価) が 7-8 割支配** + A (学習不良) は 2-3 割重畳
  - 決定的根拠: `compute_simulated_pnl` (`run_phase1_v5_purged_kfold.py` L295-316) の `return = pred_MFE/100 - cost` 設計
  - K=96 SHORT fold 1: 26,098 trade × 平均 3.23%/trade × notional $1,200 = $1,010,219/年 = 数学的必然
  - 「TP 約定率 100% + slippage 0 + TP 価格 = MFE ピーク価格」の 3 重楽観仮定
  - train_rmse/label_std 比正常 + LONG/SHORT 非対称が市場期間特性で説明可 → leak でない
- **判断 2 (次アクション)**: **案 Y (Phase 4-b 前倒し設計) 採用**
- **判断 3 (Step G Major 後送り)**: Major 4 件中 **M2 + M3 は本走前に対処すべきだった** (L-207 「test カバレッジ穴」同型バイアス再演)

### 1.6 lessons L-208 + L-209 新規追加
- **L-208**: 評価式が暫定段階で出た異常値スメルを学習不良と取り違える危険 (原因切り分け順序必須化・撤退ライン文言の解釈基準・Phase 4-b 前倒しトリガ基準)
- **L-209**: CC 同型バイアス「Major 後送り判断」 (CP3 監査で発覚・関所 G に統合)

### 1.7 memory feedback 新規追加
- `~/.claude/projects/.../memory/feedback_plain_language.md` (専門用語多用禁止・例え話で補足・固有名詞最小化)
- まこさん指摘「専門用語が多くよくわからない、わかりやすく簡潔に解説してほしい」反映

---

## §2 次セッション CC 優先順位 (Step I = Phase 4-b 前倒し設計着手・約 2-3 週間)

### §2.1 優先 1 — Step I-1: Phase 4-b 前倒し設計仕様書作成 (約 1-2 日)

設計ベース:
- `.claude/memory/phase_flow_v4_with_recovery.md` L528 周辺 (Phase 4-b-2 既存設計)
- `.claude/rules/phase_compliance_checklist.md` §4b.4 + §4b.4-b (TP 約定モデル基準)
- `.claude/memory/technical_analysis_knowledge_base.md` §I.6.3 (Phase 別データ駆動再検討フロー)

含むべき項目:
1. **TP 約定率モデル** (別 LightGBM Classifier・`P(future_high >= entry × (1+TP_PCT))`)
2. **実 TP 価格モデル** (`pred_MFE × X%` or cluster 別 quantile・X は cluster ごとデータ駆動)
3. **trailing exit 暫定モデル** (高値追従・反転で利確)
4. **time exit 暫定モデル** (N 分経過で強制決済)
5. **3 方式並列** (固定 TP / トレーリング / 時間 Exit) を Phase 1 評価式に組込み
6. **`compute_simulated_pnl` 改修方針** (pred_MFE 全額計上 → 約定率モデル乗算)

### §2.2 優先 2 — Step I-2: 実装 + smoke test (約 1-2 週間)
- 改修後 case_a smoke で異常値スメル ② が消えることを verify (sample 89 日で月次 NET < $3,800 目標)
- K=96 SHORT で sim_pnl_year_usd が $1,000,000 → $20,000-50,000 オーダーに縮小することを期待

### §2.3 優先 3 — Step I-3: Step H 再走 (約 2-3 時間・3 並列)
- 改修後 8 組合せ × 5 fold で再走し「真の」§4.1 判定
- 6+ 組合せ ALL PASS → Phase 2 進行 / 未達 → 案 X (Layer 3) or 案 Z (案 b-f 順次) 検討

### §2.4 優先 4 — Step G Major 4 件のうち M2 + M3 を本実装に統合
- **M2**: 案 a で `entropy_lift=NaN → 自動 PASS` の判定骨抜きを修正
  - 代替指標: regression 案 a 用に Spearman 相関 (pred_MFE rank vs true_MFE rank) > 閾値 等
  - `run_phase1_v5_purged_kfold.py` L532-533 修正
- **M3**: importance dominance 50% threshold + merge_asof boundary verify
  - `verify_top20_features_leak.py` (iv) importance_gain_single 閾値 50% → 30% に厳格化
  - Phase 0 v3.1 `attach_upper_tf` の `merge_asof(direction="backward")` で boundary +1 bar 漏れ独立検査ロジック追加

### §2.5 優先 5 (将来・Step I 完了後)
- 案 b-f 順次実装 (約 3-4 週間)
- Phase 5 Replay (仮テスト 2025) / Phase 6-b 本テスト 2026 Q1 / Phase 7 Bot 統合

---

## §3 引き継ぎリソース (新セッション Step 0 で必読)

### Layer 1 (毎セッション必読・~700 行)
- **本ファイル** `handoff_to_cc_v27_session_20260523.md` (最新・find で取得)
- WORKFLOW.md 改訂26 active ブロック
- CLAUDE.md (Layer 2 パス修正済)
- lessons_active.md 直近 5 件 (**L-209 最新** + L-208 + L-207 + L-206 + L-205)

### Layer 2 (Step I 着手時)
- `.claude/memory/phase_flow_v4_with_recovery.md` L528 周辺 (Phase 4-b-2)
- `.claude/rules/phase_compliance_checklist.md` §4b.4 + §4b.4-b
- `.claude/memory/technical_analysis_knowledge_base.md` §I.6.3
- 実装ベース:
  - `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` (773 行・`compute_simulated_pnl` L295-316 改修中心)
  - `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py` (785 行・L382-388 returns_per_trade)
  - `scripts/priority_rebuild/merge_step_h_summaries.py` (218 行・Step I-3 再走時再利用)
- Step H 結果:
  - `results/priority_rebuild/ml_phase1_v5_step_h_merged/phase1_v5_summary_merged.json`
  - `results/priority_rebuild/ml_phase1_v5_step_h_p{1,2,3}/phase1_v5_summary.json` + `step_h_run.log`

### データ・環境
- parquet 3 種 (`results/priority_rebuild/labels_mfe_mae_pct_{train_2021_2024,test_2025,test_2026_q1}.parquet`)
- `.venv311` (mlfinpy 0.1.2 / sklearn 1.8.0 / lightgbm 4.6.0 / scipy 1.17.1)

---

## §4 CC 同型バイアス警戒 (累積 47+ 件・本セッション +2)

handoff v26 §5 累積 45+ 件 + 本セッション 2 件:
1. **dsr.py L119 式 bug を smoke crash で偶然発見** (= CP1 監査時の test カバレッジ穴を見逃した同型・L-207)
2. **Step G CP2 監査の Major 4 件を「Step H 結果見てから判断」と CC 単独で後送り** (= 判定骨抜き系 M2 が本走前 blocker だったのに見逃した同型・L-209)

### 次セッション CC への命令

- **L-208 を Step I 着手時に最優先**: 評価式が暫定段階で出た異常値スメルを学習不良と取り違えない・原因切り分け順序 (①学習/②評価式/③データ) を必須実行
- **L-209 を CP2 監査結果受領時に再起動**: Major 後送り判断は CC 単独で確定しない・再監査経路 (CP2.5) を本走前に挟む
- **feedback_plain_language を提案前に再確認**: 専門用語を多用しない・複雑仕様提示時は例え話を入れる・固有名詞 (案 X/Y/Z・C1/C2・M1-M4) 最小化
- L-207: test カバレッジは「合格境界」だけでなく「失敗境界 (raise 境界)」を必ず含める
- L-206: ブラックリストガード判断は「停止 vs 緩和」二択でなく「物理 verify 経由続行」を選択肢に加える
- L-205: 設計閾値・パラメータ根拠 verify は最低 3 ファイル grep (cc_ml_design_spec + phase_flow_v4 + technical_analysis_knowledge_base)
- L-204: system reminder で auto-load されているファイルも Read tool で取り直す
- L-200: 「読んだ」「verify した」「監査済」と書く時は同ターン内に機械的証跡を必ず出す
- cc_role §1.2: 監査経路は CC 単独判定で進めたい時こそ使う (本セッションで CP3 監査経由で軌道修正できた・実証)
- cc_role §1.5: 戦略本丸以外は CC が判断・断言・実行 (確認質問乱発禁止)
- core_rules §MUST: コード変更前に差分提示 → GO 待ち・1 ターン 1 変更・bitget_keys.json 警告

---

## §5 本テスト Q1 (2026 Q1) 到達まで

```
[現在] Step H 不合格 (8/8 ALL PASS=0) + 異常値スメル 6/8 + CP3 監査で評価式暫定性確定
    ↓ (Step I-1 Phase 4-b 前倒し設計仕様書・1-2 日)
[Step I-2] 実装 + smoke (1-2 週間)
    ↓
[Step I-3] Step H 再走 (2-3 時間・3 並列)
    ↓ (改修評価式で 6+ 組合せ ALL PASS or 未達)
[§4.1 判定]
  ├── 6+ 組合せ ALL PASS あり → Phase 2 (Optuna ハイパラ調整・3-5 日)
  └── 未達 → 案 X (Layer 3 投入) or 案 Z (案 b-f 順次・3-4 週間)
    ↓
[Phase 3-a/3-b] cluster (KMeans / GMM / HDBSCAN 比較)
    ↓
[Phase 4-a/4-b] k-means + Exit 設計 (Step I で前倒し分の本確定)
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
- Step G CP2 監査 → Critical 2 件対処 → Step H 本走 (3 並列・80 学習) を完走できた
- dsr.py L119 隠れ bug を smoke crash で偶然発見 → 修正 → 公式 source 経由で next session 引き継ぎ
- CP3 監査経路を CC 自己判断で進めたい場面で正しく通せた (cc_role §1.2 履行)
- まこさん指摘 (専門用語多用) で `feedback_plain_language.md` を新規作成

CC 改善方向:
- 「Major 後送り判断」を CC 単独で確定しない (L-209)
- 「異常値スメル = 学習問題」と即断定しない (L-208)
- 専門用語多用癖を矯正 (feedback_plain_language)
- CP2 監査結果受領時は Critical/Major の線引きを CC が下すのでなく独立評価者に判定させる

---

以上。
