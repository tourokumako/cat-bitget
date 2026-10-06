#!/usr/bin/env python3
"""run_breaks.py — 完成の条件の「壊すプログラム」を機械で走らせ、終了コードを控えに残す。

まこさん指名 2026-09-03（監査 cp16 の E-12・承認 36051934db6eede3）
監査の逐語
  「完成の条件の各行の壊し方をコマンドの文字列にし、承認スクリプトが実際に走らせて
    acceptance_archive/<iter>.breaks.json に終了コードを保存する。
    ✅ 済 は終了コードが0でないときだけ書ける」

なぜ要るか（実測・cp13〜cp16 で4回 続いた型）
  設計書の完成の条件の「経路」も「壊し方」も CC の自由記述だった。
  CC は18行すべてに「実経路」と書いたが、実際に走らせた証拠は1件も残っていなかった。
  監査 cp16 が実測すると、C-7① は動いておらず、C-2 は Bash 経由が8通りとも通った。
  ＝書くだけで済むなら、CC は毎回 書くだけで済ませる。
  だから「実装した」と文章で書けなくし、機械が走らせた終了コードだけを根拠にする。

やること（3つ）
  1. 設計書の完成の条件の表から「壊すプログラム」の欄を読み、1行ずつ走らせる
  2. 走らせる前と後で、触った全ファイルのハッシュ値を照らす。1つでも違えば rc=2
  3. 結果を {行番号, 壊すプログラム, 終了コード} の形で <iter>.breaks.json に書く

★壊すプログラムの凍結（まこさん指示 2026-09-03・監査 cp16 の E-12 の土台）
  走る前に、.claude/breaks/*.sh のハッシュ値を breaks_frozen.json と照らす。
  1本でも違えば rc=2。凍結が無いときも rc=2（監査 cp16 の E-9 と同じ考え方）。
  ＝CC が壊すプログラムを書き換えて、終了コードを好きな値にする道を塞ぐ。

★呼び合いを止める（まこさんの注意 2026-09-03）
  b14_breaks_tampered.sh は この道具から呼ばれ、その中で また この道具を呼ぶ。
  目印の環境変数 CAT_RUN_BREAKS_DEPTH を使い、中から呼ばれた回は凍結の照合だけして戻す。

使い方
  python3 .claude/tools/run_breaks.py --design <設計書> --iter <iter名> [--out <保存先>]
  python3 .claude/tools/run_breaks.py --freeze          # 壊すプログラムの凍結を作り直す
  python3 .claude/tools/run_breaks.py --selftest
  python3 .claude/tools/run_breaks.py --design <設計書> --measure-only --only <壊すプログラムの名前>
                                                        # 表に載った1本だけを測る（記録を書かない・2026-09-26）

限界（正直に書く）
  ①この道具自身を CC が書き換えれば無効にできる（承認ゲートの対象なので、承認が要る）
  ②壊すプログラムが「本当に測りたいものを測っているか」は、この道具には分からない
    ＝終了コードが 0 以外であることしか見ない。中身は監査が見る
  ③凍結の照合は「承認のときの版と同じか」だけ。承認の前に骨抜きにした版を凍結できる
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import pathlib
import re
import signal
import subprocess
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SDK = ROOT / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
BREAKS_DIR = ROOT / ".claude" / "breaks"
FROZEN = SDK / ".claude" / "ratchet" / "breaks_frozen.json"
ARCHIVE = SDK / ".claude" / "ratchet" / "acceptance_archive"
DESIGN = ROOT / ".claude" / "state" / "acceptance.md"

DEPTH_ENV = "CAT_RUN_BREAKS_DEPTH"
# ★2026-09-11（まこさん承認）＝120 から 600 へ。
#   直す前の 120 には、理由のコメントが1行もありませんでした（git の前の版にも同じ値）。
#   600 の根拠＝壊すプログラム11本が走らせる `engine_tuner_gen.py --selftest` の
#   実測が **7分4秒（424秒）**（2026-09-11 20:40:37〜20:47:41）。120 では必ず打ち切られます。
TIMEOUT_SEC = 600
# ★やさしく止めたあと、壊すプログラムが控えから戻し終わるのを待つ時間。
#   根拠＝`lib.sh` の戻す処理がやることは、控えのコピーとハッシュ値の照合だけ。
#   ★この 30 という数字は測っていません（余裕を多めに取っています）。
GRACE_SEC = 30

AT_START = r"^<!--\s*ACCEPT_TABLE_START\s*-->\s*$(.*?)^<!--\s*ACCEPT_TABLE_END\s*-->\s*$"

# ★2026-09-06（監査 cp23 の X-7 後半）＝列がずれた行に付ける説明の頭。
#   ここを1か所に置いて、parse_table と main が同じ文字で照らす（2か所に書き写さない）。
COL_NG = "列の数が見出しと違う"

# ★2026-10-06（156回目・まこさん「OK」・next_step §6 の249番）＝本物のファイルを仮に書き替える道具の錠。
#   なぜ要るか（実測）＝2026-10-06 16:33〜16:34 に、承認のプログラムが走らせた壊すプログラムと、CC のターンの終わりの
#     検査（require_design_check_before_approval.py の A12＝仮当てと壊すプログラム）が重なった。片方が壊した状態を、
#     もう片方が「元の中身」として控えて戻したので、observe_diag.py に壊すプログラム b128 の壊し方が残った。
#   錠を持つのは2つ＝壊すプログラムを走らせる間のこの道具と、A12 の仮当ての全体（A12 はこの部品を読み込んで使う）。
#   中から呼ばれた道具は、持ち主の印（環境の変数 REAL_WRITE_LOCK_HELD）を受け継いで取り直さない（自分の錠を待って止まらない）。
#   取れないときは最大 LOCK_WAIT_SEC 秒 待ち、取れなければ書き替えずに止める。持ち主が死んで錠だけ残ったら取り直す。
#   ★限界（正直に）＝承認のプログラムが完成の条件のコマンドを走らせる所は、この錠を見ない（CC には直せない）＝
#     A12 と重なると、本物は壊れないが、行が「未着手」のまま残ることがある。
import shutil  # noqa: E402
import time  # noqa: E402

LOCK_DIR = ROOT / ".claude" / "state" / "real_write.lock"
LOCK_ENV = "REAL_WRITE_LOCK_HELD"
LOCK_WAIT_SEC = 600
LOCK_ORPHAN_SEC = 60     # 持ち主の印が書かれないまま、この秒数を過ぎた錠は残りかすと見る（印は取った直後に書く）


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def rw_take(wait: int = LOCK_WAIT_SEC, lock_dir: pathlib.Path = None):
    """錠を取る。戻り＝True（取った）／None（親が持っている＝取らない）／False（待っても取れない）。"""
    lock_dir = lock_dir or LOCK_DIR
    if os.environ.get(LOCK_ENV):
        return None
    t0, said = time.time(), False
    while True:
        try:
            lock_dir.mkdir()
        except FileExistsError:
            try:
                owner = int((lock_dir / "pid").read_text(encoding="utf-8").strip() or "0")
            except Exception:                                # noqa: BLE001
                owner = 0
            stale = (owner and not _alive(owner)) or (
                not owner and time.time() - lock_dir.stat().st_mtime > LOCK_ORPHAN_SEC)
            if stale:
                shutil.rmtree(lock_dir, ignore_errors=True)
                continue
            if not said:
                print(f"⏳ ほかの道具が本物のファイルを仮に書き替え中なので待っています"
                      f"（{lock_dir}・持ち主 {owner or '?'}）", file=sys.stderr)
                said = True
            if time.time() - t0 > wait:
                return False
            time.sleep(1)
            continue
        (lock_dir / "pid").write_text(str(os.getpid()), encoding="utf-8")
        os.environ[LOCK_ENV] = str(os.getpid())
        return True


def rw_drop(took, lock_dir: pathlib.Path = None) -> None:
    """自分が取った錠だけを外す（親から受け継いだ錠は外さない）。"""
    if took:
        shutil.rmtree(lock_dir or LOCK_DIR, ignore_errors=True)
        os.environ.pop(LOCK_ENV, None)


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def break_scripts() -> list:
    """.claude/breaks/ の .sh を、名前の順で並べて返す。"""
    if not BREAKS_DIR.is_dir():
        return []
    return sorted(p for p in BREAKS_DIR.glob("*.sh") if p.is_file())


def freeze_breaks() -> dict:
    """壊すプログラムのハッシュ値を集めて返す（承認スクリプトが呼ぶ）。"""
    return {p.name: sha(p) for p in break_scripts()}


def check_frozen() -> list:
    """凍結と いまのハッシュ値を照らす。戻り＝食い違いの説明の一覧（空なら合っている）。

    ★凍結が無いときも「食い違い」として返す（監査 cp16 の E-9＝記録が無いときは止める）。
    """
    if not FROZEN.exists():
        return [f"壊すプログラムの凍結がありません: {FROZEN}"
                "（監査 cp16 の E-9＝記録が無いときは止める）"
                "／承認を1回 打つと作られます"]
    try:
        want = json.loads(FROZEN.read_text(encoding="utf-8"))
    except Exception as e:                                   # noqa: BLE001
        return [f"凍結が読めません: {FROZEN} ({e})"]
    want = {k: v for k, v in want.items() if not str(k).startswith("_")}
    now = freeze_breaks()
    ng = []
    for name in sorted(set(want) | set(now)):
        if name not in now:
            ng.append(f"凍結に在る壊すプログラムが実物にありません: {name}")
        elif name not in want:
            ng.append(f"凍結に無い壊すプログラムが増えています: {name}")
        elif want[name] != now[name]:
            ng.append(f"壊すプログラムが承認のときから変わっています: {name}"
                      f"（いま {now[name][:16]}… ／ 承認時 {want[name][:16]}…）")
    return ng


def parse_table(md_text: str) -> list:
    """設計書の完成の条件の表から {行番号, 壊すプログラム} を読む。

    ★読むのは機械が読む目印の中だけ（監査 cp15 の C-1）。
    """
    m = re.search(AT_START, md_text, re.S | re.M)
    if m is None:
        return []
    rows = []
    for ln in m.group(1).splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            continue
        # ★2026-09-03（まこさん指示・設計書 §3.8）＝打ち消した縦棒は、列の区切りにしない。
        #   直す前＝欄の中に書いた縦棒（前に \ を付けたもの）で列がずれ、
        #   別の欄の文字を「壊すプログラムの名前」として拾い、記録に実在しない行が1つ 増えた。
        #   まこさんの逐語＝「これは『表の書き方の問題』ではありません。実際に起きたのは
        #     記録に実在しない行が1つ 増えたことです。…記録の信頼性の問題です。」
        #   実測＝記録21行のうち、名前が入っている行が 15（本当は 14）。画面の分母も狂っていた。
        s = s.replace("\\|", "\x00")
        cells = [c.strip().replace("\x00", "\\|") for c in s.strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        rows.append(cells)
    if not rows:
        return []
    head = rows[0]
    i_no = next((i for i, c in enumerate(head) if c.strip() == "#"), 0)
    i_brk = next((i for i, c in enumerate(head) if "壊すプログラム" in c), -1)
    if i_brk < 0:
        return []
    n_col = len(head)
    out = []
    for cells in rows[1:]:
        no = cells[i_no] if i_no < len(cells) else ""
        # ★2026-09-06（監査 cp23 の X-7 後半・設計書 iter="x7-column-count-20260906"）
        #   ＝見出しと列の数が違う行は読まない。
        #   直す前は、欄の中に生の縦棒を書くと列がずれ、**別の欄の文字を
        #   「壊すプログラムの名前」として拾った**（実測＝m2c4-add-parts-20260905.breaks.json
        #   の 24-27行＝"no": "4" だけ "script": "実経路"）。
        #   2026-09-03 に打ち消した縦棒（\|）は区切りにしない直しを入れたが、
        #   生の縦棒は そのままずれていた。
        if len(cells) != n_col:
            out.append({"no": no, "script": None, "code": None,
                        "note": f"列の数が見出しと違う（見出し {n_col} 列／この行 {len(cells)} 列）"
                                "＝欄の中に生の縦棒を書いていないか（打ち消して書く）"})
            continue
        raw = cells[i_brk] if i_brk < len(cells) else ""
        name = raw.strip().strip("`")
        name = re.sub(r"（.*?）", "", name).strip().strip("`")
        if not name or name in ("—", "-", "―"):
            out.append({"no": no, "script": None, "code": None,
                        "note": "壊すプログラムが無い＝この行は済にできない"})
            continue
        out.append({"no": no, "script": name, "code": None, "note": ""})
    return out


def selftest_breaks() -> list:
    """自己テストを測る壊すプログラムの名前（監査 cp36 の M-2・2026-09-16 新設）。

    ★判定＝その .sh の中で `measure` で始まる行に `--selftest` の語があるもの。
      自己テスト以外を測るもの（数える道具・設計書の検査など）は対象にしない。
      その相手は「❌ …」の形で落ちるとは限らないため。
    """
    out = []
    for p in sorted(BREAKS_DIR.glob("b*.sh")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("measure") and "--selftest" in line:
                out.append(p.name)
                break
    return out


def lint_expect() -> list:
    """自己テストを測る壊すプログラムのうち、EXPECT_MSG が「❌」で始まらないものの名前。

    ★2026-09-16（監査 cp36 の M-2・設計書 iter="m2e2-cp36-major-20260914"）
      監査の指摘＝宣言の文字が、壊していない正常な出力にも出る（例＝「T24」は進み具合の行にも出る）。
      だから別の理由で落ちても「期待どおり」に数えられた。
      直した後＝自己テストが落ちた行だけに出る「❌」を、宣言の先頭に求める。
    ★**宣言そのものが無いものは、ここでは名指ししない。**
      理由（2026-09-16 に実測）＝EXPECT_MSG を必須にする前（2026-09-11）からある古い壊すプログラムが
      **29本** あり（b28・b29・b34〜b44・b48・b52〜b60・b62〜b67・b72・b73）、全部ここで名指しすると、
      この工事と関係のない 29本 が毎回 出て、本当に見たい件が埋もれる。
      ★宣言が無いものは、**走らせた瞬間に `expect_of` が止める**（読めなかった理由を返し、
      呼ぶ側が [STOP] にする）＝守りは既に在る。ここは「宣言は在るが弱い」件だけを見る。
    """
    bad = []
    for name in selftest_breaks():
        _rc, _means, _why, msg = expect_of(name)   # 4つ目が EXPECT_MSG（読めなければ空）
        if not msg:
            continue                               # 宣言が無い＝走らせた瞬間に止まる（上の注）
        if not msg.startswith("❌"):
            bad.append(name)
    return bad


# ★2026-09-17（仕組み1の後半・設計書 iter="breaks-target-count-20260917"・まこさん指示 2026-09-16
#   「この３つのミスを繰り返さない仕組みを作れ」・L-605・まこさん決定 2026-09-17「載っているものだけにします」）
#   ＝壊すプログラムが壊すために探している文字を取り出し、いまのコードで何か所あるかを数える。
#   なぜ要るか（実測）＝コードの行を直したのに壊すプログラムの探す文字を直さないと、探す文字が0か所になり、
#     壊すプログラムは何も壊せない（103回目の b95・2026-09-17 に見つけた b52）。手で grep するのを忘れると誰も気づかない。
HEREDOC_RE = re.compile(
    r'python3\s+-\s+("[^"\n]*"|\'[^\'\n]*\'|\S+)[^\n]*?<<\s*[\'"]?(\w+)[\'"]?[ \t]*\n(.*?)\n\2[ \t]*$',
    re.S | re.M)
BASH_VAR_RE = re.compile(r'^[ \t]*([A-Za-z_][A-Za-z_0-9]*)=("([^"\n]*)"|\'([^\'\n]*)\'|([^\s;]+))[ \t]*$', re.M)


def extract_targets(path: pathlib.Path, lib_text: str) -> list:
    """壊すプログラム1本から、python のヒアドキュメントごとに {相手のファイル, 探す文字の一覧, 数えない理由} を取り出す。

    ★探す文字＝ファイルの中身を入れた変数（`s = open(…).read()` の s）に対する
      `s.replace(A, …)`・`s.count(A)`・`A in s`／`A not in s` の A と、`re.sub(形, …, s, flags=…)` の形。
      A が文字の定数か、文字の定数を入れた変数のときだけ取る（式は取らない＝数えない）。
    ★python を構文の木で読むので、`'a\\n' 'b\\n'` の連結やエスケープは python が解いた後の文字になる
      ＝`s.replace` が実際に探す文字と同じ。
    """
    def _expand(val, env):
        return re.sub(r'\$\{?([A-Za-z_][A-Za-z_0-9]*)\}?', lambda mm: env.get(mm.group(1), mm.group(0)), val)

    def _bash_vars(src, base):
        """bash の `名前="値"` の行を上から読み、$変数 を展開した辞書を返す（`$(…)` は読まない）。"""
        env = dict(base)
        for mm in BASH_VAR_RE.finditer(src):
            val = next(g for g in (mm.group(3), mm.group(4), mm.group(5)) if g is not None)
            if "$(" in val or "`" in val:
                continue
            env[mm.group(1)] = _expand(val, env)
        return env

    text = path.read_text(encoding="utf-8", errors="ignore")
    env = _bash_vars(text, _bash_vars(lib_text or "", {}))
    out = []
    for m in HEREDOC_RE.finditer(text):
        arg = m.group(1).strip("'\"")
        target = _expand(arg, env)
        item = {"target": None if "$" in target else target, "searches": [], "skip": ""}
        if item["target"] is None:
            item["skip"] = f"相手のファイルを決められない（{arg}）"
        # ★2026-09-17（設計書 breaks-fix-found-20260917）＝相手がいまの設計書なら数えない。
        #   なぜ＝設計書は工事ごとに中身が変わるので、どの文字に合わせても次の工事で0か所になる（b89）。
        if item["target"] and os.path.normpath(item["target"]) == str(ROOT / ".claude" / "state" / "acceptance.md"):
            item["skip"] = "相手がいまの設計書（工事ごとに中身が変わる＝数えない）"
            out.append(item)
            continue
        try:
            tree = ast.parse(m.group(3))
        except SyntaxError as e:
            item["skip"] = f"python が読めない（{e.msg}）"
            out.append(item)
            continue
        consts, content = {}, set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                v = node.value
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    consts[name] = v.value
                elif (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute)
                      and v.func.attr == "read"):
                    content.add(name)

        def _val(n):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                return n.value
            if isinstance(n, ast.Name):
                return consts.get(n.id)
            return None

        def _is_content(n):
            return isinstance(n, ast.Name) and n.id in content

        def _flags(call):
            f = 0
            for kw in call.keywords:
                if kw.arg != "flags":
                    continue
                for sub in ast.walk(kw.value):
                    if (isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name)
                            and sub.value.id == "re" and hasattr(re, sub.attr)):
                        f |= getattr(re, sub.attr)
            return f

        seen = set()
        # ★2026-09-17（設計書 breaks-fix-found-20260917）＝1か所以上で壊せる形を2つ覚える。
        #   ①re.sub に count を渡していない＝当たる所を全部 消す（b27）
        #   ②s.index・s.find に渡した文字＝最初の1か所を使う（b79）
        firsts, all_subs = set(), set()
        for node in ast.walk(tree):
            got = None
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                attr, recv = node.func.attr, node.func.value
                if attr in ("index", "find") and _is_content(recv) and node.args:
                    v = _val(node.args[0])
                    if v:
                        firsts.add(v)
                if attr in ("replace", "count") and _is_content(recv) and node.args:
                    v = _val(node.args[0])
                    if v:
                        got = ("文字", v, 0)
                elif (attr == "sub" and isinstance(recv, ast.Name) and recv.id == "re"
                      and len(node.args) >= 3 and _is_content(node.args[2])):
                    v = _val(node.args[0])
                    if v:
                        got = ("形", v, _flags(node))
                        if len(node.args) < 4 and not any(k.arg == "count" for k in node.keywords):
                            all_subs.add(v)
            elif (isinstance(node, ast.Compare) and len(node.ops) == 1
                  and isinstance(node.ops[0], (ast.In, ast.NotIn)) and _is_content(node.comparators[0])):
                v = _val(node.left)
                if v:
                    got = ("文字", v, 0)
            if got and (got[0], got[1]) not in seen:
                seen.add((got[0], got[1]))
                item["searches"].append({"kind": got[0], "text": got[1], "flags": got[2]})
        for srch in item["searches"]:
            srch["all"] = srch["kind"] == "形" and srch["text"] in all_subs
            srch["first"] = srch["text"] in firsts
        if not item["searches"] and not item["skip"]:
            item["skip"] = "文字で探していない（定数の文字を replace・count・in・re.sub に渡していない）"
        out.append(item)
    return out


def count_targets(design_text: str | None = None) -> tuple:
    """全部の壊すプログラムの探す文字を、相手のファイルで数える。

    戻り＝(行の一覧, 壊せないものの名前の一覧)。
      行＝{"name", "group"（"ok"＝全部1か所／"ng"＝0か所か2か所以上が在る／"skip"＝数えない）, "items"}
    ★design_text を渡すと、壊せないものの名前の一覧は「その設計書の完成の条件の表に載っているもの」だけにする
      （まこさん決定 2026-09-17「載っているものだけにします」）。一覧の行は全部 返す（画面には全部 出す）。
    """
    lib = BREAKS_DIR / "lib.sh"
    lib_text = lib.read_text(encoding="utf-8", errors="ignore") if lib.exists() else ""
    want = None
    if design_text is not None:
        want = {r["script"] for r in parse_table(design_text) if r.get("script")}
    rows = []
    for p in break_scripts():
        if p.name == "lib.sh":
            continue
        items = extract_targets(p, lib_text)
        n_search = 0
        bad = False
        for it in items:
            body = None
            if it["target"] and pathlib.Path(it["target"]).is_file():
                body = pathlib.Path(it["target"]).read_text(encoding="utf-8", errors="ignore")
            for s in it["searches"]:
                n_search += 1
                if body is None:
                    s["count"], s["note"] = 0, "相手のファイルが無い"
                elif s["kind"] == "文字":
                    s["count"], s["note"] = body.count(s["text"]), ""
                else:
                    try:
                        s["count"], s["note"] = len(re.findall(s["text"], body, s["flags"])), ""
                    except re.error as e:
                        s["count"], s["note"] = 0, f"正規表現として読めない（{e}）"
                # ★2026-09-17（設計書 breaks-fix-found-20260917）＝全部を消す形・最初の1か所を使う形は、1か所以上で壊せる
                if s["count"] > 1 and (s.get("all") or s.get("first")):
                    s["note"] = "全部を消す形＝1か所以上で壊せる" if s.get("all") else "最初の1か所を使う形＝1か所以上で壊せる"
                elif s["count"] != 1:
                    bad = True
        group = "ng" if bad else ("ok" if n_search else "skip")
        rows.append({"name": p.name, "group": group, "items": items})
    ng = [r["name"] for r in rows if r["group"] == "ng" and (want is None or r["name"] in want)]
    return rows, ng


def expect_of(name: str) -> tuple:
    """壊すプログラムの宣言（期待する終了コードと、その意味）を読む。

    ★2026-09-08（next_step §6 の159番・監査 cp29 の §4-2 と §5-5）
      監査の逐語＝「あとで記録だけを読む人は、#12 を『壊したら検査が落ちた』と読みます。
        実際に起きたのは『壊したら土台ゲートが通った』です。**意味が反対です。**」
      直す前＝合格の決め方が「終了コードが 0 以外」の1つだけだった。
        11本は「検査が落ちる」＝0 以外で意味が合っていたので、誰も気づかなかった。
        12本目（b51）は向きが反対なので、記録も表示も逆の意味になっていた。
        さらに、中で異常が起きた終了コード（lib.sh の 99＝控えから戻せなかった）も
        「止まった」に数えていた＝b51 の「正しい成功」の 1 と見分けが付かなかった。
      直した後＝壊すプログラムが自分で「期待する終了コードと、その意味」を宣言し、
        この道具がそれと照らす。**宣言が無ければ止める（fail-closed）。**

    書き方（.sh の先頭・#! の次あたり）
      # EXPECT_RC: 1
      # MEANS: その検査が落ちた（守りが働いた）

    戻り＝(期待する終了コード or None, 意味の文, 読めなかった理由 or "")
    ★読めなかったときは、呼ぶ側が止める（この関数は例外を投げない）。
    ★限界（正直に）＝宣言した値が正しいかは見ない。CC が実測から書き写す。
      間違った値を書くと、その壊すプログラムは永久に不合格になる（合格側には倒れない）。
    """
    p = BREAKS_DIR / name
    if not p.exists():
        return None, "", f"壊すプログラムがありません: {p}", ""
    rc = means = None
    msg = ""
    for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines()[:40]:
        m = re.match(r"^#\s*EXPECT_RC:\s*(-?\d+)\s*$", ln)
        if m and rc is None:
            rc = int(m.group(1))
        m = re.match(r"^#\s*MEANS:\s*(.+?)\s*$", ln)
        if m and means is None:
            means = m.group(1)
        # ★2026-09-11（まこさん決定・案A の残り半分）＝出力に在るべき文字。
        #   なぜ要るか＝終了コードの数字だけを照らすと、**守りと関係ない所でエラーが起きて
        #   落ちた場合も「期待どおり」になる**。その文字が出力に無ければ、期待どおりに数えない。
        m = re.match(r"^#\s*EXPECT_MSG:\s*(.+?)\s*$", ln)
        if m and not msg:
            msg = m.group(1)
    if rc is None:
        return None, "", f"宣言 # EXPECT_RC: がありません: {name}", ""
    if not means:
        return None, "", f"宣言 # MEANS: がありません: {name}", ""
    if not msg:
        return None, "", (f"宣言 # EXPECT_MSG: がありません: {name}"
                          "（出力に在るべき文字・2026-09-11 に必須にした）"), ""
    return rc, means, "", msg


def match_of(code, exp, out: str = "", msg: str = "") -> bool:
    """実際の結果が、宣言した期待と一致したか（本体も番人も、ここを呼ぶ）。

    照らすもの2つ（2026-09-11 に2つ目を足した）
      ① 終了コードが宣言と同じか
      ② **出力に `EXPECT_MSG` の文字が在るか**（守りと関係ない所で落ちたものを弾く）

    ★2026-09-08（設計書 insp5-path-and-tidy-head-20260908 の N）
      ＝期待値が読めないとき（None＝壊すプログラムがまだ無い・宣言が無い）は、一致とみなさない。
      直す前＝本体に `match = (code == exp)` と直に書いてあった。ファイルが無いと
        実際の終了コードも期待値も None になるので、`None == None` が真になり
        「期待どおり」に数えた。＝承認のプログラムが完成の条件を「済」にする一方で、
        書き込みの門は同じ None を「止まっていない」と見て実装を止めた。
    ★限界（正直に）＝「壊し方が弱い」ことは、この判定では分からない（まこさんと監査の目）。
    """
    if exp is None or code != exp:
        return False
    if msg:                                     # 宣言が在れば、出力にその文字を求める
        return msg in (out or "")
    return True


def run_one(name: str, depth: int) -> tuple:
    """壊すプログラムを1本 走らせる。戻り＝(終了コード, 最後の行, 出力の全体)＝3つ。

    ★2026-09-11（まこさん承認）＝打ち切りの直し。番人 T14 が守る。

    何が起きていたか（実測 2026-09-11）
      壊すプログラム b76 が走らせる `engine_tuner_gen.py --selftest` は 7分4秒 かかり、
      打ち切り（当時 120秒）に掛かった。そのとき2つの問題が同時に出た。
        ①戻り値の数が合わず、呼ぶ側が落ちた（承認が取り消された）
        ②**壊した相手（法則ファイル）が元に戻らず**、engine_tuner の自己テストが6件 落ちた。

    なぜ戻らなかったか（GNU Bash Reference Manual の Signals の節・逐語）
      "If Bash is waiting for a command to complete and receives a signal for which a
       trap has been set, it will not execute the trap until the command completes."
      ＝bash は、待っているコマンドが完了するまで、戻す仕掛け（trap）を実行しない。
      そして直す前は `subprocess.run(timeout=)` を使っていた。Python の公式ドキュメントの逐語
      ＝"If the timeout expires, the child process will be killed and waited for."
      ＝**強制終了**なので、bash は戻す仕掛けを走らせる間もなく消えた。

    どう直したか
      `start_new_session=True`（Python 公式＝"the setsid() system call will be made in the
      child process"）で bash と その子を1つの束にし、打ち切りのときは**束ごと**
      やさしく止める。子（走っている自己テスト）が止まれば bash の待ちが終わるので、
      上の逐語のとおり bash は戻す仕掛けを実行する。
      それでも残るときだけ、最後に強制で止める。
    """
    p = BREAKS_DIR / name
    if not p.exists():
        return None, f"壊すプログラムがありません: {p}", ""
    env = dict(os.environ)
    env[DEPTH_ENV] = str(depth + 1)
    proc = subprocess.Popen(["bash", str(p)], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, env=env,
                            cwd=str(ROOT), start_new_session=True)
    try:
        out, err = proc.communicate(timeout=TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        _stop_group(proc)                       # ★束ごと やさしく止める → trap が走る
        try:
            out, err = proc.communicate(timeout=GRACE_SEC)
        except subprocess.TimeoutExpired:       # 戻し終わらないときだけ強制
            _stop_group(proc, hard=True)
            out, err = proc.communicate()
        return (None, f"時間切れ（{TIMEOUT_SEC}秒）: {name}",
                (out or "") + (err or ""))
    out_all = (out or "") + (err or "")
    tail = out_all.strip().splitlines()
    # ★2026-09-11＝出力の全体も返す（`EXPECT_MSG` を照らすため）
    return proc.returncode, (tail[-1][:200] if tail else ""), out_all


def _stop_group(proc, hard: bool = False) -> None:
    """走っている束（bash と その子）を止める。hard なら強制。

    ★束にできなかったとき（setsid が効かない環境）は、その1本だけを止める。
    """
    sig = signal.SIGKILL if hard else signal.SIGTERM
    try:
        os.killpg(os.getpgid(proc.pid), sig)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill() if hard else proc.terminate()
        except ProcessLookupError:
            pass


def pick_rows(rows: list, only) -> tuple:
    """`--only` で名指しした壊すプログラムの行だけを返す。戻り＝(走らせる行, 表に無い名前の一覧)。

    ★2026-09-26（監査 CP43 の B3-c・設計書 iter="breaks-measure-one-20260926"・まこさん指示
      「範囲外の話もこのSessionで修正してほしい」）
      なぜ要るか＝測るだけの口は、表に載った壊すプログラムを全部 1回で走らせる形しか無かった。
        束1 は4本で約16分かかり、私が前面で1回に走らせられる10分を超えるので、承認の前の検査 B1
        （require_design_check_before_approval.py）を満たせなかった。1本ずつなら10分に収まる。
    ★only が空なら、行を全部 そのまま返す（承認の経路は必ずここを通る＝今までと同じ動き）。
    ★表に無い名前は、呼ぶ側が止める（何も走らせない）。打ち間違いで0本を測って「止まった 0/0」と
      出すのを防ぐため。
    """
    if not only:
        return rows, []
    want = set(only)
    names = {r.get("script") for r in rows if r.get("script")}
    missing = sorted(want - names)
    return [r for r in rows if r.get("script") in want], missing


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="完成の条件の壊すプログラムを機械で走らせる")
    ap.add_argument("--design", default=str(DESIGN))
    ap.add_argument("--iter", dest="iter_name")
    ap.add_argument("--out")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--check-frozen", action="store_true")
    ap.add_argument("--parse-only", action="store_true")
    # ★2026-09-07（next_step §6 の150番・設計書 iter="approval-audit-plumbing-20260907"）
    #   ＝壊すプログラムを走らせて終了コードを画面に出すだけの口。
    #   **記録も凍結も1バイトも書かない。**
    #   なぜ要るか（実測）＝承認より後にコードを直したとき、壊すプログラムを走らせ直せるのが
    #     まこさんだけだった（この道具は土台ゲートの通す一覧に入っていない）。
    #     2026-09-07 に監査 cp27 が、これを理由に「壊し方を1文字も変えずに写した
    #     再現プログラム」で代行した（別枠 6-2）。
    #   ★土台ゲートは、この旗が在るときだけ この道具を通す
    #     （require_acceptance_before_impl.sh の _readonly_seg の枝。--freeze・--out が在れば止める）。
    ap.add_argument("--measure-only", action="store_true")
    # ★2026-09-16（監査 cp36 の M-2・設計書 iter="m2e2-cp36-major-20260914"）
    #   ＝自己テストを測る壊すプログラムの EXPECT_MSG が「❌」で始まるかを数える口。
    #   なぜ要るか（実測）＝直す前の宣言は「T24」のように、壊していない正常な出力にも出る文字だった。
    #     だから別の理由で落ちても「期待どおり」に数えられた（監査 cp36 の §1-4）。
    #   ★対象の判定＝その .sh の `measure` で始まる行に `--selftest` の語があるもの。
    #     自己テストは落ちた行を「  ❌ T24②: …」の形で出すので、❌ 始まりの宣言なら
    #     落ちた行にしか当たらない。
    #   ★記録も凍結も1バイトも書かない（読むだけ）。
    ap.add_argument("--lint-expect", action="store_true")
    # ★2026-09-17（仕組み1の後半・設計書 iter="breaks-target-count-20260917"）
    #   ＝壊すプログラムが探す文字を、いまのコードで数える口。記録も凍結も1バイトも書かない（読むだけ）。
    #   `--design <設計書>` を一緒に渡すと、rc を決めるのは その設計書の表に載っている壊すプログラムだけ。
    ap.add_argument("--count-targets", action="store_true")
    # ★2026-09-26（監査 CP43 の B3-c・設計書 iter="breaks-measure-one-20260926"）
    #   ＝表に載った壊すプログラムを、名前で選んで走らせる。`--measure-only` と一緒のときだけ使える。
    #   重ねてよい（`--only a.sh --only b.sh`）。★承認の経路（記録と「済」を書く）は表の全部を走らせる。
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()

    # ★2026-09-26（設計書 breaks-measure-one-20260926）＝`--only` は測るだけの口でしか使わせない。
    #   なぜ＝承認のプログラムの経路で1本だけを走らせると、記録と「済」が表の一部だけで書かれてしまう。
    if a.only and not a.measure_only:
        print("[STOP] --only は --measure-only と一緒のときだけ使えます"
              "（承認の経路は、表の全部を走らせて記録を書くため）", file=sys.stderr)
        return 2

    # ★2026-09-03（まこさん指示・設計書 §3.8 の2番）＝読むだけの口。
    #   表を読んで、拾った名前と「実物が在るか」を並べるだけ。
    #   **壊すプログラムを1本も走らせない**ので、呼び合いが起きない＝深さに関わらず動く。
    #   なぜ要るか＝これが無いと、§3.8 の完成の条件に壊すプログラムを書けない
    #   （run_breaks.py を壊すプログラムの中から呼ぶと、呼び合いを止める仕組みで
    #     測る前に戻るため）。まこさんの逐語＝「— にすると人が画面を見て確かめることに
    #     なります。この工事は『人が目で確かめる項目を完成条件に入れない』ためにやってきました。」
    #   ★限界（設計書 §9 の 1c）＝「読むだけ」という前提が本当かは、私は確かめていない。
    #     監査に確かめてもらう。
    if a.parse_only:
        md_path = pathlib.Path(a.design)
        if not md_path.exists():
            print(f"[STOP] 設計書がありません: {md_path}", file=sys.stderr)
            return 2
        rows = parse_table(md_path.read_text(encoding="utf-8"))
        if not rows:
            print("[STOP] 完成の条件の表に「壊すプログラム」の欄がありません", file=sys.stderr)
            return 2
        for r in rows:
            if not r["script"]:
                continue
            mark = "OK" if (BREAKS_DIR / r["script"]).exists() else "MISSING"
            print(f"{r['no']}\t{r['script']}\t{mark}")
        # ★2026-09-06（監査 cp23 の X-7 後半）＝列がずれた表は、読めたことにしない。
        bad = [r for r in rows if COL_NG in (r.get("note") or "")]
        if bad:
            print("[STOP] 完成の条件の表に、列の数が見出しと違う行があります"
                  "（監査 cp23 の X-7）", file=sys.stderr)
            for r in bad:
                print(f"  ❌ 行 {r['no']}: {r['note']}", file=sys.stderr)
            return 2
        return 0

    if a.lint_expect:
        bad = lint_expect()
        for name in bad:
            print(f"❌ {name}")
        if bad:
            print(f"[STOP] 自己テストを測る壊すプログラムの EXPECT_MSG が「❌」で始まっていません"
                  f"（{len(bad)} 本・監査 cp36 の M-2）", file=sys.stderr)
            return 1
        print(f"✅ 自己テストを測る壊すプログラムの EXPECT_MSG は全部「❌」で始まる"
              f"（{len(selftest_breaks())} 本）")
        return 0

    if a.count_targets:
        try:
            design_text = None
            if "--design" in argv:
                _dp = pathlib.Path(a.design)
                design_text = _dp.read_text(encoding="utf-8") if _dp.exists() else ""
            rows, ng = count_targets(design_text)
        except Exception as e:                               # noqa: BLE001
            print(f"[STOP] 探す文字を数えられませんでした（{e}）", file=sys.stderr)
            return 2
        mark = {"ok": "✅ 1か所", "ng": "❌ 0か所か2か所以上", "skip": "— 数えない"}
        for r in rows:
            print(f"{mark[r['group']]}  {r['name']}")
            for it in r["items"]:
                tgt = it["target"] or "（決められない）"
                if tgt.startswith(str(ROOT) + "/"):
                    tgt = tgt[len(str(ROOT)) + 1:]
                if it["skip"] and not it["searches"]:
                    print(f"      相手={tgt}  数えない理由＝{it['skip']}")
                for s in it["searches"]:
                    head = s["text"].replace("\n", "⏎")[:40]
                    note = f"（{s['note']}）" if s.get("note") else ""
                    print(f"      相手={tgt}  {s['kind']} {s['count']} か所{note}「{head}」")
        n = {g: sum(1 for r in rows if r["group"] == g) for g in mark}
        print(f"   1か所 {n['ok']} 本 ／ 0か所か2か所以上 {n['ng']} 本 ／ 数えない {n['skip']} 本"
              f"（合計 {len(rows)} 本）")
        if design_text is not None:
            print(f"   ★rc を決める相手＝設計書の完成の条件の表に載っている壊すプログラムだけ"
                  f"（まこさん決定 2026-09-17）＝壊せないもの {len(ng)} 本: {' '.join(ng) or 'なし'}")
        if ng:
            print(f"[STOP] 壊す相手の文字を、ちょうど1か所 見つけられない壊すプログラムがあります"
                  f"（{len(ng)} 本・L-605）: {' '.join(ng)}", file=sys.stderr)
            return 1
        return 0

    if a.freeze:
        FROZEN.parent.mkdir(parents=True, exist_ok=True)
        d = freeze_breaks()
        d["_なにこれ"] = ("承認の瞬間に凍結した、壊すプログラムのハッシュ値。"
                          "run_breaks.py が走る前に照らす（監査 cp16 の E-12）")
        FROZEN.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n",
                          encoding="utf-8")
        print(f"🧊 壊すプログラムを凍結しました: {len(d) - 1} 本 → {FROZEN.name}")
        return 0

    # ★凍結の照合は、深さに関わらず必ず行う
    # ★2026-09-16（まこさん指示「まずは上記のみ修正して良い」）＝`--measure-only` のときは照らさない。
    #   なぜか（実測 2026-09-16）＝この口は 2026-09-07 に「承認より後にコードを直したとき、
    #     壊すプログラムを走らせ直せるのが まこさんだけだった」を解くために作られた
    #     （require_acceptance_before_impl.sh:253 の逐語）。ところが凍結の照合が先に走るので、
    #     **壊すプログラムを1本でも直すと、この口が使えなかった＝作った狙いを解けていなかった。**
    #   ★守りは減らない＝この口は記録も凍結も1バイトも書かない（下の 529行で return 0＝
    #     記録を書く write_record に届かない）。「済」を決める承認の経路では、
    #     いままでどおり この照合が効く。
    ng = [] if a.measure_only else check_frozen()
    if ng:
        print("[STOP] 壊すプログラムが、承認のときの版と違います（監査 cp16 の E-12）",
              file=sys.stderr)
        for x in ng:
            print(f"  ❌ {x}", file=sys.stderr)
        return 2
    if a.check_frozen:
        print(f"✅ 壊すプログラムは承認のときのまま（{len(freeze_breaks())} 本）")
        return 0

    # ★呼び合いを止める（まこさんの注意 2026-09-03）
    depth = int(os.environ.get(DEPTH_ENV, "0") or "0")
    if depth > 0:
        print(f"✅ 凍結の照合だけ行いました（中から呼ばれた回・深さ {depth}）")
        return 0

    md_path = pathlib.Path(a.design)
    if not md_path.exists():
        print(f"[STOP] 設計書がありません: {md_path}", file=sys.stderr)
        return 2
    rows = parse_table(md_path.read_text(encoding="utf-8"))
    if not rows:
        print("[STOP] 完成の条件の表に「壊すプログラム」の欄がありません"
              "（監査 cp16 の E-12）", file=sys.stderr)
        return 2

    # ★2026-09-06（監査 cp23 の X-7 後半）＝本走でも、列がずれた表は読まずに止める。
    bad = [r for r in rows if COL_NG in (r.get("note") or "")]
    if bad:
        print("[STOP] 完成の条件の表に、列の数が見出しと違う行があります"
              "（監査 cp23 の X-7）", file=sys.stderr)
        for r in bad:
            print(f"  ❌ 行 {r['no']}: {r['note']}", file=sys.stderr)
        return 2

    # ★2026-09-26（設計書 breaks-measure-one-20260926）＝`--only` で名指しした行だけに絞る。
    #   表に無い名前が1つでも在れば、何も走らせずに止める。`--only` が無ければ全部の行のまま。
    rows, _missing = pick_rows(rows, a.only)
    if _missing:
        print(f"[STOP] --only の名前が、設計書の完成の条件の表に載っていません: {' '.join(_missing)}",
              file=sys.stderr)
        return 2

    # ★2026-10-06（156回目・249番）＝壊すプログラムを走らせる前に錠を取る（終わりに外す＝atexit）。
    _took = rw_take()
    if _took is False:
        print(f"[STOP] ほかの道具が本物のファイルを仮に書き替え中で、{LOCK_WAIT_SEC} 秒 待っても錠が取れません"
              f"（{LOCK_DIR}）＝壊すプログラムを1本も走らせません", file=sys.stderr)
        return 2
    import atexit
    atexit.register(rw_drop, _took)

    before = {p.name: sha(p) for p in break_scripts()}
    n_run = n_stop = 0
    for r in rows:
        if not r["script"]:
            continue
        # ★2026-09-08（159番）＝走らせる前に宣言を読む。
        #   **ファイルは在るのに宣言が無い**ときだけ止める（fail-closed）。
        #   ★ファイルがまだ無いときは止めない＝今までどおり run_one が None を返し、
        #     その行は「未着手」のまま残る。
        #     これを止めると、新しい壊すプログラムを作る流れ
        #     （①承認で書く権利をもらう ②書く ③承認で測る）が塞がる。
        #     実測（2026-09-08）＝止める形にしたら、b52 を書く前の承認が取り消された。
        exp, means, why, want_msg = expect_of(r["script"])
        if why and (BREAKS_DIR / r["script"]).exists():
            print(f"[STOP] 壊すプログラムの宣言を読めません（159番）: {why}", file=sys.stderr)
            print("  ★書き方＝.sh の先頭に # EXPECT_RC: <数字> と # MEANS: <その意味> の2行",
                  file=sys.stderr)
            return 2
        code, note, out_all = run_one(r["script"], depth)
        r["code"], r["note"] = code, note
        r["expect"], r["means"] = exp, means
        # ★2026-09-08（設計書 insp5-path-and-tidy-head-20260908 の N）
        #   ＝期待値が読めない行（＝壊すプログラムがまだ無い行）を、一致とみなさない。
        #   直す前＝`match = (code == exp)` だけだった。ファイルが無いと、実際の終了コードも
        #     期待値も どちらも None になるので、`None == None` が真になり「期待どおり」に数えた。
        #     ＝承認のプログラムが完成の条件を「済」にする一方で、書き込みの門は同じ None を
        #       「止まっていない」と見て実装を止めた（判定の食い違いで作業が止まった）。
        #   ★この穴は 2026-09-08 の159番の直し（期待する終了コードの宣言）が新しく作ったもの。
        r["match"] = match_of(code, exp, out_all, want_msg)
        n_run += 1
        if r["match"]:
            n_stop += 1
        mark = ("✅ 期待どおり" if r["match"]
                else ("— まだ測れない（壊すプログラムがまだ無い）" if exp is None else "❌ 期待と違う"))
        print(f"   {mark}  #{r['no']:>3}  {r['script']}  rc={code}（期待 {exp}）")
        print(f"        意味＝{means}")

    after = {p.name: sha(p) for p in break_scripts()}
    if before != after:
        print("[STOP] 走らせた後で、壊すプログラム自身が変わっています"
              "（元に戻していない）", file=sys.stderr)
        return 2

    # ★2026-09-07（150番）＝測るだけの口は、ここで終わる（記録も凍結も書かない）。
    if a.measure_only:
        print(f"   🧪 測るだけ（記録は書きません）: 止まった {n_stop}/{n_run}")
        if a.only:
            print(f"   （--only で選んだ {len(set(a.only))} 本だけを測りました）")
        return 0

    iter_name = a.iter_name or "unknown"
    out = pathlib.Path(a.out) if a.out else (ARCHIVE / f"{iter_name}.breaks.json")
    write_record(out, iter_name, rows)
    print(f"   🧪 壊して確かめた件数: {n_stop}/{n_run} → {out.name}")
    return 0


def write_record(out: pathlib.Path, iter_name: str, rows: list) -> None:
    """壊すプログラムの終了コードを、設計書の控えの隣に記録として書く。

    ★2026-09-07（next_step §6 の146番・設計書 iter="approval-audit-plumbing-20260907"）
      ＝承認スクリプトの「済」の付け方は、次の2つが**両方**そろったときだけ書く形にしてある
      （approve_impl.sh:414-424）。
        ①壊すプログラムの終了コードが 0 以外 ②その行の条件のコマンドが rc=0
      ①の材料が、ここで書く記録（<iter>.breaks.json）。
      ★この直し自体を守る完成の条件が1件も無かった（監査 cp26 の別枠の指摘3）。
      だから、書く処理を関数に切り出して番人 T8 で試せるようにした
      （承認スクリプトを直に走らせると、本物の承認の印を書いてしまうため）。
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {"_なにこれ": ("完成の条件の壊すプログラムを、承認のときに機械が走らせた記録。"
                        "match が真の行だけ「済」にできる（監査 cp16 の E-12・cp29 の §5-5）"),
         "_欄の読み方": ("code＝実際の終了コード ／ expect＝壊すプログラムが宣言した期待値 ／ "
                         "means＝その値が意味すること ／ match＝一致したか。"
                         "★b51 だけは向きが裏返っている（意味の文に書いてある）＝"
                         "1 は『検査が落ちた』ではなく『土台ゲートが通った』"),
         "iter": iter_name, "rows": rows},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


SELF_TESTS = (
    ("T1", "表から壊すプログラムの欄を読める"),
    ("T2", "「—」の行は、済にできない印を付ける"),
    ("T3", "目印が無い設計書は 0件（＝呼ぶ側が止める）"),
    ("T4", "凍結が無ければ止める"),
    ("T5", "凍結と食い違えば止める"),
    ("T6", "凍結と合っていれば通る"),
    ("T7", "打ち消した縦棒を、列の区切りにしない（幽霊の行を作らない）"),
    # ★2026-09-07（next_step §6 の146番）＝承認の「済」の材料になる記録を、本当に書くか。
    ("T8", "壊すプログラムの終了コードを、記録のファイルへ書く（済の材料が残る）"),
    ("T9", "宣言（EXPECT_RC・MEANS）の無い .sh は、理由つきで読み取りを止める"),
    ("T10", "宣言が在れば、期待する終了コードと意味の文をそのまま読み取る"),
    ("T11", "期待と違う終了コードなら、記録の match が偽になる"),
    ("T12", "壊すプログラムがまだ無い行は、一致とみなさない（期待値が読めない＝未着手のまま）"),
    # ★2026-09-11（まこさん決定・案A の残り半分）＝出力に在るべき文字を照らす
    ("T13", "出力に `EXPECT_MSG` の文字が無ければ、期待どおりに数えない"
            "（守りと関係ない所で落ちたものを弾く）／宣言が無い .sh は読み取りを止める"),
    # ★2026-09-11（まこさん承認）＝打ち切りに掛かったときの検査。
    #   なぜ要るか（実測）＝この日、私（CC）が壊すプログラムを1本 走らせたところ、
    #     中で走る自己テストが7分かかり、打ち切り（120秒）に掛かった。
    #     そのとき ①戻り値の数が合わずに落ちた ②壊した相手（法則ファイル）が
    #     元に戻らず、engine_tuner の自己テストが6件 落ちる状態になった。
    #   ★13件の中に、打ち切りを試すものが1件も無かった＝だから誰も気づかなかった。
    ("T14", "打ち切りに掛かっても、戻り値が3つ返り、壊した相手が元に戻る"),
    # ★2026-09-16（監査 cp36 の M-2・設計書 iter="m2e2-cp36-major-20260914"）
    ("T15", "自己テストを測る壊すプログラムだけを拾い、EXPECT_MSG が「❌」で始まらないものを名指しする"),
    # ★2026-09-17（仕組み1の後半・設計書 iter="breaks-target-count-20260917"・L-605）
    ("T16", "壊すプログラムが探す文字を数え、1か所／0か所・2か所以上／数えない、に分ける（表に載っているものだけで止める）"),
    # ★2026-09-26（監査 CP43 の B3-c・設計書 iter="breaks-measure-one-20260926"）
    ("T17", "--only は表に載った名前の行だけを選び（空なら全部）、表に無い名前と --measure-only の無い使い方は止める"),
    # ★2026-10-06（156回目・next_step §6 の249番）
    ("T18", "錠＝取れる・親が持てば取らない・ほかが持てば待って取れない・持ち主が死んだ錠と印の無い古い錠は取り直す・自分の錠だけ外す"),
)


def selftest() -> int:
    """わざと壊して止まるか試すテスト（本物のファイルは1つも触らない）。"""
    import tempfile
    ng = []
    body = ("<!-- ACCEPT_TABLE_START -->\n"
            "| # | 完成の条件 | 壊すプログラム | いまの状態 |\n"
            "|---|---|---|---|\n"
            "| 1 | あ | `b01_x.sh` | 未着手 |\n"
            "| 2 | い | `—`（※1） | 未着手 |\n"
            "<!-- ACCEPT_TABLE_END -->\n")
    rows = parse_table(body)
    if len(rows) != 2 or rows[0]["script"] != "b01_x.sh":
        ng.append("T1")
    if rows[1]["script"] is not None or "済にできない" not in rows[1]["note"]:
        ng.append("T2")
    if parse_table("| 1 | あ | `b01_x.sh` |\n") != []:
        ng.append("T3")

    # T7 ★打ち消した縦棒（欄の中に書いた縦棒）で列がずれないか
    #    直す前＝ここで「bash` ほか」のような、実在しない名前を拾っていた
    body7 = ("<!-- ACCEPT_TABLE_START -->\n"
             "| # | 完成の条件 | 壊すプログラム | いまの状態 |\n"
             "|---|---|---|---|\n"
             "| 19 | `base64 -d \\| bash` ほかを掛ける | `—`（※2） | 未着手 |\n"
             "<!-- ACCEPT_TABLE_END -->\n")
    r7 = parse_table(body7)
    if len(r7) != 1 or r7[0]["script"] is not None:
        ng.append("T7")

    # ★T17（2026-09-26・監査 CP43 の B3-c）＝`--only` の選び方と止め方。本物のファイルは触らない。
    #   a＝名指しした行だけを選ぶ ／ b＝空なら全部の行のまま（承認の経路）／ c＝表に無い名前を返す
    #   d＝`--measure-only` の無い `--only` は、何も読まずに rc=2（承認の経路で使わせない）
    _r17 = [{"no": "1", "script": "b01_x.sh"}, {"no": "2", "script": "b02_y.sh"},
            {"no": "3", "script": None}]
    _p17, _m17 = pick_rows(_r17, ["b02_y.sh"])
    if [r["no"] for r in _p17] != ["2"] or _m17:
        ng.append(f"T17a: 名指しした行だけを選んでいない（{[r['no'] for r in _p17]}・{_m17}）")
    _p17b, _m17b = pick_rows(_r17, [])
    if len(_p17b) != 3 or _m17b:
        ng.append(f"T17b: --only が空なのに行が減った（{len(_p17b)} 行）")
    _p17c, _m17c = pick_rows(_r17, ["b01_x.sh", "b09_none.sh"])
    if _m17c != ["b09_none.sh"]:
        ng.append(f"T17c: 表に無い名前を返していない（{_m17c}）")
    import contextlib
    import io
    with contextlib.redirect_stderr(io.StringIO()):
        _rc17 = main(["--only", "b01_x.sh", "--design", "/no/such/design.md"])
    if _rc17 != 2:
        ng.append(f"T17d: --measure-only の無い --only が止まらない（rc={_rc17}）")

    global FROZEN, BREAKS_DIR, TIMEOUT_SEC
    _kf, _kb, _kt = FROZEN, BREAKS_DIR, TIMEOUT_SEC
    try:
        with tempfile.TemporaryDirectory() as d:
            BREAKS_DIR = pathlib.Path(d) / "breaks"
            BREAKS_DIR.mkdir()
            (BREAKS_DIR / "b01_x.sh").write_text("exit 1\n", encoding="utf-8")
            FROZEN = pathlib.Path(d) / "no_such_frozen.json"
            if not check_frozen():
                ng.append("T4")
            FROZEN = pathlib.Path(d) / "frozen.json"
            FROZEN.write_text(json.dumps({"b01_x.sh": "0" * 64}), encoding="utf-8")
            if not check_frozen():
                ng.append("T5")
            FROZEN.write_text(json.dumps(freeze_breaks()), encoding="utf-8")
            if check_frozen():
                ng.append("T6")
            # ★T8（2026-09-07・146番）＝記録を本当に書くか（本物のファイルは触らない）
            _o8 = pathlib.Path(d) / "rec" / "t8.breaks.json"
            write_record(_o8, "t8", [{"no": "1", "script": "b01_x.sh", "code": 1}])
            _d8 = json.loads(_o8.read_text(encoding="utf-8")) if _o8.exists() else {}
            if (_d8.get("iter") != "t8"
                    or [r.get("code") for r in (_d8.get("rows") or [])] != [1]):
                ng.append("T8")
            # ★T9・T10・T11（2026-09-08・159番）＝宣言の読み取りと、期待との照らし
            _t9 = BREAKS_DIR / "b90_no_decl.sh"
            _t9.write_text("#!/bin/bash\n# 宣言を書いていない見本\nexit 1\n", encoding="utf-8")
            if not expect_of("b90_no_decl.sh")[2]:
                ng.append("T9")
            _t10 = BREAKS_DIR / "b91_decl.sh"
            _t10.write_text("#!/bin/bash\n# EXPECT_RC: 2\n# MEANS: 見本の意味\n"
                            "# EXPECT_MSG: 見本の文字\nexit 2\n", encoding="utf-8")
            _e10, _m10, _w10, _g10 = expect_of("b91_decl.sh")
            if _w10 or _e10 != 2 or _m10 != "見本の意味" or _g10 != "見本の文字":
                ng.append("T10")
            # ★T13（2026-09-11・案A の残り半分）＝出力に `EXPECT_MSG` が無ければ「期待どおり」にしない
            if not match_of(2, 2, "…見本の文字…", "見本の文字"):
                ng.append("T13a: 出力に在るのに期待どおりにならない")
            if match_of(2, 2, "別の理由で落ちた", "見本の文字"):
                ng.append("T13b: 出力に無いのに期待どおりになった")
            # ★宣言が無い見本は、読めない理由が返る（足す前は EXPECT_RC だけで通っていた）
            _t13 = BREAKS_DIR / "b92_no_msg.sh"
            _t13.write_text("#!/bin/bash\n# EXPECT_RC: 1\n# MEANS: 見本\nexit 1\n",
                            encoding="utf-8")
            if not expect_of("b92_no_msg.sh")[2]:
                ng.append("T13c: EXPECT_MSG が無いのに読めてしまう")
            _o11 = pathlib.Path(d) / "rec" / "t11.breaks.json"
            write_record(_o11, "t11", [{"no": "1", "script": "b91_decl.sh", "code": 1,
                                        "expect": 2, "means": "見本の意味", "match": False}])
            _d11 = json.loads(_o11.read_text(encoding="utf-8")) if _o11.exists() else {}
            if [r.get("match") for r in (_d11.get("rows") or [])] != [False]:
                ng.append("T11")
            # ★T12（2026-09-08・設計書 insp5-path-and-tidy-head-20260908 の N）
            #   ＝壊すプログラムがまだ無い行を「期待どおり」と数えない。
            #   直す前＝ファイルが無いと 実際の終了コードも期待値も None になり、
            #     `None == None` が真＝「一致」に数えていた（作業が止まる食い違いの元）。
            _e12, _m12, _w12, _g12 = expect_of("b99_not_exist_yet.sh")
            if match_of(None, _e12) or not _w12:
                ng.append("T12")
            if not match_of(2, 2) or match_of(1, 2):     # ふつうの一致・不一致は今までどおり
                ng.append("T12")
            # ★T14（2026-09-11・まこさん承認）＝打ち切りに掛かったときの検査。
            #   見本の壊すプログラムを作り、わざと打ち切りに掛ける。
            #   見るもの2つ＝①戻り値が3つ返るか ②壊した相手が元に戻っているか。
            #   ★本物のファイルは1つも触らない（一時の場所だけ）。
            _t14 = pathlib.Path(d) / "t14_target.txt"
            _t14.write_text("ORIGINAL\n", encoding="utf-8")
            _t14sh = BREAKS_DIR / "b93_timeout_sample.sh"
            _t14sh.write_text(
                "#!/bin/bash\n"
                "# EXPECT_RC: 1\n"
                "# MEANS: 見本＝打ち切りの検査に使う\n"
                "# EXPECT_MSG: 見本\n"
                f'BK="$(mktemp)"\n'
                f'cp "{_t14}" "$BK"\n'
                f"trap 'cp \"$BK\" \"{_t14}\"; rm -f \"$BK\"' EXIT\n"
                f'echo BROKEN > "{_t14}"\n'
                "sleep 60\n", encoding="utf-8")
            TIMEOUT_SEC = 3                       # ★見本なので短く（本物は上の定数）
            _r14 = run_one("b93_timeout_sample.sh", 0)
            if len(_r14) != 3:
                ng.append(f"T14a: 打ち切りのとき、戻り値が {len(_r14)} 個（3個であること）")
            if _t14.read_text(encoding="utf-8").strip() != "ORIGINAL":
                ng.append("T14b: 打ち切りのあと、壊した相手が元に戻っていない"
                          f"（いまの中身＝{_t14.read_text(encoding='utf-8').strip()[:20]}）")

            # ★T15（2026-09-16・監査 cp36 の M-2）＝宣言の文字が「❌」で始まるかを数える。
            #   見本を3本 作る＝①自己テストを測る・宣言が ❌ 始まり（拾うが、名指ししない）
            #   ②自己テストを測る・宣言が ❌ 始まりでない（名指しする）
            #   ③自己テストを測らない（そもそも拾わない）。
            _head15 = "#!/bin/bash\n# EXPECT_RC: 1\n# MEANS: 見本\n"
            (BREAKS_DIR / "b95a_ok.sh").write_text(
                _head15 + "# EXPECT_MSG: ❌ T99①\nmeasure python3 x.py --selftest\n", encoding="utf-8")
            (BREAKS_DIR / "b95b_weak.sh").write_text(
                _head15 + "# EXPECT_MSG: T99①\nmeasure python3 x.py --selftest\n", encoding="utf-8")
            (BREAKS_DIR / "b95c_other.sh").write_text(
                _head15 + "# EXPECT_MSG: T99①\nmeasure python3 x.py --verify\n", encoding="utf-8")
            _pick15 = selftest_breaks()
            if "b95a_ok.sh" not in _pick15 or "b95b_weak.sh" not in _pick15:
                ng.append(f"T15a: 自己テストを測る見本を拾えていない（拾ったもの＝{_pick15}）")
            if "b95c_other.sh" in _pick15:
                ng.append("T15b: 自己テストを measure していない見本まで拾った")
            _bad15 = lint_expect()
            if "b95b_weak.sh" not in _bad15:
                ng.append(f"T15c: ❌ で始まらない宣言を名指ししていない（出たもの＝{_bad15}）")
            if "b95a_ok.sh" in _bad15:
                ng.append("T15d: ❌ で始まる宣言まで名指しした")

            # ★T16（2026-09-17・仕組み1の後半）＝探す文字を数える。見本は一時の場所だけ（本物は触らない）。
            #   見本4本＝①1か所（壊せる）②0か所 ③2か所 ④文字で探さない。①〜③の相手は同じファイル。
            for _p in list(BREAKS_DIR.glob("*.sh")):
                _p.unlink()
            (BREAKS_DIR / "lib.sh").write_text(f'ROOT="{d}"\n', encoding="utf-8")
            (pathlib.Path(d) / "t16_target.txt").write_text("AAA\nBBB\nBBB\n", encoding="utf-8")
            _q = "'"

            def _mk16(fname, search):
                (BREAKS_DIR / fname).write_text(
                    '#!/bin/bash\nT="$ROOT/t16_target.txt"\n'
                    f"python3 - \"$T\" <<{_q}PYEOF{_q}\n"
                    "import sys\np = sys.argv[1]\ns = open(p, encoding='utf-8').read()\n"
                    f"new = {search!r}\n"
                    "if new not in s:\n    raise SystemExit('壊す対象の行が見つからない')\n"
                    "open(p, 'w', encoding='utf-8').write(s.replace(new, 'X', 1))\nPYEOF\n",
                    encoding="utf-8")

            _mk16("b16a_one.sh", "AAA\n")
            _mk16("b16b_zero.sh", "CCC\n")
            _mk16("b16c_two.sh", "BBB\n")
            (BREAKS_DIR / "b16d_nosearch.sh").write_text(
                "#!/bin/bash\necho 文字で探さない\nexit 1\n", encoding="utf-8")
            _rows16, _ng16 = count_targets()
            _g16 = {r["name"]: r["group"] for r in _rows16}
            if _g16 != {"b16a_one.sh": "ok", "b16b_zero.sh": "ng", "b16c_two.sh": "ng",
                        "b16d_nosearch.sh": "skip"}:
                ng.append(f"T16a: 分け方が違う（{_g16}）")
            if sorted(_ng16) != ["b16b_zero.sh", "b16c_two.sh"]:
                ng.append(f"T16b: 壊せないものの名前が違う（{_ng16}）")
            _design16 = ("<!-- ACCEPT_TABLE_START -->\n"
                         "| # | 完成の条件 | 壊すプログラム | いまの状態 |\n|---|---|---|---|\n"
                         "| 1 | あ | `b16a_one.sh` | 未着手 |\n| 2 | い | `b16c_two.sh` | 未着手 |\n"
                         "<!-- ACCEPT_TABLE_END -->\n")
            _r16c, _ng16c = count_targets(_design16)
            if _ng16c != ["b16c_two.sh"] or len(_r16c) != 4:
                ng.append(f"T16c: 表に載っているものだけで止めていない（{_ng16c}・行 {len(_r16c)}）")

        # T18（2026-10-06・156回目・249番）＝錠。一時の置き場の錠で試す（本物の錠には触らない）。
        #   親から受け継いだ印（A12 の中で走るとき）は、試しの間だけ外して、最後に戻す。
        _env18 = os.environ.pop(LOCK_ENV, None)
        _ld18 = pathlib.Path(tempfile.mkdtemp()) / "real_write.lock"
        try:
            t1 = rw_take(wait=1, lock_dir=_ld18)
            t2 = rw_take(wait=1, lock_dir=_ld18)                        # 自分が持っている（印が在る）＝取らない
            if t1 is not True or t2 is not None or not _ld18.is_dir():
                ng.append(f"T18a: 取れない／親が持つのに取り直した（{t1}・{t2}）")
            rw_drop(t2, lock_dir=_ld18)                                  # 受け継いだ錠は外さない
            if not _ld18.is_dir():
                ng.append("T18b: 受け継いだ錠を外した")
            rw_drop(t1, lock_dir=_ld18)
            if _ld18.exists() or os.environ.get(LOCK_ENV):
                ng.append("T18c: 自分の錠を外せていない")
            _ld18.mkdir()
            (_ld18 / "pid").write_text(str(os.getppid()), encoding="utf-8")   # 生きているほかの持ち主
            t3 = rw_take(wait=1, lock_dir=_ld18)
            if t3 is not False:
                ng.append(f"T18d: ほかが持つ錠を待たずに取った（{t3}）")
                rw_drop(t3, lock_dir=_ld18)
            _dead = 2 ** 22 + 12345
            while _alive(_dead):
                _dead += 1
            (_ld18 / "pid").write_text(str(_dead), encoding="utf-8")     # 死んだ持ち主
            t4 = rw_take(wait=1, lock_dir=_ld18)
            if t4 is not True:
                ng.append(f"T18e: 持ち主が死んだ錠を取り直せない（{t4}）")
            rw_drop(t4, lock_dir=_ld18)
            _ld18.mkdir()
            _old = time.time() - LOCK_ORPHAN_SEC - 5
            os.utime(_ld18, (_old, _old))                                # 印の無い古い錠
            t5 = rw_take(wait=1, lock_dir=_ld18)
            if t5 is not True:
                ng.append(f"T18f: 印の無い古い錠を取り直せない（{t5}）")
            rw_drop(t5, lock_dir=_ld18)
        finally:
            shutil.rmtree(_ld18.parent, ignore_errors=True)
            os.environ.pop(LOCK_ENV, None)
            if _env18 is not None:
                os.environ[LOCK_ENV] = _env18
    finally:
        FROZEN, BREAKS_DIR, TIMEOUT_SEC = _kf, _kb, _kt

    for tag, what in SELF_TESTS:
        # ★2026-09-11＝落ちたときの説明は「T14a: …」のように枝番が付く。
        #   直す前は完全一致で見ていたので、枝番つきの落ちが ✅ と表示された（実測）。
        hit = [x for x in ng if str(x).startswith(tag)]
        print(f"  {'❌' if hit else '✅'} {tag} {what}")
        for x in hit:
            print(f"      └ {x}")
    total = len(SELF_TESTS)
    print(f"  {'❌' if ng else '✅'} 番人 {total - len(ng)}/{total} pass")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
