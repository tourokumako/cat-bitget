#!/usr/bin/env python3
# design_gate_fallback.py — 設計↔実装ゲート（require_design_contract_before_run.sh）の部品（2026-09-24 新設）
#
# 何をするか
#   走らせる .py の名前を stdin で受け取り、承認済みの設計書の控え（acceptance_archive/<iter>.md）のうち、
#   その .py を DESIGN_CONTRACT の impl_file に持つものを1本 選んで、そのパスを1行 出す。
#   無ければ何も出さない（rc=0）。
#
# なぜ要るか（まこさん決定 2026-09-24「よい」＝根本から直す）
#   設計書の1枚（.claude/state/acceptance.md）に「当てる道具（apply_audit_fix.py）を直す工事」の設計書が
#   入っている間は、監査の指摘をその道具で当てられなかった。
#   ＝ゲートが、未承認・未実装の設計書で道具を照らし、必ず FAIL にしたため（2026-09-24 に実測・行き止まり）。
#   この部品で「その道具の最後に承認された控え」を探し、ゲートはそれで照らす。
#
# 選ぶ条件（全部 満たすものだけ・fail-closed）
#   ① 控えの名前が <iter>.md（.actual.md と、前の版 <iter>.NN.md は見ない）
#   ② 隣に <iter>.frozen.json が在る（承認の瞬間に凍結した impl_functions＝照合A・B の相手）
#   ③ DESIGN_CONTRACT が読めて、impl_file の名前が 走らせる .py と一致する
#   ④ git に登録済みで、承認後に1バイトも変わっていない（git diff --quiet HEAD）
#   複数 在れば、いちばん新しく書かれたもの（mtime）。
#
# 限界（正直に）
#   ・控えの設計書と いまの実装が合っているかは、この部品では見ない＝ゲートが verify と --diff で見る。
#   ・控えを消せば「無い」になり、ゲートは今までどおり止まる（守りは減らない）。
#   ・この部品を書き換えれば、無関係な控えを返せる（git diff には出る）。
#
# 使い方
#   printf 'apply_audit_fix.py\n' | python3 .claude/hooks/design_gate_fallback.py [<控えの置き場>]
#   --try ＝この部品を3通り 走らせて結果を出す（本物の控えの置き場と、一時の置き場）

import glob
import os
import subprocess
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
ARC_DIR = os.path.join(SDK, ".claude", "ratchet", "acceptance_archive")
sys.path.insert(0, os.path.join(SDK, "scripts", "priority_rebuild"))


def git_frozen(path: str) -> bool:
    """git に登録済みで、HEAD から変わっていないか。"""
    try:
        r1 = subprocess.run(["git", "ls-files", "--error-unmatch", path], cwd=ROOT,
                            capture_output=True, text=True)
        if r1.returncode != 0:
            return False
        r2 = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", path], cwd=ROOT,
                            capture_output=True, text=True)
        return r2.returncode == 0
    except Exception:
        return False


def pick(run_names: set, arc_dir: str = ARC_DIR) -> str:
    """走らせる .py の名前の集合から、承認済みの控えを1本 選ぶ。無ければ空文字。"""
    from verify_design_contract import scan_contracts
    cands = []
    for md in glob.glob(os.path.join(arc_dir, "*.md")):
        base = os.path.basename(md)
        if base.endswith(".actual.md"):
            continue
        stem = base[:-3]
        if "." in stem:                                   # <iter>.NN.md（前の版）は見ない
            continue
        if not os.path.exists(os.path.join(arc_dir, stem + ".frozen.json")):
            continue
        ok, _ng, _out = scan_contracts([md])
        if not ok:
            continue
        impl = os.path.basename(str(ok[0][1].get("impl_file", "") or ""))
        if not impl or impl not in run_names:
            continue
        if not git_frozen(md):
            continue
        cands.append((os.path.getmtime(md), md))
    if not cands:
        return ""
    cands.sort(reverse=True)
    return cands[0][1]


def _try() -> int:
    import shutil
    import tempfile
    print("★design_gate_fallback --try（3通り）")
    # 1) 本物の置き場・当てる道具 → 控えが1本 出る
    got = pick({"apply_audit_fix.py"})
    print(f"  {'✅' if got else '❌'} 1 当てる道具を指す承認済みの控えが在る → {os.path.basename(got) or '（無し）'}")
    # 2) 本物の置き場・指す控えが無い名前 → 何も出ない
    got2 = pick({"no_such_tool_xyz.py"})
    print(f"  {'✅' if not got2 else '❌'} 2 指す控えが無い .py では何も出ない → {got2 or '（無し）'}")
    # 3) 一時の置き場＝git に無い写し → 何も出ない（④で落ちる）
    tmp = tempfile.mkdtemp()
    try:
        if got:
            stem = os.path.basename(got)[:-3]
            shutil.copy(got, os.path.join(tmp, stem + ".md"))
            shutil.copy(os.path.join(ARC_DIR, stem + ".frozen.json"), os.path.join(tmp, stem + ".frozen.json"))
        got3 = pick({"apply_audit_fix.py"}, tmp)
        print(f"  {'✅' if not got3 else '❌'} 3 git に登録されていない写しは選ばない → {got3 or '（無し）'}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if (got and not got2 and not got3) else 1


def main() -> int:
    if "--try" in sys.argv:
        return _try()
    arc = ARC_DIR
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        arc = args[0]
    names = {x.strip() for x in sys.stdin if x.strip()}
    got = pick(names, arc)
    if got:
        print(got)
    return 0


if __name__ == "__main__":
    sys.exit(main())
