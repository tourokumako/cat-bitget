"""scripts/regime/regime_classifier_prototype.py — regime 判定試作版 v4

v3 → v4 変更点（v3 が視認 OK・一致率横ばいを受けて）:
- ヒステリシスのみ変更: 1h → 2h
- 期待効果: 切替頻度↓ → 持続時間↑ → 肉眼ラベル（日単位ベース）との一致率↑
- 取引平均保有 60-130 分との整合では 2h の方が安全（WORKFLOW §B 持続条件）
- 統合ルール・指標・出力粒度は v3 と同一
- 出力: dashboard/regime_prototype/labels_v4.csv + charts_v4/<period>.png + meta_v4.json
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV       = _ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
HUMAN_CSV       = _ROOT / "data" / "regime_ground_truth_daily_human.csv"
OUT_DIR         = _ROOT / "dashboard" / "regime_prototype"
OUT_LABELS_CSV  = OUT_DIR / "labels_v4.csv"
OUT_CHART_DIR   = OUT_DIR / "charts_v4"
OUT_META_JSON   = OUT_DIR / "meta_v4.json"
INDEX_JSON      = OUT_DIR / "index.json"
VERSION         = "v4"

H4_MA50_LOOKBACK  = 5
H4_MA50_FLAT_PCT  = 0.003
H4_ADX_STRONG     = 25.0
H1_MA20_LOOKBACK  = 10
H1_MA20_FLAT_PCT  = 0.002
M15_DI_MARGIN     = 1.0
HYSTERESIS_HOURS  = 2

CHART_PERIODS = [
    ("2021Q3_early_uptrend",      "2021-07-01", "2021-09-30"),
    ("2022Q2_bear_start",         "2022-04-01", "2022-06-30"),
    ("2023spring_range",          "2023-03-01", "2023-05-31"),
    ("2024Q1_bull",               "2024-01-01", "2024-03-31"),
    ("2025-12_to_2026-02_recent", "2025-12-01", "2026-02-28"),
]


def load_5m(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["dt"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.set_index("dt").sort_index()
    return pd.DataFrame({
        "open":  df["open"].astype(float),
        "high":  df["high"].astype(float),
        "low":   df["low"].astype(float),
        "close": df["close"].astype(float),
    })


def resample_ohlc(df_5m: pd.DataFrame, rule: str) -> pd.DataFrame:
    return df_5m.resample(rule, label="right", closed="right").agg({
        "open": "first", "high": "max", "low": "min", "close": "last"
    }).dropna()


def adx_di(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    high, low, close = df["high"], df["low"], df["close"]
    up   = high.diff()
    down = -low.diff()
    plus_dm  = pd.Series(np.where((up > down) & (up > 0), up, 0.0),     index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)
    tr = pd.concat([
        (high - low),
        (high - close.shift(1)).abs(),
        (low  - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    atr      = tr.rolling(period, min_periods=period).mean()
    plus_di  = 100 * plus_dm.rolling(period,  min_periods=period).mean() / atr
    minus_di = 100 * minus_dm.rolling(period, min_periods=period).mean() / atr
    dx       = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return pd.DataFrame({
        "adx":      dx.rolling(period, min_periods=period).mean(),
        "plus_di":  plus_di,
        "minus_di": minus_di,
    })


def slope_dir(s: pd.Series, lookback: int, flat_pct: float) -> pd.Series:
    base = s.shift(lookback)
    rel  = (s - base) / base
    out  = pd.Series("flat", index=s.index, dtype=object)
    out[rel >  flat_pct] = "up"
    out[rel < -flat_pct] = "down"
    return out


def build_layers(df_5m: pd.DataFrame) -> pd.DataFrame:
    h1  = resample_ohlc(df_5m, "1H")
    h4  = resample_ohlc(df_5m, "4H")
    m15 = resample_ohlc(df_5m, "15min")

    h4_indi    = adx_di(h4, 14)
    h4_ma50    = h4["close"].rolling(50, min_periods=50).mean()
    h4_dir     = slope_dir(h4_ma50, H4_MA50_LOOKBACK, H4_MA50_FLAT_PCT)
    h4_strong  = (h4_indi["adx"] >= H4_ADX_STRONG)

    h1_ma20    = h1["close"].rolling(20, min_periods=20).mean()
    h1_dir     = slope_dir(h1_ma20, H1_MA20_LOOKBACK, H1_MA20_FLAT_PCT)

    m15_indi   = adx_di(m15, 14)
    m15_dir    = pd.Series("flat", index=m15.index, dtype=object)
    diff       = m15_indi["plus_di"] - m15_indi["minus_di"]
    m15_dir[diff >  M15_DI_MARGIN] = "up"
    m15_dir[diff < -M15_DI_MARGIN] = "down"

    base = pd.DataFrame(index=h1.index)
    base["h4_dir"]    = h4_dir.reindex(base.index,    method="ffill")
    base["h4_strong"] = h4_strong.reindex(base.index, method="ffill").fillna(False)
    base["h1_dir"]    = h1_dir
    base["m15_dir"]   = m15_dir.reindex(base.index,   method="ffill")
    return base


def integrate(layers: pd.DataFrame) -> pd.Series:
    """v3+: 上位 4h trend (ADX≥25) AND (1h 一致 OR 15m 一致) で trend 確定・それ以外は range。"""
    h4_up = (layers["h4_dir"] == "up")   & layers["h4_strong"]
    h4_dn = (layers["h4_dir"] == "down") & layers["h4_strong"]
    cond_up = h4_up & ((layers["h1_dir"] == "up")   | (layers["m15_dir"] == "up"))
    cond_dn = h4_dn & ((layers["h1_dir"] == "down") | (layers["m15_dir"] == "down"))
    out = pd.Series("range", index=layers.index, dtype=object)
    out[cond_up] = "uptrend"
    out[cond_dn] = "downtrend"
    return out


def hysteresis(series: pd.Series, hold_hours: int) -> pd.Series:
    out = series.copy()
    confirmed  = series.iloc[0]
    streak_val = series.iloc[0]
    streak_len = 1
    out.iloc[0] = confirmed
    for i in range(1, len(series)):
        v = series.iloc[i]
        if v == streak_val:
            streak_len += 1
        else:
            streak_val = v
            streak_len = 1
        if streak_len >= hold_hours and v != confirmed:
            confirmed = v
        out.iloc[i] = confirmed
    return out


def render_chart(df_5m: pd.DataFrame, labels: pd.Series, name: str, start: str, end: str, out_path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    h1  = resample_ohlc(df_5m, "1H").loc[start:end]
    lab = labels.loc[start:end]
    if h1.empty or lab.empty:
        print(f"[chart] skip {name} (empty range)")
        return

    fig, ax = plt.subplots(figsize=(20, 6))
    ax.plot(h1.index, h1["close"], color="black", linewidth=0.7)

    color_map = {"uptrend": "#90ee90", "downtrend": "#ffb0b0", "range": "#dcdcdc"}
    cur       = lab.iloc[0]
    seg_start = lab.index[0]
    for i in range(1, len(lab)):
        if lab.iloc[i] != cur:
            ax.axvspan(seg_start, lab.index[i], color=color_map.get(cur, "#ffffff"), alpha=0.35)
            cur       = lab.iloc[i]
            seg_start = lab.index[i]
    ax.axvspan(seg_start, lab.index[-1], color=color_map.get(cur, "#ffffff"), alpha=0.35)

    ax.set_title(f"BTC 1h chart + regime v4 - {name} ({start} - {end})")
    handles = [mpatches.Patch(color=c, alpha=0.35, label=k) for k, c in color_map.items()]
    ax.legend(handles=handles, loc="upper left")
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def load_human_labels(path: Path) -> pd.Series:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    return df.set_index("date")["label"].fillna("")


def _mode_label(s: pd.Series) -> str:
    vc = s.value_counts()
    return vc.index[0] if len(vc) else ""


def write_predictions(version: str, df_5m: pd.DataFrame, hourly_labels: pd.Series, human: pd.Series) -> dict:
    """3 粒度の predictions JSON を生成し、サマリ dict を返す。
    各行は compact array: [ts_ms, close_int, v4_label, human_label]
    """
    # broadcast: human (daily) → hourly / 5m
    hour_idx = hourly_labels.index
    day_norm_h = hour_idx.normalize()
    human_h = human.reindex(day_norm_h, method="ffill").fillna("").to_numpy()
    h1 = resample_ohlc(df_5m, "1H").reindex(hour_idx, method="ffill")
    close_h = h1["close"].round().astype(int).to_numpy()

    # ----- 1h JSON -----
    rows_1h = [
        [int(t.timestamp() * 1000), int(c), v, h]
        for t, c, v, h in zip(hour_idx, close_h, hourly_labels.to_numpy(), human_h)
    ]
    pred_1h_path = OUT_DIR / f"predictions_{version}_1h.json"
    pred_1h_path.write_text(json.dumps({
        "version": version, "granularity": "1h",
        "rows": rows_1h
    }, ensure_ascii=False), encoding="utf-8")
    print(f"[save] {pred_1h_path.relative_to(_ROOT)}  rows={len(rows_1h):,}")

    # ----- 1d JSON (24h 最頻値) -----
    daily_pred = hourly_labels.groupby(hour_idx.normalize()).agg(_mode_label)
    daily_close = h1["close"].resample("1D").last().reindex(daily_pred.index)
    daily_human = human.reindex(daily_pred.index, method="ffill").fillna("")
    rows_1d = [
        [int(t.timestamp() * 1000), int(round(c)) if pd.notna(c) else 0, v, h]
        for t, c, v, h in zip(daily_pred.index, daily_close.to_numpy(),
                              daily_pred.to_numpy(), daily_human.to_numpy())
    ]
    pred_1d_path = OUT_DIR / f"predictions_{version}_1d.json"
    pred_1d_path.write_text(json.dumps({
        "version": version, "granularity": "1d",
        "rows": rows_1d
    }, ensure_ascii=False), encoding="utf-8")
    print(f"[save] {pred_1d_path.relative_to(_ROOT)}  rows={len(rows_1d):,}")

    # ----- 5m JSON (per-month ファイル) -----
    pred_5m_dir = OUT_DIR / f"predictions_{version}_5m"
    pred_5m_dir.mkdir(parents=True, exist_ok=True)
    m5_v4  = hourly_labels.reindex(df_5m.index, method="ffill").fillna("")
    day_norm_5 = df_5m.index.normalize()
    m5_hu  = human.reindex(day_norm_5, method="ffill").fillna("")
    m5_close = df_5m["close"].round().astype(int)

    available_months = []
    for ym, idx in pd.Series(df_5m.index).groupby(df_5m.index.strftime("%Y-%m")):
        sub_idx = idx.values  # numpy datetime64
        # filter via boolean mask
        mask = df_5m.index.strftime("%Y-%m") == ym
        ts_arr   = df_5m.index[mask]
        close_a  = m5_close.values[mask]
        v4_a     = m5_v4.values[mask]
        hu_a     = m5_hu.values[mask]
        rows = [
            [int(t.timestamp() * 1000), int(c), str(v), str(h)]
            for t, c, v, h in zip(ts_arr, close_a, v4_a, hu_a)
        ]
        out_path = pred_5m_dir / f"{ym}.json"
        out_path.write_text(json.dumps({
            "version": version, "granularity": "5m", "year_month": ym,
            "rows": rows
        }, ensure_ascii=False), encoding="utf-8")
        available_months.append(ym)
    print(f"[save] {pred_5m_dir.relative_to(_ROOT)}/  files={len(available_months)}")

    # ----- accuracy summary -----
    def _acc(pred_arr, hum_arr) -> dict:
        valid = (hum_arr != "") & (pred_arr != "")
        n = int(valid.sum())
        hit = int((pred_arr[valid] == hum_arr[valid]).sum())
        return {"n": n, "hit": hit, "accuracy": round(hit / n, 4) if n else None}

    acc_1h = _acc(hourly_labels.to_numpy(), human_h)
    acc_1d = _acc(daily_pred.to_numpy(), daily_human.to_numpy())

    return {
        "available_months": available_months,
        "acc_1h": acc_1h,
        "acc_1d": acc_1d,
    }


def update_index(summary: dict, dist: dict, total: int) -> None:
    if INDEX_JSON.exists():
        index = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    else:
        index = {"prototypes": [], "available_months": []}
    spec = {
        "upper":  "4h MA50 slope (5 bars ≒ 20h, ±0.3% flat) AND 4h ADX14 ≥ 25",
        "middle": "1h MA20 slope (10 bars ≒ 10h, ±0.2% flat)",
        "lower":  "15m DI+/DI- (margin 1.0)",
        "integration": "4h trend (ADX≥25) AND (1h or 15m agrees) confirms; otherwise range",
        "hysteresis_hours": HYSTERESIS_HOURS,
        "output_granularity": "1h",
    }
    new_entry = {
        "version":      VERSION,
        "generated_utc": pd.Timestamp.utcnow().isoformat(),
        "spec":         spec,
        "distribution": {k: {"count": int(v), "pct": round(v / total * 100, 2)} for k, v in dist.items()},
        "accuracy":     {"1h": summary["acc_1h"], "1d": summary["acc_1d"]},
    }
    # 既存 v4 を置換
    index["prototypes"] = [p for p in index["prototypes"] if p["version"] != VERSION]
    index["prototypes"].append(new_entry)
    index["prototypes"].sort(key=lambda p: p["version"])
    index["available_months"] = summary["available_months"]
    INDEX_JSON.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[index] {INDEX_JSON.relative_to(_ROOT)}  prototypes={len(index['prototypes'])}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CHART_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[load] {INPUT_CSV.name}")
    df_5m = load_5m(INPUT_CSV)
    print(f"[load] rows={len(df_5m):,}  {df_5m.index[0]} 〜 {df_5m.index[-1]}")
    print(f"[load] {HUMAN_CSV.name}")
    human = load_human_labels(HUMAN_CSV)
    print(f"[load] human rows={len(human):,}  {human.index[0]} 〜 {human.index[-1]}")

    layers = build_layers(df_5m)
    raw    = integrate(layers)
    final  = hysteresis(raw, HYSTERESIS_HOURS)

    out_df = pd.DataFrame({"regime": final})
    out_df.index.name = "datetime_utc"
    out_df.to_csv(OUT_LABELS_CSV)
    print(f"[save] {OUT_LABELS_CSV.relative_to(_ROOT)}  rows={len(out_df):,}")
    dist  = final.value_counts().to_dict()
    total = sum(dist.values())
    print("[dist] " + "  ".join(f"{k}={v:,}({v/total*100:.1f}%)" for k, v in dist.items()))

    summary = write_predictions(VERSION, df_5m, final, human)
    update_index(summary, dist, total)

    print(f"[acc 1h] {summary['acc_1h']}")
    print(f"[acc 1d] {summary['acc_1d']}")
    print("[done]")


if __name__ == "__main__":
    main()
