"""
工程 [1.5] regime ensemble — 固定ルール判定器 (Stage B)

設計書: .claude/memory/ml_pipeline_baseline_v1.md v2.8 §6.1.3
CP1 監査: .claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md
  - C2 反映: ATR ボラ閾値を ATR_pct 25th/75th percentile data-driven に変更 (= 価格非依存性)

機能:
  1. Phase 0 v3.1 parquet 3 種を読み込み 1h grid に reduce
  2. 6 指標 scoring (= ADX / DI± / BB middle slope (%) / 価格 vs MA / MTF 整合 / 一目代替)
  3. 重み付き加点 (= MTF 整合のみ 1.5・他 1.0) → 上昇/下降/横ばい合計点
  4. 最高点採用 + 不明確閾値 + 連続 2 回ヒステリシス
  5. ATR_pct 25th/75th percentile (train_2021_2024 全期間) で volatility_level 算出
  6. raw 確率 (= 加点比) 算出・isotonic キャリブレーションは Stage E 直前に別途
  7. 3 dataset 全部に対して予測出力 + artifact 保存

入力:
  - results/priority_rebuild/labels_mfe_mae_pct_{train_2021_2024, test_2025, test_2026_q1}.parquet
出力:
  - results/regime_step1/rule_classifier_{ds}.parquet (1h grid・予測 + 確率 + 確信度 + volatility_level)
  - results/regime_step1/rule_classifier_artifact.json (= 閾値・統計情報)

CC 独断・要レビュー項目 (= 設計議論未経由の細部・まこさん判断待ち):
  R1: BB ミドル傾き (%) の N bar = 10 (= 直近 10 時間遡及・暫定値)
       根拠: cat_v9 BB slope ±10 は短期傾向想定・暫定値・実装後 verify
       影響: 大きすぎる N → トレンド転換検出が遅れる / 小さすぎる N → ノイズ拾う
  R2: 一目均衡表「雲」(= senkou_a/b) は Phase 0 v3.1 parquet に存在しないため
       close_vs_kijun_pct__1h で「価格 > 基準線 (+ 0.5%) / < 基準線 (- 0.5%) / 範囲内」で代替
       根拠: 雲 (senkou) は Phase 0 範囲外・kijun (基準線) で simplified approach
       影響: 雲情報量を相当削ぐ・将来 Phase 0 拡張で senkou 追加可能
  R3: 不明確閾値 = 3.0 (= 6 指標 × 平均 0.5 点・暫定値)
       根拠: ml_pipeline_baseline v2.8 §6.1.3 で明記・実装後 verify 必要
       影響: 大きい → 判定回数減・小さい → ノイズ拾う
  R4: 「価格 vs MA」の「MA 近い」判定 = ±0.5% 範囲 (= 全 3 MA すべてが ±0.5% 内なら横ばい)
       根拠: SMA20/50/EMA200 集合に対する近接性・暫定値
  R5: 「DI クロス付近」判定 = |DI+ - DI-| < 1.0
       根拠: ADX 業界閾値 (= 20-25 範囲) との整合・暫定値
  R6: ヒステリシス = 連続 2 回同じ判定で切替 (= HMM v15 と同じ)
       根拠: step1_regime_design §2.1 整合
  R7: ATR_pct percentile は train_2021_2024 全期間 (= 全 fold 統一) で計算
       根拠: state ラベル付け (= step1 §2.7) と同じ手法・fold 別ではない
  R8: BB ミドル (= SMA20) 傾き % 化計算式 = (sma20_now - sma20_N前) / sma20_N前 × 100
       根拠: USD 絶対値を避け価格非依存化・cat_v9 経験値 ±10 と同じ scale 想定
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ===== 設計書 §6.1.3 定数 =====
DATASETS = ["train_2021_2024", "test_2025", "test_2026_q1"]
LABEL_TF = "1h"
MTF_HIGHER_TF = "4h"

# scoring 重み (§6.1.3 表)
WEIGHT_ADX = 1.0
WEIGHT_DI = 1.0
WEIGHT_BB_SLOPE = 1.0
WEIGHT_PRICE_MA = 1.0
WEIGHT_MTF = 1.5
WEIGHT_ICHIMOKU = 1.0

# scoring 閾値 (§6.1.3 + cat_v9 経験値 + 業界 standard)
ADX_TREND_THRESHOLD = 25.0  # ADX >= 25 = 強トレンド (= KB §A.3.2)
ADX_WEAK_THRESHOLD = 20.0  # ADX < 20 = 弱トレンド (横ばい加点)
DI_CROSS_THRESHOLD = 1.0  # |DI+ - DI-| < 1.0 = クロス付近 (R5)
BB_SLOPE_THRESHOLD = 10.0  # BB ミドル傾き ±10% (R8・cat_v9 経験値)
PRICE_MA_PROXIMITY_PCT = 0.5  # 価格 vs MA ±0.5% (R4)
ICHIMOKU_KIJUN_THRESHOLD = 0.5  # close_vs_kijun_pct ±0.5% (R2)
UNCLEAR_THRESHOLD = 3.0  # 不明確閾値 (R3)
BB_MIDDLE_SLOPE_N_BARS = 10  # BB ミドル傾き計算用 N bars (R1・1h grid 上で 10 bar = 10 時間)

# パス
REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = REPO_ROOT / "results/priority_rebuild"
OUT_DIR = REPO_ROOT / "results/regime_step1"
OUT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_JSON = OUT_DIR / "rule_classifier_artifact.json"

# 必須列
REQUIRED_COLS = [
    "close",
    "adx14__1h", "di_plus__1h", "di_minus__1h",
    "close_vs_sma20_pct__1h", "close_vs_sma50_pct__1h", "close_vs_ema200_pct__1h",
    "close_vs_sma20_pct__4h", "close_vs_sma50_pct__4h", "close_vs_ema200_pct__4h",
    "close_vs_kijun_pct__1h",
    "atr14_pct__1h",
    # 1h SMA20 は直接列としては存在しない (= close_vs_sma20_pct__1h と close から導出)
]


def load_parquet(ds: str) -> pd.DataFrame:
    p = INPUT_DIR / f"labels_mfe_mae_pct_{ds}.parquet"
    if not p.exists():
        sys.exit(f"ABORT: input parquet not found: {p}")
    df = pd.read_parquet(p, columns=None)
    miss = [c for c in REQUIRED_COLS if c not in df.columns]
    if miss:
        sys.exit(f"ABORT: missing required cols in {ds}: {miss[:10]}")
    return df


def reduce_to_1h_grid(df_5m: pd.DataFrame) -> pd.DataFrame:
    """5m grid → 1h grid に reduce (= 各 1h bar の末尾 = 該当 1h close 時点の値)。

    Phase 0 v3.1 では上位足は forward fill 済 (= 各 5m bar に直近確定の 1h/4h 値が貼られている) ので、
    1h grid の末尾 (= label="right", closed="right") を取ると当該 1h の close 時点の確定値が得られる。
    """
    return df_5m.resample("1h", label="right", closed="right").last()


def compute_bb_middle_slope_pct_1h(df_5m: pd.DataFrame) -> pd.Series:
    """BB ミドル (= SMA20) の N-bar slope (%) を 1h grid で計算する (= R8 価格非依存化)。

    手順:
      1. 5m close を 1h grid に resample (= label="right", closed="right" で各 1h close)
      2. 1h SMA20 = 1h close の rolling(20).mean()
      3. N-bar slope (%) = (sma20_now - sma20_{N前}) / sma20_{N前} × 100
    """
    close_5m = df_5m["close"].astype(float)
    close_1h = close_5m.resample("1h", label="right", closed="right").last()
    sma20_1h = close_1h.rolling(20, min_periods=20).mean()
    slope_pct = (sma20_1h - sma20_1h.shift(BB_MIDDLE_SLOPE_N_BARS)) / sma20_1h.shift(BB_MIDDLE_SLOPE_N_BARS) * 100.0
    slope_pct.name = "bb_middle_slope_pct_1h"
    return slope_pct


def scoring_adx_di(row: pd.Series) -> tuple[float, float, float]:
    """
    ADX + DI スコアリング.
    戻り値: (up_score, down_score, range_score)

    - ADX(14): >= 25 強トレンド両方向加点 / < 20 横ばい加点
    - DI+/DI-: DI+ > DI- 上昇 / DI- > DI+ 下降 / クロス付近 (差 < 1.0) 横ばい
    """
    up, down, rng = 0.0, 0.0, 0.0
    adx = row["adx14__1h"]
    di_p = row["di_plus__1h"]
    di_m = row["di_minus__1h"]

    # ADX
    if pd.notna(adx):
        if adx >= ADX_TREND_THRESHOLD:
            up += WEIGHT_ADX  # 強トレンドは両方向加点 (= 設計書 §6.1.3 表)
            down += WEIGHT_ADX
        elif adx < ADX_WEAK_THRESHOLD:
            rng += WEIGHT_ADX

    # DI+/DI-
    if pd.notna(di_p) and pd.notna(di_m):
        di_diff = di_p - di_m
        if abs(di_diff) < DI_CROSS_THRESHOLD:
            rng += WEIGHT_DI
        elif di_diff > 0:
            up += WEIGHT_DI
        else:
            down += WEIGHT_DI

    return up, down, rng


def scoring_bb_slope(slope_pct: float) -> tuple[float, float, float]:
    up, down, rng = 0.0, 0.0, 0.0
    if pd.notna(slope_pct):
        if slope_pct > BB_SLOPE_THRESHOLD:
            up += WEIGHT_BB_SLOPE
        elif slope_pct < -BB_SLOPE_THRESHOLD:
            down += WEIGHT_BB_SLOPE
        else:
            rng += WEIGHT_BB_SLOPE
    return up, down, rng


def scoring_price_vs_ma(row: pd.Series, tf: str = "1h") -> tuple[float, float, float, str]:
    """
    価格 vs MA (SMA20/SMA50/EMA200) スコアリング.
    戻り値: (up_score, down_score, range_score, signal_direction)
      signal_direction: "up" / "down" / "range" (MTF 整合判定用)

    - 価格 > 全 MA: 上昇加点
    - 価格 < 全 MA: 下降加点
    - 全 MA が ±0.5% 範囲: 横ばい加点
    - それ以外: 加点なし (= 中間状態)
    """
    up, down, rng = 0.0, 0.0, 0.0
    sma20 = row.get(f"close_vs_sma20_pct__{tf}")
    sma50 = row.get(f"close_vs_sma50_pct__{tf}")
    ema200 = row.get(f"close_vs_ema200_pct__{tf}")

    if not all(pd.notna(v) for v in [sma20, sma50, ema200]):
        return up, down, rng, "unknown"

    above_all = all(v > 0 for v in [sma20, sma50, ema200])
    below_all = all(v < 0 for v in [sma20, sma50, ema200])
    all_near = all(abs(v) <= PRICE_MA_PROXIMITY_PCT for v in [sma20, sma50, ema200])

    if all_near:
        rng += WEIGHT_PRICE_MA
        return up, down, rng, "range"
    if above_all:
        up += WEIGHT_PRICE_MA
        return up, down, rng, "up"
    if below_all:
        down += WEIGHT_PRICE_MA
        return up, down, rng, "down"
    return up, down, rng, "mixed"


def scoring_mtf(row: pd.Series) -> tuple[float, float, float]:
    """
    MTF 整合 (= 1h + 4h の価格 vs MA 一致). 重み 1.5.
    """
    up, down, rng = 0.0, 0.0, 0.0
    _, _, _, dir_1h = scoring_price_vs_ma(row, "1h")
    _, _, _, dir_4h = scoring_price_vs_ma(row, "4h")

    if dir_1h == dir_4h:
        if dir_1h == "up":
            up += WEIGHT_MTF
        elif dir_1h == "down":
            down += WEIGHT_MTF
        elif dir_1h == "range":
            rng += WEIGHT_MTF
        # mixed/unknown は加点なし
    # 不一致は加点なし (= 設計書: 不一致 → 横ばい加点)
    elif "unknown" not in (dir_1h, dir_4h):
        rng += WEIGHT_MTF
    return up, down, rng


def scoring_ichimoku(row: pd.Series) -> tuple[float, float, float]:
    """
    一目均衡表代替 (= R2 ・close_vs_kijun_pct__1h で simplified approach).
    雲 (senkou) は Phase 0 v3.1 範囲外のため kijun (基準線) で代替.
    """
    up, down, rng = 0.0, 0.0, 0.0
    k = row.get("close_vs_kijun_pct__1h")
    if pd.notna(k):
        if k > ICHIMOKU_KIJUN_THRESHOLD:
            up += WEIGHT_ICHIMOKU
        elif k < -ICHIMOKU_KIJUN_THRESHOLD:
            down += WEIGHT_ICHIMOKU
        else:
            rng += WEIGHT_ICHIMOKU
    return up, down, rng


def compute_scores_1h(df_1h: pd.DataFrame, bb_slope_1h: pd.Series) -> pd.DataFrame:
    """各 1h bar について 6 指標 scoring を計算する。

    戻り値の列:
      - up_score / down_score / range_score: 各カテゴリの加点合計
      - max_score: 最高点
      - second_score: 2 番目の点
      - raw_label: 不明確判定なしの生 label (= "up" / "down" / "range")
      - is_unclear: 最高点が UNCLEAR_THRESHOLD 未満なら True
    """
    bb_slope_aligned = bb_slope_1h.reindex(df_1h.index)

    up_scores = np.zeros(len(df_1h))
    down_scores = np.zeros(len(df_1h))
    range_scores = np.zeros(len(df_1h))

    for i, (ts, row) in enumerate(df_1h.iterrows()):
        # 1. ADX + DI
        u, d, r = scoring_adx_di(row)
        up_scores[i] += u
        down_scores[i] += d
        range_scores[i] += r

        # 2. BB ミドル傾き
        u, d, r = scoring_bb_slope(bb_slope_aligned.iloc[i])
        up_scores[i] += u
        down_scores[i] += d
        range_scores[i] += r

        # 3. 価格 vs MA (1h)
        u, d, r, _ = scoring_price_vs_ma(row, "1h")
        up_scores[i] += u
        down_scores[i] += d
        range_scores[i] += r

        # 4. MTF 整合 (重み 1.5)
        u, d, r = scoring_mtf(row)
        up_scores[i] += u
        down_scores[i] += d
        range_scores[i] += r

        # 5. 一目均衡表代替
        u, d, r = scoring_ichimoku(row)
        up_scores[i] += u
        down_scores[i] += d
        range_scores[i] += r

    # 最高点 + 2 番目の点 + 生 label
    scores = pd.DataFrame({
        "up_score": up_scores,
        "down_score": down_scores,
        "range_score": range_scores,
    }, index=df_1h.index)

    score_matrix = scores[["up_score", "down_score", "range_score"]].values
    max_idx = np.argmax(score_matrix, axis=1)
    sorted_scores = np.sort(score_matrix, axis=1)
    max_score = sorted_scores[:, -1]
    second_score = sorted_scores[:, -2]
    label_map = {0: "uptrend", 1: "downtrend", 2: "range"}
    raw_label = np.array([label_map[i] for i in max_idx])
    is_unclear = max_score < UNCLEAR_THRESHOLD

    scores["max_score"] = max_score
    scores["second_score"] = second_score
    scores["raw_label"] = raw_label
    scores["is_unclear"] = is_unclear

    return scores


def apply_hysteresis(scores: pd.DataFrame) -> pd.Series:
    """連続 2 回同じ raw_label で切替 + 不明確時は直前判定維持 (= R6).

    戻り値: regime_label series (= "uptrend" / "downtrend" / "range" / "unclear")
    """
    raw = scores["raw_label"].values
    unclear = scores["is_unclear"].values
    n = len(raw)

    out = np.empty(n, dtype=object)
    confirmed = "range"  # 初期値 (= 任意・最初の 2 bars は確定なし → range)
    candidate = None
    streak = 0

    for i in range(n):
        if unclear[i]:
            # 不明確時は直前確定ラベル維持
            out[i] = confirmed
            # candidate streak はリセット (= 不明確 1 回挟むと連続性破綻)
            candidate = None
            streak = 0
            continue

        if raw[i] == confirmed:
            # 確定ラベルと同じ → 維持
            out[i] = confirmed
            candidate = None
            streak = 0
        else:
            # 異なる → candidate streak
            if candidate == raw[i]:
                streak += 1
            else:
                candidate = raw[i]
                streak = 1

            if streak >= 2:
                # 連続 2 回同じ candidate → 切替
                confirmed = candidate
                candidate = None
                streak = 0
                out[i] = confirmed
            else:
                # streak 1 のみ → 直前確定ラベル維持
                out[i] = confirmed

    return pd.Series(out, index=scores.index, name="regime_label")


def compute_probabilities(scores: pd.DataFrame) -> pd.DataFrame:
    """raw 確率 (= 加点比) と確信度を計算する.

    各カテゴリ確率 = score / total_score (= 0 のとき equiprobable 1/3)
    確信度 = (max_score - second_score) / max(max_score, 1e-9)
    """
    total = scores["up_score"] + scores["down_score"] + scores["range_score"]
    safe_total = total.where(total > 0, np.nan)
    prob_up = (scores["up_score"] / safe_total).fillna(1.0 / 3.0)
    prob_down = (scores["down_score"] / safe_total).fillna(1.0 / 3.0)
    prob_range = (scores["range_score"] / safe_total).fillna(1.0 / 3.0)

    confidence = (scores["max_score"] - scores["second_score"]) / scores["max_score"].where(scores["max_score"] > 0, np.nan)
    confidence = confidence.fillna(0.0)

    return pd.DataFrame({
        "prob_up": prob_up,
        "prob_down": prob_down,
        "prob_range": prob_range,
        "confidence": confidence,
    })


def compute_volatility_thresholds_from_train(df_train_1h: pd.DataFrame) -> dict:
    """train_2021_2024 で ATR_pct の 25th / 75th percentile を計算する (= R7・CP1 監査 C2)."""
    atr_1h = df_train_1h["atr14_pct__1h"].dropna()
    p25 = float(np.nanpercentile(atr_1h, 25))
    p75 = float(np.nanpercentile(atr_1h, 75))
    return {
        "p25": p25,
        "p75": p75,
        "source_ds": "train_2021_2024",
        "n_samples_used": int(len(atr_1h)),
    }


def compute_volatility_level(df_1h: pd.DataFrame, thresholds: dict) -> pd.Series:
    """ATR_pct percentile による volatility_level 算出."""
    atr = df_1h["atr14_pct__1h"]
    p25 = thresholds["p25"]
    p75 = thresholds["p75"]
    level = pd.Series(index=df_1h.index, dtype="object")
    level[atr >= p75] = "high"
    level[(atr >= p25) & (atr < p75)] = "mid"
    level[atr < p25] = "low"
    level[atr.isna()] = "unknown"
    level.name = "volatility_level"
    return level


def process_dataset(ds: str, vol_thresholds: dict | None) -> tuple[pd.DataFrame, dict]:
    """1 dataset を処理する.
    vol_thresholds が None なら train 用に新規計算して返す.
    """
    print(f"\n========== processing {ds} ==========")
    df_5m = load_parquet(ds)
    print(f"  5m rows: {len(df_5m)} ({df_5m.index.min()} -> {df_5m.index.max()})")

    df_1h = reduce_to_1h_grid(df_5m)
    print(f"  1h rows: {len(df_1h)}")

    bb_slope_1h = compute_bb_middle_slope_pct_1h(df_5m)
    print(f"  bb_middle_slope_pct_1h non-NaN: {bb_slope_1h.notna().sum()}/{len(bb_slope_1h)}")

    # vol threshold (= train で計算済なら継承・なければ train 用に計算)
    if vol_thresholds is None:
        vol_thresholds = compute_volatility_thresholds_from_train(df_1h)
        print(f"  vol_thresholds (from this dataset): p25={vol_thresholds['p25']:.4f} p75={vol_thresholds['p75']:.4f}")
    else:
        print(f"  vol_thresholds (inherited): p25={vol_thresholds['p25']:.4f} p75={vol_thresholds['p75']:.4f}")

    print("  computing scores ...")
    scores = compute_scores_1h(df_1h, bb_slope_1h)

    print("  applying hysteresis ...")
    regime_label = apply_hysteresis(scores)

    print("  computing probabilities ...")
    probs = compute_probabilities(scores)

    volatility_level = compute_volatility_level(df_1h, vol_thresholds)

    out = pd.DataFrame({
        "regime_label": regime_label,
        "regime_prob_up": probs["prob_up"],
        "regime_prob_down": probs["prob_down"],
        "regime_prob_range": probs["prob_range"],
        "regime_confidence": probs["confidence"],
        "regime_volatility_level": volatility_level,
        # debug 用 (後段検証で使う)
        "_score_up": scores["up_score"],
        "_score_down": scores["down_score"],
        "_score_range": scores["range_score"],
        "_score_max": scores["max_score"],
        "_score_second": scores["second_score"],
        "_raw_label": scores["raw_label"],
        "_is_unclear": scores["is_unclear"],
        "_bb_middle_slope_pct_1h": bb_slope_1h.reindex(df_1h.index),
        "_atr14_pct__1h": df_1h["atr14_pct__1h"],
    }, index=df_1h.index)

    label_counts = out["regime_label"].value_counts().to_dict()
    vol_counts = out["regime_volatility_level"].value_counts().to_dict()
    unclear_pct = float(scores["is_unclear"].mean() * 100)
    print(f"  regime_label distribution: {label_counts}")
    print(f"  volatility_level distribution: {vol_counts}")
    print(f"  unclear (raw) %: {unclear_pct:.2f}%")

    summary = {
        "dataset": ds,
        "rows_5m": int(len(df_5m)),
        "rows_1h": int(len(df_1h)),
        "label_distribution": {str(k): int(v) for k, v in label_counts.items()},
        "volatility_distribution": {str(k): int(v) for k, v in vol_counts.items()},
        "unclear_pct_raw": unclear_pct,
        "vol_thresholds": vol_thresholds,
    }
    return out, summary


def main() -> int:
    print(f"[input dir] {INPUT_DIR}")
    print(f"[output dir] {OUT_DIR}")

    summaries: dict = {}
    vol_thresholds: dict | None = None

    for i, ds in enumerate(DATASETS):
        # train_2021_2024 で vol threshold 計算 → test には継承
        out, sm = process_dataset(ds, vol_thresholds if ds != "train_2021_2024" else None)
        if ds == "train_2021_2024":
            vol_thresholds = sm["vol_thresholds"]
        summaries[ds] = sm

        out_path = OUT_DIR / f"rule_classifier_{ds}.parquet"
        out.to_parquet(out_path)
        print(f"  written: {out_path}")

    artifact = {
        "script": str(Path(__file__).relative_to(REPO_ROOT)),
        "design_doc": ".claude/memory/ml_pipeline_baseline_v1.md (v2.8 §6.1.3)",
        "cp1_audit": ".claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md",
        "weights": {
            "adx": WEIGHT_ADX,
            "di": WEIGHT_DI,
            "bb_slope": WEIGHT_BB_SLOPE,
            "price_ma": WEIGHT_PRICE_MA,
            "mtf": WEIGHT_MTF,
            "ichimoku": WEIGHT_ICHIMOKU,
        },
        "thresholds": {
            "adx_trend": ADX_TREND_THRESHOLD,
            "adx_weak": ADX_WEAK_THRESHOLD,
            "di_cross": DI_CROSS_THRESHOLD,
            "bb_slope": BB_SLOPE_THRESHOLD,
            "price_ma_proximity_pct": PRICE_MA_PROXIMITY_PCT,
            "ichimoku_kijun": ICHIMOKU_KIJUN_THRESHOLD,
            "unclear_score": UNCLEAR_THRESHOLD,
            "bb_middle_slope_n_bars": BB_MIDDLE_SLOPE_N_BARS,
        },
        "vol_thresholds_train": vol_thresholds,
        "summaries": summaries,
        "cc_independent_judgements": [
            "R1: BB ミドル傾き N=10 暫定値",
            "R2: 一目均衡表代替 = close_vs_kijun_pct__1h",
            "R3: 不明確閾値 3.0 暫定値",
            "R4: 価格 vs MA 近接性 ±0.5%",
            "R5: DI クロス付近 |diff| < 1.0",
            "R7: ATR_pct percentile は train 全期間 (fold 別ではない)",
            "R8: BB ミドル傾き % 化 = (sma20 N-bar slope) / sma20_N_前 × 100",
        ],
        "isotonic_calibration": "NOT applied in Stage B (= deferred to ensemble Stage E with target design)",
    }
    with ARTIFACT_JSON.open("w") as f:
        json.dump(artifact, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n[DONE] artifact saved: {ARTIFACT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
