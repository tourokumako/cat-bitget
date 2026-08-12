#!/usr/bin/env python3
"""condition_parts_diag.py — 条件の部品の突き合わせ（段C の C-2・2026-08-11 新設・まこさん OK）

これは何か。
  いまの engine_tuner は「条件の形」を11個の名前で持っている（engine_tuner_exec.FORMS）。
  その11個が、materials.md ★6 の「部品」の組み合わせで **1バーも違わず同じ結果になるか** を
  実データで確かめる読み取り専用の道具。

なぜ要るか（まこさん指摘 2026-08-11・逐語）。
  「これは手書きで思い付いたら増やす。みたいな運用になるのか？すごい原始的なんだが。」
  ＝11個の名前を手で増やす形をやめ、部品の組み合わせにする。その前に
  **「部品にしても、いま作れている条件が1つも作れなくならない」ことを実測で示す**のがこの道具。

どうやって確かめるか。
  ①部品だけを使って、11個の形と同じものを組み立てる（下の COMPOSE）
  ②同じ実データに、実行器の本物（engine_tuner_exec._eval_cond）と、①を両方 当てる
  ③1バーずつ突き合わせて、食い違いが 0 であることを見る
  ★③が 0 でない形が1つでもあれば ❌。その形は「部品が足りない」ということ。

★この道具は読み取り専用。売買記録CSVを書かない・審判(score)を呼ばない・戦略を実行しない。

使い方。
  python3 condition_parts_diag.py            … 11個の形を突き合わせる（書き方の違いを含めて15通り）
  python3 condition_parts_diag.py --selftest … 番人（わざと壊すと食い違いが出るか）
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

_DATA = _HERE.parent.parent / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"
_BARS = 20000                                  # 突き合わせに使う本数（多すぎると遅いだけ・全列は作らない）


# ══ 部品（materials.md ★6 の「いま在る部品」だけを使う）══════════════════════════════
#    ★ここに書いてよいのは ★6 の表に在る部品だけ。新しい仕組みを足さない。
def p_value(df: pd.DataFrame, col: str) -> np.ndarray:
    """①値を持ってくる。"""
    return df[col].to_numpy(float)


def p_lag(a: np.ndarray, n: int) -> np.ndarray:
    """②n本 ずらす（先頭 n 本は値なし）。"""
    out = np.roll(a, n).astype(float)
    out[:n] = np.nan
    return out


def p_ma(a: np.ndarray, m: int) -> np.ndarray:
    """③n本の平均。"""
    return pd.Series(a).rolling(m).mean().to_numpy()


def p_sub(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """④引き算。"""
    return a - b


def p_mul(a: np.ndarray, k: float) -> np.ndarray:
    """⑤掛け算（★2026-08-11 の C-2 で見つけて足した＝touch が tol × |b| で使っている）。"""
    return a * k


def p_abs(a: np.ndarray) -> np.ndarray:
    """⑥絶対値。"""
    return np.abs(a)


def p_cmp(a: np.ndarray, th, side: str) -> np.ndarray:
    """⑦比べる（以上・以下）。値が無いところは不成立にする（実行器の既定 na=fail と同じ）。"""
    ok = (a >= th) if side == "above" else (a <= th)
    return np.where(np.isfinite(a), ok, False).astype(bool)


def p_and(*xs: np.ndarray) -> np.ndarray:
    """⑧かつ。"""
    out = xs[0]
    for x in xs[1:]:
        out = out & x
    return out


def p_not(x: np.ndarray) -> np.ndarray:
    """⑨でない。"""
    return ~x


def p_exists(a: np.ndarray) -> np.ndarray:
    """⑩値が在るか（欠損でないか）★2026-08-11 の C-2 で見つけて足した。
    実行器は条件ごとに np.where(np.isfinite(a), ok, na_pass) を掛けている＝これも部品。"""
    return np.isfinite(a)


def p_all_n(cond: np.ndarray, n: int) -> np.ndarray:
    """⑪n本のうち 全部 成立。"""
    return (pd.Series(cond.astype(float)).rolling(n).sum() >= n).to_numpy()


def p_any_n(cond: np.ndarray, n: int) -> np.ndarray:
    """⑫n本のうち どれか 成立。"""
    return (pd.Series(cond.astype(float)).rolling(n).max() >= 1).to_numpy()


def p_shift_cond(cond: np.ndarray, off: int) -> np.ndarray:
    """⑬条件そのものを n本 ずらす（実行器の offset）。"""
    if not off:
        return cond
    out = np.roll(cond, off)
    out[:off] = False
    return out


def p_ts_max(a: np.ndarray, n: int) -> np.ndarray:
    """⑮直前の n本の最大値（★2026-08-13 の段C の C-6 で足した部品）。

    ★いまのバーを含めない（先に1本 ずらしてから n本の最大を取る）。
      理由＝「過去n本の高値を更新した（新高値）」を書くため。いまのバーを含めると自分自身を
      超えられず、クロスで「更新した瞬間」を書けない。過去だけを見る＝未来参照なし。
    """
    return pd.Series(a).shift(1).rolling(int(n)).max().to_numpy(float)


def p_ts_min(a: np.ndarray, n: int) -> np.ndarray:
    """⑯直前の n本の最小値（★2026-08-13 の段C の C-6 で足した部品）。ts_max と同じ理由で
    いまのバーを含めない（「過去n本の安値を更新した（新安値）」を書くため）。"""
    return pd.Series(a).shift(1).rolling(int(n)).min().to_numpy(float)


def p_cross_val(n: int, th: float) -> np.ndarray:
    """⑭閾値とのクロス（★2026-08-13 の段C の C-6 で足した部品）。

    中身＝相手の列の代わりに「閾値の定数」を置く。これで「RSI が 70 を上抜けた」が書ける。
    実行器の実物＝engine_tuner_exec._eval_cond の cross で b が無いときに np.full(len(a), 閾値)。
    """
    return np.full(int(n), float(th))


# ══ 11個の形を、部品だけで組み立て直す ══════════════════════════════════════════════
#    ★引数は実行器と同じもの（df・列名・値）。実行器のコードを1行も呼ばない。
def _c_level(df, cols, v):
    a = p_value(df, cols[0])
    return p_cmp(a, v["th"], v["side"])


def _c_band(df, cols, v):
    a = p_value(df, cols[0])
    return p_and(p_cmp(a, v["lo"], "above"), p_cmp(a, v["hi"], "below"))


def _c_band_exclude(df, cols, v):
    a = p_value(df, cols[0])
    inside = p_and(p_cmp(a, v["lo"], "above"), p_cmp(a, v["hi"], "below"))
    return p_and(p_not(inside), p_exists(a))


def _c_slope(df, cols, v):
    a = p_value(df, cols[0])
    d = p_sub(a, p_lag(a, v["n"]))
    return p_cmp(d, v["th"], v["side"])


def _c_slope_avg(df, cols, v):
    a = p_value(df, cols[0])
    ma = p_ma(a, v["m"])
    d = p_sub(ma, p_lag(ma, v["n"]))
    d = d.copy()
    d[:v["n"] + v["m"]] = np.nan                # 実行器と同じ助走の切り方
    return p_cmp(d, v["th"], v["side"])


def _c_cross(df, cols, v):
    # ★2本の書き方＝①列2本 ②列1本 ＋ 閾値（部品 cross_val・2026-08-13）。式は下で共通。
    a = p_value(df, cols[0])
    b = p_cross_val(len(a), v["th"]) if "th" in v else p_value(df, cols[1])
    pa, pb = p_lag(a, 1), p_lag(b, 1)
    fin = p_and(p_exists(a), p_exists(b))
    if v["direction"] == "down":
        return p_and(fin, p_cmp(p_sub(pa, pb), 0.0, "above"), p_cmp(p_sub(b, a), 0.0, "above"),
                     p_not(p_cmp(p_sub(b, a), 0.0, "below")))
    return p_and(fin, p_cmp(p_sub(pb, pa), 0.0, "above"), p_cmp(p_sub(a, b), 0.0, "above"),
                 p_not(p_cmp(p_sub(a, b), 0.0, "below")))


def _c_diff(df, cols, v):
    a, b = p_value(df, cols[0]), p_value(df, cols[1])
    return p_cmp(p_sub(a, b), v["th"], v["side"])


def _c_touch(df, cols, v):
    a, b = p_value(df, cols[0]), p_value(df, cols[1])
    d = p_abs(p_sub(a, b))
    return p_cmp(p_sub(d, p_mul(p_abs(b), v["tol"])), 0.0, "below")


def _c_candle_dir(df, cols, v):
    o, c = p_value(df, "open"), p_value(df, "close")
    d = p_sub(c, o) if v["dir"] == "bull" else p_sub(o, c)
    # 「より大きい（>）」は 部品の「以上」と「以下でない」の かつ で書ける（新しい部品を足さない）
    return p_and(p_cmp(d, 0.0, "above"), p_not(p_cmp(d, 0.0, "below")))


def _c_streak(df, cols, v):
    inner = _c_level(df, cols, v["inner"])
    return p_shift_cond(p_all_n(inner, v["n"]), v.get("offset", 0))


def _c_within_n(df, cols, v):
    inner = _c_level(df, cols, v["inner"])
    return p_shift_cond(p_any_n(inner, v["n"]), v.get("offset", 0))


_PRE_PARTS = {"ts_max": p_ts_max, "ts_min": p_ts_min}


def _c_cross_pre(df, cols, v):
    """★材料の前処理を掛けた列とのクロス（部品 ts_max・ts_min・2026-08-13）＝新高値・新安値。
    式は _c_cross と同じ。相手の列が「同じ列に部品を1つ掛けたもの」になるだけ。"""
    a = p_value(df, cols[0])
    b = _PRE_PARTS[v["op"]](a, v["n"])
    pa, pb = p_lag(a, 1), p_lag(b, 1)
    fin = p_and(p_exists(a), p_exists(b))
    if v["direction"] == "down":
        return p_and(fin, p_cmp(p_sub(pa, pb), 0.0, "above"), p_cmp(p_sub(b, a), 0.0, "above"),
                     p_not(p_cmp(p_sub(b, a), 0.0, "below")))
    return p_and(fin, p_cmp(p_sub(pb, pa), 0.0, "above"), p_cmp(p_sub(a, b), 0.0, "above"),
                 p_not(p_cmp(p_sub(a, b), 0.0, "below")))


COMPOSE = {"cross_pre": _c_cross_pre,
           "level": _c_level, "band": _c_band, "band_exclude": _c_band_exclude,
           "slope": _c_slope, "slope_avg": _c_slope_avg, "cross": _c_cross,
           "diff": _c_diff, "touch": _c_touch, "candle_dir": _c_candle_dir,
           "streak": _c_streak, "within_n": _c_within_n}


# ══ 実行器に渡すレシピ（同じ意味の条件を、実行器の書き方で書く）═══════════════════════
def _cases(m1: dict, m2: dict) -> list[dict]:
    """11個の形を1件ずつ。★値は分位を使わない（解決表なしで比べられるようにするため）。"""
    return [
        dict(form="level", real={"form": "level", "side": "above", "value": {"n": 55.0},
                                 "material": [m1]},
             cols=1, v={"th": 55.0, "side": "above"}),
        dict(form="band", real={"form": "band", "value": {"lo": {"n": 40.0}, "hi": {"n": 60.0}},
                                "material": [m1]},
             cols=1, v={"lo": 40.0, "hi": 60.0}),
        dict(form="band_exclude", real={"form": "band_exclude",
                                        "value": {"lo": {"n": 40.0}, "hi": {"n": 60.0}},
                                        "material": [m1]},
             cols=1, v={"lo": 40.0, "hi": 60.0}),
        dict(form="slope", real={"form": "slope", "side": "above",
                                 "value": {"n": 3, "th": {"n": 0.0}}, "material": [m1]},
             cols=1, v={"n": 3, "th": 0.0, "side": "above"}),
        dict(form="slope_avg", real={"form": "slope_avg", "side": "below",
                                     "value": {"n": 3, "m": 5, "th": {"n": 0.0}}, "material": [m1]},
             cols=1, v={"n": 3, "m": 5, "th": 0.0, "side": "below"}),
        dict(form="cross", real={"form": "cross", "value": {"direction": "up"},
                                 "material": [m1, m2]},
             cols=2, v={"direction": "up"}),
        dict(form="cross", real={"form": "cross", "value": {"direction": "down"},
                                 "material": [m1, m2]},
             cols=2, v={"direction": "down"}),
        # ★閾値とのクロス（部品 cross_val・2026-08-13 の段C の C-6 で足した）＝列1本 ＋ 閾値。
        #   『RSI が 55 を上抜けた／下抜けた』。2026-08-13 より前は、この2件は書けなかった。
        dict(form="cross", label="up（閾値55・列1本）",
             real={"form": "cross", "value": {"direction": "up", "th": {"n": 55.0}},
                   "material": [m1]},
             cols=1, v={"direction": "up", "th": 55.0}),
        dict(form="cross", label="down（閾値55・列1本）",
             real={"form": "cross", "value": {"direction": "down", "th": {"n": 55.0}},
                   "material": [m1]},
             cols=1, v={"direction": "down", "th": 55.0}),
        # ★材料の前処理（部品 ts_max・2026-08-13 の段C の C-6 で足した）＝新高値・新安値。
        #   『RSI7 が 直前6本の最大値を上抜けた／下抜けた』。2026-08-13 より前は書けなかった。
        dict(form="cross", compose="cross_pre", label="up（直前6本の最大値）",
             real={"form": "cross", "value": {"direction": "up"},
                   "material": [m1, {**m1, "pre": {"op": "ts_max", "n": 6}}]},
             cols=1, v={"direction": "up", "n": 6, "op": "ts_max"}),
        dict(form="cross", compose="cross_pre", label="down（直前6本の最大値）",
             real={"form": "cross", "value": {"direction": "down"},
                   "material": [m1, {**m1, "pre": {"op": "ts_max", "n": 6}}]},
             cols=1, v={"direction": "down", "n": 6, "op": "ts_max"}),
        dict(form="cross", compose="cross_pre", label="down（直前6本の最小値）",
             real={"form": "cross", "value": {"direction": "down"},
                   "material": [m1, {**m1, "pre": {"op": "ts_min", "n": 6}}]},
             cols=1, v={"direction": "down", "n": 6, "op": "ts_min"}),
        dict(form="cross", compose="cross_pre", label="up（直前6本の最小値）",
             real={"form": "cross", "value": {"direction": "up"},
                   "material": [m1, {**m1, "pre": {"op": "ts_min", "n": 6}}]},
             cols=1, v={"direction": "up", "n": 6, "op": "ts_min"}),
        dict(form="diff", real={"form": "diff", "side": "above", "value": {"n": 0.5},
                                "material": [m1, m2]},
             cols=2, v={"th": 0.5, "side": "above"}),
        dict(form="touch", real={"form": "touch", "value": {"n": 0.05}, "material": [m1, m2]},
             cols=2, v={"tol": 0.05}),
        dict(form="candle_dir", real={"form": "candle_dir", "value": {"dir": "bull"},
                                      "material": []},
             cols=0, v={"dir": "bull"}),
        dict(form="candle_dir", real={"form": "candle_dir", "value": {"dir": "bear"},
                                      "material": []},
             cols=0, v={"dir": "bear"}),
        # ★入れ子の形は inner が「条件の直下」に在る（value の中ではない・実物 _eval_cond:745）
        dict(form="streak", real={"form": "streak", "value": {"n": 3, "offset": 0},
                                  "inner": {"form": "level", "side": "above",
                                            "value": {"n": 55.0}, "material": [m1]},
                                  "material": []},
             cols=1, v={"n": 3, "offset": 0, "inner": {"th": 55.0, "side": "above"}}),
        dict(form="within_n", real={"form": "within_n", "value": {"n": 6, "offset": 1},
                                    "inner": {"form": "level", "side": "below",
                                              "value": {"n": 45.0}, "material": [m1]},
                                    "material": []},
             cols=1, v={"n": 6, "offset": 1, "inner": {"th": 45.0, "side": "below"}}),
    ]


def _load_df():
    """突き合わせ用のデータ＝5分足の終わりの方 20,000 本 ＋ 材料2列だけ（全列は作らない）。"""
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import observe_diag as od
        cfg = od.load_config()
        bars = pd.read_csv(_DATA, parse_dates=["timestamp"]).set_index("timestamp").tail(_BARS)
        cfg_tf = dict(cfg)
        cfg_tf["timeframes"] = ["5m"]
        cat = [t for t in od.build_catalog(cfg) if t[0] in ("RSI7", "RSI21")]
        feats, _m = od.build_features(bars, cfg_tf, catalog=cat)
    df = bars.reset_index()[["open", "high", "low", "close", "volume"]].copy()
    for c in feats.columns:
        df[c] = feats[c].to_numpy(float)
    df["ts"] = bars.index
    return df


def run(break_form: str | None = None) -> int:
    """11個の形を、実行器の本物と部品の組み立てで突き合わせる。戻り＝食い違った形の数。"""
    import engine_tuner_exec as ex
    df = _load_df()
    m1 = {"family": "RSI", "param": 7, "tf": "5m"}
    m2 = {"family": "RSI", "param": 21, "tf": "5m"}
    cols_all = ["RSI7__5m", "RSI21__5m"]
    cases = _cases(m1, m2)
    n_forms = len({c["form"] for c in cases})
    ng = 0
    print(f"データ＝{_DATA.name} の終わりの {len(df):,} 本 ／ 材料＝RSI7__5m・RSI21__5m")
    print()
    print(f"{'形':14s} {'向き等':22s} {'本物の成立':>10s} {'部品の成立':>10s} {'食い違い':>8s}")
    print("-" * 72)
    for c in cases:
        f = c["form"]
        real = ex._eval_cond(c["real"], df, {}, "legacy", None)
        v = dict(c["v"])
        if break_form == f:                       # 番人＝わざと1か所 壊す
            v = {**v, "th": v.get("th", 0.0) + 1.0} if "th" in v else {**v, "n": v.get("n", 1) + 1}
        mine = COMPOSE[c.get("compose", f)](df, cols_all[:max(c["cols"], 1)], v)
        diff = int((np.asarray(real, bool) != np.asarray(mine, bool)).sum())
        label = c.get("label") or str(c["real"]["value"].get("direction")
                                      or c["real"]["value"].get("dir")
                                      or c["real"]["value"].get("side")
                                      or c["v"].get("side") or "")
        label = label[:22]
        mark = "" if diff == 0 else "  ❌"
        print(f"{f:14s} {label:22s} {int(np.asarray(real, bool).sum()):10,d} "
              f"{int(np.asarray(mine, bool).sum()):10,d} {diff:8,d}{mark}")
        if diff:
            ng += 1
    print("-" * 72)
    if ng == 0:
        print(f"✅ {n_forms}個の形（{len(cases)}通り）すべて、部品の組み立てと 1バーも違いません（食い違い 0）")
    else:
        print(f"❌ {ng} 件の形で食い違いました＝その形は部品が足りません")
    return ng


def selftest() -> int:
    """番人＝わざと壊したら食い違いが出るか（出なければ、この突き合わせは無意味）。"""
    print("=" * 72)
    print("condition_parts_diag 番人（わざと壊すと食い違いが出るか）")
    print("=" * 72)
    ok = True
    for f in ("level", "slope", "streak"):
        print(f"\n── わざと {f} の値を1つ ずらす ──")
        n = run(break_form=f)
        if n == 0:
            print(f"  ❌ {f} を壊したのに食い違いが出なかった＝番人が効いていない")
            ok = False
        else:
            print(f"  ✅ {f} を壊したら食い違いが出た")
    print("\n" + "=" * 72)
    print("  ✅ 番人 全部 pass" if ok else "  ❌ 番人が落ちた")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(1 if run() else 0)
