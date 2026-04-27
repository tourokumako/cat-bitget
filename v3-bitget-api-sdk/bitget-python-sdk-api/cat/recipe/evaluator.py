"""§10.2 評価指標を計算する。"""
from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

# 候補B 数値（regime_research.md §4・data 駆動）
DT_DAILY_RET_MAX = -0.82  # %
UT_DAILY_RET_MIN = +1.22  # %
RANGE_DAILY_RET_ABS_MAX = 0.34  # %
RUN_LEN_MIN = 3
RUN_LEN_MAX = 30


def _runs(labels: pd.Series) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    if labels.empty:
        return out
    cur = labels.iloc[0]
    n = 1
    for v in labels.iloc[1:]:
        if v == cur:
            n += 1
        else:
            out.append((cur, n))
            cur = v
            n = 1
    out.append((cur, n))
    return out


def evaluate(
    predict_daily: pd.Series,
    labels_human: pd.DataFrame,
    daily_returns: pd.Series,
) -> dict:
    """predict と human ラベルを突合し、§10.2 全指標を返す。

    predict_daily: index=DatetimeIndex (日次), values ∈ {downtrend, range, uptrend}
    labels_human:  DataFrame, index=date, columns=[label, note]
    daily_returns: Series, index=DatetimeIndex (日次), values=日次リターン(%)

    戻り値の nan の意味（バグではない）:
    - dt_mean_pct = nan → 予測に "downtrend" が一度も出ていない（評価期間に該当 regime が出現せず）
    - ut_mean_pct = nan → 同上 (uptrend)
    - range_abs_mean_pct = nan → 同上 (range)
    365日ラベルでは月支配 DT 月が出ない構造的限界がある（regime_research.md §10.2 注意書き参照）。
    本走査（1826日）で再評価する必要あり。
    """
    pred = predict_daily.copy()
    pred.index = pd.to_datetime(pred.index).normalize()

    truth_idx = pd.to_datetime(labels_human.index)
    truth = pd.Series(labels_human["label"].values, index=truth_idx).reindex(pred.index)

    aligned = pd.DataFrame({"pred": pred, "truth": truth}).dropna()
    coverage_days = len(aligned)
    daily_acc = (aligned["pred"] == aligned["truth"]).mean() if coverage_days else float("nan")

    # 月単位支配
    monthly_pred = pred.groupby(pred.index.to_period("M")).agg(lambda s: Counter(s).most_common(1)[0][0])
    monthly_truth = pd.Series(labels_human["label"].values, index=truth_idx)
    monthly_truth = monthly_truth.groupby(monthly_truth.index.to_period("M")).agg(
        lambda s: Counter(s).most_common(1)[0][0]
    )
    common_months = monthly_pred.index.intersection(monthly_truth.index)
    monthly_acc = (
        (monthly_pred.loc[common_months] == monthly_truth.loc[common_months]).mean()
        if len(common_months)
        else float("nan")
    )
    coverage_months = len(common_months)

    # レジーム別 日次リターン
    ret = daily_returns.copy()
    ret.index = pd.to_datetime(ret.index).normalize()
    joined = pd.DataFrame({"pred": pred, "ret": ret}).dropna()
    by_reg = joined.groupby("pred")["ret"]
    dt_mean = by_reg.mean().get("downtrend", float("nan"))
    ut_mean = by_reg.mean().get("uptrend", float("nan"))
    range_abs_mean = abs(by_reg.mean().get("range", float("nan"))) if "range" in by_reg.groups else float("nan")

    candidate_b_pass = (
        (not np.isnan(dt_mean) and dt_mean < DT_DAILY_RET_MAX)
        and (not np.isnan(ut_mean) and ut_mean > UT_DAILY_RET_MIN)
        and (not np.isnan(range_abs_mean) and range_abs_mean < RANGE_DAILY_RET_ABS_MAX)
    )

    # 状態継続
    runs = _runs(pred.dropna())
    run_lens = [n for _, n in runs]
    run_median = float(np.median(run_lens)) if run_lens else float("nan")
    mode_run_len = Counter(run_lens).most_common(1)[0][0] if run_lens else None
    sticky_5d = mode_run_len == 5

    return {
        "daily_acc": daily_acc,
        "monthly_acc": monthly_acc,
        "coverage_days": coverage_days,
        "coverage_months": coverage_months,
        "dt_mean_pct": dt_mean,
        "ut_mean_pct": ut_mean,
        "range_abs_mean_pct": range_abs_mean,
        "candidate_b_pass": candidate_b_pass,
        "run_median_days": run_median,
        "mode_run_len": mode_run_len,
        "sticky_5d": sticky_5d,
    }


def daily_returns_from_5m(df_5m: pd.DataFrame) -> pd.Series:
    """5m OHLCV → 日次リターン(%)。日足 close→close。"""
    daily_close = df_5m["close"].resample("1D", label="right", closed="right").last().dropna()
    return daily_close.pct_change() * 100
