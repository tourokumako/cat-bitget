#!/usr/bin/env python3
# enforce_g2_pass.py — PreToolUse(Bash)（2026-08-21 まこさん承認 e9fa2ae6…・M2-2-2b・safety hook）
#
# 目的:
#   まこさんの逐語（2026-08-21）＝「H2 と同じ形にする＝G2 が通ったときだけ『検査済みの印』を書き、
#   その印が今のコードと合わないうちは engine_tuner を走らせない」。
#   G2（型の表に沿った案かの審査が、11件の見本に正しく反応するか）が全部 期待どおりだったときにだけ
#   書かれる「検査済みの印」（.claude/state/g2_pass.json）が、いまの指紋と一致しない限り、
#   engine_tuner・生成器・実行器・E38 を python 実行できない（fail-closed）。
#   ＝審査が壊れたまま案を作る／回す道が、物理的に無くなる。
#
# なぜ要るか（真因）:
#   G2 は 2026-08-11 から2日間 壊れていたのに、誰も走らせなかったので気づかなかった（L-467）。
#   M2-2-2 で --verify の中から呼ぶようにしたが、--verify を打たなければ走らない＝打ち忘れに頼る。
#   印にすると、打ち忘れてもプログラムが止める。
#
# 対象: engine_tuner / engine_tuner_gen / engine_tuner_exec / e38_priority_stack の python 実行。
# 対象外（通す）: --selftest・py_compile・--help・--verify・--identity（恒等検収）・
#   gen_signal_families 自身（これが走れないと印を作れない＝デッドロック回避）・
#   引用符/ヒアドキュメントの中の言及・サブエージェント。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で廃止）。
#
# 限界（正直に）:
#   ①印（g2_pass.json）を手で偽造すれば通る＝hook のファイル自体を書き換えるのと同じ明示の違反で、
#     プログラムでは見抜けない（H2 と同じ）。
#   ②印の一覧は「G2 が通った道」で集まる＝G2 が通らない道のコードを変えても印は失効しない。
#   ③審査する処理の2つの分岐（部品がカタログに無い／パラメータが範囲の外）は、前段の G6 が先に
#     弾くので本物の案では届かない＝印があっても、その2つは G2 では守られていない（next_step 65番）。
#
# 番人: python3 .claude/hooks/enforce_g2_pass.py --selftest

import hashlib
import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
PASS = os.path.join(ROOT, ".claude", "state", "g2_pass.json")
_PR = "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild"
_RT = "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet"
MUST = [   # 印の対象一覧に必ず入っていなければならないもの（一覧が痩せてすり抜ける道を塞ぐ）
    f"{_PR}/gen_signal_families.py",        # G2 の本体と審査する処理
    f"{_PR}/engine_tuner_gen.py",           # 案を作る側（G2 は本物の案で試す）
    f"{_PR}/engine_tuner_exec.py",          # 材料が読めるかの判定
    f"{_PR}/indicator_reference_diag.py",   # 名前の分解＝2026-08-11 に G2 が壊れた原因そのもの
    f"{_RT}/signal_families.json",          # 型の表
    f"{_RT}/signal_families_approved.txt",  # 表の承認
]
TARGET = re.compile(r"(engine_tuner|engine_tuner_gen|engine_tuner_exec|e38_priority_stack)\.py")
EXEMPT = re.compile(r"--selftest|py_compile|--help|--verify|--identity|gen_signal_families")


def fingerprint(files: list) -> str:
    """gen_signal_families.g2_fingerprint と同じ計算（同じ入力 → 同じ指紋）。"""
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


def _runs_target(cmd_x: str) -> bool:
    """このコマンドが、対象のスクリプトを python で実行しようとしているか。

    ★区切り（; & | 改行）で分けた断片ごとに見る（enforce_h2_pass と同じ作り）。
      コマンド全体で見ると、grep でファイルの名前を数えるだけでも止まってしまう（2026-08-19 の直し）。
    """
    for seg in re.split(r"[;&|\n]+", cmd_x):
        if not re.search(r"(^|\s)python[0-9.]*(\s|$)", seg):
            continue                                   # この断片は python 実行でない
        if EXEMPT.search(seg):
            continue                                   # 検査・検収・印を作る道具は通す
        if TARGET.search(seg):
            return True
    return False


def check(cmd_x: str):
    """止める理由を返す（無ければ None）。cmd_x＝引用符・ヒアドキュメントを外したコマンド。"""
    if not _runs_target(cmd_x):
        return None
    if not os.path.exists(PASS):
        return "検査済みの印が無い（g2_pass.json がまだ書かれていない）"
    try:
        with open(PASS, encoding="utf-8") as f:
            rec = json.load(f)
        files = rec.get("files") or []
        fp = rec.get("fingerprint") or ""
    except Exception:
        return "検査済みの印が読めない（g2_pass.json が壊れている）"
    lack = [m for m in MUST if m not in files]
    if lack:
        return f"印の対象一覧に必須のファイルが入っていない（一覧を狭めない）: {lack[:3]}"
    if fingerprint(files) != fp:
        return "コードか設定が、検査した時から変わっている（指紋の不一致）"
    return None


def fail(reason: str):
    e = sys.stderr
    print("🔒 [G2 検査済みゲート・safety hook] G2（型の表に沿った案かの審査）の検査を"
          "通してから engine_tuner を回してください。", file=e)
    print("   まこさん指示 2026-08-21「その印が今のコードと合わないうちは engine_tuner を走らせない」。", file=e)
    print("", file=e)
    print(f"不足: {reason}", file=e)
    print("", file=e)
    print("対処: 次を走らせて、11件の見本が全部 期待どおりになる（通ったときだけ印が書かれる）:", file=e)
    print("  python3 scripts/priority_rebuild/gen_signal_families.py --verify", file=e)
    print("（型の表が未承認のときは G2 を走らせられません＝まこさんの --approve が先です）", file=e)
    print("（解除は 2026-08-16 に廃止＝合言葉では通りません）", file=e)
    sys.exit(2)


def hook_main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        sys.exit(0)                                    # 読めない入力では止めない（他 hook と同型）
    if data.get("agent_type"):
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
    PASS = os.path.join(tmp, ".claude", "state", "g2_pass.json")
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
    case("印を作る側（gen_signal_families）は通る＝行き止まりの回避", None,
         "python3 scripts/priority_rebuild/gen_signal_families.py --verify")
    case("対象外のスクリプトは見ない", None, "python3 scripts/priority_rebuild/observe_diag.py x.csv")
    case("grep で名前を数えるだけなら通る", None,
         "grep -c regime scripts/priority_rebuild/engine_tuner_gen.py")
    case("grep と python が同じでも、印が正しければ通る", None,
         "grep -c regime x.py ; python3 scripts/priority_rebuild/engine_tuner.py --purpose search")
    with open(os.path.join(tmp, MUST[0]), "a", encoding="utf-8") as f:
        f.write("# 1文字 変えた\n")
    case("コードを1文字でも変えると止まる", "指紋の不一致")
    case("区切りの後ろで本当に実行する形は、印が壊れていれば止まる", "指紋の不一致",
         "grep -c regime x.py ; python3 scripts/priority_rebuild/engine_tuner.py --purpose search")
    write_pass(files=[m for m in MUST if m != f"{_RT}/signal_families.json"])
    case("印の対象一覧から必須ファイルを外すと止まる", "必須のファイル")
    write_pass(fp="deadbeef")
    case("指紋を書き換えた印は止まる", "指紋の不一致")

    shutil.rmtree(tmp, ignore_errors=True)
    ROOT, PASS = keep
    print(f"\n番人: {11 - ng}/11 pass")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    hook_main()
