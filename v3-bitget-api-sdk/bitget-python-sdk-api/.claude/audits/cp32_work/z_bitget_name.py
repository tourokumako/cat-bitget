"""監査 cp32｜T-m が「使ってはいけない系列」まで正本の候補として指すかを試す。

なぜ試すか＝要件定義書 §8.2.1.1 の②の逐語
  「⚠️ **ファイル名に `bitget` が付く足は別物**（…＝Bitget先物。…）。
    **採点に使うのは Binance Spot 系列だけ**。連結・延長は必ず Binance Spot で揃える」。
＝data には Bitget 先物の5分足（`BTCUSDT-5m-bitget-…`）が実際に置いてある。
  T-m の見分けは `data/BTCUSDT-5m-*.csv` の名前だけなので、この系列も当たる。
  当たると「BARS_CSV の指し先を直す」と言う＝要件が禁じている方へ誘導しないか。

★置いた控えは、終わったら必ず消す。
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent
                       / "scripts" / "priority_rebuild"))
import observe_diag as od  # noqa: E402

SDK = pathlib.Path(__file__).resolve().parent.parent.parent.parent
SRC = pathlib.Path(__file__).resolve().parent / "five_min_extended.csv"
DST = SDK / "data/BTCUSDT-5m-bitget-cp32test-2026-08-31.csv"

print("data に在る 5分足（名前だけ）:")
for p in sorted((SDK / "data").glob("BTCUSDT-5m-*.csv")):
    print(f"  {p.name}")

DST.write_bytes(SRC.read_bytes())
print(f"\n置いた（Bitget 先物の名前）: {DST.name}")
try:
    ng = od.selftest_insp5(exit_=False)
    print(f"■ 番人: ❌ {len(ng)} 件")
    for x in ng:
        print(f"   {x}")
finally:
    DST.unlink()
    print("\n片づけ: 置いた控えは消しました。")
