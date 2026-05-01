"""regime v13: v10 ベース + V字頂点検出オーバーライド

設計:
  - ベース判定は v10（既存 predictions_v10_1h.json をそのまま読み込み）
  - 5m足で V字頂点検出条件を全期間スキャン
  - 検出時点から regime を強制上書き（天井 → dn / 底 → up）
  - オーバーライド継続: 次の逆方向検出が出るまで（E1: 同方向再発火は無視）
  - 評価:
    1) 24サンプルでの検出ヒット率（peak±N分以内に発火するか）
    2) 全期間の発火件数・密度
    3) v10 vs v13 の判定差分（区間3 含む）
    4) 4h 教師サンプルとの一致率（参考値）

検出条件（24サンプル観察から導出・各方向 4 条件 AND）:

  天井（up V字）:
    - 5m RSI7 ≥ 70
    - 5m Williams %R ≥ -20
    - 5m DI差 ≥ +15
    - 5m BB幅 rank(50本) ≥ 0.7

  底（down V字）:
    - 5m RSI7 ≤ 30
    - 5m Williams %R ≤ -80
    - 5m DI差 ≤ -15
    - 5m BB幅 rank(50本) ≥ 0.7

ヒステリシス:
  - 検出パチパチ抑制のため、検出後 K=12 バー（60分）は同方向再発火を無視（クールダウン）

出力:
  results/vshape_design/v13_validation.md          — 24サンプルでの検出評価
  dashboard/regime_prototype/predictions_v13_1h.json  — タブ⑪ 表示用
  dashboard/regime_prototype/predictions_v13_1d.json
  dashboard/regime_prototype/index.json (v13 追加)
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import timezone

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
SAMPLES_24 = BASE / "results/vshape_design/samples_24.parquet"
V10_JSON = BASE / "dashboard/regime_prototype/predictions_v10_1h.json"
DASH_DIR = BASE / "dashboard/regime_prototype"
OUT_DIR = BASE / "results/vshape_design"
VERSION = "v14"

# v14.4: トレンド継続判定 = 「pivot からの戻り幅」の維持
# 終了条件: close が「pivot ± PIVOT_HOLD_PCT%」を超えて戻った時点
PIVOT_HOLD_PCT = 0.2                # pivot からの戻り幅の維持下限（0.2% = 戻り幅 < 0.2% で終了）
SAFETY_TIMEOUT_HOURS = 48.0         # 保険タイマー（pivot 下抜けまで維持なので長め）

# 検出パラメータ
COND_TOP = {
    "rsi7_min": 80.0,
    "stoch_k_peak_min": 90.0,
    "stoch_k_now_max": 80.0,
    "wr_min": -10.0,
    "di_diff_min": 20.0,
    "bb_rank_min": 0.85,
    "recent_move_pct_min": 2.5,  # 2h以内の急騰幅（1.5→2.5%）
}
COND_BOT = {
    "rsi7_max": 20.0,
    "stoch_k_trough_max": 10.0,
    "stoch_k_now_min": 20.0,
    "wr_max": -90.0,
    "di_diff_max": -20.0,
    "bb_rank_min": 0.85,
    "recent_move_pct_max": -2.5,  # 2h以内の急落幅（-1.5→-2.5%）
}
REVERSAL_LOOKBACK_BARS = 18  # 過熱状態を見る直近Nバー（5m×18=90分）
PIVOT_LOOKBACK_BARS = 24     # ピボット（最高値/最安値）を見る直近Nバー（5m×24=2h）
PIVOT_MIN_AGE_BARS = 3       # ピボットから現バーまで最低3本（=15分）経過
PIVOT_RETRACE_PCT_MIN = 1.0  # 戻り幅の絶対下限（小さな下落でのノイズ防止）
PIVOT_RETRACE_HALF = 0.5     # 急落/急騰幅の半値戻し（底/天井反発の本質基準）
COOLDOWN_BARS_5M = 12   # 60分（5m足12本）の同方向クールダウン
HIT_TOLERANCE_MIN = 60  # peak ±60分以内の発火を「ヒット」と判定
OVERRIDE_DURATION_HOURS = 4.0  # 発火後 N時間だけ override 有効（events half median 4.58h と同等）
RECENT_MOVE_BARS = 6  # 直近 30分（5m×6本）の価格変動率を見る


# ── 5m足指標計算（look-ahead なし） ────────────────────────

def rsi(c, period):
    d = c.diff()
    g = d.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = g / l.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def adx_di(h, l, c, period=14):
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    up = h.diff(); dn = -l.diff()
    dmp = up.where((up > dn) & (up > 0), 0.0)
    dmm = dn.where((dn > up) & (dn > 0), 0.0)
    dip = 100 * dmp.ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan)
    dim = 100 * dmm.ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan)
    return dip - dim


def williams_r(h, l, c, period=14):
    hh = h.rolling(period).max()
    ll = l.rolling(period).min()
    return -100 * (hh - c) / (hh - ll).replace(0, np.nan)


def bb_width_rank(c, period=20, rank_window=50):
    ma = c.rolling(period).mean()
    sd = c.rolling(period).std()
    width = (ma + 2*sd - (ma - 2*sd)) / ma * 100
    return width.rolling(rank_window).rank(pct=True)


def stochastic_k(h, l, c, period=14):
    ll = l.rolling(period).min()
    hh = h.rolling(period).max()
    return 100 * (c - ll) / (hh - ll).replace(0, np.nan)


def compute_signals_5m(df5m):
    """5m足で検出に必要な指標を計算。
    「過熱は直近Nバー内に経由したか」「反転は現バーで起きているか」を分離。
    """
    o, h, l, c = df5m["open"], df5m["high"], df5m["low"], df5m["close"]
    out = pd.DataFrame(index=df5m.index)
    out["close"] = c
    out["open"] = o

    rsi7 = rsi(c, 7)
    sk = stochastic_k(h, l, c, 14)
    di_diff = adx_di(h, l, c, 14)
    wr = williams_r(h, l, c, 14)
    bb = bb_width_rank(c, 20, 50)

    # 過熱状態: 直近Nバー内で極値を経由したか
    out["rsi7_peak_recent"] = rsi7.rolling(REVERSAL_LOOKBACK_BARS).max()
    out["rsi7_trough_recent"] = rsi7.rolling(REVERSAL_LOOKBACK_BARS).min()
    out["stoch_k_peak_recent"] = sk.rolling(REVERSAL_LOOKBACK_BARS).max()
    out["stoch_k_trough_recent"] = sk.rolling(REVERSAL_LOOKBACK_BARS).min()
    out["wr_peak_recent"] = wr.rolling(REVERSAL_LOOKBACK_BARS).max()
    out["wr_trough_recent"] = wr.rolling(REVERSAL_LOOKBACK_BARS).min()
    out["di_diff_peak_recent"] = di_diff.rolling(REVERSAL_LOOKBACK_BARS).max()
    out["di_diff_trough_recent"] = di_diff.rolling(REVERSAL_LOOKBACK_BARS).min()
    out["bb_rank_peak_recent"] = bb.rolling(REVERSAL_LOOKBACK_BARS).max()

    # 反転確認: 現バーは過熱から脱出している
    out["stoch_k"] = sk
    out["recent_move_pct"] = (c / c.shift(RECENT_MOVE_BARS) - 1) * 100  # 直近30分の動き
    out["candle_bullish"] = (c > o)
    out["candle_bearish"] = (c < o)

    # ピボット確認（真の底/天井からの戻り）
    # 直近 PIVOT_LOOKBACK_BARS 本での最安値・最高値とその位置（バー前数）
    pivot_low = l.rolling(PIVOT_LOOKBACK_BARS).min()
    pivot_high = h.rolling(PIVOT_LOOKBACK_BARS).max()
    out["pivot_low"] = pivot_low
    out["pivot_high"] = pivot_high
    # ピボットから現在までのバー数（簡易: lowest_idx を rolling で取る）
    def bars_since_min(s, window):
        result = np.full(len(s), np.nan)
        vals = s.values
        for i in range(window-1, len(s)):
            seg = vals[i-window+1:i+1]
            min_idx_in_window = int(np.argmin(seg))
            result[i] = (window - 1) - min_idx_in_window  # バー前数（0=現在バー）
        return pd.Series(result, index=s.index)
    def bars_since_max(s, window):
        result = np.full(len(s), np.nan)
        vals = s.values
        for i in range(window-1, len(s)):
            seg = vals[i-window+1:i+1]
            max_idx_in_window = int(np.argmax(seg))
            result[i] = (window - 1) - max_idx_in_window
        return pd.Series(result, index=s.index)
    out["bars_since_pivot_low"] = bars_since_min(l, PIVOT_LOOKBACK_BARS)
    out["bars_since_pivot_high"] = bars_since_max(h, PIVOT_LOOKBACK_BARS)
    # ピボットからの戻り幅 (%)
    out["retrace_from_low_pct"] = (c - pivot_low) / pivot_low * 100
    out["retrace_from_high_pct"] = (pivot_high - c) / pivot_high * 100
    # 「2h前 vs pivot_low/high」: 2h以内に急落/急騰があった事実の確認
    c_lookback = c.shift(PIVOT_LOOKBACK_BARS)
    out["pivot_low_drop_from_2h_ago_pct"] = (pivot_low - c_lookback) / c_lookback * 100  # ≤-1.5% なら急落あり
    out["pivot_high_rise_from_2h_ago_pct"] = (pivot_high - c_lookback) / c_lookback * 100  # ≥+1.5% なら急騰あり
    # 半値戻し基準（急落/急騰幅の絶対値 × 0.5・最低 PIVOT_RETRACE_PCT_MIN）
    bot_required = np.maximum(PIVOT_RETRACE_PCT_MIN,
                              out["pivot_low_drop_from_2h_ago_pct"].abs() * PIVOT_RETRACE_HALF)
    top_required = np.maximum(PIVOT_RETRACE_PCT_MIN,
                              out["pivot_high_rise_from_2h_ago_pct"].abs() * PIVOT_RETRACE_HALF)
    out["bot_retrace_required_pct"] = bot_required
    out["top_retrace_required_pct"] = top_required

    # v14.4: トレンド継続判定は build_vshape_regime 側で「pivot からの戻り維持」で実装
    return out


# ── V字検出ロジック ───────────────────────────────────────

def detect_vshape(sig5m):
    """5m足で V字頂点検出。各バーで top/bot 条件を評価し、
    クールダウン込みで「fired」フラグと「signal_dir」（top/bot/None）を出す。

    Returns:
        DataFrame with columns: signal_dir (str: 'top'/'bot'/None), fired (bool)
    """
    # 天井: 過熱経由 + 2h以内に急騰があった + ピボット高値からの戻り + 反転確認
    cond_top = (
        # 過熱経由
        (sig5m["rsi7_peak_recent"] >= COND_TOP["rsi7_min"]) &
        (sig5m["stoch_k_peak_recent"] >= COND_TOP["stoch_k_peak_min"]) &
        (sig5m["wr_peak_recent"] >= COND_TOP["wr_min"]) &
        (sig5m["di_diff_peak_recent"] >= COND_TOP["di_diff_min"]) &
        (sig5m["bb_rank_peak_recent"] >= COND_TOP["bb_rank_min"]) &
        # 2h以内に急騰があった（pivot_high が 2h前比で +1.5% 以上）
        (sig5m["pivot_high_rise_from_2h_ago_pct"] >= COND_TOP["recent_move_pct_min"]) &
        # ピボット高値が PIVOT_MIN_AGE_BARS 以上前にある + 半値戻し以上
        (sig5m["bars_since_pivot_high"] >= PIVOT_MIN_AGE_BARS) &
        (sig5m["retrace_from_high_pct"] >= sig5m["top_retrace_required_pct"]) &
        # 反転確認（現バー）
        (sig5m["stoch_k"] <= COND_TOP["stoch_k_now_max"]) &
        (sig5m["candle_bearish"])
    )
    # 底: 過熱経由 + 2h以内に急落があった + ピボット安値からの戻り + 反転確認
    cond_bot = (
        (sig5m["rsi7_trough_recent"] <= COND_BOT["rsi7_max"]) &
        (sig5m["stoch_k_trough_recent"] <= COND_BOT["stoch_k_trough_max"]) &
        (sig5m["wr_trough_recent"] <= COND_BOT["wr_max"]) &
        (sig5m["di_diff_trough_recent"] <= COND_BOT["di_diff_max"]) &
        (sig5m["bb_rank_peak_recent"] >= COND_BOT["bb_rank_min"]) &
        # 2h以内に急落があった（pivot_low が 2h前比で -1.5% 以下）
        (sig5m["pivot_low_drop_from_2h_ago_pct"] <= COND_BOT["recent_move_pct_max"]) &
        # ピボット安値が PIVOT_MIN_AGE_BARS 以上前にある + 半値戻し以上
        (sig5m["bars_since_pivot_low"] >= PIVOT_MIN_AGE_BARS) &
        (sig5m["retrace_from_low_pct"] >= sig5m["bot_retrace_required_pct"]) &
        # 反転確認
        (sig5m["stoch_k"] >= COND_BOT["stoch_k_now_min"]) &
        (sig5m["candle_bullish"])
    )

    # クールダウン処理
    fired_top = pd.Series(False, index=sig5m.index)
    fired_bot = pd.Series(False, index=sig5m.index)
    cooldown_top = 0
    cooldown_bot = 0
    for i in range(len(sig5m)):
        if cooldown_top > 0:
            cooldown_top -= 1
        if cooldown_bot > 0:
            cooldown_bot -= 1
        if cond_top.iloc[i] and cooldown_top == 0:
            fired_top.iloc[i] = True
            cooldown_top = COOLDOWN_BARS_5M
        if cond_bot.iloc[i] and cooldown_bot == 0:
            fired_bot.iloc[i] = True
            cooldown_bot = COOLDOWN_BARS_5M

    out = pd.DataFrame(index=sig5m.index)
    out["fired_top"] = fired_top
    out["fired_bot"] = fired_bot
    out["cond_top_raw"] = cond_top  # クールダウン前の生条件成立
    out["cond_bot_raw"] = cond_bot
    return out


def build_vshape_regime(detect_5m, sig5m, safety_timeout_hours=SAFETY_TIMEOUT_HOURS,
                        hold_pct=PIVOT_HOLD_PCT):
    """v14.5: 検出結果から regime override シリーズを構築。
    トレンド継続判定 = 「発火後の最高/最安 close からの drawdown」（trail 方式）。

    終了条件（優先順位順）:
      1. 逆方向検出が発火 → 即切替
      2. trail からの drawdown が hold_pct% を超えたら終了
         - up中: close < trail_extreme * (1 - hold_pct/100)  （trail高値からの下落）
         - dn中: close > trail_extreme * (1 + hold_pct/100)  （trail安値からの上昇）
      3. 48h 経過（保険タイマー）
    """
    regime = pd.Series(np.nan, index=detect_5m.index, dtype=object)
    safety_duration = pd.Timedelta(hours=safety_timeout_hours)
    expire_at = None
    current = None
    trail_extreme = None  # uptrend: 発火後の最高close / downtrend: 発火後の最安close

    closes = sig5m["close"].values

    for i in range(len(detect_5m)):
        ts = detect_5m.index[i]
        # 1. 検出発火（同方向はクールダウン後の新規発火・逆方向は即切替）
        if detect_5m["fired_top"].iloc[i]:
            current = "downtrend"
            expire_at = ts + safety_duration
            trail_extreme = closes[i]
        elif detect_5m["fired_bot"].iloc[i]:
            current = "uptrend"
            expire_at = ts + safety_duration
            trail_extreme = closes[i]

        if current is not None and trail_extreme is not None:
            terminate = False
            # 3. 保険タイマー
            if expire_at is not None and ts >= expire_at:
                terminate = True
            # 2. trail 更新 + drawdown 判定
            elif current == "uptrend":
                if closes[i] > trail_extreme:
                    trail_extreme = closes[i]
                if closes[i] < trail_extreme * (1 - hold_pct / 100.0):
                    terminate = True
            elif current == "downtrend":
                if closes[i] < trail_extreme:
                    trail_extreme = closes[i]
                if closes[i] > trail_extreme * (1 + hold_pct / 100.0):
                    terminate = True

            if terminate:
                current = None
                expire_at = None
                trail_extreme = None
        regime.iloc[i] = current
    return regime


# ── サンプル24でのヒット率検証 ──────────────────────────

def validate_on_samples(detect_5m, samples):
    """各サンプルの peak ± HIT_TOLERANCE_MIN 内で正しい方向の発火が出るかを確認"""
    results = []
    for _, s in samples.iterrows():
        pt = pd.Timestamp(s["peak_time"])
        direction = s["direction"]  # 'up' = 天井（top検出が正解）/ 'down' = 底（bot検出が正解）
        win_start = pt - pd.Timedelta(minutes=HIT_TOLERANCE_MIN)
        win_end = pt + pd.Timedelta(minutes=HIT_TOLERANCE_MIN)
        seg = detect_5m[(detect_5m.index >= win_start) & (detect_5m.index <= win_end)]
        # クールダウン前の raw 条件成立も確認（より緩い指標）
        if direction == "up":
            hit_fired = seg["fired_top"].any()
            hit_raw = seg["cond_top_raw"].any()
            # 発火時刻
            fired_idx = seg[seg["fired_top"]].index
            raw_idx = seg[seg["cond_top_raw"]].index
        else:
            hit_fired = seg["fired_bot"].any()
            hit_raw = seg["cond_bot_raw"].any()
            fired_idx = seg[seg["fired_bot"]].index
            raw_idx = seg[seg["cond_bot_raw"]].index

        first_fire_offset_min = ((fired_idx[0] - pt).total_seconds() / 60) if len(fired_idx) > 0 else None
        first_raw_offset_min = ((raw_idx[0] - pt).total_seconds() / 60) if len(raw_idx) > 0 else None
        results.append({
            "sample_id": s["sample_id"],
            "direction": direction,
            "year": int(s["year"]),
            "peak_time": pt,
            "hit_fired": hit_fired,
            "hit_raw": hit_raw,
            "first_fire_offset_min": first_fire_offset_min,
            "first_raw_offset_min": first_raw_offset_min,
            "fire_count_in_window": int(len(fired_idx)),
        })
    return pd.DataFrame(results)


# ── v10 ベースに被せて 1h regime を作る ─────────────────

def overlay_v10_with_v13(v10_path, vshape_5m_regime):
    """v10 1h JSON に v13 オーバーライドを被せる。
    各 1h バーについて:
      - その1h内に override regime が存在する → override の最新値を採用
      - なければ v10 の判定をそのまま使う
    """
    with open(v10_path) as f:
        v10 = json.load(f)
    rows_v10 = v10["rows"]
    df_v10 = pd.DataFrame(rows_v10, columns=["ts_ms", "close", "pred", "human"])
    df_v10["ts"] = pd.to_datetime(df_v10["ts_ms"], unit="ms")
    df_v10 = df_v10.set_index("ts")

    # vshape_5m_regime を 1h に集約: 各 1h バーの最新 override 値
    # 1h バーの開始時刻 [ts, ts+1h) 内の最新 override を取る
    rows_out = []
    overridden_count = 0
    for ts, row in df_v10.iterrows():
        bar_start = ts
        bar_end = ts + pd.Timedelta("1h")
        # 1h バー内の override 値（NaNを除く・最新を採用）。期限切れは NaN なので拾われない
        seg = vshape_5m_regime[(vshape_5m_regime.index >= bar_start) & (vshape_5m_regime.index < bar_end)]
        seg_valid = seg.dropna()
        if len(seg_valid) > 0:
            final_pred = seg_valid.iloc[-1]
            overridden_count += 1
        else:
            final_pred = row["pred"]  # v10 fallback
        rows_out.append([
            int(row["ts_ms"]),
            int(row["close"]),
            str(final_pred),
            row["human"]
        ])
    return rows_out, overridden_count, len(df_v10)


def write_dashboard(rows_1h, override_count, total_count):
    DASH_DIR.mkdir(parents=True, exist_ok=True)
    out_1h = {"version": VERSION, "granularity": "1h", "rows": rows_1h}
    with open(DASH_DIR / f"predictions_{VERSION}_1h.json", "w") as f:
        json.dump(out_1h, f, separators=(",", ":"))
    print(f"  → predictions_{VERSION}_1h.json ({len(rows_1h)} 行)")

    # 1d 集約
    df_1h = pd.DataFrame(rows_1h, columns=["ts_ms", "close", "pred", "human"])
    df_1h["ts"] = pd.to_datetime(df_1h["ts_ms"], unit="ms")
    df_1h["date"] = df_1h["ts"].dt.date
    daily = df_1h.groupby("date").agg(
        ts_ms=("ts_ms", "first"),
        close=("close", "last"),
        pred=("pred", lambda x: x.mode().iloc[0] if len(x) > 0 else "range"),
        human=("human", lambda x: x.mode().iloc[0] if len(x) > 0 and x.iloc[0] else ""),
    )
    rows_1d = [[int(r["ts_ms"]), int(r["close"]), str(r["pred"]), str(r["human"])]
               for _, r in daily.iterrows()]
    out_1d = {"version": VERSION, "granularity": "1d", "rows": rows_1d}
    with open(DASH_DIR / f"predictions_{VERSION}_1d.json", "w") as f:
        json.dump(out_1d, f, separators=(",", ":"))
    print(f"  → predictions_{VERSION}_1d.json ({len(rows_1d)} 行)")

    # index.json 更新
    idx_path = DASH_DIR / "index.json"
    with open(idx_path) as f:
        idx = json.load(f)
    dist = pd.Series([r[2] for r in rows_1h]).value_counts()
    total = len(rows_1h)
    entry = {
        "version": VERSION,
        "generated_utc": pd.Timestamp.now(tz=timezone.utc).isoformat(),
        "spec": {
            "method": "v10_base + vshape_override + trail_drawdown_continuation",
            "base": "v10",
            "vshape_conditions_top": COND_TOP,
            "vshape_conditions_bot": COND_BOT,
            "cooldown_bars_5m": COOLDOWN_BARS_5M,
            "pivot_hold_pct": PIVOT_HOLD_PCT,
            "safety_timeout_hours": SAFETY_TIMEOUT_HOURS,
            "override_count_1h": override_count,
            "total_1h": total_count,
        },
        "distribution": {
            r: {"count": int(dist.get(r, 0)), "pct": round(dist.get(r, 0)/total*100, 2)}
            for r in ["range", "uptrend", "downtrend"]
        },
    }
    idx["prototypes"] = [p for p in idx["prototypes"] if p["version"] != VERSION]
    idx["prototypes"].append(entry)
    with open(idx_path, "w") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)
    print(f"  → index.json 更新（{VERSION} 追加）")


def evaluate_2025_samples(rows_1h):
    """2025年 731サンプル一致率"""
    smp_path = BASE / "data/regime_samples_4h.csv"
    smp = pd.read_csv(smp_path, parse_dates=["timestamp_utc"])
    smp = smp.rename(columns={"timestamp_utc": "timestamp", "label": "human"})
    smp["timestamp"] = smp["timestamp"].dt.tz_localize(None)
    smp = smp[smp["human"].notna() & (smp["human"] != "")]
    df_1h = pd.DataFrame(rows_1h, columns=["ts_ms", "close", "pred", "human"])
    df_1h["ts"] = pd.to_datetime(df_1h["ts_ms"], unit="ms")
    df_1h = df_1h.set_index("ts")
    # 4h バーの開始時刻と一致する 1h を引く
    hits = 0; n = 0
    for _, r in smp.iterrows():
        ts = r["timestamp"]
        if ts in df_1h.index:
            n += 1
            if df_1h.loc[ts, "pred"] == r["human"]:
                hits += 1
    return hits, n


# ── メイン ────────────────────────────────────────────────

def main():
    print(f"=== {VERSION}: v10 + V字頂点検出オーバーライド ===")
    print("5m OHLC 読み込み...")
    df5m = pd.read_csv(DATA_5M, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    print(f"  5m: {len(df5m)} bars")

    print("5m 指標計算...")
    sig5m = compute_signals_5m(df5m)

    print("V字頂点検出...")
    detect_5m = detect_vshape(sig5m)
    n_top = detect_5m["fired_top"].sum()
    n_bot = detect_5m["fired_bot"].sum()
    print(f"  発火: top={n_top} (天井) / bot={n_bot} (底) / total={n_top+n_bot}")
    print(f"  発火密度: {(n_top+n_bot)/len(detect_5m)*100:.4f}% (5m bar基準)")

    print("\n24サンプルでのヒット率検証...")
    samples = pd.read_parquet(SAMPLES_24)
    val = validate_on_samples(detect_5m, samples)
    n_hit_fired = val["hit_fired"].sum()
    n_hit_raw = val["hit_raw"].sum()
    n_total = len(val)
    print(f"  クールダウン後ヒット: {n_hit_fired}/{n_total} ({n_hit_fired/n_total*100:.1f}%)")
    print(f"  生条件ヒット:       {n_hit_raw}/{n_total} ({n_hit_raw/n_total*100:.1f}%)")
    print(f"  ヒット時の peak からの発火オフセット (分):")
    print(f"    median: {val['first_fire_offset_min'].median():.1f} / "
          f"min: {val['first_fire_offset_min'].min()} / max: {val['first_fire_offset_min'].max()}")

    # 検証 md 出力
    md = ["# v13 検出条件 24サンプル検証", ""]
    md.append(f"- 条件 top: {COND_TOP}")
    md.append(f"- 条件 bot: {COND_BOT}")
    md.append(f"- クールダウン: {COOLDOWN_BARS_5M} bars (5m)")
    md.append(f"- ヒット許容範囲: peak ±{HIT_TOLERANCE_MIN}分")
    md.append("")
    md.append(f"**結果**: クールダウン後 {n_hit_fired}/{n_total} ({n_hit_fired/n_total*100:.1f}%) / "
              f"生条件 {n_hit_raw}/{n_total} ({n_hit_raw/n_total*100:.1f}%)")
    md.append("")
    md.append(f"**全期間発火**: top={n_top} / bot={n_bot} / 5m発火密度 {(n_top+n_bot)/len(detect_5m)*100:.4f}%")
    md.append("")
    md.append("| ID | dir | year | peak_time | hit_fired | hit_raw | fire_offset(min) | raw_offset(min) | fires |")
    md.append("|----|-----|------|-----------|----------|---------|------------------|----------------|-------|")
    for _, r in val.iterrows():
        md.append(
            f"| {r['sample_id']} | {r['direction']} | {r['year']} | "
            f"{r['peak_time']} | {'✅' if r['hit_fired'] else '❌'} | "
            f"{'✅' if r['hit_raw'] else '❌'} | "
            f"{r['first_fire_offset_min'] if r['first_fire_offset_min'] is not None else '-'} | "
            f"{r['first_raw_offset_min'] if r['first_raw_offset_min'] is not None else '-'} | "
            f"{r['fire_count_in_window']} |"
        )
    (OUT_DIR / "v13_validation.md").write_text("\n".join(md) + "\n")
    print(f"  → v13_validation.md")

    print("\nv10 ベースに v13 オーバーライドを被せる...")
    vshape_regime = build_vshape_regime(detect_5m, sig5m)
    rows_1h, override_count, total_count = overlay_v10_with_v13(V10_JSON, vshape_regime)
    print(f"  override 適用バー: {override_count} / {total_count} ({override_count/total_count*100:.1f}%)")

    print("\nダッシュボード JSON 出力...")
    write_dashboard(rows_1h, override_count, total_count)

    print("\n2025年 4h サンプルとの一致率（参考値）...")
    hits, n = evaluate_2025_samples(rows_1h)
    print(f"  v13: {hits}/{n} = {hits/n*100:.1f}%")

    # v10 比較
    with open(V10_JSON) as f:
        v10_data = json.load(f)
    df_v10 = pd.DataFrame(v10_data["rows"], columns=["ts_ms", "close", "pred", "human"])
    df_v10["ts"] = pd.to_datetime(df_v10["ts_ms"], unit="ms")
    df_v10 = df_v10.set_index("ts")
    df_v13 = pd.DataFrame(rows_1h, columns=["ts_ms", "close", "pred", "human"])
    df_v13["ts"] = pd.to_datetime(df_v13["ts_ms"], unit="ms")
    df_v13 = df_v13.set_index("ts")
    diff_count = (df_v10["pred"] != df_v13["pred"]).sum()
    print(f"  v10 vs v13 判定差分: {diff_count} / {len(df_v10)} ({diff_count/len(df_v10)*100:.1f}%)")

    # 区間3
    INT3_S = pd.Timestamp("2026-02-05")
    INT3_E = pd.Timestamp("2026-02-08")
    int3_v13 = df_v13[(df_v13.index >= INT3_S) & (df_v13.index < INT3_E)]
    int3_v10 = df_v10[(df_v10.index >= INT3_S) & (df_v10.index < INT3_E)]
    print(f"\n  区間3 (2026-02-05〜02-07):")
    print(f"    v10: {dict(int3_v10['pred'].value_counts())}")
    print(f"    v13: {dict(int3_v13['pred'].value_counts())}")

    print("\n完了。")


if __name__ == "__main__":
    main()
