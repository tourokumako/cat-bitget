#!/usr/bin/env python3
"""tuner_stats.py — engine_tuner の「その数字が本物か」を測る（要件 R7 の B5・B6・まこさん OK 2026-07-27）

なぜ要るか
--------------------------------------------------------------------------
値を N 通り試して一番良いものを選ぶと、**実力ゼロでも一番良いものは必ず出る**。
コイン投げを100人にやらせれば誰か1人は10連勝するのと同じ。だから「運で説明がつく水準を
超えているか」を測る道具が要る。合格ラインは cat_requirements H11 が決めている。

  DSR（試した回数で割り引いた成績）  > 0.95 で合格
  PBO（その選び方が過剰にあてはめている確率） < 0.5 で合格

計算式そのものは dsr_pbo.py（既知答えテスト 6/6 pass）。本ファイルはその入口を作るだけ。

★ここが監査 2026-07-27 の指摘（NO-GO 条件4）
--------------------------------------------------------------------------
前の設計は「DSR と PBO を使う」と名前を書いただけで、適用の条件が1つも無かった。実測で確かめた条件:

 (a) 期間 T は日次にする。審判 score.py は月ごとに集計するので、値決め窓 122日 だと T=4。
     PSR は √(T−1) を掛けるので T=4 では統計にならない。日ごとなら T=122。
 (b) 試行数 N は「有効試行数」にする。似た動きをする試行はまとめて1つと数える。
     さらに 過去セッションの累積を足す（同じ窓を過去に何度も探索しているため）。
 (c) 分散 V は独立に撒いた試行から推定するのが正しい。TPE は良い所へ試行を集めるので分散が縮み、
     縮んだ分だけ DSR が甘く出る。ランダムサーチの段は未実装なので、いまは TPE の試行から
     推定して その旨を必ず表示する（黙って甘い数字を出さない）。
 (d) PBO には全試行を渡さない。重複を除いた候補（クラスタの代表）を渡す。

審判に触れない（H13）
--------------------------------------------------------------------------
日ごとの net は score.py を日ごとに呼んで得る。CC が net を計算し直すことはしない。
足し合わせが全期間の net と一致することを毎回確かめる（一致しなければ止める）。
"""
from __future__ import annotations

import json
import pathlib

import numpy as np
import pandas as pd

import dsr_pbo

HERE = pathlib.Path(__file__).resolve()
# 過去セッションの試行数の積み上げ（DSR の N に足す・同じ窓を何度も探索している事実を数字にする）
CUMULATIVE = HERE.parents[2] / ".claude" / "ratchet" / "engine_tuner_trials_cumulative.json"

DSR_PASS = 0.95     # cat_requirements H11
PBO_PASS = 0.50     # cat_requirements H11


def daily_net(trades: pd.DataFrame, judge, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """日ごとの net。審判 score.py を日ごとに呼ぶ＝CC は net を計算しない（H13）。

    建てた日でその玉を数える。玉が無い日は 0。返すのは窓の全日ぶん。
    """
    days = pd.date_range(start.normalize(), (end - pd.Timedelta(days=1)).normalize(), freq="D")
    out = pd.Series(0.0, index=days)
    if trades is None or not len(trades):
        return out
    t = trades.copy()
    t["_d"] = pd.to_datetime(t["entry_time"]).dt.normalize()
    for d, sub in t.groupby("_d"):
        if d in out.index:
            out.loc[d] = float(judge.score(sub.drop(columns=["_d"]).reset_index(drop=True))["total"])
    return out


def check_daily_sum(series: pd.Series, total: float, tol: float = 0.5) -> None:
    """日ごとの合計が全期間の net と一致することの確認（分け方が壊れていない証拠）。"""
    got = float(series.sum())
    if abs(got - total) > tol:
        raise SystemExit(f"[統計エラー] 日ごとの net の合計 ${got:,.2f} が "
                         f"全期間の net ${total:,.2f} と一致しない＝分け方が壊れている")


def effective_trials(matrix: np.ndarray, rho: float = 0.8) -> tuple[int, np.ndarray]:
    """有効試行数。似た動きの試行をまとめて1つと数える（相関が rho 以上なら同じ仲間）。

    Returns: (クラスタ数, 各列のクラスタ番号)
    背景＝生の試行回数をそのまま N にすると、似た値ばかり試した分まで罰になる。
    逆にまとめすぎると罰が甘くなる。業界標準の切り方は相関 0.8。
    """
    n = matrix.shape[1]
    if n <= 1:
        return n, np.zeros(n, dtype=int)
    with np.errstate(invalid="ignore", divide="ignore"):
        c = np.corrcoef(matrix, rowvar=False)
    c = np.nan_to_num(c, nan=0.0)
    try:
        from scipy.cluster.hierarchy import fcluster, linkage
        from scipy.spatial.distance import squareform
        d = 1.0 - np.abs(c)
        np.fill_diagonal(d, 0.0)
        d = (d + d.T) / 2.0                      # 対称化（数値誤差で squareform が落ちるため）
        lab = fcluster(linkage(squareform(d, checks=False), method="complete"),
                       t=1.0 - rho, criterion="distance")
        return int(len(set(lab))), lab
    except Exception:                            # noqa: BLE001  まとめられなければ生の本数（罰が重い側へ倒す）
        return n, np.arange(n)


def load_cumulative(key: str) -> int:
    try:
        return int(json.loads(CUMULATIVE.read_text(encoding="utf-8")).get(key, {}).get("trials", 0))
    except Exception:                            # noqa: BLE001
        return 0


def add_cumulative(key: str, trials: int, stamp: str) -> int:
    """この窓に対して過去に試した回数を積み上げる。DSR の N に足すため。"""
    try:
        cur = json.loads(CUMULATIVE.read_text(encoding="utf-8")) if CUMULATIVE.exists() else {}
    except Exception:                            # noqa: BLE001
        cur = {}
    rec = cur.get(key, {"trials": 0, "runs": 0})
    rec["trials"] = int(rec.get("trials", 0)) + int(trials)
    rec["runs"] = int(rec.get("runs", 0)) + 1
    rec["last"] = stamp
    cur[key] = rec
    try:
        CUMULATIVE.parent.mkdir(parents=True, exist_ok=True)
        CUMULATIVE.write_text(json.dumps(cur, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8")
    except Exception as e:                       # noqa: BLE001
        print(f"[統計] 累積の記録に失敗した（結果には影響しない）: {e}")
    return int(rec["trials"])


def evaluate(daily: dict[int, pd.Series], best_id: int, past_trials: int,
             pbo_max_cols: int = 200, n_blocks: int = 10) -> dict:
    """DSR と PBO を出す。

    Args:
        daily: 試行番号 → 日ごとの net の列（窓の全日ぶん・同じ長さ）
        best_id: 選ばれた試行の番号
        past_trials: 過去セッションの累積試行数（N に足す）
    """
    ids = sorted(daily)
    M = np.column_stack([daily[i].to_numpy(float) for i in ids])
    T = M.shape[0]
    n_eff, lab = effective_trials(M)
    sr = np.array([dsr_pbo.per_period_sharpe(M[:, j]) for j in range(M.shape[1])])
    best_col = ids.index(best_id)

    n_for_dsr = n_eff + int(past_trials)
    d = dsr_pbo.deflated_sharpe_ratio(M[:, best_col], sr, n_trials=n_for_dsr, T=T)

    # PBO には重複を除いた候補だけ渡す（クラスタごとに Sharpe が最良の1本）
    reps = []
    for c in sorted(set(lab)):
        idx = [j for j in range(len(ids)) if lab[j] == c]
        reps.append(max(idx, key=lambda j: sr[j]))
    reps = sorted(set(reps))[:pbo_max_cols]
    pbo = None
    if len(reps) >= 2 and T >= n_blocks:
        pbo = dsr_pbo.pbo_cscv(M[:, reps], n_blocks=n_blocks)
    return {"T": T, "n_raw": len(ids), "n_eff": n_eff, "past_trials": int(past_trials),
            "n_for_dsr": n_for_dsr, "dsr": d, "pbo": pbo, "n_pbo_cols": len(reps)}


def selftest() -> int:
    """番人＝わざと壊して落ちるか・道具が正しく効くか。"""
    ng = []
    rng = np.random.default_rng(0)
    # ① 有効試行数＝同じ列を10本並べたら1つにまとまる
    base = rng.normal(size=200)
    same = np.column_stack([base + rng.normal(scale=1e-6, size=200) for _ in range(10)])
    n1, _ = effective_trials(same)
    if n1 != 1:
        ng.append(f"同じ動きの10本が1つにまとまらない（{n1}）")
    # ② 全部バラバラなら本数どおり
    n2, _ = effective_trials(rng.normal(size=(200, 8)))
    if n2 != 8:
        ng.append(f"バラバラな8本がまとまってしまう（{n2}）")
    # ③ 日ごとの合計が合わないと止まる
    try:
        check_daily_sum(pd.Series([1.0, 2.0]), 99.0)
        ng.append("日ごとの合計が合わなくても止まらない")
    except SystemExit:
        pass
    # ④ 過去の累積を足すと DSR は下がる（多重検定の罰が効いている）
    daily = {i: pd.Series(rng.normal(loc=0.05, size=120)) for i in range(12)}
    a = evaluate(daily, 0, past_trials=0)["dsr"]["dsr"]
    b = evaluate(daily, 0, past_trials=10_000)["dsr"]["dsr"]
    if not (b <= a):
        ng.append(f"過去の累積を足しても DSR が下がらない（{a:.3f} → {b:.3f}）")
    print("=" * 70)
    print("tuner_stats 自己検査")
    print("=" * 70)
    print(f"  同じ動き10本 → {n1} 個 ／ バラバラ8本 → {n2} 個")
    print(f"  DSR: 過去0回 {a:.3f} → 過去10,000回 {b:.3f}（下がれば罰が効いている）")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
