#!/usr/bin/env python3
"""gen_docmap.py — 機械が作る文書の全数の一覧を、道具の名乗りから作る（2026-08-16 新設）

なぜ要るか（まこさん決定 A・2026-08-16）
--------------------------------------------------------------------------
`composition_rules.json` が **8日間 古いまま** 残っていて、誰も気づかなかった。
気づいたのは、たまたま番人を1本ずつ走らせたときだった（28回目のセッション）。

そこで「セッションの終わりに全部 検証する」仕組みを作ろうとしたが、その前に
**「全部」が何本なのかを、誰も正しく数えていない**ことが分かった。

私（CC）が最初に数えた方法は「名前で数える」だった＝`gen_` で始まる .py を探す。
**この方法は必ず漏れる。**実測でも1本 落とした（`.claude/ratchet/gen_improvement_arc.py`）。
さらに、出力先を入れている変数の名前が道具ごとにバラバラで
（`OUT` / `OUT_MD` / `MD_OUT` / `_MD` / `TARGET` / `FINAL` / `WORKFLOW`）、
**読むファイルと作るファイルが同じ形で並んでいる**＝外から見分けられない。

だから **道具の側に「私はこの文書を作ります」と名乗らせる**（`GENERATES`）。
この道具は、その名乗りを機械で集めるだけ。名前は手がかりにしない。

出すもの
--------------------------------------------------------------------------
  .claude/ratchet/docmap.md   … 人が読む1枚
  .claude/ratchet/docmap.json … 機械が読む同じ中身

  表1 … 道具 → 作る文書 → 検証コマンドの有無
        ★「いまの検証の結果」は文書に書かない（2026-08-28・まこさん承認 案A）。
          時とともに変わる値を焼くと、ほかの道具を直すたびにこの文書が古くなるため。
          いまの結果は --status がその場で走らせ直して画面に出す。
  表2 … 文書 → それを作る道具 → 「まるごと」か「一部の節」
  表3 … ★名乗っていない道具（この一覧から漏れているもの）
  表4 … ★誰にも作られていない文書（人が手で書いているもの）

この一覧で分かること・分からないこと（正直に）
--------------------------------------------------------------------------
分かる＝機械が作る文書が全部で何本か／検証できない道具はどれか／人が書く文書はどれか。
分からない＝**文書の中身が正しいかは分からない**（「作り直した状態と同じか」だけ）。
        ＝**道具が名乗り忘れたら、その文書は一覧に出ない**（実在しないパスは落とせる）。

使い方
--------------------------------------------------------------------------
  python3 gen_docmap.py --write     … 作る
  python3 gen_docmap.py --verify    … 手で書き換えられていないか／古くなっていないか
  python3 gen_docmap.py --selftest  … 番人（わざと壊すと落ちるか）
  python3 gen_docmap.py --status    … いまの状態を表示する（文書は書かない）
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import subprocess
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_SDK = _HERE.parent.parent                                   # bitget-python-sdk-api
_ROOT = _SDK.parent.parent                                   # リポジトリの根（cat-bitget）
_RATCHET = _SDK / ".claude" / "ratchet"
_MD = _RATCHET / "docmap.md"
_JSON = _RATCHET / "docmap.json"

# ★GENERATES＝この道具が作る文書の名乗り（自分も名乗る＝例外を作らない）。
GENERATES = [
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/docmap.md", "まるごと"),
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/docmap.json", "まるごと"),
]

# 探さない場所（履歴・外から持ってきたもの・実験の出力）
# ★site-packages と .venv* は「外から入れたライブラリ」＝私たちの文書ではない。
#   入れたままにすると 表4 が1,100本に膨らんで、本当に見たいものが埋もれる（2026-08-16 実測）。
_SKIP_DIRS = {"archive", "archive_rules", ".git", "node_modules", "__pycache__",
              "results", "data", "site-packages", "lib", "bin", "include"}


def _skip(p: pathlib.Path) -> bool:
    parts = p.parts
    if any(x in _SKIP_DIRS for x in parts):
        return True
    return any(x.startswith(".venv") or x.startswith("venv") for x in parts)


# 「文書」として数える拡張子（実験の出力 CSV は文書ではない）
_DOC_SUFFIX = {".md", ".json", ".txt"}
# 表4（人が手で書いている文書）を数える範囲。
# ★リポジトリ全部を数えると、外から入れたライブラリの json まで入る。
#   数えるのは「私たちが書いた文書」だけ＝.claude 配下と、リポジトリ直下の md。
_DOC_ROOTS = (".claude", "v3-bitget-api-sdk/bitget-python-sdk-api/.claude",
              "v3-bitget-api-sdk/bitget-python-sdk-api/scripts")


def _walk_py() -> list[pathlib.Path]:
    """リポジトリ全体の .py を集める（名前で絞らない＝gen_ で始まらない道具も拾う）。"""
    return sorted(p for p in _ROOT.rglob("*.py") if not _skip(p))


def _read_generates(p: pathlib.Path) -> list[tuple[str, str]] | None:
    """.py を **実行せずに** 構文木で読んで GENERATES を取り出す。

    ★import しない理由＝道具を import すると、その道具の副作用（読み込み・生成）が走る。
      一覧を作るだけのために本体を動かさない。
    """
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return None
    for node in tree.body:
        # ★2つの書き方を両方 読む。`GENERATES = [...]` と
        #   `GENERATES: list[tuple[str, str]] = []`（型の注釈つき）。
        #   注釈つきを読み落として「名乗っていない」と誤って出した（2026-08-16 実測）。
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
        else:
            continue
        if "GENERATES" not in names or node.value is None:
            continue
        try:
            val = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            return None
        out = []
        for item in val:
            if not (isinstance(item, (list, tuple)) and len(item) == 2):
                return None
            out.append((str(item[0]), str(item[1])))
        return out
    return None


def _looks_like_generator(p: pathlib.Path, src: str) -> bool:
    """名乗っていない .py のうち「文書を作っていそうなもの」を拾う（表3 の候補）。

    ★ここだけは名前も手がかりに使う。理由＝名乗っていないものを探す側なので、
      名乗り以外の手がかりしか無い。取りこぼしは残る（下の「限界」に書く）。
    """
    if p.name.startswith("gen_"):
        return True
    return ".write_text(" in src and (".md\"" in src or ".md'" in src)


def _has_verify(src: str) -> bool:
    return '"--verify"' in src or "'--verify'" in src


def _run_verify(p: pathlib.Path) -> tuple[str, str]:
    """その道具の --verify を実際に走らせて (結果, 一言) を返す。"""
    try:
        r = subprocess.run([sys.executable, str(p), "--verify"], capture_output=True,
                           text=True, timeout=300, cwd=str(p.parent))
    except subprocess.TimeoutExpired:
        return "❌", "時間切れ（300秒）"
    if r.returncode == 0:
        return "✅", ""
    both = r.stdout + r.stderr
    if "the following arguments are required" in both:
        # ★そのままでは走らせられない道具（出力先などを引数で渡す作り）。
        #   「ずれている」のではなく「検証を自動で回せない」＝別の問題として出す。
        return "⚠️", "引数が要る＝そのままでは検証を走らせられない"
    tail = [ln for ln in both.splitlines() if ln.strip()]
    return "❌", (tail[-1][:90] if tail else f"終了コード {r.returncode}")


def collect(run_verify: bool = True, extra_src: dict | None = None) -> dict:
    """全数を集める。extra_src＝番人がわざと壊した中身を差し込むためだけに在る。"""
    tools, unnamed = [], []
    for p in _walk_py():
        rel = str(p.relative_to(_ROOT))
        src = (extra_src or {}).get(rel)
        if src is None:
            try:
                src = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
        gens = (_read_generates_src(src) if extra_src and rel in extra_src
                else _read_generates(p))
        if gens is None:
            if p.name.startswith("gen_"):
                unnamed.append(dict(道具=rel, 種類="A｜明らかな漏れ",
                                    理由="名前が gen_ で始まるのに名乗っていない"))
            elif _looks_like_generator(p, src):
                unnamed.append(dict(道具=rel, 種類="B｜要確認",
                                    理由="md を書き出す処理が在るのに名乗っていない"))
            continue
        v = _has_verify(src)
        # ★ほかの道具の「いまの検証の結果」は、この一覧に書かない（2026-08-28・まこさん承認 案A）。
        #   もともと 2026-08-16 に、自分自身の結果だけを外す形にしてあった。理由は当時のコメント＝
        #     「書くと『文書を作る → 自分の結果が ❌ から ✅ に変わる → 文書が古くなる』を永久に繰り返す」
        #   ★同じ理屈が、ほかの19本にも当てはまる。それが自分の行にしか当てられていなかった。
        #   実際に起きたこと＝`gen_filemap --write` で filemap.md を直すと、その道具の結果が
        #   ❌ から ✅ に変わり、この文書が古くなって `--verify` が落ちた（3回・2026-08-28 に原因を特定）。
        #   ＝走らせる順番の話ではない。時とともに変わる値を、変わらない前提の文書に焼いていたのが原因。
        #   いまの結果は `--status` が、その場で走らせ直して画面に出す（文書には書かない）。
        tools.append(dict(道具=rel, 作る文書=[dict(文書=a, 作り方=b) for a, b in gens],
                          検証コマンド=("あり" if v else "❌ なし")))

    # 表2＝文書 → 道具
    by_doc: dict[str, list] = {}
    for t in tools:
        for d in t["作る文書"]:
            by_doc.setdefault(d["文書"], []).append(dict(道具=t["道具"], 作り方=d["作り方"]))
    docs = [dict(文書=k, 作る道具=v, 実在=(_ROOT / k).exists()) for k, v in sorted(by_doc.items())]

    # 表4＝誰にも作られていない文書
    named = set(by_doc)
    handmade = []
    for p in _ROOT.rglob("*"):
        if p.is_dir() or p.suffix not in _DOC_SUFFIX or _skip(p):
            continue
        rel = str(p.relative_to(_ROOT))
        if not rel.startswith(_DOC_ROOTS):
            continue
        if rel not in named:
            handmade.append(rel)
    return dict(tools=sorted(tools, key=lambda x: x["道具"]), docs=docs,
                unnamed=sorted(unnamed, key=lambda x: x["道具"]), handmade=sorted(handmade))


def _read_generates_src(src: str):
    """番人用＝文字列から直接 GENERATES を読む（ファイルを書き換えずに壊せる）。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in tree.body:
        hit = (isinstance(node, ast.Assign) and any(
                   isinstance(t, ast.Name) and t.id == "GENERATES" for t in node.targets)) or (
               isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
               and node.target.id == "GENERATES" and node.value is not None)
        if hit:
            try:
                return [(str(a), str(b)) for a, b in ast.literal_eval(node.value)]
            except (ValueError, SyntaxError):
                return None
    return None


def _hash(body: dict) -> str:
    return hashlib.md5(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def render_md(b: dict) -> str:
    L = [f"<!-- DOCMAP_HASH={_hash(b)} -->",
         "# docmap.md — 機械が作る文書の全数の一覧（gen_docmap.py が自動生成＝手書き禁止）", "",
         "⚠️ 手で書き換えないでください。**道具の側の名乗り（`GENERATES`）を機械で集めています。**",
         "名前で数えていません（名前で数えると必ず漏れる＝2026-08-16 に実測で1本 落とした）。", "",
         "```",
         "python3 scripts/priority_rebuild/gen_docmap.py --write    # 作り直す",
         "python3 scripts/priority_rebuild/gen_docmap.py --verify   # 改変・古くなりの検出",
         "```", "",
         "## この一覧で分かること・分からないこと（正直に）", "",
         "**分かる**＝機械が作る文書が全部で何本か ／ 検証できない道具はどれか ／ 人が手で書く文書はどれか。", "",
         "**分からない**＝**文書の中身が正しいかは分かりません**（「作り直した状態と同じか」だけです）。",
         "＝**道具が名乗り忘れたら、その文書はこの一覧に出ません**（実在しないパスは落とせます）。", ""]
    nov = [t for t in b["tools"] if t["検証コマンド"].startswith("❌")]
    L += [f"## いまの数", "",
          f"- 名乗っている道具＝**{len(b['tools'])} 本**",
          f"- その道具が作る文書＝**{len(b['docs'])} 本**",
          f"- **検証コマンドを持たない道具＝{len(nov)} 本**"
          + (f"（{'／'.join(t['道具'].split('/')[-1] for t in nov)}）" if nov else ""),
          f"- **名乗っていない道具＝{len([u for u in b['unnamed'] if u['種類'].startswith('A')])} 本**"
          f"（明らかな漏れ）／ {len([u for u in b['unnamed'] if u['種類'].startswith('B')])} 本（要確認）＝表3",
          f"- 誰にも作られていない文書＝**{len(b['handmade'])} 本**（表4＝人が手で書いているもの）", ""]
    L += ["## 表1｜道具 → 作る文書", "",
          "**★「いまの検証の結果」の欄は、ここには書きません**（2026-08-28・まこさん承認 案A）。"
          "時とともに変わる値を焼くと、ほかの道具を直すたびにこの文書が古くなるためです。", "",
          "いまの結果は `python3 scripts/priority_rebuild/gen_docmap.py --status` が、"
          "その場で走らせ直して画面に出します（文書より新しい結果が出ます）。", "",
          "| 道具 | 作る文書 | 検証コマンド |", "|---|---|---|"]
    for t in b["tools"]:
        docs = "<br>".join(f"{d['文書'].split('/')[-1]}（{d['作り方']}）" for d in t["作る文書"])
        L.append(f"| `{t['道具'].split('/')[-1]}` | {docs} | {t['検証コマンド']} |")
    L += ["", "## 表2｜文書 → それを作る道具", "", "| 文書 | 作る道具 | 作り方 | 実在 |", "|---|---|---|---|"]
    for d in b["docs"]:
        for g in d["作る道具"]:
            L.append(f"| `{d['文書']}` | `{g['道具'].split('/')[-1]}` | {g['作り方']} "
                     f"| {'✅' if d['実在'] else '❌ 無い'} |")
    L += ["", "## 表3｜★名乗っていない道具（この一覧から漏れているもの）", "",
          "**2つに分けています。**",
          "**A＝明らかな漏れ**（名前が `gen_` で始まるのに名乗っていない）。",
          "**B＝要確認**（`.md` を書き出す処理が在るのに名乗っていない。凍結した研究の道具を含む）。", ""]
    a = [u for u in b["unnamed"] if u["種類"].startswith("A")]
    bb = [u for u in b["unnamed"] if u["種類"].startswith("B")]
    L += [f"**A＝{len(a)} 本 ／ B＝{len(bb)} 本。**", ""]
    if a:
        L += ["### A｜明らかな漏れ", "", "| 道具 | 理由 |", "|---|---|"]
        L += [f"| `{u['道具']}` | {u['理由']} |" for u in a]
        L += ["", "**★この道具に `GENERATES` を足すか、文書を作らない道具だと確かめてください。**", ""]
    else:
        L += ["### A｜明らかな漏れ", "", "**0 本。**", ""]
    if bb:
        L += ["### B｜要確認", "", "<details><summary>全部を開く</summary>", "",
              "| 道具 | 理由 |", "|---|---|"]
        L += [f"| `{u['道具']}` | {u['理由']} |" for u in bb]
        L += ["", "</details>", ""]
    L += ["", "## 表4｜誰にも作られていない文書（人が手で書いているもの）", "",
          f"**{len(b['handmade'])} 本。**この一覧に出るものは、機械の検証の対象外です"
          "（＝古くなっても検出されません。それでよいかは人が決めます）。", ""]
    L += ["<details><summary>全部を開く</summary>", ""]
    L += [f"- `{h}`" for h in b["handmade"]]
    L += ["", "</details>", ""]
    return "\n".join(L) + "\n"


def write() -> int:
    b = collect()
    _MD.write_text(render_md(b), encoding="utf-8")
    _JSON.write_text(json.dumps(dict(body=b, _本文の指紋=_hash(b)), ensure_ascii=False,
                                indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[作成] {_MD}")
    print(f"[作成] {_JSON}")
    print(f"  道具 {len(b['tools'])} ／ 文書 {len(b['docs'])} ／ 名乗っていない道具 {len(b['unnamed'])}"
          f" ／ 人が書く文書 {len(b['handmade'])} ／ 指紋 {_hash(b)}")
    return 0


def verify() -> list[str]:
    ng = []
    if not _MD.exists() or not _JSON.exists():
        return ["docmap.md／.json が無い（--write で作る）"]
    b = collect()
    if _MD.read_text(encoding="utf-8") != render_md(b):
        ng.append("docmap.md が正本と一致しない（手で書き換えたか、道具の名乗りが変わったのに作り直していない）")
    try:
        if json.loads(_JSON.read_text(encoding="utf-8")).get("_本文の指紋") != _hash(b):
            ng.append("docmap.json の指紋が正本と合わない（--write で作り直す）")
    except json.JSONDecodeError:
        ng.append("docmap.json が読めない（--write で作り直す）")
    return ng


def selftest() -> int:
    print("=" * 70)
    print("gen_docmap 自己検査")
    print("=" * 70)
    ng: list[str] = []
    base = collect(run_verify=False)

    # T1 自分も名乗っていること（例外を作らない）
    if not any(t["道具"].endswith("gen_docmap.py") for t in base["tools"]):
        ng.append("T1: この道具 自身が名乗っていない（例外を作らない）")

    # T2 名乗りを1本 消したら、表3（名乗っていない道具）に出ること（メタ確認）
    victim = "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py"
    src = (_ROOT / victim).read_text(encoding="utf-8")
    broken = src.replace("GENERATES = [", "GENERATES_USO = [", 1)
    b2 = collect(run_verify=False, extra_src={victim: broken})
    if any(t["道具"] == victim for t in b2["tools"]):
        ng.append("T2: 名乗りを消したのに、まだ表1 に居る（名乗りを見ていない）")
    if not any(u["道具"] == victim for u in b2["unnamed"]):
        ng.append("T2: 名乗りを消したのに 表3（名乗っていない道具）に出ない＝漏れが見えない")

    # T3 実在しないパスを名乗ったら、表2 で ❌ が立つこと
    fake = src.replace('GENERATES = [\n', 'GENERATES = [\n    ("zzz_uso_no_such_file.md", "まるごと"),\n', 1)
    b3 = collect(run_verify=False, extra_src={victim: fake})
    hit = [d for d in b3["docs"] if d["文書"] == "zzz_uso_no_such_file.md"]
    if not hit or hit[0]["実在"]:
        ng.append("T3: 実在しないパスを名乗っても ❌ が立たない")

    # T4 検証コマンドの有無を、中身で見ていること（★2026-08-28 に直した）
    #   直す前＝道具の名前（gen_improvement_arc.py）を焼き込んでいた。
    #   その道具に `--verify` が付いた時点で、中身は正しいのにこのテストだけが落ちた（実測）。
    #   だから名前を焼くのをやめ、わざと `--verify` を消した中身を差し込んで確かめる（T2・T3 と同じやり方）。
    no_v = src.replace('"--verify"', '"--UsO--"').replace("'--verify'", "'--UsO--'")
    b4 = collect(run_verify=False, extra_src={victim: no_v})
    row = [t for t in b4["tools"] if t["道具"] == victim]
    if not row or not row[0]["検証コマンド"].startswith("❌"):
        ng.append("T4: --verify を消した道具を『あり』と出している（中身を見ていない）")
    row0 = [t for t in base["tools"] if t["道具"] == victim]
    if not row0 or row0[0]["検証コマンド"] != "あり":
        ng.append("T4: --verify を持つ本物の道具を『あり』と出していない（過剰に落としている）")

    # T5 数がゼロでないこと（集め方が丸ごと壊れていないか）
    if len(base["tools"]) < 10 or len(base["docs"]) < 10:
        ng.append(f"T5: 集めた数が少なすぎる（道具 {len(base['tools'])} ／ 文書 {len(base['docs'])}）")

    # T6 わざと書き換えると --verify が鳴る（メタ確認）
    if _MD.exists():
        keep = _MD.read_text(encoding="utf-8")
        try:
            _MD.write_text(keep + "この行は手で足しました\n", encoding="utf-8")
            if not verify():
                ng.append("T6: 手で書き足しても --verify が鳴らない（改変検出が死んでいる）")
        finally:
            _MD.write_text(keep, encoding="utf-8")

    for m in ng:
        print(f"  ❌ {m}")
    print("  ✅ 全部 pass" if not ng else f"  ❌ {len(ng)} 件")
    return 1 if ng else 0


def status() -> int:
    """いまの状態を画面に出す（文書は書かない）。

    ★ここが「いまの検証の結果」を見る唯一の口（2026-08-28・まこさん承認 案A）。
      文書に焼くのをやめたので、見たい人はこれを打つ。その場で走らせ直すから、
      文書に書いてある写しより新しい結果が出る。
    """
    b = collect()
    print(f"名乗っている道具 {len(b['tools'])} ／ 作る文書 {len(b['docs'])} "
          f"／ 名乗っていない道具 {len(b['unnamed'])} ／ 人が書く文書 {len(b['handmade'])}")
    print("  いまの検証の結果（ここで1本ずつ走らせています）:")
    ng = 0
    for t in b["tools"]:
        rel = t["道具"]
        name = rel.split("/")[-1]
        if t["検証コマンド"].startswith("❌"):
            print(f"  — {name}: 検証コマンドが無い")
            continue
        if pathlib.Path(_ROOT / rel).resolve() == pathlib.Path(__file__).resolve():
            print(f"  — {name}: 自分自身（ここでは走らせない）"
                  f"＝`gen_docmap.py --verify` を直に打つ")
            continue
        res, why = _run_verify(_ROOT / rel)
        if res == "✅":
            continue
        ng += 1
        print(f"  {res} {name}: {why}")
    print(f"  ＝検証が通らない道具 {ng} 本" if ng else "  ＝検証が通らない道具はありません")
    for u in b["unnamed"]:
        print(f"  ⚠️ 名乗っていない: {u['道具']}")
    return 0


def main() -> int:
    a = sys.argv[1:]
    if "--write" in a:
        return write()
    if "--selftest" in a:
        return selftest()
    if "--status" in a:
        return status()
    if "--verify" in a:
        ng = verify()
        for m in ng:
            print(f"  ❌ {m}")
        print("  ✅ 一致（手で書き換えられていない・古くなっていない）" if not ng else f"[verify] ❌ {len(ng)} 件")
        return 1 if ng else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
