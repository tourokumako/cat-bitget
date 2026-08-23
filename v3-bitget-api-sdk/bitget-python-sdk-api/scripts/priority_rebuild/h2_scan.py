#!/usr/bin/env python3
"""h2_scan.py — 未来参照の「書き方」を探す探し方の正本（hook）を読み込む、小さい共有モジュール。

2026-08-23（54回目・77番・まこさん承認 eb6f38734142e25c…）に新設。

■ なぜ要るか
  未来参照の書き方（shift にマイナス・rolling の center=True）を探す正規表現と、説明の文章
  （コメント・docstring）を外してから見る処理は、hook `.claude/hooks/require_leak_annotation.py`
  の `find_bad` が正本。これを書き写すと、hook だけ直したときに写しが黙ってずれる
  （2026-08-21 に `leak_causality_diag` で実際に起きた＝41番。2026-08-23 に `observe_diag` の
  検査4 でも同じ型が見つかった＝77番＝docstring の語に反応して ❌ を出していた）。
  ＝探し方を持つ場所を hook の1か所にし、使う側（leak_causality_diag・observe_diag の検査4）は
  このモジュールを通して呼ぶ。写しを持たない。

■ 読み取り専用
  ファイルを書かない。売買も採点もしない。

■ fail-closed
  hook のファイルが見つからない・関数が無い → SystemExit で止まる（正本が無いまま「0件」と出さない）。
"""
from __future__ import annotations
import importlib.util
import pathlib

HERE = pathlib.Path(__file__).resolve()
HOOK_REL = pathlib.Path(".claude") / "hooks" / "require_leak_annotation.py"


def _load_scanner():
    # ★階層の数を書かない＝上へ辿って探す（数え間違いで黙って別の場所を指すのを防ぐ）
    p = None
    for up in [HERE] + list(HERE.parents):
        cand = up / HOOK_REL
        if cand.exists():
            p = cand
            break
    if p is None:
        raise SystemExit(f"[h2_scan] 探し方の正本（{HOOK_REL}）が {HERE} から上に見つからない"
                         "（hook と同じ探し方でなければ、この検査は検査になりません）")
    spec = importlib.util.spec_from_file_location("require_leak_annotation_scanner", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for need in ("find_bad", "PAT"):
        if not hasattr(mod, need):
            raise SystemExit(f"[h2_scan] 探し方の正本に {need} が無い: {p}")
    return mod


_SCANNER = _load_scanner()
PAT = _SCANNER.PAT            # 表示のためだけに持つ（判定は find_bad が行う）
SOURCE = _SCANNER.__file__    # どの正本を読んだか（出力に印字できるように）


def scan_text(text: str) -> list[tuple[int, str]]:
    """ファイルの全文を見て、注記（# H2OK）なしの未来参照の行を (行番号, 行) で返す。

    ★1行ずつでなく全文を渡す＝説明の文章（docstring）は複数行にまたがるので、1行だけ見ても
      「いま文字列の中か」が分からない。判定は hook の find_bad がする（写しを持たない）。
    """
    return _SCANNER.find_bad(text)


def scan_line(line: str) -> bool:
    """1行が「注記なしの未来参照」か。"""
    return bool(_SCANNER.find_bad(line + "\n"))
