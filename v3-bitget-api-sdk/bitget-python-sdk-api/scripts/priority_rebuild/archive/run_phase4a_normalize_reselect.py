"""
Phase 4-a 入力正規化 + k 再選定 (監査#5 全 16 件反映)

指示書: .claude/instructions/2026-05-14_phase4a_normalize_reselect.md
phase_compliance §4a 準拠 (4a.1〜4a.5)

Steps:
  1. 16 予測値を close で正規化 (% 換算) + sanity (close > 0 / null / inf)
  2. k=2〜6 で stability + centroid_drift + within_cluster_std_diff
  2-B. random_state {0,1,100} で robustness 確認
  2-C. random_state=42 で 2 回 fit → bit-exact 確認 (k=2〜6 全件)
  3. 正規化前後の stability 比較 + 危険水域判定
  4. 分岐 A (≤20pp が出た) / B (全 k で >20pp) 判定
  5. 分岐 A: Step 5-A〜F 詳細検証
     分岐 B: 3 選択肢の評価レポート

注:
  指示書 Step 1 の `pred_cols = startswith('pred_')` は実データの列名と不一致 (空リスト)。
  Phase 4-a と同じ LABEL_COLS 定義 (16 列) を使用 (L-180 doc-vs-impl 整合性修正)。
  test 予測パスも指示書記載の ml_phase1/ ではなく ml_phase1_k12long_refit/ が正。
"""

import hashlib
import json
import warnings
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "results" / "priority_rebuild"
REFIT_DIR = DATA_DIR / "ml_phase1_k12long_refit"
OUT_DIR = DATA_DIR / "ml_phase4_a_norm"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_PRED_PATH = REFIT_DIR / "predictions_train_2021_2024_k12long_refit.parquet"
TEST_PRED_PATH = REFIT_DIR / "predictions_test2025_k12long_refit.parquet"
LABELS_TRAIN = DATA_DIR / "labels_mfe_mae_train_2021_2024.parquet"
LABELS_TEST = DATA_DIR / "labels_mfe_mae_test_2025.parquet"

LABEL_COLS = [
    f"{side}_{kind}_K{k}"
    for k in (12, 24, 48, 96)
    for side in ("LONG", "SHORT")
    for kind in ("MFE", "MAE")
]
assert len(LABEL_COLS) == 16
PCT_COLS = [c + "_pct" for c in LABEL_COLS]

RANDOM_STATE = 42
SILHOUETTE_SAMPLE = 20000
K_RANGE = (2, 3, 4, 5, 6)
ROBUSTNESS_SEEDS = (0, 1, 100)

# Phase 4-a 完了報告 + k=2 vs k=3 完了報告から引用した正規化前の値 (比較用)
PRE_NORM_STABILITY = {
    2: {"share_max_diff_pp": 35.49, "share_sum_diff_pp": 70.98, "silhouette": 0.5075},
    3: {"share_max_diff_pp": 44.18, "share_sum_diff_pp": 88.35, "silhouette": 0.5100},
}


def log(msg, fp=None):
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    if fp:
        fp.write(line + "\n")
        fp.flush()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """16 予測値を close で割って % 換算した DataFrame を返す."""
    assert "close" in df.columns
    assert (df["close"] > 0).all(), "close <= 0 detected"
    out = df[["close"]].copy()
    for c in LABEL_COLS:
        out[c + "_pct"] = df[c] / df["close"] * 100.0
    # null / inf チェック
    assert not out[PCT_COLS].isna().any().any(), "null in normalized"
    assert not np.isinf(out[PCT_COLS].values).any(), "inf in normalized"
    return out


def stability(train_sh: dict, test_sh: dict) -> dict:
    clusters = sorted(set(train_sh.keys()) | set(test_sh.keys()))
    diffs = [abs(train_sh.get(c, 0.0) - test_sh.get(c, 0.0)) for c in clusters]
    return {"max_diff_pp": max(diffs) * 100, "sum_diff_pp": sum(diffs) * 100}


def cluster_centroid_drift(km, X_test_scaled, test_labels) -> tuple[float, dict]:
    """train 由来 centroid (km.cluster_centers_) と
    test に同 cluster 割り当てされたサンプルの mean centroid の Euclidean drift / ‖train‖."""
    drifts = {}
    for c in range(km.n_clusters):
        train_c = km.cluster_centers_[c]
        mask = test_labels == c
        if mask.sum() == 0:
            drifts[c] = float("nan")
            continue
        test_c = X_test_scaled[mask].mean(axis=0)
        norm_train = np.linalg.norm(train_c)
        if norm_train < 1e-9:
            drifts[c] = float("nan")
            continue
        drifts[c] = float(np.linalg.norm(train_c - test_c) / norm_train)
    valid_vals = [v for v in drifts.values() if not np.isnan(v)]
    mean_drift = float(np.mean(valid_vals)) if valid_vals else float("nan")
    return mean_drift, drifts


def within_cluster_std_diff(X_train, train_labels, X_test, test_labels, k) -> float:
    """各 cluster c で std_train_c (16-dim vector) と std_test_c の L2 距離 / ‖std_train‖ を平均."""
    diffs = []
    for c in range(k):
        m_tr = train_labels == c
        m_te = test_labels == c
        if m_tr.sum() < 2 or m_te.sum() < 2:
            continue
        std_tr = X_train[m_tr].std(axis=0)
        std_te = X_test[m_te].std(axis=0)
        norm = np.linalg.norm(std_tr)
        if norm < 1e-9:
            continue
        diffs.append(np.linalg.norm(std_te - std_tr) / norm)
    return float(np.mean(diffs)) if diffs else float("nan")


def robustness_check(X_scaled, k, seeds) -> dict:
    """seeds 全てで fit → cluster サイズ分布が安定か判定 (sorted sizes の相関)."""
    sorted_sizes_per_seed = {}
    for s in seeds:
        km = KMeans(n_clusters=k, random_state=s, n_init=10)
        labels = km.fit_predict(X_scaled)
        sizes = sorted(pd.Series(labels).value_counts().tolist(), reverse=True)
        sorted_sizes_per_seed[s] = sizes
    # 比較: 全 seed の sorted_sizes の最大シェアの std / mean
    max_shares = [sizes[0] / sum(sizes) for sizes in sorted_sizes_per_seed.values()]
    rel_std = float(np.std(max_shares) / np.mean(max_shares)) if max_shares else float("nan")
    return {"sorted_sizes_per_seed": sorted_sizes_per_seed, "rel_std_max_share": rel_std}


def main():
    t0 = datetime.now()
    TS = t0.strftime("%Y%m%dT%H%M%SZ")
    LOG_PATH = OUT_DIR / f"normalize_reselect_log_{TS}.txt"

    with open(LOG_PATH, "w") as logf:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            log(f"START at {t0.isoformat()}", logf)
            log(f"output: {OUT_DIR}", logf)

            # 物理証跡 1
            train_sha = sha256_file(TRAIN_PRED_PATH)
            test_sha = sha256_file(TEST_PRED_PATH)
            log(f"  train pred sha256: {train_sha[:12]}", logf)
            log(f"  test  pred sha256: {test_sha[:12]}", logf)

            # ====== Step 1: 入力正規化 ======
            log("Step 1: 入力正規化 (16 予測値 / close × 100) ...", logf)
            df_train_raw = pd.read_parquet(TRAIN_PRED_PATH).sort_index()
            df_test_raw = pd.read_parquet(TEST_PRED_PATH).sort_index()
            log(f"  train raw: rows={len(df_train_raw)}", logf)
            log(f"  test  raw: rows={len(df_test_raw)}", logf)
            assert len(df_train_raw) == 394753
            assert len(df_test_raw) == 105120

            df_train_norm = normalize(df_train_raw)
            df_test_norm = normalize(df_test_raw)

            # sanity
            log(f"  train normalized: rows={len(df_train_norm)} cols={len(df_train_norm.columns)}", logf)
            log(f"  test  normalized: rows={len(df_test_norm)} cols={len(df_test_norm.columns)}", logf)
            log(f"  train pct value range: min={df_train_norm[PCT_COLS].values.min():.4f}, "
                f"max={df_train_norm[PCT_COLS].values.max():.4f}", logf)
            log(f"  test  pct value range: min={df_test_norm[PCT_COLS].values.min():.4f}, "
                f"max={df_test_norm[PCT_COLS].values.max():.4f}", logf)

            train_norm_path = OUT_DIR / "predictions_train_normalized.parquet"
            test_norm_path = OUT_DIR / "predictions_test2025_normalized.parquet"
            df_train_norm.to_parquet(train_norm_path)
            df_test_norm.to_parquet(test_norm_path)
            log(f"  saved {train_norm_path.name} ({train_norm_path.stat().st_size} B)", logf)
            log(f"  saved {test_norm_path.name} ({test_norm_path.stat().st_size} B)", logf)

            X_train = df_train_norm[PCT_COLS].values
            X_test = df_test_norm[PCT_COLS].values

            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            log(f"  X_train_scaled shape: {X_train_scaled.shape}", logf)
            log(f"  X_test_scaled  shape: {X_test_scaled.shape}", logf)

            scaler_path = OUT_DIR / "scaler_train_2021_2024.joblib"
            assert "test" not in scaler_path.name.lower() and "train" in scaler_path.name.lower()
            joblib.dump(scaler, scaler_path)
            log(f"  saved {scaler_path.name}", logf)

            # ====== Step 2: k=2〜6 評価 ======
            log("Step 2: k=2〜6 評価 (stability/centroid_drift/within_std_diff) ...", logf)
            eval_rows = []
            km_per_k = {}
            train_labels_per_k = {}
            test_labels_per_k = {}

            for k in K_RANGE:
                log(f"  --- k={k} ---", logf)
                km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
                km.fit(X_train_scaled)
                tr_labels = km.labels_
                te_labels = km.predict(X_test_scaled)
                log(f"    fit: inertia={km.inertia_:.2f} n_iter={km.n_iter_}", logf)

                # silhouette (sampling)
                sil = silhouette_score(
                    X_train_scaled, tr_labels,
                    sample_size=SILHOUETTE_SAMPLE, random_state=RANDOM_STATE,
                )
                log(f"    silhouette: {sil:.4f}", logf)

                # share
                tr_sizes = pd.Series(tr_labels).value_counts().sort_index().to_dict()
                te_sizes = pd.Series(te_labels).value_counts().sort_index().to_dict()
                tr_share = {int(c): n / len(tr_labels) for c, n in tr_sizes.items()}
                te_share = {int(c): n / len(te_labels) for c, n in te_sizes.items()}
                stab = stability(tr_share, te_share)
                log(f"    train shares: {[(c, f'{s:.4f}') for c, s in tr_share.items()]}", logf)
                log(f"    test  shares: {[(c, f'{s:.4f}') for c, s in te_share.items()]}", logf)
                log(f"    stability: max_diff={stab['max_diff_pp']:.2f}pp sum_diff={stab['sum_diff_pp']:.2f}pp", logf)

                # centroid drift
                drift_mean, drift_per = cluster_centroid_drift(km, X_test_scaled, te_labels)
                log(f"    centroid_drift mean: {drift_mean:.4f}", logf)

                # within-cluster pred std diff (scaled 空間で)
                wsd = within_cluster_std_diff(X_train_scaled, tr_labels, X_test_scaled, te_labels, k)
                log(f"    within_cluster_std_diff mean: {wsd:.4f}", logf)

                # robustness (random_state {0,1,100})
                rob = robustness_check(X_train_scaled, k, ROBUSTNESS_SEEDS)
                log(f"    robustness rel_std(max_share) over seeds {ROBUSTNESS_SEEDS}: {rob['rel_std_max_share']:.4f}", logf)

                # bit-exact 再現性 (random_state=42 で 2 回目)
                km2 = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
                km2.fit(X_train_scaled)
                bit_exact = bool((tr_labels == km2.labels_).all())
                log(f"    bit-exact (random_state=42 2 回 fit): {bit_exact}", logf)
                assert bit_exact, f"bit-exact FAILED for k={k}"

                # save joblib
                km_path = OUT_DIR / f"kmeans_k{k}_train_2021_2024.joblib"
                assert "test" not in km_path.name.lower() and "train" in km_path.name.lower()
                joblib.dump(km, km_path)
                km_per_k[k] = km
                train_labels_per_k[k] = tr_labels
                test_labels_per_k[k] = te_labels

                # ====== Step 3 (per k): 正規化前後の比較 ======
                pre = PRE_NORM_STABILITY.get(k, {})
                pre_max = pre.get("share_max_diff_pp", None)
                improvement = (pre_max - stab["max_diff_pp"]) if pre_max is not None else None

                # 危険水域判定 (Step 3)
                if stab["max_diff_pp"] <= 10:
                    verdict = "✅ 安定 (≤ 10pp)"
                elif stab["max_diff_pp"] <= 20:
                    verdict = "⚠️ 要警戒 (10〜20pp)"
                else:
                    verdict = "❌ clustering 失敗水準 (> 20pp)"
                log(f"    verdict: {verdict}", logf)

                eval_rows.append({
                    "k": k,
                    "silhouette": round(sil, 4),
                    "inertia": round(km.inertia_, 2),
                    "n_iter": int(km.n_iter_),
                    "train_sizes": json.dumps(tr_sizes),
                    "test_sizes": json.dumps(te_sizes),
                    "share_max_diff_pp": round(stab["max_diff_pp"], 2),
                    "share_sum_diff_pp": round(stab["sum_diff_pp"], 2),
                    "centroid_drift_mean": round(drift_mean, 4),
                    "within_cluster_std_diff_mean": round(wsd, 4),
                    "robustness_rel_std_max_share": round(rob["rel_std_max_share"], 4),
                    "bit_exact_reproducibility": bit_exact,
                    "pre_norm_share_max_diff_pp": pre_max,
                    "improvement_pp": round(improvement, 2) if improvement is not None else None,
                    "verdict": verdict,
                })

            eval_df = pd.DataFrame(eval_rows)
            eval_csv = OUT_DIR / "k_evaluation_normalized.csv"
            eval_df.to_csv(eval_csv, index=False)
            log(f"  saved {eval_csv.name}", logf)

            # ====== Step 4: 分岐判定 ======
            log("Step 4: 分岐判定 ...", logf)
            passing = eval_df[eval_df["share_max_diff_pp"] <= 20]
            if not passing.empty:
                branch = "A"
                # silhouette 最大の k を採用候補
                chosen_k = int(passing.loc[passing["silhouette"].idxmax()]["k"])
                log(f"  → 分岐 A (share_max_diff ≤ 20pp の k あり)・採用候補 k={chosen_k}", logf)
            else:
                branch = "B"
                chosen_k = None
                log(f"  → 分岐 B (全 k で share_max_diff > 20pp・clustering 失敗水準)", logf)

            # ====== Step 5 (分岐 A) or 選択肢評価 (分岐 B) ======
            step5_results = {}
            if branch == "A":
                log(f"Step 5: 採用候補 k={chosen_k} 詳細検証 ...", logf)
                km = km_per_k[chosen_k]
                tr_labels = train_labels_per_k[chosen_k]
                te_labels = test_labels_per_k[chosen_k]

                # 5-A: train 前半/後半 split
                log("  Step 5-A: train 前半 (2021-2022) / 後半 (2023-2024) split", logf)
                ts_idx = df_train_norm.index
                half_idx = pd.Timestamp("2023-01-01")
                pre_mask = ts_idx < half_idx
                post_mask = ts_idx >= half_idx
                log(f"    前半 rows={int(pre_mask.sum())} 後半 rows={int(post_mask.sum())}", logf)

                scaler_split = StandardScaler()
                X_pre_scaled = scaler_split.fit_transform(X_train[pre_mask])
                X_post_scaled = scaler_split.transform(X_train[post_mask])
                km_split = KMeans(n_clusters=chosen_k, random_state=RANDOM_STATE, n_init=10)
                km_split.fit(X_pre_scaled)
                pre_labels = km_split.labels_
                post_labels = km_split.predict(X_post_scaled)
                pre_sh = pd.Series(pre_labels).value_counts(normalize=True).sort_index().to_dict()
                post_sh = pd.Series(post_labels).value_counts(normalize=True).sort_index().to_dict()
                stab_split = stability({int(c): v for c, v in pre_sh.items()},
                                       {int(c): v for c, v in post_sh.items()})
                log(f"    前半 shares: {pre_sh}", logf)
                log(f"    後半 shares: {post_sh}", logf)
                log(f"    split stability: max_diff={stab_split['max_diff_pp']:.2f}pp", logf)
                step5_results["split_max_diff_pp"] = stab_split["max_diff_pp"]

                # 5-B: cluster 移動 一致率
                log("  Step 5-B: q99 fire cluster 一致率", logf)
                bsection = []
                entry_kinds = [
                    ("K12_LONG_q99", "LONG_MFE_K12_pct", "LONG_MAE_K12_pct"),
                    ("K12_SHORT_q99", "SHORT_MFE_K12_pct", "SHORT_MAE_K12_pct"),
                    ("K96_LONG_q99", "LONG_MFE_K96_pct", "LONG_MAE_K96_pct"),
                    ("K96_SHORT_q99", "SHORT_MFE_K96_pct", "SHORT_MAE_K96_pct"),
                ]
                df_train_norm_clu = df_train_norm.copy()
                df_train_norm_clu["cluster"] = tr_labels
                df_test_norm_clu = df_test_norm.copy()
                df_test_norm_clu["cluster"] = te_labels
                for name, mfe_c, mae_c in entry_kinds:
                    ratio_tr = df_train_norm[mfe_c] / df_train_norm[mae_c].clip(lower=1e-9)
                    ratio_te = df_test_norm[mfe_c] / df_test_norm[mae_c].clip(lower=1e-9)
                    thr_tr = ratio_tr.quantile(0.99)
                    thr_te = ratio_te.quantile(0.99)
                    mask_tr = ratio_tr >= thr_tr
                    mask_te = ratio_te >= thr_te
                    tr_dist = df_train_norm_clu.loc[mask_tr, "cluster"].value_counts(normalize=True).sort_index()
                    te_dist = df_test_norm_clu.loc[mask_te, "cluster"].value_counts(normalize=True).sort_index()
                    dom_tr = int(tr_dist.idxmax())
                    dom_te = int(te_dist.idxmax())
                    # test 発火の何 % が train dominant cluster と同じか
                    in_dom_tr = float(te_dist.get(dom_tr, 0.0))
                    log(f"    {name}: train dom={dom_tr} ({tr_dist.max():.2f}) / "
                        f"test dom={dom_te} ({te_dist.max():.2f}) / "
                        f"test_in_train_dom={in_dom_tr:.2f}", logf)
                    bsection.append({
                        "entry": name,
                        "train_dom_cluster": dom_tr,
                        "train_dom_share": float(tr_dist.max()),
                        "test_dom_cluster": dom_te,
                        "test_dom_share": float(te_dist.max()),
                        "test_in_train_dom_share": in_dom_tr,
                        "match_flag": "✅ 一致" if dom_tr == dom_te else "⚠️ 不一致",
                    })
                pd.DataFrame(bsection).to_csv(OUT_DIR / "cluster_movement_match.csv", index=False)
                step5_results["cluster_movement"] = bsection

                # 5-C: 外挿検知 (per-sample min distance to centroid)
                log("  Step 5-C: 外挿検知 (per-sample nearest centroid distance)", logf)
                d_train = km.transform(X_train_scaled).min(axis=1)
                d_test = km.transform(X_test_scaled).min(axis=1)
                thr_d = np.quantile(d_train, 0.99)
                outlier_rate = float((d_test > thr_d).mean())
                log(f"    train min-dist q99 = {thr_d:.4f} / test outlier rate = {outlier_rate:.4f}", logf)
                step5_results["test_outlier_rate"] = outlier_rate
                step5_results["train_min_dist_q99"] = float(thr_d)

                # 5-D: cluster ごとの実 PnL profitability (labels から算出)
                log("  Step 5-D: cluster ごとの実 LONG/SHORT profitability (実 MFE-MAE 平均)", logf)
                labels_tr = pd.read_parquet(LABELS_TRAIN).sort_index()
                # index align
                common = df_train_norm_clu.index.intersection(labels_tr.index)
                assert len(common) == len(df_train_norm_clu)
                df_train_norm_clu_lab = df_train_norm_clu.join(labels_tr, rsuffix="_real")
                d_rows = []
                for c in range(chosen_k):
                    m = df_train_norm_clu_lab["cluster"] == c
                    long_pnl_proxy = float((df_train_norm_clu_lab.loc[m, "LONG_MFE_K12"] -
                                            df_train_norm_clu_lab.loc[m, "LONG_MAE_K12"]).mean())
                    short_pnl_proxy = float((df_train_norm_clu_lab.loc[m, "SHORT_MFE_K12"] -
                                             df_train_norm_clu_lab.loc[m, "SHORT_MAE_K12"]).mean())
                    log(f"    cluster {c}: real LONG (MFE-MAE) mean = {long_pnl_proxy:.2f} / "
                        f"SHORT (MFE-MAE) mean = {short_pnl_proxy:.2f} (USD・K12)", logf)
                    d_rows.append({
                        "cluster": c,
                        "long_mfe_minus_mae_k12": long_pnl_proxy,
                        "short_mfe_minus_mae_k12": short_pnl_proxy,
                    })
                pd.DataFrame(d_rows).to_csv(OUT_DIR / "cluster_profitability.csv", index=False)
                step5_results["profitability"] = d_rows

                # 5-E: k を下げて失う性質の定量化
                log("  Step 5-E: k=chosen_k - 1 へ縮退時に失う性質の定量化", logf)
                e_rows = []
                if chosen_k > 2:
                    km_low = km_per_k.get(chosen_k - 1)
                    if km_low is not None:
                        low_labels = km_low.labels_
                        # chosen_k のクラスタが chosen_k - 1 でどの cluster に吸収されるか
                        merge_map = pd.crosstab(tr_labels, low_labels)
                        for src_c in range(chosen_k):
                            dest = int(merge_map.loc[src_c].idxmax())
                            same_count = int(merge_map.loc[src_c].max())
                            total = int(merge_map.loc[src_c].sum())
                            log(f"    chosen_k={chosen_k} cluster {src_c} → k={chosen_k-1} cluster {dest} "
                                f"({same_count}/{total} = {same_count/total:.2%})", logf)
                            e_rows.append({"src_k": chosen_k, "src_cluster": src_c,
                                           "dest_k": chosen_k - 1, "dest_cluster": dest,
                                           "absorb_count": same_count, "src_total": total,
                                           "absorb_rate": same_count / total})
                else:
                    log("    chosen_k = 2 のため縮退方向なし", logf)
                pd.DataFrame(e_rows).to_csv(OUT_DIR / "k_reduction_loss.csv", index=False)
                step5_results["reduction_loss"] = e_rows

                # 5-F は report 記載 (定量化はモデル別比較必要・本タスクでは事実記載のみ)
                log("  Step 5-F: K12 LONG num_leaves=15 + 他 15 ラベル num_leaves=31 の混在モデル (事実記載のみ)", logf)

            else:  # 分岐 B
                log("Step 5 スキップ・分岐 B 3 選択肢評価レポート", logf)
                # 各選択肢の簡易評価を CSV に
                option_rows = [
                    {
                        "option": "1. clustering 廃止・per-entry prediction-based Exit",
                        "pros": "stability 問題を完全回避・予測値ベースで Exit を動的選択",
                        "cons": "cluster ベース構造洞察を失う・Exit ロジック複雑化",
                        "feasibility": "§4b.4-b の simulate_predicted_mfe_tp を拡張すれば実装可",
                    },
                    {
                        "option": "2. k=2 と k=3 を Phase 4-b 並走・Phase 5 実 PnL で比較",
                        "pros": "実 PnL で final 判定・clustering 機能不全でも片方が機能する可能性",
                        "cons": "実装/評価工数 2 倍・どちらも失敗時の plan C 不明",
                        "feasibility": "Phase 4-b 指示書改訂で対応可",
                    },
                    {
                        "option": "3. regime 特徴量 (1d ichimoku 等) を k-means 入力に追加",
                        "pros": "予測値以外の安定特徴で cluster 境界をアンカー",
                        "cons": "regime 研究は凍結中 (素材転用扱い)・追加特徴の look-ahead 監査必要",
                        "feasibility": "1,432 指標カタログから候補抽出可能・leak 4 点チェック必須",
                    },
                ]
                pd.DataFrame(option_rows).to_csv(OUT_DIR / "branch_b_options.csv", index=False)
                step5_results["branch_b_options"] = option_rows

            # ====== summary ======
            t1 = datetime.now()
            summary = {
                "task": "Phase 4-a 入力正規化 + k 再選定",
                "branch": branch,
                "chosen_k": chosen_k,
                "start": t0.isoformat(),
                "end": t1.isoformat(),
                "duration_sec": (t1 - t0).total_seconds(),
                "train_pred_sha256": train_sha,
                "test_pred_sha256": test_sha,
                "scaler_sha256": sha256_file(scaler_path),
                "k_evaluation": eval_rows,
                "step5_results": step5_results,
                "pre_norm_stability_ref": PRE_NORM_STABILITY,
            }
            with open(OUT_DIR / "normalize_reselect_summary.json", "w") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
            log(f"saved normalize_reselect_summary.json", logf)
            log(f"END duration={(t1 - t0).total_seconds():.2f}s", logf)

            log(f"Python warnings captured: {len(caught)}", logf)
            for w in caught:
                log(f"  WARN: {w.category.__name__}: {w.message}", logf)

    print(f"\nLOG: {LOG_PATH}", flush=True)


if __name__ == "__main__":
    main()
