"""
strat_v9_ml.py — V9ベース ML メタ判定（最初の1手・ratchet E4 候補）

設計（2026-06-04 まこさん GO / strat_v1_design とは別物・V9踏襲）:
  - 候補生成 = V9 の実トレード（replay_csv の regime切り替え出力）をそのまま使う（踏襲・翻訳ミスゼロ）
  - Exit     = V9 のまま（replay が決済済み・net_usd がラベル元）
  - ML       = 各候補に「勝つか（net>0）」を予測 → prob>=θ で採用（メタラベリング）
  - 特徴量   = 5m entry指標(pct化) + MTF(15m/30m/1h/4h・leak-safe) + regime + side + priority
  - 期間     = 学習<2025-04 / 採点2025-04〜12 / 封印2026Q1(不参照)

正直な近似（path依存）: 採用フィルタは「トレードを消す」だけ。枠が空いて新たに開いた
はずの取引は再現しない（loop内版は次段）。まず信号が出るか $172 と比較して測る。

§4.6 照合: H2(leak・train末<採点始 assert + exit_time embargo) / H6(価格非依存・pct化 assert) /
            H8(期間分割 assert) / H1・H9(サイズはreplay側=0.024固定) / H13(score.py/eval_engine不変)
V9本体（cat_v9_decider.py / cat_params_v9.json / run_once_v9.py / replay_csv.py）は一切変更しない。
"""
from __future__ import annotations
import pathlib, sys
import numpy as np
import pandas as pd
import ta
import lightgbm as lgb
from sklearn.metrics import roc_auc_score

ROOT = pathlib.Path(__file__).resolve().parents[2]
TRADES_CSV = ROOT / "results" / "replay_BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"
OHLCV_CSV  = ROOT / "data"    / "BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"
OUT_DIR    = ROOT / "results" / "priority_rebuild" / "ratchet"

TRAIN_END   = pd.Timestamp("2025-04-01")   # 学習は < これ
SCORE_START = pd.Timestamp("2025-04-01")
SCORE_END   = pd.Timestamp("2026-01-01")   # 採点は [START, END) = 2025-04〜12
THETA       = 0.50                          # 採用閾値（ツマミ）

# 5m entry 特徴（replay 出力列）。価格依存(USD絶対値)は pct 化する。
NUM_5M_RAW   = ["adx_at_entry", "rsi_at_entry", "rsi_slope_at_entry", "ret_5",
                "stoch_k_at_entry", "stoch_d_at_entry", "bb_width_at_entry",
                "entry_hour", "entry_weekday"]          # これらは無次元/pct/比率/時刻
PRICE_DEP    = ["atr_14", "bb_mid_slope_at_entry"]      # USD絶対値 → /entry_price で pct 化
CAT_COLS     = ["side_code", "priority", "regime_code"]
MTF_TFS      = {"15m": "15min", "30m": "30min", "1h": "60min", "4h": "240min"}


def _log(m): print(m, flush=True)


# ----------------------------------------------------------------------
# MTF 特徴（leak-safe）: 上位足を resample → 指標 → 「確定済みバーのみ」を entry に merge_asof
# ----------------------------------------------------------------------
def build_mtf_features(ohlcv: pd.DataFrame, entry_times: pd.Series) -> pd.DataFrame:
    o = ohlcv.set_index("timestamp").sort_index()
    out = pd.DataFrame({"entry_time": entry_times.values})
    et = pd.DataFrame({"entry_time": pd.to_datetime(entry_times.values)}).sort_values("entry_time")

    for tag, freq in MTF_TFS.items():
        bars = o.resample(freq, label="left", closed="left").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
        c, h, l = bars["close"], bars["high"], bars["low"]
        feat = pd.DataFrame(index=bars.index)
        feat[f"rsi_{tag}"]          = ta.momentum.RSIIndicator(c, 14).rsi()
        feat[f"adx_{tag}"]          = ta.trend.ADXIndicator(h, l, c, 14).adx()
        ema20                       = ta.trend.EMAIndicator(c, 20).ema_indicator()
        feat[f"close_vs_ema20_{tag}_pct"] = (c - ema20) / c * 100.0      # pct
        bb = ta.volatility.BollingerBands(c, 20)
        upper, lower = bb.bollinger_hband(), bb.bollinger_lband()
        feat[f"bb_pctb_{tag}"]      = (c - lower) / (upper - lower).replace(0, np.nan)  # 0-1 比率
        st = ta.momentum.StochasticOscillator(h, l, c, 14, 3)
        feat[f"stoch_k_{tag}"]      = st.stoch()                          # 0-100
        # 確定時刻 = バー開始 + 足幅（このバーの close は次足開始時に確定）→ leak-safe
        feat["avail_time"] = feat.index + pd.Timedelta(freq)
        feat = feat.dropna(subset=["avail_time"]).sort_values("avail_time")
        merged = pd.merge_asof(et, feat.reset_index(drop=True),
                               left_on="entry_time", right_on="avail_time",
                               direction="backward")
        merged = merged.drop(columns=["avail_time"])
        et = merged  # 次の TF を順に結合
    # 元の entry_times 順に並べ直す
    et = et.set_index("entry_time")
    return et.reindex(pd.to_datetime(entry_times.values)).reset_index(drop=True)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for p in (TRADES_CSV, OHLCV_CSV):
        if not p.exists():
            sys.exit(f"ABORT: 入力が無い {p}（先に replay を回す）")

    tr = pd.read_csv(TRADES_CSV)
    tr["entry_time"] = pd.to_datetime(tr["entry_time"])
    tr["exit_time"]  = pd.to_datetime(tr["exit_time"])
    _log(f"[load] trades={len(tr)}  range {tr['entry_time'].min()} 〜 {tr['entry_time'].max()}")

    ohlcv = pd.read_csv(OHLCV_CSV)
    ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])

    # --- 特徴量組み立て ---
    tr["side_code"]   = (tr["side"] == "LONG").astype(int)
    tr["regime_code"] = tr["regime"].astype("category").cat.codes
    for col in PRICE_DEP:                          # H6: USD絶対値 → pct
        tr[col + "_pct"] = tr[col] / tr["entry_price"] * 100.0
    price_pct_cols = [c + "_pct" for c in PRICE_DEP]

    mtf = build_mtf_features(ohlcv, tr["entry_time"])
    feat_cols = NUM_5M_RAW + price_pct_cols + CAT_COLS + list(mtf.columns)
    X = pd.concat([tr[NUM_5M_RAW + price_pct_cols + CAT_COLS].reset_index(drop=True),
                   mtf.reset_index(drop=True)], axis=1)
    y = (tr["net_usd"] > 0).astype(int).values

    # --- H6 assert: 生の価格列が特徴量に混ざっていない ---
    banned = {"entry_price", "exit_price", "atr_14", "bb_mid_slope_at_entry",
              "gross_usd", "fee_usd", "net_usd", "mfe_usd", "mae_usd", "tp_diff_usd"}
    leaked = banned & set(X.columns)
    assert not leaked, f"H6/leak: 価格依存 or 結果列が特徴量に混入 {leaked}"

    # --- 期間分割 + H8/H2 assert ---
    is_train = tr["entry_time"] < TRAIN_END
    # H2 embargo: 学習トレードの exit が採点期間に食い込むものは除外（ラベル漏れ防止）
    embargo = is_train & (tr["exit_time"] >= SCORE_START)
    is_train_clean = is_train & ~embargo
    is_score = (tr["entry_time"] >= SCORE_START) & (tr["entry_time"] < SCORE_END)

    assert tr.loc[is_train_clean, "exit_time"].max() < SCORE_START, "H2: 学習に採点期間の未来が漏れている"
    assert tr.loc[is_train_clean, "entry_time"].max() < TRAIN_END,  "H8: 学習期間境界違反"
    _log(f"[split] train={is_train.sum()} (embargo除外 {embargo.sum()} → clean {is_train_clean.sum()}) "
         f"/ score={is_score.sum()}  (封印2026Q1は除外)")

    Xtr, ytr = X[is_train_clean.values], y[is_train_clean.values]
    Xsc, ysc = X[is_score.values],       y[is_score.values]
    _log(f"[label] train 勝率={ytr.mean():.3f} / score 勝率(参考)={ysc.mean():.3f}")

    # --- LightGBM 学習（学習内 時系列valid で early stopping）---
    cat_idx = [X.columns.get_loc(c) for c in CAT_COLS]
    n = len(Xtr); cut = int(n * 0.85)
    dtr = lgb.Dataset(Xtr.iloc[:cut], label=ytr[:cut], categorical_feature=cat_idx)
    dva = lgb.Dataset(Xtr.iloc[cut:], label=ytr[cut:], categorical_feature=cat_idx, reference=dtr)
    params = dict(objective="binary", metric="auc", learning_rate=0.03,
                  num_leaves=31, min_child_samples=100, feature_fraction=0.8,
                  bagging_fraction=0.8, bagging_freq=1, seed=42, verbose=-1)
    model = lgb.train(params, dtr, num_boost_round=2000, valid_sets=[dva],
                      callbacks=[lgb.early_stopping(80, verbose=False)])
    _log(f"[train] best_iter={model.best_iteration}")

    # --- 採点期間で予測・AUC ---
    psc = model.predict(Xsc, num_iteration=model.best_iteration)
    if len(np.unique(ysc)) > 1:
        _log(f"[score] AUC={roc_auc_score(ysc, psc):.4f}  (>0.5 なら選別力あり)")

    # --- θ で採用 → フィルタ済みトレードを出力 ---
    sc = tr[is_score].copy().reset_index(drop=True)
    sc["ml_prob"] = psc
    kept = sc[sc["ml_prob"] >= THETA].copy()
    _log(f"[filter] θ={THETA}: 採点候補 {len(sc)} → 採用 {len(kept)} (見送り {len(sc)-len(kept)})")

    unfilt_path = OUT_DIR / "trades_v9_score_unfiltered.csv"   # $172 再現確認用
    filt_path   = OUT_DIR / "trades_v9ml_score.csv"            # ML 採用後
    sc.to_csv(unfilt_path, index=False)
    kept.to_csv(filt_path, index=False)
    _log(f"[out] unfiltered → {unfilt_path}")
    _log(f"[out] ML filtered → {filt_path}")
    _log("\n次: score.py を両方に通して net を $172 と比較\n"
         f"  unfiltered（$172再現の確認）/ filtered（ML効果）")

    # 重要特徴 top15
    imp = pd.Series(model.feature_importance(importance_type="gain"),
                    index=X.columns).sort_values(ascending=False)
    _log("[feat importance top15]\n" + imp.head(15).to_string())


if __name__ == "__main__":
    main()
