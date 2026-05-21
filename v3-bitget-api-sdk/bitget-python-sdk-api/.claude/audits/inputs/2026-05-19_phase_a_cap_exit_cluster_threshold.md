# 【タスク】Phase A: 前回爆死構造的欠陥の解消 (B-8 cap / A-2 Exit / B-11 cluster / A-3 一部)

(まこさん GO 待ち 2026-05-19 / Phase 5 v3 = -$985 全月マイナス爆死の構造的欠陥に対応 / 監査経路提出版)

## 構造化ルール準拠

- 保存先: `.claude/instructions/2026-05-19_phase_a_cap_exit_cluster_threshold.md`
- 完了報告: `.claude/instructions/2026-05-19_phase_a_cap_exit_cluster_threshold_completion.md`
- 本指示書を上記パスに保存し commit すること(対話ルール 19)

## 着手前必読 (省略禁止)

1. `WORKFLOW.md` §🔴 現在のフェーズ / §🔴 次のタスク
2. `CLAUDE.md` §合格ライン定義 / §絶対禁止 / §⛔ 提案禁止リスト
3. `cc_ml_design_spec.md` §1.6 / §1.6.1 / §1.6.2 / §3 / §8
4. `false_positive_incident_policy.md` §0-1 Prime Directive / §0-2 ポジション上限 / §2 類型 A〜H
5. `phase_compliance_checklist.md` 全 Phase 該当箇所
6. `ml_axis_catalog.md` §B-8 / §A-2 / §B-11 / §A-3
7. `handoff_to_web_claude_v9_session_20260518.md` §A-1〜§A-6
8. `lessons_active.md` L-192 / L-189 / L-179 / L-127 / L-159〜L-166
9. `cat_v9_decider.py` (791 行・全文読了必須・grep 部分読み禁止)
10. `cat_params_v9.json` (158 行・全文読了必須)

## Step 0-1: 必読ファイル引用 (読んだフリ防止)

a. `CLAUDE.md` §合格ライン定義 / §絶対禁止 (Prime Directive / 0.12 BTC 上限) 全文貼り付け
b. `cc_ml_design_spec.md` §8 (事前絞り込み禁止) 全文貼り付け
c. `false_positive_incident_policy.md` §0-1 / §0-2 全文貼り付け
d. `handoff v9` §A-3 (手動ロジック構成・Priority 8 種・指標 9 種・Exit 5+ 種) 全文貼り付け
e. `cat_v9_decider.py` の 8 Priority 各 ENABLE フラグ・閾値定数の全列挙
f. `cat_params_v9.json` の Exit 関連パラメータ全列挙 (TP_PCT / SL_PCT / TIME_EXIT_MIN / TRAIL_RATIO / PROFIT_LOCK / MFE_STALE / STOCH_REVERSE_EXIT / SHORT_RSI_EXIT 等)

各引用が期待値と一致しない / 省略 → STOP

---

## 背景

前回 ML pipeline (Phase 1〜5 v3) は Phase 5 月次 NET = -$985 / 全 12 ヶ月マイナスで爆死した。`handoff_to_web_claude_v9_session_20260518.md` §A-4 で爆死要因が数値根拠付きで列挙されている。

監査経路の判定: このやり方では目標達成できない。

対応: あらゆる手段を講じる必要があり、まこさん主導で全トレード手法を列挙・データ化した結果、23 軸の枠組みが出てきた。23 軸の中から目標達成に効きそうなものを段階投入する方針を確定。

Phase A は段階投入の第 1 ラウンド。前回爆死の構造的欠陥のうち、ML 観点で再発防止に必須な 4 軸 (B-8 / A-2 / B-11 / A-3 一部) を直す。

## 大目的 (不変)

月次 NET ≥ $1,900 全 12 ヶ月クリア (仮テスト 2025 + 本テスト 2026 Q1)

## Phase A の目標

Phase A 実行後の Phase 5 月次 NET で:
- 全 12 ヶ月 ≥ $1,900 → Phase 6 (本テスト) へ
- 未達 → Phase B (B-12 / B-13 / A-5) へ進む

## 前提 (動かさない・Phase A スコープ外)

| 項目 | 状態 |
|---|---|
| LightGBM × 16 ラベル | 維持 (K=12/24/48/96 × LONG/SHORT × MFE/MAE) |
| 学習データ範囲 | 維持 (train 2021-04〜2024-12 / valid 末尾 10% / 仮テスト 2025 / 本テスト 2026 Q1) |
| 既存 1432 指標 | 維持 (追加のみ・削減なし) |
| KMeans k=3 | 維持 (手法・k 値は変更しない) |
| 列名規約 `{指標名}_{時間軸}` | 維持 (L-141 再発防止) |
| ポジション上限 0.12 BTC 合計 | 絶対不変 (§0-2 第二絶対規定) |

これらは Phase A のスコープ外。再評価しない。

## 投入軸 4 件 (Phase A の本体)

### 軸 1: B-8 cap 設計

前回問題: cap なし (0.12 BTC 物理制約のみ) → K96 LONG q95-q99 が枠を独占 → no_trade 86.2% (handoff §A-4 事実 10 / ml_axis_catalog L642)

実施:
1. K96 LONG q95-q99 combo を学習対象から切り捨て
2. cap 動的設計を導入: cap=∞ (前回) / cap=3 / cap=5 の 3 案を Phase 5 で比較
3. cap=N の場合、1 ポジサイズ = 0.12 / N BTC (合計上限厳守)
4. 切り捨て後の no_trade 率を Phase 5 で測定

安全装置: 各時刻 t での `sum(active_position_btc) ≤ 0.12` を実装時 assert で verify。Phase 5 完了報告に `max(sum_active_btc)` を実測値で明記 (L-192 再発防止)

### 軸 2: A-2 Exit 設計

前回問題: trailing 0 件採用 (19 combo 中・07_phase4b_exits.csv) / 採用判定が train PnL idxmax 単独 / 既存ルールベース戦略由来 Exit 8 種以上が ML 未学習 (handoff §A-3)

実施:

#### 2-1: trailing 実装 verify
4 仮説のうち実装 bug の可能性を先に潰す:
- 仮説 1: パラメータ範囲が狭すぎる
- 仮説 2: BTC 5m 時系列特性と相性が悪い
- 仮説 3: train PnL idxmax 採用方式が trailing を不当に過小評価
- 仮説 4: trailing 実装に bug

検証手順:
- trailing 関数の入力変数を列挙し、各変数が推論時点 t で因果取得可能か 1 行ずつ宣言 (Prime Directive・§0-1)
- 単一 combo で trailing パラメータを変えて挙動を観察
- bug 検出時は修正 → 検証 → 完了報告

#### 2-2: Exit 候補拡張
既存 3 種 (fixed_tp / trailing / time_exit) に加えて、`cat_v9_decider.py` + `cat_params_v9.json` 由来の 8 種以上を ML 学習対象に追加:
- STOCH_REVERSE_EXIT (P23 由来)
- SHORT_RSI_EXIT (P24 / SHORT 共通由来)
- MFE_STALE_GATE + HOLD_MIN (P1/P2/P3/P21/P22/P23 由来)
- TRAIL_RATIO (P21 由来)
- PROFIT_LOCK_ARM_USD + LOCK_USD (LONG / P22 / P23 由来)
- TP_BB_RATIO + TP_MIN_PCT (P21 由来)
- TIME_EXIT_DOWN_FACTOR (LONG / SHORT / P22 由来)
- TP_ADX_BOOST + ADX_FACTOR (全体共通由来・現在 disable)

各 Exit のパラメータは `cat_params_v9.json` の値を初期値として、Phase 4-b で cluster × K × side ごとに範囲探索。

#### 2-3: 採用判定方式の複合化
train PnL idxmax 単独 → train PnL + Sharpe + test 期間一部 verify の複合判定に変更
- train PnL (前回方式・絶対値)
- train Sharpe (変動の安定性)
- test 期間の一部 (OOS 確認) で逆行していないか
- 複合判定の重み付けは Phase 4-b 内で決定 (CC が範囲探索)

### 軸 3: B-11 cluster 入力ベクトル拡張

前回問題: cluster がボラレベルのみで分類・LONG/SHORT 方向性未分類 (ml_axis_catalog L445-449)

実施:
- 入力ベクトルを 16 次元 (K12/24/48/96 × LONG/SHORT × MFE/MAE) から 20 次元に拡張
- 追加 4 次元 = LONG/SHORT 差分 (K12: LONG_MFE - SHORT_MFE / K24 同 / K48 同 / K96 同)
- StandardScaler + KMeans k=3 維持
- silhouette score / size_ratio ≥ 0.05 縛り維持
- cluster_profile を Phase 4-a 完了時に出力 (cluster ごとの LONG/SHORT 平均値)

判定基準: cluster ごとに「LONG 主体」「SHORT 主体」「両建て主体」に分かれているか (WORKFLOW.md / cc_ml_design_spec §1.5 準拠)

### 軸 4: A-3 既存ルールベース戦略由来の閾値派生特徴量追加

前回問題: 既存ルールベース戦略 (cat_v9_decider.py) の 8 Priority の AND 条件セットが ML 入力に未収録 → ML は手動より狭い学習範囲だった

実施:
- 既存ルールベース戦略の 8 Priority の発火条件をブール特徴量として 1432 に追加
- 約 40 列追加 (P1〜P4 / P21〜P24 の各 AND 条件部分・ENABLE 状態とは無関係に全 Priority 対象)

例 (具体的なフラグ列名):
- `is_p1_macd_golden` (MACD ゴールデンクロス)
- `is_p2_stoch_golden_with_gap` (Stoch GC + ギャップ 0.3 超)
- `is_p3_stoch_golden_strong` (Stoch GC + BB middle slope 強)
- `is_p4_pullback_to_ema_with_trend` (プルバック + EMA タッチ + 順張り)
- `is_p21_macd_dead` (MACD デッドクロス)
- `is_p22_rci_dead_with_bb_touch` (RCI DC + BB 上限タッチ + RCI52 ホット)
- `is_p23_stoch_dead_with_gap` (Stoch DC + ギャップ 0.3 超)
- `is_p24_rsi_overheat_with_stoch` (RSI 過熱 + Stoch 過熱)

各フラグの実装は `cat_v9_decider.py` の `check_entry_priority()` 関数の各 Priority 判定ロジックをそのまま真偽値化する。共通フィルタ (location_prev / entry_risk_score) も同様にフラグ化。

重要: ENABLE フラグ (cat_params_v9.json) は無視。8 Priority 全部のフラグを生成 (運用状態 ≠ 学習範囲・§F-6)。

Prime Directive verify: 各フラグ列の計算が推論時点 t で因果取得可能か 1 行ずつ宣言 (§0-1)。`cat_v9_decider.py` の元実装は推論用なので原則 OK だが、`shift(1)` 等で未来参照していないか確認必須。

## 入力ファイル

| 役割 | パス | 備考 |
|---|---|---|
| OHLCV 5y | `data/BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv` | Phase 0 起点 |
| 1432 指標 train | `results/priority_rebuild/features_train_2021_2024.parquet` (要 verify) | Phase 0 出力 |
| 1432 指標 test | `results/priority_rebuild/features_test2025.parquet` (要 verify) | Phase 0 出力 |
| ラベル train | `results/priority_rebuild/labels_mfe_mae_train_2021_2024.parquet` | 394,753 行 |
| ラベル test | `results/priority_rebuild/labels_mfe_mae_test_2025.parquet` | 105,120 行 |

入力ファイルは sha256 を起動時に assert で照合 (不一致なら sys.exit)。

## Phase A の実行フロー

```
[Step 0] 必読 + 引用 + 既存ファイル sha256 verify
   ↓
[Step 1] 軸 4 (A-3 フラグ化) の特徴量追加実装
   - cat_v9_decider.py を読み込み・8 Priority + 共通フィルタの判定ロジックをフラグ化
   - 各フラグの Prime Directive verify
   - 1432 + 約 40 列 = 約 1472 列
   ↓
[Step 2] Phase 0 ラベル + 特徴量再生成
   - 16 ラベル維持
   - 拡張特徴量で再生成
   ↓
[Step 3] Phase 1 LightGBM 学習 (16 ラベル × 約 1472 列)
   - 完了報告に feature_importance TOP20 必須
   - 追加フラグが TOP20 に入っているか確認
   ↓
[Step 4] Phase 2 精度判定 (既存 4 指標)
   ↓
[Step 5] Phase 4-a クラスタリング (20 次元入力)
   - cluster_profile 出力 (LONG/SHORT 方向性確認)
   ↓
[Step 6] Phase 4-b Exit 再設計
   - 軸 2 の trailing verify + Exit 候補 11 種以上 + 採用判定複合化
   - cluster × K × side × q-band × Exit type の組合せ評価
   ↓
[Step 7] Phase 5 月次 Replay (cap=∞ / cap=3 / cap=5 の 3 案比較)
   - K96 LONG q95-q99 切り捨て後
   - 各 cap 案の月次 NET 全 12 ヶ月評価
```

各 Step の完了時に CC が Web Claude に報告 → Web Claude がレビュー → まこさん確認 (CP1〜CP4) → 次 Step へ。

## 出力 (成果物)

| ファイル | 内容 |
|---|---|
| `results/priority_rebuild/phase_a/feature_flags_audit.md` | Step 1 のフラグ列追加結果・各フラグの Prime Directive verify 結果 |
| `results/priority_rebuild/phase_a/phase1_feature_importance_TOP20.csv` | Step 3 の feature_importance |
| `results/priority_rebuild/phase_a/phase2_4indicators_PHASEA.md` | Step 4 の精度判定結果 |
| `results/priority_rebuild/phase_a/phase4a_cluster_profile_PHASEA.csv` | Step 5 の cluster_profile (LONG/SHORT 方向性) |
| `results/priority_rebuild/phase_a/phase4b_exits_PHASEA.csv` | Step 6 の Exit 採用結果 |
| `results/priority_rebuild/phase_a/phase5_monthly_PHASEA.csv` | Step 7 の月次 PnL (cap=∞ / cap=3 / cap=5 並記) |
| `results/priority_rebuild/phase_a/phase5_summary_PHASEA.md` | Step 7 の総合サマリー |

ファイル名一意化のため全成果物に `_PHASEA` 識別子付与 (WORKFLOW.md ファイル名一意化ルール準拠)。

## 過去不正パターンのガード

### ガード A: §0-1 Prime Directive 違反禁止 (最大級・false_positive §0-1)
- 軸 4 フラグ生成で `cat_v9_decider.py` をそのまま使う場合、未来参照 (`shift(-)` / `j+1` 等) がないか確認
- Phase 5 PnL 計算式の入力変数全列挙・各変数が推論時点 t で因果取得可能か 1 行ずつ宣言

### ガード B: §0-2 ポジション上限 0.12 BTC 違反禁止 (最大級・false_positive §0-2 / L-192)
- 全エントリー時点で `sum(active_position_btc) ≤ 0.12` を実装時 assert
- Phase 5 完了報告に `max(sum_active_btc)` 実測値を必ず明記
- cap=N 時の 1 ポジサイズ = 0.12 / N BTC が実装で守られているか grep verify

### ガード C: leak verify (L-179 / L-128 / L-154)
- 静的 grep: `.shift(-` / `center=True` / `j+1` / `j+2` の不在確認
- 動的 verify: feature_importance TOP20 にブラックリスト列がゼロ件
- 軸 4 フラグ列の計算で `cat_v9_decider.py` の `i` インデックス参照 (`df.at[i-1, ...]` 等) が過去参照のみであることを grep 確認

### ガード D: 異常値スメル (false_positive §5A)
完了報告に必須:
- 勝率 / 月次 NET / IS-OOS Sharpe 比 / 最大 DD
- 異常値検出時は「合格」と書かず「異常値・要調査」と書く

### ガード E: 「読んだフリ」防止 (false_positive §2 類型 G)
- 着手前必読 10 ファイルの機械的証跡 (wc -l + 5 箇所現物引用 + 決定的事実 1 行) を完了報告冒頭に貼る
- 自己申告「読んだ」は信用しない

### ガード F: 絞り込み示唆語彙の自己 grep (L-162)
- 「採用候補」「効く」「重要」「優先」「不要」「使える」等の絞り込み語の grep 結果を完了報告に貼る (no matches 含む)

### ガード G: 暫定値・経験的判断の排除 (memory ルール 10)
- 「暫定で」「経験的に」「定番だから」の語が完了報告にあれば差し戻し
- 全パラメータ・閾値はデータ駆動 (学習データから決定)

## 完了報告必須証跡 (8 点)

1. 着手前必読 10 ファイルの機械的証跡 (wc -l + 5 箇所現物引用 + 決定的事実 1 行)
2. コード総点検 grep 結果 (leak 静的検査 4 種・ガード A〜F の grep)
3. 数値の二重提示 (サマリー + 出典ファイル引用・行番号付き)
4. 成果物ファイル実体 (sha256 + 行数 + 更新時刻)
5. 実行ログ (コマンド・開始/終了時刻・所要時間・終了コード・Python warnings 全件)
6. 絞り込み示唆語彙 自己 grep 結果 (no matches 含む)
7. 異常値スメルテスト結果 (勝率 / 月次 NET / Sharpe / DD の 4 指標)
8. 全工程の未来参照 verify (変数の因果性宣言・Entry / Exit / Replay / PnL)

## CC への注意

- Phase A は Phase 0 → 1 → 2 → 4-a → 4-b → 5 の通し実行。各 Step 完了時に Web Claude に報告 → CP1〜CP4 まこさん確認 → 次 Step
- 実装パラメータ・閾値の細部選択肢提示は不要。データ駆動で決定
- 「採用」「合格」の判断は CC ではなく Web Claude 独立評価 + 監査経路で行う
- 本タスク所要時間の見積もりを Step 0 着手前に Web Claude へ提示 (まこさんの「1 日以内」基準と照合)。1 日超なら Phase 分割を CC が提案

## 安全装置

| 装置 | 中身 |
|---|---|
| ポジション上限 verify | 全 Step で `sum(active_position_btc) ≤ 0.12` 実装時 assert + 完了報告に実測値 |
| leak 検証 4 点 | 静的 grep / データ流入経路 / timestamp range / feature_importance 即時レビュー |
| 異常値スメル STOP | 勝率 70% 超 / 月次 NET $3,800 超 / Sharpe 3 倍乖離 / DD 月次 NET の 10% 未満 → 自動 STOP・「異常値・要調査」 |
| 監査経路 | Phase A 完了時に独立 AI 監査に出す (同型バイアス対策) |
| まこさん確認 CP | Step 3 完了時 CP1+CP3 / Step 5 完了時 CP4 / Step 7 完了時 CP5 |

## 完了後の状態

- Phase A の Phase 5 月次 PnL 全 12 ヶ月の結果が cap=∞ / cap=3 / cap=5 並記で出る
- 各 cap 案で月次 NET ≥ $1,900 全月クリアか判定可能
- 達成 → Phase 6 (本テスト) へ進む判断材料が揃う
- 未達 → Phase B (B-12 / B-13 / A-5) へ進む

## 次のステップ

完了報告受領 → Web Claude が self_check (B) → 監査経路 (独立 AI 監査) → まこさん最終判定:
- 達成 → Phase 6 本テスト指示書
- 未達 → Phase B 発注書 (B-12 Fractional diff / B-13 rolling 窓 / A-5 MTF 拡張)
