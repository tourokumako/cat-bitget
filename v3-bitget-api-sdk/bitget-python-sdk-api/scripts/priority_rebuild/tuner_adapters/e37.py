#!/usr/bin/env python3
"""e37 — E37 の接続ファイル（engine_tuner が読む・要件 R4／R1・まこさん承認 2026-07-27）

値の差し替え方＝e37_scalp のモジュール定数を setattr で書き換えてから run_e37 を呼ぶ。
**この方式を知っているのは本ファイルだけ。探索器は知らない。**
中身は engine_search_e37.py（従来の E37 専用の探索器）から そのまま移した＝挙動を変えない。

⚠️ E37 は S1（ショート）と L1（ロング）が1回の走行で同時に動く一枚岩で、ロジック単位に分かれていない
   （e37_scalp.py 2832行・v11 から v59 までの枝が全部その中にある）。
   だから --logic に渡す単位は「調整するツマミ群」になる。E38 の --logic（入口と出口の組み合わせ）とは
   単位の意味が違う。S1 と L1 を別々に調整するには E37 の実装を分解する作業が要る（要件 R1 の残り）。
"""
from __future__ import annotations

import pandas as pd

import e37_scalp as e37

NAME = "e37"
LABEL = "E37 レンジスキャル（採用土台 v59d_164・S1 ショートと L1 ロングが同時に動く一枚岩）"

TYPE_COL = "ceil_type"                                     # 型別に分けて見る列
TYPE_VALUES = ("down", "flat_up")

# 土台の構成（engine_search_e37.BASE_KW と同一＝report_trades_e37_range_scalp_longfu_145_score.txt §0 実行引数）
BASE_KW = dict(
    v11=True, v12_open_range=True, v13_time_maker=True, v18_tp2_far=True, v20_rg5=True,
    v22_set=True, v24_trend_maker_tp=True, v25_adaptive_band=True,
    v26_down_hours=1.0, v26_gap=0.5, v26_max_age_hours=6.0, v26_split_ceiling=True,
    v27_flatup_lock=True, v31_time_be=True, v35_flatup_range=True, v36_flatup_near=True,
    v37_flatup_climb=True, v38_flatup_clamp=True, v40_down_no_age=True,
    v47_mtf_cut=True, v48_stale_wait=True, v50_trend_wait=True, v53_flatup_fast_cut=True,
    v56_rearm_delay=True, v57_long_support=True, v57_long_flat_up_only=True,
)

_SIGS = ["adx7", "di7", "di14", "kijun26"]                 # 急騰の判定に使うシグナルの種類

# 調整できるツマミ群。E37 は一枚岩なので「ロジック」でなく「ツマミ群」の単位で並ぶ。
LOGICS = [
    {"id": "v59", "side": "both", "label": "急騰早切りの値（型別シグナル × 建値からの逆行% × 待ち時間）",
     "searchable": True, "why": ""},
]


def logics() -> list[dict]:
    return [dict(z) for z in LOGICS]


def space(logic_id: str) -> dict:
    """探索する値の宣言。

    ★閾値をシグナルの種類ごとに分けて持つ（th_down_adx7 … th_down_kijun26）。
      kijun26 は%スケールで adx/di の 10〜70 と桁が違うため、1つの範囲では扱えない。
      kijun26 だけ quantile 型＝値決め窓の分布から実行時に決める（CC の手打ち値なし）。
      走らせるときは、選ばれたシグナルに対応する閾値だけを使う（E38 の confirm_htf / th_* と同じ方式）。
    """
    if logic_id != "v59":
        raise SystemExit(f"[エラー] ツマミ群の id が e37 に無い: {logic_id}"
                         f"（在るのは {', '.join(z['id'] for z in LOGICS)}）")
    sp: dict = {}
    for side in ("down", "flat"):
        sp[f"V59_{side.upper()}_SIG"] = {"type": "cat", "choices": list(_SIGS)}
        for s in _SIGS:
            sp[f"th_{side}_{s}"] = ({"type": "quantile", "series": "kij_dev", "q_lo": 0.50, "q_hi": 0.995}
                                    if s == "kijun26" else {"type": "float", "lo": 10.0, "hi": 70.0})
    sp["V59_DOWN_ADV_PCT"] = {"type": "float", "lo": 0.1, "hi": 1.0}
    sp["V59_FLAT_ADV_PCT"] = {"type": "float", "lo": 0.1, "hi": 1.0}
    sp["V59_DOWN_WIN_MIN"] = {"type": "cat", "choices": [0, 120, 180, 240, 360]}
    sp["V59_FLAT_WIN_MIN"] = {"type": "cat", "choices": [60, 120, 240, 360]}
    sp["V59_WAIT_MIN"] = {"type": "cat", "choices": [0, 5, 10, 15, 20, 30, 45, 60]}
    sp["V59_CUT_MODE"] = {"type": "cat", "choices": ["close", "stop"]}
    return sp


def exit_keys() -> set:
    """E37 は入口と出口が一枚岩で分かれていない＝全部まとめて run へ渡す。"""
    return set()


def series_bank(win: pd.DataFrame) -> dict:
    """quantile 型の宣言が参照する分布（値決め窓の中だけ）。
    kij_dev＝基準線（26本の高安の中値）からの乖離%＝engine_search_e37._kij_range と同じ式。"""
    kij = (win["high"].rolling(26).max() + win["low"].rolling(26).min()) / 2.0
    dev = ((win["close"] / kij) - 1.0) * 100.0
    return {"kij_dev": dev.dropna()}


def fixed(logic_id: str, space_names) -> tuple[dict, dict]:
    """設定ファイルの確定値。E37 は土台の構成が BASE_KW に固定なので、毎試行に混ぜる値は無い。"""
    return {}, {}


def min_per_day(logic_id: str):
    """件数/日 の下限。E37 はまだ設定していない（値はまこさんが決める）。"""
    return None


def load_windows(windows, warm: pd.Timedelta) -> list[pd.DataFrame]:
    """窓ごとのデータを作る。生データの読み込みは1回だけ。
    ★E37 は指標を run_e37 が内部で作るので、ここでは助走込みのスライスを返すだけ。"""
    lo = min(w[0] for w in windows) - warm
    raw = e37._load(0, start_override=str(lo.date()))
    return [raw[(raw["ts"] >= s - warm) & (raw["ts"] < e)].reset_index(drop=True).copy()
            for (s, e) in windows]


def run(df: pd.DataFrame, logic_id: str, entry_params: dict, exit_params: dict) -> pd.DataFrame:
    """値を1組受け取って売買記録を返す（1試行の中身）。

    モジュール定数を書き換えて run_e37 を呼び、**必ず元へ戻す**（戻さないと次の試行が汚れる）。
    選ばれたシグナルに対応する閾値だけを、エンジンが見る定数へ入れる。
    """
    p = {**entry_params, **exit_params}
    ov = {k: v for k, v in p.items() if k.startswith("V59_")}
    ds, fs = p["V59_DOWN_SIG"], p["V59_FLAT_SIG"]
    for s, key, dst in ((ds, f"th_down_{ds}", "V59_DOWN_ADX7_TH"), (fs, f"th_flat_{fs}", "V59_FLAT_DID7_TH")):
        if key not in p:
            raise SystemExit(f"[設定エラー] シグナル {s} に対応する閾値 {key} が無い")
        ov[dst] = float(p[key])
    saved = {k: getattr(e37, k) for k in ov}
    for k, v in ov.items():
        setattr(e37, k, v)
    try:
        t = e37.run_e37(df.copy(), "5m", tag=None, v59_adx_cut=True, return_trades=True, **BASE_KW)
    finally:
        for k, v in saved.items():
            setattr(e37, k, v)
    return t
