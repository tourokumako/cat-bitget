#!/usr/bin/env python3
"""監査 cp31 の Critical 1｜5分足を採点窓より先まで取り足した控えを作る（read-only の材料づくり）。

なぜ要るか＝監査 cp30 の Critical 1 の「本命の危険」は、5分足だけを取り足して
1分足をそのままにする道。cp31 は、その道が本当に塞がったかを実物で試す。

作るもの2つ（どちらも本物のファイルは1文字も触らない）。
  A) five_min_extended.csv  ＝本物の5分足の最後のバー（2026-06-30 23:55）から
     2026-08-31 23:55 まで、5分刻みで行を足したもの（値は最後の終値をそのまま置く）。
  B) five_min_same.csv      ＝本物の5分足と同じ末（比べる相手）。
両方とも、行数を減らすために「先頭の1行＋末の付近」だけにはしない
（selftest_insp5 は timestamp の最大しか見ないが、検査5 が読む形に合わせておく）。
"""
import pathlib
import sys

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
SDK = HERE.parent.parent.parent                      # bitget-python-sdk-api
SRC = SDK / "data" / "BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv"

NEW_END = pd.Timestamp("2026-08-31 23:55")


def main() -> int:
    if not SRC.exists():
        print(f"❌ 本物の5分足が無い: {SRC}")
        return 1
    d = pd.read_csv(SRC, parse_dates=["timestamp"])
    print(f"本物の5分足: {d['timestamp'].min()} 〜 {d['timestamp'].max()} ／ {len(d)} 行")

    # B) 同じ末（比べる相手）＝そのまま写す
    same = HERE / "five_min_same.csv"
    d.to_csv(same, index=False)
    print(f"作った B: {same.name} ／ 末 {d['timestamp'].max()}")

    # A) 採点窓より先まで取り足した控え
    last = d.iloc[-1]
    idx = pd.date_range(pd.Timestamp(last["timestamp"]) + pd.Timedelta("5min"),
                        NEW_END, freq="5min")
    add = pd.DataFrame({
        "timestamp": idx,
        "open": float(last["close"]), "high": float(last["close"]),
        "low": float(last["close"]), "close": float(last["close"]),
        "volume": 0.0,
    })
    ext = pd.concat([d, add], ignore_index=True)
    out = HERE / "five_min_extended.csv"
    ext.to_csv(out, index=False)
    print(f"作った A: {out.name} ／ 末 {ext['timestamp'].max()} ／ {len(ext)} 行"
          f"（足した行 {len(add)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
