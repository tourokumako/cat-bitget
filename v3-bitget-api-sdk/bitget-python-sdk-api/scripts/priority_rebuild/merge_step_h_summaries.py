"""Step H 3 並列 summary JSON マージスクリプト (2026-05-22).

3 並列実行で別々の out_base に書かれた `phase1_v5_summary.json` を読み込み、
combinations を統合・§4.1 v5.1 合格判定を再計算した統合 summary JSON を出力する。

P1: K={12,24} × LONG/SHORT (4 組合せ) → ml_phase1_v5_step_h_p1/
P2: K=48 × LONG/SHORT (2 組合せ)     → ml_phase1_v5_step_h_p2/
P3: K=96 × LONG/SHORT (2 組合せ)     → ml_phase1_v5_step_h_p3/

統合後 8 組合せで:
- n_combinations_all_pass / all_pass_combinations
- meets_6plus_criteria = n_combinations_all_pass >= 6
- layer3_investigation_needed = not meets_6plus_criteria
- anomaly_smell_detected = any per process
- anomaly_smell_per_combination = combined dict

Usage:
    python scripts/priority_rebuild/merge_step_h_summaries.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_P1 = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase1_v5_step_h_p1"
DEFAULT_P2 = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase1_v5_step_h_p2"
DEFAULT_P3 = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase1_v5_step_h_p3"
DEFAULT_OUT = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase1_v5_step_h_merged"

EXPECTED_COMBINATIONS = [
    "K12_LONG", "K12_SHORT",
    "K24_LONG", "K24_SHORT",
    "K48_LONG", "K48_SHORT",
    "K96_LONG", "K96_SHORT",
]


def load_summary(path: Path) -> dict:
    summary_path = path / "phase1_v5_summary.json"
    if not summary_path.exists():
        print(f"[error] not found: {summary_path}", file=sys.stderr)
        sys.exit(2)
    with open(summary_path) as f:
        return json.load(f)


def merge_summaries(p1: dict, p2: dict, p3: dict) -> Tuple[dict, List[str]]:
    """3 summary を統合し、§4.1 v5.1 判定を再計算。"""
    issues: List[str] = []
    merged_combinations: Dict[str, dict] = {}
    all_pass_combinations: List[str] = []
    anomaly_smell_combined: Dict[str, List[str]] = {}
    n_trials_set = set()

    for label, src in [("p1", p1), ("p2", p2), ("p3", p3)]:
        a = src.get("cases", {}).get("a_rmse", {})
        if not a:
            issues.append(f"{label}: cases.a_rmse 不在")
            continue
        n_trials_set.add(a.get("dsr_n_trials"))
        combos = a.get("combinations", {})
        for combo_key, combo_data in combos.items():
            if combo_key in merged_combinations:
                issues.append(f"{label}: duplicate combination {combo_key} (skip)")
                continue
            merged_combinations[combo_key] = combo_data
            summary = combo_data.get("summary", {})
            if summary.get("all_pass"):
                all_pass_combinations.append(combo_key)
        ans = a.get("anomaly_smell_per_combination", {})
        anomaly_smell_combined.update(ans)

    # expected 8 組合せの存在 verify
    missing = [c for c in EXPECTED_COMBINATIONS if c not in merged_combinations]
    extra = [c for c in merged_combinations if c not in EXPECTED_COMBINATIONS]
    if missing:
        issues.append(f"missing combinations: {missing}")
    if extra:
        issues.append(f"unexpected combinations: {extra}")

    n_combinations = len(merged_combinations)
    n_combinations_all_pass = len(all_pass_combinations)
    meets_6plus = n_combinations_all_pass >= 6
    layer3_needed = not meets_6plus

    if len(n_trials_set) > 1:
        issues.append(f"dsr_n_trials 不一致: {n_trials_set} (3 並列で同一であるべき)")
    n_trials = next(iter(n_trials_set)) if n_trials_set else None

    merged = {
        "cases": {
            "a_rmse": {
                "case_name": "a_rmse",
                "n_combinations": n_combinations,
                "combinations": merged_combinations,
                "n_combinations_all_pass": n_combinations_all_pass,
                "all_pass_combinations": sorted(all_pass_combinations),
                "meets_6plus_criteria": meets_6plus,
                "dsr_n_trials": n_trials,
                "layer3_investigation_needed": layer3_needed,
                "anomaly_smell_detected": bool(anomaly_smell_combined),
                "anomaly_smell_per_combination": anomaly_smell_combined,
                "anomaly_smell_note": (
                    "false_positive §5 関所 A: ④ DD は fold_metrics 未実装で skip。"
                    "①②③ のうち 1 つ以上ヒット → 「異常値・要調査」記録 "
                    "(Step G CP2 監査 C2 反映・2026-05-22)"
                ),
                "merge_info": {
                    "source_p1": str(DEFAULT_P1),
                    "source_p2": str(DEFAULT_P2),
                    "source_p3": str(DEFAULT_P3),
                    "merged_at": datetime.now().isoformat(),
                    "expected_combinations": EXPECTED_COMBINATIONS,
                    "merge_issues": issues,
                },
            }
        },
        "meta": {
            "spec_version": "v5.1",
            "combination_pass_count_required": 6,
            "K_default_list": [12, 24, 48, 96],
            "sides_default": ["LONG", "SHORT"],
        },
        "updated_at": datetime.now().isoformat(),
    }

    return merged, issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Step H 3 並列 summary マージ")
    parser.add_argument("--p1", type=Path, default=DEFAULT_P1, help=f"P1 out_base (既定 {DEFAULT_P1})")
    parser.add_argument("--p2", type=Path, default=DEFAULT_P2, help=f"P2 out_base (既定 {DEFAULT_P2})")
    parser.add_argument("--p3", type=Path, default=DEFAULT_P3, help=f"P3 out_base (既定 {DEFAULT_P3})")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"merge 出力先 (既定 {DEFAULT_OUT})")
    args = parser.parse_args()

    print(f"===== Step H summary merge START {datetime.now().isoformat()} =====")
    p1 = load_summary(args.p1)
    p2 = load_summary(args.p2)
    p3 = load_summary(args.p3)
    print(f"[load] P1 / P2 / P3 summary OK")

    merged, issues = merge_summaries(p1, p2, p3)

    args.out.mkdir(parents=True, exist_ok=True)
    out_path = args.out / "phase1_v5_summary_merged.json"
    with open(out_path, "w") as f:
        json.dump(merged, f, indent=2, default=str)
    print(f"[save] merged summary: {out_path}")

    a = merged["cases"]["a_rmse"]
    print(f"\n=== Step H 統合判定 (§4.1 v5.1) ===")
    print(f"n_combinations: {a['n_combinations']} (expected 8)")
    print(f"n_combinations_all_pass: {a['n_combinations_all_pass']}")
    print(f"all_pass_combinations: {a['all_pass_combinations']}")
    print(f"meets_6plus_criteria: {a['meets_6plus_criteria']}")
    print(f"layer3_investigation_needed: {a['layer3_investigation_needed']}")
    print(f"anomaly_smell_detected: {a['anomaly_smell_detected']}")
    if a["anomaly_smell_detected"]:
        print(f"anomaly_smell_per_combination:")
        for ck, trigs in a["anomaly_smell_per_combination"].items():
            print(f"  [{ck}] {len(trigs)} 件:")
            for trig in trigs:
                print(f"    - {trig}")
    if issues:
        print(f"\n⚠️ merge 警告:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    return 0 if a["meets_6plus_criteria"] else 1


if __name__ == "__main__":
    sys.exit(main())
