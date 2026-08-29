# technical_analysis_knowledge_base.md — テクニカル分析ナレッジベース (辞典レベル)

作成: 2026-05-22 (CC・cc_role v1)
版: v2 (辞典レベル拡張・WebSearch 42 件 + Gemini 見解 2 件統合)
位置付け: Phase 0 改修指示書 v2 + 今後の ML pipeline 設計の参照素材
状態: 運用しながら追記・改訂

---

## §0 本ファイルの位置付け・運用ルール

### 0.1 なぜこのファイルが必要か

2026-05-22 セッションで CC が「テクニカル分析の基礎を知らなかった」「設計時に業界知見を起動できなかった」「Web 調査を能動的にしなかった」事例が**累積 27+ 件**発覚。

`web_claude_self_check.md §限界の自覚`「知識として持っているのに起動されない」構造的問題に対し、**知識を文書化して毎セッション必読化** することで物理的に起動を強制する正本ファイル。

### 0.2 運用ルール (絶対遵守)

- **Phase 0 改修・Phase 1〜7 ML 設計判断の前に必読**
- 機械的証跡 (`wc -l` + Read 全文 view + 該当箇所引用) を出す
- **本ファイルに記載のない業界知識が必要になった場合は WebSearch / WebFetch で能動調査** (cc_role §1.0 義務)
- 調査結果は本ファイルに追記・引用 URL 明記
- CC 単独で「知ってる」と判断しない・**Gemini 等外部見解 + /audit + まこさん検閲の 3 経路** で確認

### 0.3 CC の業界知識レベル正直版

| 知識領域 | レベル |
|---|---|
| 指標・手法の定義・計算式 | ◯ (Wikipedia レベル) |
| 教科書的使い方 | △ (浅い) |
| 実運用経験知 | ❌ (ゼロ) |
| 相場局面別有効性 | ❌ (ゼロ) |
| 組合せ優劣判断 | ❌ (ゼロ) |

→ **CC の「知ってる」発言の信頼度は低い**。本ファイルに記載のない領域は能動的に WebSearch 必須。

---

## §1 パラメータ vs 閾値の本質 (Gemini 見解 #1・2026-05-22 受領)

### 1.1 パラメータ = 感度調整・時間軸定義

**役割**: インジケーターの計算期間・標準偏差倍率等の可変数値 (= センサーの感度調整)

| 操作 | 効果 |
|---|---|
| 数値を小さく (例: rsi7) | 直近の値動きに敏感反応・ダマシ (偽シグナル) 増 |
| 数値を大きく (例: rsi21) | 滑らかなデータでダマシ減・売買サイン遅延 |

**ML への組み込み方**:
- 1432 指標カタログ = 既存パラメータの並列展開済
- 未投入パラメータを追加して ML に並列提供 → **ML が「どの感度が最良か」を学習データから自動選択**

### 1.2 閾値 = 売買境界線・リスク/リターン制御

**役割**: 売買アクションの境界線 (= ブレーキを踏む車間距離)

| 操作 | 効果 |
|---|---|
| 閾値を厳しく (例: RSI 20 以下で買い) | 勝率上がる・取引チャンス激減 |
| 閾値を緩く (例: RSI 40 以下で買い) | 取引チャンス増・負けトレード増 |

**ML への組み込み方** (4 アプローチ):
1. **LightGBM 自動分割** (現状デフォルト): 決定木が閾値を自動学習
2. **手動閾値フラグ化 (CSV §A-3.6 A 案)**: cat_v9 P1〜P25 の発火条件を bool 列化 → Phase 0 改修で実装
3. **後処理フィルタ (B 案)**: 学習後・発火判定時に手動 Priority 条件で filter → Phase 4-b-2 or Phase 5
4. **cluster 入力に追加 (C 案)**: Phase 3-b cluster 入力ベクトルに bool 列追加

---

## §2 MTF + コンフルエンス + 相互補完の本質 (Gemini 見解 #2)

### 2.1 MTF を組み合わせる理由

**原則**: 「短期足の波は、長期足の波に飲み込まれる」

- **目的 1: 環境認識**: 長期足で方向性確認 + 短期足でタイミング = 大きな流れに逆らわない
- **目的 2: 引き付け精度**: 長期足で「買い場」判定 + 短期足でピンポイント反転狙い = 損切り幅最小化

### 2.2 複数指標を組み合わせる理由 (相互補完)

| 系統 | トレンド時 | レンジ時 |
|---|---|---|
| **トレンド系 (MA/MACD)** | 強い | 往復ビンタ (ダマシ) |
| **オシレーター系 (RSI/Stoch)** | 100/0 張り付き・機能停止 | 天井と底を綺麗に捉える |

**対策**: MACD or MA で「トレンドが出ていること」を確認 → RSI で「そのトレンドの中の一時的な押し目」を狙う

### 2.3 コンフルエンス = 自己実現的予言

**定義**: 複数のテクニカル根拠が同一価格水準で重なる現象 → **世界中のトレーダーが意識するため反転確率が跳ね上がる**

例: 「MA 反発 AND Fib 61.8% AND RSI < 30」(3 根拠重複) >> 「MA 反発のみ」(1 根拠)

### 2.4 cat_v9 P3 (LONG) はコンフルエンスの実装例

```
Stoch ゴールデンクロス     ← オシレーター系・トリガー
AND BB middle slope > 10    ← トレンド系・トレンド確認
AND ADX ∈ [30, 50)          ← トレンド系・強さ確認
AND ATR ≥ 250               ← ボラ系・ボラ十分性
```

= **トレンド系 + オシレーター系 + ボラ系のコンフルエンス**

---

## §3 テクニカル指標 業界標準分類 (5 カテゴリ + 二次タグ)

### 3.1 メイン 5 カテゴリ (Britannica / StockCharts ChartSchool / Altrady 整合)

| カテゴリ | 役割 | 代表指標 | 使うべき局面 |
|---|---|---|---|
| **Trend (トレンド系)** | 方向確認 | MA / EMA / SMA / Parabolic SAR / Ichimoku / ADX (方向) | トレンド相場 |
| **Momentum / Oscillator (オシレーター系)** | 買われすぎ/売られすぎ | RSI / MACD / Stochastic / RCI / Williams %R / CCI / MFI | レンジ・反転検知 |
| **Volatility (ボラ系)** | 価格変動測定・SL 設定 | Bollinger Bands / ATR / Keltner / Realized Volatility | SL/TP 幅算出 |
| **Volume (ボリューム系)** | 買い/売り圧力 | OBV / MFI / CMF / Volume Profile (POC/VAH/VAL) / VWAP | 価格動向確認 |
| **Support / Resistance** | 価格水準識別 | Pivot Points / Fibonacci / Donchian / Trendlines | 反転・ブレイクポイント |

### 3.2 二次タグ: Leading vs Lagging

| タグ | 性質 | 代表 |
|---|---|---|
| **Leading (先行)** | 将来予測・トレンド転換前 | RSI / Stochastic / CCI / Fibonacci |
| **Lagging (遅行)** | 既存トレンド確認 | MA / MACD / ADX (強さ) / Bollinger Bands |

---

## §4 5 分足スキャル特化知見

### 4.1 5 分足の本質

- **極めてノイズ多** (小さな注文・ニュース・流動性で分単位で bullish↔bearish 切替)
- 遅い TF 用指標は機能困難
- レンジトレード (サポレジ間) が defacto standard

### 4.2 5 分足での RSI 期間設定 (BTCC academy 整合)

| 期間 | 特徴 | 適用 |
|---|---|---|
| **RSI(7)** | 最速反応・ダマシ多 | 早期エントリー型スキャル |
| **RSI(9)** | 速度と安定のバランス・**5 分足最人気** | 5 分足デフォルト推奨 |
| **RSI(14)** | 標準・遅い | 中時間軸との比較用 |
| **RSI(21)** | 安定・ダマシフィルタ強 | 中期スキャル |

→ Phase 0 改修で **RSI(9) と RSI(21) を新規追加**。

### 4.3 cat_v9 との対応

- cat_v9 全 Priority が 5 分足ベース
- 1m 足回帰は禁止 (CLAUDE.md §⛔ エッジゼロ確認済)
- 3m 足は Layer 2 検討中

---

## §5 MTF 業界ベストプラクティス

### 5.1 黄金律

1. **常に最高 TF から分析開始 → 下位 TF へ** (top-down approach)
2. **上位 TF トレンドに逆らわない** (golden rule)
3. **エントリーは下位 TF・確認は上位 TF**

### 5.2 勝率改善の実証データ

- **3 TF 以上でシグナル一致のみ取引** → 単一 TF 勝率 **42% → MTF 61%** (研究実証)

### 5.3 シフト設計 (偽シグナル防止)

| TF 用途 | shift 設計 | 理由 |
|---|---|---|
| エントリー TF (5m) | shift=0 (現在足) | シグナル形成中でも捉える |
| 確認 TF (30m / 1h / 4h) | shift=1 (確定足) | 形成中バーの偽シグナル防止 |

### 5.4 Phase 0 改修への反映

- 既存 1432 指標は 5m/15m/30m/1h/4h/1d の 6 TF 並列 ✅
- **1w/1M 追加**: 長期トレンド方向確認の階層強化
- **MTF 整合 bool 列追加**: 3+ TF 一致時の bool
- **既存 mtf_slope_align_3way 拡張**: 3 TF → 5 TF (1h/4h/1d/1w/1M) 整合
- **shift 設計**: 上位 TF (1h/4h/1d/1w/1M) は shift=1 (確定足) を強制

---

## §6 Lopez de Prado AFML / mlfinlab パッケージ

### 6.1 AFML (Advances in Financial Machine Learning・2018)

金融機械学習の業界バイブル・**全 21 章**。Phase 1〜7 設計の参考書。

### 6.2 主要技術

| 章 | 技術 | 内容 | 本プロジェクト対応 |
|---|---|---|---|
| Ch.2 | Financial Data Structures | Time/Tick/Volume/Dollar Bars | **v1 完全欠落** → Phase 0 改修対象外だが Layer 2 候補 |
| Ch.3 | Triple Barrier Method | TP/SL/TIME の 3 クラス分類 | §B-13 Layer 3 記載済 |
| Ch.3 | Meta-Labeling | 1 段階予測 → 2 段階で採用/見送り判定 | §B-13 Layer 3 記載済 |
| **Ch.4** | **Sample Weights** | 同時刻ラベル重複の uniqueness 正規化 | **v1 未記載・Phase 0 改修で検討** |
| **Ch.5** | **Fractional Differentiation** | 非定常 → 定常変換 + 最大記憶保持 | §B-12 d={0.3, 0.5} 記載済 ✅ |
| Ch.7 | Cross-Validation in Finance | Purged K-Fold | §B-14 Layer 3 記載済 |
| Ch.7+ | CPCV | Combinatorial Purged CV | §B-14 Layer 3 記載済 |
| Ch.14 | Backtest Statistics | Deflated Sharpe Ratio 等 | Phase 5 評価で参考 |

### 6.3 mlfinlab パッケージ (Hudson & Thames)

- **AFML 全章を Python 実装**
- `pip install mlfinlab`
- GitHub: hudson-and-thames/mlfinlab
- 主要モジュール:
  - **Data Structures**: tick / volume / dollar bars + 情報駆動 bars
  - **Labeling**: Triple-Barrier / Meta-Labeling / Trend Scanning / Tail Sets / Matrix Flags
  - **Feature Engineering**: Fractionally Differentiated / Structural Breaks / Volatility Estimators / Auto Feature Extraction
  - **Bet Sizing**: Kelly Criterion / EF3M / 動的 bet sizes

---

## §7 業界カタログパッケージ (実装ライブラリ)

### 7.1 pandas-ta-classic (212 指標・最強)

- **150 Technical Indicators + 62 Candlestick Patterns** (合計 212)
- 9 カテゴリ: Candles (67) / Momentum / Overlap / Trend / Volume / Statistics / Volatility / Performance / Cycles
- `pip install pandas-ta-classic`
- GitHub: xgboosted/pandas-ta-classic
- Phase 0 改修 業界カタログ追加の **第一候補ソース**

### 7.2 TA-Lib (150+ 指標・defacto standard)

- C 実装 + Python wrapper
- `pip install TA-Lib` (要 C ライブラリ)
- GitHub: TA-Lib/ta-lib-python

### 7.3 mlfinlab (Lopez de Prado AFML 実装)

- AFML 全章 Python 実装
- `pip install mlfinlab`

### 7.4 ta (現状 cat_v9 で使用中)

- 軽量・基本指標のみ
- `pip install ta`
- cat/indicators.py L3 で使用中 (継続)

### 7.5 Stefan Jansen "Machine Learning for Algorithmic Trading" 教科書

- O'Reilly + GitHub (stefan-jansen/machine-learning-for-trading)
- **Ch.4 Financial Feature Engineering** + **Alphalens / SHAP** + **100+ alpha factors appendix**
- 本ファイル v2 設計の参考

---

## §8 BTC 暗号通貨特有指標

### 8.1 Funding Rate

**役割**: Perpetual Futures の spot 価格との乖離を抑える均衡メカニズム

| 状態 | 内容 |
|---|---|
| 正値 (+0.05% 以上) | LONG が SHORT に支払い・**強気センチメント** |
| 極値 (+0.08% 90th percentile 以上) | 過熱・**コントラリアン short シグナル** |
| 負値 (-0.01% 以下) | SHORT が LONG に支払い・弱気センチメント |
| 極端負値 (-0.1% 以下) | **歴史的に全ての主要 relief rally に先行** |

**精算間隔**: 8 時間ごと (00:00 / 08:00 / 16:00 UTC)
**Bitget 実測** (exchange_spec.md L26-28・audit#19 確定): median +0.0002%/8h baseline / p95 0.01%/8h stress / p05 -0.0141%/8h

### 8.2 Open Interest (OI) 分析

**定義**: 未決済の futures/perpetual 契約総数 = 市場のレバレッジ量の最良単一測定値

| 組合せ | 解釈 |
|---|---|
| OI↑ + price↑ | 新規 long 参入・トレンド継続 |
| OI↑ + price↓ | 新規 short 参入・下落継続 |
| OI↓ + price↑ | short 決済・買い戻し |
| OI↓ + price↓ | long 利確 |
| OI↑ + funding 正値 | long 過熱・サポート割れで long liquidation 連鎖 |
| OI↑ + funding 負値 | short 過熱・レジスタンス突破で short liquidation 連鎖 |

### 8.3 Liquidation Heatmap (CoinGlass)

- レバレッジ強制清算が起きる価格レベルをマップ化
- **Magnet Effect**: 価格は密集クラスター (清算多発予想点) に引き寄せられる
- **Stop Hunts**: 価格 wick がクラスターを sweep
- **設定方針**: ストップを密集クラスター内に置かない (Market makers が hunt する)

### 8.4 Active Addresses (オンチェーン)

- ネットワーク活性度の測定
- 採用率向上に応じて長期的に増加
- 価格下落時に減少 (投機家離れ)

### 8.5 NUPL (Net Unrealized Profit/Loss)

- 市場参加者の含み損益から市場心理を測定
- Bitcoin 主要高値・安値の予測に使用
- 市場 cap が利益確定より遥かに速く上昇 → 過熱

### 8.6 MVRV Z-Score

- **計算**: (Bitcoin market value - realized value) / market value 標準偏差
- **解釈**: 市場価値が公正価値からどれだけ乖離しているか
- **臨界閾値**:
  - > 6.5 → 極端高値・**過去全 cycle top を高精度予測** (±2 週)
  - < 0 (負値) → 極端安値・**過去全 cycle bottom を予測**
- 限界: 過熱状態が数週間〜数ヶ月続く可能性 (timing 不確実)

### 8.7 SOPR (Spent Output Profit Ratio)

- **計算**: USD value of spent outputs at spent time / USD value at created time
- **解釈**:
  - SOPR = 1.0 → net neutral
  - SOPR > 1.0 → 利益実現 (高いほど profit-taking 強)
  - SOPR < 1.0 → 損失実現 (低いほど panic selling)
- **変種**:
  - **aSOPR (Adjusted SOPR)**: < 1 時間取引除外・経済的に意味ある移動のみ
  - **STH-SOPR (Short-Term Holder)**: < 155 日保有者
  - **LTH-SOPR (Long-Term Holder)**: > 155 日保有者

### 8.8 半減期サイクル (Halving Cycle)

- BTC 4 年サイクル (半減期 2012 / 2016 / 2020 / 2024 / 2028 予定)
- **2024 半減期**: 2024-04-19・block reward 6.25 → 3.125 BTC
- **歴史パターン**: 半減期前 rally → 短期 correction → 大上昇 + blow-off top → 半減期後 約 18 ヶ月でピーク
- 2024-2025 cycle: ATH $126,198 (2025-10-06・100% rally from halving)

### 8.9 Stock-to-Flow (S2F) Model (PlanB)

- **計算**: S2F = Stock / Flow
- **価格式**: Price = 0.18 × (S/F)^3.3 (95% historical correlation)
- 半減期で flow 半減 → S2F 倍増
- **限界**: 需要・流動性・マクロ要因を考慮しない・近年予測精度低下

### 8.10 Pi Cycle Top Indicator (Philip Swift・Bitcoin Magazine Pro)

- **計算**: 111-Day MA と 350-Day MA × 2 のクロス
- **数学的接続**: 350/111 ≈ 3.153 ≈ π (3.142)
- **歴史実績**: 2013 / 2017 / 2021 の major top を **3 日以内** に予測
- 2017-12-17 シグナル → 3 日後に $19,783 ATH (-84% correction)

### 8.11 ETF Flow

- **2024 Spot BTC ETF 米国承認** (機関マネーフロー指標)
- **BlackRock IBIT**: 2026-02 時点 $54.12B AUM (786,300 BTC)
- IBIT 大量 inflow = 機関 accumulation 明確シグナル

### 8.12 Whale Holdings + Exchange Flows

- **Whale 定義**: ≥ 1,000 BTC アドレス
- **Smart Money Signal**: Whale は fear で buy・greed で distribute (counter-cyclical)
- **Exchange Inflow**: 取引所への流入 = 売り圧力増 (bearish)
- **Exchange Outflow**: 取引所からの流出 = HODL 意図 (bullish)
- **Netflow** = Inflow - Outflow

---

## §9 CC の知識限界・運用上の注意

### 9.1 構造的バイアス警告 (cc_role §1.4 + web_claude_self_check §限界の自覚 同型)

| バイアス | CC が陥る癖 |
|---|---|
| 「知識として持っているのに起動できない」 | 定義は知ってるが設計時に能動的に問わない |
| 「箇条書きをコピーで処理した気になる」 | handoff 等の箇条書きを反映して「網羅した」と錯覚 |
| 「Web 調査をスキップする」 | cc_role §1.0「能動的に活用」を毎セッション忘れる |
| 「『業界カタログ』と書いて済ませる」 | 具体的に調査せず抽象論で済ます |
| 「列数 30-60 の数字で具体化した気になる」 | 設計思想を問う前に「具体化した」と錯覚 |

### 9.2 累積実証 (handoff v21 §0.27 + 本セッション)

| 期間 | 件数 |
|---|---|
| handoff v19 §0.13 (1 週間前) | 5 件 |
| handoff v20 §0.26 | 5 件 |
| handoff v21 §0.27 | 8 件 |
| 本セッション (2026-05-22) | 9+ 件 |
| **累積** | **27+ 件** |

→ **CC 単独確定の信頼度はゼロ**。

### 9.3 安全策 (4 経路必須)

1. **まこさん検閲を前提手続き化**
2. **/audit 監査経路を着手前から並行起動**
3. **Gemini 等外部見解 (まこさんが Gemini にプロンプト → 貼り)**
4. **WebSearch / WebFetch 能動活用 (cc_role §1.0 義務・本ファイル更新)**

### 9.4 設計判断前のチェックリスト

- [ ] **本ファイル Read 全文 view** (機械的証跡 `wc -l` + 該当箇所引用)
- [ ] 該当領域の知識が本ファイルにあるか確認・なければ **WebSearch 能動調査**
- [ ] 調査結果を本ファイルに追記・URL 明記
- [ ] cat_v9 実装との対応を grep verify (L-180)
- [ ] Phase 0 改修等の指示書作成時、Gemini 見解 + /audit 経路を着手前から並行起動
- [ ] CC 単独で「知ってる」「網羅した」と判断しない

---

# §A 個別指標 辞典 (WebSearch 詳細・42 件 反映)

## §A.1 RSI (Relative Strength Index)

### A.1.1 計算式
```
RS = Average Gain (n bars) / Average Loss (n bars)
RSI = 100 - (100 / (1 + RS))
```
n = 通常 14 期間 (Wilder default)

### A.1.2 パラメータ別特性 (5 分足の場合)
| 期間 | 反応速度 | ダマシ | 用途 |
|---|---|---|---|
| RSI(7) | 最速 | 多 | 早期エントリー型スキャル |
| **RSI(9)** | 速・安定バランス | 中 | **5 分足最人気** |
| RSI(14) | 標準 | 少 | 中〜上位 TF |
| RSI(21) | 安定 | 最少 | 中期スキャル |

### A.1.3 閾値解釈
- **> 70 = overbought** (買われすぎ)
- **< 30 = oversold** (売られすぎ)
- **強トレンド時**: extreme 値が長期間維持される (張り付き)

### A.1.4 Divergence 分析
- **Bullish Divergence**: price lower lows + RSI higher lows → 反転 up
- **Bearish Divergence**: price higher highs + RSI lower highs → 反転 down

### A.1.5 cat_v9 対応
- cat_v9 で SHORT_RSI_PERIOD=21 + SHORT_RSI_THRESH=50 + SHORT_RSI_SLOPE_N=3 (P24/P21 RSI Reverse Exit)
- P2_RSI_MIN=45 / P4_RSI_MAX=60 / P24_RSI_MIN=65 / P23_BREAKOUT_RSI_MIN=70 等の閾値

### A.1.6 Phase 0 改修
- RSI(9) + RSI(21) 追加 (現状 RSI(7)/RSI(14) のみ)
- RSI Divergence bool 列追加 (bullish / bearish)
- RSI ROC (まこさん発振系) 追加

---

## §A.2 MACD (Moving Average Convergence Divergence)

### A.2.1 計算式
```
MACD Line = EMA(12) - EMA(26)
Signal Line = EMA(9) of MACD Line
Histogram = MACD Line - Signal Line
```

### A.2.2 標準パラメータ
- (12, 26, 9) = 業界 defacto standard
- (5, 13, 5) = 短期版
- (19, 39, 9) = 長期版

### A.2.3 解釈
- **Golden Cross**: MACD line が signal line を **上抜け** → bullish
- **Dead Cross**: MACD line が signal line を **下抜け** → bearish
- **Histogram > 0**: 上昇モメンタム強・bar が高いほど強い
- **Histogram < 0**: 下落モメンタム強

### A.2.4 Divergence
- Price higher highs + Histogram lower highs → reversal
- Histogram は line より早期シグナル

### A.2.5 cat_v9 対応
- P1_MACD_FAST=12 / P1_MACD_SLOW=26 / P1_MACD_SIGNAL=9 (P1/P21 Macd Cross)
- 標準パラメータ採用

### A.2.6 Phase 0 改修
- MACD 短期 (5,13,5) + 長期 (19,39,9) 並列追加
- MACD Histogram slope (まこさん発振系) 追加
- MACD Divergence bool 列追加

---

## §A.3 ADX (Average Directional Index)

### A.3.1 計算式 (Wilder 1978)
- **+DI**: 上昇方向の DI (高値比較)
- **-DI**: 下落方向の DI (安値比較)
- **ADX**: smoothed average of |+DI - -DI| / (+DI + -DI) × 100
- 期間: 14 (default)

### A.3.2 閾値解釈
| ADX 値 | 解釈 |
|---|---|
| < 20 | 弱トレンド (no trend) |
| 20-25 | emerging trend |
| > 25 | **強トレンド** (主要シグナル) |
| > 50 | exhaustion (反転リスク) |

### A.3.3 方向性
- **+DI > -DI**: buyers dominant (上昇圧力)
- **-DI > +DI**: sellers dominant (下落圧力)
- **+DI/-DI クロス + ADX 上昇** = 真のトレンドシフト
- **ADX < 20 でクロス** = 信頼度低い (40% 失敗率増・2026 研究)

### A.3.4 cat_v9 対応
- P1_ADX_MIN=30 / P2_ADX_MIN=30 + ADX_EXCL=[40,50) / P3_ADX_MIN=30 + ADX_MAX=50
- P21_ADX_MIN=22 / P22_ADX_MIN=22 / P22_ADX_RELAX_MIN=22
- P23_ADX_MIN=30 + ADX_MAX=50 + P23_HIGH_ADX_THRESH=40 + P23_HIGH_ADX_ATR_MIN=200
- P24/P25 ADX 系条件多数

### A.3.5 Phase 0 改修
- ADX(7) + ADX(21) 追加 (現状 ADX(14) のみ)
- +DI / -DI 個別列の維持 (既存 di_diff/di_minus/di_plus 拡張)
- ADX velocity (1 bar / 3 bar 変化) 追加候補

---

## §A.4 ATR (Average True Range)

### A.4.1 計算式
```
True Range = max(H-L, |H-PrevClose|, |L-PrevClose|)
ATR(n) = average of True Range over n periods
n = 14 (default)
```

### A.4.2 用途
- ボラティリティ測定 (方向性なし)
- **SL 設定**: N × ATR (N = 1.5-3 が標準)
- **Trailing Stop**: Chandelier Exit
- **Position Sizing**: account_risk / (ATR × multiplier)

### A.4.3 Chandelier Exit (Chuck LeBeau)
```
Long Exit  = Highest High (22) - 3 × ATR(22)
Short Exit = Lowest Low (22)  + 3 × ATR(22)
```
- Default: (22, 3.0)
- **Volatility expand 時 → SL 自動緩和** (whipsaw 回避)

### A.4.4 Multiplier 推奨
| 用途 | Multiplier |
|---|---|
| 短期スキャル | 1.0-1.5 × ATR |
| Swing (4H) | 2.0 × ATR |
| Trend Following (Daily) | 3.0 × ATR |
| 高ボラ instrument | 高 multiplier |

### A.4.5 cat_v9 対応
- P1_ATR14_MIN=60 / P1_ATR14_MAX=9999
- P2_ATR14_MIN=100 / P2_ATR14_MAX=300
- P3_ATR14_MIN=250 / P4_ATR14_MIN=150
- P21_ATR14_MIN=60 / P22_ATR14_MIN=60 / P23_ATR14_MIN=150 / P24_ATR14_MIN=30 / P25_ATR14_MIN=60
- 既存 atr14_pct (atr_14 / close × 100) で価格非依存化済

### A.4.6 Phase 0 改修
- ATR(7) + ATR(21) 追加 (現状 ATR(14) のみ)
- Chandelier Exit 計算結果を bool 列化 (現値 vs CE_long / vs CE_short)

---

## §A.5 Bollinger Bands

### A.5.1 計算式
```
Middle Band = SMA(20)
Upper Band  = SMA(20) + 2 × StdDev(20)
Lower Band  = SMA(20) - 2 × StdDev(20)
BandWidth   = ((Upper - Lower) / Middle) × 100
%B          = (Close - Lower) / (Upper - Lower)
```
Default: (20, 2.0)

### A.5.2 %B 解釈
- > 1.0 = 上バンド突破 (overbought)
- 0.5 = middle band (neutral)
- < 0.0 = 下バンド突破 (oversold)

### A.5.3 BandWidth 状態
| BandWidth | 状態 | 解釈 |
|---|---|---|
| < 10% | **Squeeze** | 極端低ボラ・大きな価格動の前兆 |
| 上昇 | **Expansion** | ボラ拡大・トレンド形成 |
| 下落 | **Contraction** | ボラ縮小・レンジ化 |

### A.5.4 Band Walk
- Upper band に張り付き → **強気モメンタム継続**
- Lower band に張り付き → **弱気モメンタム継続**
- → これは「逆張りシグナル」ではなく「順張り継続シグナル」

### A.5.5 cat_v9 対応
- P21_TP_BB_RATIO=1.0 / P21_TP_MIN_PCT=0.0003
- P3/P4_BB_MID_SLOPE_MIN=10/20 / P4_BB_MID_SLOPE_MEAN5_MIN=15
- P22_SHORT_BB_MID_SLOPE_MAX=-20 / P23_BB_MID_SLOPE_MAX=-10
- P23_BREAKOUT_BB_WIDTH_MIN=0.03 / P22_SHORT_BB_WIDTH_MAX=999
- P24_BB_SLOPE_MAX=50

### A.5.6 Phase 0 改修
- BB(10) + BB(50) window 並列追加 (現状 BB(20) のみ)
- BB Squeeze bool 列 (BW < 10%) 追加
- BB %B 列追加 (既存 bb_pct_b は 1d/1h のみ → 6 TF 補完)
- BB slope 派生列 (まこさん発振系) 追加

---

## §A.6 Stochastic Oscillator

### A.6.1 計算式 (George C. Lane・1950s)
```
%K = (Close - Lowest Low(n)) / (Highest High(n) - Lowest Low(n)) × 100
%D = SMA(3) of %K
J  = 3K - 2D  (KDJ 拡張版)
```
n = 5 / 9 / 14 (default 14)

### A.6.2 閾値解釈
- **%K > 80 / %D > 80** → overbought
- **%K < 20 / %D < 20** → oversold
- **%K > 90 / %D > 80** → extreme overbought (K 高速確認・D 低速主要)

### A.6.3 Golden / Dead Cross
- **Golden Cross**: %K が %D を **上抜け** + 20 以下なら短期 buy 信号
- 「W パターン」(50 以下で 2 回 golden cross) = 強い上昇予兆
- **Dead Cross**: %K が %D を **下抜け** + 80 以上なら短期 sell 信号
- 「M パターン」(50 以上で 2 回 dead cross) = 強い下落予兆

### A.6.4 Divergence
- Price new high + Stoch no new high = bearish divergence
- Price new low + Stoch no new low = bullish divergence

### A.6.5 cat_v9 対応
- P2/P3 Stoch Golden Cross (LONG)・P23 Dead Cross (SHORT)
- P2_STOCH_GAP_MIN=0.3 / P2_STOCH_K_MIN=0 (gap > 0.3 で発火)
- P23_STOCH_K_MAX=999 / P23_STOCH_REVERSE_EXIT_ENABLE=true
- P23_STOCH_EXIT_MFE_GATE=20 / P23_STOCH_EXIT_MIN_HOLD=150
- P24_STOCH_MIN=60

### A.6.6 Phase 0 改修
- Stoch(5m) 追加 (現状 stoch_k は 1d のみ・他 TF 欠落)
- Stoch K-D 差分 (まこさん発振系) 追加
- KDJ J 線追加候補

---

## §A.7 Ichimoku Kinko Hyo (一目均衡表)

### A.7.1 起源・パラメータ
- 1930s 細田悟一 (Goichi Hosoda) 開発・1968 出版
- (9, 26, 52) = 当時の日本市場 6 営業日/週ベース
- 30 年バックテストで確定

### A.7.2 5 構成要素
| 要素 | 計算式 | 役割 |
|---|---|---|
| **Tenkan-sen (転換線)** | (Highest High + Lowest Low) / 2 (9 期間) | 短期モメンタム |
| **Kijun-sen (基準線)** | 同 (26 期間) | 中期トレンド |
| **Senkou Span A (先行スパン A)** | (Tenkan + Kijun) / 2 → **26 bar 先行** | Cloud 上端/下端 (速い) |
| **Senkou Span B (先行スパン B)** | (52 期間 mid-point) → **26 bar 先行** | Cloud 上端/下端 (遅い) |
| **Chikou Span (遅行スパン)** | 現在 close を **26 bar 後ろ** にプロット | トレンド確認 |

### A.7.3 Kumo (雲)
- Senkou Span A と Span B の間の領域
- 価格が雲の上 = bullish / 雲の下 = bearish / 雲の中 = neutral
- 雲が厚い = 強いサポレジ

### A.7.4 cat_v9 対応
- 既存 ichimoku_kijun (絶対 USD) + ichimoku_tenkan (絶対 USD) は **Phase -1 blacklist 対象** (48 列)
- close_vs_kijun_pct (3 TF のみ) は pct 化済
- **Phase 0 改修**: close_vs_tenkan_pct 全 6 TF 追加 (現状未投入) + Senkou Span A/B 比較列追加候補

---

## §A.8 Fibonacci Retracement + Extension

### A.8.1 主要レベル
| Retracement | Extension | 解釈 |
|---|---|---|
| 23.6% | 127.2% | 浅い (Conservative target) |
| 38.2% | 161.8% | **Golden Ratio・最重要** |
| 50% | 261.8% | medium (Conservative + aggressive 中間) |
| **61.8%** | **golden ratio extension** | **最重要 retracement (反発確率最高)** |
| 78.6% | — | 深い (trend reversal リスク) |

### A.8.2 Golden Zone
- 38.2% - 61.8% の間 (50% 含む) = **反転高確率ゾーン**

### A.8.3 自己実現的予言
- 数百万のトレーダーが Fib level を意識 → 真の support/resistance 化
- 61.8% に近づくと thousands of buy orders → genuine support

### A.8.4 cat_v9 対応
- 既存 dist_to_fib_382/500/618/786_pct + dist_to_fib_v2_*_pct (1432 指標に含む)
- nearest_fib_distance_pct + nearest_fib_v2_distance_pct

### A.8.5 Phase 0 改修
- Fib Extension (127.2% / 161.8% / 261.8%) 距離列追加候補
- **Fib + 他指標コンフルエンス bool** (例: Fib 61.8% AND RSI < 30 AND MA 反発)

---

## §A.9 Volume Profile (POC / VAH / VAL / HVN / LVN)

### A.9.1 構成要素
| 要素 | 略 | 意味 |
|---|---|---|
| Point of Control | **POC** | 最大出来高価格 (price magnet) |
| Value Area High | **VAH** | Value Area 上端 |
| Value Area Low | **VAL** | Value Area 下端 |
| Value Area | **VA** | 出来高 70% が集中する範囲 |
| High Volume Node | **HVN** | 出来高ピーク = 受容領域 (magnet) |
| Low Volume Node | **LVN** | 出来高谷 = 価格高速通過 |

### A.9.2 取引応用
- Price が VA 外 → 戻る確率 **80%** で対岸 (反対 VA boundary) まで往復
- HVN = institutional order blocks と整合
- LVN = Fair Value Gaps と整合 (SMC との接続)

### A.9.3 cat_v9 対応
- 既存 dist_to_POC_pct (49 列・6 TF) + dist_to_VAH/VAL_pct (N=50/100/200 × b=020/050/100 の 9 パターン × 6 TF)
- inside_value_area_*_pct (9 パターン × 6 TF)

### A.9.4 Phase 0 改修
- HVN / LVN 距離列 (新規候補)
- VA breakout direction bool (上 vs 下)

---

## §A.10 Pivot Points (5 種類)

### A.10.1 Standard (Floor)
```
PP = (Prev_High + Prev_Low + Prev_Close) / 3
R1 = 2 × PP - Prev_Low
R2 = PP + (Prev_High - Prev_Low)
S1 = 2 × PP - Prev_High
S2 = PP - (Prev_High - Prev_Low)
```

### A.10.2 Woodie's
```
PP = (Prev_High + Prev_Low + 2 × Prev_Close) / 4  ← close 重み付け
```

### A.10.3 Camarilla (Day Trader 人気)
```
R1 = Prev_Close + (Prev_High - Prev_Low) × 1.1 / 12
S1 = Prev_Close - (Prev_High - Prev_Low) × 1.1 / 12
R2/R3/R4 = 同様 (1.1 / 6, 4, 2)
```
- 8 turning points (上下各 4)
- 狭い・精密 → intraday mean-reversion 向け

### A.10.4 Fibonacci Pivot
- Standard PP + (Prev_High - Prev_Low) × Fib levels (38.2% / 61.8% / 100%)

### A.10.5 cat_v9 対応
- 既存 dist_to_PP_pct + dist_to_R1/R2/S1/S2_pct (1432 指標に含む)

### A.10.6 Phase 0 改修
- Camarilla R3/R4/S3/S4 追加候補 (Day Trader 人気)

---

## §A.11 RCI (Rank Correlation Index・Spearman)

### A.11.1 計算式
```
RCI = (1 - 6 × Σ(d²) / (n × (n² - 1))) × 100
d = time_rank - price_rank
n = window 期間
```

### A.11.2 標準期間 (Triple-period 採用)
- **Short (9)**: 短期モメンタム
- **Mid (26)**: 中期モメンタム
- **Long (52)**: 長期モメンタム

### A.11.3 解釈
- **+80 以上** = strong upward consistency (反転狙い shorts ↓)
- **-80 以下** = strong downward consistency (反転狙い longs ↑)
- **0 line cross** = clean trend change signal
- 3 期間同時クロス = 強い反転シグナル

### A.11.4 cat_v9 対応
- cat/indicators.py L66 `RCI_WINDOWS = [7, 9, 26, 52]` (rci_7/9/26/52 既存実装)
- **P22 (SHORT)**: RCI(7)/RCI(9) デッドクロス + RCI(52) > 55 (P22_RCI52_MIN)

### A.11.5 Phase 0 改修
- rci_26 が 10_indicator_families に登録されているか verify (実装はあるが catalogue 未登録疑い)
- 3 期間 cluster (cross detection) bool 列追加候補
- TF 補完 (現状 1d のみの可能性・要 verify)

---

## §A.12 Williams %R

### A.12.1 計算式
```
Williams %R = (Highest High(n) - Close) / (Highest High(n) - Lowest Low(n)) × -100
```
- 出力範囲: 0 ～ -100 (RSI の負値版)
- n = 14 (default)

### A.12.2 閾値解釈
- **0 ～ -20** = overbought
- **-80 ～ -100** = oversold

### A.12.3 Divergence
- Bullish: price lower low + %R higher low (oversold 領域)
- Bearish: price higher high + %R lower high (overbought 領域)

### A.12.4 期間別
- 短期 (5/7/9) → 速・ノイズ多・スキャル向け
- 14 = standard
- 長期 (21+) → 安定

### A.12.5 cat_v9 対応
- 既存 williams_r (1d のみ・1432 指標カタログ)

### A.12.6 Phase 0 改修
- williams_r TF 補完 (現状 1d のみ → 6 TF 補完候補)

---

# §B チャートパターン・ローソク足 辞典

## §B.1 ローソク足 (Japanese Candlestick) パターン

### B.1.1 単一ローソク
| パターン | 形状 | 意味 |
|---|---|---|
| **Doji** | open ≈ close (十字) | 迷い・反転候補 |
| **Hammer** | 短実体上部 + 長下髭 (≥ 2 倍) | 下降後の bullish reversal |
| **Shooting Star** | 短実体下部 + 長上髭 | 上昇後の bearish reversal |
| **Inverted Hammer** | 短実体下部 + 長上髭 (下降後) | bullish reversal 候補 |
| **Pin Bar** | 長髭 + 短実体 | 反転圧力 |

### B.1.2 2 本パターン
| パターン | 意味 |
|---|---|
| **Bullish Engulfing** | 2 本目が 1 本目を完全包む (上昇) → 反転 up |
| **Bearish Engulfing** | 同 (下降) → 反転 down |
| **Bullish Harami** | 2 本目が 1 本目内に収まる (上昇) |
| **Bearish Harami** | 同 (下降) |
| **Piercing Pattern** | 下降 → 翌日陽線が前日陰線中点超え |
| **Dark Cloud Cover** | 上昇 → 翌日陰線が前日陽線中点割れ |

### B.1.3 3 本パターン
| パターン | 意味 |
|---|---|
| **Morning Star** | 下降 + Doji/小実体 + 大陽線 → bullish reversal |
| **Evening Star** | 上昇 + Doji/小実体 + 大陰線 → bearish reversal |
| **Three White Soldiers** | 3 連続上昇陽線 → 強い bullish reversal |
| **Three Black Crows** | 3 連続下落陰線 → 強い bearish reversal |
| **Three Inside Up/Down** | Harami + 確認 bar |

### B.1.4 主要 10 パターン (推奨学習)
1. Hammer / Inverted Hammer
2. Shooting Star
3. Bullish/Bearish Engulfing
4. Morning/Evening Star
5. Doji
6. Three White Soldiers / Three Black Crows
7. Harami

### B.1.5 cat_v9 対応
- 既存 bearish_engulfing / bullish_engulfing / bearish_streak / bullish_streak (1432 指標カタログ)
- pinbar_top / pinbar_bottom

### B.1.6 Phase 0 改修
- pandas-ta-classic 62 candlestick patterns 一括追加候補 (TA-Lib も同等)

---

## §B.2 チャートパターン (反転 + 継続)

### B.2.1 反転パターン (Trend Reversal)
| パターン | 形状 | 信頼度 |
|---|---|---|
| **Head & Shoulders (HS)** | 3 ピーク (中央が最高) | **89%** (最高) |
| **Inverse HS** | HS の逆 | 高 |
| **Double Top** | 2 同高ピーク + 戻り | 高 |
| **Double Bottom** | 2 同安ボトム + 戻り | **88%** (高) |
| **Triple Top/Bottom** | 3 同高/同安 | 高 |
| **Rounding Top/Bottom** | 緩やかな逆 U / U 字 | 中 |
| **Broadening Formation** | 拡大三角 (高値切上 + 安値切下) | 中 |
| **Falling/Rising Wedge** | 収束型 | 中 |

### B.2.2 継続パターン (Trend Continuation)
| パターン | 形状 | 信頼度 |
|---|---|---|
| **Bull Flag** | 上昇後の小レンジ (旗) | **85%** (高) |
| **Bear Flag** | 下降後の小レンジ | 高 |
| **Bull/Bear Pennant** | 小三角 | 高 |
| **Ascending Triangle** | 水平上限 + 上昇下限 | 中-高 |
| **Descending Triangle** | 水平下限 + 下落上限 | 中-高 |
| **Symmetrical Triangle** | 収束型 (方向中立) | 中 |
| **Rectangle** | 水平レンジ | 中 |
| **Rising/Falling Channel** | 平行チャネル | 中 |

### B.2.3 ブレイクアウト・ボラパターン
| パターン | 意味 |
|---|---|
| **Cup and Handle** | カップ + ハンドル (継続) |
| **Volatility Squeeze** | BB Squeeze 同等 |
| **Coil Range Breakout** | 蓄積後ブレイク |

### B.2.4 Price Target (Measured Move)
| パターン | 目標計算 |
|---|---|
| HS | neckline → head の距離をブレイク点から投影 |
| Double Top/Bottom | 高さを ブレイク点から投影 |
| Bull Flag | flagpole 高さを breakout から投影 |
| Triangle | 最広部を breakout から投影 |
| Cup and Handle | カップ深さを breakout から投影 |

### B.2.5 Phase 0 改修
- ChartPattern 検出 bool 列追加候補 (pandas-ta-classic 候補・自前実装難)

---

## §B.3 Dow Theory (6 原則)

### B.3.1 原則
1. **Market Discounts All**: 価格に全情報が織り込まれている
2. **Three Trends**:
   - **Primary** (主要・1 年〜数年・bullish/bearish)
   - **Secondary** (中間・10 日〜3 ヶ月)
   - **Minor** (短期・数時間〜1 ヶ月)
3. **Primary Trends 3 Phases**:
   - **Accumulation** (スマートマネー買い集め)
   - **Public Participation** (一般参加)
   - **Distribution** (スマートマネー売り抜け)
4. **Higher Highs + Higher Lows** (uptrend) / Lower Highs + Lower Lows (downtrend)
5. **Trend Confirmation Through Multiple Indices** (industrial + transportation 等)
6. **Volume Confirmation**: トレンド方向に出来高増

### B.3.2 cat_v9 / Phase 0 改修
- Higher High / Higher Low bool 列追加候補 (Trend confirmation)
- Volume increasing bool 列追加候補

---

## §B.4 Elliott Wave Theory

### B.4.1 構造
- **Impulse Wave (推進波)**: 5 波動 (1, 2, 3, 4, 5)
- **Corrective Wave (修正波)**: 3 波動 (a, b, c)
- **完全 cycle**: 8 波動

### B.4.2 3 ルール (必須)
1. Wave 2 は Wave 1 を 100% 以上 retrace しない
2. Wave 3 は 3 推進波 (1, 3, 5) の中で最短ではない
3. Wave 4 は Wave 1 価格範囲と重ならない (例外稀)

### B.4.3 Fibonacci 関係
- Wave 2 retrace 50-61.8% of Wave 1
- Wave 3 extend 161.8% of Wave 1 (most common)
- Wave 4 retrace 23.6-38.2% of Wave 3
- Wave 5 = 0.618 × Wave 3

### B.4.4 Corrective patterns
- **Zigzag (5-3-5)**: 急峻修正
- **Flat (3-3-5)**: 横ばい修正
- **Triangle (3-3-3-3-3)**: 収束修正

### B.4.5 Phase 0 改修
- Elliott Wave count は実装難・人手分析中心 → Phase 0 改修対象外
- 代替: swing high/low 検出 bool (既存 bars_since_swing_high/low_W に含む)

---

## §B.5 Harmonic Patterns (XABCD)

### B.5.1 主要パターン (XABCD 5 ピボット)
| パターン | AB レッグ retrace | BC レッグ | CD 終点 |
|---|---|---|---|
| **Gartley** | 61.8% of XA | 38.2% of XA | 78.6% of XA |
| **Bat** | 38.2-50% of XA | - | - |
| **Butterfly** | 78.6% of XA | - | 161.8% extension |
| **Crab** | - | - | **161.8% extension of XA** (深い) |
| **Shark** | - | - | - |
| **Cypher** | - | - | - |

### B.5.2 取引応用
- **Reversal pattern**: 点 D でエントリー (C or それ以上に戻り期待)
- Cleaner on higher TF (1h / 4h / daily)

### B.5.3 Phase 0 改修
- Harmonic 検出は実装難・対象外
- 代替: Fibonacci 距離列 + swing high/low 既存活用

---

## §B.6 Wyckoff Method (1930s Richard Wyckoff)

### B.6.1 中核概念
- **Composite Man**: 機関投資家の集合体仮想モデル
- **Accumulation**: スマートマネー買い集め (markup 前)
- **Distribution**: スマートマネー売り抜け (markdown 前)

### B.6.2 5 Phases
| Phase | 役割 | 期間 |
|---|---|---|
| **A** (Stopping previous trend) | climactic events で旧トレンド終了 | 1-3 週 |
| **B** (Building cause) | 機関蓄積/分散 (最長 phase) | 4-16 週 (40-70%) |
| **C** (Final test) | **Spring/Shakeout** (accumulation) or **UTAD** (distribution) | 1-2 週 |
| **D** (Breakout) | Sign of Strength/Weakness | 2-4 週 |
| **E** (Sustained trend) | markup or markdown | 可変 |

### B.6.3 重要イベント
- **Spring** (accumulation): support 以下への偽 breakdown + **low volume confirm** → major buy signal
- **UTAD (Upthrust After Distribution)**: resistance 以上への偽 breakout (distribution の鏡像) → major sell signal

### B.6.4 Phase 0 改修
- Wyckoff phase 検出は実装難・対象外
- 代替: support break + volume 低下 bool 列追加候補 (Spring 検知 proxy)

---

# §C 高度分析 辞典

## §C.1 Divergence Analysis (Regular vs Hidden)

### C.1.1 Regular Divergence (Reversal Signal)
| 種類 | Price | Indicator (RSI/MACD) | 解釈 |
|---|---|---|---|
| **Bullish Regular** | lower low | higher low | 下降終了・反転 up |
| **Bearish Regular** | higher high | lower high | 上昇終了・反転 down |

### C.1.2 Hidden Divergence (Continuation Signal・トレンド継続)
| 種類 | Price | Indicator | 解釈 |
|---|---|---|---|
| **Bullish Hidden** (uptrend) | higher low | lower low | 押し目買い継続 |
| **Bearish Hidden** (downtrend) | lower high | higher high | 戻り売り継続 |

### C.1.3 推奨 RSI 設定
- **40-50 zone bullish hidden divergence**: 最強
- **25-30 zone**: pullback ではなく構造的 trend change 警告

### C.1.4 MACD Histogram 推奨
- Line ではなく **Histogram** で divergence (earlier signal)

### C.1.5 Phase 0 改修
- Bullish/Bearish Regular Divergence bool 列追加 (RSI + MACD + Stoch)
- Hidden Divergence bool 列追加
- 既存 div_rsi14_14b / div_macd_14b (1432 指標) の拡張

---

## §C.2 Smart Money Concepts (SMC) / ICT

### C.2.1 Order Block (OB)
- **定義**: 機関が大量注文を置いた価格ゾーン = 強い impulsive move を破壊する直前の **反対色最終ローソク**
- **有効要件**:
  - **Displacement** (大実体陰陽線で強い move)
  - **Break of Structure** (前 swing high/low をブレイク)
  - **Imbalance** (Fair Value Gap を残す)

### C.2.2 Fair Value Gap (FVG)
- 3-ローソクパターン
- ローソク 1 の wick と ローソク 3 の wick が重ならない (gap)
- **70% の FVG が数セッション内に fill** (磁石効果)

### C.2.3 Liquidity
- = pending orders (stop loss + 限定 order)
- **Liquidity Grab**: スマートマネーが liquidity 領域を sweep して逆方向に動く

### C.2.4 Break of Structure (BOS) / CHOCH
- **BOS**: 前 swing high/low をブレイク → トレンド継続/反転
- **CHOCH (Change of Character)**: トレンドの変化点

### C.2.5 Bullish/Bearish Order Block
- Bullish OB = 上昇 impulse 前の **最後の bearish ローソク** (= institutions が買った場所) → 戻ったら support
- Bearish OB = 下降 impulse 前の **最後の bullish ローソク** (= institutions が売った場所) → 戻ったら resistance

### C.2.6 Python 実装
- GitHub: joshyattridge/smart-money-concepts (ICT smart money concepts for algorithmic trading)

### C.2.7 Phase 0 改修
- Order Block bool 列追加候補
- FVG 残存 bool + FVG fill 候補列
- BOS / CHOCH bool 列

---

## §C.3 Market Profile / TPO

### C.3.1 概念 (J. Peter Steidlmayer・1980s)
- TPO = Time Price Opportunity (時間価格機会)
- 価格レベル別の市場滞在時間を文字でマップ化

### C.3.2 主要構成
- **Initial Balance (IB)**: 最初の 1 時間 (or 最初の 2 TPO 期間 A/B) の price range
- **Range Extension**: IB を超える move
- **Value Area (VA)**: 取引活動の 70% が起きた範囲
- **POC (Point of Control)**: 最大 TPO 価格

### C.3.3 Day Types
| Day Type | 特徴 |
|---|---|
| **Neutral Day** | IB 両側で限定 range extension・市場迷い |
| **Normal Day** | 広い IB・以後 distribution は IB 内に収まる |
| **Trend Day** | range extension が IB の 2 倍超・最終 close が extension extremity 近く |

### C.3.4 Phase 0 改修
- Market Profile は intraday session 概念 → 24/7 crypto に直接適用困難
- Volume Profile (既存・dist_to_POC_pct 等) で代替済

---

## §C.4 VWAP (Volume Weighted Average Price)

### C.4.1 計算式
```
VWAP = Σ(Price × Volume) / Σ(Volume)
```

### C.4.2 用途
- **Intraday institutional execution benchmark**
- buy が VWAP 以下 / sell が VWAP 以上 → 機関 execution quality 良好
- Day trader: trend = price vs VWAP

### C.4.3 Standard Deviation Bands
- **±2 SD = primary mean reversion threshold** (95% price action 内包)
- **+3 SD = extreme overvaluation** (pullback 高確率)
- **-3 SD = extreme oversold**

### C.4.4 Anchored VWAP (AVWAP)
- Manual anchor point から VWAP 計算
- earnings / session high 等の specific event 起点
- Swing context に最適

### C.4.5 cat_v9 対応
- 既存 close_vs_vwap20_pct (4 TF) ← TF 補完候補
- Anchored VWAP 未実装

### C.4.6 Phase 0 改修
- VWAP + 2 SD bands 距離列追加候補
- Anchored VWAP は anchor 自動化が課題 → Phase 0 対象外

---

## §C.5 Order Flow / Footprint Chart / CVD

### C.5.1 概念
- 実行された取引をリアルタイム分析 (誰が・いつ・どれだけ)
- 通常 volume indicator (集計) より深い

### C.5.2 Footprint Chart
- ローソク内の **価格レベル別 bid volume + ask volume** 表示
- 各価格ステップに 2 値 (bid 成行 / ask 成行)

### C.5.3 Cumulative Delta (CVD)
- 各 bar の delta (bid - ask volume) を **running total**
- buying / selling pressure の連続蓄積

### C.5.4 Imbalance
- ある価格レベルで **片側が 5x 以上 dominant** = 一方向圧力強

### C.5.5 Absorption
- 大成行 volume が市場 hit したが price 動かず
- → 大 passive participant (limit order) が吸収 = 反転シグナル

### C.5.6 Phase 0 改修
- Bitget API で order flow data 取得可能か未調査 → Layer 2 候補
- 既存 volume_ratio_20b / cmf_20 / obv_slope_10b / mfi_14 で部分代替

---

## §C.6 Supply and Demand Zones

### C.6.1 概念
- 機関活動が起きた価格範囲 = 未約定 order + 価格 magnet
- Rally-Base-Rally (RBR) / Drop-Base-Drop (DBD) パターン

### C.6.2 Demand Zone (Accumulation)
- base = buyers が selling pressure を吸収して上昇前
- 強い demand sign + 買 entry candidate

### C.6.3 Supply Zone (Distribution)
- 大陰線でゾーンから下落 = institutional selling pressure
- 売 entry candidate

### C.6.4 Fresh vs Tested Zones
- **Fresh Zone**: 価格未戻り = 最高 probability (unfilled institutional orders 健在)
- **Tested Zone**: 既に price 戻り済み = probability 低下

### C.6.5 Phase 0 改修
- Demand/Supply zone 検出 bool 列追加候補
- Fresh zone bool 列追加候補

---

# §D ML for Trading 辞典 (AFML + mlfinlab + Stefan Jansen)

## §D.1 Triple Barrier Method (Lopez de Prado AFML Ch.3)

### D.1.1 3 つの Barrier
| Barrier | 内容 | ラベル |
|---|---|---|
| **Upper Barrier (TP)** | 固定 % above entry | **+1 (profit)** |
| **Lower Barrier (SL)** | 固定 % below entry | **-1 (loss)** |
| **Vertical Barrier (TIME)** | 固定 N 期間後 | **0 (neutral)** |

### D.1.2 利点
- 実際の取引メカニクスを反映 (TP/SL/TIME)
- naive fixed-horizon labeling より高品質
- 多クラス分類で「TP first / SL first / TIME first」を直接学習

### D.1.3 本プロジェクト対応
- Phase 1-c で smoke 実施済 (smoke NO-GO・entropy lift 6.04%)
- Layer 3 投入候補 (3 案未達時)

---

## §D.2 Meta-Labeling (Lopez de Prado AFML Ch.3)

### D.2.1 概念
- 2017 Lopez de Prado (Guggenheim Partners + Cornell) 開発
- **Primary model**: trade direction (LONG/SHORT/Flat) を予測
- **Secondary model**: primary 予測の correctness を予測 (bet size)
- **Side と Size を分離**

### D.2.2 効果
- Precision を sacrificing recall なしで改善
- F1-score + Sharpe Ratio 向上
- **高 recall を一部 precision に trade-off** が前提

### D.2.3 業界採用
- Multi-manager hedge funds / 系統的 traders / algorithmic research platforms
- "professional quantitative finance で最も広く採用された技術の 1 つ"

### D.2.4 本プロジェクト対応
- Layer 3 投入候補 (3 案未達時)
- AFML Ch.3 推奨閾値 < 10% (primary model lift) → Phase 1-c smoke で 6.04% (投入域)

---

## §D.3 Fractional Differentiation (AFML Ch.5)

### D.3.1 問題意識
- 金融時系列は **non-stationary** + **low signal-to-noise**
- 標準的整数差分 → 記憶完全消失 = signal 更に低下

### D.3.2 解決
- **Fractional Differencing**: 定常性 + **最大記憶保持**
- weights を fractional d (例 0.3, 0.5) で計算
- Lopez de Prado 推奨 d 値範囲: 0.3-0.5

### D.3.3 本プロジェクト対応
- learning_design_v4 §B-12 で記載済 (d={0.3, 0.5})
- Phase 0 改修で mlfinlab 経由実装候補

---

## §D.4 Sample Weights (AFML Ch.4)

### D.4.1 問題意識
- Triple Barrier ラベルは **同時刻ラベル重複** (overlapping outcomes) を生む
- 標準 ML 学習は各サンプル独立を仮定 → 重複時の bias

### D.4.2 解決手法
- **Number of Concurrent Labels**: 各サンプルの同時並行ラベル数
- **Average Uniqueness**: ラベルの平均独自性
- **Bagging Classifiers + Uniqueness**: bagging で uniqueness 反映
- **Sequential Bootstrap**: leak 防止 sampling

### D.4.3 本プロジェクト対応
- v1 未記載 → Phase 0 改修 or Layer 1 で検討
- mlfinlab で実装済

---

## §D.5 Combinatorial Purged Cross-Validation (CPCV・AFML Ch.7+)

### D.5.1 問題意識
- 金融時系列は **temporal dependencies** + **non-stationarity**
- 標準 K-fold CV は **lookahead bias** + 単一 path testing

### D.5.2 CPCV の仕組み
- 複数 train-test split を **systematically** 構築
- **Purging**: overlapping samples 削除
- **Embargo**: テストデータ後の一定期間を訓練から除外 (情報漏洩防止)

### D.5.3 効果
- **Probability of Backtest Overfitting (PBO)** 大幅低減
- **Deflated Sharpe Ratio (DSR)** 改善
- 複数 path 分布 → より rigorous 統計推論
- 単一 market regime 依存削減

### D.5.4 本プロジェクト対応
- learning_design_v4 §B-14 Layer 3 記載済
- Phase 2/Phase 3-a ハイパラ調整時に採用候補 (現状: train 末尾 10% valid)

---

## §D.6 mlfinlab パッケージ全モジュール

### D.6.1 Hudson & Thames mlfinlab (production-ready)
- GitHub: hudson-and-thames/mlfinlab
- `pip install mlfinlab`

### D.6.2 主要モジュール
| モジュール | 内容 |
|---|---|
| **Data Structures** | tick / volume / dollar bars + 情報駆動 bars |
| **Labeling** | Triple-Barrier / Meta-Labeling / Trend Scanning / Tail Sets / Matrix Flags |
| **Feature Engineering** | Fractionally Differentiated / Structural Breaks / Volatility Estimators / Auto Feature Extraction |
| **Bet Sizing** | Kelly Criterion / EF3M / 動的 bet sizes |
| **Cross-Validation** | Purged K-Fold / CPCV |
| **Backtest Statistics** | Deflated Sharpe Ratio / Bailey-Lopez de Prado tests |

### D.6.3 本プロジェクト対応
- Phase 0 改修で **Fractional Diff** + **Bar 選定** + **Sample Weights** 候補
- Phase 5 評価で **Deflated Sharpe Ratio** 採用候補

---

## §D.7 Stefan Jansen "Machine Learning for Algorithmic Trading"

### D.7.1 書籍構成
- 2nd edition (2020)
- GitHub: stefan-jansen/machine-learning-for-trading
- **Ch.4 Financial Feature Engineering**: alpha factor research
- **付録: 100+ alpha factors** (新版追加)

### D.7.2 主要技術
- **Alphalens**: signal content evaluation
- **SHAP values**: feature importance
- **Backtrader + Zipline**: backtesting frameworks
- **Autoencoder**: risk factor extraction
- **GAN**: synthetic training data
- **CNN on time series**: image format で return prediction

### D.7.3 本プロジェクト対応
- Phase 1 feature_importance review に SHAP 採用候補 (現状: LightGBM gain)
- Alphalens は equity 向けで暗号通貨 BTC 単一 instrument では限定的

---

# §E 本プロジェクトへの統合ガイド (Phase 0 改修への反映)

## §E.1 Phase 0 改修で追加すべき新カテゴリ統合表

| # | カテゴリ | 由来 | 列数見積 |
|---|---|---|---|
| 1 | A-1 欠損指標 8 件 | 既存 v1 §2.1 | +約 8-48 |
| 2 | A-1 まこさん発振系 3 件 | 既存 v1 §2.1 | +約 18 |
| 3 | A-1 業界カタログ (pandas-ta-classic 212 から選定) | §A-§B 全網羅・§A.1-A.12 + §B.1-B.6 反映 | +約 100-300 |
| 4 | A-5 1w/1M MTF 拡張 | 既存 v1 §2.2 | +約 290 |
| 5 | A-5 既存 145 ファミリー TF 欠落補完 | §A.6/A.7/A.11/A.12 で具体化 | +約 50-100 |
| 6 | B-12 Fractional differentiation d={0.3, 0.5} | §D.3 (mlfinlab) | +約 60 |
| 7 | B-12 PCA 補助列 | 既存 v1 | +約 20-50 |
| 8 | A-3 (a) パラメータ並列展開 | §A.1-A.5 補完 (rsi9/21/28/42・adx7/21・bb10/50・macd 短期/長期) | +約 30-60 |
| 9 | A-3 (b) + D-γ 統合 = 手動 Priority + 共通フィルタ bool | cat_v9 grep 結果 (約 50 閾値) | +約 50-100 |
| 10 | B-12 MTF 展開方式 4 通り選定 | §5 MTF ベストプラクティス (shift 設計含む) | 0 (選定のみ) |
| 11 | **§A.5 BB Squeeze + Band Walk bool** | §A.5.3-A.5.4 | +約 12 |
| 12 | **§A.6 KDJ J 線 + Stoch K-D divergence** | §A.6 | +約 12-18 |
| 13 | **§C.1 Divergence bool (Regular + Hidden)** | §C.1 (RSI/MACD/Stoch × Regular/Hidden) | +約 30-60 |
| 14 | **§C.2 SMC bool (Order Block + FVG + BOS)** | §C.2 (Python 実装 GitHub joshyattridge) | +約 20-40 |
| 15 | **§C.6 Supply/Demand Zone bool** | §C.6 | +約 10-20 |
| 16 | **§8.1 Funding rate 特徴量化** | §8.1 (10 派生列) | +約 10-15 |
| 17 | **§8.2 Open Interest 特徴量化** (要 API verify) | §8.2 | +約 5-10 |
| 18 | **§A.4 Chandelier Exit 距離列** | §A.4.3 | +約 12 |
| 19 | **§A.8 Fib Extension 距離列** | §A.8 (127.2/161.8/261.8) | +約 18 |
| 20 | **§B.1 Candlestick patterns 62 種** | §B.1 (pandas-ta-classic 62 candlestick patterns 一括) | +約 62-372 (6 TF) |

**合計**: 約 800-1500 列追加 → **1432 + 800-1500 = 約 2200-2900 列** (見込み拡張)

→ 元の見込み「2000-2500 列」を上回るため、優先順位付け必要。

## §E.2 優先順位付け (CC 推奨)

| 優先 | カテゴリ | 理由 |
|---|---|---|
| **High** | 1-10 (v1 既存 + cat_v9 統合) | Phase 0 改修の核 |
| **High** | 13 (Divergence bool) | 既存 div_macd_14b / div_rsi14_14b の拡張・実装軽 |
| **High** | 16 (Funding rate 特徴量化) | exchange_spec.md L26-28 で確定値あり・即実装可 |
| **Medium** | 11 (BB Squeeze + Band Walk) | 高 ROI・実装軽 |
| **Medium** | 14 (SMC Order Block + FVG) | GitHub Python 実装あり・高 ROI |
| **Medium** | 15 (Supply/Demand Zone) | 中 ROI |
| **Medium** | 18 (Chandelier Exit 距離) | Exit 設計 (Phase 4-b-1) で重要 |
| **Medium** | 19 (Fib Extension) | 既存 Fib retracement の補完 |
| **Low** | 12 (KDJ J 線) | Stochastic 拡張・中 ROI |
| **Low** | 17 (Open Interest) | Bitget API verify 要・Layer 2 候補 |
| **Low** | 20 (Candlestick 62 種) | 列数大 (62-372)・優先低・pandas-ta-classic 一括追加候補 |

## §E.3 CP1 監査依頼項目 (Claude `/audit` 経由)

§A-§D の各カテゴリについて:
1. **特徴量空間拡張妥当性** (約 800-1500 列追加・過学習リスク)
2. **MTF 4 方式選定** (ffill / 5m rolling / アンカー補間 / 複数特徴量分解)
3. **Fractional differentiation** (Lopez de Prado AFML Ch.5 準拠 + leak 不在)
4. **手動 Priority bool 列** (cat_v9 P1〜P25 + 共通フィルタ 50+ 閾値)
5. **業界カタログリスト** (pandas-ta-classic 212 から選定根拠)
6. **CC 同型バイアス 27+ 件再演有無** (本ファイル §9 整合)
7. **本ファイル §A-§E カテゴリ網羅性** (見落とし検出)

---

# §F 出典一覧 (WebSearch 42 件・2026-05-22)

## §F.1 個別指標 (12 件)

- [RSI Wikipedia](https://en.wikipedia.org/wiki/Relative_strength_index)
- [Fidelity RSI Guide](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/RSI)
- [LiteFinance RSI Guide](https://www.litefinance.org/blog/for-beginners/best-technical-indicators/rsi-relative-strength-index/)
- [MindMathMoney MACD Complete Guide](https://www.mindmathmoney.com/articles/understanding-the-macd-indicator-macd-line-signal-line-histogram-crossover-and-zero-line)
- [StockCharts MACD ChartSchool](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/macd-moving-average-convergence-divergence-oscillator)
- [StockCharts MACD-Histogram](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/macd-histogram)
- [Fidelity ADX](https://www.fidelity.com/viewpoints/active-investor/average-directional-index-ADX)
- [StockCharts ADX](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx)
- [VolatilityBox ATR Guide](https://volatilitybox.com/research/atr-average-true-range/)
- [StockCharts Chandelier Exit](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/chandelier-exit)
- [QuantVPS Bollinger Bands](https://www.quantvps.com/blog/bollinger-bands-explained)
- [StockCharts Bollinger BandWidth](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth)
- [StockCharts Bollinger Squeeze](https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/bollinger-band-squeeze)
- [Wikipedia Stochastic Oscillator](https://en.wikipedia.org/wiki/Stochastic_oscillator)
- [KuCoin KDJ Guide](https://www.kucoin.com/blog/en-what-is-the-kdj-stochastic-indicator-and-how-do-traders-use-it-in-real-trading)
- [Technical Analysis Pro Ichimoku 2026](https://www.technical-analysis-pro.com/indicators-ichimoku-cloud/)
- [RoboForex Ichimoku Guide](https://blog.roboforex.com/blog/2019/07/03/how-to-use-ichimoku-kinko-hyo/)
- [CME Fibonacci Retracement Extensions](https://www.cmegroup.com/education/courses/technical-analysis/fibonacci-retracements-and-extensions)
- [MindMathMoney Fibonacci Settings](https://www.mindmathmoney.com/articles/fibonacci-tradingview-settings-the-golden-zone)
- [TradingSim Volume Profile Strategies](https://www.tradingsim.com/blog/advanced-day-trading-strategies-using-volume-profile)
- [Alpha Flow Trader Volume Profile](https://alphaflowtrader.com/volume-profile-trading-guide/)
- [BabyPips Pivot Point Types](https://www.babypips.com/learn/forex/other-pivot-point-calculation-methods)
- [TradingView RCI](https://www.tradingview.com/support/solutions/43000765570-rank-correlation-index-rci/)
- [HeyGoTrade Williams %R](https://www.heygotrade.com/en/blog/williams-r-indicator-explained/)

## §F.2 チャートパターン (6 件)

- [Technical Analysis Pro Candlestick 2026](https://www.technical-analysis-pro.com/patterns-candlestick-patterns-complete-guide/)
- [Forex Tester Chart Patterns 2026](https://forextester.com/blog/chart-patterns/)
- [Wikipedia Dow Theory](https://en.wikipedia.org/wiki/Dow_theory)
- [Elliott Wave International Fibonacci](https://www.elliottwave.com/waveopedia/fibonacci-relationships/)
- [TradingSim Harmonic Patterns](https://www.tradingsim.com/blog/harmonic-patterns-in-stock-trading)
- [TradingWyckoff Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/)

## §F.3 高度分析 (6 件)

- [XS Divergence Cheat Sheet 2026](https://www.xs.com/en/blog/divergence-cheat-sheet/)
- [Trinity Trading Divergence Guide](https://blog.trinitytrading.io/divergence-cheat-sheet/)
- [Technical Analysis Pro SMC](https://www.technical-analysis-pro.com/strategies-smart-money-concepts-smc/)
- [GitHub joshyattridge SMC](https://github.com/joshyattridge/smart-money-concepts)
- [INTLBM Market Profile TPO 2026](https://intlbm.com/2026/03/18/the-ultimate-guide-to-market-profile-indicators-mastering-tpo-and-order-flow-in-2026/)
- [TradingSim VWAP Guide 2026](https://www.tradingsim.com/blog/vwap-indicator-guide)
- [LiteFinance Order Flow Footprint 2026](https://www.litefinance.org/blog/for-beginners/trading-strategies/order-flow-trading-with-footprint-charts/)
- [Pure Financial Academy Supply Demand](https://www.purefinancialacademy.com/blog/mastering-supply-and-demand-zones-a-practical-guide-for-modern-traders)

## §F.4 暗号通貨特有 (6 件)

- [Bitget Academy Funding Rates](https://www.bitget.com/academy/12560603880561)
- [QuantJourney Funding Rates](https://quantjourney.substack.com/p/funding-rates-in-crypto-the-hidden)
- [Phemex Academy Open Interest 2026](https://phemex.com/academy/open-interest-bitcoin-trading-2026)
- [CoinGlass Open Interest BTC](https://www.coinglass.com/open-interest/BTC)
- [CoinGlass Liquidation Heatmap](https://www.coinglass.com/pro/futures/LiquidationHeatMap)
- [Zipmex Liquidation Heatmap Guide](https://zipmex.com/blog/what-is-a-liquidation-heatmap/)
- [Bitcoin Magazine Pro Active Addresses](https://www.bitcoinmagazinepro.com/charts/bitcoin-active-addresses/)
- [Bitcoin Magazine Pro NUPL](https://www.bitcoinmagazinepro.com/charts/relative-unrealized-profit--loss/)
- [Bitcoin Magazine Pro MVRV Z-Score](https://www.bitcoinmagazinepro.com/charts/mvrv-zscore/)
- [Bitcoin Magazine Pro SOPR](https://www.bitcoinmagazinepro.com/charts/sopr-spent-output-profit-ratio/)
- [Glassnode SOPR Docs](https://docs.glassnode.com/guides-and-tutorials/metric-guides/sopr/sopr-spent-output-profit-ratio)

## §F.5 サイクル/ETF (6 件)

- [BitPay 2024 Halving Trends](https://www.bitpay.com/blog/analyzing-past-btc-halvings)
- [eToro Bitcoin 4-Year Cycle](https://www.etoro.com/crypto/bitcoin-four-year-cycle/)
- [Bitbo Stock to Flow](https://charts.bitbo.io/stock-to-flow/)
- [Bitcoin Magazine Pro S2F](https://www.bitcoinmagazinepro.com/charts/stock-to-flow-model/)
- [Bitcoin Magazine Pro Pi Cycle](https://www.bitcoinmagazinepro.com/charts/pi-cycle-top-indicator/)
- [CycleTop About](https://www.cycletop.co/about/pi-cycle-top)
- [TradingKey BlackRock IBIT 2026](https://www.tradingkey.com/analysis/cryptocurrencies/btc/261581598-bitcoin-btc-etf-proshares-wells-fargo-approval-odds-blackrock-ibit-gbtc-tradingkey)
- [Altrady Crypto Whale Tracker](https://www.altrady.com/blog/cryptocurrency/track-crypto-whales-smart-money)
- [CryptoQuant Exchange Netflow](https://cryptoquant.com/asset/btc/chart/exchange-flows/exchange-netflow-total)

## §F.6 ML 特化 (6 件)

- [Amazon AFML Lopez de Prado](https://www.amazon.com/Advances-Financial-Machine-Learning-Marcos/dp/1119482089)
- [GitHub charlesrambo AFML Code](https://github.com/charlesrambo/advances_in_financial_ML)
- [GitHub hudson-and-thames mlfinlab](https://github.com/hudson-and-thames/mlfinlab)
- [GitHub stefan-jansen ML for Trading](https://github.com/stefan-jansen/machine-learning-for-trading)
- [Quantreo Triple Barrier](https://www.newsletter.quantreo.com/p/the-triple-barrier-labeling-of-marco)
- [Wikipedia Meta-Labeling](https://en.wikipedia.org/wiki/Meta-Labeling)
- [Hudson Thames Meta-Labeling](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/)
- [Wikipedia Purged Cross-Validation](https://en.wikipedia.org/wiki/Purged_cross-validation)
- [TowardsAI CPCV Method](https://towardsai.net/p/l/the-combinatorial-purged-cross-validation-method)

## §F.7 業界カタログ分類 + 5 分足 + MTF (10 件)

- [StockCharts Technical Indicators](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators)
- [Britannica Technical Indicator Types](https://www.britannica.com/money/technical-indicator-types)
- [Altrady 4 Types of Technical Indicators](https://www.altrady.com/crypto-trading/technical-analysis/types-of-technical-indicators)
- [BTCC Best RSI Setting for 5 Min Chart](https://www.btcc.com/en-US/academy/strategy-analysis/technical-analysis/best-rsi-setting-for-5-min-chart-real-trader-settings-for-faster-entries)
- [FXOpen 5 Crypto Scalping Strategies 2026](https://fxopen.com/blog/en/5-crypto-scalping-strategies/)
- [MindMathMoney Multi Timeframe Trading 2026](https://www.mindmathmoney.com/articles/multi-timeframe-analysis-trading-strategy-the-complete-guide-to-trading-multiple-timeframes)
- [MQL5 RSI Multi-Timeframe](https://www.mql5.com/en/blogs/post/767332)
- [LuxAlgo 5 Steps Multi-Timeframe](https://www.luxalgo.com/blog/5-steps-to-confirm-entries-with-multi-timeframes/)
- [pandas-ta PyPI](https://pypi.org/project/pandas-ta/)
- [TA-Lib python GitHub](https://github.com/TA-Lib/ta-lib-python)

## §F.8 Gemini 見解 (まこさん経由・2026-05-22)

- Gemini 見解 #1: パラメータ vs 閾値の本質 (§1 反映)
- Gemini 見解 #2: MTF + 複数指標組合せの理由 (§2 反映)

---

# §G 改訂履歴

| 日付 | 版 | 内容 |
|---|---|---|
| 2026-05-22 | v1 | 初版 (Gemini 見解 2 件 + WebSearch 6 件で集積・§1〜§12 全章・450 行) |
| 2026-05-22 | **v2** | **辞典レベル拡張 (WebSearch 42 件追加 = 計 48 件)・§A〜§G 追加・約 1500+ 行**: §A 個別指標 12 件詳細 (RSI/MACD/ADX/ATR/BB/Stoch/Ichimoku/Fib/VP/Pivot/RCI/Williams) / §B チャートパターン (ローソク足/HS/ダウ/エリオット/ハーモニック/Wyckoff) / §C 高度分析 (Divergence/SMC/Market Profile/VWAP/Order Flow/Supply Demand) / §D ML for Trading (Triple Barrier/Meta-Labeling/Fractional Diff/Sample Weights/CPCV/mlfinlab/Stefan Jansen) / §E Phase 0 改修統合ガイド (20 カテゴリ + 優先順位) / §F 出典 48 件 / §G 改訂履歴 |

---

# §I 閾値設計論 (2026-05-22 WebSearch 12 件深掘り・閾値専門)

## §I.0 なぜ閾値専門章が必要か

私の Phase 0 改修指示書 v2 で `BB Squeeze BW < 10%` `KDJ J > 110/-10` 等を bool ハードコードし、まこさんから「データ駆動原則違反」「インプット不足」と指摘。WebSearch 12 件で閾値の本質を体系的に調査した結果を本章に集積。

## §I.1 閾値の 4 大分類

| 分類 | 内容 | 例 | 本プロジェクト方針 |
|---|---|---|---|
| **(1) 自己実現的閾値** (Self-Fulfilling) | 数百万トレーダー同時意識 → 真の market reaction | RSI 70/30 / Stoch 80/20 / Fib 38.2/61.8% / round numbers (100/1000) | **bool 維持** (Phase 0 で実装) |
| **(2) 計算式由来閾値** (Mathematical) | 統計的根拠 (BB 2σ = 95.4% normal distribution) | BB ±2σ / Z-Score ±2 / Stoch RSV | 連続値で表現 (距離 pct で十分・bool 不要) |
| **(3) 業界経験閾値** (Empirical) | 「定番」だが理論根拠薄・regime 依存で破綻 | BB Squeeze 10% / KDJ J > 110 / ADX > 25 | **データ駆動再検討必須**・段階廃止 |
| **(4) Adaptive/データ駆動閾値** | rolling quantile / Z-score / regime-conditional | RSI rolling 90th percentile / ATR-ratio classification | **業界トレンドの推奨設計** |

## §I.2 Fixed Threshold の破綻実証

- "Fixed thresholds fail when market conditions change" (Meridian Markets)
- 高ボラ期に通常値 = 低ボラ期に extreme 値・regime 切替で機能停止
- 学術研究 (JETIR 2026): "Traditional RSI configurations (30/70 or 20/80) underperformed all scenarios"
- Midline buy < 50 戦略が伝統 RSI 70/30 より優位 (S&P 500 2010-2024)
- **BTC 暗号通貨特有**: BB Squeeze の業界定番 10% は **BTC で 2 倍緩い** (BTC 実用値 5% / consolidation 3-4%)

## §I.3 Adaptive Threshold 設計手法

### §I.3.1 Rolling Z-Score
```
Z-Score = (current - rolling_mean(N)) / rolling_std(N)
```
- ±2 = 95% 範囲外 (overbought/oversold)
- N = 50-100 bar (本プロジェクト推奨 **100-bar default** = 5m × 100 = 約 8 時間)
- 適応性: 直近 window で再計算 → regime 変化追随

### §I.3.2 Rolling Percentile
```
threshold_upper = rolling_quantile(N, 0.90)
threshold_lower = rolling_quantile(N, 0.10)
```
- 90th / 10th percentile が業界標準
- AFML Ch.5 Fractional Diff と組み合わせで non-stationary 対応

### §I.3.3 Regime-Conditional Threshold
| Regime | 判定 | 閾値設計 |
|---|---|---|
| **TRENDING** | ADX > 25 + ATR 通常 | trend-following 閾値 (例: RSI 80/20) |
| **RANGING** | ADX < 25 + ATR 圧縮 (< rolling avg) | mean-reversion 閾値 (例: RSI 70/30) |
| **VOLATILE** | ATR > 1.5× rolling avg | multiplier 拡大で誤検知防止 |

### §I.3.4 ATR-Ratio Classification
- 現 ATR / rolling 50-bar ATR
- 1.5+ = high volatility / 0.7- = low volatility
- Bollinger Band multiplier 動的調整

### §I.3.5 Kaufman Efficiency Ratio
- 期間内純価格変化 / 期間内絶対値合計
- 1 に近い = 効率的トレンド / 0 に近い = ノイズ多
- Adaptive Moving Average の基盤

## §I.4 Multi-Threshold Ensemble

### §I.4.1 Voting Strategy
- 同一指標 × 複数閾値 (例: RSI 25/30/35/40)
- Weighted Majority Algorithm (Numin 2412.03167)
- 単一閾値の脆弱性回避

### §I.4.2 Multi-Indicator Confluence (Gemini #2 整合)
- MA + RSI + MACD + BB + Volume の voting
- Trade trigger = 閾値以上の confluence
- Genetic Algorithm 最適化研究 (Springer 2025・10462-025-11419-z)

## §I.5 Deflated Sharpe Ratio (DSR・Bailey + Lopez de Prado 2014)

### §I.5.1 問題意識
- Grid search で 200 windows × 50 thresholds 試行 → 「最良」は **selection bias**
- Standard Sharpe ratio は単一試行前提
- 100 試行 → 偶然「Sharpe 2.0」が出ても真のエッジではない可能性大

### §I.5.2 DSR 補正
```
DSR = Sharpe × √(1 - skew × Sharpe + (kurtosis - 1)/4 × Sharpe²)
       / √(1 + (N - 1) × variance(SR_trials))
```
- 補正項: **selection bias under multiple testing** + **non-normality**
- N = 試行数

### §I.5.3 適用ガイド (Lopez de Prado 推奨)
- 全 grid 試行を記録
- 100+ 試行で DSR 計算必須
- 単純な Sharpe maximizing 禁止
- mlfinlab で実装済 (`mlfinlab.backtest_statistics.DSR`)

## §I.6 ML (LightGBM) での閾値処理

### §I.6.1 Decision Tree 自動分割
- 連続値から最適閾値を **網羅探索** (axis-aligned split)
- Information Gain / Gini Impurity 最小化
- 連続値があれば bool 化は **情報損失**

### §I.6.2 推奨設計: 3 層併存
| 層 | 役割 | 列名規約 |
|---|---|---|
| (a) **連続値** | LightGBM 自動最適化 (主軸) | `{indicator}_value` / `{indicator}_dist_pct` |
| (b) **Adaptive 閾値 bool** | rolling 統計ベース (regime 追随) | `{indicator}_adaptive_z2` / `_z-2` / `_p90` / `_p10` |
| (c) **自己実現的 bool** | RSI 70/30 等 (世界中意識・維持理由あり) | `{indicator}_sf_overbought_70` / `_sf_oversold_30` |

### §I.6.3 Phase 別データ駆動再検討フロー
| Phase | 評価内容 |
|---|---|
| **Phase 1** (学習) | feature_importance top20 で **3 層別効果測定** |
| **Phase 3-b** (cluster) | cluster 入力に連続値優先・bool は cluster 分布乖離検証 |
| **Phase 4-b** (Exit 設計) | cluster 別最適閾値を **DSR + walk-forward** でデータ駆動最適化 |
| **Phase 5** (Replay) | (b) Adaptive vs (c) 自己実現的 bool 寄与度判定・(c) 廃止条件成立で削除 |
| **Phase 6** (本テスト) | 廃止 bool 再評価せず (§1.6.1 メタルール) |

## §I.7 本プロジェクト適用方針 (Phase 0 改修 v3 反映)

### §I.7.1 自己実現的閾値 維持/削除判定 (2026-05-22 確定)

| 指標 | 閾値 | 自己実現性 | 判定 |
|---|---|---|---|
| **RSI 70/30** | 業界定番・教育素材で頻出 | ◯ 高 | **維持** |
| **Stochastic 80/20** | 業界定番 | ◯ 高 | **維持** |
| **Fib 38.2 / 50 / 61.8 / 78.6%** | self-fulfilling prophecy 実証 (cascade effect) | ◎ 最高 | **維持** |
| **Round numbers** ($100, $1000, $10000, $100000) | 心理閾値 | ◯ 高 | **維持** (実装候補) |
| **ADX 25** | 経験閾値・regime 依存 | △ 低 (自己実現的根拠薄) | **削除** (Adaptive のみ) |
| **BB Squeeze 10%** | 業界経験・BTC で過剰緩 | × ゼロ | **削除** (5% or adaptive 採用) |
| **KDJ J > 110 / J < -10** | 教科書値・regime 依存 | × ゼロ | **削除** (z-score adaptive のみ) |
| **MACD 0 line** | 構造的閾値 | △ 中 | **維持** (構造的境界) |

### §I.7.2 Adaptive 閾値 default 設定

- Rolling window: **100-bar** (5m × 100 = 約 8 時間)
- Z-Score threshold: **±2** (95% 範囲)
- Percentile threshold: **90th / 10th**
- Regime classification: ADX 25 + ATR ratio 1.5/0.7

### §I.7.3 Deflated Sharpe Ratio 採用範囲

- **Phase 4-b 閾値最適化時**: 必須 (cluster × K × side × 閾値 grid)
- **Phase 5 Replay 評価**: 必須 (採用判定 Sharpe)
- **Phase 6 本テスト**: 必須 (合格判定 Sharpe)
- mlfinlab 経由実装 (自前禁止)

## §I.8 出典 (WebSearch 12 件・2026-05-22)

- [Adaptive Data-Driven Thresholds (EmergentMind)](https://www.emergentmind.com/topics/adaptive-data-driven-threshold)
- [Adaptive Thresholds Why Fixed Parameters Fail (Meridian Markets)](https://meridianmarkets.substack.com/p/adaptive-threshold-methodology-percentile)
- [Adaptive RSI Oscillator Dynamic Strategy (Sword Red Medium)](https://medium.com/@redsword_23261/adaptive-rsi-oscillator-dynamic-trading-strategy-with-threshold-optimization-745e89cfcc90)
- [RSI Threshold Optimization Walk-Forward (JETIR 2026)](https://www.jetir.org/papers/JETIRGZ06024.pdf)
- [GT-Score Overfitting Reduction (arxiv 2026)](https://arxiv.org/pdf/2602.00080)
- [Bitcoin BB Bands Backtest (QuantifiedStrategies)](https://www.quantifiedstrategies.com/bitcoin-bollinger-bands-trading-strategy-performance-backtest/)
- [BB Crypto Trading 2026 (Cripton AI)](https://cripton.ai/en/guides/bollinger-bands-crypto)
- [Decision Tree Split Methods (Analytics Vidhya 2024)](https://www.analyticsvidhya.com/blog/2024/03/decision-trees-split-methods-hyperparameter-tuning/)
- [Self-Fulfilling Prophecy (PriceActionNinja)](https://priceactionninja.com/psychological-levels-round-numbers-how-they-move-price/)
- [Regime Filtered Trend Strategy (PyQuantLab)](https://pyquantlab.medium.com/regime-filtered-trend-strategy-a-market-adaptive-trend-following-system-fa933e001237)
- [Crypto Walk-Forward Optimization (arxiv 2026)](https://arxiv.org/pdf/2602.10785)
- [Z-Score Trading Strategy (QuantStock)](https://quantstock.org/strategy-guide/zscore)
- [Deflated Sharpe Ratio (Bailey + Lopez de Prado SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)
- [Multi-Threshold Ensemble Genetic Algorithm (Springer 2025)](https://link.springer.com/article/10.1007/s10462-025-11419-z)
- [Numin Weighted-Majority Ensembles (arxiv 2412.03167)](https://arxiv.org/pdf/2412.03167)

---

# §H 今後の追加調査候補

- (a) cat_v9 P1〜P25 が依拠している原典手法 (各 Priority の業界起源を特定)
- (b) BTC 暗号通貨特有指標の追加 (Reserve Risk / Puell Multiple / Hash Rate / Difficulty Ribbon)
- (c) Bitget BTCUSDT 特化の slippage / spread / market depth 知見
- (d) 高頻度トレード (HFT) ・マーケットメイキング戦略
- (e) Murphy "Technical Analysis of the Financial Markets" 章別要点
- (f) Pring "Technical Analysis Explained" 章別要点
- (g) AFML 全 21 章詳細 (Ch.1-21・現状 Ch.3/4/5/7 のみ)
- (h) DRL (Deep Reinforcement Learning) for Trading (PPO / SAC / TD3)
- (i) Transformer-based time series prediction (TFT / Informer)
- (j) Graph Neural Networks for inter-asset correlation
- (k) NLP for crypto news sentiment (Twitter / Reddit / Discord)

これらを Phase 0 改修完了後、Phase 1〜7 の節目で本ファイルに追記。

---

以上。

---

## §J 入る合図の弱点と、それを打ち消す条件（2026-08-29 移設）

**なぜここに在るか**＝2026-08-29 に `composition_rules_src.json`（読み込ませる法則30件）を整理した。
30件のうち engine_tuner が使っていたのは7件（K-1〜K-7）だけで、残り23件は使われていなかった。
23件を消すにあたり、**逐語の出典がほかのどこにも無かった6件**をここへ移した。
まこさん指摘（逐語 2026-08-29）＝「30件は、法則を適当にいろんなところからピックアップしただけっぽいと思ってたら、そのとおりだったという結末」。

**この6件が要る場面**＝M3（入口を法則で組み立てられるようにする段）。
**入る合図には、それぞれ外れる場面が在る。それを知らないと、外れを避ける条件を作れない。**

### §J.1 入る合図の弱点（5件）

| 合図の型 | どんな場面で外れるか | 一緒に確かめること | 確かめるのに使う系統 |
|---|---|---|---|
| **オシレーターのクロス** | 強いトレンド中は 0 か 100 に張り付いて機能停止する | トレンドが出ていないこと | トレンド |
| **価格が帯の端に触れる** | 帯が拡大している時は、そのまま帯に沿って動き続ける | 帯が拡大していないこと | ボラ |
| **高い水準からの反転** | 強いトレンドでは水準に張り付いたまま維持される | 実際に向きが変わったこと（傾き） | トレンド・オシレーター |
| **端を抜ける** | ダマシの抜けが多い | 出来高が増えたこと・終値で確定したこと | 出来高・構造・位置 |
| **トレンドの強さの急上昇** | 弱い場面でのクロスは失敗率が高い | トレンドの強さの下限 | トレンド |

**出典（逐語）**

- **TW-1（オシレーターのクロス）**＝technical KB §2.2 逐語『オシレーター系 (RSI/Stoch)｜トレンド時: 100/0 張り付き・機能停止』／自己学習 §2.1『強トレンド中はクロスシグナルの信頼性低・コンソリデーション中の方が信頼性高い』
- **TW-2（価格が帯の端に触れる）**＝technical KB §A.5.4 逐語『Band Walk｜Lower band に張り付き → 弱気モメンタム継続 → これは「逆張りシグナル」ではなく「順張り継続シグナル」』／§A.5.3『BandWidth 上昇＝Expansion＝ボラ拡大・トレンド形成』
- **TW-3（高い水準からの反転）**＝technical KB §A.1.3 逐語『強トレンド時: extreme 値が長期間維持される (張り付き)』／自己学習 §5.1『強気相場の BTC｜RSI 70 を週・月維持あり (= 売りシグナルとして使えない場面)』／V9 P24 実物（RSI>65 に『RSI の3本差分がマイナス』を必ず添える）
- **TW-4（端を抜ける）**＝range_scalping_kb §5 逐語『破れの判定3点: ①20期間平均を上回る出来高 ②境界を明確に超えた終値 ③複数時間軸での確認』
- **TW-5（トレンドの強さの急上昇）**＝technical KB §A.3.3 逐語『ADX < 20 でクロス = 信頼度低い (40% 失敗率増・2026 研究)』／V9 P25 実物（ADX の急上昇に『ADX が 25 以上』を必ず添える）

### §J.2 合図が本物かを確かめる条件（1件）

**合図が本物かを確かめる条件**＝その合図が本物かを確かめる。

| 項目 | 中身 |
|---|---|
| 使える系統 | ボラ・出来高・需給・構造・位置・オシレーター |
| 時間足の層 | 合図の足以上（★候補の一覧は全部の足を挙げる。合図の足が決まってから絞る＝組み立ての段で適用） |
| 本数 | 0本から2本 |

**出典（逐語）**＝FMZQuant 逐語『confirmations validate entries』／range_scalping_kb §3（『①ゾーンに到達 → ②拒否の確認 → ③エントリー』＝到達だけで入らない）

**★この1件をここへ移した理由**＝ROLE-1（入る合図）と ROLE-2（入ってはいけない場面を除く条件）の逐語は
この文書の §2.1 と §2.2 に既に在ったが、**ROLE-3 の逐語だけは、ほかのどこにも無かった**（2026-08-29 に機械で確かめた）。
