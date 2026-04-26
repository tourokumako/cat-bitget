"""機械学習による regime 分類器（肉眼日次ラベル正本に対する学習）。

データ:
  特徴量: 5m足CSV + 日足warmup → 各日の特徴50個
  正解: data/regime_ground_truth_daily_human.csv（365日・uptrend/downtrend/range）

学習モデル:
  - RandomForest（木のアンサンブル・解釈性あり）
  - GradientBoosting（精度高い）
  - 両方学習して比較

評価:
  - 時系列分割: 学習270日（前期間）/ 検証95日（後期間）
  - クロスバリデーション（時系列対応 TimeSeriesSplit）
  - 全体正解率・per_class recall・曜日別精度・混同行列

look-ahead禁止:
  各日の特徴量は「前日確定値」のみで計算。

実行:
  .venv/bin/python scripts/ml_regime_classifier.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_5M_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2025-04-01_03-31_365d.csv"
DAILY_WARMUP_PATH = REPO_ROOT / "data" / "warmup" / "daily_warmup_BTCUSDT.csv"
GT_PATH = REPO_ROOT / "data" / "regime_ground_truth_daily_human.csv"
OUT_PATH = REPO_ROOT / "results" / "ml_regime_eval.json"
DASH_OUT_PATH = REPO_ROOT / "dashboard" / "data" / "ml_predictions.json"

LABELS = ["uptrend", "downtrend", "range"]
LABEL_TO_INT = {l: i for i, l in enumerate(LABELS)}
INT_TO_LABEL = {i: l for i, l in enumerate(LABELS)}


def _load_5m() -> pd.DataFrame:
    df = pd.read_csv(CSV_5M_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"])
    for c in ("open", "high", "low", "close", "volume"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.set_index("ts").sort_index()


def _load_daily_with_warmup(df_5m: pd.DataFrame) -> pd.DataFrame:
    daily = df_5m.resample("D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    if DAILY_WARMUP_PATH.exists():
        dw = pd.read_csv(DAILY_WARMUP_PATH)
        dw["ts"] = pd.to_datetime(dw["timestamp"])
        for c in ("open", "high", "low", "close"):
            if c in dw.columns:
                dw[c] = pd.to_numeric(dw[c], errors="coerce")
        dw = dw.set_index("ts").sort_index()
        cols = [c for c in ("open", "high", "low", "close") if c in dw.columns]
        combined = pd.concat([dw[cols], daily[cols]])
        combined = combined[~combined.index.duplicated(keep="last")].sort_index()
        return combined
    return daily


def _load_gt() -> pd.Series:
    rows = {}
    with GT_PATH.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = (r.get("date") or "").strip()
            lab = (r.get("label") or "").strip()
            if d and lab in LABELS:
                rows[d] = lab
    return pd.Series(rows)


def _safe_div(a, b):
    return a / b if b else 0.0


def _build_features(df_5m: pd.DataFrame, daily: pd.DataFrame, target_date: pd.Timestamp) -> dict | None:
    """target_date 0時時点・前日（日足）/ 前確定5m足までの情報のみで特徴を計算。"""
    import ta

    end_excl = target_date  # < end_excl
    daily_seg = daily.loc[daily.index < end_excl].copy()
    seg_5m = df_5m.loc[df_5m.index < end_excl]
    if len(daily_seg) < 30 or len(seg_5m) < 864:
        return None

    feats: dict = {}

    # ---- 日足ベース ----
    last_close = float(daily_seg["close"].iloc[-1])
    feats["close"] = last_close
    for w in (5, 10, 20, 50, 70, 200):
        ma = daily_seg["close"].rolling(w).mean().iloc[-1]
        feats[f"close_div_ma{w}"] = _safe_div(last_close, ma) - 1.0 if pd.notna(ma) else 0.0
    for w in (5, 10, 20, 50):
        ma_now = daily_seg["close"].rolling(w).mean().iloc[-1]
        ma_prev = daily_seg["close"].rolling(w).mean().iloc[-6] if len(daily_seg) >= w + 6 else np.nan
        feats[f"ma{w}_slope_pct"] = _safe_div(ma_now - ma_prev, ma_prev) if pd.notna(ma_prev) and ma_prev != 0 else 0.0
    for d in (1, 3, 5, 7, 14, 30):
        if len(daily_seg) > d:
            past = daily_seg["close"].iloc[-1 - d]
            feats[f"ret_{d}d"] = _safe_div(last_close - past, past)
        else:
            feats[f"ret_{d}d"] = 0.0

    # ADX/ATR/RSI
    adx_obj = ta.trend.ADXIndicator(daily_seg["high"], daily_seg["low"], daily_seg["close"], window=14)
    feats["adx_14"] = float(adx_obj.adx().iloc[-1]) if pd.notna(adx_obj.adx().iloc[-1]) else 0.0
    feats["di_pos"] = float(adx_obj.adx_pos().iloc[-1]) if pd.notna(adx_obj.adx_pos().iloc[-1]) else 0.0
    feats["di_neg"] = float(adx_obj.adx_neg().iloc[-1]) if pd.notna(adx_obj.adx_neg().iloc[-1]) else 0.0
    atr_obj = ta.volatility.AverageTrueRange(daily_seg["high"], daily_seg["low"], daily_seg["close"], window=14)
    feats["atr_14"] = float(atr_obj.average_true_range().iloc[-1]) if pd.notna(atr_obj.average_true_range().iloc[-1]) else 0.0
    feats["atr_pct"] = _safe_div(feats["atr_14"], last_close)
    rsi = ta.momentum.RSIIndicator(daily_seg["close"], window=14).rsi()
    feats["rsi_14"] = float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else 50.0
    rsi_7 = ta.momentum.RSIIndicator(daily_seg["close"], window=7).rsi()
    feats["rsi_7"] = float(rsi_7.iloc[-1]) if pd.notna(rsi_7.iloc[-1]) else 50.0

    # BB
    bb = ta.volatility.BollingerBands(daily_seg["close"], window=20, window_dev=2.0)
    bb_h = bb.bollinger_hband().iloc[-1]
    bb_l = bb.bollinger_lband().iloc[-1]
    bb_m = bb.bollinger_mavg().iloc[-1]
    if pd.notna(bb_h) and pd.notna(bb_l) and last_close > 0:
        feats["bb_width_pct"] = (bb_h - bb_l) / last_close * 100
        feats["bb_pos"] = _safe_div(last_close - bb_l, bb_h - bb_l)
    else:
        feats["bb_width_pct"] = 0.0
        feats["bb_pos"] = 0.5

    # 一目均衡表（日足）
    if len(daily_seg) >= 52:
        h = daily_seg["high"]
        l = daily_seg["low"]
        tenkan = (h.rolling(9).max() + l.rolling(9).min()) / 2
        kijun = (h.rolling(26).max() + l.rolling(26).min()) / 2
        span_a = ((tenkan + kijun) / 2).shift(26)
        span_b = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
        if pd.notna(span_a.iloc[-1]) and pd.notna(span_b.iloc[-1]):
            cloud_top = max(span_a.iloc[-1], span_b.iloc[-1])
            cloud_bot = min(span_a.iloc[-1], span_b.iloc[-1])
            feats["ich_close_vs_cloud"] = (last_close - (cloud_top + cloud_bot) / 2) / last_close
            feats["ich_above_cloud"] = 1.0 if last_close > cloud_top else 0.0
            feats["ich_below_cloud"] = 1.0 if last_close < cloud_bot else 0.0
            feats["ich_tenkan_kijun_diff"] = _safe_div(tenkan.iloc[-1] - kijun.iloc[-1], last_close)
        else:
            feats.update({"ich_close_vs_cloud": 0.0, "ich_above_cloud": 0.0, "ich_below_cloud": 0.0, "ich_tenkan_kijun_diff": 0.0})
    else:
        feats.update({"ich_close_vs_cloud": 0.0, "ich_above_cloud": 0.0, "ich_below_cloud": 0.0, "ich_tenkan_kijun_diff": 0.0})

    # MACD（日足）
    macd_obj = ta.trend.MACD(daily_seg["close"], window_slow=26, window_fast=12, window_sign=9)
    macd = macd_obj.macd().iloc[-1]
    macd_sig = macd_obj.macd_signal().iloc[-1]
    macd_diff = macd_obj.macd_diff().iloc[-1]
    feats["macd"] = float(macd) if pd.notna(macd) else 0.0
    feats["macd_signal"] = float(macd_sig) if pd.notna(macd_sig) else 0.0
    feats["macd_diff"] = float(macd_diff) if pd.notna(macd_diff) else 0.0
    feats["macd_above_signal"] = 1.0 if pd.notna(macd) and pd.notna(macd_sig) and macd > macd_sig else 0.0

    # 高値安値更新
    high_5d = daily_seg["high"].iloc[-5:].max() if len(daily_seg) >= 5 else last_close
    low_5d = daily_seg["low"].iloc[-5:].min() if len(daily_seg) >= 5 else last_close
    high_20d = daily_seg["high"].iloc[-20:].max() if len(daily_seg) >= 20 else last_close
    low_20d = daily_seg["low"].iloc[-20:].min() if len(daily_seg) >= 20 else last_close
    feats["pos_in_5d_range"] = _safe_div(last_close - low_5d, high_5d - low_5d)
    feats["pos_in_20d_range"] = _safe_div(last_close - low_20d, high_20d - low_20d)

    # ---- 4h足ベース ----
    h4 = seg_5m.resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    if len(h4) >= 50:
        h4_close = h4["close"].iloc[-1]
        for w in (10, 20, 50):
            ma = h4["close"].rolling(w).mean().iloc[-1]
            feats[f"h4_close_div_ma{w}"] = _safe_div(h4_close, ma) - 1.0 if pd.notna(ma) else 0.0
        for d in (6, 12, 24):
            if len(h4) > d:
                past = h4["close"].iloc[-1 - d]
                feats[f"h4_ret_{d * 4}h"] = _safe_div(h4_close - past, past)
            else:
                feats[f"h4_ret_{d * 4}h"] = 0.0
    else:
        for w in (10, 20, 50):
            feats[f"h4_close_div_ma{w}"] = 0.0
        for d in (6, 12, 24):
            feats[f"h4_ret_{d * 4}h"] = 0.0

    # ---- 1h足ベース ----
    h1 = seg_5m.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    if len(h1) >= 168:
        h1_close = h1["close"].iloc[-1]
        for w in (24, 72, 168):
            ma = h1["close"].rolling(w).mean().iloc[-1]
            feats[f"h1_close_div_ma{w}"] = _safe_div(h1_close, ma) - 1.0 if pd.notna(ma) else 0.0
    else:
        for w in (24, 72, 168):
            feats[f"h1_close_div_ma{w}"] = 0.0

    # ---- 5m足ベース：ボラ・出来高・波形 ----
    seg_24h = seg_5m.iloc[-288:]
    seg_72h = seg_5m.iloc[-864:]
    closes_24h = seg_24h["close"].values
    feats["range_24h_pct"] = _safe_div(seg_24h["high"].max() - seg_24h["low"].min(), closes_24h[-1]) if closes_24h[-1] > 0 else 0.0
    if "volume" in seg_5m.columns:
        v24 = seg_24h["volume"].sum()
        v72 = seg_72h["volume"].sum()
        v168 = seg_5m.iloc[-2016:]["volume"].sum() if len(seg_5m) >= 2016 else v24 * 7
        feats["vol_24h"] = float(v24)
        feats["vol_24h_div_72h_avg"] = _safe_div(v24, v72 / 3) - 1.0 if v72 > 0 else 0.0
        feats["vol_24h_div_168h_avg"] = _safe_div(v24, v168 / 7) - 1.0 if v168 > 0 else 0.0
        # up/down volume ratio (24h)
        seg_24h_dir = (seg_24h["close"] > seg_24h["open"]).astype(int)
        up_vol = (seg_24h["volume"] * seg_24h_dir).sum()
        feats["up_vol_ratio_24h"] = _safe_div(up_vol, v24) if v24 > 0 else 0.5
    else:
        feats["vol_24h"] = 0.0
        feats["vol_24h_div_72h_avg"] = 0.0
        feats["vol_24h_div_168h_avg"] = 0.0
        feats["up_vol_ratio_24h"] = 0.5

    # 5m足の波形：直近24hで2h窓ごとの方向（12窓）
    bars_per_2h = 24
    dir_2h = []
    for i in range(12):
        sub = seg_24h.iloc[i * bars_per_2h:(i + 1) * bars_per_2h]
        if len(sub) >= 2:
            if sub["close"].iloc[-1] > sub["close"].iloc[0]:
                dir_2h.append(1)
            elif sub["close"].iloc[-1] < sub["close"].iloc[0]:
                dir_2h.append(-1)
            else:
                dir_2h.append(0)
    if dir_2h:
        feats["dir_2h_up_ratio"] = sum(1 for x in dir_2h if x == 1) / len(dir_2h)
        feats["dir_2h_dn_ratio"] = sum(1 for x in dir_2h if x == -1) / len(dir_2h)
        # 連続性: 同方向連続最大
        max_run = 1
        cur_run = 1
        for i in range(1, len(dir_2h)):
            if dir_2h[i] == dir_2h[i - 1] and dir_2h[i] != 0:
                cur_run += 1
                max_run = max(max_run, cur_run)
            else:
                cur_run = 1
        feats["dir_2h_max_run"] = max_run
    else:
        feats["dir_2h_up_ratio"] = 0.5
        feats["dir_2h_dn_ratio"] = 0.5
        feats["dir_2h_max_run"] = 0

    # 直近24h spike: |1h return| > 1% の数
    h1_24 = h1.iloc[-24:] if len(h1) >= 24 else h1
    if len(h1_24) >= 2:
        h1_returns = h1_24["close"].pct_change().fillna(0)
        feats["spike_up_1h_count_24h"] = int((h1_returns > 0.01).sum())
        feats["spike_dn_1h_count_24h"] = int((h1_returns < -0.01).sum())
    else:
        feats["spike_up_1h_count_24h"] = 0
        feats["spike_dn_1h_count_24h"] = 0

    # 曜日 (one-hot不要・整数で)
    feats["dow"] = target_date.weekday()

    return feats


def build_dataset() -> tuple[pd.DataFrame, pd.Series, list]:
    """X: 特徴量DataFrame / y: ラベル / dates: 日付list"""
    df_5m = _load_5m()
    daily = _load_daily_with_warmup(df_5m)
    gt = _load_gt()

    X_list = []
    y_list = []
    dates = []
    for date_str, label in sorted(gt.items()):
        d = pd.Timestamp(date_str)
        feats = _build_features(df_5m, daily, d)
        if feats is None:
            continue
        X_list.append(feats)
        y_list.append(LABEL_TO_INT[label])
        dates.append(date_str)

    X = pd.DataFrame(X_list)
    y = pd.Series(y_list)
    return X, y, dates


def evaluate_predictions(y_true, y_pred, dates) -> dict:
    """正解率・per_class recall・曜日別精度・混同行列。"""
    n = len(y_true)
    correct = int(sum(np.array(y_true) == np.array(y_pred)))
    accuracy = correct / n if n else 0.0

    per_class = {}
    for lab_i, lab in enumerate(LABELS):
        true_idx = [i for i in range(n) if y_true[i] == lab_i]
        recall = sum(1 for i in true_idx if y_pred[i] == lab_i) / len(true_idx) if true_idx else None
        per_class[lab] = {"recall": round(recall, 3) if recall is not None else None, "n": len(true_idx)}

    confusion = [[0] * 3 for _ in range(3)]
    for t, p in zip(y_true, y_pred):
        confusion[int(t)][int(p)] += 1

    dow_buckets = {i: {"hit": 0, "n": 0} for i in range(7)}
    for i, date_str in enumerate(dates):
        dow = pd.Timestamp(date_str).weekday()
        dow_buckets[dow]["n"] += 1
        if y_true[i] == y_pred[i]:
            dow_buckets[dow]["hit"] += 1
    dow_names = ["月", "火", "水", "木", "金", "土", "日"]
    dow_acc = {dow_names[i]: (dow_buckets[i]["hit"] / dow_buckets[i]["n"]) if dow_buckets[i]["n"] else 0.0
               for i in range(7)}

    return {
        "n": n,
        "accuracy": round(accuracy, 3),
        "per_class": per_class,
        "confusion": confusion,
        "dow_accuracy": dow_acc,
        "dow_min": min(dow_acc.values()),
        "dow_avg": sum(dow_acc.values()) / 7,
    }


def _print_eval(label: str, res: dict) -> None:
    print(f"\n=== {label} ===")
    print(f"  正解率: {res['accuracy']:.1%} ({res['n']}日)")
    print(f"  per_class:")
    for lab in LABELS:
        pc = res["per_class"][lab]
        if pc["recall"] is not None:
            print(f"    {lab:<10}: {pc['recall']:.1%} (n={pc['n']})")
    print(f"  曜日別: " + " / ".join(f"{k}={v:.0%}" for k, v in res["dow_accuracy"].items()))
    print(f"  最低曜日: {res['dow_min']:.1%} / 平均: {res['dow_avg']:.1%}")
    print(f"  混同行列 (行=true / 列=pred):")
    print(f"    {'':>11}{'up':>6}{'dn':>6}{'rg':>6}")
    for i, lab in enumerate(LABELS):
        row = res["confusion"][i]
        print(f"    {lab:>11}{row[0]:>6}{row[1]:>6}{row[2]:>6}")


def main() -> None:
    print("[1/4] データ構築...")
    X, y, dates = build_dataset()
    print(f"  サンプル数: {len(X)}, 特徴量: {X.shape[1]}")
    print(f"  ラベル分布: {Counter([INT_TO_LABEL[v] for v in y])}")

    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import TimeSeriesSplit

    # ====== 時系列分割: 前270日 学習 / 後95日 検証 ======
    print("\n[2/4] 時系列holdout評価（前期間で学習・後期間で検証）...")
    n_train = int(len(X) * 0.74)
    X_train, X_test = X.iloc[:n_train], X.iloc[n_train:]
    y_train, y_test = y.iloc[:n_train], y.iloc[n_train:]
    dates_test = dates[n_train:]
    print(f"  学習: {len(X_train)}日 ({dates[0]} 〜 {dates[n_train - 1]})")
    print(f"  検証: {len(X_test)}日 ({dates[n_train]} 〜 {dates[-1]})")

    results = {}
    for model_name, model in [
        ("RandomForest", RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_leaf=3, random_state=42, n_jobs=-1)),
        ("GradientBoosting", GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)),
    ]:
        model.fit(X_train, y_train)
        # train precision (overfit indicator)
        y_train_pred = model.predict(X_train)
        train_acc = float(np.mean(y_train.values == y_train_pred))
        # holdout
        y_pred = model.predict(X_test)
        res = evaluate_predictions(y_test.values.tolist(), y_pred.tolist(), dates_test)
        res["train_accuracy"] = round(train_acc, 3)
        _print_eval(f"{model_name} [holdout 後{len(X_test)}日]", res)
        print(f"  学習正解率: {train_acc:.1%} （holdoutとの差 = 過学習度）")
        results[f"{model_name}_holdout"] = res

    # ====== Walk-forward (expanding window) で全日の OOF予測 ======
    # 最初の N0 日を初期学習 → N0+1 日目以降は1日ずつ rolling forecast
    # 各日: その日までの全データ（その日含まず）で学習 → その日を予測
    print("\n[3/4] Walk-forward（expanding window・最初60日学習・以降日次予測）...")
    INIT_TRAIN_DAYS = 30
    REFIT_INTERVAL = 5  # 5日ごとに再学習（毎日fitすると遅い）
    oof_predictions: dict = {}
    for model_name, get_model in [
        ("RandomForest", lambda: RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_leaf=3, random_state=42, n_jobs=-1)),
        ("GradientBoosting", lambda: GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)),
    ]:
        oof_predictions[model_name] = {}
        all_y_true = []
        all_y_pred = []
        all_dates = []
        model = None
        for i in range(INIT_TRAIN_DAYS, len(X)):
            if model is None or (i - INIT_TRAIN_DAYS) % REFIT_INTERVAL == 0:
                model = get_model()
                model.fit(X.iloc[:i], y.iloc[:i])
            pred = int(model.predict(X.iloc[i:i + 1])[0])
            oof_predictions[model_name][dates[i]] = INT_TO_LABEL[pred]
            all_y_true.append(int(y.iloc[i]))
            all_y_pred.append(pred)
            all_dates.append(dates[i])
        cv_res = evaluate_predictions(all_y_true, all_y_pred, all_dates)
        _print_eval(f"{model_name} [Walk-forward 全{len(all_y_true)}日]", cv_res)
        results[f"{model_name}_walkforward"] = cv_res

    # ====== 特徴量重要度 ======
    print("\n[4/4] 特徴量重要度（RandomForest 全データ学習）...")
    rf_full = RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_leaf=3, random_state=42, n_jobs=-1)
    rf_full.fit(X, y)
    importances = sorted(zip(X.columns, rf_full.feature_importances_), key=lambda x: -x[1])
    print(f"  上位15特徴:")
    for name, imp in importances[:15]:
        print(f"    {name:<30}: {imp:.4f}")
    results["feature_importances"] = [{"feature": n, "importance": float(i)} for n, i in importances]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    print(f"\n→ {OUT_PATH}")

    # ====== ダッシュボード用 JSON 出力 ======
    df_5m = _load_5m()
    daily = df_5m.resample("D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    gt = _load_gt()

    # 365日分の price + true label + ML predictions
    days_data = []
    all_dates = sorted(set(list(gt.index) + [d.strftime("%Y-%m-%d") for d in daily.index]))
    for d_str in all_dates:
        d = pd.Timestamp(d_str)
        if d not in daily.index:
            continue
        true_label = gt.get(d_str, "")
        rf_pred = oof_predictions.get("RandomForest", {}).get(d_str, "")
        gb_pred = oof_predictions.get("GradientBoosting", {}).get(d_str, "")
        days_data.append({
            "date": d_str,
            "close": float(daily.loc[d, "close"]),
            "true": true_label,
            "rf_pred": rf_pred,
            "gb_pred": gb_pred,
            "rf_match": rf_pred == true_label if rf_pred and true_label else None,
            "gb_match": gb_pred == true_label if gb_pred and true_label else None,
        })

    # サマリ
    rf_n = sum(1 for d in days_data if d["rf_pred"] and d["true"])
    rf_hit = sum(1 for d in days_data if d["rf_match"])
    gb_n = sum(1 for d in days_data if d["gb_pred"] and d["true"])
    gb_hit = sum(1 for d in days_data if d["gb_match"])

    importances = sorted(zip(X.columns, rf_full.feature_importances_), key=lambda x: -x[1])
    dash_out = {
        "n_days": len(days_data),
        "rf_summary": {"n": rf_n, "hit": rf_hit, "accuracy": round(rf_hit / rf_n, 3) if rf_n else None},
        "gb_summary": {"n": gb_n, "hit": gb_hit, "accuracy": round(gb_hit / gb_n, 3) if gb_n else None},
        "feature_importances": [{"feature": n, "importance": float(i)} for n, i in importances[:20]],
        "days": days_data,
    }
    DASH_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DASH_OUT_PATH.write_text(json.dumps(dash_out, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    print(f"→ {DASH_OUT_PATH}")


if __name__ == "__main__":
    main()
