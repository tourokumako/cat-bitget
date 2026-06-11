#!/usr/bin/env python3
"""analyze.py — 採点後の深掘りバッテリー（手抜き分析を物理的に不可能にする・1コマンドで全部出す）

なぜあるか（2026-06-12 まこさん「手抜き分析できない仕組みは無いのか」への実装回答）:
  E21 の敗因を「分布シフト」と誤分類した原因は、CC が見る項目を自分で選んで手数料分解・交差表・
  個別読みを省略したこと。読ませる・決意では直らない（実証済）ので、今日手作業でやった深掘りを
  全節機械化し、pdca_gate hook の必須成果物にする（score.py 採点後 これを回すまでターン終了不可）。
  数字は機械が出す＝「やったふり」が不可能。CC の仕事は各表の隣の解釈に限定され、まこさんは
  ledger の原因究明（3分類）と本書類の数字のズレを30秒で見抜ける。

使い方:
  python3 analyze.py <trades.csv> [--train <学習期間trades.csv>] [--candles <5m OHLCV csv>]

節（全節 審判式 = report._judge_cols・analysis_playbook §2 / trade_analysis_methods_kb 対応）:
  N1 損失の時間構造（最大DDの期間と深さ・最悪日・最大連敗の日付）         … §2.4
  N2 条件交差表（ATR%×bb傾き・ADX×ATR% の net/件数）                   … §2 条件分解
  N3 系列依存（前トレードからの間隔別の採算・再突入の質）               … §2 系列
  N4 分布ドリフト（--train 指定時・学習期間との帯構成差）               … 門番が死ぬ機構の検出
  N5 ブートストラップ（net/件 と 月次net の95%区間・seed固定42）        … §0.4 統計的頑健性
  N6 ワースト10の個別読み（--candles 指定時 entry前後±12本のOHLCV）     … §2.9 個別トレード読み
  N7 必要勝率と不足量（平均勝ち/平均負け→損益分岐勝率 vs 実際・pt差）    … KB §1 期待値（2026-06-12 追加）
  N8 負け玉の解剖（SL/負け玉の entry特徴中央値 vs 勝ち玉・月別集中）     … KB §4（同上）
  N9 出口効率（勝ち玉の MFE捕捉率 vs 業界基準 0.6-0.75）               … KB §3（同上）

  ⚠️ N1〜N9 は「分析の最低ライン（数字の抽出）」であって分析のゴールではない。
     ledger には 5つの問い（レバー/不足量/負け集中/過去接続/次仮説）への答えを書く
     （hook require_5q が物理強制・2026-06-12 まこさん合意）。
"""
from __future__ import annotations
import argparse, os, sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import report                                     # _judge_cols / _Tee（審判式・正本1箇所）

BANDS = {
    "ATR%":   ("atr_pct",      [0, 0.15, 0.2, 0.3, 0.4, 9e9]),
    "ADX":    ("adx_at_entry", [0, 20, 25, 30, 40, 9e9]),
    "bb傾き":  ("bb_mid_slope_at_entry", [-9e9, -30, -10, 0, 9e9]),
}


def _load(path):
    d = pd.read_csv(path)
    d["entry_time"] = pd.to_datetime(d["entry_time"]); d["exit_time"] = pd.to_datetime(d["exit_time"])
    d = report._judge_cols(d)
    d["atr_pct"] = d["atr_14"] / d["entry_price"] * 100
    return d.sort_values("entry_time").reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv"); ap.add_argument("--train"); ap.add_argument("--candles")
    a = ap.parse_args()
    d = _load(a.csv)
    name = Path(a.csv).name
    out_path = Path(a.csv).with_name(f"analysis_{Path(a.csv).stem}.txt")
    _rf = open(out_path, "w", encoding="utf-8")
    sys.stdout = report._Tee(sys.__stdout__, _rf)
    print("=" * 70)
    print(f"  深掘り分析: {name}   {d['entry_time'].min().date()}〜{d['entry_time'].max().date()} / {len(d)}件 / 審判式net ${d['net_usd'].sum():.0f}")
    print("=" * 70)

    # ===== N1. 損失の時間構造 =====
    e = d.sort_values("exit_time")
    eq = e["net_usd"].cumsum()
    peak = eq.cummax(); dd = peak - eq
    i_tr = dd.idxmax()
    i_pk = eq.loc[:i_tr].idxmax()
    daily = d.groupby(d["exit_time"].dt.date)["net_usd"].sum().sort_values()
    sign = (e["net_usd"] < 0).astype(int)
    runs = sign * (sign.groupby((sign != sign.shift()).cumsum()).cumcount() + 1)
    print("\n  N1. 損失の時間構造")
    print(f"   最大DD ${dd.max():.0f}: ピーク {e.loc[i_pk,'exit_time'].date()} → 底 {e.loc[i_tr,'exit_time'].date()}"
          f"（{(e.loc[i_tr,'exit_time']-e.loc[i_pk,'exit_time']).days}日間・この間 {int(((e.index>i_pk)&(e.index<=i_tr)).sum())}件）")
    if runs.max() > 0:
        i_end = runs.idxmax()
        print(f"   最大連敗 {int(runs.max())}連敗（終端 {e.loc[i_end,'exit_time']}）")
    print("   最悪日 top5: " + " / ".join(f"{dt} ${v:.0f}" for dt, v in daily.head(5).items()))

    # ===== N2. 条件交差表 =====
    print("\n  N2. 条件交差表（純益$ / 件数）")
    for rl, cl in (("ATR%", "bb傾き"), ("ADX", "ATR%")):
        (rc_, re_), (cc_, ce_) = BANDS[rl], BANDS[cl]
        r = pd.cut(d[rc_], re_, right=False); c = pd.cut(d[cc_], ce_, right=False)
        net = d.pivot_table(values="net_usd", index=r, columns=c, aggfunc="sum", observed=False).round(0)
        cnt = d.pivot_table(values="net_usd", index=r, columns=c, aggfunc="size", observed=False)
        print(f"   [{rl} × {cl}] 純益$")
        print("   " + net.to_string().replace("\n", "\n   "))
        print(f"   [{rl} × {cl}] 件数")
        print("   " + cnt.to_string().replace("\n", "\n   "))

    # ===== N3. 系列依存 =====
    gap = (d["entry_time"] - d["exit_time"].shift()).dt.total_seconds() / 60
    gb = pd.cut(gap, [0, 5, 30, 120, 720, 9e9], labels=["≤5分", "5-30分", "30分-2h", "2h-12h", ">12h"], right=False)
    g = d.groupby(gb, observed=True)["net_usd"]
    prev_loss = (d["net_usd"].shift() < 0)
    print("\n  N3. 系列依存（前トレード決済からの間隔別・再突入の質）")
    print("   " + pd.DataFrame({"件数": g.size(), "純益": g.sum().round(0), "平均": g.mean().round(2)}).to_string().replace("\n", "\n   "))
    for lbl, m in (("直前が負け", prev_loss), ("直前が勝ち", ~prev_loss)):
        t = d[m & gap.notna()]
        if len(t):
            print(f"   {lbl}の直後: {len(t)}件 / 平均 ${t['net_usd'].mean():.2f}")

    # ===== N4. 分布ドリフト =====
    if a.train:
        tr = _load(a.train)
        print(f"\n  N4. 分布ドリフト 学習期間({Path(a.train).name}) vs 本CSV")
        for label, (col, edges) in BANDS.items():
            s_tr = pd.cut(tr[col], edges, right=False).value_counts(normalize=True).sort_index() * 100
            s_te = pd.cut(d[col], edges, right=False).value_counts(normalize=True).sort_index() * 100
            tab = pd.DataFrame({"学習%": s_tr.round(1), "本CSV%": s_te.round(1), "差pt": (s_te - s_tr).round(1)})
            print(f"   [{label}] 最大シフト {(s_te - s_tr).abs().max():.1f}pt")
            print("   " + tab.to_string().replace("\n", "\n   "))

    # ===== N5. ブートストラップ =====
    rng = np.random.default_rng(42)
    x = d["net_usd"].to_numpy()
    bs = np.array([rng.choice(x, len(x), replace=True).mean() for _ in range(2000)])
    mo = d.groupby(d["entry_time"].dt.to_period("M"))["net_usd"].sum().to_numpy()
    bm = np.array([rng.choice(mo, len(mo), replace=True).mean() for _ in range(2000)])
    print("\n  N5. ブートストラップ95%区間（seed=42・2000回）")
    print(f"   net/件: 実測 ${x.mean():.2f} / 区間 [{np.percentile(bs,2.5):.2f}, {np.percentile(bs,97.5):.2f}]"
          f"{'  ⚠️区間が0を跨ぐ＝プラスは偶然の可能性' if np.percentile(bs,2.5) < 0 else ''}")
    print(f"   月次net: 実測 ${mo.mean():.0f} / 区間 [{np.percentile(bm,2.5):.0f}, {np.percentile(bm,97.5):.0f}]")

    # ===== N6. ワースト10 個別読み =====
    w = d.nsmallest(10, "net_usd")
    print("\n  N6. ワースト10 個別読み" + ("（entry前後±12本のOHLCV）" if a.candles else "（--candles 未指定・特徴量のみ）"))
    if a.candles:
        cd = pd.read_csv(a.candles)
        tcol = next(c for c in cd.columns if c.lower() in ("timestamp", "ts", "time", "datetime"))
        cd[tcol] = pd.to_datetime(cd[tcol])
        cd = cd.set_index(tcol).sort_index()
        for _, t in w.iterrows():
            seg = cd.loc[t["entry_time"] - pd.Timedelta(minutes=60): t["entry_time"] + pd.Timedelta(minutes=60)]
            print(f"   --- {t['entry_time']} {t['side']} net ${t['net_usd']:.1f} 出口 {t['exit_reason']} 保有 {t['hold_min']:.0f}分 ---")
            cols = [c for c in ("open", "high", "low", "close", "volume") if c in seg.columns]
            print("   " + seg[cols].round(1).to_string().replace("\n", "\n   "))
    else:
        cols = ["entry_time", "exit_reason", "hold_min", "net_usd", "adx_at_entry", "bb_mid_slope_at_entry", "atr_pct", "rsi_at_entry"]
        print("   " + w[cols].round(2).to_string(index=False).replace("\n", "\n   "))

    # ===== N7. 必要勝率と不足量（損益分岐・KB §1 期待値）=====
    wn = d[d["net_usd"] > 0]; ls = d[d["net_usd"] <= 0]
    print("\n  N7. 必要勝率と不足量（損益分岐）")
    if len(wn) and len(ls):
        aw, al = wn["net_usd"].mean(), -ls["net_usd"].mean()
        p_act = len(wn) / len(d)
        p_req = al / (aw + al)
        print(f"   平均勝ち ${aw:.2f} / 平均負け ${al:.2f} → 必要勝率 {p_req*100:.1f}% / 実際 {p_act*100:.1f}%"
              f" / 不足 {max(0,(p_req-p_act))*100:.1f}pt" + ("（分岐点超え）" if p_act >= p_req else ""))
        print(f"   （等価な別解: 平均負けを ${aw*p_act/(1-p_act):.2f} まで縮める or 平均勝ちを ${al*(1-p_act)/p_act:.2f} まで伸ばす）")
    else:
        print("   勝ち/負けの一方が0件＝計算不能")

    # ===== N8. 負け玉の解剖（entry特徴の中央値比較・月別集中・KB §4）=====
    print("\n  N8. 負け玉の解剖（entry時点で勝ち玉と何が違うか・どこに集中するか）")
    feat_cols = [c for c in ("atr_pct", "adx_at_entry", "rsi_at_entry", "bb_mid_slope_at_entry", "stoch_k_at_entry", "bb_width_at_entry") if c in d.columns]
    if len(wn) and len(ls):
        med = pd.DataFrame({"勝ち玉": wn[feat_cols].median(), "負け玉": ls[feat_cols].median()}).round(2)
        med["差"] = (med["負け玉"] - med["勝ち玉"]).round(2)
        print("   " + med.to_string().replace("\n", "\n   "))
        print("   負け玉の月別集中 top5: " + " / ".join(
            f"{m} {n}件" for m, n in ls["entry_time"].dt.to_period("M").value_counts().head(5).items()))
        for reason in ("SL_FILLED",):
            slb = d[d["exit_reason"] == reason]
            if len(slb) >= 5:
                print(f"   {reason} {len(slb)}件（全体の{len(slb)/len(d)*100:.1f}%）の中央値: " +
                      " / ".join(f"{c} {slb[c].median():.2f}" for c in feat_cols[:4]))
                print(f"   {reason} 月別 top3: " + " / ".join(
                    f"{m} {n}件" for m, n in slb["entry_time"].dt.to_period("M").value_counts().head(3).items()))

    # ===== N9. 出口効率（勝ち玉の MFE 捕捉率・KB §3）=====
    print("\n  N9. 出口効率（勝ち玉の実現益÷含み益ピーク・業界基準 0.6-0.75）")
    if "mfe_usd" in d.columns and len(wn) and not (wn["mfe_usd"] == 0).all():
        cap = (wn["net_usd"] / wn["mfe_usd"].replace(0, np.nan)).dropna()
        v = cap.median()
        verdict = "出口効率は正常域＝直すべきは入口側" if 0.6 <= v else ("早すぎる利確で取り逃し＝出口側に課題" if v < 0.6 else "")
        print(f"   MFE捕捉率 中央値 {v:.2f} / 25-75%ile [{cap.quantile(0.25):.2f}, {cap.quantile(0.75):.2f}] → {verdict}")
    else:
        print("   mfe_usd 列なし/全0＝計算不能（実験スクリプトが MFE を記録していない＝記録漏れを疑え）")

    print("\n  ⚠️ ここまでは最低ライン（数字の抽出）。ledger に 5つの問い（①どのレバーが動いたか ②あと何が")
    print("     いくら足りないか ③負けはどこに集中か ④過去のどの実験と同じ/違う構造か ⑤次の事前仮説1つ）を書くこと。")
    print(f"\n[保存] 深掘り分析を書類化 → {out_path}")


if __name__ == "__main__":
    main()
