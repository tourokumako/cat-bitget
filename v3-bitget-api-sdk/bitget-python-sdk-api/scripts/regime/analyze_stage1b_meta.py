"""analyze_stage1b_meta.py — 段階1-B 着手前のメタ分析

形状特徴量 (B-1〜B-5) について、段階1-B 本実装の窓 W・時間軸・対象特徴量を
データから決めるための事前分析。

3つの処理:
  1. 自己相関分析: 形状特徴量 × 軸 × W × lag 1〜100 の自己相関
     → 「自己相関 0.5 を切る lag」を推奨独立観測窓とする
     → lag 100 まで切らない場合は ">100" と記録し N 推奨候補から除外
  2. ラベル分離度: 教師ラベル全 4,745 バーで up/rg/dn 別 Q1〜Q3 重複度
  3. パターン特異性 (3系統): 全件 / 短命のみ / 通常のみ で計算
     - 短命: prev_run ≤ 4 (up/dn) または ≤ 6 (rg)
     - 段階2 で短命/通常分けが必要になった時の手戻り防止

対象軸: 5m / 15m / 30m / 1h / 4h / 1d (6軸)
窓 W 候補: 10 / 20 / 50 (3 candidates)

出力: results/regime_label_analysis/stage1b_meta_analysis.md
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
from shape_features import (
    FEATURE_FUNCS,
    CATEGORY_OF_FEATURE,
    compute_all_features,
)

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
OUT_DIR = BASE / "results/regime_label_analysis"
OUT_MD = OUT_DIR / "stage1b_meta_analysis.md"

TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]
W_CANDIDATES = [10, 20, 50]
MAX_LAG = 100
AC_THRESHOLDS = [0.7, 0.5, 0.3]
OVERLAP_THRESHOLDS = [0.3, 0.5, 0.7]
SHORT_THRESHOLD = {"up": 4, "rg": 6, "dn": 4}


def resample_ohlcv(df5m: pd.DataFrame, rule: str) -> pd.DataFrame:
    """pandas resample で OHLCV を作る"""
    return df5m.resample(rule).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna(subset=["close"])


def autocorrelation_analysis(features_per_tf: dict[str, dict[int, pd.DataFrame]]) -> pd.DataFrame:
    """形状特徴量 × 軸 × W × lag の自己相関を測る。"""
    rows = []
    for tf, by_W in features_per_tf.items():
        for W, feat_df in by_W.items():
            for fname in feat_df.columns:
                s = feat_df[fname].dropna()
                if len(s) < MAX_LAG * 2:
                    continue
                row = {"feature": fname, "tf": tf, "W": W}
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


def attach_features_to_labels(labels_df: pd.DataFrame,
                               features_per_tf: dict[str, dict[int, pd.DataFrame]]) -> pd.DataFrame:
    """教師ラベル 4h バーに、各軸 × 各 W の形状特徴量を merge_asof で attach。"""
    labels_df = labels_df.copy()
    labels_df["timestamp_utc"] = labels_df["timestamp_utc"].dt.tz_localize(None) if labels_df["timestamp_utc"].dt.tz is not None else labels_df["timestamp_utc"]

    # 各軸の代表 timestamp を生成
    labels_df["ts_5m"] = labels_df["timestamp_utc"] + pd.Timedelta(minutes=235)
    labels_df["ts_15m"] = labels_df["timestamp_utc"] + pd.Timedelta(minutes=225)
    labels_df["ts_30m"] = labels_df["timestamp_utc"] + pd.Timedelta(minutes=210)
    labels_df["ts_1h"] = labels_df["timestamp_utc"] + pd.Timedelta(hours=3)
    labels_df["ts_4h"] = labels_df["timestamp_utc"]
    labels_df["ts_1d"] = labels_df["timestamp_utc"].dt.floor("1D")

    for tf, by_W in features_per_tf.items():
        for W, feat_df in by_W.items():
            suffix = f"{tf}_W{W}"
            labels_df = attach_indicators(labels_df, feat_df, f"ts_{tf}", suffix)
    return labels_df


def label_separation_analysis(labels_attached: pd.DataFrame) -> pd.DataFrame:
    """全教師バー up/rg/dn 別 IQR 重複度。"""
    rows = []
    for fname in FEATURE_FUNCS.keys():
        for tf in TIMEFRAMES:
            for W in W_CANDIDATES:
                col = f"{fname}__{tf}_W{W}"
                if col not in labels_attached.columns:
                    continue
                by_label = {
                    "up": labels_attached[labels_attached["label_norm"] == "up"][col].dropna(),
                    "rg": labels_attached[labels_attached["label_norm"] == "rg"][col].dropna(),
                    "dn": labels_attached[labels_attached["label_norm"] == "dn"][col].dropna(),
                }
                res = overlap_3way(by_label)
                rows.append({
                    "feature": fname,
                    "tf": tf,
                    "W": W,
                    "overlap_ratio": res["overlap_ratio"],
                })
    return pd.DataFrame(rows)


def pattern_specificity_analysis(labels_attached: pd.DataFrame, transitions: list, subset: str) -> pd.DataFrame:
    """切替点 t=0 値で 6遷移パターン間 IQR 重複度。
    subset: "all" / "short" / "normal"
    """
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

    pattern_rows = []
    for ev in selected_tx:
        t = ev["t_idx"]
        row = {
            "pattern": f"{ev['prev']}->{ev['cur']}",
            **{c: labels_attached.iloc[t][c] for c in labels_attached.columns
               if any(c.endswith(f"__{tf}_W{W}") for tf in TIMEFRAMES for W in W_CANDIDATES)},
        }
        pattern_rows.append(row)
    if not pattern_rows:
        return pd.DataFrame()
    df = pd.DataFrame(pattern_rows)

    patterns = ["up->dn", "dn->up", "up->rg", "rg->up", "rg->dn", "dn->rg"]
    rows = []
    for fname in FEATURE_FUNCS.keys():
        for tf in TIMEFRAMES:
            for W in W_CANDIDATES:
                col = f"{fname}__{tf}_W{W}"
                if col not in df.columns:
                    continue
                by_pattern = {p: df[df["pattern"] == p][col].dropna() for p in patterns}
                for target in patterns:
                    others = [s for p, s in by_pattern.items() if p != target]
                    if len(by_pattern[target]) < 5:
                        continue
                    overlaps = [overlap_pair(by_pattern[target], o) for o in others]
                    overlaps = [o for o in overlaps if pd.notna(o)]
                    if not overlaps:
                        continue
                    rows.append({
                        "subset": subset,
                        "pattern": target,
                        "feature": fname,
                        "tf": tf,
                        "W": W,
                        "n": len(by_pattern[target]),
                        "mean_overlap_vs_others": float(np.mean(overlaps)),
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


def write_md(ac_df, sep_df, spec_dfs, out_path):
    lines = []
    lines.append("# 段階1-B メタ分析: 形状特徴量の窓 W・時間軸・対象決定")
    lines.append("")
    lines.append("段階1-B 本実装の前に、形状特徴量について以下を**データで**決める。")
    lines.append("")
    lines.append("- 窓 W: 自己相関で独立観測窓を測る (W=10/20/50 候補)")
    lines.append("- 時間軸: ラベル分離度で軸別の判定力を測る (5m/15m/30m/1h/4h/1d)")
    lines.append("- 対象特徴量: ラベル分離度 + パターン特異性 で参考順位を出す")
    lines.append(f"- パターン特異性は **全件 / 短命のみ / 通常のみ** の 3系統で計算（短命閾値: up≤{SHORT_THRESHOLD['up']} / rg≤{SHORT_THRESHOLD['rg']} / dn≤{SHORT_THRESHOLD['dn']}）")
    lines.append("- 自己相関 0.5 を切る lag が lag={MAX_LAG} までに見つからない場合は **\">100\"** と記録し N 推奨候補から除外")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === 処理 1: 自己相関 ===
    lines.append("## 処理 1: 自己相関分析")
    lines.append("")
    lines.append("### 1-A. 全特徴量 × 全軸 × 全 W × 主要 lag の自己相関")
    lines.append("")
    lines.append("| Feature | TF | W | lag1 | lag6 | lag24 | lag50 | lag100 | first<0.7 | first<0.5 | first<0.3 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for _, r in ac_df.iterrows():
        lines.append(
            f"| `{r['feature']}` | {r['tf']} | {int(r['W'])} | "
            f"{fmt(r.get('ac_lag1', np.nan))} | "
            f"{fmt(r.get('ac_lag6', np.nan))} | "
            f"{fmt(r.get('ac_lag24', np.nan))} | "
            f"{fmt(r.get('ac_lag50', np.nan))} | "
            f"{fmt(r.get('ac_lag100', np.nan))} | "
            f"{fmt(r['first_below_0.7'])} | {fmt(r['first_below_0.5'])} | {fmt(r['first_below_0.3'])} |"
        )
    lines.append("")

    lines.append("### 1-B. カテゴリ別 N 推奨値（first<0.5 切り lag の中央値・W=20 基準）")
    lines.append("")
    lines.append("| TF | カテゴリ | first<0.7 中央 | first<0.5 中央 | first<0.3 中央 | 100 超え件数 |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for tf in TIMEFRAMES:
        for cat in sorted(set(CATEGORY_OF_FEATURE.values())):
            cat_features = [f for f, c in CATEGORY_OF_FEATURE.items() if c == cat]
            sub = ac_df[(ac_df["tf"] == tf) & (ac_df["W"] == 20) & (ac_df["feature"].isin(cat_features))]
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
    lines.append("---")
    lines.append("")

    # === 処理 2: ラベル分離度 ===
    lines.append("## 処理 2: ラベル分離度")
    lines.append("")
    lines.append("教師ラベル全 4,745 バー (4h) の up/rg/dn 別 IQR 重複度。0=完全分離 / 1=完全重複。")
    lines.append("")
    lines.append("### 2-A. 重複度ランキング (上位 30)")
    lines.append("")
    lines.append("| Rank | Feature | TF | W | overlap |")
    lines.append("|---:|---|---|---:|---:|")
    sep_sorted = sep_df.dropna(subset=["overlap_ratio"]).sort_values("overlap_ratio").reset_index(drop=True)
    for i, r in sep_sorted.head(30).iterrows():
        lines.append(f"| {i+1} | `{r['feature']}` | {r['tf']} | {int(r['W'])} | {fmt(r['overlap_ratio'])} |")
    lines.append("")

    lines.append("### 2-B. 重複度閾値別 合格件数")
    lines.append("")
    lines.append("| 閾値 | 合格 (feature × tf × W) | 全体に占める割合 |")
    lines.append("|---|---:|---:|")
    total = sep_df["overlap_ratio"].notna().sum()
    for thr in OVERLAP_THRESHOLDS:
        n = (sep_df["overlap_ratio"] < thr).sum()
        lines.append(f"| < {thr} | {n} | {n / total * 100:.1f}% |")
    lines.append("")

    lines.append("### 2-C. 軸別合格件数 (重複度 < 0.5 基準)")
    lines.append("")
    lines.append("| TF | 合格件数 | 全件 |")
    lines.append("|---|---:|---:|")
    for tf in TIMEFRAMES:
        sub = sep_df[sep_df["tf"] == tf]
        n_pass = (sub["overlap_ratio"] < 0.5).sum()
        n_total = sub["overlap_ratio"].notna().sum()
        lines.append(f"| {tf} | {n_pass} | {n_total} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === 処理 3: パターン特異性 ===
    lines.append("## 処理 3: パターン特異性 (3系統)")
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
            lines.append(f"#### {p} (n={n_evt})")
            lines.append("")
            if sub.empty:
                lines.append("(切替点なし)")
                lines.append("")
                continue
            lines.append("| Rank | Feature | TF | W | mean_overlap |")
            lines.append("|---:|---|---|---:|---:|")
            for i, r in sub.head(5).iterrows():
                lines.append(f"| {i+1} | `{r['feature']}` | {r['tf']} | {int(r['W'])} | {fmt(r['mean_overlap_vs_others'])} |")
            lines.append("")

        lines.append(f"#### 3-{subset_label.upper()}-summary 重複度閾値別 合格件数")
        lines.append("")
        lines.append("| 閾値 | 合格件数 |")
        lines.append("|---|---:|")
        total = spec_df["mean_overlap_vs_others"].notna().sum()
        for thr in OVERLAP_THRESHOLDS:
            n = (spec_df["mean_overlap_vs_others"] < thr).sum()
            lines.append(f"| < {thr} | {n} ({n / total * 100:.1f}%) |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## まこさんが決めること")
    lines.append("")
    lines.append("1. **W の採用値**: 処理 1 を見て、各 (feature × tf) ごとにどの W を採るか")
    lines.append("2. **N (lag) の閾値**: 自己相関 0.3 / 0.5 / 0.7 のどれを採るか")
    lines.append("3. **対象軸**: 処理 2-C を見て 5m/15m/30m/1h/4h/1d のどれに絞るか")
    lines.append("4. **重複度閾値**: ラベル分離度・パターン特異性で 0.3 / 0.5 / 0.7 のどれを採るか")
    lines.append("5. **lag>100 の特徴量の扱い**: N 推奨候補から除外で OK か（本分析では W=10 等の短窓のみ採用するなど）")
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
    df_per_tf = {
        "5m": df5m,
        "15m": resample_ohlcv(df5m, "15min"),
        "30m": resample_ohlcv(df5m, "30min"),
        "1h": resample_ohlcv(df5m, "1h"),
        "4h": resample_ohlcv(df5m, "4h"),
        "1d": resample_ohlcv(df5m, "1D"),
    }
    for tf, d in df_per_tf.items():
        print(f"  {tf}: {len(d)} bars")

    print("形状特徴量計算 (軸 × W)...")
    features_per_tf: dict[str, dict[int, pd.DataFrame]] = {}
    for tf, df in df_per_tf.items():
        features_per_tf[tf] = {}
        for W in W_CANDIDATES:
            features_per_tf[tf][W] = compute_all_features(df, W)
        print(f"  {tf} 完了")

    print("自己相関分析...")
    ac_df = autocorrelation_analysis(features_per_tf)
    print(f"  行数: {len(ac_df)}")

    print("attach 教師ラベル...")
    labels_attached = attach_features_to_labels(labels, features_per_tf)
    print(f"  attach 後カラム数: {len(labels_attached.columns)}")

    print("ラベル分離度...")
    sep_df = label_separation_analysis(labels_attached)
    print(f"  行数: {len(sep_df)}")

    print("パターン特異性 (3系統)...")
    spec_dfs = {}
    for subset in ["all", "short", "normal"]:
        spec_dfs[subset] = pattern_specificity_analysis(labels_attached, transitions, subset)
        print(f"  {subset}: {len(spec_dfs[subset])} 行")

    print(f"md 出力: {OUT_MD}")
    write_md(ac_df, sep_df, spec_dfs, OUT_MD)
    print("DONE")


if __name__ == "__main__":
    main()
