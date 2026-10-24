# Phase 0 改修指示書 v3.1 — V4 特徴量空間拡張 + Triple Barrier ラベル同時生成 (約 2256-2956 列・5 ファイル同時改修)

(起案者・CC・2026-05-22 / 宛先・CC = 実装担当兼務)
**版**: v3.1 (v3 + Triple Barrier ラベル 28 列追加・Layer 配分逆転 v5 で Phase 1 6 案並列学習を支える · learning_design_v4 v5 + cc_ml_design_spec §1.5.1 整合)
**経緯**: v1 (270 行・破棄) → v2 (459 行) → v3 (507 行・3 層併存・閾値設計論) → v3.1 (Triple Barrier ラベル追加・本版)

## 構造化ルール準拠

- 保存先: `.claude/instructions/2026-05-22_phase0_v4_rebuild_instruction.md`
- 完了報告: `.claude/instructions/2026-05-22_phase0_v4_rebuild_completion.md`
- **本指示書を上記パスに保存し commit すること** (WORKFLOW.md §指示書のファイル保管義務)

> **full フォーマット (約 550 行) を採用**: 新規 verify (Fractional weights leak + K=7 既存維持 grep + 4 ファイル同時改修 verify) + 新規ガード 7 件追加 + CP1 監査経路新設 + ナレッジベース v2 §A-§E 統合 (cc_role §1.5.5 + L-198 整合)。

## v1 → v2 改訂理由 (重大欠落の発覚)

v1 (270 行) は 4 種類の重大欠落で破棄:

1. **メンテフラグ L-181 違反**: build_labels_pct.py L48-50 が「火/水/木 05-08 UTC メンテ」(L-196 で削除済記述) を残存
2. **4 ファイル同時改修ではない**: build_labels_pct.py 単体ではなく `pruned_column_list.json` + `analyze_regime_label_features.py` + `shape_features.py` + `structure_features.py` の 4 ファイル同時改修必要
3. **CSV §A-3.6 A/B/C 案乖離**: CC 即興案 (bool/距離 pct/統合) が正本 (フラグ化/後処理/cluster 入力) と全く別物
4. **業界知見ゼロ**: WebSearch 未実行・cat_v9 grep 未実行・Divergence/SMC/Funding 特徴量化等の業界基礎が全欠落

v2 で全反映 + ナレッジベース v2 (1528 行・WebSearch 42 件 + Gemini 2 件) 統合。

## 読了ゲート通過証跡 (L-200 機械的証跡)

- handoff v21 (301 行) / WORKFLOW.md (500 行) / learning_design_v4.md (336 行) / phase_flow_v4_with_recovery.md (977 行) / cc_ml_design_spec.md (380 行) / cc_role.md (336 行) / false_positive_incident_policy.md (225 行) / phase_compliance_checklist.md (222 行) / auditor_template.md (520 行) / 10_indicator_families.md (174 行) / lessons_active.md (1964 行・直近 300 行重点) ✅
- **technical_analysis_knowledge_base.md (1528 行・本セッションで作成) ✅**
- CAT-指標マトリックス CSV (1962 行): まこさん指示でスキップ + phase_flow_v4 で代替

## 着手前必読 (省略禁止・L-179/L-180/L-181)

1. **`.claude/memory/technical_analysis_knowledge_base.md`** (1528 行・**最重要**) — §A 個別指標 12 件 / §B チャートパターン / §C 高度分析 / §D ML for Trading / §E Phase 0 統合ガイド 20 カテゴリ
2. `WORKFLOW.md` §🔴 現在のフェーズ 改訂18 + Step 0 セッション開始プロトコル
3. `cc_ml_design_spec.md` §1.1 ラベル定義 + §8 制約・禁止事項 (Prime Directive + §0-2)
4. `phase_compliance_checklist.md` §Phase -1 USD 絶対値 blacklist 48 列 + §Phase 0 (0.1〜0.9 + Step 5 leak verify 5.1〜5.6)
5. `phase_flow_v4_with_recovery.md` §2 Phase 0 改修 (L71-135)
6. `learning_design_v4.md` §3 23 軸振り分け表 + §4 Layer 1 ① / ④ + §8 前提タスク
7. `false_positive_incident_policy.md` §0-1 Prime Directive + §0-2 ポジション上限 + §2 類型 A/G/H + §5 関所 A〜G
8. `~/.claude/projects/.../memory/feedback_ml_leak_mandatory_check.md` ML 系作業 leak 4 点必須 (L-179)
9. `results/priority_rebuild/leak_incident_20260513.md` fractal j±2 leak 全 14 件ミス記録

## Step 0-1: 必読ファイル引用 (読んだフリ防止・L-200 類型 G 防止)

着手前に以下をチャットに出力:

a. **`technical_analysis_knowledge_base.md §E.1` Phase 0 改修 20 カテゴリ統合表** を全文引用
b. **`technical_analysis_knowledge_base.md §E.2` 優先順位 (High/Medium/Low)** を全文引用
c. `phase_compliance_checklist.md §Phase -1` USD 絶対値系 blacklist 48 列表 全文引用
d. `phase_compliance_checklist.md §Phase 0` 0.1〜0.9 verify 義務 全文引用
e. `phase_flow_v4_with_recovery.md §2 Phase 0 改修` L71-135 + L110-125 (Phase -1 blacklist) 全文引用
f. `learning_design_v4.md §4 Layer 1 ④` A-1.10 / A-3.9 / A-5.10 / B-12.10 引用 + Layer 1 ① A-3.9 手動閾値派生 引用
g. `cc_ml_design_spec.md §1.1` 14 ラベル独立学習仕様 引用

各引用が省略 / 部分 view → STOP (false_positive §2 類型 G)。

## Step 0-2: 実装 verify (L-180 整合・着手前・4 ファイル全)

```bash
echo "=====Step 0-2 START $(date) ====="

# (1) build_labels_pct.py K_BARS verify
grep -nE "K_BARS|TIMEFRAMES|MAINTENANCE_" scripts/priority_rebuild/build_labels_pct.py | head -20
wc -l scripts/priority_rebuild/build_labels_pct.py

# (2) build_indicators_extended 関数 verify
grep -nE "^def |def build_indicators_extended|def compute_" scripts/regime/analyze_regime_label_features.py | head -20
wc -l scripts/regime/analyze_regime_label_features.py

# (3) shape_features compute_all_features verify
grep -nE "^def |compute_all_features|W_CANDIDATES" scripts/regime/shape_features.py | head -20
wc -l scripts/regime/shape_features.py

# (4) structure_features compute_features_for_N verify (L-179 fractal)
grep -nE "^def |compute_features_for_N|compute_c2_only|_detect_fractals|j\+2" scripts/regime/structure_features.py | head -20
wc -l scripts/regime/structure_features.py

# (5) pruned_column_list.json 既存集合確認
python -c "
import json
spec = json.loads(open('results/regime_label_analysis/pruned_column_list.json').read())
total = sum(len(spec[cat][tf]['all']) for cat in ['1-A','1-B','1-C'] for tf in spec[cat])
print(f'Current total: {total} (expected 1462)')
for cat in ['1-A','1-B','1-C']:
    for tf in spec[cat]:
        print(f'  {cat} {tf}: {len(spec[cat][tf][\"all\"])}')"

# (6) cat_v9 全閾値抽出
python -c "
import json
p = json.loads(open('config/cat_params_v9.json').read())
print(f'cat_v9 params count: {len(p)}')"
```

**期待**:
- `K_BARS = [6, 12, 24, 48, 96, 144, 288]` (K=7 既存実装 ✅)
- `TIMEFRAMES = [\"5m\", \"15m\", \"30m\", \"1h\", \"4h\", \"1d\"]` (6 TF・1w/1M 追加必要)
- `MAINTENANCE_WEEKDAYS = [1, 2, 3]` (L-196 違反残存・削除必要)
- pruned_column_list.json 集合 = 1462
- cat_v9 params count = 約 150 件

確認済事実 (2026-05-22 grep 完了):
- `build_labels_pct.py:94 K_BARS = [6, 12, 24, 48, 96, 144, 288]` (K=7 既存 ✅・改修対象外)
- `build_labels_pct.py:81 TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]` (6 TF・1w/1M 追加対象)
- `build_labels_pct.py:48-50` メンテフラグ「火/水/木 05-08 UTC」**残存** (L-196 違反・削除必要)
- cat/indicators.py L66 `RCI_WINDOWS = [7, 9, 26, 52]` (rci_26 既存・10_indicator_families 未登録疑い)
- cat_v9_decider.py L132-152 `filter_location_passed_long/short` + `filter_riskscore_passed_*` (共通フィルタ 5 bool 列既存)
- cat_v9_decider.py L240-595 P1/P2/P3/P4/P21/P22/P23/P24/P25 発火条件 (約 50 閾値)

---

## §1 タスク目的・成果物

`build_labels_pct.py` + 関連 3 ファイル (`pruned_column_list.json` / `scripts/regime/analyze_regime_label_features.py` / `scripts/regime/shape_features.py` / `scripts/regime/structure_features.py`) を **同時改修** し、特徴量を 1432 列 → **約 2200-2900 列** に拡張。parquet 3 種 (train + 仮 test 2025 + 本 test 2026 Q1) を再生成。

### 改修対象 5 ファイル (4 + JSON 1)

| ファイル | 改修内容 |
|---|---|
| `pruned_column_list.json` | 約 2200-2900 列の集合定義に拡張 |
| `scripts/regime/analyze_regime_label_features.py` | `build_indicators_extended()` に新規 1-A 指標追加 |
| `scripts/regime/shape_features.py` | `compute_all_features()` に新規 1-B 値動きの形 追加 |
| `scripts/regime/structure_features.py` | `compute_features_for_N()` / `compute_c2_only()` に新規 1-C 構造 追加 |
| `scripts/priority_rebuild/build_labels_pct.py` | TIMEFRAMES に 1w/1M 追加 + メンテフラグ削除 (L-196 整合) + 完了報告系 |

### 列数見積 (technical_analysis_knowledge_base v2 §E.1 整合)

| 優先 | 件数 | 列数増加 |
|---|---|---|
| **High** (1-11) | 11 件 | 約 500-900 |
| **Medium** (12-16) | 5 件 | 約 60-150 |
| **Low** (17-20) | 4 件 | 約 100-450 |
| **合計** | **20 件** | **約 800-1500** |

**期待結果**: 1432 + 約 800-1500 特徴量 + 28 既存ラベル + **28 Triple Barrier 新規ラベル** = **約 2316-3016 列** (v3.1 で Triple Barrier 28 列追加)

| 内訳 | 列数 |
|---|---|
| 既存 1432 指標 | 1432 |
| 新規追加特徴量 (§2.1〜§2.3 20 カテゴリ) | 約 800-1500 |
| 既存 28 ラベル列 (MFE/MAE pct × K=7 × LONG/SHORT) | 28 |
| **新規 28 ラベル列 (Triple Barrier + Meta-Labeling・v3.1)** | **28** |
| **合計** | **約 2316-3016 列** |

## §2 追加特徴量カタログ (20 カテゴリ・優先順位付き・ナレッジベース v2 §E.1 反映)

### §2.1 High 優先 (11 件)

| # | カテゴリ | 内容 | 列数 | 由来 |
|---|---|---|---|---|
| 1 | A-1 欠損指標 8 件 | RCI(7) (既存・追加 TF 補完) / RCI(9) (既存) / **RCI(26)** (10_indicator_families 未登録 → 追加) / RCI(52) (既存) / RSI(21) (新規) / RSI_slope (新規) / BB_slope (新規) / Stoch(5m) (新規 TF 補完) | 約 8-48 | ナレッジベース v2 §A.1, §A.5, §A.6, §A.11 |
| 2 | A-1 まこさん発振系 3 件 | RSI ROC (RSI 変化率) / Stoch K-D 差分 / MACD ヒストグラム slope | 約 18 (3 × 6 TF) | ナレッジベース v2 §A.2 (Histogram earlier signal) |
| 3 | A-1 業界カタログ追加 | pandas-ta-classic 212 から **5 系統別** 選定 (Trend 30 + Oscillator 20 + Volatility 15 + Volume 15 + SR 20 = 約 100 件 × 平均 3 TF = 約 300 列) | 約 100-300 | ナレッジベース v2 §7.1, §3.1 系統分類 |
| 4 | A-5 1w/1M MTF 拡張 | 既存 145 ファミリー × {1w, 1M} ffill 結合・shift=1 (確定足・偽シグナル防止) | 約 290 (145 × 2) | ナレッジベース v2 §5.3 shift 設計 |
| 5 | A-5 既存 145 ファミリー TF 欠落補完 | stoch_k (1d のみ → 6 TF) / williams_r (1d のみ) / donchian_position_20 (1h のみ) / bb_pct_b (1d/1h → 6 TF) / close_vs_kijun_pct / momentum_10b / roc_10 / rsi7 / close_vs_sma20_pct / close_vs_vwap20_pct / di_diff / di_minus / di_plus / realized_vol_20b / zscore_return_20b 等 (約 21 ファミリー) | 約 50-100 | ナレッジベース v2 §A.6, §A.12 |
| 6 | B-12 Fractional differentiation | close/high/low/open/volume × d={0.3, 0.5} × 6 TF (mlfinlab Hudson & Thames) | 約 60 (5 × 2 × 6) | ナレッジベース v2 §D.3, §6.2 Ch.5 |
| 7 | B-12 PCA 補助列 | カテゴリ 1-A / 1-B / 1-C 別に PCA n_components=10〜20 | 約 20-50 | ナレッジベース v2 §6.2 |
| 8 | A-3 (a) パラメータ並列展開 | rsi: {21, 28, 42} (新規・**rsi9 + rsi21 推奨** §4.2) / adx: {7, 21} 追加 / bb: window={10, 50} / macd: 短期(5,13,5) + 長期(19,39,9) | 約 30-60 | ナレッジベース v2 §A.1.2, §A.3, §A.5, §A.2.2 |
| 9 | A-3 (b) + D-γ 統合: 手動 Priority bool 列 (CSV §A-3.6 **A 案** 正本準拠) | (a) **共通事前フィルタ 5 bool** (cat_v9 既存・parquet に含めるのみ): filter_location_passed_long/short + filter_riskscore_passed_long/short + filter_riskscore_lower_passed_long  (b) **Priority 別発火条件 bool** (P1/P2/P3/P4/P21/P22/P23/P24/P25 × 各 5-10 AND 条件): 約 45-90 bool 列 (c) **閾値距離 pct**: (現値 - 手動閾値) / 手動閾値 × 約 50 閾値 | 約 50-100 (a+b) + 約 50 (c) = 約 100-150 | ナレッジベース v2 §1.3 + cat_v9 grep 結果 |
| 10 | B-12 MTF 展開方式 4 通り選定 | (i) ffill (現状) / (ii) 5m rolling 再計算 / (iii) アンカー補間 / (iv) 複数特徴量分解 → **CP1 監査で 1 案選定** | 0 (選定のみ) | ナレッジベース v2 §5 + learning_design_v4 §4 ④ 監査経路 |
| 11 | §C.1 **Divergence bool (Regular + Hidden)** | RSI/MACD/Stoch 各々 × Bullish/Bearish × Regular/Hidden = 12 件 × 平均 5 TF = 60 列 (既存 div_macd_14b / div_rsi14_14b 拡張) | 約 30-60 | ナレッジベース v2 §C.1 + §A.1.4/A.2.4/A.6.4 |

### §2.2 Medium 優先 (5 件・3 層併存設計 = 連続値 + Adaptive + 自己実現的)

> **重要**: 本セクション全 bool は ナレッジベース v3 §I.6.2 (3 層併存) 準拠。詳細は §I.1 閾値 4 大分類 + §I.7.1 維持/削除判定 参照。

| # | カテゴリ | (1) 連続値 (LightGBM 自動最適化・主軸) | (2) Adaptive bool (rolling 100-bar 統計) | (3) 自己実現的 bool (維持理由あり) | 列数 |
|---|---|---|---|---|---|
| 12 | §8.1 **Funding rate** | funding_rate_current + median_distance + 8h_change + 24h_mean + 7d_mean + 30d_mean (6 連続値) | funding_extreme_zscore_100b (z > 2 / z < -2・2 bool) | **funding_extreme_p95_bool** (BTC 5m 実測 ✅ audit#19 verify 済) | 約 10-15 |
| 13 | §A.5 **BB Squeeze + Band Walk** | bb_bandwidth_pct (既存) + bb_bw_rolling_p20_100b (連続) + close_vs_bb_upper_dist_pct + close_vs_bb_lower_dist_pct + bb_outside_streak | bb_squeeze_adaptive_p20 (rolling 20th percentile) / band_walk_upper_adaptive (3-bar 連続 0.5% 内) / band_walk_lower_adaptive | bb_squeeze_5pct (**BTC 実用値・10% は削除**) | 約 18-25 |
| 14 | §C.2 **SMC (Order Block + FVG + BOS)** | ob_size_pct / ob_age_bars / dist_to_ob_pct / ob_displacement_pct / fvg_size_pct / fvg_age_bars / dist_to_fvg_pct / dist_to_swing_high_pct / dist_to_swing_low_pct (9 連続値) | ob_displacement_adaptive (displacement > 2×ATR_100b) / fvg_size_adaptive (> 0.5×ATR) | (定番閾値不明・自己実現的 bool なし・Adaptive のみ) | 約 25-50 |
| 15 | §A.4 **Chandelier Exit 距離列** | chandelier_exit_long (Highest High(22) - 3×ATR(22)) / chandelier_exit_short / dist_to_ce_long_pct / dist_to_ce_short_pct × 6 TF | (不要・距離で十分) | (不要) | 約 12 |
| 16 | §A.8 **Fib Extension 距離列** | dist_to_fib_ext_127_pct / dist_to_fib_ext_161_pct / dist_to_fib_ext_261_pct × 6 TF | (不要) | **fib_ext_proximity_bool** (61.8% 同様 self-fulfilling・実装候補) | 約 18-24 |

### §2.3 Low 優先 (4 件・3 層併存設計)

| # | カテゴリ | (1) 連続値 (主軸) | (2) Adaptive bool | (3) 自己実現的 bool | 列数 |
|---|---|---|---|---|---|
| 17 | §C.6 **Supply/Demand Zone** | dist_to_demand_pct / dist_to_supply_pct / zone_age_bars / zone_strength (4 連続値) | demand_active_adaptive / supply_active_adaptive (rolling 100-bar swing 検出ベース) | (定番閾値不明・自己実現的 bool なし) | 約 10-20 |
| 18 | §A.6 **KDJ J 線 + Stoch K-D divergence** | kdj_j_value (連続) + kdj_j_diff + kdj_j_zscore_100b | kdj_j_overbought_z2 / kdj_j_oversold_z-2 | **(110/-10 教科書値は削除・自己実現的根拠ゼロ)** | 約 12-18 |
| 19 | §8.2 **Open Interest** (Bitget API verify 要) | oi_current / oi_24h_change_pct / long_short_ratio | oi_extreme_zscore_100b | (定番なし・Layer 2 候補) | 約 5-10 |
| 20 | §B.1 **Candlestick patterns 62 種** (pandas-ta-classic) | (pattern strength スコア・実体/髭 ratio で連続化候補・要設計) | (pattern 検出は自己実現的閾値前提・Adaptive 化困難) | pattern_detected_bool 62 種・**5m のみで実装** (372 → 62)・Phase 1 で寄与度低なら廃止候補 | 約 62 |

### §2.4 Phase 0 改修対象外明示

| 項目 | 理由 |
|---|---|
| LightGBM 自動分割 (閾値の決定方法) | **Phase 1 学習時**に決まる (Phase 0 改修対象外) |
| 後処理フィルタ (CSV §A-3.6 B 案) | **Phase 4-b-2 or Phase 5** 段階 (Phase 0 改修対象外) |
| Elliott Wave count | 実装難・人手分析中心 |
| Harmonic patterns (XABCD) | 実装難 |
| Wyckoff phase detection | 実装難 |
| Market Profile TPO | 24/7 crypto に直接適用困難・Volume Profile で代替 |
| Anchored VWAP | anchor 自動化が課題 |
| A-4 K=6/144/288 追加 | **既に K=7 実装済** (Step 0-2 grep verify 済) |
| **ADX 25 自己実現的 bool** | **自己実現的根拠薄・削除確定** (Adaptive のみ採用・ナレッジベース v3 §I.7.1) |
| **業界経験閾値 ハードコード** | **データ駆動原則違反** (cc_ml_design_spec §1.2 + §8)・連続値併存必須 |

### §2.5 データ駆動再検討フロー (cc_ml_design_spec §1.2 + §8 + ナレッジベース v3 §I.6.3 整合)

3 層 ((1) 連続値 / (2) Adaptive bool / (3) 自己実現的 bool) を Phase 1 以降で継続評価し、不要層を段階廃止する義務:

| Phase | データ駆動再検討内容 | 廃止判定基準 |
|---|---|---|
| **Phase 1** (学習) | feature_importance top20 で **3 層別効果測定** (Adaptive vs 自己実現的 vs 連続値) | 自己実現的 bool が top50 外なら Phase 4-b で廃止候補化 |
| **Phase 3-b** (cluster) | cluster 入力に **連続値優先**・bool は cluster 分布乖離検証 | cluster 分離度低下なら bool 廃止 |
| **Phase 4-b** (Exit 設計) | cluster 別最適閾値を **DSR (Deflated Sharpe Ratio・ガード H) + walk-forward** でデータ駆動最適化 | Adaptive bool が業界経験 bool より優位 → 業界経験 bool 廃止 |
| **Phase 5** (Replay) | bool 寄与度判定 (採用 vs 廃止)・bool なしで月次 NET 維持 → 正式廃止 | 月次 NET 維持確認で正式廃止 |
| **Phase 6** (本テスト) | 廃止された bool を **再評価せず** (§1.6.1 メタルール) | (実行後緩和禁止) |

### §2.6 列名規約 (3 層併存の判別)

| 層 | 命名規約 | 例 |
|---|---|---|
| (1) 連続値 | `{indicator}_value` / `{indicator}_dist_pct` / `{indicator}_zscore_{N}b` | `rsi_value_14` / `dist_to_fib_618_pct` / `kdj_j_zscore_100b` |
| (2) Adaptive bool | `{indicator}_adaptive_z2` / `_z-2` / `_p90` / `_p10` | `rsi_overbought_adaptive_z2` / `bb_squeeze_adaptive_p20` |
| (3) 自己実現的 bool | `{indicator}_sf_{description}` | `rsi_sf_overbought_70` / `stoch_sf_oversold_20` / `fib_sf_618_proximity` |

→ Phase 1 feature_importance で suffix grep で 3 層別効果測定可能。

## §3 ラベル定義 (K=7 既存維持 + Triple Barrier 28 列新規追加 = 56 ラベル列・v3.1)

### §3.1 既存 28 ラベル列 (K=7 維持・改修対象外)

| # | 軸 | 内容 | verify 義務 |
|---|---|---|---|
| L1 | A-4 K 窓 | K = {6, 12, 24, 48, 96, 144, 288} の **7 期間** 既存維持 (Step 0-2 grep 済) | build_labels_pct.py L94 grep |
| L2 | — | LONG_MFE_pct × K=7 + LONG_MAE_pct × K=7 = **14 ラベル独立** (cc_ml_design_spec §1.1) + 28 ラベル列 (対称性・SHORT 流用は Phase 5 で適用) | parquet schema verify |
| L3 | — | pct ベース定義: `LONG_MFE_pct_K{K} = (max(high[t+1..t+K]) − close[t]) / close[t] × 100` | USD 絶対値定義禁止・grep ヒット → STOP |

### §3.2 Triple Barrier ラベル新規追加 (28 列・v3.1 Layer 配分逆転 v5 対応)

learning_design_v4 v5 §4 Layer 1 案 e (Triple Barrier multiclass) + 案 f (Meta-Labeling 2 段階) のラベル基盤を **Phase 0 で同時生成**:

| # | ラベル名 | 計算 | 用途 |
|---|---|---|---|
| L4 | `triple_barrier_label_LONG_K{K}` × K=7 | K bar 内で **TP/SL/TIME** どれが先に hit するか (Lopez de Prado AFML Ch.3) | 案 e Triple Barrier multiclass primary model 学習 |
| L5 | `triple_barrier_label_SHORT_K{K}` × K=7 | 同上 (SHORT 側) | 同上 |
| L6 | `meta_label_LONG_K{K}` × K=7 | primary model 予測が正解か (TP hit 予測 → 実 TP hit) | 案 f Meta-Labeling secondary model 学習 |
| L7 | `meta_label_SHORT_K{K}` × K=7 | 同上 (SHORT 側) | 同上 |
| **合計** | **28 列追加** | (K=7 × 4 系統) | |

### §3.3 Triple Barrier ラベル計算仕様 (mlfinlab.labeling 経由実装)

```python
# scripts/priority_rebuild/build_labels_pct.py に追加
from mlfinlab.labeling import add_vertical_barrier, get_events, get_bins

def compute_triple_barrier_labels(df5m, K_BARS, atr_col='atr_14_pct'):
    """K=7 期間 × LONG/SHORT の Triple Barrier ラベル生成 (28 列)。
    
    AFML Ch.3 準拠:
    - Upper barrier (TP): close × (1 + 2 × ATR_pct/100)
    - Lower barrier (SL): close × (1 - 2 × ATR_pct/100)
    - Vertical barrier (TIME): K bar 経過
    - ラベル: +1 (TP first) / -1 (SL first) / 0 (TIME first・期限切れ)
    """
    out = pd.DataFrame(index=df5m.index)
    for K in K_BARS:
        for side in ['LONG', 'SHORT']:
            # TP/SL barrier の倍率 (初期固定値・Phase 4-b で Adaptive 化検討)
            pt_sl = [2.0, 2.0]  # TP = 2×ATR / SL = 2×ATR
            # mlfinlab API
            t1 = add_vertical_barrier(df5m.index, df5m['close'], num_days=K*5/1440)  # K bar = K×5 分
            events = get_events(close=df5m['close'], t_events=df5m.index,
                                pt_sl=pt_sl, target=df5m[atr_col]/100,
                                min_ret=0, num_threads=1, vertical_barrier_times=t1, side_prediction=side)
            bins = get_bins(events, df5m['close'])
            out[f'triple_barrier_label_{side}_K{K}'] = bins['bin']  # +1/-1/0
            out[f'meta_label_{side}_K{K}'] = (bins['bin'] == 1).astype(int)  # Meta-Labeling 用
    return out
```

**TP/SL 倍率の根拠 (初期固定値)**: ATR × 2.0 は業界経験閾値だが、ナレッジベース v3 §I.7.3 整合で **Phase 4-b で DSR + walk-forward Adaptive 化** 検討候補 (Phase 0 では固定値で開始)。

**leak verify**: mlfinlab.add_vertical_barrier + get_events は **future-looking** (t 時点以降の price 推移を見て barrier hit 判定) なので **ラベル生成専用** (Phase 1 学習で X に含めない・既存 MFE/MAE pct と同じ扱い・cc_ml_design_spec §8 整合)。

### §3.4 合計ラベル列数

| 既存 (v3) | 新規 (v3.1) | 合計 |
|---|---|---|
| 28 ラベル列 (MFE/MAE pct × K=7 × LONG/SHORT) | **28 ラベル列** (Triple Barrier + Meta-Labeling × K=7 × LONG/SHORT) | **56 ラベル列** |

## §4 価格非依存性義務 (web_claude_self_check §価格非依存性 6 項目)

新規 20 カテゴリ全特徴量 × 6 項目自己 verify (完了報告にチェック表):
1. **ラベル**: USD 絶対値定義禁止・pct ベースのみ
2. **Exit 系特徴量**: % / 比率 / 分単位
3. **cluster 入力候補**: pct 化 (Phase 3-b で normalize_reselect 想定)
4. **feature_importance 上位 USD 絶対値系**: §5 Phase -1 blacklist で drop
5. **add トリガ系特徴量**: % 表現
6. **TP_FEE_FLOOR 系特徴量**: BTC 価格動的計算

## §5 Phase -1 USD 絶対値 blacklist verify (既存 48 列維持)

`phase_compliance_checklist.md §Phase -1` 整合・以下 48 列が Phase 0 改修後の parquet にも存在することを verify:

| ファミリー | 件数 | 状態 |
|---|---|---|
| sma_20 / sma_50 × 6 TF | 12 | 既存・継続 |
| ichimoku_kijun / ichimoku_tenkan × 6 TF | 12 | 既存・継続 |
| macd_line / macd_signal / macd_hist / macd_hist_change × 6 TF | 24 | 既存・継続 |
| **合計** | **48** | 全 drop (Phase 1 学習スクリプト側で実行) |

新規追加 pct 化代替列 (30 列・**既に build_labels_pct.py L13-17 で実装済**):
- `close_vs_tenkan_pct` (6 TF)
- `macd_line_pct` / `macd_signal_pct` / `macd_hist_pct` / `macd_hist_change_pct` (各 6 TF = 24)
- 計 30 列

期待集合: pruned_column_list.json で **1462 + 約 800-1500 = 約 2262-2962 列**。

## §6 実装手順

```
[Step 1] L-196 違反 メンテフラグ削除 (build_labels_pct.py)
  - L48-50 メンテ時間帯フラグ記述削除
  - L103-104 MAINTENANCE_WEEKDAYS / MAINTENANCE_HOURS 削除
  - L228-238 add_maintenance_flag() 削除
  - L234 is_maintenance 列削除 (Phase 1 学習スクリプトが ~df.is_maintenance フィルタしている場合は影響調査)
  - 24/7 取引対応 (L-196 整合)

[Step 2] 4 ファイル同時改修 (新規 20 カテゴリ実装)
  (2.1) scripts/regime/analyze_regime_label_features.py: build_indicators_extended() 拡張
    - §2.1 #1-3 (欠損 + 発振系 + 業界カタログ)
    - §2.1 #5 (TF 欠落補完)
    - §2.1 #8 (パラメータ並列)
    - §2.1 #11 (Divergence bool)
    - §2.2 #13/#15/#16 (BB Squeeze + Chandelier + Fib Ext)
    - §2.3 #18 (KDJ J 線)
  (2.2) scripts/regime/shape_features.py: compute_all_features() 拡張
    - §2.1 #5 一部 (TF 欠落補完)
  (2.3) scripts/regime/structure_features.py: compute_features_for_N() / compute_c2_only() 拡張
    - §2.1 #5 一部 (TF 欠落補完)
    - §2.2 #14 (SMC Order Block + FVG + BOS)
    - §2.3 #17 (Supply/Demand Zone)
    - §2.3 #20 (Candlestick 62 種・5m のみ)
  (2.4) build_labels_pct.py: TIMEFRAMES 拡張 + Triple Barrier ラベル + 関連改修
    - L81 TIMEFRAMES に "1w", "1M" 追加 (6 → 8 TF)
    - L82 RESAMPLE_RULE に "1W", "1ME" 追加
    - L83-89 FREQ_TD に 1w, 1M 追加
    - §2.1 #4 (1w/1M MTF・既存 145 ファミリー × 2 TF)
    - §2.1 #6 (Fractional differentiation・mlfinlab 経由)
    - §2.1 #7 (PCA)
    - §2.1 #9 (cat_v9 共通フィルタ + Priority 別 bool + 閾値距離 pct)
    - §2.2 #12 (Funding rate 特徴量化・要 Funding history fetch)
    - §2.3 #19 (Open Interest・API verify 要)
    - **§3.3 新規: compute_triple_barrier_labels() 実装** (mlfinlab.labeling 経由・28 ラベル列追加)
    - 既存 compute_mfe_mae_labels_pct() の後に triple_barrier_labels も merge して 56 ラベル列 parquet 生成
  (2.5) pruned_column_list.json: 約 2256-2956 列の集合定義に拡張 (特徴量 + 既存ラベル + Triple Barrier ラベル)
  (2.6) **mlfinlab パッケージインストール** (Hudson & Thames): `pip install mlfinlab`
    - 使用モジュール: mlfinlab.features.fracdiff (Fractional Diff) + mlfinlab.labeling (Triple Barrier) + mlfinlab.cross_validation (Purged K-Fold・Phase 1 で使用) + mlfinlab.backtest_statistics (DSR・Phase 4-b で使用)
    - **自前実装禁止** (cc_role §1.0 + ナレッジベース v3 §D.6 整合)

[Step 3] smoke test (3 ヶ月のみ・1 時間以内)
  - 2024-01〜03 で smoke build → 列数 verify (約 2200-2900 範囲)
  - leak 4 点 grep (§7)
  - 期待値外 → STOP・原因究明

[Step 4] CP1 監査依頼 (smoke 結果を Claude /audit に投入・§9)

[Step 5] /audit OK 後・full build
  - train 2021-04〜2024-12 (約 2-4 時間)
  - 仮 test 2025 (約 1 時間)
  - 本 test 2026 Q1 (約 30 分)

[Step 6] 完了報告 (§8 必須証跡 8 点 + L-200 機械的証跡 + CP1 監査結果)
```

## §7 leak 4 点 verify 義務 (L-179 + 新規 #4 Fractional weights)

各 grep コマンドの出力 (no matches 含む) を完了報告に貼る:

```bash
# (1) .shift(-N) 等の未来 index 参照 grep (型 A leak)
grep -nE "\.shift\(-|center=True|j\+1|j\+2|j-1|j-2" scripts/priority_rebuild/build_labels_pct.py scripts/regime/*.py | tee leak_check_1_shift.log
# 期待: build_labels_pct.py L219-224 のラベル側 .shift(-K) のみ・feature 側 0 件

# (2) fractal / pivot の j ≤ i-K フィルタ verify (L-179 同型再発検知)
grep -nE "is_res|is_sup|pivot_high|pivot_low|fractal|_detect_fractals" scripts/regime/structure_features.py | tee leak_check_2_fractal.log
# 期待: structure_features.py の「look-ahead 完全防止 (中央バー j で確定する fractal は j ≤ i-2)」docstring 確認

# (3) train timestamp が test 期間に侵入していないか
python -c "
import pandas as pd
for fp in ['results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet', 'results/priority_rebuild/labels_mfe_mae_pct_test_2025.parquet', 'results/priority_rebuild/labels_mfe_mae_pct_test_2026_q1.parquet']:
    df = pd.read_parquet(fp, columns=['close'])
    print(fp, df.index.min(), df.index.max(), len(df))
"
# 期待: train max < test 2025 min < test 2025 max < test 2026 Q1 min

# (4) Fractional differentiation weights が未来時刻使用なし (新規)
grep -nE "fractional|fracdiff|get_weights|weights_|from mlfinlab" scripts/priority_rebuild/build_labels_pct.py scripts/regime/*.py | tee leak_check_4_fracdiff.log
# 期待: mlfinlab.features.fracdiff の weights[i] が i 時点まで過去観測のみ使用・shift(-N) 等を含まない実装
```

verify FAIL → false_positive §2 類型 A (look-ahead leak) として STOP・修正後再 build。

## §8 完了報告必須証跡 (WORKFLOW.md L53-71 + false_positive §5A/B + L-200)

### 8.1 機械的証跡 8 点 (WORKFLOW.md 既存)

1. **コード総点検 grep 結果** (4 種 grep: TF endswith / TFリスト固定値 / カテゴリ固定値 / 絞り込み処理)
2. **数値の二重提示** (列数サマリー + 出典 parquet schema 引用・行番号付き)
3. **成果物ファイル実体** (parquet 3 種 sha256 + 行数 + 更新時刻・leak_check_*.log 4 件)
4. **実行ログ** (コマンド + 開始/終了時刻 + 所要時間 + 終了コード + Python warnings 全件)
5. **絞り込み示唆語彙 自己 grep 結果** (no matches 含む)
6. **個別組合せ train→test 変化表** (Phase 0 はラベル分布 K 別 quantile train vs test 表)
7. **異常値スメル 4 条件** (列数 < 2200 or > 2900 / ラベル NaN > 5% / fractal blacklist 列残存 / Fractional weights sum > 1.0)
8. **全工程未来参照 verify** (新規 20 カテゴリ全特徴量で「t 時点で因果的に取得可能か」1 行ずつ宣言)

### 8.2 L-200 機械的証跡 3 点 (本指示書冒頭に明示・**最重要**)

1. **`wc -l`** (本指示書 + technical_analysis_knowledge_base.md + 改修後 build_labels_pct.py + 改修後 3 ファイル + 生成 parquet 3 種 schema)
2. **Read ツールで全文 view** (system reminder の部分表示では不可)
3. **該当箇所の現物引用** (1 行以上・新規カテゴリ実装箇所等)

「読んだ」「verify した」「監査済」「確認済」「総点検した」「完了した」と書く時、3 点を同じターン内で必ず出す。証跡なし → 類型 G として CC 自己申告。

### 8.3 追加報告

- 新規 20 カテゴリ別の列数実測内訳 (優先 High/Medium/Low 別)
- §5 Phase -1 blacklist 48 + 既存 pct 30 列が parquet に存在することの schema verify
- CP1 監査依頼書 (§9) と監査結果サマリー
- **§2.4 Phase 0 対象外項目が誤って実装されていないか verify** (LightGBM 自動分割 / 後処理フィルタ / Elliott Wave 等)

## §9 CP1 監査依頼テンプレ (Claude `/audit` 経由・auditor_template 整合)

`/audit` 起動時に渡す情報:

```
監査対象: Phase 0 改修 v2 (build_labels_pct.py + 関連 3 ファイル + pruned_column_list.json 同時改修・1432 → 約 2200-2900 列拡張・smoke 3 ヶ月結果)
対象の型: 混合型 (コード型 + 数値型 + 文書型)
使用観点: ① 統計学的妥当性 / ④ ソフトウェア工学 / ⑥ 実行プロセス / ⑦ 主エージェント作業バイアス
証跡要求: grep 結果 / 行番号 / sha256 / 列数実測 / 逐語引用 (技術文献)

監査依頼内容 (7 項目):
(1) 特徴量空間拡張妥当性 (約 800-1500 列追加・過学習リスク評価・PCA 圧縮率妥当性)
(2) 1w/1M MTF 4 方式選定 (ffill / 5m rolling / アンカー補間 / 複数特徴量分解) の本プロジェクト適合性
(3) Fractional differentiation (d=0.3 / d=0.5) の Lopez de Prado AFML Ch.5 準拠 + leak 不在 (weights 過去のみ)
(4) 業界カタログ追加リストが §A-§D ナレッジベース v2 の整理 (Trend/Oscillator/Volatility/Volume/SR 5 系統) を網羅しているか
(5) §7 leak 4 点 verify 結果の独立確認 (特に新規 #4 Fractional weights)
(6) CC 同型バイアス 27+ 件 (handoff v21 §0.27 + 本セッション 9+ 件) 再演有無 (cc_role §1.4 #2 spec の枠内動作 / #3 同型バイアス / #4 現状把握スキップ)
(7) §5 Phase -1 blacklist 48 + 既存 pct 30 列が parquet schema に存在するか + 新規 20 カテゴリの各列が価格非依存性 6 項目を満たすか

提供成果物:
- smoke 結果 parquet sha256 + 列数 + leak_check_*.log
- 改修前後の 5 ファイル diff
- §2.1-§2.3 新規追加カテゴリリスト + 列数内訳 (優先 High/Medium/Low 別)
- technical_analysis_knowledge_base.md v2 (1528 行) 参照
```

監査結果 OK → §6 Step 5 full build / NG → 監査指摘事項対応 → 再 smoke → 再 /audit。

## §10 失敗時の戻り

| 失敗内容 | 対応 |
|---|---|
| smoke 列数 < 2200 | Low 優先カテゴリ (§2.3 #17-20) 全実装 (1 回まで)・それでも不足なら CC 設計再検討・まこさん協議 |
| smoke 列数 > 2900 | Low 優先カテゴリから優先度低下分を削減 (Candlestick 62 種 5m のみ → 削除候補) |
| leak FAIL (§7 (1)〜(4)) | false_positive §2 類型 A 違反扱い・修正 + 再 smoke + 再 leak verify + 監査再依頼 |
| input CSV `*bitget*` 不含 | ABORT (build_labels_pct.py L72-73 assertion 起動時) |
| K_BARS が K=7 でない | Step 0-2 で発覚 → 過去拡張未反映 → コミット履歴調査 → 復元 |
| メンテフラグ削除で Phase 1 学習スクリプトエラー | Phase 1 スクリプト側の `~df.is_maintenance` フィルタを削除 (同 commit で対応) |
| CP1 監査 NG | 監査指摘事項対応 → 再 smoke → 再 /audit |
| Funding rate API 取得失敗 (§2.2 #12) | history-fund-rate API endpoint verify + 取得 retry + 失敗時は §2.2 #12 を Layer 2 候補に降格 (1 回まで) |
| Open Interest API 取得失敗 (§2.3 #19) | Layer 2 候補に降格 (Bitget API verify 後の判断) |
| full build 中断 (3-6 時間中) | 中断ポイント記録 → 再開時 timestamp 整合性 verify |

## §11 過去不正パターンのガード 7 件 (新規 5 + 既存 2)

### ガード A: §0-1 Prime Directive (false_positive §0-1)

Phase 0 改修で新規追加する全特徴量について、「本番運用の推論時点 t で因果的に取得可能か」を 1 行ずつ宣言:
- 1w/1M MTF: 上位 TF の close 時刻 = bar_start + freq (確定遅延構造・L-128 修正済構造の継承) + **shift=1 (確定足) 強制**
- Fractional differentiation: weights[i] = 過去 i 時点まで観測のみ使用 (§7 #4 で verify)
- PCA: fit は train のみ・apply (transform) は test 適用 (再 fit 禁止・L-183 同型)
- 業界カタログ追加指標: 各指標の計算式が rolling 過去 N bar に閉じている確認
- **Funding rate**: 8h 確定後のみ取得 (リアルタイム 8h 未確定 funding は使用禁止)
- **SMC Order Block / FVG**: bar 確定後の検出 (中央バー検出は j ≤ i-1)
- **Divergence**: swing high/low 確定後の検出 (j ≤ i-2 同様)

宣言なしで実装 → §0-1 違反 (最重大インシデント)。

### ガード B: §0-2 ポジション上限 (false_positive §0-2)

Phase 0 (parquet 生成のみ) では直接適用なし。ただし生成する **新規特徴量が後続 Phase 5 で `sum(active_position_btc) ≤ 0.12` 制約と整合する設計** であることを確認。

### ガード C: L-179 fractal j±2 leak 同型再発検知

§7 #2 grep で `structure_features.py` の fractal 実装が確定遅延構造 (j ≤ i-2) を維持していること verify。新規追加特徴量で fractal 系・swing 系を実装する場合は同じ確定遅延構造を採用・docstring 明記。

### ガード D: L-180 ドキュメント引用前 実装 verify (新規)

learning_design_v4 / phase_flow_v4 / ナレッジベース v2 等の記述を「やる」と書く前に必ず実装 verify。本指示書 Step 0-2 で A-4 K=7 既存実装を発覚させた失敗事例 + メンテフラグ L-181 違反残存事例を反面教師として記載。

実装手順で「§X.X に X と書いてあるから X する」を理由にしない・必ず実装 grep で現状を確認してから着手。

### ガード E: L-181 設計転換時 旧記述 grep sweep (新規・本指示書で発動)

Phase 0 改修 v2 着手時に **L-196 違反 メンテフラグ削除** を実施 (Step 1)。同型違反検知のため:

```bash
# L-196 整合 grep sweep (旧記述検出)
grep -rnE "メンテ|maintenance|定期メンテ|火.{0,3}水.{0,3}木|05.{0,3}08|MAINTENANCE" scripts/ config/ .claude/ | grep -v archive | grep -v lessons | tee l196_grep_sweep.log
# 期待: 削除対象が完了報告で 0 件確認
```

加えて、新規特徴量追加時に **旧来の同名/類似名特徴量が parquet に重複しないこと** を grep verify。

### ガード F: L-200 機械的証跡 3 点 (新規・最重要)

完了報告に以下を必ず含める:
1. `wc -l` 行数 (本指示書 + technical_analysis_knowledge_base.md + 改修後 5 ファイル + 生成 parquet 3 種 schema)
2. Read ツールで全文 view (system reminder の部分表示では不可)
3. 該当箇所の現物引用 (1 行以上)

「読んだ」「verify した」「監査済」「確認済」「総点検した」「完了した」と書く時、3 点を同じターン内で必ず出す。証跡なし → 類型 G として CC 自己申告。

### ガード G: L-194 原則違反では選択肢併置禁止 (新規・該当時のみ)

本指示書実装中に価格非依存性違反 (§4) / leak (§7) / Phase -1 blacklist drop 漏れ (§5) を発見した場合、「(A) 修正する / (B) このまま進める」のような選択肢併置は禁止。原則違反は CC 推奨 1 つ (= 修正) を断言・「逃げ道」を提示しない。

### ガード H: 閾値ハードコード禁止・3 層併存義務 + Deflated Sharpe Ratio (新規・cc_ml_design_spec §1.2 + §8 整合)

**閾値設計義務** (ナレッジベース v3 §I 整合):
- bool ハードコード単独禁止 → **必ず連続値併存** (LightGBM 自動最適化主軸)
- 3 層併存設計: (1) 連続値 + (2) Adaptive bool (rolling 100-bar Z-score/percentile) + (3) 自己実現的 bool (RSI 70/30, Stoch 80/20, Fib 38.2/50/61.8/78.6% のみ維持)
- 業界経験閾値 (BB 10%, KDJ 110/-10, ADX 25 等) → 自己実現的根拠なしなので **削除** (Adaptive のみ採用)
- 列名規約遵守 (§2.6): `_value` / `_zscore_100b` / `_adaptive_z2` / `_sf_overbought_70` 等で 3 層判別

**Deflated Sharpe Ratio (DSR・Bailey + Lopez de Prado 2014・SSRN 2460551)**:
- Phase 4-b 閾値最適化時に **DSR 必須** (Standard Sharpe maximizing 禁止)
- 100+ grid 試行記録義務 (selection bias under multiple testing 補正)
- mlfinlab.backtest_statistics.DSR 経由実装 (自前実装禁止)
- Phase 5 Replay 評価 + Phase 6 本テスト 合格判定でも DSR 採用

**廃止条件**:
- Phase 1: feature_importance で 3 層別効果測定 → 自己実現的 bool が top50 外 → Phase 4-b 廃止候補化
- Phase 5: bool なしで月次 NET 維持 → 正式廃止 (§1.6.1 メタルール準拠)

**違反時の対応**:
- 閾値ハードコード発見 (連続値併存なし) → false_positive §2 類型 不明 (新規類型 I 追加候補) として STOP
- DSR 未採用で「Sharpe X」報告 → 異常値スメル §5 関所 A 同型として再評価義務

---

## CC への注意

- **業界カタログ追加リスト** (§2.1 #3) の具体指標選定は CC が **ナレッジベース v2 §A-§D + WebSearch 結果** をベースにデザイン (cc_role §1.5 デザイン責任)・まこさんに「どの指標で OK か」確認質問しない
- ただし「業界カタログから 100 列追加 vs 300 列追加」のような大幅範囲差は CC 判断後にまこさん最終 GO を待つ
- MTF 4 方式選定 (§2.1 #10) は CP1 監査に委ね・CC 単独確定しない (auditor_template ②③⑥⑦)
- **SMC Python 実装** (§2.2 #14): GitHub joshyattridge/smart-money-concepts を活用 (実装ゼロから書かない)
- **Fractional differentiation** (§2.1 #6): mlfinlab パッケージを活用 (自前実装禁止・Lopez de Prado 推奨)
- **Candlestick 62 種** (§2.3 #20): pandas-ta-classic を活用 (TA-Lib も同等)
- **CC 同型バイアス 27+ 件** (handoff v21 §0.27 + 本セッション 9+ 件) を毎ターン警戒・「23 軸書いてあるから」「Layer 配分通り」を理由にしない (cc_role §1.4 #2)
- **WebSearch / WebFetch を能動活用** (cc_role §1.0 義務・本セッションで 42 件実行済 → ナレッジベース v2 §F.1-§F.8 に集積)

---

## 完了後の状態

- 5 ファイル (build_labels_pct.py + analyze_regime_label_features.py + shape_features.py + structure_features.py + pruned_column_list.json) 同時改修完了 (約 800-1500 列追加実装 + leak 4 点 verify pass + メンテフラグ削除 L-196 整合)
- parquet 3 種再生成 (train + 仮 test 2025 + 本 test 2026 Q1・列数約 2232-2932 + 28 ラベル列保持)
- CP1 監査 PASS (Claude `/audit` 経由独立検証 7 項目)
- Phase 1 並列学習 (案 a RMSE / 案 b Binary / 案 c Multiclass) 着手準備完了
- handoff v22 へ進捗反映 (WORKFLOW.md §🔴 現在のフェーズ 改訂19)
- ナレッジベース v2 §A-§E + §H 今後追加調査候補 を Phase 1〜7 で活用

## 次のステップ

完了報告受領 → CP1 監査結果まこさんレビュー → §3.2 Phase 1 並列学習 3 案着手 (約 1-2 週間 + CP2 分岐判定) → 採用案で Phase 2 進行 or 3 案未達なら Layer 3 投入 (Triple Barrier + Meta-Labeling・ナレッジベース v2 §D.1/§D.2 参照)

---

以上。
