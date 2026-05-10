"""analyze_intra_axis_correlation.py — 段階1 軸内 |r|>0.9 高相関群化 + 代表選出

設計原則 (まこさん指示・2026-05-09 確定):
  - corr 計算は全件 pearson 1 回 (subset 別 corr は不安定)
  - 群構造は subset 横断で共通
  - 代表選出は subset 別 (1-A 全件のみ / 1-B/1-C 全件+短命+通常)
  - 群内 best 1 自動採用は禁止 (L-159 精神)
  - 群 × subset で「min(overlap_ratio) + 閾値内同等候補」全保持
  - 閾値はまこさんが分布を見て決定 (Claude が暫定値で決めない)
  - per-bar テーブルは各軸 native 時系列 (ffill なし・軸跨ぎ計算なし)
  - 論点4 (5m タイミング merge_asof + ffill) は段階2 評価時の別用途・用途分離維持

実行 2 段:
  1 回目 --mode=distribute → 群構造 + 分布提示 (md/json)
  2 回目 --mode=select --thresholds=<json> → 代表集合 (json)

distribute / select 結果同一性保証:
  両モードで build_per_bar_tables / compute_intra_axis_corr / union_find_groups /
  compute_overlap_ratios_* を同一関数・同一入力 (DATA_5M) で呼ぶ。
  pearson 相関は決定論的 (乱数なし) / データ読み込みも決定論的 →
  両モードの groups と overlap_ratios は完全一致する。
  冗長計算は中間結果ファイル不在時の整合性優先設計。

入力: data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv
出力 (results/regime_label_analysis/):
  - intra_axis_correlation.md   (人間可読・群構造 + 除外一覧 + 分布)
  - intra_axis_groups.json      (群構造)
  - pruned_column_list.json     (--mode=select で生成・代表集合)
"""

import sys
import os
import json
import argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import pandas as pd
import numpy as np

from analyze_regime_label_features import build_indicators_extended
from analyze_transition_indicators import (
    load_labels, attach_all_indicators_dict,
)
from analyze_stage1a_meta import (
    ALL_INDICATORS as ALL_INDICATORS_1A,
    TIMEFRAMES,
    label_separation_analysis as label_sep_1a,
    overlap_3way,
)
from analyze_stage1b_meta import (
    W_CANDIDATES,
    resample_ohlcv,
    attach_features_to_labels as attach_1b,
)
from analyze_stage1c_meta import (
    compute_features_per_tf as compute_1c_features,
    attach_features_to_labels as attach_1c,
    attach_run_metadata as attach_run_meta,
    label_separation_analysis as label_sep_1c,
)
from shape_features import FEATURE_FUNCS, compute_all_features

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
OUT_DIR = BASE / "results/regime_label_analysis"
OUT_MD = OUT_DIR / "intra_axis_correlation.md"
OUT_GROUPS = OUT_DIR / "intra_axis_groups.json"
OUT_PRUNED = OUT_DIR / "pruned_column_list.json"

CORR_THRESHOLD = 0.9
# pearson 相関の統計安定性目安 (n>=30 慣行・n>=100 安全圏)。
# 軸別有効観測数 4h: 4,745 / 1d: ~1,800 でカット対象軸なし。
MIN_VALID_OBS = 100


# ── per-bar テーブル構築 ──────────────────────────

def build_per_bar_tables(df_per_tf):
    """各 (category, tf) の per-bar 値テーブルを構築。
    各 DataFrame は各軸 native 時系列 (5m への ffill なし)。
    """
    tables = {"1-A": {}, "1-B": {}, "1-C": {}}

    print("  1-A per-bar...")
    for tf in TIMEFRAMES:
        feat = build_indicators_extended(df_per_tf[tf])
        keep = [c for c in ALL_INDICATORS_1A if c in feat.columns]
        tables["1-A"][tf] = feat[keep].copy()

    print("  1-B per-bar (20 feat × 3 W)...")
    for tf in TIMEFRAMES:
        cols = {}
        for W in W_CANDIDATES:
            f = compute_all_features(df_per_tf[tf], W)
            for c in f.columns:
                cols[f"{c}_W{W}"] = f[c]
        tables["1-B"][tf] = pd.DataFrame(cols, index=df_per_tf[tf].index)

    print("  1-C per-bar (structure + c2)...")
    structure_per_tf, c2_per_tf, _ = compute_1c_features(df_per_tf)
    for tf in TIMEFRAMES:
        cols = {}
        for N, f in structure_per_tf[tf].items():
            for c in f.columns:
                cols[f"{c}_N{N}"] = f[c]
        for c in c2_per_tf[tf].columns:
            cols[f"{c}_c2"] = c2_per_tf[tf][c]
        tables["1-C"][tf] = pd.DataFrame(cols, index=df_per_tf[tf].index)

    return tables


# ── 軸内 corr 行列 + 除外一覧 ─────────────────────

def compute_intra_axis_corr(tables):
    """各 (cat, tf) で全件 pearson corr 行列を計算。
    valid: nunique>=2 かつ notna>=MIN_VALID_OBS。
    excluded: 除外カラムと理由を保持 (透明性確保)。
    """
    out = {}
    excluded = {}
    for cat, by_tf in tables.items():
        out[cat] = {}
        excluded[cat] = {}
        for tf, df in by_tf.items():
            valid = []
            excl = []
            for c in df.columns:
                nunique = df[c].nunique(dropna=True)
                notna = df[c].notna().sum()
                if nunique < 2:
                    excl.append((c, "nunique<2"))
                elif notna < MIN_VALID_OBS:
                    excl.append((c, f"notna={notna}<{MIN_VALID_OBS}"))
                else:
                    valid.append(c)
            out[cat][tf] = df[valid].corr(method="pearson")
            excluded[cat][tf] = excl
    return out, excluded


# ── union-find 群化 ────────────────────────────

def union_find_groups(corr_matrix, threshold=CORR_THRESHOLD):
    cols = list(corr_matrix.columns)
    parent = {c: c for c in cols}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    n = len(cols)
    for i in range(n):
        for j in range(i + 1, n):
            r = corr_matrix.iloc[i, j]
            if pd.notna(r) and abs(r) > threshold:
                union(cols[i], cols[j])
    groups = {}
    for c in cols:
        groups.setdefault(find(c), set()).add(c)
    return [sorted(list(g)) for g in groups.values()]


# ── overlap_ratio 取得 ──────────────────────────

def compute_overlap_ratios_1a(labels, df_per_tf):
    """1-A: subset='all' のみ (既存実装に subset 引数なし)。"""
    feat_per_tf = {tf: build_indicators_extended(df_per_tf[tf]) for tf in TIMEFRAMES}
    la = attach_all_indicators_dict(labels, feat_per_tf)
    sep = label_sep_1a(la)
    out = {}
    for _, r in sep.iterrows():
        out[(r["tf"], r["indicator"], "all")] = r["overlap_ratio"]
    return out


def compute_overlap_ratios_1b(labels, df_per_tf):
    """1-B: subset='all'/'short'/'normal' (新スクリプト側で 3 系統計算)。
    既存 attach_1b で labels_attached 構築 → attach_run_meta で is_short 付与 →
    subset 別に overlap_3way 適用。
    """
    feat_per_tf = {tf: {W: compute_all_features(df_per_tf[tf], W) for W in W_CANDIDATES}
                   for tf in TIMEFRAMES}
    la = attach_1b(labels, feat_per_tf)
    la = attach_run_meta(la)

    out = {}
    for subset in ["all", "short", "normal"]:
        if subset == "short":
            df = la[la["is_short"] == 1]
        elif subset == "normal":
            df = la[la["is_short"] == 0]
        else:
            df = la
        for fname in FEATURE_FUNCS.keys():
            for tf in TIMEFRAMES:
                for W in W_CANDIDATES:
                    col = f"{fname}__{tf}_W{W}"
                    if col not in df.columns:
                        continue
                    by_label = {
                        lbl: df[df["label_norm"] == lbl][col].dropna()
                        for lbl in ["up", "rg", "dn"]
                    }
                    if any(len(s) < 2 or s.nunique() < 2 for s in by_label.values()):
                        continue
                    res = overlap_3way(by_label)
                    out[(tf, f"{fname}_W{W}", subset)] = res["overlap_ratio"]
    return out


def compute_overlap_ratios_1c(labels, df_per_tf):
    """1-C: subset='all'/'short'/'normal' (既存 label_sep_1c に subset 引数あり)。"""
    structure_per_tf, c2_per_tf, swing_per_tf = compute_1c_features(df_per_tf)
    la = attach_1c(labels, structure_per_tf, c2_per_tf, swing_per_tf)
    la = attach_run_meta(la)

    out = {}
    for subset in ["all", "short", "normal"]:
        sep = label_sep_1c(la, subset=subset)
        for _, r in sep.iterrows():
            tf = r["tf"]
            N = r["N"]
            base = r["feature"]
            per_bar_col = f"{base}_c2" if N == "—" else f"{base}_N{N}"
            out[(tf, per_bar_col, subset)] = r["overlap_ratio"]
    return out


# ── 群別 × subset 別 分布 ──────────────────────

def group_overlap_distribution(groups_by_cat_tf, overlap_by_cat):
    rows = []
    for cat, by_tf in groups_by_cat_tf.items():
        ov = overlap_by_cat[cat]
        subsets = ["all"] if cat == "1-A" else ["all", "short", "normal"]
        for tf, glist in by_tf.items():
            for gid, members in enumerate(glist):
                for subset in subsets:
                    vals = [ov.get((tf, c, subset)) for c in members]
                    vals = [v for v in vals if v is not None and not pd.isna(v)]
                    if not vals:
                        continue
                    s = pd.Series(vals)
                    rows.append({
                        "category": cat, "tf": tf, "group_id": gid, "subset": subset,
                        "n_members": len(members), "n_valid": len(vals),
                        "min": s.min(), "q1": s.quantile(0.25), "median": s.median(),
                        "q3": s.quantile(0.75), "max": s.max(),
                    })
    return pd.DataFrame(rows)


# ── 代表集合選出 (--mode=select) ────────────────

def select_representatives(groups_by_cat_tf, overlap_by_cat, thresholds):
    """thresholds: {(cat, subset): float}。
    各群 × 各 subset で min(overlap) + 閾値内同等候補を全保持 (L-159 精神)。
    """
    out = {}
    for cat, by_tf in groups_by_cat_tf.items():
        ov = overlap_by_cat[cat]
        subsets = ["all"] if cat == "1-A" else ["all", "short", "normal"]
        out[cat] = {}
        for tf, glist in by_tf.items():
            out[cat][tf] = {}
            for subset in subsets:
                thr = thresholds.get((cat, subset))
                if thr is None:
                    continue
                kept = []
                for members in glist:
                    valid = [(c, ov.get((tf, c, subset))) for c in members]
                    valid = [(c, v) for c, v in valid if v is not None and not pd.isna(v)]
                    if not valid:
                        continue
                    best = min(v for _, v in valid)
                    same = [c for c, v in valid if v - best <= thr]
                    kept.extend(same)
                out[cat][tf][subset] = sorted(kept)
    return out


# ── md 出力 ─────────────────────────────────

def write_md(groups_by_cat_tf, excluded_by_cat, dist_df, out_path):
    lines = ["# 段階1 軸内 |r|>0.9 高相関群化 分析", ""]
    lines.append(f"作成日: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"閾値: |r| > {CORR_THRESHOLD} / 最低有効観測数: {MIN_VALID_OBS}")
    lines.append("設計: corr 全件 pearson 1 回 / 群構造 subset 横断共通 / 代表選出 subset 別 (best 1 禁止)")
    lines.append("符号: overlap_ratio 0=完全分離(良) / 1=完全重複(悪)。値が小さいほど良い。")
    lines.append("")

    # ── 1. 群構造サマリ ──
    lines.append("## 1. 群構造サマリ")
    lines.append("")
    lines.append("| category | tf | カラム総数 | 群数 | 単独群 | 多元群 | 最大群サイズ |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for cat in ["1-A", "1-B", "1-C"]:
        if cat not in groups_by_cat_tf:
            continue
        for tf in TIMEFRAMES:
            if tf not in groups_by_cat_tf[cat]:
                continue
            grps = groups_by_cat_tf[cat][tf]
            n_total = sum(len(g) for g in grps)
            n_single = sum(1 for g in grps if len(g) == 1)
            n_multi = len(grps) - n_single
            max_size = max((len(g) for g in grps), default=0)
            lines.append(
                f"| {cat} | {tf} | {n_total} | {len(grps)} | {n_single} | {n_multi} | {max_size} |"
            )
    lines.append("")

    # ── 1.5. 除外指標一覧 (透明性確保・L-160 精神) ──
    lines.append("## 1.5. 除外指標一覧 (corr 計算対象外)")
    lines.append("")
    lines.append("除外理由: nunique<2 (定数指標・分散ゼロ) または notna<MIN_VALID_OBS (有効観測数不足)")
    lines.append("")
    lines.append("| category | tf | 除外件数 | 内訳 (最大10件・以降は件数のみ) |")
    lines.append("|---|---|---:|---|")
    for cat in ["1-A", "1-B", "1-C"]:
        if cat not in excluded_by_cat:
            continue
        for tf in TIMEFRAMES:
            if tf not in excluded_by_cat[cat]:
                continue
            excl_list = excluded_by_cat[cat][tf]
            if not excl_list:
                lines.append(f"| {cat} | {tf} | 0 | (なし) |")
            else:
                cols_str = ", ".join(f"`{c}` ({reason})" for c, reason in excl_list[:10])
                if len(excl_list) > 10:
                    cols_str += f" ... 他{len(excl_list) - 10}件"
                lines.append(f"| {cat} | {tf} | {len(excl_list)} | {cols_str} |")
    lines.append("")

    # ── 2. 群別 × subset 別 分布 ──
    lines.append("## 2. 群別 × subset 別 overlap_ratio 分布")
    lines.append("")
    for cat in ["1-A", "1-B", "1-C"]:
        sub = dist_df[dist_df["category"] == cat]
        if sub.empty:
            continue
        lines.append(f"### 2-{cat[-1]}. {cat}")
        lines.append("")
        for tf in TIMEFRAMES:
            tdf = sub[sub["tf"] == tf]
            if tdf.empty:
                continue
            lines.append(f"#### {tf}")
            lines.append("")
            lines.append("| group_id | subset | n_members | n_valid | min | q1 | median | q3 | max |")
            lines.append("|---:|---|---:|---:|---:|---:|---:|---:|---:|")
            for _, r in tdf.iterrows():
                lines.append(
                    f"| {r['group_id']} | {r['subset']} | {r['n_members']} | {r['n_valid']} | "
                    f"{r['min']:.3f} | {r['q1']:.3f} | {r['median']:.3f} | "
                    f"{r['q3']:.3f} | {r['max']:.3f} |"
                )
            lines.append("")

    # ── 3. 剪定後組合せサイズ事前見積もり ──
    lines.append("## 3. 剪定後組合せサイズ事前見積もり (参考)")
    lines.append("")
    lines.append("| 採用 | 1-A | 1-B | 1-C | 合計 | k=2 組数 | k=3 組数 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for label, mode in [("剪定なし (全件)", "all"), ("各群 best 1 (参考下限)", "best1")]:
        sizes = {}
        for cat in ["1-A", "1-B", "1-C"]:
            if cat not in groups_by_cat_tf:
                sizes[cat] = 0
                continue
            sizes[cat] = (
                sum(len(grps) for grps in groups_by_cat_tf[cat].values())
                if mode == "best1"
                else sum(sum(len(g) for g in grps) for grps in groups_by_cat_tf[cat].values())
            )
        total = sum(sizes.values())
        k2 = total * (total - 1) // 2
        k3 = total * (total - 1) * (total - 2) // 6
        lines.append(
            f"| {label} | {sizes['1-A']} | {sizes['1-B']} | {sizes['1-C']} | "
            f"{total} | {k2:,} | {k3:,} |"
        )
    lines.append("")

    # ── 4. まこさんが決めること ──
    lines.append("## 4. まこさんが決めること")
    lines.append("")
    lines.append("- 各 (category, subset) の閾値: 上記 §2 分布を見て決定")
    lines.append("- thresholds.json 例:")
    lines.append("  ```json")
    lines.append("  {")
    lines.append("    \"1-A_all\": 0.05,")
    lines.append("    \"1-B_all\": 0.03, \"1-B_short\": 0.05, \"1-B_normal\": 0.04,")
    lines.append("    \"1-C_all\": 0.03, \"1-C_short\": 0.05, \"1-C_normal\": 0.04")
    lines.append("  }")
    lines.append("  ```")
    lines.append("- 確定後: `python3 analyze_intra_axis_correlation.py --mode=select --thresholds=thresholds.json`")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


# ── メイン ─────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["distribute", "select"], default="distribute")
    parser.add_argument("--thresholds", type=str, default=None)
    args = parser.parse_args()

    print("ラベル + OHLCV 読み込み...")
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

    print("per-bar テーブル構築...")
    tables = build_per_bar_tables(df_per_tf)

    print("軸内 corr 計算...")
    corr_by_cat, excluded_by_cat = compute_intra_axis_corr(tables)

    print("union-find 群化...")
    groups_by_cat_tf = {
        cat: {tf: union_find_groups(cm) for tf, cm in by_tf.items()}
        for cat, by_tf in corr_by_cat.items()
    }

    print(f"群構造 json 出力: {OUT_GROUPS}")
    OUT_GROUPS.write_text(json.dumps(
        {cat: {tf: [list(g) for g in grps] for tf, grps in by_tf.items()}
         for cat, by_tf in groups_by_cat_tf.items()},
        indent=2,
    ))

    if args.mode == "distribute":
        print("overlap_ratio 取得 (1-A 全件)...")
        ov_1a = compute_overlap_ratios_1a(labels, df_per_tf)
        print("overlap_ratio 取得 (1-B 3 系統)...")
        ov_1b = compute_overlap_ratios_1b(labels, df_per_tf)
        print("overlap_ratio 取得 (1-C 3 系統)...")
        ov_1c = compute_overlap_ratios_1c(labels, df_per_tf)
        overlap_by_cat = {"1-A": ov_1a, "1-B": ov_1b, "1-C": ov_1c}

        print("群別分布集計...")
        dist_df = group_overlap_distribution(groups_by_cat_tf, overlap_by_cat)

        print(f"md 出力: {OUT_MD}")
        write_md(groups_by_cat_tf, excluded_by_cat, dist_df, OUT_MD)

    elif args.mode == "select":
        if not args.thresholds:
            raise SystemExit("--thresholds=<json file> 必須")
        raw = json.loads(Path(args.thresholds).read_text())
        thr = {}
        for k, v in raw.items():
            cat, subset = k.rsplit("_", 1)
            thr[(cat, subset)] = v

        print("overlap_ratio 取得...")
        ov_1a = compute_overlap_ratios_1a(labels, df_per_tf)
        ov_1b = compute_overlap_ratios_1b(labels, df_per_tf)
        ov_1c = compute_overlap_ratios_1c(labels, df_per_tf)
        overlap_by_cat = {"1-A": ov_1a, "1-B": ov_1b, "1-C": ov_1c}

        print("代表集合選出...")
        reps = select_representatives(groups_by_cat_tf, overlap_by_cat, thr)

        print(f"代表集合 json 出力: {OUT_PRUNED}")
        OUT_PRUNED.write_text(json.dumps(reps, indent=2))

    print("DONE")


if __name__ == "__main__":
    main()
