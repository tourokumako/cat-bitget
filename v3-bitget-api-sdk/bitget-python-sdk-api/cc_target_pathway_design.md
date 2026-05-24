# cc_target_pathway_design.md — 月 $1,900 到達設計レシピ (Target Pathway Design)

作成: 2026-05-26 (CC・cc_role v1)
版: v1 (初版・L-219 起草分)
位置付け: **目標達成設計の上位正本**。`cc_ml_design_spec.md` (ML pipeline 仕様) + `phase_flow_v4_with_recovery.md` (Phase フロー) の **上位レイヤー** (= 「ML 手順をやる前に目標到達ロジックを設計する」役割)
状態: 運用しながら追記・改訂

---

## §0 本ファイルの位置付け・運用ルール

### 0.1 なぜこのファイルが必要か

L-215 (Phase 4-b 領域を Phase 1 で先行実装した設計逸脱で 5 セッション浪費) の根本原因は「**目標到達設計が無いまま ML 手順を回した**」こと。具体的には:

- 凍結ベースライン月 $370 → 目標月 $1,900 = **5.1× gap** をどう作るかの分解が無かった
- 各 Phase の合格基準が「予測精度」に閉じていて「月次 NET 寄与」に紐付いていなかった
- Phase 4-b (Exit 設計) が後段にあるが、お金が生まれるのは Phase 4-b ⇒ 前段の Phase 1 を頑張っても無駄打ちのリスク
- Regime filter (悪い相場を避ける) が独立 Phase として存在しない

2026-05-26 まこさん指摘「目標達成するための、phase_flow_v4 のフローに不具合や改善すべき点が多々あるってこと?」を受けて、**ML 手順の上に「目標達成レシピ」を置く** ことで構造的に解決する設計文書を新規作成。

### 0.2 文書ヒエラルキー (本ファイルの位置)

```
[上位] CLAUDE.md / WORKFLOW.md / false_positive_incident_policy.md (プロジェクト全体ルール)
       ↓
[上位] cc_role.md / cc_target_pathway_design.md (本ファイル・目標到達設計)
       ↓
[中位] cc_ml_design_spec.md (ML pipeline 仕様)
       ↓
[中位] phase_flow_v4_with_recovery.md (Phase 0-7 フロー)
       ↓
[下位] phase_compliance_checklist.md (Phase 別 verify ガード)
```

### 0.3 運用ルール (絶対遵守)

- **Phase 着手前 / Phase 合格基準改訂前 / 戦略レバー値変更前に必読**
- 機械的証跡 (`wc -l` + Read 全文 view + 該当箇所引用) を出す
- 本ファイルの数値根拠は [[industry_benchmark_knowledge_base]] に基づく (= 業界実証ベース)
- レシピ改訂は CC 単独で確定しない・まこさん最終確認 + 監査経路 (`/audit`) を通す
- 「事実」「推測」マーカーを毎数値に付ける (cc_role §1.4 #5・未検証推測の断定形禁止)

---

## §1 現状と目標の gap

### 1.1 凍結ベースライン (現状の月次 NET)

| 項目 | 値 | 出典 |
|---|---|---|
| 月平均 NET (凍結ベースライン) | **$370/月** | [[project_goal]] / CLAUDE.md §目標 |
| 日次換算 (= $370 ÷ 30) | $12.34/day | 同上 |
| 年次換算 (= $370 × 12) | $4,440/年 | 同上 |
| 戦略 | 手動 Priority P1-P24 (cat_v9_decider) | strategies/cat_v9_decider.py |
| 期間 | Replay 直近 1 年程度 | results/replay/ |

**事実マーカー**: 凍結ベースライン $370 は [[project_goal]] (= 唯一の正本) 記載値。詳細内訳 (どの Priority が何 $ 稼ぐか) は results/replay/ の集計が必要 (本ファイルでは未集計)。

### 1.2 目標 (本番投入可判定基準)

| 項目 | 値 | 出典 |
|---|---|---|
| 月次 NET (本番投入可判定基準) | **$1,900/月** (全 12 ヶ月クリア・単月でも未達なら不合格) | CLAUDE.md §目標 / [[project_goal]] |
| 日次目安 (判定基準ではない) | $60/day (= $1,900 ÷ ~30) | 同上 |
| 年次 | $22,800/年 | 同上 |

### 1.3 gap

- **5.1× 増** ($370 → $1,900)
- 業界相場との照合 ([[industry_benchmark_knowledge_base]] §1.3):
  - 凍結ベースライン月 3.08% return (exposure $12,000 base) = Crypto HF 平均年 36% と同水準
  - 目標月 15.83% return = Crypto HF 平均 5.3× 上回る = **業界トップ Quant HF 級** (Sharpe 2.51・年 48%)
- 結論: **達成可能だが業界上位 5-10% 帯**。マージン薄く・1 月でも下振れすれば未達。

---

## §2 5.1× gap の分解 — どこから作るか

### 2.1 5 レバー (業界経験則ベース・[[industry_benchmark_knowledge_base]] §2)

| # | レバー | 期待倍率 (中央値) | 範囲 (業界実証) | 担当 Phase |
|---|---|---|---|---|
| 1 | **Entry 改善** | 1.4× | 1.1-1.6× | Phase 1 + Phase 4-a |
| 2 | **Exit 最適化** | 1.7× | 1.3-2.0× | Phase 4-b |
| 3 | **戦略並立** (cluster) | 1.5× | 1.2-1.8× | Phase 4-a (cluster=3) |
| 4 | **Regime filter** | 1.3× | 1.1-1.6× | **Phase 4-c (新規・現状未設計)** |
| 5 | **Position sizing** | 1.2× | 1.1-1.3× | Phase 5-d |

**5 レバー中央値合計**: 1.4 × 1.7 × 1.5 × 1.3 × 1.2 = **5.57×** → 月 $2,060 (目標 + 8% マージン)

### 2.2 組み合わせ試算 (5.1× 達成パス・複数経路)

[[industry_benchmark_knowledge_base]] §2.6 から引用:

| ケース | Entry | Exit | 並立 | Regime | Sizing | 合計倍率 | 月次 NET | 判定 |
|---|---|---|---|---|---|---|---|---|
| A. 控えめ   | 1.2× | 1.4× | 1.3× | 1.1× | 1.1× | **2.64×** | $976 | ❌ 未達 |
| **B. 中央値** | 1.4× | 1.7× | 1.5× | 1.3× | 1.2× | **5.57×** | $2,060 | ✅ 達成 + 8% マージン |
| C. 楽観値   | 1.6× | 2.0× | 1.8× | 1.6× | 1.3× | **11.98×** | $4,433 | ◎ 過剰マージン |
| D. Entry単独頼り | 1.6× | 1.0× | 1.0× | 1.0× | 1.0× | **1.6×** | $592 | ❌ 大幅未達 (= 現状) |
| E. Exit + 並立中心 | 1.0× | 2.0× | 1.8× | 1.2× | 1.2× | **5.18×** | $1,917 | ⚠ ギリ達成・マージン薄 |

**示唆**:

- **D ケース (Entry 単独頼り)** = phase_flow_v4 で Phase 1 だけ回している現状 → **構造的に到達不可能**
- **B ケース (中央値)** で 5.57× 達成 = **5 レバーすべての中央値必要** (= どれか落ちると未達)
- **E ケース (Exit + 並立中心)** = Entry 改善が困難でも他レバーで補える代替経路あり
- 単一レバー上限値 (Exit 2.0× / 並立 1.8×) でも 5× に届かない = **複数レバー組合せ必須**

### 2.3 「設計姿勢: マージン厚く」の解釈

- B (中央値) の 8% マージンは「ジャスト達成設計」(CLAUDE.md §目標 違反リスク)
- C (楽観値) はマージン厚いが楽観値依存 = 設計欠陥になりやすい
- **推奨**: **B (中央値) で計画 + 各レバーで上振れ余地を残す** (= 楽観値依存しない)
- かつ DSR degradation (live 50% 想定・§3.2 参照) を考慮すると Phase 5 で月 $3,800 目標 = 業界相場で 2× マージン

---

## §3 各レバーの担当 Phase + 現状ステータス

### 3.1 レバー別 Phase ステータス表

| レバー | 担当 Phase | 現状 | 必要アクション |
|---|---|---|---|
| 1. Entry 改善 | Phase 1 + Phase 4-a | Phase 1 v6 6 案完走 (案 e ★最良・但し TP Precision 0.44 天井) | 監査結果 NO-GO + PIVOT 反映 (案 f AFML 修正 / アルゴ多様化 / 正則化強化 / CPCV) |
| 2. Exit 最適化 | Phase 4-b | **未着手** | **本レシピ最優先**・Phase 4-b 単体先行検証 (§5.2) |
| 3. 戦略並立 | Phase 4-a (cluster=3) | k=3 確定 (silhouette 0.510)・但し cluster 間相関未検証 | Phase 4-a 単体検証 (cluster 間相関 < 0.3 達成可能か) |
| 4. Regime filter | **Phase 4-c (新規)** | **未設計** | Phase 4-c 新規追加 + HMM/200-day MA filter 投入 |
| 5. Position sizing | Phase 5-d | 暫定 0.024 BTC 固定 (= 0.12/cap_5) | Half-Kelly + volatility targeting 投入 |

### 3.2 Phase 4-c (Regime filter) 新規追加の根拠

**現 phase_flow_v4 に Regime filter が明示 Phase として存在しない**。Phase 1 の Triple Barrier label に「TIME class (= 期間内に TP/SL 未達)」が暗黙に regime 情報を含むが、明示 filter ではない。

業界実証 ([[industry_benchmark_knowledge_base]] §2.4):
- 200-day MA regime filter: DD 60% 削減
- HMM regime detection: Sharpe 1.76 vs 1.16 (= +52% 改善)
- jump model: 年次 return +1-4%
- 一般化: risk-adjusted return +10-30%

→ **Regime filter 1.3× は外せない**。Phase 4-c として新規追加が必要。

ただし注意点:
- regime 判定研究は cat-bitget では凍結中 (WORKFLOW.md §regime 研究・[[regime_research]])
- 過去の v14 56% / stage3 33% の精度天井 + 5min 運用要件との時間軸ズレで凍結
- 「凍結素材を Phase 4-c に転用」が現実的経路 (= regime_research.md の素材活用)

### 3.3 cc_ml_design_spec.md / phase_flow_v4 への影響

| ファイル | 影響 | 対応 |
|---|---|---|
| cc_ml_design_spec.md | Phase 構成に Phase 4-c 追加 + Phase 別合格基準の PnL 紐付け改訂 | 本レシピ確定後に改訂 |
| phase_flow_v4_with_recovery.md | §2 Phase 1 評価軸 + §4 全体フロー俯瞰 + §5 CP 監査内容に Phase 4-c 追加 | 同上 |
| phase_compliance_checklist.md | Phase 4-c verify ガード追加 | 同上 |

---

## §4 各 Phase の必要条件 (= 合格基準を「月 NET 寄与」から逆算)

### 4.1 Phase 1 (Entry 精度) 必要条件

**ベースライン**: 凍結 $370 × Entry 1.4× = **$518/月** (= Phase 1 単独後の到達点)

| 既存合格基準 | 改訂提案 |
|---|---|
| entropy_lift > 0.10 | 維持 |
| TP Precision > 0.5 | **緩和: TP Precision > 0.45** (= 業界 5min XGBoost 水準・Bitcoin trend 特性で 0.55 まで上振れ可) |
| Direction Accuracy > 0.55 (案 c のみ) | 維持 |
| (新規) | **期待値 proxy > 0** ← 「TP Precision × TP_gain - (1-TP) × SL_loss - fee」で月次 NET proxy |

**根拠 ([[industry_benchmark_knowledge_base]] §2.1)**:
- 業界実証 TP Precision 0.45 = baseline 0.32 + 13pp = Phase 1 v6 6 案実測天井
- TP Precision 0.5 厳格適用 = 業界相場上限超え = 達成困難 (= L-217 で Simulated PnL を Phase 5 移動した経緯と整合)
- 緩和して「期待値 proxy > 0」を追加することで PnL 寄与を Phase 1 で確認可能

### 4.2 Phase 4-b (Exit 最適化) 必要条件

**ベースライン**: $518/月 × Exit 1.7× = **$881/月** (= Phase 4-b 後の到達点)

| 既存合格基準 | 改訂提案 |
|---|---|
| cluster_best_exit は train PnL のみで選定 | 維持 |
| Phase 4-b で best Exit (TP_PCT / SL_PCT / TIME_EXIT) 確定 | + **Triple Barrier 整合性 verify**追加 |
| (新規) | **平均 trade NET > fee floor (0.028%) + 月次 NET 寄与 +70% 以上** ← Exit 改善で 1.7× 達成 |

**根拠 ([[industry_benchmark_knowledge_base]] §2.2)**:
- 業界知見「real gains come from refining exits」(Jigsaw Trading)
- Triple Barrier method (Lopez de Prado AFML Ch.3) が業界標準
- Exit 1.7× は中央値 + 過去業界事例で 30-100% NET 改善が観測

### 4.3 Phase 4-a (cluster 並立) 必要条件

**ベースライン**: $881/月 × 並立 1.5× = **$1,322/月** (= Phase 4-a 並立後)

| 既存合格基準 | 改訂提案 |
|---|---|
| k=3 確定 (silhouette 0.510) | 維持 |
| (新規) | **cluster 間相関 < 0.3** ← 直交 alpha 確保 (Square Root Rule 効果出すため) |
| (新規) | **各 cluster の月次 Sharpe > 0.5** ← 全 cluster が独立収益源 |

**根拠 ([[industry_benchmark_knowledge_base]] §2.3)**:
- Mom + Mean-Reversion 並立で Sharpe 1.71 (= 直交 alpha の効果)
- Square Root Rule: 無相関 portfolio の max excess return = ½ × sum(Sharpe²)
- cluster 間相関 ≥ 0.7 だと並立効果ほぼゼロ (= 同一戦略を 3 倍に増やすだけ)

### 4.4 Phase 4-c (Regime filter) 必要条件 — **NEW**

**ベースライン**: $1,322/月 × Regime 1.3× = **$1,719/月** (= Phase 4-c 後)

| 新規合格基準 |
|---|
| 悪い regime (= Phase 5 backtest で月次 NET 平均 -50% 以下の局面) での発火を **50% 以上抑制** |
| 良い regime での発火を **90% 以上維持** (= regime filter 過剰反応を防止) |
| Out-of-sample で lag 検出 < 5 bar (= filter の遅延を許容範囲に) |

**根拠 ([[industry_benchmark_knowledge_base]] §2.4)**:
- 200-day MA filter: DD 60% 削減実証
- HMM out-of-sample は lag 問題あり → 5 bar lag は許容範囲 (= 5min × 5 = 25 分)

### 4.5 Phase 5-d (Position sizing) 必要条件

**ベースライン**: $1,719/月 × Sizing 1.2× = **$2,063/月** (= 5 レバー後・目標 + 8% マージン)

| 既存合格基準 | 改訂提案 |
|---|---|
| 0.12 BTC 合計上限維持 | 維持 (絶対遵守・false_positive §0-2) |
| cap=N で 1 pos = 0.12/N BTC | 動的化: **Half-Kelly + volatility targeting** に変更 |
| (新規) | **cluster 強度別動的配分**: 強い cluster に 0.04 BTC・弱い cluster に 0.01 BTC (合計 ≤ 0.12) |

**根拠 ([[industry_benchmark_knowledge_base]] §2.5)**:
- Half-Kelly = 75% 成長率 / 50% volatility 削減 = 業界 sweet spot
- Most professional traders use Half-Kelly or less
- VIX-Rank dynamic scaling = uncertain edge への robustness

### 4.6 Phase 5 (Replay 仮テスト) 必要条件 — **DSR 補正反映**

**ベースライン**: $2,063/月 × DSR degradation 補正 = 業界相場で **live で 50% degradation 想定**

| 既存合格基準 | 改訂提案 |
|---|---|
| 全 12 ヶ月 NET ≥ $1,900 | **改訂: 全 12 ヶ月 NET ≥ $3,800** (= live 50% degradation 想定で Phase 5 で 2× マージン) |
| 単月でも未達なら不合格 | 維持 |

**根拠 ([[industry_benchmark_knowledge_base]] §3.2)**:
- Deflated Sharpe Ratio (de Prado + Bailey 2014): IS Sharpe vs OOS Sharpe degradation 30-70%
- 業界実証 live vs backtest degradation factor 50% が中央値
- = Phase 5 で月 $1,900 達成 → 本番月 $950 になる risk = Phase 6-b 失敗

### 4.7 Phase 6-b (本テスト 2026 Q1) 必要条件

| 既存合格基準 | 改訂提案 |
|---|---|
| 全 3 ヶ月 NET ≥ $1,900 | 維持 (最終判定) |

**注**: Phase 5 で 2× マージン (= 月 $3,800) を確保した場合、Phase 6-b で月 $1,900 はジャスト達成圏 (= 50% degradation 想定整合)。

---

## §5 検証順序 (依存関係)

### 5.1 現 phase_flow_v4 順序 (問題)

```
Phase 0 (label) → Phase 1 (Entry 学習) → Phase 2 (精度判定) → Phase 3-a/b (ハイパラ) → Phase 4-a (cluster) → Phase 4-b (Exit) → Phase 5 (Replay)
```

**問題**:
- Phase 4-b (Exit = お金が生まれる場所) が後段
- Phase 1 を完璧にしても Phase 4-b で「どう設計しても 1.7× 出ない」だったら全部無駄
- 過去 5 セッション浪費 (L-215) はまさにこの構造

### 5.2 改訂提案順序

```
Phase 0 (完了)
  ↓
Phase 4-b 単体先行検証 (NEW・1-2 セッション) — 本レシピ最優先
  ↓ [PASS] → 続行 / [FAIL] → 根本見直し
Phase 4-a 単体検証 (NEW・1 セッション)
  ↓
Phase 1 v6 再開 (= Layer 3 投入・案 f 修正 / アルゴ多様化)
  ↓
Phase 4-c 新規追加 (Regime filter・NEW)
  ↓
Phase 5-d (Position sizing 改訂)
  ↓
Phase 5 (Replay 仮テスト・全 12 ヶ月 NET ≥ $3,800)
  ↓
Phase 6-b (本テスト 2026 Q1・全 3 ヶ月 NET ≥ $1,900)
```

### 5.3 Phase 4-b 単体先行検証の方法 (最優先・1-2 セッション)

**目的**: Exit 改善で月 $370 → 月 $630 (= 1.7×) が出るか早期検証 + Phase 1 を本格再開する前に Phase 4-b の現実性確認

**検証方法 (3 候補から推奨)**:

| 候補 | 内容 | 評価 |
|---|---|---|
| (1) ナイーブ Entry + Exit grid | Entry = ランダム or 単一指標 / Exit grid 網羅 | Phase 4-b 上限性能可視化 (但しナイーブ Entry 下) |
| **(2) 手動 Priority Entry + Exit 最適化** ★ 推奨 | Entry = cat_v9 P1-P24 (= 凍結ベースライン $370) / Exit Triple Barrier 最適化 | **実 Entry で Exit 効果直接測定・凍結ベースラインから上振れ実証** |
| (3) Phase 1 v6 案 e + Exit 最適化 | Phase 1 完走済 case_e triple_barrier 予測を Entry / Exit 別途 grid | Phase 1 を待つ |

**推奨: (2) 手動 Priority Entry + Exit 最適化**

**検証フロー**:
1. cat_v9 P1-P24 で Entry 信号生成 (= 既存 strategies/cat_v9_decider.py の発火履歴)
2. Triple Barrier method (Lopez de Prado AFML Ch.3) で TP/SL/Time を grid 探索
   - TP_PCT: [0.3, 0.5, 0.8, 1.0, 1.5, 2.0]%
   - SL_PCT: [0.3, 0.5, 0.8, 1.0]%
   - TIME_EXIT_BARS: [12, 24, 48, 96] bar
3. 各組合せで Replay → 月次 NET 集計
4. 凍結 $370 月 → best Exit で **月 $630 (= 1.7×)** 出るかを判定

**判定基準**:
- **PASS**: best Exit で月平均 ≥ $630 + 全 12 ヶ月で凍結ベースライン超え → Phase 4-b 現実性確認 → 続行
- **FAIL (1.7× 出ない・1.3-1.5× レベル)**: Exit 改善余地が業界相場以下 → 根本見直し (= 検証順序再考 / Phase 1 強化に振り替える等)
- **FAIL (1.0× 未満)**: Exit 改善効果ゼロ = 設計欠陥 → 全面再設計

### 5.4 Phase 4-a 単体検証 (1 セッション)

**目的**: cluster=3 並立で cluster 間相関 < 0.3 達成可能か確認 = 戦略並立 1.5× 寄与の現実性

**検証フロー**:
1. Phase 4-a 既存実装 (k-means k=3) を train データで fit
2. 各 cluster の月次 NET 系列を生成 (= cluster ベース backtest)
3. cluster 間 Pearson 相関係数 matrix 計算
4. max(相関) < 0.3 達成可能か判定

**判定基準**:
- **PASS**: max(相関) < 0.3 + 各 cluster の Sharpe > 0.5 → 並立 1.5× 現実性確認
- **FAIL (相関 ≥ 0.5)**: cluster が直交 alpha でない = 同一戦略の重複 → cluster 設計見直し (k 値変更 / 特徴量変更)

### 5.5 Phase 4-b → Phase 1 への戻り

Phase 4-b 単体検証 PASS なら Phase 1 v6 を再開:
- 監査結果 (NO-GO + PIVOT・`.claude/audits/2026-05-26_phase1_v6_6cases_methodology_audit_report.md`) の修正反映
- 案 f AFML 標準実装修正 (Critical 提案 1)
- B-10 アルゴ多様化 Phase 1 内並列 (Major 提案 2)
- LightGBM 正則化強化 (Major 提案 3)
- CPCV 投入 (Major 提案 4)

---

## §6 Phase 1 v6 の処置 (現状の扱い)

### 6.1 現状

- Phase 1 v6 6 案並列完走 (case_b/c/d/e/f) + 監査済 (NO-GO + PIVOT 判定)
- 案 e (entropy_lift 6/8 PASS) が ★ 最良だが TP Precision 0/8 PASS (= predictive value 不足)
- 過去 5 セッション浪費 (L-215) は本レシピなしで Phase 1 を頑張った結果

### 6.2 処置

- **保留** (アーカイブはしない・将来 Phase 4-b 検証後に再着手)
- 監査結果ファイル `.claude/audits/2026-05-26_phase1_v6_6cases_methodology_audit_report.md` を参照可能状態で保持
- 監査提案 (案 f 修正 / B-10 多様化 / 正則化強化 / CPCV) は §5.5 の Phase 1 再開時に検討
- Phase 4-b 単体検証 PASS が確認できるまで Phase 1 改修コードを書かない (= L-215 同型再演防止)

### 6.3 既存 artifact の扱い

| artifact | 場所 | 扱い |
|---|---|---|
| case_b/c/d/e/f summary JSON | results/priority_rebuild/ml_phase1_v5/_case_*/ | 保持・Phase 1 再開時に参照 |
| feature_importance top20 csv | 同上 | 保持 |
| run_lgbm_phase1_v5_case_*.py | scripts/priority_rebuild/ | 保持 (untracked のまま) |
| 監査レポート | .claude/audits/ | 保持 |

---

## §7 次のアクション (優先順位 + 工数見積)

### 7.1 即着手 (本セッション後・優先順位順)

| # | アクション | 工数 | 担当 | 完了判定 |
|---|---|---|---|---|
| 1 | 本レシピ確定 + CLAUDE.md / WORKFLOW.md に index 追加 + git commit | 本セッション内 | CC | 本ファイル作成 + index 反映 + commit |
| 2 | cc_ml_design_spec.md 改訂 (Phase 4-c 追加 + Phase 別合格基準 PnL 紐付け) | 次セッション 1 回 | CC | spec 改訂版 commit |
| 3 | phase_flow_v4_with_recovery.md 改訂 (§5.2 検証順序反映 + Phase 4-c 追加) | 次セッション 1 回 | CC | phase_flow v7 改訂 commit |
| 4 | phase_compliance_checklist.md 改訂 (Phase 4-c verify ガード追加) | 次セッション 1 回 | CC | checklist 改訂 commit |
| 5 | **Phase 4-b 単体先行検証スクリプト実装** (= §5.3 の (2) 手動 Priority Entry + Triple Barrier Exit grid) | 1-2 セッション | CC | 実装 + Replay + 月次 NET 集計 + 判定 |
| 6 | Phase 4-b 単体検証結果に基づき続行判定 | (5) 完了後 | CC + まこさん | PASS なら Phase 4-a 検証へ・FAIL なら根本見直し |

### 7.2 並行作業 (随時実施可)

- [[industry_benchmark_knowledge_base]] §6.2 (次回 WebSearch 候補) の追加調査
- 監査依頼テンプレ `.claude/audits/inputs/_template.md` の運用検証 (= 本レシピ確定後の CP 監査経路で実使用)

### 7.3 中長期 (Phase 4-b 検証 PASS 後)

| Phase | 状態 | 想定工数 |
|---|---|---|
| Phase 4-a 単体検証 | 未着手 | 1 セッション |
| Phase 1 v6 再開 (Layer 3 投入) | 保留 | 2-3 セッション |
| Phase 4-c (Regime filter) 新規追加 | 未設計 | 2-3 セッション |
| Phase 5-d (Position sizing 改訂) | 未着手 | 1-2 セッション |
| Phase 5 (Replay 仮テスト) | 未着手 | 1 セッション |
| Phase 6-b (本テスト) | 未着手 | 1 セッション (最終判定) |

**全体目安**: Phase 4-b 検証 PASS から Phase 6-b 完了まで **8-12 セッション**程度。

---

## §8 改訂履歴

| 版 | 日付 | 内容 |
|---|---|---|
| v1 | 2026-05-26 | 初版・L-219 起草分・5.1× gap 分解 5 レバー + 検証順序改訂提案 + Phase 4-c 新規追加 + Phase 4-b 単体先行検証フロー |

---

## §9 関連ファイル

- [[industry_benchmark_knowledge_base]] — 業界相場・経験則 (本レシピの数値根拠)
- [[cc_ml_design_spec]] (`cc_ml_design_spec.md`) — ML pipeline 仕様 (本レシピの下位レイヤー)
- [[phase_flow_v4_with_recovery]] — Phase 0-7 フロー (本レシピで改訂対象)
- [[cc_role]] §1.0 / §1.4.6 / §1.5 — CC 役割定義 + 目的整合性ゲート
- [[project_goal]] — 月次 NET ≥ $1,900 唯一の正本
- `CLAUDE.md` §目標 — プロジェクト目標 (本レシピと整合)
- `.claude/audits/2026-05-26_phase1_v6_6cases_methodology_audit_report.md` — Phase 1 v6 監査結果 (Layer 3 投入提案の根拠)

---

(本ファイル終わり・追記可能)
