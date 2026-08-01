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
   "時間の順位と価格の順位の相関（Spearman）×100。−100〜+100", "日本のテクニカルで標準。同値の順位は平均順位",
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
   "順張り値＝プラスで直近の上げが平常より強い", "trend", tb=_tb_zscore_ret,
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
   "n 本窓の最高値から何本たったか", "標準", "状態量", "none", tb=_tb_bars_since_high,
   known=lambda p: [(_mk(c=np.full(p[0] + 20, 100.0), o=np.full(p[0] + 20, 100.0),
                         h=np.r_[np.full(p[0] + 9, 100.0), 110.0, np.full(10, 100.0)],
                         l=np.full(p[0] + 20, 99.0)), [(-1, 10.0, 1e-9)])])
_r(r"安値からの経過バー(\d+)", "安値からの経過バー",
   "n 本窓の最安値から何本たったか", "標準", "状態量", "none", tb=_tb_bars_since_low,
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
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 0))
_r(r"close vs VAH%(\d+)", "VAH",
   "バリューエリア上端（出来高上位70%帯の上端）からの乖離%", "Market Profile。25分割の近似",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 1))
_r(r"close vs VAL%(\d+)", "VAL",
   "バリューエリア下端からの乖離%", "Market Profile。25分割の近似",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 2))
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


def lineage_coverage(families: list[str]) -> list[str]:
    """系統マップに載っていない family の一覧（空であるべき＝載っていない family は生成不可・G3）。"""
    return [f for f in dict.fromkeys(families) if f not in FAMILY_LINEAGE]


# ══ 名前つき定数レジストリ（G6・設計書 §2.4-②・出典必須・レジストリに無い名前は使えない）══════
# 教科書の固定水準＋本プロジェクトの物理定数。値の一覧は §11-11 でまこさんの承認を受ける。
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
STATE_COLS = ("unreal_pct", "mfe_pct", "mae_pct", "peak_age_bars", "hold_min", "add_count", "dist_be_pct")


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
