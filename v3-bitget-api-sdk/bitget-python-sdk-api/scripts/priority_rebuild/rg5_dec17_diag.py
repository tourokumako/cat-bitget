"""rg5_dec17_diag.py — read-only 診断（診断レーン・CSV/score 出力なし・print のみ）

まこさん指摘 2025-12-17 05:20/09:35/10:00「この辺はすべて下弦でエントリーしてる」を、
戦略の RG-v5 帯・実際の値動き（局所スイング）の両方に対して照合し、
「下弦に見える」正体（RG-v5 帯 vs 大局スイングのズレ／表示帯とのズレ）を特定する。
"""
import sys, pathlib
import numpy as np
import pandas as pd
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 30)

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import e37_range_scalp as e37

BASE = HERE.parent.parent
CANDLE = BASE / "data" / "BTCUSDT-5m-2024-09-01_2026-02-28_slice_V9FULL_safe.csv"
TRADES = BASE / "results" / "priority_rebuild" / "ratchet" / "trades_e37_range_scalp_v24_044_score.csv"

df = pd.read_csv(CANDLE)
df["ts"] = pd.to_datetime(df["timestamp"])
df = df.reset_index(drop=True)
df = e37._apply_rg5_to_5m(df)
df["ts5"] = df["ts"].dt.floor("5min")

tr = pd.read_csv(TRADES)
tr["entry_time"] = pd.to_datetime(tr["entry_time"])
day = tr[(tr["entry_time"] >= "2025-12-17") & (tr["entry_time"] < "2025-12-18")].copy()
day = day.sort_values("entry_time")
print(f"[2025-12-17 のエントリー] {len(day)} 行（fill 単位）")
print(day[["entry_time","exit_time","add_count","entry_price","exit_price","exit_reason",
           "stoch_k_at_entry","atr_14","box_W_pct_at_entry","mfe_usd","mae_usd","net_usd"]].to_string(index=False))

# --- RG-v5 帯 + 局所スイング（±12h の close 高安）を各エントリーに付与 ---
d = df.set_index("ts5")
print(f"\n[各エントリーの帯 vs 局所スイング]（pos: 1=上端res_lo / 0=下端sup_hi）")
for _, r in day.iterrows():
    t = pd.Timestamp(r["entry_time"]).floor("5min")
    if t not in d.index:
        print(f"  {t} … candle 無し"); continue
    row = d.loc[t]
    ep = float(r["entry_price"])
    res_lo, res_hi = float(row["v11_res_lo"]), float(row["v11_res_hi"])
    sup_lo, sup_hi = float(row["v11_sup_lo"]), float(row["v11_sup_hi"])
    chan = res_lo - sup_hi
    pos = (ep - sup_hi)/chan if chan > 0 else float("nan")
    # 局所スイング（±12h の close 高安＝まこさんが目視する「大局レンジ」の近似）
    w = df[(df["ts5"] >= t - pd.Timedelta(hours=12)) & (df["ts5"] <= t + pd.Timedelta(hours=12))]
    lo12, hi12 = w["low"].min(), w["high"].max()
    pos12 = (ep - lo12)/(hi12 - lo12) if hi12 > lo12 else float("nan")
    # 過去12h 高安（未来を見ない大局位置）
    wp = df[(df["ts5"] >= t - pd.Timedelta(hours=12)) & (df["ts5"] <= t)]
    loP, hiP = wp["low"].min(), wp["high"].max()
    posP = (ep - loP)/(hiP - loP) if hiP > loP else float("nan")
    print(f"  {t}  entry={ep:.1f}  range_ok={bool(row['range_ok_v11'])} uptrend={bool(row['rg5_uptrend'])}")
    print(f"     RG-v5帯: sup[{sup_lo:.0f}-{sup_hi:.0f}] res[{res_lo:.0f}-{res_hi:.0f}] 幅={(res_lo-sup_hi)/ep*100:.2f}%  → pos(RG-v5)={pos:.2f}")
    print(f"     ±12h スイング: [{lo12:.0f}-{hi12:.0f}] 幅={(hi12-lo12)/ep*100:.2f}%  → pos(±12h)={pos12:.2f}")
    print(f"     過去12h スイング: [{loP:.0f}-{hiP:.0f}] 幅={(hiP-loP)/ep*100:.2f}%  → pos(過去12h)={posP:.2f}")

# --- 3点周辺の 5分足（値動きを直接見る） ---
for tgt in ["2025-12-17 05:20", "2025-12-17 09:35", "2025-12-17 10:00"]:
    t = pd.Timestamp(tgt)
    w = df[(df["ts5"] >= t - pd.Timedelta(minutes=60)) & (df["ts5"] <= t + pd.Timedelta(minutes=90))]
    print(f"\n[{tgt} 周辺の 5分足（-60分〜+90分）]")
    print(w[["ts5","open","high","low","close","v11_res_lo","v11_res_hi","v11_sup_hi","range_ok_v11","rg5_uptrend"]].to_string(index=False))
print("\n[done] read-only 診断")
