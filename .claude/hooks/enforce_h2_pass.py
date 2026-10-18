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
#   gen_signal_families（G2 の印を作る道具・2026-10-01 に足した）・
#   引用符/ヒアドキュメントの中の言及・サブエージェント。
#   ★2026-10-01（142回目・まこさん「これ毎回不具合が起きてるから、今なおして」）＝G2 の印を作る道具も通す。
#     直す前は、両方の印の対象（search_limits.json ほか）を直すと、G2 の道具の --write をこのゲートが止め、
#     H2 の検査を G2 のゲートが止めて、どちらの印も取り直せなかった（互いに止め合う）。
#     どちらの道具も売買を回さず印を作る検査そのものなので、通しても engine_tuner を古い印で回す道は増えない。
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
# ★2026-10-17（186回目・まこさん「要でCCの案で進める」）＝除外の語を区切りのどこかで探すのをやめた。
#   除外するのは、走らせる .py が印を作る道具のときと、走らせる .py の旗として丸ごと書かれたときだけ。
#   直す前の穴＝走行の引数に除外の語の一部（例 --out leak_causality_diag_run）が入ると通った（183回目の enforce_purpose_gate と同じ穴）。
#   --lint-provenance＝engine_tuner_gen.py の静的検査（データも売買も使わない）＝9月18日に2回 止め、そのたびに H2 を取り直させた。
EXEMPT_SCRIPT = {"leak_causality_diag.py", "gen_signal_families.py"}
EXEMPT_FLAG = re.compile(r"(--selftest|--verify)(-\S*)?|--help|--identity|--lint-provenance")   # ★2026-10-18（監査 CP81）＝接尾は - で続く形だけ（--verify-nothing のような任意の語は除外にしない）
_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*=")
_WRAP = {"time", "nice", "nohup", "timeout", "exec", "command", "env", "xargs", "caffeinate"}

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
    ★2026-10-17（186回目）＝区切りの頭の python が走らせる .py だけを見る（_executed）。中身で止める部品にも、その .py だけを渡す。
    """
    for seg in re.split(r"[;&|\n]+", cmd_x):
        ex = _executed(seg)
        if ex is None:
            continue                                   # この断片は python 実行でない
        script, args = ex
        if _exempt(script, args):
            continue                                   # 検査・検収・印を作る道具は通す
        if TARGET.fullmatch(script.rsplit("/", 1)[-1]):
            return True
        if script.endswith(".py") and _scan is not None and _scan.uses_engine_entry(script):
            return True                                # ★名前が違っても、engine の入口を使うなら止める（走らせる .py だけを見る）
    return False


def _executed(seg: str):
    """区切りの頭の python が走らせる語と、その後ろの語を返す（python を走らせていなければ None）。
    ★2026-10-17（186回目）＝直す前は、区切りの中の名前を全部 見ていた（試しの道具の引数でも止めた）。"""
    toks = seg.split()
    i = 0
    while i < len(toks) and (_ASSIGN.match(toks[i]) or toks[i] in _WRAP or re.fullmatch(r"[0-9.]+[smhd]?", toks[i])
                             or (i > 0 and toks[i].startswith("-") and toks[i - 1] in _WRAP)):
        i += 1
    if i >= len(toks) or not re.fullmatch(r"python[0-9.]*", toks[i].rsplit("/", 1)[-1]):
        return None
    j = i + 1
    if "#" in toks:
        toks = toks[:toks.index("#")]   # ★2026-10-18（監査 CP81）＝区切りの後ろの注記（# --selftest）は旗でない
    while j < len(toks) and toks[j].startswith("-"):
        if toks[j] == "-m" and j + 1 < len(toks):   # -m <モジュール> は最後の名前に .py を付けて見る（CP80 の enforce_purpose_gate._run_target と同じ）
            toks[j + 1] = toks[j + 1].rsplit(".", 1)[-1] + ".py"
            j += 1
            break
        j += 2 if toks[j] in ("-X", "-W") else 1   # 値を1つ取る旗は値ごと飛ばす
    if j >= len(toks):
        return None
    return toks[j], toks[j + 1:]


def _exempt(script: str, args: list) -> bool:
    """印を作る道具か、走らせる .py の旗が検査・検収の旗か。"""
    return script.rsplit("/", 1)[-1] in EXEMPT_SCRIPT or any(EXEMPT_FLAG.fullmatch(a) for a in args)


def _scan_broken_on(cmd_x: str) -> bool:
    """判定の部品が読めないのに、.py を走らせようとしているか（＝判定できない）。"""
    if _scan is not None:
        return False
    for seg in re.split(r"[;&|\n]+", cmd_x):
        ex = _executed(seg)
        if ex is None or _exempt(*ex):
            continue
        if ex[0].endswith(".py"):
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
    for _m in re.finditer(r"\$\(([^()]*)\)|`([^`]*)`", cmd):
        cmd = cmd + "\n" + (_m.group(1) or _m.group(2) or "")   # ★2026-10-18（監査 CP81）＝$( ) と逆引用符の中は引用符の中でも走る＝別の区切りとして足す
    x = re.sub(r"(<<-?\s*[\"']?(\w+)[\"']?[^\n]*)\n.*?^\2", r"\1", cmd, flags=re.S | re.M)   # <<の行は残す（直す前は行の後ろの | python3 … も消えた）
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
    total = 0                                          # ★2026-10-17＝総数を手で書かずに数える（直す前の「23」は実際 24件だった）

    def case(name, want, cmd=run):
        nonlocal ng, total
        total += 1
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
    case("相手の印を作る道具も通る（gen_signal_families --write）＝G2 のゲートと互いに止め合わない", None,
         f"python3 {_real}/gen_signal_families.py --write")
    case("除外の言葉が在れば通る（--selftest）", None,
         f"python3 {_real}/regime_r9_diag.py --selftest")
    case("走らせずに名前を数えるだけなら通る（grep）", None,
         f"grep -c run_recipe {_real}/regime_r9_diag.py")

    # ── ★2026-10-17 新設（186回目・まこさん「要でCCの案で進める」）＝区切りの頭の python が走らせる .py だけを見る ──
    #   印は「指紋を書き換えた」状態のまま＝止まるべき所は止まる。
    case("★試しの道具の引数に engine_tuner.py の名前があるだけなら通る（走らせていない）", None,
         f"python3 .claude/tools/try_hooks.py --session s --write {_real}/engine_tuner.py")
    case("★走らせる .py の引数に除外の語の一部（leak_causality_diag）が入っても止まる", "指紋の不一致",
         "python3 scripts/priority_rebuild/engine_tuner.py --purpose search --out leak_causality_diag_run")
    case("★engine_tuner_gen.py の静的検査（--lint-provenance）は印が古くても通る", None,
         f"python3 {_real}/engine_tuner_gen.py --lint-provenance")
    case("★cd と time と -u で包んでも、本当に走らせるなら止まる", "指紋の不一致",
         "cd /x && time python3 -u scripts/priority_rebuild/engine_tuner.py --purpose search")
    case("★パスつきの python で走らせても止まる", "指紋の不一致",
         ".venv/bin/python scripts/priority_rebuild/engine_tuner.py --purpose search")
    case("★--verify で始まる旗（--verify-provenance）は、いままでどおり通る", None,
         f"python3 {_real}/engine_tuner_gen.py --verify-provenance x")
    case("★--selftest で始まる旗（--selftest-match）は、いままでどおり通る", None,
         f"python3 {_real}/regime_r9_diag.py --selftest-match")

    # ── ★2026-09-08 新設＝指紋を照らす口（--check-fingerprint）そのものを試す ──────
    #   監査 cp30 の M-2＝この口を守っているのが壊すプログラム b57 だけで、
    #   そして b57 は承認の流れでしか走らない（土台ゲートが Bash からの実行を止める）。
    #   ＝この口が腐っても、次の承認まで誰も気づかない状態だった。
    def case_fp(name, want_rc):
        nonlocal ng, total
        total += 1
        got = check_fingerprint()
        good = (got == want_rc)
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た終了コード: {got}"))
        ng += 0 if good else 1

    write_pass()                                       # 印を いまの中身で書き直す
    case_fp("★指紋を照らす口＝印と いまのコードが合っていれば 0 を返す", 0)
    with open(os.path.join(tmp, MUST[1]), "a", encoding="utf-8") as f:
        f.write("# 1文字 変えた（指紋を照らす口の番人）\n")
    case_fp("★指紋を照らす口＝コードを1文字でも変えると 1 を返す", 1)

    # ── ★2026-09-08 新設＝照合を緩める壊し方を捕まえる（監査 cp31 の別枠 A）──────
    #   監査 cp31 は check_fingerprint を5通りに壊し、2通りが生き残った。
    #   ①印のハッシュ値を先頭8文字だけで比べる ②中の「印の対象一覧を狭めない」検査を外す。
    #   ＝足した2件が守っていたのは「一致で 0」「食い違いで 1」の2つだけだった。
    write_pass()                                       # 印を いまの中身で書き直す（一致する状態）
    _now_fp = fingerprint(MUST)
    _bad_fp = _now_fp[:8] + ("1" if _now_fp[8:9] != "1" else "2") + _now_fp[9:]
    write_pass(fp=_bad_fp)
    case_fp("★指紋を照らす口＝先頭8文字だけが同じ印は通さない（照合を緩めない）", 1)
    write_pass(files=[m for m in MUST if m != f"{_PR}/e38_logics.json"])
    case_fp("★指紋を照らす口＝印の対象一覧から必須ファイルを外すと 1 を返す", 1)

    shutil.rmtree(tmp, ignore_errors=True)
    ROOT, PASS = keep
    print(f"\n番人: {total - ng}/{total} pass")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    # ★2026-09-08＝指紋を照らすだけの口（設計書 insp5-frame-and-table-tidy-20260908 の J）。
    #   hook 本体より前に置き、必ずここで終える（後ろに置くと hook 本体が標準入力を待つ）。
    if "--check-fingerprint" in sys.argv:
        sys.exit(check_fingerprint())
    if "--selftest" in sys.argv:
        selftest()
    hook_main()
