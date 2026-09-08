"""監査 cp30｜検査5 の 1m の採点窓が、理屈より 3本 少ない理由を突き止める。

元データには欠けが無い（q1c で確かめた＝採点窓に 175,680 本ちょうど在る）。
それでも検査5 は 175,677 と出した。差は 3本。

疑い＝検査5 が1分足を切り出す末が「5分足の最後のバーの開始時刻」だから。
  `_insp_samples`:4043 → `one = load_1m(span.index[0], span.index[-1])`
  span.index[-1] は5分足の最後のバー＝2026-06-30 23:55。
  ＝1分足は 23:55 で切られ、23:56・23:57・23:58・23:59 の4本が落ちる。
  そのうち「閉じた時刻」が採点窓（2026-07-01 より前）に入るのは 3本。
"""
import pathlib
import sys

import pandas as pd

PR = pathlib.Path("scripts/priority_rebuild").resolve()
sys.path.insert(0, str(PR))
import observe_diag as od  # noqa: E402

bars = pd.read_csv("data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv",
                   parse_dates=["timestamp"]).set_index("timestamp").sort_index()
cfg = od.load_config(".claude/audits/cp30_work/observe_config_cp30_small.json")
span = bars.loc[od.SEARCH_START - pd.Timedelta(days=int(cfg["warmup_days"])):]
print("=" * 100)
print(f"5分足の枠 span: {span.index[0]} 〜 {span.index[-1]}（{len(span):,} 本）")

one = od.load_1m(span.index[0], span.index[-1])
print(f"検査5 が読む1分足   : {one.index[0]} 〜 {one.index[-1]}（{len(one):,} 本）")

src, closed = od.insp5_frame(span, "1m", one)
s0, s1 = od.SCORE_START, od.SCORE_END + pd.Timedelta("1D")
n_s = int(((closed >= s0) & (closed < s1)).sum())
print(f"\n■ 検査5 の当てはめ（closed = 1分足の時刻 + 1分）で採点窓に入る本数 = {n_s:,}")
print(f"   検査5 の出力（HT_DCPERIOD__1m の採点）        = 175,677")
print(f"   理屈どおり（122日 × 1440）                     = 175,680")

full = pd.date_range(s0, s1, freq="1min", inclusive="left") - pd.Timedelta("1min")
lost = full.difference(one.index)
print(f"\n■ 落ちている1分足の時刻 = {len(lost)} 本: {[str(x) for x in lost]}")
print(f"   1分足の元データには在るか: "
      f"{[str(x) for x in lost if x <= pd.Timestamp('2026-06-30 23:59')]} は元データに在る（q1c で確認）")
print("\n■ 結論")
print("   検査5 は1分足を「5分足の最後のバーの開始時刻（23:55）」で切る。")
print("   だから 23:56・23:57・23:58・23:59 の4本が枠に入らない。")
print("   そのうち閉じた時刻が採点窓に入るのは3本＝出力が 175,677 になる。")
print("=" * 100)
