"""
analyze_time_exit.py — TIME_EXIT ポジションの価格パス分析
読み取り専用。結果CSVの上書きなし。

使い方:
  .venv/bin/python3 tools/analyze_time_exit.py
"""
import pandas as pd
import numpy as np

RESULT_CSV  = "results/replay_BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv"
CANDLES_CSV = "/Users/tachiharamasako/Documents/GitHub/cat-swing-sniper/data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv"
BAR_MIN     = 5  # 5分足

# ── データ読み込み ──────────────────────────────────────────
trades  = pd.read_csv(RESULT_CSV,  parse_dates=["entry_time", "exit_time"])
candles = pd.read_csv(CANDLES_CSV, parse_dates=["timestamp"])
candles = candles.set_index("timestamp").sort_index()

te = trades[trades["exit_reason"] == "TIME_EXIT"].copy()
print(f"TIME_EXIT 件数: {len(te)}件\n")

# ── 各トレードの価格パス解析 ────────────────────────────────
records = []
for _, row in te.iterrows():
    bars = candles.loc[row["entry_time"]:row["exit_time"]]
    if len(bars) < 2:
        continue

    ep    = row["entry_price"]
    side  = row["side"]
    size  = row["size_btc"]
    n     = len(bars)

    # バーごとの含み損益（close ベース近似）
    if side == "LONG":
        pnl_series = (bars["close"] - ep) * size
        fav_series = (bars["high"]  - ep) * size  # 有利方向
    else:
        pnl_series = (ep - bars["close"]) * size
        fav_series = (ep - bars["low"])   * size

    mfe_usd     = fav_series.clip(lower=0).max()
    mfe_bar_idx = int(fav_series.clip(lower=0).argmax())  # MFEを達成したバー番号
    mfe_pct     = mfe_bar_idx / (n - 1) if n > 1 else 0  # 保有時間の何%地点か

    # T+30/60/90min 時点のPNL
    def pnl_at(t_min):
        idx = t_min // BAR_MIN
        if idx < len(pnl_series):
            return float(pnl_series.iloc[idx])
        return float(pnl_series.iloc[-1])

    pnl_30  = pnl_at(30)
    pnl_60  = pnl_at(60)
    pnl_90  = pnl_at(90)
    pnl_120 = pnl_at(120)

    # パス分類
    if mfe_usd < 2.0 and mfe_pct < 0.2:
        path_type = "即逆行"       # 最初から逆行
    elif mfe_usd >= 2.0 and mfe_pct < 0.5:
        path_type = "前進後反転"   # 一度有利に動いた後に引き返した
    elif mfe_usd >= 2.0 and mfe_pct >= 0.5:
        path_type = "TP手前で失速" # 後半で最高値（TP未届き）
    else:
        path_type = "停滞"         # ほぼ動かず

    records.append({
        "priority":   row["priority"],
        "side":       side,
        "add_count":  row["add_count"],
        "hold_min":   row["hold_min"],
        "net_usd":    row["net_usd"],
        "mfe_usd":    mfe_usd,
        "mfe_pct":    mfe_pct,
        "pnl_30":     pnl_30,
        "pnl_60":     pnl_60,
        "pnl_90":     pnl_90,
        "pnl_120":    pnl_120,
        "path_type":  path_type,
        "adx":        row["adx_at_entry"],
        "bb_slope":   row["bb_mid_slope_at_entry"],
    })

df = pd.DataFrame(records)

# ── 1. パス分類サマリー ─────────────────────────────────────
print("=" * 60)
print("【1】TIME_EXIT パス分類（全体）")
print("=" * 60)
pt = df.groupby("path_type").agg(
    件数=("net_usd", "count"),
    NET=("net_usd", "sum"),
    avgNET=("net_usd", "mean"),
    avgMFE=("mfe_usd", "mean"),
    avgHold=("hold_min", "mean"),
).sort_values("NET")
print(pt.to_string())
print()

# ── 2. Priority別 パス分類 ──────────────────────────────────
print("=" * 60)
print("【2】Priority別 パス分類")
print("=" * 60)
for pri in sorted(df["priority"].unique()):
    sub = df[df["priority"] == pri]
    print(f"\n--- P{pri} ({len(sub)}件) ---")
    pt2 = sub.groupby("path_type").agg(
        件数=("net_usd", "count"),
        NET=("net_usd", "sum"),
        avgMFE=("mfe_usd", "mean"),
    ).sort_values("NET")
    print(pt2.to_string())

# ── 3. MFE分布（TIME_EXIT） ─────────────────────────────────
print("\n" + "=" * 60)
print("【3】MFE分布（TIME_EXIT）")
print("=" * 60)
bins = [0, 2, 5, 10, 20, 50, 999]
labels = ["<$2", "$2-5", "$5-10", "$10-20", "$20-50", "$50+"]
df["mfe_bin"] = pd.cut(df["mfe_usd"], bins=bins, labels=labels)
mfe_dist = df.groupby("mfe_bin", observed=True).agg(
    件数=("net_usd", "count"),
    NET=("net_usd", "sum"),
    avgHold=("hold_min", "mean"),
)
print(mfe_dist.to_string())

# ── 4. 早期カットシミュレーション ──────────────────────────
print("\n" + "=" * 60)
print("【4】早期カット シミュレーション（TIME_EXIT トレードのみ）")
print("=" * 60)
print("条件: T+Xmin時点で含み損 < -$N ならカット（close近似）")
print("  ※TP_FILLEDトレードへの影響は別途確認が必要\n")

# TP_FILLEDトレード数（参考）
tp_count = len(trades[trades["exit_reason"] == "TP_FILLED"])
print(f"参考: TP_FILLED件数 = {tp_count}件\n")

results_sim = []
for t_min in [30, 60, 90, 120]:
    col = f"pnl_{t_min}"
    for thresh in [-5, -10, -15, -20, -30]:
        mask = df[col] < thresh
        cut_count  = mask.sum()
        cut_net    = df.loc[mask, "net_usd"].sum()        # 現在の損失
        saved      = df.loc[mask, col].sum()              # カット時の損失（推定）
        improvement = saved - cut_net                     # 改善額（負→正なら改善）
        results_sim.append({
            "T+min":      t_min,
            "閾値":       f"<-${abs(thresh)}",
            "カット件数": int(cut_count),
            "現損失合計": round(cut_net, 1),
            "カット後損失": round(saved, 1),
            "改善額":     round(improvement, 1),
        })

sim_df = pd.DataFrame(results_sim)
print(sim_df.to_string(index=False))

# ── 5. Priority別 add_count × パス分類 ─────────────────────
print("\n" + "=" * 60)
print("【5】add_count別 MFE・パス（P22 / P23 集中確認）")
print("=" * 60)
for pri in [22, 23]:
    sub = df[df["priority"] == pri]
    if sub.empty:
        continue
    print(f"\n--- P{pri} ---")
    pt3 = sub.groupby(["add_count", "path_type"]).agg(
        件数=("net_usd", "count"),
        NET=("net_usd", "sum"),
        avgMFE=("mfe_usd", "mean"),
    )
    print(pt3.to_string())

# ── 6. 「即逆行」トレードの Entry 指標分布 ─────────────────
print("\n" + "=" * 60)
print("【6】「即逆行」トレードの Entry 指標")
print("=" * 60)
imm = df[df["path_type"] == "即逆行"]
if not imm.empty:
    print(f"件数: {len(imm)}")
    print(f"  ADX:      avg={imm['adx'].mean():.1f}  med={imm['adx'].median():.1f}")
    print(f"  bb_slope: avg={imm['bb_slope'].mean():.1f}  med={imm['bb_slope'].median():.1f}")
    print(f"  hold_min: avg={imm['hold_min'].mean():.1f}")
    print(f"\nPriority別:")
    print(imm.groupby("priority")[["adx","bb_slope","net_usd"]].mean().round(1).to_string())
