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
