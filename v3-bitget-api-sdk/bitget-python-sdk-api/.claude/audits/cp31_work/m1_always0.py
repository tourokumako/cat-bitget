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
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で廃止）。
#
# 限界（正直に）:
#   印そのもの（h2_pass.json）を手で偽造すれば通る＝hook のファイル自体を書き換えるのと同じ明示の違反で、機械では
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
_ANY_PY = re.compile(r"[A-Za-z0-9_./\-]+\.py")

# ★2026-08-27（68回目・まこさん承認「了解、修正を進めていいよ」・設計書 iter=h2g2-entry-scan-20260827）
#   止める相手を「4つのファイル名」だけで決めるのをやめ、
#   「走らせる .py が engine の入口の関数を使うか」を中身で見る部品を足した。
#   ＝別の名前のプログラムを作って中から engine の部品を呼んでも、印が古ければ止まる。
#   判定は 1か所（lib_engine_entry_scan.py）にまとめ、G2 の見張りも同じものを呼ぶ
#   （同じ判定を2か所に書き写すと片方だけ直る＝next_step.md §6 の89番の型）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import lib_engine_entry_scan as _scan
    _SCAN_ERR = ""
except Exception as _e:                                # noqa: BLE001
    _scan = None
    _SCAN_ERR = f"{type(_e).__name__}: {_e}"


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


def _runs_target(cmd_x: str) -> bool:
    """このコマンドが、対象のスクリプトを python で実行しようとしているか。

    ★2026-08-19（まこさん決定「直す」）＝コマンド全体でなく、区切り（; & | 改行）で分けた
      断片ごとに見る。直す前は「コマンドのどこかに python が在り、どこかに対象の名前が在る」で
      止めていたので、grep でファイルの名前を数えるだけでも止まった（2026-08-18 に2回・worklog §11.6）。
      直したあとは「python が、その対象のファイルを実行しようとしている断片」だけを見る。
    """
    for seg in re.split(r"[;&|\n]+", cmd_x):
        if not re.search(r"(^|\s)python[0-9.]*(\s|$)", seg):
            continue                                   # この断片は python 実行でない
        if EXEMPT.search(seg):
            continue                                   # 検査・検収・印を作る道具は通す
        if TARGET.search(seg):
            return True
        if _scan is not None and _scan.uses_engine_entry(seg):
            return True                                # ★名前が違っても、engine の入口を使うなら止める
    return False


def _scan_broken_on(cmd_x: str) -> bool:
    """判定の部品が読めないのに、.py を走らせようとしているか（＝判定できない）。"""
    if _scan is not None:
        return False
    for seg in re.split(r"[;&|\n]+", cmd_x):
        if not re.search(r"(^|\s)python[0-9.]*(\s|$)", seg):
            continue
        if EXEMPT.search(seg):
            continue
        if _ANY_PY.search(seg):
            return True
    return False


def check(cmd_x: str):
    """止める理由を返す（無ければ None）。cmd_x＝引用符・ヒアドキュメントを外したコマンド。"""
    # ★判定の部品が読めないときは止める（fail-closed）。通すと守りが黙って消えるため。
    #   行き止まりにはならない＝印を作る道具（leak_causality_diag）は、その手前の除外で通る。
    if _scan_broken_on(cmd_x):
        return f"判定の部品（lib_engine_entry_scan.py）が読めない（{_SCAN_ERR}）"
    if not _runs_target(cmd_x):
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


def check_fingerprint() -> int:
    return 0  # cp31 が わざと壊した（必ず 0 を返す）
    """印（h2_pass.json）が、いまのコードと一致しているかだけを見る（読むだけ・何も書かない）。

    ★2026-09-08（設計書 insp5-frame-and-table-tidy-20260908 の J・Web Claude の2回目の重い2）
      なぜ要るか＝「H2 の印を取り直したか」を確かめる口が、どこにも無かった。
      いちばん近いのは tidy_next_step.py の検査 (c) だが、それが照らしているのは
      「next_step.md に書いてある文字」と「json の中の文字」だけで、
      いまのコードの指紋は1行も見ていない（実測 2026-09-08＝tidy_next_step.py:218）。
      ＝コードを書き替えて印を放置しても、その検査は通ってしまう。
      この口は、上の check() が使っているのと同じ照合（125行）だけを取り出したもの。
    終了コード＝0（一致）／1（違う・印が無い・印が読めない）。
    ★番人＝壊すプログラム b57（observe_diag.py にコメントを1行 足すと、この口が 1 を返す）。
    """
    if not os.path.exists(PASS):
        print("❌ 検査済みの印が無い（h2_pass.json がまだ書かれていない）")
        return 1
    try:
        with open(PASS, encoding="utf-8") as f:
            rec = json.load(f)
        files = rec.get("files") or []
        fp = rec.get("fingerprint") or ""
    except Exception as e:                             # noqa: BLE001
        print(f"❌ 検査済みの印が読めない（h2_pass.json が壊れている）: {e}")
        return 1
    lack = [m for m in MUST if m not in files]
    if lack:
        print(f"❌ 印の対象一覧に必須のファイルが入っていない（一覧を狭めない）: {lack[:3]}")
        return 1
    now = fingerprint(files)
    if now != fp:
        print(f"❌ 印と、いまのコードが違う（印 {fp[:16]}… ／ いま {now[:16]}…）"
              "＝leak_causality_diag.py を走らせて印を取り直してください")
        return 1
    print(f"✅ 印と、いまのコードが一致（{fp[:16]}… ／ 対象 {len(files)} 件）")
    return 0


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
    print("  （解除は 2026-08-16 に廃止＝合言葉では通りません）", file=e)
    sys.exit(2)


def hook_main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        sys.exit(0)                                    # 読めない入力では止めない（他 hook と同型）
    if data.get("agent_type"):
        sys.exit(0)
    # ★解除（H2PASS_OK=1）は 2026-08-16 に廃止（まこさん指示）＝通す道は無い。
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
    # ★2026-08-19（まこさん決定「直す」）＝走らせずに名前を数えるだけなら止めない（worklog §11.6 の誤った止まり）
    case("grep で名前を数えるだけなら通る", None,
         "grep -c regime scripts/priority_rebuild/engine_tuner_gen.py")
    case("grep と python が同じコマンドに在っても、python が対象を実行していなければ通る", None,
         "grep -c regime scripts/priority_rebuild/engine_tuner_gen.py ; python3 - ")
    case("grep と python が同じでも、印が正しければ通る（本当に実行する形）", None,
         "grep -c regime x.py ; python3 scripts/priority_rebuild/engine_tuner.py --purpose search")
    with open(os.path.join(tmp, MUST[0]), "a", encoding="utf-8") as f:
        f.write("# 1文字 変えた\n")
    case("コードを1文字でも変えると止まる", "指紋の不一致")
    # ★2026-08-19＝区切りの後ろで本当に実行する形は、印が壊れていればちゃんと止まる（緩めすぎていないかの確認）
    case("区切りの後ろで本当に実行する形は、印が壊れていれば止まる", "指紋の不一致",
         "grep -c regime x.py ; python3 scripts/priority_rebuild/engine_tuner.py --purpose search")
    write_pass(files=[m for m in MUST if m != f"{_PR}/e38_logics.json"])
    case("印の対象一覧から必須ファイルを外すと止まる", "必須のファイル")
    write_pass(fp="deadbeef")
    case("指紋を書き換えた印は止まる", "指紋の不一致")

    # ── ★2026-08-27 新設＝名前でなく中身で止める（設計書 iter=h2g2-entry-scan-20260827）──
    #   印は「指紋を書き換えた」状態のまま＝止まるべき所は止まる。
    _real = "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild"
    case("★別の名前でも、engine の入口を使うなら止まる（regime_r9_diag）", "指紋の不一致",
         f"python3 {_real}/regime_r9_diag.py --build 3")
    case("★審判を呼ぶだけのものも止まる（tuner_judgement）", "指紋の不一致",
         f"python3 {_real}/tuner_judgement.py")
    case("文書を作るだけのものは、印が古くても通る（gen_materials）", None,
         f"python3 {_real}/gen_materials.py --write")
    case("文書を作るだけのものは、印が古くても通る（gen_exit_families）", None,
         f"python3 {_real}/gen_exit_families.py --write")
    case("印を作る道具は通る（leak_causality_diag）", None,
         f"python3 {_real}/leak_causality_diag.py")
    case("除外の言葉が在れば通る（--selftest）", None,
         f"python3 {_real}/regime_r9_diag.py --selftest")
    case("走らせずに名前を数えるだけなら通る（grep）", None,
         f"grep -c run_recipe {_real}/regime_r9_diag.py")

    # ── ★2026-09-08 新設＝指紋を照らす口（--check-fingerprint）そのものを試す ──────
    #   監査 cp30 の M-2＝この口を守っているのが壊すプログラム b57 だけで、
    #   そして b57 は承認の流れでしか走らない（土台ゲートが Bash からの実行を止める）。
    #   ＝この口が腐っても、次の承認まで誰も気づかない状態だった。
    def case_fp(name, want_rc):
        nonlocal ng
        got = check_fingerprint()
        good = (got == want_rc)
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た終了コード: {got}"))
        ng += 0 if good else 1

    write_pass()                                       # 印を いまの中身で書き直す
    case_fp("★指紋を照らす口＝印と いまのコードが合っていれば 0 を返す", 0)
    with open(os.path.join(tmp, MUST[1]), "a", encoding="utf-8") as f:
        f.write("# 1文字 変えた（指紋を照らす口の番人）\n")
    case_fp("★指紋を照らす口＝コードを1文字でも変えると 1 を返す", 1)

    shutil.rmtree(tmp, ignore_errors=True)
    ROOT, PASS = keep
    print(f"\n番人: {21 - ng}/21 pass")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    # ★2026-09-08＝指紋を照らすだけの口（設計書 insp5-frame-and-table-tidy-20260908 の J）。
    #   hook 本体より前に置き、必ずここで終える（後ろに置くと hook 本体が標準入力を待つ）。
    if "--check-fingerprint" in sys.argv:
        sys.exit(check_fingerprint())
    if "--selftest" in sys.argv:
        selftest()
    hook_main()
