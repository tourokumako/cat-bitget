"""
工程 1 (相場の状態判定・レジーム判定) HMM 学習スクリプト

設計書: .claude/memory/step1_regime_design.md v2.2 整合

機能:
  1. Phase 0 v3.1 parquet から 12 既存指標 (§2.2) を 6 時間軸分抽出
  2. 5m close を各 TF に resample → log_returns / rolling_volatility を新規生成 (§2.12)
  3. RobustScaler + GaussianHMM (covariance_type=diag) Pipeline で学習 (§2.4, §2.5)
  4. Walk-Forward + Purged K-Fold 5 fold 評価 (§2.6)
  5. 1h DI 差中央値で状態ラベル付け + 妥当性チェック (§2.7)
  6. artifact 保存 (§2.10): joblib×2 + JSON×2 → results/regime_step1/

入力: results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet
出力: results/regime_step1/
  - hmm_train_2021_2024.joblib
  - scaler_train_2021_2024.joblib
  - state_labels_train_2021_2024.json
  - hmm_summary_train_2021_2024.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from mlfinpy.cross_validation.cross_validation import PurgedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

# ===== 設計書 §2 定数 =====
TF_LIST = ["5m", "15m", "30m", "1h", "4h", "1d"]  # §2.2 6 時間軸
TF_RESAMPLE_RULE = {  # pandas resample rule
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1D",
}

# §2.2 14 指標 base 名 (ベース 2 + トレンド 3 + 移動平均 3 + 一目 2 + モメンタム 2 + ボラ 2)
BASE_INDICATORS_NEW = ["log_returns", "rolling_volatility"]  # 新規生成 (§2.12)
EXISTING_INDICATORS = [
    # トレンド・方向性
    "adx14", "di_plus", "di_minus",
    # 移動平均線
    "close_vs_sma20_pct", "close_vs_sma50_pct", "close_vs_ema200_pct",
    # 一目均衡表
    "close_vs_tenkan_pct", "close_vs_kijun_pct",
    # モメンタム
    "rsi14", "macd_hist_pct",
    # ボラ
    "atr14_pct", "bb_width_pct",
]

ROLLING_VOL_WINDOW = 20  # §3.1.2 業界 default

# §2.4 HMM ハイパラ
N_COMPONENTS = 3
COVARIANCE_TYPE = "diag"  # §2.4 v2.1 で full から変更 (過学習防止)
N_ITER = 100
TOL = 0.01
RANDOM_STATE = 42

# §2.6 Walk-Forward Purged K-Fold
N_FOLDS = 5
PURGE_HOURS = 24
EMBARGO_HOURS = 24

# §2.7 状態ラベル付け
LABEL_TF = "1h"  # 1h DI 差中央値で命名

# パス
REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_PARQUET = REPO_ROOT / "results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet"
# Phase 0 v3.1 で atr14_pct__1d が生成漏れ → CC が CSV から補填するため OHLCV 元 CSV を読む
# (Phase 0 build_labels_pct.py L79 と同じ正本 CSV)
INPUT_OHLCV_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv"
ATR_FALLBACK_TF = "1d"  # Phase 0 v3.1 生成漏れの 1 件

OUT_DIR = REPO_ROOT / "results/regime_step1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# artifact 命名 (§2.10 + phase_compliance_checklist §4a.4 整合 = "test" 文字列禁止・"train" 含む)
HMM_ARTIFACT = OUT_DIR / "hmm_train_2021_2024.joblib"
SCALER_ARTIFACT = OUT_DIR / "scaler_train_2021_2024.joblib"
LABELS_JSON = OUT_DIR / "state_labels_train_2021_2024.json"
SUMMARY_JSON = OUT_DIR / "hmm_summary_train_2021_2024.json"


def load_5m_ohlcv_csv(path: Path, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """正本 OHLCV CSV (= Bitget USDT-FUTURES 5m bar) を読み込む。

    Phase 0 v3.1 build_labels_pct.py L79 と同じ正本ファイルを参照。
    指定期間 [start, end] にトリムして返す。
    """
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()
    df = df.loc[start:end]
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def calc_atr14_pct_wilder(ohlcv: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder 原典 (= 設計書 §2.3 整合) で ATR14 を計算し pct (= ATR / close × 100) で返す。

    True Range = max(high - low, |high - prev_close|, |low - prev_close|)
    ATR = TR の Wilder smoothing (= RMA・EMA alpha=1/period)
    """
    high = ohlcv["high"]
    low = ohlcv["low"]
    close = ohlcv["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    return atr / close * 100.0


def build_atr14_pct_1d_fallback(df_index_5m: pd.DatetimeIndex) -> pd.Series:
    """Phase 0 v3.1 生成漏れの atr14_pct__1d を CSV から補填する。

    1. 5m OHLCV CSV を train 期間で読み込む (期間は df_index_5m から導出)
    2. 1d resample (rule="1D", label="right", closed="right") で OHLC 集計
    3. Wilder ATR14 → pct
    4. 5m grid に reindex(method='ffill') で各 5m 時点に直近確定 1d ATR を貼る
    """
    start = df_index_5m.min()
    end = df_index_5m.max()
    ohlcv_5m = load_5m_ohlcv_csv(INPUT_OHLCV_CSV, start, end)
    rule = TF_RESAMPLE_RULE[ATR_FALLBACK_TF]
    ohlcv_1d = ohlcv_5m.resample(rule, label="right", closed="right").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    ).dropna()
    atr_pct_1d = calc_atr14_pct_wilder(ohlcv_1d, period=14)
    return atr_pct_1d.reindex(df_index_5m, method="ffill")


def build_input_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Phase 0 v3.1 parquet から 84 列入力行列を構築する。

    - 12 既存指標は parquet からそのまま抽出 (= 6 TF × 12 = 72 列)
    - 2 ベース指標 (log_returns / rolling_volatility) は 5m close を各 TF に resample して新規生成 (= 6 TF × 2 = 12 列)

    並び順は設計書 §2.9 (= カテゴリ → 指標 → 時間軸):
      [ベース系] log_returns × 6 / rolling_volatility × 6
      [トレンド方向性] adx14 × 6 / di_plus × 6 / di_minus × 6
      [トレンド移動平均] close_vs_sma20_pct × 6 / close_vs_sma50_pct × 6 / close_vs_ema200_pct × 6
      [トレンド一目均衡表] close_vs_tenkan_pct × 6 / close_vs_kijun_pct × 6
      [モメンタム] rsi14 × 6 / macd_hist_pct × 6
      [ボラ] atr14_pct × 6 / bb_width_pct × 6
    """
    # Phase 0 v3.1 parquet は timestamp を DatetimeIndex として持つ (= naive・5min 間隔)
    df = df.sort_index()
    assert isinstance(df.index, pd.DatetimeIndex), f"expected DatetimeIndex, got {type(df.index)}"

    # 1. ベース系 (新規生成): 5m close を各 TF に resample → log returns + rolling vol
    close_5m = df["close"].astype(float)
    base_cols: dict[str, pd.Series] = {}
    for tf in TF_LIST:
        if tf == "5m":
            close_tf = close_5m.copy()
        else:
            # close = bar 終値 = resample 後の last
            close_tf = close_5m.resample(TF_RESAMPLE_RULE[tf], label="right", closed="right").last()
        log_ret = np.log(close_tf / close_tf.shift(1))
        rol_vol = log_ret.rolling(ROLLING_VOL_WINDOW).std()
        # 5m index に reindex (= ffill = bar 確定後の値を 5m 時点で前方埋め)
        if tf != "5m":
            log_ret = log_ret.reindex(close_5m.index, method="ffill")
            rol_vol = rol_vol.reindex(close_5m.index, method="ffill")
        base_cols[f"log_returns__{tf}"] = log_ret
        base_cols[f"rolling_volatility__{tf}"] = rol_vol
    X_base = pd.DataFrame(base_cols, index=close_5m.index)

    # 2. 既存 12 指標 (parquet から抽出)
    #    ただし atr14_pct__1d は Phase 0 v3.1 生成漏れのため CSV OHLCV から後段補填する
    existing_cols: list[str] = []
    for ind in EXISTING_INDICATORS:
        for tf in TF_LIST:
            if ind == "atr14_pct" and tf == ATR_FALLBACK_TF:
                continue  # 後段で CSV から計算
            existing_cols.append(f"{ind}__{tf}")
    missing = [c for c in existing_cols if c not in df.columns]
    if missing:
        sys.exit(f"ABORT: missing existing indicator columns in parquet: {missing[:10]}...")
    X_existing = df[existing_cols].astype(float)

    # 2b. atr14_pct__1d を CSV OHLCV から補填 (Wilder ATR14・5m grid に ffill)
    fallback_col = f"atr14_pct__{ATR_FALLBACK_TF}"
    print(f"[ATR fallback] computing {fallback_col} from {INPUT_OHLCV_CSV.name} ...")
    X_existing[fallback_col] = build_atr14_pct_1d_fallback(df.index)
    print(f"    non-NaN samples: {X_existing[fallback_col].notna().sum()} / {len(X_existing)}")

    # 3. 統合 (並び順 = ベース → トレンド方向性 → 移動平均 → 一目 → モメンタム → ボラ)
    ordered_cols: list[str] = []
    for base in BASE_INDICATORS_NEW + EXISTING_INDICATORS:
        for tf in TF_LIST:
            ordered_cols.append(f"{base}__{tf}")

    X = pd.concat([X_base, X_existing], axis=1)
    X = X[ordered_cols]
    assert X.shape[1] == 84, f"expected 84 columns, got {X.shape[1]}"
    return X


def hourly_resample_for_regime(X: pd.DataFrame) -> pd.DataFrame:
    """
    判定間隔 1 時間ごと (§2.1) — 5m grid の入力行列を 1h grid に reduce する。

    各 1h bar の末尾 (= close 時点) の値を採用 (= ffill された値を使うので、各時点で確定済の上位足情報を保持)。
    """
    return X.resample("1h", label="right", closed="right").last()


def drop_nan(X: pd.DataFrame) -> pd.DataFrame:
    """§2.5 学習時は NaN drop (上位足の最初の数百サンプル削除・約 5%)。"""
    before = len(X)
    X = X.dropna()
    after = len(X)
    print(f"[NaN drop] {before} -> {after} samples ({(before - after) / before * 100:.2f}% removed)")
    return X


def walk_forward_purged_kfold(
    X: pd.DataFrame,
) -> list[dict]:
    """
    §2.6 Walk-Forward + Purged K-Fold 5 fold 評価。

    各 fold:
      - train (= fold index in train set) で Pipeline (RobustScaler + HMM) を fit
      - test (= fold index in test set) で log-likelihood + 状態安定性を評価
    """
    # mlfinpy.PurgedKFold は samples_info_sets (= label end time series) を必要とするため、
    # 各時点について event_start = event_end (= 1h 時点・同時) として渡す。
    # この前提下では Purged K-Fold は通常の TimeSeriesSplit に embargo を加えた挙動になる。
    samples_info_sets = pd.Series(X.index, index=X.index)

    # embargo を割合に変換 (= mlfinpy.PurgedKFold は pct_embargo として割合受け取り)
    pct_embargo = EMBARGO_HOURS / len(X)

    cv = PurgedKFold(n_splits=N_FOLDS, samples_info_sets=samples_info_sets, pct_embargo=pct_embargo)

    fold_results: list[dict] = []
    for fold_i, (train_idx, test_idx) in enumerate(cv.split(X)):
        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]

        pipe = Pipeline([
            ("scaler", RobustScaler()),
            ("hmm", GaussianHMM(
                n_components=N_COMPONENTS,
                covariance_type=COVARIANCE_TYPE,
                n_iter=N_ITER,
                tol=TOL,
                random_state=RANDOM_STATE,
            )),
        ])

        # Pipeline.fit は HMM の fit に lengths を渡せないので個別 fit
        scaler = RobustScaler()
        X_train_scaled = scaler.fit_transform(X_train.values)
        hmm = GaussianHMM(
            n_components=N_COMPONENTS,
            covariance_type=COVARIANCE_TYPE,
            n_iter=N_ITER,
            tol=TOL,
            random_state=RANDOM_STATE,
        )
        hmm.fit(X_train_scaled)

        X_test_scaled = scaler.transform(X_test.values)
        ll_test = hmm.score(X_test_scaled)
        ll_train = hmm.score(X_train_scaled)

        # 状態安定性 (= test 期間中の状態切替頻度)
        states_test = hmm.predict(X_test_scaled)
        n_switches = int((np.diff(states_test) != 0).sum())
        avg_dwell = len(states_test) / max(n_switches + 1, 1)

        fold_results.append({
            "fold": fold_i,
            "train_size": int(len(train_idx)),
            "test_size": int(len(test_idx)),
            "train_start": str(X_train.index[0]),
            "train_end": str(X_train.index[-1]),
            "test_start": str(X_test.index[0]),
            "test_end": str(X_test.index[-1]),
            "log_likelihood_train": float(ll_train),
            "log_likelihood_test": float(ll_test),
            "n_state_switches_test": n_switches,
            "avg_dwell_hours_test": float(avg_dwell),
            "hmm_converged": bool(hmm.monitor_.converged),
            "hmm_n_iter": int(hmm.monitor_.iter),
        })
        print(f"[fold {fold_i}] ll_test={ll_test:.2f} ll_train={ll_train:.2f} "
              f"n_switches={n_switches} avg_dwell={avg_dwell:.1f}h converged={hmm.monitor_.converged}")
    return fold_results


def fit_final_model(X: pd.DataFrame) -> tuple[RobustScaler, GaussianHMM]:
    """train 全データで最終モデルを fit (artifact 保存用)。"""
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X.values)
    hmm = GaussianHMM(
        n_components=N_COMPONENTS,
        covariance_type=COVARIANCE_TYPE,
        n_iter=N_ITER,
        tol=TOL,
        random_state=RANDOM_STATE,
    )
    hmm.fit(X_scaled)
    print(f"[final fit] converged={hmm.monitor_.converged} n_iter={hmm.monitor_.iter} "
          f"log_likelihood={hmm.score(X_scaled):.2f}")
    return scaler, hmm


def label_states(X: pd.DataFrame, scaler: RobustScaler, hmm: GaussianHMM) -> dict:
    """
    §2.7 状態ラベル付け:
      - 1h DI 差 (= di_plus__1h - di_minus__1h) の状態別中央値で命名
      - 最大 → 「上昇」 / 最小 → 「下落」 / 残り → 「レンジ」
      - 中央値の計算範囲 = train データ全体
      - 妥当性チェック: 「レンジ」状態の adx14__1h 平均が他 2 状態より低いこと
    """
    X_scaled = scaler.transform(X.values)
    states = hmm.predict(X_scaled)

    di_plus_1h_col = f"di_plus__{LABEL_TF}"
    di_minus_1h_col = f"di_minus__{LABEL_TF}"
    adx_1h_col = f"adx14__{LABEL_TF}"

    di_diff = X[di_plus_1h_col] - X[di_minus_1h_col]
    adx_1h = X[adx_1h_col]

    per_state: dict[int, dict] = {}
    for s in range(N_COMPONENTS):
        mask = states == s
        per_state[s] = {
            "count": int(mask.sum()),
            "di_diff_median": float(di_diff[mask].median()),
            "adx14_1h_mean": float(adx_1h[mask].mean()),
        }

    # ラベル割当
    sorted_by_median = sorted(per_state.items(), key=lambda x: x[1]["di_diff_median"])
    state_to_label = {}
    state_to_label[sorted_by_median[-1][0]] = "上昇"
    state_to_label[sorted_by_median[0][0]] = "下落"
    state_to_label[sorted_by_median[1][0]] = "レンジ"

    # 妥当性チェック: レンジの ADX が他 2 状態より低い
    range_state = sorted_by_median[1][0]
    other_states = [sorted_by_median[0][0], sorted_by_median[-1][0]]
    range_adx = per_state[range_state]["adx14_1h_mean"]
    other_adx = [per_state[s]["adx14_1h_mean"] for s in other_states]
    sanity_pass = all(range_adx < a for a in other_adx)

    result = {
        "state_to_label": {int(s): lbl for s, lbl in state_to_label.items()},
        "per_state_stats": {int(s): v for s, v in per_state.items()},
        "label_tf": LABEL_TF,
        "sanity_check_passed": sanity_pass,
        "sanity_check_detail": {
            "range_state_id": int(range_state),
            "range_adx14_1h_mean": float(range_adx),
            "other_adx14_1h_mean": [float(a) for a in other_adx],
            "rule": "レンジ状態の adx14__1h 平均が他 2 状態より低いこと",
        },
    }
    return result


def main() -> int:
    print(f"[input] {INPUT_PARQUET}")
    print(f"[output dir] {OUT_DIR}")

    if not INPUT_PARQUET.exists():
        sys.exit(f"ABORT: input parquet not found: {INPUT_PARQUET}")

    # 1. データ読み込み + 84 列入力行列構築
    print("[1/6] loading parquet ...")
    df = pd.read_parquet(INPUT_PARQUET)
    print(f"    raw shape: {df.shape}")
    X_5m = build_input_matrix(df)
    print(f"    84-col matrix (5m grid): {X_5m.shape}")

    # 2. 1h grid に reduce (= 判定間隔 1 時間)
    X_1h = hourly_resample_for_regime(X_5m)
    print(f"    1h grid: {X_1h.shape}")

    # 3. 学習時 NaN drop
    X = drop_nan(X_1h)
    print(f"    after NaN drop: {X.shape}")

    # 4. Walk-Forward Purged K-Fold 5 fold 評価
    print("[2/6] Walk-Forward Purged K-Fold 5 fold evaluation ...")
    fold_results = walk_forward_purged_kfold(X)

    # 5. train 全データで最終モデル fit (artifact 保存用)
    print("[3/6] fitting final model on full train data ...")
    scaler, hmm = fit_final_model(X)

    # 6. 状態ラベル付け
    print("[4/6] labeling states by 1h DI diff median + ADX sanity check ...")
    labels = label_states(X, scaler, hmm)
    print(f"    state_to_label: {labels['state_to_label']}")
    print(f"    sanity_check_passed: {labels['sanity_check_passed']}")

    # 7. artifact 保存
    print("[5/6] saving artifacts ...")
    joblib.dump(hmm, HMM_ARTIFACT)
    joblib.dump(scaler, SCALER_ARTIFACT)
    with LABELS_JSON.open("w") as f:
        json.dump(labels, f, ensure_ascii=False, indent=2)

    # 8. 学習サマリ JSON
    print("[6/6] writing summary JSON ...")
    summary = {
        "script": __file__,
        "input_parquet": str(INPUT_PARQUET),
        "input_shape_raw": list(df.shape),
        "input_shape_84cols": list(X_5m.shape),
        "input_shape_1h_grid": list(X_1h.shape),
        "input_shape_after_dropna": list(X.shape),
        "design_doc": ".claude/memory/step1_regime_design.md (v2.2)",
        "tf_list": TF_LIST,
        "indicators_existing": EXISTING_INDICATORS,
        "indicators_new": BASE_INDICATORS_NEW,
        "rolling_vol_window": ROLLING_VOL_WINDOW,
        "hmm_hyperparams": {
            "n_components": N_COMPONENTS,
            "covariance_type": COVARIANCE_TYPE,
            "n_iter": N_ITER,
            "tol": TOL,
            "random_state": RANDOM_STATE,
        },
        "cv_config": {
            "n_folds": N_FOLDS,
            "purge_hours": PURGE_HOURS,
            "embargo_hours": EMBARGO_HOURS,
        },
        "fold_results": fold_results,
        "label_config": {"label_tf": LABEL_TF},
        "labels": labels,
        "artifacts": {
            "hmm": str(HMM_ARTIFACT),
            "scaler": str(SCALER_ARTIFACT),
            "state_labels_json": str(LABELS_JSON),
            "summary_json": str(SUMMARY_JSON),
        },
    }
    with SUMMARY_JSON.open("w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"[DONE] artifacts saved to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
