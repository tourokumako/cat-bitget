"""build_labels_pct.py — Phase 0: 5m bar × 1,432 指標 × 28 MFE/MAE (pct) ラベル を生成

目的: Phase 1 LightGBM 学習用 parquet を pct 化 + 28 ラベル + メンテ除外フラグで生成する。

旧 build_labels.py との差分:
  1. K_BARS: [12, 24, 48, 96] → [6, 12, 24, 48, 96, 144, 288] (4 → 7 K = 16 → 28 ラベル)
  2. ラベル定義: USD 絶対値 → pct ベース ((MFE / close) × 100)
     学習期間 BTC 価格 ($30k〜$100k) と本番価格 ($100k〜$150k) の乖離による分布シフトを排除。
     正本ルール: web_claude_self_check.md §価格非依存性 #1。
  3. メンテ時間帯フラグ列追加: 火/水/木 05-08 UTC (exchange_spec.md 定期メンテ)
     学習時に df[~df.is_maintenance] でフィルタ可能。
  4. 出力ファイル名: labels_mfe_mae_pct_*.parquet (旧版と共存)

実行モード:
  --dry-run         : 構造 + import + 期待集合 1,432 確認のみ (指標計算スキップ・数秒)
  --sample-days N   : 先頭 N 日のみで全処理 (sample.parquet 出力・数分)
  --test-2026q1     : 2026 Q1 のみ生成
  (引数なし)         : フル 5y 処理 + train/test 2 parquet 出力 (8〜12 時間想定)

入力:
  - data/BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv (525,887 データ行)
  - results/regime_label_analysis/pruned_column_list.json (1,432 列定義)

出力:
  - results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet
  - results/priority_rebuild/labels_mfe_mae_pct_test_2025.parquet
  - results/priority_rebuild/labels_mfe_mae_pct_test_2026_q1.parquet
  - results/priority_rebuild/labels_mfe_mae_pct_sample.parquet  (--sample-days)
  列構成: timestamp(index) + close + 1,432 指標 + 28 ラベル + is_maintenance = 1,462 列

ラベル定義 (K=6/12/24/48/96/144/288 bar = 30min/1h/2h/4h/8h/12h/24h):
  - LONG_MFE_pct_K{K}  = (max(high[t+1..t+K]) - close[t]) / close[t] × 100
  - LONG_MAE_pct_K{K}  = (close[t] - min(low[t+1..t+K]))  / close[t] × 100
  - SHORT_MFE_pct_K{K} = (close[t] - min(low[t+1..t+K]))  / close[t] × 100
  - SHORT_MAE_pct_K{K} = (max(high[t+1..t+K]) - close[t]) / close[t] × 100

look-ahead 防止:
  - 5m bar t (close 時刻 = t + 5min) で観測可能な上位 TF bar は T_upper + freq <= t + 5min
  - merge_asof(direction="backward") を 5m close 時刻 vs 上位 TF close 時刻 で適用
  - MFE/MAE ラベルは正解側のため Phase 1 学習で X に含めない (L-154 / L-179)

メンテ時間帯フラグ:
  - is_maintenance = True: 火/水/木 (weekday=1/2/3) の hour ∈ {5, 6, 7} (= 05:00-07:59 UTC)
  - 出典: exchange_spec.md `定期メンテナンス 火/水/木 05:00-08:00 UTC`
  - 行は drop せず・後段 (Phase 1 学習スクリプト) で df[~df.is_maintenance] フィルタ

検証:
  - assert: 実 parquet の指標列集合 == pruned_column_list.json の (cat, tf, base) 展開集合
  - 1 列でも不一致なら RuntimeError + 差分の先頭 10 件を提示
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.regime.analyze_regime_label_features import build_indicators_extended
from scripts.regime.shape_features import compute_all_features as compute_1b_for_W
from scripts.regime.structure_features import compute_features_for_N, compute_c2_only

INPUT_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv"
assert "bitget" in str(INPUT_CSV), \
    f"ML pipeline must use Bitget CSV, got: {INPUT_CSV}"
PRUNED_JSON = REPO_ROOT / "results" / "regime_label_analysis" / "pruned_column_list.json"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild"
OUT_TRAIN = OUT_DIR / "labels_mfe_mae_pct_train_2021_2024.parquet"
OUT_TEST = OUT_DIR / "labels_mfe_mae_pct_test_2025.parquet"
OUT_TEST_2026Q1 = OUT_DIR / "labels_mfe_mae_pct_test_2026_q1.parquet"
OUT_SAMPLE = OUT_DIR / "labels_mfe_mae_pct_sample.parquet"

TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]
RESAMPLE_RULE = {"5m": "5min", "15m": "15min", "30m": "30min", "1h": "1h", "4h": "4h", "1d": "1D"}
FREQ_TD = {
    "5m": pd.Timedelta(minutes=5),
    "15m": pd.Timedelta(minutes=15),
    "30m": pd.Timedelta(minutes=30),
    "1h": pd.Timedelta(hours=1),
    "4h": pd.Timedelta(hours=4),
    "1d": pd.Timedelta(days=1),
}

W_CANDIDATES = [10, 20, 50]
N_CANDIDATES = [50, 100, 200]
K_BARS = [6, 12, 24, 48, 96, 144, 288]

TRAIN_START = pd.Timestamp("2021-04-01")
TRAIN_END = pd.Timestamp("2024-12-31 23:59:59")
TEST_START = pd.Timestamp("2025-01-01")
TEST_END = pd.Timestamp("2025-12-31 23:59:59")
TEST_2026Q1_START = pd.Timestamp("2026-01-01")
TEST_2026Q1_END = pd.Timestamp("2026-03-31 23:59:59")

MAINTENANCE_WEEKDAYS = [1, 2, 3]
MAINTENANCE_HOURS = [5, 6, 7]


def load_5m_bars(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()
    return df[["open", "high", "low", "close", "volume"]]


def resample_ohlcv(df5m: pd.DataFrame, rule: str) -> pd.DataFrame:
    return df5m.resample(rule).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    ).dropna()


def compute_features_for_tf(df_tf: pd.DataFrame) -> pd.DataFrame:
    """1 TF 分の指標を全カテゴリ計算し、pruned ベース名形式で 1 DataFrame に横結合。
    返り列名 (attach 前 / TF suffix なし):
      - 1-A:        {base}            例: rsi14
      - 1-B:        {base}_W{W}       例: avg_body_ratio_W_W10
      - 1-C struct: {base}_N{N}       例: dist_to_POC_pct_N100_b020_N100
      - 1-C c2:     {base}_c2         例: dist_to_PP_pct_c2
    """
    parts = []
    parts.append(build_indicators_extended(df_tf))
    for W in W_CANDIDATES:
        parts.append(compute_1b_for_W(df_tf, W).add_suffix(f"_W{W}"))
    for N in N_CANDIDATES:
        parts.append(compute_features_for_N(df_tf, N).add_suffix(f"_N{N}"))
    parts.append(compute_c2_only(df_tf).add_suffix("_c2"))
    return pd.concat(parts, axis=1)


def attach_upper_tf(df5m_base: pd.DataFrame, feat_upper: pd.DataFrame, tf_upper: str) -> pd.DataFrame:
    """5m bar に上位 TF feature を look-ahead 防止 attach。
    5m close 時刻 (= 5m start + 5min) と 上位 TF close 時刻 (= 上位 start + freq) で merge_asof backward。
    """
    freq_td = FREQ_TD[tf_upper]
    feat = feat_upper.copy()
    feat.index = feat.index + freq_td
    feat.index.name = "_close_t"
    feat = feat.reset_index()

    base = df5m_base.reset_index().rename(columns={"timestamp": "_5m_start"})
    base["_close_t"] = base["_5m_start"] + FREQ_TD["5m"]

    merged = pd.merge_asof(
        base.sort_values("_close_t"),
        feat.sort_values("_close_t"),
        on="_close_t",
        direction="backward",
    )
    merged = merged.drop(columns=["_close_t"]).rename(columns={"_5m_start": "timestamp"})
    return merged.set_index("timestamp")


def assemble_features(df5m: pd.DataFrame, feat_per_tf: dict, pruned_spec: dict) -> pd.DataFrame:
    """各 TF feature DataFrame から pruned 該当列のみ保持し、{base}__{tf} で改名 -> 5m bar に統合。"""
    out = df5m[["close"]].copy()
    for tf in TIMEFRAMES:
        feat = feat_per_tf[tf]
        pruned_cols = set()
        for cat in ["1-A", "1-B", "1-C"]:
            pruned_cols |= set(pruned_spec[cat][tf]["all"])
        keep = [c for c in feat.columns if c in pruned_cols]
        feat_keep = feat[keep].add_suffix(f"__{tf}")
        if tf == "5m":
            out = pd.concat([out, feat_keep], axis=1)
        else:
            out = attach_upper_tf(out, feat_keep, tf)
    return out


def expected_indicator_columns(pruned_spec: dict) -> set:
    expected = set()
    for cat in ["1-A", "1-B", "1-C"]:
        for tf in TIMEFRAMES:
            for col in pruned_spec[cat][tf]["all"]:
                expected.add(f"{col}__{tf}")
    return expected


def validate_columns(df: pd.DataFrame, pruned_spec: dict) -> None:
    expected = expected_indicator_columns(pruned_spec)
    actual = {c for c in df.columns
              if "__" in c and c.rsplit("__", 1)[1] in TIMEFRAMES}
    missing = expected - actual
    extra = actual - expected
    if missing or extra:
        raise RuntimeError(
            f"指標列集合の不一致:\n"
            f"  expected: {len(expected)} (pruned から展開)\n"
            f"  actual:   {len(actual)} (build_labels_pct 出力)\n"
            f"  missing ({len(missing)}, head 10): {sorted(missing)[:10]}\n"
            f"  extra   ({len(extra)}, head 10):   {sorted(extra)[:10]}"
        )
    print(f"[assert OK] 指標列 {len(expected)} 完全一致 (1,432 期待)")


def compute_mfe_mae_labels_pct(df5m: pd.DataFrame) -> pd.DataFrame:
    """K=6/12/24/48/96/144/288 で 28 ラベル (pct ベース) 算出。
    t 行で h[t+1..t+K] の max / l[t+1..t+K] の min を得るため、
    shift(-K) で h[t+K] を t 行に移し、rolling(K) で過去 K 行 (= h[t+1..t+K]) を集計。
    USD 絶対値ではなく close[t] で除算した pct (BTC 価格非依存)。
    """
    out = pd.DataFrame(index=df5m.index)
    c = df5m["close"]
    h = df5m["high"]
    l = df5m["low"]
    for K in K_BARS:
        fut_max_high = h.shift(-K).rolling(K).max()
        fut_min_low = l.shift(-K).rolling(K).min()
        out[f"LONG_MFE_pct_K{K}"] = (fut_max_high - c) / c * 100
        out[f"LONG_MAE_pct_K{K}"] = (c - fut_min_low) / c * 100
        out[f"SHORT_MFE_pct_K{K}"] = (c - fut_min_low) / c * 100
        out[f"SHORT_MAE_pct_K{K}"] = (fut_max_high - c) / c * 100
    return out


def add_maintenance_flag(df: pd.DataFrame) -> pd.DataFrame:
    """火/水/木 05-08 UTC の bar に is_maintenance=True フラグを追加。
    Bitget 定期メンテ (exchange_spec.md)・Phase 1 学習時に df[~df.is_maintenance] で除外。
    行は drop しない (統計記録 + 後段切替柔軟性のため)。
    """
    df = df.copy()
    df["is_maintenance"] = (
        df.index.weekday.isin(MAINTENANCE_WEEKDAYS) &
        df.index.hour.isin(MAINTENANCE_HOURS)
    )
    return df


def run_dry_run(df5m: pd.DataFrame, pruned_spec: dict) -> None:
    """pruned_spec 構造 + 関数 import + 期待集合 1,432 を確認 (指標計算スキップ・数秒)。"""
    expected = expected_indicator_columns(pruned_spec)
    print(f"[dry-run] pruned 期待列集合: {len(expected)} 列")
    print(f"[dry-run] カテゴリ × TF 内訳:")
    for cat in ["1-A", "1-B", "1-C"]:
        per_tf = " ".join(f"{tf}={len(pruned_spec[cat][tf]['all'])}" for tf in TIMEFRAMES)
        cat_total = sum(len(pruned_spec[cat][tf]["all"]) for tf in TIMEFRAMES)
        print(f"  {cat}: {per_tf} (total {cat_total})")

    if len(expected) != 1432:
        raise RuntimeError(f"期待集合の総数が 1,432 と不一致: {len(expected)}")

    print(f"[dry-run] K_BARS: {K_BARS} → {len(K_BARS) * 4} ラベル (LONG/SHORT × MFE/MAE × {len(K_BARS)}K)")
    print(f"[dry-run] メンテ時間帯除外: weekdays={MAINTENANCE_WEEKDAYS} hours={MAINTENANCE_HOURS}")

    print(f"[dry-run] 関数 import 確認:")
    for fn in [build_indicators_extended, compute_1b_for_W, compute_features_for_N, compute_c2_only]:
        print(f"  {fn.__module__}.{fn.__name__}")

    print(f"[dry-run] 5m bar 行数: {len(df5m):,} (期間: {df5m.index.min()} 〜 {df5m.index.max()})")

    n_maint = int((df5m.index.weekday.isin(MAINTENANCE_WEEKDAYS) &
                   df5m.index.hour.isin(MAINTENANCE_HOURS)).sum())
    print(f"[dry-run] メンテ時間帯該当 bar (全期間): {n_maint:,} ({n_maint / len(df5m) * 100:.2f}%)")

    print(f"[dry-run] OK: 構造確認完了 (実計算なし)")


def run_sample(df5m: pd.DataFrame, pruned_spec: dict, sample_days: int) -> None:
    """先頭 N 日のみで全処理。出力: labels_mfe_mae_pct_sample.parquet"""
    sample_bars = sample_days * 24 * 12
    df_small = df5m.iloc[:sample_bars].copy()
    print(f"[sample] {sample_days} 日 = {len(df_small):,} 行 ({df_small.index.min()} 〜 {df_small.index.max()})")

    feat_per_tf = {}
    for tf in TIMEFRAMES:
        df_tf = df_small if tf == "5m" else resample_ohlcv(df_small, RESAMPLE_RULE[tf])
        print(f"  [feat] {tf}: {len(df_tf):,} bars, 指標計算...")
        feat_per_tf[tf] = compute_features_for_tf(df_tf)
        print(f"  [feat] {tf}: {feat_per_tf[tf].shape[1]} cols 算出")

    print("[attach] MTF 結合 (look-ahead 防止)")
    bar_with_feats = assemble_features(df_small, feat_per_tf, pruned_spec)
    validate_columns(bar_with_feats, pruned_spec)

    print("[label] MFE/MAE pct 計算 (28 ラベル)")
    labels = compute_mfe_mae_labels_pct(df_small)
    full = pd.concat([bar_with_feats, labels], axis=1)
    n_before = len(full)
    full = full.dropna(subset=[f"LONG_MFE_pct_K{K_BARS[-1]}"])
    print(f"  末尾ラベル欠損行 drop: {n_before - len(full)} 行")

    full = add_maintenance_flag(full)
    n_maint = int(full["is_maintenance"].sum())
    print(f"  メンテ時間帯 flag: {n_maint:,} 行 ({n_maint / len(full) * 100:.2f}%)")

    full.to_parquet(OUT_SAMPLE, compression="snappy")
    print(f"[sample] write: {OUT_SAMPLE} ({len(full):,} 行 / {OUT_SAMPLE.stat().st_size / 1e6:.1f} MB)")


def run_full(df5m: pd.DataFrame, pruned_spec: dict) -> None:
    """フル 5y 処理 + train/test 2 parquet 出力"""
    feat_per_tf = {}
    for tf in TIMEFRAMES:
        df_tf = df5m if tf == "5m" else resample_ohlcv(df5m, RESAMPLE_RULE[tf])
        print(f"  [feat] {tf}: {len(df_tf):,} bars, 指標計算...")
        feat_per_tf[tf] = compute_features_for_tf(df_tf)
        print(f"  [feat] {tf}: {feat_per_tf[tf].shape[1]} cols 算出 (pruned 絞り込み前)")

    print("[attach] MTF 結合 (look-ahead 防止)")
    bar_with_feats = assemble_features(df5m, feat_per_tf, pruned_spec)
    validate_columns(bar_with_feats, pruned_spec)

    print("[label] MFE/MAE pct 計算 (28 ラベル)")
    labels = compute_mfe_mae_labels_pct(df5m)
    full = pd.concat([bar_with_feats, labels], axis=1)

    n_before = len(full)
    full = full.dropna(subset=[f"LONG_MFE_pct_K{K_BARS[-1]}"])
    print(f"  末尾ラベル欠損行 drop: {n_before - len(full)} 行 (K={K_BARS[-1]} 末尾 24h)")

    full = add_maintenance_flag(full)
    n_maint_total = int(full["is_maintenance"].sum())
    print(f"  メンテ時間帯 flag (全期間): {n_maint_total:,} 行 ({n_maint_total / len(full) * 100:.2f}%)")

    train = full.loc[(full.index >= TRAIN_START) & (full.index <= TRAIN_END)]
    test = full.loc[(full.index >= TEST_START) & (full.index <= TEST_END)]
    print(f"[split] train: {len(train):,} 行 ({train.index.min()} 〜 {train.index.max()}) "
          f"maintenance={int(train['is_maintenance'].sum()):,}")
    print(f"[split] test:  {len(test):,} 行 ({test.index.min()} 〜 {test.index.max()}) "
          f"maintenance={int(test['is_maintenance'].sum()):,}")

    print(f"[write] {OUT_TRAIN}")
    train.to_parquet(OUT_TRAIN, compression="snappy")
    print(f"[write] {OUT_TEST}")
    test.to_parquet(OUT_TEST, compression="snappy")
    print(f"[done] train: {OUT_TRAIN.stat().st_size / 1e9:.2f} GB")
    print(f"[done] test:  {OUT_TEST.stat().st_size / 1e9:.2f} GB")


def run_test_2026q1(df5m: pd.DataFrame, pruned_spec: dict) -> None:
    """2026 Q1 だけのラベル parquet を生成 (Phase 6 本テスト用)。既存 train/test を上書きしない。"""
    feat_per_tf = {}
    for tf in TIMEFRAMES:
        df_tf = df5m if tf == "5m" else resample_ohlcv(df5m, RESAMPLE_RULE[tf])
        print(f"  [feat] {tf}: {len(df_tf):,} bars, 指標計算...")
        feat_per_tf[tf] = compute_features_for_tf(df_tf)
        print(f"  [feat] {tf}: {feat_per_tf[tf].shape[1]} cols 算出 (pruned 絞り込み前)")

    print("[attach] MTF 結合 (look-ahead 防止)")
    bar_with_feats = assemble_features(df5m, feat_per_tf, pruned_spec)
    validate_columns(bar_with_feats, pruned_spec)

    print("[label] MFE/MAE pct 計算 (28 ラベル)")
    labels = compute_mfe_mae_labels_pct(df5m)
    full = pd.concat([bar_with_feats, labels], axis=1)

    n_before = len(full)
    full = full.dropna(subset=[f"LONG_MFE_pct_K{K_BARS[-1]}"])
    print(f"  末尾ラベル欠損行 drop: {n_before - len(full)} 行 (K={K_BARS[-1]} 末尾 24h)")

    full = add_maintenance_flag(full)

    test_q1 = full.loc[(full.index >= TEST_2026Q1_START) & (full.index <= TEST_2026Q1_END)]
    print(f"[split] test_2026_q1: {len(test_q1):,} 行 ({test_q1.index.min()} 〜 {test_q1.index.max()}) "
          f"maintenance={int(test_q1['is_maintenance'].sum()):,}")

    print(f"[write] {OUT_TEST_2026Q1}")
    test_q1.to_parquet(OUT_TEST_2026Q1, compression="snappy")
    print(f"[done] {OUT_TEST_2026Q1.stat().st_size / 1e9:.2f} GB")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 0: 5m bar × 1,432 指標 × 28 ラベル (pct) parquet 生成")
    p.add_argument("--dry-run", action="store_true",
                   help="pruned 構造 + import + 期待集合 1,432 確認のみ (指標計算スキップ・数秒)")
    p.add_argument("--sample-days", type=int, default=None,
                   help="先頭 N 日のみで全処理 (sample.parquet 出力・数分)")
    p.add_argument("--test-2026q1", action="store_true",
                   help="2026-01-01〜2026-03-31 のラベル parquet のみ生成 (Phase 6 本テスト用)")
    return p.parse_args()


def main(args: argparse.Namespace) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = pd.Timestamp.now()
    mode = "dry-run" if args.dry_run else (f"sample-{args.sample_days}d" if args.sample_days else "full")
    print(f"[start] {t0} mode={mode}")

    print(f"[load] {INPUT_CSV}")
    df5m = load_5m_bars(INPUT_CSV)
    print(f"  5m rows: {len(df5m):,} ({df5m.index.min()} 〜 {df5m.index.max()})")

    print(f"[load] {PRUNED_JSON}")
    pruned_spec = json.loads(PRUNED_JSON.read_text())

    if args.dry_run:
        run_dry_run(df5m, pruned_spec)
    elif args.sample_days:
        run_sample(df5m, pruned_spec, args.sample_days)
    elif args.test_2026q1:
        run_test_2026q1(df5m, pruned_spec)
    else:
        run_full(df5m, pruned_spec)

    print(f"[end] elapsed: {pd.Timestamp.now() - t0}")


if __name__ == "__main__":
    main(parse_args())
