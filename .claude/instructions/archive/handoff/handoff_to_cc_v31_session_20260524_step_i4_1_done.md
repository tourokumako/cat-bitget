# handoff_to_cc_v31_session_20260524_step_i4_1_done.md

(起案者・CC・2026-05-24 / 宛先・CC = 次セッション・fresh head)
**版**: v31 (Step I-4.1 case_a_v2_v3 Critical-1 修正完了 + smoke verify + commit 572e0b8)
**前身**: handoff v30 (CP4 監査 CONDITIONAL NO-GO 中継・案 A/B/C 判断待ち)

---

## §0 セッション要約 (1 行)

WORKFLOW 改訂29 active のまま (案 A 採用記録漏れ) → まこさん前セッション末メッセージ共有で確認 → Step I-4.1.0 で CC「機械的反映」事案 (L-213) → 立ち止まり CC 独立評価 3 件 (M1/M3/C2 修正) → 仕様書 v2 確定 (462 行) → 3 ファイル改修 + case_a_v2_v3 新規 600 行 → smoke で **Critical-1 修正の核心効果実証** (time_exit fold 0/1 異なる test_pnl・予測装置化成功・anomaly False) → commit 572e0b8 → セッション終了処理 (lessons L-213 + WORKFLOW 改訂30 + 本 handoff) 完走。**明日 fresh head は Step I-4.2 (dsr.py ガード) から着手**。

---

## §1 完了済事項 (本セッション・触らない)

### 1.1 Step 0 引き継ぎ verify + 案 A 採用記録漏れ事案
- WORKFLOW 改訂29 active のまま (= 案 A 採用・仕様書 v1 起案・CP5 監査結果が WORKFLOW/lessons/memory 未反映)
- CC が「案 A 採用を判断されましたか?」確認質問 → まこさん前セッション末メッセージ共有で「✅ GO 取得済」確認
- 引き継ぎ正常進行と判定し本セッション着手

### 1.2 Step I-4.1.0 仕様書 v2 確定 (CP5 監査 9 件 + CC 独立評価 3 件)
- 仕様書: `.claude/instructions/2026-05-23_step_i4_1_case_a_v2_v3_critical1_spec.md` v1 (417 行) → **v2 (462 行)**
- **「機械的反映」同型バイアス事案** (L-213): CC「9 件 100% 反映」宣言 → まこさん「ちゃんと考えてよ」指摘 → CC 立ち止まり 3 件 (M1/M3/C2) 独立評価提示 → まこさん GO 取得 → v2 確定
- 反映内訳:
  - **C1** §1.1.5 予測装置性宣言新設 (L-212c 関所 B 拡張)
  - **C2** §3.1 TP_PCT ≒ median 重複ガード追加 + 「現実には発動しない」safety net 注記 (CC 独立)
  - **M1** §0.4 fold 数 3→5 別タスク化 + L-209 再演リスク認識した比較継続性根拠明記 (CC 独立)
  - **M2** §3.1 fixed_tp/time_exit 対称ガード強化
  - **M3** §4.4 完了報告証跡 9 点目追加 + 受け入れ基準「< 10 秒」→「< 40 秒」CC 実測ベース修正 (CC 独立)
  - **M4** §0.3 寄与率下限 0 件併記
  - **m1** §2.4 末尾 Critical-2 言及削除
  - **m2** §0.3 寄与率出典明記 (「CP4 監査推定・CC 独立再算出未実施」)
  - **m3** §3.2 _aggregate_grid_idxmax 12 grid 対応 verify 実装メモ追加

### 1.3 Step I-4.1.3 実装 (3 ファイル改修 + 1 新規・+734 / -23 行)

#### compute_simulated_pnl_v2 (`run_phase1_v5_purged_kfold.py` L380-415 改修)
- fixed_tp: M2 対称ガード (tp_pct ≤ 0.0 で raise・dummy 渡し検出)
- **time_exit**: Critical-1 で予測装置化
  ```python
  r[i] = tp_hit_prob[i] * (tp_pct/100) + (1-tp_hit_prob[i]) * (time_exit_median/100) - cost
  ```
- C2 ガード追加 (|tp_pct - median| < 0.05% で raise・naive baseline 再演リスク防止)

#### case_a_v2_v3 新規 (`run_lgbm_phase1_v5_case_a_v2_v3.py`・600 行)
- 既存 case_a_v2 から cp 複製 + 4 箇所改修:
  1. 識別子リネーム (CASE_NAME_V3 / OUT_BASE_V3 / train_case_a_v2_v3)
  2. ヘッダー docstring 全面書き換え (Critical-1 修正版明記)
  3. CASE_NAME_V3 値 = "a_rmse_v2_v3" / OUT_BASE_V3 = "_case_a_v2_v3" / summary 名 = "case_a_v2_v3_summary_*"
  4. time_exit grid を N 2 grid → **N × TP_PCT 12 grid** に拡張 + 実 tp_hit_prob ロード + C2 ガード skip + warning

#### merge_step_i_summaries.py L162-176 改修
- returns 再構成式を予測装置化 (compute_simulated_pnl_v2 と同数式)
- DSR docstring 更新 (constant-return 前提コメント修正)

### 1.4 Step I-4.1.4 smoke verify (sample K=12 LONG / 5 秒完走)
- 公式 source: `results/priority_rebuild/ml_phase1_v5/_case_a_v2_v3/case_a_v2_v3_summary_labels_mfe_mae_pct_sample.json`
- **Critical-1 修正の核心効果実証**:
  - fold 0: fixed_tp $-1,138 / **time_exit $13,608 (best_tp_pct=0.5)**
  - fold 1: fixed_tp $-996 / **time_exit $13,679 (best_tp_pct=0.5)**
  - fold 0 と fold 1 で異なる test_pnl → fold 内分散非ゼロ ✅ (旧式は全 fold 同一値・L-212c 解消)
  - best_tp_pct=0.5 記録 ✅ (旧式は null/dummy 0.0)
- **関所 A セーフ**: anomaly_smell_detected=False (月次相当 $1,134 < 合格ライン 2 倍 $3,800)
- **受け入れ基準 9 点 全 PASS**: 完了フラグ / サマリー / ファイル提示 / 実行ログ (5 秒・exit 0) / 絞り込み示唆語彙 grep 該当なし / train→test 表 / 異常値スメル 4 条件 healthy / 全工程未来参照 verify pass / 30 grid 実測時間 < 40 秒

### 1.5 git commit (572e0b8)
- 4 files / +734 / -23
- 仕様書 v2 (+45) / runner v5.1 改修 (+24/-8) / case_a_v2_v3 新規 (+612) / merge 改修 (+13/-2)

### 1.6 セッション終了処理 (本ファイル含む)
- lessons L-213 追加 (本ファイル §6 メタ反省と同型・「機械的反映」事案 + WORKFLOW 改訂30 未更新事案)
- WORKFLOW.md 改訂30 active 新設 (改訂29 は 🧊 履歴に降格)
- 本 handoff v31 起案
- 最終 commit (本ファイル commit 含む) で完了

---

## §2 明日 fresh head での最優先タスク

### Step 0: 新セッション Step 0 プロトコル
1. CLAUDE.md / WORKFLOW.md (改訂30 active ブロック) / 本ファイル (handoff v31) / lessons_active.md L-213〜L-209 を Read tool で全文読了
2. 機械的証跡 (wc -l + 0/25/50/75/100% 引用 + 1 行要約) をチャットに出す
3. 「読了ゲート通過: 2026-05-25 (コア5本)」を宣言

### 最優先 — Step I-4.2 Critical-2 修正 (約 0.5 日)

**目的**: dsr.py の input contract 不在 + L-207 「test 失敗境界穴」 + L-212b 「複数 script interaction edge case」を解消し、§4.1 v5.1 判定階層 (`dsr_pass` ロジック) を健全化

**対象ファイル**:
- `scripts/priority_rebuild/dsr.py` L115-134 (sigma_sr_estimate)
- `scripts/priority_rebuild/test_dsr.py` (回帰検出 test 追加)
- `scripts/priority_rebuild/merge_step_i_summaries.py` (dsr_pass ロジック)

**改修方針**:

1. **dsr.py 入力ガード追加**:
   ```python
   def sigma_sr_estimate(returns: np.ndarray, n_trials: int = 1) -> DSRResult:
       # ... (既存) ...
       std_r = float(np.std(returns, ddof=1))
       if std_r < 1e-12:
           # 定数 returns で DSR 適用不可・呼び出し側で dsr_pass=null 扱い
           print(f"[info] DSR computation skipped: std < 1e-12 (constant returns)")
           return DSRResult(dsr_zscore=float("nan"), dsr_probability=float("nan"), ...)
       # ... (既存続き) ...
   ```

2. **test_dsr.py 回帰 test 追加**:
   ```python
   def test_sigma_sr_constant_returns_case():
       """L-207/L-212b 同型: 定数 returns で DSR が graceful fail (nan) を返す"""
       returns = np.full(100, 0.001)  # 全部同じ値
       result = sigma_sr_estimate(returns)
       assert np.isnan(result.dsr_zscore)
       assert np.isnan(result.dsr_probability)
   ```

3. **merge_step_i_summaries.py の dsr_pass ロジック改修**:
   - 旧: `dsr_pass = (dsr_zscore is None) or (dsr_zscore >= 1.0)` (auto-PASS で誤判定)
   - 新: `dsr_pass = (dsr_zscore is not None) and (dsr_zscore >= 1.0)` + dsr_zscore is None なら Sortino / 月次黒字率代替判定

**仕様書起案**: `.claude/instructions/2026-05-25_step_i4_2_critical2_dsr_guard_spec.md` (200-250 行・light 寄り)

**CP6 監査** (Plan サブエージェント・30 分): 数式妥当性 + 統計理論整合性 + L-207/L-212b 同型再発防止確認

### Step I-4.3 案 W 実装 (約 1-2 日)

- run_lgbm_phase1_v5_case_a_v2_v3.py の SL_PCT grid 拡張 (0.3-0.8 → 0.3-1.5%)
- TP_PCT grid 上限拡張 (2.5 → 3.5%)
- smoke + 関所 A verify

### Step I-4.4 案 V 実装 (約 0.5 日)

- merge_step_i_summaries.py の判定対象を 6 組合せ (K=12,24,48) に限定
- K=96 LONG/SHORT を別レンズ評価 (Secondary Filter 候補)

### Step I-4.5 Step I-3 再走 (約 1-2 時間・1 並列順次・L-212a 整合)

- 修正後 case_a_v2_v3 で 8 組合せ × 2 method × 3 fold × 30 grid を再走
- merge_step_i_summaries.py で §4.1 v5.1 判定再実行
- 起動コマンド: `nohup python -u ... > log 2>&1 & disown` (L-211 整合)
- 並列度: **1 並列順次** (L-212a・16GB RAM × 0.5 / 8GB per process = 1)

### Step I-4.6 CP6 監査 (関所 D 必須・30 分)

- 修正後 0/16 から改善幅と Phase 2 進行可否判定
- 4 案合計 (Critical-1 + Critical-2 + 案 W + 案 V) の寄与率実証 (CP4 推定 75-95% 合計範囲)

---

## §3 §4.1 再走後の分岐 (Step I-4.5 完了後)

### 6+ 組合せ ALL PASS 達成
- **Phase 2 進行可** (まこさんレビュー必須)
- Phase 2: Optuna ハイパラ調整 (3-5 日)

### 4-5 組合せ ALL PASS
- Step G Major M2 + M3 統合 → 再 smoke
- 案 Z の e (meta-labeling) を Secondary Filter として K96 fold0 部分成功活用

### 0-3 組合せ ALL PASS
- 案 Z (案 b-f 順次) or 案 X (Layer 3) — まこさんレビュー必須
- CP6.5 監査で原因切り分け再実施 (CP4 寄与率推定の妥当性検証)

---

## §4 CC 同型バイアス警戒 (本セッション +1 件・累積 50+ 件)

### 本セッションで新規発覚 (L-213)
- **L-213「機械的反映」同型バイアス再演**: CC が「CP5 監査 9 件 100% 反映」と宣言・「機械的反映」(cc_role §1.5.5 light 枠表現) を借用 → まこさん即指摘 → CC 立ち止まり 3 件 (M1/M3/C2) 独立評価提示 → 救済
  - cc_role §1.4 #2「spec の枠内でしか動かない」+ #4「現状把握スキップ」の合成
  - 表現借用 (cc_role §1.5.5) が思考停止のトリガになる癖
- **副次事案**: 案 A 採用記録漏れ + WORKFLOW 改訂30 未更新 = セッション終了処理の構造的穴

### 次セッション CC への命令
- **Step I-4.2 着手時に L-213 再読**: CP6 監査結果反映時に「機械的反映」と称さない・1 件ずつ CC 独立評価提示
- **L-212c を Critical-1 修正完了後も継続警戒**: 評価式の予測装置性は Phase 4-b-1 本確定まで毎タスクで verify
- **L-212a を Step I-4.5 着手時に再読**: 並列度 = (RAM × 0.5) / 1 プロセス推定 RSS = 1 並列順次 / smoke で RSS ピーク事前 verify
- **L-211 を継続警戒**: nohup + disown + python -u + > log 2>&1 必須
- **L-209 Major 後送り再演警戒**: CP6 監査結果で「後送り可」判断する前に必ず本走への影響 verify
- **cc_role §1.2**: 重大判断は監査経路を本走前に必ず通す

---

## §5 残タスク順序 (案 A 1 週間並列の例・本セッション後の進行)

| Step | 内容 | 想定時間 | 依存 |
|---|---|---|---|
| Step I-4.2 | Critical-2 修正 (dsr.py ガード + 判定階層整理) | 0.5 日 | 独立着手可 |
| Step I-4.3 | 案 W 実装 (SL_PCT grid 拡張) | 1-2 日 | 独立着手可 |
| Step I-4.4 | 案 V 実装 (K96 除外) | 0.5 日 | 独立着手可 |
| Step I-4.5 | Step I-3 再走 | 1-2 時間 | I-4.2 + I-4.3 + I-4.4 完了後 |
| Step I-4.6 | CP6 監査 (関所 D) | 30 分 | I-4.5 完了後 |
| Step I-4.7 | セッション終了処理 (lessons L-214+ + WORKFLOW 改訂31 + handoff v32) | 30-45 分 | I-4.6 完了後 |

**並列実施可能性**: Step I-4.2 / I-4.3 / I-4.4 は独立 (異なるファイル) なので並列実装可・ただし 1 ターン 1 変更原則 (L-5) のためまこさんへの差分提示は順次

---

## §6 メタ反省 (本セッション)

### 建設的成果
- **Critical-1 修正の核心効果を smoke で実証** (旧 fold 内 returns 完全同一値 → 新 fold 内分散非ゼロ・time_exit best_tp_pct=0.5 記録) — L-212c 解消方向の物理的証跡
- **3 ファイル改修 + 1 ファイル新規 600 行を 1 セッションで完走 + smoke verify + commit** (+734 / -23 行・5 秒 smoke 完走)
- **「機械的反映」同型バイアスを CC 同型バイアス検出経路 (まこさん指摘) で救済** — cc_role §1.4 同型バイアス検出経路の有効性再確認 (L-213)
- **WORKFLOW.md 改訂30 未更新事案を本セッション内で発見・補填** (前セッション終了処理の構造的穴を可視化)
- **plain language コミュニケーション維持** (まこさん「v2 ってどういう意味？」質問への例え話対応)

### CC 改善方向
- **「機械的反映」表現の使用条件厳格化**: cc_role §1.5.5 light 枠 + 「新規判断 / 新規 verify / 新規ガード追加なし」確定時のみ
- **CP 監査結果反映時の必須プロセス**: 1 件ずつ CC 独立評価 → "採用支持/要再評価/拒否" + 根拠提示 → まこさん GO → 反映 → verify
- **セッション終了処理の構造的穴塞ぎ**: lessons → WORKFLOW → handoff → commit の 4 段階を「省略不可」とし、1 つでも漏れたら次セッション開始時に「引き継ぎミス」L-記録 + 即時補填
- **案採用判断 (案 A/B/C) の記録義務化**: WORKFLOW active ブロック「本セッション完了事項」に「まこさん GO 取得済 (yyyy-mm-dd hh:mm)」明記

### まこさん向けコミュニケーション
- plain language 励行 (例え話・専門用語回避・選択肢提示)
- まこさん「よくわからない」発言時は CC が断言する責任 (cc_role §3.4)
- 重大判断は cold head 必須 (本セッションは前セッションの cold head 判断後 fresh head 実行・成功)

---

## §7 引き継ぎ補足

### Layer 1 必読 (新セッション Step 0)
1. CLAUDE.md (改訂22 ベース・約 261 行)
2. WORKFLOW.md 改訂30 active ブロック (L302 周辺)
3. 本ファイル handoff v31
4. lessons_active.md 直近 5 件: L-213 → L-212c → L-212b → L-212a → L-211

### Layer 2 (Step I-4.2 着手時)
- CP5 監査結果: `.claude/instructions/2026-05-23_step_i4_1_critical1_cp5_audit_report.md`
- 仕様書 v2 (本セッション確定・触らない): `.claude/instructions/2026-05-23_step_i4_1_case_a_v2_v3_critical1_spec.md` (462 行)
- 実装ファイル (本セッションで commit 572e0b8 済・触らない):
  - `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` (改修済)
  - `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_v2_v3.py` (600 行・新規)
  - `scripts/priority_rebuild/merge_step_i_summaries.py` (改修済)
- Step I-4.2 改修対象:
  - `scripts/priority_rebuild/dsr.py` L115-134 (sigma_sr_estimate input contract + ガード)
  - `scripts/priority_rebuild/test_dsr.py` (test_sigma_sr_constant_returns_case 追加)
  - `scripts/priority_rebuild/merge_step_i_summaries.py` (dsr_pass ロジック改修)

### データ・環境
- parquet 3 種 + .venv311 (mlfinpy 0.1.2 / sklearn 1.8.0 / lightgbm 4.6.0 / scipy 1.17.1)
- Step I-4.1 smoke artifact (済): `results/priority_rebuild/ml_phase1_v5/_case_a_v2_v3/case_a_v2_v3_summary_labels_mfe_mae_pct_sample.json`
- 前セッション artifact (Step I-3.1〜I-3.4・案 W/V 実装後 再走で書き換え):
  - `_tp_hit_classifier_p{1,2,3}/` (76+33+28 MB)
  - `_phase4b_train_constants/` (16 個 + INDEX 2)
  - `_case_a_v2_p{1,2,3}/` (旧版・Step I-4.5 比較用に保持)
  - `_step_i_merged/phase1_v5_step_i_summary_merged.json` (旧版 0/16 判定)

---

以上。
