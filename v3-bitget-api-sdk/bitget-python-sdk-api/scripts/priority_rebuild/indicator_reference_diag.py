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

import math
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
    k = int(p[1]) if len(p) > 1 else 5      # 名前に本数が無い＝何も渡さないときの 5 本
    e = _ema_rec(d.close.to_numpy(float), p[0])
    out = np.full(len(e), np.nan)
    out[k:] = (e[k:] - e[:-k]) / e[:-k] * 100
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


def _tb_fractal(d, k: int, is_high: bool):
    """山と谷を、素直な繰り返し（1バーずつ）で確定させる（2026-08-21・M2-2-6）。

    ★observe_diag のまとめ計算とは別の書き方＝これで照合になる（同じ書き方を2回 書いても照合にならない）。
    ★未来を見ない＝バー t で使うのは t までの値だけ。中央のバー j＝t−k が前後 k本 より高い（安い）とき、
      バー t で初めて「バー j は山（谷）だった」と分かる。＝実例の「j+2 確定」（k=2）と同じ。
    戻り＝(直近で確定した水準, その1つ前に確定した水準)。
    """
    k = int(k)
    s = (d.high if is_high else d.low).to_numpy(float)
    n = len(s)
    last = np.full(n, np.nan)
    prev = np.full(n, np.nan)
    cur_last, cur_prev = np.nan, np.nan
    for t in range(n):
        j = t - k
        if j - k >= 0:
            mid = s[j]
            lft, rgt = s[j - k:j], s[j + 1:j + k + 1]
            ok = (mid > lft.max() and mid > rgt.max()) if is_high else (mid < lft.min() and mid < rgt.min())
            if ok:
                cur_prev, cur_last = cur_last, mid
        last[t], prev[t] = cur_last, cur_prev
    return last, prev


def _tb_fr_hi_dist(d, p):
    return _S((d.close.to_numpy(float) / _tb_fractal(d, p[0], True)[0] - 1) * 100, d)


def _tb_fr_lo_dist(d, p):
    return _S((d.close.to_numpy(float) / _tb_fractal(d, p[0], False)[0] - 1) * 100, d)


def _tb_fr_hi_step(d, p):
    a = _tb_fractal(d, p[0], True)
    return _S((a[0] / a[1] - 1) * 100, d)


def _tb_fr_lo_step(d, p):
    a = _tb_fractal(d, p[0], False)
    return _S((a[0] / a[1] - 1) * 100, d)


def _tb_fr_break(d, p):
    return _S((d.close.to_numpy(float) / _tb_fractal(d, p[0], False)[1] - 1) * 100, d)


def _fr_case(k: int, hi: bool, first: float, second: float):
    """山（谷）がちょうど2回 確定する見本。終値はずっと 100。

    並び＝[100 が k本][1つ目の山（谷）][100 が k+1本][2つ目の山（谷）][100 が k+3本]。
    間を k+1本 あけるので、2つとも前後 k本 より高い（安い）＝両方が確定する。最後のバーでは
    直近の水準＝2つ目・1つ前の水準＝1つ目 になる。
    """
    k = int(k)
    base = 100.0
    ext = np.r_[np.full(k, base), first, np.full(k + 1, base), second, np.full(k + 3, base)]
    flat = np.full(len(ext), base)
    return _mk(c=flat, o=flat,
               h=(ext if hi else flat + 1.0), l=(flat - 1.0 if hi else ext))


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
        p = int(np.argsort(agg)[::-1][0])     # 同量の帯は価格の高い側を採る（カタログの決めに合わせる）
        tot = max(agg.sum(), 1e-9)
        lo, hi, acc = p, p, agg[p]
        # POC から隣の区画のうち多い方を1つずつ足す（CQG・TradingView の作り・監査 CP60）
        while acc / tot < 0.7 and (lo > 0 or hi < 23):
            up = agg[hi + 1] if hi < 23 else -1.0
            dn = agg[lo - 1] if lo > 0 else -1.0
            if up > dn or (up == dn and (hi + 1 - p) <= (p - lo + 1)):
                hi += 1
                acc += agg[hi]
            else:
                lo -= 1
                acc += agg[lo]
        poc[i] = centers[p]
        vah[i] = centers[hi]
        val[i] = centers[lo]
    return poc, vah, val


def _tb_vs_vp(d, p, which):
    n = p[0]
    c = d.close.to_numpy(float)
    lv = _vp_ref(d, n)[which]
    return _S((c / lv - 1) * 100, d)


def _tb_sr_touch_atr1h(d, p):
    """S-Rタッチ1時間ATR の教科書の式（2026-09-26・M2-E-4c・観察の実装を使わずに書いた独立の実装）。

    ①5分足を「時刻を1時間で切り捨てた値」で束ねて1時間足を作る（高値＝最大・安値＝最小・終値＝最後）
    ②1時間足の TR＝max(高値−安値, |高値−前の終値|, |安値−前の終値|)。最初の1本は 高値−安値
    ③ATR＝Wilder の平滑（最初は TR・以後（前の ATR ×(期間−1) ＋ TR）÷ 期間）。ATR%＝ATR ÷ その1時間足の終値
    ④各バーに、そのバーが閉じた時刻（始まり＋5分）までに閉じた1時間足（始まり＋1時間 ≦ それ）のうち、
      いちばん新しいものの ATR% を当てる
    ⑤許容幅＝倍率 × ATR% を 0.15%〜0.6% に収める。タッチの数え方は _tb_sr_touch と同じ
    ★5分足の並びにだけ使う（検査3 と番人 T-A2 が5分足で呼ぶ）。
    """
    n, k, an = int(p[0]), float(p[1]), int(p[2])
    o, h, l, c, v = _arr(d)
    starts, groups = [], []
    for i, t in enumerate(d.index.floor("h")):
        if not starts or starts[-1] != t:
            starts.append(t)
            groups.append([i])
        else:
            groups[-1].append(i)
    hh = np.array([h[g].max() for g in groups])
    hl = np.array([l[g].min() for g in groups])
    hc = np.array([c[g[-1]] for g in groups])
    atr = np.full(len(groups), np.nan)
    for j in range(len(groups)):
        if j == 0:
            atr[j] = hh[j] - hl[j]
        else:
            tr = max(hh[j] - hl[j], abs(hh[j] - hc[j - 1]), abs(hl[j] - hc[j - 1]))
            atr[j] = (atr[j - 1] * (an - 1) + tr) / an
    pct = atr / hc
    closes = (pd.DatetimeIndex(starts) + pd.Timedelta("1h")).values
    pos = np.searchsorted(closes, (d.index + pd.Timedelta("5min")).values, side="right") - 1
    out = np.full(len(c), np.nan)
    for i in range(n, len(c)):
        if pos[i] < 0:
            continue
        t = min(max(k * pct[pos[i]], 0.0015), 0.006)
        band = c[i] * t
        out[i] = float(np.sum((h[i - n:i] >= c[i] - band) & (l[i - n:i] <= c[i] + band)))
    return _S(out, d)


def _known_sr_touch_atr1h(p):
    """S-Rタッチ1時間ATR の手計算の既知答え3件（2026-09-26・M2-E-4c）。

    ①下端に張り付く＝n＋12本を 100.1 で平ら（始値＝高値＝安値＝終値）・最後の1本だけ 100.0。
      1時間足の値動きの幅は0＝許容幅は下端 0.15%＝帯は 100±0.15。窓の n 本は全部 100.1＝全部 触れる → n
    ②上端に張り付く＝n＋12本を 終値 101.8・高値 104.8・安値 100.8、最後の1本だけ 100.0。
      1時間足の値動きの幅は 4.0（高値−安値）＝ATR% は 4÷101.8（約3.9%）。倍率 0.5 でも上端 0.6% に張り付く。
      帯は 100±0.6＝窓の安値 100.8 は 100.6 より上＝1本も触れない → 0
    ③1時間足と5分足で答えが割れる＝60時間ぶん、1時間ごとに 100.0 と 100.5 を交互に（1時間の中は平ら）、
      最後の1本だけ 100.0。1時間足の TR は2本目から 0.5＝ATR＝0.5×(1−(1−1/期間)^59)。
      最後に閉じた1時間足（60本目）は 100.5 で閉じる。許容幅＝倍率 × ATR ÷ 100.5 を上下限で挟む。
      窓の n 本の半分は 100.0（必ず触れる）・半分は 100.5（許容幅が 0.5% 以上のときだけ触れる）。
      ★5分足の ATR% で数えると、1時間の中は平らなので値動きの幅が小さく、許容幅は下端に張り付く
        ＝倍率 1.5 でも 100.5 に届かない＝この見本が「どの足の ATR で測ったか」を見分ける。
    """
    n, k, an = int(p[0]), float(p[1]), int(p[2])
    c1 = np.r_[np.full(n + 12, 100.1), 100.0]
    c2 = np.r_[np.full(n + 12, 101.8), 100.0]
    h2 = np.r_[np.full(n + 12, 104.8), 100.0]
    l2 = np.r_[np.full(n + 12, 100.8), 100.0]
    m = 60
    c3 = np.r_[np.repeat([100.0 + 0.5 * (j % 2) for j in range(m)], 12), 100.0]
    a3 = 0.5 * (1.0 - (1.0 - 1.0 / an) ** (m - 1))
    t3 = min(max(k * a3 / 100.5, 0.0015), 0.006)
    e3 = n / 2 + (n / 2 if 100.0 * t3 >= 0.5 else 0.0)
    return [(_mk(c1, o=c1, h=c1, l=c1), [(-1, float(n), 1e-9)]),
            (_mk(c2, o=c2, h=h2, l=l2), [(-1, 0.0, 1e-9)]),
            (_mk(c3, o=c3, h=c3, l=c3), [(-1, float(e3), 1e-9)])]


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
    return e.pct_change(int(p[1]) if len(p) > 1 else 5) * 100


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
    "n本高値": (lambda d, p: (d.close / _pta.donchian(d.high, d.low, lower_length=int(p[0]), upper_length=int(p[0])).iloc[:, 2].shift(1) - 1) * 100, "pandas-ta"),
    "n本安値": (lambda d, p: (d.close / _pta.donchian(d.high, d.low, lower_length=int(p[0]), upper_length=int(p[0])).iloc[:, 0].shift(1) - 1) * 100, "pandas-ta"),
    "fib位置": (_x2_fib, "pandas-ta"),
    "RCI": (_x2_rci, "scipy"),
    # ★2026-10-07（工事 m2c15-period-textbook-20261007）＝当日VWAP は pandas-ta の vwap（anchor="D"）と同じ作り
    "当日VWAP": (lambda d, p: (d.close / _pta.vwap(d.high, d.low, d.close, d.volume, anchor="D") - 1) * 100, "pandas-ta"),
}


def ext2_ready() -> bool:
    """2つ目の照合が使える状態か（ライブラリと道具が両方 入っているか）。"""
    return bool(PTA_OK and SCIPY_OK)


# ══ 参照表（①〜④を1種ずつ）＝ observe_diag の検査3 が読む正本 ═══════════
REFS: list[dict] = []


# ★まこさんの決定の逐語（2026-10-07・工事 m2c15-period-textbook-20261007）＝下の登録の mako の欄に書く（同じ文を11か所に書かないため）。
MAKO_K3 = '2026-10-07 まこさん決定「A」（K-3 を3つの工事に分け、K-3a で監査 CP60 の修正41 の (b)(c) と修正42 の比べる版を、今の版を残して別の材料として足す）＝逐語のファイル ok_k3_split_20261007（工事 m2c15-period-textbook-20261007）'
MAKO_K7 = '2026-10-07 まこさん決定「OK」（K-7 の1番＝前期間pivot の3種に前の週の版を別の材料として足す）＝逐語のファイル ok_k7_pivot_thermo_20261007（m2c15-memo-sort-20261007）'
# ★2026-10-09（工事 m2c15-shape-structure-20261009）＝K-3b の4種と下半分位置の「使う」の決定の逐語（mako の欄に書く）。
MAKO_K3B = '2026-10-09 まこさん「よい」（K-3b の作りの3点＝確定した山・谷の本数 k は名前に出さない引数・SMC_SWEEP の教科書の版はライブラリの 15・1.5 を使わない・下半分位置を使う）＝逐語のファイル ok_k3b_design_20261009（m2c15-k3b-decisions-20261009）。K-3 を3つの工事に分けた まこさん決定「A」＝ok_k3_split_20261007'
# ★2026-10-20（工事 m2c15-band-s1-20261020）＝帯の部品と S1 の部品の「使う」の決定の逐語（mako の欄に書く）。
MAKO_B1S1 = '2026-10-20 まこさん「OK\u3000１〜4もOK」（向きを見る所）と「OK」（3つの決定）＝逐語のファイル ok_direction_20261020・ok_three_points_20261020（m2c15-band-s1-20261020）。帯の部品＝まこさん「絶対につくってほしい」（worklog 20261003 §37）・「1,2OK」「１は案ア」（同 §35）・帯pivot と帯VA は触れた回数を数えない＝まこさん「Aでいい」（ok_pivot_a_20261020）／S1 の部品＝m2_todo.json の M2-C-15 の中身③／2026-10-21 監査 CP83 の修正＝まこさん「修正１は案A」（論文の版と E36 の版の2つ）・「修正７は案B」と「甲」（K は論文の値5つ）・「修正12（Minor）→ウ」（前の週の版の帯pivot）・「修正14は案B」（床は渡した設定から）'
# ★2026-10-11（工事 m2c15-formula-textbook-20261011）＝K-3c の15種の「使う」の決定の逐語（mako の欄に書く）。
MAKO_K3C = '2026-10-11 まこさん「把握してるならよい／指標の修正のゴールに対し、このフェーズでの修正案は正しく、齟齬が無いのであれば進めて良い」（K-3c の作りの5点＝新しい名前は作りの違いだけ・新しいパラメータは名前に出さない引数・式は監査の本文と原典の逐語から・Aberration 原作は別の材料・対応表と既知答えは K-3b と同じ形）＝逐語のファイル ok_k3c_design_20261011（m2c15-formula-textbook-20261011）。K-3 を3つの工事に分けた まこさん決定「A」＝ok_k3_split_20261007。THERMO の EMA の版＝ok_k7_pivot_thermo_20261007'


def _r(pat, family, teigi, ryugi, houkou, prop, tb=None, ext=None, known=None, tol=1e-6, mako=None, tb_kind=None):
    """材料の種類を1つ、定義表に登録する。

    ★mako（2026-09-05・M2-C-4・まこさん決定「案A にします」）＝**まこさんが個別に「使う」と
      決めた材料**に、その決定の逐語と日付を書く欄。既定は None＝既存の登録は1行も変わらない。
      この欄は印（indicator_switch.json）の源の4つ目が機械で読む＝CC が手書きの一覧を作らない。
    ★tb_kind（2026-10-11・K-4・監査 CP60 の修正59）＝独立実装 tb が「教科書から書いた物」か「カタログかライブラリと同じ変形を
      別の書き方で写した物（写し）」かの印。"写し" の登録は、検査3 で独立実装が合っただけでは「一致検証済み」に数えない
      （照合が「自分と同じか」しか確かめていないため）＝手計算の既知答えが要る（観察の道具の自己テストの番人が見る）。
      "教科書"＝教科書の式から書いた物。None＝まだ判定していない（既存の登録は1行も変わらない）。
    """
    REFS.append(dict(pat=re.compile("^" + pat + "$"), family=family, teigi=teigi, ryugi=ryugi,
                     houkou=houkou, prop=prop, tb=tb, ext=ext, known=known, tol=tol, mako=mako, tb_kind=tb_kind))


def _num(g):
    f = float(g)
    return int(f) if f == int(f) and "." not in g else f


_FIND_MEMO: dict = {}


def find(name: str):
    """カタログ名 → (参照エントリ, パラメータのタプル)。無ければ (None, None)。

    ★2026-08-13（段A の A-4）に、一度 調べた名前を覚える形にした（中身は1文字も変えていない）。
      理由＝A-4 でパラメータを範囲から引くようになり、名前の種類が増えた。この関数は
      参照表 250件 の正規表現を上から順に当てるので、呼ぶたびに時間が掛かる
      （実測＝案を30本 作るのに 22.2 秒。うち この関数と、その先の設定ファイルの読み直しで 6.6 秒）。
    """
    hit = _FIND_MEMO.get(name)
    if hit is not None:
        return hit
    out = (None, None)
    for e in REFS:
        m = e["pat"].match(name)
        if m:
            out = (e, tuple(_num(g) for g in m.groups()))
            break
    _FIND_MEMO[name] = out
    return out


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
   "MACD線 − シグナル線（MACD線の EMA）を終値で割って%化",
   "Appel。%化は本プロジェクトの流儀。"
   "★2026-08-11 に「この登録は 状態量＝加速 に直すべきではないか」を実測で確かめた（段6 の 6-9④）。"
   "結果＝直さない。加速の柱で 加速した上げ +0.0008543 ／ 加速した下げ −0.001215＝符号が分かれる"
   "（＝プラスが上げの加速という主張は支持される）。実データの柱では 上げた日 −0.000612 ／ "
   "下げた日 −0.0001865・四分位幅 0.04503＝差は幅の 1% 未満で向きが出ない（加速を測る指標なので、"
   "上げた日と下げた日で差が出ないのが正しい）。★同じ形の PPOヒスト・RVGIヒスト・VWMACDヒスト は "
   "状態量＝加速（向きを持たない）で登録されていて、この列だけ区分が違う。そろえるかどうかは "
   "実測で決める（PPOヒスト 加速上げ +0.0001571／加速下げ −0.007139・RVGIヒスト +0.002105／−0.003796 は"
   "符号が分かれる＝順張り値の側／VWMACDヒスト +0.001163／+0.001312 は分かれない＝状態量の側）",
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
   known=lambda p: [(_up(p[0] + 5), [(-1, 100.0, 1e-9)]), (_dn(p[0] + 5), [(-1, -100.0, 1e-9)])],
   mako="2026-10-04 まこさん指示「V9で使ってる指標は入れるようにしてほしい」（V9 の P22 が RCI7 と RCI9 のクロスを使う）")
_r(r"EMA(\d+)傾き%", "EMA傾き",
   "EMA の何本か前からの変化率%。比べる本数は名前に出さない引数（何も渡さないときは 5 本＝直す前の値）",
   "EMA は標準の漸化式。比べる本数は教科書でも利用者が決めるパラメータ（ChartSchool Slope「The number of days controls the period」）＝名前には出さず、引数で受け取る（まこさん 2026-10-04）",
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
                    (_w_case(int(p[0]), 92.0), [(-1, 0.0, 1e-9)])], tb_kind="写し")
# ── 山と谷（2026-08-21・M2-2-6・受け入れ条件 24a453d6… の C-1 と D）──
_r(r"fractal高値距離%\((\d+)\)", "fractal高値距離%",
   "終値と、直近で確定した山（前後 k本 より高い中央のバー）との乖離%",
   "確定は k本 遅れ＝まこさんの実例の「j+2 確定」（k=2）と同じ形（法則 C10 の②・未来を見ないため）。"
   "%化は価格非依存 H6 のための本プロジェクトの流儀。★rolling の最高値との距離（swing高値距離%・"
   "close vs n本高値%）とは別物＝あちらは窓の中の最高値、こちらは前後が下がった実際の山",
   "順張り値＝0 に近いほど直近の山に近い", "trend", tb=_tb_fr_hi_dist,
   known=lambda p: [(_fr_case(p[0], True, 110.0, 121.0), [(-1, (100.0 / 121.0 - 1) * 100, 1e-9)])])
_r(r"fractal安値距離%\((\d+)\)", "fractal安値距離%",
   "終値と、直近で確定した谷（前後 k本 より安い中央のバー）との乖離%",
   "上と同じ（k本 遅れで確定・%化は H6 のための流儀）",
   "順張り値＝0 に近いほど直近の谷に近い", "trend", tb=_tb_fr_lo_dist,
   known=lambda p: [(_fr_case(p[0], False, 90.0, 81.0), [(-1, (100.0 / 81.0 - 1) * 100, 1e-9)])])
_r(r"高値切り上げ幅%\((\d+)\)", "高値切り上げ幅%",
   "直近で確定した山と、その1つ前に確定した山との差%。プラスなら高値を切り上げている",
   "ダウ理論の Higher High（法則 U1）を1つの数字にしたもの＝本プロジェクトの流儀。真偽にするのは"
   "既存の形（level・cross）＝部品と形を混ぜない",
   "順張り値＝プラスで上昇の構造", "trend", tb=_tb_fr_hi_step,
   known=lambda p: [(_fr_case(p[0], True, 110.0, 121.0), [(-1, 10.0, 1e-9)])])
_r(r"安値切り上げ幅%\((\d+)\)", "安値切り上げ幅%",
   "直近で確定した谷と、その1つ前に確定した谷との差%。プラスなら安値を切り上げている",
   "ダウ理論の Higher Low（法則 U1）／マイナスなら Lower Low（法則 D1）。流儀は上と同じ",
   "順張り値＝プラスで上昇の構造・マイナスで下降の構造", "trend", tb=_tb_fr_lo_step,
   known=lambda p: [(_fr_case(p[0], False, 90.0, 81.0), [(-1, -10.0, 1e-9)])])
_r(r"構造破断距離%\((\d+)\)", "構造破断距離%",
   "終値と、**1つ前に確定した谷**との乖離%。マイナスならその谷を割っている",
   "法則 U9（構造破断）の逐語「close < 直近2本の確定15分安値」を1つの数字にしたもの＝本プロジェクトの流儀。"
   "★直近の谷との距離は fractal安値距離% が持つので、2本を AND で束ねると「直近2本の確定安値を割った」が"
   "そのまま書ける。★受け入れ条件の本文は「直近で確定した谷」と書いてあるが、そのとおりに作ると"
   "fractal安値距離% と1ビットも変わらない重複列になるため、法則 U9 の本文に合わせて1つ前の谷にした"
   "（2026-08-21・M2-2-6）",
   "順張り値＝マイナスで上げの構造が壊れた", "trend", tb=_tb_fr_break,
   known=lambda p: [(_fr_case(p[0], False, 90.0, 81.0), [(-1, (100.0 / 90.0 - 1) * 100, 1e-9)])])
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
   # ★K-4（監査 CP60 の修正59）＝定義（出来高×終値の合計 ÷ 出来高の合計・n 本の移動窓＝流儀の欄）から導いた既知答えを足す。
   #   ①出来高が全部 1 で1本ごとに 1 上げる足＝VWAP は終値の単純平均＝終値 − (n−1)/2
   #   ②同じ足で最後の1本だけ出来高 9＝VWAP＝(n×終値 − n(n−1)/2 ＋ 8×終値) ÷ (n＋8)。出来高の重みを外すと①は通り②だけ落ちる。
   known=lambda p: [(_flat(p[0] + 10), [(-1, 0.0, 1e-9)]),
                    (_up(p[0] + 40), [(-1, ((100.0 + p[0] + 39) / ((100.0 + p[0] + 39) - (p[0] - 1) / 2.0) - 1.0) * 100.0, 1e-9)]),
                    (_mk(100.0 + np.arange(p[0] + 40, dtype=float), v=np.r_[np.ones(p[0] + 39), 9.0]),
                     [(-1, ((100.0 + p[0] + 39) / ((p[0] * (100.0 + p[0] + 39) - p[0] * (p[0] - 1) / 2.0 + 8.0 * (100.0 + p[0] + 39)) / (p[0] + 8.0)) - 1.0) * 100.0, 1e-9)])],
   tb_kind="写し")
# ★2026-10-07（工事 m2c15-period-textbook-20261007・監査 CP60 の修正41 の (b)(c)）＝教科書の VWAP（典型価格）の2つの版。
def _tb_vs_vwap_tp(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    tp = (h + l + c) / 3
    return _S((c / _div(_roll(tp * v, n, "sum"), _roll(v, n, "sum")) - 1) * 100, d)


def _tp_case(n):
    """VWAP典型 の手計算用。全部の足が 高値112・安値100・終値103・出来高1＝典型価格105 → VWAP 105 → 乖離%＝(103÷105−1)×100。
    終値で作る今の版なら VWAP 103 → 0（＝値段の違いを見分ける）。"""
    c = np.full(n, 103.0)
    return _mk(c, o=c, h=np.full(n, 112.0), l=np.full(n, 100.0))


def _vwap_day_case():
    """当日VWAP の手計算用。1日目（3/1・288本）＝終値150・出来高1（積み上げが日で区切れていなければ、ここが混ざる）。
    2日目＝1本目と2本目は 高値112・安値100・終値103（典型価格105）・出来高1、3本目は 高値＝安値＝終値＝99・出来高2。
    2本目の VWAP＝105 → (103÷105−1)×100。3本目の VWAP＝(105＋105＋99×2)÷4＝102 → (99÷102−1)×100。"""
    c = np.r_[np.full(288, 150.0), [103.0, 103.0, 99.0]]
    h = np.r_[np.full(288, 150.0), [112.0, 112.0, 99.0]]
    l = np.r_[np.full(288, 150.0), [100.0, 100.0, 99.0]]
    v = np.r_[np.full(288, 1.0), [1.0, 1.0, 2.0]]
    return _mk(c, o=c, h=h, l=l, v=v)


_r(r"close vs VWAP典型%(\d+)", "close vs VWAP典型",
   "典型価格（(高値＋安値＋終値)÷3）で作る n 本の移動 VWAP からの乖離%",
   "監査 CP60 の修正41 の (b)＝ta の VolumeWeightedAveragePrice の作り（n 本の移動窓＋典型価格）。今の close vs VWAP（終値）とは値段だけが違う",
   "順張り値", "trend", tb=_tb_vs_vwap_tp,
   ext=lambda d, p: (d.close / _ta.volume.VolumeWeightedAveragePrice(d.high, d.low, d.close, d.volume, window=int(p[0]))
                     .volume_weighted_average_price() - 1) * 100,
   known=lambda p: [(_flat(p[0] + 10), [(-1, 0.0, 1e-9)]), (_tp_case(p[0] + 10), [(-1, (103.0 / 105.0 - 1) * 100, 1e-9)])],
   mako=MAKO_K3)
_r(r"close vs 当日VWAP%", "当日VWAP",
   "UTC の日の0時から積み上げる VWAP（典型価格・今の足までを含む）からの乖離%",
   "監査 CP60 の修正41 の (c)＝StockCharts の逐語「VWAP calculations start fresh at the open」「(H+L+C)/3」。pandas-ta の vwap（anchor の既定 D）と同じ作り",
   "順張り値", "trend",
   known=lambda p: [(_vwap_day_case(), [(-2, (103.0 / 105.0 - 1) * 100, 1e-9), (-1, (99.0 / 102.0 - 1) * 100, 1e-9)])],
   mako=MAKO_K3)
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
def _tb_dist_high_prev(d, p):
    o, h, l, c, v = _arr(d)
    return _S((c / _S(_roll(h, p[0], "max"), d).shift(1).to_numpy(float) - 1) * 100, d)


def _tb_dist_low_prev(d, p):
    o, h, l, c, v = _arr(d)
    return _S((c / _S(_roll(l, p[0], "min"), d).shift(1).to_numpy(float) - 1) * 100, d)


_r(r"close vs (\d+)本高値%", "n本高値",
   "前の n 本（今の足を含まない）の最高値からの乖離%",
   "StockCharts Price Channels の逐語「Price Channels are based on prices prior to the current period.」＝今の足を含まない（監査 CP60）",
   "順張り値", "trend", tb=_tb_dist_high_prev,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, (105.0 / 110.0 - 1) * 100, 1e-9)])])
_r(r"close vs (\d+)本安値%", "n本安値",
   "前の n 本（今の足を含まない）の最安値からの乖離%",
   "同上（監査 CP60）", "順張り値", "trend", tb=_tb_dist_low_prev,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, 5.0, 1e-9)])])
# ── 構造 ──
_r(r"close vs pivotPP%(\d+)", "pivotPP",
   "ピボットポイント PP（n 本高値＋n 本安値＋前バー終値の平均）からの乖離%",
   "★流儀に注意＝教科書の PP は前の期間の高値・安値・終値。本カタログは移動窓の高安＋前バー終値の変形",
   "順張り値", "trend", tb=_tb_vs_pivot,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, 0.0, 1e-6)])], tb_kind="写し")
_r(r"close vs pivotR1%(\d+)", "pivotR1",
   "ピボットの抵抗1 R1（2×PP − n 本安値）からの乖離%",
   "★流儀に注意＝教科書の R1 は前の期間の高安・終値から。本カタログは PP と同じ移動窓の変形（2026-07-30 検査7 を受けて追加）。外部照合は定義が違うため対象外",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_pivot_rs(d, p, +1),
   known=lambda p: [(_flat(p[0] + 20), [(-1, 0.0, 1e-9)]),
                    (_range_case(n=max(300, p[0] + 60)), [(-1, (105.0 / 110.0 - 1) * 100, 1e-6)])], tb_kind="写し")
_r(r"close vs pivotS1%(\d+)", "pivotS1",
   "ピボットの支持1 S1（2×PP − n 本高値）からの乖離%",
   "★流儀に注意＝教科書の S1 は前の期間の高安・終値から。本カタログは PP と同じ移動窓の変形（2026-07-30 検査7 を受けて追加）。外部照合は定義が違うため対象外",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_pivot_rs(d, p, -1),
   known=lambda p: [(_flat(p[0] + 20), [(-1, 0.0, 1e-9)]),
                    (_range_case(n=max(300, p[0] + 60)), [(-1, 5.0, 1e-6)])], tb_kind="写し")


def _pivot_day_case():
    """前期間ピボットの手計算用（監査 CP60）。1日目（288本）＝終値105・高値110 が1本・安値100 が1本、2日目＝終値105 が3本。
    PP=(110+100+105)/3=105・R1=2×105−100=110・S1=2×105−110=100。"""
    c = np.full(291, 105.0)
    h = c.copy()
    l = c.copy()
    h[100] = 110.0
    l[200] = 100.0
    return _mk(c, o=c, h=h, l=l)


_r(r"close vs 前期間pivotPP%", "前期間pivotPP",
   "教科書のピボット PP＝前の期間（日中の足は前の UTC の日・日足は前の月・それより長い足は前の年）の（高値＋安値＋終値）÷3 からの乖離%。期間のあいだ線は動かない",
   "StockCharts「Pivot Points」の逐語「the prior day's high, low, and close」「do not change and remain in play throughout the day」。%化は H6",
   "順張り値", "trend", known=lambda p: [(_pivot_day_case(), [(-1, 0.0, 1e-9)])])
_r(r"close vs 前期間pivotR1%", "前期間pivotR1",
   "教科書の R1＝2×PP − 前の期間の安値 からの乖離%", "StockCharts の逐語「Resistance 1 (R1) = (P x 2) - Low」",
   "順張り値", "trend", known=lambda p: [(_pivot_day_case(), [(-1, (105.0 / 110.0 - 1) * 100, 1e-9)])])
_r(r"close vs 前期間pivotS1%", "前期間pivotS1",
   "教科書の S1＝2×PP − 前の期間の高値 からの乖離%", "StockCharts の逐語「Support 1 (S1) = (P x 2) - High」",
   "順張り値", "trend", known=lambda p: [(_pivot_day_case(), [(-1, 5.0, 1e-9)])])


def _pivot_week_case():
    """前週ピボットの手計算用（2026-10-07）。データの始まり 2026-03-01 は日曜＝月曜0時 UTC に始まる週の最後の日。
    1日目（3/1・288本）＝終値105・高値110 が1本・安値100 が1本（_pivot_day_case と同じ）、2日目（3/2 月曜・288本）＝高値＝安値＝終値＝104、
    3日目（3/3）＝終値105 が3本。3日目の前週ピボット＝3/1 の週＝PP 105・R1 110・S1 100 → 乖離% 0・(105÷110−1)×100・5。
    前の日の版なら 3/2 の 104 で作る＝PP=R1=S1=104（＝週と日の取り違えを見分ける）。"""
    c = np.r_[np.full(288, 105.0), np.full(288, 104.0), np.full(3, 105.0)]
    h = c.copy()
    l = c.copy()
    h[100] = 110.0
    l[200] = 100.0
    return _mk(c, o=c, h=h, l=l)


_r(r"close vs 前週pivotPP%", "前週pivotPP",
   "教科書のピボット PP を前の週（月曜0時 UTC に始まる7日）の（高値＋安値＋終値）÷3 で作り、その週のあいだ動かない線からの乖離%",
   "StockCharts の逐語「Pivot Points for 30-, 60-, and 120-minute charts use the prior week's high, low, and close.」。週の始まりは ISO 8601 の月曜",
   "順張り値", "trend", known=lambda p: [(_pivot_week_case(), [(-1, 0.0, 1e-9)])], mako=MAKO_K7)
_r(r"close vs 前週pivotR1%", "前週pivotR1",
   "前の週の R1＝2×PP − 前の週の安値 からの乖離%", "StockCharts の逐語「Resistance 1 (R1) = (P x 2) - Low」",
   "順張り値", "trend", known=lambda p: [(_pivot_week_case(), [(-1, (105.0 / 110.0 - 1) * 100, 1e-9)])], mako=MAKO_K7)
_r(r"close vs 前週pivotS1%", "前週pivotS1",
   "前の週の S1＝2×PP − 前の週の高値 からの乖離%", "StockCharts の逐語「Support 1 (S1) = (P x 2) - High」",
   "順張り値", "trend", known=lambda p: [(_pivot_week_case(), [(-1, 5.0, 1e-9)])], mako=MAKO_K7)
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
                    (_vp_case(int(p[0]), 6, 4), [(-1, _VP_D_LO, 1e-9)])], tb_kind="写し")
_r(r"close vs VAH%(\d+)", "VAH",
   "バリューエリア上端（出来高上位70%帯の上端）からの乖離%", "Market Profile。25分割の近似",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 1),
   # 場合1＝下の区画だけで出来高の91%を占める→上位70%帯は1区画で足りる→上端も下の区画。
   # 場合2＝下の区画は60%しか無い→上位70%帯に上の区画も要る→上端は上の区画。
   known=lambda p: [(_vp_case(int(p[0]), 10, 1), [(-1, _VP_D_LO, 1e-9)]),
                    (_vp_case(int(p[0]), 6, 4), [(-1, _VP_D_HI, 1e-9)])], tb_kind="写し")
_r(r"close vs VAL%(\d+)", "VAL",
   "バリューエリア下端からの乖離%", "Market Profile。25分割の近似",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 2),
   # 下端は どちらの場合も下の区画。
   known=lambda p: [(_vp_case(int(p[0]), 10, 1), [(-1, _VP_D_LO, 1e-9)]),
                    (_vp_case(int(p[0]), 6, 4), [(-1, _VP_D_LO, 1e-9)])], tb_kind="写し")


# ★2026-10-07（工事 m2c15-period-textbook-20261007・監査 CP60 の修正42）＝日で区切る出来高プロファイルの2つの版。
def _vp_day_case(prev: bool, va, vb, n=20):
    """日で区切る出来高プロファイルの手計算用。_vp_case（終値 100 と 200 の2つだけ）を日の区切りに置く＝答えは _vp_case と同じ。
    prev=True（前日の版）＝1日目（3/1・288本）の前半144本＝終値100・出来高 va／後半144本＝終値200・出来高 vb、2日目＝終値100 が3本。
      2日目の線は1日目の足ぜんぶで作る（同じ日の足だけで作ると終値100 だけ＝乖離0 になり見分けられる）。
    prev=False（当日の版）＝1日目（288本）＝終値150・出来高1（日で区切れていなければ、出来高の多いこの値段が線になる）、
      2日目＝_vp_case(n, va, vb) と同じ n＋1本。2日目の最後の足の線は、2日目の0時から1本前までの n 本で作る。"""
    if prev:
        c = np.r_[np.full(144, 100.0), np.full(144, 200.0), np.full(3, 100.0)]
        v = np.r_[np.full(144, float(va)), np.full(144, float(vb)), np.full(3, 1.0)]
        return _mk(c, o=c, h=c, l=c, v=v)
    m = n // 2
    c = np.r_[np.full(288, 150.0), np.full(m, 100.0), np.full(n - m, 200.0), [100.0]]
    v = np.r_[np.full(288, 1.0), np.full(m, float(va)), np.full(n - m, float(vb)), [1.0]]
    return _mk(c, o=c, h=c, l=c, v=v)


for _vpk, _vpw in (("前日", True), ("当日", False)):
    _r(rf"close vs {_vpk}POC%", f"{_vpk}POC",
       f"出来高プロファイルの最厚価格帯 POC（{'前の UTC の日の足ぜんぶ・その日のあいだ固定' if _vpw else 'その日の0時から1本前までの足'}）からの乖離%",
       "監査 CP60 の修正42 の比べる版。区画24・同量なら価格の高い側（今の POC と同じ決まり＝_vp_one）",
       "順張り値", "trend",
       known=lambda p, w=_vpw: [(_vp_day_case(w, 10, 1), [(-1, _VP_D_LO, 1e-9)]), (_vp_day_case(w, 6, 4), [(-1, _VP_D_LO, 1e-9)])],
       mako=MAKO_K3)
    _r(rf"close vs {_vpk}VAH%", f"{_vpk}VAH",
       f"バリューエリア上端（出来高上位70%帯の上端・{'前の UTC の日' if _vpw else 'その日の0時から1本前まで'}）からの乖離%",
       "監査 CP60 の修正42 の比べる版。今の VAH と同じ決まり（_vp_one）",
       "順張り値", "trend",
       known=lambda p, w=_vpw: [(_vp_day_case(w, 10, 1), [(-1, _VP_D_LO, 1e-9)]), (_vp_day_case(w, 6, 4), [(-1, _VP_D_HI, 1e-9)])],
       mako=MAKO_K3)
    _r(rf"close vs {_vpk}VAL%", f"{_vpk}VAL",
       f"バリューエリア下端（{'前の UTC の日' if _vpw else 'その日の0時から1本前まで'}）からの乖離%",
       "監査 CP60 の修正42 の比べる版。今の VAL と同じ決まり（_vp_one）",
       "順張り値", "trend",
       known=lambda p, w=_vpw: [(_vp_day_case(w, 10, 1), [(-1, _VP_D_LO, 1e-9)]), (_vp_day_case(w, 6, 4), [(-1, _VP_D_LO, 1e-9)])],
       mako=MAKO_K3)
# ★2026-09-06（再監査 cp22 の N-1）＝S-RタッチATR の登録を外した。
#   理由＝実装が出どころの逐語（`tol=clamp(K×ATR%_1h,…)`＝1時間足）と違い、渡された足の ATR% を
#   使っていた。5分足では許容幅が下端 0.15% に張り付き、既存の S-Rタッチ数(288,0.0015) と
#   同じ列になった（観察の検査12 で相関 +0.9999978）。正しい形は M2-E で作る。
_SR_TOUCH_ATR_REMOVED = """（この節は 2026-09-06 に外した登録の控え。次に作る人が参照するために残す）
   名前の形＝S-RタッチATR(窓, 倍率, ATRの期間)
   定義＝いまの価格の帯に、過去 n 本の高安が何回触れたか。許容幅が『値動きの幅 × 倍率』で 0.15%〜0.6% に収まる
   ★外した理由＝許容幅を『渡された足の ATR%』で計算していた。出どころの逐語は『ATR%_1h』（1時間足）。
     5分足では下端 0.15% に張り付き、既存の S-Rタッチ数(288,0.0015) と実質 同じ列になった。
   ★既知答え2水準（0.5% と 1.0%）の作り方は、正しい形を M2-E で作るときに再利用する。
"""
_r(r"MMI(\d+)", "MMI",
   "値動きがランダムに近いかの割合（0〜100）。n 本の中央値より上でかつ前の値より上がった、または"
   "中央値より下でかつ前の値より下がった本数の割合。高いほどレンジ寄り",
   "The Financial Hacker「The Market Meanness Index」の本文の C のコードのとおり。"
   "うちの自前の実装（ta にも pandas-ta にも無い）",
   "状態量＝方向は持たない（原典の逐語『向きは測りません』）", "none",
   # ★手計算の既知答え3件（2026-09-05・監査 cp21 の C2 で作り直した）。
   #   ★直す前の2件（全部 同じ／1つ飛ばしに上下）は、**向きを逆にしても同じ答えになる見本**だった
   #     ＝原典と向きが違う実装を、この既知答えでは1件も捕まえられなかった（監査が実測）。
   #   ★いまの3件目が、向きの違いを捕まえる見本。
   #   ①終値が全部 同じ＝中央値と等しい＝「より上」でも「より下」でもない＝1本も数えない → 0
   #   ②1つ飛ばしに上下（100→101→100→101…）＝どの対も条件に当たる＝n-1 本 全部 → 100
   #   ③**最初の1本だけ 0・残りが全部 1**（★向きで答えが割れる見本）
   #     中央値＝1。原典の数え方（対の古い側に条件を付ける＝その値が「次の値」と比べてどうか）では、
   #     最古の 0 が「次の 1 より小さい」の1本だけ当たる → 100 ÷ (n−1)。
   #     ★向きを逆にした実装（前の値と比べる）だと、その 0 は窓の先頭で相手がいないので **0** になる。
   known=lambda p: [
       (_mk(np.full(int(p[0]) + 5, 100.0)), [(-1, 0.0, 1e-9)]),
       (_mk(np.array([100.0 + (i % 2) for i in range(int(p[0]) + 5)])), [(-1, 100.0, 1e-9)]),
       (_mk(np.array([0.0] + [1.0] * (int(p[0]) - 1))),
        [(-1, 100.0 / (int(p[0]) - 1), 1e-9)]),
   ],
   mako="2026-09-05 まこさん決定（案A・M2-C-4）＝材料の一覧の3つ目の源「まこさんが個別に決めたもの」")
# ★2026-09-26（M2-E-4c・束2）＝S-Rタッチ1時間ATR を足した。2026-09-06 に外した S-RタッチATR（上の控え
#   _SR_TOUCH_ATR_REMOVED）を、出どころの逐語どおり「1時間足の ATR%」で作り直したもの。名前は別にした。
_r(r"S-Rタッチ1時間ATR\((\d+),([\d.]+),(\d+)\)", "S-Rタッチ1時間ATR",
   "いまの価格の許容幅つき帯に、過去 n 本の高安が何回触れたか。許容幅＝倍率 × 1時間足の ATR%"
   "（ATR ÷ その1時間足の終値）を 0.15%〜0.6% に収めたもの",
   "出どころの逐語『tol=clamp(K×ATR%_1h,0.15%,0.6%)』（設定 observe_config.json の sr_tol の説明に写してある）。"
   "1時間足の値は、その1時間足が閉じた時刻から使う。タッチは、その足の高値・安値で数える",
   "状態量＝多いほど節が固い", "none", tb=_tb_sr_touch_atr1h, known=_known_sr_touch_atr1h,
   mako="2026-09-05 まこさん決定「1・2・4・5・6 を足す」の⑤（ATR に連動する帯の許容幅）"
        "＋2026-09-06「2-Eへ送るので、2-Eで忘れないように書いておいて」"
        "＋2026-09-26「CCの案の通りで進める」「BでOK」（M2-E-4c・束2）")
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
                     [(-1, 3.0, 1e-9)]),
                    # ★K-4（監査 CP60 の修正59）＝帯の外の既知答え＝前の n 本が全部 50 で最後の1本だけ 100（帯は 100±許容幅）＝触れる足は 0
                    (_mk(np.r_[np.full(int(p[0]) + 12, 50.0), 100.0], o=np.r_[np.full(int(p[0]) + 12, 50.0), 100.0],
                         h=np.r_[np.full(int(p[0]) + 12, 50.0), 100.0], l=np.r_[np.full(int(p[0]) + 12, 50.0), 100.0]),
                     [(-1, 0.0, 1e-9)])], tb_kind="写し")


# ★2026-10-09（工事 m2c15-shape-structure-20261009・K-3b・監査 CP60 の修正43・44・46）＝確定した山・谷で作る教科書の版。
#   独立の実装は、確定した山・谷を素直な繰り返し（_tb_fractal と同じ決まり）で作る＝観察の道具のまとめ計算とは別の書き方。
def _tb_fractal_marks(d, k, is_high):
    """確定した山（谷）の値段を、確定した足（中央の足 j の k 本 後）にだけ置いた並び。"""
    k = int(k)
    s = (d.high if is_high else d.low).to_numpy(float)
    out = np.full(len(s), np.nan)
    for t in range(len(s)):
        j = t - k
        if j - k >= 0:
            mid, lft, rgt = s[j], s[j - k:j], s[j + 1:j + k + 1]
            if (mid > lft.max() and mid > rgt.max()) if is_high else (mid < lft.min() and mid < rgt.min()):
                out[t] = mid
    return out


def _tb_w_fr(d, p, k=2):
    n, tol = int(p[0]), float(p[1])
    o, h, l, c, v = _arr(d)
    lv = _tb_fractal_marks(d, k, False)
    out = np.full(len(c), np.nan)
    tl = []
    for i in range(len(c)):
        if lv[i] == lv[i]:
            tl.append(i)
        if i < n - 1:
            continue
        out[i] = 0.0
        if len(tl) < 2:
            continue
        t1, t2 = tl[-2], tl[-1]
        j1, j2 = t1 - k, t2 - k
        if j1 < i - n + 1 or j2 - j1 < 2 or abs(lv[t1] - lv[t2]) > tol * c[i]:
            continue
        neck = max(h[j1 + 1:j2])
        if c[i] > neck and all(c[x] <= neck for x in range(j2 + 1, i)):
            out[i] = 1.0
    return _S(out, d)


def _w_case2(n):
    """W字確定谷 の「最初に上抜けた足だけ 1」の既知答え用。_w_case(n, 100.2) と同じ並びで、最後の2本の終値を 109 にする
    ＝1本前が最初の上抜け（1）・最後の足は2回目（0）。今の W字 なら最後の足も 1（条件が続く間ずっと1）。"""
    half, q = n // 2, (n // 2) // 2
    m = n + 6
    c = np.full(m, 106.0)
    h = np.full(m, 106.0)
    l = np.full(m, 105.0)
    base = m - n
    l[base + 2] = 100.0
    h[base + half] = 108.0
    l[base + half + q + 1] = 100.2
    c[-2:] = 109.0
    return _mk(c=c, o=c.copy(), h=np.maximum(h, c), l=np.minimum(l, c))


def _tb_sr_fr(d, p, k=2):
    n, tol = int(p[0]), float(p[1])
    o, h, l, c, v = _arr(d)
    hv, lv = _tb_fractal_marks(d, k, True), _tb_fractal_marks(d, k, False)
    out = np.full(len(c), np.nan)
    for i in range(n, len(c)):
        band = c[i] * tol
        out[i] = float(np.sum(np.abs(hv[i - n:i] - c[i]) <= band) + np.sum(np.abs(lv[i - n:i] - c[i]) <= band))
    return _S(out, d)


def _tb_sr_fr_atr1h(d, p, k=2):
    """S-Rタッチ確定1時間ATR の独立の実装。許容幅（1時間足の ATR%・0.15%〜0.6%）は _tb_sr_touch_atr1h の①〜⑤と同じ書き方、
    数え方は _tb_sr_fr（確定した山・谷）。"""
    n, km, an = int(p[0]), float(p[1]), int(p[2])
    o, h, l, c, v = _arr(d)
    starts, groups = [], []
    for i, t in enumerate(d.index.floor("h")):
        if not starts or starts[-1] != t:
            starts.append(t)
            groups.append([i])
        else:
            groups[-1].append(i)
    hh = np.array([h[g].max() for g in groups])
    hl = np.array([l[g].min() for g in groups])
    hc = np.array([c[g[-1]] for g in groups])
    atr = np.full(len(groups), np.nan)
    for j in range(len(groups)):
        if j == 0:
            atr[j] = hh[j] - hl[j]
        else:
            tr = max(hh[j] - hl[j], abs(hh[j] - hc[j - 1]), abs(hl[j] - hc[j - 1]))
            atr[j] = (atr[j - 1] * (an - 1) + tr) / an
    pct = atr / hc
    closes = (pd.DatetimeIndex(starts) + pd.Timedelta("1h")).values
    pos = np.searchsorted(closes, (d.index + pd.Timedelta("5min")).values, side="right") - 1
    hv, lv = _tb_fractal_marks(d, k, True), _tb_fractal_marks(d, k, False)
    out = np.full(len(c), np.nan)
    for i in range(n, len(c)):
        if pos[i] < 0:
            continue
        band = c[i] * min(max(km * pct[pos[i]], 0.0015), 0.006)
        out[i] = float(np.sum(np.abs(hv[i - n:i] - c[i]) <= band) + np.sum(np.abs(lv[i - n:i] - c[i]) <= band))
    return _S(out, d)


def _sr_fr_case(n):
    """S-Rタッチ確定数・S-Rタッチ確定1時間ATR の既知答え用（2026-10-09・K-3b）。n＋12 本の平らな足（始値＝高値＝安値＝終値＝100）に、
    確定する山を3つ（100.1・101・100.1）と谷を1つ（99.9）置く。最後の足の終値 100 の帯（許容幅 0.15%〜0.6%＝±0.15〜±0.6）に入るのは
    100.1 の山2つと 99.9 の谷1つ＝3。101 の山は帯の外。最後の足の2本前にも 100.1 の山を置くが、確定は最後の足（窓 [i−n, i) の外）なので数えない。
    今の S-Rタッチ数 なら、窓の n 本が全部 100 に触れる＝n（数え方の違いを見分ける）。"""
    m = n + 12
    c = np.full(m, 100.0)
    h = c.copy()
    l = c.copy()
    i = m - 1
    h[i - 20] = 100.1
    h[i - 15] = 101.0
    h[i - 10] = 100.1
    l[i - 5] = 99.9
    h[i - 2] = 100.1
    return _mk(c=c, o=c.copy(), h=h, l=l)


def _tb_smc_fr(d, p, k=2):
    o, h, l, c, v = _arr(d)
    hl_, _p1 = _tb_fractal(d, k, True)
    ll_, _p2 = _tb_fractal(d, k, False)
    out = np.full(len(c), np.nan)
    for i in range(1, len(c)):
        hi, lo = hl_[i - 1], ll_[i - 1]
        if hi != hi and lo != lo:
            continue
        bull = lo == lo and l[i] < lo and c[i] > lo
        bear = hi == hi and h[i] > hi and c[i] < hi
        out[i] = float(bull) - float(bear)
    return _S(out, d)


def _smc_fr_case(kind):
    """SMC_SWEEP確定 の既知答え用（2026-10-09・K-3b）。40本の平らな足（始値＝終値＝100・高値 100.2・安値 99.8）の20本目に、
    谷（安値 99.0）か山（高値 101.0）を置く（前後2本より低い（高い）＝22本目で確定）。最後の足で、
    kind="bull"＝安値 98.5・終値 99.6（谷を割って戻した＝+1）／kind="bear"＝高値 101.5・終値 100.5（山を抜いて戻した＝−1）／
    kind="stay"＝安値 98.5・終値 98.8（割ったが戻していない＝0）。陽線・陰線とヒゲの長さは条件に入れない（ライブラリの版との違い）。"""
    m = 40
    c = np.full(m, 100.0)
    o = c.copy()
    h = np.full(m, 100.2)
    l = np.full(m, 99.8)
    if kind == "bear":
        h[20] = 101.0
        h[-1] = 101.5
        c[-1] = 100.5
    else:
        l[20] = 99.0
        l[-1] = 98.5
        c[-1] = 99.6 if kind == "bull" else 98.8
    return _mk(c=c, o=o, h=h, l=l)


_r(r"W字確定谷\((\d+),([\d.]+)\)", "W字確定谷",
   "ダブルボトムの教科書の版。窓 n 本の中で確定した直近の2つの谷（前後 k 本）の値段の差が tol×終値 以内で、"
   "2つ目の谷の後に終値がネック（2つの谷の間の最高値）を最初に上抜けた足だけ 1・それ以外 0",
   "監査 CP60 の修正43＝StockCharts の逐語「Breaking resistance from the highest point between the troughs completes the Double Bottom Reversal.」。"
   "確定の本数 k は名前に出さない引数（最初の値 2＝資料の fractal の既定）。今の W字（中央区間の最高値の近似・条件が続く間ずっと1）は残す",
   "反転サイン＝1 は買い転換（ダブルボトム完成）の示唆", "reversal", tb=_tb_w_fr,
   known=lambda p: [(_w_case(int(p[0]), 100.2), [(-1, 1.0, 1e-9)]), (_w_case(int(p[0]), 92.0), [(-1, 0.0, 1e-9)]),
                    (_w_case2(int(p[0])), [(-2, 1.0, 1e-9), (-1, 0.0, 1e-9)])],
   mako=MAKO_K3B)
_r(r"S-Rタッチ確定数\((\d+),([\d.]+)\)", "S-Rタッチ確定数",
   "今の足の前の n 本の中で確定した山（高値）と谷（安値）のうち、今の終値 ± 許容幅（tol×終値）に入るものの数",
   "監査 CP60 の修正44＝教科書の数え方（chartinglens「You need to see price react at approximately the same price point at least twice」）。"
   "山・谷は前後 k 本で確定してから数える（k は名前に出さない引数・最初の値 2）。今の S-Rタッチ数（帯に掛かった足の本数＝滞在時間）は残す",
   "状態量＝多いほど節が固い", "none", tb=_tb_sr_fr,
   known=lambda p: [(_sr_fr_case(int(p[0])), [(-1, 3.0, 1e-9)])], mako=MAKO_K3B)
_r(r"S-Rタッチ確定1時間ATR\((\d+),([\d.]+),(\d+)\)", "S-Rタッチ確定1時間ATR",
   "S-Rタッチ確定数 の許容幅を「倍率 × 1時間足の ATR%（ATR ÷ その1時間足の終値）」で決め、0.15%〜0.6% に収めたもの",
   "監査 CP60 の修正44 の数え方（確定した山・谷）＋ S-Rタッチ1時間ATR と同じ許容幅（出どころの逐語『tol=clamp(K×ATR%_1h,0.15%,0.6%)』）。"
   "1時間足の値は、その1時間足が閉じた時刻から使う",
   "状態量＝多いほど節が固い", "none", tb=_tb_sr_fr_atr1h,
   known=lambda p: [(_sr_fr_case(int(p[0])), [(-1, 3.0, 1e-9)])], mako=MAKO_K3B)


# ★2026-10-20（工事 m2c15-band-s1-20261020・B-1＋S-1）＝帯の部品4種 × 許容幅の作り2つと、S1 の部品2つ（Lee-Mykland の論文の版と E36 の版）。
#   帯スイング と S1 は独立の実装（素直な繰り返しで書いた別の書き方）と手計算の既知答え、帯pivot・帯VA は手計算の既知答え
#   （前期間pivot・前日VAH と同じ形＝線は観察の道具の計算を使う）で確かめる。
def _tb_band_floor():
    """取れる距離の床（独立の実装の側）＝e37_scalp.SCALP_FLOOR × 設定ファイル observe_config.json の band_fee_mult。"""
    import json as _json
    import pathlib as _pl
    import e37_scalp as _e37r
    cfg = _json.loads((_pl.Path(__file__).resolve().parent / "observe_config.json").read_text(encoding="utf-8"))
    return float(_e37r.SCALP_FLOOR) * float(cfg["band_fee_mult"])


def _tb_band_cluster(px, price, t, m, above):
    """確定したスイングの値段を、値段の低い順に、前の値段との差が「前の値段 × t」以下なら同じ帯へ入れていく。
    スイングが m 回以上の帯のうち、帯の平均が price に近いもの（同じなら値段の低い側）の（下端, 上端）。"""
    vals = sorted(x for x in px if (x > price if above else x < price))
    groups = []
    for x in vals:
        if groups and x - groups[-1][-1] <= groups[-1][-1] * t:
            groups[-1].append(x)
        else:
            groups.append([x])
    best = None
    for g in groups:
        if len(g) >= m:
            dist = abs(sum(g) / len(g) - price)
            if best is None or dist < best[0]:
                best = (dist, min(g) * (1 - t / 2), max(g) * (1 + t / 2))
    return None if best is None else (best[1], best[2])


def _tb_tol_1h(d, km, an):
    """帯の許容幅（1時間足の ATR% × 倍率・0.15%〜0.6%）の独立の実装＝_tb_sr_fr_atr1h の①〜⑤と同じ書き方。"""
    o, h, l, c, v = _arr(d)
    starts, groups = [], []
    for i, t in enumerate(d.index.floor("h")):
        if not starts or starts[-1] != t:
            starts.append(t)
            groups.append([i])
        else:
            groups[-1].append(i)
    hh = np.array([h[g].max() for g in groups])
    hl = np.array([l[g].min() for g in groups])
    hc = np.array([c[g[-1]] for g in groups])
    atr = np.full(len(groups), np.nan)
    for j in range(len(groups)):
        if j == 0:
            atr[j] = hh[j] - hl[j]
        else:
            tr = max(hh[j] - hl[j], abs(hh[j] - hc[j - 1]), abs(hl[j] - hc[j - 1]))
            atr[j] = (atr[j - 1] * (an - 1) + tr) / an
    pct = atr / hc
    closes = (pd.DatetimeIndex(starts) + pd.Timedelta("1h")).values
    pos = np.searchsorted(closes, (d.index + pd.Timedelta("5min")).values, side="right") - 1
    out = np.full(len(c), np.nan)
    for i in range(len(c)):
        if pos[i] >= 0:
            out[i] = min(max(km * pct[pos[i]], 0.0015), 0.006)
    return out


def _tb_band_swing(d, p, k=2):
    """帯スイング・帯スイング1時間ATR の独立の実装。p＝(n, t, m) か (n, 倍率, ATR の期間, m)。"""
    n, m = int(p[0]), int(p[-1])
    o, h, l, c, v = _arr(d)
    tols = np.full(len(c), float(p[1])) if len(p) == 3 else _tb_tol_1h(d, float(p[1]), int(p[2]))
    hv, lv = _tb_fractal_marks(d, k, True), _tb_fractal_marks(d, k, False)
    floor = _tb_band_floor()
    out = np.full(len(c), np.nan)
    for i in range(n, len(c)):
        t = tols[i]
        if t != t:
            continue
        up = _tb_band_cluster([x for x in hv[i - n:i] if x == x], c[i], t, m, True)
        dn = _tb_band_cluster([x for x in lv[i - n:i] if x == x], c[i], t, m, False)
        ok = up is not None and dn is not None and dn[1] < c[i] < up[0] and (up[0] - dn[1]) / c[i] >= floor
        out[i] = 1.0 if ok else 0.0
    return _S(out, d)


def _band_case(kind, touches, unconfirmed=False):
    """帯の部品の既知答え用（2026-10-20）。どの種類も、最後の足の前 30 本の中に、上の線の山（高値だけ高い足）と下の線の谷
    （安値だけ低い足）を touches 回ずつ置く（山は最後の足の 30・24・18・12 本前、谷は 27・21・15・9 本前＝6 本おき＝前後2本で確定し、
    最後の足より前に確定する）。それ以外の足は始値＝高値＝安値＝終値。最後の足の終値は2本の線の間。
    kind="swing"＝328本・終値 100・山 110・谷 90（束ねた帯＝110 と 90）。
    答え＝touches がタッチの回数 m 以上なら 1、m より少なければ 0（上と下の線に m 回のスイングが無い）。
    ★unconfirmed＝True のときは、最後の足の1本前にも山（110）と谷（90）を置く＝その足はまだ確定していない（確定は最後の足の1本後）。
      確定していない山・谷を数える作り（未来を見る作りに近い）なら touches＋1 回になって 1 を出す＝見分けられる。
    ★2026-10-21（タッチの回数に 2 を足した・まこさん「OK」）＝答えをタッチの回数 m から作る（_band_known）。直す前は m＝3 の決め打ちだった。
    kind="narrow"＝山 100.15・谷 99.85 を 4 回ずつ＝取れる距離が許容幅 0.0015 のとき (100.15×0.99925 − 99.85×1.00075) ÷ 100 ＝ 0.0015 で、
      手数料の床（0.08% × 倍数 2 ＝ 0.0016）より狭い＝0。床の条件を外すと 1 を出す＝見分けられる。
    ★帯pivot・帯VA は触れた回数を数えない（まこさん「Aでいい」）ので、既知答えは _line_case を使う。"""
    def _spikes(c, h, l, top, bot):
        i = len(c) - 1
        for j, back in enumerate((30, 24, 18, 12)):
            if j < touches:
                h[i - back] = top
        for j, back in enumerate((27, 21, 15, 9)):
            if j < touches:
                l[i - back] = bot
    if kind not in ("swing", "narrow"):
        raise ValueError(f"_band_case の kind は swing か narrow（{kind}）")
    c = np.full(328, 100.0)
    h, l = c.copy(), c.copy()
    if kind == "narrow":
        _spikes(c, h, l, 100.15, 99.85)
    else:
        _spikes(c, h, l, 110.0, 90.0)
        if unconfirmed:
            h[-2], l[-2] = 110.0, 90.0
    return _mk(c=c, o=c.copy(), h=h, l=l)


def _band_known(kind):
    """答え＝タッチの回数 m（名前の最後のパラメータ）回ずつ置けば 1・m−1 回（と確定していない1本）なら 0・幅の狭い帯は 0。"""
    return lambda p: [(_band_case(kind, int(p[-1])), [(-1, 1.0, 1e-9)]),
                      (_band_case(kind, int(p[-1]) - 1, unconfirmed=True), [(-1, 0.0, 1e-9)]),
                      (_band_case("narrow", 4), [(-1, 0.0, 1e-9)])]


def _line_case(kind, last_close):
    """帯pivot・帯VA の既知答え用（2026-10-20・まこさん「Aでいい」＝触れた回数を数えない）。_band_case の1日目（線を作る日）と同じ並びに、
    2日目 200本（始値＝高値＝安値＝終値＝105）を続け、最後の足の終値だけ last_close にする。
    pivot＝R1 110・S1 100／va＝VAH 109.791…・VAL 100.208…。終値 105＝線の間＝1・終値 112＝上の線より上＝0。"""
    if kind == "pivot":
        c = np.full(488, 105.0)
        h, l = c.copy(), c.copy()
        h[100], l[200] = 110.0, 100.0
    else:
        c = np.r_[np.full(144, 100.0), np.full(144, 110.0), np.full(200, 105.0)]
        h, l = c.copy(), c.copy()
    c[-1] = h[-1] = l[-1] = float(last_close)
    return _mk(c=c, o=c.copy(), h=h, l=l)


def _line_known(kind):
    return lambda p: [(_line_case(kind, 105.0), [(-1, 1.0, 1e-9)]), (_line_case(kind, 112.0), [(-1, 0.0, 1e-9)])]


def _line_case_w(last_close):
    """前の週の版の帯pivot の既知答え用（2026-10-21・監査 CP83 の修正12・まこさん「ウ」）。足は _IDX0（2026-03-01 の日曜日）から始まる。
    日曜日 288本（105）→ 月曜日から日曜日の1週間 2016本（105・その中の1本だけ高値 110、別の1本だけ安値 100・週の最後の終値 105）→
    次の週の月曜日 288本（105）→ 火曜日 10本（105・最後の足だけ last_close）。前の週の pivot＝PP 105・R1 110・S1 100＝終値 105 は線の間＝1・
    112 は上の線より上＝0。★前の日の版（_pivot_prev_period(d)）なら、前の日（月曜日・全部 105）の R1＝S1＝105 で線の間が無く 0＝見分けられる。"""
    c = np.full(288 + 2016 + 288 + 10, 105.0)
    h, l = c.copy(), c.copy()
    h[288 + 500], l[288 + 1000] = 110.0, 100.0
    c[-1] = h[-1] = l[-1] = float(last_close)
    return _mk(c=c, o=c.copy(), h=h, l=l)


def _line_known_w():
    return lambda p: [(_line_case_w(105.0), [(-1, 1.0, 1e-9)]), (_line_case_w(112.0), [(-1, 0.0, 1e-9)])]


def _tb_lee_mykland(d, p):
    """S1 の部品（論文の版＝Lee-Mykland 2008 の式(7)・式(8)）の独立の実装＝論文の式を素直な繰り返しで書いた物（2026-10-21・監査 CP83 の修正1）。
    r_i＝log(c_i / c_{i−1})・V_i＝π/(2(K−2)) × Σ_{j=i−K+2}^{i−1} |r_j||r_{j−1}|（今の1本の項を入れない）・L_i＝r_i / √V_i（K 本そろう前は空）。"""
    K = int(p[0])
    c = d.close.to_numpy(float)
    r = np.full(len(c), np.nan)
    for i in range(1, len(c)):
        r[i] = math.log(c[i] / c[i - 1])
    out = np.full(len(c), np.nan)
    for i in range(K, len(c)):
        s = 0.0
        for j in range(i - K + 2, i):
            s += abs(r[j]) * abs(r[j - 1])
        with np.errstate(invalid="ignore", divide="ignore"):
            out[i] = np.float64(r[i]) / np.sqrt(np.float64(math.pi / (2.0 * (K - 2)) * s))
    return _S(out, d)


def _tb_lee_mykland_e36(d, p):
    """S1 の部品（E36 の版＝e36_short_oscillation.py の spike_stat）の独立の実装＝素直な繰り返しで書いた物。
    V_i＝π/(2(K−1)) × Σ_{j=i−K+2}^{i} |r_j||r_{j−1}|（今の1本の項を入れる）・L_i＝r_i / √V_i（K 本そろう前は空）。"""
    K = int(p[0])
    c = d.close.to_numpy(float)
    r = np.full(len(c), np.nan)
    for i in range(1, len(c)):
        r[i] = math.log(c[i] / c[i - 1])
    out = np.full(len(c), np.nan)
    for i in range(K, len(c)):
        s = 0.0
        for j in range(i - K + 2, i + 1):
            s += abs(r[j]) * abs(r[j - 1])
        with np.errstate(invalid="ignore", divide="ignore"):
            out[i] = np.float64(r[i]) / np.sqrt(np.float64(math.pi / (2.0 * (K - 1)) * s))
    return _S(out, d)


def _lm_case(x=0.01, n=300):
    """S1 の部品の既知答え用（2026-10-20）。終値を 100 と 100×e^x の交互にする（対数の値動きが +x と −x の交互）。
    bipower の項はすべて x²＝V＝π x²/2 ＝ L＝±x ÷ (x √(π/2)) ＝ ±√(2/π) ＝ ±0.79788456…。最後の足（奇数番目＝上げ）は正。
    ★この足では、ふだんの揺れに今の1本を入れても入れなくても答えが同じ＝窓の誤りを見分けるのは _lm_jump_case（監査 CP83 の修正1）。"""
    c = np.where(np.arange(n) % 2 == 0, 100.0, 100.0 * math.exp(x))
    return _mk(c=c, o=c.copy(), h=c.copy(), l=c.copy())


_LM_X, _LM_Y = 0.01, 0.1


def _lm_jump_case(x=_LM_X, y=_LM_Y, n=300):
    """S1 の部品の既知答え用（2026-10-21・監査 CP83 の修正1）。_lm_case の足の最後の1本だけ、対数の値動きを y（＝x の10倍）にする。
    論文の版＝ふだんの揺れは直前の値動き（すべて x²）だけ＝L＝y ÷ (x √(π/2)) ＝ 10 × √(2/π)。
    E36 の版＝今の1本の項 |y||x| が入る＝L＝y ÷ √(π/(2(K−1)) × ((K−2) x² + x y))。＝今の1本を入れるかで答えが変わる。"""
    c = np.where(np.arange(n) % 2 == 0, 100.0, 100.0 * math.exp(x))
    c[-1] = c[-2] * math.exp(y)
    return _mk(c=c, o=c.copy(), h=c.copy(), l=c.copy())


def _lm_known_paper(p):
    return [(_lm_case(), [(-1, math.sqrt(2.0 / math.pi), 1e-9), (-2, -math.sqrt(2.0 / math.pi), 1e-9)]),
            (_lm_jump_case(), [(-1, _LM_Y / _LM_X * math.sqrt(2.0 / math.pi), 1e-9)])]


def _lm_known_e36(p):
    K = int(p[0])
    return [(_lm_case(), [(-1, math.sqrt(2.0 / math.pi), 1e-9), (-2, -math.sqrt(2.0 / math.pi), 1e-9)]),
            (_lm_jump_case(), [(-1, _LM_Y / math.sqrt(math.pi / (2.0 * (K - 1)) * ((K - 2) * _LM_X ** 2 + _LM_X * _LM_Y)), 1e-9)])]


_r(r"帯スイング\((\d+),([\d.]+),(\d+)\)", "帯スイング",
   "確定したスイング（前後 k 本で確定した山と谷）を許容幅 t で束ねた、終値の上の帯と下の帯。今の足の前の n 本で、上の帯の山と下の帯の谷が"
   "それぞれ m 回以上・取れる距離（上の帯の下端 − 下の帯の上端）÷ 終値 が手数料の床 × 倍数以上・終値がその間なら 1、それ以外 0",
   "法則 R1・R7（regime_detection_kb.md の 11-2）・LuxAlgo の逐語 \"Overlapping zones merge into one consolidated zone and their test counts are added together\"。"
   "手数料の床＝e37_scalp.SCALP_FLOOR・倍数＝設定 band_fee_mult（名前に出さない）・k は名前に出さない引数（最初の値 2）。RG-v5 の数字は使わない",
   "状態量＝1 はレンジの帯の中", "none", tb=_tb_band_swing, known=_band_known("swing"), mako=MAKO_B1S1)
_r(r"帯スイング1時間ATR\((\d+),([\d.]+),(\d+),(\d+)\)", "帯スイング1時間ATR",
   "帯スイング の許容幅を「倍率 × 1時間足の ATR%（ATR ÷ その1時間足の終値）」で決め、0.15%〜0.6% に収めたもの",
   "帯スイング と同じ法則 ＋ S-Rタッチ1時間ATR と同じ許容幅。0.15%〜0.6% の出どころ＝§2.2 の段1 の表「許容幅0.0015〜0.006」"
   "（engine_tuner_milestones2.md:457・監査 CP83 の修正9＝RG-v6 を写す目的ではない）。1時間足の値は閉じた時刻から使う",
   "状態量＝1 はレンジの帯の中", "none", tb=_tb_band_swing, known=_band_known("swing"), mako=MAKO_B1S1)
_r(r"帯pivot\(([\d.]+)\)", "帯pivot",
   "上の線＝前の日で固定の pivot R1・下の線＝S1。上の帯の下端（R1×(1−t/2)）と下の帯の上端（S1×(1+t/2)）の間に終値が在り、"
   "取れる距離（その差）÷ 終値 が手数料の床 × 倍数以上なら 1、それ以外 0。線に触れた回数は数えない",
   "教科書の pivot の役割＝StockCharts の逐語「Pivot Points use the prior period's high, low, and close to estimate future support and "
   "resistance levels.」（前もって推定する支持線・抵抗線）・法則 R7（取れる距離）。まこさん「絶対につくってほしい」（worklog 20261003 §37）・"
   "「Aでいい」（触れた回数を数えない・ok_pivot_a_20261020）",
   "状態量＝1 は前の日の R1 と S1 の間", "none", known=_line_known("pivot"), mako=MAKO_B1S1)
_r(r"帯pivot1時間ATR\(([\d.]+),(\d+)\)", "帯pivot1時間ATR",
   "帯pivot の許容幅を「倍率 × 1時間足の ATR%」で決め、0.15%〜0.6% に収めたもの",
   "帯pivot と同じ ＋ S-Rタッチ1時間ATR と同じ許容幅",
   "状態量＝1 は前の日の R1 と S1 の間", "none", known=_line_known("pivot"), mako=MAKO_B1S1)
_r(r"帯pivot前週\(([\d.]+)\)", "帯pivot前週",
   "帯pivot の線を、前の週（月曜0時 UTC に始まる7日）の高値・安値・終値から作った pivot R1・S1 にしたもの。決まりは帯pivot と同じ",
   "StockCharts の逐語「Pivot Points for 30-, 60-, and 120-minute charts use the prior week's high, low, and close.」・先例＝K-7 の前週pivot"
   "（_pivot_prev_period(d, \"W\")）・監査 CP83 の修正12・まこさん「ウ」（前の日の版と両方を材料に置き、M2-F-10f で比べる）",
   "状態量＝1 は前の週の R1 と S1 の間", "none", known=_line_known_w(), mako=MAKO_B1S1)
_r(r"帯pivot前週1時間ATR\(([\d.]+),(\d+)\)", "帯pivot前週1時間ATR",
   "帯pivot前週 の許容幅を「倍率 × 1時間足の ATR%」で決め、0.15%〜0.6% に収めたもの",
   "帯pivot前週 と同じ ＋ S-Rタッチ1時間ATR と同じ許容幅",
   "状態量＝1 は前の週の R1 と S1 の間", "none", known=_line_known_w(), mako=MAKO_B1S1)
_r(r"帯VA\(([\d.]+)\)", "帯VA",
   "上の線＝前の UTC の日で固定の VAH・下の線＝VAL（前日VAH・前日VAL と同じ作り）。帯pivot と同じ決まりで 1 か 0（触れた回数は数えない）",
   "教科書の Value Area＝LuxAlgo の逐語「the completed value area is carried forward as a reference for later sessions」（前のセッションの値を"
   "後のセッションの参照にする）・法則 R7。worklog 20261003 §38・まこさん「Aでいい」（ok_pivot_a_20261020）",
   "状態量＝1 は前の日の VAL と VAH の間", "none", known=_line_known("va"), mako=MAKO_B1S1)
_r(r"帯VA1時間ATR\(([\d.]+),(\d+)\)", "帯VA1時間ATR",
   "帯VA の許容幅を「倍率 × 1時間足の ATR%」で決め、0.15%〜0.6% に収めたもの",
   "帯VA と同じ ＋ S-Rタッチ1時間ATR と同じ許容幅",
   "状態量＝1 は前の日の VAL と VAH の間", "none", known=_line_known("va"), mako=MAKO_B1S1)
_r(r"LeeMykland(\d+)", "LeeMykland",
   "Lee-Mykland（2008）の jump の検定統計 L＝今の1本の対数の値動き ÷ ふだんの揺れ（直前の K−1 本の bipower）の平方根（上げの jump が正）。"
   "論文の式(8)どおり、ふだんの揺れに今の1本を入れない",
   "法則 S1（regime_detection_kb.md の 11-5）・Lee-Mykland（2008）の式(7)・式(8)と逐語「With realized returns in the window consisting of the "
   "previous K − 1 observations just before a testing time ti, the instantaneous volatility is estimated」（2540ページ・監査 CP83 の修正1）。"
   "K の値＝論文の推奨値（5分足 270・15分足 156・30分足 110・1時間足 78・日足 16・2542ページ）。閾値 L*（K と α から数式で決める）は材料に入れない",
   "向きつき＝大きいほど統計的にありえない上げ・小さいほど下げ", "none", tb=_tb_lee_mykland, known=_lm_known_paper,
   mako=MAKO_B1S1)
_r(r"LeeMykland_E36版(\d+)", "LeeMykland_E36版",
   "E36（e36_short_oscillation.py の spike_stat）の jump の統計。ふだんの揺れに今の1本の項 |r_i||r_{i−1}| を入れる（K−1 項）＝論文の式(8)と違う",
   "e36_short_oscillation.py の式を材料の表へ移したもの（式は変えていない＝E36 の値は変わらない）。論文の版（LeeMykland）とどちらが良いかは "
   "M2-F-10f で比べる（監査 CP83 の修正1・まこさん「案A」）",
   "向きつき＝大きいほど統計的にありえない上げ・小さいほど下げ", "none", tb=_tb_lee_mykland_e36, known=_lm_known_e36,
   mako=MAKO_B1S1)
_r(r"SMC_SWEEP確定", "SMC_SWEEP確定",
   "流動性の刈り取りの教科書の版。1本前までに確定した直近の谷を安値で割り、終値でその上に戻した足を +1・"
   "山を高値で抜き、終値でその下に戻した足を −1",
   "監査 CP60 の修正46＝LuxAlgo の逐語「The classic anatomy is a wick through a prior swing high or low…followed by a close back inside the old range.」。"
   "山・谷は前後 k 本で確定（k は名前に出さない引数・最初の値 2）。ライブラリの版（直前15本の高安・陽線陰線・ヒゲが実体の1.5倍）の条件は使わない",
   "反転サイン", "none", tb=_tb_smc_fr,
   known=lambda p: [(_smc_fr_case("bull"), [(-1, 1.0, 1e-9)]), (_smc_fr_case("bear"), [(-1, -1.0, 1e-9)]),
                    (_smc_fr_case("stay"), [(-1, 0.0, 1e-9)])],
   mako=MAKO_K3B)


# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正37・45・47〜53 と K-7 の決定）＝計算式の教科書の版。
#   独立の実装は、素直な繰り返しと部品（_roll・_ema_seed・_wilder）で書く。観察の道具がライブラリか pandas で書いた種類とは別の書き方。
#   ★観察の道具も手の繰り返しで書いた3種（close vs SSF平均%・close vs VIDYA_CMO%・SQZ_ON_Carter）は、同じ式の写しどうしの照らしだった
#   （監査 CP73 の Q8）。K-4（2026-10-11・まこさん「CCの案でOK」）で、この3種の独立の実装を別の書き方にした＝SSF は線形フィルタ
#   （scipy.signal.lfilter）・VIDYA は畳み込みで CMO を出し accumulate で畳む・Carter の ATR は pandas の指数平滑。式の出どころは変えない。
def _tb_rvol_rv(d, p):
    c = d.close.to_numpy(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.log(c / np.where(np.roll(c, 1) == 0, np.nan, np.roll(c, 1)))
    r[0] = np.nan
    n = int(p[0])
    return _S(np.sqrt(_roll(r * r, n, "sum") / n) * 100, d)


def _geo_case(n=60, r=0.001):
    """realized_vol_rv の既知答え用＝終値が毎本 同じ割合 r で増える足（対数リターンが一定）。平均を引く今の版は 0・引かない版は 100×ln(1+r)。"""
    c = 100.0 * (1.0 + r) ** np.arange(n)
    return _mk(c=c)


def _tb_sqz_carter(d, p, bb_length=20, bb_std=2.0, kc_length=20, kc_scalar=1.5):
    """Carter のスクイーズの独立実装（K-4 で別の書き方にした）＝観察の道具は手の繰り返しで Wilder の ATR を出す。こちらは pandas の
    指数平滑（alpha＝1/n・adjust=False＝(前×(n−1)＋今)/n と同じ式）に、最初の n 本の真の値幅の単純平均を種として渡す。"""
    o, h, l, c, v = _arr(d)
    tr = pd.Series(_tr(h, l, c), index=d.index)
    seed = tr.iloc[1:kc_length + 1].mean()
    x = tr.copy()
    x.iloc[:kc_length] = np.nan
    x.iloc[kc_length] = seed
    atr = x.ewm(alpha=1.0 / kc_length, adjust=False).mean()
    atr[x.isna().cummin()] = np.nan                       # 種より前は欠損
    mid, sd = _S(_roll(c, bb_length, "mean"), d), _S(_roll(c, bb_length, "std", ddof=0), d)
    km = _S(_roll((h + l + c) / 3.0, kc_length, "mean"), d)
    inside = ((mid - bb_std * sd) > (km - kc_scalar * atr)) & ((mid + bb_std * sd) < (km + kc_scalar * atr))
    return inside.astype(float).where(atr.notna() & sd.notna())


def _tb_stochrsi_raw(d, p):
    return _S(_stochrsi_parts(d, int(p[0]), int(p[0]), 1, 1)[0], d)


def _tb_trix_ema_s(d, p):
    tx = _trix_parts(d, int(p[0]), int(p[1]))[0]
    return _S(_ema_seed(tx, int(p[1])), d)


def _tb_trix_ema_h(d, p):
    tx = _trix_parts(d, int(p[0]), int(p[1]))[0]
    return _S(tx - _ema_seed(tx, int(p[1])), d)


def _ssf2_avg(c: np.ndarray, n: int) -> np.ndarray:
    """Ehlers のスーパースムーザー（2極）＝入力を (c + c[1])/2 にしたもの（linnsoft の逐語「Filt = c1*(Close + Close[1]) / 2 + c2*Filt[1] + c3*Filt[2]」）。
    K-4 で別の書き方にした＝線形フィルタ（scipy.signal.lfilter）で書く。分子＝[c1/2, c1/2]・分母＝[1, −c2, −c3]。
    最初の2本は入力のまま（観察の道具と同じ始め方）＝その2本を初期状態（lfiltic）にして3本目から回す。"""
    from scipy.signal import lfilter, lfiltic
    x = np.pi * np.sqrt(2.0) / n
    a0 = np.exp(-x)
    b0 = 2.0 * a0 * np.cos(x)
    c2, c3 = b0, -a0 * a0
    c1 = 1.0 - c2 - c3
    y = np.asarray(c, float).copy()
    if len(y) > 2:
        b, a = [c1 / 2.0, c1 / 2.0], [1.0, -c2, -c3]
        zi = lfiltic(b, a, y=y[1::-1], x=y[1::-1])
        y[2:] = lfilter(b, a, y[2:], zi=zi)[0]
    return y


def _tb_pos_ssf_avg(d, p):
    return _pos(_ssf2_avg(d.close.to_numpy(float), int(p[0])), d)


def _trima_ta(c, n):
    """TA-Lib の TRIMA。偶数の n＝SMA(SMA(x, n/2), n/2+1)。奇数の n は今の _trima と同じ。"""
    if n % 2 == 0:
        return _roll(_roll(c, n // 2, "mean"), n // 2 + 1, "mean")
    return _trima(c, n)


def _tb_pos_trima_ta(d, p):
    return _pos(_trima_ta(d.close.to_numpy(float), int(p[0])), d)


def _vidya_cmo(c: np.ndarray, n: int, m: int = 9) -> np.ndarray:
    """VIDYA で CMO の本数 m を n と別に持つ版（ta-lib.org の逐語「n = optInTimePeriod, m = optInCMOPeriod」）。
    K-4 で別の書き方にした＝CMO の上げ・下げの合計は畳み込み（np.convolve）で出し、適応の漸化式 out←a×k×c＋(1−a×k)×out は
    itertools.accumulate で畳む（種＝最初の n 本の単純平均）。"""
    from itertools import accumulate
    c = np.asarray(c, float)
    a = 2.0 / (n + 1)
    dif = np.diff(c)
    k = np.full(len(c), np.nan)
    if len(c) > m:
        up = np.convolve(np.clip(dif, 0.0, None), np.ones(m), "valid")
        dn = np.convolve(np.clip(-dif, 0.0, None), np.ones(m), "valid")
        k[m:] = np.abs(_div(up - dn, up + dn))
    out = np.full(len(c), np.nan)
    if len(c) < n:
        return out
    kk = np.nan_to_num(k[n:], nan=0.0)
    seed = float(np.nanmean(c[:n]))
    out[n - 1:] = list(accumulate(zip(c[n:], kk), lambda prev, t: a * t[1] * t[0] + (1.0 - a * t[1]) * prev, initial=seed))
    return out


def _tb_pos_vidya_cmo(d, p, m=9):
    return _pos(_vidya_cmo(d.close.to_numpy(float), int(p[0]), int(m)), d)


def _tb_dpo_tb(d, p):
    """教科書の DPO を時点 t で作れる形＝k本前の終値 − いまの n本平均（k=n/2+1）。終値で割って%化（H6）。"""
    n = int(p[0])
    c = d.close.to_numpy(float)
    return (_S(c, d).shift(int(0.5 * n) + 1) - _S(_roll(c, n, "mean"), d)) / d.close * 100


def _tb_aber_orig(d, p, length=80, std=2.0):
    c = d.close.to_numpy(float)
    mid, sd = _roll(c, int(length), "mean"), _roll(c, int(length), "std", ddof=0)
    return _S(_div(c - (mid - std * sd), 2.0 * std * sd), d)


def _thermo_orig_arr(d):
    o, h, l, c, v = _arr(d)
    ph, pl = np.r_[np.nan, h[:-1]], np.r_[np.nan, l[:-1]]
    return c, np.maximum(np.maximum(h - ph, 0.0), np.maximum(pl - l, 0.0))


def _tb_thermo_orig(d, p):
    c, t = _thermo_orig_arr(d)
    return _S(_div(t, c) * 100.0, d)


def _tb_thermo_ema(d, p, ema_n=20):
    c, t = _thermo_orig_arr(d)
    return _S(_div(_ema_seed(t, int(ema_n)), c) * 100.0, d)


def _thermo_in_case(n=30):
    """THERMO原作% の既知答え用＝平らな足（高値 101・安値 99）の最後の足だけ内はらみ（高値 100.5・安値 99.5）。原作は 0・ライブラリの版は 0.5/100×100。"""
    c = np.full(n, 100.0)
    h = np.full(n, 101.0)
    l = np.full(n, 99.0)
    h[-1], l[-1] = 100.5, 99.5
    return _mk(c=c, o=c.copy(), h=h, l=l)


_r(r"realized_vol_rv(\d+)", "realized_vol_rv",
   "平均を引かない実現ボラ＝対数リターンの二乗の n 本平均の平方根×100",
   "監査 CP60 の修正50＝Wikipedia「RV(n) = Σ r²」「the square root of the realized variance」。今の realized_vol（平均を引いた標本の標準偏差）は残す",
   "ボラ量", "vol", tb=_tb_rvol_rv,
   known=lambda p: [(_flat(p[0] * 3), [(-1, 0.0, 1e-9)]), (_geo_case(p[0] * 3), [(-1, 100.0 * np.log(1.001), 1e-9)])],
   mako=MAKO_K3C)
_r(r"SQZ_ON_Carter", "SQZ_ON_Carter",
   "スクイーズ（Carter の作り）＝ボリンジャー（終値の SMA ± 2σ）がケルトナー（代表値段の SMA ± 1.5×ATR（Wilder））の内側なら 1",
   "監査 CP60 の修正47＝StockCharts「Carter uses 20 periods for the moving average and ATR, and 1.5 for the ATR multiplier」。"
   "4つの数は名前に出さない引数（最初の値 20・2.0・20・1.5）。今の SQZ_ON（中心を終値の SMA・幅を真の値幅の SMA）は残す",
   "状態量", "none", tb=_tb_sqz_carter, mako=MAKO_K3C, tb_kind="教科書")
_r(r"StochRSI素%K(\d+)", "StochRSI素%K",
   "RSI にストキャスを掛けた原式の値（ならさない・0〜100）",
   "監査 CP60 の修正48＝StockCharts「StochRSI = (RSI - Lowest Low RSI) / (Highest High RSI - Lowest Low RSI)」。今の %K（SMA3 でならす）は残す",
   "順張り値", "trend", tb=_tb_stochrsi_raw, mako=MAKO_K3C)
_r(r"TRIX_EMAシグナル\((\d+),(\d+)\)", "TRIX_EMAシグナル",
   "TRIX を g 本の EMA でならしたシグナル", "監査 CP60 の修正49＝StockCharts「The signal line is a 9-day EMA of the TRIX.」。今の TRIXシグナル（単純移動平均）は残す",
   "順張り値", "trend", tb=_tb_trix_ema_s, mako=MAKO_K3C)
_r(r"TRIX_EMAヒスト\((\d+),(\d+)\)", "TRIX_EMAヒスト",
   "TRIX と EMA のシグナルの差", "同上。今の TRIXヒスト（単純移動平均のシグナルとの差）は残す",
   "状態量＝加速（向きを持たない）", "none", tb=_tb_trix_ema_h, mako=MAKO_K3C)
_r(r"close vs SSF平均%(\d+)", "close vs SSF平均%",
   "終値が、入力を2本の平均にした Ehlers のスーパースムーザー（2極）から何%離れているか",
   "監査 CP60 の修正51＝linnsoft の逐語「Filt = c1*(Close + Close[1]) / 2 + c2*Filt[1] + c3*Filt[2];」。今の close vs SSF%（入力が終値）は残す",
   "反転サイン", "trend", tb=_tb_pos_ssf_avg, mako=MAKO_K3C, tb_kind="教科書")
_r(r"close vs TRIMA_TA%(\d+)", "close vs TRIMA_TA%",
   "終値が TA-Lib の TRIMA（偶数の n＝SMA(SMA(x, n/2), n/2+1)）から何%離れているか",
   "監査 CP60 の修正52＝ta-lib.org「even: SMA(SMA(x,period/2),period/2+1)」。奇数の n は今の版と同じ。今の close vs TRIMA%（偶数でも n/2+1 を2回）は残す",
   "反転サイン", "trend", tb=_tb_pos_trima_ta, mako=MAKO_K3C)
_r(r"close vs VIDYA_CMO%(\d+)", "close vs VIDYA_CMO%",
   "終値が、CMO の本数 m を n と別に持つ VIDYA から何%離れているか",
   "監査 CP60 の修正52＝ta-lib.org「n = optInTimePeriod, m = optInCMOPeriod」。m は名前に出さない引数（最初の値 9＝資料の既定）。今の版（m=n）は残す",
   "反転サイン", "trend", tb=_tb_pos_vidya_cmo, mako=MAKO_K3C, tb_kind="教科書")
_r(r"close vs HT_TRENDLINE_HL%", "close vs HT_TRENDLINE_HL%",
   "終値が、入力を (高値＋安値)/2 にしたヒルベルト変換のトレンド線から何%離れているか",
   "監査 CP60 の修正53＝Ehlers の入力は (H+L)/2（ta-lib.org の表 79）。★変換が多段で独立実装を書けない。既知答え＝値段が一定なら ぴったり 0。今の版（入力が終値）は残す",
   "反転サイン", "none",
   known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)]),
                    (_mk(c=np.full(400, 100.0), o=np.full(400, 100.0), h=np.full(400, 102.0), l=np.full(400, 100.0)),
                     [(-1, (100.0 / 101.0 - 1.0) * 100.0, 1e-9)])],
   mako=MAKO_K3C)
_r(r"close vs MAMA_HL%", "close vs MAMA_HL%",
   "終値が、入力を (高値＋安値)/2 にした MAMA から何%離れているか",
   "監査 CP60 の修正53＝MAMA.pdf のコードの逐語「Inputs: Price((H+L)/2), FastLimit(.5), SlowLimit(.05);」。★独立実装を書けない＝既知答えで検証。今の版は残す",
   "反転サイン", "none",
   known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)]),
                    (_mk(c=np.full(400, 100.0), o=np.full(400, 100.0), h=np.full(400, 102.0), l=np.full(400, 100.0)),
                     [(-1, (100.0 / 101.0 - 1.0) * 100.0, 1e-9)])],
   mako=MAKO_K3C)
_r(r"close vs FAMA_HL%", "close vs FAMA_HL%",
   "終値が、入力を (高値＋安値)/2 にした FAMA（MAMA の追従線）から何%離れているか",
   "同上", "反転サイン", "none",
   known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)]),
                    (_mk(c=np.full(400, 100.0), o=np.full(400, 100.0), h=np.full(400, 102.0), l=np.full(400, 100.0)),
                     [(-1, (100.0 / 101.0 - 1.0) * 100.0, 1e-9)])],
   mako=MAKO_K3C)
_r(r"DPO教科書%(\d+)", "DPO教科書%",
   "教科書の DPO を時点 t で作れる形＝k本前の終値 − いまの n本平均（k=n/2+1）を、終値で割って%化",
   "監査 CP60 の修正37・45＝StockCharts「Price - X-period SMA from {X/2 + 1} periods in the future」を未来を見ずに書いた形（ta の DPOIndicator と同じ）。"
   "今の DPO%（いまの終値 − k本前の n本平均＝TradingView の中心化しない版）は残す",
   "反転サイン", "none", tb=_tb_dpo_tb,
   known=lambda p: [(_flat(p[0] * 3), [(-1, 0.0, 1e-9)]),
                    (_up(p[0] * 3), [(-1, (((p[0] - 1) / 2.0) - (int(0.5 * p[0]) + 1)) / (100.0 + p[0] * 3 - 1) * 100.0, 1e-9)])],
   mako=MAKO_K3C)
_r(r"ABER原作位置", "ABER原作位置",
   "終値が、Fitschen の原作の Aberration の帯（80本・標準偏差2倍のボリンジャーバンド）の中のどこにあるか。0 で下の帯・1 で上の帯",
   "監査 CP60 の修正45・71＝georgepruitt.com「a breakout system based on Bollinger bands with a period length of 80 days and two standard deviations」。"
   "本数と倍率は名前に出さない引数（最初の値 80・2.0）。今の ABER位置（ライブラリの HLC3 の5本 SMA ± ATR15）は残す",
   "順張り値＝大きいほど帯の上側", "trend", tb=_tb_aber_orig, mako=MAKO_K3C)
_r(r"THERMO原作%", "THERMO原作%",
   "Elder の原作の温度計＝前の足から外へはみ出した幅（高値の上げ幅か安値の下げ幅の大きい方・内はらみ足は 0）を、終値で割って%化",
   "監査 CP60 の修正45・58＝Elder（Come Into My Trading Room 2002 p.162）・TradingView の逐語「Inside bars: Both protrusions clamp to zero」。"
   "今の THERMO%（絶対値を取るライブラリの版）は残す",
   "ボラ量", "vol", tb=_tb_thermo_orig,
   known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)]), (_thermo_in_case(), [(-1, 0.0, 1e-9)])], mako=MAKO_K3C)
_r(r"THERMO_EMA%", "THERMO_EMA%",
   "Elder の原作の温度計を EMA でならしたもの（終値で割って%化）",
   "K-7 の決定（ok_k7_pivot_thermo_20261007）＝教科書の既定 20（motivewave）・22（tradingview）は EMA の本数。EMA の本数は名前に出さない引数"
   "（最初の値＝ライブラリの既定 20）。EMA の種＝最初の n 本の単純平均（ライブラリの既定）",
   "ボラ量", "vol", tb=_tb_thermo_ema, known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)])], mako=MAKO_K3C)


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
    p = p or (5, 34)                          # 名前に本数が無い＝教科書の 5・34
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
    # ★重み i は窓の古い側から数える（Legoux／TradingView＝山が新しい側）。
    #   監査 CP60 で、ライブラリの逆順（w_norm[::-1]）の写しをやめた。
    return _wma_w(c, np.exp(-((i - m) ** 2) / (2 * s * s)))


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
    """直線あてはめの角度。★2026-08-11 に「1本あたり何%動くか」の傾きの角度へ直した。

    業界の実装は arctan（1本あたり何ドル動くか）だが、それだと値段の帯が変わると同じ動きでも
    角度が変わる＝H6（価格非依存）に反する（実測＝4本値を2倍にすると値が変わる・検査13）。
    うちは傾きを終値で割って%にしてから角度にする（SQZ% と同じ流儀）。
    """
    n = int(p[0])
    c = d.close.to_numpy(float)
    w = _swv(c, n) if len(c) >= n else None
    out = np.full(len(c), np.nan)
    if w is not None:
        tt = np.arange(n, dtype=float)
        tm = tt.mean()
        stt = ((tt - tm) ** 2).sum()
        ym = w.mean(axis=1)
        sl = ((w - ym[:, None]) * (tt - tm)).sum(axis=1) / stt
        out[n - 1:] = np.degrees(np.arctan(sl / c[n - 1:] * 100.0))
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


# ★2026-08-16（段A の A-6）＝1回あたりの本数（直す前は 2 の直書き）が名前に出たので、p[0] から取る。
def _tb_pos_rainbow(d, p):
    return _pos(_rainbow(d.close.to_numpy(float), int(p[0]), int(p[1])), d)


def _tb_slp_rainbow(d, p):
    return _slope(_rainbow(d.close.to_numpy(float), int(p[0]), int(p[1])), d)


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
    """スクイーズの勢い＝12本前との差を6本の単純移動平均でならしたもの（実物で確認）を、終値で割って%化。
    ★%化は 2026-08-11（段6 の 6-9①）に足した＝値段の単位のままだと H6 違反（検査13 が見つけた）。"""
    return _S(_roll(d.close.diff(12).to_numpy(float), 6, "mean"), d) / d.close * 100


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
    """Schaff のトレンド周期（教科書＝TA-Lib stc の式）。★2段とも「範囲（最大−最小）が 0 か欠損のときだけ
    前の値を持ち越す」。ならしは pf ← pf ＋ 係数×(stoch − pf)。
    ★監査 CP60＝直す前は pandas_ta_classic の誤り（1段目を「MACD の最小値が 0 より大きいとき」だけ計算する）を
    そのまま写していた＝照合が通っても教科書と同じとは言えなかった。"""
    c = d.close.to_numpy(float)
    xm = _ema_seed(c, f_) - _ema_seed(c, s_)
    m = len(xm)

    def stage(x):
        lo, hi = _roll(x, tcl, "min"), _roll(x, tcl, "max")
        rng = hi - lo
        st = np.zeros(m)
        sm = np.zeros(m)
        for i in range(1, m):
            st[i] = 100.0 * (x[i] - lo[i]) / rng[i] if rng[i] > 0 else st[i - 1]
            sm[i] = sm[i - 1] + fac * (st[i] - sm[i - 1])
        return sm

    pf = stage(xm)
    return stage(pf), pf


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
    p = p or (5, 34)                          # 名前に本数が無い＝教科書の 5・34
    return _ta.momentum.AwesomeOscillatorIndicator(
        d.high, d.low, int(p[0]), int(p[1])).awesome_oscillator() / d.close * 100


def _ext_cci(d, p):
    return _ta.trend.CCIIndicator(d.high, d.low, d.close, int(p[0]), 0.015).cci()


# ── 登録（1回目・アルファベット順 ao〜lrsi の19関数／fosc は cfo と同じ式なので入れない）──
_r(r"AO%", "AO%",
   "オーサム振動子。中値（高値と安値の平均）の短期平均 − 長期平均を、終値で割って%化。2つの本数は名前に出さない引数（何も渡さないときは 5・34）",
   "TradingView（Awesome Oscillator・lengthAO1=5・lengthAO2=34）。単純移動平均。%化は価格非依存 H6 のための本プロジェクトの流儀",
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
   "PPO とシグナルの差", "同上。StockCharts の逐語「The histogram is positive when PPO is above its 9-day EMA and "
   "negative when PPO is below its 9-day EMA.」。加速の柱の実測（MACDヒスト% の流儀の欄に記録）＝"
   "加速上げ +0.0001571／加速下げ −0.007139 で符号が分かれる＝順張り値の側（監査 CP60 で直した）",
   "順張り値＝プラスで勢いが加速", "trend", tb=_tb_ppo_h)
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
_r(r"SQZ%", "SQZ%",
   "スクイーズの勢い。ボリンジャーとケルトナーの帯の関係から作る勢いの値を、終値で割って%化",
   "John Carter（TTM Squeeze）。終値と「20本の高安の中央と20本平均の平均」の差を直線あてはめでならす。"
   "★%化は価格非依存 H6 のための本プロジェクトの流儀（2026-08-11・段6 の 6-9①）。"
   "前は値段の単位のまま材料に入っていた＝検査13（4本値を定数倍して計算し直す）が見つけた"
   "（実測＝4本値を2倍にすると値も2倍・比の中央値 2.000）",
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
   "順張り値", "trend", tb=_tb_stc,
   # ★K-4（監査 CP60 の修正59）＝TA-Lib の逐語「When a range is zero, the fraction keeps its previous value (0 before any).」から導いた
   #   既知答え＝値段が一定なら MACD は 0 で範囲も 0＝2段とも 0 のまま。
   # ★監査 CP82 の修正1＝±1 を交互に繰り返す足（_alt_pm1）では MACD の符号が毎本変わり範囲は 0 でない＝教科書の式の STC は 0 より大きい。
   #   ライブラリの誤り（1段目を「MACD の窓の最小値 > 0」のときだけ計算する・pandas_ta_classic momentum/stc.py:180）では 0 のまま＝符号で見分ける。
   known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)]), (_alt_pm1(400), [(-1, "+", 0.0)])], tb_kind="写し")
_r(r"STCstoch", "STCstoch",
   "上の STC が内部で使う、1回目のストキャスをならした値",
   "同上（Schaff Trend Cycle の1段目）", "順張り値", "trend", tb=_tb_stcstoch,
   known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)]), (_alt_pm1(400), [(-1, "+", 0.0)])], tb_kind="写し")


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
def _alma_lag(n: int, sigma: float = 6.0, off: float = 0.85) -> float:
    """ALMA の定義（Legoux／TradingView＝重みは正規分布・ずらし 0.85 で山が新しい側・幅 n/σ）から導く、
    1本ごとに 1 上げる足での遅れ＝Σ 重み_i × (n−1−i) ÷ Σ 重み_i（i は窓の古い側から数える）。
    ★K-4（監査 CP60 の修正59）の既知答え用。重みを逆向きに当てる（ライブラリの写し）と遅れは Σ 重み_i × i ÷ Σ 重み_i になり、
    値が変わる＝監査 CP60 が見つけた向きの誤りを、この既知答えが捕まえる。"""
    i = np.arange(n, dtype=float)
    w = np.exp(-((i - off * (n - 1)) ** 2) / (2.0 * (n / sigma) ** 2))
    return float(np.sum(w * (n - 1 - i)) / np.sum(w))


_r(r"close vs ALMA%(\d+)", "close vs ALMA%",
   "終値が ALMA（ガウス重みの移動平均）から何%離れているか",
   "Arnaud Legoux。重みは正規分布（ずらし 0.85・幅 n/6）＝ライブラリの既定", "反転サイン", "trend", tb=_tb_pos_alma,
   # ★K-4（監査 CP60 の修正59）＝定義から導いた既知答え＝1本ごとに 1 上げる足で、ALMA は終値 − 遅れ（_alma_lag）。
   known=lambda p: [(_up(int(p[0]) + 40), [(-1, ((100.0 + int(p[0]) + 39) / ((100.0 + int(p[0]) + 39) - _alma_lag(int(p[0]))) - 1.0) * 100.0, 1e-9)])],
   tb_kind="写し")
_r(r"ALMA(\d+)傾き%", "ALMA傾き%",
   "ALMA の5本前からの変化率%", "同上。傾きの5本は本プロジェクトの流儀", "順張り値", "trend", tb=_tb_slp_alma,
   # ★K-4＝1本ごとに 1 上げる足で、5本前からの変化＝5 ÷ (5本前の ALMA＝終値 − 5 − 遅れ) × 100。
   known=lambda p: [(_up(int(p[0]) + 40), [(-1, 5.0 / ((100.0 + int(p[0]) + 39) - 5.0 - _alma_lag(int(p[0]))) * 100.0, 1e-9)])],
   tb_kind="写し")
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
   "Gann HiLo Activator。高値13本平均・安値21本平均を、終値の上抜け／下抜けで切り替える（ライブラリの既定）。★ライブラリの流儀＝比べる相手は前の足までの高値の平均（前の13本）、線の値は今の足を含む21本の安値の平均（pandas_ta_classic overlap/hilo.py:50）。LuxAlgo の逐語「LoAvg_t = (Σ L_{t-i} over i = 1..n) / n」は今の足を含まない＝1本ごとに 1 上げる足では線が 終値 − 12 になり、この版の 終値 − 11 と違う（監査 CP82）",
   "反転サイン", "none", tb=_tb_pos_hilo,
   # ★K-4（監査 CP60 の修正59）＝定義（Krausz＝前の13本の高値の平均を終値が上抜けたら、21本の安値の平均の線）から導いた既知答え
   #   ＝1本ごとに 1 上げる足（高値＝終値・安値＝前の終値）では、終値は常に高値の平均の上＝線は安値の平均＝終値 − 11。
   known=lambda p: [(_up(80), [(-1, (179.0 / 168.0 - 1.0) * 100.0, 1e-9)])], tb_kind="写し")
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
   "n 本の直線あてはめの傾きを角度（度）にしたもの。傾きは「1本あたり何%動くか」で測る",
   "標準（Linear Regression Angle）は arctan(1本あたり何ドル動くか) だが、それだと値段の帯が変わると "
   "同じ動きでも角度が変わる＝H6 違反（実測＝4本値を2倍にすると値が変わる・検査13）。"
   "★うちは傾きを終値で割って%にしてから角度にする（本プロジェクトの流儀・2026-08-11）。"
   "★経緯＝2026-08-11 に私が一度「外す」と決めたが、それは私の勝手な判断だった（まこさん指摘）。"
   "要件のハード制約に反する指標は、外すのではなく直して使う。"
   "★この形は既に在る LRslope% の単調変換（実測＝順位の相関 1.0000000000）＝重複の候補。"
   "どちらを省くかは まこさんが決める（検査12 の一覧に出る）",
   "順張り値", "trend", tb=_tb_lrangle)



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
# ★2026-08-16（段A の A-6）＝名前に数字を2つ出した＝(1回あたりの本数, 何回 重ねがけするか)。
#   直す前は1回あたりの本数がライブラリの既定 2 に隠れていて、変えると同じ名前のまま中身が変わった。
_r(r"close vs RAINBOW%\((\d+),(\d+)\)", "close vs RAINBOW%",
   "終値が RAINBOW（n本の単純移動平均を k 回 重ねがけした線）から何%離れているか",
   "ライブラリの計算式。前の出力にまた同じ移動平均を掛ける", "反転サイン", "trend", tb=_tb_pos_rainbow)
_r(r"RAINBOW\((\d+),(\d+)\)傾き%", "RAINBOW傾き%", "その線の5本前からの変化率%", "同上", "順張り値", "trend",
   tb=_tb_slp_rainbow)
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
# ★K-4（監査 CP60 の修正60）＝下の CKSP・PMAX・PSAR・SAREXT の既知答えに「下げ続ける合成のバー」を足した。
#   足＝_dn(600, 1000.0, 1.0)（終値 1000 から1本ごとに 1 下げる・始値＝前の終値・高値＝始値・安値＝終値）。最後の終値 c＝401。
#   答えは定義から導いた（ライブラリは見ていない）＝
#   ・PSAR（Wilder）＝売り側。SAR_t＝SAR_{t−1}＋AF×(EP_{t−1}−SAR_{t−1})。毎本 新しい安値なので AF は 0.02 ずつ増えて 0.2 で頭打ち。
#     EP_{t−1}＝前の終値＝c＋1。SAR と EP の差 g は g←0.8×(g＋1) で 4 に収束＝SAR＝c＋5 → close vs PSAR%＝(c/(c+5)−1)×100・加速 0.2・反転 0。
#   ・SAREXT（TA-Lib）＝売り側の加速の上限が既定の 0.2（ta-lib.org の既定 optInAccelerationMaxShort＝0.2）なら、下げ続ける足では PSAR と同じ漸化式の
#     収束点＝SAR＝c＋5（この文は TA-Lib のページの文ではなく、定義から導いた文）。TA-Lib は売り側を負で返す（ta-lib.org「Output is +SAR when long,
#     -SAR when short.」）ので、絶対値に直してから割る＝(c/(c+5)−1)×100。
#   ・CKSP（数は TradingView の組み込みと同じ p=10・x=1・q=9・ATR は Wilder。列の名前はライブラリ pandas_ta_classic の向き）＝真の値幅は毎本 1 → ATR＝1。
#     CKSPl（ライブラリの long＝直近 q 本の max(10本高値 − ATR)。TradingView の組み込みと ProRealCode は、この線を Stop Short と呼ぶ）
#     ＝(c＋8＋10)−1＝c＋17（10本高値は 9本前の高値＝終値＋10、q 本の中で最大は 8本前）→ (c/(c+17)−1)×100。
#     CKSPs（ライブラリの short＝直近 q 本の min(10本安値 ＋ ATR)。TradingView の組み込みは Stop Long と呼ぶ）＝今の安値 c ＋ 1 → (c/(c+1)−1)×100。
#   ・PMAX（EMA10 ± 3×ATR10・下げでは上の帯）＝1本ごとに 1 下げる足で EMA10 の遅れは (10−1)/2＝4.5・ATR＝1 → 線＝c＋4.5＋3 → (c/(c+7.5)−1)×100。
#   値段が一定の足（0）だけでは売り側を一度も通らない（監査 CP60 の修正60 の文）。
_r(r"close vs CKSPl%", "close vs CKSPl%",
   "終値が Chande Kroll の売り側の逆指値（TradingView の組み込みの Stop Short＝直近 q 本の max(p 本高値 − x×ATR)）から何%離れているか",
   "Chande & Kroll。★独立実装は書いていないが、定義から導ける既知答えで検証する＝"
   "値段が一定なら逆指値も その値に張り付くので、この列は ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)]),
                                          (_dn(600, 1000.0, 1.0), [(-1, (401.0 / (401.0 + 17.0) - 1.0) * 100.0, 1e-6)])])
_r(r"close vs CKSPs%", "close vs CKSPs%",
   "終値が Chande Kroll の買い側の逆指値（TradingView の組み込みの Stop Long＝直近 q 本の min(p 本安値 ＋ x×ATR)）から何%離れているか", "同上",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)]),
                                          (_dn(600, 1000.0, 1.0), [(-1, (401.0 / (401.0 + 1.0) - 1.0) * 100.0, 1e-6)])])
_r(r"DPO%(\d+)", "DPO%",
   "デトレンド振動子。終値から「n本平均を (n/2+1) 本ずらしたもの」を引き、終値で割って%化",
   "標準（Detrended Price Oscillator）。★ライブラリの既定 centered=True は未来を見る"
   "（値を未来の足の方へずらす書き方を使う・2026-08-09 実測）ので、必ず centered=False で呼ぶ。"
   "%化は H6 のための本プロジェクトの流儀",
   "反転サイン", "none", tb=_tb_dpo,
   # ★K-4（監査 CP60 の修正59）＝流儀の欄の定義（終値 − n本平均を (n/2+1) 本ずらしたもの）から導いた既知答え
   #   ＝1本ごとに 1 上げる足では (n/2+1) ＋ (n−1)/2 を終値で割って%化。教科書の版（DPO教科書%）とは別の値になる。
   known=lambda p: [(_up(int(p[0]) * 2 + 40), [(-1, ((int(0.5 * int(p[0])) + 1) + (int(p[0]) - 1) / 2.0) / (100.0 + int(p[0]) * 2 + 39) * 100.0, 1e-9)])],
   tb_kind="写し")
_r(r"close vs PMAX%", "close vs PMAX%",
   "終値が PMAX（移動平均に値動きの荒さを足した追従線）から何%離れているか",
   "ライブラリの計算式。★定義から導ける既知答えで検証する＝値段が一定なら ぴったり 0・下げ続ける足なら EMA10＋3×ATR10 の上の帯（K-4）",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)]),
                                          (_dn(600, 1000.0, 1.0), [(-1, (401.0 / (401.0 + 7.5) - 1.0) * 100.0, 1e-6)])])
_r(r"close vs PSAR%", "close vs PSAR%",
   "終値がパラボリック SAR（放物線の逆指値）から何%離れているか",
   "Wilder（Parabolic SAR）。買い側と売り側のうち、そのとき出ている方を使う。"
   "★定義から導ける既知答えで検証する＝値段が一定なら ぴったり 0・下げ続ける足なら売り側の SAR＝終値＋5（K-4）",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)]),
                                          (_dn(600, 1000.0, 1.0), [(-1, (401.0 / (401.0 + 5.0) - 1.0) * 100.0, 1e-6)])])
_r(r"PSAR加速", "PSAR加速",
   "パラボリック SAR の加速係数（0.02 ずつ増えて 0.2 で頭打ち）",
   "Wilder。★定義から導ける既知答えで検証する＝値段が一定なら加速しないので初期値 0.02 のまま・下げ続ける足なら頭打ちの 0.2（K-4）",
   "状態量", "none", known=lambda p: [(_flat(600), [(-1, 0.02, 1e-9)]), (_dn(600, 1000.0, 1.0), [(-1, 0.2, 1e-9)])])
_r(r"PSAR反転", "PSAR反転",
   "パラボリック SAR が反転した足か。1 か 0",
   "同上。★既知答えで検証する＝値段が一定なら反転しないので 0・下げ続ける足でも反転しないので 0（K-4）", "状態量", "none",
   known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)]), (_dn(600, 1000.0, 1.0), [(-1, 0.0, 1e-9)])])
_r(r"QSTICK%(\d+)", "QSTICK%",
   "Qスティック。（終値 − 始値）の n 本平均を、終値で割って%化",
   "Tushar Chande。★値段そのものではなく差なので、終値で割って%にする（H6）",
   "順張り値", "trend", tb=_tb_qstick)
_r(r"close vs SAREXT%", "close vs SAREXT%",
   "終値が 拡張パラボリック SAR から何%離れているか",
   "TA-Lib（SAREXT）。★定義から導ける既知答えで検証する＝値段が一定なら逆指値も その値に張り付くので"
   "この列は ぴったり 0。下げ続ける足なら PSAR と同じ線（終値＋5・絶対値に直してから割る＝K-4）", "反転サイン", "none",
   known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)]), (_dn(600, 1000.0, 1.0), [(-1, (401.0 / (401.0 + 5.0) - 1.0) * 100.0, 1e-6)])])
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


# ══ 業界の指標（volume 16関数）＝独立実装・外部照合・登録（2026-08-10・フロー 段6-1 の4回目）══
#
# ★出来高系の指標は、ライブラリが返す値をそのまま材料にできません。3つの理由があります。
#   ① 積み上げ型（AD・PVT・NVI・PVI・WAD・OBV）は日が経つほど値が大きくなり続けます。
#      値そのものには意味が無く、意味があるのは「直近 n 本でどれだけ増えたか」です。
#   ② 出来高の大きさに引きずられます（取引所が成長すると同じ値動きでも値が大きくなる）。
#   ③ 「値段 × 出来高」の型は値段にも引きずられます＝H6（価格非依存）違反です。
#
# ★直し方は、既に在る OBV傾き と同じ形にそろえることです（新しい流儀を作りません）。
#   (1) 積み上げ型      … n 本の増分 ÷ 同じ n 本の出来高の合計（−1〜+1 の加重平均になる）
#   (2) 出来高スケール型 … 同じ本数の出来高の平均で割る（ADOSC・KVO）
#   (3) 値段×出来高型   … 終値と平均出来高で割る（EFI・PVOL）
#   (4) 値段²÷出来高型  … 平均出来高を掛けて、終値の2乗で割る（EOM・MARKETFI）
#   WAD だけは積み上げが値段の単位なので、増分を終値で割って%にします（QSTICK% と同じ流儀）。
def _clv_ad(h, l, c, v):
    """AD（集積・拡散）の積み上げ。CLV＝(2c−h−l)/(h−l) を出来高で重みづけて足す。"""
    rng = h - l
    clv = np.where(rng > 0, (2.0 * c - h - l) / np.where(rng > 0, rng, 1.0), 0.0)
    return np.cumsum(clv * v)


def _cum_slope(cum, v, n, d):
    """積み上げの n 本の増分 ÷ 同じ n 本の出来高の合計。"""
    out = np.full(len(cum), np.nan)
    out[n:] = _div(cum[n:] - cum[:-n], _roll(v, n, "sum")[n:])
    return _S(out, d)


def _roc1(c):
    r = np.full(len(c), np.nan)
    r[1:] = (c[1:] / c[:-1] - 1.0) * 100.0
    return r


def _tb_adosc(d, p):
    """チャイキン振動子＝AD の 3本 EMA − 10本 EMA。ライブラリは種を AD の1本目に置く
    （実物の逐語＝fast_ema = ad_arr[0]）ので、教科書の漸化式 _ema_rec と同じ形になる。"""
    o, h, l, c, v = _arr(d)
    ad = _clv_ad(h, l, c, v)
    return _S(_div(_ema_rec(ad, 3) - _ema_rec(ad, 10), _roll(v, 10, "mean")), d)


def _tb_aobv_lr(d, p):
    """AOBV の買い側。OBV の 4本 EMA と 12本 EMA から作る 0/1。
    ★式を読むと slow は打ち消されて効かない＝(inc(fast)&dec(slow))|(inc(fast)&inc(slow))。
      売り側 SR はその裏返しなので入れない（AMAT と同じ作り・実測でも食い違いは暖機だけ）。"""
    o, h, l, c, v = _arr(d)
    obv = np.zeros(len(c))
    for i in range(1, len(c)):
        s = np.sign(c[i] - c[i - 1])
        obv[i] = obv[i - 1] + (0.0 if np.isnan(s) else s) * v[i]
    f, s2 = _ema_seed(obv, 4), _ema_seed(obv, 12)
    df, ds = np.full(len(c), np.nan), np.full(len(c), np.nan)
    df[2:], ds[2:] = f[2:] - f[:-2], s2[2:] - s2[:-2]
    return _S((((df > 0) & (ds < 0)) | ((df > 0) & (ds > 0))).astype(float), d)


def _tb_efi(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    pv = np.full(len(c), np.nan)
    pv[1:] = (c[1:] - c[:-1]) * v[1:]
    return _S(_div(_ema_seed(pv, n) * 100.0, c * _roll(v, n, "mean")), d)


def _eom_raw(h, l, v):
    """イーズ・オブ・ムーブメントの素の値＝中値の動き ÷（出来高 ÷ 1e8 ÷ 値幅）。"""
    hl2 = 0.5 * (h + l)
    dist = np.full(len(hl2), np.nan)
    dist[1:] = hl2[1:] - hl2[:-1]
    return _div(dist * (h - l) * 1e8, v)


def _tb_eom(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    eom = _roll(_eom_raw(h, l, v), n, "mean")
    return _S(_div(eom * _roll(v, n, "mean") * 1e4, c * c * 1e8), d)


def _tb_marketfi(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    return _S(_div((h - l) * _roll(v, n, "mean") * 100.0, v * c), d)


def _pvni_slope(d, p, side):
    """出来高が増えた足（side=+1）／減った足（side=−1）の変化率だけを積み上げ、n 本の増分を出す。"""
    n = p[0]
    o, h, l, c, v = _arr(d)
    roc = _roc1(c)
    dv = np.full(len(c), np.nan)
    dv[1:] = v[1:] - v[:-1]
    take = (dv > 0) if side > 0 else (dv < 0)
    cum = np.cumsum(np.where(take & ~np.isnan(roc), np.nan_to_num(roc), 0.0))
    out = np.full(len(c), np.nan)
    out[n:] = cum[n:] - cum[:-n]
    return _S(out, d)


def _tb_nvi_slope(d, p):
    return _pvni_slope(d, p, -1)


def _tb_pvi_slope(d, p):
    return _pvni_slope(d, p, +1)


def _tb_pvol_ratio(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    pv = c * v
    return _S(_div(pv, _roll(pv, n, "mean")), d)


def _tb_pvt_slope(d, p):
    o, h, l, c, v = _arr(d)
    roc = _roc1(c)
    return _cum_slope(np.cumsum(np.where(np.isnan(roc), 0.0, roc) * v), v, p[0], d)


def _tb_wad_slope(d, p):
    """ウィリアムズの集積・拡散。上げた足は 終値−真の安値、下げた足は 終値−真の高値 を積む。"""
    n = p[0]
    o, h, l, c, v = _arr(d)
    pc = np.roll(c, 1)
    pc[0] = np.nan
    trh, trl = np.maximum(h, pc), np.minimum(l, pc)
    day = np.where(c > pc, c - trl, np.where(c < pc, c - trh, 0.0))
    cum = np.cumsum(np.where(np.isnan(day), 0.0, day))
    out = np.full(len(c), np.nan)
    out[n:] = (cum[n:] - cum[:-n]) / c[n:] * 100.0
    return _S(out, d)


def _kvo_parts(d):
    o, h, l, c, v = _arr(d)
    hlc3 = (h + l + c) / 3.0
    dh = np.full(len(c), np.nan)
    dh[1:] = hlc3[1:] - hlc3[:-1]
    sg = np.where(dh > 0, 1.0, np.where(dh < 0, -1.0, 0.0))
    sg[0] = 1.0                                   # ライブラリの初期値（signed_series の initial=1）
    sv = sg * v
    kvo = _ema_seed(sv, 34) - _ema_seed(sv, 55)
    return kvo, _ema_seed(kvo, 13), _roll(v, 55, "mean")


def _tb_kvo(d, p):
    kvo, _sig, vm = _kvo_parts(d)
    return _S(_div(kvo, vm), d)


def _tb_kvos(d, p):
    _kvo, sig, vm = _kvo_parts(d)
    return _S(_div(sig, vm), d)


def _tb_vosc(d, p):
    o, h, l, c, v = _arr(d)
    fast, slow = _roll(v, 14, "mean"), _roll(v, 28, "mean")
    return _S(100.0 * _div(fast - slow, slow), d)


# ── 外部ライブラリ ta による照合（非同型の相手。volume は3種を ta が持っている）──
def _ext_efi(d, p):
    n = p[0]
    fi = _ta.volume.ForceIndexIndicator(d.close, d.volume, n).force_index()
    return fi / (d.close * d.volume.rolling(n).mean()) * 100.0


def _ext_eom(d, p):
    n = p[0]
    e = _ta.volume.EaseOfMovementIndicator(d.high, d.low, d.volume, n).sma_ease_of_movement()
    return e * d.volume.rolling(n).mean() * 1e4 / (d.close * d.close * 1e8)


def _ext_pvt_slope(d, p):
    n = p[0]
    # ★ta は変化率を小数で積み、pandas-ta は%で積む＝100 倍の違い（実測＝比 100.0000000）。
    pvt = _ta.volume.VolumePriceTrendIndicator(d.close, d.volume).volume_price_trend() * 100.0
    return pvt.diff(n) / d.volume.rolling(n).sum().replace(0, np.nan)


# ── 既知答え用の合成バー（volume 用・定義から期待値が決まるものだけ）──
def _bar_clv(n, top=True):
    """終値が高値に張り付く（CLV＝+1）／安値に張り付く（CLV＝−1）バー。出来高は 1 で一定。"""
    hi, lo = np.full(n, 100.0), np.full(n, 99.0)
    c = hi.copy() if top else lo.copy()
    return _mk(c, o=c, h=hi, l=lo)


def _bar_hl(n, hi=101.0, lo=99.0, vol=2.0):
    """終値・高値・安値・出来高がすべて一定のバー（中値が動かない＝EOM は 0）。"""
    c = np.full(n, 100.0)
    return _mk(c, o=c, h=np.full(n, hi), l=np.full(n, lo), v=np.full(n, vol))


def _bar_vslope(n, up_vol=True):
    """終値は上げ続け、出来高は1本ずつ増える（または減る）バー。"""
    c = 100.0 + 0.01 * np.arange(n)
    v = 1.0 + np.arange(n, dtype=float)
    return _mk(c, o=c, h=c, l=c, v=(v if up_vol else v[::-1].copy()))


# ★AD（集積・拡散）は列にしない。増分を出来高の合計で割ると、式の上で CMF そのものになるため
#   （CMF の定義＝Σ(CLV×出来高) ÷ Σ出来高 ＝ AD の n 本の増分 ÷ 同じ n 本の出来高の合計）。
#   2026-08-10 の総当たりの重複検出が「AD傾き20 ＝ 1×CMF20（ずれ 1.0e-10）」で捕まえた。
#   ライブラリの ad は、うちの CMF が既に押さえている（対応表の CMF の行に書いた）。
_r(r"ADOSC比", "ADOSC比",
   "チャイキン振動子（AD の 3本 EMA − 10本 EMA）を、10本の平均出来高で割った値",
   "Chaikin。ライブラリは EMA の種を AD の1本目に置く（実物の逐語＝fast_ema = ad_arr[0]）。"
   "出来高の大きさに引きずられないよう平均出来高で割る（H6）",
   "順張り値＝プラスで買い集めが加速", "trend", tb=_tb_adosc,
   known=lambda p: [(_bar_clv(600, True), [(-1, 3.5, 1e-6)])])
_r(r"AOBV_LR", "AOBV_LR",
   "OBV の 4本 EMA と 12本 EMA から作る買い側の 0/1",
   "Archer OBV。★式の上で slow は打ち消されて効かず、売り側 SR は買い側の裏返し＝買い側の1列だけ入れる"
   "（AMAT と同じ作り。実測＝LR+SR≠1 の足は 158,112 本中 13 本で、位置は 0〜12 の暖機だけ）",
   "順張り値＝1 で OBV が上向き", "trend", tb=_tb_aobv_lr,
   known=lambda p: [(_up(600), [(-1, 1.0, 1e-9)]), (_dn(600), [(-1, 0.0, 1e-9)])])
_r(r"EFI比(\d+)", "EFI比",
   "エルダーの勢力指数（終値の差×出来高 の n 本 EMA）を、終値と平均出来高で割って%化",
   "Alexander Elder。値段×出来高の単位なので、終値と平均出来高の両方で割って無次元にする（H6）",
   "順張り値＝プラスで買いの勢力が優勢", "trend", tb=_tb_efi, ext=_ext_efi,
   known=lambda p: [(_flat(p[0] + 40), [(-1, 0.0, 1e-9)])])
_r(r"EOM比(\d+)", "EOM比",
   "イーズ・オブ・ムーブメント（中値の動き ÷ 出来高の厚み）の n 本平均を、平均出来高と終値²で無次元化。"
   "＝『中値の動き%』×『値幅%』÷『出来高が平均の何倍か』の n 本平均",
   "Richard Arms。素の値は 値段²÷出来高 の単位（ライブラリの divisor＝1e8）。"
   "平均出来高を掛けて終値の2乗で割り、1e8 を戻す。最後の 1e4 は%が2つ（中値の動き%×値幅%）ぶん（H6）",
   "順張り値＝プラスで少ない出来高でも上に動きやすい", "trend", tb=_tb_eom, ext=_ext_eom,
   known=lambda p: [(_bar_hl(p[0] + 40), [(-1, 0.0, 1e-9)])])
_r(r"MARKETFI比(\d+)", "MARKETFI比",
   "値幅 ÷ 出来高（ビル・ウィリアムズの市場ファシリテーション指数）を、平均出来高と終値で無次元化",
   "Bill Williams。値段÷出来高の単位なので、平均出来高を掛けて終値で割る（H6）。"
   "出来高が平均どおりのときは 値幅の終値に対する% と同じ値になる",
   "状態量＝大きいほど少ない出来高で値幅が出た（向きは持たない）", "none", tb=_tb_marketfi,
   known=lambda p: [(_bar_hl(p[0] + 40), [(-1, 2.0, 1e-9)])])
_r(r"NVI傾き(\d+)", "NVI傾き",
   "出来高が減った足の変化率だけを積み上げた指数（NVI）の n 本の増分",
   "Paul Dysart / Norman Fosback。積み上げの値そのものは意味を持たない（起点が 1000 の定数）ので"
   "増分を見る。変化率%の足し算なので、そのままで無次元",
   "順張り値＝プラスで、商いの薄い足で上げている", "trend", tb=_tb_nvi_slope,
   known=lambda p: [(_bar_vslope(p[0] + 40, True), [(-1, 0.0, 1e-9)]),
                    (_bar_vslope(p[0] + 40, False), [(-1, "+", 0.0)])])
_r(r"PVI傾き(\d+)", "PVI傾き",
   "出来高が増えた足の変化率だけを積み上げた指数（PVI）の n 本の増分", "同上（NVI の裏側）",
   "順張り値＝プラスで、商いの厚い足で上げている", "trend", tb=_tb_pvi_slope,
   known=lambda p: [(_bar_vslope(p[0] + 40, False), [(-1, 0.0, 1e-9)]),
                    (_bar_vslope(p[0] + 40, True), [(-1, "+", 0.0)])])
_r(r"PVOL比(\d+)", "PVOL比",
   "売買代金（終値×出来高）が、n 本平均の何倍か",
   "標準。値段×出来高の単位なので、同じ売買代金の平均で割って倍率にする（H6・volume_ratio と同じ形）",
   "状態量＝大きいほど売買代金が多い", "none", tb=_tb_pvol_ratio,
   known=lambda p: [(_flat(p[0] + 40), [(-1, 1.0, 1e-9)])])
_r(r"PVT傾き(\d+)", "PVT傾き",
   "価格・出来高トレンド（変化率%×出来高 の積み上げ）の n 本の増分を、同じ n 本の出来高の合計で割った値",
   "標準。出来高で重みづけた n 本の平均変化率%になる（H6・OBV傾き と同じ流儀）",
   "順張り値＝プラスで出来高を伴って上げている", "trend", tb=_tb_pvt_slope, ext=_ext_pvt_slope,
   known=lambda p: [(_flat(p[0] + 40), [(-1, 0.0, 1e-9)])])
_r(r"WAD傾き(\d+)", "WAD傾き",
   "ウィリアムズの集積・拡散（上げた足は 終値−真の安値、下げた足は 終値−真の高値 を積む）の n 本の増分を終値で割って%化",
   "Larry Williams。積み上げが値段の単位なので、増分を終値で割る（H6・QSTICK% と同じ流儀）",
   "順張り値＝プラスで買い集めが優勢", "trend", tb=_tb_wad_slope,
   known=lambda p: [(_up(p[0] + 40), [(-1, "+", 0.0)]), (_dn(p[0] + 40), [(-1, "-", 0.0)])])
_r(r"KVO比", "KVO比",
   "クリンガー出来高振動子（向きつき出来高の 34本 EMA − 55本 EMA）を、55本の平均出来高で割った値",
   "Stephen Klinger。向きは hlc3 の前足との差で決める。出来高の大きさに引きずられないよう平均出来高で割る（H6）。"
   "★2つの EMA の差は、向きつき出来高が『増えているか』にだけ反応する＝値動きの向きそのものには反応しない。"
   "出来高が一定なら、ずっと上げでも ずっと下げでも 0 になる（2026-08-10 実測＝どちらも +0.000000）。"
   "だから順張り値ではない",
   "状態量＝プラスで買い方向の出来高の流れが強まっている（上げ相場で大きくなるとは限らない）", "none", tb=_tb_kvo,
   known=lambda p: [(_bar_vslope(800, True), [(-1, 10.5 / 773.0, 1e-6)]),
                    (_flat(600), [(-1, 0.0, 1e-9)])])
_r(r"KVOシグナル比", "KVOシグナル比",
   "KVO の 13本 EMA を、55本の平均出来高で割った値", "同上（KVO を平らにしたもの＝性質は同じ）",
   "状態量＝プラスで買い方向の出来高の流れが強まっている（上げ相場で大きくなるとは限らない）", "none", tb=_tb_kvos,
   known=lambda p: [(_bar_vslope(800, True), [(-1, 10.5 / 773.0, 1e-6)]),
                    (_flat(600), [(-1, 0.0, 1e-9)])])
# ══ まこさん承認で足した2件（2026-08-10・逐語「１，２は修正して残す」）════════════════
# ★経緯＝「入れない」に置いていた2件を、まこさんの決定「完全に不要な指標以外はすべて入れてほしい」
#   に照らして入れ直した。CC の判断が狭かった（worklog 20260810 §21）。
#   ① VFI ＝ライブラリの実装が壊れていて全部ゼロだった。教科書の式（Markos Katsanos）で書き直す。
#      違い＝値動きの足切りを『対数リターンの標準偏差 × 0.2 × 終値』で作る
#      （ライブラリは『0.2 × 終値』＝終値の20%で、5分足では一度も超えない）。
#   ② 出来高変化率% ＝pvr（1〜4 の区分）の中身の半分。うちの材料に無いことを実測で確かめた
#      （volume_ratio20 ≥ 1 との一致率 0.6737＝別のもの）。pvr の区分そのものは入れない。
def _vfi_parts(h, l, c, v, n):
    """VFI の素材。typ＝代表値段／cutoff＝値動きの足切り／vave＝前の足までの平均出来高。"""
    typ = (h + l + c) / 3.0
    inter = np.full(len(c), np.nan)
    inter[1:] = np.log(typ[1:]) - np.log(typ[:-1])
    cutoff = 0.2 * _roll(inter, 30, "std", ddof=1) * c        # 教科書＝coef 0.2・標準偏差は30本
    vave = np.full(len(c), np.nan)
    vave[1:] = _roll(v, n, "mean")[:-1]                       # 前の足まで（未来を見ない）
    mf = np.full(len(c), np.nan)
    mf[1:] = typ[1:] - typ[:-1]
    return typ, cutoff, vave, mf


def _tb_vfi(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    _typ, cutoff, vave, mf = _vfi_parts(h, l, c, v, n)
    vc = np.minimum(v, vave * 2.5)                            # 教科書＝vcoef 2.5 で出来高の上を切る
    sg = np.where(np.abs(mf) > cutoff, np.sign(mf), 0.0)
    return _S(_ema_rec(_div(_roll(vc * sg, n, "sum"), vave), 3), d)


def _tb_vol_roc(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    out = np.full(len(v), np.nan)
    out[n:] = (_div(v[n:], v[:-n]) - 1.0) * 100.0
    return _S(out, d)


def _bar_geo(n, r=1.001, up=True, vol=3.0):
    """一定の比で上げ続ける（または下げ続ける）バー。対数リターンが完全に一定になるので、
    VFI の足切り（対数リターンの標準偏差）がちょうど 0 になり、期待値が定義から決まる。"""
    c = 100.0 * (r ** np.arange(n)) if up else 100.0 * (r ** -np.arange(n))
    o = np.roll(c, 1)
    o[0] = c[0]
    return _mk(c, o=o, h=np.maximum(o, c), l=np.minimum(o, c), v=np.full(n, vol))


_r(r"VFI(\d+)", "VFI",
   "出来高の勢い指数。値動きが足切りを超えた足だけ、出来高に向きの符号を付けて n 本 足し、"
   "同じ n 本の平均出来高で割った値（の3本 EMA）",
   "Markos Katsanos（VFI）。★ライブラリ pandas-ta-classic の実装は使わない＝足切りを『0.2×終値』"
   "（終値の20%）としているため、5分足では一度も超えず値が常に 0 になる（2026-08-10 実測＝"
   "157,851本すべて 0）。教科書どおり足切りを『対数リターンの30本標準偏差 × 0.2 × 終値』にした。"
   "出来高で割るので無次元（H6）",
   "順張り値＝プラスで買い方向の出来高が優勢", "trend", tb=_tb_vfi,
   known=lambda p: [(_bar_geo(p[0] + 60, up=True), [(-1, float(p[0]), 1e-9)]),
                    (_bar_geo(p[0] + 60, up=False), [(-1, -float(p[0]), 1e-9)]),
                    (_flat(p[0] + 60), [(-1, 0.0, 1e-9)])])
_r(r"出来高変化率%(\d+)", "出来高変化率%",
   "出来高が n 本前から何%増えたか（減ったか）",
   "標準。もともと比率なので無次元（H6）。★pvr（1〜4 の区分）の中身の半分＝『出来高が前の足より"
   "増えたか』を材料にしたもの。既にある volume_ratio は『n 本平均の何倍か』で別のもの"
   "（2026-08-10 実測＝『前の足より増えた』との一致率 0.6737）",
   "状態量＝プラスで出来高が増えた（値動きの向きは持たない）", "none", tb=_tb_vol_roc,
   known=lambda p: [(_flat(p[0] + 40), [(-1, 0.0, 1e-9)])])


# ══ 業界の指標（statistics 13関数）＝独立実装・登録（2026-08-10・フロー 段6-1 の5回目）══
# ★13関数のうち 8件は入れない（理由は INDUSTRY_SKIP に1件ずつ）。
#   なかでも tos_stdevall は★未来を見る（既定で「データ全部」に回帰直線を引く）。
# ★歪度・尖度の流儀＝不偏（G1・G2）。素の積率ではない（2026-08-10 実測＝不偏なら差 1e-15・素なら 0.32/4.5）。
def _mom_win(x, n):
    """窓ごとの平均まわりの積率（m2・m3・m4）と、窓の中身。"""
    w = _swv(x, n)
    dv = w - w.mean(axis=1, keepdims=True)
    return dv, (dv ** 2).mean(axis=1), (dv ** 3).mean(axis=1), (dv ** 4).mean(axis=1)


def _tb_skew(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    out = np.full(len(c), np.nan)
    if len(c) >= n:
        _dv, m2, m3, _m4 = _mom_win(c, n)
        out[n - 1:] = m3 / m2 ** 1.5 * np.sqrt(n * (n - 1)) / (n - 2)
    return _S(out, d)


def _tb_kurtosis(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    out = np.full(len(c), np.nan)
    if len(c) >= n:
        dv, m2, _m3, _m4 = _mom_win(c, n)
        s4 = (m2 * n / (n - 1)) ** 2
        out[n - 1:] = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * ((dv ** 4).sum(axis=1) / s4) \
            - 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    return _S(out, d)


def _tb_mad(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    out = np.full(len(c), np.nan)
    if len(c) >= n:
        w = _swv(c, n)
        out[n - 1:] = np.abs(w - w.mean(axis=1, keepdims=True)).mean(axis=1)
    return _S(out / c * 100.0, d)


def _tb_stdev_pct(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    return _S(_roll(c, n, "std", ddof=0) / c * 100.0, d)


def _tb_median(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    out = np.full(len(c), np.nan)
    if len(c) >= n:
        out[n - 1:] = np.median(_swv(c, n), axis=1)
    return _S((c / out - 1.0) * 100.0, d)


def _tb_median_slope(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    out = np.full(len(c), np.nan)
    if len(c) >= n:
        out[n - 1:] = np.median(_swv(c, n), axis=1)
    sl = np.full(len(c), np.nan)
    sl[5:] = (out[5:] / out[:-5] - 1.0) * 100.0
    return _S(sl, d)


def _bar_alt(n, level=100.0, amp=1.0):
    """100 を挟んで ±1 を交互に並べたバー（平均 100・母標準偏差 1・歪度 0）。"""
    c = level + np.where(np.arange(n) % 2 == 0, -amp, amp)
    return _mk(c, o=c, h=c, l=c)


_r(r"skew(\d+)", "skew",
   "直近 n 本の終値の歪度（分布の左右の偏り・不偏の G1）",
   "標準（不偏＝m3/m2^1.5 × √(n(n−1))/(n−2)）。2026-08-10 実測でライブラリと 1.8e-15 で一致。"
   "★まっすぐ上げ続けるだけの形では 0 になる＝向きの指標ではない",
   "状態量＝プラスで、窓の中の低い値段に長くとどまり最後に上へ伸びた形（向きは持たない）", "none",
   tb=_tb_skew, known=lambda p: [(_bar_alt(p[0] + 40), [(-1, 0.0, 1e-9)])])
_r(r"kurtosis(\d+)", "kurtosis",
   "直近 n 本の終値の尖度（分布の裾の厚み・不偏の G2・正規分布で 0）",
   "標準（不偏の G2）。2026-08-10 実測でライブラリと 8.9e-15 で一致",
   "状態量＝大きいほど裾が厚い（向きは持たない）", "none", tb=_tb_kurtosis,
   known=lambda p: [(_bar_alt(p[0] + 40), [(-1, -2.0 * (p[0] - 1) / (p[0] - 3), 1e-9)])])
_r(r"MAD比(\d+)", "MAD比",
   "直近 n 本の終値の平均絶対偏差を、終値で割って%化",
   "標準。値段の単位なので終値で割る（H6）。★窓の中の各足について「窓の平均からの離れ」を測って平均する"
   "（いまの足と平均の差ではない）",
   "ボラ量", "vol", tb=_tb_mad,
   known=lambda p: [(_bar_alt(p[0] + 40), [(-1, 100.0 / 101.0, 1e-9)])])
_r(r"stdev%(\d+)", "stdev%",
   "直近 n 本の終値の標準偏差を、終値で割って%化",
   "標準（母標準偏差＝ddof 0。2026-08-10 実測でライブラリの stdev は ddof=0）。値段の単位なので終値で割る（H6）",
   "ボラ量", "vol", tb=_tb_stdev_pct,
   known=lambda p: [(_bar_alt(p[0] + 40), [(-1, 100.0 / 101.0, 1e-9)])])
_r(r"close vs MEDIAN%(\d+)", "close vs MEDIAN%",
   "終値が、直近 n 本の終値の中央値から何%離れているか",
   "標準。値段そのものなので終値との距離%にする（H6・close vs SMA% と同じ流儀）",
   "順張り値", "trend", tb=_tb_median,
   known=lambda p: [(_flat(p[0] + 40), [(-1, 0.0, 1e-9)])])
_r(r"MEDIAN傾き%(\d+)", "MEDIAN傾き%",
   "直近 n 本の終値の中央値の、5本前からの変化率%", "同上（傾きの形）",
   "順張り値", "trend", tb=_tb_median_slope,
   known=lambda p: [(_flat(p[0] + 40), [(-1, 0.0, 1e-9)])])
_r(r"VOSC", "VOSC",
   "出来高振動子＝出来高の 14本平均と 28本平均の差を、28本平均で割った%",
   "標準（tulip の既定 14/28）。もともと比率なので、そのままで無次元",
   "状態量＝大きいほど直近の商いが厚い（向きは持たない）", "none", tb=_tb_vosc,
   known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)]),
                    (_bar_vslope(800, True), [(-1, 700.0 / 786.5, 1e-6)])])


# ══ 業界の指標（volatility 12関数）＝独立実装・登録（2026-08-10・フロー 段6-1 の6回目）══
# ★12関数のうち 1件は関数まるごと入れない（avolume＝うちの realized_vol の定数倍・実測）。
#   ほかに「関数の返す列の一部だけ入れない」ものが4件（理由は下の対応表 INDUSTRY_MAP に1件ずつ）。
# ★本数を2つ以上 自分で持つ指標（aberration・accbands・ce・hwc・massi・thermo）は、
#   ライブラリの既定をそのまま使う（本数を私が新しく作らない）＝volume の ADOSC・AOBV と同じ流儀。
# ★平滑の種の取り方は実測で突き止めた（2026-08-10）＝ATR は `_rma_seed`（種＝最初の n 本の単純平均）で
#   ライブラリと最大差 0〜2.8e-14 ／ EMA は `_ema_seed` で最大差 0。`_ema_rec`（先頭1本を種）では合わない。
_ABER_L, _ABER_A = 5, 15                 # aberration の既定（中心線の本数, ATR の本数）
_ACCB_L, _ACCB_C = 20, 4.0               # accbands の既定（本数, 帯の係数）
_CE_L, _CE_M = 22, 3.0                   # ce（シャンデリア・エグジット）の既定（本数, ATR の倍率）
_HW_NA, _HW_NB, _HW_NC, _HW_ND, _HW_S = 0.2, 0.1, 0.1, 0.1, 1.0   # hwc の既定
_MASSI_F, _MASSI_S = 9, 25               # massi の既定（EMA の本数, 合計する本数）
_THERMO_L = 20                           # thermo の既定（EMA の本数）


def _tr_lib(h: np.ndarray, l: np.ndarray, c: np.ndarray) -> np.ndarray:
    """真の値幅（ライブラリの流儀＝1本目は前の終値が無いので NaN）。上の `_tr` は1本目に高安差を入れる別流儀。"""
    out = np.full(len(c), np.nan)
    if len(c) > 1:
        pc = np.r_[np.nan, c[:-1]]
        out[1:] = np.nanmax(np.column_stack([(h - l)[1:], np.abs(h - pc)[1:], np.abs(pc - l)[1:]]), axis=1)
    return out


def _bar_fixed_range(n=80, level=100.0, half=1.0):
    """値段が一定で、1本ごとの値幅だけが一定（高値＝終値+half・安値＝終値−half）。
    値幅の変化を見る指標（CVI・MASSI・PDIST・TR）の既知答え用。"""
    c = np.full(n, level)
    return _mk(c, o=c, h=c + half, l=c - half)


def _aber_parts(d):
    """アバレーション＝HLC3 の n 本単純平均を中心線に、その上下へ ATR を足し引きした帯。"""
    o, h, l, c, v = _arr(d)
    zg = _roll((h + l + c) / 3.0, _ABER_L, "mean")
    atr = _rma_seed(_tr_lib(h, l, c), _ABER_A)
    return c, zg, zg + atr, zg - atr


def _tb_aber_zg(d, p):
    c, zg, _sg, _xg = _aber_parts(d)
    return _S((_div(c, zg) - 1.0) * 100.0, d)


def _tb_aber_pos(d, p):
    c, _zg, sg, xg = _aber_parts(d)
    return _S(_div(c - xg, sg - xg), d)


def _accb_parts(d):
    """アクセラレーション・バンド＝値幅の割合で高値・安値を広げてから n 本平均した帯。"""
    o, h, l, c, v = _arr(d)
    r = _ACCB_C * _div(h - l, h + l)
    return c, _roll(l * (1.0 - r), _ACCB_L, "mean"), _roll(h * (1.0 + r), _ACCB_L, "mean")


def _tb_accbl(d, p):
    c, lo, _up = _accb_parts(d)
    return _S((_div(c, lo) - 1.0) * 100.0, d)


def _tb_accbu(d, p):
    c, _lo, up = _accb_parts(d)
    return _S((_div(c, up) - 1.0) * 100.0, d)


def _ce_parts(d):
    """シャンデリア・エグジット＝n 本高値から ATR の m 倍を引いた線と、n 本安値に足した線。"""
    o, h, l, c, v = _arr(d)
    atr = _rma_seed(_tr_lib(h, l, c), _CE_L)
    return c, _roll(h, _CE_L, "max") - _CE_M * atr, _roll(l, _CE_L, "min") + _CE_M * atr


def _tb_ce_l(d, p):
    c, cl, _cs = _ce_parts(d)
    return _S((_div(c, cl) - 1.0) * 100.0, d)


def _tb_ce_s(d, p):
    c, _cl, cs = _ce_parts(d)
    return _S((_div(c, cs) - 1.0) * 100.0, d)


def _tb_cvi(d, p):
    """チャイキンのボラティリティ＝高安差の EMA が n 本前から何%増えたか。"""
    n = p[0]
    o, h, l, c, v = _arr(d)
    e = _ema_seed(h - l, n)
    prev = np.r_[np.full(n, np.nan), e[:-n]]
    return _S(100.0 * _div(e - prev, prev), d)


def _hw_parts(d):
    """ホルト・ウィンターズの水路＝水準・速さ・加速の3段の指数平滑で1本先を予測し、
    予測の外れ具合（分散の指数平滑）の平方根を上下に足し引きした帯。"""
    o, h, l, c, v = _arr(d)
    m = len(c)
    res = np.full(m, np.nan)
    up = np.full(m, np.nan)
    lo = np.full(m, np.nan)
    f = c[0] if m else np.nan
    vel = acc = var = 0.0
    prev_price = prev_res = c[0] if m else np.nan
    for i in range(m):
        f_new = (1.0 - _HW_NA) * (f + vel + 0.5 * acc) + _HW_NA * c[i]
        v_new = (1.0 - _HW_NB) * (vel + acc) + _HW_NB * (f_new - f)
        a_new = (1.0 - _HW_NC) * acc + _HW_NC * (v_new - vel)
        res[i] = f_new + v_new + 0.5 * a_new
        sd = var ** 0.5                      # ★1本前までの分散を使う（いまの足の分は入れない）
        up[i] = res[i] + _HW_S * sd
        lo[i] = res[i] - _HW_S * sd
        var = (1.0 - _HW_ND) * var + _HW_ND * (prev_price - prev_res) ** 2
        prev_price, prev_res = c[i], res[i]
        f, vel, acc = f_new, v_new, a_new
    return c, res, up, lo


def _tb_hw_pos(d, p):
    c, _res, up, lo = _hw_parts(d)
    return _S(_div(c - lo, up - lo), d)


def _tb_hw_width(d, p):
    c, _res, up, lo = _hw_parts(d)
    return _S(_div(up - lo, c) * 100.0, d)


def _tb_massi(d, p):
    """マス・インデックス＝高安差の EMA と、その EMA をもう1回 EMA した値の比を n 本 合計する。"""
    o, h, l, c, v = _arr(d)
    e1 = _ema_seed(h - l, _MASSI_F)
    e2 = _ema_seed(e1, _MASSI_F)
    return _S(_roll(_div(e1, e2), _MASSI_S, "sum"), d)


def _tb_pdist(d, p):
    """値段が動いた距離＝高安差の2倍 ＋ |始値 − 前の終値| − |終値 − 始値|。終値で割って%化。"""
    o, h, l, c, v = _arr(d)
    pc = np.r_[np.nan, c[:-1]]
    return _S(_div(2.0 * (h - l) + np.abs(o - pc) - np.abs(c - o), c) * 100.0, d)


def _tb_rvi(d, p):
    """相対ボラティリティ指数＝上げた足と下げた足それぞれに標準偏差を掛け、その EMA の比を 0〜100 にする。"""
    n = p[0]
    o, h, l, c, v = _arr(d)
    sd = _roll(c, n, "std", ddof=0)
    diff = np.r_[0.0, np.diff(c)]
    pa = _ema_seed(np.where(diff > 0, 1.0, 0.0) * sd, n)
    na = _ema_seed(np.where(diff < 0, 1.0, 0.0) * sd, n)
    return _S(100.0 * _div(pa, pa + na), d)


def _thermo_parts(d):
    """エルダーの温度計＝安値の下げ幅と高値の上げ幅の大きい方と、その EMA。"""
    o, h, l, c, v = _arr(d)
    pl = np.r_[np.nan, l[:-1]]
    ph = np.r_[np.nan, h[:-1]]
    tl = np.abs(pl - l)
    th = np.abs(h - ph)
    t = np.where(th < tl, tl, th)            # ★ライブラリは where で大きい方を残す＝実物の逐語で確認
    return c, t, _ema_seed(t, _THERMO_L)


def _tb_thermo_pct(d, p):
    c, t, _ma = _thermo_parts(d)
    return _S(_div(t, c) * 100.0, d)


def _tb_thermo_ratio(d, p):
    c, t, ma_ = _thermo_parts(d)
    return _S(_div(t, ma_), d)


def _tb_tr_pct(d, p):
    o, h, l, c, v = _arr(d)
    return _S(_div(_tr_lib(h, l, c), c) * 100.0, d)


def _tb_ui(d, p):
    """アルサー指数＝n 本最高値からの下落率の2乗を n 本 平均して平方根を取る（下げだけを測る）。"""
    n = p[0]
    o, h, l, c, v = _arr(d)
    hc = _roll(c, n, "max")
    ds = 100.0 * _div(c - hc, hc)
    return _S(np.sqrt(_roll(ds * ds, n, "sum") / n), d)


_r(r"close vs ABER_ZG%", "close vs ABER_ZG%",
   "終値が、アバレーションの中心線（高値・安値・終値の平均の5本単純移動平均）から何%離れているか",
   "標準（ライブラリの既定 length=5・atr_length=15）。値段そのものなので終値との距離%にする"
   "（H6・close vs SMA% と同じ流儀）",
   "順張り値＝プラスで中心線より上", "trend", tb=_tb_aber_zg,
   known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)])])
_r(r"ABER位置", "ABER位置",
   "終値がアバレーションの帯（中心線 ± ATR15）の中のどこにあるか。0 で下の帯・1 で上の帯",
   "標準。帯の幅そのものは 2×ATR15 ＝ うちの ATR% の定数倍なので入れない（重複）。"
   "位置だけを入れる＝BB%b と同じ流儀",
   "順張り値＝大きいほど帯の上側", "trend", tb=_tb_aber_pos)
_r(r"close vs ACCBL%", "close vs ACCBL%",
   "終値が、アクセラレーション・バンドの下の帯から何%離れているか",
   "Price Headley（ライブラリの既定 length=20・c=4）。安値を値幅の割合ぶん広げてから 20本平均する。"
   "値段そのものなので終値との距離%にする（H6）",
   "順張り値＝大きいほど下の帯から離れて上にいる", "trend", tb=_tb_accbl,
   known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)])])
_r(r"close vs ACCBU%", "close vs ACCBU%",
   "終値が、アクセラレーション・バンドの上の帯から何%離れているか", "同上（高値の側）",
   # ★方向の欄に「プラス」と書かない＝検査が「上げ相場でプラス・下げ相場でマイナス」まで要求してしまう。
   #   この列は上の帯との距離なので、上げ相場でもふつうはマイナス（帯の内側）＝2026-08-10 に機械が捕まえた。
   "順張り値＝大きいほど上の帯に近い（0 を超えると帯の外）", "trend", tb=_tb_accbu,
   known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)])])
_r(r"close vs CE_L%", "close vs CE_L%",
   "終値が、シャンデリア・エグジットの買い側の線（22本高値 − 3×ATR22）から何%離れているか",
   "Chuck LeBeau（ライブラリの既定 length=22・multiplier=3）。値段そのものなので終値との距離%にする（H6）",
   "順張り値＝大きいほど直近高値から見た余裕がある", "trend", tb=_tb_ce_l,
   known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)])])
_r(r"close vs CE_S%", "close vs CE_S%",
   "終値が、シャンデリア・エグジットの売り側の線（22本安値 ＋ 3×ATR22）から何%離れているか", "同上",
   "順張り値＝大きいほど売り側の線より上", "trend", tb=_tb_ce_s,
   known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)])])
_r(r"CVI(\d+)", "CVI",
   "チャイキンのボラティリティ＝高安差の n 本 EMA が、n 本前から何%増えたか",
   "Marc Chaikin。もともと%なので、そのままで無次元。★値幅の『大きさ』ではなく『変化』を見る指標なので、"
   "荒い相場でも静かな相場でも、値幅が一定なら 0 になる（下の既知答え）",
   "状態量＝プラスで値幅が広がっている（向きは持たない）", "none", tb=_tb_cvi,
   known=lambda p: [(_bar_fixed_range(p[0] * 6 + 60), [(-1, 0.0, 1e-9)])])
_r(r"HWC位置", "HWC位置",
   "終値がホルト・ウィンターズの水路の中のどこにあるか。0 で下の帯・1 で上の帯",
   "標準。帯は中心線 ± 予測の外れ具合。★上下の帯そのものは入れない＝この位置と下の幅%で表す"
   "（BB%b・BB幅 と同じ流儀）。★中心線が1本先を予測するので、上げ相場ではむしろ小さく出る"
   "（2026-08-10 実測＝合成の上げ 0.366 ／ 下げ 0.607・実データは 0.488 と 0.500 でほぼ差なし）",
   "状態量＝大きいほど水路の上側（向きは持たない）", "none", tb=_tb_hw_pos)
_r(r"HWC幅%", "HWC幅%",
   "ホルト・ウィンターズの水路の幅（上の帯 − 下の帯）を、終値で割って%化",
   "標準。値段の単位なので終値で割る（H6・BB幅 と同じ流儀）", "ボラ量", "vol", tb=_tb_hw_width,
   known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
_r(r"MASSI", "MASSI",
   "マス・インデックス＝高安差の9本 EMA を、それをもう1回9本 EMA した値で割った比を、25本 合計する",
   "Donald Dorsey（ライブラリの既定 fast=9・slow=25）。もともと比の合計なので、そのままで無次元。"
   "★値幅が一定なら 2つの EMA が同じになり、比が 1 ＝合計は 25（下の既知答え）",
   "状態量＝大きいほど値幅が広がった（向きは持たない）", "none", tb=_tb_massi,
   known=lambda p: [(_bar_fixed_range(200), [(-1, 25.0, 1e-9)])])
_r(r"PDIST%", "PDIST%",
   "1本のバーで値段が動いた距離＝高安差の2倍 ＋ |始値 − 前の終値| − |終値 − 始値|。終値で割って%化",
   "ProRealCode（ライブラリの既定 drift=1）。値段の単位なので終値で割る（H6）。"
   "★終値と始値が離れているほど引き算が効くので、値動きの大きさとは一致しない"
   "（2026-08-10 実測＝合成の荒い 0.679 ／ 静か 0.967＝荒い方が小さい）。だからボラ量ではなく状態量にした",
   "状態量＝大きいほど1本の中で往復した距離が長い（向きは持たない）", "none", tb=_tb_pdist,
   known=lambda p: [(_bar_fixed_range(80, half=1.0), [(-1, 4.0, 1e-9)])])
_r(r"RVI(\d+)", "RVI",
   "相対ボラティリティ指数＝上げた足の標準偏差の EMA ÷（上げた足＋下げた足の標準偏差の EMA）を 0〜100 にする",
   "Donald Dorsey。RSI の材料を『値幅の大きさ』に置き換えた形（ライブラリの既定 scalar=100・EMA 平滑）。"
   "★名前が似ている RVGI（相対活力指数）とは別物",
   "順張り値＝大きいほど上げ側の値動きが優勢", "trend", tb=_tb_rvi,
   known=lambda p: [(_up(p[0] * 6 + 40), [(-1, 100.0, 1e-9)])])
_r(r"THERMO%", "THERMO%",
   "エルダーの温度計＝安値の下げ幅と高値の上げ幅の大きい方を、終値で割って%化",
   "Alexander Elder（ライブラリの既定 length=20）。値段の単位なので終値で割る（H6）。★ライブラリの流儀＝安値の下げ幅・高値の上げ幅を絶対値にして大きい方を採る（pandas_ta_classic volatility/thermo.py:41-42 の abs）＝内はらみ足でも正の値。Elder の原作（内はらみ足は 0）は THERMO原作%（監査 CP82）", "ボラ量", "vol",
   tb=_tb_thermo_pct,
   # ★K-4（監査 CP60 の修正59）＝流儀の欄の定義（安値の下げ幅と高値の上げ幅の絶対値の大きい方）から導いた既知答え
   #   ＝内はらみ足（高値 101→100.5・安値 99→99.5）では 0.5 を終値 100 で割って%化＝0.5。教科書の版（THERMO原作%）は 0＝別の値になる。
   known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)]), (_thermo_in_case(80), [(-1, 0.5, 1e-9)])], tb_kind="写し")
_r(r"THERMO比", "THERMO比",
   "エルダーの温度計が、その20本 EMA の何倍か",
   "同上。★ライブラリはこの比に固定の閾値（2 と 0.5）を当てた 0/1 の列も返すが、その2列は入れない"
   "＝閾値は engine_tuner が探すもの（点の一覧で先に限定しない・教訓 L-408）。"
   "★値幅が一定の割合で動き続けると 1 に収束する（下の既知答え）",
   "状態量＝大きいほど、いまの値動きが直近20本の平均より大きい（向きは持たない）", "none",
   tb=_tb_thermo_ratio,
   # ★400本 使う理由＝合成バー `_up` は1本目の始値に最後の終値を入れる作りなので、2本目の温度計だけが
   #   198 になり、その汚れが EMA の種に入る。200本では 1.6e-7 しか減衰せず、許容差 1e-9 に届かない。
   #   400本 で 1.3e-15（2026-08-10 実測）。★許容差はゆるめず、減衰するまで系列を長くした。
   known=lambda p: [(_up(400), [(-1, 1.0, 1e-9)])])
_r(r"TR%", "TR%",
   "真の値幅（高安差・高値と前の終値の差・前の終値と安値の差の最大）を、終値で割って%化",
   "Wilder 1978。★うちの ATR% は これを Wilder 平滑したもの＝こちらは平滑前の1本ぶん", "ボラ量", "vol",
   tb=_tb_tr_pct, known=lambda p: [(_bar_fixed_range(80, half=1.0), [(-1, 2.0, 1e-9)])])
_r(r"UI(\d+)", "UI",
   "アルサー指数＝n 本最高値からの下落率%の2乗を n 本 平均して平方根を取る",
   "Peter Martin（ライブラリの既定 scalar=100）。もともと%なので、そのままで無次元。"
   "★下げだけを測る（上げ続けると 0・下の既知答え）",
   "ボラ量", "vol", tb=_tb_ui,
   known=lambda p: [(_up(p[0] * 4 + 40), [(-1, 0.0, 1e-9)])])


# ══ 業界の指標（cycles 8関数）＝独立実装・登録（2026-08-11・フロー 段6-1 の7回目）══
# ★8関数のうち 1件は関数まるごと入れない（dsp＝うちの close vs EMA% の単調変換・実測）。
# ★ebsw だけ ライブラリの関数を使わない＝ライブラリが角度の単位を取り違えている
#   （教科書 J.F.Ehlers の式は「度」。EasyLanguage の Sine()/Cosine() は度を取る。
#    ライブラリは 360/length などの度の数字を そのままラジアンとして numpy の sin/cos に入れている）。
#   2026-08-11 実測＝係数 alpha1 が 教科書 +0.854081 ／ ライブラリ −0.645222、
#   出てくる系列の相関は +0.5878＝別物になる。VFI と同じ扱いで、教科書の式で書き直した。
# ★ヒルベルト変換の5関数（ht_dcperiod・ht_dcphase・ht_phasor・ht_sine・ht_trendmode）は
#   Ehlers『Rocket Science for Traders』(2001) の擬似コードから独立に書き起こして照合した。
#   ★この照合が捕まえるのは「式の書き写しの間違い」と「既定の引数の違い」であって、
#     式そのものの正しさではない（ライブラリも同じ式を実装しているため）。
#     式そのものは、下の「定義から決まる既知答え」（純粋なサイン波の周期・まっすぐな上げ）で確かめる。
_CYC_SYN_NOTE = ("★合成データの柱（上げ・下げの人工の系列）だけ合わない＝この検査は ⚠️ を出す。理由は実測で突き止めた（2026-08-11）＝合成系列は上げも下げも同じゆらぎ sin(t/3)（周期18.85本）1本しか持たず、傾きの符号がデトレンドの残りを通して位相を半周期ずらす（実測＝位相 上げ 195.25度／下げ 16.83度・差 178.42度＝ほぼ180度）。実データは周期がばらばらなのでこの貼りつきが起きない（実測＝上げた日と下げた日の差が四分位幅の半分以下）。判定は実データの柱が主（この道具の決まり）。")
_HT_START_A = 12                         # ht_dcperiod・ht_phasor の開始位置（TA-Lib の lookback 32）
_HT_START_B = 37                         # ht_dcphase・ht_sine・ht_trendmode の開始位置（同 63）
_EBSW_L, _EBSW_B = 40, 10                # ebsw の既定（拾う波の上限の本数, 低域通過の本数）
_MSW_P = 5                               # msw の既定（DFT に使う本数）


def _bar_cycle(n=2000, period=20, amp=5.0, level=100.0):
    """純粋なサイン波（周期 period 本）の合成バー。サイクル系の既知答え用＝
    『支配的なサイクルの本数』が定義から period に決まる。"""
    c = level + amp * np.sin(2.0 * np.pi * np.arange(n, dtype=float) / period)
    return _mk(c, o=c, h=c, l=c)


def _ht_indep(d, ht_start: int) -> dict:
    """ヒルベルト変換（J.F.Ehlers『Rocket Science for Traders』2001 の擬似コード）を
    独立に書き起こしたもの。返すのは 支配的なサイクルの本数・位相・同相成分・直交成分・
    サイン波・45度先行のサイン波・トレンドかサイクルかの判定。"""
    o, h, l, c, v = _arr(d)
    m = len(c)
    sm = np.zeros(m); dt = np.zeros(m); i1 = np.zeros(m); q1 = np.zeros(m)
    jI = np.zeros(m); jQ = np.zeros(m); i2 = np.zeros(m); q2 = np.zeros(m)
    re = np.zeros(m); im = np.zeros(m); per = np.zeros(m); itr = np.zeros(m)
    sper = np.full(m, np.nan); phase = np.full(m, np.nan)
    ip = np.full(m, np.nan); qu = np.full(m, np.nan)
    sine = np.full(m, np.nan); lead = np.full(m, np.nan)
    tmode = np.full(m, np.nan); tline = np.full(m, np.nan)
    days = 0
    prev_s = prev_l = prev_ph = 0.0
    for i in range(m):
        if i >= ht_start and i >= 3:                       # 4本の加重平均で均す
            sm[i] = (4.0 * c[i] + 3.0 * c[i - 1] + 2.0 * c[i - 2] + c[i - 3]) / 10.0
        if i < ht_start:
            per[i] = 0.0
            sper[i] = 0.0
            continue
        adj = 0.075 * per[i - 1] + 0.54                    # 1本前の周期で係数を調整する
        dt[i] = (0.0962 * sm[i] + 0.5769 * sm[i - 2] - 0.5769 * sm[i - 4] - 0.0962 * sm[i - 6]) * adj
        q1[i] = (0.0962 * dt[i] + 0.5769 * dt[i - 2] - 0.5769 * dt[i - 4] - 0.0962 * dt[i - 6]) * adj
        i1[i] = dt[i - 3]
        jI[i] = (0.0962 * i1[i] + 0.5769 * i1[i - 2] - 0.5769 * i1[i - 4] - 0.0962 * i1[i - 6]) * adj
        jQ[i] = (0.0962 * q1[i] + 0.5769 * q1[i - 2] - 0.5769 * q1[i - 4] - 0.0962 * q1[i - 6]) * adj
        i2[i] = i1[i] - jQ[i]
        q2[i] = q1[i] + jI[i]
        i2[i] = 0.2 * i2[i] + 0.8 * i2[i - 1]
        q2[i] = 0.2 * q2[i] + 0.8 * q2[i - 1]
        re[i] = i2[i] * i2[i - 1] + q2[i] * q2[i - 1]      # ホモダイン検波
        im[i] = i2[i] * q2[i - 1] - q2[i] * i2[i - 1]
        re[i] = 0.2 * re[i] + 0.8 * re[i - 1]
        im[i] = 0.2 * im[i] + 0.8 * im[i - 1]
        per[i] = 360.0 / np.degrees(np.arctan(im[i] / re[i])) if (im[i] and re[i]) else per[i - 1]
        if per[i] > 1.5 * per[i - 1]:
            per[i] = 1.5 * per[i - 1]
        if per[i] < 0.67 * per[i - 1]:
            per[i] = 0.67 * per[i - 1]
        per[i] = max(6.0, min(50.0, per[i]))
        per[i] = 0.2 * per[i] + 0.8 * per[i - 1]
        sper[i] = 0.33 * per[i] + 0.67 * sper[i - 1]
        sp = sper[i]
        dcp = max(int(sp + 0.5), 1)                        # 教科書＝小数を四捨五入して本数にする
        rp = ipart = 0.0
        for j in range(dcp):
            if i - j >= 0:
                ang = 2.0 * np.pi * j / dcp
                rp += np.sin(ang) * sm[i - j]
                ipart += np.cos(ang) * sm[i - j]
        if abs(ipart) > 0.0:
            ph = np.degrees(np.arctan(rp / ipart))
        else:
            ph = prev_ph + (-90.0 if rp < 0 else (90.0 if rp > 0 else 0.0))
        ph += 90.0
        if sp > 0:
            ph += 360.0 / sp
        if ipart < 0:
            ph += 180.0
        if ph > 315.0:
            ph -= 360.0
        phase[i] = ph
        ip[i] = i1[i]
        qu[i] = q1[i]
        sine[i] = np.sin(np.radians(ph))
        lead[i] = np.sin(np.radians(ph + 45.0))
        itr[i] = c[max(i - dcp + 1, 0):i + 1].mean()       # 支配的なサイクルの本数で均した線
        tline[i] = (4.0 * itr[i] + 3.0 * itr[i - 1]
                    + 2.0 * (itr[i - 2] if i >= 2 else itr[0])
                    + (itr[i - 3] if i >= 3 else itr[0])) / 10.0
        tr = 1                                             # まずトレンドと仮定する（教科書の4段）
        if (sine[i] > lead[i] and prev_s <= prev_l) or (sine[i] < lead[i] and prev_s >= prev_l):
            days, tr = 0, 0                                # 段1 サイン波が交差したら数え直す
        days += 1
        if days < 0.5 * sp:
            tr = 0                                         # 段2 交差から半周期たっていない
        dph = ph - prev_ph
        if sp != 0 and 0.67 * 360.0 / sp < dph < 1.5 * 360.0 / sp:
            tr = 0                                         # 段3 位相の進みがサイクルらしい
        if tline[i] != 0 and abs((sm[i] - tline[i]) / tline[i]) >= 0.015:
            tr = 1                                         # 段4 値段が線から1.5%以上 離れた
        tmode[i] = float(tr)
        prev_s, prev_l, prev_ph = sine[i], lead[i], ph
    return dict(sper=sper, phase=phase, ip=ip, qu=qu, sine=sine, lead=lead, tmode=tmode)


def _tb_ht_dcperiod(d, p):
    return _S(_ht_indep(d, _HT_START_A)["sper"], d)


def _tb_ht_dcphase(d, p):
    return _S(_ht_indep(d, _HT_START_B)["phase"], d)


def _tb_ht_inphase(d, p):
    o, h, l, c, v = _arr(d)
    return _S(_div(_ht_indep(d, _HT_START_A)["ip"], c) * 100.0, d)


def _tb_ht_quad(d, p):
    o, h, l, c, v = _arr(d)
    return _S(_div(_ht_indep(d, _HT_START_A)["qu"], c) * 100.0, d)


def _tb_ht_sine(d, p):
    return _S(_ht_indep(d, _HT_START_B)["sine"], d)


def _tb_ht_leadsine(d, p):
    return _S(_ht_indep(d, _HT_START_B)["lead"], d)


def _tb_ht_trendmode(d, p):
    tm = _ht_indep(d, _HT_START_B)["tmode"].copy()
    tm[:63] = np.nan                       # ★TA-Lib の助走 63 本に合わせる（それ以前は 0 で出す）
    return _S(np.where(np.isnan(tm), 0.0, tm), d)


def _tb_ebsw(d, p):
    """Even Better SineWave（J.F.Ehlers, Cycle Analytics for Traders 2014）。
    ①length 本より長い波をハイパスで落とす ②bars 本より短い波を2極のスーパースムーザーで落とす
    ③3本の平均を3本の実効値で割って −1〜1 にする。★角度は度（教科書どおり）。"""
    o, h, l, c, v = _arr(d)
    m = len(c)
    out = np.full(m, np.nan)
    if m <= _EBSW_L:
        return _S(out, d)
    out[_EBSW_L - 1] = 0.0
    a_hp = (1.0 - np.sin(np.radians(360.0 / _EBSW_L))) / np.cos(np.radians(360.0 / _EBSW_L))
    a1 = np.exp(-np.sqrt(2.0) * np.pi / _EBSW_B)
    k2 = 2.0 * a1 * np.cos(np.radians(np.sqrt(2.0) * 180.0 / _EBSW_B))
    k3 = -a1 * a1
    k1 = 1.0 - k2 - k3
    last_c = last_hp = 0.0
    f2 = f1 = 0.0                          # 2本前・1本前のフィルタ出力
    for i in range(_EBSW_L, m):
        hp = 0.5 * (1.0 + a_hp) * (c[i] - last_c) + a_hp * last_hp
        filt = k1 * (hp + last_hp) / 2.0 + k2 * f1 + k3 * f2
        wave = (filt + f1 + f2) / 3.0
        pwr = (filt * filt + f1 * f1 + f2 * f2) / 3.0
        out[i] = wave / np.sqrt(pwr) if pwr > 0 else 0.0
        f2, f1 = f1, filt
        last_hp, last_c = hp, c[i]
    return _S(out, d)


def _msw_indep(d):
    """メサ・サイン波（J.F.Ehlers『Rocket Science for Traders』2001）。
    直近 period 本に離散フーリエ変換を1本だけ当てて位相を出し、そのサインと45度先行のサインを返す。"""
    o, h, l, c, v = _arr(d)
    m, n = len(c), _MSW_P
    sine = np.full(m, np.nan)
    lead = np.full(m, np.nan)
    ang = 2.0 * np.pi * np.arange(n, dtype=float) / n
    cs, sn = np.cos(ang), np.sin(ang)
    for i in range(n, m):
        w = c[i - n + 1:i + 1][::-1]       # 新しい足が j=0
        rp = float(np.dot(w, cs))
        ipt = float(np.dot(w, sn))
        ph = np.arctan(ipt / rp) if abs(rp) > 0.001 else np.pi * (-1.0 if ipt < 0 else 1.0)
        if rp < 0.0:
            ph += np.pi
        ph += np.pi / 2.0
        if ph < 0.0:
            ph += 2.0 * np.pi
        if ph > 2.0 * np.pi:
            ph -= 2.0 * np.pi
        sine[i] = np.sin(ph)
        lead[i] = np.sin(ph + np.pi / 4.0)
    return sine, lead


def _tb_msw_sine(d, p):
    return _S(_msw_indep(d)[0], d)


def _tb_msw_lead(d, p):
    return _S(_msw_indep(d)[1], d)


_r(r"EBSW", "EBSW",
   "かなり良いサイン波＝40本より長い波と10本より短い波を落として、3本の平均を3本の実効値で割った −1〜1 の値",
   "J.F.Ehlers（Cycle Analytics for Traders 2014・既定 length=40・bars=10）。"
   "★ライブラリの関数は使っていない＝ライブラリが角度の単位を取り違えている（教科書は度・"
   "ライブラリは度の数字をそのままラジアンとして sin/cos に入れている）。2026-08-11 実測＝"
   "係数 alpha1 が 教科書 +0.854081 ／ ライブラリ −0.645222 で、系列の相関は +0.5878＝別物。"
   "★まっすぐな上げ／下げでは、ハイパス通過後が一定になるので ちょうど +1／−1 になる（下の既知答え）",
   "順張り値＝プラスで上げ", "trend", tb=_tb_ebsw,
   known=lambda p: [(_up(1200, step=0.5), [(-1, 1.0, 1e-9)]),
                    (_dn(1200, start=700.0, step=0.5), [(-1, -1.0, 1e-9)])])
_r(r"HT_DCPERIOD", "HT_DCPERIOD",
   "ヒルベルト変換で測った、いま支配的なサイクルの本数（6〜50 に収める）",
   "J.F.Ehlers（Rocket Science for Traders 2001）。ホモダイン検波で1本ごとに周期を測り、"
   "1.5倍・0.67倍の変化幅と 6〜50 の範囲で抑えてから平滑する。もともと「本数」なので無次元。"
   "★純粋なサイン波を入れると、その周期の本数がそのまま出る（下の既知答え）",
   "状態量＝大きいほど長い波が支配している（向きは持たない）", "none", tb=_tb_ht_dcperiod,
   known=lambda p: [(_bar_cycle(2000, 20), [(-1, 20.0, 0.05)]),
                    (_bar_cycle(2000, 30), [(-1, 30.0, 0.05)])])
_r(r"HT_DCPHASE", "HT_DCPHASE",
   "ヒルベルト変換で測った、支配的なサイクルの中のいまの位相（度・−45〜315）",
   "同上（開始位置 37＝TA-Lib の助走 63 に合わせる）。もともと「度」なので無次元。"
   "★円環の量＝315 を超えると −360 して戻るので、大小に一直線の意味は無い。"
   "★下の HT_SINE・HT_LEADSINE は この位相のサインそのもの（sin(位相) と sin(位相+45度)）。"
   "サインは −45〜315 度の範囲で一直線でないので、『値 ≥ 閾値』の条件としては別のものになる。" + _CYC_SYN_NOTE,
   "状態量＝サイクルの中の居場所（向きは持たない）", "none", tb=_tb_ht_dcphase)
_r(r"HT_INPHASE%", "HT_INPHASE%",
   "ヒルベルト変換の同相成分（デトレンドした値段の3本前）を、終値で割って%化",
   "同上（開始位置 12）。値段の単位なので終値で割る（H6）", "順張り値＝プラスで上げ", "trend",
   tb=_tb_ht_inphase)
_r(r"HT_QUAD%", "HT_QUAD%",
   "ヒルベルト変換の直交成分（同相成分から90度ずらした側）を、終値で割って%化",
   "同上（開始位置 12）。値段の単位なので終値で割る（H6）。"
   "★作りからして同相成分より4分の1周期 先を行くので、上げ下げと一定の向きを持たない。" + _CYC_SYN_NOTE,
   "状態量＝サイクルの90度ずれた側（向きは持たない）", "none", tb=_tb_ht_quad)
_r(r"HT_SINE", "HT_SINE",
   "支配的なサイクルの位相のサイン（sin(位相)・−1〜1）",
   "同上（開始位置 37）。★使い方は下の HT_LEADSINE との交差＝この2本が交差した所がサイクルの折り返し。"
   "値そのものの大小は上げ下げの向きを表さない。" + _CYC_SYN_NOTE,
   "状態量＝サイクルの中の居場所（向きは持たない）", "none", tb=_tb_ht_sine)
_r(r"HT_LEADSINE", "HT_LEADSINE",
   "支配的なサイクルの位相を45度 先に進めたサイン（sin(位相+45度)・−1〜1）",
   "同上。★HT_SINE との交差を見るための相方。" + _CYC_SYN_NOTE, "状態量＝同上（向きは持たない）", "none",
   tb=_tb_ht_leadsine)
_r(r"HT_TRENDMODE", "HT_TRENDMODE",
   "いまがトレンドか（1）サイクルか（0）の判定",
   "同上（開始位置 37・助走 63 本は 0）。教科書の4段＝①サイン波の交差で数え直す ②交差から半周期"
   "たっていなければサイクル ③位相の進みがサイクルらしければサイクル ④値段が均した線から"
   "1.5%以上 離れていればトレンド。★まっすぐな上げでは 1 になる（下の既知答え）",
   "状態量＝1 でトレンド・0 でサイクル（向きは持たない）", "none", tb=_tb_ht_trendmode,
   known=lambda p: [(_up(800, step=0.5), [(-1, 1.0, 1e-9)])])
_r(r"MSW_SINE", "MSW_SINE",
   "メサ・サイン波＝直近5本に離散フーリエ変換を当てて出した位相のサイン（−1〜1）",
   "J.F.Ehlers（Rocket Science for Traders 2001・ライブラリの既定 period=5）。"
   "★ヒルベルト変換の HT_SINE とは位相の求め方が違う（こちらは決まった本数のフーリエ変換・"
   "あちらは1本ごとに周期を測る）。2026-08-11 実測＝2つの相関は 0.99 に届かない＝別のもの。"
   "★純粋なサイン波（周期5）で、最後の位置を5で割った余りが1のとき、"
   "定義から 位相 = 72度 に決まる（下の既知答え）",
   "順張り値＝プラスで上げ", "trend", tb=_tb_msw_sine,
   known=lambda p: [(_bar_cycle(1002, 5), [(-1, 0.9510565162951535, 1e-9)])])
_r(r"MSW_LEAD", "MSW_LEAD",
   "メサ・サイン波の45度先行（sin(位相+45度)・−1〜1）",
   "同上。★MSW_SINE との交差を見るための相方。45度ずれているので、上げ下げと一定の向きを持たない。"
   "★上と同じ合成バーで 位相+45度 = 117度 に決まる（下の既知答え）。" + _CYC_SYN_NOTE,
   "状態量＝サイクルの中の居場所（向きは持たない）", "none", tb=_tb_msw_lead,
   known=lambda p: [(_bar_cycle(1002, 5), [(-1, 0.8910065241883679, 1e-9)])])


# ══ 業界の指標（candles 4関数）＝独立実装・登録（2026-08-11・フロー 段6-h）══
# ★4関数のうち「関数の返す列の一部だけ入れない」ものが3件（理由は下の対応表 INDUSTRY_MAP に1件ずつ）＝
#   cdl_doji の 0/1（固定の閾値を当てただけ＝中身の連続値だけ入れる）／
#   cdl_z の終値の z 値（うちの zscore の本数違い・実測 スピアマン相関 1.0000000）／
#   ha の4本値そのもの（値段＝H6）。
_CDLZ_N = 30                             # cdl_z の既定（本数・標本標準偏差 ddof=1）
_DOJI_N = 10                             # cdl_doji の既定（直前 n 本の平均値幅）


def _bar_nowick(n=200, start=100.0, step=0.5, up=True):
    """ヒゲの無いまっすぐな上げ／下げ。平均足（HA）の既知答え用＝
    実体%・上ヒゲ比・下ヒゲ比 が定義から決まる（下の登録に導出を書いた）。"""
    c = start + (step if up else -step) * np.arange(n, dtype=float)
    o = c - step if up else c + step
    return _mk(c, o=o, h=np.maximum(o, c), l=np.minimum(o, c))


def _bar_inside(n=40, level=100.0):
    """最後のバーだけが、その1本前のバーの高安の内側に完全に入る陽線（内側バーの既知答え用）。"""
    c = np.full(n, level)
    o = np.full(n, level)
    h = np.full(n, level + 2.0)
    l = np.full(n, level - 2.0)
    o[-1], c[-1] = level - 0.5, level + 0.5      # 陽線（終値 > 始値）
    h[-1], l[-1] = level + 1.0, level - 1.0      # 1本前の高安（±2.0）の内側
    return _mk(c, o=o, h=h, l=l)


def _bar_fixed_body(n=40, level=100.0, body=1.0):
    """実体と値幅が同じ（＝実体幅比 = 1）バー。実体幅比の既知答え用。"""
    o = np.full(n, level)
    c = np.full(n, level + body)
    return _mk(c, o=o, h=np.maximum(o, c), l=np.minimum(o, c))


def _tb_body_range(d, p):
    """実体 ÷ 直前 n 本の平均値幅（cdl_doji の中身の連続値）。"""
    n = p[0]
    o, h, l, c, v = _arr(d)
    avg = np.r_[np.nan, _roll(h - l, n, "mean")[:-1]]     # 1本前まで（未来を見ない）
    return _S(_div(np.abs(c - o), avg), d)


def _tb_inside(d, p):
    """内側バー＝高値が前より低く、安値が前より高い。陽線なら +1・陰線なら −1。"""
    o, h, l, c, v = _arr(d)
    ph = np.r_[np.nan, h[:-1]]
    pl = np.r_[np.nan, l[:-1]]
    hit = ((h - ph) < 0) & ((l - pl) > 0)
    return _S(np.where(hit, np.where(c >= o, 1.0, -1.0), 0.0), d)


def _tb_cdlz(d, p, which: str):
    """4本値それぞれの z スコア（n 本の平均を引いて標本標準偏差で割る・ddof=1）。"""
    n = p[0]
    x = {"open": d.open, "high": d.high, "low": d.low}[which].to_numpy(float)
    return _S(_div(x - _roll(x, n, "mean"), _roll(x, n, "std", ddof=1)), d)


def _ha_indep(d):
    """平均足（Heikin-Ashi）。終値＝4本値の平均／始値＝1本前の平均足の始値と終値の平均。
    高値・安値は 平均足の始値・終値と 実際の高値・安値 を合わせた最大・最小。"""
    o, h, l, c, v = _arr(d)
    m = len(c)
    hc = (o + h + l + c) / 4.0
    ho = np.full(m, np.nan)
    if m:
        ho[0] = 0.5 * (o[0] + c[0])
        for i in range(1, m):
            ho[i] = 0.5 * (ho[i - 1] + hc[i - 1])
    hh = np.maximum.reduce([ho, h, hc])
    hl = np.minimum.reduce([ho, l, hc])
    return ho, hh, hl, hc


def _tb_ha_body(d, p):
    o, h, l, c, v = _arr(d)
    ho, hh, hl, hc = _ha_indep(d)
    return _S(_div(hc - ho, c) * 100.0, d)


def _tb_ha_uwick(d, p):
    ho, hh, hl, hc = _ha_indep(d)
    return _S(_div(hh - np.maximum(ho, hc), hh - hl), d)


def _tb_ha_lwick(d, p):
    ho, hh, hl, hc = _ha_indep(d)
    return _S(_div(np.minimum(ho, hc) - hl, hh - hl), d)


_r(r"実体幅比(\d+)", "実体幅比",
   "そのバーの実体（|終値 − 始値|）が、直前 n 本の平均値幅の何倍か",
   "cdl_doji（十字線）の中身の連続値。★ライブラリはこれに固定の閾値（平均値幅の10%）を当てた 0/1 を返すが、"
   "その 0/1 は入れない＝閾値は engine_tuner が探すもの（教訓 L-408・THERMO の 0/1 と同じ扱い）。"
   "★うちの body比（実体 ÷ そのバーの値幅）とは別もの＝あちらは同じバーの中の比、これは直近の平均との比。"
   "★平均は1本前まで（当該バーを入れない＝ライブラリと同じ流儀・未来を見ない）",
   "状態量＝大きいほど迷いのないバー（向きは持たない）", "none", tb=_tb_body_range,
   known=lambda p: [(_bar_fixed_body(p[0] * 4 + 20), [(-1, 1.0, 1e-9)])])
_r(r"内側バー", "内側バー",
   "高値が1本前より低く、安値が1本前より高いバー（内側バー）。陽線なら +1・陰線なら −1・当てはまらなければ 0",
   "cdl_inside（ライブラリの既定＝当てはまった所にローソクの色 ±1 を掛ける）。"
   "★うちの 孕み足 とは別もの＝孕み足は『実体』が前のバーの実体の内側、内側バーは『高安』が前のバーの内側",
   "反転サイン＝+1 は陽線の内側バー（もみ合いからの上放れの前触れ）", "reversal", tb=_tb_inside,
   known=lambda p: [(_bar_inside(), [(-1, 1.0, 1e-9)])])
_r(r"open_Z(\d+)", "open_Z",
   "始値が、直前 n 本の始値の平均から標準偏差いくつぶん離れているか",
   "cdl_z（ライブラリの既定 length=30・標本標準偏差 ddof=1）。もともと無次元。"
   "★終値の z 値は入れない＝うちの zscore の本数違い（2026-08-11 実測＝本数30 のうちの式と"
   "スピアマン相関 1.0000000）。本数30 が うちの一覧に無いことは materials.md ★3 の"
   "『zscore … 20 本・50 本』で見える＝本数の側で埋める穴。"
   "始値・高値・安値の z 値は うちに1つも無いので入れる。"
   "★まっすぐな上げでは (n−1)/2 ÷ √(n(n+1)/12) に決まる（下の既知答え）",
   "順張り値＝プラスで直近の平均より上", "trend", tb=lambda d, p: _tb_cdlz(d, p, "open"),
   known=lambda p: [(_up(200, step=1.0),
                     [(-1, ((p[0] - 1) / 2) / np.sqrt(p[0] * (p[0] + 1) / 12.0), 1e-9)])])
_r(r"high_Z(\d+)", "high_Z",
   "高値が、直前 n 本の高値の平均から標準偏差いくつぶん離れているか", "同上（高値の側）",
   "順張り値＝プラスで直近の平均より上", "trend", tb=lambda d, p: _tb_cdlz(d, p, "high"),
   known=lambda p: [(_up(200, step=1.0),
                     [(-1, ((p[0] - 1) / 2) / np.sqrt(p[0] * (p[0] + 1) / 12.0), 1e-9)])])
_r(r"low_Z(\d+)", "low_Z",
   "安値が、直前 n 本の安値の平均から標準偏差いくつぶん離れているか", "同上（安値の側）",
   "順張り値＝プラスで直近の平均より上", "trend", tb=lambda d, p: _tb_cdlz(d, p, "low"),
   known=lambda p: [(_up(200, step=1.0),
                     [(-1, ((p[0] - 1) / 2) / np.sqrt(p[0] * (p[0] + 1) / 12.0), 1e-9)])])
_r(r"HA実体%", "HA実体%",
   "平均足の実体（平均足の終値 − 平均足の始値）を、終値で割って%化",
   "ha（平均足）。平均足の終値＝4本値の平均／始値＝1本前の平均足の始値と終値の平均。"
   "値段の単位なので終値で割る（H6）。★4本値そのものは入れない＝値段（H6）。"
   "★ヒゲの無いまっすぐな上げ（1本 step ぶん）では、平均足の実体が ちょうど 2×step に収まる"
   "（実測＝step 0.5・終値 199.5 で 0.5012531…％＝1.0 ÷ 199.5 × 100）",
   "順張り値＝プラスで平均足が陽線", "trend", tb=_tb_ha_body,
   known=lambda p: [(_bar_nowick(200, step=0.5), [(-1, 100.0 / 199.5, 1e-9)]),
                    (_bar_nowick(200, start=200.0, step=0.5, up=False), [(-1, -100.0 / 100.5, 1e-9)])])
_r(r"HA上ヒゲ比", "HA上ヒゲ比",
   "平均足の上ヒゲが、平均足の全幅の何割か",
   "同上。★ヒゲの無いまっすぐな下げでは、平均足の始値が上限になるので ちょうど 0 になる（下の既知答え）",
   "反転サイン＝大きいほど上値の売り圧の示唆", "reversal", tb=_tb_ha_uwick,
   known=lambda p: [(_bar_nowick(200, start=200.0, step=0.5, up=False), [(-1, 0.0, 1e-9)]),
                    (_bar_nowick(200, step=0.5), [(-1, 0.2, 1e-9)])])
_r(r"HA下ヒゲ比", "HA下ヒゲ比",
   "平均足の下ヒゲが、平均足の全幅の何割か",
   "同上。★ヒゲの無いまっすぐな上げでは、平均足の始値が下限になるので ちょうど 0 になる"
   "＝『上げが強いと平均足に下ヒゲが出ない』という平均足の使い方そのもの（下の既知答え）",
   "反転サイン＝大きいほど下値の買い支えの示唆", "reversal", tb=_tb_ha_lwick,
   known=lambda p: [(_bar_nowick(200, step=0.5), [(-1, 0.0, 1e-9)]),
                    (_bar_nowick(200, start=200.0, step=0.5, up=False), [(-1, 0.2, 1e-9)])])


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
    dict(cat="形(W窓)", token="swing_dist", impl=[r"close vs \d+本高値%", r"close vs \d+本安値%"],
         status="あり",
         note="★2026-08-11 に指す列を変えた。前は swing高値距離%・swing安値距離% を指していたが、"
              "検査12（重複の総当たり）で close vs n本高値%・close vs n本安値% と『実質 同じもの』"
              "（値の相関も順位の相関も 1.0000000）と出たので、まこさん OK 2026-08-11（逐語"
              "「同じ挙動ならどちらかは使わないようにしていいよ」）で swing 側を省いた。中身は同じ"),
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
# ★2026-10-20（工事 m2c15-band-s1-20261020・F-4）＝監査 CP60 の修正69 の直した後の文字に、正時の区切りの切り替え（h1_edge）を足した。
RANGE_GEO_TF = ("5m（1h ゾーンは label=right・closed=right で5分足の始まりの時刻を束ねる＝1時間足の区切りは正時から5分ずれる"
                "（例 10:05〜11:05）。5分足の行 T（11:00）へ ffill＝その行が閉じた時に確定済み。h1_edge=hour で正時の区切り（10:00〜11:00）に"
                "切り替えられる＝その区切りの最後の5分足（10:55）の行から使う。既定は今の区切り・状態機械は過去 close の逐次更新）")
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
    # ★2026-10-09（工事 m2c15-shape-structure-20261009・監査 CP60 の修正65 の直した後の文字＋まこさんの決定の欄）
    "下半分位置": dict(kind="ratio", teigi="下半分の帯内位置＝(close − mid) / (mid − sup_lo)。mid=0・sup_lo=−1",
                   ryugi="帯内位置% の下半分の対（%b と同じく、その半分の幅で割る・監査 CP60）。分母≤0 は欠損",
                   houkou="順張り値＝−1 に近いほど下端（押し目買いの場所）", mako=MAKO_K3B),
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
    """既知答え＝合成バーの最終行で、帯の4隅・mid・W%・帯内位置%・下半分位置 が電卓式と一致するか。
    電卓式: res 帯＝110×(1∓tol/2)・sup 帯＝90×(1∓tol/2)・mid=(res_lo+sup_hi)/2・
    W%=(res_hi−sup_lo)/100×100・帯内位置%=(100−mid)/(res_hi−mid)・下半分位置=(100−mid)/(mid−sup_lo)。geo_fn は観察側の実装
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
    exp["下半分位置"] = (100.0 - exp["mid"]) / (exp["mid"] - exp["sup_lo"])     # 2026-10-09（K-3b・監査 CP60 の修正65）
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


# ══ ta のクラスとの対応（M2-C-2・まこさん承認 2026-09-02「書き込んでよい」）════════════════
# 何のためか＝まこさん決定 2026-08-27（逐語「本来の目的が達成できるまでは、指標一覧はta 43種にする」）を
#   機械で実行するには、ta のクラス名（BollingerBands）と、うちの材料の名前（BB）を突き合わせる必要がある。
#   文字が違うので自動では突き合わない。だからここに対応を持つ。
#
# ★CC が指標を選んでいるのではない。作り方の順序は次の3段:
#   ① gen_indicator_switch.py --ta-candidates が、機械の規則（クラス名の略号の前方一致）で候補を出す
#   ② まこさんが1回 見て承認する（2026-09-02）
#   ③ 承認されたものだけをここに書く
#
# ★ここに書かないもの＝ta を呼ぶ照合式（ext=）が定義表に在る19クラス。
#   そちらは gen_indicator_switch.py が関数のソースから機械で引くので、二重に持たない。
#
# ★除いたもの（1件）＝PercentageVolumeOscillator の候補に出た「PVOL比」。
#   機械は略号 PVO の前方一致で拾ったが、実物の定義が別物だった（2026-09-02 に定義表で確認）＝
#   PVO は出来高の短期 EMA と長期 EMA の差／PVOL比 は 売買代金が n 本平均の何倍か。
#
# 形＝{ta のクラス名: (材料の種類, ...)}。材料の種類が定義表に実在するかは
#   gen_indicator_switch.py --selftest が毎回 確かめる（打ち間違いは そこで止まる）。
TA_CLASS_MAP: dict[str, tuple[str, ...]] = {
    # ── 略号の一致で候補が出た15クラス（まこさん承認 2026-09-02）──
    "AroonIndicator": ("AROONU", "AROOND", "AROONOSC"),
    # ★2026-10-11（工事 m2c15-formula-textbook-20261011・全体の表 G-1・監査 CP60 の修正37 の補足）＝ta の DPOIndicator（k本前の終値 − SMA）を
    #   教科書の版に対応させる。今の DPO% は比べるために残す（M2-F-10f）。
    "DPOIndicator": ("DPO教科書%", "DPO%"),
    "KAMAIndicator": ("KAMA傾き%", "close vs KAMA%"),
    "KSTIndicator": ("KST", "KSTシグナル"),
    "KeltnerChannel": ("Keltner上", "Keltner下"),
    "MassIndex": ("MASSI",),
    "PSARIndicator": ("PSAR加速", "PSAR反転", "close vs PSAR%"),
    "PercentagePriceOscillator": ("PPO", "PPOシグナル", "PPOヒスト"),
    "PercentageVolumeOscillator": ("PVO", "PVOシグナル", "PVOヒスト"),
    "STCIndicator": ("STC", "STCstoch"),
    "StochRSIIndicator": ("StochRSI%K", "StochRSI%D"),
    "TRIXIndicator": ("TRIX", "TRIXシグナル", "TRIXヒスト"),
    "TSIIndicator": ("TSI", "TSIシグナル", "TSIヒスト"),
    "VolumeWeightedAveragePrice": ("close vs VWAP",),
    "WMAIndicator": ("WMA傾き%", "close vs WMA%"),
    # ── 略号では当たらないが材料に相当が在る4クラス（まこさん承認 2026-09-02）──
    "VortexIndicator": ("VTXP", "VTXM"),                 # 名前が Vortex と VTX で違う
    "UlcerIndex": ("UI",),                               # 略号が2文字＝機械の照合から外してある
    "NegativeVolumeIndexIndicator": ("NVI傾き",),         # 名前が長く略号を作れない
    # ★OBV傾き＝ta に相当は在るが、値の照合はしない（定義表 954行の逐語＝
    #   「外部ライブラリ ta は同値を上昇扱いする変種のため外部照合の対象外」）。
    #   ＝照合式が無いのは登録漏れではなく、意図した状態。だから ta 由来の対応はここで持つ。
    "OnBalanceVolumeIndicator": ("OBV傾き",),
}


# ══ 系統マップ（G3 同系統制限の正本・CP3 Q4・全 family を単一割当＝載っていない family は生成不可）══
# 8系統＝トレンド／オシレーター／ボラ／出来高／ローソク／構造・位置／需給／時間帯（設計書 G3）。
# 両属性の family は主用途で単一割当し、理由を note に書く（例＝MFI はオシレーター・CP3 の例示どおり）。
FAMILY_LINEAGE: dict[str, dict] = {
    # トレンド
    "ADX": dict(k="トレンド", note="向きを持たないがトレンドの強さの計測が主用途（Wilder）"),
    "DI差": dict(k="トレンド"), "MACD線%": dict(k="トレンド"), "MACDヒスト%": dict(k="トレンド"),
    "MACDシグナル線%": dict(k="トレンド"), "EMA傾き": dict(k="トレンド"),
    # ★RSI傾き は 2026-08-11 に足して同じ日に省いた（列で持たず form=slope で作る）。経緯は
    #   observe_diag の build_catalog の RSI の所と、worklog 20260811 §44。
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
    "SQZ%": dict(k="ボラ", note="帯の縮み具合から作る値を終値で割って%化（H6・2026-08-11）"),
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
    # ★2026-09-05（M2-C-4）＝MMI は CHOP・ER と同じ「もみ合いの度合い」を測る（向きを持たない）
    "MMI": dict(k="ボラ", note="値動きがランダムに近いかの割合（向きを持たない）＝CHOP・ER と同じ物差し"),
    "close vs CKSPl%": dict(k="構造・位置"), "close vs CKSPs%": dict(k="構造・位置"),
    "DPO%": dict(k="オシレーター"),
    "close vs PMAX%": dict(k="構造・位置"), "close vs PSAR%": dict(k="構造・位置"),
    "PSAR加速": dict(k="トレンド"), "PSAR反転": dict(k="構造・位置"),
    "QSTICK%": dict(k="ローソク", note="終値と始値の差の平均＝バスの中の押し切り方"),
    "close vs SAREXT%": dict(k="構造・位置"),
    "TTM_TREND": dict(k="トレンド"), "VHF": dict(k="ボラ"), "VTXP": dict(k="トレンド"), "VTXM": dict(k="トレンド"),
    # 業界の指標（pandas-ta 由来・フロー 段6-1 の4回目＝volume）＝全部 出来高の系統
    "ADOSC比": dict(k="出来高"), "AOBV_LR": dict(k="出来高"),
    "EFI比": dict(k="出来高"), "EOM比": dict(k="出来高"),
    "MARKETFI比": dict(k="出来高", note="値幅÷出来高。ボラ系でもあるが出来高で割るのが主用途"),
    "NVI傾き": dict(k="出来高"), "PVI傾き": dict(k="出来高"), "PVOL比": dict(k="出来高"),
    "PVT傾き": dict(k="出来高"), "WAD傾き": dict(k="出来高"),
    "KVO比": dict(k="出来高"), "KVOシグナル比": dict(k="出来高"), "VOSC": dict(k="出来高"),
    "VFI": dict(k="出来高"), "出来高変化率%": dict(k="出来高"),
    # 業界の指標（pandas-ta 由来・フロー 段6-1 の5回目＝statistics）
    "skew": dict(k="ボラ", note="窓の中の値段の分布の形＝値動きの大きさの計測に属する"),
    "kurtosis": dict(k="ボラ", note="同上（裾の厚み）"),
    "MAD比": dict(k="ボラ"), "stdev%": dict(k="ボラ"),
    # 業界の指標（pandas-ta 由来・フロー 段6-1 の6回目＝volatility）
    "close vs ABER_ZG%": dict(k="構造・位置", note="中心線との距離＝位置の計測（close vs SMA% と同じ作り）"),
    "ABER位置": dict(k="構造・位置", note="帯の中の位置＝BB%b と同じ作り。★ただし BB%b は行き過ぎの計測が"
                                          "主用途でオシレーターに置いてある。こちらは中心線が値段の平均でなく"
                                          "HLC3 の平均で、帯の幅が ATR＝位置の計測が主用途"),
    "close vs ACCBL%": dict(k="構造・位置", note="帯との距離＝位置の計測（Keltner 上下と同じ作り）"),
    "close vs ACCBU%": dict(k="構造・位置", note="同上"),
    "close vs CE_L%": dict(k="構造・位置", note="直近高値から ATR ぶん下げた線との距離＝位置の計測"),
    "close vs CE_S%": dict(k="構造・位置", note="同上（直近安値の側）"),
    "HWC位置": dict(k="構造・位置", note="水路の中の位置＝位置の計測"),
    "HWC幅%": dict(k="ボラ", note="水路の幅＝値動きの大きさの計測（BB幅 と同じ作り）"),
    "CVI": dict(k="ボラ", note="高安差の平均が何%増えたか＝値動きの大きさの変化"),
    "MASSI": dict(k="ボラ", note="高安差の広がりの計測"),
    "PDIST%": dict(k="ボラ", note="1本の中で値段が動いた距離"),
    "RVI": dict(k="ボラ", note="上げ側と下げ側それぞれの値動きの大きさの比。★0〜100 の有界だが、"
                               "材料が値幅（標準偏差）なのでオシレーターでなくボラに置く"),
    "THERMO%": dict(k="ボラ"), "THERMO比": dict(k="ボラ"),
    "TR%": dict(k="ボラ", note="1本ぶんの真の値幅＝ATR% の平滑前"),
    "UI": dict(k="ボラ", note="高値からの下落の深さ＝下げ側だけの値動きの大きさ"),
    # 業界の指標（cycles・フロー 段6-g・2026-08-11）
    "EBSW": dict(k="オシレーター", note="長い波と短い波を落として −1〜1 に正規化した波＝行き過ぎの計測"),
    "HT_DCPERIOD": dict(k="ボラ", note="支配的なサイクルの本数＝値動きの速さの計測（向きを持たない）。"
                                       "★ボラに置いた理由＝8つの系統に『サイクル』が無く、"
                                       "向きを持たない値動きの性質の置き場がボラだから（ER と同じ扱い）"),
    "HT_DCPHASE": dict(k="構造・位置", note="サイクルの中のいまの位相（度）＝位置の計測"),
    "HT_INPHASE%": dict(k="オシレーター", note="デトレンドした値段の同相成分＝0 を挟んで振動する"),
    "HT_QUAD%": dict(k="オシレーター", note="同じく直交成分＝0 を挟んで振動する"),
    "HT_SINE": dict(k="オシレーター", note="位相のサイン＝−1〜1 の有界の振動"),
    "HT_LEADSINE": dict(k="オシレーター", note="同上（45度先行）"),
    "HT_TRENDMODE": dict(k="トレンド", note="トレンドかサイクルかの判定そのもの"),
    "MSW_SINE": dict(k="オシレーター", note="フーリエ変換で出した位相のサイン＝−1〜1 の有界の振動"),
    "MSW_LEAD": dict(k="オシレーター", note="同上（45度先行）"),
    # 業界の指標（candles・フロー 段6-h・2026-08-11）
    "実体幅比": dict(k="ローソク", note="実体 ÷ 直前 n 本の平均値幅＝1本のバーの迷いの無さ"),
    "内側バー": dict(k="ローソク", note="高安が前のバーの内側に収まった形"),
    "open_Z": dict(k="オシレーター", note="始値の z スコア＝行き過ぎの計測（うちの zscore と同じ作り）"),
    "high_Z": dict(k="オシレーター", note="高値の z スコア＝同上"),
    "low_Z": dict(k="オシレーター", note="安値の z スコア＝同上"),
    "HA実体%": dict(k="ローソク", note="平均足の実体＝ならしたローソクの向きと厚み"),
    "HA上ヒゲ比": dict(k="ローソク", note="平均足の上ヒゲの割合"),
    "HA下ヒゲ比": dict(k="ローソク", note="平均足の下ヒゲの割合"),
    "close vs MEDIAN%": dict(k="構造・位置"), "MEDIAN傾き%": dict(k="トレンド"),
    "LRangle": dict(k="トレンド"),
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
    "前期間pivotPP": dict(k="構造・位置"), "前期間pivotR1": dict(k="構造・位置"), "前期間pivotS1": dict(k="構造・位置"),
    "fib位置": dict(k="構造・位置"), "POC": dict(k="構造・位置"), "VAH": dict(k="構造・位置"),
    "VAL": dict(k="構造・位置"), "S-Rタッチ数": dict(k="構造・位置"),
    # ★2026-10-07（工事 m2c15-period-textbook-20261007）＝教科書の期間の区切りの版（監査 CP60 の修正41・42・K-7 の決定）
    "close vs VWAP典型": dict(k="構造・位置"), "当日VWAP": dict(k="構造・位置"),
    "前週pivotPP": dict(k="構造・位置"), "前週pivotR1": dict(k="構造・位置"), "前週pivotS1": dict(k="構造・位置"),
    "前日POC": dict(k="構造・位置"), "前日VAH": dict(k="構造・位置"), "前日VAL": dict(k="構造・位置"),
    "当日POC": dict(k="構造・位置"), "当日VAH": dict(k="構造・位置"), "当日VAL": dict(k="構造・位置"),
    # ★2026-09-26（M2-E-4c・束2）＝S-Rタッチ数 と同じ数え方。許容幅だけが1時間足の値動きの幅に連動する。
    "S-Rタッチ1時間ATR": dict(k="構造・位置", note="S-Rタッチ数と同じ数え方で、許容幅を1時間足の ATR% に連動させたもの"),
    # ★2026-10-09（工事 m2c15-shape-structure-20261009）＝確定した山・谷で作る教科書の版（監査 CP60 の修正43・44・46）
    "W字確定谷": dict(k="構造・位置", note="W字と同じ（ダブルボトム＝構造パターン）"),
    "S-Rタッチ確定数": dict(k="構造・位置"), "S-Rタッチ確定1時間ATR": dict(k="構造・位置"),
    # ★2026-10-20（工事 m2c15-band-s1-20261020）＝帯の部品（法則 R1・R7）と S1 の部品（1本の動き ÷ ふだんの動き＝ばらつき）
    "帯スイング": dict(k="構造・位置"), "帯スイング1時間ATR": dict(k="構造・位置"),
    "帯pivot": dict(k="構造・位置"), "帯pivot1時間ATR": dict(k="構造・位置"),
    "帯pivot前週": dict(k="構造・位置"), "帯pivot前週1時間ATR": dict(k="構造・位置"),
    "帯VA": dict(k="構造・位置"), "帯VA1時間ATR": dict(k="構造・位置"),
    "LeeMykland": dict(k="ボラ", note="法則 S1 の「見ているもの」＝1本の動き ÷ ふだんの動き（regime_detection_kb.md の 11-5）"),
    "LeeMykland_E36版": dict(k="ボラ", note="LeeMykland と同じ（E36 の式＝ふだんの揺れに今の1本を入れる版）"),
    "SMC_SWEEP確定": dict(k="構造・位置", note="SMC_SWEEP と同じ（確定した山・谷を抜いて戻した足＝水準に関わる判定）"),
    # ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c）＝計算式の教科書の版（系統は元の種類と同じ）
    "realized_vol_rv": dict(k="ボラ"), "SQZ_ON_Carter": dict(k="ボラ"), "THERMO原作%": dict(k="ボラ"), "THERMO_EMA%": dict(k="ボラ"),
    "StochRSI素%K": dict(k="オシレーター"), "DPO教科書%": dict(k="オシレーター"),
    "TRIX_EMAシグナル": dict(k="トレンド"), "TRIX_EMAヒスト": dict(k="トレンド"),
    "close vs SSF平均%": dict(k="構造・位置"), "close vs TRIMA_TA%": dict(k="構造・位置"), "close vs VIDYA_CMO%": dict(k="構造・位置"),
    "close vs HT_TRENDLINE_HL%": dict(k="構造・位置"), "close vs MAMA_HL%": dict(k="構造・位置"), "close vs FAMA_HL%": dict(k="構造・位置"),
    "ABER原作位置": dict(k="構造・位置", note="ABER位置 と同じ（帯の中の位置）"),
    # ★2026-09-05（M2-C-4）に足した。S-RタッチATR は 2026-09-06（再監査 cp22 の N-1）に外した。
    "レンジ幾何": dict(k="構造・位置", note="RG ゾーンビルダーの帯＝構造そのもの"),
    # 山と谷（2026-08-21・M2-2-6）＝高値と安値の並びそのもの＝構造・位置
    "fractal高値距離%": dict(k="構造・位置", note="前後が下がった実際の山との距離（k本 遅れで確定）"),
    "fractal安値距離%": dict(k="構造・位置", note="同じく谷との距離"),
    "高値切り上げ幅%": dict(k="構造・位置", note="ダウ理論の Higher High（法則 U1）を数字にしたもの"),
    "安値切り上げ幅%": dict(k="構造・位置", note="同じく Higher Low／マイナスなら Lower Low（法則 D1）"),
    "構造破断距離%": dict(k="構造・位置", note="1つ前に確定した谷との距離（法則 U9・構造破断）"),
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
    "CFO": (("cfo",), "fosc は同じ式（実測でぴったり重なる）＝『入れない』の一覧に載せている"),
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
    "SQZ%": (("squeeze",), "squeeze が4列 返す"),
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
    # ── volume 16関数（4回目）──
    "ADOSC比": (("adosc",), "出来高スケール。うちは平均出来高で割る（H6）"),
    "AOBV_LR": (("aobv",), "aobv が7列 返すうち、買い側の1列だけ入れた（式の上で slow は効かず SR は裏返し）"),
    "EFI比": (("efi",), "値段×出来高。うちは終値と平均出来高で割って%化（H6）"),
    "EOM比": (("eom",), "値段²÷出来高。うちは平均出来高と終値²で無次元化（H6）"),
    "MARKETFI比": (("marketfi",), "値段÷出来高。うちは平均出来高と終値で無次元化（H6）"),
    "NVI傾き": (("nvi",), "積み上げそのもの。うちは n 本の増分（変化率%の足し算＝すでに無次元）"),
    "PVI傾き": (("pvi",), "同上"),
    "PVOL比": (("pvol",), "売買代金そのもの。うちは n 本平均に対する倍率（H6）"),
    "PVT傾き": (("pvt",), "積み上げそのもの。うちは増分を出来高の合計で割る（H6）"),
    "WAD傾き": (("wad",), "値段の単位の積み上げ。うちは増分を終値で割って%化（H6）"),
    "KVO比": (("kvo",), "kvo が本体とシグナルをまとめて返す。うちは平均出来高で割る（H6）"),
    "KVOシグナル比": (("kvo",), "同上"),
    "VOSC": (("vosc",), "もともと%＝そのまま"),
    "VFI": (("vfi",), "★ライブラリの実装は使わない（全部ゼロになる）。教科書の式で書き直した"
                      "＝まこさん承認 2026-08-10・逐語「１，２は修正して残す」"),
    "出来高変化率%": ((), "ライブラリに相当する関数が無い。pvr（1〜4 の区分）の中身の半分を"
                          "材料にしたもの＝まこさん承認 2026-08-10"),
    # ── statistics 13関数（5回目）──
    "skew": (("skew",), ""), "kurtosis": (("kurtosis",), ""),
    "MAD比": (("mad",), "値段の単位。うちは終値で割って%化（H6）"),
    "stdev%": (("stdev",), "値段の単位。うちは終値で割って%化（H6・母標準偏差＝ddof 0）"),
    "close vs MEDIAN%": (("median",), "値段そのもの。うちは終値との距離%（H6）"),
    "MEDIAN傾き%": (("median",), "同上（傾きの形）"),
    # ── volatility 12関数（6回目）──
    "close vs ABER_ZG%": (("aberration",), "aberration が中心線・上の帯・下の帯・ATR の4列を返す。"
                                           "うちは終値との距離%（H6）。★ATR の列は入れない＝"
                                           "うちの ATR%（期間 7/14/21）と同じ指標"),
    "ABER位置": (("aberration",), "同上。帯の中の位置。★帯の幅は 2×ATR15 ＝ うちの ATR% の定数倍なので入れない"),
    "close vs ACCBL%": (("accbands",), "accbands が下の帯・中心線・上の帯の3列を返す。うちは終値との距離%（H6）。"
                                       "★中心線は入れない＝うちの close vs SMA%20/50/200 と実測 差 0"),
    "close vs ACCBU%": (("accbands",), "同上（上の帯）"),
    "close vs CE_L%": (("ce",), "ce が買い側・売り側の2列を返す。値段そのものなので終値との距離%（H6）"),
    "close vs CE_S%": (("ce",), "同上（売り側）"),
    "CVI": (("cvi",), "もともと%＝そのまま"),
    "HWC位置": (("hwc",), "hwc が中心線・上の帯・下の帯・幅・位置の5列を返す（channel_eval=True）。"
                          "うちが足すのは帯の2列だけ。★中心線は入れない＝うちに既に在る close vs HWMA% の"
                          "HWMA と同じ値だった（2026-08-10 実測＝40,000本すべて 最大差 0.0）。"
                          "★上下の帯そのものも入れない＝この位置と下の幅%で表す（BB%b・BB幅 と同じ流儀）"),
    "HWC幅%": (("hwc",), "同上。幅は値段の単位なので終値で割って%化（H6）"),
    "MASSI": (("massi",), "もともと比の合計＝そのまま"),
    "PDIST%": (("pdist",), "値段の単位。うちは終値で割って%化（H6）"),
    "RVI": (("rvi",), "もともと 0〜100＝そのまま。★名前の似た RVGI（相対活力指数）とは別の関数"),
    "THERMO%": (("thermo",), "thermo が値・その EMA・0/1 の2列 の4列を返す。値は値段の単位なので%化（H6）。"
                             "★0/1 の2列は入れない＝THERMO比 に固定の閾値 2・0.5 を当てただけ"),
    "THERMO比": (("thermo",), "同上。値をその EMA で割った比＝もともと無次元"),
    "TR%": (("true_range",), "値段の単位。うちは終値で割って%化（H6）。★うちの ATR% は これを Wilder 平滑したもの"),
    "UI": (("ui",), "もともと%＝そのまま"),
    # ── cycles 8関数（フロー 段6-g・2026-08-11）──
    "EBSW": (("ebsw",), "★ライブラリの関数は使っていない＝ライブラリが角度の単位を取り違えている"
                        "（教科書は度・ライブラリは度の数字をそのままラジアンとして sin/cos に入れる）。"
                        "2026-08-11 実測＝係数 alpha1 が 教科書 +0.854081 ／ ライブラリ −0.645222、"
                        "系列の相関 +0.5878＝別物。VFI と同じく教科書（J.F.Ehlers）の式で書き直した"),
    "HT_DCPERIOD": (("ht_dcperiod",), "もともと『本数』＝そのまま"),
    "HT_DCPHASE": (("ht_dcphase",), "もともと『度』＝そのまま。★円環の量（−45〜315）"),
    "HT_INPHASE%": (("ht_phasor",), "ht_phasor が同相成分と直交成分の2列を返す。値段の単位なので終値で割って%化（H6）"),
    "HT_QUAD%": (("ht_phasor",), "同上（直交成分）"),
    "HT_SINE": (("ht_sine",), "ht_sine がサイン波と45度先行の2列を返す。もともと −1〜1＝そのまま"),
    "HT_LEADSINE": (("ht_sine",), "同上（45度先行）"),
    "HT_TRENDMODE": (("ht_trendmode",), "もともと 0/1＝そのまま"),
    "MSW_SINE": (("msw",), "msw がサイン波と45度先行の2列を返す。もともと −1〜1＝そのまま"),
    "MSW_LEAD": (("msw",), "同上（45度先行）"),
    # ── candles 4関数（フロー 段6-h・2026-08-11）──
    "実体幅比": (("cdl_doji",), "cdl_doji（十字線）の中身の連続値。★ライブラリが返す 0/1 は入れない＝"
                              "『実体 ≤ 直前10本の平均値幅の10%』という固定の閾値を当てただけで、"
                              "閾値は engine_tuner が探すもの（教訓 L-408・THERMO の 0/1 と同じ扱い）"),
    "内側バー": (("cdl_inside",), "そのまま（±1・0）。★うちの 孕み足 とは別もの＝"
                                "孕み足は実体、内側バーは高安が内側に収まる形"),
    "open_Z": (("cdl_z",), "cdl_z が 始値・高値・安値・終値 の4つの z スコアを返す。もともと無次元＝そのまま。"
                           "★終値の z 値は入れない＝うちの zscore の本数違い（2026-08-11 実測＝"
                           "本数30 のうちの式とスピアマン相関 1.0000000・最大差 5.3e-07）"),
    "high_Z": (("cdl_z",), "同上（高値）"),
    "low_Z": (("cdl_z",), "同上（安値）"),
    "HA実体%": (("ha",), "ha が平均足の4本値を返す。★4本値そのものは入れない＝値段（H6）。"
                        "実体は値段の単位なので終値で割って%化"),
    "HA上ヒゲ比": (("ha",), "同上。上ヒゲ ÷ 全幅＝もともと比"),
    "HA下ヒゲ比": (("ha",), "同上。下ヒゲ ÷ 全幅＝もともと比"),
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
    "LRangle": (("linregangle",), "★角度は値段の単位に依存する（実測）。うちは傾きを%にしてから角度にする＝流儀が違う"),
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
    "fractal高値距離%": ((), "前後 k本 より高い中央のバー（山）との距離%。ライブラリに相当する関数が無い"),
    "fractal安値距離%": ((), "同上（谷）"),
    "高値切り上げ幅%": ((), "確定した山どうしの差%。ライブラリに相当する関数が無い"),
    "安値切り上げ幅%": ((), "同上（谷）"),
    "構造破断距離%": ((), "終値と1つ前に確定した谷の距離%。ライブラリに相当する関数が無い"),
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
    # ★G-2（2026-10-04・工事 m2c15-indicator-six-items-20261004）＝監査 CP60 の修正18〜21 で足した教科書の前期間 pivot。151回目に当てたとき、
    #   この対応表に足し忘れ、観察の道具の自己テスト（検査10）が止まっていた。ライブラリの cpr と同じ作りかは照らしていない（定義表の既知答え＝修正20 で確かめる）。
    "前期間pivotPP": ((), "前の UTC の日で固定する教科書の PP。ライブラリの cpr と同じ作りかは照らしていない（定義表の既知答えで確かめる）"),
    "前期間pivotR1": ((), "同上（教科書の R1＝2×PP − 前の期間の安値）"),
    "前期間pivotS1": ((), "同上（教科書の S1＝2×PP − 前の期間の高値）"),
    "fib位置": ((), "N本の高安の中で終値がどこか（0〜1）。式の形は Stoch%K と同じだが、"
                   "フィボナッチの関数はライブラリに無い"),
    "POC": (("vp",), "vp＝出来高プロファイル。POC・VAH・VAL をまとめて出す"),
    "VAH": (("vp",), "同上"),
    "VAL": (("vp",), "同上"),
    # ★2026-10-07（工事 m2c15-period-textbook-20261007）＝教科書の期間の区切りの版
    "close vs VWAP典型": ((), "ta の VolumeWeightedAveragePrice（n 本の移動窓＋典型価格）と同じ作り（定義表の外部照合で確かめる）。pandas-ta の vwap は日の始まりから積み上げる版＝当日VWAP"),
    "当日VWAP": (("vwap",), "pandas-ta の vwap（anchor の既定 D＝日の始まりから積み上げる典型価格・overlap/vwap.py）。定義表の2つ目の照合で値を確かめる"),
    "前週pivotPP": ((), "前の週で固定する教科書の PP。ライブラリの cpr と同じ作りかは照らしていない（定義表の既知答えで確かめる）"),
    "前週pivotR1": ((), "同上（教科書の R1＝2×PP − 前の週の安値）"),
    "前週pivotS1": ((), "同上（教科書の S1＝2×PP − 前の週の高値）"),
    "前日POC": (("vp",), "vp の作りを前の UTC の日で区切ったもの。日で区切る形はライブラリと照らしていない（定義表の既知答えで確かめる）"),
    "前日VAH": (("vp",), "同上"),
    "前日VAL": (("vp",), "同上"),
    "当日POC": (("vp",), "vp の作りを、その日の0時から1本前までで区切ったもの。日で区切る形はライブラリと照らしていない（定義表の既知答えで確かめる）"),
    "当日VAH": (("vp",), "同上"),
    "当日VAL": (("vp",), "同上"),
    "S-Rタッチ数": ((), "同じ値段に何回 触れたか。ライブラリに相当する関数が無い"),
    "S-Rタッチ1時間ATR": ((), "S-Rタッチ数の許容幅を1時間足の ATR% に連動させたもの。ライブラリに相当する関数が無い"),
    # ★2026-10-09（工事 m2c15-shape-structure-20261009）＝確定した山・谷で作る教科書の版
    "W字確定谷": ((), "ダブルボトムの教科書の版（確定した谷・ネック・最初の上抜け）。ライブラリに相当する関数が無い"),
    "S-Rタッチ確定数": ((), "確定した山・谷のうち今の値段の帯に入る数。ライブラリに相当する関数が無い"),
    "S-Rタッチ確定1時間ATR": ((), "S-Rタッチ確定数の許容幅を1時間足の ATR% に連動させたもの。ライブラリに相当する関数が無い"),
    # ★2026-10-20（工事 m2c15-band-s1-20261020）＝帯の部品と S1 の部品
    "帯スイング": ((), "確定したスイングを束ねた上下の帯（法則 R1・R7）。ライブラリに相当する関数が無い"),
    "帯スイング1時間ATR": ((), "帯スイング の許容幅を1時間足の ATR% に連動させたもの。ライブラリに相当する関数が無い"),
    "帯pivot": ((), "前の日の pivot R1・S1 の間に終値が在り、取れる距離が手数料の床以上か（法則 R7）。ライブラリに相当する関数が無い"),
    "帯pivot1時間ATR": ((), "帯pivot の許容幅を1時間足の ATR% に連動させたもの。ライブラリに相当する関数が無い"),
    "帯pivot前週": ((), "前の週の pivot R1・S1 の間に終値が在り、取れる距離が手数料の床以上か（法則 R7）。ライブラリに相当する関数が無い"),
    "帯pivot前週1時間ATR": ((), "帯pivot前週 の許容幅を1時間足の ATR% に連動させたもの。ライブラリに相当する関数が無い"),
    "帯VA": ((), "前の日の VAL・VAH の間に終値が在り、取れる距離が手数料の床以上か（法則 R7）。ライブラリに相当する関数が無い"),
    "帯VA1時間ATR": ((), "帯VA の許容幅を1時間足の ATR% に連動させたもの。ライブラリに相当する関数が無い"),
    "LeeMykland": ((), "Lee-Mykland（2008）の jump の検定統計（論文の式(8)どおり）。ライブラリに相当する関数が無い"),
    "LeeMykland_E36版": ((), "E36 の jump の統計（ふだんの揺れに今の1本を入れる版・E36 から移した）。ライブラリに相当する関数が無い"),
    "SMC_SWEEP確定": ((), "pandas-ta の smc_sweep は直前 n 本の高安とヒゲの倍率で作る別の版。確定した山・谷で作る教科書の版の関数は"
                          "ライブラリに無い（定義表の既知答えで確かめる）"),
    # ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c）＝計算式の教科書の版（ライブラリの相当する関数と、作りの違い）
    "realized_vol_rv": (("hvol",), "hvol は平均を引いた標準偏差。平均を引かない版の関数はライブラリに無い"),
    "SQZ_ON_Carter": (("squeeze",), "squeeze はケルトナーの中心を終値の SMA・幅を真の値幅の SMA で作る。Carter の作りの関数はライブラリに無い"),
    "StochRSI素%K": (("stochrsi",), "stochrsi の k を 1 にしたもの（ならさない）"),
    "TRIX_EMAシグナル": (("trix", "ema"), "trix の本体を ema でならしたもの（trix のシグナルは単純移動平均）"),
    "TRIX_EMAヒスト": (("trix", "ema"), "同上（本体との差）"),
    "close vs SSF平均%": (("ssf",), "ssf は入力を2本の平均にしていない。Ehlers の式の関数はライブラリに無い"),
    "close vs TRIMA_TA%": (("trima",), "trima は偶数の n でも n/2+1 を2回。TA-Lib の偶数の形の関数はライブラリに無い"),
    "close vs VIDYA_CMO%": (("vidya",), "vidya は CMO の本数を n と同じにする。別に持つ形の関数はライブラリに無い"),
    "close vs HT_TRENDLINE_HL%": (("ht_trendline",), "入力を (高値＋安値)/2 にして呼ぶ"),
    "close vs MAMA_HL%": (("mama",), "入力を (高値＋安値)/2 にして呼ぶ"), "close vs FAMA_HL%": (("mama",), "同上"),
    "DPO教科書%": (("dpo", "sma"), "dpo の centered=False（いまの終値 − k本前の SMA）と値が違う。k本前の終値 − いまの SMA を sma で作る"),
    "ABER原作位置": ((), "aberration は HLC3 の SMA ± ATR の別の作り。原作（80本・2σ のボリンジャー）の関数は aberration の名ではライブラリに無い"),
    "THERMO原作%": (("thermo",), "thermo は絶対値を取る（内はらみ足も 0 にならない）。原作の関数はライブラリに無い"),
    "THERMO_EMA%": (("thermo", "ema"), "原作の温度計を ema でならす"),
    # ★2026-09-05（M2-C-4）に足した。ライブラリに相当する関数が無い＝空のタプルと理由。
    #   S-RタッチATR は 2026-09-06（再監査 cp22 の N-1）に外した。
    "MMI": ((), "Market Meanness Index。ta にも pandas-ta にも無い"
                "（原典＝The Financial Hacker の記事の C のコード）"),
}

# ★入れない候補（★まこさんの承認はまだ・next_step §5 の10番）。既定は「入れる」（まこさん決定＝
#   「利益最大化するために完全に不要な指標以外はすべて入れてほしい」）。だから ここに載せるのは
#   「指標ではないもの」に限る。1件ずつ理由を書く。
# ★まこさんが実際に承認した「入れない」の一覧（2026-08-09・逐語「1,2,3,4全部いれないくていい」）。
#   出どころ＝そのときの materials.md（git の 03aad50 の ★4）から機械で取り出した19件。
#   ★これ以降に足したものは まこさんの承認を受けていない。materials.md が1件ずつ ✅／★未承認 で出す。
#   2026-08-10 に、文書が44件すべてを「承認済み」と書いていたのを是正した（承認の偽装になっていた）。
SKIP_APPROVED_20260809: frozenset = frozenset({
    "hl2", "hlc3", "ohlc4", "wcp", "medprice", "typprice", "avgprice",
    "drawdown", "log_return", "percent_return",
    "increasing", "decreasing", "long_run", "short_run", "tsignals", "xsignals",
    "decay", "edecay", "ma",
    # ★willr は同じ日にまこさんが名指しで「入れない」と言われている（逐語＝「willrは入れない。
    #   他にも同じ挙動の指標があれば紛らわしいので片方を省いていく」）。2026-08-10 に足した
    #   （それまで CC が ★未承認 に入れていた＝印の付け忘れ）。
    "willr",
})

# ★「方針は承認済み」＝まこさんが 2026-08-09 に承認した方針に当たるもの（逐語＝
#   「他にも同じ挙動の指標があれば紛らわしいので片方を省いていく」）。
#   ★「同じ挙動かどうか」の判定は CC が実測でやった＝まこさんは1件ずつは見ていない。
#   だから ✅（名指しの承認）とは分ける（まこさん OK 2026-08-10・印を3種類にする）。
#   ★ここに入れ忘れたものは ★未承認 として出る＝承認が勝手に広がらない側に倒してある。
SKIP_POLICY_DUP_20260809: frozenset = frozenset({
    "rocp", "rocr", "rocr100", "stochf", "fosc", "macdext", "macdfix",
    "slope", "smi", "plus_dm", "minus_dm", "ad", "emv", "md", "quantile",
})

# ★2026-08-10 にまこさんが承認した「入れない」（逐語＝「４…→OK ／ １，２は修正して残す。
#   ３は入れないということだよね」）。CC が9件を型ごとに説明し、まこさんが「３」＝この7件を
#   入れないと確認した。★pvr は入れていない＝「1〜4 の区分そのものを入れない」ことについて
#   明示の逐語が無いため（中身の半分は「出来高変化率%」として材料に入れた）。承認は広げない。
SKIP_APPROVED_20260810: frozenset = frozenset({
    "mavp", "tos_stdevall", "entropy", "stderr", "variance", "beta", "correl",
})

# 承認の一覧（印つき）＝gen_materials が1件ずつ印を付けるために読む。印は3種類（まこさん OK 2026-08-10）。
#   ✅ …まこさんが名指しで「入れない」と言われたもの
#   ◯ …まこさんが方針を承認したもの（同じ挙動なら片方を省く）。同じかどうかの判定は CC の実測
#   ★未承認 …上のどちらにも当たらないもの（この辞書に無いもの）
SKIP_APPROVED: dict[str, str] = {
    **{fn: "✅ 2026-08-09" for fn in SKIP_APPROVED_20260809},
    **{fn: "✅ 2026-08-10" for fn in SKIP_APPROVED_20260810},
    **{fn: "◯ 方針は承認済み（判定は CC の実測）" for fn in SKIP_POLICY_DUP_20260809},
}

INDUSTRY_SKIP: dict[str, str] = {
    # (2026-08-11・段6 の 6-9① で新しく「入れない」にしたもの)
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
    "ad": "★うちの CMF そのもの。CMF の定義＝Σ(CLV×出来高)÷Σ出来高 は、AD（CLV×出来高 の積み上げ）の"
          "n 本の増分を同じ n 本の出来高の合計で割ったものと式の上で同じ"
          "（2026-08-10 実測＝AD傾き20 ＝ 1×CMF20 ＋ −5.2e-14・ずれ 1.0e-10。総当たりの重複検出が捕まえた）",
    "emv": "eom（イーズ・オブ・ムーブメント）を 1本平均で出したものの1万分の1（実測 2026-08-10＝"
           "eom(length=1) ÷ emv の比が 158,112 本すべてで 10000.000000 ・ばらつき 1.3e-12）。"
           "うちは EOM比 として入れている＝重複",
    # (d) 数の大小に意味が無い＝『値 ≥ 閾値』の形の条件に使えない（2026-08-10・volume）
    "pvr": "1〜4 の区分（1＝上げ×出来高増／2＝上げ×出来高減／3＝下げ×出来高増／4＝下げ×出来高減）。"
           "数が大きいほど◯◯という並びになっておらず、2 と 3 の境目で意味が反転する。"
           "engine_tuner の条件は『値 ≥ 閾値』の形なので、この並びのままでは条件にできない。"
           "★2026-08-10 訂正＝前は『中身の2つは ROC と volume_ratio で表せる』と書いていたが、"
           "実測で間違いだった。『終値が上げたか』は ROC1 ≥ 0 と一致率 1.0000 で表せるが、"
           "『出来高が前の足より増えたか』は volume_ratio20 ≥ 1 と一致率 0.6737 しかない"
           "（volume_ratio は 20本平均に対する倍率で、前の足との比較ではないため）。"
           "★足りていなかった半分は『出来高変化率%』として材料に入れた"
           "（まこさん承認 2026-08-10・逐語「１，２は修正して残す」）＝"
           "入れないのは 1〜4 の区分そのものだけ",
    "tos_stdevall": "★未来を見る（H2 違反）。既定の length=None で『データ全部』に回帰直線を引き、"
                    "全期間の標準偏差を足し引きするので、各足の値がその足より後のデータで変わる。"
                    "2026-08-10 実測＝同じ足の値が、データを 2,000本で切ると 3,000本のときと最大 213.06 ずれる",
    "beta": "別の銘柄の系列（benchmark）が要る。うちは BTCUSDT の1本だけなので、自分自身との比＝常に 1 になる",
    "correl": "同上（別の銘柄との相関）",
    "md": "mad（平均絶対偏差）と同じ関数を呼ぶだけ（実物のコードの逐語＝result = mad(close, length=length)・"
          "実測でも最大差 0）",
    "quantile": "既定が中央値＝median と同じ（実測＝最大差 0）",
    "stderr": "stdev の定数倍（stdev の 1/√(n−1) 倍。実測＝比が 0.18569533〜0.18569539 で一定・1/√29＝0.185695338）。"
              "定数倍は『値 ≥ 閾値』の条件として同じ並びになる＝新しい条件を作れない",
    "variance": "stdev の2乗（実測＝最大差 9.3e-10）。2乗は大小の並びを変えないので、"
                "『値 ≥ 閾値』の条件として stdev と同じ",
    "dsp": "うちの close vs EMA%（終値が EMA から何%離れているか）の単調変換。"
           "dsp = 終値 − EMA。値段の単位なので終値で割って%化すると (終値−EMA)÷終値 になる。"
           "うちの式は (終値÷EMA − 1)。r = 終値÷EMA と置くと、うちは (r−1)・dsp% は (r−1)÷r で、"
           "r > 0 では大小の並びが完全に一致する。2026-08-11 実測＝**スピアマン相関 1.0000000000**"
           "（値決め窓 157,112 本・暖機1,000本を除く）＝『値 ≥ 閾値』の条件として同じ並びになる。"
           "★ただし dsp の既定の本数 14 は うちの本数の一覧に無い（materials.md ★3 の"
           "『close vs EMA … 9 本・20 本・50 本・200 本』で見える）。この穴は本数の側で埋める＝"
           "同じ形の指標を、名前を変えて2つ持たない。本数を範囲で探せるようにするのがマイルストーン③",
    "avolume": "うちの realized_vol の定数倍（どちらも対数リターンの標準偏差。avolume は母標準偏差×√252・"
               "うちは 標本標準偏差×100）。2026-08-10 実測＝比が値決め窓の全区間で1つの値"
               "（20本 0.154725563499／50本 0.157149610245・式から出る定数 √252×√((n−1)/n)/100 と12桁 一致）。"
               "定数倍は『値 ≥ 閾値』の条件として同じ並びになる＝新しい条件を作れない（stderr と同じ理屈）",
    # (e) ライブラリの実装が壊れていて、実データで値が出ない（2026-08-10 実測で検出）
    "entropy": "★実データでほとんど動かない（値決め窓の実測＝最小 3.3212716880・最大 3.3219280938・"
               "ばらつき 9.1e-06＝上限 log2(10)＝3.3219280949 に張り付く）。原因＝ライブラリが"
               "終値そのものに当てているため、窓の中の値段がどれも近い値になり、分布がほぼ均等になる。"
               "条件の材料にならない（どの閾値でも切れない）。★2026-08-10 実測＝入力を変化率に変えても"
               "直らない（ばらつき 4.0e-06・幅 1.7e-04）。ライブラリの作り（窓の合計で割って分布にする）"
               "が原因なので、入力の直しでは動かない",
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
