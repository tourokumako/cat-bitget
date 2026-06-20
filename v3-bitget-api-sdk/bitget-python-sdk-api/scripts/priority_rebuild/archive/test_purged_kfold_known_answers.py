#!/usr/bin/env python3
"""
test_purged_kfold_known_answers.py — purged_kfold.py 項目D の既知答えテスト D1-D5

位置づけ:
  ml_pipeline_baseline_v1.md §6「評価基盤 詳細設計 D」の既知答えテスト。
  答えが数学的に分かりきった問題で計器の正しさを証明（L-242）。

既知答え（baseline §6 D・AFML Ch.7）:
  D1 purge 後、全 fold で train のラベル窓が test 窓と重ならない（重なり数 = 0）
  D2 embargo 後、test 直後 (test_hi, test_hi+E] に始まる train は 0 件
  D3 全 fold で「test より前の train」のラベル終端 < test 開始（train末 < test始）
  D4 test 集合は全サンプルの完全分割（purge/embargo は train のみ削る・test は不変）
  D5 リーク注入（重なりで隣接ラベル相関）→ purge ありは CV 精度が低下（過大評価剥がれ）

実行:
  $SDK/.venv311/bin/python3 scripts/priority_rebuild/test_purged_kfold_known_answers.py
"""

from __future__ import annotations

import sys

import numpy as np

from purged_kfold import (
    PurgedKFold, count_label_overlap_with_test, naive_kfold_split,
)

_results: list[tuple[str, bool, str]] = []


def _check(name: str, cond: bool, detail: str) -> None:
    _results.append((name, cond, detail))
    print(f"  {'✅ PASS' if cond else '❌ FAIL'}  {name}: {detail}")


def _spans(n: int, K: int) -> tuple[np.ndarray, np.ndarray]:
    """連続する n サンプル・各ラベル窓長 K（隣接は重なる）。"""
    starts = np.arange(n, dtype=np.int64)
    ends = np.minimum(starts + K, n + K)  # clip しないで重なりを残す（bar 全長 = n+K 想定）
    return starts, ends


# ── D1: purge 後、全 fold で重なり 0 ────────────────────────────────────────
def test_d1_purge_no_overlap() -> None:
    n, K = 200, 20
    starts, ends = _spans(n, K)
    pk = PurgedKFold(n_splits=5, starts=starts, ends=ends, embargo_bars=0)
    max_overlap = 0
    for tr, te in pk.split(n):
        max_overlap = max(max_overlap, count_label_overlap_with_test(tr, te, starts, ends))
    _check("D1 purge 後 全fold で train×test ラベル重なり = 0",
           max_overlap == 0, f"全fold 最大重なり数={max_overlap}（期待 0）")


# ── D1-ref: 素朴 KFold だと重なり > 0（リークが存在する対照）────────────────
def test_d1_naive_has_overlap() -> None:
    n, K = 200, 20
    starts, ends = _spans(n, K)
    total_overlap = 0
    for tr, te in naive_kfold_split(n, 5):
        total_overlap += count_label_overlap_with_test(tr, te, starts, ends)
    _check("D1-ref 素朴 KFold は重なり > 0（リーク経路あり）",
           total_overlap > 0, f"素朴 KFold 重なり合計={total_overlap}（purge で 0 に消える）")


# ── D2: embargo 後、test 直後の train が 0 件 ───────────────────────────────
def test_d2_embargo() -> None:
    n, K, E = 200, 20, 10
    starts, ends = _spans(n, K)
    pk = PurgedKFold(n_splits=5, starts=starts, ends=ends, embargo_bars=E)
    viol = 0
    for tr, te in pk.split(n):
        test_hi = int(ends[te].max())
        in_embargo = (starts[tr] > test_hi) & (starts[tr] <= test_hi + E)
        viol += int(np.sum(in_embargo))
    _check("D2 embargo 後 test直後(E窓)の train = 0",
           viol == 0, f"embargo 窓内 train 残存={viol}（期待 0・E={E}bar）")


# ── D3: train末 < test始（test より前の train のラベル終端）──────────────────
def test_d3_train_end_before_test_start() -> None:
    n, K = 200, 20
    starts, ends = _spans(n, K)
    pk = PurgedKFold(n_splits=5, starts=starts, ends=ends, embargo_bars=0)
    ok = True
    detail = ""
    for fi, (tr, te) in enumerate(pk.split(n)):
        test_lo = int(starts[te].min())
        before = tr[starts[tr] < test_lo]  # test より前に始まる train
        if len(before) and int(ends[before].max()) >= test_lo:
            ok = False
            detail = f"fold{fi}: train末={int(ends[before].max())} >= test始={test_lo}"
            break
    _check("D3 全fold で train末 < test始（前方 train）",
           ok, detail or "全 fold で train のラベル終端 < test 開始 bar")


# ── D4: test は完全分割（purge/embargo は train のみ削る）────────────────────
def test_d4_test_full_partition() -> None:
    n, K = 200, 20
    starts, ends = _spans(n, K)
    pk = PurgedKFold(n_splits=5, starts=starts, ends=ends, embargo_bars=10)
    test_all = []
    disjoint = True
    seen = set()
    for tr, te in pk.split(n):
        if seen & set(te.tolist()):
            disjoint = False
        seen |= set(te.tolist())
        test_all.extend(te.tolist())
    full = sorted(test_all) == list(range(n))
    _check("D4 test 集合 = 全サンプルの完全分割（test は不変）",
           full and disjoint and len(test_all) == n,
           f"test 総数={len(test_all)}/{n} / 重複なし={disjoint} / 全網羅={full}")


# ── D5: リーク注入 → purge で CV 精度が低下（過大評価剥がれ）──────────────────
def test_d5_purge_drops_leaked_accuracy() -> None:
    """リーク注入の構成（全テスト点に効くよう設計）:
    - 特徴 X = 時刻インデックス → 1-NN は「時間的に最も近い train」を引く。
    - ラベル y = sign(z[i+K]-z[i])（z=ランダムウォーク）。窓が K 本重なるので
      y は run length ≈ K の持続（隣接が同じ値の塊）を持つ。
    - K(=60) > テストブロック幅(=50) にすると、全テスト点のラベル窓が train に食い込む。
    naive: テスト点の最近傍 train = ブロック境界の隣接サンプル → 同じ run → 高精度（リーク）。
    purge: 境界の隣接(±K)が train から消える → 最近傍は K 本以上離れ別 run → 精度がチャンス水準へ低下。"""
    from sklearn.neighbors import KNeighborsClassifier

    rng = np.random.default_rng(0)
    n_bars = 2000
    K = 60
    n_splits = 40  # テストブロック幅 ≈ (2000-60)/40 ≈ 48.5 < K=60 → 全テスト点が train と重なる
    z = np.cumsum(rng.normal(0, 1, n_bars))
    n = n_bars - K
    starts = np.arange(n, dtype=np.int64)
    ends = starts + K
    X = (starts / n).reshape(-1, 1).astype(np.float64)  # 時刻インデックス特徴
    y = (z[ends] > z[starts]).astype(int)

    def cv_acc(splitter) -> float:
        accs = []
        for tr, te in splitter:
            if len(tr) < 5 or len(te) < 5:
                continue
            clf = KNeighborsClassifier(n_neighbors=1)
            clf.fit(X[tr], y[tr])
            accs.append(float(np.mean(clf.predict(X[te]) == y[te])))
        return float(np.mean(accs))

    acc_naive = cv_acc(naive_kfold_split(n, n_splits))
    pk = PurgedKFold(n_splits=n_splits, starts=starts, ends=ends, embargo_bars=K)
    acc_purged = cv_acc(pk.split(n))

    # 既知答え: naive はリークで高精度 / purge で大きく低下し、チャンス(0.5)近傍へ
    ok = (acc_naive > acc_purged + 0.08) and (acc_purged < 0.70)
    _check("D5 リーク注入 → purge で CV 精度低下（過大評価剥がれ）",
           ok, f"naive acc={acc_naive:.3f} → purged acc={acc_purged:.3f}（差 {acc_naive - acc_purged:+.3f}）")


def main() -> int:
    print("=" * 60)
    print("purged_kfold.py 既知答えテスト D1-D5（計器の正しさ＝数学的事実）")
    print("=" * 60)
    print("\n[D1] purge 後 重なり 0 / 素朴 KFold は重なりあり")
    test_d1_purge_no_overlap()
    test_d1_naive_has_overlap()
    print("\n[D2] embargo 後 test 直後の train 0 件")
    test_d2_embargo()
    print("\n[D3] train末 < test始")
    test_d3_train_end_before_test_start()
    print("\n[D4] test は完全分割")
    test_d4_test_full_partition()
    print("\n[D5] リーク注入 → purge で CV 精度低下")
    test_d5_purge_drops_leaked_accuracy()

    n_pass = sum(1 for _, ok, _ in _results if ok)
    n_total = len(_results)
    print("\n" + "=" * 60)
    print(f"結果: {n_pass} / {n_total} pass")
    print("=" * 60)
    if n_pass == n_total:
        print("✅ 全 pass — 計器（Purged K-Fold + Embargo 項目D）は正しく測れている")
        return 0
    print("❌ FAIL あり:")
    for name, ok, detail in _results:
        if not ok:
            print(f"   - {name}: {detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
