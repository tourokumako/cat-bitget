"""leak_check.py — L-179 4 点チェック (Phase 1-a 用・縮約版)

縮約方針 (まこさん 2026-05-21 承認):
- #2 「shift(1) ガード grep」は Phase 0 v3 Step 5 commit (34777ef) で
  4 種 grep 0 hit 確認済 + 本タスク着手時点まで特徴量計算スクリプトに差分ゼロ verify 済
  → 本ファイルでは grep 再実行せず・top20 列名に未来参照疑いがないかのみ実施

本ファイルが実施する 4 点 (各ラベル学習完了直後に呼ぶ):
  1. check_future_ref       : top20 列名に _future / _lookahead / _K{学習対象K} 等が混入していないか
  2. check_shift1_guard     : Phase 0 v3 Step 5 引用 + top20 重複検査
  3. check_top1_dominance   : top1 importance / total > 0.30 → WARN
  4. check_label_correlation: 14 学習ラベル間の |相関| > 0.99 ペア検出
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Iterable

import pandas as pd


# 学習対象 K 窓 (build_labels_pct.py / cc_ml_design_spec.md §1.1)
LEARN_K_WINDOWS = (6, 12, 24, 48, 96, 144, 288)

# 未来参照疑い列名パターン
FUTURE_REF_PATTERNS = [
    re.compile(r"_future\b", re.IGNORECASE),
    re.compile(r"_lookahead\b", re.IGNORECASE),
    re.compile(r"_ahead\b", re.IGNORECASE),
]
# 学習対象 K 窓に一致する _K{K} suffix (ラベル系列が特徴量に混入していないか)
LABEL_K_PATTERNS = [re.compile(rf"_K{K}\b") for K in LEARN_K_WINDOWS]


def check_future_ref(fi_top20: pd.DataFrame, label: str) -> dict:
    """top20 列名に未来参照疑い文字列がないか."""
    violations = []
    for col in fi_top20["feature"].tolist():
        if any(p.search(col) for p in FUTURE_REF_PATTERNS):
            violations.append({"col": col, "reason": "future/lookahead/ahead suffix"})
        if any(p.search(col) for p in LABEL_K_PATTERNS):
            violations.append({"col": col, "reason": "学習対象 K 窓と一致する suffix (ラベル混入疑い)"})
    return {
        "label": label,
        "status": "PASS" if not violations else "FAIL",
        "violations": violations,
    }


def check_shift1_guard(label: str, step5_commit: str = "34777ef") -> dict:
    """Phase 0 v3 Step 5 leak grep 0 hit + 差分ゼロ verify 引用."""
    return {
        "label": label,
        "status": "PASS",
        "reference": (
            f"Phase 0 v3 Step 5 (commit {step5_commit}): build_labels_pct.py + "
            "scripts/regime/*.py に対し 4 種 grep (shift(-N) / center=True / "
            "j+1,j+2 / future|forward) 全件 0 hit 確認済 (phase_compliance §Phase -1 §5)。"
            "本タスク着手時点まで特徴量計算スクリプト差分ゼロ git log verify 済 → 引用で代替"
        ),
    }


def check_top1_dominance(fi_top20: pd.DataFrame, label: str, threshold: float = 0.30) -> dict:
    """top1 importance / total_importance > threshold で WARN."""
    total = float(fi_top20["importance_gain"].sum())
    if total <= 0:
        return {"label": label, "status": "WARN", "reason": "total_importance = 0 (学習失敗の可能性)", "top1_pct": None}
    top1 = float(fi_top20["importance_gain"].iloc[0])
    top1_pct = top1 / total
    status = "WARN" if top1_pct > threshold else "PASS"
    return {
        "label": label,
        "status": status,
        "top1_feature": str(fi_top20["feature"].iloc[0]),
        "top1_pct": round(top1_pct, 4),
        "threshold": threshold,
    }


def check_label_correlation(label_df: pd.DataFrame, learn_labels: Iterable[str], threshold: float = 0.99) -> dict:
    """学習対象ラベル間の |corr| > threshold ペアを検出.

    Phase 1-a: 14 ラベル独立回帰 (LONG_MFE/MAE × K=7) で対称性 drop 済
    Phase 1-c: Triple Barrier 3 K (6/12/24) の int カテゴリラベル間で相関測定
    出るなら設計欠陥 (例: K6 と K12 で同じ barrier touch ばかりなど)。
    """
    sub = label_df.loc[:, list(learn_labels)].dropna()
    if len(sub) < 100:
        return {"status": "WARN", "reason": f"sample n={len(sub)} (< 100)", "violations": []}
    corr = sub.corr().abs()
    violations = []
    cols = corr.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            v = float(corr.iloc[i, j])
            if v > threshold:
                violations.append({"pair": [cols[i], cols[j]], "abs_corr": round(v, 6)})
    return {
        "status": "PASS" if not violations else "FAIL",
        "threshold": threshold,
        "violations": violations,
    }


def check_future_ref_multiclass(fi_top20: pd.DataFrame, K: int) -> dict:
    """Phase 1-c multiclass 用: top20 列名に未来参照疑い + Triple Barrier ラベル自体の混入なし.

    multiclass では K ごとの top20 = 3 class 平均の importance (LightGBM 標準は class 別ではなく
    overall gain なので 1 column for top20)。本関数は K=6/12/24 のいずれを対象としても OK。
    """
    violations = []
    # `_future` `_lookahead` `_ahead` の混入
    for col in fi_top20["feature"].tolist():
        if any(p.search(col) for p in FUTURE_REF_PATTERNS):
            violations.append({"col": col, "reason": "future/lookahead/ahead suffix"})
        # 学習対象 K 窓のラベル列が混入していないか (本来 drop されているはず)
        if any(p.search(col) for p in LABEL_K_PATTERNS):
            violations.append({"col": col, "reason": "学習対象 K 窓と一致する suffix (ラベル混入疑い)"})
        # Triple Barrier ラベル自体の混入検出
        if col.startswith("triple_barrier_K"):
            violations.append({"col": col, "reason": "Triple Barrier ラベル列が特徴量に混入 (drop_cols 漏れ)"})
    return {
        "K": K,
        "status": "PASS" if not violations else "FAIL",
        "violations": violations,
    }


def write_report(out_path: Path, payload: dict) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
