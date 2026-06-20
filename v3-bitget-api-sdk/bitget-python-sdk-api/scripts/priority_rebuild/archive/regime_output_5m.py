"""
工程 [1.5] regime ensemble — 5m grid 出力 6 列 + merge_asof backward causal alignment (Stage F)

設計書: .claude/memory/ml_pipeline_baseline_v1.md v2.8 §6.1.6
CP1 監査 M3 反映: merge_asof(direction="backward") + assert no look-ahead

機能:
  1. ensemble_{ds}.parquet (1h grid) と rule_classifier_{ds}.parquet (volatility_level 1h grid) をマージ
  2. 5m grid に merge_asof(direction="backward") で causal alignment
     - 5m timestamp t に対し、t 以前の最新の 1h judgment を充当
     - 1h bar `14:00:00 - 14:59:59` の close (= label="right", closed="right") = 14:00:00 という pandas resample 仕様
       → 5m bar 14:00 に 1h judgment 14:00 が allow 充当 (= 14:00 close 時点で 1h 確定)
  3. assert no look-ahead: 全 5m bar の regime source 1h timestamp <= 5m timestamp を verify
  4. 出力 6 列 + one-hot encoded 派生列
  5. 保存: results/regime_step1/regime_predictions_{ds}.parquet

入力:
  - results/regime_step1/ensemble_{ds}.parquet (1h grid)
  - results/regime_step1/rule_classifier_{ds}.parquet (1h grid・volatility_level 抽出用)
  - results/priority_rebuild/labels_mfe_mae_pct_{ds}.parquet (5m grid index)
出力:
  - results/regime_step1/regime_predictions_{ds}.parquet
  - results/regime_step1/regime_predictions_artifact.json

CC 独断・要レビュー項目:
  F1: 「regime_label = unclear」の判定は ensemble の不明確閾値時のヒステリシス維持結果から派生 (= range 維持されているので unclear ラベルは表面化しない)
       v2.8 §6.1.6 で「regime_label = uptrend / downtrend / range / unclear」と 4 値だが、本実装は前 3 値のみ
       根拠: ヒステリシス維持により unclear はラベル化されない・要レビュー
  F2: causal alignment の前提 = 5m parquet の index timestamp が「bar close 時刻」
       根拠: Phase 0 v3.1 build_labels_pct.py L60 で `timestamp` を index 化し close__1h 等が ffill 済
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = REPO_ROOT / "results/priority_rebuild"
OUT_DIR = REPO_ROOT / "results/regime_step1"
ARTIFACT_JSON = OUT_DIR / "regime_predictions_artifact.json"

DATASETS = ["train_2021_2024", "test_2025", "test_2026_q1"]

OUTPUT_COLS_CORE = [
    "regime_label",
    "regime_prob_up",
    "regime_prob_down",
    "regime_prob_range",
    "regime_confidence",
    "regime_volatility_level",
]
ONE_HOT_COLS = ["regime_is_uptrend", "regime_is_downtrend", "regime_is_range", "regime_is_unclear"]


def load_5m_index(ds: str) -> pd.DatetimeIndex:
    p = INPUT_DIR / f"labels_mfe_mae_pct_{ds}.parquet"
    df = pd.read_parquet(p, columns=["close"])
    return df.sort_index().index


def load_1h_inputs(ds: str) -> pd.DataFrame:
    """ensemble + rule_classifier の 1h grid を統合."""
    ens_path = OUT_DIR / f"ensemble_{ds}.parquet"
    rule_path = OUT_DIR / f"rule_classifier_{ds}.parquet"
    ens = pd.read_parquet(ens_path)
    rule = pd.read_parquet(rule_path)
    merged = ens[[c for c in OUTPUT_COLS_CORE if c in ens.columns]].copy()
    merged["regime_volatility_level"] = rule["regime_volatility_level"]
    return merged


def merge_asof_backward(idx_5m: pd.DatetimeIndex, df_1h: pd.DataFrame) -> pd.DataFrame:
    """5m index に対し 1h judgment を backward causal alignment.

    pandas.merge_asof(direction="backward") は left.index の各時点に対し right.index <= left.index の最大を選ぶ.
    → causal: 5m time t の judgment は t 以前の最新 1h close 時刻のもの
    """
    left = pd.DataFrame(index=idx_5m).reset_index().rename(columns={"index": "_5m_ts", "timestamp": "_5m_ts"})
    # 列名: 5m parquet の index 名が "timestamp" or 無名なので reset_index 後の名前を正規化
    if "_5m_ts" not in left.columns:
        # 場合により reset_index 結果が "index" の場合
        first_col = left.columns[0]
        left = left.rename(columns={first_col: "_5m_ts"})

    right = df_1h.reset_index().rename(columns={df_1h.index.name or "index": "_1h_ts"})
    if "_1h_ts" not in right.columns:
        first_col = right.columns[0]
        right = right.rename(columns={first_col: "_1h_ts"})

    left = left.sort_values("_5m_ts")
    right = right.sort_values("_1h_ts")
    merged = pd.merge_asof(left, right, left_on="_5m_ts", right_on="_1h_ts", direction="backward")
    merged = merged.set_index("_5m_ts")
    merged.index.name = "timestamp"

    # 1h timestamp も debug 用に保持 (= assert no look-ahead 用)
    merged = merged.rename(columns={"_1h_ts": "_source_1h_ts"})
    return merged


def assert_no_look_ahead(merged: pd.DataFrame) -> dict:
    """5m timestamp >= source 1h timestamp を verify (= causal alignment)."""
    src = merged["_source_1h_ts"]
    target = merged.index
    valid_src = src.notna()
    if valid_src.sum() == 0:
        return {"valid_rows": 0, "violations": 0, "min_lag_seconds": None, "max_lag_seconds": None}

    src_valid = src[valid_src]
    target_valid = target[valid_src]
    lags = (target_valid - pd.DatetimeIndex(src_valid)).total_seconds()
    violations = int((lags < 0).sum())
    if violations > 0:
        # 違反例を 5 件まで dump
        idx_viol = (lags < 0)
        viol_rows = pd.DataFrame({
            "5m_ts": target_valid[idx_viol][:5],
            "source_1h_ts": pd.DatetimeIndex(src_valid)[idx_viol][:5],
            "lag_seconds": lags[idx_viol][:5],
        })
        print("[ERROR] look-ahead violations:")
        print(viol_rows.to_string())
        sys.exit(f"ABORT: {violations} look-ahead violations in causal alignment")
    return {
        "valid_rows": int(valid_src.sum()),
        "violations": int(violations),
        "min_lag_seconds": float(lags.min()),
        "max_lag_seconds": float(lags.max()),
        "median_lag_seconds": float(lags.median() if hasattr(lags, "median") else 0),
    }


def add_one_hot(out: pd.DataFrame) -> pd.DataFrame:
    """one-hot encoded 派生列を追加."""
    out["regime_is_uptrend"] = (out["regime_label"] == "uptrend").astype(int)
    out["regime_is_downtrend"] = (out["regime_label"] == "downtrend").astype(int)
    out["regime_is_range"] = (out["regime_label"] == "range").astype(int)
    out["regime_is_unclear"] = (~out["regime_label"].isin(["uptrend", "downtrend", "range"])).astype(int)
    return out


def main() -> int:
    print(f"[output dir] {OUT_DIR}")

    summaries: dict = {}

    for ds in DATASETS:
        print(f"\n----- {ds} -----")
        idx_5m = load_5m_index(ds)
        df_1h = load_1h_inputs(ds)
        print(f"  5m rows: {len(idx_5m)}, 1h rows: {len(df_1h)}")

        merged = merge_asof_backward(idx_5m, df_1h)
        print(f"  after merge_asof shape: {merged.shape}")

        # assert no look-ahead
        causal = assert_no_look_ahead(merged)
        print(f"  causal alignment: valid_rows={causal['valid_rows']} violations={causal['violations']} median_lag_sec={causal['median_lag_seconds']:.0f}")

        # 出力 6 列 + 派生 4 列
        out = merged[OUTPUT_COLS_CORE].copy()
        # NaN ラベルは "unclear" にする (= F1)
        out["regime_label"] = out["regime_label"].fillna("unclear")
        out = add_one_hot(out)

        # 確認: 5m index と完全一致
        assert (out.index == idx_5m).all(), f"index mismatch for {ds}"

        out_path = OUT_DIR / f"regime_predictions_{ds}.parquet"
        out.to_parquet(out_path)
        print(f"  written: {out_path}")
        print(f"  output shape: {out.shape}")
        dist = out["regime_label"].value_counts(dropna=False).to_dict()
        vol = out["regime_volatility_level"].value_counts(dropna=False).to_dict()
        print(f"  regime_label dist: {dist}")
        print(f"  volatility_level dist: {vol}")

        summaries[ds] = {
            "rows_5m": int(len(out)),
            "label_distribution": {str(k): int(v) for k, v in dist.items()},
            "volatility_distribution": {str(k): int(v) for k, v in vol.items()},
            "causal_alignment": causal,
        }

    artifact = {
        "script": str(Path(__file__).relative_to(REPO_ROOT)),
        "design_doc": ".claude/memory/ml_pipeline_baseline_v1.md (v2.8 §6.1.6)",
        "cp1_audit": ".claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md",
        "output_cols_core": OUTPUT_COLS_CORE,
        "one_hot_cols": ONE_HOT_COLS,
        "causal_alignment_rule": "merge_asof(direction='backward') + assert no look-ahead",
        "summaries": summaries,
        "cc_independent_judgements": [
            "F1: 5m bar に NaN ラベルが残った場合 = 'unclear' に置換 (= ヒステリシスでは表面化しない設計)",
            "F2: causal alignment 前提 = 5m parquet index は bar close 時刻表記",
        ],
    }
    with ARTIFACT_JSON.open("w") as f:
        json.dump(artifact, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n[DONE] artifact: {ARTIFACT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
