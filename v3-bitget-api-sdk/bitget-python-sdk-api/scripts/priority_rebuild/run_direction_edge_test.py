"""run_direction_edge_test.py — 方向エッジ存在検証(やり直しの一手目・2026-05-31)

まこさん指示「最初からやりなおせ・方向エッジがあるか最初にチェックしろ」。
過去フロー全滅もTB再発も「方向を諦めてボラ予測に逃げる」が原因。
ならば最初に問うべきは: **テクニカル特徴量で5分足の方向に予測エッジが存在するのか?**

検証:
  - 純粋な方向ラベル y = 1 if close[t+K] > close[t] else 0 (= K本後に上がったか)
  - 全特徴量(2,604・blacklist除外) + regime 8列
  - leak安全 purged walk-forward CV(embargo K_max=288)の OOF で 方向AUC / 方向accuracy
  - ベースライン = 「常に多数派」prior と比較
  - 短期/中期/長期 K=12(1h)/96(8h)/288(24h)

判定:
  - AUC ≈ 0.50 → テクニカルで方向は取れない(設計の大前提を変える)
  - AUC ≳ 0.55 → 方向エッジは在る → 今のパイプライン(ボラ逃げ)が潰していた
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, accuracy_score

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
)

K_LIST = [12, 96, 288]
N_SPLITS = 5
VALID_TAIL = 0.10
OUT = REPO_ROOT / "results" / "priority_rebuild" / "direction_edge_test"


def build_direction_label(parquet: Path, K: int) -> pd.Series:
    close = pd.read_parquet(parquet, columns=["close"])["close"].sort_index()
    fwd = close.shift(-K)
    y = (fwd > close).astype("float")
    y[fwd.isna()] = np.nan  # 末尾 K bars
    return y


def train_oof_auc(X, index, y, K) -> dict:
    cv = prepare_purged_cv(n_splits=N_SPLITS)
    folds = list(split_with_purging(cv, X, index, K=288))
    oof_y, oof_p = [], []
    for tr_pos, te_pos in folds:
        # 方向ラベル NaN(末尾) を除外
        tr = tr_pos[~np.isnan(y.values[tr_pos])]
        te = te_pos[~np.isnan(y.values[te_pos])]
        if len(tr) < 500 or len(te) < 100:
            continue
        n_va = max(1, int(len(tr) * VALID_TAIL))
        tr2, va = tr[:-n_va], tr[-n_va:]
        ytr = y.values[tr2].astype(int)
        params = {**LGB_DEFAULT_PARAMS_BASE, "objective": "binary", "metric": "auc"}
        model = lgb.LGBMClassifier(**params)
        model.fit(X.iloc[tr2], ytr,
                  eval_set=[(X.iloc[va], y.values[va].astype(int))], eval_metric="auc",
                  callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)])
        p = model.predict_proba(X.iloc[te])[:, 1]
        oof_y.append(y.values[te].astype(int)); oof_p.append(p)
    yy = np.concatenate(oof_y); pp = np.concatenate(oof_p)
    auc = roc_auc_score(yy, pp)
    acc = accuracy_score(yy, (pp > 0.5).astype(int))
    up_rate = float(yy.mean())
    base_acc = max(up_rate, 1 - up_rate)  # 常に多数派
    return {"K": K, "n_oof": int(len(yy)), "up_rate_%": round(100 * up_rate, 2),
            "direction_AUC": round(float(auc), 4),
            "direction_acc_%": round(100 * acc, 2),
            "majority_baseline_acc_%": round(100 * base_acc, 2),
            "acc_lift_pt": round(100 * (acc - base_acc), 2)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    print(f"[load] {PARQUET_TRAIN.name}")
    X, _y, index = load_parquet_with_blacklist(PARQUET_TRAIN, verbose=True)
    X = merge_regime_columns(X, PARQUET_REGIME)
    print(f"[load] X: {X.shape}")
    results = []
    for K in K_LIST:
        print(f"\n[K={K}] 方向ラベル生成 + OOF 学習")
        y = build_direction_label(PARQUET_TRAIN, K)
        r = train_oof_auc(X, index, y, K)
        results.append(r)
        print(f"  → AUC={r['direction_AUC']} acc={r['direction_acc_%']}% "
              f"(多数派{r['majority_baseline_acc_%']}% / lift {r['acc_lift_pt']}pt) up率={r['up_rate_%']}%")
    summary = {"results": results, "elapsed_sec": round(time.time() - t0, 1)}
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n=== 方向エッジ検証 summary ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n判定目安: AUC≈0.50→テクニカルで方向取れない / AUC≳0.55→エッジ在り(パイプラインが潰してた)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
