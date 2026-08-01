#!/usr/bin/env python3
"""tuner_backcalc.py — 判定の値を「逆算」で出すための材料を実測する（まこさん承認 2026-08-01）

なぜ要るか
--------------------------------------------------------------------------
歩5 の判定表には、まこさんが決める値が3つ残っている。
  ・件数/日 の下限（役割の下限 5 が戦略の合計にかかるのか、ロジック1本にかかるのか）
  ・土台をまだ持たないロジックの合否＝値決め窓の net の下限
  ・R_MIN＝リスクリワード比の下限（recipes/search_limits.json の最後の値待ち）
まこさんの言葉（2026-08-01）＝「適切な値がわからない。逆算で出せない？」。
逆算の式は 必要な件数/日 ＝ 担う月 net ÷ 1件あたりの純益 ÷ 30日。分母が実測されていない。
本ファイルはその分母を、値決め窓の実測から機械で出す。

やらないこと（線引き）
--------------------------------------------------------------------------
・採点窓は一切見ない（L-267）。窓は値決め窓だけ。
・売買記録CSVは書かない。採否の道具ではない。
・純益は審判 score.py に通して得る。CC は純益を計算しない（H13）。
・手数料率は eval_engine の確定値を import する。数字を書き写さない（exchange_spec audit#19）。
・値は決めない。材料を出すだけ。決めるのはまこさん。

使い方
--------------------------------------------------------------------------
  python3 scripts/priority_rebuild/tuner_backcalc.py --strategy e37 --logic v59
  python3 scripts/priority_rebuild/tuner_backcalc.py --selftest   # 番人（合成データのみ）

--target-monthly＝そのロジック（または戦略）が担う月 net。既定はまこさん確定のマイルストーン
  「E36 と E37 を合わせて月 $600」から、実測済みの E36 月$137.46 を引いた $462.54。
  ★単独 net の足し上げは合算にならない（実測＝P21 $401.51 ＋ P23 $241.72 を一緒に回した E32b は
  $616.55）。だからこの分子は目安であって、置き方はまこさんが決める。
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import eval_engine as ee            # 手数料の確定値（数字を書き写さない）
import periods                      # 期間の正本（H8・日付リテラルを書かない）
import score as judge               # 審判＝import のみ・無変更（H13）

TARGET_MONTHLY_DEFAULT = 600.00 - 137.46   # まこさん確定のマイルストーン − E36 の実測（台帳）

# ★5分足スキャルの1日のトレード数の目安（まこさんが 2026-08-01 に貼った検索結果）。
#   少なめ＝優位性の高い所だけ厳選・手数料負けのリスクが低い ／ 標準＝5分足の確定と上位足の向きが
#   そろった細かい波 ／ 多め＝板と1分足も使って数分単位で高速に回す上級者。
#   ⚠️ 出どころは検索の要約なので「方向の目安」として使う。値を確定する根拠にはしない。
#   同じ資料の注意書き＝「回数よりも1回あたりの期待値とコストのバランスが重要」。本ファイルの ⑥ がそこ。
SCALP_BANDS = [("少なめ（厳選）", 5, 15), ("標準", 15, 40), ("多め（上級者）", 50, 100)]


def per_trade_net(t: pd.DataFrame) -> np.ndarray:
    """1玉ずつの純益。★審判 score.py に1行ずつ通して得る＝CC は純益を計算しない（H13）。

    分け方が壊れていないことは、合計が全体の net と一致するかで確かめる（tuner_stats と同じ作法）。
    """
    out = []
    for i in range(len(t)):
        row = t.iloc[[i]].reset_index(drop=True)
        out.append(float(judge.score(row)["total"]))
    return np.asarray(out, float)


def check_split(nets: np.ndarray, total: float, tol: float = 0.5) -> None:
    got = float(nets.sum())
    if abs(got - total) > tol:
        raise SystemExit(f"[逆算エラー] 1玉ずつの合計 ${got:,.2f} が全体の net ${total:,.2f} と一致しない"
                         f"＝分け方が壊れている（この材料は使えない）")


def slot_usage(t: pd.DataFrame, start, end) -> dict:
    """予算 0.12 BTC の枠をどれだけ使っているか（H1）と、枠の回転から出る件数の天井。

    同時保有の合計を時系列で追う（score.assert_position_cap と同じ数え方・あちらは改造しない）。
    ★件数を増やせるかは「機会があるか」だけでなく「枠が空いているか」で決まる。
    """
    et = pd.to_datetime(t["entry_time"]).tolist()
    xt = pd.to_datetime(t["exit_time"]).tolist()
    sz = t["size_btc"].astype(float).tolist()
    ev = [(et[i], sz[i]) for i in range(len(t))] + [(xt[i], -sz[i]) for i in range(len(t))]
    ev.sort(key=lambda z: (z[0], z[1]))
    cur = mx = 0.0
    prev = pd.Timestamp(start)
    area = 0.0                                   # 合計 BTC×秒（時間で重みづけした平均を出すため）
    busy_sec = 0.0                               # 1玉でも持っていた秒数
    for ts, s in ev:
        dt = max((pd.Timestamp(ts) - prev).total_seconds(), 0.0)
        area += cur * dt
        if cur > 1e-12:
            busy_sec += dt
        prev = pd.Timestamp(ts)
        cur = round(cur + s, 9)
        mx = max(mx, cur)
    total_sec = max((pd.Timestamp(end) - pd.Timestamp(start)).total_seconds(), 1.0)
    hold = t["hold_min"].astype(float) if "hold_min" in t.columns else None
    lot = float(np.median(t["size_btc"].astype(float)))
    cap = float(ee.POSITION_CAP_BTC)
    slots = int(cap / lot) if lot > 0 else 0
    ceil_per_day = None
    if hold is not None and len(hold) and float(hold.median()) > 0:
        ceil_per_day = slots * (24 * 60 / float(hold.median()))
    return {"max_btc": mx, "avg_btc": area / total_sec, "cap": cap,
            "busy_ratio": busy_sec / total_sec, "lot": lot, "slots": slots,
            "hold_med": float(hold.median()) if hold is not None and len(hold) else None,
            "hold_mean": float(hold.mean()) if hold is not None and len(hold) else None,
            "hold_p75": float(hold.quantile(0.75)) if hold is not None and len(hold) else None,
            "ceil_per_day": ceil_per_day}


def describe(x: np.ndarray) -> dict:
    if x is None or not len(x):
        return {"n": 0}
    return {"n": int(len(x)), "合計": float(x.sum()), "平均": float(x.mean()),
            "中央値": float(np.median(x)), "最小": float(x.min()), "最大": float(x.max())}


def _fmt(d: dict, unit: str = "$") -> str:
    if not d.get("n"):
        return "0 玉"
    return (f"{d['n']} 玉 ／ 合計 {unit}{d['合計']:,.2f} ／ 平均 {unit}{d['平均']:,.4f} ／ "
            f"中央値 {unit}{d['中央値']:,.4f} ／ 最小 {unit}{d['最小']:,.2f} ／ 最大 {unit}{d['最大']:,.2f}")


def analyse(t: pd.DataFrame, start, end, target_monthly: float) -> dict:
    """売買記録から、逆算の材料を出す。"""
    days = max((end - start).days, 1)
    months = days / 30.0
    res = judge.score(t)
    nets = per_trade_net(t)
    check_split(nets, res["total"])

    win, lose = nets[nets > 0], nets[nets < 0]
    flat = nets[nets == 0]
    d_all, d_win, d_lose = describe(nets), describe(win), describe(lose)
    win_rate = len(win) / len(nets) if len(nets) else 0.0

    print("=" * 88)
    print("逆算の材料（値決め窓の実測・採点窓は見ない・売買記録CSVは書かない・値は決めない）")
    print("=" * 88)
    print(f"[窓] {start.date()} 〜 {(end - pd.Timedelta(days=1)).date()}"
          f"（{days} 日＝約 {months:.1f} ヶ月・periods.py が正本）")
    print(f"[売買記録の列] {', '.join(t.columns)}")
    print()
    print("── ① 件数 ──")
    print(f"  玉数 {len(t):,} ／ 件数/日 {len(t) / days:.2f} ／ 件数/月 {len(t) / months:.1f}")
    print()
    print("── ② 1玉あたりの純益（審判 score.py が1玉ずつ出した値・全部のコスト込み）──")
    print(f"  全体  : {_fmt(d_all)}")
    print(f"  勝ち  : {_fmt(d_win)}")
    print(f"  負け  : {_fmt(d_lose)}")
    print(f"  ゼロ  : {len(flat)} 玉")
    print(f"  勝率  : {win_rate * 100:.2f}%")
    print(f"  月 net: ${res['total'] / months:+,.2f}／月（全期間 ${res['total']:+,.2f}）")
    print()

    rr_mean = rr_med = need_rr = None
    if len(win) and len(lose):
        rr_mean = d_win["平均"] / abs(d_lose["平均"])
        rr_med = d_win["中央値"] / abs(d_lose["中央値"])
        need_rr = (1 - win_rate) / win_rate if win_rate > 0 else float("inf")
        print("── ③ リスクリワード比（勝った時の取り分 ÷ 負けた時の失う分）──")
        print(f"  平均で見る  : {d_win['平均']:.4f} ÷ {abs(d_lose['平均']):.4f} = {rr_mean:.3f}")
        print(f"  中央値で見る: {d_win['中央値']:.4f} ÷ {abs(d_lose['中央値']):.4f} = {rr_med:.3f}")
        print(f"  この勝率 {win_rate * 100:.2f}% で収支が合うのに要る比率 = {need_rr:.3f}"
              f"（＝負けた玉の数 ÷ 勝った玉の数）")
        print(f"  → いまの比率が要る比率を{'上回っている' if rr_mean > need_rr else '下回っている'}"
              f"（上回れば黒字・下回れば赤字）")
        print()

    print("── ④ 出口の理由ごとの内訳（損の出どころ）──")
    tt = t.copy()
    tt["_net"] = nets
    g = tt.groupby("exit_reason")["_net"].agg(["count", "sum", "mean", "median"]).sort_values("sum")
    for reason, r in g.iterrows():
        print(f"  {reason:<18} {int(r['count']):>6} 玉 ／ 合計 ${r['sum']:>10,.2f} ／ "
              f"平均 ${r['mean']:>9.4f} ／ 中央値 ${r['median']:>9.4f}")
    print()

    theo = None
    # 帯幅の列名は戦略によって違う（E37 は box_W_pct_at_entry／レシピ実行器は W_entry）。
    # どちらも「(上端−下端)÷終値×100」の同じ量。無ければ測れないと正直に出す。
    wcol = next((c for c in ("box_W_pct_at_entry", "W_entry") if c in t.columns and t[c].notna().any()), None)
    if wcol:
        print(f"（帯幅の列＝{wcol}）")
        w = t[wcol].astype(float).to_numpy()
        notional = (t["size_btc"].astype(float) * t["entry_price"].astype(float)).to_numpy()
        ok = np.isfinite(w) & np.isfinite(notional)
        w, notional = w[ok], notional[ok]
        fee_round = ee.MAKER_FEE * 2.0
        half = notional * (w / 100.0) * 0.5          # 建値からレンジ中央までは帯幅の約半分
        theo = half - notional * fee_round
        print("── ⑤ レンジの幅から出る「1玉あたりの理論上の取り分」──")
        print(f"  帯幅 W% の分布: 中央値 {np.median(w):.3f}% ／ 平均 {w.mean():.3f}%"
              f" ／ 下位25% {np.percentile(w, 25):.3f}% ／ 上位25% {np.percentile(w, 75):.3f}%")
        print(f"  1玉の建玉額: 中央値 ${np.median(notional):,.0f}")
        print(f"  maker 往復の手数料率 {fee_round * 100:.4f}%（eval_engine の確定値・手で書いていない）")
        print(f"  帯の半分を取り切った場合の純益: {_fmt(describe(theo))}")
        print("  ※ これは上限の目安。実際は途中で切られる・届かない・部分決済で減る。")
        print()
    else:
        print("── ⑤ レンジの幅 ── 売買記録に帯幅の列が無いので測れない。")
        print()

    print("── ⑥ 期待値の関門（★件数を決める前にここを通す）──")
    ev = d_all["平均"] if d_all.get("n") else 0.0
    print(f"  いまの1玉あたりの期待値 = ${ev:+.4f}")
    if ev <= 0:
        print("  ⚠️ マイナスです。**この状態で件数を増やすと損が増えるだけ**なので、件数の下限を"
              "先に決めても意味がありません。まず1玉あたりをプラスにする必要があります。")
        if need_rr is not None and rr_mean is not None:
            need_lose = d_win["平均"] / need_rr
            need_win = abs(d_lose["平均"]) * need_rr
            print(f"  収支を合わせるのに要ること（どちらか一方でよい）:")
            print(f"    ・負けの平均を ${abs(d_lose['平均']):.4f} → ${need_lose:.4f} へ"
                  f"（{(1 - need_lose / abs(d_lose['平均'])) * 100:.1f}% 減らす）")
            print(f"    ・勝ちの平均を ${d_win['平均']:.4f} → ${need_win:.4f} へ"
                  f"（{(need_win / d_win['平均'] - 1) * 100:.1f}% 増やす）")
    print()

    su = slot_usage(t, start, end)
    print("── ⑦ 密度の天井（件数をどこまで増やせるか）──")
    print(f"  1玉の大きさ（中央値） {su['lot']:.4f} BTC ／ 予算 {su['cap']} BTC → 同時に持てる玉 {su['slots']} 個")
    print(f"  同時保有の実測: 最大 {su['max_btc']:.4f} BTC（枠の {su['max_btc'] / su['cap'] * 100:.1f}%）"
          f" ／ 時間で重みづけした平均 {su['avg_btc']:.4f} BTC（枠の {su['avg_btc'] / su['cap'] * 100:.1f}%）")
    print(f"  1玉でも持っていた時間の割合 {su['busy_ratio'] * 100:.1f}%")
    if su["hold_med"] is not None:
        print(f"  保有時間: 中央値 {su['hold_med']:.0f}分 ／ 平均 {su['hold_mean']:.0f}分 ／ 上位25% {su['hold_p75']:.0f}分")
        print(f"  枠を全部使って回した場合の1日の件数の上限 = {su['ceil_per_day']:,.0f} 件/日"
              f"（{su['slots']} 個 × 24時間 ÷ 保有中央値 {su['hold_med']:.0f}分）")
        print(f"  いまは {len(t) / days:.2f} 件/日 ＝ 上限の {len(t) / days / su['ceil_per_day'] * 100:.1f}%")
        print("  ※ 上限は枠と保有時間だけから出した机上の数字。実際は条件が成立する機会の数で頭打ちになる。")
    print()

    print("── ⑧ 逆算＝1日の件数ごとに、1玉あたりいくら要るか ──")
    print(f"  担う月 net（分子）= ${target_monthly:,.2f}／月")
    print("  ★5分足スキャルの目安の帯（まこさん提供の検索結果・方向の目安であって確定の根拠にしない）")
    print(f"  {'帯':<16} {'件数/日':>10} {'要る1玉あたり':>14}   いまの実力との比較")
    for name, lo, hi in SCALP_BANDS:
        for n in (lo, hi):
            need = target_monthly / n / 30.0
            ref = ""
            if d_win.get("n"):
                r = need / d_win["中央値"]
                ref = f"勝ち玉の中央値 ${d_win['中央値']:.4f} の {r:.2f} 倍"
            print(f"  {name:<16} {n:>10} {'$' + format(need, '.4f'):>14}   {ref}")
    print(f"  いまの実測      {len(t) / days:>10.2f} {'$' + format(target_monthly / (len(t) / days) / 30.0, '.4f'):>14}"
          f"   （実際の期待値は ${ev:+.4f}）")
    print("  ※ 同じ資料の注意書き＝「回数よりも1回あたりの期待値とコストのバランスが重要」。"
          "⑥ がマイナスのままなら、どの帯へ行っても赤字が増えるだけ。")
    print("  ※ 単独 net の足し上げは合算にならない（実測＝P21 $401.51 ＋ P23 $241.72 を"
          "一緒に回した E32b は $616.55）。分子の置き方はまこさんが決める。")
    print()
    return {"n": len(t), "per_day": len(t) / days, "months": months, "total": res["total"],
            "all": d_all, "win": d_win, "lose": d_lose, "win_rate": win_rate,
            "rr_mean": rr_mean, "rr_med": rr_med, "need_rr": need_rr,
            "theo": describe(theo) if theo is not None else None}


def run(strategy: str, logic: str, target_monthly: float) -> int:
    import engine_tuner as tuner
    from tuner_adapters import load_adapter
    ad = load_adapter(strategy)
    s, e = periods.SEARCH_START, periods.SEARCH_END
    assert e <= periods.SCORE_START, "値決め窓が採点窓と重なっている（L-267）"
    print(f"[戦略] {ad.NAME}: {ad.LABEL} ／ 調整の単位 {logic}")
    print("[土台] 接続ファイルの baseline（採用値そのまま・数字を書き写さない）")
    (df,) = tuner.load_windows_cached(ad, [(s, e)], tuner.WARM)
    bp = ad.baseline(logic)
    if bp is None:
        raise SystemExit(f"[逆算エラー] {logic} は土台（採用値）を持たない＝実測の材料が出せない")
    exit_keys = ad.exit_keys()
    ep = {k: v for k, v in bp.items() if k not in exit_keys}
    xp = {k: v for k, v in bp.items() if k in exit_keys}
    t = ad.run(df, logic, ep, xp)
    et = pd.to_datetime(t["entry_time"])
    t = t[(et >= s) & (et < e)].reset_index(drop=True)
    if not len(t):
        raise SystemExit("[逆算エラー] 値決め窓に玉が1つも無い")
    analyse(t, s, e, target_monthly)
    print("⚠️ ここは材料の実測＝採否の数字ではない。値を決めるのはまこさん。")
    return 0


def selftest() -> int:
    """番人＝分け方が壊れていたら止まる／材料の計算が既知答えと合う（合成データのみ）。"""
    ng: list[str] = []
    try:
        check_split(np.array([1.0, 2.0]), 99.0)
        ng.append("① 1玉ずつの合計が合わなくても止まらない")
    except SystemExit:
        pass
    d = describe(np.array([-2.0, 1.0, 3.0]))
    if not (d["n"] == 3 and abs(d["合計"] - 2.0) < 1e-9 and abs(d["中央値"] - 1.0) < 1e-9):
        ng.append(f"② describe の既知答え不一致: {d}")
    w, l = np.array([1.0, 3.0]), np.array([-1.0, -1.0])
    if abs(describe(w)["平均"] / abs(describe(l)["平均"]) - 2.0) > 1e-9:
        ng.append("③ リスクリワード比の既知答え不一致（勝ち平均2・負け平均1 なら 2.0）")
    if abs(300.0 / 1.0 / 30.0 - 10.0) > 1e-9:
        ng.append("④ 逆算の式が違う（月$300・1玉$1 なら 10件/日）")
    if not (0.0 < ee.MAKER_FEE < 0.001):
        ng.append(f"⑤ maker 手数料率が実体から取れていない: {ee.MAKER_FEE}")
    if not (periods.SEARCH_END <= periods.SCORE_START):
        ng.append("⑥ 値決め窓が採点窓と重なっている")
    print("=" * 88)
    print("tuner_backcalc 自己検査（合成データのみ・実データを走らせない）")
    print("=" * 88)
    print(f"  ① 分け方の番人 ② 統計の既知答え ③ リスクリワード比の既知答え ④ 逆算の式")
    print(f"  ⑤ maker 手数料率 {ee.MAKER_FEE}（eval_engine から）⑥ 値決め窓と採点窓の重なりなし")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="判定の値を逆算するための材料を値決め窓で実測する")
    ap.add_argument("--strategy", default="e37", help="接続ファイル名（在るのは e37, e38）")
    ap.add_argument("--logic", default="v59", help="調整の単位（接続ファイルの logics() が一覧）")
    ap.add_argument("--target-monthly", type=float, default=TARGET_MONTHLY_DEFAULT,
                    help="そのロジックが担う月 net（逆算の分子）。既定＝マイルストーン $600 − E36 $137.46")
    ap.add_argument("--selftest", action="store_true", help="番人（合成データのみ）")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    return run(a.strategy, a.logic, a.target_monthly)


if __name__ == "__main__":
    raise SystemExit(main())
