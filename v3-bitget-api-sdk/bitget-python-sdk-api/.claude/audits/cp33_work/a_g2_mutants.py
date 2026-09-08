#!/usr/bin/env python3
"""監査 cp33 — G2 の「印を照らす口」を5通りに壊して、足した番人が落ちるかを見る。

★本物のファイルは1文字も書き替えない。写しを作業場に作って、その写しを壊す。
★cp32 が H2 でやったのと同じ形（依頼書 §3.4）。
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/enforce_g2_pass.py")
S = SRC.read_text(encoding="utf-8")

# ---- 壊す相手の実物の行（見つからなければ止める＝前提が変わったことが分かる）----
FP_HEAD = '''    if not os.path.exists(PASS):
        print("❌ 検査済みの印が無い（g2_pass.json がまだ書かれていない）")
        return 1'''

FP_MUST = '''    lack = [m for m in MUST if m not in files]
    if lack:
        print(f"❌ 印の対象一覧に必須のファイルが入っていない（一覧を狭めない）: {lack[:3]}")
        return 1'''

FP_CMP = '''    now = fingerprint(files)
    if now != fp:'''

CHK_MUST = '''    lack = [m for m in MUST if m not in files]
    if lack:
        return f"印の対象一覧に必須のファイルが入っていない（一覧を狭めない）: {lack[:3]}"'''

for name, frag in [("FP_HEAD", FP_HEAD), ("FP_MUST", FP_MUST), ("FP_CMP", FP_CMP), ("CHK_MUST", CHK_MUST)]:
    if S.count(frag) != 1:
        sys.exit(f"前提が変わった: {name} が {S.count(frag)} 件（1件のはず）")

MUTANTS = {
    "m1_always0": S.replace(FP_HEAD, '    return 0\n' + FP_HEAD, 1),
    "m2_always1": S.replace(FP_HEAD, '    return 1\n' + FP_HEAD, 1),
    "m3_no_must_all": S.replace(FP_MUST, '    lack = []', 1).replace(CHK_MUST, '    lack = []', 1),
    "m4_prefix8": S.replace(FP_CMP, '    now = fingerprint(files)\n    if now[:8] != fp[:8]:', 1),
    "m5_no_must_only_fp": S.replace(FP_MUST, '    lack = []', 1),
}

print("=" * 72)
print("G2 の印を照らす口＝5通りに壊して、番人が落ちるか（監査 cp33・依頼書 §3.4）")
print("=" * 72)

base = HERE / "m0_intact.py"
base.write_text(S, encoding="utf-8")
r = subprocess.run([sys.executable, str(base), "--selftest"], capture_output=True, text=True)
tail = [l for l in r.stdout.splitlines() if "番人:" in l]
print(f"\n■ 素のまま  rc={r.returncode}  {tail[-1].strip() if tail else ''}")

for name, src in MUTANTS.items():
    p = HERE / f"{name}.py"
    p.write_text(src, encoding="utf-8")
    r = subprocess.run([sys.executable, str(p), "--selftest"], capture_output=True, text=True)
    lines = r.stdout.splitlines()
    ng = [l.strip() for l in lines if l.strip().startswith("❌")]
    tally = [l for l in lines if "番人:" in l]
    verdict = "落ちた（殺した）" if r.returncode != 0 else "★生き残った"
    print(f"\n■ {name}  rc={r.returncode}  → {verdict}")
    print(f"   {tally[-1].strip() if tally else '(集計行なし)'}")
    for l in ng:
        print(f"   落ちた札: {l[:110]}")
    if r.returncode == 0:
        print("   ★この壊し方は、番人が1件も捕まえられていない")
