"""
工程 [1.5] regime ensemble — HMM v15 既存 + isotonic キャリブレーション (Stage D)

設計書: .claude/memory/ml_pipeline_baseline_v1.md v2.8 §6.1.2 + §6.1.5
CP1 監査 C1 反映: HMM predict_proba 出力に isotonic regression キャリブレーション追加

機能:
  1. v15 HMM artifact (hmm_train_2021_2024.joblib + scaler_train_2021_2024.joblib) をロード
  2. train_hmm_regime.py の build_input_matrix を再利用して 84 列入力行列を構築
  3. 1h grid に reduce → predict_proba 取得
  4. state ID → label (uptrend/downtrend/range) にマッピング (= state_labels_train_2021_2024.json)
  5. isotonic キャリブレーション fit (= train_2021_2024 全期間 1 calibrator・target = future 4h log_return 3 クラス)
  6. 3 dataset 全部に適用 → 出力 parquet

入力:
  - results/regime_step1/hmm_train_2021_2024.joblib (v15 既存)
  - results/regime_step1/scaler_train_2021_2024.joblib (v15 既存)
  - results/regime_step1/state_labels_train_2021_2024.json (v15 既存)
  - results/priority_rebuild/labels_mfe_mae_pct_{ds}.parquet
出力:
  - results/regime_step1/hmm_calibrated_{ds}.parquet
  - results/regime_step1/hmm_isotonic_train_2021_2024.joblib
  - results/regime_step1/hmm_calibrated_artifact.json

CC 独断・要レビュー項目:
  H1: state ID → label mapping は state_labels_train_2021_2024.json から抽出 (= v15 既存)
       中身: "上昇"/"下落"/"レンジ" → "uptrend"/"downtrend"/"range"
  H2: isotonic fit は target = future 4h log_return 3 クラス (= T1, T2)
  H3: isotonic fit は train_2021_2024 全期間 1 calibrator (= T4)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

# 共通モジュール
sys.path.insert(0, str(Path(__file__).resolve().parent))
from regime_target_labels import compute_target_for_dataset, get_config as target_config
import train_hmm_regime as thr  # build_input_matrix / hourly_resample_for_regime / drop_nan

# パス
REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "results/regime_step1"
HMM_PATH = OUT_DIR / "hmm_train_2021_2024.joblib"
SCALER_PATH = OUT_DIR / "scaler_train_2021_2024.joblib"
LABELS_PATH = OUT_DIR / "state_labels_train_2021_2024.json"
ISO_ARTIFACT = OUT_DIR / "hmm_isotonic_train_2021_2024.joblib"
CALIBRATED_ARTIFACT_JSON = OUT_DIR / "hmm_calibrated_artifact.json"

DATASETS = ["train_2021_2024", "test_2025", "test_2026_q1"]

# H1: 日本語 → 英語ラベルマッピング
JP_TO_EN = {"上昇": "uptrend", "下落": "downtrend", "レンジ": "range"}


def load_state_label_map() -> dict[int, str]:
    """v15 HMM state ID → 英語ラベル."""
    with LABELS_PATH.open() as f:
        labels = json.load(f)
    state_to_jp = {int(k): v for k, v in labels["state_to_label"].items()}
    return {sid: JP_TO_EN.get(jp, "unknown") for sid, jp in state_to_jp.items()}


def predict_proba_for_ds(ds: str, hmm, scaler, state_to_label_en: dict[int, str]) -> pd.DataFrame:
    """1 dataset の HMM predict_proba を 1h grid で計算し label aggregated 確率を返す.

    train_hmm_regime.py の build_input_matrix を再利用 → 84 列入力構築.
    1h grid に reduce → predict_proba → state probs → label aggregated probs.
    """
    parquet_path = REPO_ROOT / "results/priority_rebuild" / f"labels_mfe_mae_pct_{ds}.parquet"
    print(f"  loading parquet: {parquet_path.name}")
    df = pd.read_parquet(parquet_path)

    # 84 列入力 (train_hmm_regime.py L152-218 の build_input_matrix)
    # 注意: build_input_matrix は INPUT_OHLCV_CSV (= data/BTCUSDT-...csv) から atr14_pct__1d を補填する
    # → test_2025/test_2026_q1 でも同じ CSV から train 期間外の 1d ATR を補填可能か確認必要
    # build_input_matrix 内で df.index の min/max を使って CSV をトリムするので、期間外でも動く想定
    X_5m = thr.build_input_matrix(df)
    print(f"    5m 84-col shape: {X_5m.shape}")

    X_1h = thr.hourly_resample_for_regime(X_5m)
    print(f"    1h grid shape: {X_1h.shape}")

    # NaN は drop (= 学習時と同じ)
    valid_mask = X_1h.notna().all(axis=1)
    X_1h_valid = X_1h[valid_mask]
    print(f"    after NaN drop: {len(X_1h_valid)}")

    # predict_proba
    X_scaled = scaler.transform(X_1h_valid.values)
    state_probs = hmm.predict_proba(X_scaled)  # (n, n_states)
    state_labels = hmm.predict(X_scaled)  # (n,)
    log_lik = hmm.score(X_scaled)
    print(f"    log_likelihood: {log_lik:.2f}")

    # state ID → label aggregated probs
    label_probs = {"uptrend": np.zeros(len(X_1h_valid)), "downtrend": np.zeros(len(X_1h_valid)), "range": np.zeros(len(X_1h_valid))}
    for sid, lbl in state_to_label_en.items():
        if lbl in label_probs:
            label_probs[lbl] += state_probs[:, sid]

    df_probs = pd.DataFrame(label_probs, index=X_1h_valid.index)
    # state predicted label を debug 用に保持
    df_probs["_state_id"] = state_labels
    df_probs["_state_label"] = [state_to_label_en[int(s)] for s in state_labels]

    # 元の 1h grid index に reindex (= NaN サンプルは NaN のまま)
    return df_probs.reindex(X_1h.index), log_lik, X_1h.index


def fit_isotonic(raw_probs: pd.DataFrame, target_label: pd.Series) -> dict[str, IsotonicRegression]:
    cals: dict[str, IsotonicRegression] = {}
    for cat in ["uptrend", "downtrend", "range"]:
        m = raw_probs[cat].notna() & target_label.notna()
        x = raw_probs.loc[m, cat].values
        y = (target_label.loc[m] == cat).astype(float).values
        if len(x) < 100:
            print(f"  WARN: isotonic skipped for {cat} (n={len(x)})")
            cals[cat] = None
            continue
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        iso.fit(x, y)
        cals[cat] = iso
    return cals


def apply_isotonic(raw_probs: pd.DataFrame, cals: dict) -> pd.DataFrame:
    cal_probs: dict[str, pd.Series] = {}
    for cat in ["uptrend", "downtrend", "range"]:
        if cals.get(cat) is None:
            cal_probs[cat] = raw_probs[cat].copy()
        else:
            valid = raw_probs[cat].notna()
            ser = pd.Series(index=raw_probs.index, dtype=float)
            ser[valid] = cals[cat].predict(raw_probs.loc[valid, cat].values)
            cal_probs[cat] = ser
    df = pd.DataFrame(cal_probs)
    s = df.sum(axis=1)
    df = df.div(s.where(s > 0, 1.0 / 3.0), axis=0)
    return df


def main() -> int:
    print(f"[output dir] {OUT_DIR}")

    # ========== v15 artifact ロード ==========
    print("\n[1/4] loading v15 HMM artifacts ...")
    hmm = joblib.load(HMM_PATH)
    scaler = joblib.load(SCALER_PATH)
    state_to_label_en = load_state_label_map()
    print(f"  state_to_label_en: {state_to_label_en}")

    # ========== train_2021_2024 で raw probs 取得 + isotonic fit ==========
    print("\n[2/4] computing raw probs for train_2021_2024 ...")
    raw_train, ll_train, idx_train = predict_proba_for_ds("train_2021_2024", hmm, scaler, state_to_label_en)
    target_train_df = compute_target_for_dataset("train_2021_2024")
    target_train = target_train_df["target_3class"].reindex(raw_train.index)

    print("\n[3/4] fitting isotonic calibrators (target = future 4h log_return 3-class) ...")
    raw_probs_only_train = raw_train[["uptrend", "downtrend", "range"]]
    cals = fit_isotonic(raw_probs_only_train, target_train)
    print(f"  isotonic fitted: {[k for k, v in cals.items() if v is not None]}")

    # ========== 3 dataset 全部に適用 ==========
    print("\n[4/4] applying to all 3 datasets ...")
    summaries: dict = {}
    log_liks: dict = {"train_2021_2024": ll_train}

    for ds in DATASETS:
        print(f"\n  ----- {ds} -----")
        if ds == "train_2021_2024":
            raw = raw_train
            ll = ll_train
        else:
            raw, ll, _ = predict_proba_for_ds(ds, hmm, scaler, state_to_label_en)
            log_liks[ds] = ll

        raw_only = raw[["uptrend", "downtrend", "range"]]
        cal = apply_isotonic(raw_only, cals)

        full_index = raw.index
        out = pd.DataFrame(index=full_index)
        out["regime_label"] = cal.idxmax(axis=1).where(cal.notna().all(axis=1), "unknown")
        out["regime_prob_up"] = cal["uptrend"]
        out["regime_prob_down"] = cal["downtrend"]
        out["regime_prob_range"] = cal["range"]
        out["regime_confidence"] = (cal.max(axis=1) - cal.apply(lambda r: sorted(r.values)[-2] if r.notna().all() else np.nan, axis=1))
        out["_raw_prob_up"] = raw_only["uptrend"]
        out["_raw_prob_down"] = raw_only["downtrend"]
        out["_raw_prob_range"] = raw_only["range"]
        out["_state_id"] = raw["_state_id"]
        out["_state_label"] = raw["_state_label"]

        out_path = OUT_DIR / f"hmm_calibrated_{ds}.parquet"
        out.to_parquet(out_path)
        dist = out["regime_label"].value_counts(dropna=False).to_dict()
        print(f"    rows={len(out)}, label dist: {dist}, log_lik={ll:.2f}")
        summaries[ds] = {
            "rows": int(len(out)),
            "label_distribution": {str(k): int(v) for k, v in dist.items()},
            "log_likelihood": float(ll),
        }

    # ========== artifact 保存 ==========
    joblib.dump(cals, ISO_ARTIFACT)
    print(f"\n  isotonic saved: {ISO_ARTIFACT}")

    artifact = {
        "script": str(Path(__file__).relative_to(REPO_ROOT)),
        "design_doc": ".claude/memory/ml_pipeline_baseline_v1.md (v2.8 §6.1.2 + §6.1.5)",
        "cp1_audit": ".claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md",
        "hmm_path": str(HMM_PATH),
        "scaler_path": str(SCALER_PATH),
        "state_to_label_en": state_to_label_en,
        "isotonic_path": str(ISO_ARTIFACT),
        "log_likelihoods": log_liks,
        "summaries": summaries,
        "target_config": target_config(),
        "cc_independent_judgements": [
            "H1: state ID → 英語ラベル変換 (v15 既存 mapping から)",
            "H2: isotonic target = future 4h log_return 3-class",
            "H3: isotonic fit = train_2021_2024 全期間 1 calibrator",
        ],
    }
    with CALIBRATED_ARTIFACT_JSON.open("w") as f:
        json.dump(artifact, f, ensure_ascii=False, indent=2, default=str)
    print(f"  artifact saved: {CALIBRATED_ARTIFACT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
