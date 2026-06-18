#!/usr/bin/env python3
"""report.py — 結果レポート1本化（V9検証時代の散らばった出力を A〜I に統合）

使い方:
  python3 report.py <trades.csv> [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--vs <v9_full.csv>]

役割: 売買記録CSVを食わせると整理された結果一覧を出すだけ（戦略ロジックなし・replay呼ばない=安全）。
  - 公式 net / NET/day / 月別 は score.py（固定審判・改造しない）から取得
  - 内訳（A リスク指標・B〜L）は**全節 審判式**（score.py と同じコスト式・現行計器・funding 除く）で行単位に再計算して集計
    ⚠️ 旧仕様（CSV の net_usd 列をそのまま集計）は E0.4 trail maker 化以降 P21 の trail 行が旧計器の値になり
    誤表示だった（2026-06-12 まこさん指摘「間違った数字を出すレポートはゴミ以下」→ 全節を審判式に統一）
出力: A全体 / B優先度別 / C出口理由別 / D サイズ・add別 / E ベスト・ワースト / F月別(+AI vs V9) /
      G指標帯別 / H予測確率帯別(p列があれば) / I MFE/MAE別
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score as judge                                    # 固定審判（import のみ）
import eval_engine as ee                                 # 確定コスト定数（import のみ・改造禁止）
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


def _collapse_positions(d):
    """position_id があれば玉(取引)単位に集約（fill/add 複数行を1取引に・position-level accounting）。
    金額(net/gross/fee/size/_netj等)=合計・hold_min=最大・入口特徴/出口理由/entry_time=最初。
    position_id 無し or 既に1行1玉(P23/E34)はそのまま返す（後方互換・退化させない）。"""
    if "position_id" not in d.columns or d["position_id"].nunique() == len(d):
        return d
    agg = {}
    for c in d.columns:
        if c == "position_id":
            continue
        agg[c] = "sum" if c in ("net_usd", "gross_usd", "fee_usd", "size_btc", "_gross", "_fee", "_slip", "_netj") \
            else ("max" if c == "hold_min" else "first")
    return d.groupby("position_id", as_index=False).agg(agg)


def _funding_collapse(d):
    """公式 score.py と揃える(funding込み net)＋取引(玉)単位に集約＝analyze.py と整合・KB §0。"""
    import numpy as np
    if "_netj" in d.columns and "side" in d.columns:
        fund = np.array([judge._funding_for_trade(r["entry_time"], r["exit_time"],
                         1 if r["side"] == "LONG" else -1, r["size_btc"], r["entry_price"]) for _, r in d.iterrows()])
        d = d.copy(); d["net_usd"] = d["_netj"] - fund
    return _collapse_positions(d)


def _judge_cols(t):
    """審判（score.py）と同じ式で gross/手数料/slip/net を行単位に再計算し、内訳用の列を上書きする。
    CSV の net_usd は「生成時の計器」の値＝E0.4（trail maker 化）以降 trail 行が旧値のため表示に使わない。"""
    t = t.copy()
    mk = getattr(judge, "MAKER_EXIT_REASONS", {"TP_FILLED", "SL_FILLED", "TRAIL_EXIT"})
    dirn = t["side"].map({"LONG": 1, "SHORT": -1}).fillna(-1)
    tk = (~t["exit_reason"].isin(mk)).astype(float)
    t["_gross"] = (t["exit_price"] - t["entry_price"]) * t["size_btc"] * dirn
    t["_fee"] = t["entry_price"] * t["size_btc"] * ee.MAKER_FEE \
        + t["exit_price"] * t["size_btc"] * (tk * ee.TAKER_FEE + (1 - tk) * ee.MAKER_FEE)
    t["_slip"] = t["exit_price"] * t["size_btc"] * ee.SLIPPAGE * tk
    t["_netj"] = t["_gross"] - t["_fee"] - t["_slip"]
    t["net_usd"] = t["_netj"]; t["gross_usd"] = t["_gross"]; t["fee_usd"] = t["_fee"] + t["_slip"]
    return t


def _grp(d, by, net="net_usd"):
    g = d.groupby(by, observed=True)
    out = pd.DataFrame({"件数": g.size(), "純益": g[net].sum().round(0),
                        "平均": g[net].mean().round(2), "勝率%": (g[net].apply(lambda x: (x > 0).mean()) * 100).round(1)})
    if "p" in d.columns: out["平均prob"] = g["p"].mean().round(3)
    if "hold_min" in d.columns: out["平均保有"] = g["hold_min"].mean().round(0)
    return out


def _print_params(csv_path):
    """節0: 戦略が記録した使用パラメータ サイドカー（<stem>_params.json）を表示（params_sidecar.write_sidecar が出力）。
    無ければ注記して継続（後方互換）。戦略名で分岐せず JSON の sections を汎用に列挙する（E36/E37 でもそのまま効く）。"""
    sp = Path(csv_path).with_name(f"{Path(csv_path).stem}_params.json")
    print("\n  0. 使用パラメータ（戦略が実行時に記録した実使用値・指標/閾値/TP/SL/TimeExit）")
    if not sp.exists():
        print(f"     （パラメータ記録なし: {sp.name} が無い。戦略にサイドカー出力を足して再走すると表示されます）")
        return
    try:
        pj = json.loads(sp.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"     （パラメータJSON 読み込み失敗: {e}）")
        return
    print(f"     戦略 {pj.get('strategy', '?')} / script {pj.get('script', '?')} / 実験 {pj.get('experiment', '?')}")
    if pj.get("run_args"):
        print(f"     実行引数: {pj['run_args']}")
    for sec, params in (pj.get("sections") or {}).items():
        print(f"     [{sec}]")
        if isinstance(params, dict):
            for k, v in params.items():
                print(f"        {k}: {v}")
        else:
            print(f"        {params}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv"); ap.add_argument("--start"); ap.add_argument("--end"); ap.add_argument("--vs")
    a = ap.parse_args()
    d = _load(a.csv, a.start, a.end)
    if not len(d):
        print("空CSV"); return
    d_raw = d.copy()                                     # 審判（score.py）には CSV 原本を渡す（fill単位・公式 total用）
    d = _judge_cols(d)                                   # 内訳は全節 審判式（現行計器）で集計
    d = _funding_collapse(d)                             # ★公式 funding込み net ＋ 取引(玉)単位に集約（analyze.py と整合・KB §0 取引単位）
    has_p = "p" in d.columns
    name = Path(a.csv).name
    out_path = Path(a.csv).with_name(f"report_{Path(a.csv).stem}.txt")   # 結果一覧を書類保存
    _rf = open(out_path, "w", encoding="utf-8"); _orig = sys.stdout; sys.stdout = _Tee(_orig, _rf)

    # ===== 0. 使用パラメータ（戦略が記録したサイドカー・指標/閾値/TP/SL/TimeExit）=====
    _print_params(a.csv)

    # ===== A. 全体サマリー =====
    r = judge.score(d_raw)                               # 公式 net / 月別（原本で採点）
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
          f" / 内訳net(審判式・funding込み・公式一致) ${d['net_usd'].sum():.0f}")
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
    mo = (d.assign(_m=d["entry_time"].dt.strftime("%Y-%m")).groupby("_m")["net_usd"]    # ★玉単位（A節・合計と整合）
          .agg(純益="sum", 件数="size").rename_axis("月")); mo["純益"] = mo["純益"].round(0)
    if a.vs:
        v = _funding_collapse(_judge_cols(_load(a.vs, a.start, a.end)))                 # ★V9 も玉単位・funding込み（AI と単位を揃える）
        dm = d.assign(_m=d["entry_time"].dt.strftime("%Y-%m")).groupby("_m")["net_usd"].agg(["sum", "size"])
        vm = v.assign(_m=v["entry_time"].dt.strftime("%Y-%m")).groupby("_m")["net_usd"].agg(["sum", "size"])
        cmp = pd.DataFrame({"AI純益": dm["sum"].round(0), "AI件数": dm["size"],
                            "V9純益": vm["sum"].round(0), "V9件数": vm["size"]}).fillna(0).rename_axis("月")
        print(cmp.to_string()); print(f"   合計  AI ${d['net_usd'].sum():.0f}({len(d)}件)  vs  V9 ${v['net_usd'].sum():.0f}({len(v)}件)  → 差 ${d['net_usd'].sum()-v['net_usd'].sum():+.0f}")
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
    d = d.copy()
    if "atr_14" in d.columns and "entry_price" in d.columns:
        d["atr_pct"] = (d["atr_14"] / d["entry_price"] * 100)
    if "stoch_d_at_entry" in d.columns and "stoch_k_at_entry" in d.columns:
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

    # ===== J. コスト分解（審判式・出口別・②執行の判定材料・2026-06-12 まこさん承認）=====
    dj = d                                                # 全節 審判式に統一済み（_judge_cols）
    print("\n  J. コスト分解（審判式＝現行計器・funding除く・gross黒字なのにnet赤=②執行＝手数料負け）")
    gj = dj.groupby("exit_reason")
    jt = pd.DataFrame({"件数": gj.size(), "gross": gj["_gross"].sum().round(0), "手数料": gj["_fee"].sum().round(0),
                       "slip": gj["_slip"].sum().round(0), "net": gj["_netj"].sum().round(0)})
    print(jt.rename(index=EXIT_JP).rename_axis("出口理由").to_string())
    print(f"   合計: gross ${dj['_gross'].sum():,.0f} / 手数料 ${dj['_fee'].sum():,.0f}"
          f"（gross比 {dj['_fee'].sum()/max(1e-9, abs(dj['_gross'].sum()))*100:.0f}%）"
          f" / slip ${dj['_slip'].sum():,.0f} / net ${dj['_netj'].sum():,.0f}")

    # ===== K. 期待値4要素（勝率×平均勝ち−負率×平均負け・trade_analysis_methods_kb §1）=====
    def _exp_row(t, label):
        win = t[t["_netj"] > 0]; los = t[t["_netj"] <= 0]
        wr = len(win) / max(1, len(t))
        aw = float(win["_netj"].mean()) if len(win) else 0.0
        al = abs(float(los["_netj"].mean())) if len(los) else 0.0
        return {"集団": label, "件数": len(t), "勝率%": round(wr * 100, 1), "平均勝ち$": round(aw, 2),
                "平均負け$": round(al, 2), "期待値$/件": round(wr * aw - (1 - wr) * al, 2),
                "コスト$/件": round(float((t["_fee"] + t["_slip"]).mean()), 2),
                "gross$/件": round(float(t["_gross"].mean()), 2)}
    rows_k = [_exp_row(dj, "今回")]
    if a.vs:
        vj = v                                            # _judge_cols 済み
        rows_k.append(_exp_row(vj, "ベースライン"))
    print("\n  K. 期待値4要素（どのレバーが動いたかを特定・--vs でベースライン比較）")
    print("   " + pd.DataFrame(rows_k).set_index("集団").to_string().replace("\n", "\n   "))

    # ===== L. 限界分解（--vs 時のみ・追加/削除した玉だけの採算・件数レバーの事前/事後ゲート）=====
    if a.vs:
        vset = set(v["entry_time"]); dset = set(d["entry_time"])
        print("\n  L. 限界分解（ベースラインとの集合差・breakeven倍率=平均gross÷往復コスト・<1=手数料負け確定/<1.5=危険域）")
        for lbl, t in (("追加した玉", dj[~dj["entry_time"].isin(vset)]), ("削った玉", vj[~vj["entry_time"].isin(dset)])):
            if not len(t):
                print(f"   {lbl}: なし"); continue
            ag = float(t["_gross"].mean()); ac = float((t["_fee"] + t["_slip"]).mean())
            be = ag / ac if ac > 0 else float("inf")
            print(f"   {lbl}: {len(t)}件 / gross ${t['_gross'].sum():,.0f} / net ${t['_netj'].sum():,.0f}"
                  f" / 平均gross ${ag:.2f}/件 / 往復コスト ${ac:.2f}/件 / breakeven倍率 {be:.2f}")

    sys.stdout = _orig; _rf.close()
    print(f"\n[保存] この結果一覧を書類化 → {out_path}（IDEで開いて確認できます）")


if __name__ == "__main__":
    main()
