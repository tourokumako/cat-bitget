"""
Phase 3+4 グリッドサーチ: TP_PCT × P4_MAX_ADDS / P2_MAX_ADDS
Usage:
  .venv/bin/python3 tools/grid_search.py <candles_csv>            # TP × P4 グリッド
  .venv/bin/python3 tools/grid_search.py <candles_csv> --p2       # P2 グリッド（TP/P4固定）
  .venv/bin/python3 tools/grid_search.py <candles_csv> --p23-tp   # P23_TP_PCT グリッド（他固定）
  .venv/bin/python3 tools/grid_search.py <candles_csv> --p22-tp   # P22_TP_PCT グリッド（他固定）
  .venv/bin/python3 tools/grid_search.py <candles_csv> --p24-tp   # P24_TP_PCT グリッド（他固定）
"""
import json
import re
import subprocess
import sys
import copy
from pathlib import Path
from itertools import product

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "cat_params_v9.json"
REPLAY_SCRIPT = BASE_DIR / "runner" / "replay_csv.py"

# TP × P4 グリッド
TP_PCTS   = [0.003, 0.0035, 0.004, 0.005, 0.006, 0.007]
P4_MAXES  = [1, 2, 3, 4, 5]

# P2 グリッド（TP=0.005 / P4=5 固定）
FIXED_TP  = 0.005
FIXED_P4  = 5
P2_MAXES  = [1, 2, 3, 4, 5]

# SHORT TP グリッド（LONG_TP=0.005 / P2=P4=5固定 / SHORT adds上限=5）
SHORT_TP_PCTS = [0.003, 0.0035, 0.004, 0.005, 0.006, 0.007]


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def run_replay(candles_csv: str) -> str:
    result = subprocess.run(
        [sys.executable, str(REPLAY_SCRIPT), candles_csv],
        capture_output=True, text=True
    )
    return result.stdout + result.stderr


def parse_output(output: str) -> dict:
    d = {}

    m = re.search(r"NET合計:\s+\$([+\-]?\d+\.\d+)\s+\(\$([+\-]?\d+\.\d+)/day\)", output)
    if m:
        d["net_total"] = float(m.group(1))
        d["net_per_day"] = float(m.group(2))

    m = re.search(r"総トレード数:\s+(\d+)", output)
    if m:
        d["trades"] = int(m.group(1))

    # Priority別: 例 "P2-LONG       129  $ +733.46    67%"
    for pri in ["P2-LONG", "P4-LONG", "P22-SHORT", "P23-SHORT", "P24-SHORT"]:
        pat = rf"{re.escape(pri)}\s+(\d+)\s+\$\s*([+\-]?\d+\.\d+)\s+(\d+)%"
        m = re.search(pat, output)
        if m:
            key = pri.replace("-", "_").lower()
            d[f"{key}_count"] = int(m.group(1))
            d[f"{key}_net"]   = float(m.group(2))
            d[f"{key}_tp"]    = int(m.group(3))

    return d


def fmt(val, width=9):
    if val is None:
        return " " * width
    return f"${val:+.0f}".rjust(width)


def run_p2_grid(candles_csv, original_cfg):
    results = {}
    total = len(P2_MAXES)
    print(f"  TP={FIXED_TP} 固定 / P4max={FIXED_P4} 固定 / P2max を [{', '.join(map(str, P2_MAXES))}] で検証\n")

    try:
        for i, p2m in enumerate(P2_MAXES, 1):
            print(f"\n[{i:02d}/{total}] P2max={p2m} ...", flush=True)
            cfg = copy.deepcopy(original_cfg)
            cfg["LONG_TP_PCT"]  = FIXED_TP
            cfg["SHORT_TP_PCT"] = FIXED_TP
            adds = dict(cfg["MAX_ADDS_BY_PRIORITY"])
            adds["2"] = p2m
            adds["4"] = FIXED_P4
            cfg["MAX_ADDS_BY_PRIORITY"] = adds
            save_config(cfg)

            out = run_replay(candles_csv)
            parsed = parse_output(out)
            results[p2m] = parsed

            net = parsed.get("net_total", float("nan"))
            trd = parsed.get("trades", "?")
            print(f"  → NET ${net:+.2f} / {trd}trades", flush=True)
    finally:
        save_config(original_cfg)
        print("\n[config restored]", flush=True)

    cur_p2 = original_cfg.get("MAX_ADDS_BY_PRIORITY", {}).get("2", 4)

    print("\n" + "=" * 60)
    print("  P2 MAX_ADDS グリッド結果（TP=0.005 / P4max=5 固定）")
    print("=" * 60)
    print(f"  {'P2max':>6}  {'trades':>6}  {'NET':>10}  {'NET/day':>8}  {'P2 NET':>9}  {'P4 NET':>9}")
    print("-" * 60)
    for p2m in P2_MAXES:
        d = results.get(p2m, {})
        cur = " ◀ current" if p2m == cur_p2 else ""
        print(
            f"  {p2m:>6}  {d.get('trades', '?'):>6}  "
            f"${d.get('net_total', 0):>9.2f}  "
            f"${d.get('net_per_day', 0):>7.1f}  "
            f"${d.get('p2_long_net', 0):>8.2f}  "
            f"${d.get('p4_long_net', 0):>8.2f}"
            f"{cur}"
        )

    best_p2 = max(results.items(), key=lambda x: x[1].get("net_total", float("-inf")))
    bp, bd = best_p2
    print(f"\n★ 最良: P2max={bp}  NET ${bd.get('net_total', 0):+.2f}  ({bd.get('net_per_day', 0):+.1f}/day)")


def run_short_tp_grid(candles_csv, original_cfg):
    results = {}
    total = len(SHORT_TP_PCTS)
    print(f"  LONG_TP=0.005固定 / SHORT adds上限=5 / SHORT_TP_PCT を {SHORT_TP_PCTS} で検証\n")

    cur_short_tp = original_cfg.get("SHORT_TP_PCT", 0.005)

    try:
        for i, stp in enumerate(SHORT_TP_PCTS, 1):
            print(f"\n[{i:02d}/{total}] SHORT_TP={stp:.4f} ...", flush=True)
            cfg = copy.deepcopy(original_cfg)
            cfg["LONG_TP_PCT"]  = 0.005
            cfg["SHORT_TP_PCT"] = stp
            adds = dict(cfg["MAX_ADDS_BY_PRIORITY"])
            adds["22"] = 5
            adds["23"] = 5
            adds["24"] = 5
            cfg["MAX_ADDS_BY_PRIORITY"] = adds
            save_config(cfg)

            out = run_replay(candles_csv)
            parsed = parse_output(out)
            results[stp] = parsed

            net = parsed.get("net_total", float("nan"))
            trd = parsed.get("trades", "?")
            print(f"  → NET ${net:+.2f} / {trd}trades", flush=True)
    finally:
        save_config(original_cfg)
        print("\n[config restored]", flush=True)

    print("\n" + "=" * 70)
    print("  SHORT TP グリッド結果（LONG_TP=0.005 / SHORT adds上限=5 固定）")
    print("=" * 70)
    print(f"  {'SHORT_TP':>9}  {'trades':>6}  {'NET':>10}  {'NET/day':>8}  {'P22':>8}  {'P23':>8}  {'P24':>8}")
    print("-" * 70)
    for stp in SHORT_TP_PCTS:
        d = results.get(stp, {})
        cur = " ◀ current" if stp == cur_short_tp else ""
        print(
            f"  {stp:.4f}    {d.get('trades', '?'):>6}  "
            f"${d.get('net_total', 0):>9.2f}  "
            f"${d.get('net_per_day', 0):>7.1f}  "
            f"${d.get('p22_short_net', 0):>7.2f}  "
            f"${d.get('p23_short_net', 0):>7.2f}  "
            f"${d.get('p24_short_net', 0):>7.2f}"
            f"{cur}"
        )

    best = max(results.items(), key=lambda x: x[1].get("net_total", float("-inf")))
    bp, bd = best
    print(f"\n★ 最良: SHORT_TP={bp:.4f}  NET ${bd.get('net_total', 0):+.2f}  ({bd.get('net_per_day', 0):+.1f}/day)")


def run_tp_p4_grid(candles_csv, original_cfg):
    results = {}
    total = len(TP_PCTS) * len(P4_MAXES)
    done  = 0

    try:
        for tp, p4m in product(TP_PCTS, P4_MAXES):
            done += 1
            label = f"TP={tp:.4f}/P4max={p4m}"
            print(f"\n[{done:02d}/{total}] {label} ...", flush=True)

            cfg = copy.deepcopy(original_cfg)
            cfg["LONG_TP_PCT"]  = tp
            cfg["SHORT_TP_PCT"] = tp
            adds = dict(cfg["MAX_ADDS_BY_PRIORITY"])
            adds["4"] = p4m
            cfg["MAX_ADDS_BY_PRIORITY"] = adds
            save_config(cfg)

            out = run_replay(candles_csv)
            parsed = parse_output(out)
            results[(tp, p4m)] = parsed

            net = parsed.get("net_total", float("nan"))
            trd = parsed.get("trades", "?")
            print(f"  → NET ${net:+.2f} / {trd}trades", flush=True)

    finally:
        save_config(original_cfg)
        print("\n[config restored]", flush=True)

    print("\n" + "=" * 72)
    print("  GRID SEARCH RESULTS — NET合計($) / 90日")
    print("=" * 72)

    header = f"{'':16}" + "".join(f"P4max={p}".rjust(12) for p in P4_MAXES)
    print(header)
    print("-" * 72)
    for tp in TP_PCTS:
        row = f"TP={tp:.4f}      "
        for p4m in P4_MAXES:
            d = results.get((tp, p4m), {})
            net = d.get("net_total")
            mark = " ◀" if (tp == 0.005 and p4m == 5) else "  "
            cell = (f"${net:+.0f}" if net is not None else "  ERR") + mark
            row += cell.rjust(12)
        print(row)

    print("\n" + "=" * 72)
    print("  NET/day ($)")
    print("=" * 72)
    print(header)
    print("-" * 72)
    for tp in TP_PCTS:
        row = f"TP={tp:.4f}      "
        for p4m in P4_MAXES:
            d = results.get((tp, p4m), {})
            v = d.get("net_per_day")
            mark = " ◀" if (tp == 0.005 and p4m == 5) else "  "
            cell = (f"${v:+.1f}" if v is not None else "ERR") + mark
            row += cell.rjust(12)
        print(row)

    best = max(results.items(), key=lambda x: x[1].get("net_total", float("-inf")))
    bp, bd = best
    print(f"\n★ 最良: TP={bp[0]:.4f} / P4max={bp[1]}  NET ${bd.get('net_total', 0):+.2f}  ({bd.get('net_per_day', 0):+.1f}/day)")

    print("\n" + "=" * 72)
    print("  全結果詳細")
    print("=" * 72)
    print(f"{'TP':>7}  {'P4max':>5}  {'trades':>6}  {'NET':>9}  {'P2':>8}  {'P4':>8}")
    print("-" * 72)
    for tp in TP_PCTS:
        for p4m in P4_MAXES:
            d = results.get((tp, p4m), {})
            cur = " ◀ current" if (tp == 0.005 and p4m == 5) else ""
            print(
                f"  {tp:.4f}  {p4m:>5}  {d.get('trades', '?'):>6}  "
                f"${d.get('net_total', 0):>8.2f}  "
                f"${d.get('p2_long_net', 0):>7.2f}  "
                f"${d.get('p4_long_net', 0):>7.2f}"
                f"{cur}"
            )


def run_priority_tp_grid(candles_csv, original_cfg, priority: int):
    """P22 / P23 / P24 それぞれ独立した TP_PCT グリッド。他 priority は現行値固定。"""
    tp_grid = {
        22: [0.004, 0.005, 0.006, 0.007],
        23: [0.005, 0.006, 0.007, 0.008],
        24: [0.004, 0.005, 0.006, 0.007],
    }
    tp_values = tp_grid[priority]
    param_key = f"P{priority}_TP_PCT"
    cur_val   = original_cfg.get(param_key, original_cfg.get("SHORT_TP_PCT", 0.005))

    print(f"  {param_key} を {tp_values} で検証（他 priority TP は現行値固定）\n")

    results = {}
    try:
        for i, tp in enumerate(tp_values, 1):
            print(f"\n[{i:02d}/{len(tp_values)}] {param_key}={tp:.4f} ...", flush=True)
            cfg = copy.deepcopy(original_cfg)
            cfg[param_key] = tp
            # P22/P23/P24 はads上限=5で検証（Priority別TP最適化の前提）
            adds = dict(cfg.get("MAX_ADDS_BY_PRIORITY", {}))
            adds[str(priority)] = 5
            cfg["MAX_ADDS_BY_PRIORITY"] = adds
            save_config(cfg)

            out = run_replay(candles_csv)
            parsed = parse_output(out)
            results[tp] = parsed

            net = parsed.get("net_total", float("nan"))
            trd = parsed.get("trades", "?")
            p_net = parsed.get(f"p{priority}_short_net", float("nan"))
            print(f"  → NET ${net:+.2f} / {trd}trades / P{priority} ${p_net:+.2f}", flush=True)
    finally:
        save_config(original_cfg)
        print("\n[config restored]", flush=True)

    print("\n" + "=" * 72)
    print(f"  {param_key} グリッド結果（他 priority 固定）")
    print("=" * 72)
    print(f"  {'TP_PCT':>8}  {'trades':>6}  {'NET':>10}  {'NET/day':>8}  {'P22':>8}  {'P23':>8}  {'P24':>8}")
    print("-" * 72)
    for tp in tp_values:
        d = results.get(tp, {})
        cur = " ◀ current" if abs(tp - cur_val) < 1e-9 else ""
        print(
            f"  {tp:.4f}    {d.get('trades', '?'):>6}  "
            f"${d.get('net_total', 0):>9.2f}  "
            f"${d.get('net_per_day', 0):>7.1f}  "
            f"${d.get('p22_short_net', 0):>7.2f}  "
            f"${d.get('p23_short_net', 0):>7.2f}  "
            f"${d.get('p24_short_net', 0):>7.2f}"
            f"{cur}"
        )

    best = max(results.items(), key=lambda x: x[1].get("net_total", float("-inf")))
    bp, bd = best
    print(f"\n★ 最良: {param_key}={bp:.4f}  NET ${bd.get('net_total', 0):+.2f}  ({bd.get('net_per_day', 0):+.1f}/day)")


def main():
    if len(sys.argv) < 2:
        print("Usage: grid_search.py <candles_csv> [--p2 | --short-tp | --p23-tp | --p22-tp | --p24-tp]")
        sys.exit(1)

    candles_csv = sys.argv[1]
    original_cfg = load_config()

    if "--p2" in sys.argv:
        run_p2_grid(candles_csv, original_cfg)
    elif "--short-tp" in sys.argv:
        run_short_tp_grid(candles_csv, original_cfg)
    elif "--p23-tp" in sys.argv:
        run_priority_tp_grid(candles_csv, original_cfg, priority=23)
    elif "--p22-tp" in sys.argv:
        run_priority_tp_grid(candles_csv, original_cfg, priority=22)
    elif "--p24-tp" in sys.argv:
        run_priority_tp_grid(candles_csv, original_cfg, priority=24)
    else:
        run_tp_p4_grid(candles_csv, original_cfg)


if __name__ == "__main__":
    main()
