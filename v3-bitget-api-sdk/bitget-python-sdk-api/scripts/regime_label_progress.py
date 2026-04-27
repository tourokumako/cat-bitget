"""regime_label_progress.py — 1825日ラベル進捗確認

Usage:
    python3 scripts/regime_label_progress.py
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "regime_ground_truth_daily_human.csv"

VALID_LABELS = {"downtrend", "range", "uptrend"}


def main() -> None:
    rows: list[tuple[date, str, str]] = []
    with CSV_PATH.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append((date.fromisoformat(r["date"]), r["label"].strip(), r["note"].strip()))

    rows.sort(key=lambda x: x[0])
    total = len(rows)
    filled = [r for r in rows if r[1] != ""]
    empty = [r for r in rows if r[1] == ""]
    invalid = [r for r in filled if r[1] not in VALID_LABELS]

    print(f"=== regime label progress ===")
    print(f"total days     : {total}")
    print(f"filled         : {len(filled):>5} ({len(filled) / total * 100:5.1f}%)")
    print(f"empty          : {len(empty):>5} ({len(empty) / total * 100:5.1f}%)")
    print(f"invalid label  : {len(invalid):>5}  (expected: {sorted(VALID_LABELS)})")

    if filled:
        c = Counter(r[1] for r in filled)
        print()
        print(f"label distribution (filled only):")
        for k in sorted(c):
            print(f"  {k:<10} {c[k]:>5} ({c[k] / len(filled) * 100:5.1f}%)")

    if empty:
        runs: list[tuple[date, date, int]] = []
        run_start = empty[0][0]
        prev = empty[0][0]
        for d, _, _ in empty[1:]:
            if (d - prev).days == 1:
                prev = d
            else:
                runs.append((run_start, prev, (prev - run_start).days + 1))
                run_start = d
                prev = d
        runs.append((run_start, prev, (prev - run_start).days + 1))
        runs.sort(key=lambda r: -r[2])

        print()
        print(f"empty contiguous runs (top 5 by length):")
        for s, e, n in runs[:5]:
            print(f"  {s} 〜 {e}  ({n} days)")

    if invalid:
        print()
        print(f"invalid label samples (top 5):")
        for d, lab, _ in invalid[:5]:
            print(f"  {d}  label='{lab}'")


if __name__ == "__main__":
    main()
