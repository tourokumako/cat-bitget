#!/usr/bin/env python3
"""r9_compare.py — regime_r9_diag.py の出力（[機械が読む形] の json）どうしを、束の欄ごとに比べる（読み取りだけ）。

使い方: python3 r9_compare.py <出力ファイル> [<出力ファイル> ...]
  ・各ファイルの最後の json 行を読み、R9_n ごとに 注（A/B/C/G/F/D・stages・order_n）と ①③ を出す
  ・2つ目以降は1つ目と比べて、違う欄を出す
"""
import json
import pathlib
import sys

KEYS = ("order_n", "A", "B", "C", "G", "F", "D")


def parse(p):
    lines = pathlib.Path(p).read_text(encoding="utf-8").splitlines()
    js = [ln for ln in lines if ln.startswith("[{")]
    rows = json.loads(js[-1]) if js else []
    out = {}
    for r in rows:
        name = r.get("判定")
        note = r.get("注")
        try:
            d = json.loads(note) if isinstance(note, str) else (note or {})
        except json.JSONDecodeError:
            d = {}
        out[name] = {"①": round(float(r.get("①時間の割合", 0)), 4),
                     "③24": round(float(r.get("③実はトレンド(先24本)", 0)), 4),
                     "③288": round(float(r.get("③実はトレンド(先288本)", 0)), 4),
                     **{k: d.get(k) for k in KEYS},
                     "stages": [(s.get("stage"), s.get("n_candidates")) for s in d.get("stages", [])]}
    return out


base = None
for p in sys.argv[1:]:
    rows = parse(p)
    print(f"== {pathlib.Path(p).name}: 判定 {list(rows)}")
    for name, r in rows.items():
        if name.startswith("R9"):
            print(f"  {name}: ①{r['①']} ③24={r['③24']} ③288={r['③288']} order_n={r['order_n']} "
                  f"B={(r['B'] or {}).get('col')} C={(r['C'] or {}).get('col')} G={(r['G'] or {}).get('col')} "
                  f"A={(r['A'] or {}).get('geo')}/{(r['A'] or {}).get('側')} F={(r['F'] or {}).get('本数')} D={(r['D'] or {}).get('真偽の列')} stages={r['stages']}")
    if base is None:
        base = rows
        continue
    diff = []
    for name in rows:
        if name not in base:
            diff.append((name, "土台に無い"))
            continue
        for k in ("①", "③24", "③288", *KEYS, "stages"):
            if base[name].get(k) != rows[name].get(k):
                diff.append((name, k, base[name].get(k), rows[name].get(k)))
    print("  土台との違い:", diff if diff else "なし")
