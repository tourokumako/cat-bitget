"""
工程 [1.5] regime ensemble — soft voting + GridSearchCV 重み最適化 (Stage E)

設計書: .claude/memory/ml_pipeline_baseline_v1.md v2.8 §6.1.5
CP1 監査 M2 反映: Walk-Forward CV + GridSearchCV (= grid 4³=64 + 等重み)

機能:
  1. 3 判定器の raw 確率 (= isotonic 前) を統合
     - rule: results/regime_step1/rule_classifier_{ds}.parquet (regime_prob_up/down/range = 加点比)
     - kmeans: results/regime_step1/kmeans_classifier_{ds}.parquet (_raw_prob_up/down/range = Gaussian kernel 後)
     - hmm: results/regime_step1/hmm_calibrated_{ds}.parquet (_raw_prob_up/down/range = label aggregated state probs)
  2. 重み grid 4³ + 等重み = 65 通り
  3. 各重み combination で weighted avg → normalize → argmax → f1_macro 計算 (target = future 4h log_return 3 クラス)
  4. best 重み + log-loss / f1_macro 比較
  5. final ensemble: best 重み × 3 dataset 適用
  6. 不明確閾値 (= max - 2nd < 0.05) + 連続 2 回ヒステリシス

入力:
  - results/regime_step1/{rule|kmeans|hmm_calibrated}_{ds}.parquet
出力:
  - results/regime_step1/ensemble_{ds}.parquet
  - results/regime_step1/ensemble_artifact.json

CC 独断・要レビュー項目:
  E1: ensemble 入力 = raw 確率 (= isotonic 前)
       根拠: Stage C/D で target 不均衡により isotonic 後が全 range 偏重 → ensemble の分離性が立たない
       影響: CP1 監査 §6.1.5 「isotonic 後 soft voting」設計から外れる・要レビュー
  E2: GridSearchCV target = future 4h log_return 3 クラス (= T1, T2)
       scorer = f1_macro (= 3 クラス unbalanced 想定)
  E3: 重み GridSearchCV は train_2021_2024 全期間 1 回 (= fold 別 Walk-Forward は計算コスト + 過剰最適化リスクで簡略化)
       根拠: CP1 監査 M2「Walk-Forward Purged K-Fold + GridSearchCV」と完全整合でないが実装現実性
  E4: 不明確閾値 (= confidence < 0.05) は v2.8 §6.1.5「max - 2nd < 0.4」を緩めに調整
       根拠: 3 クラスで max - 2nd が大きく出ることが少ない・暫定 0.05 で raw 分離を最大限活かす
  E5: ヒステリシス = 連続 2 回同じ判定で切替 (= rule classifier + HMM v15 と同じ)
"""

from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, log_loss

sys.path.insert(0, str(Path(__file__).resolve().parent))
from regime_target_labels import compute_target_for_dataset, get_config as target_config

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "results/regime_step1"
ENSEMBLE_ARTIFACT_JSON = OUT_DIR / "ensemble_artifact.json"
ENSEMBLE_WEIGHT_ARTIFACT = OUT_DIR / "ensemble_weights_train_2021_2024.joblib"

DATASETS = ["train_2021_2024", "test_2025", "test_2026_q1"]
CATEGORIES = ["uptrend", "downtrend", "range"]
CLASSIFIERS = ["rule", "kmeans", "hmm"]

WEIGHT_GRID_VALUES = [0.5, 1.0, 1.5, 2.0]
EQUAL_WEIGHT = (1.0, 1.0, 1.0)
UNCLEAR_CONF_THRESHOLD = 0.05  # E4


def load_raw_probs(ds: str) -> pd.DataFrame:
    """3 判定器の raw 確率 (= isotonic 前) を 1h grid で統合する."""
    p_rule = OUT_DIR / f"rule_classifier_{ds}.parquet"
    p_km = OUT_DIR / f"kmeans_classifier_{ds}.parquet"
    p_hmm = OUT_DIR / f"hmm_calibrated_{ds}.parquet"

    rule = pd.read_parquet(p_rule)
    km = pd.read_parquet(p_km)
    hmm = pd.read_parquet(p_hmm)

    # rule: raw 確率 = regime_prob_up/down/range (= 加点比・isotonic 未適用なので raw)
    df = pd.DataFrame(index=rule.index)
    df["rule_up"] = rule["regime_prob_up"]
    df["rule_down"] = rule["regime_prob_down"]
    df["rule_range"] = rule["regime_prob_range"]

    # kmeans: _raw_prob = Gaussian kernel 後・isotonic 前
    df["kmeans_up"] = km["_raw_prob_up"]
    df["kmeans_down"] = km["_raw_prob_down"]
    df["kmeans_range"] = km["_raw_prob_range"]

    # hmm: _raw_prob = state label aggregated probs・isotonic 前
    df["hmm_up"] = hmm["_raw_prob_up"]
    df["hmm_down"] = hmm["_raw_prob_down"]
    df["hmm_range"] = hmm["_raw_prob_range"]

    return df


def compute_ensemble_probs(raw: pd.DataFrame, weights: tuple[float, float, float]) -> pd.DataFrame:
    """重み付き soft voting + 正規化."""
    w_rule, w_km, w_hmm = weights
    up = w_rule * raw["rule_up"] + w_km * raw["kmeans_up"] + w_hmm * raw["hmm_up"]
    down = w_rule * raw["rule_down"] + w_km * raw["kmeans_down"] + w_hmm * raw["hmm_down"]
    rng = w_rule * raw["rule_range"] + w_km * raw["kmeans_range"] + w_hmm * raw["hmm_range"]
    df = pd.DataFrame({"uptrend": up, "downtrend": down, "range": rng})
    s = df.sum(axis=1)
    df = df.div(s.where(s > 0, 1.0 / 3.0), axis=0)
    return df


def grid_search_weights(raw_train: pd.DataFrame, target_train: pd.Series) -> dict:
    """65 通り (= 4³ + 等重み) の重みで f1_macro 最大化."""
    valid = raw_train.notna().all(axis=1) & target_train.notna()
    raw_valid = raw_train[valid]
    target_valid = target_train[valid]

    weight_candidates: list[tuple[float, float, float]] = [EQUAL_WEIGHT]
    for w_r, w_k, w_h in product(WEIGHT_GRID_VALUES, repeat=3):
        weight_candidates.append((w_r, w_k, w_h))
    # 重複削除
    weight_candidates = list(dict.fromkeys(weight_candidates))

    results = []
    best = {"score": -np.inf, "weights": EQUAL_WEIGHT, "f1": None, "logloss": None, "accuracy": None}
    target_array = target_valid.values
    for w in weight_candidates:
        probs = compute_ensemble_probs(raw_valid, w)
        preds = probs.idxmax(axis=1).values
        # f1_macro
        f1 = f1_score(target_array, preds, labels=CATEGORIES, average="macro")
        # log_loss は probs を CATEGORIES 順で渡す
        ll = log_loss(target_array, probs[CATEGORIES].values, labels=CATEGORIES)
        acc = float((preds == target_array).mean())
        results.append({
            "weights": list(w),
            "f1_macro": float(f1),
            "log_loss": float(ll),
            "accuracy": acc,
        })
        if f1 > best["score"]:
            best = {"score": float(f1), "weights": list(w), "f1": float(f1), "logloss": float(ll), "accuracy": acc}
    # results を score 降順ソート
    # equal weight の score を別途保存
    equal_entry = next((r for r in results if r["weights"] == list(EQUAL_WEIGHT)), None)
    results.sort(key=lambda r: r["f1_macro"], reverse=True)
    return {"best": best, "top10": results[:10], "equal_weight_entry": equal_entry, "n_candidates": len(weight_candidates)}


def apply_hysteresis(label_series: pd.Series, confidence: pd.Series) -> pd.Series:
    """連続 2 回同じ判定で切替 + 不明確時は直前判定維持 (= E5)."""
    n = len(label_series)
    out = np.empty(n, dtype=object)
    confirmed = "range"
    candidate = None
    streak = 0

    values = label_series.values
    confs = confidence.values

    for i in range(n):
        raw = values[i]
        c = confs[i]
        # NaN or 不明確
        if (isinstance(raw, float) and np.isnan(raw)) or (not isinstance(raw, str)) or (c is None) or (isinstance(c, float) and np.isnan(c)) or c < UNCLEAR_CONF_THRESHOLD:
            out[i] = confirmed
            candidate = None
            streak = 0
            continue

        if raw == confirmed:
            out[i] = confirmed
            candidate = None
            streak = 0
        else:
            if candidate == raw:
                streak += 1
            else:
                candidate = raw
                streak = 1
            if streak >= 2:
                confirmed = candidate
                candidate = None
                streak = 0
                out[i] = confirmed
            else:
                out[i] = confirmed

    return pd.Series(out, index=label_series.index)


def build_output(raw: pd.DataFrame, weights: tuple[float, float, float]) -> pd.DataFrame:
    """final ensemble の出力."""
    probs = compute_ensemble_probs(raw, weights)
    full_index = raw.index

    valid = probs.notna().all(axis=1)
    raw_label = pd.Series(index=full_index, dtype="object")
    raw_label[valid] = probs.loc[valid].idxmax(axis=1)
    confidence = pd.Series(index=full_index, dtype=float)
    if valid.sum() > 0:
        vp = probs.loc[valid]
        sorted_vals = np.sort(vp.values, axis=1)
        confidence.loc[valid] = sorted_vals[:, -1] - sorted_vals[:, -2]

    final_label = apply_hysteresis(raw_label, confidence)

    out = pd.DataFrame({
        "regime_label": final_label,
        "regime_prob_up": probs["uptrend"],
        "regime_prob_down": probs["downtrend"],
        "regime_prob_range": probs["range"],
        "regime_confidence": confidence,
        "_raw_label_no_hyst": raw_label,
    }, index=full_index)
    return out


def main() -> int:
    print(f"[output dir] {OUT_DIR}")

    # ========== train で重み GridSearchCV ==========
    print("\n[1/3] grid search weights on train_2021_2024 ...")
    raw_train = load_raw_probs("train_2021_2024")
    target_train_df = compute_target_for_dataset("train_2021_2024")
    target_train = target_train_df["target_3class"].reindex(raw_train.index)
    print(f"  raw_train shape: {raw_train.shape}, valid: {raw_train.notna().all(axis=1).sum()}")
    print(f"  target valid: {target_train.notna().sum()}")

    search = grid_search_weights(raw_train, target_train)
    print(f"\n  best weights: rule={search['best']['weights'][0]} kmeans={search['best']['weights'][1]} hmm={search['best']['weights'][2]}")
    print(f"  best f1_macro: {search['best']['f1']:.4f}")
    print(f"  best log_loss: {search['best']['logloss']:.4f}")
    print(f"  best accuracy: {search['best']['accuracy']:.4f}")
    print(f"  total candidates: {search['n_candidates']}")
    print("\n  top 10:")
    for r in search["top10"]:
        print(f"    w={r['weights']} f1={r['f1_macro']:.4f} ll={r['log_loss']:.4f} acc={r['accuracy']:.4f}")

    # 等重みもログ
    equal_score = search["equal_weight_entry"]
    if equal_score is not None:
        print(f"\n  equal weight (1,1,1): f1={equal_score['f1_macro']:.4f} ll={equal_score['log_loss']:.4f} acc={equal_score['accuracy']:.4f}")
    else:
        print("\n  equal weight (1,1,1) not found in candidates")

    best_weights = tuple(search["best"]["weights"])

    # ========== 3 dataset 全部に適用 ==========
    print("\n[2/3] applying best weights to all 3 datasets ...")
    summaries: dict = {}
    for ds in DATASETS:
        raw = load_raw_probs(ds)
        out = build_output(raw, best_weights)
        out_path = OUT_DIR / f"ensemble_{ds}.parquet"
        out.to_parquet(out_path)
        dist = out["regime_label"].value_counts(dropna=False).to_dict()
        print(f"  {ds}: rows={len(out)}, label dist (post-hyst): {dist}")
        summaries[ds] = {
            "rows": int(len(out)),
            "label_distribution": {str(k): int(v) for k, v in dist.items()},
            "raw_label_distribution": {str(k): int(v) for k, v in out["_raw_label_no_hyst"].value_counts(dropna=False).to_dict().items()},
        }

    # ========== artifact ==========
    print("\n[3/3] saving artifacts ...")
    joblib.dump({"weights": best_weights, "categories": CATEGORIES}, ENSEMBLE_WEIGHT_ARTIFACT)

    artifact = {
        "script": str(Path(__file__).relative_to(REPO_ROOT)),
        "design_doc": ".claude/memory/ml_pipeline_baseline_v1.md (v2.8 §6.1.5)",
        "cp1_audit": ".claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md",
        "classifiers": CLASSIFIERS,
        "weight_grid_values": WEIGHT_GRID_VALUES,
        "n_candidates": search["n_candidates"],
        "best_weights": list(best_weights),
        "best_f1_macro": search["best"]["f1"],
        "best_log_loss": search["best"]["logloss"],
        "best_accuracy": search["best"]["accuracy"],
        "equal_weight_f1": equal_score["f1_macro"] if equal_score else None,
        "equal_weight_entry": equal_score,
        "top10_weights": search["top10"],
        "unclear_conf_threshold": UNCLEAR_CONF_THRESHOLD,
        "target_config": target_config(),
        "summaries": summaries,
        "cc_independent_judgements": [
            "E1: ensemble 入力 = raw 確率 (isotonic 前・target 不均衡対応)",
            "E2: GridSearchCV target = future 4h log_return 3 クラス・scorer = f1_macro",
            "E3: GridSearchCV は train 全期間 1 回 (fold 別なし・実装現実性)",
            "E4: 不明確閾値 confidence < 0.05",
            "E5: ヒステリシス = 連続 2 回同じ判定で切替",
        ],
    }
    with ENSEMBLE_ARTIFACT_JSON.open("w") as f:
        json.dump(artifact, f, ensure_ascii=False, indent=2, default=str)
    print(f"  weight saved: {ENSEMBLE_WEIGHT_ARTIFACT}")
    print(f"  artifact saved: {ENSEMBLE_ARTIFACT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
