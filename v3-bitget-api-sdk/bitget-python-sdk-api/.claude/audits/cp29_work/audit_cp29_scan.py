#!/usr/bin/env python3
"""audit_cp29_scan.py — 監査 cp29 の数字を、実物から機械で数える。

まこさん指示 2026-09-08（逐語・cp28 の §7 に記録）＝「手で数えるのを禁じる→audit_m2c_scan.py」。
この監査（cp29）の報告書に出る数字は、すべてこのプログラムが実物から出したもの。

見るもの
  C-1 … 土台ゲートの2か所（Bash 側の BASE_SUFFIX ／ Write 側の case）と、画面の文言、
        b51 の実在・凍結との一致。
  C-2 … worklog §57-17 に2件が書かれているか。その2件が実物と合っているか。
  C-3 … 設計書の触る関数の一覧が空でないか／作るプログラムの出力と一致するか／
        承認のときに凍結された中身が空でないか・設計書と同じか。
  M-1 … 依頼書を作るプログラムの説明に --element の使い方が残っていないか／
        説明に書いた使い方と、実際に受け付ける口が合っているか。

使い方
  python3 .claude/audits/audit_cp29_scan.py
  python3 .claude/audits/audit_cp29_scan.py --selftest

限界（正直に書く）
  ①どのファイルを見るかは監査が選んだ（下の SRC）。
  ②重さの判定（その穴が重いか）はプログラムがしていない。監査が書く。
  ③壊すプログラムを実際に走らせるのは run_breaks.py --measure-only（別のコマンド）。
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
PR = os.path.join(SDK, "scripts", "priority_rebuild")
ARC = os.path.join(SDK, ".claude", "ratchet", "acceptance_archive")
ITER = "approval-audit-plumbing-20260907"

SRC = {
    "gate": os.path.join(ROOT, ".claude", "hooks", "require_acceptance_before_impl.sh"),
    "b51": os.path.join(ROOT, ".claude", "breaks", "b51_dirty_json_unguarded.sh"),
    "frozen_breaks": os.path.join(SDK, ".claude", "ratchet", "breaks_frozen.json"),
    "acceptance": os.path.join(ROOT, ".claude", "state", "acceptance.md"),
    "approved": os.path.join(ROOT, ".claude", "state", "acceptance.approved"),
    "frozen_fn": os.path.join(ARC, ITER + ".frozen.json"),
    "breaks_rec": os.path.join(ARC, ITER + ".breaks.json"),
    "worklog": os.path.join(ROOT, ".claude", "state", "session_worklog_20260904.md"),
    "dcgate": os.path.join(ROOT, ".claude", "hooks", "require_design_contract_before_run.sh"),
    "m2todo": os.path.join(SDK, ".claude", "ratchet", "m2_todo.json"),
    "genreq": os.path.join(PR, "gen_audit_request.py"),
}

sys.path.insert(0, PR)


def read(key: str) -> str:
    with open(SRC[key], encoding="utf-8") as f:
        return f.read()


def sha(path: str) -> str:
    out = subprocess.run(["shasum", "-a", "256", path], capture_output=True, text=True)
    return out.stdout.split()[0] if out.returncode == 0 else ""


# ---------------------------------------------------------------- C-1
def c1_base_suffix(text: str) -> list:
    """Bash 側の一覧 BASE_SUFFIX の中身を、代入の行から取り出す。"""
    m = re.search(r"^BASE_SUFFIX\s*=\s*\((.*?)\)", text, re.M | re.S)
    if not m:
        return []
    return re.findall(r"'([^']+)'", m.group(1))


def c1_write_case(text: str) -> list:
    """Write 側の場合分けのうち、末尾で見ている形（*.〜.json）を取り出す。"""
    return sorted(set(re.findall(r"\*(\.[a-z_]+\.json)\|", text)))


def c1_message_lines(text: str) -> int:
    """画面に出す文言に <iter>.dirty.json の行が在るか。"""
    return len([ln for ln in text.splitlines()
                if ln.lstrip().startswith("echo") and "<iter>.dirty.json" in ln])


# ---------------------------------------------------------------- C-3
def contract(text: str) -> dict:
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    return json.loads(m.group(1)) if m else {}


def rel_to_abs(rel: str) -> str:
    if rel.startswith(".claude/tools/"):
        return os.path.join(ROOT, rel)
    if rel.startswith("scripts/priority_rebuild/"):
        return os.path.join(SDK, rel)
    return os.path.join(ROOT, rel)


# ---------------------------------------------------------------- M-1
def genreq_flags(text: str) -> list:
    """argparse が受け付ける旗を、構文木から取り出す（文字列の検索ではない）。"""
    tree = ast.parse(text)
    flags = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"):
            for a in node.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    flags.append(a.value)
    return sorted(flags)


def genreq_usage(text: str) -> list:
    """説明（docstring）の「使い方」の節に並ぶコマンドの行を取り出す。"""
    doc = ast.get_docstring(ast.parse(text)) or ""
    out, on = [], False
    for ln in doc.splitlines():
        if ln.strip().startswith("使い方"):
            on = True
            continue
        if on:
            if ln.strip().startswith("限界"):
                break
            if "gen_audit_request.py" in ln:
                out.append(ln.strip())
    return out


def genreq_doc_flags(text: str) -> list:
    """説明の「使い方」の行に出てくる旗だけを取り出す。"""
    return sorted(set(re.findall(r"--[a-z-]+", " ".join(genreq_usage(text)))))


# ---------------------------------------------------------------- 本体
def scan() -> int:
    gate = read("gate")
    print("=" * 66)
    print("C-1｜汚れの記録が土台ゲートの守りに入っているか")
    print("=" * 66)
    bs = c1_base_suffix(gate)
    wc = c1_write_case(gate)
    print(f"  Bash 側の一覧 BASE_SUFFIX = {bs}")
    print(f"    → '.dirty.json' が在る: {'.dirty.json' in bs}")
    print(f"  Write 側の case の末尾の形 = {wc}")
    print(f"    → '.dirty.json' が在る: {'.dirty.json' in wc}")
    print(f"  画面の文言に <iter>.dirty.json の行 = {c1_message_lines(gate)} 行")
    b51_ok = os.path.exists(SRC["b51"])
    fz = json.loads(read("frozen_breaks"))
    name = "b51_dirty_json_unguarded.sh"
    now, want = sha(SRC["b51"]), fz.get(name, "")
    print(f"  b51 が実在 = {b51_ok} ／ 凍結の一覧に在る = {name in fz}")
    print(f"    いまのハッシュ値 = {now[:16]}… ／ 凍結 = {want[:16]}… ／ 一致 = {now == want}")
    rec = json.loads(read("breaks_rec"))
    r12 = [r for r in rec["rows"] if r["no"] == "12"]
    print(f"  承認のときの記録 #12 = {r12}")

    print()
    print("=" * 66)
    print("C-2｜設計書に書いていない変更2件が、記録に書かれているか")
    print("=" * 66)
    wl = read("worklog")
    m = re.search(r"### §57-17(.*?)### §57-18", wl, re.S)
    body = m.group(1) if m else ""
    print(f"  §57-17 の節が在る = {bool(m)} ／ 行数 = {len(body.splitlines())}")
    for label, key in (("（1）免除の旗", "lint-provenance"),
                       ("（2）やることリストの2行", "m2_todo")):
        print(f"  {label}＝§57-17 に '{key}' が {body.count(key)} 件")
    dc = read("dcgate")
    print(f"  実物①: 設計↔実装ゲートに --lint-provenance = {dc.count('--lint-provenance')} 件")
    todo = read("m2todo")
    tj = json.loads(todo)

    def find_state(obj, key):
        found = []
        if isinstance(obj, dict):
            if obj.get("id") == key or obj.get("no") == key:
                found.append(obj.get("状態") or obj.get("state") or obj.get("status"))
            for v in obj.values():
                found += find_state(v, key)
        elif isinstance(obj, list):
            for v in obj:
                found += find_state(v, key)
        return [x for x in found if x is not None]

    for k in ("M2-C-6", "M2-C-7"):
        st = find_state(tj, k)
        print(f"  実物②: {k} の状態の欄 = {st}")

    print()
    print("=" * 66)
    print("C-3｜触る関数の一覧が埋まっているか")
    print("=" * 66)
    acc = read("acceptance")
    c = contract(acc)
    impl = c.get("impl_functions", {})
    print(f"  設計書の一覧 = {len(impl)} ファイル ／ 関数の総数 = {sum(len(v) for v in impl.values())}")
    print(f"  空でないか = {bool(impl)}")
    from verify_design_contract import functions_ast     # noqa: E402
    ng = 0
    for rel, names in impl.items():
        with open(rel_to_abs(rel), encoding="utf-8") as f:
            now_fn = sorted(functions_ast(f.read()))
        same = sorted(names) == now_fn
        if not same:
            ng += 1
        print(f"    {'✅' if same else '❌'} {rel}: 設計書 {len(names)} 件 / 実物 {len(now_fn)} 件"
              + ("" if same else f" ／ 設計書だけ={set(names) - set(now_fn)}"
                                f" 実物だけ={set(now_fn) - set(names)}"))
    print(f"  作るプログラムの出どころと食い違うファイル = {ng} 件")
    fzf = json.loads(read("frozen_fn"))
    fzk = {k: v for k, v in fzf.items() if not k.startswith("_")}
    print(f"  凍結された一覧 = {len(fzk)} ファイル ／ 関数の総数 = {sum(len(v) for v in fzk.values())}")
    print(f"    空でないか = {bool(fzk)} ／ 設計書と同じか = "
          f"{ {k: sorted(v) for k, v in fzk.items()} == {k: sorted(v) for k, v in impl.items()} }")
    print(f"  no_impl_functions_reason の欄 = {'在る' if 'no_impl_functions_reason' in c else '無い'}")
    print(f"  must_use = {len(c.get('must_use', {}))} 件")
    print(f"  いまの設計書のハッシュ値 = {sha(SRC['acceptance'])[:16]}… ／ "
          f"承認の印 = {read('approved').strip()[:16]}… ／ 一致 = "
          f"{sha(SRC['acceptance']) == read('approved').strip()}")

    print()
    print("=" * 66)
    print("M-1｜説明から --element が消えているか")
    print("=" * 66)
    gr = read("genreq")
    print(f"  受け付ける口（構文木）= {genreq_flags(gr)}")
    print("  説明の「使い方」の行:")
    for ln in genreq_usage(gr):
        print(f"    {ln}")
    doc_flags = genreq_doc_flags(gr)
    real = [f for f in genreq_flags(gr) if f.startswith("--")]
    print(f"  説明に出る旗 = {doc_flags} ／ 実際の口 = {real}")
    print(f"    説明にあるのに実在しない旗 = {sorted(set(doc_flags) - set(real))}")
    print(f"  --element が説明の「使い方」に在る = {'--element' in doc_flags}")
    print(f"  --element がファイル全体に出る回数 = {gr.count('--element')}"
          " （消したと書いた注記の1件は残ってよい）")
    print(f"  N_ELEMENTS が定義として在る = "
          f"{bool(re.search(r'^N_ELEMENTS\\s*=', gr, re.M))}")
    return 0


# ---------------------------------------------------------------- 番人
def selftest() -> int:
    ok = fail = 0

    def t(name, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  ✅ {name}")
        else:
            fail += 1
            print(f"  ❌ {name}")

    print("わざと壊して止まるか試すテスト")
    # T1〜T3: BASE_SUFFIX の取り出しが、形を変えても正しく効くか
    t("T1 BASE_SUFFIX を取り出せる",
      c1_base_suffix("BASE_SUFFIX = ('.a.json', '.b.json')") == ['.a.json', '.b.json'])
    t("T2 一覧から 1件 消したら、その件が消えて見える",
      '.b.json' not in c1_base_suffix("BASE_SUFFIX = ('.a.json',)"))
    t("T3 代入が無ければ空を返す（黙って合格にしない）",
      c1_base_suffix("# BASE_SUFFIX の説明だけ") == [])
    # T4〜T5: Write 側の case
    t("T4 case の形を取り出せる",
      c1_write_case("*.breaks.json|*.frozen.json|*.dirty.json|\\") ==
      ['.breaks.json', '.dirty.json', '.frozen.json'])
    t("T5 case から dirty を消したら見えなくなる",
      '.dirty.json' not in c1_write_case("*.breaks.json|*.frozen.json|\\"))
    # T6〜T8: 旗の取り出しが構文木ベースで、コメントに釣られないか
    src_ok = 'import argparse\nap = argparse.ArgumentParser()\nap.add_argument("--frozen")\n'
    t("T6 add_argument から旗を取り出せる", genreq_flags(src_ok) == ['--frozen'])
    t("T7 コメントの中の --element は口として数えない",
      genreq_flags(src_ok + '# --element は外した\n') == ['--frozen'])
    t("T8 説明の使い方の行だけを拾う",
      genreq_usage('"""x\n\n使い方\n---\n  python3 gen_audit_request.py --frozen a\n\n'
                   '限界\n---\n  python3 gen_audit_request.py --element 4\n"""\n')
      == ['python3 gen_audit_request.py --frozen a'])
    # T9: 契約の取り出し
    t("T9 設計書の囲みから契約を取り出せる",
      contract('```json\n{"impl_functions": {"a": ["b"]}}\n```')["impl_functions"] == {"a": ["b"]})
    # T10: 文言の行数
    t("T10 文言の行は echo の行だけを数える",
      c1_message_lines('  echo "  <iter>.dirty.json" >&2\n# <iter>.dirty.json の説明\n') == 1)
    print(f"わざと壊して止まるか試すテスト {ok}/{ok + fail} pass")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else scan())
