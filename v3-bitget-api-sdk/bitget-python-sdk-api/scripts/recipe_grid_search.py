"""recipe_grid_search.py — レシピ型 grid search CLI（regime_research.md §10.6）

Usage:
    # 動作テスト（R01 単体・default グリッド・365日）
    python3 scripts/recipe_grid_search.py \
        --recipes configs/recipes.yaml \
        --recipe-id R01 \
        --ohlcv data/BTCUSDT-5m-2025-04-01_03-31_365d.csv \
        --labels data/regime_ground_truth_daily_human.csv \
        --grid-mode default

    # 全件本走査（5x5 grid・5y）
    python3 scripts/recipe_grid_search.py \
        --recipes configs/recipes.yaml \
        --ohlcv data/BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv \
        --labels data/regime_ground_truth_daily_human.csv \
        --grid-mode full
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cat.recipe.aggregator import expand_grid, predict_with_recipe
from cat.recipe.evaluator import daily_returns_from_5m, evaluate
from cat.recipe.indicators_multi_tf import (
    load_human_labels,
    load_ohlcv_5m,
    precompute_panels,
)
from cat.recipe.loader import load_recipes
from cat.recipe.reporter import (
    write_dashboard_predictions_json,
    write_scores_csv,
    write_top10_markdown,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--recipes", required=True, type=Path)
    p.add_argument("--recipe-id", default=None, help="単一レシピのみ実行（指定なしで全件）")
    p.add_argument("--ohlcv", required=True, type=Path)
    p.add_argument("--labels", required=True, type=Path)
    p.add_argument("--grid-mode", choices=["default", "full"], default="default")
    p.add_argument("--output-csv", default="results/recipe_scores.csv", type=Path)
    p.add_argument("--output-md", default="results/recipe_top10.md", type=Path)
    p.add_argument("--output-dashboard-json", default="dashboard/data/recipe_predictions.json", type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()

    print(f"[1/5] load recipes: {args.recipes}")
    recipes = load_recipes(args.recipes, filter_id=args.recipe_id)
    if not recipes:
        print(f"  no recipes loaded (filter_id={args.recipe_id})", file=sys.stderr)
        return 2
    print(f"  loaded {len(recipes)} recipe(s): {[r.id for r in recipes]}")

    print(f"[2/5] load OHLCV 5m: {args.ohlcv}")
    df_5m = load_ohlcv_5m(args.ohlcv)
    print(f"  rows={len(df_5m)} range={df_5m.index.min()} 〜 {df_5m.index.max()}")

    print(f"[3/5] load labels: {args.labels}")
    labels = load_human_labels(args.labels)
    print(f"  filled days={len(labels)}")

    print(f"[4/5] precompute panels (resample + indicators)")
    t0 = time.time()
    panels = precompute_panels(df_5m, recipes, labels_human=labels)
    print(f"  panels={list(panels.keys())} (took {time.time()-t0:.1f}s)")

    daily_ret = daily_returns_from_5m(df_5m)

    # 評価対象日: ラベル充足日
    eval_dates = pd.DatetimeIndex(pd.to_datetime(labels.index))

    print(f"[5/5] evaluate {len(recipes)} recipe(s) × grid-mode={args.grid_mode}")
    rows: list[dict] = []
    default_predicts: dict[str, pd.Series] = {}
    for recipe in recipes:
        combos = expand_grid(recipe, mode=args.grid_mode)
        for i, combo in enumerate(combos):
            pred = predict_with_recipe(recipe, panels, combo, eval_dates)
            metrics = evaluate(pred, labels, daily_ret)
            rows.append(
                {
                    "recipe_id": recipe.id,
                    "threshold_json": json.dumps(combo, ensure_ascii=False),
                    **metrics,
                }
            )
            if i == 0:
                default_predicts[recipe.id] = pred
        print(f"  {recipe.id}: {len(combos)} combos done")

    df = write_scores_csv(rows, args.output_csv)
    write_top10_markdown(df, recipes, args.output_md)
    print(f"=> {args.output_csv} ({len(df)} rows)")
    print(f"=> {args.output_md}")

    # ダッシュボード用 JSON（default 閾値 1 通りの日次予測）
    daily_close = df_5m["close"].resample("1D", label="right", closed="right").last().dropna()
    write_dashboard_predictions_json(
        default_predicts,
        recipes,
        df,
        labels,
        daily_close,
        args.output_dashboard_json,
    )
    print(f"=> {args.output_dashboard_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
