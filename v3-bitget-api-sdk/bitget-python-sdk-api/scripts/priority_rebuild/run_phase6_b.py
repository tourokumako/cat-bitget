#!/usr/bin/env python3
"""
run_phase6_b.py — ML Phase 6-b: 本テスト 2026 Q1 で End-to-End 検証

指示書: bitget-python-sdk-api/cc_ml_design_spec.md §5 Phase 6

処理パイプライン:
  1. 2026 Q1 ラベル parquet ロード
  2. Phase 3-b の 16 モデルで予測
  3. Phase 4-a と同じ派生特徴量 (26 次元) + k=4 KMeans
     ※ 一貫性のため test 2025 features で fit → 2026 Q1 features で predict
  4. Phase 4-b と同じ Exit 戦略 (cluster_best_exit.csv) で Entry 候補 × 1 Exit 抽出
  5. Phase 5 / 5-b と同じ Replay + cap=5/10/20 比較
  6. 月次 NET 集計 + §6 合格判定 (月次 $1,900 全月クリア)

入力:
  results/priority_rebuild/labels_mfe_mae_test_2026_q1.parquet  (Phase 6-a 出力)
  results/priority_rebuild/labels_mfe_mae_test_2025.parquet      (k-means fit 用)
  results/priority_rebuild/ml_phase3_b/models/lgbm_<label>.txt × 16
  results/priority_rebuild/ml_phase3_b/entry_thresholds.json
  results/priority_rebuild/ml_phase4_b/cluster_best_exit.csv
  data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv

出力 (results/priority_rebuild/ml_phase6_b/):
  phase6b_log_<TS>.txt
  predictions_2026q1.parquet
  cluster_labels_2026q1_k4.parquet
  entry_candidates_2026q1.parquet
  exit_simulations_2026q1.parquet
  trades_2026q1.parquet                  cluster best exit 適用後
  monthly_pnl_2026q1.csv                 cap=none/5/10/20 別月次
  summary.md                             §6 合格判定
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[2]
LABELS_DIR = REPO_ROOT / "results" / "priority_rebuild"
P3B_DIR = LABELS_DIR / "ml_phase3_b"
P4B_DIR = LABELS_DIR / "ml_phase4_b"
OUT_DIR = LABELS_DIR / "ml_phase6_b"

LABELS_TEST_2026Q1 = LABELS_DIR / "labels_mfe_mae_test_2026_q1.parquet"
LABELS_TEST_2025 = LABELS_DIR / "labels_mfe_mae_test_2025.parquet"
MODELS_DIR = P3B_DIR / "models"
THRESHOLDS_PATH = P3B_DIR / "entry_thresholds.json"
BEST_EXIT_PATH = P4B_DIR / "cluster_best_exit.csv"
OHLC_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d.csv"

LABEL_COLS = [
    f"{side}_{kind}_K{k}"
    for k in (12, 24, 48, 96)
    for side in ("LONG", "SHORT")
    for kind in ("MFE", "MAE")
]
META_COLS = ["close"]
K_WINDOWS = (12, 24, 48, 96)
SIDES = ("LONG", "SHORT")
THRESHOLD_Q = "q95"

POS_SIZE_BTC = 0.12
FEE_RATE_MAKER = 0.00014

K_CLUSTERS = 4  # Phase 4-a 採用
RANDOM_STATE = 42
POSITION_CAPS = (5, 10, 20)
THRESHOLD_PASS_MONTHLY = 1900.0

TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_PATH = OUT_DIR / f"phase6b_log_{TS}.txt"


def log(msg: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def predict_16_labels(X: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """Phase 3-b の 16 モデルで予測。"""
    pred = pd.DataFrame(index=X.index)
    for label in LABEL_COLS:
        model_path = MODELS_DIR / f"lgbm_{label}.txt"
        booster = lgb.Booster(model_file=str(model_path))
        pred[label] = booster.predict(X[feature_cols])
    return pred


def build_cluster_features(pred: pd.DataFrame) -> pd.DataFrame:
    """Phase 4-a と同じ 26 次元派生特徴量。"""
    feat = pred[LABEL_COLS].copy()
    eps = 1e-9
    for k in K_WINDOWS:
        for side in SIDES:
            mfe = pred[f"{side}_MFE_K{k}"]
            mae = pred[f"{side}_MAE_K{k}"]
            feat[f"{side}_ratio_K{k}"] = mfe / (mae + eps)
    for side in SIDES:
        feat[f"{side}_long_vs_short"] = pred[f"{side}_MFE_K96"] / (pred[f"{side}_MFE_K12"] + eps)
    return feat.fillna(0.0).replace([np.inf, -np.inf], 0.0)


def fit_kmeans_on_2025(scaler_class, k: int) -> tuple:
    """test 2025 の features で StandardScaler + KMeans を fit。"""
    log("  loading test 2025 for kmeans fit ...")
    df25 = pd.read_parquet(LABELS_TEST_2025)
    # 2025 の予測値: Phase 3-b の predictions_test2025.parquet を直接使う
    pred25 = pd.read_parquet(P3B_DIR / "predictions_test2025.parquet")
    feat25 = build_cluster_features(pred25)
    scaler = scaler_class()
    Xs = scaler.fit_transform(feat25.values)
    km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    km.fit(Xs)
    log(f"  kmeans fit on 2025 done (k={k} inertia={km.inertia_:.0f})")
    return scaler, km


def load_ohlc_2026q1() -> tuple:
    df = pd.read_csv(OHLC_CSV, parse_dates=["timestamp"])
    df = df.set_index("timestamp").sort_index()
    df = df.loc["2026-01-01 00:00:00":"2026-03-31 23:55:00"]
    opens = df["open"].to_numpy(dtype=np.float64)
    highs = df["high"].to_numpy(dtype=np.float64)
    lows = df["low"].to_numpy(dtype=np.float64)
    closes = df["close"].to_numpy(dtype=np.float64)
    ts_to_idx = {ts: i for i, ts in enumerate(df.index)}
    return df, opens, highs, lows, closes, ts_to_idx


def simulate_exit_for_entry(
    entry_price: float, side: str, entry_idx: int, K: int,
    exit_type: str, exit_param: float, pred_mfe: float,
    highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
) -> tuple[float, int]:
    """1 Entry 1 Exit シミュレーション → (exit_price, exit_idx)。Phase 4-b と同じロジック。"""
    n = len(closes)
    if exit_type == "time_exit":
        target = min(entry_idx + int(exit_param), n - 1)
        return float(closes[target]), target
    end = min(entry_idx + K + 1, n)
    if end <= entry_idx + 1:
        return entry_price, entry_idx
    if exit_type == "fixed_tp":
        tp_diff = pred_mfe * exit_param
        if side == "LONG":
            tp_price = entry_price + tp_diff
            sl = slice(entry_idx + 1, end)
            hits = highs[sl] >= tp_price
        else:
            tp_price = entry_price - tp_diff
            sl = slice(entry_idx + 1, end)
            hits = lows[sl] <= tp_price
        if hits.any():
            return float(tp_price), entry_idx + 1 + int(np.argmax(hits))
        return float(closes[end - 1]), end - 1
    # trailing
    if side == "LONG":
        peak = entry_price
        for i in range(entry_idx + 1, end):
            if highs[i] > peak:
                peak = highs[i]
            stop = peak * (1 - exit_param)
            if lows[i] <= stop:
                return float(stop), i
        return float(closes[end - 1]), end - 1
    else:
        trough = entry_price
        for i in range(entry_idx + 1, end):
            if lows[i] < trough:
                trough = lows[i]
            stop = trough * (1 + exit_param)
            if highs[i] >= stop:
                return float(stop), i
        return float(closes[end - 1]), end - 1


def compute_pnl(entry_price: float, exit_price: float, direction: int) -> float:
    price_pnl = POS_SIZE_BTC * (exit_price - entry_price) * direction
    fee = (entry_price + exit_price) * POS_SIZE_BTC * FEE_RATE_MAKER
    return price_pnl - fee


def replay_with_cap(df: pd.DataFrame, cap: int | None) -> pd.DataFrame:
    if cap is None:
        return df
    df = df.sort_values("entry_ts").reset_index(drop=True)
    n = len(df)
    taken = np.zeros(n, dtype=bool)
    active = []
    entry_ts = df["entry_ts"].values
    exit_ts = df["exit_ts"].values
    for i in range(n):
        active = [e for e in active if e > entry_ts[i]]
        if len(active) < cap:
            taken[i] = True
            active.append(exit_ts[i])
    return df[taken].copy()


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log("=== Phase 6-b START ===")

    # 1. 2026 Q1 ラベル parquet
    log("loading 2026 Q1 labels ...")
    df26 = pd.read_parquet(LABELS_TEST_2026Q1)
    log(f"  2026 Q1: {df26.shape} ({df26.index[0]} → {df26.index[-1]})")
    feature_cols = [c for c in df26.columns if c not in LABEL_COLS + META_COLS]
    log(f"  features: {len(feature_cols)} (expected 1432)")
    assert len(feature_cols) == 1432

    # 2. Phase 3-b 16 モデルで予測
    log("predicting with Phase 3-b 16 models ...")
    pred26 = predict_16_labels(df26, feature_cols)
    pred26["close"] = df26["close"].values
    pred26.to_parquet(OUT_DIR / "predictions_2026q1.parquet")
    log(f"saved predictions_2026q1.parquet ({pred26.shape})")

    # 3. KMeans (test 2025 で fit)
    log("fitting kmeans on test 2025 features ...")
    scaler, km = fit_kmeans_on_2025(StandardScaler, K_CLUSTERS)
    feat26 = build_cluster_features(pred26)
    Xs26 = scaler.transform(feat26.values)
    clusters_26 = km.predict(Xs26)
    df_cl = pd.DataFrame({"cluster": clusters_26}, index=pred26.index)
    df_cl.to_parquet(OUT_DIR / "cluster_labels_2026q1_k4.parquet")
    log(f"saved cluster_labels_2026q1_k4.parquet (cluster distribution: {np.bincount(clusters_26, minlength=K_CLUSTERS)})")

    # 4. Entry 候補抽出 (q95)
    log("loading thresholds + best exit ...")
    with open(THRESHOLDS_PATH) as f:
        thresholds = json.load(f)
    df_best = pd.read_csv(BEST_EXIT_PATH)
    log(f"  best exit table: {df_best.shape}")

    log("loading OHLC 2026 Q1 ...")
    ohlc, opens, highs, lows, closes, ts_to_idx = load_ohlc_2026q1()
    log(f"  ohlc 2026Q1: {ohlc.shape}")

    log("extracting entries (q95) ...")
    entry_rows = []
    for k in K_WINDOWS:
        for side in SIDES:
            mfe = pred26[f"{side}_MFE_K{k}"]
            mae = pred26[f"{side}_MAE_K{k}"]
            ratio = mfe / mae.replace(0, np.nan)
            thr = thresholds[f"K{k}"][side][THRESHOLD_Q]
            mask = (ratio >= thr).fillna(False)
            firing = pred26.index[mask]
            log(f"  K={k} {side} q95 fires={len(firing)}")
            for ts in firing:
                if ts not in ts_to_idx:
                    continue
                entry_rows.append(
                    dict(
                        timestamp=ts, K=k, side=side,
                        entry_idx=ts_to_idx[ts],
                        entry_price=float(pred26.loc[ts, "close"]),
                        predicted_MFE=float(mfe.loc[ts]),
                        predicted_MAE=float(mae.loc[ts]),
                        cluster=int(df_cl.loc[ts, "cluster"]),
                    )
                )
    df_entries = pd.DataFrame(entry_rows)
    df_entries["dir"] = df_entries["side"].map({"LONG": 1, "SHORT": -1})
    df_entries.to_parquet(OUT_DIR / "entry_candidates_2026q1.parquet")
    log(f"saved entry_candidates_2026q1.parquet ({len(df_entries):,} rows)")

    # 5. cluster best exit でフィルタしながら Exit シミュレーション
    log("applying cluster best exit ...")
    best_map = {
        (int(r.cluster), int(r.K), r.side): (r.exit_type, float(r.exit_param))
        for _, r in df_best.iterrows()
    }
    trade_records = []
    for row in df_entries.itertuples(index=False):
        key = (row.cluster, row.K, row.side)
        if key not in best_map:
            continue
        exit_type, exit_param = best_map[key]
        xp, xi = simulate_exit_for_entry(
            row.entry_price, row.side, row.entry_idx, row.K,
            exit_type, exit_param, row.predicted_MFE,
            highs, lows, closes,
        )
        pnl = compute_pnl(row.entry_price, xp, row.dir)
        trade_records.append(
            dict(
                entry_ts=row.timestamp, K=row.K, side=row.side, cluster=row.cluster,
                exit_type=exit_type, exit_param=exit_param,
                entry_price=row.entry_price, exit_price=xp,
                exit_idx=xi, pnl_usd=pnl,
            )
        )
    df_trades = pd.DataFrame(trade_records)
    idx_to_ts = list(ts_to_idx.keys())
    df_trades["exit_ts"] = [idx_to_ts[min(xi, len(idx_to_ts) - 1)] for xi in df_trades["exit_idx"]]
    df_trades["entry_ts"] = pd.to_datetime(df_trades["entry_ts"])
    df_trades["exit_ts"] = pd.to_datetime(df_trades["exit_ts"])
    df_trades.to_parquet(OUT_DIR / "trades_2026q1.parquet")
    log(f"saved trades_2026q1.parquet ({len(df_trades):,} rows)")

    # 6. cap=none/5/10/20 で月次集計
    log("computing monthly PnL for each cap ...")
    all_monthly = []
    for cap_label, cap in [("none", None)] + [(str(c), c) for c in POSITION_CAPS]:
        df_use = replay_with_cap(df_trades, cap)
        df_use = df_use.copy()
        df_use["month"] = df_use["entry_ts"].dt.to_period("M").astype(str)
        agg = (
            df_use.groupby("month", sort=True)
            .agg(
                n=("pnl_usd", "size"),
                pnl_sum=("pnl_usd", "sum"),
                win_rate=("pnl_usd", lambda x: (x > 0).mean()),
            )
            .reset_index()
        )
        agg["cap"] = cap_label
        agg["pass_1900"] = agg["pnl_sum"] >= THRESHOLD_PASS_MONTHLY
        all_monthly.append(agg)
        log(f"  cap={cap_label}: n={len(df_use):,} total_pnl=${df_use['pnl_usd'].sum():,.0f} pass_months={int(agg['pass_1900'].sum())}/{len(agg)}")
    df_monthly = pd.concat(all_monthly, ignore_index=True)
    df_monthly.to_csv(OUT_DIR / "monthly_pnl_2026q1.csv", index=False)
    log("saved monthly_pnl_2026q1.csv")

    elapsed = time.time() - t0
    log(f"=== Phase 6-b END (elapsed={elapsed/60:.2f} min) ===")
    write_summary(elapsed, df_trades, df_monthly)


def write_summary(elapsed: float, df_trades: pd.DataFrame, df_monthly: pd.DataFrame) -> None:
    md = []
    md.append("# Phase 6-b — 本テスト 2026 Q1 End-to-End 検証\n\n")
    md.append(f"- 実行 TS: {TS}\n")
    md.append(f"- 所要: {elapsed/60:.2f} 分\n")
    md.append(f"- 採用 ML: Phase 3-b / k=4 / cluster_best_exit (Phase 4-b)\n\n")
    md.append("## 再現コマンド\n\n")
    md.append("```\npython3 scripts/priority_rebuild/run_phase6_b.py\n```\n\n")

    md.append("## 全体 (no cap)\n\n")
    md.append(f"- 総 trades: **{len(df_trades):,}**\n")
    md.append(f"- 総 PnL: **${df_trades['pnl_usd'].sum():,.0f}**\n")
    md.append(f"- 月次平均 (Q1=3ヶ月): **${df_trades['pnl_usd'].sum()/3:,.0f}**\n")
    md.append(f"- Win rate: {(df_trades['pnl_usd']>0).mean()*100:.1f}%\n\n")

    md.append("## §6 合格判定 (cap 別月次)\n\n")
    md.append("| cap | n | total PnL ($) | monthly avg ($) | pass $1,900 (months) |\n|---|---|---|---|---|\n")
    for cap_label in ["none", "5", "10", "20"]:
        sub = df_monthly[df_monthly.cap == cap_label]
        total = sub["pnl_sum"].sum()
        n_months = len(sub)
        n_total = int(sub["n"].sum())
        pass_n = int(sub["pass_1900"].sum())
        avg = total / max(1, n_months)
        md.append(f"| {cap_label} | {n_total:,} | {total:,.0f} | {avg:,.0f} | {pass_n}/{n_months} |\n")

    md.append("\n## 月次内訳 (全 cap)\n\n")
    md.append("| month | cap | n | pnl_sum ($) | win | pass $1,900 |\n|---|---|---|---|---|---|\n")
    for _, r in df_monthly.iterrows():
        md.append(
            f"| {r['month']} | {r['cap']} | {int(r['n']):,} | {r['pnl_sum']:,.0f} | "
            f"{r['win_rate']*100:.1f}% | {'✅' if r['pass_1900'] else '❌'} |\n"
        )
    md.append("\n## §1.5 過学習対策チェック\n\n")
    md.append("- 2026 Q1 は本テスト (Phase 6 以前未使用) → 過学習リスクの最終確認\n")
    md.append("- 仮テスト (2025) と比較: Phase 5 月次平均 vs Phase 6-b 月次平均\n")
    md.append("- 著しい乖離があれば過学習の兆候\n")

    with open(OUT_DIR / "summary.md", "w") as f:
        f.write("".join(md))


if __name__ == "__main__":
    main()
