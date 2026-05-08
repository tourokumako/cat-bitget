"""analyze_stage1c_meta.py — 段階1-C 着手前のメタ分析

構造的特徴量 (C-1〜C-4) について、段階1-C 本実装の N・時間軸・感度パラメータを
データから決めるための事前分析。

4つの処理:
  1. 自己相関分析: 特徴量 × 軸 × N × lag 1〜100 の自己相関
     → 「自己相関 0.5 を切る lag」を推奨独立観測窓とする
  2. ラベル分離度: 教師ラベル全 4,745 バーで up/rg/dn 別 Q1〜Q3 重複度
  3. パターン特異性 (3系統): 全件 / 短命のみ / 通常のみ
     - 短命: prev_run ≤ 4 (up/dn) または ≤ 6 (rg)
  4. 段階1-B との相関 (案A 全期間 + 案B 切替点のみ・両方併記)
     - stage1b の swing_high/low_dist_pct_W (W=10/20/50) との Pearson 相関
     - |r_all - r_tx| > 0.3 で乖離マーク ⚠️

対象軸: 5m / 15m / 30m / 1h / 4h / 1d (6軸)
N 候補: 50 / 100 / 200 (3 candidates・C-2 は N 非依存)
感度パラメータ:
  TOUCH_THRESHOLDS [0.003/0.005/0.010/0.020] (C-1 のみ)
  VOLUME_BIN_COUNTS [20/50/100] × VA_RATIOS [0.60/0.70/0.80] (C-3 のみ)

出力: results/regime_label_analysis/stage1c_meta_analysis.md
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import pandas as pd
import numpy as np

from analyze_transition_indicators import (
    load_labels,
    run_length_encode,
    extract_transitions,
    attach_indicators,
)
from analyze_stage1a_meta import overlap_3way, overlap_pair
from structure_features import (
    N_CANDIDATES,
    TOUCH_THRESHOLDS,
    VOLUME_BIN_COUNTS,
    VA_RATIOS,
    compute_features_for_N,
    compute_c2_only,
    category_of_column,
)
# 段階1-B との相関 (処理4) 用
from shape_features import (
    swing_high_dist_pct_W,
    swing_low_dist_pct_W,
)

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
OUT_DIR = BASE / "results/regime_label_analysis"
OUT_MD = OUT_DIR / "stage1c_meta_analysis.md"

DEFAULT_TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]
TIMEFRAMES = os.environ.get("STAGE1C_TIMEFRAMES", ",".join(DEFAULT_TIMEFRAMES)).split(",")
MAX_LAG = 100
AC_THRESHOLDS = [0.7, 0.5, 0.3]
OVERLAP_THRESHOLDS = [0.3, 0.5, 0.7]
SHORT_THRESHOLD = {"up": 4, "rg": 6, "dn": 4}
STAGE1B_W_CANDIDATES = [10, 20, 50]
DIVERGENCE_THRESHOLD = 0.3  # |r_all - r_tx| > 0.3 で乖離マーク


def resample_ohlcv(df5m: pd.DataFrame, rule: str) -> pd.DataFrame:
    return df5m.resample(rule).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna(subset=["close"])


def compute_features_per_tf(df_per_tf: dict[str, pd.DataFrame]):
    """全軸 × 全 N で structure 特徴量を計算。
    Returns:
        structure_per_tf: {tf: {N: DataFrame_features}}
        c2_per_tf: {tf: DataFrame_c2_features}
        swing_per_tf: {tf: {W: DataFrame_swing_features}}  ← 処理4 用
    """
    structure_per_tf: dict[str, dict[int, pd.DataFrame]] = {}
    c2_per_tf: dict[str, pd.DataFrame] = {}
    swing_per_tf: dict[str, dict[int, pd.DataFrame]] = {}

    for tf, df in df_per_tf.items():
        print(f"  {tf}: structure 計算開始...")
        structure_per_tf[tf] = {}
        for N in N_CANDIDATES:
            structure_per_tf[tf][N] = compute_features_for_N(df, N)
        c2_per_tf[tf] = compute_c2_only(df)
        # 段階1-B swing 系 (処理4 用)
        swing_per_tf[tf] = {}
        for W in STAGE1B_W_CANDIDATES:
            swing_df = pd.DataFrame(index=df.index)
            swing_df[f"swing_high_dist_pct_W_W{W}"] = swing_high_dist_pct_W(df, W)
            swing_df[f"swing_low_dist_pct_W_W{W}"] = swing_low_dist_pct_W(df, W)
            swing_per_tf[tf][W] = swing_df
        print(f"  {tf}: 完了")
    return structure_per_tf, c2_per_tf, swing_per_tf


def autocorrelation_analysis(structure_per_tf, c2_per_tf) -> pd.DataFrame:
    """各特徴量 × tf × N の自己相関。"""
    rows = []
    for tf, by_N in structure_per_tf.items():
        for N, feat_df in by_N.items():
            for fname in feat_df.columns:
                s = feat_df[fname].dropna()
                if len(s) < MAX_LAG * 2:
                    continue
                if s.nunique() < 2:
                    continue
                row = {"feature": fname, "tf": tf, "N": N,
                       "category": category_of_column(fname)}
                for lag in [1, 3, 6, 12, 24, 50, 100]:
                    if lag <= MAX_LAG:
                        row[f"ac_lag{lag}"] = s.autocorr(lag=lag)
                for thr in AC_THRESHOLDS:
                    first_below = None
                    for lag in range(1, MAX_LAG + 1):
                        val = s.autocorr(lag=lag)
                        if pd.notna(val) and abs(val) < thr:
                            first_below = lag
                            break
                    row[f"first_below_{thr}"] = first_below if first_below is not None else f">{MAX_LAG}"
                rows.append(row)
    # C-2 (N 非依存・別途)
    for tf, c2_df in c2_per_tf.items():
        for fname in c2_df.columns:
            s = c2_df[fname].dropna()
            if len(s) < MAX_LAG * 2:
                continue
            if s.nunique() < 2:
                continue
            row = {"feature": fname, "tf": tf, "N": "—",
                   "category": category_of_column(fname)}
            for lag in [1, 3, 6, 12, 24, 50, 100]:
                if lag <= MAX_LAG:
                    row[f"ac_lag{lag}"] = s.autocorr(lag=lag)
            for thr in AC_THRESHOLDS:
                first_below = None
                for lag in range(1, MAX_LAG + 1):
                    val = s.autocorr(lag=lag)
                    if pd.notna(val) and abs(val) < thr:
                        first_below = lag
                        break
                row[f"first_below_{thr}"] = first_below if first_below is not None else f">{MAX_LAG}"
            rows.append(row)
    return pd.DataFrame(rows)


def attach_features_to_labels(labels_df: pd.DataFrame, structure_per_tf, c2_per_tf, swing_per_tf) -> pd.DataFrame:
    """教師ラベル 4h バーに、各軸 × 各 N × 全 structure 特徴量 + swing を attach。"""
    labels_df = labels_df.copy()
    if labels_df["timestamp_utc"].dt.tz is not None:
        labels_df["timestamp_utc"] = labels_df["timestamp_utc"].dt.tz_localize(None)

    labels_df["ts_5m"] = labels_df["timestamp_utc"] + pd.Timedelta(minutes=235)
    labels_df["ts_15m"] = labels_df["timestamp_utc"] + pd.Timedelta(minutes=225)
    labels_df["ts_30m"] = labels_df["timestamp_utc"] + pd.Timedelta(minutes=210)
    labels_df["ts_1h"] = labels_df["timestamp_utc"] + pd.Timedelta(hours=3)
    labels_df["ts_4h"] = labels_df["timestamp_utc"]
    labels_df["ts_1d"] = labels_df["timestamp_utc"].dt.floor("1D")

    for tf, by_N in structure_per_tf.items():
        for N, feat_df in by_N.items():
            suffix = f"{tf}_N{N}_struct"
            labels_df = attach_indicators(labels_df, feat_df, f"ts_{tf}", suffix)
    for tf, c2_df in c2_per_tf.items():
        suffix = f"{tf}_c2"
        labels_df = attach_indicators(labels_df, c2_df, f"ts_{tf}", suffix)
    for tf, by_W in swing_per_tf.items():
        for W, sw_df in by_W.items():
            suffix = f"{tf}_W{W}_swing"
            labels_df = attach_indicators(labels_df, sw_df, f"ts_{tf}", suffix)
    return labels_df


def attach_run_metadata(labels_df: pd.DataFrame) -> pd.DataFrame:
    """各バーが属する run の長さと is_short フラグを attach。
    短命: run_len ≤ SHORT_THRESHOLD[label_norm]
    """
    out = labels_df.copy()
    labels = out["label_norm"].tolist()
    n = len(labels)
    run_lens = np.zeros(n, dtype=int)
    is_shorts = np.zeros(n, dtype=int)
    i = 0
    while i < n:
        j = i
        while j < n and labels[j] == labels[i]:
            j += 1
        run_len = j - i
        for k in range(i, j):
            run_lens[k] = run_len
            thr = SHORT_THRESHOLD.get(labels[k], 99)
            is_shorts[k] = 1 if run_len <= thr else 0
        i = j
    out["run_len"] = run_lens
    out["is_short"] = is_shorts
    return out


def _structure_columns_in(labels_attached: pd.DataFrame) -> list[str]:
    """attach 後カラムから structure (C-1/C-2/C-3/C-4) のオリジナル名を再構成して返す。
    attach_indicators の suffix 仕様により col 名は f"{base}__{suffix}" になる前提。
    """
    cols = []
    for col in labels_attached.columns:
        if "__" not in col:
            continue
        base, suffix = col.rsplit("__", 1)
        if suffix.endswith("_struct") or suffix.endswith("_c2"):
            cat = category_of_column(base)
            if cat in ("C1_resistsupp", "C2_pivot", "C3_volume", "C4_fib", "C4_fib_v2"):
                cols.append(col)
    return cols


def _swing_columns_in(labels_attached: pd.DataFrame) -> list[str]:
    cols = []
    for col in labels_attached.columns:
        if "__" not in col:
            continue
        _, suffix = col.rsplit("__", 1)
        if suffix.endswith("_swing"):
            cols.append(col)
    return cols


def label_separation_analysis(labels_attached: pd.DataFrame, subset: str = "all") -> pd.DataFrame:
    """教師バー up/rg/dn 別 IQR 重複度。
    subset: "all" / "short" / "normal" — is_short フラグでフィルタ。
    """
    if subset == "short":
        df = labels_attached[labels_attached.get("is_short", 0) == 1]
    elif subset == "normal":
        df = labels_attached[labels_attached.get("is_short", 0) == 0]
    else:
        df = labels_attached

    rows = []
    for col in _structure_columns_in(labels_attached):
        base, suffix = col.rsplit("__", 1)
        if suffix.endswith("_struct"):
            parts = suffix[:-len("_struct")].split("_")
            tf = parts[0]
            N = parts[1].replace("N", "") if len(parts) > 1 else "—"
        else:
            tf = suffix.replace("_c2", "")
            N = "—"
        by_label = {
            "up": df[df["label_norm"] == "up"][col].dropna(),
            "rg": df[df["label_norm"] == "rg"][col].dropna(),
            "dn": df[df["label_norm"] == "dn"][col].dropna(),
        }
        if any(len(s) < 2 or s.nunique() < 2 for s in by_label.values()):
            continue
        res = overlap_3way(by_label)
        rows.append({
            "subset": subset,
            "feature": base,
            "tf": tf,
            "N": N,
            "category": category_of_column(base),
            "overlap_ratio": res["overlap_ratio"],
        })
    return pd.DataFrame(rows)


def pattern_specificity_analysis(labels_attached: pd.DataFrame, transitions: list, subset: str) -> pd.DataFrame:
    """切替点 t=0 値で 6遷移パターン間 IQR 重複度。"""
    selected_tx = []
    for ev in transitions:
        prev_thr = SHORT_THRESHOLD.get(ev["prev"], 99)
        is_short = ev["prev_len"] <= prev_thr
        if subset == "all":
            selected_tx.append(ev)
        elif subset == "short" and is_short:
            selected_tx.append(ev)
        elif subset == "normal" and not is_short:
            selected_tx.append(ev)

    cols = _structure_columns_in(labels_attached)
    if not cols or not selected_tx:
        return pd.DataFrame()

    pattern_rows = []
    for ev in selected_tx:
        t = ev["t_idx"]
        row = {"pattern": f"{ev['prev']}->{ev['cur']}"}
        for c in cols:
            row[c] = labels_attached.iloc[t][c]
        pattern_rows.append(row)
    df = pd.DataFrame(pattern_rows)

    patterns = ["up->dn", "dn->up", "up->rg", "rg->up", "rg->dn", "dn->rg"]
    rows = []
    for col in cols:
        base, suffix = col.rsplit("__", 1)
        if suffix.endswith("_struct"):
            parts = suffix[:-len("_struct")].split("_")
            tf = parts[0]
            N = parts[1].replace("N", "") if len(parts) > 1 else "—"
        else:
            tf = suffix.replace("_c2", "")
            N = "—"
        by_pattern = {p: df[df["pattern"] == p][col].dropna() for p in patterns}
        for target in patterns:
            others = [s for p, s in by_pattern.items() if p != target]
            if len(by_pattern[target]) < 5:
                continue
            overlaps = [overlap_pair(by_pattern[target], o) for o in others if len(o) >= 5]
            overlaps = [o for o in overlaps if pd.notna(o)]
            if not overlaps:
                continue
            rows.append({
                "subset": subset,
                "pattern": target,
                "feature": base,
                "tf": tf,
                "N": N,
                "category": category_of_column(base),
                "n": len(by_pattern[target]),
                "mean_overlap_vs_others": float(np.mean(overlaps)),
            })
    return pd.DataFrame(rows)


def stage1b_correlation_analysis(labels_attached: pd.DataFrame, transitions: list) -> pd.DataFrame:
    """処理4: 段階1-B swing 系との相関 (案A 全期間 + 案B 切替点)"""
    struct_cols = _structure_columns_in(labels_attached)
    swing_cols = _swing_columns_in(labels_attached)
    if not struct_cols or not swing_cols:
        return pd.DataFrame()

    t_idxs = [ev["t_idx"] for ev in transitions]
    rows = []
    for sc in struct_cols:
        s_full = labels_attached[sc]
        s_tx = labels_attached.iloc[t_idxs][sc]
        max_r_all = 0.0
        max_r_tx = 0.0
        max_b_all = ""
        max_b_tx = ""
        for bc in swing_cols:
            b_full = labels_attached[bc]
            b_tx = labels_attached.iloc[t_idxs][bc]
            r_all = s_full.corr(b_full)
            r_tx = s_tx.corr(b_tx)
            if pd.notna(r_all) and abs(r_all) > abs(max_r_all):
                max_r_all = r_all
                max_b_all = bc
            if pd.notna(r_tx) and abs(r_tx) > abs(max_r_tx):
                max_r_tx = r_tx
                max_b_tx = bc
        # 同一 swing カラムでの A/B 比較も保持 (max_r_all のカラムで両方計算)
        if max_b_all:
            r_tx_at_a = labels_attached.iloc[t_idxs][sc].corr(labels_attached.iloc[t_idxs][max_b_all])
        else:
            r_tx_at_a = np.nan
        divergence = abs(abs(max_r_all) - abs(r_tx_at_a)) if pd.notna(r_tx_at_a) else None
        warn = "⚠️" if (divergence is not None and divergence > DIVERGENCE_THRESHOLD) else ""
        base, suffix = sc.rsplit("__", 1)
        rows.append({
            "c_feature": base,
            "c_suffix": suffix,
            "category": category_of_column(base),
            "max_b_all": max_b_all.rsplit("__", 1)[0] if "__" in max_b_all else max_b_all,
            "max_r_all": max_r_all,
            "max_r_tx_at_a": r_tx_at_a,
            "divergence_a_vs_tx": divergence,
            "warn": warn,
            "max_b_tx": max_b_tx.rsplit("__", 1)[0] if "__" in max_b_tx else max_b_tx,
            "max_r_tx": max_r_tx,
        })
    return pd.DataFrame(rows)


def fmt(x):
    if isinstance(x, str):
        return x
    if pd.isna(x):
        return "—"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    if abs(x) >= 100:
        return f"{x:.1f}"
    if abs(x) >= 10:
        return f"{x:.2f}"
    return f"{x:.3f}"


def write_md(ac_df, sep_dfs, spec_dfs, corr_df, out_path):
    lines = []
    lines.append("# 段階1-C メタ分析: 構造的特徴量の N・時間軸・感度パラメータ決定")
    lines.append("")
    lines.append("段階1-C 本実装の前に、構造的特徴量について以下を**データで**決める。")
    lines.append("")
    lines.append(f"- N: 自己相関で独立観測窓を測る ({N_CANDIDATES} 候補)")
    lines.append(f"- 時間軸: ラベル分離度で軸別の判定力を測る ({TIMEFRAMES})")
    lines.append(f"- タッチ閾値 (C-1): {[f'{t*100:.1f}%' for t in TOUCH_THRESHOLDS]} の感度分析")
    lines.append(f"- ビン数 (C-3): {VOLUME_BIN_COUNTS} × VA比率: {VA_RATIOS} の感度分析")
    lines.append("- 段階1-B (swing 系) との相関: 案A 全期間 + 案B 切替点 を併記、|乖離| > 0.3 で ⚠️")
    lines.append("")
    lines.append("確定パラメータ: 5点 fractal / C-2 同軸前1バー")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === 処理 1 ===
    lines.append("## 処理 1: 自己相関分析")
    lines.append("")
    lines.append("### 1-A. カテゴリ別 N 推奨値 (first<0.5 切り lag の中央値)")
    lines.append("")
    lines.append("| TF | カテゴリ | first<0.7 中央 | first<0.5 中央 | first<0.3 中央 | 100超え件数 |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for tf in TIMEFRAMES:
        for cat in ["C1_resistsupp", "C2_pivot", "C3_volume", "C4_fib"]:
            sub = ac_df[(ac_df["tf"] == tf) & (ac_df["category"] == cat)]
            if sub.empty:
                continue

            def median_or_dash(s):
                numeric = pd.to_numeric(s, errors="coerce")
                v = numeric.median()
                return fmt(v) if pd.notna(v) else "—"

            over_100 = (sub["first_below_0.5"].astype(str) == f">{MAX_LAG}").sum()
            lines.append(
                f"| {tf} | {cat} | "
                f"{median_or_dash(sub['first_below_0.7'])} | "
                f"{median_or_dash(sub['first_below_0.5'])} | "
                f"{median_or_dash(sub['first_below_0.3'])} | {over_100} |"
            )
    lines.append("")

    lines.append("### 1-B. lag>100 の特徴量数 (N 推奨候補から除外対象)")
    lines.append("")
    lines.append("| TF | N | 100超え件数 | 全件 |")
    lines.append("|---|---:|---:|---:|")
    for tf in TIMEFRAMES:
        for N in [*N_CANDIDATES, "—"]:
            sub = ac_df[(ac_df["tf"] == tf) & (ac_df["N"] == (str(N) if N != "—" else "—"))]
            if sub.empty:
                continue
            over = (sub["first_below_0.5"].astype(str) == f">{MAX_LAG}").sum()
            total = len(sub)
            lines.append(f"| {tf} | {N} | {over} | {total} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === 処理 2 ===
    lines.append("## 処理 2: ラベル分離度 (3系統: 全件 / 短命 / 通常)")
    lines.append("")
    for subset_label, subset_jp in [("all", "全件"), ("short", "短命のみ"), ("normal", "通常のみ")]:
        sep_df = sep_dfs.get(subset_label, pd.DataFrame())
        lines.append(f"### 2-{subset_label.upper()}. {subset_jp}")
        lines.append("")
        if sep_df.empty:
            lines.append("(該当なし)")
            lines.append("")
            continue

        lines.append("#### 重複度ランキング (上位 30)")
        lines.append("")
        lines.append("| Rank | Feature | TF | N | Cat | overlap |")
        lines.append("|---:|---|---|---:|---|---:|")
        sep_sorted = sep_df.dropna(subset=["overlap_ratio"]).sort_values("overlap_ratio").reset_index(drop=True)
        for i, r in sep_sorted.head(30).iterrows():
            lines.append(f"| {i+1} | `{r['feature']}` | {r['tf']} | {r['N']} | {r['category']} | {fmt(r['overlap_ratio'])} |")
        lines.append("")

        lines.append("#### 重複度閾値別 合格件数")
        lines.append("")
        lines.append("| 閾値 | 合格 | 全体に占める割合 |")
        lines.append("|---|---:|---:|")
        total = sep_df["overlap_ratio"].notna().sum()
        for thr in OVERLAP_THRESHOLDS:
            n = (sep_df["overlap_ratio"] < thr).sum()
            ratio = n / total * 100 if total > 0 else 0
            lines.append(f"| < {thr} | {n} | {ratio:.1f}% |")
        lines.append("")

        lines.append("#### 軸別合格件数 (重複度 < 0.5 基準)")
        lines.append("")
        lines.append("| TF | 合格件数 | 全件 |")
        lines.append("|---|---:|---:|")
        for tf in TIMEFRAMES:
            sub = sep_df[sep_df["tf"] == tf]
            n_pass = (sub["overlap_ratio"] < 0.5).sum()
            n_total = sub["overlap_ratio"].notna().sum()
            lines.append(f"| {tf} | {n_pass} | {n_total} |")
        lines.append("")

        lines.append("#### カテゴリ別合格件数 (重複度 < 0.5 基準)")
        lines.append("")
        lines.append("| カテゴリ | 合格件数 | 全件 |")
        lines.append("|---|---:|---:|")
        for cat in ["C1_resistsupp", "C2_pivot", "C3_volume", "C4_fib"]:
            sub = sep_df[sep_df["category"] == cat]
            n_pass = (sub["overlap_ratio"] < 0.5).sum()
            n_total = sub["overlap_ratio"].notna().sum()
            lines.append(f"| {cat} | {n_pass} | {n_total} |")
        lines.append("")
    lines.append("---")
    lines.append("")

    # === 処理 3 ===
    lines.append("## 処理 3: パターン特異性 (3系統)")
    lines.append("")

    # 3-0. 各パターン × subset の n 一覧表
    lines.append("### 3-0. 各パターン × subset の切替点件数 (n)")
    lines.append("")
    lines.append("| Pattern | n_all | n_short | n_normal |")
    lines.append("|---|---:|---:|---:|")
    for p in ["up->dn", "dn->up", "up->rg", "rg->up", "rg->dn", "dn->rg"]:
        n_per_subset = {}
        for subset_label in ["all", "short", "normal"]:
            sd = spec_dfs.get(subset_label, pd.DataFrame())
            if sd.empty:
                n_per_subset[subset_label] = 0
                continue
            sub = sd[sd["pattern"] == p]
            n_per_subset[subset_label] = int(sub["n"].iloc[0]) if len(sub) > 0 else 0
        lines.append(f"| {p} | {n_per_subset['all']} | {n_per_subset['short']} | {n_per_subset['normal']} |")
    lines.append("")

    for subset_label, subset_jp in [("all", "全件"), ("short", "短命のみ"), ("normal", "通常のみ")]:
        spec_df = spec_dfs.get(subset_label, pd.DataFrame())
        lines.append(f"### 3-{subset_label.upper()}. {subset_jp}")
        lines.append("")
        if spec_df.empty:
            lines.append("(該当なし)")
            lines.append("")
            continue
        for p in ["up->dn", "dn->up", "up->rg", "rg->up", "rg->dn", "dn->rg"]:
            sub = spec_df[spec_df["pattern"] == p].dropna(subset=["mean_overlap_vs_others"])
            sub = sub.sort_values("mean_overlap_vs_others")
            n_evt = int(sub["n"].iloc[0]) if len(sub) > 0 else 0
            lines.append(f"#### {p} (n={n_evt}) — TOP 5")
            lines.append("")
            if sub.empty:
                lines.append("(切替点なし)")
                lines.append("")
                continue
            lines.append("| Rank | Feature | TF | N | Cat | mean_overlap |")
            lines.append("|---:|---|---|---:|---|---:|")
            for i, r in sub.head(5).reset_index(drop=True).iterrows():
                lines.append(f"| {i+1} | `{r['feature']}` | {r['tf']} | {r['N']} | {r['category']} | {fmt(r['mean_overlap_vs_others'])} |")
            lines.append("")

        lines.append(f"#### 3-{subset_label.upper()}-summary 重複度閾値別 合格件数")
        lines.append("")
        lines.append("| 閾値 | 合格件数 |")
        lines.append("|---|---:|")
        total = spec_df["mean_overlap_vs_others"].notna().sum()
        for thr in OVERLAP_THRESHOLDS:
            n = (spec_df["mean_overlap_vs_others"] < thr).sum()
            ratio = n / total * 100 if total > 0 else 0
            lines.append(f"| < {thr} | {n} ({ratio:.1f}%) |")
        lines.append("")
    lines.append("---")
    lines.append("")

    # === 処理 4 ===
    lines.append("## 処理 4: 段階1-B (swing 系) との相関")
    lines.append("")
    lines.append("各構造特徴量について、段階1-B の `swing_high/low_dist_pct_W` (W=10/20/50) のうち")
    lines.append("**最大相関** を取った swing カラムを記録。")
    lines.append("")
    lines.append("- **r_all (案A)**: 全教師時系列での Pearson 相関")
    lines.append("- **r_tx_at_a (案B)**: 案A で選ばれた swing カラムを切替点 198 点で再相関")
    lines.append("- **divergence**: |r_all| と |r_tx_at_a| の差")
    lines.append(f"- **⚠️**: divergence > {DIVERGENCE_THRESHOLD}（切替点で独立挙動の可能性・段階2 で要注意）")
    lines.append("- **r_tx 単独最大**: 切替点のみで最大相関を取った swing カラム (案B 単独)")
    lines.append("")

    lines.append("### 4-A. 重複懸念上位 (|r_all| 大きい順・上位 30)")
    lines.append("")
    lines.append("| Rank | C feature | suffix | Cat | best_swing(A) | r_all | r_tx_at_a | divergence | ⚠️ | best_swing(B) | r_tx |")
    lines.append("|---:|---|---|---|---|---:|---:|---:|---|---|---:|")
    if not corr_df.empty:
        sorted_corr = corr_df.dropna(subset=["max_r_all"]).copy()
        sorted_corr["abs_r_all"] = sorted_corr["max_r_all"].abs()
        sorted_corr = sorted_corr.sort_values("abs_r_all", ascending=False).reset_index(drop=True)
        for i, r in sorted_corr.head(30).iterrows():
            lines.append(
                f"| {i+1} | `{r['c_feature']}` | {r['c_suffix']} | {r['category']} | "
                f"`{r['max_b_all']}` | {fmt(r['max_r_all'])} | {fmt(r['max_r_tx_at_a'])} | "
                f"{fmt(r['divergence_a_vs_tx'])} | {r['warn']} | "
                f"`{r['max_b_tx']}` | {fmt(r['max_r_tx'])} |"
            )
    lines.append("")

    lines.append("### 4-B. 乖離マーク (⚠️) 一覧 — 段階2 で「切替点で独立に効く」可能性あり")
    lines.append("")
    if not corr_df.empty:
        warn_df = corr_df[corr_df["warn"] == "⚠️"].copy()
        if warn_df.empty:
            lines.append("(該当なし)")
        else:
            warn_df = warn_df.sort_values("divergence_a_vs_tx", ascending=False).reset_index(drop=True)
            lines.append("| Rank | C feature | suffix | Cat | r_all | r_tx_at_a | divergence |")
            lines.append("|---:|---|---|---|---:|---:|---:|")
            for i, r in warn_df.iterrows():
                lines.append(
                    f"| {i+1} | `{r['c_feature']}` | {r['c_suffix']} | {r['category']} | "
                    f"{fmt(r['max_r_all'])} | {fmt(r['max_r_tx_at_a'])} | {fmt(r['divergence_a_vs_tx'])} |"
                )
    lines.append("")

    lines.append("### 4-C. 重複度閾値別 合格件数 (|r_all| < threshold)")
    lines.append("")
    lines.append("| 閾値 | 合格 | 全体に占める割合 |")
    lines.append("|---|---:|---:|")
    if not corr_df.empty:
        total = corr_df["max_r_all"].notna().sum()
        for thr in [0.3, 0.5, 0.7]:
            n = (corr_df["max_r_all"].abs() < thr).sum()
            ratio = n / total * 100 if total > 0 else 0
            lines.append(f"| < {thr} | {n} | {ratio:.1f}% |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === まこさんが決めること ===
    lines.append("## まこさんが決めること")
    lines.append("")
    lines.append("1. **N の採用値**: 処理 1 を見て、各カテゴリ × 軸でどの N を採るか")
    lines.append("2. **タッチ閾値 (C-1)**: 処理 2/3 の感度分析を見て 0.3/0.5/1.0/2.0% のどれか")
    lines.append("3. **ビン数 + VA比率 (C-3)**: 処理 2/3 の感度分析を見て決定")
    lines.append("4. **対象軸**: 処理 2-C を見て 5m/15m/30m/1h/4h/1d のどれに絞るか")
    lines.append("5. **重複度閾値**: ラベル分離度・パターン特異性で 0.3/0.5/0.7 のどれか")
    lines.append("6. **段階1-B 重複扱い**: 処理 4-A/B/C を見て |r| ≥ ? を重複として除外するか")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


def main():
    print("ラベル + 切替点抽出...")
    labels = load_labels()
    runs = run_length_encode(labels["label_norm"].tolist())
    transitions = extract_transitions(runs)
    print(f"  切替点数: {len(transitions)}")

    print("OHLCV resample (6軸)...")
    df5m = pd.read_csv(DATA_5M, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    all_dfs = {
        "5m": df5m,
        "15m": resample_ohlcv(df5m, "15min"),
        "30m": resample_ohlcv(df5m, "30min"),
        "1h": resample_ohlcv(df5m, "1h"),
        "4h": resample_ohlcv(df5m, "4h"),
        "1d": resample_ohlcv(df5m, "1D"),
    }
    df_per_tf = {tf: all_dfs[tf] for tf in TIMEFRAMES if tf in all_dfs}
    print(f"  対象軸: {list(df_per_tf.keys())}")
    for tf, d in df_per_tf.items():
        print(f"  {tf}: {len(d)} bars")

    print("構造特徴量計算 (軸 × N)...")
    structure_per_tf, c2_per_tf, swing_per_tf = compute_features_per_tf(df_per_tf)

    print("自己相関分析...")
    ac_df = autocorrelation_analysis(structure_per_tf, c2_per_tf)
    print(f"  行数: {len(ac_df)}")

    print("attach 教師ラベル...")
    labels_attached = attach_features_to_labels(labels, structure_per_tf, c2_per_tf, swing_per_tf)
    print(f"  attach 後カラム数: {len(labels_attached.columns)}")

    print("run metadata attach (短命/通常判定用)...")
    labels_attached = attach_run_metadata(labels_attached)
    n_short = int((labels_attached["is_short"] == 1).sum())
    n_normal = int((labels_attached["is_short"] == 0).sum())
    print(f"  短命: {n_short} / 通常: {n_normal}")

    print("ラベル分離度 (3系統)...")
    sep_dfs = {}
    for subset in ["all", "short", "normal"]:
        sep_dfs[subset] = label_separation_analysis(labels_attached, subset=subset)
        print(f"  {subset}: {len(sep_dfs[subset])} 行")

    print("パターン特異性 (3系統)...")
    spec_dfs = {}
    for subset in ["all", "short", "normal"]:
        spec_dfs[subset] = pattern_specificity_analysis(labels_attached, transitions, subset)
        print(f"  {subset}: {len(spec_dfs[subset])} 行")

    print("段階1-B 相関 (処理4・案A+案B)...")
    corr_df = stage1b_correlation_analysis(labels_attached, transitions)
    print(f"  行数: {len(corr_df)}")

    print(f"md 出力: {OUT_MD}")
    write_md(ac_df, sep_dfs, spec_dfs, corr_df, OUT_MD)
    print("DONE")


if __name__ == "__main__":
    main()
