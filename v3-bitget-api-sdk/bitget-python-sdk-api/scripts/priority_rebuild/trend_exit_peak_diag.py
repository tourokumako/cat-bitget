#!/usr/bin/env python3
"""trend_exit_peak_diag.py — read-only 検証（診断レーン・acceptance 免除・2026-07-16 まこさん指示）

目的（まこさん指示 2026-07-16）: v23 で「反転待ち利確(STOCH_REVERSE_EXIT)＋含み益失速切り(MFE_STALE_CUT)」に
   移った trend_caught 玉（＝uptrend 発火で畳む玉）が、entry 後どれだけ含み益ピークを持っていたかを観察し、
   「ピーク帯 resting maker 利確」を建値+L% に置いたら何%取れて net がどう動くかを L 別にあたり付ける。
   ＝v24（反転待ちをやめてピーク帯で固定利確・学習ゼロ）の固定値 L の根拠を分布から作る（疑似シミュであたり付け）。

read-only: v23 結果CSV を read・print のみ・売買記録CSV/score.py に不関与（診断レーン）。
   ★因果性: mfe_usd は保有中ピーク（未来参照）＝「観察(あたり付け)」専用。
   実装する利確は建値+L% の maker 指値（その時点で取得可能＝leak なし）。採否は実エンジン両窓 score.py（L-267）。
"""
import sys
import pandas as pd

sys.path.insert(0, "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild")
import eval_engine as ee   # noqa: E402  maker 手数料の確定値（改造禁止）

BASE = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/results/priority_rebuild/ratchet/"
CSVS = {"採点窓": BASE + "trades_e37_range_scalp_v23_043_score.csv",
        "学習窓": BASE + "trades_e37_range_scalp_v23_043_train.csv"}
RT_FEE_PCT = 2 * ee.MAKER_FEE * 100                       # maker 往復 %（≈0.028）
TREND_EXITS = ("STOCH_REVERSE_EXIT", "MFE_STALE_CUT")     # v23 で trend_caught 玉に付く2枝（report §0）


def analyze(win, csv):
    print("\n" + "=" * 100)
    print(f"【{win}】 {csv.split('/')[-1]}")
    print("=" * 100)
    d = pd.read_csv(csv, parse_dates=["entry_time", "exit_time"])
    print(f"全 {len(d)} 玉(決済record単位) / net ${d.net_usd.sum():,.0f} / 往復maker費 {RT_FEE_PCT:.3f}%")

    print("\n[出口理由別 確認（C節照合）]")
    g = d.groupby("exit_reason").agg(件数=("net_usd", "size"), net=("net_usd", "sum")).sort_values("net")
    for r, row in g.iterrows():
        print(f"  {r:<22} {int(row.件数):>4}件  net ${row.net:>8,.0f}")

    tc = d[d.exit_reason.isin(TREND_EXITS)].copy()
    tc["mfe_pct"] = tc.mfe_usd / (tc.entry_price * tc.size_btc) * 100
    tc["mae_pct"] = tc.mae_usd / (tc.entry_price * tc.size_btc) * 100
    print(f"\n[対象＝trend_caught 玉（{'/'.join(TREND_EXITS)}）] {len(tc)}件 / 現状 net ${tc.net_usd.sum():,.0f}")
    print(f"  含み益ピーク mfe_pct: 平均{tc.mfe_pct.mean():.3f}% / 中央{tc.mfe_pct.median():.3f}%")
    print(f"  含み損ピーク mae_pct: 平均{tc.mae_pct.mean():.3f}% / 中央{tc.mae_pct.median():.3f}%")
    print(f"  現状 平均net/件 ${tc.net_usd.mean():.2f}")

    print("\n[含み益ピーク分布（この帯までピークが伸びた玉の数＝どこに利確を置けば取れるか）]")
    edges = [-99, 0, 0.028, 0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.30, 0.50, 99]
    lab = ["ピーク≤0(即逆行)", "0-0.028(費用未満)", "0.028-0.05", "0.05-0.08", "0.08-0.10", "0.10-0.12",
           "0.12-0.15", "0.15-0.20", "0.20-0.30", "0.30-0.50", ">0.50"]
    tc["bin"] = pd.cut(tc.mfe_pct, bins=edges, labels=lab, right=False)
    for b in lab:
        sub = tc[tc.bin == b]
        if len(sub):
            print(f"  {b:<18} {len(sub):>4}件  この帯の現状net ${sub.net_usd.sum():>7,.0f}  平均mae {sub.mae_pct.mean():.3f}%")

    print("\n[利確ライン L% 別 net（あたり付け・建値+L% に maker 利確を置いた粗試算）]")
    print("  ⚠️あたり付け＝設計に焼かない・採否は実エンジン両窓 score.py（L-267）")
    print("  想定: mfe_pct>=L の玉は L% で maker 利確／mfe_pct<L の玉は現状の出口(net_usd)のまま")
    print(f"  {'L%':>7} {'到達玉':>7} {'到達率':>7} {'利確net':>9} {'非到達net':>10} {'合計net':>9} {'対現状':>9}")
    cur = tc.net_usd.sum()
    for L in (0.028, 0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30):
        hit = tc[tc.mfe_pct >= L]
        miss = tc[tc.mfe_pct < L]
        pnl_hit = (hit.size_btc * hit.entry_price * (L / 100 - RT_FEE_PCT / 100)).sum()
        pnl_miss = miss.net_usd.sum()
        tot = pnl_hit + pnl_miss
        print(f"  {L:>7.3f} {len(hit):>6}件 {len(hit) / len(tc) * 100:>6.0f}% ${pnl_hit:>8,.0f} ${pnl_miss:>9,.0f} "
              f"${tot:>8,.0f} {tot - cur:>+9,.0f}")

    print("\n  ★読み方: 対現状が最大化する L の『範囲(plateau)』を見る（一点の最良値は焼かない）。")
    print("     非到達net が現状の出口のまま＝v24 は到達玉だけ利確に置換・非到達は既存(災害SL/TIME)に委ねる形。")


def main():
    print("=" * 100)
    print("E37 v24 あたり付け: trend_caught 玉の含み益ピーク分布 & 利確ライン別 net（両窓＝過剰適合チェック）")
    for win, csv in CSVS.items():
        analyze(win, csv)
    print("\n★両窓で分布・plateau が再現すれば固定値 L の根拠が固い（採点窓だけの最良一点は焼かない・L-267）。")


if __name__ == "__main__":
    main()
