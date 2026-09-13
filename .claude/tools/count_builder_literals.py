#!/usr/bin/env python3
"""count_builder_literals.py — 組む関数の範囲に、乱数と法則番号の直書きが残っていないかを数える。

設計書 m2e2-s22-verified-build-20260910 の完成の条件 #4（AUDIT-3）
  「組む関数に法則番号の直書きが0件、かつ乱数（rng・draw_param）が0件」を測る道具。

なぜ作るか（2026-09-13・97回目）
--------------------------------------------------------------------------
まこさん指示（逐語）＝「本来修正すべきものなので、このセッションでは修正する」
                      「了解。では修正してよい」（案1＝コードに法則番号の文字を書かない）。
直す前の条件のコマンド（`awk … | grep -cE 'rng|draw_param'`）には、問題が5つあった（実測）。
  ①`awk` で始まるので、承認のプログラム（`python3 `・`bash ` で始まるものだけを走らせる）が走らせない
  ②`grep -c` は0件のとき終了コード 1 を返す＝走らせても合否が逆
  ③説明の文とコメントも数えた＝5件（全部 説明の文）
  ④壊すプログラム b78 の数え方は、1行で閉じる説明の文で内と外の判定が逆になり、壊す前から2件
  ⑤条件の前半「法則番号の直書き」を数えていなかった
直し方の出どころ＝監査 cp35 の 3-3「数える対象を『コメントと文字列を外したコード』にしてください」
  （手本＝`gen_acceptance.py` の `build_random`＝構文の木で `rng` を数える）。

何をするか
--------------------------------------------------------------------------
  `engine_tuner_gen.py` を構文の木で読み、`def _ranked_material_at` から `def default_regime` の手前までの
  最上位の文（関数・代入）を相手にして、次の2つを数える。
    ①乱数＝名前 `rng`・`random`（使う所・受け取る引数・名前つき引数）、呼び出し `draw_param`・`draw_q`・
      `draw_int`・`draw_num`、属性 `random`・`default_rng`・`shuffle`・`choice`
    ②法則番号の直書き＝文字列の値そのものが、法則ファイル（regime_laws.json）の法則の番号と同じもの
  ★コメントは構文の木に入らないので数えない。★説明の文（関数・クラスの頭の文字列）は数えない。
  両方0件なら終了コード 0、1件でも在れば 1、読めないときは 2（fail-closed）。

使い方
--------------------------------------------------------------------------
  python3 .claude/tools/count_builder_literals.py

限界（正直に書く）
--------------------------------------------------------------------------
  ・数えるのは決めた名前だけ。別の名前に置き換えた乱数や、ほかのファイルの関数を通した乱数は数えない。
  ・法則番号は「文字列の値そのもの」だけ。文に混ぜた番号（例＝"R1 が系統を…"）や、組み立てた番号は数えない。
  ・段の役割を元データから読んでいるかは数えない（役割の名前は組む関数の外にも正しく在るため）。
  ・範囲の端は関数の名前で決める。どちらかの名前が消えたら止まる（黙って0件にしない）。
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SDK = ROOT / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
GEN = SDK / "scripts" / "priority_rebuild" / "engine_tuner_gen.py"
LAWS = SDK / ".claude" / "ratchet" / "regime_laws.json"

START = "_ranked_material_at"     # 範囲の始まり（この関数を含む）
END = "default_regime"            # 範囲の終わり（この関数を含まない）

RNG_NAMES = {"rng", "random"}
RNG_CALLS = {"draw_param", "draw_q", "draw_int", "draw_num"}     # 手本 gen_acceptance.build_random と同じ
RNG_ATTRS = {"random", "default_rng", "shuffle", "choice"}        # 監査 cp35 の 3-3 の2番


def law_numbers() -> set:
    """法則ファイルから法則の番号を読む（★番号の形を私が決めない＝ファイルに在る番号だけ）。"""
    if not LAWS.exists():
        raise SystemExit(f"[count_builder_literals] 法則ファイルが無い: {LAWS}（fail-closed）")
    d = json.loads(LAWS.read_text(encoding="utf-8"))
    nos = {str(x.get("番号")) for x in (d.get("法則") or []) if isinstance(x, dict) and x.get("番号")}
    if not nos:
        raise SystemExit("[count_builder_literals] 法則の番号を1件も読めない（fail-closed）")
    return nos


def target_nodes(tree: ast.Module) -> list:
    """範囲の最上位の文を返す。始まりか終わりの関数が見つからなければ止まる。"""
    names = [getattr(n, "name", None) for n in tree.body]
    if START not in names:
        raise SystemExit(f"[count_builder_literals] 範囲の始まりの関数が無い: {START}（fail-closed）")
    if END not in names:
        raise SystemExit(f"[count_builder_literals] 範囲の終わりの関数が無い: {END}（fail-closed）")
    i, j = names.index(START), names.index(END)
    if not i < j:
        raise SystemExit(f"[count_builder_literals] 範囲の並びが逆: {START}（{i}）→ {END}（{j}）（fail-closed）")
    return tree.body[i:j]


def docstring_ids(nodes: list) -> set:
    """説明の文（関数・クラスの頭の文字列）の節の id を集める（数えないため）。"""
    ids = set()
    for top in nodes:
        for n in ast.walk(top):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
                b0 = n.body[0]
                if isinstance(b0, ast.Expr) and isinstance(b0.value, ast.Constant) \
                        and isinstance(b0.value.value, str):
                    ids.add(id(b0.value))
    return ids


def count(text: str, laws: set) -> tuple[list, list]:
    """(乱数の見つかった所, 法則番号の見つかった所) を返す。各要素＝(行, 説明)。"""
    tree = ast.parse(text)
    nodes = target_nodes(tree)
    skip = docstring_ids(nodes)
    rng_hits: list = []
    law_hits: list = []
    for top in nodes:
        for n in ast.walk(top):
            ln = getattr(n, "lineno", 0)
            if isinstance(n, ast.Name) and n.id in RNG_NAMES:
                rng_hits.append((ln, f"名前 {n.id}"))
            elif isinstance(n, ast.arg) and n.arg in RNG_NAMES:
                rng_hits.append((ln, f"引数 {n.arg}"))
            elif isinstance(n, ast.keyword) and n.arg in RNG_NAMES:
                rng_hits.append((ln, f"名前つき引数 {n.arg}"))
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in RNG_CALLS:
                rng_hits.append((ln, f"呼び出し {n.func.id}"))
            elif isinstance(n, ast.Attribute) and n.attr in RNG_ATTRS:
                rng_hits.append((ln, f"属性 .{n.attr}"))
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in skip \
                    and n.value in laws:
                law_hits.append((ln, f"法則番号の文字 {n.value!r}"))
    return rng_hits, law_hits


def main() -> int:
    if not GEN.exists():
        print(f"[count_builder_literals] 数える相手が無い: {GEN}（fail-closed）")
        return 2
    try:
        laws = law_numbers()
        rng_hits, law_hits = count(GEN.read_text(encoding="utf-8"), laws)
    except SystemExit as e:
        print(str(e))
        return 2
    except SyntaxError as e:
        print(f"[count_builder_literals] 構文の木を作れない: {e}（fail-closed）")
        return 2
    print(f"[count_builder_literals] 範囲＝{START} 〜 {END} の手前 ／ 法則の番号 {len(laws)}件を照らした")
    print(f"  乱数＝{len(rng_hits)}件 ／ 法則番号の直書き＝{len(law_hits)}件"
          "（説明の文とコメントは数えない）")
    for ln, what in rng_hits + law_hits:
        print(f"    {GEN.name}:{ln}  {what}")
    if rng_hits or law_hits:
        print("  ❌ 0件ではない（完成の条件 #4 を満たしていない）")
        return 1
    print("  ✅ 両方 0件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
