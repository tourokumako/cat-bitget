"""A1-b＝法則ファイルを書き替えると、組まれる束が本当に変わるかを実測する（監査 cp35・読み取り専用）。
★本物の regime_laws.json は書き替えない。作業場に写しを作り、ex.LAWS_PATH を写しへ向ける。"""
import json
import pathlib
import sys

sys.path.insert(0, "scripts/priority_rebuild")
import numpy as np                      # noqa: E402
import engine_tuner_exec as ex          # noqa: E402
import engine_tuner_gen as g            # noqa: E402

WORK = pathlib.Path(".claude/audits/cp35_work")
ORIG = pathlib.Path(".claude/ratchet/regime_laws.json")


def build_draw(order_n=0, seed=7):
    rng = np.random.default_rng([seed, 1, 0])
    lm, _w = g.load_limits()
    pool, tfs, _ = g.material_pool()
    table = g.load_signal_table()
    _bd, draw = g.sample_regime_build(rng, lm, pool, tfs, table, name="range", order_n=order_n)
    return draw


def use_laws(path):
    ex.LAWS_PATH = pathlib.Path(path)
    ex._REGIME_LAWS = None
    ex._REGIME_LAW_COUNTS = None


def summary(d):
    return {"A(帯の幅)": d.get("A", {}).get("geo"),
            "B(帯)": d.get("B", {}).get("col"),
            "C(強さの否定)": d.get("C", {}).get("col"),
            "G(3枠目)": d.get("G", {}).get("col"),
            "F(持続)": (d.get("F") or {}).get("形"),
            "形": d["法則から組んだ"]["形"],
            "数える法則": d["法則から組んだ"]["数える法則"]}


def variant(name, mutate):
    body = json.loads(ORIG.read_text(encoding="utf-8"))
    mutate(body)
    p = WORK / f"laws_{name}.json"
    p.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    use_laws(p)
    try:
        return summary(build_draw())
    except Exception as e:
        return {"組めない": f"{type(e).__name__}: {str(e)[:120]}"}


def law(body, no):
    for l in body["法則"]:
        if l["番号"] == no:
            return l
    raise SystemExit(f"法則 {no} が無い")


use_laws(ORIG)
base = summary(build_draw())
print("【0】正規の法則 :", json.dumps(base, ensure_ascii=False))


def m1(b):
    j = law(b, "R5")["機械が読む判定"]["数える部品"]
    j["family"] = [f for f in j["family"] if f != "DI差"]
    j["側"].pop("DI差", None)
print("【1】R5 から DI差 を消す :", json.dumps(variant("r5_drop_di", m1), ensure_ascii=False))


def m2(b):
    j = law(b, "R6")["機械が読む判定"]["数える部品"]
    j["family"] = ["ATR%"]
    j["側"] = {"ATR%": "below"}
print("【2】R6 を ATR% だけにする :", json.dumps(variant("r6_only_atr", m2), ensure_ascii=False))


def m3(b):
    j = law(b, "R7")["機械が読む判定"]["数える部品"]
    j["geo"] = ["帯内位置%"]
    j["側"] = {"帯内位置%": "above"}
print("【3】R7 の geo を 帯内位置% に変える :", json.dumps(variant("r7_geo", m3), ensure_ascii=False))


def m4(b):
    law(b, "R4")["機械が読む判定"]["掛かる場面"] = ["uptrend"]
print("【4】R4（streak）を range から外す :", json.dumps(variant("r4_off", m4), ensure_ascii=False))


def m5(b):
    for no in ("R1", "R3"):
        j = law(b, no)["機械が読む判定"]["数える部品"]
        j["系統"] = ["ボラ"]
print("【5】R1・R3 の系統を ボラ に変える :", json.dumps(variant("r1r3_vol", m5), ensure_ascii=False))
