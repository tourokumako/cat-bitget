"""inspect_v10_misclassify.py — v10 が真逆判定を出した区間の特徴量を抜き出す

まこさん指定区間で、4h バーごとに v10 予測ラベルと全特徴量値を表示。
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from regime_inverter import build_features, load_ohlcv

BASE = Path(__file__).resolve().parents[2]


def load_v10_pred() -> pd.DataFrame:
    p = BASE / "dashboard/regime_prototype/predictions_v10_1h.json"
    raw = json.loads(p.read_text())
    rows = raw["rows"]  # [ts_ms, close, pred, human]
    df = pd.DataFrame(rows, columns=["ts_ms", "close", "pred", "human"])
    df["ts"] = pd.to_datetime(df["ts_ms"], unit="ms")
    return df.set_index("ts")[["close", "pred", "human"]]


def show_window(df_4h: pd.DataFrame, feats: pd.DataFrame, pred1h: pd.DataFrame,
                start: str, end: str) -> None:
    s = pd.Timestamp(start)
    e = pd.Timestamp(end)
    print(f"\n{'=' * 88}")
    print(f"区間: {start}  〜  {end}")
    print(f"{'=' * 88}")

    bars = df_4h.loc[s:e]
    f = feats.loc[bars.index]

    # 4h ごとに 1h の予測（4h floor で対応）
    pred_at_bar = []
    for ts in bars.index:
        # その 4h バーが属する 1h 予測（先頭 1h）
        if ts in pred1h.index:
            pred_at_bar.append(pred1h.loc[ts, "pred"])
        else:
            pred_at_bar.append("?")

    cols = ["close_vs_ma20", "delta_close_vs_ma20_3b",
            "reversal_from_low_10b", "reversal_from_high_10b",
            "retrace_ratio_20b", "retrace_ratio_30b",
            "close_vs_ma50", "delta_close_vs_ma50_5b",
            "slope_2b", "adx14", "di_diff"]
    header = f"{'time':<17} {'close':>7} {'pred':>9}  " + "  ".join(f"{c:>14}" for c in cols)
    print(header)
    for ts, pred in zip(bars.index, pred_at_bar):
        close = bars.loc[ts, "close"]
        vals = "  ".join(f"{f.loc[ts, c]:>+14.4f}" if pd.notna(f.loc[ts, c]) else f"{'nan':>14}" for c in cols)
        print(f"{ts.strftime('%Y-%m-%d %H:%M'):<17} {close:>7.0f} {pred:>9}  {vals}")


def main() -> None:
    print("4h OHLCV 読み込み...")
    df_4h = load_ohlcv("4h")
    print(f"  {len(df_4h)} バー  {df_4h.index[0]} 〜 {df_4h.index[-1]}")

    print("特徴量計算（4h・全期間）...")
    feats = build_features(df_4h)

    print("v10 予測 JSON 読み込み...")
    pred1h = load_v10_pred()

    windows = [
        ("2026-03-04 16:00", "2026-03-05 16:00"),
        ("2026-03-10 12:00", "2026-03-11 04:00"),
        ("2026-02-05 20:00", "2026-02-07 00:00"),
    ]
    for s, e in windows:
        show_window(df_4h, feats, pred1h, s, e)


if __name__ == "__main__":
    main()
