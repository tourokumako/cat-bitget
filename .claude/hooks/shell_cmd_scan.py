#!/usr/bin/env python3
"""shell_cmd_scan.py — コマンドの文字列から「本当に走らせる戦略ファイル」だけを取り出す

新設: 2026-08-22（50回目・まこさん決定 A・`next_step.md` §6 の24番）。

★何が問題だったか（実測・2026-08-22 に私自身が止められた）
  `require_tag_for_experiment.sh` は、コマンドの文字列を2つの目で見ていた。
    ①どこかに `python` の語が在るか
    ②どこかに 戦略の `.py` の名前が在るか
  **この2つが別の場所に在っても「実験だ」と判断していた。**
  実際に止まった例＝1つのコマンドの中に、①ファイルを読む `sed -n ... e38_priority_stack.py` と
  ②設定ファイルを読む `python3 -c ...` が並んでいただけ。**どちらも実験ではない。**
  41番（H2 の hook が説明の文で誤って止めた件）と同じ型。

★直し方（2つ重ねる）
  1. **ヒアドキュメントの中身と、`#` から始まる注記を先に外す。**
     ＝文書やテストの文に「python3 …/e38_… .py --tag v1」と書いただけで止まるのを防ぐ。
  2. **`python` と同じ ひとかたまり の中で、その `.py` が引数として続いているときだけ拾う。**
     ＝`|` `&` `;` 改行 で区切られた別のかたまりに在る名前は拾わない。
     （`pdca_mark.py` が probe を拾うときと同じ書き方＝`python[0-9.]*[ \\t]+[^|&;\\n]*_probe\\.py`）

★限界（正直に書きます）
  ①引用符の中身は外していません＝`python3 "…/e38_x.py"` のように引用符つきで渡す本物の実行を
    拾えなくなるためです。**本物を見逃さない側に倒しました。**
  ②`eval` や変数に入れてからの実行は追えません（`$SCRIPT` の中身までは見ません）。

使い方
  python3 shell_cmd_scan.py --strategy   # 標準入力のコマンド文字列から、走らせる戦略名を1つ出す（無ければ空）
  python3 shell_cmd_scan.py --selftest
"""
from __future__ import annotations

import re
import sys

# 戦略ファイルの名前（e3N_ / strat_ / measure_）。分析の probe と deep_analysis は戦略ではない。
STRAT_RE = r"(?:e3[0-9][a-z0-9_]*|strat_[a-z0-9_]*|measure_[a-z0-9_]*)\.py"
NOT_STRAT_RE = re.compile(r"(_probe|_deep_analysis)\.py$")
# python の後ろに、区切り（| & ; 改行）を挟まずに続く .py だけを拾う
RUN_RE = re.compile(r"python[0-9.]*[ \t]+[^|&;\n]*?(" + STRAT_RE + r")")
HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def strip_heredocs(cmd: str) -> str:
    """ヒアドキュメント（<<'EOF' … EOF）の中身を外す。終わりの行が無ければ、そこから先を全部 外す。"""
    lines = cmd.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = HEREDOC_RE.search(line)
        if m:
            delim = m.group(2)
            i += 1
            while i < len(lines) and lines[i].strip() != delim:
                i += 1          # 中身は捨てる
            if i < len(lines):
                out.append(lines[i])   # 終わりの行だけ残す（形を保つ）
        i += 1
    return "\n".join(out)


def strip_comments(cmd: str) -> str:
    """行の先頭が # の注記を外す（行の途中の # は URL などに使われるので触らない）。"""
    return "\n".join("" if ln.lstrip().startswith("#") else ln for ln in cmd.split("\n"))


def effective(cmd: str) -> str:
    """見るべき部分だけにしたコマンドの文字列。"""
    return strip_comments(strip_heredocs(cmd))


def find_strategy(cmd: str) -> str:
    """走らせる戦略ファイルの名前。実験でなければ空文字。"""
    for m in RUN_RE.finditer(effective(cmd)):
        name = m.group(1)
        if not NOT_STRAT_RE.search(name):
            return name
    return ""


def _selftest() -> int:
    ng: list[str] = []

    def chk(name: str, cond: bool, got: object = "") -> None:
        print(("  ✅ " if cond else "  ❌ ") + name + (f"（実際＝{got!r}）" if not cond else ""))
        if not cond:
            ng.append(name)

    print("[shell_cmd_scan] わざと壊して止まるか試すテスト")

    g = find_strategy("python3 scripts/priority_rebuild/e38_priority_stack.py --tag v1")
    chk("T1 本物の実験は拾う", g == "e38_priority_stack.py", g)

    g = find_strategy("python3 scripts/priority_rebuild/e37_scalp.py")
    chk("T2 タグ無しの本物も拾う", g == "e37_scalp.py", g)

    # ★実際に止められた形（2026-08-22）
    real = ("sed -n '95,115p' scripts/priority_rebuild/e38_priority_stack.py\n"
            "python3 -c \"import json; print(1)\"")
    g = find_strategy(real)
    chk("T3 ★ファイルを読むだけ＋別の行の python では拾わない（実際に止められた形）", g == "", g)

    g = find_strategy("cat scripts/priority_rebuild/e38_priority_stack.py | python3 -c 'pass'")
    chk("T4 パイプの向こうの python では拾わない", g == "", g)

    hd = ("cat >> memo.md <<'EOF'\n"
          "python3 scripts/priority_rebuild/e38_priority_stack.py --tag v1\n"
          "EOF\n")
    g = find_strategy(hd)
    chk("T5 ★ヒアドキュメントに書いた例では拾わない", g == "", g)

    g = find_strategy("# python3 scripts/priority_rebuild/e37_scalp.py\nls")
    chk("T6 注記に書いた例では拾わない", g == "", g)

    g = find_strategy("python3 /tmp/foo_probe.py")
    chk("T7 分析の probe は戦略でない", g == "", g)

    g = find_strategy("python3 scripts/priority_rebuild/e37_deep_analysis.py")
    chk("T8 deep_analysis は戦略でない", g == "", g)

    g = find_strategy("echo hi && python3 scripts/priority_rebuild/e36_short_oscillation.py --tag a")
    chk("T9 && の後ろの本物は拾う", g == "e36_short_oscillation.py", g)

    g = find_strategy("python3 -m py_compile scripts/priority_rebuild/e38_priority_stack.py")
    chk("T10 ★py_compile も python の引数なので拾う（.sh 側が別に通す）",
        g == "e38_priority_stack.py", g)

    hd2 = "cat <<EOF\npython3 measure_x.py\n"       # 終わりの行が無い
    g = find_strategy(hd2)
    chk("T11 ヒアドキュメントの終わりが無ければ、そこから先を全部 外す", g == "", g)

    print(f"[shell_cmd_scan] {11 - len(ng)}/11 pass")
    return 1 if ng else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.stdout.write(find_strategy(sys.stdin.read()))
