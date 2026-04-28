"""recipe_scores.csv と recipe_top10.md を出力。"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd

from .loader import Recipe


def write_scores_csv(rows: list[dict], path: Path | str) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df


def write_dashboard_predictions_json(
    predictions_by_recipe: dict[str, pd.Series],
    recipes: list[Recipe],
    scores_df: pd.DataFrame,
    labels_human: pd.DataFrame,
    daily_close: pd.Series,
    path: Path | str,
) -> None:
    """ダッシュボード ⑩タブ用に日次予測 + 肉眼ラベル + close を出力。

    出力構造:
    {
      "n_days": 1826,
      "recipes": [{"id": "R01", "label": "...", "monthly_acc": 0.22, "daily_acc": 0.33, ...}, ...],
      "days": [{"date": "2021-04-01", "close": ..., "true": "uptrend",
                "predicts": {"R01": "uptrend", ...},
                "matches": {"R01": true, ...}}, ...]
    }
    """
    recipes_by_id = {r.id: r for r in recipes}

    truth = pd.Series(labels_human["label"].values, index=pd.to_datetime(labels_human.index))
    truth.index = truth.index.normalize()
    close = daily_close.copy()
    close.index = pd.to_datetime(close.index).normalize()

    all_dates = sorted(set(truth.index).union(*[p.index for p in predictions_by_recipe.values()]))

    days_out = []
    for ts in all_dates:
        d_str = ts.strftime("%Y-%m-%d")
        true_lab = truth.get(ts, None)
        c = close.get(ts, None)
        predicts = {}
        matches = {}
        for rid, pred in predictions_by_recipe.items():
            p = pred.get(ts, None)
            if p is not None and not (isinstance(p, float) and pd.isna(p)):
                predicts[rid] = str(p)
                if true_lab is not None:
                    matches[rid] = bool(p == true_lab)
                else:
                    matches[rid] = None
        days_out.append({
            "date": d_str,
            "close": float(c) if c is not None and not pd.isna(c) else None,
            "true": str(true_lab) if true_lab is not None and not (isinstance(true_lab, float) and pd.isna(true_lab)) else None,
            "predicts": predicts,
            "matches": matches,
        })

    recipes_meta = []
    score_by_id = {row["recipe_id"]: row for _, row in scores_df.iterrows()}
    for r in recipes:
        s = score_by_id.get(r.id, {})
        recipes_meta.append({
            "id": r.id,
            "label": r.label,
            "timeframes": r.timeframes,
            "indicators": [{"tf": ind.tf, "name": ind.name, "period": ind.period} for ind in r.indicators],
            "aggregation_intra": r.aggregation_intra,
            "aggregation_cross": r.aggregation_cross,
            "daily_acc": float(s.get("daily_acc")) if s.get("daily_acc") is not None and not pd.isna(s.get("daily_acc")) else None,
            "monthly_acc": float(s.get("monthly_acc")) if s.get("monthly_acc") is not None and not pd.isna(s.get("monthly_acc")) else None,
            "candidate_b_pass": bool(s.get("candidate_b_pass", False)),
            "mode_run_len": int(s.get("mode_run_len")) if s.get("mode_run_len") is not None and not pd.isna(s.get("mode_run_len")) else None,
        })

    out = {
        "n_days": len(days_out),
        "period": {"start": days_out[0]["date"], "end": days_out[-1]["date"]} if days_out else None,
        "recipes": recipes_meta,
        "days": days_out,
    }

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(out, f, ensure_ascii=False)


def _format_combo(combo: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in combo.items())


def _component_histogram(recipes_by_id: dict[str, Recipe], top_ids: list[str]) -> dict[str, list[tuple[str, int]]]:
    tf_counter: Counter = Counter()
    ind_counter: Counter = Counter()
    intra_counter: Counter = Counter()
    cross_counter: Counter = Counter()
    for rid in top_ids:
        r = recipes_by_id.get(rid)
        if r is None:
            continue
        for tf in r.timeframes:
            tf_counter[tf] += 1
        for ind in r.indicators:
            ind_counter[ind.name] += 1
        intra_counter[r.aggregation_intra] += 1
        cross_counter[str(r.aggregation_cross)] += 1
    return {
        "timeframes": tf_counter.most_common(),
        "indicators": ind_counter.most_common(),
        "aggregation_intra": intra_counter.most_common(),
        "aggregation_cross": cross_counter.most_common(),
    }


def write_top10_markdown(
    df: pd.DataFrame,
    recipes: list[Recipe],
    path: Path | str,
    delta_net_col: str | None = None,
) -> None:
    """月単位支配 desc → 日次 desc → ΔNET desc でソートして上位10件を MD 出力。"""
    if df.empty:
        Path(path).write_text("(no scores)")
        return

    recipes_by_id = {r.id: r for r in recipes}
    sort_cols = ["monthly_acc", "daily_acc"]
    ascending = [False, False]
    if delta_net_col and delta_net_col in df.columns:
        sort_cols.append(delta_net_col)
        ascending.append(False)
    ranked = df.sort_values(sort_cols, ascending=ascending).head(10).reset_index(drop=True)

    lines: list[str] = []
    lines.append("# レシピ型 grid search トップ10サマリ")
    lines.append("")
    lines.append(f"対象スコア件数: {len(df)} / 表示: 上位10")
    lines.append("")

    for i, row in ranked.iterrows():
        rid = row["recipe_id"]
        recipe = recipes_by_id.get(rid)
        label = recipe.label if recipe else ""
        delta_str = ""
        if delta_net_col and delta_net_col in row:
            delta_str = f" / ΔNET={row[delta_net_col]:+.2f}"

        lines.append(
            f"## #{i+1} {rid} {label}  "
            f"[monthly={row['monthly_acc']:.2f} / daily={row['daily_acc']:.2f}{delta_str}]"
        )
        if recipe:
            tf_str = ", ".join(recipe.timeframes)
            ind_str = " / ".join(f"{ind.tf}={ind.name}" + (f"({ind.period})" if ind.period else "") for ind in recipe.indicators)
            lines.append(f"- TF: {tf_str} / IND: {ind_str}")
            lines.append(f"- AGG: intra={recipe.aggregation_intra} / cross={recipe.aggregation_cross}")
        lines.append(f"- 閾値: {_format_combo(json.loads(row['threshold_json']))}")
        lines.append(
            f"- 月単位支配: {row['monthly_acc']:.2%} ({int(row['coverage_months'])}月) "
            f"/ 日次: {row['daily_acc']:.2%} ({int(row['coverage_days'])}日)"
        )
        cb = "✅" if row["candidate_b_pass"] else "❌"
        lines.append(
            f"- 候補B: {cb} DT={row['dt_mean_pct']:+.2f}% / UT={row['ut_mean_pct']:+.2f}% / RANGE=±{row['range_abs_mean_pct']:.2f}%"
        )
        sticky = "あり ⚠" if row["sticky_5d"] else "なし"
        lines.append(
            f"- 状態継続中央値: {row['run_median_days']:.1f}日 / 5日刻み張り付き: {sticky}"
        )
        lines.append("")

    # ベースライン参考（R01 があれば）
    base = df[df["recipe_id"] == "R01"]
    if not base.empty:
        b = base.iloc[0]
        lines.append("---")
        lines.append("## ベースライン (R01)")
        lines.append(
            f"- monthly={b['monthly_acc']:.2f} / daily={b['daily_acc']:.2f} / "
            f"DT={b['dt_mean_pct']:+.2f}% UT={b['ut_mean_pct']:+.2f}% RANGE=±{b['range_abs_mean_pct']:.2f}%"
        )
        lines.append("")

    # 共通構成要素ヒストグラム
    hist = _component_histogram(recipes_by_id, ranked["recipe_id"].tolist())
    lines.append("---")
    lines.append("## 上位10で共通する構成要素（ヒストグラム）")
    for k, items in hist.items():
        lines.append(f"- **{k}**: " + ", ".join(f"{n}({c})" for n, c in items))
    lines.append("")

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines))
