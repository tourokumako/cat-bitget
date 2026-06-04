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

> ⚠️ **【2026-05-31 後半で覆った・この方針では進めない】** 下記「縦カスケード化」方針は実装着手後に前提が崩れた。①PnL を測ったら全月マイナス ②学習が方向でなくボラ予測に逃げている（過去フロー全滅の再発）③**約定/コスト計算に基本的な不正が確定（成行決済を maker で計算・gross を net と偽る・指値必ず約定の非現実仮定・funding 未控除）→ 過去の PnL/Replay/$1,900 判定はすべて無効**。**→ 全設計し直し。まず正しい評価基盤を作るのが先**（下の §1.9 と現在地参照）。この縦カスケード方針自体は評価基盤が正しくなってから再判断する（破棄ではなく保留）。

**2026-05-31 合意した修正方針（まこさん合意済・実装着手 → ⚠️後半で覆り・保留）**:

論点①〜④を「縦のカスケード（primary→secondary meta-labeling）への組み直し」で一本化。実行順序を 3 段で合意。

**実行順序（合意）**:
1. **メタラベリング接続を直す（前段→後段の縦化）＋ cluster 入力差し替え**（= 工程 [2] の作り直し + [2.5] cluster 最小版）
   - 前段（primary）= **方向当て（TB 3 分類）を主役に確定**。**regime は方向 primary に昇格させない**（regime 先行型 = 類型 D 回避・業界でも regime は「モデル/サイズを切り替える条件役」が標準 [QuantInsti](https://blog.quantinsti.com/regime-adaptive-trading-python/)）→ 論点② は「regime=条件役」で決着。
   - 後段（secondary meta）= **primary が発火（買い/売り予測）したバーのみ**で「その賭けが勝ったか」を学習＝採用ゲート + sizing。現 meta_label（全 bar 独立 binary・[build_labels_pct.py:316](../../scripts/priority_rebuild/build_labels_pct.py#L316)）の使い方を置換 → 論点①。
   - **揺れ幅（MFE/MAE 回帰）は entry 判定から外す**（§6.2.7 の 97% 支配欠陥）。TP 設定（ATR/realized vol）に転用 → 論点③。
   - **cluster（[2.5]）入力を揺れ幅 28 → TB 決着確率（質軸）に差し替え**（regime 除外）。ただし**磨かず最小版でつなぐだけ**（効果未実証・L-239）→ 論点④。
2. **工程 [3] Sizing・[4] Exit を実装＆学習 → 全工程つないで Stage 3 PnL を見る**
   - ⚠️ **この損益は「合格判定」でなく「感度測定」**（どの工程を上げると NET が伸びるかを測る）。各工程が荒削りなので **$1,900 未達が前提・低くても廃案にしない**（L-238 統計指標早計判断の再発防止）。
3. **損益を見てから 1〜4 をブラッシュアップ**（効く工程に的を絞る・本丸は後段レバー Exit 1.7× / 並立 1.5× / サイズ 1.2×・L-239）。

**業界 verify（2026-05-31 WebSearch）**: メタラベリング = primary（方向・recall 重視・**弱くて可**）→ secondary（誤検出フィルタ + sizing）。「後段の性能は前段の精度に依存・**前段がゼロエッジだと機能しない**」（[Meta-Labeling Wikipedia](https://en.wikipedia.org/wiki/Meta-Labeling) / [mlfinlab tb_meta_labeling](https://random-docs.readthedocs.io/en/latest/implementations/tb_meta_labeling.html)）。現状 regime 0.65 / TB acc 0.49（+0.16pt）= **弱いがエッジあり → リレー可**。meta AUC 0.51 は前段条件付け不在が原因（1 で改善見込み・**未検証**）。

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

### 工程横断: 評価基盤（約定/コストモデル）の実態把握（2026-05-31 本セッション・発注フロー精読）

| 実行日 | 内容 | 実測/事実（実コード・推測排し精読） | 決定/設計原則 | リンク |
|---|---|---|---|---|
| 2026-05-31 | 本番発注フロー精読（run_once_v9.py / replay_csv.py） | **replay_csv.py（手動v9・$370 を出したエンジン）= 約定/コスト正しい**: ①指値 maker entry（`close±0.01%`・L1352）②**不約定モデルあり**（TTL=2bar・`low≤limit`(LONG)/`high≥limit`(SHORT)で約定判定・未到達は取引不成立・L1126-1135）③決済 fee 分岐（`exit_rate = maker if TP_FILLED else taker`＝**TP=maker / SL・TIME・能動クローズ=taker**・L375-379）④**funding・slippage 未控除**（grep 0件）。**run_once_v9.py（本番）**: 指値TTL=**3bar**（L31・replayは2bar）/ SL=placePosTpsl指値（L341）/ 能動クローズ=close_market成行（L374）/ ⚠️ net記録 L130 は能動クローズを `maker×2` で過小計上（実発注は成行taker） | **正しい約定/コストモデルは replay_csv.py に既存** → ML pipeline（run_phase4_b）は「無条件約定＋全maker」で二重に過小＝コスト不正の正体。**評価基盤修正 = ゼロから作らず ML を replay_csv の仕様に合わせる**。$370 も funding/slippage 未控除なので、公平比較には両方に §0.4 funding を同条件で足す（地面が少し下がる） | replay_csv.py L375-379 / L1126-1135 / L1352 ・ run_once_v9.py L31 / L130 / L341 / L374 |

**設計原則（最低限遵守・まこさん指示 2026-05-31）**: ML pipeline は手動時代（run_once_v9.py / replay_csv.py）の約定/コスト仕様を最低限守る:
- 指値 maker entry + **不約定モデル**（指値が TTL 内に到達しなければ取引不成立として扱う・「指値が必ず約定」禁止）
- 決済コスト分岐: **TP=maker指値 / SL・TIME・能動クローズ=taker成行**（「全決済 maker」禁止・§0.2）
- $370 と比較する時は両方に funding / slippage を同条件で適用（地面と現在地を同じ計器で測る）

### 工程横断: 病巣診断と修正順序の確定（2026-05-31・前セッション監査4エージェント + 本セッション統合）

**病巣は2つ重なる（独立4エージェント監査が同じ核心へ収束）**:
- **(A) エッジ源の欠如**: OHLCV テクニカルのみで 5分足の方向にエッジがほぼ無い。423 特徴に方向を生む **order flow / funding / OI / 板情報（OBI/CVD）が1列も無い**。Triple Barrier モデルの上位特徴量が LONG/SHORT とも全部ボラ系（realized_vol / bb_width / body_ratio / adx＝強さで方向でない）＝**「揺れ幅予測への逃げ」が過去フロー全滅と同型で再発**。
- **(B) 評価の楽観化**: コスト過小（全maker）/ sample uniqueness 未適用（AFML #5・K=288 で隣接ラベル窓重複 **99.65%** → OOS 過大評価）/ 「embargo 288」は実体 purge のみ（用語取り違え）/ 生 close 残留（非定常・本番価格レンジで分割無効）/ DSR 現パイプラインから外れ機能せず・PBO 未実装。**すべて数字を実態より良く見せる方向**。

**実証（前セッション Stage3 実測）**: 1取引 粗利 **+0.0101% < 往復コスト 0.038%** → 全15ヶ月マイナス。TP38% : SL48% ≒ 1.5 : 2.0 = **ランダムウォーク幾何 = 方向エッジゼロ**の裏付け。純方向勝率 52.76% / 方向 AUC ≈ 0.50。※純方向 AUC の正面検証は一度も実行されないまま本番学習していた。

**後段レバーの前提（CC の見落とし訂正）**: industry §2.6 の掛け算（Exit 1.7× × 並立 1.5× × Sizing 1.2× = 5.57×）は **Entry が最低限の方向エッジ >1.0× を持つ前提**。Entry が <1.0×（コスト負け）なら後段レバーを掛けても黒字化しない。→ **後段 [3]Sizing / [4]Exit の詳細設計は「Entry にエッジが在る」確認の後**（「後段設計を先に」は誤り）。

**修正順序（監査総意・確定）**: **① 評価を正直にする**（コスト taker/funding 込み・sample uniqueness weight・生 close 除去・embargo 正しく・DSR/PBO 再接続）→ **② 方向エッジが在るか正面確認**（純方向 AUC 実測 + 方向源データ funding/OI/板情報を1列でも足して効くか）→ **③ エッジ確認後にパイプライン作り直す**（縦カスケード）。後段設計は③に含まれ②の後。

**認識（確定・まこさんの直感が正しい）**: 方法（LightGBM / purged walk-forward CV / leak 防止 / pct 化）は業界標準で正しい。だが**枠組み（テクニカルのみ・5分足で方向当て）に方向エッジが構造的に無い**。「方法」でなく「枠組み」の問題。

### 工程横断: 本セッション学習サマリ（設計修正の素材一式・2026-05-31・CC が自ら網羅棚卸し）

**A. 設計修正の骨子（baseline §6 対応・GO 後に §6 へ反映）**:

| §6 | 実証済み欠陥 | 修正方向 |
|---|---|---|
| 横断評価（§6.1.1/§6.2.1 Stage群） | コスト過小 / uniqueness未 / embargo実はpurge / 生close / DSR外PBO無 | **replay_csv 仕様に合わせ正しい計器化**（taker/funding/不約定 + uniqueness weight + 正embargo + fracdiff d* + DSR/PBO 再接続） |
| 入力（§6.0/§6.2.4） | 方向源データ 0 列 | **(A) 方向源（funding/OI/OBI/CVD）追加・効くか検証** ← 本丸 |
| Entry集約（§6.2.3/§6.2.7） | 揺れ幅 97%支配 / meta 全bar独立（縦カスケード未実装） | 揺れ幅を TP 設定へ転用 / **primary方向→secondary採用ゲートの縦カスケード** |
| cluster（§6.3） | 入力 揺れ幅・効果未実証 | TB 質軸・最小版 |
| regime（§6.1） | engagement 17% | 条件役維持・lag 対策 |
| [3]Sizing/[4]Exit（§6.4/6.5 未設計） | 詳細設計なし | **エッジ確認後**に設計（後段レバーは Entry>1.0× 前提） |

**B. 3 KB 全文読了の設計素材**:
- cc_entry §18.5/§20.7: Phase1 v6 全滅 = **8 軸多様性欠落**（①ボラML欠陥 ②アルゴ多様性0[全LightGBM] ③bar種別0[全5m time] ④cascade不在 ⑤strategy配分機械固定 ⑥Meta-Labeling同型[primary悪いと救えない] ⑦リスク管理レイヤー不在 ⑧運用層不在）
- industry §2.6: 5 レバー掛け算 = Entry 1.4× × Exit 1.7× × 並立 1.5× × regime 1.3× × Sizing 1.2× = 5.57×。**全レバー Entry>1.0× 前提**（Entry単独頼り=$592 大幅未達）
- 方向源 order flow: raw alpha 30秒 0.42bps 極小 → 単独の儲け源でなく **執行用シグナル**が業界位置づけ（足しても alpha 小・コスト負けリスクあり＝「足せば勝てる」でなく「効くか検証する設計」に）

**C. 監査 Major の設計直結項目（前セッション・証跡付き）**:
- sample uniqueness 未適用（窓重複 99.65%）→ AFML Ch.4 uniqueness weighting + sequential bootstrap
- 「embargo 288」は実体 **purge のみ**（用語取り違え）→ 正しい embargo を実装
- 生 close（std $19,247・非定常）残留・「close>$48,000」分割は本番$100k超で無効 → fracdiff d* を **ADF 最小 d 探索**（d ハードコード廃止）
- SHORT 偏り 1:20 は **2023 下落相場由来**（SHORT 65% が 2023・in-sample でも勝っていない）= 類型 D 時代依存
- 5 分 time bar 固定を無自覚に既定値化 → 情報ドリブンバー（volume/dollar/imbalance）未検討

**D. 2026 WebSearch verify（4 本）**:
- Triple Barrier は meta-labeling と tandem が 2026 も標準 / ensemble-HMM 2024-26 OOS で DD 半減・walk-forward 必須 / Half-Quarter Kelly 標準・rising vol→smaller position / RL(SAC) exit が volatile regime で Sharpe>2.0（traditional 0.8-1.2）

**E. CC が未だ理解していない項目（次セッションで埋める・正直な棚卸し）**:
- 指値 maker の実際の約定率（→「指値で取れる利益 / 成行に回る割合」を見積もれない）
- 指値約定モデルの作り方（約定確率の業界モデル化手法を知らない）
- 残り未検証の不正（本番実態の確定・net/gross 横断・今日生成したスクリプトは未検証のまま）

### 工程横断: 評価基盤の設計詳細 完成（2026-05-31 本セッション末）

**今セッション完了**: 評価基盤（§0.8 原則）の**詳細設計を baseline §6 直前に新設**（A 約定/コスト + C-F mlfinlab 活用 + leak/regime・各項目に既知答えテスト）。約定/コスト不正の真因を実コードで確定: ①ML が replay_csv の正しいモデルを継承せず（全maker・無条件約定）②**replay_csv 自体も楽観3点**（TP を SL より先に判定 [replay_csv.py L1254-1281]・gap 無視・touch 約定）→ **$370 の地面も楽観値**。

**方針確定（まこさん合意）**: 計器は ML pipeline の当たり前の基礎（ごく一部）→ **監査でなく既知答えテスト**（コインフリップ→net負 等・数学的事実）で検証。テスト pass を正しさの証明とし、まこさんはテスト結果だけ見る（技術不要）。**計器が正しい ≠ 戦略が良い**（計器は「正直に測る」担保のみ・儲かるかは別）。

**次セッション着手**: 評価エンジン実装 **A→C→D→E→F→leak/regime** を1項目ずつ実装 + 既知答えテスト全 pass。mlfinlab 活用（`sampling`/`cross_validation`/`backtest_statistics`/`features`）。`ml_phase2_production` 予測データで **再学習不要**。見積もり 2-4セッション。**詳細仕様は baseline §6 冒頭「評価基盤 詳細設計」参照**。

### 工程横断: 評価基盤 全6項目 実装完了（2026-05-31 第3セッション・1セッションで A〜F+leak/regime 完走）

**完了サマリ**: baseline §6「評価基盤 詳細設計」の全項目を**自前実装 + 既知答えテスト全 pass** で完成。各テストは「答えが数学的に分かりきった問題」で計器の正しさを証明（L-242・まこさんはテスト結果だけ見れば良い）。

| 項目 | 実装ファイル | 既知答えテスト | commit |
|---|---|---|---|
| A 約定/コスト | `eval_engine.py` | T1-T5（コインフリップ→net負/不約定0件/両到達→SL/gap→open/funding控除）5/5 | 66de850 |
| C uniqueness | `sample_uniqueness.py` | C1-C5（同一窓→ū=1/N/重なりなし→1.0/部分手計算/実効N=1/seq>std）5/5 | a0de94a |
| D purge+embargo | `purged_kfold.py` | D1-D5（purge後重なり0[素朴160]/embargo窓0/train末<test始/完全分割/リーク注入naive0.82→purged0.45）6/6 | f991582 |
| E fracdiff | `frac_diff.py` | E1-E6（d=0恒等/d=1=1階差/重み既知/生close非定常→d*=0.35定常/記憶保持corr0.42/生close閾値本番退化）6/6 | 0db306f |
| F DSR/PBO | `dsr_pbo.py` | F1-F6（ノイズbest DSR0.94/N過少→過大/本物1.0/N増単調低下/ノイズPBO≈0.50[8seed]/本物エッジPBO0.0）6/6 | b8a4d8d |
| leak/regime | `leak_regime_check.py` | L1-L3/R1-R2（クリーンleak0/shift(-1)検出/静的スキャン/2023だけ時代依存/全年頑健）5/5 | 7ab373a |

**重要な設計修正（mlfinlab 除外・WebSearch verify）**: baseline §6 は当初「mlfinlab 活用」だったが、検証の結果 mlfinlab(H&T) は **商用有償ライセンス必須 + Python 3.7-3.9 で 3.11 非対応・2023 保守停止**、代替 mlfinpy は MIT/3.11 だが **Alpha・19ヶ月更新なし** → **計器の心臓部に未成熟依存を入れない**判断で全項目自前実装（アルゴリズムは AFML Ch.4/5/7/8 + Bailey&LdP の公開知識・教科書実装は合法）。baseline §6 v3.15 に反映。

**CC の実装プロセス（本セッション・健全だった点）**: 各項目で①既知答えテスト先行 ②fail 時は推測でなく原因診断（T1=エントリー選択バイアス / D5=リークがブロック境界に希釈 / F5=パラメータ実験で実装正当性確認後にテスト修正 / R1=判定基準が端値で脆い）③エンジンを直すかテストを直すかを切り分けて報告。物理 hook（§1.4.6.2）が baseline 編集を 2 回ブロック→WebSearch 再実行で正規通過（bypass せず）。

**⚠️ 計器が正しい ≠ 戦略が良い**: 評価基盤は「正直に net を測る」担保のみ。net がプラスとは限らない（方向エッジは別問題・優先3 で実測判明する）。

### 工程横断: 設計修正の前提整理（2026-05-31 改訂56 後の新セッション・ガワだけ再診断 + 本番実装制約）

> **目的**: 設計を「正しく実装し直す」前に、本セッションで確定した前提を固定する。これを残さないと CC の「業界の形だけ真似る」癖が次セッションで再発する（物理的な錨）。まこさん合意済（本セッションで A〜E を承認）。

**A. 中核の再診断（病巣の言い直し）**
問題は「3工程 vs 1工程」の構成選択ではない。**どの構成でも、業界の道具の"名前"だけ付いて"中の仕組み"が実装されていない（ガワだけ）から赤字**。証拠：
- meta-labeling：列名はあるが primary→meta の縦カスケードが未実装（AUC 0.509＝コイン投げ・0章既述）
- regime：業界の「条件役（戦略を切り替える条件）」でなく「過去描写」を教師なしで作っただけ・edge未検証・後段の使用率17.3%
- cluster：「trade の質」で分けるはずが入力が揺れ幅（ボラ）で regime と冗長（質を分けていない）
- Entry集約 §6.2.7：揺れ幅 z-score が97%支配の中身のない加重和
- この「形だけ真似る」は CC 自身の癖（業界フレーム逃避・cc_role §1.4 / [[feedback_cc_low_perspective_narrow_view]]）

**B. 修正の原則（まこさん確定）**
3工程でも1工程でも、ML 知見でヌケモレ無く正確に実装できなければ失敗する。→ 各工程（regime / Entry / cluster …）を「業界の本当の仕組み vs 名前だけ」で1つずつ棚卸しし、空っぽを正しく実装し直す。**「正確な再現」は5分足 BTC に中身を合わせるところまで含む**（アルゴリズムの名前を揃えるだけは不可・meta_label 列を作る≠メタラベリングを実装した）。

**C. 本番実装可能性の制約（設計時から織り込む・本セッション新規）**
- エントリーは「瞬時の成行」ではない。バー確定→次バーに指値 maker（close±0.01%）→ TTL 3本（15分）で約定 or キャンセル。**採算は maker 約定前提**（焦って成行 taker で入れば薄い edge がコストで消える）。
- 速度は問題でない（時間予算は分単位・手動 run_once_v9 が既に5分足で「判定→指値→TTL」を実証・黒字）。本当の穴は2つ：
  - (1) 本番でバックテストと **1e-9 一致する増分計算が未実装**（今のスクリプトは全部バッチ前提・Phase 7-c 宿題）。ズレると本番で別物＆ leak の温床。
  - (2) **指値の実約定率が未知**（バックテストは「close±0.01% に touch で約定」と仮定・本当の約定率は実弾デモまで不明・既述「CC 未理解項目」）。
- **設計原則（新規）**: 各特徴量・モデルは ①バー確定後に増分計算できる ②オフライン=オンライン一致 ③指値 maker と両立、を**最初から**条件にする。バッチ前提で設計して本番を後回しにしない。

**D. 計器の状態**
評価基盤6本完成（net 正直測定可）。順番は「**中身を正しく実装 → 正しい net で測る**」。計器が正しい≠戦略が良い。

**E. 着手順（未確定・論点）**
regime / Entry の方向エッジ / meta-labeling ——どれも空っぽ。CC のML的見解：regime と cluster は「増幅装置」で、掛ける元＝**Entry の方向エッジがプラスでないと意味がない**（execlog 既述「純方向 AUC の正面検証は一度も実行されないまま本番学習していた」）。手動は regime 工程なしで黒字＝直接エントリーの土台は実在証明済み。→ 推奨：regime を直すなら「accuracy を磨く」でなく「**条件役として net を増やすか**」をゴールに。可能なら先に Entry の方向の土台を正しい計器で測る。ただし着手順は本丸判断（まこさん決定）。

### 工程 [2] Entry エンジン 修正計画（2026-05-31・着手決定＝エンジンから・6軸照合・まこさんGO済）

**着手決定（まこさんGO）**: 増幅装置（regime/cluster）の前に、掛ける元＝**Entry 方向のエッジを正しい計器で測る**。手動は regime 工程なしで黒字＝直接エントリーの土台は実在証明済み（execlog 既述「純方向 AUC 正面検証 未実施」）。

**ベースアップ済（まこさん命令・3KB 全文方向読了 + WebSearch）**:
- industry_benchmark §2.6（Entry 単独 1.6×=$592 未達・全レバー Entry>1.0× 前提）/ §2.1（5min 直接方向 acc 49-51.5% near random・XGBoost 5min 59.4%）
- cc_entry_logic §18.5:1571-1576（6軸診断・逐語）/ §18.4（メタ正攻法）/ §14.1（TB=実取引ミラー・MFE/MAE はバックテスト固有）/ §1-9（手動の品質シグナル + MTF 欠落）
- technical_analysis §I（固定閾値は regime 破綻・adaptive 推奨）/ §D.2（メタ=side/size 分離）
- WebSearch（meta-labeling 正しい実装）: primary=方向 / secondary=**別アーキ**・**primary 発火サンプルのみ**で学習・入力=primary の盲点情報（直近ボラ/regime/確信度）/ 70-30 walk-forward 分割。出典 Wikipedia Meta-Labeling / WhatWorksInTrading / QuantConnect。

**修正 4 手（各 6軸 §18.5 逐語 file:line 宣言・`entry_fix_6axis_gate.md` 義務）**:

| 手 | 軸 | §18.5 逐語（cc_entry_logic_self_study.md:行） | 直す内容 |
|---|---|---|---|
| ① 段1 固定ロジック | 軸4 | :1574「cascade 構造不在（= ML 単段 entry 判定）」 | 手動が使う"種類"の品質シグナル（oversold/BB touch/ADX フィルタ）で高 recall 絞り→ML 段。※手動レシピのコピー禁止・テクニカル基本シグナルで独立設計（[[feedback_priority_starting_line_only]] 整合・手動は"この種類で黒字"の存在証明） |
| ② primary 方向 | 軸1 | :1571「ボラ予測 ML 設計欠陥（= regime 不在 + LONG/SHORT 並列 + ボラ依存ラベル）」 | 方向主役を Triple Barrier 3分類・LONG/SHORT 分離。揺れ幅予測は捨てずサイジング/TP-SL へ役割移動（§14.3/14.5/14.7） |
| ③ メタ 縦カスケード | 軸6 | :1576「Meta-Labeling 失敗（= 案 f primary も secondary も同型）」 | secondary=別アーキ・primary 発火サンプルのみ・盲点情報（②で外した揺れ幅+出来高+MTF・全 OHLCV 由来）入力・出力=採用ゲート+size。現「全bar独立 binary・集約一項」を置換 |
| ④ 異種 stacking | 軸2 | :1572「アルゴリズム多様性ゼロ（= 全 LightGBM）」 | 後段精緻化に回す（土台のエッジ確認後） |

**本番制約（メモ C 整合）**: 4 手すべて既存 OHLCV 特徴量・バー確定後の増分計算で再現可・指値 maker 両立・**新データ（板/order flow）足さない**（大前提整合）。

**最初の一手（最小検証単位・GO 済）**: 手②の核だけ実装 → 純方向エッジ測定。
- 作る: primary 方向（TB3分類・LONG/SHORT 分離・揺れ幅を方向スコアから除外）の純方向 AUC/precision 測定
- 計器: `eval_engine.py`（指値 maker・不約定・net）で手動 $370 と同条件 net 比較
- 入力: 既存 `ml_phase2_production` 予測 + Phase0 ラベル（**再学習・新データなし**）
- 完了条件: 「方向の土台が手数料に勝つか」が初めて数字で出る

⚠️ この net がプラスとは限らない（計器は正直に測る担保のみ）。だが net マイナスを計器/データのせいにしない（大前提）。原因は 4 手のどこが未実装か。

**実測（2026-05-31・最初の一手 完了・`scripts/priority_rebuild/measure_primary_direction_edge.py`）**: 既存 TB 予測（class2_cal=TP先着確率・揺れ幅/meta 不使用＝軸1 の純方向）から方向シグナルを組み `eval_engine.py` で net 測定（再学習なし）。クラス確定 `encode_tb_label=y+1` → class0=SL/1=TIME/2=TP。
- **結果（K12）**: per-trade 平均 net = **マイナス**（test_2025 thr0.35→0.50 で −1.39/−1.22/−1.25/−0.32・取引 55516/16803/2144/183 / test_2026_q1 も −1.20〜−0.91・唯一 +4.53 は thr0.50 N=13 非有意）。**AUC = LONG 0.54-0.56 / SHORT 0.54-0.56（両期間 0.5超で一貫）**。勝率(TP) は閾値上げで 0.348→0.399 と上昇（TB 確率に rank 力あり）。
- **読み**: 素の方向シグナルは**弱エッジ実在（AUC>0.5）だが単体ではコスト負け**。手①(段1フィルタ)/手③(メタ門番)未実装が原因（大前提＝データ/枠組みのせいにしない）。WebSearch「primary 弱くてもゼロでなければメタ効く（ゼロエッジだと機能しない）」の前提を満たす。
- **異常値スメル**: 該当なし（net 負・勝率<70%・唯一の正は N=13）。
- **次**: 手③（本物のメタ門番）→ 弱タネを黒字部分集合に絞れるか測る。出力 `results/priority_rebuild/primary_direction_edge/summary_*.json`。

**実測（2026-05-31・手③ メタ門番 構造実装+評価・`scripts/priority_rebuild/measure_meta_gate_edge.py`）**: 一段目発火バーのみ・別アーキ(LogisticRegression)・盲点特徴量(非ボラ entry品質22列)で「勝つか(net>0)」を門番。二段目 train OOF(baseline fold0-2連結236736)で学習→test適用(leak assert: train末<test始 pass)。
- **結果(K12 primary_thr0.40)**: ungated avg_net/取引 test_2025 **−1.22** / 2026Q1 **−0.96**。門番で改善方向(絞るほど net↑: 2025 thr0.65 で −0.29[N314] / 2026Q1 −0.55[N58])**だが黒字未達**。二段目 AUC 0.52/0.53(弱)。
- **構造的発見(重要)**: 二段目 AUC が伸びないのは**一段目が既に同 OHLCV 特徴量を全部見ているから**(§18.4/Hudson&Thames「primary が使い切った情報では secondary 上乗せ小」)。新データ足さない(大前提)→ **手動の黒字エッジは"特徴量"でなく"特定の固定ルール組合せの構造"**＝ML が同材料から再抽出不可。→ 次は**手①(段1固定ロジック)が本命**(ルールの形を構造で足す・ML 層より効く見込み)。
- **数値裏付け**: 勝率〜40% vs 損益分岐〜43%(TP2.0×/SL1.5×ATR) → あと数pt を良セットアップ絞り込み(手①)で稼ぐ筋。
- ⚠️ データ/枠組みのせいにしない(弱エッジ実在 AUC>0.5)・原因は手①未実装。目標コミット維持。
- **次**: 手①(段1フィルタ)実装 + K6/24/48 horizon 方向エッジ probe(より良い土台確認)。

**実測（2026-05-31・偵察 horizon+幾何 probe・`measure_primary_direction_edge.py` 幾何引数化）**:
- **K horizon probe（test_2025・方向）**: K6 AUC **0.58(最強)** / K12 0.55 / K24 0.53 / K48 0.52。だが avg_net は全K マイナス。**K6 が信号最強でも net 最悪**（勝率0.29・TP2.0×ATR が30分で稀にしか当たらない＝幾何ミスマッチ）。
- **K6 スキャル幾何 probe**: 利確タイト化(TP1.0-1.5/SL2.0-3.0)で**勝率 0.29→0.60 に上昇するが avg_net は不変(−1.6台のまま)**。利確タイト=当たり増えるが1回の儲け小 → 相殺。
- **幾何は土台レバーでない（確定）**: 弱信号では障壁の置き方は「勝率 vs 1回の儲け」を入れ替えるだけで平均(net)を動かさない。**エッジは"信号そのもの"から来るしかない**（martingale 的・ドリフト−コストで決まる）。
- **偵察 中間結論**: 幾何❌ / horizon❌（どの K もマイナス）/ メタ門番△（正方向だが届かない）→ **残る本命レバー = 手①（手動の特定固定ルール構造）**。ML が同材料から再抽出不可な"形"を構造で足す唯一の未検証レバー。手①も届かねば一段大きい設計判断（有限で区切る）。大前提（手動黒字=エッジ実在）でコミット維持。
- 出力 `results/priority_rebuild/primary_direction_edge/summary_*_tp*sl*.json`。

**実測（2026-05-31・手① 段1固定ロジック v1・`scripts/priority_rebuild/measure_stage1_filter_edge.py`）**: 手動式セットアップ(売られすぎ反発 LONG / 買われすぎ戻り SHORT・自己実現的閾値 RSI30/70 + BB pct_b + ADX<25)を固定ルールで直接定義 → eval_engine で net 測定(再学習なし・固定閾値で test に fit せず leak なし)。
- **結果(K12・幾何TP1.5/SL2.0)**: 勝率 **0.40(ML素)→0.53-0.57 に大幅上昇**＝固定セットアップに**本物の精度**(手③ ML 層では出なかった)。avg_net/取引 test_2025 LONG−1.27/SHORT−0.60 / 2026Q1 LONG−0.74/**SHORT +0.23✅**。
- **読み**: 手①が**土台を break-even まで前進**(手②/手③より明確に良い)。勝率0.53-0.57 は幾何TP1.5/SL2.0 の損益分岐 0.571 の境目→net ゼロ付近(僅かにマイナス/SHORT 2026Q1 僅かプラス)。**手動の"特定の形"のエッジは実在**(計器で確認)。あと一押しで黒字。
- **次**: セットアップを**原理ベース強化**(Stoch/MTF confluence + トレンド追随追加・data-snooping 禁止・両期間検証)→ break-even 明確超えを狙う。届けば土台確定→本建設。

**実測（2026-05-31・手① v2 セットアップ強化・6セットアップ化）**: 基本MR + Stoch/MTF確認 + トレンド追随を両期間測定。
- **結果**: 確認(Stoch/MTF)は LONG 勝率0.61に上げるが SHORT 悪化・トレンド追随は今の幾何(TP1.5/SL2.0)で不利(勝率0.44)。**どれも両期間で安定黒字にならず＝break-even の壁**。最良 LONG_mr+c(2025 −0.65 / 2026Q1 −0.39・勝率0.61/0.52)。
- **🔴 偵察 最終結論**: **Entry 単体（ML / 手動式固定ルール / 強化版）は どう切っても ~break-even**。エントリーのいじり(horizon/幾何/確認フィルタ)では明確な黒字に届かない。業界一致（5分 entry 方向は弱・儲けレバーは Exit 1.7×・industry §2.2）。
- **重要（失敗でなく発見）**: セットアップの**勝率0.55-0.61＝本物の精度**(良い場所を選べている)。マイナスは**計器の出口が雑**(固定TP1.5×ATR で頭打ち・損は full)だから＝勝ち場所を選べているが**出口で取り切れていない**。→ **儲けは"出口"で作る**(手動 cat_v9 が12種 Exit を持つ理由)。Entry break-even は後段レバーが乗る土台として十分。
- **次（工程転換）**: Entry break-even を土台に **Exit（出口）設計**(トレーリング/利益ロック/伸ばす)を載せ per-trade net が黒字に乗るか測る。あわせて **手動 $370 を正しい計器で測り直し**(地面確認・execlog 宿題)。
- 出力 `summary_stage1_*.json`。

### 工程横断: 方針転換＝ラチェット（固定審判＋数字だけで採用判定）+ 手動の正直な地面確定（2026-06-01）

**経緯（なぜ転換したか・正直に）**: これまで「業界 ML 手法の"名前"だけ実装（ガワ）→ ガワの出力を測る → CC の原因分析で判断」を繰り返し、何セッションも手動 $370 すら超えられず本番テスト（バックテスト）で崩れ続けた。まこさん診断「すべてが疑わしい／どう制御すればいいか分からない／詐欺に思える」。**積み上がらない構造的原因2つ**: ① 検証可能な1つの数字に何も積ませてこなかった（積んでいたのは計画・診断・"理解"＝複利で増えない）② CC の判断を信じてきた（CC は中身が空でも確信ありげな出力を作れ、テストするまで自分でも本物か見分けられない構造的限界）。資料追加・整理・読ませる、は限界までやっても直らない（＝知識不足が原因ではない）。

**新方式＝ラチェット（戻り止め・まこさん合意）**:
- **選手と審判を分離**: 選手＝戦略（ML・Entry→Exit 通し）／審判＝味見の機械（固定した正直な net 計算）。
- **採用判定は審判の数字だけ**: 数字が上がった変更だけ残す。CC の原因分析は「次に何を試すかのアイデア出し」に降格・採用判定には使わない（数字が答え合わせ）。ガワを出しても数字が動かず自動で捨てられる（まこさんが CC を見張らなくてよい）。
- **蓄積するのは「数字を上げた変更＋コード」だけ**: 理解・設計・長文は蓄積に数えない。
- **制約**: 1周（小変更→学習→テスト）≤ 約5分・小さく速く回す（手動を反復テストで磨いた経緯と同型・まこさん指摘）。8時間の 56 ラベルまとめ学習は廃止。

**作った物 + 測った数字（まこさんが再実行で検証可能）**:
- `scripts/priority_rebuild/score.py`（審判）新規・約80行。入力＝売買記録 CSV、出力＝月次 net 1つ。コストは `eval_engine`（T1-T5 pass 済）の確定値: entry=指値 maker／決済 TP_FILLED=maker・他=成行 taker+slippage／funding 8h 境界。実行時に**自己検算**（再計算 gross/fee が CSV と一致＝審判がデータを正しく読めている証拠）を表示。
- **手動 cat_v9 の正直な地面**（既存 replay 出力 1,157 trade を score.py に通す・`replay_csv.py` は実行せず＝保護ファイル）: **月平均 net $354.54/月**（合計 $4,254）。CSV(slippage/funding 抜き)$4,506 → 審判 $4,254（差＝追加した slippage $252 ＋ funding ≈0）。自己検算 gross 差 $0.001／fee 差 $0.05 ≒ 0。
- **正直な事実（地面の中身）**: 月次は −$144〜+$1,896 でバラバラ・利益 99% が下落5ヶ月集中。**全月 ≥ $1,900 クリアは 12ヶ月中 0**（2026-02 のみ辛うじて）。＝超えるべき地面は「月平均 $354／全月 $1,900 は 0/12」。
- 再現: `python3 scripts/priority_rebuild/score.py results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv`。commit 未（まこさん OK 待ち）。

**次（本エントリー後の議論）**: PDCA の回し方を決める（1ステップの"小変更"の単位／entry→exit 通しの最小戦略の作り方／審判の入力フォーマット統一／train と test の分け方＝leak 防止／5分制約の運用）。

---

## 2. 現在地 + 次セッション着手（新セッションは最初にここを読む）

**【2026-06-05 最新・新セッションはここを最初に読む】**

- **まず読む**: `.claude/ratchet/session_log_20260605.md`（今日の全経緯・V9構造/MLラチェット方法/E4失敗/学び）＋ `v9_priority_styles.md`(auto-memory) ＋ lessons L-247。
- **大前提訂正**: 地面 $172/$354 ＝ **V9全部入り（regime切替・全Priority）の数字**（P23単独でない・sha256一致＋score.py $172.68 で確定）。5年暖機版は採点 **$149.50**。ライブBotはP23単独（手動で1つずつ調整しP23まで）。詳細 [[manual_v9_p23_only_reason]]。
- **V9構造（CCが読めなかった核心）**: **Priorityごとにスタイルを変えて設計**（MAX_ADDS=1=スキャル小勝ち / 5=平均建値ポジション大勝ち）。詳細 [[v9_priority_styles]]。
- **E4（`strat_v9_ml.py`・破棄）**: V9候補に勝率二値メタ＋MTF → AUC 0.673 だが net 超えず。原因＝corr(prob,net)=−0.027（勝率とnet無相関）＋**スタイル違いPriorityを1モデルに混ぜた**。
- **現方針の設計書（正本）** ＝ **`.claude/ratchet/strat_v9ml_design.md`**（V9踏襲ML・§1方針確定/§5未確定/§6最初の一手）。旧v1設計は `strat_v1_design.md`（破棄バナー付き・履歴）。
- **次の一手（合意・未着手）**: **Priority（スタイル）別に Entry閾値+採用+Exitパラメータをセットで net最適化**（予測対象は勝率でなく**net金額**・MTF入力・出口を同サイズに揃えれば勝率≈net）。§4.6照合で設計(A)報告→実装。RLは小データ過学習リスクで保留（業界裏取り済）。
- **地面**: 採点 $172(365d)/$149.50(5年暖機) ／ coinflip −$268 ／ v1 E3 −$430。

---

**【2026-06-04・新セッションはここを最初に読む】**

- **まず読む**: `.claude/ratchet/session_log_20260604.md`（今日の全経緯・CC の失敗・現在地・歯止め4点）＋ lessons L-246。
- **今日やったこと（ratchet E2/E3）**: v1 戦略 `scripts/priority_rebuild/strat_v1.py` 実装 → 採点期間2025-04〜12 で **E2（LONG TP0.6/SL2・SHORT TP0.8/SL2）月−$897（破棄）→ E3（TP/SL 対称1.0%）月−$430（採用だが SHORT 完全死亡・全LONG）**。ledger E2/E3 記録。
- **診断（`diagnose_short.py`）**: 病巣は判定(θ)でなく **学習構造**。v1 は全bar無差別の単段＝**過去 Phase1 v6 全滅(8軸欠落)の再演**。工程1 regime・工程2 候補生成・確認が無い。下落bar無差別 SHORT の実勝率0.446（＝絞りの段が無いと素材が死ぬ）。
- **🚨 CC のループ・欺き（L-246・最重要警告）**: ①KB3本(technical/industry/cc_entry)を読まずに引用(類型G・読んだフリ) ②v1 が負けた後 `ml_pipeline_baseline_v1.md`(8工程設計)に戻ろうとした＝**ガワで何セッションも失敗して ratchet になった経緯(本 §1 方針転換 2026-06-01)を踏み外したループ** ③短絡連発。**→ 新セッションは「設計図(8工程)に戻る／資料を読んで設計をなぞる」を絶対にしない**（本 §1 が「効かない・知識不足が原因でない」と結論済み）。
- **トレード手法ノート**: `.claude/memory/trade_methods_study.md` 新規（ML設計用・最低限・細部は都度深掘り）。設計方針＝**regime最上位 → 局面別の手法で候補生成(コンフルエンス) → 確認 → ML判定 → Exit の段構造**（v1 の8軸欠落と対照）。
- **次の方針（ratchet・設計図に戻らない）**: v1(E3 −$430)から **数字が上がる小変更を1つずつ** `score.py` で測る。トレード手法の知識(regime判定/候補生成/確認)を**小変更として1つ入れて数字を見る**（壮大設計を一気に作らない）。1周≤5分。封印2026Q1は触らない。
- **超える地面**: 採点期間2025-04〜12 月平均 **$172**(手動)／ coinflip −$268 ／ v1 E3 −$430。

**新セッションが読む文書（この順）**:
1. `.claude/ratchet/session_log_20260604.md`（今日の詳細・最初に読む）
2. 本 execlog §2 現在地（この 2026-06-04 ブロック）
3. `lessons_active.md` L-246（歯止め）＋ L-245
4. `.claude/ratchet/ledger.md`（E0-E3 PDCA記録）
5. `.claude/memory/trade_methods_study.md`（ML設計用トレード手法ノート）
6. Layer1 必読（`cat_requirements.md` / `cc_role.md` / `false_positive_incident_policy.md` / `CLAUDE.md` / `WORKFLOW.md` 改訂59）

---

**【🧊 2026-06-01 方針転換: ラチェット方式（転換の経緯・参照のみ）】**

- **やり方が変わった**: 大きく設計して測る → ❌。**小さく変える → 固定審判 `score.py` で月次 net を測る → 数字が上がった分だけ残す**、を速く回す（ラチェット）。詳細は直上 §1「方針転換＝ラチェット」エントリー。
- **超えるべき地面（確定・2026-06-01）**: 手動 cat_v9 = **月平均 net $354.54**／全月 ≥ $1,900 は 12ヶ月中 0。これが ML が超える対象。
- **審判**: `scripts/priority_rebuild/score.py`（固定・改造しない・改造する時は再検証）。全戦略をこれに通す。
- **CC の出力の扱い**: 理解・設計・長文は蓄積に数えない。残すのは「score.py の数字を上げた変更＋コード」のみ。CC の原因分析はアイデア出しまで・採用は数字が決める。
- **次の着手**: PDCA の回し方を確定（議論中）→ 確定後、entry→exit 通しの最小戦略を1個作って score.py に通し、$354 を超えるか測る。

---

> ↓ 以下 2026-05-31 改訂57（Entry break-even 偵察）は本方針転換前の記録・🧊 参照のみ。「Entry break-even が天井／儲けは Exit」結論は、6軸が開いたままのガワのモデル（`ml_phase2_production`）を測った判断で、地面の数字（$354）に対する検証を経ていない（＝ラチェットで測り直す対象）。

**【🧊 2026-05-31 本セッション（改訂56後）末・旧・参照のみ】**

**本セッション結論（一行）**: Entry エンジンを「ガワだけ→正しい仕組み」で作り直し、4手＋偵察で実測 → **Entry 単体（ML / 手動式固定ルール / 強化版）は どう切っても per-trade net ≈ break-even**。儲けのレバーは Entry でなく **Exit（出口）**と判明。次は Exit 設計。

**本セッション経緯（時系列・詳細は §1 各実測ブロック・全 commit 済）**:
1. **設計再診断（A〜E 前提整理）**: 問題は「3工程 vs 1工程」でなく「業界の名前だけ真似て中の仕組み未実装（ガワだけ）」。meta-labeling / regime / cluster / §6.2.7 すべて空っぽ実装と確定。本番実装制約（増分計算・指値maker・新データ足さない）を設計時から織込む原則を固定。
2. **着手＝Entry エンジンから**（増幅装置 regime/cluster の前に掛ける元のエッジを測る）。3KB全文 + WebSearch でベースアップ。修正4手を baseline §6.2 改訂バナーに反映（軸4 段1固定 / 軸1 primary方向 / 軸6 メタ縦カスケード / 軸2 stacking後段）。
3. **実測（全て eval_engine・再学習なし・既存予測/特徴量流用）**:
   - **手② 純方向**: AUC 0.54-0.58（弱エッジ実在）だが per-trade net 負。
   - **手③ メタ門番（構造実装）**: net を正方向に動かすが届かない・二段目 AUC 0.52。**構造的発見**＝一段目が同 OHLCV 特徴量を既に全部使用済 → OHLCV 内で ML を重ねても上乗せ限定（§18.4）。手動エッジは"特徴量"でなく"特定の固定ルールの形"。
   - **horizon probe**: K6 が方向最強(AUC0.58)も net 最悪・全K負。
   - **幾何 probe**: 利確タイトで勝率 0.29→0.60 上がるが net 不変 → **幾何は土台レバーでない**（弱信号は障壁で勝率/儲けを入替えるだけ・平均不変）。
   - **手① 固定ルール（手動式 mean-reversion）**: 勝率 0.40→0.55-0.61 **大幅上昇＝本物の精度**。だが net は break-even 境目（2026Q1 SHORT +0.23）。
   - **手① v2 強化（Stoch/MTF/トレンド追随）**: break-even 超えず。
4. **🔴 偵察 最終結論**: Entry は **break-even が天井**（業界一致・5分 entry 方向は弱）。勝率は出ている（良い場所を選べている）が**固定TPで勝ちを切っている＝出口で取り切れていない**。→ **儲けは Exit で作る**（industry Exit 1.7× が最大レバー・手動 cat_v9 が12種 Exit を持つ理由）。Entry break-even は後段レバーが乗る土台として十分。
5. **生成物（commit 済）**: `measure_primary_direction_edge.py`（手②/horizon/幾何）/ `measure_meta_gate_edge.py`（手③）/ `measure_stage1_filter_edge.py`（手①）。出力 `results/priority_rebuild/primary_direction_edge/summary_*.json`。

**次セッション着手（5列表・Exit へ工程転換）**:

| 優先 | 使う/直すファイル(パス) | 入力データ | 存在✅ | 最初の一手 | 完了条件 |
|---|---|---|---|---|---|
| 1 Exit probe | 新規 `scripts/priority_rebuild/measure_exit_edge.py`（eval_engine コスト定数流用・ATRトレーリング simulator） | 手① mean-reversion セットアップ + bars(CSV) | ✅ セットアップ/bars 存在 | break-even の良エントリー(勝率0.55-0.61)に **ATRトレーリング出口**(固定TP外す・trail M×ATR・保有延長12→48)を載せ per-trade net が黒字に乗るか測る。trail/保有 数点。未来非参照(fill+1以降) | トレーリングで net がプラスに乗るか判定 |
| 2 手動$370 地面確認 | `runner/replay_csv.py` / `strategies/cat_v9_decider.py` | 手動 entry | ✅ コード存在 | 手動 $370 を正しい計器(eval_engine 同条件)で測り直し + 利益源(entry/exit/add)を分解 | 真の地面が出る |
| 3 土台確定→本建設 | （Exit 黒字なら） | Exit付き結果 | — | 手①エントリー + Exit を段構造に確定 → primary/メタ/サイジング載せ → Replay 月次 net | 月次 net 測定経路確立 |

⚠️ 偵察は締めた（Entry break-even 確認・stop ルール通り）。Exit が黒字に乗らなければ後段レバー（並立/サイジング）や一段大きい設計見直しへ（有限で区切る・大前提でコミット維持・データ/枠組みのせいにしない）。

---

**【2026-05-31 第3セッション末 更新・🧊 旧（本セッションで Entry 実測まで超過）】評価基盤 全6項目 完成（A/C/D/E/F/leak-regime・既知答えテスト全 pass）**:
- 「正しい計器」が揃った（net を正直に測る土台）。実装ファイル6本 + テスト6本・commit 66de850〜7ab373a。詳細は §1 末尾「評価基盤 全6項目 実装完了」。
- mlfinlab は商用有償+3.11非対応で除外確定 → 全項目自前実装（baseline §6 v3.15）。
**🚨 大前提（まこさん指摘・毎回再演・L-243 / [[feedback_ml_defect_not_data]]）**: 手動 cat_v9 は初歩 OHLCV ロジックのみで net 黒字（月$370）→ ML が net マイナスは **ML 設計の不具合**が原因。「エッジが無い」「order flow が要る」「枠組み barren」「5分足方向は無理」とデータ/枠組み/市場のせいにする診断は**禁止（excuse-making・恥）**。手動黒字＝このデータでエッジ実在・捕捉可能の存在証明。ML が手動スタートライン（cc_role §1.7）を下回る＝設計欠陥確定。

- **次セッション着手 = 6軸ゲートに沿った Entry 設計欠陥の修正**（`entry_fix_6axis_gate.md`・§18.5 由来・SessionStart 強制ロード）。「計器を実データに繋ぐ」「現モデルの net 測定」は**先送り**（現モデルは 6軸欠落のまま＝測っても判断材料にならない・confounded）。計器（eval_engine 等6本）は 6軸修正の各段を測る道具として使う。
- **着手順 確定（2026-05-31・まこさんGO）= エンジン（Entry 方向）から**。最初の一手＝**primary 方向の純エッジ測定**（既存 `ml_phase2_production` 予測 + `eval_engine.py` で手動 $370 と同条件 net 比較・再学習なし）。修正 4 手の詳細は §1「工程 [2] Entry エンジン 修正計画」（軸4 段1固定 / 軸1 primary 方向 / 軸6 メタ縦カスケード / 軸2 stacking は後段）。
- **新 5列表（2026-05-31 第3セッション末・6軸リフレーム）**:

| 優先 | 使う/直すファイル(パス) | 入力データ | 存在✅ | 最初の一手 | 完了条件 |
|---|---|---|---|---|---|
| 1 軸1 ボラ逃げ是正 | `entry_fix_6axis_gate.md` 照合 + Entry 学習スクリプト | Phase0 ラベル(TB方向) + regime出力 | ✅ ラベル/regime 存在 | entry 方向の主役を Triple Barrier(方向)+regime に・LONG/SHORT分離・揺れ幅は捨てずサイジング/TP-SL/フィルタへ（§14.3/14.5/14.7） | 軸1 受け入れ条件 ✅（方向スコアで揺れ幅非支配・分離・揺れ幅活用先あり） |
| 2 軸4 cascade | 固定ロジック段1 設計 | 手動が使う entry品質シグナル(RSI/Stoch/BB/ADX・cc_entry §1-9) | ✅ 特徴量に存在 | 手動クラスの固定ロジックで段1絞り→ML段。手動の働くシグナルを構造で強制 | 段構造あり+段1発火率記録 |
| 3 軸2/3/5/6 | 6軸ゲート各行 | — | — | 異種stacking/bar多様性/HRP配分/Meta是正を順次 | 各軸 ✅ |
| 4 計器で測定 | eval_engine 等6本 | 6軸修正後の予測 | ✅ 計器完成 | 6軸修正版を正しい net で測り手動$370 と同条件比較 | net 現在地（手動超えたか） |

⚠️ **計器が正しい ≠ 戦略が良い**。だが net マイナスを**計器/データ/エッジのせいにしない**。原因は 6軸のどこが閉じてないか（大前提）。L-238 早計判断禁止とは別物（こちらは「設計欠陥を直視せず諦める」禁止）。

---

**↓ 以下は本セッション開始時点の現在地（評価基盤完成で優先1は達成済・参照のみ）**

**現在地（2026-05-31 セッション末・最重要・前回までの前提が崩れた）**:

⚠️ **今日、ML pipeline の土台に「基本的な不正」が確定した（workflow 監査・実コード証跡）**:
- **約定モデルの不正**: TIME_EXIT・能動クローズ（本番は成行 taker 0.042%）を全部 maker（0.014%）で計算。`TAKER_FEE` 定数すら未定義（`run_phase4_b.py` compute_pnl L221-229 / rolling_option5 系）。
- **net でなく gross 判定**: funding 未控除・slippage 未加算・taker 未適用の値で `月次 net_pnl ≥ 1900` 判定。`run_phase5.py` に「楽観 Maker 指値 fill / スリッページなし」と明記。
- **本番再現不可能**: 「指値が必ず約定」前提で不約定（取引不成立）を無視。funding 旧廃止値/未控除（phase5_e は確定 p50 の50倍）。
- → **過去の PnL / Replay / $1,900 判定はすべて無効・信用できない**（水増し）。false_positive §2 類型E + §0-1。

**結論: 全設計し直し（まこさん判断）**:
- 0 章「縦カスケード化 修正方針」は、評価が水増しだった前提が崩れたため**保留**（破棄でなく評価基盤が正しくなってから再判断）。
- **まず正しい評価基盤（PnL/Replay エンジン）を作るのが最優先**: 指値maker/成行taker 使い分け・funding 控除・slippage・不約定モデル・net 判定。これが無いと過去も未来も判定不能。
- 正しい計器で測り直して**本当の net 現在地（手動 Priority 月$370 より上か下か）**を出してから Entry/Exit/cluster/縦カスケード を実数で再判断。

**今日の整備（完了）**:
- **§0 大原則を baseline 冒頭に追記**（net判定 / 指値maker・成行taker / Prime Directive / コスト確定値 / 0.12BTC / 手動扱い / 異常値STOP）。散在大前提を集約。hook 一時無効化（まこさん承認）→書く→sha256 復元検証済。
- **プロセス変更の合意**: CC は「読め」で守らない構造欠陥が全面実証（grep ショートカット / 手動ベンチマーク扱い / マイナスを地面と呼ぶ / 積み上げ無視ちゃぶ台返し連発 / コスト不正を自分の PnL でも再演）。文書を増やす対策は効かない（false_positive §5）。→ **機械的ゲート（assertion / 完了報告の機械証跡義務 / 物理hook）+ まこさんの問いかけリスト + CC が答えに毎回証跡添付**、で縛る方向。

**監査結果（workflow・実コード証跡）**:
- 学習パイプライン全体監査（de Prado 7 reasons）: task `w1iajfa3i`（方向エッジ薄い・ボラ逃げ再発・sample uniqueness 未対処・embargo 実は無い・生 close 残留・多重検定未補正）
- 約定/コスト不正監査: task `weg49ehfw`（上記）。ただし 9 中 5 エージェント構造化出力失敗＝**私の PnL baseline・本番実態確定・net/gross 横断・破壊係 は未検証・要再実行**。

**次セッション CC 優先順位（5 列表・全部やり直しの新・本丸）**:

| 優先 | 使う/直すファイル(パス) | 入力データ | 存在✅ | 最初の一手 | 完了条件 |
|---|---|---|---|---|---|
| 1 評価基盤を正す | `scripts/priority_rebuild/run_phase4_b.py` compute_pnl(L221-229) + PnL/Replay 全般 | 本番約定実態(exchange_spec.md・§0.2) | ✅ コード存在 | compute_pnl を exit 種別で maker/taker 分岐・funding/slippage 控除・不約定モデル・net 判定に直す + **コスト検証 assertion を埋める** | 正しい計器で動く + assertion 稼働 |
| 2 問いかけリスト+機械ゲート 正式化 | `.claude/rules/cc_questioning_checklist.md`(新規) + PnL assertion | 本セッション問いかけリスト草案 | — | 問いかけリスト確定 + assertion/hook 化 | まこさんレビューOK + ゲート稼働 |
| 3 正しい計器で現在地測定 | 評価基盤 + `ml_phase2_production/` 既存予測 | 正しいコストモデル | ✅ 予測生成済 | 既存 Entry を正しい net で測り **手動 $370 と比較** | 本当の net 現在地が出る |
| 4 設計し直し判断 | （議論 + baseline §0 遵守） | 優先3 の net 実数 | — | net 実数を見て Entry/Exit/cluster/縦カスケード を再判断 | 方向確定 |

**⚠️ 次セッションへの最重要警告**: 過去の `ml_phase2_production` / Phase5 系の PnL 数値・$1,900 判定を「効いている根拠」に使わない（コスト不正で全無効）。**正しい評価基盤（優先1）が出来るまで、損益に関する一切の合否判断をしない**。問いかけリスト草案の詳細は本セッションのチャット参照。

---

**↓ 以下は 2026-05-30 時点の旧現在地（上の不正発覚で前提が無効・参照のみ）**

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
