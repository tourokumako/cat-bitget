"""build_indicator_catalogue.py — 1,432 指標の人間可読カタログ生成

問い: priority_rebuild フェーズで使う指標素材 1,432 列の中身を一覧化したい
目的: 設計時に「どの指標があるか」「どのパラメータ範囲か」を即座に参照できるようにする

入力:
  - results/regime_label_analysis/pruned_column_list.json (1,432 列・剪定済)

出力:
  - results/priority_rebuild/indicator_catalogue.csv (機械可読・全 1,432 行)
  - results/priority_rebuild/indicator_catalogue.md  (人間可読・ファミリー集約 + 完全一覧)

ファミリー抽出ロジック:
  - 1-A: family = カラム名そのまま (例: rsi14, adx14, atr14_pct)
  - 1-B: "_W{N}" サフィックスを剥がす (例: avg_body_ratio_W_W10 → family=avg_body_ratio_W, W=10)
  - 1-C: "_N{N}_b{B}_va{V}" 等のパラメータを剥がす (例: dist_to_POC_pct_N100_b020 → family=dist_to_POC_pct, N=100, b=020)
"""

import json
import re
from collections import defaultdict
from pathlib import Path
import pandas as pd

BASE = Path(__file__).parent.parent.parent
PRUNED_JSON = BASE / "results" / "regime_label_analysis" / "pruned_column_list.json"
OUT_DIR = BASE / "results" / "priority_rebuild"
OUT_CSV = OUT_DIR / "indicator_catalogue.csv"
OUT_MD = OUT_DIR / "indicator_catalogue.md"

TFS_ORDER = ["5m", "15m", "30m", "1h", "4h", "1d"]
CATS_ORDER = ["1-A", "1-B", "1-C"]


def parse_column(cat: str, col: str) -> dict:
    """カテゴリ別にファミリー名 + パラメータを抽出"""
    info = {"original": col, "family": col, "params": {}}

    if cat == "1-A":
        # ほぼそのまま (パラメータが名前埋め込み・ex: adx14 / atr14_pct / rsi_slope_5b)
        info["family"] = col
        # 末尾 _Xb / _Xd / _NN 等の抽出は粒度過剰なので省略
        return info

    if cat == "1-B":
        # 末尾 _W{N} を剥がす (ex: avg_body_ratio_W_W10 → avg_body_ratio_W, W=10)
        m = re.search(r"_W(\d+)$", col)
        if m:
            info["family"] = col[: m.start()]
            info["params"]["W"] = int(m.group(1))
        return info

    if cat == "1-C":
        # 末尾 _N{N} / _b{B} / _va{V} 系を剥がす
        # 例: dist_to_POC_pct_N100_b020_N100 / dist_to_VAH_pct_b020_va60_N50_struct
        # struct サフィックスは無視できる
        s = col
        # 末尾 _struct がある場合は剥がす (1-C 内部マーカー)
        if s.endswith("_struct"):
            s = s[: -len("_struct")]
        # _c2 (pivot 種類) 抽出
        if s.endswith("_c2"):
            info["params"]["c"] = 2
            s = s[: -len("_c2")]
        # _N{N} 抽出 (複数あれば最後)
        m = re.search(r"_N(\d+)$", s)
        if m:
            info["params"]["N"] = int(m.group(1))
            s = s[: m.start()]
        # _b{B} 抽出
        m = re.search(r"_b(\d+)$", s)
        if m:
            info["params"]["b"] = m.group(1)
            s = s[: m.start()]
        # _va{V} 抽出
        m = re.search(r"_va(\d+)$", s)
        if m:
            info["params"]["va"] = int(m.group(1))
            s = s[: m.start()]
        # _N{N} がさらに残っている可能性 (二重表記)
        m = re.search(r"_N(\d+)$", s)
        if m:
            info["params"].setdefault("N_inner", int(m.group(1)))
            s = s[: m.start()]
        info["family"] = s

    return info


def main():
    print(f"[load] {PRUNED_JSON}")
    d = json.loads(PRUNED_JSON.read_text())

    rows = []
    family_map = defaultdict(lambda: defaultdict(set))  # family -> tf -> set of params
    family_cat = {}

    for cat, by_tf in d.items():
        for tf, subs in by_tf.items():
            cols = subs.get("all", [])
            for col in cols:
                info = parse_column(cat, col)
                family = info["family"]
                family_cat[family] = cat
                # store full params hash
                param_str = json.dumps(info["params"], sort_keys=True) if info["params"] else ""
                family_map[family][tf].add(param_str)
                rows.append({
                    "category": cat,
                    "timeframe": tf,
                    "column": col,
                    "family": family,
                    **{f"param_{k}": v for k, v in info["params"].items()},
                })

    df = pd.DataFrame(rows)
    df = df.sort_values(["category", "family", "timeframe", "column"]).reset_index(drop=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"[done] csv: {OUT_CSV} ({len(df)} rows)")

    # ── md 生成 ──
    md = []
    md.append("# 指標カタログ — Priority 再構築フェーズ用 1,432 列\n")
    md.append(f"- 入力: `{PRUNED_JSON.relative_to(BASE)}`")
    md.append(f"- 合計: **{len(df):,} 列** (1-A: 348 / 1-B: 347 / 1-C: 737)")
    md.append("- ファミリー抽出: パラメータ (W, N, b, va, c) を剥がして基底名を取得")
    md.append("- CSV 版（機械可読・全 1,432 行）: [`indicator_catalogue.csv`](indicator_catalogue.csv)\n")

    # §1: カテゴリ × TF クロス表
    md.append("## §1 カテゴリ × 時間軸 クロス表\n")
    md.append("| カテゴリ | 5m | 15m | 30m | 1h | 4h | 1d | 小計 |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for cat in CATS_ORDER:
        sub = df[df["category"] == cat]
        counts = [int((sub["timeframe"] == tf).sum()) for tf in TFS_ORDER]
        md.append(f"| {cat} | " + " | ".join(str(c) for c in counts) + f" | **{sum(counts)}** |")
    total_per_tf = [int((df["timeframe"] == tf).sum()) for tf in TFS_ORDER]
    md.append(f"| **合計** | " + " | ".join(f"**{c}**" for c in total_per_tf) + f" | **{len(df)}** |")
    md.append("")

    # §2: ファミリー一覧（カテゴリ別）
    md.append("## §2 指標ファミリー一覧（パラメータを畳んだベース名）\n")
    for cat in CATS_ORDER:
        cat_families = sorted([f for f, c in family_cat.items() if c == cat])
        md.append(f"### {cat} ({len(cat_families)} ファミリー)\n")
        md.append("| ファミリー | TF 存在 | パターン数 |")
        md.append("|---|---|---:|")
        for fam in cat_families:
            tf_list = sorted(family_map[fam].keys(), key=lambda x: TFS_ORDER.index(x) if x in TFS_ORDER else 99)
            tf_str = " ".join(tf_list)
            n_patterns = sum(len(family_map[fam][tf]) for tf in tf_list)
            md.append(f"| `{fam}` | {tf_str} | {n_patterns} |")
        md.append("")

    # §3: パラメータ範囲一覧
    md.append("## §3 パラメータ範囲一覧（カテゴリ別）\n")
    for cat in CATS_ORDER:
        sub = df[df["category"] == cat]
        param_cols = [c for c in sub.columns if c.startswith("param_") and sub[c].notna().any()]
        if not param_cols:
            md.append(f"### {cat}\n\nパラメータなし（指標名に埋込）\n")
            continue
        md.append(f"### {cat}\n")
        md.append("| パラメータ | 値の集合 |")
        md.append("|---|---|")
        for pc in param_cols:
            vals = sorted(set(sub[pc].dropna().tolist()), key=lambda x: (str(type(x)), x))
            md.append(f"| `{pc.replace('param_', '')}` | " + ", ".join(str(v) for v in vals) + " |")
        md.append("")

    # §4: 全 1,432 列の完全一覧
    md.append("## §4 全 1,432 列 完全一覧（カテゴリ × TF 別）\n")
    md.append("折りたたみ表示で長大。CSV 版（[indicator_catalogue.csv](indicator_catalogue.csv)）が見やすい。\n")
    for cat in CATS_ORDER:
        for tf in TFS_ORDER:
            sub = df[(df["category"] == cat) & (df["timeframe"] == tf)]
            if sub.empty:
                continue
            md.append(f"<details><summary><strong>{cat} × {tf}</strong> ({len(sub)} 列)</summary>\n")
            md.append("")
            for col in sub["column"].tolist():
                md.append(f"- `{col}`")
            md.append("")
            md.append("</details>\n")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"[done] md: {OUT_MD}")

    # サマリ出力
    print()
    print(f"[summary] total cols: {len(df)}")
    print(f"[summary] unique families: {len(family_cat)}")
    for cat in CATS_ORDER:
        n_fam = sum(1 for f, c in family_cat.items() if c == cat)
        n_col = int((df["category"] == cat).sum())
        print(f"[summary]   {cat}: {n_fam} families / {n_col} cols")


if __name__ == "__main__":
    main()
