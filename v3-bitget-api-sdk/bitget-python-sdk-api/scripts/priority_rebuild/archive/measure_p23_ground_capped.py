#!/usr/bin/env python3
"""measure_p23_ground_capped.py — V9手書きP23の「正しい地面」を連続モード（逐次・予算0.12遵守）で測る

背景（2026-06-07・ledger INC-1）:
  旧地面 $1,943（trades_p23_full_test.csv）は gen の独立モード（各候補を別々に建てる）で
  同時保有が 0.60 BTC（予算 0.12 BTC の5倍）＝本番で発注不可能な楽観値だった（false_positive §0-2 類型H）。
  本スクリプトは V9 本来の逐次運用（連続モード = replay_csv.run() と件数・net 一致が自己検査済）で測り直す。

予算 0.12 BTC の定義（CLAUDE.md §0-2・絶対に取り違えない）:
  「任意の時点 t で、保有中の全ポジションのサイズの合計 ≤ 0.12 BTC」。1ポジ上限ではなく合計上限。
  P23 SHORT は連続モードで同時に1ポジ（add で平均建値が膨らむ＝size_btc が 0.024→0.12 に増える）。
  → その1ポジの size がそのまま「合計」。add5 で最大 0.12。複数ポジを同時に建てない＝予算内。

★物理検証（私の言葉を信じない・コードが保証する）:
  連続モードの全トレードから各時点の sum(active_btc) を実測し、max ≤ 0.12 を assert（守らねば停止）。
  さらに出力CSVは cap ゲート付き score.py で採点する（二重の物理チェック）。

V9 本体不変（import のみ）: gen_p23_candidates / replay_csv / cat_v9_decider。
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
import gen_p23_candidates as gen                              # noqa: E402  連続モード（import のみ）
from strategies.cat_v9_decider import check_entry_priority    # noqa: E402

OUT = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p23_ground_capped.csv"
CAP = 0.12   # 予算（合計上限）・CLAUDE.md §0-2


def verify_concurrent_budget(trades: list) -> float:
    """全トレードから各時点の同時保有「合計」を実測し max を返す。0.12 超なら停止（コードが保証）。"""
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
    print(f"[物理検証] 連続モード 同時保有合計 max = {mx:.4f} BTC @ {mxt}（予算 {CAP}）")
    assert mx <= CAP + 1e-9, (
        f"連続モードでも合計 {mx:.4f} BTC > 予算 {CAP} BTC（想定外・停止）。"
        f"P23 が単独1ポジでない可能性 → 設計を再確認すること。"
    )
    print(f"[物理検証] ✅ 全期間で sum(active) ≤ {CAP} BTC を満たす（私の主張でなくコードが証明）")
    return mx


def main():
    params = rc._load_params()
    p23 = dict(params)                                        # P23 のみ有効（gen.main と同条件）
    for k in list(p23):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p23[k] = (k == "ENABLE_P23_SHORT")
    df, _df_raw = rc.preload(str(gen.OHLCV_CSV), p23)
    bar_ms = int(df.at[1, "timestamp_ms"] - df.at[0, "timestamp_ms"])
    print(f"[load] bars={len(df)}")

    full_fn = lambda i: (check_entry_priority(i, df, p23) == gen.PRIORITY)
    trades = gen.run_continuous(df, bar_ms, p23, full_fn)
    net = sum(float(t["net_usd"]) for t in trades)
    print(f"[連続モード] P23 full トレード {len(trades)} 件 / net合計（全期間・コスト前）${net:.1f}")

    verify_concurrent_budget(trades)                          # ★ 0.12 を物理検証（守らなければ停止）

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(trades).to_csv(OUT, index=False)
    print(f"[出力] {OUT}")
    print(f"→ 次: python3 scripts/priority_rebuild/score.py {OUT} --start 2025-04-01 --end 2025-12-31")
    print("  （score.py の cap ゲートでも二重に 0.12 を検証 → 正しい地面 net）")


if __name__ == "__main__":
    main()
