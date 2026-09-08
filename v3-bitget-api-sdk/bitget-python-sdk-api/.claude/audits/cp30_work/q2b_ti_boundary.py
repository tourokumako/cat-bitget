"""監査 cp30｜Q2 の追加＝番人 T-i が見ている期間の末が、検査5 が実際に要る末と合っているか。

読み取ったこと（実物）
  ・T-i は `need_e = SCORE_END` で見る（observe_diag.py:6168）。SCORE_END は
    `pd.Timestamp("2026-06-30")`＝**その日の 00:00**（periods.py:81）。
  ・ところが検査5 が実際に `load_1m` へ渡す末は `span.index[-1]`＝5分足の最後のバー
    ＝**2026-06-30 23:55**（`_insp_samples`:4043）。
  ＝T-i が見ている末は、検査5 が要る末より **約24時間 手前**。

この試しでやること
  ①「2023-06-25 00:00 と 2026-06-30 12:00 の2行だけ」の1分足の控えを作る
  ②その控えを指し先にして T-i を走らせる → 通ってしまうか
  ③同じ控えで、検査5 が実際に渡す末（2026-06-30 23:55）を要求する → 止まるか
  ＝②が通って③が止まれば、T-i は「検査5 が走る」ことを守り切れていない。
★本物のデータも observe_diag.py も1文字も触らない（記憶の中で指し先を差し替えるだけ）。
"""
import pathlib
import sys

import pandas as pd

PR = pathlib.Path("scripts/priority_rebuild").resolve()
sys.path.insert(0, str(PR))
import observe_diag as od  # noqa: E402

WORK = pathlib.Path(".claude/audits/cp30_work").resolve()
tiny = WORK / "one_min_two_rows.csv"
pd.DataFrame({
    "timestamp": ["2023-06-25 00:00:00", "2026-06-30 12:00:00"],
    "open": [1.0, 2.0], "high": [1.0, 2.0], "low": [1.0, 2.0],
    "close": [1.0, 2.0], "volume": [1.0, 1.0],
}).to_csv(tiny, index=False)

print("=" * 100)
print("監査 cp30 Q2 追加｜T-i が見ている期間の末は、検査5 が要る末と合っているか")
print("=" * 100)
print(f"  SCORE_END（T-i が見る末）        = {od.SCORE_END}")
print(f"  検査5 が load_1m へ渡す末（実物） = 5分足の最後のバー＝2026-06-30 23:55")
print(f"  差                               = 約 {(pd.Timestamp('2026-06-30 23:55') - od.SCORE_END)}")

od.ONE_MIN_CSV = str(tiny)
od._ONE_MIN_CACHE.clear()
od._CYC_MEMO["sig"], od._CYC_MEMO["v"] = None, {}

print("\n① 2行だけの控え（2023-06-25 00:00 と 2026-06-30 12:00）を指し先にして、番人を走らせる")
ng = od.selftest_insp5(exit_=False)
ti = [x for x in ng if x.startswith("T-i")]
print(f"   → T-i は {'落ちた' if ti else '★通ってしまった'} ／ ❌ 全体 {len(ng)} 件")
for x in ng:
    print(f"     ❌ {x[:130]}")

print("\n② 同じ控えで、検査5 が実際に渡す末（2026-06-30 23:55）を要求してみる")
try:
    od._ONE_MIN_CACHE.clear()
    od.load_1m(pd.Timestamp("2023-06-25 00:00"), pd.Timestamp("2026-06-30 23:55"))
    print("   → 止まらなかった")
except SystemExit as e:
    print(f"   → ★止まった: {str(e)[:150]}")

print("\n③ おまけ＝T-i は『中身が埋まっているか』を見るか（2行しかない控えで通るか）")
print("   上の①の結果がその答え（設計書 §7 の補4 に『期間を覆っているかだけ』と明記あり）")
print("=" * 100)
