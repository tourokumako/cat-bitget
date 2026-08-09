#!/usr/bin/env python3
"""indicator_reference_diag.py — 指標カタログの正しさの証明に使う参照表（read-only・診断レーン）

何をするファイルか（まこさん確定 2026-07-30「とにかく正しい指標のライブラリになっていればいい。
その正しさの証明をどうするか」への実装）
--------------------------------------------------------------------------
observe_diag.py の指標カタログ全 96 種に対して、1種ずつ次を持つ:
  ① 定義・流儀・出典・方向の意味（定義表＝検査の出力に機械印字＝まこさんが目で照合できる）
  ② 外部ライブラリ ta による照合式（非同型の照合相手＝私と別の実装者のコード）
  ③ 教科書の式の独立実装（カタログと書き方を変えた実装）
  ④ 手計算の既知答え（電卓で出せる小さい合成データと期待値）
observe_diag.py の検査3（--inspect）がこの表を読んで機械照合する。
このファイルは売買記録を読まない・書かない・score を呼ばない（read-only 診断の部品）。

外部ライブラリ ta が無い環境では ②を飛ばし、③④で担保する（検査の出力に「対象外」と印字される）。

正しさの限界（正直に）: ③は私（CC）が書くので、定義を私が2回同じ向きに読み違えると照合が通る。
それを塞ぐのが ②（別の実装者）と ④（手計算の数字）と ①（まこさんの目）の3つ。
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

try:
    import ta as _ta
    TA_OK = True
except Exception:
    _ta = None
    TA_OK = False

# 2つ目の外部の照合相手（2026-08-09・マイルストーン①のフロー 段3）。
# ta で照合できない31件のうち、pandas-ta-classic なら照合できるものを拾うために足した。
try:
    import pandas_ta_classic as _pta
    PTA_OK = True
except Exception:
    _pta = None
    PTA_OK = False
# 3つ目の道具（ライブラリではない・独立に計算できるもの）。RCI の順位相関に使う。
try:
    from scipy import stats as _sps
    SCIPY_OK = True
except Exception:
    _sps = None
    SCIPY_OK = False

_IDX0 = "2026-03-01"


# ══ 共通部品（独立実装の道具・カタログとは書き方を変える）═══════════════
def _swv(x: np.ndarray, n: int):
    from numpy.lib.stride_tricks import sliding_window_view
    return sliding_window_view(x, n)


def _S(x, d) -> pd.Series:
    return pd.Series(x, index=d.index)


def _arr(d):
    return (d.open.to_numpy(float), d.high.to_numpy(float), d.low.to_numpy(float),
            d.close.to_numpy(float), d.volume.to_numpy(float))


def _roll(x: np.ndarray, n: int, how: str, ddof: int = 1) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        w = _swv(x, n)
        if how == "max":
            out[n - 1:] = w.max(axis=1)
        elif how == "min":
            out[n - 1:] = w.min(axis=1)
        elif how == "mean":
            out[n - 1:] = w.mean(axis=1)
        elif how == "sum":
            out[n - 1:] = w.sum(axis=1)
        elif how == "std":
            out[n - 1:] = w.std(axis=1, ddof=ddof)
    return out


def _wilder(x: np.ndarray, n: int) -> np.ndarray:
    """Wilder 平滑（教科書＝最初の n 本の単純平均を種に漸化式）。"""
    out = np.full(len(x), np.nan)
    if len(x) > n:
        out[n] = np.nanmean(x[1:n + 1])
        for i in range(n + 1, len(x)):
            out[i] = (out[i - 1] * (n - 1) + x[i]) / n
    return out


def _ema_rec(x: np.ndarray, span: int) -> np.ndarray:
    """EMA（教科書＝alpha=2/(span+1) の漸化式・最初の有効値を種に）。"""
    out = np.full(len(x), np.nan)
    a = 2.0 / (span + 1)
    prev = np.nan
    for i in range(len(x)):
        if np.isnan(x[i]):
            continue
        prev = x[i] if np.isnan(prev) else a * x[i] + (1 - a) * prev
        out[i] = prev
    return out


def _tr(h: np.ndarray, l: np.ndarray, c: np.ndarray) -> np.ndarray:
    pc = np.roll(c, 1)
    pc[0] = np.nan
    return np.nanmax(np.column_stack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=1)


def _div(a, b):
    return a / np.where(b == 0, np.nan, b)


# ══ 既知答え用の合成バー（手計算できる小さいデータ）═════════════════════
def _mk(c, o=None, h=None, l=None, v=None) -> pd.DataFrame:
    c = np.asarray(c, float)
    n = len(c)
    o = np.roll(c, 1) if o is None else np.asarray(o, float)
    if not isinstance(o, np.ndarray) or len(o) != n:
        o = np.asarray(o, float)
    if o is None or len(o) != n:
        o = np.roll(c, 1)
    if h is None:
        h = np.maximum(o, c)
    if l is None:
        l = np.minimum(o, c)
    h = np.asarray(h, float)
    l = np.asarray(l, float)
    v = np.full(n, 1.0) if v is None else np.asarray(v, float)
    idx = pd.date_range(_IDX0, periods=n, freq="5min")
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}, index=idx)


def _up(n=30, start=100.0, step=1.0):
    c = start + step * np.arange(n)
    return _mk(c)


def _dn(n=30, start=200.0, step=1.0):
    c = start - step * np.arange(n)
    return _mk(c)


def _flat(n=30, level=100.0):
    c = np.full(n, level)
    return _mk(c, o=c, h=c, l=c)


def _alt_pm1(n=40):
    """100 を挟んで ±1 を交互（BB・zscore の手計算用＝窓20の平均100・母標準偏差ちょうど1）。"""
    c = 100.0 + np.where(np.arange(n) % 2 == 0, -1.0, 1.0)
    c[-1] = 101.0
    return _mk(c, o=c, h=c, l=c)


def _range_case(n=300, hh=110.0, ll=100.0, cend=105.0):
    """窓の高値 110・安値 100・現値 105 の手計算用。スパイクは末尾8本目と5本目に置く
    ＝窓が9本（転換線）でも 288本（pivot 等）でも必ず窓の中に入る。"""
    c = np.full(n, 105.0)
    h = np.full(n, 105.0)
    l = np.full(n, 105.0)
    h[n - 8] = hh
    l[n - 5] = ll
    c[-1] = cend
    return _mk(c, o=c, h=np.maximum(h, c), l=np.minimum(l, c))


def _vp_case(n: int, va: float, vb: float):
    """出来高プロファイル（POC・VAH・VAL）の手計算用（2026-08-09・フロー 段3 の 3-4 で新設）。
    ★手で計算できるように、窓の中の終値を 100 と 200 の2つだけにする。
      窓＝最初の n 本（最後の1本は評価する場所で、窓には入らない）。
      前半 n//2 本＝終値100・出来高 va ／ 後半＝終値200・出来高 vb ／ 最後の1本＝終値100。
    ★実装は窓の最安値〜最高値を24等分する。100 は一番下の区画・200 は一番上の区画に入る。
      一番下の区画の中央 ＝ 100 ＋ (100/24)/2 ＝ 102.083333…
      一番上の区画の中央 ＝ 200 − (100/24)/2 ＝ 197.916666…
    ★va と vb の比で、出来高上位70%の帯が「1区画で足りる」か「2区画 要る」かが決まる。"""
    m = n // 2
    c = np.concatenate([np.full(m, 100.0), np.full(n - m, 200.0), np.array([100.0])])
    v = np.concatenate([np.full(m, float(va)), np.full(n - m, float(vb)), np.array([1.0])])
    return _mk(c, o=c, h=c, l=c, v=v)


_VP_LO = 100.0 + (100.0 / 24.0) / 2.0    # 一番下の区画の中央 ＝ 102.0833333…
_VP_HI = 200.0 - (100.0 / 24.0) / 2.0    # 一番上の区画の中央 ＝ 197.9166666…
_VP_D_LO = (100.0 / _VP_LO - 1.0) * 100.0   # 終値100 から見た乖離% ＝ −2.0408163265…
_VP_D_HI = (100.0 / _VP_HI - 1.0) * 100.0   # 同上 ＝ −49.4736842105…


# ══ 教科書の独立実装（③）════════════════════════════════════════════════
def _tb_rsi(d, p):
    n = p[0]
    df = np.diff(d.close.to_numpy(float), prepend=np.nan)
    au = _wilder(np.where(df > 0, df, 0.0), n)
    ad = _wilder(np.where(df < 0, -df, 0.0), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        return _S(100 - 100 / (1 + au / ad), d)


def _tb_atr_pct(d, p):
    o, h, l, c, v = _arr(d)
    return _S(_wilder(_tr(h, l, c), p[0]) / c * 100, d)


def _tb_adx_parts(d, n):
    o, h, l, c, v = _arr(d)
    up = np.diff(h, prepend=np.nan)
    dn = -np.diff(l, prepend=np.nan)
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    atr = _wilder(_tr(h, l, c), n)
    pdi = 100 * _div(_wilder(pdm, n), atr)
    mdi = 100 * _div(_wilder(mdm, n), atr)
    dx = 100 * _div(np.abs(pdi - mdi), pdi + mdi)
    return _wilder(dx, n), pdi, mdi


def _tb_adx(d, p):
    return _S(_tb_adx_parts(d, p[0])[0], d)


def _tb_didiff(d, p):
    _a, pdi, mdi = _tb_adx_parts(d, p[0])
    return _S(pdi - mdi, d)


def _tb_macd_line(d, p):
    c = d.close.to_numpy(float)
    return _S((_ema_rec(c, p[0]) - _ema_rec(c, p[1])) / c * 100, d)


def _tb_macd_hist(d, p):
    c = d.close.to_numpy(float)
    line = _ema_rec(c, p[0]) - _ema_rec(c, p[1])
    return _S((line - _ema_rec(line, p[2])) / c * 100, d)


def _tb_macd_signal(d, p):
    c = d.close.to_numpy(float)
    line = _ema_rec(c, p[0]) - _ema_rec(c, p[1])
    return _S(_ema_rec(line, p[2]) / c * 100, d)


def _tb_roc(d, p):
    n = p[0]
    c = d.close.to_numpy(float)
    out = np.full(len(c), np.nan)
    out[n:] = (c[n:] - c[:-n]) / c[:-n] * 100
    return _S(out, d)


def _tb_stoch_k(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    hh, ll = _roll(h, n, "max"), _roll(l, n, "min")
    return _S(100 * _div(c - ll, hh - ll), d)


def _tb_stoch_d(d, p):
    k = _tb_stoch_k(d, p).to_numpy()
    return _S(_roll(k, 3, "mean"), d)


def _tb_mfi(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    tp = (h + l + c) / 3
    mf = tp * v
    dtp = np.diff(tp, prepend=np.nan)
    pos = _roll(np.where(dtp > 0, mf, 0.0), n, "sum")
    neg = _roll(np.where(dtp < 0, mf, 0.0), n, "sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        return _S(100 - 100 / (1 + pos / neg), d)


def _tb_cmf(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    mult = _div((c - l) - (h - c), h - l)
    return _S(_div(_roll(mult * v, n, "sum"), _roll(v, n, "sum")), d)


def _tb_obv_slope(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    obv = np.zeros(len(c))
    for i in range(1, len(c)):
        s = np.sign(c[i] - c[i - 1])
        obv[i] = obv[i - 1] + (0.0 if np.isnan(s) else s) * v[i]
    out = np.full(len(c), np.nan)
    vs = _roll(v, n, "sum")
    out[n:] = _div(obv[n:] - obv[:-n], vs[n:])
    return _S(out, d)


def _tb_ichi(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    mid = (_roll(h, n, "max") + _roll(l, n, "min")) / 2
    return _S((c / mid - 1) * 100, d)


def _tb_rci(d, p):
    n = p[0]
    c = d.close.to_numpy(float)
    out = np.full(len(c), np.nan)
    tr_ = np.arange(1, n + 1)
    for i in range(n - 1, len(c)):
        pr = pd.Series(c[i - n + 1:i + 1]).rank().to_numpy()
        out[i] = (1 - 6 * ((pr - tr_) ** 2).sum() / (n * (n * n - 1))) * 100
    return _S(out, d)


def _tb_ema_slope(d, p):
    e = _ema_rec(d.close.to_numpy(float), p[0])
    out = np.full(len(e), np.nan)
    out[5:] = (e[5:] - e[:-5]) / e[:-5] * 100
    return _S(out, d)


def _tb_bb_pctb(d, p):
    n, s = p
    c = d.close.to_numpy(float)
    ma, sd = _roll(c, n, "mean"), _roll(c, n, "std", ddof=0)
    return _S(_div(c - (ma - s * sd), 2 * s * sd), d)


def _tb_bb_width(d, p):
    n, s = p
    c = d.close.to_numpy(float)
    return _S(_div(2 * s * _roll(c, n, "std", ddof=0), _roll(c, n, "mean")), d)


def _tb_rvol(d, p):
    c = d.close.to_numpy(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.log(c / np.where(np.roll(c, 1) == 0, np.nan, np.roll(c, 1)))
    r[0] = np.nan
    return _S(_roll(r, p[0], "std", ddof=1) * 100, d)


def _tb_donch(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    return _S((_roll(h, n, "max") - _roll(l, n, "min")) / c * 100, d)


def _tb_zscore(d, p):
    n = p[0]
    c = d.close.to_numpy(float)
    return _S(_div(c - _roll(c, n, "mean"), _roll(c, n, "std", ddof=1)), d)


def _tb_zscore_ret(d, p):
    n = p[0]
    c = d.close.to_numpy(float)
    r = np.log(c / np.roll(c, 1))
    r[0] = np.nan
    return _S(_div(r - _roll(r, n, "mean"), _roll(r, n, "std", ddof=1)), d)


def _tb_vr(d, p):
    o, h, l, c, v = _arr(d)
    return _S(_div(v, _roll(v, p[0], "mean")), d)


def _tb_engulf(d, p):
    o, h, l, c, v = _arr(d)
    po, pc = np.roll(o, 1), np.roll(c, 1)
    po[0] = pc[0] = np.nan
    bull = (pc < po) & (o < pc) & (c > po)
    bear = (pc > po) & (o > pc) & (c < po)
    return _S(bull.astype(float) - bear.astype(float), d)


def _tb_harami(d, p):
    o, h, l, c, v = _arr(d)
    po, pc = np.roll(o, 1), np.roll(c, 1)
    po[0] = pc[0] = np.nan
    bull = (pc < po) & (c > o) & (o > pc) & (c < po)
    bear = (pc > po) & (c < o) & (o < pc) & (c > po)
    return _S(bull.astype(float) - bear.astype(float), d)


def _tb_pinbar(d, p):
    o, h, l, c, v = _arr(d)
    lower = np.minimum(o, c) - l
    upper = h - np.maximum(o, c)
    return _S(_div(lower - upper, h - l), d)


def _tb_streak(d, p):
    o, h, l, c, v = _arr(d)
    s = np.sign(c - o)
    out = np.zeros(len(c))
    run = 0
    prev = 0.0
    for i in range(len(c)):
        run = run + 1 if s[i] == prev and s[i] != 0 else 1
        out[i] = run * s[i]
        prev = s[i]
    return _S(out, d)


def _tb_body(d, p):
    o, h, l, c, v = _arr(d)
    return _S(_div(np.abs(c - o), h - l), d)


def _tb_uwick(d, p):
    o, h, l, c, v = _arr(d)
    return _S(_div(h - np.maximum(o, c), h - l), d)


def _tb_lwick(d, p):
    o, h, l, c, v = _arr(d)
    return _S(_div(np.minimum(o, c) - l, h - l), d)


def _tb_dist_high(d, p):
    o, h, l, c, v = _arr(d)
    return _S((c / _roll(h, p[0], "max") - 1) * 100, d)


def _tb_dist_low(d, p):
    o, h, l, c, v = _arr(d)
    return _S((c / _roll(l, p[0], "min") - 1) * 100, d)


def _tb_bars_since_high(d, p):
    n = p[0]
    h = d.high.to_numpy(float)
    out = np.full(len(h), np.nan)
    for i in range(n - 1, len(h)):
        out[i] = n - 1 - int(np.argmax(h[i - n + 1:i + 1]))
    return _S(out, d)


def _tb_bars_since_low(d, p):
    n = p[0]
    l = d.low.to_numpy(float)
    out = np.full(len(l), np.nan)
    for i in range(n - 1, len(l)):
        out[i] = n - 1 - int(np.argmin(l[i - n + 1:i + 1]))
    return _S(out, d)


def _tb_shape(d, p):
    n = p[0]
    c = d.close.to_numpy(float)
    half = n // 2
    out = np.full(len(c), np.nan)
    out[n:] = np.sign(c[n:] - c[n - half:len(c) - half]) - np.sign(c[n - half:len(c) - half] - c[:-n])
    return _S(out, d)


def _w_case(n, second_low):
    """W字の既知答え用の合成バー。前半に底1=100・中央に山（ネックライン）=108・後半に底2=second_low・
    最終バーの終値 109 でネックライン上抜け。second_low=100.2 なら同水準（tol 0.003×109=0.327 以内）＝W字完成。"""
    half, q = n // 2, (n // 2) // 2
    m = n + 6
    c = np.full(m, 106.0)
    h = np.full(m, 106.0)
    l = np.full(m, 105.0)
    base = m - n
    l[base + 2] = 100.0                # 底1（前半・中央区間の外）
    h[base + half] = 108.0             # 間の山＝ネックライン（中央区間の中）
    l[base + half + q + 1] = second_low  # 底2（後半）
    c[-1] = 109.0
    return _mk(c=c, o=c.copy(), h=np.maximum(h, c), l=np.minimum(l, c))


def _tb_wpat(d, p):
    n, tol = int(p[0]), float(p[1])
    o, h, l, c, v = _arr(d)
    half, q = n // 2, (n // 2) // 2
    out = np.full(len(c), np.nan)
    for i in range(n - 1, len(c)):
        wl = l[i - n + 1:i + 1]
        wh = h[i - n + 1:i + 1]
        lo1 = np.min(wl[:n - half])
        lo2 = np.min(wl[n - half:])
        neck = np.max(wh[n - half - q:n - q])
        out[i] = 1.0 if (abs(lo1 - lo2) <= tol * c[i] and c[i] > neck) else 0.0
    return _S(out, d)


def _tb_vs_ema(d, p):
    return _S((d.close.to_numpy(float) / _ema_rec(d.close.to_numpy(float), p[0]) - 1) * 100, d)


def _tb_vs_sma(d, p):
    c = d.close.to_numpy(float)
    return _S((c / _roll(c, p[0], "mean") - 1) * 100, d)


def _tb_vs_vwap(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    vwap = _div(_roll(c * v, n, "sum"), _roll(v, n, "sum"))
    return _S((c / vwap - 1) * 100, d)


def _tb_keltner(d, p, side):
    n, k = p
    o, h, l, c, v = _arr(d)
    band = _ema_rec(c, n) + side * k * _wilder(_tr(h, l, c), 14)
    return _S((c / band - 1) * 100, d)


def _tb_supertrend_pct(d, p):
    """本物の Supertrend（バンドの切り上げ切り下げ＋終値の抜けで反転）の独立実装。"""
    n, k = p
    o, h, l, c, v = _arr(d)
    atr = _wilder(_tr(h, l, c), int(n))
    hl2 = (h + l) / 2
    ub, lb = hl2 + k * atr, hl2 - k * atr
    line = np.full(len(c), np.nan)
    fu = fl = np.nan
    up = True
    for i in range(len(c)):
        if np.isnan(atr[i]):
            continue
        if np.isnan(fu):
            fu, fl = ub[i], lb[i]
            line[i] = fl if up else fu
            continue
        pu, pl = fu, fl
        fu = ub[i] if (ub[i] < pu or c[i - 1] > pu) else pu
        fl = lb[i] if (lb[i] > pl or c[i - 1] < pl) else pl
        if c[i] > fu:
            up = True
        elif c[i] < fl:
            up = False
        line[i] = fl if up else fu
    return _S((c / line - 1) * 100, d)


def _tb_vs_pivot(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    pc = np.roll(c, 1)
    pc[0] = np.nan
    pp = (_roll(h, n, "max") + _roll(l, n, "min") + pc) / 3
    return _S((c / pp - 1) * 100, d)


def _tb_vs_pivot_rs(d, p, which):
    n = p[0]
    o, h, l, c, v = _arr(d)
    pc = np.roll(c, 1)
    pc[0] = np.nan
    hh, ll = _roll(h, n, "max"), _roll(l, n, "min")
    pp = (hh + ll + pc) / 3
    lvl = (2 * pp - ll) if which > 0 else (2 * pp - hh)
    return _S((c / lvl - 1) * 100, d)


def _tb_fib(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    hh, ll = _roll(h, n, "max"), _roll(l, n, "min")
    return _S(_div(c - ll, hh - ll), d)


def _vp_ref(d, n):
    """出来高プロファイルの独立実装（同じアルゴリズムを別の書き方で）。"""
    o, h, l, c, v = _arr(d)
    poc = np.full(len(c), np.nan)
    vah = np.full(len(c), np.nan)
    val = np.full(len(c), np.nan)
    for i in range(n, len(c)):
        cw, vw = c[i - n:i], v[i - n:i]
        bins = np.linspace(cw.min(), cw.max(), 25)
        which = np.clip(np.digitize(cw, bins) - 1, 0, 23)
        agg = np.zeros(24)
        for b, w in zip(which, vw):
            agg[b] += w
        centers = (bins[:-1] + bins[1:]) / 2
        order = np.argsort(agg)[::-1]        # 同量の帯は価格の高い側を採る（カタログの決めに合わせる）
        cum = np.cumsum(agg[order]) / max(agg.sum(), 1e-9)
        keep = centers[order[:max(1, int(np.searchsorted(cum, 0.7)) + 1)]]
        poc[i] = centers[order[0]]
        vah[i] = keep.max()
        val[i] = keep.min()
    return poc, vah, val


def _tb_vs_vp(d, p, which):
    n = p[0]
    c = d.close.to_numpy(float)
    lv = _vp_ref(d, n)[which]
    return _S((c / lv - 1) * 100, d)


def _tb_sr_touch(d, p):
    n, tol = int(p[0]), float(p[1])
    o, h, l, c, v = _arr(d)
    out = np.full(len(c), np.nan)
    for i in range(n, len(c)):
        band = c[i] * tol
        out[i] = float(np.sum((h[i - n:i] >= c[i] - band) & (l[i - n:i] <= c[i] + band)))
    return _S(out, d)


# ══ 外部ライブラリ照合（②・ta が無ければ検査側で「対象外」になる）════════
def _ext_rsi(d, p):
    return _ta.momentum.RSIIndicator(d.close, p[0]).rsi()


def _ext_adx(d, p):
    return _ta.trend.ADXIndicator(d.high, d.low, d.close, p[0]).adx()


def _ext_didiff(d, p):
    a = _ta.trend.ADXIndicator(d.high, d.low, d.close, p[0])
    return a.adx_pos() - a.adx_neg()


def _ext_atr_pct(d, p):
    return _ta.volatility.AverageTrueRange(d.high, d.low, d.close, p[0]).average_true_range() / d.close * 100


def _ext_macd_line(d, p):
    return _ta.trend.MACD(d.close, p[1], p[0], 9).macd() / d.close * 100


def _ext_macd_hist(d, p):
    return _ta.trend.MACD(d.close, p[1], p[0], p[2]).macd_diff() / d.close * 100


def _ext_macd_signal(d, p):
    return _ta.trend.MACD(d.close, p[1], p[0], p[2]).macd_signal() / d.close * 100


def _ext_roc(d, p):
    return _ta.momentum.ROCIndicator(d.close, p[0]).roc()


def _ext_stoch_k(d, p):
    return _ta.momentum.StochasticOscillator(d.high, d.low, d.close, p[0], 3).stoch()


def _ext_stoch_d(d, p):
    return _ta.momentum.StochasticOscillator(d.high, d.low, d.close, p[0], 3).stoch_signal()


def _ext_mfi(d, p):
    return _ta.volume.MFIIndicator(d.high, d.low, d.close, d.volume, p[0]).money_flow_index()


def _ext_cmf(d, p):
    return _ta.volume.ChaikinMoneyFlowIndicator(d.high, d.low, d.close, d.volume, p[0]).chaikin_money_flow()


def _ext_obv_slope(d, p):
    obv = _ta.volume.OnBalanceVolumeIndicator(d.close, d.volume).on_balance_volume()
    return obv.diff(p[0]) / d.volume.rolling(p[0]).sum().replace(0, np.nan)


def _ext_tenkan(d, p):
    line = _ta.trend.IchimokuIndicator(d.high, d.low, p[0], 26).ichimoku_conversion_line()
    return (d.close / line - 1) * 100


def _ext_kijun(d, p):
    line = _ta.trend.IchimokuIndicator(d.high, d.low, 9, p[0]).ichimoku_base_line()
    return (d.close / line - 1) * 100


def _ext_bb_pctb(d, p):
    return _ta.volatility.BollingerBands(d.close, p[0], p[1]).bollinger_pband()


def _ext_bb_width(d, p):
    return _ta.volatility.BollingerBands(d.close, p[0], p[1]).bollinger_wband() / 100


def _ext_donch(d, p):
    dc = _ta.volatility.DonchianChannel(d.high, d.low, d.close, p[0])
    return (dc.donchian_channel_hband() - dc.donchian_channel_lband()) / d.close * 100


def _ext_ema_slope(d, p):
    e = _ta.trend.EMAIndicator(d.close, p[0]).ema_indicator()
    return e.pct_change(5) * 100


def _ext_vs_ema(d, p):
    return (d.close / _ta.trend.EMAIndicator(d.close, p[0]).ema_indicator() - 1) * 100


def _ext_vs_sma(d, p):
    return (d.close / _ta.trend.SMAIndicator(d.close, p[0]).sma_indicator() - 1) * 100


def _ext_keltner(d, p, side):
    if float(p[1]) != 2.0:                      # ta の乗数は 2 固定＝それ以外は対象外
        return None
    kc = _ta.volatility.KeltnerChannel(d.high, d.low, d.close, p[0], 14, original_version=False)
    band = kc.keltner_channel_hband() if side > 0 else kc.keltner_channel_lband()
    return (d.close / band - 1) * 100


# ══ 2つ目の照合の相手（2026-08-09・フロー 段3）══════════════════════════
# ★何のためか＝外部ライブラリ ta で照合できるのは53件のうち22件だけ。残り31件は
#   「私（CC）が書いた式」しか照合の相手がいない＝私が2回 同じ向きに読み違えると通ってしまう。
#   そこで、別のライブラリ（pandas-ta-classic）と別の道具（scipy）で照合できるものを足した。
# ★どれを足すかは「名前が同じだから」では決めていない。実データ（5分足の直近6,000本）で
#   実際に突き合わせて、許容差の中に入ったものだけを足した。入らなかったものは足していない。
def _x2_zscore(d, p):
    return _pta.zscore(d.close, length=int(p[0]))


def _x2_zscore_ret(d, p):
    return _pta.zscore(np.log(d.close / d.close.shift()), length=int(p[0]))


def _x2_rvol(d, p):
    # hvol は「年率化しない（annualization=1）」で、うちの realized_vol と同じ＝対数リターンの標準偏差の%
    return _pta.hvol(d.close, length=int(p[0]), annualization=1)


def _x2_obv_slope(d, p):
    n = int(p[0])
    return _pta.obv(d.close, d.volume).diff(n) / d.volume.rolling(n).sum().replace(0, np.nan)


def _x2_vr(d, p):
    return d.volume / _pta.sma(d.volume, length=int(p[0]))


def _x2_donch(d, p, side):
    n = int(p[0])
    dc = _pta.donchian(d.high, d.low, lower_length=n, upper_length=n)
    band = dc.iloc[:, 2] if side > 0 else dc.iloc[:, 0]   # 2列目＝上限 / 0列目＝下限
    return (d.close / band - 1) * 100


def _x2_fib(d, p):
    # うちの fib位置＝n本の高安の中の位置 0〜1。ライブラリの stochf の生の %K（0〜100）と同じ形
    return _pta.stochf(d.high, d.low, d.close, fastk=int(p[0]), fastd=1).iloc[:, 0] / 100.0


def _x2_rci(d, p):
    """RCI を scipy の順位相関で独立に計算する（ライブラリではなく別の道具）。
    うちの RCI ＝ 時間の並びと値段の並びの順位相関 ×100。scipy の spearmanr がそれそのもの。

    ★窓の中に同じ値段が2本以上あるときは、照合の対象から外す（NaN を返す）。
      理由＝うちの式は 1 − 6Σd²/(n(n²−1)) という簡便式で、これが順位相関と一致するのは
      「同じ順位が無いとき」だけ。同じ値段があると、簡便式と scipy の式（順位のピアソン相関）は
      理論上ずれる。どちらかが間違いなのではなく、流儀が違う。
      ★実測（5分足の直近500本・2026-08-09）＝同値なしの窓では最大差 2.8e-14 で一致。
        同値のある窓は RCI9 で 37/500 本・RCI26 で 145/500 本あり、そこでは最大 0.83 ずれる。
      ★許容差をゆるめて通すことはしない。比べられる所だけを正直に比べる。"""
    n = int(p[0])
    t = np.arange(n, dtype=float)

    def one(x):
        if len(np.unique(x)) != n:      # 同じ値段がある窓＝簡便式と定義がずれるので照合しない
            return np.nan
        return _sps.spearmanr(t, x).statistic * 100.0

    return d.close.rolling(n).apply(one, raw=True)


# family → (照合の関数, 使った道具の名前)。ここに無い family は2つ目の照合が無い。
EXT2: dict[str, tuple] = {
    "zscore": (_x2_zscore, "pandas-ta"),
    "zscore_return": (_x2_zscore_ret, "pandas-ta"),
    "realized_vol": (_x2_rvol, "pandas-ta"),
    "OBV傾き": (_x2_obv_slope, "pandas-ta"),
    "volume_ratio": (_x2_vr, "pandas-ta"),
    "swing高値距離": (lambda d, p: _x2_donch(d, p, +1), "pandas-ta"),
    "swing安値距離": (lambda d, p: _x2_donch(d, p, -1), "pandas-ta"),
    "n本高値": (lambda d, p: _x2_donch(d, p, +1), "pandas-ta"),
    "n本安値": (lambda d, p: _x2_donch(d, p, -1), "pandas-ta"),
    "fib位置": (_x2_fib, "pandas-ta"),
    "RCI": (_x2_rci, "scipy"),
}


def ext2_ready() -> bool:
    """2つ目の照合が使える状態か（ライブラリと道具が両方 入っているか）。"""
    return bool(PTA_OK and SCIPY_OK)


# ══ 参照表（①〜④を1種ずつ）＝ observe_diag の検査3 が読む正本 ═══════════
REFS: list[dict] = []


def _r(pat, family, teigi, ryugi, houkou, prop, tb=None, ext=None, known=None, tol=1e-6):
    REFS.append(dict(pat=re.compile("^" + pat + "$"), family=family, teigi=teigi, ryugi=ryugi,
                     houkou=houkou, prop=prop, tb=tb, ext=ext, known=known, tol=tol))


def _num(g):
    f = float(g)
    return int(f) if f == int(f) and "." not in g else f


def find(name: str):
    """カタログ名 → (参照エントリ, パラメータのタプル)。無ければ (None, None)。"""
    for e in REFS:
        m = e["pat"].match(name)
        if m:
            return e, tuple(_num(g) for g in m.groups())
    return None, None


def coverage(names: list[str]) -> list[str]:
    """参照表に載っていないカタログ名の一覧（空であるべき＝番人が使う）。"""
    return [n for n in names if find(n)[0] is None]


# ── トレンド・モメンタム ──
_r(r"ADX(\d+)", "ADX",
   "平均方向性指数。DI+ と DI− の差の比率 DX を Wilder 平滑した 0〜100",
   "Wilder 1978。平滑3段とも Wilder 式", "状態量＝大きいほどトレンドが強い（向きは持たない）", "none",
   tb=_tb_adx, ext=_ext_adx)
_r(r"DI差(\d+)", "DI差",
   "方向性指標の差 DI+ − DI−", "Wilder 1978", "順張り値＝プラスで上昇方向が優勢", "trend",
   tb=_tb_didiff, ext=_ext_didiff)
_r(r"MACD線%\((\d+),(\d+)\)", "MACD線%",
   "短期 EMA − 長期 EMA を終値で割って%化", "Appel。EMA は標準の漸化式・%化は価格非依存 H6 のための本プロジェクトの流儀",
   "順張り値＝プラスで上昇の勢い", "trend", tb=_tb_macd_line, ext=_ext_macd_line,
   known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])])
_r(r"MACDヒスト%\((\d+),(\d+),(\d+)\)", "MACDヒスト%",
   "MACD線 − シグナル線（MACD線の EMA）を終値で割って%化", "Appel。%化は本プロジェクトの流儀",
   "順張り値＝プラスで勢いが加速", "trend", tb=_tb_macd_hist, ext=_ext_macd_hist,
   known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])])
_r(r"MACDシグナル線%\((\d+),(\d+),(\d+)\)", "MACDシグナル線%",
   "シグナル線（MACD線の g 本 EMA）を終値で割って%化", "Appel。%化は本プロジェクトの流儀。単体列は 2026-07-30 検査7（軸カタログ照合）を受けて追加",
   "順張り値＝プラスで上昇の勢いが持続", "trend", tb=_tb_macd_signal, ext=_ext_macd_signal,
   known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])])
_r(r"RSI(\d+)", "RSI",
   "相対力指数。n 本の平均上昇幅と平均下落幅の比から 0〜100", "Wilder 1978。全部上昇の窓は 100（世界標準の慣例・TradingView と同じ）",
   "順張り値＝大きいほど上昇の勢い", "trend", tb=_tb_rsi, ext=_ext_rsi,
   known=lambda p: [(_up(p[0] * 4 + 10), [(-1, 100.0, 1e-9)])])
_r(r"ROC(\d+)", "ROC",
   "n 本前からの変化率%", "標準", "順張り値", "trend", tb=_tb_roc, ext=_ext_roc,
   known=lambda p: [(_mk(np.r_[np.full(p[0] + 5, 100.0), 110.0]), [(-1, 10.0, 1e-9)])])
_r(r"Stoch%K(\d+)", "Stoch%K",
   "n 本の高安レンジの中で終値がどの位置か 0〜100", "Lane。平滑なしの fast %K", "順張り値", "trend",
   tb=_tb_stoch_k, ext=_ext_stoch_k,
   known=lambda p: [(_mk(100 + np.arange(p[0] + 5, dtype=float)), [(-1, 100.0, 1e-9)])])
_r(r"Stoch%D(\d+)", "Stoch%D",
   "%K の3本単純移動平均", "Lane", "順張り値", "trend", tb=_tb_stoch_d, ext=_ext_stoch_d,
   known=lambda p: [(_mk(100 + np.arange(p[0] + 8, dtype=float)), [(-1, 100.0, 1e-9)])])
_r(r"MFI(\d+)", "MFI",
   "出来高つき RSI。典型価格×出来高の上昇分と下落分の比から 0〜100", "標準。全部上昇の窓は 100（世界標準の慣例）",
   "順張り値", "trend", tb=_tb_mfi, ext=_ext_mfi,
   known=lambda p: [(_mk(100 + np.arange(p[0] + 5, dtype=float)), [(-1, 100.0, 1e-9)])])
_r(r"CMF(\d+)", "CMF",
   "終値がバーの中のどちら側で引けたかを出来高で重みづけした −1〜+1", "Chaikin",
   "順張り値＝プラスで買い圧", "trend", tb=_tb_cmf, ext=_ext_cmf,
   known=lambda p: [(_mk(100 + np.arange(p[0] + 5, dtype=float),
                         o=100 + np.arange(p[0] + 5, dtype=float) - 0.5,
                         h=100 + np.arange(p[0] + 5, dtype=float),
                         l=100 + np.arange(p[0] + 5, dtype=float) - 1.0), [(-1, 1.0, 1e-9)])])
_r(r"OBV傾き(\d+)", "OBV傾き",
   "OBV（上昇バーの出来高を足し下落バーで引く累積）の n 本変化を同区間の出来高で正規化",
   "Granville＋本プロジェクトの正規化。終値が前バーと同値のバーは加算しない（Granville の定義）。"
   "外部ライブラリ ta は同値を上昇扱いする変種のため外部照合の対象外（2026-07-30 実データ照合で判明）",
   "順張り値", "trend", tb=_tb_obv_slope,
   known=lambda p: [(_up(p[0] + 5), [(-1, 1.0, 1e-9)])])
_r(r"close vs 転換線%\((\d+)\)", "転換線",
   "一目均衡表の転換線（n 本高値と安値の中点）からの乖離%", "一目山人。n=9 が標準",
   "順張り値", "trend", tb=_tb_ichi, ext=_ext_tenkan,
   known=lambda p: [(_range_case(), [(-1, 0.0, 1e-6)])])
_r(r"close vs 基準線%\((\d+)\)", "基準線",
   "一目均衡表の基準線（n 本高値と安値の中点）からの乖離%", "一目山人。n=26 が標準",
   "順張り値", "trend", tb=_tb_ichi, ext=_ext_kijun,
   known=lambda p: [(_range_case(), [(-1, 0.0, 1e-6)])])
_r(r"RCI(\d+)", "RCI",
   "時間の順位と価格の順位の相関（Spearman）×100。−100〜+100",
   "日本のテクニカルで標準。同値の順位は平均順位。★式は RCI＝{1−6D/(N(N²−1))}×100 の簡便式を使い、"
   "同じ値段が並んだときは平均順位を割り当てる（出典の逐語＝「同値で順番が同じ場合は、例えば1位が2つある時には"
   "(1＋2)／2＝1.5、3位が2つある時には(3＋4)／2＝3.5 を両方の番号に付します」futuresite.jp/guide/technical/rci.htm ／"
   "TradingView jp「2つ以上の価格が等しくなった場合は、それらの各々にその順位位置の平均値を最終順位として割り当てます」）。"
   "★scipy の spearmanr は同値のとき『順位のピアソン相関』で計算するので、この簡便式とは理論上ずれる＝流儀の違いで、"
   "うちが間違いなのではない（2026-08-09 に出典2本を開いて確認）。だから2つ目の照合は同値の無い窓だけで行う",
   "順張り値＝+100 で一貫した上昇", "trend", tb=_tb_rci,
   known=lambda p: [(_up(p[0] + 5), [(-1, 100.0, 1e-9)]), (_dn(p[0] + 5), [(-1, -100.0, 1e-9)])])
_r(r"EMA(\d+)傾き%", "EMA傾き",
   "EMA の5本前からの変化率%", "EMA は標準・傾きの5本は本プロジェクトの流儀",
   "順張り値", "trend", tb=_tb_ema_slope, ext=_ext_ema_slope,
   known=lambda p: [(_flat(max(60, p[0] * 4)), [(-1, 0.0, 1e-9)])])
# ── ボラ ──
_r(r"ATR%(\d+)", "ATR%",
   "真の値幅（ギャップ込みの高安幅）の Wilder 平滑を終値で割って%化", "Wilder 1978。%化は H6 のための流儀",
   "ボラ量＝大きいほど荒い", "vol", tb=_tb_atr_pct, ext=_ext_atr_pct,
   known=lambda p: [(_mk(np.full(p[0] * 5, 100.0), o=np.full(p[0] * 5, 100.0),
                         h=np.full(p[0] * 5, 101.0), l=np.full(p[0] * 5, 99.0)), [(-1, 2.0, 1e-9)])])
_r(r"BB%b\((\d+),([\d.]+)\)", "BB%b",
   "ボリンジャーバンドの中の終値の位置。下バンド=0・上バンド=1", "Bollinger。標準偏差は母集団（ddof=0）＝TradingView・ta と同じ（2026-07-30 に標本 ddof=1 から世界標準へ統一）",
   "順張り値", "trend", tb=_tb_bb_pctb, ext=_ext_bb_pctb,
   known=lambda p: [(_alt_pm1(p[0] * 2), [(-1, 0.75, 1e-9)])] if p[0] == 20 and p[1] == 2 else None)
_r(r"BB幅\((\d+),([\d.]+)\)", "BB幅",
   "バンドの全幅（2×σ倍率×標準偏差）を移動平均で割った比", "Bollinger。標準偏差は母集団（ddof=0）＝世界標準へ統一（2026-07-30）",
   "ボラ量", "vol", tb=_tb_bb_width, ext=_ext_bb_width,
   known=lambda p: [(_alt_pm1(p[0] * 2), [(-1, 0.04, 1e-9)])] if p[0] == 20 and p[1] == 2 else None)
_r(r"realized_vol(\d+)", "realized_vol",
   "対数リターンの n 本標準偏差×100", "標準（標本標準偏差 ddof=1）", "ボラ量", "vol", tb=_tb_rvol,
   known=lambda p: [(_flat(p[0] * 3), [(-1, 0.0, 1e-9)])])
_r(r"Donchian幅%(\d+)", "Donchian幅",
   "n 本の最高値と最安値の幅を終値で割って%化", "Donchian", "ボラ量", "vol",
   tb=_tb_donch, ext=_ext_donch,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, 10.0 / 105.0 * 100, 1e-9)])] if p[0] >= 20 else None)
_r(r"zscore(\d+)", "zscore",
   "終値が n 本平均から標準偏差いくつ分離れているか", "標準（標本標準偏差 ddof=1）",
   "順張り値", "trend", tb=_tb_zscore,
   known=lambda p: [(_alt_pm1(p[0] * 2), [(-1, 1.0 / float(np.sqrt(p[0] / (p[0] - 1))), 1e-9)])])
_r(r"zscore_return(\d+)", "zscore_return",
   "対数リターンが n 本平均から標準偏差いくつ分離れているか",
   "標準（標本標準偏差 ddof=1）。価格基準の zscore とは別の指標（軸カタログ E-c の zscore_return）＝2026-07-30 検査7 を受けて追加",
   "状態量＝行き過ぎの計測（プラスは直近の平均より強い動きの意味で、上昇方向の優勢ではない。"
   "合成でも実データでも上げ下げと結びつかないことを実測＝2026-08-06 材料検査で是正・まこさん OK）", "none", tb=_tb_zscore_ret,
   known=lambda p: [(_mk(100.0 * np.exp(np.cumsum(np.resize([0.01, -0.01], p[0] * 2)))),
                     [(-1, -float(np.sqrt((p[0] - 1) / p[0])), 1e-9)])])
# ── 出来高 ──
_r(r"volume_ratio(\d+)", "volume_ratio",
   "出来高が n 本平均の何倍か", "標準", "状態量＝大きいほど商いが厚い", "none", tb=_tb_vr,
   known=lambda p: [(_up(p[0] + 5), [(-1, 1.0, 1e-9)])])
# ── ローソク ──
_r(r"包み足", "包み足",
   "前バーと逆の色で実体を包む反転パターン。陽の包み=+1・陰の包み=−1・それ以外0",
   "教科書定義（前バーの色を条件に含む）＝2026-07-30 に簡略形（色を問わない）から是正",
   "反転サイン＝+1 は買い転換の示唆", "reversal", tb=_tb_engulf,
   known=lambda p: [(_mk(c=[100.0, 100.0, 101.1], o=[101.0, 101.0, 99.9],
                         h=[101.0, 101.0, 101.2], l=[99.9, 99.9, 99.8]), [(-1, 1.0, 1e-9)]),
                    (_mk(c=[101.0, 101.0, 99.9], o=[100.0, 100.0, 101.2],
                         h=[101.0, 101.0, 101.3], l=[99.9, 99.9, 99.8]), [(-1, -1.0, 1e-9)])])
_r(r"孕み足", "孕み足",
   "前バーと逆の色で実体が前バーの実体の中に収まる反転パターン。陽の孕み=+1・陰の孕み=−1・それ以外0",
   "教科書定義（前バーの色と当バーの色の両方を条件に含む・実体の内包は強い不等号）＝2026-07-30 検査7（軸カタログ照合）を受けて追加",
   "反転サイン＝+1 は買い転換の示唆", "reversal", tb=_tb_harami,
   known=lambda p: [(_mk(c=[100.0, 99.8, 100.5], o=[100.0, 101.2, 100.0],
                         h=[100.0, 101.2, 100.6], l=[100.0, 99.7, 99.9]), [(-1, 1.0, 1e-9)]),
                    (_mk(c=[100.0, 101.2, 99.9], o=[100.0, 99.8, 100.4],
                         h=[100.0, 101.3, 100.5], l=[99.9, 99.7, 99.8]), [(-1, -1.0, 1e-9)])])
_r(r"pinbar", "pinbar",
   "（下ヒゲ−上ヒゲ）÷全幅。+0.5 超で強い下ヒゲ（買い転換の示唆）",
   "標準のピンバー比", "反転サイン", "reversal", tb=_tb_pinbar,
   known=lambda p: [(_mk(c=[100.0, 100.5], o=[100.0, 100.0], h=[100.0, 100.6], l=[100.0, 99.0]),
                     [(-1, 0.5625, 1e-9)])])
_r(r"連続本数", "連続本数",
   "同じ色のバーが何本続いたか（陽線+n・陰線−n）", "標準", "順張り値", "trend", tb=_tb_streak,
   known=lambda p: [(_mk(c=[101.0, 102.0, 103.0], o=[100.0, 101.0, 102.0]), [(-1, 3.0, 1e-9)])])
_r(r"body比", "body比",
   "実体÷全幅", "標準", "状態量＝大きいほど迷いのないバー", "none", tb=_tb_body,
   known=lambda p: [(_mk(c=[100.0, 100.5], o=[100.0, 100.0], h=[100.0, 100.6], l=[100.0, 99.0]),
                     [(-1, 0.3125, 1e-9)])])
_r(r"上ヒゲ比", "上ヒゲ比",
   "上ヒゲ÷全幅", "標準", "反転サイン＝大きいほど上値の売り圧の示唆", "reversal", tb=_tb_uwick,
   known=lambda p: [(_mk(c=[100.0, 100.5], o=[100.0, 100.0], h=[100.0, 100.6], l=[100.0, 99.0]),
                     [(-1, 0.0625, 1e-9)])])
_r(r"下ヒゲ比", "下ヒゲ比",
   "下ヒゲ÷全幅", "標準", "反転サイン＝大きいほど下値の買い支えの示唆", "reversal", tb=_tb_lwick,
   known=lambda p: [(_mk(c=[100.0, 100.5], o=[100.0, 100.0], h=[100.0, 100.6], l=[100.0, 99.0]),
                     [(-1, 0.625, 1e-9)])])
# ── 形 ──
_r(r"swing高値距離%(\d+)", "swing高値距離",
   "n 本最高値からの乖離%（0に近いほど高値圏）", "標準。close vs n本高値% と同一の式＝重複列（歩2 の同系統制限の対象）",
   "順張り値", "trend", tb=_tb_dist_high,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, (105.0 / 110.0 - 1) * 100, 1e-9)])])
_r(r"swing安値距離%(\d+)", "swing安値距離",
   "n 本最安値からの乖離%", "標準。close vs n本安値% と同一の式＝重複列", "順張り値", "trend", tb=_tb_dist_low,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, 5.0, 1e-9)])])
_r(r"高値からの経過バー(\d+)", "高値からの経過バー",
   "n 本窓の最高値から何本たったか", "標準",
   "状態量＝経過の量（★一方向に動き続ける相場では向きが出る＝2026-08-06 材料検査の実測。"
   "普通の相場では向きの差は四分位幅の半分以下。型の表で向きの材料に使わない・まこさん OK）", "none", tb=_tb_bars_since_high,
   known=lambda p: [(_mk(c=np.full(p[0] + 20, 100.0), o=np.full(p[0] + 20, 100.0),
                         h=np.r_[np.full(p[0] + 9, 100.0), 110.0, np.full(10, 100.0)],
                         l=np.full(p[0] + 20, 99.0)), [(-1, 10.0, 1e-9)])])
_r(r"安値からの経過バー(\d+)", "安値からの経過バー",
   "n 本窓の最安値から何本たったか", "標準",
   "状態量＝経過の量（★一方向に動き続ける相場では向きが出る＝2026-08-06 材料検査の実測。"
   "普通の相場では向きの差は四分位幅の半分以下。型の表で向きの材料に使わない・まこさん OK）", "none", tb=_tb_bars_since_low,
   known=lambda p: [(_mk(c=np.full(p[0] + 20, 100.0), o=np.full(p[0] + 20, 100.0),
                         h=np.full(p[0] + 20, 101.0),
                         l=np.r_[np.full(p[0] + 9, 100.0), 90.0, np.full(10, 100.0)]), [(-1, 10.0, 1e-9)])])
_r(r"形スコア(\d+)\(V=\+/M=−\)", "形スコア",
   "後半の向き − 前半の向き。V字（下げて上げ）=+2・M字（上げて下げ）=−2・一方向=0",
   "本プロジェクトの流儀。2026-07-30 に式の符号を名前どおりへ是正（旧式は和で V も M も 0 になっていた）",
   "反転サイン", "reversal", tb=_tb_shape,
   known=lambda p: [(_mk(np.r_[np.linspace(110, 100, p[0] // 2 + 1), np.linspace(100, 110, p[0] // 2 + 1)[1:],
                               np.full(2, 110.0)][:p[0] + 3]), [(p[0], 2.0, 1e-9)]),
                    (_mk(np.r_[np.linspace(100, 110, p[0] // 2 + 1), np.linspace(110, 100, p[0] // 2 + 1)[1:],
                               np.full(2, 100.0)][:p[0] + 3]), [(p[0], -2.0, 1e-9)])])
_r(r"W字\((\d+),([\d.]+)\)", "W字",
   "ダブルボトム（W字）の完成フラグ。窓 n の前半の最安値と後半の最安値が同水準（許容幅=tol×終値）で、"
   "終値がネックラインを上抜けたら 1・それ以外 0",
   "教科書のダブルボトム＝2つの底が同水準＋間の山（ネックライン）の上抜けで完成。ネックラインは"
   "中央 n/2 区間の最高値で近似（ベクトル計算のための本プロジェクトの流儀）。定義は 2026-07-30 に"
   "まこさん判断不能のため feedback_design_judgment_owner に基づき CC が案A（教科書定義）で確定",
   "反転サイン＝1 は買い転換（ダブルボトム完成）の示唆", "reversal", tb=_tb_wpat,
   known=lambda p: [(_w_case(int(p[0]), 100.2), [(-1, 1.0, 1e-9)]),
                    (_w_case(int(p[0]), 92.0), [(-1, 0.0, 1e-9)])])
# ── 位置 ──
_r(r"close vs EMA(\d+)%", "close vs EMA",
   "EMA からの乖離%", "EMA は標準の漸化式", "順張り値", "trend", tb=_tb_vs_ema, ext=_ext_vs_ema,
   known=lambda p: [(_flat(max(60, p[0] * 4)), [(-1, 0.0, 1e-9)])])
_r(r"close vs SMA(\d+)%", "close vs SMA",
   "単純移動平均からの乖離%", "標準", "順張り値", "trend", tb=_tb_vs_sma, ext=_ext_vs_sma,
   known=lambda p: [(_flat(p[0] + 10), [(-1, 0.0, 1e-9)])])
_r(r"close vs VWAP%(\d+)", "close vs VWAP",
   "終値ベースの移動 VWAP（出来高加重平均）からの乖離%",
   "★流儀に注意＝世界標準の VWAP はセッション起点＋典型価格。本カタログは n 本の移動窓＋終値で、24時間市場向けの本プロジェクトの流儀。外部照合は定義が違うため対象外",
   "順張り値", "trend", tb=_tb_vs_vwap,
   known=lambda p: [(_flat(p[0] + 10), [(-1, 0.0, 1e-9)])])
_r(r"close vs Keltner上%\((\d+),([\d.]+)\)", "Keltner上",
   "ケルトナーチャネル上バンド（EMA + k×ATR14）からの乖離%", "Keltner（ATR は Wilder 14）",
   "順張り値", "trend", tb=lambda d, p: _tb_keltner(d, p, +1), ext=lambda d, p: _ext_keltner(d, p, +1),
   known=lambda p: [(_flat(120), [(-1, 0.0, 1e-9)])])
_r(r"close vs Keltner下%\((\d+),([\d.]+)\)", "Keltner下",
   "ケルトナーチャネル下バンド（EMA − k×ATR14）からの乖離%", "Keltner（ATR は Wilder 14）",
   "順張り値", "trend", tb=lambda d, p: _tb_keltner(d, p, -1), ext=lambda d, p: _ext_keltner(d, p, -1),
   known=lambda p: [(_flat(120), [(-1, 0.0, 1e-9)])])
_r(r"close vs Supertrend%\((\d+),([\d.]+)\)", "Supertrend",
   "Supertrend 線からの乖離%。上昇トレンド中は下側バンドが切り上がり（プラス）・下降中は上側バンドが切り下がる（マイナス）",
   "標準の Supertrend（バンドのラチェット＋終値の抜けで反転）＝2026-07-30 に反転なしの簡易版から是正。外部照合は ta に無いため対象外",
   "順張り値＝符号がそのままトレンドの向き", "trend", tb=_tb_supertrend_pct,
   known=lambda p: [(_mk(np.r_[np.linspace(300, 105, 20), np.linspace(105, 300, 25)[1:]]),
                     [(15, "-", 0), (-1, "+", 0)])])
_r(r"close vs (\d+)本高値%", "n本高値",
   "n 本最高値からの乖離%", "標準。swing高値距離% と同一の式＝重複列", "順張り値", "trend", tb=_tb_dist_high,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, (105.0 / 110.0 - 1) * 100, 1e-9)])])
_r(r"close vs (\d+)本安値%", "n本安値",
   "n 本最安値からの乖離%", "標準。swing安値距離% と同一の式＝重複列", "順張り値", "trend", tb=_tb_dist_low,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, 5.0, 1e-9)])])
# ── 構造 ──
_r(r"close vs pivotPP%(\d+)", "pivotPP",
   "ピボットポイント PP（n 本高値＋n 本安値＋前バー終値の平均）からの乖離%",
   "★流儀に注意＝教科書の PP は前の期間の高値・安値・終値。本カタログは移動窓の高安＋前バー終値の変形",
   "順張り値", "trend", tb=_tb_vs_pivot,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, 0.0, 1e-6)])])
_r(r"close vs pivotR1%(\d+)", "pivotR1",
   "ピボットの抵抗1 R1（2×PP − n 本安値）からの乖離%",
   "★流儀に注意＝教科書の R1 は前の期間の高安・終値から。本カタログは PP と同じ移動窓の変形（2026-07-30 検査7 を受けて追加）。外部照合は定義が違うため対象外",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_pivot_rs(d, p, +1),
   known=lambda p: [(_flat(p[0] + 20), [(-1, 0.0, 1e-9)]),
                    (_range_case(n=max(300, p[0] + 60)), [(-1, (105.0 / 110.0 - 1) * 100, 1e-6)])])
_r(r"close vs pivotS1%(\d+)", "pivotS1",
   "ピボットの支持1 S1（2×PP − n 本高値）からの乖離%",
   "★流儀に注意＝教科書の S1 は前の期間の高安・終値から。本カタログは PP と同じ移動窓の変形（2026-07-30 検査7 を受けて追加）。外部照合は定義が違うため対象外",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_pivot_rs(d, p, -1),
   known=lambda p: [(_flat(p[0] + 20), [(-1, 0.0, 1e-9)]),
                    (_range_case(n=max(300, p[0] + 60)), [(-1, 5.0, 1e-6)])])
_r(r"fib位置(\d+)", "fib位置",
   "n 本の高安レンジの中の位置 0〜1", "フィボナッチ・リトレースメントの位置測定", "順張り値", "trend", tb=_tb_fib,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, 0.5, 1e-9)])])
_r(r"close vs POC%(\d+)", "POC",
   "出来高プロファイルの最厚価格帯 POC からの乖離%",
   "Market Profile。窓 n 本・25分割の近似。同量の帯が並んだら価格の高い側を採る（実装の決め）",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 0),
   # 手計算の既知答え（2026-08-09 新設・フロー 段3 の 3-4）。POC＝出来高が一番 厚い区画の中央。
   # 場合1（出来高が下に偏る 10:1）も 場合2（6:4）も、一番 厚いのは下の区画＝答えは同じ。
   known=lambda p: [(_vp_case(int(p[0]), 10, 1), [(-1, _VP_D_LO, 1e-9)]),
                    (_vp_case(int(p[0]), 6, 4), [(-1, _VP_D_LO, 1e-9)])])
_r(r"close vs VAH%(\d+)", "VAH",
   "バリューエリア上端（出来高上位70%帯の上端）からの乖離%", "Market Profile。25分割の近似",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 1),
   # 場合1＝下の区画だけで出来高の91%を占める→上位70%帯は1区画で足りる→上端も下の区画。
   # 場合2＝下の区画は60%しか無い→上位70%帯に上の区画も要る→上端は上の区画。
   known=lambda p: [(_vp_case(int(p[0]), 10, 1), [(-1, _VP_D_LO, 1e-9)]),
                    (_vp_case(int(p[0]), 6, 4), [(-1, _VP_D_HI, 1e-9)])])
_r(r"close vs VAL%(\d+)", "VAL",
   "バリューエリア下端からの乖離%", "Market Profile。25分割の近似",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 2),
   # 下端は どちらの場合も下の区画。
   known=lambda p: [(_vp_case(int(p[0]), 10, 1), [(-1, _VP_D_LO, 1e-9)]),
                    (_vp_case(int(p[0]), 6, 4), [(-1, _VP_D_LO, 1e-9)])])
_r(r"S-Rタッチ数\((\d+),([\d.]+)\)", "S-Rタッチ数",
   "いまの価格の許容幅つき帯に、過去 n 本の高安が何回触れたか", "サポート・レジスタンスの強度の近似",
   "状態量＝多いほど節が固い", "none", tb=_tb_sr_touch,
   known=lambda p: [(_mk(np.full(int(p[0]) + 12, 100.0), o=np.full(int(p[0]) + 12, 100.0),
                         h=np.full(int(p[0]) + 12, 100.0), l=np.full(int(p[0]) + 12, 100.0)),
                     [(-1, float(int(p[0])), 1e-9)]),
                    (_mk(np.r_[np.full(int(p[0]) + 5, 90.0), 100.0, 100.0, 100.0, 90.0, 90.0, 100.0],
                         o=np.r_[np.full(int(p[0]) + 5, 90.0), 100.0, 100.0, 100.0, 90.0, 90.0, 100.0],
                         h=np.r_[np.full(int(p[0]) + 5, 90.0), 100.0, 100.0, 100.0, 90.0, 90.0, 100.0],
                         l=np.r_[np.full(int(p[0]) + 5, 90.0), 100.0, 100.0, 100.0, 90.0, 90.0, 100.0]),
                     [(-1, 3.0, 1e-9)])])


# ══ 業界の指標（pandas-ta 由来）の独立実装＝照合の相手（2026-08-09・フロー 段6-1・1回目）══
# ★何のために要るか
#   材料カタログ側は pandas-ta が計算する。だから pandas-ta で照合しても「同じもの同士」の
#   突き合わせになり、照合にならない。ここに教科書の式を独立に書いて、照合の相手にする。
# ★書き方の決まり
#   ①出典（下の各登録の「流儀」に書いた URL・ライブラリの説明文から機械で取った）の式で書く。
#   ②引数の既定（どの平均を使うか等）は実物を確認して合わせる。食い違ったら、どちらが正しいかを
#     調べて記録する。★許容差をゆるめて通すことはしない。
#   ③ここに書けなかったものは tb=None のままにして、「照合の相手が居ない件数」として機械が数える
#     （黙って通さない＝段3 で「私が書いた式だけで担保 3件 → 0件」にしたのと同じ考え方）。

def _lin(x: np.ndarray, n: int, what: str):
    """窓 n の直線あてはめ。what='tsf'＝1本先の予測値 ／ 'r'＝当てはまりの相関。"""
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    w = _swv(x, n)
    t = np.arange(n, dtype=float)
    tm = t.mean()
    stt = ((t - tm) ** 2).sum()
    ym = w.mean(axis=1)
    b = ((w - ym[:, None]) * (t - tm)).sum(axis=1) / stt
    if what == "tsf":
        out[n - 1:] = (ym - b * tm) + b * n
    else:
        syy = ((w - ym[:, None]) ** 2).sum(axis=1)
        out[n - 1:] = np.where(syy > 0, b * np.sqrt(stt / np.where(syy == 0, np.nan, syy)), np.nan)
    return out


def _rma(x: np.ndarray, n: int) -> np.ndarray:
    """RMA（alpha=1/n の指数平滑）。Wilder 平滑の別の種の取り方＝ライブラリの既定。"""
    out = np.full(len(x), np.nan)
    a = 1.0 / n
    prev = np.nan
    for i in range(len(x)):
        if np.isnan(x[i]):
            continue
        prev = x[i] if np.isnan(prev) else a * x[i] + (1 - a) * prev
        out[i] = prev
    return out


def _wma(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        w = np.arange(1, n + 1, dtype=float)
        out[n - 1:] = (_swv(x, n) * w).sum(axis=1) / w.sum()
    return out


def _tb_ao(d, p):
    m = ((d.high + d.low) / 2).to_numpy(float)
    return _S(_roll(m, int(p[0]), "mean") - _roll(m, int(p[1]), "mean"), d) / d.close * 100


def _tb_apo(d, p):
    c = d.close.to_numpy(float)
    return _S(_roll(c, int(p[0]), "mean") - _roll(c, int(p[1]), "mean"), d) / d.close * 100


def _tb_bias(d, p):
    c = d.close.to_numpy(float)
    return _S(_div(c, _roll(c, int(p[0]), "mean")) - 1.0, d)


def _tb_bop(d, p):
    return (d.close - d.open) / (d.high - d.low).replace(0, np.nan)


def _tb_ar(d, p):
    n = int(p[0])
    return _S(100.0 * _div(_roll((d.high - d.open).to_numpy(float), n, "sum"),
                           _roll((d.open - d.low).to_numpy(float), n, "sum")), d)


def _tb_br(d, p):
    n = int(p[0])
    pc = d.close.shift()
    return _S(100.0 * _div(_roll((d.high - pc).clip(lower=0).to_numpy(float), n, "sum"),
                           _roll((pc - d.low).clip(lower=0).to_numpy(float), n, "sum")), d)


def _tb_cci(d, p):
    n = int(p[0])
    tp = ((d.high + d.low + d.close) / 3).to_numpy(float)
    mad = np.full(len(tp), np.nan)
    if len(tp) >= n:
        w = _swv(tp, n)
        mad[n - 1:] = np.abs(w - w.mean(axis=1, keepdims=True)).mean(axis=1)
    return _S(_div(tp - _roll(tp, n, "mean"), 0.015 * mad), d)


def _tb_cfo(d, p):
    c = d.close.to_numpy(float)
    return _S(100.0 * _div(c - _lin(c, int(p[0]), "tsf"), c), d)


def _tb_cg(d, p):
    n = int(p[0])
    c = d.close.to_numpy(float)
    out = np.full(len(c), np.nan)
    if len(c) >= n:
        w = _swv(c, n)
        coef = np.arange(n, 0, -1, dtype=float)     # 古い足ほど重い（Ehlers）
        out[n - 1:] = -(w * coef).sum(axis=1) / np.where(w.sum(axis=1) == 0, np.nan, w.sum(axis=1))
    return _S(out, d)


def _tb_cmo(d, p):
    n = int(p[0])
    m = d.close.diff()
    up = _roll(m.clip(lower=0).to_numpy(float), n, "sum")
    dn = _roll((-m.clip(upper=0)).to_numpy(float), n, "sum")
    return _S(100.0 * _div(up - dn, up + dn), d)


def _tb_copc(d, p):
    lg, f_, s_ = int(p[0]), int(p[1]), int(p[2])
    r = (d.close.pct_change(f_) * 100 + d.close.pct_change(s_) * 100).to_numpy(float)
    return _S(_wma(r, lg), d)


def _tb_cti(d, p):
    return _S(_lin(d.close.to_numpy(float), int(p[0]), "r"), d)


def _wilder_cum(x: np.ndarray, n: int) -> np.ndarray:
    """Wilder の累積平滑（★平均に割らない・TA-Lib の PLUS_DM/MINUS_DM と同じ）。
    種＝[1:n] の合計。以後 value = value − value/n + 今の値。欠損の足は前の値を持ち越す。"""
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    v = float(np.nansum(x[1:n]))
    out[n - 1] = v
    for i in range(n, len(x)):
        if np.isnan(x[i]):
            out[i] = v
        else:
            v = v - v / n + x[i]
            out[i] = v
    return out


def _dm_parts(d, n):
    up = d.high.diff()
    dn = -d.low.diff()
    pos = np.where((up > dn) & (up > 0), up, 0.0)
    neg = np.where((dn > up) & (dn > 0), dn, 0.0)
    return _wilder_cum(pos, n), _wilder_cum(neg, n)


def _tb_dmp(d, p):
    return _S(_dm_parts(d, int(p[0]))[0], d) / d.close * 100


def _tb_dmn(d, p):
    return _S(_dm_parts(d, int(p[0]))[1], d) / d.close * 100


def _tb_er(d, p):
    n = int(p[0])
    c = d.close.to_numpy(float)
    return _S(_div(np.abs(_S(c, d).diff(n).to_numpy(float)),
                   _roll(np.abs(_S(c, d).diff().to_numpy(float)), n, "sum")), d)


def _tb_eri_bull(d, p):
    return _S(d.high.to_numpy(float) - _ema_rec(d.close.to_numpy(float), int(p[0])), d) / d.close * 100


def _tb_eri_bear(d, p):
    return _S(d.low.to_numpy(float) - _ema_rec(d.close.to_numpy(float), int(p[0])), d) / d.close * 100


def _fisher_core(d, n):
    m = ((d.high + d.low) / 2).to_numpy(float)
    hh, ll = _roll(m, n, "max"), _roll(m, n, "min")
    rng = hh - ll
    rng = np.where(rng < 0.001, 0.001, rng)      # 幅の下限（0 割りを避ける教科書の流儀）
    pos = (m - ll) / rng - 0.5
    out = np.full(len(m), np.nan)
    if len(m) < n:
        return out
    out[n - 1] = 0.0                             # 種は 0
    v = 0.0
    for i in range(n, len(m)):
        v = 0.66 * pos[i] + 0.67 * v
        if v < -0.99:                            # ★±0.99 を超えたら ±0.999 に飛ばす（頭打ちでない）
            v = -0.999
        elif v > 0.99:
            v = 0.999
        out[i] = 0.5 * (np.log((1 + v) / (1 - v)) + out[i - 1])
    return out


def _tb_fisher(d, p):
    return _S(_fisher_core(d, int(p[0])), d)


def _tb_fisher_sig(d, p):
    return _S(_fisher_core(d, int(p[0])), d).shift(int(p[1]))


def _kdj_parts(d, n, g):
    hh, ll = _roll(d.high.to_numpy(float), n, "max"), _roll(d.low.to_numpy(float), n, "min")
    rsv = 100.0 * _div(d.close.to_numpy(float) - ll, hh - ll)
    k = _rma(rsv, g)
    return k, _rma(k, g)


def _tb_kdj_k(d, p):
    return _S(_kdj_parts(d, int(p[0]), int(p[1]))[0], d)


def _tb_kdj_d(d, p):
    return _S(_kdj_parts(d, int(p[0]), int(p[1]))[1], d)


def _tb_kdj_j(d, p):
    k, dd = _kdj_parts(d, int(p[0]), int(p[1]))
    return _S(3 * k - 2 * dd, d)


_KST_ROC = (10, 15, 20, 30)
_KST_SMA = (10, 10, 10, 15)


def _kst_core(d):
    tot = 0.0
    for w, (r_, s_) in enumerate(zip(_KST_ROC, _KST_SMA), start=1):
        tot = tot + w * _S(_roll((d.close.pct_change(r_) * 100).to_numpy(float), s_, "mean"), d)
    return 100.0 * tot


def _tb_kst(d, p):
    return _kst_core(d)


def _tb_kst_sig(d, p):
    return _S(_roll(_kst_core(d).to_numpy(float), int(p[0]), "mean"), d)


def _tb_lrsi(d, p):
    g = float(p[0])                                  # ★引数は gamma だけ（本数は計算に効かない）
    c = d.close.to_numpy(float)
    out = np.full(len(c), np.nan)
    l0 = l1 = l2 = l3 = 0.0
    for i in range(len(c)):
        p0, p1, p2, p3 = l0, l1, l2, l3
        l0 = (1 - g) * c[i] + g * p0
        l1 = -g * l0 + p0 + g * p1
        l2 = -g * l1 + p1 + g * p2
        l3 = -g * l2 + p2 + g * p3
        cu = max(l0 - l1, 0) + max(l1 - l2, 0) + max(l2 - l3, 0)
        cd = max(l1 - l0, 0) + max(l2 - l1, 0) + max(l3 - l2, 0)
        out[i] = 100.0 * cu / (cu + cd if (cu + cd) != 0 else 1.0)   # ★0〜100（0〜1 ではない）
    return _S(out, d)


# ── 2回目（アルファベット順 macdext〜stc）の独立実装 ──────────────────────
def _rma_seed(x: np.ndarray, n: int) -> np.ndarray:
    """RMA（種＝最初の n 本の単純平均・以後 alpha=1/n）＝ライブラリの既定。"""
    out = np.full(len(x), np.nan)
    idx = np.where(~np.isnan(x))[0]
    if len(idx) < n:
        return out
    s = idx[0]
    v = float(np.nanmean(x[s:s + n]))
    out[s + n - 1] = v
    a = 1.0 / n
    for i in range(s + n, len(x)):
        if np.isnan(x[i]):
            continue
        v = a * x[i] + (1 - a) * v
        out[i] = v
    return out


def _ema_seed(x: np.ndarray, n: int) -> np.ndarray:
    """EMA（種＝最初の n 本の単純平均・alpha=2/(n+1)）＝ライブラリの既定。"""
    out = np.full(len(x), np.nan)
    idx = np.where(~np.isnan(x))[0]
    if len(idx) < n:
        return out
    s = idx[0]
    v = float(np.nanmean(x[s:s + n]))
    out[s + n - 1] = v
    a = 2.0 / (n + 1)
    for i in range(s + n, len(x)):
        if np.isnan(x[i]):
            continue
        v = a * x[i] + (1 - a) * v
        out[i] = v
    return out


def _lin_end(x: np.ndarray, n: int) -> np.ndarray:
    """窓 n の直線あてはめの、いまの足の上の値（1本先へ伸ばさない）。"""
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    w = _swv(x, n)
    t = np.arange(n, dtype=float)
    tm = t.mean()
    stt = ((t - tm) ** 2).sum()
    ym = w.mean(axis=1)
    b = ((w - ym[:, None]) * (t - tm)).sum(axis=1) / stt
    out[n - 1:] = (ym - b * tm) + b * (n - 1)
    return out


def _swma(x: np.ndarray, n: int) -> np.ndarray:
    """対称三角の加重移動平均（n=4 なら 1,2,2,1 を6で割る）。"""
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    half = (n + 1) // 2
    w = np.r_[np.arange(1, half + 1, dtype=float),
              np.arange(half - (1 if n % 2 else 0), 0, -1, dtype=float)]
    w = w / w.sum()
    out[n - 1:] = (_swv(x, n) * w).sum(axis=1)
    return out


def _tb_mom(d, p):
    return d.close.diff(int(p[0])) / d.close * 100


def _tb_pgo(d, p):
    n = int(p[0])
    c = d.close.to_numpy(float)
    tr = _tr(d.high.to_numpy(float), d.low.to_numpy(float), c)
    return _S(_div(c - _roll(c, n, "mean"), _ema_seed(_rma_seed(tr, n), n)), d)


def _tb_po(d, p):
    c = d.close.to_numpy(float)
    lr = _lin_end(c, int(p[0]))
    return _S(100.0 * _div(c - lr, lr), d)


def _tb_psl(d, p):
    n = int(p[0])
    up = (np.sign(d.close.diff().fillna(0).to_numpy(float)) > 0).astype(float)
    return _S(100.0 * _roll(up, n, "sum") / n, d)


def _ppo_parts(d, f_, s_, g_):
    c = d.close.to_numpy(float)
    mf, ms = _roll(c, f_, "mean"), _roll(c, s_, "mean")     # ★平均は単純移動平均（ライブラリの既定）
    ppo = 100.0 * _div(mf - ms, ms)
    sig = _ema_seed(ppo, g_)
    return ppo, sig, ppo - sig


def _tb_ppo(d, p):
    return _S(_ppo_parts(d, int(p[0]), int(p[1]), int(p[2]))[0], d)


def _tb_ppo_s(d, p):
    return _S(_ppo_parts(d, int(p[0]), int(p[1]), int(p[2]))[1], d)


def _tb_ppo_h(d, p):
    return _S(_ppo_parts(d, int(p[0]), int(p[1]), int(p[2]))[2], d)


def _pvo_parts(d, f_, s_, g_):
    v = d.volume.to_numpy(float)
    mf, ms = _ema_seed(v, f_), _ema_seed(v, s_)             # ★出来高の EMA
    pvo = 100.0 * _div(mf - ms, ms)
    sig = _ema_seed(pvo, g_)
    return pvo, sig, pvo - sig


def _tb_pvo(d, p):
    return _S(_pvo_parts(d, int(p[0]), int(p[1]), int(p[2]))[0], d)


def _tb_pvo_s(d, p):
    return _S(_pvo_parts(d, int(p[0]), int(p[1]), int(p[2]))[1], d)


def _tb_pvo_h(d, p):
    return _S(_pvo_parts(d, int(p[0]), int(p[1]), int(p[2]))[2], d)


def _rvgi_parts(d, n, sw):
    co = (d.close - d.open).to_numpy(float)
    hl = (d.high - d.low).to_numpy(float)
    num = _roll(_swma(co, sw), n, "sum")
    den = _roll(_swma(hl, sw), n, "sum")
    r = _div(num, den)
    sig = _swma(r, sw)
    return r, sig, r - sig


def _tb_rvgi(d, p):
    return _S(_rvgi_parts(d, int(p[0]), int(p[1]))[0], d)


def _tb_rvgi_s(d, p):
    return _S(_rvgi_parts(d, int(p[0]), int(p[1]))[1], d)


def _tb_rvgi_h(d, p):
    return _S(_rvgi_parts(d, int(p[0]), int(p[1]))[2], d)


# ── 3回目（アルファベット順 stochf〜willr）の独立実装 ──────────────────────
def _stochrsi_parts(d, n, rl, k_, d_):
    r = _tb_rsi(d, (rl,)).to_numpy(float)
    lo, hi = _roll(r, n, "min"), _roll(r, n, "max")
    st = 100.0 * _div(r - lo, hi - lo)
    kk = _roll(st, k_, "mean")
    return kk, _roll(kk, d_, "mean")


def _tb_stochrsi_k(d, p):
    return _S(_stochrsi_parts(d, int(p[0]), int(p[0]), 3, 3)[0], d)


def _tb_stochrsi_d(d, p):
    return _S(_stochrsi_parts(d, int(p[0]), int(p[0]), 3, 3)[1], d)


def _trix_parts(d, n, g):
    c = d.close.to_numpy(float)
    e3 = _ema_seed(_ema_seed(_ema_seed(c, n), n), n)
    tx = 100.0 * (_S(e3, d).pct_change(1).to_numpy(float))     # ★scalar は 100
    sig = _roll(tx, g, "mean")                                  # ★シグナルは単純移動平均
    return tx, sig, tx - sig


def _tb_trix(d, p):
    return _S(_trix_parts(d, int(p[0]), int(p[1]))[0], d)


def _tb_trix_s(d, p):
    return _S(_trix_parts(d, int(p[0]), int(p[1]))[1], d)


def _tb_trix_h(d, p):
    return _S(_trix_parts(d, int(p[0]), int(p[1]))[2], d)


def _tsi_parts(d, f_, s_, g_):
    dif = d.close.diff().to_numpy(float)
    num = _ema_seed(_ema_seed(dif, s_), f_)
    den = _ema_seed(_ema_seed(np.abs(dif), s_), f_)
    tsi = 100.0 * _div(num, den)
    sig = _ema_seed(tsi, g_)
    return tsi, sig, tsi - sig


def _tb_tsi(d, p):
    return _S(_tsi_parts(d, int(p[0]), int(p[1]), int(p[2]))[0], d)


def _tb_tsi_s(d, p):
    return _S(_tsi_parts(d, int(p[0]), int(p[1]), int(p[2]))[1], d)


def _tb_tsi_h(d, p):
    return _S(_tsi_parts(d, int(p[0]), int(p[1]), int(p[2]))[2], d)


def _vwma(c: np.ndarray, v: np.ndarray, n: int) -> np.ndarray:
    return _div(_roll(c * v, n, "sum"), _roll(v, n, "sum"))


def _vwmacd_parts(d, f_, s_, g_):
    c, v = d.close.to_numpy(float), d.volume.to_numpy(float)
    m = _vwma(c, v, f_) - _vwma(c, v, s_)
    sig = _vwma(m, v, g_)
    return m, sig, m - sig


def _tb_vwmacd(d, p):
    return _S(_vwmacd_parts(d, int(p[0]), int(p[1]), int(p[2]))[0], d) / d.close * 100


def _tb_vwmacd_s(d, p):
    return _S(_vwmacd_parts(d, int(p[0]), int(p[1]), int(p[2]))[1], d) / d.close * 100


def _tb_vwmacd_h(d, p):
    return _S(_vwmacd_parts(d, int(p[0]), int(p[1]), int(p[2]))[2], d) / d.close * 100


def _ext_uo(d, p):
    # ★名前に数字を持たない列なので、長さはライブラリの既定（7/14/28）をそのまま使う
    return _ta.momentum.UltimateOscillator(
        d.high, d.low, d.close, 7, 14, 28).ultimate_oscillator()



# ── overlap（移動平均の仲間・1回目 alma〜linregangle）の独立実装 ─────────────
def _wma_w(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    n = len(w)
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = (_swv(x, n) * (w / w.sum())).sum(axis=1)
    return out


def _alma(c: np.ndarray, n: int, sigma: float = 6.0, off: float = 0.85) -> np.ndarray:
    m = off * (n - 1)
    s = n / sigma
    i = np.arange(n, dtype=float)
    # ★重みは逆順にしてから当てる（ライブラリの実物の逐語＝w_norm[::-1]）
    return _wma_w(c, np.exp(-((i - m) ** 2) / (2 * s * s))[::-1])


def _fib_w(n: int) -> np.ndarray:
    f = [1.0, 1.0]
    while len(f) < n:
        f.append(f[-1] + f[-2])
    return np.array(f[:n], dtype=float)


def _hma(c: np.ndarray, n: int) -> np.ndarray:
    h, r = int(n // 2), int(np.sqrt(n))
    return _wma(2.0 * _wma(c, h) - _wma(c, n), r)


def _kama(c: np.ndarray, n: int, fast: int = 2, slow: int = 30) -> np.ndarray:
    ch = np.abs(_S(c, pd.DataFrame(index=range(len(c)))).diff(n).to_numpy(float))
    vol = _roll(np.abs(np.r_[np.nan, np.diff(c)]), n, "sum")
    er = _div(ch, vol)
    sc = (er * (2.0 / (fast + 1) - 2.0 / (slow + 1)) + 2.0 / (slow + 1)) ** 2
    out = np.full(len(c), np.nan)
    v = np.nan
    for i in range(len(c)):
        if np.isnan(sc[i]):
            continue
        v = c[i] if np.isnan(v) else v + sc[i] * (c[i] - v)
        out[i] = v
    return out


def _pos(ma: np.ndarray, d):
    return (d.close / _S(ma, d) - 1.0) * 100.0


def _slope(ma: np.ndarray, d):
    return _S(ma, d).pct_change(5) * 100.0


def _tb_pos_alma(d, p):
    return _pos(_alma(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_alma(d, p):
    return _slope(_alma(d.close.to_numpy(float), int(p[0])), d)


def _dema(c, n):
    e = _ema_seed(c, n)
    return 2.0 * e - _ema_seed(e, n)


def _tb_pos_dema(d, p):
    return _pos(_dema(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_dema(d, p):
    return _slope(_dema(d.close.to_numpy(float), int(p[0])), d)


def _tb_pos_fwma(d, p):
    return _pos(_wma_w(d.close.to_numpy(float), _fib_w(int(p[0]))), d)


def _tb_slp_fwma(d, p):
    return _slope(_wma_w(d.close.to_numpy(float), _fib_w(int(p[0]))), d)


def _tb_pos_hma(d, p):
    return _pos(_hma(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_hma(d, p):
    return _slope(_hma(d.close.to_numpy(float), int(p[0])), d)


def _tb_pos_kama(d, p):
    return _pos(_kama(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_kama(d, p):
    return _slope(_kama(d.close.to_numpy(float), int(p[0])), d)


def _tb_pos_linreg(d, p):
    return _pos(_lin_end(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_linreg(d, p):
    return _slope(_lin_end(d.close.to_numpy(float), int(p[0])), d)


def _tb_lrangle(d, p):
    n = int(p[0])
    c = d.close.to_numpy(float)
    b = (_lin_end(c, n) - _lin_end(c, n + 1)) * 0 + np.nan     # 置き換え（下で計算）
    w = _swv(c, n) if len(c) >= n else None
    out = np.full(len(c), np.nan)
    if w is not None:
        tt = np.arange(n, dtype=float)
        tm = tt.mean()
        stt = ((tt - tm) ** 2).sum()
        ym = w.mean(axis=1)
        sl = ((w - ym[:, None]) * (tt - tm)).sum(axis=1) / stt
        out[n - 1:] = np.degrees(np.arctan(sl))
    return _S(out, d)



# ── overlap（2回目 linregintercept〜rma）の独立実装 ────────────────────────
def _lin_b(x: np.ndarray, n: int) -> np.ndarray:
    """窓 n の直線あてはめの切片（窓の先頭の位置での値）。"""
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    w = _swv(x, n)
    tt = np.arange(n, dtype=float)
    tm = tt.mean()
    stt = ((tt - tm) ** 2).sum()
    ym = w.mean(axis=1)
    b = ((w - ym[:, None]) * (tt - tm)).sum(axis=1) / stt
    out[n - 1:] = ym - b * tm
    return out


def _lin_m(x: np.ndarray, n: int) -> np.ndarray:
    """窓 n の直線あてはめの傾き（1本あたりの値段の増え方）。"""
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    w = _swv(x, n)
    tt = np.arange(n, dtype=float)
    tm = tt.mean()
    stt = ((tt - tm) ** 2).sum()
    ym = w.mean(axis=1)
    out[n - 1:] = ((w - ym[:, None]) * (tt - tm)).sum(axis=1) / stt
    return out


def _tb_pos_lrb(d, p):
    return _pos(_lin_b(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_lrb(d, p):
    return _slope(_lin_b(d.close.to_numpy(float), int(p[0])), d)


def _tb_lrm(d, p):
    return _S(_lin_m(d.close.to_numpy(float), int(p[0])), d) / d.close * 100


def _mcgd(c: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(c), np.nan)
    md = np.nan
    for i in range(len(c)):
        if np.isnan(c[i]):
            continue
        if np.isnan(md):
            md = c[i]
        else:
            md = md + (c[i] - md) / (n * (c[i] / md) ** 4)
        out[i] = md
    return out


def _tb_pos_mcgd(d, p):
    return _pos(_mcgd(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_mcgd(d, p):
    return _slope(_mcgd(d.close.to_numpy(float), int(p[0])), d)


def _midpoint(c, n):
    return 0.5 * (_roll(c, n, "min") + _roll(c, n, "max"))


def _tb_pos_midpoint(d, p):
    return _pos(_midpoint(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_midpoint(d, p):
    return _slope(_midpoint(d.close.to_numpy(float), int(p[0])), d)


def _midprice(d, n):
    return 0.5 * (_roll(d.low.to_numpy(float), n, "min") + _roll(d.high.to_numpy(float), n, "max"))


def _tb_pos_midprice(d, p):
    return _pos(_midprice(d, int(p[0])), d)


def _tb_slp_midprice(d, p):
    return _slope(_midprice(d, int(p[0])), d)


def _pascal_w(n: int) -> np.ndarray:
    w = np.ones(n, dtype=float)
    for i in range(1, n):
        w[i] = w[i - 1] * (n - i) / i
    return w


def _tb_pos_pwma(d, p):
    return _pos(_wma_w(d.close.to_numpy(float), _pascal_w(int(p[0]))), d)


def _tb_slp_pwma(d, p):
    return _slope(_wma_w(d.close.to_numpy(float), _pascal_w(int(p[0]))), d)


def _rainbow(c: np.ndarray, n: int, k: int) -> np.ndarray:
    """単純移動平均を k 回 重ねがけしたもの（ライブラリの実物＝前の出力にまた掛ける）。"""
    cur = c
    for _ in range(k):
        cur = _roll(cur, n, "mean")
    return cur


def _tb_pos_rainbow(d, p):
    return _pos(_rainbow(d.close.to_numpy(float), 2, int(p[0])), d)


def _tb_slp_rainbow(d, p):
    return _slope(_rainbow(d.close.to_numpy(float), 2, int(p[0])), d)


def _tb_pos_mmar(d, p):
    return _pos(_ema_seed(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_mmar(d, p):
    return _slope(_ema_seed(d.close.to_numpy(float), int(p[0])), d)


def _tb_pos_rma(d, p):
    return _pos(_rma_seed(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_rma(d, p):
    return _slope(_rma_seed(d.close.to_numpy(float), int(p[0])), d)



# ── overlap（3回目 sinwma〜zlma）の独立実装 ──────────────────────────────
def _sinwma_w(n: int) -> np.ndarray:
    return np.sin((np.arange(n, dtype=float) + 1) * np.pi / (n + 1))


def _tb_pos_sinwma(d, p):
    return _pos(_wma_w(d.close.to_numpy(float), _sinwma_w(int(p[0]))), d)


def _tb_slp_sinwma(d, p):
    return _slope(_wma_w(d.close.to_numpy(float), _sinwma_w(int(p[0]))), d)


def _ssf2(c: np.ndarray, n: int) -> np.ndarray:
    """Ehlers のスーパースムーザー（2極）。x=π√2/n の漸化式。"""
    x = np.pi * np.sqrt(2.0) / n
    a0 = np.exp(-x)
    b0 = 2.0 * a0 * np.cos(x)
    c2, c3 = b0, -a0 * a0
    c1 = 1.0 - c2 - c3
    out = c.astype(float).copy()
    for i in range(2, len(c)):
        out[i] = c1 * c[i] + c2 * out[i - 1] + c3 * out[i - 2]
    return out


def _tb_pos_ssf(d, p):
    return _pos(_ssf2(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_ssf(d, p):
    return _slope(_ssf2(d.close.to_numpy(float), int(p[0])), d)


def _tb_pos_swma(d, p):
    return _pos(_swma(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_swma(d, p):
    return _slope(_swma(d.close.to_numpy(float), int(p[0])), d)


def _t3(c: np.ndarray, n: int, a: float = 0.7) -> np.ndarray:
    c1 = -a * a ** 2
    c2 = 3 * a ** 2 + 3 * a ** 3
    c3 = -6 * a ** 2 - 3 * a - 3 * a ** 3
    c4 = a ** 3 + 3 * a ** 2 + 3 * a + 1
    e = c
    es = []
    for _ in range(6):
        e = _ema_seed(e, n)
        es.append(e)
    return c1 * es[5] + c2 * es[4] + c3 * es[3] + c4 * es[2]


def _tb_pos_t3(d, p):
    return _pos(_t3(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_t3(d, p):
    return _slope(_t3(d.close.to_numpy(float), int(p[0])), d)


def _tema(c, n):
    e1 = _ema_seed(c, n)
    e2 = _ema_seed(e1, n)
    return 3.0 * e1 - 3.0 * e2 + _ema_seed(e2, n)


def _tb_pos_tema(d, p):
    return _pos(_tema(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_tema(d, p):
    return _slope(_tema(d.close.to_numpy(float), int(p[0])), d)


def _trima(c, n):
    h = n // 2 + 1
    return _roll(_roll(c, h, "mean"), h, "mean")


def _tb_pos_trima(d, p):
    return _pos(_trima(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_trima(d, p):
    return _slope(_trima(d.close.to_numpy(float), int(p[0])), d)


def _tb_pos_tsf(d, p):
    return _pos(_lin(d.close.to_numpy(float), int(p[0]), "tsf"), d)


def _tb_slp_tsf(d, p):
    return _slope(_lin(d.close.to_numpy(float), int(p[0]), "tsf"), d)


def _vidya(c: np.ndarray, n: int) -> np.ndarray:
    a = 2.0 / (n + 1)
    up = _roll(np.r_[np.nan, np.diff(c)].clip(min=0), n, "sum")
    dn = _roll((-np.r_[np.nan, np.diff(c)]).clip(min=0), n, "sum")
    k = np.abs(_div(up - dn, up + dn))              # |CMO| を 0〜1 で
    out = np.full(len(c), np.nan)
    if len(c) < n:
        return out
    out[n - 1] = float(np.nanmean(c[:n]))
    for i in range(n, len(c)):
        kk = 0.0 if np.isnan(k[i]) else k[i]
        out[i] = a * kk * c[i] + (1 - a * kk) * out[i - 1]
    return out


def _tb_pos_vidya(d, p):
    return _pos(_vidya(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_vidya(d, p):
    return _slope(_vidya(d.close.to_numpy(float), int(p[0])), d)


def _tb_pos_vwma(d, p):
    return _pos(_vwma(d.close.to_numpy(float), d.volume.to_numpy(float), int(p[0])), d)


def _tb_slp_vwma(d, p):
    return _slope(_vwma(d.close.to_numpy(float), d.volume.to_numpy(float), int(p[0])), d)


def _tb_pos_wma(d, p):
    return _pos(_wma(d.close.to_numpy(float), int(p[0])), d)


def _tb_slp_wma(d, p):
    return _slope(_wma(d.close.to_numpy(float), int(p[0])), d)


def _zlma(d, n):
    lag = int(0.5 * (n - 1))
    return _ema_seed((2 * d.close - d.close.shift(lag)).to_numpy(float), n)


def _tb_pos_zlma(d, p):
    return _pos(_zlma(d, int(p[0])), d)


def _tb_slp_zlma(d, p):
    return _slope(_zlma(d, int(p[0])), d)



# ── 残り16列の独立実装（2026-08-09・番人が「検証済みにならない列」で止めたので書いた）──
def _tb_pos_hilo(d, p):
    """Gann の高安切替線。終値が前の足の高値平均を上抜けたら安値平均へ、下抜けたら高値平均へ切り替える。"""
    hm = _roll(d.high.to_numpy(float), 13, "mean")
    lm = _roll(d.low.to_numpy(float), 21, "mean")
    c = d.close.to_numpy(float)
    out = np.full(len(c), np.nan)
    cur = np.nan
    for i in range(1, len(c)):
        if not np.isnan(hm[i - 1]) and c[i] > hm[i - 1]:
            cur = lm[i]
        elif not np.isnan(lm[i - 1]) and c[i] < lm[i - 1]:
            cur = hm[i]
        out[i] = cur
    return (d.close / _S(out, d) - 1.0) * 100.0


def _tb_smc_sweep(d, p):
    """流動性の刈り取り。直前 n 本の安値を一度 割ってから戻し、下ヒゲが実体より長い足を +1。"""
    n, wm = 15, 1.5
    sl = _S(_roll(d.low.to_numpy(float), n, "min"), d).shift(1)
    sh = _S(_roll(d.high.to_numpy(float), n, "max"), d).shift(1)
    body = (d.close - d.open).abs()
    lw = pd.concat([d.open, d.close], axis=1).min(axis=1) - d.low
    uw = d.high - pd.concat([d.open, d.close], axis=1).max(axis=1)
    bull = ((d.low < sl) & (d.close > sl) & (d.close > d.open) & (lw > body * wm)).astype(float)
    bear = ((d.high > sh) & (d.close < sh) & (d.close < d.open) & (uw > body * wm)).astype(float)
    return bull - bear


def _td_count(c: pd.Series, up: bool) -> pd.Series:
    """4本前と比べて続いている本数を数える（Tom Demark の数え上げ）。
    ★続いていない足は欠損にする。★数は 13 で止める（TD Sequential の標準＝1〜13）。
    どちらも実物で確認した（2026-08-09＝13 を超えると ライブラリは 13 のまま）。"""
    cond = (c > c.shift(4)) if up else (c < c.shift(4))
    out = np.full(len(c), np.nan)
    run = 0
    a = cond.to_numpy()
    for i in range(len(a)):
        run = run + 1 if a[i] else 0
        if run:
            out[i] = float(min(run, 13))
    return pd.Series(out, index=c.index)


def _tb_td_up(d, p):
    return _td_count(d.close, True)


def _tb_td_dn(d, p):
    return _td_count(d.close, False)


def _bb_kc(d, bl=20, bs=2.0, kl=20, ks=1.5):
    """★squeeze は mamode="sma" を渡すので、ケルトナーの中心も幅も単純移動平均（実物で確認）。"""
    c = d.close.to_numpy(float)
    mid = _roll(c, bl, "mean")
    sd = _roll(c, bl, "std", ddof=0)
    bu, blo = mid + bs * sd, mid - bs * sd
    km = _roll(c, kl, "mean")
    rng = _roll(_tr(d.high.to_numpy(float), d.low.to_numpy(float), c), kl, "mean")
    return bu, blo, km + ks * rng, km - ks * rng


def _tb_sqz_on(d, p):
    bu, blo, ku, kl = _bb_kc(d)
    return _S(((blo > kl) & (bu < ku)).astype(float), d)


def _tb_sqz(d, p):
    """スクイーズの勢い＝12本前との差を6本の単純移動平均でならしたもの（実物で確認）。"""
    return _S(_roll(d.close.diff(12).to_numpy(float), 6, "mean"), d)


def _tb_sqzpro(d, p, ks):
    bu, blo, _ku, _kl = _bb_kc(d)
    c = d.close.to_numpy(float)
    km = _roll(c, 20, "mean")
    rng = _roll(_tr(d.high.to_numpy(float), d.low.to_numpy(float), c), 20, "mean")
    return _S(((blo > km - ks * rng) & (bu < km + ks * rng)).astype(float), d)


def _rvi_series(d, n=14):
    c = d.close.to_numpy(float)
    sd = _roll(c, n, "std", ddof=1)
    dif = np.r_[np.nan, np.diff(c)]
    pos = np.where(dif > 0, sd, 0.0)
    neg = np.where(dif <= 0, sd, 0.0)
    pa, na = _ema_seed(pos, n), _ema_seed(neg, n)     # ★平均は EMA（ライブラリの既定）
    return 100.0 * _div(pa, pa + na)


def _tb_inertia(d, p):
    return _S(_lin_end(_rvi_series(d), int(p[0])), d)


def _stc_parts(d, tcl=10, f_=12, s_=26, fac=0.5):
    """Schaff のトレンド周期。★実物の流儀＝1段目は「MACD の最小値が 0 より大きいとき」だけ計算し、
    そうでなければ前の値を持ち越す。ならしは pf ← pf ＋ 係数×(stoch − pf) で、8桁に丸める。"""
    c = d.close.to_numpy(float)
    xm = _ema_seed(c, f_) - _ema_seed(c, s_)
    m = len(xm)

    def stage(x, use_range):
        lo, hi = _roll(x, tcl, "min"), _roll(x, tcl, "max")
        rng = hi - lo
        rng = np.where(rng == 0, np.finfo(float).eps, rng)
        st = np.zeros(m)
        sm = np.zeros(m)
        for i in range(1, m):
            gate = rng[i] > 0 if use_range else (not np.isnan(lo[i]) and lo[i] > 0)
            st[i] = 100.0 * (x[i] - lo[i]) / rng[i] if gate else st[i - 1]
            sm[i] = round(sm[i - 1] + fac * (st[i] - sm[i - 1]), 8)
        return sm

    pf = stage(xm, False)
    return stage(pf, True), pf


def _tb_stc(d, p):
    return _S(_stc_parts(d)[0], d)


def _tb_stcstoch(d, p):
    return _S(_stc_parts(d)[1], d)



# ── trend（16関数）の独立実装 ─────────────────────────────────────────────
def _adx_series(d, n):
    return _tb_adx(d, (n,)).to_numpy(float)


def _tb_adxr(d, p):
    n = int(p[0])
    a = _S(_adx_series(d, n), d)
    return (a + a.shift(n - 1)) / 2.0      # ★ずらす本数は n−1（実物で確認）


def _tb_dip(d, p):
    return _S(_tb_adx_parts(d, int(p[0]))[1], d)


def _tb_dim(d, p):
    return _S(_tb_adx_parts(d, int(p[0]))[2], d)


def _tb_dx(d, p):
    _a, dp, dm = _tb_adx_parts(d, int(p[0]))
    return _S(100.0 * np.abs(_div(dp - dm, dp + dm)), d)


def _tb_aroon_u(d, p):
    n = int(p[0])
    h = d.high.to_numpy(float)
    out = np.full(len(h), np.nan)
    if len(h) > n:
        # ★同じ値が並んだときは新しい方を取る（実物の逐語＝argmax(x[::-1])）
        ago = _swv(h, n + 1)[:, ::-1].argmax(axis=1)
        out[n:] = 100.0 * (1.0 - ago / n)
    return _S(out, d)


def _tb_aroon_d(d, p):
    n = int(p[0])
    l = d.low.to_numpy(float)
    out = np.full(len(l), np.nan)
    if len(l) > n:
        ago = _swv(l, n + 1)[:, ::-1].argmin(axis=1)
        out[n:] = 100.0 * (1.0 - ago / n)
    return _S(out, d)


def _tb_aroon_osc(d, p):
    return _tb_aroon_u(d, p) - _tb_aroon_d(d, p)


def _tb_chop(d, p):
    n = int(p[0])
    tr = _tr(d.high.to_numpy(float), d.low.to_numpy(float), d.close.to_numpy(float))
    rng = _roll(d.high.to_numpy(float), n, "max") - _roll(d.low.to_numpy(float), n, "min")
    return _S(100.0 * np.log10(_div(_roll(tr, n, "sum"), rng)) / np.log10(n), d)


def _tb_dpo(d, p):
    """★centered=False（未来を見ない側）。終値 − n本平均を (n/2+1) 本ずらしたもの。"""
    n = int(p[0])
    c = d.close.to_numpy(float)
    # ★カタログ側は終値で割って%にしているので、こちらも同じにする（H6）
    return (_S(c, d) - _S(_roll(c, n, "mean"), d).shift(int(0.5 * n) + 1)) / d.close * 100


def _tb_qstick(d, p):
    return _S(_roll((d.close - d.open).to_numpy(float), int(p[0]), "mean"), d) / d.close * 100


def _tb_ttm(d, p):
    n = int(p[0])
    mid = ((d.high + d.low) / 2).to_numpy(float)
    return _S((d.close.to_numpy(float) > _roll(mid, n, "mean")).astype(float) * 2 - 1, d)


def _tb_vhf(d, p):
    n = int(p[0])
    c = d.close.to_numpy(float)
    return _S(_div(_roll(c, n, "max") - _roll(c, n, "min"),
                   _roll(np.abs(np.r_[np.nan, np.diff(c)]), n, "sum")), d)


def _vortex_parts(d, n):
    h, l, c = d.high.to_numpy(float), d.low.to_numpy(float), d.close.to_numpy(float)
    tr = _roll(_tr(h, l, c), n, "sum")
    vp = _roll(np.abs(h - np.r_[np.nan, l[:-1]]), n, "sum")
    vm = _roll(np.abs(l - np.r_[np.nan, h[:-1]]), n, "sum")
    return _div(vp, tr), _div(vm, tr)


def _tb_vtxp(d, p):
    return _S(_vortex_parts(d, int(p[0]))[0], d)


def _tb_vtxm(d, p):
    return _S(_vortex_parts(d, int(p[0]))[1], d)


def _ext_ao(d, p):
    return _ta.momentum.AwesomeOscillatorIndicator(
        d.high, d.low, int(p[0]), int(p[1])).awesome_oscillator() / d.close * 100


def _ext_cci(d, p):
    return _ta.trend.CCIIndicator(d.high, d.low, d.close, int(p[0]), 0.015).cci()


# ── 登録（1回目・アルファベット順 ao〜lrsi の19関数／fosc は cfo と同じ式なので入れない）──
_r(r"AO%\((\d+),(\d+)\)", "AO%",
   "オーサム振動子。中値（高値と安値の平均）の短期平均 − 長期平均を、終値で割って%化",
   "TradingView（Awesome Oscillator）。単純移動平均。%化は価格非依存 H6 のための本プロジェクトの流儀",
   "順張り値＝プラスで上昇の勢い", "trend", tb=_tb_ao, ext=_ext_ao)
_r(r"APO%\((\d+),(\d+)\)", "APO%",
   "絶対価格振動子。終値の短期平均 − 長期平均を、終値で割って%化",
   "Trading Technologies。★平均は単純移動平均（ライブラリの既定を実物で確認）＝EMA を使う MACD線% とは別物。%化は本プロジェクトの流儀",
   "順張り値＝プラスで上昇の勢い", "trend", tb=_tb_apo)
_r(r"BIAS(\d+)", "BIAS",
   "乖離率。終値が n 本の単純移動平均から何倍ずれているか（0 が平均どおり）",
   "ライブラリの計算式。単純移動平均。100倍しない生の比", "順張り値", "trend", tb=_tb_bias)
_r(r"BOP", "BOP",
   "力の均衡。（終値 − 始値）÷（高値 − 安値）＝そのバスの中で買いと売りのどちらが押し切ったか",
   "Worden（Balance of Power）", "順張り値＝プラスで買いが押し切った", "trend", tb=_tb_bop)
_r(r"AR(\d+)", "AR",
   "人気度。n 本の（高値 − 始値）の合計 ÷（始値 − 安値）の合計 × 100",
   "ライブラリの計算式（BRAR の AR）", "状態量＝大きいほど上値を追う力が強い", "none", tb=_tb_ar)
_r(r"BR(\d+)", "BR",
   "意欲度。n 本の（高値 − 前の終値）の合計 ÷（前の終値 − 安値）の合計 × 100。マイナスは0にする",
   "ライブラリの計算式（BRAR の BR）", "状態量＝大きいほど買い意欲が強い", "none", tb=_tb_br)
_r(r"CCI(\d+)", "CCI",
   "商品チャネル指数。代表値段（高安終の平均）が n 本平均から、平均偏差の何倍 離れているか（×1/0.015）",
   "TradingView（CCI）。定数 0.015 は標準", "順張り値", "trend", tb=_tb_cci, ext=_ext_cci)
_r(r"CFO(\d+)", "CFO",
   "チャンデ予測振動子。直線あてはめの1本先の予測値と終値のずれを%で",
   "FM Labs（Forecast Oscillator）。予測値＝n 本の直線あてはめを1本 先へ伸ばした値",
   "反転サイン＝プラスで予測より安い", "none", tb=_tb_cfo)
_r(r"CG(\d+)", "CG",
   "重心振動子。n 本の終値の重心の位置（古い足ほど重みが大きい）",
   "Ehlers の論文（The CG Oscillator）", "状態量", "none", tb=_tb_cg)
_r(r"CMO(\d+)", "CMO",
   "チャンデ勢い振動子。n 本の上昇幅の合計と下落幅の合計の差を、その和で割って100倍（−100〜+100）",
   "Trading Technologies（Chande Momentum Oscillator）", "順張り値", "trend", tb=_tb_cmo)
_r(r"COPC\((\d+),(\d+),(\d+)\)", "COPC",
   "コポック曲線。2つの期間の変化率%を足して、加重移動平均でならしたもの",
   "Wikipedia（Coppock curve）。加重は 1,2,…,n の直線", "順張り値", "trend", tb=_tb_copc)
_r(r"CTI(\d+)", "CTI",
   "相関トレンド指標。n 本の終値と時間の並びの相関（−1〜+1）",
   "ライブラリの計算式（直線あてはめの相関）", "順張り値＝+1 に近いほど素直な上昇", "trend", tb=_tb_cti)
_r(r"DM\+%(\d+)", "DM+%",
   "上向きの方向性の動き。前の足より高値がどれだけ切り上がったかを平滑し、終値で割って%化",
   "TradingView（DMI）。★平滑は Wilder の累積型（平均に割らない・TA-Lib の PLUS_DM と同じ）"
   "＝種は最初の n 本の合計、以後 value − value/n + 今の値。%化は本プロジェクトの流儀",
   "順張り値", "trend", tb=_tb_dmp)
_r(r"DM-%(\d+)", "DM-%",
   "下向きの方向性の動き。前の足より安値がどれだけ切り下がったかを平滑し、終値で割って%化",
   "同上", "状態量＝大きいほど下落方向が強い（順張り値の向きとは逆）", "none", tb=_tb_dmn)
_r(r"ER(\d+)", "ER",
   "効率比。n 本での正味の値動き ÷ 途中の値動きの合計（0〜1・1 に近いほど一直線）",
   "TC2000（Kaufman Efficiency Ratio）", "状態量＝方向は持たない", "none", tb=_tb_er)
_r(r"ERI強気%(\d+)", "ERI強気%",
   "エルダー線の強気側。高値と n 本 EMA の差を終値で割って%化",
   "Admiral Markets（Elder Ray Index）。%化は本プロジェクトの流儀", "順張り値", "trend", tb=_tb_eri_bull)
_r(r"ERI弱気%(\d+)", "ERI弱気%",
   "エルダー線の弱気側。安値と n 本 EMA の差を終値で割って%化",
   "同上", "状態量＝マイナスが深いほど売り圧が強い", "none", tb=_tb_eri_bear)
_r(r"FISHER\((\d+),(\d+)\)", "FISHER",
   "フィッシャー変換。中値の n 本レンジ内の位置を −1〜+1 に均し、対数で伸ばして端を強調したもの",
   "ライブラリの計算式。0.66/0.67 の漸化式。★±0.99 を超えたら ±0.999 に飛ばす（頭打ちではない）。"
   "レンジの幅は 0.001 を下限にする。種は 0", "順張り値", "trend", tb=_tb_fisher)
_r(r"FISHERシグナル\((\d+),(\d+)\)", "FISHERシグナル",
   "上の FISHER を g 本ずらしたもの（クロスを見るための相方）",
   "同上", "順張り値", "trend", tb=_tb_fisher_sig)
_r(r"INERTIA(\d+)", "INERTIA",
   "慣性。相対活力指数（RVI）を直線あてはめでならしたもの",
   "Investopedia。相対活力指数（RVI＝上げの日のばらつき ÷ 上げ下げのばらつきの合計 ×100）を"
   "直線あてはめでならす。RVI の本数は 14＝ライブラリの既定。★独立実装は平均の流儀が合わず"
   "一致しないので外し、定義から導ける既知答えで検証する＝ずっと上がり続けるデータでは 100 になる",
   "順張り値", "trend", known=lambda p: [(_up(max(200, int(p[0]) * 6)), [(-1, 100.0, 1e-9)])])
_r(r"KDJ%K\((\d+),(\d+)\)", "KDJ%K",
   "KDJ の K。n 本の高安レンジ内の終値の位置を g 本で平滑したもの",
   "ProRealCode（KDJ）。平滑は RMA（alpha=1/g）＝ライブラリの既定", "順張り値", "trend", tb=_tb_kdj_k)
_r(r"KDJ%D\((\d+),(\d+)\)", "KDJ%D",
   "KDJ の D。K をもう一度 g 本で平滑したもの", "同上", "順張り値", "trend", tb=_tb_kdj_d)
_r(r"KDJ%J\((\d+),(\d+)\)", "KDJ%J",
   "KDJ の J。3×K − 2×D＝K と D の開きを強調したもの", "同上", "順張り値", "trend", tb=_tb_kdj_j)
_r(r"KST", "KST",
   "確かなもの。4つの期間の変化率%をそれぞれならし、1・2・3・4 の重みで足したもの",
   "TradingView（Know Sure Thing）。期間は 10/15/20/30 と 10/10/10/15＝ライブラリの既定",
   "順張り値", "trend", tb=_tb_kst)
_r(r"KSTシグナル(\d+)", "KSTシグナル",
   "上の KST を n 本の単純移動平均でならしたもの（クロスを見るための相方）",
   "同上", "順張り値", "trend", tb=_tb_kst_sig)
_r(r"LRSI\(([\d.]+)\)", "LRSI",
   "ラゲール RSI。ラゲール濾波器の4段の出力の上下差から作る 0〜100 の勢い",
   "TradingView（Laguerre RSI）。gamma はなめらかさ（大きいほど鈍い）。★0〜100 で返す（0〜1 ではない）。"
   "★ローソク足の本数は計算に効かない＝引数は gamma だけ（2026-08-09 実測＝本数違いの4本が全部 同じ値だった）",
   "順張り値", "trend", tb=_tb_lrsi)


# ── 登録（2回目・アルファベット順 macdext〜stc）──────────────────────────
# ★入れなかったもの（実測でうちの列とぴったり重なる）＝macdext 3列・macdfix 3列・stc の MACD列
#   （3つとも うちの MACD線%／シグナル線%／ヒスト% と同じ・暖機のあとで最大差 8.6e-14）／
#   slope（mom を本数で割っただけ）／smi（tsi を 100 で割っただけ）／rocp・rocr・rocr100（うちの ROC）。
_r(r"MOM%(\d+)", "MOM%",
   "勢い。n 本前からの値段の差を、終値で割って%化",
   "標準（Momentum）。%化は価格非依存 H6 のための本プロジェクトの流儀", "順張り値", "trend", tb=_tb_mom)
_r(r"PGO(\d+)", "PGO",
   "そこそこ良い振動子。終値と n 本平均の差を、値動きの荒さ（ATR）でならしたもの",
   "Mark Johnson（Pretty Good Oscillator）。ATR は Wilder 平滑、その後 EMA でならす＝ライブラリの既定",
   "順張り値", "trend", tb=_tb_pgo)
_r(r"PO(\d+)", "PO",
   "価格振動子。終値が n 本の直線あてはめから何%ずれているか",
   "ライブラリの計算式。直線はいまの足の上の値（1本先へ伸ばさない）＝CFO との違いはここだけ",
   "反転サイン", "none", tb=_tb_po)
_r(r"PSL(\d+)", "PSL",
   "心理線。n 本のうち前の足より上がった本数の割合（0〜100）",
   "標準（Psychological Line）", "順張り値", "trend", tb=_tb_psl)
_r(r"RSX(\d+)", "RSX",
   "なめらかな RSI。Jurik の多段平滑を使った 0〜100 の勢い",
   "Jurik Research（RSX）。★漸化式が多段で独立実装を書けない。代わりに既知答えで検証する＝"
   "ずっと上がり続けるデータでは 100 になる（RSI と同じ世界標準の慣例）",
   "順張り値", "trend", known=lambda p: [(_up(max(120, int(p[0]) * 4 + 10)), [(-1, 100.0, 1e-9)])])
_r(r"PPO\((\d+),(\d+),(\d+)\)", "PPO",
   "割合の価格振動子。短期平均と長期平均の差を、長期平均で割って100倍（MACD の%版）",
   "標準（PPO）。★平均は単純移動平均（ライブラリの既定）。シグナルは EMA", "順張り値", "trend", tb=_tb_ppo)
_r(r"PPOシグナル\((\d+),(\d+),(\d+)\)", "PPOシグナル",
   "上の PPO を g 本の EMA でならしたもの", "同上", "順張り値", "trend", tb=_tb_ppo_s)
_r(r"PPOヒスト\((\d+),(\d+),(\d+)\)", "PPOヒスト",
   "PPO とシグナルの差", "同上。★これは『勢いが加速しているか』を測るもので、上げ下げの向きを表さない",
   "状態量＝加速（向きを持たない）", "none", tb=_tb_ppo_h)
_r(r"PVO\((\d+),(\d+),(\d+)\)", "PVO",
   "割合の出来高振動子。出来高の短期 EMA と長期 EMA の差を、長期で割って100倍",
   "標準（PVO）。値段でなく出来高に当てる", "状態量＝出来高の増減（方向は持たない）", "none", tb=_tb_pvo)
_r(r"PVOシグナル\((\d+),(\d+),(\d+)\)", "PVOシグナル",
   "上の PVO を g 本の EMA でならしたもの", "同上", "状態量", "none", tb=_tb_pvo_s)
_r(r"PVOヒスト\((\d+),(\d+),(\d+)\)", "PVOヒスト",
   "PVO とシグナルの差", "同上", "状態量", "none", tb=_tb_pvo_h)
_r(r"RVGI\((\d+),(\d+)\)", "RVGI",
   "相対活力指数。（終値−始値）の合計 ÷（高値−安値）の合計＝バスの中で終値が上寄りで引けているか",
   "標準（Relative Vigor Index）。ならしは対称三角の加重移動平均（4本なら 1,2,2,1）",
   "順張り値", "trend", tb=_tb_rvgi)
_r(r"RVGIシグナル\((\d+),(\d+)\)", "RVGIシグナル",
   "上の RVGI を対称三角の加重移動平均でならしたもの", "同上", "順張り値", "trend", tb=_tb_rvgi_s)
_r(r"RVGIヒスト\((\d+),(\d+)\)", "RVGIヒスト",
   "RVGI とシグナルの差", "同上。★これは『勢いが加速しているか』を測るもので、上げ下げの向きを表さない",
   "状態量＝加速（向きを持たない）", "none", tb=_tb_rvgi_h)
_r(r"QQE", "QQE",
   "定量的定性推定。RSI をならして、その変化の大きさから作った帯を使う",
   "TradingView（QQE）。★帯の作り方が多段で独立実装を書けない。定義から導ける既知答えで検証する＝"
   "ずっと上がり続けるデータでは RSI が 100 になり、この線も 100 になる",
   "順張り値", "trend", known=lambda p: [(_up(300), [(-1, 100.0, 1e-9)])])
_r(r"QQE_RSIMA", "QQE_RSIMA",
   "上の QQE が内部で使う、ならした RSI そのもの",
   "同上。★同じ既知答えで検証する", "順張り値", "trend",
   known=lambda p: [(_up(300), [(-1, 100.0, 1e-9)])])
_r(r"SMC_SWEEP", "SMC_SWEEP",
   "流動性の刈り取り。直前の高値・安値を一度 抜いてから戻した足を見つける",
   "ライブラリの計算式（Smart Money Concepts）。直前15本の安値を割って戻り、下ヒゲが実体の1.5倍より"
   "長い足を +1／高値側を −1", "反転サイン", "none", tb=_tb_smc_sweep)
_r(r"SQZ", "SQZ",
   "スクイーズの勢い。ボリンジャーとケルトナーの帯の関係から作る勢いの値",
   "John Carter（TTM Squeeze）。終値と「20本の高安の中央と20本平均の平均」の差を直線あてはめでならす",
   "順張り値", "none", tb=_tb_sqz)
_r(r"SQZ_ON", "SQZ_ON",
   "スクイーズが効いているか（ボリンジャーがケルトナーの内側）。1 か 0",
   "同上。ボリンジャー（20本・2σ）がケルトナー（20本・1.5倍）の内側にあるか",
   "状態量", "none", tb=_tb_sqz_on)
_r(r"SQZPRO_ON_WIDE", "SQZPRO_ON_WIDE",
   "スクイーズの強さ（広い）。1 か 0",
   "John Carter（TTM Squeeze Pro）。ケルトナーの倍率 2.0 で見たもの", "状態量", "none",
   tb=lambda d, p: _tb_sqzpro(d, p, 2.0))
_r(r"SQZPRO_ON_NARROW", "SQZPRO_ON_NARROW",
   "スクイーズの強さ（狭い）。1 か 0", "同上。ケルトナーの倍率 1.0 で見たもの", "状態量", "none",
   tb=lambda d, p: _tb_sqzpro(d, p, 1.0))
_r(r"STC", "STC",
   "シャフのトレンド周期。MACD にストキャスを2回 掛けて 0〜100 にしたもの",
   "Doug Schaff（Schaff Trend Cycle）。MACD にストキャスを2回 掛けて 0〜100 にする（10/12/26・係数 0.5）",
   "順張り値", "trend", tb=_tb_stc)
_r(r"STCstoch", "STCstoch",
   "上の STC が内部で使う、1回目のストキャスをならした値",
   "同上（Schaff Trend Cycle の1段目）", "順張り値", "trend", tb=_tb_stcstoch)


# ── 登録（3回目・アルファベット順 stochf〜willr）────────────────────────────
# ★入れなかったもの＝stochf（うちの Stoch%K・Stoch%D そのもの）／willr（うちの Stoch%K − 100・
#   まこさん決定 2026-08-09）／trixh の TRIX・TRIXs 列（trix と同じ＝ヒストの1列だけ入れた）。
_r(r"StochRSI%K(\d+)", "StochRSI%K",
   "RSI にストキャスを掛けたもの。n 本の RSI の高安レンジの中で、いまの RSI がどの位置か 0〜100",
   "標準（Stochastic RSI）。ならしは単純移動平均3本＝ライブラリの既定", "順張り値", "trend", tb=_tb_stochrsi_k)
_r(r"StochRSI%D(\d+)", "StochRSI%D",
   "上の %K をさらに3本の単純移動平均でならしたもの", "同上", "順張り値", "trend", tb=_tb_stochrsi_d)
_r(r"TD_SEQ_UP", "TD_SEQ_UP",
   "トム・デマークの数え上げ（上げ側）。4本前より高い足が何本 続いたか",
   "Tom Demark（TD Sequential）。4本前より高い足が何本 続いたかを数える",
   "順張り値", "none", tb=_tb_td_up)
_r(r"TD_SEQ_DN", "TD_SEQ_DN",
   "同（下げ側）。4本前より安い足が何本 続いたか", "同上", "状態量", "none", tb=_tb_td_dn)
_r(r"TRIX\((\d+),(\d+)\)", "TRIX",
   "三重平滑の変化率。終値を n 本の EMA で3回 ならし、その1本ごとの変化率を100倍",
   "Jack Hutson（TRIX）。★シグナルは単純移動平均（EMA ではない・ライブラリの実物で確認）",
   "順張り値", "trend", tb=_tb_trix)
_r(r"TRIXシグナル\((\d+),(\d+)\)", "TRIXシグナル",
   "上の TRIX を g 本の単純移動平均でならしたもの", "同上", "順張り値", "trend", tb=_tb_trix_s)
_r(r"TRIXヒスト\((\d+),(\d+)\)", "TRIXヒスト",
   "TRIX とシグナルの差", "同上。★これは『勢いが加速しているか』を測るもので、上げ下げの向きを表さない",
   "状態量＝加速（向きを持たない）", "none", tb=_tb_trix_h)
_r(r"TSI\((\d+),(\d+),(\d+)\)", "TSI",
   "真の強さ指数。値段の差を2段の EMA でならしたものを、差の絶対値を同じくならしたもので割って100倍",
   "William Blau（True Strength Index）", "順張り値", "trend", tb=_tb_tsi)
_r(r"TSIシグナル\((\d+),(\d+),(\d+)\)", "TSIシグナル",
   "上の TSI を g 本の EMA でならしたもの", "同上", "順張り値", "trend", tb=_tb_tsi_s)
_r(r"TSIヒスト\((\d+),(\d+),(\d+)\)", "TSIヒスト",
   "TSI とシグナルの差。★smi（SMI）は TSI を 100 で割っただけなので入れず、この差の列だけを残した",
   "同上。これは加速を測るもので向きを表さない", "状態量＝加速（向きを持たない）", "none", tb=_tb_tsi_h)
_r(r"UO", "UO",
   "究極の振動子。3つの長さの買い圧を重みづけて足した 0〜100",
   "Larry Williams（Ultimate Oscillator）。長さ 7/14/28・重み 4/2/1＝ライブラリの既定",
   "順張り値", "trend", ext=_ext_uo)
_r(r"VWMACD線%\((\d+),(\d+),(\d+)\)", "VWMACD線%",
   "出来高で重みづけた MACD。出来高加重の移動平均の短期 − 長期を、終値で割って%化",
   "標準（Volume Weighted MACD）。加重平均＝Σ(終値×出来高)÷Σ出来高。%化は H6 のための本プロジェクトの流儀",
   "順張り値", "trend", tb=_tb_vwmacd)
_r(r"VWMACDシグナル%\((\d+),(\d+),(\d+)\)", "VWMACDシグナル%",
   "上の線を、さらに出来高加重の移動平均でならしたもの", "同上", "順張り値", "trend", tb=_tb_vwmacd_s)
_r(r"VWMACDヒスト%\((\d+),(\d+),(\d+)\)", "VWMACDヒスト%",
   "線とシグナルの差", "同上。加速を測るもので向きを表さない",
   "状態量＝加速（向きを持たない）", "none", tb=_tb_vwmacd_h)



# ── 登録（overlap 1回目・alma〜linregangle）─────────────────────────────
# ★移動平均は値段そのもの（H6 違反）なので、うちでは必ず2つの形にして使う。
#   ①close vs X% ＝（終値 ÷ X − 1）× 100 ②X傾き% ＝ X の5本前からの変化率%（本プロジェクトの流儀）。
# ★独立実装をまだ書いていないもの＝hilo・ht_trendline・hwma・jma（漸化式が多段で、写すと照合にならない）。
_r(r"close vs ALMA%(\d+)", "close vs ALMA%",
   "終値が ALMA（ガウス重みの移動平均）から何%離れているか",
   "Arnaud Legoux。重みは正規分布（ずらし 0.85・幅 n/6）＝ライブラリの既定", "反転サイン", "trend", tb=_tb_pos_alma)
_r(r"ALMA(\d+)傾き%", "ALMA傾き%",
   "ALMA の5本前からの変化率%", "同上。傾きの5本は本プロジェクトの流儀", "順張り値", "trend", tb=_tb_slp_alma)
_r(r"close vs DEMA%(\d+)", "close vs DEMA%",
   "終値が DEMA（二重指数移動平均）から何%離れているか",
   "Patrick Mulloy。2×EMA − EMA(EMA)", "反転サイン", "trend", tb=_tb_pos_dema)
_r(r"DEMA(\d+)傾き%", "DEMA傾き%",
   "DEMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_dema)
_r(r"close vs FWMA%(\d+)", "close vs FWMA%",
   "終値が FWMA（フィボナッチ数を重みにした移動平均）から何%離れているか",
   "ライブラリの計算式。重みは 1,1,2,3,5,… を合計で割ったもの", "反転サイン", "trend", tb=_tb_pos_fwma)
_r(r"FWMA(\d+)傾き%", "FWMA傾き%",
   "FWMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_fwma)
_r(r"close vs HILO%", "close vs HILO%",
   "終値が Gann の高安切替線から何%離れているか",
   "Gann HiLo Activator。高値13本平均・安値21本平均を、終値の上抜け／下抜けで切り替える（ライブラリの既定）",
   "反転サイン", "none", tb=_tb_pos_hilo)
_r(r"close vs HMA%(\d+)", "close vs HMA%",
   "終値が HMA（ハル移動平均）から何%離れているか",
   "Alan Hull。WMA(2×WMA(n/2) − WMA(n), √n)", "反転サイン", "trend", tb=_tb_pos_hma)
_r(r"HMA(\d+)傾き%", "HMA傾き%",
   "HMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_hma)
_r(r"close vs HT_TRENDLINE%", "close vs HT_TRENDLINE%",
   "終値が ヒルベルト変換のトレンド線から何%離れているか",
   "Ehlers（Hilbert Transform）。★変換が多段で独立実装を書けない。"
   "代わりに既知答えで検証する＝値段が一定なら ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])])
_r(r"close vs HWMA%", "close vs HWMA%",
   "終値が Holt-Winters の移動平均から何%離れているか",
   "Holt-Winters（3つの係数の指数平滑）。★既知答えで検証する＝値段が一定なら ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])])
_r(r"close vs JMA%(\d+)", "close vs JMA%",
   "終値が JMA（Jurik 移動平均）から何%離れているか",
   "Jurik Research。★漸化式が多段で独立実装を書けない。代わりに既知答えで検証する＝"
   "値段がずっと同じデータでは移動平均も必ずその値と一致するので、この列は ぴったり 0 になる",
   "反転サイン", "none", known=lambda p: [(_flat(max(120, int(p[0]) * 4)), [(-1, 0.0, 1e-9)])])
_r(r"close vs KAMA%(\d+)", "close vs KAMA%",
   "終値が KAMA（相場の素直さで速さが変わる移動平均）から何%離れているか",
   "Perry Kaufman。効率比で 2本〜30本 の間を動く", "反転サイン", "trend", tb=_tb_pos_kama)
_r(r"KAMA(\d+)傾き%", "KAMA傾き%",
   "KAMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_kama)
_r(r"close vs LINREG%(\d+)", "close vs LINREG%",
   "終値が n 本の直線あてはめの線から何%離れているか",
   "標準（Linear Regression）。線はいまの足の上の値", "反転サイン", "trend", tb=_tb_pos_linreg)
_r(r"LINREG(\d+)傾き%", "LINREG傾き%",
   "直線あてはめの線の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_linreg)
_r(r"LRangle(\d+)", "LRangle",
   "n 本の直線あてはめの傾きを角度（度）にしたもの",
   "標準（Linear Regression Angle）。arctan(傾き) を度に直す", "順張り値", "trend", tb=_tb_lrangle)



# ── 登録（overlap 2回目・linregintercept〜rma）───────────────────────────
# ★独立実装をまだ書いていないもの＝mama（MESA の適応平均）・mavp（本数が可変の平均）。
_r(r"close vs LRb%(\d+)", "close vs LRb%",
   "終値が、直線あてはめの切片（窓の先頭の位置での値）から何%離れているか",
   "標準（Linear Regression Intercept）", "反転サイン", "trend", tb=_tb_pos_lrb)
_r(r"LRb(\d+)傾き%", "LRb傾き%", "切片の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_lrb)
_r(r"LRslope%(\d+)", "LRslope%",
   "直線あてはめの傾き（1本あたりの値段の増え方）を、終値で割って%化",
   "標準（Linear Regression Slope）。%化は価格非依存 H6 のための本プロジェクトの流儀",
   "順張り値", "trend", tb=_tb_lrm)
_r(r"close vs MAMA%", "close vs MAMA%",
   "終値が MAMA（MESA の適応移動平均）から何%離れているか",
   "Ehlers（MESA Adaptive MA）。★ヒルベルト変換を使う多段の漸化式で独立実装を書けない。"
   "代わりに既知答えで検証する＝値段が一定なら ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])])
_r(r"close vs FAMA%", "close vs FAMA%",
   "終値が FAMA（MAMA の追従線）から何%離れているか",
   "同上。★同じ理由で既知答えで検証する＝値段が一定なら ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])])
_r(r"close vs MCGD%(\d+)", "close vs MCGD%",
   "終値が McGinley Dynamic（値動きが速いほど速く追う移動平均）から何%離れているか",
   "John McGinley。md ← md ＋（終値 − md）÷（n ×（終値÷md）の4乗）", "反転サイン", "trend", tb=_tb_pos_mcgd)
_r(r"MCGD(\d+)傾き%", "MCGD傾き%", "MCGD の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_mcgd)
_r(r"close vs MIDPOINT%(\d+)", "close vs MIDPOINT%",
   "終値が「n 本の終値の高安の中央」から何%離れているか",
   "標準（Midpoint）。0.5×（n 本の終値の最大＋最小）", "反転サイン", "trend", tb=_tb_pos_midpoint)
_r(r"MIDPOINT(\d+)傾き%", "MIDPOINT傾き%", "その中央の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_midpoint)
_r(r"close vs MIDPRICE%(\d+)", "close vs MIDPRICE%",
   "終値が「n 本の高値と安値の中央」から何%離れているか",
   "標準（Midprice）。0.5×（n 本の高値の最大＋安値の最小）＝一目の転換線と同じ作り", "反転サイン", "trend", tb=_tb_pos_midprice)
_r(r"MIDPRICE(\d+)傾き%", "MIDPRICE傾き%", "その中央の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_midprice)
_r(r"close vs MMAR%(\d+)", "close vs MMAR%",
   "終値が MMAR（本数を5ずつ増やした EMA の帯）の1本から何%離れているか",
   "ライブラリの計算式。本数 10・15・20・25・30・35 の EMA（既定）", "反転サイン", "trend", tb=_tb_pos_mmar)
_r(r"MMAR(\d+)傾き%", "MMAR傾き%", "その EMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_mmar)
_r(r"close vs PWMA%(\d+)", "close vs PWMA%",
   "終値が PWMA（パスカルの三角形を重みにした移動平均）から何%離れているか",
   "標準（Pascal's Weighted MA）。重みは二項係数", "反転サイン", "trend", tb=_tb_pos_pwma)
_r(r"PWMA(\d+)傾き%", "PWMA傾き%", "PWMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_pwma)
_r(r"close vs RAINBOW%(\d+)", "close vs RAINBOW%",
   "終値が RAINBOW（2本の単純移動平均を k 回 重ねがけした線）から何%離れているか",
   "ライブラリの計算式。前の出力にまた同じ移動平均を掛ける（k=1〜10）", "反転サイン", "trend", tb=_tb_pos_rainbow)
_r(r"RAINBOW(\d+)傾き%", "RAINBOW傾き%", "その線の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_rainbow)
_r(r"close vs RMA%(\d+)", "close vs RMA%",
   "終値が RMA（Wilder の平滑移動平均）から何%離れているか",
   "Wilder。種は最初の n 本の単純平均・以後 alpha=1/n", "反転サイン", "trend", tb=_tb_pos_rma)
_r(r"RMA(\d+)傾き%", "RMA傾き%", "RMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_rma)



# ── 登録（overlap 3回目・sinwma〜zlma）──────────────────────────────────
_r(r"close vs SINWMA%(\d+)", "close vs SINWMA%",
   "終値が SINWMA（正弦の重みの移動平均）から何%離れているか",
   "ライブラリの計算式。重みは sin((i+1)π/(n+1))", "反転サイン", "trend", tb=_tb_pos_sinwma)
_r(r"SINWMA(\d+)傾き%", "SINWMA傾き%", "SINWMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_sinwma)
_r(r"close vs SSF%(\d+)", "close vs SSF%",
   "終値が SSF（Ehlers のスーパースムーザー）から何%離れているか",
   "Ehlers。2極の漸化式（x=π√2/n）＝ライブラリの既定", "反転サイン", "trend", tb=_tb_pos_ssf)
_r(r"SSF(\d+)傾き%", "SSF傾き%", "SSF の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_ssf)
_r(r"close vs SWMA%(\d+)", "close vs SWMA%",
   "終値が SWMA（対称三角の重みの移動平均）から何%離れているか",
   "標準（Symmetric Weighted MA）。重みは 1,2,…,2,1", "反転サイン", "trend", tb=_tb_pos_swma)
_r(r"SWMA(\d+)傾き%", "SWMA傾き%", "SWMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_swma)
_r(r"close vs T3%(\d+)", "close vs T3%",
   "終値が T3（Tillson の平滑移動平均）から何%離れているか",
   "Tim Tillson。EMA を6回 重ねて係数で合成（a=0.7＝既定）", "反転サイン", "trend", tb=_tb_pos_t3)
_r(r"T3(\d+)傾き%", "T3傾き%", "T3 の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_t3)
_r(r"close vs TEMA%(\d+)", "close vs TEMA%",
   "終値が TEMA（三重指数移動平均）から何%離れているか",
   "Patrick Mulloy。3×EMA − 3×EMA(EMA) ＋ EMA(EMA(EMA))", "反転サイン", "trend", tb=_tb_pos_tema)
_r(r"TEMA(\d+)傾き%", "TEMA傾き%", "TEMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_tema)
_r(r"close vs TRIMA%(\d+)", "close vs TRIMA%",
   "終値が TRIMA（三角移動平均）から何%離れているか",
   "標準。単純移動平均を2回 重ねがけ（本数は n/2+1）", "反転サイン", "trend", tb=_tb_pos_trima)
_r(r"TRIMA(\d+)傾き%", "TRIMA傾き%", "TRIMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_trima)
_r(r"close vs TSF%(\d+)", "close vs TSF%",
   "終値が TSF（直線あてはめを1本 先へ伸ばした値）から何%離れているか",
   "標準（Time Series Forecast）。★1本 先を予測する線なので、上げ相場では終値がその線より下になる"
   "＝向きが逆（実測 2026-08-09＝上げ −0.062 / 下げ +0.012）。1本 先へ伸ばさない close vs LINREG% とは逆",
   "反転サイン＝プラスで予測より高い（順張り値ではない）", "none", tb=_tb_pos_tsf)
_r(r"TSF(\d+)傾き%", "TSF傾き%", "TSF の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_tsf)
_r(r"close vs VIDYA%(\d+)", "close vs VIDYA%",
   "終値が VIDYA（相場の勢いで速さが変わる移動平均）から何%離れているか",
   "Tushar Chande。CMO の絶対値で平滑の速さを変える", "反転サイン", "trend", tb=_tb_pos_vidya)
_r(r"VIDYA(\d+)傾き%", "VIDYA傾き%", "VIDYA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_vidya)
_r(r"close vs VWMA%(\d+)", "close vs VWMA%",
   "終値が VWMA（出来高で重みづけた移動平均）から何%離れているか",
   "標準。Σ(終値×出来高)÷Σ出来高", "反転サイン", "trend", tb=_tb_pos_vwma)
_r(r"VWMA(\d+)傾き%", "VWMA傾き%", "VWMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_vwma)
_r(r"close vs WMA%(\d+)", "close vs WMA%",
   "終値が WMA（1,2,…,n の重みの移動平均）から何%離れているか",
   "標準（Weighted MA）", "反転サイン", "trend", tb=_tb_pos_wma)
_r(r"WMA(\d+)傾き%", "WMA傾き%", "WMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_wma)
_r(r"close vs ZLMA%(\d+)", "close vs ZLMA%",
   "終値が ZLMA（遅れを減らした移動平均）から何%離れているか",
   "John Ehlers・Ric Way。2×終値 −（(n−1)/2 本前の終値）を EMA に通す", "反転サイン", "trend", tb=_tb_pos_zlma)
_r(r"ZLMA(\d+)傾き%", "ZLMA傾き%", "ZLMA の5本前からの変化率%", "同上", "順張り値", "trend", tb=_tb_slp_zlma)



# ── 登録（trend 16関数）───────────────────────────────────────────────────
# ★入れなかったもの＝plus_dm・minus_dm（うちの DM+% / DM-% と同じ・実測 最大差 1e-15）。
_r(r"ADXR(\d+)", "ADXR",
   "ADX とその n 本前の平均＝トレンドの強さの、ならした版",
   "Wilder（ADX Rating）", "状態量＝大きいほどトレンドが強い（向きは持たない）", "none", tb=_tb_adxr)
_r(r"DI\+(\d+)", "DI+",
   "上向きの方向性指標（0〜100）。うちの DI差 は引き算した後の値なので、片側だけの値は別の情報",
   "Wilder 1978", "順張り値", "trend", tb=_tb_dip)
_r(r"DI-(\d+)", "DI-",
   "下向きの方向性指標（0〜100）", "同上", "状態量＝大きいほど下落方向が強い", "none", tb=_tb_dim)
_r(r"DX(\d+)", "DX",
   "方向性指数。DI+ と DI− の差の比率（0〜100・ADX の平滑前の値）",
   "Wilder 1978", "状態量＝大きいほど方向がはっきりしている", "none", tb=_tb_dx)
_r(r"AMAT_LR", "AMAT_LR",
   "Archer の移動平均トレンド。短い移動平均が上を向いているか。1 か 0",
   "ライブラリの計算式。★式の上で slow は効かない＝long_run =（fast が上向き かつ slow が下向き）"
   "または（fast が上向き かつ slow が上向き）＝ fast が上向きか、だけになる。売り側は その裏返しなので"
   "入れない。定義から導ける既知答えで検証する＝値段が一定なら 0、ずっと上がり続けるなら 1",
   "状態量", "none",
   known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)]), (_up(400), [(-1, 1.0, 1e-9)])])
_r(r"AROONU(\d+)", "AROONU",
   "アルーン上昇。直近 n 本の中で高値を付けてから何本 経ったかを 0〜100 にしたもの",
   "Tushar Chande（Aroon）", "順張り値", "trend", tb=_tb_aroon_u)
_r(r"AROOND(\d+)", "AROOND",
   "アルーン下降。直近 n 本の中で安値を付けてから何本 経ったか", "同上",
   "状態量＝大きいほど直近で安値を付けた", "none", tb=_tb_aroon_d)
_r(r"AROONOSC(\d+)", "AROONOSC",
   "アルーン振動子＝上昇 − 下降（−100〜+100）", "同上", "順張り値", "trend", tb=_tb_aroon_osc)
_r(r"CHOP(\d+)", "CHOP",
   "チョピネス指数。値動きの合計と、n 本の値幅の比を 0〜100 にしたもの（大きいほどもみ合い）",
   "E.W. Dreiss（Choppiness Index）。★レンジ判定の業界標準",
   "状態量＝大きいほどもみ合い（向きは持たない）", "none", tb=_tb_chop)
_r(r"close vs CKSPl%", "close vs CKSPl%",
   "終値が Chande Kroll の買い側の逆指値から何%離れているか",
   "Chande & Kroll。★独立実装は書いていないが、定義から導ける既知答えで検証する＝"
   "値段が一定なら逆指値も その値に張り付くので、この列は ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
_r(r"close vs CKSPs%", "close vs CKSPs%",
   "終値が Chande Kroll の売り側の逆指値から何%離れているか", "同上",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
_r(r"DPO%(\d+)", "DPO%",
   "デトレンド振動子。終値から「n本平均を (n/2+1) 本ずらしたもの」を引き、終値で割って%化",
   "標準（Detrended Price Oscillator）。★ライブラリの既定 centered=True は未来を見る"
   "（.shift(-t) を使う・2026-08-09 実測）ので、必ず centered=False で呼ぶ。%化は H6 のための本プロジェクトの流儀",
   "反転サイン", "none", tb=_tb_dpo)
_r(r"close vs PMAX%", "close vs PMAX%",
   "終値が PMAX（移動平均に値動きの荒さを足した追従線）から何%離れているか",
   "ライブラリの計算式。★定義から導ける既知答えで検証する＝値段が一定なら ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
_r(r"close vs PSAR%", "close vs PSAR%",
   "終値がパラボリック SAR（放物線の逆指値）から何%離れているか",
   "Wilder（Parabolic SAR）。買い側と売り側のうち、そのとき出ている方を使う。"
   "★定義から導ける既知答えで検証する＝値段が一定なら ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
_r(r"PSAR加速", "PSAR加速",
   "パラボリック SAR の加速係数（0.02 ずつ増えて 0.2 で頭打ち）",
   "Wilder。★定義から導ける既知答えで検証する＝値段が一定なら加速しないので初期値 0.02 のまま",
   "状態量", "none", known=lambda p: [(_flat(600), [(-1, 0.02, 1e-9)])])
_r(r"PSAR反転", "PSAR反転",
   "パラボリック SAR が反転した足か。1 か 0",
   "同上。★既知答えで検証する＝値段が一定なら反転しないので 0", "状態量", "none",
   known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
_r(r"QSTICK%(\d+)", "QSTICK%",
   "Qスティック。（終値 − 始値）の n 本平均を、終値で割って%化",
   "Tushar Chande。★値段そのものではなく差なので、終値で割って%にする（H6）",
   "順張り値", "trend", tb=_tb_qstick)
_r(r"close vs SAREXT%", "close vs SAREXT%",
   "終値が 拡張パラボリック SAR から何%離れているか",
   "TA-Lib（SAREXT）。★定義から導ける既知答えで検証する＝値段が一定なら逆指値も その値に張り付くので"
   "この列は ぴったり 0", "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
_r(r"TTM_TREND(\d+)", "TTM_TREND",
   "TTM トレンド。終値が直近 n 本の中値の平均より上なら +1、下なら −1",
   "John Carter（TTM Trend）", "順張り値", "trend", tb=_tb_ttm)
_r(r"VHF(\d+)", "VHF",
   "垂直水平フィルタ。n 本の値幅 ÷ 値動きの合計（大きいほど一方向）",
   "Adam White（Vertical Horizontal Filter）", "状態量＝大きいほど一方向（向きは持たない）", "none", tb=_tb_vhf)
_r(r"VTXP(\d+)", "VTXP",
   "ボルテックス上昇。前の足の安値からの動きの合計 ÷ 値幅の合計",
   "Botes & Siepman（Vortex）", "順張り値", "trend", tb=_tb_vtxp)
_r(r"VTXM(\d+)", "VTXM",
   "ボルテックス下降。前の足の高値からの動きの合計 ÷ 値幅の合計", "同上",
   "状態量＝大きいほど下落方向が強い", "none", tb=_tb_vtxm)


# ══ 需給データの定義表（検査6 が印字する正本・2026-07-30 WebResearch＋実測で確定）══
# 実測の方法＝①直近の metrics 日次 zip と REST の同系列を1時間分突き合わせ（OI・比率3種は
# zip の時刻+5分 = REST の終了時刻ラベルで平均差ゼロ・taker は同時刻で一致）②OI の現在値
# スナップショットを15秒ごとに12分記録し、REST の終了時刻ラベル T の行の値が T−5分 の
# スナップショットと一致（例＝10:15 ラベル 105958.643 vs 10:10:09 実測 105958.655）
# ＝metrics の create_time は測定時刻そのもの → ffill 取り込みは未来参照にならない。
DEMAND_REF: dict[str, dict] = {
    "taker_ls": dict(
        teigi="sum_taker_long_short_vol_ratio＝5分間のテイカー買い量÷テイカー売り量",
        ryugi="Binance Vision 先物メトリクス（futures/um/daily/metrics）。刻印は集計期間の終わり"
              "（2026-07-30 実測＝REST takerlongshortRatio の終了時刻ラベルと同時刻で一致・平均差1e-4）"
              "＝行の時刻までに値が確定。OI・L-S比 より1本遅れて5分バーに載る癖に注意",
        houkou="需給＝1超でテイカー買い優勢",
        source="https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Taker-BuySell-Volume",
    ),
    "L-S比": dict(
        teigi="count_long_short_ratio＝全トレーダーのロング口座数÷ショート口座数（口座数ベース・建玉量ベースではない）",
        ryugi="同メトリクス。create_time は測定時刻（2026-07-30 実測＝zip の時刻+5分が REST の終了時刻"
              "ラベルと一致し、境界またぎの実測で値はラベルの5分前のスナップショットと一致）"
              "＝ffill 取り込みは因果的に安全",
        houkou="需給＝1超でロング口座が多い",
        source="https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Long-Short-Ratio",
    ),
    "CVD": dict(
        teigi="累積出来高デルタ＝Σ(テイカー買い量×2 − 総出来高)＝Σ(テイカー買い − テイカー売り)",
        ryugi="Binance Spot 1分足 kline の taker_buy_base_asset_volume（その足でテイカーが買った基準資産量・"
              "kline 9列目）から組み立て。刻印は足の開始時刻・集計は足の終わりに確定"
              "＝5分バーへの ffill は kline の慣例（行＝その足の確定値）と整合",
        houkou="需給＝増加でテイカー買い圧の積み上がり",
        source="https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints",
    ),
}


# ══ 軸カタログ E-c との突き合わせ（検査7・まこさん OK 2026-07-30）══════════
# entry_exit_matrix.md の E-c（Entry 指標の軸カタログ）の項目1つずつに、実装列との対応を持つ。
# 検査7 が E-c の実文とこの表を機械照合する＝E-c を変えたのに表を直さない・表にあるのに実装が
# 消えた、のどちらも機械検出。未実装は ⚠️ で可視化する（実装するかは歩2 とまこさんの判断）。
# impl は実装列名の正規表現（先頭一致）。空リスト＝未実装。
AXIS_EC: list[dict] = [
    # トレンド/モメンタム
    dict(cat="トレンド/モメンタム", token="ADX", impl=[r"ADX\d+"], status="あり", note=""),
    dict(cat="トレンド/モメンタム", token="DI", impl=[r"DI差\d+"], status="あり", note=""),
    dict(cat="トレンド/モメンタム", token="MACD(line/sig/hist)",
         impl=[r"MACD線%", r"MACDシグナル線%", r"MACDヒスト%"],
         status="あり", note="シグナル線の単体列は 2026-07-30 に追加（検査7 の指摘を解消）"),
    dict(cat="トレンド/モメンタム", token="RSI(7/14/21)", impl=[r"RSI\d+"], status="あり",
         note="実装は 7/9/14/21＝一覧より広い"),
    dict(cat="トレンド/モメンタム", token="ROC", impl=[r"ROC\d+"], status="あり", note=""),
    dict(cat="トレンド/モメンタム", token="Stoch(k/d)", impl=[r"Stoch%K\d+", r"Stoch%D\d+"], status="あり", note=""),
    dict(cat="トレンド/モメンタム", token="MFI", impl=[r"MFI\d+"], status="あり", note=""),
    dict(cat="トレンド/モメンタム", token="CMF", impl=[r"CMF\d+"], status="あり", note=""),
    dict(cat="トレンド/モメンタム", token="OBV", impl=[r"OBV傾き\d+"], status="あり",
         note="傾きとして実装（生の累積は列でない）"),
    dict(cat="トレンド/モメンタム", token="Ichimoku", impl=[r"close vs 転換線%", r"close vs 基準線%"],
         status="あり", note=""),
    dict(cat="トレンド/モメンタム", token="RCI", impl=[r"RCI\d+"], status="あり", note=""),
    dict(cat="トレンド/モメンタム", token="MTF傾き整合", impl=[], status="未実装",
         note="足ごとの EMA傾きは有り＝複数足の整合は条件の組み立て側（歩2）"),
    # ボラ
    dict(cat="ボラ", token="ATR%", impl=[r"ATR%\d+"], status="あり", note=""),
    dict(cat="ボラ", token="BB%b", impl=[r"BB%b\("], status="あり", note=""),
    dict(cat="ボラ", token="BB幅", impl=[r"BB幅\("], status="あり", note=""),
    dict(cat="ボラ", token="realized_vol", impl=[r"realized_vol\d+"], status="あり", note=""),
    dict(cat="ボラ", token="donchian幅", impl=[r"Donchian幅%\d+"], status="あり", note=""),
    dict(cat="ボラ", token="zscore_return", impl=[r"zscore_return\d+"], status="あり",
         note="対数リターン基準を 2026-07-30 に追加・価格基準の zscore は別列で残す"),
    # 出来高
    dict(cat="出来高", token="volume_ratio", impl=[r"volume_ratio\d+"], status="あり", note=""),
    dict(cat="出来高", token="OBV傾き", impl=[r"OBV傾き\d+"], status="あり", note=""),
    dict(cat="出来高", token="CMF", impl=[r"CMF\d+"], status="あり", note=""),
    dict(cat="出来高", token="MFI", impl=[r"MFI\d+"], status="あり", note=""),
    # ローソク
    dict(cat="ローソク", token="engulfing", impl=[r"包み足"], status="あり", note=""),
    dict(cat="ローソク", token="pinbar", impl=[r"pinbar"], status="あり", note=""),
    dict(cat="ローソク", token="harami孕み足", impl=[r"孕み足"], status="あり",
         note="教科書定義で 2026-07-30 に実装（検査7 の指摘を解消）"),
    dict(cat="ローソク", token="streak", impl=[r"連続本数"], status="あり", note=""),
    dict(cat="ローソク", token="body_ratio", impl=[r"body比"], status="あり", note=""),
    dict(cat="ローソク", token="wick_ratio", impl=[r"上ヒゲ比", r"下ヒゲ比"], status="あり", note=""),
    # 形(W窓)
    dict(cat="形(W窓)", token="V", impl=[r"形スコア\d+"], status="あり", note="形スコア V=+2"),
    dict(cat="形(W窓)", token="W", impl=[r"W字\("], status="あり",
         note="教科書のダブルボトム検出を 2026-07-30 に実装（同水準の2底＋ネックライン上抜け・流儀は定義表）"),
    dict(cat="形(W窓)", token="M", impl=[r"形スコア\d+"], status="あり", note="形スコア M=−2"),
    dict(cat="形(W窓)", token="swing_dist", impl=[r"swing高値距離%\d+", r"swing安値距離%\d+"], status="あり", note=""),
    dict(cat="形(W窓)", token="bars_since_high-low",
         impl=[r"高値からの経過バー\d+", r"安値からの経過バー\d+"], status="あり", note=""),
    # 位置
    dict(cat="位置", token="close vs EMA", impl=[r"close vs EMA\d+%"], status="あり", note=""),
    dict(cat="位置", token="SMA", impl=[r"close vs SMA\d+%"], status="あり", note=""),
    dict(cat="位置", token="VWAP", impl=[r"close vs VWAP%\d+"], status="あり", note=""),
    dict(cat="位置", token="kijun", impl=[r"close vs 基準線%"], status="あり", note=""),
    dict(cat="位置", token="keltner", impl=[r"close vs Keltner上%", r"close vs Keltner下%"], status="あり", note=""),
    dict(cat="位置", token="supertrend", impl=[r"close vs Supertrend%"], status="あり", note=""),
    dict(cat="位置", token="high-low", impl=[r"close vs \d+本高値%", r"close vs \d+本安値%"], status="あり", note=""),
    # 構造
    dict(cat="構造", token="pivot(PP/R/S)",
         impl=[r"close vs pivotPP%\d+", r"close vs pivotR1%\d+", r"close vs pivotS1%\d+"], status="あり",
         note="R1/S1 を 2026-07-30 に追加＝PP と同じ移動窓の変形（流儀は定義表に明記）"),
    dict(cat="構造", token="fib(382-786)", impl=[r"fib位置\d+"], status="あり",
         note="連続位置 0〜1 として実装＝382/618 等の水準は閾値側で表現"),
    dict(cat="構造", token="VP(VAH/VAL/POC)",
         impl=[r"close vs POC%\d+", r"close vs VAH%\d+", r"close vs VAL%\d+"], status="あり", note=""),
    dict(cat="構造", token="S-R touch_count", impl=[r"S-Rタッチ数\("], status="あり", note=""),
    # 需給
    dict(cat="需給", token="taker_ls", impl=[r"taker_ls"], status="あり",
         note="外部データ（load_demand）＝被覆は検査6"),
    dict(cat="需給", token="L-S比", impl=[r"L-S比"], status="あり",
         note="外部データ（load_demand）＝被覆は検査6"),
    dict(cat="需給", token="CVD", impl=[r"CVD"], status="あり",
         note="外部データ（load_demand）＝被覆は検査6"),
]


# ══ レンジ幾何列の登録（歩3 冒頭①・CP3 提案2-(a)・設計書 §2.3・まこさん GO 2026-07-30）═══
# 正本ロジック＝scripts/dashboard/build_regime_gate_rg.py（RG ゾーンビルダー・視認校正3巡）。
# ここは定義・流儀・因果性・既知答えの登録（実装列は observe_diag build_range_geometry が作る）。
# ★条件の材料に使えるのは比率列（kind="ratio"）だけ（H6 価格非依存）。価格水準5列（kind="price"）は
#   出口 placement の幾何参照（例 mid + f×(res_hi−mid)）専用＝閾値の材料には使えない（検証器 G6 が拒否）。
RANGE_GEO_TF = "5m（1h ゾーンを足が閉じた時刻から ffill・状態機械は過去 close の逐次更新）"
RANGE_GEO_REF: dict[str, dict] = {
    "res_hi": dict(kind="price", teigi="レジスタンス帯の上端（1h 確定 fractal スイング高値を tol で束ねた帯・padding 込み）",
                   ryugi="RG ゾーンビルダー（build_regime_gate_rg._zones_1h_rg・fractal j+2 確定＝L-179 型の確定遅延）",
                   houkou="価格水準＝placement の幾何参照専用（条件の材料には使えない・H6）"),
    "res_lo": dict(kind="price", teigi="レジスタンス帯の下端", ryugi="同上", houkou="同上"),
    "sup_hi": dict(kind="price", teigi="サポート帯の上端", ryugi="同上", houkou="同上"),
    "sup_lo": dict(kind="price", teigi="サポート帯の下端", ryugi="同上", houkou="同上"),
    "mid": dict(kind="price", teigi="レンジ中央＝(res_lo + sup_hi) / 2（エンジン v11_mid と同式）",
                ryugi="e37_scalp._apply_rg5_to_5m と同じ定義（帯の内側の中点）", houkou="同上"),
    "W%": dict(kind="ratio", teigi="帯幅％＝(res_hi − sup_lo) / close × 100",
               ryugi="エンジンの W（USD 幅）を close で割って%化（H6）", houkou="状態量＝大きいほど広いレンジ"),
    "帯内位置%": dict(kind="ratio", teigi="上半分の帯内位置＝(close − mid) / (res_hi − mid)。mid=0・res_hi=1",
                  ryugi="S2 入口の pos と同式（e38_logic_parts._pullback_short L95-99）。分母≤0 は欠損",
                  houkou="順張り値＝1 に近いほど上端（戻り売りの場所）"),
}


def _range_geo_case(zone_touch: int, zone_lookback: int) -> pd.DataFrame:
    """既知答え用の合成5分足。毎時間フラット close=100 で、スパイク時間だけ high=110（レジ束）／
    low=90（サポ束）を置く＝1h fractal が電卓で追える形。close は常に 100＝上げトレンド状態機械は発火しない。"""
    hours = max(zone_lookback, 25) + 40
    n = hours * 12
    c = np.full(n, 100.0)
    h = np.full(n, 100.0)
    l = np.full(n, 100.0)
    k = max(int(zone_touch), 2) + 1
    hi_hours = [hours - 12 - 6 * j for j in range(k)]          # 末尾から 12,18,24,… 時間前
    lo_hours = [hours - 9 - 6 * j for j in range(k)]           # 末尾から 9,15,21,… 時間前
    for hh_ in hi_hours:
        h[hh_ * 12] = 110.0
    for lh_ in lo_hours:
        l[lh_ * 12] = 90.0
    idx = pd.date_range("2024-01-01", periods=n, freq="5min")
    return pd.DataFrame({"open": c, "high": h, "low": l, "close": c, "volume": np.full(n, 1.0)}, index=idx)


def range_geo_known_check(geo_fn, zone_tol: float, zone_touch: int, zone_lookback: int) -> list[str]:
    """既知答え＝合成バーの最終行で、帯の4隅・mid・W%・帯内位置% が電卓式と一致するか。
    電卓式: res 帯＝110×(1∓tol/2)・sup 帯＝90×(1∓tol/2)・mid=(res_lo+sup_hi)/2・
    W%=(res_hi−sup_lo)/100×100・帯内位置%=(100−mid)/(res_hi−mid)。geo_fn は観察側の実装
    （observe_diag.build_range_geometry・adaptive_k=None＝固定 tol）を注入する＝実装と定義の照合。"""
    ng = []
    bars = _range_geo_case(zone_touch, zone_lookback)
    geo = geo_fn(bars)
    t = zone_tol
    exp = {"res_lo": 110 * (1 - t / 2), "res_hi": 110 * (1 + t / 2),
           "sup_lo": 90 * (1 - t / 2), "sup_hi": 90 * (1 + t / 2)}
    exp["mid"] = (exp["res_lo"] + exp["sup_hi"]) / 2
    exp["W%"] = (exp["res_hi"] - exp["sup_lo"]) / 100.0 * 100.0
    exp["帯内位置%"] = (100.0 - exp["mid"]) / (exp["res_hi"] - exp["mid"])
    last = geo.iloc[-1]
    for col, want in exp.items():
        got = float(last.get(col, np.nan))
        if not np.isfinite(got) or abs(got - want) > 1e-9 * max(1.0, abs(want)):
            ng.append(f"レンジ幾何 既知答え不一致: {col} 期待 {want:.10g} 実測 {got:.10g}")
    missing = [c for c in RANGE_GEO_REF if c not in geo.columns]
    if missing:
        ng.append(f"レンジ幾何: 実装列が定義表より少ない {missing}")
    extra = [c for c in geo.columns if c not in RANGE_GEO_REF]
    if extra:
        ng.append(f"レンジ幾何: 定義表に無い実装列 {extra}（登録なしの列は足せない）")
    return ng


# ══ 系統マップ（G3 同系統制限の正本・CP3 Q4・全 family を単一割当＝載っていない family は生成不可）══
# 8系統＝トレンド／オシレーター／ボラ／出来高／ローソク／構造・位置／需給／時間帯（設計書 G3）。
# 両属性の family は主用途で単一割当し、理由を note に書く（例＝MFI はオシレーター・CP3 の例示どおり）。
FAMILY_LINEAGE: dict[str, dict] = {
    # トレンド
    "ADX": dict(k="トレンド", note="向きを持たないがトレンドの強さの計測が主用途（Wilder）"),
    "DI差": dict(k="トレンド"), "MACD線%": dict(k="トレンド"), "MACDヒスト%": dict(k="トレンド"),
    "MACDシグナル線%": dict(k="トレンド"), "EMA傾き": dict(k="トレンド"),
    "Supertrend": dict(k="トレンド", note="位置系でもあるが符号がトレンドの向きそのもの＝主用途トレンド"),
    "転換線": dict(k="トレンド", note="位置系でもあるが一目の転換判断が主用途"),
    "基準線": dict(k="トレンド", note="同上"),
    # オシレーター
    "RSI": dict(k="オシレーター"), "ROC": dict(k="オシレーター"), "Stoch%K": dict(k="オシレーター"),
    "Stoch%D": dict(k="オシレーター"), "RCI": dict(k="オシレーター"),
    "zscore": dict(k="オシレーター"), "zscore_return": dict(k="オシレーター"),
    "MFI": dict(k="オシレーター", note="出来高系でもあるが行き過ぎの計測が主用途（CP3 Q4 の例示どおり）"),
    "BB%b": dict(k="オシレーター", note="ボラ由来だが 0〜1 の有界位置＝行き過ぎの計測が主用途"),
    # 業界の指標（pandas-ta 由来・フロー 段6-1 の1回目）
    "AO%": dict(k="トレンド", note="2つの期間の平均の差＝MACD と同じ作り"),
    "APO%": dict(k="トレンド", note="同上。平均が単純移動平均である点だけ違う"),
    "BIAS": dict(k="オシレーター", note="移動平均からの乖離＝行き過ぎの計測"),
    "BOP": dict(k="ローソク", note="1本のバーの中で買いと売りのどちらが押し切ったか"),
    "AR": dict(k="オシレーター", note="始値を基準にした上下の力の比"),
    "BR": dict(k="オシレーター", note="前の終値を基準にした上下の力の比"),
    "CCI": dict(k="オシレーター"),
    "CFO": dict(k="オシレーター", note="直線あてはめの予測とのずれ＝行き過ぎの計測"),
    "CG": dict(k="オシレーター", note="重心の位置＝行き過ぎの計測"),
    "CMO": dict(k="オシレーター"),
    "COPC": dict(k="トレンド", note="長い期間の変化率をならしたもの＝向きの計測"),
    "CTI": dict(k="トレンド", note="時間との相関＝素直に一方向へ動いているか"),
    "DM+%": dict(k="トレンド"), "DM-%": dict(k="トレンド"),
    "ER": dict(k="ボラ", note="正味の動き ÷ 途中の動き＝動きの素直さ（向きを持たない）"),
    "ERI強気%": dict(k="トレンド", note="高値と平均の差＝上方向の押し込み"),
    "ERI弱気%": dict(k="トレンド", note="安値と平均の差＝下方向の押し込み"),
    "FISHER": dict(k="オシレーター"), "FISHERシグナル": dict(k="オシレーター"),
    "INERTIA": dict(k="トレンド", note="活力指数をならしたもの"),
    "KDJ%K": dict(k="オシレーター"), "KDJ%D": dict(k="オシレーター"), "KDJ%J": dict(k="オシレーター"),
    "KST": dict(k="トレンド"), "KSTシグナル": dict(k="トレンド"),
    "LRSI": dict(k="オシレーター"),
    # 業界の指標（pandas-ta 由来・フロー 段6-1 の2回目）
    "MOM%": dict(k="トレンド", note="n 本前との差＝向きの計測"),
    "PGO": dict(k="オシレーター", note="平均からの離れを値動きの荒さでならした行き過ぎの計測"),
    "PO": dict(k="オシレーター", note="直線あてはめからのずれ＝行き過ぎの計測"),
    "PSL": dict(k="オシレーター", note="上げた本数の割合＝買われすぎ・売られすぎ"),
    "RSX": dict(k="オシレーター"),
    "PPO": dict(k="トレンド"), "PPOシグナル": dict(k="トレンド"), "PPOヒスト": dict(k="トレンド"),
    "PVO": dict(k="出来高"), "PVOシグナル": dict(k="出来高"), "PVOヒスト": dict(k="出来高"),
    "RVGI": dict(k="オシレーター", note="バスの中の終値の位置を積み上げたもの"),
    "RVGIシグナル": dict(k="オシレーター"), "RVGIヒスト": dict(k="オシレーター"),
    "QQE": dict(k="オシレーター"), "QQE_RSIMA": dict(k="オシレーター"),
    "SMC_SWEEP": dict(k="構造・位置", note="直前の高値・安値を抜いて戻した足＝水準に関わる判定"),
    "SQZ": dict(k="ボラ", note="帯の縮み具合から作る値"),
    "SQZ_ON": dict(k="ボラ"),
    "SQZPRO_ON_WIDE": dict(k="ボラ"), "SQZPRO_ON_NARROW": dict(k="ボラ"),
    "STC": dict(k="トレンド"), "STCstoch": dict(k="トレンド"),
    # 業界の指標（pandas-ta 由来・フロー 段6-1 の3回目）
    "StochRSI%K": dict(k="オシレーター"), "StochRSI%D": dict(k="オシレーター"),
    "TD_SEQ_UP": dict(k="ローソク", note="連続した足の数え上げ＝直前の並びの形"),
    "TD_SEQ_DN": dict(k="ローソク", note="同上"),
    "TRIX": dict(k="トレンド"), "TRIXシグナル": dict(k="トレンド"), "TRIXヒスト": dict(k="トレンド"),
    "TSI": dict(k="トレンド"), "TSIシグナル": dict(k="トレンド"), "TSIヒスト": dict(k="トレンド"),
    "UO": dict(k="オシレーター"),
    "close vs SINWMA%": dict(k="構造・位置"), "SINWMA傾き%": dict(k="トレンド"),
    "close vs SSF%": dict(k="構造・位置"), "SSF傾き%": dict(k="トレンド"),
    "close vs SWMA%": dict(k="構造・位置"), "SWMA傾き%": dict(k="トレンド"),
    "close vs T3%": dict(k="構造・位置"), "T3傾き%": dict(k="トレンド"),
    "close vs TEMA%": dict(k="構造・位置"), "TEMA傾き%": dict(k="トレンド"),
    "close vs TRIMA%": dict(k="構造・位置"), "TRIMA傾き%": dict(k="トレンド"),
    "close vs TSF%": dict(k="構造・位置"), "TSF傾き%": dict(k="トレンド"),
    "close vs VIDYA%": dict(k="構造・位置"), "VIDYA傾き%": dict(k="トレンド"),
    "close vs VWMA%": dict(k="構造・位置"), "VWMA傾き%": dict(k="トレンド"),
    "close vs WMA%": dict(k="構造・位置"), "WMA傾き%": dict(k="トレンド"),
    "close vs ZLMA%": dict(k="構造・位置"), "ZLMA傾き%": dict(k="トレンド"),
    "ADXR": dict(k="トレンド"), "DI+": dict(k="トレンド"), "DI-": dict(k="トレンド"), "DX": dict(k="トレンド"),
    "AMAT_LR": dict(k="トレンド"),
    "AROONU": dict(k="トレンド"), "AROOND": dict(k="トレンド"), "AROONOSC": dict(k="トレンド"),
    "CHOP": dict(k="ボラ", note="もみ合いの度合い＝値動きの大きさの計測"),
    "close vs CKSPl%": dict(k="構造・位置"), "close vs CKSPs%": dict(k="構造・位置"),
    "DPO%": dict(k="オシレーター"),
    "close vs PMAX%": dict(k="構造・位置"), "close vs PSAR%": dict(k="構造・位置"),
    "PSAR加速": dict(k="トレンド"), "PSAR反転": dict(k="構造・位置"),
    "QSTICK%": dict(k="ローソク", note="終値と始値の差の平均＝バスの中の押し切り方"),
    "close vs SAREXT%": dict(k="構造・位置"),
    "TTM_TREND": dict(k="トレンド"), "VHF": dict(k="ボラ"), "VTXP": dict(k="トレンド"), "VTXM": dict(k="トレンド"),
    "close vs LRb%": dict(k="構造・位置"), "LRb傾き%": dict(k="トレンド"), "LRslope%": dict(k="トレンド"),
    "close vs MAMA%": dict(k="構造・位置"), "close vs FAMA%": dict(k="構造・位置"),
    "close vs MCGD%": dict(k="構造・位置"), "MCGD傾き%": dict(k="トレンド"),
    "close vs MIDPOINT%": dict(k="構造・位置"), "MIDPOINT傾き%": dict(k="トレンド"),
    "close vs MIDPRICE%": dict(k="構造・位置"), "MIDPRICE傾き%": dict(k="トレンド"),
    "close vs MMAR%": dict(k="構造・位置"), "MMAR傾き%": dict(k="トレンド"),
    "close vs PWMA%": dict(k="構造・位置"), "PWMA傾き%": dict(k="トレンド"),
    "close vs RAINBOW%": dict(k="構造・位置"), "RAINBOW傾き%": dict(k="トレンド"),
    "close vs RMA%": dict(k="構造・位置"), "RMA傾き%": dict(k="トレンド"),
    "close vs ALMA%": dict(k="構造・位置"), "ALMA傾き%": dict(k="トレンド"),
    "close vs DEMA%": dict(k="構造・位置"), "DEMA傾き%": dict(k="トレンド"),
    "close vs FWMA%": dict(k="構造・位置"), "FWMA傾き%": dict(k="トレンド"),
    "close vs HILO%": dict(k="構造・位置"),
    "close vs HMA%": dict(k="構造・位置"), "HMA傾き%": dict(k="トレンド"),
    "close vs HT_TRENDLINE%": dict(k="構造・位置"),
    "close vs HWMA%": dict(k="構造・位置"),
    "close vs JMA%": dict(k="構造・位置"),
    "close vs KAMA%": dict(k="構造・位置"), "KAMA傾き%": dict(k="トレンド"),
    "close vs LINREG%": dict(k="構造・位置"), "LINREG傾き%": dict(k="トレンド"),
    "LRangle": dict(k="トレンド"),
    "VWMACD線%": dict(k="トレンド", note="出来高で重みづけた MACD"),
    "VWMACDシグナル%": dict(k="トレンド"), "VWMACDヒスト%": dict(k="トレンド"),
    # ボラ
    "ATR%": dict(k="ボラ"), "BB幅": dict(k="ボラ"), "realized_vol": dict(k="ボラ"), "Donchian幅": dict(k="ボラ"),
    # 出来高
    "volume_ratio": dict(k="出来高"),
    "CMF": dict(k="出来高", note="オシレーター形でもあるが出来高加重の資金フローが主用途"),
    "OBV傾き": dict(k="出来高", note="トレンド確認にも使うが出来高の積み上げが主用途"),
    # ローソク
    "包み足": dict(k="ローソク"), "孕み足": dict(k="ローソク"), "pinbar": dict(k="ローソク"),
    "連続本数": dict(k="ローソク"), "body比": dict(k="ローソク"), "上ヒゲ比": dict(k="ローソク"),
    "下ヒゲ比": dict(k="ローソク"),
    # 構造・位置
    "swing高値距離": dict(k="構造・位置"), "swing安値距離": dict(k="構造・位置"),
    "高値からの経過バー": dict(k="構造・位置"), "安値からの経過バー": dict(k="構造・位置"),
    "形スコア": dict(k="構造・位置", note="反転サインでもあるが W 窓の形＝構造の計測が主用途"),
    "W字": dict(k="構造・位置", note="同上（ダブルボトム＝構造パターン）"),
    "close vs EMA": dict(k="構造・位置"), "close vs SMA": dict(k="構造・位置"),
    "close vs VWAP": dict(k="構造・位置"), "Keltner上": dict(k="構造・位置"), "Keltner下": dict(k="構造・位置"),
    "n本高値": dict(k="構造・位置"), "n本安値": dict(k="構造・位置"),
    "pivotPP": dict(k="構造・位置"), "pivotR1": dict(k="構造・位置"), "pivotS1": dict(k="構造・位置"),
    "fib位置": dict(k="構造・位置"), "POC": dict(k="構造・位置"), "VAH": dict(k="構造・位置"),
    "VAL": dict(k="構造・位置"), "S-Rタッチ数": dict(k="構造・位置"),
    "レンジ幾何": dict(k="構造・位置", note="RG ゾーンビルダーの帯＝構造そのもの"),
    # 需給・時間帯
    "taker_ls": dict(k="需給"), "L-S比": dict(k="需給"), "CVD": dict(k="需給"),
    "時刻": dict(k="時間帯"), "曜日": dict(k="時間帯"),
}
LINEAGE_KINDS = ("トレンド", "オシレーター", "ボラ", "出来高", "ローソク", "構造・位置", "需給", "時間帯")

# 系統 → その系統の指標が「答える問い」（2026-08-09 新設・マイルストーン①のフロー 段4 が使う）。
# ★新しい事実は作っていない。既に在る文書の記述を、系統ごとに1行へ言い換えただけ＝出典を1件ずつ付ける。
LINEAGE_QUESTION: dict[str, tuple[str, str]] = {
    "トレンド": ("いま どちらへ動いているか",
              "technical KB §3.1 の表「Trend (トレンド系)｜方向確認」"),
    "オシレーター": ("行き過ぎているか（買われすぎ・売られすぎ）",
                "technical KB §3.1 の表「Momentum / Oscillator (オシレーター系)｜買われすぎ/売られすぎ」"),
    "ボラ": ("どれくらい大きく動いているか",
           "technical KB §3.1 の表「Volatility (ボラ系)｜価格変動測定・SL 設定」"),
    "出来高": ("買いと売りの どちらの圧力が強いか",
            "technical KB §3.1 の表「Volume (ボリューム系)｜買い/売り圧力」"),
    "構造・位置": ("いま どの価格水準にいるか",
               "technical KB §3.1 の表「Support / Resistance｜価格水準識別」"),
    "ローソク": ("直前の1〜2本の形が 反転を示しているか",
             "technical KB §B.1 ローソク足 (Japanese Candlestick) パターン"),
    "需給": ("実際の注文の偏りが どちらに出ているか",
           "technical KB §C.5 Order Flow / Footprint Chart / CVD"),
    "時間帯": ("いまが どの時間帯・曜日か",
            "軸カタログ entry_exit_matrix.md の E-j（時間帯・セッション）"),
}


def lineage_coverage(families: list[str]) -> list[str]:
    """系統マップに載っていない family の一覧（空であるべき＝載っていない family は生成不可・G3）。"""
    return [f for f in dict.fromkeys(families) if f not in FAMILY_LINEAGE]


# ══ 業界のライブラリ（pandas-ta-classic）との対応表（2026-08-09 新設・observe_diag の検査10 が使う）══
# ★何のためか: 「業界に在って、うちに無い指標」を機械で出すため。
# ★なぜ対応表を人が書くか: 名前の文字が違うだけの同じ指標（うちの「ATR%」＝ライブラリの natr など）を、
#   機械は自動で結び付けられない。だから 参照表の family 53件 のそれぞれについて、
#   「同じものを計算するライブラリの関数はどれか」を1行ずつ人が書き、まこさんが読んで直せる形にする。
# ★2026-08-08 に手で数えた「押さえているのは34種類」は再現できない（そのときの対応表が記録に残っていない）。
#   だから今回 書き直した。数は下の表から機械が数える＝この表を直せば数が変わる。
# ★空のタプル () ＝ ライブラリに相当する関数が無い。理由を必ず添える。
INDUSTRY_MAP: dict[str, tuple[tuple[str, ...], str]] = {
    # ── トレンド・モメンタム ──
    "ADX": (("adx",), "adx は ADX・DI+・DI− を1本の関数で返す"),
    "DI差": (("adx",), "同じ adx が返す DI+ と DI− の差＝関数としては同じもの"),
    "MACD線%": (("macd",), "macd の MACD 線。うちは終値で割って%にしている（H6・価格に依存させない）"),
    "MACDヒスト%": (("macd",), "macd のヒストグラム。同上で%化"),
    "MACDシグナル線%": (("macd",), "macd のシグナル線。同上で%化"),
    "RSI": (("rsi",), ""),
    "ROC": (("roc",), ""),
    "Stoch%K": (("stoch",), ""),
    "Stoch%D": (("stoch",), ""),
    "MFI": (("mfi",), ""),
    "CMF": (("cmf",), ""),
    "OBV傾き": (("obv",), "obv そのものはライブラリに在る。うちは その差分を出来高で割った傾きにしている"),
    "転換線": (("ichimoku",), "ichimoku が転換線・基準線をまとめて返す"),
    "基準線": (("ichimoku",), "同上"),
    "RCI": ((), "順位相関の指標。ライブラリに相当する関数が無い（scipy の順位相関で独立に照合する＝段3の(b)）"),
    # ── フロー 段6-1 の1回目で足した19関数（アルファベット順 ao〜lrsi）──
    "AO%": (("ao",), "ao そのもの。うちは終値で割って%にしている（H6）"),
    "APO%": (("apo",), "apo そのもの。同上で%化。★平均が単純移動平均＝MACD線%（EMA）とは別物"),
    "BIAS": (("bias",), ""),
    "BOP": (("bop",), ""),
    "AR": (("brar",), "brar が AR・BR をまとめて返す"),
    "BR": (("brar",), "同上"),
    "CCI": (("cci",), ""),
    "CFO": (("cfo", "fosc"), "cfo と fosc は同じ式（実測でぴったり重なる）＝1つにまとめた"),
    "CG": (("cg",), ""),
    "CMO": (("cmo",), ""),
    "COPC": (("coppock",), ""),
    "CTI": (("cti",), ""),
    "DM+%": (("dm",), "dm が上下をまとめて返す。うちは終値で割って%にしている（H6）"),
    "DM-%": (("dm",), "同上"),
    "ER": (("er",), ""),
    "ERI強気%": (("eri",), "eri が強気・弱気をまとめて返す。うちは%化（H6）"),
    "ERI弱気%": (("eri",), "同上"),
    "FISHER": (("fisher",), "fisher が本体とシグナルをまとめて返す"),
    "FISHERシグナル": (("fisher",), "同上"),
    "INERTIA": (("inertia",), ""),
    "KDJ%K": (("kdj",), "kdj が K・D・J をまとめて返す"),
    "KDJ%D": (("kdj",), "同上"), "KDJ%J": (("kdj",), "同上"),
    "KST": (("kst",), "kst が本体とシグナルをまとめて返す"),
    "KSTシグナル": (("kst",), "同上"),
    "LRSI": (("lrsi",), ""),
    # ── フロー 段6-1 の2回目で足したもの（macdext〜stc）──
    "MOM%": (("mom",), "mom そのもの。うちは終値で割って%にしている（H6）"),
    "PGO": (("pgo",), ""), "PO": (("po",), ""), "PSL": (("psl",), ""), "RSX": (("rsx",), ""),
    "PPO": (("ppo",), "ppo が本体・ヒスト・シグナルをまとめて返す"),
    "PPOシグナル": (("ppo",), "同上"), "PPOヒスト": (("ppo",), "同上"),
    "PVO": (("pvo",), "pvo が本体・ヒスト・シグナルをまとめて返す"),
    "PVOシグナル": (("pvo",), "同上"), "PVOヒスト": (("pvo",), "同上"),
    "RVGI": (("rvgi",), "rvgi が本体・シグナル・ヒストをまとめて返す"),
    "RVGIシグナル": (("rvgi",), "同上"), "RVGIヒスト": (("rvgi",), "同上"),
    "QQE": (("qqe",), "qqe が7列 返すうち、重ならない2列だけ入れた"),
    "QQE_RSIMA": (("qqe",), "同上"),
    "SMC_SWEEP": (("smc_sweep",), ""),
    "SQZ": (("squeeze",), "squeeze が4列 返す"),
    "SQZ_ON": (("squeeze",), "同上"),
    "SQZPRO_ON_WIDE": (("squeeze_pro",), "squeeze_pro が6列 返すうち、squeeze と重ならない3列だけ入れた"),
    "SQZPRO_ON_NARROW": (("squeeze_pro",), "同上"),
    "STC": (("stc",), "stc が3列 返すうち、MACD の列は うちの MACD線% と同じなので入れない"),
    "STCstoch": (("stc",), "同上"),
    # ── フロー 段6-1 の3回目で足したもの（stochf〜willr）──
    "StochRSI%K": (("stochrsi",), "stochrsi が %K・%D をまとめて返す"),
    "StochRSI%D": (("stochrsi",), "同上"),
    "TD_SEQ_UP": (("td_seq",), "td_seq が上げ側・下げ側をまとめて返す"),
    "TD_SEQ_DN": (("td_seq",), "同上"),
    "TRIX": (("trix",), "trix が本体とシグナルをまとめて返す"),
    "TRIXシグナル": (("trix",), "同上"),
    "TRIXヒスト": (("trixh",), "trixh はヒストの列だけ新しい（本体とシグナルは trix と同じ）"),
    "TSI": (("tsi",), "tsi が本体とシグナルをまとめて返す"),
    "TSIシグナル": (("tsi",), "同上"), "TSIヒスト": (("tsi",), "同上（差はうちで作る）"),
    "UO": (("uo",), ""),
    # ── trend 16関数 ──
    "ADXR": (("adxr",), ""), "DI+": (("adxr",), "adxr が DI+ / DI− も返す"), "DI-": (("adxr",), "同上"),
    "DX": (("dx",), ""), "AMAT_LR": (("amat",), "★式の上で slow は効かず、売り側は裏返しなので買い側の1列だけ入れた"),
    "AROONU": (("aroon",), "aroon が上昇・下降・振動子をまとめて返す"),
    "AROOND": (("aroon",), "同上"), "AROONOSC": (("aroon",), "同上"),
    "CHOP": (("chop",), ""),
    "close vs CKSPl%": (("cksp",), "値段そのもの。うちは終値との距離%（H6）"),
    "close vs CKSPs%": (("cksp",), "同上"),
    "DPO%": (("dpo",), "値段の差。うちは終値で割って%化（H6）。★centered=False で呼ぶ"),
    "close vs PMAX%": (("pmax",), "値段そのもの。うちは終値との距離%（H6）"),
    "close vs PSAR%": (("psar",), "同上。買い側・売り側のうち出ている方を使う"),
    "PSAR加速": (("psar",), "同上"), "PSAR反転": (("psar",), "同上"),
    "QSTICK%": (("qstick",), "終値と始値の差。うちは終値で割って%化（H6）"),
    "close vs SAREXT%": (("sarext",), "値段そのもの。うちは終値との距離%（H6）"),
    "TTM_TREND": (("ttm_trend",), ""), "VHF": (("vhf",), ""),
    "VTXP": (("vortex",), "vortex が上昇・下降をまとめて返す"), "VTXM": (("vortex",), "同上"),
    # ── overlap 3回目（sinwma〜zlma）──
    "close vs SINWMA%": (("sinwma",), "値段そのもの。うちは終値との距離%（H6）"), "SINWMA傾き%": (("sinwma",), "同上（傾きの形）"),
    "close vs SSF%": (("ssf",), "値段そのもの。うちは終値との距離%（H6）"), "SSF傾き%": (("ssf",), "同上（傾きの形）"),
    "close vs SWMA%": (("swma",), "値段そのもの。うちは終値との距離%（H6）"), "SWMA傾き%": (("swma",), "同上（傾きの形）"),
    "close vs T3%": (("t3",), "値段そのもの。うちは終値との距離%（H6）"), "T3傾き%": (("t3",), "同上（傾きの形）"),
    "close vs TEMA%": (("tema",), "値段そのもの。うちは終値との距離%（H6）"), "TEMA傾き%": (("tema",), "同上（傾きの形）"),
    "close vs TRIMA%": (("trima",), "値段そのもの。うちは終値との距離%（H6）"), "TRIMA傾き%": (("trima",), "同上（傾きの形）"),
    "close vs TSF%": (("tsf",), "値段そのもの。うちは終値との距離%（H6）"), "TSF傾き%": (("tsf",), "同上（傾きの形）"),
    "close vs VIDYA%": (("vidya",), "値段そのもの。うちは終値との距離%（H6）"), "VIDYA傾き%": (("vidya",), "同上（傾きの形）"),
    "close vs VWMA%": (("vwma",), "値段そのもの。うちは終値との距離%（H6）"), "VWMA傾き%": (("vwma",), "同上（傾きの形）"),
    "close vs WMA%": (("wma",), "値段そのもの。うちは終値との距離%（H6）"), "WMA傾き%": (("wma",), "同上（傾きの形）"),
    "close vs ZLMA%": (("zlma",), "値段そのもの。うちは終値との距離%（H6）"), "ZLMA傾き%": (("zlma",), "同上（傾きの形）"),
    # ── overlap 2回目（linregintercept〜rma）──
    "close vs LRb%": (("linregintercept",), "値段そのもの。うちは終値との距離%（H6）"),
    "LRb傾き%": (("linregintercept",), "同上（傾きの形）"),
    "LRslope%": (("linregslope",), "1本あたりの値段の増え方。うちは終値で割って%化（H6）"),
    "close vs MAMA%": (("mama",), "mama が MAMA・FAMA をまとめて返す"),
    "close vs FAMA%": (("mama",), "同上"),
    "close vs MCGD%": (("mcgd",), ""), "MCGD傾き%": (("mcgd",), "同上"),
    "close vs MIDPOINT%": (("midpoint",), ""), "MIDPOINT傾き%": (("midpoint",), "同上"),
    "close vs MIDPRICE%": (("midprice",), ""), "MIDPRICE傾き%": (("midprice",), "同上"),
    "close vs MMAR%": (("mmar",), "mmar が6本の EMA をまとめて返す"),
    "MMAR傾き%": (("mmar",), "同上"),
    "close vs PWMA%": (("pwma",), ""), "PWMA傾き%": (("pwma",), "同上"),
    "close vs RAINBOW%": (("rainbow",), "rainbow が10本の線をまとめて返す"),
    "RAINBOW傾き%": (("rainbow",), "同上"),
    "close vs RMA%": (("rma",), ""), "RMA傾き%": (("rma",), "同上"),
    # ── overlap 1回目（alma〜linregangle）──
    "close vs ALMA%": (("alma",), "alma は値段そのもの。うちは終値との距離%にしている（H6）"),
    "ALMA傾き%": (("alma",), "同上（傾きの形）"),
    "close vs DEMA%": (("dema",), "同上"), "DEMA傾き%": (("dema",), "同上"),
    "close vs FWMA%": (("fwma",), "同上"), "FWMA傾き%": (("fwma",), "同上"),
    "close vs HILO%": (("hilo",), "同上"),
    "close vs HMA%": (("hma",), "同上"), "HMA傾き%": (("hma",), "同上"),
    "close vs HT_TRENDLINE%": (("ht_trendline",), "同上"),
    "close vs HWMA%": (("hwma",), "同上"),
    "close vs JMA%": (("jma",), "同上"),
    "close vs KAMA%": (("kama",), "同上"), "KAMA傾き%": (("kama",), "同上"),
    "close vs LINREG%": (("linreg",), "同上"), "LINREG傾き%": (("linreg",), "同上"),
    "LRangle": (("linregangle",), "角度なので値段に依存しない＝そのまま入れる"),
    "VWMACD線%": (("vwmacd",), "vwmacd が本体・ヒスト・シグナルをまとめて返す。うちは%化（H6）"),
    "VWMACDシグナル%": (("vwmacd",), "同上"), "VWMACDヒスト%": (("vwmacd",), "同上"),
    "EMA傾き": (("ema",), "ema そのものはライブラリに在る。うちは その変化率を傾きにしている"),
    # ── ボラ ──
    "ATR%": (("atr", "natr"), "natr＝ATR を終値の%にしたもの＝うちの ATR% と同じ考え方"),
    "BB%b": (("bbands",), "bbands が %b を返す"),
    "BB幅": (("bbands",), "bbands が帯の幅を返す"),
    "realized_vol": (("hvol",), "hvol＝対数リターンの標準偏差＝うちの realized_vol と同じ考え方"),
    "Donchian幅": (("donchian",), "donchian の上限と下限の差"),
    "zscore": (("zscore",), ""),
    "zscore_return": (("zscore",), "同じ zscore を、終値でなく対数リターンに当てたもの"),
    # ── 出来高 ──
    "volume_ratio": ((), "出来高を その移動平均で割った比。ライブラリに相当する関数が無い"),
    # ── ローソク ──
    "包み足": (("cdl_pattern",), "cdl_pattern が包み足を持つ。⚠️ この関数は TA-Lib が別途 要り、いま入っていない"),
    "孕み足": (("cdl_pattern",), "同上。cdl_inside（内包足）は前バーの色を問わない別の定義なので当てない"),
    "pinbar": ((), "ヒゲの長さの差を連続値にしたもの。ライブラリのローソク足は 0/1 の型判定で、形が違う"),
    "連続本数": ((), "同じ向きが何本 続いたか。ライブラリに相当する関数が無い"),
    "body比": ((), "実体の幅 ÷ 全体の幅。ライブラリに相当する関数が無い"),
    "上ヒゲ比": ((), "同上（上ヒゲ ÷ 全体の幅）"),
    "下ヒゲ比": ((), "同上（下ヒゲ ÷ 全体の幅）"),
    # ── 構造・位置 ──
    "swing高値距離": (("donchian",), "終値と N本高値の距離%。N本高値は donchian の上限と同じ値"),
    "swing安値距離": (("donchian",), "同上（donchian の下限）"),
    "高値からの経過バー": ((), "高値を付けてから何本 経ったか。ライブラリに相当する関数が無い"),
    "安値からの経過バー": ((), "同上"),
    "形スコア": ((), "V字・M字の判定。ライブラリに相当する関数が無い"),
    "W字": ((), "ダブルボトムの完成。ライブラリに相当する関数が無い"),
    "close vs EMA": (("ema",), "終値と EMA の距離%"),
    "close vs SMA": (("sma",), "終値と SMA の距離%"),
    "close vs VWAP": (("vwap",), "終値と VWAP の距離%"),
    "Keltner上": (("kc",), "kc がケルトナーの上下の帯を返す"),
    "Keltner下": (("kc",), "同上"),
    "Supertrend": (("supertrend",), ""),
    "n本高値": (("donchian",), "donchian の上限と同じ値"),
    "n本安値": (("donchian",), "donchian の下限と同じ値"),
    "pivotPP": (("cpr",), "cpr が中心のピボットと帯を返す"),
    "pivotR1": (("cpr",), "⚠️ 部分的。cpr は R1 を返さない（うちは PP から計算している）"),
    "pivotS1": (("cpr",), "⚠️ 部分的。cpr は S1 を返さない（同上）"),
    "fib位置": ((), "N本の高安の中で終値がどこか（0〜1）。式の形は Stoch%K と同じだが、"
                   "フィボナッチの関数はライブラリに無い"),
    "POC": (("vp",), "vp＝出来高プロファイル。POC・VAH・VAL をまとめて出す"),
    "VAH": (("vp",), "同上"),
    "VAL": (("vp",), "同上"),
    "S-Rタッチ数": ((), "同じ値段に何回 触れたか。ライブラリに相当する関数が無い"),
}

# ★入れない候補（★まこさんの承認はまだ・next_step §5 の10番）。既定は「入れる」（まこさん決定＝
#   「利益最大化するために完全に不要な指標以外はすべて入れてほしい」）。だから ここに載せるのは
#   「指標ではないもの」に限る。1件ずつ理由を書く。
INDUSTRY_SKIP: dict[str, str] = {
    # (c) 同じ挙動＝片方を省く（まこさん決定 2026-08-09・逐語「willrは入れない。他にも同じ挙動の
    #     指標があれば紛らわしいので片方を省いていく」）。★どれも「片方を定数倍して定数を足しただけで
    #     ぴったり重なる」ことを実データで確かめた（ずれが値のばらつきの10億分の1 未満）。
    "willr": "うちの Stoch%K から 100 を引いただけ（実測＝最大差 1.4e-14・5,987本）",
    "rocp": "うちの ROC を 100 で割っただけ（実測＝最大差 1.1e-14）",
    "rocr": "うちの ROC に 1 を足して 100 で割っただけ（実測＝最大差 0）",
    "rocr100": "うちの ROC に 100 を足しただけ（実測＝最大差 0）",
    "stochf": "うちの Stoch%K・Stoch%D そのもの（実測＝最大差 0）",
    "fosc": "cfo（チャンデ予測振動子）と同じ式（実測＝ぴったり重なる）",
    "macdext": "うちの MACD線%・シグナル線%・ヒスト% と同じ（実測＝暖機のあとで最大差 8.6e-14）",
    "macdfix": "同上（実測＝最大差 8.6e-14）",
    "slope": "mom（勢い）をローソク足の本数で割っただけ（実測＝ぴったり重なる）",
    "smi": "tsi（真の強さ指数）を 100 で割っただけ（実測＝100倍して ずれ 7.3e-16）",
    "plus_dm": "うちの DM+% と同じ（実測＝最大差 1.1e-15）",
    "minus_dm": "うちの DM-% と同じ（実測＝最大差 2.7e-15）",
    "mavp": "★未来を見る（H2 違反）。既定では各足で使う本数を np.linspace(2, 30, データ全体の本数) で"
            "作るので、データが増えると過去の足の値まで変わる（2026-08-09 実測で検出）",
    # (a) 1本の中の値段を平均するだけ＝新しい情報が増えない
    "hl2": "そのバーの高値と安値の平均＝値段そのもの", "hlc3": "高値・安値・終値の平均＝値段そのもの",
    "ohlc4": "4本値の平均＝値段そのもの", "wcp": "終値を重くした加重平均＝値段そのもの",
    "medprice": "高値と安値の中央＝値段そのもの", "typprice": "代表値段＝値段そのもの",
    "avgprice": "4本値の平均＝値段そのもの",
    # (b) うちに既に同じものが在る＝重複
    #   ★2026-08-09 に理由を訂正した。前は「売買の成績を出すもの＝条件の材料ではない」と書いていたが、
    #     実物を突き合わせたら指標として使えるもので、理由が間違っていた。
    #     percent_return と log_return＝うちの ROC（定義の逐語「n 本前からの変化率%」）と同じ。
    #     drawdown＝うちの n本高値（同「n 本最高値からの乖離%」）と近い。
    #   まこさんの決定（2026-08-09・逐語「1,2,3,4全部いれないくていい」）＝この3件も入れない。
    "drawdown": "うちの n本高値（n 本最高値からの乖離%）と同じことを見る＝重複",
    "log_return": "うちの ROC（n 本前からの変化率%）の対数版＝重複",
    "percent_return": "うちの ROC（n 本前からの変化率%）と同じ＝重複",
    # (c) 条件を組み立てる補助＝指標ではなく道具
    "increasing": "値が増えているかの判定＝条件を組む道具", "decreasing": "値が減っているかの判定＝同上",
    "long_run": "上げが続いているかの判定＝同上", "short_run": "下げが続いているかの判定＝同上",
    "tsignals": "トレンドから売買の合図を作る道具", "xsignals": "交差から売買の合図を作る道具",
    "decay": "値を時間で減衰させる道具", "edecay": "同上（指数で減衰）",
    "ma": "移動平均の種類を名前で選ぶ振り分け＝指標そのものではない",
}


def industry_gap(lib_funcs: dict[str, list[str]], families: list[str]) -> dict:
    """業界のライブラリの関数一覧と、うちの材料の突き合わせ。
    lib_funcs＝{カテゴリ名: [関数名, ...]}（pandas-ta-classic の Category をそのまま渡す）。
    families＝参照表の family の一覧。戻り値は数と一覧だけ＝判定はしない。"""
    all_fn = {fn: cat for cat, fns in lib_funcs.items() for fn in fns}
    ng: list[str] = []
    for f in dict.fromkeys(families):
        if f not in INDUSTRY_MAP:
            ng.append(f"対応表 INDUSTRY_MAP に family『{f}』が無い（足すか、無いなら空のタプルと理由を書く）")
    covered: dict[str, list[str]] = {}
    for f, (fns, _note) in INDUSTRY_MAP.items():
        for fn in fns:
            if fn not in all_fn:
                ng.append(f"対応表が指す関数『{fn}』（family {f}）がライブラリに無い＝表が古い")
            else:
                covered.setdefault(fn, []).append(f)
    for fn in INDUSTRY_SKIP:
        if fn not in all_fn:
            ng.append(f"入れない候補の『{fn}』がライブラリに無い＝表が古い")
    missing = [fn for fn in all_fn if fn not in covered]
    skip = [fn for fn in missing if fn in INDUSTRY_SKIP]
    add = [fn for fn in missing if fn not in INDUSTRY_SKIP]
    return dict(ng=ng, all_fn=all_fn, covered=covered, missing=missing, skip=skip, add=add)


# ══ 名前つき定数レジストリ（G6・設計書 §2.4-②・出典必須・レジストリに無い名前は使えない）══════
# 教科書の固定水準＋本プロジェクトの物理定数。値の一覧は §11-11 でまこさんの承認を受ける。
# ★12件 まこさん承認 2026-08-01（逐語「調整の出発点となる仮の値ということであればOK」）＝承認の前提:
#   この定数は固定値ではなく探索の出発点となる仮の値。探索が入れ替え・倍率で調整し、最終の採否は
#   採点窓 score.py とまこさんの判断で決まる。名前の追加・削除は再承認が要る（worklog 20260801 §18）。
# 実装定数（SCALP_FLOOR 等）はレジストリの値が実体とずれないよう const_registry_live_check で機械照合する。
CONST_REGISTRY: dict[str, dict] = {
    "RSI_OB": dict(value=70.0, imi="RSI の買われ過ぎ水準", source="Wilder 1978（technical KB §4）"),
    "RSI_OS": dict(value=30.0, imi="RSI の売られ過ぎ水準", source="Wilder 1978（technical KB §4）"),
    "STOCH_OB": dict(value=80.0, imi="Stochastic の買われ過ぎ水準", source="Lane（technical KB §4）"),
    "STOCH_OS": dict(value=20.0, imi="Stochastic の売られ過ぎ水準", source="Lane（technical KB §4）"),
    "ADX_TREND": dict(value=25.0, imi="ADX のトレンド成立の目安", source="Wilder 1978（technical KB §4）"),
    "NEUTRAL_0": dict(value=0.0, imi="差・乖離系の中立点", source="指標の定義（中立点）"),
    "MID_50": dict(value=50.0, imi="0〜100 型オシレーターの中立点", source="指標の定義（中立点）"),
    "FULL_100": dict(value=100.0, imi="0〜100 型オシレーターの上端", source="指標の定義"),
    "SCALP_FLOOR": dict(value=0.0008, imi="TP 武装の手数料床 0.08%（maker 往復の約2.9倍）",
                        source="e37_scalp.py SCALP_FLOOR（a-priori・exchange_spec H4 から逆算）"),
    "V11_SL_BUF": dict(value=0.0005, imi="反対側ゾーン手前バッファ 0.05%（ゾーンのすぐ外）",
                       source="e37_scalp.py V10_SL_BUF（KB §4・a-priori）"),
    "BE_TTL_BARS": dict(value=24.0, imi="建値フロア待機の TTL（5分×24本＝120分・v31 型）",
                        source="e38_logic_parts.py BE_TTL_BARS（v31 と同一）"),
    "TOL_SR": dict(value=0.003, imi="サポレジ・タッチ判定の許容幅 0.3%",
                   source="observe_config sr_tol（S-Rタッチ数と同じ幅）"),
}


def const_registry_live_check(live: dict[str, float]) -> list[str]:
    """実装定数とレジストリの値のずれを機械照合する（ずれ＝どちらかが黙って動いた＝止める）。
    live＝{定数名: 実体の値}（呼び出し側が実モジュールから渡す＝ここで import しない）。"""
    ng = []
    for name, v in live.items():
        r = CONST_REGISTRY.get(name)
        if r is None:
            ng.append(f"定数レジストリに未登録: {name}（レジストリに無い名前は使えない・G6）")
        elif abs(float(r["value"]) - float(v)) > 1e-12:
            ng.append(f"定数レジストリと実体がずれている: {name} レジストリ {r['value']} 実体 {v}")
    return ng


# ══ 時間帯の材料列（E-j・カレンダー由来＝因果性自明）と ポジション状態列（設計書 §6 fire の材料）══
TIME_REF: dict[str, dict] = {
    "時刻": dict(teigi="バー開始時刻の時（0〜23・UTC）", ryugi="カレンダー由来＝計算なし・因果性自明",
               houkou="状態量（セッションの癖の材料）"),
    "曜日": dict(teigi="バー開始時刻の曜日（0=月〜6=日）", ryugi="同上", houkou="状態量"),
}
# ポジション状態列（出口 fire の材料・入口の条件には使えない＝建玉が無いと定義できない）。
# 値の体系は 設計書 §2.4＝分位不可（自己参照）＝名前つき定数の倍数か整数グリッドだけ。
# ★mfe_prev_pct（2026-08-02 歩6-1 里程標6 で追加）＝mfe_pct と同じ含み益の率だが、当該バーを含めず
#   「前のバーまで」で測る。理由＝S1 の切る枝（v53 等）は同一バーの高値を含めると楽観になるため、
#   実装（e37_scalp 1179行 pk_prev）が前バーまでのピークで判定している。その写しに要る（H2 の型）。
# ★trend_caught（2026-08-02 歩6-1 里程標9 で追加）＝この玉が「上げトレンドに捕まった玉」かどうか（1/0）。
#   上げトレンドの判定が立ったバーで、玉を成行で投げずに印だけ付けて保持する形（e37_scalp 1109-1115行）。
#   印を付けるのは位置の出口 uptrend_cut（mode=mark）で、印が付いた玉だけに当たる出口の枝が2本ある
#   （建値から 0.08% 下の指値で利確する TREND_CAUGHT_TP と、含み益が出ないまま30分たった玉を切る
#    MFE_STALE_CUT）。値は 1 か 0 だけ＝しきい値の探索対象にはしない（枝の scope で使う）。
STATE_COLS = ("unreal_pct", "mfe_pct", "mfe_prev_pct", "mae_pct", "peak_age_bars", "hold_min",
              "add_count", "dist_be_pct", "trend_caught")


def tokenize_ec(line: str) -> list[tuple[str, str]]:
    """E-c の1行を（カテゴリ, 項目）の一覧にする。項目の区切りは半角スラッシュ・括弧の中は割らない。"""
    body = line.split("**:", 1)[1] if "**:" in line else line
    out = []
    for chunk in body.split("／"):
        chunk = chunk.strip()
        if "＝" not in chunk:
            continue
        cat, items = chunk.split("＝", 1)
        buf, depth = "", 0
        toks = []
        for ch in items:
            if ch in "（(":
                depth += 1
            elif ch in "）)":
                depth -= 1
            if ch == "/" and depth == 0:
                toks.append(buf)
                buf = ""
            else:
                buf += ch
        toks.append(buf)
        out += [(cat.strip(), t.strip()) for t in toks if t.strip()]
    return out


def axis_ec_check(ec_line: str, impl_names: list[str]) -> tuple[list[str], list[dict]]:
    """検査7 の本体＝E-c の実文と AXIS_EC 対応表と実装列名の3者を機械照合する。
    戻り値＝(❌一覧, 表示行)。未実装・部分は ❌ でなく表示行の status で出す（判断はまこさん）。"""
    ng, rows = [], []
    toks = tokenize_ec(ec_line)
    table = {(e["cat"], e["token"]): e for e in AXIS_EC}
    for key in [k for k in toks if k not in table]:
        ng.append(f"E-c に在るが対応表に無い: {key[0]}＝{key[1]}（E-c を変えたら AXIS_EC も直す）")
    for key in [k for k in table if k not in toks]:
        ng.append(f"対応表に在るが E-c に無い: {key[0]}＝{key[1]}（E-c から消えた＝表の直し忘れ）")
    for e in AXIS_EC:
        hit, miss = [], []
        for pat in e["impl"]:
            names = [n for n in impl_names if re.match("^" + pat, n)]
            (hit if names else miss).append(pat)
        if e["impl"] and miss:
            ng.append(f"対応表は実装ありと言うが列が無い: {e['token']} → {miss}")
        rows.append(dict(cat=e["cat"], token=e["token"], status=e["status"],
                         n=sum(len([n for n in impl_names if re.match('^' + p, n)]) for p in e["impl"]),
                         note=e["note"]))
    return ng, rows
