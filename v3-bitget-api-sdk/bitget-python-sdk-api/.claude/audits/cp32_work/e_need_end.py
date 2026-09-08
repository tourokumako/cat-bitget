"""監査 cp32｜別枠 E＝短い5分足を渡しても、守りが弱くならないかを見る。

依頼書 §3.4 の E の逐語＝「★短い切れ端（`…_slice_V9FULL_safe.csv`）を渡して、
守りが弱くならないかを見てください」。

★見えるようにするやり方＝`load_1m` を「呼ばれた引数を覚えるだけ」のものに差し替えて、
  番人 `selftest_insp5` が **何日まで覆っていることを要求したか（need_e）** を取り出す。
  ＝画面の ❌ の件数だけでは、要求が下がったのか上がったのかが分からないため。
★本物のファイルは1文字も書き替えない（差し替えは記憶の中だけ）。
"""
import pathlib
import sys

SDK = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str((SDK / "scripts" / "priority_rebuild").resolve()))
import observe_diag as od  # noqa: E402

CASES = {
    "(a) パスを渡さない": None,
    "(b) 本物の5分足（正本）": str(SDK / "data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv"),
    "(c) 短い切れ端（末 2026-02-28）": str(SDK / "data/BTCUSDT-5m-2024-09-01_2026-02-28_slice_V9FULL_safe.csv"),
    "(d) 取り足した控え（末 2026-08-31）": str(pathlib.Path(__file__).resolve().parent / "five_min_extended.csv"),
}

real_load_1m = od.load_1m
seen: list = []


def spy(start, end, path=None):
    seen.append((start, end))
    return real_load_1m(start, end, path)


print(f"5分足の正本（BARS_CSV）= {od.BARS_CSV}")
print(f"その末 = {od._tail_timestamps(SDK / od.BARS_CSV, n=1)[-1]}")
print()
for name, p in CASES.items():
    seen.clear()
    od.load_1m = spy
    try:
        ng = od.selftest_insp5(exit_=False, bars_csv=p)
    finally:
        od.load_1m = real_load_1m
    need_e = seen[0][1] if seen else "(load_1m が呼ばれなかった)"
    print(f"■ {name}")
    print(f"   要求した末（need_e）= {need_e}")
    print(f"   ❌ {len(ng)} 件" + ("" if not ng else "＝" + " ／ ".join(x[:70] for x in ng)))
