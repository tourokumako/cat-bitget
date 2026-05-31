#!/usr/bin/env python3
"""measure_primary_direction_edge.py — 最初の一手: primary 方向の「純エッジ」測定

位置づけ（execlog 工程[2]「Entry エンジン 修正計画」/ baseline §6.2 改訂バナー）:
  Entry エンジン修正 4 手のうち、軸1（§18.5『ボラ予測 ML 設計欠陥』
  cc_entry_logic_self_study.md:1571）の受け入れ条件①②を **実測で確認する第一歩**。
  「買い/売りの判断を、揺れ幅を混ぜずに方向だけで作ったら、手数料を引いてプラスか」を、
  既存 ml_phase2_production の Triple Barrier 予測を使って測る。**再学習なし・新データなし。**

純方向シグナル（軸1: 揺れ幅も meta も使わない＝§6.2.7 の 97%支配を排除した状態）:
  - LONG  の TP 先着確率 = triple_barrier_label_LONG_K{K}.pred_proba_class2_cal
  - SHORT の TP 先着確率 = triple_barrier_label_SHORT_K{K}.pred_proba_class2_cal
  - 各 bar で高い方の側を採用・閾値超なら entry・両方低ければ見送り（排他 1bar1trade）。
  - LONG/SHORT は既に別モデル（軸1 の分離は満たし済）。

クラス対応（run_phase2_entry_ml_baseline.encode_tb_label = y+1 で確定）:
  class0 = SL(-1) / class1 = TIME(0) / class2 = TP(+1)

net の測り方:
  eval_engine.simulate_trade（指値 maker・不約定 TTL3・SL先着/gap/保守fill・taker/slippage/funding）。
  tp_pct = atr14_pct__5m × TP_MULT/100 / sl_pct = × SL_MULT/100（build_labels_pct と 1字1句一致）。
  max_hold = K bars。size = 0.024 BTC（暫定固定・0.12/cap5 相当）。

⚠️ 計器は「正直に測る」担保のみ。net がプラスとは限らない（大前提: マイナスでもデータ/枠組みの
   せいにしない・原因は 4 手のどこが未実装か）。
⚠️ 本スクリプトは **per-trade（1取引あたり）の方向エッジ** を測る。月次合計は独立 trade の単純和で、
   0.12 BTC 合計上限・同時保有は未モデル化（= サイジング/手③ の後段で扱う）。よって月次合計は
   $370 と直接比較しない（per-trade avg net を主指標とする）。

leak 4 点:
  ① 特徴量生成なし（学習済モデルの test 予測を使用）
  ② 予測は train のみ学習のモデル出力（本番再現可）
  ③ timestamp range: signal は period 内・hold は signal+1 以降の OHLC のみ参照（eval_engine が保証）
  ④ feature_importance: 該当なし（学習しない）
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_engine as ee  # noqa: E402

REPO = Path(__file__).resolve().parents[2]  # bitget-python-sdk-api
PROD = REPO / "results" / "priority_rebuild" / "ml_phase2_production"
CSV = REPO / "data" / "BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv"
OUT_DIR = REPO / "results" / "priority_rebuild" / "primary_direction_edge"

LABELS_PARQUET = {
    "test_2025": REPO / "results" / "priority_rebuild" / "labels_mfe_mae_pct_test_2025.parquet",
    "test_2026_q1": REPO / "results" / "priority_rebuild" / "labels_mfe_mae_pct_test_2026_q1.parquet",
}

TP_MULT = 2.0   # build_labels_pct.py と一致
SL_MULT = 1.5
SIZE_BTC = 0.024
ATR_COL = "atr14_pct__5m"
THRESHOLDS = [0.35, 0.40, 0.45, 0.50]  # TB TP先着確率は大半 0.5未満 → 実発火帯に合わせる


def load_bars() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """全 5m bars をロード → (open, high, low, close, timestamps(ns), ts_str→pos)。"""
    df = pd.read_csv(CSV, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    ts = df["timestamp"].values.astype("datetime64[ns]")
    ts_to_pos = {str(pd.Timestamp(t)): i for i, t in enumerate(ts)}
    return (df["open"].to_numpy(float), df["high"].to_numpy(float),
            df["low"].to_numpy(float), df["close"].to_numpy(float), ts, ts_to_pos)


def load_direction_signal(period: str, K: int) -> pd.DataFrame:
    """LONG/SHORT TB の TP先着確率(class2_cal) + atr を結合した signal 表を返す。"""
    long_f = PROD / f"triple_barrier_label_LONG_K{K}" / f"predictions_{period}.parquet"
    short_f = PROD / f"triple_barrier_label_SHORT_K{K}" / f"predictions_{period}.parquet"
    dl = pd.read_parquet(long_f)[["entry_id", "pred_proba_class2_cal", "y_true"]]
    ds = pd.read_parquet(short_f)[["entry_id", "pred_proba_class2_cal", "y_true"]]
    dl = dl.rename(columns={"pred_proba_class2_cal": "p_long_tp", "y_true": "y_long"})
    ds = ds.rename(columns={"pred_proba_class2_cal": "p_short_tp", "y_true": "y_short"})
    sig = dl.merge(ds, on="entry_id", how="inner")

    lab = pd.read_parquet(LABELS_PARQUET[period], columns=[ATR_COL])
    lab.index = lab.index.astype(str)
    sig = sig.merge(lab, left_on="entry_id", right_index=True, how="inner")
    sig = sig.rename(columns={ATR_COL: "atr_pct"})
    sig = sig.dropna(subset=["p_long_tp", "p_short_tp", "atr_pct"])
    return sig.reset_index(drop=True)


def measure(period: str, K: int, smoke: int | None) -> dict:
    o, h, l, c, ts, ts_to_pos = load_bars()
    sig = load_direction_signal(period, K)
    if smoke:
        sig = sig.iloc[:smoke].copy()

    # 純方向の側選択（高い TP 先着確率の側・揺れ幅/meta 不使用）
    sig["side"] = np.where(sig["p_long_tp"] >= sig["p_short_tp"], ee.LONG, ee.SHORT)
    sig["p_chosen"] = np.maximum(sig["p_long_tp"], sig["p_short_tp"])
    # 採用側の実 TB 結果（class2=TP 先着なら勝ち）
    sig["y_chosen"] = np.where(sig["side"] == ee.LONG, sig["y_long"], sig["y_short"])

    # 各 signal の bar position（hold window のため全 bars 配列にマップ）
    pos = sig["entry_id"].map(ts_to_pos)
    valid = pos.notna()
    sig = sig[valid].copy()
    sig["pos"] = pos[valid].astype(int).values

    results = {"period": period, "K": K, "n_signals_total": int(len(sig)),
               "smoke": smoke, "size_btc": SIZE_BTC, "tp_mult": TP_MULT, "sl_mult": SL_MULT,
               "class_map": "class0=SL / class1=TIME / class2=TP(採用確率)",
               "by_threshold": []}

    # per-side AUC（TB の TP先着確率が実 TP 先着をどれだけ rank できるか＝方向情報の有無）
    try:
        from sklearn.metrics import roc_auc_score
        auc_long = float(roc_auc_score((sig["y_long"] == 2).astype(int), sig["p_long_tp"]))
        auc_short = float(roc_auc_score((sig["y_short"] == 2).astype(int), sig["p_short_tp"]))
    except Exception as e:
        auc_long = auc_short = float("nan")
        print(f"[warn] AUC 計算失敗: {e}")
    results["auc_long_tp"] = auc_long
    results["auc_short_tp"] = auc_short

    for thr in THRESHOLDS:
        ent = sig[sig["p_chosen"] >= thr]
        nets, reasons, filled = [], [], 0
        months: dict[str, float] = {}
        for _, r in ent.iterrows():
            tp_pct = float(r["atr_pct"]) * TP_MULT / 100.0
            sl_pct = float(r["atr_pct"]) * SL_MULT / 100.0
            tr = ee.simulate_trade(
                int(r["pos"]), int(r["side"]), SIZE_BTC,
                o, h, l, c, ts, tp_pct, sl_pct, max_hold_bars=K)
            if tr is None:
                continue  # 不約定（取引不成立）
            filled += 1
            nets.append(tr.net)
            reasons.append(tr.exit_reason)
            mkey = str(pd.Timestamp(ts[tr.fill_idx]))[:7]  # YYYY-MM
            months[mkey] = months.get(mkey, 0.0) + tr.net
        nets_a = np.array(nets) if nets else np.array([0.0])
        reasons_a = np.array(reasons) if reasons else np.array([""])
        n_sig = int(len(ent))
        row = {
            "threshold": thr,
            "n_signals": n_sig,
            "n_filled": filled,
            "fill_rate": round(filled / n_sig, 4) if n_sig else 0.0,
            "avg_net_per_trade": round(float(nets_a.mean()), 6),   # ← 主指標
            "median_net_per_trade": round(float(np.median(nets_a)), 6),
            "total_net": round(float(nets_a.sum()), 2),
            "win_rate_TP": round(float((reasons_a == "TP").mean()), 4),
            "sl_rate": round(float((reasons_a == "SL").mean()), 4),
            "time_rate": round(float((reasons_a == "TIME").mean()), 4),
            "monthly_net": {k: round(v, 2) for k, v in sorted(months.items())},
        }
        results["by_threshold"].append(row)
        print(f"  thr={thr}: signals={n_sig} filled={filled} "
              f"avg_net/trade={row['avg_net_per_trade']:+.6f} "
              f"total_net={row['total_net']:+.2f} winTP={row['win_rate_TP']:.3f}")
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", default="test_2025", choices=list(LABELS_PARQUET))
    ap.add_argument("--k", type=int, default=12)
    ap.add_argument("--tp-mult", type=float, default=2.0,
                    help="TP barrier 倍率（既定2.0=production・スキャル幾何は小さく）")
    ap.add_argument("--sl-mult", type=float, default=1.5,
                    help="SL barrier 倍率（既定1.5=production・スキャル幾何は大きく）")
    ap.add_argument("--smoke", type=int, default=None,
                    help="先頭 N signals のみ（動作確認用）")
    args = ap.parse_args()
    # 幾何を probe 用に上書き（⚠️ 既存モデルは production 幾何 2.0/1.5 用に学習済・粗い当たり確認）
    global TP_MULT, SL_MULT
    TP_MULT, SL_MULT = args.tp_mult, args.sl_mult

    print("=" * 70)
    print(f"primary 方向 純エッジ測定 | period={args.period} K={args.k} "
          f"smoke={args.smoke}")
    print(f"クラス: class0=SL / class1=TIME / class2=TP(採用) | "
          f"size={SIZE_BTC}BTC tp×{TP_MULT}/sl×{SL_MULT}")
    print("=" * 70)

    res = measure(args.period, args.k, args.smoke)

    print("-" * 70)
    print(f"AUC(TP先着|LONG)={res['auc_long_tp']:.4f}  "
          f"AUC(TP先着|SHORT)={res['auc_short_tp']:.4f}  (0.5=情報なし)")
    print("-" * 70)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tag = f"{args.period}_K{args.k}_tp{TP_MULT}sl{SL_MULT}" + (f"_smoke{args.smoke}" if args.smoke else "")
    out = OUT_DIR / f"summary_{tag}.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[出力] {out}")


if __name__ == "__main__":
    main()
