"""run_phase2_meta_secondary.py — 後段 meta(secondary)学習・縦カスケードの価値検証

2026-05-31 execlog 0章「合意した修正方針」step 1 の核。
build_metalabel_dataset.py で作った「前段が発火したバー」集合に対し、
後段 meta モデル(features → その賭けが勝つか)を学習し、
**「発火集合の中から勝ち筋を選び出せるか」**を OOF AUC + lift で測る。

問い: 前段のエッジは薄い(発火集合の素勝率 37%)。後段が features を使って、
      この中から勝つ賭けを選別できる(AUC > 0.5・上位予測の勝率 > 37%)か?
      - YES → 縦リレーが価値を生む。test 期間評価 + 後段レバー統合へ。
      - NO  → 前段のエッジ自体を作り直す(K 集約・特徴量見直し)番。

設計(baseline と揃える・leak 安全):
  - 入力 X = labels_mfe_mae_pct_train_2021_2024.parquet の特徴量(blacklist 除外)+ regime 8 列
  - 対象 = 発火バーのみ(metalabel_train_2021_2024.parquet・θ=0.40)
  - 教師 = meta_label(発火方向の TP 先着 1/0)
  - CV = baseline と同じ purged walk-forward k-fold(embargo K_max=288)。各 fold の
        train 部分の発火バーで学習 → test 部分の発火バーを予測 → OOF 集約
  - 早期終了用 valid = 各 fold train の時系列末尾 10%

使い方:
  python run_phase2_meta_secondary.py --smoke   # 1 fold のみ(動作確認)
  python run_phase2_meta_secondary.py           # 3 fold OOF
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.priority_rebuild.run_phase1_v5_purged_kfold import (  # noqa: E402
    load_parquet_with_blacklist,
    prepare_purged_cv,
    split_with_purging,
)
from scripts.priority_rebuild.run_phase2_entry_ml_baseline import (  # noqa: E402
    LGB_DEFAULT_PARAMS_BASE,
    EARLY_STOPPING_ROUNDS,
    PARQUET_TRAIN,
    PARQUET_REGIME,
    merge_regime_columns,
    compute_scale_pos_weight,
)

LABEL_K_MAX = 288
N_SPLITS = 5  # → 実 yield 3 fold
VALID_TAIL_FRACTION = 0.10
FIRED_TRAIN = REPO_ROOT / "results" / "priority_rebuild" / "metalabel_dataset" / "metalabel_train_2021_2024.parquet"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase2_meta_secondary"


def train_binary(X_tr, y_tr, X_va, y_va, X_te):
    spw = compute_scale_pos_weight(y_tr.astype(int))
    params = {**LGB_DEFAULT_PARAMS_BASE,
              "objective": "binary", "metric": "binary_logloss",
              "scale_pos_weight": spw}
    model = lgb.LGBMClassifier(**params)
    model.fit(X_tr, y_tr.astype(int),
              eval_set=[(X_va, y_va.astype(int))], eval_metric="binary_logloss",
              callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)])
    return model.predict_proba(X_te)[:, 1], model


def lift_report(y: np.ndarray, p: np.ndarray) -> dict:
    """素勝率に対し、後段予測の上位群がどれだけ勝率を上げるか。"""
    base = float(y.mean())
    order = np.argsort(-p)
    out = {"base_win_%": round(100 * base, 1), "n": int(len(y))}
    for q, name in [(0.10, "top10%"), (0.25, "top25%"), (0.50, "top50%")]:
        k = max(1, int(len(y) * q))
        out[f"{name}_win_%"] = round(100 * float(y[order[:k]].mean()), 1)
    # gate at pred>0.5
    gate = p > 0.5
    out["gate>0.5_n"] = int(gate.sum())
    out["gate>0.5_win_%"] = round(100 * float(y[gate].mean()), 1) if gate.sum() else None
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="1 fold のみ")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    print(f"[step 1] load features: {PARQUET_TRAIN.name}")
    X, _y, index = load_parquet_with_blacklist(PARQUET_TRAIN, verbose=True)
    X = merge_regime_columns(X, PARQUET_REGIME)
    print(f"[step 1] X shape: {X.shape}")

    print(f"[step 2] load fired set: {FIRED_TRAIN.name}")
    fired = pd.read_parquet(FIRED_TRAIN)
    fired_ts = pd.to_datetime(fired["entry_id"])
    meta_y = pd.Series(fired["meta_label"].astype(float).values, index=fired_ts)
    meta_y = meta_y[~meta_y.index.duplicated()]
    print(f"[step 2] 発火バー {len(meta_y):,} | 素勝率 {100*meta_y.mean():.1f}%")

    print(f"[step 3] purged CV on 発火部分集合 n_splits={N_SPLITS} embargo K={LABEL_K_MAX}")
    # 発火バーは前段 OOF が存在する後半 fold の test 部分にのみ存在するため、
    # フル index でなく「発火部分集合の index」上で purged walk-forward CV を組む(leak 安全)。
    fired_index = pd.DatetimeIndex(sorted(meta_y.index))
    X_fired = X.loc[fired_index]
    y_fired = meta_y.loc[fired_index]
    cv = prepare_purged_cv(n_splits=N_SPLITS)
    fold_splits = list(split_with_purging(cv, X_fired, fired_index, K=LABEL_K_MAX))
    print(f"[step 3] folds: {len(fold_splits)}")

    oof_y, oof_p, oof_ts = [], [], []
    folds = fold_splits[:1] if args.smoke else fold_splits
    for fi, (tr_pos, te_pos) in enumerate(folds):
        if len(tr_pos) < 100 or len(te_pos) < 20:
            print(f"  fold{fi}: skip (train={len(tr_pos)} test={len(te_pos)})")
            continue
        n_va = max(1, int(len(tr_pos) * VALID_TAIL_FRACTION))
        tr2_pos, va_pos = tr_pos[:-n_va], tr_pos[-n_va:]
        Xtr, ytr = X_fired.iloc[tr2_pos], y_fired.iloc[tr2_pos]
        Xva, yva = X_fired.iloc[va_pos], y_fired.iloc[va_pos]
        Xte, yte = X_fired.iloc[te_pos], y_fired.iloc[te_pos]
        p_te, _m = train_binary(Xtr, ytr, Xva, yva, Xte)
        auc = roc_auc_score(yte.astype(int), p_te) if yte.nunique() > 1 else float("nan")
        print(f"  fold{fi}: train={len(tr2_pos):,} test={len(te_pos):,} | "
              f"test素勝率={100*yte.mean():.1f}% | AUC={auc:.3f}")
        oof_y.append(yte.values); oof_p.append(p_te); oof_ts.append(fired_index[te_pos].values)

    if not oof_y:
        print("[done] OOF なし"); return 1
    y_all = np.concatenate(oof_y); p_all = np.concatenate(oof_p)
    overall_auc = roc_auc_score(y_all.astype(int), p_all) if len(set(y_all.tolist())) > 1 else float("nan")
    lift = lift_report(y_all, p_all)
    summary = {
        "mode": "smoke" if args.smoke else "full",
        "n_oof": int(len(y_all)),
        "oof_auc": round(float(overall_auc), 4),
        "lift": lift,
        "elapsed_sec": round(time.time() - t0, 1),
    }
    pd.DataFrame({"ts": np.concatenate(oof_ts), "y": y_all, "p": p_all}).to_parquet(
        OUT_DIR / ("oof_smoke.parquet" if args.smoke else "oof_meta_secondary.parquet"))
    (OUT_DIR / ("summary_smoke.json" if args.smoke else "summary.json")).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2))
    print("=== summary ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
