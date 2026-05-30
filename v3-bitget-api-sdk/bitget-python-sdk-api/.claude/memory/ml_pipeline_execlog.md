# ml_pipeline_execlog.md — ML pipeline 実行ログ + 現在地（新セッション最初に読む正本）

> **目的（まこさん指示・2026-05-30）**: 新セッションが経緯を誤解なく理解し、ズレた発言をせず建設的に議論を始めるための記録。
>
> **このファイルの位置づけ（3 層構造の分離）**:
> - **設計の正本 = `ml_pipeline_baseline_v1.md` §1-§7**（各工程を「どう作るか」・議論決着 + CP 監査反映）
> - **本ファイル = 実装の実行・実測・現在地ログ**（旧 baseline §8 を分離・「実際に作って動かしたら何が起きたか」の時系列 + 設計論点）
> - **hook 対象外**: 記録・整理の追記に WebSearch は不要。設計確定（§6 本文）の編集は baseline 側で行い、そこで WebSearch hook が gate する（提案前ベースアップの強制）。
>
> **新セッションはこの 0 章（フロー意図）と末尾（現在地 + 次セッション着手）を最初に読む。**

---

## 0. フロー意図・役割分担（新セッション必読・誤解防止・最重要）

本フローは「**連鎖学習（パイプライン）**」（baseline §3.3）: 各工程を独立モデルにして、前段の出力を後段の**入力**に渡す [1.5]→[2]→[2.5]→[3]→[4]。マルチタスク学習（1 モデル同時学習）の現実的代替。狙いは 5 レバーの掛け算 **5.57×**（baseline §2.2）。

| 工程 | 軸 | 何を判定 | 出力の渡し先 |
|---|---|---|---|
| [1.5] regime | **方向 / 環境軸** | 上昇 / 下降 / 横ばい + 確信度 | [3] Sizing / [4] Exit が**直接**受け取る（強制フィルタしない・§1 L24） |
| [2] Entry ML | 候補生成 | 56 ラベル予測 + direction + confidence | [2.5] cluster / [3] / [4] |
| [2.5] cluster | **trade 質軸** | 「方向では分けられない質の違い」をグループ分け | [3] / [4] が cluster 別に Exit/Sizing を変える（戦略並立 1.5×） |

**誤解防止（最重要）**:
- regime（方向）と cluster（質）は**別の軸**。役割を混同しない。天気予報の例え: regime =「晴れ / 雨（方向）」、cluster =「同じ天気でも傘が要る人 / 要らない人（質）」。
- **cluster 入力に regime を直接入れない**: cluster が方向を再現するだけの冗長になる（L-238 実測「regime4 入力は上昇/下降塊に分かれるが regime と冗長」で確認済）。regime × cluster の組み合わせは**後段 [3]/[4] で効かせる**。

**2026-05-30 baseup で判明した設計上の根本論点（未確定・要議論）**:
- 本フローは regime も TB も meta も**全部「横並びの独立モデル + 特徴量連鎖」**で、業界の meta-labeling の**縦のカスケード（primary→meta）になっていない**。
- **meta は meta-labeling として実装されていない**: 現 meta_label =「全 bar で独立に TP 先着を予測する binary」= TB の TP クラスを二値化しただけの冗長ラベル。primary 発火サンプルに条件付けされず・ゲートでなく集約スコアの加重一項（§6.2.7 `meta_yes×0.3`）として誤用。だから AUC 0.509（ほぼランダム）。
- 業界の正しい meta-labeling = **primary（方向シグナル {-1,0,1}）→ meta（その候補を採用/棄却するゲート + sizing）の二段カスケード**。meta は primary が発火したサンプルのみで「その bet が勝ったか」を学習（[Hudson&Thames](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/) / AFML Ch.3）。
- **regime が方向 primary の有力候補**だが、現状は入力特徴量の 8 列に薄められている（baseline での engagement 17.3%）。regime を primary に昇格 → entry ML/meta を採用ゲートにする案が業界整合（ただし regime 先行型に近づく懸念 + data verify 要）。

---

## 1. 工程別 実行ログ（時系列）

### 工程 [1.5] regime ensemble（相場の状態判定）

| 実行日 | 内容 | 実測結果 | 決定/修正 | リンク |
|---|---|---|---|---|
| 〜2026-05-27 | Stage B-G 実装（8 script 新規）+ target v1→v2（未来予測→過去描写）+ k-means v1→v2→v3 | ensemble v3: accuracy 0.46→0.65 / Brier 0.29→0.16 / ECE 0.26→0.15 / 3 判定器予測誤差相関 0.69→0.42（CP1 基準クリア） | まこさん視認「結構改善」確認・Stage 3 まで regime 調整保留 | L-234 / §6.1 |

**現状**: regime 判定は実装済・accuracy 0.65 で一旦確定（Stage 3 PnL で再調整余地）。

### 工程 [2] Entry ML（Entry 判定の機械学習）

| 実行日 | 内容 | 実測結果 | 決定/修正 | リンク |
|---|---|---|---|---|
| 2026-05-28〜29 | baseline 168 学習（56 ラベル × 3 fold・LightGBM default・8.3h） | 回帰（揺れ幅）R² 中央値 **-0.044**（CV） / 多クラス（Triple Barrier）acc 47.6%（+14.3pt ✅） / 2 値（meta）AUC 0.522（+2.1pt △） | MFE 直接予測は業界実証で困難（path-dependent + heavy-tail）・揺れ幅は当たらないと一旦判断（後に production で修正・下行） | L-237 / §6.2 |
| 2026-05-29 | Optuna tune（3 系統 × 30 trials・6.93h） | 改善幅 0.07-1.9% で小 | LightGBM default が既に robust・tune 保留（Stage 3 不合格時に戻る） | L-237 |
| 2026-05-29 | Step 6 集約 + 5 variant 比較 | §6.2.7 集約式に **scale mismatch 設計欠陥**発覚（CP2 監査見逃し）: MFE z-score が集約スコア 97% 支配 | E variant（[0,1] clip + data-driven threshold 0.477）で月 275 件達成 ✅・SHORT 偏り 1:20 は scale 整合だけでは解消せず | L-237 / §6.2.7 注記 |
| **2026-05-30** | **本番モデル学習完遂**（新規 `run_phase2_entry_ml_production.py`・全 train fit + booster 保存 + test 2 期間予測・56 ラベル・5.7h・leak 4 点 verify pass・異常値スメルテスト該当なし） | **揺れ幅 回帰28 test R² 中央値 +0.050（CV の -0.044 と違い正）・20/28 が正・短期 K6-48 は +0.05〜+0.20・長期 K288 のみ負** / TB 多クラス14 acc 中央値 0.490 / **meta 2値14 AUC 中央値 0.509（ほぼ無価値）** / blacklist hit 0 | **優先1（評価データ確保）完遂**。揺れ幅は「一律当たらない」でなく**短期はボラ駆動で部分的に正**（atr14_pct が top 特徴）。meta はほぼランダム=用途以前にラベル設計が meta-labeling になっていない（0 章 論点） | L-239 / `ml_phase2_production/summary.json` |
| 2026-05-30 | baseup: entry 予測対象アーキの業界 verify（本文 2 件）+ meta-labeling 詰め直し + フロー意図 verify | 業界一致「entry 予測対象は Triple Barrier 分類・大きさの回帰予測は使わない」（MQL5: magnitude 回帰は「ROC 対角線張り付き＝無価値」/ QuantStrategy: 「まず分類優先」）。meta は primary→meta カスケード未実装と判明 | **設計判断（/audit 検証待ち）**: entry 集約 §6.2.7 を決着主軸（TB）に・揺れ幅は entry 集約から外す（TP は ATR/realized vol）・meta は正しいカスケードに作り替え候補 | L-239 / [MQL5](https://www.mql5.com/en/articles/18864) / [QuantStrategy](https://quantstrategy.io/blog/machine-learning-for-exit-optimization-predicting-the-best/) |

**現状**: Entry ML 本番モデル + test 予測 揃った（cluster/Stage3 評価の前提クリア）。**設計の本丸論点（meta カスケード未実装・regime primary 化・entry 集約 §6.2.7 反転）が議論で浮上・未確定**（0 章参照）。

### 工程 [2.5] cluster 分類（Entry trade の質をグループ分け・案 P）

| 実行日 | 内容 | 実測結果 | 決定/修正 | リンク |
|---|---|---|---|---|
| 2026-05-29〜30 | `run_phase2_cluster_classifier.py` 新規・§6.3 設計通り（全投入 2,666 + PCA + KMeans+GMM hybrid + Isotonic） | smoke で **silhouette 0.90 偽分離**（PCA 1 主成分が分散 95% 支配） | 前処理欠陥 3 件修正（inf→NaN / ±5 IQR clip / 高 NaN 列 drop + median 補完） | L-238 |
| 2026-05-30 | 入力 3 パターン比較 | 全投入 2,666: **0.022** / 予測値 56: 0.14 / 揺れ幅予測 28: **0.326** | §6.3.3「全投入」が覆る → 揺れ幅予測 28 のみ採用 | L-238 |
| 2026-05-30 | アルゴリズム / 確率 / 門番 | GMM hybrid 0.15 << KMeans 0.33 / 教師なしで Brier・ECE=0 / どの入力も silhouette 0.4 未達 | KMeans 単体 + 距離 softmax + 門番緩和（weak 0.25・実益 Stage 3 判定） | L-238 |
| 2026-05-30 | **cluster 確定**（KMeans + 揺れ幅 28 + k=4） | silhouette **0.326** / 偏り cluster2=61%（1 巨大塊） / 命名重複 | 品質課題（偏り + 命名）は次セッション | L-238 / cluster_summary.json |
| 05-30後半 | cluster 偏り原因究明 + Stage-3 PnL probe | 偏り61%は**入力（揺れ幅）が弱い症状**でアルゴ問題でない / PnL probe は IS で b/a 5-6× だが **OOS 1.03-1.32× に崩壊（過学習）**・fold2=171 件で評価不能 | **cluster 効果 未実証**・cluster は磨かない（データ揃うまで） | L-239 / /tmp/stage3_pnl_probe.py |

**§6.3 設計が実装で覆った 4 件**: 入力（全投入→揺れ幅28）/ アルゴ（GMM hybrid→KMeans）/ 確率（Isotonic→距離softmax）/ 門番（0.4→緩和）。**教訓（L-236-B）**: 監査済「確定設計」も実データで覆る・「設計値は仮定・実装後 data-driven 確定」。

**フロー意図に照らした cluster の次の方向（2026-05-30 baseup・未確定・提案中）**: cluster は「質軸」なので、入力は**揺れ幅でなく Triple Barrier 予測（TP/SL/TIME 決着確率＝質そのもの）**にするのが筋（揺れ幅はボラ系で regime と冗長 + 当たらない）。regime は cluster 入力に入れない（0 章）。ただし有効性は Stage 3 PnL でしか確定しない。← **まこさん指示の「cluster 結果の見方 + どうすべきか」提案は本セッション未完了（次の宿題）**。

---

## 2. 現在地 + 次セッション着手（新セッションは最初にここを読む）

**現在地（2026-05-30 第3セッション末）**:
- 工程 [1.5] regime / [2] Entry ML / [2.5] cluster の 3 工程が「一旦動く」（暫定・Stage 3 PnL 未判定）。
- **本番モデル学習完了**（56 booster + test 2 期間予測・`ml_phase2_production/`）→ cluster/Stage3 の評価データは揃った。
- **構造整備完了**: §8 → 本 execlog 分離 + baseline §6 経緯ログ除去（設計記述と実測ログの分離完成・hook 意図整合・新セッション誤解防止導線）。
- **設計の本丸論点が baseup で浮上（0 章）**: ① meta が meta-labeling として未実装（primary→meta カスケードでなく集約一項の誤用・AUC 0.509） ② regime を方向 primary に昇格するか ③ entry 集約 §6.2.7 を決着主軸に反転（/audit 検証待ち） ④ cluster 入力を Triple Barrier 質軸に。これらは相互に絡む。

**最重要認識（L-239 + baseup）**: 本丸は Entry 精緻化でなく **後段レバー（Exit/並立/Sizing）の掛け算**（Entry 単独は業界実証 1.6×=月$592 で大幅未達・industry_benchmark §2.6）。

**積み残し課題**:
- 工程 [2]: SHORT 偏り 1:20（構造的・下落相場 fold 由来） / meta カスケード未実装
- 工程 [2.5]: cluster 偏り 61% + silhouette 0.326 weak・効果未実証（過学習）
- **まこさん指示で未完了**: 「cluster 結果の見方 + どうすべきか」のわかりやすい提案

**次セッション CC 優先順位（L-239 5 列表）**:

| 優先 | 使う/直すファイル | 入力データ | 存在✅ | 最初の一手 | 完了条件 |
|---|---|---|---|---|---|
| 1 設計整理 | （議論 + baseline §6 反映） | 0 章の論点 ①〜④ | — | meta カスケード化 / regime primary 化 / cluster 質軸 / §6.2.7 反転 を統合した設計方針を提案（相互の絡みを整理） | まこさん合意 + 必要なら /audit |
| 2 /audit | `.claude/audits/inputs/2026-05-31_entry_target_cp4_audit_request.md`（新規・`_template.md` 雛形） | §6.2.7 + 本ログ + L-237 | ✅ template | 依頼書作成（Q: entry 集約の決着主軸化 + meta カスケード化 + regime primary 化は妥当か） | 依頼書 commit + 別セッション監査結果受領 |
| 3 cluster 作り直し | `run_phase2_cluster_classifier.py` 改修 | Triple Barrier 予測（production 出力） | ✅ test 予測生成済 | cluster 入力を揺れ幅 28→Triple Barrier 予測（決着確率）に変更・regime 除外 | silhouette + Stage 3 PnL で評価 |
| 4 後段レバー | [3] Sizing / [4] Exit 設計（未着手） | 前段出力 + cluster | — | industry_benchmark §2.6 の Exit 1.7× / 並立 1.5× / Sizing 1.2× レバー設計着手 | Stage 3 PnL 判定経路確立 |
| 5 最終判定 | Phase 5 Replay | 全前段出力 | — | 月次 NET 集計 | 全 12 ヶ月 ≥ $1,900 |

**本番学習スクリプト**: `run_phase2_entry_ml_production.py`（全 train fit + booster + test 予測・background は絶対パス python + caffeinate 必須・L-237/238 再演防止）。
