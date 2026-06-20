"""
strat_v9ml_p23.py — V9ベース ML（ratchet E5・Priority別 + net金額目的）

E4（strat_v9_ml.py・破棄）からの直し（session_log_20260605 §4 の根本2点を閉じる）:
  ① ラベル = 勝率(net>0 二値) → **net_usd の金額**（回帰・Huber 損失で fat-tail 過学習を抑える）
  ② スタイル違い Priority を1モデルに混在 → **P23 のみ**で学習（混ぜない）

踏襲（V9・変えない）:
  候補生成 = V9 replay の実トレード（regime切替・全部入り出力）から P23 SHORT のみ抽出
  Exit     = V9 のまま（replay が決済済み・net_usd がラベル元・E5 では Exit は振らない＝E6）

正直な近似（path依存・E4 と同じ）: 採用フィルタは「トレードを消す」だけ。枠が空いて新たに
開いたはずの取引は再現しない。E5 は「net目的 ML が P23 で value を足すか」の検証（filter）。
サイジング（de Prado・予測 net で size）は次段 E6。

判定軸: P23-無filter（技術検証の地） 対 P23-net目的filter。全Priority地面$172は P23単独
（$916/9mo≈$102/mo）では構造的に超えられない（部分集合・filterは削るだけ）。効けば E6 で
サイジング＋他Priority展開で $1,900 を狙う（設計§5②）。

§4.6 照合: H2(leak・MTF backward merge・net_usd は教師のみ・train末<採点始 assert + embargo) /
            H6(価格非依存・pct化 assert・banned列 assert) / H8(期間分割 assert) /
            H1・H9(size は replay 側 0.024 固定) / H13(score.py/eval_engine 不変)
V9本体（cat_v9_decider.py / cat_params_v9.json / run_once_v9.py / replay_csv.py）は一切変更しない。
"""
from __future__ import annotations
import pathlib, sys
import numpy as np
import pandas as pd
import ta
import lightgbm as lgb
from scipy.stats import spearmanr

ROOT = pathlib.Path(__file__).resolve().parents[2]
TRADES_CSV = ROOT / "results" / "replay_BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"
OHLCV_CSV  = ROOT / "data"    / "BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"
OUT_DIR    = ROOT / "results" / "priority_rebuild" / "ratchet"

PRIORITY    = 23                            # E5 = P23 SHORT のみ（スタイル別・混ぜない）
TRAIN_END   = pd.Timestamp("2025-04-01")    # 学習は < これ
SCORE_START = pd.Timestamp("2025-04-01")
SCORE_END   = pd.Timestamp("2026-01-01")    # 採点は [START, END) = 2025-04〜12（封印2026Q1は不参照）

# 5m entry 特徴（replay 出力列）。価格依存(USD絶対値)は pct 化する（H6）。priority は P23 固定で除外。
NUM_5M_RAW   = ["adx_at_entry", "rsi_at_entry", "rsi_slope_at_entry", "ret_5",
                "stoch_k_at_entry", "stoch_d_at_entry", "bb_width_at_entry",
                "entry_hour", "entry_weekday"]          # 無次元/pct/比率/時刻
PRICE_DEP    = ["atr_14", "bb_mid_slope_at_entry"]      # USD絶対値 → /entry_price で pct 化
CAT_COLS     = ["regime_code"]                          # side は P23=SHORT 固定で除外
MTF_TFS      = {"15m": "15min", "30m": "30min", "1h": "60min", "4h": "240min"}


def _log(m): print(m, flush=True)


# ----------------------------------------------------------------------
# MTF 特徴（leak-safe）: 上位足を resample → 指標 → 「確定済みバーのみ」を entry に merge_asof
# （E4 build_mtf_features と同一・leak verify 済の構造を踏襲）
# ----------------------------------------------------------------------
def build_mtf_features(ohlcv: pd.DataFrame, entry_times: pd.Series) -> pd.DataFrame:
    o = ohlcv.set_index("timestamp").sort_index()
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
        et = merged.drop(columns=["avail_time"])
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

    # --- Priority別（E5 = P23 のみ・混ぜない）---
    tr = tr[tr["priority"] == PRIORITY].copy().reset_index(drop=True)
    assert (tr["side"] == "SHORT").all(), f"P{PRIORITY} は SHORT のみ想定だが LONG 混入"
    _log(f"[load] P{PRIORITY} trades={len(tr)}  range {tr['entry_time'].min()} 〜 {tr['entry_time'].max()}")

    ohlcv = pd.read_csv(OHLCV_CSV)
    ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])

    # --- 特徴量組み立て ---
    tr["regime_code"] = tr["regime"].astype("category").cat.codes
    for col in PRICE_DEP:                          # H6: USD絶対値 → pct
        tr[col + "_pct"] = tr[col] / tr["entry_price"] * 100.0
    price_pct_cols = [c + "_pct" for c in PRICE_DEP]

    mtf = build_mtf_features(ohlcv, tr["entry_time"])
    X = pd.concat([tr[NUM_5M_RAW + price_pct_cols + CAT_COLS].reset_index(drop=True),
                   mtf.reset_index(drop=True)], axis=1)
    y = tr["net_usd"].astype(float).values         # ラベル = net 金額そのもの（回帰・E4 の二値を捨てる）

    # --- H6 assert: 生の価格列・結果列が特徴量に混ざっていない ---
    banned = {"entry_price", "exit_price", "atr_14", "bb_mid_slope_at_entry",
              "gross_usd", "fee_usd", "net_usd", "mfe_usd", "mae_usd", "tp_diff_usd"}
    leaked = banned & set(X.columns)
    assert not leaked, f"H6/leak: 価格依存 or 結果列が特徴量に混入 {leaked}"

    # --- 期間分割 + H8/H2 assert ---
    is_train = tr["entry_time"] < TRAIN_END
    embargo  = is_train & (tr["exit_time"] >= SCORE_START)   # 学習 exit が採点に食い込む→ラベル漏れ防止
    is_train_clean = is_train & ~embargo
    is_score = (tr["entry_time"] >= SCORE_START) & (tr["entry_time"] < SCORE_END)

    assert tr.loc[is_train_clean, "exit_time"].max() < SCORE_START, "H2: 学習に採点期間の未来が漏れている"
    assert tr.loc[is_train_clean, "entry_time"].max() < TRAIN_END,  "H8: 学習期間境界違反"
    _log(f"[split] train={is_train.sum()} (embargo除外 {embargo.sum()} → clean {is_train_clean.sum()}) "
         f"/ score={is_score.sum()}  (封印2026Q1は除外)")

    Xtr, ytr = X[is_train_clean.values], y[is_train_clean.values]
    Xsc, ysc = X[is_score.values],       y[is_score.values]
    _log(f"[label] train net: mean=${ytr.mean():.2f} median=${np.median(ytr):.2f} "
         f"勝率(参考)={ (ytr>0).mean():.3f} / score net mean(参考)=${ysc.mean():.2f}")

    # --- LightGBM 回帰（Huber 損失で fat-tail 過学習を抑える・学習内 時系列valid で early stopping）---
    cat_idx = [X.columns.get_loc(c) for c in CAT_COLS]
    n = len(Xtr); cut = int(n * 0.85)
    dtr = lgb.Dataset(Xtr.iloc[:cut], label=ytr[:cut], categorical_feature=cat_idx)
    dva = lgb.Dataset(Xtr.iloc[cut:], label=ytr[cut:], categorical_feature=cat_idx, reference=dtr)
    params = dict(objective="huber", alpha=0.9, metric="huber", learning_rate=0.03,
                  num_leaves=15, min_child_samples=20, feature_fraction=0.8,
                  bagging_fraction=0.8, bagging_freq=1, seed=42, verbose=-1)
    model = lgb.train(params, dtr, num_boost_round=2000, valid_sets=[dva],
                      callbacks=[lgb.early_stopping(80, verbose=False)])
    _log(f"[train] best_iter={model.best_iteration}")

    # --- 採点期間で予測 net・順位相関（E4 の corr(prob,net)=-0.027 と対比）---
    psc = model.predict(Xsc, num_iteration=model.best_iteration)
    if len(ysc) > 2:
        rho, _ = spearmanr(psc, ysc)
        _log(f"[score] Spearman(pred_net, 実net)={rho:.4f}  (>0 なら net 順位の選別力あり・E4 は corr -0.027)")

    # --- θ 掃引: 予測 net ≥ θ で採用 → score.py で net 比較 ---
    sc = tr[is_score].copy().reset_index(drop=True)
    sc["pred_net"] = psc
    # 無filter（P23 単独の地）と filter 済みを両方出力
    unfilt_path = OUT_DIR / f"trades_v9ml_p{PRIORITY}_unfiltered.csv"
    sc.to_csv(unfilt_path, index=False)
    _log(f"[out] P{PRIORITY} 無filter → {unfilt_path}（採点 {len(sc)}件・実net合計 ${sc['net_usd'].sum():.1f}）")

    _log("[θ掃引・参考(CSV net・slippage/funding 抜き)]")
    for th in [None, sc['pred_net'].quantile(0.25), sc['pred_net'].quantile(0.5),
               sc['pred_net'].quantile(0.75), 0.0]:
        kept = sc if th is None else sc[sc["pred_net"] >= th]
        tag = "無filter" if th is None else f"θ={th:.2f}"
        _log(f"  {tag:>14}: 採用 {len(kept):3d}/{len(sc)}  CSV net ${kept['net_usd'].sum():8.1f}  "
             f"avg ${kept['net_usd'].mean() if len(kept) else 0:6.2f}")

    # 採点用 filter 済みファイル（θ=0：予測 net が正のものを採用）を出力 → score.py に通す
    th0 = 0.0
    kept0 = sc[sc["pred_net"] >= th0].copy()
    filt_path = OUT_DIR / f"trades_v9ml_p{PRIORITY}_filtered.csv"
    kept0.to_csv(filt_path, index=False)
    _log(f"[out] P{PRIORITY} filter(θ=0・予測net≥0) → {filt_path}（採用 {len(kept0)}件）")

    # 重要特徴 top15
    imp = pd.Series(model.feature_importance(importance_type="gain"),
                    index=X.columns).sort_values(ascending=False)
    _log("[feat importance top15]\n" + imp.head(15).to_string())
    _log("\n次: score.py を 無filter / filtered 両方に通して採点期間 net を比較\n"
         f"  python3 scripts/priority_rebuild/score.py {unfilt_path} --start 2025-04-01 --end 2025-12-31\n"
         f"  python3 scripts/priority_rebuild/score.py {filt_path}   --start 2025-04-01 --end 2025-12-31")


if __name__ == "__main__":
    main()
