#!/usr/bin/env python3
"""measure_p21_ground_E16.py — P21 SHORT 単独の地面を連続モード（replay_csv.run・cap遵守）で測る（E16）

目的（ledger E16事前分析 → WORKFLOW 改訂73）:
  P21 SHORT は V9 全体地図で学習期間最強（+$1,192・460件・勝率89.8%・regime切替下）。
  P21 を単独（regime切替なし・他Priority全OFF）で動かした時の実力＝地面を測り、
  E16（P21 横展開）の ratchet 比較基準にする。P23 の E0.2 と同じ流儀。

手段（自作 sim は書かない＝移植リスクを消す）:
  replay_csv.run(OHLCV5年, p21_params, regime_switch=False) を直接呼ぶ。
  前例 = gen_p23_candidates.py L209 の自己検査（rc.run() が「本物」の基準側）。
  V9 本体不変（replay_csv / cat_v9_decider / cat_params_v9.json は import・読み込みのみ）。

予算 0.12 BTC（CLAUDE.md §0-2）:
  P21 は MAX_ADDS_BY_PRIORITY["21"]=1・P21_POSITION_SIZE_BTC=0.06 → 同時保有 max=0.06 想定。
  全トレードから各時点の sum(active_btc) を実測 assert ＋ score.py cap ゲートで二重検証。

自己検査（このスクリプト固有）:
  ① priority 列が全件 21 ② side 全件 SHORT ③ size_btc ≤ 0.06+ε（addなし確認）
  ④ 同時保有合計 max ≤ 0.12（H1）
"""
from __future__ import annotations
import sys
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                                       # noqa: E402  V9 リプレイ（import のみ）
import gen_p23_candidates as gen                              # noqa: E402  OHLCV_CSV パス参照のみ

OUT = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p21_E16_ground.csv"
CAP = 0.12   # 予算（合計上限）・CLAUDE.md §0-2
P21_SIZE = 0.06  # cat_params_v9.json P21_POSITION_SIZE_BTC（読み込み値で再確認する）


def verify_concurrent_budget(trades: list) -> float:
    """全トレードから各時点の同時保有「合計」を実測し max を返す。0.12 超なら停止。"""
    d = pd.DataFrame(trades)
    et = pd.to_datetime(d["entry_time"]).tolist()
    xt = pd.to_datetime(d["exit_time"]).tolist()
    sz = d["size_btc"].astype(float).tolist()
    events = [(et[i], sz[i]) for i in range(len(d))] + [(xt[i], -sz[i]) for i in range(len(d))]
    events.sort(key=lambda x: (x[0], x[1]))   # 同時刻は exit(マイナス) を先に
    cur = mx = 0.0
    mxt = None
    for t, s in events:
        cur = round(cur + s, 9)
        if cur > mx:
            mx = cur
            mxt = t
    print(f"[物理検証] 同時保有合計 max = {mx:.4f} BTC @ {mxt}（予算 {CAP}）")
    assert mx <= CAP + 1e-9, f"合計 {mx:.4f} BTC > 予算 {CAP} BTC（停止）"
    print(f"[物理検証] ✅ 全期間で sum(active) ≤ {CAP} BTC")
    return mx


def main():
    params = rc._load_params()
    p21 = dict(params)
    for k in list(p21):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p21[k] = (k == "ENABLE_P21_SHORT")
    size_cfg = float(p21.get("P21_POSITION_SIZE_BTC", 0.0))
    adds_cfg = int(p21.get("MAX_ADDS_BY_PRIORITY", {}).get("21", -1))
    print(f"[params] ENABLE_P21_SHORT only / P21_POSITION_SIZE_BTC={size_cfg} / MAX_ADDS(21)={adds_cfg}")

    print(f"[run] replay_csv.run({gen.OHLCV_CSV.name}, regime_switch=False) ...")
    trades = rc.run(str(gen.OHLCV_CSV), p21, regime_switch=False)
    assert trades, "トレード 0 件（想定外・停止）"

    d = pd.DataFrame(trades)
    # 自己検査 ①②③
    assert set(d["priority"].astype(int)) == {21}, f"P21 以外が混入: {set(d['priority'])}"
    assert set(d["side"]) == {"SHORT"}, f"SHORT 以外が混入: {set(d['side'])}"
    mx_size = d["size_btc"].astype(float).max()
    assert mx_size <= size_cfg + 1e-9, f"size_btc max {mx_size} > {size_cfg}（add 発生の疑い・停止）"
    print(f"[自己検査] ✅ 全 {len(d)} 件 priority=21 / SHORT / size_btc max={mx_size}")

    verify_concurrent_budget(trades)   # 自己検査 ④（H1）

    net_all = d["net_usd"].astype(float).sum()
    print(f"[全期間] {len(d)} 件 / net合計 ${net_all:.1f}（期間別は score.py が正）")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT, index=False)
    print(f"[出力] {OUT}")
    print(f"→ 次: python3 scripts/priority_rebuild/score.py {OUT} --start 2025-04-01 --end 2025-12-31")


if __name__ == "__main__":
    main()
