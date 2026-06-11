#!/usr/bin/env python3
"""train_p21_entry_E21.py — E21: P21 Entry 判定そのものを ML に置き換える（型だけ残す・固い閾値を全部外す）

設計（まこさん GO 2026-06-12・固定値調整禁止の下で）:
  - 型（残す）= MACD デッドクロス（i-1 で macd≥signal かつ i で macd<signal・cat_v9_decider.py L556-569 原本）。
    ⚠️ P21 の型は MACD（stoch ではない・原本確認 2026-06-12）。ADX_MIN=0（実質無効）・束縛は ATR14≥150 のみ。
  - 外す（木に渡す）= ATR 床ほか固い閾値。木が場面（指標生値×MTF×文脈）から「入って正味プラスか」の
    切れ目を学習する（§10.17 方針0 の P21 適用・手置きの床・グリッドは作らない）。
  - 入る条件 = 較正済み prob > 0.5（= 期待 net プラスの定義・手置き値ではない）。
  - Exit / サイズ 0.06 / add なし = V9 のまま（H16 1変更）。

Phase 1（本スクリプト・--teacher）: 候補生成＋教師 sim＋実測サマリ（学習期間・採点なし）
  - 候補 = 全 MACD デッドクロスバー（型のみ・閾値なし）。
  - 約定モデル = V9 と同一（SHORT limit=close×1.0001・fill は翌バー high≥limit・不成立は取引なし）。
  - 出口 = train_p21_exit_E19.simulate_exit（V9 P21 Exit・地面 4,175 件完全一致 実証済）。
  - ラベル net = 審判（score.py）と同じ手数料式（entry maker / exit TP・SL・TRAIL=maker / 能動=taker+slip・
    funding は短時間保有で微小につき除外）。自己検査=この式で地面 CSV を再計算し score.py の
    採点期間 $2,697.32・学習期間 $9,676.61 と一致（funding 分の誤差 $1 以内）。
  - サマリ = V9 通過集団 vs 見送り集団（ATR<150 等）の件数・net 合計・年別（新計器でどちらに取り分があるか）。

H 照合: H2=型判定・特徴量とも t 時点確定値のみ・教師 sim は前向き／H6=判定は生値を木に渡す（USD 床を
門番にしない）／H8=教師は学習期間 entry のみ（サマリも学習期間のみ・採点期間に触れない）／
H15=ラベル=net 符号・金額は重み（Phase 2）／H16=1変更（Entry 判定のみ）。
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from decimal import Decimal

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                # noqa: E402  V9 リプレイ（import のみ・改造禁止）
import gen_p23_candidates as gen       # noqa: E402  OHLCV_CSV パス参照のみ
import eval_engine as ee               # noqa: E402  確定コスト定数（審判と同じ計器・改造禁止）
import train_p21_exit_E19 as e19       # noqa: E402  simulate_exit / calc_tp_price（自己検査済）

GROUND_CSV  = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p21_E16_ground.csv"
OUT_TEACHER = ROOT / "results" / "priority_rebuild" / "ratchet" / "p21_entry_E21_teacher.csv"
TRAIN_END   = pd.Timestamp("2024-12-31 23:59:59")   # H8
MAKER_EXIT_REASONS = {"TP_FILLED", "SL_FILLED", "TRAIL_EXIT"}   # score.py L39 と同一（E0.4 後）


def judge_net(side_dir: int, ep: float, xp: float, size: float, reason: str) -> float:
    """score.py L116-123 と同じ式（funding 除く・短時間保有で微小）。ラベル用。最終判定は score.py が正。"""
    gross = (xp - ep) * size * side_dir
    entry_fee = ep * size * ee.MAKER_FEE
    is_taker = reason not in MAKER_EXIT_REASONS
    exit_fee = xp * size * (ee.TAKER_FEE if is_taker else ee.MAKER_FEE)
    slip = (xp * size * ee.SLIPPAGE) if is_taker else 0.0
    return gross - entry_fee - exit_fee - slip


def find_type_bars(df: pd.DataFrame) -> np.ndarray:
    """MACD デッドクロスバー（cat_v9_decider.py L557-564 の型条件のみ・閾値なし）。"""
    macd = df["macd"].to_numpy(dtype=float)
    msig = df["macd_signal"].to_numpy(dtype=float)
    prev_ge = np.roll(macd >= msig, 1)
    cross = (macd < msig) & prev_ge
    ok = ~(np.isnan(macd) | np.isnan(msig) | np.isnan(np.roll(macd, 1)) | np.isnan(np.roll(msig, 1)))
    cross &= ok
    cross[: rc.CANDLE_WARMUP] = False
    return np.where(cross)[0]


def phase2_oof():
    """Phase 2: 教師 CSV から 場面特徴量 → 「入って net>0 か」符号二値＋|net|重みを purged k-fold OOF で検証。
    実行は python3.13（lightgbm）。採点期間は一切触らない。
    事前宣言の運用: prob > 0.5 で入る（手置き θ なし・|net| 重み付き二値で「期待 net プラス」の定義）。
    停止条件: 較正（prob 分位 × 実 net）が壊れている／vol_share ≥ 0.5（H15①）なら採点に進まず報告して停止。"""
    import lightgbm as lgb                      # noqa: F401（python3.13 のみ）
    from sklearn.metrics import roc_auc_score
    from scipy.stats import spearmanr
    import train_p23_size_E13 as e13            # 特徴量基盤（E13 と同一群・import のみ）
    import train_p23_entry_E8b as e8b           # build_multiperiod / OHLCV パス
    import ratchet_guards as rg                 # 番人（vol_share 可視化）

    assert OUT_TEACHER.exists(), f"教師 CSV が無い: {OUT_TEACHER}（先に Phase 1 を実行）"
    te = pd.read_csv(OUT_TEACHER)
    entry_ts = pd.to_datetime(te["entry_time"])
    assert entry_ts.max() <= TRAIN_END, "H8 違反: 教師に学習期間外の entry（停止）"
    print(f"[load] 教師 {len(te)} 玉（V9 通過 {int(te['v9_pass'].sum())} / 見送り {int((~te['v9_pass']).sum())}）")

    # ---- 場面特徴量（E13 と同一群 ＋ ret1h/ret4h・E19 phase2 と同じ流儀）----
    ohlcv = pd.read_csv(e8b.OHLCV)
    ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])
    mp = e8b.build_multiperiod(ohlcv)
    vol = e13.build_vol_feats(ohlcv)
    # ⚠️ leak 修正（2026-06-12）: 特徴量は entry_time（fill バー j＝close が決定時点で未来）でなく
    #    sig_time（シグナルバー i＝注文を出す時点で閉じた足）で引く。fill バー基準は類型 A（look-ahead）。
    Xt = e13.make_features_e13(te["sig_time"], mp, vol, ohlcv)
    c_idx = ohlcv.set_index("timestamp")["close"].sort_index()
    for nb, name in ((12, "ret1h"), (48, "ret4h")):
        r = (c_idx.pct_change(nb) * 100.0)      # 過去 close のみ（H2）
        Xt[name] = r.reindex(pd.to_datetime(te["sig_time"].values)).values
    print(f"[特徴量] {Xt.shape[1]} 列（E13 同一群 + ret1h/ret4h・sig_time 基準＝シグナルバー確定値）")

    # ---- ラベル・重み（E12/E13 の型: 符号ラベル・金額は重み・H15）----
    net = te["net_judge"].to_numpy(dtype=float)
    y = (net > 0).astype(int)
    clip = float(np.quantile(np.abs(net), 0.99))
    w = np.minimum(np.abs(net), clip)
    print(f"[ラベル] 件数勝率 {y.mean()*100:.1f}%・重み p99 クリップ ${clip:.2f}"
          f"（重み付き勝ちマス {w[y == 1].sum() / w.sum() * 100:.1f}%）")

    # ---- purged k-fold（玉単位・E19 と同じ）----
    exit_ts = entry_ts + pd.to_timedelta(te["hold_min"], unit="m")
    oof = np.full(len(te), np.nan)
    folds = []
    for fi, (ti, vi, (v0, v1)) in enumerate(e13.purged_folds(entry_ts, exit_ts, 5)):
        if len(ti) < 500 or len(vi) < 100 or len(np.unique(y[ti])) < 2:
            continue
        m = e13.fit_weighted(Xt.iloc[ti], y[ti], w[ti], Xt.iloc[vi], y[vi], w[vi])
        p = m.predict(Xt.iloc[vi], num_iteration=m.best_iteration)
        oof[vi] = p
        auc = roc_auc_score(y[vi], p) if len(np.unique(y[vi])) > 1 else float("nan")
        sp = spearmanr(p, net[vi])
        folds.append({"fold": fi, "val": f"{v0.date()}〜{v1.date()}", "n": int(len(vi)),
                      "auc": round(float(auc), 4), "spearman": round(float(sp.statistic), 4),
                      "best_iter": int(m.best_iteration)})
        print(f"[fold{fi}] val {v0.date()}〜{v1.date()} n{len(vi)} AUC={auc:.4f} "
              f"Spearman(prob,net)={sp.statistic:+.4f} best_iter={m.best_iteration}")
    assert folds, "有効 fold 0"
    has = ~np.isnan(oof)
    auc_all = roc_auc_score(y[has], oof[has])
    sp_all = spearmanr(oof[has], net[has])
    print(f"[OOF全体] AUC={auc_all:.4f} / Spearman(prob,net)={sp_all.statistic:+.4f} / 充足 {has.mean()*100:.0f}%")

    # ---- 較正（prob 10分位 × 実 net・壊れていたら停止）----
    d = pd.DataFrame({"prob": oof[has], "net": net[has], "win": y[has],
                      "year": pd.to_datetime(te["sig_time"]).dt.year.to_numpy()[has],
                      "v9": te["v9_pass"].to_numpy()[has]})
    d["dec"] = pd.qcut(d["prob"], 10, labels=False, duplicates="drop")
    cal = d.groupby("dec").agg(n=("net", "size"), prob_min=("prob", "min"), win=("win", "mean"),
                               avg_net=("net", "mean"), sum_net=("net", "sum"))
    print("\n[較正] OOF prob 10分位 × 実net（avg_net が分位とともに上がるか）:")
    print(cal.round(3).to_string())

    # ---- OOF 方策（事前宣言: prob>0.5 で入る）・V9 床との比較・年別 ----
    take = d[d["prob"] > 0.5]
    v9t = d[d["v9"]]
    print(f"\n[OOF 方策] prob>0.5: 採用 {len(take)} 玉 / net ${take['net'].sum():,.1f}"
          f" ／ V9 床(同集合): {len(v9t)} 玉 / ${v9t['net'].sum():,.1f}"
          f" ／ 全玉: {len(d)} 玉 / ${d['net'].sum():,.1f}")
    print("  年別（ML 方策 / V9 床）:")
    for yy in sorted(d["year"].unique()):
        a = take[take["year"] == yy]
        b = v9t[v9t["year"] == yy]
        print(f"    {yy}: ML {len(a):>5}件 ${a['net'].sum():>9,.1f} / V9 {len(b):>5}件 ${b['net'].sum():>9,.1f}")
    drop_v9 = d[d["v9"] & (d["prob"] <= 0.5)]
    add_new = d[~d["v9"] & (d["prob"] > 0.5)]
    print(f"  入替の中身: V9 玉を落とした {len(drop_v9)} 玉（net ${drop_v9['net'].sum():,.1f} を放棄）"
          f" / 見送り玉を拾った {len(add_new)} 玉（net ${add_new['net'].sum():,.1f}）")

    # ---- ボラ支配チェック（H15①）＋ 重要特徴 ----
    cut = int(len(Xt) * 0.85)
    m_full = e13.fit_weighted(Xt.iloc[:cut], y[:cut], w[:cut], Xt.iloc[cut:], y[cut:], w[cut:])
    vr = rg.report_vol_importance(dict(zip(m_full.feature_name(), m_full.feature_importance("gain"))))
    imp = pd.Series(m_full.feature_importance("gain"), index=Xt.columns).sort_values(ascending=False)
    print(f"\n[ボラ寄与] vol_share={vr['vol_share']}（停止 0.5・H15①）")
    print("[重要特徴 top12]\n" + imp.head(12).to_string())

    # ---- 出力（OOF prob は後段の連続モード wrapper 検証で使う）----
    import json
    oof_csv = OUT_TEACHER.parent / "p21_entry_E21_oof.csv"
    pd.DataFrame({"bar_i": te["bar_i"], "entry_time": te["entry_time"], "prob": oof,
                  "net_judge": net, "v9_pass": te["v9_pass"]}).to_csv(oof_csv, index=False)
    out = {"folds": folds, "oof_auc": round(float(auc_all), 4),
           "oof_spearman": round(float(sp_all.statistic), 4),
           "calibration": json.loads(cal.round(4).to_json(orient="index")),
           "policy_take": {"n": int(len(take)), "net": round(float(take["net"].sum()), 1)},
           "vol_share": vr["vol_share"],
           "top_features": {k: round(float(v), 1) for k, v in imp.head(12).to_dict().items()}}
    outp = OUT_TEACHER.parent / "p21_entry_E21_oof.json"
    outp.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"\n[出力] {oof_csv}\n[出力] {outp}")
    print("→ 次: OOF 結果をまこさんに報告 → 較正/vol_share が健全なら連続モード wrapper×年別（2024 非劣化）→ 採点1回")


def phase3_score():
    """Phase 3: 本番採点（1回・まこさん GO 2026-06-12）＋対照実験（予測逆転・源泉検証）。
    学習＝教師（学習期間のみ）全体・時系列85/15で early stopping → 採点期間（2025-04〜12）の
    型バーに prob 適用 → prob>0.5 のみ entry（検証済み連続モード wrapper）→ trades CSV。
    正式判定は score.py（このスクリプトは CSV を出すだけ）。実行は python3.13（lightgbm）。"""
    import lightgbm as lgb                      # noqa: F401（python3.13 のみ）
    import train_p23_size_E13 as e13
    import train_p23_entry_E8b as e8b
    import measure_p21_mlgate_E21 as mw         # 連続モード wrapper（自己検査2本 済）

    score_start = pd.Timestamp("2025-04-01")
    score_end = pd.Timestamp("2025-12-31 23:59:59")
    out_csv = OUT_TEACHER.parent / "trades_p21_E21_mlgate.csv"

    te = pd.read_csv(OUT_TEACHER)
    assert pd.to_datetime(te["entry_time"]).max() <= TRAIN_END, "H8 違反: 教師に学習期間外（停止）"

    # ---- 特徴量（OOF と同一・sig_time 基準）----
    ohlcv = pd.read_csv(e8b.OHLCV)
    ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])
    mp = e8b.build_multiperiod(ohlcv)
    vol = e13.build_vol_feats(ohlcv)
    c_idx = ohlcv.set_index("timestamp")["close"].sort_index()

    def feats(times: pd.Series) -> pd.DataFrame:
        X = e13.make_features_e13(times, mp, vol, ohlcv)
        for nb, name in ((12, "ret1h"), (48, "ret4h")):
            X[name] = (c_idx.pct_change(nb) * 100.0).reindex(pd.to_datetime(times.values)).values
        return X

    Xt = feats(te["sig_time"])
    net = te["net_judge"].to_numpy(dtype=float)
    y = (net > 0).astype(int)
    clip = float(np.quantile(np.abs(net), 0.99))
    w = np.minimum(np.abs(net), clip)
    cut = int(len(Xt) * 0.85)
    m = e13.fit_weighted(Xt.iloc[:cut], y[:cut], w[:cut], Xt.iloc[cut:], y[cut:], w[cut:])
    print(f"[学習] 教師 {len(Xt)} 玉（学習期間のみ）・best_iter={m.best_iteration}")

    # ---- 採点期間の候補（型バー）に prob 適用 ----
    base = rc._load_params()
    p21 = dict(base)
    for k in list(p21):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p21[k] = (k == "ENABLE_P21_SHORT")
    print(f"[load] OHLCV preload: {gen.OHLCV_CSV.name}")
    df, _ = rc.preload(str(gen.OHLCV_CSV), p21)
    ts_a = df["timestamp_ms"].to_numpy(dtype=np.int64)
    arrs = (ts_a, df["close"].to_numpy(dtype=float),
            df["high_raw"].to_numpy(dtype=float), df["low_raw"].to_numpy(dtype=float))
    bars = find_type_bars(df)
    bts = pd.to_datetime(ts_a[bars], unit="ms")
    bars_w = bars[(bts >= score_start) & (bts <= score_end)]
    print(f"[候補] 採点期間の型バー {len(bars_w)} 本")
    Xs = feats(pd.Series(pd.to_datetime(ts_a[bars_w], unit="ms")))
    prob = m.predict(Xs, num_iteration=m.best_iteration)
    allow = {int(b) for b, p in zip(bars_w, prob) if p > 0.5}
    inv = {int(b) for b, p in zip(bars_w, prob) if p <= 0.5}
    print(f"[ゲート] prob>0.5: {len(allow)} / {len(bars_w)} 本（逆＝対照用 {len(inv)} 本）")

    # ---- 連続モード（採点期間のみ・window 外は allow に無く自動 veto）----
    p21_open = dict(p21)
    p21_open["P21_ATR14_MIN"] = 0
    d, s, v = mw.run_continuous(df, arrs, p21_open, lambda i: int(i) not in allow)
    d = pd.DataFrame(d)
    et = pd.to_datetime(d["entry_time"]).values
    xt = pd.to_datetime(d["exit_time"]).values
    assert all(et[k + 1] >= xt[k] for k in range(len(d) - 1)), "同時保有を検出（停止）"
    d.to_csv(out_csv, index=False)
    jsum = sum(judge_net(-1, float(r.entry_price), float(r.exit_price), float(r.size_btc), str(r.exit_reason))
               for r in d.itertuples())
    print(f"[MLゲート] トレード {len(d)} 件 / judge式 ${jsum:,.1f} → {out_csv.name}")
    print("  （正式数字は score.py。地面 $2,697.32 / 912件・E0.4）")

    # ---- 対照実験（予測逆転・源泉検証・judge式の参考値）----
    d2, _, _ = mw.run_continuous(df, arrs, p21_open, lambda i: int(i) not in inv)
    d2 = pd.DataFrame(d2)
    j2 = sum(judge_net(-1, float(r.entry_price), float(r.exit_price), float(r.size_btc), str(r.exit_reason))
             for r in d2.itertuples()) if len(d2) else 0.0
    print(f"[対照実験] prob≤0.5（逆）: {len(d2)} 件 / judge式 ${j2:,.1f}（本命より良ければ ML 寄与なし）")
    print("→ 次: score.py で正式採点（1回）→ report.py → ledger 記録 → まこさん報告")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="候補先頭500件のみ・ファイル出力なし")
    ap.add_argument("--oof", action="store_true", help="Phase 2: OOF 学習（python3.13・教師 CSV 必須）")
    ap.add_argument("--score", action="store_true", help="Phase 3: 本番採点用 CSV 生成＋対照実験（python3.13）")
    args = ap.parse_args()
    if args.oof:
        phase2_oof()
        return
    if args.score:
        phase3_score()
        return

    base = rc._load_params()
    p21 = dict(base)
    for k in list(p21):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p21[k] = (k == "ENABLE_P21_SHORT")

    print(f"[load] OHLCV preload: {gen.OHLCV_CSV.name}")
    df, _ = rc.preload(str(gen.OHLCV_CSV), p21)
    assert "macd" in df.columns and "macd_signal" in df.columns, "macd 列が無い（停止）"
    ts_a = df["timestamp_ms"].to_numpy(dtype=np.int64)
    cl_a = df["close"].to_numpy(dtype=float)
    hi_a = df["high_raw"].to_numpy(dtype=float)
    lo_a = df["low_raw"].to_numpy(dtype=float)
    arrs = (ts_a, cl_a, hi_a, lo_a)
    atr_a = df["atr_14"].to_numpy(dtype=float)
    adx_a = df["adx"].to_numpy(dtype=float)

    # ---- 自己検査①: ラベル用 judge_net 式が審判と一致するか（地面 CSV 再計算 vs score.py 確定値）----
    g = pd.read_csv(GROUND_CSV)
    g["entry_ts"] = pd.to_datetime(g["entry_time"])
    gj = g.apply(lambda r: judge_net(-1, float(r.entry_price), float(r.exit_price),
                                     float(r.size_btc), str(r.exit_reason)), axis=1)
    sc = gj[(g.entry_ts >= "2025-04-01") & (g.entry_ts <= "2025-12-31 23:59:59")].sum()
    tr_ = gj[g.entry_ts <= TRAIN_END].sum()
    print(f"[自己検査①] judge式 地面再計算: 採点期間 ${sc:,.2f}（score.py $2,697.32）/ 学習期間 ${tr_:,.2f}（score.py $9,676.61）")
    assert abs(sc - 2697.32) < 1.0 and abs(tr_ - 9676.61) < 1.0, "judge式が審判と不一致（停止）"

    # ---- 候補生成（型のみ・学習期間）----
    bars = find_type_bars(df)
    bar_ts = pd.to_datetime(ts_a[bars], unit="ms")
    bars = bars[bar_ts <= TRAIN_END]                       # H8: 教師は学習期間のみ
    print(f"[候補] MACD デッドクロス型バー（学習期間）: {len(bars)} 本")
    if args.smoke:
        bars = bars[:500]

    # ---- 各候補: V9 と同一の約定モデル → 前向き sim（V9 Exit）→ judge式 net ----
    sig_cols = e21_sig_cols = {"adx_at_entry": "adx", "bb_mid_slope_at_entry": "bb_mid_slope",
                               "rsi_at_entry": "rsi_short", "rsi_slope_at_entry": "rsi_slope_short",
                               "stoch_k_at_entry": "stoch_k", "stoch_d_at_entry": "stoch_d",
                               "bb_width_at_entry": "bb_width"}
    rows = []
    n_nofill = 0
    n = len(df)
    for i in bars:
        j = i + 1                                          # fill は翌バーのみ（TTL2・E20 実証）
        if j >= n:
            continue
        limit = float(Decimal(str(cl_a[i])) * Decimal("1.0001"))
        if hi_a[j] < limit:
            n_nofill += 1
            continue
        ts_fill = int(ts_a[j])
        states = rc._calc_entry_states(df, j, ts_fill)
        tp = e19.calc_tp_price(df, j, limit, float(adx_a[i]), states["atr_14"], p21)
        sl = rc._calc_sl_price("SHORT", limit, p21, 21)
        extra = {f: (float(df.at[i, c]) if c in df.columns else float("nan")) for f, c in sig_cols.items()}
        extra.update({"ret_5": states["ret_5"], "atr_14": states["atr_14"],
                      "entry_hour": states["entry_hour"], "entry_weekday": states["entry_weekday"]})
        t = e19.simulate_exit(df, arrs, j, limit, ts_fill, tp, sl, p21, extra)
        if t is None:
            continue
        atr_pct_sig = atr_a[i] / cl_a[i] * 100.0
        v9_pass = (adx_a[i] >= float(p21.get("P21_ADX_MIN", 0))
                   and float(p21.get("P21_ATR14_MIN", 150)) <= atr_a[i] <= float(p21.get("P21_ATR14_MAX", 9999)))
        rows.append({
            "bar_i": int(i), "sig_time": str(pd.Timestamp(int(ts_a[i]), unit="ms")),
            "entry_time": t["entry_time"], "exit_time": t["exit_time"], "exit_reason": t["exit_reason"],
            "hold_min": t["hold_min"], "entry_price": t["entry_price"], "exit_price": t["exit_price"],
            "net_rc": float(t["net_usd"]),
            "net_judge": judge_net(-1, float(t["entry_price"]), float(t["exit_price"]), 0.06, t["exit_reason"]),
            "v9_pass": bool(v9_pass), "atr_sig": float(atr_a[i]), "atr_pct_sig": float(atr_pct_sig),
            "adx_sig": float(adx_a[i]),
            **{f: extra[f] for f in sig_cols}, "ret_5": extra["ret_5"], "atr_14": extra["atr_14"],
            "entry_hour": extra["entry_hour"], "entry_weekday": extra["entry_weekday"],
        })
    te = pd.DataFrame(rows)
    print(f"[教師] 約定 {len(te)} 件 / 不約定 {n_nofill} 件")

    # ---- 自己検査②: V9 通過候補のうち地面に居る玉は net_rc が完全一致（独立 sim の正しさ）----
    gset = dict(zip(g["entry_time"], g["net_usd"]))
    sub = te[te["entry_time"].isin(gset.keys())]
    bad = sub[abs(sub["net_rc"] - sub["entry_time"].map(gset)) > 0.01]
    print(f"[自己検査②] 地面と同一 entry の候補 {len(sub)} 件 → net_rc 一致 {len(sub)-len(bad)}/{len(sub)}")
    assert len(bad) == 0, "独立 sim が地面と不一致（停止）"

    # ---- 実測サマリ（学習期間・新計器 net_judge）----
    print("\n========== E21 Phase1 実測（学習期間・judge式 net・サイズ 0.06） ==========")
    for name, m in (("V9 通過（ATR≥150）", te["v9_pass"]), ("V9 見送り（型のみ）", ~te["v9_pass"])):
        s = te[m]
        print(f"  {name}: {len(s)} 件 / net ${s['net_judge'].sum():,.1f} / avg ${s['net_judge'].mean():.2f}/件 "
              f"/ 勝率 {(s['net_judge'] > 0).mean()*100:.1f}%")
    yr = pd.to_datetime(te["sig_time"]).dt.year
    print("\n  年別（V9 通過 / 見送り）:")
    for y in sorted(yr.unique()):
        a = te[(yr == y) & te["v9_pass"]]["net_judge"].sum()
        b = te[(yr == y) & ~te["v9_pass"]]["net_judge"].sum()
        na = int(((yr == y) & te["v9_pass"]).sum()); nb = int(((yr == y) & ~te["v9_pass"]).sum())
        print(f"    {y}: 通過 {na:>5}件 ${a:>9,.1f} / 見送り {nb:>5}件 ${b:>9,.1f}")
    print("\n  見送り集団の ATR%帯別（場面差の素材）:")
    miss = te[~te["v9_pass"]].copy()
    miss["band"] = pd.cut(miss["atr_pct_sig"], [0, 0.1, 0.15, 0.2, 0.3, 99],
                          labels=["0-0.1", "0.1-0.15", "0.15-0.2", "0.2-0.3", "0.3+"])
    agg = miss.groupby("band", observed=True)["net_judge"].agg(["size", "sum", "mean"])
    print(agg.round(2).to_string())

    if not args.smoke:
        OUT_TEACHER.parent.mkdir(parents=True, exist_ok=True)
        te.to_csv(OUT_TEACHER, index=False)
        print(f"\n[出力] {OUT_TEACHER}")
    print("→ 次: サマリをまこさんに報告 → Phase 2（OOF 学習・lightgbm）")


if __name__ == "__main__":
    main()
