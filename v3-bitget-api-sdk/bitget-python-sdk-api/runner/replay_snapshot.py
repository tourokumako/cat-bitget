# runner/replay_snapshot.py
# 목적: Bitget APIを叩かずに snapshot(JSON) を入力として cat_live_decider を実行し、
#      DECISION と MAT_FIRED を JSON lines で出す（F1/F2の証跡採取用）
#
# 実行例（ワンショット）:
# python3 - <<'PY'
# import runner.replay_snapshot as r
# r.main(["--snapshot","state/market_snapshot.json","--params","config/cat_params.json","--tag","F1"])
# PY

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from typing import Any, Callable, Dict, List, Optional


def _log(event: str, payload: Optional[Dict[str, Any]] = None) -> None:
    obj: Dict[str, Any] = {"event": event}
    if payload:
        obj.update(payload)
    print(json.dumps(obj, ensure_ascii=False))


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _pick_decider_func(mod: Any) -> Callable[..., Dict[str, Any]]:
    """
    cat_live_decider 内の「判断関数」を実在コードに依存しすぎず選ぶ。
    優先順:
      1) strategy_decide
      2) decide
      3) decide_entry
    それ以外は、(snapshot, params) or (snapshot, params, tag=...) を受けそうな関数を探索。
    """
    preferred = ["strategy_decide", "decide", "decide_entry"]
    for name in preferred:
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn  # type: ignore[return-value]

    # fallback: 探索（関数だけ）
    cands: List[Callable[..., Any]] = []
    for name, obj in vars(mod).items():
        if callable(obj) and inspect.isfunction(obj):
            cands.append(obj)

    # snapshot/params を受け取れそうなものを優先
    for fn in cands:
        try:
            sig = inspect.signature(fn)
        except Exception:
            continue
        params = list(sig.parameters.values())
        if len(params) >= 2:
            return fn  # type: ignore[return-value]

    raise RuntimeError("No callable decider function found in strategies/cat_live_decider.py")


def _call_decider(fn: Callable[..., Dict[str, Any]], snapshot: Dict[str, Any], params: Dict[str, Any], tag: str) -> Dict[str, Any]:
    """
    関数シグネチャが環境で多少違っても動くように、呼び出しを段階的に試す。
    """
    # 1) (snapshot, params, tag=...)
    try:
        return fn(snapshot, params, tag=tag)  # type: ignore[misc]
    except TypeError:
        pass

    # 2) (snapshot, params)
    try:
        return fn(snapshot, params)  # type: ignore[misc]
    except TypeError:
        pass

    # 3) (snapshot,)
    try:
        return fn(snapshot)  # type: ignore[misc]
    except TypeError as e:
        raise RuntimeError(f"Decider call failed. fn={getattr(fn, '__name__', str(fn))}, err={e}") from e


def main(argv: Optional[List[str]] = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default="state/market_snapshot.json")
    ap.add_argument("--params", default="config/cat_params_v9.json")
    ap.add_argument("--tag", default="F1")
    ns = ap.parse_args(argv)

    # 実行位置に依存しないように cwd を前提にする（あなたの運用ルール通り）
    snapshot_path = ns.snapshot
    params_path = ns.params

    snap = _read_json(snapshot_path)
    params = _read_json(params_path)

    run_id = snap.get("run_id") or snap.get("RUN_ID") or ""
    _log("RUN_ID", {"run_id": run_id} if run_id else {"run_id": ""})

    # 既存ログと同様の補助情報（無ければ出さない）
    candle_last = snap.get("candle_last")
    if isinstance(candle_last, dict):
        _log("CANDLE_USED", {"candle_last": candle_last})
        ts = candle_last.get("ts")
        if ts is not None:
            _log("TARGET_TS", {"target_ts": ts})

    # gate系（snapshotに存在する場合だけ）
    gate_payload: Dict[str, Any] = {"tag": ns.tag}
    for k in ["entry_ok", "pos_count", "MAX_POSITIONS"]:
        if k in snap:
            gate_payload[k] = snap.get(k)
    if len(gate_payload) > 1:
        _log("GATE", gate_payload)

    mod = importlib.import_module("strategies.cat_live_decider")
    fn = _pick_decider_func(mod)
    out = _call_decider(fn, snap, params, ns.tag)

    # DECISION
    if not isinstance(out, dict):
        raise RuntimeError(f"Decider returned non-dict: {type(out)}")
    _log("DECISION", out)

    # MAT_FIRED（runnerと同じ監査観点）
    # F1では「発火（ENTER）」の証跡だけ欲しいので、ENTER以外はノイズとして出さない
    if out.get("action") == "ENTER":
        material = out.get("material")
        has_material = isinstance(material, dict) and len(material) > 0
        keys = sorted(list(material.keys())) if has_material else []
        ep = out.get("entry_priority", out.get("priority", 0))
        _log("MAT_FIRED", {"entry_priority": ep, "has_material": has_material, "material_keys": keys})

    _log("END", {"result": "REPLAY_DONE"})


if __name__ == "__main__":
    main()
