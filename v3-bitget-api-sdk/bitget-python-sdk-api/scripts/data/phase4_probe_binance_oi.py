"""Binance Vision futures metrics アーカイブ（OI 含む）の取得可否を probe（E28 Step2）。

OI は futures の概念 → Binance USDT-M futures の daily metrics アーカイブを確認。
  URL: https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-YYYY-MM-DD.zip
  期待列: create_time, symbol, sum_open_interest, sum_open_interest_value, ...（5分粒度）

目的: 2021-2024 まで遡れるか・列・粒度を確認してから downloader を書く（無駄打ち防止）。
無認証 public archive のみ。
"""
from __future__ import annotations
import io
import urllib.request
import zipfile

BASE = "https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT"
DATES = ["2021-01-01", "2021-06-01", "2022-01-01", "2023-01-01",
         "2023-06-01", "2024-01-01", "2024-06-01", "2024-12-01"]


def probe(d: str):
    url = f"{BASE}/BTCUSDT-metrics-{d}.zip"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "oi-probe"})
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read()
        z = zipfile.ZipFile(io.BytesIO(raw))
        name = z.namelist()[0]
        with z.open(name) as f:
            text = f.read().decode(errors="replace")
        lines = text.splitlines()
        print(f"✅ {d}: {len(raw):,} bytes / {name} / 行数 {len(lines)-1}")
        print(f"   header: {lines[0]}")
        if len(lines) > 1:
            print(f"   row1:   {lines[1]}")
        if len(lines) > 2:
            print(f"   row2:   {lines[2]}")
    except urllib.error.HTTPError as e:
        print(f"❌ {d}: HTTP {e.code}（このアーカイブに無い）")
    except Exception as e:
        print(f"❌ {d}: {type(e).__name__} {e}")


def main():
    print("=" * 70)
    print("[E28 Step2] Binance futures metrics(OI)アーカイブ 取得可否 probe")
    print(f"  {BASE}")
    print("=" * 70)
    for d in DATES:
        probe(d)
    print("\n→ ✅ が並べば daily metrics で OI 履歴取得可。最古の ✅ がカバー開始。")


if __name__ == "__main__":
    main()
