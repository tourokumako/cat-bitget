#!/usr/bin/env python3
"""measure_p23_ground_scaleout.py — V9手書きP23の「正しい地面」を add＋部分決済（段階利確 scale out）で測り直す

背景（2026-06-09・WORKFLOW 改訂66 / strat_v9ml_design §10.17 / session_log §8）:
  旧地面 $925.73（measure_p23_ground_capped.py・連続モード）は「1ポジを一括決済・部分決済を使わない」
  測り方で、P23の設計思想（add で大勝ち ＋ 部分決済で小勝ちを刻む）を反映していなかった＝無効。
  本スクリプトは「V9 のまま積み上げた玉を、複数 TP で段階利確（部分決済）したら net がいくらか」を測る。

★まこさん承認済みの「地面測定用の固定ルール」（最適化しない・素直な1通り・§5.2 値は承認済）:
  1) 分割数 = V9 の積み上げ単位（保有ロット数）。1 ロット = 0.024 BTC。保有 k ロットの玉 → k 個に分けて段階利確。
  2) 各刻みの利確価格 = V9 が玉ごとに entry 時点で計算する動的 TP までを「現在の保有ロット数」で等分。
     一番近い刻み（1/k 地点）に価格が届いたら 1 ロット部分利確（指値 maker・TP_FILLED）。
     最後の 1 ロットは残して V9 の通常出口（TP/SL/STALE/TIME/STOCH）が決済する。
  3) 手数料下限ガード（薄利＝手数料負け禁止）: 刻み幅 step% = (TP までの値幅%)/k が往復 maker 0.028%
     （2×MAKER_FEE）を下回る玉は刻まない。

★案B（まこさん承認 2026-06-09）= 実際の取引所（Bitget）通り。部分決済で保有が「本当に減る」:
  - 部分決済で 1 ロットおろす → 保有 size・保有ロット数が減る → V9 の出口判定（MFE_STALE/size 依存等）と
    add 上限判定が「現在の保有」に追従する（満玉のまま固定しない）。
  - 平均建値は Bitget の merge 通り：部分決済では変えず数量だけ減らす。買い増し（add）でのみ再平均
    avg=(avg×size+price×unit)/(size+unit)。
  - 部分決済で枠が空けば（保有ロット数 < MAX_ADDS）、V9 の発火条件でまた買い増せる（同サイド 1 ポジに merge）。
  - 予算 0.12 = 全建玉合計の上限（H1・score.py の cap ゲートが物理検証）。

★V9 を壊さない（確認1・まこさん承認）:
  V9 の判定式（_calc_tp_price/_calc_sl_price/_check_exits_replay/check_entry_priority）は import のみ・改造なし。
  本スクリプトはそれらに「現在の保有（avg/size/add_count）」を渡して呼ぶだけ。途中刻みに届く前に V9 の他出口
  （SL/STALE/TIME/STOCH）が発動したら、残っている全ロットをその出口で決済する。

★手数料按分（確認2・まこさん承認・地面が実態より良く出ないように）:
  (a) 各部分決済を 1 行（size 0.024・建値＝その時点の merge 平均建値・出口＝刻み価格・TP_FILLED）にして
      score.py へ渡す → score.py が各行で entry/exit の maker fee を計算 ＝ 決済回数ぶんの maker fee が乗る。
  (b) ⚠️ P23=SHORT は funding 受取（net にプラス）。各行の entry_time を「その 0.024 が実際に add 約定した
      時刻（FIFO＝先に入れた玉を先に部分利確）」にする → score.py の funding が保有数量の時系列に一致し、
      先頭時刻から全ロットにかける過大計上（＝地面が良く出る）を防ぐ。

★自己検査（移植の正しさを物理的に証明・偽の数字を出さない）:
  enable_scaleout=False では部分決済が一切起きず保有も減らない → 1 ポジ＝1 行（満玉一括決済）＝
  gen.run_continuous（現地面 $925.73/265件）と完全一致するはず → 件数・net を assert（不一致なら停止）。

★不正防止3点（cat_requirements §8.4-2.9）: 判定は score.py の数字だけ（本スクリプトは net 計算に触れず
  rc._record_trade / score.py を import のみ）／実装後に独立（非同型）レビュー／番人ゲートのメタ確認。

V9 本体不変（import のみ）: gen_p23_candidates / replay_csv / cat_v9_decider / score / eval_engine。
"""
from __future__ import annotations
import argparse
import copy
import sys
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                                       # noqa: E402  V9 リプレイ（import のみ）
import gen_p23_candidates as gen                              # noqa: E402  連続モード移植（import のみ）
import eval_engine as ee                                      # noqa: E402  確定コスト定数（maker 等）
from strategies.cat_v9_decider import check_entry_priority    # noqa: E402

OUT = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p23_E03_ground_scaleout.csv"  # E番号=ledger E0.3（analysis_playbook §3.1）
CAP = 0.12                       # 予算（合計上限）・CLAUDE.md §0-2
FEE_FLOOR_PCT = 2 * ee.MAKER_FEE  # 往復 maker = 0.00028 (0.028%)・薄利ガードの下限


def _log(m):
    print(m, flush=True)


def _emit_portion(trades, pos, add_time_ms, exit_price, exit_reason, exit_ts_ms, params):
    """1 ロット（0.024 BTC）を 1 行として記録。建値＝現在の merge 平均建値・entry_time＝その 0.024 が
    実際に add 約定した時刻（FIFO・funding 用）。gross/fee は rc._record_trade（V9 と同一）が計算。"""
    tmp = copy.copy(pos)                              # feature 列・regime・add_count・mfe 等を引き継ぐ
    tmp["size_btc"] = float(pos["_unit_size"])        # ★この行は 0.024 ぶんだけ
    tmp["entry_price"] = float(pos["entry_price"])    # 現在の merge 平均建値（part close は不変）
    tmp["entry_time"] = int(add_time_ms)              # ★funding 用：実 add 時刻（FIFO）
    rc._record_trade(trades, tmp, exit_price=exit_price, exit_reason=exit_reason,
                     exit_ts_ms=exit_ts_ms, params=params)


def _close_remaining(trades, pos, exit_price, exit_reason, exit_ts_ms, params, enable_scaleout):
    """V9 の出口（TP/SL/他）が発動 → 残っている全ロットを同じ出口で決済。
    scaleout OFF は満玉 1 行（gen と完全一致＝自己検査用）。ON は残ロットごとに 1 行（FIFO funding）。"""
    if not enable_scaleout:
        rc._record_trade(trades, pos, exit_price=exit_price, exit_reason=exit_reason,
                         exit_ts_ms=exit_ts_ms, params=params)
        return
    for lot in pos["_lots"]:
        _emit_portion(trades, pos, lot["add_time"], exit_price, exit_reason, exit_ts_ms, params)
    pos["_lots"] = []


def _refresh_v9_view(pos):
    """V9 判定式に渡す「現在の保有」を _lots から再構成（size・add_count）。avg は merge 管理で別途保持。"""
    pos["size_btc"] = len(pos["_lots"]) * float(pos["_unit_size"])
    pos["add_count"] = len(pos["_lots"])


def _step_scaleout(state, df, arrays, bar_ms, i, params, initial_fn, enable_scaleout):
    """連続モード（gen._step 準拠）に部分決済（案B＝保有が動的に減る・空けば買い増す）を重ねた版。
    V9 の判定式は import のみで改造せず、現在の保有（avg/size/add_count）を渡して呼ぶ。
    arrays = (timestamp_ms, close, high_raw, low_raw) の numpy 配列（毎バー読む4列の高速アクセス）。"""
    pos, pending, trades = state["pos"], state["pending"], state["trades"]
    ts_arr, close_arr, high_arr, low_arr = arrays
    ts_ms   = int(ts_arr[i])
    close_p = float(close_arr[i])
    high_p  = float(high_arr[i])
    low_p   = float(low_arr[i])
    mark_p  = close_p
    side = "SHORT"
    unit = float(params.get(f"P{gen.PRIORITY}_POSITION_SIZE_BTC", params["SHORT_POSITION_SIZE_BTC"]))

    # 1. pending fill（SHORT: high>=limit）
    if pending is not None:
        if max(0, (ts_ms - int(pending["placed_bar_ms"])) // bar_ms) >= rc.PENDING_TTL_BARS:
            pending = None
        elif high_p >= float(pending["limit_price"]):
            fill_p  = float(pending["limit_price"])
            adx_val = float(pending.get("adx_at_entry", 0.0))
            states  = rc._calc_entry_states(df, i, ts_ms)
            if pos is None:                                       # 新規 entry（1 ロット目）
                pos = {
                    "side": side, "entry_priority": gen.PRIORITY, "entry_price": fill_p,
                    "entry_time": ts_ms, "add_count": 1, "size_btc": unit,
                    "tp_price": rc._calc_tp_price(side, fill_p, adx_val, params, gen.PRIORITY, atr_14=states.get("atr_14", float("nan"))),
                    "sl_price": rc._calc_sl_price(side, fill_p, params, gen.PRIORITY),
                    "regime": "", "mfe_usd": 0.0, "mae_usd": 0.0,
                    "max_high": float("-inf"), "min_low": float("inf"),
                    "adx_at_entry": pending.get("adx_at_entry", 0.0),
                    "bb_mid_slope_at_entry": pending.get("bb_mid_slope_at_entry", float("nan")),
                    "rsi_at_entry": pending.get("rsi_at_entry", float("nan")),
                    "rsi_slope_at_entry": pending.get("rsi_slope_at_entry", float("nan")),
                    "stoch_k_at_entry": pending.get("stoch_k_at_entry", float("nan")),
                    "stoch_d_at_entry": pending.get("stoch_d_at_entry", float("nan")),
                    "bb_width_at_entry": pending.get("bb_width_at_entry", float("nan")),
                    "ret_5": states["ret_5"], "atr_14": states["atr_14"],
                    "entry_hour": states["entry_hour"], "entry_weekday": states["entry_weekday"],
                    "mfe_peak_pct": 0.0, "trail_stop_price": None,
                    "_unit_size": unit, "_adx_last": adx_val,
                    "_lots": [{"add_time": ts_ms, "add_price": fill_p}],   # FIFO 台帳（funding 用）
                }
            else:                                                # ADD（merge 平均建値・V9 のまま）
                old_sz, old_p = float(pos["size_btc"]), float(pos["entry_price"])
                new_sz  = old_sz + unit
                new_avg = (old_p * old_sz + fill_p * unit) / new_sz
                pos["entry_price"] = new_avg
                pos["_adx_last"] = adx_val
                pos["_lots"].append({"add_time": ts_ms, "add_price": fill_p})
                _refresh_v9_view(pos)
                pos["tp_price"] = rc._calc_tp_price(side, new_avg, adx_val, params, gen.PRIORITY, atr_14=states.get("atr_14", float("nan")))
                pos["sl_price"] = rc._calc_sl_price(side, new_avg, params, gen.PRIORITY) if pos["add_count"] >= 2 else None
            pending = None

    closed = False
    # 2. MFE/MAE/極値（現在の avg・size で更新＝部分決済で保有が減れば追従）
    if pos is not None:
        entry_p, size_b = float(pos["entry_price"]), float(pos["size_btc"])
        unreal = (entry_p - mark_p) * size_b
        if unreal > float(pos.get("mfe_usd", 0.0)): pos["mfe_usd"] = unreal
        if unreal < float(pos.get("mae_usd", 0.0)): pos["mae_usd"] = unreal
        if low_p < float(pos.get("min_low", float("inf"))): pos["min_low"] = low_p

    # 2.5 ★部分決済（段階利確）── 現在の保有ロット数 k で V9 TP を等分し、一番近い刻み(1/k)に届いたら 1 ロット利確。
    #     最後の 1 ロットは残して V9 の通常出口に乗せる。利確でロットが減れば次バー以降の V9 出口・add 枠が追従。
    if enable_scaleout and pos is not None:
        while len(pos["_lots"]) >= 2:                  # 最後の 1 ロットは残す（j=k は V9 出口が決済）
            k   = len(pos["_lots"])
            avg = float(pos["entry_price"]); tp = float(pos["tp_price"])
            tp_drop_pct = (avg - tp) / avg             # SHORT: 建値→V9 TP の値幅%（正）
            if (tp_drop_pct / k) < FEE_FLOOR_PCT:      # 薄利ガード：刻み幅が往復 maker 未満なら刻まない
                break
            level = avg + (tp - avg) * (1.0 / k)       # 一番近い刻み（1/k 地点・SHORT は avg より下）
            if low_p <= level:
                lot = pos["_lots"].pop(0)              # FIFO：最古の add を先に部分利確
                _emit_portion(trades, pos, lot["add_time"], exit_price=level,
                              exit_reason="TP_FILLED", exit_ts_ms=ts_ms, params=params)
                _refresh_v9_view(pos)                  # 保有 size・add_count を減らす（avg は merge で不変）
            else:
                break

    # 3. TP（SHORT: low<=tp）── V9 の TP。残り全ロットをここで決済
    if pos is not None and low_p <= float(pos["tp_price"]):
        _close_remaining(trades, pos, float(pos["tp_price"]), "TP_FILLED", ts_ms, params, enable_scaleout)
        pos = None; closed = True
    # 4. SL（SHORT: high>=sl）
    if pos is not None and pos.get("sl_price") is not None and high_p >= float(pos["sl_price"]):
        _close_remaining(trades, pos, float(pos["sl_price"]), "SL_FILLED", ts_ms, params, enable_scaleout)
        pos = None; closed = True
    # 5. TRAIL は P1/P21 専用 → P23 は無し
    # 6. _check_exits_replay（TP/SL 以外の V9 出口 12種・現在の保有で判定）── 残り全ロットを決済
    if pos is not None:
        reason = rc._check_exits_replay(pos, mark_p, df, i, params, ts_ms)
        if reason:
            _close_remaining(trades, pos, mark_p, reason, ts_ms, params, enable_scaleout)
            pos = None; closed = True

    # 7. エントリー / ADD 判断（部分決済で保有ロットが減れば枠が空き、また買い増せる＝案B）
    fire_add = (check_entry_priority(i, df, params) == gen.PRIORITY)   # add は常にフル閾値（V9のまま）
    want_initial = (pos is None and pending is None and initial_fn(i))
    if (fire_add and pos is not None) or want_initial:
        if pos is not None:                                       # ADD 上限＝現在の保有ロット数で判定
            if len(pos["_lots"]) >= int(params.get("MAX_ADDS_BY_PRIORITY", {}).get(str(gen.PRIORITY), 5)):
                pass
            elif pending is None:
                pending = gen._mk_pending(df, i, close_p)
        elif pending is None:
            pending = gen._mk_pending(df, i, close_p)

    state["pos"], state["pending"] = pos, pending
    return closed


def run_scaleout(df, bar_ms, params, initial_fn, enable_scaleout):
    """連続モード（閉じたら次を開く）＋ 部分決済。enable_scaleout=False は gen.run_continuous と同一挙動。
    ② 高速化: 毎バー読む 4 列を numpy 配列で事前取得（pandas df.at の1個ずつ探す遅さを回避）。"""
    arrays = (df["timestamp_ms"].to_numpy(), df["close"].to_numpy(),
              df["high_raw"].to_numpy(), df["low_raw"].to_numpy())
    state = {"pos": None, "pending": None, "trades": []}
    for i in range(rc.CANDLE_WARMUP, len(df)):
        _step_scaleout(state, df, arrays, bar_ms, i, params, initial_fn, enable_scaleout)
    if state["pos"] is not None:                                  # 期間末強制クローズ
        _close_remaining(state["trades"], state["pos"], float(df.iloc[-1]["close"]),
                         "FORCE_CLOSE_EOD", int(df.iloc[-1]["timestamp_ms"]), params, enable_scaleout)
    return state["trades"]


def verify_concurrent_budget(trades: list) -> float:
    """全行から各時点の同時保有合計を実測し max を返す（0.12 超なら停止）。score.py の cap ゲートと二重。"""
    d = pd.DataFrame(trades)
    et = pd.to_datetime(d["entry_time"]).tolist()
    xt = pd.to_datetime(d["exit_time"]).tolist()
    sz = d["size_btc"].astype(float).tolist()
    events = [(et[i], sz[i]) for i in range(len(d))] + [(xt[i], -sz[i]) for i in range(len(d))]
    events.sort(key=lambda x: (x[0], x[1]))
    cur = mx = 0.0
    mxt = None
    for t, s in events:
        cur = round(cur + s, 9)
        if cur > mx:
            mx = cur; mxt = t
    print(f"[物理検証] 同時保有合計 max = {mx:.4f} BTC @ {mxt}（予算 {CAP}）")
    assert mx <= CAP + 1e-9, f"合計 {mx:.4f} BTC > 予算 {CAP} BTC（停止）"
    print(f"[物理検証] ✅ 全期間で sum(active) ≤ {CAP} BTC（コードが証明）")
    return mx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", type=int, default=0, help="先頭 N バーだけで動作確認（0=全期間）")
    ap.add_argument("--warmup-start", default=None,
                    help="ループ開始日 YYYY-MM-DD（指標は全期間計算済・ここから連続モードを回す）。"
                         "ポジションは最長6h＝月をまたがないので、採点期間の数ヶ月前から回せば 2025-04〜12 の"
                         "結果は全期間と同一。下の scope-check（OFF採点期間 trade=265 一致）で歪みゼロを物理確認。")
    ap.add_argument("--full-selfcheck", action="store_true",
                    help="全期間で自己検査(OFF=現地面 + scope-check)を回す。重い(OFF+gen の2パス追加)。"
                         "省略時は本番 ON 1パスのみ＝約3倍速（自己検査はスモークで担保）。")
    a = ap.parse_args()

    params = rc._load_params()
    p23 = dict(params)                                            # P23 のみ有効（gen.main / measure と同条件）
    for k in list(p23):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p23[k] = (k == "ENABLE_P23_SHORT")
    df, _df_raw = rc.preload(str(gen.OHLCV_CSV), p23)             # 指標は全期間で計算（ウォームアップ確保）
    if a.smoke:
        df = df.iloc[:a.smoke].reset_index(drop=True)
    if a.warmup_start:                                           # 連続モードのループ範囲だけを絞る（指標値は不変）
        ts0 = int(pd.Timestamp(a.warmup_start).timestamp() * 1000)
        df = df[df["timestamp_ms"] >= ts0].reset_index(drop=True)
    bar_ms = int(df.at[1, "timestamp_ms"] - df.at[0, "timestamp_ms"])
    _log(f"[load] bars={len(df)} bar_ms={bar_ms} smoke={a.smoke} warmup_start={a.warmup_start}")

    full_fn = lambda i: (check_entry_priority(i, df, p23) == gen.PRIORITY)

    # ---- ① 自己検査(OFF=現地面)+scope-check は --full-selfcheck 時のみ（重い OFF+gen の2パス）。
    #         省略時は本番 ON 1パスのみ＝約3倍速。numpy化(②)が壊れていないかはスモークで --full-selfcheck 確認。
    if a.full_selfcheck:
        off = run_scaleout(df, bar_ms, p23, full_fn, enable_scaleout=False)
        ref = gen.run_continuous(df, bar_ms, p23, full_fn)
        n_off, n_ref = len(off), len(ref)
        s_off = sum(float(t["net_usd"]) for t in off); s_ref = sum(float(t["net_usd"]) for t in ref)
        _log(f"[self-check] scaleout OFF: {n_off}件 net=${s_off:.2f} / 現地面 gen: {n_ref}件 net=${s_ref:.2f}")
        assert n_off == n_ref and abs(s_off - s_ref) < 0.01, \
            f"自己検査NG: scaleout OFF が現地面と一致しない（{n_off}vs{n_ref} / {s_off:.2f}vs{s_ref:.2f}）→ 移植ミス・停止"
        _log("[self-check] ✅ scaleout OFF = 現地面に完全一致 → V9 移植は正しい（numpy化後も不変）")
        _odf = pd.DataFrame(off)
        _et = pd.to_datetime(_odf["entry_time"])
        _m = (_et >= pd.Timestamp("2025-04-01")) & (_et < pd.Timestamp("2026-01-01"))
        _log(f"[scope-check] OFF 採点期間2025-04〜12 trade数 = {int(_m.sum())}（旧地面265と一致なら scoping は結果を歪めない）")
    else:
        _log("[self-check] スキップ（本番ON 1パスのみ＝高速）。OFF=現地面 一致はスモーク --full-selfcheck で担保済み")

    # ---- 部分決済 ON（案B＝保有が動的に減る・空けば買い増す）で測定 ----
    on = run_scaleout(df, bar_ms, p23, full_fn, enable_scaleout=True)
    net_on = sum(float(t["net_usd"]) for t in on)
    _log(f"[scaleout ON] 行数 {len(on)}（部分決済で 1 ポジが複数行に）/ net合計（コスト前）${net_on:.1f}")
    verify_concurrent_budget(on)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(on).to_csv(OUT, index=False)
    _log(f"[出力] {OUT}")
    _log(f"→ 次: python3 scripts/priority_rebuild/score.py {OUT} --start 2025-04-01 --end 2025-12-31")
    _log("  （score.py の cap・最小注文・funding/slippage 込みで正しい地面 net を出す＝判定はこの数字だけ）")


if __name__ == "__main__":
    main()
