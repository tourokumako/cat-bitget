#!/usr/bin/env python3
"""e38 — E38 の接続ファイル（engine_tuner が読む・要件 R4・まこさん承認 2026-07-27）

値の差し替え方＝共通の売買ループ e38_logic_parts.generic_logic_loop の引数。
**この方式を知っているのは本ファイルだけ。探索器は知らない。**
ロジックの定義と探索範囲の正本＝e38_logics.json（設定駆動・段1 の確定事項）。

中身は engine_tuner.py（旧 engine_search_e38.py）から E38 に依っていた部分をそのまま移した。
挙動は変えない＝同じ種で同じ値が選ばれることを恒等の確認で示す。
"""
from __future__ import annotations

import json
import pathlib

import pandas as pd

import e37_scalp as e37
import e38_logic_parts as parts

NAME = "e38"
LABEL = "E38 優先度スタック（レンジ・両方向・スキャル・設定駆動）"

HERE = pathlib.Path(__file__).resolve().parent.parent      # scripts/priority_rebuild/
CONFIG = HERE / "e38_logics.json"

TYPE_COL = "ceil_type"                                     # 型別に分けて見る列
TYPE_VALUES = ("down", "flat_up")


def config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _logic(logic_id: str) -> dict:
    lg = next((z for z in config()["logics"] if z["id"] == logic_id), None)
    if lg is None:
        raise SystemExit(f"[エラー] ロジック id が {CONFIG.name} に無い: {logic_id}")
    return lg


def logics() -> list[dict]:
    """扱えるロジックの一覧。回せるかの判定も返す（説明書 engine_tuner_manual と同じ条件）。"""
    cfg = config()
    out = []
    for lg in cfg["logics"]:
        ok, why = True, ""
        if lg.get("impl", {}).get("module") != "e38_logic_parts":
            ok, why = False, f"実装が {lg.get('impl', {}).get('module', '未指定')}＝共通の売買ループで動かない"
        elif lg["entry"]["type"] not in parts.ENTRY_FNS:
            ok, why = False, f"入口の型 {lg['entry']['type']} が実装されていない"
        elif cfg["search_space"]["logics"].get(lg["id"]) is None:
            ok, why = False, "探索する値が宣言されていない"
        out.append({"id": lg["id"], "side": lg.get("side", ""), "label": lg.get("label", ""),
                    "searchable": ok, "why": why})
    return out


def space(logic_id: str) -> dict:
    """探索する値の宣言＝出口の共通 ＋ そのロジックの入口。
    ★同名のキーはロジック側が勝つ（例 S2 の tmax_bars＝枠外の長い保有の除外・まこさん決定 2026-07-25）。"""
    cfg = config()
    lg = _logic(logic_id)
    if lg.get("impl", {}).get("module") != "e38_logic_parts" or lg["entry"]["type"] not in parts.ENTRY_FNS:
        raise SystemExit(f"[エラー] 回せるのは共通の売買ループのロジックだけ"
                         f"（{logic_id}: {lg.get('impl', {})} / {lg['entry']['type']}）")
    sp = cfg["search_space"]["logics"].get(logic_id)
    if sp is None:
        raise SystemExit(f"[エラー] search_space.logics に {logic_id} が無い（正本 {CONFIG.name}）")
    return {**cfg["search_space"]["common_exit"], **sp}


def coverage(logic_id: str) -> list[str]:
    """この探索が触れる指標の列（＝網羅度の分子・2026-07-27 まこさん OK・監査 提案1）。

    分母は observe_diag の指標カタログ（96種 × 8足 = 768列）。ここは手で書いた部品の一覧を返す
    ＝入口の確認に使えるのは HTF_PARTS と VOL_PARTS だけで、時間足も部品名に焼き付いている。
    要件 R3 が終わればここがカタログ側に置き換わる。
    """
    sp = space(logic_id)
    used = []
    for k in ("confirm_htf", "confirm_vol"):
        if k in sp:
            used += [c for c in sp[k]["choices"] if c != "none"]
    return used


def exit_keys() -> set:
    """出口側のキー（探索器が試行の値を入口と出口へ振り分けるのに使う）。"""
    return set(config()["search_space"]["common_exit"])


def series_bank(win: pd.DataFrame) -> dict:
    """quantile 型の宣言が参照する分布（値決め窓の中だけ＝確認窓・採点窓は見ない）。"""
    r12 = win["close"].pct_change(12)
    out = {
        "dev_z_abs": win["dev_z"].abs().dropna(),
        "ret12_abs_down": (-r12[r12 < 0]).dropna(),
    }
    for c in win.columns:                       # 確認2軸の部品列（prepare_df が付ける）
        if c.startswith("e38_htf_") or c.startswith("e38_vol_"):
            out[c] = win[c].dropna()
    return out


def fixed(logic_id: str, space_names) -> tuple[dict, dict]:
    """設定ファイルの確定値（探索対象でないもの）。毎試行に混ぜる。

    ★2026-07-25 に見つけた配線漏れの対策＝試行の値だけを部品に渡すと、設定ファイルの
      固定値（例 S2 の ceil_filter=flat_up）が探索中に無視される。探索対象のキーは試行値が勝つ。
    """
    lg = _logic(logic_id)
    ep = {k: v for k, v in lg["entry"].get("params", {}).items() if v is not None and k not in space_names}
    xp = {k: v for k, v in lg["exit"].get("params", {}).items() if v is not None and k not in space_names}
    return ep, xp


def min_per_day(logic_id: str):
    """件数/日 の下限（値の確定はまこさん・null ならゲートなし）。"""
    v = _logic(logic_id).get("params", {}).get("search_min_per_day")
    return None if v is None else float(v)


def load_windows(windows, warm: pd.Timedelta) -> list[pd.DataFrame]:
    """窓ごとの指標つきデータを作る。生データの読み込みは1回だけ（重いため）。"""
    lo = min(w[0] for w in windows) - warm
    raw = e37._load(0, start_override=str(lo.date()))
    cfg = config()
    adaptive_k = e37.V25_K if cfg["global"].get("regime", {}).get("v25_adaptive_band") else None
    out = []
    for (s, e) in windows:
        d = raw[(raw["ts"] >= s - warm) & (raw["ts"] < e)].reset_index(drop=True).copy()
        out.append(parts.prepare_df(d, adaptive_k=adaptive_k))
    return out


def run(df: pd.DataFrame, logic_id: str, entry_params: dict, exit_params: dict) -> pd.DataFrame:
    """値を1組受け取って売買記録を返す（1試行の中身・CSV は書かない）。"""
    lg = _logic(logic_id)
    tr = parts.generic_logic_loop(df, lg["entry"]["type"], entry_params, exit_params,
                                  max_lots=int(lg.get("params", {}).get("max_lots", 2)),
                                  logic_id=logic_id)
    return pd.DataFrame(tr)
