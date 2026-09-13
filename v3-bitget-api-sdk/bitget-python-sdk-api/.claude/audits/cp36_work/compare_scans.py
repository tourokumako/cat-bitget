#!/usr/bin/env python3
"""compare_scans.py — scan_bundles.py の出力どうしを欄ごとに突き合わせる（読み取りだけ）。

使い方: python3 compare_scans.py <土台 json> <比べる json> [<比べる json> ...]
  ・案の番号ごとに A/B/C/G/F/D/hyst_n/B_side/build_hash/stages を比べ、変わった欄を出す
  ・組めなかった番号（fails）も出す
"""
import json
import pathlib
import sys

FIELDS = ("A", "B", "B_side", "C", "C_pre", "G", "F", "D", "hyst_n", "stages", "laws", "build_hash")


def load(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


base = load(sys.argv[1])
for other in sys.argv[2:]:
    o = load(other)
    name = pathlib.Path(other).name
    rows_b, rows_o = base["rows"], o["rows"]
    ns = sorted(set(rows_o) | set(rows_b), key=int)
    ns = [n for n in ns if n in rows_o or n in o["summary"]["fails"]]
    changed = {}
    for n in ns:
        if n not in rows_o:
            changed[n] = {"組めない": o["summary"]["fails"].get(n)}
            continue
        if n not in rows_b:
            changed[n] = {"土台に無い": True}
            continue
        d = {}
        for f in FIELDS:
            if rows_b[n].get(f) != rows_o[n].get(f):
                d[f] = {"前": rows_b[n].get(f), "後": rows_o[n].get(f)}
        if d:
            changed[n] = d
    n_total = len(ns)
    n_ch = len(changed)
    fields_ch = sorted({f for v in changed.values() for f in v if f not in ("組めない", "土台に無い")})
    fails = len(o["summary"]["fails"])
    print(f"== {name}: 比べた番号 {n_total} 本 ／ 変わった {n_ch} 本 ／ 組めない {fails} 本 ／ 変わった欄 {fields_ch}")
    for n in list(changed)[:3]:
        v = changed[n]
        if "組めない" in v:
            print(f"   案 {n}: 組めない: {str(v['組めない'])[:150]}")
        else:
            for f, pv in v.items():
                if f in ("stages", "laws", "build_hash"):
                    print(f"   案 {n} {f}: 前={str(pv['前'])[:110]} → 後={str(pv['後'])[:110]}")
                else:
                    print(f"   案 {n} {f}: 前={pv['前']} → 後={pv['後']}")
