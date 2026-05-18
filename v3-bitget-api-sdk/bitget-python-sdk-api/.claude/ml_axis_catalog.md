# ML 軸カタログ（CAT-bitget ML Pipeline 決定変数 全23軸）

ソース: `CAT－指標マトリックス - シート1.csv`（2026-05-18 生成）
目的: CC が ML 学習フローを考察するための参照資料。設計判断の「どこが確定でどこが未探索か」を可視化する。

---

## 凡例

### 戦略コード（絞り込み戦略）

| コード | 意味 | 判断タイミング |
|--------|------|--------------|
| A | 全期入れ（全候補を ML に投入、事前絞り込みなし） | 学習時 |
| B | 探索試行（複数候補を試してベストを選ぶ） | Phase 4〜5 実験 |
| C | ML 学習対象（ML が自動最適化する変数） | 学習中 |
| D | 既定固定（事前確定・変更禁止） | 設計時 |

### Layer 定義

| Layer | 対象 | 状態 |
|-------|------|------|
| Layer 1 | 基盤整備（特徴量追加・combos見直し・trailing修正） | **現在進行中** |
| Layer 2 | 統合フェーズ（add設計・サイジング・マルチサイド・フィルタ） | Layer 1 完了後 |
| Layer 3 | 高度最適化（アルゴ多様化・ハイパラ・walk-forward・不確実性） | Layer 2 完了後 |
| Phase 7 | Bot統合・本番運用 | 全Layer完了後 |

### Phase 定義（ML Pipeline フロー）

```
Phase 0（ラベル生成）→ Phase 1（学習）→ Phase 2（検証）→ Phase 3（refit）
→ Phase 4-a（クラスタリング）→ Phase 4-b（Exit選定）→ Phase 5（月次評価）
→ Phase 7（Bot統合）
```

---

## 23軸 概要マトリックス

| 軸ID | 軸名 | カテゴリ | 戦略 | Layer | 状態 |
|------|------|---------|------|-------|------|
| A-1 | Entry 指標 | I. シグナル定義 | A | Layer 1④ | 1432指標投入済・8件未学習・拡張中 |
| A-2 | Exit 指標 | I. シグナル定義 | A+B | Layer 1①/2①⑤ | trailing 0件採用が構造的問題 |
| A-3 | 閾値/パラメータ | I. シグナル定義 | A+C | Layer 1①/2 | LightGBM自動分割・パラメータ違い未追加 |
| A-4 | 時間軸（K） | II. 時間設計 | B | Layer 1③ | K=12/24/48/96・K96 LONG がno_trade主因 |
| A-5 | 時間足（bar） | II. 時間設計 | A | Layer 1④ | 5m〜1d の6軸・1w/1M 未投入 |
| D-α | シグナル発火頻度 | II. 時間設計 | C | Layer 1①/2 | 他軸の従属変数 |
| A-6 | add数/配分 | III. ポジション設計 | B+C | Layer 2 | ML学習対象外（Priority別固定） |
| A-7 | ポジションサイジング | III. ポジション設計 | D+B+C | Layer 2② | 0.12 BTC 上限絶対不変 |
| B-8 | 同時保有数（cap） | III. ポジション設計 | B | Layer 1②/2 | 明示的cap なし・no_trade 86.2%の根本原因 |
| D-β | 保有期間中の管理 | III. ポジション設計 | B+C | Layer 2 | add トリガ・部分決済（A-2/A-3/A-7に統合） |
| D-ζ | マルチサイド | III. ポジション設計 | D+C | Layer 2/3 | hedge_mode許可（D固定）・0.12 BTC内両建て可 |
| D-γ | エントリー位置フィルタ | IV. フィルタ | B | Layer 2 | location_prev・直近Nレンジ位置（未ML化） |
| D-δ | 時間帯・曜日フィルタ | IV. フィルタ | B | Layer 2統合 | 未投入・個別Priority最適化禁止（L230） |
| D-ε | 市況フィルタ（regime） | IV. フィルタ | B | Layer 2以降 | 未投入・研究凍結中 |
| B-9 | 発火条件の組み合わせ深さ | V. 学習設計 | C | Layer 3 | num_leaves=31（K12 LONGのみ15） |
| B-10 | 学習アルゴリズム | V. 学習設計 | B | Layer 3 | LightGBM×16ラベル・他アルゴ未試行 |
| B-11 | クラスタリング手法 | V. 学習設計 | B | Layer 1/2 | KMeans k=3・ボラレベル分類のみ（方向性未分類） |
| B-12 | 特徴量変換 | V. 学習設計 | A+B | Layer 1④ | pct/rank等は1432内・Fractional diff等未追加 |
| B-13 | Entry ratio 閾値 | V. 学習設計 | B+C | Layer 1①/3 | rolling 365日 q90/q95/q99・K24/K96の欠落あり |
| B-14 | 学習データ範囲 | V. 学習設計 | D+B | Layer 3 | train 2021-04〜2024-12（D固定） |
| B-15 | 目的関数/不確実性 | V. 学習設計 | D+B | Layer 3 | RMSE最小化・NET乖離が構造的問題 |
| D-η | 手数料モデル | VI. 執行設計 | D | Phase 7 | Maker 0.014%/Taker 0.042%（D固定・Phase 5控除済） |
| D-θ | 発注タイプ | VI. 執行設計 | D+B | Phase 7/Layer 3 | Maker指値前提（D固定）・不約定リスク未モデル化 |

---

## カテゴリ別詳細

### I. シグナル定義（3軸）

---

#### 軸 A-1: Entry 指標

**定義**: MLがEntry判定の入力として参照する指標群。

**現状**:
- 1432指標 / 145ファミリー、6時間足（5m/15m/30m/1h/4h/1d）
- カテゴリ構成:
  - 1-A: 指標値・推移（66ファミリー/348列）— ADX/ATR/BB/RSI/MACD/Stoch/MFI等
  - 1-B: 値動きの形（20ファミリー/347列）— W形/M形/V字/スイング距離等
  - 1-C: 構造的要素（59ファミリー/737列）— Fibonacci/Pivot/Volume Profile/サポレジ等

**未学習 8件**（1432不在確認済）:

| 指標 | 状況 |
|------|------|
| Stochastic(14,3) K | 1dのみ存在 → 5m/15m/30m/1h/4h 不在 |
| Stochastic(14,3) D | 全TFで不在 |
| RSI(21) | rsi14/rsi7のみ → rsi21全TF不在 |
| RSI slope（diff-3） | 差分系ファミリーなし |
| BB middle slope | bb_pct_b/bb_width_pctはあるが傾き系不在 |
| RCI(7)/RCI(9)/RCI(52) | rci系ゼロ・完全不在 |
| ADX spike（3bar diff） | adx14/di系はあるがスパイク検知不在 |

**まこさん発振系 3種**:

| 指標 | 判定 |
|------|------|
| RSI レートオブチェンジ（RSI ROC） | 代替不可・新規追加が必要（roc_10/20は価格ROC） |
| MACD ヒストグラム slope | macd_hist_change で部分カバー・要verify |
| Stoch %K-%D 差分 | stoch_d不在のため計算不可・stoch_d追加とセット |

**追加候補（未取得）**: TA-Lib/pandas-ta/tulipindicators/Backtrader/QuantConnect/TradingView/Wikipedia/Murphy・Kaufman/Lopez de Pradoのカタログを網羅して新規指標を抽出予定。

**拡張見込み**: 1432 → 約2000〜2500列（未学習8件+発振系3種+1w/1M MTF拡張+業界カタログ追加）

**戦略**: A（全投入）— cc_ml_design_spec §8「特徴量の事前絞り込み禁止」明文

**Layer担当**: Layer 1④（最優先・Phase 0から再実行）

---

#### 軸 A-2: Exit 指標

**定義**: ポジション解消の判断材料となる指標群。

**現状（Phase 4-b v3 採用結果）**:

| Exit方式 | 採用combo数 | train PnL合計 |
|---------|-----------|-------------|
| time_exit（時間Exit） | 16 | $2,668,698 |
| fixed_tp（固定TP） | 3 | $129,420 |
| trailing | **0** | $0 |

**構造的問題（trailing 0件採用）**:
- 仮説1: trailing候補パラメータ範囲が狭すぎる
- 仮説2: BTC 5m値動きの粒度でtrailingが機能しない
- 仮説3: train PnL idxmax採用方式がtrailingを不当に過小評価
- 仮説4: trailing実装にbugがある
→ Layer 1①で実装verify + 再評価が最優先

**手動Priority Exit 11種類以上（未ML学習）**:
TP_PCT / SL_PCT / TIME_EXIT_MIN / TIME_EXIT_DOWN_FACTOR / MFE_STALE_GATE / TRAIL_RATIO / PROFIT_LOCK / STOCH_REVERSE_EXIT / SHORT_RSI_EXIT / TP_BB_RATIO / TP_ADX_BOOST

**第2弾候補（cc_ml_design_spec §3.2・未実装）**:
- ATR連動SL（ボラに応じた損切り幅）
- MFE比例Exit（含み益ピークのX%戻りで利確）
- Stale検知（一定時間動きなしで決済）

**戦略**: A（指標カタログ全投入）+ B（Exit方式探索）

**Layer担当**:
- Layer 1①: trailing不採用原因究明・手動Priority 8種類をML対象追加・採用方式見直し
- Layer 2①: 第2弾3候補追加
- Layer 2⑤: 業界カタログ追加Exit + 部分決済（scale-out）追加

---

#### 軸 A-3: 閾値 / パラメータ

**定義**: 2種類を含む
- A-3-a パラメータ: 指標自体の計算パラメータ（RSI period=21等）
- A-3-b 発火閾値: 指標値が満たすべき条件値（ADX≥30等）

**現状**:
- パラメータ: 1432に特定パラメータのみ（rsi14/rsi7・adx14・macd 12,26,9等）。rsi21/adx7/adx21等の違いは未投入
- 発火閾値: LightGBMの決定木が自動学習。手動Priorityの特定値（ADX≥30等）を保証はしない
- LightGBM現状: num_leaves=31（K12 LONGのみ15）/ max_depth=-1 / min_data_in_leaf=100 → 16ラベル×5000木×31葉 ≈ 2.5M通りの暗黙的閾値分割

**手動Priority未カバーの閾値ズレ（CC棚卸し §9）**:
- 別閾値2件: ADX(14)、MACD(12,26,9)のクロス判定（派生特徴量化されていない）
- 部分5件: ATR絶対値・EMA絶対値・BBタッチ近傍・location_prev（前バーシフト）・entry_risk_score

**手動Priorityの閾値組み込み案（3案）**:
- A案（フラグ化）: is_adx_ge_30等のブール特徴量を1432に追加。MLが手動知見を直接学習可能
- B案（後処理フィルタ）: ML出力後に手動Priorityフィルタを重ねる
- C案（cluster入力追加）: k-means入力に手動閾値フラグを混ぜる
→ 現時点推奨: A案+B案併用（監査経路で最終判断）

**戦略**: A（パラメータ違い並列追加）+ C（閾値帯はML自動学習）

**Layer担当**: Layer 1④（パラメータ違い追加）/ Layer 1①・Layer 2（派生特徴量・後処理フィルタ判断）

---

### II. 時間設計（3軸）

---

#### 軸 A-4: 時間軸（予測ホライズン K）

**定義**: MLが何時間先までのMFE/MAEを予測するか（K = 何5mbar先まで）

**現状**:

| K値 | 保有時間 | 状況 |
|-----|---------|------|
| K=12 | 1h | 採用中 |
| K=24 | 2h | 採用中（q99欠落あり） |
| K=48 | 4h | 採用中 |
| K=96 | 8h | 採用中・**no_trade 86.2%の主因** |

**構造的問題**: K96 LONG q95-q99がtime_exit 8h保有 → 0.12 BTC枠を独占 → 他combo発火不能

**追加候補**:
- K=6（30分）— 短時間スキャルピング的
- K=144（12h）— 中期
- K=288（24h）— 保有時間上限1日制約内の最大値

**q-band欠落**:
- K24 LONG q99・K24 SHORT q99 が欠落
- K96 SHORT q95-q99 が test 0件

**戦略**: B（探索試行）

**Layer担当**: Layer 1③（K窓見直し・K96問題解消）

---

#### 軸 A-5: 時間足（特徴量集計周期 bar）

**定義**: 特徴量を計算するbarの周期（予測ホライズンKとは別軸）

**現状**: 6軸（5m / 15m / 30m / 1h / 4h / 1d）

**未投入**:
- 1w（週足）/ 1M（月足）— CC棚卸し §10でFalse確認済
- 1m / 3m — CLAUDE.md §⛔「1m足回帰禁止」提案禁止リスト

**1w/1M追加の課題**:
- ffill / 5m rolling / アンカー補間 / 複数特徴量分解 の4方式で MTF展開方式が未確定（監査依頼予定）
- 学習データ3.7年（2021-04〜2024-12）で1M rolling windowの計算可否要確認

**戦略**: A（全投入）

**Layer担当**: Layer 1④（1w/1M追加・A-1と同時実施）

---

#### 軸 D-α: シグナル発火頻度（密度）

**定義**: per-dt-dayの発火件数（独立決定変数ではなく、他軸の従属変数として決まる）

**現状**: no_trade 86.2%（K96 LONG独占による構造的問題）

**重要教訓（L-117）**: 発火件数が少ないシグナルにフィルタをかけるとNET悪化。発火頻度単独の操作は禁止。

**戦略**: C（ML学習対象・他軸の結果として従属的に決まる）

**Layer担当**: Layer 1①/Layer 2（combo見直しの副産物として改善）

---

### III. ポジション設計（5軸）

---

#### 軸 A-6: add数 / 配分

**定義**: 同一Priority内の追加エントリー（add）回数とper-addのサイズ配分

**現状**: MAX_ADDSはPriority別固定値（cc_ml_design_spec §4）。ML学習対象外。

**設計変数**:
- MAX_ADDS: 1/2/3/4/5
- per-addサイズ: 等分/逓増/逓減/動的（予測強度依存）
- addトリガ（D-β-1統合）: 時間経過/含み損閾値/指標再発火/価格逆行幅

**戦略**: B（探索試行）+ C（動的係数はML学習対象）

**Layer担当**: Layer 2

---

#### 軸 A-7: ポジションサイジング / 配分

**定義**: 個別ポジションのBTCサイズとcombo別配分

**第二絶対規定（事前固定D）**: **合計 0.12 BTC 厳守・絶対不変**

**現状**: Phase 5 v3 = remaining/n_sim動的サイジング

**サイジング方式候補**:
一律 / 予測強度比例 / Kelly criterion / Risk parity / Volatility-targeting / cluster別固定 / 過去パフォーマンス重み付け

**既知問題（L-192）**: v2でレバレッジ計算ミスにより2.28 BTC計上（規定の19倍）事案。安全装置は絶対に触らない。

**戦略**: D（0.12 BTC上限）+ B（配分方式探索）+ C（動的係数はML学習）

**Layer担当**: Layer 2②

---

#### 軸 B-8: 同時保有数（cap）

**定義**: 同時に保有できるポジション数の上限

**現状**: 明示的cap設定なし。0.12 BTC + min_sizeの物理制約のみ。

**構造的問題**: K96 LONG 1件が0.12 BTC枠を独占 → 他combo発火不能 = no_trade 86.2%の根本原因

**cap設計候補**:
- 静的: cap=1/2/3/5/10/∞
- 動的: ボラ依存/時間帯依存/予測強度依存
- FIFO（先着順）/ 質駆動（予測強度優先）

**A-4/A-7との連動**: K96系combo削除+サイジング方式変更でcap問題がどう変わるかを先に確認

**戦略**: B（探索試行）

**Layer担当**: Layer 1②（損combo切り捨てと連動）/ Layer 2（cap動的化）

---

#### 軸 D-β: 保有期間中の管理

**定義**: addトリガ条件・部分決済（scale-out）・per-add動的サイズ変化

**統合先**: Step 3の判定で3軸に分解・統合済
- D-β-1（addトリガ閾値）→ A-3に統合
- D-β-2（部分決済scale-out）→ A-2に統合
- D-β-3（per-add動的サイズ）→ A-7に統合

**戦略**: B+C

**Layer担当**: Layer 2

---

#### 軸 D-ζ: マルチサイド（LONG/SHORT同時保有）

**定義**: LONGとSHORTを同時保有できるか・hedge_modeの運用設計

**現状**: hedge_mode許可（D事前固定）。0.12 BTC上限内で両建て可能。

**課題**:
- LONG/SHORT同時保有時のcapカウント方法（B-8連動）
- 合計0.12 BTC上限のLONG/SHORT配分設計（A-7連動）
- Delta-neutral構成の可能性

**戦略**: D（許可ルール・固定）+ C（動的活用方式はML学習対象）

**Layer担当**: Layer 2/Layer 3

---

### IV. フィルタ（3軸）

---

#### 軸 D-γ: エントリー位置フィルタ

**定義**: location_prev（前bar時点での直近Nbar内レンジ位置）・高値圏Entry抑制

**現状**: 手動PriorityではlocationフィルタをLONG/SHORT共通で適用（≤0.9）。ML特徴量化は未対応（entry_risk_scoreの代替はあるが別物）。

**戦略**: B（探索試行）

**Layer担当**: Layer 2（A-3のB案後処理フィルタと連動）

---

#### 軸 D-δ: 時間帯・曜日フィルタ

**定義**: アジア/欧州/米国セッション・曜日・月初月末等の時間帯ベースフィルタ

**現状**: 未投入。WORKFLOW.md §設計思想 L230で「個別Priority最適化禁止」明文。統合フェーズのみ適用可。

**BTC/USDT特有論点**:
- Funding Rate計算時刻（8h毎）
- 米国先物オープン時のボラ変化
- 24/7/365市場（株式のセッション概念とは異なる）

**戦略**: B（探索試行）・ただしLayer 2統合フェーズ以降のみ

**Layer担当**: Layer 2統合フェーズ

---

#### 軸 D-ε: 市況フィルタ（regime / volatility state）

**定義**: 事前regime/volatility stateでそもそもEntryを出すか判定する事前フィルタ

**現状**: 未投入。regime研究は凍結中（WORKFLOW.md L140-144）。

**B-11との構造的差異**:
- D-ε: 事前判定（エントリー前に市況を判断）
- B-11: 事後分類（Entryシグナルをcluster分類）
→ 二段構成として併用可能

**戦略**: B（探索試行）・Layer 2以降のみ（凍結解除が必要）

**Layer担当**: Layer 2以降

---

### V. 学習設計（7軸）

---

#### 軸 B-9: 発火条件の組み合わせ深さ

**定義**: ML（決定木）が学習するAND条件の段数（複数指標の組み合わせ複雑さ）

**現状ハイパラ**:

| パラメータ | 現状値 | 意味 |
|----------|-------|------|
| num_leaves | 31（K12 LONGのみ15） | 1木あたり最大葉数 |
| max_depth | -1（無制限） | 木の深さ上限 |
| min_data_in_leaf | 100 | 1葉あたり最小データ数 |
| n_estimators | 5000（early stopping） | 木の本数 |

**既知教訓（L-189）**: ハイパラ単体調整の効果は限界がある。特徴量の質が先。

**戦略**: C（MLが自動最適化）

**Layer担当**: Layer 3（特徴量改善後にハイパラ最適化）

---

#### 軸 B-10: 学習アルゴリズム

**定義**: MLの予測モデルとして何を使うか

**現状**: LightGBM（GBDT）× 16ラベル独立回帰。他アルゴ未試行。

**候補カタログ**:
- Tree系: XGBoost / CatBoost / Random Forest
- Linear系: Ridge / Lasso / ElasticNet
- Neural Net: MLP / LSTM / Transformer
- 時系列特化: MiniROCKET（handoff §F候補）
- 強化学習: DQN / PPO / SAC（audit#16で評価過小指摘）
- ハイブリッド: ルールベース + ML アンサンブル

**audit#16指摘**: 強化学習が cc_ml_design_spec で過小評価されている可能性。実装回避バイアスに注意。

**戦略**: B（探索試行）

**Layer担当**: Layer 3（特徴量・クラスタリング安定後に試行）

---

#### 軸 B-11: クラスタリング手法

**定義**: Entryシグナルを性質ごとにグループ分けする手法

**現状**:
- StandardScaler + KMeans k=3
- 入力: 16次元予測値ベクトル（K×side×MFE/MAEの予測値）
- silhouette=0.510 / size_ratio=0.159

**構造的問題（cluster_profile発見）**:
- clusterが「ボラレベル」を分類している
- 「LONG/SHORT方向性」を分類していない
→ LONG/SHORTが同一clusterに混在 → Exit選定・サイジングの精度低下

**入力ベクトル代替案**:
- A案: 現状（16予測値のみ）
- B案: 16予測値 + LONG/SHORT差分特徴量追加（方向性を分類に含める）
- C案: 1432指標の一部も入力に追加

**手法カタログ**:
k-means / GMM / HMM / Hierarchical / DBSCAN / HDBSCAN / UMAP+HDBSCAN / Spectral / SOM

**戦略**: B（探索試行）

**Layer担当**: Layer 1（手法・入力見直し）/ Layer 2

---

#### 軸 B-12: 特徴量変換

**定義**: 生の指標値をML入力用に変換する処理

**現状（1432内で実施済の変換）**:
- _pct: パーセント変換
- _rank_50b: 直近50bar内ランク
- _streak: 連続本数
- _change: 変化量
- _slope: 傾き（一部）

**MTF展開方式（核心論点・監査依頼予定）**:
4方式が存在し未確定:
1. ffill（前回値で補完）
2. 5m rolling（5mbarで再計算）
3. アンカー補間（特定時点からの補間）
4. 複数特徴量分解（1つのTFを複数列に展開）

**未投入の変換（業界標準）**:
- Fractional Differentiation（Lopez de Prado推奨・定常性とmemoryのトレードオフ）
- Wavelet分解
- PCA

**戦略**: A（変換済特徴量は全投入）+ B（MTF展開方式の探索）

**Layer担当**: Layer 1④ + 監査経路

---

#### 軸 B-13: Entry ratio 閾値の決定方法

**定義**: MLが予測したMFE/MAE比（ratio）をEntry発火判定する閾値の決定方法

**現状**: rolling 365日 q90/q95/q99 加重採用（cc_ml_design_spec §1.6 案G）
- 採用経緯: 絶対閾値のdrift問題への対処（2026-05-15 改訂11）

**q-band構造**:
- q90-q95帯: エントリー許容（低品質）
- q95-q99帯: エントリー許容（中品質）
- q99以上: エントリー許容（高品質）

**構造的問題**:
- K24 LONG q99・K24 SHORT q99 が欠落
- K96 SHORT q95-q99 が test 0件

**決定方法候補**:
静的q値 / rolling N日 / cluster別独立 / 強化学習動的最適化 / Online adaptive

**戦略**: B（探索試行）+ C（dynamic閾値はML学習対象）

**Layer担当**: Layer 1①（欠落修正）/ Layer 3（動的閾値探索）

---

#### 軸 B-14: 学習データ範囲・サンプリング

**定義**: MLが学習するデータの期間・分割・サンプリング戦略

**現状（D固定）**:

| 期間 | 行数 | 用途 |
|------|------|------|
| 2021-04〜2024-12 | 394,753行 | train |
| 2025年 | 105,120行 | 仮test（valid） |
| 2026 Q1 | 25,823行 | 本test（§8違反防止・見るのみ） |

**§8違反防止**: 本test 2026 Q1の結果を見て学習を変える行為はL-183違反

**サンプリング候補**:
Walk-forward / Expanding window / Purged K-fold / Combinatorial Purged CV（Lopez de Prado CPCV）/ SMOTE

**戦略**: D（期間分割は固定）+ B（サンプリング戦略は探索）

**Layer担当**: Layer 3（Walk-forward等の発展的CV）

---

#### 軸 B-15: 目的関数 / 不確実性定量化

**定義**: MLが「何を最大化/最小化するように学習するか」+ 予測の信頼度をどう測るか

**現状**:
- train: RMSE最小化
- Phase 5評価: 月次NET $1,900以上

**構造的問題**: RMSEとNET（実際の収益）の乖離が大きい。RMSE最小化がNET最大化を保証しない。

**目的関数候補**:
MSE/RMSE / MAE / Huber / Quantile loss / Sharpe / Sortino / Calmar / Expectancy

**不確実性定量化候補（audit#16指摘・過小評価領域）**:
Calibration / Conformal prediction / 予測区間 / SHAP / Permutation importance

**合格ライン（D固定）**: 月次NET ≥ $1,900（全月クリア）

**戦略**: D（RMSE最小化は主目的として固定）+ B（補助指標・不確実性は探索）

**Layer担当**: Layer 3

---

### VI. 執行設計（2軸）

---

#### 軸 D-η: 手数料モデル

**定義**: 取引コスト構造（手数料・スリッページ・Funding Rate）

**確定値（D固定・exchange_spec.mdより）**:
- Maker: 0.014%
- Taker: 0.042%
- Funding Rate: 8h毎0.01%（Phase 5-eで控除済）
- スリッページ: Maker指値前提で未モデル化

**戦略**: D（固定）

**Layer担当**: Phase 7（本番運用後の実績検証）

---

#### 軸 D-θ: 発注タイプ

**定義**: 注文の種類（成行/指値/Stop/OCO等）

**現状**: Maker指値前提（D固定）。不約定リスクは未モデル化。

**Maker指値の不約定リスク**: D-η §D-η.5の継続論点。急変時に指値が約定しない可能性。

**戦略**: D（Maker指値は固定）+ B（Layer 3で執行最適化探索）

**Layer担当**: Phase 7 Bot統合 / Layer 3

---

## Layer別 作業マップ

### Layer 1（基盤整備）— 現在進行中

| 優先度 | 作業 | 関連軸 |
|--------|------|--------|
| ① | trailing 0件採用の原因究明 + 手動Priority Exit 8種類以上をML追加 | A-2 |
| ① | B-13 q-band欠落（K24 q99 / K96 SHORT）の修正 | B-13, D-α |
| ② | K96 LONG no_trade 86.2%解消（K96 combo見直し or cap設計） | A-4, B-8 |
| ③ | K窓の見直し（K=6/144/288追加候補検証） | A-4 |
| ④ | 未学習8件+発振系3種+1w/1M MTF追加 + Phase 0〜5再実行 | A-1, A-5, B-12 |

### Layer 2（統合フェーズ）— Layer 1完了後

| 作業 | 関連軸 |
|------|--------|
| add設計の最適化（MAX_ADDS・addトリガ・per-addサイズ） | A-6, D-β |
| サイジング方式の探索（0.12 BTC上限内） | A-7 |
| cap動的化（K96解消後のcap再設計） | B-8 |
| 時間帯・曜日フィルタの統合 | D-δ |
| regime凍結解除判断 + 市況フィルタ統合 | D-ε |
| マルチサイドの動的活用設計 | D-ζ |
| Exit候補の拡張（第2弾3種・業界カタログ） | A-2 |
| クラスタリング手法・入力ベクトル見直し | B-11 |

### Layer 3（高度最適化）— Layer 2完了後

| 作業 | 関連軸 |
|------|--------|
| 学習アルゴリズムの多様化（XGBoost/NN/MiniROCKET等） | B-10 |
| ハイパラ最適化（num_leaves等） | B-9 |
| Walk-forward / CPCV等の発展的CV | B-14 |
| Entry ratio閾値の動的化（cluster別・強化学習） | B-13 |
| 目的関数の改善（RMSE→Sharpe等の補助指標） | B-15 |
| 不確実性定量化（Calibration/SHAP） | B-15 |
| 執行最適化（不約定リスクモデル化） | D-θ |

---

## 既知問題・制約 一覧

| 問題 | 影響 | 関連軸 | 解消方針 |
|------|------|--------|--------|
| **no_trade 86.2%** | K96 LONG q95-q99が0.12 BTC枠を独占し他combo発火不能 | A-4, B-8 | K96 combo削除 or cap設計変更（Layer 1②） |
| **trailing 0件採用** | 全19 comboでtrailing未選択・Exit多様性ゼロ | A-2 | 実装verify + パラメータ範囲拡大（Layer 1①） |
| **K24/K96 q-band欠落** | K24 LONG/SHORT q99・K96 SHORT q95-q99がtest 0件 | B-13 | q-band生成ロジックの修正（Layer 1①） |
| **cluster方向性未分類** | clusterがボラレベルのみ分類・LONG/SHORT混在 | B-11 | 入力ベクトルにLONG/SHORT差分追加（Layer 1） |
| **RMSE-NET乖離** | RMSE最小化がNET最大化を保証しない | B-15 | 補助指標追加（Layer 3） |
| **1w/1M未投入** | 長期トレンド情報が特徴量に含まれない | A-1, A-5 | Phase 0から再実行（Layer 1④） |
| **未学習8指標** | RCI系/RSI21/Stoch D等が1432に不在 | A-1 | 追加後Phase 0再実行（Layer 1④） |
| **手動Priority Exit未ML化** | 11種類以上のExitロジックがML学習対象外 | A-2 | Phase 4-b候補に追加（Layer 1①） |

---

## 軸間依存関係

```
A-4（K窓）→ B-8（cap設計）→ D-α（発火頻度）
              ↓
A-7（サイジング）← D-ζ（マルチサイド）

A-1（Entry指標）→ B-12（特徴量変換）→ B-9（組み合わせ深さ）
                                      → B-11（クラスタリング入力）

B-13（Entry ratio閾値）→ D-α（発火頻度）
                        → A-2（Exit選定タイミング）

B-11（クラスタリング）→ A-2（Phase 4-b Exit選定）
                       → A-7（サイジング・cluster別）

B-14（学習データ）→ B-13（rolling q値計算ベース）

D-ε（regime）→ B-11（事前判定 vs 事後分類の二段構成）

A-2（Exit）─ D-β-2（部分決済）統合済
A-3（閾値）─ D-β-1（addトリガ閾値）統合済
A-7（サイジング）─ D-β-3（per-add動的サイズ）統合済
```

---

## 絶対制約（変更禁止）

1. **第二絶対規定**: 合計ポジション上限 0.12 BTC 厳守（A-7）
2. **§8違反禁止**: 本test 2026 Q1を見て学習パラメータを変える行為禁止（B-14）
3. **1m足回帰禁止**: CLAUDE.md §⛔ 提案禁止リスト（A-5）
4. **個別Priority最適化禁止**: 時間帯フィルタは統合フェーズ限定（D-δ・WORKFLOW.md L230）
5. **安全装置変更禁止**: leverage=25xのリスク管理コード（A-7・feedback_rules L-5）
