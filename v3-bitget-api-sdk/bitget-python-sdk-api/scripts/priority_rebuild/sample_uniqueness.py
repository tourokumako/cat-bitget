#!/usr/bin/env python3
"""
sample_uniqueness.py — 評価基盤 項目C: sample uniqueness + sequential bootstrap（自前・AFML Ch.4）

位置づけ:
  ml_pipeline_baseline_v1.md §0.8③ / §6「評価基盤 詳細設計 C」の実装。
  重なり合うラベル（overlapping labels）の冗長を補正し、OOS 過大評価（intra-estimator
  overlap）を断つ。cat-bitget では K=288 窓で隣接ラベル重複 99.65%（execlog）＝
  「同じ情報を何百回も数えて証拠量を錯覚」する状態。

なぜ mlfinlab でなく自前か（2026-05-31 WebSearch verify・記憶でなく検証済）:
  - mlfinlab（Hudson & Thames）は **全権利留保・商用は有償ライセンス必須**（実弾商用ボットで使用不可）
    かつ Python 3.7〜3.9 世代で **3.11 非対応**（本 venv=3.11.15・2023 から保守停止）。
  - mlfinpy（MIT・3.11 対応フォーク）は v0.1.2(2024-10)・**Alpha**・約19ヶ月更新なし → 計器の心臓部に
    未成熟依存は入れない。
  - アルゴリズム自体は López de Prado AFML Ch.4 の公開知識（教科書の式を実装するのは合法）。
    約定/コスト計器（項目A）と同様、自前実装 + 既知答えテストで正しさを数学的に証明する（L-242）。

正しさの証明: test_sample_uniqueness_known_answers.py の C1-C5 が全 pass すること。

参照: Lopez de Prado "Advances in Financial Machine Learning" Ch.4 (snippets 4.1-4.5)
"""

from __future__ import annotations

import numpy as np


def label_spans_from_horizon(n_signals: int, horizon_bars: int, n_bars: int,
                             start_idx: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """固定ホライズン K のラベル区間 [start, start+K] を bar index で返す。

    cat-bitget の Phase 0 ラベルは bar i から K 本先までの未来を見る → 区間 = [i, min(i+K, n-1)]。

    Args:
        n_signals: シグナル本数（start_idx 未指定時は 0..n_signals-1 を使う）
        horizon_bars: K（ラベルが見る未来の本数）
        n_bars: 系列全長
        start_idx: 各ラベルの開始 bar index（省略時 arange）
    Returns:
        (starts, ends) いずれも int 配列・end は inclusive・n_bars-1 で clip
    """
    if start_idx is None:
        start_idx = np.arange(n_signals)
    starts = np.asarray(start_idx, dtype=np.int64)
    ends = np.minimum(starts + horizon_bars, n_bars - 1).astype(np.int64)
    return starts, ends


def concurrency(starts: np.ndarray, ends: np.ndarray, n_bars: int) -> np.ndarray:
    """各 bar で「同時に生きているラベル数」c_t を返す（AFML snippet 4.1）。

    ラベル i は区間 [starts[i], ends[i]]（inclusive）で生きている。
    """
    c = np.zeros(n_bars, dtype=np.float64)
    for s, e in zip(starts, ends):
        c[s:e + 1] += 1.0
    return c


def average_uniqueness(starts: np.ndarray, ends: np.ndarray,
                       conc: np.ndarray | None = None, n_bars: int | None = None) -> np.ndarray:
    """各ラベルの平均ユニークネス ū_i を返す（AFML snippet 4.2）。

    ū_i = mean over t in [start_i, end_i] of 1/c_t。
    全ラベルが同一区間で N 本重なるなら各 ū_i = 1/N（＝重み 1/N）。
    重なりが無ければ ū_i = 1.0（完全にユニーク）。
    """
    if conc is None:
        if n_bars is None:
            n_bars = int(max(ends)) + 1
        conc = concurrency(starts, ends, n_bars)
    u = np.empty(len(starts), dtype=np.float64)
    for i, (s, e) in enumerate(zip(starts, ends)):
        seg = conc[s:e + 1]
        u[i] = float(np.mean(1.0 / seg))
    return u


def sample_weight_by_uniqueness(starts: np.ndarray, ends: np.ndarray, n_bars: int,
                                normalize: bool = True) -> np.ndarray:
    """学習用 sample_weight（= 平均ユニークネス）。

    normalize=True で sum(weight)=N（sklearn/LightGBM の sample_weight 慣例）に正規化。
    重なりの多いサンプルほど軽く扱い、冗長カウントによる過大評価を防ぐ。
    """
    u = average_uniqueness(starts, ends, n_bars=n_bars)
    if normalize:
        u = u * (len(u) / u.sum())
    return u


def effective_sample_size(starts: np.ndarray, ends: np.ndarray, n_bars: int) -> float:
    """実効サンプル数 = sum(平均ユニークネス)（AFML）。

    「独立サンプルが実質何個分か」。全 N 本が同一窓なら 1.0（N 個あっても独立は 1 個分）。
    これが N より大幅に小さいほど OOS 成績が過大評価されている（証拠量の錯覚）。
    """
    return float(np.sum(average_uniqueness(starts, ends, n_bars=n_bars)))


def _avg_uniqueness_of_sample(picks: list[int], starts: np.ndarray, ends: np.ndarray,
                              n_bars: int) -> float:
    """抽出した（重複含む）サンプル集合の平均ユニークネス。

    抽出集合から concurrency を作り直し、各 pick の 1/c をその生存 bar で平均 → 全 pick で平均。
    sequential bootstrap が standard bootstrap よりこの値を高くする（= debiasing）。
    """
    c = np.zeros(n_bars, dtype=np.float64)
    for p in picks:
        c[starts[p]:ends[p] + 1] += 1.0
    vals = []
    for p in picks:
        seg = c[starts[p]:ends[p] + 1]
        vals.append(float(np.mean(1.0 / seg)))
    return float(np.mean(vals))


def sequential_bootstrap(starts: np.ndarray, ends: np.ndarray, n_bars: int,
                         n_draw: int | None = None, seed: int = 0) -> list[int]:
    """sequential bootstrap（AFML snippet 4.5）。

    既に引いたサンプルとの重なりが少ない（情報を新しく足す）サンプルを優先して逐次抽出する。
    引くたびに各候補の「既抽出集合に加えたときの平均ユニークネス」を確率に使う。
    計算量 O(n_draw × n_labels × bars) → 大規模は bagging のサブサンプルに適用する。
    """
    n_labels = len(starts)
    if n_draw is None:
        n_draw = n_labels
    rng = np.random.default_rng(seed)
    c_drawn = np.zeros(n_bars, dtype=np.float64)  # 既抽出の concurrency
    picks: list[int] = []
    for _ in range(n_draw):
        avg_u = np.zeros(n_labels, dtype=np.float64)
        for j in range(n_labels):
            s, e = starts[j], ends[j]
            cj = c_drawn[s:e + 1] + 1.0  # 候補 j を 1 本足した場合の concurrency
            avg_u[j] = float(np.mean(1.0 / cj))
        prob = avg_u / avg_u.sum()
        pick = int(rng.choice(n_labels, p=prob))
        picks.append(pick)
        c_drawn[starts[pick]:ends[pick] + 1] += 1.0
    return picks


def standard_bootstrap(n_labels: int, n_draw: int | None = None, seed: int = 0) -> list[int]:
    """通常の一様復元抽出（比較用ベースライン）。"""
    if n_draw is None:
        n_draw = n_labels
    rng = np.random.default_rng(seed)
    return [int(x) for x in rng.integers(0, n_labels, size=n_draw)]
