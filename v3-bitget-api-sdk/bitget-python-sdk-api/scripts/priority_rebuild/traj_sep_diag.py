#!/usr/bin/env python3
"""traj_sep_diag.py — read-only 検証（診断レーン・acceptance 免除・2026-07-14 GO）

問い（状態機械が一律トレーリングを超えられるかの分かれ目）:
  建玉が益 +L(=0.1%)に達した時点で、その後「+2L(=0.2%)まで伸びる（持てば勝ち＝C・hold）」か
  「0以下に崩れる（反転して負け＝A・lock）」かを、その時点で取得可能な因果指標で見分けられるか。
  ＝見分けられれば、状態機械は A だけ利確し C は持てる（一律トレーリングの相殺 L-334 を超える）。

因果性: 判定に使う指標は「その決定バー j までに確定した値」のみ（未来参照なし＝H2）。
両窓（学習/採点）で分離を測る＝N10 と同じ「両窓再現」基準（採点窓で選ぶのでない・分離の存在確認）。
read-only: print のみ・売買記録CSV/score.py に不関与（診断レーン）。
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild")
from v22_gate_diag import build_setup, run_cfg   # noqa: E402
import periods                                    # noqa: E402

TRAIN_END = periods.TRAIN_END
SC_START = periods.SCORE_START
SCORE_END = periods.SEAL_START
HORIZON = 48
L = 0.10      # 益の第1閾値 %（決定バー）
L2 = 0.20     # 益の第2閾値 %（ここまで伸びれば hold が勝ち）


def build_records(trades, arrs, idx_of, lo, hi):
    close, stoch, rsi9, adx, atrp = arrs
    n = len(close)
    recs = []
    for r in trades:
        et = pd.Timestamp(r["entry_time"])
        if not (lo <= et < hi):
            continue
        i0 = idx_of.get(et.value)
        if i0 is None or i0 < 6:
            continue
        ep = float(r["entry_price"])
        j1 = min(i0 + HORIZON, n - 1)
        # 益 +L に最初に達したバー j
        jdec = None
        for j in range(i0, j1 + 1):
            if (ep - close[j]) / ep * 100.0 >= L:
                jdec = j
                break
        if jdec is None:
            continue                                  # 益が +L に届かない玉は対象外（決定機会がない）
        # target: jdec 以降、+2L 先着=1(hold勝ち) / 0以下先着=0(崩れ=lock) / どちらもなければ末尾符号
        tgt = None
        for j in range(jdec, j1 + 1):
            p = (ep - close[j]) / ep * 100.0
            if p >= L2:
                tgt = 1
                break
            if p <= 0.0:
                tgt = 0
                break
        if tgt is None:
            tgt = 1 if (ep - close[j1]) / ep * 100.0 > L else 0
        # 決定バー jdec の因果特徴（jdec までに確定した値のみ）
        mom3 = (close[jdec - 3] - close[jdec]) / close[jdec - 3] * 100.0   # +なら価格下落継続=SHORT有利
        mom6 = (close[jdec - 6] - close[jdec]) / close[jdec - 6] * 100.0
        recs.append(dict(target=tgt, bars_to_dec=jdec - i0,
                         stoch_k=stoch[jdec], rsi9=rsi9[jdec], adx=adx[jdec], atr_pct=atrp[jdec],
                         mom3=mom3, mom6=mom6))
    return pd.DataFrame(recs)


def rank_features(dtr, dsc, feats):
    print(f"\n  分離ランキング（益+{L}%到達玉・target=1 hold勝ち[+{L2}%先着] / 0 崩れ[0以下先着]）")
    print(f"  学習窓 n={len(dtr)}（hold勝ち {dtr.target.mean()*100:.0f}%） / 採点窓 n={len(dsc)}（hold勝ち {dsc.target.mean()*100:.0f}%）")
    print(f"  {'特徴':<12}{'学習corr':>10}{'採点corr':>10}{'両窓':>6}   勝ち中央 vs 崩れ中央（採点窓）")
    out = []
    for f in feats:
        ctr = dtr[f].corr(dtr["target"])
        csc = dsc[f].corr(dsc["target"])
        same = "✓" if (np.sign(ctr) == np.sign(csc) and abs(ctr) > 0.03 and abs(csc) > 0.03) else "✗"
        w = dsc[dsc.target == 1][f].median()
        l = dsc[dsc.target == 0][f].median()
        out.append((abs(csc), f, ctr, csc, same, w, l))
    for _, f, ctr, csc, same, w, l in sorted(out, reverse=True):
        print(f"  {f:<12}{ctr:>+10.3f}{csc:>+10.3f}{same:>6}   hold勝ち {w:>8.3f} vs 崩れ {l:>8.3f}")


def main():
    print("=" * 100)
    print(f"状態機械の分離可能性（益+{L}%時点で hold勝ち[C] と 崩れ[A] を因果指標で見分けられるか・両窓）")
    print("=" * 100)
    df, v15p_base, up20 = build_setup()
    trades = run_cfg(df, v15p_base, up20, {})      # incumbent
    arrs = (df["close"].to_numpy(float), df["stoch_k"].to_numpy(float), df["rsi9"].to_numpy(float),
            df["adx"].to_numpy(float), df["atr_pct"].to_numpy(float))
    idx_of = {pd.Timestamp(t).value: i for i, t in enumerate(df["ts"].to_numpy())}

    dtr = build_records(trades, arrs, idx_of, pd.Timestamp("2021-04-01"), TRAIN_END)
    dsc = build_records(trades, arrs, idx_of, SC_START, SCORE_END)
    feats = ["stoch_k", "rsi9", "adx", "atr_pct", "mom3", "mom6", "bars_to_dec"]
    rank_features(dtr, dsc, feats)

    # 最強特徴の分位別 hold勝ち率（採点窓）＝閾値でなく傾向を見る
    if len(dsc):
        best = max(feats, key=lambda f: abs(dsc[f].corr(dsc["target"])))
        print(f"\n  [最強特徴 {best} の5分位別 hold勝ち率（採点窓）＝単調なら状態機械の分岐に使える]")
        dsc2 = dsc.copy()
        try:
            dsc2["q"] = pd.qcut(dsc2[best], 5, labels=False, duplicates="drop")
            g = dsc2.groupby("q").agg(n=("target", "size"), hold_win=("target", "mean"))
            for q, row in g.iterrows():
                print(f"    分位{int(q)}: n={int(row['n']):>4}  hold勝ち率 {row['hold_win']*100:>5.0f}%")
        except Exception as e:
            print(f"    （分位計算スキップ: {e}）")

    print("\n  ⚠️ これは分離の存在確認（Check）＝閾値は焼かない。状態機械の分岐は場面×タイプ別に ML 学習し、")
    print("     採否は実エンジン両窓 score.py（L-267）。因果指標のみ使用＝leak なし。")


if __name__ == "__main__":
    main()
