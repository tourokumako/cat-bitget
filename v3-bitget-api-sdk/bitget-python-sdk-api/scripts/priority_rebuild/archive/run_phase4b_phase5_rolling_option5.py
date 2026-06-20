#!/usr/bin/env python3
"""
Phase 4-b Exit設計 + Phase 5 Replay — rolling 365 × Option 5
指示書: .claude/instructions/2026-05-14_rolling_phase4b_phase5.md

Guard: fit/KMeans なし / shift(1) look-ahead フリー / CSV 本体はここに貼らない
"""

import hashlib, sys, json, warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

# ── パス定義 ─────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parents[2]
DATA_DIR     = BASE_DIR / "results/priority_rebuild"
REFIT_DIR    = DATA_DIR / "ml_phase1_k12long_refit"

TRAIN_PRED   = REFIT_DIR / "predictions_train_2021_2024_k12long_refit.parquet"
TEST_PRED    = REFIT_DIR / "predictions_test2025_k12long_refit.parquet"
LABELS_TR    = DATA_DIR  / "labels_mfe_mae_train_2021_2024.parquet"
LABELS_TE    = DATA_DIR  / "labels_mfe_mae_test_2025.parquet"

OUT_ROLLING  = DATA_DIR / "ml_phase4_a_norm" / "predictions_test2025_rolling365.parquet"
OUT_4B_DIR   = DATA_DIR / "ml_phase4_b"
OUT_5_DIR    = DATA_DIR / "ml_phase5"
OUT_4B_DIR.mkdir(parents=True, exist_ok=True)
OUT_5_DIR.mkdir(parents=True, exist_ok=True)

TS = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
LOG_PATH = OUT_5_DIR / f"phase4b_phase5_log_{TS}.txt"

# ── 定数 ─────────────────────────────────────────────────────────
WINDOW       = 365 * 288          # 105,120 bars (365日分)
MIN_PERIODS  = WINDOW // 4        # ~26,280 bars (約91日)
POSITION_BTC = 0.12               # 0.12 BTC / trade
MAKER_FEE    = 0.00014            # 0.014%
SLIPPAGE     = 0.00005            # 0.005%
MIN_SAMPLES  = 100                # 足切り基準

# K × side 全組合せ
KS = [(12,'LONG'),(12,'SHORT'),(24,'LONG'),(24,'SHORT'),
      (48,'LONG'),(48,'SHORT'),(96,'LONG'),(96,'SHORT')]

# q99 発火数期待値 (threshold_drift_eval_completion.md §3 / rolling 365)
EXPECTED_Q99 = {
    'K12_LONG':552, 'K12_SHORT':1574,
    'K24_LONG':596, 'K24_SHORT':1556,
    'K48_LONG':951, 'K48_SHORT':1409,
    'K96_LONG':541, 'K96_SHORT':1230,
}

# Active 19 組合せ (option5_eval_REEVAL.csv cutoff_status=active)
# K96 SHORT q99: audit9 除外を rolling 採用後も維持
ACTIVE_19 = [
    (12,'LONG','q99'), (12,'LONG','q95-q99'), (12,'LONG','q90-q95'),
    (12,'SHORT','q99'), (12,'SHORT','q95-q99'), (12,'SHORT','q90-q95'),
    (24,'LONG','q95-q99'), (24,'LONG','q90-q95'),
    (24,'SHORT','q95-q99'), (24,'SHORT','q90-q95'),
    (48,'LONG','q99'), (48,'LONG','q95-q99'), (48,'LONG','q90-q95'),
    (48,'SHORT','q99'), (48,'SHORT','q95-q99'), (48,'SHORT','q90-q95'),
    (96,'LONG','q95-q99'), (96,'LONG','q90-q95'),
    (96,'SHORT','q90-q95'),
]

BAND_LABELS = ['q99', 'q95-q99', 'q90-q95']


# ── ユーティリティ ────────────────────────────────────────────────
def log(msg, lf=None):
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    if lf:
        lf.write(line + "\n")
        lf.flush()

def sha12(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]

def rolling_qn(series, window, min_periods, q):
    """look-ahead フリー rolling 分位数 (shift(1): t 時点 → t-1 以前の history のみ参照)"""
    return series.shift(1).rolling(window=window, min_periods=min_periods).quantile(q)

def band_fire_mask(ratio, q90, q95, q99, band):
    """ratio が指定 band に該当するかのマスク"""
    q99_valid = q99.notna()
    q95_valid = q95.notna()
    q90_valid = q90.notna()
    if band == 'q99':
        return (ratio >= q99) & q99_valid
    elif band == 'q95-q99':
        return (ratio >= q95) & (ratio < q99) & q95_valid & q99_valid
    else:  # q90-q95
        return (ratio >= q90) & (ratio < q95) & q90_valid & q95_valid

def fixed_thr(ratio_tr, band):
    """固定 train 閾値で band fire マスク (Phase 4-b train Exit 設計用)"""
    q99 = float(ratio_tr.quantile(0.99))
    q95 = float(ratio_tr.quantile(0.95))
    q90 = float(ratio_tr.quantile(0.90))
    if band == 'q99':
        return ratio_tr >= q99
    elif band == 'q95-q99':
        return (ratio_tr >= q95) & (ratio_tr < q99)
    else:
        return (ratio_tr >= q90) & (ratio_tr < q95)


# ── メイン ────────────────────────────────────────────────────────
def main():
    with open(LOG_PATH, "w") as lf:
        t0 = datetime.now()
        log(f"START {t0.isoformat()}", lf)
        log(f"WINDOW={WINDOW} bars / MIN_PERIODS={MIN_PERIODS} / POSITION={POSITION_BTC} BTC", lf)

        # ── データロード ──────────────────────────────────────────
        log("Load data ...", lf)
        df_tr_pred = pd.read_parquet(TRAIN_PRED)
        df_te_pred = pd.read_parquet(TEST_PRED)
        df_tr_lab  = pd.read_parquet(LABELS_TR)
        df_te_lab  = pd.read_parquet(LABELS_TE)

        log(f"  train pred: {len(df_tr_pred)} rows", lf)
        log(f"  test  pred: {len(df_te_pred)} rows", lf)

        # train + test 連結 (rolling は test 開始時に直近 365d の train を参照)
        df_all_pred = pd.concat([df_tr_pred, df_te_pred])
        te_start    = df_te_pred.index[0]

        # ── Step 1: rolling 365 閾値 → test 発火フラグ ───────────
        log("Step 1: rolling 365 threshold → test fire flags ...", lf)
        fire_cols  = {}
        q99_counts = {}

        for k, side in KS:
            mfe_col = f"{side}_MFE_K{k}"
            mae_col = f"{side}_MAE_K{k}"
            ratio_all = df_all_pred[mfe_col] / df_all_pred[mae_col].clip(lower=1e-9)

            rq90 = rolling_qn(ratio_all, WINDOW, MIN_PERIODS, 0.90)
            rq95 = rolling_qn(ratio_all, WINDOW, MIN_PERIODS, 0.95)
            rq99 = rolling_qn(ratio_all, WINDOW, MIN_PERIODS, 0.99)

            te_mask   = ratio_all.index >= te_start
            ratio_te  = ratio_all[te_mask]
            q90_te    = rq90[te_mask]
            q95_te    = rq95[te_mask]
            q99_te    = rq99[te_mask]

            n_q99 = int(band_fire_mask(ratio_te, q90_te, q95_te, q99_te, 'q99').sum())
            key   = f"K{k}_{side}"
            q99_counts[key] = n_q99

            for band in BAND_LABELS:
                col_name = f"K{k}_{side}_{band.replace('-','_')}"
                fire_cols[col_name] = band_fire_mask(ratio_te, q90_te, q95_te, q99_te, band)

        df_fire_te = pd.DataFrame(fire_cols, index=df_te_pred.index)
        df_fire_te.to_parquet(OUT_ROLLING)
        log(f"  saved predictions_test2025_rolling365.parquet ({len(df_fire_te)} rows, "
            f"{len(df_fire_te.columns)} cols) sha256={sha12(OUT_ROLLING)}", lf)

        # Step 1-3: 発火数 verify (q99 期待値照合)
        log("Step 1-3: q99 fire count verify ...", lf)
        verify_ok = True
        for key, expected in EXPECTED_Q99.items():
            actual = q99_counts.get(key, -1)
            # K96 SHORT q99 はゼロでよい (audit9 除外・ただし rolling で火花があるので raw count は出す)
            tol   = max(20, expected * 0.10)  # 10% 許容
            ok    = abs(actual - expected) <= tol
            if key == 'K96_SHORT':
                # K96 SHORT q99: audit9 で除外だが rolling count は確認のみ
                log(f"  {key} q99: actual={actual} expected={expected} (audit9 excluded from replay)", lf)
            else:
                mark = "✅" if ok else "❌"
                log(f"  {key} q99: actual={actual} expected={expected} diff={actual-expected:+d} {mark}", lf)
                if not ok:
                    verify_ok = False

        if not verify_ok:
            log("STOP: q99 fire count mismatch > 10%. 指示書 Step 1-3 STOP 条件に該当。", lf)
            sys.exit(1)

        # ── Step 2: Phase 4-b — train Exit 設計 ─────────────────
        log("Step 2: Phase 4-b Exit design on train data ...", lf)

        # train ラベルに将来 close (time exit 用) を事前計算
        close_tr = df_tr_lab['close']

        exit_rows = []
        for k, side, q_band in ACTIVE_19:
            mfe_col = f"{side}_MFE_K{k}"
            mae_col = f"{side}_MAE_K{k}"

            ratio_tr = df_tr_pred[mfe_col] / df_tr_pred[mae_col].clip(lower=1e-9)
            fire_tr  = fixed_thr(ratio_tr, q_band)
            n_tr     = int(fire_tr.sum())

            if n_tr < MIN_SAMPLES:
                log(f"  SKIP (train n={n_tr} < {MIN_SAMPLES}): K{k}_{side}_{q_band}", lf)
                continue

            fired_idx = fire_tr.index[fire_tr]
            mfe_vals  = df_tr_lab.loc[fired_idx, mfe_col].values.astype(float)
            mae_vals  = df_tr_lab.loc[fired_idx, mae_col].values.astype(float)
            close_e   = df_tr_lab.loc[fired_idx, 'close'].values.astype(float)

            # 時間 Exit: K 本後 close (§4b.3: K まで制限)
            future_close_k = close_tr.shift(-k)
            fc_vals = future_close_k.loc[fired_idx].values.astype(float)

            # TP/SL パラメータ (train median)
            tp_usd = float(np.nanmedian(mfe_vals))
            sl_usd = float(np.nanmedian(mae_vals))
            close_avg = float(np.nanmean(close_e))
            tp_pct = tp_usd / close_avg
            sl_pct = sl_usd / close_avg

            # 3 種 Exit 評価
            best_exit_type = None
            best_pnl       = -np.inf
            exit_results   = {}

            for exit_type in ('fixed_tp', 'time_exit', 'trailing'):
                pnls = []
                for i in range(n_tr):
                    ce, mfe, mae, fc = close_e[i], mfe_vals[i], mae_vals[i], fc_vals[i]
                    if np.isnan(fc) or np.isnan(mfe) or np.isnan(mae):
                        continue
                    mfe_frac = mfe / ce
                    mae_frac = mae / ce

                    if exit_type == 'fixed_tp':
                        if mfe_frac >= tp_pct:
                            raw = ce * tp_pct * POSITION_BTC
                        elif mae_frac >= sl_pct:
                            raw = -ce * sl_pct * POSITION_BTC
                        else:
                            # time exit fallback
                            raw = ((fc - ce) if side == 'LONG' else (ce - fc)) * POSITION_BTC
                    elif exit_type == 'time_exit':
                        raw = ((fc - ce) if side == 'LONG' else (ce - fc)) * POSITION_BTC
                    else:  # trailing 50% of MFE
                        raw = ce * (mfe_frac * 0.50) * POSITION_BTC
                    pnls.append(raw)

                n_valid  = len(pnls)
                fee_tot  = n_valid * 2 * MAKER_FEE * POSITION_BTC * close_avg
                net_pnl  = sum(pnls) - fee_tot
                tp_hr    = float(np.mean(mfe_vals / close_e >= tp_pct)) if exit_type == 'fixed_tp' else np.nan
                exit_results[exit_type] = {'net_pnl': net_pnl, 'n_valid': n_valid,
                                            'tp_hit_rate': tp_hr}
                if net_pnl > best_pnl:
                    best_pnl       = net_pnl
                    best_exit_type = exit_type

            log(f"  K{k}_{side}_{q_band}: best={best_exit_type} "
                f"train_net={best_pnl:.0f}$ n_tr={n_tr} "
                f"tp_pct={tp_pct*100:.2f}% sl_pct={sl_pct*100:.2f}%", lf)

            exit_rows.append({
                'K': k, 'side': side, 'q_band': q_band,
                'exit_type': best_exit_type,
                'tp_pct': round(tp_pct, 6),
                'sl_pct': round(sl_pct, 6),
                'time_bars': k,  # §4b.3: K まで制限
                'train_hit_rate': round(exit_results['fixed_tp']['tp_hit_rate'], 4)
                    if not np.isnan(exit_results['fixed_tp']['tp_hit_rate']) else np.nan,
                'train_net_pnl': round(best_pnl, 2),
                'n_train_fires': n_tr,
            })

        df_exit = pd.DataFrame(exit_rows)
        exit_path = OUT_4B_DIR / "cluster_best_exit_option5.csv"
        df_exit.to_csv(exit_path, index=False)
        log(f"  saved cluster_best_exit_option5.csv ({len(df_exit)} rows) "
            f"sha256={sha12(exit_path)}", lf)

        # Exit 約定率チェック (§4b compliance: ≥12%)
        avg_tp_hr = float(df_exit['train_hit_rate'].mean())
        log(f"  avg TP hit rate (fixed_tp combos): {avg_tp_hr*100:.1f}% "
            f"({'✅ ≥12%' if avg_tp_hr >= 0.12 else '❌ <12% WARNING'})", lf)

        # ── Step 3: Phase 5 Replay (test 2025) ──────────────────
        log("Step 3: Phase 5 Replay (test 2025, cap=none) ...", lf)

        # 将来 close (time exit 用)
        close_te_future = {}
        for k, _ in set((x[0], x[1]) for x in ACTIVE_19):
            close_te_future[k] = df_te_lab['close'].shift(-k)

        replay_rows = []
        for _, row in df_exit.iterrows():
            k, side, q_band = int(row['K']), row['side'], row['q_band']
            exit_type = row['exit_type']
            tp_pct    = float(row['tp_pct'])
            sl_pct    = float(row['sl_pct'])

            col_name = f"K{k}_{side}_{q_band.replace('-','_')}"
            if col_name not in df_fire_te.columns:
                log(f"  WARN: fire column not found: {col_name}", lf)
                continue

            fire_mask = df_fire_te[col_name]
            fired_idx = fire_mask.index[fire_mask]

            # K96 SHORT q99 は audit9 除外 (念のため guard)
            if k == 96 and side == 'SHORT' and q_band == 'q99':
                log(f"  SKIP K96_SHORT_q99 (audit9 excluded)", lf)
                continue

            if len(fired_idx) < 1:
                log(f"  {col_name}: 0 fires in test → skip", lf)
                continue

            mfe_col = f"{side}_MFE_K{k}"
            mae_col = f"{side}_MAE_K{k}"
            mfe_te  = df_te_lab.loc[fired_idx, mfe_col].values.astype(float)
            mae_te  = df_te_lab.loc[fired_idx, mae_col].values.astype(float)
            close_e = df_te_lab.loc[fired_idx, 'close'].values.astype(float)
            fc_vals = close_te_future[k].loc[fired_idx].values.astype(float)
            months  = fired_idx.to_period('M')

            for i in range(len(fired_idx)):
                ce, mfe, mae, fc = close_e[i], mfe_te[i], mae_te[i], fc_vals[i]
                if np.isnan(mfe) or np.isnan(mae) or np.isnan(ce):
                    continue
                mfe_frac = mfe / ce
                mae_frac = mae / ce
                # entry price: close + slippage
                entry = ce * (1 + SLIPPAGE) if side == 'LONG' else ce * (1 - SLIPPAGE)

                if exit_type == 'fixed_tp':
                    if mfe_frac >= tp_pct:
                        raw = entry * tp_pct * POSITION_BTC
                    elif mae_frac >= sl_pct:
                        raw = -entry * sl_pct * POSITION_BTC
                    else:
                        if np.isnan(fc):
                            continue
                        raw = ((fc - entry) if side == 'LONG' else (entry - fc)) * POSITION_BTC
                elif exit_type == 'time_exit':
                    if np.isnan(fc):
                        continue
                    raw = ((fc - entry) if side == 'LONG' else (entry - fc)) * POSITION_BTC
                else:  # trailing 50%
                    raw = entry * (mfe_frac * 0.50) * POSITION_BTC

                fee = 2 * MAKER_FEE * POSITION_BTC * entry
                net = raw - fee

                replay_rows.append({
                    'month': str(months[i]),
                    'combo': f"K{k}_{side}_{q_band}",
                    'net_pnl': net,
                    'exit_type': exit_type,
                })

        df_replay = pd.DataFrame(replay_rows)
        replay_path = OUT_5_DIR / "replay_entries_option5.csv"
        df_replay.to_csv(replay_path, index=False)
        log(f"  total entries: {len(df_replay)} sha256={sha12(replay_path)}", lf)

        # 月次集計
        monthly = (df_replay.groupby('month')
                   .agg(n_fires=('net_pnl','count'), net_pnl=('net_pnl','sum'))
                   .reset_index()
                   .sort_values('month'))
        monthly_path = OUT_5_DIR / "monthly_pnl_option5.csv"
        monthly.to_csv(monthly_path, index=False)

        # ── 月次 PnL 出力 ──────────────────────────────────────
        log("", lf)
        log("=" * 60, lf)
        log("Phase 5 月次 PnL (2025)", lf)
        log("=" * 60, lf)
        total_pnl   = float(monthly['net_pnl'].sum())
        total_fires = int(monthly['n_fires'].sum())
        n_pass      = int((monthly['net_pnl'] >= 1900).sum())

        for _, r in monthly.iterrows():
            mark = "✅" if r['net_pnl'] >= 1900 else "❌"
            log(f"  {r['month']}  fires={int(r['n_fires']):5d}  "
                f"net_pnl=${r['net_pnl']:8,.0f}  {mark}", lf)

        log("", lf)
        log(f"  合計 PnL    : ${total_pnl:,.0f}", lf)
        log(f"  月次平均    : ${total_pnl/12:,.0f}/月", lf)
        log(f"  ≥$1,900 達成: {n_pass}/12 ヶ月", lf)
        log(f"  $60/day換算 : ${total_pnl/365:,.0f}/日", lf)
        log(f"  総発火数    : {total_fires:,}", lf)
        log("=" * 60, lf)

        log(f"  saved monthly_pnl_option5.csv sha256={sha12(monthly_path)}", lf)

        # ── Summary JSON ─────────────────────────────────────────
        t1 = datetime.now()
        summary = {
            "start": t0.isoformat(),
            "end":   t1.isoformat(),
            "duration_sec": (t1 - t0).total_seconds(),
            "rolling_window_days": 365,
            "n_active_combos": len(df_exit),
            "total_test_fires": total_fires,
            "total_net_pnl_usd": round(total_pnl, 2),
            "monthly_avg_pnl_usd": round(total_pnl / 12, 2),
            "pnl_per_day_usd": round(total_pnl / 365, 2),
            "months_ge_1900": n_pass,
            "q99_verify_ok": verify_ok,
            "outputs": {
                "rolling_parquet": str(OUT_ROLLING),
                "cluster_best_exit": str(exit_path),
                "replay_entries": str(replay_path),
                "monthly_pnl": str(monthly_path),
            },
        }
        summary_path = OUT_5_DIR / "phase5_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        log(f"END duration={(t1-t0).total_seconds():.1f}s", lf)
        log(f"LOG: {LOG_PATH}", lf)


if __name__ == "__main__":
    main()
