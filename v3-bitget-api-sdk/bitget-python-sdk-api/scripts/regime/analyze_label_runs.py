"""
analyze_label_runs.py
教師ラベル（4h 粒度・regime_samples_4h_*.csv）の実体検証。
連続区間（run）の長さ分布・空ラベルギャップ・遷移パターンを集計する。

入力: data/regime_samples_4h_2022.csv / _2023.csv / _2024.csv / regime_samples_4h.csv(2025)
出力: results/regime_label_analysis/label_run_audit.md

副作用なし（ラベルファイルは読むだけ）。
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
OUT_DIR = REPO_ROOT / "results" / "regime_label_analysis"
OUT_PATH = OUT_DIR / "label_run_audit.md"

INPUTS = [
    ("2022", DATA_DIR / "regime_samples_4h_2022.csv"),
    ("2023", DATA_DIR / "regime_samples_4h_2023.csv"),
    ("2024", DATA_DIR / "regime_samples_4h_2024.csv"),
    ("2025", DATA_DIR / "regime_samples_4h.csv"),
]

VALID_LABELS = {"uptrend", "range", "downtrend", "up", "rg", "dn"}
LABEL_NORMALIZE = {"uptrend": "up", "range": "rg", "downtrend": "dn"}


def load_all() -> pd.DataFrame:
    frames = []
    for year, path in INPUTS:
        if not path.exists():
            print(f"[WARN] missing: {path}", file=sys.stderr)
            continue
        df = pd.read_csv(path)
        df["year"] = year
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out["timestamp_utc"] = pd.to_datetime(out["timestamp_utc"], utc=True)
    out = out.sort_values("timestamp_utc").reset_index(drop=True)
    out["label_raw"] = out["label"].fillna("").astype(str).str.strip()
    out["label_norm"] = out["label_raw"].map(
        lambda x: LABEL_NORMALIZE.get(x, x) if x else "blank"
    )
    return out


def run_length_encode(labels: list[str]) -> list[tuple[str, int, int, int]]:
    """returns list of (label, start_idx, end_idx_inclusive, length_in_bars)"""
    runs = []
    if not labels:
        return runs
    cur = labels[0]
    start = 0
    for i in range(1, len(labels)):
        if labels[i] != cur:
            runs.append((cur, start, i - 1, i - start))
            cur = labels[i]
            start = i
    runs.append((cur, start, len(labels) - 1, len(labels) - start))
    return runs


def quantile(arr: list[int], q: float) -> float:
    if not arr:
        return float("nan")
    s = sorted(arr)
    return float(pd.Series(s).quantile(q))


def fmt_run_distribution(name: str, lengths: list[int]) -> str:
    if not lengths:
        return f"### {name}\n\n(no runs)\n\n"
    n = len(lengths)
    total_bars = sum(lengths)
    median_bars = quantile(lengths, 0.5)
    q1 = quantile(lengths, 0.25)
    q3 = quantile(lengths, 0.75)
    mn = min(lengths)
    mx = max(lengths)
    le_2 = sum(1 for x in lengths if x <= 2)
    le_6 = sum(1 for x in lengths if x <= 6)
    le_12 = sum(1 for x in lengths if x <= 12)
    le_30 = sum(1 for x in lengths if x <= 30)
    lines = [
        f"### {name}",
        "",
        f"- run 件数: **{n}**",
        f"- 総バー数: {total_bars} bar ({total_bars * 4} h ≈ {total_bars * 4 / 24:.1f} d)",
        f"- 長さ分布（バー単位 / 1 bar = 4h）: 中央値 **{median_bars:.0f}** [Q1={q1:.0f}, Q3={q3:.0f}] / min={mn}, max={mx}",
        f"- 中央値を時間換算: **{median_bars * 4:.0f} h ≈ {median_bars * 4 / 24:.1f} d**",
        "",
        "**短区間の割合**:",
        "",
        "| 閾値 | 件数 | 全 run に占める割合 |",
        "|---|---:|---:|",
        f"| ≤ 2 bar (≤ 8 h) | {le_2} | {le_2 / n * 100:.1f}% |",
        f"| ≤ 6 bar (≤ 24 h, 1日) | {le_6} | {le_6 / n * 100:.1f}% |",
        f"| ≤ 12 bar (≤ 48 h, 2日) | {le_12} | {le_12 / n * 100:.1f}% |",
        f"| ≤ 30 bar (≤ 120 h, 5日) | {le_30} | {le_30 / n * 100:.1f}% |",
        "",
    ]
    return "\n".join(lines)


def fmt_short_samples(label: str, runs: list[tuple], df: pd.DataFrame, threshold: int = 2, k: int = 3) -> list[str]:
    short = [r for r in runs if r[0] == label and r[3] <= threshold]
    if not short:
        return [f"- {label}: 該当 run なし"]
    lines = [f"- {label} ≤ {threshold} bar (≤ {threshold * 4} h) の短 run 例（先頭 {min(k, len(short))}件 / 全{len(short)}件）:"]
    for r in short[:k]:
        s_ts = df.loc[r[1], "timestamp_utc"]
        e_ts = df.loc[r[2], "timestamp_utc"]
        lines.append(f"  - {s_ts.strftime('%Y-%m-%d %H:%M')} 〜 {e_ts.strftime('%Y-%m-%d %H:%M')} ({r[3]} bar)")
    return lines


def main() -> None:
    df = load_all()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total = len(df)
    counts = df["label_norm"].value_counts().to_dict()

    runs_all = run_length_encode(df["label_norm"].tolist())

    by_label_lengths: dict[str, list[int]] = {"up": [], "rg": [], "dn": [], "blank": []}
    for r in runs_all:
        by_label_lengths.setdefault(r[0], []).append(r[3])

    direct_trans = Counter()
    blank_bridged = Counter()
    for i in range(1, len(runs_all)):
        prev = runs_all[i - 1][0]
        cur = runs_all[i][0]
        direct_trans[(prev, cur)] += 1
        if prev == "blank" and i >= 2:
            before_blank = runs_all[i - 2][0]
            blank_bridged[(before_blank, cur)] += 1

    out_lines: list[str] = []
    out_lines.append("# 教師ラベル run-length 監査（C: ラベル実体検証）")
    out_lines.append("")
    out_lines.append(f"対象ファイル: regime_samples_4h_2022/2023/2024.csv + regime_samples_4h.csv(2025)")
    out_lines.append(f"粒度: **4h バー** / 期間: {df['timestamp_utc'].min()} 〜 {df['timestamp_utc'].max()}")
    out_lines.append("")

    out_lines.append("## ① ラベル全体カウント")
    out_lines.append("")
    out_lines.append(f"- 総バー数: **{total}** (= {total / 6:.0f} 日相当)")
    out_lines.append("")
    out_lines.append("| label | バー数 | 割合 |")
    out_lines.append("|---|---:|---:|")
    for k in ["up", "rg", "dn", "blank"]:
        c = counts.get(k, 0)
        out_lines.append(f"| {k} | {c} | {c / total * 100:.1f}% |")
    out_lines.append("")

    out_lines.append("## ② run-length 分布（同一ラベル連続塊）")
    out_lines.append("")
    out_lines.append(f"全 run 件数: **{len(runs_all)}**")
    out_lines.append("")

    out_lines.append(fmt_run_distribution("Uptrend (up)", by_label_lengths.get("up", [])))
    out_lines.append(fmt_run_distribution("Range (rg)", by_label_lengths.get("rg", [])))
    out_lines.append(fmt_run_distribution("Downtrend (dn)", by_label_lengths.get("dn", [])))
    out_lines.append(fmt_run_distribution("Blank (空ラベル)", by_label_lengths.get("blank", [])))

    out_lines.append("## ③ 遷移パターン（直接遷移）")
    out_lines.append("")
    out_lines.append("隣接する run の (前ラベル → 後ラベル) の件数。空ラベルも含む。")
    out_lines.append("")
    out_lines.append("| 前 → 後 | 件数 |")
    out_lines.append("|---|---:|")
    states = ["up", "rg", "dn", "blank"]
    for a in states:
        for b in states:
            if a == b:
                continue
            c = direct_trans.get((a, b), 0)
            if c > 0:
                out_lines.append(f"| {a} → {b} | {c} |")
    out_lines.append("")

    out_lines.append("## ④ 空ラベル跨ぎ遷移（blank を挟んだ非空遷移）")
    out_lines.append("")
    out_lines.append("`X → blank → Y` の (X, Y) 件数（X≠blank, Y≠blank）。")
    out_lines.append("空ラベルが「中間状態」として真の遷移を分断しているケースの実体。")
    out_lines.append("")
    out_lines.append("| X → blank → Y | 件数 |")
    out_lines.append("|---|---:|")
    for a in ["up", "rg", "dn"]:
        for b in ["up", "rg", "dn"]:
            c = blank_bridged.get((a, b), 0)
            if c > 0:
                out_lines.append(f"| {a} → blank → {b} | {c} |")
    out_lines.append("")

    out_lines.append("## ⑤ 短 run 代表サンプル（≤ 2 bar = ≤ 8 h）")
    out_lines.append("")
    for label in ["up", "rg", "dn"]:
        out_lines.extend(fmt_short_samples(label, runs_all, df, threshold=2, k=3))
    out_lines.append("")

    out_lines.append("## ⑥ 観察メモ（数値の意味付けはまこさんと相談）")
    out_lines.append("")
    out_lines.append("- 空ラベル ratio が高いほど「人間が判断保留した中間状態」が多い")
    out_lines.append("- 短 run（≤ 2 bar）の割合が高いほど切替が頻繁・ノイズ的可能性")
    out_lines.append("- blank 跨ぎ遷移の構成（同ラベル戻り vs 別ラベル遷移）が切替点定義の参考になる")
    out_lines.append("")

    OUT_PATH.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"WROTE: {OUT_PATH}")
    print(f"total bars: {total}, runs: {len(runs_all)}")
    print(f"label counts: {counts}")


if __name__ == "__main__":
    main()
