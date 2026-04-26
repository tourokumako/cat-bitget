"""Phase 2 安定性検証: 推奨構成（n=6 / drop_ret_skew_30d / cov=full）を seed 20通りで検証

入力: results/phase1_features_daily.csv, data/BTCUSDT-...5y.csv
出力: results/phase2_hmm_stability.json

合格率・各seedの主要指標・状態シーケンス類似度を測定。
"""
from __future__ import annotations

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
OUT_PATH = REPO_ROOT / "results" / "phase2_hmm_stability_n7_dropma50.json"

CRITERIA_B = {
    "uptrend_min": 1.2212616859789105,
    "downtrend_max": -0.8215951246819279,
    "range_max_abs": 0.3404761351101398,
    "duration_min": 3,
    "duration_max": 30,
    "p_value_max": 0.05,
}

CONFIG = {
    "n_states": 7,
    "covariance_type": "full",
    "drop_features": ["ma50_dev"],
}
SEEDS = [0, 1, 7, 13, 42, 99, 100, 123, 256, 512, 999, 1024, 2024, 2025, 2026, 3000, 5000, 7777, 9999, 31337]


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


def evaluate_one(feats_sub, returns, seed):
    X = StandardScaler().fit_transform(feats_sub.values)
    model = GaussianHMM(
        n_components=CONFIG["n_states"],
        covariance_type=CONFIG["covariance_type"],
        n_iter=200,
        tol=1e-4,
        random_state=seed,
    )
    model.fit(X)
    states = model.predict(X)
    n = CONFIG["n_states"]
    state_returns = {int(s): float(np.mean(returns[states == s])) for s in range(n) if (states == s).any()}
    if len(state_returns) < n:
        return {"degenerate": True, "seed": seed}
    labels = label_states(state_returns, n)
    durations = state_durations(states)
    overall_mean = float(np.mean(returns))
    summary = {}
    for s in range(n):
        mask = states == s
        if not mask.any():
            continue
        sret = returns[mask]
        t_stat, p_val = stats.ttest_1samp(sret, overall_mean)
        durs = durations.get(s, [])
        summary[labels[s]] = {
            "n_days": int(mask.sum()),
            "ret_mean_pct": round(float(np.mean(sret)), 4),
            "p_value": round(float(p_val), 6),
            "duration_median_days": float(np.median(durs)) if durs else None,
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
    return {
        "seed": seed,
        "all_passed": all(pc.values()),
        "n_passed": sum(pc.values()),
        "n_total": len(pc),
        "logL": round(float(model.score(X)), 4),
        "converged": bool(model.monitor_.converged),
        "summary": summary,
        "pass_check": pc,
        "states_array": [int(s) for s in states],
        "labels": {str(k): v for k, v in labels.items()},
    }


def state_label_sequence(result):
    labels = {int(k): v for k, v in result["labels"].items()}
    return [labels[s] for s in result["states_array"]]


def jaccard_label(seq_a, seq_b, label):
    a = np.array(seq_a) == label
    b = np.array(seq_b) == label
    inter = int((a & b).sum())
    union = int((a | b).sum())
    return round(inter / union, 4) if union > 0 else 0.0


def main():
    print(f"[stability] config: n={CONFIG['n_states']} cov={CONFIG['covariance_type']} drop={CONFIG['drop_features']}")
    feats, rets = load_data()
    feats_sub = feats.drop(columns=CONFIG["drop_features"])
    print(f"  特徴量: {list(feats_sub.columns)} ({feats_sub.shape[1]}本)")
    print(f"  期間: {feats.index.min().date()} 〜 {feats.index.max().date()} ({len(feats)}日)")

    results = []
    for seed in SEEDS:
        try:
            r = evaluate_one(feats_sub, rets.values, seed)
            results.append(r)
            if r.get("degenerate"):
                print(f"  seed={seed:5d} → degenerate")
            else:
                print(f"  seed={seed:5d} {'✅' if r['all_passed'] else '❌'} {r['n_passed']}/{r['n_total']}  logL={r['logL']}")
        except Exception as e:
            print(f"  seed={seed} ERROR: {e}")

    valid = [r for r in results if not r.get("degenerate")]
    passed = [r for r in valid if r["all_passed"]]
    print(f"\n========== 安定性サマリ ==========")
    print(f"  合格: {len(passed)} / {len(valid)} ({100 * len(passed) / len(valid):.1f}%)")

    # ラベル一致度（合格構成同士）
    if len(passed) >= 2:
        seqs = [state_label_sequence(r) for r in passed]
        ups = [jaccard_label(seqs[0], s, "UPTREND") for s in seqs[1:]]
        dns = [jaccard_label(seqs[0], s, "DOWNTREND") for s in seqs[1:]]
        rgs = [jaccard_label(seqs[0], s, "RANGE") for s in seqs[1:]]
        print(f"  ラベル一致度（先頭合格構成 vs その他合格構成・Jaccard）:")
        print(f"    UPTREND   平均={np.mean(ups):.3f}  範囲={np.min(ups):.3f}〜{np.max(ups):.3f}")
        print(f"    DOWNTREND 平均={np.mean(dns):.3f}  範囲={np.min(dns):.3f}〜{np.max(dns):.3f}")
        print(f"    RANGE     平均={np.mean(rgs):.3f}  範囲={np.min(rgs):.3f}〜{np.max(rgs):.3f}")

    # 合格構成の指標分布
    if passed:
        up_rets = [r["summary"]["UPTREND"]["ret_mean_pct"] for r in passed]
        dn_rets = [r["summary"]["DOWNTREND"]["ret_mean_pct"] for r in passed]
        rg_rets = [r["summary"]["RANGE"]["ret_mean_pct"] for r in passed]
        print(f"\n  合格構成の主要指標:")
        print(f"    UP   ret: 平均{np.mean(up_rets):+.4f}%  範囲{min(up_rets):+.4f}〜{max(up_rets):+.4f}")
        print(f"    DOWN ret: 平均{np.mean(dn_rets):+.4f}%  範囲{min(dn_rets):+.4f}〜{max(dn_rets):+.4f}")
        print(f"    RANGE ret: 平均{np.mean(rg_rets):+.4f}%  範囲{min(rg_rets):+.4f}〜{max(rg_rets):+.4f}")

    out = {
        "config": CONFIG,
        "n_seeds": len(SEEDS),
        "n_passed": len(passed),
        "pass_rate_pct": round(100 * len(passed) / len(valid), 2) if valid else 0,
        "per_seed": [
            {k: v for k, v in r.items() if k != "states_array"}
            for r in results
        ],
    }
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n  → {OUT_PATH.name}")


if __name__ == "__main__":
    main()
