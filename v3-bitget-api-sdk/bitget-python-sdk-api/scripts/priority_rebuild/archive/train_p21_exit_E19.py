#!/usr/bin/env python3
"""train_p21_exit_E19.py — E19: P21 Exit 値の場面別学習（CPO 型）Phase 1 = 教師生成＋oracle/最良固定/V9 実測

設計の正本: strat_v9ml_design §10.18（2026-06-12 まこさん GO）

このフェーズでやること:
  ① 地面 entry（trades_p21_E16_ground.csv）の学習期間（〜2024-12-31）各玉 × Exit 候補12組を
     前向き独立 sim → 教師 CSV（p21_exit_menu_E19_teacher.csv）
  ② oracle（玉ごと最良組の合計＝場面別の理論天井）/ 最良固定（全玉共通の最良組）/ V9 の3点を実測報告
  ③ 自己検査 = V9 組の sim が地面 CSV と (exit_time / exit_reason / net_usd) 全件完全一致

やらないこと（このフェーズ）: ML 学習・採点（oracle 報告 → まこさん確認 → 次フェーズ）。

V9 本体不変: replay_csv は import のみ。出口判定 = rc._check_exits_replay / net 計算 = rc._record_trade
（CC は net 計算に触れない・cat_requirements §8.4-2.9）。バー内の処理順は rc.run() L1214-1312 を完全踏襲
（MFE/trail 更新 → TP → SL → TRAIL → その他 Exit）。

Exit 候補メニュー（12組・§10.18 承認値）:
  P21_TRAIL_RATIO      {0.7, 0.8, 0.9(V9)}
  P21_MFE_STALE_HOLD_MIN {30, 90(V9)}   （GATE $4 固定）
  P21_TIME_EXIT_MIN    {90, 180(V9)}
  SL 2%・TP 系は不変（1変更・H16）。V9 現行組 = T0.9_S90_TE180 を必ず含む。

H 照合: H2=前向き sim（fill バーから実価格を進めるだけ・未来参照なし）・教師は学習期間 entry のみ／
H8=学習 entry ≤ 2024-12-31 assert／H15=このフェーズはラベル未生成（差額の実測のみ）／H16=1変更。
"""
from __future__ import annotations

import argparse
import math
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc            # noqa: E402  V9 リプレイ（import のみ・改造禁止）
import gen_p23_candidates as gen   # noqa: E402  OHLCV_CSV パス参照のみ

GROUND_CSV  = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p21_E16_ground.csv"
OUT_TEACHER = ROOT / "results" / "priority_rebuild" / "ratchet" / "p21_exit_menu_E19_teacher.csv"
TRAIN_END   = pd.Timestamp("2024-12-31 23:59:59")   # H8: 学習 entry はここまで

# Exit 候補メニュー（§10.18・V9 現行 = trail 0.9 / stale_hold 90 / time 180）
MENU = [
    {"trail": t, "stale_hold": s, "time": te}
    for t in (0.7, 0.8, 0.9)
    for s in (30, 90)
    for te in (90, 180)
]
V9_COMBO_ID = "T0.9_S90_TE180"


def combo_id(c: dict) -> str:
    return f"T{c['trail']}_S{c['stale_hold']}_TE{c['time']}"


def make_combo_params(base: dict, c: dict) -> dict:
    p = dict(base)
    p["P21_TRAIL_RATIO"]        = float(c["trail"])
    p["P21_MFE_STALE_HOLD_MIN"] = float(c["stale_hold"])
    p["P21_TIME_EXIT_MIN"]      = float(c["time"])
    return p


def simulate_exit(df, arrs, i_fill: int, fill_p: float, entry_ms: int,
                  tp_price: float, sl_price, cparams: dict, extra: dict):
    """1玉を fill バーから前向き sim（rc.run() のバー内処理順を完全踏襲）。戻り = trade dict / None。"""
    ts_a, cl_a, hi_a, lo_a = arrs
    gate_pct    = float(cparams.get("P21_MFE_GATE_PCT", 0.05))
    trail_ratio = float(cparams.get("P21_TRAIL_RATIO", 0.8))
    pos = {
        "side": "SHORT", "entry_priority": 21,
        "entry_price": fill_p, "entry_time": entry_ms,
        "add_count": 1, "size_btc": float(cparams.get("P21_POSITION_SIZE_BTC", 0.06)),
        "tp_price": tp_price, "sl_price": sl_price, "regime": "",
        "mfe_usd": 0.0, "mae_usd": 0.0,
        "max_high": float("-inf"), "min_low": float("inf"),
        "mfe_peak_pct": 0.0, "trail_stop_price": None,
        **extra,
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

        # rc.run() step2: MFE/MAE/極値 更新（close ベース）＋ P21 trail 追跡（low ベース）
        unreal = (ep - close_p) * sz
        if unreal > pos["mfe_usd"]:
            pos["mfe_usd"] = unreal
        if unreal < pos["mae_usd"]:
            pos["mae_usd"] = unreal
        if low_p < pos["min_low"]:
            pos["min_low"] = low_p
        fav = (ep - low_p) / ep * 100.0
        if fav > pos["mfe_peak_pct"]:
            pos["mfe_peak_pct"] = fav
            if fav >= gate_pct:
                pos["trail_stop_price"] = ep * (1.0 - fav / 100.0 * trail_ratio)

        # rc.run() step3: TP（low が tp 到達）
        if low_p <= tp_price:
            rc._record_trade(out, pos, exit_price=tp_price, exit_reason="TP_FILLED",
                             exit_ts_ms=ts_ms, params=cparams)
            return out[0]
        # rc.run() step4: SL（high が sl 到達）
        if pos["sl_price"] is not None and high_p >= float(pos["sl_price"]):
            rc._record_trade(out, pos, exit_price=float(pos["sl_price"]), exit_reason="SL_FILLED",
                             exit_ts_ms=ts_ms, params=cparams)
            return out[0]
        # rc.run() step4b: TRAIL（high が trail stop 到達）
        tsp = pos["trail_stop_price"]
        if tsp is not None and high_p >= float(tsp):
            rc._record_trade(out, pos, exit_price=float(tsp), exit_reason="TRAIL_EXIT",
                             exit_ts_ms=ts_ms, params=cparams)
            return out[0]
        # rc.run() step5: その他 Exit（V9 の判定関数そのまま・close 成行）
        reason = rc._check_exits_replay(pos, close_p, df, j, cparams, ts_ms)
        if reason:
            rc._record_trade(out, pos, exit_price=close_p, exit_reason=reason,
                             exit_ts_ms=ts_ms, params=cparams)
            return out[0]
    return None


def calc_tp_price(df, i_fill: int, fill_p: float, adx_at_entry: float, atr14: float, base: dict) -> float:
    """rc.run() L1151-1163 の P21 新規エントリー TP 計算を踏襲（メニューは TP を触らない＝全組共通）。"""
    bb_u = float(df.at[i_fill, "bb_sigma2_upper"]) if "bb_sigma2_upper" in df.columns else float("nan")
    bb_l = float(df.at[i_fill, "bb_sigma2_lower"]) if "bb_sigma2_lower" in df.columns else float("nan")
    if not (math.isnan(bb_u) or math.isnan(bb_l)):
        bb_half = (bb_u - bb_l) / 2.0
        tp_dist = max(bb_half * float(base.get("P21_TP_BB_RATIO", 1.0)),
                      fill_p * float(base.get("P21_TP_MIN_PCT", 0.0003)))
        return fill_p - tp_dist
    return rc._calc_tp_price("SHORT", fill_p, adx_at_entry, base, 21, atr_14=atr14)


def reconstruct_fill_price(df, cl_a, i_fill: int, entry_price_csv: float):
    """fill 価格の厳密復元: SHORT limit = 直前シグナルバー close × (1+0.0001)（TTL2 → 1〜2 本前）。
    CSV の entry_price は 2dp 丸めなので、丸め一致する候補から復元する。一致なしは CSV 値（許容誤差照合）。"""
    for back in (1, 2):
        j = i_fill - back
        if j < 0:
            continue
        cand = float(cl_a[j]) * (1.0 + 0.0001)
        if abs(round(cand, 2) - entry_price_csv) < 0.005:
            return cand, True
    return float(entry_price_csv), False


def phase2_oof():
    """Phase 2: 教師 CSV から (場面特徴量 ⊕ 組) → 「V9 組より得か」符号二値＋|差額|重みを purged k-fold OOF で検証。
    実行は python3.13（lightgbm）。採点期間は一切触らない。
    事前宣言の切替候補: OOF prob 最大の組が cutoff {0.5, 0.6, 0.7, 0.8} 以上なら切替（それ以外 V9 fallback）。"""
    import lightgbm as lgb                      # noqa: F401（python3.13 のみ）
    from sklearn.metrics import roc_auc_score
    from scipy.stats import spearmanr
    import train_p23_size_E13 as e13            # 特徴量基盤（E13 と同一群・import のみ）
    import train_p23_entry_E8b as e8b           # build_multiperiod / OHLCV パス
    import ratchet_guards as rg                 # 番人（vol_share 可視化）

    assert OUT_TEACHER.exists(), f"教師 CSV が無い: {OUT_TEACHER}（先に Phase 1 を実行）"
    te = pd.read_csv(OUT_TEACHER)
    print(f"[load] 教師 {len(te)} 玉 × {len(MENU)} 組")
    entry_ts = pd.to_datetime(te["entry_time"])
    assert entry_ts.max() <= TRAIN_END, "H8 違反: 教師に学習期間外の entry（停止）"

    # ---- 場面特徴量（E13 と同一群 ＋ ret1h/ret4h）----
    ohlcv = pd.read_csv(e8b.OHLCV)
    ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])
    mp  = e8b.build_multiperiod(ohlcv)
    vol = e13.build_vol_feats(ohlcv)
    Xt  = e13.make_features_e13(te["entry_time"], mp, vol, ohlcv)
    c_idx = ohlcv.set_index("timestamp")["close"].sort_index()
    for n, name in ((12, "ret1h"), (48, "ret4h")):
        r = (c_idx.pct_change(n) * 100.0)       # 過去 close のみ（H2）
        Xt[name] = r.reindex(pd.to_datetime(te["entry_time"].values)).values
    print(f"[特徴量] {Xt.shape[1]} 列（E13 同一群 + ret1h/ret4h）")

    # ---- ペア表（玉 × 11 代替組・タイ除外＝重み0は情報なし）----
    alts = [c for c in MENU if combo_id(c) != V9_COMBO_ID]
    v9net = te[f"net__{V9_COMBO_ID}"]
    plist = []
    for c in alts:
        cid = combo_id(c)
        plist.append(pd.DataFrame({
            "trade_idx": te.index.values, "combo": cid,
            "trail": float(c["trail"]), "stale_hold": float(c["stale_hold"]), "time_exit": float(c["time"]),
            "diff": (te[f"net__{cid}"] - v9net).values,
        }))
    pairs = pd.concat(plist, ignore_index=True)
    pairs = pairs[pairs["diff"].abs() > 0.01].reset_index(drop=True)
    y = (pairs["diff"] > 0).astype(int).values
    clip = float(pairs["diff"].abs().quantile(0.99))
    w = pairs["diff"].abs().clip(upper=clip).values
    print(f"[ペア] {len(pairs)} 行（タイ除外後）・勝ちペア率 {y.mean()*100:.2f}%・重み p99 クリップ ${clip:.2f}")

    Xp = Xt.iloc[pairs["trade_idx"].values].reset_index(drop=True)
    Xp = pd.concat([Xp, pairs[["trail", "stale_hold", "time_exit"]].reset_index(drop=True)], axis=1)

    # ---- purged k-fold（玉単位・purge 終端 = 全組の最長 hold）----
    hold_cols = [f"hold__{combo_id(c)}" for c in MENU]
    exit_ts = entry_ts + pd.to_timedelta(te[hold_cols].max(axis=1), unit="m")
    oof_prob = np.full(len(pairs), np.nan)
    folds = []
    for fi, (ti, vi, (v0, v1)) in enumerate(e13.purged_folds(entry_ts, exit_ts, 5)):
        tr_set, va_set = set(ti), set(vi)
        pm_tr = pairs["trade_idx"].isin(tr_set).values
        pm_va = pairs["trade_idx"].isin(va_set).values
        if pm_tr.sum() < 500 or pm_va.sum() < 100 or len(np.unique(y[pm_tr])) < 2:
            continue
        m = e13.fit_weighted(Xp[pm_tr], y[pm_tr], w[pm_tr], Xp[pm_va], y[pm_va], w[pm_va])
        p = m.predict(Xp[pm_va], num_iteration=m.best_iteration)
        oof_prob[pm_va] = p
        auc = roc_auc_score(y[pm_va], p) if len(np.unique(y[pm_va])) > 1 else float("nan")
        sp = spearmanr(p, pairs["diff"].values[pm_va])
        folds.append({"fold": fi, "val": f"{v0.date()}〜{v1.date()}", "n_pair": int(pm_va.sum()),
                      "auc": round(float(auc), 4), "spearman": round(float(sp.statistic), 4),
                      "best_iter": int(m.best_iteration)})
        print(f"[fold{fi}] val {v0.date()}〜{v1.date()} pair{pm_va.sum()} AUC={auc:.4f} "
              f"Spearman(prob,diff)={sp.statistic:+.4f} best_iter={m.best_iteration}")
    assert folds, "有効 fold 0"
    has = ~np.isnan(oof_prob)
    auc_all = roc_auc_score(y[has], oof_prob[has])
    sp_all = spearmanr(oof_prob[has], pairs["diff"].values[has])
    print(f"[OOF全体] AUC={auc_all:.4f} / Spearman(prob,diff)={sp_all.statistic:+.4f} / 充足 {has.mean()*100:.0f}%")

    # ---- OOF 方策（事前宣言 cutoff）: 玉ごと prob 最大の組・cutoff 未満は V9 fallback ----
    pr = pairs.assign(prob=oof_prob).dropna(subset=["prob"])
    best = pr.loc[pr.groupby("trade_idx")["prob"].idxmax()]
    print("\n[OOF 方策] 切替 = prob 最大の組が cutoff 以上（残り V9）・学習期間で V9 比:")
    print(f"  参考: oracle +$1,561 / 厳密勝ち玉 83/2,492（3.3%）/ 損益分岐 precision ≈10%")
    pol = []
    for q in (0.5, 0.6, 0.7, 0.8):
        sw = best[best["prob"] >= q]
        gain = float(sw["diff"].sum())
        prec = float((sw["diff"] > 0).mean()) if len(sw) else float("nan")
        pol.append({"cutoff": q, "n_switch": int(len(sw)), "precision": round(prec, 3), "oof_gain": round(gain, 1)})
        print(f"  cutoff {q}: 切替 {len(sw):>4} 玉 / precision {prec*100 if len(sw) else float('nan'):.1f}% "
              f"/ OOF 上積み ${gain:+,.1f}")

    # ---- 診断（選定でなく理解用）: fold 内 prob 順位の上位 N 玉の precision / 上積み ----
    # prob の絶対値は fold 間でスケールが揃わない（best_iter 2〜19 の浅い木）ため、fold 内百分位で順位化。
    pr_d = pairs.assign(prob=oof_prob).dropna(subset=["prob"]).copy()
    fold_of_trade = {}
    for fi, (ti, vi, _rng) in enumerate(e13.purged_folds(entry_ts, exit_ts, 5)):
        for t in vi:
            fold_of_trade[int(t)] = fi
    pr_d["fold"] = pr_d["trade_idx"].map(fold_of_trade)
    pr_d["pct_in_fold"] = pr_d.groupby("fold")["prob"].rank(pct=True)
    bd = pr_d.loc[pr_d.groupby("trade_idx")["pct_in_fold"].idxmax()]
    bd = bd.sort_values("pct_in_fold", ascending=False)
    print("\n[診断] fold 内 prob 順位の上位 N 玉（切替したと仮定した場合・選定には使わない）:")
    for nN in (25, 50, 100, 200):
        top = bd.head(nN)
        print(f"  top{nN:>3}: precision {(top['diff'] > 0).mean()*100:5.1f}% / 上積み合計 ${top['diff'].sum():+,.1f}")
    pr_d.to_csv(OUT_TEACHER.parent / "p21_exit_E19_oof_pairs.csv", index=False)

    # ---- ボラ支配チェック（H15①）＋ 重要特徴 ----
    cut = int(len(Xp) * 0.85)
    m_full = e13.fit_weighted(Xp.iloc[:cut], y[:cut], w[:cut], Xp.iloc[cut:], y[cut:], w[cut:])
    vr = rg.report_vol_importance(dict(zip(m_full.feature_name(), m_full.feature_importance("gain"))))
    imp = pd.Series(m_full.feature_importance("gain"), index=Xp.columns).sort_values(ascending=False)
    print(f"\n[ボラ寄与] vol_share={vr['vol_share']}（停止 0.5・H15①）")
    print("[重要特徴 top12]\n" + imp.head(12).to_string())

    out = {"folds": folds, "oof_auc": round(float(auc_all), 4),
           "oof_spearman": round(float(sp_all.statistic), 4), "policy": pol,
           "vol_share": vr["vol_share"],
           "top_features": {k: round(float(v), 1) for k, v in imp.head(12).to_dict().items()}}
    import json
    outp = OUT_TEACHER.parent / "p21_exit_E19_oof.json"
    outp.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"\n[出力] {outp}")
    print("→ 次: OOF 結果をまこさんに報告 → 採点に進むか・メニューを閉じるか判断")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="自己検査400件＋教師300件のみ・ファイル出力なし")
    ap.add_argument("--oof", action="store_true", help="Phase 2: OOF 学習（要 python3.13・教師 CSV 必須）")
    args = ap.parse_args()
    if args.oof:
        phase2_oof()
        return

    base = rc._load_params()
    assert float(base.get("P21_TRAIL_RATIO")) == 0.9 and float(base.get("P21_MFE_STALE_HOLD_MIN")) == 90.0 \
        and float(base.get("P21_TIME_EXIT_MIN")) == 180.0, "V9 現行値が想定と不一致（メニューの V9 組を見直すこと・停止）"

    print(f"[load] OHLCV preload: {gen.OHLCV_CSV.name}")
    df, _df_raw = rc.preload(str(gen.OHLCV_CSV), base)
    ts_a = df["timestamp_ms"].to_numpy(dtype=np.int64)
    cl_a = df["close"].to_numpy(dtype=float)
    hi_a = df["high_raw"].to_numpy(dtype=float)
    lo_a = df["low_raw"].to_numpy(dtype=float)
    arrs = (ts_a, cl_a, hi_a, lo_a)
    idx_of_ts = {int(t): i for i, t in enumerate(ts_a)}

    g = pd.read_csv(GROUND_CSV)
    assert set(g["priority"].astype(int)) == {21} and set(g["side"]) == {"SHORT"}, "地面 CSV が P21 SHORT 単独でない（停止）"
    g["entry_ts"] = pd.to_datetime(g["entry_time"])
    g = g.sort_values("entry_ts").reset_index(drop=True)
    print(f"[load] 地面 {len(g)} 件（全期間）")

    # ---- 各玉の固定要素（fill バー index / fill 価格 / TP / SL）を準備 ----
    prep = []
    n_exact = 0
    for r in g.itertuples():
        ems = int(pd.Timestamp(r.entry_time).value // 10**6)
        i_fill = idx_of_ts.get(ems)
        assert i_fill is not None, f"entry_time が OHLCV に見つからない: {r.entry_time}（停止）"
        fill_p, exact = reconstruct_fill_price(df, cl_a, i_fill, float(r.entry_price))
        n_exact += int(exact)
        tp = calc_tp_price(df, i_fill, fill_p, float(r.adx_at_entry), float(r.atr_14), base)
        sl = rc._calc_sl_price("SHORT", fill_p, base, 21)
        extra = {
            "adx_at_entry": r.adx_at_entry, "bb_mid_slope_at_entry": r.bb_mid_slope_at_entry,
            "rsi_at_entry": r.rsi_at_entry, "rsi_slope_at_entry": r.rsi_slope_at_entry,
            "stoch_k_at_entry": r.stoch_k_at_entry, "stoch_d_at_entry": r.stoch_d_at_entry,
            "bb_width_at_entry": r.bb_width_at_entry, "ret_5": r.ret_5, "atr_14": r.atr_14,
            "entry_hour": r.entry_hour, "entry_weekday": r.entry_weekday,
        }
        prep.append((ems, i_fill, fill_p, tp, sl, extra, r))
    print(f"[fill 復元] 厳密復元 {n_exact}/{len(g)} 件（残りは CSV 2dp 値・許容誤差で照合）")

    # ---- 自己検査: V9 組の sim が地面 CSV と完全一致 ----
    chk = prep[:400] if args.smoke else prep
    v9p = make_combo_params(base, {"trail": 0.9, "stale_hold": 90, "time": 180})
    n_ng = 0
    for ems, i_fill, fill_p, tp, sl, extra, r in chk:
        t = simulate_exit(df, arrs, i_fill, fill_p, ems, tp, sl, v9p, extra)
        ok = (t is not None and t["exit_time"] == r.exit_time and t["exit_reason"] == r.exit_reason
              and abs(float(t["net_usd"]) - float(r.net_usd)) <= 0.01)
        if not ok:
            n_ng += 1
            if n_ng <= 5:
                print(f"  [不一致] {r.entry_time}: sim={None if t is None else (t['exit_time'], t['exit_reason'], t['net_usd'])} "
                      f"vs 地面=({r.exit_time}, {r.exit_reason}, {r.net_usd})")
    assert n_ng == 0, f"自己検査 FAIL: {n_ng}/{len(chk)} 件不一致（移植ミス・停止）"
    print(f"[自己検査] ✅ V9 組 sim = 地面 CSV 完全一致（{len(chk)} 件・exit_time/exit_reason/net ≤$0.01）")

    # ---- 教師生成（学習期間のみ・12組）----
    train = [p for p in prep if pd.Timestamp(p[6].entry_time) <= TRAIN_END]
    assert all(pd.Timestamp(p[6].entry_time) <= TRAIN_END for p in train), "H8 違反（停止）"
    if args.smoke:
        train = train[:300]
    print(f"[教師] 学習期間 entry {len(train)} 件 × {len(MENU)} 組 を前向き sim ...")

    rows = []
    for ems, i_fill, fill_p, tp, sl, extra, r in train:
        row = {
            "entry_time": r.entry_time, "entry_price": fill_p,
            "adx_at_entry": r.adx_at_entry, "bb_mid_slope_at_entry": r.bb_mid_slope_at_entry,
            "rsi_at_entry": r.rsi_at_entry, "rsi_slope_at_entry": r.rsi_slope_at_entry,
            "stoch_k_at_entry": r.stoch_k_at_entry, "stoch_d_at_entry": r.stoch_d_at_entry,
            "bb_width_at_entry": r.bb_width_at_entry, "ret_5": r.ret_5, "atr_14": r.atr_14,
            "entry_hour": r.entry_hour, "entry_weekday": r.entry_weekday,
        }
        for c in MENU:
            cid = combo_id(c)
            t = simulate_exit(df, arrs, i_fill, fill_p, ems, tp, sl, make_combo_params(base, c), extra)
            row[f"net__{cid}"]    = float("nan") if t is None else float(t["net_usd"])
            row[f"reason__{cid}"] = "" if t is None else t["exit_reason"]
            row[f"hold__{cid}"]   = float("nan") if t is None else float(t["hold_min"])
        rows.append(row)
    te = pd.DataFrame(rows)
    n_open = int(te[[f"net__{combo_id(c)}" for c in MENU]].isna().any(axis=1).sum())
    assert n_open == 0, f"未決済 sim {n_open} 件（データ末尾・想定外）"

    # ---- oracle / 最良固定 / V9 の3点（学習期間）----
    net_cols = {combo_id(c): f"net__{combo_id(c)}" for c in MENU}
    totals = {cid: te[col].sum() for cid, col in net_cols.items()}
    v9_total = totals[V9_COMBO_ID]
    best_fixed_id = max(totals, key=totals.get)
    oracle_series = te[list(net_cols.values())].max(axis=1)
    oracle_pick   = te[list(net_cols.values())].idxmax(axis=1).str.replace("net__", "", regex=False)
    print("\n========== E19 Phase1 実測（学習期間・サイズ 0.06 固定） ==========")
    print(f"  玉数: {len(te)}")
    print(f"  V9 組      ({V9_COMBO_ID}): ${v9_total:,.1f}")
    print(f"  最良固定   ({best_fixed_id}): ${totals[best_fixed_id]:,.1f}  （V9 比 {totals[best_fixed_id]-v9_total:+,.1f}）")
    print(f"  oracle（玉ごと最良・場面別の理論天井）: ${oracle_series.sum():,.1f}  （V9 比 {oracle_series.sum()-v9_total:+,.1f}）")
    print("\n  組別合計（全12組）:")
    for cid, tv in sorted(totals.items(), key=lambda x: -x[1]):
        mark = " ←V9" if cid == V9_COMBO_ID else (" ←最良固定" if cid == best_fixed_id else "")
        print(f"    {cid:<18} ${tv:>10,.1f}{mark}")
    print("\n  oracle の組選択分布（場面別性の有無）:")
    for cid, cnt in oracle_pick.value_counts().items():
        print(f"    {cid:<18} {cnt:>5} 玉 ({cnt/len(te)*100:.1f}%)")
    # 年別（V9 / 最良固定 / oracle）
    yr = pd.to_datetime(te["entry_time"]).dt.year
    print("\n  年別（V9 / 最良固定 / oracle）:")
    for y in sorted(yr.unique()):
        m = yr == y
        print(f"    {y}: V9 ${te.loc[m, net_cols[V9_COMBO_ID]].sum():>8,.1f} / "
              f"固定 ${te.loc[m, net_cols[best_fixed_id]].sum():>8,.1f} / "
              f"oracle ${oracle_series[m].sum():>8,.1f}")

    if not args.smoke:
        OUT_TEACHER.parent.mkdir(parents=True, exist_ok=True)
        te.to_csv(OUT_TEACHER, index=False)
        print(f"\n[出力] {OUT_TEACHER}（{len(te)} 行 × 12組）")
    print("\n→ 次: oracle/最良固定の数字をまこさんに報告 → OOF 学習（Phase 2）へ進むか判断")


if __name__ == "__main__":
    main()
