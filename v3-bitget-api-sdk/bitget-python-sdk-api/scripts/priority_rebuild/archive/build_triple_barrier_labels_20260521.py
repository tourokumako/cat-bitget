"""build_triple_barrier_labels.py — Phase 1-c Triple Barrier 3-class ラベル生成

指示書: .claude/instructions/2026-05-21_phase1c_triple_barrier_multiclass.md §4.2

各 5m bar t について K bars 以内に以下のどれが先に起きるかを 3-class で分類:
  TP   (2): high[t+j] ≥ close[t] × (1 + ATR_pct[t] × TP_MULT / 100)
  SL   (0): low[t+j]  ≤ close[t] × (1 - ATR_pct[t] × SL_MULT / 100)
  TIME (1): K bars 経過まで両 barrier 未到達
同 bar 内両 hit 時は SL 優先 (保守的・Phase 1-b と同方針)

入力:
  - labels_mfe_mae_pct_{train_2021_2024,test_2025}.parquet (atr14_pct__5m + close 含む)
  - BTC CSV (high / low 取得用)

出力:
  - labels_triple_barrier_{train_2021_2024,test_2025}.parquet (各 K のラベル列 + atr14_pct__5m 等)
  - label_distribution.csv (7 K × 3-class %)
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

LABELS_TRAIN = REPO_ROOT / "results" / "priority_rebuild" / "labels_mfe_mae_pct_train_2021_2024.parquet"
LABELS_TEST = REPO_ROOT / "results" / "priority_rebuild" / "labels_mfe_mae_pct_test_2025.parquet"
OHLC_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase1c_triple_barrier"

K_TARGETS = (6, 12, 24, 48, 96, 144, 288)

# まこさん 2026-05-21 確定: 初期は TP=2.0 / SL=1.5 (RR 4:3)
# K=288 で TIME < 5% なら代替 A (TP=1.5/SL=1.0) → 代替 B (TP=1.0/SL=0.8) の順
TP_MULT = 2.0
SL_MULT = 1.5

# 3-class encoding
LABEL_SL = 0
LABEL_TIME = 1
LABEL_TP = 2


def log_line(log_f, msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    log_f.write(line + "\n")
    log_f.flush()


def load_inputs(log_f, parq_path: Path) -> pd.DataFrame:
    """labels parquet (atr + close + maint) + OHLC (high/low) を merge."""
    log_line(log_f, f"loading {parq_path.relative_to(REPO_ROOT)}")
    keep_cols = ["atr14_pct__5m", "close", "is_maintenance"]
    df = pd.read_parquet(parq_path, columns=keep_cols)
    log_line(log_f, f"  rows={len(df):,} ts {df.index.min()} .. {df.index.max()}")

    log_line(log_f, f"merging OHLC high/low from {OHLC_PATH.name}")
    ohlc = pd.read_csv(OHLC_PATH, parse_dates=["timestamp"]).set_index("timestamp")
    ohlc_sub = ohlc.loc[df.index, ["high", "low"]]
    df = df.join(ohlc_sub)
    assert df["high"].notna().all() and df["low"].notna().all(), "OHLC merge で NaN 発生"
    log_line(log_f, f"  merged shape={df.shape}")
    return df


def build_labels_for_k(
    K: int,
    close: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    atr_pct: np.ndarray,
    tp_mult: float,
    sl_mult: float,
) -> np.ndarray:
    """1 K の Triple Barrier ラベル配列を返す.

    末尾 K bars は NaN (label=-1) → 後で drop 対象。
    """
    n = len(close)
    labels = np.full(n, -1, dtype=np.int8)  # -1 = invalid (末尾)

    # barrier price (各 bar i ごと・shape (n,))
    tp_price = close * (1 + atr_pct * tp_mult / 100.0)
    sl_price = close * (1 - atr_pct * sl_mult / 100.0)

    for i in range(n - K):
        tp = tp_price[i]
        sl = sl_price[i]
        fut_low = low[i + 1 : i + 1 + K]
        fut_high = high[i + 1 : i + 1 + K]
        sl_hit = fut_low <= sl
        tp_hit = fut_high >= tp
        sl_any = sl_hit.any()
        tp_any = tp_hit.any()
        if not sl_any and not tp_any:
            labels[i] = LABEL_TIME
            continue
        if sl_any and not tp_any:
            labels[i] = LABEL_SL
            continue
        if tp_any and not sl_any:
            labels[i] = LABEL_TP
            continue
        # 両 hit: 先に touch する方を採用 (同 bar なら SL 優先)
        sl_first = int(sl_hit.argmax())
        tp_first = int(tp_hit.argmax())
        if sl_first <= tp_first:
            labels[i] = LABEL_SL
        else:
            labels[i] = LABEL_TP
    return labels


def process_dataset(log_f, parq_path: Path, tag: str, tp_mult: float, sl_mult: float) -> pd.DataFrame:
    df = load_inputs(log_f, parq_path)

    close = df["close"].to_numpy(dtype=np.float64)
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    atr_pct = df["atr14_pct__5m"].to_numpy(dtype=np.float64)

    out = df[["atr14_pct__5m", "close", "is_maintenance"]].copy()

    for K in K_TARGETS:
        t0 = time.time()
        labels = build_labels_for_k(K, close, high, low, atr_pct, tp_mult, sl_mult)
        out[f"triple_barrier_K{K}"] = labels
        n_valid = int((labels >= 0).sum())
        n_sl = int((labels == LABEL_SL).sum())
        n_time = int((labels == LABEL_TIME).sum())
        n_tp = int((labels == LABEL_TP).sum())
        elapsed = time.time() - t0
        log_line(
            log_f,
            f"  [{tag}] K={K}: SL={n_sl:,} ({n_sl/n_valid*100:.1f}%) "
            f"TIME={n_time:,} ({n_time/n_valid*100:.1f}%) "
            f"TP={n_tp:,} ({n_tp/n_valid*100:.1f}%) | "
            f"valid={n_valid:,} ({elapsed:.1f}s)",
        )

    return out


def aggregate_distribution(train_df: pd.DataFrame, test_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for K in K_TARGETS:
        col = f"triple_barrier_K{K}"
        for tag, df in [("train_2021_2024", train_df), ("test_2025", test_df)]:
            s = df[col]
            valid = s[s >= 0]
            total = len(valid)
            if total == 0:
                continue
            n_sl = int((valid == LABEL_SL).sum())
            n_time = int((valid == LABEL_TIME).sum())
            n_tp = int((valid == LABEL_TP).sum())
            rows.append({
                "dataset": tag,
                "K": K,
                "n_valid": total,
                "SL_pct": n_sl / total * 100,
                "TIME_pct": n_time / total * 100,
                "TP_pct": n_tp / total * 100,
                "SL_n": n_sl,
                "TIME_n": n_time,
                "TP_n": n_tp,
            })
    return pd.DataFrame(rows)


def check_stop_condition(dist_df: pd.DataFrame, log_f) -> list[str]:
    """1 クラス 80% 超 or 5% 未満なら STOP 候補."""
    violations = []
    for _, row in dist_df.iterrows():
        for cls in ["SL_pct", "TIME_pct", "TP_pct"]:
            v = float(row[cls])
            if v > 80.0 or v < 5.0:
                msg = f"[{row['dataset']}] K={row['K']} {cls}={v:.1f}% (基準: 5% ≤ x ≤ 80%)"
                violations.append(msg)
                log_line(log_f, f"  ⚠️ STOP 候補: {msg}")
    return violations


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = OUT_DIR / "execution_log.txt"
    with log_path.open("w", encoding="utf-8") as log_f:
        log_line(log_f, "START build_triple_barrier_labels")
        log_line(log_f, f"TP_MULT={TP_MULT} SL_MULT={SL_MULT} (RR={TP_MULT}:{SL_MULT})")
        log_line(log_f, f"K_TARGETS={K_TARGETS}")

        t0 = time.time()
        train_df = process_dataset(log_f, LABELS_TRAIN, "train", TP_MULT, SL_MULT)
        test_df = process_dataset(log_f, LABELS_TEST, "test_2025", TP_MULT, SL_MULT)

        # 保存
        out_train = OUT_DIR / "labels_triple_barrier_train_2021_2024.parquet"
        out_test = OUT_DIR / "labels_triple_barrier_test_2025.parquet"
        train_df.to_parquet(out_train)
        test_df.to_parquet(out_test)
        log_line(log_f, f"saved {out_train.name} ({len(train_df):,} rows)")
        log_line(log_f, f"saved {out_test.name} ({len(test_df):,} rows)")

        # 分布集計
        dist_df = aggregate_distribution(train_df, test_df)
        dist_path = OUT_DIR / "label_distribution.csv"
        dist_df.to_csv(dist_path, index=False)
        log_line(log_f, f"saved {dist_path.name}")

        # STOP 条件 check
        violations = check_stop_condition(dist_df, log_f)
        if violations:
            log_line(log_f, f"⚠️ STOP 候補 {len(violations)} 件: 代替 multiplier 検討要")
        else:
            log_line(log_f, "✅ 分布健全 (5% ≤ all classes ≤ 80%)")

        log_line(log_f, f"END build_triple_barrier_labels total={time.time()-t0:.1f}s")

    print(f"\n=== DONE ===")
    print(f"out_dir = {OUT_DIR.relative_to(REPO_ROOT)}")
    print(f"label_distribution.csv 概要:")
    print(dist_df.round(2).to_string(index=False))
    return 0 if not violations else 2


if __name__ == "__main__":
    sys.exit(main())
