# 工程 1 (相場の状態判定・レジーム判定) 詳細設計書

最終更新: 2026-05-25 (v2・実装詳細 11 項目全確定版)
位置付け: ChatGPT 7 工程フレームの工程 1 の実装設計書。新セッション CC が即座に実装着手できる詳細レベルで記述。
セッション間で情報がリセットされる前提で、自己完結的に書く。

---

## 0. このファイルの読み方

新セッション CC へ: このファイル + `current_redesign_context.md` (経緯) + `cc_entry_logic_self_study.md` v6 (= 業界知識カタログ・2485 行) の 3 つで工程 1 の実装に必要な情報は揃う。各セクションの説明は専門用語に括弧書きで補足を入れている。

本ファイル v2 (= 2026-05-25 まこさんとの議論で確定) で実装詳細 11 項目を全て確定済。新セッション CC が読めばそのまま実装着手可能。

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

## 2. 確定事項一覧 (= 実装詳細 11 項目)

### 2.1 学習構造

| 項目 | 確定内容 |
|---|---|
| 判定間隔 | 1 時間ごと |
| 切替の慣性 (= ヒステリシス) | 連続 2 回同じ判定で切替 (= 2 時間相当) |
| 分類数 | 3 種類 (= 上昇 / 下落 / レンジ) |
| アルゴリズム | HMM (Hidden Markov Model・隠れマルコフモデル) 教師なし学習 |
| 学習データ期間 | 2021-04 〜 2024-12 (= 約 4 年・約 35,000 サンプル) |

### 2.2 入力特徴量 (= 14 指標 × 6 時間軸 = 84 次元・業界実証 verify 済)

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
| zscore_return / realized_vol | window | 20 期間 | Phase 0 v3.1 既存定義 |

### 2.4 HMM ハイパーパラメータ

| パラメータ | 値 | 役割 |
|---|---|---|
| n_components | 3 | 状態数 (= 上昇 / 下落 / レンジ) |
| covariance_type | 'full' | 共分散行列の型 (= 特徴量間の相関も学習・MTF 構造の相関を活かすため) |
| n_iter | 100 | Baum-Welch (= EM) の反復回数上限 |
| tol | 0.01 | 尤度の改善幅がこの値以下なら学習終了 |
| random_state | 42 | 乱数シード固定 (= 再現性確保) |

### 2.5 前処理

- スケーリング: RobustScaler (= 外れ値に強い・中央値と IQR ベース) を Pipeline で fold 毎 fit (= data leak 防止)
- NaN 処理:
  - **学習時**: drop (= 上位足の最初の数百サンプル削除・全体の約 5%)
  - **本番運用時**: Phase 0 v3.1 の ffill 処理に依存 (= 新規実装不要)
- 理由: hmmlearn (= HMM ライブラリ) は NaN を扱えないため。学習データ 35,000 サンプルから約 1,800 サンプル (= SMA50 で 50 日 × 24 時間 + EMA200 で 200 日 × 24 時間の最大値 = 4,800 時間程度) を drop しても残り十分。

### 2.6 評価方法 (= Walk-Forward + Purged K-Fold)

| パラメータ | 値 | 役割 |
|---|---|---|
| fold 数 | 5 | train 4 年を 5 等分 |
| purge 期間 | 24 時間 (= 24 サンプル) | fold 境界の overlap 防止・Phase 0 v3.1 のラベル最大期間 K=288 に対応 |
| embargo 期間 | 24 時間 (= 24 サンプル) | train 終了 → test 開始の空白期間 |

評価指標 (= 統計指標のみ・PnL 評価は工程 3-5 通した Phase 5 Replay で別途):
- HMM の log-likelihood (= データへの当てはまり)
- 状態の安定性 (= 切替頻度・連続滞留時間)
- 機械的命名 + 視認チェックの一致率

fold 境界 (= train データを 5 等分):

| fold | 範囲 |
|---|---|
| Fold 1 | 2021-04 〜 2021-12 (約 9 ヶ月) |
| Fold 2 | 2022-01 〜 2022-09 |
| Fold 3 | 2022-10 〜 2023-06 |
| Fold 4 | 2023-07 〜 2024-03 |
| Fold 5 | 2024-04 〜 2024-12 |

実装ライブラリ: `mlfinpy.cross_validation.PurgedKFold` (= 業界標準・Lopez de Prado AFML 整合)

### 2.7 状態ラベル付け

- **機械的ルール**: 1 時間足 (= 1h time frame) の DI 差 (= DI+ - DI-) の中央値で命名
  - 最大の状態 → 「上昇」
  - 最小の状態 → 「下落」
  - 残りの状態 → 「レンジ」
- **中央値の計算範囲**: train データ全体 (= fold ごとではない)
- **妥当性チェック**: レンジに分類された状態の ADX 平均が他 2 状態より低いこと (= トレンドが弱いこと) を verify
- チェック失敗時はまこさんに報告して入力特徴量の見直しを検討

### 2.8 本番運用時の推論

- **方式**: オンライン Viterbi
- **スライディング窓**: 100 時間 (= 約 4 日分・業界相場の中央値)
- **使用 API** (= hmmlearn ライブラリ):
  - `model.predict(window)` で状態 (= 整数 0/1/2) 取得 → ヒステリシス判定の入力
  - `model.predict_proba(window)` で各状態の確率取得 → 工程 3 への入力 (= ソフトな確度情報)
- 計算コスト: 数ミリ秒程度 (= 本番運用で問題なし)

### 2.9 入力ベクトルの並び順

カテゴリ → 指標 → 時間軸の順で並べる:

```
[ベース系] (12 列)
  log_returns__5m, ..., log_returns__1d
  rolling_volatility__5m, ..., rolling_volatility__1d

[トレンド系 - 方向性] (18 列)
  adx14__5m, adx14__15m, adx14__30m, adx14__1h, adx14__4h, adx14__1d
  di_plus__5m, ..., di_plus__1d
  di_minus__5m, ..., di_minus__1d

[トレンド系 - 移動平均] (18 列)
  close_vs_sma20_pct__5m, ..., __1d
  close_vs_sma50_pct__5m, ..., __1d
  close_vs_ema200_pct__5m, ..., __1d

[トレンド系 - 一目均衡表] (12 列)
  close_vs_tenkan_pct__5m, ..., __1d
  close_vs_kijun_pct__5m, ..., __1d

[モメンタム系] (12 列)
  rsi14__5m, ..., rsi14__1d
  macd_hist_pct__5m, ..., macd_hist_pct__1d

[ボラティリティ系] (12 列)
  atr14_pct__5m, ..., atr14_pct__1d
  bb_width_pct__5m, ..., bb_width_pct__1d
```

合計 84 列。Phase 0 v3.1 で生成済の parquet データから抽出する形 (= 新規データ生成は不要)。

### 2.10 artifact 保存形式・命名規則

| ファイル | 形式 | 命名 |
|---|---|---|
| HMM モデル | joblib | `hmm_train_2021_2024.joblib` |
| Scaler (RobustScaler) | joblib | `scaler_train_2021_2024.joblib` |
| 状態ラベル付け結果 | JSON | `state_labels_train_2021_2024.json` |
| 学習サマリ (= 各 fold の log-likelihood 等) | JSON | `hmm_summary_train_2021_2024.json` |

- 保存先: `results/regime_step1/`
- 命名規則: phase_compliance_checklist §4a.4 整合 (= "test" 文字列禁止・"train" 含む)

### 2.11 ライブラリバージョン

- 既存 `.venv311` 環境を継承 (= Python 3.11)
- 既存ライブラリ: sklearn / pandas / numpy / mlfinpy / joblib / scipy (= Phase 1 v6 でインストール済)
- 新規インストール: **hmmlearn 0.3.x** (= 業界標準安定版・HMM ライブラリ)
- 実装着手時に `.venv311/bin/pip freeze > requirements_step1.txt` でバージョンを記録 (= 後から再現可能に)

---

## 3. 入力データの詳細

### 3.1 既存データの再利用 + 新規生成

Phase 0 v3.1 (= 過去フローの実装) で既に 8 時間軸 (= 5m/15m/30m/1h/4h/1d/1w/1M) × 多指標が生成済 (= 2,724 列の parquet データ)。工程 1 では:

- 6 時間軸 (= 5m/15m/30m/1h/4h/1d) を使用 (= 1w / 1M は使わない)
- §2.2 の 14 指標のうち **12 指標 (= 既存・再利用)**: adx14 / di_plus / di_minus / close_vs_sma20_pct / close_vs_sma50_pct / close_vs_ema200_pct / close_vs_tenkan_pct / close_vs_kijun_pct / rsi14 / macd_hist_pct / atr14_pct / bb_width_pct → Phase 0 v3.1 既存 parquet から抽出
- §2.2 の 14 指標のうち **2 指標 (= 新規生成が必要)**: log_returns / rolling_volatility → Phase 0 v3.1 に存在しないため新規生成 (= 業界 default 必須として採用するため・まこさん 2026-05-25 OK 内容に整合)

**新規生成内容**:
- log_returns: `ln(close_t / close_{t-1})` (= 対数リターン・1 期間)
- rolling_volatility: 過去 20 期間の log_returns の標準偏差
- 6 時間軸分 (= log_returns__{5m, 15m, 30m, 1h, 4h, 1d} + rolling_volatility__{5m, 15m, 30m, 1h, 4h, 1d} = 12 列追加)
- 生成スクリプトの出力先: Phase 0 v3.1 既存 parquet に追加列として統合・または工程 1 用に別 parquet として出力

データファイル:
- `results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet` (= train・1.5 GB)
- `results/priority_rebuild/labels_mfe_mae_pct_test_2025.parquet` (= test 2025・469 MB)
- `results/priority_rebuild/labels_mfe_mae_pct_test_2026_q1.parquet` (= test 2026 Q1・112 MB)

### 3.2 時間整合の処理 (= データリーク防止)

1 時間ごとのサンプル時点で、各時間軸の値は **確定済の bar のみ** から取る。Phase 0 v3.1 の生成時点で時間整合は守られているので、再利用すれば leak リスクは低い (= 念のため Phase 1 着手前に再 verify する)。

例 (= 判定時点 9:00 の場合):

| 時間軸 | 使う bar |
|---|---|
| 5m | 8:55-9:00 bar (= 完成) |
| 15m | 8:45-9:00 bar (= 完成) |
| 30m | 8:30-9:00 bar (= 完成) |
| 1h | 8:00-9:00 bar (= 完成) |
| 4h | 4:00-8:00 bar (= 完成・次の 8:00-12:00 はまだ完成していない) |
| 1d | 前日完成日足 |

---

## 4. 学習方法の詳細

### 4.1 アルゴリズム選定理由

- 教師なし学習 = データから自然な状態を発見する手法
- 凍結された旧研究 (= 1826 日肉眼ラベル + LightGBM 教師あり) は精度天井 56% で月次 NET 寄与見えなかった (= L-126 の経緯)
- 教師あり学習は「正解ラベルを再現」する仕組みなので、正解の質を超えられない
- HMM 教師なしならデータから新しい構造を発見できる可能性

### 4.2 学習プロセス (= 5 ステップ)

**ステップ 1: 入力データ準備**

- 4 万サンプル × 84 次元の行列を作成 (= §3.1 + §2.9)
- NaN 行を drop (= 上位足の初期不安定期間)
- RobustScaler で前処理 (= Pipeline で fold 毎 fit)

**ステップ 2: HMM パラメータ初期化**

- 状態数 K=3
- 各状態の特徴量分布 (= 多次元正規分布の平均 + 分散共分散行列) をランダム初期化 (random_state=42)
- 状態遷移確率行列をランダム初期化

**ステップ 3: Baum-Welch アルゴリズムで反復学習**

- EM (Expectation-Maximization) を反復
- E ステップ: 現在のパラメータで「各時点でどの状態にいる確率が高いか」を計算
- M ステップ: 推定結果を使ってパラメータを更新
- 尤度が収束するか n_iter=100 回に達するまで反復 (= tol=0.01)

**ステップ 4: 学習結果の確認**

学習後に各状態の特徴量分布 + 状態遷移確率を保存。例 (= 想定結果):

| 状態 | 典型パターン (= 抜粋) |
|---|---|
| 状態 0 | ADX_1d 平均 28 / DI+_1d 平均 24 / DI-_1d 平均 16 / RSI_4h 平均 58 |
| 状態 1 | ADX_1d 平均 15 / DI+_1d 平均 19 / DI-_1d 平均 20 / RSI_4h 平均 50 |
| 状態 2 | ADX_1d 平均 30 / DI+_1d 平均 15 / DI-_1d 平均 26 / RSI_4h 平均 42 |

**ステップ 5: 状態のラベル付け (= 機械的ルール + 妥当性チェック)**

§2.7 のルールに従って:
- DI 差中央値 (= 1h time frame) が最大 → 「上昇」
- DI 差中央値が最小 → 「下落」
- 残り → 「レンジ」

妥当性チェック: レンジ状態の ADX 平均が他 2 状態より低い (= トレンド弱い) ことを verify。失敗時はまこさんに報告。

### 4.3 学習評価方法

Walk-Forward + Purged K-Fold (= §2.6) で交差検証。各 fold で:

1. fold 内データを train/test に分割
2. train で HMM 学習
3. test で log-likelihood + 状態安定性 + 機械的命名一致率を評価
4. fold 間で結果のばらつきを記録

評価指標は統計指標のみ (= PnL 評価は工程 3-5 通した Phase 5 Replay で別途)。

---

## 5. 本番運用時の判定ロジック

### 5.1 推論プロセス

各時点 (= 1 時間ごと) で以下を実行:

1. 最新の特徴量を観測 (= 84 次元ベクトル・§2.9 の並び順)
2. 直近 100 時間分のスライディング窓を構築 (= §2.8)
3. 学習済 RobustScaler で前処理 (= `scaler.transform()`)
4. `hmm.predict(window)` で状態系列を取得 (= 最尤状態・Viterbi)
5. `hmm.predict_proba(window)` で各状態の確率系列を取得 (= forward-backward)
6. 窓の最後の時点 (= 現在) の状態と確率を出力
7. ヒステリシス (= §5.2) を適用して確定レジームを決定

### 5.2 ヒステリシス擬似コード (= §2.1 の連続 2 回切替を実装)

```python
# 初期化
current_regime = None              # 確定状態 (= None なら未確定)
recent_predictions = []            # 直近の HMM 出力履歴 (最大 2 個)

# 各時点 (= 1 時間ごと) で実行
def update_regime(hmm_prediction: int) -> int | None:
    """
    hmm_prediction: HMM が出した状態 (= 0/1/2 のいずれか)
    返り値: 確定レジーム (= 0/1/2 or None)
    """
    recent_predictions.append(hmm_prediction)
    if len(recent_predictions) > 2:
        recent_predictions.pop(0)
    
    # 直近 2 回が同じ判定なら確定状態を切替
    if len(recent_predictions) == 2 and recent_predictions[0] == recent_predictions[1]:
        current_regime = recent_predictions[0]
    
    # それ以外は前回の確定状態を維持
    return current_regime
```

挙動の具体例:

| 時刻 | HMM 生判定 | 直近 2 回 | 確定レジーム | 動作 |
|---|---|---|---|---|
| 9:00 | 上昇 | [上昇] | None | 履歴に追加・確定なし |
| 10:00 | 上昇 | [上昇, 上昇] | **上昇** | 連続同じなので確定 |
| 11:00 | 下落 | [上昇, 下落] | 上昇 (維持) | 直近 2 回が違うので維持 |
| 12:00 | 上昇 | [下落, 上昇] | 上昇 (維持) | 直近 2 回が違うので維持 |
| 13:00 | 下落 | [上昇, 下落] | 上昇 (維持) | 同上 |
| 14:00 | 下落 | [下落, 下落] | **下落** | 連続同じなので切替 |

### 5.3 工程 3 への出力

- 現在のレジーム状態 (= ヒステリシス後の確定状態・0/1/2 or None)
- 各状態の確率 (= ソフトな確度情報・例: [0.7, 0.1, 0.2])

`current_regime = None` の場合: 工程 3 は Entry 発火しない (= 待機)。

---

## 6. 実装手順 (= 新セッション CC が着手する順序)

1. **環境準備**: `.venv311/bin/pip install hmmlearn` で hmmlearn インストール → `pip freeze > requirements_step1.txt` で記録
2. **新規指標生成スクリプト作成**: log_returns + rolling_volatility を 6 時間軸分計算 (= 12 列追加) → Phase 0 v3.1 既存 parquet に統合 or 工程 1 用別 parquet 出力 (= §3.1 新規生成内容)
3. **データ抽出スクリプト作成**: 統合 parquet から 84 列 (= §2.2 の 14 指標 × 6 時間軸) を抽出 + NaN 行 drop
4. **学習スクリプト作成**:
   - RobustScaler + HMM (= §2.4 のハイパーパラメータ) のパイプライン
   - mlfinpy.PurgedKFold で 5 fold 学習評価 (= §2.6)
5. **状態ラベル付けスクリプト作成**: §2.7 の機械的ルール + 妥当性チェック
6. **artifact 保存**: §2.10 の命名規則 + 保存先で 4 種類のファイル出力
7. **本番運用スクリプト作成**: §5.1 + §5.2 のオンライン推論 + ヒステリシス
8. **視認チェック (= まこさんレビュー)**: 過去 12 ヶ月のチャート上で命名が肉眼判定と一致するか確認
9. 視認チェック OK なら工程 2 の議論に進む・NG なら入力特徴量見直し

---

## 7. 保留事項 (= 今回は入れない・Phase 5 Replay 結果で再判定)

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

## 8. 不採用事項 (= 工程 1 範囲外)

| 不採用項目 | 理由 |
|---|---|
| Drift Detection (= ADWIN / KSWIN / Page-Hinkley) | 工程 7 (運用監視) で扱う範囲 |
| 1826 日肉眼ラベルを正解とする教師あり学習 | 2026-05-11 凍結対象 (= 精度天井 56% で月次 NET 寄与見えず) |
| MA70 ベース判定 | 同上・凍結対象 |

---

## 9. 評価方法のまとめ

### 9.1 工程 1 単体の評価 (= 統計指標)

レジーム判定単体では PnL 評価しない (= 単体では PnL が出ない構造のため)。以下の統計指標で評価する。

- HMM の log-likelihood (= データへの当てはまりの良さ)
- 状態の安定性 (= 切替頻度・連続滞留時間)
- 機械的命名 + 視認チェックの一致率

### 9.2 工程 1 の最終評価 (= PnL 指標・工程 3-5 通した結果)

- Phase 5 Replay で月次 NET ≥ $1,900 達成への寄与を測定
- 工程 1 ありなしの A/B 比較で寄与を verify
- 寄与が見えなければ工程 1 の入力特徴量・学習方法を見直す (= 凍結された旧研究と同じ罠を避ける)

### 9.3 統計指標と PnL 指標の分離 (= cc_role §1.4.6.1 #9 整合)

- 統計指標 (= 9.1) は工程 1 学習中の進捗 verify に使う
- PnL 指標 (= 9.2) は本格判定に使う
- 「視認チェック 80% 達成したから合格」のような統計指標での本格判定は禁止

---

## 10. 関連ファイル

| ファイル | 役割 |
|---|---|
| `current_redesign_context.md` | 経緯サマリ (= なぜこの工程 1 設計に至ったか) |
| `cc_entry_logic_self_study.md` v6 §14.6 + §16 + §17 + §20.1 | 業界知識カタログ (= 工程 1 関連の知見全文) |
| `feedback_regime_essence.md` (auto-memory) | レジーム判定の本質 (= 1h regime + 2-3h ヒステリシス) |
| `feedback_regime_visual_check.md` (auto-memory) | 月単位視認チェック (= 視認チェック合格まで 10 回以上調整覚悟) |
| `feedback_priority_starting_line_only.md` (auto-memory) | 旧手動 Priority の扱い (= スタートライン参照のみ) |
| `feedback_writing_style.md` (auto-memory) | 設計提案前の 4 問形式義務 |
| Phase 0 v3.1 parquet データ 3 種 | 既存の特徴量データ (= 再利用元) |

---

## 11. 設計上の重要な前提 (= 新セッション CC が忘れがちな点)

### 11.1 「学習資産を全部使う」は目的ではない

案 B 学習で整理した 7 領域カタログ (= cc_entry_logic_self_study.md v6) の知見を **全部** 入れるのではなく、**目標達成 (= 月次 NET ≥ $1,900) に必要な構成** を採用・残りは保留に置く。

### 11.2 「凍結対象の再演」を避ける

CLAUDE.md §現在の方針で 2026-05-11 凍結された手法 (= MA70 ベース判定 + 1826 日肉眼ラベル + LightGBM 教師あり ML 分類) を再提案しない。Phase 0 v3.1 既存データは凍結対象ではない (= 新フローの実装基盤として継続使用)。

### 11.3 「精度を目的化しない」

レジーム判定の精度自体は最終評価軸ではない。最終評価軸は **「工程 3-7 通した月次 NET ≥ $1,900 達成」**。レジーム判定が肉眼判定と完全一致しなくても、工程 3 の Entry ML 学習で有効な前提情報として機能して PnL に寄与すれば OK。

### 11.4 「閾値ではなく分布で判定」

HMM は「ADX > 25 なら上昇」のような離散的な閾値判定ではなく、「ADX の確率分布」(= 平均 + 分散) で判定する。各状態の特徴量分布をデータから学習し、新しいデータ点の各状態への適合度を確率で計算する。

### 11.5 「ロング/ショート別ロジックは工程 1 にない」

ロング/ショートで RSI の閾値が違う等のロジックは Entry 判定 (= 工程 2/3) の話で、工程 1 のレジーム判定は方向中立的。

---

## 12. 改訂履歴

| 日付 | バージョン | 内容 |
|---|---|---|
| 2026-05-25 | v1 | 初版作成 (= 工程 1 詳細設計書として独立化) |
| 2026-05-25 | v2 | **実装詳細 11 項目を全確定** (= まこさんとの議論で確定): 指標計算式 + HMM ハイパラ + Phase 0 v3.1 カラム名 verify + Walk-Forward Purged K-Fold 詳細 + 状態ラベル付け計算範囲 + ヒステリシス擬似コード + Viterbi オンライン推論 + 入力ベクトル並び順 + NaN 処理 + artifact 保存 + ライブラリバージョン + 業界実証 verify 済の 14 指標 (= log_returns + rolling_volatility 追加) |
