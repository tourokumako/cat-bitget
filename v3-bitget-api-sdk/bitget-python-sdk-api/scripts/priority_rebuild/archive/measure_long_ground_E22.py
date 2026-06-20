#!/usr/bin/env python3
"""measure_long_ground_E22.py — LONG Priority 単独の地面を連続モードで測る（E22・P3/P2）

E16(P21)/E17(P1) と同じ流儀: replay_csv.run(OHLCV5年, 当該PのみON, regime_switch=False) 直呼び・V9不変。
- P3 = stoch ゴールデンクロス LONG（P23-SHORT のミラー・LONG側TOP）・ADX 30-50・ATR≥250・
  bb傾き>+10・unit 0.024・MAX_ADDS=1・出口 TP0.8%/SL1.5%/TIME480/MFE_STALE $4・90分（trail なし）。
  regime 切替表（replay_csv L56-72）で全 regime False ＝ 5年間一度も発火実績なし（単独実力 未測定）。
- P2 = stoch GC 系 LONG・ADX≥30(40-50除外)・ATR 100-300・RSI≥45・unit 0.024・MAX_ADDS=5・
  出口 TP0.6%/TIME480/MFE_STALE $3・90分（trail なし）。
自己検査: ① priority 全件一致 ② side 全件 LONG ③ size max ≤ 上限 ④ 同時保有合計 ≤ 0.12（H1）。
"""
from __future__ import annotations
import argparse
import sys
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                                       # noqa: E402
import gen_p23_candidates as gen                              # noqa: E402
from preload_cache import cached_preload                      # noqa: E402  (時短③・selfcheck PASS 後に有効)

CAP = 0.12
_R = ROOT / "results" / "priority_rebuild" / "ratchet"
SPEC = {
    3: {"flag": "ENABLE_P3_LONG", "size_max": 0.024, "out": _R / "trades_p3_E22_ground.csv"},
    2: {"flag": "ENABLE_P2_LONG", "size_max": 0.12, "out": _R / "trades_p2_E22_ground.csv"},
    4: {"flag": "ENABLE_P4_LONG", "size_max": 0.12, "out": _R / "trades_p4_E22_ground.csv"},
}


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--priority", type=int, choices=[3, 2, 4], required=True)
    args = ap.parse_args()
    spec = SPEC[args.priority]

    params = rc._load_params()
    p = dict(params)
    for k in list(p):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p[k] = (k == spec["flag"])
    adds = p.get("MAX_ADDS_BY_PRIORITY", {}).get(str(args.priority))
    print(f"[params] {spec['flag']} only / unit={p.get(f'P{args.priority}_POSITION_SIZE_BTC') or p.get('LONG_POSITION_SIZE_BTC')} / MAX_ADDS={adds}")

    pre = cached_preload(str(gen.OHLCV_CSV), p)
    trades = rc.run(str(gen.OHLCV_CSV), p, _preloaded=pre, regime_switch=False)
    if not trades:
        print(f"[結果] トレード 0 件（P{args.priority} は5年間 単独でも発火せず）")
        return
    d = pd.DataFrame(trades)
    assert set(d["priority"].astype(int)) == {args.priority}, f"P{args.priority} 以外混入: {set(d['priority'])}"
    assert set(d["side"]) == {"LONG"}, f"LONG 以外混入: {set(d['side'])}"
    mx_size = d["size_btc"].astype(float).max()
    assert mx_size <= spec["size_max"] + 1e-9, f"size max {mx_size} > {spec['size_max']}"
    print(f"[自己検査] ✅ 全 {len(d)} 件 priority={args.priority} / LONG / size max={mx_size}")
    verify_concurrent_budget(trades)
    spec["out"].parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(spec["out"], index=False)
    print(f"[出力] {spec['out']} / net合計（全期間・CSV基準）${d.net_usd.astype(float).sum():.1f}")


if __name__ == "__main__":
    main()
