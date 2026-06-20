#!/usr/bin/env python3
"""strat_long_E25.py — LONG 新入口 改善版（E24 の欠陥3つを是正・まこさん GO 2026-06-12）

E24（strat_long_E24.py・閉じ）からの是正点:
 ① 出口セット作り直し（対称固定バリア TP=SL を廃止 → V9 流儀の非対称・3段构成）:
      TP   +0.5%  指値 maker（学習期間 OHLC 全バー前向き実測: 150分内到達率 44.1%）
      失速 保有50分時点で含み益 +0.15% 未達なら降りる（成行 taker・負け玉の54.6%を小さく切り勝ち玉誤切り11.1%）
      SL   -1.5%  事故ブレーキ（V9 P3 流儀=TPより広い pct・TP到達玉の98.2%はSLに触れずTP到達）
      TIME 150分  上限バックストップ（TP到達玉の90%ileは120分）
    値の出典: 学習期間 2021-04〜2024-12 の OHLC 全バー実測（N=131,556・2026-06-12 まこさん承認）
 ② 特徴量: 5m単一期間のみ → ＋複数期間(e8b.build_multiperiod) ＋MTF 15m/30m/1h/4h(e8.build_mtf)
    ★物理 assert: MTF 列が存在しなければ学習前に停止（実装で黙って消えるのを物理防止・まこさん 2026-06-12）
 ③ 記録: fold別 AUC / 較正表 / feature importance top10 / vol_share / 全特徴量リストを JSON 保存
関所: OOF → 対照実験(prob逆転) → precheck → 通過時のみ採点1回（採点はこのスクリプトではやらない）。
V9 本体 / 審判(score.py・eval_engine) / E24 原本は不変・import のみ。
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                      # noqa: E402
import gen_p23_candidates as gen             # noqa: E402
import eval_engine as ee                     # noqa: E402
from preload_cache import cached_preload     # noqa: E402
import train_p23_entry_E8b as e8b            # noqa: E402  複数期間（方向系）
import train_p23_entry_E8 as e8              # noqa: E402  MTF
import lightgbm as lgb                       # noqa: E402
from sklearn.metrics import roc_auc_score    # noqa: E402

RATCHET = ROOT / "results" / "priority_rebuild" / "ratchet"
TRAIN_END = pd.Timestamp("2025-01-01")

# 出口セット（導出値・2026-06-12 まこさん承認・ヘッダ①に出典）
TP_PCT = 0.005
SL_PCT = 0.015
STALE_BARS = 10        # 50分
STALE_MFE_PCT = 0.0015 # +0.15%
HOLD_BARS = 30         # 150分

CUTOFF_QS = (0.90, 0.95)
SIZE = 0.024


def build_base_features(df: pd.DataFrame) -> pd.DataFrame:
    """E24 と同じ 5m 基本特徴量（pct 化・シグナルバー確定値）。"""
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


def sim_exitset(i, opens, highs, lows, closes, tss):
    """出口セット（TP/失速/SL/TIME）を eval_engine のみで前向き sim（自作 net 計算なし）。
    2段方式: まず失速窓(50分)で sim → TP/SL ならそこで確定 ／ TIME なら順行チェック →
    +0.15% 未達=そのまま失速カット（taker・計器の TIME 結果が正確にそれ） ／ 順行あり= full 150分で再 sim。"""
    tr1 = ee.simulate_trade(i, ee.LONG, SIZE, opens, highs, lows, closes, tss,
                            tp_pct=TP_PCT, sl_pct=SL_PCT, max_hold_bars=STALE_BARS, entry_type="maker")
    if tr1 is None:
        return None, None
    if tr1.exit_reason in ("TP", "SL"):
        return tr1, tr1.exit_reason
    mfe_pct = (highs[tr1.fill_idx:tr1.exit_idx + 1].max() - tr1.entry_price) / tr1.entry_price
    if mfe_pct < STALE_MFE_PCT:
        return tr1, "STALE"  # 失速カット = 50分時点 taker クローズ（tr1 の TIME と同一の執行・コスト）
    tr2 = ee.simulate_trade(i, ee.LONG, SIZE, opens, highs, lows, closes, tss,
                            tp_pct=TP_PCT, sl_pct=SL_PCT, max_hold_bars=HOLD_BARS, entry_type="maker")
    if tr2 is None:
        return None, None
    return tr2, tr2.exit_reason


def gen_labels(df, opens, highs, lows, closes, tss, smoke=False):
    n = len(closes)
    end = int((pd.Series(pd.to_datetime(df.timestamp_ms, unit="ms")) < TRAIN_END).sum())
    step = 50 if smoke else 1
    rows = []
    for i in range(200, end - HOLD_BARS - 2, step):
        tr, reason = sim_exitset(i, opens, highs, lows, closes, tss)
        if tr is None:
            continue
        rows.append((i, tr.fill_idx, tr.exit_idx, tr.entry_price, tr.net, reason,
                     tr.gross, tr.fee, tr.slippage_cost + tr.funding_cost))
    lab = pd.DataFrame(rows, columns=["sig_idx", "fill_idx", "exit_idx", "entry_price",
                                      "net", "reason", "gross", "fee", "slipfund"])
    lab["y"] = (lab.net > 0).astype(int)
    cnt = np.zeros(n)
    for _, r in lab.iterrows():
        cnt[int(r.fill_idx):int(r.exit_idx) + 1] += 1
    lab["uniq_w"] = [1.0 / max(1.0, cnt[int(r.fill_idx):int(r.exit_idx) + 1].mean()) for _, r in lab.iterrows()]
    return lab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    params = rc._load_params()
    df, _ = cached_preload(str(gen.OHLCV_CSV), params)
    ts = pd.to_datetime(df.timestamp_ms, unit="ms")
    assert ts.iloc[-1] >= pd.Timestamp("2026-03-01"), "データ範囲異常"
    opens = df.open.to_numpy(float); highs = df.high_raw.to_numpy(float)
    lows = df.low_raw.to_numpy(float); closes = df.close.to_numpy(float)
    tss = ts.to_numpy()

    print(f"[E25] ラベル生成（出口セット TP{TP_PCT*100}%/失速{STALE_BARS*5}分+{STALE_MFE_PCT*100}%/SL{SL_PCT*100}%/TIME{HOLD_BARS*5}分・計器執行込み）...", flush=True)
    lab = gen_labels(df, opens, highs, lows, closes, tss, smoke=args.smoke)
    lab["ts"] = ts.iloc[lab.sig_idx.values].values
    lab["year"] = pd.DatetimeIndex(lab.ts).year
    assert lab.ts.max() < TRAIN_END, "H8 違反: 学習ラベルが 2025 に侵入"
    print(f"  ラベル {len(lab)}件 / 勝率 base {lab.y.mean():.3f} / 出口内訳 {lab.reason.value_counts().to_dict()}", flush=True)

    # ---- 特徴量（基本 + 複数期間 + MTF）----
    ohlcv = pd.DataFrame({"timestamp": ts.values, "open": opens, "high": highs, "low": lows, "close": closes})
    base = build_base_features(df)
    sig_ts = pd.Series(ts.iloc[lab.sig_idx.values].values)
    mp = e8b.build_multiperiod(ohlcv).reindex(pd.to_datetime(sig_ts.values)).reset_index(drop=True)
    mtf = e8.build_mtf(ohlcv, sig_ts).reset_index(drop=True)
    Xl = pd.concat([base.iloc[lab.sig_idx.values].reset_index(drop=True), mp, mtf], axis=1)
    Xl = Xl.loc[:, ~Xl.columns.duplicated()]
    feats = list(Xl.columns)

    # ★ 物理 assert: MTF 列の存在（黙って消えるのを防止・まこさん 2026-06-12）
    mtf_cols = [c for c in feats if c.endswith(("_15m", "_30m", "_1h", "_4h")) or
                any(t in c for t in ("_15m_", "_30m_", "_1h_", "_4h_"))]
    assert len(mtf_cols) >= 15, f"MTF 列が特徴量に無い/不足（{len(mtf_cols)}列）。実装欠落＝停止"
    assert not Xl[mtf_cols].isna().all().any(), "MTF 列が全 NaN＝結合失敗。停止"
    mp_cols = [c for c in feats if any(c.startswith(p) for p in ("stoch_k_", "stoch_d_", "stoch_gap_", "adx_", "bb_slope_pct_", "bb_pctb_", "rsi_")) and c[-1].isdigit()]
    assert len(mp_cols) >= 15, f"複数期間列が不足（{len(mp_cols)}列）。停止"
    print(f"  特徴量 {len(feats)}列（基本 {len(base.columns)} / 複数期間 {len(mp_cols)} / MTF {len(mtf_cols)}）", flush=True)

    ok = ~Xl.isna().any(axis=1)
    lab, Xl = lab[ok.values].reset_index(drop=True), Xl[ok.values].reset_index(drop=True)

    # ---- walk-forward 学習（年 expanding・purge+embargo）＋ fold 別記録 ----
    embargo_bars = 288
    oof = np.full(len(lab), np.nan)
    fold_log = []
    for te_year in (2022, 2023, 2024):
        tr_m = (lab.year < te_year).values
        te_m = (lab.year == te_year).values
        if te_m.sum() == 0 or tr_m.sum() < 1000:
            continue
        te_start_idx = lab[te_m].sig_idx.min()
        tr_m &= (lab.exit_idx.values < te_start_idx - embargo_bars)
        w = (lab.uniq_w * lab.net.abs().clip(upper=lab.net.abs().quantile(0.99)))
        m = lgb.LGBMClassifier(n_estimators=300, num_leaves=31, min_child_samples=200,
                               learning_rate=0.05, random_state=42, verbose=-1)
        m.fit(Xl[tr_m], lab.y[tr_m], sample_weight=w[tr_m])
        p = m.predict_proba(Xl[te_m])[:, 1]
        oof[te_m] = p
        auc = roc_auc_score(lab.y[te_m], p)
        imp = pd.Series(m.feature_importances_, index=feats)
        vol_share = imp[[c for c in feats if "atr" in c or "bb_width" in c]].sum() / imp.sum()
        top10 = imp.sort_values(ascending=False).head(10)
        # 較正表（OOF prob 五分位 × 実勝率）
        qb = pd.qcut(p, 5, duplicates="drop")
        calib = pd.DataFrame({"prob": p, "y": lab.y[te_m].values}).groupby(qb, observed=True).agg(
            n=("y", "size"), mean_prob=("prob", "mean"), win=("y", "mean")).round(3)
        print(f"\n  wf→{te_year}: train {tr_m.sum()} / AUC {auc:.4f} / vol_share {vol_share:.3f}" +
              ("  ⚠️>0.5 停止基準" if vol_share > 0.5 else ""), flush=True)
        print(f"  importance top10: {top10.round(0).to_dict()}", flush=True)
        print(f"  較正表:\n{calib.to_string()}", flush=True)
        if vol_share > 0.5:
            sys.exit("H15 停止: vol_share > 0.5（揺れ幅が方向スコアを支配）")
        fold_log.append({"year": te_year, "n_train": int(tr_m.sum()), "n_test": int(te_m.sum()),
                         "auc": round(float(auc), 4), "vol_share": round(float(vol_share), 4),
                         "imp_top10": {k: float(v) for k, v in top10.items()},
                         "calib": calib.reset_index(drop=True).to_dict("records")})

    lab["prob"] = oof
    val = lab.dropna(subset=["prob"]).reset_index(drop=True)
    print(f"\n[OOF] 対象 {len(val)}件（2022-24）", flush=True)

    def one_pos_select(sel):
        keep, busy = [], -1
        for _, r in sel.sort_values("sig_idx").iterrows():
            if r.sig_idx > busy:
                keep.append(r); busy = r.exit_idx
        return pd.DataFrame(keep)

    def emit(k, name):
        out = pd.DataFrame({
            "entry_time": ts.iloc[k.fill_idx.values.astype(int)].values,
            "exit_time": ts.iloc[k.exit_idx.values.astype(int)].values,
            "side": "LONG", "priority": 91, "size_btc": SIZE,
            "entry_price": k.entry_price.values,
            "exit_price": np.where(k.reason == "TP", k.entry_price * (1 + TP_PCT),
                          np.where(k.reason == "SL", k.entry_price * (1 - SL_PCT),
                                   closes[k.exit_idx.values.astype(int)])),
            "exit_reason": k.reason.map({"TP": "TP_FILLED", "SL": "SL_FILLED",
                                         "STALE": "MFE_STALE_CUT", "TIME": "TIME_EXIT"}).values,
            "net_usd": k.net.values, "gross_usd": k.gross.values, "fee_usd": k.fee.values,
            "mfe_usd": np.array([(highs[int(f):int(e) + 1].max() - ep) * SIZE
                                 for f, e, ep in zip(k.fill_idx, k.exit_idx, k.entry_price)]),
            "mae_usd": np.array([(lows[int(f):int(e) + 1].min() - ep) * SIZE
                                 for f, e, ep in zip(k.fill_idx, k.exit_idx, k.entry_price)]),
            "hold_min": (ts.iloc[k.exit_idx.values.astype(int)].values -
                         ts.iloc[k.fill_idx.values.astype(int)].values).astype("timedelta64[m]").astype(float),
            "adx_at_entry": df.adx.values[k.sig_idx.values.astype(int)],
            "bb_mid_slope_at_entry": df.bb_mid_slope.values[k.sig_idx.values.astype(int)],
            "rsi_at_entry": df.rsi_short.values[k.sig_idx.values.astype(int)],
            "rsi_slope_at_entry": 0.0,
            "atr_14": df.atr_14.values[k.sig_idx.values.astype(int)],
            "stoch_k_at_entry": df.stoch_k.values[k.sig_idx.values.astype(int)],
            "stoch_d_at_entry": df.stoch_d.values[k.sig_idx.values.astype(int)],
            "bb_width_at_entry": df.bb_width.values[k.sig_idx.values.astype(int)],
            "ret_5": pd.Series(df.close.values).pct_change(1).values[k.sig_idx.values.astype(int)] * 100,
            "add_count": 1,
        })
        f = RATCHET / f"trades_long_E25_{name}.csv"
        out.to_csv(f, index=False)
        yearly = k.groupby(pd.DatetimeIndex(k.ts).year).net.sum().round(0).to_dict()
        print(f"  {name}: {len(k)}玉(1ポジ制) / 計器 net 合計 {k.net.sum():.0f} / 年別 {yearly} / 勝率 {k.y.mean():.3f}\n    → {f.name}", flush=True)
        return float(k.net.sum())

    summary = {}
    for q in CUTOFF_QS:
        th = val.prob.quantile(q)
        k = one_pos_select(val[val.prob >= th])
        summary[f"top_q{int(q*100)}"] = emit(k, f"q{int(q*100)}")
        # ★ 対照実験（prob 逆転・下位同分位・1ポジ制）— ML に情報があるなら明確に悪いはず
        kb = one_pos_select(val[val.prob <= val.prob.quantile(1 - q)])
        nb = float(kb.net.sum())
        summary[f"bottom_q{int(q*100)}"] = nb
        print(f"  対照(下位 q{int((1-q)*100)}): {len(kb)}玉 / net {nb:.0f} / 勝率 {kb.y.mean():.3f}", flush=True)

    meta = {"_source": "strat_long_E25.py（E24是正: 出口セット/MTF+複数期間/fold記録）",
            "exit_set": {"tp_pct": TP_PCT, "sl_pct": SL_PCT, "stale_bars": STALE_BARS,
                         "stale_mfe_pct": STALE_MFE_PCT, "hold_bars": HOLD_BARS},
            "n_labels": int(len(lab)), "base_rate": round(float(lab.y.mean()), 4),
            "features_all": feats, "n_mtf_cols": len(mtf_cols), "n_mp_cols": len(mp_cols),
            "folds": fold_log, "selection_summary": summary}
    jf = RATCHET / "long_E25_learned_params.json"
    jf.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f"\n[保存] {jf.name}（全特徴量リスト・fold記録・較正・選抜サマリ）", flush=True)


if __name__ == "__main__":
    main()
