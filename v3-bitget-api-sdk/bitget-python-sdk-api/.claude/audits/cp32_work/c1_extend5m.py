"""監査 cp32｜Critical 1 を試すための、取り足した5分足の控えを作る。

★本物の5分足（data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv）は1バイトも書き替えない。
★番人が読むのは「ファイルの末尾 8KB」だけ（observe_diag._tail_timestamps）なので、
  控えは末尾だけで足りる。値は最後の終値のまま（期間の判定を試すための偽のデータ）。

作るもの（引数で選ぶ）
  make      ＝cp32_work/five_min_extended.csv（末＝2026-08-31 23:55）
              cp32_work/one_min_like.csv     （末＝同じ・ただしバーの間隔は1分）
  put-data  ＝data/BTCUSDT-5m-cp32test-2026-08-31.csv を置く（T-m を試す）
  put-sub   ＝data/_cp32sub/BTCUSDT-5m-cp32test-2026-08-31.csv を置く（抜け道の試し）
  put-name  ＝data/cp32test-5m-2026-08-31.csv を置く（名前が違う場合の抜け道の試し）
  clean     ＝上の3つを消す（data を元に戻す）
"""
import pathlib
import shutil
import sys

import pandas as pd

SDK = pathlib.Path(__file__).resolve().parent.parent.parent.parent
HERE = pathlib.Path(__file__).resolve().parent
REAL5 = SDK / "data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv"
EXT = HERE / "five_min_extended.csv"
ONEMIN_LIKE = HERE / "one_min_like.csv"
END = pd.Timestamp("2026-08-31 23:55")

PUTS = {
    "put-data": SDK / "data/BTCUSDT-5m-cp32test-2026-08-31.csv",
    "put-sub": SDK / "data/_cp32sub/BTCUSDT-5m-cp32test-2026-08-31.csv",
    "put-name": SDK / "data/cp32test-5m-2026-08-31.csv",
}


def tail_frame(n: int = 500) -> pd.DataFrame:
    """本物の5分足の末尾 n 本だけを読む（全部は読まない）。"""
    head = pd.read_csv(REAL5, nrows=1)
    with open(REAL5, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - 200_000))
        tail = f.read().decode("utf-8", "ignore").splitlines()
    rows = [ln for ln in tail[1:] if ln.count(",") == len(head.columns) - 1]
    df = pd.read_csv(pd.io.common.StringIO("\n".join([",".join(head.columns)] + rows[-n:])),
                     parse_dates=["timestamp"])
    return df


def make() -> None:
    df = tail_frame()
    last = df.iloc[-1]
    idx = pd.date_range(pd.Timestamp(last["timestamp"]) + pd.Timedelta("5min"), END, freq="5min")
    add = pd.DataFrame({"timestamp": idx})
    for c in df.columns:
        if c != "timestamp":
            add[c] = last[c]
    out = pd.concat([df, add], ignore_index=True)
    out.to_csv(EXT, index=False)
    print(f"作った: {EXT.name} ／ {len(out)} 行 ／ 末 {out['timestamp'].iloc[-1]}")
    # 1分足のふりをした控え（バーの間隔だけ1分・末は同じ）＝別枠 F を試す
    idx1 = pd.date_range(END - pd.Timedelta("500min"), END, freq="1min")
    one = pd.DataFrame({"timestamp": idx1})
    for c in df.columns:
        if c != "timestamp":
            one[c] = last[c]
    one.to_csv(ONEMIN_LIKE, index=False)
    print(f"作った: {ONEMIN_LIKE.name} ／ {len(one)} 行 ／ 末 {one['timestamp'].iloc[-1]}（間隔 1分）")


def put(kind: str) -> None:
    dst = PUTS[kind]
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(EXT, dst)
    print(f"置いた: {dst.relative_to(SDK)}")


def clean() -> None:
    for k, p in PUTS.items():
        if p.exists():
            p.unlink()
            print(f"消した: {p.relative_to(SDK)}")
    sub = SDK / "data/_cp32sub"
    if sub.exists() and not any(sub.iterdir()):
        sub.rmdir()
        print("消した: data/_cp32sub")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "make"
    if cmd == "make":
        make()
    elif cmd == "clean":
        clean()
    elif cmd in PUTS:
        put(cmd)
    else:
        raise SystemExit(f"知らない指示: {cmd}")
