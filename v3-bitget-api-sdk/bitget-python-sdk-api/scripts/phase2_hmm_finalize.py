"""Phase 2 確定: マルチイニット最良採択 + 固定モデル戦略

候補2構成（n=6/drop_ret_skew_30d, n=7/drop_ma50_dev）× seed 100通り = 200試行
→ 候補B合格 → logL最大 → DOWN/UPマージン最大 で採択
→ pickle で models/hmm_final.pkl に凍結保存

入力: results/phase1_features_daily.csv, data/BTCUSDT-...5y.csv
出力:
  models/hmm_final.pkl（model + scaler + config + labels）
  results/phase2_hmm_final_states.csv
  results/phase2_hmm_final_summary.json
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from scipy import stats
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
FEAT_PATH = REPO_ROOT / "results" / "phase1_features_daily.csv"
RAW_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"
MODEL_PATH = REPO_ROOT / "models" / "hmm_final.pkl"
STATES_CSV = REPO_ROOT / "results" / "phase2_hmm_final_states.csv"
SUMMARY_JSON = REPO_ROOT / "results" / "phase2_hmm_final_summary.json"

CRITERIA_B = {
    "uptrend_min": 1.2212616859789105,
    "downtrend_max": -0.8215951246819279,
    "range_max_abs": 0.3404761351101398,
    "duration_min": 3,
    "duration_max": 30,
    "p_value_max": 0.05,
}

CANDIDATES = [
    {"label": "n6_drop_ret_skew", "n_states": 6, "drop_features": ["ret_skew_30d"]},
    {"label": "n7_drop_ma50_dev", "n_states": 7, "drop_features": ["ma50_dev"]},
]
N_SEEDS = 100


def load_data():
    feats = pd.read_csv(FEAT_PATH, parse_dates=["date"]).set_index("date")
    feats.index = feats.index.normalize()
    df = pd.read_csv(RAW_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    daily_close = df.set_index("ts")["close"].resample("D").last().dropna()
    daily_ret = daily_close.pct_change() * 100
    daily_ret.index = daily_ret.index.normalize()
    common = feats.index.intersection(daily_ret.index)
    feats = feats.loc[common]
    rets = daily_ret.loc[common]
    keep = ~rets.isna()
    return feats[keep], rets[keep]


def state_durations(states):
    durations = {}
    if len(states) == 0:
        return durations
    cur, cnt = states[0], 1
    for s in states[1:]:
        if s == cur:
            cnt += 1
        else:
            durations.setdefault(int(cur), []).append(cnt)
            cur, cnt = s, 1
    durations.setdefault(int(cur), []).append(cnt)
    return durations


def label_states(state_returns, n_states):
    sorted_s = sorted(state_returns.items(), key=lambda x: x[1])
    labels = {sorted_s[0][0]: "DOWNTREND", sorted_s[-1][0]: "UPTREND"}
    if n_states == 3:
        labels[sorted_s[1][0]] = "RANGE"
    else:
        mids = sorted(sorted_s[1:-1], key=lambda x: abs(x[1]))
        labels[mids[0][0]] = "RANGE"
        for i, (sid, _) in enumerate(mids[1:], 1):
            labels[sid] = f"MID{i}"
    return labels


def evaluate_one(feats_sub, returns, n_states, seed):
    X = StandardScaler().fit_transform(feats_sub.values)  # 評価用：採択時は別途再構成
    model = GaussianHMM(n_components=n_states, covariance_type="full", n_iter=200, tol=1e-4, random_state=seed)
    model.fit(X)
    states = model.predict(X)
    state_returns = {int(s): float(np.mean(returns[states == s])) for s in range(n_states) if (states == s).any()}
    if len(state_returns) < n_states:
        return None
    labels = label_states(state_returns, n_states)
    durations = state_durations(states)
    overall_mean = float(np.mean(returns))
    summary = {}
    for s in range(n_states):
        mask = states == s
        if not mask.any():
            continue
        sret = returns[mask]
        t_stat, p_val = stats.ttest_1samp(sret, overall_mean)
        durs = durations.get(s, [])
        summary[labels[s]] = {
            "state_id": int(s),
            "n_days": int(mask.sum()),
            "ret_mean_pct": round(float(np.mean(sret)), 4),
            "ret_median_pct": round(float(np.median(sret)), 4),
            "p_value": round(float(p_val), 6),
            "duration_median_days": float(np.median(durs)) if durs else None,
            "duration_mean_days": round(float(np.mean(durs)), 2) if durs else None,
        }
    pc = {}
    if "UPTREND" in summary:
        u = summary["UPTREND"]
        pc["UPTREND_ret"] = u["ret_mean_pct"] > CRITERIA_B["uptrend_min"]
        pc["UPTREND_duration"] = u["duration_median_days"] is not None and CRITERIA_B["duration_min"] <= u["duration_median_days"] <= CRITERIA_B["duration_max"]
        pc["UPTREND_pvalue"] = u["p_value"] < CRITERIA_B["p_value_max"]
    if "DOWNTREND" in summary:
        d = summary["DOWNTREND"]
        pc["DOWNTREND_ret"] = d["ret_mean_pct"] < CRITERIA_B["downtrend_max"]
        pc["DOWNTREND_duration"] = d["duration_median_days"] is not None and CRITERIA_B["duration_min"] <= d["duration_median_days"] <= CRITERIA_B["duration_max"]
        pc["DOWNTREND_pvalue"] = d["p_value"] < CRITERIA_B["p_value_max"]
    if "RANGE" in summary:
        r = summary["RANGE"]
        pc["RANGE_ret"] = abs(r["ret_mean_pct"]) < CRITERIA_B["range_max_abs"]
        pc["RANGE_duration"] = r["duration_median_days"] is not None and CRITERIA_B["duration_min"] <= r["duration_median_days"] <= CRITERIA_B["duration_max"]
    all_pass = all(pc.values()) if pc else False
    margin = (
        (summary["UPTREND"]["ret_mean_pct"] - CRITERIA_B["uptrend_min"])
        + (CRITERIA_B["downtrend_max"] - summary["DOWNTREND"]["ret_mean_pct"])
        if "UPTREND" in summary and "DOWNTREND" in summary
        else 0
    )
    return {
        "all_passed": all_pass,
        "logL": float(model.score(X)),
        "margin": float(margin),
        "summary": summary,
        "pass_check": pc,
        "labels": labels,
        "states": states,
    }


def main():
    feats, rets = load_data()
    rets_arr = rets.values
    print(f"[finalize] データ: {len(feats)}日 / {feats.index.min().date()} 〜 {feats.index.max().date()}")
    print(f"[finalize] 候補構成 × seed {N_SEEDS} = {len(CANDIDATES) * N_SEEDS} 試行")

    seeds = list(range(N_SEEDS))
    all_results = []
    for cand in CANDIDATES:
        feats_sub = feats.drop(columns=cand["drop_features"])
        n_pass = 0
        for seed in seeds:
            r = evaluate_one(feats_sub, rets_arr, cand["n_states"], seed)
            if r is None:
                continue
            r["candidate_label"] = cand["label"]
            r["n_states"] = cand["n_states"]
            r["drop_features"] = cand["drop_features"]
            r["seed"] = seed
            r["features_used"] = list(feats_sub.columns)
            all_results.append(r)
            if r["all_passed"]:
                n_pass += 1
        print(f"  {cand['label']}: 合格 {n_pass}/{N_SEEDS} ({100*n_pass/N_SEEDS:.1f}%)")

    passers = [r for r in all_results if r["all_passed"]]
    print(f"\n[finalize] 合格構成総数: {len(passers)} / {len(all_results)}")
    if not passers:
        print("  ❌ 合格構成ゼロ。段階2移行が必要")
        return

    # 採択: 候補B合格 → margin最大 → logL最大
    passers.sort(key=lambda r: (-r["margin"], -r["logL"]))
    best = passers[0]
    print(f"\n========== 採択構成 ==========")
    print(f"  config={best['candidate_label']} seed={best['seed']}")
    print(f"  margin={best['margin']:.4f}  logL={best['logL']:.2f}")
    print(f"  features({len(best['features_used'])}本): {best['features_used']}")
    print(f"\n  状態別サマリ:")
    for label, s in best["summary"].items():
        print(
            f"    {label:10s} n={s['n_days']:4d}  ret_mean={s['ret_mean_pct']:+7.4f}%  "
            f"median={s['ret_median_pct']:+7.4f}%  dur_med={s['duration_median_days']}  p={s['p_value']}"
        )

    # 採択構成の上位5を表示（ロバスト確認）
    print(f"\n========== 合格構成 上位5（採択候補比較） ==========")
    for rank, r in enumerate(passers[:5], 1):
        ss = r["summary"]
        print(
            f"  #{rank} {r['candidate_label']} seed={r['seed']:3d}  "
            f"margin={r['margin']:.3f}  logL={r['logL']:.1f}  "
            f"UP={ss['UPTREND']['ret_mean_pct']:+.3f}% DOWN={ss['DOWNTREND']['ret_mean_pct']:+.3f}%"
        )

    # 採択構成を fit し直して pickle 凍結
    feats_sub = feats.drop(columns=best["drop_features"])
    scaler = StandardScaler().fit(feats_sub.values)
    X = scaler.transform(feats_sub.values)
    final_model = GaussianHMM(
        n_components=best["n_states"],
        covariance_type="full",
        n_iter=200,
        tol=1e-4,
        random_state=best["seed"],
    )
    final_model.fit(X)
    final_states = final_model.predict(X)

    # 再現性確認
    final_state_returns = {int(s): float(np.mean(rets_arr[final_states == s])) for s in range(best["n_states"]) if (final_states == s).any()}
    final_labels = label_states(final_state_returns, best["n_states"])

    # 採択時の states と一致確認（label別の日数で同等性確認）
    orig_label_seq = [best["labels"][s] for s in best["states"]]
    new_label_seq = [final_labels[s] for s in final_states]
    match_pct = float(np.mean(np.array(orig_label_seq) == np.array(new_label_seq)) * 100)
    print(f"\n  再現性確認: 採択時とのラベル一致率 = {match_pct:.2f}%")
    if match_pct < 100.0:
        print(f"    ⚠️ 警告: 完全一致しない（{100 - match_pct:.2f}%差異）")

    # pickle 保存
    bundle = {
        "model": final_model,
        "scaler": scaler,
        "labels": {int(k): v for k, v in final_labels.items()},
        "config": {
            "n_states": best["n_states"],
            "drop_features": best["drop_features"],
            "features_used": best["features_used"],
            "random_state": best["seed"],
            "covariance_type": "full",
        },
        "criteria_B": CRITERIA_B,
        "data_period": {
            "start": str(feats.index.min().date()),
            "end": str(feats.index.max().date()),
            "n_days": len(feats),
        },
    }
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)
    print(f"\n  → {MODEL_PATH}")

    # 状態CSV
    out_df = pd.DataFrame({
        "date": feats.index,
        "state_id": final_states,
        "state_label": new_label_seq,
        "daily_return_pct": rets_arr,
    })
    out_df.to_csv(STATES_CSV, index=False)
    print(f"  → {STATES_CSV.name} ({len(out_df)}行)")

    # サマリ JSON
    summary = {
        "adopted_config": {
            "candidate_label": best["candidate_label"],
            "n_states": best["n_states"],
            "drop_features": best["drop_features"],
            "random_state": best["seed"],
            "features_used": best["features_used"],
        },
        "metrics": {
            "logL": round(best["logL"], 4),
            "margin": round(best["margin"], 4),
            "reproducibility_pct": round(match_pct, 2),
        },
        "state_summary": {k: v for k, v in best["summary"].items()},
        "pass_check": best["pass_check"],
        "search_stats": {
            "n_combinations_tried": len(all_results),
            "n_passed": len(passers),
            "pass_rate_pct": round(100 * len(passers) / len(all_results), 2),
        },
        "criteria_B": CRITERIA_B,
        "label_id_map": {str(k): v for k, v in final_labels.items()},
    }
    with open(SUMMARY_JSON, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  → {SUMMARY_JSON.name}")

    # pickle reload テスト
    print(f"\n[finalize] pickle reload テスト...")
    with open(MODEL_PATH, "rb") as f:
        loaded = pickle.load(f)
    X_test = loaded["scaler"].transform(feats_sub.values)
    test_states = loaded["model"].predict(X_test)
    if (test_states == final_states).all():
        print(f"  ✅ 完全一致（pickle reload で同じ予測）")
    else:
        diff = int((test_states != final_states).sum())
        print(f"  ❌ {diff}箇所差異！要調査")


if __name__ == "__main__":
    main()
