# handoff_to_cc_v23_session_20260522.md

(起案者・CC・2026-05-22 / 宛先・CC = 次セッション)
**版**: v23 (Step C 完了 + Phase 1 v5 指示書 mlfinpy 切替 + Step D 着手準備完了)
**前身**: handoff v22 (Y 案確定 + Phase 0 v3.1 全完了反映)

---

## §0 セッション要約 (1 行)

Step C 完了 (.venv311 + mlfinpy + timeseriescv + 依存全 install + 機能 verify) + Phase 1 v5 指示書 mlfinlab → mlfinpy 切替 (PyPI 削除 + closed-source 化対応) + lessons L-203 追加 (実態調査不足の自己反省)。

---

## §1 本セッション完了事項

### 1.1 blacklist 48 → 64 列反映 (commit `ef0e26d`)

L-202 Q1 自己申告反映 (1w/1M MTF 拡張で 8 family × 8 TF = 64 列):
- Phase 1 v5 指示書 6 箇所 (L83/L90/L98/L294/L339/L364)
- phase_compliance_checklist.md 13 箇所 (説明 + 見出し + テーブル 8 行 + 合計 + 学習対象数 + 完了報告件数 + 経緯末尾追記)
- 学習対象 feature 数: 1,414 → **2,604** (実 parquet 2,724 - 56 ラベル - 64 blacklist)

### 1.2 Step C 完了 (commit `560122e`)

- `brew install python@3.11` → Python 3.11.15 (実行時間 14m 44s・post-install 警告は無害)
- `.venv311` 構築 (`/usr/local/bin/python3.11 -m venv .venv311`・gitignore 済)
- パッケージ install: mlfinpy 0.1.2 / timeseriescv 0.2 / scikit-learn 1.8.0 / lightgbm 4.6.0 / pandas-ta-classic 0.6.20 / pyarrow 24.0.0 / ta 0.11.0
- 依存制約: numpy 1.26.4 / pandas 2.3.3 (mlfinpy 経由 numba 0.60.0 制約)
- 機能 verify 全 pass: Triple Barrier / Meta-Labeling / PurgedWalkForwardCV / CombinatorialPurgedKFold / Fractional Diff / Sample Weights
- parquet 読み込み verify OK (test_2026_q1: shape **25,631 × 2,724** ← Phase 0 v3.1 期待値完全一致)

### 1.3 重大発見: mlfinlab PyPI 削除 + closed-source 化 (commit `560122e`)

- **mlfinlab は PyPI 削除済** (`https://pypi.org/project/mlfinlab/` = 404)
- GitHub `hudson-and-thames/mlfinlab` は **"All Rights Reserved" license** (Hudson & Thames が Business/Enterprise 商業ライセンスのみ提供・open-source ではない)
- handoff v22 §7 Q4「mlfinlab Python 3.13 wheel なし → 自前実装」の根拠認識は誤り (**実態は商業化による PyPI 削除**)
- **代替確定**: mlfinpy (PyPI 公開・open-source・AFML 直接実装・`baobach/mlfinpy`) + timeseriescv (Walk-forward Purged CV・`sam31415/timeseriescv`) + 自前 DSR
- Phase 1 v5 指示書 18 hit → mlfinpy + timeseriescv に修正 (12 Edit・残存 8 件は経緯/API リファレンスとして意図的に保持)
- WebSearch 能動活用義務 (cc_role §1.0 + L-201) を本セッション後半でようやく履行 → **L-201 1 週間以内再演**

### 1.4 Phase 1 v5 指示書 mlfinpy 切替 (commit `560122e`)

12 Edit カテゴリ:
- A. 読了ゲート / 引用 (L33 / L170 / L405 / L406): GitHub URL を `baobach/mlfinpy` + `sam31415/timeseriescv` に変更
- B. Step 0-2 verify ブロック (L72-99): mlfinpy + timeseriescv + 各機能 import verify に書き換え + DSR 自前実装注記
- C. §3 PurgedKFold 設計コード (L182-197): `timeseriescv.PurgedWalkForwardCV` 主用 + `mlfinpy.CombinatorialPurgedKFold` 補助 (Layer 3 CPCV 用)
- D. その他 (L213 / L258 / L292 / L353 / L374 / L378): DSR 自前実装明記 / Step 2 セットアップ更新 / leak verify 更新 / 失敗時の戻り更新 / ガード C/D 更新

### 1.5 lessons L-203 追加

- 外部ライブラリの実態調査不足 (handoff の自己申告を WebSearch verify せず鵜呑み)
- L-201 1 週間以内再演 (「ルール追加だけでは効かない」実証ループ)
- 絶対遵守ルール 3 経路で固定:
  1. 外部ライブラリの import を指示書に書く前に PyPI 実存確認 (WebFetch `https://pypi.org/project/<name>/`)
  2. handoff の自己申告 (特に外部ライブラリ・パッケージ依存関連) は WebSearch + WebFetch で実態 verify してから引用
  3. install 試行は機能 verify までセット (`pip install OK` だけで「動く」と判断しない)

---

## §2 自己申告 (cc_role §1.3.4 義務)

### 2.1 確認質問乱発 (cc_role §1.4 #7 / L-202 同型再演)

本セッション中盤で「実行しますか？それともカテゴリごとに分けて確認したいですか？」と CC が判断すべき技術的実装単位をまこさんに投げ返した。まこさん「技術的なことはわからないから判断できない」で訂正。即実行に切替。
→ 教訓: 戦略本丸以外の確認質問禁止 (cc_role §1.5)

### 2.2 mlfinlab 実態調査の遅延 (L-203 起票)

handoff v22 Q4 自己申告を WebSearch verify せず鵜呑み・Step 3 pip install 失敗まで実態未認識。WebSearch 能動活用 (L-201 / cc_role §1.0) を本セッション後半でようやく履行。
→ 教訓: L-203 で 3 経路固定済

### 2.3 WORKFLOW.md 改訂20 のパス誤記

CC が改訂20 で書いた「`/usr/local/opt/python@3.11/bin/python3 -m venv .venv311`」は **そのパスは存在しない** (誤記)。実際は `/usr/local/bin/python3.11` または `/usr/local/opt/python@3.11/libexec/bin/python3`。Step C 着手時に CC 自身が機械的 verify で発見・即訂正。

---

## §3 次セッション CC 優先順位 (Step D 着手)

### §3.1 優先 1 (dsr.py 自前実装・1-2 時間)

**根拠**: Bailey + Lopez de Prado (2014) "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality" SSRN 2460551

**数式 (概要)**:
```
DSR = (SR_observed - SR_expected_max) / sigma_SR

ここで:
- SR_observed = 観測された Sharpe Ratio
- SR_expected_max ≈ sigma_SR * ((1 - γ) * Phi^(-1)(1 - 1/N) + γ * Phi^(-1)(1 - 1/(N*e)))
  - γ = Euler-Mascheroni constant ≈ 0.5772
  - N = grid trial 数 (selection bias 補正)
  - Phi^(-1) = standard normal inverse CDF
- sigma_SR = sqrt((1 - γ_3 * SR + (γ_4 - 1)/4 * SR^2) / (T - 1))
  - γ_3 = skewness of returns
  - γ_4 = kurtosis of returns
  - T = sample size
```

**配置**: `scripts/priority_rebuild/dsr.py`

**実装方針**:
- scipy.stats.norm + numpy ベース
- 100+ grid 試行記録機能 (selection bias 補正用)
- 入力: returns array + trial count N
- 出力: DSR scalar + intermediate stats (SR / SR* / sigma_SR / skew / kurt)

**test ケース**:
- 既知 Sharpe (例: SR=1.0・N=100・T=252) で SSRN paper の検証データに対し DSR 一致確認

### §3.2 優先 2 (Phase 1 v5 実装着手・約 3-4 週間)

Phase 1 v5 指示書 (`.claude/instructions/2026-05-22_phase1_layer_inversion_instruction.md`・約 440 行) §6 実装手順 Step 2 以降:

```
[Step 1] Phase 0 改修 v3.1 完了 (✅ 完了済・Step 0-2 で verify)
[Step 2] mlfinpy + timeseriescv セットアップ (✅ Step C 完了済) + Purged K-Fold runner + dsr.py
  - run_phase1_v5_purged_kfold.py (共通 CV runner・timeseriescv.PurgedWalkForwardCV 主用)
  - dsr.py (自前 DSR・優先 1)
[Step 3] 6 案実装 (case_a 〜 case_f)
  - case_a (14 ラベル RMSE・流用ベースライン)
  - case_b (Entry Binary Classification)
  - case_c (Direction Multiclass)
  - case_d (Ranking LambdaRank・新規)
  - case_e (Triple Barrier・mlfinpy.labeling.get_events)
  - case_f (Meta-Labeling・mlfinpy.labeling.get_bins・case_e 後 sequential)
[Step 4] smoke test (Fold 0 のみ・1-2 ヶ月・1 時間以内)
[Step 5] CP2 監査依頼 (Claude `/audit` 経由・7 項目)
[Step 6] /audit OK 後・full 5 fold × 6 案実行 (約 20 時間・3 並列・30-45 GB)
[Step 7] phase1_v5_summary.json 生成 (5 指標 × 6 案 × 5 fold + DSR + 合格判定)
[Step 8] 完了報告 (8 点必須証跡 + L-200 機械的証跡 3 点)
[Step 9] Layer 3 投入判定 (§4.1 厳格化・6 案ベストでも 5 指標未達なら即 Layer 3)
```

### §3.3 優先 3 (将来)

- Phase 4-b 設計再 audit (DSR + Adaptive 閾値最適化)
- Phase 5/6/7 統合
- OI 特徴量化 (§2.3 #19・Phase 4-b 結果次第)
- Phase 7-d 着手前 maxMarketOrderQty paper trading test

---

## §4 引き継ぎリソース (新セッション Step 0 で必読)

### §4.1 本 handoff + 直近 lessons

- **本ファイル `handoff_to_cc_v23_session_20260522.md`** (本ハンドオフ)
- **lessons_active.md L-203** — mlfinlab PyPI 削除 + WebSearch 能動活用義務再確認 (本セッション学習・最重要)
- **lessons_active.md L-202** — CC 完全網羅志向 + 指示書フロー並列実施手順違反
- **lessons_active.md L-201** — WebSearch 能動活用 + 業界経験閾値 bool ハードコード禁止 (L-203 と同型)

### §4.2 設計ドキュメント

- **Phase 1 v5 指示書 (mlfinpy 切替版)** (`.claude/instructions/2026-05-22_phase1_layer_inversion_instruction.md`・約 440 行・commit `560122e`)
- **phase_compliance_checklist.md §Phase -1** (blacklist 64 列反映済・commit `ef0e26d`)
- **cc_ml_design_spec.md §1.5.1** (Phase 1 合格基準 5 指標・約 410 行)
- **learning_design_v4.md v5** (約 377 行・Layer 配分逆転確定)
- **technical_analysis_knowledge_base.md v3** (1691 行・§D ML for Trading + §I 閾値設計論)

### §4.3 データ・環境

- **parquet 3 種** (`results/priority_rebuild/labels_mfe_mae_pct_{train_2021_2024,test_2025,test_2026_q1}.parquet`・sha256 既出)
- **`.venv311` 環境** (Step C 完了・gitignore 済・mlfinpy + timeseriescv + scikit-learn + lightgbm + 依存全 install 済)
- **build_labels_pct.py** (Phase 0 v3.1 完了済・compute_triple_barrier_labels 統合済・L290)

### §4.4 ガバナンス文書 (毎セッション必読・cc_role §1.6)

- WORKFLOW.md (改訂21・本セッション末更新)
- CLAUDE.md (提案禁止リスト + セッション開始時必読リスト)
- cc_role.md (CC 役割定義・§1.4 同型バイアス 7 件警戒・§1.5 デザイン責任範囲)
- false_positive_incident_policy.md (§0-1 Prime Directive + §0-2 0.12 BTC 合計厳守 + 類型 A-H + 関所 A-G)
- exchange_spec.md (Bitget USDT-FUTURES スペック・audit#19 確定値)
- web_claude_self_check.md (読了ゲート + チェック A/B/C・CC 兼用)

---

## §5 CC 同型バイアス警戒 (handoff v22 §0.30 累積 36+ 件 + 本セッション 3 件 = **累積 39+ 件**)

### §5.1 本セッション再演 3 件

1. **確認質問乱発** (cc_role §1.4 #7・「実行しますか？それともカテゴリごとに分けて確認?」)
2. **外部ライブラリ実態調査不足** (cc_role §1.4 #4 現状把握スキップ・L-201 1 週間以内再演)
3. **WORKFLOW.md パス誤記** (cc_role §1.4 #5 まこさん発言を翻訳・「`/usr/local/opt/python@3.11/bin/python3`」が存在しないパスだった)

### §5.2 次セッション CC への命令

- **本ブロックを Step 0 で最優先で警戒**
- L-200 機械的証跡 3 点 (wc -l + Read 全文 view + 該当箇所現物引用) を「読了」「verify」「総点検」と書く時に同じターン内で必ず出す
- L-201 / L-203 を踏まえ、外部ライブラリ依存を含む判断は **WebSearch + WebFetch で実態 verify** してから断言する
- 戦略本丸以外 (技術的実装単位・パッケージ install 順序・修正単位など) はまこさんに確認質問せず CC が判断・断言・実行する (cc_role §1.5)

---

## §6 本テスト Q1 (2026 Q1) 到達まで

```
[現在] Step C 完了・Step D 着手準備
    ↓
[次セッション] dsr.py 自前実装 (1-2 時間)
    ↓
[Phase 1 v5 実装 (約 3-4 週)] 6 案並列 + Purged K-Fold 5 fold + DSR
    ↓ CP2 監査
[分岐]
  ├── 5 指標 ALL PASS → Phase 2 (Optuna ハイパラ調整・約 3-5 日)
  └── 5 指標未達 → 即 Layer 3 (CPCV + Class balancing + custom loss + アルゴ多様化)
    ↓
[Phase 3-a/3-b] cluster (KMeans / GMM / HDBSCAN 比較)
    ↓
[Phase 4-a/4-b] k-means + Exit 設計
    ↓
[Phase 5] 365d Replay (仮 test 2025 月次 NET ≥ $1,900 全 12 ヶ月)
    ↓
[Phase 6-b] 本テスト 2026 Q1 (月次 NET ≥ $1,900 全 3 ヶ月)
    ↓
[Phase 7] Bot 統合 (推論再現性 → ML Decider → run_once_ml → デモ → 本番)
```

---

## §7 メタ反省 (handoff v23 起案 CC からの記録)

本セッションで L-201 / L-202 / L-203 が連鎖的に発火 (累積 39+ 件・「ルール追加だけでは効かない」実証ループ)。これは:
- cc_role §1.4 同型バイアス 7 件 を理解してもなお再演する CC の構造的問題
- まこさんの監視 + 監査経路 (`/audit`) + WebSearch 能動活用が三位一体で必須
- 次セッション CC は「自分は同型バイアスを持つ」「自分の判断は鵜呑みにせず web で verify する」を Step 0 で明示宣言してから着手する

---

以上。
