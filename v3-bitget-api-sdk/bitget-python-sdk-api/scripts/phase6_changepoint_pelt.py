"""phase6_changepoint_pelt.py

段階6: 変化点検知でレジームを推定する。
- 入力: data/BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv（5m足5年）
- 1日足リサンプル → log return の累積系列から変化点を検出
- segment 平均日次リターンに応じて UP/DOWN/RANGE をルールでラベリング
- 候補B 判定: UP > +1.22% / DOWN < -0.82% / RANGE |.| < 0.34% かつ 継続中央値 ∈ [3, 30]日

CLI:
    python scripts/phase6_changepoint_pelt.py [--algo pelt|binseg|window] [--penalty auto|N]

出力:
    results/phase6_pelt_segments.csv
    results/phase6_pelt_summary.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import ruptures as rpt


REPO = Path(__file__).resolve().parent.parent
CSV_5M = REPO / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"
OUT_CSV = REPO / "results" / "phase6_pelt_segments.csv"
OUT_JSON = REPO / "results" / "phase6_pelt_summary.json"

# 候補B 閾値（phase0_return_distribution.json より・%単位）
UP_MIN = 1.2212616859789105
DOWN_MAX = -0.8215950246819278  # mean - 0.3*std
RANGE_ABS = 0.3404761351101398   # 0.1*std

DUR_MIN_DAYS = 3
DUR_MAX_DAYS = 30


def load_daily(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp")
    daily = df["close"].resample("1D").last().to_frame("close").dropna()
    daily["log_close"] = np.log(daily["close"])
    daily["log_ret"] = daily["log_close"].diff()
    daily["pct_ret"] = daily["close"].pct_change() * 100.0
    daily = daily.dropna()
    return daily


def detect_changepoints(signal: np.ndarray, algo: str, penalty) -> list[int]:
    """ruptures で変化点インデックスのリストを返す。終端 n は含む。"""
    n = len(signal)
    if algo == "pelt":
        model = rpt.Pelt(model="rbf").fit(signal)
        bkps = model.predict(pen=penalty)
    elif algo == "binseg":
        model = rpt.Binseg(model="rbf").fit(signal)
        # binseg は n_bkps か pen どちらか。pen を使う。
        bkps = model.predict(pen=penalty)
    elif algo == "window":
        model = rpt.Window(width=20, model="rbf").fit(signal)
        bkps = model.predict(pen=penalty)
    else:
        raise ValueError(f"unknown algo: {algo}")
    if bkps[-1] != n:
        bkps.append(n)
    return bkps


def label_segment(mean_ret: float) -> str:
    if mean_ret >= UP_MIN:
        return "UPTREND"
    if mean_ret <= DOWN_MAX:
        return "DOWNTREND"
    if abs(mean_ret) < RANGE_ABS:
        return "RANGE"
    return "MIXED"  # 候補B いずれにも該当しない中間帯


def build_segments(daily: pd.DataFrame, bkps: list[int]) -> pd.DataFrame:
    rows = []
    start = 0
    for end in bkps:
        seg = daily.iloc[start:end]
        if len(seg) == 0:
            start = end
            continue
        mean_ret = seg["pct_ret"].mean()
        rows.append(
            {
                "start_date": seg.index[0].date().isoformat(),
                "end_date": seg.index[-1].date().isoformat(),
                "duration_days": len(seg),
                "mean_pct_ret": mean_ret,
                "median_pct_ret": seg["pct_ret"].median(),
                "std_pct_ret": seg["pct_ret"].std(),
                "label": label_segment(mean_ret),
            }
        )
        start = end
    return pd.DataFrame(rows)


def evaluate(seg_df: pd.DataFrame) -> dict:
    summary = {
        "n_segments": int(len(seg_df)),
        "by_label": {},
        "criteria_B": {
            "UPTREND_min_mean_ret": UP_MIN,
            "DOWNTREND_max_mean_ret": DOWN_MAX,
            "RANGE_abs_mean_ret": RANGE_ABS,
            "duration_min_days": DUR_MIN_DAYS,
            "duration_max_days": DUR_MAX_DAYS,
        },
    }
    for label in ["UPTREND", "DOWNTREND", "RANGE", "MIXED"]:
        sub = seg_df[seg_df["label"] == label]
        if len(sub) == 0:
            summary["by_label"][label] = {"count": 0}
            continue
        durations = sub["duration_days"].astype(int)
        in_window = (durations >= DUR_MIN_DAYS) & (durations <= DUR_MAX_DAYS)
        summary["by_label"][label] = {
            "count": int(len(sub)),
            "duration_median": float(durations.median()),
            "duration_mean": float(durations.mean()),
            "duration_min": int(durations.min()),
            "duration_max": int(durations.max()),
            "in_window_ratio": float(in_window.mean()),
            "mean_pct_ret_avg": float(sub["mean_pct_ret"].mean()),
        }

    # 候補B 合格判定
    pass_uptrend = (
        summary["by_label"].get("UPTREND", {}).get("count", 0) > 0
        and summary["by_label"]["UPTREND"]["mean_pct_ret_avg"] >= UP_MIN
        and DUR_MIN_DAYS <= summary["by_label"]["UPTREND"]["duration_median"] <= DUR_MAX_DAYS
    )
    pass_downtrend = (
        summary["by_label"].get("DOWNTREND", {}).get("count", 0) > 0
        and summary["by_label"]["DOWNTREND"]["mean_pct_ret_avg"] <= DOWN_MAX
        and DUR_MIN_DAYS <= summary["by_label"]["DOWNTREND"]["duration_median"] <= DUR_MAX_DAYS
    )
    pass_range = (
        summary["by_label"].get("RANGE", {}).get("count", 0) > 0
        and abs(summary["by_label"]["RANGE"]["mean_pct_ret_avg"]) < RANGE_ABS
        and DUR_MIN_DAYS <= summary["by_label"]["RANGE"]["duration_median"] <= DUR_MAX_DAYS
    )
    summary["criteria_B_pass"] = {
        "UPTREND": bool(pass_uptrend),
        "DOWNTREND": bool(pass_downtrend),
        "RANGE": bool(pass_range),
        "ALL": bool(pass_uptrend and pass_downtrend and pass_range),
    }
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--algo", default="pelt", choices=["pelt", "binseg", "window"])
    ap.add_argument(
        "--penalty",
        default="auto",
        help="auto: BIC近似(log(n)*sigma^2) / 数値: 直接指定",
    )
    ap.add_argument("--out-suffix", default="", help="出力ファイル末尾につけるサフィックス")
    args = ap.parse_args()

    print(f"[phase6] load: {CSV_5M.name}")
    daily = load_daily(CSV_5M)
    print(f"[phase6] daily rows: {len(daily)} ({daily.index[0].date()} 〜 {daily.index[-1].date()})")

    signal = daily["log_ret"].values.astype(float)
    sigma2 = float(np.var(signal))
    n = len(signal)

    if args.penalty == "auto":
        penalty = np.log(n) * sigma2  # BIC 近似
    else:
        penalty = float(args.penalty)
    print(f"[phase6] algo={args.algo} penalty={penalty:.6f} sigma2={sigma2:.6f} n={n}")

    bkps = detect_changepoints(signal, args.algo, penalty)
    print(f"[phase6] changepoints: {len(bkps)} (incl. terminal)")

    seg_df = build_segments(daily, bkps)
    suffix = args.out_suffix
    csv_out = OUT_CSV.with_name(OUT_CSV.stem + suffix + OUT_CSV.suffix)
    json_out = OUT_JSON.with_name(OUT_JSON.stem + suffix + OUT_JSON.suffix)
    seg_df.to_csv(csv_out, index=False)
    print(f"[phase6] segments csv -> {csv_out}")

    summary = evaluate(seg_df)
    summary["params"] = {
        "algo": args.algo,
        "penalty": penalty,
        "sigma2": sigma2,
        "n_days": n,
    }
    json_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"[phase6] summary json -> {json_out}")

    print("\n=== summary ===")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
