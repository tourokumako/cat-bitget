"""監査 cp30｜検査5 が出した1分足の本数を、元データを直に数えて裏取りする。

検査5 の出力（2026-09-08・監査の走行）
  1m … 有効 790560（値決め）・175677（採点）
  3m … 有効 263520（値決め）・ 58560（採点）
  5m … 有効 158112（値決め）・ 35136（採点）

理屈どおりの本数
  値決め窓 2024-03-01〜2025-09-01（排他）＝549日 → 1m 790,560／3m 263,520／5m 158,112
  採点窓   2026-03-01〜2026-07-01（排他）＝122日 → 1m 175,680／3m  58,560／5m  35,136

★1m の採点窓だけ 175,677＝理屈より 3本 少ない。元データの欠けかどうかを、CSV を直に数えて確かめる。
"""
import pathlib
import sys

import pandas as pd

PR = pathlib.Path("scripts/priority_rebuild").resolve()
sys.path.insert(0, str(PR))
import observe_diag as od  # noqa: E402

p = pathlib.Path(od.ONE_MIN_CSV)
d = pd.read_csv(p, usecols=["timestamp"], parse_dates=["timestamp"]).set_index("timestamp").sort_index()
print("=" * 100)
print(f"元データ: {p.name}（{len(d)} 行 ／ {d.index.min()} 〜 {d.index.max()}）")
print("=" * 100)

for nm, a, b, per_day in (("値決め窓", od.SEARCH_START, od.SEARCH_END, 1440),
                          ("採点窓", od.SCORE_START, od.SCORE_END + pd.Timedelta("1D"), 1440)):
    # 検査5 と同じ当てはめ＝closed = index + 1分 が窓の中に入るか
    closed = d.index + pd.Timedelta("1min")
    n = int(((closed >= a) & (closed < b)).sum())
    days = (b - a).days
    ideal = days * per_day
    print(f"\n■ {nm} {a.date()}〜{(b - pd.Timedelta('1D')).date()}（{days} 日）")
    print(f"   1分足の実数 = {n:,} 本 ／ 理屈どおり = {ideal:,} 本 ／ 差 = {ideal - n:,} 本")
    if ideal != n:
        full = pd.date_range(a, b, freq="1min", inclusive="left") - pd.Timedelta("1min")
        missing = full.difference(d.index)
        print(f"   ★欠けている時刻（最大10件）: {[str(x) for x in missing[:10]]}")

print("\n" + "=" * 100)
print("★この欠けは、この工事が作ったものではない（元データそのものの欠け）。")
print("  直す前は 1m の欄が5分足の写しだったので、この欠けは1度も画面に出ていなかった。")
print("=" * 100)
