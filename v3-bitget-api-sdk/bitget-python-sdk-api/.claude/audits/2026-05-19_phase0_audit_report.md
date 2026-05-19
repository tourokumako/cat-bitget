# Phase 0 Audit Report (着手前監査)

| 項目 | 内容 |
|---|---|
| 作成日 | 2026-05-19 |
| 監査対象 | Phase 0 v3 (ラベル pct 化 + 28 ラベル + メンテ除外 + USD 絶対値 blacklist + leak verify) |
| 監査対象 commit | ea52650 / 6803a60 / 34777ef |
| Phase 0 Step 1-5 完了状態 | ✅ 構造的監査完了 (Step 3d フル実行 = parquet 生成は未着手) |
| 監査者 | CC (Phase 0 実装担当・PM 役務兼務) |
| 関連指示書 | [.claude/instructions/2026-05-19_ml_implementation_phase0_1.md](../instructions/2026-05-19_ml_implementation_phase0_1.md) §3 Step 6 |

---

## §6.1 第二絶対規定 (0.12 BTC 上限) 遵守確認

### 6.1.1 Phase 0 のスコープ

Phase 0 は **ラベル + 特徴量 parquet 生成のみ**。発注ロジック・ポジション保有・add 等を**一切実装しない**。

| 項目 | Phase 0 適用範囲 |
|---|---|
| エントリー判定ロジック | ❌ 実装なし (Phase 5/6 で適用) |
| ポジションサイズ計算 | ❌ 実装なし (Phase 5 A-7 で適用) |
| add ロジック | ❌ 実装なし (Phase 5 A-6 で適用) |
| cap 制御 | ❌ 実装なし (Phase 5 B-8 で適用) |
| sum(active_position_btc) verify | N/A (発注がないため) |

### 6.1.2 grep verify (0.12 BTC 違反コード追加なし)

```
grep -rn "0\.12\s*BTC\|POSITION_BTC\|position_size" \
  v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/build_labels_pct.py \
  v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_vshape_indicators.py \
  v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_regime_label_features.py
```
→ **検出 0 件** (今回作成・編集ファイルに発注関連コードを含めていない)

### 6.1.3 判定

✅ **第二絶対規定遵守**。Phase 0 の責務範囲外でありポジション上限関連の verify は Phase 5 以降に持ち越し。

---

## §6.2 leak verify (未来値使用検出・最重要)

### 6.2.1 shift(-N) 未来参照 grep

| 対象 | 検出箇所 | 判定 |
|---|---|---|
| `build_labels.py` L200-201 | `fut_max_high = h.shift(-K).rolling(K).max()` / `fut_min_low = l.shift(-K).rolling(K).min()` | ✅ **ラベル側** (推論時 X に含めない・L-154 / 命名 `fut_*` で明示) |
| `build_labels_pct.py` L219-220 | 同上 (pct 化版) | ✅ ラベル側 |
| `scripts/regime/` 配下 全 .py | grep 検出 **0 件** | ✅ feature 側 leak なし |
| `headroom_analysis*.py` L50, L315 | `close.shift(-N)` | ⚠️ Phase 5 後の別解析 (Phase 0 ML pipeline スコープ外) |

### 6.2.2 L-128 MA70 ルックアヘッド (resample + 当日含む集計) pattern

| 検証 | 結果 |
|---|---|
| `build_labels_pct.py` `attach_upper_tf` (L142-160) | ✅ `merge_asof(direction="backward")` + 「5m close 時刻 (= 5m start + 5min)」 vs 「上位 TF close 時刻 (= 上位 start + freq)」基準で attach |
| `resample()` 使用の regime 系スクリプト (ml_regime_classifier.py / regime_mom_1h.py / check_*_regime.py / evaluate_regime_rules.py 等) | ✅ **全て regime 凍結対象** (WORKFLOW.md §regime 研究 凍結中) → Phase 0 影響なし |

### 6.2.3 L-179 fractal j±2 未来参照 (2026-05-13 leak)

| 対象 | 構造 | 判定 |
|---|---|---|
| `structure_features.py` `_detect_fractals` (L44-67) | 判定: `h[j] > h[j±1] and h[j] > h[j±2]` (j+1/j+2 を見て中央 j がピークか判定)<br>記録: `is_res[j+2] = True`, `pivot_high[j+2] = h[j]` (j+2 バーに確定情報を記録) | ✅ **確定遅延構造** — 推論時 i バーで `is_res[i]=True` は「i-2 バーがピーク」を意味し、i 時点で既に確定済の過去情報のみ参照 |
| `structure_features.py` `compute_c4_v2_features` L302+ | 同 fractal 検出ロジック・docstring L304「look-ahead 完全防止 (中央バー j で確定する fractal は j ≤ i-2)」 | ✅ L-179 修正済 |

### 6.2.4 window 内ローカル未来 index pattern

| 対象 | 構造 | 判定 |
|---|---|---|
| `shape_features.py` L151 (`w_shape_in_W`) / L167 (`m_shape_in_W`) | `win = l[i-W+1:i+1]` で **過去 W バー** (i 含む) を window 取得・`win[j+1]` は window 内ローカル index (最大 `l[i]` = 現在まで) | ✅ leak なし (window 内ローカル参照) |
| `structure_features.py` L195 (`bin_volume[hi+1]`) | hi は volume bin index (時系列ではない) | ✅ leak なし |
| `structure_features.py` L224-226, L262-263 (`l/h/v[i-N+1:i+1]`) | 過去 N バー window slice | ✅ 過去のみ |

### 6.2.5 center=True rolling (未来参照含む集計)

| 対象 | 結果 |
|---|---|
| 全 feature scripts (scripts/regime/, scripts/priority_rebuild/) | `center=True` 検出 **0 件** ✅ |

### 6.2.6 leak verify 総合判定

| 項目 | 検出 leak | 判定 |
|---|---:|---|
| shift(-N) feature 側 | 0 件 | ✅ |
| L-128 同型再発 | 0 件 | ✅ |
| L-179 同型再発 | 0 件 | ✅ |
| window 内 / volume bin / その他 i+N | 0 件 | ✅ |
| center=True | 0 件 | ✅ |
| **総合** | **0 件** | ✅ **類型 A (look-ahead leak) 完全排除** |

---

## §6.3 本番再現性 7 項目 (Phase 0 適用範囲)

| # | 項目 | Phase 0 での状態 | 実装 |
|---|---|---|---|
| 1 | 最小注文サイズ 0.0001 BTC | Phase 0 適用なし (Phase 5 で適用) | — |
| 2 | 最小注文額 5 USDT | Phase 0 適用なし | — |
| 3 | Tick size 0.1 USDT | Phase 0 適用なし | — |
| 4 | Maker 指値 TTL 3 本 + 同一 side pending 禁止 | Phase 0 適用なし | — |
| 5 | SL 設定 add_count ≥ 2 のみ | Phase 0 適用なし | — |
| 6 | **メンテ時間帯 火/水/木 05-08 UTC** | **Phase 0 Step 2 で実装** | `add_maintenance_flag()` 関数 + `is_maintenance` 列 ([build_labels_pct.py L256-265](../../scripts/priority_rebuild/build_labels_pct.py)) |
| 7 | Maker 剥落 0.02% stress | Phase 5 で適用 | — |

### §6.3 補足: メンテ除外実測値 (dry-run 結果)

```
[dry-run] メンテ時間帯該当 bar (全期間): 28,152 (5.35%)
```

期待値計算: 1826 日 × (3 day/week × 3 hour × 12 bar/h ÷ 7 day/week) = **約 28,100 bar (5.3%)** → 実測 5.35% と一致 ✅

---

## §6.4 価格非依存性 6 項目 (Phase 0 適用範囲)

| # | 項目 | Phase 0 での状態 |
|---|---|---|
| 1 | **ラベル MFE/MAE pct ベース** | ✅ **Phase 0 Step 3 で実装** ([build_labels_pct.py L207-221](../../scripts/priority_rebuild/build_labels_pct.py)・`(fut_max_high - c) / c * 100` 等) |
| 2 | Exit パラメータ % / 比率 / 分単位 | Phase 4-b で適用 |
| 3 | cluster 入力 pct 化 | Phase 3 で適用 |
| 4 | **feature_importance USD 絶対値系 blacklist** | ✅ **Phase 0 Step 4 で実装** (48 feature: sma_*/ichimoku_kijun/tenkan/macd_line/signal/hist/hist_change × 6 TF・Phase 1 学習側で drop) |
| 5 | add トリガ % 表現 | Phase 5 で適用 |
| 6 | TP_FEE_FLOOR BTC 価格動的計算 | Phase 4-b で適用 |

### §6.4 補足: USD 絶対値 → pct 化対応詳細

| 対応 | 件数 | 実装 |
|---|---:|---|
| 旧 USD 絶対値 feature を blacklist (Phase 1 学習対象から除外) | 48 件 | [phase_compliance_checklist.md §Phase -1 blacklist 表](../rules/phase_compliance_checklist.md) |
| 代替 pct feature を新規追加 (代替既存なし分) | 30 件 | `close_vs_tenkan_pct` + `macd_line_pct` + `macd_signal_pct` + `macd_hist_pct` + `macd_hist_change_pct` (×6 TF) |
| 旧 ラベル `LONG_MFE_K{K}` (USD 絶対値) を pct 化 | 16 → 28 | `LONG_MFE_pct_K{K} = (fut_max_high - c) / c * 100` 等 (K_BARS = 7 → 28 ラベル) |
| **Phase 1 学習対象 feature 数** | **1,414** | 1,462 (pct 追加後) - 48 (blacklist drop) |

---

## §6.5 やってるフリ・虚偽報告チェック (類型 G・最重要)

[`false_positive_incident_policy.md`](../rules/false_positive_incident_policy.md) §2 類型 G (虚偽報告) 防止のため、自己申告と実証の境界を明示。

### 6.5.1 必読 14 ファイル読了証跡

機械的証跡 (`wc -l` 出力) は [Step 0 verify](../instructions/2026-05-19_ml_implementation_phase0_1.md) チャット履歴に記載済。

| # | ファイル | wc -l | 読了方法 |
|---|---|---:|---|
| 1 | CLAUDE.md | 239 | system reminder で全文 view |
| 2 | WORKFLOW.md | 781 | Read tool + 関連 section grep |
| 3 | cc_ml_design_spec.md | 351 | Read tool 全文 |
| 4 | phase_compliance_checklist.md | 117 | system reminder で全文 view |
| 5 | exchange_spec.md | 224 | system reminder で全文 view |
| 6 | web_claude_role.md | 431 | system reminder で全文 view |
| 7 | web_claude_self_check.md | 231 | system reminder で全文 view |
| 8 | false_positive_incident_policy.md | 225 | system reminder で全文 view |
| 9 | lessons_active.md (L-117/128/129/139) | 1815 | 該当 L 番号 grep + Read tool 部分 view |
| 10 | indicator_catalogue.md | 1743 | Read tool 構造 view (先頭 50 行) |
| 11 | 10_indicator_families.md | 174 | Read tool 全文 |
| 12 | CAT_指標マトリックス__一覧.csv | (チャット提供) | ユーザーから受領・23 軸構成要素 + 絞り込み戦略確認 |
| 13 | handoff_to_web_claude_v12_session_20260519.md | 256 | 本セッションで作成 |
| 14 | 2026-05-19_role_and_self_check_addendum.md | 270 | Read tool 関連箇所 view |

### 6.5.2 Step 1-5 各実装の物理証跡

| Step | 物理証跡 | 確認方法 |
|---|---|---|
| 1 (期間 verify) | parquet 行数 394,753 / 105,120 / 25,823 期待完全一致 | `python3 pd.read_parquet` で実測 |
| 2 (メンテ除外設計) | 28,152 bar / 5.35% (期待 5.3% と一致) | dry-run 出力 |
| 3a (build_labels_pct.py) | git diff (commit ea52650) | `git log --stat` |
| 3b (旧 parquet archive 移動) | `ls -la archive/` で 3 ファイル確認 | shell |
| 3c (spec/workflow sweep) | git diff (commit ea52650) | grep `labels_mfe_mae_` 残骸 0 件 verify |
| 4 (blacklist + pct 化追加) | dry-run 1432 → 1462 確認 + sample-3d で実数値出力 | python3 dry-run + sample 実行 |
| 5 (leak verify) | grep ログ + Read tool 実装確認 | phase_compliance §Step 5 leak verify 結果 表に全件記載 |

### 6.5.3 leak verify の grep ログ (省略禁止・全件)

[phase_compliance_checklist.md §Step 5 leak verify 結果](../rules/phase_compliance_checklist.md) に grep 対象パターン・検出件数・判定理由を全件記載済。

### 6.5.4 自己申告のみで済ませた箇所

**列挙**:
- ⚠️ Step 6.5.1 必読ファイル #12 `CAT_指標マトリックス__一覧.csv` の読了は **チャット経由受領** (ローカル file なし)・ファイル全文の機械的証跡 (wc -l) は実施不可
  - 緩和策: ユーザー (まこさん) から直接チャットに貼り付けで受領・構造 (23 軸 × 6 カテゴリ + 絞り込み戦略) を確認
  - 残リスク: 「読了」を自己申告で済ませた状態・ローカル sync を別途実施推奨

- 上記以外: **なし** (Step 1-5 全ての verify は機械的証跡 + Read tool + grep / git log で実施)

---

## §6.6 過去 incident との同型 verify

| Incident | 同型再発 | 確認方法 | 結果 |
|---|---|---|---|
| **L-128 MA70 ルックアヘッドバイアス** (2026-04-25) | **無** | Phase 0 Step 5 §6.2.2 grep | ✅ `build_labels_pct.py` の MTF attach は `merge_asof(direction="backward")` で close 時刻基準 |
| **2026-05-13 フラクタル指標 leak** (L-179・j±2 未来参照) | **無** | Phase 0 Step 5 §6.2.3 grep | ✅ `structure_features.py` `_detect_fractals` は j+2 バー記録 (確定遅延) で修正済 |
| **Phase 5 v3 -$985/月 ラベル USD 絶対値依存** (2026-05-19 セッション内) | **対応済** | Phase 0 Step 3 ラベル pct 化 + Step 4 USD 絶対値 blacklist | ✅ pct ラベル 28 + USD 絶対値 feature 48 blacklist + pct 代替 feature 30 追加 |
| **handoff v11 §2.1 MAX_ADDS verify 省略** (2026-05-19 セッション内) | **該当なし** | Phase 0 は MAX_ADDS / cap / per-position 関与なし (Phase 5 で適用) | ✅ Phase 0 スコープ外 |
| **L-183 #13 fit/apply 分離違反** (Phase 4-a 関連) | **該当なし** | Phase 0 は fit/apply 段階以前 (ラベル + 特徴量生成のみ) | ✅ Phase 0 スコープ外 |
| **类型 G 虚偽報告 (読んだフリ等)** | **1 件懸念あり (§6.5.4)** | CSV #12 の機械的証跡なし | ⚠️ チャット経由受領で緩和・ローカル sync 推奨 |

**「未確認」項目**: **0 件**。

---

## §結論: Phase 0 着手判定

### Step 1-5 完了状況

| Step | 内容 | 状態 | commit |
|---|---|---|---|
| 1 | 期間分割 verify (394,753 / 105,120 / 25,823 行) | ✅ | ea52650 |
| 2 | メンテ時間帯除外設計 (火/水/木 05-07 UTC・28,152 bar / 5.35%) | ✅ | ea52650 |
| 3a | `build_labels_pct.py` 新規作成 (pct + 28 ラベル + メンテフラグ) | ✅ | ea52650 / 6803a60 |
| 3b | 旧 USD 絶対値 parquet 3 ファイルを `archive/` 移動 | ✅ | ea52650 |
| 3c | spec/workflow grep sweep (cc_ml_design_spec.md §1.1/§9 + WORKFLOW.md L260/L564-574/L608/L698) | ✅ | ea52650 |
| 4 | USD 絶対値系 48 blacklist + 30 pct 化追加 (1432 → 1462 → drop 48 = 1,414 feature) | ✅ | 6803a60 |
| 5 | leak verify 機械化 (全 6 パターン clear) | ✅ | 34777ef |

### Phase 0 着手判定 (Step 3d フル実行)

✅ **Phase 0 Step 3d (フル実行) 着手可**

**理由**:
- 全 leak verify pass (類型 A 該当 0 件)
- 価格非依存性 #1, #4 適用済 (ラベル pct + USD 絶対値 blacklist + pct 代替追加)
- 本番再現性 #6 (メンテ時間帯除外) 実装済
- 過去 incident 同型再発なし (L-128 / L-179)
- 第二絶対規定遵守 (発注関連実装なし)
- dry-run 1462 完全一致 + sample-3d で実生成 verify 通過

### Step 3d 後追記項目 (`*_completion_phase0.md` で記録)

以下は実行後の実数値を要するため、本 audit report の対象外:
- 期間別 parquet 行数 verify (期待: train 394,753 - 288 / 仮 test 105,120 - 288 / 本 test 25,823 - 288 ※末尾 K=288 drop)
- 全 28 ラベル統計値 (mean / std / min / max) per K × side × MFE/MAE
- メンテ時間帯除外前後行数 (除外 bar 数の実測)
- 期間別 is_maintenance flag count
- 計算結果サンプル (各 K の上位 5 行)
- フル実行所要時間
- 生成 parquet ファイルサイズ

### 残課題 (Phase 1 持ち越し)

| 項目 | 内容 |
|---|---|
| `obv_slope_10b` volume scale | Phase 1 feature_importance top20 に出現したら再確認・取引所成長による分布シフトリスク |

---

## §改訂履歴

| バージョン | 日付 | 内容 |
|---|---|---|
| v1 | 2026-05-19 | 初版 (Step 1-5 完了・Step 3d 着手前監査) |
