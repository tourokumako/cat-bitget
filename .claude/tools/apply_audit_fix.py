#!/usr/bin/env python3
"""apply_audit_fix.py — 監査結果の「修正の指示」を、実物に当てる。

設計書＝.claude/state/acceptance.md（iter audit-autofix-apply-20260916・まこさん承認 2026-09-16）。--design の口と自己テスト＝iter impl-instruction-apply-20260924（まこさん承認 2026-09-24）。

まこさん指示（逐語 2026-09-14）
  「その監査が書いた修正方法の通りに修正をするように自動生成をしろっていってんだよ。」
  「設計書の修正だけではない。実装データの修正をする場合もある。他にもあらゆる修正指示を出せて、
   それに対して自動で対応出来る状態にしろ。意味分かる？矮小化するな。」

なぜ要るか
  監査結果は 102回目にテンプレの形になった（1件ずつ6つの欄）。しかし欄のとおりに当てる
  プログラムが無く、当てる作業が私（CC）の手に残っていた。100回目は同じ作業で照合を9回 繰り返し、
  約4時間54分と agent 約359万トークンを使った（まこさんの逐語「これは詐欺行為である」）。

使い方
  python3 .claude/tools/apply_audit_fix.py --report <監査結果.md> --severity Critical,Major[,Minor,Process] [--dry]
    --dry を付けると、当てずに「当たるか」だけを確かめて一覧を出す。
  python3 .claude/tools/apply_audit_fix.py --design [<設計書.md>] [--dry]
    ★2026-09-24（設計書 impl-instruction-apply-20260924・まこさん承認）＝設計書の「4-20 実装の指示」を当てる口。
    --report と同時には受けない。当てる前に、承認の印（.claude/state/acceptance.approved）と設計書の
    ハッシュ値を照らし、合わなければ1件も当てない。欄の形は gen_audit_docs.item_errors で見る。
    対象のファイルが設計書の TARGET／NEW_FILE に無い件は当てない。当てなかった件が1件でも在れば終了コードは 1。
  python3 .claude/tools/apply_audit_fix.py --selftest
    見本の設計書と見本のコードを一時の置き場に作り、設計書 4-19 の場面を測る（本物には1バイトも書かない）。
  python3 .claude/tools/apply_audit_fix.py --report <監査結果.md> --decline 35,39 --verbatim <工事名>/<名前> [--dry]
    ★2026-10-17（184回目）＝まこさんが「当てない」と決めた修正を、当てた記録に「まこさんが当てないと決めた」で書く（当てない）。
    逐語のファイル（gen_verbatim.py で作った物）が記録の発言と合い、まこさんの発言を含むときだけ書く。
    hook 12・次の一手のプログラム・この道具は、記録に在る修正を済んだ物として扱う。試す口＝--selftest-decline。

何をするか（設計書 4-4）
  1. 監査結果を読み、修正の指示を番号の順に並べる（読み取りは gen_audit_docs.item_fields）
  2. --severity に当たる重さの件だけに絞る
  3. 全件を先に確かめる（当てる前に）＝状態が「確定」／対象のファイルが実在／
     直す前の文字がちょうど1か所／根拠の抜き書きの行が実物と合う
  4. 1件でも合わなければ、1件も当てずに一覧を出して rc=1（半分だけ当たった状態を作らない）
  5. 全件が確かめられたら、番号の順に当てる
  6. 当てた件数と、走らせるコマンドの件の一覧を画面に出す

止めて まこさんに報告するのは2つだけ（設計書 4-5）
  ①直す前の文字か根拠の抜き書きが実物と合わない ②状態が「未決」か「案が複数」

書かない相手（設計書 4-16）
  承認の印・凍結の記録・hook・道具そのもの（守りを1本で外せる道を作らないため）。
  監査が「hook を直せ」と書いたときは、当てずに一覧へ出す＝私が Write ツールで直す
  （そのとき承認ゲートと土台ゲートが効く）。

限界（正直に）
  ①当てた後の文が正しいかは見ない（監査が書いた文字をそのまま入れる）。
  ②この道具そのものを書き替えれば守りを外せる（承認ゲートの相手・git diff には出る）。
  ③同じ事実を書いたほかの場所を揃えるのは、いまも人の手（恒久72番の2番）。
  ④--report の道には、壊すプログラムと自己テストを付けない（恒久71番・まこさん決定 2026-09-16「３作らなくてよい」）。--design の道は、当てる先が売買のロジックの本体なので付けた（自己テスト --selftest・壊すプログラム b101・b102・設計書 impl-instruction-apply-20260924）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
sys.path.insert(0, os.path.join(ROOT, ".claude", "tools"))

import gen_audit_docs as g                                    # noqa: E402

SEVERITIES = ("Critical", "Major", "Minor", "Process")
# ★書かない相手（設計書 4-16）＝守りの仕組み。監査が名指ししても当てない。
NEVER_WRITE = (
    ".claude/hooks/", ".claude/tools/", ".claude/breaks/",
    "acceptance.approved", "verify_tool.approved", "design_approved.json",
    "_frozen.json", ".breaks.json", ".dirty.json", "h2_pass.json", "g2_pass.json",
    # ★2026-09-24（監査 CP41 の修正 1・A1-a）＝hook の登録そのもの。1回の書き込みで hook を全部 外せる穴を塞ぐ。
    ".claude/settings.json", ".claude/settings.local.json",
)
EVID_RE = re.compile(r"(\S+):(\d+)[^「]*「(.*)」\s*$")
# ★2026-09-24（設計書 impl-instruction-apply-20260924）＝設計書を当てる口が読むもの
APPROVED = os.path.join(ROOT, ".claude", "state", "acceptance.approved")     # 承認の印（設計書の sha256）
DESIGN = os.path.join(ROOT, ".claude", "state", "acceptance.md")            # 既定の設計書
# ★2026-09-30（設計書 point1-one-way-20260930-2）＝元データの JSON（SRC_JSON）は消した。
#   設計書の実装の指示は、設計書の ARC の iter の工事のフォルダ（gen_acceptance.src_from_work）と照らす。
IMPL_HEAD_RE = re.compile(r"^### 4-20 .*$", re.M)                            # 設計書の「実装の指示」の節の見出し
# ★2026-09-30（設計書 audit-fix-tools-target-20260930・まこさん承認）
#   ＝道具のファイル（.claude/tools の .py）にも、承認と TARGET がそろったときだけ当てる。
#   ＝監査結果の「走らせるコマンド」のうち、決まった形のものだけを走らせる（道具の名前と、旗ごとに受ける値の数）。
#   なぜ＝監査 cp52 の20件のうち19件を、この道具が飛ばし、CC が手で写していた
#     （まこさん指示 2026-09-30「手書きだと虚偽、改ざん、不正を働くので、手書きをせざるを得ないもの以外は、すべて自動生成」）。
TOOLS_DIR = os.path.join(ROOT, ".claude", "tools")                          # 自己テストが一時の置き場に替える
# ★2026-09-30（設計書 point2-design-to-impl-20260930）＝hook と壊すプログラムにも、承認と TARGET／NEW_FILE がそろったときだけ当てる
HOOKS_DIR = os.path.join(ROOT, ".claude", "hooks")                          # 自己テストが一時の置き場に替える
BREAKS_DIR = os.path.join(ROOT, ".claude", "breaks")                        # 自己テストが一時の置き場に替える
RUN_TOOLS = {
    "gen_acceptance.py": {"--write": 0, "--verify": 0, "--dry-run": 0, "--selftest": 0, "--work": 1},
    "gen_verbatim.py": {"--verify": 1, "--summary": 1},
    "gen_s22_map.py": {"--verify": 0},
    "run_breaks.py": {"--design": 1, "--measure-only": 0},
    # ★2026-10-01（監査 cp54 の C-1・C-2）＝法則と ToDo の文書を書く道具と、監査に出す前のチェックも、一覧の形なら走らせる
    #   （cp43・cp48・cp49 で gen_regime_kb.py --write が4回、cp47 で pre_audit_check.py --run が2回＝全部［手書き］に回っていた）。
    #   pre_audit_check.py --run が書くのは自分の結果（.claude/state/pre_audit_check.json）だけ。走らせる道具は決まった順番（ORDER・CHECKS）。
    "gen_regime_kb.py": {"--write": 1, "--verify": 1},
    "pre_audit_check.py": {"--run": 0, "--verify": 0},
}
# ★2026-09-30（工事 point5-report-direct-20260930）＝監査結果の「走らせるコマンド」のうち、確かめのコマンドは scripts/priority_rebuild の道具も走らせる
#   （直す前は .claude/tools の2本だけで、verify_design_contract・engine_tuner_gen・印の取り直しは まこさんが打った）。承認のプログラムは入れない。
SCRIPTS_DIR = os.path.join(SDK, "scripts", "priority_rebuild")
# ★2026-10-01（監査 cp54 の C-3）＝監査が名指しした結果ファイルの削除（rm）を行ってよい置き場。この下に実在するファイル1つだけ
RESULTS_DIR = os.path.join(SDK, "results", "priority_rebuild")
RUN_SCRIPTS = {
    "verify_design_contract.py": {"--diff": 1},
    "engine_tuner_gen.py": {"--selftest": 0},
    "gen_signal_families.py": {"--verify": 0},
    "leak_causality_diag.py": {},
}
# ★同＝印（G2・H2）の対象のファイルの一覧の置き場。ここに在るファイルを直したら、G2 → H2 の順で印を取り直す
PASS_MARKS = (os.path.join(ROOT, ".claude", "state", "g2_pass.json"), os.path.join(ROOT, ".claude", "state", "h2_pass.json"))
# ★2026-10-17（186回目・まこさん「設計書はなしでよい」）＝型の表の承認が今の表と合わないうちは、生成器と実行器に書かない（G1）。
#   hook enforce_signal_table_gate.sh は Write・Edit にしか掛からず、この道具は python の中で書くので、その外を通っていた。
#   照らしの計算は gen_signal_families.py --status をそのまま走らせる（計算を書き写さない）。
G1_TARGETS = ("engine_tuner_gen.py", "engine_tuner_exec.py")


def table_status() -> tuple:
    """型の表の承認が今の表と合うか（gen_signal_families.py --status の終了コード 0＝合う）。自己テストが差し替える。"""
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS_DIR, "gen_signal_families.py"), "--status"],
                       capture_output=True, text=True, cwd=SDK, timeout=120)
    return r.returncode == 0, (r.stdout.strip() or r.stderr.strip())[:200]
# ★2026-09-30（設計書 audit-fix-evidence-20260930・まこさん承認）＝監査が見た版の設計書の控え。
#   main が監査結果の「監査が照らしたハッシュ値」と sha256 が同じ承認の控えを見つけて入れる。
#   根拠が acceptance.md の行なら、いまの acceptance.md ではなく、この控えと照らす（監査の後に設計書が書き替わるため）。
AUDITED_DESIGN = ""
ARCHIVE_DIR = os.path.join(SDK, ".claude", "ratchet", "acceptance_archive")
# ★2026-09-30（設計書 point1-one-way-20260930-2・まこさん決定「案A」）＝当てた監査の修正の記録。hook 12（enforce_audit_fix.py）が読む。
#   git に残る置き場＝書き替えれば差分に出る。書くのはこの道具の _record_applied だけ。
APPLIED_RECORD = os.path.join(SDK, ".claude", "audits", "applied_fixes.json")
# ★2026-09-30（工事 point4-record-applied-20260930）＝いま当てている監査結果の名前（main が入れる・設計書の道では空）。
#   already_applied が当てた記録と照らす（当てた後の工事で同じ所が書き替わっても、当て終わりと分かる）。
CURRENT_REPORT = ""
# ★2026-09-30（工事 point5-report-direct-20260930）＝使わなくなった元データ（ratchet に無い）。監査結果の修正がこれを相手にしていたら、
#   全件を止める理由にせず、当てずに［手書き］で分ける（直す前は「対象のファイルが実在しない」で全件が止まった＝cp47・cp49）。
RETIRED_SOURCES = ("acceptance_src.json",)


def repo_path(p: str) -> str:
    """監査が書いたパスを、実物の場所に直す。"""
    p = (p or "").strip().strip("`")
    if p.startswith("SDK/"):
        return os.path.join(SDK, p[4:])
    cand = os.path.join(ROOT, p)
    if os.path.exists(cand):
        return cand
    # ★2026-09-30（工事 cp53-fix-20260930）＝まだ無いファイル（新しく作るファイル）は、置き場のフォルダが直下にだけ在れば直下にする
    #   （直す前は SDK 側に回り、.claude/breaks の新しい壊すプログラムを守りの仕組みと見て飛ばした）
    sdk = os.path.join(SDK, p)
    if os.path.isdir(os.path.dirname(cand)) and not os.path.isdir(os.path.dirname(sdk)):
        return cand
    return sdk


def never_write(rel: str) -> bool:
    # 守りの仕組みか。書いた形・揃えた形・実物の場所の3つで見る（大文字と小文字は区別しない）。
    # ★2026-09-24（監査 CP42 の A4）＝直す前は書いた文字のままを見たので、「.claude/./hooks/x.sh」と書くと
    #   一覧に当たらず、TARGET の縛り（揃えた形で照らす）も通って、hook に書けた（写しで実測）。
    raw = (rel or "").strip().strip("`")
    forms = (raw, os.path.normpath(raw), os.path.realpath(repo_path(raw)))
    return any(k.lower() in f.replace(os.sep, "/").lower() for f in forms for k in NEVER_WRITE)


def read_fixes(report_text: str) -> list:
    """監査結果から、修正の指示を番号の順に読む。★読み取りは gen_audit_docs.item_fields。"""
    out = []
    body, _ = g.split_mark(report_text)
    _, secs = g.split_sections(body)
    for head, lines in secs:
        kind = g.kind_of(head.split(". ", 1)[-1], g.RESULT_KIND)
        if kind not in ("修正", "プロセス"):
            continue
        text = "\n".join(lines)
        sev = ""
        for chunk in re.split(r"^### ", text, flags=re.M)[1:]:
            name = chunk.split("\n", 1)[0].strip()
            if name in SEVERITIES:
                sev = name
            parts = re.split(r"^#### 修正 (\d+)[ \t]*$", chunk, flags=re.M)
            for num, block in zip(parts[1::2], parts[2::2]):
                f = g.item_fields(num, block)
                f["重さ"] = sev
                out.append(f)
    out.sort(key=lambda f: int(f["番号"]))
    return out


# ══ 設計書の「実装の指示」を当てる口（2026-09-24・設計書 impl-instruction-apply-20260924）══════════

def read_design_blocks(design_text: str) -> list:
    """設計書から「4-20 実装の指示」の節を切り出し、[(番号, 1件の塊), …] を返す。節が無ければ空。"""
    m = IMPL_HEAD_RE.search(design_text)
    if not m:
        return []
    rest = design_text[m.end():]
    # 次の見出し（### 4-A や ## 5）まで。#### は件の見出しなので飛ばさない。
    # ★2026-09-24（監査 CP42 の A3）＝囲み（チルダ3つの行）の中の行は見出しと見ない。直す前は、中身の中の
    #   「# コメント」の行を次の見出しと取り違えて節が途中で切れ、1件も当てられなかった（写しで実測）。
    end, pos, fence = len(rest), 0, False
    for ln in rest.splitlines(keepends=True):
        if ln.rstrip("\n") == "~" * 3:
            fence = not fence
        elif not fence and re.match(r"#{1,3} ", ln):
            end = pos
            break
        pos += len(ln)
    sec = rest[:end]
    parts = re.split(r"^#### 実装 (\d+)[ \t]*$", sec, flags=re.M)
    return list(zip(parts[1::2], parts[2::2]))


def read_design_fixes(design_text: str) -> list:
    """設計書の「実装の指示」を、監査結果の修正と同じ形（item_fields の戻り）で番号の順に読む。重さは空。"""
    out = []
    for num, block in read_design_blocks(design_text):
        f = g.item_fields(num, block)                     # ★読み取りは監査結果と同じ1か所
        f["重さ"] = ""
        out.append(f)
    out.sort(key=lambda f: int(f["番号"]))
    return out


def approved_ok(design_path: str, mark_path: str = None) -> tuple:
    """承認の印の値と、設計書の sha256 が同じか。戻り＝(同じか, 理由)。印が無い・空・違う＝全部 いいえ（fail-closed）。"""
    import hashlib
    mark_path = mark_path or APPROVED
    if not os.path.isfile(design_path):
        return False, f"設計書が無い（{design_path}）"
    if not os.path.isfile(mark_path):
        return False, "承認の印が無い"
    want = open(mark_path, encoding="utf-8").read().strip()
    if not want:
        return False, "承認の印が空"
    now = hashlib.sha256(open(design_path, "rb").read()).hexdigest()
    if want != now:
        return False, f"承認の印（{want[:16]}…）と設計書（{now[:16]}…）が違う＝承認の後に設計書が変わった"
    return True, ""


def design_targets(design_text: str) -> set:
    """設計書の TARGET: と NEW_FILE: に書いたファイルの集合（当ててよい相手）。"""
    out = set()
    for ln in design_text.splitlines():
        if ln.startswith("TARGET:") or ln.startswith("NEW_FILE:"):
            for p in ln.split(":", 1)[1].split(","):
                p = p.strip().strip("`")
                if p:
                    out.add(os.path.realpath(repo_path(p)))
    return out


def tool_target_ok(rel: str, design_path: str = None, mark_path: str = None) -> bool:
    """道具のファイル（TOOLS_DIR の .py）・hook（HOOKS_DIR の .py・.sh）・壊すプログラム（BREAKS_DIR の .sh）に当ててよいか。

    ①承認の印と設計書のハッシュ値が合う ②そのファイルが設計書の TARGET か NEW_FILE に在る、の両方のときだけ真。
    承認の印・凍結の記録・settings に当たる名前なら、いつも偽（設計書 3-1 の1。hook と壊すプログラムは point2-design-to-impl-20260930 で当てる相手に入れた）。
    """
    raw = (rel or "").strip().strip("`")
    real = os.path.realpath(repo_path(raw))
    # ★2026-09-30（設計書 point2-design-to-impl-20260930）＝道具の .py に加えて、hook（.py・.sh）と壊すプログラム（.sh）にも当てる
    kinds = {os.path.realpath(TOOLS_DIR): (".py",), os.path.realpath(HOOKS_DIR): (".py", ".sh"),
             os.path.realpath(BREAKS_DIR): (".sh",)}
    ends = kinds.get(os.path.dirname(real))
    if not ends or not real.endswith(ends):
        return False
    others = [k for k in NEVER_WRITE if k not in (".claude/tools/", ".claude/hooks/", ".claude/breaks/")]
    forms = (raw, os.path.normpath(raw), real)
    if any(k.lower() in f.replace(os.sep, "/").lower() for f in forms for k in others):
        return False
    design_path = design_path or DESIGN
    ok, _why = approved_ok(design_path, mark_path)
    if not ok:
        return False
    return real in design_targets(open(design_path, encoding="utf-8").read())


def report_new_file_ok(rel: str, design_path: str = None, mark_path: str = None) -> bool:
    """監査結果の道で、新しいファイル（直す前の文字が「なし」）を作ってよいか（2026-10-01・監査 cp54 の C-4）。

    承認の印と設計書のハッシュ値が合い、そのファイルが承認済みの設計書の NEW_FILE に在るときだけ真。
    直す前は --report の道で新しいファイルを1件も作れず、1件でも在ると「対象のファイルが実在しない」で全件が止まった（cp45 の修正5）。
    """
    design_path = design_path or DESIGN
    ok, _why = approved_ok(design_path, mark_path)
    if not ok:
        return False
    real = os.path.realpath(repo_path((rel or "").strip().strip("`")))
    new_files = set()
    for ln in open(design_path, encoding="utf-8").read().splitlines():
        if ln.startswith("NEW_FILE:"):
            for p in ln.split(":", 1)[1].split(","):
                p = p.strip().strip("`")
                if p:
                    new_files.add(os.path.realpath(repo_path(p)))
    return real in new_files


def command_argv(cmd: str):
    """走らせるコマンドが決まった形なら (置き場, 引数の並び) を、違えば None を返す（シェルを通さない）。

    決まった形＝前に「cd <リポジトリの中の置き場> &&」が付いてもよい、python3 と RUN_TOOLS の道具と、
    その道具の旗（旗ごとに決まった数の値＝英数字・_・.・-・/ だけ。「..」は不可・/ で始まる値はリポジトリの中だけ）。
    scripts/priority_rebuild の道具は RUN_SCRIPTS の分だけ（旗の無い道具も一覧に在れば通す）。区切り・置き換え・リダイレクトの記号が在れば None。
    """
    import shlex
    s = (cmd or "").strip()
    if not s or "\n" in s:
        return None
    cwd = ROOT
    m = re.match(r"^cd\s+(\S+)\s+&&\s+(.*)$", s)
    if m:
        cwd = os.path.realpath(os.path.join(ROOT, m.group(1)))
        if not (cwd == ROOT or cwd.startswith(ROOT + os.sep)) or not os.path.isdir(cwd):
            return None
        s = m.group(2)
    if re.search(r"[;&|<>`$()\\]", s):
        return None
    try:
        toks = shlex.split(s)
    except ValueError:
        return None
    # ★2026-10-01（監査 cp54 の C-3）＝results の下の結果ファイル1つの削除（rm <パス>）も、一覧の形なら行う（cp49 で2回）。
    #   形＝語が2つ・先頭が rm・パスは英数字と _ . / - だけで「..」を含まない・RESULTS_DIR の下に実在するファイル。それ以外は None
    if toks[0] == "rm":
        if len(toks) != 2 or not re.fullmatch(r"[A-Za-z0-9_./-]+", toks[1]) or ".." in toks[1].split("/"):
            return None
        rp = os.path.realpath(os.path.join(cwd, toks[1]))
        if not (rp.startswith(os.path.realpath(RESULTS_DIR) + os.sep) and os.path.isfile(rp)):
            return None
        return cwd, ["/bin/rm", rp]
    if len(toks) < 2 or toks[0] != "python3":
        return None
    tool = os.path.realpath(os.path.join(cwd, toks[1]))
    # ★2026-09-30（工事 point5-report-direct-20260930）＝.claude/tools は RUN_TOOLS、scripts/priority_rebuild は RUN_SCRIPTS
    table = {os.path.realpath(TOOLS_DIR): RUN_TOOLS, os.path.realpath(SCRIPTS_DIR): RUN_SCRIPTS}.get(os.path.dirname(tool)) or {}
    rule = table.get(os.path.basename(tool))
    if rule is None:
        return None
    rest, i = toks[2:], 0
    if not rest and rule:
        return None                                        # 旗を持つ道具を旗なしで走らせない
    while i < len(rest):
        if rest[i] not in rule:
            return None
        n = rule[rest[i]]
        v = rest[i + 1] if i + 1 < len(rest) else ""
        if n and (not re.fullmatch(r"[A-Za-z0-9_./-]+", v) or ".." in v.split("/")
                  or (v.startswith("/") and not os.path.realpath(v).startswith(ROOT + os.sep))):
            return None
        i += 1 + n
    return cwd, [sys.executable, tool] + rest


def run_commands(cmds: list, design_path: str = None, check=None) -> int:
    """照合を1回 掛け、通れば番号の順にコマンドを走らせる。戻り＝0（全部 終了コード 0）／1。

    ★照合＝設計↔実装ゲート（require_design_contract_before_run.sh）と同じ verify_design_contract の check。
      道具の中から走らせると Bash の hook は掛からないので、同じ照合をここで掛ける（設計書 6-2 の1）。
    ★check は自己テストが渡す（本物の呼び出しでは None＝verify_design_contract.check）。
    """
    import subprocess
    if not cmds:
        return 0
    design_path = design_path or DESIGN
    print("\n— 走らせる前の照合（verify_design_contract の check・設計↔実装ゲートと同じ）")
    if check is None:
        sys.path.insert(0, os.path.join(SDK, "scripts", "priority_rebuild"))
        import verify_design_contract as vdc                # noqa: E402
        passed = bool(vdc.check(design_path))
    else:
        passed = bool(check(design_path))
    if not passed:
        print("❌ 照合が通らないので、コマンドを1つも走らせません")
        return 1
    for f, (cwd, argv) in cmds:
        shown = " ".join(argv[1:])
        print(f"\n▶ 修正 {f['番号']}: {shown}（置き場 {os.path.relpath(cwd, ROOT)}）")
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        out = ((r.stdout or "") + (r.stderr or "")).rstrip()
        if out:
            print(out[-4000:])
        print(f"▶ 修正 {f['番号']}: → 終了コード {r.returncode}")
        if r.returncode != 0:
            print("❌ コマンドが落ちたので、その後のコマンドは走らせません")
            return 1
    return 0


def impl_src_mismatch(fixes: list, items: list) -> list:
    """設計書から読んだ実装の指示が、工事のフォルダの `実装の指示`（items）と1文字も違わないか。違いを文で返す。

    ★なぜ要るか（監査 CP41 の A3-d）＝囲みの中に囲みの記号（チルダ3つ）が入ると、読み取りが内側で
      黙って切れ、切れた文字が実物に書かれた。元と突き合わせれば、切れた読み取りは必ず違いになる。
    ★2026-09-30（設計書 point1-one-way-20260930-2）＝元データの JSON のパスを受けるのをやめ、実装の指示の一覧を受ける
      （main が設計書の iter の工事のフォルダから読む・自己テストは見本の一覧を渡す）。
    """
    items = items or []
    if len(items) != len(fixes):
        return [f"元データの実装の指示は {len(items)} 件、設計書から読めたのは {len(fixes)} 件"]
    bad = []
    for it, f in zip(items, fixes):
        num = str(it.get("番号", "")) or f["番号"]
        if str(it.get("番号")) != f["番号"]:
            bad.append(f"実装 {f['番号']}: 番号が元データ（{it.get('番号')}）と違う")
        if (it.get("直す前の文字") or "") != (f["直す前の文字"] or ""):
            bad.append(f"実装 {num}: 直す前の文字が元データと違う（囲みの中で読み取りが切れた疑い）")
        bodies = [b for _a, _k, b in f["4つ目"]]
        if str(it.get("中身") or "") not in bodies:
            bad.append(f"実装 {num}: 中身（4つ目の欄）が元データと違う（囲みの中で読み取りが切れた疑い）")
        # ★2026-09-24（監査 CP42 の A3）＝1行の欄も元データと照らす。直す前は中身と直す前の文字だけを照らしたので、
        #   中身の中に「状態: 確定」の行が在ると読み取りがそれを欄と取り違え、元データで「未決」の件が当たった（写しで実測）。
        want = {"対象のファイル": it.get("対象のファイル", ""), "直す箇所": it.get("直す箇所", "なし"),
                "根拠の抜き書き": it.get("根拠の抜き書き", ""), "状態": it.get("状態", "確定")}
        for key, val in want.items():
            if str(val or "").strip() != str(f.get(key) or "").strip():
                bad.append(f"実装 {num}: {key}が元データと違う（囲みの中の行を欄と読み違えた疑い）")
        if str(it.get("種類", "直した後の文字")) not in [k for _a, k, _b in f["4つ目"]]:
            bad.append(f"実装 {num}: 種類（4つ目の見出し）が元データと違う")
    return bad


def applied_keys(path: str = None) -> set:
    """当てた記録を読み、(監査結果の名前, 修正の番号) の組の集まりを返す。記録が無い・読めなければ空。"""
    path = path or APPLIED_RECORD
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:                                     # noqa: BLE001
        return set()
    return {(str(x.get("report", "")), str(x.get("num", ""))) for x in (d.get("applied") or []) if isinstance(x, dict)}


def _record_applied(entries: list, path: str = None) -> int:
    """当てた修正（と、もう当て終わっていると分かった修正）を記録に書き足す。戻り＝新しく足した件数。

    entries＝[{"report": 監査結果の名前, "num": 修正の番号, "file": 対象のファイル, "how": "当てた"／"もう当て終わっていた"}]。
    ★消さない（書き足すだけ）。同じ組が在れば足さない。一時のファイルに書いてから置き替える。
    """
    import time
    path = path or APPLIED_RECORD
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:                                     # noqa: BLE001
        d = {}
    d.setdefault("_これは何か", "当てる道具（apply_audit_fix.py）が当てた監査の修正の記録。hook 12 が読み、"
                               "ここに在る修正を当て済みとして扱う。書くのは当てる道具だけ（手で書き替えない・差分は git に出る）")
    rows = [x for x in (d.get("applied") or []) if isinstance(x, dict)]
    have = {(str(x.get("report", "")), str(x.get("num", ""))) for x in rows}
    added = 0
    for e in entries:
        key = (str(e.get("report", "")), str(e.get("num", "")))
        if not key[0] or not key[1] or key in have:
            continue
        rows.append({"report": key[0], "num": key[1], "file": str(e.get("file", "")),
                     "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "how": str(e.get("how", "")),
                     **({"verbatim": str(e["verbatim"])} if e.get("verbatim") else {})})
        have.add(key)
        added += 1
    d["applied"] = rows
    tmp_path = path + ".tmp"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(tmp_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    os.replace(tmp_path, path)
    return added


def _verbatim_ok(name: str) -> tuple:
    """逐語のファイルが記録の発言と1文字も違わず（gen_verbatim.verify）、まこさんの発言を含むか。戻り＝(よいか, 理由, 本文)。"""
    import gen_verbatim as gv
    ok, why = gv.verify(name)
    if not ok:
        return False, why, ""
    txt, meta = gv.paths(name)
    if "まこさん" not in (json.load(open(meta, encoding="utf-8")).get("who") or []):
        return False, f"{name} に まこさんの発言が無い（CC の文だけ）", ""
    return True, "", txt.read_text(encoding="utf-8")


def decline(report: str, nums: list, verbatim: str, dry: bool = False, record: str = None, check=None) -> int:
    """★2026-10-17（184回目・まこさん「CC の案：要として、不具合1と2を直す」「修正進めて良い」）＝まこさんが「当てない」と
    決めた修正を、当てた記録に how「まこさんが当てないと決めた」で書く。hook 12・次の一手のプログラム・この道具は、記録に在る
    修正を済んだ物として扱う。書く条件＝監査結果が audits の直下の *_audit_report.md・番号が全部 監査結果に在る・
    逐語のファイル（gen_verbatim で作った物）が記録の発言と合い、まこさんの発言を含む。
    直す前は、当てた修正しか記録できず、まこさんが範囲の外にした修正のファイルを hook 12 が止め続けた（CP60 の修正35・39）。"""
    rp = os.path.realpath(report if os.path.isabs(report) else os.path.join(ROOT, report))
    if os.path.dirname(rp) != os.path.realpath(os.path.join(SDK, ".claude", "audits")) or not rp.endswith("_audit_report.md") \
            or not os.path.isfile(rp):
        print(f"❌ 監査結果ではない（audits の直下の *_audit_report.md だけ）: {report}")
        return 2
    fixes = {str(f.get("番号")): f for f in read_fixes(open(rp, encoding="utf-8").read())}
    miss = [n for n in nums if n not in fixes]
    if not nums or miss:
        print(f"❌ 監査結果に無い番号: {'・'.join(miss) or '（番号が空）'}")
        return 2
    ok, why, body = (check or _verbatim_ok)(verbatim)
    if not ok:
        print(f"❌ 逐語のファイルが使えない: {why}")
        return 2
    print(f"まこさんの決定（逐語のファイル {verbatim}）:")
    print("\n".join(f"  > {ln}" for ln in body.splitlines()))
    rows = [{"report": os.path.basename(rp), "num": n, "file": fixes[n].get("対象のファイル") or "",
             "how": "まこさんが当てないと決めた", "verbatim": verbatim} for n in nums]
    for r in rows:
        print(f"  {'（--dry＝書かない）' if dry else '書く'}: {r['report']} の 修正 {r['num']}（{r['file']}）")
    if dry:
        return 0
    print(f"✅ 当てた記録に {_record_applied(rows, record)} 件 足した（同じ組が在れば足さない）")
    return 0


def selftest_decline() -> int:
    """★2026-10-17＝--decline だけを試す軽い口。記録は一時の置き場に書く（本物の記録には書かない）。監査結果は本物を読むだけ。"""
    import tempfile
    rep = os.path.join(SDK, ".claude", "audits", "2026-10-03_indicator_textbook_check_cp60_audit_report.md")
    work = os.path.join(SDK, ".claude", "audits", "cp60_work", "cp60_result.md")
    good = lambda _n: (True, "", "当てない")                               # noqa: E731
    bad = lambda _n: (False, "合わない", "")                                # noqa: E731
    d = tempfile.mkdtemp(prefix="decline_selftest_")
    rec = os.path.join(d, "applied_fixes.json")
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        r1 = decline(rep, ["35", "39"], "x/y", record=rec, check=good)
        k1 = applied_keys(rec)
        r2 = decline(rep, ["9999"], "x/y", record=os.path.join(d, "r2.json"), check=good)
        r3 = decline(rep, ["35"], "x/y", record=os.path.join(d, "r3.json"), check=bad)
        r4 = decline(work, ["35"], "x/y", record=os.path.join(d, "r4.json"), check=good)
    rows = json.load(open(rec, encoding="utf-8")).get("applied") or [] if os.path.isfile(rec) else []
    cases = [
        ("D1 番号が在り逐語が合う → 記録に「まこさんが当てないと決めた」で2件 足り、applied_keys に入る",
         r1 == 0 and {(os.path.basename(rep), "35"), (os.path.basename(rep), "39")} <= k1
         and all(x.get("how") == "まこさんが当てないと決めた" and x.get("verbatim") == "x/y" for x in rows) and len(rows) == 2),
        ("D2 監査結果に無い番号 → 書かずに止まる", r2 == 2 and not os.path.exists(os.path.join(d, "r2.json"))),
        ("D3 逐語のファイルが使えない → 書かずに止まる", r3 == 2 and not os.path.exists(os.path.join(d, "r3.json"))),
        ("D4 作業場の結果を渡す → 書かずに止まる", r4 == 2 and not os.path.exists(os.path.join(d, "r4.json"))),
    ]
    ng = 0
    for nm, ok in cases:
        ng += not ok
        print(f"  {'✅' if ok else '❌'} {nm}")
    for fn in os.listdir(d):
        os.remove(os.path.join(d, fn))
    os.rmdir(d)
    print(f"自己テスト（--decline）{len(cases) - ng}/{len(cases)}")
    return 1 if ng else 0


def _recheck(f: dict, cur: str) -> bool:
    """当てる直前に、いまの中身（前の件を当てた後）でも「直す前の文字がちょうど1か所」かを見る。

    ★なぜ要るか（監査 CP41 の A2-b・実測）＝全件の確かめは当てる前の中身に対して行う。先の件を当てると
      中身が変わり、後の件の「直す前の文字」が消えることがある。直す前は そのまま進んで rc=0 だった。
    """
    before = f["直す前の文字"] or ""
    return bool(before) and cur.count(before) == 1


def design_key(design_text: str, design_path: str) -> str:
    """設計書の道の、当てた記録の名前＝「design:<ARC の iter>」（目印が無ければ設計書のファイル名）。"""
    m = re.search(r'<!-- ARC iter="([^"]+)" -->', design_text)
    return "design:" + (m.group(1) if m else os.path.basename(design_path))


def new_file_check(f: dict, path: str) -> tuple:
    """新しいファイル（直す前の文字が「なし」）の件が作れるか。戻り＝(作れるか, 理由, "")。★設計書の道だけ。

    作れる＝4つ目が「直した後の文字」1つだけ・中身が空でない・ファイルがまだ無い・置き場のフォルダが在る。
    同じ中身でもう在れば当て済み。別の中身で在れば止める（上書きしない）。
    """
    plans = [(k, b) for _a, k, b in f["4つ目"]]
    # ★2026-10-01（監査 cp54 の C-4）＝依頼書のテンプレの書き方どおり、見出し「足す文字」の全文も受ける（cp45 の修正5）
    if len(plans) != 1 or plans[0][0] not in ("直した後の文字", "足す文字") or not plans[0][1]:
        return False, "新しいファイルの件は、4つ目が「直した後の文字」か「足す文字」1つ（ファイルの全文）であること", ""
    body = plans[0][1]
    if os.path.exists(path):
        if open(path, encoding="utf-8").read().rstrip("\n") == body.rstrip("\n"):
            return False, "もう当て終わっている（新しいファイルが同じ中身で在る）", ""
        return False, f"新しいファイルのはずが、別の中身でもう在る（{path}）＝上書きしない", ""
    if not os.path.isdir(os.path.dirname(path)):
        return False, f"新しいファイルの置き場のフォルダが無い（{os.path.dirname(path)}）", ""
    return True, "新しいファイル", ""


def _done_in(before: str, kind: str, body: str, cur: str) -> bool:
    """直した後の文字（足す文字なら直す前の文字＋足す文字）が実物に在る＝当て終わりか（2026-10-01・監査 cp55 の R-5）。

    ★行を消す直し（直した後の文字が直す前の文字の中に含まれる）は、直した後の文字が消す前から実物に在るので、
      直す前の文字がまだ実物に在れば当て終わりと見ない（cp54 の修正2 が、当てる前に「当て終わり」と誤判定された）。
    ★check_one と already_applied の両方がこれを呼ぶ（同じ判定を2か所に書き写さない）。
    """
    if kind not in ("直した後の文字", "足す文字") or not body:
        return False
    done = (before + body) if kind == "足す文字" else body
    if not done.strip() or done not in cur:
        return False
    if kind == "直した後の文字" and body in before and before in cur:
        return False
    # ★2026-10-06（工事 m2c15-hidden-params-20261004 の修正45）＝直す前の文字がまだ実物に在り、直した後の文字が
    #   直す前の文字を含まない（＝当てても直す前の文字は残らない）なら、当て終わっていない。直す前は、直した後の文字と
    #   同じ文字が別の行に偶然 在ると（known=… の行が2つの登録で同じ）「当て終わり」と誤判定して、その件を飛ばした。
    if kind == "直した後の文字" and before in cur and before not in body:
        return False
    return True


def check_one(f: dict, chosen: dict = None, run_ok: bool = False, new_ok: bool = False) -> tuple:
    """1件が当てられるかを確かめる。戻り＝(当てられるか, 理由, 実物の中身)。

    ★chosen＝`--choose` で まこさんが決めた件（{番号: 案の記号 or "確定"}）。
      設計書 audit-autofix-apply-20260916 の 4-9・4-5・完成の条件 AUDIT-3。
    ★run_ok＝走らせるコマンドの件を、決まった形なら走らせる側へ回す（--report の道だけ真・設計書 audit-fix-tools-target-20260930）。
      走らせる側へ回した件は、理由に「走らせる」を入れて返す（main がファイルの直しと分ける）。
    """
    chosen = chosen or {}
    num, rel = f["番号"], (f["対象のファイル"] or "")
    fourth = f["4つ目"]
    pick = chosen.get(num)
    if f["状態"] != "確定" and pick is None:
        return False, f"状態が「{f['状態']}」＝まこさんが決めるまで当てない", ""
    if pick and pick != "確定":
        if not any(a == pick for a, _k, _b in fourth):
            have = "・".join(sorted({a for a, _k, _b in fourth if a})) or "（案の記号が無い）"
            return False, f"--choose で {pick} を選んだが、この件に その案が無い（在るのは {have}）", ""
    if any(k == "走らせるコマンド" for _, k, _ in fourth):
        body = next(b for _a, k, b in fourth if k == "走らせるコマンド")
        if run_ok and command_argv(body) is not None:
            return True, "走らせる", ""
        return False, "走らせるコマンド（当てずに、打つべきコマンドとして出す）", ""
    # ★2026-09-30（工事 point4-fix-label-20260930）＝逐語のファイル（まこさんの発言と OK した案の写し）には当てない。
    #   直す相手は、直す【番号】だけの次の案（まこさんの OK が要る）。直す前は OK の逐語をそのまま書き替えた。
    if is_verbatim(rel):
        return False, "逐語のファイルなので当てない（まこさんの発言・OK した案の写し）＝直す【番号】だけの次の案を出し、まこさんの OK をもらう", ""
    # ★2026-10-06（工事 m2c15-hidden-params-20261004 の件49・50）＝当てた記録（applied_fixes.json）に在る件は、相手を問わず
    #   当て終わり。行を消す直し（直した後の文字が空）は、当てた後に「直した後の文字が実物に在る」で見分けられず、
    #   「直す前の文字が実物に 0か所」＝実物と合わない件に数えられて、2回目の承認の前の検査（A11）が止まった。
    #   ★見る相手は、行を消す直し（直した後の文字が全部 空）だけ＝ほかの件は今までどおり実物の文字で見分ける。
    _del = all(not (b or "").strip() for _a, _k, b in f["4つ目"]) and (f["直す前の文字"] or "").strip() not in ("", "なし")
    _key = CURRENT_REPORT
    # ★2026-10-06（156回目・穴 B・まこさん「よい」）＝設計書の道では、同じ工事名（design:<iter>）の当てた記録に在る件は、
    #   行を消す直しに限らず当て終わり。直す前は、当てた後に まこさんが実物を手で直すと（恒久74番・observe_diag.py:7057 の
    #   sorted）、直した後の文字が実物から消えて直す前の文字だけが残り、実装41 を「当たる」と出した＝--design か
    #   承認の前の検査 A12 が、番人の囲みを二重に差し込んだ。★監査結果の道（--report）は今までどおり行を消す直しだけ。
    #   限界＝当てた後に誰かが実物を元へ戻しても、当てずに飛ばす（監査 CP62 の Q12 の S4 と同じ向き）。
    #   ★新しいファイルの件（直す前の文字が「なし」）は外す＝new_file_check が中身で見分ける（同じなら当て終わり・違えば止める）。
    _new = (f["直す前の文字"] or "").strip() == "なし"
    _design = not _key and not _new and os.path.isfile(DESIGN)   # 設計書の道（承認の前の検査 A11・A12 は check_one を直接 呼ぶ）
    if _design:
        _key = design_key(open(DESIGN, encoding="utf-8").read(), DESIGN)
    if (_del or _design) and _key and (_key, str(f.get("番号", ""))) in applied_keys():
        return False, "もう当て終わっている（当てた記録に在る）", ""
    # ★同＝守りの仕組みの相手でも、もう当て終わっている件は先に見分ける（直す前は「［手書き］CC が書く」と出た）
    if never_write(rel) and not tool_target_ok(rel) and already_applied(f):
        return False, "もう当て終わっている（直した後の文字が実物に在る）", ""
    if never_write(rel) and not tool_target_ok(rel):
        return False, f"守りの仕組みなので当てない（{rel}）＝私が Write ツールで直す", ""
    # ★2026-09-30（工事 point5-report-direct-20260930）＝使わなくなった元データを相手にした件は当てない（全件を止める理由にしない）
    if os.path.basename((rel or "").strip().strip("`")) in RETIRED_SOURCES and not os.path.isfile(repo_path(rel)):
        return False, f"使わなくなった元データなので当てない（{rel}）＝直す中身を、工事のフォルダの元へ写す", ""
    path = repo_path(rel)
    # ★2026-09-30（設計書 point2-design-to-impl-20260930）＝新しいファイル（直す前の文字が「なし」）は、設計書の道でだけ作る
    if (f["直す前の文字"] or "").strip() == "なし":
        if new_ok:
            return new_file_check(f, path)
        # ★2026-10-01（監査 cp54 の C-4）＝作れない新しいファイルの件は、全件を止める理由にせず［手書き］で分ける
        return False, f"新しいファイルは、承認済みの設計書の NEW_FILE に在るときだけ作る（{rel}）＝設計書に NEW_FILE を書いて承認をもらう", ""
    if not os.path.isfile(path):
        return False, f"対象のファイルが実在しない（{rel}）", ""
    cur = open(path, encoding="utf-8").read()
    before = f["直す前の文字"]
    if before is None:
        return False, "直す前の文字の囲みが無い", ""
    # ★2026-09-16＝もう当て終わっているかを、先に見る。
    #   なぜ要るか＝「足す文字」の件と、直した後の文字が直す前の文字を含む件は、
    #   当てた後も「直す前の文字」がちょうど1か所 残る＝二重に当たる。
    #   実測＝修正 9・13・21（足す文字）と 43（"…selftest" → "…selftest, \"stage_candidates\""）。
    for _a, kind, body in fourth:
        if not body:
            continue
        if _done_in(before, kind, body, cur):          # ★2026-10-01（監査 cp55 の R-5）＝行を消す直しは、直す前の文字が残っていれば当て終わりと見ない
            return False, "もう当て終わっている（直した後の文字が実物に在る）", cur
    n = cur.count(before)
    if n == 0:
        # ★2026-09-16＝もう当て終わっている件を見分ける。
        #   「直した後の文字」が実物に在れば、この件は当て済み（実物と合わない件に数えない）。
        #   直す前＝当て済みの件も「0か所」として全件を止めたので、2回目のコマンドが必ず落ちた。
        for _a, kind, body in fourth:
            if kind in ("直した後の文字", "足す文字") and body and body.strip() in cur:
                return False, "もう当て終わっている（直した後の文字が実物に在る）", cur
    if n != 1:
        return False, f"直す前の文字が実物に {n} か所（ちょうど1か所であること）", cur
    ok, why = check_evidence(f)
    if not ok:
        return False, why, cur
    return True, "", cur


def check_evidence(f: dict) -> tuple:
    """根拠の抜き書き「ファイル名:行番号「その行の逐語」」が、実物のその行と合うか。"""
    ev = (f["根拠の抜き書き"] or "").strip()
    m = EVID_RE.search(ev)
    if not m:
        return True, ""                       # 形が違うものは form の側が見る（ここでは通す）
    name, line, quote = m.group(1).strip("`"), int(m.group(2)), m.group(3)
    # ★2026-09-24（設計書 iter="audit-fix-evidence-backtick-20260924"・まこさん決定「案A」）
    #   ＝逐語の外側の1組のバッククォートを外す（ファイル名と同じ扱い）。
    #   実測（CP40）＝監査が20件とも逐語を「`…`」で囲んで書き、5件が「実物と合わない」になって
    #     1件も当てられなかった。テンプレは囲む・囲まないを決めておらず、形の検査（hook 11）は通す。
    #   ★外すのは先頭と末尾が両方 バッククォートのときだけ（行の中のバッククォートは残す）。
    if len(quote) >= 2 and quote[0] == "`" and quote[-1] == "`":
        quote = quote[1:-1]
    # ★2026-09-30（設計書 audit-fix-evidence-20260930）＝根拠が設計書（acceptance.md）の行なら、監査が見た版の控えと照らす。
    if os.path.basename(name) == "acceptance.md" and AUDITED_DESIGN:
        return _cmp_line(AUDITED_DESIGN, name, line, quote)
    # ★2026-09-16＝根拠のファイル名が、対象のファイルと同じ名前なら、対象のパスを使う。
    #   なぜ＝監査は作業場の写しを見て行番号を書く。同じ名前の本物を見ると、別の行が入っている。
    #   実測＝修正7 の根拠 acceptance_src.json:61 が、いまの ratchet の元データと合わなかった。
    tgt = repo_path(f["対象のファイル"] or "")
    if os.path.basename(tgt) == os.path.basename(name):
        return _cmp_line(tgt, name, line, quote)
    path = repo_path(name)
    if not os.path.isfile(path):
        # ★2026-09-16＝監査の作業場（audits の下）に在る写しを掴まないようにする。
        #   実測＝engine_tuner_gen.py は5か所に在り、4か所が監査の写し（mirror）だった。
        #   写しを見ると、同じ行番号でも別の行が入っていて「実物と合わない」と誤って言う。
        for r, _d, fs in os.walk(ROOT):
            if any(k in r for k in (".git", "__pycache__", os.sep + "audits" + os.sep)):
                continue
            if os.path.basename(name) in fs:
                path = os.path.join(r, os.path.basename(name))
                break
    return _cmp_line(path, name, line, quote)


def _cmp_line(path: str, name: str, line: int, quote: str) -> tuple:
    """そのファイルの その行が、書いてある逐語と合うか。"""
    if not os.path.isfile(path):
        return True, ""                       # 置き場を探せないものは見ない（限界）
    lines = open(path, encoding="utf-8").read().splitlines()
    if not (1 <= line <= len(lines)):
        return False, f"根拠の行が無い（{name} は全{len(lines)}行・書いてあるのは {line} 行）"
    # ★2026-09-30（設計書 audit-fix-evidence-20260930）＝監査が途中を「…」で省いた逐語は、
    #   「…」で区切った空でない文が、その行の中に順に全部 在れば合うとする（1つでも無ければ合わない）。
    #   「…」の無い逐語は今までどおり（逐語がそのまま行に含まれるか）。
    q = quote.strip()
    parts = [p.strip() for p in q.split("…") if p.strip()] if "…" in q else [q]
    pat = re.compile(".*?".join(re.escape(p) for p in parts))
    if q and not pat.search(lines[line - 1]):
        # ★2026-09-16＝同じ文が別の行に在れば、行番号がずれただけ（中身は合っている）。
        #   なぜ要るか＝監査が読んだ後に、そのファイルへ行を足すと行番号が動く。
        #   実測＝修正31 の根拠の行が、私が今日15行 足したことで動いていた。
        hits = [i + 1 for i, s in enumerate(lines) if pat.search(s)]
        if hits:
            return True, f"（行番号のずれ＝{name} の {line} 行 → {hits[0]} 行。中身は合っている）"
        return False, (f"根拠の行が実物と合わない（{name}:{line}）\n"
                       f"       書いてある: {quote.strip()[:60]}\n"
                       f"       実物      : {lines[line - 1].strip()[:60]}")
    return True, ""


def apply_one(f: dict, cur: str, pick: str = "") -> tuple:
    """1件を当てる。戻り＝(当てた後の中身, 何をしたか)。

    ★pick＝`--choose` で選んだ案の記号（例＝"B"）。案が複数の件は、その案だけを当てる。
    """
    before = f["直す前の文字"]
    plans = f["4つ目"]
    if pick and pick != "確定":
        plans = [(a, k, b) for a, k, b in plans if a == pick]
    for a, kind, body in plans:
        if kind == "直した後の文字":
            return cur.replace(before, body, 1), ("置き替えた" + (f"（案{a}）" if a else ""))
        if kind == "足す文字":
            return cur.replace(before, before + body, 1), ("足した" + (f"（案{a}）" if a else ""))
        if kind == "消す文字":
            return cur.replace(before, before.replace(body, "", 1), 1), ("消した" + (f"（案{a}）" if a else ""))
    return cur, "何もしなかった"


def already_applied(f: dict) -> bool:
    """もう当て終わっているか（直した後の文字か、直す前の文字＋足す文字が実物に在るか）。check_one の見分け方と同じ。

    ★2026-09-30（工事 point4-fix-label-20260930）＝守りの仕組みの相手でも、当て終わった件を先に見分けるため。
    """
    # ★2026-09-30（工事 point4-record-applied-20260930）＝当てた記録に在る件は当て終わり（直した後の文字が実物に残っていなくても）
    if CURRENT_REPORT and (CURRENT_REPORT, str(f.get("番号", ""))) in applied_keys():
        return True
    path = repo_path(f["対象のファイル"] or "")
    before = f["直す前の文字"]
    if before is None or not os.path.isfile(path):
        return False
    cur = open(path, encoding="utf-8").read()
    for _a, kind, body in f["4つ目"]:
        if not body:
            continue
        if _done_in(before, kind, body, cur):          # ★2026-10-01（監査 cp55 の R-5）＝check_one と同じ関数で見分ける
            return True
    return False


def is_verbatim(rel: str) -> bool:
    """逐語のファイル（まこさんの発言と OK した案の写し＝verbatim/ の下の .txt と .meta.json）か。

    ★2026-09-30（工事 point4-fix-label-20260930）＝やることの表.md と要件のまとめ.md は .md なので当たらない。
    """
    p = os.path.realpath(repo_path(rel)).replace(os.sep, "/")
    return "/verbatim/" in p and p.endswith((".txt", ".meta.json"))


def hand_label(why: str) -> str:
    """当てなかった件に付ける手書きの印（まこさん指示 2026-09-30「手書きせざるを得ない項目は、手書きと明記する」）。

    ★理由の文そのものは変えない（main の hard の判定と自己テストが、理由の文の頭を照らすため）。
    もう当て終わっている件・TARGET の外・実物と合わない件には印を付けない（空の文字を返す）。
    """
    if why.startswith(("状態が", "--choose で")):
        return "［手書き］まこさんが選ぶ"
    if why.startswith("走らせるコマンド"):
        return "［手書き］まこさんが打つ"
    if why.startswith("守りの仕組みなので"):
        return "［手書き］CC が書く"
    if why.startswith("逐語のファイル"):
        return "［手書き］次の案に まこさんの OK が要る"
    if why.startswith("使わなくなった元データ"):
        return "［手書き］CC が写す（手書きの項目は やることの表.md へ・自動の項目は次の案に まこさんの OK が要る）"
    if why.startswith("新しいファイルは"):
        return "［手書き］設計書に NEW_FILE を書いて承認をもらう"
    return ""


def main(argv: list = None, approved_path: str = None, src_items: list = None) -> int:
    """★argv と approved_path は自己テストが渡す（本物の呼び出しでは None＝コマンドの引数と本物の印）。
    ★src_items＝自己テストが渡す見本の実装の指示（本物の呼び出しでは None＝設計書の iter の工事のフォルダから読む）。"""
    global AUDITED_DESIGN, CURRENT_REPORT
    CURRENT_REPORT = ""                                     # ★2026-09-30（工事 point4-record-applied-20260930）＝監査結果の道でだけ入れる
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--report", default="")
    ap.add_argument("--severity", default="")
    ap.add_argument("--design", nargs="?", const=DESIGN, default="")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--choose", default="")
    ap.add_argument("--only", default="")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--decline", default="")       # ★2026-10-17＝まこさんが当てないと決めた修正の番号（, で区切る）
    ap.add_argument("--verbatim", default="")      # ★2026-10-17＝その決定の逐語のファイル（gen_verbatim の名前）
    ap.add_argument("--selftest-decline", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.selftest_decline:
        return selftest_decline()
    if a.decline:                                  # ★2026-10-17＝--report と一緒に使う・--severity は要らない・当てずに記録だけ書く
        if not a.report or not a.verbatim:
            print("❌ --decline には --report と --verbatim が要ります")
            return 2
        return decline(a.report, [x.strip() for x in a.decline.split(",") if x.strip()], a.verbatim, a.dry)
    if a.report and a.design:
        print("❌ --report と --design は同時に渡せません（どちらか1つにしてください）")
        return 2
    design_mode = bool(a.design)
    if a.help or (not design_mode and (not a.report or not a.severity)):
        print(__doc__)
        return 2
    want: list = []
    targets: set = set()
    if design_mode:
        # ★設計書を当てる道（設計書 4-4 の 1〜4）＝承認の印 → 節の切り出し → 欄の形 → 元データとの突き合わせ
        print(f"設計書: {a.design}")
        ok, why = approved_ok(a.design, approved_path)
        print(f"承認の印と一致: {'はい' if ok else 'いいえ'}{'' if ok else '（' + why + '）'}")
        if not ok:
            print("❌ 承認の印と設計書が合わないので、1件も当てません")
            return 1
        text = open(a.design, encoding="utf-8").read()
        blocks = read_design_blocks(text)
        errs = []
        for num, block in blocks:
            errs += g.item_errors(num, block)                # ★欄の形は監査結果と同じ検査
        if errs:
            print(f"❌ 実装の指示の欄が6つの形になっていません（{len(errs)} 件）＝1件も当てません")
            for e in errs[:10]:
                print(f"   ❌ {e}")
            return 1
        all_fixes = read_design_fixes(text)
        if not all_fixes:
            print("— 設計書に実装の指示が0件（4-20 の節が無いか、空）＝当てるものがありません")
            return 0
        # ★2026-09-30（設計書 point1-one-way-20260930-2）＝照らす相手は、設計書の iter の工事のフォルダの実装の指示
        if src_items is None:
            mi = re.search(r'<!-- ARC iter="([^"]+)" -->', text)
            if not mi:
                print("❌ 設計書に ARC の目印（iter）が無いので、工事のフォルダを決められません＝1件も当てません")
                return 1
            import gen_acceptance as ga
            try:
                ga.WORK = mi.group(1)
                src_items = ga.src_from_work(mi.group(1)).get("実装の指示") or []
            except SystemExit as e:
                print(f"❌ 工事のフォルダ {mi.group(1)} を読めません（{e}）＝1件も当てません")
                return 1
        bad = impl_src_mismatch(all_fixes, src_items)
        if bad:
            print(f"❌ 設計書から読んだ実装の指示が、元データと合いません（{len(bad)} 件）＝1件も当てません")
            for e in bad[:10]:
                print(f"   ❌ {e}")
            return 1
        targets = design_targets(text)
    else:
        if not os.path.isfile(a.report):
            print(f"❌ 監査結果がありません: {a.report}")
            return 1
        want = [s.strip() for s in a.severity.split(",") if s.strip()]
        bad = [s for s in want if s not in SEVERITIES]
        if bad:
            print(f"❌ 知らない重さ: {bad}（{'・'.join(SEVERITIES)} から選ぶ）")
            return 1

        text = open(a.report, encoding="utf-8").read()
        errs = g.form_errors(text)
        if errs:
            print(f"❌ 監査結果がテンプレの形ではありません（{len(errs)} 件）＝当てません")
            for e in errs[:10]:
                print(f"   ❌ {e}")
            return 1

        all_fixes = read_fixes(text)
        CURRENT_REPORT = os.path.basename(a.report)   # ★2026-09-30（工事 point4-record-applied-20260930）＝当てた記録の名前と同じ形
        # ★2026-09-30（設計書 audit-fix-evidence-20260930）＝監査が見た版の設計書の控えを探す（無ければ今までどおり）。
        AUDITED_DESIGN = ""
        mh = re.search(r"監査が照らしたハッシュ値:\s*([0-9a-f]{64})", text)
        if mh:
            import glob
            import hashlib
            for cand in sorted(glob.glob(os.path.join(ARCHIVE_DIR, "*.md"))):
                if hashlib.sha256(open(cand, "rb").read()).hexdigest() == mh.group(1):
                    AUDITED_DESIGN = cand
                    print(f"— 設計書の根拠は、監査が見た版の控え {os.path.basename(cand)} と照らす")
                    break
    # ★--choose＝まこさんが決めた件（{番号: 案の記号 or "確定"}）。書いていない番号は当てない。
    chosen = {}
    for pair in [x.strip() for x in a.choose.split(",") if x.strip()]:
        if "=" not in pair:
            print(f"❌ --choose の書き方が違う（<番号>=<案の記号 または 確定>）: {pair}")
            return 1
        num, pick = [t.strip() for t in pair.split("=", 1)]
        if num not in {f["番号"] for f in all_fixes}:
            print(f"❌ --choose に書いた番号が、監査結果に無い: {num}")
            return 1
        chosen[num] = pick
    if chosen:
        print(f"— まこさんが決めた件: {'・'.join(f'{k}={v}' for k, v in sorted(chosen.items(), key=lambda x: int(x[0])))}")

    # ★--only＝この番号だけを当てる（まこさんが件ごとに決めたときに使う。書かなければ重さで選ぶ）。
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    for num in only:
        if num not in {f["番号"] for f in all_fixes}:
            print(f"❌ --only に書いた番号が、監査結果に無い: {num}")
            return 1
    fixes = [f for f in all_fixes if (design_mode or f["重さ"] in want) and (not only or f["番号"] in only)]
    if only:
        print(f"— 当てる番号を絞った: 修正 {'・'.join(sorted(only, key=int))}")
    if design_mode:
        print(f"— 設計書の実装の指示: {len(fixes)} 件（当ててよい相手＝TARGET／NEW_FILE の {len(targets)} 本）")
    else:
        print(f"— 監査結果: {os.path.relpath(a.report, ROOT)}")
        print(f"— 当てる重さ: {'・'.join(want)} ／ 当たる件: {len(fixes)} 件")

    ready, stopped = [], []
    for f in fixes:
        # ★2026-10-01（監査 cp54 の C-4）＝監査結果の道でも、承認済みの設計書の NEW_FILE に在る新しいファイルは作る
        ok, why, cur = check_one(f, chosen, run_ok=not design_mode,
                                 new_ok=design_mode or report_new_file_ok(f["対象のファイル"] or "", None, approved_path))
        # ★設計書の道だけ（設計書 4-4 の 9）＝対象のファイルが TARGET／NEW_FILE に無ければ当てない
        if ok and design_mode:
            rel = os.path.realpath(repo_path(f["対象のファイル"] or ""))
            if rel not in targets:
                ok, why, cur = False, f"TARGET の外（設計書の TARGET／NEW_FILE に無い: {rel}）", cur
        (ready if ok else stopped).append((f, why, cur))

    for f, why, _c in stopped:
        print(f"   ⏸ 修正 {f['番号']}（{f['重さ']}）{hand_label(why)}: {why}")

    # ★「実物と合わない」だけが、全件を止める理由（設計書 4-5）。
    #   状態が未決・案が複数／走らせるコマンド／守りの仕組みは、当てないだけで、ほかの件は当てる。
    hard = [x for x in stopped
            if not x[1].startswith(("状態が", "走らせるコマンド", "守りの仕組みなので",
                                    "もう当て終わっている", "--choose で", "TARGET の外", "逐語のファイル", "使わなくなった元データ", "新しいファイルは"))]
    if hard:
        print(f"\n❌ 実物と合わない件が {len(hard)} 件 あるので、1件も当てません（先に全件を確かめる形）")
        return 1

    # ★2026-09-30（設計書 audit-fix-tools-target-20260930）＝走らせるコマンドの件を、ファイルの直しと分ける。
    #   ファイルの直しを全部 当てた後に、番号の順に走らせる（設計書 4-4 の⑤⑥）。
    cmds = [(f, command_argv(next(b for _a, k, b in f["4つ目"] if k == "走らせるコマンド")))
            for f, why, _c in ready if why == "走らせる"]
    ready = [x for x in ready if x[1] != "走らせる"]
    if a.dry:
        # ★--dry のときは走らせる予定だけを出す（CP42 の修正13 で足した --dry の節は、ひと続きのまま残す）
        for f, (cwd, argv) in cmds:
            print(f"   ▶ 走らせる予定 修正 {f['番号']}: {' '.join(argv[1:])}（置き場 {os.path.relpath(cwd, ROOT)}）")


    # ★2026-09-24（監査 CP41 の A2・修正 3）＝全件を先に「当てた後の中身」で確かめてから、まとめて書く。
    #   直す前＝1件ずつ読み直して書いていた。同じファイルに2件 当てて、先の件が後の件の「直す前の文字」を
    #   消すと、先の件だけ当たって rc=0 になった（監査が実測）。
    #   いま＝ファイルごとに中身を1回 読み、番号の順に中身の上で当てる。当てる直前に「直す前の文字が
    #   ちょうど1か所」を いまの中身で見直し、1件でも合わなければ 1バイトも書かずに rc=1（git apply と同じ）。
    mem: dict = {}
    plan: list = []
    for f, _w, _c in ready:
        path = repo_path(f["対象のファイル"])
        if _w == "新しいファイル":
            # ★2026-09-30（設計書 point2-design-to-impl-20260930）＝新しいファイルは中身の全文を書く（同じファイルに2件は止める）
            if path in mem:
                print(f"\n❌ 修正 {f['番号']}: 新しいファイル {os.path.relpath(path, ROOT)} に2件 当てようとしています＝1件も当てません")
                return 1
            mem[path] = next(b for _a, k, b in f["4つ目"] if k in ("直した後の文字", "足す文字")).rstrip("\n") + "\n"   # ★2026-10-01（cp54 の C-4）＝足す文字も全文
            plan.append((f, "新しいファイルを作った", path))
            continue
        if path not in mem:
            mem[path] = open(path, encoding="utf-8").read()
        cur = mem[path]
        if not _recheck(f, cur):
            print(f"\n❌ 修正 {f['番号']}: 先の件を当てた後の中身では「直す前の文字」がちょうど1か所ではありません"
                  f"＝実物と合わない件が在るので、1件も当てません（半分だけ当たった状態を作らない）")
            return 1
        new, what = apply_one(f, cur, chosen.get(f["番号"], ""))
        if new == cur:
            print(f"\n❌ 修正 {f['番号']}: 当てても中身が変わりません（消す文字が直す前の文字の中に無い など）"
                  f"＝実物と合わない件が在るので、1件も当てません（半分だけ当たった状態を作らない）")
            return 1
        mem[path] = new
        plan.append((f, what, path))
    # ★2026-10-17（186回目）＝生成器・実行器に当てる件が在れば、書く前に型の表の承認を照らす（G1・--dry でも照らす）
    g1 = sorted({os.path.basename(p) for _f, _w, p in plan if os.path.basename(p) in G1_TARGETS})
    if g1:
        t_ok, t_msg = table_status()
        if not t_ok:
            print(f"\n❌ {'・'.join(g1)} に当てる件が在りますが、型の表の承認が今の表と合いません（{t_msg}）"
                  f"＝1件も当てません（G1・enforce_signal_table_gate と同じ照らし）")
            print("   解除＝まこさんが scripts/priority_rebuild/gen_signal_families.py --approve を実行する")
            return 1
    if a.dry:
        nums = "・".join(f["番号"] for f, _w, _p in plan) or "（無し）"
        print(f"\n✅ --dry: 当たる {len(plan)} 件（修正 {nums}）／"
              f"当てない {len(stopped)} 件（実物と合わない件は0・当てた後の中身でも確かめた）")
        return 1 if (design_mode and [x for x in stopped if not x[1].startswith("もう当て終わっている")]) else 0
    done = 0
    for path, new in mem.items():
        if any(p == path for _f, _what, p in plan):
            # ★2026-09-24（監査 CP42 の A2-b）＝一時のファイルに書いてから置き替える（書き込みの途中で落ちても、
            #   そのファイルが途中で切れない）。書けなかったら例外で落とさず、止まった所を出して rc=1。
            tmp_path = path + ".apply_tmp"
            try:
                with open(tmp_path, "w", encoding="utf-8") as fh:
                    fh.write(new)
                os.chmod(tmp_path, (os.stat(path).st_mode & 0o7777) if os.path.exists(path)
                         else (0o755 if path.endswith(".sh") else 0o644))
                os.replace(tmp_path, path)
            except OSError as e:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                print(f"\n❌ 書き込みに失敗しました（{os.path.relpath(path, ROOT)}・{e}）。"
                      f"この前に書いたファイルは当たった後です＝途中まで当たった状態が残っています")
                return 1
    for f, what, path in plan:
        done += 1
        print(f"   ✅ 修正 {f['番号']}（{f['重さ'] or '設計書'}）［自動］: {what} → {os.path.relpath(path, ROOT)}")
    print(f"\n✅ 当てた {done} 件／当てなかった {len(stopped)} 件")
    # ★2026-09-30（設計書 point1-one-way-20260930-2・まこさん決定「案A」）＝監査結果の道だけ、当てた修正と
    #   もう当て終わっていた修正を記録に書き足す（hook 12 が読む）。--dry と設計書の道では書かない。
    # ★2026-09-30（設計書 point2-design-to-impl-20260930）＝設計書の道でも記録に書く（名前は「design:<iter>」）
    rep = design_key(text, a.design) if design_mode else os.path.basename(a.report)
    rec = [{"report": rep, "num": f["番号"], "file": f["対象のファイル"] or "", "how": "当てた"}
           for f, _what, _path in plan]
    rec += [{"report": rep, "num": f["番号"], "file": f["対象のファイル"] or "", "how": "もう当て終わっていた"}
            for f, why, _c in stopped if why.startswith("もう当て終わっている")]
    n_rec = _record_applied(rec)
    print(f"— 当てた記録に {n_rec} 件を足した（{os.path.relpath(APPLIED_RECORD, ROOT)}）")
    # ★2026-09-30（工事 point5-report-direct-20260930）＝印（G2・H2）の対象のファイルを直したら、G2 → H2 の順で印を取り直す（next_step の決まり）
    touched = {os.path.relpath(p, ROOT) for _f, _w, p in plan}
    hit = False
    for mk in PASS_MARKS:
        try:
            hit = hit or bool(touched & set(json.load(open(mk, encoding="utf-8")).get("files") or []))
        except (OSError, ValueError):
            pass
    if hit:
        print("— 印の対象のファイルを直したので、G2 → H2 の印を取り直す")
        for s in ("gen_signal_families.py --verify", "leak_causality_diag.py"):
            cmds.append(({"番号": "印"}, command_argv(
                f"cd v3-bitget-api-sdk/bitget-python-sdk-api && python3 scripts/priority_rebuild/{s}")))
    rc_cmd = run_commands(cmds)
    # ★設計書の道（設計書 4-4 の 10）＝当てなかった件が1件でも在れば rc=1（当て忘れを機械で見つける）
    #   ★2026-09-30＝もう当て終わっていた件は数えない（2回目の承認の後に、足した件だけを当てられる）
    left = [x for x in stopped if not x[1].startswith("もう当て終わっている")]
    return 1 if ((design_mode and left) or rc_cmd) else 0


# ══ 自己テスト（設計書 4-19 の場面・本物には1バイトも書かない）═══════════════════════════════

def selftest() -> int:
    """見本の設計書と見本のコードを一時の置き場に作り、設計書 4-19 の場面を測る。

    ★終了コード 1 のときは、落ちた場面を「❌ …」で画面に出す（壊すプログラム b101・b102 が照らす文字）。
    """
    import hashlib
    import shutil
    import tempfile
    sys.path.insert(0, os.path.join(ROOT, ".claude", "tools"))
    import gen_acceptance as ga                            # ★節を作る側（build_impl）と同じ形かを測る
    from contextlib import redirect_stdout
    import io

    # ★2026-09-30（設計書 point1-one-way-20260930-2）＝見本の実装の指示は、ファイル（--src）でなく main の引数で渡す
    state = {"items": []}

    def run(argv, mark):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(argv, approved_path=mark, src_items=state["items"])
        return rc, buf.getvalue()

    def item(num, rel, before, kind, body, ev, state="確定"):
        return {"番号": num, "対象のファイル": rel, "直す箇所": "1-1", "直す前の文字": before,
                "種類": kind, "中身": body, "根拠の抜き書き": ev, "状態": state}

    def design(items, target_rel):
        d = {"実装の指示": items}
        state["items"] = items
        sec = ga.build_impl(d)
        return ("<!-- ARC iter=\"selftest\" -->\n# 設計書｜見本\n\n"
                f"TARGET: {target_rel}\n\n## 4｜設計の中身\n\n### 4-20 実装の指示（見本）\n\n"
                + sec + "\n### 4-A この節に何を書いたか（一覧）\n\n| a |\n")

    def mark_of(md_path, mark_path, text=None):
        text = text if text is not None else open(md_path, "rb").read()
        open(mark_path, "w", encoding="utf-8").write(hashlib.sha256(text).hexdigest())

    ok = total = 0
    fails: list = []
    tmp = tempfile.mkdtemp(prefix="_selftest_impl_apply_", dir=os.path.join(ROOT, ".claude", "state"))
    rec_saved = globals()["APPLIED_RECORD"]
    globals()["APPLIED_RECORD"] = os.path.join(tmp, "applied_selftest.json")   # ★本物の記録には書かない
    try:
        rel = os.path.relpath(os.path.join(tmp, "sample.py"), ROOT)
        code = os.path.join(tmp, "sample.py")
        md = os.path.join(tmp, "design.md")
        mark = os.path.join(tmp, "approved")
        ev = f"{rel}:1「x = 1」"

        def clear_rec():
            # ★2026-10-06（穴 B）＝試しの当てた記録を空にする。設計書の道は「同じ工事名の当てた記録に在る件は当て終わり」と
            #   見るので、前の場面の記録（工事名 selftest・番号 1）が残ると、別の中身の件まで当て終わりと見る（本物では
            #   1つの工事の番号と件は1対1）。新しい試しの設計書を作るたびに空にする。
            if os.path.exists(globals()["APPLIED_RECORD"]):
                os.remove(globals()["APPLIED_RECORD"])

        def fresh(items, target_rel=None, body_text="x = 1\n"):
            clear_rec()
            open(code, "w", encoding="utf-8").write(body_text)
            txt = design(items, target_rel or rel)
            open(md, "w", encoding="utf-8").write(txt)
            mark_of(md, mark)

        # T1（完成の条件 #1）＝節を作る側の出力が、欄の検査で食い違い0件。指示が無ければ空
        total += 1
        d1 = {"実装の指示": [item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)]}
        blocks = read_design_blocks("### 4-20 見本\n\n" + ga.build_impl(d1) + "\n### 4-A\n")
        e1 = []
        for num, block in blocks:
            e1 += g.item_errors(num, block)
        if not e1 and len(blocks) == 1 and ga.build_impl({}) == "":
            ok += 1
            print(f"   T{total} 節を作る側の出力が6つの欄の形（食い違い0件・空なら出ない） → pass")
        else:
            fails.append(f"❌ 節の形 T{total}: {e1 or '塊の数が違う／空でも出る'}")

        # T2 --dry で当たる1件が出る
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
        rc, out = run(["--design", md, "--dry"], mark)
        if rc == 0 and "当たる 1 件" in out and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} --design --dry で当たる1件が出る → pass")
        else:
            fails.append(f"❌ --dry T{total}: rc={rc} {out[-200:]}")

        # T3 --dry なしで見本のコードが変わる
        total += 1
        rc, out = run(["--design", md], mark)
        if rc == 0 and open(code).read() == "x = 2\n":
            ok += 1
            print(f"   T{total} 当てると見本のコードが x = 2 になる → pass")
        else:
            fails.append(f"❌ 当てる T{total}: rc={rc} code={open(code).read()!r}")

        # T4（完成の条件 #3）＝承認の印を1文字 変えると、1件も当たらない
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
        open(mark, "w", encoding="utf-8").write("0" * 64)
        rc, out = run(["--design", md], mark)
        if rc == 1 and "承認の印と一致: いいえ" in out and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} 承認の印が違うと1件も当たらない → pass")
        else:
            fails.append(f"❌ 承認の印 T{total}: 印が違うのに当たった／止まらない（rc={rc}）")

        # T5 「状態」の行を消すと、形の食い違いで止まる
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
        txt = open(md, encoding="utf-8").read().replace("状態: 確定\n", "")
        open(md, "w", encoding="utf-8").write(txt)
        mark_of(md, mark)
        rc, out = run(["--design", md], mark)
        if rc == 1 and "6つの形になっていません" in out and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} 欄の形が違うと1件も当たらない → pass")
        else:
            fails.append(f"❌ 欄の形 T{total}: rc={rc}")

        # T6 監査結果を当てる道（--report）が、いままでどおり通る（本物の監査結果を --dry で）
        #   ★測るのは「読み取り → テンプレの形の検査 → 全件の確かめ」の段まで通ること。
        #     当たるかどうかは実物の状態に依る（当てた後に実物が動くと「合わない」が正しい答え）ので見ない
        #     （2026-09-24 に実測＝完成の条件のコマンドを直した後、修正 8 が「合わない」になって T6 が落ちた）。
        total += 1
        rep = os.path.join(SDK, ".claude", "audits",
                           "2026-09-24_impl_instruction_design_cp41_audit_report.md")
        rc, out = run(["--report", rep, "--severity", "Critical,Major", "--dry"], None)
        if (rc in (0, 1) and "— 当てる重さ:" in out and "テンプレの形ではありません" not in out
                and ("✅ --dry:" in out or "\n❌ " in out)):
            ok += 1
            print(f"   T{total} --report の道が通る（読み取り・形の検査・全件の確かめまで） → pass")
        else:
            fails.append(f"❌ --report T{total}: rc={rc} {out[-200:]}")

        # T7（完成の条件 #4）＝同じファイルに2件・先の件が後の件の「直す前の文字」を消す → 1件も当たらず rc=1
        total += 1
        fresh([item(1, rel, "x = 1\ny = 2", "直した後の文字", "x = 9", ev),
               item(2, rel, "y = 2", "直した後の文字", "y = 3", ev)], body_text="x = 1\ny = 2\n")
        rc, out = run(["--design", md], mark)
        if rc == 1 and open(code).read() == "x = 1\ny = 2\n":
            ok += 1
            print(f"   T{total} 先の件が後の件を消すと、1件も当たらず rc=1 → pass")
        else:
            fails.append(f"❌ 実物と合わない件 T{total}: 半分だけ当たった／rc={rc} code={open(code).read()!r}")

        # T8 対象が守りの仕組み（NEVER_WRITE）なら当てず、一覧に出て rc=1
        total += 1
        guard_rel = ".claude/settings.json"
        fresh([item(1, guard_rel, "x = 1", "直した後の文字", "x = 2", ev)], target_rel=guard_rel)
        rc, out = run(["--design", md], mark)
        if rc == 1 and "守りの仕組みなので当てない" in out:
            ok += 1
            print(f"   T{total} 守りの仕組みは当てず一覧に出る（rc=1） → pass")
        else:
            fails.append(f"❌ 守りの仕組み T{total}: rc={rc} {out[-200:]}")

        # T9 対象が TARGET／NEW_FILE に無いなら当てず、一覧に出て rc=1
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)], target_rel="scripts/priority_rebuild/other.py")
        rc, out = run(["--design", md], mark)
        if rc == 1 and "TARGET の外" in out and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} TARGET の外は当てず一覧に出る（rc=1） → pass")
        else:
            fails.append(f"❌ TARGET の外 T{total}: rc={rc} code={open(code).read()!r}")

        # T10 中身に囲みの記号（チルダ3つ）が入ると、元データと合わず1件も当たらない
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2\n~~~\nz = 0", ev)])
        rc, out = run(["--design", md], mark)
        if rc == 1 and "元データと合いません" in out and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} 囲みの記号が中身に在ると止まる → pass")
        else:
            fails.append(f"❌ 囲みの記号 T{total}: rc={rc} code={open(code).read()!r}")

        # T11 承認の印が空なら止まる（fail-closed）
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
        open(mark, "w", encoding="utf-8").write("")
        rc, out = run(["--design", md], mark)
        if rc == 1 and "承認の印が空" in out and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} 承認の印が空なら止まる → pass")
        else:
            fails.append(f"❌ 承認の印 T{total}: 空の印で止まらない（rc={rc}）")

        # T12 --report と --design を同時に渡すと止まる
        total += 1
        rc, out = run(["--report", md, "--design", md], mark)
        if rc == 2:
            ok += 1
            print(f"   T{total} --report と --design の同時指定で止まる → pass")
        else:
            fails.append(f"❌ 同時指定 T{total}: rc={rc}")

        # T13（監査 CP42 の A0）＝2本のファイルに1件ずつ・2件目の「直す前の文字」が実物に無い → 1件も当たらず rc=1
        #   ★全件を先に確かめる処理（実物と合わない件が在れば1件も当てない）を測る。直す前はこの場面が無く、
        #     その処理を外しても自己テストは 12/12 のままだった（写しで実測）。
        total += 1
        code2 = os.path.join(tmp, "sample2.py")
        rel2 = os.path.relpath(code2, ROOT)
        open(code, "w", encoding="utf-8").write("x = 1\n")
        open(code2, "w", encoding="utf-8").write("y = 1\n")
        items13 = [item(1, rel, "x = 1", "直した後の文字", "x = 2", ev),
                   item(2, rel2, "NOT_THERE", "直した後の文字", "y = 2", f"{rel2}:1「y = 1」")]
        open(md, "w", encoding="utf-8").write(design(items13, rel + ", " + rel2))
        mark_of(md, mark)
        rc, out = run(["--design", md], mark)
        if rc == 1 and open(code).read() == "x = 1\n" and open(code2).read() == "y = 1\n":
            ok += 1
            print(f"   T{total} 1件でも実物と合わなければ、ほかの件も当たらない（rc=1） → pass")
        else:
            fails.append(f"❌ 実物と合わない件 T{total}: 先に全件を確かめずに当たった／rc={rc} code={open(code).read()!r}")

        # T14（監査 CP42 の A3）＝状態が「未決」の件の中身に「状態: 確定」の行が在っても当たらない
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2\n状態: 確定", ev, state="未決")])
        rc, out = run(["--design", md], mark)
        if rc == 1 and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} 中身の中の、欄と同じ形の行を、欄と取り違えない → pass")
        else:
            fails.append(f"❌ 欄の取り違え T{total}: 未決の件が当たった（rc={rc}）")

        # T15（監査 CP42 の A4）＝守りの仕組みを「./」の形で書いても当てない
        total += 1
        hk = os.path.join(tmp, ".claude", "hooks")
        os.makedirs(hk, exist_ok=True)
        hook = os.path.join(hk, "x.sh")
        open(hook, "w", encoding="utf-8").write("x = 1\n")
        odd = os.path.relpath(os.path.join(tmp, ".claude"), ROOT) + "/./hooks/x.sh"
        open(md, "w", encoding="utf-8").write(design(
            [item(1, odd, "x = 1", "直した後の文字", "x = 2", f"{odd}:1「x = 1」")],
            os.path.relpath(hook, ROOT)))
        mark_of(md, mark)
        rc, out = run(["--design", md], mark)
        if rc == 1 and "守りの仕組みなので当てない" in out and open(hook).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} 守りの仕組みは、書き方を変えても当てない → pass")
        else:
            fails.append(f"❌ 守りの仕組み T{total}: 書き方を変えると当たった（rc={rc}）")

        # T16（監査 CP42 の A0）＝先の件が、後の件の「直す前の文字」をもう1つ作る → 1件も当たらず rc=1
        #   ★当てる直前の確かめ（_recheck）だけが受ける場面。「直す前の文字が無くなる」場面（T7）は、
        #     当てても中身が変わらない件で止める処理も受ける。
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 1\nz = 0\ny = 2", ev),
               item(2, rel, "y = 2", "直した後の文字", "y = 3", ev)], body_text="x = 1\ny = 2\n")
        rc, out = run(["--design", md], mark)
        if rc == 1 and open(code).read() == "x = 1\ny = 2\n":
            ok += 1
            print(f"   T{total} 先の件が後の件の「直す前の文字」を2つにすると、1件も当たらず rc=1 → pass")
        else:
            fails.append(f"❌ 実物と合わない件 T{total}: 2か所になった件が当たった／rc={rc} code={open(code).read()!r}")

        # ★T17〜T21（2026-09-30・設計書 audit-fix-tools-target-20260930）＝道具のファイルと、走らせるコマンド
        #   道具の置き場・設計書・承認の印を、一時の置き場に替えて測る（本物の道具には1バイトも書かない）。
        g_saved = (globals()["TOOLS_DIR"], globals()["DESIGN"], globals()["APPROVED"],
                   globals()["HOOKS_DIR"], globals()["BREAKS_DIR"])
        tdir = os.path.join(tmp, ".claude", "tools")
        os.makedirs(tdir, exist_ok=True)
        globals()["TOOLS_DIR"], globals()["DESIGN"], globals()["APPROVED"] = tdir, md, mark
        globals()["HOOKS_DIR"] = os.path.join(tmp, ".claude", "hooks")
        globals()["BREAKS_DIR"] = os.path.join(tmp, ".claude", "breaks")
        os.makedirs(globals()["HOOKS_DIR"], exist_ok=True)
        os.makedirs(globals()["BREAKS_DIR"], exist_ok=True)
        try:
            tpy = os.path.join(tdir, "t.py")
            trel = os.path.relpath(tpy, ROOT)
            tfix = {"番号": "1", "対象のファイル": trel, "直す箇所": "1-1", "直す前の文字": "x = 1",
                    "4つ目": [("", "直した後の文字", "x = 2")], "根拠の抜き書き": f"{trel}:1「x = 1」", "状態": "確定"}

            def tool_case(target_line, good_mark):
                open(tpy, "w", encoding="utf-8").write("x = 1\n")
                open(md, "w", encoding="utf-8").write(f"# 見本\n\nTARGET: {target_line}\n")
                mark_of(md, mark) if good_mark else open(mark, "w", encoding="utf-8").write("0" * 64)
                return check_one(tfix)

            # T17 承認の印が合い、TARGET に在る道具のファイルには当てる
            total += 1
            ok17, why17, _c = tool_case(trel, True)
            if ok17:
                ok += 1
                print(f"   T{total} 承認と TARGET がそろった道具のファイルには当てる → pass")
            else:
                fails.append(f"❌ 道具のファイル T{total}: そろっているのに当てない（{why17}）")

            # T18 承認の印が違えば、道具のファイルには当てない
            total += 1
            ok18, why18, _c = tool_case(trel, False)
            if not ok18 and "守りの仕組みなので当てない" in why18:
                ok += 1
                print(f"   T{total} 承認の印が違えば、道具のファイルには当てない → pass")
            else:
                fails.append(f"❌ 道具のファイル T{total}: 承認の印が違うのに当たる")

            # T19 TARGET の外の道具のファイルには当てない
            total += 1
            ok19, why19, _c = tool_case("scripts/priority_rebuild/other.py", True)
            if not ok19 and "守りの仕組みなので当てない" in why19:
                ok += 1
                print(f"   T{total} TARGET の外の道具のファイルには当てない → pass")
            else:
                fails.append(f"❌ 道具のファイル T{total}: TARGET の外なのに当たる")

            # T20 走らせるコマンドは、決まった形だけ通す
            total += 1
            good = [f"python3 {os.path.relpath(tdir, ROOT)}/gen_acceptance.py --work w-1 --write",
                    f"cd {os.path.relpath(tmp, ROOT)} && python3 .claude/tools/gen_acceptance.py --selftest",
                    f"python3 {os.path.relpath(tdir, ROOT)}/gen_verbatim.py --summary w-1"]
            bad = ["rm -rf x",
                   f"python3 {os.path.relpath(tdir, ROOT)}/gen_acceptance.py --write; rm x",
                   f"python3 {os.path.relpath(tdir, ROOT)}/apply_audit_fix.py --selftest",
                   f"python3 {os.path.relpath(tdir, ROOT)}/gen_acceptance.py --write --rm",
                   f"python3 {os.path.relpath(tdir, ROOT)}/gen_acceptance.py --work",
                   f"python3 {os.path.relpath(tdir, ROOT)}/gen_acceptance.py --work $(whoami)",
                   "cd /tmp && python3 x/gen_acceptance.py --write"]
            miss = [c for c in good if command_argv(c) is None] + [c for c in bad if command_argv(c) is not None]
            if not miss:
                ok += 1
                print(f"   T{total} 走らせるコマンドは決まった形だけ通す（通す {len(good)}・止める {len(bad)}） → pass")
            else:
                fails.append(f"❌ コマンドの形 T{total}: 見分けを誤った {miss}")

            # T21 照合が通らなければ、コマンドを1つも走らせない
            total += 1
            flag = os.path.join(tmp, "ran")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc21 = run_commands([({"番号": "1"}, (tmp, ["touch", flag]))], md, check=lambda _p: False)
            if rc21 == 1 and "照合が通らない" in buf.getvalue() and not os.path.exists(flag):
                ok += 1
                print(f"   T{total} 照合が通らなければ、コマンドを1つも走らせない → pass")
            else:
                fails.append(f"❌ 照合 T{total}: 照合が通らないのに走った（rc={rc21}）")

            # ★T22〜T24（2026-09-30・設計書 audit-fix-evidence-20260930）＝根拠の照らし方
            lf = os.path.join(tmp, "ev.md")
            open(lf, "w", encoding="utf-8").write("| 甲 | 乙 | 丙 | 丁 |\n")
            # T22 「…」で区切った文が、その行に順に全部 在れば合う
            total += 1
            g22, _w22 = _cmp_line(lf, "ev.md", 1, "| 甲 | …| 丙 |")
            if g22:
                ok += 1
                print(f"   T{total} 「…」で区切った文が順に全部 在れば合う → pass")
            else:
                fails.append(f"❌ 根拠の照らし T{total}: 「…」で区切った文が在るのに合わない")
            # T23 1つでも無い・順が違えば合わない
            total += 1
            g23a, _w = _cmp_line(lf, "ev.md", 1, "| 甲 | …| 戊 |")
            g23b, _w = _cmp_line(lf, "ev.md", 1, "| 丙 | …| 甲 |")
            if not g23a and not g23b:
                ok += 1
                print(f"   T{total} 「…」で区切った文が欠ける・順が違えば合わない → pass")
            else:
                fails.append(f"❌ 根拠の照らし T{total}: 欠けた・順が違うのに合う")
            # T24 根拠が acceptance.md の行なら、監査が見た版の控えと照らす
            total += 1
            arc = os.path.join(tmp, "audited.md")
            open(arc, "w", encoding="utf-8").write("監査が見た行\n")
            globals()["AUDITED_DESIGN"] = arc
            open(code, "w", encoding="utf-8").write("x = 1\n")
            fix24 = {"番号": "1", "対象のファイル": rel, "直す箇所": "1-1", "直す前の文字": "x = 1",
                     "4つ目": [("", "直した後の文字", "x = 2")],
                     "根拠の抜き書き": ".claude/state/acceptance.md:1「監査が見た行」", "状態": "確定"}
            g24, _w24, _c = check_one(fix24)
            globals()["AUDITED_DESIGN"] = ""
            if g24:
                ok += 1
                print(f"   T{total} 設計書の行は、監査が見た版の控えと照らす → pass")
            else:
                fails.append(f"❌ 根拠の照らし T{total}: 控えと照らしていない（{_w24}）")

            # ★T25（2026-09-30・設計書 point1-one-way-20260930-2・案A）＝当てた修正が記録に入り、
            #   記録に在る修正を hook 12 が止めない（記録に無い修正は今までどおり止める）。本物の記録には書かない。
            total += 1
            rec25 = os.path.join(tmp, "applied.json")
            rep25 = os.path.join(tmp, "zz_selftest_audit_report.md")
            open(code, "w", encoding="utf-8").write("x = 1\n")
            open(rep25, "w", encoding="utf-8").write(
                "# 見本\n\n## 8. 修正の指示\n\n### Major\n\n#### 修正 1\n"
                f"対象のファイル: {rel}\n直す箇所: 1\n直す前の文字:\n~~~\nx = 1\n~~~\n"
                f"直した後の文字:\n~~~\nx = 2\n~~~\n根拠の抜き書き: {rel}:1「x = 1」\n状態: 確定\n")
            sys.path.insert(0, os.path.join(ROOT, ".claude", "hooks"))
            import enforce_audit_fix as e12
            import apply_audit_fix as a12                  # hook 12 が読む同じ道具（__main__ とは別に読み込まれる）
            saved12 = (e12.REPORTS, a12.APPLIED_RECORD)
            e12.REPORTS, a12.APPLIED_RECORD = os.path.join(tmp, "*_audit_report.md"), rec25
            try:
                before25 = os.path.realpath(code) in e12.pending()
                n25 = _record_applied([{"report": os.path.basename(rep25), "num": "1", "file": rel, "how": "当てた"}], rec25)
                keys25 = applied_keys(rec25)
                after25 = os.path.realpath(code) in e12.pending()
            finally:
                e12.REPORTS, a12.APPLIED_RECORD = saved12
            if before25 and n25 == 1 and (os.path.basename(rep25), "1") in keys25 and not after25:
                ok += 1
                print(f"   T{total} 当てた修正が記録に入り、記録に在る修正を hook 12 が止めない → pass")
            else:
                fails.append(f"❌ 当てた記録 T{total}: 前={before25} 足した={n25} 後={after25}")

            # ★T26〜T30（2026-09-30・設計書 point2-design-to-impl-20260930）＝hook と、新しいファイル
            hpy = os.path.join(globals()["HOOKS_DIR"], "h.sh")
            hrel = os.path.relpath(hpy, ROOT)
            hfix = {**tfix, "対象のファイル": hrel, "根拠の抜き書き": f"{hrel}:1「x = 1」"}

            def hook_case(good_mark):
                open(hpy, "w", encoding="utf-8").write("x = 1\n")
                open(md, "w", encoding="utf-8").write(f"# 見本\n\nTARGET: {hrel}\n")
                mark_of(md, mark) if good_mark else open(mark, "w", encoding="utf-8").write("0" * 64)
                return check_one(hfix)

            # T26 承認と TARGET がそろった hook には当てる／印が違えば当てない
            total += 1
            ok26a, _w, _c = hook_case(True)
            ok26b, why26b, _c = hook_case(False)
            if ok26a and not ok26b and "守りの仕組みなので当てない" in why26b:
                ok += 1
                print(f"   T{total} hook は承認と TARGET がそろったときだけ当てる → pass")
            else:
                fails.append(f"❌ 道具のファイル T{total}: hook の照らしが違う（そろった={ok26a}・印が違う={ok26b}）")

            # T27 新しいファイル（直す前の文字「なし」）を、承認と NEW_FILE がそろえば作る
            total += 1
            npath = os.path.join(globals()["BREAKS_DIR"], "b_new.sh")
            nrel = os.path.relpath(npath, ROOT)
            nitems = [item(1, nrel, "なし", "直した後の文字", "#!/bin/bash\necho new", ev)]
            open(code, "w", encoding="utf-8").write("x = 1\n")
            open(md, "w", encoding="utf-8").write(design(nitems, rel).replace(
                f"TARGET: {rel}\n", f"TARGET: {rel}\nNEW_FILE: {nrel}\n"))
            mark_of(md, mark)
            rc, out = run(["--design", md], mark)
            if rc == 0 and os.path.isfile(npath) and open(npath).read() == "#!/bin/bash\necho new\n":
                ok += 1
                print(f"   T{total} 新しいファイルを作る（承認と NEW_FILE がそろったとき） → pass")
            else:
                fails.append(f"❌ 新しいファイル T{total}: 作れない（rc={rc}）{out[-200:]}")

            # T28 同じ設計書をもう1回 当てると、当て済みとして rc=0（2回目の承認の後に、足した件だけを当てられる）
            total += 1
            rc, out = run(["--design", md], mark)
            if rc == 0 and "もう当て終わっている" in out:
                ok += 1
                print(f"   T{total} もう当て終わった件は失敗に数えない（rc=0） → pass")
            else:
                fails.append(f"❌ 新しいファイル T{total}: 2回目で rc={rc}")

            # T29 新しいファイルが別の中身でもう在れば、上書きせず1件も当てない
            total += 1
            open(npath, "w", encoding="utf-8").write("other\n")
            rc, out = run(["--design", md], mark)
            if rc == 1 and open(npath).read() == "other\n":
                ok += 1
                print(f"   T{total} 別の中身の既存ファイルは上書きしない → pass")
            else:
                fails.append(f"❌ 新しいファイル T{total}: 上書きした／rc={rc}")

            # T30 NEW_FILE に無い新しいファイルは作らない
            total += 1
            os.remove(npath)
            open(md, "w", encoding="utf-8").write(design(nitems, rel))
            mark_of(md, mark)
            rc, out = run(["--design", md], mark)
            if rc == 1 and not os.path.exists(npath):
                ok += 1
                print(f"   T{total} NEW_FILE に無い新しいファイルは作らない → pass")
            else:
                fails.append(f"❌ 新しいファイル T{total}: NEW_FILE の外なのに作った（rc={rc}）")

            # T31 承認済みの設計書に実装の指示が在る間は、hook 12 がその TARGET を CC の手の直しから守る
            total += 1
            fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
            saved31 = (e12.REPORTS, a12.DESIGN, a12.APPROVED)
            e12.REPORTS, a12.DESIGN, a12.APPROVED = os.path.join(tmp, "none_*_audit_report.md"), md, mark
            try:
                in31 = os.path.realpath(code) in e12.pending()
                open(mark, "w", encoding="utf-8").write("0" * 64)
                out31 = os.path.realpath(code) in e12.pending()
            finally:
                e12.REPORTS, a12.DESIGN, a12.APPROVED = saved31
            if in31 and not out31:
                ok += 1
                print(f"   T{total} 承認済みの設計書の TARGET は hook 12 が守る（承認が外れたら守らない） → pass")
            else:
                fails.append(f"❌ hook 12 T{total}: 承認中={in31} 承認が外れた後={out31}")

            # T32（2026-09-30・工事 cp53-fix-20260930）＝まだ無いファイルは、置き場のフォルダが直下にだけ在れば直下にする
            #   （T27 は置き場を一時フォルダにしたので、本物の置き場 .claude/breaks の新しいファイルを試していなかった）
            total += 1
            p32 = repo_path(".claude/breaks/zz_not_yet_made.sh")
            if p32 == os.path.join(ROOT, ".claude/breaks/zz_not_yet_made.sh"):
                ok += 1
                print(f"   T{total} まだ無い壊すプログラムの置き場は直下の .claude/breaks → pass")
            else:
                fails.append(f"❌ 置き場 T{total}: まだ無いファイルが直下にならない（{p32}）")

            # T33（2026-09-30・工事 point4-hand-label-20260930）＝当てなかった件に手書きの印が付く（当て終わった件には付かない）
            total += 1
            got33 = [hand_label(w) for w in ("状態が「未決」＝まこさんが決めるまで当てない",
                                             "走らせるコマンド（当てずに、打つべきコマンドとして出す）",
                                             "守りの仕組みなので当てない（x）＝私が Write ツールで直す",
                                             "もう当て終わっている（直した後の文字が実物に在る）")]
            if got33 == ["［手書き］まこさんが選ぶ", "［手書き］まこさんが打つ", "［手書き］CC が書く", ""]:
                ok += 1
                print(f"   T{total} 当てなかった件に［手書き］の印が付く（当て終わった件には付かない） → pass")
            else:
                fails.append(f"❌ 手書きの印 T{total}: {got33}")

            # T34（2026-09-30・工事 point4-fix-label-20260930）＝守りの仕組みの相手でも、もう当て終わっている件は「もう当て終わっている」
            total += 1
            f34 = {"番号": "1", "重さ": "Major", "対象のファイル": ".claude/hooks/enforce_audit_fix.py", "状態": "確定",
                   "直す前の文字": "zz_not_in_the_file", "根拠の抜き書き": "",
                   "4つ目": [("", "直した後の文字", "def pending() -> dict:")]}
            ok34, why34, _c = check_one(f34)
            if not ok34 and why34.startswith("もう当て終わっている") and hand_label(why34) == "":
                ok += 1
                print(f"   T{total} 守りの仕組みの相手でも、当て終わった件は「もう当て終わっている」 → pass")
            else:
                fails.append(f"❌ 当て終わりの印 T{total}: {why34}")

            # T35（同）＝逐語のファイルを相手にした件は当てず、「［手書き］次の案に まこさんの OK が要る」
            total += 1
            f35 = dict(f34, **{"対象のファイル": ".claude/state/verbatim/zz_work/okd_zz.txt"})
            ok35, why35, _c = check_one(f35)
            if not ok35 and why35.startswith("逐語のファイル") and hand_label(why35) == "［手書き］次の案に まこさんの OK が要る":
                ok += 1
                print(f"   T{total} 逐語のファイルは当てず、次の案に まこさんの OK が要ると出る → pass")
            else:
                fails.append(f"❌ 逐語のファイル T{total}: {why35}")

            # T36（2026-09-30・工事 point4-record-applied-20260930）＝当てた記録に在る件は、実物に直した後の文字が無くても「もう当て終わっている」
            total += 1
            _record_applied([{"report": "zz_t36_audit_report.md", "num": "9", "file": ".claude/hooks/enforce_audit_fix.py", "how": "当てた"}])
            f36 = dict(f34, **{"番号": "9", "4つ目": [("", "直した後の文字", "zz_absent_in_the_file")]})
            globals()["CURRENT_REPORT"] = "zz_t36_audit_report.md"
            try:
                ok36, why36, _c = check_one(f36)
            finally:
                globals()["CURRENT_REPORT"] = ""
            ok36b, why36b, _c = check_one(f36)
            if not ok36 and why36.startswith("もう当て終わっている") and why36b.startswith("守りの仕組みなので"):
                ok += 1
                print(f"   T{total} 当てた記録に在る件は、実物に文字が無くても「もう当て終わっている」 → pass")
            else:
                fails.append(f"❌ 当てた記録 T{total}: 記録あり={why36} 記録を見ない={why36b}")

            # T37（2026-09-30・工事 point5-report-direct-20260930）＝使わなくなった元データを相手にした件は全件を止めず［手書き］で分け、ほかの件は当てる
            total += 1
            fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev),
                   item(2, "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json", "zz_old", "直した後の文字", "zz_new", ev)])
            rc37, out37 = run(["--design", md], mark)
            if (open(code).read() == "x = 2\n" and "使わなくなった元データなので当てない" in out37
                    and "［手書き］CC が写す" in out37 and "実物と合わない件が" not in out37):
                ok += 1
                print(f"   T{total} 使わなくなった元データの件は［手書き］で分け、ほかの件は当てる → pass")
            else:
                fails.append(f"❌ 使わなくなった元データ T{total}: rc={rc37} {out37[-200:]}")

            # T38（2026-09-30・工事 point5-report-direct-20260930）＝確かめのコマンド（scripts の道具・パスの値）も決まった形なら通し、外は止める
            total += 1
            sdk38, td38 = os.path.relpath(SDK, ROOT), os.path.relpath(tdir, ROOT)
            good38 = [f"python3 {td38}/gen_s22_map.py --verify",
                      f"python3 {td38}/run_breaks.py --design .claude/state/acceptance.md --measure-only",
                      f"cd {sdk38} && python3 scripts/priority_rebuild/verify_design_contract.py --diff {ROOT}/.claude/state/acceptance.md",
                      f"cd {sdk38} && python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest",
                      f"cd {sdk38} && python3 scripts/priority_rebuild/leak_causality_diag.py"]
            bad38 = [f"python3 {td38}/run_breaks.py --design ../../x --measure-only",
                     f"cd {sdk38} && python3 scripts/priority_rebuild/verify_design_contract.py --diff /etc/passwd",
                     f"cd {sdk38} && python3 scripts/priority_rebuild/score.py --selftest",
                     f"python3 {td38}/gen_acceptance.py"]
            miss38 = [c for c in good38 if command_argv(c) is None] + [c for c in bad38 if command_argv(c) is not None]
            if not miss38:
                ok += 1
                print(f"   T{total} 確かめのコマンドも決まった形なら通し、外は止める（通す {len(good38)}・止める {len(bad38)}） → pass")
            else:
                fails.append(f"❌ 確かめのコマンド T{total}: 見分けを誤った {miss38}")

            # T39（2026-09-30・工事 point5-report-direct-20260930）＝印の対象のファイルを直したら G2 → H2 を走らせるコマンドに足す（対象でなければ足さない）
            total += 1
            g39 = os.path.join(tmp, "g2_zz.json")
            json.dump({"files": [rel]}, open(g39, "w", encoding="utf-8"))
            got39 = []
            saved39 = (globals()["PASS_MARKS"], globals()["run_commands"])
            globals()["run_commands"] = lambda cmds, *a, **k: (got39.append(" ".join(" ".join(x[1][1][1:]) for x in cmds)) or 0)
            try:
                globals()["PASS_MARKS"] = (g39,)
                fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
                rc39, out39 = run(["--design", md], mark)
                globals()["PASS_MARKS"] = ()
                fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
                rc39b, out39b = run(["--design", md], mark)
            finally:
                globals()["PASS_MARKS"], globals()["run_commands"] = saved39
            if (len(got39) == 2 and "gen_signal_families.py --verify" in got39[0] and "leak_causality_diag.py" in got39[0]
                    and got39[1] == "" and "G2 → H2 の印を取り直す" in out39):
                ok += 1
                print(f"   T{total} 印の対象のファイルを直したら G2 → H2 を走らせる（対象でなければ走らせない） → pass")
            else:
                fails.append(f"❌ 印の取り直し T{total}: {got39} rc={rc39}/{rc39b}")

            # T40（2026-10-01・監査 cp54 の C-1・C-2）＝gen_regime_kb.py --write と pre_audit_check.py --run を一覧の形なら通し、外は止める
            total += 1
            good40 = [f"python3 {td38}/gen_regime_kb.py --write todo", f"python3 {td38}/gen_regime_kb.py --write laws",
                      f"python3 {td38}/pre_audit_check.py --run"]
            bad40 = [f"python3 {td38}/gen_regime_kb.py --write ../x", f"python3 {td38}/gen_regime_kb.py",
                     f"python3 {td38}/pre_audit_check.py --write"]
            miss40 = [c for c in good40 if command_argv(c) is None] + [c for c in bad40 if command_argv(c) is not None]
            if not miss40:
                ok += 1
                print(f"   T{total} gen_regime_kb.py --write と pre_audit_check.py --run を一覧の形なら通す（通す {len(good40)}・止める {len(bad40)}） → pass")
            else:
                fails.append(f"❌ 走らせる道具 T{total}: 見分けを誤った {miss40}")

            # T41（2026-10-01・監査 cp54 の C-3）＝results の下の実在する結果ファイル1つの rm だけ通し、外・不在・語が3つ以上・「..」は止める
            total += 1
            r41 = os.path.join(tmp, "results_zz")
            os.makedirs(r41, exist_ok=True)
            f41 = os.path.join(r41, "rank_zz.json")
            open(f41, "w", encoding="utf-8").write("{}")
            saved41 = globals()["RESULTS_DIR"]
            globals()["RESULTS_DIR"] = r41
            try:
                got41 = command_argv(f"rm {os.path.relpath(f41, ROOT)}")
                bad41 = [f"rm -rf {os.path.relpath(r41, ROOT)}", f"rm {os.path.relpath(r41, ROOT)}/../rank_zz.json",
                         f"rm {os.path.relpath(r41, ROOT)}/none_zz.json", "rm /etc/passwd", f"rm {rel}"]
                miss41 = [c for c in bad41 if command_argv(c) is not None]
            finally:
                globals()["RESULTS_DIR"] = saved41
            if got41 is not None and got41[1] == ["/bin/rm", os.path.realpath(f41)] and not miss41 and os.path.isfile(f41):
                ok += 1
                print(f"   T{total} results の下の結果ファイル1つの rm だけ通す（止める {len(bad41)}・まだ消していない） → pass")
            else:
                fails.append(f"❌ rm T{total}: {got41} {miss41}")

            # T42（2026-10-01・監査 cp54 の C-4）＝--report の道の新しいファイルは、承認の印が合い NEW_FILE に在るときだけ作ってよい
            total += 1
            new42 = os.path.relpath(os.path.join(tmp, "made_zz.py"), ROOT)
            md42, mark42 = os.path.join(tmp, "design42.md"), os.path.join(tmp, "approved42")
            open(md42, "w", encoding="utf-8").write(f"<!-- ARC iter=\"zz42\" -->\nTARGET: {rel}\nNEW_FILE: {new42}\n")
            mark_of(md42, mark42)
            in42 = report_new_file_ok(new42, md42, mark42)
            out42 = report_new_file_ok(rel, md42, mark42)
            open(mark42, "w", encoding="utf-8").write("0" * 64)
            bad42 = report_new_file_ok(new42, md42, mark42)
            if in42 and not out42 and not bad42:
                ok += 1
                print(f"   T{total} 新しいファイルは、承認の印が合い NEW_FILE に在るときだけ作ってよい → pass")
            else:
                fails.append(f"❌ 新しいファイルの許し T{total}: NEW_FILE に在る={in42} 無い={out42} 印が違う={bad42}")

            # T43（2026-10-01・監査 cp54 の C-4）＝見出し「足す文字」の全文でも作れる。作れない件は全件を止めずに［手書き］で分ける
            total += 1
            f43 = {"番号": "1", "重さ": "Critical", "対象のファイル": new42, "状態": "確定", "直す前の文字": "なし",
                   "根拠の抜き書き": "", "4つ目": [("", "足す文字", "print(1)\n")]}
            ok43a, _w, _c = new_file_check(f43, os.path.join(ROOT, new42))
            ok43b, _w, _c = new_file_check(dict(f43, **{"4つ目": [("", "消す文字", "x")]}), os.path.join(ROOT, new42))
            ok43c, why43c, _c = check_one(f43, run_ok=True, new_ok=False)
            if (ok43a and not ok43b and not ok43c and why43c.startswith("新しいファイルは")
                    and hand_label(why43c) == "［手書き］設計書に NEW_FILE を書いて承認をもらう" and not os.path.exists(os.path.join(ROOT, new42))):
                ok += 1
                print(f"   T{total} 足す文字の全文でも作れ、作れない件は［手書き］で分ける（本物には作らない） → pass")
            else:
                fails.append(f"❌ 足す文字の新しいファイル T{total}: {ok43a} {ok43b} {ok43c} {why43c}")

            # T44（2026-10-01・監査 cp55 の R-5）＝行を消す直しは、直す前の文字が残っていれば当て終わりと見ず、当てた後は当て終わりと見る
            total += 1
            clear_rec()                                       # ★2026-10-06（穴 B）＝前の場面の試しの記録を残さない
            open(code, "w", encoding="utf-8").write("a = 1\nb = 2\nc = 3\n")
            f44 = {"番号": "1", "重さ": "Critical", "対象のファイル": rel, "状態": "確定", "直す前の文字": "b = 2\nc = 3\n",
                   "根拠の抜き書き": "", "4つ目": [("", "直した後の文字", "c = 3\n")]}
            ok44a, why44a, _c = check_one(f44)
            pre44 = already_applied(f44)
            open(code, "w", encoding="utf-8").write("a = 1\nc = 3\n")
            ok44b, why44b, _c = check_one(f44)
            post44 = already_applied(f44)
            if ok44a and not pre44 and not ok44b and why44b.startswith("もう当て終わっている") and post44:
                ok += 1
                print(f"   T{total} 行を消す直しは、直す前の文字が残っていれば当て終わりと見ず、当てた後は当て終わりと見る → pass")
            else:
                fails.append(f"❌ 行を消す直し T{total}: 前={ok44a}/{pre44} 後={ok44b}/{post44} {why44a} {why44b}")

            # T45（監査 CP62 の Q12・3f0ac4c）＝直した後の文字と同じ文字が別の行に在っても、直す前の文字が残っていれば当て終わりと見ない
            total += 1
            clear_rec()                                       # ★2026-10-06（穴 B）＝前の場面の試しの記録を残さない
            open(code, "w", encoding="utf-8").write("k = p[0]\nq = p[1] + 10\n")
            f45 = {"番号": "1", "重さ": "Critical", "対象のファイル": rel, "状態": "確定", "直す前の文字": "q = p[1] + 10\n",
                   "根拠の抜き書き": "", "4つ目": [("", "直した後の文字", "k = p[0]\n")]}
            ok45, why45, _c = check_one(f45)
            if ok45 and not already_applied(f45):
                ok += 1
                print(f"   T{total} 直した後の文字が別の行に在っても、直す前の文字が残っていれば当てる → pass")
            else:
                fails.append(f"❌ 別の行の同じ文字 T{total}: {ok45} {why45}")

            # T46（監査 CP62 の Q12・e353f27）＝行を消す直し（直した後の文字が空）は、当てた記録に在れば当て終わり・無ければ実物と合わない件
            total += 1
            open(code, "w", encoding="utf-8").write("a = 1\n")
            f46 = {"番号": "46", "重さ": "Critical", "対象のファイル": rel, "状態": "確定", "直す前の文字": "b = 2\n",
                   "根拠の抜き書き": "", "4つ目": [("", "直した後の文字", "")]}
            globals()["CURRENT_REPORT"] = "design:zz46"
            try:
                ok46a, why46a, _c = check_one(f46)
                _record_applied([{"report": "design:zz46", "num": "46", "file": rel, "how": "当てた"}])
                ok46b, why46b, _c = check_one(f46)
            finally:
                globals()["CURRENT_REPORT"] = ""
            if (not ok46a and why46a.startswith("直す前の文字が実物に 0 か所") and not ok46b
                    and why46b == "もう当て終わっている（当てた記録に在る）"):
                ok += 1
                print(f"   T{total} 行を消す直しは、当てた記録に在れば当て終わり・無ければ実物と合わない件 → pass")
            else:
                fails.append(f"❌ 行を消す直しと当てた記録 T{total}: 記録なし={why46a} 記録あり={why46b}")

            # T47（2026-10-06・156回目・穴 B・まこさん「よい」）＝設計書の道で、当てた後に実物が手で直され、直した後の文字が
            #   実物から消えて直す前の文字だけが残った件は、同じ工事名の当てた記録に在れば当て終わり（二重に差し込まない）。
            #   記録が無ければ今までどおり当たる。監査結果の道（--report）は今までどおり（行を消す直しだけ記録を見る）。
            total += 1
            clear_rec()
            md47 = os.path.join(tmp, "design47.md")
            open(md47, "w", encoding="utf-8").write("<!-- ARC iter=\"zz47\" -->\n# 見本\n")
            open(code, "w", encoding="utf-8").write("x = 1\n")                # 直した後の文字（x = 1\ny = 2\n）は手直しで消えた
            f47 = {"番号": "41", "重さ": "Critical", "対象のファイル": rel, "状態": "確定", "直す前の文字": "x = 1\n",
                   "根拠の抜き書き": "", "4つ目": [("", "直した後の文字", "x = 1\ny = 2\n")]}
            d47 = globals()["DESIGN"]
            globals()["DESIGN"] = md47
            try:
                ok47a, why47a, _c = check_one(f47)                                    # 記録なし → 当たる
                _record_applied([{"report": "design:zz47", "num": "41", "file": rel, "how": "当てた"}])
                ok47b, why47b, _c = check_one(f47)                                    # 記録あり → 当て終わり
                globals()["CURRENT_REPORT"] = "zz47_audit_report.md"
                ok47c, why47c, _c = check_one(f47)                                    # 監査結果の道 → 今までどおり当たる
            finally:
                globals()["CURRENT_REPORT"] = ""
                globals()["DESIGN"] = d47
            if (ok47a and not ok47b and why47b == "もう当て終わっている（当てた記録に在る）" and ok47c):
                ok += 1
                print(f"   T{total} 設計書の道は、当てた記録に在る件を、直した後の文字が消えていても当て終わりと見る（監査結果の道は今までどおり） → pass")
            else:
                fails.append(f"❌ 設計書の道と当てた記録 T{total}: 記録なし={ok47a}/{why47a} 記録あり={ok47b}/{why47b} 監査結果={ok47c}/{why47c}")

            # T48（2026-10-17・186回目・まこさん「設計書はなしでよい」）＝engine_tuner_gen.py・engine_tuner_exec.py に当てる件は、
            #   型の表の承認が今の表と合わなければ1件も書かない（G1＝enforce_signal_table_gate と同じ照らし）。
            #   直す前は、この道具が python の中で書くので、Write・Edit にだけ掛かる G1 の hook の外を通っていた。
            total += 1
            clear_rec()
            code48 = os.path.join(tmp, "engine_tuner_gen.py")
            rel48 = os.path.relpath(code48, ROOT)
            ts_saved = globals().get("table_status")
            try:
                open(code48, "w", encoding="utf-8").write("x = 1\n")
                items48 = [item(1, rel48, "x = 1", "直した後の文字", "x = 2", f"{rel48}:1「x = 1」")]
                open(md, "w", encoding="utf-8").write(design(items48, rel48))
                mark_of(md, mark)
                globals()["table_status"] = lambda: (False, "見本の未承認")
                rc48a, out48a = run(["--design", md], mark)
                body48a = open(code48).read()
                clear_rec()
                globals()["table_status"] = lambda: (True, "見本の承認済み")
                rc48b, _out48b = run(["--design", md], mark)
                body48b = open(code48).read()
            finally:
                if ts_saved is None:
                    globals().pop("table_status", None)
                else:
                    globals()["table_status"] = ts_saved
            if rc48a == 1 and "型の表の承認" in out48a and body48a == "x = 1\n" and rc48b == 0 and body48b == "x = 2\n":
                ok += 1
                print(f"   T{total} engine_tuner_gen.py に当てる件は、型の表の承認が合わなければ1件も書かない（合えば当たる） → pass")
            else:
                fails.append(f"❌ 型の表の承認 T{total}: 未承認 rc={rc48a} 中身={body48a!r} ／ 承認済み rc={rc48b} 中身={body48b!r}")
        finally:
            (globals()["TOOLS_DIR"], globals()["DESIGN"], globals()["APPROVED"],
             globals()["HOOKS_DIR"], globals()["BREAKS_DIR"]) = g_saved
            globals()["AUDITED_DESIGN"] = ""
    finally:
        globals()["APPLIED_RECORD"] = rec_saved
        shutil.rmtree(tmp, ignore_errors=True)
    for x in fails:
        print(x)
    print(f"\n{'✅' if ok == total else '❌'} selftest {ok}/{total} pass")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
