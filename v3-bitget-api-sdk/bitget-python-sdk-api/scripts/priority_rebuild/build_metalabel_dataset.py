"""build_metalabel_dataset.py — メタラベリング学習データセット構築（工程[2] 縦化・第一手）

2026-05-31 execlog 0章「合意した修正方針」step 1 の最初の一手。

狙い:
  業界標準のメタラベリング = 前段(primary・方向)→後段(secondary meta・採用ゲート+sizing)の二段カスケード。
  その肝は「前段が発火(買い/売り予測)したバーだけで後段を学習する」こと。
  本スクリプトはその前段階として「前段が発火したバーを抽出し、後段の正解(meta_label)を付けた
  データセット」を作る。meta モデルの学習はまだ行わない(まず発火の質を見る)。

前段 primary の定義(暫定・smoke で調整):
  - 各バーで方向当て(Triple Barrier 3クラス)の「利確確率 P(TP)」を LONG/SHORT それぞれ取る。
    クラス対応: encode_tb_label = y+1 (SL=-1→0 / TIME=0→1 / TP=1→2) → pred_proba_class2_cal = P(TP)。
  - LONG_score = P_LONG(TP), SHORT_score = P_SHORT(TP)。calibrated 値を使用。
  - 発火: score_max = max(LONG_score, SHORT_score) > θ。方向 = argmax(排他)。両方低ければ見送り。
  - θ は recall 重視で緩め。smoke で発火率/勝率の感度表を見てから確定(L-238 設計値は仮定・実装後 data-driven)。
  - K は暫定 K=12(1時間相当)単独。集約は smoke 後に検討。

データ範囲(leak 防止):
  - train(2021-2024) primary = baseline の out-of-fold 予測(ml_phase2_baseline/*_fold{0,1,2})
  - test(2025 / 2026Q1) primary = production の test 予測(ml_phase2_production)
  後段 meta の教師信号 = labels_mfe_mae_pct_*.parquet の meta_label_{side}_K{K}(既存)。

出力: results/priority_rebuild/metalabel_dataset/metalabel_{period}.parquet
  列 = [entry_id, primary_side, LONG_score, SHORT_score, score_max, meta_label]
  ※ features は付けない(meta モデル学習時に join)。本段階は発火の質確認のみ。

使い方:
  python build_metalabel_dataset.py --smoke           # train の感度表のみ表示(書き出さない)
  python build_metalabel_dataset.py --theta 0.50      # 全期間を θ=0.50 で書き出し
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SDK = Path(__file__).resolve().parents[2]            # bitget-python-sdk-api
RES = SDK / "results" / "priority_rebuild"
BASELINE = RES / "ml_phase2_baseline"
PRODUCTION = RES / "ml_phase2_production"
OUT = RES / "metalabel_dataset"

LABELS = {
    "train_2021_2024": RES / "labels_mfe_mae_pct_train_2021_2024.parquet",
    "test_2025": RES / "labels_mfe_mae_pct_test_2025.parquet",
    "test_2026_q1": RES / "labels_mfe_mae_pct_test_2026_q1.parquet",
}
PRODUCTION_PERIOD_FILE = {
    "test_2025": "predictions_test_2025.parquet",
    "test_2026_q1": "predictions_test_2026_q1.parquet",
}

TP_CLASS_COL = "pred_proba_class2_cal"               # class2 = TP (encode_tb_label: y+1)
SIDES = ("LONG", "SHORT")
THETA_GRID = [0.30, 0.35, 0.40, 0.45, 0.50]
K_ALL = [6, 12, 24, 48, 96, 144, 288]                # primary 方向集約に使える全ホライズン
META_K = 12                                          # 取引成立の勝ち負け(meta_label)の保有ホライズン


def _merge_sides(long_df: pd.DataFrame, short_df: pd.DataFrame) -> pd.DataFrame:
    """LONG/SHORT score を entry_id で inner join。"""
    m = long_df.merge(short_df, on="entry_id", how="inner")
    return m


def _agg_side_train(side: str, kset: list[int]) -> pd.DataFrame:
    """1 side: 各 K の P(TP)(out-of-fold 3 fold concat)を entry_id で揃え K 平均 → {side}_score。"""
    per_k = []
    for K in kset:
        parts = [pd.read_parquet(
            BASELINE / f"triple_barrier_label_{side}_K{K}_fold{f}" / "predictions.parquet",
            columns=["entry_id", TP_CLASS_COL]) for f in (0, 1, 2)]
        d = pd.concat(parts, ignore_index=True).rename(columns={TP_CLASS_COL: f"s{K}"})
        per_k.append(d)
    m = per_k[0]
    for d in per_k[1:]:
        m = m.merge(d, on="entry_id", how="inner")    # 全 K に予測がある bar のみ
    m[f"{side}_score"] = m[[f"s{K}" for K in kset]].mean(axis=1)
    return m[["entry_id", f"{side}_score"]]


def _agg_side_test(side: str, kset: list[int], period: str) -> pd.DataFrame:
    fname = PRODUCTION_PERIOD_FILE[period]
    per_k = []
    for K in kset:
        d = pd.read_parquet(PRODUCTION / f"triple_barrier_label_{side}_K{K}" / fname,
                            columns=["entry_id", TP_CLASS_COL]).rename(columns={TP_CLASS_COL: f"s{K}"})
        per_k.append(d)
    m = per_k[0]
    for d in per_k[1:]:
        m = m.merge(d, on="entry_id", how="inner")
    m[f"{side}_score"] = m[[f"s{K}" for K in kset]].mean(axis=1)
    return m[["entry_id", f"{side}_score"]]


def load_primary_train(kset: list[int]) -> pd.DataFrame:
    """baseline out-of-fold の前段 score(K 平均)を LONG/SHORT 結合して返す。"""
    return _merge_sides(_agg_side_train("LONG", kset), _agg_side_train("SHORT", kset))


def load_primary_test(kset: list[int], period: str) -> pd.DataFrame:
    return _merge_sides(_agg_side_test("LONG", kset, period), _agg_side_test("SHORT", kset, period))


def attach_primary_side_and_meta(df: pd.DataFrame, K: int, period: str) -> pd.DataFrame:
    """primary_side / score_max / 発火方向の meta_label(保有ホライズン K)を付与。"""
    lab = pd.read_parquet(LABELS[period], columns=[f"meta_label_LONG_K{K}", f"meta_label_SHORT_K{K}"])
    lab.index = pd.to_datetime(lab.index)            # timestamp index

    out = df.copy()
    out["primary_side"] = np.where(out["LONG_score"] >= out["SHORT_score"], "LONG", "SHORT")
    out["score_max"] = out[["LONG_score", "SHORT_score"]].max(axis=1)

    ts = pd.to_datetime(out["entry_id"])
    ml_long = ts.map(lab[f"meta_label_LONG_K{K}"])
    ml_short = ts.map(lab[f"meta_label_SHORT_K{K}"])
    out["meta_label"] = np.where(out["primary_side"].values == "LONG",
                                 ml_long.values, ml_short.values)
    return out


def fire_sensitivity_table(df: pd.DataFrame) -> pd.DataFrame:
    """θ 候補ごとの 発火件数 / 発火率 / LONG:SHORT / 発火した賭けの実勝率。"""
    rows = []
    n_all = len(df)
    for th in THETA_GRID:
        fired = df[df["score_max"] > th]
        valid = fired[fired["meta_label"].notna()]
        n = len(valid)
        nlong = int((valid["primary_side"] == "LONG").sum())
        nshort = n - nlong
        win = float(valid["meta_label"].mean()) if n else float("nan")
        rows.append({
            "theta": th,
            "fired": n,
            "fire_rate_%": round(100 * n / n_all, 1) if n_all else 0.0,
            "LONG": nlong,
            "SHORT": nshort,
            "win_rate_%": round(100 * win, 1) if n else None,
        })
    return pd.DataFrame(rows)


def base_win_rates(df: pd.DataFrame) -> str:
    """発火フィルタなしの素の勝率(比較用ベースライン)。"""
    lw = df[df["primary_side"] == "LONG"]["meta_label"].mean()
    sw = df[df["primary_side"] == "SHORT"]["meta_label"].mean()
    return f"全バー素勝率: LONG={100*lw:.1f}% / SHORT={100*sw:.1f}% (発火フィルタ前・比較用)"


def run_smoke(kset: list[int], meta_k: int) -> None:
    print(f"=== smoke: train(out-of-fold) primary集約K={kset} / meta保有K={meta_k} ===")
    tr = load_primary_train(kset)
    tr = attach_primary_side_and_meta(tr, meta_k, "train_2021_2024")
    print(f"  primary 評価対象バー数: {len(tr):,} (meta_label 有: {tr['meta_label'].notna().sum():,})")
    print(f"  {base_win_rates(tr)}")
    print("  --- θ 感度表(発火した賭けの実勝率が、素勝率より上がるか) ---")
    print(fire_sensitivity_table(tr).to_string(index=False))


def run_full(kset: list[int], meta_k: int, theta: float) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"=== full: primary集約K={kset} / meta保有K={meta_k} / θ={theta} → {OUT} ===")
    cols = ["entry_id", "primary_side", "LONG_score", "SHORT_score", "score_max", "meta_label"]
    loaders = {
        "train_2021_2024": lambda: load_primary_train(kset),
        "test_2025": lambda: load_primary_test(kset, "test_2025"),
        "test_2026_q1": lambda: load_primary_test(kset, "test_2026_q1"),
    }
    for period, loader in loaders.items():
        df = attach_primary_side_and_meta(loader(), meta_k, period)
        fired = df[(df["score_max"] > theta) & (df["meta_label"].notna())][cols].reset_index(drop=True)
        path = OUT / f"metalabel_{period}.parquet"
        fired.to_parquet(path)
        win = float(fired["meta_label"].mean()) if len(fired) else float("nan")
        nlong = int((fired["primary_side"] == "LONG").sum())
        print(f"  {period}: 発火 {len(fired):,} 件 (LONG {nlong:,} / SHORT {len(fired)-nlong:,}) "
              f"実勝率 {100*win:.1f}% → {path.name}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="train の感度表のみ表示(書き出さない)")
    ap.add_argument("--theta", type=float, default=0.40, help="発火閾値(full モード)")
    ap.add_argument("--kset", type=str, default=",".join(map(str, K_ALL)),
                    help="primary 方向集約に使う K (カンマ区切り)")
    ap.add_argument("--meta-k", type=int, default=META_K, help="meta_label の保有ホライズン K")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    kset = [int(x) for x in args.kset.split(",")]
    if args.smoke:
        run_smoke(kset, args.meta_k)
    else:
        run_full(kset, args.meta_k, args.theta)


if __name__ == "__main__":
    main()
