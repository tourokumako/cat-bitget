#!/usr/bin/env python3
"""tuner_adapters — 戦略ごとの接続ファイル（engine_tuner が読む・要件 R4・まこさん承認 2026-07-27）

1戦略＝1ファイル。探索器 engine_tuner.py は本ディレクトリのモジュールだけを見て、
戦略の中身（値をどこで差し替えるか）を知らない。戦略を1つ足すときは ここに1枚足すだけで
探索器は書き換えない＝これが要件 R4 の受け入れ条件そのもの。

なぜ要るか（実測・2026-07-27）: 3戦略とも「データを渡して売買記録を返す関数」を持つが、
値の渡し方が3通りに分かれる。E37 はコードの中の定数を書き換えてから呼ぶ。E38 は関数の引数で渡す。
E36 は関数のキーワード引数で、細かい値は実行時のフラグで切り替える。
共通するのは「データを渡す」と「売買記録が返る」の2点だけ。だから差し替え方を接続ファイルへ閉じ込める。

接続ファイルが持つもの（揃っていないと engine_tuner が実行前に止める）:
  NAME            … 戦略の名前（--strategy に渡す文字列）
  LABEL           … 人が読む説明
  logics()        … 扱えるロジックの一覧（id / side / label / searchable / why）
  space(id)       … 探索する値の宣言（type=float/cat/quantile）
  exit_keys()     … 出口側のキーの集合（探索器が入口と出口へ振り分けるのに使う）
  series_bank(df) … quantile 型の宣言が参照する分布（値決め窓の中だけ）
  fixed(id, names)… 設定ファイルの確定値（探索対象でないもの・毎試行に混ぜる）
  min_per_day(id) … 件数の下限（無ければ None）
  load_windows()  … 窓ごとの指標つきデータを作る（生データの読み込みは1回だけ）
  run()           … 値を1組受け取って売買記録を返す
任意:
  TYPE_COL / TYPE_VALUES … 型別に分けて見る列と値（無ければ型別の内訳を出さない）
"""
from __future__ import annotations

import importlib
import pathlib

# 接続ファイルに必ず在るもの（1つでも欠けたら実行前に止める＝形骸の接続ファイルを走らせない）
REQUIRED = ("NAME", "LABEL", "logics", "space", "exit_keys", "series_bank",
            "fixed", "min_per_day", "load_windows", "run")


def available() -> list[str]:
    """在る接続ファイルの名前。"""
    d = pathlib.Path(__file__).resolve().parent
    return sorted(p.stem for p in d.glob("*.py") if p.stem != "__init__")


def load_adapter(name: str):
    """名前で接続ファイルを読み込み、必要なものが揃っているか検査する。"""
    try:
        mod = importlib.import_module(f"{__name__}.{name}")
    except ModuleNotFoundError as e:
        raise SystemExit(f"[エラー] 接続ファイルが無い: {name}"
                         f"（在るのは {', '.join(available())}／詳細 {e}）")
    miss = [k for k in REQUIRED if not hasattr(mod, k)]
    if miss:
        raise SystemExit(f"[エラー] 接続ファイル {name} に足りないものがある: {miss}"
                         f"（tuner_adapters/__init__.py の REQUIRED が正本）")
    if mod.NAME != name:
        raise SystemExit(f"[エラー] 接続ファイル {name} の NAME が食い違う: {mod.NAME}")
    return mod
