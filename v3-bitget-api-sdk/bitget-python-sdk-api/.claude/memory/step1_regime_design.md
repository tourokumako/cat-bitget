# 工程 1 (相場の状態判定・レジーム判定) 詳細設計書

最終更新: 2026-05-26 (v2.2・議論未経由の細部を削除した整理版)
位置付け: ChatGPT 7 工程フレームの工程 1 の実装設計書。

---

## 0. このファイルの読み方

新セッション CC へ: このファイル + `current_redesign_context.md` (経緯) + `cc_entry_logic_self_study.md` v6 (= 業界知識カタログ・2485 行) の 3 つで工程 1 の議論進捗が分かる。各セクションの説明は専門用語に括弧書きで補足を入れている。

**本ファイル v2.2 で残している内容は 2026-05-25 〜 2026-05-26 のまこさん × CC 議論で OK が出た内容のみ**。議論未経由の細部 (= 実装手順・想定結果例・fold 境界の具体日付・rolling_volatility window 期間等) は §3 に「議論未経由項目リスト」として明示しており、実装着手前にこれらを 1 ステップずつ議論で詰める必要がある。

---

## 1. 工程 1 の目的と位置付け

### 1.1 目的

5 分足の取引 BOT が「今は相場全体としてどういう状態か」を判定する工程。判定結果を工程 3 (Entry の ML 判定) に入力前提として渡すことで、状態ごとに異なる予測モデルや判定基準を使えるようにする。

### 1.2 役割

- 相場全体の状態を 3 種類 (= 上昇 / 下落 / レンジ) で判定
- 方向中立的な判定 (= ロング/ショートの方向別ロジックは工程 2/3 で扱う・工程 1 では扱わない)
- 1 時間ごとに判定を更新
- 工程 3 以降の前提情報として使う

### 1.3 過去フローとの違い (= なぜ新規工程か)

- 過去フロー (`phase_flow_v4_with_recovery.md` v7) には工程 1 が存在しなかった
- Phase 1 v6 で 6 案全滅した構造的原因として「regime context を入力に入れていない」が判明 (= L-223)
- ChatGPT 7 工程フレームに切り替えて工程 1 を最上流に新設

---

## 2. 議論で OK が出ている確定事項

### 2.1 学習構造

| 項目 | 確定内容 |
|---|---|
| 判定間隔 | 1 時間ごと |
| 切替の慣性 (= ヒステリシス) | 連続 2 回同じ判定で切替 (= 2 時間相当) |
| 分類数 | 3 種類 (= 上昇 / 下落 / レンジ) |
| アルゴリズム | HMM (Hidden Markov Model・隠れマルコフモデル) 教師なし学習 |
| 学習データ期間 | 2021-04 〜 2024-12 (= Phase 0 v3.1 train 期間) |

### 2.2 入力特徴量 (= 14 指標 × 6 時間軸 = 84 次元)

| カテゴリ | 指標 base 名 | 数 |
|---|---|---|
| ベース (= 業界 default・必須) | log_returns, rolling_volatility | 2 |
| トレンド・方向性 | adx14, di_plus, di_minus | 3 |
| 移動平均線 | close_vs_sma20_pct, close_vs_sma50_pct, close_vs_ema200_pct | 3 |
| 一目均衡表 | close_vs_tenkan_pct, close_vs_kijun_pct | 2 |
| モメンタム | rsi14, macd_hist_pct | 2 |
| ボラティリティ | atr14_pct, bb_width_pct | 2 |

時間軸: `5m / 15m / 30m / 1h / 4h / 1d` の 6 個。

業界実証: Preprints 202603.0831 (BTC HMM 3 状態研究 2024-2026)・QuantInsti (regime adaptive trading)・PickMyTrade 2026 等で「log returns + rolling volatility + 主要テクニカル指標」が業界 default 構成。

### 2.3 指標計算パラメータ (= 業界標準・Wilder / Bollinger 原典)

| 指標 | パラメータ | 値 | 根拠 |
|---|---|---|---|
| ADX | period | 14 | Wilder 原典 |
| DI+ / DI- | period | 14 | ADX とセット |
| RSI | period | 14 | Wilder 原典 |
| MACD | fast / slow / signal | 12 / 26 / 9 | Gerald Appel 原典 |
| ATR | period | 14 | Wilder 原典 |
| Bollinger Band | period / 標準偏差倍率 | 20 / 2.0 | John Bollinger 原典 |
| SMA20 / SMA50 / EMA200 | period | 20 / 50 / 200 | 業界標準 |

### 2.4 HMM ハイパーパラメータ

| パラメータ | 値 | 役割 |
|---|---|---|
| n_components | 3 | 状態数 (= 上昇 / 下落 / レンジ) |
| covariance_type | **'diag'** | 共分散行列の型 (= 各特徴量を独立として扱う・hmmlearn の業界 default)・過学習防止のため full から変更 (= 2026-05-26・サンプル数/パラメータ数比 1.7 倍 → 約 140 倍に改善)。Phase 5 Replay 結果で diag が不足と判明したら full に戻す可逆性あり |
| n_iter | 100 | Baum-Welch (= EM) の反復回数上限 |
| tol | 0.01 | 尤度の改善幅がこの値以下なら学習終了 |
| random_state | 42 | 乱数シード固定 (= 再現性確保) |

### 2.5 前処理

- スケーリング: RobustScaler (= 外れ値に強い・中央値と IQR ベース) を Pipeline で fold 毎 fit (= data leak 防止)
- NaN 処理:
  - **学習時**: drop (= 上位足の最初の数百サンプル削除・全体の約 5%)
  - **本番運用時**: Phase 0 v3.1 の ffill 処理に依存 (= 新規実装不要)
- 理由: hmmlearn (= HMM ライブラリ) は NaN を扱えないため

### 2.6 評価方法 (= Walk-Forward + Purged K-Fold)

| パラメータ | 値 | 役割 |
|---|---|---|
| fold 数 | 5 | train 4 年を 5 等分 |
| purge 期間 | 24 時間 (= 24 サンプル) | fold 境界の overlap 防止 |
| embargo 期間 | 24 時間 (= 24 サンプル) | train 終了 → test 開始の空白期間 |

評価指標 (= 統計指標のみ・PnL 評価は工程 3-5 通した Phase 5 Replay で別途):
- HMM の log-likelihood (= データへの当てはまり)
- 状態の安定性 (= 切替頻度・連続滞留時間)
- 機械的命名 + 視認チェックの一致率

実装ライブラリ: `mlfinpy.cross_validation.PurgedKFold` (= 業界標準・Lopez de Prado AFML 整合)

### 2.7 状態ラベル付け

- **機械的ルール**: 1 時間足 (= 1h time frame) の DI 差 (= DI+ - DI-) の中央値で命名
  - 最大の状態 → 「上昇」
  - 最小の状態 → 「下落」
  - 残りの状態 → 「レンジ」
- **中央値の計算範囲**: train データ全体 (= fold ごとではない)
- **妥当性チェック**: レンジに分類された状態の ADX 平均が他 2 状態より低いこと (= トレンドが弱いこと) を verify

### 2.8 本番運用時の推論

- **方式**: オンライン Viterbi
- **スライディング窓**: 100 時間 (= 約 4 日分・業界相場の中央値)
- **使用 API** (= hmmlearn ライブラリ):
  - `model.predict(window)` で状態 (= 整数 0/1/2) 取得 → ヒステリシス判定の入力
  - `model.predict_proba(window)` で各状態の確率取得 → 工程 3 への入力 (= ソフトな確度情報)

### 2.9 入力ベクトルの並び順

カテゴリ → 指標 → 時間軸の順で並べる:

- [ベース系] log_returns × 6 時間軸 / rolling_volatility × 6 時間軸 (= 12 列)
- [トレンド系・方向性] adx14 × 6 / di_plus × 6 / di_minus × 6 (= 18 列)
- [トレンド系・移動平均] close_vs_sma20_pct × 6 / close_vs_sma50_pct × 6 / close_vs_ema200_pct × 6 (= 18 列)
- [トレンド系・一目均衡表] close_vs_tenkan_pct × 6 / close_vs_kijun_pct × 6 (= 12 列)
- [モメンタム系] rsi14 × 6 / macd_hist_pct × 6 (= 12 列)
- [ボラティリティ系] atr14_pct × 6 / bb_width_pct × 6 (= 12 列)

合計 84 列。

### 2.10 artifact 保存形式・命名規則

| ファイル | 形式 | 命名 |
|---|---|---|
| HMM モデル | joblib | `hmm_train_2021_2024.joblib` |
| Scaler (RobustScaler) | joblib | `scaler_train_2021_2024.joblib` |
| 状態ラベル付け結果 | JSON | `state_labels_train_2021_2024.json` |
| 学習サマリ | JSON | `hmm_summary_train_2021_2024.json` |

- 保存先: `results/regime_step1/`
- 命名規則: phase_compliance_checklist §4a.4 整合 (= "test" 文字列禁止・"train" 含む)

### 2.11 ライブラリバージョン

- 既存 `.venv311` 環境を継承 (= Python 3.11)
- 既存ライブラリ: sklearn / pandas / numpy / mlfinpy / joblib / scipy
- 新規インストール: **hmmlearn 0.3.x** (= 業界標準安定版)
- 実装着手時に `.venv311/bin/pip freeze > requirements_step1.txt` でバージョンを記録

### 2.12 ベース指標の新規生成が必要 (= まこさん 2026-05-25 OK・実装上の対応)

§2.2 の 14 指標のうち:

- **12 指標 (= 既存・再利用)**: adx14 / di_plus / di_minus / close_vs_sma20_pct / close_vs_sma50_pct / close_vs_ema200_pct / close_vs_tenkan_pct / close_vs_kijun_pct / rsi14 / macd_hist_pct / atr14_pct / bb_width_pct → Phase 0 v3.1 既存 parquet から抽出
- **2 指標 (= 新規生成が必要)**: log_returns / rolling_volatility → Phase 0 v3.1 に存在しないため新規生成 (= 業界 default 必須として採用)
  - log_returns: `ln(close_t / close_{t-1})` (= 対数リターン・1 期間)
  - rolling_volatility: log_returns の標準偏差 (= window 期間は §3 で別議論)
  - 6 時間軸分必要

データファイル (= Phase 0 v3.1 既存):
- `results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet`
- `results/priority_rebuild/labels_mfe_mae_pct_test_2025.parquet`
- `results/priority_rebuild/labels_mfe_mae_pct_test_2026_q1.parquet`

---

## 3. 議論未経由の細部 (= 実装着手前に 1 ステップずつ議論で詰める必要)

以下は議論で OK が出ていない・実装着手前にまこさんとの議論で 1 ステップずつ詰める必要がある:

### 3.1 データ生成・統合まわり
- log_returns / rolling_volatility の新規生成スクリプト仕様 (= 出力先 / 統合 or 別 parquet / 既存 parquet への列追加方法等)
- rolling_volatility の window 期間 (= 業界相場 20 期間が候補だが議論未経由)
- データリーク防止の verify 手順 (= Phase 1 着手前)
- 時間整合の処理確認 (= Phase 0 v3.1 で処理済の前提だが verify が必要)

### 3.2 学習・評価まわり
- fold 境界の具体日付 (= 「train 4 年を 5 等分」までは OK・具体日付は未確定)
- Walk-Forward + Purged K-Fold の実装詳細 (= 各 fold の train/test 比率・cross_validation_generator 等)
- 学習プロセスの実装詳細 (= 各 fold の RobustScaler 再 fit 手順等)
- 状態ラベル付けの妥当性チェック失敗時の対処
- 評価指標の具体的な計測手順 (= log-likelihood の集計方法・状態安定性の指標定義等)

### 3.3 本番運用まわり
- 本番運用時の推論パイプライン構造 (= Phase 0 v3.1 既存処理との接続)
- 視認チェックの具体手順 (= まこさんレビューのチャート出力形式・期間等)
- 学習結果の保存形式詳細 (= JSON / joblib の中身の構造定義)

### 3.4 実装手順全体
- スクリプト分割・順序・テスト方法
- ロギング・エラーハンドリング方針
- 視認チェック合格基準の閾値設定

実装着手時にこれらを 1 つずつまこさんに確認 → GO を取って詰める。CC が独断で決定して設計書に書き込むことは禁止 (= feedback_no_unauthorized_changes 整合)。

---

## 4. 保留事項 (= 議論で OK・今回は入れない・Phase 5 Replay 結果で再判定)

| 保留項目 | 入れない理由 |
|---|---|
| 出来高系特徴量 (= OBV / VWAP / Volume Profile) | BTC 5m で効果が不明・PMC 2025 で importance 0 だった事例あり |
| 板情報系 microstructure (= OBI / Taker Ratio / Funding Rate) | レジームは大局判定なので高頻度ノイズが効くか不明・Phase 0 v4 でデータ取得実装が必要 |
| Fractional Differentiation | レジーム判定で必須という業界実証なし |
| CPCV (= 15 paths) | Purged K-Fold で出発時は十分・計算コスト約 27 時間 |
| Clustered MDA (= 特徴量選択) | 出発時は特徴量数 84 で十分・特徴量を増やした後で導入検討 |
| Meta-Labeling 2 段構造 | まず HMM 単体で精度確認してから追加検討 |
| ストキャスティクス | RSI と情報が重なる可能性 |
| Volume bar / Dollar bar / Imbalance bar の並行入力 | 計算コスト高・MVP で足りない時に追加 |

---

## 5. 不採用事項 (= 議論で OK・工程 1 範囲外)

| 不採用項目 | 理由 |
|---|---|
| Drift Detection (= ADWIN / KSWIN / Page-Hinkley) | 工程 7 (運用監視) で扱う範囲 |
| 1826 日肉眼ラベルを正解とする教師あり学習 | 2026-05-11 凍結対象 (= 精度天井 56% で月次 NET 寄与見えず) |
| MA70 ベース判定 | 同上・凍結対象 |

---

## 6. 評価方法のまとめ

### 6.1 工程 1 単体の評価 (= 統計指標)

レジーム判定単体では PnL 評価しない (= 単体では PnL が出ない構造のため)。以下の統計指標で評価する。

- HMM の log-likelihood (= データへの当てはまりの良さ)
- 状態の安定性 (= 切替頻度・連続滞留時間)
- 機械的命名 + 視認チェックの一致率

### 6.2 工程 1 の最終評価 (= PnL 指標・工程 3-5 通した結果)

- Phase 5 Replay で月次 NET ≥ $1,900 達成への寄与を測定
- 工程 1 ありなしの A/B 比較で寄与を verify
- 寄与が見えなければ工程 1 の入力特徴量・学習方法を見直す

### 6.3 統計指標と PnL 指標の分離 (= cc_role §1.4.6.1 #9 整合)

- 統計指標 (= 6.1) は工程 1 学習中の進捗 verify に使う
- PnL 指標 (= 6.2) は本格判定に使う
- 統計指標での本格判定は禁止

---

## 7. 関連ファイル

| ファイル | 役割 |
|---|---|
| `current_redesign_context.md` | 経緯サマリ (= なぜこの工程 1 設計に至ったか) |
| `cc_entry_logic_self_study.md` v6 §14.6 + §16 + §17 + §20.1 | 業界知識カタログ (= 工程 1 関連の知見全文) |
| `feedback_regime_essence.md` (auto-memory) | レジーム判定の本質 (= 1h regime + 2-3h ヒステリシス) |
| `feedback_regime_visual_check.md` (auto-memory) | 月単位視認チェック (= 視認チェック合格まで 10 回以上調整覚悟) |
| `feedback_priority_starting_line_only.md` (auto-memory) | 旧手動 Priority の扱い (= スタートライン参照のみ) |
| `feedback_writing_style.md` (auto-memory) | 設計提案前の 4 問形式義務 |
| `feedback_no_unauthorized_changes.md` (auto-memory) | 無断変更の絶対禁止・1 ターン 1 変更 |
| Phase 0 v3.1 parquet データ 3 種 | 既存の特徴量データ (= 再利用元) |

---

## 8. 改訂履歴

| 日付 | バージョン | 内容 |
|---|---|---|
| 2026-05-25 | v1 | 初版作成 (= 工程 1 詳細設計書として独立化) |
| 2026-05-25 | v2 | 実装詳細 11 項目確定 (= ただし議論未経由の細部も混入していた) |
| 2026-05-26 | v2.1 | ベース指標を log_returns/rolling_volatility に修正 + covariance_type diag に変更 |
| 2026-05-26 | **v2.2** | **議論未経由の細部を削除して整理** (= まこさん「無断改ざん禁止・絶対命令」指示反映): zscore_return/realized_vol 残骸削除 + fold 境界具体日付削除 + rolling_volatility window 20 期間削除 + 生成スクリプト出力先削除 + NaN 削除サンプル数値詳細削除 + 時間整合具体例削除 + 学習プロセス想定結果テーブル削除 + 実装手順 9 ステップ削除 + 設計上の重要な前提 5 項目削除 + 「議論未経由の細部」セクション §3 として新設 (= 実装着手前に 1 ステップずつ議論で詰める対象を明示) |
