#!/usr/bin/env python3
"""gen_code_index.py — 大きなプログラムの目次を、コードから機械で作る。

なぜ作ったか
------------
まこさん指示（2026-09-09・逐語）＝「長くて読むのがだるいなら、メニューつけて、
必要な箇所だけ読めるようにしたら？」「よい」。

何が起きていたか（実測 2026-09-09）
  CC が `engine_tuner_gen.py`（6,310行）を「全文 読んだ」と記録に書いた。
  実際には乱数を使う場所だけを探し、それ以外を見ていなかった。
  その結果、まこさんが 2026-08-24 に承認された「4つの要素の強制」の仕組み
  （345行〜365行・まこさんの逐語がそのまま書いてある）を丸ごと見落とし、
  1日かけて「その仕組みは無い」と言い続けた。
  根っこ＝長すぎて読み切れないのに「全文を読んだ」と書けること。

何をするか
----------
  --write      目次を作って code_index.md に書く
  --verify     目次が、いまのコードと食い違っていないかを見る
  --dry-run    書かずに、組み立てた本文を画面に出す
  --selftest   わざと壊して ❌ が出るかを試す

★節の見出しは、いまコードに在る `# ══` の行をそのまま使う（新しい印を作らない）。
★関数は構文の木で拾う（正規表現で探さない）。
★見出しの無い区間も表に出す（見落とした所を隠さない）。

fail-closed（黙って通さない・3つ）
  1. 読む相手のファイルが無い → 止まる
  2. 節の見出しが1つも見つからない → 止まる
  3. 表に並べた関数の数が、構文の木で数えた総数と合わない → 止まる

★この道具は「文書を作るだけの道具」なので、設計書と承認が要りません
  （まこさん指示 2026-09-09・逐語「今回のような小規模なインフラ整備では設計書も必要ないよね？」
   →「それでOK」。恒久の決まり71番）。書き出す先は code_index.md の1本だけ。

限界（正直に）
  ・目次を作っても、読んだかどうかは機械には分からない。
  ・見出しの名前が中身と合っているかは見ない（コードの文字をそのまま写す）。
  ・この道具自身を書き換えれば無効にできる（承認ゲートの相手なので承認が要る）。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
PRIORITY = SDK / "scripts" / "priority_rebuild"
RATCHET = SDK / ".claude" / "ratchet"

DEST = RATCHET / "code_index.md"

# ── 目次を作る相手（大きくて読み切れないもの）─────────────────────
TARGETS = (
    PRIORITY / "engine_tuner_gen.py",
    PRIORITY / "engine_tuner_exec.py",
)

# ── 節の見出しの形（いまコードに在るもの）────────────────────────
#   例＝`# ══ 材料の候補プール ═════════════════════════════════`
SECTION_RE = re.compile(r"^#\s*═+\s*(.*?)\s*═*\s*$")

BEGIN = "<!-- CODE_INDEX_START hash={h} gen_code_index.py が自動生成＝手で書き換えない -->"
BEGIN_RE = re.compile(r"<!-- CODE_INDEX_START hash=([0-9a-f]{16}).*?-->")
END = "<!-- CODE_INDEX_END -->"


def _h(body: str) -> str:
    """本文のハッシュ値（先頭16文字）。数える前に末尾の改行を落とす。"""
    return hashlib.sha256(body.rstrip("\n").encode("utf-8")).hexdigest()[:16]


def _esc(s) -> str:
    """表のセルに入れるとき、| を壊さないようにする。"""
    return str(s).replace("|", "／").replace("\n", " ")


def read_src(path: Path) -> str:
    """相手のコードを読む。無ければ止まる（fail-closed の1つ目）。"""
    if not path.exists():
        raise SystemExit(f"[gen_code_index] 読む相手が無い: {path}（fail-closed）")
    return path.read_text(encoding="utf-8")


def find_sections(src: str) -> list:
    """節の見出しを拾う。戻り＝[(行番号, 節の名前), ...]（行番号は1始まり）。

    ★`# ══` で始まる行だけを節の始まりとする。囲みの中は見ない
      （コードのコメントなので、囲みという考え方が無い）。
    """
    out = []
    for i, line in enumerate(src.splitlines(), start=1):
        m = SECTION_RE.match(line)
        if m and m.group(1):
            out.append((i, m.group(1).strip()))
    return out


def find_defs(src: str) -> list:
    """モジュールの直下に在る関数とクラスを、構文の木で拾う。

    戻り＝[(行番号, 名前, 種類), ...]。★正規表現で探さない。
    ★中に入れ子になった関数は数えない（目次が細かくなりすぎるため）。
    """
    tree = ast.parse(src)
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append((node.lineno, node.name, "関数"))
        elif isinstance(node, ast.ClassDef):
            out.append((node.lineno, node.name, "クラス"))
    return sorted(out)


def build_rows(path: Path) -> tuple:
    """1つのファイルの目次の行を作る。戻り＝(行の一覧, 関数の総数)。

    ★見出しの無い区間も1行として出す（fail-closed の3つ目で数を照らす）。
    """
    src = read_src(path)
    secs = find_sections(src)
    if not secs:
        raise SystemExit(f"[gen_code_index] 節の見出しが1つも無い: {path.name}（fail-closed）")
    defs = find_defs(src)
    total_lines = len(src.splitlines())

    # 節の区切り＝[(始まりの行, 終わりの行, 名前), ...]。最初の見出しより前は「見出しの無い区間」。
    bounds = []
    if secs[0][0] > 1:
        bounds.append((1, secs[0][0] - 1, "（見出しの無い区間）"))
    for k, (ln, name) in enumerate(secs):
        end = secs[k + 1][0] - 1 if k + 1 < len(secs) else total_lines
        bounds.append((ln, end, name))

    rows = []
    counted = 0
    for lo, hi, name in bounds:
        names = [n for (dl, n, _k) in defs if lo <= dl <= hi]
        counted += len(names)
        rows.append((name, lo, hi, names))
    return rows, counted, len(defs)


def build_table(path: Path) -> str:
    """1つのファイルの表を組み立てる。"""
    rows, counted, total = build_rows(path)
    if counted != total:
        raise SystemExit(
            f"[gen_code_index] 表に並べた関数 {counted}件 と、構文の木で数えた {total}件 が"
            f"合わない: {path.name}（fail-closed）")
    L = []
    add = L.append
    src_lines = len(read_src(path).splitlines())
    add(f"### {path.name}（{src_lines:,}行・節 {len(rows)}・関数とクラス {total}）")
    add("")
    add("| 節の名前 | 行 | 関数とクラス | 数 |")
    add("|---|---|---|---|")
    for name, lo, hi, names in rows:
        shown = "・".join(f"`{n}`" for n in names) if names else "—"
        add(f"| {_esc(name)} | {lo}〜{hi} | {_esc(shown)} | {len(names)} |")
    add("")
    return "\n".join(L)


def build_body() -> str:
    """目次の本文（囲みの中身）を作る。"""
    L = []
    add = L.append
    add("**★この表はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝コードの `# ══` の見出しと、構文の木で拾った関数。")
    add("")
    add("**読むもの宣言には、ファイル名でなく節の名前を書きます。**"
        "「全文を読んだ」と書けなくするためです。")
    add("")
    for p in TARGETS:
        add(build_table(p))
    return "\n".join(L).rstrip()


def page() -> str:
    """書き出す文書の全文（囲みの外の見出しも含む）。"""
    body = build_body()
    L = []
    add = L.append
    add("# コードの目次（読む箇所を指定するための表）")
    add("")
    add("**なぜ在るか**＝2026-09-09 に、CC が 6,310行 のプログラムを"
        "「全文 読んだ」と書いて、実際には一部しか見ていませんでした。"
        "そのせいで、まこさんが承認済みの仕組みを見落としました。")
    add("")
    add("**使い方**＝設計書を書く前の読むもの宣言に、この表の節の名前と行を書きます。")
    add("")
    add("**作り直し方**＝`python3 .claude/tools/gen_code_index.py --write`。"
        "手で書き換えると `--verify` が見つけます。")
    add("")
    add(BEGIN.format(h=_h(body)))
    add(body)
    add(END)
    add("")
    return "\n".join(L)


def write(dry: bool = False, dest: Path = None) -> int:
    """目次を作って書く。`dest` を省くと正本の置き場に書く。"""
    body = page()
    if dry:
        print(body)
        return 0
    out = Path(dest) if dest else DEST
    out.write_text(body, encoding="utf-8")
    print(f"✅ --write 完了: {out}（{len(body.splitlines())}行）")
    for p in TARGETS:
        rows, counted, total = build_rows(p)
        blank = sum(1 for r in rows if not r[3])
        print(f"   {p.name}: 節 {len(rows)}／関数とクラス {total}／関数が0の節 {blank}")
    return 0


def verify(dest: Path = None) -> int:
    """目次が、いまのコードと食い違っていないかを見る。"""
    target = Path(dest) if dest else DEST
    if not target.exists():
        print(f"❌ 目次が無い: {target}（--write で作ってください）")
        return 1
    cur = target.read_text(encoding="utf-8")
    m = BEGIN_RE.search(cur)
    e = cur.find(END)
    if not m or e < 0:
        print("❌ --verify: 囲みが無い")
        return 1
    got = cur[cur.find("\n", m.start()) + 1: e].rstrip("\n")
    want = build_body()
    if _h(got) != m.group(1):
        print(f"❌ --verify: 目次は手で書き換えられています（本文 {_h(got)} ／ 目印 {m.group(1)}）")
        return 1
    if got.rstrip() != want.rstrip():
        print("❌ --verify: 目次がいまのコードと食い違っています（--write で作り直してください）")
        return 1
    print(f"✅ --verify: 目次はコードと合っています（hash={m.group(1)}）")
    return 0


def selftest() -> int:
    """わざと壊して ❌ が出るかを試す（6件）。★正本の目次には1文字も書かない。"""
    import tempfile
    ok = 0
    total = 0
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix="_code_index.md",
                                      delete=False, encoding="utf-8")
    tmp.close()
    copy = Path(tmp.name)
    try:
        # T1 いまの状態で --verify が通る
        total += 1
        write(dest=copy)
        if verify(dest=copy) == 0:
            ok += 1
            print(f"   T{total} いまの状態で --verify → pass")
        else:
            print(f"   T{total} いまの状態で --verify が ❌ → fail")

        # T2 囲みの中を1行 書き換えると ❌
        total += 1
        base = copy.read_text(encoding="utf-8")
        m = BEGIN_RE.search(base)
        copy.write_text(base[:m.end()] + "\nわざと足した1行\n" + base[m.end():], encoding="utf-8")
        if verify(dest=copy) == 1:
            ok += 1
            print(f"   T{total} 囲みに1行 足すと ❌ → pass")
        else:
            print(f"   T{total} 1行 足しても ✅ のまま → fail")
        copy.write_text(base, encoding="utf-8")

        # T3 読む相手が無いと止まる
        total += 1
        try:
            read_src(PRIORITY / "存在しないプログラム.py")
            print(f"   T{total} 無いファイルでも通る → fail")
        except SystemExit:
            ok += 1
            print(f"   T{total} 無いファイルで止まる → pass")

        # T4 節の見出しが1つも無いと止まる
        total += 1
        try:
            if not find_sections("def a():\n    pass\n"):
                raise SystemExit("節の見出しが無い")
            print(f"   T{total} 見出しが無くても通る → fail")
        except SystemExit:
            ok += 1
            print(f"   T{total} 見出しが1つも無いと止まる → pass")

        # T5 関数を構文の木で拾っている（正規表現でない）
        total += 1
        src = "# ══ 節 ══\n# def にせもの():\n\ndef ほんもの():\n    pass\n"
        names = [n for (_l, n, _k) in find_defs(src)]
        if names == ["ほんもの"]:
            ok += 1
            print(f"   T{total} コメントの中の def を拾わない → pass")
        else:
            print(f"   T{total} コメントの def を拾った（{names}） → fail")

        # T6 見出しの無い区間が表に出る
        total += 1
        rows, _c, _t = build_rows(TARGETS[0])
        if rows and rows[0][0] == "（見出しの無い区間）":
            ok += 1
            print(f"   T{total} 見出しの無い区間が表の先頭に出る（{rows[0][1]}〜{rows[0][2]}行） → pass")
        else:
            print(f"   T{total} 見出しの無い区間が出ない → fail")
    finally:
        copy.unlink(missing_ok=True)
    print(f"\n{'✅' if ok == total else '❌'} selftest {ok}/{total} pass")
    return 0 if ok == total else 1


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true", help="目次を作って書く")
    p.add_argument("--verify", action="store_true", help="目次がコードと合っているかを見る")
    p.add_argument("--dry-run", action="store_true", help="書かずに画面に出す")
    p.add_argument("--selftest", action="store_true", help="わざと壊して ❌ が出るかを試す")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if a.write:
        return write()
    if a.dry_run:
        return write(dry=True)
    if a.verify:
        return verify()
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
