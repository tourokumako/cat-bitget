"""
Phase 4-a 再検討: k=2 vs k=3 比較評価

指示書: .claude/instructions/2026-05-14_phase4a_k2_revisit.md
phase_compliance §4a 準拠 (4a.1〜4a.5)

Steps:
  1. k=2 で k-means fit (train) + joblib 保存
  2. k=2 を test 2025 に apply (transform/predict のみ・再 fit 禁止)
  3. k=2 vs k=3 安定性比較 (cluster share max_diff / sum_diff)
  4. K12 LONG q99 / K96 SHORT q99 サンプル数 (k=2 版)
  5. bit-exact 再現性確認 (random_state=42 で 2 回 fit → labels 一致)

注:
  指示書の `pred_cols = startswith('pred_')` は実データの列名と不一致 (空リストになる)。
  実データの列名は LONG_MFE_K12 等 16 列。Phase 4-a と同じ LABEL_COLS 定義に揃える (L-180 doc-vs-impl 整合性修正)。
  test 予測パスも指示書記載の ml_phase1/ ではなく ml_phase1_k12long_refit/ が正 (実ファイルパス)。
"""

import hashlib
import json
import os
import sys
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
PHASE4A_K3_DIR = DATA_DIR / "ml_phase4_a"          # k=3 既存 (比較用)
OUT_DIR = DATA_DIR / "ml_phase4_a_k2"              # k=2 新規
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_PRED_PATH = REFIT_DIR / "predictions_train_2021_2024_k12long_refit.parquet"
TEST_PRED_PATH = REFIT_DIR / "predictions_test2025_k12long_refit.parquet"
LABELS_TRAIN = DATA_DIR / "labels_mfe_mae_train_2021_2024.parquet"

# Phase 4-a と同じ 16 列 (指示書 typo `pred_*` を実データに整合)
LABEL_COLS = [
    f"{side}_{kind}_K{k}"
    for k in (12, 24, 48, 96)
    for side in ("LONG", "SHORT")
    for kind in ("MFE", "MAE")
]
assert len(LABEL_COLS) == 16

RANDOM_STATE = 42
SILHOUETTE_SAMPLE = 20000
K_CHOSEN = 2

# Phase 4-a 完了報告 (Step 5) から引用した k=3 test share (比較用固定値)
K3_TRAIN_SHARES = {0: 172091, 1: 192065, 2: 30597}
K3_TEST_SHARES = {0: 71030, 1: 4707, 2: 29383}


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


def main():
    t0 = datetime.now()
    TS = t0.strftime("%Y%m%dT%H%M%SZ")
    LOG_PATH = OUT_DIR / f"k2_revisit_log_{TS}.txt"
    warn_buffer = []

    with open(LOG_PATH, "w") as logf:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            log(f"Phase 4-a k=2 revisit START at {t0.isoformat()}", logf)
            log(f"output: {OUT_DIR}", logf)

            # 物理証跡 1: 入力ファイル整合性
            assert TRAIN_PRED_PATH.exists(), f"missing {TRAIN_PRED_PATH}"
            assert TEST_PRED_PATH.exists(), f"missing {TEST_PRED_PATH}"
            train_sha = sha256_file(TRAIN_PRED_PATH)
            test_sha = sha256_file(TEST_PRED_PATH)
            log(f"  train pred sha256: {train_sha[:12]}", logf)
            log(f"  test  pred sha256: {test_sha[:12]}", logf)

            # ====== Step 1: k=2 で k-means fit (train) ======
            log("Step 1: k=2 で k-means fit (train) ...", logf)
            df_train = pd.read_parquet(TRAIN_PRED_PATH).sort_index()
            log(f"  train: rows={len(df_train)} cols={len(df_train.columns)}", logf)
            assert len(df_train) == 394753, f"expected 394753 rows, got {len(df_train)}"

            X_train = df_train[LABEL_COLS].values
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            log(f"  X_train_scaled shape: {X_train_scaled.shape}", logf)

            km2 = KMeans(n_clusters=K_CHOSEN, random_state=RANDOM_STATE, n_init=10)
            km2.fit(X_train_scaled)
            train_labels = km2.labels_
            log(f"  k=2 fit: inertia={km2.inertia_:.2f} n_iter={km2.n_iter_}", logf)

            # silhouette (Phase 4-a と同じ sample size)
            sil_k2 = silhouette_score(
                X_train_scaled, train_labels,
                sample_size=SILHOUETTE_SAMPLE, random_state=RANDOM_STATE,
            )
            log(f"  k=2 silhouette: {sil_k2:.4f}", logf)

            # 4a.4: artifact 名禁止チェック
            scaler_path = OUT_DIR / "scaler_train_2021_2024.joblib"
            km_path = OUT_DIR / "kmeans_k2_train_2021_2024.joblib"
            for p in (scaler_path, km_path):
                assert "test" not in p.name.lower(), f"forbidden 'test' in {p.name}"
                assert "train" in p.name.lower(), f"missing 'train' in {p.name}"
            joblib.dump(scaler, scaler_path)
            joblib.dump(km2, km_path)
            log(f"  saved {scaler_path.name} ({scaler_path.stat().st_size} B)", logf)
            log(f"  saved {km_path.name} ({km_path.stat().st_size} B)", logf)

            # 物理証跡 3: 出力 joblib sha256
            scaler_sha = sha256_file(scaler_path)
            km_sha = sha256_file(km_path)
            log(f"  scaler sha256: {scaler_sha[:12]}", logf)
            log(f"  km     sha256: {km_sha[:12]}", logf)

            # 物理証跡 4: 第三者再読み出し検証
            scaler_reload = joblib.load(scaler_path)
            km_reload = joblib.load(km_path)
            assert km_reload.n_clusters == 2
            assert km_reload.cluster_centers_.shape == (2, 16), \
                f"unexpected cluster_centers_ shape {km_reload.cluster_centers_.shape}"
            log(f"  joblib reload OK: n_clusters=2 cluster_centers_ shape=(2,16)", logf)

            # ====== Step 2: k=2 を test 2025 に apply ======
            log("Step 2: k=2 を test 2025 に apply (transform/predict のみ) ...", logf)
            df_test = pd.read_parquet(TEST_PRED_PATH).sort_index()
            log(f"  test: rows={len(df_test)} cols={len(df_test.columns)}", logf)
            X_test = df_test[LABEL_COLS].values
            X_test_scaled = scaler.transform(X_test)
            test_labels = km2.predict(X_test_scaled)
            df_test["cluster_k2"] = test_labels
            df_test.to_parquet(OUT_DIR / "predictions_test2025_clustered_k2.parquet")
            log(f"  saved predictions_test2025_clustered_k2.parquet", logf)

            # ====== Step 3: train/test 安定性比較 ======
            log("Step 3: k=2 vs k=3 安定性比較 ...", logf)

            train_sizes_k2 = pd.Series(train_labels).value_counts().sort_index().to_dict()
            test_sizes_k2 = pd.Series(test_labels).value_counts().sort_index().to_dict()
            n_train = len(df_train)
            n_test = len(df_test)

            train_shares_k2 = {int(c): n / n_train for c, n in train_sizes_k2.items()}
            test_shares_k2 = {int(c): n / n_test for c, n in test_sizes_k2.items()}
            log(f"  k=2 train shares: {[(c, f'{s:.3f}') for c, s in train_shares_k2.items()]}", logf)
            log(f"  k=2 test  shares: {[(c, f'{s:.3f}') for c, s in test_shares_k2.items()]}", logf)

            k3_train_shares = {c: n / sum(K3_TRAIN_SHARES.values()) for c, n in K3_TRAIN_SHARES.items()}
            k3_test_shares = {c: n / sum(K3_TEST_SHARES.values()) for c, n in K3_TEST_SHARES.items()}

            def stability(train_sh, test_sh):
                # 同じ cluster id 同士の share 差を比較
                clusters = sorted(set(train_sh.keys()) | set(test_sh.keys()))
                diffs = [abs(train_sh.get(c, 0) - test_sh.get(c, 0)) for c in clusters]
                return {"max_diff_pp": max(diffs) * 100, "sum_diff_pp": sum(diffs) * 100}

            stab_k2 = stability(train_shares_k2, test_shares_k2)
            stab_k3 = stability(k3_train_shares, k3_test_shares)
            log(f"  k=2 stability: max_diff={stab_k2['max_diff_pp']:.2f}pp sum_diff={stab_k2['sum_diff_pp']:.2f}pp", logf)
            log(f"  k=3 stability: max_diff={stab_k3['max_diff_pp']:.2f}pp sum_diff={stab_k3['sum_diff_pp']:.2f}pp", logf)

            # ====== Step 3-D: K12 LONG q99 / K96 SHORT q99 サンプル数 (k=2 版) ======
            log("Step 3-D: K12 LONG q99 / K96 SHORT q99 サンプル数 (k=2 版) ...", logf)

            df_train_lab = df_train.copy()
            df_train_lab["cluster_k2"] = train_labels

            # K12 LONG q99 (train)
            ratio_k12long = df_train_lab["LONG_MFE_K12"] / df_train_lab["LONG_MAE_K12"].clip(lower=1e-9)
            q99_thr_k12 = ratio_k12long.quantile(0.99)
            mask_k12 = ratio_k12long >= q99_thr_k12
            k12_dist_train = df_train_lab.loc[mask_k12, "cluster_k2"].value_counts().sort_index().to_dict()
            log(f"  K12 LONG q99 train threshold={q99_thr_k12:.4f} total_fire={int(mask_k12.sum())}", logf)
            for cl in range(K_CHOSEN):
                n = int(k12_dist_train.get(cl, 0))
                v = "✅ 統計的有意" if n >= 100 else ("⚠️ 仮説レベル" if n >= 30 else "❌ 根拠不足")
                log(f"    cluster {cl}: n={n} {v}", logf)

            # K12 LONG q99 (test) - 検証情報として記録
            ratio_k12long_test = df_test["LONG_MFE_K12"] / df_test["LONG_MAE_K12"].clip(lower=1e-9)
            q99_thr_k12_test = ratio_k12long_test.quantile(0.99)
            mask_k12_test = ratio_k12long_test >= q99_thr_k12_test
            k12_dist_test = df_test.loc[mask_k12_test, "cluster_k2"].value_counts().sort_index().to_dict()
            log(f"  K12 LONG q99 test  threshold={q99_thr_k12_test:.4f} total_fire={int(mask_k12_test.sum())}", logf)
            for cl in range(K_CHOSEN):
                n = int(k12_dist_test.get(cl, 0))
                log(f"    cluster {cl}: n={n} (test)", logf)

            # K96 SHORT q99 (train) + フォールバック判定
            labels_train_real = pd.read_parquet(LABELS_TRAIN).sort_index()
            common_idx = df_train_lab.index.intersection(labels_train_real.index)
            assert len(common_idx) == len(df_train_lab), "index mismatch"
            ratio_k96short = df_train_lab["SHORT_MFE_K96"] / df_train_lab["SHORT_MAE_K96"].clip(lower=1e-9)
            q99_thr_k96 = ratio_k96short.quantile(0.99)
            mask_k96 = ratio_k96short >= q99_thr_k96
            log(f"  K96 SHORT q99 train threshold={q99_thr_k96:.4f} total_fire={int(mask_k96.sum())}", logf)

            k96_rows = []
            for cl in range(K_CHOSEN):
                cl_mask = mask_k96 & (df_train_lab["cluster_k2"] == cl)
                n = int(cl_mask.sum())
                if n == 0:
                    k96_rows.append({"cluster": cl, "n_k96short_q99": 0,
                                     "real_MFE_mean": np.nan, "real_MAE_mean": np.nan,
                                     "mfe_mae_ratio": np.nan, "fallback_flag": "—"})
                    log(f"    cluster {cl}: n=0", logf)
                    continue
                idx_in_labels = df_train_lab.index[cl_mask]
                real_mfe = float(labels_train_real.loc[idx_in_labels, "SHORT_MFE_K96"].mean())
                real_mae = float(labels_train_real.loc[idx_in_labels, "SHORT_MAE_K96"].mean())
                ratio = real_mfe / real_mae if real_mae > 0 else float("nan")
                flag = "⚠️ no-trade 候補 (MFE/MAE < 1.0)" if ratio < 1.0 else "✅ trade 可"
                log(f"    cluster {cl}: n={n} MFE/MAE={ratio:.4f} {flag}", logf)
                k96_rows.append({"cluster": cl, "n_k96short_q99": n,
                                 "real_MFE_mean": real_mfe, "real_MAE_mean": real_mae,
                                 "mfe_mae_ratio": ratio, "fallback_flag": flag})

            # K96 SHORT q99 (test) - 検証情報として記録
            ratio_k96short_test = df_test["SHORT_MFE_K96"] / df_test["SHORT_MAE_K96"].clip(lower=1e-9)
            q99_thr_k96_test = ratio_k96short_test.quantile(0.99)
            mask_k96_test = ratio_k96short_test >= q99_thr_k96_test
            k96_dist_test = df_test.loc[mask_k96_test, "cluster_k2"].value_counts().sort_index().to_dict()
            log(f"  K96 SHORT q99 test  threshold={q99_thr_k96_test:.4f} total_fire={int(mask_k96_test.sum())}", logf)
            for cl in range(K_CHOSEN):
                n = int(k96_dist_test.get(cl, 0))
                log(f"    cluster {cl}: n={n} (test)", logf)

            # ====== Step 5 / 物理証跡 7: bit-exact 再現性確認 ======
            log("Step 5: bit-exact 再現性確認 (k=2 fit を 2 回実行 → labels 一致) ...", logf)
            # Phase 4-a と同じ random_state=42 / n_init=10 で再実行
            scaler2 = StandardScaler()
            X_train_scaled_2 = scaler2.fit_transform(X_train)
            km2_b = KMeans(n_clusters=K_CHOSEN, random_state=RANDOM_STATE, n_init=10)
            km2_b.fit(X_train_scaled_2)
            labels_b = km2_b.labels_
            bit_exact = bool((train_labels == labels_b).all())
            log(f"  2 回目 inertia={km2_b.inertia_:.2f} n_iter={km2_b.n_iter_}", logf)
            log(f"  labels match: {bit_exact}", logf)
            assert bit_exact, "bit-exact reproducibility FAILED"

            # ====== 比較 CSV 出力 ======
            log("Step 3-final: k=2 vs k=3 比較表を CSV 出力 ...", logf)
            comparison_rows = [
                {"metric": "silhouette", "k2": round(sil_k2, 4), "k3": 0.5100, "winner": "k=3 (僅差)"},
                {"metric": "train cluster sizes", "k2": json.dumps(train_sizes_k2), "k3": json.dumps(K3_TRAIN_SHARES), "winner": "-"},
                {"metric": "test  cluster sizes", "k2": json.dumps(test_sizes_k2), "k3": json.dumps(K3_TEST_SHARES), "winner": "-"},
                {"metric": "stability max_diff (pp)", "k2": round(stab_k2["max_diff_pp"], 2),
                 "k3": round(stab_k3["max_diff_pp"], 2),
                 "winner": "k=2" if stab_k2["max_diff_pp"] < stab_k3["max_diff_pp"] else "k=3"},
                {"metric": "stability sum_diff (pp)", "k2": round(stab_k2["sum_diff_pp"], 2),
                 "k3": round(stab_k3["sum_diff_pp"], 2),
                 "winner": "k=2" if stab_k2["sum_diff_pp"] < stab_k3["sum_diff_pp"] else "k=3"},
                {"metric": "bit-exact reproducibility", "k2": str(bit_exact), "k3": "(未測定)", "winner": "-"},
            ]
            pd.DataFrame(comparison_rows).to_csv(OUT_DIR / "k2_vs_k3_comparison.csv", index=False)
            log(f"  saved k2_vs_k3_comparison.csv", logf)

            # サンプル数 CSV (k=2 / 監査 #2 基準)
            sample_rows = []
            for cl in range(K_CHOSEN):
                sample_rows.append({
                    "k": 2,
                    "cluster": cl,
                    "n_k12long_q99_train": int(k12_dist_train.get(cl, 0)),
                    "n_k96short_q99_train": int(k96_rows[cl]["n_k96short_q99"]),
                    "k96short_real_mfe_mae_ratio": k96_rows[cl]["mfe_mae_ratio"],
                    "k96short_fallback_flag": k96_rows[cl]["fallback_flag"],
                })
            pd.DataFrame(sample_rows).to_csv(OUT_DIR / "k2_sample_size_check.csv", index=False)
            log(f"  saved k2_sample_size_check.csv", logf)

            # summary JSON
            t1 = datetime.now()
            summary = {
                "task": "Phase 4-a k=2 revisit",
                "chosen_k": K_CHOSEN,
                "silhouette_k2": float(sil_k2),
                "silhouette_k3_ref": 0.5100,
                "inertia_k2": float(km2.inertia_),
                "n_iter_k2": int(km2.n_iter_),
                "bit_exact_reproducibility": bit_exact,
                "train_sizes_k2": {int(k): int(v) for k, v in train_sizes_k2.items()},
                "test_sizes_k2": {int(k): int(v) for k, v in test_sizes_k2.items()},
                "stability_k2_max_diff_pp": stab_k2["max_diff_pp"],
                "stability_k2_sum_diff_pp": stab_k2["sum_diff_pp"],
                "stability_k3_max_diff_pp": stab_k3["max_diff_pp"],
                "stability_k3_sum_diff_pp": stab_k3["sum_diff_pp"],
                "train_pred_sha256": train_sha,
                "test_pred_sha256": test_sha,
                "scaler_sha256": scaler_sha,
                "km_sha256": km_sha,
                "start": t0.isoformat(),
                "end": t1.isoformat(),
                "duration_sec": (t1 - t0).total_seconds(),
            }
            with open(OUT_DIR / "k2_revisit_summary.json", "w") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            log(f"  saved k2_revisit_summary.json", logf)
            log(f"END duration={(t1 - t0).total_seconds():.2f}s", logf)

            # warning 全件
            warn_buffer.extend(caught)
            log(f"Python warnings captured: {len(warn_buffer)}", logf)
            for w in warn_buffer:
                log(f"  WARN: {w.category.__name__}: {w.message}", logf)

    print(f"\nLOG: {LOG_PATH}", flush=True)


if __name__ == "__main__":
    main()
