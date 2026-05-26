"""工程 1 (相場の状態判定・レジーム判定) 視認チェック用ダッシュボードデータ生成。

設計書: .claude/memory/step1_regime_design.md v2.2 整合

入力 (= train_hmm_regime.py で出力済の artifact):
  results/regime_step1/hmm_train_2021_2024.joblib
  results/regime_step1/scaler_train_2021_2024.joblib
  results/regime_step1/state_labels_train_2021_2024.json
  results/regime_step1/hmm_summary_train_2021_2024.json
  results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet (84 列特徴量元)
  data/BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv (atr14_pct__1d 補填用)

出力:
  dashboard/regime_prototype/labels_v15.csv (= datetime_utc + regime ラベル・1h 粒度)
  dashboard/regime_prototype/index.json (= 既存 v1-v14 配列に v15 追記)

動作確認:
  python scripts/dashboard/dashboard_server.py
  → http://localhost:8765/index.html → ⑪ レジーム試作 → v15 を選択
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

# 入力 artifact
ARTIFACT_DIR = REPO_ROOT / "results" / "regime_step1"
HMM_PATH = ARTIFACT_DIR / "hmm_train_2021_2024.joblib"
SCALER_PATH = ARTIFACT_DIR / "scaler_train_2021_2024.joblib"
LABELS_JSON = ARTIFACT_DIR / "state_labels_train_2021_2024.json"
SUMMARY_JSON = ARTIFACT_DIR / "hmm_summary_train_2021_2024.json"

# 特徴量元
INPUT_PARQUET = REPO_ROOT / "results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet"
INPUT_OHLCV_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv"

# 出力
PROTO_DIR = REPO_ROOT / "dashboard" / "regime_prototype"
OUT_CSV = PROTO_DIR / "labels_v15.csv"
INDEX_JSON = PROTO_DIR / "index.json"

VERSION = "v15"

# ===== train_hmm_regime.py 整合 定数 (= 設計書 §2.2 / §2.3 / §2.9) =====
TF_LIST = ["5m", "15m", "30m", "1h", "4h", "1d"]
TF_RESAMPLE_RULE = {
    "5m": "5min", "15m": "15min", "30m": "30min",
    "1h": "1h", "4h": "4h", "1d": "1D",
}
BASE_INDICATORS_NEW = ["log_returns", "rolling_volatility"]
EXISTING_INDICATORS = [
    "adx14", "di_plus", "di_minus",
    "close_vs_sma20_pct", "close_vs_sma50_pct", "close_vs_ema200_pct",
    "close_vs_tenkan_pct", "close_vs_kijun_pct",
    "rsi14", "macd_hist_pct",
    "atr14_pct", "bb_width_pct",
]
ROLLING_VOL_WINDOW = 20
ATR_FALLBACK_TF = "1d"

# 日本語ラベル → 英語ラベル (= 過去ダッシュボード v1-v14 整合)
LABEL_JP_TO_EN = {"上昇": "uptrend", "下落": "downtrend", "レンジ": "range"}

# ヒステリシス: 連続 N 回同判定で切替 (= 設計書 §2.1 「連続 2 回」)
HYSTERESIS_N = 2


# ===== 特徴量構築 (train_hmm_regime.py と同じロジック) =====
def load_5m_ohlcv_csv(path: Path, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()
    df = df.loc[start:end]
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def calc_atr14_pct_wilder(ohlcv: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = ohlcv["high"], ohlcv["low"], ohlcv["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    return atr / close * 100.0


def build_atr14_pct_1d_fallback(df_index_5m: pd.DatetimeIndex) -> pd.Series:
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
    df = df.sort_index()
    assert isinstance(df.index, pd.DatetimeIndex)

    # ベース系 (新規生成・5m close を各 TF に resample)
    close_5m = df["close"].astype(float)
    base_cols: dict[str, pd.Series] = {}
    for tf in TF_LIST:
        if tf == "5m":
            close_tf = close_5m.copy()
        else:
            close_tf = close_5m.resample(TF_RESAMPLE_RULE[tf], label="right", closed="right").last()
        log_ret = np.log(close_tf / close_tf.shift(1))
        rol_vol = log_ret.rolling(ROLLING_VOL_WINDOW).std()
        if tf != "5m":
            log_ret = log_ret.reindex(close_5m.index, method="ffill")
            rol_vol = rol_vol.reindex(close_5m.index, method="ffill")
        base_cols[f"log_returns__{tf}"] = log_ret
        base_cols[f"rolling_volatility__{tf}"] = rol_vol
    X_base = pd.DataFrame(base_cols, index=close_5m.index)

    # 既存指標 (atr14_pct__1d 除く)
    existing_cols: list[str] = []
    for ind in EXISTING_INDICATORS:
        for tf in TF_LIST:
            if ind == "atr14_pct" and tf == ATR_FALLBACK_TF:
                continue
            existing_cols.append(f"{ind}__{tf}")
    missing = [c for c in existing_cols if c not in df.columns]
    if missing:
        sys.exit(f"ABORT: missing columns: {missing[:5]}")
    X_existing = df[existing_cols].astype(float)
    X_existing[f"atr14_pct__{ATR_FALLBACK_TF}"] = build_atr14_pct_1d_fallback(df.index)

    # 並び順整列 (= 設計書 §2.9 カテゴリ → 指標 → 時間軸)
    ordered_cols = [f"{b}__{tf}" for b in BASE_INDICATORS_NEW + EXISTING_INDICATORS for tf in TF_LIST]
    X = pd.concat([X_base, X_existing], axis=1)[ordered_cols]
    assert X.shape[1] == 84
    return X


def apply_hysteresis(states: np.ndarray, n: int = HYSTERESIS_N) -> np.ndarray:
    """連続 n 回同判定で切替 (= 設計書 §5.2 擬似コード整合)。

    確定状態の初期値は -1 (= 未確定)。最初に n 連続が揃った時点で初期確定。
    切替も連続 n 回別判定が揃った時点で起こる。
    """
    out = np.full(len(states), -1, dtype=int)
    current = -1
    history: list[int] = []
    for i, raw in enumerate(states):
        history.append(int(raw))
        if len(history) > n:
            history.pop(0)
        if len(history) == n and len(set(history)) == 1:
            current = history[0]
        out[i] = current
    return out


def main() -> int:
    for p in [HMM_PATH, SCALER_PATH, LABELS_JSON, SUMMARY_JSON, INPUT_PARQUET, INPUT_OHLCV_CSV, INDEX_JSON]:
        if not p.exists():
            sys.exit(f"ABORT: missing input: {p}")

    print(f"[1/5] loading artifacts ...")
    hmm = joblib.load(HMM_PATH)
    scaler = joblib.load(SCALER_PATH)
    labels_data = json.loads(LABELS_JSON.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    state_to_label_jp = {int(k): v for k, v in labels_data["state_to_label"].items()}
    print(f"    state_to_label_jp: {state_to_label_jp}")

    print(f"[2/5] loading parquet + building 84-col matrix ...")
    df = pd.read_parquet(INPUT_PARQUET)
    X_5m = build_input_matrix(df)
    X_1h = X_5m.resample("1h", label="right", closed="right").last()
    X = X_1h.dropna()
    print(f"    1h grid after NaN drop: {X.shape}")

    print(f"[3/5] predicting states (HMM Viterbi) ...")
    X_scaled = scaler.transform(X.values)
    raw_states = hmm.predict(X_scaled)
    print(f"    raw state distribution: {dict(zip(*np.unique(raw_states, return_counts=True)))}")

    print(f"[4/5] applying hysteresis (n={HYSTERESIS_N}) + mapping to labels ...")
    confirmed_states = apply_hysteresis(raw_states, n=HYSTERESIS_N)

    def map_label(s: int) -> str:
        if s < 0:
            return "range"  # 未確定は range 扱い (= 視認チェック上は中立的)
        jp = state_to_label_jp.get(s, "レンジ")
        return LABEL_JP_TO_EN[jp]

    regime_labels = [map_label(s) for s in confirmed_states]

    # CSV 出力 (= datetime_utc + regime・1h 粒度・デバッグ用)
    out_df = pd.DataFrame({
        "datetime_utc": X.index.tz_localize("UTC") if X.index.tz is None else X.index,
        "regime": regime_labels,
    })
    PROTO_DIR.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False)
    print(f"    saved: {OUT_CSV} ({len(out_df)} rows)")

    # ===== ダッシュボードフロント (= app.js) が期待する compact array 形式 JSON 出力 =====
    # 各行 = [ts_ms, close_int, predicted_label, human_label] (human は工程 1 では空文字)
    close_5m_full = df["close"].astype(float).sort_index()
    close_1h_full = close_5m_full.resample("1h", label="right", closed="right").last()
    close_1h = close_1h_full.reindex(X.index).ffill().round().astype(int)
    ts_ms_1h = (X.index.astype("int64") // 10**6).tolist()
    rows_1h = [
        [int(ts), int(c), str(reg), ""]
        for ts, c, reg in zip(ts_ms_1h, close_1h.tolist(), regime_labels)
    ]
    pred_1h_path = PROTO_DIR / f"predictions_{VERSION}_1h.json"
    pred_1h_path.write_text(
        json.dumps({"version": VERSION, "granularity": "1h", "rows": rows_1h},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"    saved: {pred_1h_path.name} ({len(rows_1h)} rows)")

    # 1d 集約: 24h 内最頻 regime + 日次終値
    df_1h = pd.DataFrame(
        {"close": close_1h.values, "regime": regime_labels, "date": X.index.normalize()},
        index=X.index,
    )
    daily_pred = df_1h.groupby("date").agg(
        close=("close", "last"),
        regime=("regime", lambda s: s.value_counts().idxmax()),
    )
    ts_ms_1d = (daily_pred.index.astype("int64") // 10**6).tolist()
    rows_1d = [
        [int(ts), int(c), str(reg), ""]
        for ts, c, reg in zip(
            ts_ms_1d, daily_pred["close"].tolist(), daily_pred["regime"].tolist()
        )
    ]
    pred_1d_path = PROTO_DIR / f"predictions_{VERSION}_1d.json"
    pred_1d_path.write_text(
        json.dumps({"version": VERSION, "granularity": "1d", "rows": rows_1d},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"    saved: {pred_1d_path.name} ({len(rows_1d)} rows)")

    # 分布計算
    counts = out_df["regime"].value_counts().to_dict()
    total = len(out_df)
    distribution = {
        lbl: {"count": int(counts.get(lbl, 0)),
              "pct": round(counts.get(lbl, 0) / total * 100, 2)}
        for lbl in ["range", "uptrend", "downtrend"]
    }
    print(f"    distribution: {distribution}")

    print(f"[5/5] updating index.json (= v15 を prototypes に追記) ...")
    index_obj = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    # 既存 v15 があれば置換
    index_obj["prototypes"] = [p for p in index_obj["prototypes"] if p.get("version") != VERSION]
    fold_results = summary.get("fold_results", [])
    new_entry = {
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "spec": {
            "method": "hmm_unsupervised_step1",
            "design_doc": ".claude/memory/step1_regime_design.md v2.2",
            "n_components": summary["hmm_hyperparams"]["n_components"],
            "covariance_type": summary["hmm_hyperparams"]["covariance_type"],
            "features": "14 indicators × 6 TFs = 84 dims (§2.2)",
            "rolling_vol_window": ROLLING_VOL_WINDOW,
            "hysteresis_bars": HYSTERESIS_N,
            "output_granularity": "1h",
            "label_tf": labels_data["label_tf"],
            "sanity_check_passed": labels_data["sanity_check_passed"],
        },
        "distribution": distribution,
        "evaluation": {
            "method": "walk_forward_purged_kfold",
            "n_folds": len(fold_results),
            "mean_log_likelihood_test": round(
                float(np.mean([f["log_likelihood_test"] for f in fold_results])), 2
            ) if fold_results else None,
            "mean_avg_dwell_hours_test": round(
                float(np.mean([f["avg_dwell_hours_test"] for f in fold_results])), 2
            ) if fold_results else None,
        },
    }
    index_obj["prototypes"].append(new_entry)
    INDEX_JSON.write_text(
        json.dumps(index_obj, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"    index.json updated: {VERSION} appended (total {len(index_obj['prototypes'])} prototypes)")

    print(f"[DONE] dashboard ready. Start server with:")
    print(f"    python scripts/dashboard/dashboard_server.py")
    print(f"    → http://localhost:8765/index.html → ⑪ レジーム試作 → {VERSION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
