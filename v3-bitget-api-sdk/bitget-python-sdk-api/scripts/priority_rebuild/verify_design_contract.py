#!/usr/bin/env python3
"""verify_design_contract.py — 設計書 ↔ 実装 の機械照合（CC の「設計通り実装しない」虚偽＝類型G を物理検出）

なぜこれがあるか:
  CC は設計書に時間をかけても、まこさんが確認できない工程で設計の核心成分を実装から
  抜くこと（虚偽報告・false_positive 類型G）を繰り返した（例: E35 設計 §5.2 の RANGE_OK は
  Jump Model を成分に含むのに実装に無い）。net は score.py が V9 計算で出すので偽れないが、
  「設計通り作った」という工程の報告だけは私の言葉に頼っていて物理チェックが無かった。
  本スクリプトはその唯一の穴（設計↔実装の照合）を機械で塞ぐ。

仕組み:
  設計書(.md)に機械可読な DESIGN_CONTRACT（fenced json）を埋め込む（＝まこさんが設計 GO 時に見る面に置く）。
  実装ファイルを AST 解析し、設計が要求する各成分が「最終シグナルの定義式に実際に連結されているか」を照合。
  1つでも欠けたら exit 1（戦略の self-check に組めば CSV を出す前に停止＝採点に進めない）。

  私が嘘をつけるのは contract を改ざんする所だけ → それは設計書なのでまこさんの目に触れる。
  assert 自体は contract と実装を機械照合するだけ（私の判断は入らない）。
  本物であることは --self-test（わざと成分を抜いて落ちるか）のメタ確認で証明する。

使い方:
  python3 verify_design_contract.py <design.md>      # 設計書の contract で実装を照合（FAIL=exit 1）
  python3 verify_design_contract.py --self-test      # メタ確認: わざと壊して検出するか
"""
import ast
import json
import os
import re
import sys


def extract_contract(md_text: str):
    """設計書から 'DESIGN_CONTRACT' 直後の fenced json を1つ取り出す。"""
    idx = md_text.find("DESIGN_CONTRACT")
    if idx < 0:
        return None
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", md_text[idx:], re.S)
    if not m:
        return None
    return json.loads(m.group(1))


def rhs_names_for_symbol(tree: ast.AST, symbol: str):
    """symbol への全代入を集め、その右辺に現れる Name 一式を返す。
    返り値: (代入が見つかったか, 右辺 Name の集合)。"""
    names = set()
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == symbol for t in node.targets):
                found = True
                for sub in ast.walk(node.value):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
    return found, names


def _resolve_impl(md_path: str, impl_file: str) -> str:
    if os.path.isabs(impl_file):
        return impl_file
    start = os.path.abspath(md_path)
    for _ in range(8):
        start = os.path.dirname(start)
        cand = os.path.join(start, impl_file)
        if os.path.exists(cand):
            return cand
    raise FileNotFoundError(f"impl_file が見つからない: {impl_file}（{md_path} から上位探索）")


def check(md_path: str) -> bool:
    with open(md_path) as f:
        contract = extract_contract(f.read())
    if not contract:
        print(f"[STOP] DESIGN_CONTRACT が設計書に無い: {md_path}")
        return False
    impl = _resolve_impl(md_path, contract["impl_file"])
    src = open(impl, encoding="utf-8").read()
    print(f"design : {md_path}  ({contract.get('design_ref','')})")
    print(f"impl   : {contract['impl_file']}")
    ok = True
    calls = contract.get("self_check_calls")
    if calls:
        # contract-driven 方式: 実装が設計書を読んで自己チェックする「配線」が在るか。
        # 配線が在れば実装は設計書の部品リスト通りにしか動けない（成分欠落なら実行時に自停止）。
        # 配線を外す＝自己チェックを無力化する改変は、ここで検出してブロックする。
        for c in calls:
            if c in src:
                print(f"  [PASS] 自己チェック配線あり: {c}")
            else:
                print(f"  [FAIL] 自己チェック配線が無い（外された疑い）: {c}")
                ok = False
    else:
        # 旧方式: 実装の代入式に設計要求成分が連結されているか（literal assignment・contract-driven でない実装用）
        tree = ast.parse(src)
        for symbol, required in contract.get("must_combine", {}).items():
            found, names = rhs_names_for_symbol(tree, symbol)
            if not found:
                print(f"  [FAIL] {symbol}: 代入が実装に無い")
                ok = False
                continue
            missing = [c for c in required if c not in names]
            if missing:
                print(f"  [FAIL] {symbol}: 設計要求の成分が欠落 → {missing}  (実装RHS={sorted(names)})")
                ok = False
            else:
                print(f"  [PASS] {symbol}: 全成分あり {required}")
    print("RESULT:", "PASS（設計通り）" if ok else "FAIL（設計と実装が乖離＝採点に進めない）")
    return ok


def self_test() -> bool:
    """メタ確認: 健全な実装は通し、自己チェックを外した/成分を抜いた実装は検出するか。"""
    # 方式1（配線チェック・contract-driven）
    calls = ["_entry_contract(", "_assemble_signals("]
    wired = "x = _entry_contract()\ny = _assemble_signals(c, x)\n"
    ripped = "range_ok = a & b\n"                     # 自己チェック配線を外した
    w_ok = all(c in wired for c in calls)
    r_ok = all(c in ripped for c in calls)
    # 方式2（成分チェック・literal assignment）
    good = "a=1\nb=1\nc=1\nrange_ok = a & b & c\n"
    bad = "a=1\nb=1\nrange_ok = a & b\n"              # c（=設計要求成分）を抜いた

    def comp(src):
        found, names = rhs_names_for_symbol(ast.parse(src), "range_ok")
        return found and not [x for x in ["a", "b", "c"] if x not in names]

    g_ok, b_ok = comp(good), comp(bad)
    print(f"配線: 健全→{'PASS' if w_ok else 'FAIL'}(期待PASS) / 外し→{'PASS' if r_ok else 'FAIL'}(期待FAIL=検出)")
    print(f"成分: 健全→{'PASS' if g_ok else 'FAIL'}(期待PASS) / 欠落→{'PASS' if b_ok else 'FAIL'}(期待FAIL=検出)")
    ok = w_ok and not r_ok and g_ok and not b_ok
    print("メタ確認:", "成立（健全=通過・外し/欠落=検出）" if ok else "不成立＝番人が壊れている")
    return ok


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(0 if self_test() else 1)
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(0 if check(sys.argv[1]) else 1)
