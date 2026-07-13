#!/usr/bin/env python3
"""v24_guard_diag.py — 番人メタ確認（read-only 診断レーン・acceptance 免除・2026-07-16）

目的（§2.9③ わざと壊して落ちるか）: v24 の resting maker 利確（TREND_CAUGHT_TP）が
   V24_TREND_TP_PCT に正しく配線されているかを、極端値で証明する。
   - 極小（0.001%）→ 建値のすぐ下で即約定＝TREND_CAUGHT_TP が支配（trend_caught の大半を利確）
   - 通常（0.08%）→ 通常発火
   - 極大（5.0%）→ 利確水準に届かない＝TREND_CAUGHT_TP ≈ 0・MFE_STALE/SL/TIME へ退行（恒等退行）
   ＝発火数が V24_TREND_TP_PCT に単調反応すれば「resting maker 利確は L に正しく配線」の証明。

read-only: build_setup を import 再利用・print のみ・売買記録CSV/score.py に不関与（診断レーン）。
   V24_TREND_TP_PCT の monkey-patch は番人のための一時変更（本体の定数は 0.08 のまま）。
"""
import sys

sys.path.insert(0, "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild")
import e37_range_scalp as e37   # noqa: E402
from v22_gate_diag import build_setup   # noqa: E402  検証済みセットアップ（v18 base fit・df）

smoke_n = 60000   # 先頭バー（動作確認・全期間は不要）


def run_v24(df, up20, v15p_base, tp_pct):
    e37.V24_TREND_TP_PCT = tp_pct    # monkey-patch（番人・本体定数は 0.08）
    p = {k: (dict(v) if isinstance(v, dict) else v) for k, v in v15p_base.items() if k != "cell_fn"}
    if "cell_fn" in v15p_base:
        p["cell_fn"] = v15p_base["cell_fn"]
    p["v23_trend_exit"] = True                # trend_caught 保持
    p["v24_trend_maker_tp"] = True            # v24: resting maker 利確
    p["v22_anchor"] = {0: 24}                 # V24_FIXED_V22（v22 学習の定数化）
    e37.run_continuous_v11(df, "5m", no_add=False, single_tp=False, v11_open_entry=False,
                           v12_open_range=True, v13_time_maker=True, v15_params=p, v20_uptrend=up20)
    s = p["_stats"]
    return s.get("v23_trend_caught", 0), s.get("TREND_CAUGHT_TP", 0), s.get("MFE_STALE_CUT", 0)


def main():
    print("=" * 90)
    print("v24 番人メタ確認: V24_TREND_TP_PCT 極端値で TREND_CAUGHT_TP が支配/恒等退行するか（配線証明）")
    print("=" * 90)
    df, v15p_base, up20 = build_setup()
    df = df.iloc[:smoke_n].reset_index(drop=True)
    up20 = up20[:smoke_n]
    print(f"  smoke {smoke_n} バー / build_setup 完了")
    print(f"\n  {'V24_TREND_TP_PCT':>18} {'trend_caught':>13} {'TREND_CAUGHT_TP':>16} {'MFE_STALE':>11}")
    res = {}
    for tp in (0.08, 0.001, 5.0):
        caught, tct, stale = run_v24(df, up20, v15p_base, tp)
        res[tp] = tct
        print(f"  {tp:>18} {caught:>13} {tct:>16} {stale:>11}")
    e37.V24_TREND_TP_PCT = 0.08   # 復元
    print("\n  [判定]")
    ok_small = res[0.001] > res[0.08]     # 極小で支配（増える）
    ok_large = res[5.0] < res[0.08]       # 極大で退行（減る）
    print(f"    極小0.001% で TREND_CAUGHT_TP が支配（{res[0.001]} > 通常{res[0.08]}）: {'✅' if ok_small else '⛔'}")
    print(f"    極大5.0%   で TREND_CAUGHT_TP が退行（{res[5.0]} < 通常{res[0.08]}）: {'✅' if ok_large else '⛔'}")
    print(f"    → resting maker 利確は V24_TREND_TP_PCT に正しく配線: {'✅ 番人 PASS' if (ok_small and ok_large) else '⛔ 配線疑い'}")


if __name__ == "__main__":
    main()
