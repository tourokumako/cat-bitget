"""数値ルール候補をground truthに対して評価する（層2）。

評価方式（日次切り替え + 最頻値集計）:
  ・ルールは t日0時時点で「t-1日までの確定値」のみを使い、その日のregimeを判定する（look-ahead禁止）。
  ・各週7日間の日次予測を集計し、最頻値ラベルを「週支配」とする。
  ・週支配がground truthラベルと一致するか採点。
  ・評価対象は ground truth でラベル付き(uptrend/downtrend/range)の週のみ。

入力:
  data/regime_ground_truth.csv（53週）
  data/BTCUSDT-5m-2025-04-01_03-31_365d.csv（5m足CSV）
  data/warmup/daily_warmup_BTCUSDT.csv（warmup日足）

出力:
  標準出力: 各ルールの正解率・クラス別再現率・混同行列
  results/regime_rules_eval.json: 構造化結果
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Callable, Dict, List

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
GROUND_TRUTH_PATH = REPO_ROOT / "data" / "regime_ground_truth.csv"  # 旧・週単位・肉眼（並走比較用）
GROUND_TRUTH_DAILY_PATH = REPO_ROOT / "data" / "regime_ground_truth_daily.csv"  # 機械（破棄予定）
GROUND_TRUTH_DAILY_HUMAN_PATH = REPO_ROOT / "data" / "regime_ground_truth_daily_human.csv"  # 正本・肉眼日次
CSV_5M_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2025-04-01_03-31_365d.csv"
DAILY_WARMUP_PATH = REPO_ROOT / "data" / "warmup" / "daily_warmup_BTCUSDT.csv"
OUT_PATH = REPO_ROOT / "results" / "regime_rules_eval.json"

LABELS = ("uptrend", "downtrend", "range")


def _load_ground_truth() -> Dict[str, str]:
    out: Dict[str, str] = {}
    with GROUND_TRUTH_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = (row.get("label") or "").strip()
            week = (row.get("week_start") or "").strip()
            if not week:
                continue
            out[week] = label
    return out


def _load_ground_truth_daily() -> Dict[str, str]:
    out: Dict[str, str] = {}
    with GROUND_TRUTH_DAILY_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = (row.get("label") or "").strip()
            date = (row.get("date") or "").strip()
            if not date:
                continue
            out[date] = label
    return out


def _load_5m() -> pd.DataFrame:
    df_5m = pd.read_csv(CSV_5M_PATH)
    df_5m["ts"] = pd.to_datetime(df_5m["timestamp"])
    for c in ("open", "high", "low", "close", "volume"):
        if c in df_5m.columns:
            df_5m[c] = pd.to_numeric(df_5m[c], errors="coerce")
    return df_5m.set_index("ts").sort_index()


def _load_daily_with_warmup(df_5m: pd.DataFrame = None) -> pd.DataFrame:
    """5m → 日足 + warmup を結合した日足DataFrameを返す（インデックス=日付・UTC基準）。"""
    if df_5m is None:
        df_5m = _load_5m()
    daily = df_5m.resample("D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()

    if DAILY_WARMUP_PATH.exists():
        dw = pd.read_csv(DAILY_WARMUP_PATH)
        dw["ts"] = pd.to_datetime(dw["timestamp"])
        for c in ("open", "high", "low", "close"):
            if c in dw.columns:
                dw[c] = pd.to_numeric(dw[c], errors="coerce")
        dw = dw.set_index("ts").sort_index()
        cols = ["open", "high", "low", "close"]
        cols = [c for c in cols if c in dw.columns]
        combined = pd.concat([dw[cols], daily[cols]])
        combined = combined[~combined.index.duplicated(keep="last")].sort_index()
        return combined
    return daily


# ====== ルール定義 ======
# シグネチャ: (daily, df_5m, target_date) -> ラベル
# 各ルールは「target_dateのregime」を「target_date前日(5m足は前確定バー)まで」のデータのみで判定する。

def rule_R1_weekly_return_sign(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R1: 「前日終値時点の直近7日間 close 騰落率」の符号で判定。
    ground truth とほぼ同型のベースライン上限（ただしlook-aheadなし版）。"""
    end = target_date - pd.Timedelta(days=1)
    start = end - pd.Timedelta(days=6)
    seg = daily.loc[(daily.index >= start) & (daily.index <= end)]
    if len(seg) < 5:
        return "unknown"
    r = (seg["close"].iloc[-1] - seg["close"].iloc[0]) / seg["close"].iloc[0] * 100
    if abs(r) < 1.0:
        return "range"
    return "uptrend" if r > 0 else "downtrend"


def rule_R2_gamma(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R2-γ: 日足 close vs MA20 + ADX_14 + 直近5日 return（前日終値時点）。

    判定:
      ① 直近5日 return（前日close / 5日前close - 1）
      ② close_yesterday vs MA20_yesterday
      ③ ADX_14_yesterday（trend強度）
      → 全て前日までの確定値で計算

    分類:
      ADX < 20 → range
      close > MA20 AND 5d_return > +1.5% → uptrend
      close < MA20 AND 5d_return < -1.5% → downtrend
      それ以外 → range（弱trendはrange扱い）
    """
    try:
        import ta
    except ImportError:
        return "unknown"

    end = target_date - pd.Timedelta(days=1)
    seg = daily.loc[daily.index <= end].copy()
    if len(seg) < 30:
        return "unknown"

    seg["ma20"] = seg["close"].rolling(20, min_periods=20).mean()
    adx = ta.trend.ADXIndicator(seg["high"], seg["low"], seg["close"], window=14)
    seg["adx"] = adx.adx()

    last = seg.iloc[-1]
    if pd.isna(last["ma20"]) or pd.isna(last["adx"]):
        return "unknown"

    five_ago_idx = seg.index[-6] if len(seg) >= 6 else None
    if five_ago_idx is None:
        return "unknown"
    ret_5d = (last["close"] - seg.loc[five_ago_idx, "close"]) / seg.loc[five_ago_idx, "close"] * 100

    if last["adx"] < 20:
        return "range"
    if last["close"] > last["ma20"] and ret_5d > 1.5:
        return "uptrend"
    if last["close"] < last["ma20"] and ret_5d < -1.5:
        return "downtrend"
    return "range"


def rule_R3_ma5_ma20_cross(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R3: 日足 MA5 vs MA20 ゴールデン/デッドクロス + 直近5日 return（弱trendはrange）。

    判定（前日確定値）:
      ma5 > ma20 AND ret_5d > +1.0% → uptrend
      ma5 < ma20 AND ret_5d < -1.0% → downtrend
      それ以外 → range
    """
    end = target_date - pd.Timedelta(days=1)
    seg = daily.loc[daily.index <= end].copy()
    if len(seg) < 25:
        return "unknown"
    seg["ma5"] = seg["close"].rolling(5, min_periods=5).mean()
    seg["ma20"] = seg["close"].rolling(20, min_periods=20).mean()
    last = seg.iloc[-1]
    if pd.isna(last["ma5"]) or pd.isna(last["ma20"]):
        return "unknown"
    if len(seg) < 6:
        return "unknown"
    five_ago = seg["close"].iloc[-6]
    ret_5d = (last["close"] - five_ago) / five_ago * 100

    if last["ma5"] > last["ma20"] and ret_5d > 1.0:
        return "uptrend"
    if last["ma5"] < last["ma20"] and ret_5d < -1.0:
        return "downtrend"
    return "range"


def rule_R4_short_long_ma(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R4: 短期 MA5 と長期 MA20 の位置関係 + close vs MA20。

    判定（前日確定値）:
      close > MA20 AND MA5 > MA20 → uptrend
      close < MA20 AND MA5 < MA20 → downtrend
      上記外（位置関係不一致）→ range
    """
    end = target_date - pd.Timedelta(days=1)
    seg = daily.loc[daily.index <= end].copy()
    if len(seg) < 25:
        return "unknown"
    seg["ma5"] = seg["close"].rolling(5, min_periods=5).mean()
    seg["ma20"] = seg["close"].rolling(20, min_periods=20).mean()
    last = seg.iloc[-1]
    if pd.isna(last["ma5"]) or pd.isna(last["ma20"]):
        return "unknown"
    if last["close"] > last["ma20"] and last["ma5"] > last["ma20"]:
        return "uptrend"
    if last["close"] < last["ma20"] and last["ma5"] < last["ma20"]:
        return "downtrend"
    return "range"


def rule_R5_hourly_ma168(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R5: 1h相当の MA168（=7日相当）と close の位置関係（look-ahead禁止）。

    daily は5m由来の日足だが、1h MA168 は 168本=7日窓 → 日足換算で MA7 close 比較に等価。
    判定（前日確定値）:
      close > MA7 AND MA7 上昇（MA7[t-1] > MA7[t-3]）→ uptrend
      close < MA7 AND MA7 下降 → downtrend
      上記外 → range
    """
    end = target_date - pd.Timedelta(days=1)
    seg = daily.loc[daily.index <= end].copy()
    if len(seg) < 12:
        return "unknown"
    seg["ma7"] = seg["close"].rolling(7, min_periods=7).mean()
    if pd.isna(seg["ma7"].iloc[-1]) or pd.isna(seg["ma7"].iloc[-3]):
        return "unknown"
    last = seg.iloc[-1]
    ma7_now = seg["ma7"].iloc[-1]
    ma7_prev = seg["ma7"].iloc[-3]
    if last["close"] > ma7_now and ma7_now > ma7_prev:
        return "uptrend"
    if last["close"] < ma7_now and ma7_now < ma7_prev:
        return "downtrend"
    return "range"


def rule_R6_5m_72h(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R6: 5m足直接・過去72h窓・close vs MA864 + 24h return（簡素版）。

    判定（target_date 0時時点・前確定5m足まで使用）:
      ① 過去72h（864本）の close 平均と直前 close を比較
      ② 過去24h（288本）の return

    分類:
      close > MA864 AND ret_24h > +0.5% → uptrend
      close < MA864 AND ret_24h < -0.5% → downtrend
      上記外 → range

    L: up_ratio 条件は5m足ノイズで機能しない（BTCは強trend中も50%付近）→削除済。
    """
    end_excl = target_date
    seg = df_5m.loc[df_5m.index < end_excl]
    if len(seg) < 864:
        return "unknown"
    seg = seg.iloc[-864:]
    closes = seg["close"].values
    last_close = closes[-1]
    ma864 = closes.mean()

    closes_24h = seg.iloc[-288:]["close"].values
    if len(closes_24h) < 2 or closes_24h[0] == 0:
        return "unknown"
    ret_24h = (closes_24h[-1] - closes_24h[0]) / closes_24h[0] * 100

    if last_close > ma864 and ret_24h > 0.5:
        return "uptrend"
    if last_close < ma864 and ret_24h < -0.5:
        return "downtrend"
    return "range"


def _classify_window_5m(seg_5m: pd.DataFrame, ma_window_bars: int, ret_bars: int, ret_thresh: float) -> str:
    """5m足の任意窓・任意return期間で簡易判定（補助関数）。"""
    if len(seg_5m) < max(ma_window_bars, ret_bars + 1):
        return "unknown"
    seg = seg_5m.iloc[-ma_window_bars:]
    last_close = seg["close"].iloc[-1]
    ma = seg["close"].mean()
    ret_seg = seg_5m.iloc[-(ret_bars + 1):]
    if ret_seg["close"].iloc[0] == 0:
        return "unknown"
    ret = (ret_seg["close"].iloc[-1] - ret_seg["close"].iloc[0]) / ret_seg["close"].iloc[0] * 100
    if last_close > ma and ret > ret_thresh:
        return "uptrend"
    if last_close < ma and ret < -ret_thresh:
        return "downtrend"
    return "range"


def rule_R7_ensemble(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R7: 多重時間窓アンサンブル。24h/72h/168h/336h の4窓で予測 → 多数決。

    各窓の判定（前確定5m足まで）:
      - 24h:  MA288   / ret_24h  / 閾値 0.5%
      - 72h:  MA864   / ret_72h  / 閾値 1.0%
      - 168h: MA2016  / ret_168h / 閾値 2.0%
      - 336h: MA4032  / ret_336h / 閾値 3.0%

    集計:
      4票中 ≥3 が同じ trend → そのラベル採用
      同数同票 or rangeが多数 → range
    """
    end_excl = target_date
    seg = df_5m.loc[df_5m.index < end_excl]
    if len(seg) < 4032:
        return "unknown"

    votes = [
        _classify_window_5m(seg, 288, 288, 0.5),
        _classify_window_5m(seg, 864, 864, 1.0),
        _classify_window_5m(seg, 2016, 2016, 2.0),
        _classify_window_5m(seg, 4032, 4032, 3.0),
    ]
    cnt = Counter(votes)
    if cnt.get("uptrend", 0) >= 3:
        return "uptrend"
    if cnt.get("downtrend", 0) >= 3:
        return "downtrend"
    return "range"


def rule_R8_ema_long(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R8: 日足 EMA20 vs EMA50（クラシカルな長中期）。

    判定（前日確定値・指数移動平均）:
      close > EMA20 > EMA50 AND ret_10d > +1.0% → uptrend
      close < EMA20 < EMA50 AND ret_10d < -1.0% → downtrend
      上記外 → range
    """
    end = target_date - pd.Timedelta(days=1)
    seg = daily.loc[daily.index <= end].copy()
    if len(seg) < 60:
        return "unknown"
    seg["ema20"] = seg["close"].ewm(span=20, adjust=False).mean()
    seg["ema50"] = seg["close"].ewm(span=50, adjust=False).mean()
    last = seg.iloc[-1]
    if pd.isna(last["ema20"]) or pd.isna(last["ema50"]):
        return "unknown"
    ten_ago = seg["close"].iloc[-11] if len(seg) >= 11 else None
    if ten_ago is None or ten_ago == 0:
        return "unknown"
    ret_10d = (last["close"] - ten_ago) / ten_ago * 100

    if last["close"] > last["ema20"] > last["ema50"] and ret_10d > 1.0:
        return "uptrend"
    if last["close"] < last["ema20"] < last["ema50"] and ret_10d < -1.0:
        return "downtrend"
    return "range"


def rule_R9_ma14_30(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R9: 日足 close vs MA14 + MA30 + ret_14d（中期窓・週短期ノイズに頑健）。

    判定:
      close > MA14 AND MA14 > MA30 AND ret_14d > +2.0% → uptrend
      close < MA14 AND MA14 < MA30 AND ret_14d < -2.0% → downtrend
      上記外 → range
    """
    end = target_date - pd.Timedelta(days=1)
    seg = daily.loc[daily.index <= end].copy()
    if len(seg) < 35:
        return "unknown"
    seg["ma14"] = seg["close"].rolling(14, min_periods=14).mean()
    seg["ma30"] = seg["close"].rolling(30, min_periods=30).mean()
    last = seg.iloc[-1]
    if pd.isna(last["ma14"]) or pd.isna(last["ma30"]):
        return "unknown"
    fourteen_ago = seg["close"].iloc[-15] if len(seg) >= 15 else None
    if fourteen_ago is None or fourteen_ago == 0:
        return "unknown"
    ret_14d = (last["close"] - fourteen_ago) / fourteen_ago * 100

    if last["close"] > last["ma14"] and last["ma14"] > last["ma30"] and ret_14d > 2.0:
        return "uptrend"
    if last["close"] < last["ma14"] and last["ma14"] < last["ma30"] and ret_14d < -2.0:
        return "downtrend"
    return "range"


def rule_R10_zscore(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R10: 過去30日 close 平均からの z-score（ボラ正規化）。

    判定:
      z-score > +1.0 → uptrend
      z-score < -1.0 → downtrend
      |z| <= 1.0 → range
    """
    end = target_date - pd.Timedelta(days=1)
    seg = daily.loc[daily.index <= end].copy()
    if len(seg) < 30:
        return "unknown"
    last_close = seg["close"].iloc[-1]
    window = seg["close"].iloc[-30:]
    mean = window.mean()
    std = window.std(ddof=0)
    if std == 0:
        return "range"
    z = (last_close - mean) / std
    if z > 1.0:
        return "uptrend"
    if z < -1.0:
        return "downtrend"
    return "range"


def rule_R11_roc_adx(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R11: 14日 ROC + ADX_14（モメンタム + trend強度）。

    判定:
      ADX < 20 → range（trend弱い）
      ROC_14 > +5% AND ADX >= 20 → uptrend
      ROC_14 < -5% AND ADX >= 20 → downtrend
      上記外 → range
    """
    try:
        import ta
    except ImportError:
        return "unknown"
    end = target_date - pd.Timedelta(days=1)
    seg = daily.loc[daily.index <= end].copy()
    if len(seg) < 30:
        return "unknown"
    adx_obj = ta.trend.ADXIndicator(seg["high"], seg["low"], seg["close"], window=14)
    seg["adx"] = adx_obj.adx()
    last = seg.iloc[-1]
    if pd.isna(last["adx"]):
        return "unknown"
    fourteen_ago = seg["close"].iloc[-15] if len(seg) >= 15 else None
    if fourteen_ago is None or fourteen_ago == 0:
        return "unknown"
    roc_14 = (last["close"] - fourteen_ago) / fourteen_ago * 100

    if last["adx"] < 20:
        return "range"
    if roc_14 > 5.0:
        return "uptrend"
    if roc_14 < -5.0:
        return "downtrend"
    return "range"


def rule_R12_ranking(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R12: 過去30日の close 分布における直近 close の位置（パーセンタイル）。

    判定:
      直近close >= 30日70%tile以上 AND ret_7d > +0.5% → uptrend
      直近close <= 30日30%tile以下 AND ret_7d < -0.5% → downtrend
      上記外 → range
    """
    end = target_date - pd.Timedelta(days=1)
    seg = daily.loc[daily.index <= end].copy()
    if len(seg) < 30:
        return "unknown"
    last_close = seg["close"].iloc[-1]
    window = seg["close"].iloc[-30:]
    p70 = window.quantile(0.7)
    p30 = window.quantile(0.3)
    seven_ago = seg["close"].iloc[-8] if len(seg) >= 8 else None
    if seven_ago is None or seven_ago == 0:
        return "unknown"
    ret_7d = (last_close - seven_ago) / seven_ago * 100

    if last_close >= p70 and ret_7d > 0.5:
        return "uptrend"
    if last_close <= p30 and ret_7d < -0.5:
        return "downtrend"
    return "range"


def rule_R13_dual_horizon(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R13: 短期（7日 close vs MA7）と中期（14日 close vs MA14）の両方一致を要求。

    判定:
      ma7 > ma14 AND close > ma7 AND ret_7d > +0.5% → uptrend
      ma7 < ma14 AND close < ma7 AND ret_7d < -0.5% → downtrend
      上記外 → range
    """
    end = target_date - pd.Timedelta(days=1)
    seg = daily.loc[daily.index <= end].copy()
    if len(seg) < 20:
        return "unknown"
    seg["ma7"] = seg["close"].rolling(7).mean()
    seg["ma14"] = seg["close"].rolling(14).mean()
    last = seg.iloc[-1]
    if pd.isna(last["ma7"]) or pd.isna(last["ma14"]):
        return "unknown"
    seven_ago = seg["close"].iloc[-8] if len(seg) >= 8 else None
    if seven_ago is None or seven_ago == 0:
        return "unknown"
    ret_7d = (last["close"] - seven_ago) / seven_ago * 100

    if last["ma7"] > last["ma14"] and last["close"] > last["ma7"] and ret_7d > 0.5:
        return "uptrend"
    if last["ma7"] < last["ma14"] and last["close"] < last["ma7"] and ret_7d < -0.5:
        return "downtrend"
    return "range"


def rule_R14_continuous_trend(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R14: 過去5日連続で同方向trend（強い継続性のみ confident 判定）。

    判定:
      過去5日それぞれの close > 前日close → 5/5連続上昇 → uptrend
      過去5日それぞれの close < 前日close → 5/5連続下落 → downtrend
      上記いずれでもない → range
    """
    end = target_date - pd.Timedelta(days=1)
    seg = daily.loc[daily.index <= end].copy()
    if len(seg) < 6:
        return "unknown"
    last_5 = seg["close"].iloc[-6:].values  # 6点で5日変化
    if len(last_5) < 6:
        return "unknown"
    diffs = last_5[1:] - last_5[:-1]
    if (diffs > 0).all():
        return "uptrend"
    if (diffs < 0).all():
        return "downtrend"
    return "range"


def rule_R15_consensus_3rules(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R15: R5 + R6改 + R9 の合意制（3票中2票一致なら採用・全部不一致は range）。"""
    votes = [
        rule_R5_hourly_ma168(daily, df_5m, target_date),
        rule_R6_5m_72h(daily, df_5m, target_date),
        rule_R9_ma14_30(daily, df_5m, target_date),
    ]
    cnt = Counter(votes)
    for lab in LABELS:
        if cnt.get(lab, 0) >= 2:
            return lab
    return "range"


def rule_R16_vwap(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R16: 出来高加重平均 (VWAP) と直前 close の比較。168h窓。

    判定（前確定5m足まで）:
      vwap = sum(close*volume) / sum(volume)
      close > vwap * 1.005 AND ret_24h > +0.5% → uptrend
      close < vwap * 0.995 AND ret_24h < -0.5% → downtrend
      上記外 → range
    """
    end_excl = target_date
    seg = df_5m.loc[df_5m.index < end_excl]
    if len(seg) < 2016 or "volume" not in seg.columns:
        return "unknown"
    seg = seg.iloc[-2016:]
    if seg["volume"].sum() == 0:
        return "unknown"
    vwap = (seg["close"] * seg["volume"]).sum() / seg["volume"].sum()
    last_close = seg["close"].iloc[-1]
    closes_24h = seg.iloc[-288:]["close"].values
    if len(closes_24h) < 2 or closes_24h[0] == 0:
        return "unknown"
    ret_24h = (closes_24h[-1] - closes_24h[0]) / closes_24h[0] * 100

    if last_close > vwap * 1.005 and ret_24h > 0.5:
        return "uptrend"
    if last_close < vwap * 0.995 and ret_24h < -0.5:
        return "downtrend"
    return "range"


def rule_R17_volume_weighted_trend(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R17: 過去72h窓で出来高加重した「上下バーの volume 比」+ ret_72h。

    判定:
      過去72h で「up bar volume / total volume」を計算
      vol_up_ratio > 0.55 AND ret_72h > +1.0% → uptrend
      vol_up_ratio < 0.45 AND ret_72h < -1.0% → downtrend
      上記外 → range
    """
    end_excl = target_date
    seg = df_5m.loc[df_5m.index < end_excl]
    if len(seg) < 864 or "volume" not in seg.columns:
        return "unknown"
    seg = seg.iloc[-864:].copy()
    seg["dir"] = (seg["close"] > seg["open"]).astype(int)
    total_vol = seg["volume"].sum()
    if total_vol == 0:
        return "unknown"
    up_vol_ratio = (seg["volume"] * seg["dir"]).sum() / total_vol
    closes = seg["close"].values
    if closes[0] == 0:
        return "unknown"
    ret_72h = (closes[-1] - closes[0]) / closes[0] * 100

    if up_vol_ratio > 0.55 and ret_72h > 1.0:
        return "uptrend"
    if up_vol_ratio < 0.45 and ret_72h < -1.0:
        return "downtrend"
    return "range"


def rule_R18_5m_trend_continuity(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R18: 5m高解像度・直近24h を 12個の2h時間帯に分割し、各2h trend を集計。

    判定:
      各2h窓: 開始close→終了close の符号
      12窓中 ≥8 が同方向 → そのトレンド
      上記外 → range
    """
    end_excl = target_date
    seg = df_5m.loc[df_5m.index < end_excl]
    if len(seg) < 288:
        return "unknown"
    seg = seg.iloc[-288:]
    bars_per_2h = 24
    n_windows = 12
    ups = 0
    dns = 0
    for i in range(n_windows):
        sub = seg.iloc[i * bars_per_2h:(i + 1) * bars_per_2h]
        if len(sub) < 2:
            continue
        if sub["close"].iloc[-1] > sub["close"].iloc[0]:
            ups += 1
        elif sub["close"].iloc[-1] < sub["close"].iloc[0]:
            dns += 1
    if ups >= 8:
        return "uptrend"
    if dns >= 8:
        return "downtrend"
    return "range"


def rule_R19_multi_horizon_majority(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R19: 6窓多数決アンサンブル（24h/48h/72h/120h/168h/336h）。

    各窓: ret > +閾値 → up / ret < -閾値 → dn / それ以外 → range
    閾値はwindow比例で設定。多数決 ≥4 を要求。
    """
    end_excl = target_date
    seg = df_5m.loc[df_5m.index < end_excl]
    if len(seg) < 4032:
        return "unknown"
    windows = [
        (288, 0.5),
        (576, 1.0),
        (864, 1.5),
        (1440, 2.5),
        (2016, 3.0),
        (4032, 4.0),
    ]
    votes = []
    for bars, thr in windows:
        sub = seg.iloc[-bars:]
        if sub["close"].iloc[0] == 0:
            votes.append("range")
            continue
        ret = (sub["close"].iloc[-1] - sub["close"].iloc[0]) / sub["close"].iloc[0] * 100
        if ret > thr:
            votes.append("uptrend")
        elif ret < -thr:
            votes.append("downtrend")
        else:
            votes.append("range")
    cnt = Counter(votes)
    if cnt.get("uptrend", 0) >= 4:
        return "uptrend"
    if cnt.get("downtrend", 0) >= 4:
        return "downtrend"
    return "range"


def rule_R20_4h_resample(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R20: 4h足にresampleし、過去42本（=7日相当）の MA42 close比較 + slope。

    判定:
      close > MA42 AND MA42上昇（now > 6本前）→ uptrend
      close < MA42 AND MA42下降 → downtrend
      上記外 → range
    """
    end_excl = target_date
    seg = df_5m.loc[df_5m.index < end_excl]
    if len(seg) < 2016:
        return "unknown"
    h4 = seg.resample("4h").agg({"close": "last"}).dropna()
    if len(h4) < 42:
        return "unknown"
    h4["ma42"] = h4["close"].rolling(42, min_periods=42).mean()
    last = h4.iloc[-1]
    if pd.isna(last["ma42"]) or len(h4) < 7:
        return "unknown"
    ma_now = h4["ma42"].iloc[-1]
    ma_prev = h4["ma42"].iloc[-7]
    if pd.isna(ma_prev):
        return "unknown"
    if last["close"] > ma_now and ma_now > ma_prev:
        return "uptrend"
    if last["close"] < ma_now and ma_now < ma_prev:
        return "downtrend"
    return "range"


def rule_R21_1h_ema(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R21: 1h足 EMA20 / EMA72 + close位置。

    判定:
      close > EMA20 > EMA72 → uptrend
      close < EMA20 < EMA72 → downtrend
      上記外 → range
    """
    end_excl = target_date
    seg = df_5m.loc[df_5m.index < end_excl]
    if len(seg) < 1000:
        return "unknown"
    h1 = seg.resample("1h").agg({"close": "last"}).dropna()
    if len(h1) < 100:
        return "unknown"
    h1["ema20"] = h1["close"].ewm(span=20, adjust=False).mean()
    h1["ema72"] = h1["close"].ewm(span=72, adjust=False).mean()
    last = h1.iloc[-1]
    if pd.isna(last["ema20"]) or pd.isna(last["ema72"]):
        return "unknown"
    if last["close"] > last["ema20"] > last["ema72"]:
        return "uptrend"
    if last["close"] < last["ema20"] < last["ema72"]:
        return "downtrend"
    return "range"


def rule_R22_higher_highs_lows(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R22: 過去7日の日足で higher highs / lower lows を判定。

    判定:
      直近4日で高値が単調増加 → uptrend
      直近4日で安値が単調減少 → downtrend
      上記外 → range
    """
    end = target_date - pd.Timedelta(days=1)
    seg = daily.loc[daily.index <= end].copy()
    if len(seg) < 7:
        return "unknown"
    last4_h = seg["high"].iloc[-4:].values
    last4_l = seg["low"].iloc[-4:].values
    h_inc = all(last4_h[i + 1] > last4_h[i] for i in range(3))
    l_dec = all(last4_l[i + 1] < last4_l[i] for i in range(3))
    if h_inc:
        return "uptrend"
    if l_dec:
        return "downtrend"
    return "range"


def rule_R23_atr_trend(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R23: ATR_14 で正規化した return（ATR比でトレンドの強さ判定）。

    判定:
      ret_7d / atr_14 > +1.5 → uptrend
      ret_7d / atr_14 < -1.5 → downtrend
      上記外 → range
    """
    try:
        import ta
    except ImportError:
        return "unknown"
    end = target_date - pd.Timedelta(days=1)
    seg = daily.loc[daily.index <= end].copy()
    if len(seg) < 30:
        return "unknown"
    atr_obj = ta.volatility.AverageTrueRange(seg["high"], seg["low"], seg["close"], window=14)
    seg["atr"] = atr_obj.average_true_range()
    last = seg.iloc[-1]
    if pd.isna(last["atr"]) or last["atr"] == 0:
        return "unknown"
    seven_ago = seg["close"].iloc[-8] if len(seg) >= 8 else None
    if seven_ago is None:
        return "unknown"
    ret_abs = last["close"] - seven_ago
    norm = ret_abs / last["atr"]
    if norm > 1.5:
        return "uptrend"
    if norm < -1.5:
        return "downtrend"
    return "range"


def rule_R24_volume_surge_direction(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R24: 出来高急増バーの方向比率（過去48h）。

    判定:
      過去48h（576本）で「volume > 平均×1.5 倍」のバーを抽出
      これらの bar が close > open の比率 > 0.55 AND ret_48h > +1% → uptrend
      < 0.45 AND ret_48h < -1% → downtrend
      上記外 → range
    """
    end_excl = target_date
    seg = df_5m.loc[df_5m.index < end_excl]
    if len(seg) < 576 or "volume" not in seg.columns:
        return "unknown"
    seg = seg.iloc[-576:].copy()
    avg_vol = seg["volume"].mean()
    if avg_vol == 0:
        return "unknown"
    surge = seg[seg["volume"] > avg_vol * 1.5]
    if len(surge) < 5:
        return "range"  # 急増バー少ない → range
    up_ratio = (surge["close"] > surge["open"]).mean()
    closes = seg["close"].values
    if closes[0] == 0:
        return "unknown"
    ret_48h = (closes[-1] - closes[0]) / closes[0] * 100
    if up_ratio > 0.55 and ret_48h > 1.0:
        return "uptrend"
    if up_ratio < 0.45 and ret_48h < -1.0:
        return "downtrend"
    return "range"


def rule_R25_super_consensus(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R25: 7ルール大合議（R5/R6/R16/R17/R18/R20/R22）→ 4票以上一致で採用。"""
    votes = [
        rule_R5_hourly_ma168(daily, df_5m, target_date),
        rule_R6_5m_72h(daily, df_5m, target_date),
        rule_R16_vwap(daily, df_5m, target_date),
        rule_R17_volume_weighted_trend(daily, df_5m, target_date),
        rule_R18_5m_trend_continuity(daily, df_5m, target_date),
        rule_R20_4h_resample(daily, df_5m, target_date),
        rule_R22_higher_highs_lows(daily, df_5m, target_date),
    ]
    cnt = Counter(votes)
    for lab in LABELS:
        if cnt.get(lab, 0) >= 4:
            return lab
    return "range"


def rule_R6b_5m_48h_window(daily: pd.DataFrame, df_5m: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """R6改改: 5m足・過去72h MA + 過去48h return（土日ノイズの相対影響を48h窓で抑える）。

    判定（target_date 0時時点・前確定5m足まで）:
      ① 過去72h（864本）の close 平均 vs 直前 close
      ② 過去48h（576本）の return（48h前 close → 直前 close）

    分類:
      close > MA864 AND ret_48h > +1.0% → uptrend
      close < MA864 AND ret_48h < -1.0% → downtrend
      上記外 → range

    狙い: 月曜0時時点で先週金-土-日の動きが48h windowに入る → 前週後半trendを反映。
    """
    end_excl = target_date
    seg = df_5m.loc[df_5m.index < end_excl]
    if len(seg) < 864:
        return "unknown"
    seg = seg.iloc[-864:]
    closes = seg["close"].values
    last_close = closes[-1]
    ma864 = closes.mean()

    closes_48h = seg.iloc[-576:]["close"].values
    if len(closes_48h) < 2 or closes_48h[0] == 0:
        return "unknown"
    ret_48h = (closes_48h[-1] - closes_48h[0]) / closes_48h[0] * 100

    if last_close > ma864 and ret_48h > 1.0:
        return "uptrend"
    if last_close < ma864 and ret_48h < -1.0:
        return "downtrend"
    return "range"


RULES: Dict[str, Callable[[pd.DataFrame, pd.DataFrame, pd.Timestamp], str]] = {
    "R1_weekly_return_sign": rule_R1_weekly_return_sign,
    "R2_gamma": rule_R2_gamma,
    "R3_ma5_ma20_cross": rule_R3_ma5_ma20_cross,
    "R4_short_long_ma": rule_R4_short_long_ma,
    "R5_hourly_ma168": rule_R5_hourly_ma168,
    "R6_5m_72h": rule_R6_5m_72h,
    "R6b_5m_48h_window": rule_R6b_5m_48h_window,
    "R7_ensemble": rule_R7_ensemble,
    "R8_ema_long": rule_R8_ema_long,
    "R9_ma14_30": rule_R9_ma14_30,
    "R10_zscore": rule_R10_zscore,
    "R11_roc_adx": rule_R11_roc_adx,
    "R12_ranking": rule_R12_ranking,
    "R13_dual_horizon": rule_R13_dual_horizon,
    "R14_continuous_trend": rule_R14_continuous_trend,
    "R15_consensus_3rules": rule_R15_consensus_3rules,
    "R16_vwap": rule_R16_vwap,
    "R17_volume_weighted_trend": rule_R17_volume_weighted_trend,
    "R18_5m_trend_continuity": rule_R18_5m_trend_continuity,
    "R19_multi_horizon_majority": rule_R19_multi_horizon_majority,
    "R20_4h_resample": rule_R20_4h_resample,
    "R21_1h_ema": rule_R21_1h_ema,
    "R22_higher_highs_lows": rule_R22_higher_highs_lows,
    "R23_atr_trend": rule_R23_atr_trend,
    "R24_volume_surge_direction": rule_R24_volume_surge_direction,
    "R25_super_consensus": rule_R25_super_consensus,
}


# ====== 評価エンジン ======

def _week_dominant(daily_preds: List[str]) -> str:
    """日次予測7日分の最頻値（同数の場合は uptrend > downtrend > range > unknown）。"""
    if not daily_preds:
        return "unknown"
    cnt = Counter(daily_preds)
    priority = {"uptrend": 0, "downtrend": 1, "range": 2, "unknown": 3}
    sorted_items = sorted(cnt.items(), key=lambda x: (-x[1], priority.get(x[0], 99)))
    return sorted_items[0][0]


def _score(by_week: List[dict], pred_key: str) -> dict:
    confusion: Dict[str, Dict[str, int]] = {l: {ll: 0 for ll in LABELS} for l in LABELS}
    correct = 0
    total_eval = 0
    for r in by_week:
        if r["true"] not in LABELS:
            continue
        total_eval += 1
        pred = r[pred_key]
        if pred == r["true"]:
            correct += 1
        if pred in LABELS:
            confusion[r["true"]][pred] += 1

    per_class = {}
    for lab in LABELS:
        n = sum(1 for r in by_week if r["true"] == lab)
        match = sum(1 for r in by_week if r["true"] == lab and r[pred_key] == lab)
        per_class[lab] = {"recall": round(match / n, 3) if n else None, "n": n}

    return {
        "n_eval": total_eval,
        "n_correct": correct,
        "accuracy": round(correct / total_eval, 3) if total_eval else None,
        "per_class": per_class,
        "confusion": confusion,
    }


def evaluate(name: str, rule, gt: Dict[str, str], daily: pd.DataFrame, df_5m: pd.DataFrame) -> dict:
    """採点方式 3種を併記:
       D = 月曜0時単点（先週確定値ベース・1週ラグ構造）
       A = 週内7日最頻値
       C = 日曜（offset=6）時点の判定（週内月-土の確定値が入る・最も情報量大）
    """
    by_week: List[dict] = []
    for week_str, true_label in gt.items():
        week_start = pd.to_datetime(week_str)
        daily_preds = []
        for offset in range(7):
            d = week_start + pd.Timedelta(days=offset)
            daily_preds.append(rule(daily, df_5m, d))
        by_week.append({
            "week_start": week_str,
            "true": true_label,
            "pred_D_monday": daily_preds[0],
            "pred_C_sunday": daily_preds[6],
            "pred_A_dominant": _week_dominant(daily_preds),
            "daily_preds": daily_preds,
        })

    return {
        "scoring_D_monday": _score(by_week, "pred_D_monday"),
        "scoring_C_sunday": _score(by_week, "pred_C_sunday"),
        "scoring_A_dominant": _score(by_week, "pred_A_dominant"),
        "by_week": by_week,
    }


def _print_score(label: str, sc: dict) -> None:
    if sc["accuracy"] is None:
        print(f"  [{label}] 評価サンプルなし")
        return
    print(f"  [{label}] 正解率: {sc['accuracy']:.1%} ({sc['n_correct']}/{sc['n_eval']} 週)")
    parts = []
    for lab in LABELS:
        pc = sc["per_class"][lab]
        if pc["recall"] is None:
            parts.append(f"{lab[:2]}=—")
        else:
            parts.append(f"{lab[:2]}={pc['recall']:.0%}(n={pc['n']})")
    print(f"        クラス別再現率: {' / '.join(parts)}")
    print(f"        混同行列 (行=true / 列=pred):")
    print(f"          {'':>11}{'uptrend':>10}{'downtrend':>11}{'range':>8}")
    for true_lab in LABELS:
        row = sc["confusion"][true_lab]
        print(f"          {true_lab:>11}{row['uptrend']:>10}{row['downtrend']:>11}{row['range']:>8}")


def _print_result(name: str, res: dict) -> None:
    print(f"\n=== {name} ===")
    _print_score("D 月曜0時単点", res["scoring_D_monday"])
    _print_score("C 日曜時点単点", res["scoring_C_sunday"])
    _print_score("A 週内最頻値", res["scoring_A_dominant"])


def _dow_accuracy(res: dict) -> Dict[str, float]:
    """各曜日 (0=月..6=日) の精度を返す。"""
    by_offset = {i: {"hit": 0, "n": 0} for i in range(7)}
    for r in res["by_week"]:
        if r["true"] not in LABELS:
            continue
        for i, p in enumerate(r["daily_preds"]):
            by_offset[i]["n"] += 1
            if p == r["true"]:
                by_offset[i]["hit"] += 1
    dow_names = ["月", "火", "水", "木", "金", "土", "日"]
    return {dow_names[i]: (by_offset[i]["hit"] / by_offset[i]["n"]) if by_offset[i]["n"] else 0.0
            for i in range(7)}


def _print_dow_accuracy(res: dict) -> None:
    accs = _dow_accuracy(res)
    print(f"  [曜日別 日次精度]")
    parts = [f"{k}={v:.1%}" for k, v in accs.items()]
    print(f"    {' / '.join(parts)}")
    vals = list(accs.values())
    print(f"    最低: {min(vals):.1%} / 平均: {sum(vals)/len(vals):.1%} / 80%以上達成日: {sum(1 for v in vals if v >= 0.8)}/7")


def evaluate_daily(name: str, rule, gt_daily: Dict[str, str], daily: pd.DataFrame, df_5m: pd.DataFrame) -> dict:
    """日次 ground truth に対する評価。各日のラベル vs 各ルール予測を直接照合。"""
    by_day: List[dict] = []
    confusion: Dict[str, Dict[str, int]] = {l: {ll: 0 for ll in LABELS} for l in LABELS}
    correct = 0
    total = 0
    dow_buckets = {i: {"hit": 0, "n": 0} for i in range(7)}

    for date_str, true_label in sorted(gt_daily.items()):
        if true_label not in LABELS:
            continue
        d = pd.to_datetime(date_str)
        pred = rule(daily, df_5m, d)
        by_day.append({"date": date_str, "true": true_label, "pred": pred})
        total += 1
        if pred == true_label:
            correct += 1
        if pred in LABELS:
            confusion[true_label][pred] += 1
        # 曜日: pandas weekday() = 月曜0
        dow = d.weekday()
        dow_buckets[dow]["n"] += 1
        if pred == true_label:
            dow_buckets[dow]["hit"] += 1

    per_class = {}
    for lab in LABELS:
        n = sum(1 for r in by_day if r["true"] == lab)
        match = sum(1 for r in by_day if r["true"] == lab and r["pred"] == lab)
        per_class[lab] = {"recall": round(match / n, 3) if n else None, "n": n}

    dow_names = ["月", "火", "水", "木", "金", "土", "日"]
    dow_acc = {dow_names[i]: (dow_buckets[i]["hit"] / dow_buckets[i]["n"]) if dow_buckets[i]["n"] else 0.0
               for i in range(7)}

    return {
        "n_eval": total,
        "n_correct": correct,
        "accuracy": round(correct / total, 3) if total else None,
        "per_class": per_class,
        "confusion": confusion,
        "dow_accuracy": dow_acc,
    }


def main() -> None:
    gt = _load_ground_truth()
    df_5m = _load_5m()
    daily = _load_daily_with_warmup(df_5m)
    print(f"ground truth: {len(gt)} 週")
    print(f"5m DF: {len(df_5m)} 本 ({df_5m.index.min()} 〜 {df_5m.index.max()})")
    print(f"daily DF: {len(daily)} 日 ({daily.index.min().date()} 〜 {daily.index.max().date()})")

    labeled = sum(1 for v in gt.values() if v in LABELS)
    print(f"評価対象（ラベル付き）: {labeled} 週")
    print(f"評価除外（未記入）: {len(gt) - labeled} 週")

    results = {}
    summary = []  # 全ルールの曜日別精度を最後にまとめる
    for name, rule in RULES.items():
        res = evaluate(name, rule, gt, daily, df_5m)
        _print_result(name, res)
        _print_dow_accuracy(res)
        results[name] = res
        accs = _dow_accuracy(res)
        vals = list(accs.values())
        summary.append({
            "rule": name,
            "dow": accs,
            "min": min(vals),
            "avg": sum(vals)/len(vals),
            "n_ge_80": sum(1 for v in vals if v >= 0.8),
            "n_ge_60": sum(1 for v in vals if v >= 0.6),
        })

    print("\n" + "=" * 90)
    print("=== [週単位 ground truth・肉眼判定] 全ルール 曜日別精度ランキング（最低値降順）===")
    print(f"{'rule':<27}{'min':>7}{'avg':>7}{'≥80日':>7}{'≥60日':>7}  {'月':>4}{'火':>4}{'水':>4}{'木':>4}{'金':>4}{'土':>4}{'日':>4}")
    summary.sort(key=lambda x: -x["min"])
    for s in summary:
        d = s["dow"]
        print(f"{s['rule']:<27}{s['min']:>6.0%}{s['avg']:>6.0%}{s['n_ge_80']:>5}/7{s['n_ge_60']:>5}/7  "
              f"{d['月']:>3.0%} {d['火']:>3.0%} {d['水']:>3.0%} {d['木']:>3.0%} {d['金']:>3.0%} {d['土']:>3.0%} {d['日']:>3.0%}")

    # ====== 日次 ground truth（肉眼正本）に対する評価（最重要・採点はここ）======
    if GROUND_TRUTH_DAILY_HUMAN_PATH.exists():
        gt_daily_human: Dict[str, str] = {}
        with GROUND_TRUTH_DAILY_HUMAN_PATH.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                d = (row.get("date") or "").strip()
                lab = (row.get("label") or "").strip()
                if d:
                    gt_daily_human[d] = lab
        labeled_h = sum(1 for v in gt_daily_human.values() if v in LABELS)
        print(f"\n{'=' * 90}")
        print(f"[日次 ground truth・肉眼正本] 評価対象: {labeled_h} 日")
        h_summary = []
        h_results = {}
        for name, rule in RULES.items():
            res_h = evaluate_daily(name, rule, gt_daily_human, daily, df_5m)
            h_results[name] = res_h
            vals = list(res_h["dow_accuracy"].values())
            h_summary.append({
                "rule": name,
                "acc": res_h["accuracy"] or 0.0,
                "dow": res_h["dow_accuracy"],
                "min": min(vals),
                "avg": sum(vals)/len(vals),
                "n_ge_80": sum(1 for v in vals if v >= 0.8),
                "n_ge_60": sum(1 for v in vals if v >= 0.6),
                "per_class": res_h["per_class"],
            })

        print("\n=== [日次 肉眼正本] 全ルール 曜日別精度ランキング（最低値降順）===")
        print(f"{'rule':<27}{'acc':>6}{'min':>7}{'avg':>7}{'≥80日':>7}{'≥60日':>7}  {'月':>4}{'火':>4}{'水':>4}{'木':>4}{'金':>4}{'土':>4}{'日':>4}  {'up_rec':>7}{'dn_rec':>7}{'rg_rec':>7}")
        h_summary.sort(key=lambda x: -x["acc"])
        for s in h_summary:
            d = s["dow"]
            pc = s["per_class"]
            up_r = pc["uptrend"]["recall"]
            dn_r = pc["downtrend"]["recall"]
            rg_r = pc["range"]["recall"]
            print(f"{s['rule']:<27}{s['acc']:>5.0%}{s['min']:>6.0%}{s['avg']:>6.0%}{s['n_ge_80']:>5}/7{s['n_ge_60']:>5}/7  "
                  f"{d['月']:>3.0%} {d['火']:>3.0%} {d['水']:>3.0%} {d['木']:>3.0%} {d['金']:>3.0%} {d['土']:>3.0%} {d['日']:>3.0%}  "
                  f"{(up_r or 0):>6.0%} {(dn_r or 0):>6.0%} {(rg_r or 0):>6.0%}")

        results["_human_daily_eval"] = h_results

    # ====== 日次 ground truth（機械生成）に対する評価（参考） ======
    if GROUND_TRUTH_DAILY_PATH.exists():
        gt_daily = _load_ground_truth_daily()
        labeled_daily = sum(1 for v in gt_daily.values() if v in LABELS)
        print(f"\n[参考: 機械生成 ground truth] 評価対象: {labeled_daily} 日")
        daily_summary = []
        daily_results = {}
        for name, rule in RULES.items():
            res_d = evaluate_daily(name, rule, gt_daily, daily, df_5m)
            daily_results[name] = res_d
            vals = list(res_d["dow_accuracy"].values())
            daily_summary.append({
                "rule": name,
                "acc": res_d["accuracy"] or 0.0,
                "dow": res_d["dow_accuracy"],
                "min": min(vals),
                "avg": sum(vals)/len(vals),
                "n_ge_80": sum(1 for v in vals if v >= 0.8),
                "n_ge_60": sum(1 for v in vals if v >= 0.6),
                "per_class": res_d["per_class"],
            })

        print("\n=== [日次 ground truth] 全ルール 曜日別精度ランキング（最低値降順）===")
        print(f"{'rule':<27}{'acc':>6}{'min':>7}{'avg':>7}{'≥80日':>7}{'≥60日':>7}  {'月':>4}{'火':>4}{'水':>4}{'木':>4}{'金':>4}{'土':>4}{'日':>4}")
        daily_summary.sort(key=lambda x: -x["min"])
        for s in daily_summary:
            d = s["dow"]
            print(f"{s['rule']:<27}{s['acc']:>5.0%}{s['min']:>6.0%}{s['avg']:>6.0%}{s['n_ge_80']:>5}/7{s['n_ge_60']:>5}/7  "
                  f"{d['月']:>3.0%} {d['火']:>3.0%} {d['水']:>3.0%} {d['木']:>3.0%} {d['金']:>3.0%} {d['土']:>3.0%} {d['日']:>3.0%}")

        results["_daily_eval"] = daily_results

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {OUT_PATH}")


if __name__ == "__main__":
    main()
