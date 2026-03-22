from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from runner.io_json import read_json, write_json, state_path

# bitget-python-sdk-api がプロジェクトルート（io_json.state_path と同じ基準）
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_STRATEGY_FILE = _PROJECT_ROOT / "strategies" / "cat_v9_decider.py"

# キャッシュ（毎回importし直さない）
_cached_mod: Optional[object] = None
_cached_path: Optional[Path] = None


def _load_external_strategy(path: Path) -> object:
    if not path.exists():
        raise FileNotFoundError(str(path))

    spec = importlib.util.spec_from_file_location("cat_strategy_external", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec load failed: {path}")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def _pick_decider(mod: object) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    外部CATのエントリポイント名が確定してないため、
    「よくある候補名」を順番に探索して、最初に見つかった callable を使う。
    見つからなければ例外。
    """
    candidates = [
        "decide",                 # 最優先：今回のstubと同名
        "decide_from_snapshot",   # 代替
        "make_decision",          # 代替
    ]
    for name in candidates:
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn  # type: ignore[return-value]
    raise AttributeError(f"no decision function found in external strategy: tried={candidates}")


def decide(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bitget SDK には触れない。
    snapshot(dict) -> decision(dict) の純粋関数として外部CATを呼ぶ。
    失敗時は STOP を返す（runner側で「異常STOPして追撃しない」ための材料）。
    """
    global _cached_mod, _cached_path

    try:
        # 外部戦略のファイルが差し替わった場合だけ再ロード
        if _cached_mod is None or _cached_path != _STRATEGY_FILE:
            _cached_mod = _load_external_strategy(_STRATEGY_FILE)
            _cached_path = _STRATEGY_FILE

        decider = _pick_decider(_cached_mod)
        out = decider(snapshot)

        if not isinstance(out, dict):
            raise TypeError("external strategy must return dict")

        # 最低限の必須キーだけチェック（なければ STOP）
        action = out.get("action")
        reason = out.get("reason")
        if action is None or reason is None:
            return {
                "action": "STOP",
                "reason": "strategy_invalid_output: missing action/reason",
                "strategy_file": str(_STRATEGY_FILE),
            }

        # 付帯情報（デバッグ用。大量出力はしない）
        out.setdefault("strategy_file", str(_STRATEGY_FILE))
        return out

    except Exception as e:
        return {
            "action": "STOP",
            "reason": f"strategy_load_or_run_failed: {type(e).__name__}: {e}",
            "strategy_file": str(_STRATEGY_FILE),
        }


def main() -> None:
    snap = read_json(state_path("market_snapshot.json"))
    dec = decide(snap)
    write_json(state_path("decision.json"), dec)


if __name__ == "__main__":
    main()
