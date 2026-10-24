# 【タスク】Phase 0-1 ML 実装 (データ準備 + 学習空間構築 + B-15 並列実装)

保存先: `.claude/instructions/2026-05-19_ml_implementation_phase0_1.md` として保存 + commit (memory ルール 19)
発注: Phase 0 完了報告 → 内部レビュー後 → Phase 1 着手 (段階制御)
タイムライン目安: Phase 0 = 1-2 日 / Phase 1 = 3-5 日

---

## 0. 目的

ML 学習デザイン v3 (2026-05-19 PM-EVE 確定) の Phase 0-1 を実装する。

### Phase 0 = データ準備
- 1432 指標の leak verify + USD 絶対値系の blacklist 適用
- ラベル pct 化 (MFE/MAE を USD 絶対値から pct ベースへ)
- 期間分割 verify (train 2021-04〜2024-12 / 仮 test 2025 / 本 test 2026 Q1)
- 価格非依存性 6 項目 verify (web_claude_self_check.md line 107-114)

### Phase 1 = 学習空間構築 + B-15 並列実装
- A-1 × A-4 × A-5 の組み合わせ展開 (1432 指標 × K={6,12,24,48,96,144,288} × 6 TF)
- B-12 特徴量変換 (Fractional diff + PCA + Wavelet) 並列
- B-14 Walk-forward + Purged K-fold 実装
- **B-15 RMSE + 直接 PnL + Sharpe maximizing custom objective を Phase 1 から並列実装** (v3 確定済 C 案)
- LightGBM baseline 学習・feature_importance top20 計算

### 目標達成への寄与
- Phase 5 v3 (-$985/月) の主因 = ラベル/評価関数のミスマッチ仮説の検証
- B-15 3 系列並列で「どのラベル+評価関数が月次 NET ≥ $1,900 に近づくか」を Phase 5 で並列比較できる土台作り

---

## 1. 必読 (Step 0 前に全文読了・機械的証跡 wc -l + 全文 view 必須)

| # | ファイル | 用途 |
|---|---|---|
| 1 | `/mnt/project/CLAUDE.md` | 目標 / 第二絶対規定 / 提案禁止リスト |
| 2 | `/mnt/project/WORKFLOW.md` | 現フェーズ / 次タスク確認 |
| 3 | `/mnt/project/cc_ml_design_spec.md` | ML pipeline 仕様 / 合否基準 |
| 4 | `/mnt/project/phase_compliance_checklist.md` | Phase 別必須 verify |
| 5 | `/mnt/project/exchange_spec.md` | Bitget 確定値 (本番再現性 7 項目) |
| 6 | `/mnt/project/web_claude_role.md` (431 行・§1.5/§1.6/§1.7) | デザイン責任 / 23 軸存在理由 / 手動 Priority |
| 7 | `/mnt/project/web_claude_self_check.md` (231 行) | チェック A 本番再現性 + 価格非依存性 + 23 軸 First Principles |
| 8 | `/mnt/project/false_positive_incident_policy.md` | 類型 A〜H 全項目 |
| 9 | `/mnt/project/lessons_active.md` | L-117 / L-128 / L-129 / L-139 |
| 10 | `/mnt/project/indicator_catalogue.md` (1744 行) | 1432 指標完全リスト |
| 11 | `/mnt/project/10_indicator_families.md` (174 行) | 145 ファミリー分類 |
| 12 | `/mnt/project/CAT_指標マトリックス__一覧.csv` (1962 行) | 23 軸構成要素 + 絞り込み戦略 |
| 13 | `/mnt/project/handoff_to_web_claude_v8_session_20260516.md` (最新版があれば優先) | 直近セッション引き継ぎ |
| 14 | `.claude/instructions/2026-05-19_role_and_self_check_addendum.md` | 23 軸 First Principles 確定版 |

読了ゲート通過証跡を完了報告冒頭に記載。

---

## 2. Step 0: 前提認識 (Phase 0 着手前・self_check A 通過確認)

完了報告冒頭に以下を 1 行ずつチャットに提示:

### 2.1 本番再現性 7 項目 verify (memory ルール 23 / self_check line 98-106)
1. 最小注文サイズ 0.0001 BTC: 本 Phase は学習のみ・発注ロジックなし → Phase 5 で適用 (Phase 0-1 では設計時記録のみ)
2. 最小注文額 5 USDT: 同上
3. Tick size 0.1 USDT: 同上
4. Maker 指値 TTL 3 本: 同上
5. SL 設定 add_count ≥ 2 のみ: 同上
6. メンテ時間帯 火/水/木 05-08 UTC: バックテスト期間からメンテ時間帯を除外する処理を Phase 0 で実装
7. Maker 剥落 0.02% stress: Phase 5 で適用 (Phase 0-1 では設計時記録のみ)

### 2.2 価格非依存性 6 項目 verify (self_check line 107-114)
1. ラベル MFE/MAE pct ベース: Phase 0 で実装 (USD 絶対値定義を pct 化)
2. Exit パラメータ % / 比率 / 分単位: Phase 4-b で適用 (Phase 0-1 では設計時記録のみ)
3. cluster 入力 pct 化: Phase 3 で適用 (Phase 0-1 では設計時記録のみ)
4. feature_importance USD 絶対値系 blacklist: Phase 0 で適用
5. add トリガ % 表現: Phase 5 で適用
6. TP_FEE_FLOOR BTC 価格動的計算: Phase 4-b で適用

### 2.3 23 軸 First Principles verify (web_claude_role §1.5/§1.6/§1.7)
1. 正本読了機械的証跡: 上記必読リストの wc -l 出力で示す
2. デザイン責任: 本指示書は Web Claude (まこさん経由) のデザイン判断・CC は実装責任のみ
3. 禁止フレーズ: 本指示書本体に手動 Priority への言及なし
4. 23 軸選定完成形: 学習対象 (A-1/A-3/A-4/A-5/B-12/B-14/B-15) を Phase 0-1 で実装・他軸は後 Phase
5. ML 知見根拠: B-15 3 系列並列は cc_ml_design_spec §B-15 + Lopez de Prado "Advances in Financial ML" 準拠
6. 手動 Priority スタートライン: Phase 5 で評価 (Phase 0-1 では設計時記録のみ)

---

## 3. Phase 0 ステップ詳細

### Step 1: 期間分割の verify
- train: 2021-04-01 〜 2024-12-31 (394,753 行・5m)
- 仮 test: 2025-01-01 〜 2025-12-31 (105,120 行)
- 本 test: 2026-01-01 〜 2026-03-31 (25,823 行)
- 各期間の行数を `wc -l` で実数 verify + 完了報告に記載

### Step 2: メンテ時間帯除外処理
- 火曜 05:00-08:00 UTC + 水曜 05:00-08:00 UTC + 木曜 05:00-08:00 UTC の 5m バーを「学習対象外」フラグ
- 除外後行数を完了報告に記載
- 除外せず学習させると「メンテ中の異常価格動 → 学習バイアス」(false_positive 類型 H 隣接)

### Step 3: ラベル pct 化 (重要・価格非依存性 #1)
**旧 (NG)**: `LONG_MFE = max(high[t:t+K]) - close[t]` (USD 絶対値)
**新 (必須)**:
```
LONG_MFE_pct = (max(high[t:t+K]) - close[t]) / close[t] × 100
LONG_MAE_pct = (close[t] - min(low[t:t+K])) / close[t] × 100
SHORT_MFE_pct = (close[t] - min(low[t:t+K])) / close[t] × 100
SHORT_MAE_pct = (max(high[t:t+K]) - close[t]) / close[t] × 100
```

- K = {6, 12, 24, 48, 96, 144, 288} の 7 種類で全部計算 → 28 ラベル (LONG/SHORT × K)
- 計算スクリプト: `regime_research/scripts/compute_labels_pct.py` 新規作成

### Step 4: USD 絶対値系 feature blacklist 適用
**blacklist 対象** (価格非依存性 #4):
- `dist_to_fib_*_pct_*` の中で価格絶対値ベースのもの (実体は pct 表現だが計算上 USD 単位の中間変数を含むものを精査)
- `resistance_distance_pct_*` / `support_distance_pct_*` (同様)
- `nearest_level_distance_pct_*` (同様)
- `nearest_fib_distance_pct_*` / `nearest_fib_v2_distance_pct_*` (同様)

**精査方法**:
- 各 feature の計算スクリプトを grep で確認
- 価格絶対値 (`close` / `high` / `low` の生値) を計算過程に含むかチェック
- 含む場合は blacklist に追加 → `phase_compliance_checklist.md` Phase -1 に記載

**完了報告に提示**: blacklist 適用前後の feature 数 (例: 1432 → 1xxx) + blacklist 詳細リスト

### Step 5: leak verify 機械化 (重要・全工程)
- feature 計算スクリプト全部に対し、未来参照 (`shift(-N)` / `rolling(...).max()` の中身 / 集計の time index 確認) を grep + 静的解析
- レポート: `phase_compliance_checklist.md` Phase -1 に「leak verify チェックリスト」として記載・全 chk 項目を grep ログで証跡
- false_positive 類型 A (look-ahead leak) 該当を完全排除
- L-128 (MA70 ルックアヘッドバイアス) + 2026-05-13 フラクタル指標 leak 教訓を grep 対象に含める

### Step 6: 結果詳細レポート (Phase 0 完了時)

完了報告と別に `phase0_audit_report.md` を提出。内容:

#### 6.1 第二絶対規定 (0.12 BTC 上限) 遵守確認
- Phase 0 は学習のみ・発注ロジックなし → 「発注関連実装なし・Phase 5 で適用」を明記
- Phase 0 で「合計 0.12 BTC 上限」に違反するコード変更を加えていないか grep 結果

#### 6.2 leak verify (未来値使用検出・最重要)
- 全 feature 計算スクリプトの grep ログ (`shift(-`, `rolling(.*).max() at t+`, 集計の time index 越え) 全項目
- L-128 (MA70 ルックアヘッドバイアス) パターン grep 結果
- 2026-05-13 フラクタル指標 leak (未来 2 本参照) パターン grep 結果
- ラベル計算 `LONG_MFE_pct = max(high[t:t+K])` で `t+K` が予測時刻より未来なのは **ラベル側なので OK** (推論時に使わない) → ただし feature 側に同パターンがないか chk
- 検出された全 leak 候補を 1 件ずつ判定 (OK = ラベル側 / NG = feature 側 / NG なら即 STOP)

#### 6.3 本番再現性 7 項目 (Phase 0 適用範囲のみ)
| # | 項目 | Phase 0 での状態 |
|---|---|---|
| 1 | 最小注文サイズ 0.0001 BTC | Phase 0 適用なし (Phase 5 で適用) |
| 2 | 最小注文額 5 USDT | Phase 0 適用なし |
| 3 | Tick size 0.1 USDT | Phase 0 適用なし |
| 4 | Maker 指値 TTL 3 本 | Phase 0 適用なし |
| 5 | SL 設定 add_count ≥ 2 | Phase 0 適用なし |
| 6 | メンテ時間帯 火/水/木 05-08 UTC | **Phase 0 Step 2 で実装** → 除外前後行数を記載 |
| 7 | Maker 剥落 0.02% stress | Phase 5 で適用 |

#### 6.4 価格非依存性 6 項目 (Phase 0 適用範囲)
| # | 項目 | Phase 0 での状態 |
|---|---|---|
| 1 | ラベル MFE/MAE pct ベース | **Phase 0 Step 3 で実装** → 全 28 ラベル統計値 (mean/std/min/max) を記載 |
| 2 | Exit パラメータ % | Phase 4-b で適用 |
| 3 | cluster 入力 pct 化 | Phase 3 で適用 |
| 4 | USD 絶対値系 feature blacklist | **Phase 0 Step 4 で実装** → 適用前後 feature 数 + blacklist リスト全件 |
| 5 | add トリガ % 表現 | Phase 5 で適用 |
| 6 | TP_FEE_FLOOR BTC 価格動的計算 | Phase 4-b で適用 (Phase 1 仮想 PnL では FEE_MARGIN 1.5 適用済) |

#### 6.5 やってるフリ・虚偽報告チェック (類型 G・最重要)
- 必読 14 ファイルの読了証跡: `wc -l` 出力 + 各ファイル末尾 5 行の現物引用
- Step 1-5 各実装の物理証跡: sha256 (修正スクリプト) / git diff (新規スクリプト)
- leak verify の grep ログ: コマンド + 出力全文 (省略禁止)
- 「読了」「実装完了」「verify 通過」を **自己申告のみで済ませた箇所を全件列挙** (なければ「なし」と明記)

#### 6.6 過去 incident との同型 verify
| Incident | 同型再発有無 | 確認方法 |
|---|---|---|
| L-128 MA70 ルックアヘッドバイアス | 有/無 | Phase 0 Step 5 grep 結果で確認 |
| 2026-05-13 フラクタル指標 leak | 有/無 | Phase 0 Step 5 grep 結果で確認 |
| Phase 5 v3 -$985/月 ラベル USD 絶対値依存 | 有/無 | Phase 0 Step 3 ラベル pct 化で対応済 |
| handoff v11 §2.1 MAX_ADDS verify 省略 | 有/無 | Phase 0 は MAX_ADDS 関与なし → 該当なし |

各 incident について「対応済」「該当なし」「未確認」のいずれかを明記。「未確認」が 1 件でもあれば即 STOP。

### Phase 0 完了条件
- [ ] 全 14 ファイル読了ゲート通過 (wc -l + 全文 view 証跡)
- [ ] Step 0 (前提認識 self_check A) 通過証跡
- [ ] train/仮 test/本 test 行数 verify (機械的証跡)
- [ ] メンテ時間帯除外処理実装 + 除外後行数記載
- [ ] ラベル pct 化スクリプト + 計算結果サンプル (各 K 5 行ずつ)
- [ ] USD 絶対値系 feature blacklist リスト + 適用前後 feature 数
- [ ] leak verify レポート (Phase -1 phase_compliance に追記)
- [ ] **結果詳細レポート `phase0_audit_report.md`** (Step 6.1-6.6 全項目)
- [ ] 完了報告 `.claude/instructions/2026-05-19_ml_implementation_phase0_1_completion_phase0.md`

**Phase 0 完了報告後、Web Claude (Phase 1 着手判定) のレビュー → OK で Phase 1 着手**

---

## 4. Phase 1 ステップ詳細

### Step 7: 学習空間構築 (A-1 × A-4 × A-5)
- A-1: 1432 指標 (blacklist 適用後の feature・Phase 0 Step 4 で確定)
- A-4: K={6, 12, 24, 48, 96, 144, 288} → 28 ラベル (LONG/SHORT × 7K)
- A-5: 現行 6 TF (5m/15m/30m/1h/4h/1d) で baseline 学習・1w/1M 追加は Phase 3 で検討

### Step 8: B-12 特徴量変換 並列実装
4 系統並列で feature 拡張・各系統独立に学習:

| # | 系統 | 内容 |
|---|---|---|
| 1 | baseline | 現行 1432 (blacklist 後) のみ |
| 2 | Fractional diff | d={0.3, 0.5} で全 1432 を fractional diff (Lopez de Prado §5 準拠) |
| 3 | PCA | 上位 50 主成分追加 |
| 4 | Wavelet | Daubechies-4 で 5 段分解・係数を特徴量化 |

各系統で feature 数を完了報告に記載。

### Step 9: B-14 サンプリング戦略 実装
- Walk-forward: 6 ヶ月 train → 1 ヶ月 valid を window スライド (train 期間内で 全 44 fold)
- Purged K-fold: K=5・purge=24 bar (Lopez de Prado §7)
- baseline 学習は **Walk-forward の最終 fold** で実施 (= 2024-07〜12 train・2024-12 valid)

### Step 10: B-15 並列実装 (v3 確定済 C 案・重要)
**3 系列を Phase 1 から同時実装**:

#### Series A: RMSE (現行 baseline)
- objective: regression
- metric: rmse
- target: LONG_MFE_pct (K=24 baseline)
- 既存 LightGBM 標準学習

#### Series B: 直接 PnL (NET_PnL_pct)
- objective: custom
- metric: custom
- target: NET_PnL_pct = (理論 PnL - 手数料 - スリッページ - Funding) / close[t] × 100
- 理論 PnL = LONG_MFE_pct × win_prob - LONG_MAE_pct × (1 - win_prob) を K 別に算出
- 手数料 = Maker 0.014% × 2 (Entry + Exit) (FEE_MARGIN 1.5 適用 = 0.021% × 2)
- スリッページ = Maker のため 0 (Taker 不約定モデル化は Phase 7)
- Funding = (K × 5min) / (8h × 60min) × 0.01% (LONG/SHORT 別)
- custom objective: `objective_pnl(y_true, y_pred) → grad/hess`

#### Series C: Sharpe maximizing
- objective: custom
- metric: custom
- target: predicted Sharpe ratio per trade
- custom objective: `objective_sharpe(y_true, y_pred) → grad/hess` (Lopez de Prado §15)

**3 系列の独立 model + 独立 feature_importance を完了報告に記載**

### Step 11: feature_importance 計算 + 価格非依存性最終 verify
- 各 B-15 系列で top20 feature_importance 抽出
- top20 で USD 絶対値系 (Phase 0 blacklist 対象) が再混入していないか verify
- 混入があれば Phase 0 Step 4 に戻り blacklist 再精査

### Step 12: ベースライン month 集計 (Phase 5 評価に向けた土台)
- 各 B-15 系列の予測値で擬似的な月次 PnL を推定 (TP=0.5% / SL=2% / time_exit=K の固定 Exit 仮定)
- 「仮想バックテスト」として 12 ヶ月分の月次 PnL を完了報告に記載 (実 Phase 5 ではなく目安)
- 系列別に「どの目的関数が月次 NET 安定性に近づくか」の初期感触を得る

### Step 13: 結果詳細レポート (Phase 1 完了時)

完了報告と別に `phase1_audit_report.md` を提出。内容:

#### 13.1 第二絶対規定 (0.12 BTC 上限) 遵守確認
- Phase 1 は学習のみ・発注ロジックなし → 「発注関連実装なし・Phase 5 で適用」を明記
- 仮想月次 PnL 推定で「合計 0.12 BTC 上限」を仮定した計算式かどうか明示 (Phase 1 段階では n_sim=1 想定で計算する場合は明記)

#### 13.2 leak verify (未来値使用検出・最重要)
- B-15 3 系列の各 custom objective に未来情報が混入していないか:
  - **Series A (RMSE)**: target が `LONG_MFE_pct[t:t+K]` を **ラベル**として使用 (推論時には使わない) → OK
  - **Series B (直接 PnL)**: 理論 PnL 計算で `win_prob` が train 期間集計値 → train 内集計なら OK / valid 集計を train で使ったら NG (要 verify)
  - **Series C (Sharpe)**: 同様に `Sharpe_per_trade` の集計範囲を verify
- B-12 4 系統で Fractional diff / PCA / Wavelet の計算過程に未来参照がないか grep
- feature_importance top20 全件で「予測時刻 t より未来の値を使う feature」がないか 1 件ずつ判定
- 検出された leak 候補を 1 件ずつ判定 (OK / NG / NG なら即 STOP)

#### 13.3 本番再現性 7 項目 (Phase 1 適用範囲)
| # | 項目 | Phase 1 での状態 |
|---|---|---|
| 1 | 最小注文サイズ 0.0001 BTC | Phase 5 で適用 |
| 2 | 最小注文額 5 USDT | Phase 5 で適用 |
| 3 | Tick size 0.1 USDT | Phase 5 で適用 |
| 4 | Maker 指値 TTL 3 本 | Phase 5 で適用 |
| 5 | SL 設定 add_count ≥ 2 | Phase 5 で適用 |
| 6 | メンテ時間帯除外 | Phase 0 で適用済 (Phase 1 で再 verify) |
| 7 | Maker 剥落 0.02% stress | **Phase 1 仮想月次 PnL で適用** → 0.014% と 0.02% 両方の仮想月次 PnL を提示 |

#### 13.4 価格非依存性 6 項目 (Phase 1 適用範囲)
| # | 項目 | Phase 1 での状態 |
|---|---|---|
| 1 | ラベル MFE/MAE pct ベース | Phase 0 で適用済 (Phase 1 で再 verify) |
| 2 | Exit パラメータ % | Phase 1 仮想バックテスト固定 Exit (TP=0.5% / SL=2%) は **% 表現** → OK |
| 3 | cluster 入力 pct 化 | Phase 3 で適用 (Phase 1 では cluster なし) |
| 4 | **USD 絶対値系 feature blacklist 再混入なし** | feature_importance top20 (3 系列 × 4 B-12 系統 = 12 リスト) 全件で USD 絶対値系混入有無を 1 件ずつ chk |
| 5 | add トリガ % 表現 | Phase 5 で適用 |
| 6 | TP_FEE_FLOOR BTC 価格動的計算 | Phase 4-b で適用 (Phase 1 仮想 PnL では FEE_MARGIN 1.5 適用済) |

#### 13.5 やってるフリ・虚偽報告チェック (類型 G・最重要)
- Step 7-12 各実装の物理証跡: sha256 (新規スクリプト) / git diff
- B-15 3 系列 model の物理ファイル存在確認: `ls -la` + sha256
- feature_importance top20 リスト: csv 出力結果 (3 系列 × 4 B-12 系統 = 12 csv) の sha256 + 抜粋
- 仮想月次 PnL 12 ヶ月推移: csv 出力 (3 系列 × 4 B-12 系統 = 12 csv) の sha256 + 全 12 ヶ月の値
- 「学習完了」を **自己申告のみで済ませた箇所を全件列挙** (なければ「なし」と明記)

#### 13.6 過去 incident との同型 verify
| Incident | 同型再発有無 | 確認方法 |
|---|---|---|
| L-128 MA70 ルックアヘッドバイアス | 有/無 | B-12 Fractional diff / PCA / Wavelet 計算過程 grep |
| 2026-05-13 フラクタル指標 leak | 有/無 | B-12 feature 計算過程 grep |
| L-129 教師あり学習精度上限 | 有/無 | B-15 3 系列の valid_rmse 比較で「Series A (RMSE) が精度上限に達していないか」確認 |
| Phase 5 v3 -$985/月 ラベルミスマッチ | **対応中** | B-15 3 系列並列で「どの系列が月次 NET 安定か」を仮想月次 PnL で初期判定 |
| handoff v11 §2.1 MAX_ADDS verify 省略 | Phase 1 は MAX_ADDS 関与なし | 該当なし |

各 incident について「対応済」「該当なし」「未確認」のいずれかを明記。「未確認」が 1 件でもあれば即 STOP。

#### 13.7 本番再現可能状態の verify
Phase 1 完了時点で「Phase 5 で発注ロジック実装する際の前提条件」が揃っているか:
- ラベル pct 化済 (Phase 5 Exit 設計で使う) → 状態: ✅/❌
- USD 絶対値系 feature blacklist 適用済 → 状態: ✅/❌
- B-15 3 系列の model + feature_importance + 仮想月次 PnL 完備 → 状態: ✅/❌
- leak verify 完了 (Phase 0 + Phase 1 両方) → 状態: ✅/❌
- メンテ時間帯除外実装 → 状態: ✅/❌

全項目 ✅ で初めて Phase 2 着手可。1 項目でも ❌ なら Phase 1 やり直し。

### Phase 1 完了条件
- [ ] Step 7-13 全実装完了
- [ ] B-12 4 系統別 feature 数記載
- [ ] B-15 3 系列 model 学習完了 (train_rmse / valid_rmse / 別 custom metric)
- [ ] feature_importance top20 で USD 絶対値系再混入なし verify
- [ ] 仮想月次 PnL 12 ヶ月推移 (3 系列 × 4 B-12 系統 = 12 csv)
- [ ] **結果詳細レポート `phase1_audit_report.md`** (Step 13.1-13.7 全項目)
- [ ] 完了報告 `.claude/instructions/2026-05-19_ml_implementation_phase0_1_completion_phase1.md`

**Phase 1 完了報告後、Web Claude のレビュー + audit#18 監査経路 → Phase 2 (B-9 Optuna ハイパラ確定) 指示書作成**

---

## 5. ガード (不正・leak・虚偽達成防止)

### 5.1 leak verify (類型 A)
- 全 feature の計算過程に未来参照がないか grep + 静的解析
- L-128 (MA70 ルックアヘッドバイアス) + 2026-05-13 フラクタル指標 leak 教訓
- feature_importance top20 に USD 絶対値系・未来情報依存系がないか verify
- 完了報告で「leak verify チェック済 chk: N/N」(N = 全 chk 項目数) を明記

### 5.2 価格非依存性 (類型 H 隣接・価格絶対値依存禁止)
- ラベル MFE/MAE 必ず pct ベース
- feature_importance top20 USD 絶対値系再混入禁止
- 違反検出時は即 STOP + 再設計

### 5.3 機械的証跡 (類型 G・虚偽報告防止)
- 「読了」「実装完了」「verify 通過」を自己申告のみで済ませない
- 各 Step 完了時に `wc -l` / grep 結果 / 行数比較 / sha256 等の物理証跡を完了報告に提示
- ダッシュボード URL は実 URL を記載 (ダミーやスクリーンショットなしの自己申告は禁止)

### 5.4 メンテ時間帯除外 (類型 H・運用制約遵守)
- 火/水/木 05-08 UTC の bar を学習対象外
- 除外せず学習させると本番再現性違反 (発注スキップ時間帯で取引前提のラベル学習)
- 除外実装スクリプトを完了報告に提示

### 5.5 per-day 発火頻度ライン (L-117)
- B-15 直接 PnL / Sharpe 系列の Entry ratio 閾値設定で per-day ≥ 10 件確保
- 閾値設計は Phase 4-b 詳細・Phase 1 では仮想バックテストで「閾値次第で per-day 件数がどう変動するか」を可視化

---

## 6. 監査マップ

| Step | 監査経路 | タイミング |
|---|---|---|
| Step 5 (leak verify 機械化) | audit#18 (独立評価) | Phase 0 完了報告後 |
| Step 10 (B-15 並列実装) | audit#18 (custom objective 数式 verify) | Phase 1 完了報告後 |
| Step 11 (feature_importance 価格非依存性) | audit#18 (USD 絶対値系混入有無) | Phase 1 完了報告後 |

audit#18 = Web Claude が本セッションで 12 回見落としを起こした事を踏まえ、独立評価を義務化。

---

## 7. 完了報告フォーマット

### Phase 0 完了報告 (`*_completion_phase0.md`)

```
# Phase 0 完了報告

## 読了ゲート
- [必読 14 ファイル全部の wc -l 出力]

## Step 0 (前提認識・self_check A)
- 本番再現性 7 項目: [1 行ずつ]
- 価格非依存性 6 項目: [1 行ずつ]
- 23 軸 First Principles 6 項目: [1 行ずつ]

## Step 1: 期間分割 verify
- train: NNN,NNN 行 (期待 394,753)
- 仮 test: NNN,NNN 行 (期待 105,120)
- 本 test: NN,NNN 行 (期待 25,823)

## Step 2: メンテ時間帯除外
- 除外前: NNN,NNN 行
- 除外後: NNN,NNN 行
- 除外 bar 数: N,NNN
- 実装スクリプト: [パス]

## Step 3: ラベル pct 化
- 計算スクリプト: [パス]
- サンプル (LONG_MFE_pct K=24): [5 行]
- サンプル (LONG_MAE_pct K=24): [5 行]
- 全 28 ラベル分布 統計値 (mean / std / min / max)

## Step 4: USD 絶対値系 blacklist
- blacklist 前 feature 数: 1432
- blacklist 後 feature 数: 1XXX
- 除外 feature 詳細: [リスト全件]

## Step 5: leak verify
- 全 feature の grep 結果: [ログサマリ + 該当箇所詳細]
- 検出された未来参照: [なし or 該当箇所]

## Step 6: 結果詳細レポート
- `phase0_audit_report.md` 提出済 [パス]
- 6.1 第二絶対規定遵守: [結果]
- 6.2 leak verify: [結果]
- 6.3 本番再現性 7 項目: [Phase 0 適用範囲 verify 結果]
- 6.4 価格非依存性 6 項目: [Phase 0 適用範囲 verify 結果]
- 6.5 やってるフリチェック: [自己申告のみ箇所列挙 or 「なし」]
- 6.6 過去 incident 同型 verify: [全項目 OK/該当なし/未確認]

## 次フェーズ着手判定
Web Claude レビュー待ち (Phase 1 Step 7-13 着手)
```

### Phase 1 完了報告 (`*_completion_phase1.md`)
- 同様のフォーマットで Step 7-13 各項目を機械的証跡で記載
- Step 13 (結果詳細レポート) は `phase1_audit_report.md` 別途提出 + 完了報告には 13.1-13.7 各項目の結果サマリ記載

---

## 8. WORKFLOW.md / phase_compliance_checklist.md 更新義務

完了報告と同時に以下を更新:

### WORKFLOW.md
- 現フェーズを「Phase 0」→ 「Phase 1」→ 「Phase 2 待ち」と段階更新
- 次タスクを明示

### phase_compliance_checklist.md
- Phase -1 (Phase 0 着手前 verify) セクション追加
- 価格非依存性 6 項目チェックリスト
- USD 絶対値系 blacklist リスト
- leak verify chk リスト

---

## 9. 実行優先順位 (CC への指示)

1. **必読 14 ファイル全文読了** (省略禁止・wc -l 証跡)
2. Step 0 (self_check A) 完了報告冒頭に提示
3. Phase 0 Step 1-6 順次実装
4. Phase 0 完了報告 + commit
5. **Web Claude レビュー待ち** (CC が自走して Phase 1 着手禁止)
6. Phase 1 着手 OK で Step 7-13 順次実装
7. Phase 1 完了報告 + commit
8. **audit#18 監査経路** 通過待ち

---

## 10. 補足

### Phase 0-1 と他 Phase の関係
- Phase 0-1 = データ + 学習空間 + B-15 並列実装の土台
- Phase 2 = B-9 (Optuna ハイパラ) → Phase 1 結果次第で次回指示書発行
- Phase 3 = B-10 / B-11 (アルゴ + cluster) → Phase 2 結果次第
- Phase 4-b = A-2 / B-13 (Exit + ratio 閾値) → Phase 3 結果次第
- Phase 5 = A-6 / A-7 / B-8 / D-ζ / D-α (ポジ設計) → Phase 4-b 結果次第
- Phase 6-7 = D-δ / D-ε / D-θ (Bot 統合)

### 失敗時の対応
- 仮想月次 PnL の 3 系列いずれも月次 NET ≥ $1,900 に届かない場合 → B-12 4 系統で改善余地ある (Phase 1 内で探索) or Phase 2 Optuna でハイパラ最適化に進む
- leak 検出 → 即 STOP + Phase 0 Step 5 再実行
- USD 絶対値系再混入 → Phase 0 Step 4 blacklist 再精査

「失敗した = 開発中止」ではない (memory ルール 15・救出ヒント探し禁止 + L-50 失敗は学習結果)。
