#!/usr/bin/env python3
"""measure_ground_combined_E32.py — P21+P23 合算地面（第一歩＝V9忠実 23→21・cap実態を測るだけ）

背景（2026-06-13・まこさん指示）:
  単独地面（P21 月$401 / P23 月$241・E31）は予算0.12共有で足し算できない。
  合算は同サイドSHORTが1ポジに merge され、優先順位（decider コード=P23>P21）で
  どちらが建てるか・どのExitで回るかが決まる（cat_v9_decider L469-484 が P21 L556-569 より先）。

第一歩の狙い（最小・忠実・エンジン不変）:
  rc.run(P21+P23 両オン・regime_switch=False) を回す＝V9本体の merge/Exit/add を完全忠実に再現
  （gen._step は P23専用で TRAIL 無し＝P21 を回せないので使わない）。
  ★ cap は止めずに「各時点の同時保有合計の最大」を**報告だけ**する（assert で止めない）。
  → max ≤ 0.12 なら cap停止 不要・そのまま新窓 score で 23→21 合算地面が確定。
  → max > 0.12 なら replay_csv の add ロジックが混在Priorityで cap違反する実証＝
     cap停止（0.12到達でadd停止）の作り込みが必要（次段でまこさんと設計）。

V9本体不変（import のみ）: replay_csv / cat_v9_decider / cat_params_v9.json。
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

NEW_OHLCV = ROOT / "data" / "BTCUSDT-5m-2024-09-01_2026-02-28_slice_V9FULL_safe.csv"
OUT = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p21p23_E32_combined_2321.csv"
CAP = 0.12


def report_budget(trades):
    """各時点の同時保有「合計」の最大を測る（止めない・報告のみ）。混在Priority add の cap実態を出す。"""
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
    return mx, mxt


def main():
    print(f"[ohlcv] {NEW_OHLCV.name}")
    params = rc._load_params()
    # P21+P23 のみ有効・他 Priority 無効
    p = dict(params)
    for k in list(p):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p[k] = (k in ("ENABLE_P21_SHORT", "ENABLE_P23_SHORT"))
    print(f"[params] ENABLE P21_SHORT={p.get('ENABLE_P21_SHORT')} / P23_SHORT={p.get('ENABLE_P23_SHORT')} / 他OFF")
    print(f"[run] rc.run(P21+P23, regime_switch=False)＝V9忠実 23→21（decider 優先順位そのまま） ...")

    trades = rc.run(str(NEW_OHLCV), p, regime_switch=False)
    assert trades, "トレード0件（停止）"
    d = pd.DataFrame(trades)
    sides = set(d["side"]); pris = sorted(set(d["priority"].astype(int)))
    by_pri = d["priority"].astype(int).value_counts().to_dict()
    print(f"[結果] {len(d)} 件 / side={sides} / priority別 件数={by_pri}")
    print(f"       entry_priority＝最初に建てたPriority（merge後はこのExitで一括決済）")

    mx, mxt = report_budget(trades)
    flag = "✅ ≤0.12（cap停止 不要）" if mx <= CAP + 1e-9 else "⛔ >0.12（cap違反＝cap停止の作り込みが必要）"
    print(f"[cap実態] 同時保有合計 max = {mx:.4f} BTC @ {mxt}  → {flag}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT, index=False)
    print(f"[出力] {OUT.name}")
    if mx <= CAP + 1e-9:
        print("→ cap OK。採点可:")
        print(f"  precheck.py {OUT.name} --authorize {OUT.name}")
        print(f"  score.py {OUT} --start 2025-06-01 --end 2026-02-28   （新窓 23→21 合算地面）")
        print(f"  score.py {OUT} --start 2025-04-01 --end 2025-12-31   （旧窓 参考）")
    else:
        print("→ ⛔ cap違反。score.py の cap ゲートで拒否される。次段で cap停止（0.12到達でadd停止）を設計。")


if __name__ == "__main__":
    main()
