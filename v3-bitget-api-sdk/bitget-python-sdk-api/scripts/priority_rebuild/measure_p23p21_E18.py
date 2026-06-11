#!/usr/bin/env python3
"""measure_p23p21_E18.py — P23+P21 SHORT 並立の実測（連続モード・E18）

狙い（§6.2 並立構成の実現可能性を直接測る）:
  P23（downtrend 戻り売り・保有8h級・add5）と P21（デッドクロス・保有10分・add1）を
  同時 ON にした SHORT 1ポジ排他の世界で、単独合算（$926+$1,021/9ヶ月）が
  共食いでどこまで残るかを実測。replay_csv.run() 直呼び・V9 不変。

⚠️ 既知の観察対象（実装事実・2026-06-12 コード読みで判明）:
  replay は SHORT ポジ保有中に別 Priority のシグナルが来ると「既存ポジへの add」として
  積む（unit は新シグナル側の P*_POSITION_SIZE_BTC・max_adds はポジ側 Priority の値）。
  → P23 ポジに P21 の 0.06 が混成 add される経路があり、0.024×4+0.06=0.156 > 0.12 の
  cap 違反があり得る。本スクリプトは同時保有合計を実測して報告（違反は score.py が採点拒否）。
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

OUT = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p23p21_E18.csv"
CAP = 0.12


def concurrent_max(trades: list) -> float:
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
    return mx


def main():
    params = rc._load_params()
    p = dict(params)
    for k in list(p):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p[k] = k in ("ENABLE_P23_SHORT", "ENABLE_P21_SHORT")
    print("[params] P23+P21 SHORT 並立 / 他 OFF / regime_switch=False")

    trades = rc.run(str(gen.OHLCV_CSV), p, regime_switch=False)
    assert trades, "トレード 0 件（停止）"
    d = pd.DataFrame(trades)
    pris = set(d["priority"].astype(int))
    assert pris <= {21, 23}, f"想定外 priority: {pris}"
    assert set(d["side"]) == {"SHORT"}
    mx = concurrent_max(trades)
    print(f"[実測] 全 {len(d)} 件 / priority内訳 {d.priority.value_counts().to_dict()} / size max {d.size_btc.max()}")
    print(f"[実測] 同時保有合計 max = {mx:.4f} BTC（予算 {CAP}・超過なら score.py が採点拒否）")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT, index=False)
    print(f"[出力] {OUT} / net合計（全期間）${d.net_usd.astype(float).sum():.1f}")


if __name__ == "__main__":
    main()
