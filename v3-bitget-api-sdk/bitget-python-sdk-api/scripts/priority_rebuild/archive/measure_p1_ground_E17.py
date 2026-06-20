#!/usr/bin/env python3
"""measure_p1_ground_E17.py — P1 LONG 単独の地面を連続モード（replay_csv.run・cap遵守）で測る（E17）

E16（P21）と同じ流儀: replay_csv.run(OHLCV5年, P1のみON, regime_switch=False) 直呼び・V9不変。
P1 = MACD ゴールデンクロス・ADX≥30・ATR 60-9999・スキャル（MAX_ADDS=1・0.06 BTC）・trail 主出口。
サイズ依存 USD ゲート = LONG_PROFIT_LOCK（ARM $15 / LOCK $6）のみ
（P1_MFE_STALE_* は params に残るが replay に実装なし＝grep 確認済 2026-06-12）。
自己検査: ① priority 全件 1 ② side 全件 LONG ③ size max ≤ 0.06 ④ 同時保有合計 ≤ 0.12（H1）。
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

OUT = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p1_E17_ground.csv"
CAP = 0.12


def verify_concurrent_budget(trades: list) -> float:
    d = pd.DataFrame(trades)
    et = pd.to_datetime(d["entry_time"]).tolist()
    xt = pd.to_datetime(d["exit_time"]).tolist()
    sz = d["size_btc"].astype(float).tolist()
    events = [(et[i], sz[i]) for i in range(len(d))] + [(xt[i], -sz[i]) for i in range(len(d))]
    events.sort(key=lambda x: (x[0], x[1]))
    cur = mx = 0.0
    for ts, s in events:
        cur = round(cur + s, 9)
        mx = max(mx, cur)
    print(f"[物理検証] 同時保有合計 max = {mx:.4f} BTC（予算 {CAP}）")
    assert mx <= CAP + 1e-9, f"合計 {mx} > {CAP}（停止）"
    return mx


def main():
    params = rc._load_params()
    p1 = dict(params)
    for k in list(p1):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p1[k] = (k == "ENABLE_P1_LONG")
    print(f"[params] ENABLE_P1_LONG only / size={p1.get('P1_POSITION_SIZE_BTC')} / MAX_ADDS(1)={p1.get('MAX_ADDS_BY_PRIORITY', {}).get('1')}")

    trades = rc.run(str(gen.OHLCV_CSV), p1, regime_switch=False)
    assert trades, "トレード 0 件（停止）"
    d = pd.DataFrame(trades)
    assert set(d["priority"].astype(int)) == {1}, f"P1 以外混入: {set(d['priority'])}"
    assert set(d["side"]) == {"LONG"}, f"LONG 以外混入: {set(d['side'])}"
    mx_size = d["size_btc"].astype(float).max()
    assert mx_size <= 0.06 + 1e-9, f"size max {mx_size} > 0.06"
    print(f"[自己検査] ✅ 全 {len(d)} 件 priority=1 / LONG / size max={mx_size}")
    verify_concurrent_budget(trades)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT, index=False)
    print(f"[出力] {OUT} / net合計（全期間）${d.net_usd.astype(float).sum():.1f}")


if __name__ == "__main__":
    main()
