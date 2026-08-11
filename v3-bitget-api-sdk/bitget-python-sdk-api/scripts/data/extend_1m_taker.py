"""1分足（taker 列つき）の前に、足りない月をつないで新しい正本を作る（§8.2.1.1 の④＝別名で保存）。

なぜ要るか（2026-08-11・マイルストーン①のフロー 段7 の 7-1）:
  engine_tuner が使う時間足を 1分足まで広げる（要件 R15）。ところが 1分足の元データは
  2024-04-01 から しか無く、値決め窓は 2024-03-01 から始まる＝最初の1ヶ月が欠けていた（実測）。
  `download_binance_1m_taker.py 2024-03 2024-04` で欠けた月を取り、この道具でつなぐ。

やること（§8.2.1.1 の4段のうち ②③④）:
  ② つなぐ（時刻で並べ直し・重複は先に在る方を残す）
  ③ 連続性の確認（1分グリッドの欠け・重複・境目の値段の段差）
  ④ 別名で保存する（元のファイルは消さない・上書きしない）

使い方:
  python3 scripts/data/extend_1m_taker.py <古い方のCSV> <新しい方のCSV> [...]
  例) python3 scripts/data/extend_1m_taker.py \
        data/BTCUSDT-1m-binance-taker-2024-03-01_2024-03-31.csv \
        data/BTCUSDT-1m-binance-taker-2024-04-01_2026-06-30.csv

出力: data/BTCUSDT-1m-binance-taker-<先頭日>_<末尾日>.csv（既に在れば止まる＝上書きしない）
★この道具は売買しない・採点しない・値も決めない（データを作るだけ）。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]        # bitget-python-sdk-api/（download_binance_1m_taker と同じ）
OUT_DIR = REPO / "data"
STEP_WARN_PCT = 0.5   # 境目の段差の報告の線（別系列の混入を疑う）
COLS = ["timestamp", "open", "high", "low", "close", "volume", "taker_buy_base"]


def _load(p: Path) -> pd.DataFrame:
    df = pd.read_csv(p)
    miss = [c for c in COLS if c not in df.columns]
    if miss:
        raise SystemExit(f"[止めた] {p.name} に無い列がある: {miss}")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df[COLS].sort_values("timestamp")


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("使い方: python3 scripts/data/extend_1m_taker.py <CSV> <CSV> [...]")
    parts = []
    for a in sys.argv[1:]:
        p = Path(a) if Path(a).is_absolute() else REPO / a
        df = _load(p)
        print(f"  [読む] {p.name}: {len(df):,} 行 / {df['timestamp'].iloc[0]} 〜 {df['timestamp'].iloc[-1]}")
        parts.append(df)

    both = pd.concat(parts, ignore_index=True).sort_values("timestamp")
    dup = int(both["timestamp"].duplicated().sum())
    both = both.drop_duplicates(subset="timestamp", keep="first").reset_index(drop=True)

    t = both["timestamp"]
    full = pd.date_range(t.iloc[0], t.iloc[-1], freq="1min")
    missing = len(full) - len(t)
    print(f"  [連続性] 行 {len(both):,} / 重複 {dup}（先に在る方を残した）/ 1分グリッドの欠け {missing}")
    if missing:
        have = set(t)
        gaps = [x for x in full if x not in have]
        print(f"     欠けの先頭10件: {[str(x) for x in gaps[:10]]}")

    # 境目の段差（つないだ所で別系列が混ざっていないか）＝前の足の終値 → 次の足の始値
    step = (pd.to_numeric(both["open"]).shift(-1) / pd.to_numeric(both["close"]) - 1).abs() * 100
    big = step[step > STEP_WARN_PCT]
    print(f"  [段差] 前の終値→次の始値 が {STEP_WARN_PCT}% 超 = {len(big)} 件"
          f"（最大 {step.max():.4f}% ／ {both['timestamp'].iloc[int(step.idxmax())]}）")
    for i in big.index[:5]:
        print(f"     ・{both['timestamp'].iloc[i]} {both['close'].iloc[i]} → {both['open'].iloc[i + 1]}"
              f"（{step.iloc[i]:.4f}%）")

    out = OUT_DIR / (f"BTCUSDT-1m-binance-taker-{t.iloc[0]:%Y-%m-%d}_{t.iloc[-1]:%Y-%m-%d}.csv")
    if out.exists():
        raise SystemExit(f"[止めた] 同じ名前のファイルが在る（上書きしない）: {out}")
    both.to_csv(out, index=False)
    print(f"\n→ {out}\n   {len(both):,} bars / {t.iloc[0]} 〜 {t.iloc[-1]}")


if __name__ == "__main__":
    main()
