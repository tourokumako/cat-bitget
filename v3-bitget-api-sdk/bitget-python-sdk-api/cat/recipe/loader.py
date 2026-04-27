"""recipes.yaml → Recipe オブジェクトへ変換"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class IndicatorSpec:
    tf: str
    name: str
    period: int | None = None
    lookback: int | None = None
    extra: dict = field(default_factory=dict)

    @property
    def key(self) -> str:
        """precompute panel と threshold dict の共通キー（例: ma_slope_70_d_5 / adx_14_1h / human_label_m_dom）"""
        parts = [self.name]
        if self.period is not None:
            parts.append(str(self.period))
        parts.append(self.tf.lower().replace("_", ""))
        if self.lookback is not None:
            parts.append(str(self.lookback))
        return "_".join(parts)


@dataclass
class Recipe:
    id: str
    label: str
    timeframes: list[str]
    indicators: list[IndicatorSpec]
    aggregation_intra: str
    aggregation_cross: str | None
    threshold_default: dict[str, float]
    threshold_grid: dict[str, list[float]]

    def indicators_by_tf(self) -> dict[str, list[IndicatorSpec]]:
        out: dict[str, list[IndicatorSpec]] = {}
        for ind in self.indicators:
            out.setdefault(ind.tf, []).append(ind)
        return out


def load_recipes(yaml_path: Path | str, filter_id: str | None = None) -> list[Recipe]:
    with Path(yaml_path).open() as f:
        raw = yaml.safe_load(f)

    out: list[Recipe] = []
    for r in raw["recipes"]:
        if filter_id and r["id"] != filter_id:
            continue
        indicators = [
            IndicatorSpec(
                tf=i["tf"],
                name=i["name"],
                period=i.get("period"),
                lookback=i.get("lookback"),
                extra={k: v for k, v in i.items() if k not in {"tf", "name", "period", "lookback"}},
            )
            for i in r["indicators"]
        ]
        out.append(
            Recipe(
                id=r["id"],
                label=r["label"],
                timeframes=[str(t) for t in r["timeframes"]],
                indicators=indicators,
                aggregation_intra=r["aggregation"]["intra"],
                aggregation_cross=r["aggregation"].get("cross"),
                threshold_default=dict(r.get("threshold_default", {})),
                threshold_grid=dict(r.get("threshold_grid", {})),
            )
        )
    return out


def collect_needed_timeframes(recipes: list[Recipe]) -> set[str]:
    out: set[str] = set()
    for r in recipes:
        out.update(r.timeframes)
    return out
