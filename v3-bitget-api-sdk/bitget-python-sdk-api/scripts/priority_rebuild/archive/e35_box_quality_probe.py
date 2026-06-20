#!/usr/bin/env python3
"""e35_box_quality_probe.py — 箱の質（出来高の厚み・タッチ回数）＋レンジ純度（ER×ADX）が
TP(中心C回帰)玉 と 非TP(TIME/SL)玉 を分けるかを測る解剖プローブ（採点窓＋学習窓・両窓一致）。

背景: まこさん別AIリサーチ（複数タッチ＋出来高ノードで箱品質）の事前検証 ＋ iter4 N12（ER低×ADX低だけ+）の両窓再現。
方法: 玉単位。entry idx で box_strength・タッチ回数(±0.1%/±0.3%)・ER・ADX を df から再付与。
  - タッチ回数 = 過去 N_TOUCH 本で low/high が壁価格±tol 以内に入った回数（当該バーまで＝leak-safe）。
  - 採点窓(score)と学習窓(train)の両方で出し、両窓一致だけを本物の候補にする。
分析のみ・net は CSV(eval_engine 由来)。固定値(tol/N/中央境界)は検証用＝採点窓スイープしない(L-267 非該当)。
"""
import sys
import numpy as np
import pandas as pd

PR = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild"
sys.path.insert(0, PR)
import e35_range_oscillation as e35   # noqa: E402  _load / _attach_entry_cols
import e35_box                        # noqa: E402  BOX_N / box 列名

RAT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/results/priority_rebuild/ratchet"
TAG = sys.argv[1] if len(sys.argv) > 1 else "iter4"
SCORE = f"{RAT}/trades_e35_oscillation_5m_{TAG}_score.csv"
TRAIN = f"{RAT}/trades_e35_oscillation_5m_{TAG}_train.csv"
OUT = f"{RAT}/probe_e35_box_quality_{TAG}.txt"
BOX_TF = "5m"
N_TOUCH = e35_box.BOX_N    # 100（箱を探す窓と同じ・固定）

L = []
def p(s=""):
    L.append(str(s)); print(s)

# ── df から box_strength/箱位置/OHLC/ER/ADX を idx 付与（CSV に無いため）──
df = e35._load(0)
e35._attach_entry_cols(df, BOX_TF)
idx_of = {t: i for i, t in enumerate(df["ts"].tolist())}
close = df["close"].to_numpy(float); high = df["high"].to_numpy(float); low = df["low"].to_numpy(float)
sup = df[e35_box.sup_col(BOX_TF)].to_numpy(float)
res = df[e35_box.res_col(BOX_TF)].to_numpy(float)
strength = df[e35_box.strength_col(BOX_TF)].to_numpy(float)
er = df["er"].to_numpy(float); adx = df["adx"].to_numpy(float)


def touch_count(i: int, side: str, tol: float) -> float:
    """entry idx i・side が『逆張りする壁』を過去 N_TOUCH 本で何回タッチしたか（壁±tol 以内・当該バーまで＝leak-safe）。"""
    if not (np.isfinite(sup[i]) and np.isfinite(res[i])):
        return np.nan
    lo = max(0, i - N_TOUCH + 1)
    if side == "LONG":
        S = close[i] / (1.0 + sup[i] / 100.0)
        seg = low[lo:i + 1]
        return float(np.sum(np.abs(seg - S) / S <= tol))
    R = close[i] * (1.0 + res[i] / 100.0)
    seg = high[lo:i + 1]
    return float(np.sum(np.abs(seg - R) / R <= tol))


def load_pos(csv: str) -> pd.DataFrame:
    d = pd.read_csv(csv); d["entry_time"] = pd.to_datetime(d["entry_time"])
    g = d.groupby("position_id").agg(
        entry_time=("entry_time", "first"), side=("side", "first"),
        exit_reason=("exit_reason", "first"), net=("net_usd", "sum")).reset_index()
    ix = g["entry_time"].map(idx_of)
    gv = lambda arr, i: arr[i] if pd.notna(i) and np.isfinite(arr[i]) else np.nan
    g["strength"] = ix.map(lambda i: gv(strength, i))
    g["er"] = ix.map(lambda i: gv(er, i))
    g["adx"] = ix.map(lambda i: gv(adx, i))
    g["touch01"] = [touch_count(int(i), s, 0.001) if pd.notna(i) else np.nan for i, s in zip(ix, g["side"])]
    g["touch03"] = [touch_count(int(i), s, 0.003) if pd.notna(i) else np.nan for i, s in zip(ix, g["side"])]
    g["is_tp"] = g["exit_reason"].isin(["TP_FILLED", "EDGE_TP", "CENTER_LOCK"]).astype(int)  # 戻る玉
    g["win"] = (g["net"] > 0).astype(int)
    return g


g = load_pos(SCORE); gt = load_pos(TRAIN)
days = max((g.entry_time.max() - g.entry_time.min()).days, 1)
# 中央境界は学習窓で固定（覗き見なし・両窓に同じ境界を適用）
er_med = float(gt.er.median()); adx_med = float(gt.adx.median())
p("=" * 88)
p(f"  E35 箱の質＋レンジ純度 プローブ（{TAG}）  採点窓 玉 {len(g)} / net ${g.net.sum():.0f} / 学習窓 玉 {len(gt)}")
p(f"  境界(学習窓中央・両窓共通): ER<{er_med:.3f}=レンジ / ADX<{adx_med:.2f}=弱トレンド")
p("=" * 88)

# ── A. 分離（TP玉 vs 非TP玉 中央値・相関・両窓一致）──
p(f"\n  A. 指標の分離（採点窓中央・★両窓一致=学習窓でも同じ向き・|学習相関|>0.03）")
p(f"   {'指標':<10}{'TP中央':>10}{'非TP中央':>10}{'相関(採点)':>12}{'相関(学習)':>12}  両窓")
for f in ["strength", "touch01", "touch03", "er", "adx"]:
    tp = g[g.is_tp == 1][f]; ntp = g[g.is_tp == 0][f]
    cs = g[f].corr(g["is_tp"]); ct = gt[f].corr(gt["is_tp"])
    same = "一致✓" if (np.isfinite(cs) and np.isfinite(ct) and np.sign(cs) == np.sign(ct) and abs(ct) > 0.03) else "不一致✗"
    p(f"   {f:<10}{tp.median():>10.3f}{ntp.median():>10.3f}{cs:>+12.3f}{ct:>+12.3f}  {same}")

# ── B. タッチ回数ビン別（±0.1% で解像度を上げて再測）──
def bin_table(binner, label):
    p(f"\n  {label}")
    p(f"   {'帯':<14}{'採点 件数':>9}{'TP率':>7}{'net$':>9}{'  ':>2}{'学習 件数':>9}{'TP率':>7}{'net$':>9}")
    for name, ms in binner:
        gs = g[ms(g).fillna(False)]; gtt = gt[ms(gt).fillna(False)]
        cell = lambda x: (len(x), x.is_tp.mean() if len(x) else float('nan'), x.net.sum())
        ns, ts_, vs = cell(gs); nt, tt, vt = cell(gtt)
        p(f"   {name:<14}{ns:>9,}{ts_:>7.2f}{vs:>9.0f}{'  ':>2}{nt:>9,}{tt:>7.2f}{vt:>9.0f}")

bin_table([("0回", lambda d: d.touch01 == 0), ("1回", lambda d: d.touch01 == 1),
           ("2回", lambda d: d.touch01 == 2), ("3-5回", lambda d: (d.touch01 >= 3) & (d.touch01 <= 5)),
           ("6回以上", lambda d: d.touch01 >= 6)],
          "B. タッチ回数ビン別（壁±0.1%・解像度UP）")

# ── C. レンジ純度クロス（★iter4 N12 を両窓で・ER×ADX 4象限の net/TP率・件数）──
p(f"\n  C. レンジ純度クロス ER×ADX（★N12 の両窓再現・学習窓中央で固定）")
def cross(gx, lab):
    gx = gx.dropna(subset=["er", "adx"]).copy()
    gx["er_b"] = np.where(gx.er < er_med, "ER<中(レンジ)", "ER≥中(トレンド)")
    gx["adx_b"] = np.where(gx.adx < adx_med, "ADX<中", "ADX≥中")
    net = gx.pivot_table(index="er_b", columns="adx_b", values="net", aggfunc="sum").round(0)
    tpr = gx.pivot_table(index="er_b", columns="adx_b", values="is_tp", aggfunc="mean").round(2)
    cnt = gx.pivot_table(index="er_b", columns="adx_b", values="net", aggfunc="size")
    p(f"   [{lab}] net$\n" + net.to_string())
    p(f"   [{lab}] TP率\n" + tpr.to_string())
    p(f"   [{lab}] 件数\n" + cnt.to_string())
cross(g, "採点窓"); cross(gt, "学習窓")

# ── D. フィルタ・シミュ（弱い箱/非レンジを除外で 非TP削減・TP残存・net・玉/日・両窓）──
p(f"\n  D. フィルタ・シミュ（★両窓で net 改善＋件数が尻すぼみでないか）")
p(f"   現状: 採点 net ${g.net.sum():.0f} / 玉 {len(g)}({len(g)/days:.2f}/日) / 非TP {len(g[g.is_tp==0])} / TP {len(g[g.is_tp==1])}")
sq = gt["strength"].quantile([1/3, 2/3]).tolist()
filters = [
    ("タッチ01≥3", lambda d: d.touch01 >= 3),
    ("厚み≥2/3分位", lambda d: d.strength >= sq[1]),
    ("ER<中(レンジ)", lambda d: d.er < er_med),
    ("ADX<中(弱トレンド)", lambda d: d.adx < adx_med),
    ("ER<中 & ADX<中(純レンジ)", lambda d: (d.er < er_med) & (d.adx < adx_med)),
]
p(f"   {'フィルタ':<26}{'採点net$':>9}{'玉':>6}{'/日':>6}{'非TP':>6}{'TP':>5}{'  ':>2}{'学習net$':>9}{'玉':>6}")
for name, m in filters:
    gs = g[m(g).fillna(False)]; gtt = gt[m(gt).fillna(False)]
    dd = max((gs.entry_time.max() - gs.entry_time.min()).days, 1) if len(gs) else 1
    p(f"   {name:<26}{gs.net.sum():>9.0f}{len(gs):>6}{len(gs)/dd:>6.2f}"
      f"{len(gs[gs.is_tp==0]):>6}{len(gs[gs.is_tp==1]):>5}{'  ':>2}{gtt.net.sum():>9.0f}{len(gtt):>6}")

# ── E. NaN/箱なし玉 ──
p(f"\n  E. 箱なし(NaN)玉: 採点 厚み{g.strength.isna().sum()}/{len(g)} ER{g.er.isna().sum()} ／ タッチ中央(±0.1%) {g.touch01.median():.0f}回・(±0.3%) {g.touch03.median():.0f}回")

p("\n" + "=" * 88)
open(OUT, "w").write("\n".join(L))
print(f"\n[保存] {OUT}")
