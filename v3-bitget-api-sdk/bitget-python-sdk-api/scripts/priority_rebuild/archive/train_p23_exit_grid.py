#!/usr/bin/env python3
"""train_p23_exit_grid.py — P23 Exit TP/SL 場面別学習（strat_v9ml_design §10.17.1 章7・2026-06-10 改訂）

設計（§10.17.1 章7・まこさん承認「一旦 CC 想定で実装してテスト」2026-06-10）:
  - 木が各建玉に最適な TP/SL の組を場面別に選ぶ（多クラス分類・net 基準）。
    net 金額は当てない（どの組が net 最大かを分類＝E9 連続回帰の R² 破綻回避）。
    MFE% ラベルにしない（E10 で 伸びる確率 prob と実 net が −0.08 の無相関だったため net 基準に）。
  - 入口 = θ足切りなし（全型バー・件数を減らさない・方針1）。
  - 学習対象 = TP/SL の組（離散グリッド）。制約: TP 下限（手数料超・薄利禁止）・SL 常識範囲。R:R 自由。
  - TimeExit = 固定480分（学習しない・add 育ち維持・E9 の add 破壊回避）。
  - 教師 = 各型バー×各組を gen.simulate_independent 前向き sim（leak-safe）→ net 最大の組。
  - 採点 = 連続モードで各建玉に予測組の TP/SL 適用・cap0.12・score.py vs 地面 $925.73（E0.2）。
  - 場面別性の監視 = 予測組の分布（1組に張り付けば場面別でない＝ML価値なし）/ feature importance / vol_share。

★ 不正防止（cat_requirements §8.4-2.9）: 判定は score.py の数字のみ／番人(ratchet_guards)はメタ確認／
  本スクリプトは net 計算に触れない（gen/replay_csv/score/eval_engine は import のみ・改造しない）。
"""
from __future__ import annotations
import sys
import pathlib
import json
import numpy as np
import pandas as pd
import lightgbm as lgb

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                       # noqa: E402  V9 リプレイ（import のみ）
import gen_p23_candidates as gen              # noqa: E402  連続モード/型/sim（import のみ・改造しない）
import score as judge                         # noqa: E402  審判（import のみ・改造禁止）
import ratchet_guards as rg                   # noqa: E402  番人（leak/期間/自己検査・既知答え済）
import train_p23_entry_E8b as e8b             # noqa: E402  特徴量/with_exit/label_type_bars/定数 を流用

RAT = e8b.RAT
SC_START, SC_END = e8b.SC_START, e8b.SC_END
TRAIN_ENTRY_END, EMBARGO_END = e8b.TRAIN_ENTRY_END, e8b.EMBARGO_END
GROUND = e8b.GROUND                            # trades_p23_ground_capped.csv = $925.73（連続モード・部分決済なし・cap遵守）

# Exit グリッド（§10.17.1 章7・CC 想定・まこさん 2026-06-10「一旦 CC 想定で」）。
#   TP 下限 = 手数料超（最小 0.6%）。SL 常識範囲 0.5〜2%。TimeExit 固定 480分（add 育ち維持）。
#   R:R は事前固定せず木が組を選ぶ（場面別）。具体値は score.py の net で判定し回して直す。
TP_GRID = [0.006, 0.010, 0.015]                # 0.6 / 1.0 / 1.5%
SL_GRID = [0.005, 0.010, 0.020]                # 0.5 / 1.0 / 2.0%
TIME_FIXED = 480                               # TimeExit 固定（分・学習しない・安全弁）
EXIT_SETS = [(tp, sl) for tp in TP_GRID for sl in SL_GRID]   # 9 組（粗め・計算量は SMOKE で実測）


def _log(m):
    print(m, flush=True)


def _exit_params(base: dict, tp: float, sl: float) -> dict:
    """V9 params のコピーに TP/SL/TimeExit の上書きを当てた dict（元 params・gen は不変）。"""
    return e8b.with_exit(base, {"P23_TP_PCT": tp, "P23_SL_PCT": sl, "P23_TIME_EXIT_MIN": TIME_FIXED})


# ======================================================================
# 連続モード 多クラス（gen._step を import 呼び出し・gen 改造なし）
#   新規建玉が開く型バー i（pos も pending も無い）の予測クラスで その建玉の出口 params を確定。
#   add は同じ建玉に積むのでクラスを引き継ぐ（active を変えない）。
#   ⚠ 既知の近似（E10 と同型）: 1バーで前建玉が閉じ同バーで次が開く稀ケースは前クラスを引き継ぐ
#     （gen import-only の制約・Web Claude レビュー対象・採点は score.py が正しく出す）。
# ======================================================================
def run_grid_continuous(df, bar_ms, params_by_cls, pred_cls_by_bar, default_cls, type_set):
    state = {"pos": None, "pending": None, "trades": []}
    active = params_by_cls[default_cls]
    initial_fn = lambda j: (j in type_set)
    for i in range(rc.CANDLE_WARMUP, len(df)):
        if state["pos"] is None and state["pending"] is None and (i in type_set):
            active = params_by_cls[pred_cls_by_bar.get(i, default_cls)]
        gen._step(state, df, bar_ms, i, active, initial_fn)
    if state["pos"] is not None:
        rc._record_trade(state["trades"], state["pos"], exit_price=float(df.iloc[-1]["close"]),
                         exit_reason="FORCE_CLOSE_EOD", exit_ts_ms=int(df.iloc[-1]["timestamp_ms"]), params=active)
    return state["trades"]


def train_multiclass(X, y, n_class, valid_frac=0.15):
    """末尾 valid_frac を時系列 valid に early stopping（多クラス）。学習済みモデルを返す。"""
    n = len(X)
    cut = max(1, int(n * (1.0 - valid_frac)))
    lp = dict(objective="multiclass", num_class=n_class, metric="multi_logloss",
              learning_rate=0.03, num_leaves=15, min_child_samples=100,
              feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1,
              lambda_l1=1.0, lambda_l2=1.0, seed=42, verbose=-1)
    dtr = lgb.Dataset(X.iloc[:cut], label=y[:cut])
    dva = lgb.Dataset(X.iloc[cut:], label=y[cut:], reference=dtr)
    model = lgb.train(lp, dtr, num_boost_round=3000, valid_sets=[dva],
                      callbacks=[lgb.early_stopping(80, verbose=False)])
    return model


def main():
    SMOKE = "--smoke" in sys.argv
    _log("[ExitGrid] P23 Exit TP/SL 場面別学習（多クラス・net基準・TimeExit固定480・連続モード・地面$925.73）")

    # 静的番人（実行前・私の正直さに依存しない）: leak 未来参照 / 期間分割
    rg.assert_no_future_ref(pathlib.Path(__file__).read_text())
    rg.assert_no_future_ref(pathlib.Path(e8b.__file__).read_text())
    rg.assert_period_split(TRAIN_ENTRY_END, SC_START)

    # ---- データ（P23 のみ有効・gen.main と同条件）----
    params = rc._load_params()
    p23 = dict(params)
    for k in list(p23):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p23[k] = (k == "ENABLE_P23_SHORT")
    df, _ = rc.preload(str(gen.OHLCV_CSV), p23)
    bar_ms = int(df.at[1, "timestamp_ms"] - df.at[0, "timestamp_ms"])
    ohlcv = pd.read_csv(e8b.OHLCV)
    ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])
    mp = e8b.build_multiperiod(ohlcv)             # 複数期間 方向系（ボラ系除外＝軸1・E8b 流用・E10 と同じ＝1ターン1変更）

    # ---- 型バー（θ足切りなし＝全部）----
    type_bars = [i for i in range(rc.CANDLE_WARMUP, len(df)) if gen._p23_type_fires(df, i)]
    type_set = set(type_bars)
    _log(f"[型バー] {len(type_bars)} 本（θ足切りなし・件数を減らさない・方針1）")
    _log(f"[グリッド] {len(EXIT_SETS)} 組 = TP{[t*100 for t in TP_GRID]}% × SL{[s*100 for s in SL_GRID]}% / TimeExit固定{TIME_FIXED}分（R:R自由・木が場面別に選ぶ）")

    # ---- 自己検査: AIゲート無し連続 == gen 型関数連続（移植一致・番人・本番のみ）----
    if not SMOKE:
        tr_ref = gen.run_continuous(df, bar_ms, params, lambda i: gen._p23_type_fires(df, i))
        tr_gate = gen.run_continuous(df, bar_ms, params, lambda i: (i in type_set))
        rg.assert_selfcheck_match(len(tr_gate), sum(float(t["net_usd"]) for t in tr_gate),
                                  len(tr_ref), sum(float(t["net_usd"]) for t in tr_ref))
        _log(f"[self-check] ✅ AIゲート無し連続 == 型関数連続（{len(tr_gate)}件・gen と同一挙動）")

    # ---- 教師ラベル: 各型バー × 各 TP/SL 組 を前向き sim → net 最大の組（学習期間のみ）----
    #   採点は予測クラスで（全型バー）。leak-safe（建玉時点から実価格を進めるだけ・H2）。
    train_tb = [i for i in type_bars
                if pd.to_datetime(df.at[i, "timestamp_ms"], unit="ms") < TRAIN_ENTRY_END]
    if SMOKE:
        step = max(1, len(train_tb) // 300)
        train_tb = train_tb[::step]
        _log(f"[SMOKE] 学習型バーを {len(train_tb)} 本に間引き（計算量実測用・本採点は省略）")
    _log(f"[教師] 学習期間型バー {len(train_tb)} 本 × {len(EXIT_SETS)} 組 = {len(train_tb) * len(EXIT_SETS)} sim → net 最大の組を正解クラスに")
    net_by_cls = {}
    for ci, (tp, sl) in enumerate(EXIT_SETS):
        lab_c = e8b.label_type_bars(df, bar_ms, _exit_params(params, tp, sl), train_tb)
        net_by_cls[ci] = lab_c.set_index("bar_i")["net_usd"]
        _log(f"  組{ci} TP{tp*100:.1f}%/SL{sl*100:.1f}%: 約定{len(lab_c)} / net合計${lab_c['net_usd'].sum():.0f} / avg${lab_c['net_usd'].mean():.2f}")
    net_mat = pd.DataFrame(net_by_cls).dropna()    # 全組が約定した型バーのみ（揃える）
    best_cls = net_mat.values.argmax(axis=1)
    lab = pd.DataFrame({"bar_i": net_mat.index.astype(int)})
    lab["bar_time"] = [pd.to_datetime(df.at[int(i), "timestamp_ms"], unit="ms") for i in lab["bar_i"]]
    lab["y"] = best_cls.astype(int)
    cls_dist = pd.Series(best_cls).value_counts(normalize=True).sort_index()
    _log(f"[教師ラベル] {len(lab)} 件 / 正解クラス分布（前向き sim の net 最大組）: "
         + str({int(k): round(float(v), 3) for k, v in cls_dist.items()}))
    assert len(np.unique(best_cls)) > 1, "教師ラベルが1クラスに張り付き（場面で最適 Exit が変わらない＝ML 価値なし・要報告）"

    # ---- 特徴量（E10 と同じ＝複数期間＋MTF・1ターン1変更=変更は出口学習のみ・H16）----
    X = e8b.make_features(lab["bar_time"], mp, ohlcv)
    n_class = len(EXIT_SETS)
    model = train_multiclass(X, lab["y"].values, n_class)
    _log(f"[train] 多クラス {n_class} / best_iter={model.best_iteration}")

    if SMOKE:
        _log("[SMOKE] 学習 OK（計算量実測完了）。本採点は省略＝本番で実行。")
        return

    # ---- 全型バー予測（採点用）----
    all_times = pd.Series([pd.to_datetime(df.at[i, "timestamp_ms"], unit="ms") for i in type_bars])
    X_all = e8b.make_features(all_times, mp, ohlcv)
    pred_all = model.predict(X_all, num_iteration=model.best_iteration).argmax(axis=1).astype(int)
    pred_cls_by_bar = dict(zip(type_bars, pred_all))

    # ② 場面別性の監視（＝ML 価値の判定・1組に張り付けば場面別でない）
    pred_dist = pd.Series(pred_all).value_counts(normalize=True).sort_index()
    _log(f"[②場面別性] 予測組の分布: {{{', '.join(f'{int(k)}:{v:.3f}' for k, v in pred_dist.items())}}}"
         f"（1組に張り付けば場面別でない＝ML 価値なし）")
    vr = rg.report_vol_importance(dict(zip(model.feature_name(), model.feature_importance("gain"))))
    _log(f"[②ボラ可視化] vol_share={vr['vol_share']} / top5={vr['top']}")

    # ---- 採点（連続モードで予測組 params 適用・cap0.12 ゲート score.py）----
    params_by_cls = {ci: _exit_params(params, tp, sl) for ci, (tp, sl) in enumerate(EXIT_SETS)}
    default_cls = int(pd.Series(best_cls).mode()[0])
    trades = run_grid_continuous(df, bar_ms, params_by_cls, pred_cls_by_bar, default_cls, type_set)
    if not trades:
        _log("[採点] トレード 0 件 → net $0（地面 $925.73 に負け）。正常終了。")
        return
    out_csv = RAT / "trades_p23_exitgrid.csv"
    tdf = pd.DataFrame(trades)
    for col in ("entry_time", "exit_time"):
        tdf[col] = pd.to_datetime(tdf[col])
    tdf.to_csv(out_csv, index=False)
    sc = tdf[(tdf["entry_time"] >= SC_START) & (tdf["entry_time"] < SC_END)].reset_index(drop=True)
    r = judge.score(sc)
    _log("\n===== 採点（score.py・cap0.12 ゲート・採点 2025-04〜12・連続モード）=====")
    _log(f"  AI(Exit 場面別): {r['n_trades']:5d}件 / 月平均 ${r['monthly_avg']:8.2f} / 合計 ${r['total']:8.1f}")
    if r.get("anomaly"):
        _log("  ⚠️ 異常値・要調査（H12）: " + " / ".join(r["anomaly"]))
    ground_total = None
    if GROUND.exists():
        g = pd.read_csv(GROUND)
        g["entry_time"] = pd.to_datetime(g["entry_time"]); g["exit_time"] = pd.to_datetime(g["exit_time"])
        gsc = g[(g["entry_time"] >= SC_START) & (g["entry_time"] < SC_END)].reset_index(drop=True)
        rgnd = judge.score(gsc)
        ground_total = rgnd["total"]
        _log(f"  地面 E0.2(連続モードV9手書きP23): {rgnd['n_trades']:5d}件 / 合計 ${rgnd['total']:8.1f}")
        _log(f"  → AI {'勝ち' if r['total'] > rgnd['total'] else '負け'}（差 ${r['total'] - rgnd['total']:+.1f} / 地面 $925.73）")

    # ---- 重要特徴 + 学習値 ----
    imp = pd.Series(model.feature_importance("gain"), index=X.columns).sort_values(ascending=False)
    _log("\n[重要特徴 top15（どの指標で出口組を分けているか）]\n" + imp.head(15).to_string())
    learned = {
        "_source": "train_p23_exit_grid.py（§10.17.1 章7・Exit TP/SL 場面別学習・多クラス・net 基準）",
        "_design": "入口θ足切りなし。各建玉に最適な TP/SL 組を場面別に多クラス分類（net 最大の組を教師）。"
                   "TimeExit 固定480。R:R 自由。地面 $925.73（E0.2）。",
        "EXIT_SETS": [{"cls": ci, "tp_pct": tp * 100, "sl_pct": sl * 100, "time_min": TIME_FIXED}
                      for ci, (tp, sl) in enumerate(EXIT_SETS)],
        "TEACHER_CLASS_DIST": {int(k): round(float(v), 3) for k, v in cls_dist.items()},
        "PRED_CLASS_DIST": {int(k): round(float(v), 3) for k, v in pred_dist.items()},
        "ML_VOL_SHARE": vr["vol_share"],
        "ML_BEST_ITER": int(model.best_iteration),
        "AI_SCORE_TOTAL_USD": round(float(r["total"]), 2),
        "AI_SCORE_MONTHLY_AVG_USD": round(float(r["monthly_avg"]), 2),
        "GROUND_E02_TOTAL_USD": round(float(ground_total), 2) if ground_total is not None else 925.73,
        "_top_features_gain": {k: round(float(v), 1) for k, v in imp.head(12).to_dict().items()},
    }
    json.dump(learned, open(RAT / "p23_learned_params_exitgrid.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    _log(f"\n[out] AI 連続モード trade → {out_csv}")
    _log(f"[out] 使用した値一覧 → p23_learned_params_exitgrid.json")
    _log("\n[次] python3 scripts/priority_rebuild/report.py "
         f"{out_csv} --start 2025-04-01 --end 2025-12-31 --vs {GROUND}  （A〜I 分析）")


if __name__ == "__main__":
    main()
