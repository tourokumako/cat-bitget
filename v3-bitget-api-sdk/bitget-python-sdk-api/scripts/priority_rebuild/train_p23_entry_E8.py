"""
train_p23_entry_E8.py — P23「最初に入るか」を AI 学習（ratchet E8・E6改修）

【E8 変更点】ラベルを ○×(勝つか net>0) → 「**伸びるか**」（含み益ピークが価格%≥0.8 の二値）に変更。
E6 の「勝つか」は大勝ちを切った（fat-tail・corr逆較正）。「伸びるか」は伸びた大勝ち玉を全部○にし切らない。
特徴量(5m+MTF)・段取り・θ*学習側net最大化は E6 踏襲。出力は E番号(E08)付き。

土台: gen_p23_candidates.py が出した候補（V9の add/exit 込み net 付き・自己検査でV9と一致確認済）。
やること:
  - typeonly 候補（型だけで広げた50,328件）で「うまくいくか（net>0）」を **○×分類** で学習
    （金額回帰=E5は弱かった / 分類>回帰は WebSearch 裏取り 2026-06-05）
  - 手がかり = 入口時点の指標（atr/bb_slope は pct化=H6）＋ MTF(15m/30m/1h/4h・leak-safe)。
    結果列（add_count/hold_min/exit_price/mfe/mae/net 等）は除外（H2 leak防止）。regime列は空→MTFで代替。
  - 過学習対策（num_leaves小・min_child大・L1/L2・time-series early stopping）
  - 期間: 学習<2025-04(embargo: exit<2025-04) / テスト2025-04〜12 / 封印2026Q1不参照
  - 判定: θ* は **学習側で net 最大化** して決め（test覗き見=類型C 回避）テストに適用
          → score.py で「AI選択(test)」 vs 「V9手書き full(test)」を採点比較

§4.6: H2(leak・特徴量は入口のみ・netは教師・train末<test始 assert) / H6(pct化・banned assert) /
       H8(期間分割 assert) / H13(score.py import・改造なし) / H1(注記: 独立評価は同時保有cap未適用=技術検証)
V9本体・score.py・eval_engine は import のみ・改造しない。
"""
from __future__ import annotations
import sys, pathlib, json
import numpy as np
import pandas as pd
import ta
import lightgbm as lgb
from sklearn.metrics import roc_auc_score

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import score as judge                                   # 審判（import のみ・改造しない）

RAT = ROOT / "results" / "priority_rebuild" / "ratchet"
TYPEONLY = RAT / "p23_candidates_typeonly.csv"
FULL     = RAT / "p23_candidates_full.csv"
OHLCV    = ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"

TRAIN_END = pd.Timestamp("2025-04-01")
MFE_MOVE_THRESH_PCT = 0.8   # E8「伸びた」閾値=含み益ピークの価格下落率%（学習期間で伸びた群net最大$75623・size/価格非依存H6）
SC_START, SC_END = pd.Timestamp("2025-04-01"), pd.Timestamp("2026-01-01")

NUM_RAW = ["adx_at_entry", "rsi_at_entry", "rsi_slope_at_entry", "ret_5",
           "stoch_k_at_entry", "stoch_d_at_entry", "bb_width_at_entry", "entry_hour", "entry_weekday"]
PRICE_DEP = ["atr_14", "bb_mid_slope_at_entry"]          # USD絶対値 → pct化（H6）
MTF_TFS = {"15m": "15min", "30m": "30min", "1h": "60min", "4h": "240min"}
BANNED = {"net_usd", "gross_usd", "fee_usd", "mfe_usd", "mae_usd", "tp_diff_usd",
          "exit_price", "exit_reason", "hold_min", "add_count", "size_btc", "entry_price"}  # 結果列=leak


def _log(m): print(m, flush=True)


def build_mtf(ohlcv, entry_times):
    """上位足を resample→指標→確定済みバーのみ backward merge（gen/E5 と同一・leak-safe）。"""
    o = ohlcv.set_index("timestamp").sort_index()
    et = pd.DataFrame({"entry_time": pd.to_datetime(entry_times.values)}).sort_values("entry_time")
    for tag, freq in MTF_TFS.items():
        bars = o.resample(freq, label="left", closed="left").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
        c, h, l = bars["close"], bars["high"], bars["low"]
        f = pd.DataFrame(index=bars.index)
        f[f"rsi_{tag}"] = ta.momentum.RSIIndicator(c, 14).rsi()
        f[f"adx_{tag}"] = ta.trend.ADXIndicator(h, l, c, 14).adx()
        ema = ta.trend.EMAIndicator(c, 20).ema_indicator()
        f[f"close_vs_ema20_{tag}_pct"] = (c - ema) / c * 100.0
        bb = ta.volatility.BollingerBands(c, 20)
        f[f"bb_pctb_{tag}"] = (c - bb.bollinger_lband()) / (bb.bollinger_hband() - bb.bollinger_lband()).replace(0, np.nan)
        f[f"stoch_k_{tag}"] = ta.momentum.StochasticOscillator(h, l, c, 14, 3).stoch()
        f["avail_time"] = f.index + pd.Timedelta(freq)
        f = f.dropna(subset=["avail_time"]).sort_values("avail_time")
        et = pd.merge_asof(et, f.reset_index(drop=True), left_on="entry_time", right_on="avail_time",
                           direction="backward").drop(columns=["avail_time"])
    et = et.set_index("entry_time")
    return et.reindex(pd.to_datetime(entry_times.values)).reset_index(drop=True)


def make_features(df, ohlcv):
    for c in PRICE_DEP:
        df[c + "_pct"] = df[c] / df["entry_price"] * 100.0          # H6
    mtf = build_mtf(ohlcv, df["entry_time"])
    X = pd.concat([df[NUM_RAW + [c + "_pct" for c in PRICE_DEP]].reset_index(drop=True),
                   mtf.reset_index(drop=True)], axis=1)
    leaked = BANNED & set(X.columns)
    assert not leaked, f"H2/H6 leak: 結果列が特徴量に混入 {leaked}"
    return X


def _edge(df, col, edges):
    """指標を帯に切り、実netが平均プラスの帯の範囲[下端, 上端]を返す（±無限は None=開放端）。"""
    b = pd.cut(df[col], edges, right=False)
    m = df.groupby(b, observed=True)["net_usd"].mean()
    good = [iv for iv, v in m.items() if v > 0]
    if not good:
        return None
    lo = min(iv.left for iv in good); hi = max(iv.right for iv in good)
    return [None if abs(lo) >= 9e8 else round(float(lo), 3), None if abs(hi) >= 9e8 else round(float(hi), 3)]


def main():
    ty = pd.read_csv(TYPEONLY); fu = pd.read_csv(FULL)
    for d in (ty, fu):
        d["entry_time"] = pd.to_datetime(d["entry_time"]); d["exit_time"] = pd.to_datetime(d["exit_time"])
    ohlcv = pd.read_csv(OHLCV); ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])

    Xty = make_features(ty, ohlcv)
    # E8: ラベル = ○×(勝つか net>0) → 「伸びるか」（含み益ピークが価格%で閾値以上・size/価格非依存H6）
    #   mfe_usd/size_btc/entry_price = SHORT含み益ピークの価格下落率%。mfe_usd等はBANNED(特徴量除外)だがラベルには可。
    mfe_move_pct = ty["mfe_usd"] / ty["size_btc"] / ty["entry_price"] * 100.0
    y = (mfe_move_pct >= MFE_MOVE_THRESH_PCT).astype(int).values

    is_tr = (ty["entry_time"] < TRAIN_END) & (ty["exit_time"] < SC_START)   # embargo
    is_te = (ty["entry_time"] >= SC_START) & (ty["entry_time"] < SC_END)
    assert ty.loc[is_tr, "exit_time"].max() < SC_START, "H2: 学習に採点期間の未来が漏れている"
    _log(f"[split] 学習 {is_tr.sum()} (伸び率{y[is_tr.values].mean():.3f}) / テスト {is_te.sum()} (伸び率{y[is_te.values].mean():.3f})")

    Xtr, ytr = Xty[is_tr.values], y[is_tr.values]
    n = len(Xtr); cut = int(n * 0.85)                                       # 時系列 valid
    pos_w = (ytr[:cut] == 0).sum() / max(1, (ytr[:cut] == 1).sum())
    dtr = lgb.Dataset(Xtr.iloc[:cut], label=ytr[:cut])
    dva = lgb.Dataset(Xtr.iloc[cut:], label=ytr[cut:], reference=dtr)
    params = dict(objective="binary", metric="auc", learning_rate=0.03, num_leaves=15,
                  min_child_samples=100, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1,
                  lambda_l1=1.0, lambda_l2=1.0, scale_pos_weight=pos_w, seed=42, verbose=-1)
    model = lgb.train(params, dtr, num_boost_round=3000, valid_sets=[dva],
                      callbacks=[lgb.early_stopping(80, verbose=False)])
    _log(f"[train] best_iter={model.best_iteration} / scale_pos_weight={pos_w:.2f}")

    ptr = model.predict(Xtr, num_iteration=model.best_iteration)
    pte = model.predict(Xty[is_te.values], num_iteration=model.best_iteration)
    if len(np.unique(y[is_te.values])) > 1:
        _log(f"[score] テストAUC={roc_auc_score(y[is_te.values], pte):.4f}")

    # θ* = 学習側で「採用候補の net 合計」最大化（test 覗き見しない＝類型C回避）
    tr_df = ty[is_tr].reset_index(drop=True); tr_df["p"] = ptr
    best_th, best_net = 0.5, -1e18
    for th in np.round(np.arange(0.30, 0.81, 0.02), 2):
        s = tr_df.loc[tr_df["p"] >= th, "net_usd"].sum()
        if s > best_net:
            best_net, best_th = s, th
    _log(f"[θ*] 学習で net 最大 → θ*={best_th}（学習net ${best_net:.0f}）")

    # テスト適用 + 採点比較（score.py）
    te_df = ty[is_te].reset_index(drop=True); te_df["p"] = pte
    ai = te_df[te_df["p"] >= best_th].copy()
    fu_te = fu[(fu["entry_time"] >= SC_START) & (fu["entry_time"] < SC_END)].copy()

    out_ai = RAT / "trades_p23_E08_ai_test.csv"; ai.to_csv(out_ai, index=False)
    out_fu = RAT / "trades_p23_full_test.csv"; fu_te.to_csv(out_fu, index=False)

    r_ai = judge.score(ai); r_fu = judge.score(fu_te)
    _log("\n===== 採点（score.py・採点期間2025-04〜12・独立評価=同時保有cap未適用の技術検証）=====")
    _log(f"  V9手書き full : {r_fu['n_trades']:5d}件 / 月平均 ${r_fu['monthly_avg']:8.2f} / 合計 ${r_fu['total']:8.1f}")
    _log(f"  AI選択 θ*={best_th}: {r_ai['n_trades']:5d}件 / 月平均 ${r_ai['monthly_avg']:8.2f} / 合計 ${r_ai['total']:8.1f}")
    _log(f"  → AI {'勝ち' if r_ai['total'] > r_fu['total'] else '負け'}（合計差 ${r_ai['total']-r_fu['total']:+.1f}）")

    _log("\n[θ掃引・テスト独立net 参考]")
    for th in [0.4, 0.5, 0.6, 0.7, best_th]:
        k = te_df[te_df["p"] >= th]
        _log(f"  θ={th}: 採用 {len(k):4d}/{len(te_df)} / CSV net ${k['net_usd'].sum():8.1f} / avg ${k['net_usd'].mean() if len(k) else 0:6.2f}")

    imp = pd.Series(model.feature_importance("gain"), index=Xty.columns).sort_values(ascending=False)
    _log("\n[重要特徴 top12（どの指標を見ているか）]\n" + imp.head(12).to_string())

    # ===== AIが学習した「閾値・好む値」 =====
    # (1) 学習した分岐閾値: どの指標をどの値で切っているか（gain順）
    tdf = model.trees_to_dataframe()
    sp = tdf[tdf["split_feature"].notna()].groupby("split_feature").agg(
        分岐回数=("threshold", "size"), 代表閾値=("threshold", "median"),
        最小閾値=("threshold", "min"), 最大閾値=("threshold", "max"),
        gain合計=("split_gain", "sum")).sort_values("gain合計", ascending=False).round(3)
    _log("\n[AIが学習した分岐閾値 top10（指標をどの値で切るか・gain順）]\n" + sp.head(10).to_string())

    # (2) AIが高評価する値域: 自信あり(prob≥0.6) と 自信なし(prob<0.4) の指標中央値を対比
    tf = ty[is_te].reset_index(drop=True).copy(); tf["p"] = pte
    tf["atr_pct"] = tf["atr_14"] / tf["entry_price"] * 100
    tf["stoch_gap"] = tf["stoch_d_at_entry"] - tf["stoch_k_at_entry"]
    hi, lo = tf[tf["p"] >= 0.6], tf[tf["p"] < 0.4]
    inds = {"ADX": "adx_at_entry", "ATR%": "atr_pct", "RSI": "rsi_at_entry", "RSI傾き": "rsi_slope_at_entry",
            "stochギャップ": "stoch_gap", "bb傾き": "bb_mid_slope_at_entry", "BB幅": "bb_width_at_entry"}
    prof = pd.DataFrame({"自信あり_中央値": {k: hi[v].median() for k, v in inds.items()},
                         "自信なし_中央値": {k: lo[v].median() for k, v in inds.items()}}).round(2)
    _log(f"\n[AIが高評価する値域: 自信あり {len(hi)}件 ${hi['net_usd'].sum():.0f} vs 自信なし {len(lo)}件 ${lo['net_usd'].sum():.0f}]\n"
         + prof.to_string())

    # 保存: 全テスト候補(prob付き) → report.py で G/H を全域分析できる
    tf.to_csv(RAT / "trades_p23_E08_all_scored.csv", index=False)
    _log("\n[out] 全テスト候補(prob付き) → trades_p23_E08_all_scored.csv（report.py の H/G を全域で見られる）")

    # ===== 使用した値一覧（cat_params_v9.json 風・AIが学習/使用した値） =====
    learned = {
        "_source": "train_p23_entry_E8.py E8 学習モデル（P23・最初に入る→『伸びるか』二値・mfe価格%>=0.8）",
        "_period": "学習 <2025-04 / テスト 2025-04〜2025-12",
        "_label": f"伸びる = mfe_usd/size/entry*100 >= {MFE_MOVE_THRESH_PCT}%（E6の net>0 から変更・fat-tail切らない）",
        "_note": "AIは決定木の集まりで単一閾値ではない。LEARNED_SPLIT_*=木の分岐閾値の中央値（AIがよく切る値）。EDGE_*=実netが平均プラスの帯の範囲[下端,上端]（テスト実測・データ由来、null=開放端）。比較用に V9手書き値を _V9 に併記。",
        "ML_THETA_ADOPT": round(float(best_th), 3),
        "ML_AUC_TEST": round(float(roc_auc_score(y[is_te.values], pte)), 3) if len(np.unique(y[is_te.values])) > 1 else None,
        "ML_NUM_LEAVES": 15, "ML_MIN_CHILD_SAMPLES": 100, "ML_LAMBDA_L1": 1.0, "ML_LAMBDA_L2": 1.0,
        "ML_SCALE_POS_WEIGHT": round(float(pos_w), 2), "ML_BEST_ITER": int(model.best_iteration),
    }
    for k, v in sp["代表閾値"].head(8).to_dict().items():
        learned[f"LEARNED_SPLIT_{k}"] = round(float(v), 4)
    learned["EDGE_ADX"]       = _edge(tf, "adx_at_entry",          [0, 20, 25, 30, 35, 40, 50, 9e9])
    learned["EDGE_ATR_PCT"]   = _edge(tf, "atr_pct",               [0, 0.2, 0.3, 0.4, 0.5, 0.7, 9e9])
    learned["EDGE_RSI"]       = _edge(tf, "rsi_at_entry",          [0, 40, 45, 50, 55, 60, 70, 9e9])
    learned["EDGE_BB_SLOPE"]  = _edge(tf, "bb_mid_slope_at_entry", [-9e9, -30, -20, -10, 0, 9e9])
    learned["EDGE_STOCH_GAP"] = _edge(tf, "stoch_gap",             [0, 0.3, 1, 3, 6, 9e9])
    learned["_V9手書き"] = {"P23_ADX_MIN": 30, "P23_ADX_MAX": 50, "P23_ATR14_MIN": 150,
                          "P23_BB_MID_SLOPE_MAX": -10, "P23_TP_PCT": 0.012, "P23_TIME_EXIT_MIN": 480}
    pj = RAT / "p23_learned_params_E08.json"
    json.dump(learned, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    _log(f"\n[out] 使用した値一覧（cat_params風）→ {pj}\n" + json.dumps(learned, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
