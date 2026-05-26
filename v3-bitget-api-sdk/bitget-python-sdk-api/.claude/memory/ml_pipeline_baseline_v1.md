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

## 6. 改訂履歴

| 日付 | 版 | 内容 |
|---|---|---|
| 2026-05-26 | v1 | 初版作成 (= 6 工程ドラフト・議論のスタート点) |
| 2026-05-27 | v2 | 6 工程 → 8 工程拡張 (= [1.5] regime + [2.5] cluster 新規追加)・各工程の学習目標 / ラベル / 入出力 / 制約を決着事項として確定・5.1× レバー寄与見積追加 (= ケース B 中央値 5.57×)・WebSearch 業界実証出典追加 |
