"""B3＝段2b の json（rg5_uptrend の not）が、実行器の検査を本当に通るかを走らせて確かめる。"""
import json
import sys

sys.path.insert(0, "scripts/priority_rebuild")
import numpy as np                      # noqa: E402
import engine_tuner_exec as ex          # noqa: E402
import engine_tuner_gen as g            # noqa: E402


def make_build():
    rng = np.random.default_rng([7, 1, 0])
    lm, _w = g.load_limits()
    pool, tfs, _ = g.material_pool()
    table = g.load_signal_table()
    bd, _draw = g.sample_regime_build(rng, lm, pool, tfs, table, name="range", order_n=0)
    return bd


def try_checks(tag, bd):
    bd = g.strip_marks(bd)
    rg = {"name": "range", "entry_col": bd["entry"]["out_col"], "build": bd}
    out = []
    try:
        legacy = []
        ex._walk_build_tree(bd["entry"]["tree"], "build", f"{tag}/G5", legacy)
        out.append("G5 通った")
    except Exception as e:
        out.append(f"G5 で止まった: {type(e).__name__}: {str(e)[:110]}")
    try:
        ex._check_scene_rules(rg, "main")
        out.append("G7 通った")
    except Exception as e:
        out.append(f"G7 で止まった: {type(e).__name__}: {str(e)[:160]}")
    print(f"[{tag}] " + " ／ ".join(out))


base = make_build()
try_checks("段2b なし（いまの束）", base)

# 設計書のとおり＝ not(bool_col, want=true) を all に足す
b_true = json.loads(json.dumps(base))
b_true["entry"]["tree"]["all"].append({"not": {"bool_col": "rg5_uptrend", "want": True}})
try_checks("段2b あり want=true（設計書の形）", b_true)

# 設計書が「書いてはいけない」と言う形＝ want=false を直接
b_false = json.loads(json.dumps(base))
b_false["entry"]["tree"]["all"].append({"bool_col": "rg5_uptrend", "want": False})
try_checks("段2b want=false（設計書が禁じた形）", b_false)

# ★hysteresis の on の中（5つの枠の並び）に入れた場合も試す
b_on = json.loads(json.dumps(base))
b_on["entry"]["tree"]["all"][0]["on"]["all"].append({"not": {"bool_col": "rg5_uptrend", "want": True}})
try_checks("段2b を on の中に入れた場合", b_on)

# ★C（強さの否定）の not を外して、段2b の not だけにした場合＝R8 は満たせるか
b_only = json.loads(json.dumps(base))
on_all = b_only["entry"]["tree"]["all"][0]["on"]["all"]
b_only["entry"]["tree"]["all"][0]["on"]["all"] = [c for c in on_all if "not" not in c]
b_only["entry"]["tree"]["all"][0]["on"]["all"].append({"not": {"bool_col": "rg5_uptrend", "want": True}})
try_checks("C の not を外し、段2b の not だけ", b_only)

print()
print("=== 束の形（段2b あり・先頭2階層）===")
print(json.dumps(b_true["entry"]["tree"], ensure_ascii=False)[:400])
