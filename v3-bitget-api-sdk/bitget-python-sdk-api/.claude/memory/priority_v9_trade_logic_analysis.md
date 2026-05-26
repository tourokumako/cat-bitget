# 旧 Priority v9 トレードロジック構造分析

最終更新: 2026-05-26
位置付け: 旧 Priority (= cat_v9_decider.py + cat_params_v9.json) のトレード戦略としての構造を CC が真に理解した結果をまとめた資料。スタートライン (= ML が最低限超えるべきライン) として消化・理解する目的。

**重要な前提** (= feedback_priority_starting_line_only):
- 旧 Priority は cat-bitget で **唯一の実利資産** (= 月 $370 実績)
- これを **最低レベル** として消化・理解した上で、ML を使ってどう **目標達成 (= 月 $1,900)** に進化させるかを考える
- 「素材転用」「ハイブリッド」「経験則ベース」禁止・**構造的継承 (= 設計思想を学んで活かす) は推奨**

---

## 1. 全体構造

### 1.1 Priority 一覧 (= 9 個・LONG 4 + SHORT 5)

| # | 方向 | 名称 (戦略タイプ) | 主指標 | MAX_ADDS |
|---|---|---|---|---|
| P1 | LONG | MACD ゴールデンクロス・スキャル | MACD | 1 |
| P2 | LONG | Stoch ゴールデンクロス・標準 | Stoch | 5 |
| P3 | LONG | Stoch 強・上位 (P23 ミラー) | Stoch + BB | 1 |
| P4 | LONG | プルバック + 順張り | EMA20 + BB | 5 |
| P21 | SHORT | MACD デッドクロス・スキャル | MACD | 1 |
| P22 | SHORT | RCI クロス + BB 天井 | RCI + BB | 5 |
| P23 | SHORT | Stoch デッドクロス・標準 (P3 ミラー) | Stoch + BB | 5 |
| P24 | SHORT | RSI 高位 + Stoch 高位反転 | RSI + Stoch | 5 |
| P25 | SHORT | ADX スパイク順張り | ADX + BB | 1 |

### 1.2 判定順序 (= 排他的・先勝ち)

`check_entry_priority()` 内で以下の順番に判定し、最初に条件を満たした Priority が採用される (1 bar で 1 Priority のみ発火):

1. P3 (LONG 強)
2. P4 (LONG プルバック)
3. P2 (LONG 標準)
4. P23 (SHORT 強)
5. P22 (SHORT RCI)
6. P24 (SHORT RSI 高)
7. P1 (LONG スキャル)
8. P21 (SHORT スキャル)
9. P25 (SHORT ADX スパイク)

= **強シグナル → 標準シグナル → スキャルシグナル** の優先順位

### 1.3 使用指標 (= 10 種類・cc_role §1.7 スタートライン整合)

| カテゴリ | 指標 | 役割 |
|---|---|---|
| トレンド強度 | ADX (14) | トレンドの強さ |
| ボラティリティ | ATR (14) | 値動きの幅 |
| 価格位置 (バンド) | Bollinger Band (中央/幅/スロープ/2σ) | 価格の偏り |
| トレンド (移動平均) | EMA20 | 短期トレンド |
| モメンタム転換 | MACD + Signal | 方向性転換 |
| 順位相関 | RCI (7/9/52) | 価格の規則性 |
| 過熱度 | RSI (短期・スロープ) | 売られ・買われすぎ |
| モメンタム | Stochastic (K/D) | 短期勢い |
| 相対位置 | location_prev (= 過去 20 足内の位置) | 高値圏 / 安値圏 |
| リスク評価 | entry_risk_score (= 20 足ボラ / close) | ボラ過剰検出 |

### 1.4 共通事前フィルタ (= preprocess L131-153)

LONG 系の全 Priority が以下の AND フィルタを通過してから判定:

- `filter_location_passed_long`: location_prev <= 0.9 (= 価格が直近 20 足の高値圏 90% 以下)
- `filter_riskscore_passed_long`: entry_risk_score <= 0.3398 (= ボラ過剰でない)
- `filter_riskscore_lower_passed_long`: entry_risk_score >= 0.0007 (= ボラ少なすぎない)
- `entry_ok_long` = 上記 3 つの AND

設計意図: **「高値圏での買い」「異常ボラ時の取引」を事前に排除** して、安全な Entry のみ判定対象に。

---

## 2. 各 Priority の詳細構造

### 2.1 P1 (LONG・MACD ゴールデンクロス・スキャル)

**狙う市場**: ボラ適度 (ATR 60-150) でトレンド転換期・適度なトレンド強度 (ADX 22+)

**Entry 条件** (= AND・cat_v9_decider.py L538-551):
1. MACD 前足 ≤ Signal 前足 (= 前足はデッドクロス状態)
2. MACD 現足 > Signal 現足 (= 現足でゴールデンクロス転換)
3. ADX >= 22.0
4. ATR 60-150 USD (= 適度なボラレンジ)

**Exit ロジック**:
- TP_PCT 0.5%
- TIME_EXIT 480 分 (= 8 時間)
- MFE_STALE_GATE 0.5 USD / HOLD 90 分 (= 含み益が少額で 90 分動かなければ Exit)
- POSITION_SIZE 0.06 BTC
- MAX_ADDS=1 (= スキャル・単発)

**設計意図**:
- MACD クロスで **トレンド転換の起点** を捉える短期スキャル
- ATR レンジ制限で「ボラ少なすぎ」「ボラ大きすぎ」を回避 → 確実に小さく利確
- MAX_ADDS=1 でナンピンせず・転換失敗時は損切り or 時間切れ

---

### 2.2 P2 (LONG・Stoch ゴールデンクロス・標準)

**狙う市場**: 中程度ボラ・進行中のトレンドの **小休止後の再加速**

**Entry 条件** (= L443-464):
1. Stoch_K < Stoch_D が 2 足前・1 足前で **連続** (= 売られ過ぎ局面の維持)
2. 現足で Stoch_K > Stoch_D に転換 (= ゴールデンクロス)
3. (Stoch_K - Stoch_D) > 0.3 (= 明確なクロス・ノイズ排除)
4. 現足陽線 (close >= open)
5. ADX 30-50 (= 強トレンド・ただし過熱でない)
6. ADX が 40-50 を除外 (= ADX 過熱回避・反転リスク回避)
7. RSI >= 45 (= 売られすぎ回避・反転失敗回避)
8. ATR 100-300 (= 中程度ボラ・利確届く範囲)

**Exit ロジック**:
- TP_PCT 0.6%
- SL_PCT 5% (= 大きめ・ナンピン前提)
- TIME_EXIT 480 分
- MFE_STALE_GATE 3.0 USD / HOLD 90 分
- MAX_ADDS=5 (= 平均建値型・ナンピン許容)

**設計意図**:
- 進行中のトレンドの **押し目** で Stoch 売られすぎ → 再加速を Entry
- 二重フィルタ (= ADX 過熱回避 + RSI 売られすぎ回避) で「反転失敗」を防ぐ
- MAX_ADDS=5 でナンピン → 平均建値で利確届く

---

### 2.3 P3 (LONG・Stoch 強・上位)

**狙う市場**: 高ボラ・明確な上昇トレンドでの再加速 Entry

**Entry 条件** (= L334-348):
1. Stoch クロス (2 足デッド連続 → 現足ゴールデン)
2. (Stoch_K - Stoch_D) > 0.3
3. 陽線
4. BB_MID_SLOPE > 10.0 (= BB 中央線が明確に上昇)
5. ADX 30-50
6. ATR >= 250 (= 高ボラ)

**Exit ロジック**:
- TP_PCT 0.8% (= P2 より大きい)
- SL_PCT 1.5%
- TIME_EXIT 480 分
- MFE_STALE_GATE 4.0 USD / HOLD 90 分
- POSITION_SIZE 0.024 BTC
- MAX_ADDS=1 (= スキャル単発)

**設計意図**:
- P2 を **強化した上位版** (BB ミドル明確上昇 + 高 ATR)
- 高ボラ環境では TP も大きく取れる (= 0.8%)
- MAX_ADDS=1 でナンピンせず・確度高い Entry に絞る

---

### 2.4 P4 (LONG・プルバック + 順張り)

**狙う市場**: 強い上昇トレンド + プルバック (= 押し目) 発生 + 過熱していない局面

**Entry 条件** (= L351-438):
1. 過去 10 足以内に `low` が EMA20 or BB_MIDDLE まで到達 (= プルバック発生)
2. 現足 close >= EMA20 (= 戻し)
3. BB_MID_SLOPE >= 20.0 (= BB ミドル明確上昇)
4. BB_MID_SLOPE 直近 5 足平均 >= 15.0 (= 継続的上昇)
5. 陽線
6. entry_ok_long (= 共通事前フィルタ通過)
7. RSI <= 60 (= 過熱回避)
8. ATR >= 200 (= 高ボラ)
9. ADX が 20-25 を除外 (= 弱トレンド除外)

**Exit ロジック**:
- TP_PCT 0.5%
- 多数の補助パラメータ (P4_BB_MID_SLOPE_MIN, P4_PULLBACK_LOOKBACK 等)
- MAX_ADDS=5

**設計意図**:
- **典型的な順張り押し目買い**: トレンド継続中の押し目で Entry
- 二重トレンド確認 (= BB ミドル上昇 + 5 足平均も上昇) で「一時的な上昇」と「継続的なトレンド」を区別
- RSI 過熱フィルタで「天井買い」を回避
- ADX 弱トレンド除外で「方向感のない相場」を回避

---

### 2.5 P21 (SHORT・MACD デッドクロス・スキャル・P1 ミラー)

**狙う市場**: 下落転換初動・適度なボラ

**Entry 条件** (= L556-569):
- MACD デッドクロス (= P1 ミラー)
- ADX >= 22
- ATR >= 150

**Exit ロジック** (= P1 より複雑):
- TP_BB_RATIO 1.0 (= BB 拡張に比例した TP)
- TP_MIN_PCT 0.0003 (= 最低 TP 保証)
- MFE_GATE_PCT 0.04 (= 含み益 4% 超えで管理開始)
- TRAIL_RATIO 0.9 (= トレーリング 90% 維持)
- SL_PCT 2%
- TIME_EXIT 180 分 (= P1 より短い)
- MFE_STALE_GATE 4.0 USD
- MAX_ADDS=1

**設計意図**:
- P1 のミラーだが Exit ロジックが **大幅に複雑化** (= BB 拡張比例 TP + Trailing 90%)
- 理由: SHORT 特有の **高速反転リスク** を意識・Trailing で利益を確実に確保
- TIME_EXIT が短い (180 分 vs P1 の 480 分) = SHORT は時間経過で不利になりやすい

---

### 2.6 P22 (SHORT・RCI クロス + BB 天井)

**狙う市場**: 上昇トレンドの **過熱・天井圏** での反転 SHORT

**Entry 条件 2 系統** (= L487-510・どちらかで発火):
- 通常系統:
  - RCI クロス (RCI7 が RCI9 を下抜け = デッドクロス)
  - BB 上限タッチ (= 直近 2 足で high が BB 上限到達)
  - BB ミドル下向き or 横ばい
  - RCI52 ホット (> 55 = 中期過熱)
  - ADX >= 22
  - BB_MID_SLOPE_MAX < -20 (= ミドル明確下落)
- RELAX 系統:
  - RCI クロス + ADX 緩和条件 (= 強い反転シグナル時は条件緩める)

**Exit ロジック** (= 最も複雑):
- TP_PCT 0.5%
- MFE_EXIT_PROFIT_USD 15 (= 含み益 $15 超えで利確開始)
- MFE_MAX_GATE_USD 20 (= 含み益 $20 を上限の目安)
- MFE_STALE_GATE_USD 12 (= 含み益 $12 で動かなければ Exit)
- PROFIT_LOCK 機構 (= 利益ロック・USD ベース)
- MAX_ADDS=5

**設計意図**:
- 上昇局面の **天井圏で SHORT** を狙う
- RCI のオーバーバウト + BB 上限タッチで **反転を予測**
- 2 系統 (= 通常 + RELAX) で「強シグナルなら緩い条件・標準シグナルなら厳しい条件」と二段構え
- 複雑な Exit (= PROFIT_LOCK + MFE_STALE) で「天井予測が当たった瞬間に確実に利確」

---

### 2.7 P23 (SHORT・Stoch デッドクロス・標準・P3 ミラー)

**狙う市場**: 下落トレンド + 高ボラ + Stoch 売りシグナル

**Entry 条件** (= L469-484・P3 のミラー):
1. Stoch クロス (デッド)
2. Stoch_K <= 上限 (= 999.0・実質無制限)
3. (Stoch_D - Stoch_K) > 0.3 (= 明確なクロス)
4. 陰線
5. BB_MID_SLOPE < -10 (= 下落)
6. ADX 30-50
7. ATR >= 150
8. 高 ADX 時の追加条件: ADX > 40 → ATR >= 200 (= 過熱トレンドではボラも必要)

**Exit ロジック**:
- TP_PCT 1.2% (= P3 の 0.8% より大きい・SHORT 特有の利確余裕)
- TIME_EXIT 480 分
- MFE_GATE 20 USD / STALE_GATE 4 USD
- STOCH_REVERSE_EXIT 有効 (= Stoch が逆クロスしたら Exit)
- MAX_ADDS=5

**設計意図**:
- P3 のミラー (= LONG 強の SHORT 版)
- 高 ADX 時の追加 ATR 条件で「ボラ枯れトレンド」を回避
- STOCH_REVERSE_EXIT で「Stoch が再びゴールデンクロスしたら速やかに Exit」

---

### 2.8 P24 (SHORT・RSI 高位 + Stoch 高位反転)

**狙う市場**: 過熱トレンドの **天井圏** での反転シグナル

**Entry 条件** (= L515-533):
1. RSI > 65 (= 買われすぎ)
2. RSI_SLOPE < 0 (= RSI が下降中)
3. BB_MID_SLOPE < 50 (= 過剰上昇していない)
4. Stoch_K > 60 (= 高位)
5. 陰線
6. ATR >= 30 (= 低ボラでも OK)

**Exit ロジック**:
- TP_PCT 0.7%
- MAX_ADDS=5

**設計意図**:
- **過熱局面での反転 SHORT** を狙う
- RSI + Stoch の **二重高位確認** + **RSI 下降開始** + **陰線** で確度高い反転シグナル
- ATR 低でも OK = 過熱の後は急変しなくても利確届く

---

### 2.9 P25 (SHORT・ADX スパイク順張り)

**狙う市場**: 下落加速期・ADX 急騰

**Entry 条件** (= L574-584):
1. ADX 現在 - ADX 3 足前 >= 5 (= ADX スパイク・トレンド急加速)
2. ADX 現在 >= 25
3. BB_MID_SLOPE < 0 (= 下落)
4. 陰線

**Exit ロジック**:
- TP_PCT 1.0%
- SL_PCT 2.0%
- TIME_EXIT 360 分
- MAX_ADDS=1

**設計意図**:
- **下落加速期** での順張り SHORT (= 反転狙いではない)
- ADX スパイクで「トレンドが急に強まった」瞬間を捉える
- MAX_ADDS=1 でナンピンせず・急加速の継続力に賭ける

---

## 3. Exit ロジック 12 種類の構成 (= cc_role §1.7 整合)

旧 Priority が組み合わせて使う Exit ロジック:

| # | ロジック | 役割 |
|---|---|---|
| 1 | TP_PCT | 固定 % 利確 |
| 2 | SL_PCT | 固定 % 損切 |
| 3 | TIME_EXIT | 時間切れ強制決済 |
| 4 | TIME_EXIT_DOWN_FACTOR | 含み損時の時間切れ短縮 |
| 5 | MFE_STALE | 最大含み益が一定時間動かなければ Exit |
| 6 | MFE_GATE | 最大含み益が一定額超えた管理 |
| 7 | TRAIL_RATIO | トレーリングストップ比率 |
| 8 | PROFIT_LOCK | 利益ロック (= USD ベース) |
| 9 | STOCH_REVERSE | Stoch 逆クロス検知 Exit |
| 10 | RSI_REVERSE | RSI 逆転検知 Exit (= FEAT_SHORT_RSI_REVERSE_EXIT) |
| 11 | TP_BB_RATIO | BB 拡張比例 TP |
| 12 | TP_FEE_FLOOR | 手数料保証 TP (= 手数料分を上乗せ) |

**動的 TP 計算** (= cat_params_v9.json L7-15):
- TP_FEE_FLOOR_ENABLE: 手数料分を TP に上乗せ
- TP_ADX_BOOST_ENABLE: ADX 高い時 TP 拡大
- TP_PCT_CLAMP_ENABLE: TP 上限制限

これら 12 ロジックを Priority ごとに組み合わせて、状況別に最適な Exit を実現している。

---

## 4. 設計思想の整理 (= トレード戦略としての本質)

### 4.1 方向別の戦略多様性
LONG 4 個 + SHORT 5 個 (= SHORT が多い・5 分足では下落の方が速くて利益確定しやすい)。

### 4.2 発火条件の組合せ深さ
各 Priority で **5-10 条件の AND**。単一指標で判定せず、複数指標の組合せで Entry の質を確保。

### 4.3 ナンピン使い分け (= 重要な設計)
- **スキャル系 (MAX_ADDS=1)**: P1 / P3 / P21 / P25 → 単発で短期利確
- **平均建値型 (MAX_ADDS=5)**: P2 / P4 / P22 / P23 / P24 → ナンピン許容で平均建値で利確届く

### 4.4 TP_PCT の段階性 (= 戦略タイプ別)
- 短期 0.5%: P1 / P4 / P22 (= スキャル + プルバック狙い)
- 中期 0.6-0.8%: P2 / P3 / P24 (= 標準的なトレンド狙い)
- 長期 1.0-1.2%: P23 / P25 (= トレンド継続狙い)

### 4.5 市場局面別の使い分け (= 暗黙の regime 判定)
| 市場局面 | 主 Priority |
|---|---|
| 強上昇トレンド + プルバック | P4 |
| 上昇トレンド + Stoch 再加速 | P2 / P3 |
| トレンド転換期 + MACD クロス | P1 / P21 |
| 上昇過熱・天井圏 | P22 / P24 |
| 下落トレンド + Stoch 再加速 | P23 |
| 下落加速期 | P25 |

### 4.6 safety_margin (= 安全マージン)
- **過熱回避**: RSI <= 60 (P4) / RSI 45+ (P2)
- **ADX 除外帯**: P2 / P4 で弱トレンド除外
- **location フィルタ**: 高値圏買い回避 (LONG 共通)
- **risk_score フィルタ**: ボラ過剰回避 (LONG 共通)

### 4.7 排他的判定 (= 1 bar で 1 Priority)
複数 Priority が同時条件を満たしても、優先順位で **先勝ち** (= 排他的)。これは「強い確度のシグナルから順に Entry」する設計。

### 4.8 LONG vs SHORT の非対称性
- LONG: 共通事前フィルタ + シンプルな Exit
- SHORT: 個別 Priority に複雑な Exit (= TRAIL_RATIO / PROFIT_LOCK / STOCH_REVERSE) → SHORT 特有の高速反転リスクを Exit で吸収

### 4.9 Priority 別 POSITION_SIZE の差別化
- P1: 0.06 BTC (= スキャル単発・大きめ)
- P3: 0.024 BTC (= 高ボラ + 強シグナル・標準)
- 他: cat_params_v9.json で個別設定

### 4.10 動的 TP 計算 (= 環境適応)
TP_FEE_FLOOR / TP_ADX_BOOST / TP_PCT_CLAMP で「手数料保証」「ADX 強い時の TP 拡大」「TP 暴走防止」を動的化。

---

## 5. ML での進化案 (= 目標達成のための再設計)

旧 Priority を最低レベルとして消化した上で、ML を使ってどう進化させて月 $1,900 達成するか:

### 5.1 動的閾値学習 (= ML 進化 #1)
旧 Priority の固定閾値 (= ADX >= 22, RSI <= 60, etc.) を ML で動的化。

例:
- 旧: P4 の RSI_MAX = 60 (固定)
- ML 化: 「上昇相場では RSI <= 70 / 横ばいでは RSI <= 50」のように **regime / 時間帯別に動的化**
- 同じ Priority でも市場状況に応じて閾値を変える

### 5.2 並列 Priority 統合 ML (= ML 進化 #2)
旧 Priority は **排他的・先勝ち**。ML で複数 Priority 同時発火を許容し、ML が「どの組合せが最も有利か」を判定。

例:
- 旧: P3 が先勝ち → P2 / P4 の条件も満たしていても無視
- ML 化: P2 + P3 + P4 同時発火 → ML が **3 つの confidence を統合** して「3 シグナル合意」と判定 → confidence 最高で Entry

### 5.3 Exit ロジック 12 種類の連鎖判定 (= ML 進化 #3)
旧 Priority は固定 if 文で 12 種類の Exit ロジック。ML で 12 出力を **同時生成** → どの組合せでも 1 つでも閾値超えたら Exit。

例:
- 旧: P1 は TP_PCT 0.5% + TIME_EXIT 480 分 + MFE_STALE のみ (3 種類)
- ML 化: P1 でも 12 種類すべてを同時判定 → 「TP_PCT 0.5% で利確 / MFE_STALE で利益確定 / Trailing で追い上げ」を **状況に応じて動的選択**

### 5.4 動的サイズ調整 (= ML 進化 #4)
旧 Priority は固定サイズ (0.024 / 0.06 BTC 等)。ML が **Entry 確信度** を出力 → サイズ調整 (0.005-0.05 BTC)。

例:
- 確信度 90% → 0.05 BTC で大きく入る
- 確信度 50% → 0.01 BTC で小さく入る (= 死ぬ Entry のリスクを抑える)
- 合計 0.12 BTC 上限内で動的配分

### 5.5 regime 接続 (= 工程 1 出力の明示的活用・ML 進化 #5)
旧 Priority は暗黙の regime 判定 (= 「上昇トレンドで P4」等)。工程 1 出力 (= 上昇/下落/レンジ) を **明示的に Entry ML の入力** にする。

例:
- regime=上昇 → P1/P2/P3/P4 系優先発火 + SHORT 系の発火 threshold 上げる
- regime=下落 → P21-P25 系優先発火 + LONG 系の threshold 上げる
- regime=レンジ → 反転系 (= P22/P24) 優先

### 5.6 多時間軸 (MTF) 統合 (= ML 進化 #6)
旧 Priority は **5 分足単独判定**。ML で 6 時間軸 (5m/15m/30m/1h/4h/1d) の指標を同時入力。

例:
- 5m Stoch クロスでも 1h trend が下なら confidence 下げる
- 5m + 15m + 30m の **3 足合意** で confidence 上げる
- MTF 整合性が ML に組み込まれる

### 5.7 連鎖学習 (= 工程 3 → 4 → 5 接続・ML 進化 #7)
- **工程 3 (Entry ML)** の confidence 出力 → **工程 4 (Position Sizing ML)** の入力
- 工程 4 のサイズ出力 → **工程 5 (Exit ML)** の入力
- 各 ML が前段の判定結果を参照 → **整合性のある判定**

例:
- Entry ML が「P22 相当の天井 SHORT・confidence 85%」を出力
- Position Sizing ML が「天井 SHORT は反転失敗リスクある → 0.02 BTC」を出力
- Exit ML が「P22 + 0.02 BTC → STOCH_REVERSE 検知で速やかに Exit」を出力

---

## 6. 目標達成 (= 月 $1,900) からの逆算 + 旧 Priority 構造活用

### 6.1 必要件数試算
- 月 $1,900 / 30 日 = 1 日 $63 必要
- 平均ポジサイズ 0.04 BTC × BTC $100,000 × TP_PCT 0.20% = グロス $8
- 手数料 0.014% maker × 2 = $1.1 → 1 件 NET $6.9
- → **月 275 件** = 1 日 9 件 必要

### 6.2 旧 Priority の Entry 件数キャパ
旧 Priority は実績で月 $370 → おそらく月 100-150 件 (= 1 件 NET $2.5-3.7)。
月 275 件達成には:
- **複数 Priority 並列発火** で件数増 (= ML 進化 #2)
- **動的閾値で発火頻度上げる** (= ML 進化 #1)
- **MTF で確度判定** で「外す Entry を減らす」(= ML 進化 #6)

### 6.3 1 件 NET 引き上げ
旧 Priority の TP_PCT 0.5-1.2% をそのまま継承 + **Exit ML の連鎖判定** (= ML 進化 #3) で「伸ばせる時は伸ばす」「STALE 検知で早期確定」の動的最適化。

### 6.4 大負け回避
**動的サイズ調整** (= ML 進化 #4) で「危険な Entry は 0.005 BTC で小さく」→ 大負け回避 + 件数確保。

---

## 7. 関連ファイル

| ファイル | 役割 |
|---|---|
| `strategies/cat_v9_decider.py` | 旧 Priority Entry 判定本体 (823 行) |
| `config/cat_params_v9.json` | パラメータ正本 (169 行) |
| `cat/indicators.py` | 指標計算 (ensure_ema20) |
| `feedback_priority_starting_line_only.md` (auto-memory) | 旧 Priority スタートライン位置付け |
| `seven_step_framework.md` | 7 工程フレーム全体構成 (= 本資料は工程 2 議論の前提) |
| `chatgpt_seven_step_origin.md` | ChatGPT 提案要約 (= 業界一般論・参考) |

---

## 8. CC の理解状態 (= まこさんレビュー対象)

本資料は CC が **トレード経験ゼロ** の状態で cat_v9_decider.py 全 823 行 + cat_params_v9.json 169 行を read して整理した内容。以下の点で **まこさんの現場知識による修正フィードバック** を必要とする可能性:

1. 各 Priority の「狙う市場」の解釈が実態と合っているか
2. Entry 条件の組合せの本質的意義 (= なぜこの組合せが利益を生むか) の解釈が正しいか
3. Exit ロジック 12 種類の組合せ意図が正しく理解されているか
4. ML 進化案が「旧 Priority の構造を活かす」方向で妥当か
5. 必要 Entry 件数 (= 月 275 件) の試算が現実的か

これらは想定する CC の理解で書いているため、まこさんの実態理解と齟齬があれば修正してください。

---

## 9. 改訂履歴

| 日付 | バージョン | 内容 |
|---|---|---|
| 2026-05-26 | v1 | 初版作成 (= cat_v9_decider.py + cat_params_v9.json 全文 read を基に CC が構造分析) |
