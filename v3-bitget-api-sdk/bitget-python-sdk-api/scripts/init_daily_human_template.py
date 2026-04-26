"""data/regime_ground_truth_daily_human.csv の初期テンプレートを生成。

既存の週単位肉眼判定（regime_ground_truth.csv）を365日に展開し、
週ラベル → その週7日全部に同ラベルをデフォルトセット。
未記入の週は空欄のまま。後でダッシュボードで日単位調整。
"""
from __future__ import annotations

import csv
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
WEEKLY_PATH = REPO_ROOT / "data" / "regime_ground_truth.csv"
CSV_5M_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2025-04-01_03-31_365d.csv"
OUT_PATH = REPO_ROOT / "data" / "regime_ground_truth_daily_human.csv"


def main() -> None:
    df_5m = pd.read_csv(CSV_5M_PATH)
    df_5m["ts"] = pd.to_datetime(df_5m["timestamp"])
    dates = pd.date_range(df_5m["ts"].min().normalize(), df_5m["ts"].max().normalize(), freq="D")

    # 週ラベル読み込み（week_start ISO月曜起点）
    weekly: dict = {}
    with WEEKLY_PATH.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ws = r.get("week_start", "").strip()
            label = (r.get("label") or "").strip()
            note = (r.get("note") or "").strip()
            if ws:
                weekly[ws] = (label, note)

    rows = [["date", "label", "note"]]
    for d in dates:
        # この日が属する週の week_start（pandas の月曜起点）を計算
        weekday = d.weekday()  # 月=0 ... 日=6
        wk_start = (d - pd.Timedelta(days=weekday)).strftime("%Y-%m-%d")
        # ただし週版はISO日曜終わり（pandasのW-SUN・left）= 月曜起点だが
        # サンデー終わりweekendなのでweek_startは日曜起点ケースもある。
        # 実データ確認: 既CSVは "2025-03-30"（日曜）から始まっている → 日曜起点。
        # → 日曜起点で再計算
        sunday_start = (d - pd.Timedelta(days=(d.weekday() + 1) % 7)).strftime("%Y-%m-%d")
        # weekly に sunday_start があるか確認
        if sunday_start in weekly:
            label, note = weekly[sunday_start]
        elif wk_start in weekly:
            label, note = weekly[wk_start]
        else:
            label, note = "", ""
        # CSV エスケープ
        if "," in note or '"' in note:
            note = '"' + note.replace('"', '""') + '"'
        rows.append([d.strftime("%Y-%m-%d"), label, note])

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(row)

    labeled = sum(1 for r in rows[1:] if r[1])
    print(f"[init_daily_human_template] {len(rows) - 1} 日 ({labeled} 日にデフォルト継承) → {OUT_PATH}")


if __name__ == "__main__":
    main()
