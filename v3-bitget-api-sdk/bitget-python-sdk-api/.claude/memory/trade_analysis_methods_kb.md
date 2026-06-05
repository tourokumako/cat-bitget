# trade_analysis_methods_kb.md — トレード結果データ分析方法 ナレッジベース

作成: 2026-06-05 (CC・まこさん指示「トレード結果のデータ分析方法を WebSearch してナレッジ化」)
位置付け: **トレード結果（売買記録 CSV）を正しく読み解く方法の知識正本**。`analysis_playbook.md` が「PDCA のどの工程で何を実行するか（手順）」なら、本書は「各分析が何を意味し・なぜやり・基準値はいくつか（知識）」を担当する。
出典: WebSearch 2026-06-05（下記各節）+ technical/industry KB + AFML。
状態: 運用しながら追記。

> ⚠️ **作成の経緯（恥・固定）**: 2026-06-05 E8a-2 で「前回レポートと比較せず」「トレード数激減を見落とし」「θ単独いじり」と、データ分析の基本を欠いてまこさんに叱責された（「データ分析ってわかる？」）。本書はその再発防止。**分析を思いつきでやらず、毎回本書の型でやる**。

---

## §0 大原則（毎回・最初に確認）

1. **変更の効果は必ず「前回 vs 今回」で測る**（単体で「AI負け」と言わない）。最低でも **件数・net・avg・勝率** を前後で並べる。トレード数が激減/急増していたら、それ自体が最大の発見。
2. **1変更ずつ**（multi-adjustment 同時変更禁止）。複数同時に変えると、どれが効いたか attribution 不能（[traderssecondbrain](https://traderssecondbrain.com/guides/mae-mfe-analysis)）。
3. **gross と net を分ける**。net がマイナスでも「手数料負け」か「方向外し」かは別物（CLAUDE.md §TP_PCT・L-40）。
4. **件数と1件あたりを両方見る**。総net = 件数 × avg。片方だけ見ると誤診（fat-tail 戦略は件数を削ると総net激減）。

---

## §1 成績指標（report.py A）

| 指標 | 意味 | 見方 |
|---|---|---|
| net（審判） | 全コスト控除後の純益 | 唯一の合格判定軸（月次 ≥ $1,900 全月） |
| expectancy（期待値） | **勝率 × 平均利益 − 敗率 × 平均損失** | 1トレードの平均稼ぎ。プラスが大前提（trade_methods §6） |
| R-multiple | 利益 ÷ 初期リスク(SL幅) | リスク単位で揃えて比較（[forexmechanics](https://forexmechanics.com/traders-workshop/journal-metrics/)） |
| Sharpe / Sortino | リスク調整後リターン | fat-tail 戦略は純net最適化が過剰適合→Sharpe/Sortinoで補正 |
| Profit Factor | 総利益 ÷ 総損失 | >1.0 が黒字。1.3-2.0 が実用域 |
| Recovery Factor | net ÷ 最大DD | DD に対する稼ぎの効率 |
| 最大DD / 最大連敗 | 下振れの深さ | 月次 net の10%未満なら逆に異常値STOP（過剰適合疑い・false_positive 関所A） |

---

## §2 トレード分布分析（少数大勝ち依存かを暴く）

- **P/L ヒストグラム**: 利益が「少数の大勝ち」に偏るか「コンスタント」かを見る（[adventuresofgreg](https://adventuresofgreg.com/blog/2025/12/20/complete-guide-strategy-backtesting-traders/)）。
- cat-bitget の P23 は **fat-tail（少数大勝ち）型**＝確定事実。だから：
  - **勝率を上げる/件数を削る系の改善は大勝ちを切って逆効果**（E4/E6/E8a-2 で実証）。
  - net を見るときは「上位数件を除くと残るか」も確認（1発依存の脆さ）。

---

## §3 MAE / MFE 分析（出口較正の中核・report.py I）

- **MAE（最大逆行）**＝決済までに到達した最大含み損 / **MFE（最大含み益）**＝到達した最大含み益（[tradewink](https://www.tradewink.com/learn/understanding-mfe-mae-day-trading)）。
- **較正の業界基準値**（[traderssecondbrain](https://traderssecondbrain.com/guides/mae-mfe-analysis) / [journalplus](https://journalplus.co/learn/guides/mae-mfe-guide/)）:
  - **勝ちトレードの MAE 80th percentile = SL（損切り）較正の基準**（勝ち玉がそこまで逆行に耐えた幅）。
  - **MFE 中央値の 60-70% = TP（利確）較正の基準**（多くのトレードを綺麗に捕まえる）。
  - MAE/MFE 最適化で **expectancy +20-30%** が業界相場。
- ⚠️ **ラベルとの関係（重要・§14.1 AFML）**: **MFE ピークは「バックテスト固有」で実トレードでは取れない**。ラベルを MFE ピークで作ると「実際の出口で取れない益」を教師にする＝実 net と乖離する。**ラベルは Triple Barrier（TP/SL/time の実出口でどれが先か）で作るのが業界標準**（実トレードをミラー）。MFE/MAE は出口較正の診断材料に使い、ラベルそのものには実出口を使う。
- **再測定**: 出口を変えたら 30-60 日後に MAE/MFE 分布を測り直し、比率改善と net 影響の両方を見る（1変数ずつ）。

---

## §4 スライス分析（高/低成績の塊を探す・report.py B-G）

「どの条件で勝ち/負けが集中するか」を切り分ける（ML診断の error analysis）:
- **月別 / 年別**（季節性・継続的不調の検出・[adventuresofgreg](https://adventuresofgreg.com/blog/2025/12/20/complete-guide-strategy-backtesting-traders/)）
- **regime 別**（下げ/レンジ/上げ・最弱 regime が robust 下限＝MRP）
- **出口理由別**（TP/SL/時間切れ/失速/反転：どこで稼ぎどこで死ぬか）
- **サイズ・add 別**（単発 vs 買い増し育ち）
- **指標帯別**（ADX/ATR%/stoch/bb傾き帯ごとの net＝V9 手書き閾値が最適かを問う）

---

## §5 較正（予測確率 × 実 net・report.py H）

- AI の「自信度（予測確率）」が高い帯ほど実 net が高いか。
- **逆較正（一番儲かる帯に AI が低確率）は致命**（E6 で bb傾き≤−30 が実証）。確率順サイジングが逆効果になる。
- 確率を sizing に使う前に、必ず較正を確認する。歪んでいれば確率の意味づけ（scale_pos_weight 等）を疑う。

---

## §6 ロバスト性検証（本物の edge か・過剰適合でないか）

| 手法 | 何を見る | 出典 |
|---|---|---|
| **前後比較**（§0） | 変更の効果（件数・net・avg・勝率） | 本書最重要 |
| **ブートストラップ信頼区間** | トレードから復元抽出して mean R の区間。**0 をまたぐなら統計的に黒字と言えない** | [traderssecondbrain](https://traderssecondbrain.com/guides/mae-mfe-analysis) |
| **Monte Carlo（順序シャッフル）** | トレード順を入れ替え1000通り。特定の並び依存でなく真の edge か | [adventuresofgreg](https://adventuresofgreg.com/blog/2025/12/20/complete-guide-strategy-backtesting-traders/) |
| **確率コーン（5th/95th equity band）** | 実績がコーン外＝不調 or 想定外ストレス | 同上 |
| **Walk-Forward / Purged K-Fold** | 時系列の OOS 検証・leak 防止 | AFML Ch.7・cc_entry §17 |
| **DSR / PBO** | backtest 過大評価の補正（IS→OOS degradation 30-70%） | AFML Ch.14・industry §3.2 |
| **較正70%/検証30%** | 閾値はテストでなく検証データで決める | [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12571449/) |

---

## §7 原因3分類（直す前に必ず1つに分類・analysis_playbook §2.4 と同一）

| 種別 | 兆候 | 直し方（誤診=逆効果） |
|---|---|---|
| ① 戦略欠陥 | 全 regime/月で負け・誤ラベル・逆較正・IS≫OOS | ラベル定義・特徴量・モデル設計 |
| ② 執行 | gross 黒字なのに net 赤・手数料/slippage・発注過多 | コスト/約定/発注頻度 |
| ③ regime依存 | 特定 regime(月)だけ負け | regime 条件付け/別モデル/フィルタ |

---

## §8 分析の最低手順（毎実験・これを飛ばしたら L-250 違反）

```
1. score.py で採点（月次 net・地面と比較）
2. report.py を --vs 前回ベースライン で通す（§0 前後比較・件数とnet両方）
3. §2-5 で「どの塊で勝ち/負けが集中するか」「較正は正常か」を読む
4. §7 で原因を3分類に1つ + §6 でロバスト性（過剰適合でないか）
5. ledger.md に「結果（前後比較込み）+ 原因(分類) + 改善1つ」を記録
```

物理強制: score.py 採点後 report.py + ledger 未済ならターン終了不可（`pdca_gate.sh`・L-250）。

---

## §9 出典 URL

- https://adventuresofgreg.com/blog/2025/12/20/complete-guide-strategy-backtesting-traders/
- https://www.researchgate.net/publication/399129762
- https://arxiv.org/pdf/2309.09094
- https://traderssecondbrain.com/guides/mae-mfe-analysis
- https://forexmechanics.com/traders-workshop/journal-metrics/
- https://www.tradewink.com/learn/understanding-mfe-mae-day-trading
- https://journalplus.co/learn/guides/mae-mfe-guide/
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12571449/
