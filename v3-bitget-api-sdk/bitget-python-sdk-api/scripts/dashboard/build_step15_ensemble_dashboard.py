"""工程 [1.5] regime ensemble v3 視認チェック用ダッシュボードデータ生成 (= v16).

設計書: ml_pipeline_baseline_v1.md v2.8 §6.1 + CP1 監査
入力:
  results/regime_step1/regime_predictions_train_2021_2024.parquet (= 5m grid 最終出力 10 列)
  results/regime_step1/ensemble_artifact.json (= GridSearchCV 結果)
出力:
  dashboard/regime_prototype/labels_v16.csv
  dashboard/regime_prototype/predictions_v16_1h.json
  dashboard/regime_prototype/predictions_v16_1d.json
  dashboard/regime_prototype/index.json (= v16 エントリ追加)

動作確認:
  python scripts/dashboard/dashboard_server.py
  → http://localhost:8765/index.html → ⑪ レジーム試作 → v16
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
ENSEMBLE_OUTPUT = REPO_ROOT / "results/regime_step1/regime_predictions_train_2021_2024.parquet"
ENSEMBLE_ARTIFACT = REPO_ROOT / "results/regime_step1/ensemble_artifact.json"
KMEANS_ARTIFACT = REPO_ROOT / "results/regime_step1/kmeans_classifier_artifact.json"
STAGE1_REPORT = REPO_ROOT / "results/regime_step1/stage1_evaluation_report.json"

PROTO_DIR = REPO_ROOT / "dashboard" / "regime_prototype"
INDEX_JSON = PROTO_DIR / "index.json"
VERSION = "v16"
OUT_CSV = PROTO_DIR / f"labels_{VERSION}.csv"


def main() -> int:
    for p in [ENSEMBLE_OUTPUT, ENSEMBLE_ARTIFACT, INDEX_JSON]:
        if not p.exists():
            sys.exit(f"ABORT: missing input: {p}")

    print(f"[1/4] loading 5m predictions ...")
    df_5m = pd.read_parquet(ENSEMBLE_OUTPUT)
    print(f"    5m rows: {len(df_5m)}")

    print(f"[2/4] reducing 5m → 1h (= 各 1h close 時点の確定 ensemble 出力) ...")
    df_1h = df_5m.resample("1h", label="right", closed="right").last()
    df_1h = df_1h.dropna(subset=["regime_label"])
    print(f"    1h rows: {len(df_1h)}")

    # CSV (= 視認チェック用・date + regime + 確信度)
    out_df = pd.DataFrame({
        "datetime_utc": df_1h.index.tz_localize("UTC") if df_1h.index.tz is None else df_1h.index,
        "regime": df_1h["regime_label"].astype(str),
        "prob_up": df_1h["regime_prob_up"].round(4),
        "prob_down": df_1h["regime_prob_down"].round(4),
        "prob_range": df_1h["regime_prob_range"].round(4),
        "confidence": df_1h["regime_confidence"].round(4),
        "volatility_level": df_1h["regime_volatility_level"].astype(str),
    })
    PROTO_DIR.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False)
    print(f"    saved CSV: {OUT_CSV.name} ({len(out_df)} rows)")

    # ===== compact array JSON (= ダッシュボード前段の app.js が期待する形式) =====
    # 各行 = [ts_ms, close_int, predicted_label, human_label]
    # close を 5m parquet から取り出す
    print(f"[3/4] generating compact array JSON (1h + 1d) ...")
    src_parquet = REPO_ROOT / "results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet"
    close_5m = pd.read_parquet(src_parquet, columns=["close"])["close"].astype(float)
    close_1h_full = close_5m.resample("1h", label="right", closed="right").last()
    close_1h = close_1h_full.reindex(df_1h.index).ffill().round().astype(int)

    ts_ms_1h = (df_1h.index.astype("int64") // 10**6).tolist()
    rows_1h = [
        [int(ts), int(c), str(reg), ""]
        for ts, c, reg in zip(ts_ms_1h, close_1h.tolist(), df_1h["regime_label"].tolist())
    ]
    pred_1h_path = PROTO_DIR / f"predictions_{VERSION}_1h.json"
    pred_1h_path.write_text(
        json.dumps({"version": VERSION, "granularity": "1h", "rows": rows_1h}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"    saved: {pred_1h_path.name} ({len(rows_1h)} rows)")

    # 1d 集約 (= 24h 最頻 regime + 日次終値)
    daily = pd.DataFrame({
        "close": close_1h.values,
        "regime": df_1h["regime_label"].astype(str).values,
        "date": df_1h.index.normalize(),
    }, index=df_1h.index)
    daily_pred = daily.groupby("date").agg(
        close=("close", "last"),
        regime=("regime", lambda s: s.value_counts().idxmax()),
    )
    ts_ms_1d = (daily_pred.index.astype("int64") // 10**6).tolist()
    rows_1d = [
        [int(ts), int(c), str(reg), ""]
        for ts, c, reg in zip(ts_ms_1d, daily_pred["close"].tolist(), daily_pred["regime"].tolist())
    ]
    pred_1d_path = PROTO_DIR / f"predictions_{VERSION}_1d.json"
    pred_1d_path.write_text(
        json.dumps({"version": VERSION, "granularity": "1d", "rows": rows_1d}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"    saved: {pred_1d_path.name} ({len(rows_1d)} rows)")

    # 分布
    counts = out_df["regime"].value_counts().to_dict()
    total = len(out_df)
    distribution = {
        lbl: {"count": int(counts.get(lbl, 0)),
              "pct": round(counts.get(lbl, 0) / total * 100, 2)}
        for lbl in ["range", "uptrend", "downtrend", "unclear"]
    }
    print(f"    distribution: {distribution}")

    # ===== index.json 更新 =====
    print(f"[4/4] updating index.json with {VERSION} entry ...")
    ensemble_meta = json.loads(ENSEMBLE_ARTIFACT.read_text())
    km_meta = json.loads(KMEANS_ARTIFACT.read_text()) if KMEANS_ARTIFACT.exists() else {}
    stage1 = json.loads(STAGE1_REPORT.read_text()) if STAGE1_REPORT.exists() else {}

    index_obj = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    index_obj["prototypes"] = [p for p in index_obj["prototypes"] if p.get("version") != VERSION]

    new_entry = {
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "spec": {
            "method": "regime_ensemble_v3 (= rule + kmeans + hmm soft voting)",
            "design_doc": ".claude/memory/ml_pipeline_baseline_v1.md (v2.8 §6.1)",
            "cp1_audit_reflected": True,
            "ensemble_weights": ensemble_meta.get("best_weights"),
            "ensemble_classifiers": ensemble_meta.get("classifiers"),
            "kmeans_features_v3": [
                "obv_slope_10b__1h", "streak_diff_1h",
                "zscore_return_20b__1h", "donchian_position_20__1h",
            ],
            "kmeans_chosen_k": km_meta.get("chosen_k"),
            "target_config": ensemble_meta.get("target_config"),
            "hysteresis_bars": 2,
            "unclear_conf_threshold": ensemble_meta.get("unclear_conf_threshold"),
            "output_granularity": "1h (= reduced from 5m)",
        },
        "distribution": distribution,
        "evaluation": {
            "method": "gridsearch_cv_weight + brier + ece + pearson_error_corr",
            "best_f1_macro": ensemble_meta.get("best_f1_macro"),
            "best_accuracy": ensemble_meta.get("best_accuracy"),
            "best_log_loss": ensemble_meta.get("best_log_loss"),
            "equal_weight_f1": ensemble_meta.get("equal_weight_f1"),
            "stage1_train": stage1.get("per_dataset", {}).get("train_2021_2024"),
        },
    }
    index_obj["prototypes"].append(new_entry)
    INDEX_JSON.write_text(json.dumps(index_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    index.json updated: {VERSION} appended (total {len(index_obj['prototypes'])} prototypes)")

    print(f"\n[DONE] dashboard data ready. Start server with:")
    print(f"    python scripts/dashboard/dashboard_server.py")
    print(f"    → http://localhost:8765/index.html → ⑪ レジーム試作 → {VERSION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
