#!/usr/bin/env python3
"""analyze_e35_deep.py — E35 地面(iter1b)の深掘り分析 N0〜N12（E34 analysis フォーマット準拠・E35 カラム対応）
目的: 入口の質＝TP(中心Cに戻る)玉 vs TIME/SL(戻らない)玉 を何が分けるか炙り出す → jm_ok 厳格化(ER)の根拠。
玉単位（position_id で集約）。entry 時点の ER(Kaufman・jm_ok の素)/箱位置を df から再付与（CSV に無いため）。
分析のみ・net 計算しない（玉/net は CSV＝eval_engine 由来をそのまま使う）。"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild")
import e35_range_oscillation as e35

RAT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/results/priority_rebuild/ratchet"
TAG = sys.argv[1] if len(sys.argv) > 1 else "iter1b"
SCORE = f"{RAT}/trades_e35_oscillation_5m_{TAG}_score.csv"
TRAIN = f"{RAT}/trades_e35_oscillation_5m_{TAG}_train.csv"
OUT = f"{RAT}/analysis_trades_e35_oscillation_5m_{TAG}_score.txt"
BOX_TF = "5m"
L = []
def p(s=""): L.append(str(s)); print(s)

# ── df から ER(jm_ok 素)/箱位置 を entry idx で再付与 ──
df = e35._load(0); e35._attach_entry_cols(df, BOX_TF)
idx_of = {t: i for i, t in enumerate(df["ts"].tolist())}
er = df["er"].to_numpy(float); chop = df["chop"].to_numpy(float)
sup = df["box_sup_dist__5m"].to_numpy(float); res = df["box_res_dist__5m"].to_numpy(float)
sup4 = df["box_sup_dist__4h"].to_numpy(float); res4 = df["box_res_dist__4h"].to_numpy(float)

def load_pos(csv):
    d = pd.read_csv(csv); d["entry_time"] = pd.to_datetime(d["entry_time"])
    # 玉単位に集約（最初の lot の入口特徴・玉の合計net・出口は共通・最大保有）
    g = d.groupby("position_id").agg(
        entry_time=("entry_time", "first"), side=("side", "first"), exit_reason=("exit_reason", "first"),
        net=("net_usd", "sum"), mfe=("mfe_usd", "first"), add_count=("add_count", "first"),
        hold_min=("hold_min", "max"), adx=("adx_at_entry", "first"), stoch_k=("stoch_k_at_entry", "first"),
        box_W=("box_W_pct_at_entry", "first"), atr14=("atr_14", "first"), entry_price=("entry_price", "first"),
        entry_hour=("entry_hour", "first")).reset_index()
    # ER/atr% を entry idx で付与
    ix = g["entry_time"].map(idx_of)
    g["er"] = ix.map(lambda i: er[i] if pd.notna(i) and np.isfinite(er[i]) else np.nan)
    g["chop"] = ix.map(lambda i: chop[i] if pd.notna(i) else np.nan)
    g["sup_d"] = ix.map(lambda i: sup[i] if pd.notna(i) else np.nan)
    g["res_d"] = ix.map(lambda i: res[i] if pd.notna(i) else np.nan)
    g["atr_pct"] = g["atr14"] / g["entry_price"] * 100.0
    g["win"] = (g["net"] > 0).astype(int)
    g["is_tp"] = g["exit_reason"].isin(["TP_FILLED", "EDGE_TP", "CENTER_LOCK"]).astype(int)  # 戻る玉=中心到達系（iter3 は EDGE_TP/CENTER_LOCK）
    return g

g = load_pos(SCORE); gt = load_pos(TRAIN)
days = max((g.entry_time.max() - g.entry_time.min()).days, 1)
p("=" * 78)
p(f"  E35 地面(iter1b) 深掘り分析 N0〜N12  {g.entry_time.min().date()}〜{g.entry_time.max().date()} / 玉 {len(g)} / net ${g.net.sum():.0f}")
p("  目的: 入口の質＝TP(中心C回帰)玉 vs TIME/SL(非回帰)玉 を何が分けるか → jm_ok 厳格化(ER)の根拠")
p("=" * 78)

# N0
p(f"\n  N0. 件数・頻度の妥当性")
p(f"   玉 {len(g)} / 期間 {days}日 / 玉/日 {len(g)/days:.2f} / 出口 {dict(g.exit_reason.value_counts())}")
p(f"   TP率 {g.is_tp.mean():.3f} / 勝率(net>0) {g.win.mean():.3f} / add分布 {dict(g.add_count.value_counts().sort_index())}")

# N1
p(f"\n  N1. 損失の時間構造")
eq = g.sort_values("entry_time"); cum = eq.net.cumsum(); dd = (cum.cummax() - cum)
p(f"   最大DD ${dd.max():.0f} / 玉平均net ${g.net.mean():.2f}")
bydate = g.assign(d=g.entry_time.dt.date).groupby("d").net.sum().sort_values()
p(f"   最悪日 top5: " + " / ".join(f"{k} ${v:.0f}" for k, v in bydate.head(5).items()))

# N7 必要勝率（玉net基準）
win_m = g[g.net > 0].net.mean(); los_m = -g[g.net <= 0].net.mean()
req = los_m / (win_m + los_m) * 100 if (win_m + los_m) else float("nan")
p(f"\n  N7. 必要勝率と不足（玉net）")
p(f"   平均勝ち ${win_m:.2f} / 平均負け ${los_m:.2f} → 必要勝率 {req:.1f}% / 実際 {g.win.mean()*100:.1f}% / 不足 {req-g.win.mean()*100:.1f}pt")

# N8 負け玉 vs 勝ち玉（TP vs 非TP の入口差＝入口の質）
p(f"\n  N8. TP玉 vs 非TP玉(TIME/SL) の入口指標差（★戻る玉と戻らない玉の違い＝入口の質）")
feats = ["er", "chop", "adx", "stoch_k", "box_W", "atr_pct", "sup_d", "res_d", "add_count", "hold_min"]
tp = g[g.is_tp == 1]; ntp = g[g.is_tp == 0]
p(f"   {'指標':<10}{'TP玉中央':>12}{'非TP中央':>12}{'差':>10}")
for f in feats:
    a, b = tp[f].median(), ntp[f].median()
    p(f"   {f:<10}{a:>12.3f}{b:>12.3f}{a-b:>10.3f}")
p(f"   非TP(TIME/SL) 玉 {len(ntp)}（{len(ntp)/len(g)*100:.0f}%）の net 合計 ${ntp.net.sum():.0f} / TP玉 net ${tp.net.sum():.0f}")

# N9 出口効率（mfe 捕捉・mfe_usd は最初lot基準の含み益ピーク）
gw = g[g.net > 0].copy()
gw["cap"] = gw.net / gw.mfe.replace(0, np.nan)
cap = gw["cap"].replace([np.inf, -np.inf], np.nan).dropna()
p(f"\n  N9. 出口効率（勝ち玉の実現net÷mfe・業界 0.6-0.75）")
p(f"   中央 {cap.median():.2f} / 25-75%ile [{cap.quantile(.25):.2f}, {cap.quantile(.75):.2f}]（mfe は first-lot 基準・参考）")

# N10 分離指標ランキング（TP=1 を分ける指標・相関/中央値/5分位net/両窓）
p(f"\n  N10. 分離指標ランキング（★TP(中心回帰)を分ける指標＝jm_ok/入口の候補）")
def quint_mono(s, y):
    try:
        q = pd.qcut(s, 5, duplicates="drop")
        m = y.groupby(q, observed=True).mean()
        return "単調" if (m.is_monotonic_increasing or m.is_monotonic_decreasing) else "非単調"
    except Exception:
        return "—"
rows = []
for f in feats:
    s = g[f]; y = g["is_tp"]
    if s.nunique() < 3: continue
    corr = s.corr(y)
    tpm, ntpm = tp[f].median(), ntp[f].median()
    # 両窓: train でも TP玉ほど同方向か
    st = gt[f]; yt = gt["is_tp"]
    tcorr = st.corr(yt)
    same = "両窓一致✓" if (np.sign(corr) == np.sign(tcorr) and abs(tcorr) > 0.03) else "両窓不一致✗"
    rows.append((f, corr, tpm, ntpm, quint_mono(s, y), same))
rows.sort(key=lambda r: -abs(r[1]))
for f, corr, a, b, mono, same in rows:
    p(f"   {f:<10} 相関{corr:+.3f} / TP中央{a:.3f} vs 非TP{b:.3f} / 5分位{mono} {same}")
if rows:
    p(f"   ★最強分離 = {rows[0][0]}（相関{rows[0][1]:+.3f}）→ ML 特徴量/jm_ok の核に（⛔固定値手調整禁止・L-267）")

# N11 SL(箱ブレイク)玉の方向判定
sl = g[g.exit_reason == "BOX_BREAK_SL"]
p(f"\n  N11. 箱ブレイクSL玉の方向（方向ミスか）")
p(f"   箱ブレイクSL {len(sl)}玉（{len(sl)/len(g)*100:.0f}%）/ net ${sl.net.sum():.0f} / 平均net ${sl.net.mean() if len(sl) else 0:.2f}")

# N12 勝ち場面クロス（ER × box_W＝レンジ性×箱幅）
p(f"\n  N12. 勝ち場面クロス（★ER × ADX でどの場面が TP に戻るか）")
g2 = g.dropna(subset=["er", "adx"]).copy()
g2["er_b"] = np.where(g2.er < g2.er.median(), "ER<中(レンジ)", "ER≥中(トレンド)")
g2["adx_b"] = np.where(g2.adx < g2.adx.median(), "ADX<中", "ADX≥中")
ct_net = g2.pivot_table(index="er_b", columns="adx_b", values="net", aggfunc="sum").round(0)
ct_tp = g2.pivot_table(index="er_b", columns="adx_b", values="is_tp", aggfunc="mean").round(2)
p("   [ER × ADX] 純益$\n" + ct_net.to_string())
p("   [ER × ADX] TP率\n" + ct_tp.to_string())

# N4 ドリフト（er/atr_pct/adx 学習 vs 採点）
p(f"\n  N4. 分布ドリフト（学習 vs 採点・玉単位）")
for f in ["er", "atr_pct", "adx"]:
    try:
        b = [-1e9] + list(np.nanquantile(gt[f], [.25, .5, .75])) + [1e9]
        a1 = pd.cut(gt[f], b).value_counts(normalize=True).sort_index() * 100
        a2 = pd.cut(g[f], b).value_counts(normalize=True).sort_index() * 100
        d = (a2 - a1).abs().max()
        p(f"   {f}: 最大シフト {d:.1f}pt（学習中央 {gt[f].median():.3f} / 採点中央 {g[f].median():.3f}）")
    except Exception as e:
        p(f"   {f}: —")

p("\n" + "=" * 78)
open(OUT, "w").write("\n".join(L))
print(f"\n[保存] {OUT}")
