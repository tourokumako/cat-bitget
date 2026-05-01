"""V字頂点検出設計のためのサンプル抽出（ステップ1）

events.parquet から 2024-01 以降の代表的な急騰急落イベントを上下各12件抽出。

filter:
  - half_retrace_time が peak から ≤12h（純粋スパイク寄り）
  - |magnitude_pct| ≥ 3%（明確な振幅）
  - cluster 代表（同一 cluster_id 内で最大規模）

サンプル: up12 / down12 を年代均等（2024 ×8 / 2025 ×8 / 2026 ×8 = 24件）

出力:
  results/vshape_design/samples_24.parquet — 24件のメタデータ
  results/vshape_design/samples_24.md      — 人間確認用サマリ表
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
SRC = BASE / "results/spike_analysis_from202301/events.parquet"
OUT_DIR = BASE / "results/vshape_design"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HALF_MAX_HOURS = 12.0
MIN_MAGNITUDE = 0.03   # 3%
PER_DIRECTION = 12     # up12 / down12
YEARS_PER_SIDE = {2024: 4, 2025: 4, 2026: 4}  # 12件 = 4+4+4

print(f"=== V字頂点検出 サンプル選定 ===")
print(f"src: {SRC}")
ev = pd.read_parquet(SRC)
print(f"  raw events: {len(ev)}")

# half到達フィルタ
ev = ev[ev["half_retrace_time"].notna()].copy()
ev["hours_to_half"] = (ev["half_retrace_time"] - ev["peak_time"]).dt.total_seconds() / 3600.0
ev = ev[ev["hours_to_half"] <= HALF_MAX_HOURS].copy()
print(f"  after half<={HALF_MAX_HOURS}h: {len(ev)}")

# magnitude フィルタ
ev = ev[ev["magnitude_pct"].abs() >= MIN_MAGNITUDE].copy()
print(f"  after |mag|>={MIN_MAGNITUDE*100}%: {len(ev)}")

# 2024-01 以降
ev = ev[ev["peak_time"] >= pd.Timestamp("2024-01-01")].copy()
print(f"  after >=2024-01: {len(ev)}")

# cluster 代表（同一 cluster_id × direction で |magnitude| 最大の1件）
ev["abs_mag"] = ev["magnitude_pct"].abs()
ev = ev.sort_values(["cluster_id", "direction", "abs_mag"], ascending=[True, True, False])
ev = ev.drop_duplicates(subset=["cluster_id", "direction"], keep="first")
print(f"  after cluster dedupe: {len(ev)}")

# year 列
ev["year"] = ev["peak_time"].dt.year

# up/down に分け、年代均等に上位 |magnitude| でサンプル
def sample_balanced(df, per_year):
    parts = []
    for year, n in per_year.items():
        sub = df[df["year"] == year].sort_values("abs_mag", ascending=False).head(n)
        parts.append(sub)
        print(f"    {year}: 候補 {(df['year']==year).sum()} → 採用 {len(sub)}")
    return pd.concat(parts, ignore_index=True)

print(f"\n  up direction:")
up = sample_balanced(ev[ev["direction"] == "up"], YEARS_PER_SIDE)
print(f"  down direction:")
dn = sample_balanced(ev[ev["direction"] == "down"], YEARS_PER_SIDE)

samples = pd.concat([up, dn], ignore_index=True).sort_values("peak_time").reset_index(drop=True)
samples["sample_id"] = [f"V{i+1:02d}" for i in range(len(samples))]
print(f"\n  最終サンプル数: {len(samples)} (up={len(up)} / down={len(dn)})")

# 出力
out_cols = ["sample_id", "direction", "year", "peak_time", "start_time",
            "start_price", "peak_price", "magnitude_pct", "hours_to_half",
            "retrace_24h", "max_retrace_pct", "cluster_id"]
samples_out = samples[out_cols].copy()
samples_out.to_parquet(OUT_DIR / "samples_24.parquet")
print(f"  → {OUT_DIR / 'samples_24.parquet'}")

# md レポート
md = ["# V字頂点検出 サンプル24件（2024-01 以降）", ""]
md.append(f"- filter: half到達≤{HALF_MAX_HOURS}h / |mag|≥{MIN_MAGNITUDE*100}% / cluster代表")
md.append(f"- 上下各 {PER_DIRECTION} 件・年代均等（{YEARS_PER_SIDE}）")
md.append("")
md.append("| ID | dir | year | peak_time | mag% | hrs→half | start→peak価格 |")
md.append("|----|-----|------|-----------|------|---------|----------------|")
for _, r in samples_out.iterrows():
    md.append(
        f"| {r['sample_id']} | {r['direction']} | {int(r['year'])} | "
        f"{r['peak_time']} | {r['magnitude_pct']*100:+.2f}% | {r['hours_to_half']:.1f}h | "
        f"{r['start_price']:.0f}→{r['peak_price']:.0f} |"
    )
(OUT_DIR / "samples_24.md").write_text("\n".join(md) + "\n")
print(f"  → {OUT_DIR / 'samples_24.md'}")

print("\n完了。samples_24.md でまこさん肉眼確認 → ステップ2 指標集計へ。")
