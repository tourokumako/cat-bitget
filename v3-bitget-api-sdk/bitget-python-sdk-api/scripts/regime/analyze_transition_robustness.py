"""analyze_transition_robustness.py — 切替点5発見のロバストネス検証

メイン分析（analyze_transition_indicators.py）で抽出した 5発見について、
中央値の罠を潰すために以下を出す:
  a. Q1/Q3 範囲の併記（per-event 値分布の幅）
  b. 「典型形」一致イベント割合（pattern別の各発見の成立率）
  c. 極値サンプル top3（datetime + 実値）

対象 5発見:
  ① up→dn / dn→up: macd_hist__1h（ピーク/底打ち型）
  ② up→dn / dn→up: close_vs_ema20_pct__1h
  ③ dn→up: close_below_cloud__5m（雲下抜けダマシ）
  ④ 短命 vs 通常 up→dn: macd_hist__1h（急峻スパイク vs 漸進過熱）
  ⑤ dn→up: macd_hist_change__1h（先行サイン）

出力: results/regime_label_analysis/transition_indicator_robustness.md
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import pandas as pd
import numpy as np

from analyze_regime_label_features import (
    build_indicators_extended,
    attach_indicators,
)
from analyze_vshape_indicators import resample_ohlcv
from analyze_transition_indicators import (
    load_labels,
    run_length_encode,
    extract_transitions,
    attach_all_indicators,
    WINDOW_BARS,
)

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
OUT_DIR = BASE / "results/regime_label_analysis"
OUT_MD = OUT_DIR / "transition_indicator_robustness.md"


def per_event_with_meta(labels_df, transitions, indicator_cols):
    """切替点ごとに pre/t0/post + datetime メタを返す。"""
    rows = []
    for ev in transitions:
        t = ev["t_idx"]
        pre_lo = max(ev["prev_start"], t - WINDOW_BARS)
        post_hi = min(ev["cur_end"] + 1, t + WINDOW_BARS)
        if pre_lo >= t or t >= post_hi:
            continue
        pre_block = labels_df.iloc[pre_lo:t]
        post_block = labels_df.iloc[t:post_hi]
        t_ts = labels_df.iloc[t]["timestamp_utc"]
        for col in indicator_cols:
            rows.append({
                "pattern": f"{ev['prev']}->{ev['cur']}",
                "subset": ev["subset"],
                "indicator": col,
                "t_datetime": t_ts,
                "pre_median": pre_block[col].median(skipna=True),
                "t0_value": labels_df.iloc[t][col],
                "post_median": post_block[col].median(skipna=True),
                "prev_len": ev["prev_len"],
                "cur_len": ev["cur_len"],
            })
    return pd.DataFrame(rows)


def cohort_with_quantiles(per_event_df, pattern, indicator, subset=None):
    sub = per_event_df[(per_event_df["pattern"] == pattern) & (per_event_df["indicator"] == indicator)]
    if subset is not None:
        sub = sub[sub["subset"] == subset]
    n = len(sub)
    if n == 0:
        return None
    return {
        "n": n,
        "pre_q1": sub["pre_median"].quantile(0.25),
        "pre_med": sub["pre_median"].median(),
        "pre_q3": sub["pre_median"].quantile(0.75),
        "t0_q1": sub["t0_value"].quantile(0.25),
        "t0_med": sub["t0_value"].median(),
        "t0_q3": sub["t0_value"].quantile(0.75),
        "post_q1": sub["post_median"].quantile(0.25),
        "post_med": sub["post_median"].median(),
        "post_q3": sub["post_median"].quantile(0.75),
        "raw": sub,
    }


def fmt(x):
    if pd.isna(x):
        return "—"
    if abs(x) >= 100:
        return f"{x:.1f}"
    if abs(x) >= 10:
        return f"{x:.2f}"
    return f"{x:.3f}"


def fmt_block(stats):
    return (
        f"pre **{fmt(stats['pre_med'])}** [Q1={fmt(stats['pre_q1'])}, Q3={fmt(stats['pre_q3'])}] / "
        f"t0 **{fmt(stats['t0_med'])}** [Q1={fmt(stats['t0_q1'])}, Q3={fmt(stats['t0_q3'])}] / "
        f"post **{fmt(stats['post_med'])}** [Q1={fmt(stats['post_q1'])}, Q3={fmt(stats['post_q3'])}]"
    )


def typical_match_rate(raw, predicate, label):
    """raw（per-event 行）に predicate を適用、True 件数と割合を返す。"""
    n = len(raw)
    if n == 0:
        return f"{label}: n=0"
    hits = raw.apply(predicate, axis=1).sum()
    return f"{label}: **{hits}/{n} ({hits / n * 100:.0f}%)**"


def top_extremes(raw, key, k=3, asc=False):
    """raw を key で sort して top k の代表サンプルを返す。"""
    if raw.empty:
        return []
    s = raw.sort_values(key, ascending=asc).head(k)
    return [
        {
            "datetime": r["t_datetime"],
            "pre": r["pre_median"],
            "t0": r["t0_value"],
            "post": r["post_median"],
        }
        for _, r in s.iterrows()
    ]


def fmt_extremes(samples):
    if not samples:
        return "(該当なし)"
    lines = []
    for s in samples:
        ts = s["datetime"]
        if isinstance(ts, pd.Timestamp):
            ts = ts.strftime("%Y-%m-%d %H:%M")
        lines.append(f"  - {ts}: pre={fmt(s['pre'])} / t0={fmt(s['t0'])} / post={fmt(s['post'])}")
    return "\n".join(lines)


def main():
    print("ラベル + 切替点抽出...")
    labels = load_labels()
    runs = run_length_encode(labels["label_norm"].tolist())
    transitions = extract_transitions(runs)
    print(f"  切替点数: {len(transitions)}")

    print("OHLCV resample + 指標計算...")
    df5m = pd.read_csv(DATA_5M, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    df1h = resample_ohlcv(df5m, "1h")
    df4h = resample_ohlcv(df5m, "4h")
    df1d = resample_ohlcv(df5m, "1D")
    feat5m = build_indicators_extended(df5m)
    feat1h = build_indicators_extended(df1h)
    feat4h = build_indicators_extended(df4h)
    feat1d = build_indicators_extended(df1d)

    print("attach...")
    labels_attached = attach_all_indicators(labels, feat5m, feat1h, feat4h, feat1d)

    target_cols = [
        "macd_hist__1h",
        "close_vs_ema20_pct__1h",
        "close_below_cloud__5m",
        "macd_hist_change__1h",
    ]
    print("per-event 集計（5発見の対象指標のみ）...")
    per_event = per_event_with_meta(labels_attached, transitions, target_cols)
    print(f"  per-event 行数: {len(per_event)}")

    lines = []
    lines.append("# 切替点 5発見のロバストネス検証")
    lines.append("")
    lines.append("メイン分析（transition_indicator_main.md）の中央値が「中央値の罠」を踏んでいないか検証する。")
    lines.append("")
    lines.append("各発見ごとに以下を出す:")
    lines.append("- **a. Q1/Q3 併記**: pre / t0 / post の四分位範囲")
    lines.append("- **b. 典型形一致率**: 発見の語った形に合致する切替点の件数/全数")
    lines.append("- **c. 極値サンプル top3**: t0 値の絶対値が大きい代表 3件の datetime + 実値")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === ① macd_hist__1h up→dn / dn→up ===
    lines.append("## ① macd_hist (1h) — up→dn / dn→up のピーク/底打ち")
    lines.append("")
    lines.append("**典型形の定義**:")
    lines.append("- up→dn: t0 ≥ pre **かつ** post < t0 (= 切替点で頂点 → 反落)")
    lines.append("- dn→up: t0 ≤ pre **かつ** post > t0 (= 切替点で底 → 反発)")
    lines.append("")

    for pattern, direction in [("up->dn", "peak"), ("dn->up", "bottom")]:
        s = cohort_with_quantiles(per_event, pattern, "macd_hist__1h")
        if s is None:
            continue
        lines.append(f"### {pattern}  (n={s['n']})")
        lines.append("")
        lines.append(f"- **a. Q1/Q3**: {fmt_block(s)}")
        if direction == "peak":
            pred = lambda r: pd.notna(r["pre_median"]) and pd.notna(r["t0_value"]) and pd.notna(r["post_median"]) and r["t0_value"] >= r["pre_median"] and r["post_median"] < r["t0_value"]
        else:
            pred = lambda r: pd.notna(r["pre_median"]) and pd.notna(r["t0_value"]) and pd.notna(r["post_median"]) and r["t0_value"] <= r["pre_median"] and r["post_median"] > r["t0_value"]
        lines.append(f"- **b. 典型形一致**: " + typical_match_rate(s["raw"], pred, "ピーク/底打ち型"))
        # 補助: 単純な符号反転（post と pre の符号が異なる）
        sign_pred = lambda r: pd.notna(r["pre_median"]) and pd.notna(r["post_median"]) and (np.sign(r["pre_median"]) != np.sign(r["post_median"]))
        lines.append(f"- 参考: 符号反転（pre と post が反対符号）: " + typical_match_rate(s["raw"], sign_pred, "符号反転"))
        # c. extremes
        ext = top_extremes(s["raw"], "t0_value", k=3, asc=(direction == "bottom"))
        lines.append(f"- **c. 極値サンプル top3** (t0 の{'最大' if direction == 'peak' else '最小'}3件):")
        lines.append(fmt_extremes(ext))
        lines.append("")

    lines.append("---")
    lines.append("")

    # === ② close_vs_ema20_pct__1h up→dn / dn→up ===
    lines.append("## ② close_vs_ema20_pct (1h) — 切替点で乖離ピーク")
    lines.append("")
    lines.append("**典型形の定義**:")
    lines.append("- up→dn: t0 > pre かつ post < t0 (乖離が拡大 → 縮小)")
    lines.append("- dn→up: t0 < pre かつ post > t0 (負乖離が拡大 → 縮小)")
    lines.append("")

    for pattern, direction in [("up->dn", "peak"), ("dn->up", "bottom")]:
        s = cohort_with_quantiles(per_event, pattern, "close_vs_ema20_pct__1h")
        if s is None:
            continue
        lines.append(f"### {pattern}  (n={s['n']})")
        lines.append("")
        lines.append(f"- **a. Q1/Q3**: {fmt_block(s)}")
        if direction == "peak":
            pred = lambda r: pd.notna(r["pre_median"]) and pd.notna(r["t0_value"]) and pd.notna(r["post_median"]) and r["t0_value"] > r["pre_median"] and r["post_median"] < r["t0_value"]
        else:
            pred = lambda r: pd.notna(r["pre_median"]) and pd.notna(r["t0_value"]) and pd.notna(r["post_median"]) and r["t0_value"] < r["pre_median"] and r["post_median"] > r["t0_value"]
        lines.append(f"- **b. 典型形一致**: " + typical_match_rate(s["raw"], pred, "乖離ピーク型"))
        ext = top_extremes(s["raw"], "t0_value", k=3, asc=(direction == "bottom"))
        lines.append(f"- **c. 極値サンプル top3**:")
        lines.append(fmt_extremes(ext))
        lines.append("")

    lines.append("---")
    lines.append("")

    # === ③ close_below_cloud__5m dn→up ===
    lines.append("## ③ close_below_cloud (5m) — dn→up の雲下抜けダマシ")
    lines.append("")
    lines.append("**典型形の定義**: t0=1.0 (切替点で雲下) かつ post=0.0 (24h 後は雲外)")
    lines.append("")
    s = cohort_with_quantiles(per_event, "dn->up", "close_below_cloud__5m")
    if s is not None:
        lines.append(f"### dn->up  (n={s['n']})")
        lines.append("")
        lines.append(f"- **a. Q1/Q3**: {fmt_block(s)}")
        pred = lambda r: r["t0_value"] == 1.0 and r["post_median"] == 0.0
        lines.append(f"- **b. 典型形一致**: " + typical_match_rate(s["raw"], pred, "ダマシ型 (t0=1, post=0)"))
        # 補助: t0=1.0 の件数
        t0_one = lambda r: r["t0_value"] == 1.0
        lines.append(f"- 参考: t0=1 (切替時に雲下): " + typical_match_rate(s["raw"], t0_one, "t0=1"))
        post_zero = lambda r: r["post_median"] == 0.0
        lines.append(f"- 参考: post=0 (24h後雲外): " + typical_match_rate(s["raw"], post_zero, "post=0"))
        lines.append("")
    lines.append("---")
    lines.append("")

    # === ④ 短命 vs 通常 up→dn macd_hist__1h ===
    lines.append("## ④ 短命 vs 通常 up→dn — macd_hist (1h) の急峻 vs 漸進")
    lines.append("")
    lines.append("**仮説**: 短命 up→dn は pre→t0 のジャンプが大きい / 通常 up→dn は pre から既に高水準")
    lines.append("")
    for subset, label in [("short", "短命前run (prev≤4bar)"), ("normal", "通常前run (prev>4bar)")]:
        s = cohort_with_quantiles(per_event, "up->dn", "macd_hist__1h", subset=subset)
        if s is None:
            continue
        lines.append(f"### {label}  (n={s['n']})")
        lines.append("")
        lines.append(f"- **a. Q1/Q3**: {fmt_block(s)}")
        # ジャンプ量: t0 - pre
        s["raw"]["jump"] = s["raw"]["t0_value"] - s["raw"]["pre_median"]
        jump_q1 = s["raw"]["jump"].quantile(0.25)
        jump_med = s["raw"]["jump"].median()
        jump_q3 = s["raw"]["jump"].quantile(0.75)
        lines.append(f"- **pre→t0 ジャンプ量** (t0-pre): 中央値 **{fmt(jump_med)}** [Q1={fmt(jump_q1)}, Q3={fmt(jump_q3)}]")
        big_jump = lambda r: pd.notna(r["t0_value"]) and pd.notna(r["pre_median"]) and (r["t0_value"] - r["pre_median"]) > 30
        lines.append(f"- **b. ジャンプ>30 のイベント割合**: " + typical_match_rate(s["raw"], big_jump, "急峻スパイク"))
        ext = top_extremes(s["raw"], "jump", k=3, asc=False)
        lines.append(f"- **c. ジャンプ最大 top3**:")
        lines.append(fmt_extremes(ext))
        lines.append("")

    lines.append("---")
    lines.append("")

    # === ⑤ dn→up macd_hist_change__1h ===
    lines.append("## ⑤ dn→up — macd_hist_change (1h) の先行符号反転")
    lines.append("")
    lines.append("**仮説**: post 24h 中央値が正に転じる。t0 時点ではまだ負でも先行する。")
    lines.append("")
    s = cohort_with_quantiles(per_event, "dn->up", "macd_hist_change__1h")
    if s is not None:
        lines.append(f"### dn->up  (n={s['n']})")
        lines.append("")
        lines.append(f"- **a. Q1/Q3**: {fmt_block(s)}")
        sign_flip = lambda r: pd.notna(r["pre_median"]) and pd.notna(r["post_median"]) and r["pre_median"] < 0 and r["post_median"] > 0
        lines.append(f"- **b. 符号反転 (pre<0, post>0)**: " + typical_match_rate(s["raw"], sign_flip, "符号反転"))
        post_pos = lambda r: pd.notna(r["post_median"]) and r["post_median"] > 0
        lines.append(f"- 参考: post>0: " + typical_match_rate(s["raw"], post_pos, "post 正"))
        ext_high = top_extremes(s["raw"], "post_median", k=3, asc=False)
        lines.append(f"- **c. post 最大 top3** (反発が強かったイベント):")
        lines.append(fmt_extremes(ext_high))
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 解釈の指針")
    lines.append("")
    lines.append("- **典型形一致率 ≥ 70%**: 中央値が示す形は信頼できる → 判定ロジック設計の有力候補")
    lines.append("- **50〜70%**: 弱い傾向。単独では使えないが他指標と組み合わせる前提なら可")
    lines.append("- **< 50%**: 中央値の見え方は罠。発見として再考が必要")
    lines.append("- **Q1/Q3 が pre/post で 0 を跨ぐ**: 個別イベントは正負バラバラ・中央値だけで判定できない")
    lines.append("")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines))
    print(f"WROTE: {OUT_MD}")


if __name__ == "__main__":
    main()
