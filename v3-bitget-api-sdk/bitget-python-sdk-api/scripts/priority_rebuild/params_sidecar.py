#!/usr/bin/env python3
"""params_sidecar.py — 戦略が「実際に使ったパラメータ」を売買記録CSVの隣に書き出す汎用ヘルパー。

なぜ要るか:
  report.py は売買記録CSVだけを入力にするため、使用した指標・閾値・TP/SL/TimeExit を出せない
  （これらは戦略の定数＋CLIフラグで決まり CSV に載らない）。report.py がソースを推測すると
  CLIフラグ（--partial-tp 等）を取りこぼし誤表示になる。→ 戦略実行時に「実使用値」をここで
  <csv_stem>_params.json として記録し、report.py の節0 が読んで表示する（E35 専用でない・汎用）。

  業界の標準パターンと整合（2026-06-18 ベースアップ）:
    arxiv 2603.09219（IS-WFA-OOS）= 各走行で data version/seed/コスト前提/探索予算/パラメータロック/
      pass-fail を記録し戦略を完全再構成・第三者検証可能に。
    microsoft/qlib Recorder = run 単位で params/metrics/artifacts を記録（MLflow 実装）。

使い方（戦略側・E35/E36/E37 共通）:
  import params_sidecar as psc
  psc.write_sidecar(csv_path, strategy="...", script="...", experiment="iter7",
                    sections={"検証期間": {...}, "Entry": {...}, "Exit/TP/SL/TimeExit": {...}})
  ＝ <csv_stem>_params.json を書き出す（read 専用メタ・net 計算には一切関与しない＝審判に影響なし）。

JSON 形式（report.py が汎用に読む・戦略名で分岐しない）:
  {"strategy","script","experiment","run_args","note","sections":{ 節名: {キー: 値, ...}, ... }}
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


def sidecar_path(csv_path) -> Path:
    """売買記録CSV → そのサイドカーJSON パス（<stem>_params.json）。"""
    p = Path(csv_path)
    return p.with_name(f"{p.stem}_params.json")


def write_sidecar(csv_path, *, strategy: str, script: str, experiment: str = "",
                  run_args: str = "", sections=None) -> Path:
    """売買記録CSVの隣に使用パラメータJSONを書き出す。戻り値=書いたパス。

    run_args 省略時は sys.argv からコマンドライン引数を拾う。
    """
    out = sidecar_path(csv_path)
    payload = {
        "strategy": strategy,
        "script": script,
        "experiment": experiment,
        "run_args": run_args if run_args else " ".join(sys.argv[1:]),
        "note": "戦略実行時に記録した実使用パラメータ（report.py 節0 が表示）",
        "sections": sections or {},
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
