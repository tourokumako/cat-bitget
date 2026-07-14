"""rg6_adaptive_band_diag.py — read-only 診断（診断レーン・CSV/score なし・print のみ）

ATR 連動の束ね幅（RG-v6 案）が狙い通りか検証（共有 builder は触らない・自前replicaで比較）:
  ① 高ボラ帯の range_ok 率が上がるか（＝高ボラレンジを拾えるか）
  ② 平坦帯の帯幅が鋭くなるか（＝下弦/轢かれの根の是正）
  ③ 総 range_ok 件数が落ちないか（＝頻度維持）
v5（固定 tol=0.3%）と v6（tol=clamp(K×ATR%_1h, 0.15%, 0.6%)）を同一 uptrend/brk で比較。
"""
import sys, pathlib
import numpy as np
import pandas as pd
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import e37_range_scalp as e37
rgmod = e37._import_rg5()          # build_regime_gate_rg（v17・sf・_uptrend_state_5m を内包）
v17 = rgmod.v17; sf = rgmod.sf
BASE = HERE.parent.parent
CANDLE = BASE / "data" / "BTCUSDT-5m-2024-09-01_2026-02-28_slice_V9FULL_safe.csv"

K_TOL, TOL_MIN, TOL_MAX = 1.0, 0.0015, 0.006   # RG-v6 案の初期値

def zones_adaptive(px_arr, idx_arr, i, lo_w, price, above, tol):
    j0 = int(np.searchsorted(idx_arr, lo_w)); j1 = int(np.searchsorted(idx_arr, i + 1))
    if j1 <= j0: return []
    px = px_arr[j0:j1]; sel = (px > price) if above else (px < price)
    if not sel.any(): return []
    px = np.sort(px[sel]); out = []; s = 0
    pad_ov = globals().get("_PAD_OVERRIDE", None)
    for k in range(1, len(px) + 1):
        if k == len(px) or px[k] - px[k - 1] > px[k - 1] * tol:
            cl = px[s:k]
            if len(cl) >= v17.ZONE_TOUCH:
                pad = (tol / 2) if pad_ov is None else pad_ov
                out.append((float(cl.min()) * (1 - pad), float(cl.max()) * (1 + pad)))
            s = k
    out.sort(key=lambda z: abs((z[0] + z[1]) / 2 - price))
    return out

def zones_1h_v6(df1h, tol_arr):
    is_res, is_sup, piv_h, piv_l = sf._detect_fractals(df1h)
    n = len(df1h); c = df1h["close"].to_numpy(float)
    is_res = np.asarray(is_res, bool); is_sup = np.asarray(is_sup, bool)
    piv_h = np.asarray(piv_h, float); piv_l = np.asarray(piv_l, float)
    res_idx = np.flatnonzero(is_res); res_px = piv_h[res_idx]
    sup_idx = np.flatnonzero(is_sup); sup_px = piv_l[sup_idx]
    r_lo = np.full(n, np.nan); r_hi = np.full(n, np.nan); s_lo = np.full(n, np.nan); s_hi = np.full(n, np.nan)
    ok = np.zeros(n, bool)
    start = max(v17.ZONE_LOOKBACK, 25)
    for i in range(start, n):
        tol = tol_arr[i]; lo_w = i - v17.ZONE_LOOKBACK + 1
        rcs = zones_adaptive(res_px, res_idx, i, lo_w, c[i], True, tol)
        if not rcs: continue
        scs = zones_adaptive(sup_px, sup_idx, i, lo_w, c[i], False, tol)
        if not scs: continue
        pairs = sorted(((rz, sz) for rz in rcs for sz in scs),
                       key=lambda p: abs((p[0][0]+p[0][1])/2 - c[i]) + abs((p[1][0]+p[1][1])/2 - c[i]))
        for rz, sz in pairs:
            if (rz[0] - sz[1]) / c[i] >= v17.ZONE_MIN_W:
                r_lo[i], r_hi[i] = rz; s_lo[i], s_hi[i] = sz; ok[i] = True; break
    out = df1h.copy()
    out["res_lo"]=r_lo; out["res_hi"]=r_hi; out["sup_lo"]=s_lo; out["sup_hi"]=s_hi; out["zone_ok"]=ok
    return out

# --- データ・共通部品 ---
df = pd.read_csv(CANDLE); df["ts"] = pd.to_datetime(df["timestamp"]); df = df.reset_index(drop=True)
d5 = df.set_index(pd.DatetimeIndex(df["ts"]))[["open","high","low","close","volume"]]
d1h = v17._resample(d5, "1h")
# 1h ATR% と tol_arr
h1,l1,c1 = d1h["high"].to_numpy(float), d1h["low"].to_numpy(float), d1h["close"].to_numpy(float)
pc1 = np.roll(c1,1); pc1[0]=c1[0]
tr1 = np.maximum(h1-l1, np.maximum(np.abs(h1-pc1), np.abs(l1-pc1)))
atr1 = pd.Series(tr1).rolling(14).mean().to_numpy()
atr_pct_1h = np.where(c1>0, atr1/c1, np.nan)
tol_arr = np.clip(K_TOL*np.nan_to_num(atr_pct_1h, nan=v17.ZONE_TOL), TOL_MIN, TOL_MAX)

idx5 = pd.DatetimeIndex(df["ts"]); up = rgmod._uptrend_state_5m(d5)
c5 = df["close"].to_numpy(float)
# 5m ATR%（帯別集計用）
hh,ll = df["high"].to_numpy(float), df["low"].to_numpy(float); pc5=np.roll(c5,1); pc5[0]=c5[0]
tr5 = np.maximum(hh-ll, np.maximum(np.abs(hh-pc5), np.abs(ll-pc5)))
atr_pct5 = pd.Series(tr5).rolling(14).mean().to_numpy()/c5*100.0

def build_range_ok(z):
    okz = z["zone_ok"].reindex(idx5, method="ffill").fillna(False).astype(bool).to_numpy()
    res_hi = z["res_hi"].reindex(idx5, method="ffill").to_numpy(float)
    sup_lo = z["sup_lo"].reindex(idx5, method="ffill").to_numpy(float)
    res_lo = z["res_lo"].reindex(idx5, method="ffill").to_numpy(float)
    brk = np.where(np.isfinite(res_hi)&np.isfinite(sup_lo), (c5>res_hi)|(c5<sup_lo), False)
    rng = okz & ~brk & ~up
    width = (res_hi - res_lo)/c5*100.0
    return rng, width

z5 = rgmod._zones_1h_rg(d1h)
rng5, w5 = build_range_ok(z5)
sel = (df["ts"]>="2025-06-01")&(df["ts"]<"2026-03-01")&pd.Series(atr_pct5).notna()
def hi_mask(): return (pd.Series(atr_pct5)>=0.4).to_numpy()
def flat_mask(): return (pd.Series(atr_pct5)<0.15).to_numpy()
selN = sel.to_numpy(); hiN = hi_mask(); flN = flat_mask()

print(f"[採点窓 全バー {int(selN.sum())}]  ★頻度=総range_ok / 高ボラ拾い=高ボラrange_ok率 / 下弦是正=平坦帯幅")
print(f"{'構成':28s} {'総range_ok':>10s} {'高ボラrange_ok率':>14s} {'平坦帯幅%中央':>12s} {'全体帯幅%中央':>12s}")
def summ(name, rng, w):
    tot = int((rng&selN).sum())
    hr = (rng[selN&hiN]).mean() if (selN&hiN).sum() else float('nan')
    fw = np.nanmedian(w[rng&selN&flN]) if (rng&selN&flN).sum() else float('nan')
    aw = np.nanmedian(w[rng&selN])
    print(f"{name:28s} {tot:>10d} {hr:>14.3f} {fw:>12.3f} {aw:>12.3f}")
summ("v5(固定tol0.3%)", rng5, w5)
for K in [0.4, 0.5, 0.75, 1.0]:
    for PAD in [None, 0.0005]:   # PAD=None: padding=tol/2（結合）／PAD=0.0005: 固定0.05%（分離）
        ta = np.clip(K*np.nan_to_num(atr_pct_1h, nan=v17.ZONE_TOL), TOL_MIN, TOL_MAX)
        # padding 分離版のため zones を差し替え
        globals()["_PAD_OVERRIDE"] = PAD
        z = zones_1h_v6(d1h, ta)
        rng, w = build_range_ok(z)
        summ(f"v6 K={K} pad={'tol/2' if PAD is None else f'{PAD*100:.2f}%'}", rng, w)
print("\n[done] read-only 診断")
