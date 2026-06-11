#!/usr/bin/env python3
"""preload_cache.py — replay preload(=ローソク足読込+指標計算) の parquet キャッシュ（時短③・承認済 2026-06-12）

毎実験で数分かかる rc.preload(csv, params) の結果 (df, df_raw) を parquet で保存し、
2回目以降は読み込みだけで返す。replay_csv.py / cat_v9_decider.py は無改造（import のみ）。

安全設計:
- キャッシュキー = CSV 実体 (パス+サイズ+mtime) ＋ preprocess が読む params 12 キーの値 の sha256。
  ENABLE_P* フラグや Exit 値は preprocess に影響しない（指標計算は共通）のでキーに含めない。
  preprocess が読む params（cat_v9_decider.py L52-230 grep 全数・2026-06-12）:
  SHORT_RSI_PERIOD / SHORT_RSI_SLOPE_N / P1_MACD_FAST / P1_MACD_SLOW / P1_MACD_SIGNAL /
  LONG_LOCATION_THRESH / SHORT_LOCATION_THRESH / LONG_RISK_THRESH / SHORT_RISK_THRESH /
  LONG_RISKSCORE_LOWER_THRESH / P22_RCI52_MIN / P22_ADX_MIN
- parquet は float64 をビット完全で保存（pyarrow）。保存直後に再読込して frame 完全一致を assert。
- --selfcheck: preload 直計算と cached_preload の (df, df_raw) 完全一致 ＋ rc.run() trades 完全一致を機械検証。

使い方:
    from preload_cache import cached_preload
    df, df_raw = cached_preload(csv_path, params)
    trades = rc.run(csv_path, params, _preloaded=(df, df_raw), regime_switch=False)
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))

import replay_csv as rc  # noqa: E402

CACHE_DIR = ROOT / "results" / "priority_rebuild" / "cache"

# preprocess(cat_v9_decider.py) が参照する params キー（grep 全数・このリスト変更時はキャッシュ全クリア）
PREPROCESS_PARAM_KEYS = [
    "SHORT_RSI_PERIOD", "SHORT_RSI_SLOPE_N",
    "P1_MACD_FAST", "P1_MACD_SLOW", "P1_MACD_SIGNAL",
    "LONG_LOCATION_THRESH", "SHORT_LOCATION_THRESH",
    "LONG_RISK_THRESH", "SHORT_RISK_THRESH", "LONG_RISKSCORE_LOWER_THRESH",
    "P22_RCI52_MIN", "P22_ADX_MIN",
]


def _cache_key(csv_path: str, params: dict) -> str:
    p = pathlib.Path(csv_path)
    st = p.stat()
    payload = {
        "csv": str(p.resolve()),
        "size": st.st_size,
        "mtime": int(st.st_mtime),
        "params": {k: params.get(k) for k in PREPROCESS_PARAM_KEYS},
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]


def _assert_frame_identical(a: pd.DataFrame, b: pd.DataFrame, name: str) -> None:
    assert list(a.columns) == list(b.columns), f"{name}: 列不一致"
    assert len(a) == len(b), f"{name}: 行数不一致"
    pd.testing.assert_frame_equal(a, b, check_exact=True, check_dtype=False)


def cached_preload(csv_path: str, params: dict, verbose: bool = True):
    """rc.preload と同じ (df, df_raw) を返す。キャッシュヒット時は読込のみ（数分→数秒）。"""
    key = _cache_key(csv_path, params)
    d = CACHE_DIR / key
    f_df, f_raw = d / "df.parquet", d / "df_raw.parquet"
    if f_df.exists() and f_raw.exists():
        df = pd.read_parquet(f_df)
        df_raw = pd.read_parquet(f_raw)
        if verbose:
            print(f"[cache] HIT {key}（preload スキップ）")
        return df, df_raw

    if verbose:
        print(f"[cache] MISS {key} → preload 実行（初回のみ数分）")
    df, df_raw = rc.preload(csv_path, params)
    d.mkdir(parents=True, exist_ok=True)
    df.to_parquet(f_df, index=False)
    df_raw.to_parquet(f_raw, index=False)
    # 保存直後の完全一致検証（劣化保存をその場で検出）
    _assert_frame_identical(df.reset_index(drop=True), pd.read_parquet(f_df), "df")
    _assert_frame_identical(df_raw.reset_index(drop=True), pd.read_parquet(f_raw), "df_raw")
    if verbose:
        print(f"[cache] SAVE {d}（再読込 完全一致✅）")
    return df, df_raw


def _selfcheck(csv_path: str):
    """直計算 vs キャッシュ経由で (df, df_raw) と rc.run() trades の完全一致を機械検証。"""
    params = rc._load_params()
    print("[selfcheck 1/3] preload 直計算...")
    df0, raw0 = rc.preload(csv_path, params)
    print("[selfcheck 2/3] cached_preload（MISS→SAVE→HIT の2回）...")
    cached_preload(csv_path, params)            # MISS → SAVE
    df1, raw1 = cached_preload(csv_path, params)  # HIT
    _assert_frame_identical(df0.reset_index(drop=True), df1.reset_index(drop=True), "df")
    _assert_frame_identical(raw0.reset_index(drop=True), raw1.reset_index(drop=True), "df_raw")
    print("  (df, df_raw) 完全一致✅")
    print("[selfcheck 3/3] rc.run() trades 一致（P23 のみ ON・直 vs キャッシュ）...")
    p = dict(params)
    for k in list(p):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p[k] = (k == "ENABLE_P23_SHORT")
    t0 = rc.run(csv_path, p, _preloaded=(df0, raw0), regime_switch=False)
    t1 = rc.run(csv_path, p, _preloaded=(df1, raw1), regime_switch=False)
    a, b = pd.DataFrame(t0), pd.DataFrame(t1)
    assert len(a) == len(b), f"件数不一致 {len(a)} vs {len(b)}"
    for c in ("entry_time", "exit_time", "exit_reason", "net_usd"):
        assert (a[c] == b[c]).all(), f"{c} 不一致"
    print(f"  trades {len(a)}件 (entry/exit/reason/net) 完全一致✅")
    print("[selfcheck] ALL PASS")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--csv", default=None, help="省略時は gen_p23_candidates.OHLCV_CSV")
    args = ap.parse_args()
    if args.csv is None:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import gen_p23_candidates as gen
        args.csv = str(gen.OHLCV_CSV)
    if args.selfcheck:
        _selfcheck(args.csv)
    else:
        cached_preload(args.csv, rc._load_params())
