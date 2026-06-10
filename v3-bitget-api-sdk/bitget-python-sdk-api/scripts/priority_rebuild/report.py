#!/usr/bin/env python3
"""report.py — 結果レポート1本化（V9検証時代の散らばった出力を A〜I に統合）

使い方:
  python3 report.py <trades.csv> [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--vs <v9_full.csv>]

役割: 売買記録CSVを食わせると整理された結果一覧を出すだけ（戦略ロジックなし・replay呼ばない=安全）。
  - 公式 net / NET/day / 月別 は score.py（固定審判・改造しない）から取得
  - 内訳(B〜I)は CSV の engine net_usd（= gross - maker/taker fee。slippage/funding は審判が別途加算）で集計
出力: A全体 / B優先度別 / C出口理由別 / D サイズ・add別 / E ベスト・ワースト / F月別(+AI vs V9) /
      G指標帯別 / H予測確率帯別(p列があれば) / I MFE/MAE別
"""
from __future__ import annotations
import argparse, os, sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score as judge                                    # 固定審判（import のみ）
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 30)
SIDE_JP = {"LONG": "買い", "SHORT": "売り"}
EXIT_JP = {"TP_FILLED": "利確(TP)", "SL_FILLED": "損切(SL)", "TIME_EXIT": "時間切れ", "MFE_STALE_CUT": "含み益失速",
           "STOCH_REVERSE_EXIT": "ストキャス反転", "RSI_REVERSE_EXIT": "RSI反転", "TRAIL_EXIT": "トレール",
           "PROFIT_LOCK": "利益確保", "MAE_CUT": "含み損切", "MIDTERM_CUT": "中期切", "FORCE_CLOSE_EOD": "期末強制"}


class _Tee:
    """print 出力を端末とファイルの両方へ流す（結果一覧を書類として保存する）。"""
    def __init__(self, *streams): self.streams = streams
    def write(self, x):
        for s in self.streams: s.write(x)
    def flush(self):
        for s in self.streams: s.flush()


def _load(path, start, end):
    d = pd.read_csv(path)
    d["entry_time"] = pd.to_datetime(d["entry_time"]); d["exit_time"] = pd.to_datetime(d["exit_time"])
    if start: d = d[d["entry_time"] >= pd.Timestamp(start)]
    if end:   d = d[d["entry_time"] < pd.Timestamp(end) + pd.Timedelta(days=1)]
    return d.reset_index(drop=True)


def _band(s, edges, labels):
    return pd.cut(s, bins=edges, labels=labels, right=False)


def _grp(d, by, net="net_usd"):
    g = d.groupby(by, observed=True)
    out = pd.DataFrame({"件数": g.size(), "純益": g[net].sum().round(0),
                        "平均": g[net].mean().round(2), "勝率%": (g[net].apply(lambda x: (x > 0).mean()) * 100).round(1)})
    if "p" in d.columns: out["平均prob"] = g["p"].mean().round(3)
    if "hold_min" in d.columns: out["平均保有"] = g["hold_min"].mean().round(0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv"); ap.add_argument("--start"); ap.add_argument("--end"); ap.add_argument("--vs")
    a = ap.parse_args()
    d = _load(a.csv, a.start, a.end)
    if not len(d):
        print("空CSV"); return
    has_p = "p" in d.columns
    name = Path(a.csv).name
    out_path = Path(a.csv).with_name(f"report_{Path(a.csv).stem}.txt")   # 結果一覧を書類保存
    _rf = open(out_path, "w", encoding="utf-8"); _orig = sys.stdout; sys.stdout = _Tee(_orig, _rf)

    # ===== A. 全体サマリー =====
    r = judge.score(d)                                   # 公式 net / 月別
    days = max(1, (d["exit_time"].max() - d["entry_time"].min()).days)
    eq = d.sort_values("exit_time")["net_usd"].cumsum()
    dd = (eq.cummax() - eq).max()
    sign = (d.sort_values("exit_time")["net_usd"] < 0).astype(int)
    streak = (sign * (sign.groupby((sign != sign.shift()).cumsum()).cumcount() + 1)).max()
    daily = d.groupby(d["exit_time"].dt.date)["net_usd"].sum()
    dn = d.groupby(d["exit_time"].dt.normalize())["net_usd"].sum()
    dn = dn.reindex(pd.date_range(dn.index.min(), dn.index.max(), freq="D"), fill_value=0)
    _sd, _dsd = dn.std(), dn[dn < 0].std()
    sharpe = dn.mean() / _sd * (365 ** 0.5) if _sd and _sd > 0 else 0.0
    sortino = dn.mean() / _dsd * (365 ** 0.5) if _dsd and _dsd > 0 else 0.0
    _w = d.loc[d["net_usd"] > 0, "net_usd"].sum(); _l = abs(d.loc[d["net_usd"] < 0, "net_usd"].sum())
    pf = _w / _l if _l > 0 else float("inf")
    recov = r["total"] / dd if dd > 0 else float("inf")
    print("=" * 70); print(f"  結果レポート: {name}   期間 {d['entry_time'].min().date()}〜{d['entry_time'].max().date()} ({days}日)")
    print("=" * 70)
    print(f"  A. 全体  トレード数 {len(d)} / 粗利 ${d['gross_usd'].sum():.0f} / 手数料 ${d['fee_usd'].sum():.0f}"
          f"（{d['fee_usd'].sum()/max(1,abs(d['gross_usd'].sum()))*100:.0f}% ・ ${d['fee_usd'].mean():.2f}/件）")
    print(f"         純益(審判) ${r['total']:.0f} / 月平均 ${r['monthly_avg']:.0f} / 日次純益 ${r['total']/days:.2f}"
          f" / 計器純益 ${d['net_usd'].sum():.0f}")
    print(f"         勝率 {(d['net_usd']>0).mean()*100:.1f}% / 最大DD ${dd:.0f} / 最大連敗 {int(streak)} / 日次最悪 ${daily.min():.0f}")
    print(f"         Sharpe {sharpe:.2f} / Sortino {sortino:.2f} / Profit Factor {pf:.2f} / Recovery {recov:.2f}（日次USD純益・年率365）")

    # ===== B. 優先度別 =====
    print("\n  B. 優先度別")
    print(_grp(d, ["priority", "side"]).rename(index=SIDE_JP).rename_axis(["優先度", "方向"]).to_string())

    # ===== C. 出口理由別（LONG/SHORT 列）=====
    print("\n  C. 出口理由別")
    piv = d.pivot_table(index="exit_reason", columns="side", values="net_usd", aggfunc="sum", observed=True).round(0)
    cnt = d.pivot_table(index="exit_reason", columns="side", values="net_usd", aggfunc="size", observed=True)
    piv.columns = [f"純益_{SIDE_JP.get(c, c)}" for c in piv.columns]; cnt.columns = [f"件数_{SIDE_JP.get(c, c)}" for c in cnt.columns]
    cm = pd.concat([cnt, piv], axis=1).fillna(0)
    cm["平均保有"] = d.groupby("exit_reason")["hold_min"].mean().round(0)
    print(cm.rename(index=EXIT_JP).rename_axis("出口理由").to_string())

    # ===== D. サイズ / add 別（増強）=====
    print("\n  D. サイズ・add別（mean が右肩上がりなら買い増しが効いている）")
    dd2 = _grp(d, "size_btc"); dd2["平均買増"] = d.groupby("size_btc")["add_count"].mean().round(2)
    print(dd2.rename_axis("サイズ").to_string())

    # ===== E. ベスト / ワースト（入った時の指標値＝閾値の組み合わせ付き・ベスト/ワースト10）=====
    _ind = ["adx_at_entry", "bb_mid_slope_at_entry", "stoch_k_at_entry", "stoch_d_at_entry", "atr_14", "rsi_at_entry"]
    cols = [c for c in ["entry_time", "exit_reason", "hold_min", "add_count", "net_usd"] if c in d.columns] \
        + [c for c in _ind if c in d.columns]
    _cjp = {"entry_time": "日時", "exit_reason": "出口理由", "hold_min": "保有分", "add_count": "add数", "net_usd": "純益",
            "adx_at_entry": "ADX", "bb_mid_slope_at_entry": "bb傾き", "stoch_k_at_entry": "stochK",
            "stoch_d_at_entry": "stochD", "atr_14": "ATR", "rsi_at_entry": "RSI"}
    def _disp(t):
        t = t.copy()
        for c in _ind + ["hold_min", "net_usd"]:
            if c in t.columns: t[c] = t[c].round(1)
        t = t.rename(columns=_cjp)
        if "出口理由" in t.columns: t["出口理由"] = t["出口理由"].map(EXIT_JP).fillna(t["出口理由"])
        return t
    print("\n  E. ベスト10（指標値＝入った時の閾値の組み合わせ・V9閾値: ADX30-50/bb傾き<-10/ATR≥150 と対比）")
    print(_disp(d.nlargest(10, "net_usd")[cols]).to_string(index=False))
    print("     ワースト10")
    print(_disp(d.nsmallest(10, "net_usd")[cols]).to_string(index=False))

    # ===== F. 月別（+AI vs V9）=====
    print("\n  F. 月別 純益（審判）")
    mo = r["monthly"].copy().rename(columns={"net_usd": "純益", "n": "件数"}).rename_axis("月"); mo["純益"] = mo["純益"].round(0)
    if a.vs:
        v = _load(a.vs, a.start, a.end); rv = judge.score(v)
        cmp = pd.DataFrame({"AI純益": r["monthly"]["net_usd"].round(0), "AI件数": r["monthly"]["n"],
                            "V9純益": rv["monthly"]["net_usd"].round(0), "V9件数": rv["monthly"]["n"]}).fillna(0).rename_axis("月")
        print(cmp.to_string()); print(f"   合計  AI ${r['total']:.0f}({len(d)}件)  vs  V9 ${rv['total']:.0f}({len(v)}件)  → 差 ${r['total']-rv['total']:+.0f}")
    else:
        print(mo.to_string())

    # ===== F2/F3/F4. 時系列（月別×出口理由/サイズ・1日あたり）=====
    d["_m"] = d["entry_time"].dt.strftime("%Y-%m")
    print("\n  F2. 月別 × 出口理由（純益）")
    print(d.pivot_table(index="_m", columns="exit_reason", values="net_usd", aggfunc="sum", observed=True)
          .rename(columns=EXIT_JP).round(0).fillna(0).rename_axis("月").to_string())
    print("\n  F3. 月別 × サイズ・add（純益／件数）")
    pvs = d.pivot_table(index="_m", columns="size_btc", values="net_usd", aggfunc=["sum", "size"]).fillna(0).round(0)
    pvs.columns = [f"{'純益' if a=='sum' else '件数'}_{b}" for a, b in pvs.columns]
    print(pvs.rename_axis("月").to_string())
    adays = d["entry_time"].dt.date.nunique()
    print(f"\n  F4. 1日あたり（取引のあった {adays} 日で平均）")
    print(f"   トレード数 {len(d)/adays:.2f} 件/日 ・ 純益 ${r['total']/adays:.2f}/取引日")
    er = (d["exit_reason"].map(EXIT_JP).value_counts() / adays).round(2)
    print("   出口理由別 件数/日: " + " / ".join(f"{k} {v}" for k, v in er.items()))
    sz = (d["size_btc"].value_counts().sort_index() / adays).round(2)
    print("   サイズ別 件数/日: " + " / ".join(f"{k} {v}" for k, v in sz.items()))

    # ===== G. 指標帯別 net/勝率 =====
    print("\n  G. 指標帯別（エッジがどの帯に居るか・V9手書き閾値が最適かを見る）")
    d = d.copy(); d["atr_pct"] = (d["atr_14"] / d["entry_price"] * 100)
    d["stoch_gap"] = (d["stoch_d_at_entry"] - d["stoch_k_at_entry"])
    _e = lambda x: "" if abs(x) >= 9e8 else f"{x:g}"
    bands = {
        "ADX":       ("adx_at_entry",          [0, 20, 25, 30, 35, 40, 50, 9e9]),
        "ATR%":      ("atr_pct",               [0, 0.2, 0.3, 0.4, 0.5, 0.7, 9e9]),
        "stochギャップ": ("stoch_gap",          [0, 0.3, 1, 3, 6, 9e9]),
        "bb傾き":    ("bb_mid_slope_at_entry",  [-9e9, -30, -20, -10, 0, 9e9]),
    }
    for label, (col, edges) in bands.items():
        if col not in d.columns: continue
        lab = [f"{_e(edges[i])}〜{_e(edges[i+1])}" for i in range(len(edges) - 1)]
        d["_b"] = _band(d[col], edges, lab)
        print(f"   [{label}]")
        print("   " + _grp(d, "_b").drop(columns=["平均保有"], errors="ignore").rename_axis("帯").to_string().replace("\n", "\n   "))

    # ===== H. 予測確率帯別（ML のとき）=====
    if has_p:
        print("\n  H. 予測確率帯別（AIの自信度が儲けと対応しているか=較正）")
        d["_pb"] = _band(d["p"], [0, 0.4, 0.5, 0.56, 0.6, 0.7, 1.01], ["〜0.4", "0.4〜0.5", "0.5〜0.56", "0.56〜0.6", "0.6〜0.7", "0.7〜"])
        print("   " + _grp(d, "_pb").drop(columns=["平均保有"], errors="ignore").rename_axis("確率帯").to_string().replace("\n", "\n   "))

    # ===== I. MFE/MAE 別 =====
    if "mfe_usd" in d.columns and "mae_usd" in d.columns:
        print("\n  I. MFE(含み益ピーク)/MAE(含み損ピーク)別（出口が利益を取り逃していないか）")
        d["_mfe"] = _band(d["mfe_usd"], [-1, 5, 15, 30, 60, 9e9], ["〜5", "5〜15", "15〜30", "30〜60", "60〜"])
        gm = _grp(d, "_mfe").drop(columns=["平均保有"], errors="ignore").rename_axis("MFE帯")
        gm["平均MFE"] = d.groupby("_mfe", observed=True)["mfe_usd"].mean().round(1)
        gm["取り逃し率%"] = (100 * (1 - d.groupby("_mfe", observed=True)["net_usd"].mean() /
                                    d.groupby("_mfe", observed=True)["mfe_usd"].mean())).round(0)
        print("   " + gm.to_string().replace("\n", "\n   "))

    sys.stdout = _orig; _rf.close()
    print(f"\n[保存] この結果一覧を書類化 → {out_path}（IDEで開いて確認できます）")


if __name__ == "__main__":
    main()
