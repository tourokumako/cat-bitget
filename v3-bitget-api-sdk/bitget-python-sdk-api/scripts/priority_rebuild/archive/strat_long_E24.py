#!/usr/bin/env python3
"""strat_long_E24.py — LONG 新入口の学習（E24・指標の組み合わせを木が学ぶ・Exit はラベルと同一の固定バリア）

設計（まこさん GO 2026-06-12）:
- ラベル＝eval_engine.simulate_trade（指値 maker TTL・コスト込み・既知答えテスト済の計器）で各バーから
  前向き sim した net>0 二値。執行込みラベル＝実出口と完全一致・不約定はラベル外（leak なし）。
- 機会定義2案（事前宣言・lightgbm が場面を学習）: scalp = TP0.3%/SL0.3%/30分 ／ std = TP0.5%/SL0.5%/150分。
- 特徴量＝シグナルバー確定値のみ18個（5m 指標＋過去リターン 15m-8h＋時間帯・全て%・H6/H15）。
- 学習＝walk-forward（年 expanding: 21→22, 21-22→23, 21-23→24）＋purge（ラベル区間）＋embargo 1日
  ＋uniqueness 重み（同時アクティブ数の逆数・AFML §4）。
- 評価＝OOF prob 上位（cutoff 分位 {0.90, 0.95} 事前宣言）→ 1ポジ制で時系列フィルタ →
  score.py 形式 CSV → score.py 採点（学習期間・年別非劣化を見る）。採点期間は不接触。
- H 照合: H1(1ポジ 0.024)/H2(walk-forward+purge+期間 assert)/H5(計器)/H6(%のみ)/H8(学習≤2024-12)/
  H15(ラベル=バリア先着方向・vol_share 監視)/H16(1変更=新入口・Exit 固定)。
実行: python3.13（lightgbm）。--def scalp|std --smoke あり。
"""
from __future__ import annotations
import argparse
import sys
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                      # noqa: E402
import gen_p23_candidates as gen             # noqa: E402
import eval_engine as ee                     # noqa: E402
from preload_cache import cached_preload     # noqa: E402

RATCHET = ROOT / "results" / "priority_rebuild" / "ratchet"
TRAIN_END = pd.Timestamp("2025-01-01")
DEFS = {"scalp": {"tp": 0.003, "sl": 0.003, "hold": 6},
        "std":   {"tp": 0.005, "sl": 0.005, "hold": 30}}
CUTOFF_QS = (0.90, 0.95)
SIZE = 0.024


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    X = pd.DataFrame(index=df.index)
    X["slope_pct"] = df.bb_mid_slope / df.close * 100
    X["atr_pct"] = df.atr_14 / df.close * 100
    X["ema_dev"] = (df.close - df.ema_20) / df.close * 100
    for c in ["adx", "rsi_short", "stoch_k", "stoch_d", "rci_9", "rci_52", "bb_width"]:
        X[c] = df[c].values
    cs = pd.Series(df.close.values)
    for m in [3, 6, 12, 48, 96]:
        X[f"ret_{m*5}m"] = cs.pct_change(m).values * 100
    ts = pd.to_datetime(df.timestamp_ms, unit="ms")
    X["hour"] = ts.dt.hour
    X["dow"] = ts.dt.dayofweek
    return X


def gen_labels(df, opens, highs, lows, closes, tss, spec, smoke=False, entry_type="maker"):
    """全学習バーを eval_engine.simulate_trade でラベル化（執行込み・不約定=対象外）。"""
    n = len(closes)
    end = int((pd.Series(pd.to_datetime(df.timestamp_ms, unit="ms")) < TRAIN_END).sum())
    step = 50 if smoke else 1
    rows = []
    for i in range(200, end - spec["hold"] - spec["hold"] - 2, step):
        tr = ee.simulate_trade(i, ee.LONG, SIZE, opens, highs, lows, closes, tss,
                               tp_pct=spec["tp"], sl_pct=spec["sl"], max_hold_bars=spec["hold"], entry_type=entry_type)
        if tr is None:
            continue
        mfe = (highs[tr.fill_idx:tr.exit_idx+1].max() - tr.entry_price) * SIZE
        mae = (tr.entry_price - lows[tr.fill_idx:tr.exit_idx+1].min()) * SIZE
        rows.append((i, tr.fill_idx, tr.exit_idx, tr.net, tr.exit_reason, tr.gross, tr.fee, tr.slippage_cost + tr.funding_cost, mfe, mae))
    lab = pd.DataFrame(rows, columns=["sig_idx", "fill_idx", "exit_idx", "net", "reason", "gross", "fee", "slipfund", "mfe", "mae"])
    lab["y"] = (lab.net > 0).astype(int)
    # uniqueness 重み: ラベル区間 [fill, exit] の同時アクティブ数の逆数（AFML §4 簡易版）
    cnt = np.zeros(n)
    for _, r in lab.iterrows():
        cnt[int(r.fill_idx):int(r.exit_idx) + 1] += 1
    lab["uniq_w"] = [1.0 / max(1.0, cnt[int(r.fill_idx):int(r.exit_idx) + 1].mean()) for _, r in lab.iterrows()]
    return lab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--def", dest="defname", choices=list(DEFS), required=True)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--entry", choices=["maker","taker"], default="maker")
    args = ap.parse_args()
    spec = DEFS[args.defname]

    params = rc._load_params()
    df, _ = cached_preload(str(gen.OHLCV_CSV), params)
    ts = pd.to_datetime(df.timestamp_ms, unit="ms")
    assert ts.iloc[-1] >= pd.Timestamp("2026-03-01"), "データ範囲異常"
    opens = df.open.to_numpy(float); highs = df.high_raw.to_numpy(float)
    lows = df.low_raw.to_numpy(float); closes = df.close.to_numpy(float)
    tss = ts.to_numpy()  # datetime64[ns]（eval_engine._to_utc 対応型）

    print(f"[E24:{args.defname}:{args.entry}] ラベル生成（eval_engine 計器・執行込み）...")
    lab = gen_labels(df, opens, highs, lows, closes, tss, spec, smoke=args.smoke, entry_type=args.entry)
    lab["ts"] = ts.iloc[lab.sig_idx.values].values
    lab["year"] = pd.DatetimeIndex(lab.ts).year
    assert lab.ts.max() < TRAIN_END, "H8 違反: 学習ラベルが 2025 に侵入"
    print(f"  ラベル {len(lab)}件 / 勝率 base {lab.y.mean():.3f} / fill 率込み")

    X_all = build_features(df)
    feats = list(X_all.columns)
    Xl = X_all.iloc[lab.sig_idx.values].reset_index(drop=True)
    ok = ~Xl.isna().any(axis=1)
    lab, Xl = lab[ok.values].reset_index(drop=True), Xl[ok.values].reset_index(drop=True)

    import lightgbm as lgb
    embargo_bars = 288  # 1日
    oof = np.full(len(lab), np.nan)
    for te_year in (2022, 2023, 2024):
        tr_m = (lab.year < te_year).values
        te_m = (lab.year == te_year).values
        if te_m.sum() == 0 or tr_m.sum() < 1000:
            continue
        te_start_idx = lab[te_m].sig_idx.min()
        # purge: ラベル区間が test 期間に届く学習玉を除外 + embargo
        tr_m &= (lab.exit_idx.values < te_start_idx - embargo_bars)
        m = lgb.LGBMClassifier(n_estimators=300, num_leaves=31, min_child_samples=200,
                               learning_rate=0.05, random_state=42, verbose=-1)
        m.fit(Xl[tr_m], lab.y[tr_m], sample_weight=(lab.uniq_w * lab.net.abs().clip(
            upper=lab.net.abs().quantile(0.99)))[tr_m])
        oof[te_m] = m.predict_proba(Xl[te_m])[:, 1]
        # H15: vol_share 監視
        imp = pd.Series(m.feature_importances_, index=feats)
        vol_share = imp[["atr_pct", "bb_width"]].sum() / imp.sum()
        print(f"  wf→{te_year}: train {tr_m.sum()} / vol_share {vol_share:.3f}" +
              ("  ⚠️>0.5 停止基準" if vol_share > 0.5 else ""))

    lab["prob"] = oof
    val = lab.dropna(subset=["prob"]).reset_index(drop=True)  # 2022-24 の OOF
    print(f"\n[OOF] 対象 {len(val)}件（2022-24）")
    for q in CUTOFF_QS:
        th = val.prob.quantile(q)
        sel = val[val.prob >= th].sort_values("sig_idx")
        # 1ポジ制: 前の玉の exit まで次のシグナルをスキップ
        keep, busy_until = [], -1
        for _, r in sel.iterrows():
            if r.sig_idx > busy_until:
                keep.append(r)
                busy_until = r.exit_idx
        k = pd.DataFrame(keep)
        out = pd.DataFrame({
            "entry_time": ts.iloc[k.fill_idx.values].values,
            "exit_time": ts.iloc[k.exit_idx.values].values,
            "side": "LONG", "priority": 90,
            "size_btc": SIZE,
            "entry_price": closes[k.fill_idx.values],   # 近似表示用（net は計器値が正）
            "exit_price": closes[k.exit_idx.values],
            "exit_reason": k.reason.map({"TP": "TP_FILLED", "SL": "SL_FILLED", "TIME": "TIME_EXIT"}).values,
            "net_usd": k.net.values,
            "gross_usd": k.gross.values, "fee_usd": k.fee.values,
            "mfe_usd": k.mfe.values, "mae_usd": (-k.mae.abs()).values,
            "hold_min": (ts.iloc[k.exit_idx.values].values - ts.iloc[k.fill_idx.values].values).astype("timedelta64[m]").astype(float),
            "adx_at_entry": X_all.adx.values[k.sig_idx.values.astype(int)],
            "bb_mid_slope_at_entry": df.bb_mid_slope.values[k.sig_idx.values.astype(int)],
            "rsi_at_entry": X_all.rsi_short.values[k.sig_idx.values.astype(int)],
            "rsi_slope_at_entry": 0.0,
            "atr_14": df.atr_14.values[k.sig_idx.values.astype(int)],
            "stoch_k_at_entry": X_all.stoch_k.values[k.sig_idx.values.astype(int)],
            "stoch_d_at_entry": X_all.stoch_d.values[k.sig_idx.values.astype(int)],
            "bb_width_at_entry": X_all.bb_width.values[k.sig_idx.values.astype(int)],
            "ret_5": df.close.pct_change(1).values[k.sig_idx.values.astype(int)]*100,
            "add_count": 1,
        })
        f = RATCHET / f"trades_long_E24_{args.defname}_{args.entry}_q{int(q*100)}.csv"
        out.to_csv(f, index=False)
        yearly = k.groupby(pd.DatetimeIndex(k.ts).year).net.sum().round(0).to_dict()
        print(f"  cutoff q{q}: {len(k)}玉(1ポジ制) / 計器 net 合計 {k.net.sum():.0f} / 年別 {yearly} / 勝率 {k.y.mean():.3f}")
        print(f"    → {f.name}")


if __name__ == "__main__":
    main()
