#!/usr/bin/env python3
"""traj_branch_diag.py — read-only 検証（診断レーン・acceptance 免除・2026-07-14 GO）

決定的チェック（あたり付け）: 勢い mom3 で分岐した出口が、一律トレーリングを net で超えるか。
  全方式に共通の SL(-0.5%) + horizon(48本) を入れ、違いを「トレーリングを勢いで条件分岐するか」だけに絞る。
  ＝差が出れば「状態機械（勢いで分岐）が一律を超える」が数字で言える（相殺 L-334 を破れるか）。

方式（採点窓の incumbent 玉・maker fill・crude・あたり付け）:
  base       : SL-0.5% + horizon のみ（トレーリングなし）
  uniform(D) : + 走行ピークから D% 割戻しで一律利確
  branch     : + 勢いで分岐＝mom3<M（勢い死＝反発）なら tight 割戻し・mom3>=M（下げ継続）なら loose 割戻し

⚠️ あたり付け＝閾値/設定は焼かない。採否は実エンジン両窓 score.py（L-267）。因果指標のみ＝leak なし。
read-only: print のみ・売買記録CSV/score.py に不関与（診断レーン）。
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild")
from v22_gate_diag import build_setup, run_cfg   # noqa: E402
import periods                                    # noqa: E402
import eval_engine as ee                          # noqa: E402

TRAIN_END = periods.TRAIN_END
SC_START = periods.SCORE_START
SCORE_END = periods.SEAL_START
HORIZON = 48
SL = 0.5           # 共通 SL %（含み損がこれを超えたら切る＝B型の止血）
MAKER = ee.MAKER_FEE


def _exit_net(ep, size, exit_px):
    gross = (ep - exit_px) * size
    fee = ep * size * MAKER + exit_px * size * MAKER
    return gross - fee


def sim(rows, close, idx_of, lo, hi, mode, D=0.10, D_tight=0.10, D_loose=0.40, M=0.0):
    tot = 0.0
    n = 0
    for r in rows:
        et = pd.Timestamp(r["entry_time"])
        if not (lo <= et < hi):
            continue
        i0 = idx_of.get(et.value)
        if i0 is None or i0 < 6:
            continue
        ep = float(r["entry_price"]); size = float(r["size_btc"])
        j1 = min(i0 + HORIZON, len(close) - 1)
        peak = -1e9
        exit_px = close[j1]                       # 未発火は horizon 末
        for j in range(i0, j1 + 1):
            p = (ep - close[j]) / ep * 100.0
            if p <= -SL:                          # 共通 SL（B型の止血）
                exit_px = close[j]; break
            peak = max(peak, p)
            if peak > 0:
                if mode == "uniform":
                    thr = D
                elif mode == "branch":
                    mom3 = (close[j - 3] - close[j]) / close[j - 3] * 100.0
                    thr = D_tight if mom3 < M else D_loose
                else:                             # base
                    thr = 1e9
                if (peak - p) >= thr:
                    exit_px = close[j]; break
        tot += _exit_net(ep, size, exit_px)
        n += 1
    return tot, n


def main():
    print("=" * 100)
    print("状態機械あたり付け: 勢い分岐トレーリング vs 一律トレーリング（共通 SL-0.5%+horizon48・crude・あたり付け）")
    print("=" * 100)
    df, v15p_base, up20 = build_setup()
    trades = run_cfg(df, v15p_base, up20, {})
    close = df["close"].to_numpy(float)
    idx_of = {pd.Timestamp(t).value: i for i, t in enumerate(df["ts"].to_numpy())}

    for wname, lo, hi in [("学習窓", pd.Timestamp("2021-04-01"), TRAIN_END), ("採点窓", SC_START, SCORE_END)]:
        print(f"\n[{wname}]（参考: incumbent 実エンジン net＝採点窓 -453）")
        b, nb = sim(trades, close, idx_of, lo, hi, "base")
        print(f"  base(SLのみ・トレーリングなし)          net ${b:>9,.0f}  (n={nb})")
        for D in (0.10, 0.20):
            u, _ = sim(trades, close, idx_of, lo, hi, "uniform", D=D)
            print(f"  uniform 一律割戻し D={D:.2f}%              net ${u:>9,.0f}   (対base {u-b:+,.0f})")
        for M in (0.0, 0.03):
            br, _ = sim(trades, close, idx_of, lo, hi, "branch", D_tight=0.10, D_loose=0.40, M=M)
            print(f"  branch 勢い分岐(tight0.10/loose0.40,M={M:.2f}) net ${br:>9,.0f}   (対base {br-b:+,.0f})")

    print("\n  ⚠️ あたり付け＝crude maker fill・一律 SL・add無視。方向確認専用＝設計に焼かない。")
    print("     採否は状態機械を実装し実エンジン両窓 score.py で判定（L-267・因果指標のみ＝leak なし）。")


if __name__ == "__main__":
    main()
