"""
verify_top20_features_leak.py — phase_compliance §1.4 ブラックリスト top20 検出時の物理 leak verify

Phase 1 v5.1 smoke で検出された fractal/level/fib 系 4 特徴量が leak フリーか、
物理証跡 4 項目で verify する.

監査推奨フロー (2026-05-22 Plan エージェント独立評価):
- (i)   lag-1 shift 不変性 (df[col].shift(1) と現在値の差分が出ること = 過去のみ依存の sanity)
- (ii)  末尾 K=12 bars 内の値が NaN になっていない (未来 K 本を見ていない間接証跡)
- (iii) 二重 N サフィックス内外 N 一致 assert (build_labels_pct.py add_suffix 重複の安全性)
- (iv)  importance gain 絶対値 sanity (single > 50% で異常値・関所 A)

使い方:
    python verify_top20_features_leak.py --parquet sample
    python verify_top20_features_leak.py --parquet full
    python verify_top20_features_leak.py --parquet sample --importance-csv path/to/fi_top20.csv

正本:
- Plan エージェント監査結果 (2026-05-22)
- phase_compliance_checklist.md §1.4 (3 段階運用)
- false_positive_incident_policy.md §0-1 Prime Directive
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PARQUET_DIR = REPO_ROOT / "results" / "priority_rebuild"

# smoke で検出された 4 特徴量 (sample.parquet 2021-04-01 〜 06-28 で top20 入り)
DEFAULT_FEATURES = (
    "dist_to_fib_v2_382_pct_N50_N50__5m",
    "resistance_distance_pct_N100_N100__4h",
    "dist_to_fib_v2_500_pct_N200_N200__30m",
    "nearest_level_touch_count_N200_t200_N200__15m",
)

# K=12 LONG_MFE 学習対象の K 値 (smoke で検出された組合せ)
DEFAULT_K = 12

# importance gain sanity (single > 50% で異常)
IMPORTANCE_SINGLE_DOMINANCE_THRESHOLD = 0.50


def _extract_tf_minutes(feature_name: str) -> Optional[int]:
    """特徴量名末尾 __TF (例: __5m, __15m, __30m, __1h, __4h, __1d, __1w, __1M) から分数を抽出.

    Returns:
        TF 分数 (5m → 5, 4h → 240, 1d → 1440, ...) or None (TF サフィックスなし)
    """
    m = re.search(r"__(\d+)([smhdwM])$", feature_name)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2)
    mult = {"m": 1, "h": 60, "d": 1440, "w": 10080, "M": 43200, "s": 1.0 / 60}
    if unit not in mult:
        return None
    return int(n * mult[unit])


def verify_lag1_shift_invariance(
    df: pd.DataFrame,
    features: Tuple[str, ...],
    bar_minutes: int = 5,
    tolerance: float = 0.50,
) -> Dict[str, Dict[str, float]]:
    """(i) lag-1 shift 不変性 verify (TF-aware).

    過去のみ依存の特徴量は df[col].shift(1) と現在値で差分が出る (= 値が変化する).
    ただし MTF (上位 TF) 特徴量は forward-fill で 5m bar 間更新されないため、
    expected pct_diff = bar_minutes / TF_minutes (例: 4h → 5/240 = 2.08%).
    実測 pct_diff が expected の ±tolerance 範囲内なら PASS.

    Returns:
        Dict[feat, Dict["n_diff" / "n_total" / "pct_diff" / "tf_minutes" /
                        "expected_pct_diff" / "ratio" / "judgment"]]
    """
    result = {}
    for feat in features:
        if feat not in df.columns:
            result[feat] = {"error": f"not in parquet: {feat}"}
            continue
        s = df[feat]
        s_lag = s.shift(1)
        mask_both_notna = s.notna() & s_lag.notna()
        n_total = int(mask_both_notna.sum())
        if n_total == 0:
            result[feat] = {"error": "all NaN"}
            continue
        diff_mask = (s != s_lag) & mask_both_notna
        n_diff = int(diff_mask.sum())
        pct_diff = n_diff / n_total

        tf_minutes = _extract_tf_minutes(feat)
        if tf_minutes is None:
            expected = 1.0  # TF 不明は 5m 想定
            tf_label = "unknown"
        else:
            expected = min(1.0, bar_minutes / tf_minutes)
            tf_label = f"{tf_minutes}min"

        # ratio = 実測 / 期待 (1.0 で完全整合・0.5-1.5 で許容範囲)
        ratio = pct_diff / expected if expected > 0 else float("inf")
        lower = expected * (1 - tolerance)
        upper = expected * (1 + tolerance) if expected < 1.0 else 1.0 + tolerance

        if lower <= pct_diff <= upper:
            judgment = (
                f"PASS (MTF整合・TF={tf_label}・"
                f"expected={expected*100:.2f}% 実測={pct_diff*100:.2f}%・ratio={ratio:.3f})"
            )
        elif pct_diff < lower:
            judgment = (
                f"WARN (静的傾向・TF={tf_label}・"
                f"expected={expected*100:.2f}% 実測={pct_diff*100:.2f}%・leak 疑い)"
            )
        else:
            judgment = (
                f"WARN (期待超過・TF={tf_label}・"
                f"expected={expected*100:.2f}% 実測={pct_diff*100:.2f}%・要調査)"
            )
        result[feat] = {
            "n_diff": n_diff,
            "n_total": n_total,
            "pct_diff": float(pct_diff),
            "tf_minutes": tf_minutes,
            "tf_label": tf_label,
            "expected_pct_diff": float(expected),
            "ratio": float(ratio),
            "lower": float(lower),
            "upper": float(upper),
            "judgment": judgment,
        }
    return result


def verify_tail_nan_pattern(
    df: pd.DataFrame,
    features: Tuple[str, ...],
    K: int = DEFAULT_K,
) -> Dict[str, Dict[str, object]]:
    """(ii) 末尾 K bars NaN verify.

    feature 側は推論時点 t で過去のみ参照なら末尾でも NaN になる必要はない.
    むしろ末尾 K bars が全部 NaN だと「未来 K 本を見ているラベル的特徴量」の疑い.

    末尾 K bars NaN 比率を計算し:
    - 0% (全部値あり): PASS (過去のみ依存・末尾でも計算可能)
    - 100% (全部 NaN): WARN (未来 K 本参照疑い・leak 同型 pattern)
    - その他: 動的 NaN (実装上の rolling window 起因等)
    """
    result = {}
    n = len(df)
    tail_indices = list(range(n - K, n))
    for feat in features:
        if feat not in df.columns:
            result[feat] = {"error": f"not in parquet: {feat}"}
            continue
        s_tail = df[feat].iloc[tail_indices]
        n_nan_tail = int(s_tail.isna().sum())
        pct_nan_tail = n_nan_tail / K
        # 先頭 K bars NaN 比較 (rolling window 起因の NaN は先頭で発生)
        s_head = df[feat].iloc[:K]
        n_nan_head = int(s_head.isna().sum())
        pct_nan_head = n_nan_head / K
        if pct_nan_tail <= 0.05:
            judgment = f"PASS (末尾 NaN {pct_nan_tail*100:.1f}% ≤ 5%・過去依存)"
        elif pct_nan_tail >= 0.95:
            judgment = f"WARN (末尾 NaN {pct_nan_tail*100:.1f}% ≥ 95%・未来参照疑い)"
        else:
            judgment = f"NOTE (末尾 NaN {pct_nan_tail*100:.1f}%・先頭 NaN {pct_nan_head*100:.1f}%)"
        result[feat] = {
            "K": K,
            "n_nan_tail": n_nan_tail,
            "pct_nan_tail": float(pct_nan_tail),
            "n_nan_head": n_nan_head,
            "pct_nan_head": float(pct_nan_head),
            "judgment": judgment,
        }
    return result


def verify_double_N_suffix_match(
    features: Tuple[str, ...],
) -> Dict[str, Dict[str, object]]:
    """(iii) 二重 N サフィックスの内側/外側 N 一致 assert.

    例: "resistance_distance_pct_N100_N100__4h"
    - 内側 N = 100 (compute_c1_features 内の f"_pct_N{N}")
    - 外側 N = 100 (build_labels_pct.py L148 add_suffix(f"_N{N}"))
    - TF サフィックス: "__4h"
    両 N が一致しないと leak ではないが命名規則不整合.
    """
    result = {}
    # パターン: <base>_N<内側>_N<外側>__<TF> または <base>_t<thr>_N<内側>_N<外側>__<TF>
    # 末尾 __TF を分離した上で _N\d+_N\d+ を探す
    for feat in features:
        m = re.match(r"^(?P<base>.+?)__(?P<tf>[^_]+)$", feat)
        if not m:
            result[feat] = {"error": "no TF suffix found"}
            continue
        base = m.group("base")
        tf = m.group("tf")
        # _N\d+ を全部抽出 (連続 2 個以上で二重)
        n_matches = re.findall(r"_N(\d+)", base)
        if len(n_matches) < 2:
            result[feat] = {
                "tf": tf,
                "n_count": len(n_matches),
                "n_values": n_matches,
                "judgment": "NOTE (二重 N なし)",
            }
            continue
        # 末尾 2 つを内側/外側として比較
        inner_n, outer_n = n_matches[-2], n_matches[-1]
        match_flag = inner_n == outer_n
        result[feat] = {
            "tf": tf,
            "n_count": len(n_matches),
            "n_values": n_matches,
            "inner_n": inner_n,
            "outer_n": outer_n,
            "match": match_flag,
            "judgment": "PASS (内外 N 一致)" if match_flag else "FAIL (内外 N 不一致)",
        }
    return result


def verify_importance_dominance(
    importance_csv: Optional[Path],
    features: Tuple[str, ...],
    threshold: float = IMPORTANCE_SINGLE_DOMINANCE_THRESHOLD,
) -> Dict[str, object]:
    """(iv) importance gain 絶対値 sanity.

    auditor_template §B「単一列の支配 importance > 50% なら leak を疑う」.
    importance_csv (feature_importance_top20.csv) が必要.

    Returns:
        Dict["max_importance_pct" / "single_dominance" / "top4_features" / "judgment"]
    """
    if importance_csv is None or not importance_csv.exists():
        return {
            "error": f"importance_csv not provided or not found: {importance_csv}",
            "judgment": "SKIP (importance_csv なし)",
        }
    df = pd.read_csv(importance_csv)
    if "feature" not in df.columns or "importance" not in df.columns:
        return {
            "error": f"importance_csv must have columns [feature, importance], got {df.columns.tolist()}",
            "judgment": "ERROR",
        }
    total_imp = float(df["importance"].sum())
    if total_imp <= 0:
        return {"error": "total importance <= 0", "judgment": "ERROR"}
    df["importance_pct"] = df["importance"] / total_imp
    max_imp_pct = float(df["importance_pct"].max())
    single_dominance = max_imp_pct > threshold

    # 検出された 4 特徴量の rank + importance_pct
    top4_in_top20 = []
    for feat in features:
        row = df[df["feature"] == feat]
        if row.empty:
            top4_in_top20.append({
                "feature": feat,
                "in_top20": False,
                "rank": None,
                "importance_pct": None,
            })
        else:
            rank = int(df.index[df["feature"] == feat][0]) + 1
            top4_in_top20.append({
                "feature": feat,
                "in_top20": True,
                "rank": rank,
                "importance_pct": float(row["importance_pct"].iloc[0]),
            })

    if single_dominance:
        judgment = f"FAIL (max importance {max_imp_pct*100:.1f}% > {threshold*100:.0f}%・関所 A 異常値)"
    else:
        judgment = f"PASS (max importance {max_imp_pct*100:.1f}% ≤ {threshold*100:.0f}%)"

    return {
        "total_importance": total_imp,
        "max_importance_pct": max_imp_pct,
        "single_dominance": single_dominance,
        "threshold": threshold,
        "top4_in_top20": top4_in_top20,
        "all_top20": df[["feature", "importance", "importance_pct"]].to_dict(orient="records"),
        "judgment": judgment,
    }


def run_all_verifications(
    parquet_path: Path,
    features: Tuple[str, ...] = DEFAULT_FEATURES,
    K: int = DEFAULT_K,
    importance_csv: Optional[Path] = None,
) -> Dict[str, object]:
    """4 verify を順次実施 + 総合判定."""
    print(f"\n=== verify_top20_features_leak.py START ===")
    print(f"parquet: {parquet_path}")
    print(f"features: {features}")
    print(f"K: {K}")
    print(f"importance_csv: {importance_csv}")
    print(f"---")

    print(f"\n[load] reading parquet...")
    df = pd.read_parquet(parquet_path)
    print(f"[load] shape: {df.shape}")
    print(f"[load] index: {df.index[0]} ~ {df.index[-1]}")

    # (i) lag-1 shift
    print(f"\n[verify i] lag-1 shift 不変性 verify")
    result_i = verify_lag1_shift_invariance(df, features)
    for feat, r in result_i.items():
        print(f"  {feat}")
        for k, v in r.items():
            print(f"    {k}: {v}")

    # (ii) tail NaN
    print(f"\n[verify ii] 末尾 K={K} bars NaN pattern verify")
    result_ii = verify_tail_nan_pattern(df, features, K)
    for feat, r in result_ii.items():
        print(f"  {feat}")
        for k, v in r.items():
            print(f"    {k}: {v}")

    # (iii) double N suffix
    print(f"\n[verify iii] 二重 N サフィックス内外 N 一致 assert")
    result_iii = verify_double_N_suffix_match(features)
    for feat, r in result_iii.items():
        print(f"  {feat}")
        for k, v in r.items():
            print(f"    {k}: {v}")

    # (iv) importance dominance
    print(f"\n[verify iv] importance gain 絶対値 sanity")
    result_iv = verify_importance_dominance(importance_csv, features)
    for k, v in result_iv.items():
        if k == "all_top20":
            print(f"  all_top20: (first 5 of 20)")
            for row in v[:5]:
                print(f"    rank={row['feature']:<60} imp={row['importance']:.0f} pct={row['importance_pct']:.4f}")
        elif k == "top4_in_top20":
            print(f"  top4_in_top20:")
            for row in v:
                print(f"    {row['feature']:<60} in_top20={row['in_top20']} rank={row['rank']} pct={row['importance_pct']}")
        else:
            print(f"  {k}: {v}")

    # 総合判定
    print(f"\n=== 総合判定 ===")
    all_pass_i = all(
        r.get("judgment", "").startswith("PASS")
        for r in result_i.values()
        if "error" not in r
    )
    all_pass_ii = all(
        r.get("judgment", "").startswith("PASS")
        for r in result_ii.values()
        if "error" not in r
    )
    all_pass_iii = all(
        r.get("judgment", "").startswith("PASS")
        for r in result_iii.values()
        if "error" not in r
    )
    all_pass_iv = (
        result_iv.get("judgment", "").startswith("PASS")
        if "error" not in result_iv and not result_iv.get("judgment", "").startswith("SKIP")
        else None
    )
    print(f"  (i) lag-1 shift:        {'PASS' if all_pass_i else 'WARN/FAIL'}")
    print(f"  (ii) tail NaN:          {'PASS' if all_pass_ii else 'WARN/FAIL'}")
    print(f"  (iii) double N match:   {'PASS' if all_pass_iii else 'FAIL'}")
    print(f"  (iv) importance:        {'PASS' if all_pass_iv else ('SKIP' if all_pass_iv is None else 'FAIL')}")

    overall_pass = (
        all_pass_i and all_pass_ii and all_pass_iii
        and (all_pass_iv is None or all_pass_iv)
    )
    print(f"  overall: {'PASS' if overall_pass else 'WARN/FAIL'}")

    summary = {
        "parquet": str(parquet_path),
        "features": list(features),
        "K": K,
        "importance_csv": str(importance_csv) if importance_csv else None,
        "verify_i_lag1_shift": result_i,
        "verify_ii_tail_nan": result_ii,
        "verify_iii_double_N": result_iii,
        "verify_iv_importance": result_iv,
        "overall_pass": overall_pass,
        "all_pass_i": all_pass_i,
        "all_pass_ii": all_pass_ii,
        "all_pass_iii": all_pass_iii,
        "all_pass_iv": all_pass_iv,
        "executed_at": datetime.now().isoformat(),
    }
    return summary


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="phase_compliance §1.4 top20 leak verify")
    p.add_argument(
        "--parquet",
        type=str,
        default="sample",
        help="'sample' / 'full' / 絶対パス (sample=labels_mfe_mae_pct_sample.parquet, full=train_2021_2024.parquet)",
    )
    p.add_argument(
        "--features",
        type=str,
        nargs="+",
        default=list(DEFAULT_FEATURES),
        help="verify する特徴量名リスト",
    )
    p.add_argument(
        "--K",
        type=int,
        default=DEFAULT_K,
        help="末尾 NaN verify で見る bar 数 (既定 12)",
    )
    p.add_argument(
        "--importance-csv",
        type=Path,
        default=None,
        help="feature_importance_top20.csv パス (verify iv 用・省略可)",
    )
    p.add_argument(
        "--out-json",
        type=Path,
        default=None,
        help="結果 JSON 保存先 (省略時は results/priority_rebuild/leak_verify_TIMESTAMP.json)",
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()

    # parquet path 解決
    if args.parquet == "sample":
        parquet_path = PARQUET_DIR / "labels_mfe_mae_pct_sample.parquet"
    elif args.parquet == "full":
        parquet_path = PARQUET_DIR / "labels_mfe_mae_pct_train_2021_2024.parquet"
    else:
        parquet_path = Path(args.parquet)

    if not parquet_path.exists():
        print(f"ERROR: parquet not found: {parquet_path}")
        return 2

    print(f"=====verify_top20_features_leak START {datetime.now().isoformat()} =====")
    summary = run_all_verifications(
        parquet_path=parquet_path,
        features=tuple(args.features),
        K=args.K,
        importance_csv=args.importance_csv,
    )

    # JSON 保存
    if args.out_json is None:
        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        out_json = PARQUET_DIR / f"leak_verify_{ts}.json"
    else:
        out_json = args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\n[save] {out_json}")
    print(f"=====verify_top20_features_leak END {datetime.now().isoformat()} =====")

    return 0 if summary["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
