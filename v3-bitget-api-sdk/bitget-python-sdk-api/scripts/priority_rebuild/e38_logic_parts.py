#!/usr/bin/env python3
"""e38_logic_parts.py — E38 候補ロジックの汎用売買部品（段2・まこさん GO 2026-07-24・設計 e38_design.md／グリッド節 E38）

run_long_support（e37_scalp.py 1569行〜）の型を側対称に一般化した単純な売買ループ1本＋入口関数テーブル。
入口条件だけを e38_logics.json の entry.type / entry.params で差し替える（設定駆動）。
出口は共通部品＝PARTIAL_TP 半分・TP2・災害SL（帯幾何）・TIME・建値フロア待機（v31 型 BE_EXIT）＝新しい出口軸を作らない。
決済の maker/taker・funding・売買記録の列構成は e37._record を import 再利用（score.py 登録済み exit_reason のみ＝H13 無変更）。
シグナルは全て当該バーまでの確定値・約定は次バー以降（H2）。maker 指値・TTL 3本・1バー1発注・手数料床 SCALP_FLOOR。

S4 の注記（まこさん報告済み 2026-07-24）: dev_z=(close−SMA20)/std20 は BB20 の kσ と同じ窓の標準化＝数学的に同値なので
指標カテゴリは dev_z に一本化した（別窓の BB を足す時は entry.params に窓を持たせて拡張する）。
S5/L5 グリッドは売買構造が別物（複数 resting・在庫管理）＝generic_logic_loop に押し込まず、別の関数 grid_loop が持つ
（要件 R2・まこさん OK 2026-08-04。2026-08-03 までは json に名前だけで実装が無く、enabled にすると設定エラーで停止していた）。
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


def prepare_df(df: pd.DataFrame, adaptive_k=None, h1_edge: str = "right") -> pd.DataFrame:
    """部品が使う列を付ける（rsi9・RG-v5/v6 帯列・stoch_d・出来高移動平均・S2 確認2軸の上位足部品）。
    全て確定バーのみ（H2）＝上位足は『足が閉じた時刻』から ffill（observe_diag build_features と同じ方式）。"""
    df = e37._rsi9_v10(df)
    # ★2026-10-20（工事 m2c15-band-s1-20261020・F-4）＝帯の1時間足の区切り（right＝今・hour＝正時）。既定は今のまま
    df = e37._apply_rg5_to_5m(df, adaptive_k=adaptive_k, h1_edge=h1_edge)
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


_REGIME_CACHE: dict = {}


def config_regime() -> dict:
    """E38 が担当する相場の宣言を、自分の設定ファイル e38_logics.json から読む。

    ★なぜこれを足したか（監査 4-19／要件 R5・2026-08-03）
      それまで、この売買ループの中には レンジ判定の列の名前 range_ok_rg5 が直接書いてありました。
      だから、レンジ以外の相場を扱えませんでした。監査の逐語はこうです。
        「局面の判定はレンジに固定です。共通の売買ループが range_ok_rg5 を前提にしています」
      いまは設定ファイルに書いてある名前を読みます。値はいままでと同じです。
    """
    if not _REGIME_CACHE:
        import json as _json
        import pathlib as _pl
        cfg = _json.loads((_pl.Path(__file__).resolve().parent / "e38_logics.json").read_text(encoding="utf-8"))
        rg = (cfg.get("global") or {}).get("regime") or {}
        for k in ("name", "entry_col", "block_col"):
            _REGIME_CACHE[k] = rg.get(k)
        if not _REGIME_CACHE.get("entry_col"):
            raise SystemExit("[相場の宣言エラー] e38_logics.json の global.regime に entry_col がありません")
    return dict(_REGIME_CACHE)


def generic_logic_loop(df: pd.DataFrame, entry_type: str, entry_params: dict, exit_params: dict,
                       max_lots: int = 2, logic_id: str = "", regime: dict | None = None) -> list:
    """汎用売買ループ（run_long_support の側対称一般化）。

    regime … この売買が担当する相場の宣言（監査 4-19／要件 R5・2026-08-03 追加）。
             省略したときは、自分の設定ファイル e38_logics.json の global.regime を読む。

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
    # ★相場の列は宣言から読む（監査 4-19／要件 R5＝直書きをやめた）。列が無ければ走らせない。
    _rg = dict(regime) if regime else config_regime()
    _ent, _blk = _rg.get("entry_col"), _rg.get("block_col")
    if _ent not in df.columns:
        raise SystemExit(f"[相場の列が無い] 玉を建ててよいバーの列 {_ent} がデータにありません"
                         f"（宣言された相場＝{_rg.get('name')}）")
    if _blk is not None and _blk not in df.columns:
        raise SystemExit(f"[相場の列が無い] 新規の発注を止める列 {_blk} がデータにありません")
    ok = df[_ent].to_numpy(bool)
    up = df[_blk].to_numpy(bool) if _blk is not None else np.zeros(len(df), dtype=bool)
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


# ---------------------------------------------------------------- グリッド売買（S5・L5＝要件 R2）

GRID_ENTRY_TYPES = {"grid_short": "SHORT", "grid_long": "LONG"}


def _grid_rec(trades: list, lot: dict, px: float, reason: str, i: int, ts_arr) -> None:
    """記録は E37 の記録処理を借りる（手数料の分類の見張りの前提＝e37._record( を呼ぶ形を維持）。
    そのうえで、どの線で建った玉かの診断列 grid_level を1行に足す（net 不関与）。"""
    e37._record(trades, lot, px, reason, i, ts_arr)
    trades[-1]["grid_level"] = int(lot["grid_level"])


def grid_loop(df: pd.DataFrame, entry_type: str, entry_params: dict, exit_params: dict,
              max_lots: int = 2, logic_id: str = "", regime: dict | None = None) -> list:
    """グリッド売買ループ（S5 売り・L5 買い・要件 R2・まこさん OK 2026-08-04）。

    generic_logic_loop と何が違うか
      あちらは発注中の指値を1つしか持てない（pend が1個）。グリッドは、レンジの半分を等間隔に
      区切った線それぞれに resting の指値を置き続ける型なので、複数の指値を同時に管理する。
      置き直しは毎バー（実運用のキャンセル→再発注に対応）。約定の判定は置いた次のバーから（H2）。

    どの範囲に線を引くか（ロジック固定＝e38_logics.json のラベルどおり）
      grid_short（S5）… レンジ中央 mid から上端 res_hi の間（上半分に売り）
      grid_long （L5）… 下端帯上端 sup_hi から中央 mid の間（下半分に買い）

    値
      entry_params: grid_n   … 線の本数（1以上の整数。範囲の宣言は e38_logics.json search_space が正本）
      exit_params : sl_zone_k … 災害SL＝ゾーン外側 + k×帯幅（generic_logic_loop と同じ幾何）
                    tmax_bars … 時間切れ（5分足の本数・成行 taker）
      利確＝1段下（買いは1段上）の線への resting maker（TP_FILLED）。
      線の間隔が手数料床 SCALP_FLOOR（0.08%）を割る密度では発注しない（床割れ TP の物理禁止）。
      いまの値段をまたぐ線には置かない（置いた瞬間に成行になる指値の禁止＝maker 保証）。

    決済理由は登録済みの4種（TP_FILLED / SL_FILLED / TIME_EXIT / FORCE_CLOSE_EOD）だけ
    ＝審判 score.py は無変更（H13）。記録は e37._record を借りる（_grid_rec 経由）。
    """
    if entry_type not in GRID_ENTRY_TYPES:
        raise SystemExit(f"[設定エラー] grid_loop に未知の entry type: {entry_type}"
                         f"（使えるのは {tuple(GRID_ENTRY_TYPES)}）")
    side = GRID_ENTRY_TYPES[entry_type]
    gn = entry_params.get("grid_n")
    if not isinstance(gn, (int, np.integer)) or isinstance(gn, bool) or gn < 1:
        raise SystemExit(f"[設定エラー] grid_n が未確定か不正: {gn}（1以上の整数・範囲の確定はまこさん）")
    gn = int(gn)
    for _k in ("sl_zone_k", "tmax_bars"):
        if exit_params.get(_k) is None:
            raise SystemExit(f"[設定エラー] grid_loop の出口の値が無い: {_k}")
    sl_k = float(exit_params["sl_zone_k"]); tmax = int(exit_params["tmax_bars"])

    o = df["open"].to_numpy(float); h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    ts = df["ts"].to_numpy()
    atr_e = df["atr"].to_numpy(float); adx_e = df["adx"].to_numpy(float); k_e = df["stoch_k"].to_numpy(float)
    res_lo = df["v11_res_lo"].to_numpy(float); res_hi = df["v11_res_hi"].to_numpy(float)
    sup_lo = df["v11_sup_lo"].to_numpy(float); sup_hi = df["v11_sup_hi"].to_numpy(float)
    mid = df["v11_mid"].to_numpy(float)

    # 相場の列は宣言から読む（要件 R5 と同じ決まり・直書きしない）。列が無ければ走らせない。
    _rg = dict(regime) if regime else config_regime()
    _ent, _blk = _rg.get("entry_col"), _rg.get("block_col")
    if _ent not in df.columns:
        raise SystemExit(f"[相場の列が無い] 玉を建ててよいバーの列 {_ent} がデータにありません"
                         f"（宣言された相場＝{_rg.get('name')}）")
    if _blk is not None and _blk not in df.columns:
        raise SystemExit(f"[相場の列が無い] 新規の発注を止める列 {_blk} がデータにありません")
    ok = df[_ent].to_numpy(bool)
    up = df[_blk].to_numpy(bool) if _blk is not None else np.zeros(len(df), dtype=bool)

    gap = 0.5 / 100.0                                      # 型判定 gap（generic_logic_loop と同じ・診断列用）
    n = len(df); trades: list = []; lots: list = []
    pend: dict = {}                                        # 線の番号 → resting 指値（前のバーに置いた分だけが約定対象）
    for i in range(1, n):
        # ── ① 約定（前のバーで置いた指値だけ＝H2。触れた線は全部このバーで約定＝複数の指値の同時管理）──
        for lv, od in sorted(pend.items(), key=lambda kv: kv[1]["limit"], reverse=(side == "LONG")):
            if i - od["placed_idx"] < 1:                   # 置いたバーでは約定しない（構造上も置き直しは後段）
                continue
            filled = (h[i] >= od["limit"]) if side == "SHORT" else (l[i] <= od["limit"])
            if not filled or len(lots) >= max_lots:        # 在庫の上限（置く数も後段で制限＝二重の守り）
                continue
            lots.append({"side": side, "avg": od["limit"], "size": UNIT_LOT,
                         "add_count": len(lots) + 1, "first_idx": i, "last_fill_idx": i,
                         "atr_entry": atr_e[i], "adx_entry": adx_e[i], "k_entry": k_e[i],
                         "W_entry": od["W_pct"], "max_fav": h[i] if side == "LONG" else l[i],
                         "max_adv": l[i] if side == "LONG" else h[i],
                         "pos_frac": od["pos_frac"], "mid_frac": od["mid_frac"],
                         "res_zone_pos": np.nan, "ceil_type": od["ceil_type"],
                         "tp": od["tp"], "sl": od["sl"], "grid_level": lv})
        # ── ② 出口（約定バーの次以降・TIME → SL → TP の順＝generic_logic_loop と同じ悲観側）──
        still = []
        for lot in lots:
            if i <= lot["last_fill_idx"]:
                still.append(lot); continue
            if side == "LONG":
                lot["max_fav"] = max(lot["max_fav"], h[i]); lot["max_adv"] = min(lot["max_adv"], l[i])
                sl_hit = l[i] <= lot["sl"]; sl_px = min(lot["sl"], o[i]); tp_hit = h[i] >= lot["tp"]
            else:
                lot["max_fav"] = min(lot["max_fav"], l[i]); lot["max_adv"] = max(lot["max_adv"], h[i])
                sl_hit = h[i] >= lot["sl"]; sl_px = max(lot["sl"], o[i]); tp_hit = l[i] <= lot["tp"]
            if (i - lot["first_idx"]) >= tmax:             # 時間切れ（成行 taker）
                _grid_rec(trades, lot, c[i], "TIME_EXIT", i, ts); continue
            if sl_hit:                                     # 災害SL（maker・悲観側の約定価格）
                _grid_rec(trades, lot, sl_px, "SL_FILLED", i, ts); continue
            if tp_hit:                                     # 1段戻りの利確（resting maker）＝在庫が減る
                _grid_rec(trades, lot, lot["tp"], "TP_FILLED", i, ts); continue
            still.append(lot)
        lots = still
        # ── ③ 置き直し（毎バーのキャンセル→再発注。約定の判定は次のバー＝H2）──
        pend = {}
        if up[i] or not ok[i]:                             # 新規停止（保有は SL/TIME が守る）
            continue
        lo_b = mid[i] if side == "SHORT" else sup_hi[i]
        hi_b = res_hi[i] if side == "SHORT" else mid[i]
        if not (np.isfinite(lo_b) and np.isfinite(hi_b) and hi_b > lo_b
                and np.isfinite(res_hi[i]) and np.isfinite(sup_lo[i])):
            continue
        step = (hi_b - lo_b) / (gn + 1)
        if step < c[i] * SCALP_FLOOR:                      # 手数料床＝TP1段（=step）が床を割る密度では置かない
            continue
        W = max(res_hi[i] - sup_lo[i], 1e-9)
        isdn = bool(np.isfinite(res_lo[i]) and res_lo[i] > c[i] * (1.0 + gap))
        ctype = "down" if isdn else "flat_up"
        sl_px = res_hi[i] + sl_k * W if side == "SHORT" else sup_lo[i] - sl_k * W
        if not np.isfinite(sl_px):
            continue
        occupied = {lot["grid_level"] for lot in lots}     # 玉が居る線には置き直さない（在庫の管理）
        budget = max_lots - len(lots)                      # 置く数 ≤ 空き在庫＝全部約定しても上限を超えない
        for lv in range(1, gn + 1):                        # 1=価格に近い側（売りは下から・買いは上から）
            if budget <= 0:
                break
            if lv in occupied:
                continue
            lim = lo_b + lv * step if side == "SHORT" else hi_b - lv * step
            if not (lim > c[i] if side == "SHORT" else lim < c[i]):
                continue                                   # いまの値段をまたぐ線には置かない（maker 保証）
            pend[lv] = {"limit": lim, "tp": (lim - step) if side == "SHORT" else (lim + step),
                        "sl": sl_px, "placed_idx": i, "W_pct": W / c[i] * 100.0,
                        "pos_frac": ((lim - sup_lo[i]) / W) if W > 0 else np.nan,
                        "mid_frac": ((mid[i] - sup_lo[i]) / W) if W > 0 else np.nan,
                        "ceil_type": ctype}
            budget -= 1
    for lot in lots:
        _grid_rec(trades, lot, c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
    for r in trades:
        r["logic"] = logic_id                              # 診断列（net 不関与）
    return trades


# ---------------------------------------------------------------- grid_loop の番人（合成データの既知答え）

def _selftest_grid() -> None:
    """grid_loop の番人5件（全部 合成データ・実データゼロ・CSV を書かない）。落ちたら SystemExit。"""
    def mk(bars, res_hi=110.0):
        d = pd.DataFrame({
            "ts": pd.date_range("2024-06-03", periods=len(bars), freq="5min"),
            "open": [b[0] for b in bars], "high": [b[1] for b in bars],
            "low": [b[2] for b in bars], "close": [b[3] for b in bars],
            "volume": 1.0, "atr": 1.0, "adx": 20.0, "stoch_k": 50.0,
            "v11_res_lo": 109.0, "v11_res_hi": res_hi,
            "v11_sup_lo": 100.0, "v11_sup_hi": 101.0, "v11_mid": 105.0,
            "g_ok": True,
        })
        return d

    rg = {"name": "range", "entry_col": "g_ok", "block_col": None}
    xp = {"sl_zone_k": 1.0, "tmax_bars": 12}
    flat = (105.0, 105.0, 105.0, 105.0)

    # 番人1: 1本のバーで2つの線に同時に約定（在庫 0→2→0）→ 空いた線に置き直して再約定（在庫 0→1→0）
    #   線（grid_n=2・mid105〜res_hi110・間隔 5/3≒1.667）＝106.67 と 108.33。TP は各1段下＝105.00 と 106.67。
    bars = [flat, flat, (105, 109, 105, 108), (108, 108, 104.9, 105), flat,
            (105, 107, 105, 106), (106, 106, 104.9, 105), flat]
    t = grid_loop(mk(bars), "grid_short", {"grid_n": 2}, xp, max_lots=4, logic_id="S5", regime=rg)
    assert len(t) == 3 and all(r["exit_reason"] == "TP_FILLED" for r in t), f"番人1: 3玉 TP のはず: {t}"
    assert sorted(r["add_count"] for r in t) == [1, 1, 2], f"番人1: 同時在庫が 2 に達していない: {[r['add_count'] for r in t]}"
    assert len({r["entry_time"] for r in t}) == 2, "番人1: 同時約定（同じ entry_time の2玉）が出ていない"
    assert sorted(r["grid_level"] for r in t) == [1, 1, 2], "番人1: 線の割り当て（lv1×2・lv2×1）が違う"
    print("  ✅ 番人1: 複数の指値の同時約定（在庫 0→2→0）と置き直し（0→1→0）が売買記録に出た")

    # 番人2: 在庫の上限＝max_lots=1 なら同じ相場でも約定は1玉だけ（置く数の制限が効く）
    t = grid_loop(mk(bars), "grid_short", {"grid_n": 2}, xp, max_lots=1, logic_id="S5", regime=rg)
    assert all(r["add_count"] == 1 for r in t), f"番人2: 上限1なのに同時在庫が2以上: {[r['add_count'] for r in t]}"
    print("  ✅ 番人2: 在庫の上限（max_lots）を超えない")

    # 番人3: 手数料の床＝帯が狭くて線の間隔が床 0.08% を割るなら発注ゼロ（触れても約定しない）
    t = grid_loop(mk([flat, flat, (105, 105.09, 105, 105.05), flat], res_hi=105.1),
                  "grid_short", {"grid_n": 2}, xp, max_lots=4, logic_id="S5", regime=rg)
    assert t == [], f"番人3: 床割れの密度で発注された: {t}"
    print("  ✅ 番人3: 線の間隔が手数料床を割る置き方はしない")

    # 番人4: H2＝置いたバーでは約定しない（最初の置き直しと同じバーの急騰では建たない）
    t = grid_loop(mk([flat, (105, 120, 105, 105), flat]), "grid_short", {"grid_n": 2}, xp,
                  max_lots=4, logic_id="S5", regime=rg)
    assert t == [], f"番人4: 置いたバーで約定した（H2 違反）: {t}"
    print("  ✅ 番人4: 置いたバーでは約定しない（約定は次のバーから＝H2）")

    # 番人5: L5（買い）の対称＝下半分（sup_hi101〜mid105・間隔 4/3≒1.333）の線 103.67 と 102.33
    bars_l = [flat, flat, (105, 105, 101, 102), (102, 105.2, 102, 105), flat]
    t = grid_loop(mk(bars_l), "grid_long", {"grid_n": 2}, xp, max_lots=4, logic_id="L5", regime=rg)
    assert len(t) == 2 and all(r["exit_reason"] == "TP_FILLED" for r in t), f"番人5: {t}"
    assert sorted(r["add_count"] for r in t) == [1, 2], "番人5: 買い側で同時在庫2が出ていない"
    print("  ✅ 番人5: 買い側（L5）も上下対称に動く")
    print("[grid_loop 番人] 5件とも既知答えと一致（全部 合成データ・実データゼロ・CSV なし）")


def _grid_demo() -> None:
    """S5 と L5 を確認用の値で値決め窓を1回走らせる（R2 完了の線の実証・採否に使わない・CSV は書かない）。

    確認用の値は構造から決めた（net で選んでいない・L-267）:
      grid_n=2      … 「複数の指値の同時管理」を示せる最小の本数
      sl_zone_k=1.0 … 採用中の L1 と同じ値（e38_logics.json L1.params.sl_zone_k）
      tmax_bars=12  … scalp の役割の保有上限（60分・recipes/search_limits.json の hold_bars_by_role）
    """
    import periods
    import score as judge
    from tuner_adapters import e38 as ad
    print(f"[grid demo] 窓＝値決め窓 {periods.SEARCH_START.date()}〜{periods.SEARCH_END.date()}"
          f"（採点窓 {periods.SCORE_START.date()} 以降は不使用・L-267）")
    dfp = ad.load_windows([(periods.SEARCH_START, periods.SEARCH_END)], pd.Timedelta(days=60))[0]
    days = max((periods.SEARCH_END - periods.SEARCH_START).days, 1)
    for logic_id, etype in (("S5", "grid_short"), ("L5", "grid_long")):
        tr = grid_loop(dfp, etype, {"grid_n": 2}, {"sl_zone_k": 1.0, "tmax_bars": 12},
                       max_lots=2, logic_id=logic_id, regime=ad.regime(logic_id))
        t = pd.DataFrame(tr)
        if len(t):
            et = pd.to_datetime(t["entry_time"])
            t = t[(et >= periods.SEARCH_START) & (et < periods.SEARCH_END)].reset_index(drop=True)
        if not len(t):
            print(f"[grid demo] {logic_id}: 窓内の売買 0 行")
            continue
        multi = int((t.groupby("entry_time").size() >= 2).sum())
        rearm = {int(k): int(v) for k, v in t["grid_level"].value_counts().sort_index().items()}
        reasons = {k: int(v) for k, v in t["exit_reason"].value_counts().items()}
        res = judge.score(t)                               # 審判が通る実証（未登録の決済理由なら STOP する）
        print(f"[grid demo] {logic_id}: {len(t)} 玉 ／ {len(t) / days:.2f} 件/日 ／ 保有中央値 "
              f"{float(t['hold_min'].median()):.0f} 分")
        print(f"  同時在庫の最大 {int(t['add_count'].max())} 玉 ／ 同じバーで2玉以上 同時に建った回数 {multi} 回"
              f" ／ 線ごとの約定回数 {rearm}（同じ線の2回目以降＝置き直し後の再約定＝在庫の増減）")
        print(f"  決済理由の内訳 {reasons}（全部 審判 score.py に登録済み）")
        print(f"  審判の net 合計 {res['total']:+.2f}（★確認用の値の1走＝採否に使わない・比較しない）")
    print("[grid demo] CSV は書いていない・採点していない・試行の累積は増えていない")


# ── H2 実行時の守り（2026-08-16 まこさん GO「H2 完全化」の層3・穴④）──────────────────
#    自分のコードに未来参照の典型（shift にマイナスの数字・rolling の center を True）が無いことを、
#    読み込みのたびに ratchet_guards で機械確認する。違反が入ると import の瞬間に止まる＝
#    偽の数字を出す前に落ちる。説明文では誤発火しない（行内コメントを外してから見る）。
import pathlib as _h2_pathlib                            # noqa: E402
import ratchet_guards as _h2_rg                          # noqa: E402
_h2_rg.assert_no_future_ref(_h2_pathlib.Path(__file__).read_text(encoding="utf-8"))


if __name__ == "__main__":
    import argparse
    _ap = argparse.ArgumentParser(description="E38 汎用売買部品（grid_loop の番人と動作実測だけを持つ・本走の口は無い）")
    _ap.add_argument("--selftest", action="store_true", help="grid_loop の番人5件（合成データのみ・既知答え）")
    _ap.add_argument("--selftest-grid-demo", action="store_true",
                     help="S5/L5 を確認用の値で値決め窓を1回走らせる（R2 完了の線の実証・CSV は書かない・採否に使わない）")
    _a = _ap.parse_args()
    if _a.selftest:
        _selftest_grid()
    if _a.selftest_grid_demo:
        _grid_demo()
    if not (_a.selftest or _a.selftest_grid_demo):
        _ap.print_help()
