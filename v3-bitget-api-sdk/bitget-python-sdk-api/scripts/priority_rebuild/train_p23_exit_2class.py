#!/usr/bin/env python3
"""train_p23_exit_2class.py — P23 出口2分岐 ML（strat_v9ml_design §10.17.1 章7・まこさん承認 2026-06-10）

設計（§10.17.1 章7・確定）:
  - 木が「伸びるか」(章4 ラベル= 前向き H_HORIZON 本内に下落 MFE% >= T)を当てる（net 金額でない＝H15）。
  - 入口は θ足切りせず広く取る（型バー全部入る・件数を減らさない・方針1）。
  - 出口を木の伸びる確率で2分岐（建玉ごと・TP/SL/TimeExit セット・de Prado・バラさない）:
      伸びる玉(prob>=分け目) = base（V9 のまま: TP1.2%/Time480/SL5%・粘らせて大勝ち）
      伸びない玉(prob<分け目) = cut（TP0.6%/Time120/SL2%・早く小さく切る）
  - 分け目 = 学習期間の prob 中央値（採点期間は覗かない・類型C回避）。
  - グリッド(全玉共通の単一組)にしない＝玉ごとに変わる。具体値は §5 初期値（回して score.py で判定）。
  - 1回目は部分決済なし・連続モード（部分決済の刻みは2回目）。地面 = $925.73（E0.2・連続モード・cap遵守）。

★ 不正防止3点（cat_requirements §8.4-2.9）: 判定は score.py の数字のみ／実装後 Web Claude 独立レビュー→
  指摘を潰してから採点／番人(ratchet_guards)はメタ確認。本スクリプトは net 計算に触れない（score/eval_engine import のみ）。
gen_p23_candidates / replay_csv / score / eval_engine は import のみ・改造しない。
"""
from __future__ import annotations
import sys
import pathlib
import json
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                       # noqa: E402  V9 リプレイ（import のみ）
import gen_p23_candidates as gen              # noqa: E402  連続モード/型/_step（import のみ・改造しない）
import score as judge                         # noqa: E402  審判（import のみ・改造禁止）
import ratchet_guards as rg                   # noqa: E402  番人（leak/期間/ボラ可視化・既知答え済）
import train_p23_entry_E8b as e8b             # noqa: E402  学習・特徴量・採点ヘルパを流用（重複回避）

RAT = e8b.RAT
SC_START, SC_END = e8b.SC_START, e8b.SC_END
TRAIN_ENTRY_END = e8b.TRAIN_ENTRY_END
H_HORIZON, T_FACTOR = e8b.H_HORIZON, e8b.T_FACTOR
GROUND = e8b.GROUND                            # trades_p23_ground_capped.csv = $925.73（連続モード・部分決済なし・cap遵守）

# 伸びない玉の早切り params override（§5 初期値・まこさん承認 2026-06-10・回して直す）。
#   伸びる玉 = V9 base（override なし＝TP1.2%/Time480/SL5%）。SL は _calc_sl_price が P23_SL_PCT を優先で読む。
CUT_OVERRIDE = {"P23_TP_PCT": 0.006, "P23_TIME_EXIT_MIN": 120, "P23_SL_PCT": 0.02}


def _log(m):
    print(m, flush=True)


# ======================================================================
# 連続モード 2分岐（gen._step を import 呼び出し・gen 改造なし）
#   新規建玉が開く型バー i（pos も pending も無い）の prob で その建玉の出口クラスを確定:
#     prob >= theta_mid → base(伸びる=粘らせる) / else → cut(伸びない=早切り)。
#   add は同じ建玉に積むのでクラスを引き継ぐ（active を変えない）。
#   ⚠ 既知の近似: 1バーで前建玉が閉じ同バーで次が開く稀ケースは前クラスを引き継ぐ
#     （gen import-only の制約・Web Claude レビュー対象・採点は score.py が正しく出す）。
# ======================================================================
def run_2class_continuous(df, bar_ms, base_params, cut_params, prob_by_bar, theta_mid, type_set):
    state = {"pos": None, "pending": None, "trades": []}
    active = base_params
    initial_fn = lambda j: (j in type_set)
    for i in range(rc.CANDLE_WARMUP, len(df)):
        if state["pos"] is None and state["pending"] is None and (i in type_set):
            active = base_params if prob_by_bar.get(i, 0.0) >= theta_mid else cut_params
        gen._step(state, df, bar_ms, i, active, initial_fn)
    if state["pos"] is not None:
        rc._record_trade(state["trades"], state["pos"], exit_price=float(df.iloc[-1]["close"]),
                         exit_reason="FORCE_CLOSE_EOD", exit_ts_ms=int(df.iloc[-1]["timestamp_ms"]), params=active)
    return state["trades"]


def main():
    SMOKE = "--smoke" in sys.argv
    _log("[Exit2class] P23 出口2分岐 ML（伸びる=粘らせる / 伸びない=早切り・連続モード・地面 $925.73）")

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
    mp = e8b.build_multiperiod(ohlcv)                          # 複数期間 方向系（ボラ系除外＝軸1・E8b 流用）

    # ---- 型バー（θ足切りなし＝全部・件数を減らさない）----
    type_bars = [i for i in range(rc.CANDLE_WARMUP, len(df)) if gen._p23_type_fires(df, i)]
    type_set = set(type_bars)
    _log(f"[型バー] {len(type_bars)} 本（θ足切りなし＝全部入る・件数を減らさない・方針1）")

    # ---- ラベル「伸びるか」: 各型バー close 基準・前向き H_HORIZON 本内の下落 MFE% >= T（教師のみ=leak-safe・H2）----
    close_a = df["close"].to_numpy()
    low_a = df["low_raw"].to_numpy()
    nb = len(df)
    rows = []
    for i in type_bars:
        e = float(close_a[i])
        end = min(nb - 1, i + H_HORIZON)
        lo = low_a[i + 1:end + 1]
        mfe = (e - float(lo.min())) / e * 100.0 if len(lo) and e > 0 else 0.0
        rows.append({"bar_i": i, "bar_time": pd.to_datetime(df.at[i, "timestamp_ms"], unit="ms"), "mfe_pct": mfe})
    lab = pd.DataFrame(rows)
    is_tr = lab["bar_time"] < TRAIN_ENTRY_END
    is_sc = (lab["bar_time"] >= SC_START) & (lab["bar_time"] < SC_END)
    # T = 学習期間 V9base 勝ち玉(net>0) の前向き96本 下落MFE% 中央値 1.392% × 0.65 = 0.905%
    #   （§10.17.1 章4・data由来・固定・/tmp/measure_T_label.py で実測済）。net金額にしない（H15）・採点は見ない。
    T = 0.905
    lab["y"] = (lab["mfe_pct"] >= T).astype(int)
    _log(f"[ラベル] 伸びるか = 保有{H_HORIZON}本内 下落MFE% >= T={T:.3f}%（学習勝ち玉MFE%中央値×{T_FACTOR}・data由来）"
         f" / 伸びた {int(lab['y'].sum())} / 全 {len(lab)} / 伸び率 {lab['y'].mean() * 100:.1f}%（金額不使用=軸1 / MFEは教師のみ=leak-safe）")

    # ---- 特徴量（方向系・ATR/bb_width 除外＝軸1・E8b の make_features 流用）----
    X = e8b.make_features(lab["bar_time"], mp, ohlcv)
    Xtr = X[is_tr.values].reset_index(drop=True)
    ytr = lab.loc[is_tr, "y"].values
    assert len(np.unique(ytr)) > 1, "学習ラベルが片寄り（伸びた/伸びない の一方が0）"

    # ---- 学習（E8b.train_lgb 流用・既定ハイパラ・過学習対策）----
    lparams = dict(objective="binary", metric="auc", learning_rate=0.03, num_leaves=15,
                   min_child_samples=100, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1,
                   lambda_l1=1.0, lambda_l2=1.0, seed=42, verbose=-1)
    model, pos_w = e8b.train_lgb(Xtr, ytr, lparams)
    prob_all = model.predict(X, num_iteration=model.best_iteration)
    prob_by_bar = dict(zip(lab["bar_i"].astype(int).values, prob_all))
    theta_mid = float(np.median(prob_all[is_tr.values]))      # 分け目 = 学習期間 prob 中央値（採点は覗かない・C）
    if len(np.unique(lab.loc[is_sc, "y"])) > 1:
        _log(f"[参考] 採点AUC={roc_auc_score(lab.loc[is_sc, 'y'], prob_all[is_sc.values]):.4f}（最終判定は net）")
    _log(f"[分け目] 学習 prob 中央値 theta_mid={theta_mid:.4f}（以上=伸びる/粘らせる ・ 未満=伸びない/早切り）")

    # ② ボラ可視化（軸1・X からボラ系除外済なので 0 期待）
    vr = rg.report_vol_importance(dict(zip(model.feature_name(), model.feature_importance("gain"))))
    _log(f"[②ボラ可視化] vol_share={vr['vol_share']} / top5={vr['top']}（X からボラ系除外済＝0 期待）")

    base_p = e8b.with_exit(params, {})                        # 伸びる = V9 base
    cut_p = e8b.with_exit(params, CUT_OVERRIDE)               # 伸びない = 早切り override
    _log(f"[出口2分岐] 伸びる(base)=TP{base_p['P23_TP_PCT']}/Time{base_p['P23_TIME_EXIT_MIN']}"
         f"/SL{base_p.get('P23_SL_PCT', base_p['SHORT_SL_PCT'])}"
         f" ／ 伸びない(cut)=TP{cut_p['P23_TP_PCT']}/Time{cut_p['P23_TIME_EXIT_MIN']}/SL{cut_p['P23_SL_PCT']}")

    if SMOKE:
        _log("[SMOKE] 完了（学習・分け目・ボラ可視化・2分岐 params 確認 OK・本採点は省略＝Web Claude レビュー後）")
        return

    # ---- 連続モード 2分岐 → 採点（score.py・cap0.12 ゲート）----
    trades = run_2class_continuous(df, bar_ms, base_p, cut_p, prob_by_bar, theta_mid, type_set)
    if not trades:
        _log("[採点] トレード 0 件 → net $0（地面 $925.73 に負け）。正常終了。")
        return
    out_csv = RAT / "trades_p23_exit2class.csv"
    tdf = pd.DataFrame(trades)
    for col in ("entry_time", "exit_time"):
        tdf[col] = pd.to_datetime(tdf[col])
    tdf.to_csv(out_csv, index=False)
    sc = tdf[(tdf["entry_time"] >= SC_START) & (tdf["entry_time"] < SC_END)].reset_index(drop=True)
    r = judge.score(sc)
    _log("\n===== 採点（score.py・cap0.12 ゲート・採点 2025-04〜12・連続モード）=====")
    _log(f"  AI(出口2分岐): {r['n_trades']:5d}件 / 月平均 ${r['monthly_avg']:8.2f} / 合計 ${r['total']:8.1f}")
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

    # ---- 重要特徴 + 学習値（§10.4 の答え）----
    imp = pd.Series(model.feature_importance("gain"), index=X.columns).sort_values(ascending=False)
    _log("\n[重要特徴 top15（どの指標・どの期間を見ているか）]\n" + imp.head(15).to_string())
    all_scored = lab.copy()
    all_scored["p"] = prob_all
    all_scored["side"] = "SHORT"
    all_scored.to_csv(RAT / "trades_p23_exit2class_all_scored.csv", index=False)

    learned = {
        "_source": "train_p23_exit_2class.py（§10.17.1 章7・出口2分岐・連続モード・部分決済なし）",
        "_design": "入口θ足切りなし（全型バー）。出口を伸びる確率で2分岐: 伸びる(prob>=学習中央値)=base(TP1.2/Time480/SL5) "
                   "/ 伸びない=cut(TP0.6/Time120/SL2)。TP/SL/TimeExit セット・de Prado。地面 $925.73(E0.2)。",
        "ML_THETA_MID": round(theta_mid, 4),
        "ML_CUT_OVERRIDE": CUT_OVERRIDE,
        "ML_LABEL_T_PCT": round(T, 4),
        "ML_BEST_ITER": int(model.best_iteration),
        "ML_SCALE_POS_WEIGHT": round(float(pos_w), 2),
        "ML_VOL_SHARE": vr["vol_share"],
        "ML_AUC_SCORE": round(float(roc_auc_score(lab.loc[is_sc, "y"], prob_all[is_sc.values])), 3)
        if len(np.unique(lab.loc[is_sc, "y"])) > 1 else None,
        "AI_SCORE_TOTAL_USD": round(float(r["total"]), 2),
        "AI_SCORE_MONTHLY_AVG_USD": round(float(r["monthly_avg"]), 2),
        "GROUND_E02_TOTAL_USD": round(float(ground_total), 2) if ground_total is not None else None,
        "_top_features_gain": {k: round(float(v), 1) for k, v in imp.head(12).to_dict().items()},
    }
    json.dump(learned, open(RAT / "p23_learned_params_exit2class.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    _log(f"\n[out] AI 連続モード trade → {out_csv}")
    _log(f"[out] 全型バー(prob付き) → trades_p23_exit2class_all_scored.csv")
    _log(f"[out] 使用した値一覧 → p23_learned_params_exit2class.json")
    _log("\n[次] python3 scripts/priority_rebuild/report.py "
         f"{out_csv} --start 2025-04-01 --end 2025-12-31 --vs {GROUND}  （A〜I 分析）")


if __name__ == "__main__":
    main()
