"""stage3_validate_judgment_set.py — 段階3 (3-1) 検証

設計原則 (論点1+2+3 確定済・2026-05-10):
  - 入力: stage2_final_judgment_set.json (30 件・6 パターン × M=5)
  - 5m 確定足タイミングで merge_asof + ffill (各 TF 値同期・論点4 整合)
  - 全データ中央値で二値化 (段階2 と同じ)
  - 5 ケース並走: OR (1件発火) / vote2 / vote3 / vote4 / AND (5件全発火)
  - 6 パターン衝突解決: 平均乖離 pt 最大採用 (β は段階3 結果見て再検証余地)
  - 合格基準 4 項目評価:
    ① 24 サンプルヒット率 (samples_24.parquet・peak_time±24 5m バーで該当 direction 発火)
    ② 2025 年一致率
    ③ 月別肉眼合格 (5 ケース全部 csv 出力 1 ファイル並走列・まこさん視認)
    ④ 持続安定性 (連続発火期間中央値・2 時間 = 24 5m バー目安)

メモリ最適化: 30 判定式に必要な列のみ抽出 (重複除いて 30-60 列)

実行: python3 stage3_validate_judgment_set.py
出力: results/regime_label_analysis/stage3_validation_report.md +
      results/regime_label_analysis/stage3_monthly_comparison.csv (5 ケース並走列)
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict

from analyze_regime_label_features import build_indicators_extended
from analyze_transition_indicators import load_labels
from analyze_stage1a_meta import TIMEFRAMES, ALL_INDICATORS as ALL_INDICATORS_1A
from analyze_stage1b_meta import W_CANDIDATES, resample_ohlcv
from analyze_stage1c_meta import compute_features_per_tf as compute_1c_features
from shape_features import compute_all_features

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
OUT_DIR = BASE / "results/regime_label_analysis"
FINAL_JSON = OUT_DIR / "stage2_final_judgment_set.json"
SAMPLES_24 = BASE / "results/vshape_design/samples_24.parquet"
OUT_MD = OUT_DIR / "stage3_validation_report.md"
OUT_MONTHLY = OUT_DIR / "stage3_monthly_comparison.csv"

PATTERNS = ["up->dn", "dn->up", "up->rg", "rg->up", "rg->dn", "dn->rg"]
VOTE_CASES = [(1, "OR"), (2, "vote2"), (3, "vote3"), (4, "vote4"), (5, "AND")]
PERSISTENCE_TARGET_BARS = 24  # 2h = 5m × 24
SAMPLE_24_HIT_WINDOW_BARS = 24  # peak_time ± 24 5m バー (±2h) で発火していれば hit

# 24 サンプル direction → CC パターン マッピング
# samples_24.parquet の direction は "up" (V字下→上) / "down" (逆V字上→下)
# CC pattern: dn->up = direction "up" / up->dn = direction "down"
DIRECTION_TO_PATTERN = {"up": "dn->up", "down": "up->dn"}


# ── ロード + カラム抽出 ──────────────────────────

def load_final_judgment_set():
    return json.loads(FINAL_JSON.read_text())


def collect_required_cols(final_set):
    """30 判定式に出る pruned カラムを重複除いて抽出。
    Returns: set of (tf, col_name) where col_name は labels_attached 形式
    """
    cols_set = set()
    for ptn in PATTERNS:
        for j in final_set.get(ptn, []):
            for col, tf in zip(j["combo"], j.get("combo_tfs", [])):
                cols_set.add((tf, col))
    return cols_set


# ── per-bar テーブル構築 (5m index) ──────────────

def build_per_bar_for_required_cols(required_cols, df_per_tf):
    """必要な列のみ各 TF native 時系列で計算 → 5m index に merge_asof + ffill。
    Returns: dict {(tf, col): np.ndarray of float aligned to 5m index}
    """
    df5m = df_per_tf["5m"]
    n_5m = len(df5m)

    cols_per_tf = defaultdict(set)
    for tf, col in required_cols:
        cols_per_tf[tf].add(col)

    # 各 TF で必要な base columns (suffix を外したもの) を計算
    out = {}
    for tf, cols in cols_per_tf.items():
        print(f"  {tf}: {len(cols)} 列計算...", flush=True)
        feats = _compute_features_for_tf(df_per_tf[tf], cols, tf)
        # feats のカラムは labels_attached 形式 (例: "rsi14__5m")
        # 5m なら direct copy / 他 TF なら merge_asof + ffill
        if tf == "5m":
            for col in cols:
                if col in feats.columns:
                    out[(tf, col)] = feats[col].values
                else:
                    out[(tf, col)] = np.full(n_5m, np.nan)
        else:
            tf_minutes = {"15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}[tf]
            # バー完了時刻 = バー開始時刻 + バー幅
            feats_completed = feats.copy()
            feats_completed.index = feats.index + pd.Timedelta(minutes=tf_minutes)
            df5m_ts = pd.DataFrame({"timestamp": df5m.index}).sort_values("timestamp")
            for col in cols:
                if col in feats_completed.columns:
                    s = feats_completed[col].dropna()
                    if len(s) == 0:
                        out[(tf, col)] = np.full(n_5m, np.nan)
                        continue
                    src = pd.DataFrame({"timestamp": s.index, "value": s.values}).sort_values("timestamp")
                    aligned = pd.merge_asof(df5m_ts, src, on="timestamp", direction="backward")
                    out[(tf, col)] = aligned["value"].values
                else:
                    out[(tf, col)] = np.full(n_5m, np.nan)
    return out


def _compute_features_for_tf(df_tf, cols_needed, tf):
    """指定 TF の必要列を計算 → labels_attached 形式カラム名で DataFrame 返す。
    cols_needed: set of "{base}__{tf}_<suffix>" (1-A は suffix なし・1-B は _W{W}・1-C は _N{N}_struct or _c2)
    """
    # 1-A 列 (例: "rsi14__5m"): suffix なし
    cols_1a_base = set()
    # 1-B 列 (例: "v_shape_in_W__5m_W10"): suffix _W{W}
    cols_1b_W_to_base = defaultdict(set)
    # 1-C 列: _N{N}_struct or _c2
    cols_1c_struct = defaultdict(set)  # N → set of base cols
    cols_1c_c2 = set()

    for col in cols_needed:
        if "__" not in col:
            continue
        base, suffix = col.rsplit("__", 1)
        # suffix の形式判定
        if suffix == tf:
            # 1-A
            cols_1a_base.add(base)
        elif suffix.startswith(f"{tf}_W"):
            # 1-B: 例 "5m_W10"
            W_part = suffix[len(f"{tf}_"):]  # "W10"
            cols_1b_W_to_base[W_part].add(base)
        elif suffix.endswith("_struct") and suffix.startswith(f"{tf}_N"):
            # 1-C struct: 例 "5m_N50_struct"
            N_part = suffix[len(f"{tf}_"):-len("_struct")]  # "N50"
            cols_1c_struct[N_part].add(base)
        elif suffix == f"{tf}_c2":
            # 1-C c2
            cols_1c_c2.add(base)

    out = pd.DataFrame(index=df_tf.index)

    # 1-A
    if cols_1a_base:
        feats_1a = build_indicators_extended(df_tf)
        for base in cols_1a_base:
            if base in feats_1a.columns:
                out[f"{base}__{tf}"] = feats_1a[base]

    # 1-B
    for W_part, bases in cols_1b_W_to_base.items():
        W = int(W_part[1:])
        feats_W = compute_all_features(df_tf, W)
        for base in bases:
            if base in feats_W.columns:
                out[f"{base}__{tf}_{W_part}"] = feats_W[base]

    # 1-C: structure_features の compute_features_for_N + compute_c2_only を直接呼ぶ
    if cols_1c_struct or cols_1c_c2:
        from structure_features import compute_features_for_N, compute_c2_only
        if cols_1c_struct:
            for N_part, bases in cols_1c_struct.items():
                N = int(N_part[1:])
                feats_N = compute_features_for_N(df_tf, N)
                for base in bases:
                    if base in feats_N.columns:
                        out[f"{base}__{tf}_{N_part}_struct"] = feats_N[base]
        if cols_1c_c2:
            feats_c2 = compute_c2_only(df_tf)
            for base in cols_1c_c2:
                if base in feats_c2.columns:
                    out[f"{base}__{tf}_c2"] = feats_c2[base]

    return out


# ── 二値化 ─────────────────────────────────────

def binarize_per_5m(per_bar_5m):
    """全データ中央値で二値化。"""
    out = {}
    for key, arr in per_bar_5m.items():
        valid = arr[~np.isnan(arr)]
        if len(valid) == 0:
            out[key] = np.zeros(len(arr), dtype=np.uint8)
            continue
        median = float(np.median(valid))
        bin_arr = (arr > median).astype(np.uint8)
        bin_arr[np.isnan(arr)] = 0
        out[key] = bin_arr
    return out


# ── 30 判定式の発火マスク構築 ────────────────────

def build_judgment_fire_masks(final_set, binarized, n_5m):
    """各判定式 (k=2 or k=3) の発火 bool 配列を構築。
    Returns: dict {(pattern, rank): np.ndarray of bool}
    """
    out = {}
    for ptn in PATTERNS:
        for rank, j in enumerate(final_set.get(ptn, [])):
            cols = j["combo"]
            tfs = j.get("combo_tfs", [])
            bool_combo = None
            ok = True
            for col, tf in zip(cols, tfs):
                key = (tf, col)
                if key not in binarized:
                    ok = False
                    break
                if bool_combo is None:
                    bool_combo = binarized[key].astype(bool)
                else:
                    bool_combo = bool_combo & binarized[key].astype(bool)
            if not ok or bool_combo is None:
                bool_combo = np.zeros(n_5m, dtype=bool)
            out[(ptn, rank)] = bool_combo
    return out


# ── パターン別多数決 (5 ケース並走) ────────────

def vote_per_pattern(judgment_masks, vote_threshold, n_5m):
    """各パターンで M=5 中 vote_threshold 件以上発火 = パターン発火。"""
    out = {}
    for ptn in PATTERNS:
        votes = np.zeros(n_5m, dtype=int)
        for rank in range(5):
            key = (ptn, rank)
            if key in judgment_masks:
                votes += judgment_masks[key].astype(int)
        out[ptn] = votes >= vote_threshold
    return out


# ── 6 パターン衝突解決 ────────────────────────

def resolve_conflicts(pattern_fires, final_set, n_5m):
    """各 5m バーで複数パターン発火時、平均乖離 pt 最大のパターン採用。
    Returns: np.ndarray of str
    """
    pattern_avg_diverg = {}
    for ptn in PATTERNS:
        if final_set.get(ptn):
            divergs = [j["fold_avg_diverg_pt"] for j in final_set[ptn]]
            pattern_avg_diverg[ptn] = float(np.mean(divergs))
        else:
            pattern_avg_diverg[ptn] = -np.inf

    out = np.full(n_5m, "none", dtype=object)
    sorted_patterns = sorted(PATTERNS, key=lambda p: -pattern_avg_diverg[p])
    for ptn in sorted_patterns:
        mask = pattern_fires[ptn] & (out == "none")
        out[mask] = ptn
    return out


# ── 評価指標 ─────────────────────────

def evaluate_persistence(pattern_label):
    """各パターン発火後の連続発火期間 (バー数)。"""
    out = {}
    for ptn in PATTERNS:
        is_fire = pattern_label == ptn
        runs = []
        in_run = False
        run_len = 0
        for v in is_fire:
            if v:
                in_run = True
                run_len += 1
            else:
                if in_run and run_len > 0:
                    runs.append(run_len)
                in_run = False
                run_len = 0
        if in_run:
            runs.append(run_len)
        if runs:
            out[ptn] = {
                "n_runs": len(runs),
                "median_bars": float(np.median(runs)),
                "mean_bars": float(np.mean(runs)),
                "max_bars": int(np.max(runs)),
                "ge_target": int(sum(1 for r in runs if r >= PERSISTENCE_TARGET_BARS)),
            }
        else:
            out[ptn] = {"n_runs": 0, "median_bars": 0, "mean_bars": 0, "max_bars": 0, "ge_target": 0}
    return out


def evaluate_24_samples(pattern_label, df5m_index):
    """samples_24.parquet と照合。peak_time ±SAMPLE_24_HIT_WINDOW_BARS で該当 direction 発火 = hit。"""
    if not SAMPLES_24.exists():
        return {"hit_rate": None, "note": f"{SAMPLES_24} 未存在"}
    samples = pd.read_parquet(SAMPLES_24)
    hits = 0
    total = 0
    miss_details = []
    for _, s in samples.iterrows():
        peak_time = pd.to_datetime(s["peak_time"])
        direction = s["direction"]
        expected_pattern = DIRECTION_TO_PATTERN.get(direction)
        if expected_pattern is None:
            continue
        idx = df5m_index.searchsorted(peak_time)
        if idx < 0 or idx >= len(df5m_index):
            continue
        lo = max(0, idx - SAMPLE_24_HIT_WINDOW_BARS)
        hi = min(len(df5m_index), idx + SAMPLE_24_HIT_WINDOW_BARS + 1)
        window = pattern_label[lo:hi]
        is_hit = (window == expected_pattern).any()
        if is_hit:
            hits += 1
        else:
            miss_details.append(f"{s['sample_id']} ({direction}/{peak_time.strftime('%Y-%m-%d')})")
        total += 1
    return {
        "hit_rate": hits / total if total > 0 else 0,
        "hits": hits,
        "total": total,
        "miss": miss_details,
    }


def evaluate_2025_match(pattern_label, df5m_index, labels_4h):
    """2025 年 4h 教師ラベルとの一致率 (pattern の cur 部分と label_norm 比較)。"""
    is_2025_arr = np.array([(t.year == 2025) for t in df5m_index])
    if not is_2025_arr.any():
        return {"match_rate": None, "note": "2025 年データなし"}
    labels_4h = labels_4h.copy()
    if labels_4h["timestamp_utc"].dt.tz is not None:
        labels_4h["timestamp_utc"] = labels_4h["timestamp_utc"].dt.tz_localize(None)
    aligned = pd.merge_asof(
        pd.DataFrame({"timestamp": df5m_index}).sort_values("timestamp"),
        labels_4h[["timestamp_utc", "label_norm"]].rename(columns={"timestamp_utc": "timestamp"}).sort_values("timestamp"),
        on="timestamp", direction="backward"
    )
    expected = aligned["label_norm"].values
    actual = np.array(["none" if p == "none" else p.split("->")[1] for p in pattern_label])
    valid = is_2025_arr & (expected != "none") & pd.notna(expected) & (actual != "none")
    if valid.sum() == 0:
        return {"match_rate": None, "note": "valid サンプルなし"}
    matches = ((actual == expected) & valid).sum()
    return {"match_rate": float(matches / valid.sum()), "matches": int(matches), "total": int(valid.sum())}


# ── 5 ケース並走 csv 出力 ─────────────────────

def write_monthly_csv_5cases(pattern_labels_by_case, df5m_index, out_path):
    """1 csv 内で 5 ケース並走列出力 (timestamp / OR_judge / vote2_judge / vote3_judge / vote4_judge / AND_judge)。"""
    df = pd.DataFrame({"timestamp": df5m_index})
    for thr, name in VOTE_CASES:
        df[f"{name}_judge"] = pattern_labels_by_case[name]
    df["month"] = df["timestamp"].dt.to_period("M").astype(str)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)


# ── md 出力 ─────────────────────────────

def write_validation_report(persistence_by_case, hits_24_by_case, match_2025_by_case, out_path):
    lines = ["# 段階3 (3-1) 検証レポート", ""]
    lines.append(f"作成日: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("入力: stage2_final_judgment_set.json (30 件 / 6 パターン × M=5)")
    lines.append("評価: 5 ケース並走 (OR / vote2 / vote3 / vote4 / AND) × 6 パターン衝突解決 (乖離 pt 最大)")
    lines.append("")

    lines.append("## ケース別 合格基準サマリ")
    lines.append("| ケース | 24 サンプルヒット | 2025 年一致率 | 持続発火件数 | 持続中央値平均 (バー) |")
    lines.append("|---|---|---|---:|---:|")
    for thr, name in VOTE_CASES:
        h = hits_24_by_case.get(name, {})
        m = match_2025_by_case.get(name, {})
        p = persistence_by_case.get(name, {})
        h_str = (f"{h.get('hits', 0)}/{h.get('total', 0)} ({h.get('hit_rate', 0)*100:.1f}%)"
                 if h.get("hit_rate") is not None else h.get("note", "?"))
        m_str = (f"{m.get('match_rate', 0)*100:.1f}% ({m.get('matches', 0)}/{m.get('total', 0)})"
                 if m.get("match_rate") is not None else m.get("note", "?"))
        n_runs_total = sum(v["n_runs"] for v in p.values())
        median_avg = float(np.mean([v["median_bars"] for v in p.values()])) if p else 0
        lines.append(f"| {name} | {h_str} | {m_str} | {n_runs_total} | {median_avg:.1f} |")
    lines.append("")

    lines.append(f"## 24 サンプル miss 詳細 (各ケース・hit 失敗分)")
    for thr, name in VOTE_CASES:
        h = hits_24_by_case.get(name, {})
        misses = h.get("miss", [])
        lines.append(f"\n### {name} (miss {len(misses)} 件)")
        for m in misses:
            lines.append(f"- {m}")
    lines.append("")

    lines.append(f"## ケース × パターン別 持続安定性 (目標 {PERSISTENCE_TARGET_BARS} バー = 2 時間)")
    for thr, name in VOTE_CASES:
        p = persistence_by_case.get(name, {})
        if not p:
            continue
        lines.append(f"\n### {name}")
        lines.append("| パターン | 発火件数 | 中央値 (バー) | 平均 | 最大 | 目標達成 |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for ptn in PATTERNS:
            v = p.get(ptn, {})
            lines.append(f"| {ptn} | {v.get('n_runs', 0)} | {v.get('median_bars', 0):.1f} | "
                         f"{v.get('mean_bars', 0):.1f} | {v.get('max_bars', 0)} | {v.get('ge_target', 0)} |")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


# ── メイン ─────────────────────────────

def main():
    print("入力ロード...", flush=True)
    final_set = load_final_judgment_set()
    labels_4h = load_labels()
    df5m = pd.read_csv(DATA_5M, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    df_per_tf = {
        "5m": df5m,
        "15m": resample_ohlcv(df5m, "15min"),
        "30m": resample_ohlcv(df5m, "30min"),
        "1h": resample_ohlcv(df5m, "1h"),
        "4h": resample_ohlcv(df5m, "4h"),
        "1d": resample_ohlcv(df5m, "1D"),
    }

    print("必要カラム抽出...", flush=True)
    required_cols = collect_required_cols(final_set)
    print(f"  抽出: {len(required_cols)} 列", flush=True)

    print("per-bar 5m 構築 + ffill...", flush=True)
    per_bar_5m = build_per_bar_for_required_cols(required_cols, df_per_tf)
    print(f"  完了: {len(per_bar_5m)} 列", flush=True)

    print("二値化...", flush=True)
    binarized = binarize_per_5m(per_bar_5m)

    print("判定式 30 件 発火マスク構築...", flush=True)
    n_5m = len(df5m)
    judgment_masks = build_judgment_fire_masks(final_set, binarized, n_5m)

    print("ケース別評価 + 衝突解決...", flush=True)
    persistence_by_case = {}
    hits_24_by_case = {}
    match_2025_by_case = {}
    pattern_labels_by_case = {}
    for vote_thr, name in VOTE_CASES:
        print(f"  ケース {name} (vote >= {vote_thr})...", flush=True)
        pattern_fires = vote_per_pattern(judgment_masks, vote_thr, n_5m)
        pattern_label = resolve_conflicts(pattern_fires, final_set, n_5m)
        pattern_labels_by_case[name] = pattern_label
        persistence_by_case[name] = evaluate_persistence(pattern_label)
        hits_24_by_case[name] = evaluate_24_samples(pattern_label, df5m.index)
        match_2025_by_case[name] = evaluate_2025_match(pattern_label, df5m.index, labels_4h)

    print(f"5 ケース並走 csv 出力: {OUT_MONTHLY}", flush=True)
    write_monthly_csv_5cases(pattern_labels_by_case, df5m.index, OUT_MONTHLY)

    print(f"レポート出力: {OUT_MD}", flush=True)
    write_validation_report(persistence_by_case, hits_24_by_case, match_2025_by_case, OUT_MD)
    print("DONE")


if __name__ == "__main__":
    main()
