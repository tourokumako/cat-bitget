"""
analyze_early_cut.py — 早期カットのTP_FILLED副作用確認
読み取り専用。結果CSVの上書きなし。

使い方:
  .venv/bin/python3 tools/analyze_early_cut.py
"""
import pandas as pd
import numpy as np

RESULT_CSV  = "results/replay_BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv"
CANDLES_CSV = "/Users/tachiharamasako/Documents/GitHub/cat-swing-sniper/data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv"
BAR_MIN     = 5

trades  = pd.read_csv(RESULT_CSV,  parse_dates=["entry_time", "exit_time"])
candles = pd.read_csv(CANDLES_CSV, parse_dates=["timestamp"])
candles = candles.set_index("timestamp").sort_index()

def pnl_at_t(row, t_min):
    """エントリーから t_min 後のバーの close ベース含み損益（USD）"""
    bars = candles.loc[row["entry_time"]:row["exit_time"]]
    idx = t_min // BAR_MIN
    if idx >= len(bars):
        return None  # 保有時間がt_minより短い
    close = float(bars["close"].iloc[idx])
    ep    = row["entry_price"]
    size  = row["size_btc"]
    if row["side"] == "LONG":
        return (close - ep) * size
    else:
        return (ep - close) * size

print("TP_FILLED / TIME_EXIT それぞれの T+60min PNL 分布を確認します\n")

for reason in ["TP_FILLED", "TIME_EXIT"]:
    sub = trades[trades["exit_reason"] == reason].copy()
    pnl60 = sub.apply(lambda r: pnl_at_t(r, 60), axis=1)
    sub["pnl_60"] = pnl60

    # hold < 60min のトレードは除外（そもそも60分前に決済済み）
    valid = sub[sub["pnl_60"].notna()].copy()
    short_hold = sub[sub["pnl_60"].isna()]

    print("=" * 60)
    print(f"【{reason}】 {len(sub)}件 (うち保有<60min: {len(short_hold)}件 → 除外)")
    print(f"  T+60min PNL が計算できる件数: {len(valid)}件")
    print()

    for thresh in [-5, -10, -15, -20]:
        cut = (valid["pnl_60"] < thresh).sum()
        pct = cut / len(valid) * 100 if len(valid) > 0 else 0
        net_sum = valid.loc[valid["pnl_60"] < thresh, "net_usd"].sum()
        print(f"  T+60min < -${abs(thresh)}: {cut}件 ({pct:.1f}%)  "
              f"現在のNET合計: ${net_sum:.1f}")
    print()

    # Priority別内訳（-$10閾値）
    thresh = -10
    cut_mask = valid["pnl_60"] < thresh
    print(f"  Priority別（T+60min < -$10）:")
    pri_grp = valid[cut_mask].groupby("priority").agg(
        件数=("net_usd", "count"),
        NET=("net_usd", "sum"),
        avgNET=("net_usd", "mean"),
    )
    if pri_grp.empty:
        print("    (なし)")
    else:
        print(pri_grp.to_string())
    print()

# ── シミュレーション: TP_FILLEDの誤カットを考慮した純改善額 ──────────
print("=" * 60)
print("【シミュレーション】T+60min <-$10 早期カットの純改善額")
print("=" * 60)
print()
print("  前提: カット時の損失 = T+60min時点のPNL（close近似）")
print()

te  = trades[trades["exit_reason"] == "TIME_EXIT"].copy()
tp  = trades[trades["exit_reason"] == "TP_FILLED"].copy()

te["pnl_60"] = te.apply(lambda r: pnl_at_t(r, 60), axis=1)
tp["pnl_60"] = tp.apply(lambda r: pnl_at_t(r, 60), axis=1)

te_valid = te[te["pnl_60"].notna()]
tp_valid = tp[tp["pnl_60"].notna()]

thresh = -10

# TIME_EXIT: カット対象
te_cut  = te_valid[te_valid["pnl_60"] < thresh]
te_save = te_cut["pnl_60"].sum() - te_cut["net_usd"].sum()  # 改善額

# TP_FILLED: 誤カット対象（本来TPに届くが早期カットされる）
tp_wrongcut = tp_valid[tp_valid["pnl_60"] < thresh]
tp_loss     = tp_wrongcut["pnl_60"].sum() - tp_wrongcut["net_usd"].sum()  # 損失額（負）

net_effect = te_save + tp_loss

print(f"  TIME_EXIT カット件数:      {len(te_cut)}件")
print(f"  TIME_EXIT 改善額:          +${te_save:.1f}")
print()
print(f"  TP_FILLED 誤カット件数:    {len(tp_wrongcut)}件")
print(f"  TP_FILLED 誤カットによる損失: ${tp_loss:.1f}")
print()
print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  純改善額（90日）:          ${net_effect:.1f}")
print(f"  純改善額（/day）:          ${net_effect/90:.2f}")
print()

# Priority別の内訳
print("  Priority別 誤カット内訳（TP_FILLED）:")
if len(tp_wrongcut) > 0:
    print(tp_wrongcut.groupby("priority").agg(
        誤カット件数=("net_usd","count"),
        失うTP利益=("net_usd","sum"),
        カット時損失=("pnl_60","sum"),
    ).to_string())
else:
    print("  (なし)")
