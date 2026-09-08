"""監査 cp30｜Q2 の追加2＝番人4件が全部 通るのに、検査5 は止まる形が作れるか。

前の試し（q2b）では T-g が道連れで落ちたので、「番人の束としては落ちた」とも読めた。
ここでは、番人4件が **全部 通る**のに検査5 が止まる控えを作れるかを試す。

作る控え（1分足）
  ・2023-06-25 00:00 に1行（T-i の始まりを満たす）
  ・2024-03-01 00:00 〜 2024-03-04 まで1分ごとに詰める（T-g と T-j が使う3日ぶんの切れ端）
  ・2026-06-30 12:00 に1行（T-i の末 SCORE_END＝2026-06-30 00:00 を満たす）
  ＝T-i は min と max しか見ないので通る。T-g・T-j は3日ぶんが詰まっているので通る。
  ＝ところが検査5 は 2026-06-30 23:55 まで要るので、load_1m が止める。

★本物のデータも observe_diag.py も1文字も触らない。
"""
import pathlib
import sys

import numpy as np
import pandas as pd

PR = pathlib.Path("scripts/priority_rebuild").resolve()
sys.path.insert(0, str(PR))
import observe_diag as od  # noqa: E402

WORK = pathlib.Path(".claude/audits/cp30_work").resolve()
csv = WORK / "one_min_missing_last_day.csv"

dense = pd.date_range("2024-03-01", "2024-03-05", freq="1min", inclusive="left")
idx = pd.DatetimeIndex(["2023-06-25 00:00:00"]).append(dense).append(
    pd.DatetimeIndex(["2026-06-30 12:00:00"]))
c = 100.0 + np.arange(len(idx), dtype=float) * 0.001
pd.DataFrame({"timestamp": idx, "open": c, "high": c + 0.05, "low": c - 0.05,
              "close": c, "volume": 1.0}).to_csv(csv, index=False)

print("=" * 100)
print("監査 cp30 Q2 追加2｜番人4件が全部 通るのに、検査5 は止まる形が作れるか")
print("=" * 100)
print(f"  作った控え: {csv.name}（{len(idx)} 行 ／ {idx.min()} 〜 {idx.max()}）")
print("  ＝最後の1日（2026-06-30 12:00 より後）が欠けている1分足")

od.ONE_MIN_CSV = str(csv)
od._ONE_MIN_CACHE.clear()
od._CYC_MEMO["sig"], od._CYC_MEMO["v"] = None, {}

print("\n① 番人4件（--selftest-insp5 と同じもの）")
ng = od.selftest_insp5(exit_=False)
print(f"   → ❌ {len(ng)} 件 ／ 終了コードに直すと {1 if ng else 0}")
for x in ng:
    print(f"     ❌ {x[:140]}")

print("\n② 検査5 が実際に渡す末（2026-06-30 23:55）で load_1m を呼ぶ＝検査5 の1行目と同じ")
try:
    od._ONE_MIN_CACHE.clear()
    od.load_1m(pd.Timestamp("2023-06-25 00:00"), pd.Timestamp("2026-06-30 23:55"))
    print("   → 止まらなかった")
except SystemExit as e:
    print(f"   → ★止まった: {str(e)[:160]}")

print("\n■ 判定")
if not ng:
    print("   ★番人4件は全部 通り、検査5 は止まる＝番人は『検査5 が最後まで走る』ことを守り切れていない。")
else:
    print("   番人のどれかが落ちた＝この形では守れている。落ちた番人は上のとおり。")
print("=" * 100)
