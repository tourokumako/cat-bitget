#!/usr/bin/env python3
"""e16_premap_analysis.py — E16 事前分析3本（E15棚上げ後の次レバー選定・学習期間のみ・採点不接触・2026-06-11）

実行: python3.13 scripts/priority_rebuild/e16_premap_analysis.py [boundary|adxyear|map]
  boundary = P23 閾値境界スキャン（1条件落ち帯別 net・typeonly CSV）
  adxyear  = ADX 50-60 帯の年別安定性
  map      = V9 全部入り5年の Priority×regime×年 全体地図
結果は ledger E16事前分析 / session_log_20260611 に記録済み。"""
import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "map"

if MODE == "boundary":
    import pandas as pd
    
    CSV = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/results/priority_rebuild/ratchet/p23_candidates_typeonly.csv"
    d = pd.read_csv(CSV)
    d["entry_time"] = pd.to_datetime(d["entry_time"])
    d = d[d["entry_time"] < pd.Timestamp("2025-01-01")].copy()          # 学習期間のみ（H8）
    d["gap"] = d["stoch_d_at_entry"] - d["stoch_k_at_entry"]
    
    c_gap   = d["gap"] > 0.3
    c_slope = d["bb_mid_slope_at_entry"] < -10.0
    c_adx   = (d["adx_at_entry"] >= 30.0) & (d["adx_at_entry"] < 50.0)
    c_atr   = d["atr_14"] >= 150.0
    c_high  = (d["adx_at_entry"] < 40.0) | (d["atr_14"] >= 200.0)
    conds = {"gap": c_gap, "slope": c_slope, "adx": c_adx, "atr": c_atr, "high_adx": c_high}
    
    full = c_gap & c_slope & c_adx & c_atr & c_high
    def stat(m, label):
        s = d[m]
        if len(s) == 0:
            print(f"{label:42s}      0件")
            return
        print(f"{label:42s} {len(s):6d}件  net計 ${s['net_usd'].sum():9.1f}  avg ${s['net_usd'].mean():6.2f}  勝率 {(s['net_usd']>0).mean()*100:4.1f}%")
    
    print(f"== 学習期間 typeonly 全候補: {len(d)}件  net計 ${d['net_usd'].sum():.1f}（独立sim・楽観・相対比較用）==")
    stat(full, "V9 full 通過（全条件AND）")
    print("\n== 1条件だけ落ち（他は全部通過）の帯別 ==")
    others = lambda k: pd.concat([v for kk, v in conds.items() if kk != k], axis=1).all(axis=1)
    
    o = others("adx")
    stat(o & (d.adx_at_entry >= 25) & (d.adx_at_entry < 30), "ADX 25-30（下に緩めると入る）")
    stat(o & (d.adx_at_entry >= 20) & (d.adx_at_entry < 25), "ADX 20-25")
    stat(o & (d.adx_at_entry < 20),                          "ADX <20")
    stat(o & (d.adx_at_entry >= 50) & (d.adx_at_entry < 60), "ADX 50-60（上に緩めると入る）")
    stat(o & (d.adx_at_entry >= 60),                         "ADX 60+")
    
    o = others("atr")
    stat(o & (d.atr_14 >= 100) & (d.atr_14 < 150),           "ATR 100-150（下に緩めると入る）")
    stat(o & (d.atr_14 < 100),                               "ATR <100")
    
    o = others("slope")
    stat(o & (d.bb_mid_slope_at_entry >= -10) & (d.bb_mid_slope_at_entry < -5), "bb傾き -10〜-5（緩めると入る）")
    stat(o & (d.bb_mid_slope_at_entry >= -5) & (d.bb_mid_slope_at_entry < 0),   "bb傾き -5〜0")
    stat(o & (d.bb_mid_slope_at_entry >= 0),                                    "bb傾き 0以上（上向き）")
    
    o = others("gap")
    stat(o & (d.gap > 0.1) & (d.gap <= 0.3),                 "クロス幅 0.1-0.3（緩めると入る）")
    stat(o & (d.gap > 0) & (d.gap <= 0.1),                   "クロス幅 0-0.1")
    
    o = others("high_adx")
    stat(o & ~c_high,                                        "high_adx 分岐落ち（ADX40+ & ATR<200）")
    
    print("\n== 参考: 2条件落ち以上も含めた全不採用 ==")
    stat(~full, "V9 不採用 全部")

elif MODE == "adxyear":
    import pandas as pd
    
    CSV = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/results/priority_rebuild/ratchet/p23_candidates_typeonly.csv"
    d = pd.read_csv(CSV)
    d["entry_time"] = pd.to_datetime(d["entry_time"])
    d = d[d["entry_time"] < pd.Timestamp("2025-01-01")].copy()
    d["gap"] = d["stoch_d_at_entry"] - d["stoch_k_at_entry"]
    d["year"] = d["entry_time"].dt.year
    
    c_gap   = d["gap"] > 0.3
    c_slope = d["bb_mid_slope_at_entry"] < -10.0
    c_atr   = d["atr_14"] >= 150.0
    c_high  = (d["adx_at_entry"] < 40.0) | (d["atr_14"] >= 200.0)
    adx5060 = (d["adx_at_entry"] >= 50.0) & (d["adx_at_entry"] < 60.0)
    full    = c_gap & c_slope & (d.adx_at_entry>=30) & (d.adx_at_entry<50) & c_atr & c_high
    
    tgt = d[c_gap & c_slope & c_atr & c_high & adx5060]
    print("== ADX 50-60（他条件通過）年別 ==")
    print(tgt.groupby("year").agg(n=("net_usd","size"), net=("net_usd","sum"),
                                  avg=("net_usd","mean"), win=("net_usd", lambda s:(s>0).mean()*100)).round(2).to_string())
    print("\n== 参考: V9 full 通過の年別 ==")
    print(d[full].groupby("year").agg(n=("net_usd","size"), net=("net_usd","sum"),
                                      avg=("net_usd","mean"), win=("net_usd", lambda s:(s>0).mean()*100)).round(2).to_string())
    print("\n== ADX 50-60 の中の high_adx 内訳（ADX50+は全部 ADX>=40 なので ATR>=200 が必須になっている）==")
    t2 = d[c_gap & c_slope & c_atr & adx5060]
    print(f"ATR>=200 (採用可能): {len(t2[t2.atr_14>=200])}件 net ${t2[t2.atr_14>=200]['net_usd'].sum():.1f}")
    print(f"ATR<200 (high_adx落ち): {len(t2[t2.atr_14<200])}件 net ${t2[t2.atr_14<200]['net_usd'].sum():.1f}")

elif MODE == "map":
    import pandas as pd
    
    CSV = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/results/replay_BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"
    d = pd.read_csv(CSV)
    print("列:", list(d.columns)[:20])
    d["entry_time"] = pd.to_datetime(d["entry_time"])
    print("期間:", d.entry_time.min(), "〜", d.entry_time.max(), "/", len(d), "件")
    d = d[d["entry_time"] < pd.Timestamp("2025-01-01")].copy()      # 学習期間のみ（採点・封印 不接触）
    d["year"] = d.entry_time.dt.year
    print(f"\n== 学習期間のみ: {len(d)}件 net計 ${d['net_usd'].sum():.1f} ==")
    
    print("\n== Priority×side 別（学習期間・net 降順）==")
    g = d.groupby(["priority", "side"]).agg(n=("net_usd", "size"), net=("net_usd", "sum"),
                                            avg=("net_usd", "mean"), win=("net_usd", lambda s: (s > 0).mean() * 100)).round(2)
    print(g.sort_values("net", ascending=False).to_string())
    
    if "regime" in d.columns:
        print("\n== regime 別 ==")
        print(d.groupby("regime").agg(n=("net_usd", "size"), net=("net_usd", "sum")).round(1).to_string())
        print("\n== Priority × regime（net 絶対値が大きい組のみ・|net|>200）==")
        pr = d.groupby(["priority", "regime"]).agg(n=("net_usd", "size"), net=("net_usd", "sum")).round(1)
        print(pr[pr["net"].abs() > 200].sort_values("net").to_string())
    
    print("\n== Priority 別 × 年（net）==")
    py = d.pivot_table(index="priority", columns="year", values="net_usd", aggfunc="sum").round(0)
    print(py.to_string())
    
    print("\n== 出口理由別（学習期間・全Priority）==")
    print(d.groupby("exit_reason").agg(n=("net_usd", "size"), net=("net_usd", "sum")).round(1).sort_values("net").to_string())
