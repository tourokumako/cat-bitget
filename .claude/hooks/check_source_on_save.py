#!/usr/bin/env python3
# check_source_on_save.py — 「元」を保存する瞬間に、後でそれを読む「作るプログラム」と同じ検査を掛ける
#   （PreToolUse Write|Edit|MultiEdit・2026-10-10・165回目）
#
# まこさん指示（2026-10-10・逐語）＝
#   「毎回ミスが発生する依頼は明確だと思うので、その依頼の前に強制でプログラムを走らせる用にするようにできない？」
#   「毎回、設計書の元から設計書を作る時とか、依頼書の元から依頼書を作る時に、承認後にミスが発覚して、
#     再度やり直しをしていることが多いように思う。」
#   「どういうミスをしてるのか検証して、ミスをしないような仕組みを作る」「この強制は作って」
#
# なぜ要るか（検証＝session_worklog_20261010.md の §42 の型 C・10回）＝
#   作るプログラム（依頼書を作る gen_audit_docs.py ほか）は、元の形が違えば止める（fail-closed）。
#   ただし止まるのは「作る時」で、元を書いた時ではなかった。監査依頼の手書きの文書は、まこさんの OK を
#   いただいた後に初めて作るプログラムに掛かる。2026-10-10 は、OK の後に出どころの番号で止まり、
#   OK をいただいた文書を直すことになった（2026-10-06 にも同じ出どころの誤りが在った）。
#
# 何をするか＝次の「元」を Write・Edit・MultiEdit で保存しようとした瞬間に、保存した後の中身で検査する。
#   ① 監査依頼の手書きの文書（工事のフォルダの「監査依頼の手書き（設計書の監査｜実装の監査）.md」）
#      ＝工事のフォルダを一時の置き場に写し、保存した後の中身を置き、依頼書を作るプログラムの
#        build_design_src を、依頼書を作る時と同じ引数で呼ぶ（依頼書も元データも書かない）。
#        止まれば、その文を全部 出して保存を止める。
#   ★判定は書き写していない＝作るプログラムの関数をそのまま呼ぶ（作るプログラムを直せば、ここも同じに動く）。
#
# 止めないとき（fail-open）＝この検査そのものが走らせられないとき（作るプログラムを読み込めない・
#   その工事の設計書が、いまの設計書にも承認の控えにも無い）。理由は標準エラーに1行 出す。
#   2026-10-01 に、止め続ける hook が進行を妨げた（まこさん「強制の不具合で進行が妨げられている」）ので、
#   検査が見つけた不足だけで止め、検査が走らないことでは止めない。
#   ★2026-10-17（185回目）＝Write の中身が空のとき（試しの道具の --write を --content なしで打った形）も止めない。
#     標準エラーに1行、中身で試す口を知らせる。
#
# 使い方:
#   hook        ：標準入力に PreToolUse の json
#   手で確かめる：python3 .claude/hooks/check_source_on_save.py --check <元のファイル> [--as <中身を書いたファイル>]
#                 （--as を省くと、いまのファイルの中身で見る。終了コード 0＝通る／1＝不足が在る／3＝走らせられない）
#
# 限界（正直に）＝
#   ・見るのは、作るプログラムが見る物（表の形・出どころの番号・必読のパスと行の範囲・問いの形）まで。
#     中身が正しいかは見ない（見直し表・監査・まこさんの目）。
#   ・Bash で書く道は見ない（リダイレクトで書けば通る＝明示の違反・git の差分には出る）。
#   ・いまの相手は①だけ。設計書の元（やることの表.md）は、設計書を作るプログラムの検査が1つの関数に
#     切り出されていないので、まだ入れていない（session_worklog_20261010.md の §43）。
#   ・この hook 自身を書き換えれば無効にできる（git の差分には出る）。
import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
HAND_RE = re.compile(r"^監査依頼の手書き（(.+)）\.md$")


def is_hand(path: Path) -> bool:
    """工事のフォルダ（…/verbatim/<工事名>/）の、監査依頼の手書きの文書か。"""
    return bool(HAND_RE.match(path.name)) and path.parent.parent.name == "verbatim"


def text_after(tool: str, ti: dict, path: Path) -> str:
    """保存した後の中身（Write＝渡された全文／Edit・MultiEdit＝いまの中身に置き換えを当てた文）。"""
    if tool == "Write":
        return ti.get("content") or ""
    try:
        t = path.read_text(encoding="utf-8")
    except OSError:
        t = ""
    for e in (ti.get("edits") or []) if tool == "MultiEdit" else [ti]:
        old, new = e.get("old_string") or "", e.get("new_string") or ""
        t = t.replace(old, new) if e.get("replace_all") else t.replace(old, new, 1)
    return t


def hand_problems(path: Path, text: str) -> tuple:
    """監査依頼の手書きの文書を、依頼書を作るプログラムと同じ読み方で照らす。
    戻り＝(不足の一覧, 走らせられなかった理由)。どちらも空なら通る。本物には何も書かない。"""
    work = path.parent.name
    label = HAND_RE.match(path.name).group(1)
    sys.path.insert(0, str(ROOT / ".claude/tools"))
    try:
        import gen_audit_docs as gad
        import gen_acceptance as ga
    except Exception as e:                                   # noqa: BLE001
        return [], f"作るプログラムを読み込めない（{type(e).__name__} {e}）"
    kind = next((k for k, (lb, _s) in gad.KINDS.items() if lb == label), None)
    if kind is None:
        names = "・".join(lb for lb, _s in gad.KINDS.values())
        return [f"ファイルの名前の（{label}）が、依頼書の種類（{names}）のどれでもない"], ""
    if not path.parent.is_dir():
        return [], f"工事のフォルダが無い（{path.parent}）"
    acc = ROOT / ".claude/state/acceptance.md"
    arch = SDK / f".claude/ratchet/acceptance_archive/{work}.md"
    cur = acc.read_text(encoding="utf-8") if acc.is_file() else ""
    if f'iter="{work}"' in cur:
        dp = None                                            # いまの設計書が、この工事の設計書
    elif arch.is_file():
        dp = str(arch)                                       # 承認の控え
    else:
        return [], f"工事 {work} の設計書が、いまの設計書にも承認の控えにも無い"
    tmp = Path(tempfile.mkdtemp(prefix="_src_on_save_"))
    real = (ga.gv.VERBATIM_DIR, ga.gv.ARCHIVE_DIR)
    try:
        dst = tmp / "verbatim" / work
        shutil.copytree(path.parent, dst)
        (dst / path.name).write_text(text, encoding="utf-8")
        ga.gv.VERBATIM_DIR, ga.gv.ARCHIVE_DIR = tmp / "verbatim", tmp / "none"
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                gad.build_design_src(kind, 0, work=work, design_path=dp, show_path=dp)
        except SystemExit as e:
            return [str(e)], ""
        except Exception as e:                               # noqa: BLE001
            return [], f"依頼書を作るプログラムが途中で落ちた（{type(e).__name__} {e}）"
    finally:
        ga.gv.VERBATIM_DIR, ga.gv.ARCHIVE_DIR = real
        shutil.rmtree(tmp, ignore_errors=True)
    return [], ""


def check(path: Path, text: str) -> tuple:
    """相手のファイルなら検査する。戻り＝(相手の名前 or "", 不足の一覧, 走らせられなかった理由)。"""
    if is_hand(path):
        bad, why = hand_problems(path, text)
        return "監査依頼の手書きの文書", bad, why
    return "", [], ""


def cli(argv: list) -> int:
    p = Path(os.path.abspath(argv[argv.index("--check") + 1]))
    src = Path(argv[argv.index("--as") + 1]) if "--as" in argv else p
    what, bad, why = check(p, src.read_text(encoding="utf-8"))
    if not what:
        print(f"相手ではない（検査しない）: {p}")
        return 0
    if why:
        print(f"⚠️ 検査を走らせられない（{what}）＝{why}")
        return 3
    for b in bad:
        print("   ❌ " + b)
    print(f"{'❌ 不足 ' + str(len(bad)) + ' 件' if bad else '✅ 通る'}（{what}・作るプログラムと同じ検査）: {p}")
    return 1 if bad else 0


def hook() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:                                        # noqa: BLE001
        return 0
    tool = data.get("tool_name") or ""
    ti = data.get("tool_input") or {}
    fp = ti.get("file_path") or ""
    if tool not in ("Write", "Edit", "MultiEdit") or not fp:
        return 0
    path = Path(os.path.abspath(fp))
    try:
        what, bad, why = check(path, text_after(tool, ti, path))
    except Exception as e:                                   # noqa: BLE001
        print(f"[元を保存する瞬間の検査] 検査が走らなかった（止めない）＝{type(e).__name__} {e}", file=sys.stderr)
        return 0
    if not what:
        return 0
    if tool == "Write" and not (ti.get("content") or ""):
        # ★2026-10-17（185回目）＝空の中身の Write は、試しの道具（try_hooks.py --write を --content なしで）の形。
        #   空の手書きの文書を本当に保存する場面は無い。検査すると「表が無い」の誤報になる（10月11日・13日）。
        print(f"[元を保存する瞬間の検査] Write の中身が空なので検査しない（止めない）。"
              f"中身で試すときは try_hooks.py --write <パス> --content <中身のファイル> か、"
              f"python3 .claude/hooks/check_source_on_save.py --check <元のファイル> --as <中身のファイル>", file=sys.stderr)
        return 0
    if why:
        print(f"[元を保存する瞬間の検査] {what}の検査を走らせられない（止めない）＝{why}", file=sys.stderr)
        return 0
    if not bad:
        return 0
    print(f"🔒 [元を保存する瞬間の検査] この{what}は、作るプログラムが読めません（まこさんにお願いする前に、全部 直してから保存する）:",
          file=sys.stderr)
    for b in bad:
        print("   " + b, file=sys.stderr)
    print("   ★同じ検査を手で走らせる口＝python3 .claude/hooks/check_source_on_save.py --check <元のファイル> --as <中身を書いたファイル>",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(cli(sys.argv) if "--check" in sys.argv else hook())
