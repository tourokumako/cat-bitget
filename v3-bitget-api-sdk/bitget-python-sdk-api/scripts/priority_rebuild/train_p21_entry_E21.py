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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="候補先頭500件のみ・ファイル出力なし")
    args = ap.parse_args()

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
