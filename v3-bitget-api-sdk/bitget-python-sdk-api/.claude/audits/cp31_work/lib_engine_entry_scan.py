#!/usr/bin/env python3
# lib_engine_entry_scan.py — 「そのコマンドは engine の入口を使うか」を判定する部品
#   （2026-08-27・68回目・まこさん承認「了解、修正を進めていいよ」・設計書 iter=h2g2-entry-scan-20260827）
#
# 何のためにあるか
#   H2（未来参照なしの検査）と G2（案の審査の検査）の印が合わないうちは engine_tuner を走らせない、
#   という止めが2本ある（enforce_h2_pass.py / enforce_g2_pass.py）。
#   その2本は「コマンドの文字に4つのファイル名が在るか」だけで止める相手を決めていた。
#   ＝別の名前のプログラムを作り、その中から engine の部品を呼べば、印が古くても走った。
#
#   この部品は「走らせる .py が、engine の入口の関数を使うか」を中身で見る。
#   ＝ファイルの名前を変えても、engine を使うなら止まる。
#
# ★判定を1か所にまとめた理由
#   H2 と G2 は同じ判定を2か所に持っていた。同じ直しを書き写すと、片方だけ直る形になる
#   （2026-08-23 に next_step.md §6 の89番として記録した型）。だから2本がこの1本を呼ぶ。
#
# ★行き過ぎない線（実測 2026-08-27・worklog §33）
#   「engine の部品を import しているか」で止めると、文書を作る4本まで止まる。
#   H2 の印の対象21件には exit_families.json と signal_families.json が入っているので、
#   文書を作り直すと印が失効する＝「印が古いと文書を作れない」にすると堂々巡りになる。
#   だから import ではなく「engine の入口の関数を使うか」で決める。
#
# 限界（正直に書く）
#   ①入口の関数の名前6つは人が選んだ一覧。別の名前で engine を呼ぶ道があればすり抜ける。
#     番人は「6つが実物に在るか」しか見ない（「ほかに入口が無いか」は見ない）。
#   ②たどる深さは MAX_DEPTH まで。それより深く包むとすり抜ける。
#   ③走らせる .py の取り出しはコマンドの文字から行う。変数から組み立てて走らせるとすり抜ける。
#
# 番人: python3 .claude/hooks/lib_engine_entry_scan.py --selftest

from __future__ import annotations

import ast
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
_PR = os.path.join(SDK, "scripts", "priority_rebuild")

# engine の入口＝ここを呼ぶなら「engine を使っている」。
#   run_recipe            … 売買を回す
#   build_regime_columns  … 場面の判定の列を作る
#   sample_structure      … 案を組む
#   sample_regime_build   … 場面の判定の束を組む
#   score                 … 審判に通す（score.score / judge.score の呼び出し）
#   load_windows          … 窓の指標つきデータを読む（load_windows / load_windows_cached）
ENTRY_NAMES = (
    "run_recipe",
    "build_regime_columns",
    "sample_structure",
    "sample_regime_build",
    "score.score",
    "load_windows",
)

# ★上の6つが「本当に実物のコードに在るか」を確かめる相手（番人が毎回 数える）。
#   名前が変わったら番人が落ちる＝黙って効かなくなるのを防ぐ（手書きの一覧は腐る・L-468）。
ENTRY_HOME = {
    "run_recipe": os.path.join(_PR, "engine_tuner_exec.py"),
    "build_regime_columns": os.path.join(_PR, "engine_tuner_exec.py"),
    "sample_structure": os.path.join(_PR, "engine_tuner_gen.py"),
    "sample_regime_build": os.path.join(_PR, "engine_tuner_gen.py"),
    "score.score": os.path.join(_PR, "score.py"),
    "load_windows": os.path.join(_PR, "engine_tuner.py"),
}

MAX_DEPTH = 3                      # たどる深さ（限界②）
_PY_TOKEN = re.compile(r"[A-Za-z0-9_./\-]+\.py")

# ★engine そのもの＝ここへは たどらない（2026-08-27 の実測で直した）。
#   なぜ＝engine 本体は、自分の中で入口の関数を呼ぶ。たどってしまうと、
#   「engine を読み込んでいるだけ」の文書を作るプログラムまで当たる（実測＝P3 が落ちた）。
#   見たいのは「呼ぶ側が入口を呼んでいるか」なので、engine の中は見ない。
ENGINE_MODULES = {
    "engine_tuner", "engine_tuner_gen", "engine_tuner_exec",
    "e38_priority_stack", "e38_logic_parts", "score", "eval_engine",
}


def _resolve(rel: str) -> str | None:
    """コマンドに出てきた .py の文字を、実在するファイルの道に直す（2か所を探す）。"""
    r = rel.strip("'\"`")
    for base in (ROOT, SDK, _PR, os.path.join(SDK, "scripts", "dashboard")):
        p = os.path.join(base, r)
        if os.path.isfile(p):
            return os.path.realpath(p)
    if os.path.isabs(r) and os.path.isfile(r):
        return os.path.realpath(r)
    return None


def scripts_in_segment(seg: str) -> list[str]:
    """コマンドの断片から、実在する .py の道を集める。"""
    out: list[str] = []
    for m in _PY_TOKEN.finditer(seg):
        p = _resolve(m.group(0))
        if p and p not in out:
            out.append(p)
    return out


def _source(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:                                  # noqa: BLE001  読めないものは追わない
        return ""


def _uses_entry_here(src: str) -> str | None:
    """その1本のコードが、入口の関数を呼んでいるか（構文木で見る＝説明の文には反応しない）。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Name):
            if f.id in ENTRY_NAMES:
                return f.id
        elif isinstance(f, ast.Attribute):
            if f.attr in ENTRY_NAMES:
                return f.attr
            if f.attr == "score" and isinstance(f.value, ast.Name):
                return "score.score"                    # score.score(...) / judge.score(...)
            if f.attr.startswith("load_windows"):
                return "load_windows"
        # 名前が load_windows_cached のような形も拾う
        if isinstance(f, ast.Name) and f.id.startswith("load_windows"):
            return "load_windows"
    return None


def _imported_files(path: str, src: str) -> list[str]:
    """そのコードが読み込んでいる、このリポジトリの中の .py を集める。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    mods: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods += [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.append(node.module.split(".")[0])
    out: list[str] = []
    here = os.path.dirname(path)
    for m in dict.fromkeys(mods):
        if m in ENGINE_MODULES:
            continue                                    # engine の中へは たどらない（上の説明）
        for base in (here, _PR, os.path.join(SDK, "scripts", "dashboard")):
            c = os.path.join(base, m + ".py")
            if os.path.isfile(c):
                rp = os.path.realpath(c)
                if rp not in out:
                    out.append(rp)
                break
    return out


def reaches_entry(path: str, depth: int = MAX_DEPTH, seen: set | None = None) -> str | None:
    """その .py が、入口の関数に届くか。届いたら、その名前を返す。"""
    seen = set() if seen is None else seen
    rp = os.path.realpath(path)
    if rp in seen or depth < 0:
        return None
    seen.add(rp)
    src = _source(rp)
    if not src:
        return None
    hit = _uses_entry_here(src)
    if hit:
        return hit
    for nxt in _imported_files(rp, src):
        hit = reaches_entry(nxt, depth - 1, seen)
        if hit:
            return hit
    return None


def uses_engine_entry(seg: str) -> str | None:
    """コマンドの断片が、engine の入口を使う .py を走らせようとしているか。

    ★呼ぶ側（enforce_h2_pass / enforce_g2_pass）が、先に次を済ませてから呼ぶ:
        ①その断片が python 実行であること
        ②除外の言葉（--selftest・py_compile・--help・--verify・--identity・印を作る道具）でないこと
        ③4つのファイル名で既に止まっていないこと
    """
    for p in scripts_in_segment(seg):
        hit = reaches_entry(p)
        if hit:
            return f"{os.path.relpath(p, ROOT)} が engine の入口 {hit} を使う"
    return None


# ── わざと壊して止まるか試すテスト ──────────────────────────────────────────
def selftest() -> int:
    import tempfile

    ng: list[str] = []

    # P8 入口の6つが、実物のコードに在るか（手書きの一覧が腐るのを防ぐ）
    for name, home in ENTRY_HOME.items():
        needle = name.split(".")[-1]
        src = _source(home)
        if not src:
            ng.append(f"P8: 実物が読めない: {home}")
            continue
        if f"def {needle}" not in src and needle not in src:
            ng.append(f"P8: 入口の名前が実物に無い（名前が変わった疑い）: {name} ← {home}")

    with tempfile.TemporaryDirectory() as td:
        def w(name: str, body: str) -> str:
            p = os.path.join(td, name)
            with open(p, "w", encoding="utf-8") as f:
                f.write(body)
            return p

        direct = w("direct.py", "import engine_tuner_exec as ex\n"
                                "def go(df, rec):\n    return ex.run_recipe(df, rec)\n")
        middle = w("middle.py", "import direct\n\ndef go(df, rec):\n    return direct.go(df, rec)\n")
        outer = w("outer.py", "import middle\n\ndef go(df, rec):\n    return middle.go(df, rec)\n")
        docs = w("docs_only.py", "import engine_tuner_gen as g\n"
                                 "def count():\n    return len(g.FORMS)\n")
        words = w("words_only.py", '"""run_recipe と score.score の話を書いただけの文章。"""\n'
                                   "def f():\n    return 1\n")

        def case(name, seg, want_hit):
            got = uses_engine_entry(seg)
            good = (got is not None) if want_hit else (got is None)
            print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た結果: {got}"))
            if not good:
                ng.append(name)

        case("P1/P2 入口を直に呼ぶ .py は当たる", f"python3 {direct}", True)
        case("P4 間に1本 挟んでも当たる（深さ2）", f"python3 {middle}", True)
        case("P4b 間に2本 挟んでも当たる（深さ3）", f"python3 {outer}", True)
        case("P3 入口を呼ばない .py は当たらない", f"python3 {docs}", False)
        case("P3b 説明の文に名前が在るだけなら当たらない", f"python3 {words}", False)
        case("P7 走らせずに名前を数えるだけなら当たらない", f"grep -c run_recipe {direct}", True)

    # ★P7 の注記＝この部品は「python 実行かどうか」を見ない（呼ぶ側が先に見る）。
    #   だから grep の行でも当たる。呼ぶ側の番人で「grep は通る」を確かめる。

    # P5/P6/P9 は呼ぶ側（enforce_h2_pass / enforce_g2_pass）の番人で確かめる。
    # P9 深さの上限を超えるとすり抜ける（限界②を、そのまま実測で見せる）
    with tempfile.TemporaryDirectory() as td2:
        prev = None
        for i in range(6):
            body = ("import engine_tuner_exec as ex\ndef go(d, r):\n    return ex.run_recipe(d, r)\n"
                    if prev is None else f"import lay{i-1}\ndef go(d, r):\n    return lay{i-1}.go(d, r)\n")
            p = os.path.join(td2, f"lay{i}.py")
            with open(p, "w", encoding="utf-8") as f:
                f.write(body)
            prev = p
        deep = uses_engine_entry(f"python3 {prev}")
        print(f"  {'✅' if deep is None else '❌'} P9 深さの上限（{MAX_DEPTH}）を超えると当たらない＝限界②のとおり")
        if deep is not None:
            ng.append("P9: 深さの上限の外なのに当たった（限界の書き方と実物が食い違う）")

    for x in ng:
        print(f"❌ {x}")
    total = 6 + len(ENTRY_HOME) + 1
    print(f"{'❌' if ng else '✅'} 番人 {total - len(ng)}/{total} pass")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 0)
