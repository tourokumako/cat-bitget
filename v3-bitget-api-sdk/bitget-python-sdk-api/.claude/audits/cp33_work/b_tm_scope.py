#!/usr/bin/env python3
"""監査 cp33 — 番人 T-m が見る範囲を、実物の data で試す（依頼書 §3.1・§3.2・§3.3）。

置く控えは4通り。1つ試すたびに消す。★本物の5分足には1文字も触らない。
  ① Bitget 先物の名前（正本より後の末）      → T-m は落ちてはいけない（Major の直し）
  ② Binance Spot の名前（正本より後の末）    → T-m は落ちなければいけない（守りを弱めていない）
  ③ data の下の階層（Binance Spot の名前）   → T-m は落ちなければいけない（別枠 A）
  ④ 末の時刻が読めない（Binance Spot の名前）→ 名前が ❌ に出なければいけない（別枠 B）
"""
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api")
DATA = ROOT / "data"
OBS = ROOT / "scripts" / "priority_rebuild" / "observe_diag.py"
LATER = "2026-08-31 23:55:00"
GOOD = "timestamp,open,high,low,close,volume\n" + \
       "\n".join(f"2026-08-31 23:{m:02d}:00,1,1,1,1,1" for m in (35, 40, 45, 50, 55)) + "\n"
BAD = "timestamp,open,high,low,close,volume\nこれは時刻ではない,1,1,1,1,1\n"

CASES = [
    ("① Bitget 先物の名前", DATA / "BTCUSDT-5m-bitget-cp33test-2026-08-31.csv", GOOD, "落ちてはいけない"),
    ("② Binance Spot の名前", DATA / "BTCUSDT-5m-cp33test-2026-08-31.csv", GOOD, "落ちなければいけない"),
    ("③ 下の階層", DATA / "_cp33sub" / "BTCUSDT-5m-cp33test-2026-08-31.csv", GOOD, "落ちなければいけない"),
    ("④ 末の時刻が読めない", DATA / "BTCUSDT-5m-cp33edge-badtail.csv", BAD, "名前が ❌ に出なければいけない"),
]


def run():
    r = subprocess.run([sys.executable, str(OBS), "--selftest-insp5"],
                       capture_output=True, text=True, cwd=str(ROOT))
    ng = [l.strip() for l in (r.stdout + r.stderr).splitlines() if l.strip().startswith("❌")]
    return r.returncode, ng


print("=" * 76)
print("番人 T-m が見る範囲（監査 cp33・依頼書 §3.1〜§3.3）")
print("=" * 76)
rc0, ng0 = run()
print(f"\n■ 素のまま（何も置かない）  rc={rc0}  ❌ {len(ng0)} 件")
for l in ng0:
    print("   " + l[:150])

before = sorted(p.name for p in DATA.iterdir())
for name, path, body, want in CASES:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    rc, ng = run()
    print(f"\n■ {name}  置いた: {path.relative_to(DATA)}")
    print(f"   期待＝{want}  ／ 実測 rc={rc}・❌ {len(ng)} 件")
    for l in ng:
        print("   " + l[:170])
    # 片づけ
    if path.parent != DATA:
        shutil.rmtree(path.parent, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)

after = sorted(p.name for p in DATA.iterdir())
print(f"\n■ 片づけの確認  data の中身 前 {len(before)} 件 → 後 {len(after)} 件 ／ "
      f"差分 {set(before) ^ set(after) or 'なし'}")
