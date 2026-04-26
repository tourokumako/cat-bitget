"""Phase 2: HMM ハイパラ網羅サーチ（n=3-7 × cov={full,diag} × seed=5種・計50組）

入力:
  results/phase1_features_daily.csv
  data/BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv

処理:
  全組み合わせを fit → 候補B 各項目スコア化 → 上位5構成を表示
  最良構成は phase2_hmm_train.py と同じフォーマットで出力

出力:
  results/phase2_hmm_search_summary.json（全組合せの結果）
  results/phase2_hmm_states_daily_best.csv（最良構成）
  results/phase2_hmm_eval_best.json（最良構成の詳細）

スコア定義:
  各項目（UPTREND_ret/DOWNTREND_ret/RANGE_ret/各duration/各pvalue）が
  基準にどれだけ近いか正規化（0=完全達成・正値=未達距離）。総和最小が最良。
"""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from scipy import stats
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
FEAT_PATH = REPO_ROOT / "results" / "phase1_features_daily.csv"
RAW_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"
OUT_DIR = REPO_ROOT / "results"

CRITERIA_B = {
    "uptrend_min": 1.2212616859789105,
    "downtrend_max": -0.8215951246819279,
    "range_max_abs": 0.3404761351101398,
    "duration_min": 3,
    "duration_max": 30,
    "p_value_max": 0.05,
}

N_STATES_LIST = [6, 7, 8, 9, 10]
COV_TYPES = ["full"]
SEEDS = [0, 7, 42, 123, 2024, 2025, 2026, 9999]
FEATURE_SUBSETS = {
    "all": None,
    "drop_ma50_dev": ["ma50_dev"],
    "drop_ret_skew_30d": ["ret_skew_30d"],
    "drop_volcat": ["atr_14_pct", "bb_width_20", "bb_pct_b"],
}


def load_daily_returns() -> pd.Series:
    df = pd.read_csv(RAW_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    daily_close = df.set_index("ts")["close"].resample("D").last().dropna()
    daily_ret = daily_close.pct_change() * 100
    daily_ret.index = daily_ret.index.normalize()
    return daily_ret


def load_features() -> pd.DataFrame:
    feats = pd.read_csv(FEAT_PATH, parse_dates=["date"]).set_index("date")
    feats.index = feats.index.normalize()
    return feats


def state_durations(states: np.ndarray) -> dict[int, list[int]]:
    durations: dict[int, list[int]] = {}
    if len(states) == 0:
        return durations
    cur = states[0]
    cnt = 1
    for s in states[1:]:
        if s == cur:
            cnt += 1
        else:
            durations.setdefault(int(cur), []).append(cnt)
            cur = s
            cnt = 1
    durations.setdefault(int(cur), []).append(cnt)
    return durations


def label_states(state_returns: dict[int, float], n_states: int) -> dict[int, str]:
    sorted_states = sorted(state_returns.items(), key=lambda x: x[1])
    labels: dict[int, str] = {}
    if n_states == 3:
        labels[sorted_states[0][0]] = "DOWNTREND"
        labels[sorted_states[1][0]] = "RANGE"
        labels[sorted_states[2][0]] = "UPTREND"
    else:
        labels[sorted_states[0][0]] = "DOWNTREND"
        labels[sorted_states[-1][0]] = "UPTREND"
        # 中間: 平均リターンが0に最も近いものを RANGE とする
        mids = sorted_states[1:-1]
        mids_sorted = sorted(mids, key=lambda x: abs(x[1]))
        labels[mids_sorted[0][0]] = "RANGE"
        for i, (sid, _) in enumerate(mids_sorted[1:], start=1):
            labels[sid] = f"MID{i}"
    return labels


def evaluate(
    states: np.ndarray,
    returns: np.ndarray,
    feats: pd.DataFrame,
    model: GaussianHMM,
    n_states: int,
) -> dict:
    state_returns = {
        int(s): float(np.mean(returns[states == s]))
        for s in range(n_states)
        if (states == s).any()
    }
    if len(state_returns) < n_states:
        return {"degenerate": True}

    labels = label_states(state_returns, n_states)
    durations = state_durations(states)
    overall_mean = float(np.mean(returns))

    state_summary: dict[str, dict] = {}
    for s in range(n_states):
        mask = states == s
        if not mask.any():
            continue
        sret = returns[mask]
        if len(sret) > 1:
            t_stat, p_val = stats.ttest_1samp(sret, overall_mean)
        else:
            t_stat, p_val = float("nan"), float("nan")
        durs = durations.get(s, [])
        state_summary[labels[s]] = {
            "state_id": int(s),
            "n_days": int(mask.sum()),
            "share_pct": round(float(mask.mean() * 100), 2),
            "ret_mean_pct": round(float(np.mean(sret)), 4),
            "ret_median_pct": round(float(np.median(sret)), 4),
            "ret_std_pct": round(float(np.std(sret)), 4),
            "t_stat_vs_overall": None if np.isnan(t_stat) else round(float(t_stat), 4),
            "p_value": None if np.isnan(p_val) else round(float(p_val), 6),
            "duration_median_days": float(np.median(durs)) if durs else None,
            "duration_mean_days": round(float(np.mean(durs)), 2) if durs else None,
            "duration_max_days": int(max(durs)) if durs else None,
            "n_runs": len(durs),
            "feature_means": {
                col: round(float(feats.loc[mask, col].mean()), 4)
                for col in feats.columns
            },
        }

    pass_check = {}
    score_components = {}
    if "UPTREND" in state_summary:
        up = state_summary["UPTREND"]
        pass_check["UPTREND_ret"] = up["ret_mean_pct"] > CRITERIA_B["uptrend_min"]
        score_components["UPTREND_ret"] = max(0.0, CRITERIA_B["uptrend_min"] - up["ret_mean_pct"])
        pass_check["UPTREND_duration"] = (
            up["duration_median_days"] is not None
            and CRITERIA_B["duration_min"] <= up["duration_median_days"] <= CRITERIA_B["duration_max"]
        )
        if up["duration_median_days"] is None:
            score_components["UPTREND_duration"] = 10
        elif up["duration_median_days"] < CRITERIA_B["duration_min"]:
            score_components["UPTREND_duration"] = (CRITERIA_B["duration_min"] - up["duration_median_days"]) * 0.5
        elif up["duration_median_days"] > CRITERIA_B["duration_max"]:
            score_components["UPTREND_duration"] = (up["duration_median_days"] - CRITERIA_B["duration_max"]) * 0.05
        else:
            score_components["UPTREND_duration"] = 0
        pass_check["UPTREND_pvalue"] = up["p_value"] is not None and up["p_value"] < CRITERIA_B["p_value_max"]
        score_components["UPTREND_pvalue"] = 0 if pass_check["UPTREND_pvalue"] else 0.5

    if "DOWNTREND" in state_summary:
        dn = state_summary["DOWNTREND"]
        pass_check["DOWNTREND_ret"] = dn["ret_mean_pct"] < CRITERIA_B["downtrend_max"]
        score_components["DOWNTREND_ret"] = max(0.0, dn["ret_mean_pct"] - CRITERIA_B["downtrend_max"])
        pass_check["DOWNTREND_duration"] = (
            dn["duration_median_days"] is not None
            and CRITERIA_B["duration_min"] <= dn["duration_median_days"] <= CRITERIA_B["duration_max"]
        )
        if dn["duration_median_days"] is None:
            score_components["DOWNTREND_duration"] = 10
        elif dn["duration_median_days"] < CRITERIA_B["duration_min"]:
            score_components["DOWNTREND_duration"] = (CRITERIA_B["duration_min"] - dn["duration_median_days"]) * 0.5
        elif dn["duration_median_days"] > CRITERIA_B["duration_max"]:
            score_components["DOWNTREND_duration"] = (dn["duration_median_days"] - CRITERIA_B["duration_max"]) * 0.05
        else:
            score_components["DOWNTREND_duration"] = 0
        pass_check["DOWNTREND_pvalue"] = dn["p_value"] is not None and dn["p_value"] < CRITERIA_B["p_value_max"]
        score_components["DOWNTREND_pvalue"] = 0 if pass_check["DOWNTREND_pvalue"] else 0.5

    if "RANGE" in state_summary:
        rg = state_summary["RANGE"]
        pass_check["RANGE_ret"] = abs(rg["ret_mean_pct"]) < CRITERIA_B["range_max_abs"]
        score_components["RANGE_ret"] = max(0.0, abs(rg["ret_mean_pct"]) - CRITERIA_B["range_max_abs"])
        pass_check["RANGE_duration"] = (
            rg["duration_median_days"] is not None
            and CRITERIA_B["duration_min"] <= rg["duration_median_days"] <= CRITERIA_B["duration_max"]
        )
        if rg["duration_median_days"] is None:
            score_components["RANGE_duration"] = 10
        elif rg["duration_median_days"] < CRITERIA_B["duration_min"]:
            score_components["RANGE_duration"] = (CRITERIA_B["duration_min"] - rg["duration_median_days"]) * 0.5
        elif rg["duration_median_days"] > CRITERIA_B["duration_max"]:
            score_components["RANGE_duration"] = (rg["duration_median_days"] - CRITERIA_B["duration_max"]) * 0.05
        else:
            score_components["RANGE_duration"] = 0

    transition_matrix = [[round(float(p), 4) for p in row] for row in model.transmat_]
    return {
        "degenerate": False,
        "labels": {str(k): v for k, v in labels.items()},
        "state_summary": state_summary,
        "pass_check": pass_check,
        "all_passed": all(pass_check.values()) if pass_check else False,
        "score": round(sum(score_components.values()), 4),
        "score_components": {k: round(v, 4) for k, v in score_components.items()},
        "transition_matrix_label_order": [labels[i] for i in range(n_states)],
        "transition_matrix": transition_matrix,
    }


def main() -> None:
    print(f"[search] 特徴量読込: {FEAT_PATH.name}")
    feats = load_features()
    daily_ret_full = load_daily_returns()
    common_idx = feats.index.intersection(daily_ret_full.index)
    feats = feats.loc[common_idx]
    returns_aligned = daily_ret_full.loc[common_idx]
    if returns_aligned.isna().any():
        keep = ~returns_aligned.isna()
        feats = feats[keep]
        returns_aligned = returns_aligned[keep]
    print(f"  整列: {len(feats)}日 / mean={returns_aligned.mean():.4f}% std={returns_aligned.std():.4f}%")

    combos = list(product(N_STATES_LIST, COV_TYPES, SEEDS, FEATURE_SUBSETS.keys()))
    print(f"[search] 組み合わせ: {len(combos)} 件 (n_states×cov×seed×subset)")

    # サブセット別に scaler 用意
    feats_subsets: dict[str, pd.DataFrame] = {}
    X_subsets: dict[str, np.ndarray] = {}
    for sname, drop_cols in FEATURE_SUBSETS.items():
        if drop_cols:
            sub = feats.drop(columns=drop_cols)
        else:
            sub = feats
        feats_subsets[sname] = sub
        X_subsets[sname] = StandardScaler().fit_transform(sub.values)

    results = []
    failed = 0
    for i, (n, cov, seed, sname) in enumerate(combos, 1):
        try:
            sub_feats = feats_subsets[sname]
            X = X_subsets[sname]
            model = GaussianHMM(
                n_components=n,
                covariance_type=cov,
                n_iter=200,
                tol=1e-4,
                random_state=seed,
            )
            model.fit(X)
            states = model.predict(X)
            ev = evaluate(states, returns_aligned.values, sub_feats, model, n)
            if ev.get("degenerate"):
                failed += 1
                continue
            ev["n_states"] = n
            ev["covariance_type"] = cov
            ev["random_state"] = seed
            ev["feature_subset"] = sname
            ev["n_features"] = sub_feats.shape[1]
            ev["log_likelihood"] = round(float(model.score(X)), 4)
            ev["converged"] = bool(model.monitor_.converged)
            ev["_states_array"] = states
            ev["_feats_subset"] = sub_feats
            ev["_model"] = model
            results.append(ev)
        except Exception as e:
            print(f"  [{i}/{len(combos)}] n={n} seed={seed} subset={sname} → ERROR: {e}")
            failed += 1
        if i % 20 == 0:
            print(f"  進捗: {i}/{len(combos)} (失敗 {failed})")

    print(f"\n[search] 完了: 成功 {len(results)} / 失敗 {failed}")

    # 合格優先・次にスコア昇順
    results.sort(key=lambda r: (not r["all_passed"], r["score"]))

    # サマリ JSON（_states_array/_model は除外）
    summary_records = []
    for r in results:
        rec = {k: v for k, v in r.items() if not k.startswith("_")}
        summary_records.append(rec)
    summary_path = OUT_DIR / "phase2_hmm_search_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary_records, f, indent=2, ensure_ascii=False)
    print(f"  → {summary_path.name}（全{len(summary_records)}件）")

    # 上位5表示
    print(f"\n========== 上位5構成 ==========")
    for rank, r in enumerate(results[:5], 1):
        ss = r["state_summary"]
        up = ss.get("UPTREND", {})
        dn = ss.get("DOWNTREND", {})
        rg = ss.get("RANGE", {})
        print(
            f"\n  #{rank}  n={r['n_states']} seed={r['random_state']} subset={r['feature_subset']}({r['n_features']}f)"
            f"  score={r['score']}  pass={r['all_passed']}  logL={r['log_likelihood']}"
        )
        print(
            f"    UP   ret={up.get('ret_mean_pct')}%  dur_med={up.get('duration_median_days')}  p={up.get('p_value')}"
        )
        print(
            f"    DOWN ret={dn.get('ret_mean_pct')}%  dur_med={dn.get('duration_median_days')}  p={dn.get('p_value')}"
        )
        print(
            f"    RANGE ret={rg.get('ret_mean_pct')}%  dur_med={rg.get('duration_median_days')}"
        )
        for k, v in r["pass_check"].items():
            print(f"      {'✅' if v else '❌'} {k}")

    # 最良構成を CSV/JSON 出力
    if results:
        best = results[0]
        out_csv = OUT_DIR / "phase2_hmm_states_daily_best.csv"
        labels_map = {int(k): v for k, v in best["labels"].items()}
        best_idx = best["_feats_subset"].index
        out_df = pd.DataFrame({
            "date": best_idx,
            "state_id": best["_states_array"],
            "state_label": [labels_map[int(s)] for s in best["_states_array"]],
            "daily_return_pct": returns_aligned.loc[best_idx].values,
        })
        out_df.to_csv(out_csv, index=False)
        print(f"\n  最良 → {out_csv.name}")

        best_eval = {k: v for k, v in best.items() if not k.startswith("_")}
        out_json = OUT_DIR / "phase2_hmm_eval_best.json"
        with open(out_json, "w") as f:
            json.dump(best_eval, f, indent=2, ensure_ascii=False)
        print(f"  最良 → {out_json.name}")


if __name__ == "__main__":
    main()
