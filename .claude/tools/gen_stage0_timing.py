#!/usr/bin/env python3
"""gen_stage0_timing.py — §2.2 の段0 の②｜1列と1組の時間を実測する。

なぜ作るか
----------
§2.2（レンジ判定の検索方法・まこさん決定 2026-09-01）の段0 の②＝
「1列・1組の時間の実測（3分超の段だけ『帯の形→付帯』に分割・差し戻しで拾い直す）」。

何が問題か（2026-09-09 に実測して分かったこと）
  §2.2 は列の数を「段1 約48・段2a 約60・段2c 約50」と書いている。
  これは 2026-09-01 の数字で、M2-C で印ができ成績表を作り直した後の実測とは3桁 違う
  （env 15,828／location 10,482／sufficiency 12,624／trigger 2,250）。
  だから 2026-09-01 の時間の見積もりは使えない。**測り直さないと段1 の設計が書けない。**

何を測るか（2つ）
  ①1列を作る時間＝`engine_tuner_exec.material_array` を1回 呼ぶ時間。
    ★同じ列は覚えて返す作りなので、覚えている分を消してから測る。
  ②1組（束）を評価する時間＝作った列を閾値と比べて真偽の並びにする時間。

  --run     測って画面に出す
  --write   測って stage0_timing.md に書く

★売買は1件も回さない（net はゼロのまま）。読むのは値決め窓のデータだけ。
★この道具は文書を作るだけ＝設計書と承認は要らない（恒久の決まり71番）。

限界（正直に）
  ・測るのは1列と1組だけ。段の全体の時間は、列の数を掛けた見積もりになる。
  ・同じ列を覚えて返す仕組みが効くと、2回目からは速い。だから初回だけを測る。
  ・機械の混み具合で変わる。何回か測って中央値を出す。
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
PRIORITY = SDK / "scripts" / "priority_rebuild"
RATCHET = SDK / ".claude" / "ratchet"

DEST = RATCHET / "stage0_timing.md"

# ★測る列＝§2.2 の段ごとに、成績表の1位を1本ずつ（段0 の①の突き合わせで「引ける」と出たもの）
SAMPLES = [
    ("段1 帯（location）", "close vs 24本高値%__1d"),
    ("段2a 強さの否定（env）", "ADX14__1d"),
    ("段2c 3枠目（sufficiency）", "ATR%14__1d"),
]

REPEAT = 5          # 何回 測るか（中央値を出す）


def load_frame():
    """値決め窓のデータを1回 読む。戻り＝(データ, 読むのにかかった秒)。

    ★読み方は `regime_r9_diag.py`:230 と同じにする（実物に合わせる・自分で作らない）＝
      `engine_tuner.load_windows_cached(接続, [(始まり, 終わり)], WARM)`。
    """
    sys.path.insert(0, str(PRIORITY))
    t0 = time.perf_counter()
    import engine_tuner as et
    from tuner_adapters import e38 as ad
    import periods
    df, = et.load_windows_cached(ad, [(periods.SEARCH_START, periods.SEARCH_END)], et.WARM)
    return df, time.perf_counter() - t0


def time_one_column(df, name: str) -> list:
    """1列を作る時間を REPEAT 回 測る。覚えている分は毎回 消す。"""
    sys.path.insert(0, str(PRIORITY))
    import engine_tuner_exec as ex
    out = []
    for _ in range(REPEAT):
        ex._MAT_MEMO["sig"], ex._MAT_MEMO["v"] = None, {}   # 覚えている分を消す
        t0 = time.perf_counter()
        ex.material_array(df, name)
        out.append(time.perf_counter() - t0)
    return out


def time_one_bundle(df, name: str) -> list:
    """1組（1つの条件）を評価する時間を REPEAT 回 測る。列は作り終えた後から測る。"""
    sys.path.insert(0, str(PRIORITY))
    import numpy as np
    import engine_tuner_exec as ex
    arr = ex.material_array(df, name)          # 先に作っておく（列の時間は含めない）
    out = []
    for _ in range(REPEAT):
        t0 = time.perf_counter()
        thr = float(np.nanquantile(arr, 0.30))  # 閾値（分位）を1つ出して
        _ = arr < thr                           # 真偽の並びにする
        out.append(time.perf_counter() - t0)
    return out


def measure() -> dict:
    """測って、結果をまとめて返す。"""
    df, load_sec = load_frame()
    rows = []
    for stage, name in SAMPLES:
        col = time_one_column(df, name)
        bun = time_one_bundle(df, name)
        rows.append({
            "stage": stage, "name": name,
            "col_med": statistics.median(col), "col_min": min(col), "col_max": max(col),
            "bun_med": statistics.median(bun),
        })
    return {"load_sec": load_sec, "bars": len(df), "rows": rows}


def build(res: dict) -> str:
    """結果の表を組み立てる。"""
    L = []
    add = L.append
    add("# 段0 の②｜1列と1組の時間の実測")
    add("")
    add("**★この表はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`gen_stage0_timing.py --write` の実測。")
    add("")
    add("**なぜ在るか**＝§2.2 は列の数を「段1 約48」と書いていますが、"
        "M2-C の後の実測は location が 10,482本 で3桁 違います。"
        "**2026-09-01 の時間の見積もりは使えません。**")
    add("")
    add(f"**データを読む時間＝{res['load_sec']:.1f}秒**（値決め窓の {res['bars']:,} 本）。"
        "★1回 読んで使い回します（§2.2 の共通の決まり）。")
    add("")
    add(f"**測った回数＝各 {REPEAT} 回。下の数字は中央値です。**")
    add("")
    add("| 段 | 測った列 | 1列を作る | 1組を評価する |")
    add("|---|---|---|---|")
    for r in res["rows"]:
        add(f"| {r['stage']} | `{r['name']}` | **{r['col_med'] * 1000:.1f} ミリ秒**"
            f"（{r['col_min'] * 1000:.1f}〜{r['col_max'] * 1000:.1f}） "
            f"| **{r['bun_med'] * 1000:.2f} ミリ秒** |")
    add("")
    add("## 段ごとの見積もり（列の数 × 1列の時間）")
    add("")
    add("**★列の数は成績表の実測です**（`material_ranking.json`）。")
    add("")
    add("| 段 | 役割 | 列の本数 | 1列の時間（中央値） | 全部 作ると |")
    add("|---|---|---|---|---|")
    counts = {"段1 帯（location）": ("location", 10482),
              "段2a 強さの否定（env）": ("env", 15828),
              "段2c 3枠目（sufficiency）": ("sufficiency", 12624)}
    for r in res["rows"]:
        role, n = counts[r["stage"]]
        sec = r["col_med"] * n
        add(f"| {r['stage']} | {role} | {n:,} | {r['col_med'] * 1000:.1f} ミリ秒 "
            f"| **{sec / 60:.1f} 分**（{sec:.0f}秒） |")
    add("")
    add("**★これは1列ずつ順に作った場合です。**同じ指標の期間違いは、"
        "まとめて作れば速くなる見込みがあります（§2.2 の「列を1回 作って閾値は一括比較」）。"
        "**その効き目は、この表では測っていません。**")
    add("")
    return "\n".join(L)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run", action="store_true", help="測って画面に出す")
    p.add_argument("--write", action="store_true", help="測って stage0_timing.md に書く")
    a = p.parse_args()
    if not (a.run or a.write):
        p.print_help()
        return 0
    res = measure()
    body = build(res)
    if a.write:
        DEST.write_text(body, encoding="utf-8")
        print(f"✅ --write 完了: {DEST}（{len(body.splitlines())}行）")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
