# lessons_active.md — 現役教訓 (2026-05-02 以降・L-203〜L-153 + 新規 L-206 以降)

> **構造 (2026-05-22 改訂22 で再整理)**:
> - active = 2026-05-02 以降の教訓 (L-206〜L-153 + 新規追加 L-207 以降・約 1320 行)
> - [archive](lessons_archive.md) = L-152 以前 (2026-05-01 以前の Phase 1〜7-a / regime 研究時代教訓・約 2515 行)
> - **Step 0 では active 直近 5 件のみ全文読了で十分**。残りは必要時参照。

---

### L-211: VS Code 強制終了で background `tee` 経由プロセスが SIGPIPE 詰まりで 2 時間半ハング — Step I-3.1 3 並列実行事案 (2026-05-23)

**何が起きたか:**
Step I-3.1 (tp_hit_classifier --full 3 並列) を `python ... 2>&1 | tee log_file | tail -50` パターンで `Bash run_in_background=true` 起動。約 2 時間半後 (07:30 JST) にまこさん起床して状況確認したところ、3 プロセス全てが CPU TIME = 5:30 のまま停止 (起動から 2:44 経過しているのに 5 分の CPU time のみ蓄積)。output ファイル mtime も 04:46 のまま更新なし (= "RUN START" の 58 byte のみ)。

VS Code 強制終了 (まこさん操作) で **tee コマンドが kill** され、Python の stdout (pipe で tee に書く側) が **SIGPIPE 詰まり** (= reader 不在で write block) で凍結したと推定。Python は最初の 5 分 (parquet load + 初期処理) は CPU 使用したが、stdout を tee に大きく書こうとした時点で永久ブロック。

**Why:**
- `python ... 2>&1 | tee log | tail -50` の pipe chain は VS Code の terminal セッション (= claude code Bash の親プロセス) に依存する構造だった
- VS Code 強制終了 → terminal セッション kill → tee/tail kill → Python の stdout の reader が消失 → Python は write block (デフォルトは SIGPIPE で terminate するが、claude code の Bash 内で何らかの handle が SIGPIPE を block していた可能性)
- nohup していない・disown していない・`python -u` (unbuffered) でもないため、stdout buffer が満ちると write が block する条件が複数重なっていた
- 「Bash run_in_background は OS から detach されている」と思い込んでいたが、実際は claude code セッションの subprocess group に紐付いていた

**How to apply:**
- **長時間実行 background プロセスは VS Code 強制終了から守る** ため、以下 3 点セットを必須化:
  1. `python -u` (unbuffered stdout = SIGPIPE 詰まり回避 + 早期 flush で進捗可視化)
  2. `> log_file 2>&1` (tee 経由禁止 = 中継 process 不在で詰まらない)
  3. `nohup ... & disown` (親プロセス死亡から完全独立 = OS init 親に re-parent)
- **進捗診断は output mtime ではなく CPU TIME で確認**: `ps aux` の TIME 列が経過時間と乖離 (例: 経過 2 時間で CPU TIME 5 分) なら write block 強疑い
- **VS Code/claude code 強制終了時の事後 verify**: まこさん操作で session 終了した場合、即座に 3 並列プロセスの CPU TIME と mtime を確認し、ハング検出時は kill して再起動
- **再起動時の判定**: 既に書かれた output が < 100 byte ならゼロから再起動・> 1MB なら resume 可能性を検討 (今回は < 100 byte で全 kill 妥当)
- **claude code 仕様の理解修正**: Bash `run_in_background=true` は claude code セッションに紐付くため、claude code/VS Code 終了で death の可能性あり。**真の detach は `nohup ... & disown` が必要**

**関連:**
- L-203 / L-201 「外部ライブラリ・OS 挙動の実態調査不足」シリーズ (本件は OS process tree + claude code Bash の挙動)
- L-205 / L-200 「機械的証跡」シリーズ (本件で「output mtime のみで生死判断」誤りに気付かず 2 時間半放置)
- cc_role §1.0 業界知見能動活用 (本件後の修正で nohup + disown + python -u を Best Practice として導入)
- false_positive §2 類型 G (虚偽報告) を防ぐ意味で「進捗確認は CPU TIME + mtime + log size の三点」を明文化
- 修正後の Step I-3.1 起動コマンド: handoff v29 §3 参照
- 公式 source: 04:46 起動 → 07:30 ハング検出 / kill 完了 / memory 6.5GB 解放

---

### L-210: Phase 4-b 前倒し評価式実装で smoke 関所 A ② 0/8 達成 — Step I 設計が機能している定量実証 (2026-05-23)

**何が起きたか:**
L-208 で「評価式の暫定過大評価」が Step H 異常値スメル 6/8 ヒットの主因 (7-8 割支配) と判定された。CP3 監査で案 Y (Phase 4-b 前倒し設計) 採用が確定。本セッション (2026-05-23 同日続編) で Step I-1 仕様書 v2 + v2.1 確定 → CP3.5 監査で Critical 2 + Major 5 + Minor 4 指摘 → 全件反映で v2.1 → I-2.1〜I-2.4 順次実装 → smoke で **anomaly_smell_detected: False (0/8 達成)** を確認した。

具体数値 (sample K=12 LONG / 2 fold):
- 旧式 K=12 LONG max month_pnl = $4,298 (関所 A ② ヒット)
- 新式 fixed_tp method test_pnl_year = $-1,138 〜 $-4,296 (月次相当 $-95 〜 $-358)
- 新式 time_exit method test_pnl_year = $-2,061 (月次相当 $-172)

「3 重楽観仮定 (TP 約定率 100% + slippage 0 + TP 価格 = MFE ピーク) を取り除いた評価式は smoke で正直に赤字を出した」が、これは Step I の核心目標 (= 評価式が現実的な値を返す状態) の達成を意味する。

**Why:**
- 旧式 `pred_MFE/100 - cost` 設計は TP 約定率 100% × TP 価格 = MFE ピークの 3 重楽観仮定を内包し、Step H で K=96 SHORT $84,185/月 (合格ライン $1,900 の 44 倍) を出していた
- 新式 `compute_simulated_pnl_v2` (`run_phase1_v5_purged_kfold.py` L319-449) は:
  (a) tp_hit_prob (Classifier 出力 0-1 確率) で TP 約定率を重み付け
  (b) 固定 TP_PCT (定数) で TP 価格を pred_MFE 由来から切り離し (3 重楽観 (1)(3) 物理的解消)
  (c) method (fixed_tp / time_exit) 2 並列で sim_pnl 計算
- CP3.5 監査で論理破綻 (C1 trailing 数式) + pred_MFE 残存 (C2) を本走前 blocker として指摘・全件反映 → 評価式が「正直」に動作するようになった
- smoke の sample 89 日 / 2 fold / 浅学習でも関所 A ② 達成 = 設計の方向性が正しい

**How to apply:**
- **設計修正の効果は smoke 段階で観察可能な指標で verify する**: 関所 A 4 条件 (異常値スメル) は full 期間 / 多 fold を待たずに smoke で初動 verify できる・Step I の方向性確認に活用
- **monitoring 指標として「異常値スメル件数」を継続採用**: anomaly_smell_detected=False が Step I-3 本走 (full 4 年 / 5 fold) でも維持されれば「評価式信頼性回復」達成 → Phase 2 進行判定の前提が整う
- **smoke 赤字 = 設計が機能していない、と誤読しない** (L-208 整合): smoke で全 method 赤字でも、これは「3 重楽観仮定なしで sample 89 日では TP 約定率 30% × TP 0.5% では cost を回収できない」という正直な計算結果。full 4 年で TP_hit_prob が安定して高くなる組合せ (K=96 SHORT 等の高ボラ trade) で改善期待
- **「異常値スメル 0/8 達成 = 合格」ではない**: §8.1 関所 A 達成は評価式信頼性回復の前提条件・本来の合格判定 (§4.1 v5.1 6+ 組合せ ALL PASS) は別軸。Step I-3 本走で再評価

**関連:**
- L-208 評価式暫定過大評価 (本件で解消・直接的解決の実証)
- L-209 Major 後送り判断 (本セッション CP3.5 で全件反映 → 再演阻止)
- L-207 test カバレッジ穴 (本件で unit test 5/5 PASS で再演防止)
- cc_role §1.5 (CP3.5 監査推奨を CC 単独判断で却下せず全件採用 → 物理的に L-209 阻止)
- 仕様書 v2.1: `.claude/instructions/2026-05-23_phase4b_forward_design_spec.md` (612 行)
- 実装 (4 ファイル):
  - run_tp_hit_classifier.py (684 行・I-2.1)
  - compute_phase4b_train_constants.py (458 行・I-2.2)
  - run_phase1_v5_purged_kfold.py (873 行・I-2.3 で compute_simulated_pnl_v2 追加・unit test 5/5 PASS)
  - run_lgbm_phase1_v5_case_a_v2.py (597 行・I-2.4・新規・既存 case_a 保護)
- 公式 source: `results/priority_rebuild/ml_phase1_v5/_case_a_v2/case_a_v2_summary_*.json` (smoke 結果・anomaly_smell_detected: false)

---

### L-209: CC 同型バイアス「Major 後送り判断」= 自分で範囲狭めて OK 判定する癖の再演 (CP3 監査で発覚・2026-05-23)

**何が起きたか:**
Step G CP2 監査 (2026-05-22) で Critical 2 件 + Major 4 件が指摘された。CC + まこさん相談で「Critical 2 件のみ対処 → Step H 本走へ」を採用。Major 4 件は「Step H 結果見てから判断」とした。Step H 完走後の CP3 監査で、Major 4 件のうち M2 (案 a で `entropy_lift=NaN → 自動 PASS` の判定骨抜き) と M3 (importance dominance 50% threshold 緩さ + merge_asof boundary verify 不在) は本走前に対処すべきだったと判定された。

**Why:**
- L-207「test カバレッジが合格境界のみで失敗境界を含まないと bug 素通り」と同型構造
- L-207 は「test 範囲を自分で狭く区切って合格判定」
- 本件は「Major 範囲を自分で『後送り可』と区切る」
- cc_role §1.4 #2「spec の枠内でしか動かない」(Critical/Major の線引き spec を CC 自身が下している) + #4「現状把握をスキップ」(M2 の判定骨抜きが本走 sim_pnl 異常値解釈に直接影響することを Step G 時点で確認しなかった) の合成
- 関所 G「チェックリスト有効性検証ループ」が起動しなかった
- 「Critical/Major のどちらが本走 blocker か」を CC が単独判断する構造そのものが同型バイアスを内包

**How to apply:**
- **監査結果の Major 後送り判断は CC 単独で確定しない**: Critical 対処後の再監査経路 (CP2.5 / CP3) を本走前に挟む or Major 各件について「本走への影響」を独立評価者に判定させる
- **判定骨抜き系の指摘 (M2 同型) は Major でなく Critical 扱い**: 評価指標が NaN/自動 PASS になる構造は実質的に判定欠陥・本走前に必ず修正
- 「Major は結果見てから」の判断パターンが出たら **自動的に L-209 再演警戒を起動**・関所 G に統合
- false_positive §5 関所 G の文言「すり抜けるたびに穴を塞ぐ」を CP2 監査結果に対しても適用する (Critical 漏れ・Major 後送りの両方を「すり抜け」と扱う)

**関連:**
- L-207 (test カバレッジ穴・同型構造)
- L-200 / L-204 / L-205 (実装 verify と documentation の乖離シリーズ)
- L-206 (Z 案ガード・defense-in-depth 維持)
- cc_role §1.2 (監査経路を CC 自己判断で進めたい時こそ通す)
- cc_role §1.4 #2 #4 (同型バイアス)
- false_positive §5 関所 G (チェックリスト有効性検証ループ)
- Step G CP2 監査 (commit `de709a5` Critical 対処) + CP3 監査 (本セッション末)
- 公式 source: [phase1_v5_summary_merged.json](../../results/priority_rebuild/ml_phase1_v5_step_h_merged/phase1_v5_summary_merged.json) (Step H 本走結果)

---

### L-208: 評価式が暫定段階で出た「異常値スメル」を学習不良と取り違える危険 — Step H 本走 6/8 組合せ ② ヒット事案 (2026-05-23)

**何が起きたか:**
Step H 本走 (full parquet × 8 組合せ × 5 fold = 80 学習) 完走後の merge で、8 組合せ中 6 件で関所 A 異常値スメル ② (月次 NET > $3,800) がヒット。最悪 K=96 SHORT で月次 $84,185 = 合格ライン $1,900 の **44 倍**。CC は当初「学習が leak/overfit している可能性」と「評価式が暫定的に過大評価」の両仮説を提示し、CP3 監査経路で判定を依頼。

CP3 監査結果: **仮説 B (評価式の暫定過大評価) が 7-8 割支配・A (学習不良) は 2-3 割重畳**。決定的根拠:
- `compute_simulated_pnl` (`run_phase1_v5_purged_kfold.py` L295-316) は `return = pred_MFE/100 - 0.033% cost` を全 trade で計上
- K=96 SHORT fold 1: 26,098 trade × 平均 3.23%/trade = return 累計 841 倍 → notional $1,200 × 841 = $1,010,219/年 = 数学的必然
- 「TP 約定率 100% + slippage 0 + TP 価格 = MFE ピーク価格」の 3 重楽観仮定の帰結
- train_rmse / valid_rmse / label_std 比 (W1/W2 警告) は閾値内 → leak 同型 (L-179 fractal) なら train_rmse/label_std が極端に低くなるが、その兆候なし
- LONG vs SHORT 非対称 (K=96 で 157 倍乖離) は学習データ期間 (2022 LUNA / FTX / 2024-04) に SHORT 大相場期間が複数あった市場特性で説明可能・leak でない

**Why:**
- cc_ml_design_spec.md §1.5.1 v5.1 自身が「**本確定は Phase 4-b-2**」と明記している通り、Phase 1 の `return = pred_MFE - cost` 計算は **設計上の暫定段階**
- TP 約定率モデル + 実 Exit 価格モデルは Phase 4-b 着手後に組込み予定
- 暫定段階で発生する「異常値スメル」を「学習不良」と即断定して Layer 3 (CPCV + Focal loss + アルゴ多様化) に飛ぶと、評価式が同じため新アルゴでも同型異常値が出る → 投資対効果なし
- §1.5.1 v5.1 撤退ライン文言「6 案いずれも 6+ 組合せ ALL PASS なし → 即 Layer 3」は「学習方法を変えても合格不可」前提で書かれた条項・**評価式暫定段階の今は前提が崩れているため文言そのまま適用は誤読**

**How to apply:**
- **異常値スメル発火時の原因切り分け順序を必須化**: ① 学習 (leak/overfit)・② 評価式 (暫定仮定)・③ データ (regime 過依存) のどれが支配的かを判定してから次アクションを選ぶ
- **判定基準** (CP3 監査整理):
  - train_rmse / label_std 比が異常に低い (例: < 0.3) → leak 強疑い (類型 A)
  - W1/W2 警告閾値超え → overfit 疑い (sample 小データ由来含む)
  - LONG/SHORT 非対称が市場期間特性で説明可能 → 評価式問題
  - sim_pnl_year_usd を notional × return_sum に分解して 「1 trade あたり mean return」が pred_MFE 中央値オーダーで一致 → 評価式問題確定
- **撤退ライン文言の解釈基準**: 撤退ラインは「学習方法変更で合格不可」を前提とした条項。評価式が暫定段階で発火した不合格は「評価式直してから再判定」が正しい順序・spec 文言を機械的適用しない
- **Phase 4-b 前倒し設計の判断トリガ**: Phase 1 で異常値スメル ② (sim_pnl 過大) が 4+ 組合せでヒット = 評価式暫定性が学習評価を歪める閾値と判定 → Phase 4-b の TP 約定率モデル + 実 Exit を Phase 1 評価式に前倒し組込み

**関連:**
- L-206 (Z 案ガード・物理 verify 経由続行で defense-in-depth 維持)
- L-207 (test カバレッジ穴・同セッションで dsr bug 発見)
- L-209 (Major 後送り判断の同型バイアス・本件と並行発覚)
- Step G CP2 監査 C2 (c)「pred_MFE/100 returns 設計の暫定性 = 関所 C 同型問題」予測 → 本走で実証
- cc_ml_design_spec.md §1.5.1 v5.1 + §1.6 撤退ライン + §3 Exit 設計
- phase_flow_v4_with_recovery.md L528 (Phase 4-b-2 仕様)
- phase_compliance_checklist.md §4b.4 + §4b.4-b (TP 約定モデル基準)
- false_positive §5 関所 A (異常値判定基準・C (NET の実体 verify))
- 公式 source: [phase1_v5_summary_merged.json](../../results/priority_rebuild/ml_phase1_v5_step_h_merged/phase1_v5_summary_merged.json) (8 組合せ統合・anomaly_smell_detected: true)

---

### L-207: test カバレッジが「合格境界」のみで「失敗境界」を含まないと bug が素通りする — dsr.py L119 式 bug 事案 (2026-05-22)

**何が起きたか:**
Step F 本走 smoke 1 回目 (sample 5 fold) で `dsr.py` `sigma_sr_estimate` が `ValueError: sigma_SR denominator non-positive (-0.194571)` で crash。fold 3 で SR=4.19・skew=0.74・excess_kurt=1.44 → `inner = 1 - skew·SR + (excess_kurt - 1)/4 · SR² = -0.195`。

調査の結果、`dsr.py` L119 の式 `(excess_kurt - 1.0) / 4.0` は **Bailey-Lopez de Prado 2014 / Mertens 2002 の正本形式 `(γ₄ - 1)/4` の γ₄ が「総 kurtosis」(Pearson β₂・Gaussian で 3) を前提**にしているが、`dsr.py` は `scipy.stats.kurtosis(fisher=True)` (= excess kurt・Gaussian で 0) を渡しており、パラメータと式がミスマッチ。Gaussian (excess_kurt=0) で `(0-1)/4 = -0.25` → `inner = 1 - 0 - 0.25·SR²` → **SR > 2 で常に負値** (= 分散として不成立)。Lo (2002) closed form `Var(SR̂) = (1 + 0.5·SR²)/T` と一致しない。

修正: `(excess_kurt + 2.0) / 4.0` (等価: `total_kurt = excess_kurt + 3 → (total_kurt - 1)/4 = (excess_kurt + 2)/4`)・Lo (2002) と一致確認。test 10/10 PASS 維持・smoke 再走で 1.3 分完走。

**Why:**
- `test_dsr.py` の Gaussian ケース (`test_sigma_sr_normal_distribution_case`) は **SR=1 でのみ test**。`inner = 1 - 0.25·1² = 0.75 > 0` で PASS してしまい、SR > 2 の失敗境界をテストしなかった
- `test_paper_eq5_eq9_extreme_case` (SR=2.5・skew=-3・excess_kurt=10) は **大きな負 skew が inner を救う特殊ケース** (1 + 7.5 + 2.25·6.25 = 22.56 で正値) → bug を素通り
- 「10/10 PASS」を実装 verify 証跡として WORKFLOW.md / handoff に記載していたため、本走 smoke crash 前に bug を検出できなかった
- L-200 機械的証跡 3 点 (wc -l + Read + 該当行引用) は守られていたが、「test 内容自体の妥当性」を verify する手続きが欠落していた

**How to apply:**
- **数値式の test は「失敗境界 (raise する境界)」を必ず含める**:
  - 例: dsr.py なら Gaussian 連続入力 (SR=0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0) で sigma が単調増加することを assertion
  - 「raise しない正常境界」だけでなく「raise する異常境界」の両方を test に書く
- **「test PASS」を bug 不在証跡として引用する前に test カバレッジを目視確認**:
  - 引数の取りうる範囲のうち test 済範囲を 1 行で要約
  - 範囲外で raise が想定される値 (= 失敗境界) があるかチェック
- **業界既知の closed-form (Lo 2002 等) と数値一致 sanity check を sanity test として追加**:
  - 数式実装の test は paper の hand-derivation だけでなく、独立 closed-form (簡単な特殊例) で cross-check
  - dsr.py で言えば Gaussian (skew=0, excess_kurt=0) で `sigma = sqrt((1 + 0.5·SR²)/(T-1))` と一致するか
- **連動策**: cc_role §1.0「業界知見能動活用」を「test 設計時にも適用」 — Lo (2002) を WebSearch すれば変数定義の誤解 (excess vs total) は事前に気付けた可能性が高い

**関連:**
- L-180 / L-200 / L-204 / L-205 「実装 verify と documentation の乖離」シリーズ (本件は test 内容自体の乖離・新規 layer)
- L-206 (本セッション・smoke crash で発覚した連鎖事象)
- cc_role §1.0 (業界知見能動活用)
- false_positive §2 類型 E (計算ミス)・§5 関所 G (チェックリスト有効性検証ループ)
- 修正 commit: pending (本セッション末)
- 公式 source: [phase1_v5_summary.json](../../results/priority_rebuild/ml_phase1_v5/phase1_v5_summary.json) (smoke 再走後・2026-05-22T22:55:00)

---

### L-206: ブラックリストガードを保守一辺倒で運用すると false positive で物理進行不能になる — Z 案 (物理 verify 経由続行) 改訂で defense-in-depth 維持 (2026-05-22)

**何が起きたか:**
2026-05-22 セッション後半 (Phase 1 v5.1 案 a smoke 実行中) で phase_compliance §1.4 ブラックリストガード (`dist_to_fib_v2_*` / `resistance_distance_*` / `support_distance_*` / `nearest_level_*` 4 パターン) が発動・top1-20 hit で `sys.exit(1)` で停止。CC は 2 仮説 (leak 残存 / false positive) を立て、Plan エージェント独立監査 + 物理 leak verify 4 項目セット (lag-1 shift 不変性 + 末尾 K bars NaN + 二重 N サフィックス内外一致 + importance dominance) を実装・実行。

sample 89 日 4 件 + full 4 年 1 件 (support_distance) 計 5 件で全 4 verify PASS。さらに **sample で top20 入りした 4 件は full では top20 外** = sample レジーム過依存 (類型 D 時代依存) と確定。一方 phase_compliance §1.4 旧運用「ブラックリスト緩和は実施しない・top1-20 hit 即停止」では false positive (本物の強い予測子) でも sys.exit され Phase 1 全 8 組合せ × 6 案実装が物理的に進行不能になる構造問題があった。

Z 案 (改訂後運用) を確定:
- (a-1) hit 検出 → 物理 verify 4 項目セット **全 PASS** → 警告ログ + `full_rank.csv` 記録 + 続行可
- (a-2) **1 項目でも FAIL/SKIP** → 即停止 sys.exit(1)・調査必須
- (b) top21-50 hit / (c) top51以下 は旧運用継続
- ブラックリストパターン自体の緩和は実施しない (将来回帰検出機能維持・defense-in-depth)

**Why:**
- ブラックリストガード設計の初期意図は「L-179 fractal leak 再発検知の保守」(2026-05-13)
- ただし「false positive (= 本物の強い予測子) でも一律 sys.exit」は **業界知見と整合する強い予測子の学習を完全に封じる** 副作用がある
- sample 89 日のような **短期間データ単独で「top20 入り → leak 残存疑い」と判定** するロジックは類型 D regime 過依存を検出できず・full 4 年で別の特徴量に置き換わる前提を持っていなかった
- L-179 当時の防衛は妥当だったが、運用期間 9 日 (2026-05-13 → 2026-05-22) で false positive 事象に直面 → 物理 verify 経路で安全に通す改訂が必要

**How to apply:**
- **ブラックリストガードは「停止 vs 緩和」の二択でなく「物理 verify 経由続行」を選択肢に加える** (false_positive §5 関所 G「すり抜けるたびに穴を塞ぐ」整合)
- 新規 verify ロジック実装時の **TF-aware (MTF resampling 自然挙動考慮)** 設計義務化:
  - 5m bar 単位で MTF (1h/4h 等) 特徴量を扱う場合、lag-1 shift 不変性の expected pct_diff = bar_minutes / TF_minutes (例: 4h → 5/240 = 2.08%)
  - 単純「95% 以上変化で PASS」判定は 5m TF のみに妥当・MTF 非対応で false WARN を出す
- 監査エージェント (Plan) を **自己判断で進めたくなった時こそ通す** (cc_role §1.2)・本セッション初期に CC は (γ) ガード OFF を独断提案し監査経由で軌道修正できた
- 異常値スメル smoke 結果 (sharpe=6.417・sim_pnl=$8689/年 / fold 1 のみ) は短期間 (sample 89 日・n_estimators=30 浅学習) 由来のため統計的有意性なし・本走 (full parquet 5 fold) で再評価必須
- ブラックリストパターン自体の緩和 (除外) は実施しない (将来の真の leak 再混入時の検出機能維持)

**関連:**
- L-179 fractal j±2 leak (本ガード設計の起源・2026-05-13)
- L-180 ドキュメント引用前 実装 verify (本件で監査経由 verify 完了)
- L-200 機械的証跡 3 点 (本件で物理 verify 4 項目 + JSON 保存で適用)
- L-205 早計自己申告 (本件初期 CC が「γ ガード OFF」を独断提案して監査で軌道修正・同型バイアス)
- false_positive_incident_policy §0-1 Prime Directive / §2 類型 A / §5 関所 G
- phase_compliance_checklist §1.4 (2026-05-22 Z 案改訂・3 段階運用)
- 新規ツール: `scripts/priority_rebuild/verify_top20_features_leak.py` (物理 verify 4 項目 + TF-aware lag-1)

---

### L-205: ドキュメント引用前 実装 verify 漏れ + 早計自己申告 — L-180 同型再演 (2026-05-22)

**何が起きたか:**
2026-05-22 セッション (Phase 1 v5 §6 Step 3 案 a 設計議論) で、まこさん Q1「Entry 判定の閾値 1.5 の根拠」に対し、CC は cc_ml_design_spec §2 を grep で確認し「閾値は学習データからデータ駆動で決定 (人間が事前に決めない)」記述を発見 → 「**1.5 は CC 独断値・cc_ml_design_spec §2 と矛盾・修正必要**」と早計自己申告した (cc_role §1.3.4 発見時自己申告義務に基づく即時報告)。

しかしまこさんから「念のため learning_design_v4 / phase_flow_v4_with_recovery / technical_analysis_knowledge_base を読んでみて」と指示を受け、3 ファイル grep + Read 後に **phase_flow_v4_with_recovery.md L151 に「予測 MFE / 予測 MAE ≥ 1.5 で買う・改善期待しない・比較用ベースライン」と明示記載**されていることが判明。1.5 は CC 独断値ではなく phase_flow_v4 既定値で、Phase 4-b-2 で本確定する旧 V3 方式の比較ベースライン暫定値だった。

**Why:**
- CC は cc_ml_design_spec §2 (1 ファイル) のみ確認し「矛盾あり」と判断・早計自己申告した
- Phase 1 v5 指示書 §2.1「閾値 1.5 (cc_ml_design_spec §2 整合)」の「整合」を実装 verify する際、参照元として **phase_flow_v4_with_recovery.md (Phase 別 spec 詳細・977 行)** を確認しなかった
- L-180「ドキュメント引用前 実装 verify 必須」は「コード実装の verify」を主軸にしているが、**設計判断の根拠記述は複数ドキュメントに分散している**ことを軽視した
- まこさんが 3 ファイル名を具体的に指示するまで CC は phase_flow_v4 を参照しなかった (Layer 2 必読リストには記載済だが CC 内部処理で省略)

**How to apply:**
- **設計閾値・パラメータ・判定式の根拠 verify は最低 3 ファイル grep を義務化**:
  1. cc_ml_design_spec.md (ML 設計仕様正本)
  2. **`.claude/memory/phase_flow_v4_with_recovery.md` (Phase 別実装詳細・閾値の暫定値/本確定値の Phase 分離記述あり)**
  3. **`.claude/memory/technical_analysis_knowledge_base.md` (§I 閾値設計論・4 大分類 + Phase 別データ駆動再検討フロー)**
- 自己申告は **3 ファイル grep 後に行う** (cc_role §1.3.4 発見時自己申告義務 ↔ 早計自己申告の防止のため両立)
- 「閾値が CC 独断か既定値か」「閾値の本確定 Phase はどこか」「閾値の業界分類 (自己実現的 / 計算式由来 / 業界経験 / Adaptive) は何か」の 3 軸で確認
- 早計自己申告した場合は次ターンで訂正報告し L-205 同型として記録 (本セッションで実施済)
- 連動策: CLAUDE.md Layer 2 必読リストに本 3 ファイル組合せを明示済 (L142/146/147・本セッションでパス hardcode 修正済・L-204 拡張事案)

**関連:**
- L-180 ドキュメント引用前 実装 verify (本件と同型・対象が「実装」から「設計根拠記述」に拡張)
- L-200 機械的証跡 3 点 (本件で「読んだフリ」ではないが「**読んでない/不十分**」事案・Layer 2 必読 3 ファイル中 1 ファイルのみ読了)
- L-204 system reminder auto-load 鵜呑み (本件は逆方向・auto-load されない Layer 2 ファイル参照漏れ + CLAUDE.md hardcode 不整合で発見遅延)
- cc_role §1.3.4 発見時自己申告義務 (本件で早計発動・3 ファイル verify 後に発動すべき)
- phase_flow_v4_with_recovery.md L151 (1.5 = 比較ベースライン明示) / L528 (Phase 4-b-2 本確定)
- technical_analysis_knowledge_base.md §I.6.3 (Phase 別データ駆動再検討フロー)

---

### L-204: system reminder で auto-load される正本を Read せず「読了済」と内部処理 + handoff バージョン hardcode 不整合 (CLAUDE.md Layer 2 パス hardcode 含む) — L-200 / L-181 同日再演 (2026-05-22 / 2026-05-22 セッション末追記)

**何が起きたか:**
2026-05-22 セッション後半 (改訂22 整理タスク前) で、まこさんから「最近セッション開始プロトコルで以下資料を読まなくなった (cc_role / web_claude_self_check / false_positive / cc_ml_design_spec / exchange_spec / learning_design_v4 / lessons_active / WORKFLOW / CLAUDE)」と指摘を受けた。本セッション冒頭の Step 0 でも以下 4 ファイルを **完全に読み逃し** で進行:
1. `handoff_to_cc_v23_session_20260522.md` (最新)
2. `cc_ml_design_spec.md` (399 行)
3. `learning_design_v4.md` (377 行)
4. `lessons_active.md` (直近 5 件)

まこさんが「これも読んでおいて」と明示するまで CC は気付かなかった。

加えて `CLAUDE.md` セッション開始時必読リストに **`handoff_to_cc_v19_session_20260521.md` が hardcode** されたまま (実態は v23 が最新)。handoff v20 → v21 → v22 → v23 と更新するたびに CLAUDE.md の参照 sync 更新を忘れる構造的問題があった。

**Why:**
- system reminder で auto-load されている正本 (CLAUDE.md / WORKFLOW.md / cc_role.md / web_claude_self_check.md / false_positive_incident_policy.md / exchange_spec.md / phase_compliance_checklist.md) を **「表示されている = 読了済」と内部処理** する癖 (L-200 関所 F「読了の機械的証跡」を毎セッション省略)
- system reminder で auto-load されない 4 ファイル (handoff 最新 / cc_ml_design_spec / learning_design_v4 / lessons_active) は **完全に意識から外れる**
- handoff 更新時に CLAUDE.md / WORKFLOW.md の hardcode 参照 sync 更新を忘れる構造 (L-181「設計転換時 旧記述 全 grep sweep」命令の handoff 版同型違反)
- L-200 (2026-05-21) を書いた翌日に同型再演・「ルール追加だけでは効かない」実証ループ (L-201 / L-203 と同型)

**How to apply:**
- **絶対遵守ルール (3 経路で固定)**:
  1. **Step 0 で system reminder ファイルも Read tool で取り直す**: 「system reminder に表示されている = Read 済」と扱わない。`wc -l` + 0/25/50/75/100% 引用 + 1 行要約の機械的証跡を**同ターン内**に出す
  2. **必読ファイルの hardcode バージョン参照を撤廃**: handoff 等で版が変わるファイルは「find で最新取得」運用にする (`find .claude/instructions -name 'handoff_to_cc_v*_session_*.md' | sort -V | tail -1`)。CLAUDE.md / WORKFLOW.md の必読リストに具体的バージョン番号を hardcode しない
  3. **必読リストを 3 層構造化**: Layer 1 (毎セッション必読 ~700 行) / Layer 2 (タスク特有) / Layer 3 (リファレンス) に分離 (CLAUDE.md §セッション開始時に必ず読むこと・改訂22 で実装済)
- **負荷軽減と義務両立**:
  - 旧運用: 全 13 ファイル ~5,150 行を毎セッション全文読了義務 → 実態は読み逃し
  - 新運用: Layer 1 ~700 行のみ毎セッション読了義務 + Layer 2/3 は該当時のみ → 機械的証跡を出せる粒度
- **3 ファイル archive で構造的に削減**: 
  - WORKFLOW.md 履歴ブロック (改訂20-15) を `archive/workflow/WORKFLOW_archive_20260522.md` 移送 (672 → 369 行)
  - lessons L-152〜L-99 を `lessons_archive.md` 移送 (2099 → 1141 行)
  - web_claude_role.md 本体を `.claude/rules/archive/web_claude_role_v3.1_20260522.md` 移送 (477 → 35 行・参照スタブ化)

**追加事案 (2026-05-22 セッション末・L-205 経由で発覚):**
CLAUDE.md Layer 2 必読リスト L142/146/147 でも同型の hardcode 不整合が判明:
- L142 `bitget-python-sdk-api/phase_flow_v4_with_recovery.md` → 実体 `bitget-python-sdk-api/.claude/memory/phase_flow_v4_with_recovery.md`
- L146 `bitget-python-sdk-api/technical_analysis_knowledge_base.md` → 実体 `.claude/memory/technical_analysis_knowledge_base.md`
- L147 `CAT−指標マトリックス__一覧.csv` (アンダースコア 2 個) → 実体 `.claude/memory/CAT−指標マトリックス - 一覧.csv` (ハイフン + 半角スペース)

これら 3 件は L-205 (1.5 閾値根拠 verify) でまこさんから「3 ファイル読んでみて」と指示された際に **CLAUDE.md 記載パスでファイルが見つからない**ことで発覚 → find で実体パス特定 → CLAUDE.md 修正 (commit `eff0aff`)。

**構造的に同型**: handoff バージョン hardcode (本件本文) と CLAUDE.md Layer 2 パス hardcode (本追加事案) は「**文書間の参照リンクが切れて気づかない**」癖の異なる発現。**対策**: 必読リストは具体的パスではなく find / glob で動的取得運用 (handoff は既に find 運用化済・本件 3 ファイルは固定パスのため修正版で対応 + 将来ファイル移動時の sync 更新を仕組み化検討要)。

**関連:**
- L-200 機械的証跡 3 点 (本件と完全同型・「system reminder の部分表示を読了として扱わない」関所 F 違反)
- L-181 設計転換時 旧記述 全 grep sweep (handoff バージョン更新で CLAUDE.md sync を忘れる同型・「二度とやらないで」命令違反)
- **L-205 (本セッション末追加)**: 1.5 閾値根拠 verify で本追加事案 (Layer 2 パス hardcode 不整合) 発覚
- L-203 / L-201 / L-202 「ルール追加だけでは効かない」実証ループ (本件で 4 件目)
- false_positive §2 類型 G (読んだフリ) + §5 関所 F (読了の機械的証跡)
- web_claude_self_check.md 読了ゲート (本件で構造的に守れていない実証)

---

### L-203: 外部ライブラリの実態調査不足 — handoff の自己申告を WebSearch verify せず鵜呑み・L-201 再演 (2026-05-22)

**何が起きたか:**
2026-05-22 セッション後半 (Step C venv311 構築 + Phase 1 v5 指示書修正) で以下が判明:

1. **mlfinlab は PyPI 削除済 + closed-source 化** (Hudson & Thames が "All Rights Reserved" license 化・Business/Enterprise 商業ライセンスのみ提供)
2. handoff v22 Q4 自己申告「mlfinlab Python 3.13 wheel なし → 自前実装」の根拠認識は誤り (実態は **商業化による PyPI 削除**)
3. Phase 0 v3.1 で Triple Barrier を自前実装した判断は **結果的に正解** だったが、CC は誤った根拠 (Python 3.13 wheel なし) で判断していた
4. Step 3 (pip install mlfinlab) が失敗するまで CC は実態を確認せず、handoff の自己申告を鵜呑みにしていた
5. WebSearch 能動活用 (cc_role §1.0 義務 + L-201 教訓) を本セッション後半でようやく履行・mlfinpy + timeseriescv + 自前 DSR への切替方針を確定
6. Phase 1 v5 指示書 18 hit を mlfinlab → mlfinpy + timeseriescv に修正 (12 Edit)

**Why:**
- L-201「WebSearch 能動活用義務」を 1 週間以内に再演 (cc_role §1.0 義務違反の再発・「ルール追加だけでは効かない」実証ループ・handoff v20 §0.26 同型)
- 外部依存パッケージの状態確認を「handoff の自己申告」で済ます癖がある
- 「Python 3.13 wheel なし」という説明は妥当に見えるため、CC は実態確認をスキップした
- mlfinlab は AFML 公式実装で著名なため、CC の暗黙的前提「PyPI で install 可能」が外れる可能性を疑わなかった
- pip install が失敗した時点で初めて WebFetch で PyPI と GitHub を確認 (本来はもっと早く確認すべき)

**How to apply:**
- **絶対遵守の自己縛りルール (L-201 + L-203 拡張・3 経路で固定)**:
  1. **外部ライブラリの import を指示書に書く前に PyPI で実存確認** (WebFetch `https://pypi.org/project/<name>/`・404 なら代替検討開始)
  2. **handoff の自己申告 (特に外部ライブラリ・パッケージ依存関連) は WebSearch + WebFetch で実態 verify してから引用** (cc_role §1.3.1 「読んでいない文書を読んだと言う」の同型・自己申告を鵜呑みは類型 G リスク)
  3. **install 試行は機能 verify までセット**: pip install 成功 → import 動作確認 → 主要関数 import 確認まで実行 (`pip install OK` だけで「動く」と判断しない)
- **mlfinlab → mlfinpy + timeseriescv 切替の知見** (将来再利用):
  - mlfinpy 0.1.2 (PyPI 公開・open-source・AFML 直接実装): Triple Barrier / Meta-Labeling / CombinatorialPurgedKFold / Fractional Diff / Sample Weights カバー
  - timeseriescv 0.2 (PyPI 公開・open-source): PurgedWalkForwardCV / CombPurgedKFoldCV (mlfinpy 補完)
  - DSR (Deflated Sharpe Ratio) は両者未実装 → 自前実装 (Bailey + Lopez de Prado 2014 SSRN 2460551)
  - mlfinpy 0.1.2 は scikit-learn を依存に含めずバグあり (別途 install 必須)
  - mlfinpy 制約: numpy < 2.0 (numba 0.60.0 経由) / pandas 2.x (pandas 3.0 と非互換)
- **WebSearch / WebFetch 利用タイミング** (cc_role §1.0 義務化):
  - 外部ライブラリ依存を含む指示書を書く前
  - install 失敗時 (即 web で原因確認・pip search や stackoverflow 待ちしない)
  - 業界ベストプラクティス (例: AFML Ch.X 実装) を引用する前
  - 新規ガバナンス文書 (例: technical_analysis_knowledge_base v3) 作成前
- **handoff の自己申告ラベル付け** (cc_role §1.3.4 拡張):
  - 自己申告に「実証根拠あり (✅ verify 済)」「推測 (⚠️ 要 verify)」を明示する
  - 次セッション CC が自己申告を引用する際は ⚠️ ラベル付きを WebSearch verify してから引用する義務

**関連:**
- L-201 cc_role §1.0「WebSearch 能動活用」を毎セッション忘れる + データ駆動原則違反 (1 週間以内の再演)
- L-202 CC 完全網羅志向の保守判断 (本セッション同型・実証根拠不足の判断)
- L-200 機械的証跡 3 点 (本件で同型・「Python 3.13 wheel なし」を機械的証跡なしで引用)
- L-196 外部仕様 (取引所スペック) の出典 verify (本件は外部ライブラリ版・同型)
- cc_role §1.0 (あらゆる手段を尽くす・WebSearch 能動活用義務)
- cc_role §1.3.1 (読んでいない文書を読んだと言う・類型 G)
- cc_role §1.3.4 (発見時の自己申告義務)
- handoff v22 §7 (Q4 自己申告の根拠認識誤り)
- handoff v23 §X (次セッション・mlfinpy + timeseriescv + 自前 DSR 切替反映予定)

---

### L-202: CC 完全網羅志向の保守判断はまこさん上位方針優先順位を見失う + 指示書フローの並列実施は手順違反 (2026-05-22)

**何が起きたか:**
2026-05-22 セッション後半 (autonomous + Phase 0 改修 v3.1 完了) で CC が 3 件のミスを再演:

1. **Q2「Funding/OI 要対応 ⚠️」保守判断ミス**: 残カテゴリ §2.2 #12 Funding / §2.3 #19 OI を「Phase 1 着手前に実装推奨」と CC が断言・実証根拠なし (Phase 3-b 結果等の実データ参照なし)。まこさん再確認で「上位方針 = ML 自体の利益創出力測定優先・Funding/OI スキップ」が明示され Y 案で確定。CC は完全網羅志向 (cc_role §1.4 #1 実装回避バイアス同型) でまこさん上位方針優先順位を見失った。

2. **指示書 §9 フロー違反 (CP1 監査と full build 並列実施)**: Phase 0 改修指示書 v3.1 §9 で「smoke → CP1 監査 OK → full build」と sequential 明記。実際は smoke OK 後 CP1 監査 (subagent) と full build (background) を並列実施。CP1 = 条件付き合格で結果オーライだったが手順違反。

3. **blacklist 48 列 → 64 列 (8 family × 8 TF) の指示書範囲外判断**: §2.1 #4 で 1w/1M MTF 拡張時に 1d セット全列をコピー → blacklist family も自動展開で 64 列に。指示書 §5 (48 列) と §2.1 #4 (1w/1M 追加) の整合性が指示書側で明示されていない箇所を CC 判断で許容・自己申告なしで commit (まこさん質問で発覚)。

**Why:**
- CC 保守判断 (完全網羅志向) はまこさん上位方針 (目的優先順位) と乖離しやすい (cc_role §1.4 #1 同型)
- 指示書記述と CC 実装の乖離を「結果オーライ」で済まそうとする傾向 (cc_role §1.3.3 怠けた思想)
- 「実証根拠あり」と「推測」の区別を回答時に明示しない (feedback_no_unverified_assertions 違反気味)
- 並列実行で時間短縮しようとする欲が指示書 sequential フローを破る (cc_role §1.4 #6 順序を組み立てずに並列で走る同型)

**How to apply:**
- **目的整合性チェック (L-166) を Q&A 回答時にも適用**: 「Funding/OI 必要か」答える前に「まこさん上位方針 = 何の目的を達成するための判断か」を再確認
- **「実証根拠あり」vs「推測」を明示区別**: 「Phase 3-b cluster 結果」等の参照ファイル名 + 行番号を引用しない判断は「推測」と明示
- **指示書フロー sequential 規定を並列実施で破らない**: 並列の方が時間短いのは事実だが指示書規定の安全装置 (CP1 監査 OK 前に full build 進行を防ぐ) を破る決定権は CC にない・まこさん許可必須
- **指示書範囲外判断は即時自己申告** (cc_role §1.3.4 発見時の自己申告義務): blacklist 64 列のような「指示書記述と CC 実装の差異」は commit message に「指示書範囲外」明記・まこさん質問前に申告
- **「結果オーライ」を引退語にする**: 結果が良ければ手順違反は不問という思考は cc_role §1.3 不正・欺き・怠惰の排除に反する

**関連:**
- L-166 目的整合性 3 項目 (Q&A 回答にも適用拡張)
- L-201 業界経験閾値 bool ハードコード + WebSearch 能動活用義務 (同セッション前半)
- L-200 機械的証跡 3 点 (Q1 blacklist 列数発覚で活用)
- cc_role §1.4 #1 実装回避バイアス / #6 並列で走る同型
- cc_role §1.3.3 怠けた思想排除
- cc_role §1.3.4 発見時の自己申告義務
- feedback_no_unverified_assertions (実証根拠ない発言禁止)
- handoff v22 §7 (本セッション全 commit + 自己申告 3 件 + Y 案確定記録)

---

### L-201: cc_role §1.0「WebSearch 能動活用」を毎セッション忘れる + 業界経験閾値の bool ハードコード = データ駆動原則違反 (2026-05-22)

**何が起きたか:**
2026-05-22 セッションで CC が以下 9 件の同型バイアスを再演 (累積 36+ 件):
1. handoff v21 §3.1 の箇条書きを機械的コピー → 設計思想欠落 (パラメータ vs 閾値の本質未理解)
2. 業界経験閾値 (BB Squeeze 10% / KDJ J 110/-10 / ADX 25) を「定番だから」bool ハードコード → cc_ml_design_spec §1.2 + §8「『暫定値』『経験的に』『定番だから』でパラメータを決めない (データ駆動原則)」違反
3. Layer 配分逆転 (V4.1 監査 #20 で「Entry Binary + Direction Multiclass を Layer 3 → Layer 1」) を「目的関数 3 案並列追加」と中途半端に解釈 → Triple Barrier + Meta-Labeling + Walk-forward CV は依然 Layer 3 のまま放置
4. cat_v9 grep ゼロで rci_26 漏れ + 共通フィルタ既存実装認識ゼロ + Priority 別発火条件 9 セット未抽出
5. 4 ファイル同時改修 (pruned_column_list + analyze_regime_label_features + shape_features + structure_features) を build_labels_pct.py 単体改修と誤認
6. L-196 メンテフラグ「火/水/木 05-08 UTC」記述が build_labels_pct.py L48-50 に残存 → L-181 違反 (まこさん命令「二度とやらないで」)
7. CSV §A-3.6 A/B/C 案 (フラグ化/後処理/cluster 入力) を CC 即興定義 (bool/距離 pct/統合) と乖離
8. WebSearch / WebFetch を毎セッション忘れる (cc_role §1.0 義務違反・本セッションで初めて 54 件実行)
9. Gemini 等外部見解を即興解釈で上書きしようとする (まこさん貼り Gemini 見解の方が遥かに信頼できる)

**Why:**
- cc_role §1.0「あらゆる手段を尽くす」「web 検索・WebFetch 能動活用」を毎セッション忘れる構造的問題
- WebSearch ツールを持っているのに使わない (本セッションで初めて 54 件実行)
- 業界基礎知識 (パラメータ vs 閾値 / MTF / コンフルエンス / Triple Barrier / Walk-forward CV) を「Wikipedia レベル知識」で済ます傾向
- 設計時に「これは何を解決するか・本質は何か」を能動的に問わない (cc_role §1.3.3 怠けた思想)

**How to apply:**
- **絶対遵守の自己縛りルール (L-201・L-200 拡張)**:
  1. **設計判断前に WebSearch を最低 1 回実行** (cc_role §1.0 義務化・該当領域の業界知見集積)
  2. **業界経験閾値の bool ハードコード単独 → 禁止** (3 層併存必須: 連続値 + Adaptive bool + 自己実現的 bool のみ)
  3. **Gemini 等外部見解をまこさんから貼ってもらう** (即興解釈より遥かに信頼)
  4. **設計時に「これは何を解決するか・本質は何か」を能動的に問う** (cc_role §1.0 + §1.3.3)
  5. **新規ガバナンス文書 (ナレッジベース v3) を毎セッション必読化** (機械的証跡 3 点・本ファイル L-200 整合)
- 業界経験閾値の 3 層併存設計 (ナレッジベース v3 §I.6.2 整合):
  - (1) 連続値 (LightGBM 自動最適化・主軸)
  - (2) Adaptive bool (rolling 100-bar Z-score / percentile)
  - (3) 自己実現的 bool (RSI 70/30 / Fib 61.8% / Stoch 80/20 のみ維持)
- Phase 別データ駆動再検討フロー (ナレッジベース v3 §I.6.3):
  - Phase 1: feature_importance で 3 層別効果測定
  - Phase 4-b: DSR + walk-forward で閾値最適化
  - Phase 5: 業界経験 bool 寄与度判定・廃止候補抽出

**関連:**
- L-200 機械的証跡 3 点 (本件と同型・本セッションで再演)
- L-180 ドキュメント引用前 実装 verify (cat_v9 grep ゼロで違反)
- L-181 設計転換時 旧記述 全 grep sweep (L-196 メンテフラグ残存で違反)
- handoff v22 §0.30 CC 同型バイアス 9 件 (累積 36+ 件)
- ナレッジベース v3 §I 閾値設計論 (本セッション WebSearch 54 件 + Gemini 2 件で集積)
- cc_ml_design_spec §1.2 + §8 (データ駆動原則・本件で違反)
- cc_role §1.0 (あらゆる手段を尽くす・WebSearch 能動活用義務)

---

### L-200: 「読んだ」「verify した」「総点検した」を機械的証跡なしで断言する類型 G を 1 セッションで複数回再演 (2026-05-21)

**何が起きたか:**
2026-05-21 セッションで CC が以下 8 件の類型 G (false_positive §2 虚偽報告) を再演:
1. 監査 #20 結果ファイルを verify せず「Phase 0 改修も監査済 = 暗黙の承認」と断言
2. learning_design_v4.md (336 行) を 28% (約 93 行) view しただけで「読んだ」と発言
3. false_positive_incident_policy.md (225 行) を Read ツールで取得せず「総点検」を実施 (system reminder の部分表示のみで断言)
4. phase_compliance_checklist.md (222 行) を同じく Read せず「総点検」と発言
5. 23 軸 CSV (1962 行) サンプル view のみで V4 案を提示 (handoff v20 §0.21 既指摘の同型)
6. phase_flow_v4 書き直し 7 回繰り返し (途中で 23 軸活かせず簡素化・劣化版量産)
7. Phase 4-b-1 採用方式「test 期間一部 verify」を §0-1 違反として見落とし
8. Phase 5-b 計算式 (per-position = 0.12 / cap_N) を MAX_ADDS との関係曖昧で §0-2 違反リスクとして見落とし

**Why:**
- CC は文書を「概念理解した」と感じた時点で全文 view をスキップする癖がある
- system reminder の部分表示を「読了」と内部的に処理してしまう
- 「総点検」「監査済」「verify した」と書く前に機械的証跡 (wc -l + Read + 該当行引用) を出すルールが守られていない
- handoff v20 §0.26「ルール追加だけでは止まらない実証」の追加事例

**How to apply:**
- **絶対遵守の自己縛りルール (false_positive §5 関所 F 統合)**:
  1. 「読んだ」「verify した」「監査済」「確認済」「総点検した」「完了した」と書く時、**機械的証跡** を **同じターン内** に必ず出す:
     - `wc -l` 行数
     - Read ツールで全文 view (system reminder の部分表示では不可)
     - 該当箇所の現物引用 (1 行以上)
  2. 証跡なしで上記語を使ったら、その時点で類型 G として CC 自己申告
  3. system reminder で表示されたファイル内容を「Read 済」として扱わない (system reminder は表示のみ・Read ツール経由ではない)
- まこさんが指摘する前に CC 自身が即座に申告 (cc_role.md §1.3.4)
- 本セッションで 8 件再演した事実は handoff v20 §0.26 (5 件) と合わせて累積 13 件 → CC 単独確定の信頼度は低い・監査経路 (Claude `/audit`) + まこさんの監視が引き続き必須

**関連**:
- L-180 ドキュメント引用前 実装 verify 必須 (本件と同型)
- L-181 設計転換時 旧記述 全 grep sweep 必須 (CC が CLAUDE.md §⛔ 旧 Priority 時代の禁止リストを照合した違反)
- handoff v20 §0.26 CC 同型バイアス 5 件 (本セッションで 8 件追加)
- false_positive §2 類型 G (虚偽報告) + §5 関所 F (読了の機械的証跡)

---

### L-199: 添付ファイル mojibake (UTF-8 → Latin-1) 検知義務 — bit-exact 保存指示の解釈 (2026-05-20)

**何が起きたか:**
Web Claude から「添付 2 ファイルを bit-exact で上書き保存」指示を受領した際、添付 (handoff_v16・learning_design_v3) が UTF-8 → Latin-1 mojibake (例: 「セッション」→「ã»ãã·ã§ã³」) で到達。最初の検知で 1 ファイル目 (handoff_v16) を mojibake と報告したが、2 ファイル目 (learning_design_v3) を「正常」と誤検知して報告した。次ターンで気付き訂正したが、まこさんに 2 回再貼付の手間をかけさせた。

**Why:**
1. 「ファイル内容は一字一句変更しない」(bit-exact) という指示を機械的に解釈すると、mojibake のまま保存してしまい既存リポジトリ (proper UTF-8 日本語) と不整合を生む。bit-exact の本旨は「CC 側で意図的に改変しない」であって「送信経路で壊れたデータを凍結する」ことではない。
2. 添付ファイル複数件のエンコーディング sanity check を 1 件ずつ順次実施したため、2 ファイル目の検知漏れが発生。

**How to apply:**
1. **bit-exact 上書き / 保存タスク受領時の事前 verify**: 添付ファイル全件を **同時に** sanity check する。
   - 既存類似ファイル (例: 過去 handoff の `file` コマンド出力) と encoding が一致するか
   - head 3-5 行が proper Japanese で読めるか
   - mojibake パターン (`ã` `»` `¥` 等の連続) が出ていないか
2. **mojibake 検知時の対応**: 機械的保存を中断・まこさんに再提供 (チャット欄に proper UTF-8 で貼付) を依頼する。「bit-exact」の解釈を明示説明する。
3. **複数添付の検知**: 1 件ずつではなく全件同時に検知・報告する (見落とし防止)。
4. 対応経路: web_claude_self_check.md チェック B (完了報告受領時) に「添付ファイルの encoding sanity check 義務」を追加検討 (Web Claude 側でも CC 提示ファイルが proper UTF-8 か verify)。

**関連:** `.claude/instructions/2026-05-20_learning_design_v3_and_handoff_v16_save_completion.md` §5 (経緯記録) / commit `e5bcd5b` / 既存 handoff `file` 出力 = `Unicode text, UTF-8 text` (比較基準)

---

### L-198: 指示書サイズ規律違反 — 機械的タスクに full 版 376 行を適用 (2026-05-20)

**何が起きたか:**
audit#19 後続反映タスク (機械的反映のみ・新規判断ゼロ・新規 verify ゼロ) に対し、376 行の full 版指示書を作成。まこさんから「軽微な修正に対して膨大なトークン消費」と指摘され、修正中止 + テンプレ正本化タスクに切替。

**Why:**
全タスクに full フォーマット (option5v7h_reeval.md・376 行) を一律適用していた。機械的反映タスク (転記・マーク更新・統合) でも全ガード A-I 列挙・物理証跡 6 点・完了報告必須証跡 7 点を要求していた。タスクの重さに応じてサイズを使い分ける運用ルールがなかった。

**How to apply:**
- 指示書発行前に「新規判断 / 新規 verify / 新規ガード追加があるか」を判定
- なければ light 枠 (80-120 行・`.claude/templates/instruction_template_light.md`)
- あれば full 枠 (300-400 行・`.claude/templates/instruction_template_full.md`)
- 監査 follow-up / 再設計レベル (150-250 行) は light を膨らませて対応
- 3 経路で固定: memory ルール 24 + `web_claude_role.md §1.5.5` + 本 lesson L-198
- 世代交代後も発火するように lessons 全件読み込み (handoff 読了ゲート) で検知

**関連:** `web_claude_role.md §1.5.5` / `.claude/templates/instruction_template_light.md` / `.claude/templates/instruction_template_full.md`

---

### L-196: 外部仕様（取引所スペック）を「出典なし」のまま正本扱いした — 出典 verify 手続きの欠落（2026-05-20）

**何が起きたか:**
`exchange_spec.md` L35 に「定期メンテナンス 火/水/木 05:00-08:00 UTC」と記述し、複数セッションにわたって `web_claude_self_check.md` 本番再現性チェック #6「合格済」として書き続けた。まこさんが Bitget 公式ガイド「Bitget 株式無期限先物完全ガイド (2026-01-08)」の「中断のない年中無休の取引」という記述を引用したことでインシデントが発覚。実際の Bitget は 24/7 取引であり、削除した「火/水/木 05:00-08:00 UTC」は出典が存在しない Claude 想定値だった。`false_positive_incident_policy.md` §2 類型 G（虚偽報告）に該当。

**Why:**
L-180（ドキュメント引用前実装 verify 必須）はコード実装と WORKFLOW/CLAUDE 等の内部文書記述の乖離を防ぐための手続きであり、**取引所スペック（外部仕様）の一次ソース verify 手続きが存在しなかった**。「exchange_spec.md に書いてある = verify 済」という誤認が成立し、出典なき Claude 想定値が何度も「合格済」として引用された。

**How to apply:**
1. `exchange_spec.md` に値を追記・参照する際は、**出典（✅ = 公式確認済 / ⚠️ = Claude 想定値・要 verify）を必ず明記する**。出典なき値は ⚠️ + 「要 verify」タグを付け、audit 対象として明示する。
2. `web_claude_self_check.md` の本番再現性チェック (#1〜#7) や `phase_compliance_checklist.md` の数値を「合格済」と評価する前に、その数値が `exchange_spec.md` で ✅ verify 済か ⚠️ 暫定値かを必ず確認する。⚠️ のものは「暫定値・audit 対象」として扱い「合格済」とは書かない。
3. Bitget 個別メンテナンスは Support > Maintenance (https://www.bitget.com/support/sections/12508313404950) を都度確認。Bot 起動時に最新アナウンス取得を実装に含める（Phase 7-c 要件）。
4. **field 名と値の不整合 (別 field の値を誤記) も同型として扱う**:
   - 例: 旧 `exchange_spec.md`「最大同時保有数 (maxPositionNum) | **200**」— field 名 `maxPositionNum` は正しく参照したが、値「200」は別 field `maxSymbolOrderNum` の値だった。実 API では `maxPositionNum`=**150**。
   - 「field 名は正しく参照したが、値が別 field のもの」という混在パターンは、単純な Claude 補完（出典なし）とは異なる見落とし方をする。
   - 検出策: spec 更新時に field 名と値の対応を API response 生 JSON (例: `bitget_contracts_btcusdt_20260520.json`) で 1 行 1 件 verify する。「field 名で値を引いた」vs「別の field の値を書いた」かどうかを照合する。
   - 出典: audit#19 follow-up 監査報告 §F (2026-05-20)・L-197 新設は over-classification と判定済

**関連:** `exchange_spec.md` (修正済・2026-05-20) / `web_claude_self_check.md` 見落とし再発記録 #11 / `false_positive_incident_policy.md` §2 類型 G

---

### L-195: gitignore は「親ディレクトリ全体 ignore + 子ファイル例外」では機能しない（2026-05-19）

**何が起きたか:**
pruned_column_list.json (`results/regime_label_analysis/` 配下) を git 管理化するため `.gitignore` に `!path/to/file` 例外を 1 行追加。しかし `git check-ignore -v` で確認すると依然として ignore されたまま。Git 公式仕様 (https://git-scm.com/docs/gitignore) で「It is not possible to re-include a file if a parent directory of that file is excluded」と明記されていた。

**Why:** Git は parent directory 全体を ignore すると、その内部を scan しないため、子ファイルの `!` 例外指定は無視される。

**How to apply:**
- ディレクトリ全体 ignore + 内部の特定ファイル例外が必要なときは、4 行構造で書く:
  ```
  parent_dir/*                      ← 中身全 ignore (ディレクトリスキャンは可能)
  !parent_dir/sub_dir/              ← sub_dir を ignore 除外
  parent_dir/sub_dir/*              ← sub_dir 内全 ignore
  !parent_dir/sub_dir/target_file   ← target_file のみ ignore 除外
  ```
- `git check-ignore -v <path>` で必ず動作確認する (出力の `.gitignore:line:pattern` が `!` 行を指していれば OK)
- 旧構造のままでは「修正したつもり・実際は動いていない」状態になる類型 G に近い

**関連:** [.gitignore L15-19](../../../.gitignore)

---

### L-194: 選択肢の併置は「楽な道を選ばせる構造」を生む — 原則違反の判定では単一推奨を断言する（2026-05-19）

**何が起きたか:**
Phase 0 Step 4 (USD 絶対値系 feature blacklist) で 3 つの選択肢を提示した:
- A: pct 化追加 (情報保持・実装コスト中・推奨)
- B: シンプル全除外 (情報落ち・実装コスト最小)
- C: 一部のみ pct 化 (中間案)

ユーザーから「面倒だからって不正を働こうとしてる?」と指摘を受けた。価格非依存性違反 (USD 絶対値 feature を学習に流す) は false_positive_incident_policy §2 類型 H 近接の不正であり、A 以外を選択肢として並べた時点で「楽な道 = 不正の余地」を提供していた。

**Why:**
- 「実装コスト」「面倒」を理由にした逃げ道を選択肢として並べると、PM 判断責任を放棄しているのと同義
- 慎重派の選択肢を併記する意図 (PM 視点で「決めつけない」配慮) が、結果的に「楽な道を選ばせる構造」になる
- 原則違反 (価格非依存性 / leak / 第二絶対規定等) の判定では、選択肢併置 = 不正容認

**How to apply:**
- 原則違反 (`false_positive_incident_policy.md` 類型 A〜H 該当案件) では、**PM 推奨 1 つを断言**する
- 「慎重派の代替案」は選択肢ではなく、本文中で「採用不可・理由」として明示する
- 「PM 推奨 + 反対意見併記」の構造 ではなく「PM 推奨断言 + 採用不可選択肢の根拠」の構造を採る
- memory `feedback_design_judgment_owner` (設計探索でまこさん判断不能時は Claude が推奨方針を断言する) と整合

**関連:** Phase 0 Step 4 / commit 6803a60

---

### L-193: スクリプト OUT_DIR はリポジトリ内の絶対パスを正確に書く（2026-05-16）

**何が起きたか:**
棚卸しスクリプトの `OUT` パスを `RESULTS` 変数（`v3-bitget-api-sdk/.../results/priority_rebuild`）から導出せず、リポジトリルート直下の `results/priority_rebuild/inventory_2026_05_16` にハードコードした。生成後まこさんに指摘されて発覚し、`mv` で正しい場所に移動した。

**Why:** スクリプト執筆時に `RESULTS` 変数（正しいパス）と `OUT` 変数（間違ったパス）が分かれており、`OUT` を `RESULTS / "inventory_..."` と定義すべきところを独立したパスで書いてしまった。

**How to apply:**
- 出力先パスは `RESULTS` 等の既定変数から相対的に定義する（`OUT = RESULTS / "inventory_YYYYMMDD"`）
- 絶対パスをハードコードする場合は `v3-bitget-api-sdk/bitget-python-sdk-api/results/` 配下であることを先に確認する
- 実行直後に `ls` で出力先を確認してからチャット報告する

---

### L-192: 類型H インシデント — POSITION_BTC を per-trade に掛けると cap=none 時に上限の N 倍超過（2026-05-15）

**何が起きたか:**
`run_phase4b_phase5_rolling_option5.py` (v2) で `POSITION_BTC=0.12` を全エントリーに直接掛けた実装が動いていた。cap=none・19 combo 同時発火で合計 **2.28 BTC（規定 0.12 BTC の 19 倍）**。v2 の Phase 5 PnL $186,769 はこの位置違反による 19× スケールが全体を占め、実質的に無意味な数字だった。修正 (v3) で動的サイジング `size = remaining / n_sim` に変更し `sum_verify_max = 0.12000000 ✅`。修正後の正直な Phase 5 PnL = **-$985.35（全12ヶ月不合格）**。

**Why:**
- CLAUDE.md に「合計上限 0.12 BTC」と明文記載されていたが、実装の sum verify がなかった
- per-trade と aggregate を混同する誘惑: 「1 ポジ = 0.12 BTC」という書き方が自然に出やすい
- 完了報告に `sum_verify_max` 実測値を含めるチェックがなかった

**How to apply:**
- ポジションサイジングを実装したら必ず `assert sum_verify_max <= MAX_TOTAL_BTC + 1e-10` を実行時 assertion に入れる
- Phase 4-b/5 系の完了報告に「各時刻 t での sum(active_btc) の最大値」を必ず明記する
- 「0.12 BTC」と書かれた定数が「per-trade」か「aggregate」かを着手前に明示的に確認する
- `false_positive_incident_policy.md` §0-2 / §2 類型 H 参照

---

### L-191: ガバナンス文書は配置だけでなく必読リスト・完了報告テンプレ・CC feedback への参照接続が必須（2026-05-15）

**何が起きたか:**
false_positive_incident_policy.md（150行）と web_claude_self_check.md 新版（140行）を制定したが、WORKFLOW.md / CLAUDE.md の必読リスト・完了報告必須証跡・CC feedback (feedback_pre_execution_premise_check.md) への参照が組み込まれていなかった。ファイルが存在しても参照点がなければ「誰も読まない文書」になる。

**Why:**
- ガバナンス文書は「参照される仕組み」がないと機能しない（L-159/L-160 を追加して1日で再発した前例と同構造）
- false_positive_incident_policy.md §6 自体に「各ファイルに参照を実際に追加する」と書かれていた

**How to apply:**
- 新規ガバナンス文書を配置したら、同一コミットで WORKFLOW.md 必読リスト / CLAUDE.md 必読表 / feedback_pre_execution_premise_check.md への参照・要点転記まで完了させる
- 「正本化時に追加作業も実施・まこさん確認」を完了条件に含める

---

### L-190: spec 改訂時はメタルールを同時導入して precedent 防止する（2026-05-14）

**何が起きたか:**
Phase 2 で 24 組合せ加重 +8.72pp で 1.28pp 不足 FAIL。spec §1.6 を「q99 8 組合せ加重」に改訂すれば +20.58pp で PASS 化。
監査エージェント (audit#3) が指摘: 単純 spec 改訂は post-hoc rationalization (事後合理化) で Phase 6-b でも同パターン (基準緩和) が再演されるリスク。

**Why:**
- 合格基準を結果確認後に変更する慣行ができると、最終 Phase 6-b の「月次 NET ≥ $1,900 全 3 ヶ月」も実行後に緩和される precedent になる
- audit#2 で既に指摘されていた spec 欠陥への遅延対応として正当化できる場合でも、メタルール明示なしの改訂は危険

**How to apply:**
- spec 改訂が必要なときは同時にメタルール (§1.6.1) を導入: 「Phase 実行前に基準確定・実行後の緩和禁止」
- 例外 (今回の遅延補正) は「最後の例外」として明示・適用範囲を明記
- Phase 6-b 等の最終 Phase には特に lock 文言を WORKFLOW.md に追記 (cap・Exit・$1,900 全 3 ヶ月)

---

### L-189: ハイパラ調整は構造的問題を解けない・Phase 4-b 設計で根本対処せよ（2026-05-14）

**何が起きたか:**
Phase 2 FAIL 受けて Phase 3 短期試行 (K 窓別 num_leaves)。24 組合せ加重 +8.72 → +9.86 (+1.14・閾値未達)。改訂後 spec (q99 8 組合せ加重) では +20.58 → +18.50 (悪化)。K12 LONG q99 のみ大幅改善 (+20pp) だが K24 SHORT q99 大幅悪化 (-26pp)。K48/K96 系・K96 SHORT q99 構造的逆行は完全に不変。

**Why:**
- 新 Phase 1 が既に旧 Phase 3-a 相当のハイパラ (lr=0.02・min_data_in_leaf=100・feature_fraction=0.7・bagging 等) で学習されており改善余地が小さい
- K96 SHORT q99 の暴騰局面集中 (2025-01/09 で 75% 集中) はハイパラとは独立な構造的問題 → regime 検知 (Phase 4-a) が必要
- K12 LONG MFE_lift マイナスは MFE 絶対値不足の問題 → TP 設計 (Phase 4-b) が必要

**How to apply:**
- Phase 3 ハイパラ調整は「微改善が見込めれば試す」程度・期待値を高く設定しない
- 構造的問題 (K96 SHORT 暴騰時逆行・K12 LONG 低 MFE) は Phase 4-a (cluster) / Phase 4-b (Exit) で対処
- 部分採用 (1 ラベルだけ別ハイパラ) は可能・bit-exact 再現性を確保する設計で残り 14 ラベル無影響を担保

---

### L-188: 部分採用 (1 ラベル別ハイパラ) で他 14 ラベル bit-exact 同一性を assertion で担保（2026-05-14）

**何が起きたか:**
Phase 3 trial で K12 LONG q99 net_quality が +20pp 大幅改善発見 → 「他は触らず K12 LONG MFE/MAE のみ num_leaves=15 で再学習」を採用したい。実装時に他 14 ラベル predictions が bit-exact 同一であることを保証する必要があった。

**Why:**
- 部分採用は「特定ラベルだけ改善・他は触らない」が前提
- 実装ミスで他のラベル predictions まで変えてしまうと「現行 Phase 1 を維持」という採用前提が崩れる
- 副作用検証なしで採用すると Phase 4-a クラスタリングの再現性も崩れる

**How to apply:**
- 部分採用スクリプトに「他 N ラベル bit-exact 同一」の assertion を埋め込む (`assert refit_test[lab].equals(p1_test[lab])`)
- 完了後 verify でも別途 grep / pandas equals で再確認 (二重チェック)
- 完了報告に「14 untouched ラベル + close 完全 bit-exact 同一」を明示

---

### L-187: 監査懸念に対する「入力段階解消」と「Exit 段階対処」の使い分け（2026-05-14）

**何が起きたか:**
Step 1-2 で監査懸念1 (K12 LONG MFE_lift マイナス) を mechanism 分析 → ML が「低ボラ・直近高値帯・上昇継続中」を選好。Phase 3 trial で num_leaves=15 だと MFE_lift -9.99% → +46.07% (+56pp 改善・低ボラ選好構造的解消)。これは「入力段階解消」(ML 自体の選好を変える) の例。一方 K96 SHORT q99 暴騰局面集中は num_leaves で変わらず → 「時期別 no-trade フィルタ (Phase 4-a/4-b)」が必要。

**Why:**
- 監査懸念には性質が異なる 2 種類ある:
  - (A) ML 自体の偏り (低ボラ選好等) → ハイパラ/特徴量で「入力段階解消」可能
  - (B) 市場局面固有の問題 (暴騰時 SHORT 誤発火等) → ML 出力後の「Exit/フィルタ段階対処」が必要

**How to apply:**
- 監査懸念を 2 種類に分類して対処レベルを選ぶ
- (A) は Phase 1/3 で構造的解消・(B) は Phase 4-a (cluster 分離) / 4-b (Exit 制限) で対処
- 「ハイパラ調整で全部解決できる」前提を持たない

---

### L-186: silhouette 評価で size_ratio (min/max) を併用して退化分割を排除（2026-05-14）

**何が起きたか:**
Phase 4-a k-means で k=2〜8 silhouette 評価。k=6 以降は silhouette がそれなりに高い (0.46/0.43/0.40) が cluster sizes の min/max ratio が 0.006 (= 933 行 vs 158,721 行) で 1 cluster が極端に小さい退化分割になっていた。silhouette だけで採用すると見落とす。

**Why:**
- silhouette score は globally good な分離度を見る指標で、極小 cluster が他から離れていれば高得点になりうる
- 実用 (Phase 4-b で各 cluster に Exit を設計) には「全 cluster にサンプル数が確保されている」ことが必要

**How to apply:**
- silhouette 評価には必ず min/max size ratio を併記する
- 採用候補は size_ratio ≥ 0.05 (= 全 cluster 5% 以上) のものに限定してから silhouette 最大を選ぶ
- 退化分割 (1 cluster < 1%) は採用候補から除外

---

### L-185: 証跡 verify で importance_type の不一致に注意 — script が 'split' 保存なら verify も 'split'（2026-05-14）

**何が起きたか:**
Phase 1 Step B 完了後の証跡4 (bit-exact reproducibility) で `LGBMRegressor.feature_importances_` の値が指示書の 「importance_type='gain'」 と一致しないと判定 → MISMATCH。実際には run_lgbm_phase1.py が `importance_type` を指定せず `model.feature_importances_` (デフォルト='split') を保存していた。verify 側が `importance_type='gain'` で再計算したため値が食い違った。

**Why:**
- 指示書に「gain で検証」と書かれていたが、スクリプトが実際にどの importance_type を使うかを実装 grep せずに従った
- 'split' (特徴量が分岐に使われた回数) と 'gain' (情報利得) は同じモデルでも値が全く異なる

**How to apply:**
- feature_importance verify 時は必ずスクリプト側の保存コードを grep して `importance_type` を確認してから verify を実装する
- LightGBM デフォルトは 'split'。指示書に 'gain' とあれば実装に不一致がないか先に確認する

---

### L-184: sys.exit(0) の直前にモデル保存コードがあっても、sys.exit が先に来るとモデルが保存されない（2026-05-14）

**何が起きたか:**
run_lgbm_phase1.py の dry-run pause セクションで `sys.exit(0)` (L-227) が `model.booster_.save_model()` (L-235) より前に実行される構造になっていた。1ラベル目の feature_importance 確認用 pause で中断すると、モデルファイルが保存されないまま終了。続きの Step B 実行時に dry-run 証跡が存在しないことに気づいた。

**Why:**
- コードの見た目上「保存処理がある」と判断し、実行順序 (sys.exit の位置) を確認しなかった
- pause → 中断 → 継続 という条件分岐で「中断時のみ実行される処理」を保存より前に書いてしまった

**How to apply:**
- sys.exit / return / break による早期終了の**前に**保存・flush・ログ書き出しが完了しているか必ず確認する
- 証跡として保存が必要なファイル (model.txt / CSV) は sys.exit より前の行に書く
- コードレビュー時は「この sys.exit に到達したとき、すでに保存は完了しているか」を 1 行ずつ確認する

---

### L-183: Phase 4-a/4-b/6-b で test data に対する fit / idxmax = data snooping 構造（2026-05-13）

**何が起きたか:**
- Phase 4-a (`run_phase4_a.py:215`): scaler/k-means を test 2025 で fit → クラスタ自体が 2025 に over-fit
- Phase 4-b (`run_phase4_b.py:330`): `cluster_best_exit` を test 2025 PnL で idxmax 選定 → Exit 規則が 2025 に over-fit
- Phase 6-b (`run_phase6_b.py:125-127`): **本テスト 2026 Q1 評価時にも test 2025 で再 fit** → クラスタが 2025 over-fit のまま 2026 評価
- artifact 名 `scaler_test2025.joblib` / `kmeans_k4_test2025.joblib` で test fit を公言・本番運用でもこれをロード
- Phase 5/5-c/5-d/5-e はすべてこの test-fit artifact を継承

**Phase 6-b 固有の最重要事案 (#13):**
本テスト評価時に scaler/km を再 fit すると、たとえ artifact が leak フリーでも
「test fit on train target」と同等の data snooping になる。
本テスト評価は必ず Phase 4-a で **train fit** した artifact を joblib ロードして
**transform/predict のみ** で実施。
v4 §6-b「未見データで 63-69% 維持」の正当性が崩壊した最重要事案。

**Why:**
- 「test 2025 の予測値を使ってクラスタを作る」のは「予測のクラスタ性質を分析する」発想として自然・しかし Exit 選定/評価に使うと data snooping
- 名前空間 "test_2025" でデータが流用される構造をスクリプトが互いに前提とし続ける
- artifact 命名で test data fit を公言しているのに警告がない

**How to apply:**
- fit / fit_transform / idxmax / argmax は入力が **train (train_2021_2024)** であることを実装で verify
- test 2025 / test 2026 Q1 入力は transform / predict / 計算後評価のみ (**再 fit 禁止**)
- 横展開 grep: `grep -rnE '\.fit\(|\.fit_transform\(|idxmax|argmax' scripts/priority_rebuild/` の入力データ全件 review
- artifact 名は "train_2021_2024" 等 fit データを反映・**"test" 名を禁止**
- Phase 7-c 起動時に artifact 名を log 出力 → "test" 文字列含むなら起動中止 (checklist 7c.9)
- 詳細: [.claude/rules/phase_compliance_checklist.md](../rules/phase_compliance_checklist.md) Phase 4-a/4-b/6-b/7-c

---

### L-182: バックテスト採用ロジックで「期間全体ソート」を使うと未来情報 leak 同等のバグ（2026-05-13）

**何が起きたか:**
- Phase 5-c 質駆動採用 (`run_phase5_c.py:97`) で `df.sort_values("pred_ratio", ascending=False)` と期間全体一括ソート → ループ i は時系列順ではなく品質順
- ある entry の採用判定で **pred_ratio がより高い未来 entry が既に taken** に入っているため、過去の判断を未来情報で覆す
- Phase 5-d/5-e がこの leak ロジックを継承 (`run_phase5_d.py:89-118`, `run_phase5_e` は 5-d 出力経由)
- コメント L237-239 で「異 timestamp の Entry を入れ替えるロジックは含まない」と書きつつ実装は入れ替えている → コメントが実装と矛盾

**Why:**
- バックテストで「最良の採用ルール」を再現したい誘惑から、期間全体ソートが直感的に書かれた
- 未来 entry の影響が active カウントに紛れ込む leak は、表面上「採用ループ」が時系列順に見えないだけで検出しづらい

**How to apply:**
- 採用ロジックは必ず `entry_ts` 昇順ループ + 各 bar 内のみで pred_ratio 優先順位付け
- ループ中に「未来の何か」を参照する箇所がないかチェックする (active counter は OK だが、未来 entry の存在自体を見ない)
- L-179 (leak 4 点) + 本 L-182 を Phase 4/5 系のチェックに組み込む
- 詳細: [.claude/rules/phase_compliance_checklist.md](../rules/phase_compliance_checklist.md) Phase 5 5.1-5.3

---

### L-183: §8 違反 (K12 LONG refit) - test 結果を見て学習データを変更 (2026-05-14)

**何が起きたか:** Phase 3 短期試行で「audit#3 K12 LONG MFE_lift -9.99%」を発見 → K12 LONG のみ num_leaves=15 で refit (commit d9d322c)。MFE_lift -9.99% は **test 2025** の数値 (net_quality_24combinations.csv 由来)・train では +364.97% で正反対。test 結果を見て学習データを変更 = §8「テスト結果を見てから学習データで再学習する際、テスト結果を直接参照しない」直接抵触。監査#7 で発覚。

**Why:**
- audit#3 の「K12 LONG MFE_lift マイナス」を train 由来問題と誤認
- 数値の出所 (train か test か) を着手前に確認しなかった

**How to apply:**
- ML 関連の数値を引用する前に出所 (train / test / refit 前後) をパスまで確認
- `feedback_pre_execution_premise_check.md` 4 項目を着手前に通す
- §8 違反かどうかを学習データ変更前に必ず確認

---

### L-184: spec/script 乖離 - 案 G で spec を改訂したが script を改修せず手計算で補完 (2026-05-14)

**何が起きたか:** 案 G (commit b14be88) で §1.6 指標 1 を「q99 8 組合せ加重 + 6/8 positive」に改訂したが、run_phase2_precision.py の改修が案 G タスクに含まれず。元 Phase 2 / 案 Z の自動判定は旧 spec (24 組合せ加重 + 20 positive) で実行され FAIL。両完了報告は手計算で「改訂後 spec PASS」を提示・公式判定 source と認識されていた。監査#8 で発覚。

**Why:**
- spec 改訂タスクに対応する script 改修が連動していなかった
- 完了報告の手計算を「公式判定」と扱う暗黙慣行

**How to apply:**
- spec 改訂時は対応 script の grep verify を同タスクに含める
- 公式判定 source は `phaseX_summary.json` (script 出力) のみ・完了報告内手計算は「参考」と明記 (WORKFLOW.md 「公式判定 source の定義」)
- L-179 拡張 (ML leak 限定 → spec/実装一般整合性) を本日適用済

---

### L-185: ファイル名一意化 - フォルダ違い同名でチャット添付時に取り違え多発 (2026-05-14)

**何が起きたか:** `ml_phase2_rerun_prerefit/net_quality_24combinations.csv` と `ml_phase2_rerun_postrefit/net_quality_24combinations.csv` (同名・フォルダ違い) でチャット添付時に Web Claude が取り違え 3 回発生。チャット添付ではフォルダ階層が失われるため、ファイル名だけで識別可能であるべき。

**How to apply:**
- 比較・対照される成果物 (prerefit/postrefit・複数 k・複数 option) はファイル名末尾に識別子付与
- 例: `*_PREREFIT.csv` / `*_POSTREFIT.csv` / `*_DRIFT.csv`
- 「注意力で防ぐ」のではなく「命名規則で物理的に防ぐ」
- 詳細: WORKFLOW.md 「成果物ファイル名の一意化ルール」 (2026-05-14 追加)

---

### L-186: 着手前 premise check 4 項目 (2026-05-14)

**何が起きたか:** 詳細な指示書 (監査済/Web Claude レビュー済/まこさん GO 済 三段書き) を受領した時、「手順をなぞれば責任を果たした」と錯覚し、指示書自体の前提を疑う動作を省略していた。L-183 (§8 違反 K12 LONG refit) / L-184 (spec/script 乖離) はいずれも着手前 verify で防げた。

**How to apply (毎タスク Step 0 着手前に 1 行ずつ宣言):**
1. 指示書が当然視している判定が script 自動か手計算か
2. 数値の出所 (train / test / 間接参照のどれか)
3. 指示書の前提 X はデータ Y で verify できるか
4. 必読ファイル引用 (Step 0-1) と指示書の論理的整合 (機械的に貼るだけでなく内容照合)

1〜4 のいずれかに疑義があれば着手前にチャットで提示して GO 待ち。
詳細: `~/.claude/projects/.../memory/feedback_pre_execution_premise_check.md`

---

### L-181: 設計転換時の旧記述放置を「毎回やってる」とまこさんに命令で禁止（2026-05-13）

**何が起きたか:**
2026-05-13 leak 修正セッションで Step 0 ③ の前提条件「walk-forward 5 fold・MFE/MAE 中央値+比」を verify せず読み上げ → まこさん指摘で古い記述発覚。grep sweep したところ WORKFLOW.md / CLAUDE.md / .claude/memory/ 配下に**旧「段階 A-1〜D」framework の残骸が大量に放置**されていた (2026-05-11 大方針転換 + 2026-05-13 ML pipeline 切替時に新方針セクションだけ追加・旧記述未削除)。まこさんから「この古い情報のまま放置するミスは毎回やってる」「二度とやらないで」「これは命令」と禁止された。

**Why:**
- 設計転換時に「新方針セクションを足したから OK」で完了とみなし、旧方針記述の grep sweep をスキップする癖がある
- 「他のドキュメントは後で直す」と保留して結果残骸化
- セッション間で全体整合性チェックがなく、複数セッション通過後に発覚

**How to apply:**
- [feedback_design_transition_grep_sweep.md](~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_design_transition_grep_sweep.md) (命令) 参照
- 設計転換が決まったら旧設計の固有名詞を全プロジェクト grep → ヒット 1 件ずつ判定 (削除 / 🧊 注記 / 置換) するまで完了とみなさない
- 大方針転換コミット直後セッションでは feedback_design_transition_grep_sweep.md を Step 0 で必ず再読

---

### L-180: WORKFLOW/CLAUDE/memory 引用前 実装 verify 必須・L-179 から 1 セッションで別面に再発（2026-05-13）

**何が起きたか:**
2026-05-13 セッションで L-179 (ML leak チェック) を memory に書いた**直後の次セッション 1 ターン目**に、WORKFLOW.md Step 0 ③ の「walk-forward 5 fold・MFE/MAE 中央値+比」を verify せず読み上げ → まこさん指摘で古い記述発覚。L-179 を書いた直後に「ドキュメント信頼」の穴が別面に再発した。L-179 は特徴量コードの leak チェックを止めただけで、Step 0 で読み上げる前提条件そのものの verify は組み込まれていなかった。

**Why:**
- L-179 の教訓を「特徴量コード verify」と狭く受け取り、「ドキュメント全般を verify」に拡張しなかった
- WORKFLOW.md が「セッション開始時必読」リストに入っているため「読んだ = 信頼できる」と扱う癖
- 教訓追加だけでは「頭で分かっていても漏れる」癖を止められない (L-159/L-160 と同じ構造)

**How to apply:**
- [feedback_doc_verify_before_quote.md](~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_doc_verify_before_quote.md) 参照
- WORKFLOW.md / CLAUDE.md / .claude/memory/*.md / 仕様書 (cc_*.md / handoff_*.md) の記述を Step 0 やレポートで引用する前に、必ず実装/直近コミットで grep verify する
- WORKFLOW.md に Step 0 ⓪ を追加 (本セッションで実装済)
- 「ドキュメントに書いてあったから引用しました」は理由にならない・実装で verify する責任は引用者にある

---

### L-179: 未来データ参照 leak が ML パイプライン Phase 1〜7-a の全 14 段階を素通り・本番投入直前で発覚（2026-05-13）

**何が起きたか:**
Web Claude 仕様書に基づいて構築した ML パイプライン (16 LightGBM + KMeans k=4) で、
特徴量計算側 (`structure_features.py:_detect_fractals`) が中央バー j で
j+1, j+2 (未来 2 本) を比較して fractal を確定し、後段の
`compute_c1_features` / `compute_c4_v2_features` で `is_res[start:i+1]`
(= j ∈ [start, i]) を参照していた。これにより j = i-1, i の fractal が
i 行の特徴量に **未来 2 本のデータを含む形で流入**。

Phase 1 → 2 → 3-a → 3-b → 4-a → 4-b → 5 → 5-b → 5-c → 6-a → 6-b → 7-a の
12 段階 + 5-d / 5-e の 14 段階すべてで leak チェックを行わず、本テスト
2026 Q1 (out-of-sample) 3/3 合格まで素通り。Phase 7-b 着手直前にまこさんの
「特徴量に未来データ使ってないか」指示で初めて検証し、feature_importance top7
(rank 1-7) が全て fractal ベース列 (dist_to_fib_v2_* / resistance_distance_*)
で占有されていたことを確認。Phase 1〜7-a の全数値は信頼性疑義 = 無効扱い。

**Why:**
- `structure_features.py:299` の「look-ahead 完全防止 (中央バー j で確定する
  fractal は j ≤ i-2)」というコメントを verify せずに信頼した
- Web Claude 仕様書 + CC 実装の役割分担を「責任の分離」と誤認し、構造検証を
  実装者責任で行わなかった
- out-of-sample (本テスト 2026 Q1) 合格を「leak なし」の証拠と誤認した
  (同じ leak 規則が test 側でも漏れていれば偽精度が出る)
- Phase 3-b で `feature_importance_top20.csv` を保存していたのに review しなかった

**How to apply:**
- ML 系作業の着手前に必ず `feedback_ml_leak_mandatory_check.md` (memory) の
  4 点チェック (grep / 使用箇所 verify / timestamp range / feature_importance
  即時 review) を実行する
- コードコメントの「look-ahead 防止」表記を信頼しない。実装で守られているか
  を必ず verify
- out-of-sample 合格を leak フリーの証拠と誤認しない
- 詳細は [results/priority_rebuild/leak_incident_20260513.md](../../results/priority_rebuild/leak_incident_20260513.md)

**2026-05-14 拡張 (監査#8 必須 5)**: L-179 の「実装で verify」原則は ML leak 限定ではなく、
**spec / 実装の一般的整合性に適用する**。
- spec 改訂時は必ず対応スクリプトの該当箇所を grep verify する (例: 案 G 改訂時に
  run_phase2_precision.py L72-73 を grep して値が反映されたか確認)
- 完了報告の「PASS / 合格」表記を信頼せず、`phaseX_summary.json` の `overall_pass` を
  実物で verify する (WORKFLOW.md「公式判定 source」準拠)
- 背景: 2026-05-14 監査#8 で run_phase2_precision.py が案 G (commit b14be88) の §1.6
  改訂を反映していなかった事案を発見 (元 Phase 2 + 案 Z で 2 度 implementation gap が
  気づかれずに通過していた)

**修正完了 (2026-05-13 セッション末):**
- `_detect_fractals` を**返り値 4 配列に拡張** (`is_res, is_sup, pivot_high, pivot_low`)、ピボット確定タイミングを j+2 バー後ろシフト
- `is_res[i]=True` のとき `pivot_high[i] = h[i-2]` → i 時点で確定済みの過去データのみ参照
- `compute_c1_features` / `compute_c4_v2_features` の使用箇所を `pivot_high/pivot_low` 経由に置換
- 監査範囲 5 ファイル・4 種 grep で fractal 以外に新規 leak なし確認
- データ・モデルは依然 leak 由来 → Phase 1 から再学習が必要

---

### L-178: ML パイプライン (LightGBM + KMeans) は scaler/kmeans の joblib 保存 + deterministic 検証で完全再現可能（2026-05-13）

**事実:**
Phase 4-a で fit した StandardScaler + KMeans を後で再 fit する際、Phase 4-a の cluster_labels_k4.parquet と完全一致した。LightGBM Booster の予測も batch / 1-row どちらも diff=0.0e+00。`scripts/priority_rebuild/verify_ml_inference.py` で全 4 検証項目 PASS。

**Why:** sklearn StandardScaler / KMeans / LightGBM 全てが `random_state` 固定下で deterministic。同じ入力 + 同じ random_state なら結果は浮動小数点誤差なしに一致する。

**How to apply:**
- 本番運用候補のアーティファクトは joblib (scaler/kmeans) + LightGBM.save_model() で保存習慣化
- 「保存忘れて再 fit」は時間ロス。fit 時に即 joblib.dump する
- Bot 統合前に「batch 予測 vs 1-row 予測」「保存前 vs ロード後」の完全一致検証を入れる
- 完全一致が確認できれば「リアルタイム推論で別結果が出る」リスクなしで本番進める

---

### L-177: 同時保有 active カウントは timeline 配列の範囲 increment が O(N²) を O(N×K) に高速化（2026-05-13）

**事実:**
Phase 5-c の質駆動採用 (predicted ratio 降順 + cap) を最初 O(N²) で実装 (`sum(1 for ae, ax in taken if ae <= et < ax)`)。test 2025 48k entries × cap=5 で **30 分**かかり、cap=10/20 で数時間想定。numpy timeline 配列 (`active[entry_bar:exit_bar+1] += 1` ・採用判定は `active[entry_bar] < cap`) に書き換えたら **1.2 秒** で全 cap 完了。

**Why:** O(N²) の N=48k は 2.3B op で Python forloop には重すぎる。timeline 配列は O(N × K_avg=100) = 5M op で済む。

**How to apply:**
- Replay/シミュレーションで「同時保有」「active 件数」「重複判定」を扱うときは **timeline 配列の範囲 increment** が第一選択
- bisect + sorted list は理論計算量は良くても `list.insert` の O(N) shift がボトルネック
- 「Python で素直に書く」段階で N²/N³ になりかけたら、必ず timeline 配列か bucket 化で抑える

---

### L-176: FIFO 採用は仮テスト合格でも本テストで月次未達のリスクがある・質駆動採用で解消（2026-05-13・⛔ 数値は leak 由来）

> ⛔ 本教訓内の具体数値 (12/12 合格・$173k・-$1,708〜-$4,140 等) は L-179 leak 由来。**構造的洞察 (FIFO vs 質駆動の対比) は leak フリー再学習でも再評価して valid なら再記録する。数値の引用は禁止 (L-180)。**

**事実 (⛔ 数値無効):**
Phase 5-b (FIFO・early-arrival) で仮テスト 2025 は cap=5/10/20 全て 12/12 合格。Phase 6-b の本テスト 2026 Q1 では **2026-02 だけが cap=5/10/20 で全部マイナス** (-$1,708 〜 -$4,140)。no cap だと同月 +$173k で最大利益月。FIFO が「最初に来た負け Entry」を採用して、後の勝ち Entry を逃した。Phase 5-c で質駆動 (predicted MFE/MAE 比 降順) に切り替えたら 3/3 合格。

**Why:** FIFO は時系列順序のみが基準で、Entry の **品質** を一切見ない。仮テストでは品質と時系列がたまたま揃っていたが、本テストで揃わなくなった。

**How to apply:**
- Position 制限のある Replay では FIFO だけで判定しない。**必ず質駆動採用と並列比較する**
- 仮テスト 100% 合格 → 本テスト未達のリスクがある事例として記憶。OOS で必ず再検証する
- 質駆動採用のスコア軸は「予測 MFE/MAE 比」が今回有効。他軸 (predicted MFE 単独 / cluster 優先度) も将来検討

---

### L-175: 長時間バックグラウンド Python スクリプトは print(flush=True) を徹底する（2026-05-13）

**事実:**
build_labels.py を `nohup ... > stdout &` で 89 分走らせたが、stdout が空のまま。Python print は line-buffered だが TTY 接続なしだと block-buffered で flush されない。プロセス CPU は動いており、内部処理は進んでいたが、外から進捗確認できなかった。完了時にまとめて flush された。run_lgbm_phase1.py 等で `print(line, flush=True)` を入れたものは即時 stdout に出ていたので、対策は明確。

**Why:** Python の I/O buffer は TTY 接続時のみ line-buffered。`>` リダイレクトでは block-buffered (~4KB ごと) のため、長時間処理の途中 print が見えない。

**How to apply:**
- 長時間 (10分超) 実行する Python スクリプトの print は **必ず `flush=True` を指定**
- log() helper を作るなら最初から `print(line, flush=True)` で書く (Phase 1-6 のスクリプトはこれを採用済み)
- 環境変数 `PYTHONUNBUFFERED=1` でも回避可能だが、コード側で明示するほうが安全
- 既存スクリプトに print が多い場合は `python3 -u` でも同等

---

### L-174: 月次平均だけでなく月別 worst month と win rate ばらつきも評価軸に入れる（2026-05-13）

**事実:**
Phase 5 で月次平均 $166k / Phase 6-b 本テストで $120k と高い数字が出たが、本テストの 2026-02 が cap 入れると軒並みマイナスで「月次平均は良くても **特定月だけ崩れる**」現象が露呈した。仮テスト 2025 の 2025-09 も他月の 1/10 規模で弱かった。月次平均だけ見ていると、これら「弱月」を見落とす。

**Why:** 月次平均は外れ値月でも引き上げられる。指示書 §6 の合格条件は「全月クリア」なので、平均ではなく最弱月で判定する必要がある。

**How to apply:**
- 月次集計時は必ず {mean, min, max, std, worst-month-id} を併記する
- §6 合格判定は最弱月で行う。「平均は X 倍超」は補助指標
- 弱月の原因分析: cluster 分布 / Entry 種別 / 市況 (volatility / trend) を切り分ける
- 改善時も「最弱月の押し上げ」を狙うほうが平均改善より価値が高い

---

### L-173: ML 統合は新規ファイル (`cat_ml_decider.py` 等) で実装し、既存 V9 (P1-P23) には触らない（2026-05-13）

**事実:**
Phase 7 Bot 統合の設計で、既存 `cat_v9_decider.py` (823行) を改修するか新規 `cat_ml_decider.py` を作るか検討した。CLAUDE.md「現在の方針」で「既存 P1/P2/P4/P21/P23 は **改修ではなく解体・再設計**」とあり、新規 ML Priority として実装する方針が妥当。既存安全装置 (ALLOW_LIVE_ORDERS / paper_trading) を維持しやすい。

**Why:** 既存 V9 改修は 1) 安全装置を壊すリスク 2) P1-P23 ロジックと ML ロジックの混在で複雑度爆発 3) ロールバック困難 で危険。新規ファイルは並走テスト + 単独ロールバックが容易。

**How to apply:**
- Bot 統合は「新規 strategies/cat_ml_decider.py + runner/run_once_ml.py」方式で進める
- 既存 V9 (run_once_v9.py / cat_v9_decider.py) は **触らない**
- ALLOW_LIVE_ORDERS / paper_trading の確認はまこさん側 (機密パスは私から読まない)
- Phase 7-c で runner 起動可能化、Phase 7-d でデモトレード起動 (まこさん明示 GO 必須)

---

### L-172: dashboard 用 JSON 化で pandas NaN を残すと JS の JSON.parse が破綻する（2026-05-12）

**事実:**
頭打ち原因分析 (⑮ タブ) で `mw_u_pvalue_mae_vs_random` 等の列に NaN が残ったまま `json.dumps(data, ensure_ascii=False)` で書き出した。Python は `allow_nan=True` がデフォルトのため `NaN` トークンを許容するが、JS の `JSON.parse` は JSON 仕様外で拒否 (`SyntaxError: Unexpected token 'N'`)。ブラウザの ⑮ パネルが全パネル空表示になった。

**Why:** Python と JS の JSON 厳格度の違いを知らず、Python 側で valid なら通ると思い込んだ。pandas `df.where(df.notna(), None).to_dict()` も列によっては NaN が残る (浮動小数列は dtype 維持のため Python None ではなく NaN として扱われる) 。

**How to apply:**
- ブラウザ配信用 JSON は **必ず** `allow_nan=False` を指定する (落ちれば事前検知できる)
- 加えて再帰的に NaN→None を置換する helper を通す:
  ```python
  def clean_nan(o):
      if isinstance(o, dict): return {k: clean_nan(v) for k, v in o.items()}
      if isinstance(o, list): return [clean_nan(v) for v in o]
      if isinstance(o, float) and math.isnan(o): return None
      return o
  ```
- 検証コマンド: `node -e 'JSON.parse(require("fs").readFileSync("path.json","utf8"))'` を完了報告必須証跡 4. に追加 (Python の `json.load` は lenient なので不可)

---

### L-171: 設計議論で行き詰まったら別 AI 分業に切り替える（2026-05-12）

**事実:**
A-2 設計議論で 1 セッション中に 6 回設計を撤回（閾値辞書要否・中央値固定・k=2固定・レビュー方式・信頼度区分・月次$1,900判定軸）。私が事前に全論点を出さず、ユーザー指摘で都度後付け修正する癖が原因。Claude Code は実装が前提のワークフローのため、長い設計議論で context が分断され一貫性を保てない。まこさんが「Claude Code は設計議論が不得意か？」と問い、Web Claude で大枠を詰める分業に切替を決定。引き継ぎ資料 [handoff_to_web_claude.md](../memory/handoff_to_web_claude.md) を作成。

**ルール:**
- 設計議論を 3 ターン以上続けて結論が固まらない/同じ撤回パターンが出たら、別 AI 分業を提案する
- 別 AI に渡すときは self-contained な引き継ぎ資料を作成（リポジトリアクセス不可前提で数値・経緯・制約をすべて文書内に明記）
- 引き継ぎ資料には「Claude Code 側の手戻り癖」も書く（別 AI が同じ穴に落ちないため）

**Why:** Claude Code はツール呼び出し中心の対話で、長い論理連鎖が分断されやすい。設計議論で一貫性を保つには、別の長文思考が得意な AI（Web Claude / ChatGPT 等）に大枠を詰めさせ、結論を Claude Code に持ち込んで実装する分業が合理的。

**How to apply:**
1. 設計議論で 2 ターン連続で撤回が出たら「Web Claude 分業」を提案する
2. 引き継ぎ資料は handoff_to_*.md として `.claude/memory/` に保存
3. 大枠（L0-L3）は別 AI で確定 → 詳細（L4-L5）は Claude Code で詰める分業を基本パターンに

**関連:** L-169 / L-170 / handoff_to_web_claude.md

---

### L-170: 段階間の役割を混同しない（A-2 で月次 NET を判定しようとした失敗）（2026-05-12）

> ⚠️ 「A-2 / 段階 B / 段階 D」は旧 framework (2026-05-13 ML pipeline 切替で廃止・現方針は Phase 0〜7)。
> 但しこの教訓の**構造的ロジック**（次段階の入力に依存する判定を当該段階で先行させない）は普遍的に valid・Phase 0〜7 にも適用可。

**事実:**
A-2 設計で「擬似 NET 試算で月次 $1,900 到達見込みを判定」というステップを設計した。しかし A-2 は Entry 規則探索段階で、Exit 設計（TP/SL/トレーリング/時間Exit）は段階 B で行う。Entry だけで月次 NET を判定するのは構造的に不可能（TP/SL 仮置きの擬似試算は偽の Replay）。まこさん指摘で気付き撤回。月次 $1,900 判定は段階 D まで遅延すべき。

**ルール:**
- 段階別フローを設計するとき、各段階の**入力 / 出力 / 判定対象**を明示する
- 判定対象が次段階の入力に依存する場合、その段階で判定しない（次段階に委ねる）
- 「整合的に見える」基準を後付けで入れない（A-2 に月次 $1,900 判定を入れたのは整合性偽装）

**段階別役割の正解:**
| 段階 | 最適化対象 | 判定対象 |
|---|---|---|
| A-2 | Entry 質 | Entry エッジ強さ（MFE/MAE 比・年別安定度・発火頻度）|
| 段階 B | Entry × Exit | 365d Replay 月次 NET |
| 段階 D | 統合 | 月次 ≥ $1,900 全 12 ヶ月クリア |

**Why:** Entry/Exit は不可分。Entry だけで月次 NET を試算しようとすると TP/SL を仮置きせざるを得ず、本物の Replay と乖離する。段階分割の本質は「測定単位の独立性」を保つこと。

**How to apply:**
1. 設計段階に名前を付ける前に、入力/出力/判定対象の 3 軸を表で出す
2. 判定対象が「次段階で初めて測れる」なら、当該段階の合格条件にしない
3. 後付けで「整合的に見える」基準を追加したくなったら、なぜそう感じるかを 1 行書いてから採否判定

**関連:** L-169 / L-163 / handoff_to_web_claude.md §7

---

### L-169: 既存フレーム流用の罠 + bottom-up 思考の弊害（2026-05-12）

**事実:**
A-2 設計で priority_rebuild.md §2.4「閾値 = train 中央値」を疑わず流用した。これは regime 研究 stage2 のフレーム（regime label を当てる目的）であり、Priority 再構築（Entry エッジを見つける目的）とは目的が違う。中央値固定では RSI 30 / ADX 25 等の意味的閾値を取りこぼす構造。まこさん指摘で気付き 4 ターン後に撤回。さらに L4（Entry 規則詳細）から議論を始めて L2/L3（戦略骨格・Priority 枠組み）を飛ばす bottom-up 癖も併発。

**ルール:**
- 既存ドキュメント（priority_rebuild.md / WORKFLOW.md 等）の前提条件を流用する前に「**この前提は今の目的と一致しているか**」を 1 行書く
- 設計議論は L0（目標）→ L1（全体構成）→ L2（戦略骨格）→ L3（Priority 枠組み）→ L4（Entry 詳細）→ L5（Exit 詳細）の順に top-down で詰める
- L4 から議論を始めない（必ず L2/L3 を確認してから降りる）

**Why:** 既存フレーム流用は「思考の節約」だが、目的が違うフレームを流用すると構造的に間違った設計になる。bottom-up は局所最適に陥り、全体の整合性を破る。

**How to apply:**
1. 設計議論の最初に L0-L5 階層を表で出して、確定済み / 未確定 を区別
2. 既存フレームを流用するときは「元フレームの目的」と「今の目的」を 1 行ずつ書いて一致確認
3. L2/L3 が未確定のまま L4 議論に降りない（思考フレーム自己点検 L-136 の手順 1-3 を実行）

**関連:** L-136 / L-170 / L-171 / WORKFLOW.md 思考フレーム自己点検

---

### L-168: 目標は「下限」か「達成目標」か区別する（2026-05-12）

**事実:**
セッション初期、まこさんの「最低でも $60/day 以上」を「達成目標 $60/day」と読み、CLAUDE.md の「100 件/日 × $0.60 = $60/day」と組み合わせて「シグナル発火頻度は日 30-100 回必要」と誤推論した。まこさん指摘で「100 件/日」は手数料逆算の計算例示であり目標値ではないと判明。さらに「下限」「合格ライン」「目標」の語感が混在しており、CLAUDE.md・WORKFLOW.md・MEMORY/project_goal.md で数値が食い違っていた（$60/day vs $120/day）。MEMORY/project_goal.md を一次ソースとして月次 $1,900 に統一・全 6 箇所を書き換え。

**ルール:**
- 「最低でも X 以上」は**下限 / 合格ライン**であり、**達成目標**ではない
- 件数の例示（手数料逆算）を**達成すべき目標値**と読まない
- 数値の正本ファイル（MEMORY/project_goal.md）を 1 箇所に固定し、他ファイルからは「一次ソース: project_goal.md」と参照表記する
- 「日次絶対下限」と「月次合格ライン」は別概念（日次は変動 OK・月次が判定軸）

**Why:** 目標定義のズレは全設計を歪める。「月次 $1,900」と「日次 $60」と「100 件/日」は同じ次元ではない。「最低でも」「以上」「目標」「下限」「合格ライン」の語感を正確に区別する規律が必要。

**How to apply:**
1. 目標定義を Step 0 で必ず**月次基準**で確認（デイリーは目安）
2. 数値が複数ファイルに散らばっていたら「一次ソースはどれか」を最初に特定
3. 件数の逆算式（100 件 × 手数料率 = ...）を見たら、計算前提か目標値か 1 行で識別
4. CLAUDE.md「目標」セクションには **❌ 禁止する誤読** リストを必ず置く

**関連:** MEMORY/project_goal.md / CLAUDE.md 目標表 / WORKFLOW.md Step 0

---

### L-167: pandas method chain で reset_index 前後の参照ズレに注意（2026-05-12）

**事実:**
build_labels.py attach_upper_tf で `feat = feat.reset_index().rename(columns={feat.columns[0]: "_close_t"})` と書いた。`feat.columns[0]` は **reset_index 前** の feat の最初の列（最初のデータ列）を指していたため、`timestamp` 列はそのまま残り、float64 のデータ列が `_close_t` に rename された。merge_asof で dtype 不一致 (datetime64 vs float64) で失敗。段階 2 (--sample-days 7) で初検出。dry-run では merge_asof を通らないため検知不可だった。

**ルール:**
- `df = df.reset_index().rename(columns={df.columns[0]: ...})` のように **method chain 内で評価順序がブレやすい操作**は分割する
- index を named にしてから reset_index する方が堅牢:
  ```python
  df.index.name = "_close_t"
  df = df.reset_index()
  ```
- `feat.columns[0]` のような暗黙的参照は、想定する列が固定されているか確認する

**Why:** Python の式評価では `feat.reset_index()` で新しい DataFrame が返るが、`columns={feat.columns[0]: ...}` の `feat` は元の (reset_index 前) feat を指す。「列位置でアクセスして rename」のような書き方は副作用と評価順序に脆い。

**How to apply:**
1. rename + reset_index 組合せでは index.name 経由が安全
2. method chain で同じ変数を 2 度参照する場合、評価タイミングを意識する
3. 段階 2 (sample) のような中間検証段階は、dry-run で検知できない実行時バグの早期発見に不可欠（3 段階フロー §3.0 の設計妥当性が実証された）

**関連:** priority_rebuild.md §3.0 3 段階実行手順 / build_labels.py attach_upper_tf

---

### L-166: 着手前の目的整合性チェック（粒度・カバレッジ・直接性の 3 項目）（2026-05-11）

**事実:**
trade × 4h 教師ラベル境界 整合性検証で、着手前にズレを察知できたのに作業を進めた。
trade median 15min vs 教師 4h 粒度 → 構造的に境界跨ぎ稀（→ STRICT で 0 件確定）。
教師ラベル 54% 密度 + 2026 Q1 ゼロ → 1,157 trade 中 88% UNDETERMINED で判断分岐（90%/70%/50%）を適用するのは無理筋。
途中で IMPLIED 定義を独走（指示外）で導入して数字を出したが、まこさんが Web Claude に確認して「テスト無効」判明。1 ターン分の工程・コード・チャット容量が無駄。

**再発防止:**
着手前チェック 3 項目（順番厳守）:
1. データ粒度 vs 検証対象粒度: 結果が構造的に出るか（例: trade 15min × 教師 4h → 跨ぎ稀）
2. データカバレッジ: 判定対象標本が判断分岐閾値（例 90%）を成立させるのに十分か
3. 直接検証 vs 代理指標: 目的を直接測れる別手段（例: Replay 比較）がないか

1 つでも NO/不明なら、作業前にチャットで「この手順は目的に対して構造的に弱い理由 + 代替案」を 200 字以内で提示する。

完了報告で「サンプル小に留意」と書くのは遅い。**着手前に止める**。

**関連:** [feedback_early_objection.md](../../../../../../tachiharamasako/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_early_objection.md) / L-163 / L-164

---

### L-165: 詳細な仕様が来ても目的整合性確認を省略しない（2026-05-11）

**事実:**
ユーザーから「判断分岐」「絶対禁止」「完了報告必須証跡 4 点」付きの詳細仕様が来ると、**仕様精度の高さに引っ張られて「黙って従う」モード**に入ってしまった。具体的には trade×境界テストで「IMPLIED 定義の独走（指示外追加）」を完了報告まで気付かず実行した。feedback_discussion_style に「能動的に意見」と書いてあるのに、仕様詳細度が高いと適用が弱まる癖がある。

**再発防止:**
- 「詳細な仕様 = 必ず正しい」ではない。**前提条件のズレは仕様詳細度と独立に存在する**
- 仕様で禁止されている事項（「独自定義禁止」等）を**回避策**として導入したくなったら、その時点で停止して提示
- 「指示通り進めば責任は薄い」モードを警戒する
- 仕様詳細度が高いほど目的整合性チェックを**強める**（弱めない）

**関連:** L-166 / feedback_discussion_style / feedback_no_unauthorized_changes

---

### L-164: 段階定義は規定 (regime_research.md §3) を必ず確認してから着手（2026-05-10）

**事実:**
段階3 検証 連続 2 回不合格を受けて「(B) Replay 評価」を独自フェーズとして実行。実際は regime_research.md §3 で「3-2 = 実装（VERSION 上げ・diff GO）」と定義されている。私が「3-2 = Replay 評価」と独自再定義 → regime 確定前の Priority 経済価値評価 = WORKFLOW.md「regime 確定まで Priority 最適化全停止」と矛盾する作業に侵入。まこさん撤回指示で気付いた。

**ルール:**
- 段階フェーズ名（3-1 / 3-2 / 3-3 等）を使う前に必ず regime_research.md §3 のフロー本体を確認
- 規定にない独自フェーズを定義するときは「規定外フェーズ」と明示し、まこさん戦略判断 GO を取る
- 「次のフェーズ」「次の段階」と進める前に、それが既存規定のどこに該当するかを 1 行で言語化
- regime 確定前は **Priority パラメータ・既存戦略の経済価値評価系作業** には立ち入らない（Replay 実行を含む）

**Why:** WORKFLOW.md「regime 確定まで Priority 最適化全停止」は明示規定。フェーズ名の独自再定義は規定回避と機能上同じ。今回は Priority パラメータ自体は変更しなかったが、Replay 1 回 + regime ON 判定式の経済価値評価という侵入が発生。

**How to apply:**
1. 段階フェーズに進む前に regime_research.md §3 の該当行を引用してから着手
2. 独自フェーズ案は「規定外」と明示してまこさん GO 取得
3. Replay 実行は regime 判定 GO 後のみ
4. 段階3 不合格時は「3-1 不合格 → 段階2 戻り / 連続 2 回不合格 → 思考フレーム自己点検」の規定フローに従う

---

### L-163: 段階設計時に「学習目的 vs 検証目的の整合性」を必ず確認（2026-05-10）

**事実:**
段階1+2 で「切替点 t=0 の 1 バー」を target_match の母数として学習。段階3 検証で「regime 持続区間全体」と比較 → 2025 年一致率 7%・持続中央値 5 バー（22.5 分）で大幅未達。学習対象（切替点・1 バー）と検証対象（持続区間）の評価単位が不一致。段階2 設計時にこの構造ミスマッチを詰められなかった。

**ルール:**
段階設計（特に段階1 / 段階2 / 段階3 の境界設定時）で必ず以下を明示する:
1. **学習側の評価単位**（1 バー / 連続区間 / 何 N バーウィンドウ / etc.）
2. **検証側の評価単位**（同上）
3. **両者が一致しているか**（一致してない場合、後段の合格基準が達成不可能な構造）

不一致のまま進める場合、回避策（後処理 / 検証指標変更 / 学習目的変更）を着手前に明示する。

**Why:** 学習対象と検証対象が異なる評価単位だと、学習側で良い数値が出ても検証側では達成不可能になる。今回は段階1+2 の 12+ 時間投下が部分的に無駄になりかけた（latch 後処理で救済中）。段階設計時の 5 分の確認で防げる構造的問題。

**How to apply:**
1. 段階素描で評価単位を必ず言語化（「target_n は ○○ 件・1 サンプル = △△」）
2. 段階間で評価単位が変わる場合、その変換ロジックを設計に含める
3. 「学習で 80pt の乖離 → 検証で何になる前提か」を着手前に算出してまこさんに提示

---

### L-162: 段階1 結果観察報告で絞り込み示唆表現禁止（2026-05-09）

**事実:**
intra_axis_correlation.md 抜粋報告で「採用候補にならない」「安定した採用候補」と書いた。観察事実 (数値) を超えて段階2 母集団からの絞り込みを暗黙に示唆。3原則 #3 + L-159/L-160 の精神延長違反。L-160 (2026-05-08 学習) から 1 日で再発。

**ルール:**
段階1 結果のチャット報告・md 出力で以下の表現を使わない:
- 「採用候補にならない / になる」
- 「切れる / 残せる / 除外して良い」
- 「効く / 効かない」
- 「重要 / 不要」
- 「優先 / 後回し」
- 「使える」「意味がある / ない」

観察は「数値の事実 + 軸/カテゴリ間の比較」のみ。判断はまこさん。

**Why:** 観察として書いた示唆表現が後続セッションで「段階1 で否定された素材」と認識され、段階1 で絞り込んだのと同じ結果になる。L-160 の Claude 主導カテゴリ抽出と同種パターン。「頭で分かっていても漏れる」癖は手続きで矯正するしかない (思考フレーム自己点検 L-136 と同じ思想)。

**How to apply:**
1. 段階1 結果を出す前に「数値以外の判断語彙を含んでないか」自問
2. 含むなら数値表記に置き換える
3. WORKFLOW.md「完了報告必須証跡 5点」§5 の自己 grep を実行（grep 結果なしでは完了報告として認めない）

---

### L-161: 完了報告前にコードハードコード総点検必須（2026-05-08）

**事実:**
段階1-A の TIMEFRAMES 修正後、`pattern_specificity_analysis` 内の `endswith(("__5m", "__1h", "__4h", "__1d"))` ハードコードが残っていることを見落とし、「全6軸完了」と虚偽報告した。15m/30m の spec 列がすべて「—」で ★ 件数 0。点検が表面的だった（TIMEFRAMES 定義だけ見て関数本体を見ていなかった）。

**ルール:**
完了報告前に必ず以下4種の grep を全関連ファイルで実行する:
1. `endswith` / `startswith` の TF タプルハードコード
2. TF リスト固定値（`["5m", "1h", "4h", "1d"]` 等）
3. カテゴリ固定値（`"inside_value_area"` 等の Claude 主導抽出）
4. 絞り込み処理（`best 1` / `top 1` / `argmax` / `nlargest(1)`）

grep 結果は「no matches」も含めて全件提示。違反検出時は修正後の diff も提示。

**Why:** TIMEFRAMES 定義を 6軸にしても、関数本体で `__1h, __4h, __1d` が直接書いてあれば 15m/30m が抜ける。点検の解像度を関数本体まで下げる必要がある。

**How to apply:**
1. 完了報告前 = 必ず grep 4種実行
2. 結果を証跡ログ（例: `stage1_evidence_log.md`）に記録
3. 「総点検したから違反なし」を grep 結果なしに主張しない

詳細運用は WORKFLOW.md「完了報告必須証跡4点」参照。

---

### L-160: 段階1 で Claude 主導のカテゴリ抽出禁止（2026-05-08）

**事実:**
段階1-C メタ分析の §5「重要発見3点」セクションで、Claude が動作確認版（1h/4h/1d）の結果から「inside_value_area / VAH-VAL距離 / pivot_zone」の3カテゴリを「重要」と判断して抽出。これは段階1 で「効きそうな指標を選ぶ」最適化を先取りする違反。3原則 #3「段階1 で絞り込まない」違反、2026-05-08 までに通算5度違反した同種パターン。

**ルール:**
- 段階1 で「重要発見」「効く指標」「最強指標」「TOP N」を Claude 発案で出さない
- 動作確認版の結果を見て「これが効きそう」と新セクションを派生させない
- カテゴリ抽出（注目すべき少数を選ぶ）は段階2 でまこさんが行う

**Why:** 段階1 は素材調達フェーズ。Claude が「重要」と判断して絞り込むと、段階2 の最適化母集団が縮む = 真の最適を取り逃すリスク。

**How to apply:** 段階1 のスクリプト・報告書に「重要発見」「効く指標」「TOP N」「最強」のキーワードが入りそうになったら、その時点で停止して「これは段階2 の役割では?」と自問。`regime_research.md` §5 のキーワード警告と着手前チェックを再読。

---

### L-159: 集計表示で best 1 自動採用禁止（2026-05-08）

**事実:**
段階1-C メタ分析の §5 集計で、各パターン × カテゴリで「全候補（軸 × N × 感度設定）から best 1 を自動採用」する集計を実装。結果として v1 rg→dn (1h_N50) と v2 rg→dn (4h_N50) のように異なる軸の数値を比較していて、比較が無効化。3原則 #3「段階1 で絞り込まない」違反、2026-05-08 までに通算5度違反した同種パターン。

**ルール:**
- 集計表示・報告書出力で「best 1 自動採用」を書かない
- 軸跨ぎ・カテゴリ跨ぎのソート表示（TOP N）は並列出力の補助として許容
- ただし「best 1 を選定して採用候補にする」は NG
- 集計表示は次元を保持: カテゴリ × 時間軸 × N窓 × 感度パラメータ × パターン
- キーワード警告: `best_*` / `max_overlap` / `for col in cols: if divergence > best_divergence` 等

**Why:** 段階1 で best 1 を選ぶと、その選定基準が暗黙の絞り込みになる。軸混在比較は数字として無効。段階2 の最適化が「軸跨ぎ best」を選ぶか「軸内 best」を選ぶかは段階2 で決める判断。

**How to apply:** 段階1 系スクリプトで集計関数を書く前に「軸別並列出力か?」を確認。`for col in cols: if metric > best:` パターンを書こうとしたら違反候補。軸別ループ（`for tf in TIMEFRAMES: for col in cols_in_tf:`）に分解して、各軸内の best または各軸並列出力にする。

---

### L-158: 段階1 サブセット分けは per-event テーブルに prev_run カラムを必ず含めて段階2 でフィルタ可能化（2026-05-07）

**事実:**
段階1-B 実装時、まこさんから「段階2 で短命/通常分けが必要になった時の手戻りを防ぐため、per-event テーブルに prev_run カラム必須・メタスコアは『全件・短命のみ・通常のみ』の3系統で計算してほしい」と指示。実装したところ、★ 件数が subset で違うことが定量化でき（全件45 / 短命46 / 通常52）「通常前 run の方が形状特徴量で安定」という発見につながった。

**ルール:**
- 段階1 で per-event テーブルを作る場合、必ず prev_run / cur_run カラムを含める
- メタスコア（分離度・特異性）は subset 別に複数系統計算する
- 段階1 では合算データも残す（subset 分けは段階2 でフィルタするので両方必要）

**Why:** 後段階で subset 分け再分析が必要になったとき、per-event テーブルが prev_run なしだと全部やり直しになる。3系統メタスコア併記で「短命でだけ効く特徴」「通常でだけ効く特徴」の両方を発見できる。

**How to apply:** 段階1 系の analyze_*.py で per-event 集計するときは prev_run / subset カラムを必ず含める。メタスコア計算は subset 別に 3系統で実行。

---

### L-157: 窓なし指標は t=0 値だけでなく過去 N バーからのドリフト方向を併用すべき（2026-05-06）

**事実:**
段階1-A の窓なし指標（pivot_position_100b / streak 系 / close_to_low_pct）について、t=0 値と t-1/t-2/t-5 の差分検証を実施。pivot_position_100b は t-5 から +0.08-0.10 のドリフトのみで、「切替前から既に高値圏で停滞」型の事例が混在することが判明。streak 系は中央値レベルで t-5 から 0 のまま（静的）。close_to_low_pct (rg→dn) は -1.46 と顕著なドリフトで判定材料として強い。

**ルール:**
- 窓なし指標を判定材料に採用する場合、必ず過去 N バー（t-1/t-2/t-5 等）との差分を併記する
- 「t=0 値」+「ドリフト方向（slope や差分符号）」の組み合わせで判定する
- ドリフトが小さい指標は「切替前から同じ値」事例で false positive を出すので単独不可

**Why:** 窓なし指標の中央値だけ見ると「切替点で特定の値になる」ように見えるが、実は数バー前から同じ値で停滞していた可能性がある。判定材料としての価値はドリフトで決まる。

**How to apply:** 段階2 で窓なし指標を採用するなら、必ず slope 計算 or t-N 比較を組み合わせる。pivot_position_100b 単独・streak 単独などは却下。

---

### L-156: メタ分析駆動 — N・時間軸・閾値は直感でなくデータで決める（2026-05-06）

**事実:**
段階1-A / 1-B 着手時、まこさんから「N（過去バー数）・対象軸・対象指標を私の直感で決めるのは feedback_quantitative_comparison 違反」と指摘。Claude が 1〜4 でまこさんに直感を求めた振り方が間違いと自己認識。代替として 自己相関分析（N 候補）+ ラベル分離度（軸・指標選定）+ パターン特異性（横断スクリーニング） の3処理を「メタ分析」として先行実施した。3閾値感度分析（0.3/0.5/0.7）も併記。結果、段階1-A は 1h/4h/1d / N=5-14 / 重複度0.3、段階1-B は 15m/30m/1h/4h/1d / W=10主軸 が**データから**決まった。

**ルール:**
- 大規模分析の対象範囲（指標・軸・閾値・窓）はメタ分析で先に決める
- まこさんに「直感で決めて」と振らない（quantitative_comparison 違反）
- 閾値は複数候補（0.3/0.5/0.7 等）の感度分析で選択肢を見せる
- メタ分析自体の妥当性チェックはまこさんがする・採用閾値もまこさんが選ぶ

**Why:** 大規模分析を先験で決めると後段で「閾値が違ったら結論が変わるか」を検証できない。メタ分析はかかる時間（数十分）を考えても投資に見合う。

**How to apply:** 段階1-C・段階2 でも同じパターン。「対象を絞る前にメタ分析でデータから決める」を必ず先行。

---

### L-155: 中央値の罠 — 分布中央値だけで判定材料を選ぶと個別事例で半分以下しか同じ形にならない（2026-05-06）

**事実:**
段階1-A 旧メイン分析（post 使用版）で「up→dn は macd_hist が t=0 でピーク」「dn→up は底打ち」等の 5発見を中央値ベースで提示。ロバストネス検証で典型形一致率を計算したところ、5発見中 ≥70% 達成は **0個**（57% / 48% / 65% / 52% / 32% / 65% / 42% / 43%）。Q1/Q3 で見ると pre/t0/post のいずれかが 0 を跨ぐケース多数 = 個別事例で正負バラバラ。

**ルール:**
- 分布の中央値だけで判定材料を選ばない
- Q1/Q3 を必ず併記し「0 を跨ぐ場合は典型形が存在しない可能性」と認識する
- 「典型形」を仮説として明示し、それに合致する個別イベントの割合（一致率）を必ず計算する
- 一致率 ≥70% を採用基準、50-70% は「弱い傾向」、<50% は「中央値の罠」と分類

**Why:** 中央値はクリーンに見えても外れ値や bimodal 分布で個別事例は全然違う形をしていることがある。判定ロジック設計時に採用してから「実際にはバラついてルール化できない」と判明すると手戻りが大きい。

**How to apply:** 段階1 で発見を提示するときは Q1/Q3 + 典型形一致率を必須セット。<50% の発見は「再考」マークを付ける。

---

### L-154: regime 判定研究で post（未来）を使うと未来予測的判定リスク（2026-05-06）

**事実:**
段階1-A 初期実装で「切替点 t=0 + 前後 24h ウィンドウ」の集計を出した（[transition_indicator_main.md](../../results/regime_label_analysis/transition_indicator_main.md)）。post（切替後 24h）を分析対象に含めた結果、「教師ラベルがまだ up なのに 24h 後を見て dn 判定」という未来予測的判定に傾く危険が顕在化。まこさんから「これはボット運用で取れない情報」「分析方針そのものを直す」と指摘。§13 v3 で 3原則を明示した。

**ルール:**
- regime 判定研究では **現バーで取得可能な情報のみ**を判定材料にする
- 過去情報（過去 N バー推移・値動きの形・構造）は使ってよい
- post（切替後・未来）は分析にも判定材料にも一切使わない

**Why:** ボット運用では「現在判定」しかできない。post を使った分析は「探求」としては成立するが、判定ロジック直結ではない。post 込み分析と現在判定の境界を曖昧にすると、未来情報を使っているのに気づかず判定ロジックを組んでしまう。

**How to apply:** §13 v3 3原則の1。新規分析スクリプトを書くたびに「post 使ってないか」をセルフチェック。既存成果物（transition_indicator_main.md 等）は「post 使用版・参照保持」と明記して残し、現行正本は post 不使用版とする。

---

### L-153: scripts/ と results/ の直下に .py / データを置かない（2026-05-02）

**事実:**
過去セッションで scripts/ 直下 57本・results/ 直下 60ファイル超まで膨張した。整理時、`Path(__file__).parents[N]` の階層補正・OUT_DIR 修正・doc パス書き換えで大規模な追従工事が必要になった（67 files / +2357行 / -103行）。

**ルール:**
- 新スクリプト作成時は WORKFLOW.md「ファイル配置規則」のサブフォルダのいずれかを必ず指定する
- 新規スクリプトの書き出し先は必ず `results/<サブフォルダ>/` にする
- 直下に置きそうになったら **STOP** → サブフォルダを WORKFLOW.md に追加するか相談する

**Why:** 平置きは数ヶ月で 50本超まで増えて整理工数が膨大化する。最初から分類が一番安い。

**How to apply:** Write で新規スクリプトを作る前に、配置先サブフォルダパスを必ず確認する。書き出し先 OUT_DIR も同様。

---

