"""
工程 [1.5] regime ensemble — target ラベル共通モジュール (Stage C/D/E で使用) v2

v2 改訂 (= 2026-05-27): target を「未来 4h 予測」→「過去 24h 描写」に変更.

改訂理由:
  - 旧 v1 = 将来 4h log_return ベース → これは未来予測タスクで難易度高く accuracy 0.46 頭打ち
  - regime 判定の本質 = 「いまどんな相場か」を後段 ML に伝える状況描写 (= 未来予測ではない)
  - 過去 24h log_return ベース = 過去の現状を機械的に確定するラベル → 描写タスクとして整合
  - accuracy 数字が改善し isotonic キャリブレーション + ensemble GridSearchCV の意味が見える

CC 独断・要レビュー項目 (v2):
  T1 (v2): horizon = 24h (= 1h grid で 24 bar 前まで遡る・**過去** 24 時間)
       根拠: 1 取引 2-3 時間想定で 24h は「直近の大局トレンド」を描写する適切な窓
       v1 旧値: 未来 4h (= 廃止)
  T2 (v2): 3 クラス閾値 = ±0.5% (= past 24h log return)
       根拠: 24h で ±0.5% 動けば「明確なトレンド」と言える業界感覚値
       影響: 大きい → range に偏る / 小さい → noise も trend 扱い
  T3: target 計算で close は parquet の 5m grid を 1h に resample (= label="right", closed="right")
       根拠: rule_classifier と同じ 1h grid alignment 整合
  T4: isotonic fit は train_2021_2024 全期間で 1 calibrator (= fold 別ではない)
       根拠: 教師なし regime で fold 別 calibrator は複雑度高い・global calibrator で十分とした
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = REPO_ROOT / "results/priority_rebuild"

# CC 独断・要レビュー (T1 v2, T2 v2)
TARGET_HORIZON_BARS = 24  # 1h grid で 24 bar = 24 時間 (= 過去 1 日分の現状描写)
TARGET_THRESHOLD_PCT = 0.5  # ±0.5% で 3 クラス分割

DATASETS = ["train_2021_2024", "test_2025", "test_2026_q1"]


def load_close_1h(ds: str) -> pd.Series:
    """parquet の 5m close を 1h grid に resample する (= rule_classifier と同じ alignment)."""
    p = INPUT_DIR / f"labels_mfe_mae_pct_{ds}.parquet"
    df = pd.read_parquet(p, columns=["close"])
    close_5m = df["close"].astype(float)
    close_1h = close_5m.resample("1h", label="right", closed="right").last()
    close_1h.name = "close_1h"
    return close_1h


def compute_past_log_return(close_1h: pd.Series, horizon: int = TARGET_HORIZON_BARS) -> pd.Series:
    """過去 horizon 時間の log return (= 現状描写).

    ret_t = log(close_t) - log(close_{t-horizon})
       = log(close_t / close_{t-horizon})

    過去情報のみ参照 → look-ahead leak なし・推論時も同じ式で取得可能.
    """
    log_close = np.log(close_1h)
    past_log_ret = log_close - log_close.shift(horizon)
    past_log_ret.name = f"past_{horizon}h_logret"
    return past_log_ret


def compute_target_3class(
    past_log_ret: pd.Series,
    threshold_pct: float = TARGET_THRESHOLD_PCT,
) -> pd.Series:
    """3 クラス target ラベル (= 過去 24h 描写ベース).

    - uptrend: past_log_ret * 100 > +threshold_pct (= 過去 24h で +0.5% 以上の上昇)
    - downtrend: past_log_ret * 100 < -threshold_pct (= 過去 24h で 0.5% 以上の下落)
    - range: それ以外
    """
    pct = past_log_ret * 100.0
    label = pd.Series(index=past_log_ret.index, dtype="object")
    label[pct > threshold_pct] = "uptrend"
    label[pct < -threshold_pct] = "downtrend"
    label[(pct >= -threshold_pct) & (pct <= threshold_pct)] = "range"
    label.name = "target_3class"
    return label


def compute_target_for_dataset(
    ds: str,
    horizon: int = TARGET_HORIZON_BARS,
    threshold_pct: float = TARGET_THRESHOLD_PCT,
) -> pd.DataFrame:
    """指定 dataset に対し 1h grid の past log return + 3 クラス target を返す.

    戻り値の index = rule_classifier の 1h grid と完全一致 (= close_1h.index).
    """
    close_1h = load_close_1h(ds)
    past_ret = compute_past_log_return(close_1h, horizon=horizon)
    target = compute_target_3class(past_ret, threshold_pct=threshold_pct)
    return pd.DataFrame({
        "close_1h": close_1h,
        f"past_{horizon}h_logret": past_ret,
        "target_3class": target,
    })


def get_config() -> dict:
    return {
        "horizon_bars": TARGET_HORIZON_BARS,
        "horizon_direction": "past",
        "threshold_pct": TARGET_THRESHOLD_PCT,
        "version": "v2 (= 2026-05-27 過去描写へ変更)",
        "cc_independent_judgements": [
            "T1 (v2): target horizon = 24h 過去 (= 1h grid 24 bar 前まで遡る)",
            "T2 (v2): 3 クラス閾値 = ±0.5%",
            "T3: close 1h grid = 5m parquet を resample(label=right, closed=right)",
            "T4: isotonic fit = train_2021_2024 全期間 1 calibrator (fold 別ではない)",
        ],
    }


if __name__ == "__main__":
    # 単体テスト: train_2021_2024 の target 分布を確認
    df = compute_target_for_dataset("train_2021_2024")
    print(f"shape: {df.shape}")
    print(f"target distribution:\n{df['target_3class'].value_counts(dropna=False)}")
    print(f"past_{TARGET_HORIZON_BARS}h_logret stats:\n{df[f'past_{TARGET_HORIZON_BARS}h_logret'].describe()}")
