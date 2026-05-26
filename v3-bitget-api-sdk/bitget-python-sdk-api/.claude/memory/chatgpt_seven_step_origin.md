# 7 工程フレーム決定の根拠 (= ChatGPT 提案要約)

最終更新: 2026-05-26
位置付け: `seven_step_framework.md` (= 7 工程フレーム全体構成正本) の **決定根拠**。
出典: ChatGPT (まこさんが 2026-05-26 セッションで提示)。本ファイルはまこさん指示「要約して記録」に基づき CC が要約。

---

## 1. 中核原則 (= 最重要)

### 1.1 ML の役割

ML にやらせるのは **「未来価格予測」ではなく「期待値プラスな局面の通過」**。

- ML = **Entry フィルタ / Entry スコアリング**
- 学習対象 = 「このエントリーは TP しやすいか?」(= `P(tp_first)`)
- ラベル = TP first → 1 / SL first → 0 / TIME_EXIT → 0
- **方向予測 (= 上がるか下がるか) はやらせない**

理由: BTC は「方向」より「**TP まで届くか / 途中で逆噴射するか**」の方が重要。

### 1.2 0.12 BTC 制限下の最優先

ナンピン無限救済できない制約下では:

- ML は「勝ちを増やす」より **「死ぬ Entry を除外する」** 方向が重要
- = **巨大損失回避が最優先**

### 1.3 月 $1,900 USDT 達成の優先順位

| # | 領域 |
|---|---|
| 1 | **regime 判定** |
| 2 | **Entry フィルタ** |
| 3 | 損切り改善 |
| 4 | stale exit |
| 5 | TP 最適化 |

**Exit 改善より Entry 品質** が重要 (= 5 分 BTC は「どこで入るか」でほぼ決まる)。

---

## 2. 7 工程の構成

```
1. 市場状態判定 (regime)
   ↓
2. Entry 候補生成 (固定ルール)
   ↓
3. Entry ML (LightGBM Classifier・P(tp_first) 出力)
   ↓
4. Position sizing (risk_score で配分調整)
   ↓
5. Exit ML (3 系統: TP 系 / 損切系 / STALE 系)
   ↓
6. Risk 管理 (spread / volatility / slippage spike で新規 Entry 停止)
   ↓
7. Online 監視 (winrate / slippage / fee / spread / latency / TP 到達率)
```

### 2.1 工程別の方針

| 工程 | 方針 | 理由 |
|---|---|---|
| 1 市場状態判定 | 上昇/下降/レンジ/高ボラ/低ボラ を分類 | レンジ用戦略をトレンド相場で使うと崩壊する |
| 2 Entry 候補生成 | 固定ルール (= MACD cross / BB rebound / VWAP reclaim 等) | 完全 ML Entry は過学習・解釈不能・本番崩壊しやすい |
| 3 Entry ML | LightGBM Classifier で P(tp_first) 出力 | tabular 最強・学習速・過学習検知容易・SHAP 解析可・本番実装軽量 |
| 4 Position sizing | risk_score 出力 → 高 risk 0.01 BTC / 低 risk 0.04 BTC 等 | 危険度に応じた動的サイズ調整 |
| 5 Exit ML | TP 系 (= 伸び切り / 減速検知) / 損切系 (= 戻り不能検知) / STALE 系 (= 動かない検知) の 3 系統 | 固定 TP だけだと伸びない |
| 6 Risk 管理 | spread widening / volatility spike / slippage spike で新規 Entry 停止 | 危険局面回避 |
| 7 Online 監視 | 学習時と本番のズレ検出が最大事故防止 | BTC bot は本番とのズレが最大事故源 |

### 2.2 実運用フロー (= 工程 2-3-4 の接続)

```
[既存ロジック] Entry 候補生成 (工程 2)
   ↓
[ML] P(tp_first) を出力 (工程 3)
   ↓
EV = P(tp) × TP − (1 − P(tp)) × SL − fee − slippage
   ↓
if EV > threshold: entry
```

---

## 3. 学習特徴量カタログ (= 工程 3 Entry ML の入力)

### 3.1 絶対 NG (= バックテストトラップ)

- 未来高値 / 未来安値 / MFE / MAE / 未来 ATR / 未来 BB
- → 学習も推論も「**エントリー時点で観測可能値のみ**」を使う (= CAT ルールとも一致・false_positive_incident_policy §0-1 Prime Directive 整合)

### 3.2 推奨特徴量 5 カテゴリ

| カテゴリ | 例 | 重要度 / 備考 |
|---|---|---|
| **価格位置系** | bb_pos / price_to_vwap / ema_distance | BB 上限近いのに LONG は危険 |
| **傾き系** | bb_slope / ema_slope / macd_hist_slope | **最重要** (= BTC は「方向」より「加速 / 減速」が効く) |
| **ボラ系** | ATR / BB width / realized volatility | **必須** (= TP 0.06% スキャルはボラ不足だと届かない) |
| **過熱系** | RSI / stoch / distance from mean | 単独弱・**傾きと組合せ**で活きる |
| **マイクロ構造系** | spread / imbalance / taker ratio / volume surge | **強** (= 薄い板での逆張り回避・Bitget 本番寄り) |

---

## 4. 推奨構成 vs 危険構成

| 構成 | 評価 | 理由 |
|---|---|---|
| **固定ロジック + ML フィルタ + ML Exit + Risk 停止装置** | おすすめ | 解釈可能・本番再現性・leakage 防止 |
| 完全 End-to-End 深層学習 | **危険** | BT だけ強い / 本番崩壊 / 解釈不能 / leakage 地獄 |

---

## 5. 段階的導入 (= 提案)

- Phase 1: 「**負けトレード除外 ML**」を作る (= 工程 3 の出発点)
- Phase 2: 「**高 EV のみ通す**」に発展

---

## 6. cat-bitget 設計判断との接続

ChatGPT 提案は cat-bitget の現フロー (= seven_step_framework.md) と整合:

| ChatGPT 提案 | cat-bitget の現状 |
|---|---|
| 7 工程フレーム | `seven_step_framework.md` §1 整理表で採用 |
| 工程 2 = 固定ルール | 「固定ロジック (= テクニカル全体から構築・旧 Priority 素材化禁止)」で確定 |
| 工程 3 = LightGBM Classifier・P(tp_first) | 「ML (LightGBM Classifier・TP first 確率)」で確定 |
| 0.12 BTC 制限下「巨大損失回避が最優先」 | CLAUDE.md §⛔ 第二絶対規定 (= 合計 0.12 BTC 厳守) と整合 |
| 月 $1,900 USDT 達成の優先順位 (regime > Entry フィルタ > 損切 > stale exit > TP) | WORKFLOW + lessons_active で工程 1 (regime) → 工程 2-3 (Entry) を最優先で詰めている流れと整合 |
| 学習特徴量「現在値のみ」 | `false_positive_incident_policy.md` §0-1 Prime Directive と整合 |

---

## 7. 関連ファイル

| ファイル | 役割 |
|---|---|
| `seven_step_framework.md` | 7 工程フレーム全体構成正本 (= 本ファイルはその決定根拠) |
| `current_redesign_context.md` | 経緯サマリ (= なぜこのフレームに至ったか) |
| `cc_entry_logic_self_study.md` v6 | 業界知識カタログ (= 各工程の業界整合 verify) |
| `false_positive_incident_policy.md` §0-1 | Prime Directive (= 学習時も推論時点で取得可能な値のみ) |
| CLAUDE.md §⛔ 第二絶対規定 | 0.12 BTC 合計厳守 (= 巨大損失回避の制約) |

---

## 8. 改訂履歴

| 日付 | バージョン | 内容 |
|---|---|---|
| 2026-05-26 | v1 | 初版作成 (= ChatGPT 提案要約・まこさん 2026-05-26 セッション提示内容を CC 要約) |
