"""監査 cp32｜この直しが新しい不具合を作っていないかを、端の場合で探す。

見るもの（5つ）
  ① 行が1本しか無い CSV を渡す（バーの間隔が測れない）→ 落ちるか・例外にならないか
  ② 中身が空の CSV を渡す → 落ちるか・例外にならないか
  ③ 実在しないパスを渡す → 落ちるか・例外にならないか
  ④ data に「末が読めない」5分足を置く → T-m は見つけるか（黙って見逃さないか）
  ⑤ data に「末が正本と同じ」5分足を置く → T-m は誤って落ちないか（誤報が出ないか）

★本物のファイルは1文字も書き替えない。④⑤で data に置いた控えは、終わったら必ず消す。
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent
                       / "scripts" / "priority_rebuild"))
import observe_diag as od  # noqa: E402

SDK = pathlib.Path(__file__).resolve().parent.parent.parent.parent
HERE = pathlib.Path(__file__).resolve().parent
HEAD = "timestamp,open,high,low,close,volume\n"

one_row = HERE / "edge_one_row.csv"
one_row.write_text(HEAD + "2026-08-31 23:55:00,1,1,1,1,1\n", encoding="utf-8")
empty = HERE / "edge_empty.csv"
empty.write_text(HEAD, encoding="utf-8")

CASES = {
    "① 行が1本しか無い": str(one_row),
    "② 中身が空": str(empty),
    "③ 実在しないパス": str(HERE / "no_such_file.csv"),
}
for name, p in CASES.items():
    try:
        ng = od.selftest_insp5(exit_=False, bars_csv=p)
        print(f"■ {name}: ❌ {len(ng)} 件")
        for x in ng:
            print(f"     {x[:120]}")
    except Exception as e:                              # noqa: BLE001
        print(f"■ {name}: ★例外で落ちた {type(e).__name__}: {e}")

# ④ 末が読めない5分足を data に置く
bad = SDK / "data/BTCUSDT-5m-cp32edge-badtail.csv"
bad.write_text(HEAD + "これは時刻ではない,1,1,1,1,1\n", encoding="utf-8")
try:
    ng = od.selftest_insp5(exit_=False)
    print(f"■ ④ data に末が読めない5分足を置いた: ❌ {len(ng)} 件"
          + ("（T-m は見つけていない＝黙って見逃す）" if not any("T-m" in x for x in ng) else ""))
finally:
    bad.unlink()

# ⑤ 末が正本と同じ5分足を data に置く（誤報が出ないか）
same = SDK / "data/BTCUSDT-5m-cp32edge-same.csv"
same.write_text(HEAD + "2026-06-30 23:55:00,1,1,1,1,1\n", encoding="utf-8")
try:
    ng = od.selftest_insp5(exit_=False)
    print(f"■ ⑤ data に末が正本と同じ5分足を置いた: ❌ {len(ng)} 件"
          + ("（誤報なし）" if not any("T-m" in x for x in ng) else "（★誤報＝T-m が落ちた）"))
finally:
    same.unlink()

for p in (one_row, empty):
    p.unlink()
print("\n片づけ: data に置いた控えは消しました。")
