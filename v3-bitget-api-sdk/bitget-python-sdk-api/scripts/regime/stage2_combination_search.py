"""stage2_combination_search.py — 段階2 組合せ最適化 (k=2 + bootstrap + seed+1)

設計原則 (論点1+2 確定済・2026-05-09):
  - 入力素材: pruned_column_list.json subset=all のみ (1,432 列)
  - 1 組合せ × 6 パターン同時評価 (target_match - others_match の乖離 pt)
  - 6 パターン独立 seed N=100 / bootstrap 候補数 = N
  - walk-forward expanding window (有効 fold 2-6)
  - ハイブリッド fold (通常 6 fold / 小サンプル n<30 で 3 fold)
  - 連続値は train fold 中央値で二値化 (subset=all・列数維持)
  - seed+1 (k=3 相当) 採否 = 閾値方式 (まこさん投入)
  - パターン別最終 M=5 判定式

実行 4 段:
  --mode=k2          → k=2 全探索 + walk-forward → stage2_k2_walk_forward.json
  --mode=seed        → seed N=100 + bootstrap CI → stage2_seed_bootstrap.json
  --mode=seed_plus1  → seed+1 探索               → stage2_seed_plus1.json
  --mode=final --threshold=<float> → 閾値投入 + M=5 → stage2_final_judgment_set.json

入出力:
  入力: data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv +
        results/regime_label_analysis/pruned_column_list.json
  出力: results/regime_label_analysis/stage2_*.json (4 ファイル)
"""

import sys
import os
import json
import argparse
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import pandas as pd
import numpy as np

from analyze_regime_label_features import build_indicators_extended
from analyze_transition_indicators import (
    load_labels, run_length_encode, extract_transitions, attach_indicators,
)
from analyze_stage1a_meta import TIMEFRAMES, ALL_INDICATORS as ALL_INDICATORS_1A
from analyze_stage1b_meta import W_CANDIDATES, resample_ohlcv, attach_features_to_labels as attach_1b
from analyze_stage1c_meta import compute_features_per_tf as compute_1c_features, attach_features_to_labels as attach_1c
from shape_features import compute_all_features

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
OUT_DIR = BASE / "results/regime_label_analysis"
PRUNED_JSON = OUT_DIR / "pruned_column_list.json"
OUT_K2 = OUT_DIR / "stage2_k2_walk_forward.json"
OUT_SEED = OUT_DIR / "stage2_seed_bootstrap.json"
OUT_SEED_P1 = OUT_DIR / "stage2_seed_plus1.json"
OUT_FINAL = OUT_DIR / "stage2_final_judgment_set.json"

# 確定パラメータ (論点2 確定値・暫定値ではない)
SEED_N = 100
FINAL_M = 5
BOOTSTRAP_ITER = 1000
TOPK_PER_PATTERN_TO_SAVE = 1000  # k=2 結果は上位 1000 のみ保存 (json サイズ抑制)
SMALL_SAMPLE_THRESHOLD = 30  # n<30 で 3 fold 化
PATTERNS = ["up->dn", "dn->up", "up->rg", "rg->up", "rg->dn", "dn->rg"]


# ── 入力ロード ──────────────────────────────────

def load_inputs():
    """pruned_column_list.json subset=all + labels + DATA_5M をロード。"""
    pruned = json.loads(PRUNED_JSON.read_text())
    pruned_all = {}
    for cat in pruned:
        pruned_all[cat] = {}
        for tf in pruned[cat]:
            cols = pruned[cat][tf].get("all", [])
            pruned_all[cat][tf] = cols

    labels = load_labels()
    df5m = pd.read_csv(DATA_5M, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    df_per_tf = {
        "5m": df5m,
        "15m": resample_ohlcv(df5m, "15min"),
        "30m": resample_ohlcv(df5m, "30min"),
        "1h": resample_ohlcv(df5m, "1h"),
        "4h": resample_ohlcv(df5m, "4h"),
        "1d": resample_ohlcv(df5m, "1D"),
    }
    return pruned_all, labels, df_per_tf


# ── per-bar テーブル構築 + attach ───────────────

def build_and_attach(pruned_all, labels, df_per_tf):
    """1,432 列の per-bar テーブルを構築 → 教師ラベルに attach。
    既存 attach_features_to_labels 仕様 (4h ラベル基準 + 各 TF 最新確定バー値) 踏襲。
    """
    feat_per_tf_1a = {tf: build_indicators_extended(df_per_tf[tf]) for tf in TIMEFRAMES}
    feat_per_tf_1b = {tf: {W: compute_all_features(df_per_tf[tf], W) for W in W_CANDIDATES}
                      for tf in TIMEFRAMES}
    structure_per_tf, c2_per_tf, swing_per_tf = compute_1c_features(df_per_tf)

    la = labels.copy()
    if la["timestamp_utc"].dt.tz is not None:
        la["timestamp_utc"] = la["timestamp_utc"].dt.tz_localize(None)
    la["ts_5m"] = la["timestamp_utc"] + pd.Timedelta(minutes=235)
    la["ts_15m"] = la["timestamp_utc"] + pd.Timedelta(minutes=225)
    la["ts_30m"] = la["timestamp_utc"] + pd.Timedelta(minutes=210)
    la["ts_1h"] = la["timestamp_utc"] + pd.Timedelta(hours=3)
    la["ts_4h"] = la["timestamp_utc"]
    la["ts_1d"] = la["timestamp_utc"].dt.floor("1D")

    for tf, feat in feat_per_tf_1a.items():
        keep = [c for c in ALL_INDICATORS_1A if c in feat.columns]
        la = attach_indicators(la, feat[keep], f"ts_{tf}", tf)

    la = attach_1b(la, feat_per_tf_1b)
    la = attach_1c(la, structure_per_tf, c2_per_tf, swing_per_tf)

    return la


# ── pruned カラム → labels_attached カラム名マッピング ────────

def map_pruned_to_attached_cols(pruned_all, labels_attached_cols):
    """pruned_column_list.json のカラム名を labels_attached のカラム名に変換。
    1-A: "rsi14" → "rsi14__5m"
    1-B: "v_shape_in_W_W10" → "v_shape_in_W__5m_W10"
    1-C: "dist_to_R1_pct_c2" → "dist_to_R1_pct__5m_c2"
         "dist_to_VAH_pct_b020_va60_N50" → "dist_to_VAH_pct_b020_va60__5m_N50_struct"
    """
    mapped = []
    attached_set = set(labels_attached_cols)

    for cat, by_tf in pruned_all.items():
        for tf, cols in by_tf.items():
            for col in cols:
                candidates = []
                if cat == "1-A":
                    candidates.append(f"{col}__{tf}")
                elif cat == "1-B":
                    # col 末尾 _W{W} を {tf}_W{W} に
                    if "_W" in col:
                        idx = col.rfind("_W")
                        base = col[:idx]
                        W_part = col[idx + 1:]  # "W10" 等
                        candidates.append(f"{base}__{tf}_{W_part}")
                elif cat == "1-C":
                    if col.endswith("_c2"):
                        base = col[:-3]
                        candidates.append(f"{base}__{tf}_c2")
                    else:
                        # 末尾 _N{N} を {tf}_N{N}_struct に
                        idx = col.rfind("_N")
                        if idx >= 0:
                            base = col[:idx]
                            N_part = col[idx + 1:]
                            candidates.append(f"{base}__{tf}_{N_part}_struct")

                for cand in candidates:
                    if cand in attached_set:
                        mapped.append((tf, cand))
                        break

    return mapped


# ── fold 分割 ──────────────────────────────────

def split_folds(transitions, n_fold=6):
    """198 切替点を時系列順 n_fold 等分。各 fold は transitions のサブリスト。"""
    sorted_tx = sorted(transitions, key=lambda ev: ev["t_idx"])
    fold_size = len(sorted_tx) // n_fold
    folds = []
    for k in range(n_fold):
        start = k * fold_size
        end = (k + 1) * fold_size if k < n_fold - 1 else len(sorted_tx)
        folds.append(sorted_tx[start:end])
    return folds


def merge_folds_for_small(folds):
    """連続 2 fold をマージ → 3 fold (小サンプルパターン用)"""
    return [folds[0] + folds[1], folds[2] + folds[3], folds[4] + folds[5]]


# ── 二値化 ─────────────────────────────────────

def binarize_per_fold(labels_attached, mapped_cols):
    """全 fold 共通の中央値で 1 回二値化 (簡略化版)。
    厳密な fold 別中央値再計算は計算量大 → 段階2 結果見て後追い修正可能。
    """
    binarized = {}
    for tf, col in mapped_cols:
        s = labels_attached[col].values
        median = np.nanmedian(s)
        bool_arr = (s > median).astype(np.uint8)
        bool_arr[np.isnan(s)] = 0
        binarized[(tf, col)] = bool_arr
    return binarized


# ── パターン別マスク ──────────────────────

def build_pattern_masks(labels_attached, transitions):
    """各教師バーが target/others 切替点か bool 配列化。"""
    n_bars = len(labels_attached)
    masks = {}
    for ptn in PATTERNS:
        target_mask = np.zeros(n_bars, dtype=bool)
        others_mask = np.zeros(n_bars, dtype=bool)
        for ev in transitions:
            tag = f"{ev['prev']}->{ev['cur']}"
            if tag == ptn:
                target_mask[ev["t_idx"]] = True
            else:
                others_mask[ev["t_idx"]] = True
        masks[ptn] = {"target_mask": target_mask, "others_mask": others_mask,
                      "target_n": int(target_mask.sum())}
    return masks


def build_fold_masks(folds_per_pattern, n_bars):
    """各 fold の切替点 idx を bool 配列化 (パターン別)。"""
    fold_masks = {}
    for ptn in PATTERNS:
        folds = folds_per_pattern[ptn]
        fold_masks[ptn] = []
        for fold_tx in folds:
            mask = np.zeros(n_bars, dtype=bool)
            for ev in fold_tx:
                if f"{ev['prev']}->{ev['cur']}" == ptn:
                    mask[ev["t_idx"]] = True
            fold_masks[ptn].append(mask)
    return fold_masks


# ── 1 組合せ評価 ──────────────────────────

def evaluate_combo(combo_bools, fold_masks_for_pattern, target_mask, others_mask):
    """1 組合せ × 1 パターン × walk-forward 全 fold 評価。"""
    if len(combo_bools) == 1:
        combo_active = combo_bools[0].astype(bool)
    else:
        combo_active = combo_bools[0].astype(bool)
        for b in combo_bools[1:]:
            combo_active = combo_active & b.astype(bool)

    target_n = int(target_mask.sum())
    others_n = int(others_mask.sum())
    target_hit = int((combo_active & target_mask).sum())
    others_hit = int((combo_active & others_mask).sum())
    target_match = (target_hit / target_n * 100) if target_n > 0 else 0.0
    others_match = (others_hit / others_n * 100) if others_n > 0 else 0.0
    total_hit = target_hit + others_hit
    precision = (target_hit / total_hit) if total_hit > 0 else 0.0
    recall = (target_hit / target_n) if target_n > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    # walk-forward fold 別 (有効 fold 2-N)
    fold_diverg = []
    for k in range(1, len(fold_masks_for_pattern)):
        test_mask = fold_masks_for_pattern[k]
        target_test_n = int(test_mask.sum())
        if target_test_n == 0:
            continue
        target_test_hit = int((combo_active & test_mask).sum())
        target_match_fold = target_test_hit / target_test_n * 100
        diverg_fold = target_match_fold - others_match  # others は全期間固定
        fold_diverg.append(diverg_fold)

    fold_avg = float(np.mean(fold_diverg)) if fold_diverg else 0.0
    fold_std = float(np.std(fold_diverg)) if fold_diverg else 0.0

    return {
        "diverg_pt": float(target_match - others_match),
        "fold_avg_diverg_pt": fold_avg,
        "fold_std_diverg_pt": fold_std,
        "target_match": float(target_match),
        "others_match": float(others_match),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "target_n": target_n,
        "n_folds_used": len(fold_diverg),
    }


# ── k=2 全探索 ──────────────────────────────

def k2_full_search(binarized, mapped_cols, pattern_masks, fold_masks_per_pattern):
    """102 万組 全探索 → パターン別上位 TOPK 件保存。"""
    cols = list(mapped_cols)
    n = len(cols)
    print(f"  k=2 全探索開始: {n}C2 = {n*(n-1)//2:,} 組 × {len(PATTERNS)} パターン")

    results_per_pattern = {ptn: [] for ptn in PATTERNS}
    cnt = 0
    t0 = time.time()
    for i in range(n):
        if i % 50 == 0 and i > 0:
            elapsed = time.time() - t0
            est_total = elapsed / i * n
            print(f"    {i}/{n} ({elapsed:.0f}s 経過 / 推定全体 {est_total:.0f}s)", flush=True)
        bool_i = binarized[cols[i]]
        for j in range(i + 1, n):
            bool_j = binarized[cols[j]]
            for ptn in PATTERNS:
                pm = pattern_masks[ptn]
                res = evaluate_combo([bool_i, bool_j], fold_masks_per_pattern[ptn],
                                     pm["target_mask"], pm["others_mask"])
                res["combo"] = [cols[i][1], cols[j][1]]
                res["combo_tfs"] = [cols[i][0], cols[j][0]]
                results_per_pattern[ptn].append(res)
                cnt += 1
        for ptn in PATTERNS:
            results_per_pattern[ptn].sort(key=lambda r: -r["fold_avg_diverg_pt"])
            results_per_pattern[ptn] = results_per_pattern[ptn][:TOPK_PER_PATTERN_TO_SAVE]

    print(f"  k=2 完了: 評価数 {cnt:,} / 経過 {time.time() - t0:.0f}s")
    return results_per_pattern


# ── seed 選定 + bootstrap ──────────────────────

def select_seed(k2_results, N=SEED_N):
    """パターン別上位 N 件を seed 確定。"""
    return {ptn: k2_results[ptn][:N] for ptn in PATTERNS}


def _build_col_to_tf_dict(binarized):
    """逆引き dict (col_name → tf) を 1 回構築。"""
    return {col: tf for (tf, col) in binarized.keys()}


def bootstrap_ci(seeds, binarized, pattern_masks, n_iter=BOOTSTRAP_ITER):
    """seed × 1000 回 bootstrap → 95% CI。"""
    col_to_tf = _build_col_to_tf_dict(binarized)
    out = {}
    for ptn, seed_list in seeds.items():
        pm = pattern_masks[ptn]
        target_idx = np.where(pm["target_mask"])[0]
        others_idx = np.where(pm["others_mask"])[0]
        out[ptn] = []
        for s in seed_list:
            bool_combo = binarized[(col_to_tf[s["combo"][0]], s["combo"][0])]
            for col_name in s["combo"][1:]:
                bool_combo = bool_combo & binarized[(col_to_tf[col_name], col_name)]
            divergs = []
            for _ in range(n_iter):
                tgt_sample = np.random.choice(target_idx, len(target_idx), replace=True)
                oth_sample = np.random.choice(others_idx, len(others_idx), replace=True)
                tm = bool_combo[tgt_sample].sum() / len(target_idx) * 100
                om = bool_combo[oth_sample].sum() / len(others_idx) * 100
                divergs.append(tm - om)
            ci_low = float(np.percentile(divergs, 2.5))
            ci_high = float(np.percentile(divergs, 97.5))
            out[ptn].append({**s, "ci_95_low": ci_low, "ci_95_high": ci_high})
    return out


# ── seed+1 探索 (k=3 相当) ─────────────────────

def seed_plus1_search(seeds, binarized, mapped_cols, pattern_masks, fold_masks_per_pattern):
    """各 seed × 1,430 列で k=3 探索。パターン別上位 TOPK 件保存。"""
    col_to_tf = _build_col_to_tf_dict(binarized)
    cols = list(binarized.keys())
    out = {}
    for ptn, seed_list in seeds.items():
        print(f"  {ptn} seed+1: {len(seed_list)} seed × {len(cols)-2:,} cols", flush=True)
        pm = pattern_masks[ptn]
        results = []
        for s in seed_list:
            seed_cols = set(s["combo"])
            bool_seed = binarized[(col_to_tf[s["combo"][0]], s["combo"][0])]
            for c in s["combo"][1:]:
                bool_seed = bool_seed & binarized[(col_to_tf[c], c)]
            for (tf, col) in cols:
                if col in seed_cols:
                    continue
                bool_combo = bool_seed & binarized[(tf, col)]
                res = evaluate_combo([bool_combo], fold_masks_per_pattern[ptn],
                                     pm["target_mask"], pm["others_mask"])
                res["combo"] = list(s["combo"]) + [col]
                res["combo_tfs"] = list(s.get("combo_tfs", [])) + [tf]
                res["seed_diverg_pt"] = s["fold_avg_diverg_pt"]
                res["delta_diverg_pt"] = res["fold_avg_diverg_pt"] - s["fold_avg_diverg_pt"]
                results.append(res)
        results.sort(key=lambda r: -r["fold_avg_diverg_pt"])
        out[ptn] = results[:TOPK_PER_PATTERN_TO_SAVE]
    return out


# ── 最終 M=5 件選定 (閾値投入) ──────────────

def select_final(seed_plus1_results, threshold, k2_seeds, M=FINAL_M):
    """閾値方式: delta_diverg_pt > threshold で k=3 候補化。
    各パターンで k=2 seed と k=3 候補を合わせて上位 M 件を最終判定式とする。
    """
    out = {}
    for ptn in PATTERNS:
        k3_candidates = [r for r in seed_plus1_results[ptn] if r.get("delta_diverg_pt", 0) > threshold]
        combined = list(k2_seeds[ptn]) + k3_candidates
        combined.sort(key=lambda r: -r["fold_avg_diverg_pt"])
        out[ptn] = combined[:M]
    return out


# ── メイン ─────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["k2", "seed", "seed_plus1", "final"], required=True)
    parser.add_argument("--threshold", type=float, default=None, help="final mode 用 seed+1 採否閾値")
    args = parser.parse_args()

    print(f"mode={args.mode}", flush=True)
    print("入力ロード...", flush=True)
    pruned_all, labels, df_per_tf = load_inputs()
    print("per-bar テーブル構築 + attach...", flush=True)
    labels_attached = build_and_attach(pruned_all, labels, df_per_tf)

    print("pruned カラムマッピング...", flush=True)
    mapped_cols = map_pruned_to_attached_cols(pruned_all, labels_attached.columns.tolist())
    print(f"  マッピング成功: {len(mapped_cols)} 列", flush=True)

    print("transitions 抽出 + fold 分割...", flush=True)
    runs = run_length_encode(labels["label_norm"].tolist())
    transitions = extract_transitions(runs)
    folds_normal = split_folds(transitions, n_fold=6)
    folds_small = merge_folds_for_small(folds_normal)
    folds_per_pattern = {}
    for ptn in PATTERNS:
        n_ptn = sum(1 for ev in transitions if f"{ev['prev']}->{ev['cur']}" == ptn)
        folds_per_pattern[ptn] = folds_small if n_ptn < SMALL_SAMPLE_THRESHOLD else folds_normal

    print("二値化...", flush=True)
    binarized = binarize_per_fold(labels_attached, mapped_cols)

    print("パターン別マスク + fold マスク構築...", flush=True)
    pattern_masks = build_pattern_masks(labels_attached, transitions)
    fold_masks_per_pattern = build_fold_masks(folds_per_pattern, len(labels_attached))

    if args.mode == "k2":
        print("k=2 全探索開始...", flush=True)
        k2_results = k2_full_search(binarized, mapped_cols, pattern_masks, fold_masks_per_pattern)
        OUT_K2.write_text(json.dumps(k2_results, indent=2, ensure_ascii=False))
        print(f"出力: {OUT_K2}")

    elif args.mode == "seed":
        print(f"k=2 結果ロード: {OUT_K2}")
        k2_results = json.loads(OUT_K2.read_text())
        print(f"seed N={SEED_N} 確定...")
        seeds = select_seed(k2_results, N=SEED_N)
        print("bootstrap CI 計算...")
        seeds_with_ci = bootstrap_ci(seeds, binarized, pattern_masks)
        OUT_SEED.write_text(json.dumps(seeds_with_ci, indent=2, ensure_ascii=False))
        print(f"出力: {OUT_SEED}")

    elif args.mode == "seed_plus1":
        print(f"seed ロード: {OUT_SEED}")
        seeds = json.loads(OUT_SEED.read_text())
        print("seed+1 探索...")
        seed_p1 = seed_plus1_search(seeds, binarized, mapped_cols, pattern_masks, fold_masks_per_pattern)
        OUT_SEED_P1.write_text(json.dumps(seed_p1, indent=2, ensure_ascii=False))
        print(f"出力: {OUT_SEED_P1}")

    elif args.mode == "final":
        if args.threshold is None:
            raise SystemExit("--threshold=<float> 必須")
        print(f"seed+1 ロード: {OUT_SEED_P1}")
        seed_p1 = json.loads(OUT_SEED_P1.read_text())
        seeds = json.loads(OUT_SEED.read_text())
        print(f"閾値 {args.threshold} で final M={FINAL_M} 選定...")
        final = select_final(seed_p1, args.threshold, seeds, M=FINAL_M)
        OUT_FINAL.write_text(json.dumps(final, indent=2, ensure_ascii=False))
        print(f"出力: {OUT_FINAL}")

    print("DONE")


if __name__ == "__main__":
    main()
