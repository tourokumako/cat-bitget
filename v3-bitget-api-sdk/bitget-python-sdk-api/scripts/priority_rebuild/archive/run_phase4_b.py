#!/usr/bin/env python3
"""
run_phase4_b.py — ML Phase 4-b: Exit シミュレーション (3 方式 × グリッド)

指示書: bitget-python-sdk-api/cc_ml_design_spec.md §3.1 / §5 Phase 4 step 2-3
採用 ML: Phase 3-b / 採用クラスタ: k=4 (Phase 4-a)

スコープ:
  - Entry 候補: 24 種 (K∈{12,24,48,96} × side∈{LONG,SHORT}) × q95 閾値
  - Exit 3 方式 × グリッド = 11 パターン:
    A) 固定 TP   : TP_pct ∈ {0.3, 0.5, 0.7, 0.9}    (予測 MFE の X%)
    B) トレーリング: retrace ∈ {0.10, 0.20, 0.30, 0.50}
    C) 時間 Exit  : N_bars ∈ {K//2, K, K*2}
  - 約定モデル: 指値 Maker fill 楽観 (bar 内到達で TP price 約定 / 時間 Exit は bar close)
  - PnL = POS_SIZE_BTC × (exit_price − entry_price) × dir − fee_roundtrip
  - 集計: cluster × (K, side) × Exit × param で平均 NET / 月次 NET

入力:
  data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv           (5m OHLC・2025 を slice)
  results/priority_rebuild/ml_phase3_b/predictions_test2025.parquet
  results/priority_rebuild/ml_phase3_b/entry_thresholds.json
  results/priority_rebuild/ml_phase4_a/cluster_labels_k4.parquet

出力 (results/priority_rebuild/ml_phase4_b/):
  phase4b_log_<TS>.txt
  entry_candidates.parquet              全 Entry × 24 種 × q95 発火
  exit_simulations.parquet              Entry × Exit 戦略 × exit_price / pnl
  cluster_exit_pnl_summary.csv          cluster × (K,side) × exit × param → 平均/月次
  cluster_best_exit.csv                 cluster × (K,side) ごとの最良 Exit
  summary.md

技術要件 / 注意:
  - 約定モデルは楽観 (TP 指値 fill 想定)。Phase 5 統合 Replay でより現実的にする
  - Position 同時保有上限なし (指示書 §4)
  - fee = FEE_RATE_MAKER (0.00014) × 2 (round-trip)
  - POS_SIZE_BTC = 0.12
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OHLC_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
PHASE3B_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase3_b"
PHASE4A_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase4_a"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase4_b"

PREDICTIONS_TRAIN = PHASE3B_DIR / "predictions_train_2021_2024.parquet"  # best 選定用 (L-183 / checklist 4b.1)
PREDICTIONS_TEST = PHASE3B_DIR / "predictions_test2025.parquet"          # apply 評価用 (best 選定なし)
THRESHOLDS = PHASE3B_DIR / "entry_thresholds.json"
CLUSTER_TRAIN = PHASE4A_DIR / "cluster_labels_train_k4.parquet"          # train 期間クラスタ
CLUSTER_TEST = PHASE4A_DIR / "cluster_labels_test2025_k4.parquet"        # test 期間クラスタ

K_WINDOWS = (12, 24, 48, 96)
SIDES = ("LONG", "SHORT")
THRESHOLD_Q = "q95"

POS_SIZE_BTC = 0.12
FEE_RATE_MAKER = 0.00014
ROUND_TRIP_FEE = FEE_RATE_MAKER * 2

# Exit パラメータグリッド
TP_PCT_GRID = (0.3, 0.5, 0.7, 0.9)
TRAILING_PCT_GRID = (0.10, 0.20, 0.30, 0.50)


def time_exit_n_bars(k: int) -> tuple[int, ...]:
    return (max(1, k // 2), k)  # K×2 削除 (予測窓を超える Exit 禁止・checklist 4b.3)


TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_PATH = OUT_DIR / f"phase4b_log_{TS}.txt"


def log(msg: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def load_ohlc_period(start: str, end: str) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """1826d CSV から 指定期間を抽出。numpy array + ts→idx マップを返す。"""
    df = pd.read_csv(OHLC_CSV, parse_dates=["timestamp"])
    df = df.set_index("timestamp").sort_index()
    df = df.loc[start:end]
    log(f"  ohlc {start[:10]}〜{end[:10]}: {df.shape} ({df.index[0]} → {df.index[-1]})")
    opens = df["open"].to_numpy(dtype=np.float64)
    highs = df["high"].to_numpy(dtype=np.float64)
    lows = df["low"].to_numpy(dtype=np.float64)
    closes = df["close"].to_numpy(dtype=np.float64)
    ts_to_idx = {ts: i for i, ts in enumerate(df.index)}
    return df, opens, highs, lows, closes, ts_to_idx


def extract_entries(
    pred: pd.DataFrame,
    cluster_labels: pd.DataFrame,
    thresholds: dict,
    ts_to_idx: dict,
) -> pd.DataFrame:
    """24 種 (K × side) × q95 で Entry 候補を抽出。"""
    rows = []
    for k in K_WINDOWS:
        for side in SIDES:
            mfe = pred[f"{side}_MFE_K{k}"]
            mae = pred[f"{side}_MAE_K{k}"]
            ratio = mfe / mae.replace(0, np.nan)
            thr = thresholds[f"K{k}"][side][THRESHOLD_Q]
            mask = (ratio >= thr).fillna(False)
            firing = pred.index[mask]
            log(f"  K={k} {side} q95 thr={thr:.4f} fires={len(firing)}")
            for ts in firing:
                if ts not in ts_to_idx:
                    continue
                rows.append(
                    {
                        "timestamp": ts,
                        "K": k,
                        "side": side,
                        "entry_idx": ts_to_idx[ts],
                        "entry_price": float(pred.loc[ts, "close"]),
                        "predicted_MFE": float(mfe.loc[ts]),
                        "predicted_MAE": float(mae.loc[ts]),
                        "cluster": int(cluster_labels.loc[ts, "cluster"]),
                    }
                )
    df = pd.DataFrame(rows)
    df["dir"] = df["side"].map({"LONG": 1, "SHORT": -1})
    log(f"  total entries (24 種 × q95): {len(df):,}")
    return df


def simulate_fixed_tp(
    entry_price: float,
    side: str,
    entry_idx: int,
    K: int,
    pct: float,
    pred_mfe: float,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
) -> tuple[float, int, bool]:
    """予測 MFE × pct で TP。届かなければ K bar 後 close で Time Exit。"""
    n = len(closes)
    end = min(entry_idx + K + 1, n)
    if end <= entry_idx + 1:
        return entry_price, entry_idx, False
    tp_diff = pred_mfe * pct
    if side == "LONG":
        tp_price = entry_price + tp_diff
        sl = slice(entry_idx + 1, end)
        hits = highs[sl] >= tp_price
    else:
        tp_price = entry_price - tp_diff
        sl = slice(entry_idx + 1, end)
        hits = lows[sl] <= tp_price
    if hits.any():
        first = int(np.argmax(hits))
        return float(tp_price), entry_idx + 1 + first, True
    return float(closes[end - 1]), end - 1, False


def simulate_trailing(
    entry_price: float,
    side: str,
    entry_idx: int,
    K: int,
    retrace: float,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
) -> tuple[float, int, bool]:
    """ピーク追従・retrace% で trailing stop。届かなければ K bar 後 close。"""
    n = len(closes)
    end = min(entry_idx + K + 1, n)
    if end <= entry_idx + 1:
        return entry_price, entry_idx, False
    if side == "LONG":
        peak = entry_price
        for i in range(entry_idx + 1, end):
            if highs[i] > peak:
                peak = highs[i]
            stop = peak * (1 - retrace)
            if lows[i] <= stop:
                return float(stop), i, True
        return float(closes[end - 1]), end - 1, False
    else:
        trough = entry_price
        for i in range(entry_idx + 1, end):
            if lows[i] < trough:
                trough = lows[i]
            stop = trough * (1 + retrace)
            if highs[i] >= stop:
                return float(stop), i, True
        return float(closes[end - 1]), end - 1, False


def simulate_time_exit(
    entry_price: float,
    entry_idx: int,
    n_bars: int,
    closes: np.ndarray,
) -> tuple[float, int, bool]:
    """N bar 経過で close 約定。"""
    n = len(closes)
    target = min(entry_idx + n_bars, n - 1)
    return float(closes[target]), target, False


def compute_pnl(
    entry_price: float,
    exit_price: float,
    direction: int,
) -> float:
    """PnL USD = POS_SIZE_BTC × (exit-entry) × dir − fee_roundtrip"""
    price_pnl = POS_SIZE_BTC * (exit_price - entry_price) * direction
    fee = (entry_price + exit_price) * POS_SIZE_BTC * FEE_RATE_MAKER  # 各サイドで Maker fee
    return price_pnl - fee


def simulate_all_strategies(
    df_entries: pd.DataFrame,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    label: str = "",
) -> list[dict]:
    """全 Entry × Exit 戦略グリッド (固定 TP × 4 + Trailing × 4 + Time × 2) でシミュレーション"""
    sim_records: list[dict] = []
    n_entries = len(df_entries)
    n_per_log = max(1, n_entries // 20)
    t_sim = time.time()
    for i, row in enumerate(df_entries.itertuples(index=False), 1):
        if i % n_per_log == 0:
            log(f"  [{label} {i:,}/{n_entries:,}] ({i/n_entries*100:.1f}%) elapsed={time.time()-t_sim:.1f}s")
        entry_price = row.entry_price
        side = row.side
        entry_idx = row.entry_idx
        K = row.K
        direction = row.dir
        pred_mfe = row.predicted_MFE

        for pct in TP_PCT_GRID:
            xp, xi, hit = simulate_fixed_tp(entry_price, side, entry_idx, K, pct, pred_mfe, highs, lows, closes)
            sim_records.append(dict(
                entry_ts=row.timestamp, K=K, side=side, cluster=row.cluster,
                exit_type="fixed_tp", exit_param=pct,
                exit_price=xp, exit_idx=xi, hit_tp=hit,
                pnl_usd=compute_pnl(entry_price, xp, direction),
            ))
        for retrace in TRAILING_PCT_GRID:
            xp, xi, hit = simulate_trailing(entry_price, side, entry_idx, K, retrace, highs, lows, closes)
            sim_records.append(dict(
                entry_ts=row.timestamp, K=K, side=side, cluster=row.cluster,
                exit_type="trailing", exit_param=retrace,
                exit_price=xp, exit_idx=xi, hit_tp=hit,
                pnl_usd=compute_pnl(entry_price, xp, direction),
            ))
        for n_bars in time_exit_n_bars(K):
            xp, xi, _ = simulate_time_exit(entry_price, entry_idx, n_bars, closes)
            sim_records.append(dict(
                entry_ts=row.timestamp, K=K, side=side, cluster=row.cluster,
                exit_type="time_exit", exit_param=n_bars,
                exit_price=xp, exit_idx=xi, hit_tp=False,
                pnl_usd=compute_pnl(entry_price, xp, direction),
            ))
    log(f"  [{label}] simulations done ({len(sim_records):,} records, elapsed={time.time()-t_sim:.1f}s)")
    return sim_records


def aggregate_results(df_sim: pd.DataFrame, n_months: float) -> pd.DataFrame:
    """cluster × (K, side) × exit_type × exit_param で集計。月次平均は n_months で除算。"""
    df_sim["entry_ts"] = pd.to_datetime(df_sim["entry_ts"])
    df_sim["month"] = df_sim["entry_ts"].dt.to_period("M").astype(str)
    agg = (
        df_sim.groupby(["cluster", "K", "side", "exit_type", "exit_param"], sort=False)
        .agg(
            n=("pnl_usd", "size"),
            pnl_total=("pnl_usd", "sum"),
            pnl_mean=("pnl_usd", "mean"),
            pnl_median=("pnl_usd", "median"),
            win_rate=("pnl_usd", lambda x: (x > 0).mean()),
        )
        .reset_index()
    )
    agg["pnl_monthly_avg"] = agg["pnl_total"] / n_months
    return agg


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log("=== Phase 4-b START (L-183 data snooping 解消) ===")

    # === ロード: train + test 両期間 ===
    log("=== load OHLC (train + test) ===")
    ohlc_tr, opens_tr, highs_tr, lows_tr, closes_tr, ts_to_idx_tr = load_ohlc_period(
        "2021-04-01 00:00:00", "2024-12-31 23:55:00"
    )
    ohlc_te, opens_te, highs_te, lows_te, closes_te, ts_to_idx_te = load_ohlc_period(
        "2025-01-01 00:00:00", "2025-12-31 23:55:00"
    )

    log("=== load predictions / clusters / thresholds ===")
    pred_train = pd.read_parquet(PREDICTIONS_TRAIN)
    pred_test = pd.read_parquet(PREDICTIONS_TEST)
    cluster_train = pd.read_parquet(CLUSTER_TRAIN)
    cluster_test = pd.read_parquet(CLUSTER_TEST)
    with open(THRESHOLDS) as f:
        thresholds = json.load(f)
    log(f"  pred_train: {pred_train.shape}, pred_test: {pred_test.shape}")
    log(f"  cluster_train: {cluster_train.shape}, cluster_test: {cluster_test.shape}")

    # === Step 1: train で entries + simulate + best 選定 (checklist 4b.1) ===
    log("=== Step 1: train entries + simulate + best 選定 ===")
    df_entries_train = extract_entries(pred_train, cluster_train, thresholds, ts_to_idx_tr)
    df_entries_train.to_parquet(OUT_DIR / "entry_candidates_train.parquet")
    log(f"saved entry_candidates_train.parquet ({len(df_entries_train):,} rows)")

    sim_train = simulate_all_strategies(df_entries_train, highs_tr, lows_tr, closes_tr, label="train")
    df_sim_train = pd.DataFrame(sim_train)
    df_sim_train.to_parquet(OUT_DIR / "exit_simulations_train.parquet")
    log("saved exit_simulations_train.parquet")

    log("aggregating train ...")
    n_months_train = (pd.Timestamp("2024-12-31") - pd.Timestamp("2021-04-01")).days / 30.44
    agg_train = aggregate_results(df_sim_train, n_months_train)
    agg_train.to_csv(OUT_DIR / "cluster_exit_pnl_summary_train.csv", index=False)
    log("saved cluster_exit_pnl_summary_train.csv")

    # cluster × (K, side) ごとに最良 Exit (train PnL のみで選定・L-183 #4)
    best_idx = agg_train.groupby(["cluster", "K", "side"], sort=False)["pnl_total"].idxmax()
    df_best = agg_train.loc[best_idx].reset_index(drop=True)
    df_best.to_csv(OUT_DIR / "cluster_best_exit_FROM_TRAIN.csv", index=False)
    log("saved cluster_best_exit_FROM_TRAIN.csv (train PnL で選定・checklist 4b.1)")

    # === Step 2: test 2025 で entries + simulate + apply (best 選定なし・checklist 4b.2) ===
    log("=== Step 2: test 2025 entries + simulate + apply (best 選定なし) ===")
    df_entries_test = extract_entries(pred_test, cluster_test, thresholds, ts_to_idx_te)
    df_entries_test.to_parquet(OUT_DIR / "entry_candidates.parquet")
    log(f"saved entry_candidates.parquet ({len(df_entries_test):,} rows)")

    sim_test = simulate_all_strategies(df_entries_test, highs_te, lows_te, closes_te, label="test")
    df_sim_test = pd.DataFrame(sim_test)
    df_sim_test.to_parquet(OUT_DIR / "exit_simulations.parquet")
    log("saved exit_simulations.parquet (test 2025・Phase 5 入力)")

    log("aggregating test 2025 ...")
    agg_test = aggregate_results(df_sim_test, 12.0)
    agg_test.to_csv(OUT_DIR / "cluster_exit_pnl_summary.csv", index=False)
    log("saved cluster_exit_pnl_summary.csv (test 2025 集計・best 選定なし)")

    elapsed = time.time() - t0
    log(f"=== Phase 4-b END (elapsed={elapsed/60:.2f} min) ===")

    write_summary(elapsed, df_sim_test, agg_test, df_best)


def write_summary(
    elapsed: float,
    df_sim: pd.DataFrame,
    agg: pd.DataFrame,
    df_best: pd.DataFrame,
) -> None:
    md = []
    md.append("# Phase 4-b — Exit シミュレーション (3 方式 × グリッド)\n\n")
    md.append(f"- 実行 TS: {TS}\n")
    md.append(f"- 所要: {elapsed/60:.2f} 分\n")
    md.append(f"- 採用 ML: Phase 3-b / クラスタ: k=4 (Phase 4-a)\n")
    md.append(f"- Entry 閾値: {THRESHOLD_Q}\n")
    md.append(f"- POS_SIZE_BTC: {POS_SIZE_BTC} / FEE_RATE_MAKER: {FEE_RATE_MAKER}\n")
    md.append(f"- シミュレーション件数: {len(df_sim):,}\n")
    md.append(f"- Entry 候補数: {df_sim['entry_ts'].nunique():,} 種 × Exit 11 = {len(df_sim):,}\n\n")
    md.append("## 再現コマンド\n\n")
    md.append("```\npython3 scripts/priority_rebuild/run_phase4_b.py\n```\n\n")

    md.append("## クラスタ × (K, side) ごとの最良 Exit\n\n")
    md.append("| cluster | K | side | exit_type | param | n | pnl_total ($) | pnl_mean ($) | win_rate | monthly_avg ($) |\n")
    md.append("|---|---|---|---|---|---|---|---|---|---|\n")
    for _, r in df_best.iterrows():
        md.append(
            f"| {int(r['cluster'])} | {int(r['K'])} | {r['side']} | {r['exit_type']} | "
            f"{r['exit_param']} | {int(r['n']):,} | {r['pnl_total']:,.0f} | "
            f"{r['pnl_mean']:.2f} | {r['win_rate']*100:.1f}% | {r['pnl_monthly_avg']:,.0f} |\n"
        )

    md.append("\n## クラスタごとの最良 Exit 合計 (全 K × side)\n\n")
    by_cluster = df_best.groupby("cluster").agg(
        pnl_total=("pnl_total", "sum"),
        n_entries=("n", "sum"),
        pnl_monthly_avg=("pnl_monthly_avg", "sum"),
    ).reset_index()
    md.append("| cluster | total entries | total PnL ($) | monthly_avg ($) |\n|---|---|---|---|\n")
    for _, r in by_cluster.iterrows():
        md.append(f"| {int(r['cluster'])} | {int(r['n_entries']):,} | {r['pnl_total']:,.0f} | {r['pnl_monthly_avg']:,.0f} |\n")

    md.append("\n## 合計 (全クラスタ × 全 K × 全 side)\n\n")
    total = df_best["pnl_total"].sum()
    n_total = int(df_best["n"].sum())
    monthly = total / 12.0
    md.append(f"- total entries: **{n_total:,}**\n")
    md.append(f"- total PnL: **${total:,.0f}**\n")
    md.append(f"- monthly_avg: **${monthly:,.0f}**\n")
    md.append(f"- vs 合格ライン $1,900/月: {'OK' if monthly >= 1900 else 'NG'}\n")
    md.append(f"- vs §1.6 撤退ライン $500/月: {'OK (Phase 3 進行可)' if monthly >= 500 else 'NG (ML 単独不合格)'}\n")

    md.append("\n## 注記\n\n")
    md.append("- 約定モデルは楽観 (TP 指値 fill 想定)。Phase 5 統合 Replay でより現実的に。\n")
    md.append("- Position 同時保有上限なし (指示書 §4)。Phase 5 で制限追加を検討。\n")
    md.append("- 上記合計は「クラスタ × (K, side) ごとの最良 Exit を全部足した」値。Phase 5 で同時保有衝突を解消するとさらに変化。\n")

    with open(OUT_DIR / "summary.md", "w") as f:
        f.write("".join(md))


if __name__ == "__main__":
    main()
