#!/usr/bin/env python3
"""gen_filemap.py — 何がどこにあるかの地図を実体から機械生成する（まこさん指示 2026-07-27「一旦作ってみて」）

なぜ作ったか
--------------------------------------------------------------------------
手書きの地図は必ず腐る。実測（2026-07-27）＝大本 cat_requirements §8.2.1 のファイル地図に
載っている .py は 10 本で、実体は 58 本。しかも載っている strat_coinflip.py は既に存在しない。
まこさんが別途メモを出して CC に道具の存在を思い出させる状態になっていた（window_similarity.py 事案）。

正直な限界（まこさんへ先に伝えた通り）
--------------------------------------------------------------------------
これは「道具の存在を知らない」型の間違いしか減らせない。「あるのに開かない」型と
「経緯の受け取り方を間違える」型は減らない。だから量で圧倒しない作りにする＝
  ① 先頭に「やりたいこと → どれを使うか」の索引を置く（テンプレ固定・gen_flow と同型）
  ② どこからも使われていないファイルを別枠で出す（消し忘れ・自作の重複を可視化）
  ③ 説明は各ファイルの1行目から機械で取る＝中身とずれない

使い方
--------------------------------------------------------------------------
  python3 scripts/priority_rebuild/gen_filemap.py --write     # 作り直す
  python3 scripts/priority_rebuild/gen_filemap.py --verify    # 改変・未更新の検出
  python3 scripts/priority_rebuild/gen_filemap.py --selftest  # 材料が実体から取れているかの番人
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent                  # scripts/priority_rebuild/
ROOT = HERE.parent.parent                                       # bitget-python-sdk-api/
REPO = ROOT.parent.parent                                       # cat-bitget/
OUT = ROOT / ".claude" / "ratchet" / "filemap.md"

SCAN = [
    ("売買と判定のスクリプト", HERE, "*.py"),
    ("戦略の接続ファイル", HERE / "tuner_adapters", "*.py"),
    ("作業の正本・記録", ROOT / ".claude" / "ratchet", "*.md"),
    ("ルール", ROOT / ".claude" / "rules", "*.md"),
    ("知識と教訓", ROOT / ".claude" / "memory", "*.md"),
    ("物理強制の hook", REPO / ".claude" / "hooks", "*.sh"),
]

# 名前の規約から種類を決める（pdca_flow §5 の命名規約が根拠・規約が増えたらここへ1行）
KIND_RULES = [
    (r"^(score|precheck|eval_engine|periods)\.py$", "審判・期間の正本（改造禁止）"),
    (r"^(report|analyze|plot_trades)\.py$", "結果を見る道具"),
    (r"^(strat_base|ratchet_io|params_sidecar)\.py$", "全戦略の共通土台"),
    (r"^gen_.*\.py$", "文書の生成器（手書き禁止の文書を作る）"),
    (r"^engine_.*\.py$", "値を調整する探索器"),
    (r".*_diag\.py$", "観察・診断（売買記録を出さない）"),
    (r"^(verify_|test_).*\.py$", "番人・検査"),
    (r"^e\d\d[_a-z]*\.py$", "戦略の実装"),
    (r"^(build_labels|preload_cache|window_similarity|download_).*\.py$", "データ・材料を作る"),
    (r".*\.sh$", "hook（条件を満たすまで手を動かせなくする）"),
    (r".*\.md$", "文書"),
]

# 「やりたいこと → どれを使うか」の索引。ここだけテンプレ固定（実体から機械で決められないため）。
# ★足すときはこの表へ1行。実在しないファイルを書くと --selftest が落ちる。
INDEX = [
    ("いまの戦略の弱点を知りたい", "observe_diag.py", "採点窓の売買記録を診断する。数えると診断するの2つだけ"),
    ("Entry/Exit の値を調整したい", "engine_tuner.py", "実エンジンと審判を回して値決め窓で値を選ぶ"),
    ("E37 の値だけ調整したい", "engine_search_e37.py", "E37 専用の探索器"),
    ("採否を決めたい", "score.py", "採点窓の公式 net。ここだけが採否の数字"),
    ("結果の中身を見たい", "report.py", "型別・月別・出口別の内訳を出す"),
    ("前回との差を見たい", "analyze.py", "前後比較と分布のずれを出す"),
    ("検証期間を知りたい", "periods.py", "学習・捨て・値決め・確認・採点・封印の唯一の正本"),
    ("採点窓を変えたので探索窓を選び直したい", "window_similarity.py", "値動きの構造が近い窓を全期間から順位づける"),
    ("窓の選定の経緯を知りたい", "windows.md", "期間の意味と経緯。gen_windows.py が機械生成"),
    ("いま何を採用しているか知りたい", "adopted_strategies.md", "全戦略の地図と採用台帳"),
    ("まこさんが何を決めたか知りたい", "decisions.md", "決定の一覧。提案の前に必ず読む"),
    ("次に何をするか知りたい", "next_step.md", "次セッションの起点。セッション開始で全文表示される"),
]


def _first_line_py(p: pathlib.Path) -> str:
    """.py の説明＝module docstring の1行目（無ければ先頭のコメント行）。"""
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"))
        doc = ast.get_docstring(tree)
    except Exception as e:
        return f"（読めない: {str(e)[:40]}）"
    if doc:
        first = doc.strip().splitlines()[0].strip()
        return re.sub(rf"^{re.escape(p.name)}\s*[—-]\s*", "", first)
    for line in p.read_text(encoding="utf-8").splitlines()[:8]:
        if line.startswith("#") and not line.startswith("#!"):
            return line.lstrip("# ").strip()
    return "（説明が無い＝先頭に1行の説明を書くこと）"


def _first_line_md(p: pathlib.Path) -> str:
    for line in p.read_text(encoding="utf-8").splitlines()[:12]:
        if line.startswith("# "):
            return re.sub(rf"^{re.escape(p.name)}\s*[—-]\s*", "", line[2:].strip())
    return "（見出しが無い）"


def _first_line_sh(p: pathlib.Path) -> str:
    for line in p.read_text(encoding="utf-8").splitlines()[:6]:
        if line.startswith("#") and not line.startswith("#!"):
            return re.sub(rf"^{re.escape(p.name)}\s*[—-]\s*", "", line.lstrip("# ").strip())
    return "（説明が無い）"


def describe(p: pathlib.Path) -> str:
    d = {".py": _first_line_py, ".md": _first_line_md, ".sh": _first_line_sh}[p.suffix](p)
    return (d[:118] + "…") if len(d) > 120 else d


def kind(p: pathlib.Path) -> str:
    for pat, label in KIND_RULES:
        if re.match(pat, p.name):
            return label
    return "その他"


def _py_sources() -> dict[pathlib.Path, str]:
    out = {}
    for d in (HERE, HERE / "tuner_adapters"):
        for p in sorted(d.glob("*.py")):
            out[p] = p.read_text(encoding="utf-8")
    return out


def _is_cli(src: str) -> bool:
    """走らせて使うスクリプトか。__main__ ガードが無くてもトップレベルで動くものを拾う。

    ★2026-07-27 の是正＝当初は __main__ と argparse だけを見ており、ガードを持たない
      window_similarity.py などを「どこからも使われていない」と誤って出していた。
    """
    if "__main__" in src or "argparse" in src:
        return True
    try:
        tree = ast.parse(src)
    except Exception:
        return False
    for node in tree.body:
        if isinstance(node, (ast.For, ast.While, ast.With)):
            return True
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            return True                      # トップレベルの関数呼び出し＝読み込んだ瞬間に動く
    return False


def usage(py_src: dict[pathlib.Path, str]) -> dict[str, str]:
    """.py が「読み込まれて使う」か「実行して使う」かを機械で判定する。どちらでもなければ孤立。"""
    out = {}
    for p, src in py_src.items():
        stem = p.stem
        if p.parent.name == "tuner_adapters":
            # 接続ファイルは engine_tuner が名前で動的に読む（importlib）＝静的な grep では出ない。
            out[p.name] = "探索器が名前で読む"
            continue
        imported = any(re.search(rf"^\s*(import\s+{stem}\b|from\s+{stem}\s+import)", s, re.M)
                       for q, s in py_src.items() if q != p)
        cli = _is_cli(src)
        out[p.name] = ("読み込まれて使う" if imported else "") + \
                      ("／" if imported and cli else "") + ("実行して使う" if cli else "")
        if not imported and not cli:
            out[p.name] = "⚠️ どこからも使われていない"
    return out


def md_referenced(md: list[pathlib.Path], py_src: dict[pathlib.Path, str]) -> dict[str, bool]:
    """.md が他の文書やコードから名前で参照されているか（孤立文書の可視化）。"""
    hay = "\n".join(py_src.values())
    for p in md:
        hay += "\n" + p.read_text(encoding="utf-8")
    return {p.name: hay.count(p.name) > 1 for p in md}


def collect() -> tuple[list, dict, dict]:
    py_src = _py_sources()
    groups = []
    all_md = []
    for label, d, pat in SCAN:
        if not d.exists():
            groups.append((label, d, [])); continue
        # ★自分の出力（filemap.md）は一覧から外す。入れると「書いた瞬間に一覧が変わる」ので
        #   --write の直後の --verify が必ず落ちる（2026-07-27 実測）。
        files = [f for f in sorted(d.glob(pat)) if f != OUT]
        all_md += [f for f in files if f.suffix == ".md"]
        groups.append((label, d, files))
    return groups, usage(py_src), md_referenced(all_md, py_src)


def _rel(p: pathlib.Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p.relative_to(REPO))


def doc() -> str:
    groups, use, ref = collect()
    total = sum(len(f) for _l, _d, f in groups)
    L = ["<!-- FILEMAP_HASH={h} -->",
         "# filemap.md — 何がどこにあるかの地図（gen_filemap.py が自動生成＝手書き禁止）",
         "",
         "⚠️ 手で書き換えないでください。ファイルの一覧も説明も、実体から機械で取っています。",
         "説明はそのファイルの1行目です。だから中身とずれません。",
         "",
         "```",
         "python3 scripts/priority_rebuild/gen_filemap.py --write    # 作り直す",
         "python3 scripts/priority_rebuild/gen_filemap.py --verify   # 改変・未更新の検出",
         "```",
         "",
         "## この地図でできること・できないこと（正直に）",
         "",
         "できるのは「その道具が在ることを知らずに似たものを自作する」型の間違いを減らすことです。",
         "できないのは「在るのに開かない」型と「経緯の受け取り方を間違える」型です。",
         "そこはまこさんの目が最後の関所のまま残ります。",
         "",
         "## 置き場所の注意（2026-07-27 に実測して判明）",
         "",
         "- `.claude` は2箇所あります。repo の直下（hook・settings・state）と、"
         "bitget-python-sdk-api の下（ratchet・rules・memory）です。",
         "- `bitget-python-sdk-api/.claude/state` は repo 直下の `.claude/state` へのリンクです。"
         "中身は1つで、どちらの道から開いても同じファイルです。",
         "- next_step.md・goal_block.md・worklog は state にあります。",
         "",
         "## やりたいこと → どれを使うか（迷ったらここだけ見る）",
         "",
         "| やりたいこと | 使うもの | それは何か |",
         "|---|---|---|"]
    for want, name, why in INDEX:
        L.append(f"| {want} | `{name}` | {why} |")
    L += ["",
          f"## 全部の一覧（{total} 件）",
          ""]
    for label, d, files in groups:
        L += [f"### {label} — {_rel(d)}（{len(files)} 件）", ""]
        if not files:
            L += ["（無し）", ""]; continue
        L += ["| ファイル | 種類 | 使われ方 | 1行目の説明 |", "|---|---|---|---|"]
        for p in files:
            u = use.get(p.name, "—") if p.suffix == ".py" else \
                ("" if p.suffix != ".md" else ("" if ref.get(p.name, True) else "⚠️ どこからも参照されていない"))
            L.append(f"| {p.name} | {kind(p)} | {u or '—'} | {describe(p).replace('|', '／')} |")
        L.append("")
    lonely = [n for n, u in use.items() if u.startswith("⚠️")]
    lonely_md = [n for n, r in ref.items() if not r]
    L += ["## 使われていないもの（消し忘れ・重複の芽）",
          "",
          "読み込まれてもいないし、実行もされないスクリプトです。"
          "同じ役割の道具を知らずに自作したときも、ここに出ます。",
          ""]
    L += [f"- {n}" for n in lonely] or ["- 無し"]
    L += ["",
          "どこからも名前を参照されていない文書です。役目を終えたか、書いたまま忘れられたものです。",
          ""]
    L += [f"- {n}" for n in lonely_md] or ["- 無し"]
    L += ["",
          "## 足すときの決まり",
          "",
          "- 新しいファイルの先頭には、必ず1行の説明を書きます。ここに出るのはその1行です。",
          "- 「やりたいこと → どれを使うか」の索引に足すときは、gen_filemap.py の INDEX へ1行足します。",
          "  実在しないファイル名を書くと自己検査が落ちます。",
          "- 種類の分け方は名前の規約です。規約を増やすときは KIND_RULES へ1行足します。",
          ""]
    body = "\n".join(L)
    h = hashlib.sha256(body.replace("<!-- FILEMAP_HASH={h} -->\n", "").encode("utf-8")).hexdigest()[:16]
    return body.replace("{h}", h) + "\n"


def selftest() -> int:
    ng = []
    groups, use, _ref = collect()
    if sum(len(f) for _l, _d, f in groups) < 100:
        ng.append("集めたファイルが少なすぎる＝走査するディレクトリが間違っている疑い")
    for _want, name, _why in INDEX:
        # ★repo ルート側の .claude も見る。bitget-python-sdk-api/.claude/state は
        #   ../../../.claude/state へのシンボリックリンクで、Python 3.13 の rglob は既定でリンクを辿らない
        #   （2026-07-27 に実測して判明＝next_step.md が「実在しない」と誤判定された）。
        hit = (list(HERE.rglob(name)) + list((ROOT / ".claude").rglob(name))
               + list((REPO / ".claude").rglob(name)))
        if not hit:
            ng.append(f"索引が実在しないファイルを指している: {name}")
    for label, d, files in groups:
        if not files:
            ng.append(f"走査で0件: {label}（{d}）")
    d1, d2 = doc(), doc()
    if d1 != d2:
        ng.append("実行のたびに中身が変わる（hash が安定しない）")
    if "（説明が無い" in d1:
        n = d1.count("（説明が無い")
        print(f"   ※ 先頭に1行の説明が無いファイルが {n} 件（落とさないが、書き足すと地図が読みやすくなる）")
    if ng:
        print("❌ 自己検査 NG:")
        for x in ng:
            print(f"   - {x}")
        return 1
    print(f"✅ 自己検査 OK（走査 {sum(len(f) for _l,_d,f in groups)} 件・索引 {len(INDEX)} 件すべて実在・hash 安定）")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="何がどこにあるかの地図を実体から機械生成する")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.verify:
        if not OUT.exists():
            print(f"❌ {OUT.name} が無い（--write で作る）"); sys.exit(1)
        if OUT.read_text(encoding="utf-8") != doc():
            print(f"❌ {OUT.name} が実体と食い違う＝手で書き換えたか、ファイルが増減した")
            print("   直し方: python3 scripts/priority_rebuild/gen_filemap.py --write"); sys.exit(1)
        print(f"✅ {OUT.name} は実体と一致"); sys.exit(0)
    if a.write:
        OUT.write_text(doc(), encoding="utf-8")
        print(f"[書いた] {OUT.relative_to(ROOT)}（{len(doc().splitlines())} 行）")
        sys.exit(0)
    print(doc())


if __name__ == "__main__":
    main()
