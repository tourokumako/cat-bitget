# analysis_playbook.md — PDCA 分析プレイブック（原因分析の唯一の正本）

作成: 2026-06-05
位置付け: ratchet PDCA の **Check(分析)工程を業界標準で完全化**し、毎セッション同じ手順で原因分析できるようにする唯一の正本。思いつき分析を排除し、**結果データの保管場所も本書に集約**（散らばり防止）。
出典(WebSearch 2026-06-05): ドローダウン3分類 [tradealgo](https://www.tradealgo.com/trading-guides/stocks/how-to-recover-from-a-trading-drawdown-a-step-by-step-framework) / ML診断・データスライス [FutureAGI](https://futureagi.com/glossary/ml-diagnostics/)・[error analysis](https://www.analyticsvidhya.com/blog/2021/08/a-quick-guide-to-error-analysis-for-machine-learning-classification-models/) / 成績指標 [backtest metrics](https://stoic.ai/blog/backtesting-trading-strategies/) / 実験ログ=ラボノート [W&B quant lifecycle](https://wandb.ai/site/articles/architecting-alpha-the-modern-quant-lifecycle/) / 最小regime成績MRP [arxiv 2604.08356](https://arxiv.org/pdf/2604.08356)

---

## §0 3行サマリ
- 1周ごとに **score.py で採点 → report.py で分析 → ledger に記録**。
- 負けたら **「戦略/執行/regime」のどれか必ず分類**してから直す（誤診=逆効果・§2.4）。
- 結果データは `results/priority_rebuild/ratchet/` に集約。本書 §3 がカタログ。

## §1 PDCA 工程（ツール対応）

| 段階 | 何をする | ツール / 成果物 |
|---|---|---|
| **Plan(設計)** | 変更を**1つ**、`cat_requirements §4.6 H1-H14` 照合で設計 | `ledger.md` E エントリ / `strat_v9ml_design.md` |
| **Do(実装)** | V9不変・新規ファイル・**自己検査(assert)つき** | `gen_*` / `train_*` / `strat_*` |
| **Check(採点)** | 固定審判で月次 net（地面 $172 と比較） | `score.py` |
| **Check(分析)** | 本書 §2 バッテリーを実行・原因を §2.4 で分類 | `report.py` / `*_learned_params.json` |
| **Act(判定)** | 数字が上がれば残す／原因+分類+改善を記録 | `ledger.md`（採用 or 破棄） |

原則: **1ターン1変更** / 封印期間(2026Q1)は触らない / judge(score.py・eval_engine)は改造しない。

## §2 分析バッテリー（完全版・毎周これを全部見る）

### 2.1 成績指標（report.py A）
net(審判) / 月平均 / NET日次 / 勝率 / 最大DD / 最大連敗 / 日次最悪 / **Sharpe / Sortino / Profit Factor / Recovery**。
最終合格は別途 **全月 net ≥ $1,900 + DSR>0.95 + PBO<0.5**（`cat_requirements §1.2`）。

### 2.2 スライス分析（report.py B–G, F2–F4）= 高/低成績の「塊」を探す
優先度別(B) / 出口理由別(C) / **サイズ・add別(D)** / ベスト・ワースト(E) / 月別(F) / **月別×出口・サイズ(F2/F3)** / 1日あたり(F4) / **指標帯別 ADX・ATR%・stoch・bb傾き(G)**。
→ 「どの帯・どの条件で勝ち/負けが集中するか」を特定（ML診断のデータスライス）。

### 2.3 較正（report.py H）= AI確率 × 実net の対応
高確率帯ほど net が高いか。**逆較正（一番儲かる帯にAIが低確率）は致命**（E6 で bb傾き<−30 が実証）。

### 2.4 ★ ドローダウン3分類（原因分析の幹・直す前に必ず1つに分類）

| 種別 | report での兆候 | 直し方（ここを間違えると逆効果） |
|---|---|---|
| **① 戦略欠陥** | 全 regime/月で負け・誤ラベル・逆較正(2.3)・IS≫OOS | ラベル定義・特徴量・モデル設計を直す |
| **② 執行** | gross 黒字なのに net 赤・手数料率高・slippage・発注過多 | コスト/約定モデル/発注頻度を直す |
| **③ regime依存** | 特定 regime(月)だけ負け・他月は黒（F で確認） | regime 条件付け / regime 別モデル / regime フィルタ |

出典 tradealgo: 「3種は別の対処が必要・誤診すると wrong fix」。

### 2.5 regime 頑健性（MRP）
**最悪月 = 最小 regime 成績**を robust 下限として見る（F の最小月）。最終目標は**全月** ≥ $1,900（単月判定）。「通算だけ黒字」で安心しない。

### 2.6 原因チェックリスト（ML 根因・該当を ledger に明記）
☐ 誤ラベル ☐ train/test 分布シフト ☐ leak(未来参照) ☐ **fat-tail(勝率と金額の乖離=大勝ちを切る)** ☐ 逆較正 ☐ 過学習(IS≫OOS・best_iter 過大)

### 2.7 学習の中身（train_* の出力）
重要特徴 top / 学習した分岐閾値 / AIが高評価する値域 / **使用した値一覧 JSON（cat_params風・`p23_ml_learned_params.json`）** で V9手書きと対比。

## §3 結果データ 保管場所カタログ（散らばり防止・ここを見れば全部ある）

| 種別 | パス | 中身 |
|---|---|---|
| PDCA 記録（正本） | `.claude/ratchet/ledger.md` | 各 E：変更/結果/原因(3分類)/改善/採用 or 破棄 |
| 設計（正本） | `.claude/ratchet/strat_v9ml_design.md` | 現方針 |
| **分析手法（正本=本書）** | `.claude/ratchet/analysis_playbook.md` | 分析バッテリー・PDCA・保管場所 |
| セッション経緯 | `.claude/ratchet/session_log_YYYYMMDD.md` | その日の学び |
| 候補・トレード記録 | `results/priority_rebuild/ratchet/*.csv` | 候補/AI選択/full/scored（score.py・report.py の入力） |
| 学習した値一覧 | `results/priority_rebuild/ratchet/p23_ml_learned_params.json` | AI が使用/学習した値 |
| 審判（固定） | `scripts/priority_rebuild/score.py` | 売買記録→月次 net |
| 分析ツール | `scripts/priority_rebuild/report.py` | A–I/F2–F4 一括 |
| **結果一覧（書類・人が確認）** | `results/priority_rebuild/ratchet/report_<名前>.txt` | report.py が実行ごとに保存する結果全文（A–I）。まこさんが開いて確認するのはこれ |
| 実装（候補生成/学習） | `scripts/priority_rebuild/gen_p23_candidates.py` / `train_p23_entry.py` | V9不変・自己検査つき |

## §4 毎セッション実行チェックリスト（この順で回す）

```
1. 新しい売買記録 CSV を score.py で採点（月次 net・地面 $172 と比較）
   python3 scripts/priority_rebuild/score.py <trades.csv> --start 2025-04-01 --end 2025-12-31
2. report.py を通す（比較対象があれば --vs）→ §2.1–2.3,2.5 が一括で出る
   python3 scripts/priority_rebuild/report.py <trades.csv> --start ... --end ... [--vs <baseline.csv>]
3. §2.4 で勝ち/負けの原因を「戦略/執行/regime」に1つ分類 + §2.6 チェックリスト
4. ledger.md に「結果 + 原因(分類) + 改善1つ」を記録 → 次周 Plan へ
```

report.py 1コマンドで §2.1–2.3・2.5 が出る。**§2.4 の3分類と §2.6 チェックは CC が判断して ledger に明記**（report は材料、分類は人/CC の判断）。

## §5 関連
- `cat_requirements.md §4.6`（ハード制約 H1-H14・Plan で照合）/ §8.4（PDCA フロー・本書を参照）
- `ledger.md`（記録）/ `strat_v9ml_design.md`（設計）
- 出典 URL は本書冒頭。
