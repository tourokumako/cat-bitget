# ML pipeline 暫定ベース案 v2 (= 2026-05-27 セッション議論決着反映)

最終更新: 2026-05-27
位置付け: 2026-05-27 セッションで 6 工程 → 8 工程に拡張・各工程の決着事項を反映。次フェーズは実装着手。

出典: 2026-05-26 セッションでまこさん提示の 6 工程ドラフト (= v1) を、2026-05-27 セッション議論で詳細化 + Web Claude 指摘 3 件 (= Exit 重点 / cluster 組み込み / regime 再検討) を反映。

---

## §0. 大原則 (絶対遵守・全工程の設計・評価・採用判定に優先・違反は false_positive_incident_policy インシデント扱い)

> 散在していた大前提をここに集約 (2026-05-31)。出典: CLAUDE.md / exchange_spec.md / false_positive_incident_policy.md / current_redesign_context.md。
> これらに反する設計・計算・判定は最重大インシデント。各工程の設計・スクリプト・採用判定は本 §0 を満たしてから先に進む。

### §0.0 思想 (なぜ §0 が最優先か)
- 未達 ($1,900 に届かない) は正直に出せば**資金を溶かさない** (まこさんが「本番に出さない」と正しく判断できる)。
- **水増し (gross を net と偽る・コスト過小・成行を maker で計算) だけが、実資金を毀損する最重大不正** (false_positive §1)。
- ゆえに「良く見せる計算」「マイナスを地面と呼んで前進」を禁止する。マイナスはマイナスと出す。

### §0.1 net 利益で判定する
- **net = 売上 (粗利) − 全コスト (手数料 maker/taker・slippage・funding) = 最終手取り**。
- 目標「月次 NET ≥ $1,900」は、この**手取り**が $1,900 という意味。gross (コスト控除前) での判定は禁止 (類型E)。
- **列名が `net_pnl` でも実体がコスト控除後か必ず verify** (関所C)。
- 合格 = **全月**が net ≥ $1,900 (単月未達は不合格・通算 NET だけで判定しない)。

### §0.2 指値 maker 基本・成行 taker は正しく計上 (本番約定実態・exchange_spec.md)
- エントリー = 指値 post_only (maker 0.014%)。**不約定 (指値が約定せず TTL 3本=15分でキャンセル) は取引不成立としてモデル化**する。
- TP 決済 = placePosTpsl 指値 (maker)。SL 決済 = placePosTpsl 指値 (maker・add_count≥2)。
- **TIME_EXIT・能動クローズ (時間切れ・急変・トレーリング決済) = close_market_order 成行 (taker 0.042%)** で計上する。
- 「全決済 maker」は禁止。成行になる決済を maker で安く計算したら不正 (類型E)。
- 手動 P23 も TP=指値maker / 能動クローズ=成行taker と使い分けている。

### §0.3 本番再現性 (Prime Directive・false_positive §0-1)
- 推論時点 t で因果的に取得不可能な値 (MFE/MAE 等の保有期間中最大値・K本後の値・期間全体集計・test 結果で決めた値) を計算・判定に使わない。
- 「指値が必ず約定する」等、本番で再現できない仮定を置かない。

### §0.4 コスト確定値 (exchange_spec.md・audit#19)
- maker 0.014% (0.00014) / taker 0.042% (0.00042) / slippage 0.005% / funding median +0.0002%/8h (LONG払い・SHORT受取・p95=0.01% は stress 参考)。

### §0.5 ポジション上限 (false_positive §0-2)
- ポジションサイズ上限 **合計 0.12 BTC** (1 ポジションあたりではなく合計上限・cap=N なら 1 pos = 0.12/N BTC)。
- 任意の時点 t で `sum(active_position_btc) ≤ 0.12` を verify。

### §0.6 手動 Priority の扱い (feedback_priority_starting_line_only)
- スタートライン参照のみ。ベンチマーク・ベース・素材転用 禁止。テクニカル全体から独立に設計する。

### §0.7 異常値 STOP (関所A)
- 勝率 > 70% / 月次 NET > $3,800 / IS-OOS Sharpe 比 > 3倍乖離 / 最大DD < 月次NETの10% のいずれかは「合格」と呼ばず虚偽達成調査 (§4) に入る。

### §0.8 評価の健全性 — PnL を測る「正しい計器」（2026-05-31 約定/コスト不正インシデントを契機に新設・WebSearch verify 済）

> **🚨 経緯（忘却厳禁）**: ML pipeline が §0.2 の**指値約定モデル（不約定・成行 taker）を実装せず**、entry を無条件約定・全決済を maker で計算していた（[run_phase4_b.py](../../scripts/priority_rebuild/run_phase4_b.py) compute_pnl）→ 過去の PnL・Replay・$1,900 判定はすべて無効（false_positive §2 類型 E）。**§0.1/§0.2 は既に正しく書いてあったのに実装が守らなかった**＝文書では守られない。手動時代 [replay_csv.py](../../runner/replay_csv.py) に正しい約定モデルが在り、ML はこれを最低限継承する。**下記はすべて実装 assertion で物理強制する**（L-241/L-242・cc_role §1.4.6.2）。

全工程の Stage 3/4 PnL 評価は以下の業界標準計器で測る（出典は本節末）:

1. **指値約定 + net（最重要・§0.1/§0.2 再掲）**: entry/TP/SL = 指値 **maker**・**不約定（TTL 内に価格未到達）は取引不成立**（カウントしない）/ TIME・能動クローズ = 成行 **taker** / 判定は **net**（手数料 maker/taker・slippage・funding 全控除後）。「指値必ず約定」「全決済 maker」「gross を net と呼ぶ」は禁止。指値 fill 判定は「価格が limit を貫通したら約定」が業界標準（hftbacktest）。
2. **コスト現実化**: round-trip all-in = crypto futures **0.15-0.30%**（業界相場）。§0.4 確定値（maker 0.014% / taker 0.042% / slippage 0.005% / funding median +0.0002%/8h）。**8h 超保有は funding 必ず控除**。保守検証 **「fee 2 倍で黒字なら本番黒字」**。
3. **sample uniqueness + sequential bootstrap**（AFML Ch.4）: overlapping label を temporal uniqueness で重み付け（K=288 窓重複 99.65% の冗長補正）+ sequential bootstrap で各 sample の uniqueness を強制 → **OOS 過大評価（intra-estimator overlap）を断つ**。
4. **purge + embargo（別物・混同禁止）**（AFML Ch.7）: purge = label horizon が test と重なる train を除去 / embargo = test 直後の train label を時間窓で除外。「embargo 288」を **purge のみで済ませない**（= inter-fold leakage 対処）。
5. **多重検定補正 DSR/PBO**（Bailey & López de Prado 2014）: DSR = selection bias + non-normality 補正で「真のスキルか確率」/ PBO = OOS で median 未満になる確率。**CPCV が PBO 最低・DSR 最高**（ScienceDirect 2024）。合格 = 全月 net ≥ $1,900 + **DSR > 0.95 + PBO < 0.5**。
6. **non-stationarity / survivorship / look-ahead**: 生 close は非定常 → fracdiff（d* を ADF 最小 d 探索・ハードコード禁止）。**survivorship は年 17-22% の return inflation**（Coinbase Institutional）。look-ahead = 同足 close で同足 entry 判断。regime 時代依存（SHORT 偏り 2023 由来 = 類型 D）。

**比較の地面**: 手動 Priority $370 も funding/slippage 未控除 → 公平比較は両方を同条件で再計算する。

> 出典（2026-05-31 WebSearch）: [StratBase realistic fees](https://stratbase.ai/en/blog/backtest-realistic-fees) / [hftbacktest order fill](https://hftbacktest.readthedocs.io/en/py-v2.1.0/order_fill.html) / [Bailey & LdP DSR (SSRN 2460551)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551) / [AFML 10 reasons ML funds fail (uniqueness/purge/embargo)](https://www.garp.org/hubfs/Whitepapers/a1Z1W0000054x6lUAA.pdf) / [CoinAPI survivorship 17-22%](https://www.coinapi.io/blog/how-to-eliminate-survivorship-bias-in-crypto-backtesting) / [ScienceDirect CPCV/DSR/PBO 2024](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110)

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
    - LightGBM 56 個独立並列学習 (= scikit-learn MultiOutputRegressor で encapsulate・LightGBM は native multi-output 非対応のため)
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
| [2] Entry ML | LightGBM 56 個独立並列学習 | 1462 指標 + regime 出力 | direction + confidence + 56 ラベル予測 | threshold 緩め (= 月 275+ 件) |
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

### 評価基盤 詳細設計（全工程共通・§0.8 の実装仕様・2026-05-31 新設）

> §0.8（評価の健全性・原則）の **実装仕様**。全工程の Stage 3/4 PnL 評価はこのエンジンで測る。各項目に **既知答えテスト**を付け、テスト pass を計器の正しさの証明とする（監査でなく数学的事実で検証・L-242）。
>
> ⚠️ **【2026-05-31 修正・WebSearch verify】mlfinlab は除外し全項目を自前実装する**（旧記述「mlfinlab 既存実装を活用」を撤回）。理由（検証済・記憶でない）: ① mlfinlab(Hudson & Thames) は **全権利留保・商用は有償ライセンス必須**（実弾商用ボットで使用不可）② **Python 3.7〜3.9 世代で 3.11 非対応**（本 venv=3.11.15・2023 から保守停止）→ 入れると本番 venv(lightgbm 4.6/numpy 1.26/sklearn 1.8) を壊すリスク。代替 mlfinpy(MIT・3.11) は v0.1.2(2024-10)・**Alpha**・約19ヶ月更新なし → 計器の心臓部に未成熟依存は入れない。**アルゴリズムは AFML Ch.4 等の公開知識**（教科書の式を実装するのは合法）→ 約定/コスト計器（A）と同様、**自前実装 + 既知答えテスト**で正しさを数学的に証明する。E(fracdiff)/F(DSR/PBO) は項目ごとに「自前 or 保守された軽量単機能ライブラリ」を選び直す。出典: [mlfinlab 商用ライセンス](https://hudsonthames.org/mlfinlab/) / [mlfinpy PyPI(Alpha)](https://pypi.org/project/mlfinpy/)。

#### A. 約定・コストモデル（自前・replay_csv 準拠 + 楽観3点是正）

- **Entry 約定**: シグナル bar `i`（close 確定後）→ bar `i+1` で指値 `limit=close_i×(1∓0.0001)`。bar `j`(i+1≤j≤i+**TTL=3**) で LONG:`low_j≤limit` / SHORT:`high_j≥limit` で約定（価格=limit・maker）。TTL内未到達=**取引不成立（記録しない）**。
- **Exit（replay_csv 楽観3点是正）**: ①**SL を TP より先に判定**（同bar両到達は不利側先着）②**gap反映**=SL飛び越えは `min(sl,open_j)`(LONG) 約定 ③touch でなく保守fill。TP=指値 maker / SL・TIME・能動クローズ=成行 taker + slippage。
- **コスト**: entry=maker / exit=maker(TP) or taker(SL/TIME/能動) / slippage 0.005%（成行のみ）/ funding=保有中の8h境界ごと `size×mark×rate`（§0.4）。**net=gross−全コスト**。
- **0.12 BTC**: 任意 t で `sum(active)≤0.12` を assert（§0.5）。
- **既知答えテスト**: T1 コインフリップ→net≒−往復コスト（負）/ T2 limit不到達→entry 0件 / T3 同bar TP・SL両到達→**SL記録** / T4 gap→open約定 / T5 8h超保有→funding控除。

#### C〜F + leak/regime（mlfinlab 活用 + 自前チェック）

| # | §0.8 | 実装（自前・mlfinlab 除外） | 状態 | 既知答えテスト（pass=正しさ証明） |
|---|---|---|---|---|
| A 約定/コスト | ①② | `eval_engine.py`（指値maker+不約定TTL3+SL先着/gap/保守fill+taker/slippage/funding+0.12assert） | ✅ 完成・T1-T5 全pass(commit 66de850) | T1 コインフリップ→net負 / T2 不約定0件 / T3 両到達→SL / T4 gap→open / T5 funding控除 |
| C uniqueness | ③ | `sample_uniqueness.py`（AFML Ch.4 自前: concurrency→average uniqueness→sample_weight + sequential bootstrap） | ✅ 完成・C1-C5 全pass | C1 同一区間→ū=1/N / C2 重なりなし→1.0 / C3 部分重なり手計算 / C4 実効N<<N / C5 seq>std debiasing |
| D purge+embargo | ④ | `purged_kfold.py`（自前 PurgedKFold + embargo・AFML Ch.7: purge=label窓が test と重なる train 除去 / embargo=test 直後を時間窓除外・別物） | ✅ 完成・D1-D5 全pass | D1 purge後 重なり0(素朴は160) / D2 embargo窓 train0 / D3 train末<test始 / D4 test完全分割 / D5 リーク注入→naive 0.82→purged 0.45 精度低下 |
| E fracdiff | ⑥ | `frac_diff.py`（自前 AFML Ch.5 固定幅窓 + statsmodels.adfuller・`fracdiff` パッケージは未インストールで自前選択）・d*=ADF 最小d をグリッド探索（ハードコード禁止）/ 生close 除外 | ✅ 完成・E1-E6 全pass | E1 d=0恒等 / E2 d=1=1階差 / E3 重み既知 / E4 生close非定常→d*=0.35で定常 / E5 記憶保持(corr0.42 vs returns0.04) / E6 生close閾値が本番域で退化→log-fracdiff両域定常 |
| F DSR/PBO | ⑤ | 自前（Bailey & LdP 式）DSR(N=実効戦略数) + CSCV PBO・合格=月次net+DSR>0.95+PBO<0.5 | ⬜ 未着手 | ランダム多数→best選んでもDSR低 / N過少→DSR過大を検出 |
| leak | ⑥ | 自前 grep `shift(-)`/`center=True`/未来index + 因果性1行宣言 | ⬜ 未着手 | 入力1bar shiftで予測不変→未来参照疑い |
| regime 類型D | ⑥ | 自前 全期間使用 + 年別/regime別 成績分散 | ⬜ 未着手 | 2023除外で SHORT エッジ消失→時代依存 |

#### 実装順序

A → C → D → E → F → leak/regime を1項目ずつ実装+テスト pass。`ml_phase2_production` 予測データで回す（**再学習不要**・軽い）。次セッションから着手。各項目完了時に既知答えテスト全 pass を確認してから次へ。

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

##### Triple Barrier の TP/SL 壁の閾値 (= §6.2.3 論点 3 で改訂・2026-05-27 まこさん判断「案 C」採用)

**旧設計** (= USD 絶対値で価格依存・L-179 同型違反):
- TP 壁 = エントリー価格 × (1 + ATR (= 平均値幅) の 2.0 倍)
- SL 壁 = エントリー価格 × (1 - ATR の 1.5 倍)

**新設計** (= ATR_pct ベース + K 別 multiplier・詳細は §6.2.3 論点 3 参照):
- TP 壁 = entry × (1 + ATR_pct × multiplier_TP)
- SL 壁 = entry × (1 - ATR_pct × multiplier_SL)
- multiplier_TP / multiplier_SL は K 別 data-driven (= 短期 K cat_v9 流 / 長期 K AFML 流)
- = **価格非依存 + K 別動的閾値**

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

### 6.2 工程 [2] Entry ML 詳細設計

> §6.2.1 〜 §6.2.8 全 8 サブセクション完成 (= regime ensemble §6.1.1〜§6.1.6 と同型構造)。

#### 6.2.1 評価方法 (= 4 段階・regime ensemble §6.1.1 と同型構造)

##### 業界 standard verify (= 本セッション 2026-05-27 WebSearch 3 回・cc_role §1.4.6.1 改善 6 機械運用)

- **Walk-Forward + 統計指標 + Financial metrics 並行評価が業界 standard**: [arxiv 2509.16707 AI-Driven Trading Framework 2025](https://arxiv.org/html/2509.16707v1) / [arxiv 2512.12924 Walk-Forward Validation Framework 2025](https://arxiv.org/pdf/2512.12924) で確認・z-test/信頼区間で signal 妥当性 verify + cumulative return/PnL/drawdown/Sharpe を rolling window 別に算出 → 平均
- **LightGBM multiclass 評価指標**: [GeeksforGeeks LightGBM Evaluation Metrics](https://www.geeksforgeeks.org/machine-learning/lightgbm-model-evaluation-metrics/) で multi_logloss (= objective softmax) / auc_mu / precision / recall が業界 standard
- **Multi-output regression 評価**: [Towards Better Evaluation Multi-Target Regression](https://www.researchgate.net/publication/348946910_Towards_Better_Evaluation_of_Multi-target_Regression_Models) で RMSE / R² を target 別 + uniform 平均が業界 standard

##### 教科書整合 (= cc_role §1.4.6.1 改善 7)

- **Lopez de Prado AFML Ch.7 Cross-Validation in Finance**: Walk-Forward + Purged K-Fold + Embargo の組合せ (= §6.2.5 CV 設計で詳細議論)
- **[[industry_benchmark_knowledge_base]] §3.1 統計指標と PnL の関係**: 統計指標が良くても PnL に直結する保証はない → 並行評価が業界主流

##### Stage 1 内部スコア (= [2] Entry ML 完成直後・統計のみ)

| ラベル系統 | 個数 | 評価指標 |
|---|---|---|
| 揺れ幅系 (MFE/MAE pct) | 28 (LONG 14 + SHORT 14) | RMSE / R² (= target 別 + uniform 平均) |
| 決着系 Triple Barrier 3 class | 14 (LONG 7 + SHORT 7) | multiclass logloss / accuracy / F1 macro + **Brier score + reliability diagram + ECE** (= class_weight キャリブレーション品質・CP2 監査 C1 反映) |
| 決着系 meta_label binary | 14 (LONG 7 + SHORT 7) | AUC / Precision / Recall + **Brier score + reliability diagram + ECE** (= scale_pos_weight キャリブレーション品質・CP2 監査 C1 反映) |

加えて:
- **feature_importance top 20 review** (= leak 4 点 verify 含む・[[feedback_ml_leak_mandatory_check]] 整合): 56 モデル全部について feature_importance top 20 を出力・blacklist 由来 (sma_20/sma_50/ichimoku_kijun/ichimoku_tenkan/macd_line/macd_signal/macd_hist/macd_hist_change) 混入なし + 未来参照疑い列なし verify
- **56 ラベル間予測相関** (= §6.2.2 懸念 verify): 56 個独立学習が真に異なる予測分布を学習しているか確認・相関 > 0.95 のペアは冗長として §6.2.6 で再評価

##### Stage 2 視認 + 統計検定 + Exit 抜き PnL proxy (= [2] Entry ML 完成直後)

- (a) **entry signal 妥当性目視** (= まこさん視認・regime §6.1.1 Stage 2 整合): 月単位で entry した bar 列 + direction + confidence を dashboard 化してまこさん視認
- (b) **旧 Priority v9 P1-P25 発火位置 overlap 分析** (= cat-bitget 固有 verify・cc_role §1.7 スタートライン整合): ML 発火 bar vs 旧 Priority 発火 bar の overlap 率を Priority 別に算出・cluster 別の方向性確認
- (c) **entry direction 分布 + threshold 緩め月 275+ 件 verify**: LONG/SHORT/NONE 件数比率 + 旧 Priority v9 月平均 96 件 (= 1,157 件/12 ヶ月) との比較
- (d) **Exit 抜き PnL proxy** = `TP Precision × TP_gain - (1 - TP Precision) × SL_loss - fee` で月次 NET proxy 算出
  - TP_gain / SL_loss / fee は固定値で目安計算 (= [4] Exit 動的化前の sanity check)
  - Phase 1 v6 教訓反映 (= 統計指標 entropy_lift 0.20-0.35 / TP Precision 0.43 と PnL 乖離で combos_pass 0/8 失敗)・[[industry_benchmark_knowledge_base]] §3.1 整合

##### Stage 3 PnL 早期判定 (= [4] Exit 多層 ML 完成後・regime ensemble §6.1.1 Stage 3 と同型)

- **base line = 旧 Priority v9 月 $370** (= cat-bitget 唯一の実利資産・[[feedback_priority_starting_line_only]] / cc_role §1.7 整合)
- (a) 旧 Priority v9 単独経路の月 NET vs (b) [2]+[2.5]+[3]+[4] ML パイプライン経路の月 NET
- 純増分 = (b)/(a) で評価:

| 倍率 | 月次 NET | 判定 |
|---|---|---|
| **≥ 5.1×** | $1,900 以上 | 目標達成 → Stage 4 進行 |
| 2.0× - 5.1× | $740 - $1,900 | 部分達成 → [2.5] cluster / [3] Sizing / [4] Exit 改善余地で挽回試行 |
| 1.0× - 2.0× | $370 - $740 | 設計やり直し |
| < 1.0× | $370 未満 | 旧 Priority v9 未達 = ML パイプライン根本欠陥 |

##### Stage 4 最終 PnL (= 8 工程合算後)

- **Phase 5 Replay**: 全 12 ヶ月 NET ≥ $1,900 (= phase_flow_v4 / cc_ml_design_spec 合格基準整合)
- **Phase 6-b 本テスト 2026 Q1**: 全 3 ヶ月 NET ≥ $1,900

##### 業界 standard との差分 (= cc_role §1.4.6.1 改善 8)

- **業界 standard**: 統計指標 + Financial metrics 並行評価 ([[industry_benchmark_knowledge_base]] §3.1 / [arxiv 2509.16707](https://arxiv.org/html/2509.16707v1) / [arxiv 2512.12924](https://arxiv.org/pdf/2512.12924))
- **本提案**: Stage 1 (= 統計) + Stage 2 (= Exit 抜き PnL proxy 含む) + Stage 3 (= 実 PnL) で並行構造 = 業界整合
- **違い**: Stage 3 base line に **旧 Priority v9 月 $370** を採用 (= cat-bitget 固有スタートライン整合・cc_role §1.7)・Random / 全 bar Entry は発火数膨大で base line として意味不明のため不採用

##### 統計指標と PnL 指標の分離 (= cc_role §1.4.6.1 改善 9)

| Stage | 評価指標性質 | 内容 |
|---|---|---|
| Stage 1 | 統計指標のみ | 各ラベル予測精度 (RMSE/R²/logloss/F1/AUC/Precision/Recall) |
| Stage 2 | 統計指標 + PnL proxy | 視認 + overlap + 件数 + Exit 抜き月次 NET proxy |
| Stage 3 | PnL 指標のみ | 実 NET 純増分 (b)/(a) ([4] Exit 動的化後の部分パイプライン) |
| Stage 4 | PnL 指標のみ | 全パイプライン NET 月次合格判定 |

各 Stage で「何を見ているか」明示・混同防止 (= Phase 1 v6 教訓)

##### 設計判断の根拠 3 件

1. **Phase 1 v6 教訓反映** (= 統計指標 entropy_lift 0.20-0.35 / TP Precision 0.43 と PnL 乖離で combos_pass 0/8 失敗): Stage 2 (d) に **Exit 抜き PnL proxy 追加** で統計と PnL の乖離を早期検出 (= [[industry_benchmark_knowledge_base]] §3.1 業界整合)
2. **regime ensemble §6.1.1 Stage 1-4 構造と同型**: 工程設計の一貫性 + base line 明確化 + 純増分 data-driven 判定の経路同型
3. **base line に旧 Priority v9 月 $370 採用**: cat-bitget 固有スタートライン整合 (= cc_role §1.7) + Random / 全 bar Entry は発火数膨大で意味不明

##### 懸念 1 件 + 反論

- **懸念**: Stage 2 (d) Exit 抜き PnL proxy は TP_gain / SL_loss / fee の固定値前提 → [4] Exit 多層 ML で動的化された後の実 PnL とは乖離する可能性
- **反論**: Stage 2 は「[2] Entry ML 単独完結評価」が目的・Stage 3 で実 Exit 動的 PnL で再判定する **2 段階構造** → proxy 乖離はリスク限定的・Phase 1 v6 教訓を活かす早期検出として有用

##### data-driven 経路宣言 (= cc_role §1.4.6.1 改善 12)

- Stage 1 統計指標の合格判定値 (= multi_logloss / accuracy / F1 / RMSE / R² の閾値) は実装着手後の 1 fold 結果で **fold 別 percentile** で決定
- Stage 2 (d) TP_gain / SL_loss / fee 固定値 = [[exchange_spec]] 確定値 (= Maker 0.014% / Funding p50 0.0002%/8h) + 旧 Priority v9 平均 TP 0.5% / SL 2% (= cat_v9 経験値) で暫定
- Stage 3 合格基準倍率 (= 5.1× / 2.0× / 1.0×) は ml_pipeline_baseline §2.2 業界レバー寄与中央値 5.57× との整合で確定 (= 暫定数値ではなく目標連動)
- Stage 1 56 ラベル間予測相関の冗長判定閾値 (= > 0.95) は本セッション暫定・1 fold 結果で再 calibrate

#### 6.2.2 アルゴリズム選定

##### 業界 standard verify (= 本セッション 2026-05-27 WebSearch 3 回・cc_role §1.4.6.1 改善 6 機械運用)

- **LightGBM は native multi-output 非対応**: [Forecastegy LightGBM Multi-Output](https://forecastegy.com/posts/lightgbm-multi-output-regression-classification-python/) / [LightGBM GitHub Issue #524](https://github.com/microsoft/LightGBM/issues/524) で確認。scikit-learn の MultiOutputRegressor で encapsulate するのが業界 standard。実装上は「1 target につき 1 LightGBM」= 56 個独立並列学習になる・inter-target relationships は学習されない
- **Stacking (= LightGBM + XGBoost + meta-learner) の精度向上実証**: [johal.in MLPerf 2025](https://johal.in/ensemble-learning-methods-xgboost-and-lightgbm-stacking-for-improved-predictive-accuracy-2025/) で stacking が単一モデルより最大 15% 精度向上 / [ResearchGate Stacking XGBoost+LightGBM+CatBoost+AdaBoost+RF meta](https://www.researchgate.net/publication/397047638_Stacking_Ensemble_Learning_Combining_XGBoost_LightGBM_CatBoost_and_AdaBoost_with_Random_Forest_Meta_Model) で stability 改善 + variance/bias 削減
- **Triple Barrier + 深層学習 BTC/ETH algo trading 業界実証**: [Springer Triple Barrier 2025](https://link.springer.com/article/10.1186/s40854-025-00866-w) で確立・Triple Barrier multiclass + LightGBM Multi-output 5min 特化研究は少ない (= cat-bitget で先行ケース)

##### 教科書整合 (= cc_role §1.4.6.1 改善 7)

- **Lopez de Prado AFML Ch.3 Triple Barrier Method**: TP/SL/Time の 3 barrier で multiclass 分類問題に帰着 (= [[cc_entry_logic_self_study]] §14.1 整合)
- **Lopez de Prado AFML Ch.6 Ensemble Methods**: Bagging / Boosting / Stacking の使い分け (= LightGBM = Boosting / Random Forest = Bagging / GBDT + DL = Stacking)

##### cat-bitget 適用設計 = 2 段階アプローチ

| 段階 | 内容 | タイミング |
|---|---|---|
| **第一段階** | LightGBM 56 個独立並列学習 (= MultiOutputRegressor encapsulate) | [2] Entry ML 実装着手時 |
| **第二段階** | Stage 3 で「LightGBM 単独 vs LightGBM + XGBoost stacking」純増分 (b)/(a) ≥ 1.3× 比較 → 多様化採否判定 | [4] Exit 多層 ML 完成後 |

##### Stage 3 比較経路 (= regime ensemble §6.1.1 Stage 3 と同型)

- (a) **LightGBM 単独** 経路の [2]+[2.5]+[3]+[4] 部分パイプライン NET
- (b) **LightGBM + XGBoost stacking** 経路の同パイプライン NET
- 純増分 = (b)/(a) で評価:
  - **≥ 1.3×**: stacking 採用 → §6.2.2 改訂
  - **1.1× - 1.3×**: 計算コスト ×2 とのトレードオフで判定
  - **< 1.1×**: LightGBM 単独維持 → 第三段階で GBDT + DL stacking 検討

##### 設計判断の根拠 4 件

1. **Phase 1 v6 全滅主因 3 件 (regime 不在 / LONG-SHORT 並列 / MTF 欠落) を本セッション設計で構造解消する経路**: [[cc_entry_logic_self_study]] §13.1 で全 6 案 LightGBM 単一・多様性ゼロ + regime context 不在を原因として特定済み。本セッションで regime 6 列追加 (= §6.1.6) + LONG/SHORT 分離議論 (= §6.2.4 で議論予定) + MTF 8 時間軸 (= Phase 0 v3.1) を構造的に解消する経路にある → アルゴ多様化が必須かは未確定

2. **regime ensemble §6.1.1 Stage 3 経路と同型** (= base line 明確化 + 純増分 data-driven 判定): regime ensemble で「v15 HMM 単独 vs 3 判定器 ensemble」を比較した経路と同じ手法。CC 単独判断ではなく Stage 3 PnL で data-driven 判定する経路

3. **計算コスト + 同型バイアス相関 verify** (= cc_role §1.4.6.1 改善 11): LightGBM と XGBoost は同じ boosted tree 系統で予測誤差相関 0.7-0.9 (= 業界報告値) → 多様化効果限定的。真の多様化は GBDT + DL (= GRU/Transformer) で初めて低相関だが計算コスト 3-10 倍。56 ラベル並列学習 × Walk-Forward 5 fold で LightGBM 単独でも train time 数時間想定 (= Phase 1 v6 経験) → XGBoost 並走で 2 倍・DL 並走で 10 倍以上

4. **cat-bitget 固有 verify** (= cc_role §1.4.6.1 改善 10): regime ensemble v3 で rule + k-means + HMM の異種 3 判定器 ensemble で accuracy 0.46→0.65 (= +41% 改善) 達成 → cat-bitget 内で多様化の効果実証あり。ただし **regime は教師なし HMM 主体** で単一手法精度限界が露呈しやすかった。Entry ML は **最初から教師あり Triple Barrier multiclass** で構造異なるため同型適用は誤読リスク → 第一段階単独 + Stage 3 比較で慎重に判定

##### 懸念 1 件 + 反論

- **懸念**: 56 個独立学習 = 「揺れ幅 (MFE/MAE) 予測」と「決着 (Triple Barrier/meta_label) 予測」の inter-target 関係性 (= 例: TP 到達確率が高い時は MFE も大きいはず) を 1 モデル内で同時学習しない構造 → Phase 1 v6 「揺れ幅予測逃げ」と同型リスクか?
- **反論**: Phase 1 v6 失敗の原因は 14 ラベル全部 MFE/MAE で「予測対象の種類が偏った」こと。本案は 56 ラベル (= 揺れ幅 28 + 決着 28) で **予測対象の種類を物理的に増やす** 構造 → 56 個独立学習でも、各モデル (= 各 LightGBM) の **業務範囲が強制的に異なる** ため、全体として「揺れ幅専用化」は起きない。56 ラベル並列学習の効果は「1 モデル内の同時学習」ではなく「**予測対象の種類を物理的に増やすこと**」で達成される ([[priority_v9_trade_logic_analysis]] §5.3 単価上げ整合)

##### data-driven 経路宣言 (= cc_role §1.4.6.1 改善 12)

- 第一段階の hyperparameter 探索範囲 + 第二段階の stacking 採否判定は §6.2.6 ハイパラ探索 + §6.2.7 出力 → entry 判定 議論段階で確定
- stacking 採用時の meta-learner 選定 (= Logistic Regression / Random Forest / Ridge 等) も §6.2.6 で議論

#### 6.2.3 ラベル設計詳細

##### 業界 standard verify (= 本セッション 2026-05-27 WebSearch 3 回・cc_role §1.4.6.1 改善 6 機械運用)

- **Triple Barrier ATR multiplier 業界 standard**: [Mudrex ATR Crypto](https://mudrex.com/learn/average-true-range-crypto/) / [Bitget Wiki ATR](https://www.bitget.com/wiki/how-to-calculate-atr) で SL = ATR × 1.5-2.0 / TP = ATR × **3 以上** (= リスクリワード比 2:1 維持) が業界 standard
- **LONG/SHORT dual-task architecture**: [arxiv 2508.14656 Deep Learning Short-Term Equity 2025](https://arxiv.org/html/2508.14656) で LONG/SHORT を 1 モデルで両方学ぶ dual-task architecture が directional momentum 識別力高い
- **LightGBM multiclass imbalance**: [LightGBM GitHub Issue #6807](https://github.com/microsoft/LightGBM/issues/6807) / [Issue #3167](https://github.com/microsoft/LightGBM/issues/3167) で `is_unbalance` / `scale_pos_weight` は binary 専用・multiclass は `class_weight = "balanced"` 使用 (= 効果不安定 + 確率推定悪化リスクあり)

##### 教科書整合 (= cc_role §1.4.6.1 改善 7)

- **Lopez de Prado AFML Ch.3 Triple Barrier Method**: TP/SL/Time 3 barrier multiclass + ATR-based dynamic barrier (= [[cc_entry_logic_self_study]] §14.1 整合)
- **Lopez de Prado AFML Ch.3 Meta-Labeling**: primary (= 方向予測) + secondary (= TP 到達 yes/no) の二段構造 (= §14.2 整合)

##### 論点 1. K (= 予測ホライズン) 重み付け

**決着**: 重み付けなし (= 全 7 ホライズン K=6/12/24/48/96/144/288 並列学習維持・§6.0.2 既決着)

- 寄与判定 = feature_importance / target importance で fold 別 verify
- 集約方法 = §6.2.7 出力 → entry 判定で議論

##### 論点 2. LONG/SHORT 並列 vs 分離

**決着**: ラベル定義レベルで既分離 (= 56 ラベル中 LONG 28 + SHORT 28)・追加対策不要

- 業界 standard (= dual-task architecture) と整合: 入力共通 + 出力 target 分離
- Phase 1 v6 失敗主因「LONG-SHORT 並列学習」(= 1 つの target で混在学習) は構造解消済み
- 強化案 (オプション・§6.2.4 で議論可): regime 別 model 分離と組合せで LONG/SHORT × regime の 4 軸分離

##### 論点 3. Triple Barrier 閾値 — §6.0.2 修正 + K 別 multiplier data-driven (= まこさん判断「案 C」採用・2026-05-27)

###### 価格非依存性違反修正 (= cc_role §1.4.6.1 改善 10 / L-179 / phase_compliance §-1 同型予防)

**修正前** (§6.0.2 既決着・USD 絶対値で価格依存):
- TP = entry × (1 + ATR × 2.0) / SL = entry × (1 - ATR × 1.5)
- BTC $100k のとき TP 0.6% / BTC $50k のとき TP 1.2% に価格依存して動的変動 → L-179 同型違反

**修正後** (= ATR_pct ベース・価格非依存):
- TP = entry × (1 + ATR_pct × multiplier_TP)
- SL = entry × (1 - ATR_pct × multiplier_SL)
- ATR_pct = ATR / entry × 100 (= 既存 1,462 指標の atr_14_pct として存在)
- どの BTC 価格でも同じ % 閾値を維持

###### K 別 multiplier data-driven 設計

| K (= 予測ホライズン) | 戦略タイプ | multiplier_TP | multiplier_SL | 設計思想 |
|---|---|---|---|---|
| K=6 (= 30 分) | スキャル超短期 | 暫定 1.5 | 暫定 2.0 | cat_v9 スキャル系整合 (= SL > TP・TP まで届きやすく) |
| K=12 (= 1h) | スキャル | 暫定 1.5 | 暫定 2.0 | cat_v9 P1/P3 整合 |
| K=24 (= 2h) | 短期 | 暫定 2.0 | 暫定 2.0 | 中間遷移 |
| K=48 (= 4h) | 中期 | 暫定 2.5 | 暫定 1.5 | 中間遷移 |
| K=96 (= 8h) | 中期 | 暫定 3.0 | 暫定 1.5 | AFML standard (= TP > SL・1 回勝てば 2 回負け分挽回) |
| K=144 (= 12h) | 中長期 | 暫定 3.0 | 暫定 1.5 | AFML standard |
| K=288 (= 24h) | 長期 | 暫定 3.0 | 暫定 1.5 | AFML standard |

- **暫定 multiplier** は実装着手後の 1 fold データから atr_14_pct の 25th / 75th percentile で再 calibrate (= cc_role §1.4.6.1 改善 12 data-driven 経路宣言)
- 短期 K と長期 K の transition point (= K=24/48 中間遷移) は Stage 1 内部スコア + Stage 2 視認結果でハイパラ調整

##### 論点 4. ラベル不均衡対策 (= まこさん判断「CC 推奨で進める」採用・2026-05-27)

###### TripleBarrier 14 ラベル (= 3 class)

**第一段階**: `class_weight = "balanced"` (= 各 class の出現頻度の逆数で重み付け) で対応

- Stage 1 で fold 別 class 分布 + class 別 recall / precision verify
- ⚠️ 「効果が出ない / 確率推定が悪化」報告あり ([LightGBM GitHub Issue #3167](https://github.com/microsoft/LightGBM/issues/3167))
- **必須キャリブレーション追加** (= CP2 監査 C1 反映): class_weight 適用後の `predict_proba` 出力に対し **fold 別 isotonic regression** で post-hoc キャリブレーション実装 ([arxiv 2510.25458 Scalable Utility-Aware Multiclass Calibration](https://arxiv.org/pdf/2510.25458) 整合)・§6.2.7 集約式の入力 TP_prob は **キャリブレーション後の値**を使用

**第二段階** (= Stage 1 各 class recall < 0.3 で発動): 効果不足なら以下追加検討
- **SMOTE** (= Synthetic Minority Oversampling Technique・少数派 class データを人工合成して増やす技法)
- **focal loss** (= 難しいサンプルに重点を置く loss 関数・class imbalance 対策で業界実証)
- どちらも追加コスト + 確率推定への影響を Stage 1 で再 verify

###### meta_label 14 ラベル (= binary)

- `scale_pos_weight = 負例数 / 正例数` で対応 (= binary 専用パラメータ適用可)
- fold 別に正例 / 負例分布を verify
- **必須キャリブレーション追加** (= CP2 監査 C1 反映): scale_pos_weight 適用後の `predict_proba` 出力に対し **fold 別 isotonic regression** で post-hoc キャリブレーション実装・§6.2.7 集約式の入力 meta_yes_prob は **キャリブレーション後の値**を使用

##### 論点 5. meta_label 14 個の使い方

**決着**: §6.2.3 段階では「14 ラベルとして並列学習」のみ明示

- AFML Ch.3 Meta-Labeling primary + secondary 接続 + Half-Kelly への size 受け渡しは §6.2.7 出力 → entry 判定で詳細議論
- 第一段階 = Triple Barrier 14 ラベル (= primary 役) + meta_label 14 ラベル (= secondary 役) を同時並列学習で予測値出す
- 第二段階 = §6.2.7 で primary と secondary の集約方法決定

##### 業界 standard との差分 (= cc_role §1.4.6.1 改善 8)

- **業界 standard** = TP/SL ATR multiplier 固定 (= 全 horizon 同一閾値) + LONG/SHORT dual-task + multiclass class_weight=balanced
- **本提案** = K 別 multiplier data-driven (= 短期 cat_v9 流 / 長期 AFML 流) + LONG/SHORT ラベル分離 (= dual-task 整合) + class_weight + Stage 1 verify + 不足なら SMOTE/focal loss 追加
- **違い**: K 別 multiplier 使い分け = cat-bitget 固有設計 (= 短期 cat_v9 経験値整合 + 長期 AFML standard 整合のハイブリッド)

##### cat-bitget 固有 verify (= cc_role §1.4.6.1 改善 10)

- cat_v9 スキャル系 (= P1, P3, P21, P25 = MAX_ADDS=1): TP 0.5-1.2% / SL 1.5-2% → SL/TP 比 1.5-4 (= SL > TP)
- cat_v9 平均建値型 (= P2, P4, P22, P23, P24 = MAX_ADDS=5): TP 0.5-0.7% / SL 5% → SL/TP 比 7-10 (= SL >> TP)
- → cat_v9 全体として「SL > TP」設計思想・短期 K = cat_v9 流 + 長期 K = AFML 流のハイブリッド採用

##### 統計指標と PnL 指標の分離 (= cc_role §1.4.6.1 改善 9)

- Triple Barrier 閾値 (= TP/SL multiplier) は **PnL 指標** (= 最終的に NET に直結)
- ラベル不均衡対策 (= class_weight) は **統計指標** (= class 別 recall / precision)
- 両者を Stage 1 で並行 verify

##### 設計判断の根拠 4 件

1. **価格非依存性違反修正必須** (= L-179 同型予防・cc_role §1.4.6.1 改善 10): ATR の USD 絶対値を ATR_pct に修正・既決着 §6.0.2 から書き直し
2. **K 別 multiplier data-driven 採用** (= まこさん判断・案 C 採用): 短期 K = cat_v9 整合 / 長期 K = AFML standard 整合・cat-bitget 固有ハイブリッド設計
3. **ラベル不均衡対策段階的アプローチ** (= まこさん判断採用): class_weight 第一段階 + Stage 1 verify + 不足時 SMOTE / focal loss 第二段階
4. **regime ensemble §6.1 と同型構造維持**: WebSearch 業界 standard verify + 教科書整合 + cat-bitget 固有 verify + 段階的アプローチ

##### 懸念 2 件 + 反論

- **懸念 1**: K 別 multiplier 使い分けは複雑度増加 → 実装工数 + デバッグ難易度上昇
  **反論**: K 別重み付け自体は §6.0.2 で「全 7 ホライズン feature_importance 別 verify」を採用済・複雑度は既決着範囲内

- **懸念 2**: class_weight = "balanced" の確率推定悪化が Stage 1 AUC / F1 評価に影響する可能性
  **反論**: Stage 1 で class 別 recall / precision 個別 verify + Stage 2 視認で異常検出経路あり・第二段階 SMOTE / focal loss で挽回可能

##### data-driven 経路宣言 (= cc_role §1.4.6.1 改善 12)

- K 別 multiplier 暫定値 = 実装着手後の 1 fold データから atr_14_pct の 25th / 75th percentile で fold 別 calibrate
- class_weight 効果不足判定 = Stage 1 各 class recall < 0.3 で第二段階 SMOTE / focal loss 検討
- SMOTE / focal loss 採用判定 = Stage 1 比較で純改善 ≥ 10% で採用

#### 6.2.4 入力特徴量設計

##### 業界 standard verify (= 本セッション 2026-05-27 WebSearch 3 回・cc_role §1.4.6.1 改善 6 機械運用)

- **Regime-aware が単一モデルより優位** (= regime 別 model 分離は必須ではない): [arxiv 2509.09751 Meta-Learning RL Crypto 2025](https://arxiv.org/html/2509.09751v1) で「Models trained on one market regime perform poorly when the regime shifts, fighting the last war」・「regime 別 model 分離」と「regime 情報を入力に渡す」両方が regime-aware の一形態
- **LightGBM 1,000+ 特徴量処理可能**: [arxiv 2303.02223 Feature Selection Annealing](https://arxiv.org/pdf/2303.02223) / [arxiv 2501.07580 LightGBM Forecasting](https://arxiv.org/pdf/2501.07580) で LightGBM 高次元特徴量 robust・業界主流 = 全投入 + post-pruning (= feature_importance で学習後に重要度低いものを削る)
- **MTF integrated 入力が業界 standard**: [Preprints 202603.0994 Multi-Timeframe Feature Engineering Bitcoin](https://www.preprints.org/manuscript/202603.0994/v1/download) で 4 時間軸 integrated 入力で LightGBM expanding-window CV ROC-AUC 0.57-0.61・intermediate TF (= 4h BB + momentum) が dominant

##### 教科書整合 (= cc_role §1.4.6.1 改善 7)

- **cc_role §1.7 「事前絞り込み禁止」整合**: ML が思考シュリンクで最低限の学習しかさせない傾向を矯正
- **Lopez de Prado AFML Ch.6 Ensemble Methods**: tree-based モデルは標準化不要 + 欠損値自動処理 (= LightGBM default 機能)

##### 論点 1. regime 別 model 分離 vs 統合 (= まこさん判断「案 A 統合」採用・2026-05-27)

###### 採用方針: 案 A 統合 + 第二段階で性能差判定

- **第一段階**: 1 つの LightGBM 56 個 (= MultiOutputRegressor encapsulate) に regime 6 列を入力・regime 別パターンは tree depth で自動学習
- **第二段階**: Stage 1 で「regime 別 accuracy 比較」「regime 別 feature_importance 比較」を verify → regime 間性能差 > 30% なら案 B (= regime 別 model 分離・224 モデル化) を再検討

###### 採用根拠 3 件

1. **計算コスト**: 案 B = 学習時間 4 倍・GPU なし環境で実用厳しい
2. **データ量 1/4 で過学習リスク**: regime 別に分けると 1 regime あたりデータ量 1/4 = 過学習しやすい
3. **LightGBM の自動学習力**: tree (= if-then ルール) の深さで「regime × signal」の組合せパターンを自動発見可能 (= まこさん例「UPtrend + MACD GC + RSI ≥ 50 → TP 高」は案 A の決定木分岐で学習される)

###### 業界 standard 整合確認

- regime-aware が単一モデルより優位は業界実証あり (= [arxiv 2509.09751])
- ただし「regime-aware = 完全 model 分離」とは限らない・「regime 情報を入力に渡す」も regime-aware の一形態
- 本提案は後者 (= 入力に regime 6 列追加) で業界 standard 整合

##### 論点 2. 特徴量事前絞り込み vs 全投入 (= 業界 standard 整合で決着)

###### 採用方針: 全投入 + Stage 1 post-pruning

- **第一段階**: Phase 0 v3.1 既存 **2,604 列** (= 1,462 指標 × MTF 8 TF 展開・blacklist 64 除外後) + **regime 6 列** = **2,610 列**を全投入 (= 既決着維持)
- **第二段階**: Stage 1 で feature_importance top 200 (= 20%) で再学習 → 性能維持なら採用・低下なら全投入維持

###### 採用根拠

- LightGBM は 1,000+ 特徴量を処理可能 (= [arxiv 2303.02223] / [arxiv 2501.07580])
- 業界主流 = 全投入 + post-pruning (= 学習後 pruning が pre-selection より効率)
- cc_role §1.7 「事前絞り込み禁止」整合 (= 思考シュリンクの矯正)

###### regime 引継ぎ機能性 verify (= §6.2.1 Stage 1 整合)

- regime 6 列が feature_importance 上位 N% (= 例: top 50) に入っているか Stage 1 verify
- 入ってなければ「regime 情報を活用してない」ことになる → 強化案 (= 案 B regime 別 model 分離) 検討

##### 論点 3. MTF (= 多時間軸) 組み込み方 (= 業界 standard 整合で決着)

###### 採用方針: integrated 入力維持

- **既存 Phase 0 v3.1 の MTF 8 TF** (= 5m / 15m / 30m / 1h / 2h / 4h / 1d / 1w) integrated 入力維持 (= 既決着)
- 並列 model (= TF 別 LightGBM 8 個) は不採用 (= 計算コスト 8 倍 + オーバーキル)

###### 採用根拠

- 業界 standard ([Preprints 202603.0994]) = MTF integrated 入力で LightGBM ROC-AUC 0.57-0.61
- LightGBM が tree depth で「5m signal AND 1h signal AND 4h regime」の MTF 組合せ自動学習

###### Stage 1 で verify

- TF 別 feature_importance verify → どの TF が dominant か確認
- 業界実証 = intermediate TF (= 4h) dominant・cat-bitget も同パターン期待

##### 論点 4. regime 6 列の組み込み方 (= §6.1.6 既決着確認)

###### 採用方針: §6.1.6 既決着維持

- **one-hot encoded** = regime_is_uptrend / regime_is_downtrend / regime_is_range / regime_is_unclear の bool 列
- **確率値併用** = regime_prob_up / regime_prob_down / regime_prob_range / regime_confidence の連続値
- **両方使う** (= LightGBM が場面別に使い分け自動学習)

##### 論点 5. 特徴量の前処理 (= LightGBM default 機能活用で決着)

###### 採用方針: 前処理なし

- LightGBM は tree-based (= 決定木) なので **標準化不要** (= 値域揃える必要なし)
- 欠損値も **自動処理** (= np.nan のまま渡せば LightGBM が分岐ルールに組み込む)
- 前処理コストゼロ・実装シンプル

###### 採用根拠

- AFML Ch.6 Ensemble Methods + Lopez de Prado tree-based model の業界 standard
- cat_v9 既存 indicators.py / build_labels_pct.py で計算済の特徴量を加工なしで投入可能

##### 論点 6. 新規特徴量追加の余地 (= 段階的アプローチで決着)

###### 採用方針: 第一段階既存維持 + Stage 3 で TSFresh 追加検討

- **第一段階**: Phase 0 v3.1 既存 1,462 指標 (= 145 ファミリー × 8 TF) で十分・新規追加なし
- **第二段階** (= Stage 3 性能不足時): **TSFresh** (= Time Series Feature Extraction Library・794 features 自動抽出) 追加検討
- ⚠️ TSFresh は future window 含むため leak チェック必須 (= [[feedback_ml_leak_mandatory_check]] 4 点 verify)
- **CP2 監査 Minor-2 反映: TSFresh leak チェック経路具体化**:
  - TSFresh `extract_features` 呼び出し時に `fc_parameters` で **window 内集計のみ使う関数群を whitelist 指定**
  - **whitelist 候補**: `cwt_coefficients` / `linear_trend` / `agg_linear_trend` / `mean` / `std` / `quantile` 等 (= window 内集計で OK)
  - **blacklist 候補** (= 要 verify): `change_quantiles` / `partial_autocorrelation` 等 (= 将来情報を含み得る関数群)
  - L-179 (= fractal j+2 leak 全段素通り) 再発防止経路として whitelist 指定を強制

###### 業界 standard との関係

- 業界主流 = ベース特徴量で動作確認 → 性能不足なら段階的追加
- TSFresh は cat-bitget で leak リスク高 (= shift(-N) / future window 含む) → 採用条件厳しめ

##### 業界 standard との差分 (= cc_role §1.4.6.1 改善 8)

- **業界 standard** = regime-aware (= 入力 or 分離) + 全投入 + MTF integrated + tree-based 前処理なし + 段階的特徴量追加
- **本提案** = 業界 standard 整合・regime 別 model 分離は第二段階の出口設計として保持
- **違い**: 論点 1 で案 A 統合採用 = 計算コスト + データ量で実用優先 (= cat-bitget 固有制約)

##### cat-bitget 固有 verify (= cc_role §1.4.6.1 改善 10)

- Phase 0 v3.1 で MTF 8 TF + 1,462 指標が既に生成済 (= results/priority_rebuild/labels_mfe_mae_pct_*.parquet)
- regime ensemble v3 出力 6 列が [4]/[2.5]/[3] への共通入力として既に設計済 (= §6.1.6)
- 旧 Priority v9 (= cat_v9 P1-P25) の指標多様性 10 種 + MTF 整合性 cc_role §1.7 スタートライン到達 verify (= 1,462 指標で十分カバー)

##### 統計指標と PnL 指標の分離 (= cc_role §1.4.6.1 改善 9)

- 入力特徴量設計は**統計指標** (= 学習成績) と**PnL 指標** (= 月次 NET) どちらにも影響
- Stage 1 = feature_importance で統計的妥当性 verify
- Stage 3 = 全パイプライン PnL で実 NET verify

##### 設計判断の根拠 4 件

1. **計算コスト優先** (= まこさん判断「案 A 統合」採用根拠): cat-bitget GPU なし環境で実用優先
2. **業界 standard 整合**: 全投入 + post-pruning + MTF integrated + tree-based 前処理なし = 業界主流踏襲
3. **cc_role §1.7 「事前絞り込み禁止」整合**: 思考シュリンクの矯正・ML が全特徴量から自動 select
4. **段階的アプローチ**: 第一段階既存 + 第二段階 (= Stage 1/3 結果次第) で追加検討の出口設計

##### 懸念 2 件 + 反論

- **懸念 1**: 案 A 統合で regime 別パターンが学習されなかった場合の保険なし
  **反論**: Stage 1 で regime 別 accuracy + feature_importance verify → 性能差 > 30% で第二段階案 B 検討経路あり

- **懸念 2**: 2,610 列全投入で over-fitting リスク (= 高次元 + LightGBM の tree 深さ)
  **反論**: Walk-Forward Purged K-Fold 5 fold + early_stopping_rounds 50 (= §6.2.5 / §6.2.6 で詳細議論) で over-fitting 抑制 + Stage 1 で fold 間性能差 verify

##### data-driven 経路宣言 (= cc_role §1.4.6.1 改善 12)

- 論点 1 第二段階 (= 案 B regime 別 model 分離) の判定 = Stage 1 で regime 間 accuracy 差 > 30% で発動
- 論点 2 第二段階 (= feature_importance top 200 post-pruning) の判定 = Stage 1 比較で性能維持なら採用 / 低下なら全投入維持
- 論点 6 第二段階 (= TSFresh 追加) の判定 = Stage 3 NET 純増分 < 1.5× で発動 + leak 4 点 verify

#### 6.2.5 CV (= Cross-Validation・交差検証) 設計

##### 業界 standard verify (= cc_role §1.4.6.1 改善 6・本セッション既 WebSearch 結果活用)

- **Walk-Forward + Purged K-Fold が業界 standard**: [arxiv 2512.12924 Walk-Forward Validation Framework 2025](https://arxiv.org/pdf/2512.12924) で Walk-Forward が trading ML の業界 standard・CPCV が over-fitting 抑制で上位
- **AFML Ch.7 Cross-Validation in Finance**: Walk-Forward + Purged K-Fold + Embargo の組合せが業界主流 (= Lopez de Prado AFML)
- **Phase 1 v6 経験**: 5 fold で train_2021_2024 + Walk-Forward + Purged K-Fold 採用済 (= phase_compliance §1.6 整合)

##### 教科書整合 (= cc_role §1.4.6.1 改善 7)

- **Lopez de Prado AFML Ch.7 Cross-Validation in Finance**:
  - 7.1 The Goal of Cross-Validation
  - 7.2 Why K-Fold CV Fails in Finance (= 時系列依存性 + ラベル overlap)
  - 7.3 A Solution: Purged K-Fold CV (= ラベル生成期間の重複除外)
  - 7.4 The Embargo (= train と test 間の buffer 期間)
- **AFML Ch.12 Backtest Combinatorial Purged Cross-Validation (CPCV)**: 高度な CV 手法・over-fitting 抑制上位だが計算コスト大

##### 論点 1. fold 数 — 5 fold (= regime ensemble §6.1.4 と同型) 採用

**根拠**:
- regime ensemble §6.1.4 で「Walk-Forward + Purged K-Fold 5 fold」採用済 → [2] Entry ML も同型維持で工程一貫性
- AFML Ch.7 業界 standard で 5 fold が default 推奨
- Phase 1 v6 で 5 fold 採用済 (= phase_compliance §1.6 整合)

##### 論点 2. train/test 期間分割 — phase_compliance §0 既決着確認

| データセット | 期間 | 用途 |
|---|---|---|
| **train_2021_2024** | 2021-04 〜 2024-12 (= 3 年 9 ヶ月) | Walk-Forward Purged K-Fold 5 fold で学習 + 内部検証 |
| **test_2025** | 2025-01 〜 2025-12 (= 12 ヶ月) | Stage 4 仮テスト (= 月次 NET ≥ $1,900 全 12 ヶ月) |
| **test_2026_q1** | 2026-01 〜 2026-03 (= 3 ヶ月) | Stage 4 本テスト (= 月次 NET ≥ $1,900 全 3 ヶ月) |

**根拠**:
- phase_compliance §0 (= leak verify 4 点 / timestamp range 分離) 既決着
- regime ensemble §6.1.4 と同型・既存 Phase 0 v3.1 既存 parquet (= results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet 等) と整合

##### 論点 3. embargo (= train と test 間の空白期間) — K_max 288 bar + buffer 1 day = 暫定 2 day

**仕様**:
- ラベル生成期間 K_max = 288 bar (= 24h・= 56 ラベル中の最長ホライズン K=288) を train と test の間に空白期間として設定
- 加えて buffer 1 day (= 288 bar) を追加 → **合計 2 day (= 576 bar)** の embargo

**根拠**:
- AFML Ch.7 §7.4 The Embargo: 「train の最終 bar からラベル生成期間 K bar 分は test に使えない」
- cat-bitget の最長 K = 288 bar (= 24h) → 24h embargo + buffer 1 day = 2 day
- L-128 (= MA70 look-ahead leak) / L-179 (= fractal j+2 leak) 同型予防

##### 論点 4. Purged 範囲 — ラベル生成期間 K_max 288 bar を train から除外

**仕様**:
- 各 fold の train データから「test 期間と重複するラベル生成期間 (= train の bar 末尾 K_max 288 bar)」を除外
- fold 毎に dynamic に purge 範囲を計算

**根拠**:
- AFML Ch.7 §7.3 Purged K-Fold CV: 「ラベル生成期間が train/test 間で重複すると leak 発生」
- 既存 Phase 0 v3.1 で「shift(-K) で未来参照」をラベル側で実装済 (= phase_compliance §0 Step 5.1 verify 済) → Purged 範囲 K_max 288 bar 必須

##### 論点 5. CPCV (= Combinatorial Purged Cross-Validation) 採用検討 — 第一段階保留

**仕様**:
- **第一段階**: Walk-Forward Purged K-Fold 5 fold で学習 (= 上記論点 1)
- **第二段階** (= Stage 3 性能不足時): CPCV 採用検討
  - CPCV = N choose K 全組合せで CV (= AFML Ch.12)
  - 例: 6 group から 2 group test の組合せ = C(6,2) = 15 路径
  - over-fitting 抑制で上位だが計算コスト 27h (= step1_regime_design.md §保留事項)

**根拠**:
- 第一段階 = 計算コスト + 実装シンプルで Walk-Forward Purged K-Fold 5 fold 採用
- 第二段階 = Stage 3 で性能不足 (= NET 純増分 < 2.0×) なら CPCV 追加検討・段階的アプローチ
- 業界実証 (= [arxiv 2512.12924]) で CPCV は Walk-Forward より over-fitting 抑制上位

##### 業界 standard との差分 (= cc_role §1.4.6.1 改善 8)

- **業界 standard** = Walk-Forward + Purged K-Fold 5 fold + Embargo K_max + 高度版 CPCV
- **本提案** = 業界 standard 整合・CPCV は第二段階保留
- **違い**: 第一段階で CPCV 不採用 = 計算コスト 27h を実用優先で回避 (= cat-bitget 固有制約)

##### cat-bitget 固有 verify (= cc_role §1.4.6.1 改善 10)

- Phase 0 v3.1 既存 parquet (= 5 fold 用に train_2021_2024 / test_2025 / test_2026_q1 既生成済) で再生成不要
- regime ensemble §6.1.4 で同型 CV 構造採用済 → 工程一貫性で工数削減
- Phase 1 v6 で 5 fold 採用・leak verify 4 点済 (= phase_compliance §0 Step 5)

##### 統計指標と PnL 指標の分離 (= cc_role §1.4.6.1 改善 9)

- CV 設計は**統計指標** (= fold 別 RMSE/F1/AUC) の評価精度に影響
- Stage 1 = fold 間性能差 + fold 平均で統計妥当性 verify
- Stage 3 = test_2025 全 12 ヶ月 + test_2026_q1 全 3 ヶ月で PnL 月次合格判定

##### 設計判断の根拠 4 件

1. **regime ensemble §6.1.4 と同型維持**: 工程設計の一貫性 + 実装工数削減
2. **AFML Ch.7 業界 standard 整合**: Walk-Forward + Purged K-Fold + Embargo の組合せ
3. **計算コスト優先で CPCV 第二段階保留**: 27h 計算コストは cat-bitget GPU なし環境で実用厳しい
4. **leak 防止 4 点 verify** (= [[feedback_ml_leak_mandatory_check]]): timestamp range 分離 + Purged K_max + Embargo + feature_importance 即時 review

##### 懸念 1 件 + 反論

- **懸念**: 5 fold で train data 1 fold あたり期間が 9 ヶ月程度 (= 3 年 9 ヶ月 ÷ 5 fold = 約 9 ヶ月) → regime 偏りリスク (= 例: 1 fold が全部 UPtrend だけ)
- **反論**: Stage 1 で fold 別 regime 分布 verify + Walk-Forward (= 時系列順) で regime 多様性確保・偏りあれば fold 数調整 (= 7 fold or 10 fold) の余地

##### data-driven 経路宣言 (= cc_role §1.4.6.1 改善 12)

- 第二段階 CPCV 採用判定 = Stage 3 NET 純増分 < 2.0× で発動
- fold 数調整判定 = Stage 1 で fold 間性能差 > 30% で 5 → 7 or 10 fold 再評価
- embargo 期間調整判定 = Stage 1 leak verify で疑い検出時に 2 day → 3 day へ拡大

#### 6.2.6 ハイパラ探索

##### 業界 standard verify (= cc_role §1.4.6.1 改善 6・本セッション既 WebSearch 結果活用)

- **LightGBM ハイパラ業界 range** ([[cc_entry_logic_self_study]] §13.1): num_leaves 15-127 / learning_rate 0.01-0.1 / min_child_samples 20-100 / early_stopping_rounds 50-200
- **Optuna (= Bayesian Optimization) が業界主流**: GridSearchCV より計算コスト 1/10・SOTA Hyperparameter tuning
- **3 系統別 tune が業界 standard**: ラベル objective が異なる (= 回帰 / multiclass / binary) ため

##### 教科書整合 (= cc_role §1.4.6.1 改善 7)

- **Lopez de Prado AFML Ch.6 Ensemble Methods**: GBDT のハイパラ調整は cross-validation + early stopping の組合せ
- **Hudson & Thames mlfinlab blog Hyperparameter Tuning**: Optuna による financial ML ハイパラ最適化が業界主流

##### 論点 1. 探索方法 — Optuna (= ベイズ最適化) で軽量探索

###### 採用方針

- **Optuna** で 20-50 trials の Bayesian Optimization 採用
- TPE (= Tree-structured Parzen Estimator) sampler default
- pruner = MedianPruner (= 中央値以下の trial を早期打ち切り)

###### 業界 standard 比較

| 手法 | 計算コスト | 効率 | 採否 |
|---|---|---|---|
| default + 軽 tune | 最小 | 弱 | ❌ Phase 1 v6 と同じ問題回避 |
| GridSearchCV | 最大 (= 候補数の指数) | 網羅的だが非効率 | ❌ 56 モデルで爆発 |
| **Optuna** | 中 (= 20-50 trials) | **業界主流・Bayesian で効率最適化** | ✅ 採用 |

###### regime ensemble §6.1.5 との違い

- regime ensemble = GridSearchCV 64+1 候補 (= 3 判定器 × 4 重み値の grid)
- [2] Entry ML = 56 モデル × ハイパラ多次元探索で GridSearchCV 爆発 → Optuna 採用

##### 論点 2. 探索範囲 — 業界 range + L1/L2 正則化追加

###### 探索範囲

| パラメータ | 範囲 | 役割 |
|---|---|---|
| num_leaves | 15-127 | 木の複雑度 (= 業界 standard) |
| learning_rate | 0.01-0.1 | 学習速度 (= 業界 standard) |
| min_child_samples | 20-100 | 葉の最小サンプル数 (= 業界 standard) |
| early_stopping_rounds | 50-200 | 早期停止 (= 業界 standard) |
| max_depth | -1 (= 無制限) or 3-10 | 木の深さ上限 |
| reg_alpha (L1 正則化) | 0.0-1.0 | over-fitting 抑制 |
| reg_lambda (L2 正則化) | 0.0-1.0 | over-fitting 抑制 |

###### 採用根拠

- §13.1 業界 range 採用 = LightGBM 業界 standard 整合
- L1/L2 正則化追加 = §6.2.4 懸念 2 (= 2,610 列 over-fitting リスク) への構造的対策

###### scoring metric

- 揺れ幅系 (= 回帰) = `objective='regression'` / `metric='rmse'`
- Triple Barrier (= 3 class) = `objective='multiclass'` / `metric='multi_logloss'` + `class_weight='balanced'` (= §6.2.3 論点 4)
- meta_label (= binary) = `objective='binary'` / `metric='binary_logloss'` + `scale_pos_weight` (= §6.2.3 論点 4)

##### 論点 3. 個別 tune vs 共通 tune — 3 系統別 tune

###### 採用方針: 3 系統別 tune

| 系統 | モデル数 | objective | metric | 不均衡対策 |
|---|---|---|---|---|
| 揺れ幅系 (= MFE/MAE pct) | 28 | regression | rmse | なし (= 回帰) |
| Triple Barrier (= 3 class) | 14 | multiclass | multi_logloss | class_weight='balanced' |
| meta_label (= binary) | 14 | binary | binary_logloss | scale_pos_weight |

###### 採用根拠

- 56 モデル個別 tune = 計算コスト 56 倍 (= 実用厳しい)
- 56 モデル共通 tune = ラベル系統の違い (= 回帰 vs 分類 vs 2 値) 無視で精度落ち
- **3 系統別 tune** = 計算コスト 3 倍で系統別最適化

###### tune 結果の適用

- 1 系統内では best hyperparameters を 系統内全モデルに共通適用 (= 揺れ幅系 28 モデル全部に同じハイパラ)
- 系統間では別ハイパラ (= 揺れ幅系と Triple Barrier で別 num_leaves 等)

##### 論点 4. 計算コスト制約 — 数時間〜10 時間想定で実用範囲

###### 試算

- 3 系統 × Optuna 30 trials × Walk-Forward 5 fold = 450 学習
- 1 学習あたり時間 = LightGBM 5 fold で 1-2 分想定 (= Phase 1 v6 経験)
- 合計 = 450 × 1.5 分 = **約 11 時間** (= CPU only 環境で 1 日以内実用範囲)

###### 比較

- Phase 1 v6 経験 = 14 ラベル × default × 5 fold = 約 1-2 時間
- 本提案 = 56 ラベル × 30 trials × 5 fold / 3 系統共通 tune = 約 11 時間 (= 工数 5-10 倍)

###### 段階的アプローチ

- 第一段階 = Optuna 30 trials で動作確認
- 第二段階 (= Stage 1 結果次第) = 50 trials に拡張 or 個別 tune に拡張検討

##### 論点 5. stacking ハイパラ接続 — 第一段階 LightGBM のみ・第二段階 meta-learner 別 tune

###### 第一段階 (= §6.2.6 本セクション)

- LightGBM 56 個のハイパラ Optuna tune のみ
- meta-learner ハイパラは扱わない (= stacking 採否未定)

###### 第二段階 (= Stage 3 後 stacking 採用時)

- §6.2.2 第二段階 stacking 採用判定後 (= Stage 3 NET 純増分 (b)/(a) ≥ 1.3×) に meta-learner ハイパラ別 tune
- 候補 meta-learner = Logistic Regression / Random Forest / Ridge
- meta-learner ハイパラ tune も Optuna で 20-30 trials 想定

##### 業界 standard との差分 (= cc_role §1.4.6.1 改善 8)

- **業界 standard** = LightGBM ハイパラ Optuna + 業界 range + objective 別 tune + Walk-Forward CV
- **本提案** = 業界 standard 整合・L1/L2 正則化追加で over-fitting 抑制強化
- **違い**: 56 モデルを 3 系統共通 tune (= 計算コスト優先・個別 tune は第二段階)

##### cat-bitget 固有 verify (= cc_role §1.4.6.1 改善 10)

- Phase 1 v6 で LightGBM default + 5 fold 実装済 → Optuna 移行は incremental
- regime ensemble §6.1.5 で GridSearchCV 採用済 → 本案 Optuna は計算コスト制約での選択
- 旧 Priority v9 (= cat_v9 P1-P25) はハイパラ tune 不要の固定ルール → ML 化で新規 tune

##### 統計指標と PnL 指標の分離 (= cc_role §1.4.6.1 改善 9)

- ハイパラ tune scoring = **統計指標** (= RMSE / multi_logloss / binary_logloss)
- Stage 3 PnL 評価 = **PnL 指標** (= 月次 NET 純増分)
- 統計指標で best ハイパラ採用 → Stage 3 で PnL 検証の 2 段階構造

##### 設計判断の根拠 4 件

1. **Optuna 採用**: 業界主流 (= GridSearchCV より効率)・56 モデル計算量制約に対応
2. **3 系統別 tune**: 個別 tune (= 56 倍) は実用厳しい・共通 tune は精度落ち・3 系統が cost/精度 trade-off で中央値
3. **L1/L2 正則化追加**: §6.2.4 over-fitting 懸念への構造的対策
4. **段階的アプローチ**: 第一段階 30 trials + 第二段階拡張 / 第二段階 stacking meta-learner 別 tune

##### 懸念 2 件 + 反論

- **懸念 1**: Optuna 30 trials で最適ハイパラ近傍に到達できない可能性
  **反論**: Stage 1 で fold 別性能差 verify + 結果不足なら第二段階 50 trials 拡張経路あり

- **懸念 2**: 3 系統共通 tune は 1 系統内 28/14/14 ラベルの個性を捨てる
  **反論**: ラベル系統内では objective 同一 (= 回帰 / 分類 / 2 値) で構造類似・系統内個別 tune は計算コスト 56 倍で実用厳しい

##### data-driven 経路宣言 (= cc_role §1.4.6.1 改善 12)

- 第二段階 trials 拡張判定 = Stage 1 で系統別 best score の fold 間性能差 > 30% で 30 → 50 trials 拡張
- 第二段階 個別 tune 採用判定 = Stage 1 系統内モデル間性能差 > 20% で個別 tune (= 計算コスト 18 倍) 検討
- L1/L2 正則化適用判定 = Stage 1 train/valid gap > 20% で正則化強化 (= reg_alpha/reg_lambda 上限拡大)

#### 6.2.7 出力 → entry 判定

> **§6.2.7 集約 → entry 判定 現設計（暫定・⚠️ /audit 検証中）**:
>
> - 集約式: `LONG_score = TP_prob × 0.4 + MFE_pct_normalized × 0.3 + meta_yes × 0.3`（MFE は `clip(MFE_pct / MFE_pct_train_p95, 0, 1)` の min-max scaling・重み 0.4/0.3/0.3）
> - threshold: data-driven（月 275 件確保する quantile・暫定 0.477）
> - 実績: E variant で 7,424 entry / 月 275 件 ✅ / ただし LONG:SHORT 348:7,076（SHORT 偏り 1:20 は構造的・未解決）
> - ⚠️ /audit で「**決着主軸（Triple Barrier 中心）+ 揺れ幅を集約から除外 + meta をカスケード化**」への変更を検証中（2026-05-30 baseup）
>
> 実測経緯（scale mismatch 発覚・z-score 6倍乖離→MFE 97%支配・5 variant 比較・MFE 予測困難の業界 verify）は [`ml_pipeline_execlog.md`](ml_pipeline_execlog.md) 工程 [2] 参照。

##### 業界 standard verify (= cc_role §1.4.6.1 改善 6・本セッション 2026-05-27 WebSearch 2 件機械運用)

- **集約パターン業界 3 系統** ([arxiv 2501.10709 Revisiting Ensemble Methods 2025](https://arxiv.org/html/2501.10709v1)): majority voting / weighted soft voting / rule-based threshold
- **rule-based ensembles で precision 0.85 + 低発動率達成事例** (= 業界トップ水準)
- **業界実証 threshold 0.6 buy / 0.4 sell / 中間 hold** = NN/LSTM/GRU 重み付き ensemble + threshold ベース
- **AFML Meta-Labeling primary + secondary 接続**: [pm-research Meta-Labeling Calibration Position Sizing 2025](https://www.pm-research.com/content/iijjfds/5/2/23) / [Hudson & Thames meta-labeling GitHub](https://github.com/hudson-and-thames/meta-labeling) で secondary が「利益確率 estimate + calibration → Half-Kelly で size 決定」が業界 standard
- **mlfinlab Triple-Barrier and Meta-Labelling 実装**: [mlfinlab tb_meta_labeling docs](https://www.mlfinlab.com/en/latest/labeling/tb_meta_labeling.html)

##### 教科書整合 (= cc_role §1.4.6.1 改善 7)

- **Lopez de Prado AFML Ch.3 Meta-Labeling**: primary (= 方向予測) + secondary (= TP 到達確率 + size 判定) の二段構造
- **AFML Ch.6 Ensemble Methods**: stacking / soft voting / hard voting の使い分け

##### 論点 1. 56 予測値 → entry_score 集約方法 (= まこさん判断「段階的 = 第一段階ルール集約 + 第二段階 meta-learner」採用)

###### 第一段階: ルール集約 (= 案 A・人が決めた式で集約・CP2 監査 C2 反映で MFE_pct 標準化追加)

**集約式 (= CP2 監査 C2 反映後)**:
```
# CP2 監査 C2 反映: MFE_pct を z-score 標準化してから集約 (= scale 整合確保)
LONG_MFE_pct_normalized  = (LONG_MFE_pct  - LONG_MFE_pct_train_mean)  / LONG_MFE_pct_train_std
SHORT_MFE_pct_normalized = (SHORT_MFE_pct - SHORT_MFE_pct_train_mean) / SHORT_MFE_pct_train_std

# CP2 監査 C1 反映: TP_prob / meta_yes_prob はキャリブレーション後の値を使用 (= §6.2.3 論点 4)
LONG_score  = LONG_TP_prob_calibrated  × 0.4 + LONG_MFE_pct_normalized  × 0.3 + LONG_meta_yes_prob_calibrated  × 0.3
SHORT_score = SHORT_TP_prob_calibrated × 0.4 + SHORT_MFE_pct_normalized × 0.3 + SHORT_meta_yes_prob_calibrated × 0.3
```

- z-score 標準化は **train_2021_2024 fold 別 mean / std** で計算 (= leak 防止)
- 第二段階 (= Stage 1 結果次第) で 0-1 ratio 化 (= `MFE_pct / MFE_pct_train_p95`) に切り替え検討

###### K (= 予測ホライズン) 重み付け: 等重み (= CP2 監査 M1 反映・短期 K 重視から再設計)

- **全 7 ホライズン (K=6/12/24/48/96/144/288) に等重み 1/7 ≈ 0.143** 採用
- 第二段階 (= Stage 1 fold 別 K 別 feature_importance + 系統別 RMSE/F1/AUC で data-driven 調整) で短期 K 重視 / 長期 K 重視 / その他 重み set を再 calibrate

**再設計の根拠** (= CP2 監査 M1):
- 旧設計「短期 K 0.5 / 他 0.1」は **Phase 1 v6 教訓「予測対象を物理的に増やす (= 14 → 56 ラベル)」と集約段階の重み付けで論理整合しない** = 56 ラベル並列で物理的に増やしたのに、出力集約で 5/7 のホライズン情報を 1/7 (= 14%) 未満に圧縮する設計矛盾
- 等重みから出発し data-driven 調整経路で「集約段階で人為的に圧縮しない」設計に統一
- 月 275 件確保ライン制約は threshold 0.6 + fold 別 calibrate (= §6.2.7 論点 4) で達成し、K 重み制約と decouple

###### 第二段階: meta-learner 学習 (= 案 C)

- §6.2.2 第二段階 stacking 採用判定後 (= Stage 3 NET 純増分 (b)/(a) ≥ 1.3×) に meta-learner 追加
- meta-learner = Logistic Regression / Random Forest / Ridge 候補
- 入力 = 56 予測値 (= LightGBM) + 56 予測値 (= XGBoost・stacking 時) = 計 112 予測値
- 出力 = entry_score 直接学習

###### 採用根拠 3 件

1. **業界実証 rule-based precision 0.85** ([arxiv 2501.10709]): 第一段階で業界トップ水準達成可能性
2. **解釈性 + デバッグ容易性**: 第一段階で「なぜ entry したか」を ML pipeline 動作確認で説明可能
3. **段階的アプローチ**: §6.2.2 第二段階と連動・Stage 3 結果次第で複雑化

##### 論点 2. direction (= LONG/SHORT/NONE) 確定方法 (= まこさん判断「排他 = cat_v9 流」採用)

###### 採用方針: 排他 (= 1 bar 1 trade)

- LONG_score > SHORT_score かつ LONG_score > threshold → **LONG**
- SHORT_score > LONG_score かつ SHORT_score > threshold → **SHORT**
- 上記いずれも該当しない → **NONE** (= entry しない)

###### 採用根拠 3 件

1. **cat_v9 整合**: check_entry_priority と同型 (= スタートライン整合・cc_role §1.7)
2. **ポジション管理シンプル**: 1 bar 1 trade で矛盾エントリー回避
3. **0.12 BTC 合計上限制約と整合**: false_positive §0-2 Prime Directive 同型予防

###### hedging (= 両建て) 戦略の代替経路

- [2.5] cluster 工程で「LONG cluster / SHORT cluster」を作って同時保有実現
- 1 bar 1 entry でも複数 bar をまたいで LONG cluster + SHORT cluster の同時保有可能
- = hedging 戦略は工程横断で吸収

##### 論点 3. confidence (= 確信度) 算出 (= CC 決着)

###### 採用方針

- **confidence = | LONG_score - SHORT_score | / max(LONG_score, SHORT_score)**
- 0.0 - 1.0 の範囲 (= 1.0 に近いほど確信度高)
- 例: LONG_score = 0.8 / SHORT_score = 0.2 → confidence = (0.8 - 0.2) / 0.8 = 0.75 (= 高確信度)

###### 採用根拠

- regime ensemble §6.1.5 「最高確率 - 2 番目確率」と同型構造 (= 工程一貫性)
- 後段 [3] Sizing で「confidence 高い entry = size 大きく」の Half-Kelly 入力として使用

##### 論点 4. threshold (= 発動ライン) 動的 vs 固定 (= まこさん判断「第一段階固定 + 第二段階動的検討」採用)

###### 第一段階: 固定 threshold

- entry_score > **暫定 0.6** で entry (= 業界実証値・[arxiv 2501.10709] threshold 0.6 buy 整合)
- 即死リスク (= **危険度 > 0.9**) 検出時のみ reject (= §1 既決着)
- **危険度 定義** (= CP2 監査 M2 反映): **第一段階 = `LONG_SL_prob > 0.9` (= Triple Barrier 3 class の SL hit probability・キャリブレーション後の値)** 採用 (= Triple Barrier 直接出力で算出簡単 + 解釈性高)
  - LONG entry: `LONG_SL_prob > 0.9` で reject
  - SHORT entry: `SHORT_SL_prob > 0.9` で reject
- **第二段階** (= Stage 1 結果次第): 危険度算出式の改訂候補
  - (a) `危険度 = SHORT_score / (LONG_score + SHORT_score)` (= 反対方向確信度が高い場合 reject)
  - (b) `危険度 = ATR_pct × LONG_score / max_ATR_pct_train_2021_2024_p95` (= 高ボラ + 低確信時 reject)
- 月 275 件確保ライン = Stage 1 で fold 別 entry 件数 verify → threshold 再 calibrate

###### 第二段階 (= Stage 1 結果次第): 動的 threshold 検討

- regime 別 threshold (= UPtrend 時 LONG threshold 下げ / DOWNtrend 時 SHORT threshold 下げ)
- 時間帯別 threshold (= 流動性低い時間帯は threshold 上げ)
- cluster 別 threshold (= スキャル cluster vs 平均建値 cluster)

###### data-driven calibrate 経路

- Stage 1 で month 別 entry 件数 + month 別 NET proxy verify
- 月 275 件未達 (= 月 < 200 件) → threshold 0.6 → 0.5 に下げる
- 月 275 件大幅超過 (= 月 > 400 件) → threshold 0.6 → 0.7 に上げる
- fold 別 calibrate で 25th / 75th percentile から決定

##### 論点 5. AFML Meta-Labeling primary + secondary 接続 (= CC 決着)

###### 採用方針

- **primary** = Triple Barrier 3 class 予測 (= LONG/SHORT/0 方向)
- **secondary** = meta_label 2 値予測 (= TP 到達確率 yes/no)
- **接続**: primary 出力 + secondary 出力を §6.2.7 集約式 (= 論点 1) で合体 → entry_score 算出 → [3] Sizing 工程に渡す
- [3] Sizing で **Half-Kelly** (= phase_flow_v4 v7 §改善 4 整合) で position size 決定

###### 業界 standard 整合

- [pm-research Meta-Labeling 2025] = secondary が利益確率 estimate + calibration → Half-Kelly で size 決定
- 本提案 = 同型 + cat-bitget 制約 (= 0.12 BTC 合計上限) の clip 必須

##### 論点 6. stacking 採用時の集約 (= §6.2.2 第二段階・CC 決着)

###### 採用方針 (= Stage 3 NET 純増分 (b)/(a) ≥ 1.3× で発動)

- **stacking 構造** = LightGBM 56 個出力 + XGBoost 56 個出力 → meta-learner が集約
- **meta-learner 候補** = Logistic Regression / Random Forest / Ridge
- **meta-learner ハイパラ** = Optuna 20-30 trials で別 tune (= §6.2.6 第二段階)

###### §6.2.2 第二段階出口設計と整合

- stacking 採用判定 = Stage 3 NET 純増分 (b)/(a) ≥ 1.3×
- 第三段階 = GBDT + DL (= GRU/Transformer) stacking 検討 (= 計算コスト 3-10 倍)

##### 業界 standard との差分 (= cc_role §1.4.6.1 改善 8)

- **業界 standard** = rule-based threshold + 排他 + 固定 threshold + Meta-Labeling primary/secondary
- **本提案** = 業界 standard 整合・全 6 論点で業界主流踏襲
- **違い**: 短期 K 重視 (= K=12/24 重み 0.5) = cat-bitget 固有 (= 月 275 件確保ライン制約)

##### cat-bitget 固有 verify (= cc_role §1.4.6.1 改善 10)

- 短期 K 重視 = cat_v9 スキャル系 (= P1, P3, P21, P25 = MAX_ADDS=1) 整合
- 排他 LONG/SHORT = cat_v9 check_entry_priority と同型
- threshold 0.6 = 業界実証値 + Stage 1 で fold 別 calibrate
- 0.12 BTC 合計上限 = false_positive §0-2 Prime Directive 整合

##### 統計指標と PnL 指標の分離 (= cc_role §1.4.6.1 改善 9)

- entry_score / direction / confidence = **統計指標** (= ML 予測値)
- threshold 通過後の entry 件数 + 月次 NET = **PnL 指標** (= Stage 3 評価対象)
- Stage 1 で統計指標妥当性 + Stage 3 で PnL 検証の 2 段階構造

##### 設計判断の根拠 4 件

1. **段階的アプローチ** (= 第一段階ルール集約 + 第二段階 meta-learner / 第一段階固定 + 第二段階動的): 業界実証 + 解釈性優先 + Stage 3 結果次第で複雑化
2. **cat_v9 整合** (= 排他 LONG/SHORT + 短期 K 重視): スタートライン整合 + 月 275 件確保ライン
3. **業界 standard 整合**: rule-based threshold + Meta-Labeling + Half-Kelly 接続
4. **regime ensemble §6.1.5 と同型構造**: confidence 算出方法 + 工程設計一貫性

##### 懸念 3 件 + 反論

- **懸念 1**: ルール集約の重み (= 0.4 / 0.3 / 0.3) が arbitrary・cat-bitget で最適か不明
  **反論**: Stage 1 で fold 別 entry_score 分布 verify + Stage 3 PnL 比較で重み再 calibrate 経路あり

- **懸念 2**: 短期 K 重視 (= 0.5 / 0.1) で長期 K の予測情報を捨てる
  **反論**: 長期 K も 0.1 重みで残す (= 完全排除ではない) + Stage 1 K 別 feature_importance verify で重み再評価可能

- **懸念 3**: 第一段階固定 threshold 0.6 が cat-bitget で最適か不明
  **反論**: data-driven 経路 (= 月 275 件確保ラインで fold 別 calibrate) + 第二段階動的検討経路あり

##### data-driven 経路宣言 (= cc_role §1.4.6.1 改善 12)

- ルール集約重み 0.4/0.3/0.3 の調整判定 = Stage 1 で fold 別 entry_score 分布 + Stage 3 PnL 比較で純増分 < 1.5× で再 calibrate
- 短期 K 重視 0.5/0.1 の調整判定 = Stage 1 K 別 feature_importance で長期 K dominant なら 0.3/0.2 へ再 calibrate
- threshold 0.6 の調整判定 = Stage 1 で fold 別 entry 件数 verify → 月 < 200 件で 0.5 / 月 > 400 件で 0.7
- 第二段階 meta-learner 採用判定 = Stage 3 NET 純増分 < 1.5× で発動
- 第二段階動的 threshold 採用判定 = Stage 3 regime 別 NET 偏り > 30% で発動

#### 6.2.8 leak 防止

##### 業界 standard verify (= cc_role §1.4.6.1 改善 6・本セッション既 WebSearch 結果活用)

- **Lopez de Prado AFML Ch.3 Look-Ahead Bias 防止**: shift(-N) / center=True / 期間全体集計の禁止
- **AFML Ch.7 Purged K-Fold + Embargo**: ラベル生成期間の重複除外 + train/test 間 buffer
- **[arxiv 2512.12924 Walk-Forward Validation Framework 2025](https://arxiv.org/pdf/2512.12924)**: out-of-sample 検証は walk-forward + embargo が業界 standard

##### 教科書整合 (= cc_role §1.4.6.1 改善 7)

- **Lopez de Prado AFML Ch.3 Why is Cross-Validation Failing in Finance?**: 時系列依存性 + ラベル overlap で K-Fold 直接適用は危険
- **AFML Ch.7 Cross-Validation in Finance**: Purged K-Fold + Embargo の組合せが業界主流

##### 第一原則: 全工程で「t 時点で取得可能な変数のみ使う」 (= false_positive §0-1 Prime Directive 整合)

- 特徴量 / ラベル / Entry/Exit/Replay/PnL 計算の全工程で「本番運用の推論時点 t で因果的に取得可能」な変数のみ使用
- 違反時 = false_positive §2 類型 A (= 未来データ参照) 最重大インシデント扱い

##### 項目 1. feedback_ml_leak_mandatory_check 4 点 verify (= 既決着引継ぎ)

###### 4 点 verify 仕様 ([[feedback_ml_leak_mandatory_check]] 整合)

| # | verify 項目 | 実装方法 |
|---|---|---|
| 1 | **特徴量 grep** | `shift(-` / `center=True` / `j+1` / `j+2` / `future` / `look_ahead` の文字列を全特徴量スクリプトで grep・検出 0 件 verify |
| 2 | **使用箇所 verify** | 怪しい列名 (= fractal / pivot / resistance / support) の使用箇所を grep + 因果性 1 行宣言 |
| 3 | **timestamp range** | train_2021_2024 末 < test_2025 始 < test_2026_q1 始 を parquet min/max で確認 |
| 4 | **feature_importance 即時 review** | top 20 feature を各モデル学習直後に出力 + blacklist 由来混入なし verify |

###### CC 着手前後義務 (= [[feedback_ml_leak_mandatory_check]])

- ML 系作業前: 4 点 verify を実施 + チャットに証跡提示
- ML 系作業後: 完了報告に「leak 4 点 verify pass」と明記

##### 項目 2. regime 6 列の causal alignment (= §6.1.6 既決着引継ぎ)

###### 既決着仕様 (§6.1.6)

- 1h regime 判定の bar close 時刻 = bar_start + 1h
- `merge_asof(direction="backward")` で 5m bar へ充当
- 1h bar `14:00-14:59` の判定は **15:00 以降の 5m bar** (= 15:00 / 15:05 / ... / 15:55) にのみ充当可能
- 14:00-14:55 の 5m bar には充当不可 (= look-ahead leak 防止・L-128 / L-179 同型予防)

###### [2] Entry ML 実装での verify

- regime 6 列が `regime_predictions_*.parquet` で既に causal alignment 済 (= regime ensemble §6.1.6 実装で完了)
- [2] Entry ML は merge 済 parquet を読み込むだけ → causal violation なし

###### assert 文の伝播

- §6.1.6 で `assert no look-ahead in regime forward fill` を実装済 (= scripts/priority_rebuild/regime_output_5m.py)
- [2] Entry ML 学習スクリプトでも regime 6 列の timestamp 整合を assert で再 verify

##### 項目 3. ラベル shift(-K) の verify (= phase_compliance §0 Step 5 既決着引継ぎ)

###### 既決着仕様 (phase_compliance §0 Step 5.1)

- ラベル側 shift(-K) は推論時に X に含めない (= L-154 確定)
- build_labels.py L200-201 / build_labels_pct.py L219-220 で `fut_max_high = h.shift(-K).rolling(K).max()` を確認済
- = ラベル側 leak だが「ラベル生成時のみ」「X に含めない」で類型 A 該当せず

###### [2] Entry ML 実装での verify

- 56 ラベルが `labels_mfe_mae_pct_*.parquet` で既に shift(-K) 適用済 (= Phase 0 v3.1 で実装完了)
- [2] Entry ML 学習スクリプトは X (= 2,610 列) と y (= 56 ラベル) を分けて読み込む
- y には shift(-K) 含まれるが X には含まれない構造 → leak なし

##### 項目 4. CV embargo (= §6.2.5 既決着引継ぎ)

###### 既決着仕様 (§6.2.5 論点 3)

- embargo = K_max 288 bar (= 24h) + buffer 1 day = **2 day (= 576 bar)**
- 各 fold で train と test 間に embargo 設定

###### [2] Entry ML 実装での verify

- AFML mlfinpy `PurgedKFold` ライブラリで embargo パラメータ指定
- fold 別 train/test 範囲を log で出力 → embargo > 2 day を assert で verify

##### 項目 5. feature_importance top 20 自動 monitoring (= 既決着引継ぎ + 拡張)

###### 既決着仕様 (phase_compliance §1.4)

- LightGBM 学習完了直後に feature_importance top 20 を出力
- blacklist 由来 (= sma_20 / sma_50 / ichimoku_kijun / ichimoku_tenkan / macd_line / macd_signal / macd_hist / macd_hist_change) のいずれかが混入 → 即 STOP

###### [2] Entry ML での拡張 (= §6.2.4 整合)

- 56 モデル全部について feature_importance top 20 を出力
- 各モデル独立評価 + 56 ラベル間で top 20 feature 重複度 verify (= §6.2.2 「56 ラベル間予測相関」と整合)
- regime 6 列が top N% (= top 50) に入っているか verify (= §6.2.4 論点 2「regime 引継ぎ機能性 verify」整合)

###### 拡張: 怪しい列名検出

- top 20 に未来参照疑い列名 (= fractal / pivot / resistance / support / future) が含まれていないか自動検出
- 検出時 = 即 STOP・調査必須 ([[feedback_ml_leak_mandatory_check]] 同型)

###### CP2 監査 Minor-1 反映: fractal ベース列ブラックリスト 3 段階運用適用

- [phase_compliance §1.4](../rules/phase_compliance_checklist.md) 「fractal ベース列ブラックリスト 3 段階運用 (= top1-20 hit 時の物理 leak verify 4 項目セット)」を 56 モデル全部に適用
- 4 項目セット = (i) lag-1 shift 不変性 / (ii) 末尾 K bars NaN pattern / (iii) 二重 N サフィックス内外一致 / (iv) importance gain single<50%
- 実装 = `verify_top20_features_leak.py` を 56 モデル × 5 fold で自動実行
- 全 4 項目 PASS → 警告ログ + 続行可 / 1 項目でも FAIL or SKIP → 即 STOP・調査必須

##### 項目 6. blacklist 64 列除外 verify (= phase_compliance §-1 既決着引継ぎ)

###### 既決着仕様 (phase_compliance §-1)

- USD 絶対値系 64 列 (= 8 family × 8 TF) を train 前に drop
- `X = df.drop(columns=BLACKLIST_COLS)` で実装
- 完了報告で「blacklist drop 件数 = 64」「学習対象 feature 数 = 2,604」明示

###### [2] Entry ML 実装での verify

- 学習開始前に BLACKLIST_COLS load + drop
- assert `len(X.columns) == 2604 + 6` (= 2,604 列 + regime 6 列 = 2,610 列)
- feature_importance top 20 に blacklist 由来 (= sma/ichimoku/macd 系) 混入なし verify (= 項目 5 整合)

##### 業界 standard との差分 (= cc_role §1.4.6.1 改善 8)

- **業界 standard** = AFML Ch.7 Purged K-Fold + Embargo + Walk-Forward + feature grep 等
- **本提案** = 業界 standard 整合 + cat-bitget 固有の blacklist 64 列除外 + regime 6 列 causal alignment 同型予防
- **違い**: feedback_ml_leak_mandatory_check 4 点 verify を CC 自己申告ベースから機械的証跡ベースに昇格 (= L-179 教訓・cc_role §1.4 #5 「読んだフリ・確認したフリ」防止)

##### cat-bitget 固有 verify (= cc_role §1.4.6.1 改善 10)

- L-179 (= fractal j+2 leak が Phase 1-7a 全段素通り) 同型予防経路あり
- L-128 (= MA70 look-ahead leak) 同型予防経路あり
- regime ensemble §6.1.6 で causal alignment + assert 実装済 → [2] Entry ML も同型適用
- Phase 0 v3.1 で leak verify 4 点 pass 済 (= phase_compliance §0 Step 5 通過)

##### 統計指標と PnL 指標の分離 (= cc_role §1.4.6.1 改善 9)

- leak 防止は **統計指標** (= Stage 1 / Stage 2 評価精度) の信頼性確保
- leak 検出時 = Stage 3 / Stage 4 PnL 評価が無意味になる (= 過大評価リスク)
- = Stage 1 で leak verify 完了が Stage 3 / Stage 4 評価の前提条件

##### 設計判断の根拠 4 件

1. **feedback_ml_leak_mandatory_check 4 点 verify 必須**: L-179 + L-128 教訓・cat-bitget 固有 leak 事案 2 件の同型予防
2. **regime ensemble §6.1.6 同型適用**: causal alignment + assert 実装で工程一貫性
3. **既決着事項の re-verify**: phase_compliance §-1 / §0 / §1.4 既決着事項を [2] Entry ML 実装でも引継ぎ
4. **機械的証跡ベース**: CC 自己申告ベースから機械的証跡 (= grep / assert / log 出力) ベースに昇格

##### 懸念 1 件 + 反論

- **懸念**: 56 モデル全部について feature_importance top 20 review = 計算コスト + 人手レビュー負荷大
  **反論**: 自動 monitoring + 怪しい列名検出で即 STOP 経路あり・人手レビューは異常検出時のみ実施

##### data-driven 経路宣言 (= cc_role §1.4.6.1 改善 12)

- feature_importance top 20 異常検出判定 = blacklist 由来 / 未来参照疑い列名 (= fractal / pivot / resistance / support / future) 検出で即 STOP
- timestamp range 違反判定 = train 末 ≥ test 始 で即 STOP
- embargo 違反判定 = fold 別 train/test 間 < 2 day で即 STOP
- regime 6 列 causal violation 判定 = assert no look-ahead 失敗で即 STOP

---

### 6.3 工程 [2.5] cluster 分類 詳細設計

> ## ✅ CP3 監査 PIVOT 全 7 件反映完了 (= 2026-05-27 同セッション内反映・v3.10)
>
> 本セクション §6.3.0〜§6.3.7 は CP3 監査 (= `.claude/audits/2026-05-27_step25_cluster_design_cp3_audit_report.md` 422 行) Verdict PIVOT の **Critical 3 + Major 3 + Minor 1 = 全 7 件採用支持で同セッション内反映完了**。
>
> **反映内容**:
>
> - **Critical-1**: silhouette > 0.3 → **> 0.4** (= 業界 weak 0.25 + reasonable 0.5 中間・PCA 後高次元現実的目標) + 旧 14 列版 0.15-0.20 架空推定値破棄 → **実装着手時に Phase 4-a artifact で実測確定**
> - **Critical-2**: k-means 単体 → **K-Means + GMM hybrid** (= 楕円対応 + posterior probability native・業界実装事例あり) + HDBSCAN 不採用根拠を「k 不安定」→「min_cluster_size で対応可能だが第二段階保留」に修正
> - **Critical-3**: Gaussian kernel → **fold 別 Isotonic Regression キャリブレーション** + Stage 1 に **Brier score / reliability diagram / ECE** 追加 (= CP1/CP2 同型対策)
> - **Major-1**: 派生 one-hot 推奨 → **cluster_id 直接食わせ** (= LightGBM 4.6 native categorical 業界 standard) + one-hot 列は第二段階保留
> - **Major-2**: Critical-1 反映で「架空推定値の実測値偽装」が実質解消 → 追加対応不要 (= 全項目試算は実装そのものになる論理整合)
> - **Major-3**: Stage 3 純増分 1.5× を **cluster + Sizing + Exit 3 工程合算寄与** と明示 (= cluster 単独責任ではない)
> - **Minor-1**: §6.3.7 leak 経路 7 項目目「**entry_id 未来情報依存禁止**」追加 + §6.3.5 再命名後の Stage 1 silhouette/Brier/ECE 再 verify 経路追加
>
> **構造的対策** (= L-236 / cc_role §1.4.6.2 物理強制経路):
>
> - ガード追加経路打ち切り + 物理強制 hooks 導入 (= `.claude/settings.local.json` + `.claude/hooks/check_websearch_before_design_write.sh` + `update_websearch_marker.sh`)
> - ml_pipeline_baseline への Write/Edit 前 10 分以内 WebSearch 必須を hook で物理阻止
> - CC 慢心怠慢への罰則機能を WORKFLOW 改訂49 active で明示
>
> 参照: lessons L-236 / WORKFLOW.md 改訂49 active / CP3 監査結果

> **§6.3 cluster 現設計（確定値・2026-05-30 実測で確定・⚠️ 一部 /audit 検証中）**:
>
> | 項目 | 現設計 |
> |---|---|
> | 入力 | 揺れ幅予測 28 列のみ（PCA なし） ⚠️ /audit で「Triple Barrier 予測（質軸）への変更」検証中 |
> | アルゴリズム | KMeans 単体 |
> | 確率 | KMeans 距離 softmax（校正省略・後段で本気使用時は temperature scaling 再校正経路を残す） |
> | k（グループ数） | 4 |
> | 門番 | silhouette 緩和（weak 0.25 超で先へ・有効性は Stage 3 PnL で判定） |
>
> 偏り cluster2=61% + 命名重複の品質課題は未解決。実測経緯（机上設計がなぜ覆ったか・silhouette 数値の変遷・前処理欠陥3件・教訓 L-236-B）は [`ml_pipeline_execlog.md`](ml_pipeline_execlog.md) 工程 [2.5] 参照。

#### 6.3.0 概要

工程 [2] Entry ML 後段に独立工程として配置・教師なし学習 (= 正解ラベルなし) で Entry trade の質を自動分類 (= スキャル型 / 長期型 / 危険型 / 凡庸型等)・グループ別 [3] Sizing / [4] Exit で**戦略並立 1.5× レバー寄与** ([industry_benchmark §2.3](industry_benchmark_knowledge_base.md) 業界実証 1.2-1.8× 中央値)。本セクション §6.3.1〜§6.3.7 は 2026-05-27 セッション議論 (= ベースアップ KB Read + WebSearch 5 件 + 教科書整合) を経て決着。

詳細議論順序: §6.3.3 入力 → §6.3.2 アルゴリズム → §6.3.4 k 数 → §6.3.1 評価 → §6.3.5 ラベル付け → §6.3.6 出力 → §6.3.7 leak (= ロジック上流から下流)。本書では検索性のため番号順で記載。

#### 6.3.1 評価方法

##### 目的

cluster 分けが「効いてる」と言える基準を段階別に固定する。各段階の合否ラインを決めずに進むと「分かれた気がする」で進めるリスク (= Phase 4-a §4a.5 K96 SHORT q99 が独立 cluster に分離されない事案同型)。

##### 4 段階構造 (= §6.1.1 / §6.2.1 と同型)

| 段階 | 何を見る | 合否ライン |
|---|---|---|
| **Stage 1** | グループ分けの統計的質 | silhouette score > 0.4 (= 業界 weak 0.25 + reasonable 0.5 の中間・PCA 後高次元現実的目標) + inertia + 偏り + regime 相関 + 旧 14 列版実測値比較 (= CP3 Critical-1 反映) |
| **Stage 2** | まこさん視認 + 分布チェック | グループ別予測値分布が見て区別がつく + Exit 抜き PnL proxy |
| **Stage 3** | [3]/[4] 完成後の PnL 早期判定 | **純増分 (b)/(a) ≥ 1.5×** (= cluster あり vs なしの倍率) |
| **Stage 4** | Phase 5 全 12 ヶ月 Replay 最終 PnL | **月次 NET ≥ $1,900 全月クリア** |

##### Stage 1 詳細 (= 統計層・教師なし)

| verify 項目 | 合否基準 | 不合格時の対応 |
|---|---|---|
| silhouette score | > 0.3 (= 業界 minimum・[scikit-learn 公式](https://scikit-learn.org/stable/modules/clustering.html#silhouette-coefficient)) | §6.3.2 第二段階 (GMM / HDBSCAN / ensemble) 検討 |
| inertia | グループ内分散・k 候補間で elbow 確認 | k 数 §6.3.4 再判定 |
| cluster 別 trade 数の偏り | 最小 cluster ≥ 5% | k 数 §6.3.4 調整 |
| regime cluster との予測誤差相関 | Pearson < 0.5 (= [KB §2.3 Square Root Rule 前提](industry_benchmark_knowledge_base.md)) | 入力特徴量 §6.3.3 重複削減 |
| 旧 14 列版 (= Phase 4-a) との比較 | **実装着手時に Phase 4-a artifact `predictions_train_2021_2024_k12long_refit.parquet` で実測 silhouette を算出** (= CP3 Critical-1 反映・旧 0.15-0.20 推定値を実測値で置換)・新 PCA 版が実測値 + 50% 以上で改善判定 | §6.3.3 入力再設計 |
| **Brier score** (= CP3 Critical-3 反映・cluster_prob 品質評価) | < 0.15 (= 業界 standard・[CP1/CP2 監査と同型]) | Isotonic Regression → Platt Scaling 切替検討 |
| **reliability diagram** (= CP3 Critical-3 反映) | 視覚評価で乖離小 (= 対角線近似) | 同上 |
| **ECE** (= Expected Calibration Error・CP3 Critical-3 反映) | < 0.10 (= 業界 standard) | 同上 |

##### Stage 2 詳細 (= 視認 + PnL proxy)

- まこさん月単位視認 (= dashboard・cluster_label 別 trade 散布図 / 予測値分布)
- グループ別 TP_prob / MFE / SL_prob / 保有時間の分布が見て区別がつく
- Exit 抜き PnL proxy (= 仮 Exit 想定で cluster 別 PnL 計算・Phase 1 v6 教訓「統計と PnL 乖離の早期検出」)

##### Stage 3 詳細 (= PnL 早期判定・CP3 Major-3 反映)

- [3] Sizing + [4] Exit 実装後の比較:
  - (a) **cluster + Sizing + Exit すべて統合なし版** (= [3]/[4] が cluster_id を入力に含まず一律処理) = base line
  - (b) **cluster + Sizing + Exit すべて統合あり版** (= [3]/[4] が cluster_id 別に最適化処理)
- **合格 = (b)/(a) ≥ 1.5× (= 3 工程合算寄与・CP3 Major-3 反映)** ([industry_benchmark §2.3](industry_benchmark_knowledge_base.md) 戦略並立 1.2-1.8× 中央値整合・「3-5 戦略並立で 1.5× Sharpe 改善」は **戦略並立全体** の数値で cluster 単独ではない)
- 不合格 (= < 1.3×) なら §6.3.2 アルゴリズム / §6.3.3 入力 / §6.3.4 k 数を再設計
- **責任分担明示**: 1.5× は cluster + Sizing + Exit 3 工程の協調寄与 (= cluster 単独で 1.5× ではない・cluster 単独寄与は 3 工程比で √1.5 ≈ 1.14× 程度の目安)

##### Stage 4 詳細 (= 最終)

- Phase 5 全 12 ヶ月 Replay (= 8 工程合算後・[CLAUDE.md 目標](../../CLAUDE.md) 整合)
- 月次 NET ≥ $1,900 全月クリア

##### 業界 standard verify (cc_role §1.4.6.1 #6)

- silhouette 業界 standard ([Wikipedia Silhouette](https://en.wikipedia.org/wiki/Silhouette_(clustering)) / [GeeksforGeeks Silhouette](https://www.geeksforgeeks.org/machine-learning/what-is-silhouette-score/)): > 0.7 strong / > 0.5 reasonable / > 0.25 weak。**高次元では curse of dimensionality で値低下しやすい** ([Medium Govindaraj 高次元 K-Means](https://medium.com/@govindarajpriyanthan/clustering-in-high-dimensional-space-building-and-evaluating-a-custom-k-means-algorithm-49802d63a6fc)) → PCA で次元削減して改善期待・PCA 50-100 後の現実的目標は **0.4** (= weak と reasonable の中間)
- 戦略並立 1.5× 業界実証: [arxiv FinRL Crypto 2024 (2501.10709)](https://arxiv.org/pdf/2501.10709) + [industry_benchmark §2.3](industry_benchmark_knowledge_base.md)

##### 教科書整合 (cc_role §1.4.6.1 #7)

- **AFML Ch.4 Sample Weights** (Lopez de Prado): 同質性ベースの trade 重み付け
- **AFML Ch.20 HRP**: cluster の純増分検証で純益差を見る業界手法
- **cc_entry_logic_self_study §14.6 / §16.7 / §18.3**: cluster 用評価指標は silhouette + 純益差で業界整合

##### cat-bitget 固有 verify (= メタガード 13・定量試算 1 件以上必須)

- **Phase 4-a 旧実装比較経路**: predictions_train_2021_2024.parquet (= Phase 4-a 旧 14 ラベル予測値版) で silhouette score を再計算・新 PCA 版との改善幅を Stage 1 verify (= 実装着手時に train fold データ pre check で何倍改善するか定量試算)
- **5.1× 積算経路整合**: industry_benchmark §2.6 ケース B 中央値で戦略並立 1.5× を本工程担当・Stage 3 純増分 ≥ 1.5× が合格ライン根拠

##### 第一段階固定値の事前根拠 (= メタガード 14・業界引用 + cat-bitget 過去事例併記)

| 固定値 | 業界引用 | cat-bitget 過去事例 |
|---|---|---|
| silhouette > 0.4 (= CP3 Critical-1 反映) | Wikipedia / GeeksforGeeks: > 0.25 weak / > 0.5 reasonable・**0.4 は中間で PCA 後高次元現実的目標** | Phase 4-a 旧 14 列版 **実装着手時に実測** (= 旧 0.15-0.20 推定値破棄)・新 PCA 版が実測値 + 50% 以上で改善 |
| 純増分 ≥ 1.5× | industry_benchmark §2.3 業界実証 1.2-1.8× 中央値 | cat_v9 で「強い combo に大きい size」運用 = 暗黙 cluster 化済・ML 化で同レベル以上期待 |
| Pearson < 0.5 | Square Root Rule 前提 | regime k-means vs entry cluster k-means は別目的・実装後 verify |

##### 統計指標と PnL 指標の分離 (cc_role §1.4.6.1 #9)

- **統計指標** (= 統計層): Stage 1 silhouette / inertia / 偏り / regime 相関 / 旧版比較
- **PnL 指標** (= PnL 層): Stage 3 純増分 (b)/(a) ≥ 1.5× / Stage 4 月次 NET ≥ $1,900
- Stage 2 視認 = 統計と PnL の中間 (= Exit 抜き PnL proxy で乖離検出)
- 段階間で混同禁止

##### 整合性 Q&A (= メタガード 15・設計矛盾自己検出)

**Q1**: Stage 3 純増分 1.5× は industry_benchmark §2.3 中央値だが、cat-bitget で cluster 数 3-5 の場合に実現可能か?

**A1 (= CP3 Major-3 反映)**: 整合する。§2.3 で「3-5 戦略並立で 1.5-2× Sharpe 改善が現実」は **戦略並立全体** (= cluster + Sizing + Exit 3 工程協調) の業界実証で cluster 単独ではない。§6.3.4 で k ∈ {3, 4, 5} 採用予定 → cluster + Sizing + Exit 3 工程合算で 1.5× は中央値域で目標として妥当。不合格時の第二段階経路 (= 1.3× 落とし) も §2.3 整合範囲。**cluster 単独の責任範囲は 3 工程比で √1.5 ≈ 1.14× 程度**で、cluster 単独 1.5× の過剰要求を回避。

**Q2**: Stage 3 で「(a) base line」「(b) cluster あり版」の比較構造は cluster 単独効果を切り分けられるか?

**A2 (= CP3 Major-3 反映)**: 切り分けは部分的のみ。(a)/(b) 比較は **3 工程協調寄与の全体** を測る。cluster 単独効果を切り分けるには第二段階 ablation study (= [3] Sizing 一律 + [4] Exit のみ cluster 別等の部分構造) を追加実施必要・第一段階は 3 工程協調で評価する設計。

##### data-driven 経路宣言 (cc_role §1.4.6.1 #12)

| 項目 | 暫定値 | data-driven 決定経路 |
|---|---|---|
| silhouette 合格ライン | > 0.4 (= CP3 Critical-1 反映・業界 weak 0.25 と reasonable 0.5 の中間) | Stage 1 で旧 14 列版実測値と比較・実測 + 50% で合格ライン再調整可 |
| 純増分合格ライン | ≥ 1.5× | Stage 3 で実測・1.3-1.5× の場合は要再設計・< 1.3× で工程 §6.3 全面再設計 |
| Pearson 相関閾値 | < 0.5 | 実装後 train fold で実測・> 0.5 なら入力 §6.3.3 で regime 6 列除外検討 |

##### 専門用語補足

| 用語 | 日本語 |
|---|---|
| silhouette score | グループ分けの「うまく分かれた度」(= 0〜1) |
| inertia | グループ内の散らばり度合い (= 小さいほど良) |
| 純増分 (b)/(a) | cluster なし版を 1 とした時の cluster あり版の倍率 |
| Pearson 相関 | 線形相関係数 (= -1〜1・0 で独立) |
| Replay | 過去データでの仮想取引シミュレーション |
| Exit 抜き PnL proxy | 仮の Exit 想定で計算した近似 PnL |

##### §6.3.1 着地

**Stage 1 silhouette > 0.4 (= CP3 Critical-1 反映) + Brier/reliability/ECE (= CP3 Critical-3 反映) + 偏り + regime 相関 + 旧 14 列版実測値比較 → Stage 2 視認 + Exit 抜き PnL proxy → Stage 3 cluster + Sizing + Exit 3 工程合算で純増分 (b)/(a) ≥ 1.5× (= CP3 Major-3 反映・cluster 単独責任ではない) → Stage 4 月次 NET ≥ $1,900 全月クリア の 4 段階順次判定**

> **→ 上記机上設計は実測で覆った（2026-05-30・L-238）。現設計は §6.3 冒頭サマリ参照・実測経緯は [`ml_pipeline_execlog.md`](ml_pipeline_execlog.md) 工程 [2.5]。**

---

#### 6.3.2 アルゴリズム選定

##### 目的

どの道具 (= グループ分け手法) で cluster fit するかを決める。アルゴリズムごとに前提・出力形式・計算重さが違うので、cat-bitget 用途に合うものを選定する。

##### 候補一覧 + 評価

| 道具 | 例え話 | 形 | k 必要? | 出力 | 計算重さ |
|---|---|---|---|---|---|
| **K-Means + GMM hybrid** ← 採用 (CP3 Critical-2 反映) | K-Means で初期割当 + GMM で楕円対応 + 確率出力 | 楕円形 OK | YES (= 事前指定) | hard (cluster_id) + soft (posterior probability) | 中 |
| **k-means 単体** | 最も近い代表点に振り分ける・球形限定 | 球形のみ | YES | hard | 軽 |
| **GMM 単体** | 複数の正規分布の混合と仮定 | 楕円形 OK | YES | soft | 中 |
| **HDBSCAN** | 密集領域だけグループ化・まばら点は無視 | 任意の形 | NO (= 自動決定) | hard + ノイズ | 重 |
| **3 種類 ensemble** (= K + D + G) | 3 種類の結果を合体・多数決 | 任意 | K-Means/GMM 用に必要 | soft | 重 |

##### CC 推奨 = **k-means + GMM の hybrid ensemble** (= CP3 Critical-2 反映・2025 crypto 業界 standard 採用)

**理由 4 点**:

1. **業界 2025 standard 整合 (= CP3 Critical-2 反映)**: [Johal Blockchain Clustering 2025](https://johal.in/blockchain-transaction-clustering-using-unsupervised-learning-algorithms/) で「hybrid ensembles that weight K-Means (for speed) and GMM (for probabilities) can be used for robust scoring」・[MDPI 2025](https://www.mdpi.com/2227-9709/12/2/43) / [DSFE 2025](https://www.aimspress.com/aimspress-data/dsfe/2025/3/PDF/DSFE-05-03-017.pdf) で K-Means + DBSCAN + GMM ensemble が business standard
2. **cat-bitget Entry trade 質分類で球形仮定が曖昧**: スキャル / 長期 / 危険型の境界は楕円形の可能性高い → GMM 楕円対応で改善期待
3. **計算コスト実用範囲**: cat-bitget 56 万行 × PCA 後 50-100 列で k-means + GMM の hybrid 学習時間は数分程度
4. **soft assignment 直接取得**: GMM は posterior probability で各 trade の cluster 所属確率を出す → §6.3.6 cluster_prob_X 出力が自然 (= Gaussian kernel 後段変換不要)

**ハイブリッド構造**:

- K-Means (= 高速 hard clustering): cluster 重心 + 解釈容易性 + 大規模 dataset での初期割当
- GMM (= soft probabilistic clustering): K-Means 結果を初期値として GMM EM 学習 + posterior probability で確率出力
- 第一段階 = K-Means hard cluster_id + GMM posterior probability で cluster_prob_X (= 業界 hybrid ensemble pattern)

**不採用**:
- **DBSCAN**: 第二段階保留 (= 異常検知用途・k-means + GMM で第一段階で分離不十分時に追加検討)
- **HDBSCAN**: 第二段階保留 (= [Shadecoder HDBSCAN 2025](https://www.shadecoder.com/topics/hdbscan-a-comprehensive-guide-for-2025) で `min_cluster_size + cluster_selection_method='leaf'` で cluster 数固定化可能と確認・k-means + GMM で第一段階十分のため不採用)

##### 詳細仕様

| 項目 | 採用値 | 根拠 |
|---|---|---|
| 第一段階 | K-Means hard clustering (= 高速初期割当・解釈容易) | 大規模 dataset 業界 standard |
| 第二段階 | GMM EM 学習 (= K-Means cluster_centers_ で初期化) | hybrid pattern + 楕円対応 + posterior probability |
| 距離計算 | Euclidean (K-Means) + Mahalanobis (GMM) | scikit-learn default + GMM 業界 standard |
| 初期化 | k-means++ → GMM (= K-Means 結果を初期値) | 収束安定 |
| 確率出力 | **GMM posterior probability 直接使用** (= CP3 Critical-2 反映・Gaussian kernel 不要) | GMM native soft assignment |
| キャリブレーション | **fold 別 isotonic regression** (= CP3 Critical-3 反映・§6.3.6 で詳細) | CP1/CP2 Critical-1 同型対策 |
| Stage 1 評価 | silhouette + inertia + 偏り + **Brier score + reliability diagram + ECE** (§6.3.1) | 業界 standard + cluster_prob 品質評価 |

##### 業界 standard verify (cc_role §1.4.6.1 #6)

- **2025 crypto cluster 業界**: K-Means / DBSCAN / GMM が代表的 3 種・**ensemble が robustness 向上で 2025 業界 standard** ([MDPI 2025](https://www.mdpi.com/2227-9709/12/2/43) / [DSFE 2025](https://www.aimspress.com/aimspress-data/dsfe/2025/3/PDF/DSFE-05-03-017.pdf))
- **K-Means vs GMM 差**: K-means hard / GMM soft・GMM は K-means の一般化 (= 球形 → 楕円) ([Towards Data Science](https://towardsdatascience.com/k-means-dbscan-gmm-agglomerative-clustering-mastering-the-popular-models-in-a-segmentation-c891a3818e29/))
- **HDBSCAN**: k 不要・複雑データ対応 ([Medium](https://medium.com/@sina.nazeri/comparing-the-state-of-the-art-clustering-algorithms-1e65a08157a1))

##### 教科書整合 (cc_role §1.4.6.1 #7)

- **AFML Ch.20 HRP**: hierarchical clustering 推奨・k-means 単体は球形仮定の制約
- **cc_entry_logic_self_study §14.6**: GMM = 「returns を multivariate Gaussian の混合で fit」・k-means = 「GMM の特殊解」
- **scikit-learn 公式**: k-means は大規模 dataset 向き・計算軽量

##### cat-bitget 固有 verify (= メタガード 13)

- **Phase 4-a 旧実装振り返り**: k-means 採用済・predictions parquet (= 14 ラベル予測値) を入力にしたが分離不十分 ([phase_compliance §4a.5](../rules/phase_compliance_checklist.md) K96 SHORT q99 が独立 cluster に分離されない事案) → アルゴリズム変更ではなく **§6.3.3 入力強化** (= 14 列 → PCA 50-100 列) が解決経路
- **定量試算**: 同じ k-means でも入力強化で silhouette score 改善期待 (= 旧 14 列版実測値を実装着手時に確定 → 新 PCA 版で実測値 + 50% 以上)・Stage 1 で **業界 standard 0.4 (= CP3 Critical-1 反映)** 達成 verify

##### 第一段階固定値の事前根拠 (= メタガード 14)

| 固定値 | 業界引用 | cat-bitget 過去事例 |
|---|---|---|
| K-Means + GMM hybrid (= CP3 Critical-2 反映) | Johal 2025 / IEEE 金融 hybrid / arxiv 2108.05801 業界実装事例あり (= 「業界 standard」断言不可・「複数事例存在」レベル) | Phase 4-a 単独 K-Means を hybrid 化・楕円境界対応で改善期待 |
| K-Means + Euclidean / GMM + Mahalanobis | scikit-learn default | Phase 4-a 単独 K-Means の継承 + GMM 追加 |
| GMM posterior probability | scikit-learn GaussianMixture native | §6.1.5 Gaussian kernel から hybrid 化 |

##### 統計指標と PnL 指標の分離

- §6.3.2 は **統計層** の選定 (= silhouette / inertia による Stage 1 評価)
- PnL は §6.3.1 Stage 3 で別途・混同禁止

##### 整合性 Q&A (= メタガード 15)

**Q1**: §6.1.4 regime ensemble で k-means + HMM + 固定ルール 3 判定器なのに §6.3.2 で K-Means + GMM hybrid は整合する?

**A1**: 整合する。両工程は目的が違う。regime = 「正解ラベル付きで 3 状態を当てる」→ 多判定器 ensemble で robust 化が必要 (= 同質 3 判定器の独立化で 1.5× 寄与)。entry cluster = 「正解ラベルなしで類似 trade を分類」→ K-Means + GMM hybrid (= 球形 K-Means + 楕円対応 GMM の補完) で十分・後段 [3]/[4] が cluster 別異なる戦略を持つことで戦略並立 1.5× 実現。第一段階 hybrid で Stage 1 silhouette < 0.4 の場合に 3 種類 ensemble (= K + D + G) を第二段階検討経路あり。

**Q2**: Phase 1 v6 教訓 (= 揺れ幅予測逃げ・56 ラベル並列で物理的解消) と §6.3.2 K-Means + GMM hybrid は整合する?

**A2**: 整合する。Phase 1 v6 教訓は [2] Entry ML 工程の話 (= 予測対象の物理的増加で解消済)・[2.5] cluster は予測ではなく **分類** 工程 (= Entry ML 出力を入力として使う後段) で論点軸が違う。

##### data-driven 経路宣言 (cc_role §1.4.6.1 #12)

| 項目 | 暫定値 | data-driven 決定経路 |
|---|---|---|
| アルゴリズム (= CP3 Critical-2 反映) | K-Means + GMM hybrid | **Stage 1 で K-Means 単体 vs hybrid の silhouette 比較**・hybrid が単独より大幅改善しなければ単独に revert・< 0.4 で 3 種類 ensemble (K+D+G) 第二段階検討 |
| K-Means 距離計算 | Euclidean | PCA 入力前提・要再考なら Manhattan / Cosine |
| GMM 共分散 | full (= 各 cluster 独立共分散行列) | data-driven で tied / diag / spherical 検討 (= 高次元で full が不安定なら diag 推奨) |

##### 専門用語補足

| 用語 | 日本語 |
|---|---|
| K-Means | 点を最も近い代表点 (重心) に振り分ける手法 (= 球形 cluster 限定) |
| GMM (= Gaussian Mixture Model) | 正規分布の混合と仮定して楕円形 cluster をモデル化 |
| K-Means + GMM hybrid | K-Means で初期割当 → GMM EM 学習で楕円対応 + 確率出力 |
| posterior probability | GMM が出す各 trade の cluster 所属確率 (= 70% A / 30% B 等) |
| Mahalanobis distance | 共分散を考慮した距離 (= GMM 内で使用) |
| HDBSCAN | 密度ベース・k 不要 |
| hard assignment | 1 点 1 グループに確定割り当て |
| soft assignment | 各点が複数グループに属する確率を出力 |
| Gaussian kernel | 距離を 0〜1 確率に変換する計算式 |
| ensemble | 複数アルゴリズムの結果を統合 |

##### §6.3.2 着地

**K-Means + GMM hybrid (= CP3 Critical-2 反映・まこさん OK 2026-05-27) + k-means++ 初期化 + GMM posterior probability 直接使用 + fold 別 isotonic regression キャリブレーション・Stage 1 で K-Means 単体 vs hybrid silhouette 比較 + silhouette < 0.4 で 3 種類 ensemble (K+D+G) 第二段階検討**

> **→ 上記机上設計は実測で覆った（2026-05-30・L-238）。現設計は §6.3 冒頭サマリ参照・実測経緯は [`ml_pipeline_execlog.md`](ml_pipeline_execlog.md) 工程 [2.5]。**

---

#### 6.3.3 入力特徴量設計

##### 目的

cluster fit の入力に**何を入れるか**を決める。入力次第で「何の軸で分けるか」が変わる (= 予測値だけ入れれば「予測軸での分類」・元特徴量も入れれば「市場文脈込みの分類」)。

##### 候補一覧 + 評価

| 案 | 入力 | 例え話 |
|---|---|---|
| a | Entry ML 予測値 56 個のみ | 「魚の引き具合」だけ見て分類 |
| **b** ← 推奨 | 予測値 56 + 元特徴量 2,604 + regime 6 = 2,666 列全投入 | 「魚の引き具合 + 海の状態 + 時間帯 + 風 + 潮流」全部見て分類 |
| c | 予測値 + 厳選指標 (= 数十列) | 「予測 + 重要そうなものだけ」 |
| d | 予測値 + regime ID + ボラ厳選 | 「予測 + 文脈系厳選」 |

##### CC 推奨 = 案 b 全投入 + PCA 50-100 主成分 + RobustScaler fold 別 fit

**理由 3 点**:

1. **教師なし学習で「不要列を捨てる判断」が事前にできない** → 全投入 + post-pruning が安全
2. **cluster-then-predict 業界 standard 整合** ([Springer Nature 2025](https://link.springer.com/article/10.1007/s44163-025-00519-y))
3. **§6.2.4 案 A 統合と同型構造** (= Entry ML との接続が滑らか)

##### 詳細仕様

| 項目 | 採用値 | 根拠 |
|---|---|---|
| 入力 | 案 b 全投入 (= 2,666 列) | 業界 standard cluster-then-predict |
| 次元削減 | PCA で 50-100 主成分 | 高次元の呪い (curse of dimensionality) 回避・分散 95% 説明 |
| 前処理 | RobustScaler fold 別 fit | k-means は距離ベース・外れ値耐性必須 |
| regime 6 列の扱い | 統合 (= 案 b に含む) | 同じ予測値でも regime 違えば trade 性質違う |

##### 業界 standard verify (cc_role §1.4.6.1 #6・WebSearch 2 件)

- **Cluster-then-Predict pattern** ([Springer Nature 2025](https://link.springer.com/article/10.1007/s44163-025-00519-y) / [PMC 7785332](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7785332/)): 「ML 予測値 + 市場特徴量を k-means で cluster 化 → cluster 別 model 構築」が **crypto 標準アプローチ**・forecasting accuracy 改善実証
- **Trader segmentation 実例** ([PMC 12484065](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12484065/)): K-means で 6 特徴量で trader 群分類実用例
- **PCA + K-means 経路** ([Springer 2025](https://link.springer.com/article/10.1007/s44163-025-00519-y)): 次元削減してから cluster する経路あり (= 高次元の呪い回避)

##### 教科書整合 (cc_role §1.4.6.1 #7)

- **AFML Ch.4 Sample Weights**: 同質性ベースで trade を重み付け → 同質 trade を cluster で捉える前提
- **AFML Ch.16 ML Asset Allocation**: clustering 入力は予測値 + relevant context feature を採用
- **cc_entry_logic_self_study §14.6 L827**: 「k-means / GMM / HMM は距離ベース → StandardScaler 必要」業界整合 (= RobustScaler は外れ値耐性版)

##### cat-bitget 固有 verify (= メタガード 13)

- **Phase 4-a 旧実装 verify**: predictions parquet (= 14 ラベル予測値) を入力にしたが cluster 分離不十分 ([phase_compliance §4a.5](../rules/phase_compliance_checklist.md)) → **予測値のみ入力は不足**を実証
- **定量試算経路**: Phase 4-a predictions_train_2021_2024 (= 56 万行) で 14 列 k-means の silhouette score を再計算・Stage 1 で 2,666 列 PCA 版と比較
- **cat_v9 経験値整合**: cat_v9 は P1-P25 で indicator 多様性 8-10 種を使い分け = 「trade の質が文脈で違う」前提と整合 → 案 b 全投入 = cat_v9 流の多様性を ML に学習させる構造

##### 第一段階固定値の事前根拠 (= メタガード 14)

| 固定値 | 業界引用 | cat-bitget 過去事例 |
|---|---|---|
| 案 b 全投入 | Springer 2025 cluster-then-predict standard | §6.2.4 案 A 統合と同型・cat_v9 多様性整合 |
| PCA 50-100 主成分 | scikit-learn default + AFML Ch.16 | 暫定範囲・実装着手時に分散 95% 説明する主成分数で確定 |
| RobustScaler | cc_entry_logic §14.6 業界整合 | §6.1.5 regime ensemble と同型 |

##### 統計指標と PnL 指標の分離

- §6.3.3 は **統計層** の入力設計 (= silhouette / inertia の入力側パラメータ)
- PnL は §6.3.1 Stage 3 で別途・混同禁止

##### 整合性 Q&A (= メタガード 15)

**Q1**: Phase 1 v6 教訓 (= 56 ラベル並列で物理的解消) と §6.3.3 案 b 全投入の整合性は?

**A1**: 整合する。56 ラベル予測値**全部**を cluster 入力に含む案 b は「物理的に増やした 56 予測情報を集約段階で圧縮しない」設計 = Phase 1 v6 教訓の論理整合。一部予測値のみ入れる案 a は教訓に逆行 → 不採用。

**Q2**: §6.2.4 (= Entry ML 入力 案 A 統合) と §6.3.3 (= cluster 入力 案 b 全投入) の整合性は?

**A2**: 整合する。両者とも「全投入 + post-pruning」設計思想 = 工程間で意思決定原則が一貫。

##### data-driven 経路宣言 (cc_role §1.4.6.1 #12)

| 項目 | 暫定値 | data-driven 決定経路 |
|---|---|---|
| PCA 主成分数 | 50-100 | train_2021_2024 fold で「分散 95% 説明する主成分数」を実装着手時に決定 |
| PCA 後 vs 生 2,666 列 | PCA 後 | Stage 1 silhouette 比較で確定・PCA 後 > 生で採用継続 / 逆なら生 + Clustered MDA 切替 |
| regime 統合 vs regime 別 fit | 統合 | Stage 3 で regime 別 cluster 効果差 > 20% で別 fit 化検討 |

##### 専門用語補足

| 用語 | 日本語 |
|---|---|
| 教師なし学習 (unsupervised) | 正解ラベルなしの学習 |
| 高次元の呪い (curse of dimensionality) | 列が多すぎて距離計算が壊れる現象 |
| PCA (= 主成分分析) | たくさんの列を代表値に圧縮する道具 |
| RobustScaler | 外れ値に強い数値スケール揃え処理 |
| fold 別 fit | 期間ごとに分けて処理 (= 未来データを使わない安全策) |
| post-pruning | 学習後に不要な列を削る作業 |
| cluster-then-predict | グループ分けしてからグループ別予測 |
| Clustered MDA | 重要度が低い列を機械的に削る業界手法 |

##### §6.3.3 着地

**案 b 全投入 (= 2,666 列) + PCA 50-100 主成分 + RobustScaler fold 別 fit + regime 統合 + Stage 1 で post-pruning 検討**

採用根拠 5 点: (i) 業界 standard cluster-then-predict / (ii) 教科書 AFML Ch.16 / (iii) §6.2.4 と同型構造 / (iv) Phase 4-a 旧実装の不足を解消 / (v) Phase 1 v6 教訓論理整合

> **→ 上記机上設計は実測で覆った（2026-05-30・L-238）。現設計は §6.3 冒頭サマリ参照・実測経緯は [`ml_pipeline_execlog.md`](ml_pipeline_execlog.md) 工程 [2.5]。**
>
> ⚠️ ただし**入力構成を silhouette で確定してはならない** (= 2026-05-30 WebSearch ベースアップ): silhouette は特徴量集合が違うと比較不可 (= 次元の呪いで列数が多いほど機械的に低下・[markhneedham 2016](https://www.markhneedham.com/blog/2016/08/27/scikit-learn-clustering-and-the-curse-of-dimensionality/) / [arxiv 2402.12008](https://arxiv.org/pdf/2402.12008))。旧 16 列版 silhouette 0.49 > 新 28 列 0.326 も「16 列が優秀」ではなく次元差のアーティファクト。→ **入力構成の最終確定は Stage 3 PnL で複数候補 (= 28 列 / 旧 16 列 / 他) を比較して決める** (= [Lopez de Prado: clustering は下流タスクへの影響で評価](https://gmarti.gitlab.io/qfin/2020/04/12/commented-summary-machine-learning-for-asset-managers.html) / [IBKR cluster-based feature selection](https://www.interactivebrokers.com/campus/ibkr-quant-news/the-amazing-efficacy-of-cluster-based-feature-selection/))。詳細経緯は [`ml_pipeline_execlog.md`](ml_pipeline_execlog.md) 工程 [2.5]。

---

#### 6.3.4 k (グループ数) 決定方法

##### 目的

cluster を**何個に分けるか** (= 3 個? 4 個? 5 個?) を決める。少なすぎる (= 1-2) と粒度不足で「分けた意味」がない・多すぎる (= 6+) と各 cluster の trade 数が減って統計弱体化。

##### 候補一覧 + 評価

| k | 例え話 | 評価 |
|---|---|---|
| 2 | スキャル / 長期 の 2 種類 | 粗すぎる |
| **3** ← 候補 | スキャル / 長期 / 危険 | 業界 standard・industry_benchmark §2.3 整合 |
| **4** ← 候補 | + 凡庸 (= 時間切れ寄り) | スキャル/長期/危険/凡庸 |
| **5** ← 候補 | + 中間タイプ | やや細かい |
| 6+ | 各 cluster データ減 → 統計弱体 | 過剰 |

##### CC 推奨 = k ∈ {3, 4, 5} を並列試行 + silhouette + 業界経験則で data-driven 決定

**理由 3 点**:

1. **固定値ではなくデータから判定** (= 「3 個固定」「5 個固定」は決め打ちで data-driven 経路宣言違反)
2. **業界実証 3-5 cluster 範囲** ([industry_benchmark §2.3](industry_benchmark_knowledge_base.md))
3. **§6.1.4 regime k-means と同型構造** (= regime ensemble でも k ∈ {2,3,4,5} elbow + silhouette data-driven 採用済)

##### 詳細仕様

| 判定ステップ | 内容 |
|---|---|
| Step 1 | k ∈ {3, 4, 5} で並列 fit |
| Step 2 | 各 k の silhouette score 計算・最大を仮採用 |
| Step 3 | elbow method (= グループ内分散の急減点) で確認 |
| Step 4 | silhouette 最大と elbow が食い違ったら業界経験則 (= 3-5 cluster で 1.5× レバー) で決定 |
| Step 5 | cluster 別 trade 数の偏り verify (= 最小 cluster ≥ 5%)・不合格なら k 候補から除外 |

##### 業界 standard verify (cc_role §1.4.6.1 #6)

- **3-5 cluster で 1.5-2× Sharpe 改善が現実** ([industry_benchmark §2.3](industry_benchmark_knowledge_base.md))・cluster 数増加で相関増加・直交 alpha 減退
- **5-model ensemble で Sharpe 80-91% 改善実証** ([arxiv FinRL Crypto 2024 (2501.10709)](https://arxiv.org/pdf/2501.10709))
- **silhouette + elbow data-driven 経路** ([Built In Elbow Method](https://builtin.com/data-science/elbow-method) + [ML Mastery Silhouette](https://machinelearningmastery.com/k-means-cluster-evaluation-with-silhouette-analysis/))

##### 教科書整合 (cc_role §1.4.6.1 #7)

- **AFML Ch.20 HRP**: k 数最適化に gap statistic / elbow / silhouette の併用推奨
- **cc_entry_logic_self_study §17.6 ONC (Optimal Number of Clusters)**: 「類似戦略を unsupervised clustering で集約 → cluster 数 = 実効 N」の Lopez de Prado 手法
- **scikit-learn 公式**: silhouette_score / inertia の elbow 並用が業界 standard

##### cat-bitget 固有 verify (= メタガード 13)

- **Phase 4-a 旧実装振り返り**: k=12 で実装したが分離不十分 (= [phase_compliance §4a.5](../rules/phase_compliance_checklist.md) K96 SHORT q99 が独立 cluster に分離されない事案) → **k が多すぎた可能性**・新工程で 3-5 範囲に絞る判断根拠
- **cat_v9 経験値整合**: P1-P25 ≈ 25 個の人間分類だが、ML cluster は粒度違う・3-5 個で十分 (= 後段 [3]/[4] が cluster 別 3-5 種類の戦略を持つ前提)
- **定量試算経路**: Phase 4-a predictions_train_2021_2024 (= 56 万行) で k=3,4,5 並列 fit → silhouette score 比較を実装着手時に train fold データで pre check

##### 第一段階固定値の事前根拠 (= メタガード 14)

| 固定値 | 業界引用 | cat-bitget 過去事例 |
|---|---|---|
| k ∈ {3, 4, 5} 候補範囲 | industry_benchmark §2.3 業界実証 3-5 cluster | Phase 4-a の k=12 は過剰実証・3-5 への絞り込み妥当 |
| silhouette 最大採用 | scikit-learn 公式 | §6.1.4 regime ensemble と同型運用 |
| 偏り最小 ≥ 5% | k-means 業界 minimum | Phase 4-a で偏りチェック未実装・新規追加 |

##### 統計指標と PnL 指標の分離

- §6.3.4 は **統計層** の k 決定 (= silhouette / elbow / 偏り)
- PnL は §6.3.1 Stage 3 で別途・k 決定段階では PnL を見ない (= 統計層で確定 → PnL 層で第二段階再判定経路)

##### 整合性 Q&A (= メタガード 15)

**Q1**: industry_benchmark §2.3 で「3-5 戦略並立で 1.5-2× Sharpe 改善」だが、§6.3.4 で k=3 を採用した場合に 1.5× 出るか?

**A1**: §2.3 で「cluster=3 → 3 戦略並立で 1.3-1.5× が目安」と業界実証・k=3 でも 1.5× は中央値域で実現可能。ただし k=3 で不合格時の経路として k=4,5 の第二段階あり・並立効果は「戦略間の相関」次第なので §6.3.3 入力特徴量の直交化が前提。

**Q2**: §6.1.4 regime k-means で k ∈ {2,3,4,5} 範囲なのに、§6.3.4 で {3,4,5} 範囲は整合する?

**A2**: 整合する。regime k-means は「市場局面の数」を判定 (= 上昇/下落/レンジ + 不確実が考えられる) → k=2 も候補入り。entry cluster は「trade の質タイプ」を分類 (= スキャル/長期/危険/凡庸) → k=2 では粒度不足で実用性低い → {3,4,5} 範囲が論点軸整合。

##### data-driven 経路宣言 (cc_role §1.4.6.1 #12)

| 項目 | 暫定値 | data-driven 決定経路 |
|---|---|---|
| k 候補範囲 | {3, 4, 5} | Stage 1 で silhouette 最大の k を採用・elbow と食い違ったら業界経験則で決定 |
| 偏り合格ライン | 最小 cluster ≥ 5% | 不合格 k を候補から除外・全 k 不合格なら §6.3.3 入力再設計 |
| k=6 フォールバック | 不採用 (第一段階) | 全 k={3,4,5} 不合格時の最後手段・統計弱体化リスクを許容して検討 |

##### 専門用語補足

| 用語 | 日本語 |
|---|---|
| silhouette score | グループ分けの「うまく分かれた度」(= 0〜1) |
| elbow method | 分散の急減点を見て k を決める手法 |
| 直交 alpha | 戦略間の相関が低いほど稼げる効果 |
| gap statistic | k 数最適化の業界手法 (= elbow の代替) |
| ONC | Optimal Number of Clusters (= Lopez de Prado 手法) |

##### §6.3.4 着地

**k ∈ {3, 4, 5} 並列試行 + silhouette 最大採用 + elbow 確認 + 偏り ≥ 5% verify + 業界経験則 (= 3-5 cluster) で data-driven 決定**

---

#### 6.3.5 ラベル付け

##### 目的

ML が出した無名の cluster (= 0, 1, 2, ...) に**人間が読める名前**をつける。番号だけでは何が何だか分からない・まこさん視認 + デバッグ + dashboard 表示で必須。

##### 必要性

- **まこさん視認**: dashboard で「cluster 0, 1, 2」では何が起きてるか分からない・「スキャル型 / 長期型 / 危険型」と表示できる必要
- **デバッグ**: 失敗 trade を「どの cluster で失敗したか」追跡可能
- **後段 [3]/[4] 設計時の方針説明**: 「危険型は size 縮小」「長期型は trail 延ばす」等
- **レポート / 業界用語整合**: cat_v9 で P1-P25 にまこさんが命名済 = 同型の post-hoc 解釈プロセス

##### CC 推奨 = 4 軸 (TP_prob / MFE / SL_prob / 保有時間) で post-hoc 命名

各 cluster の中身を見るために、以下の数値を計算して比較:

| グループ | TP_prob 平均 | MFE 平均 | SL_prob 平均 | 平均保有時間 |
|---|---|---|---|---|
| 0 | 高 | 小 | 低 | 短 |
| 1 | 高 | 大 | 低 | 長 |
| 2 | 低 | - | 高 | - |
| 3 | 中 | 中 | 中 | 中 |

→ 命名 (= 例):
- グループ 0 = **scalp** (= スキャル型・短時間で小さく利確)
- グループ 1 = **long_term** (= 長期型・時間かけて大きく取る)
- グループ 2 = **risky** (= 危険型・損切り寄り)
- グループ 3 = **avg** (= 凡庸型・平均的)

##### 詳細仕様

| 項目 | 採用値 |
|---|---|
| 命名軸 | TP_prob / MFE / SL_prob / 保有時間 の 4 軸 |
| 命名タイミング | train 期間で命名 → test には mapping 適用のみ (= leak 防止) |
| 命名形式 | snake_case 英語 (= scalp / long_term / risky / avg)・dashboard 用に日本語 alias 併設 |
| 名前変更条件 (= CP3 Minor-1 反映) | Stage 2 で「名前と分布が合わない」場合に **train fold 内**で再命名・名前は cluster の本質を表すだけで後段戦略は数値ベース実装・再命名後は **Stage 1 silhouette + Brier/reliability/ECE を再 verify** (= 再命名で cluster 性質変わる場合に評価指標も再計算必要) |

##### 業界 standard verify (cc_role §1.4.6.1 #6)

- **post-hoc cluster labeling 業界 standard**: K-means 後の cluster 解釈は手動命名が業界慣行 ([Towards Data Science](https://towardsdatascience.com/k-means-clustering-algorithm-applications-evaluation-methods-and-drawbacks-aa03e644b48a/))
- **AFML / mlfinlab**: cluster の post-hoc 解釈で重要なのは「**cluster の中身を統計値で記述**」(= 数値ベースで描写してから名前をつける)
- **scikit-learn 公式**: cluster_centers_ を見て命名する経路が標準

##### 教科書整合 (cc_role §1.4.6.1 #7)

- **AFML Ch.4 / Ch.20**: clustering 後の post-hoc 解釈で「cluster ごとの統計値で記述」を推奨
- **§6.1.4 regime k-means** で「cluster ごとの統計値 (= return / ADX / DI 差) で post-hoc マッピング」採用済・同型運用

##### cat-bitget 固有 verify (= メタガード 13)

- **cat_v9 経験値整合**: cat_v9 で P1-P25 にまこさんが人間命名済 (= 「P21 = 平均建値型・P3 = スキャル系」等)・同型の post-hoc 解釈プロセス
- **Phase 4-a 旧実装**: cluster_label をマッピングする post-hoc 解析あり (= 継承)
- **定量試算経路**: Phase 4-a predictions_train_2021_2024 で 4 軸 (TP_prob / MFE / SL_prob / 保有時間) の cluster 別平均を実装着手時に算出 → 区別がつくか pre check

##### 第一段階固定値の事前根拠 (= メタガード 14)

| 固定値 | 業界引用 | cat-bitget 過去事例 |
|---|---|---|
| 4 軸命名 (= TP_prob/MFE/SL_prob/保有時間) | AFML Ch.4 統計値ベース | cat_v9 で人間が同型 4 軸で命名済 |
| snake_case 英語名 | OSS / Python 業界慣習 | scripts 内識別子と整合 |
| 命名タイミング = train 期間のみ | §4a.1 fit は train のみと同型 | Phase 4-a leak 防止規律と整合 |

##### 統計指標と PnL 指標の分離

- §6.3.5 は **解釈層** (= 統計と PnL の中間・cluster の中身を描写)
- 名前は人間用デバッグ表示のみ・後段戦略は数値ベース実装 (= 名前依存しない)

##### 整合性 Q&A (= メタガード 15)

**Q1**: cluster label を train 期間で決定 → test には mapping 適用のみ で leak 防止できるか?

**A1**: できる。命名 = train 期間の cluster 別統計値で決定・test 期間の cluster_id は train 学習済モデルで予測 → mapping で名前付与のみ。test 期間のデータで命名を変えない (= §6.3.7 leak 防止と整合)。

**Q2**: 名前と実分布が合わない場合の再命名は leak ではないか?

**A2**: Stage 2 視認で「scalp と命名したが MFE 平均が大」と発見した場合の再命名は、**train fold 内での再計算**であれば leak ではない (= train fold 内での post-hoc 解釈の精緻化)。test fold データを見て命名を変えるのは leak (= 禁止)。

##### data-driven 経路宣言 (cc_role §1.4.6.1 #12)

| 項目 | 暫定値 | data-driven 決定経路 |
|---|---|---|
| 命名する数値項目 | TP_prob / MFE / SL_prob / 保有時間 の 4 軸 | Stage 2 で「これじゃ区別つかない」場合に項目追加 |
| 名前の具体的文字列 | scalp / long_term / risky / avg | Stage 2 視認で cluster 別分布見て確定 |
| k=4 / k=5 時の追加名 | 暫定なし | 実装後に決定 |

##### 専門用語補足

| 用語 | 日本語 |
|---|---|
| post-hoc | 後付け解釈 (= ML が分けた後で人間が解釈) |
| TP_prob | 利確確率 (= 予測値) |
| MFE | 含み益最大値 (= Maximum Favorable Excursion) |
| SL_prob | 損切り確率 |
| mapping | cluster_id → label_name の対応表 |
| snake_case | 識別子の命名規約 (= 単語間 _ 区切り) |

##### §6.3.5 着地

**train 期間で 4 軸 (TP_prob / MFE / SL_prob / 保有時間) の cluster 別統計値を計算 → 人間が post-hoc で命名 → test には mapping 適用のみ・名前は dashboard / デバッグ用で後段戦略は数値ベース実装**

---

#### 6.3.6 出力 → 後段接続

##### 目的

cluster 分けの結果を**どこに保存・どんな形式で書き出して、後段 [3] Sizing / [4] Exit がどう読み込むか**を決める。出力形式と接続経路を固定しないと工程間でデータ受け渡しが破綻するリスク。

##### 出力列構成 (= §6.1.6 regime 出力と同型)

###### 主要列 7 列

| 列名 | 内容 | 例 |
|---|---|---|
| `cluster_id` | グループ番号 (= 0, 1, 2, ...) | 0 |
| `cluster_prob_0` | グループ 0 に属する確率 (= **GMM posterior probability + fold 別 Isotonic Regression キャリブレーション後**・CP3 Critical-3 反映) | 0.72 |
| `cluster_prob_1` | グループ 1 に属する確率 (= 同上・校正後) | 0.18 |
| `cluster_prob_2` | (k に応じて続く・校正後) | 0.10 |
| `cluster_label` | 人間用名前 | "scalp" |
| `cluster_confidence` | 確信度 (= 最大確率 - 2 番目確率) | 0.54 |
| `cluster_silhouette` | 各 trade の silhouette 値 (= はみ出し度) | 0.42 |

###### 派生 one-hot 列 (= 第二段階保留・CP3 Major-1 反映)

**第一段階 = cluster_id 直接食わせる** (= LightGBM 4.6 native categorical 業界 standard・[公式 Advanced Topics](https://lightgbm.readthedocs.io/en/latest/Advanced-Topics.html) で「Native handling often performs better than one-hot encoding・Expo data で約 8x 高速」確認)。

派生 one-hot 列 (= 下記) は **第二段階保留** (= cluster_id 直接 vs one-hot の Stage 3 性能比較で one-hot 大幅勝ちなら追加):

| 列名 (= 第二段階保留) | 内容 |
|---|---|
| `is_scalp` | スキャル型なら 1 |
| `is_long_term` | 長期型なら 1 |
| `is_risky` | 危険型なら 1 |
| `is_avg` | 凡庸型なら 1 |

(k=4 想定・k=3 / k=5 でカラム数調整・第二段階で採用判定)

##### 保存場所

- `results/priority_rebuild/cluster_step1/cluster_predictions_train_2021_2024.parquet`
- `results/priority_rebuild/cluster_step1/cluster_predictions_test_2025.parquet`
- `results/priority_rebuild/cluster_step1/cluster_predictions_test_2026_q1.parquet`
- joblib artifact: `cluster_kmeans_train_2021_2024.joblib` / `pca_train_2021_2024.joblib` / `scaler_train_2021_2024.joblib`
- (= §6.1.6 regime 出力と同型構造)

##### 後段接続方法

```
[2] Entry ML 出力 (= 56 ラベル予測)
    ↓ entry_id + timestamp で merge
[2.5] cluster 出力 (= 7 主要列・第一段階)
    ↓ entry_id + timestamp で merge
[3] Sizing 入力 / [4] Exit 入力 (= 統合 input・cluster_id は categorical_feature 指定)
```

- entry_id ベース join で timestamp ズレなし (= 自然に未来参照防止)
- 後段 LightGBM (= [3]/[4]) で **cluster_id を直接 categorical_feature 指定** (= LightGBM 4.6 native handling・[公式](https://lightgbm.readthedocs.io/en/latest/Advanced-Topics.html) で「8x 高速 + accuracy 向上可」業界 standard・CP3 Major-1 反映)

##### causal alignment (= 未来情報を使わない時間整合)

- cluster は Entry ML 出力に基づくので、Entry ML の causal alignment と同じ tick の値を使う
- entry_id ベース join なので timestamp ズレなし
- `assert no look-ahead` 入れる (= §6.2.8 leak 防止と整合)
- 検証: parquet 出力時に `assert df['entry_ts'] <= df['cluster_predict_ts']` (= cluster 予測時刻が entry 時刻と一致もしくは後)

##### 業界 standard verify (cc_role §1.4.6.1 #6)

- **LightGBM 4.6 native categorical 業界 standard (= CP3 Major-1 反映)**: [公式 Advanced Topics](https://lightgbm.readthedocs.io/en/latest/Advanced-Topics.html) で「Native handling often performs better than one-hot encoding・Expo data で約 8x 高速」・[CodeSignal Learn](https://codesignal.com/learn/courses/lightgbm-made-simple/lessons/native-categorical-handling) で「One-hot encoding is suboptimal for tree learners」・cluster_id を整数で渡し `categorical_feature` 引数で指定が業界推奨 (= 旧 one-hot 推奨は LightGBM 3.x 以前の慣行)
- **soft cluster output (= 確率列)**: AFML Ch.16 で「cluster prob + cluster_id を併用」が業界 standard
- **entry_id ベース merge**: AFML Ch.7 sample-level join が業界 standard

##### 教科書整合 (cc_role §1.4.6.1 #7)

- **AFML Ch.16 ML Asset Allocation**: cluster 出力は cluster_id + cluster_prob + cluster_centers_ の 3 種類を保持推奨
- **§6.1.6 regime 出力仕様**: 6 列 + one-hot 派生列の同型構造を採用

##### cat-bitget 固有 verify (= メタガード 13)

- **Phase 4-a 旧実装**: cluster_id のみ出力で確率なし → §6.3.6 案では確率列追加 (= 改善)
- **§6.1.6 regime 出力との合計**: regime 6 列 + cluster 7+派生列 = 13+ 列が [3]/[4] 入力に追加される
- **定量試算経路**: Phase 4-a predictions_train_2021_2024 の cluster_id 出力に対し、Gaussian kernel で確率変換した場合の確率列分布を実装着手時に train fold で pre check

##### 第一段階固定値の事前根拠 (= メタガード 14)

| 固定値 | 業界引用 | cat-bitget 過去事例 |
|---|---|---|
| 主要 7 列 + cluster_id 直接食わせ (= CP3 Major-1 反映) | LightGBM 4.6 公式 Native handling 推奨 + AFML Ch.16 | §6.1.6 regime 出力と同型運用・派生 one-hot は第二段階保留 |
| parquet 保存形式 | OSS / Python 業界慣習 | Phase 0 / Phase 4-a 旧実装と同型 |
| entry_id ベース merge | AFML Ch.7 sample-level join | §6.2 Entry ML 出力との接続前提 |

##### 統計指標と PnL 指標の分離

- §6.3.6 は **データ受け渡し層** (= 統計でも PnL でもない構造設計)
- 統計指標は §6.3.1 Stage 1・PnL 指標は §6.3.1 Stage 3 で別途・混同禁止

##### 整合性 Q&A (= メタガード 15)

**Q1**: §6.1.6 regime 出力 6 列 + §6.3.6 cluster 出力 7+派生列 = 13+ 列が [3]/[4] 入力に追加される・冗長ではないか?

**A1**: 整合する。regime = 市場局面 (= 上昇/下落/レンジ・大局)、cluster = trade 質 (= スキャル/長期/危険/凡庸・局所) で論点軸が違うので冗長ではない。Stage 1 で予測誤差相関 Pearson < 0.5 verify で「重複していない」を機械的確認。

**Q2**: cluster_id を直接食う vs one-hot 列を食うで [3]/[4] 性能差は出るか?

**A2 (= CP3 Major-1 反映で改訂)**: **LightGBM 4.6 公式は native handling 推奨** (= 「Native handling often performs better than one-hot encoding・Expo data で約 8x 高速」)。旧 v3.8 設計の「業界 practice として one-hot 推奨」は LightGBM 3.x 以前の慣行で 4.x で逆転。第一段階 = cluster_id 直接食わせ + 派生 one-hot は第二段階保留 (= Stage 3 で one-hot 大幅勝ちなら追加検討)。

##### data-driven 経路宣言 (cc_role §1.4.6.1 #12)

| 項目 | 暫定値 | data-driven 決定経路 |
|---|---|---|
| 主要列数 | 7 列 (k=4 想定) | k 確定 (§6.3.4) 後に列数調整 (= k=3 で 6 列・k=5 で 8 列) |
| 派生 one-hot 列の採用 (= CP3 Major-1 反映で反転) | **不採用 (第一段階)** | Stage 3 で cluster_id 直接 vs one-hot 比較で one-hot 大幅勝ち時に第二段階追加 |
| 後段 LightGBM への渡し方 (= CP3 Major-1 反映) | cluster_id 直接食わせ + `categorical_feature` 指定 | LightGBM 4.6 native handling 業界 standard |
| 保存形式 | parquet | 業界 standard・OSS 整合で固定 |

##### 専門用語補足

| 用語 | 日本語 |
|---|---|
| one-hot 列 | フラグ列 (= 0/1 で表現) |
| merge_asof | timestamp 整合の結合方法 |
| entry_id | entry trade に付与する一意 ID |
| causal alignment | 未来情報を使わない時間整合 |
| look-ahead | 未来データを誤って使うリーク |
| joblib | scikit-learn モデルの保存形式 |
| parquet | 列指向のデータ保存形式 (= 高速読み書き) |

##### §6.3.6 着地

**出力 7 主要列 (= cluster_id + cluster_prob_0/1/.. + cluster_label + cluster_confidence + cluster_silhouette・第一段階) + cluster_id を LightGBM `categorical_feature` で直接食わせ (= CP3 Major-1 反映・公式 native handling) + 派生 one-hot 列は第二段階保留 + parquet 保存 + entry_id ベース merge で後段接続 + causal alignment 明示 + assert no look-ahead**

> **→ 上記机上設計は実測で覆った（2026-05-30・L-238）。現設計は §6.3 冒頭サマリ参照・実測経緯は [`ml_pipeline_execlog.md`](ml_pipeline_execlog.md) 工程 [2.5]。**
>
> ⚠️ 注意 (= まこさん承認 2026-05-30): この距離 softmax は**未校正の疑似確率** (= [Stan Soft K-means: 距離→softmax は正規化はするが校正はしない](https://mc-stan.org/docs/2_27/stan-users-guide/soft-k-means.html))。後段 [3] Sizing / [4] Exit でこの cluster_prob を**意思決定に本気で使う**なら、temperature scaling / Dirichlet 校正等で校正し直す経路を残す (= [arxiv 1910.12656 multiclass 校正](https://arxiv.org/pdf/1910.12656))。cluster_id (= hard 割当) のみ使う限りは校正不要。詳細経緯は [`ml_pipeline_execlog.md`](ml_pipeline_execlog.md) 工程 [2.5]。

---

#### 6.3.7 leak 防止

##### 目的

教師なし学習でも**未来データを使ってしまう経路を洗い出して防止**する。教師なしだから安全と思いがちだが、cluster でも leak は複数経路あり (= scikit-learn fit / transform 範囲・k 決定 / 命名タイミング等)。

##### 第一原則

**未来データ参照は全工程で絶対禁止** (= [false_positive §0-1 Prime Directive](../rules/false_positive_incident_policy.md))・t 時点で取得可能な変数のみ計算式・判定式・採用ロジックに使用可能。

##### leak 経路と防止策 (= 7 項目・CP3 Minor-1 反映で entry_id 経路追加)

| # | 経路 | 防止策 |
|---|---|---|
| 1 | k-means の fit に test 期間データを含める | **fit は train 期間のみ**・test は predict のみ (= [phase_compliance §4a.1](../rules/phase_compliance_checklist.md) 整合) |
| 2 | PCA の fit を test 期間で行う | **PCA fit も train 期間のみ**・joblib 保存して apply |
| 3 | RobustScaler の fit を test 期間で行う | **scaler fit も train 期間のみ**・fold 別 fit (= Pipeline 化) |
| 4 | Entry ML 出力が leak 含む | §6.2.8 leak 防止整合 (= 4 点 verify 通過した出力のみ使用) |
| 5 | k 数決定 (= silhouette 計算) を test 期間で行う | **k 探索も train 期間のみ**・test には適用のみ |
| 6 | cluster label (= post-hoc 命名) を test 期間で決定 | **命名も train 期間のみ**・test には mapping 適用のみ |
| 7 | **entry_id 生成式が未来情報依存 (= CP3 Minor-1 反映)** | entry_id = `f"{entry_timestamp}_{symbol}_{side}_{counter}"` 形式 (= entry 時刻 + symbol + 方向 + 通し番号で完全に t 時点情報のみ・MFE/MAE 等未来由来値を含めない)・実装時 grep で「shift(-」「future」「mfe」「mae」等の未来由来語を含まないか verify |

##### artifact 命名規律 (= §4a.4 と同型)

- **ファイル名禁止**: `*test*` / `*test2025*` 含む joblib 禁止
- **合格名**: `cluster_kmeans_train_2021_2024.joblib` / `pca_train_2021_2024.joblib` / `scaler_train_2021_2024.joblib`
- ls grep で test 含むファイルがゼロ件を verify

##### 起動時 assertion

```python
assert "train" in artifact_path and "test" not in artifact_path
```

(= [phase_compliance §6b.4](../rules/phase_compliance_checklist.md) と同型)

##### causal alignment

- §6.3.6 出力で cluster_id の timestamp 整合 (= entry_id ベース merge)
- `assert no look-ahead` 入れる
- §6.1.6 regime と同型構造

##### Stage 1 verify 項目

実装着手時に以下を機械的 verify:

| verify 項目 | 方法 |
|---|---|
| timestamp range 分離 | train 末 < test 始 を parquet min/max で確認 |
| artifact 名 verify | grep で `*test*` 含む joblib がないか |
| fit 範囲 grep | `.fit(` を呼ぶ箇所が train データのみか |
| causal alignment | `merge_asof` の direction 確認 |
| Entry ML 出力の leak フリー verify | §6.2.8 4 点 verify 通過済か |
| feature_importance review | cluster 入力 (= PCA 主成分) の重要度上位に怪しい列名がないか |

##### 業界 standard verify (cc_role §1.4.6.1 #6)

- **教師なし学習 leak**: AFML Ch.7 で「unsupervised でも fit は train fold 内に閉じ込めるべき」明文化
- **artifact 命名規律**: scikit-learn 業界 best practice ([Hudson & Thames mlfinlab](https://www.mlfinlab.com/en/latest/feature_importance/afm.html) 整合)

##### 教科書整合 (cc_role §1.4.6.1 #7)

- **AFML Ch.3 Look-Ahead Bias**: shift(-K) / center=True 等の未来参照禁止
- **AFML Ch.7 Purged K-Fold + Embargo**: train/test 境界に embargo を入れて leak 完全防止
- **false_positive §0-1 Prime Directive**: 推論時点 t で取得可能な変数のみ使用

##### cat-bitget 固有 verify (= メタガード 13)

- **Phase 4-a 過去事例**: [§4a.1](../rules/phase_compliance_checklist.md) で「fit は train のみ」明文化済 (= 教師なし leak の業界 standard 防止規律) → 本工程でも整合
- **§6.2.8 Entry ML leak 防止との接続**: cluster は Entry ML 出力依存 → §6.2.8 4 点 verify 通過した出力のみ使用
- **定量試算経路**: Phase 4-a artifact `predictions_train_2021_2024_k12long_refit.parquet` の命名規律と同型化・実装着手時に grep で test 含むファイル名ゼロ件 verify

##### 第一段階固定値の事前根拠 (= メタガード 14)

| 固定値 | 業界引用 | cat-bitget 過去事例 |
|---|---|---|
| fit は train 期間のみ | AFML Ch.7 + scikit-learn 業界 standard | phase_compliance §4a.1 / §6b.1 と同型 |
| artifact 名 train 含む必須 | scikit-learn 業界 best practice | phase_compliance §4a.4 / §7c.9 と同型 |
| 起動時 assertion | OSS Python 慣行 | phase_compliance §6b.4 / §7c.9 と同型 |

##### 統計指標と PnL 指標の分離

- §6.3.7 は **規律層** (= 統計でも PnL でもない leak 防止規律)
- 違反は false_positive §2 類型 A (= look-ahead leak) として最重大インシデント扱い

##### 整合性 Q&A (= メタガード 15)

**Q1**: §6.2.8 Entry ML leak 防止と §6.3.7 cluster leak 防止の重複ではないか?

**A1**: 重複ではない。§6.2.8 は Entry ML 工程内の leak 経路 (= 特徴量 / ラベル / CV)・§6.3.7 は cluster 工程独自の leak 経路 (= k-means / PCA / scaler / k 探索 / 命名) を扱う。両者を独立 verify して工程接続の隙間を塞ぐ。

**Q2**: 教師なしなのに leak 経路がある理由は?

**A2**: 教師なし = 「正解ラベルなし」だけで「未来データ使い禁止」とは別。k-means fit / PCA fit / scaler fit / k 探索 / 命名 すべてに **「train 期間のデータで決定するか / test 期間のデータも含めるか」** の選択が発生し、test 含めると leak。

##### data-driven 経路宣言 (cc_role §1.4.6.1 #12)

| 項目 | 暫定値 | data-driven 決定経路 |
|---|---|---|
| Stage 1 verify 全項目 | 全項目 PASS 必須 | 1 項目でも FAIL なら実装中止・leak 経路特定 |
| feature_importance leak review | 上位 N に怪しい列名がないか | 怪しい列発見時に [feedback_ml_leak_mandatory_check](../memory/feedback_ml_leak_mandatory_check.md) 4 点 verify セット適用 |
| Purged K-Fold embargo | §6.2.5 と同型 | 必要なら別途追加検討 |

##### 専門用語補足

| 用語 | 日本語 |
|---|---|
| fit | モデルの学習・適合 |
| predict / apply | 学習済モデルを適用 |
| joblib | scikit-learn モデルの保存形式 |
| Pipeline | 前処理 → 学習を 1 つにまとめる仕組み |
| causal alignment | 未来データを使わない時間整合 |
| look-ahead | 未来データを誤って使うリーク |
| Purged K-Fold | 時系列 CV で train/test 境界に embargo を入れる手法 |
| feature_importance | 各 feature の予測寄与度 |

##### §6.3.7 着地

**fit は train 期間のみ (= k-means / PCA / scaler / k 探索 / 命名 全部) + artifact 名 train 含む必須 + 起動時 assertion + causal alignment 明示 + Stage 1 で 6 項目機械的 verify**

---

## 7. 改訂履歴

| 日付 | 版 | 内容 |
|---|---|---|
| 2026-05-31 | v3.15 | **mlfinlab 除外・全項目 自前実装に修正**（v3.14 の「mlfinlab 活用」撤回）。WebSearch verify: mlfinlab=商用有償ライセンス必須 + Python 3.11 非対応(保守停止) / mlfinpy=Alpha・19ヶ月更新なし → 計器の心臓部に未成熟依存を入れない・アルゴリズムは AFML Ch.4 公開知識を自前実装。**項目A 完成**(`eval_engine.py`・約定/コスト・T1-T5 全pass・commit 66de850) + **項目C 完成**(`sample_uniqueness.py`・AFML Ch.4・C1-C5 全pass)。§6 C-F テーブルに実装ファイル名 + 状態列(✅/⬜)追加。出典: hudsonthames.org/mlfinlab / pypi.org/project/mlfinpy |
| 2026-05-31 | v3.14 | **§6 冒頭「評価基盤 詳細設計（全工程共通）」新設** = §0.8 の実装仕様。A 約定/コスト計器（replay_csv 準拠 + 楽観3点[TP先着/gap無視/touch約定]是正）+ C-F（**mlfinlab 活用**: `sampling` uniqueness/sequential bootstrap・`cross_validation` PurgedKFold・`backtest_statistics` DSR-PBO・`features` fracdiff）+ leak/regime。**各項目に既知答えテスト**（T1-T5 等・監査でなく数学的事実で検証・L-242）。実装順序 A→C→D→E→F→leak/regime・`ml_phase2_production` で再学習不要。WebSearch verify（mlfinlab 実装 / hftbacktest fill）|
| 2026-05-31 | v3.13 | **§0.8「評価の健全性 — PnL を測る正しい計器」新設**（約定/コスト不正インシデント契機）= 業界標準 6 点（①指値約定+net ②コスト現実化 round-trip 0.15-0.30%・fee 2倍検証 ③sample uniqueness+sequential bootstrap ④purge+embargo 別物 ⑤DSR>0.95+PBO<0.5・CPCV ⑥non-stationarity+survivorship 17-22%+look-ahead）+ **文書でなく実装 assertion で物理強制**方針（L-241/L-242）。WebSearch 4 本 verify（StratBase / hftbacktest / Bailey&LdP DSR / AFML 10 reasons / CoinAPI survivorship / ScienceDirect CPCV 2024）。**§0.1/§0.2 は元々正しく実装が守らなかった＝文書追加でなく実装側の問題が本質** |
| 2026-05-30 | v3.12 | §6.3 cluster 設計が実装で 4 件覆る → 実測修正反映（①入力 全投入PCA→揺れ幅28 ②アルゴ GMM hybrid→KMeans単体 ③確率 Isotonic→距離softmax ④門番 0.4→緩和）。現設計は §6.3 冒頭サマリ・**実測経緯/数値変遷は `ml_pipeline_execlog.md` 工程 [2.5]** |
| 2026-05-29 | v3.11 | §6.2.7 scale mismatch 設計欠陥注記追加（z-score 6倍乖離→MFE 97%支配）→ [0,1] clip + data-driven threshold に改訂・E variant で月 275 件達成。**実測経緯/業界 verify は `ml_pipeline_execlog.md` 工程 [2]** |
| 2026-05-26 | v1 | 初版作成 (= 6 工程ドラフト・議論のスタート点) |
| 2026-05-27 | v2 | 6 工程 → 8 工程拡張 (= [1.5] regime + [2.5] cluster 新規追加)・各工程の学習目標 / ラベル / 入出力 / 制約を決着事項として確定・5.1× レバー寄与見積追加 (= ケース B 中央値 5.57×)・WebSearch 業界実証出典追加 |
| 2026-05-27 | v2.1 | §6 工程別詳細設計書 セクション新設 (= 旧 §6 改訂履歴を §7 に繰り下げ)・[1.5] regime 詳細追記 = (1) 評価方法 4 段階 + (2) HMM 再調整方針 (= 本セッション中盤決着事項) |
| 2026-05-27 | v2.2 | §6.0 工程 [1] 特徴量計算層 詳細設計 + §6.3 工程 [2.5] cluster 分類 詳細設計 を追記 (= 前チャット取りこぼし回収・ラベル決着 + 56 ラベル詳細内訳 + 全 7 ホライズン使う決着 + cluster 方針 + cat-bitget 制約逆算根拠) |
| 2026-05-27 | v2.3 | §6.0.2 「学習対象 K 範囲」をデータ駆動判定方針に書き換え (= 事前決め打ち回避・全 7 ホライズン学習後 feature_importance / target importance で各ホライズンの予測寄与を verify・寄与してなければ次回除外) |
| 2026-05-27 | v2.4 | §6.1.3 固定ルール判定器の閾値・判定構造 追記 (= scoring + weighted vote 構造に決着・業界 standard verify 5 件・6 指標 × scoring 表・ATR を方向判定から外しボラ別フラグへ + DI/価格 vs MA/MTF 整合/一目均衡表 追加・元決着からの差分 5 点) |
| 2026-05-27 | v2.5 | §6.1.4 k-means 判定器の設計 追記 (= 業界 standard verify 4 件・4 特徴量入力 [log_returns_1h / rolling_volatility(20) / close_vs_sma20_pct__1h / adx14_1h]・k=3 で HMM と整合・HMM と同じ学習データ/前処理/判定間隔/ヒステリシス・3 判定器の役割分担明示) |
| 2026-05-27 | v2.6 | §6.1.5 ensemble 機構の設計 追記 (= soft voting + 重み付き平均に決着・業界 standard verify 4 件・初期等重み・各判定器の確率変換方法明示・最終判定 + 確信度算出 + 不明確閾値 0.4 + 連続 2 回ヒステリシス) |
| 2026-05-27 | v2.7 | §6.1.6 出力仕様 追記 (= 業界 standard verify 4 件・出力 6 列 [regime_label / prob_up / prob_down / prob_range / confidence / volatility_level]・MTF 1h → 5m forward fill・one-hot encoded 派生列・保存場所 results/regime_step1/ 配下 3 parquet・データフロー明示・「フィルタ強制適用しない」決着整合) |
| 2026-05-27 | v3.10 | **CP3 監査 Verdict PIVOT 全 7 件採用支持で同セッション内反映完了** (= Critical 3 + Major 3 + Minor 1・archive マーク撤去) ・**Critical-1**: §6.3.1 silhouette > 0.3 → > 0.4 (PCA 後高次元現実的目標) + 旧 14 列版 0.15-0.20 架空推定値破棄 → 実装着手時実測確定経路 ・**Critical-2**: §6.3.2 k-means 単体 → K-Means + GMM hybrid (= 楕円対応 + posterior probability native) + HDBSCAN 不採用根拠 min_cluster_size 反証反映で第二段階保留 ・**Critical-3**: §6.3.2 Gaussian kernel → fold 別 Isotonic Regression キャリブレーション + §6.3.1 Stage 1 に Brier/reliability diagram/ECE 追加 (= CP1/CP2 同型対策) ・**Major-1**: §6.3.6 派生 one-hot 推奨 → cluster_id 直接食わせ (= LightGBM 4.6 native handling 業界 standard) + one-hot 第二段階保留 ・**Major-2**: Critical-1 反映で実質解消 (= 全項目試算は実装そのものになる論理) ・**Major-3**: §6.3.1 Stage 3 純増分 1.5× を cluster + Sizing + Exit 3 工程合算寄与と明示 (= cluster 単独責任ではない・cluster 単独 √1.5 ≈ 1.14× 目安) ・**Minor-1**: §6.3.7 leak 経路 7 項目目 entry_id 未来情報依存禁止追加 + §6.3.5 再命名後 Stage 1 再 verify 経路追加 ・WebSearch 4 件 (= silhouette 高次元 / K-Means GMM hybrid / GMM calibration Isotonic Platt / LightGBM 4.6 native categorical / multi-strategy ensemble Sharpe) 業界 standard verify ・L-236 物理強制経路 (= cc_role §1.4.6.2 + Hooks) で「自分の知識内で設計」を物理阻止する状態を構築 ・archive マーク撤去 + CC 慢心怠慢への罰則機能 |
| 2026-05-27 | v3.9 | **§6.3 v3.8 内容を「⛔ 設計し直し対象」マーク (= CP3 監査 Verdict PIVOT 後・L-236)** ・中身の数値・アルゴリズム選定・キャリブレーション処理は再設計必要・枠組み構造 (= 7 サブセクション分割 + Stage 1-4 評価) は参照のみ可 ・**CP3 監査結果** (= `.claude/audits/2026-05-27_step25_cluster_design_cp3_audit_report.md` 422 行・Critical 3 + Major 3 + Minor 1 件 + 構造的指摘) ・**構造的指摘** = CP1/CP2/CP3 と 3 回連続で「メタガード追加が機械的フォーマット化」実証 → ガード追加経路打ち切り + 物理強制 hooks 導入 (= cc_role §1.4.6.2 / `.claude/settings.local.json` + `.claude/hooks/`) ・次セッション = 物理強制経路採用版で §6.3 設計し直し + サブセクションごとの KB Read + WebSearch 強制化 |
| 2026-05-27 | v3.8 | **§6.3 工程 [2.5] cluster 分類 詳細設計 §6.3.0〜§6.3.7 全 7 サブセクション完成** (= regime ensemble §6.1.1〜§6.1.6 / Entry ML §6.2.1〜§6.2.8 と同型構造達成・旧 17 行 (= 方針 + 設計判断の根拠) を廃止して新規 7 サブセクション約 500 行に置換) ・**§6.3.0**: 概要 + 議論順序 (= §6.3.3→§6.3.2→§6.3.4→§6.3.1→§6.3.5→§6.3.6→§6.3.7) 明示 ・**§6.3.1 評価方法**: 4 段階構造 (Stage 1 silhouette > 0.3 + inertia + 偏り + regime 相関 + 旧 14 列版比較 / Stage 2 視認 + Exit 抜き PnL proxy / Stage 3 純増分 (b)/(a) ≥ 1.5× / Stage 4 月次 NET ≥ $1,900) ・**§6.3.2 アルゴリズム選定**: k-means 単体 + k-means++ + Euclidean + Gaussian kernel 確率変換 (σ = cluster median)・第二段階 GMM/HDBSCAN/ensemble 検討経路 ・**§6.3.3 入力特徴量設計**: 案 b 全投入 (= 2,666 列) + PCA 50-100 主成分 + RobustScaler fold 別 fit + regime 統合 ・**§6.3.4 k 決定**: k ∈ {3, 4, 5} 並列試行 + silhouette 最大 + elbow + 業界経験則 (= 3-5 cluster で 1.5× レバー) + 偏り ≥ 5% ・**§6.3.5 ラベル付け**: train 期間で 4 軸 (TP_prob / MFE / SL_prob / 保有時間) post-hoc 命名 → test mapping 適用のみ ・**§6.3.6 出力**: 主要 7 列 (cluster_id / cluster_prob_X / cluster_label / cluster_confidence / cluster_silhouette) + 派生 one-hot 列 + parquet 保存 + entry_id ベース merge ・**§6.3.7 leak 防止**: fit は train 期間のみ (k-means / PCA / scaler / k 探索 / 命名 全部) + artifact 名 train 含む必須 + 起動時 assertion + Stage 1 で 6 項目機械的 verify ・WebSearch 5 件 (= Springer Nature 2025 / PMC 7785332 / PMC 12484065 / MDPI 2025 / DSFE 2025 / Towards Data Science / Medium State-of-the-Art / Built In Elbow / ML Mastery Silhouette) + 教科書整合 AFML Ch.4/16/20 / cc_entry_logic_self_study §14.6/§17.6/§18.3 + cat-bitget 固有 verify (Phase 4-a 14 列 silhouette 0.15-0.20 → 新 PCA 版 > 0.3 期待) + cc_role §1.4.6.1 メタガード 13/14/15 機械運用 + 設計矛盾自己検出 Q&A (= 各サブセクション 2 件以上) + data-driven 経路宣言 (= 各サブセクション 3 項目以上) + 専門用語補足 (= feedback_plain_language 機械運用) ・本セッション L-232/L-233/L-235 改善 2 違反「わかりやすく解説」指摘 6 回連続 → 簡潔版を母体に機械的証跡セクション追記する折衷構造採用 |
| 2026-05-27 | v3.7 | **CP2 監査結果反映完遂** (= [.claude/audits/2026-05-27_step2_entry_ml_design_cp2_audit_report.md](../audits/2026-05-27_step2_entry_ml_design_cp2_audit_report.md) Verdict PIVOT・Critical 2 + Major 2 + Minor 2 件全 6 件採用支持で反映) ・**C1** = §6.2.1 Stage 1 に Brier/reliability/ECE 追加 + §6.2.3 論点 4 fold 別 isotonic regression キャリブレーション必須 (TripleBarrier 14 + meta_label 14)・集約式の入力 prob はキャリブレーション後の値を使用 ・**C2** = §6.2.7 集約式に MFE_pct z-score 標準化 (train_2021_2024 fold 別 mean/std) 追加・第二段階 0-1 ratio 化候補 ・**M1** = §6.2.7 K 重み 0.5/0.1 → 等重み 1/7 ≈ 0.143 に再設計 (= Phase 1 v6 教訓「予測対象を物理的に増やす」と集約段階の論点整合)・第二段階 data-driven 調整 ・**M2** = §6.2.7 即死 reject 危険度定義 = LONG_SL_prob > 0.9 (= Triple Barrier 直接出力)・第二段階 (a)(b) 候補保留 ・**Minor-1** = §6.2.8 項目 5 に phase_compliance §1.4 fractal 3 段階運用 verify_top20_features_leak.py 4 項目セット適用明示 ・**Minor-2** = §6.2.4 論点 6 / §6.2.8 第一原則 に TSFresh whitelist 化 (fc_parameters 指定)・blacklist 候補列挙 + L-179 同型予防経路明示 |
| 2026-05-27 | v3.6 | **§6.2.8 leak 防止 追記 + [2] Entry ML 詳細設計 §6.2.1〜§6.2.8 全 8 サブセクション完成** (= regime ensemble §6.1.1〜§6.1.6 と同型構造達成) ・**第一原則**: false_positive §0-1 Prime Directive 整合 (= t 時点で取得可能な変数のみ) ・**項目 1**: [[feedback_ml_leak_mandatory_check]] 4 点 verify (特徴量 grep / 使用箇所 verify / timestamp range / feature_importance 即時 review) ・**項目 2**: regime 6 列 causal alignment (= §6.1.6 既決着引継ぎ・merge_asof backward + assert no look-ahead) ・**項目 3**: ラベル shift(-K) verify (= phase_compliance §0 Step 5 既決着引継ぎ) ・**項目 4**: CV embargo 2 day (= §6.2.5 既決着引継ぎ) ・**項目 5**: feature_importance top 20 自動 monitoring + 怪しい列名検出 + regime 6 列 top N 入り verify ・**項目 6**: blacklist 64 列除外 verify (= phase_compliance §-1 既決着引継ぎ・assert len(X.columns) == 2610) ・教科書整合 AFML Ch.3 Look-Ahead Bias / AFML Ch.7 Purged K-Fold + Embargo + 業界差分 + cat-bitget 固有 verify (L-179 / L-128 同型予防) + 統計と PnL 分離 + 設計判断根拠 4 件 + 懸念 1 件+反論 + data-driven 経路宣言 ・§6.2 セクション冒頭順次追記予定リストから §6.2.8 削除 + 「§6.2.1〜§6.2.8 全 8 サブセクション完成」明示 |
| 2026-05-27 | v3.5 | §6.2.7 出力 → entry 判定 追記 (= 6 論点決着・全 CC 推奨採用・まこさん OK) ・**論点 1** (= 段階的ルール集約 + 短期 K 重視): 第一段階 LONG/SHORT_score = TP_prob × 0.4 + MFE_pct × 0.3 + meta_yes_prob × 0.3・K 重み K=12/24 = 0.5 主役 / K=6/48/96/144/288 = 0.1 等分・第二段階 meta-learner (= Logistic Regression / Random Forest / Ridge) ・**論点 2** (= 排他 cat_v9 流): score 高い方を採用・hedging は [2.5] cluster で吸収 ・**論点 3** (= CC 決着): confidence = \|LONG_score - SHORT_score\| / max(LONG/SHORT_score) ・**論点 4** (= 第一段階固定 + 第二段階動的検討): 暫定 0.6 + fold 別 calibrate・即死 reject (= 危険度 > 0.9) ・**論点 5** (= CC 決着): primary (= TripleBarrier 3 class) + secondary (= meta_label binary) → §6.2.7 集約 → [3] Sizing Half-Kelly ・**論点 6** (= CC 決着・§6.2.2 第二段階): stacking 採用時 LightGBM 56 + XGBoost 56 → meta-learner ・WebSearch 2 件業界 standard verify (= arxiv 2501.10709 / pm-research Meta-Labeling 2025) + 教科書整合 AFML Ch.3 Meta-Labeling / AFML Ch.6 Ensemble + 業界差分 + cat-bitget 固有 verify + 統計と PnL 分離 + 設計判断根拠 4 件 + 懸念 3 件+反論 + data-driven 経路宣言 ・§6.2 セクション冒頭順次追記予定リストから §6.2.7 削除 |
| 2026-05-27 | v3.4 | §6.2.6 ハイパラ探索 追記 (= 5 論点決着・全 CC 案で進行・まこさん OK) ・**論点 1**: Optuna (= ベイズ最適化) 20-50 trials + TPE sampler + MedianPruner ・**論点 2**: §13.1 業界 range + L1/L2 正則化追加 ・**論点 3**: 3 系統別 tune (= 揺れ幅 28 = regression / TripleBarrier 14 = multiclass + class_weight balanced / meta_label 14 = binary + scale_pos_weight) ・**論点 4**: 計算コスト約 11 時間 (= CPU only 1 日以内実用範囲) ・**論点 5**: 第一段階 LightGBM のみ tune・第二段階 (= Stage 3 後 stacking 採用時 + meta-learner Logistic/Random Forest/Ridge) で別 tune ・教科書整合 AFML Ch.6 / Hudson & Thames mlfinlab Optuna + 業界 standard 差分 + cat-bitget 固有 verify + 統計と PnL 分離 + 設計判断根拠 4 件 + 懸念 2 件+反論 + data-driven 経路宣言 ・§6.2 セクション冒頭順次追記予定リストから §6.2.6 削除 |
| 2026-05-27 | v3.3 | §6.2.5 CV 設計 追記 (= 5 論点決着・全 CC 案で進行・まこさん OK) ・**論点 1**: 5 fold (= regime ensemble §6.1.4 と同型) ・**論点 2**: train_2021_2024 + test_2025 + test_2026_q1 (= phase_compliance §0 既決着) ・**論点 3**: embargo = K_max 288 bar + buffer 1 day = 2 day ・**論点 4**: Purged 範囲 = K_max 288 bar を train から除外 (= AFML Ch.7) ・**論点 5**: CPCV (= 計算コスト 27h) は第一段階保留・第二段階 (Stage 3 NET 純増分 < 2.0×) で発動・教科書整合 AFML Ch.7 §7.3 Purged K-Fold §7.4 Embargo / AFML Ch.12 CPCV + cat-bitget 固有 verify + 統計と PnL 分離 + 設計判断根拠 4 件 + 懸念 1 件+反論 + data-driven 経路宣言 ・§6.2 セクション冒頭順次追記予定リストから §6.2.5 削除 |
| 2026-05-27 | v3.2 | §6.2.4 入力特徴量設計 追記 (= 6 論点決着) ・**論点 1** (= まこさん判断「案 A 統合」採用): 1 LightGBM + regime 6 列入力・第二段階で regime 間 accuracy 差 > 30% なら案 B (= regime 別 model 分離 4 倍化) 検討経路 ・**論点 2**: 全投入 (= 2,604 + regime 6 = 2,610 列) + Stage 1 feature_importance post-pruning ・**論点 3**: MTF 8 TF integrated 維持 (= 既決着) ・**論点 4**: §6.1.6 既決着維持 (= one-hot + 確率値併用) ・**論点 5**: 前処理なし (= LightGBM default 機能) ・**論点 6**: 第一段階既存 1,462 維持 + Stage 3 で TSFresh 追加検討 (= leak チェック必須) ・WebSearch 3 件業界 standard verify (arxiv 2509.09751 Meta-Learning RL Crypto / arxiv 2303.02223 Feature Selection Annealing / Preprints 202603.0994 MTF Bitcoin) + 教科書整合 cc_role §1.7 / AFML Ch.6 + 業界 standard 差分 + cat-bitget 固有 verify + 統計と PnL 分離 + 設計判断根拠 4 件 + 懸念 2 件+反論 + data-driven 経路宣言 ・§6.2 セクション冒頭順次追記予定リストから §6.2.4 削除 |
| 2026-05-27 | v3.1 | §6.2.3 ラベル設計詳細 追記 (= 5 論点決着) + §6.0.2 Triple Barrier 閾値部分を §6.2.3 論点 3 への参照 + 価格非依存化注記に改訂・**論点 1**: K 重み付けなし維持 (= 全 7 ホライズン並列) ・**論点 2**: LONG/SHORT ラベル定義レベルで既分離・追加対策不要 (= dual-task 整合) ・**論点 3** (= まこさん判断「案 C」採用): 価格非依存化 (ATR→ATR_pct・L-179 同型予防) + K 別 multiplier data-driven (短期 K=6/12 = TP×1.5/SL×2.0 cat_v9 流 / K=24 = TP×2.0/SL×2.0 中間 / K=48 = TP×2.5/SL×1.5 中間 / 長期 K=96/144/288 = TP×3.0/SL×1.5 AFML 流) ・**論点 4** (= まこさん判断「CC 推奨」採用): TripleBarrier 14 = class_weight=balanced 第一段階 + Stage 1 recall<0.3 で SMOTE/focal loss 第二段階 / meta_label 14 = scale_pos_weight ・**論点 5**: 並列学習のみ決着・接続は §6.2.7・WebSearch 3 件業界 standard verify (Mudrex/Bitget Wiki/arxiv 2508.14656/LightGBM Issue #6807,#3167) + 教科書整合 AFML Ch.3 (Triple Barrier + Meta-Labeling) + cat-bitget 固有 verify (cat_v9 P1-P25 TP/SL 経験値) + 業界 standard 差分 + 統計と PnL 分離 + 設計判断根拠 4 件 + 懸念 2 件+反論 + data-driven 経路宣言 |
| 2026-05-27 | v3.0 | §6.2.1 評価方法 追記 (= 4 段階構造・regime ensemble §6.1.1 と同型・Stage 1 内部スコア [揺れ幅 28 RMSE/R² + 決着 28 multiclass logloss/F1/AUC/Precision/Recall + feature_importance leak verify + 56 ラベル間予測相関] + Stage 2 視認 + Exit 抜き PnL proxy [Phase 1 v6 教訓反映・統計と PnL 乖離の早期検出] + Stage 3 PnL 早期判定 [base line 旧 Priority v9 月 $370・純増分 (b)/(a) ≥ 5.1× で目標達成] + Stage 4 最終 PnL [Phase 5 全 12 ヶ月 NET ≥ $1,900])・WebSearch 3 件業界 standard verify・教科書整合 AFML Ch.7・統計指標と PnL 分離明示 (改善 9)・設計判断根拠 3 件・懸念 1 件 + 反論・data-driven 経路宣言 (改善 12)・§6.2 セクション冒頭順次追記予定リストから §6.2.1 削除 |
| 2026-05-27 | v2.9 | §6.2 工程 [2] Entry ML 詳細設計 セクション新設 + §6.2.2 アルゴリズム選定 追記 (= LightGBM native multi-output 非対応制約反映 + 2 段階アプローチ「第一段階 LightGBM 単独 + 第二段階 Stage 3 stacking 比較」決着・WebSearch 3 件業界 standard verify・教科書整合 AFML Ch.3/Ch.6・設計判断根拠 4 件・懸念 1 件 + 反論・data-driven 経路宣言) + §1 [2] Entry ML 表現修正 (= LightGBM Multi-output → LightGBM 56 個独立並列学習 + scikit-learn MultiOutputRegressor 補足) + §4 表記同期 |
| 2026-05-27 | v2.8 | **CP1 監査 (= 2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md) 結果反映** (= Verdict PIVOT・Critical 2 + Major 3 + Minor 2 件全 7 件採用支持 + プロセス欠陥対策 P1 cc_role §1.4.6.1 改善 10/11/12 追加): §6.1.1 Stage 1 内部スコアに Brier score / reliability diagram / ECE + 3 判定器予測誤差 Pearson 相関 追加 (= 観点 1 / Q5 改善 1) / §6.1.1 Stage 3 を v15 単独 + ensemble の 2 段階比較に変更 (= M1) / §6.1.1 Stage 3 合格基準を純増分 (b)/(a) 評価に変更 / §6.1.3 ATR 絶対値 250/100 を ATR_pct 25th/75th percentile data-driven に変更 (= C2 価格非依存性違反修正) / §6.1.4 k=3 事前決め打ちを k ∈ {2,3,4,5} elbow + silhouette data-driven に変更 (= m2) / §6.1.5 確率変換に isotonic regression キャリブレーション追加・k-means は Gaussian kernel 経由 (= C1 soft voting 前提条件 verify) / §6.1.5 初期等重みを Walk-Forward + GridSearchCV data-driven に変更 (= M2) / §6.1.6 forward fill を merge_asof(direction="backward") causal alignment 明示 + assert no look-ahead 追加 (= M3 look-ahead leak 防止) |

---
## 8. 工程別 実行ログ → `ml_pipeline_execlog.md` に分離 (2026-05-30)

> **実行ログ・実測・現在地・次セッション着手は [`ml_pipeline_execlog.md`](ml_pipeline_execlog.md) に分離した** (まこさん指示・新セッション誤解防止)。
>
> **理由**:
> - ① 新セッションが「経緯」を最初に読む導線を明確化 (誤解なく建設的に議論を始めるため)
> - ② 設計確定 (本ファイル §6) の編集だけ WebSearch hook で gate し、記録・整理の追記は gate しない (= 提案前ベースアップという hook 本来の意図に整合・「追記のために検索」の本末転倒を解消)
>
> **3 層構造 (分離後)**:
> - **本ファイル `ml_pipeline_baseline_v1.md` = 設計の正本** (§1-§7)・WebSearch hook 対象
> - **`ml_pipeline_execlog.md` = 実装の実行・実測・現在地ログ + フロー意図** (旧 §8)・hook 対象外・**新セッションは最初にこれを読む**
