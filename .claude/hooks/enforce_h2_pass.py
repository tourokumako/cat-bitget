#!/usr/bin/env python3
# enforce_h2_pass.py — PreToolUse(Bash)（2026-08-16 まこさん GO「H2 完全化」の層2・safety hook）
#
# 目的:
#   まこさんの逐語（2026-08-16）＝「H2が守られない状態で、engine_tuner使っても意味がないので、
#   H2が完全に守られる状態にすることを第一優先としてほしい」。
#   leak_causality_diag（打ち切り再現テスト＝検査2→3→1-a→1-b→1-c の全部）が pass したときにだけ
#   書かれる「検査済みの印」（.claude/state/h2_pass.json＝対象コードと設定の指紋）が、いまの指紋と
#   一致しない限り、engine_tuner・実行器・生成器・E38 を python 実行できない（fail-closed）。
#   ＝コードか設定が1文字でも変わったら、H2 の検査をやり直すまで探索は物理的に回らない。
#
# 対象: engine_tuner / engine_tuner_gen / engine_tuner_exec / e38_priority_stack の python 実行。
# 対象外（通す）: --selftest・py_compile・--help・--verify・--identity（恒等検収）・
#   leak_causality_diag 自身（これが走れないと印を作れない＝デッドロック回避）・
#   引用符/ヒアドキュメントの中の言及・サブエージェント。
# 解除: H2PASS_OK=1（まこさんの明示 OK 時のみ・乱用禁止）。
#
# 限界（正直に）:
#   印そのもの（h2_pass.json）を手で偽造すれば通る＝TODO_OK=1 の乱用と同じ明示の違反で、機械では
#   見抜けない。検査そのものの限界は leak_causality_diag の冒頭（結果を変えない未来参照は捕まらない）。
#
# 番人: python3 .claude/hooks/enforce_h2_pass.py --selftest

import hashlib
import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
PASS = os.path.join(ROOT, ".claude", "state", "h2_pass.json")
_PR = "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild"
MUST = [   # 印の対象一覧に必ず入っていなければならないもの（一覧を狭めてすり抜ける道を塞ぐ）
    f"{_PR}/engine_tuner.py", f"{_PR}/engine_tuner_gen.py", f"{_PR}/engine_tuner_exec.py",
    f"{_PR}/e38_priority_stack.py", f"{_PR}/e38_logic_parts.py", f"{_PR}/e37_scalp.py",
    f"{_PR}/e38_logics.json", f"{_PR}/leak_causality_diag.py",
]
TARGET = re.compile(r"(engine_tuner|engine_tuner_gen|engine_tuner_exec|e38_priority_stack)\.py")
EXEMPT = re.compile(r"--selftest|py_compile|--help|--verify|--identity|leak_causality_diag")


def fingerprint(files: list) -> str:
    """leak_causality_diag.h2_fingerprint と同じ計算（同じ入力 → 同じ指紋）。"""
    h = hashlib.sha256()
    for rel in sorted(files):
        p = os.path.join(ROOT, rel)
        h.update(rel.encode())
        if os.path.exists(p):
            with open(p, "rb") as f:
                h.update(hashlib.sha256(f.read()).digest())
        else:
            h.update(b"<missing>")
    return h.hexdigest()


def check(cmd_x: str):
    """止める理由を返す（無ければ None）。cmd_x＝引用符・ヒアドキュメントを外したコマンド。"""
    if not re.search(r"python[0-9.]*[ \t]", cmd_x):
        return None                                    # python 実行でなければ見ない
    if EXEMPT.search(cmd_x):
        return None                                    # 検査・検収・印を作る道具は通す
    if not TARGET.search(cmd_x):
        return None
    if not os.path.exists(PASS):
        return "検査済みの印が無い（h2_pass.json がまだ書かれていない）"
    try:
        with open(PASS, encoding="utf-8") as f:
            rec = json.load(f)
        files = rec.get("files") or []
        fp = rec.get("fingerprint") or ""
    except Exception:
        return "検査済みの印が読めない（h2_pass.json が壊れている）"
    lack = [m for m in MUST if m not in files]
    if lack:
        return f"印の対象一覧に必須のファイルが入っていない（一覧を狭めない）: {lack[:3]}"
    if fingerprint(files) != fp:
        return "コードか設定が、検査した時から変わっている（指紋の不一致）"
    return None


def fail(reason: str):
    e = sys.stderr
    print("🔒 [H2 検査済みゲート・safety hook] H2（未来参照なし）の検査を通してから engine_tuner を回してください。", file=e)
    print("   まこさん指示 2026-08-16「H2が完全に守られる状態にすることを第一優先としてほしい」。", file=e)
    print("", file=e)
    print(f"不足: {reason}", file=e)
    print("", file=e)
    print("対処: 次を走らせて、全部の検査を pass させる（pass したときだけ印が書かれる）:", file=e)
    print("  python3 scripts/priority_rebuild/leak_causality_diag.py", file=e)
    print("（コードか設定を変えるたびに、検査のやり直しが要る＝それがこのゲートの目的です。", file=e)
    print("  H2PASS_OK=1 はまこさん明示 OK 時のみ）", file=e)
    sys.exit(2)


def hook_main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        sys.exit(0)                                    # 読めない入力では止めない（他 hook と同型）
    if data.get("agent_type"):
        sys.exit(0)
    if "H2PASS_OK=1" in raw:
        sys.exit(0)
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    cmd = (data.get("tool_input") or {}).get("command", "") or ""
    x = re.sub(r"<<\s*[\"']?(\w+)[\"']?.*?^\1", " ", cmd, flags=re.S | re.M)
    x = re.sub(r'"[^"]*"', " ", x)
    x = re.sub(r"'[^']*'", " ", x)
    reason = check(x)
    if reason:
        fail(reason)
    sys.exit(0)


# ---------------- 番人（わざと壊して、止まることを確かめる） ----------------

def selftest():
    import shutil
    import tempfile

    global ROOT, PASS
    keep = (ROOT, PASS)
    tmp = tempfile.mkdtemp()
    ROOT = tmp
    PASS = os.path.join(tmp, ".claude", "state", "h2_pass.json")
    os.makedirs(os.path.dirname(PASS), exist_ok=True)

    for rel in MUST:
        p = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"# {rel}\n")

    def write_pass(files=None, fp=None):
        files = MUST if files is None else files
        with open(PASS, "w", encoding="utf-8") as f:
            json.dump({"files": files, "fingerprint": fp or fingerprint(files)}, f)

    run = "python3 scripts/priority_rebuild/engine_tuner.py --purpose search"
    ng = 0

    def case(name, want, cmd=run):
        nonlocal ng
        got = check(cmd)
        good = (got is None) if want is None else (got is not None and want in got)
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た理由: {got}"))
        ng += 0 if good else 1

    if os.path.exists(PASS):
        os.remove(PASS)
    case("印が無いと止まる", "印が無い")
    write_pass()
    case("印が正しければ通る", None)
    case("検査・検収は印なしでも通る（--selftest）", None, run.replace("--purpose search", "--selftest"))
    case("leak_causality_diag 自身は通る", None, "python3 scripts/priority_rebuild/leak_causality_diag.py")
    case("対象外のスクリプトは見ない", None, "python3 scripts/priority_rebuild/observe_diag.py x.csv")
    with open(os.path.join(tmp, MUST[0]), "a", encoding="utf-8") as f:
        f.write("# 1文字 変えた\n")
    case("コードを1文字でも変えると止まる", "指紋の不一致")
    write_pass(files=[m for m in MUST if m != f"{_PR}/e38_logics.json"])
    case("印の対象一覧から必須ファイルを外すと止まる", "必須のファイル")
    write_pass(fp="deadbeef")
    case("指紋を書き換えた印は止まる", "指紋の不一致")

    shutil.rmtree(tmp, ignore_errors=True)
    ROOT, PASS = keep
    print(f"\n番人: {8 - ng}/8 pass")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    hook_main()
