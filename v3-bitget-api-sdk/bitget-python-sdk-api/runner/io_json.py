from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object(dict): {path}")
    return data


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    if not isinstance(obj, dict):
        raise ValueError("obj must be dict")
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    _atomic_write_text(path, text + "\n")


def state_path(*parts: str) -> Path:
    # runner/ 配下から見たプロジェクト直下 = bitget-python-sdk-api
    root = Path(__file__).resolve().parents[1]
    return root.joinpath("state", *parts)
