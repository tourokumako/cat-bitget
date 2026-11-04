#!/usr/bin/env python3
"""CP101 の修正の案を、メモリの上の写しで試す（本物には1バイトも書かない）。

①枝型3本に 向き を足す ②売り方 S2〜S5 をオフにする。読む口・--check-sources・T44 の本体が通るかを見る。
③line_of の探す文字を変えたときに、S1 の数の出どころが値の在る行を指すかを見る。
"""
import copy, json, pathlib, sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
sys.path.insert(0, str(ROOT / ".claude" / "tools"))
import check_one_path as cop  # noqa: E402

laws, r = cop._laws_reader()


def row(d, no):
    return next(x for x in d["法則の行"] if x["番号"] == no)


def run(label, d):
    try:
        rd = laws.Laws(d, reader=r.ind)
        why, same, _u, _s = cop._s1_diff(rd)
        ng = rd.check_sources()
        print(f"{label}: 読める S1={same}/12 T44の違い={why} check_sources={ng} 行数={len(rd.rows())}")
        return rd
    except SystemExit as e:
        print(f"{label}: 止まった {e}")


d = copy.deepcopy(r.data)
for no in ("枝型-TP_PCT", "枝型-BEEXIT", "枝型-BESTALE", "枝型-REVERSE_IND"):
    row(d, no)["値段の決め方"]["向き"] = "利の側"
run("向きを足す", d)
d = copy.deepcopy(r.data)
for s in ("S2", "S3", "S4", "S5"):
    row(d, "売り方" + s)["オン/オフと注意"] = {"状態": "オフ"}
rd = run("S2〜S5 をオフ", d)
if rd:
    print("  文書の差の行:", [ln[:40] for ln in rd.doc().splitlines() if ln.startswith("| 売り方")])
    print("  S2〜S5 を指す枝の行:", [x["番号"] for x in d["法則の行"] if set(x.get("どの売り方用か") or []) & {"売り方S2", "売り方S3", "売り方S4", "売り方S5"}])

print("=== 枝型の 建値から% の行と、engine_tuner_gen の side_sign")
g = (cop.SCRIPTS / "engine_tuner_gen.py").read_text(encoding="utf-8").splitlines()
for i, ln in enumerate(g, 1):
    if 'mk("TP_PCT"' in ln or 'mk("SL_PCT"' in ln or '"side_sign"' in ln:
        print(f"  gen:{i} {ln.strip()[:130]}")

print("=== line_of の探す文字を変えたときの行")
path = cop.SCRIPTS / "recipes" / "identity_s1_legacy.json"
lines = path.read_text(encoding="utf-8").splitlines()


def line_of(needle, start=0):
    for i, ln in enumerate(lines, 1):
        if i > start and needle in ln:
            return i
    return None


for needle in ('"down_window_hours"', '"max_age_hours"'):
    n = line_of(needle)
    print(f"  {needle} → :{n} {lines[n-1].strip()[:70]}  ／引用符なしの今の探し方 → :{line_of(needle.strip(chr(34)))}")
for name in ("FASTCUT", "V59DOWN", "V59FLAT", "TCTP"):
    start = line_of(f'"name": "{name}"')
    now, new = line_of('"pct"', start), line_of('"k"', start)
    print(f"  {name}: 枝の行 :{start} 今の '\"pct\"' → :{now}／案の '\"k\"' → :{new} {lines[new-1].strip()[:70]}")
for ln_no in (46, 47, 48, 49, 50, 51, 52, 69, 70, 78, 79):
    print(f"  :{ln_no} {lines[ln_no-1].strip()[:110]}")
