#!/usr/bin/env python3
"""tuner_window_diag.py — 窓の位置と長さを決めるための材料を実測する（読み取り専用・歩5 の3回目）

なぜ要るか
--------------------------------------------------------------------------
いま値決め窓と確認窓が同じ日付になっている（periods.py・まこさん確定 2026-07-30 の暫定）。
同じ日付だと確認窓に弾く力がゼロで、判定表の B2 が必ず「判定不能」になる。
その状態ではどの設定にも「これ以上出ない」と言えない（tuner_judgement.py の _rows_b1b2）。
窓を決め直すには判断材料が要る。本ファイルはその材料を機械で出す。

やらないこと（線引き）
--------------------------------------------------------------------------
・窓を決めない。値も決めない。決めるのはまこさん。
・期間の正本 periods.py を1文字も変えない（H8）。候補の窓は下の CANDIDATES に置くだけ。
・採点窓（periods.SCORE_START 以降）に1本も掛けない。番人が掛かったら止める（L-267・H2）。
・売買記録CSVを書かない。採否の道具ではない。
・net は審判 score.py が出す。CC は計算しない（H13）。手数料は eval_engine から（H4）。
・★「土台の net が一番大きい窓」を推さない。それは過去に一番合う値を選ぶのと同じで L-267。
  net と件数は「その窓が土台にとってどんな相場か」を知るための参考として出すだけ。
  窓を選ぶ根拠に使えるのは、成績を一切使わない構造の近さ（window_similarity_ranking.md）。

使い方
--------------------------------------------------------------------------
  python3 scripts/priority_rebuild/tuner_window_diag.py --strategy e37 --logic v59
  python3 scripts/priority_rebuild/tuner_window_diag.py --selftest   # 番人（合成データのみ）
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import periods                              # 期間の正本（H8）
import score as judge                       # 審判＝import のみ・無変更（H13）
from tuner_backcalc import describe, per_trade_net, check_split
from tuner_judgement import slot_usage      # 枠の数え方は判定表と同じものを使う（二重に持たない）

HERE = pathlib.Path(__file__).resolve()
RANKING = HERE.parents[2] / ".claude" / "ratchet" / "window_similarity_ranking.md"


def _ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(s)


# ══ 候補の窓（★これは「候補」であって正本ではない・正本は periods.py のまま）═════════════
#   並べ方の考え方＝動かす軸を1つに絞る。
#     確認窓は採点窓の直前に置いて固定する（walk-forward の形＝値を選んだ後の期間で確かめる）。
#     値決め窓はその直前まで。長さだけを 12／18／24／全部 の4通りに変える。
#     確認窓の長さは 3ヶ月 と 6ヶ月 の2通り。4×2＝8通り。
#   「全部」の始まりは5分足データの先頭（2021-04）。ここは期間の区切りではなくデータの端。
CANDIDATES: list[tuple[str, str, str, str, str]] = [
    # 名前,        値決め開始,     値決め終了(排他), 確認開始,     確認終了(排他)
    ("確認3ヶ月×値決め12ヶ月", "2024-12-01", "2025-12-01", "2025-12-01", "2026-03-01"),
    ("確認3ヶ月×値決め18ヶ月", "2024-06-01", "2025-12-01", "2025-12-01", "2026-03-01"),
    ("確認3ヶ月×値決め24ヶ月", "2023-12-01", "2025-12-01", "2025-12-01", "2026-03-01"),
    ("確認3ヶ月×値決め全部",   "2021-04-01", "2025-12-01", "2025-12-01", "2026-03-01"),
    ("確認6ヶ月×値決め12ヶ月", "2024-09-01", "2025-09-01", "2025-09-01", "2026-03-01"),
    ("確認6ヶ月×値決め18ヶ月", "2024-03-01", "2025-09-01", "2025-09-01", "2026-03-01"),
    ("確認6ヶ月×値決め24ヶ月", "2023-09-01", "2025-09-01", "2025-09-01", "2026-03-01"),
    ("確認6ヶ月×値決め全部",   "2021-04-01", "2025-09-01", "2025-09-01", "2026-03-01"),
]


def current_window() -> tuple[str, str, str, str, str]:
    """比較のために、いまの窓も同じ表に載せる。数字は periods.py から引く（手で書かない・H8）。"""
    return ("いまの窓（値決め＝確認）",
            str(periods.SEARCH_START.date()), str(periods.SEARCH_END.date()),
            str(periods.CONFIRM_START.date()), str(periods.CONFIRM_END.date()))


def assert_no_score_overlap(rows) -> None:
    """★番人＝候補の窓が採点窓に1日でも掛かったら止める（L-267・H2）。"""
    for name, ss, se, cs, ce in rows:
        for lab, a, b in (("値決め窓", ss, se), ("確認窓", cs, ce)):
            if _ts(b) > periods.SCORE_START:
                raise SystemExit(
                    f"[窓エラー] 候補『{name}』の{lab} {a}〜{b} が採点窓 "
                    f"{periods.SCORE_START.date()} 以降に掛かっています。"
                    f"採点窓は探索にも選定にも使えません（L-267・H2）。")
            if _ts(a) >= _ts(b):
                raise SystemExit(f"[窓エラー] 候補『{name}』の{lab}の前後が逆です: {a} 〜 {b}")


# ══ 構造の近さ（成績を一切使わない物差し・窓を選ぶ根拠に使ってよい唯一の数字）═══════════
def load_ranking() -> list[tuple[pd.Timestamp, pd.Timestamp, float]]:
    """window_similarity_ranking.md の順位表を読む。

    行の形＝「   2   2024-04〜2024-07         1.78   DI差14裾q90-1.0 / ...」
    窓は4ヶ月幅（2024-04〜2024-07 は 4〜7月の4ヶ月）。距離は採点窓との構造距離で、小さいほど近い。
    ★この距離は戦略の成績を一切使っていない（同ファイル §抽出方法の逐語）。
    """
    if not RANKING.exists():
        return []
    out = []
    pat = re.compile(r"^\s*\d+\s+(\d{4})-(\d{2})〜(\d{4})-(\d{2})\s+([\d.]+)\s")
    for ln in RANKING.read_text(encoding="utf-8").splitlines():
        m = pat.match(ln)
        if not m:
            continue
        y1, m1, y2, m2, d = m.groups()
        s = pd.Timestamp(f"{y1}-{m1}-01")
        e = pd.Timestamp(f"{y2}-{m2}-01") + pd.offsets.MonthBegin(1)   # 末月の翌月頭＝排他
        out.append((s, e, float(d)))
    return out


def structure_distance(rank, start: pd.Timestamp, end: pd.Timestamp) -> tuple[float | None, int, int]:
    """その窓の中にすっぽり入る4ヶ月の小窓を集め、距離の中央値と件数と上位10入りの数を返す。"""
    inside = [d for (s, e, d) in rank if s >= start and e <= end]
    if not inside:
        return None, 0, 0
    top10 = sorted(d for (_s, _e, d) in rank)[:10]
    cut = top10[-1] if top10 else float("inf")
    return float(np.median(inside)), len(inside), sum(1 for d in inside if d <= cut)


# ══ 窓ごとの実測 ═══════════════════════════════════════════════════════════════════════
def slice_stats(t: pd.DataFrame, nets: np.ndarray, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    """建てた時刻がその窓に入る玉だけを切り出して集計する。"""
    et = pd.to_datetime(t["entry_time"])
    m = (et >= start) & (et < end)
    sub = t[m].reset_index(drop=True)
    sub_net = nets[m.to_numpy()]
    days = max((end - start).days, 1)
    months = days / 30.0
    if not len(sub):
        return {"n": 0, "days": days, "months": months, "per_day": 0.0,
                "total": 0.0, "per_month": 0.0, "win_rate": None, "rr": None, "slot": {}}
    win, lose = sub_net[sub_net > 0], sub_net[sub_net < 0]
    total = float(sub_net.sum())
    rr = None
    if len(win) and len(lose):
        rr = float(win.mean() / abs(lose.mean()))
    return {"n": len(sub), "days": days, "months": months, "per_day": len(sub) / days,
            "total": total, "per_month": total / months,
            "win_rate": len(win) / len(sub_net), "rr": rr,
            "slot": slot_usage(sub, start, end)}


def run(strategy: str, logic: str) -> int:
    import engine_tuner as tuner
    from tuner_adapters import load_adapter

    rows = [current_window()] + CANDIDATES
    assert_no_score_overlap(rows)

    ad = load_adapter(strategy)
    full_start = min(_ts(r[1]) for r in rows)
    full_end = periods.SCORE_START            # 採点窓の直前まで（排他・ここから先は触らない）
    print("=" * 100)
    print("窓を決めるための材料（読み取りのみ・窓も値も決めない・決めるのはまこさん）")
    print("=" * 100)
    print(f"[戦略] {ad.NAME}: {ad.LABEL} ／ 調整の単位 {logic}")
    print(f"[土台] 接続ファイルの baseline（採用値そのまま・数字を書き写さない）")
    print(f"[走らせる範囲] {full_start.date()} 〜 {(full_end - pd.Timedelta(days=1)).date()}"
          f"（1回だけ走らせて、窓ごとに切り出す＝8回走らせても結果は同じで時間だけかかるため）")
    print(f"[採点窓] {periods.SCORE_START.date()} 〜 {periods.SCORE_END.date()} ＝ 一切触らない")
    print()

    (df,) = tuner.load_windows_cached(ad, [(full_start, full_end)], tuner.WARM)
    bp = ad.baseline(logic)
    if bp is None:
        raise SystemExit(f"[窓エラー] {logic} は土台（採用値）を持たない＝材料が出せない")
    exit_keys = ad.exit_keys()
    ep = {k: v for k, v in bp.items() if k not in exit_keys}
    xp = {k: v for k, v in bp.items() if k in exit_keys}
    t = ad.run(df, logic, ep, xp)
    et = pd.to_datetime(t["entry_time"])
    t = t[(et >= full_start) & (et < full_end)].reset_index(drop=True)
    if not len(t):
        raise SystemExit("[窓エラー] 走らせた範囲に玉が1つも無い")

    print(f"[実測] 玉 {len(t):,} 本。1玉ずつの純益を審判 score.py に通します（少し時間がかかります）...")
    nets = per_trade_net(t)
    check_split(nets, judge.score(t)["total"])
    print(f"[実測] 全体 net ${nets.sum():+,.2f}（1玉ずつの合計が全体と一致することを確認済み）")
    print()

    rank = load_ranking()
    print(f"[構造の近さ] window_similarity_ranking.md から4ヶ月の小窓 {len(rank)} 個を読みました。"
          f"距離は採点窓との構造の遠さで、小さいほど近い。★戦略の成績は一切使っていない物差しです。")
    print()

    out = []
    for name, ss, se, cs, ce in rows:
        s1, e1, s2, e2 = _ts(ss), _ts(se), _ts(cs), _ts(ce)
        a = slice_stats(t, nets, s1, e1)
        b = slice_stats(t, nets, s2, e2)
        d1, n1, k1 = structure_distance(rank, s1, e1)
        d2, n2, k2 = structure_distance(rank, s2, e2)
        same = (s1 == s2 and e1 == e2)
        out.append(dict(name=name, s1=s1, e1=e1, s2=s2, e2=e2, a=a, b=b,
                        d1=d1, n1=n1, k1=k1, d2=d2, n2=n2, k2=k2, same=same))

    def fmt(x, w=9):
        return "—".rjust(w) if x is None else f"{x:,.2f}".rjust(w)

    print("── 表1: 値を選ぶ窓（この期間の値動きでツマミの数字を決める）──")
    print(f"  {'候補':<24} {'期間':<25} {'月':>4} {'玉':>7} {'件/日':>7} {'月net':>10} {'勝率%':>7} {'RR':>6} {'構造距離':>9}")
    for r in out:
        a = r["a"]
        print(f"  {r['name']:<24} {str(r['s1'].date())}〜{str((r['e1'] - pd.Timedelta(days=1)).date())} "
              f"{a['months']:>4.0f} {a['n']:>7,} {a['per_day']:>7.2f} {a['per_month']:>+10,.2f} "
              f"{(a['win_rate'] * 100 if a['win_rate'] is not None else float('nan')):>7.2f} "
              f"{fmt(a['rr'], 6)} {fmt(r['d1'], 9)}")
    print()

    print("── 表2: 確かめる窓（選んだ数字のまま1回走らせて、まぐれでないか見る）──")
    print(f"  {'候補':<24} {'期間':<25} {'月':>4} {'玉':>7} {'件/日':>7} {'月net':>10} {'勝率%':>7} {'RR':>6} {'構造距離':>9}")
    for r in out:
        b = r["b"]
        tail = "  ★値を選ぶ窓と同じ日付＝弾く力ゼロ" if r["same"] else ""
        print(f"  {r['name']:<24} {str(r['s2'].date())}〜{str((r['e2'] - pd.Timedelta(days=1)).date())} "
              f"{b['months']:>4.0f} {b['n']:>7,} {b['per_day']:>7.2f} {b['per_month']:>+10,.2f} "
              f"{(b['win_rate'] * 100 if b['win_rate'] is not None else float('nan')):>7.2f} "
              f"{fmt(b['rr'], 6)} {fmt(r['d2'], 9)}{tail}")
    print()

    print("── 表3: 枠の占有（予算 0.12 BTC のうちどれだけ使っていたか・値を選ぶ窓の側）──")
    print(f"  {'候補':<24} {'最大BTC':>9} {'時間平均':>9} {'埋まり%':>8} {'4ヶ月小窓':>10} {'上位10入り':>10}")
    for r in out:
        su = r["a"]["slot"]
        print(f"  {r['name']:<24} {su.get('max_btc', float('nan')):>9.4f} {su.get('avg_btc', float('nan')):>9.4f} "
              f"{su.get('busy_ratio', float('nan')) * 100:>8.1f} {r['n1']:>10} {r['k1']:>10}")
    print()

    print("── 読み方（★間違えないための線引き）──")
    print("  ・窓を選ぶ根拠に使ってよいのは『構造距離』だけです。成績を一切使わない物差しだからです。")
    print("  ・月net・勝率・RR は『その窓が土台にとってどんな相場か』を知るための参考です。")
    print("    ★『月net が一番大きい窓』を選んではいけません。過去に一番合う値を選ぶのと同じで、")
    print("      本番で効かなくなります（L-267・2022-07〜12 で実証済みの失敗）。")
    print("  ・値を選ぶ窓が長いほどデータが増えて多重検定に強くなりますが、相場の性格が混ざります。")
    print("  ・値を選ぶ窓が短いほど採点窓に構造が近づきますが、過剰にあてはまりやすくなります。")
    print("  ・確かめる窓は長いほど弾く力が強くなりますが、そのぶん値を選ぶ窓が短くなります。")
    print()
    print("⚠️ ここは材料の実測です。窓も値も決めていません。periods.py は1文字も変えていません。")
    print("   窓を決めるのはまこさんです。決まったら periods.py の SEARCH と CONFIRM だけを直します。")
    return 0


# ══ 番人（合成データのみ・実データを走らせない）════════════════════════════════════════
def selftest() -> int:
    ng: list[str] = []

    # ① 候補の窓が採点窓に掛かったら止まる
    bad = [("わざと採点窓に掛けた", "2025-12-01", "2026-04-01", "2026-04-01", "2026-05-01")]
    try:
        assert_no_score_overlap(bad)
        ng.append("① 採点窓に掛かる候補で止まらない（L-267 の番人が死んでいる）")
    except SystemExit:
        pass
    # ② 本物の候補は全部通る
    try:
        assert_no_score_overlap([current_window()] + CANDIDATES)
    except SystemExit as e:
        ng.append(f"② 本物の候補で止まってしまう: {e}")
    # ③ 前後が逆の窓で止まる
    try:
        assert_no_score_overlap([("逆", "2025-12-01", "2025-06-01", "2025-12-01", "2026-01-01")])
        ng.append("③ 前後が逆の窓で止まらない")
    except SystemExit:
        pass

    # ④ 切り出しの既知答え＝窓ごとの玉数の合計が全体と一致する（重複も抜けも無い）
    t = pd.DataFrame({
        "entry_time": pd.to_datetime(["2024-01-15", "2024-06-15", "2025-01-15", "2025-06-15"]),
        "exit_time": pd.to_datetime(["2024-01-15", "2024-06-15", "2025-01-15", "2025-06-15"]),
        "size_btc": [0.006] * 4, "hold_min": [30.0] * 4,
    })
    nets = np.array([1.0, -2.0, 3.0, -4.0])
    parts = [slice_stats(t, nets, pd.Timestamp("2024-01-01"), pd.Timestamp("2025-01-01")),
             slice_stats(t, nets, pd.Timestamp("2025-01-01"), pd.Timestamp("2026-01-01"))]
    if sum(p["n"] for p in parts) != len(t):
        ng.append(f"④ 窓ごとの玉数の合計が全体と合わない（{[p['n'] for p in parts]} vs {len(t)}）")
    if abs(sum(p["total"] for p in parts) - float(nets.sum())) > 1e-9:
        ng.append("④ 窓ごとの net の合計が全体と合わない")
    if parts[0]["n"] != 2 or abs(parts[0]["total"] - (-1.0)) > 1e-9:
        ng.append(f"④ 2024年の切り出しの既知答え不一致（2玉・net −1.0 のはずが "
                  f"{parts[0]['n']}玉・{parts[0]['total']}）")

    # ⑤ 構造距離の読み取りの既知答え（正本の順位表の逐語＝2位 2024-04〜2024-07 が 1.78）
    rank = load_ranking()
    hit = [d for (s, e, d) in rank
           if s == pd.Timestamp("2024-04-01") and e == pd.Timestamp("2024-08-01")]
    if not rank:
        ng.append("⑤ 順位表を読めていない（window_similarity_ranking.md）")
    elif not hit or abs(hit[0] - 1.78) > 1e-9:
        ng.append(f"⑤ 順位表の既知答え不一致（2024-04〜2024-07 は 1.78 のはずが {hit}）")
    # ⑥ 窓に入る小窓だけを拾う（採点窓に掛かる小窓を拾わない）
    d, n, _k = structure_distance(rank, pd.Timestamp("2024-04-01"), pd.Timestamp("2024-08-01"))
    if n != 1 or d is None or abs(d - 1.78) > 1e-9:
        ng.append(f"⑥ 4ヶ月ちょうどの窓に入る小窓が1個でない（{n}個・中央値 {d}）")
    d2, n2, _k2 = structure_distance(rank, pd.Timestamp("2024-04-01"), pd.Timestamp("2024-07-01"))
    if n2 != 0 or d2 is not None:
        ng.append(f"⑥ 窓からはみ出す小窓を拾っている（{n2}個）")

    # ⑦ 期間の正本を変えていない（このファイルは periods を読むだけ）
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    for k in ("TRAIN_END", "SCORE_END", "SEAL_START", "EMBARGO_START"):
        if re.search(rf"^{k}\s*=", src, re.M):
            ng.append(f"⑦ 期間の値を自前で定義している: {k}（H8 違反）")

    print("=" * 88)
    print("tuner_window_diag 自己検査（合成データのみ・実データを走らせない・採点しない）")
    print("=" * 88)
    print("  ① 採点窓に掛かる候補で止まる ② 本物の候補は通る ③ 前後が逆で止まる")
    print("  ④ 窓ごとの玉数と net の合計が全体と一致する ⑤ 順位表の既知答え")
    print("  ⑥ 窓に入る小窓だけを拾う ⑦ 期間の値を自前で定義していない")
    print(f"  [候補] {len(CANDIDATES)} 通り＋いまの窓。採点窓 {periods.SCORE_START.date()} 以降は不使用。")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="窓の位置と長さを決めるための材料を実測する（読み取り専用）")
    ap.add_argument("--strategy", default="e37", help="接続ファイル名（在るのは e37, e38）")
    ap.add_argument("--logic", default="v59", help="調整の単位（接続ファイルの logics() が一覧）")
    ap.add_argument("--selftest", action="store_true", help="番人（合成データのみ）")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    return run(a.strategy, a.logic)


if __name__ == "__main__":
    raise SystemExit(main())
