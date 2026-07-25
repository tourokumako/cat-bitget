#!/usr/bin/env python3
"""engine_search_e38.py — 層3エンジン内探索の E38 版（ロジック単位・設定 json の値を差し替え・まこさん GO 2026-07-24）

engine_search_e37 の型の流用。違い＝差し替え先がモジュール定数 setattr でなく e38_logics.json の宣言
（entry/exit params ＋ search_space）＝設定 json が探索範囲まで含めて正本（採択値は json に書き戻せば設計書と一致）。

窓構成（まこさん決定 2026-07-24・正本 window_similarity_ranking.md・e38_requirements.json decisions）:
  値決め＝探索窓 SEARCH_*（2024-04〜07・構造類似2位・距離1.78）だけを目的関数にする。
  確認＝CONFIRM_*（2025-12〜2026-02・8位相当・距離2.26・採点窓直前3ヶ月）を best 1点のみ1回走らせ表示のみ
  ＝確認窓の成績で選び直さない（選び直すと確認の意味が消える）。
  採点窓（periods）は不使用＝段5 の統合最終形1つだけ（覗き見ゼロ）。
探索範囲＝e38_logics.json search_space の宣言（float=幾何 a-priori の広め固定幅／quantile=探索窓の分布分位から
  実行時に上下限を決める＝CC の手打ち値なし・kijun26 前例）。

実行: TAGLESS_OK=1 python3 scripts/priority_rebuild/engine_search_e38.py --logic S2 --trials 150
  （TAGLESS_OK＝require_tag hook の e3N 正規表現がファイル名に反応するための明示通過。本装置は選定装置＝
   売買記録 CSV を出さない＝実験でない。engine_search_e37 と同じ扱い・pdca_flow §5）
"""
from __future__ import annotations
import argparse
import contextlib
import io
import json
import pathlib
import time

import pandas as pd

import e37_scalp as e37
import e38_logic_parts as parts
import periods                      # 採点窓の正本（重複 assert 用・数値は書かない）
import score as judge               # 審判＝import のみ・無変更（H13）

HERE = pathlib.Path(__file__).resolve()
LOGIC_JSON = HERE.parent / "e38_logics.json"

SEARCH_START = pd.Timestamp("2024-04-01")   # まこさん決定 2026-07-24（構造類似2位・正本 window_similarity_ranking.md）
SEARCH_END = pd.Timestamp("2024-08-01")     # 排他（2024-07-31 まで）
CONFIRM_START = pd.Timestamp("2025-12-01")  # まこさん決定 2026-07-24（確認窓＝8位相当・採点窓直前・表示のみ）
CONFIRM_END = pd.Timestamp("2026-03-01")    # 排他（採点窓 SCORE_START と接し重ならない）
WARM = pd.Timedelta(days=60)                # 助走（RG 168h＋rolling を満たす a-priori・e37._load と同じ考え方）

assert SEARCH_END <= periods.SCORE_START and CONFIRM_END <= periods.SCORE_START, \
    "探索/確認窓が採点窓（periods 正本）と重複＝采否の窓の汚染"


def _series_bank(win: pd.DataFrame) -> dict:
    """quantile 型の探索範囲が参照する分布（探索窓内のみ＝確認窓・採点窓は見ない）。"""
    r12 = win["close"].pct_change(12)
    out = {
        "dev_z_abs": win["dev_z"].abs().dropna(),
        "ret12_abs_down": (-r12[r12 < 0]).dropna(),
    }
    for c in win.columns:                       # S2 確認2軸の部品列（prepare_df が付ける・2026-07-25 まこさん GO）
        if c.startswith("e38_htf_") or c.startswith("e38_vol_"):
            out[c] = win[c].dropna()
    return out


def _resolve_space(space_decl: dict, bank: dict) -> dict:
    """search_space 宣言 → Optuna 用の実レンジ（quantile は実行時実値・印字して透明化）。"""
    out = {}
    for name, d in space_decl.items():
        if d["type"] == "float":
            out[name] = ("float", float(d["lo"]), float(d["hi"]))
        elif d["type"] == "cat":
            out[name] = ("cat", list(d["choices"]))
        elif d["type"] == "quantile":
            s = bank[d["series"]]
            out[name] = ("float", float(s.quantile(d["q_lo"])), float(s.quantile(d["q_hi"])))
        else:
            raise SystemExit(f"[探索範囲エラー] 未知の type: {d}（正本 e38_logics.json search_space）")
    return out


def _suggest(trial, space: dict) -> dict:
    return {n: (trial.suggest_float(n, r[1], r[2]) if r[0] == "float" else trial.suggest_categorical(n, r[1]))
            for n, r in space.items()}


def _run_window(dfp: pd.DataFrame, lg: dict, ep: dict, xp: dict, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    """1走＝汎用部品を回し窓内を審判式で評価（CSV を書かない）。"""
    tr = parts.generic_logic_loop(dfp, lg["entry"]["type"], ep, xp,
                                  max_lots=int(lg.get("params", {}).get("max_lots", 2)), logic_id=lg["id"])
    t = pd.DataFrame(tr)
    if len(t):
        et = pd.to_datetime(t["entry_time"])
        t = t[(et >= start) & (et < end)].reset_index(drop=True)
    if not len(t):
        return {"total": 0.0, "n": 0, "per_day": 0.0, "hold_med": float("nan"), "t": t}
    res = judge.score(t)
    days = max((end - start).days, 1)
    return {"total": float(res["total"]), "n": len(t), "per_day": len(t) / days,
            "hold_med": float(t["hold_min"].median()), "t": t}


def _type_split(t: pd.DataFrame) -> str:
    """型別（ceil_type）の審判値内訳（機械出力・段2 完了条件の型別列）。"""
    outs = []
    for ct in ("down", "flat_up"):
        sub = t[t["ceil_type"] == ct].reset_index(drop=True)
        outs.append(f"{ct} {len(sub)}玉 ${judge.score(sub)['total']:+,.0f}" if len(sub) else f"{ct} 0玉 $0")
    return " / ".join(outs)


def main() -> None:
    ap = argparse.ArgumentParser(description=f"E38 層3探索（ロジック単位・値決め={SEARCH_START.date()}〜{SEARCH_END.date()} 排他／確認={CONFIRM_START.date()}〜{CONFIRM_END.date()} 排他=表示のみ・まこさん決定 2026-07-24）")
    ap.add_argument("--logic", required=True, help="探索するロジック id（例 S2・e38_logics.json の generic ロジック）")
    ap.add_argument("--trials", type=int, default=150)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--log", default=None)
    a = ap.parse_args()
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    cfg = json.loads(LOGIC_JSON.read_text(encoding="utf-8"))
    lg = next((z for z in cfg["logics"] if z["id"] == a.logic), None)
    if lg is None:
        raise SystemExit(f"[エラー] logic id が e38_logics.json に無い: {a.logic}")
    if lg.get("impl", {}).get("module") != "e38_logic_parts" or lg["entry"]["type"] not in parts.ENTRY_FNS:
        raise SystemExit(f"[エラー] 探索対象は汎用部品ロジックのみ（{a.logic}: {lg.get('impl', {})} / {lg['entry']['type']}）")
    sp_entry = cfg["search_space"]["logics"].get(a.logic)
    sp_exit = cfg["search_space"]["common_exit"]
    if sp_entry is None:
        raise SystemExit(f"[エラー] search_space.logics に {a.logic} が無い（正本 e38_logics.json）")

    print(f"[窓] 値決め {SEARCH_START.date()}〜{SEARCH_END.date()}（排他）／確認 {CONFIRM_START.date()}〜{CONFIRM_END.date()}（排他・表示のみ）＝まこさん決定 2026-07-24・採点窓不使用")
    t0 = time.time()
    df_all = e37._load(0, start_override=str((SEARCH_START - WARM).date()))
    adaptive_k = e37.V25_K if cfg["global"].get("regime", {}).get("v25_adaptive_band") else None
    df_s = parts.prepare_df(df_all[(df_all["ts"] >= SEARCH_START - WARM) & (df_all["ts"] < SEARCH_END)].reset_index(drop=True).copy(), adaptive_k=adaptive_k)
    df_c = parts.prepare_df(df_all[(df_all["ts"] >= CONFIRM_START - WARM) & (df_all["ts"] < CONFIRM_END)].reset_index(drop=True).copy(), adaptive_k=adaptive_k)
    print(f"[共通部分] 探索スライス {len(df_s):,} バー／確認スライス {len(df_c):,} バー（{time.time()-t0:.0f}秒）")
    bank = _series_bank(df_s[df_s["ts"] >= SEARCH_START])
    # ロジック側の宣言が common_exit の同名キーを上書きする（後勝ち）＝S2 tmax_bars [24,48]＝8時間持ちの除外
    # （まこさん決定 2026-07-25「8時間は外す」・スキャル役割 §8.6）。同名キーは1回だけ suggest され、
    # exit_keys 分類は common_exit のキー名で行うので xp へ正しく流れる。
    space = {**_resolve_space(sp_exit, bank), **_resolve_space(sp_entry, bank)}
    for n, r in space.items():
        print(f"[範囲] {n}: {r[0]} {r[1] if r[0]=='float' else r[1]}" + (f" 〜 {r[2]:.6g}" if r[0] == "float" else ""))

    exit_keys = set(sp_exit)
    # ★json の確定値（null でない entry/exit params＝例 S2 ceil_filter="flat_up"）を毎試行にマージする。
    #   2026-07-25 発見の配線漏れ＝試行の値だけを部品に渡し、json の固定値が探索中に無視されていた
    #   （2回目探索で flat_up 限定が効かず down 玉95が混入＝型別表示で検出）。探索対象キーは試行値が勝つ。
    fixed_ep = {k: v for k, v in lg["entry"].get("params", {}).items() if v is not None and k not in space}
    fixed_xp = {k: v for k, v in lg["exit"].get("params", {}).items() if v is not None and k not in space}
    if fixed_ep or fixed_xp:
        print(f"[固定値（json 確定値＝全試行に適用）] entry={fixed_ep} / exit={fixed_xp}")
    # ★件数/日の下限ゲート（2026-07-25 まこさん指摘「段2 の目標を段3 の検証条件に入れるべき」）:
    #   json の logics[].params.search_min_per_day（値の確定はまこさん・null=ゲートなし）。
    #   下限未満の試行は棄却＝net だけを見て件数極小へ逃げ込む形（pos_min 0.82 事案）を探索空間から締め出す。
    min_per_day = lg.get("params", {}).get("search_min_per_day")
    if min_per_day is not None:
        min_per_day = float(min_per_day)
        print(f"[件数ゲート] 値決め窓の件数/日 < {min_per_day} の試行は棄却（出典＝json params.search_min_per_day・段2 最低ラインからの割り付け＝まこさん確定値）")
    else:
        print("[件数ゲート] なし（json params.search_min_per_day が未設定＝値はまこさんが決める）")
    logf = open(a.log or f"engine_search_e38_{a.logic}.log", "w", encoding="utf-8")
    results = []

    def obj(trial):
        pr = _suggest(trial, space)
        ep = {**fixed_ep, **{k: v for k, v in pr.items() if k not in exit_keys}}
        xp = {**fixed_xp, **{k: v for k, v in pr.items() if k in exit_keys}}
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = _run_window(df_s, lg, ep, xp, SEARCH_START, SEARCH_END)
        results.append((trial.number, dict(trial.params), res))
        logf.write(f"T{trial.number}\t{res['total']:+.1f}\t{res['n']}\t{res['per_day']:.2f}\t{trial.params}\n")
        logf.flush()
        if trial.number % 20 == 0:
            print(f"  trial {trial.number}: net ${res['total']:+,.0f} / {res['n']}玉 / {res['per_day']:.2f}件/日 / 経過 {(time.time()-t0)/60:.1f}分", flush=True)
        if min_per_day is not None and res["per_day"] < min_per_day:
            return -1e9                    # 件数下限ゲート＝段2 最低ラインの割り付け（値はまこさん確定）
        return res["total"]

    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=a.seed))
    st.optimize(obj, n_trials=a.trials, show_progress_bar=False)

    print(f"\n[上位10（{a.logic}・値決め窓の審判値・件数/日は §8.6 の一級列＝net だけで上位に置かない）]")
    for num, params, res in sorted(results, key=lambda z: -z[2]["total"])[:10]:
        print(f"  #{num}: net ${res['total']:+,.0f} / {res['n']}玉 / {res['per_day']:.2f}件/日\n      {params}")

    bp = dict(st.best_trial.params)
    ep = {**fixed_ep, **{k: v for k, v in bp.items() if k not in exit_keys}}
    xp = {**fixed_xp, **{k: v for k, v in bp.items() if k in exit_keys}}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rs = _run_window(df_s, lg, ep, xp, SEARCH_START, SEARCH_END)
        rc = _run_window(df_c, lg, ep, xp, CONFIRM_START, CONFIRM_END)
    print(f"\n[best #{st.best_trial.number}（値決め窓で選定・確認窓は表示のみ＝選び直し禁止）] {bp}")
    print(f"  値決め窓: net ${rs['total']:+,.0f} / {rs['n']}玉 / {rs['per_day']:.2f}件/日 / 保有中央 {rs['hold_med']:.0f}分 / 型別 {_type_split(rs['t']) if len(rs['t']) else '—'}")
    print(f"  確認窓  : net ${rc['total']:+,.0f} / {rc['n']}玉 / {rc['per_day']:.2f}件/日 / 保有中央 {rc['hold_med']:.0f}分 / 型別 {_type_split(rc['t']) if len(rc['t']) else '—'}")
    print("⚠️ ここは探索側の数字＝採否の数字ではない。統合最終形1つだけを段5 で採点窓 score.py にかけ、採否はまこさんが判断する。")
    logf.close()


if __name__ == "__main__":
    main()
