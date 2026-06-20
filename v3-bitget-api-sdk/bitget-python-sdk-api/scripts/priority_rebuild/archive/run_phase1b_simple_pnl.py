"""run_phase1b_simple_pnl.py — Phase 1-b 簡易 PnL チェック (naive Replay)

指示書: .claude/instructions/2026-05-21_phase1b_simple_pnl_check.md
発注: Web Claude (PM) / 実装: CC (2026-05-21)

Phase 1-a 予測値 (predictions_test_2025.parquet) を入力に、K=6/12/24 並列 naive 売買 simulation。
LONG only・1 ポジ 0.01 BTC・max 12 同時 (合計 0.12 BTC)・Maker fee 0.014%×2・Funding 適用なし。

Entry: bar[i].close 時の `pred_MFE / pred_MAE >= 1.5` → bar[i+1].open で fill
Exit (next-bar から K bars 走査・同 bar 内 SL 優先):
  - bar.low ≤ entry × (1 - pred_MAE/100)             → SL fill at SL_price
  - bar.high ≥ entry × (1 + pred_MFE × 0.8/100)      → TP fill at TP_price
  - K bars 経過・未約定                                → bar[i+1+K-1].close で時間 Exit

実行: python3 scripts/priority_rebuild/run_phase1b_simple_pnl.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

PREDS_PATH = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase1a_rmse" / "predictions_test_2025.parquet"
LABELS_PATH = REPO_ROOT / "results" / "priority_rebuild" / "labels_mfe_mae_pct_test_2025.parquet"
OHLC_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase1b_simple_pnl"

K_TARGETS = (6, 12, 24)
RATIO_THRESHOLD = 1.5
POS_BTC = 0.01
MAX_ACTIVE = 12
POS_BTC_CAP = 0.12
FEE_ROUND_TRIP_PCT = 0.014 * 2  # 0.028% (Maker × 2)


def log_line(log_f, msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    log_f.write(line + "\n")
    log_f.flush()


def load_inputs(log_f):
    """predictions / labels (ATR) / OHLC を load・ts 整合 verify."""
    log_line(log_f, f"loading predictions: {PREDS_PATH.relative_to(REPO_ROOT)}")
    preds = pd.read_parquet(PREDS_PATH)
    log_line(log_f, f"  shape={preds.shape} ts {preds.index.min()} .. {preds.index.max()}")

    log_line(log_f, f"loading atr14_pct__5m from labels parquet")
    atr = pd.read_parquet(LABELS_PATH, columns=["atr14_pct__5m"])
    assert atr.index.equals(preds.index), "ATR labels index と predictions index 不一致"

    log_line(log_f, f"loading OHLC: {OHLC_PATH.relative_to(REPO_ROOT)}")
    ohlc = pd.read_csv(OHLC_PATH, parse_dates=["timestamp"]).set_index("timestamp")
    ohlc_2025 = ohlc.loc["2025-01-01":"2025-12-31 23:55:00"]
    log_line(log_f, f"  OHLC 2025 rows={len(ohlc_2025):,} (期待 105,120)")

    assert ohlc_2025.index.equals(preds.index), \
        f"OHLC ts と predictions ts 不一致: ohlc[0]={ohlc_2025.index[0]} preds[0]={preds.index[0]}"
    return preds, atr, ohlc_2025


def simulate_one_k(
    K: int,
    preds: pd.DataFrame,
    open_arr: np.ndarray,
    high_arr: np.ndarray,
    low_arr: np.ndarray,
    close_arr: np.ndarray,
    ts_arr: np.ndarray,
) -> dict:
    """1 K の naive simulation. trades・active_max・entry_signal_ts を返す."""
    n = len(open_arr)
    mfe = preds[f"LONG_MFE_pct_K{K}"].to_numpy()
    mae = preds[f"LONG_MAE_pct_K{K}"].to_numpy()
    # mae > 0 確認 (Phase 1-a predictions describe で min ≥ 0.14)
    assert (mae > 0).all(), f"K{K}: pred_MAE に 0 以下が含まれる"
    ratio = mfe / mae

    trades: list[dict] = []
    # active list: dict(entry_i, ex_max_i, entry_price, tp_price, sl_price)
    active: list[dict] = []
    entry_signal_ts: list = []
    active_count_max = 0
    sum_btc_max = 0.0

    # 末尾 K+1 bar は Entry できない (Exit 走査範囲確保)
    for i in range(n):
        # ---- Step 1: 既存 active position の Exit 判定 (この bar i で) ----
        survivors: list[dict] = []
        for pos in active:
            ei = pos["entry_i"]
            if i <= ei:
                # entry bar 当日 (i == ei は fill 直後・bar の中で評価しない)
                survivors.append(pos)
                continue
            hi, lo = high_arr[i], low_arr[i]
            ep, tp, sl = pos["entry_price"], pos["tp_price"], pos["sl_price"]
            ex_max = pos["ex_max_i"]

            exit_price = None
            exit_reason = None
            if lo <= sl:  # SL 優先 (保守的)
                exit_price = sl
                exit_reason = "SL"
            elif hi >= tp:
                exit_price = tp
                exit_reason = "TP"
            elif i >= ex_max:
                exit_price = close_arr[i]
                exit_reason = "TIME"

            if exit_price is not None:
                pnl_pct = (exit_price - ep) / ep * 100.0 - FEE_ROUND_TRIP_PCT
                pnl_usd = pnl_pct / 100.0 * ep * POS_BTC
                trades.append({
                    "entry_ts": ts_arr[ei],
                    "exit_ts": ts_arr[i],
                    "entry_price": float(ep),
                    "exit_price": float(exit_price),
                    "exit_reason": exit_reason,
                    "pnl_pct": float(pnl_pct),
                    "pnl_usd": float(pnl_usd),
                    "hold_bars": int(i - ei),
                })
            else:
                survivors.append(pos)
        active = survivors

        # ---- Step 2: Entry シグナル判定 (current bar i の予測値) ----
        if i + 1 < n and ratio[i] >= RATIO_THRESHOLD and len(active) < MAX_ACTIVE:
            entry_i = i + 1
            ep = float(open_arr[entry_i])
            pmfe = float(mfe[i])
            pmae = float(mae[i])
            tp = ep * (1.0 + pmfe * 0.8 / 100.0)
            sl = ep * (1.0 - pmae / 100.0)
            ex_max = entry_i + K
            active.append({
                "entry_i": entry_i,
                "ex_max_i": ex_max,
                "entry_price": ep,
                "tp_price": tp,
                "sl_price": sl,
            })
            entry_signal_ts.append(ts_arr[i])

        # ---- Step 3: ポジション上限 verify ----
        active_count_max = max(active_count_max, len(active))
        sum_btc = len(active) * POS_BTC
        sum_btc_max = max(sum_btc_max, sum_btc)
        assert sum_btc <= POS_BTC_CAP + 1e-9, \
            f"K{K}: sum_btc={sum_btc} > {POS_BTC_CAP} at i={i} (Prime Directive 違反)"

    # 末尾未約定は close で強制 Exit
    for pos in active:
        ei = pos["entry_i"]
        last_idx = min(pos["ex_max_i"], n - 1)
        ep = pos["entry_price"]
        exit_price = float(close_arr[last_idx])
        pnl_pct = (exit_price - ep) / ep * 100.0 - FEE_ROUND_TRIP_PCT
        pnl_usd = pnl_pct / 100.0 * ep * POS_BTC
        trades.append({
            "entry_ts": ts_arr[ei],
            "exit_ts": ts_arr[last_idx],
            "entry_price": float(ep),
            "exit_price": exit_price,
            "exit_reason": "FORCED_END",
            "pnl_pct": float(pnl_pct),
            "pnl_usd": float(pnl_usd),
            "hold_bars": int(last_idx - ei),
        })

    return {
        "trades": trades,
        "active_count_max": active_count_max,
        "sum_btc_max": sum_btc_max,
        "entry_signal_ts": entry_signal_ts,
    }


def aggregate_monthly(trades: list[dict]) -> pd.DataFrame:
    """trades を exit_ts の月でグループ化し、月次集計."""
    if not trades:
        return pd.DataFrame(columns=["month", "n_trades", "net_pnl_usd", "win_rate", "avg_pnl_usd"])
    df = pd.DataFrame(trades)
    df["exit_month"] = pd.to_datetime(df["exit_ts"]).dt.to_period("M").astype(str)
    out = df.groupby("exit_month").agg(
        n_trades=("pnl_usd", "count"),
        net_pnl_usd=("pnl_usd", "sum"),
        win_rate=("pnl_usd", lambda x: float((x > 0).mean())),
        avg_pnl_usd=("pnl_usd", "mean"),
    ).reset_index().rename(columns={"exit_month": "month"})
    return out


def daily_entry_frequency(entry_signal_ts: list) -> pd.DataFrame:
    if not entry_signal_ts:
        return pd.DataFrame(columns=["date", "n_entries"])
    s = pd.Series(1, index=pd.to_datetime(entry_signal_ts))
    daily = s.resample("D").sum()
    return pd.DataFrame({"date": daily.index.strftime("%Y-%m-%d"), "n_entries": daily.values})


def judge_k12(monthly: pd.DataFrame, entries_per_day_avg: float) -> tuple[str, dict]:
    """K=12 主判定 (指示書 §5.1)."""
    plus_months = int((monthly["net_pnl_usd"] > 0).sum())
    annual_net = float(monthly["net_pnl_usd"].sum())
    cond_1 = plus_months >= 6
    cond_2 = annual_net > 0
    cond_3 = 5.0 <= entries_per_day_avg <= 50.0
    all_pass = cond_1 and cond_2 and cond_3
    return ("PASS" if all_pass else "FAIL"), {
        "plus_months": plus_months,
        "annual_net_usd": annual_net,
        "entries_per_day_avg": entries_per_day_avg,
        "cond_1_plus_months_ge_6": bool(cond_1),
        "cond_2_annual_net_positive": bool(cond_2),
        "cond_3_freq_in_5_50": bool(cond_3),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = OUT_DIR / "execution_log.txt"
    with log_path.open("w", encoding="utf-8") as log_f:
        log_line(log_f, "START phase1b_simple_pnl")
        log_line(log_f, f"cwd={Path.cwd()} repo_root={REPO_ROOT}")

        t0 = time.time()
        preds, atr, ohlc_2025 = load_inputs(log_f)

        open_arr = ohlc_2025["open"].to_numpy(dtype=np.float64)
        high_arr = ohlc_2025["high"].to_numpy(dtype=np.float64)
        low_arr = ohlc_2025["low"].to_numpy(dtype=np.float64)
        close_arr = ohlc_2025["close"].to_numpy(dtype=np.float64)
        ts_arr = ohlc_2025.index.to_numpy()

        atr_all_median = float(atr["atr14_pct__5m"].median())
        log_line(log_f, f"ATR all median = {atr_all_median:.6f}")

        per_k_result: dict[int, dict] = {}
        per_k_judge: dict[str, dict] = {}
        sum_btc_global_max = 0.0
        active_count_global_max = 0

        for K in K_TARGETS:
            log_line(log_f, f"--- simulate K={K} ---")
            tk = time.time()
            r = simulate_one_k(K, preds, open_arr, high_arr, low_arr, close_arr, ts_arr)
            elapsed = time.time() - tk
            n_trades = len(r["trades"])
            log_line(log_f, f"  K={K} done in {elapsed:.1f}s | n_trades={n_trades:,} "
                            f"active_max={r['active_count_max']} sum_btc_max={r['sum_btc_max']:.4f}")
            sum_btc_global_max = max(sum_btc_global_max, r["sum_btc_max"])
            active_count_global_max = max(active_count_global_max, r["active_count_max"])

            # 月次集計
            monthly = aggregate_monthly(r["trades"])
            monthly.to_csv(OUT_DIR / f"monthly_pnl_K{K}.csv", index=False)

            # trade log
            tdf = pd.DataFrame(r["trades"])
            tdf.to_parquet(OUT_DIR / f"trade_log_K{K}.parquet")

            # 発火頻度
            freq = daily_entry_frequency(r["entry_signal_ts"])
            freq.to_csv(OUT_DIR / f"entry_frequency_K{K}.csv", index=False)
            entries_per_day_avg = float(freq["n_entries"].mean()) if len(freq) else 0.0

            judgment, detail = judge_k12(monthly, entries_per_day_avg)
            per_k_judge[f"K{K}"] = {
                "judgment": judgment,
                "n_trades": n_trades,
                "active_count_max": r["active_count_max"],
                "sum_btc_max": r["sum_btc_max"],
                "entries_per_day_avg": entries_per_day_avg,
                **detail,
            }
            log_line(log_f, f"  K={K} judgment: {judgment} (plus_months={detail['plus_months']}/12 "
                            f"annual_net={detail['annual_net_usd']:.2f} entries/day={entries_per_day_avg:.2f})")

            per_k_result[K] = r

        # ATR dominance (K=12 主判定基準・観察 2 対応)
        k12_entry_ts = per_k_result[12]["entry_signal_ts"]
        if k12_entry_ts:
            entry_ts_set = pd.DatetimeIndex(k12_entry_ts)
            atr_entry_median = float(atr.loc[entry_ts_set, "atr14_pct__5m"].median())
            X = atr_entry_median / atr_all_median if atr_all_median > 0 else float("nan")
        else:
            atr_entry_median = float("nan")
            X = float("nan")
        log_line(log_f, f"ATR dominance: entry_median={atr_entry_median:.6f} all_median={atr_all_median:.6f} X={X:.4f}")

        # GO/NO-GO 総合判定 (K=12 主)
        k12_judge = per_k_judge["K12"]["judgment"]
        atr_warn = False if not np.isfinite(X) else (X > 1.5)
        atr_stop = False if not np.isfinite(X) else (X > 2.0)

        if k12_judge == "PASS" and not atr_stop:
            go = "GO"
            recovery = "Phase 1-c 指示書 (full 枠) 発注へ"
        elif k12_judge == "PASS" and atr_stop:
            go = "NO-GO"
            recovery = "Phase 1-a 立て直し協議 (ATR dominance X > 2.0・ATR_pct を blacklist 入れて再学習検討)"
        else:
            d12 = per_k_judge["K12"]
            all_minus = (d12["plus_months"] == 0)
            if all_minus:
                go = "NO-GO"
                recovery = "Phase 1-a 立て直し協議 (K=12 で 12 ヶ月全マイナス)"
            elif d12["cond_3_freq_in_5_50"] is False:
                go = "CONDITIONAL"
                recovery = f"発火頻度 {d12['entries_per_day_avg']:.2f} → 閾値 1.5 を {'1.3' if d12['entries_per_day_avg'] < 5 else '2.0'} に変えて再 simulation (1 回まで)"
            else:
                go = "NO-GO"
                recovery = "Phase 1-c へ進む (PnL/Sharpe で改善見込み・annual_net マイナス or plus_months<6)"

        summary = {
            "phase": "phase1b_simple_pnl",
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "K_targets": list(K_TARGETS),
            "ratio_threshold": RATIO_THRESHOLD,
            "position_size_btc": POS_BTC,
            "max_active": MAX_ACTIVE,
            "fee_round_trip_pct": FEE_ROUND_TRIP_PCT,
            "position_sum_btc_global_max": sum_btc_global_max,
            "active_count_global_max": active_count_global_max,
            "atr_all_median": atr_all_median,
            "atr_entry_median_K12": atr_entry_median,
            "atr_dominance_X": X,
            "atr_dominance_judgment": (
                "STOP (X > 2.0)" if atr_stop else
                "WARN (1.5 < X <= 2.0)" if atr_warn else
                "OK (X <= 1.5)"
            ),
            "per_k": per_k_judge,
            "go_judgment": go,
            "recovery_path": recovery,
        }
        (OUT_DIR / "summary_judgment.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

        log_line(log_f, f"GO judgment: {go}")
        log_line(log_f, f"recovery_path: {recovery}")
        log_line(log_f, f"END phase1b_simple_pnl total elapsed={time.time()-t0:.1f}s")

    print(f"\n=== DONE ===\nout_dir = {OUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
