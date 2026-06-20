#!/usr/bin/env python3
"""strat_v1.py — ratchet E2「最初の本物の戦略」（設計: .claude/ratchet/strat_v1_design.md）

選手（戦略）。審判 score.py に通す売買記録 CSV を生成する。戦略ロジックのみを持ち、
約定・コスト・出口・不約定は計器 eval_engine（改造禁止・H13）に委ねる。

設計（A・ツマミ）:
  - 特徴量: 手動材料（複数期間×複数足×ローソク足の形×時間軸）+ regime。閾値は木が学習。
  - モデル: LONG/SHORT 別 LightGBM 2値。ラベル = 固定出口で simulate して net>0 なら勝ち(1)。
  - 出口: 固定 maker（LONG TP0.6%/SL2%/96bar・SHORT TP0.8%/SL2%/96bar）。
  - サイズ: 1ポジ 0.024 BTC・同時保有合計 ≤ 0.12（H1）。エントリー閾値 θ=0.5。

B 関所（assert で物理停止＝偽の数字を出さない）:
  H2 leak  : 特徴量は parquet 確定値（phase_compliance Step5 で leak verify 済）/ ラベルは未来 simulate
             だが教師のみで X に入れない / train 末 < 採点始 − embargo を assert。
  H6 価格非依存: 特徴量から USD 絶対値列（macd 生・sma 生・ichimoku 生）を除外し assert。
  H8 期間分割: 学習 = train(〜2024-12) のみ fit / 採点 = test2025 の 2025-04〜12 のみ。
  H9 最小注文: size 0.024 ≥ 0.0001 BTC ∧ ×price ≥ 5 USDT を assert。
  H1 上限   : 同時保有合計 ≤ 0.12 を enforce（eval_engine.assert_position_cap）。
  H12 異常値: 採点後に勝率/月NET を score.py で見る（本スクリプトは件数のみ）。

実行:
  スモーク（先頭2万行・動作確認）: python3 strat_v1.py --smoke
  本番（採点用 CSV 生成・重い→ caffeinate + 絶対パス background）: python3 strat_v1.py
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eval_engine as ee  # noqa: E402  改造禁止の計器（既知答えテスト pass 済）
import lightgbm as lgb    # noqa: E402

REPO = Path(HERE).resolve().parents[1]  # bitget-python-sdk-api
DATA_CSV = REPO / "data" / "BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv"
PQ = REPO / "results" / "priority_rebuild"
REGIME = REPO / "results" / "regime_step1"
OUTDIR = PQ / "ratchet"
TRAIN_PQ = PQ / "labels_mfe_mae_pct_train_2021_2024.parquet"
TEST_PQ = PQ / "labels_mfe_mae_pct_test_2025.parquet"
REGIME_TRAIN = REGIME / "regime_predictions_train_2021_2024.parquet"
REGIME_TEST = REGIME / "regime_predictions_test_2025.parquet"

# ── 設計パラメータ（A・ツマミ・数字で判定）──────────────────────────────────
SIDE_PARAMS = {  # E3: 先生を厳しく = TP/SL を対称1:1 に是正（0.6-0.8%/2% → 1.0%/1.0%）
    "LONG":  dict(direction=ee.LONG,  tp=0.010, sl=0.010, hold=96),
    "SHORT": dict(direction=ee.SHORT, tp=0.010, sl=0.010, hold=96),
}
SIZE_BTC = 0.024
THETA = 0.5
EMBARGO_BARS = 96
SCORE_START = pd.Timestamp("2025-04-01")
SCORE_END = pd.Timestamp("2025-12-31 23:59:59")

# H6: USD 絶対値 blacklist（phase_compliance §-1）。_pct を持たない生指標を除外。
USD_BL = ["macd_line__", "macd_signal__", "macd_hist__", "macd_hist_change__",
          "sma_20__", "sma_50__", "ichimoku_kijun", "ichimoku_tenkan"]
# 手動材料の include パターン（複数期間×複数足×ローソク足×時間軸は parquet に既存）
INC = ["adx", "atr14_pct", "rsi", "stoch", "rci_", "bb_", "close_vs_ema", "macd",
       "location_prev", "entry_risk_score", "wick_ratio", "body_ratio", "body_direction",
       "close_to_high_pct", "close_to_low_pct", "new_high_streak", "new_low_streak",
       "cdl_", "significant_wick"]
REGIME_FEATS = ["regime_prob_up", "regime_prob_down", "regime_prob_range", "regime_confidence",
                "regime_is_uptrend", "regime_is_downtrend", "regime_is_range", "regime_is_unclear"]


def log(m):
    print(m, flush=True)


def select_features(all_cols):
    """手動材料に対応する列を select。ラベル列と USD 絶対値列は除外（H6）。"""
    feats = []
    for c in all_cols:
        if c in ("timestamp", "close", "open", "high", "low", "volume", "is_maintenance"):
            continue
        if c.startswith(("LONG_", "SHORT_")):  # MFE/MAE ラベル列を除外
            continue
        if any(b in c for b in USD_BL) and "_pct" not in c:  # H6 USD 絶対値除外
            continue
        if any(k in c for k in INC):
            feats.append(c)
    return feats


def assert_h6(feats):
    bad = [c for c in feats if any(b in c for b in USD_BL) and "_pct" not in c]
    assert not bad, f"H6違反(USD絶対値混入): {bad[:5]}"
    log(f"[H6] 価格非依存 OK・特徴量 {len(feats)} 列（USD絶対値 blacklist 除外済）")


def load_ohlc():
    """生 5m OHLC（約定 simulate 用）。timestamp 昇順の numpy 配列を返す。"""
    df = pd.read_csv(DATA_CSV)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    arrays = (df["open"].to_numpy(float), df["high"].to_numpy(float),
              df["low"].to_numpy(float), df["close"].to_numpy(float),
              df["timestamp"].to_numpy())  # datetime64
    ts2idx = {pd.Timestamp(t): i for i, t in enumerate(df["timestamp"])}
    return arrays, ts2idx


def make_labels(side, feat_index, ts2idx, arrays):
    """train の各 bar を固定出口で simulate → net>0:勝ち(1)/負け(0)/不約定:NaN（学習対象外）。"""
    p = SIDE_PARAMS[side]
    opens, highs, lows, closes, tss = arrays
    ys = np.full(len(feat_index), np.nan)
    n = len(feat_index)
    for k, ts in enumerate(feat_index):
        si = ts2idx.get(ts)
        if si is None:
            continue
        r = ee.simulate_trade(si, p["direction"], SIZE_BTC, opens, highs, lows, closes, tss,
                              p["tp"], p["sl"], p["hold"])
        if r is not None:
            ys[k] = 1.0 if r.net > 0 else 0.0
        if k % 50000 == 0:
            log(f"  [{side}] label {k:,}/{n:,}")
    return ys


def train_model(X, y, feat_names):
    """末尾10%を valid に early stopping。NaN ラベル（不約定）は学習対象外。"""
    mask = ~np.isnan(y)
    Xt, yt = X[mask], y[mask].astype(int)
    cut = int(len(Xt) * 0.9)
    dtr = lgb.Dataset(Xt[:cut], yt[:cut], feature_name=feat_names)
    dva = lgb.Dataset(Xt[cut:], yt[cut:], feature_name=feat_names, reference=dtr)
    params = dict(objective="binary", metric="binary_logloss", verbose=-1, seed=42,
                  learning_rate=0.05, num_leaves=63)
    m = lgb.train(params, dtr, num_boost_round=600, valid_sets=[dva],
                  callbacks=[lgb.early_stopping(50, verbose=False)])
    pos = int(yt.sum()); tot = len(yt)
    log(f"  fit n={tot:,} 勝ち率(ラベル)={pos/tot:.3f} best_iter={m.best_iteration}")
    return m


def run_score_period(models, Xte, feat_names, ts2idx, arrays):
    """採点期間で bar 順に θ 判定 → entry → simulate。H1 合計上限を enforce。"""
    opens, highs, lows, closes, tss = arrays
    proba = {s: models[s].predict(Xte[feat_names].to_numpy()) for s in models}
    active = []   # 保有中の exit_idx
    trades = []
    for k, ts in enumerate(Xte.index):
        si = ts2idx.get(ts)
        if si is None:
            continue
        active = [e for e in active if e > si]  # 決済済みを除去
        cand = sorted([(proba[s][k], s) for s in models if proba[s][k] >= THETA], reverse=True)
        if not cand:
            continue
        _, s = cand[0]  # 排他=高確率 side 1つ（手動の先勝ちに対応）
        # H1: 合計 ≤ 0.12（assert_position_cap で物理検証）
        try:
            ee.assert_position_cap([SIZE_BTC] * (len(active) + 1))
        except AssertionError:
            continue  # 上限到達 → skip
        p = SIDE_PARAMS[s]
        r = ee.simulate_trade(si, p["direction"], SIZE_BTC, opens, highs, lows, closes, tss,
                              p["tp"], p["sl"], p["hold"])
        if r is None:
            continue  # 不約定 = 取引不成立
        active.append(r.exit_idx)
        trades.append(dict(entry_time=pd.Timestamp(tss[r.fill_idx]), exit_time=pd.Timestamp(tss[r.exit_idx]),
                           side=s, size_btc=SIZE_BTC, entry_price=r.entry_price,
                           exit_price=r.exit_price, exit_reason=r.exit_reason))
    return pd.DataFrame(trades)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="先頭2万行で動作確認")
    a = ap.parse_args()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    log("=" * 64)
    log(f"strat_v1 {'[SMOKE]' if a.smoke else '[本番]'} 開始")
    log("=" * 64)

    # 生 OHLC + 特徴量列
    arrays, ts2idx = load_ohlc()
    import pyarrow.parquet as pq
    feats = select_features(pq.ParquetFile(TRAIN_PQ).schema.names)
    assert_h6(feats)
    feat_all = feats + REGIME_FEATS

    # train 特徴量 + regime
    Xtr = pd.read_parquet(TRAIN_PQ, columns=feats).join(
        pd.read_parquet(REGIME_TRAIN, columns=REGIME_FEATS), how="left")
    if a.smoke:
        Xtr = Xtr.iloc[:20000]

    # H8/H2: train 末 < 採点始 − embargo
    assert Xtr.index.max() < SCORE_START - pd.Timedelta(minutes=5 * EMBARGO_BARS), \
        f"H8/H2 embargo違反: train末 {Xtr.index.max()} ≥ 採点始 {SCORE_START} − {EMBARGO_BARS}bar"
    log(f"[H8/H2] train末 {Xtr.index.max()} < 採点始 {SCORE_START}（embargo {EMBARGO_BARS}bar）OK")
    # H9: 最小注文
    px0 = arrays[3][0]
    assert SIZE_BTC >= 0.0001 and SIZE_BTC * px0 >= 5.0, "H9 最小注文違反"
    log(f"[H9] 最小注文 OK（{SIZE_BTC} BTC ≥ 0.0001 ∧ ×${px0:.0f} ≥ 5 USDT）")

    # ラベル生成 + 側別学習
    models = {}
    for s in SIDE_PARAMS:
        y = make_labels(s, Xtr.index, ts2idx, arrays)
        models[s] = train_model(Xtr[feat_all].to_numpy(), y, feat_all)
        log(f"[train] {s} 完了")

    # 採点期間 test（2025-04〜12）で推論 → entry → simulate
    Xte = pd.read_parquet(TEST_PQ, columns=feats).join(
        pd.read_parquet(REGIME_TEST, columns=REGIME_FEATS), how="left")
    Xte = Xte[(Xte.index >= SCORE_START) & (Xte.index <= SCORE_END)]
    if a.smoke:
        Xte = Xte.iloc[:20000]
    log(f"[採点期間] {Xte.index.min()} 〜 {Xte.index.max()}  n={len(Xte):,}")
    trades = run_score_period(models, Xte, feat_all, ts2idx, arrays)

    out = OUTDIR / ("trades_v1_smoke.csv" if a.smoke else "trades_v1.csv")
    trades.to_csv(out, index=False)
    log("-" * 64)
    log(f"[out] {out}  trades={len(trades)}")
    if len(trades):
        log(f"  side別: {trades['side'].value_counts().to_dict()}")
        log(f"  exit別: {trades['exit_reason'].value_counts().to_dict()}")
    log(f"次: python3 {HERE}/score.py {out} --start 2025-04-01 --end 2025-12-31")


if __name__ == "__main__":
    main()
