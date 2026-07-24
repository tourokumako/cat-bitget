#!/usr/bin/env python3
"""e38_logic_parts.py — E38 候補ロジックの汎用売買部品（段2・まこさん GO 2026-07-24・設計 e38_design.md／グリッド節 E38）

run_long_support（e37_scalp.py 1569行〜）の型を側対称に一般化した単純な売買ループ1本＋入口関数テーブル。
入口条件だけを e38_logics.json の entry.type / entry.params で差し替える（設定駆動）。
出口は共通部品＝PARTIAL_TP 半分・TP2・災害SL（帯幾何）・TIME・建値フロア待機（v31 型 BE_EXIT）＝新しい出口軸を作らない。
決済の maker/taker・funding・売買記録の列構成は e37._record を import 再利用（score.py 登録済み exit_reason のみ＝H13 無変更）。
シグナルは全て当該バーまでの確定値・約定は次バー以降（H2）。maker 指値・TTL 3本・1バー1発注・手数料床 SCALP_FLOOR。

S4 の注記（まこさん報告済み 2026-07-24）: dev_z=(close−SMA20)/std20 は BB20 の kσ と同じ窓の標準化＝数学的に同値なので
指標カテゴリは dev_z に一本化した（別窓の BB を足す時は entry.params に窓を持たせて拡張する）。
S5/L5 グリッドは売買構造が別物（複数 resting・在庫管理）＝本部品に押し込まず後続の実装単位（json に定義のみ・enabled 不可）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import e37_scalp as e37
from strat_base import ENTRY_OFFSET, TTL, UNIT

SCALP_FLOOR = e37.SCALP_FLOOR          # 手数料床 0.08%（maker 往復の約2.9倍・a-priori）
V11_SL_BUF = e37.V11_SL_BUF            # 反対側ゾーン手前バッファ 0.05%（v18 と同一）
BE_TTL_BARS = 24                       # 建値フロア待機 TTL（v31 と同じ 24本=120分・既存定数の再利用＝新数値なし）
UNIT_LOT = UNIT / e37.V15_UNIT_DIV     # 0.012 BTC/lot（S1/L1 と同じ lot 幾何）


def prepare_df(df: pd.DataFrame, adaptive_k=None) -> pd.DataFrame:
    """部品が使う列を付ける（rsi9・RG-v5/v6 帯列・stoch_d・出来高移動平均）。全て確定バーのみ（H2）。"""
    df = e37._rsi9_v10(df)
    df = e37._apply_rg5_to_5m(df, adaptive_k=adaptive_k)
    df["e38_stoch_d"] = df["stoch_k"].rolling(3).mean()
    df["e38_vol_ma20"] = df["volume"].rolling(20).mean()
    return df


# ---------------------------------------------------------------- 入口関数テーブル
# fn(ctx, i, p) -> bool。共通前提（range_ok ∩ 帯あり ∩ uptrend 非発火 ∩ スロット空き）はループ側が課す。

def _pullback_short(ctx, i, p):
    """S2 戻り売り: mid 以上への戻り（帯内位置 pos_min 以上）∩ 失速確認（カテゴリ）。"""
    span = ctx["res_hi"][i] - ctx["mid"][i]
    if not (np.isfinite(span) and span > 0):
        return False
    pos = (ctx["c"][i] - ctx["mid"][i]) / span
    if not (pos >= p["pos_min"]):
        return False
    confirm = p.get("confirm", "none")
    if confirm == "stoch_dc":
        k, d = ctx["k"], ctx["d"]
        return bool(np.isfinite(k[i]) and np.isfinite(d[i]) and k[i - 1] >= d[i - 1] and k[i] < d[i])
    if confirm == "rsi9_down":
        r = ctx["rsi9"]
        return bool(np.isfinite(r[i]) and np.isfinite(r[i - 1]) and r[i] < r[i - 1])
    if confirm == "bear_bar":
        return bool(ctx["c"][i] < ctx["o"][i])
    return True                                            # none＝到達で即


def _fade_short(ctx, i, p):
    """S3 上抜け失敗: res_hi を上抜け ∩ close は帯内へ戻る（W 比の上抜け幅が over_min 以上）。"""
    W = ctx["res_hi"][i] - ctx["sup_lo"][i]
    if not (np.isfinite(W) and W > 0):
        return False
    if int(p.get("confirm_bars", 0)) >= 1:                 # 1本待ち＝前バー上抜け ∩ 当バー帯内 close
        over = (ctx["h"][i - 1] - ctx["res_hi"][i - 1])
        return bool(np.isfinite(over) and over / W >= p["over_min"] and ctx["c"][i] < ctx["res_hi"][i])
    over = ctx["h"][i] - ctx["res_hi"][i]                  # 当バー完結＝高値は上抜け・close は帯内
    return bool(over / W >= p["over_min"] and ctx["c"][i] < ctx["res_hi"][i])


def _zscore_short(ctx, i, p):
    """S4 統計的回帰: dev_z 上側行き過ぎ（トリガ＝即 / 反転確認=close 下向き）。"""
    z = ctx["dev_z"][i]
    if not (np.isfinite(z) and z >= p["z_th"]):
        return False
    return bool(ctx["c"][i] < ctx["c"][i - 1]) if p.get("trigger", "imm") == "rev" else True


def _crash_rebound_long(ctx, i, p):
    """L2 急落後反発: k_bars 本での下落率 ∩ 出来高スパイク（E28 型の5分足近似＝taker 不在の置き換え・まこさん OK）。"""
    kb = int(p["k_bars"])
    if i < kb:
        return False
    ret = ctx["c"][i] / ctx["c"][i - kb] - 1.0
    vma = ctx["vol_ma"][i]
    if not (np.isfinite(ret) and np.isfinite(vma) and vma > 0):
        return False
    return bool(ret <= -p["drop_th"] and ctx["vol"][i] >= p["vol_mult"] * vma)


def _fade_long(ctx, i, p):
    """L3 下抜け失敗: sup_lo を下抜け ∩ close は帯内へ戻る。"""
    W = ctx["res_hi"][i] - ctx["sup_lo"][i]
    if not (np.isfinite(W) and W > 0):
        return False
    if int(p.get("confirm_bars", 0)) >= 1:
        under = ctx["sup_lo"][i - 1] - ctx["l"][i - 1]
        return bool(np.isfinite(under) and under / W >= p["over_min"] and ctx["c"][i] > ctx["sup_lo"][i])
    under = ctx["sup_lo"][i] - ctx["l"][i]
    return bool(under / W >= p["over_min"] and ctx["c"][i] > ctx["sup_lo"][i])


def _zscore_long(ctx, i, p):
    """L4 統計的回帰: dev_z 下側行き過ぎ。"""
    z = ctx["dev_z"][i]
    if not (np.isfinite(z) and z <= -p["z_th"]):
        return False
    return bool(ctx["c"][i] > ctx["c"][i - 1]) if p.get("trigger", "imm") == "rev" else True


ENTRY_FNS = {
    "pullback_short": ("SHORT", _pullback_short),
    "fade_short": ("SHORT", _fade_short),
    "zscore_short": ("SHORT", _zscore_short),
    "crash_rebound_long": ("LONG", _crash_rebound_long),
    "fade_long": ("LONG", _fade_long),
    "zscore_long": ("LONG", _zscore_long),
}


def generic_logic_loop(df: pd.DataFrame, entry_type: str, entry_params: dict, exit_params: dict,
                       max_lots: int = 2, logic_id: str = "") -> list:
    """汎用売買ループ（run_long_support の側対称一般化）。

    出口 exit_params:
      tp1_frac   … TP1 の位置＝建値と TP2 の間の比率（0〜1・建値寄りほど小さい）
      tp2_target … "mid"（レンジ中央）| "opp"（反対側ゾーン手前×V11_SL_BUF＝v18 と同じ幾何）
      sl_zone_k  … 災害SL＝ゾーン外側 + k×帯幅（run_long_support SL_K と同じ幾何）
      tmax_bars  … 時間切れ（本数・成行 taker）
      be_wait    … 1 なら TIME 満了時に建値フロア resting maker（BE_EXIT・TTL 24本＝v31 型）
    """
    side, entry_fn = ENTRY_FNS[entry_type]
    o = df["open"].to_numpy(float); h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    ts = df["ts"].to_numpy()
    ctx = {
        "o": o, "h": h, "l": l, "c": c,
        "atr": df["atr"].to_numpy(float), "adx": df["adx"].to_numpy(float),
        "k": df["stoch_k"].to_numpy(float), "d": df["e38_stoch_d"].to_numpy(float),
        "rsi9": df["rsi9"].to_numpy(float), "dev_z": df["dev_z"].to_numpy(float),
        "vol": df["volume"].to_numpy(float), "vol_ma": df["e38_vol_ma20"].to_numpy(float),
        "res_lo": df["v11_res_lo"].to_numpy(float), "res_hi": df["v11_res_hi"].to_numpy(float),
        "sup_lo": df["v11_sup_lo"].to_numpy(float), "sup_hi": df["v11_sup_hi"].to_numpy(float),
        "mid": df["v11_mid"].to_numpy(float),
    }
    ok = df["range_ok_rg5"].to_numpy(bool); up = df["rg5_uptrend"].to_numpy(bool)
    atr_e, adx_e, k_e = ctx["atr"], ctx["adx"], ctx["k"]
    res_lo, res_hi, sup_lo, sup_hi, mid = ctx["res_lo"], ctx["res_hi"], ctx["sup_lo"], ctx["sup_hi"], ctx["mid"]
    tp1_frac = float(exit_params["tp1_frac"]); tp2_target = exit_params["tp2_target"]
    sl_k = float(exit_params["sl_zone_k"]); tmax = int(exit_params["tmax_bars"])
    be_wait = bool(exit_params.get("be_wait", 0))
    gap = 0.5 / 100.0                                      # 型判定 gap（v26_gap と同じ・診断列 ceil_type 用）
    n = len(df); trades: list = []; lots: list = []; pend = None
    for i in range(1, n):
        if pend is not None:                               # pend 約定（約定バーの次以降＝H2・maker fill）
            el = i - pend["placed_idx"]
            filled = (h[i] >= pend["limit"]) if side == "SHORT" else (l[i] <= pend["limit"])
            if el > TTL:
                pend = None
            elif el >= 1 and filled:
                lots.append({"side": side, "avg": pend["limit"], "size": UNIT_LOT,
                             "add_count": len(lots) + 1, "first_idx": i, "last_fill_idx": i,
                             "atr_entry": atr_e[i], "adx_entry": adx_e[i], "k_entry": k_e[i],
                             "W_entry": pend["W_pct"], "max_fav": h[i] if side == "LONG" else l[i],
                             "max_adv": l[i] if side == "LONG" else h[i],
                             "pos_frac": pend["pos_frac"], "mid_frac": pend["mid_frac"],
                             "res_zone_pos": np.nan, "ceil_type": pend["ceil_type"],
                             "tp1": pend["tp1"], "tp2": pend["tp2"], "sl": pend["sl"],
                             "tp1_done": False, "be_lvl": np.nan, "be_dl": -1})
                pend = None
        if up[i]:                                          # uptrend 発火＝新規停止（保有は災害SL/TIME が守る・両 side 共通）
            pend = None
        still = []                                         # 出口ループ（約定バーの次以降・SL→TP1→TP2→BE→TIME）
        for lot in lots:
            if i <= lot["last_fill_idx"]:
                still.append(lot); continue
            if side == "LONG":
                lot["max_fav"] = max(lot["max_fav"], h[i]); lot["max_adv"] = min(lot["max_adv"], l[i])
                sl_hit = l[i] <= lot["sl"]; sl_px = min(lot["sl"], o[i])
                tp1_hit = h[i] >= lot["tp1"]; tp2_hit = h[i] >= lot["tp2"]
            else:
                lot["max_fav"] = min(lot["max_fav"], l[i]); lot["max_adv"] = max(lot["max_adv"], h[i])
                sl_hit = h[i] >= lot["sl"]; sl_px = max(lot["sl"], o[i])
                tp1_hit = l[i] <= lot["tp1"]; tp2_hit = l[i] <= lot["tp2"]
            if lot["be_dl"] >= 0:                          # 建値フロア待機中（v31 型・災害SL 併走）
                if sl_hit:
                    e37._record(trades, lot, sl_px, "SL_FILLED", i, ts); continue
                be_hit = (l[i] <= lot["be_lvl"]) if side == "SHORT" else (h[i] >= lot["be_lvl"])
                if be_hit:
                    e37._record(trades, lot, lot["be_lvl"], "BE_EXIT", i, ts); continue
                if i >= lot["be_dl"]:
                    e37._record(trades, lot, c[i], "TIME_EXIT", i, ts); continue
                still.append(lot); continue
            if (i - lot["first_idx"]) >= tmax:             # 時間切れ（be_wait なら建値フロアへ・でなければ成行）
                if be_wait:
                    lot["be_lvl"] = lot["avg"] * (1 - SCALP_FLOOR) if side == "SHORT" else lot["avg"] * (1 + SCALP_FLOOR)
                    lot["be_dl"] = i + BE_TTL_BARS
                    still.append(lot); continue
                e37._record(trades, lot, c[i], "TIME_EXIT", i, ts); continue
            if sl_hit:                                     # 災害SL（maker・悲観側）
                e37._record(trades, lot, sl_px, "SL_FILLED", i, ts); continue
            if (not lot["tp1_done"]) and tp1_hit:          # TP1＝半分（maker）
                half = dict(lot); half["size"] = lot["size"] / 2.0
                e37._record(trades, half, lot["tp1"], "PARTIAL_TP", i, ts)
                lot["size"] = lot["size"] / 2.0; lot["tp1_done"] = True
            if tp2_hit:                                    # TP2＝残り全部（maker）
                e37._record(trades, lot, lot["tp2"], "TP_FILLED", i, ts); continue
            still.append(lot)
        lots = still
        band_ok = ok[i] and np.isfinite(res_hi[i]) and np.isfinite(sup_lo[i]) and np.isfinite(mid[i])
        if (not up[i]) and pend is None and len(lots) < max_lots and band_ok and entry_fn(ctx, i, entry_params):
            if side == "SHORT":
                lim = c[i] * (1 + ENTRY_OFFSET)
                tp2_px = mid[i] if tp2_target == "mid" else sup_hi[i] * (1 + V11_SL_BUF)
                sl_px = res_hi[i] + sl_k * max(res_hi[i] - sup_lo[i], 1e-9)
                tp1_px = lim - (lim - tp2_px) * tp1_frac
                floor_ok = np.isfinite(tp2_px) and tp2_px < lim and (lim - tp1_px) >= lim * SCALP_FLOOR
            else:
                lim = c[i] * (1 - ENTRY_OFFSET)
                tp2_px = mid[i] if tp2_target == "mid" else res_lo[i] * (1 - V11_SL_BUF)
                sl_px = sup_lo[i] - sl_k * max(res_hi[i] - sup_lo[i], 1e-9)
                tp1_px = lim + (tp2_px - lim) * tp1_frac
                floor_ok = np.isfinite(tp2_px) and tp2_px > lim and (tp1_px - lim) >= lim * SCALP_FLOOR
            if floor_ok and np.isfinite(sl_px):            # 手数料床（tp_floor_check の思想・TP1 幅 ≥ SCALP_FLOOR）
                W = max(res_hi[i] - sup_lo[i], 1e-9)
                isdn = bool(np.isfinite(res_lo[i]) and res_lo[i] > c[i] * (1.0 + gap))
                pend = {"limit": lim, "placed_idx": i, "tp1": tp1_px, "tp2": tp2_px, "sl": sl_px,
                        "W_pct": W / c[i] * 100.0, "ceil_type": "down" if isdn else "flat_up",
                        "pos_frac": ((lim - sup_lo[i]) / W) if W > 0 else np.nan,
                        "mid_frac": ((mid[i] - sup_lo[i]) / W) if W > 0 else np.nan}
    for lot in lots:
        e37._record(trades, lot, c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
    for r in trades:
        r["logic"] = logic_id                              # 診断列（net 不関与）
    return trades
