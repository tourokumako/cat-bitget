#!/usr/bin/env python3
"""train_p23_entry_E9.py — P23 Entry/Exit セット学習（出口の「値」を連続最適化）

設計: .claude/ratchet/e9_design.md（まこさん承認 2026-06-08）。strat_v9ml_design §10.16 要約。

★ 核心（まこさんの定義）:
  入口の条件（gap/ADX/ATR%/bb傾き/stoch/MTF の切れ目）と、出口の条件（利確幅/損切り/保有時間の"値"）を
  一緒に動かして、往復net が最大になる組合せを木に学習させる。
  - 出口は **値を連続学習**（プリセットから選ぶのではない）: 各型バーに出口値を連続範囲からランダム
    サンプリングし、(入口指標 ⊕ 出口値) → 往復net を回帰木で学習。推論で各入口に最適な出口値を選ぶ。
  - 入口条件 = 予測往復net>0（θ足切りでない）。
  - 採点 = 自前連続ループ(gen._step import・建玉ごとに最適出口値)→ cap0.12 → score.py → 地面$925.73。

禁止: θ足切り / 出口先固定 / 出口プリセット選択 / 勝率・○×・伸びるかラベル。予測対象は往復net金額。
import のみ・改造禁止: replay_csv / cat_v9_decider / cat_params_v9 / score / eval_engine / gen / E8 / E8b。
"""
from __future__ import annotations
import sys
import time
import pathlib
import json
import numpy as np
import pandas as pd
import ta
import lightgbm as lgb
from sklearn.metrics import r2_score, mean_absolute_error

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                       # noqa: E402  V9 リプレイ（import のみ）
import gen_p23_candidates as gen              # noqa: E402  連続モード/型/sim（import のみ・_step 流用）
import score as judge                         # noqa: E402  審判（import のみ・改造しない）
import train_p23_entry_E8 as e8               # noqa: E402  build_mtf 流用（MTF・方向系のみ）
import train_p23_entry_E8b as e8b             # noqa: E402  build_multiperiod/with_exit 流用
import ratchet_guards as rg                   # noqa: E402  番人（既知答え済）

RAT = ROOT / "results" / "priority_rebuild" / "ratchet"
OHLCV = ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"
GROUND = RAT / "trades_p23_ground_capped.csv"   # 地面（V9手書きP23・$925.73）

# ---- 期間分割（H8・# src: まこさん確定値）----
TRAIN_ENTRY_END = pd.Timestamp("2024-12-31")    # src: H8 学習末
EMBARGO_END     = pd.Timestamp("2025-04-01")    # src: H8 embargo 2025Q1
SC_START        = pd.Timestamp("2025-04-01")    # src: H8 採点開始
SC_END          = pd.Timestamp("2026-01-01")    # src: H8 封印2026Q1不参照
assert TRAIN_ENTRY_END <= pd.Timestamp("2024-12-31"), "H8: 学習末が採点へ侵入"

CAP = 0.12   # src: CLAUDE §0-2 予算合計上限

# ---- 出口値の連続範囲（★実データ実測が根拠・e9_design §5）----
TP_RANGE    = (0.003, 0.025)   # src: e9_design §5 利確0.3%(往復手数料0.028%の約10倍)〜2.5%(含み益max5%・p90 1.5%)
SL_RANGE    = (0.005, 0.050)   # src: e9_design §5 損切り0.5%〜5.0%(V9 SL設定・含み損max7.4%)
TIME_RANGE  = (15, 480)        # src: e9_design §5 保有15分(急落即TP実例)〜480分(V9時間切れ・実max470)

# ---- 入口指標の期間（複数・木が有効期間を選ぶ・e9_design §4.3c）----
STOCH_PERIODS = [5, 9, 14]   # src: e9_design §4.3c
ADX_PERIODS   = [7, 14, 21]  # src: e9_design §4.3c
BB_PERIODS    = [10, 20, 40] # src: e9_design §4.3c
RSI_PERIODS   = [7, 14, 21]  # src: e9_design §4.3c
ATR_PERIODS   = [7, 14, 28]  # src: e9_design §4.3e ATR%(入れて監視)

# ---- 学習規模（★スモークで1simの実時間を計測してから本番値をまこさんと決める・e9_design §10）----
N_TRAIN_BARS = 6000   # src: 仮置き・スモーク計算量実測後にまこさん報告して確定（勝手に削らない）
K_EXIT       = 16     # src: 仮置き・各型バーに連続サンプリングする出口値の組数（同上）
N_SMOKE_BARS = 200    # src: スモーク用小サンプル
# 推論の出口値グリッド解像度（predict は軽いので密に・e9_design §8）
N_TP, N_SL, N_TM = 12, 8, 12   # src: 仮置き・連続範囲を離散化する点数

# 結果列 = leak（特徴量に絶対入れない・H2）
BANNED = {"net_usd", "gross_usd", "fee_usd", "mfe_usd", "mae_usd", "exit_price", "exit_reason",
          "hold_min", "add_count", "size_btc", "entry_price", "exit_time", "entry_time", "side",
          "priority", "regime", "bar_i", "bar_time"}


def _log(m):
    print(m, flush=True)


# ======================================================================
# 入口特徴量（e9_design §4・方向系 + ATR%/bb_width%(入れて監視) + MTF + 時間）
# ======================================================================
def build_entry_features(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """5m 入口指標。方向系(build_multiperiod 流用) + ATR%/bb_width%(まこさん 2026-06-08 入れて監視)。
    index=timestamp。全て t 時点の確定値（shift 正方向・center 不使用・leak-safe）。"""
    mp = e8b.build_multiperiod(ohlcv)            # 方向系: stoch/adx/bb_slope_pct/bb_pctb/rsi/ret_5（ボラ系除外済）
    o = ohlcv.set_index("timestamp").sort_index()
    c, h, l = o["close"], o["high"], o["low"]
    # ★ATR%（入れて監視・e9_design §4.3e）
    for p in ATR_PERIODS:
        atr = ta.volatility.AverageTrueRange(h, l, c, window=p).average_true_range()
        mp[f"atr_pct_{p}"] = (atr / c * 100.0).reindex(mp.index)
    # ★bb_width%（バンド幅＝エネルギー・入れて監視・e9_design §4.3g）
    for p in BB_PERIODS:
        bb = ta.volatility.BollingerBands(c, window=p, window_dev=2)
        mid = bb.bollinger_mavg()
        mp[f"bb_width_pct_{p}"] = ((bb.bollinger_hband() - bb.bollinger_lband()) / mid.replace(0, np.nan) * 100.0).reindex(mp.index)
    return mp


def make_features_e9(bar_times: pd.Series, entry_feats: pd.DataFrame, ohlcv: pd.DataFrame) -> pd.DataFrame:
    """型バー時刻に対し 入口指標(方向+ボラ) + MTF(build_mtf・方向系) + 時間 を組む。"""
    bt = pd.to_datetime(bar_times.values)
    X_mp = entry_feats.reindex(bt).reset_index(drop=True)
    mtf = e8.build_mtf(ohlcv, pd.Series(bt))     # MTF 15m/30m/1h/4h（方向系のみ・leak-safe）
    bt_s = pd.Series(bt)
    tcol = pd.DataFrame({"entry_hour": bt_s.dt.hour.values, "entry_weekday": bt_s.dt.weekday.values})
    X = pd.concat([X_mp, mtf.reset_index(drop=True), tcol], axis=1)
    leaked = BANNED & set(X.columns)
    assert not leaked, f"H2 leak: 結果列が特徴量に混入 {leaked}"
    return X


# ======================================================================
# 出口値の連続サンプリング（★プリセットでない・e9_design §5）
# ======================================================================
def sample_exit_values(rng: np.random.RandomState, k: int):
    """利確/損切り/保有時間 を連続範囲から一様ランダムに k 組。保有時間は5分刻み（5m足）。"""
    tp = rng.uniform(TP_RANGE[0], TP_RANGE[1], k)
    sl = rng.uniform(SL_RANGE[0], SL_RANGE[1], k)
    tm = (np.round(rng.uniform(TIME_RANGE[0], TIME_RANGE[1], k) / 5.0) * 5).astype(int)
    tm = np.clip(tm, 5, TIME_RANGE[1])
    return list(zip(tp.tolist(), sl.tolist(), tm.tolist()))


def exit_override(tp: float, sl: float, tm: int) -> dict:
    """出口値 → V9 params の上書き（利確/損切り/時間切れ）。gen は不変・params コピーに当てる。"""
    return {"P23_TP_PCT": float(tp), "SHORT_SL_PCT": float(sl), "P23_TIME_EXIT_MIN": int(tm)}


# ======================================================================
# 学習データ生成: 各型バー i × 連続出口値 K 組 → 往復 net/gross（e9_design §6）
# ======================================================================
def gen_dataset(df, bar_ms, params, sample_bars, k_exit, rng):
    rows = []
    n_sim = 0
    t0 = time.time()
    for i in sample_bars:
        for (tp, sl, tm) in sample_exit_values(rng, k_exit):
            n_sim += 1
            tr = gen.simulate_independent(df, bar_ms, i, e8b.with_exit(params, exit_override(tp, sl, tm)))
            if tr is None:
                continue
            rows.append({"bar_i": int(i),
                         "bar_time": pd.to_datetime(df.at[i, "timestamp_ms"], unit="ms"),
                         "entry_time": pd.to_datetime(tr["entry_time"]),
                         "exit_time": pd.to_datetime(tr["exit_time"]),
                         "x_tp_pct": float(tp), "x_sl_pct": float(sl), "x_time_exit": float(tm),
                         "net_usd": float(tr["net_usd"]), "gross_usd": float(tr["gross_usd"])})
    elapsed = time.time() - t0
    return pd.DataFrame(rows), n_sim, elapsed


def train_lgb_reg(X, y, lparams, valid_frac=0.15):
    n = len(X); cut = max(1, int(n * (1.0 - valid_frac)))
    dtr = lgb.Dataset(X.iloc[:cut], label=y[:cut])
    dva = lgb.Dataset(X.iloc[cut:], label=y[cut:], reference=dtr)
    return lgb.train(lparams, dtr, num_boost_round=3000, valid_sets=[dva],
                     callbacks=[lgb.early_stopping(80, verbose=False)])


# ======================================================================
# 採点: 自前連続ループ（gen._step import・建玉ごとに選定出口値・e9_design §9・gen不変）
# ======================================================================
def run_continuous_setexit(df, bar_ms, params, enter_set: set, exit_ov_by_bar: dict) -> list:
    state = {"pos": None, "pending": None, "trades": []}
    active_ov = {}
    fn_in = lambda k: (k in enter_set)
    for i in range(rc.CANDLE_WARMUP, len(df)):
        if state["pos"] is None and state["pending"] is None and (i in enter_set):
            active_ov = exit_ov_by_bar.get(i, {})
        gen._step(state, df, bar_ms, i, e8b.with_exit(params, active_ov), fn_in)
    if state["pos"] is not None:
        rc._record_trade(state["trades"], state["pos"], exit_price=float(df.iloc[-1]["close"]),
                         exit_reason="FORCE_CLOSE_EOD", exit_ts_ms=int(df.iloc[-1]["timestamp_ms"]), params=params)
    return state["trades"]


def main():
    _log("[E9] P23 Entry/Exit セット学習 — 出口の値を連続学習 / (入口⊕出口値)→往復net / 足切りなし")
    SMOKE = "--smoke" in sys.argv

    # ① 静的番人（実行前）
    _src = pathlib.Path(__file__).read_text()
    rg.assert_no_future_ref(_src)
    rg.assert_period_split(TRAIN_ENTRY_END, SC_START)
    rg.assert_constants_sourced(_src)
    if SMOKE:
        _log("[SMOKE] 小サンプル＋1simの実時間を計測（本採点/Optuna/グリッド推論は省略）。")

    params = rc._load_params()
    p23 = dict(params)
    for k in list(p23):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p23[k] = (k == "ENABLE_P23_SHORT")
    df, _ = rc.preload(str(gen.OHLCV_CSV), p23)
    bar_ms = int(df.at[1, "timestamp_ms"] - df.at[0, "timestamp_ms"])
    _log(f"[load] bars={len(df)} bar_ms={bar_ms}")

    ohlcv = pd.read_csv(OHLCV)
    ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])
    entry_feats = build_entry_features(ohlcv)    # 方向系 + ATR%/bb_width%(入れて監視)
    _log(f"[特徴量] 入口指標 {entry_feats.shape[1]} 列（方向系 + atr_pct{ATR_PERIODS} + bb_width_pct{BB_PERIODS}）")

    type_bars = [i for i in range(rc.CANDLE_WARMUP, len(df)) if gen._p23_type_fires(df, i)]
    type_set = set(type_bars)
    ref_fire = {i for i in range(rc.CANDLE_WARMUP, len(df)) if gen._p23_type_fires(df, i)}
    assert type_set == ref_fire, "自己検査NG(1): 型ゲート不一致"
    _log(f"[self-check 1] ✅ 型ゲート == gen._p23_type_fires（{len(type_set)} バー）")

    def bar_time(i):
        return pd.to_datetime(df.at[i, "timestamp_ms"], unit="ms")

    # 学習期間の型バーから層化サンプリング
    tr_bars = [i for i in type_bars if bar_time(i) < TRAIN_ENTRY_END]
    rng = np.random.RandomState(42)
    n_pick = N_SMOKE_BARS if SMOKE else N_TRAIN_BARS
    if len(tr_bars) > n_pick:
        months = np.array([bar_time(i).to_period("M").ordinal for i in tr_bars])
        picked = []
        for m in np.unique(months):
            idxs = [tr_bars[j] for j in range(len(tr_bars)) if months[j] == m]
            kk = max(1, int(round(n_pick * len(idxs) / len(tr_bars))))
            picked += rng.choice(idxs, min(kk, len(idxs)), replace=False).tolist()
        sample_bars = sorted(picked)
    else:
        sample_bars = tr_bars
    _log(f"[sample] 学習期間型バー {len(tr_bars)} → サンプル {len(sample_bars)}（{'SMOKE' if SMOKE else '本番'}）")

    # 自己検査(2): 出口V9既定固定の自前連続 == gen.run_continuous（本番のみ全期間／スモークは小区間）
    if not SMOKE:
        a = run_continuous_setexit(df, bar_ms, params, type_set, {i: {} for i in type_bars})
        b = gen.run_continuous(df, bar_ms, params, lambda k: (k in type_set))
        rg.assert_selfcheck_match(len(a), sum(float(t["net_usd"]) for t in a),
                                  len(b), sum(float(t["net_usd"]) for t in b))
        _log(f"[self-check 2] ✅ 自前連続(V9既定全型) == gen.run_continuous（{len(a)}件 net一致）")
    else:
        df_s = df.iloc[:30000].reset_index(drop=True)
        ts_s = {i for i in range(rc.CANDLE_WARMUP, len(df_s)) if gen._p23_type_fires(df_s, i)}
        a = run_continuous_setexit(df_s, bar_ms, params, ts_s, {i: {} for i in ts_s})
        b = gen.run_continuous(df_s, bar_ms, params, lambda k: (k in ts_s))
        rg.assert_selfcheck_match(len(a), sum(float(t["net_usd"]) for t in a),
                                  len(b), sum(float(t["net_usd"]) for t in b))
        _log(f"[SMOKE self-check 2] ✅ 小区間(先頭30000bar) 自前連続==gen.run_continuous（{len(a)}件一致・移植OK）")

    # ★規模確認ゲート（本番モード・--confirm-scale 無しは 小サンプルで実測→見積もり→停止・e9_design §10）
    #   設計書通り「スモークで時間を測ってまこさんが本番規模を決めてから本番」を物理化。勝手に本番を回さない。
    if not SMOKE and "--confirm-scale" not in sys.argv:
        _pb, _np, _el = gen_dataset(df, bar_ms, params, sample_bars[:100], 4, rng)
        _ms = _el / max(1, _np) * 1000
        _full = N_TRAIN_BARS * K_EXIT
        _log(f"\n[規模確認・停止] 本番 {N_TRAIN_BARS}本 × {K_EXIT}組 = {_full} sim × 実測 {_ms:.2f}ms/sim "
             f"≈ データ生成 {_full*_ms/1000/60:.1f}分 ＋ 連続採点 ＋ グリッド推論 {N_TP*N_SL*N_TM}点。")
        _log("  この規模でよければ `--confirm-scale` を付けて再実行。規模を変えるなら N_TRAIN_BARS / K_EXIT / N_TP等 を編集。")
        _log("  ★まこさん確認待ちで停止（勝手に本番を回さない・e9_design §10）。")
        return

    # ---- データ生成（各型バー × 連続出口値 K 組）----
    k_exit = 4 if SMOKE else K_EXIT
    _log(f"\n[データ生成] サンプル {len(sample_bars)} × 出口値 {k_exit}組 = {len(sample_bars)*k_exit} sim")
    dataset, n_sim, elapsed = gen_dataset(df, bar_ms, params, sample_bars, k_exit, rng)
    _log(f"[計算量・実測] {n_sim} sim を {elapsed:.1f}秒（{elapsed/max(1,n_sim)*1000:.2f} ms/sim）")
    _log(f"[データ生成] 約定 {len(dataset)} 行 / net分布 min={dataset['net_usd'].min():.1f} median={dataset['net_usd'].median():.1f} max={dataset['net_usd'].max():.1f}")

    # ③ 番人メタ確認（cat_requirements §8.4-2.9）: fee=gross-net が過小=ダミー/未控除なら停止
    _gross = float(dataset["gross_usd"].sum()); _net = float(dataset["net_usd"].sum())
    assert (_gross - _net) > len(dataset) * 0.05, \
        f"検査メタNG: fee合計 {_gross-_net:.2f} が過小＝gross/netダミー/未控除疑い（{len(dataset)}件）"
    rg.assert_cost_applied(_gross, _net)

    # ---- 本番計算量の見積もり（実測ms/sim から・まこさんに報告して規模確定）----
    ms_per_sim = elapsed / max(1, n_sim) * 1000
    _log(f"[計算量・本番見積もり] 本番 {N_TRAIN_BARS}本 × {K_EXIT}組 = {N_TRAIN_BARS*K_EXIT} sim "
         f"× {ms_per_sim:.2f}ms ≈ {N_TRAIN_BARS*K_EXIT*ms_per_sim/1000/60:.1f}分（実測ms/simベース）")

    if SMOKE:
        # スモークは学習だけ軽く回してボラ可視化・健全性を確認（推論/採点は省略）
        uniq = dataset.drop_duplicates("bar_i")[["bar_i", "bar_time"]].reset_index(drop=True)
        Xin = make_features_e9(uniq["bar_time"], entry_feats, ohlcv)
        Xin["bar_i"] = uniq["bar_i"].values
        in_cols = [c for c in Xin.columns if c != "bar_i"]
        merged = dataset.merge(Xin, on="bar_i", how="left")
        feat_cols = in_cols + ["x_tp_pct", "x_sl_pct", "x_time_exit"]
        is_tr = (merged["entry_time"] < TRAIN_ENTRY_END) & (merged["exit_time"] < EMBARGO_END)
        Xtr = merged.loc[is_tr, feat_cols].reset_index(drop=True)
        ytr = merged.loc[is_tr, "net_usd"].values.astype(float)
        lp = dict(objective="regression_l1", metric="l1", learning_rate=0.05, num_leaves=15,
                  min_child_samples=50, feature_fraction=0.8, seed=42, verbose=-1)
        model = train_lgb_reg(Xtr, ytr, lp)
        pred = model.predict(Xtr, num_iteration=model.best_iteration)
        imp = dict(zip(model.feature_name(), model.feature_importance(importance_type="gain")))
        vr = rg.report_vol_importance(imp)
        _log(f"[SMOKE 学習] R²={r2_score(ytr, pred):.3f} MAE={mean_absolute_error(ytr, pred):.2f} / 特徴量 {len(feat_cols)}列")
        _log(f"[SMOKE ②ボラ可視化・H15] vol_share={vr['vol_share']} / top5={vr['top']} / top内ボラ={vr['top_vol']}")
        _log(f"[SMOKE] 完了: クラッシュ無 / 自己検査1,2 ✅ / 計算量実測={ms_per_sim:.2f}ms/sim / 本番見積もり上記。"
             f" 本番規模(N_TRAIN_BARS/K_EXIT/グリッド)をまこさんと確定してから本番。")
        return

    # ======================== 本番 ========================
    uniq = dataset.drop_duplicates("bar_i")[["bar_i", "bar_time"]].reset_index(drop=True)
    Xin = make_features_e9(uniq["bar_time"], entry_feats, ohlcv)
    Xin["bar_i"] = uniq["bar_i"].values
    in_cols = [c for c in Xin.columns if c != "bar_i"]
    merged = dataset.merge(Xin, on="bar_i", how="left")
    feat_cols = in_cols + ["x_tp_pct", "x_sl_pct", "x_time_exit"]
    is_tr = (merged["entry_time"] < TRAIN_ENTRY_END) & (merged["exit_time"] < EMBARGO_END)
    Xtr = merged.loc[is_tr, feat_cols].reset_index(drop=True)
    ytr = merged.loc[is_tr, "net_usd"].values.astype(float)
    assert len(Xtr) > 0, "H8: 学習データが空"
    _log(f"[特徴量] {len(feat_cols)}列（入口{len(in_cols)} + 出口値3）/ 学習行 {len(Xtr)}")

    lp = dict(objective="regression_l1", metric="l1", learning_rate=0.03, num_leaves=15,
              min_child_samples=100, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1,
              lambda_l1=1.0, lambda_l2=1.0, seed=42, verbose=-1)
    model = train_lgb_reg(Xtr, ytr, lp)
    pred_tr = model.predict(Xtr, num_iteration=model.best_iteration)
    _log(f"[train] best_iter={model.best_iteration} / R²={r2_score(ytr, pred_tr):.3f} MAE={mean_absolute_error(ytr, pred_tr):.2f}")

    imp = dict(zip(model.feature_name(), model.feature_importance(importance_type="gain")))
    vr = rg.report_vol_importance(imp)
    _log(f"[②ボラ可視化・H15] vol_share={vr['vol_share']} / top5={vr['top']} / top内ボラ={vr['top_vol']}")

    # ---- 推論: 各入口で出口値グリッド → 予測net最大の出口値（e9_design §8）----
    Xin_all = make_features_e9(pd.Series([bar_time(i) for i in type_bars]), entry_feats, ohlcv)
    assert in_cols == list(Xin_all.columns), f"列不一致(学習vs推論): {set(in_cols)^set(Xin_all.columns)}"
    tp_grid = np.linspace(TP_RANGE[0], TP_RANGE[1], N_TP)
    sl_grid = np.linspace(SL_RANGE[0], SL_RANGE[1], N_SL)
    tm_grid = (np.round(np.linspace(TIME_RANGE[0], TIME_RANGE[1], N_TM) / 5) * 5).astype(int)
    G = [(float(tp), float(sl), int(tm)) for tp in tp_grid for sl in sl_grid for tm in tm_grid]
    _log(f"\n[推論] 出口値グリッド {len(G)}点（TP{N_TP}×SL{N_SL}×時間{N_TM}）を全型バー {len(type_bars)} に predict")
    best_net = np.full(len(type_bars), -1e18)
    best_g = np.zeros(len(type_bars), dtype=int)
    base = Xin_all[in_cols].copy()
    for gi, (tp, sl, tm) in enumerate(G):
        Xq = base.copy()
        Xq["x_tp_pct"] = tp; Xq["x_sl_pct"] = sl; Xq["x_time_exit"] = float(tm)
        p = model.predict(Xq[feat_cols], num_iteration=model.best_iteration)
        msk = p > best_net
        best_net[msk] = p[msk]; best_g[msk] = gi
    enter_set = {type_bars[j] for j in range(len(type_bars)) if best_net[j] > 0.0}
    exit_ov_by_bar = {type_bars[j]: exit_override(*G[best_g[j]]) for j in range(len(type_bars))}
    _log(f"[推論] 入口=予測net>0 で入る型バー {len(enter_set)} / 全 {len(type_bars)}（足切りθなし）")

    # ---- 採点: 自前連続（建玉別 出口値）→ score.py（cap0.12 ゲート）----
    ai_trades = run_continuous_setexit(df, bar_ms, params, enter_set, exit_ov_by_bar)
    if len(ai_trades) == 0:
        _log("[採点] 入る玉 0 件 → net $0（地面 $925.73 に負け）。正常終了。")
        return
    ai_df = pd.DataFrame(ai_trades)
    for col in ("entry_time", "exit_time"):
        ai_df[col] = pd.to_datetime(ai_df[col])
    out_ai = RAT / "trades_p23_E09_ai.csv"
    ai_df.to_csv(out_ai, index=False)

    sc = ai_df[(ai_df["entry_time"] >= SC_START) & (ai_df["entry_time"] < SC_END)].reset_index(drop=True)
    r_ai = judge.score(sc) if len(sc) else {"total": 0.0, "monthly_avg": 0.0, "n_trades": 0, "anomaly": []}
    _log("\n===== 採点（score.py・cap0.12 ゲート・2025-04〜12・連続モード）=====")
    _log(f"  AI-E9: {r_ai['n_trades']:5d}件 / 月平均 ${r_ai['monthly_avg']:8.2f} / 合計 ${r_ai['total']:8.1f}")
    if r_ai.get("anomaly"):
        _log("  ⚠️ 異常値・要調査(H12): " + " / ".join(r_ai["anomaly"]))
    ground_total = None
    if GROUND.exists():
        g = pd.read_csv(GROUND); g["entry_time"] = pd.to_datetime(g["entry_time"]); g["exit_time"] = pd.to_datetime(g["exit_time"])
        g_sc = g[(g["entry_time"] >= SC_START) & (g["entry_time"] < SC_END)].reset_index(drop=True)
        r_g = judge.score(g_sc); ground_total = r_g["total"]
        _log(f"  地面: {r_g['n_trades']:5d}件 / 月平均 ${r_g['monthly_avg']:8.2f} / 合計 ${r_g['total']:8.1f}")
        _log(f"  → AI {'勝ち' if r_ai['total'] > r_g['total'] else '負け'}（差 ${r_ai['total']-r_g['total']:+.1f} / 地面 $925.73）")
    rg.assert_output_exists(str(out_ai))

    # ---- 結果の出し方（e9_design §8.1）: Entry=指標×閾値(V9対比) / 出口=選んだ保有時間・TP・SL ----
    _log("\n[結果A・Entry] 木が学習した『指標 × 閾値』top12（V9手書き値と対比）")
    tdf = model.trees_to_dataframe()
    sp = tdf[tdf["split_feature"].notna()].groupby("split_feature").agg(
        分岐回数=("threshold", "size"), 代表閾値=("threshold", "median"),
        gain合計=("split_gain", "sum")).sort_values("gain合計", ascending=False).round(4)
    _log(sp.head(12).to_string())
    _log("  V9手書き値（対比）: ADX 30-50 / bb_slope_pct ~-10相当 / stoch_gap 0.3 / TP 1.2% / 時間 480分")

    chosen = pd.DataFrame([G[best_g[j]] for j in range(len(type_bars)) if best_net[j] > 0.0],
                          columns=["tp", "sl", "tm"])
    _log("\n[結果B・出口] AIが選んだ出口値（入る玉)の分布")
    if len(chosen):
        _log(f"  利確TP%: median {chosen['tp'].median()*100:.2f} / 範囲 {chosen['tp'].min()*100:.2f}〜{chosen['tp'].max()*100:.2f}")
        _log(f"  損切りSL%: median {chosen['sl'].median()*100:.2f} / 範囲 {chosen['sl'].min()*100:.2f}〜{chosen['sl'].max()*100:.2f}")
        _log(f"  保有時間分: median {chosen['tm'].median():.0f} / 範囲 {chosen['tm'].min():.0f}〜{chosen['tm'].max():.0f}")

    # 入口帯別（bb傾き帯）の選んだ出口値（e9_design §8.1）
    enter_idx = [j for j in range(len(type_bars)) if best_net[j] > 0.0]
    if enter_idx and "bb_slope_pct_20" in Xin_all.columns:
        bbs = Xin_all["bb_slope_pct_20"].values
        tmp = pd.DataFrame({"bb_slope": [bbs[j] for j in enter_idx],
                            "tp": [G[best_g[j]][0]*100 for j in enter_idx],
                            "sl": [G[best_g[j]][1]*100 for j in enter_idx],
                            "tm": [G[best_g[j]][2] for j in enter_idx]})
        tmp["bb帯"] = pd.cut(tmp["bb_slope"], [-1e9, -30, -10, 0, 1e9], labels=["〜-30", "-30〜-10", "-10〜0", "0〜"])
        _log("\n[結果C・入口帯別の出口値] bb傾き帯ごとに AIが選んだ TP%/SL%/保有分(中央値)")
        _log(tmp.groupby("bb帯", observed=True)[["tp", "sl", "tm"]].median().round(2).to_string())

    # ---- 学習値 JSON ----
    learned = {
        "_source": "train_p23_entry_E9.py（出口の値を連続学習・足切りなし・建玉別出口連続採点）",
        "_period": "学習 entry<2024-12-31 かつ exit<2025-04-01 / 採点 2025-04-01〜2026-01-01 / 封印2026Q1不参照",
        "ML_OBJECTIVE": "regression_l1（往復net金額）",
        "ML_EXIT_RANGES": {"tp_pct": TP_RANGE, "sl_pct": SL_RANGE, "time_min": TIME_RANGE},
        "ML_N_TRAIN_BARS": N_TRAIN_BARS, "ML_K_EXIT": K_EXIT, "ML_GRID": [N_TP, N_SL, N_TM],
        "ML_MS_PER_SIM": round(ms_per_sim, 3),
        "ML_BEST_ITER": int(model.best_iteration), "ML_TRAIN_R2": round(float(r2_score(ytr, pred_tr)), 4),
        "ML_VOL_SHARE": vr["vol_share"], "ML_N_ENTER": len(enter_set), "ML_N_TYPE_BARS": len(type_bars),
        "AI_SCORE_TOTAL_USD": round(float(r_ai["total"]), 2),
        "AI_SCORE_MONTHLY_AVG_USD": round(float(r_ai["monthly_avg"]), 2),
        "GROUND_SCORE_TOTAL_USD": round(float(ground_total), 2) if ground_total is not None else None,
        "_chosen_exit_median": {"tp_pct": round(float(chosen["tp"].median()), 4) if len(chosen) else None,
                                "sl_pct": round(float(chosen["sl"].median()), 4) if len(chosen) else None,
                                "time_min": float(chosen["tm"].median()) if len(chosen) else None},
        "_entry_split_top": {k: round(float(v), 4) for k, v in sp["代表閾値"].head(10).to_dict().items()},
        "_top_features_gain": {k: round(float(v), 1) for k, v in pd.Series(imp).sort_values(ascending=False).head(12).to_dict().items()},
    }
    pj = RAT / "p23_learned_params_E09.json"
    json.dump(learned, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    ai_df.assign(p=None).to_csv(RAT / "trades_p23_E09_all.csv", index=False)
    _log(f"\n[out] AI 連続モード trade → {out_ai}")
    _log(f"[out] 学習値 → {pj}")
    _log(f"[次] python3 scripts/priority_rebuild/report.py {out_ai} --start 2025-04-01 --end 2025-12-31 --vs {GROUND}")


if __name__ == "__main__":
    main()
