"""C3-a＝分位をまとめて計算しても、1段ずつと同じ値になるかを測る（監査 cp35）。"""
import numpy as np

grid = ["q10", "q20", "q30", "q40", "q50", "q60", "q70", "q80", "q90"]
ps = [int(q.lstrip("q")) / 100.0 for q in grid]
rng = np.random.default_rng(0)
worst = 0.0
for n in (7, 100, 1001, 50000):
    for kind in ("正規", "偏り", "同じ値ばかり", "とても小さい値"):
        if kind == "正規":
            s = rng.normal(size=n)
        elif kind == "偏り":
            s = rng.pareto(1.5, size=n) * 1e6
        elif kind == "同じ値ばかり":
            s = np.concatenate([np.zeros(n - 1), [1.0]])
        else:
            s = rng.normal(size=n) * 1e-12
        one = np.array([float(np.quantile(s, p)) for p in ps])
        many = np.asarray(np.quantile(s, ps), float)
        d = float(np.max(np.abs(one - many)))
        rel = d / max(1.0, float(np.max(np.abs(one))))
        worst = max(worst, d)
        print(f"n={n:>6} {kind:<12} 最大の差={d:.3e}  相対={rel:.3e}  完全一致={np.array_equal(one, many)}")
print()
print(f"いちばん大きかった差 = {worst:.3e} ／ 完成の条件の線 1e-12 を超えたか = {worst > 1e-12}")
