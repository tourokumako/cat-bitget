#!/usr/bin/env python3
"""
Phase 4-b Exit設計 + Phase 5 Replay — rolling 365 × Option 5 v2
v1 (commit 2e5fdc9) の leak 2件を修正:
  1. trailing exit leak (mfe_vals 直接流用) → bar-by-bar 時系列実装 (TRAIL_PCT=0.3% 固定定数)
  2. fixed_tp fit-by-construction   → train-A/B 分離方式
     (TP/SL 価格は train-A 中央値・Exit 選定は train-B net_pnl)

Prime Directive 準拠 (false_positive_incident_policy §0):
  全入力変数が推論時点 t で因果的に取得可能であることを Step 0-2 で宣言済み。
  trailing exit: entry + bar-by-bar high/low/close のみ使用 (mfe/mae 不使用)
  fixed_tp: tp_pct/sl_pct は train-A 事前定数・TP 命中判定は標準バックテスト手法

指示書: .claude/instructions/2026-05-15_phase4b_phase5_rerun.md
"""

import hashlib, sys, json, warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

# ── パス定義 ──────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parents[2]
DATA_DIR    = BASE_DIR / "results/priority_rebuild"
REFIT_DIR   = DATA_DIR / "ml_phase1_k12long_refit"

TRAIN_PRED  = REFIT_DIR / "predictions_train_2021_2024_k12long_refit.parquet"
TEST_PRED   = REFIT_DIR / "predictions_test2025_k12long_refit.parquet"
LABELS_TR   = DATA_DIR  / "labels_mfe_mae_train_2021_2024.parquet"
LABELS_TE   = DATA_DIR  / "labels_mfe_mae_test_2025.parquet"
OHLC_CSV    = BASE_DIR  / "data" / "BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv"

OUT_ROLLING = DATA_DIR / "ml_phase4_a_norm" / "predictions_test2025_rolling365.parquet"
OUT_4B_DIR  = DATA_DIR / "ml_phase4_b"
OUT_5_DIR   = DATA_DIR / "ml_phase5"
OUT_4B_DIR.mkdir(parents=True, exist_ok=True)
OUT_5_DIR.mkdir(parents=True, exist_ok=True)

TS       = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
LOG_PATH = OUT_5_DIR / f"phase4b_phase5_log_v2_{TS}.txt"

# ── 定数 ──────────────────────────────────────────────────────────────
WINDOW       = 365 * 288           # 105,120 bars (365日分)
MIN_PERIODS  = WINDOW // 4
POSITION_BTC = 0.12
MAKER_FEE    = 0.00014             # exchange_spec.md 確定値 (Maker 0.014%)
SLIPPAGE     = 0.00005             # 0.005% 全約定加算
MIN_SAMPLES  = 30                  # train-A/B 両方に最低 30 fires 必要

# trailing exit: peak からの反転閾値 (Prime Directive Candidate A: 本番固定定数・fit なし)
TRAIL_PCT    = 0.003               # 0.3% pullback から exit

# fixed_tp: train-A (TP/SL 決定) / train-B (Exit 選定)
TRAIN_A_END   = pd.Timestamp('2023-06-30 23:55:00')   # train-A: 2021-04〜2023-06 (~27ヶ月)
TRAIN_B_START = pd.Timestamp('2023-07-01 00:00:00')   # train-B: 2023-07〜2024-12 (~18ヶ月)

# K × side 全組合せ
KS = [(12,'LONG'),(12,'SHORT'),(24,'LONG'),(24,'SHORT'),
      (48,'LONG'),(48,'SHORT'),(96,'LONG'),(96,'SHORT')]

EXPECTED_Q99 = {
    'K12_LONG':552, 'K12_SHORT':1574,
    'K24_LONG':596, 'K24_SHORT':1556,
    'K48_LONG':951, 'K48_SHORT':1409,
    'K96_LONG':541, 'K96_SHORT':1230,
}

# Active 19 組合せ (K96 SHORT q99 は audit9 除外)
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


# ── ユーティリティ ────────────────────────────────────────────────────
def log(msg, lf=None):
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    if lf:
        lf.write(line + "\n")
        lf.flush()

def sha12(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]

def rolling_qn(series, window, min_periods, q):
    """look-ahead フリー rolling 分位数 (shift(1): t 時点 → t-1 以前の history のみ)"""
    return series.shift(1).rolling(window=window, min_periods=min_periods).quantile(q)

def band_fire_mask(ratio, q90, q95, q99, band):
    q99v = q99.notna(); q95v = q95.notna(); q90v = q90.notna()
    if band == 'q99':
        return (ratio >= q99) & q99v
    elif band == 'q95-q99':
        return (ratio >= q95) & (ratio < q99) & q95v & q99v
    else:
        return (ratio >= q90) & (ratio < q95) & q90v & q95v

def fixed_thr(ratio_tr, band):
    q99 = float(ratio_tr.quantile(0.99))
    q95 = float(ratio_tr.quantile(0.95))
    q90 = float(ratio_tr.quantile(0.90))
    if band == 'q99':      return ratio_tr >= q99
    elif band == 'q95-q99': return (ratio_tr >= q95) & (ratio_tr < q99)
    else:                   return (ratio_tr >= q90) & (ratio_tr < q95)


def sim_trailing_bar_by_bar(fired_positions, K, side, entry_prices,
                              high_arr, low_arr, close_arr, n_total):
    """
    Bar-by-bar trailing exit (Prime Directive 準拠).

    入力変数（すべて推論時点 t で因果的に取得可能）:
      fired_positions : エントリーバーの全体インデックス位置 (int array)
      entry_prices    : エントリー価格 array（close × (1±SLIPPAGE) または close）
      high_arr/low_arr/close_arr : 全体 OHLC numpy 配列
      TRAIL_PCT       : 固定定数 0.003（本番でも同じ値を使用）

    MFE / MAE は一切使用しない。
    exit 価格 = trailing stop trigger 時の bar close、または K 本後 close (フォールバック)。

    戻り値:
      raw     : PnL の生値 array（POSITION_BTC 込み・手数料前）
      valid   : 入力 fired_positions 各要素の有効フラグ (bool array)
    """
    n = len(fired_positions)
    if n == 0:
        return np.array([]), np.zeros(n, dtype=bool)

    # 将来 K バーの位置 matrix: (n, K)
    future_pos = fired_positions[:, np.newaxis] + np.arange(1, K + 1)

    # 全 K 本が存在するかチェック (境界)
    valid = future_pos[:, -1] < n_total
    if valid.sum() == 0:
        return np.array([]), valid

    fp = future_pos[valid]               # (n_valid, K)
    ep = entry_prices[valid]             # (n_valid,)
    n_valid = len(ep)

    # 将来バーの OHLC 抽出
    f_high  = high_arr[fp]    # (n_valid, K)
    f_low   = low_arr[fp]     # (n_valid, K)
    f_close = close_arr[fp]   # (n_valid, K)

    # NaN が残っている bar は entry 値で埋める（保守的: peak が進まない）
    nan_mask = np.isnan(f_high) | np.isnan(f_low) | np.isnan(f_close)
    if nan_mask.any():
        ep_expanded = np.broadcast_to(ep[:, np.newaxis], (n_valid, K))
        f_high  = np.where(nan_mask, ep_expanded, f_high)
        f_low   = np.where(nan_mask, ep_expanded, f_low)
        f_close = np.where(nan_mask, ep_expanded, f_close)

    # 各バーでの running peak (entry を初期値に含める)
    init = ep[:, np.newaxis]  # (n_valid, 1)
    if side == 'LONG':
        peak_seq = np.maximum.accumulate(
            np.concatenate([init, f_high], axis=1), axis=1
        )[:, 1:]              # (n_valid, K)
        trigger = f_close <= peak_seq * (1.0 - TRAIL_PCT)
    else:  # SHORT
        peak_seq = np.minimum.accumulate(
            np.concatenate([init, f_low], axis=1), axis=1
        )[:, 1:]
        trigger = f_close >= peak_seq * (1.0 + TRAIL_PCT)

    # 最初の反転バー (なければ K-1 = time exit フォールバック)
    has_trigger = trigger.any(axis=1)
    exit_bar    = np.where(has_trigger, np.argmax(trigger, axis=1), K - 1)
    exit_prices = f_close[np.arange(n_valid), exit_bar]

    if side == 'LONG':
        raw = (exit_prices - ep) * POSITION_BTC
    else:
        raw = (ep - exit_prices) * POSITION_BTC

    return raw, valid


# ── メイン ────────────────────────────────────────────────────────────
def main():
    with open(LOG_PATH, "w") as lf:
        t0 = datetime.now()
        log(f"START {t0.isoformat()}", lf)
        log(f"TRAIL_PCT={TRAIL_PCT} / TRAIN_A_END={TRAIN_A_END} / TRAIN_B_START={TRAIN_B_START}", lf)
        log(f"MAKER_FEE={MAKER_FEE} / POSITION_BTC={POSITION_BTC} / SLIPPAGE={SLIPPAGE}", lf)

        # ── データロード ──────────────────────────────────────────
        log("Load label / pred parquet ...", lf)
        df_tr_pred = pd.read_parquet(TRAIN_PRED)
        df_te_pred = pd.read_parquet(TEST_PRED)
        df_tr_lab  = pd.read_parquet(LABELS_TR)
        df_te_lab  = pd.read_parquet(LABELS_TE)
        log(f"  train pred: {len(df_tr_pred)} / test pred: {len(df_te_pred)}", lf)
        log(f"  train lab:  {len(df_tr_lab)} / test lab:  {len(df_te_lab)}", lf)

        # OHLC ロード (bar-by-bar trailing 用)
        log(f"Load OHLC: {OHLC_CSV.name} ...", lf)
        df_ohlc = pd.read_csv(OHLC_CSV, parse_dates=['timestamp']).set_index('timestamp')
        all_lab_idx = df_tr_lab.index.append(df_te_lab.index)
        ohlc_al = df_ohlc[['high','low','close']].reindex(all_lab_idx).ffill()

        nan_remaining = int(ohlc_al.isnull().sum().sum())
        log(f"  OHLC aligned: {len(ohlc_al)} bars / NaN after ffill: {nan_remaining}", lf)
        if nan_remaining > len(ohlc_al) * 0.01:
            log(f"  ERROR: OHLC NaN > 1% ({nan_remaining}) — タイムスタンプ不一致を確認", lf)
            sys.exit(1)

        high_arr  = ohlc_al['high'].values.astype(float)
        low_arr   = ohlc_al['low'].values.astype(float)
        close_ohlc = ohlc_al['close'].values.astype(float)
        n_total   = len(all_lab_idx)
        n_train   = len(df_tr_lab)

        # 全体インデックス位置 mapping
        pos_of = pd.Series(np.arange(n_total), index=all_lab_idx)

        # ── Step 1: rolling 365 閾値 → test 発火フラグ (変更なし) ─
        log("Step 1: rolling 365 threshold ...", lf)
        df_all_pred = pd.concat([df_tr_pred, df_te_pred])
        te_start    = df_te_pred.index[0]
        fire_cols   = {}
        q99_counts  = {}

        for k, side in KS:
            mfe_col = f"{side}_MFE_K{k}"
            mae_col = f"{side}_MAE_K{k}"
            ratio_all = df_all_pred[mfe_col] / df_all_pred[mae_col].clip(lower=1e-9)

            rq90 = rolling_qn(ratio_all, WINDOW, MIN_PERIODS, 0.90)
            rq95 = rolling_qn(ratio_all, WINDOW, MIN_PERIODS, 0.95)
            rq99 = rolling_qn(ratio_all, WINDOW, MIN_PERIODS, 0.99)

            te_mask  = ratio_all.index >= te_start
            ratio_te = ratio_all[te_mask]
            q90_te = rq90[te_mask]; q95_te = rq95[te_mask]; q99_te = rq99[te_mask]

            n_q99 = int(band_fire_mask(ratio_te, q90_te, q95_te, q99_te, 'q99').sum())
            key = f"K{k}_{side}"; q99_counts[key] = n_q99

            for band in BAND_LABELS:
                col = f"K{k}_{side}_{band.replace('-','_')}"
                fire_cols[col] = band_fire_mask(ratio_te, q90_te, q95_te, q99_te, band)

        df_fire_te = pd.DataFrame(fire_cols, index=df_te_pred.index)
        df_fire_te.to_parquet(OUT_ROLLING)
        log(f"  saved rolling365 parquet ({len(df_fire_te)} rows)", lf)

        verify_ok = True
        for key, expected in EXPECTED_Q99.items():
            actual = q99_counts.get(key, -1)
            tol  = max(20, expected * 0.10)
            ok   = abs(actual - expected) <= tol
            if key == 'K96_SHORT':
                log(f"  {key} q99: actual={actual} (audit9 excluded)", lf)
            else:
                mark = "✅" if ok else "❌"
                log(f"  {key} q99: actual={actual} expected={expected} diff={actual-expected:+d} {mark}", lf)
                if not ok: verify_ok = False
        if not verify_ok:
            log("STOP: q99 fire count mismatch > 10%.", lf); sys.exit(1)

        # ── Step 2: Phase 4-b — train-A TP/SL fit / train-B 選定 ──
        log("Step 2: Phase 4-b (train-A TP fit / train-B exit selection) ...", lf)
        close_tr = df_tr_lab['close']
        exit_rows = []

        for k, side, q_band in ACTIVE_19:
            mfe_col = f"{side}_MFE_K{k}"
            mae_col = f"{side}_MAE_K{k}"

            ratio_tr = df_tr_pred[mfe_col] / df_tr_pred[mae_col].clip(lower=1e-9)
            fire_tr  = fixed_thr(ratio_tr, q_band)

            # train-A / train-B 分割
            fire_A = fire_tr & (fire_tr.index <= TRAIN_A_END)
            fire_B = fire_tr & (fire_tr.index >= TRAIN_B_START)
            n_A = int(fire_A.sum()); n_B = int(fire_B.sum())

            if n_A < MIN_SAMPLES or n_B < MIN_SAMPLES:
                log(f"  SKIP (n_A={n_A} n_B={n_B} < {MIN_SAMPLES}): K{k}_{side}_{q_band}", lf)
                continue

            # ── train-A: TP/SL 価格パラメータ決定 ──
            idx_A   = fire_A.index[fire_A]
            mfe_A   = df_tr_lab.loc[idx_A, mfe_col].values.astype(float)
            mae_A   = df_tr_lab.loc[idx_A, mae_col].values.astype(float)
            ce_A    = df_tr_lab.loc[idx_A, 'close'].values.astype(float)
            ca_avg  = float(np.nanmean(ce_A))
            tp_pct  = float(np.nanmedian(mfe_A)) / ca_avg   # train-A 中央値のみ
            sl_pct  = float(np.nanmedian(mae_A)) / ca_avg

            # ── train-B: 各 exit 種別 net_pnl を計算・選定 ──
            idx_B    = fire_B.index[fire_B]
            mfe_B    = df_tr_lab.loc[idx_B, mfe_col].values.astype(float)
            mae_B    = df_tr_lab.loc[idx_B, mae_col].values.astype(float)
            ce_B     = df_tr_lab.loc[idx_B, 'close'].values.astype(float)
            fc_B     = close_tr.shift(-k).loc[idx_B].values.astype(float)
            cb_avg   = float(np.nanmean(ce_B))
            pos_B    = pos_of.loc[idx_B].values.astype(int)

            best_exit_type = None
            best_pnl       = -np.inf
            exit_results   = {}

            for exit_type in ('fixed_tp', 'time_exit', 'trailing'):
                if exit_type == 'trailing':
                    # bar-by-bar (MFE/MAE 不使用)
                    raw_arr, _ = sim_trailing_bar_by_bar(
                        pos_B, k, side, ce_B, high_arr, low_arr, close_ohlc, n_total
                    )
                    pnls   = raw_arr.tolist()
                    tp_hr  = np.nan
                else:
                    pnls  = []
                    for i in range(n_B):
                        ce, mfe, mae, fc = ce_B[i], mfe_B[i], mae_B[i], fc_B[i]
                        if np.isnan(mfe) or np.isnan(mae) or np.isnan(ce): continue
                        mf = mfe / ce; ma = mae / ce
                        if exit_type == 'fixed_tp':
                            if   mf >= tp_pct: raw = ce * tp_pct * POSITION_BTC
                            elif ma >= sl_pct:  raw = -ce * sl_pct * POSITION_BTC
                            else:
                                if np.isnan(fc): continue
                                raw = ((fc-ce) if side=='LONG' else (ce-fc)) * POSITION_BTC
                        else:  # time_exit
                            if np.isnan(fc): continue
                            raw = ((fc-ce) if side=='LONG' else (ce-fc)) * POSITION_BTC
                        pnls.append(raw)
                    tp_hr = float(np.mean(mfe_B / ce_B >= tp_pct)) if exit_type == 'fixed_tp' else np.nan

                n_v     = len(pnls)
                fee_tot = n_v * 2 * MAKER_FEE * POSITION_BTC * cb_avg
                net_pnl = float(np.sum(pnls)) - fee_tot if n_v > 0 else 0.0

                exit_results[exit_type] = {'net_pnl': net_pnl, 'n': n_v, 'tp_hit_rate': tp_hr}
                if net_pnl > best_pnl:
                    best_pnl = net_pnl; best_exit_type = exit_type

            log(f"  K{k}_{side}_{q_band}: best={best_exit_type} "
                f"Bnet={best_pnl:.0f}$ nA={n_A} nB={n_B} "
                f"tp={tp_pct*100:.2f}% sl={sl_pct*100:.2f}%"
                f"  [ft={exit_results['fixed_tp']['net_pnl']:.0f}"
                f" te={exit_results['time_exit']['net_pnl']:.0f}"
                f" tr={exit_results['trailing']['net_pnl']:.0f}]", lf)

            exit_rows.append({
                'K': k, 'side': side, 'q_band': q_band,
                'exit_type': best_exit_type,
                'tp_pct': round(tp_pct, 6),
                'sl_pct': round(sl_pct, 6),
                'time_bars': k,
                'trainB_tp_hit_rate': round(tp_hr, 4) if not np.isnan(tp_hr) else np.nan,
                'trainB_net_pnl': round(best_pnl, 2),
                'n_train_A': n_A, 'n_train_B': n_B,
            })

        df_exit = pd.DataFrame(exit_rows)
        exit_path = OUT_4B_DIR / "cluster_best_exit_option5_v2.csv"
        df_exit.to_csv(exit_path, index=False)
        log(f"  saved cluster_best_exit_option5_v2.csv ({len(df_exit)} rows) "
            f"sha256={sha12(exit_path)}", lf)

        # TP hit rate ログ (fixed_tp combos のみ)
        fp_combos = df_exit[df_exit['exit_type']=='fixed_tp']
        if len(fp_combos) > 0:
            avg_tp_hr = float(fp_combos['trainB_tp_hit_rate'].mean())
            log(f"  avg TP hit rate (fixed_tp combos, train-B): {avg_tp_hr*100:.1f}%", lf)

        # ── Step 3: Phase 5 Replay (test 2025) ──────────────────
        log("Step 3: Phase 5 Replay (test 2025, cap=none) ...", lf)

        replay_rows = []
        for _, row in df_exit.iterrows():
            k, side, q_band = int(row['K']), row['side'], row['q_band']
            exit_type = row['exit_type']
            tp_pct    = float(row['tp_pct'])
            sl_pct    = float(row['sl_pct'])

            col = f"K{k}_{side}_{q_band.replace('-','_')}"
            if col not in df_fire_te.columns:
                log(f"  WARN: col not found: {col}", lf); continue

            fire_mask = df_fire_te[col]
            fired_idx = fire_mask.index[fire_mask]

            if k == 96 and side == 'SHORT' and q_band == 'q99':
                log(f"  SKIP K96_SHORT_q99 (audit9)", lf); continue
            if len(fired_idx) < 1:
                log(f"  {col}: 0 fires → skip", lf); continue

            mfe_col = f"{side}_MFE_K{k}"
            mae_col = f"{side}_MAE_K{k}"
            mfe_te  = df_te_lab.loc[fired_idx, mfe_col].values.astype(float)
            mae_te  = df_te_lab.loc[fired_idx, mae_col].values.astype(float)
            ce_te   = df_te_lab.loc[fired_idx, 'close'].values.astype(float)
            fc_te   = df_te_lab['close'].shift(-k).loc[fired_idx].values.astype(float)
            months  = fired_idx.to_period('M')

            if exit_type == 'trailing':
                # bar-by-bar trailing (MFE/MAE 不使用)
                entry_te = np.where(
                    side == 'LONG',
                    ce_te * (1.0 + SLIPPAGE),
                    ce_te * (1.0 - SLIPPAGE)
                )
                pos_te = pos_of.loc[fired_idx].values.astype(int)
                raw_arr, valid_mask = sim_trailing_bar_by_bar(
                    pos_te, k, side, entry_te, high_arr, low_arr, close_ohlc, n_total
                )
                valid_idx = np.where(valid_mask)[0]
                for vi, raw in zip(valid_idx, raw_arr):
                    ev   = entry_te[vi]
                    fee  = 2 * MAKER_FEE * POSITION_BTC * ev
                    replay_rows.append({
                        'month': str(months[vi]),
                        'combo': f"K{k}_{side}_{q_band}",
                        'net_pnl': float(raw) - fee,
                        'exit_type': exit_type,
                    })

            else:  # fixed_tp or time_exit
                for i in range(len(fired_idx)):
                    ce, mfe, mae, fc = ce_te[i], mfe_te[i], mae_te[i], fc_te[i]
                    if np.isnan(mfe) or np.isnan(mae) or np.isnan(ce): continue
                    mf = mfe / ce; ma = mae / ce
                    entry = ce * (1.0 + SLIPPAGE) if side == 'LONG' else ce * (1.0 - SLIPPAGE)

                    if exit_type == 'fixed_tp':
                        if   mf >= tp_pct: raw = entry * tp_pct * POSITION_BTC
                        elif ma >= sl_pct:  raw = -entry * sl_pct * POSITION_BTC
                        else:
                            if np.isnan(fc): continue
                            raw = ((fc-entry) if side=='LONG' else (entry-fc)) * POSITION_BTC
                    else:  # time_exit
                        if np.isnan(fc): continue
                        raw = ((fc-entry) if side=='LONG' else (entry-fc)) * POSITION_BTC

                    fee = 2 * MAKER_FEE * POSITION_BTC * entry
                    replay_rows.append({
                        'month': str(months[i]),
                        'combo': f"K{k}_{side}_{q_band}",
                        'net_pnl': raw - fee,
                        'exit_type': exit_type,
                    })

        df_replay = pd.DataFrame(replay_rows)
        replay_path = OUT_5_DIR / "replay_entries_option5_v2.csv"
        df_replay.to_csv(replay_path, index=False)
        log(f"  total entries: {len(df_replay)}", lf)

        # 月次集計
        monthly = (df_replay.groupby('month')
                   .agg(n_fires=('net_pnl','count'), net_pnl=('net_pnl','sum'))
                   .reset_index().sort_values('month'))
        monthly_path = OUT_5_DIR / "monthly_pnl_option5_v2.csv"
        monthly.to_csv(monthly_path, index=False)

        # ── 結果出力 ──────────────────────────────────────────────
        log("", lf); log("=" * 60, lf)
        log("Phase 5 月次 PnL v2 (2025)", lf)
        log("=" * 60, lf)
        total_pnl   = float(monthly['net_pnl'].sum())
        total_fires = int(monthly['n_fires'].sum())
        n_pass      = int((monthly['net_pnl'] >= 1900).sum())

        # 勝率集計 (異常値スメルテスト用)
        wins  = int((df_replay['net_pnl'] > 0).sum())
        total_tr = len(df_replay)
        win_rate = wins / total_tr if total_tr > 0 else 0.0
        monthly_max = float(monthly['net_pnl'].max()) if len(monthly) > 0 else 0.0

        for _, r in monthly.iterrows():
            mark = "✅" if r['net_pnl'] >= 1900 else "❌"
            log(f"  {r['month']}  fires={int(r['n_fires']):5d}  net_pnl=${r['net_pnl']:8,.0f}  {mark}", lf)

        log("", lf)
        log(f"  合計 PnL    : ${total_pnl:,.0f}", lf)
        log(f"  月次平均    : ${total_pnl/12:,.0f}/月", lf)
        log(f"  ≥$1,900 達成: {n_pass}/12 ヶ月", lf)
        log(f"  $60/day換算 : ${total_pnl/365:,.0f}/日", lf)
        log(f"  総発火数    : {total_fires:,}", lf)
        log(f"  勝率        : {win_rate*100:.1f}% ({wins}/{total_tr})", lf)
        log(f"  月次最大    : ${monthly_max:,.0f}", lf)
        log("=" * 60, lf)

        # 異常値スメルテスト (false_positive_incident_policy §5 関所A)
        log("", lf)
        log("【異常値スメルテスト】", lf)
        anomaly = []
        if win_rate > 0.70:        anomaly.append(f"① 勝率 {win_rate*100:.1f}% > 70%")
        if monthly_max > 3800:     anomaly.append(f"② 月次最大 ${monthly_max:,.0f} > $3,800")
        if total_pnl/12 > 3800:    anomaly.append(f"② 月次平均 ${total_pnl/12:,.0f} > $3,800")
        # ③ IS/OOS Sharpe 比はこのスクリプト単体では計算不可 → 完了報告時に手動確認
        # ④ 最大 DD はこのスクリプト単体では計算不可 → 完了報告時に確認
        if anomaly:
            log("  ⚠️  異常値・要調査: " + " / ".join(anomaly), lf)
        else:
            log("  ✅ 異常値スメルテスト: ①②チェック クリア（③④は完了報告で確認）", lf)

        # Summary JSON
        t1 = datetime.now()
        summary = {
            "version": "v2",
            "start": t0.isoformat(), "end": t1.isoformat(),
            "duration_sec": round((t1 - t0).total_seconds(), 1),
            "prime_directive_params": {
                "trail_pct": TRAIL_PCT,
                "train_a_end": str(TRAIN_A_END),
                "train_b_start": str(TRAIN_B_START),
                "maker_fee": MAKER_FEE,
                "slippage": SLIPPAGE,
                "position_btc": POSITION_BTC,
            },
            "n_active_combos": len(df_exit),
            "total_test_fires": total_fires,
            "win_rate": round(win_rate, 4),
            "total_net_pnl_usd": round(total_pnl, 2),
            "monthly_avg_pnl_usd": round(total_pnl / 12, 2),
            "pnl_per_day_usd": round(total_pnl / 365, 2),
            "months_ge_1900": n_pass,
            "monthly_max_pnl_usd": round(monthly_max, 2),
            "anomaly_flags": anomaly,
        }
        summary_path = OUT_5_DIR / "phase5_summary_v2.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        log(f"END duration={(t1-t0).total_seconds():.1f}s", lf)
        log(f"LOG: {LOG_PATH}", lf)
        log(f"公式 source: {summary_path}", lf)


if __name__ == "__main__":
    main()
