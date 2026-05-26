# ML pipeline 暫定ベース案 v2 (= 2026-05-27 セッション議論決着反映)

最終更新: 2026-05-27
位置付け: 2026-05-27 セッションで 6 工程 → 8 工程に拡張・各工程の決着事項を反映。次フェーズは実装着手。

出典: 2026-05-26 セッションでまこさん提示の 6 工程ドラフト (= v1) を、2026-05-27 セッション議論で詳細化 + Web Claude 指摘 3 件 (= Exit 重点 / cluster 組み込み / regime 再検討) を反映。

---

## 1. 8 工程フロー (= 2026-05-27 セッション決着・1 字 1 句一致義務)

```
[1] 特徴量計算層 (= 共通基盤)
    - 既存 Phase 0 v3.1 の 1462 指標 + MTF 8 TF (= 5m / 15m / 30m / 1h / 2h / 4h / 1d / 1w)
    - 追加なし (= 素材は揃っている)
       ↓
[1.5] regime 判定 (= 新規追加・独立工程化)
    - 3 つの判定器を ensemble で束ねる:
      * HMM 判定器 (= 既存・前セッション保留中・再調整)
      * 固定ルール判定器 (= ATR + BB ミドル傾き + ADX の閾値で「上昇 / 下降 / 横ばい」判定)
      * k-means 判定器 (= データから自然なグループ自動分け)
    - ensemble 機構 = 平均化 or 多数決
    - 出力: 「上昇 / 下降 / 横ばい」の判定 + 確信度
    - 役割: 後段の Entry ML / cluster / Sizing / Exit の入力に渡す
    - 注意: フィルタとして強制適用しない (= 低精度時の機会損失リスク回避)
       ↓
[2] Entry ML (= 件数確保最優先)
    - LightGBM Multi-output
    - 学習対象: Phase 0 v3.1 既存の 56 ラベル並列学習
      * 揺れ幅系 28 個 (= MFE/MAE pct × LONG/SHORT × K=1〜7)
      * 決着系 28 個 (= Triple Barrier 3 クラス + meta_label × LONG/SHORT × K=1〜7)
    - 出力: entry_score / direction (LONG/SHORT/NONE) / confidence
    - threshold 緩め (= 月 275+ 件確保)・即死リスク (危険度>0.9) のみ reject
       ↓
[2.5] cluster 分類 (= 新規追加・独立工程化)
    - k-means で Entry の状況を 3-5 グループに自動分け
    - 入力: Entry ML 出力 (= 予測値 56 個 + direction + confidence) + 特徴量
    - 出力: cluster_id (= 0, 1, 2, ...)
    - 役割: グループ別に Exit / Sizing を変える (= 戦略並立 1.5× レバー狙い)
       ↓
[3] Position Sizing ML + add (= 連鎖入力)
    - 入力: 特徴量 + Entry ML 出力 + cluster ID + regime 判定
    - 学習目標: Kelly 基準 (= 信頼度 × 過去成績 × ボラ で最適サイズ計算)
    - 出力: recommended_size (= 0.005-0.05 BTC 動的)
    - cap = 5 (= 同時保有数上限・固定・1 ポジ最大 0.024 BTC)
    - 0.12 BTC 合計上限内で危険度別配分 (= sum ≤ 0.12 BTC enforcement)
    - add: cluster 別固定ルール (= 暫定 C・バックテストで調整):
      * スキャル cluster → add なし (= MAX_ADDS=1)
      * 平均建値 cluster → add あり (= MAX_ADDS=5)
       ↓
[4] Exit 多層 ML (= 旧 Priority 12 種類継承・階層構造)
    - 入力: ポジ情報 + Entry 時特徴量 + 現在特徴量 + 経過時間 + 含み損益 + cluster ID + regime 判定
    - 学習対象: 工程 [2] と 56 ラベル共有 + 各時点の PnL ラベル追加
    - 階層構造 (= 3 段階):
      * 1. 初期保護: SL_PCT / TIME_EXIT_DOWN
      * 2. 損益分岐点保護: MFE_GATE / PROFIT_LOCK
      * 3. トレーリング (= 利益最大化): TP_PCT / TRAIL_RATIO / MFE_STALE / TP_BB_RATIO / TP_FEE_FLOOR / STOCH_REVERSE / RSI_REVERSE / TIME_EXIT
    - cluster 別優先順位: cluster ごとに各段階の重みを変える
    - 出力 (= 同時 12 種類): 各 Exit の発動シグナル
    - 1 つでも閾値超えたら Exit 発動 (= 過剰 Exit リスクは階層構造 + cluster 別優先順位で抑制)
       ↓
[5] Risk 管理 (= 固定ルール・ML 不使用)
    - ATR / volume / spread が急変したら全停止
    - 0.12 BTC 上限の物理的強制 (= sum(active_position_btc) ≤ 0.12 を全エントリー時に verify)
       ↓
[6] 運用監視 (= drift 検知 + 段階的対応)
    - 監視対象 3 つ:
      * AI の予測精度 (= 過去比で当たり率の変化)
      * 入力データの分布 (= 相場特性の変化)
      * 実運用の成績 (= 月次 NET / 勝率)
    - 検知時の段階的対応:
      * 軽微: alert を出して人間判断
      * 中度: サイズを自動縮小
      * 重度: 自動停止
    - 詳細実装は Phase 7 (= Bot 統合) で詰める
```

---

## 2. 目標達成試算

### 2.1 件数 × 単価ベース (= v1 維持)

- 月 $1,900 / 30 日 = 1 日 $63 必要
- 平均ポジサイズ 0.04 BTC × BTC $100,000 × TP_PCT 0.20% = グロス $8
- 手数料 0.014% maker × 2 = 0.028% → fee $1.1
- 1 件 NET ≒ $6.9
- 月 $1,900 / $6.9 ≒ 月 275 件 = 1 日 9 件 (= 1 時間 0.4 件)

### 2.2 業界レバー寄与ベース (= 2026-05-27 追加・KB §2.6 ケース B 中央値)

| レバー | 寄与 | 担当工程 |
|---|---|---|
| Entry 改善 | 1.4× | [2] Entry ML |
| Exit 最適化 | 1.7× | [4] Exit 多層 ML |
| 戦略並立 | 1.5× | [2.5] cluster 分類 |
| regime filter | 1.3× | [1.5] regime ensemble |
| Position sizing | 1.2× | [3] Sizing ML |

**合計**: 1.4 × 1.7 × 1.5 × 1.3 × 1.2 = **5.57×** → 月 $2,060 (= 目標 $1,900 + 8% マージン)

---

## 3. 設計思想

### 3.1 全体方向性 (= v1 維持)

「**多めにエントリー + Exit で利益最大化**」:
- [2] Entry ML threshold 緩め = 多めにエントリー
- [4] Exit 多層 ML 12 種類 = Exit で利益最大化
- [3] Position Sizing で危険度別配分 = 危険な Entry は小サイズで損失抑制

### 3.2 Entry / Exit の密接関係 (= v1 維持)

- Entry が「TP まで届く確率が高い状況」をピンポイント検出 → Exit シンプル 3 ロジック (TP/SL/TIME_EXIT) で成立
- Entry が雑 (= TP 確率半々) → Exit 側で複雑なロジックで救う必要
- = **Entry の品質 ↔ Exit の複雑さ** のトレードオフ・Entry/Exit はセット設計

### 3.3 マルチタスク学習との関係 (= v1 維持 + v2 で具体化)

- まこさん理想: **マルチタスク学習** (= Entry / Sizing / Exit を 1 モデルで同時学習・損失関数統合)
- 現実的な落としどころ: **連鎖学習** = 各段独立モデル・前段出力を後段入力に取る
- v2 で工程ごとに「連鎖入力」を明示 (= [1.5] → [2] → [2.5] → [3] → [4] の連鎖)

### 3.4 regime / cluster の独立工程化根拠 (= 2026-05-27 新規追加)

**[1.5] regime を独立工程化した理由**:
- 過去 regime ML 学習が単一手法で失敗 (= v14 56% / stage3 33% / HMM「精度微妙」)
- 業界主流 = 複数判定器 ensemble (= RegimeFolio 137% return / Sharpe 1.17 実証)
- 単一手法の精度限界を多角的判定で補強

**[2.5] cluster を独立工程化した理由**:
- 戦略並立 1.5× レバーを取るためには cluster 識別が不可避
- 旧 Priority v9 が手動で 9 個に分けていた発想を ML で自動化
- グループ別 Exit / Sizing を出すための前提

### 3.5 ラベル設計の反省 (= 2026-05-27 新規追加)

- 過去 Phase 1 失敗の根本原因 = 14 ラベル (= LONG_MFE/MAE × K=7) しか学習対象にしてなかった → AI が「揺れ幅予測」に逃げた
- v2 修正: **56 ラベル全部並列学習** (= 揺れ幅 28 + 決着 28) で「揺れ幅予測逃げ」を構造的に防ぐ

### 3.6 危険度の指標 (= 2026-05-27 新規追加)

工程 [3] Position Sizing で使う「危険度」は **Kelly 基準** (= 信頼度 × 過去成績 × ボラ) を業界主流として採用。

### 3.7 Exit 階層構造の根拠 (= 2026-05-27 新規追加)

過剰 Exit リスク (= 12 種類のうち 1 つでも誤判定すると Exit) を抑制するため、業界主流の階層構造 (= 多段 Exit Stack) を採用:
- 1. 初期保護 → 2. 損益分岐点保護 → 3. トレーリング の段階適用
- cluster 別に各段階の重みを変えることで「スキャル / 平均建値」の戦略差を吸収

---

## 4. 決着事項一覧 (= 2026-05-27 セッション・v1 §4 議論未確定事項を全て決着)

| 工程 | 学習目標 / 機構 | 入力 | 出力 | 制約 |
|---|---|---|---|---|
| [1] 特徴量計算層 | 既存 Phase 0 v3.1 維持 | 5m bar OHLCV | 1462 指標 + MTF 8 TF | USD 絶対値 64 列 blacklist |
| [1.5] regime 判定 | 複数判定器 ensemble | 1462 指標 | regime ラベル + 確信度 | フィルタ強制適用しない |
| [2] Entry ML | LightGBM Multi-output | 1462 指標 + regime 出力 | direction + confidence + 56 ラベル予測 | threshold 緩め (= 月 275+ 件) |
| [2.5] cluster 分類 | k-means | Entry ML 出力 + 特徴量 | cluster_id (= 0-4) | 教師なし |
| [3] Sizing + add | Kelly 基準 | 全前段出力 | recommended_size + add 上限 | cap=5・0.12 BTC 合計上限 |
| [4] Exit 多層 ML | 階層構造 (= 3 段階) | ポジ情報 + 現在特徴量 + 経過時間 + cluster + regime | 12 種類 Exit シグナル | cluster 別優先順位 |
| [5] Risk 管理 | 固定ルール | 市況情報 | 全停止シグナル | 0.12 BTC 上限強制 |
| [6] 運用監視 | drift 検知 | 予測精度 + 入力分布 + 実成績 | 段階的対応 alert | Phase 7 で詳細実装 |

---

## 5. 関連メモリ・参照ファイル

### 必読 (= Layer 1)

- [[feedback_cat_v9_no_modification]] — cat_v9 改造禁止 (= 構造的継承 OK)
- [[feedback_baseup_before_design_discussion]] — 設計議論前 KB Read + WebSearch 必須
- [[feedback_priority_starting_line_only]] — 手動 Priority はスタートライン参照のみ
- [[feedback_cc_low_perspective_narrow_view]] — 視点低い・視野狭い癖矯正
- [[feedback_trade_ml_knowledge_gap]] — トレード ML 業界標準理解浅・WebSearch + 教科書引用必須

### 参照ファイル

- `priority_v9_trade_logic_analysis.md` v2 (= 旧 Priority 構造分析)
- `industry_benchmark_knowledge_base.md` (= 業界相場・5 レバー定量根拠)
- `technical_analysis_knowledge_base.md` (= テクニカル指標辞典 + 閾値設計論)
- `cc_entry_logic_self_study.md` v6 (= 業界実装カタログ・各工程の業界実装パターン部分のみ抽出)

### 業界実証出典 (= 2026-05-27 セッション WebSearch)

- [RegimeNAS arxiv 2508.11338](https://arxiv.org/pdf/2508.11338) (= regime tight integration)
- [RegimeFolio arxiv 2510.14986](https://arxiv.org/pdf/2510.14986) (= regime ensemble 137% return)
- [Quantinsti HMM + Random Forest Specialist Models](https://blog.quantinsti.com/regime-adaptive-trading-python/)
- [Akash Kumar HMM+LSTM Crypto Regime Classifier Medium](https://medium.com/@akashdevbuilds/how-i-built-a-market-regime-classifier-for-crypto-using-hmms-and-lstms-8151047582f7)
- [Springer Triple Barrier 2025](https://link.springer.com/article/10.1186/s40854-025-00866-w)
- [ScienceDirect Crypto DRL with LSTM XGBoost 2025](https://www.sciencedirect.com/science/article/abs/pii/S1568494625003400)
- [QuantStrategy ML Exit Optimization](https://quantstrategy.io/blog/machine-learning-for-exit-optimization-predicting-the-best/)

---

## 6. 工程別詳細設計書 (= 2026-05-27 セッション中盤以降決着事項を都度追記)

> 各工程の決着事項を **都度追記**。後でまとめて書かない (= 記入ミス防止・まこさん指示 2026-05-27)。

### 6.0 工程 [1] 特徴量計算層 詳細設計

#### 6.0.1 ラベル決着

##### 過去 Phase 1 失敗の正確な原因
- 過去は **14 ラベル** (= LONG_MFE/MAE × K=1〜7) しか学習対象にしてなかった
- AI に「揺れ幅」しか答えさせなかったので、**揺れ幅予測に逃げた**
- = 予測種類が少なすぎた + 種類が一方向に偏っていた

##### 修正方針 (= 56 ラベル並列学習)
- Phase 0 v3.1 で **既に生成済みの 56 ラベル全部** を学習対象に並列追加する:
  - 揺れ幅系 28 個 (= エントリー後の最大変動幅)
  - 決着系 28 個 (= 利確 / 損切り / 時間切れ の 3 択 + 利確到達 yes/no)
- = AI が「揺れ幅 + 決着 + 到達確率」の **複数視点を同時学習** する形になる
- 揺れ幅予測逃げを **構造的に防ぐ**

##### cat-bitget 制約逆算
- 1 件 NET $6.9 達成 = 「利確到達するか (= 決着系)」+「どれだけ伸びるか (= 揺れ幅系・動的 TP 設計用)」両方が必要
- 並列予測でこの両方をカバー

##### ML 知見補足
- マルチタスク学習 (= 複数予測を同時学習する仕組み) = 単一予測より「汎化性能 (= 未知データへの強さ)」が上がる業界標準
- §3.3 でもまこさん理想として記録済み

##### 追加実装コスト
- なし (= 56 ラベル既に生成済み・[labels_mfe_mae_pct_train_2021_2024.parquet](../../results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet))

#### 6.0.2 56 ラベル詳細内訳

##### 系統別分類 (= 2 系統 × 4 サブカテゴリ × 7 ホライズン = 56)

| 系統 | サブカテゴリ | 方向 | 個数 |
|---|---|---|---|
| 揺れ幅系 | MFE pct (= エントリー後の最大有利幅・%) | LONG × 7 / SHORT × 7 | 14 |
| 揺れ幅系 | MAE pct (= エントリー後の最大不利幅・%) | LONG × 7 / SHORT × 7 | 14 |
| 決着系 | Triple Barrier 3 クラス (= TP / SL / 時間切れ) | LONG × 7 / SHORT × 7 | 14 |
| 決着系 | meta_label (= TP 先到達 yes/no) | LONG × 7 / SHORT × 7 | 14 |
| **合計** | | | **56** |

##### K の意味 (= 予測ホライズン・5 分足の本数)

| K | 時間 | 戦略タイプ目安 |
|---|---|---|
| 6 | 30 分 | スキャル超短期 |
| 12 | 1 時間 | スキャル |
| 24 | 2 時間 | 短期 |
| 48 | 4 時間 | 中期 |
| 96 | 8 時間 | 中期 |
| 144 | 12 時間 | 中長期 |
| 288 | 24 時間 | 長期 |

##### Triple Barrier の TP/SL 壁の閾値
- TP 壁 = エントリー価格 × (1 + ATR (= 平均値幅) の 2.0 倍)
- SL 壁 = エントリー価格 × (1 - ATR の 1.5 倍)
- = **現在の値動きの大きさに連動した動的閾値**

##### 学習対象 K 範囲 (= 決着済・データ駆動判定)
- **全 7 ホライズン使う** (= §1 [2] で確定済・K=1〜7 全部並列学習・56 ラベル全部使う)
- **判定方針 = データ駆動**:
  - 業界一般論として「関連性低いタスクを並列学習すると negative transfer (= 学習ノイズ) のリスクあり」は存在するが、cat-bitget 5 分足取引で K=288 が実際にノイズになるかは業界実証なし (= WebSearch で確定情報出ず)
  - 事前に「絞る/全部使う」を決め打たず、**1 回学習させて feature_importance / target importance** (= モデルが各ホライズンをどれくらい予測に使ってるか) で客観的に verify
  - 寄与してれば残す・寄与してなければ次回除外
- **運用時考慮事項**: ベース案 §2 で「月 275 件・1 取引 2-3 時間想定」になっている。一方、K=144 / 288 (= 12-24h 保有) は長期戦略向けで、ベース案戦略と整合しない可能性 → **運用時に [2] Entry ML の出力閾値で短期 K の優先度を上げる対応** で吸収 (= 学習対象から外す決着ではない)

---

### 6.1 工程 [1.5] regime 判定 詳細設計

#### 6.1.1 評価方法 (= 4 段階)

| Stage | タイミング | 内容 | 性質 |
|---|---|---|---|
| **Stage 1** 内部スコア | [1.5] 完成直後 | log-likelihood (HMM 用) / BIC (HMM 用) / silhouette score (k-means 用) / **Brier score + reliability diagram + ECE** (= Expected Calibration Error・ensemble 全体評価・キャリブレーション品質) / **3 判定器の予測誤差 pairwise Pearson 相関** (= 相関 < 0.5 で ensemble 効果あり / > 0.7 で判定器選び直し・KB §2.3 Square Root Rule 前提 verify) | 統計 ([1.5] 単独) |
| **Stage 2** 視認 + 統計検定 | [1.5] 完成直後 | (a) まこさん月単位視認 (= [feedback_regime_visual_check](../../../../../.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_regime_visual_check.md) 整合・最低 10 回調整) + (b) 各状態の収益性検定 (= 上昇 regime の平均 return が統計的に正・下降が負・レンジは vol 低) + (c) 既存特徴量との相関 (= regime が新情報を持つか確認) | 統計 ([1.5] 単独) |
| **Stage 3** PnL 早期判定 | **[4] Exit 多層 ML 完成後** | **2 段階比較**: (a) **v15 HMM 単独あり vs なし** NET 比率 + (b) **ensemble (= v15 + 固定 + k-means) あり vs なし** NET 比率・ensemble の純増分 = (b) / (a) で評価 (= base line 明確化・CP1 監査 M1) | PnL ([1.5]+[2]+[2.5]+[3]+[4] 部分パイプライン) |
| **Stage 4** 最終 PnL | 8 工程合算後 | Phase 5 Replay 全工程通しで最終 verify | PnL (全パイプライン) |

##### Stage 3 合格基準 (= **ensemble の純増分** = (b) / (a) = ensemble NET 比率 ÷ v15 単独 NET 比率)
- 1.3 倍以上 → ◎ 狙い通り (= 業界中央値・§2.2 [1.5] 担当値)
- 1.1〜1.3 倍 → ○ ぎりぎり合格 (= 業界相場下限・[industry_benchmark §2.4](industry_benchmark_knowledge_base.md))
- 1.0〜1.1 倍 → ✗ 不合格・ensemble 設計やり直し
- 1.0 倍以下 → ✗ ensemble 使わない判定 (= v15 HMM 単独に戻す・設計から外す)
- **base line 明確化**: 「v15 単独で既に何倍出ているか」を (a) で実測 → ensemble 追加の純増分が (b)/(a) で見える

##### 評価順序
- [1.5] 完成直後 = Stage 1 + Stage 2 (= 統計判定・まこさん視認 OK までやる)
- [4] Exit 完成後 = Stage 3 (= 早期 PnL 判定・regime 寄与不足なら [1.5] 設計やり直し)
- 8 工程完成後 = Stage 4 (= 最終 verify)

##### 設計判断の根拠
- [1.5] 単独で PnL 評価は構造的に不可能 (= 戦略ないと NET が出ない・cat_v9 改造禁止 + フィルタとして強制適用しない決着で他経路なし)
- → Stage 3 は最短で [4] Exit 完成後の部分パイプラインで早期判定 (= 8 工程合算を待たない)
- 業界実証 ([industry_benchmark §2.4](industry_benchmark_knowledge_base.md)) でも「シンプルなベース戦略 + regime」で評価が standard

#### 6.1.2 HMM 単体の再調整方針

##### v15 HMM (= 前セッション保留中) 実態 verify (= results/regime_step1/)

| 項目 | 値 | 評価 |
|---|---|---|
| 学習収束 | 5 fold 全 converge | ✅ |
| sanity check (= 妥当性チェック) | レンジ ADX 23.59 < 上昇/下降 ADX 32 → PASS | ✅ |
| 各状態の DI 差中央値 (= 上昇圧力指標) | 上昇 +13.9 / 下降 -15.7 / レンジ -0.94 | ✅ 妥当 |
| 状態分布 | レンジ 51% / 上昇 26% / 下降 23% | △ 均衡 |
| 平均切替間隔 (avg dwell time) | 7.89 時間 | △ 5 分取引にやや遅め |
| 正解一致率 (accuracy) | **教師なしのため計測不可** | -- |

##### 「精度微妙」の原因 (= 構造的)

教師なし HMM は正解ラベルがないので「内部スコア」と「人間視認」しか評価軸がない。内部スコア PASS なのに視認で「微妙」 = **教師なし単一手法の構造的限界**。業界実証 ([QuantStart QSTrader](https://www.quantstart.com/articles/market-regime-detection-using-hidden-markov-models-in-qstrader/) / [industry_benchmark §2.4](industry_benchmark_knowledge_base.md)) でも「HMM 単独は OOS で lag 問題」「単一手法は精度天井あり」と確認済。

##### 再調整方針 (= 決着)

1. **HMM 単体は v15 をベースに大幅変更なし**:
   - 状態数 k=3 (= 上昇 / 下降 / レンジ) 維持
   - covariance_type=diag (= 過学習防止) 維持
   - MTF 6 時間軸 (= 5m / 15m / 30m / 1h / 4h / 1d) × 14 指標 = 84 次元入力 維持
   - 1 時間判定 + 連続 2 回ヒステリシス 維持
2. **大きな改善は ensemble で取りに行く** (= §3.4 決着と整合):
   - 固定ルール判定器 + k-means 判定器を追加
   - 3 つの判定を束ねて HMM 単独の弱点を補強
3. **HMM 単体の合格判定** = 内部スコア + sanity check PASS で **OK 扱い** (= Stage 1 通過)
4. **視認「微妙」は ensemble 後の Stage 2 で再評価** (= まこさん視認 OK までやる・最低 10 回調整)

#### 6.1.3 固定ルール判定器の閾値・判定構造

##### 業界 standard verify (= 本セッション 2026-05-27 WebSearch 3 回)

- **全部 AND は使わない** (= 厳しすぎて発火しない・トレンド転換にも追従しない) = 業界否定的
- **scoring + weighted vote (= 重み付き点数 + 多数決) が主流**:
  - 各指標が「上昇 / 下降 / 横ばい」のいずれかに重み付き点数を加算
  - 全指標の点数を合計
  - 最高点のカテゴリを採用
  - 点数差で **確信度** も同時出力

##### 出典 (= 5 件)
- [AIMS 2025 ensemble-HMM voting framework](https://www.aimspress.com/article/id/69045d2fba35de34708adb5d) (= hybrid voting classifier)
- [Macrosynergy 2025 Classifying market regimes](https://macrosynergy.com/research/classifying-market-regimes/)
- [Lopez de Prado AFML](https://github.com/emoen/Machine-Learning-for-Asset-Managers) (= serial / conditional / hybrid / parallel 結合)
- [Hudson & Thames MLFinLab Trend Scanning](https://hudsonthames.org/) (= max t-value 動的選択)
- [PyQuantLab Regime Filtered Trend Strategy](https://pyquantlab.com/article.php?file=Regime+Filtered+Trend+Strategy+A+Market-Adaptive+Trend-Following+System.html) (= scoring system で trending / ranging / volatile を weighted point で判定)

##### cat-bitget 適用: 6 指標 × scoring 構造

| 指標 | 上昇に加点する条件 | 下降に加点する条件 | 横ばいに加点する条件 | 重み |
|---|---|---|---|---|
| ADX(14) | ≥ 25 | ≥ 25 (= 強トレンド両方向) | < 20 | 1.0 |
| DI+/DI- | DI+ > DI- | DI- > DI+ | クロス付近 (= 差 < 1.0) | 1.0 |
| BB ミドル傾き | > 10 | < -10 | -10 〜 10 | 1.0 |
| 価格 vs MA (= SMA20/SMA50/EMA200) | 価格 > 全 MA | 価格 < 全 MA | MA 近い (= ±0.5%) | 1.0 |
| MTF 整合 (= 1h + 4h 判定一致) | 両足上昇一致 | 両足下降一致 | 不一致 | **1.5** (= 上位足重視) |
| 一目均衡表 | 価格 > 雲上限 | 価格 < 雲下限 | 雲内 | 1.0 |

##### 判定ロジック

1. 各指標が「上昇 / 下降 / 横ばい」に重み付きで加点
2. 上昇合計点 / 下降合計点 / 横ばい合計点 を計算
3. **最高点のカテゴリを採用**
4. 最高点が閾値 (= 暫定 3.0) 未満なら **「不明確」→ 直前判定維持** (= ヒステリシス)
5. 確信度 = (最高点 - 2 番目の点) / 最高点 × 100

##### ATR (= ボラ大きさ) は方向判定から外して別フラグ並列出力 (= 価格非依存化済・CP1 監査 C2)

- **ATR_pct (= ATR(14) / close × 100)** で価格非依存化 (= [false_positive §0-1 Prime Directive](../rules/false_positive_incident_policy.md) + L-179 同型予防 + [phase_compliance §-1 USD 絶対値 blacklist](../rules/phase_compliance_checklist.md) 整合・cat_v9 既存 atr14_pct 運用と整合)
- 閾値は **train_2021_2024 期間の atr14_pct の 25th / 75th percentile を data-driven で fold 別決定** (= 暫定数値の決め打ち回避・CP1 監査 P1 改善 12 整合)
- 高ボラ: atr14_pct ≥ 75th percentile
- 中ボラ: 25th ≤ atr14_pct < 75th
- 低ボラ: atr14_pct < 25th percentile
- 根拠: ATR は値動き幅指標で方向 (= 上か下か) を判別できないため、方向判定から外す。代わりに後段への並列情報として渡す
- **CP1 監査 C2 反映** (= 旧版「ATR(14) 絶対値 250/100」は train 期間 BTC $30k-$60k vs 本番 $100k-$150k で意味が変わる価格非依存性違反 → 撤廃済)

##### 時間軸 + ヒステリシス

- 判定間隔 = 1 時間ごと (= HMM と同じ)
- 連続 2 回同じ判定で切替 (= ヒステリシス・HMM と同じ)
- 入力指標の時間軸 = 1h ベース + 4h (= MTF 整合用)

##### 数値根拠

- ADX 25 / 20: 業界 standard ([KB §A.3.2](technical_analysis_knowledge_base.md))
- BB ミドル傾き ±10: cat_v9 経験値 (= P3/P4/P22/P23・[KB §A.5.5](technical_analysis_knowledge_base.md))
- BB width < 10% Squeeze: 業界 standard ([KB §A.5.3](technical_analysis_knowledge_base.md))
- ATR 250/100: cat_v9 経験値 (= P3/P21 等・[KB §A.4.5](technical_analysis_knowledge_base.md))
- MTF 重み 1.5: 上位足重視の業界実証 ([Multi-Timeframe Adaptive Regime](https://medium.com/@FMZQuant/multi-timeframe-adaptive-market-regime-quantitative-trading-strategy-1b16309ddabb))
- 不明確閾値 3.0: 6 指標 × 平均 0.5 点として暫定値 (= **実装後 verify 必要**)

##### ml_pipeline_baseline v2 §1 [1.5] 元決着からの差分 (5 ポイント修正)

1. **ATR を方向判定から外す** → ボラ別フラグへ (= 値動き幅は方向を判別できない)
2. **DI+/DI- を方向判定に追加** (= 上昇/下降の矢印情報)
3. **価格 vs MA を追加** (= 大局トレンド・SMA20/50/EMA200)
4. **MTF 整合を追加** (= 上位足重視・重み 1.5×)
5. **一目均衡表を追加** (= 雲との位置)

##### 設計判断の根拠

- 全部 AND ロジックは業界否定的 + 発火しなさすぎ → 採用しない
- scoring + weighted vote = 業界主流 + 確信度も同時に得られる
- HMM (= 84 次元統計判定) との差別化 = 6 指標明示的ルール + 解釈性高い

#### 6.1.4 k-means 判定器の設計

##### 業界 standard verify (= 本セッション 2026-05-27 WebSearch 3 回)

- 入力特徴量 = **log returns + rolling volatility が default** (= 2-4 特徴量・シンプル)
- クラスタ数 = financial regime で **k=3 が default** (= bullish / bearish / sideways)
- 評価 = elbow method + silhouette score
- HMM/GMM/k-means **統合 ensemble が業界 standard**

##### 出典
- [JDMDC k-means + HMM Bitcoin 2025](https://jdmdc.com/index.php/JDMDC/article/view/57) = ハイブリッドが単独より高 log likelihood + 低 BIC
- [Borst Detecting Market Regimes K-Means Medium](https://datadave1.medium.com/detecting-market-regimes-k-means-57a5c55e17d9)
- [LSEG 2023 AI framework](https://developers.lseg.com/en/article-catalog/article/market-regime-detection) = HMM + GMM + k-means 統合
- [Built In Elbow Method](https://builtin.com/data-science/elbow-method) + [ML Mastery Silhouette](https://machinelearningmastery.com/k-means-cluster-evaluation-with-silhouette-analysis/)

##### cat-bitget 適用設計

| 項目 | 設計 | 根拠 |
|---|---|---|
| 入力特徴量 | 4 つ: log_returns_1h / rolling_volatility(20) / close_vs_sma20_pct__1h / adx14_1h | 業界 default 2-4 特徴量 + HMM の 84 次元と差別化 (= シンプル + 解釈性) |
| クラスタ数 | **k ∈ {2, 3, 4, 5} で elbow method + silhouette score を fold 別評価し最頻 k を採用** (= data-driven 判定・[step1_regime_design §2.6](step1_regime_design.md) 整合・CP1 監査 m2) | 事前決め打ち回避・business default の k=3 が最頻候補だが data で確認 |
| 学習データ | train_2021_2024 + Walk-Forward Purged K-Fold 5 fold | HMM と同じ |
| 前処理 | RobustScaler + fold 毎 fit (= leak 防止) | HMM と同じ |
| ラベル付け | cluster ごとの統計値 (= return / ADX / DI 差) で post-hoc マッピング | HMM と同じ手法 |
| 判定間隔 | 1 時間ごと | HMM と同じ |
| ヒステリシス | 連続 2 回切替 | HMM と同じ |
| 評価 | silhouette score (= cluster 品質) + elbow plot (= k=3 妥当性 verify) | 業界 standard |

##### 3 判定器の役割分担 (= ensemble 設計上)

| 判定器 | 視点 | 強み |
|---|---|---|
| HMM | 84 次元統計判定 + 時系列依存 | 多角性・確率的 |
| k-means | 4 特徴量シンプル判定 + 時系列依存なし | 簡潔性・解釈性 |
| 固定ルール | 6 指標明示的ルール | 明示性・人間検証可 |

3 つで補完関係 = 違う視点で同じ判定 → ensemble で精度向上を狙う。

#### 6.1.5 ensemble 機構の設計

##### 業界 standard verify (= 本セッション 2026-05-27 WebSearch 3 回)

業界の投票方式:
- **Hard voting (= 多数決)** = 各モデルがクラス予測 → 最多のクラス採用 (= 確信度なし・シンプル)
- **Soft voting (= 確率平均)** = 各モデルの確率を平均化 → 最高確率採用 (= **業界推奨**)
- **Weighted voting** = 重み付きで重要度差をつける (= 信頼度や historical performance ベース)

業界結論 = 「キャリブレーション済みモデルなら **soft voting がほぼ常に好まれる**」 (= 各モデルの確信度を活かせる)

##### 出典
- [AIMS 2025 ensemble-HMM voting](https://www.aimspress.com/article/id/69045d2fba35de34708adb5d) (= hybrid voting・Sharpe 1.68 / drawdown 削減 / false signal 削減)
- [Voting Ensemble Hard vs Soft (mcpanalytics)](https://mcpanalytics.ai/articles/voting-ensemble-practical-guide-for-data-driven-decisions)
- [Hudson & Thames Pairs Trading Markov Regime Switching](https://hudsonthames.org/pairs-trading-with-markov-regime-switching-model/) (= ensemble は regime + 非線形データで特に効果)
- [Weighted Majority Rule (Raschka)](https://sebastianraschka.com/Articles/2014_ensemble_classifier.html)

##### cat-bitget 適用設計 = soft voting + 重み付き平均

| 項目 | 設計 |
|---|---|
| 投票方式 | soft voting (= 確率平均) |
| 重み (= CP1 監査 M2 反映) | **Walk-Forward Purged K-Fold 5 fold + GridSearchCV で初期重み決定** (= 探索空間 各判定器重み ∈ {0.5, 1.0, 1.5, 2.0} の grid 4³=64 通り + 等重み (1.0, 1.0, 1.0))・scikit-learn VotingClassifier + aimspress 2025 hybrid voting 実装と整合・等重み決め打ち回避 |
| 各判定器の確率変換 (= CP1 監査 C1 反映・キャリブレーション必須) | **全判定器に isotonic regression キャリブレーションを fold 別適用** (= scikit-learn calibration 業界 standard・soft voting 前提条件 verify): HMM `predict_proba` 出力 → isotonic で再キャリブレーション / 固定ルール scoring 点数比 → isotonic で再キャリブレーション / k-means cluster 距離 → **Gaussian kernel `exp(-d²/2σ²)` で確率化** → isotonic で再キャリブレーション (= 旧版 softmax 直接適用は撤廃) |
| 最終判定 | 平均後の最高確率カテゴリを採用 |
| 確信度 | 最高確率 - 2 番目確率 |
| 不明確時 | 最高確率が閾値 (= 暫定 0.4) 未満なら「不明確」→ 直前判定維持 (= ヒステリシス) |
| 判定間隔 | 1 時間ごと (= HMM と同じ) |
| ヒステリシス | 連続 2 回切替 (= HMM と同じ) |

##### 例 (= イメージ)

- HMM: 上昇 60% / 下降 20% / 横ばい 20%
- 固定ルール: 上昇 50% / 下降 30% / 横ばい 20%
- k-means: 上昇 70% / 下降 10% / 横ばい 20%
- → 重み付き平均 (= 等重み): 上昇 60% / 下降 20% / 横ばい 20%
- → 最終判定 = **上昇** / 確信度 = 60% - 20% = **40%**

##### 設計判断の根拠

- 業界推奨 = soft voting (= キャリブレーション済みモデルなら soft が hard より精度高い)
- 初期等重みの根拠 = 3 判定器の優劣を事前に決め打たない + Walk-Forward で当たり率を見て最適化する経路
- 不明確閾値 0.4 = 6 指標 scoring の閾値 3.0 と整合・実装後 verify 必要

#### 6.1.6 出力仕様

##### 業界 standard verify (= 本セッション 2026-05-27 WebSearch 3 回)

- 確率分布 + ラベル + 確信度 を **両方併用** が standard
- 後段への接続 = one-hot encoded + 確率値 併用
- 1h 判定 → 5m bar に **forward fill** (= 前の値で空白を埋める処理) で展開

##### 出典
- [GitHub akash-kumar5 CryptoMarket Regime Classifier](https://github.com/akash-kumar5/CryptoMarket_Regime_Classifier) (= HMM + LSTM・downstream strategy/sizing/risk management で使う実装例)
- [Live-Market-Regime-Classifier](https://github.com/akash-kumar5/Live-Market-Regime-Classifier/blob/main/README.md) (= merge_asof で異なる時間軸を統合)
- [Regime-Aware LightGBM MDPI 2025](https://www.mdpi.com/2079-9292/15/6/1334) (= rolling HMM regime を LightGBM に投入実証)
- [Calibration of probabilities tree-based models](https://gdmarmerola.github.io/probability-calibration/)

##### 出力列 6 種 (= 既存 parquet に追記)

| 列名 | 型 | 値域 | 役割 |
|---|---|---|---|
| `regime_label` | category | "uptrend" / "downtrend" / "range" / "unclear" | 最終判定ラベル |
| `regime_prob_up` | float | 0.0 - 1.0 | 上昇確率 |
| `regime_prob_down` | float | 0.0 - 1.0 | 下降確率 |
| `regime_prob_range` | float | 0.0 - 1.0 | 横ばい確率 |
| `regime_confidence` | float | 0.0 - 1.0 | 確信度 (= 最高確率 - 2 番目確率) |
| `regime_volatility_level` | category | "high" / "mid" / "low" | ATR ボラ並列フラグ |

##### MTF (= 多時間軸) 接続 — causal alignment 明示 (= CP1 監査 M3 反映・look-ahead leak 防止)

- 1 時間ごとに判定
- **`merge_asof(direction="backward")` で causal alignment** (= [Live-Market-Regime-Classifier merge_asof 実装例](https://github.com/akash-kumar5/Live-Market-Regime-Classifier/blob/main/README.md) / [arxiv 2603.20237 Temporal Coverage Bias](https://arxiv.org/abs/2603.20237) 整合):
  - 1h bar `14:00-14:59` の判定は 1h bar **close 時刻 = 15:00 時点で初めて使用可能**
  - **15:00 以降の 5m bar (= 15:00 / 15:05 / ... / 15:55) にのみ充当可能**
  - 14:00-14:55 の 5m bar には **充当不可** (= look-ahead leak 防止・L-128 / L-179 同型予防)
- 実装スクリプトに **`assert no look-ahead in regime forward fill`** を追加

##### 後段への接続

- 6 列を Phase 0 v3.1 既存 parquet に追記
- [2] Entry ML / [2.5] cluster / [3] Sizing / [4] Exit が入力特徴量として使用
- one-hot encoded 派生列 (= `regime_is_uptrend` / `regime_is_downtrend` / `regime_is_range` / `regime_is_unclear`) も学習時に自動生成
- 確率値も併用 (= LightGBM は連続値を効率的に分割可能)

##### 保存場所 (= 既存 [results/regime_step1/](../../results/regime_step1/) 配下)

- `regime_predictions_train_2021_2024.parquet`
- `regime_predictions_test_2025.parquet`
- `regime_predictions_test_2026_q1.parquet`

##### データフロー

1. Phase 0 v3.1 既存 parquet (= 5m bar)
2. ↓
3. [1.5] regime ensemble 判定 (= 1h ごと)
4. ↓
5. 1h → 5m forward fill 展開
6. ↓
7. regime 出力 6 列を parquet に追記
8. ↓
9. [2] / [2.5] / [3] / [4] が入力特徴量として使用

##### 設計判断の根拠

- 確率 + ラベル + 確信度 併用 = 業界 standard (= 後段が状況に応じて使い分け可能)
- forward fill = 業界 MTF standard
- 「フィルタ強制適用しない」決着と整合 (= 入力として渡すだけ・後段が使うかどうかは後段判断)

---

### 6.3 工程 [2.5] cluster 分類 詳細設計

#### 6.3.1 方針
- 工程 [2] Entry ML の **後段に「グループ自動分け」を独立工程として配置**
- 仕組み (= 例え話):
  - Entry ML が出した「予測値 56 個 + 特徴量」のセットを、データを自然なグループにまとめる手法 (= k-means) で動的に 3〜5 グループに分ける
  - 例えば「利確に早く届くタイプ」「損切り寄りタイプ」「時間切れになりやすいタイプ」が自然に出てくる
  - 工程 [3] Sizing / 工程 [4] Exit がグループ別に異なる出力を出す

#### 6.3.2 設計判断の根拠 (cat-bitget 制約逆算)
- **教師なし手法 (= 正解ラベル不要でグループ分け) なので安全**:
  - グループの正解ラベルを事前に作るのは困難 (= リークの原因になる)
- **過去 Phase 4-a でも同じ手法 = 構造的継承**
- **戦略並立 1.5× への寄与**:
  - グループ別に Exit / Sizing が変わる = 「異なる戦略を並立」と等価
  - [industry_benchmark §2.3](industry_benchmark_knowledge_base.md) で実証されている 1.5× 効果の前提に乗る

---

## 7. 改訂履歴

| 日付 | 版 | 内容 |
|---|---|---|
| 2026-05-26 | v1 | 初版作成 (= 6 工程ドラフト・議論のスタート点) |
| 2026-05-27 | v2 | 6 工程 → 8 工程拡張 (= [1.5] regime + [2.5] cluster 新規追加)・各工程の学習目標 / ラベル / 入出力 / 制約を決着事項として確定・5.1× レバー寄与見積追加 (= ケース B 中央値 5.57×)・WebSearch 業界実証出典追加 |
| 2026-05-27 | v2.1 | §6 工程別詳細設計書 セクション新設 (= 旧 §6 改訂履歴を §7 に繰り下げ)・[1.5] regime 詳細追記 = (1) 評価方法 4 段階 + (2) HMM 再調整方針 (= 本セッション中盤決着事項) |
| 2026-05-27 | v2.2 | §6.0 工程 [1] 特徴量計算層 詳細設計 + §6.3 工程 [2.5] cluster 分類 詳細設計 を追記 (= 前チャット取りこぼし回収・ラベル決着 + 56 ラベル詳細内訳 + 全 7 ホライズン使う決着 + cluster 方針 + cat-bitget 制約逆算根拠) |
| 2026-05-27 | v2.3 | §6.0.2 「学習対象 K 範囲」をデータ駆動判定方針に書き換え (= 事前決め打ち回避・全 7 ホライズン学習後 feature_importance / target importance で各ホライズンの予測寄与を verify・寄与してなければ次回除外) |
| 2026-05-27 | v2.4 | §6.1.3 固定ルール判定器の閾値・判定構造 追記 (= scoring + weighted vote 構造に決着・業界 standard verify 5 件・6 指標 × scoring 表・ATR を方向判定から外しボラ別フラグへ + DI/価格 vs MA/MTF 整合/一目均衡表 追加・元決着からの差分 5 点) |
| 2026-05-27 | v2.5 | §6.1.4 k-means 判定器の設計 追記 (= 業界 standard verify 4 件・4 特徴量入力 [log_returns_1h / rolling_volatility(20) / close_vs_sma20_pct__1h / adx14_1h]・k=3 で HMM と整合・HMM と同じ学習データ/前処理/判定間隔/ヒステリシス・3 判定器の役割分担明示) |
| 2026-05-27 | v2.6 | §6.1.5 ensemble 機構の設計 追記 (= soft voting + 重み付き平均に決着・業界 standard verify 4 件・初期等重み・各判定器の確率変換方法明示・最終判定 + 確信度算出 + 不明確閾値 0.4 + 連続 2 回ヒステリシス) |
| 2026-05-27 | v2.7 | §6.1.6 出力仕様 追記 (= 業界 standard verify 4 件・出力 6 列 [regime_label / prob_up / prob_down / prob_range / confidence / volatility_level]・MTF 1h → 5m forward fill・one-hot encoded 派生列・保存場所 results/regime_step1/ 配下 3 parquet・データフロー明示・「フィルタ強制適用しない」決着整合) |
| 2026-05-27 | v2.8 | **CP1 監査 (= 2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md) 結果反映** (= Verdict PIVOT・Critical 2 + Major 3 + Minor 2 件全 7 件採用支持 + プロセス欠陥対策 P1 cc_role §1.4.6.1 改善 10/11/12 追加): §6.1.1 Stage 1 内部スコアに Brier score / reliability diagram / ECE + 3 判定器予測誤差 Pearson 相関 追加 (= 観点 1 / Q5 改善 1) / §6.1.1 Stage 3 を v15 単独 + ensemble の 2 段階比較に変更 (= M1) / §6.1.1 Stage 3 合格基準を純増分 (b)/(a) 評価に変更 / §6.1.3 ATR 絶対値 250/100 を ATR_pct 25th/75th percentile data-driven に変更 (= C2 価格非依存性違反修正) / §6.1.4 k=3 事前決め打ちを k ∈ {2,3,4,5} elbow + silhouette data-driven に変更 (= m2) / §6.1.5 確率変換に isotonic regression キャリブレーション追加・k-means は Gaussian kernel 経由 (= C1 soft voting 前提条件 verify) / §6.1.5 初期等重みを Walk-Forward + GridSearchCV data-driven に変更 (= M2) / §6.1.6 forward fill を merge_asof(direction="backward") causal alignment 明示 + assert no look-ahead 追加 (= M3 look-ahead leak 防止) |
