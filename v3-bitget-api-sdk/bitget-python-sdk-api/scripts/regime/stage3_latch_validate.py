"""stage3_latch_validate.py — 段階3 (3-1) latch 後処理付き再検証

設計原則 (2026-05-10 確定・段階3 検証不合格対応 第 1 手):
  - stage3_validate_judgment_set.py の前段（per-bar 構築 / 二値化 / 発火マスク /
    vote / 衝突解決）を import 再利用
  - latch 後処理を追加:
    - C-1 N=24 固定 (2h・合格基準整合)
    - C-2 同パターン新発火で延長リセット
    - C-3 異パターン発火時は乖離 pt 比較で切替判定
  - 5 ケース並走維持 (OR / vote2 / vote3 / vote4 / AND)
  - 合格基準 4 項目評価 (24 サンプル / 2025 年 / 持続安定性 / 月別 csv)

実行: python3 stage3_latch_validate.py
出力: results/regime_label_analysis/stage3_latch_validation_report.md +
      results/regime_label_analysis/stage3_latch_monthly_comparison.csv
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import pandas as pd
import numpy as np

from analyze_transition_indicators import load_labels
from analyze_stage1b_meta import resample_ohlcv

# stage3 既存関数を再利用 (DRY)
from stage3_validate_judgment_set import (
    load_final_judgment_set, collect_required_cols,
    build_per_bar_for_required_cols, binarize_per_5m,
    build_judgment_fire_masks, vote_per_pattern,
    evaluate_persistence, evaluate_24_samples, evaluate_2025_match,
    PATTERNS, VOTE_CASES, PERSISTENCE_TARGET_BARS,
    DATA_5M, OUT_DIR,
)

OUT_MD = OUT_DIR / "stage3_latch_validation_report.md"
OUT_MONTHLY = OUT_DIR / "stage3_latch_monthly_comparison.csv"

LATCH_BARS = 24  # C-1: 2h = 5m × 24


# ── パターン別平均乖離 pt 計算 (latch 切替判定用) ──

def compute_pattern_avg_diverg(final_set):
    """各パターンの最終 M=5 判定式の平均乖離 pt。"""
    out = {}
    for ptn in PATTERNS:
        if final_set.get(ptn):
            divergs = [j["fold_avg_diverg_pt"] for j in final_set[ptn]]
            out[ptn] = float(np.mean(divergs))
        else:
            out[ptn] = -np.inf
    return out


# ── 衝突解決 (stage3 と同じロジックを inline 再実装) ──

def resolve_conflicts_inline(pattern_fires, pattern_avg_diverg, n_5m):
    """各 5m バーで複数パターン発火時、平均乖離 pt 最大のパターン採用。"""
    out = np.full(n_5m, "none", dtype=object)
    sorted_patterns = sorted(PATTERNS, key=lambda p: -pattern_avg_diverg[p])
    for ptn in sorted_patterns:
        mask = pattern_fires[ptn] & (out == "none")
        out[mask] = ptn
    return out


# ── latch 後処理 (本ファイル新規) ──────────

def apply_latch(pattern_label, pattern_avg_diverg, n_latch=LATCH_BARS):
    """latch 後処理:
    - 発火 (none 以外) → N バー保持
    - 同パターン新発火 → 延長リセット (新発火時刻から N バー再カウント)
    - 異パターン発火 → 乖離 pt 比較
        新パターン乖離 pt > 既存 latch パターン乖離 pt → 切替 + リセット
        否則 → latch 維持
    """
    n = len(pattern_label)
    out = np.full(n, "none", dtype=object)
    active_latch = None
    latch_until = -1
    latch_diverg_pt = -np.inf

    for i in range(n):
        current = pattern_label[i]

        if current != "none":
            if active_latch is None:
                # 初回 latch
                active_latch = current
                latch_until = i + n_latch
                latch_diverg_pt = pattern_avg_diverg.get(current, 0.0)
                out[i] = active_latch
            elif current == active_latch:
                # 同パターン → 延長リセット
                latch_until = i + n_latch
                out[i] = active_latch
            else:
                # 異パターン → 乖離 pt 比較
                new_diverg = pattern_avg_diverg.get(current, 0.0)
                if new_diverg > latch_diverg_pt:
                    # 切替
                    active_latch = current
                    latch_until = i + n_latch
                    latch_diverg_pt = new_diverg
                out[i] = active_latch  # 切替済 or 既存維持
        else:
            # 発火なし
            if active_latch is not None and i <= latch_until:
                out[i] = active_latch
            else:
                # latch 期間終了
                active_latch = None
                latch_until = -1
                latch_diverg_pt = -np.inf
    return out


# ── 5 ケース並走 csv (latch 後) ──────────

def write_latch_monthly_csv(pattern_labels_by_case, df5m_index, out_path):
    """latch 適用後の 5 ケース並走 csv 出力。"""
    df = pd.DataFrame({"timestamp": df5m_index})
    for thr, name in VOTE_CASES:
        df[f"{name}_latched"] = pattern_labels_by_case[name]
    df["month"] = df["timestamp"].dt.to_period("M").astype(str)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)


# ── md 出力 (latch 状況も記録) ──────────

def write_latch_report(persistence_by_case, hits_24_by_case, match_2025_by_case,
                        latch_stats_by_case, out_path):
    lines = ["# 段階3 (3-1) latch 後処理付き 検証レポート", ""]
    lines.append(f"作成日: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"latch 設定: N={LATCH_BARS} バー (2h)")
    lines.append("仕様: 同パターン新発火で延長リセット / 異パターン発火は乖離 pt 比較切替")
    lines.append("")

    lines.append("## ケース別 合格基準サマリ (latch 後)")
    lines.append("| ケース | 24 サンプルヒット | 2025 年一致率 | 持続発火件数 | 持続中央値平均 |")
    lines.append("|---|---|---|---:|---:|")
    for thr, name in VOTE_CASES:
        h = hits_24_by_case.get(name, {})
        m = match_2025_by_case.get(name, {})
        p = persistence_by_case.get(name, {})
        h_str = (f"{h.get('hits', 0)}/{h.get('total', 0)} ({h.get('hit_rate', 0)*100:.1f}%)"
                 if h.get("hit_rate") is not None else h.get("note", "?"))
        m_str = (f"{m.get('match_rate', 0)*100:.1f}% ({m.get('matches', 0)}/{m.get('total', 0)})"
                 if m.get("match_rate") is not None else m.get("note", "?"))
        n_runs_total = sum(v["n_runs"] for v in p.values())
        median_avg = float(np.mean([v["median_bars"] for v in p.values()])) if p else 0
        lines.append(f"| {name} | {h_str} | {m_str} | {n_runs_total} | {median_avg:.1f} |")
    lines.append("")

    lines.append("## latch 後処理 統計")
    lines.append("| ケース | 元発火件数 | latch 後件数 | 圧縮率 | 切替発生件数 |")
    lines.append("|---|---:|---:|---:|---:|")
    for thr, name in VOTE_CASES:
        s = latch_stats_by_case.get(name, {})
        ratio = s.get("after", 0) / s.get("before", 1) if s.get("before") else 0
        lines.append(f"| {name} | {s.get('before', 0)} | {s.get('after', 0)} | {ratio*100:.1f}% | {s.get('switches', 0)} |")
    lines.append("")

    lines.append(f"## ケース × パターン別 持続安定性 (latch 後・目標 {PERSISTENCE_TARGET_BARS} バー)")
    for thr, name in VOTE_CASES:
        p = persistence_by_case.get(name, {})
        if not p:
            continue
        lines.append(f"\n### {name}")
        lines.append("| パターン | 発火件数 | 中央値 (バー) | 平均 | 最大 | 目標達成 |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for ptn in PATTERNS:
            v = p.get(ptn, {})
            lines.append(f"| {ptn} | {v.get('n_runs', 0)} | {v.get('median_bars', 0):.1f} | "
                         f"{v.get('mean_bars', 0):.1f} | {v.get('max_bars', 0)} | {v.get('ge_target', 0)} |")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


def compute_latch_stats(pattern_label_pre, pattern_label_post):
    """latch 前後の統計 (発火件数・切替件数)。"""
    before = int((pattern_label_pre != "none").sum())
    after = int((pattern_label_post != "none").sum())
    switches = 0
    prev_active = "none"
    for i in range(len(pattern_label_post)):
        cur = pattern_label_post[i]
        if cur != "none" and cur != prev_active and prev_active != "none":
            switches += 1
        if cur != "none":
            prev_active = cur
    return {"before": before, "after": after, "switches": switches}


# ── メイン ─────────────────────────────

def main():
    print("入力ロード...", flush=True)
    final_set = load_final_judgment_set()
    labels_4h = load_labels()
    df5m = pd.read_csv(DATA_5M, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    df_per_tf = {
        "5m": df5m,
        "15m": resample_ohlcv(df5m, "15min"),
        "30m": resample_ohlcv(df5m, "30min"),
        "1h": resample_ohlcv(df5m, "1h"),
        "4h": resample_ohlcv(df5m, "4h"),
        "1d": resample_ohlcv(df5m, "1D"),
    }

    print("必要カラム抽出 + per-bar 5m 構築 + ffill...", flush=True)
    required_cols = collect_required_cols(final_set)
    print(f"  抽出: {len(required_cols)} 列", flush=True)
    per_bar_5m = build_per_bar_for_required_cols(required_cols, df_per_tf)

    print("二値化 + 判定式 30 件 発火マスク...", flush=True)
    binarized = binarize_per_5m(per_bar_5m)
    n_5m = len(df5m)
    judgment_masks = build_judgment_fire_masks(final_set, binarized, n_5m)

    pattern_avg_diverg = compute_pattern_avg_diverg(final_set)
    print(f"  パターン別平均乖離 pt: {pattern_avg_diverg}", flush=True)

    print("ケース別評価 + latch 適用...", flush=True)
    persistence_by_case = {}
    hits_24_by_case = {}
    match_2025_by_case = {}
    pattern_labels_by_case = {}
    latch_stats_by_case = {}

    for vote_thr, name in VOTE_CASES:
        print(f"  ケース {name} (vote >= {vote_thr})...", flush=True)
        pattern_fires = vote_per_pattern(judgment_masks, vote_thr, n_5m)
        pattern_label_pre = resolve_conflicts_inline(pattern_fires, pattern_avg_diverg, n_5m)
        pattern_label_post = apply_latch(pattern_label_pre, pattern_avg_diverg)

        pattern_labels_by_case[name] = pattern_label_post
        latch_stats_by_case[name] = compute_latch_stats(pattern_label_pre, pattern_label_post)
        persistence_by_case[name] = evaluate_persistence(pattern_label_post)
        hits_24_by_case[name] = evaluate_24_samples(pattern_label_post, df5m.index)
        match_2025_by_case[name] = evaluate_2025_match(pattern_label_post, df5m.index, labels_4h)

    print(f"5 ケース並走 csv (latch 後) 出力: {OUT_MONTHLY}", flush=True)
    write_latch_monthly_csv(pattern_labels_by_case, df5m.index, OUT_MONTHLY)

    print(f"レポート出力: {OUT_MD}", flush=True)
    write_latch_report(persistence_by_case, hits_24_by_case, match_2025_by_case,
                       latch_stats_by_case, OUT_MD)
    print("DONE")


if __name__ == "__main__":
    main()
