# ML 学習デザイン v4 完成版 (2026-05-21 CC ML 設計担当移譲後・23 軸 §X.10 整合再構築)

## §0 v4 の位置付け

### v3 → v4 切替理由
- v3 (2026-05-20 まこさん承認) は Web Claude 作成・**23 軸全体構造は反映済だが Layer 配分の確定根拠未明示**
- 2026-05-21 ML 設計担当が Web Claude → CC へ完全移譲 (handoff v18/v19)
- handoff v19 §0.14 で Entry/Exit 両側学習方法改善議論到達 (新 Path A 改) + Phase 1-a/1-b/1-c smoke 物理証跡 3 連続
- CC が `CAT−指標マトリックス - 一覧.csv` (1962 行) 全文 view + §X.10 確定 Layer 担当を完全把握した上で再構築

### v3 archive 先
`.claude/memory/archive/learning_design_v3_20260521.md` (174 行・全文保存)

### v4 の構造
1. v3 23 軸振り分け表 + Phase 別優先順位は **§X.10 確定 Layer 担当に整合する形で再構築**
2. Web Claude ドラフト「5 学習タスク (T1〜T5) 分解 + Layer 1〜3 割り付け + Layer 1 着手フロー」構造を採用
3. handoff v19 §0.14 Entry 学習問題 5 つへの対応を**特徴量空間拡張 + cluster 入力 B 案で第一弾応答** (学習方法そのものの Layer 配分逆転はしない)

---

## §1 設計提案前 verify (毎回必須・3 項目)

### 本番再現性 7 項目 (exchange_spec.md 整合)
1. 最小注文サイズ 0.0001 BTC (per-position サイズ verify)
2. 最小注文額 5 USDT (BTC 価格 stress test $30k-$150k 全域)
3. Tick size 0.1 USDT (Exit 指値で適用)
4. Maker 指値 TTL 3 本 + 同一 side pending 禁止 → add トリガ「前回 add 約定確認 + 時間経過 ≥ 15 分」必須
5. SL 設定 add_count ≥ 2 のみ → MAX_ADDS=1 combo は time_exit/TP のみ運用
6. メンテはナシ (24/7 取引・exchange_spec.md L37・公式ガイド確認済)
7. Maker 剥落 0.014% / 0.02% stress test → Phase 5 NET 計算で両値

### 価格非依存性 6 項目
1. ラベル MFE/MAE は pct ベース (USD 絶対値禁止・14 ラベル独立学習 LONG_MFE/MAE_pct × K=7)
2. Exit パラメータ % / 比率 / 分単位 (PROFIT_LOCK_USD → PROFIT_LOCK_PCT 置換)
3. cluster 入力 pct 化
4. feature_importance 上位の USD 絶対値系 blacklist
5. add トリガ % 表現
6. TP_FEE_FLOOR は BTC 価格動的計算

### 23 軸 First Principles (cc_role.md §1.5 / §1.6 / §1.7)
- デザイン責任は CC (Web Claude 確認質問乱発禁止)
- 23 軸を「思考シュリンク矯正・判断材料素材」として参照 (教条主義禁止)
- 手動 Priority は「最低スタートライン」(ベンチマーク扱い禁止)

---

## §2 23 軸 → 5 学習タスク分解 (Web Claude ドラフト構造採用)

| タスク | 役割 | 必要な軸 (学習対象) | 制約として効く軸 (D 固定) |
|---|---|---|---|
| **T1: Entry タイミング予測** | 5 分足ごとに「Entry すべきか・どっち側か・どの強さか」 | A-1 / A-3 / A-4 / A-5 / B-9 / B-10 / B-12 / B-13 / B-15 | B-14 期間 |
| **T2: Entry の質分類** | T1 の Entry を性質別に cluster 化 → T3/T4 の分岐入力 | B-11 (手法 + 入力ベクトル) | — |
| **T3: Exit タイミング予測** | cluster 別に最適 Exit を決める | A-2 / A-3 Exit 側 (共有) / D-β (A-2 統合済) | D-η 手数料 |
| **T4: ポジション配分** | 0.12 BTC 枠内で combo・cluster 別配分 | A-6 / A-7 配分側 / B-8 / D-ζ 活用方式側 | A-7 上限 / D-ζ hedge 許可 |
| **T5: 発火フィルタ** | Entry 出ても見送る条件 | D-γ 位置 / D-δ 時間帯 / D-ε regime / D-α 発火頻度 (結果) | — |
| **全タスク共通制約** | 学習データ・執行 | — | B-14 期間 / D-η 手数料 / D-θ 発注タイプ |

### 学習タスクの依存順序

```
T1 (Entry タイミング)
   出力: 予測 14 ラベル MFE/MAE pct (LONG_MFE/MAE × K=7・対称性活用で SHORT 流用)
        ↓
T2 (質分類)
   出力: cluster ID
        ↓
   ┌────┴────┐
T3 (Exit)   T4 (配分)
   ↓          ↓
   └────┬────┘
        ↓
T5 (発火フィルタ・後付け除外)
```

---

## §3 23 軸振り分け表 (v3 §X.10 整合・修正点明示)

| 軸 | 戦略 (Step 4 確定) | 内容 | Layer 担当 (§X.10 確定) |
|---|---|---|---|
| A-1 Entry 指標 | A 全投入 | 1432 指標 + 未学習 8 件 + まこさん発振系 3 件 + 業界カタログ (TA-Lib / pandas-ta / Murphy / Lopez de Prado) + 1w/1M MTF 拡張 = 約 2000-2500 列見込み | **Layer 1 ④** |
| A-2 Exit 指標 | A 全投入 + B 探索 | 業界カタログ 16 サブカテゴリから 12 種以上 + 手動 Priority 8 種以上追加 + trailing 不採用構造的原因究明 + 採用方式見直し (train PnL idxmax → 複合採用) | **Layer 1 ① (最優先)** + Layer 2 ① / ⑤ |
| A-3 閾値・パラメータ | A 全投入 (パラメータ) + C 学習 (閾値) | パラメータ違い並列 (rsi21 / adx7/21 / bb_window_10/50 / macd 別パラメータ) + 閾値は LightGBM 自動分割 + D-γ 統合 (location_prev / entry_risk_score を特徴量化) + 手動閾値派生特徴量 A/B/C 案監査 | **Layer 1 ④ + Layer 1 ①** + Layer 2 + Layer 3 |
| A-4 時間軸 K | B 探索 | K = {6, 12, 24, 48, 96, 144, 288} 並列 = **14 ラベル** (対称性活用) + K=24 LONG/SHORT q99 欠落原因究明 + K=96 q95-q99 切り捨て判定 (保有時間上限 1 日内) | **Layer 1 ③** + Layer 1 ② + Layer 2 |
| A-5 時間足 bar | A 全投入 | 6 TF (5m/15m/30m/1h/4h/1d) + 1w/1M 追加 = 8 TF + TF 不均衡解消 (stoch_k / bb_pct_b の TF 欠落補完) + ffill 初期実装 + 監査経由 MTF 4 方式比較 (3m は Layer 2 検討・1m は禁止) | **Layer 1 ④** + 監査経路 + Layer 2 + Layer 3 |
| A-6 MAX_ADDS / 配分 | B + C 学習 + 制約セット | MAX_ADDS={1,2,3,5,8,10} × per-add 配分 6 方式並列 + add トリガ条件 ML 学習対象化 | Layer 2 ② + Layer 2 ⑤ + Layer 1 ② |
| A-7 サイジング | D 上限固定 + B + C | 合計 0.12 BTC 固定 + per-position ≥ 0.000167 BTC + 8 サイジング方式並列 + cluster 別配分 | 前提 (§4 矛盾解消) + Layer 2 ② / ③ + Layer 3 |
| B-8 cap | B 探索 | 静的 cap + combo 別 cap + 動的 cap 並列 (MAX_ADDS × n_sim ≤ 150 物理上限厳守) + **K96 LONG q95-q99 切り捨てによる no_trade 86.2% 改善幅測定** | **Layer 1 ② (最優先)** + Layer 2 ② / ③ |
| B-9 組み合わせ深さ | C 学習 | num_leaves={7,15,31,63,127} × max_depth={3,5,7,10,-1} × min_data_in_leaf={50,100,200,500} Optuna 探索 | **Layer 3** + Layer 1 ④ 後の検証 |
| B-10 学習アルゴ | B 探索 | 第 1 弾 XGBoost / CatBoost + 第 2 弾 MiniROCKET + 第 3 弾 MLP / TabNet + **第 4 弾 X2 強化学習** (audit#16 過小評価指摘・実装回避バイアス対策) | **Layer 3 第 1-4 弾** + 本番 / Bot 統合 (X2) |
| B-11 cluster | B 探索 | **B 案 (LONG/SHORT 差分 4 個追加・16→20 次元)** で cluster 構造的問題「方向性を分類していない」直接対応 + KMeans vs GMM vs HDBSCAN 比較 | **Layer 1 (B 案最優先)** + Layer 2 + Layer 3 |
| B-12 特徴量変換 | A 全投入 + B 探索 | **Fractional differentiation (d=0.3/0.5・Lopez de Prado 推奨) + PCA 補助列** + Wavelet 追加 (Layer 2) + MTF 4 方式 (ffill / 5m rolling / アンカー補間 / 複数特徴量分解) 監査比較 | **Layer 1 ④** + 監査経路 + Layer 2 + Layer 3 |
| B-13 Entry ratio 閾値 | B + C 学習 | rolling 365 日 q90/95/99 (現状) + cluster 別独立 quantile 並列 + **K24 LONG/SHORT q99 欠落原因究明 + 救出判定** + **Triple Barrier / Meta-Labeling (Layer 1 前倒し・2026-05-22 v5)** | **Layer 1 ① (最優先)** + Layer 1 ② + **Layer 1 (Layer 配分逆転・案 e/f)** |
| B-14 学習データ範囲 | D 期間固定 + B 探索 | 期間分割固定 (train 2021-04〜2024-12 / 仮 test 2025 / 本 test 2026 Q1) + **Walk-forward Purged K-Fold 5 fold を Phase 1 から導入 (Layer 1 前倒し・2026-05-22 v5)** + CPCV は Layer 3 + Class balancing / Focal loss / regime-based stratified サンプリング | **Layer 1 (Phase 1 から Purged K-Fold)** + Layer 2 (rolling 再学習) + Layer 3 (CPCV) |
| B-15 目的関数 | D 主目的固定 + B 探索 | 合格 = 月次 NET ≥ $1,900 全月固定 / **train 目的関数 = 6 案並列 (RMSE / Binary / Multiclass / Ranking LambdaRank / Triple Barrier multiclass / Meta-Labeling 2 段階・2026-05-22 v5 Layer 配分逆転)** + Layer 2 ⑤ Calibration + Layer 3 前半 SHAP / Conformal prediction / custom loss (直接 PnL / Sharpe / Asymmetric loss 等) + Layer 3 後半 高信頼度 only Entry | **Layer 1 (6 案並列・2026-05-22 v5)** + Layer 2 ⑤ + **Layer 3 前半/後半** |
| D-α 発火頻度 | C 学習 | 他軸従属変数・per-day 最低限ライン ≥ 10 件制約 (L-117 教訓) + 発火頻度実態可視化 | Layer 1 ① / Layer 1 ② / Layer 2 |
| D-γ Entry 位置 | A-3 統合 | location_prev / entry_risk_score を A-3 内で特徴量化 | A-3 内 |
| D-δ 時間帯曜日 | B 探索 (統合) | 統合フェーズで時間帯発火分布可視化 → フィルタ探索 (個別最適化禁止・WORKFLOW.md §設計思想 L230 遵守) | **Layer 2 統合フェーズ** |
| D-ε regime | B 探索 (Layer 2) | B-11 B 案結果次第・凍結解除判定 (教師なし HMM / GMM-HMM / UMAP+HDBSCAN) | Layer 1 (B-11 B 案連動) + Layer 2 以降 |
| D-ζ マルチサイド | D 許可固定 + C 学習 | hedge_mode 許可・合計 0.12 BTC 内で LONG/SHORT 動的配分 ML 学習 + cap カウント方法明文化 (合算 / 別 / net exposure) | 前提 (§4 改訂) + Layer 2 ② + Layer 3 |
| D-η 手数料 | D 固定 | Maker 0.014% (適用) / 0.02% (剥落) / Taker 0.042% / **Funding median +0.0002%/8h baseline** (audit#19 確定) + 不約定リスクモデル化 (Layer 3) | D 固定 + Layer 3 + Phase 7 |
| D-θ 発注タイプ | D 固定 + Layer 3 探索 | Maker 指値前提・不約定モデル化 + Stop/OCO は Layer 3 / Phase 7 | D 固定 + Layer 3 + Phase 7 |

### v3 → v4 修正点 (Layer 配分の明示)

| 軸 | v3 記述 | v4 修正 (明示化) |
|---|---|---|
| A-2 | 「Phase 4-b で cluster × K × side ごとに最適 Exit」 | **Layer 1 ① 最優先で trailing 不採用構造的原因究明 + 採用方式見直し (train PnL idxmax → 複合採用)** 追加 |
| B-8 | (Layer 配分明示なし) | **Layer 1 ② 最優先で K96 LONG q95-q99 切り捨て** 追加 |
| B-11 | (B 案明示なし) | **Layer 1 で B 案 (LONG/SHORT 差分追加) 最優先** 明示 |
| B-12 | (Fractional / PCA / MTF 4 方式明示なし) | **Layer 1 ④ Fractional differentiation + PCA + 監査経由 MTF 4 方式比較** 明示 |
| B-13 | (Layer 1 ① 欠落 combo 究明明示なし) | **Layer 1 ① K24 LONG/SHORT q99 欠落原因 verify + 救出判定** 追加 |
| B-15 | (audit#16 不確実性定量化過小評価対策明示なし) | **Layer 2 ⑤ Calibration + Layer 3 前半 SHAP / Conformal prediction + custom loss** 明示 |
| B-10 | (X2 強化学習過小評価対策明示なし) | **Layer 3 第 4 弾 X2 強化学習を本格検討対象** として明示 |
| A-1 | (業界カタログ追加見込み明示なし) | **1432 → 約 2000-2500 列見込み** (業界カタログ + 1w/1M MTF) 明示 |

---

## §4 Layer 1 タスク確定リスト (CC が深掘りで把握)

### Layer 1 ① (最優先・Exit 系 + 欠落 combo 究明)
- **A-2.10**: trailing exit ゼロ採用問題 (19 combo 中 0 件採用) の構造的原因究明 + Exit 候補拡張 (手動 Priority 8 種以上) + 採用方式見直し (train PnL idxmax → train PnL + train Sharpe + test 期間一部 verify の複合採用)
- **A-3.9**: 手動閾値派生特徴量 A/B/C 案監査
- **B-13.10**: K24 LONG/SHORT q99 欠落原因 verify + 救出判定
- **D-α.9**: 発火頻度実態可視化・最低限ライン設定 (per-day ≥ 10 件制約)

### Layer 1 ② (最優先・損 combo 切り捨て)
- **A-4.9**: K=96 q95-q99 切り捨て判定
- **B-8.9**: K96 LONG q95-q99 切り捨て (no_trade 86.2% の主因解消)
- **B-13.10**: K96 SHORT q95-q99 を含む test 不発火 combo の取り扱い
- **D-α.9**: 発火頻度改善幅測定

### Layer 1 ③ (K 窓見直し)
- **A-4.9**: K=6 / K=144 / K=288 追加 + K=24 欠落究明 (14 ラベル独立学習構成)

### Layer 1 ④ (特徴量空間 Layer 1 拡張・handoff v19 §0.14 Entry 学習問題第一弾応答)
- **A-1.10**: 未学習 8 件 (RCI(7/9/52) / RSI(21) / RSI_slope / BB_slope / Stoch(5m)) + まこさん発振系 3 件 (RSI ROC / Stoch K-D 差分 / MACD ヒストグラム slope) + 業界カタログ追加 (TA-Lib / pandas-ta / Murphy / Lopez de Prado) + 1w/1M MTF 拡張 = 1432 → 約 2000-2500 列
- **A-3.9**: パラメータ並列展開 (rsi21 / adx7 / adx21 / bb_window_10/50 / macd 別パラメータ)
- **A-5.10**: 1w/1M 軸追加 + TF カバー不均衡解消 + ffill 初期実装
- **B-12.10**: Fractional differentiation (d=0.3/0.5) + PCA 補助列追加

### Layer 1 (B-11 cluster B 案)
- **B-11.11**: 入力ベクトル B 案 (LONG/SHORT 差分 4 個追加・16→20 次元) + KMeans vs GMM vs HDBSCAN 比較 (cluster が「方向性を分類していない」構造的問題への直接対応)

### Layer 1 (監査 #20 で追加・Entry 学習方法選択肢並列・Layer 3 → Layer 1 昇格)
- **案 a (14 ラベル独立 RMSE)**: Phase 1-a 既存方式の特徴量拡張版で再学習 (流用ベースライン)
- **案 b (Entry Binary Classification・1/0 直接学習)**: 各 bar に「Entry すべきか (1/0)」ラベル・LightGBM Binary objective・class balancing 適用
- **案 c (Direction Multiclass・3 クラス分類・LONG/SHORT/Flat)**: LONG_MFE_pct > 閾値 → LONG / SHORT_MFE_pct > 閾値 → SHORT / どちらも閾値未満 → Flat・LightGBM Multiclass objective・hedge_mode 整合
- 3 案を Phase 1 並列実装 (監査 #20・2026-05-21)

### Layer 1 (Layer 配分逆転・2026-05-22 v5・Triple Barrier + Meta-Labeling + Walk-forward CV + Ranking を Layer 3 → Layer 1 前倒し)

まこさん指摘「学習方法が悪い」を反映した真の Layer 配分逆転。Layer 1 で **6 案並列**実装 + **Walk-forward Purged K-Fold 5 fold** + **DSR (Deflated Sharpe Ratio)** 採用:

- **案 d (新規・Ranking LambdaRank)**: LightGBM `objective='lambdarank'`・MFE_pct ランキング上位 N% のみ Entry 採用・Stefan Jansen *Machine Learning for Algorithmic Trading* Ch.12-13 整合
- **案 e (新規・Triple Barrier multiclass・Lopez de Prado AFML Ch.3)**: TP/SL/TIME 3 クラスラベル必要 → **Phase 0 改修指示書 v3.1 で同時生成** (28 ラベル列追加・56 ラベル列合計)・LightGBM Multiclass objective
- **案 f (新規・Meta-Labeling 2 段階・Lopez de Prado AFML Ch.3)**: 案 e の primary model 完了後 sequential 実装・secondary model で「primary 予測の correctness」予測 → precision 改善 + F1-score + Sharpe 向上 (Hudson & Thames mlfinlab 整合)
- **Walk-forward Purged K-Fold 5 fold** (Lopez de Prado AFML Ch.7 推奨・全 6 案で必須・mlfinlab.cross_validation.PurgedKFold 経由実装)
- **DSR 採用** (Bailey + Lopez de Prado 2014・SSRN 2460551・selection bias 補正・100+ grid 試行記録義務)

### Phase 1 合格基準 5 指標数値 (cc_ml_design_spec §1.6 と並列追加・2026-05-22 v5)

| # | 指標 | 合格閾値 | 根拠 |
|---|---|---|---|
| 1 | **entropy lift** | **> 10%** | AFML Ch.3 (< 10% で meta-labeling 投入推奨域・Phase 1-c smoke 6.04% は投入域) |
| 2 | **TP Precision** | **> 0.5** | 信頼度 50% 以上 (ベースライン 50% 超え必須) |
| 3 | **Direction Accuracy** (案 c) | **> 0.55** | LONG/SHORT 当たり率 (5% 以上有意性) |
| 4 | **Simulated PnL** | 12 ヶ月中 8+ ヶ月プラス + 年間 NET ≥ $500 | cc_ml_design_spec §1.6 整合 (Position size 未確定なので暫定基準) |
| 5 | **Walk-forward CV Sharpe (DSR 補正)** | **DSR > 1.0** | 本テスト相当 (selection bias 補正後) |

### Layer 3 投入条件厳格化 (2026-05-22 v5)

- **6 案いずれか上記 5 指標 ALL PASS** → 採用案で Phase 2 進行
- **6 案ベストでも 5 指標未達** → **即** Layer 3 投入 (現状 B-13.10 / B-14.12 / B-15.10 Layer 3 残存タスク = CPCV / Class balancing Focal loss / custom loss)
- **「ベスト案で Phase 2 進行して判定」は禁止** (Phase 1 未達 → Phase 2 改善保証なし)

### Phase 1 リソース計画 (2026-05-22 v5)

- **並列度**: 3 並列 (CPU 競合 + メモリ制約)
- **メモリ**: 30-45 GB (各案 10-15 GB × 3 並列)
- **学習時間**: 5 fold × 6 案 = 約 20 時間 (約 1 日)
- **Phase 1 全体期間**: 約 3-4 週 (ラベル設計 1 週 + 実装 1-2 週 + 学習 1 日 + CP2 監査 + 結果分析 1 週)

### 監査経路 (Layer 1 ④ と並行)
- **B-12.10**: MTF 展開方式 4 通り (ffill / 5m rolling / アンカー補間 / 複数特徴量分解) の最適解判定

---

## §5 Layer 2 タスク確定リスト

- **A-2.10**: 第 2 弾 3 候補 (ATR 連動 SL / MFE 比例 / Stale 検知) + 業界カタログ追加 Exit + 部分決済 (scale-out)
- **A-6.9**: MAX_ADDS / per-add 配分 (6 方式並列) + add トリガ条件 ML 学習対象化
- **A-7.12**: 8 サイジング方式比較学習 + K96 系の長時間占有問題対応
- **B-8.9**: cap 方式比較学習 + サイジング連動探索
- **B-11.11**: D-ε との併用 + cluster サンプル偏り対応 (rolling 再学習)
- **B-12.10**: Wavelet 分解
- **B-15.10**: ⑤ Calibration 組み込み
- **D-α.9**: 質と頻度の同時最適化 (Phase 5 評価指標に取引件数・1 件期待値追加)
- **D-δ.9**: 統合フェーズ (時間帯発火分布可視化 + フィルタ候補探索 + 仮 test/本 test 再現性 verify)
- **D-ε.11**: 凍結解除判断 (教師なし ML 系)
- **D-ζ.10**: LONG / SHORT 動的配分

---

## §6 Layer 3 タスク確定リスト (2026-05-22 v5・Layer 配分逆転で縮小)

> ⚠️ **2026-05-22 v5 Layer 配分逆転**: 旧 Layer 3 の B-13.10 / B-14.12 / B-15.10 のうち、**Triple Barrier + Meta-Labeling + Walk-forward Purged K-Fold** は Layer 1 (§4) に前倒し済。Layer 3 残存は以下のみ。

- **B-9.9**: ラベル別 num_leaves / max_depth / min_data_in_leaf の Optuna 探索
- **B-10.11**: 第 1 弾 XGBoost / CatBoost 比較 → 第 2 弾 MiniROCKET → 第 3 弾 MLP / TabNet → 第 4 弾 X2 強化学習 (本番運用後 / Bot 統合)
- **B-11.11**: GMM-HMM / Markov regime switching
- **B-12.10**: MiniROCKET 等で時系列構造変換
- **B-13.10**: ~~Triple Barrier / Meta-Labeling~~ **(Layer 1 v5 へ前倒し済)**・残存タスク = cluster 別独立 quantile の精緻化
- **B-14.12**: ~~Walk-forward Purged K-Fold~~ **(Layer 1 v5 へ前倒し済)**・残存タスク = **CPCV (Combinatorial Purged CV)** + Class balancing / Focal loss / regime-based stratified サンプリング
- **B-15.10**: ~~6 案目的関数並列~~ **(Layer 1 v5 へ前倒し済)**・残存タスク = 前半 SHAP / Conformal prediction / custom loss (直接 PnL / Sharpe / Asymmetric loss) + 後半 高信頼度 only Entry
- **D-ζ.10**: 純 hedge / Delta-neutral 系
- **D-η.9**: 不約定リスクモデル化
- **D-θ.10**: 執行最適化

---

## §7 Phase 7 Bot 統合 / 本番運用後タスク

- **B-10**: X2 強化学習本格検討
- **D-η**: 板情報を Bot 判断に組み込み + 実運用差異モニタリング
- **D-θ**: 発注タイプ選定ロジック実装 + バックテスト vs 実運用差異検証

---

## §8 前提タスク (Layer 1 着手前・必須)

- **cc_ml_design_spec §4 改訂**: 「1 回のサイズ 固定 0.12 BTC」→「合計 0.12 BTC 上限」明文化 (handoff §F-1 矛盾解消・A-7.4)
- **cc_ml_design_spec §4 改訂**: B-8 cap カウント方法明文化 (合算 / 別 / Net exposure のいずれか確定・D-ζ.10)
- **8 指標追加 Phase 0 改修**: build_labels_pct.py 改修 + parquet 再生成 (約 3 時間)

---

## §9 handoff v19 §0.14 Entry 学習問題 5 つへの対応マップ

| Phase 1-a/1-b/1-c 物理証跡 | 構造的問題 | v4 第一弾応答 (Layer 1) | v4 第二弾応答 (Layer 2-3) |
|---|---|---|---|
| top1 = atr14_pct__5m **33-65% dominance** | 方向性 (LONG/SHORT) を学習できない・ボラ予測のみ機能 | **Layer 1 ④ A-1 特徴量空間 1432→2000-2500 列拡張** + **Layer 1 B-11 B 案 (LONG/SHORT 差分追加 cluster)** | Layer 3 B-15 Direction Multiclass / Asymmetric loss・Layer 3 B-10 MiniROCKET (時系列特化) |
| SL hit が TP の **1.78 倍** | 時間順序を学習できない | **Layer 1 ① A-2 trailing 究明 + Exit 採用方式見直し** + **Layer 1 ② B-8 K96 切り捨て** | Layer 3 B-13 Triple Barrier multiclass + Meta-labeling |
| multiclass logloss **entropy lift 6.04%** (実測再計算・計算式 `1 − valid_logloss/ln(3) = 1 − 1.0322/1.0986 = 0.0604`・旧 v4 §9「2.2%」は出所不明の誤記・**2026-05-21 監査 #20 で訂正**) | 直接 Entry 判定が著しく困難 (Lopez de Prado *AFML* Ch.3 推奨閾値: primary model lift < 10% なら meta-labeling 投入域・**6.04% は明確に投入域**) | Layer 1 ④ 特徴量拡張で間接予測の精度を底上げ (副次) + **Layer 1 に Entry Binary Classification + Direction Multiclass 並列追加** (Layer 3 → Layer 1 昇格・監査 #20 反映) | Layer 3 B-15 custom loss + B-13 Meta-labeling (Triple Barrier 2 段階) |
| 全 105k 行学習・実 Entry ~2% (q99 only) | Entry でない 98% が学習支配 (class imbalance) | (Layer 1 では対応せず) | Layer 3 B-14 Class balancing / Focal loss / 負例サブサンプリング |
| 末尾 10% valid のみ | 時系列汎化が verify できていない | (Layer 1 では対応せず) | Layer 3 B-14 Walk-forward + Purged K-fold + CPCV |

### v4 の応答方針 (2026-05-21 監査 #20 で改訂)

**Layer 配分判断の根拠** (CSV §X.10 は教条主義の根拠としない・handoff v19 §0.13 #4 教訓):
- CSV §X.10 は「Layer 1 ① / Layer 3」両論併記 (例: B-13.10) を含む。「§X.10 確定 Layer 3」と扱うのは事実誤認 (旧 v4 §9 記述を 2026-05-21 監査 #20 で訂正)
- 判断軸 = **数値根拠 (entropy lift / TP precision / Direction accuracy / simulated PnL) + 業界基準 (Lopez de Prado *AFML* Ch.3 primary model lift threshold < 10% なら meta-labeling 投入推奨)**

**Layer 1 タスク** (監査 #20 を反映・Entry 学習方法選択肢を Layer 1 並列追加):
- 特徴量空間拡張 (A-1 + A-3 + A-5 + B-12 / 約 2000-2500 列)
- cluster 入力 B 案 (B-11 LONG/SHORT 差分追加・16→20 次元)
- Exit 採用方式見直し (A-2 trailing 究明 + 採用方式複合化)
- 損 combo 切り捨て (B-8 K96 LONG q95-q99)
- 欠落 combo 究明 (B-13.10 K24 q99 + A-4)
- 発火頻度可視化 (D-α)
- **【監査 #20 追加・Layer 3 → Layer 1 昇格】 Entry Binary Classification + Direction Multiclass を 14 ラベル独立 RMSE と Layer 1 並列実装** (handoff v19 §0.14 #4 で CC 自身が出した案・entropy lift 6.04% が Lopez de Prado 投入域・特徴量で改善か・ラベルで改善かを物理証跡で分離検証)

**Layer 1 完了後の判定 (CP2 物理証跡対比)**:
- 「ラベル変更版 (Binary / Direction Multiclass)」と「14 ラベル独立学習版 (RMSE)」を Phase 1 で並列学習
- 比較指標: entropy lift / TP precision / Direction accuracy / simulated PnL
- 「特徴量で改善か・ラベルで改善か・両方か」を物理証跡で分離検証

**Layer 1 完了後 Phase 5 で月次 NET ≥ $1,900 全月クリア達成可能性判定**:
- 達成 → Phase 6 本テスト 2026 Q1
- 未達 → Layer 2 タスクに進む (Calibration / D-δ / D-ε / Exit 第 2 弾)
- それでも未達 → Layer 3 (Triple Barrier multiclass + Meta-labeling 2 段階 + Walk-forward + Purged K-fold + Class balancing + X2 強化学習)
- **Layer 1〜3 のいずれかで合格ラインに届けば本テスト 2026 Q1 へ進行**

---

## §10 v3 → v4 修正履歴

| # | 修正箇所 | v3 | v4 | 根拠 |
|---|---|---|---|---|
| 1 | §0 v4 位置付け | (v3 になし) | CC ML 設計担当移譲後・§X.10 整合再構築 | handoff v18/v19 + cc_role.md §1.5 |
| 2 | §2 23 軸 → 5 学習タスク分解 | (v3 になし) | Web Claude ドラフト構造採用 (T1〜T5 + 依存順序) | Web Claude ドラフト (2026-05-21) |
| 3 | §3 23 軸振り分け表 Layer 担当明示 | (Phase 別優先順位のみ・Layer 担当明示なし) | §X.10 確定 Layer 担当を全 23 軸で明示 | CSV §X.10 全文 view 完了 |
| 4 | §4 Layer 1 タスク確定リスト | (v3 になし・最優先タスク不明示) | Layer 1 ①②③④ + B-11 + 監査経路の全タスク列挙 | CSV §X.10 整理結果 |
| 5 | §9 handoff v19 §0.14 Entry 学習問題対応マップ | (v3 になし) | 物理証跡 3 連続への第一弾 (Layer 1) / 第二弾 (Layer 2-3) 対応分離 | handoff v19 §0.14 + §X.10 整合判断 |
| 6 | A-1 列数見込み | 「1432 + 業界カタログ拡張」 | 「1432 → 約 2000-2500 列」明示 | §A-1.9 |
| 7 | A-2 採用方式 | 「12 種以上」 | 「+ trailing 不採用構造的原因究明 + 採用方式見直し」 | §A-2.10 Layer 1 ① 最優先 |
| 8 | B-8 cap | 「3 方式並列」 | 「+ K96 LONG q95-q99 切り捨て」明示 | §B-8.9 Layer 1 ② 最優先 |
| 9 | B-11 入力 | 「B 案 (LONG/SHORT 差分 4 個追加・16→20 次元)」 | 「+ Layer 1 で B 案最優先・cluster 構造的問題対応」明示 | §B-11.11 Layer 1 |
| 10 | B-12 変換 | 「Fractional diff (d=0.3/0.5) + PCA + Wavelet 追加 + MTF 4 方式」 | (v3 と同じだが Layer 配分明示) | §B-12.10 Layer 1 ④ + 監査経路 |
| 11 | B-13 閾値 | 「rolling + cluster 別 quantile + Triple Barrier (Layer 3)」 | 「+ K24 LONG/SHORT q99 欠落原因究明 (Layer 1 ①)」明示 | §B-13.10 |
| 12 | B-15 目的関数 | 「RMSE + Triple Barrier multiclass + EV フィルタ並列」 | 「+ Layer 2 ⑤ Calibration + Layer 3 前半 SHAP / Conformal / custom loss」明示 | §B-15.10 (audit#16 過小評価指摘) |
| 13 | B-10 アルゴ | 「LightGBM 主軸 + XGBoost / CatBoost 比較・MiniROCKET 不合格時投入」 | 「+ 第 4 弾 X2 強化学習を本格検討対象」明示 | §B-10.7 (audit#16 過小評価指摘・実装回避バイアス対策) |
| 14 | 制約セット | (CC が見落とし) | per-position ≥ 0.000167 BTC + MAX_ADDS × n_sim ≤ 150 + add トリガ TTL 制約 + MAX_ADDS=1 SL なし + per-position × BTC price ≥ 5 USDT を §1 / §3 で明示継承 | exchange_spec.md / v3 制約セット継承 |
| 15 | 削除類型 10 種 | (v3 から継承) | (v3 そのまま継承・変更なし) | learning_design_v3.md §「削除類型 (Phase 5 必須・10 種)」 |
| 16 | 手動 Priority スタートライン到達 verify | (v3 から継承) | (v3 そのまま継承・変更なし) | learning_design_v3.md §「手動 Priority スタートライン到達 verify」 |
| 17 | §9 entropy lift 数値 | 「2.2%」(出所不明の誤記) | **「6.04%」(実測再計算・計算式併記)** | **監査 #20 (2026-05-21) 指摘・false_positive §2 類型 E/G リスク回避・即時訂正** |
| 18 | §9 Layer 配分判断根拠 | 「§X.10 確定 Layer 担当 = Layer 3 に従う」 | 削除・**「CSV §X.10 は両論併記を含む事実・判断軸は数値根拠 + Lopez de Prado AFML Ch.3 閾値」**に変更 | 監査 #20 指摘 (CSV B-13.10 両論併記を事実誤認・handoff v19 §0.13 #4 教条主義再演) |
| 19 | §4 Layer 1 タスク | (RMSE 単独・特徴量拡張 + cluster B 案 + Exit 採用見直し のみ) | **Entry Binary Classification + Direction Multiclass を 14 ラベル独立 RMSE と Layer 1 並列追加** (Layer 3 → Layer 1 昇格) | 監査 #20 指摘 (Lopez de Prado AFML Ch.3 推奨閾値・entropy lift 6.04% は投入域・handoff v19 §0.14 #4 で CC 自身が出した案を Layer 1 化) |
| 20 | §11 着手フロー CP2 | 「Phase 1 再学習・特徴量空間拡張版で物理証跡レビュー」 | **「3 案 (RMSE / Binary / Direction Multiclass) × 特徴量空間拡張版を 4 指標で物理証跡対比 → 分岐判定」** | 監査 #20 (特徴量で改善か・ラベルで改善か・両方かを分離検証する設計) |

---

## §11 着手フロー (Layer 1)

```
[前提タスク・Layer 1 着手前]
  - cc_ml_design_spec §4 改訂 (「1 回」→「合計」+ cap カウント方法明文化)
  - Phase 0 改修 (8 指標 + まこさん発振系 3 件 + 1w/1M MTF + Fractional differentiation + PCA + パラメータ並列展開・1432 → 約 2000-2500 列・約 3-6 時間)
   ↓ CP1 (Phase 0 改修完了・列数 verify + leak 4 点チェック)
[Layer 1 タスク並列・約 3-4 週間 (2026-05-22 v5 Layer 配分逆転・6 案並列 + Walk-forward CV)]
  - Layer 1 ①: A-2 trailing 究明 + A-3 派生特徴量監査 + B-13 K24 q99 欠落究明 + D-α 発火頻度可視化
  - Layer 1 ②: A-4 K96 切り捨て + B-8 K96 LONG 切り捨て + B-13 K96 SHORT 切り捨て
  - Layer 1 ③: A-4 K=6/144/288 追加
  - Layer 1 ④: A-1 特徴量拡張 (前提タスクと統合・約 800-1500 列追加) + A-3 パラメータ並列 (同) + A-5 1w/1M (同) + B-12 Fractional (同)
  - Layer 1 (B-11): B 案 LONG/SHORT 差分追加 + 手法比較
  - **Layer 1 (監査 #20 + v5 Layer 配分逆転): 6 案並列 Phase 1 学習** (約 3-4 週間):
    - 案 a (14 ラベル独立 RMSE・流用)
    - 案 b (Entry Binary Classification)
    - 案 c (Direction Multiclass)
    - **案 d (Ranking LambdaRank・v5 新規)**
    - **案 e (Triple Barrier multiclass・Layer 3 → Layer 1 前倒し・v5)**
    - **案 f (Meta-Labeling 2 段階・案 e 完了後 sequential・v5)**
    - **Walk-forward Purged K-Fold 5 fold** (全案で必須・mlfinlab.cross_validation.PurgedKFold・Layer 3 → Layer 1 前倒し)
    - **3 並列実行** (CPU 競合 + メモリ制約 30-45 GB)・学習時間 約 20 時間 (約 1 日)
   ↓ CP2 (Phase 1 6 案 × Purged K-Fold 5 fold 物理証跡対比・5 指標合格判定 (entropy lift / TP Precision / Direction Accuracy / Simulated PnL / DSR))
   ↓ 分岐判定 (Layer 3 投入条件厳格化・v5):
     ↳ 6 案いずれか上記 5 指標 ALL PASS → 採用案で Phase 2 進行
     ↳ 6 案ベストでも 5 指標未達 → **即** Layer 3 残存タスク投入 (CPCV + Class balancing / Focal loss + custom loss + アルゴ多様化)
     ↳ 「ベスト案で Phase 2 進行して判定」は禁止 (Phase 1 未達 → Phase 2 改善保証なし・v5 厳格化)
[Phase 2-3 (v3 phase_flow §3-4 通り)]
  - Phase 2: B-9 4 指標判定 (合格基準 cc_ml_design_spec §1.6)
  - Phase 3-a / 3-b: cluster 入力 B 案 + KMeans vs GMM vs HDBSCAN 比較
   ↓ CP3 (Phase 3 完了レビュー)
[Phase 4-b (v3 phase_flow §5 通り)]
  - Phase 4-b-1: A-2 Exit 12 種以上 (Layer 1 ① trailing 究明反映)
  - Phase 4-b-2: B-13 rolling + cluster 別 quantile
  - ★ ゲート: Entry-Exit 整合性 review (前回 Phase 5 v3 = -$985 同型再発検知)
   ↓ CP4
[Phase 5 (v3 phase_flow §7 通り)]
  - 5-a〜5-g: A-6 / A-7 / B-8 / D-ζ / Funding / 削除類型 10 種 / D-α per-day ≥ 10 件
  - 合格基準: 仮 test 2025 月次 NET ≥ $1,900 全 12 ヶ月クリア
   ↓ CP5 (Phase 5 結果・本丸合否判定第一段)
[達成判定]
  - 達成 → Phase 6 (本 test 2026 Q1・1 回限り)
  - 未達 → Layer 2 タスクに進む (D-δ / D-ε / Exit 第 2 弾 + Calibration 等)
  - Layer 2 でも未達 → Layer 3 (B-13 Triple Barrier + Meta-labeling / B-14 Walk-forward / B-15 custom loss / B-10 アルゴ多様化 / 不確実性定量化 / X2 強化学習)
```

### CP1-CP5 + Claude 監査モード (`/audit` サブエージェント) による独立検証

**注記**: 本プロジェクトでは ChatGPT 等の外部独立検証は使わない (まこさん課金外)。Claude 監査モード (`/audit` で auditor_template.md ベースのサブエージェント起動・WORKFLOW.md §監査エージェント) を使用する。

**同型バイアス警告 (cc_role.md §1.4 #3 / auditor_template.md L24)**: CC と監査エージェントは同じ Claude 訓練ベースで同型バイアスを共有する可能性あり。それでも CC + まこさんの 2 者で確定するより独立性が増すため、重大判断・前提に関わる判断は監査経路を通す (cc_role.md §1.5 + false_positive_incident_policy §5 関所 D)。

- **CP1 前**: Phase 0 改修着手前に `/audit` (特徴量空間拡張の妥当性・1w/1M MTF 4 方式選定 + Fractional differentiation の本プロジェクト適合性)
- **CP2 前**: Phase 1 再学習着手前に `/audit` (cluster B 案設計妥当性)
- **CP3 前**: Phase 3-b 着手前に `/audit` (KMeans vs GMM vs HDBSCAN の本プロジェクト適合性)
- **CP4 前**: Phase 4-b 着手前に Entry-Exit 整合性 review (前回 Phase 5 v3 = -$985 同型再発検知・`/audit` 経由)
- **CP5 前**: Phase 5 着手前に `/audit` (削除類型 10 種 + per-day ≥ 10 件制約 + サイジング 8 方式の妥当性)

---

## §12 v4 改訂履歴

| Date | Ver | 内容 |
|---|---|---|
| 2026-05-21 | v4 | 初版 (CC ML 設計担当移譲後・23 軸 §X.10 整合再構築・Web Claude ドラフト 5 タスク構造採用・handoff v19 §0.14 Entry 学習問題対応マップ追加・v3 archive 移動完了) |
| 2026-05-21 | v4.1 | **監査 #20 (Claude 監査エージェント) で 3 件懸念指摘 → 5 箇所修正反映**: ① §9 entropy lift 2.2% → 6.04% 訂正 (false_positive §2 類型 E/G リスク回避) / ② §9「§X.10 確定 Layer 担当 = Layer 3 に従う」削除 + CSV 両論併記を事実として明記 (handoff v19 §0.13 #4 教条主義再演回避) / ③ §4 Layer 1 に Entry Binary Classification + Direction Multiclass 並列追加 (Lopez de Prado *AFML* Ch.3 推奨閾値・entropy lift 6.04% は meta-labeling 投入域) / ④ §11 着手フロー CP2 にラベル変更版並列実装 + 分岐判定追加 / ⑤ §10 修正履歴に監査 #20 反映 4 件追加 |
| 2026-05-22 | **v5** | **Layer 配分逆転確定 (まこさん指摘「学習方法が悪い」最終反映・3 案 → 6 案並列)**: ① §3 振り分け表 B-13/B-14/B-15 を Layer 1 前倒し (Triple Barrier + Meta-Labeling + Walk-forward Purged K-Fold + Ranking LambdaRank) / ② §4 Layer 1 タスクに「Layer 配分逆転 v5」セクション追加 (案 d/e/f + Walk-forward CV + Phase 1 合格基準 5 指標数値 + Layer 3 投入条件厳格化 + リソース計画 3 並列 30-45 GB) / ③ §6 Layer 3 タスク縮小 (B-13/B-14/B-15 の Triple Barrier 等を Layer 1 へ移行・残存は CPCV / Class balancing / custom loss / SHAP / Conformal prediction) / ④ §11 着手フロー大幅修正 (6 案並列 + Purged K-Fold 5 fold + CP2 分岐判定厳格化 + Phase 1 期間 2-3 週 → 3-4 週) / ⑤ ナレッジベース v3 §I 閾値設計論 + 3 層併存設計 (連続値 + Adaptive + 自己実現的) を Phase 1 ml 設計と整合 / ⑥ DSR (Deflated Sharpe Ratio・Bailey + Lopez de Prado 2014) 採用 (Phase 4-b/5/6 必須) / ⑦ Triple Barrier ラベル生成は Phase 0 改修指示書 v3.1 で同時実装 (build_labels_pct.py compute_triple_barrier_labels 追加・28 ラベル列追加・合計 56 ラベル列) |

---

## §13 v3 との関係

- **v3 (`archive/learning_design_v3_20260521.md`・174 行)**: 23 軸振り分け表の基盤・本 v4 で §X.10 確定 Layer 担当を明示化した上で継承
- **v3 §「削除類型 10 種」「手動 Priority スタートライン到達 verify」「修正履歴 (v2 → v3)」**: v4 で変更なし・v3 archive ファイル参照
- **v3 §「per-add 配分パターン (6 方式並列)」「add トリガ条件 (D-β-1 統合)」「Phase 別優先順位」**: v4 §3 振り分け表 + §11 着手フローに統合
