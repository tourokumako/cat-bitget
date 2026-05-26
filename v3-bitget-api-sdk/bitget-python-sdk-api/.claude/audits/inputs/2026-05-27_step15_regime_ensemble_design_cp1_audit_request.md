# 【監査依頼】工程 [1.5] regime ensemble 詳細設計 (= ml_pipeline_baseline v2.7 §6.1.1-6.1.6) CP1 監査

---

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 N 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて結果ファイル `.claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md` を Write
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / NO-GO / PIVOT / OTHER)
   - 最優先指摘 (Critical) 件数

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)

---

## 監査依頼メタ情報

- 依頼日: 2026-05-27
- 依頼者: CC (起案者・メインセッション)
- 監査区分: CP1 (= 工程 [1.5] 詳細設計 第 1 回監査・実装着手前)
- 監査対象タスク: 工程 [1.5] regime ensemble 詳細設計 (= 評価方法 / HMM 再調整 / 固定ルール / k-means / ensemble 機構 / 出力仕様)
- 結果ファイル保存先: `.claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md`
- 入力ファイル保存先 (本依頼書): `.claude/audits/inputs/2026-05-27_step15_regime_ensemble_design_cp1_audit_request.md`

---

## 監査依頼の経緯

1. 2026-05-27 セッションで CC が ml_pipeline_baseline v2 §1 [1.5] 元決着 (= HMM + 固定ルール + k-means の ensemble) の詳細設計を 6 項目に分けて決着 (= §6.1.1-6.1.6 として追記)
2. 本セッション中 CC は L-232 改善 1 (= 雑な言い切り癖) を 9 回 + 改善 2 (= 文章わかりづらい) を 10 回違反・WebSearch 事後対応 (= 固定ルール提案で全部 AND を出して指摘されてから scoring 構造に修正)
3. まこさん「自分でわからない部分が多い・信じて任せて大丈夫か」と懸念表明 → CC が監査経路提案
4. 本監査で第三者 (Plan agent) 視点で詳細設計の業界整合性 + cat-bitget 制約整合性 + 内部一貫性を verify

---

## 着手前必読 (省略禁止・auditor 用・10 件)

1. `bitget-python-sdk-api/.claude/memory/ml_pipeline_baseline_v1.md` §6.1.1-6.1.6 — **監査対象本体** (= 評価方法 4 段階 + HMM 再調整方針 + 固定ルール scoring + k-means 4 特徴量 + ensemble soft voting + 出力 6 列仕様)
2. `bitget-python-sdk-api/.claude/memory/ml_pipeline_baseline_v1.md` §1 [1.5] — 元決着事項 (= HMM + 固定ルール + k-means ensemble・フィルタとして強制適用しない)
3. `bitget-python-sdk-api/.claude/memory/ml_pipeline_baseline_v1.md` §3.4 — 単一手法限界を ensemble で補強する設計思想根拠
4. `bitget-python-sdk-api/.claude/memory/ml_pipeline_baseline_v1.md` §2.2 — 5 レバー寄与見積 (= [1.5] regime 担当 1.3×)
5. `bitget-python-sdk-api/.claude/memory/step1_regime_design.md` — HMM 詳細仕様 v2.2 (= 14 指標 × 6 TF = 84 次元入力・covariance_type=diag・1h 判定 + 連続 2 回ヒステリシス)
6. `bitget-python-sdk-api/results/regime_step1/hmm_summary_train_2021_2024.json` — v15 HMM 実 学習結果 (= 5 fold Walk-Forward + log_likelihood + state_switches + dwell_time)
7. `bitget-python-sdk-api/.claude/memory/industry_benchmark_knowledge_base.md` §2.4 — regime filter 業界実証 1.1-1.6× (= 200日MA / HMM / Jump model / LuxAlgo)
8. `bitget-python-sdk-api/.claude/memory/technical_analysis_knowledge_base.md` §A.3-A.5 — ADX / ATR / BB の業界 standard 閾値 + cat_v9 経験値
9. `bitget-python-sdk-api/.claude/memory/lessons_active.md` L-230 / L-231 / L-232 — 本セッション関連の構造的失敗パターン
10. `~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_cat_v9_no_modification.md` + `feedback_priority_starting_line_only.md` — cat_v9 改造禁止 + スタートライン参照のみ

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = **[1.5] regime ensemble 詳細設計の業界整合性 + cat-bitget 制約整合性 + 内部一貫性** の verify。月次 NET 達成可能性判定は対象外 (= 8 工程合算後の Phase 5 Replay で判定)。実装スクリプトの監査も対象外 (= 設計段階・実装はこれから)。

---

## 監査対象の事実データ

### 詳細設計の決着事項 (= 6 サブセクション)

| サブセクション | 内容 | 主要決着 |
|---|---|---|
| §6.1.1 評価方法 | 4 段階 (Stage 1-4) | Stage 1 = 内部スコア / Stage 2 = 視認 + 統計検定 / Stage 3 = PnL 早期判定 ([4] Exit 完成後) / Stage 4 = 8 工程合算後 PnL |
| §6.1.2 HMM 再調整方針 | v15 ベースで微調整のみ | k=3 / diag / 84 次元入力 / 1h 判定 / 連続 2 回ヒステリシス 維持・改善は ensemble で取る |
| §6.1.3 固定ルール判定器 | 6 指標 × scoring + weighted vote | ADX / DI / BB ミドル傾き / 価格 vs MA / MTF 整合 (重み 1.5) / 一目均衡表・最高点採用 + 不明確閾値 3.0 + 連続 2 回ヒステリシス |
| §6.1.4 k-means 判定器 | 4 特徴量 + k=3 | log_returns_1h / rolling_volatility(20) / close_vs_sma20_pct__1h / adx14_1h・HMM と同じ学習データ/前処理/判定間隔 |
| §6.1.5 ensemble 機構 | soft voting + 重み付き平均 | 等重み初期値 (= 全部 1.0)・最高確率採用・確信度 = 最高 - 2 番目・不明確閾値 0.4 + 連続 2 回ヒステリシス |
| §6.1.6 出力仕様 | 6 列追記 + MTF forward fill | regime_label / prob_up / prob_down / prob_range / confidence / volatility_level・1h → 5m forward fill・one-hot encoded 派生列・「フィルタ強制適用しない」決着整合 |

### v15 HMM 既存学習結果 (= results/regime_step1/hmm_summary_train_2021_2024.json)

- 5 fold Walk-Forward Purged K-Fold 全 converge
- mean log_likelihood_test = -597,630
- mean avg_dwell_hours_test = 7.89
- 状態切替 670-956 回 (5 fold 別)
- sanity_check: レンジ ADX 23.59 < 上昇 ADX 31.56 < 下降 ADX 32.75 → PASS
- 各状態 DI 差中央値: 上昇 +13.9 / 下降 -15.7 / レンジ -0.94
- 状態分布: レンジ 51% / 上昇 26% / 下降 23%

---

## 監査スコープ

### 監査対象 (本監査内)

- 各サブセクション (§6.1.1-6.1.6) の **業界整合性** (= WebSearch + 教科書引用 + auditor 独立調査)
- 各サブセクションの **cat-bitget 制約整合性** (= 5 分足 / 0.12 BTC 上限 / 月 275 件想定 / cat_v9 改造禁止 / フィルタ強制適用しない決着)
- 6 サブセクション間の **内部一貫性** (= 判定間隔 / ヒステリシス / 学習データ範囲 / 不明確閾値 等の整合性)
- 3 判定器 (HMM / 固定ルール / k-means) の **役割分担** (= 補完関係になっているか・差別化されているか)
- 元決着 (= ml_pipeline_baseline v2 §1 [1.5]) からの **修正点の妥当性** (= 特に ATR の方向判定から外す変更)

### 監査対象外 (現時点で判定不可能 or 別監査スコープ)

- 月次 NET ≥ $1,900 達成可能性 → 8 工程合算後の Phase 5 Replay 判定
- 実装スクリプトの品質 → 別監査 (= 実装完成後)
- 工程 [2] Entry ML 以降の設計 → 各工程の詳細設計時に別途監査

---

## 監査観点 (一般・auditor_template ①〜⑦)

- ①統計学的妥当性 (= scoring 閾値 / 確率変換 / 確信度算出)
- ②リスク管理 (= 「フィルタ強制適用しない」決着整合・不明確時のヒステリシス挙動)
- ③認知バイアス (= 視点低い・視野狭い癖 + 振り子の極端さ + 業界フレーム逃避癖の検出・本セッションで実証済 L-232)
- ④ソフトウェア工学 (= 出力 6 列の型・MTF forward fill の look-ahead leak リスク)
- ⑤再現性 (= 学習データ範囲 train_2021_2024 統一・Walk-Forward Purged K-Fold)
- ⑥実行プロセス (= 段階的検証 Stage 1-4 の妥当性)
- ⑦主エージェントバイアス (= CC が業界 standard を引用した提案で「業界 standard だから OK」と判断根拠化していないか)

---

## 監査観点 (本監査固有・Q1-Q7)

### Q1 — 評価方法 4 段階 (§6.1.1) の業界整合性

- Stage 1 (= 内部スコア log-likelihood / BIC / silhouette score) は教師なし regime detection で業界 standard か?
- Stage 2 (= まこさん視認 + 各状態の収益性検定 + 既存特徴量との相関) は業界実証あるか?
- Stage 3 (= [4] Exit 完成後の PnL 早期判定・regime あり vs なし NET 比率) のタイミング (= [4] 後) は妥当か? 早すぎる/遅すぎるリスクは?
- Stage 4 (= 8 工程合算後 Phase 5 Replay 最終 verify) は標準的経路か?
- NET 比率合格基準 (1.3× ◎ / 1.1× ○ / 1.0× ✗) の数値根拠は妥当か?

### Q2 — HMM 再調整方針 (§6.1.2) の妥当性

- v15 HMM の sanity check PASS だが視認「精度微妙」の構造的原因 = 教師なし単一手法限界、と CC は結論。auditor 視点で妥当か?
- v15 をベースに大幅変更なし + 改善は ensemble で取る方針は業界整合か? 単独調整 (= 特徴量変更 / 状態数 k=2 or 4 / covariance_type=full 復活) の余地は本当にないか?
- 7.89h 平均切替間隔は 5 分足取引にとって遅すぎるリスクは?

### Q3 — 固定ルール判定器 (§6.1.3) の業界整合性

- 6 指標 (ADX / DI / BB ミドル傾き / 価格 vs MA / MTF 整合 重み 1.5 / 一目均衡表) の選定根拠は業界整合か?
- scoring + weighted vote 構造は CC の「全部 AND は雑」指摘後の修正だが、業界 standard と整合するか?
- 不明確閾値 3.0 (= 6 指標 × 平均 0.5 点) の数値根拠は妥当か?
- ATR を方向判定から外しボラ別フラグへの変更 (= 元決着の修正) は業界整合か?
- 数値根拠 (= ADX 25 / BB 傾き ±10 / BB width <10% / ATR 250/100) は業界 standard + cat_v9 経験値で十分裏付けられているか?

### Q4 — k-means 判定器 (§6.1.4) の業界整合性

- 4 特徴量 (log_returns_1h / rolling_volatility(20) / close_vs_sma20_pct__1h / adx14_1h) の選定は業界 standard 2-4 特徴量と整合か? もっと適切な特徴量はあるか?
- k=3 (= 上昇 / 下降 / 横ばい) は financial regime default だが、elbow method + silhouette score で k=3 が実際に最適か未 verify。事前に k=3 と決め打つリスクは?
- HMM (= 84 次元) との差別化を「シンプルさ」だけで担保するのは十分か?

### Q5 — ensemble 機構 (§6.1.5) の業界整合性

- soft voting + 重み付き平均は業界推奨だが、k-means の cluster 中心からの距離を softmax で確率変換するのは標準的手法か?
- 初期等重み (= 全部 1.0) は妥当か? 業界では Cross-validation で重み調整するのが standard・初期等重みのリスクは?
- 不明確閾値 0.4 の数値根拠は妥当か?
- ヒステリシス (= 連続 2 回切替) は HMM 単独でも提案されていたが、ensemble 全体でもこの粒度で十分か?

### Q6 — 出力仕様 (§6.1.6) の業界整合性 + look-ahead leak リスク

- 出力 6 列 (regime_label / prob_up / prob_down / prob_range / confidence / volatility_level) の構造は業界 standard か?
- MTF forward fill (= 1h 判定を 5m bar にコピー) で look-ahead leak リスクはないか? (= 1h 判定タイミングと 5m bar タイムスタンプの整合性 verify)
- one-hot encoded 派生列 + 確率値の併用は LightGBM 入力として効率的か? 冗長性のリスクは?
- 保存場所 (= results/regime_step1/ 配下) は適切か?

### Q7 — 全体一貫性 + cat-bitget 制約整合性

- 3 判定器 (HMM 84 次元 / 固定ルール 6 指標 / k-means 4 特徴量) の役割分担は明確か? 補完関係になっているか・冗長な視点はないか?
- 判定間隔 (= 1h) + ヒステリシス (= 連続 2 回) を 3 判定器すべてで統一しているが、判定器ごとに最適な粒度は違う可能性は?
- 「フィルタとして強制適用しない」決着と出力仕様 (= 入力として後段に渡す) は整合か?
- cat-bitget 制約 (= 5 分足 / 0.12 BTC 上限 / 月 275 件想定 / 1 取引 2-3 時間 / cat_v9 改造禁止) と本設計は整合か?

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

`.claude/memory/technical_analysis_knowledge_base.md` 等の内部知識に閉じない。auditor は以下の **外部検索を必ず実施** すること。ChatGPT 等の外部 AI 使用不可 (まこさん課金外)。

### 検索対象 (例・auditor 適宜拡張)

1. **regime ensemble 評価方法業界 standard 2025**:
   - クエリ案: "regime detection evaluation statistical financial metrics walk-forward 2025"
   - 期待発見: 教師なし regime 評価の業界 default
2. **HMM 単独限界 + ensemble 補強実証**:
   - クエリ案: "HMM regime detection single method limitation ensemble improvement crypto"
   - 期待発見: HMM 単独で精度天井がある実証 + ensemble での改善実証
3. **固定ルール scoring + weighted vote regime classification 2025**:
   - クエリ案: "rule-based regime classification scoring weighted vote multi-indicator crypto 2025"
   - 期待発見: 全部 AND ではない業界 standard 設計
4. **k-means 特徴量選択 BTC 5m**:
   - クエリ案: "k-means regime detection feature selection cryptocurrency 5-minute return volatility"
   - 期待発見: 4 特徴量より適切な選定があるか
5. **soft voting + 重み付き平均 financial ensemble**:
   - クエリ案: "soft voting weighted ensemble financial regime classifier initial weights cross validation"
   - 期待発見: 初期等重みのリスク + walk-forward 重み調整方法
6. **MTF forward fill look-ahead leak**:
   - クエリ案: "multi-timeframe forward fill look-ahead leak regime feature 1h to 5m"
   - 期待発見: forward fill の look-ahead リスクと対策
7. **一目均衡表 regime detection 業界実証**:
   - クエリ案: "Ichimoku cloud regime detection trading rule cryptocurrency"
   - 期待発見: 一目均衡表を regime 判定に組み込んだ業界実証

---

## 結果ファイルフォーマット (auditor 用)

`.claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md` に以下 7 セクションを出力:

1. **Step -1 監査対象の型宣言** (文書型 = 詳細設計レビュー・実装スクリプトはない段階)
2. **Step 0 指摘前提確認** (= ml_pipeline_baseline_v1.md §6.1.1-6.1.6 全文 view 機械的証跡 + v15 HMM 実数値 verify)
3. **観点 ①〜⑦ + Q1-Q7 の所見** (各観点・各 Q に対し「数値根拠ある断言」or「データ不足 (理由)」)
   - 観点 = PASS / FAIL 明示
   - Q = 業界整合 / 改善余地 N 件 明示
4. **外部検索結果サマリー** (検索クエリ + 主要発見 5-10 件・URL or 論文出典)
5. **総合判定**:
   - Verdict: GO (= 実装着手可) / NO-GO (= 重大欠陥・再設計必要) / PIVOT (= 一部修正で着手可) / OTHER
   - 業界基準・学術根拠を伴う根拠
6. **改善方向性** (具体提案 3-7 件・優先度明示 Critical/Major/Minor)
7. **CC プロセス欠陥対策** (= cc_role §1.4.6 改訂提案・該当があれば・本セッションでの L-232 違反 9-10 回再演対策)

---

## 必ず守ること (auditor 守則)

- 本監査スコープ = **詳細設計の妥当性 verify**。月次 NET 達成可能性は対象外
- 月次 NET ≥ $1,900 を下げる方向の提案禁止 (cc_role §1.0 / auditor_template L15)
- 「可能性がある」「かもしれない」「検討の余地」は禁止 (auditor_template L20)
- 数値根拠の断言 or 「データ不足 (理由: 〇〇)」で答える
- 同型バイアス警告: 同一訓練ベース AI として CC の論理に共感しすぎないこと (auditor_template L24-30)
- ChatGPT 等の外部 AI 使用不可
- **外部検索は WebSearch / WebFetch ツールで必ず実施** (= 7 トピック以上)
- 内部文書だけでなく、トレードについての外部認知 (Crypto futures algo trading の業界実情) を踏まえる
- L-232 改善 1-4 (= 雑な言い切り癖 / 文章わかりづらい / cat-bitget 固有性 verify / 翻訳禁止) を auditor 自身も遵守

---

依頼書終わり。

## まこさん向け呼びかけ例文 (新規セッション起動時)

別 Claude Code セッションを開き、本依頼書のフルパスを明示して以下のように依頼:

```
監査してほしい
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-05-27_step15_regime_ensemble_design_cp1_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。
