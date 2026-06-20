#!/usr/bin/env python3
"""p4_oracle_E23.py — P4 LONG: Exit 値の場面別調整（CPO型）の oracle 天井測定 ＋ OOF 学習検証（E23・採点なし・学習期間のみ）

目的: 「値の場面別調整（§6.2）」が P4 で net をいくら生めるかを、採点前に2段の関所で測る（E19 と同じプロセス）:
  Phase 1（本体・python3 可）: add1 玉（学習期間）× Exit 値候補の前向き独立 sim → oracle 天井・切替対象の厚み。
    E19 は P21 でここが「3.3% の希少玉」と判明し学習に進まず閉じた。P4 で薄ければ同様に閉じる（採点温存）。
  Phase 2（--oof・python3.13=lightgbm）: 場面特徴量 → 切替得の学習が OOF で立つか（ML 場面別学習・玉単位 purged fold）。
- 候補値はデータ分位から導出（手置きしない）: TP = 学習期間 TP玉 MFE% の 75/90 分位 + V9動的 ／
  TIME = 学習期間 TP玉 保有の 50/75/90 分位 + V9 150 分。ML が場面ごとに選ぶ離散アクションメニュー。
- V9 本体不変: replay_csv は import のみ。出口判定 = rc._check_exits_replay / net 計算 = rc._record_trade（自作 net なし）。
- 自己検査: V9 組（TP=動的・TIME=150）の sim が地面 CSV の add1 玉と (exit_reason/net) 一致。
"""
from __future__ import annotations
import math
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                      # noqa: E402
import gen_p23_candidates as gen             # noqa: E402
from preload_cache import cached_preload     # noqa: E402

GROUND = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p4_E22_ground.csv"
OUT    = ROOT / "results" / "priority_rebuild" / "ratchet" / "p4_oracle_E23_teacher.csv"
TRAIN_END = pd.Timestamp("2025-01-01")

# ML が場面ごとに選ぶ離散アクションメニュー（lightgbm Phase 2 の行動空間・値はデータ分位由来）
TP_CANDS   = [None, 0.00685, 0.00887]        # None = V9 動的 TP（base0.5%×ADXクランプ）
TIME_CANDS = [20.0, 40.0, 65.0, 150.0]       # 150 = V9 現行
COMBOS = [(tp, tm) for tp in TP_CANDS for tm in TIME_CANDS]
V9_KEY = "net_tpV9_tm150"


def combo_key(tp, tm) -> str:
    return f"net_tp{'V9' if tp is None else tp}_tm{int(tm)}"


def simulate_p4(df, arrs, i_fill: int, fill_p: float,
                adx_at_entry: float, atr14: float, base_params: dict,
                tp_override, time_exit_min: float):
    """add1 の P4 玉を fill バーから前向き sim（rc.run() のバー内処理順を踏襲・LONG）。"""
    ts_a, cl_a, hi_a, lo_a = arrs
    cparams = dict(base_params)
    cparams["P4_TIME_EXIT_MIN"] = float(time_exit_min)   # _check_exits_replay が P{pri}_TIME_EXIT_MIN を優先参照
    if tp_override is None:
        tp_price = rc._calc_tp_price("LONG", fill_p, adx_at_entry, cparams, 4, atr_14=atr14)
    else:
        tp_price = fill_p * (1.0 + float(tp_override))
    sl_price = rc._calc_sl_price("LONG", fill_p, cparams, 4)
    pos = {
        "side": "LONG", "entry_priority": 4,
        "entry_price": fill_p, "entry_time": int(ts_a[i_fill]),
        "add_count": 1, "size_btc": float(cparams.get("LONG_POSITION_SIZE_BTC", 0.024)),
        "tp_price": tp_price, "sl_price": sl_price, "regime": "",
        "mfe_usd": 0.0, "mae_usd": 0.0,
        "max_high": float("-inf"), "min_low": float("inf"),
        "mfe_peak_pct": 0.0, "trail_stop_price": None,
    }
    out: list = []
    n = len(df)
    ep = fill_p
    sz = pos["size_btc"]
    for j in range(i_fill, n):
        ts_ms   = int(ts_a[j])
        close_p = float(cl_a[j])
        high_p  = float(hi_a[j])
        low_p   = float(lo_a[j])

        unreal = (close_p - ep) * sz
        if unreal > pos["mfe_usd"]:
            pos["mfe_usd"] = unreal
        if unreal < pos["mae_usd"]:
            pos["mae_usd"] = unreal
        if high_p > pos["max_high"]:
            pos["max_high"] = high_p

        # TP（high が tp 到達・指値 maker）
        if high_p >= tp_price:
            rc._record_trade(out, pos, exit_price=tp_price, exit_reason="TP_FILLED",
                             exit_ts_ms=ts_ms, params=cparams)
            return out[0]
        # SL（low が sl 到達・指値）
        if pos["sl_price"] is not None and low_p <= float(pos["sl_price"]):
            rc._record_trade(out, pos, exit_price=float(pos["sl_price"]), exit_reason="SL_FILLED",
                             exit_ts_ms=ts_ms, params=cparams)
            return out[0]
        # その他 Exit（PROFIT_LOCK / TIME_EXIT 等・V9 判定関数そのまま・close 成行）
        reason = rc._check_exits_replay(pos, close_p, df, j, cparams, ts_ms)
        if reason:
            rc._record_trade(out, pos, exit_price=close_p, exit_reason=reason,
                             exit_ts_ms=ts_ms, params=cparams)
            return out[0]
    return None


def reconstruct_fill(cl_a, i_fill: int, entry_price_csv: float):
    """LONG limit = シグナルバー close×(1−0.0001)。TTL2 → fill の 1〜2 本前から復元（CSV は 2dp 丸め）。"""
    for back in (1, 2):
        j = i_fill - back
        if j < 0:
            continue
        cand = float(cl_a[j]) * (1.0 - 0.0001)
        if abs(round(cand, 2) - entry_price_csv) < 0.005:
            return cand, True
    return float(entry_price_csv), False


def phase1():
    g = pd.read_csv(GROUND, parse_dates=["entry_time", "exit_time"])
    g = g[(g.add_count == 1) & (g.entry_time < TRAIN_END)].reset_index(drop=True)
    print(f"[対象] 学習期間 add1 玉: {len(g)}件 / CSV net {g.net_usd.sum():.1f}")

    params = rc._load_params()
    df, _raw = cached_preload(str(gen.OHLCV_CSV), params)
    ts_a = df["timestamp_ms"].to_numpy()
    cl_a = df["close"].to_numpy()
    hi_a = df["high_raw"].to_numpy()
    lo_a = df["low_raw"].to_numpy()
    arrs = (ts_a, cl_a, hi_a, lo_a)
    ts_index = pd.Series(range(len(df)), index=pd.to_datetime(df["timestamp_ms"], unit="ms"))

    rows = []
    n_fill_exact = 0
    for _, t in g.iterrows():
        et = t.entry_time
        if et not in ts_index.index:
            continue
        i_fill = int(ts_index.loc[et])
        fill_p, exact = reconstruct_fill(cl_a, i_fill, float(t.entry_price))
        n_fill_exact += int(exact)
        row = {"entry_time": et, "csv_net": float(t.net_usd), "csv_reason": t.exit_reason,
               "fill_exact": exact,
               "adx": float(t.adx_at_entry), "atr_14": float(t.atr_14),
               "slope": float(t.bb_mid_slope_at_entry), "rsi": float(t.rsi_at_entry),
               "ret_5": float(t.ret_5), "stoch_k": float(t.stoch_k_at_entry),
               "bb_width": float(t.bb_width_at_entry), "entry_price": float(t.entry_price)}
        for tp, tm in COMBOS:
            tr = simulate_p4(df, arrs, i_fill, fill_p, float(t.adx_at_entry), float(t.atr_14),
                             params, tp, tm)
            row[combo_key(tp, tm)] = float(tr["net_usd"]) if tr is not None else float("nan")
            if tp is None and tm == 150.0 and tr is not None:
                row["v9_reason"] = tr["exit_reason"]
        rows.append(row)

    d = pd.DataFrame(rows)
    print(f"[fill 復元] 厳密 {n_fill_exact}/{len(d)}")

    # ---- 自己検査: V9 組 = 地面 CSV と一致 ----
    diff = (d[V9_KEY] - d.csv_net).abs()
    n_match = int((diff < 0.01).sum())
    reason_match = int((d.v9_reason == d.csv_reason).sum())
    print(f"[自己検査] V9 組 sim vs 地面 CSV: net 一致($0.01) {n_match}/{len(d)} / reason 一致 {reason_match}/{len(d)}")
    if n_match < len(d):
        bad = d[diff >= 0.01]
        print(bad[["entry_time", "csv_net", V9_KEY, "csv_reason", "v9_reason"]].head(10).to_string())

    # ---- oracle B 集計 ----
    netcols = [c for c in d.columns if c.startswith("net_")]
    d["oracle_net"] = d[netcols].max(axis=1)
    d["oracle_combo"] = d[netcols].idxmax(axis=1)
    d["year"] = d.entry_time.dt.year
    v9_total = d[V9_KEY].sum()
    print("\n=== 各組 固定適用の net（学習期間 add1・参考＝固定では使わない）===")
    print(d[netcols].sum().round(0).sort_values(ascending=False).to_string())
    print(f"\n=== oracle B（玉ごと最良・天井）===")
    print(f"V9 固定 {v9_total:.0f} → oracle {d.oracle_net.sum():.0f}（+{d.oracle_net.sum()-v9_total:.0f}）")
    print("年別 oracle 増分:")
    print((d.groupby('year').oracle_net.sum() - d.groupby('year')[V9_KEY].sum()).round(0).to_string())
    gain = d[d.oracle_net > d[V9_KEY] + 0.01]
    print(f"\n切替で得する玉: {len(gain)}/{len(d)}件（{len(gain)/len(d)*100:.1f}%）/ 増分合計 +{(gain.oracle_net-gain[V9_KEY]).sum():.0f}")
    print(gain.oracle_combo.value_counts().to_string())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT, index=False)
    print(f"\n[出力] {OUT}")


def phase2_oof():
    """Phase 2（python3.13）: 場面特徴量 → 「V9 組より得な組があるか」を lightgbm で OOF 検証（玉単位 5fold）。
    oracle（Phase 1）が立った場合のみ実行。組ごと差額二値（E19 流）・重み=|差額| p99・cutoff は実行前宣言 {0.6,0.7,0.8}。"""
    import numpy as np
    import lightgbm as lgb
    from sklearn.metrics import roc_auc_score
    d = pd.read_csv(OUT, parse_dates=["entry_time"])
    netcols = [c for c in d.columns if c.startswith("net_") and c != V9_KEY]
    feats = ["adx", "rsi", "ret_5", "stoch_k", "bb_width"]
    d["slope_pct"] = d.slope / d.entry_price * 100
    d["atr_pct"] = d.atr_14 / d.entry_price * 100
    feats += ["slope_pct", "atr_pct"]
    rows = []
    for c in netcols:
        sub = d[["entry_time"] + feats + [V9_KEY, c]].dropna().copy()
        sub["combo"] = c
        sub["diff"] = sub[c] - sub[V9_KEY]
        rows.append(sub.rename(columns={c: "net_combo"}))
    t = pd.concat(rows, ignore_index=True)
    t["y"] = (t["diff"] > 0).astype(int)
    t["w"] = t["diff"].abs().clip(upper=t["diff"].abs().quantile(0.99))
    t["combo_id"] = t.combo.astype("category").cat.codes
    X = t[feats + ["combo_id"]]
    # 玉単位 fold（同一玉の全組は同じ fold・時系列順）
    balls = t.entry_time.drop_duplicates().sort_values().reset_index(drop=True)
    fold_of = {et: int(i * 5 / len(balls)) for i, et in enumerate(balls)}
    t["fold"] = t.entry_time.map(fold_of)
    oof = pd.Series(index=t.index, dtype=float)
    for f in range(5):
        tr_i, te_i = t.fold != f, t.fold == f
        m = lgb.LGBMClassifier(n_estimators=300, num_leaves=15, min_child_samples=50,
                               learning_rate=0.05, random_state=42, verbose=-1)
        m.fit(X[tr_i], t.y[tr_i], sample_weight=t.w[tr_i])
        oof[te_i] = m.predict_proba(X[te_i])[:, 1]
    t["prob"] = oof
    auc = roc_auc_score(t.y, t.prob, sample_weight=t.w)
    print(f"[OOF] 加重 AUC = {auc:.4f} / 切替得 base rate = {t.y.mean():.3f}")
    for cutoff in (0.6, 0.7, 0.8):
        # 玉ごと: prob 最大の組が cutoff 超なら切替、それ以外 V9
        pick = t.loc[t.groupby("entry_time").prob.idxmax()]
        sw = pick[pick.prob >= cutoff]
        total = d[V9_KEY].sum() + (sw.net_combo - sw[V9_KEY]).sum()
        print(f"  cutoff {cutoff}: 切替 {len(sw)}玉 / OOF 適用後 net {total:.0f}（V9 {d[V9_KEY].sum():.0f}）")


if __name__ == "__main__":
    if "--oof" in sys.argv:
        phase2_oof()
    else:
        phase1()
