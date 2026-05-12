"""build_labels.py — 段階 A-1: 5m bar × 1,432 指標 × 16 MFE/MAE ラベル を生成

目的: A-2 k=2 全探索の入力 parquet を作る。

実行モード (priority_rebuild.md §3.0):
  --dry-run            : pruned 構造 + import + 期待集合 1,432 確認のみ (数秒・指標計算スキップ)
  --sample-days N      : 先頭 N 日のみで全処理 (sample.parquet 出力・数分)
  (引数なし)            : フル 5y 処理 + train/test 2 parquet 出力 (数時間〜半日)

入力:
  - data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv (5m bar 525,709 行)
  - results/regime_label_analysis/pruned_column_list.json (1,432 列定義)

出力:
  - results/priority_rebuild/labels_mfe_mae_train_2021_2024.parquet (フル)
  - results/priority_rebuild/labels_mfe_mae_test_2025.parquet      (フル)
  - results/priority_rebuild/labels_mfe_mae_sample.parquet         (--sample-days)
  列構成: timestamp(index) + close + 1,432 指標列 + 16 ラベル列

列名規則 (pruned ベース名 + __{tf}):
  - 1-A:        rsi14__5m
  - 1-B:        avg_body_ratio_W_W10__5m
  - 1-C struct: dist_to_POC_pct_N100_b020_N100__5m
  - 1-C c2:     dist_to_PP_pct_c2__5m

ラベル (K=12/24/48/96 bar = 1h/2h/4h/8h):
  - LONG_MFE_K{K}  = max(high[t+1..t+K]) - close[t]
  - LONG_MAE_K{K}  = close[t] - min(low[t+1..t+K])
  - SHORT_MFE_K{K} = close[t] - min(low[t+1..t+K])
  - SHORT_MAE_K{K} = max(high[t+1..t+K]) - close[t]

look-ahead 防止:
  - 5m bar t (close 時刻 = t + 5min) で観測可能な上位 TF bar は T_upper + freq <= t + 5min
  - merge_asof(direction="backward") を 5m close 時刻 vs 上位 TF close 時刻 で適用
  - MFE/MAE ラベルは正解側のため A-2 で X に含めない (L-154)

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

INPUT_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
PRUNED_JSON = REPO_ROOT / "results" / "regime_label_analysis" / "pruned_column_list.json"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild"
OUT_TRAIN = OUT_DIR / "labels_mfe_mae_train_2021_2024.parquet"
OUT_TEST = OUT_DIR / "labels_mfe_mae_test_2025.parquet"
OUT_SAMPLE = OUT_DIR / "labels_mfe_mae_sample.parquet"

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
K_BARS = [12, 24, 48, 96]

TRAIN_START = pd.Timestamp("2021-04-01")
TRAIN_END = pd.Timestamp("2024-12-31 23:59:59")
TEST_START = pd.Timestamp("2025-01-01")
TEST_END = pd.Timestamp("2025-12-31 23:59:59")


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
            f"  actual:   {len(actual)} (build_labels 出力)\n"
            f"  missing ({len(missing)}, head 10): {sorted(missing)[:10]}\n"
            f"  extra   ({len(extra)}, head 10):   {sorted(extra)[:10]}"
        )
    print(f"[assert OK] 指標列 {len(expected)} 完全一致 (1,432 期待)")


def compute_mfe_mae_labels(df5m: pd.DataFrame) -> pd.DataFrame:
    """K=12/24/48/96 で 16 ラベル算出。
    t 行で h[t+1..t+K] の max / l[t+1..t+K] の min を得るため、
    shift(-K) で h[t+K] を t 行に移し、rolling(K) で過去 K 行 (= h[t+1..t+K]) を集計。
    """
    out = pd.DataFrame(index=df5m.index)
    c = df5m["close"]
    h = df5m["high"]
    l = df5m["low"]
    for K in K_BARS:
        fut_max_high = h.shift(-K).rolling(K).max()
        fut_min_low = l.shift(-K).rolling(K).min()
        out[f"LONG_MFE_K{K}"] = fut_max_high - c
        out[f"LONG_MAE_K{K}"] = c - fut_min_low
        out[f"SHORT_MFE_K{K}"] = c - fut_min_low
        out[f"SHORT_MAE_K{K}"] = fut_max_high - c
    return out


def run_dry_run(df5m: pd.DataFrame, pruned_spec: dict) -> None:
    """pruned_spec 構造 + 関数 import + 期待集合 1,432 を確認 (指標計算スキップ・数秒)。
    実コードの列名一致確認は --sample-days で行う (実計算が必要なため)。
    """
    expected = expected_indicator_columns(pruned_spec)
    print(f"[dry-run] pruned 期待列集合: {len(expected)} 列")
    print(f"[dry-run] カテゴリ × TF 内訳:")
    for cat in ["1-A", "1-B", "1-C"]:
        per_tf = " ".join(f"{tf}={len(pruned_spec[cat][tf]['all'])}" for tf in TIMEFRAMES)
        cat_total = sum(len(pruned_spec[cat][tf]["all"]) for tf in TIMEFRAMES)
        print(f"  {cat}: {per_tf} (total {cat_total})")

    if len(expected) != 1432:
        raise RuntimeError(f"期待集合の総数が 1,432 と不一致: {len(expected)}")

    print(f"[dry-run] 関数 import 確認:")
    for fn in [build_indicators_extended, compute_1b_for_W, compute_features_for_N, compute_c2_only]:
        print(f"  {fn.__module__}.{fn.__name__}")

    print(f"[dry-run] 5m bar 行数: {len(df5m):,} (期間: {df5m.index.min()} 〜 {df5m.index.max()})")
    print(f"[dry-run] OK: 構造確認完了 (実計算なし)")


def run_sample(df5m: pd.DataFrame, pruned_spec: dict, sample_days: int) -> None:
    """先頭 N 日のみで全処理 (assert + MTF attach 動作確認)。出力: labels_mfe_mae_sample.parquet"""
    sample_bars = sample_days * 24 * 12  # 5m bar/日 = 288
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

    print("[label] MFE/MAE 計算")
    labels = compute_mfe_mae_labels(df_small)
    full = pd.concat([bar_with_feats, labels], axis=1)
    n_before = len(full)
    full = full.dropna(subset=[f"LONG_MFE_K{K_BARS[-1]}"])
    print(f"  末尾ラベル欠損行 drop: {n_before - len(full)} 行")

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

    print("[label] MFE/MAE 計算")
    labels = compute_mfe_mae_labels(df5m)
    full = pd.concat([bar_with_feats, labels], axis=1)

    n_before = len(full)
    full = full.dropna(subset=[f"LONG_MFE_K{K_BARS[-1]}"])
    print(f"  末尾ラベル欠損行 drop: {n_before - len(full)} 行")

    train = full.loc[(full.index >= TRAIN_START) & (full.index <= TRAIN_END)]
    test = full.loc[(full.index >= TEST_START) & (full.index <= TEST_END)]
    print(f"[split] train: {len(train):,} 行 ({train.index.min()} 〜 {train.index.max()})")
    print(f"[split] test:  {len(test):,} 行 ({test.index.min()} 〜 {test.index.max()})")

    print(f"[write] {OUT_TRAIN}")
    train.to_parquet(OUT_TRAIN, compression="snappy")
    print(f"[write] {OUT_TEST}")
    test.to_parquet(OUT_TEST, compression="snappy")
    print(f"[done] train: {OUT_TRAIN.stat().st_size / 1e9:.2f} GB")
    print(f"[done] test:  {OUT_TEST.stat().st_size / 1e9:.2f} GB")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="段階 A-1: 5m bar × 1,432 指標 × 16 ラベル parquet 生成")
    p.add_argument("--dry-run", action="store_true",
                   help="pruned 構造 + import + 期待集合 1,432 確認のみ (指標計算スキップ・数秒)")
    p.add_argument("--sample-days", type=int, default=None,
                   help="先頭 N 日のみで全処理 (sample.parquet 出力・数分)")
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
    else:
        run_full(df5m, pruned_spec)

    print(f"[end] elapsed: {pd.Timestamp.now() - t0}")


if __name__ == "__main__":
    main(parse_args())
