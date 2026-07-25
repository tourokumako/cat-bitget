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


# ---------------------------------------------------------------- S2 確認2軸の部品
# 出典＝S2 層1 観察（observe_diag --scene S2・worklog 20260725 §7）の両半期プラス9組の部品そのまま
# （まこさん GO 2026-07-25）。軸1＝上位足モメンタム非過熱（値が閾値 以下 の時だけ通す）／
# 軸2＝ボラ出来高の床（値が閾値 以上 の時だけ通す）。閾値の実値は層3 が探索窓の分布から決める（手打ちなし）。
HTF_PARTS = ("roc24_2h", "macd_2h", "di7_4h", "adx14_2h", "stochd14_2h")   # ≤ 側
VOL_PARTS = ("volr20_15m", "volr50_15m", "bbw50_1d", "donch20_1d")         # ≥ 側


def _resample_htf(d5: pd.DataFrame, rule: str) -> pd.DataFrame:
    return d5.resample(rule, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()


def _adx_di_htf(h, l, c, n):
    """ADX/DI（Wilder ewm・observe_diag._adx_di と同式＝式のドリフト防止のため出典を固定）。"""
    up, dn = h.diff(), -l.diff()
    p = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=h.index)
    m = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=h.index)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    a = tr.ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * p.ewm(alpha=1 / n, adjust=False).mean() / a
    mdi = 100 * m.ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean(), pdi, mdi


def prepare_df(df: pd.DataFrame, adaptive_k=None) -> pd.DataFrame:
    """部品が使う列を付ける（rsi9・RG-v5/v6 帯列・stoch_d・出来高移動平均・S2 確認2軸の上位足部品）。
    全て確定バーのみ（H2）＝上位足は『足が閉じた時刻』から ffill（observe_diag build_features と同じ方式）。"""
    df = e37._rsi9_v10(df)
    df = e37._apply_rg5_to_5m(df, adaptive_k=adaptive_k)
    df["e38_stoch_d"] = df["stoch_k"].rolling(3).mean()
    df["e38_vol_ma20"] = df["volume"].rolling(20).mean()
    # ★S2 確認2軸の上位足部品（2026-07-25 まこさん GO・観察の9組の部品そのまま・受け身の列＝既存挙動に不関与）
    idx5 = pd.DatetimeIndex(df["ts"])
    d5 = df.set_index(idx5)[["open", "high", "low", "close", "volume"]]

    def _al(s: pd.Series, rule: str):
        s = s.copy()
        s.index = s.index + pd.Timedelta(rule)             # 足が閉じた時刻から有効（未来を見ない）
        return s.reindex(idx5, method="ffill").to_numpy(float)

    d2h, d4h = _resample_htf(d5, "2h"), _resample_htf(d5, "4h")
    d15, d1d = _resample_htf(d5, "15min"), _resample_htf(d5, "1D")
    df["e38_htf_roc24_2h"] = _al(d2h["close"].pct_change(24) * 100.0, "2h")
    df["e38_htf_macd_2h"] = _al((d2h["close"].ewm(span=12).mean() - d2h["close"].ewm(span=26).mean())
                                / d2h["close"] * 100.0, "2h")
    _a4, p4, m4 = _adx_di_htf(d4h["high"], d4h["low"], d4h["close"], 7)
    df["e38_htf_di7_4h"] = _al(p4 - m4, "4h")
    a2, _p2, _m2 = _adx_di_htf(d2h["high"], d2h["low"], d2h["close"], 14)
    df["e38_htf_adx14_2h"] = _al(a2, "2h")
    k14 = 100 * (d2h["close"] - d2h["low"].rolling(14).min()) / (
        d2h["high"].rolling(14).max() - d2h["low"].rolling(14).min()).replace(0, np.nan)
    df["e38_htf_stochd14_2h"] = _al(k14.rolling(3).mean(), "2h")
    df["e38_vol_volr20_15m"] = _al(d15["volume"] / d15["volume"].rolling(20).mean().replace(0, np.nan), "15min")
    df["e38_vol_volr50_15m"] = _al(d15["volume"] / d15["volume"].rolling(50).mean().replace(0, np.nan), "15min")
    df["e38_vol_bbw50_1d"] = _al(2 * 3.0 * d1d["close"].rolling(50).std() / d1d["close"].rolling(50).mean(), "1D")
    df["e38_vol_donch20_1d"] = _al((d1d["high"].rolling(20).max() - d1d["low"].rolling(20).min())
                                   / d1d["close"] * 100.0, "1D")
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
    if not _confirm_2axis(ctx, i, p):
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


def _confirm_2axis(ctx, i, p) -> bool:
    """S2 層1 観察の2軸確認（worklog 20260725 §7・両サイド共通・まこさん GO 2026-07-25）。
    軸1 confirm_htf＝上位足モメンタム非過熱（値 ≤ 閾値）／軸2 confirm_vol＝ボラ出来高の床（値 ≥ 閾値）。
    向きは side 非依存＝「上位足が過熱していない」「短期ボラ/出来高がある」は買い売り両方に効く観察事実。
    None/"none" は素通り（部品未使用）。閾値欠落・未知部品は generic_logic_loop 先頭の番人が実行前に停止。"""
    htf = p.get("confirm_htf") or "none"
    if htf != "none":
        v = ctx[f"htf_{htf}"][i]
        th = p.get(f"th_{htf}")
        if th is None or not (np.isfinite(v) and v <= float(th)):
            return False
    volp = p.get("confirm_vol") or "none"
    if volp != "none":
        v = ctx[f"vol_{volp}"][i]
        th = p.get(f"th_{volp}")
        if th is None or not (np.isfinite(v) and v >= float(th)):
            return False
    return True


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


def _support_touch_long(ctx, i, p):
    """L1 入口改良: 下端 fresh touch（low≤sup_hi ∩ close>sup_lo・帯に入った最初のバー）∩ 2軸確認。
    L1a 観察（worklog 20260725 §19/§20）＝下端タッチ全体で浅い戻り（床×2）の素の勝率 62%・在庫 36バー/日。
    現行 L1（run_long_support）の入口幾何そのまま＋S2 で確立した2軸確認を足す（まこさん承認 2026-07-25）。"""
    if not (ctx["l"][i] <= ctx["sup_hi"][i] and ctx["c"][i] > ctx["sup_lo"][i]):
        return False
    if p.get("fresh_only", True):                          # 帯に入った最初のバー＝1バー1発注（現行 L1 と同じ）
        prev = (ctx["l"][i - 1] <= ctx["sup_hi"][i - 1] and ctx["c"][i - 1] > ctx["sup_lo"][i - 1])
        if prev:
            return False
    return _confirm_2axis(ctx, i, p)


ENTRY_FNS = {
    "pullback_short": ("SHORT", _pullback_short),
    "fade_short": ("SHORT", _fade_short),
    "zscore_short": ("SHORT", _zscore_short),
    "crash_rebound_long": ("LONG", _crash_rebound_long),
    "fade_long": ("LONG", _fade_long),
    "zscore_long": ("LONG", _zscore_long),
    "support_touch_long": ("LONG", _support_touch_long),
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
    for _pt in HTF_PARTS:                                  # S2 確認2軸（2026-07-25 まこさん GO）
        ctx[f"htf_{_pt}"] = df[f"e38_htf_{_pt}"].to_numpy(float)
    for _pt in VOL_PARTS:
        ctx[f"vol_{_pt}"] = df[f"e38_vol_{_pt}"].to_numpy(float)
    _ch = entry_params.get("confirm_htf") or "none"        # 番人＝未知の部品名・閾値欠落は走らせない
    _cv = entry_params.get("confirm_vol") or "none"
    if _ch != "none":
        if _ch not in HTF_PARTS:
            raise SystemExit(f"[設定エラー] confirm_htf に未知の部品: {_ch}（使えるのは {('none',) + HTF_PARTS}）")
        if entry_params.get(f"th_{_ch}") is None:
            raise SystemExit(f"[設定エラー] confirm_htf={_ch} なのに閾値 th_{_ch} が無い")
    if _cv != "none":
        if _cv not in VOL_PARTS:
            raise SystemExit(f"[設定エラー] confirm_vol に未知の部品: {_cv}（使えるのは {('none',) + VOL_PARTS}）")
        if entry_params.get(f"th_{_cv}") is None:
            raise SystemExit(f"[設定エラー] confirm_vol={_cv} なのに閾値 th_{_cv} が無い")
    ceil_filter = entry_params.get("ceil_filter")          # ★型の限定（S2=flat_up 専用・まこさん承認 2026-07-25
    if ceil_filter not in (None, "down", "flat_up"):       #   ＝値決め窓で down −$28/flat_up +$284 の型別差が根拠）
        raise SystemExit(f"[設定エラー] ceil_filter が不正: {ceil_filter}（None / down / flat_up）")
    ok = df["range_ok_rg5"].to_numpy(bool); up = df["rg5_uptrend"].to_numpy(bool)
    atr_e, adx_e, k_e = ctx["atr"], ctx["adx"], ctx["k"]
    res_lo, res_hi, sup_lo, sup_hi, mid = ctx["res_lo"], ctx["res_hi"], ctx["sup_lo"], ctx["sup_hi"], ctx["mid"]
    tp1_frac = float(exit_params["tp1_frac"]); tp2_target = exit_params["tp2_target"]
    sl_k = float(exit_params["sl_zone_k"]); tmax = int(exit_params["tmax_bars"])
    be_wait = bool(exit_params.get("be_wait", 0))
    # ★tp_mode（2026-07-25 まこさん承認「段3 のセット粗探索をやり直し」）:
    #   zone＝レンジ幾何の2段TP（従来・既定＝恒等）／ pct＝建値からの固定% 1段TP（スキャル幾何・全量 maker）。
    #   pct は床×tp_pct_k（k≥1＝手数料床割れの物理禁止）。時間の枠（5〜60分）と噛み合う値幅で決まる出口。
    tp_mode = exit_params.get("tp_mode", "zone")
    tp_k = float(exit_params.get("tp_pct_k") or 0.0)
    if tp_mode not in ("zone", "pct"):
        raise SystemExit(f"[設定エラー] tp_mode が不正: {tp_mode}（zone / pct）")
    if tp_mode == "pct" and tp_k < 1.0:
        raise SystemExit(f"[設定エラー] tp_mode=pct なのに tp_pct_k が 1.0 未満か未指定: {tp_k}（床割れ TP の禁止）")
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
                             "tp1_done": (tp_mode == "pct"),   # pct＝1段TP（全量）＝TP1 段階なし
                             "be_lvl": np.nan, "be_dl": -1})
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
                sl_px = res_hi[i] + sl_k * max(res_hi[i] - sup_lo[i], 1e-9)
                if tp_mode == "pct":                       # スキャル幾何＝建値から床×k の1段TP（全量 maker）
                    tp2_px = lim * (1 - tp_k * SCALP_FLOOR)
                    tp1_px = tp2_px
                    floor_ok = True                        # k≥1 は先頭の番人で保証＝床割れなし
                else:
                    tp2_px = mid[i] if tp2_target == "mid" else sup_hi[i] * (1 + V11_SL_BUF)
                    tp1_px = lim - (lim - tp2_px) * tp1_frac
                    floor_ok = np.isfinite(tp2_px) and tp2_px < lim and (lim - tp1_px) >= lim * SCALP_FLOOR
            else:
                lim = c[i] * (1 - ENTRY_OFFSET)
                sl_px = sup_lo[i] - sl_k * max(res_hi[i] - sup_lo[i], 1e-9)
                if tp_mode == "pct":
                    tp2_px = lim * (1 + tp_k * SCALP_FLOOR)
                    tp1_px = tp2_px
                    floor_ok = True
                else:
                    tp2_px = mid[i] if tp2_target == "mid" else res_lo[i] * (1 - V11_SL_BUF)
                    tp1_px = lim + (tp2_px - lim) * tp1_frac
                    floor_ok = np.isfinite(tp2_px) and tp2_px > lim and (tp1_px - lim) >= lim * SCALP_FLOOR
            if floor_ok and np.isfinite(sl_px):            # 手数料床（tp_floor_check の思想・TP1 幅 ≥ SCALP_FLOOR）
                W = max(res_hi[i] - sup_lo[i], 1e-9)
                isdn = bool(np.isfinite(res_lo[i]) and res_lo[i] > c[i] * (1.0 + gap))
                ctype = "down" if isdn else "flat_up"
                if ceil_filter is not None and ctype != ceil_filter:
                    continue                               # 型の限定＝指定と違う型では建てない（S2 flat_up 専用）
                pend = {"limit": lim, "placed_idx": i, "tp1": tp1_px, "tp2": tp2_px, "sl": sl_px,
                        "W_pct": W / c[i] * 100.0, "ceil_type": ctype,
                        "pos_frac": ((lim - sup_lo[i]) / W) if W > 0 else np.nan,
                        "mid_frac": ((mid[i] - sup_lo[i]) / W) if W > 0 else np.nan}
    for lot in lots:
        e37._record(trades, lot, c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
    for r in trades:
        r["logic"] = logic_id                              # 診断列（net 不関与）
    return trades
