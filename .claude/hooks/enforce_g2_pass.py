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
#   leak_causality_diag（H2 の印を作る道具・2026-10-01 に足した）・
#   引用符/ヒアドキュメントの中の言及・サブエージェント。
#   ★2026-10-01（142回目・まこさん「これ毎回不具合が起きてるから、今なおして」）＝H2 の印を作る道具も通す。
#     直す前は、両方の印の対象を直すと、H2 の検査をこのゲートが止め、G2 の道具の --write を H2 のゲートが止めて、
#     どちらの印も取り直せなかった（互いに止め合う）。どちらの道具も売買を回さず印を作る検査そのもの。
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
EXEMPT = re.compile(r"--selftest|py_compile|--help|--verify|--identity|gen_signal_families|leak_causality_diag")
_ANY_PY = re.compile(r"[A-Za-z0-9_./\-]+\.py")

# ★2026-08-27（68回目・まこさん承認「了解、修正を進めていいよ」・設計書 iter=h2g2-entry-scan-20260827）
#   止める相手を「4つのファイル名」だけで決めるのをやめ、
#   「走らせる .py が engine の入口の関数を使うか」を中身で見る部品を足した（H2 の見張りと同じ1本）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import lib_engine_entry_scan as _scan
    _SCAN_ERR = ""
except Exception as _e:                                # noqa: BLE001
    _scan = None
    _SCAN_ERR = f"{type(_e).__name__}: {_e}"


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
    #   行き止まりにはならない＝印を作る道具（gen_signal_families）は、その手前の除外で通る。
    if _scan_broken_on(cmd_x):
        return f"判定の部品（lib_engine_entry_scan.py）が読めない（{_SCAN_ERR}）"
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


def check_fingerprint() -> int:
    """印（g2_pass.json）が、いまのコードと一致しているかだけを見る（読むだけ・何も書かない）。

    ★2026-09-08（監査 cp32 の別枠 D・設計書 tm-scope-and-g2-fingerprint-20260908 の E）
      なぜ要るか＝H2 には この口が在る（`enforce_h2_pass.py --check-fingerprint`）が、
      G2 には無かった。監査 cp32 は `fingerprint` を直に呼んで照らすしかなかった。
      ＝「G2 の印を取り直したか」を確かめる口が、どこにも無い状態だった。
      この口は、上の check() が使っているのと同じ照合（129-133行）だけを取り出したもの。
    終了コード＝0（一致）／1（違う・印が無い・印が読めない）。
    ★番人＝壊すプログラム b66（照合を先頭8文字だけに緩めると、足した番人が落ちる）。
    """
    if not os.path.exists(PASS):
        print("❌ 検査済みの印が無い（g2_pass.json がまだ書かれていない）")
        return 1
    try:
        with open(PASS, encoding="utf-8") as f:
            rec = json.load(f)
        files = rec.get("files") or []
        fp = rec.get("fingerprint") or ""
    except Exception as e:                             # noqa: BLE001
        print(f"❌ 検査済みの印が読めない（g2_pass.json が壊れている）: {e}")
        return 1
    lack = [m for m in MUST if m not in files]
    if lack:
        print(f"❌ 印の対象一覧に必須のファイルが入っていない（一覧を狭めない）: {lack[:3]}")
        return 1
    now = fingerprint(files)
    if now != fp:
        print(f"❌ 印と、いまのコードが違う（印 {fp[:16]}… ／ いま {now[:16]}…）"
              "＝gen_signal_families.py --verify を走らせて印を取り直してください")
        return 1
    print(f"✅ 印と、いまのコードが一致（{fp[:16]}… ／ 対象 {len(files)} 件）")
    return 0


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

    # ── ★2026-08-27 新設＝名前でなく中身で止める（設計書 iter=h2g2-entry-scan-20260827）──
    _real = "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild"
    case("★別の名前でも、engine の入口を使うなら止まる（regime_r9_diag）", "指紋の不一致",
         f"python3 {_real}/regime_r9_diag.py --build 3")
    case("★審判を呼ぶだけのものも止まる（tuner_judgement）", "指紋の不一致",
         f"python3 {_real}/tuner_judgement.py")
    case("文書を作るだけのものは、印が古くても通る（gen_materials）", None,
         f"python3 {_real}/gen_materials.py --write")
    case("文書を作るだけのものは、印が古くても通る（gen_exit_families）", None,
         f"python3 {_real}/gen_exit_families.py --write")
    case("印を作る道具は通る（gen_signal_families）", None,
         f"python3 {_real}/gen_signal_families.py --approve")
    case("相手の印を作る道具も通る（leak_causality_diag）＝H2 のゲートと互いに止め合わない", None,
         f"python3 {_real}/leak_causality_diag.py")
    case("除外の言葉が在れば通る（--selftest）", None,
         f"python3 {_real}/regime_r9_diag.py --selftest")
    case("走らせずに名前を数えるだけなら通る（grep）", None,
         f"grep -c run_recipe {_real}/regime_r9_diag.py")

    # ── ★2026-09-08 新設＝印を照らす口（--check-fingerprint）そのものを試す ──────
    #   監査 cp32 の別枠 D＝H2 には この口が在るのに、G2 には無かった。
    #   ＝「G2 の印を取り直したか」を確かめる口が、どこにも無かった。
    def case_fp(name, want_rc):
        nonlocal ng
        got = check_fingerprint()
        good = (got == want_rc)
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た終了コード: {got}"))
        ng += 0 if good else 1

    write_pass()                                       # 印を いまの中身で書き直す
    case_fp("★印を照らす口＝印と いまのコードが合っていれば 0 を返す", 0)
    _now_fp = fingerprint(MUST)
    _bad_fp = _now_fp[:8] + ("1" if _now_fp[8:9] != "1" else "2") + _now_fp[9:]
    write_pass(fp=_bad_fp)
    case_fp("★印を照らす口＝先頭8文字だけが同じ印は通さない（照合を緩めない）", 1)
    # ★2026-09-09（監査 cp33 の Major 1）＝H2 と同じ4件にそろえる。
    #   直す前＝G2 は2件しか無く、「口の中の必須ファイルの検査だけを外す」壊し方が
    #   生き残った（監査 cp33 が5通りに壊して実測＝20/20 のまま通った）。
    #   設計書 tm-scope-and-g2-fingerprint-20260908 は「H2 と同じ作り」と書いたが、
    #   番人の数は H2 が4件・G2 が2件で、実物が食い違っていた。
    write_pass(files=[m for m in MUST if m != f"{_RT}/signal_families.json"])
    case_fp("★印を照らす口＝印の対象一覧から必須ファイルを外すと 1 を返す", 1)
    write_pass()                                       # 印を いまの中身で書き直す
    with open(os.path.join(tmp, MUST[1]), "a", encoding="utf-8") as f:
        f.write("# 1文字 変えた（印を照らす口の番人）\n")
    case_fp("★印を照らす口＝コードを1文字でも変えると 1 を返す", 1)

    shutil.rmtree(tmp, ignore_errors=True)
    ROOT, PASS = keep
    print(f"\n番人: {22 - ng}/22 pass")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    # ★2026-09-08（監査 cp32 の別枠 D）＝印を照らす口。hook 本体より前に置き、必ずここで終える
    #   （後ろに置くと hook 本体が動いて標準入力を待つ＝H2 と同じ作り）。
    if "--check-fingerprint" in sys.argv:
        sys.exit(check_fingerprint())
    if "--selftest" in sys.argv:
        selftest()
    hook_main()
