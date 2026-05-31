#!/usr/bin/env python3
"""
purged_kfold.py — 評価基盤 項目D: Purged K-Fold + Embargo（自前・AFML Ch.7）

位置づけ:
  ml_pipeline_baseline_v1.md §0.8④ / §6「評価基盤 詳細設計 D」の実装。
  重なり合うラベル（overlapping labels）がある時系列で、交差検証の fold 間リークを断つ。
  普通の KFold は「テスト期間とラベル窓が重なる学習データ」を残すため OOS を過大評価する。

  purge と embargo は別物（baseline §0.8④・混同禁止）:
  - **purge（パージ）**: テスト窓と「ラベルの未来窓」が重なる学習サンプルを除去（intra/inter-fold leak）
  - **embargo（禁足）**: テスト窓直後の一定期間に始まる学習サンプルを除外（特徴量の前方リーク対策）

なぜ自前か: mlfinlab は商用有償+3.11非対応で除外（baseline §6 v3.15）。アルゴリズムは
  AFML Ch.7 の公開知識。自前実装 + 既知答えテストで正しさを数学的に証明（L-242）。

前提: サンプルは start（ラベル開始 bar index）昇順に並んでいること（時系列順）。
  本番再現性: test fold は時系列で連続ブロック・train は test より前/十分後のみ（未来先読みなし）。

参照: Lopez de Prado "Advances in Financial Machine Learning" Ch.7 (PurgedKFold, snippet 7.3)
"""

from __future__ import annotations

from typing import Iterator

import numpy as np


class PurgedKFold:
    """Purged K-Fold（embargo 付き）。

    Args:
        n_splits: fold 数
        starts: 各サンプルのラベル開始 bar index（昇順前提）
        ends:   各サンプルのラベル終了 bar index（inclusive・= start + K で clip）
        embargo_bars: テスト窓直後に禁足する bar 数（0 で embargo なし）
    """

    def __init__(self, n_splits: int, starts: np.ndarray, ends: np.ndarray,
                 embargo_bars: int = 0):
        if n_splits < 2:
            raise ValueError("n_splits は 2 以上")
        self.n_splits = n_splits
        self.starts = np.asarray(starts, dtype=np.int64)
        self.ends = np.asarray(ends, dtype=np.int64)
        self.embargo_bars = int(embargo_bars)
        if len(self.starts) != len(self.ends):
            raise ValueError("starts と ends の長さ不一致")
        if np.any(np.diff(self.starts) < 0):
            raise ValueError("starts は昇順である必要がある（時系列順）")

    def split(self, n_samples: int | None = None) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        """(train_idx, test_idx) を fold ごとに yield。

        - test fold = サンプル index の連続ブロック（時系列順を保つ）
        - train から purge（テスト窓と重なるラベル）+ embargo（テスト直後）を除去
        - test 集合からは何も除去しない（test は完全分割を保つ）
        """
        n = len(self.starts)
        if n_samples is not None and n_samples != n:
            raise ValueError(f"n_samples({n_samples}) != starts 長({n})")
        all_idx = np.arange(n)
        for test_idx in np.array_split(all_idx, self.n_splits):
            test_lo_bar = int(self.starts[test_idx].min())   # テスト窓の最早 bar
            test_hi_bar = int(self.ends[test_idx].max())      # テスト窓の最遅 bar
            embargo_hi = test_hi_bar + self.embargo_bars

            train_mask = np.ones(n, dtype=bool)
            train_mask[test_idx] = False
            # purge: ラベル窓 [s,e] がテスト窓 [test_lo, test_hi] と重なる train を除去
            overlap = (self.starts <= test_hi_bar) & (self.ends >= test_lo_bar)
            train_mask &= ~overlap
            # embargo: テスト窓直後 (test_hi, test_hi+embargo] に始まる train を除去
            if self.embargo_bars > 0:
                emb = (self.starts > test_hi_bar) & (self.starts <= embargo_hi)
                train_mask &= ~emb

            yield all_idx[train_mask], test_idx


def count_label_overlap_with_test(train_idx: np.ndarray, test_idx: np.ndarray,
                                  starts: np.ndarray, ends: np.ndarray) -> int:
    """train のうち、ラベル窓がテスト窓と重なるサンプル数（= リーク経路の本数）。

    purge が効いていれば 0。普通の KFold（purge なし）では > 0。
    """
    test_lo = int(starts[test_idx].min())
    test_hi = int(ends[test_idx].max())
    s, e = starts[train_idx], ends[train_idx]
    overlap = (s <= test_hi) & (e >= test_lo)
    return int(np.sum(overlap))


def naive_kfold_split(n_samples: int, n_splits: int) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """purge/embargo なしの素朴な時系列連続 KFold（比較用ベースライン）。"""
    all_idx = np.arange(n_samples)
    for test_idx in np.array_split(all_idx, n_splits):
        train_idx = np.setdiff1d(all_idx, test_idx, assume_unique=True)
        yield train_idx, test_idx
