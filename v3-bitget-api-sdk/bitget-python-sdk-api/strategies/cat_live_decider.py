from __future__ import annotations

from math import sqrt
from typing import Any, Dict, List, Tuple


# ===== 固定（Phase1/2で合意済み）=====
SIDE_DEFAULT = "LONG"
SIDE_SHORT = "SHORT"
SIZE_DEFAULT = "0.0001"

# （削除）TP/SLは runner 側の責務（strategyは判断のみ）

ADX_MIN_P1 = 25.0
STOCH_DIFF_MIN = 0.3


def _to_f(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return float("nan")


def _parse_candles(candles_5m: List[List[str]]) -> Tuple[List[float], List[float], List[float], List[float], List[float]]:
    # [ts, open, high, low, close, volume, quoteVol]
    o, h, l, c, ts = [], [], [], [], []
    for row in candles_5m:
        if not isinstance(row, list) or len(row) < 5:
            continue
        ts.append(_to_f(row[0]))
        o.append(_to_f(row[1]))
        h.append(_to_f(row[2]))
        l.append(_to_f(row[3]))
        c.append(_to_f(row[4]))
    return ts, o, h, l, c


def _sma(vals: List[float], n: int) -> float:
    if len(vals) < n:
        return float("nan")
    w = vals[-n:]
    return sum(w) / n


def _std(vals: List[float], n: int) -> float:
    # ddof=0（母分散）: BB系はこれ（taのBBに寄せる想定）
    if len(vals) < n:
        return float("nan")
    w = vals[-n:]
    m = sum(w) / n
    v = sum((x - m) ** 2 for x in w) / n
    return sqrt(v)


def _std_ddof1(vals: List[float], n: int) -> float:
    # ddof=1（標本分散）: CAT_v8_01 の rolling.std()（既定ddof=1）に合わせる
    if len(vals) < n:
        return float("nan")
    if n <= 1:
        return float("nan")
    w = vals[-n:]
    m = sum(w) / n
    v = sum((x - m) ** 2 for x in w) / (n - 1)
    return sqrt(v)


def _ema_series(vals: List[float], n: int) -> List[float]:
    # standard EMA with alpha = 2/(n+1)
    if not vals:
        return []
    alpha = 2.0 / (n + 1.0)
    out = [vals[0]]
    for x in vals[1:]:
        out.append(alpha * x + (1.0 - alpha) * out[-1])
    return out

def _stoch_kd(highs: List[float], lows: List[float], closes: List[float], n: int = 14, d_n: int = 3) -> Tuple[List[float], List[float]]:
    # %K and %D (simple smoothing on K)
    if len(closes) < n:
        nan = [float("nan")] * len(closes)
        return nan, nan

    k = [float("nan")] * len(closes)
    for i in range(n - 1, len(closes)):
        hh = max(highs[i - n + 1 : i + 1])
        ll = min(lows[i - n + 1 : i + 1])
        if hh == ll:
            k[i] = 0.0
        else:
            k[i] = 100.0 * (closes[i] - ll) / (hh - ll)

    d = [float("nan")] * len(closes)
    for i in range(n - 1 + d_n - 1, len(closes)):
        w = [x for x in k[i - d_n + 1 : i + 1] if x == x]
        d[i] = sum(w) / len(w) if w else float("nan")

    return k, d


def _adx_series(highs: List[float], lows: List[float], closes: List[float], n: int = 14) -> List[float]:
    """
    ta.trend.ADXIndicator(window=n, fillna=False) と同型のADX系列を返す（index合わせ含む）
    - 返却長は len(closes)
    - 初期は 0.0 が入る（ta実装が np.zeros を concat するため）
    """
    L = len(closes)
    if n <= 0:
        return [float("nan")] * L
    if L < (n + 1):
        return [float("nan")] * L

    # close_shift (= close.shift(1))
    close_shift = [float("nan")] * L
    for i in range(1, L):
        close_shift[i] = closes[i - 1]

    # TR相当：max(high, prev_close) - min(low, prev_close)（taの_runと同型）
    diff_dm = [float("nan")] * L
    for i in range(L):
        pc = close_shift[i]
        if pc != pc:
            continue
        pdm = highs[i] if highs[i] >= pc else pc
        pdn = lows[i] if lows[i] <= pc else pc
        diff_dm[i] = pdm - pdn

    trs_initial = [0.0] * (n - 1)
    trs_len = L - (n - 1)
    trs = [0.0] * trs_len

    # trs[0] = diff_dm.dropna().iloc[0:n].sum() 相当（= 元系列の i=1..n の和）
    trs[0] = sum(diff_dm[1 : n + 1])

    # Wilder smoothing（taは range(1, len(trs)-1) で最後は未更新=0のまま）
    for i in range(1, trs_len - 1):
        trs[i] = trs[i - 1] - (trs[i - 1] / float(n)) + diff_dm[n + i]

    # +DM / -DM（taのpos/negと同型）
    diff_up = [float("nan")] * L
    diff_down = [float("nan")] * L
    for i in range(1, L):
        diff_up[i] = highs[i] - highs[i - 1]
        diff_down[i] = lows[i - 1] - lows[i]

    pos = [float("nan")] * L
    neg = [float("nan")] * L
    for i in range(1, L):
        up = diff_up[i]
        dn = diff_down[i]
        if up != up or dn != dn:
            continue
        pos[i] = abs(up) if (up > dn and up > 0) else 0.0
        neg[i] = abs(dn) if (dn > up and dn > 0) else 0.0

    dip = [0.0] * trs_len
    din = [0.0] * trs_len
    dip[0] = sum(pos[1 : n + 1])
    din[0] = sum(neg[1 : n + 1])

    for i in range(1, trs_len - 1):
        dip[i] = dip[i - 1] - (dip[i - 1] / float(n)) + pos[n + i]
        din[i] = din[i - 1] - (din[i - 1] / float(n)) + neg[n + i]

    # DI%
    di_plus = [0.0] * trs_len
    di_minus = [0.0] * trs_len
    for idx, trv in enumerate(trs):
        if trv != 0:
            di_plus[idx] = 100.0 * (dip[idx] / trv)
            di_minus[idx] = 100.0 * (din[idx] / trv)
        else:
            di_plus[idx] = 0.0
            di_minus[idx] = 0.0

    # DX (= directional_index)
    dx = [0.0] * trs_len
    for idx in range(trs_len):
        den = di_plus[idx] + di_minus[idx]
        dx[idx] = 0.0 if den == 0 else 100.0 * abs((di_plus[idx] - di_minus[idx]) / den)

    # ADX（ta: adx_series[n] = mean(dx[0:n]); 以降は dx[i-1] を入れる）
    adx_series = [0.0] * trs_len
    if trs_len > n:
        adx_series[n] = sum(dx[0:n]) / float(n)
        for i in range(n + 1, trs_len):
            adx_series[i] = ((adx_series[i - 1] * (n - 1)) + dx[i - 1]) / float(n)

    # concat(trs_initial, adx_series) で元系列長に復元
    out = trs_initial + adx_series
    # 念のため長さ合わせ
    if len(out) < L:
        out += [0.0] * (L - len(out))
    elif len(out) > L:
        out = out[:L]
    return out


def _rank_avg_ties(vals: List[float]) -> List[float]:
    # average-rank for ties
    pairs = sorted([(v, i) for i, v in enumerate(vals)], key=lambda x: x[0])
    ranks = [0.0] * len(vals)
    i = 0
    r = 1
    while i < len(pairs):
        j = i
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        # ranks r..r+(j-i)-1 -> average
        avg = (r + (r + (j - i) - 1)) / 2.0
        for k in range(i, j):
            _, idx = pairs[k]
            ranks[idx] = avg
        r += (j - i)
        i = j
    return ranks


# （削除）pricePlace/丸め/TP/SL計算は runner 側の責務（strategyは判断のみ）


def _rci_latest(closes: List[float], n: int) -> Tuple[float, float]:
    # returns (rci_now, rci_prev)
    if len(closes) < n + 1:
        return float("nan"), float("nan")

    def _calc_rci(window: List[float]) -> float:
        # CAT_v8_01: window 内に NaN が1つでもあれば RCI を算出しない（その時点は NaN のまま）
        if any(v != v for v in window):
            return float("nan")

        t_rank = list(range(1, n + 1))
        p_rank = _rank_avg_ties(window)
        d2 = sum((t_rank[i] - p_rank[i]) ** 2 for i in range(n))
        den = n * (n * n - 1)
        return (1.0 - (6.0 * d2) / den) * 100.0

    now_w = closes[-n:]
    prev_w = closes[-n - 1 : -1]
    return _calc_rci(now_w), _calc_rci(prev_w)

# （削除）_rci_pair は未使用（_rci_latest/_rci_last_pair を直接使用）

def _bb20_latest(closes: List[float]) -> Tuple[float, float, float, float]:
    # returns (mid, upper2, lower2, width_pct)  ※CAT_v8_01: (upper-lower)/mid
    mid = _sma(closes, 20)
    sd = _std(closes, 20)
    if mid != mid or sd != sd:
        return float("nan"), float("nan"), float("nan"), float("nan")
    upper = mid + 2.0 * sd
    lower = mid - 2.0 * sd
    width = (upper - lower) / mid if mid != 0 else float("nan")
    return mid, upper, lower, width


def _rci_last(closes: List[float], n: int) -> float:
    # latest RCI(n)
    if not isinstance(closes, list) or len(closes) < n:
        return float("nan")
    try:
        rci_now, _rci_prev = _rci_latest(closes, n)
        return float(rci_now)
    except Exception:
        return float("nan")


def _rci_last_pair(closes: List[float], n: int) -> Tuple[float, float]:
    # (prev, now) for cross checks
    if not isinstance(closes, list) or len(closes) < (n + 1):
        return float("nan"), float("nan")
    try:
        rci_now, rci_prev = _rci_latest(closes, n)
        return float(rci_prev), float(rci_now)
    except Exception:
        return float("nan"), float("nan")


# （削除）_rsi_series は上側（n引数版）に統一

# （削除）_adx_latest は未使用（_adx_series を使用）


def decide(snapshot: Dict[str, Any]) -> Dict[str, Any]:

    # E-3_C専用：配線検証のための強制アクション（戦略ロジックは変更しない）
    fa = snapshot.get("force_action")

    forced_action = None
    forced_side = None  # "LONG" / "SHORT" / None

    if fa in ("ENTER", "EXIT", "NOOP", "STOP"):
        forced_action = fa
    elif fa == "ENTER_SHORT":
        forced_action = "ENTER"
        forced_side = "SHORT"
    elif fa == "EXIT_SHORT":
        forced_action = "EXIT"
        forced_side = "SHORT"


    candles = snapshot.get("candles_5m") or []
    if not isinstance(candles, list) or len(candles) < 30:
        return {
            "action": "STOP",
            "reason": "cat_live_decider: insufficient candles_5m (<30)",
            "side": SIDE_DEFAULT,
        }

    ts, o, h, l, c = _parse_candles(candles)
    if len(c) < 30:
        return {
            "action": "STOP",
            "reason": "cat_live_decider: candles_5m parse failed",
            "side": SIDE_DEFAULT,
        }

    # latest bar
    o0, h0, l0, c0 = o[-1], h[-1], l[-1], c[-1]
    bullish = c0 > o0
    # CAT_v8_01(P23): close <= open（同値も陰線扱い）
    bearish = c0 <= o0
    real_body = abs(c0 - o0)
    lower_wick = (min(o0, c0) - l0)

    # indicators (latest + previous where needed)
    bb_mid, bb_u2, bb_l2, bb_w = _bb20_latest(c)
    # prev bb width
    bb_mid_p, bb_u2_p, bb_l2_p, bb_w_p = _bb20_latest(c[:-1])

    ema20 = _ema_series(c, 20)
    ema20_now = ema20[-1] if ema20 else float("nan")

    adx = _adx_series(h, l, c, 14)
    adx_now = adx[-1] if adx else float("nan")

    stoch_k, stoch_d = _stoch_kd(h, l, c, 7, 2)

    rci7_now, rci7_prev = _rci_latest(c, 7)
    rci9_now, rci9_prev = _rci_latest(c, 9)

    # --- params (optional) ---
    params = snapshot.get("params") or {}
    if not isinstance(params, dict):
        params = {}

    # --- common values ---
    c_prev = c[-2]
    h_prev = h[-2]
    o_prev = o[-2]

# indicators for SHORT
    # adx_now は上で計算済みの値を使う（上書きしない）

    # （削除）RSIは runner 側の責務（strategyでは一切計算しない）

    # risk score (v8: std20/close)  ※CAT_v8_01 に合わせて ddof=1
    vola20 = _std_ddof1(c, 20)
    entry_risk_score = (vola20 / c0) if (vola20 == vola20 and c0 and c0 > 0) else float("nan")
    if entry_risk_score == entry_risk_score:
        entry_risk_score = max(entry_risk_score, 0.0)

    risk_thresh = float(params.get("risk_thresh", 0.3398))
    filter_riskscore_passed = (entry_risk_score == entry_risk_score) and (entry_risk_score <= risk_thresh)

    # BB for P22 touch
    bb_mid_now, bb_u2_now, bb_l2_now, bb_w_now = bb_mid, bb_u2, bb_l2, bb_w
    bb_mid_prev, bb_u2_prev, bb_l2_prev, bb_w_prev = bb_mid_p, bb_u2_p, bb_l2_p, bb_w_p
    bb_mid_slope = bb_mid_now - bb_mid_prev

    # RCI for P22
    rci7_prev, rci7_now = _rci_last_pair(c, 7)
    rci9_prev, rci9_now = _rci_last_pair(c, 9)
    rci52_now = _rci_last(c, 52)

    # --- P22 (SHORT): RCI dead-cross + BB upper touch + mid_down OR rci52 hot; plus ADX/risk gates ---
    p22 = False
    p22_reason = ""
    # rci dead cross (7 vs 9): prev >=, now <=
    rci_cross = (rci7_prev == rci7_prev and rci9_prev == rci9_prev and rci7_now == rci7_now and rci9_now == rci9_now
                 and (rci7_prev >= rci9_prev) and (rci7_now <= rci9_now))

    # BB upper touch (now or prev), eps_rel=0.0012
    eps_abs, eps_rel = 1e-8, 1.2e-3
    touch_now = (h0 == h0 and bb_u2_now == bb_u2_now and (h0 >= bb_u2_now * (1 - eps_rel) - eps_abs))
    touch_prev = (h_prev == h_prev and bb_u2_prev == bb_u2_prev and (h_prev >= bb_u2_prev * (1 - eps_rel) - eps_abs))
    bb_upper_touch = bool(touch_now or touch_prev)

    # mid down ok: NaN allowed or <= 0.02
    mid_down_ok = (bb_mid_slope != bb_mid_slope) or (bb_mid_slope <= 0.02)

    thr_rci52 = float(params.get("P22_RCI52_MIN", 55.0))
    rci52_hot_eval = (rci52_now == rci52_now) and (rci52_now > thr_rci52)

    cross_mid = (rci_cross and bb_upper_touch and mid_down_ok)
    core_gate = (cross_mid or rci52_hot_eval)

    thr_adx = float(params.get("P22_ADX_MIN", 22.0))
    adx_ok_p22 = (adx_now == adx_now) and (adx_now >= thr_adx)
    risk_ok_p22 = bool(filter_riskscore_passed)

    trace_flags = snapshot.get("trace_flags", {}) if isinstance(snapshot, dict) else {}
    TRACE_P22 = bool(trace_flags.get("TRACE_P22", False))
    idx0 = len(c) - 1

    if TRACE_P22:
        print(f"[P22_TRACE_ON] idx={idx0}")

    if TRACE_P22 and core_gate:
        print(f"[P22_CAND] idx={idx0} adx_ok={adx_ok_p22} risk_ok={risk_ok_p22} mid_slope={bb_mid_slope}")

    if core_gate and adx_ok_p22 and risk_ok_p22:
        p22 = True
        p22_reason = "p22:core_gate+adx+risk"
        if TRACE_P22:
            print(f"[P22_FIRE] idx={idx0} mode=normal")
    else:
        if int(params.get("P22_RELAX_FINAL", 1)) == 1 and core_gate:
            p22 = True
            p22_reason = "p22:core_gate(relax)"
            if TRACE_P22:
                print(f"[P22_FIRE] idx={idx0} mode=relax")

    # --- P23 (SHORT): stoch dead-cross + bearish ---
    p23 = False
    p23_reason = ""
    if params.get("ENABLE_P23_SHORT", False) and stoch_k and stoch_d and len(stoch_k) >= 3 and len(stoch_d) >= 3:
        k2, d2 = stoch_k[-3], stoch_d[-3]
        k1, d1 = stoch_k[-2], stoch_d[-2]
        k0, d0 = stoch_k[-1], stoch_d[-1]
        if (k2 > d2) and (k1 > d1) and (k0 < d0) and ((d0 - k0) > 0.3) and bearish:
            p23 = True
            p23_reason = "p23:stoch_dead+bearish"

    # --- P21 (SHORT): close<ema20, ema20 down, adx gate, bearish, bb_mid_slope gate ---
    p21 = False
    p21_reason = ""
    SHORT_S1_ENABLE = bool(params.get("SHORT_S1_ENABLE", True))
    if SHORT_S1_ENABLE:
        ema20_now = ema20[-1] if ema20 and len(ema20) >= 1 else float("nan")
        ema20_prev = ema20[-2] if ema20 and len(ema20) >= 2 else float("nan")

        ADX_THRESH = float(params.get("ADX_THRESH", 25.0))
        p21_adx_min = float(params.get("P21_ADX_MIN", 18.0))
        p21_slope_max = float(params.get("P21_BB_SLOPE_MAX", 50.0))

        slope_ok = True
        if bb_mid_slope == bb_mid_slope:
            slope_ok = (bb_mid_slope <= p21_slope_max)

        cond_short = (
            slope_ok
            and (ema20_now == ema20_now) and (ema20_prev == ema20_prev)
            and (c0 < ema20_now)
            and ((ema20_now - ema20_prev) < 0)
            and (adx_now == adx_now) and (adx_now > ADX_THRESH) and (adx_now >= p21_adx_min)
            and bearish
        )
        if cond_short:
            p21 = True
            p21_reason = "p21:trend_short"


    # === Decide (exclusive, CAT_v8_01 order) ===
        # ===== Entry Priority 1/2/3 (define here to avoid undefined vars) =====

    # ----- P1 -----
    p1 = False
    p1_reason = ""

    bb_width = bb_w
    bb_width_prev = bb_w_p
    bb_expanding = (
        (bb_width == bb_width)
        and (bb_width_prev == bb_width_prev)
        and (bb_width > bb_width_prev)
    )

    bb_touch_idx = None
    for back in range(2, 7):
        j = len(c) - 1 - back
        if j < 0:
            continue

        low_j = l[j]
        bb_lower2_j = _bb20_latest(c[: j + 1])[2]

        # touch候補足(j)の実体・下ヒゲをその場計算（CAT_v8_01と同等）
        # real_body = abs(close-open)
        # lower_wick = min(open,close) - low
        real_body_j = abs(float(c[j]) - float(o[j]))
        lower_wick_j = min(float(o[j]), float(c[j])) - float(l[j])

        # CAT_v8_01: touch候補足の bullish は close > open
        bullish_j = (float(c[j]) > float(o[j]))

        sigma2_touch = (
            (low_j == low_j)
            and (bb_lower2_j == bb_lower2_j)
            and (low_j <= bb_lower2_j + 1e-8)
        )

        has_long_lower_wick = (
            bullish_j
            and (real_body_j == real_body_j)
            and (lower_wick_j == lower_wick_j)
            and real_body_j > 0
            and lower_wick_j > real_body_j * 1.3
        )

        if sigma2_touch or has_long_lower_wick:
            bb_touch_idx = j
            break

    cond_third_bullish = False
    if bb_touch_idx is not None:
        delta = (len(c) - 1) - bb_touch_idx
        if delta in (1, 2, 3, 4, 5, 6):
            cond_third_bullish = (c0 >= o0)

    adx_ok = (adx_now == adx_now) and (adx_now > 16)

    if bb_expanding and cond_third_bullish and adx_ok:
        p1 = True
        p1_reason = f"p1:bb_width_up adx={adx_now:.2f}"


    # ----- P2 -----
    p2 = False
    p2_reason = ""
    if len(stoch_k) >= 3 and len(stoch_d) >= 3:
        k2, d2 = stoch_k[-3], stoch_d[-3]
        k1, d1 = stoch_k[-2], stoch_d[-2]
        k0, d0 = stoch_k[-1], stoch_d[-1]
        if all(x == x for x in [k2, d2, k1, d1, k0, d0]):
            # CAT_v8_01(P2): 直前(i-1)のみ K < D を要求（i-2 はnotnaチェックのみ）
            cond_prev2 = (k1 < d1)
            cond_now = (k0 > d0) and ((k0 - d0) > STOCH_DIFF_MIN)
            if cond_prev2 and cond_now and (c0 >= o0):
                p2 = True
                p2_reason = f"p2:stoch_cross diff={(k0-d0):.2f}"

    # ----- P3 -----
    p3 = False
    p3_reason = ""
    # rci7_prev/rci7_now, rci9_prev/rci9_now はこの時点で既に計算済みの値を使う（上で代入されている想定）
    if (rci7_prev == rci7_prev) and (rci9_prev == rci9_prev) and (rci7_now == rci7_now) and (rci9_now == rci9_now):
        if (rci7_prev < rci9_prev) and (rci7_now > rci9_now):
            # CAT_v8_01: bb_mid_slope が下向きなら P3ロングは除外
            if (bb_mid_slope == bb_mid_slope) and (bb_mid_slope < 0):
                p3 = False
                p3_reason = "p3:excluded bb_mid_slope<0"
            else:
                p3 = True
                p3_reason = "p3:rci_gc"

    # Order:
    #   P4(LONG) -> P1(LONG) -> P3(LONG) -> P2(LONG) -> P22(SHORT) -> P23(SHORT) -> P21(SHORT)
    action = "NOOP"
    reason = ""
    entry_priority = None

    # side default / forced
    decided_side = SIDE_DEFAULT
    if forced_side is not None:
        decided_side = forced_side

    # ---- P4 (LONG) minimal: pullback + close>=ema20 + bullish/equal + entry_ok_flag ----
    p4 = False
    p4_reason = ""
    lookback_pullback = int(params.get("P4_PULLBACK_LOOKBACK", 5))
    p4_ema_tol = float(params.get("P4_EMA_TOL", 0.001))
    if lookback_pullback < 1:
        lookback_pullback = 1

    # current candle
    bullish_now = (c0 == c0) and (o0 == o0) and (c0 >= o0)

    pullback_ok = False
    for back in range(1, lookback_pullback + 1):
        j = len(c) - 1 - back
        if j < 0:
            break

        low_j = l[j]
        ema20_j = ema20[j] if (ema20 and j < len(ema20)) else float("nan")
        # bb_mid at that time (needs >=20 closes)
        bb_mid_j = _bb20_latest(c[: j + 1])[0] if (j >= 19) else float("nan")

        if low_j == low_j:
            ema_hit = (ema20_j == ema20_j) and (low_j <= ema20_j * (1.0 + p4_ema_tol))
            mid_hit = (bb_mid_j == bb_mid_j) and (low_j <= bb_mid_j * (1.0 + p4_ema_tol))
            if ema_hit or mid_hit:
                pullback_ok = True
                break

    trend_ok = (ema20_now == ema20_now) and (c0 == c0) and (c0 >= ema20_now)

    # entry_ok_flag: snapshot側に無ければ True（CAT_v8_01 row.get("entry_ok", True) 相当）
    entry_ok_flag = bool(snapshot.get("entry_ok", True))

    if pullback_ok and trend_ok and bullish_now and entry_ok_flag:
        p4 = True
        p4_reason = "p4:pullback_hit+close>=ema20+bullish"




    # ---- forced_action has absolute priority (test_only) ----
    if forced_action is not None:
        action = forced_action
        reason = f"force_action:{forced_action}(test_only)"
        # side is already forced by forced_side if provided
    else:
        # LONG block (CAT_v8_01 order)
        if p4:
            action = "ENTER"
            decided_side = "LONG"
            entry_priority = 4
            reason = p4_reason
            decision_material = {
                "close": c0,
                "open": o0,
                "ema20_now": ema20_now,
                "bullish_now": bullish_now,
                "pullback_ok": pullback_ok,
                "trend_ok": trend_ok,
                "entry_ok_flag": entry_ok_flag,
            }

        elif p1:
            action = "ENTER"
            decided_side = "LONG"
            entry_priority = 1
            reason = p1_reason

            # F1: P1 material (minimum proof set)
            # ※判断条件は変更しない。P1がTrueになった後に、成立材料を再計算して記録するだけ。
            touch = None
            if bb_touch_idx is not None:
                j = int(bb_touch_idx)
                try:
                    low_j = l[j]
                    bb_lower2_j = _bb20_latest(c[: j + 1])[2]

                    real_body_j = abs(float(c[j]) - float(o[j]))
                    lower_wick_j = min(float(o[j]), float(c[j])) - float(l[j])
                    bullish_j = (float(c[j]) > float(o[j]))

                    sigma2_touch = (
                        (low_j == low_j)
                        and (bb_lower2_j == bb_lower2_j)
                        and (low_j <= bb_lower2_j + 1e-8)
                    )

                    has_long_lower_wick = (
                        bullish_j
                        and (real_body_j == real_body_j)
                        and (lower_wick_j == lower_wick_j)
                        and real_body_j > 0
                        and lower_wick_j > real_body_j * 1.3
                    )

                    delta = (len(c) - 1) - j

                    touch = {
                        "bb_touch_idx": j,
                        "delta": delta,
                        "low_j": low_j,
                        "bb_lower2_j": bb_lower2_j,
                        "sigma2_touch": sigma2_touch,
                        "has_long_lower_wick": has_long_lower_wick,
                        "real_body_j": real_body_j,
                        "lower_wick_j": lower_wick_j,
                        "bullish_j": bullish_j,
                    }
                except Exception:
                    touch = {"bb_touch_idx": j}

            decision_material = {
                "bb_w": bb_w,
                "bb_w_prev": bb_w_p,
                "adx_now": adx_now,
                "close": c0,
                "open": o0,
                "touch": touch,
            }

        elif p3:
            action = "ENTER"
            decided_side = "LONG"
            entry_priority = 3
            reason = p3_reason
            decision_material = {
                "bb_mid_slope": bb_mid_slope,
                "rci_ctx": {
                    "rci7_prev": rci7_prev,
                    "rci9_prev": rci9_prev,
                    "rci7_now": rci7_now,
                    "rci9_now": rci9_now,
                },
            }

        elif p2:
            action = "ENTER"
            decided_side = "LONG"
            entry_priority = 2
            reason = p2_reason

            # F1: P2 material (minimum proof set)
            k1 = (stoch_k[-2] if len(stoch_k) >= 2 else None)
            d1 = (stoch_d[-2] if len(stoch_d) >= 2 else None)
            k0 = (stoch_k[-1] if len(stoch_k) >= 1 else None)
            d0 = (stoch_d[-1] if len(stoch_d) >= 1 else None)

            diff = float("nan")
            try:
                if (k0 is not None) and (d0 is not None):
                    kk = float(k0)
                    dd = float(d0)
                    if (kk == kk) and (dd == dd):
                        diff = kk - dd
            except Exception:
                pass

            decision_material = {
                "stoch_prev": {"k": k1, "d": d1},
                "stoch_now": {"k": k0, "d": d0},
                "diff_now": diff,
                "STOCH_DIFF_MIN": STOCH_DIFF_MIN,
                "bullish_now": (c0 >= o0),
            }


        # SHORT block (CAT_v8_01 order)
        elif p22:
            action = "ENTER"
            decided_side = "SHORT"
            entry_priority = 22
            reason = p22_reason

            # F1: P22 material (minimum proof set / ONLY vars used in P22 gates)
            decision_material = {
                "adx_now": adx_now,
                "P22_ADX_MIN": thr_adx,
                "entry_risk_score": entry_risk_score,
                "risk_thresh": risk_thresh,
                "bb_mid_slope": bb_mid_slope,
                "bb_touch": {
                    "h_now": h0,
                    "bb_u2_now": bb_u2_now,
                    "h_prev": h_prev,
                    "bb_u2_prev": bb_u2_prev,
                },
                "rci_ctx": {
                    "rci7_prev": rci7_prev,
                    "rci9_prev": rci9_prev,
                    "rci7_now": rci7_now,
                    "rci9_now": rci9_now,
                    "rci52_now": rci52_now,
                    "P22_RCI52_MIN": thr_rci52,
                },
            }

        elif p23:
            action = "ENTER"
            decided_side = "SHORT"
            entry_priority = 23
            reason = p23_reason


            # F1: P23 material (minimum proof set)
            stoch_gap = float("nan")
            try:
                if len(stoch_k) >= 1 and len(stoch_d) >= 1:
                    k0, d0 = stoch_k[-1], stoch_d[-1]
                    if (k0 == k0) and (d0 == d0):
                        stoch_gap = k0 - d0
            except Exception:
                pass

            decision_material = {
                "stoch_k": (stoch_k[-1] if len(stoch_k) >= 1 else None),
                "stoch_d": (stoch_d[-1] if len(stoch_d) >= 1 else None),
                "gap": stoch_gap,
                "bearish": (c0 <= o0),
                "ENABLE_P23_SHORT": bool(params.get("ENABLE_P23_SHORT", False)),
            }

        else:
            reason = "no_entry"


    # strategy は判断のみ（合意）：TP/SL/RSI/TIME_EXIT は runner 側の責務
    out = {
        "action": action,
        "reason": f"cat_live_decider:{reason}",
        "side": decided_side,
    }
    if entry_priority is not None:
        out["entry_priority"] = entry_priority

    # F1: material proof (for fired priority)
    # 発火した priority の成立材料を out["material"] に載せる（判断ロジックは変えない）
    if ("decision_material" in locals()) and (decision_material is not None):
        out["material"] = decision_material


    # NOOP時だけ、最小の根拠数値を残す（E-1_Aデバッグ用途）
    if action == "NOOP":
        # stoch diff
        stoch_diff = float("nan")
        if len(stoch_k) >= 1 and len(stoch_d) >= 1:
            k0, d0 = stoch_k[-1], stoch_d[-1]
            if (k0 == k0) and (d0 == d0):
                stoch_diff = k0 - d0

        out["debug"] = {
            "close": c0,
            "open": o0,
            "bullish": bullish,
            "bb_w": bb_w,
            "bb_w_prev": bb_w_p,
            "adx": adx_now,
            "ema20": ema20_now,
            "stoch_diff": stoch_diff,
            "rci7_now": rci7_now,
            "rci7_prev": rci7_prev,

            "rci9_now": rci9_now,
            "rci9_prev": rci9_prev,

        }

    return out

