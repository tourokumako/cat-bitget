"""Phase 2: ガウシアンHMM 学習・状態解釈・候補B合格判定

入力:
  results/phase1_features_daily.csv（1778行 × 8特徴・warmup49日除外）
  data/BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv（日次リターン算出元）

処理:
  1. 8特徴を StandardScaler で正規化
  2. GaussianHMM(n_components=N, covariance_type="full") で fit
  3. 各日の予測状態 + 遷移確率行列 + 状態別 平均特徴量
  4. 状態別 平均日次リターン・継続日数中央値・t検定
  5. 候補B（平均±0.3σ）合格判定

出力:
  results/phase2_hmm_states_daily_n{N}.csv
  results/phase2_hmm_eval_n{N}.json

CLI:
  python3 scripts/phase2_hmm_train.py            # n=3 のみ
  python3 scripts/phase2_hmm_train.py --all      # n=3,4,5 全部
  python3 scripts/phase2_hmm_train.py -n 4       # n=4 のみ
"""
from __future__ import annotations

import argparse
import json
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

RANDOM_STATE = 42


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


def fit_hmm(X: np.ndarray, n_states: int) -> GaussianHMM:
    model = GaussianHMM(
        n_components=n_states,
        covariance_type="full",
        n_iter=200,
        tol=1e-4,
        random_state=RANDOM_STATE,
    )
    model.fit(X)
    return model


def label_states_by_return(state_returns: dict[int, float], n_states: int) -> dict[int, str]:
    """平均リターン昇順 → DOWN < ... < UP のラベル割当."""
    sorted_states = sorted(state_returns.items(), key=lambda x: x[1])
    labels: dict[int, str] = {}
    if n_states == 3:
        labels[sorted_states[0][0]] = "DOWNTREND"
        labels[sorted_states[1][0]] = "RANGE"
        labels[sorted_states[2][0]] = "UPTREND"
    else:
        labels[sorted_states[0][0]] = "DOWNTREND"
        labels[sorted_states[-1][0]] = "UPTREND"
        for i, (sid, _) in enumerate(sorted_states[1:-1], start=1):
            labels[sid] = f"MID{i}"
    return labels


def state_durations(states: np.ndarray) -> dict[int, list[int]]:
    """各状態の連続滞在日数リスト."""
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


def evaluate_states(
    states: np.ndarray,
    returns: np.ndarray,
    feats: pd.DataFrame,
    model: GaussianHMM,
    n_states: int,
) -> tuple[dict, dict[int, str]]:
    state_returns = {
        int(s): float(np.mean(returns[states == s]))
        for s in range(n_states)
        if (states == s).any()
    }
    labels = label_states_by_return(state_returns, n_states)
    durations = state_durations(states)

    state_summary = {}
    overall_mean = float(np.mean(returns))
    for s in range(n_states):
        mask = states == s
        if not mask.any():
            continue
        sret = returns[mask]
        # 全体平均との差をt検定（その状態の特殊性確認）
        if len(sret) > 1:
            t_stat, p_val = stats.ttest_1samp(sret, overall_mean)
        else:
            t_stat, p_val = float("nan"), float("nan")
        durs = durations.get(s, [])
        state_summary[labels[s]] = {
            "state_id": s,
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

    # 候補B合格判定
    pass_check = {}
    if "UPTREND" in state_summary:
        up = state_summary["UPTREND"]
        pass_check["UPTREND_ret"] = up["ret_mean_pct"] > CRITERIA_B["uptrend_min"]
        pass_check["UPTREND_duration"] = (
            up["duration_median_days"] is not None
            and CRITERIA_B["duration_min"] <= up["duration_median_days"] <= CRITERIA_B["duration_max"]
        )
        pass_check["UPTREND_pvalue"] = up["p_value"] is not None and up["p_value"] < CRITERIA_B["p_value_max"]
    if "DOWNTREND" in state_summary:
        dn = state_summary["DOWNTREND"]
        pass_check["DOWNTREND_ret"] = dn["ret_mean_pct"] < CRITERIA_B["downtrend_max"]
        pass_check["DOWNTREND_duration"] = (
            dn["duration_median_days"] is not None
            and CRITERIA_B["duration_min"] <= dn["duration_median_days"] <= CRITERIA_B["duration_max"]
        )
        pass_check["DOWNTREND_pvalue"] = dn["p_value"] is not None and dn["p_value"] < CRITERIA_B["p_value_max"]
    if "RANGE" in state_summary:
        rg = state_summary["RANGE"]
        pass_check["RANGE_ret"] = abs(rg["ret_mean_pct"]) < CRITERIA_B["range_max_abs"]
        pass_check["RANGE_duration"] = (
            rg["duration_median_days"] is not None
            and CRITERIA_B["duration_min"] <= rg["duration_median_days"] <= CRITERIA_B["duration_max"]
        )

    transition_matrix = [[round(float(p), 4) for p in row] for row in model.transmat_]

    eval_dict = {
        "n_states": n_states,
        "n_days_total": int(len(states)),
        "log_likelihood": round(float(model.score(feats.values)), 4) if False else None,
        "criteria_B": CRITERIA_B,
        "labels": {str(k): v for k, v in labels.items()},
        "state_summary": state_summary,
        "pass_check": pass_check,
        "all_passed": all(pass_check.values()) if pass_check else False,
        "transition_matrix_label_order": [labels[i] for i in range(n_states)],
        "transition_matrix": transition_matrix,
    }
    return eval_dict, labels


def run_for_n(n_states: int, feats: pd.DataFrame, returns_aligned: pd.Series) -> dict:
    print(f"\n========== n_states = {n_states} ==========")
    scaler = StandardScaler()
    X = scaler.fit_transform(feats.values)

    model = fit_hmm(X, n_states)
    states = model.predict(X)
    print(f"  収束: {model.monitor_.converged} / iter={model.monitor_.iter}")

    eval_dict, labels = evaluate_states(states, returns_aligned.values, feats, model, n_states)
    eval_dict["log_likelihood"] = round(float(model.score(X)), 4)
    eval_dict["converged"] = bool(model.monitor_.converged)
    eval_dict["n_iter"] = int(model.monitor_.iter)

    # CSV 出力（date / state_id / state_label / daily_return）
    out_csv = OUT_DIR / f"phase2_hmm_states_daily_n{n_states}.csv"
    out_df = pd.DataFrame({
        "date": feats.index,
        "state_id": states,
        "state_label": [labels[s] for s in states],
        "daily_return_pct": returns_aligned.values,
    })
    out_df.to_csv(out_csv, index=False)
    print(f"  → {out_csv.name} ({len(out_df)}行)")

    out_json = OUT_DIR / f"phase2_hmm_eval_n{n_states}.json"
    with open(out_json, "w") as f:
        json.dump(eval_dict, f, indent=2, ensure_ascii=False)
    print(f"  → {out_json.name}")

    # サマリ表示
    print(f"\n  [状態別サマリ]")
    for label, s in eval_dict["state_summary"].items():
        print(
            f"    {label:10s} n={s['n_days']:4d} ({s['share_pct']:5.2f}%)"
            f"  ret_mean={s['ret_mean_pct']:+7.4f}%  median={s['ret_median_pct']:+7.4f}%"
            f"  dur_median={s['duration_median_days']}  p={s['p_value']}"
        )

    print(f"\n  [候補B 合格判定]")
    for k, v in eval_dict["pass_check"].items():
        print(f"    {'✅' if v else '❌'} {k}")
    print(f"  → 総合: {'✅ 合格' if eval_dict['all_passed'] else '❌ 不合格'}")

    return eval_dict


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--n-states", type=int, default=3)
    parser.add_argument("--all", action="store_true", help="n=3,4,5 全部実行")
    args = parser.parse_args()

    print(f"[phase2] 特徴量読込: {FEAT_PATH.name}")
    feats = load_features()
    print(f"  {len(feats)}行 × {len(feats.columns)}列")

    print(f"[phase2] 日次リターン算出: {RAW_PATH.name}")
    daily_ret_full = load_daily_returns()

    # 特徴量と日次リターンを date で揃える
    common_idx = feats.index.intersection(daily_ret_full.index)
    feats = feats.loc[common_idx]
    returns_aligned = daily_ret_full.loc[common_idx]
    # 1日目の return が NaN になる可能性
    if returns_aligned.isna().any():
        keep = ~returns_aligned.isna()
        feats = feats[keep]
        returns_aligned = returns_aligned[keep]
    print(f"  整列後: {len(feats)}日（{feats.index.min().date()} 〜 {feats.index.max().date()}）")
    print(f"  リターン分布: mean={returns_aligned.mean():.4f}% std={returns_aligned.std():.4f}%")

    n_list = [3, 4, 5] if args.all else [args.n_states]
    results = {}
    for n in n_list:
        results[n] = run_for_n(n, feats, returns_aligned)

    print(f"\n========== 全体まとめ ==========")
    for n, ev in results.items():
        print(f"  n={n}: {'✅ 合格' if ev['all_passed'] else '❌ 不合格'}  logL={ev['log_likelihood']}")


if __name__ == "__main__":
    main()
