#!/usr/bin/env python3
"""col_snapshot.py — 材料の列（build_catalog の全部 × 全部の時間足）の名前と値を控える／控えと比べる（読むだけ・本物には書かない）。

ToDo の152番（cc_steps6_20261024.txt の「3.」）＝「直す前の列652本の名前と値を控えます。かかる時間を、先に小さく走らせて測ります。」
修正の5つの確かめ方（okd_plan5:V45）＝「直す前と後で、列652本の名前と計算した値が同じであること」。
列は、観察の道具の build_features（observe_diag.py:2382）をそのまま呼んで作る（計算を書き写さない）。値は列ごとに sha256 で控える。
使い方:
  python3 .claude/state/indicator_review/col_snapshot.py --out <控えの json> [--rows 30000] [--cols 正規表現]
  python3 .claude/state/indicator_review/col_snapshot.py --compare <控えの json> [--rows 30000] [--cols 正規表現]
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
PR = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild"
SDK = PR.parent.parent
CHUNK, BUDGET = 50, 0


def _save(path: Path, s: dict) -> None:
    """一時のファイルに書いてから名前を替える（途中で落ちても、前の区切りまでの控えは壊れない）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def snapshot(rows: int, cols: str | None, out_path: Path | None = None) -> dict:
    sys.path.insert(0, str(PR))
    cwd = os.getcwd()
    os.chdir(SDK)
    with contextlib.redirect_stdout(io.StringIO()):
        import observe_diag as od  # noqa: E402
    cfg = od.load_config()
    cat = od.build_catalog(cfg)
    if cols:
        cat = [c for c in cat if re.search(cols, c[0])]
    bars = pd.read_csv(od.BARS_CSV, parse_dates=["timestamp"]).set_index("timestamp").sort_index().iloc[-rows:]
    t0 = time.time()
    all_names = [c[0] for c in cat]
    idx_sha = hashlib.sha256(bars.index.asi8.tobytes()).hexdigest()
    out, done, done_chunks = {}, 0, []
    # ★2026-10-24（まこさん「走らせて落ちても控えのデータが消えないようにして」）＝区切りごとに控えを書き、走らせ直したら続きから計算する
    if out_path is not None and out_path.exists():
        prev = json.loads(out_path.read_text(encoding="utf-8"))
        if prev.get("all_names") == all_names and prev.get("rows") == rows and prev.get("index_sha256") == idx_sha:
            out, done_chunks = prev["cols"], prev.get("done_chunks", [])
            print(f"  続きから＝控え済みの区切り {len(done_chunks)} 個（列 {len(out)} 本）を飛ばす", flush=True)
        else:
            raise SystemExit(f"[続きから] 控え {out_path} は、種類の並び・5分足の本数・足の時刻のどれかが今と違う＝続きにできない（別の名前で控える）")
    for i in range(0, len(cat), CHUNK):            # ★50種ずつ計算し、区切りごとに時間を出す（全部を1回で計算すると、途中が見えず時間も読めない）
        if i in done_chunks:
            done = min(i + CHUNK, len(cat))
            continue
        t1 = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            feats, _meta = od.build_features(bars, cfg, catalog=cat[i:i + CHUNK])
        for c in sorted(feats.columns):
            a = np.ascontiguousarray(pd.to_numeric(feats[c], errors="coerce").to_numpy(dtype=np.float64))
            out[c] = {"sha256": hashlib.sha256(a.tobytes()).hexdigest(), "nan": int(np.isnan(a).sum())}
        done = min(i + CHUNK, len(cat))
        done_chunks.append(i)
        s = dict(all_names=all_names, names=all_names, n_names=len(all_names), done_chunks=sorted(done_chunks),
                 complete=len(done_chunks) == -(-len(cat) // CHUNK), timeframes=cfg["timeframes"], rows=rows,
                 bars_from=str(bars.index[0]), bars_to=str(bars.index[-1]), index_sha256=idx_sha, cols=out, seconds=round(time.time() - t0, 1))
        if out_path is not None:
            _save(out_path, s)
        print(f"  {done}/{len(cat)} 種（{cat[i][0]}〜{cat[done - 1][0]}）この区切り {time.time() - t1:.0f} 秒・累計 {time.time() - t0:.0f} 秒"
              f"{'・控えに書いた' if out_path is not None else ''}", flush=True)
        if BUDGET and time.time() - t0 > BUDGET and done < len(cat):
            print(f"  ★{BUDGET} 秒で切った＝全部の見込み 約 {(time.time() - t0) * len(cat) / done / 60:.0f} 分", flush=True)
            break
    os.chdir(cwd)
    return dict(all_names=all_names, names=all_names, n_names=len(all_names), done_chunks=sorted(done_chunks),
                complete=len(done_chunks) == -(-len(cat) // CHUNK), timeframes=cfg["timeframes"], rows=rows,
                bars_from=str(bars.index[0]), bars_to=str(bars.index[-1]), index_sha256=idx_sha, cols=out, seconds=round(time.time() - t0, 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--compare")
    ap.add_argument("--rows", type=int, default=30000)
    ap.add_argument("--cols")
    ap.add_argument("--budget", type=int, default=0, help="この秒数を超えたら、区切りの終わりで止めて全部の見込みを出す（0＝止めない）")
    a = ap.parse_args()
    global BUDGET
    BUDGET = a.budget
    s = snapshot(a.rows, a.cols, Path(a.out) if a.out else None)
    print(f"名前 {s['n_names']} 本 × 時間足 {len(s['timeframes'])} ＝ 列 {len(s['cols'])} 本・5分足 {s['rows']} 本（{s['bars_from']}〜{s['bars_to']}）"
          f"・計算 {s['seconds']} 秒・{'全部済み' if s['complete'] else '途中'}")
    if a.out:
        print("控え:", a.out)
    if a.compare:
        b = json.loads(Path(a.compare).read_text(encoding="utf-8"))
        miss = sorted(set(b["cols"]) - set(s["cols"]))
        new = sorted(set(s["cols"]) - set(b["cols"]))
        diff = sorted(c for c in set(b["cols"]) & set(s["cols"]) if b["cols"][c] != s["cols"][c])
        print(f"控えに在って今に無い列 {len(miss)}・今にだけ在る列 {len(new)}・値が違う列 {len(diff)}・名前の並び {'同じ' if b['names'] == s['names'] else '違う'}")
        for x in (miss + new + diff)[:30]:
            print("  ", x)
        sys.exit(0 if not (miss or new or diff) and b["names"] == s["names"] else 1)


if __name__ == "__main__":
    main()
