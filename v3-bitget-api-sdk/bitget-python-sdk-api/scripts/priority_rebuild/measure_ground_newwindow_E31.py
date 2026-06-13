#!/usr/bin/env python3
"""measure_ground_newwindow_E31.py — 検証期間 2ヶ月後ろ倒し版で P21/P23 の地面を測り直す（E31）

背景（2026-06-13・まこさん指示）:
  期間分割を決めてから2ヶ月経過 → 新しい2ヶ月（2026-04/05）を活用して検証窓を後ろ倒し。
  新区切り: 学習〜2025-02 / 捨て 2025-03〜05 / 採点 2025-06〜2026-02 / 封印 2026-03〜05。
  採点の正本5m足（Binance Spot）を 2026-05末まで延長済（cat_requirements §8.2.1.1）。

測り方（旧 E0.2 / E16 を完全再現・OHLCV だけ延長ファイルに差し替え）:
  P21 = replay_csv.run(OHLCV, p21, regime_switch=False)         （単独・連続モード）
  P23 = gen.run_continuous(df, bar_ms, p23, full_fn)            （連続モード・cap遵守）
  net は rc.run / gen.run_continuous（V9 リプレイ）の net_usd をそのまま使う＝旧地面と同一計器。
  自作 net 計算はしない（eval_engine は ML sim 用・L-268 取り違え回避）。採点は score.py。
  V9 本体不変（import のみ）。出力は別名（旧地面 CSV を温存）。

検証:
  ① 同時保有合計 max ≤ 0.12（H1・物理 assert）
  ② P21=priority21/SHORT/add無 ③ 旧窓でも採点して旧地面と一致するか（延長で過去不変の証明）
"""
from __future__ import annotations
import sys
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                                       # noqa: E402
import gen_p23_candidates as gen                              # noqa: E402
from strategies.cat_v9_decider import check_entry_priority    # noqa: E402

# ★ 高速版（B・2026-06-13）: 5年通しは遅すぎ（P21 だけで CPU 18分）→ 採点窓+助走だけスライス。
#   スライス = 2024-09-01〜2026-02-28（採点窓 2025-06〜2026-02 の手前に約8ヶ月の助走）。
#   P21(regime_switch=False)/P23(連続モード) は regime/_DAILY_WARMUP を使わない＝5m指標の助走のみ。
#   ★等価性チェック: 旧窓(2025-04〜12)で score して旧地面 P21 $2,697 / P23 $925 と一致すれば
#   「スライス+助走=5年通しと同値」が証明される（一致しなければ助走を前に伸ばす）。
NEW_OHLCV = ROOT / "data" / "BTCUSDT-5m-2024-09-01_2026-02-28_slice_V9FULL_safe.csv"
gen.OHLCV_CSV = NEW_OHLCV

OUT_P21 = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p21_E31_newwin_ground.csv"
OUT_P23 = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p23_E31_newwin_ground.csv"
CAP = 0.12


def verify_budget(trades, tag):
    d = pd.DataFrame(trades)
    et = pd.to_datetime(d["entry_time"]).tolist()
    xt = pd.to_datetime(d["exit_time"]).tolist()
    sz = d["size_btc"].astype(float).tolist()
    events = [(et[i], sz[i]) for i in range(len(d))] + [(xt[i], -sz[i]) for i in range(len(d))]
    events.sort(key=lambda x: (x[0], x[1]))
    cur = mx = 0.0; mxt = None
    for t, s in events:
        cur = round(cur + s, 9)
        if cur > mx: mx, mxt = cur, t
    print(f"[{tag}] 同時保有合計 max = {mx:.4f} BTC @ {mxt}（予算 {CAP}）")
    assert mx <= CAP + 1e-9, f"[{tag}] 合計 {mx:.4f} > {CAP}（停止）"
    return mx


def main():
    print(f"[ohlcv] {NEW_OHLCV.name}")
    params = rc._load_params()

    # ---- P21 SHORT 単独（regime_switch=False） ----
    p21 = dict(params)
    for k in list(p21):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p21[k] = (k == "ENABLE_P21_SHORT")
    print(f"[P21] run regime_switch=False ...")
    t21 = rc.run(str(NEW_OHLCV), p21, regime_switch=False)
    assert t21, "P21 トレード0件（停止）"
    d21 = pd.DataFrame(t21)
    assert set(d21["priority"].astype(int)) == {21}, f"P21混入: {set(d21['priority'])}"
    assert set(d21["side"]) == {"SHORT"}, f"P21 side: {set(d21['side'])}"
    verify_budget(t21, "P21")
    d21.to_csv(OUT_P21, index=False)
    print(f"[P21] {len(d21)} 件 → {OUT_P21.name}")

    # ---- P23 SHORT 連続モード ----
    p23 = dict(params)
    for k in list(p23):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p23[k] = (k == "ENABLE_P23_SHORT")
    df, _raw = rc.preload(str(NEW_OHLCV), p23)
    bar_ms = int(df.at[1, "timestamp_ms"] - df.at[0, "timestamp_ms"])
    full_fn = lambda i: (check_entry_priority(i, df, p23) == gen.PRIORITY)
    print(f"[P23] run_continuous ... bars={len(df)}")
    t23 = gen.run_continuous(df, bar_ms, p23, full_fn)
    verify_budget(t23, "P23")
    pd.DataFrame(t23).to_csv(OUT_P23, index=False)
    print(f"[P23] {len(t23)} 件 → {OUT_P23.name}")

    print("\n→ 採点（新窓 採点期間 2025-06〜2026-02）:")
    print(f"  python3 scripts/priority_rebuild/score.py {OUT_P21} --start 2025-06-01 --end 2026-02-28")
    print(f"  python3 scripts/priority_rebuild/score.py {OUT_P23} --start 2025-06-01 --end 2026-02-28")
    print("→ 旧窓 一致確認（延長で過去不変の証明・旧地面 P21 $2,697 / P23 $925）:")
    print(f"  python3 scripts/priority_rebuild/score.py {OUT_P21} --start 2025-04-01 --end 2025-12-31")
    print(f"  python3 scripts/priority_rebuild/score.py {OUT_P23} --start 2025-04-01 --end 2025-12-31")


if __name__ == "__main__":
    main()
