"""A1-b（続き）＝法則を1件ずつ書き替えて、組まれる束が変わるかを全件で見る（監査 cp35）。
完成の条件 AUDIT-1「法則を1件 変えると、組まれる束が変わる（R1〜R10 の10件）」が、
いまの実装で満たせるかを測る。"""
import json
import pathlib
import sys

sys.path.insert(0, "scripts/priority_rebuild")
import numpy as np                      # noqa: E402
import engine_tuner_exec as ex          # noqa: E402
import engine_tuner_gen as g            # noqa: E402

WORK = pathlib.Path(".claude/audits/cp35_work")
ORIG = pathlib.Path(".claude/ratchet/regime_laws.json")


def build_draw():
    rng = np.random.default_rng([7, 1, 0])
    lm, _w = g.load_limits()
    pool, tfs, _ = g.material_pool()
    table = g.load_signal_table()
    _bd, draw = g.sample_regime_build(rng, lm, pool, tfs, table, name="range", order_n=0)
    return draw


def use_laws(path):
    ex.LAWS_PATH = pathlib.Path(path)
    ex._REGIME_LAWS = None
    ex._REGIME_LAW_COUNTS = None


def key(d):
    return json.dumps({"A": d.get("A", {}).get("geo"), "B": d.get("B", {}).get("col"),
                       "C": d.get("C", {}).get("col"), "G": d.get("G", {}).get("col"),
                       "F": (d.get("F") or {}).get("本数"), "形": d["法則から組んだ"]["形"]},
                      ensure_ascii=False)


def law(body, no):
    for l in body["法則"]:
        if l["番号"] == no:
            return l
    return None


use_laws(ORIG)
base = key(build_draw())
print("基準 :", base)
print()
print("| 法則 | 掛かる場面から外したとき | 束は変わったか |")
print("|---|---|---|")
for no in ["C1", "C4", "C6", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R10"]:
    body = json.loads(ORIG.read_text(encoding="utf-8"))
    l = law(body, no)
    if l is None or "機械が読む判定" not in l:
        print(f"| {no} | （機械が読む判定を持たない） | — |")
        continue
    l["機械が読む判定"]["掛かる場面"] = ["uptrend"]      # range から外す
    p = WORK / f"laws_off_{no}.json"
    p.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    use_laws(p)
    try:
        k = key(build_draw())
        changed = "**変わった**" if k != base else "変わらない"
        note = k if k != base else ""
    except Exception as e:
        changed = "**組めなくなった**"
        note = f"{type(e).__name__}: {str(e)[:70]}"
    print(f"| {no} | {note or '同じ束'} | {changed} |")
