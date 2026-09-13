#!/usr/bin/env python3
"""scan_bundles.py — 写しのエンジンを直接 呼び、場面の判定の束を案の番号 0..N-1 で組んで数える（監査 cp36）。

使い方: python3 scan_bundles.py <mirror|mirror_old> <N> <出力 json>
  ・sample_regime_build(limits, pool, tfs, table, order_n=n) を直接 呼ぶ（乱数を渡す口は無い）
  ・数えるもの＝B/C/G の時間足・C の材料に前処理（abs）が付くか・B/C/G の指標が §2.2 の元データの中か
    ・同じ番号で2回 組んで同じか（build のハッシュ値）・組めなかった番号と理由
本物のファイルは読むだけ。写しの中のエンジンだけを import する。
"""
import hashlib
import json
import pathlib
import sys

W = pathlib.Path(__file__).resolve().parent
which, N, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
PR = W / which / "v3-bitget-api-sdk" / "bitget-python-sdk-api" / "scripts" / "priority_rebuild"
sys.path.insert(0, str(PR))
import engine_tuner_gen as g  # noqa: E402

tbl = g.load_signal_table()
pool, tfs, _ = g.material_pool()
lm, _w = g.load_limits()
lm = g.resolve_hold_range(lm, "e38")
try:
    sc = {k: g.stage_candidates(k) for k in ("stage1", "stage2a", "stage2c")}
except Exception as e:  # noqa: BLE001
    sc = {}
    print("stage_candidates を読めない:", e)


def h(o):
    return hashlib.sha256(json.dumps(g.strip_marks(o), sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def in_src(stage, fam):
    if not sc or fam is None:
        return None
    s = sc[stage]
    import indicator_reference_diag as iref
    return (fam in s["families"]) or (iref.FAMILY_LINEAGE.get(fam, {}).get("k") in s["lineages"])


rows = {}
fail = {}
for n in range(N):
    try:
        b1, d1 = g.sample_regime_build(lm, pool, tfs, tbl, order_n=n)
        b2, d2 = g.sample_regime_build(lm, pool, tfs, tbl, order_n=n)
    except g.SampleError as e:
        fail[n] = str(e)[:140]
        continue
    hy = b1["entry"]["tree"]["all"][0]
    on = hy["on"]["all"]
    # C は not で包まれた level（材料に pre が在るか）
    c_mat = None
    for c in on:
        if isinstance(c, dict) and "not" in c and isinstance(c["not"], dict) and c["not"].get("role") == d1.get("C", {}).get("役割", d1.get("C", {}).get("role", "env")):
            c_mat = c["not"]["material"][0]
    if c_mat is None:
        for c in on:
            if isinstance(c, dict) and "not" in c and isinstance(c["not"], dict) and "material" in c["not"]:
                c_mat = c["not"]["material"][0]
    rows[n] = {
        "same_twice": h(b1) == h(b2),
        "build_hash": h(b1),
        "A": d1.get("A"), "B": {k: d1["B"].get(k) for k in ("col", "種類", "時間足", "rank")},
        "B_side": next((c.get("side") for c in on if isinstance(c, dict) and c.get("role") == d1["B"].get("role", "location") and c.get("material") and "geo" not in c["material"][0]), None),
        "C": {k: d1["C"].get(k) for k in ("col", "種類", "時間足", "rank", "法則の側", "not で包む側")},
        "C_pre": (c_mat or {}).get("pre"),
        "G": {k: d1["G"].get(k) for k in ("col", "種類", "時間足", "rank", "側")} if d1.get("G") else None,
        "F": d1.get("F"), "D": d1.get("D"),
        "hyst_n": hy["value"].get("n"),
        "B_in_src": in_src("stage1", d1["B"].get("種類")),
        "C_in_src": in_src("stage2a", d1["C"].get("種類")),
        "G_in_src": in_src("stage2c", d1["G"].get("種類")) if d1.get("G") else None,
        "stages": [(s["stage"], s.get("n_candidates"), s.get("keep")) for s in d1.get("stages", [])],
        "laws": d1.get("法則から組んだ"),
    }

# 集計
from collections import Counter  # noqa: E402
tf_b = Counter(r["B"]["時間足"] for r in rows.values())
tf_c = Counter(r["C"]["時間足"] for r in rows.values())
tf_g = Counter((r["G"] or {}).get("時間足") for r in rows.values())
summary = {
    "which": which, "N": N, "built": len(rows), "failed": len(fail),
    "same_twice_all": all(r["same_twice"] for r in rows.values()),
    "tf_B": dict(tf_b), "tf_C": dict(tf_c), "tf_G": dict(tf_g),
    "C_pre_abs_count": sum(1 for r in rows.values() if (r["C_pre"] or {}).get("op") == "abs"),
    "C_signed_fams_no_abs": sorted({r["C"]["種類"] for r in rows.values()
                                    if r["C"]["種類"] in ("DI差", "MACDヒスト%", "EMA傾き") and (r["C_pre"] or {}).get("op") != "abs"}),
    "B_not_in_src": sorted({r["B"]["種類"] for r in rows.values() if r["B_in_src"] is False}),
    "C_not_in_src": sorted({r["C"]["種類"] for r in rows.values() if r["C_in_src"] is False}),
    "G_not_in_src": sorted({(r["G"] or {}).get("種類") for r in rows.values() if r["G_in_src"] is False}),
    "B_sides": dict(Counter(r["B_side"] for r in rows.values())),
    "F_n": dict(Counter((r["F"] or {}).get("本数") for r in rows.values())),
    "hyst_n": dict(Counter(r["hyst_n"] for r in rows.values())),
    "fails": fail,
}
pathlib.Path(out).write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
