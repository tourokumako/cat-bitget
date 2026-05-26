# ML pipeline 暫定ベース案 v1 (= 議論のスタート点)

最終更新: 2026-05-26
位置付け: **暫定ベース案** (= 議論のスタート点・確定事項ではない)。本ファイルから議論を出発させて、各工程の詳細を詰めていく対象。CC が本ファイルを「確定」と扱うことを禁止 (= まこさん 2026-05-26 明示指示)。

出典: 2026-05-26 セッションでまこさんが目標達成からの逆算 (= 月 $1,900 / 30 日 / 0.04 BTC × $100,000 × TP_PCT 0.20% × 月 275 件) で組み立てたドラフト案。本セッション末でまこさん再掲。

---

## 1. 6 工程フロー (= まこさん提示そのまま・1 字 1 句一致義務)

```
[1] 特徴量計算層 (= 共通基盤)
    - 5 分足ごとに 100+ 特徴量 (= Phase 0 v3.1 既存活用)
    - regime context は特徴量に吸収 (= 独立工程化しない)
       ↓
[2] Entry ML (= 件数確保最優先)
    - LightGBM Multi-output
    - 出力: entry_score / direction (LONG/SHORT/NONE) / confidence
    - threshold 緩め (= 月 275+ 件確保) ・即死リスク (危険度>0.9) のみ reject
       ↓
[3] Position Sizing ML (= 連鎖入力)
    - 入力: 特徴量 + Entry ML 出力
    - 出力: recommended_size (= 0.005-0.05 BTC 動的)
    - 0.12 BTC 合計上限内で危険度別配分
       ↓
[4] Exit 多層 ML (= 旧 Priority 12 種類継承・連鎖入力)
    - 入力: ポジ情報 + Entry 時特徴量 + 現在特徴量 + 経過時間 + 含み損益
    - 出力 (同時 12 種類): TP_signal / SL_signal / TIME_EXIT / TIME_EXIT_DOWN / MFE_STALE / MFE_GATE / TRAIL_RATIO / PROFIT_LOCK / STOCH_REVERSE / RSI_REVERSE / TP_BB_RATIO / TP_FEE_FLOOR
    - 1 つでも閾値超えたら Exit 発動
       ↓
[5] Risk 管理 (= 固定 + ML)
    - ATR/volume/spread spike で全停止
    - 0.12 BTC 上限 enforcer
       ↓
[6] 運用監視 (= drift 検知 + alert)
```

---

## 2. 目標達成試算 (= まこさん提示そのまま)

- 月 $1,900 / 30 日 = 1 日 $63 必要
- 平均ポジサイズ 0.04 BTC × BTC $100,000 × TP_PCT 0.20% = グロス $8
- 手数料 0.014% maker × 2 = 0.028% → fee $1.1
- 1 件 NET ≒ $6.9
- 月 $1,900 / $6.9 ≒ 月 275 件 = 1 日 9 件 (= 1 時間 0.4 件)

---

## 3. 設計思想 (= 2026-05-26 セッション議論で部分的に整理)

### 3.1 全体方向性 (= 暫定)

「**多めにエントリー + Exit で利益最大化**」 (= まこさん明示・2026-05-26):
- [2] Entry ML threshold 緩め = 多めにエントリー
- [4] Exit 多層 ML 12 種類 = Exit で利益最大化
- [3] Position Sizing で危険度別配分 = 危険な Entry は小サイズで損失抑制

### 3.2 Entry / Exit の密接関係 (= まこさん明示・2026-05-26)

- Entry が「TP まで届く確率が高い状況」をピンポイント検出 → Exit シンプル 3 ロジック (TP/SL/TIME_EXIT) で成立
- Entry が雑 (= TP 確率半々) → Exit 側で複雑なロジックで救う必要
- = **Entry の品質 ↔ Exit の複雑さ** のトレードオフ・Entry/Exit はセット設計

### 3.3 マルチタスク学習との関係 (= まこさん明示・2026-05-26)

- まこさん理想: **マルチタスク学習** (= Entry / Sizing / Exit を 1 モデルで同時学習・損失関数統合)
- ただし難易度高い → **連鎖学習** で現実的な落としどころを探る
- 連鎖学習 = 各段独立モデル・前段出力を後段入力に取る (= [2] Entry ML → [3] Position Sizing ML → [4] Exit ML)

---

## 4. 議論未確定事項 (= 次セッションで詰める対象)

### 4.1 フロー全体構造の検証

- 6 工程フロー全体で月 $1,900 達成可能性 (= ML 精度依存・Phase 5 Replay まで確証なし)
- 業界整合との比較 (= KB §2.6 ケース B 中央値 5 レバー = 5.57× 達成の業界相場との照合)
- Entry/Exit/Sizing の ML 化と固定ロジックの仕分け (= 業界実装はハイブリッド推奨・WebSearch 2025 整合)
- [4] Exit を ML 化するか / 固定ロジック改善するか / 折衷するか

### 4.2 各工程の詳細

各工程の **学習対象 / 特徴量 / ラベル / 評価指標 / ML 化判断** は議論未確定。次セッションで [1] → [6] の順に 1 工程ずつ詰める。

### 4.3 Entry/Exit の品質バランス

- まこさん発想「Entry 高品質 + Exit 単純」と本フロー「Entry 緩め (件数最優先) + Exit 多層」の整合性
- KB 業界知見「Entry 単独頼り = 大幅未達 ($592/月) / Exit + 並立中心 = ギリ達成可 ($1,917/月)」との関係
- 件数 ($6.9 × 月 275 件) と単価 (P23 水準 $13.9 等) のバランス

---

## 5. 関連メモリ・参照ファイル

### 必読 (= Layer 1)

- [[feedback_cat_v9_no_modification]] — cat_v9 は ML スタートライン参照素材であり改造対象ではない
- [[feedback_baseup_before_design_discussion]] — 設計議論前 KB Read + WebSearch 必須・記憶ベース断定発言禁止
- [[feedback_priority_starting_line_only]] — 手動 Priority はスタートライン参照のみ
- [[feedback_cc_low_perspective_narrow_view]] — 視点低い・視野狭い癖矯正
- [[feedback_trade_ml_knowledge_gap]] — トレード ML 業界標準理解浅・WebSearch + 教科書引用必須

### 参照ファイル

- `priority_v9_trade_logic_analysis.md` v2 (= 旧 Priority 構造分析・Replay 365 日データ起点 4 軸)
- `industry_benchmark_knowledge_base.md` (= 業界相場・5 レバー定量根拠)
- `technical_analysis_knowledge_base.md` (= テクニカル指標辞典 + 閾値設計論)
- `cc_entry_logic_self_study.md` v6 (= 業界実装カタログ・⚠️ 7 工程フレーム前提で書かれている点に注意・引用時はフレーム部分を引きずらない)

### 破綻判定済 (= 参照のみ・新フローのベースに使わない)

- `seven_step_framework.md` (= 7 工程フレーム・破綻判定済)
- `chatgpt_seven_step_origin.md` (= ChatGPT 7 工程提案要約・破綻判定済)

---

## 6. 改訂履歴

| 日付 | 版 | 内容 |
|---|---|---|
| 2026-05-26 | v1 | 初版作成 (= 2026-05-26 セッションでまこさん提示の 6 工程ドラフトを暫定ベース案として記録・議論のスタート点) |
