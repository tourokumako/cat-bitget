"""
regime_inverter.py — 判定器逆算スクリプト

731バーの人間サンプルを直接教師データとして、backward-looking 指標の
最適な組み合わせを決定木で逆算する。

結果はダッシュボード タブ⑪ に v5 として登録される。

実行:
    python3 scripts/regime_inverter.py
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import timezone

BASE = Path(__file__).parent.parent
DASH_DIR = BASE / "dashboard/regime_prototype"
VERSION = "v10"

# ── データ読み込み ───────────────────────────────────────────

def load_ohlcv(freq="4h"):
    df = pd.read_csv(BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv",
                     parse_dates=["timestamp"])
    df = df.set_index("timestamp").sort_index()
    return df.resample(freq).agg(
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last"),
        volume=("volume", "sum"),
    ).dropna()

# ── 指標計算（look-ahead なし） ──────────────────────────────

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)

def compute_adx_di(high, low, close, period=14):
    tr = pd.concat([high - low,
                    (high - close.shift()).abs(),
                    (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    up = high.diff(); dn = -low.diff()
    dmp = up.where((up > dn) & (up > 0), 0.0)
    dmm = dn.where((dn > up) & (dn > 0), 0.0)
    dip = 100 * dmp.ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan)
    dim = 100 * dmm.ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan)
    dx = 100 * (dip - dim).abs() / (dip + dim).replace(0, np.nan)
    return dx.ewm(alpha=1/period, adjust=False).mean(), dip - dim

def slope_pct(series, lookback):
    """過去 lookback バーの線形回帰傾き（%/bar）"""
    slopes = np.full(len(series), np.nan)
    vals = series.values
    for i in range(lookback, len(vals)):
        y = vals[i-lookback:i]
        if np.any(np.isnan(y)):
            continue
        b = np.polyfit(np.arange(lookback), y, 1)[0]
        slopes[i] = b / vals[i-1] * 100 if vals[i-1] != 0 else np.nan
    return pd.Series(slopes, index=series.index)

def build_features(df):
    c, h, l = df["close"], df["high"], df["low"]
    f = pd.DataFrame(index=df.index)
    # MA 乖離率
    f["close_vs_ma20"] = (c / c.rolling(20).mean() - 1) * 100
    f["close_vs_ma50"] = (c / c.rolling(50).mean() - 1) * 100
    # MA 乖離率の変化（位置の上昇 / 下降を捕捉）
    f["delta_close_vs_ma20_3b"] = f["close_vs_ma20"] - f["close_vs_ma20"].shift(3)
    f["delta_close_vs_ma50_5b"] = f["close_vs_ma50"] - f["close_vs_ma50"].shift(5)
    # 傾き（複数 lookback）
    f["slope_2b"]  = slope_pct(c, 2)
    f["slope_3b"]  = slope_pct(c, 3)
    f["slope_4b"]  = slope_pct(c, 4)
    f["slope_8b"]  = slope_pct(c, 8)
    f["slope_12b"] = slope_pct(c, 12)
    f["slope_ma20_5b"] = slope_pct(c.rolling(20).mean(), 5)
    f["slope_ma50_5b"] = slope_pct(c.rolling(50).mean(), 5)
    # ADX / DI差
    f["adx14"], f["di_diff"] = compute_adx_di(h, l, c, 14)
    # RSI
    f["rsi14"] = compute_rsi(c, 14)
    # 直近 10 バー（40h）の極値からの反発率（強反発の初動を捕捉）
    low_10 = l.rolling(10).min()
    high_10 = h.rolling(10).max()
    f["reversal_from_low_10b"] = (c - low_10) / low_10 * 100
    f["reversal_from_high_10b"] = (high_10 - c) / high_10 * 100
    # 直近高安レンジ内での位置（半値戻し / もみ合い圏を捕捉・0〜100%）
    low_20 = l.rolling(20).min()
    high_20 = h.rolling(20).max()
    f["retrace_ratio_20b"] = (c - low_20) / (high_20 - low_20).replace(0, np.nan) * 100
    low_30 = l.rolling(30).min()
    high_30 = h.rolling(30).max()
    f["retrace_ratio_30b"] = (c - low_30) / (high_30 - low_30).replace(0, np.nan) * 100
    return f

# ── ヒステリシス適用 ──────────────────────────────────────────

def apply_hysteresis(series, hys_bars):
    """hys_bars 連続で同じ判定が出たら採用（切替抑制）"""
    result, current, candidate, cand_count = [], None, None, 0
    for v in series:
        if pd.isna(v) or v is None:
            result.append(current)
            continue
        if v == candidate:
            cand_count += 1
        else:
            candidate, cand_count = v, 1
        if cand_count >= hys_bars:
            current = candidate
        result.append(current)
    return pd.Series(result, index=series.index)

# ── ダッシュボード出力 ────────────────────────────────────────

def load_daily_human_labels():
    path = BASE / "data/regime_ground_truth_daily_human.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.set_index("date")
    return df["regime"] if "regime" in df.columns else df.iloc[:, 0]

def load_sample_4h_labels():
    """4h サンプルラベルを {timestamp: label} dict で返す（2025年・731バーのみ）"""
    smp = pd.read_csv(BASE / "data/regime_samples_4h.csv", parse_dates=["timestamp_utc"])
    smp = smp.rename(columns={"timestamp_utc": "timestamp", "label": "human"})
    smp["timestamp"] = smp["timestamp"].dt.tz_localize(None)
    smp = smp[smp["human"].notna()]
    return dict(zip(smp["timestamp"], smp["human"]))

def generate_auto_labels(df4h, years=(2022, 2023, 2024), lookback=6, threshold=0.12):
    """② スロープ法で指定年の 4h バーにラベルを自動生成する。
    slope_pct(close, lookback) >  threshold → uptrend
    slope_pct(close, lookback) < -threshold → downtrend
    otherwise                               → range
    """
    slopes = slope_pct(df4h["close"], lookback)
    labels = pd.Series("range", index=df4h.index)
    labels[slopes >  threshold] = "uptrend"
    labels[slopes < -threshold] = "downtrend"

    results = []
    for year in years:
        mask = (df4h.index.year == year) & slopes.notna()
        sub = pd.DataFrame({
            "timestamp": df4h.index[mask],
            "human": labels[mask].values,
            "source": f"auto_{year}",
        })
        results.append(sub)
        dist = sub["human"].value_counts().to_dict()
        print(f"  {year} 自動ラベル: {len(sub)}バー  {dist}")
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()


def write_dashboard_json(pred_1h, stats, feature_cols):
    """タブ⑪ 互換の JSON を生成して index.json を更新する"""
    DASH_DIR.mkdir(parents=True, exist_ok=True)

    # 4h サンプルラベル（上段表示用）
    sample_labels_4h = load_sample_4h_labels()

    # ── 1h JSON ──
    # row 形式: [ts_ms, close, pred_label, human_label]  ← r[2]=pred / r[3]=human
    rows_1h = []
    for ts, row in pred_1h.iterrows():
        ts_ms = int(ts.timestamp() * 1000)
        close_val = int(row["close"])
        pred_label = str(row["pred"]) if pd.notna(row["pred"]) else "range"
        # 1h バーが属する 4h バーの開始時刻（切り捨て）でサンプルを引く
        ts_4h_floor = ts.floor("4h")
        human_label = sample_labels_4h.get(ts_4h_floor, "")
        rows_1h.append([ts_ms, close_val, pred_label, human_label])

    out_1h = {"version": VERSION, "granularity": "1h", "rows": rows_1h}
    with open(DASH_DIR / f"predictions_{VERSION}_1h.json", "w") as f:
        json.dump(out_1h, f, separators=(",", ":"))
    print(f"  → predictions_{VERSION}_1h.json ({len(rows_1h)} 行)")

    # ── 1d JSON（1h を日次集約）──
    pred_1h_copy = pred_1h.copy()
    pred_1h_copy["date"] = pred_1h_copy.index.date
    daily = pred_1h_copy.groupby("date").agg(
        close=("close", "last"),
        pred=("pred", lambda x: x.mode().iloc[0] if len(x) > 0 else "range"),
    )
    # 1d の human ラベル: 4h サンプルの多数決（その日にラベル付き4hバーがあれば）
    rows_1d = []
    for date, row in daily.iterrows():
        ts_ms = int(pd.Timestamp(date).timestamp() * 1000)
        close_val = int(row["close"])
        # その日の 4h サンプルラベルを収集
        day_start = pd.Timestamp(date)
        day_labels = [v for k, v in sample_labels_4h.items()
                      if day_start <= k < day_start + pd.Timedelta(days=1)]
        human_label = pd.Series(day_labels).mode().iloc[0] if day_labels else ""
        pred_label = str(row["pred"])
        rows_1d.append([ts_ms, close_val, pred_label, human_label])

    out_1d = {"version": VERSION, "granularity": "1d", "rows": rows_1d}
    with open(DASH_DIR / f"predictions_{VERSION}_1d.json", "w") as f:
        json.dump(out_1d, f, separators=(",", ":"))
    print(f"  → predictions_{VERSION}_1d.json ({len(rows_1d)} 行)")

    # ── index.json 更新 ──
    idx_path = DASH_DIR / "index.json"
    with open(idx_path) as f:
        idx = json.load(f)

    dist = pred_1h["pred"].value_counts()
    total = len(pred_1h)

    entry = {
        "version": VERSION,
        "generated_utc": pd.Timestamp.now(tz=timezone.utc).isoformat(),
        "spec": {
            "method": "decision_tree_direct",
            "train_samples": stats["n_train"],
            "max_depth": stats["max_depth"],
            "features": feature_cols,
            "hysteresis_bars": stats["hys_bars"],
            "output_granularity": "1h",
        },
        "distribution": {
            r: {"count": int(dist.get(r, 0)), "pct": round(dist.get(r, 0)/total*100, 2)}
            for r in ["range", "uptrend", "downtrend"]
        },
        "accuracy": {
            "sample_731": {
                "n": stats["n_sample"],
                "hit": stats["sample_hit"],
                "pct": round(stats["sample_hit"] / stats["n_sample"] * 100, 2),
            }
        },
    }

    # 同バージョンがあれば置換
    idx["prototypes"] = [p for p in idx["prototypes"] if p["version"] != VERSION]
    idx["prototypes"].append(entry)
    with open(idx_path, "w") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)
    print(f"  → index.json 更新（{VERSION} 追加）")

# ── メイン ──────────────────────────────────────────────────

def main():
    print("データ読み込み中...")
    df4h = load_ohlcv("4h")
    df1h = load_ohlcv("1h")
    print(f"  4h: {len(df4h)} バー  1h: {len(df1h)} バー")

    print("人間サンプル読み込み（全年）...")
    csv_files = {
        2025: BASE / "data/regime_samples_4h.csv",
        2024: BASE / "data/regime_samples_4h_2024.csv",
        2023: BASE / "data/regime_samples_4h_2023.csv",
        2022: BASE / "data/regime_samples_4h_2022.csv",
    }
    smp_parts = []
    for year, path in csv_files.items():
        if not path.exists():
            continue
        tmp = pd.read_csv(path, parse_dates=["timestamp_utc"])
        tmp = tmp.rename(columns={"timestamp_utc": "timestamp", "label": "human"})
        tmp["timestamp"] = tmp["timestamp"].dt.tz_localize(None)
        tmp = tmp[tmp["human"].notna() & (tmp["human"] != "")].copy()
        if len(tmp) > 0:
            print(f"  {year}: {len(tmp)}バー  {dict(tmp['human'].value_counts())}")
            smp_parts.append(tmp)
    smp = pd.concat(smp_parts, ignore_index=True) if smp_parts else pd.DataFrame()
    print(f"  合計: {len(smp)}バー")
    # 2025年サンプルは一致率評価にも使う
    smp_2025 = smp[smp["timestamp"].dt.year == 2025].copy()

    print("特徴量計算中（4h）...")
    feats4h = build_features(df4h)
    feats4h["close"] = df4h["close"]

    # 学習データ: 731 サンプルと 4h 特徴量を結合
    train_df = smp.merge(feats4h.reset_index(), on="timestamp", how="inner").dropna()
    print(f"  学習データ: {len(train_df)} 件（731 サンプルのうち特徴量が揃うもの）")

    feature_cols = [c for c in feats4h.columns if c != "close"]
    X = train_df[feature_cols].values
    y = train_df["human"].values

    # 区間単位の交差検証（同区間バーが train/test に混入しないよう interval_id で分割）
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score

    # 区間 ID 付与（同じ regime の連続区間）
    train_df = train_df.copy()
    train_df["interval_id"] = (train_df["human"] != train_df["human"].shift()).cumsum()

    # 区間単位の CV: 各 fold で interval_id をまるごと train or test に割り当て
    interval_ids = train_df["interval_id"].unique()
    np.random.seed(42)
    np.random.shuffle(interval_ids)
    n_folds = 5
    fold_assignments = {iid: i % n_folds for i, iid in enumerate(interval_ids)}
    train_df["fold"] = train_df["interval_id"].map(fold_assignments)

    cv_accs = []
    for fold in range(n_folds):
        tr = train_df[train_df["fold"] != fold]
        te = train_df[train_df["fold"] == fold]
        clf_tmp = RandomForestClassifier(n_estimators=300, max_depth=4,
                                          random_state=42, class_weight="balanced", n_jobs=-1)
        clf_tmp.fit(tr[feature_cols].values, tr["human"].values)
        pred = clf_tmp.predict(te[feature_cols].values)
        cv_accs.append(accuracy_score(te["human"].values, pred))

    cv_mean = np.mean(cv_accs) * 100
    print(f"\n  CV 精度（5-fold 区間分割）: {cv_mean:.1f}%  各 fold: {[f'{a*100:.1f}%' for a in cv_accs]}")

    # 全データで最終モデル学習
    MAX_DEPTH = 4
    from sklearn.ensemble import RandomForestClassifier
    clf = RandomForestClassifier(n_estimators=300, max_depth=MAX_DEPTH,
                                  random_state=42, class_weight="balanced", n_jobs=-1)
    clf.fit(X, y)

    # 学習データへの適合確認
    y_pred_train = clf.predict(X)
    acc_train = accuracy_score(y, y_pred_train) * 100
    print(f"  学習データ精度: {acc_train:.1f}%  （CV: {cv_mean:.1f}%）")

    # ── 全期間（4h）に適用 → 1h に展開 ──
    print("\n全期間（4h）に適用 → 1h 展開中...")
    feats4h_all = build_features(df4h)
    feats4h_all["close"] = df4h["close"]

    feats4h_clean = feats4h_all.dropna(subset=feature_cols)
    X_all = feats4h_clean[feature_cols].values
    preds_all = clf.predict(X_all)
    pred_series = pd.Series(preds_all, index=feats4h_clean.index, name="pred")

    # ヒステリシス（4hバー単位・2バー=8h）
    HYS_BARS = 2
    pred_hys = apply_hysteresis(pred_series, HYS_BARS)
    pred_hys = pred_hys.fillna("range")

    pred_4h = feats4h_all[["close"]].copy()
    pred_4h["pred"] = pred_hys

    # 4h → 1h に前向き補完（各 4h バーの判定を次の 4h まで維持）
    df1h_close = load_ohlcv("1h")[["close"]]
    pred_1h = df1h_close.copy()
    pred_1h["pred"] = pred_4h["pred"].reindex(pred_1h.index, method="ffill").fillna("range")

    dist = pred_1h["pred"].value_counts()
    total = len(pred_1h)
    print(f"  全期間分布: dt{dist.get('downtrend',0)/total*100:.1f}% "
          f"rg{dist.get('range',0)/total*100:.1f}% "
          f"up{dist.get('uptrend',0)/total*100:.1f}%")

    # 2025年人間サンプルとの一致率
    smp_check = smp_2025.copy()
    smp_check = smp_check.merge(
        pred_1h[["pred"]].reset_index().rename(columns={"timestamp": "timestamp"}),
        on="timestamp", how="left"
    )
    smp_check = smp_check[smp_check["pred"].notna()]
    sample_hit = (smp_check["human"] == smp_check["pred"]).sum()
    sample_acc = sample_hit / len(smp_check) * 100 if len(smp_check) > 0 else 0
    print(f"  2025年サンプル一致率: {sample_acc:.1f}%  ({sample_hit}/{len(smp_check)}件)")

    # 特徴量重要度
    print(f"\n── 特徴量重要度（上位8）──")
    importances = pd.Series(clf.feature_importances_, index=feature_cols)
    for name, val in importances.sort_values(ascending=False).head(8).items():
        print(f"  {name:<25} {val:.3f}")

    # ダッシュボード出力
    print("ダッシュボード JSON 生成中...")
    stats = {
        "n_train": len(train_df),
        "max_depth": MAX_DEPTH,
        "hys_bars": HYS_BARS,
        "n_sample": len(smp_check),
        "sample_hit": int(sample_hit),
        "cv_acc": cv_mean,
    }
    write_dashboard_json(pred_1h, stats, feature_cols)

    print(f"\n完了。ダッシュボードをリロードしてタブ⑪ → {VERSION} を選択してください。")
    print(f"731 サンプル一致率: {sample_acc:.1f}%  CV 精度: {cv_mean:.1f}%")


if __name__ == "__main__":
    main()
