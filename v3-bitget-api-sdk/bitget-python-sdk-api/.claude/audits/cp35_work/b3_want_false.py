"""B3（続き）＝壊すプログラム b83（want を false にすると R8 が落ちる）が、本当に鳴るかを確かめる。"""
import json
import sys

sys.path.insert(0, "scripts/priority_rebuild")
import numpy as np                      # noqa: E402
import engine_tuner_exec as ex          # noqa: E402
import engine_tuner_gen as g            # noqa: E402

rng = np.random.default_rng([7, 1, 0])
lm, _w = g.load_limits()
pool, tfs, _ = g.material_pool()
table = g.load_signal_table()
bd0, _d = g.sample_regime_build(rng, lm, pool, tfs, table, name="range", order_n=0)
bd0 = g.strip_marks(bd0)


def check(tag, bd):
    rg = {"name": "range", "entry_col": bd["entry"]["out_col"], "build": bd}
    seen = {"geo": set(), "fams": set(), "tfs": set(), "parts": set(),
            "not": False, "hysteresis": False, "forms": set(), "on_parts": []}
    ex._scene_scan((bd["entry"] or {}).get("tree"), seen)
    try:
        ex._check_scene_rules(rg, "main")
        r = "G7 通った"
    except Exception as e:
        r = f"G7 で止まった: {str(e)[:90]}"
    print(f"[{tag}] 集まった形={sorted(seen['forms'])} → {r}")


# ① いまの束（C の枠が not を持つ）
check("① いまの束（C が not を持つ）", bd0)

# ② C の not を外し、中身（強さの条件）をそのまま置く＝R5 は満たすが not は消える
bd1 = json.loads(json.dumps(bd0))
on = bd1["entry"]["tree"]["all"][0]["on"]["all"]
bd1["entry"]["tree"]["all"][0]["on"]["all"] = [(c["not"] if "not" in c else c) for c in on]
check("② C の not を外した（強さの条件は残す）", bd1)

# ③ ② に、設計書のとおり段2b（want=true）を足す
bd2 = json.loads(json.dumps(bd1))
bd2["entry"]["tree"]["all"][0]["on"]["all"].append({"not": {"bool_col": "rg5_uptrend", "want": True}})
check("③ ② ＋ 段2b want=true（設計書の形）", bd2)

# ④ ② に、b83 が壊す形（want=false）を足す
bd3 = json.loads(json.dumps(bd1))
bd3["entry"]["tree"]["all"][0]["on"]["all"].append({"bool_col": "rg5_uptrend", "want": False})
check("④ ② ＋ 段2b want=false（b83 が壊す形）", bd3)

# ⑤ いまの束（C の not あり）に、want=false の段2b を足す＝実装後に想定される形
bd4 = json.loads(json.dumps(bd0))
bd4["entry"]["tree"]["all"][0]["on"]["all"].append({"bool_col": "rg5_uptrend", "want": False})
check("⑤ いまの束 ＋ 段2b want=false", bd4)
