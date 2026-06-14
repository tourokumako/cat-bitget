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

    # ===== N0. 件数・頻度の妥当性（質より先に量を見る・設計意図照合・#0/#1/#18・2026-06-14 まこさん）=====
    days = max(1, (d["entry_time"].max() - d["entry_time"].min()).days)
    per_day = len(d) / days
    print("\n  N0. 件数・頻度の妥当性（★質の前に量・設計意図と照合）")
    print(f"   総件数 {len(d)} / 期間 {days}日 / 件数/日 {per_day:.2f}")
    if per_day < 3:
        print(f"   ⚠️ 件数/日 {per_day:.2f} が低い＝戦略が高頻度狙い(レンジ等)なら過しぼりを疑え（入口・発火ファネルを点検・#1/#2）")
    if len(d) < 100:
        print(f"   ⚠️ 全体 n={len(d)} <100＝サンプル少・帯別/月別の断定は慎重に（#18）")
    small = []                                   # 帯別 n<30 ガード（少数で効く/効かないを断定しない・#18）
    for label, (col, edges) in BANDS.items():
        if col in d.columns:
            for b, c in pd.cut(d[col], edges, right=False).value_counts().items():
                if 0 < c < 30:
                    small.append(f"{label}{b}={int(c)}件")
    if small:
        print(f"   ⚠️ サンプル不足(n<30)の帯＝ここで効く/効かないを断定不可（#18）: " + " / ".join(small))
    print("   → 設計意図（レンジ=高頻度/スキャル=小利多数/トレンド=少数大利）と上の頻度が一致するか必ず照合（#0）")

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

    # ===== N10. 分離指標ランキング（★どの指標が勝敗を分けるか・構造を機械抽出・2026-06-14 まこさん「構造の解釈も強制」）=====
    # 「数字の抽出」で止めず「勝敗を分ける指標」を相関で機械順位づけ→改善は固定値調整でなく ML 特徴量化に向かう。
    print("\n  N10. 分離指標ランキング（★勝敗を分ける指標を機械抽出＝固定値調整でなく ML 特徴量の候補）")
    cand = [c for c in ("dev_z_at_entry", "taker_ls_at_entry", "adx_at_entry", "bb_mid_slope_pct_at_entry",
            "rsi_at_entry", "rsi_slope_at_entry", "stoch_k_at_entry", "bb_width_at_entry", "atr_pct",
            "ret_5", "add_count", "entry_hour") if c in d.columns and d[c].notna().sum() > 30]
    tr_d = _load(a.train) if a.train else None       # 両窓再現チェック用（地合いボーナスか本物か）
    rows = []
    for c in cand:
        sub = d[[c, "net_usd"]].dropna()
        if len(sub) < 30 or sub[c].nunique() < 5:
            continue
        rho = sub[c].corr(sub["net_usd"], method="spearman")
        wmed = wn[c].median() if len(wn) else np.nan
        lmed = ls[c].median() if len(ls) else np.nan
        try:                                          # 5分位の net 単調性（向きが一貫しているか）
            q = pd.qcut(sub[c], 5, duplicates="drop")
            qnet = sub.groupby(q, observed=True)["net_usd"].mean()
            if qnet.shape[0] < 3:                     # bin が潰れた（低カーディナリティ）＝単調判定不能
                mono = "?"
            else:
                mono = "単調" if (qnet.is_monotonic_increasing or qnet.is_monotonic_decreasing) else "非単調"
        except Exception:
            mono = "?"
        repro = ""                                    # 学習窓で符号が一致するか（過剰適合/地合い検出）
        if tr_d is not None and c in tr_d.columns:
            ts = tr_d[[c, "net_usd"]].dropna()
            if len(ts) > 30 and ts[c].nunique() >= 5:
                trho = ts[c].corr(ts["net_usd"], method="spearman")
                repro = "両窓再現✓" if (pd.notna(trho) and pd.notna(rho) and np.sign(trho) == np.sign(rho) and abs(trho) > 0.05) else "両窓不一致✗"
        rows.append((c, rho, wmed, lmed, mono, repro))
    rows.sort(key=lambda r: -abs(r[1]) if pd.notna(r[1]) else 0)
    for c, rho, wmed, lmed, mono, repro in rows:
        dir_ = "勝ち玉ほど高い" if (pd.notna(rho) and rho > 0) else "勝ち玉ほど低い"   # 向きは順位統計 rho の符号で（中央値split と食い違わせない）
        print(f"   {c:26s} 相関{rho:+.3f} / 勝中央{wmed:.3f} vs 負{lmed:.3f}（{dir_}）/ 5分位net {mono} {repro}")
    if rows and pd.notna(rows[0][1]) and abs(rows[0][1]) >= 0.1:        # ★|相関|<0.1 はノイズ＝断定しない（誤誘導防止・レビュー blocking 2026-06-14）
        top = rows[0]
        tdir = "高い" if top[1] > 0 else "低い"
        print(f"   ★最強分離指標 = {top[0]}（相関{top[1]:+.3f}・勝ち玉ほど{tdir}・5分位{top[4]}・{top[5]}）")
        print(f"   → この指標を機械学習の特徴量として木に渡す（⛔ 固定値の手調整＝閾値を X→Y にするのは禁止・hook L-267）")
    elif rows:
        print(f"   ★分離指標なし（最大|相関| {abs(rows[0][1]):.3f}<0.1＝どの指標も勝敗を明確に分けていない＝入口の指標選びから見直す）")

    # ===== N11. 損切り玉の方向判定（★方向ミスか損切りが狭すぎか・構造を機械抽出）=====
    print("\n  N11. 損切り玉の方向判定（★方向ミスか損切りが狭すぎか）")
    slb = d[d["exit_reason"] == "SL_FILLED"] if "exit_reason" in d.columns else d.iloc[0:0]
    if len(slb) >= 5 and "mfe_usd" in d.columns and "mae_usd" in d.columns:
        ratio = (slb["mfe_usd"] / slb["mae_usd"].abs().replace(0, np.nan)).dropna()
        rmed = ratio.median() if len(ratio) else np.nan
        almost = (slb["mfe_usd"] >= slb["mae_usd"].abs()).mean() * 100      # 含み益>含み損＝惜しい(tight疑い)
        if pd.notna(rmed):
            verdict = ("方向ミスが主因（入口の向きが逆＝損切り幅でなく入口を直す）" if rmed < 0.7
                       else "含み益を経て戻る玉が多い＝損切りが狭すぎる疑い")
            print(f"   SL {len(slb)}件: 含み益ピーク/含み損 中央値 {rmed:.2f} / 含み益≧含み損 の玉 {almost:.0f}% → ★{verdict}")
        else:
            print(f"   SL {len(slb)}件: mfe/mae 比が計算不能（mae 全0?）＝方向判定不能")
    else:
        print("   SL<5件 or mfe/mae 列なし＝判定不能")

    # ===== N12. 勝ち場面クロス（★上位2分離指標の組み合わせ・構造を機械抽出）=====
    print("\n  N12. 勝ち場面クロス（★どの組み合わせが黒字か＝木に学ばせる勝ち場面）")
    if len(rows) >= 2:
        c1, c2 = rows[0][0], rows[1][0]
        sub = d[[c1, c2, "net_usd"]].dropna()
        b1 = (sub[c1] > sub[c1].median()).map({True: f"{c1}≥中", False: f"{c1}<中"})
        b2 = (sub[c2] > sub[c2].median()).map({True: f"{c2}≥中", False: f"{c2}<中"})
        net = sub.pivot_table("net_usd", b1, b2, aggfunc="sum", observed=False).round(0)
        wr = (sub.assign(w=(sub["net_usd"] > 0)).pivot_table("w", b1, b2, aggfunc="mean", observed=False) * 100).round(0)
        print(f"   [{c1} × {c2}] 純益$"); print("   " + net.to_string().replace("\n", "\n   "))
        print(f"   [{c1} × {c2}] 勝率%"); print("   " + wr.to_string().replace("\n", "\n   "))
        st = net.stack()
        if len(st):
            print(f"   ★最も黒字の組み合わせ = {st.idxmax()}（net ${st.max():.0f}）／ 最も赤字 = {st.idxmin()}（net ${st.min():.0f}）")
    else:
        print("   分離指標が2つ未満＝クロス不能")

    print("\n  ⚠️ N1〜N12 は数字の抽出。ledger の5つの問いを N10〜N12 の構造解釈を引用して書く（数字でなく構造で結論）:")
    print("     【問1 レバー】=N10 最強分離指標 / 【問3 負け集中】=N11 SL方向判定・N8 / 【問5 次仮説】=N10上位指標を ML 特徴量化")
    print("     ⛔【問5】に固定値の手調整（閾値を X→Y にする）を書いたら違反＝分離指標を木に渡す形で書く（②思考の強制・まこさん 2026-06-14）")
    print("     （①どのレバーが動いたか ②あといくら足りないか ③負けはどこに集中か ④過去のどの実験と同じ/違う構造か ⑤次の事前仮説1つ）")
    print(f"\n[保存] 深掘り分析を書類化 → {out_path}")


if __name__ == "__main__":
    main()
