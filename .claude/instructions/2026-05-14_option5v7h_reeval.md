# 【タスク】選択肢 5 / 7 / ハイブリッド 再評価 (rolling 却下後・Phase 4-b 設計選択)

(監査#10 設計レビュー済・Web Claude レビュー済・まこさん GO 待ち 2026-05-14)

## 構造化ルール準拠

- 保存先: `.claude/instructions/2026-05-14_option5v7h_reeval.md`
- 完了報告: `.claude/instructions/2026-05-14_option5v7h_reeval_completion.md`
- **本指示書を上記パスに保存し commit すること**(対話ルール19・指示書のファイル保管義務)

## 着手前必読 (省略禁止・L-179/L-180/L-181)

1. WORKFLOW.md §🔴現在のフェーズ (改訂8) / §🔴次のタスク
2. cc_ml_design_spec.md §1.6 / §1.6.1 / §1.6.2 (drift 対処方針)
3. phase_compliance_checklist.md §4a.5 (K96 SHORT q99 フォールバック)
4. handoff_to_web_claude_v5_session_20260514.md §1 (確定事項4件) / §3 (本題) / §4 (宿題)
5. `.claude/instructions/2026-05-14_clustering_alternatives_eval_completion.md` (前回評価の完了報告)
6. `.claude/instructions/2026-05-14_threshold_drift_eval_completion.md` (rolling 却下の経緯)
7. results/priority_rebuild/leak_incident_20260513.md (背景)

## Step 0-1: 必読ファイル引用 (読んだフリ防止)

a. cc_ml_design_spec.md §1.6.2「絶対閾値 drift 対処方針」全文貼り付け
b. phase_compliance_checklist.md §4a.5 全文貼り付け
c. 前回完了報告 (clustering_alternatives_eval_completion.md) から、選択肢5・選択肢7 の
   組合せ数・test 少数セル数・K96 SHORT q99 の扱いに関する記述を全数引用
d. 前回完了報告から「選択肢5: K96_SHORT_q95-q99 band の test 件数」「K96_SHORT_q90-q95
   band の test 件数」の実数値を引用

各引用が期待値と一致しない / 省略 → STOP

---

## 背景

handoff_to_web_claude_v5_session_20260514.md §3 の次タスク。前回 clustering_alternatives_eval
で選択肢 1/4/5/6/7 を評価し、5 と 7 が残った。ただし前回 CC 推奨「選択肢 7 + rolling
キャリブレーション」のうち rolling は audit#9 で却下確定 (固定維持 + K96 SHORT q99 除外)。

**本タスクは rolling 前提が消えた状態で 5 と 7 をフェアに再評価する。** 監査#10 (本指示書
ドラフトの設計レビュー) の指摘により、**ハイブリッド (5 と 7 の構造的融合) を第 3 の評価
対象に追加**する。

## 前提 (動かさない・前セッション確定事項)

- K12 LONG refit 維持 (num_leaves=15 部分採用)
- Phase 2 = 改訂後 spec 4 指標 ALL PASS
- 絶対閾値 drift 対処 = 固定維持 + K96 SHORT q99 除外 (rolling 却下)

この 3 つは本タスクのスコープ外。再評価しない。

## 評価対象 (3 案)

| 案 | 構造 |
|---|---|
| 選択肢 5 | K × side × q-level (24 組合せ)・q90/q95/q99 を natural classifier に |
| 選択肢 7 | SHORT clustering(k=2) + LONG per-entry (12 組合せ)・非対称設計 |
| ハイブリッド | 5 と 7 の構造的融合 (例: q-level band 化 + LONG のみ per-entry)。具体構成は CC がデータを見て 1〜2 案提示 |

## 入力ファイル (前回と同一・評価条件を揃えるため)

| 役割 | パス | sha256 (先頭) |
|---|---|---|
| train 正規化済み予測値 | `results/priority_rebuild/ml_phase4_a_norm/predictions_train_norm_2021_2024.parquet` | bee59c1197d3 |
| test 正規化済み予測値 | `results/priority_rebuild/ml_phase4_a_norm/predictions_test2025_norm.parquet` | c6149c8b7b82 |

- artifact (scaler/kmeans) は train fit 版のみ使用・test 不使用 (L-183)
- **入力 2 ファイルは起動時に sha256 を assert で照合**。log のみは不可。指示書記載値と
  不一致なら `sys.exit`

### Step 0-2: 入力ファイル整合性 verify

```bash
echo "=====Step 0-2 START $(date) ====="
sha256sum results/priority_rebuild/ml_phase4_a_norm/predictions_train_norm_2021_2024.parquet
sha256sum results/priority_rebuild/ml_phase4_a_norm/predictions_test2025_norm.parquet
```

期待: 上記表の sha256 (先頭 12 桁) と一致。不一致 → STOP

---

## Step 1: 完了報告テンプレ改訂 (4 軸評価より先に確定)

WORKFLOW.md「完了報告必須証跡 5 点」に **6 点目を追加**:

```
6. **個別組合せ/クラスタの train→test 変化表**
   (形式: 組合せ名 / train値 / test値 / 差(pp) / test件数)
```

手順: 追加 → `git status` 提示 → ファイル単位で add → commit →
そのあと Step 2 の 4 軸評価に進む。

**本タスク自身の完了報告もこの新テンプレ (6 点) に準拠する。**

理由: audit#9 懸念 2 (完了報告テンプレに train→test 変化表必須化)。本タスクの軸 3 が
まさにこの表を必要とするため、テンプレ改訂を先行確定してから評価する
(監査#10 懸念 7)。

---

## Step 2: 4 軸評価 (3 案すべてで全軸を算出)

### 軸 1: K96 SHORT q99 除外後の成立性 (中立評価)

3 案それぞれ「K96 SHORT q99 をどう処理するか」を評価する。

**前回データの既知事実を完了報告本文に明示すること** (監査#10 懸念 2):
- K96_SHORT_q95-q99 band も test 0 件 (band 化で救済できない)
- K96_SHORT_q90-q95 band は test 約 274 件 (前回完了報告で要実数確認)

**K96 SHORT q99 除外の band 化適用ルール = 解釈 C を採用** (監査#10 懸念 4):
- q99 単独除外
- q95-q99 band は test 0 件のため自動除外
- q90-q95 band は別判定 (使用可否を軸 2 で評価)

各案の処理:
- 選択肢 5: 解釈 C を適用。q90-q95 band の K96 SHORT が使用可能か軸 2 で判定
- 選択肢 7: SHORT_cluster*_K96_q99 は §4a.5 フォールバックで no-trade 除外。
  除外後の有効組合せを評価
- ハイブリッド: 構成次第で適用方法を CC が明示

「3 案とも K96 SHORT q99 を除外/band 化した後、設計思想が崩れていないか」を明示。
**「救済」「除外」のような片寄った表現を使わず、3 案を同じ枠組み (どう処理するか) で
記述すること** (監査#10 懸念 2: framing bias 防止)。

### 軸 2: サンプル数 + signal quality (2 部構成)

監査#10 懸念 1: 件数のみでは signal quality を見落とす。2 部構成にする。

**(a) 件数**:
- 各組合せ/クラスタの train 件数・test 件数を全数列挙
- test < 100 件セルは **足切り条件 = デフォルト no-trade** として扱う
  (audit#2 基準「< 100 件は統計的有意性なし」を運用に反映・監査#10 懸念 3)
- 3 案それぞれ「足切り後の有効組合せ数」を出す

**(b) signal quality**:
- 各組合せの net_quality / MFE_lift / MAE_lift を算出 (前回 clustering_alternatives_eval
  では未測定・監査#10 懸念 1)

**< 100 件セルの代替策を別軸として 3 案比較** (監査#10 懸念 3):
- (i) no-trade (デフォルト)
- (ii) 隣接セル補完 (選択肢 5 なら隣接 q band・選択肢 7 なら隣接 cluster)
- (iii) < 100 件でも train 高 signal なら使用 (緩和)

**per-組合せ contribution 統合表** (監査#10 懸念 9):
- contribution = test_fire × net_quality (proxy)
- 3 案別個に上位 10 組合せを列挙
- 「組合せ数 × per-組合せ signal quality」のトレードオフを 1 表で見えるようにする

### 軸 3: train→test 安定性 (参照ライン分離)

- Step 1 の train→test 変化表を全組合せ/クラスタで出力
- **参照ラインを案の構造別に分離** (監査#10 懸念 6: max_diff は cluster 指標であり
  選択肢 5 の band 構造には適用できない):
  - 選択肢 7 / ハイブリッドの cluster 部分 → max_diff ≤ 20pp 安定 / 20-40pp 要警戒 /
    > 40pp 失敗 (Phase 4-a 基準)
  - 選択肢 5 / ハイブリッドの band 部分 → test/train fire ratio 0.5-2.0 で安定 /
    範囲外は警戒
- 3 案それぞれ max_diff / 平均 drift / fire ratio を出す

### 軸 4: Phase 4-b への引き渡し適性 (定量化)

監査#10 懸念 5: 「変換コスト」を定性評価で済ませない。定量化する。

- 各案の出力が cluster × K × side の Exit 設計にそのまま渡せるか
- **定量指標: 現 `run_phase4_b.py` 骨子からのスクリプト改修行数の見積もり**
  (cluster_best_exit 選定の入力フォーマットへの変換ロジック行数)
- 3 案それぞれ見積もり行数を出す

---

## 出力 (成果物)

| ファイル | 内容 |
|---|---|
| `results/priority_rebuild/option5v7h_reeval/option5_eval_REEVAL.csv` | 選択肢 5 の 4 軸評価結果 |
| `results/priority_rebuild/option5v7h_reeval/option7_eval_REEVAL.csv` | 選択肢 7 の 4 軸評価結果 |
| `results/priority_rebuild/option5v7h_reeval/optionH_eval_REEVAL.csv` | ハイブリッドの 4 軸評価結果 |
| `results/priority_rebuild/option5v7h_reeval/contribution_table_REEVAL.csv` | 3 案の per-組合せ contribution 統合表 |
| `results/priority_rebuild/option5v7h_reeval/raw_aggregation_REEVAL.csv` | 4 軸評価の集計前 raw データ (各組合せ/クラスタの生件数・生 net_quality 等・Web Claude 独立再集計用) |
| `results/priority_rebuild/option5v7h_reeval/comparison_5v7vH_REEVAL.md` | 4 軸の 3 案対比サマリー (事実観察のみ・CC 推奨は書かない) |

**CSV 本体は完了報告に貼らない**。CC はパス・sha256・行数のみ報告する。CSV の中身は
まこさん経由で Web Claude に渡り、Web Claude が独立再集計する (ガード G)。

**本タスクはダッシュボードタブ不要**。採用判定者は Web Claude 独立評価 + 監査#11 の数値
レビューであり、判定材料は上記 CSV/md そのもの。cc_ml_design_spec §7.3 が想定する
「視覚化しないと誤読する分析 (発火分布・時系列チャート)」とは性質が異なる。
ファイル名一意化のため全成果物に `_REEVAL` 識別子を付与済 (WORKFLOW.md ファイル名一意化
ルール準拠)。

---

## 過去不正パターンのガード (lessons_active.md L-99〜L-190 全件レビュー由来・省略禁止)

過去セッションで CC が繰り返した不正・ミスを、本タスクで物理的に踏ませないための verify
項目。各項目は「気をつける」ではなく「やったら検出される」形で定義する。完了報告で各項目の
verify 結果 (grep 出力・実数値) を提示しないものは差し戻し。

### ガード A: §8 違反 (test を見て学習を変える・L-183)

- 本タスクは既存 predictions parquet の集計のみ。学習・refit・fit 系処理を一切含まない
- 評価スクリプトに対し `grep -nE '\.fit\(|\.fit_transform\(|refit|KMeans|LGBM|train.*model'` を
  実行し、ヒットゼロを完了報告に貼る (artifact の joblib.load は可・再 fit は不可)
- test 側の数値を見て評価条件・閾値・集計方法を後から変更しない。評価条件は本指示書で固定済

### ガード B: 手計算で PASS と言い張る (spec/script 乖離・L-184)

- 4 軸の全数値は **スクリプトが出力した CSV のセル** であること。完了報告本文に出てくる数値で
  出典 CSV に存在しないものが 1 つでもあれば差し戻し
- 完了報告の各数値に「出典: option5_eval_REEVAL.csv L23」形式で行番号を付ける
- 完了報告本文に「手計算」「手で計算」「目視で」「概算」「およそ」の語があれば差し戻し
- 公式の評価結果 source は成果物 CSV のみ。完了報告内の記述は CSV の引用であること

### ガード C: 未来値 leak (L-179 / L-182 / L-128 / L-154)

- test 集計で train の統計量 (閾値・平均・分位点) を参照していないか、その逆もないかを
  集計コードの grep で確認。train 用閾値と test 用閾値の算出箇所を完了報告に明示
- 集計は時系列ソートを要しない単純 groupby のみ。**期間全体ソート禁止** (L-182: 期間全体
  ソートは未来 entry を taken に混入させる leak と同等)
- 「コメントに leak 防止と書いてあるから安全」を理由にしない。集計コードの実装で verify

### ガード D: 絞り込み・best 1 自動採用 (L-159 / L-160 / L-162)

- comparison md に「優位」「採用」「best」「効く」「効かない」「重要」「不要」「採用候補」
  「使える」の語が無いことを自己 grep し、結果を「no matches」含めて完了報告に貼る
- comparison md は 4 軸の数値を 3 案並記するのみ。「どの案が良い」の判断を書かない
- 「事実観察」= 数値の事実 + 軸間/案間の数値比較まで。総合判定は Web Claude の役割

### ガード E: やったフリ・連続実行で確認を奪う (L-143 / L-144 / L-161 / L-131)

- 4 軸それぞれの集計過程 (中間出力・groupby 前後の行数) をログに残す
- bit-exact 再現性: 同コマンド 2 回実行で集計結果が一致することを確認・完了報告に明記
- grep 結果は「no matches」も含めて全件提示。「総点検した」を grep 結果なしに書かない
- Step 1 (テンプレ改訂 commit) と Step 2 (4 軸評価) の間で STOP しない設計だが、Step 1 の
  commit hash を Step 2 着手前に完了報告に記録すること (連続実行でも各 Step の証跡を残す)

### ガード F: 机上指標と実態の乖離を見ない (L-105 / L-111 / L-112 / L-123 / L-126)

- contribution = test_fire × net_quality は **proxy であり実 Replay PnL ではない**ことを
  comparison md に明記。「これは月次 PnL の予測ではない」と限界を 1 行書く
- net_quality / MFE_lift / MAE_lift の算出定義 (分母・分子・対象期間) を完了報告に明記
- 「proxy が高い = Phase 5 月次 PnL が高い」と断定しない。proxy はあくまで設計選択の補助指標

### ガード G: サマリーの都合よい書き換え (CC の結果サマリー過信防止)

- CC は成果物 CSV を生成しパス・sha256・行数を報告するのみ。**CSV 本体を完了報告に
  整形・抜粋して貼らない** (貼る時点で CC の作為が入る余地ができるため)
- CSV の中身はまこさん経由で Web Claude に直接渡る。Web Claude は CC のサマリーを
  読む前に `raw_aggregation_REEVAL.csv` から独立に再集計する
- 独立再集計結果と CC サマリーが一致しなければ差し戻し
- 「集計過程で除外した行」がある場合、除外理由と除外行数を完了報告に明示
  (無断除外は差し戻し)
- CC が報告した sha256 と、まこさんが貼った CSV の sha256 を Web Claude が照合する
  (CC が「A という CSV を作った」と報告して実際は別物、を検出)

---

## 物理証跡 10 点

1. 入力ファイル整合性 (Step 0-2・正規化版 predictions 2 ファイルの sha256 assert 照合)
2. 試算プロセス (各案の組合せ数・サンプル数・signal quality の集計過程)
3. 出力ファイル証跡 (成果物 CSV/md の sha256 + 行数)
4. 第三者再計算検証 (1 案のサンプル数 + net_quality を独立再集計で一致確認)
5. データ sanity (集計対象の行数・null 率・全組合せにサンプルが入っているか)
6. stderr / Python warning 全件 (no warnings の場合も明示)
7. 同コマンド bit-exact 再現性確認 (2 回実行で集計結果一致)
8. 監査#10 全項目マッピング (下表) の各項目が完了報告で言及されているか
9. 過去不正パターンのガード A〜G の各 verify 結果 (grep 出力・実数値・no matches 含む)
10. 生 CSV 成果物のパス + sha256 + 行数 (CSV 本体は貼らない・ガード G)

---

## 監査#10 全項目 対応マッピング (取りこぼし防止)

| 監査#10 指摘 | 本タスクでの対応 |
|---|---|
| 懸念 1 (signal quality 軸 欠落) | 軸 2 を「件数 + signal quality」2 部構成に拡張 |
| 懸念 2 (軸 1 の framing bias) | 軸 1 を「3 案とも K96 SHORT q99 をどう処理するか」中立記述化 + 既知事実 (q95-q99 band も test 0 件) を本文明示 |
| 懸念 3 (サンプル数閾値運用) | 軸 2 で test < 100 件を足切り条件 (デフォルト no-trade) 化 + 代替策を別軸で 3 案比較 |
| 懸念 4 (K96 除外の band 解釈曖昧) | 軸 1 で解釈 C を確定明記 |
| 懸念 5 (軸 4 が定性的) | 軸 4 を「run_phase4_b.py 改修行数の見積もり」で定量化 |
| 懸念 6 (軸 3 参照ライン) | 軸 3 で cluster 用 (max_diff) と band 用 (fire ratio) の参照ラインを分離 |
| 懸念 7 (テンプレ改訂を Step 1 先行) | Step 1 でテンプレ改訂 → commit → そのあと Step 2 評価 |
| 懸念 8 (「CC 推奨」要求が監査経路と矛盾) | comparison md は事実観察のみ・CC 推奨を要求しない。総合判定は Web Claude 独立評価 → 監査#11 |
| 懸念 9 (contribution 統合表なし) | 軸 2 に per-組合せ contribution 統合表を追加 |
| 懸念 10 (並行タスクの依存) | spec-script consistency 2 項目を「本タスク結論待ち」に変更 (下記「後続タスク」) |
| 見落とし A (軸の重み付け未定義) | **意図的に指示書に含めない**。軸の重み付け = 総合判定は Web Claude の独立評価の役割。CC は数値出力のみ (懸念 8 と整合) |
| 見落とし B (ハイブリッド未検討) | ハイブリッドを第 3 評価対象に追加 |
| 見落とし C (選択肢 5 の実質組合せ数) | 軸 2(a) で「足切り後の有効組合せ数」として明示 (24 → 実質値) |
| 見落とし D (選択肢 7 の実質組合せ数) | 軸 2(a) で「足切り後の有効組合せ数」として明示 (12 → 実質値) |
| 見落とし E (sha256 照合方法) | Step 0-2 で「assert で照合・不一致なら sys.exit」と明記 |
| 見落とし F (「採用判定に使わない原則」出典) | 出力セクションで cc_ml_design_spec §7.3 を出典明記 |
| 見落とし G (軸の評価期間) | train 全期間 (2021-2024) で集計・test は 2025 全年。軸 3 のみ train→test transition。完了報告で各軸の評価期間を明示すること |
| 見落とし H (2026 Q1 への波及) | 本タスクのスコープ外。5/7/H 確定後の Phase 4-b/6-b で扱う (§8: 本テストデータを Phase 6 以前に使わない) |
| 見落とし I (per-entry の Exit パラメータ) | 本タスクは「設計選択」まで。per-entry Exit パラメータの具体化は Phase 4-b。軸 4 で「引き渡し適性」として粒度のみ評価 |
| 見落とし J (K12 LONG refit の 5/7 非対称影響) | 軸 2(b) の signal quality 算出時に、K12 LONG が refit 版であることを明記。5 は q-level 同スケール / 7 は LONG per-entry で refit 直接活用される差を完了報告に記載 |
| 見落とし K (ダッシュボード実装コスト) | 本タスクはダッシュボード不要と確定 (出力セクション参照)。実装コスト議論は発生しない |
| 見落とし L (テンプレ 6 点目の位置づけ) | Step 1 で「6 点目として追加」と明記。既存 5 点との関係を完了報告で示す |

---

## 完了報告必須証跡 (新テンプレ 6 点準拠)

1. **コード総点検 grep 結果** (新規評価スクリプトの絞り込み示唆語彙 grep・4 種 grep)
2. **数値の二重提示** (4 軸サマリー表 + 出典 CSV・行番号付き)
3. **成果物ファイル実体** (sha256 + 行数 + 更新時刻・CSV 4 本 + md 1 本)
4. **実行ログ** (コマンド・開始/終了時刻・所要時間・終了コード・Python warnings 全件)
5. **絞り込み示唆語彙 自己 grep 結果** (no matches 含む・チャット出力 + 報告 md 対象)
6. **個別組合せ/クラスタの train→test 変化表** (新テンプレ 6 点目・形式: 組合せ名 /
   train値 / test値 / 差(pp) / test件数)

加えて報告に含めること:
- 入力 2 ファイルの sha256 assert 照合結果
- 4 軸の結果サマリー (軸ごとに 3 案並記・次元保持)
- **事実観察のみ**: 4 軸の数値がどの案に有利か (「どちらが優位」の推奨判断はしない)
- 監査#10 全項目マッピング表の各項目が完了報告のどこで言及されているか
- **過去不正パターンのガード A〜G の各 verify 結果** (ガード A の grep 出力 / ガード B の
  「手計算」語 grep / ガード C の閾値算出箇所明示 / ガード D の絞り込み語 grep /
  ガード E の bit-exact 結果 / ガード F の proxy 限界明記 / ガード G の生 CSV パス+sha256)
- **生 CSV 成果物のパス + sha256 + 行数** (CSV 本体は貼らない。Web Claude がまこさん経由で
  受け取り独立再集計する・ガード G)

---

## CC への注意

- 「選択肢 5 か 7 かハイブリッドか」の **推奨判断を CC に求めない**。CC は 4 軸の数値出力 +
  各軸がどの案に有利かの事実観察まで
- 総合判定は Web Claude が独立評価で行い、監査経路 (監査#11) で第三者検証する
  (handoff §3「audit#9 が次の audit を経由と明記」準拠・監査#10 懸念 8)
- CC が「A/B/C どの構成で?」等の選択肢を提示してきても、それは Web Claude が吸収する
  (まこさんに転送しない)

---

## 後続タスク (本タスク結論待ち・並行ではない)

spec-script consistency 未実装 2 項目 (§4b.4-b simulate_predicted_mfe_tp /
§1.6.1 メタルール script guard) は、5/7/ハイブリッドのどれを採るかで §4b.4-b の関数構造が
変わる (cluster 単位 vs 組合せ単位 vs band 単位) ため、**本タスク結論確定後に着手**する
(監査#10 懸念 10)。

---

## 完了後の状態

- 完了報告テンプレに 6 点目 (train→test 変化表) が追加・commit 済
- 選択肢 5 / 7 / ハイブリッドの 4 軸評価が完了
- 各案の「足切り後の有効組合せ数」「signal quality」「train→test 安定性」「Phase 4-b
  引き渡し適性」が数値で揃う
- per-組合せ contribution 統合表で「組合せ数 × signal quality」のトレードオフが可視化
- 監査#10 全項目が本タスクで対応済
- どの案を採用するかの判断材料が揃う (総合判定は Web Claude 独立評価 → 監査#11)

## 次のステップ

完了報告受領 → Web Claude が self_check (B) → 生 CSV から独立再集計 → 独自評価 →
監査#11 (数値レビュー) → まこさん最終 GO → 選択肢確定 → 確定案に応じた Phase 4-b 指示書 +
§4b spec 改訂 + spec-script consistency 2 項目

## Web Claude 独立評価の手順 (監査経路前提)

- **生 CSV の受け取り経路**: CC は完了報告で CSV のパス + sha256 + 行数のみ報告する。
  CSV 本体はまこさんがファイルを開いてチャットに貼り、Web Claude はそれを受け取る
  (CC 経由で整形されたサマリーではなく、生データを直接見る)
- Web Claude は CC 完了報告の数値表を読む前に、まこさん経由で受け取った
  `raw_aggregation_REEVAL.csv` から自分で集計を再実行する
  (各案のサンプル数・net_quality を独自に再計算)
- 独自集計と CC サマリーを差分照合。一致しなければ差し戻し
- CC が報告した sha256 と、まこさんが貼った CSV の sha256 を照合 (同一ファイル確認)
- 4 軸の重み付け = 総合判定は Web Claude が独自に行う (CC には委ねない)
- ただし重大判断は監査経路 (監査#11) を通す。Web Claude + CC の収束バイアスは
  self_check では防げない (handoff §6)
