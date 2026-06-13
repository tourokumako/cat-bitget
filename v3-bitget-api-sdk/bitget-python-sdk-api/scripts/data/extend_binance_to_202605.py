"""既存の正本 Binance 5m足（2021-04-01〜2026-03-31）に 2026-04・05 を連結する一回限りスクリプト。

背景: 検証期間を2ヶ月後ろ倒し（封印2026-03〜05）するため、採点の土台である Binance Spot 5m足を
2026-05末まで延長する。download_binance_5y.py 本体は μs(16桁) タイムスタンプ判定にバグがあり
2025年以降が 0 行になるため、本スクリプトで 2026-04/05 の zip を正しく parse して連結する（本体は別件で修正）。

入力:
  data/BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv  （既存正本・2021-04-01〜2026-03-31 23:55）
  data/_binance_tmp/BTCUSDT-5m-2026-04.zip / ...2026-05.zip  （Binance Vision 既取得）
出力:
  data/BTCUSDT-5m-2021-04-01_2026-05-31_V9FULL_safe.csv  （6列・既存と同形式・既存ファイルは温存）

検証（実行時に出す）: 境界連続性 / 5分グリッド欠損数 / 重複 / 行数。
"""
from __future__ import annotations
import csv, io, zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"
TMP = ROOT / "data" / "_binance_tmp"
NEW_MONTHS = ["2026-04", "2026-05"]
OUT = ROOT / "data" / "BTCUSDT-5m-2021-04-01_2026-05-31_V9FULL_safe.csv"

FMT = "%Y-%m-%d %H:%M:%S"


def parse_raw_ts(raw: int) -> datetime:
    """Binance Vision: 2024以前=ms(13桁), 2025以降=μs(16桁・~1.7e15)。
    1e14 を境に μs/ms を分離（μs ~1.7e15 > 1e14 > ms ~1.7e12）。"""
    if raw > 1e14:
        sec = raw / 1e6   # μs
    elif raw > 1e11:
        sec = raw / 1e3   # ms
    else:
        sec = raw         # sec
    return datetime.utcfromtimestamp(sec)


def load_base(path: Path):
    rows = []
    with open(path) as f:
        r = csv.reader(f)
        header = next(r)
        for row in r:
            if not row:
                continue
            rows.append(row)  # [ts_str, o, h, l, c, v]
    return header, rows


def load_zip_month(month: str):
    p = TMP / f"BTCUSDT-5m-{month}.zip"
    if not p.exists():
        raise FileNotFoundError(p)
    out = []
    with zipfile.ZipFile(p) as zf:
        name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        with zf.open(name) as f:
            for r in csv.reader(io.TextIOWrapper(f, encoding="utf-8")):
                if not r or not r[0].lstrip("-").isdigit():
                    continue
                ts = parse_raw_ts(int(r[0])).strftime(FMT)
                # Binance kline: 1=open 2=high 3=low 4=close 5=volume
                out.append([ts, r[1], r[2], r[3], r[4], r[5]])
    return out


def main():
    header, base = load_base(BASE)
    print(f"[base] {BASE.name}: {len(base)} rows  {base[0][0]} .. {base[-1][0]}")

    added = []
    for mth in NEW_MONTHS:
        rows = load_zip_month(mth)
        print(f"[zip ] {mth}: {len(rows)} rows  {rows[0][0]} .. {rows[-1][0]}")
        added.append((mth, rows[0][0], rows[-1][0]))
        base.extend(rows)

    # 重複除去（timestamp） + ソート
    seen = {}
    for row in base:
        seen[row[0]] = row  # 後勝ち（zip が base 末尾と重なれば zip を採用）
    merged = [seen[k] for k in sorted(seen.keys())]
    dup = len(base) - len(merged)

    # 5分グリッド連続性チェック
    gaps = []
    prev = None
    for row in merged:
        t = datetime.strptime(row[0], FMT)
        if prev is not None:
            d = (t - prev).total_seconds()
            if d != 300:
                gaps.append((prev.strftime(FMT), row[0], int(d)))
        prev = t

    # 書き出し
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(merged)

    print(f"\n[merge] 重複除去: {dup} 件 / 連結後 {len(merged)} rows  {merged[0][0]} .. {merged[-1][0]}")
    print(f"[gaps ] 5分グリッド非連続: {len(gaps)} 箇所")
    for g in gaps[:20]:
        print(f"   gap {g[0]} -> {g[1]}  ({g[2]}s)")
    # 境界（旧末尾 2026-03-31 23:55 → 2026-04-01 00:00）
    boundary = [r for r in merged if r[0] in ("2026-03-31 23:55:00", "2026-04-01 00:00:00")]
    print(f"[bound] 境界バー:")
    for r in boundary:
        print(f"   {r}")
    print(f"\n→ {OUT}")


if __name__ == "__main__":
    main()
