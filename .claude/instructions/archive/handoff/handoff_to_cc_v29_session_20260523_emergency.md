# handoff_to_cc_v29_session_20260523_emergency.md

(起案者・CC・2026-05-23 / 宛先・CC = 次セッション = PC 再起動後の新 claude code session)
**版**: v29 (緊急中継・VS Code 強制終了で I-3.1 ハング → kill → PC 再起動が必要・I-3.2 / I-2.8 / I-2.6-2.7 / merge スクリプト は完了済)
**前身**: handoff v28 (Step I-1 仕様書 v2.1 確定 + I-2.1〜I-2.4 + smoke 関所 A ② 0/8 達成)

---

## §0 セッション要約 (1 行)

I-2.8 unit test 10/10 PASS + I-2.6/I-2.7 §8 verify 完了 + I-3.2 完了 (16 artifact) + merge_step_i_summaries.py 作成完了 + I-3.1 (3 並列 tp_hit_classifier --full) を tee 経由 background 起動 → VS Code 強制終了で 2 時間半ハング (SIGPIPE 詰まり) → 3 プロセス kill (memory 6.5GB 解放) → PC 再起動が必要 (L-211)。

---

## §1 完了済事項 (本セッション・触らない)

### 1.1 I-2.8: 集約ロジック unit test 完了
- **`scripts/priority_rebuild/test_aggregate_grid_idxmax.py`** (新規・270 行)
- L-207 失敗境界 5 件 (empty / tied / 全 zero / 空 ts / NaN) 含む 10 test
- **10/10 PASS** (`python test_aggregate_grid_idxmax.py` 実行)

### 1.2 I-2.6/I-2.7: §8 受け入れ基準 verify 完了
- §8.1 関所 A ②: smoke `anomaly_smell_detected: False` ✅ (1 組合せ・full で 8 組合せ verify 必要)
- §8.2 TP Classifier: AUC 0.7062 ✅ / Brier 0.2216 ✅ / Calibration 0.1362 ❌ (smoke 浅学習由来・**full で 12% まで許容ルール** まこさん承認済)
- §8.3 月次 NET: smoke median $-171.73 (現実レンジ・L-210 整合)
- §8.4 leak verify 6 項目: (i)/(ii)/(iii)/(v)/(vi) ✅ / (iv) slippage 0.005% 往復扱い (まこさん承認・現値継承 → Phase 4-b-1 で再評価)

### 1.3 I-3.2 完了 (5 秒完走)
- **`compute_phase4b_train_constants.py --full`**: 16 artifact + INDEX
- 出力: `results/priority_rebuild/ml_phase1_v5/_phase4b_train_constants/`
- 全 16 ファイルで月別歪度 > 1.0 警告 (Phase 4-b-1 で cluster 別 median 化予定)

### 1.4 merge_step_i_summaries.py 作成完了 (動作未検証)
- **`scripts/priority_rebuild/merge_step_i_summaries.py`** (新規・453 行)
- §4.1 v5.1 判定 (4 指標・案 a):
  1. TP Precision > 0.5 (time_exit 不適用 → 自動 PASS)
  2. Simulated PnL: 12 ヶ月中 8+ ヶ月プラス + 年間 NET ≥ $500
  3. DSR > 1.0 (n_trials = 16 = 8 組合せ × 2 method)
  4. entropy lift > 10% (案 a NaN 自動 PASS 継承)
- method 別 (fixed_tp / time_exit) で 6+ 組合せ ALL PASS あれば Phase 2 進行

### 1.5 I-3.1 ハング → kill (L-211)
- 起動: 04:46 JST × 3 並列 (`tee` 経由)
- 検出: 07:30 JST (CPU TIME = 5:30 のまま停止 / mtime 04:46 のまま)
- kill: 07:35 JST (memory 13GB → 6.5GB)
- 原因: VS Code 強制終了で tee/tail が kill → Python stdout SIGPIPE 詰まり

---

## §2 PC 再起動後の最優先タスク

### Step 0: 新 claude code session の Step 0 プロトコル
1. CLAUDE.md / WORKFLOW.md (改訂28 active ブロック) / 本ファイル (handoff v29) / lessons_active.md L-211〜L-207 を Read tool で全文読了
2. 機械的証跡 (wc -l + 0/25/50/75/100% 引用 + 1 行要約) をチャットに出す
3. ML leak 4 点 verify (Step 0 ⑥)
4. 「読了ゲート通過: 2026-05-23 (コア5本)」を宣言

### Step I-3.1 再起動コマンド (修正後・必須採用)

```bash
echo "=====🚀 P1 RUN START $(date) =====" && \
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
source .venv311/bin/activate && \
nohup python -u scripts/priority_rebuild/run_tp_hit_classifier.py --full --k 12 24 \
  --out-base results/priority_rebuild/ml_phase1_v5/_tp_hit_classifier_p1 \
  > results/priority_rebuild/ml_phase1_v5/_tp_hit_classifier_p1.log 2>&1 &
disown
```

(P2: `--k 48 --out-base _tp_hit_classifier_p2`、P3: `--k 96 --out-base _tp_hit_classifier_p3` で同様)

**修正点 (L-211 対応・必須)**:
- ✅ `python -u` (unbuffered stdout・SIGPIPE 回避)
- ✅ `> log 2>&1` (tee 削除・中継不要)
- ✅ `nohup ... & disown` (VS Code/claude code 終了から完全独立)

**禁止 (旧パターン)**:
- ❌ `2>&1 | tee log | tail -50` (tee/tail が中継で詰まる)
- ❌ Bash `run_in_background=true` 単独 (claude code セッション死亡で道連れの可能性)

### 推定所要時間
- 各 P1/P2/P3: 1.5 - 2 時間 (3 並列)
- 進捗確認: `ps aux` で各 PID の **CPU TIME 列** が経過時間と整合しているか確認 (mtime 単独ではなく)

---

## §3 残タスク順序 (PC 再起動後)

### Step I-3.1 (1.5-2 時間 3 並列)
上記コマンドで起動。完了通知後 §4.1 進行。

### Step I-3.3: case_a_v2 --full 3 並列 (30-60 分)
```bash
# P1 (K=12,24)
nohup python -u scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_v2.py --full \
  --k 12 24 \
  --tp-hit-predictions results/priority_rebuild/ml_phase1_v5/_tp_hit_classifier_p1/tp_hit_classifier_predictions_train_2021_2024.parquet \
  --time-exit-index results/priority_rebuild/ml_phase1_v5/_phase4b_train_constants/time_exit_return_median_INDEX_train_2021_2024.json \
  --out-base results/priority_rebuild/ml_phase1_v5/_case_a_v2_p1 \
  > results/priority_rebuild/ml_phase1_v5/_case_a_v2_p1.log 2>&1 &
disown
```
(P2/P3 同様に K と out-base / tp-hit-predictions パスを差し替え)

### Step I-3.4: merge_step_i_summaries.py 実行 (5 分)
```bash
python scripts/priority_rebuild/merge_step_i_summaries.py
```
出力: `_step_i_merged/phase1_v5_step_i_summary_merged.json` + コンソール §4.1 判定

**動作未検証なので初回エラー時はデバッグ必要**。期待出力:
- `n_combinations: 8`
- method 別 ALL PASS 集計
- `meets_6plus_any_method: True/False`
- `next_action`: "Phase 2 進行" or "Step G Major 統合" or "案 X / 案 Z 検討"

### Step I-3.5: CP4 監査依頼 (30 分・関所 D 必須)
- `/audit` サブエージェント起動
- 監査対象: Step I-3 本走結果 + §4.1 判定 + merge スクリプトの妥当性
- 仕様書 v2.1 §10.2 厳格化判定基準で評価
- まこさん起こさず CC 単独で進める判断は不可 → CP4 監査結果をまこさんにレビュー依頼

### Step I-3.6: セッション終了処理
- lessons L-212+ 追加 (Step I-3 本走結果の教訓)
- WORKFLOW 改訂29 (Step I-3 完了 → 結果別の次タスク確定)
- handoff v30 作成
- git commit (今回未 commit 分を含む全変更)

---

## §4 §4.1 判定結果別の分岐

### 6+ 組合せ ALL PASS (Phase 2 進行可)
- **CC + まこさんレビュー必須** (CC 単独で Phase 2 着手不可)
- Phase 2: Optuna ハイパラ調整 (3-5 日)

### 4-5 組合せ ALL PASS
- Step G Major M2 + M3 統合 → 再 smoke
- まこさん最終判断必須

### 0-3 組合せ ALL PASS
- 案 X (Layer 3 投入) or 案 Z (案 b-f 順次・3-4 週間)
- まこさんレビュー必須

---

## §5 CC 同型バイアス警戒 (累積 49+ 件・本セッション +1: L-211 stdout buffering 軽視)

### 本セッションで新規発覚した同型バイアス
- **L-211**: OS process tree + Bash background の挙動を実装段階で verify せず "Bash run_in_background は detach" と思い込んだ → VS Code 強制終了で 3 並列が SIGPIPE 詰まり
- 教訓: 長時間 background プロセスは **OS 観点で完全 detach 必須** (`nohup` + `disown` + `python -u` + tee 経由禁止)

### 次セッション CC への命令
- **L-211 を I-3.1 再起動時に再読**: 修正後コマンドを必ず採用 (旧パターン禁止)
- **L-210 を Step I-3 結果 verify 時に再読**: smoke で達成済の関所 A ② 0/8 が full でも維持されるか継続 verify
- **L-209 を継続警戒**: §4.1 で「method (a) で 0 件 ALL PASS」だった場合、Major 後送りで Phase 2 進行を CC 単独決定しない
- **L-208 を継続警戒**: full で異常値スメル再ヒット時、原因切り分け順序 (①学習 / ②評価式 / ③データ) を必ず実行
- **cc_role §1.2**: CP4 監査は本走前に必ず通す (CC 単独判定不可)

---

## §6 メタ反省

### 本セッションで建設的成果
- I-2.8 unit test 10/10 PASS (L-207 失敗境界 5 件含む) — 集約ロジックの edge case を test として保護
- I-2.6/I-2.7 §8 verify 完了 — full 走前に基準を確認・許容範囲 (Calibration 12% まで) をまこさん承認済
- I-3.2 16 artifact 生成 — full 走用の time_exit median 確定
- merge_step_i_summaries.py 設計 — §4.1 判定を機械的に集計できる形に
- まこさん向け説明の plain language 励行 (Q1/Q2/Q3 で例え話・専門用語回避)

### CC 改善方向
- background プロセスの起動方法を **L-211 修正後コマンドに固定** (旧パターン禁止)
- 進捗確認は **CPU TIME + mtime + log size の三点** (mtime 単独で判断しない)
- VS Code/claude code 強制終了時の事後 verify を即座に実施 (ハング検出 → kill → 再起動)

---

以上。
