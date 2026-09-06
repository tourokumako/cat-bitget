#!/usr/bin/env python3
"""gen_audit_request.py — 監査の依頼書を、既に在るテンプレのとおりに機械で組み立てる（92番）

2026-08-27（68回目）・まこさん承認・設計書 iter=gen-audit-request-20260827（2回目の版）。

なぜ要るか
--------------------------------------------------------------------------
依頼書は これまで CC が手で書いてきた。手で書くと「何を入れるか・何を書かないか」を CC が選べる
＝監査は CC が見せたものしか見られない。まこさんの決定（2026-08-27）＝
「監査に出す前に依頼書を自動で作る道具をつくる」「もっと分けて依頼したほうがいいのでは？
 監査も CC なので大量に依頼したら不正、虚偽働きやすいよね？」
「以前使っていた監査依頼用のテンプレートの通りに作って」。

何をするか
--------------------------------------------------------------------------
物差しの13要素（engine_tuner_milestones2.md §3.4 の表）のうち **1件だけ**を指定すると、
`_template.md`（編集禁止・構造を維持する）の **節の並びどおり**に依頼書を組み立てる。

  節の出どころは3つだけ:
    template … テンプレからそのまま複写（auditor 宣言・大目的・監査観点(一般)・結果の形・守則・呼びかけ）
    frozen   … 凍結ファイル（経緯・スコープ・監査観点(本監査固有)・外部検索要請）
    machine  … 実物から機械で作る（メタ情報・着手前必読・事実データ）

  ★CC が文章を書けるのは frozen の中だけ。凍結ファイルはハッシュ値で見張る。
  ★節の並びと数はテンプレから読む＝CC が決めない。テンプレに知らない見出しが増えたら止まる。

使い方
--------------------------------------------------------------------------
  python3 scripts/priority_rebuild/gen_audit_request.py --element 4
  python3 scripts/priority_rebuild/gen_audit_request.py --selftest

限界（正直に書く）
--------------------------------------------------------------------------
  ・凍結ファイルの中身を最初に書くのは CC。凍結できるのは書いた後だけ。
  ・複写元の文書が間違っていれば、依頼書も間違ったまま渡る。
  ・監査も同じ CC。分けて出しても答えが正しい保証はない。
  ・テンプレが古くなっていても、この道具は気づけない（2026-05-24 から更新なし）。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import pathlib
import re
from datetime import date

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent                     # bitget-python-sdk-api
REPO = ROOT.parent.parent                     # cat-bitget

# ★GENERATES＝空にする（2026-08-27）。
#   なぜ＝この道具が作るのは「毎回 名前の違う新しいファイル」（要素の番号ごとの依頼書）で、
#   決まった文書を作り直す型ではない。フォルダを書くと、必読ゲートが
#   「その対象が作る文書を開け」とフォルダを開かせようとして止まる（実測 2026-08-27）。
GENERATES: list = []

MILE = ROOT / ".claude" / "ratchet" / "engine_tuner_milestones2.md"
LAWS = ROOT / ".claude" / "memory" / "regime_detection_kb.md"
QUESTION = ROOT / ".claude" / "audits" / "inputs" / "_frozen_question_regime.md"
TEMPLATE = ROOT / ".claude" / "audits" / "inputs" / "_template.md"
OUT_DIR = ROOT / ".claude" / "audits" / "inputs"
WORKLOG = REPO / ".claude" / "state" / "session_worklog_20260827.md"

# ★凍結ファイルのハッシュ値（2026-08-27・まこさん承認の2回目の版）。
QUESTION_SHA = "27571f67cd960ed71857fb5c3be1afa0ae8be4d05e75a8b2a4fb435f1b314033"

FROZEN_SECTIONS = ("経緯", "必読の精査", "スコープ", "問い", "外部検索要請")

# テンプレの見出し（先頭一致）→ その節をどう埋めるか。
#   ★中身は書かない。「どこから取るか」だけを決める表。
#   テンプレにこの表に無い `## ` 見出しが在れば止める（テンプレが変わったら気づく）。
SECTION_KIND: dict = {
    "## ⚠️ auditor 宣言": ("template", None),
    "## 監査依頼メタ情報": ("machine", "meta"),
    "## 監査依頼の経緯": ("frozen", "経緯"),
    "## 着手前必読": ("machine", "reading"),
    "## 大目的": ("template", None),
    "## 監査対象の事実データ": ("machine", "facts"),
    "## 監査スコープ": ("frozen", "スコープ"),
    "## 監査観点 (一般": ("template", None),
    "## 監査観点 (本監査固有": ("frozen", "問い"),
    "## 外部検索要請": ("frozen", "外部検索要請"),
    "## 結果ファイルフォーマット": ("template", None),
    "## 必ず守ること": ("template", None),
    "## まこさん向け呼びかけ例文": ("template", None),
}

N_ELEMENTS = 13                               # §3.4 の表の行数（読み取って照合する）
N_LAWS = 50                                   # §11 の法則の件数（C10＋R10＋U10＋D9＋S6＋T5）

SOURCES = [
    ("比べる相手＝RG-v5 が5分足でレンジを判定する所",
     ROOT / "scripts" / "priority_rebuild" / "e37_scalp.py", "_apply_rg5_to_5m"),
    ("比べる相手＝RG-v5 の上げトレンドのスイッチ",
     ROOT / "scripts" / "dashboard" / "build_regime_gate_rg.py", "_uptrend_state_5m"),
    ("いまの実装＝engine_tuner が場面の判定の束を組む所",
     ROOT / "scripts" / "priority_rebuild" / "engine_tuner_gen.py", "sample_regime_build"),
    ("いまの実装＝材料を成績表の順位から取る所",
     ROOT / "scripts" / "priority_rebuild" / "engine_tuner_gen.py", "_ranked_material_at"),
    ("いまの実装＝順位を種類×時間足でまとめ直す所",
     ROOT / "scripts" / "priority_rebuild" / "engine_tuner_gen.py", "ranked_groups"),
    ("いまの実装＝束を真偽の列にする所",
     ROOT / "scripts" / "priority_rebuild" / "engine_tuner_exec.py", "build_regime_columns"),
]

MEASURES = [("## §41", WORKLOG)]

# ★着手前必読に並べるもの（2026-08-27）。
#   経緯＝まこさん指摘「必読リストが少なすぎないか？」→ まこさんが16本を挙げた
#         → まこさん指示「私は適当に資料をみつくろったので、依頼するCCが精査すべき」
#         → CC が16本の中身を確かめて13本を採り、3本を外した（まこさん OK）。
#   外した3本と理由（依頼書にも印字する＝隠さない）:
#     exit_families.md      … 出口の枝の表＝玉の決済の話で、場面の判定とつながらない
#     entry_exit_matrix.md  … 入口×出口の網羅＝売買の軸で、場面の判定の軸ではない
#     observe_diag_manual.md… 順位づけの道具の説明書＝「帯を作れるか」とは別の論点
#   ★1行の説明は CC が書かない＝そのファイルの1行目（見出し）から機械で取る。
#   ★存在しないファイルが1本でも在れば止める（fail-closed）。
_PR = ROOT / "scripts" / "priority_rebuild"
_RT = ROOT / ".claude" / "ratchet"
_RU = ROOT / ".claude" / "rules"
# ★必読＝省略禁止。だから「本当に全部 読める量」にする（2026-08-27・まこさん指摘
#   「必読と、資料で分けたほうが良くないか？」）。6本・合計 約3,900行。
READING = [
    MILE,                                   # 物差しの13要素・やることリスト＝問1/問2 の対象
    LAWS,                                   # 場面ごとの法則50件＝問3 の対象
    _RT / "materials.md",                   # 材料の正本＝山と谷の部品が在るか
    _RT / "signal_families.md",             # 型の表＝帯の部品が許されているか
    _RT / "composition_rules.md",           # 組み立ての決まり
    _RU / "exchange_spec.md",               # 手数料＝幅0.4%（往復のコストを超える）の根拠
]

# ★資料＝必要になったら見る。必読から外した理由は凍結ファイルの [SECTION:必読の精査] に書いてある。
REFERENCE = [
    _PR / "engine_tuner_gen.py", _PR / "engine_tuner_exec.py",
    _PR / "indicator_reference_diag.py", _RT / "signal_families.json",
    _PR / "e37_scalp.py", _PR / "gen_signal_families.py",
    _RU / "cat_requirements.md", _PR / "engine_tuner.py",
    _RT / "engine_tuner_requirements.md", _RT / "engine_tuner_manual.md",
    _RT / "engine_tuner_materials.md", TEMPLATE,
]

# ★精査で外した3本の一覧と理由は、凍結ファイルの [SECTION:必読の精査] に書いてある。
#   ここには持たない＝CC がこのソースの中で理由を書き換えられないようにするため。


# ══ 材料を実物から取る（どれも複写・印字だけ）════════════════════════════════════
def load_frozen_question() -> dict:
    """凍結ファイルを読み、節ごとに切り分けて返す。ハッシュが合わなければ止まる（fail-closed）。"""
    if not QUESTION.exists():
        raise SystemExit(f"[依頼書] 凍結ファイルが無い: {QUESTION}")
    body = QUESTION.read_text(encoding="utf-8")
    got = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if got != QUESTION_SHA:
        raise SystemExit("[依頼書] 凍結ファイルが書き換えられている（ハッシュ値の不一致）\n"
                         f"  記録: {QUESTION_SHA}\n  いま: {got}")
    out: dict = {}
    for name in FROZEN_SECTIONS:
        m = re.search(rf"^## \[SECTION:{re.escape(name)}\]\s*$", body, re.M)
        if not m:
            raise SystemExit(f"[依頼書] 凍結ファイルに節が無い: {name}")
        rest = body[m.end():]
        e = re.search(r"^## |^---\s*$", rest, re.M)
        seg = rest[:e.start()] if e else rest
        if not seg.strip():
            raise SystemExit(f"[依頼書] 凍結ファイルの節が空: {name}")
        out[name] = seg.strip()
    return out


def template_heads() -> list[str]:
    """テンプレの `## ` 見出しを、並びのまま返す（数も並びも CC が決めない）。"""
    if not TEMPLATE.exists():
        raise SystemExit(f"[依頼書] テンプレが無い: {TEMPLATE}")
    return [ln.rstrip() for ln in TEMPLATE.read_text(encoding="utf-8").splitlines()
            if ln.startswith("## ")]


def copy_template_section(head: str) -> str:
    """テンプレの1節を、そのまま複写する（テンプレは編集しない）。"""
    text = TEMPLATE.read_text(encoding="utf-8")
    m = re.search(rf"^{re.escape(head)}.*$", text, re.M)
    if not m:
        raise SystemExit(f"[依頼書] テンプレの節が見つからない: {head}")
    rest = text[m.end():]
    e = re.search(r"^## ", rest, re.M)
    seg = (m.group(0) + (rest[:e.start()] if e else rest)).rstrip()
    if len(seg.splitlines()) < 2:
        raise SystemExit(f"[依頼書] テンプレの節が空: {head}")
    return seg


def _table_rows(text: str, start_pat: str, end_pat: str) -> list[str]:
    m = re.search(start_pat, text, re.M)
    if not m:
        raise SystemExit(f"[依頼書] 複写元の見出しが見つからない: {start_pat}")
    rest = text[m.end():]
    e = re.search(end_pat, rest, re.M)
    seg = rest[:e.start()] if e else rest
    return [ln for ln in seg.splitlines() if ln.strip().startswith("|")]


def copy_element_row(n: int) -> tuple[str, list[str]]:
    """§3.4 の13要素の表から、n 番目の行をそのまま取り出す。戻り＝(その行, 表の全行)。"""
    text = MILE.read_text(encoding="utf-8")
    rows = _table_rows(text, r"^## 3\.4 .*$", r"^\*\*書けない9件")
    body = [r for r in rows if not r.strip().startswith("|---")
            and not r.strip().startswith("| #")]
    if len(body) != N_ELEMENTS:
        raise SystemExit(f"[依頼書] 13要素の表の行数が {len(body)}（{N_ELEMENTS} のはず）＝複写元が変わった")
    if not (1 <= n <= N_ELEMENTS):
        raise SystemExit(f"[依頼書] 要素の番号は 1〜{N_ELEMENTS}（受け取った値＝{n}）")
    return body[n - 1], body


def copy_all_laws() -> list[str]:
    """§11 の法則を、群ごとの見出しごと 全部そのまま複写する（選ばない）。"""
    text = LAWS.read_text(encoding="utf-8")
    m = re.search(r"^# §11 .*$", text, re.M)
    if not m:
        raise SystemExit("[依頼書] 法則の一覧（§11）の見出しが見つからない")
    seg = text[m.start():]
    out = [ln for ln in seg.splitlines()
           if ln.strip().startswith("|") or ln.strip().startswith("## 11-")]
    n = len([ln for ln in out if re.match(r"^\|\s*\*{0,2}(C|R|U|D|S|T)\d+", ln.strip())])
    if n != N_LAWS:
        raise SystemExit(f"[依頼書] 法則の件数が {n}（{N_LAWS} のはず）＝複写元が変わった")
    return out


def copy_todo_rows() -> list[str]:
    """§4 のやることリスト（M2 の全行）を、見出しごと そのまま複写する。"""
    text = MILE.read_text(encoding="utf-8")
    m = re.search(r"^# §4 やることリスト.*$", text, re.M)
    if not m:
        raise SystemExit("[依頼書] やることリスト（§4）の見出しが見つからない")
    seg = text[m.start():]
    e = re.search(r"^# §5 ", seg, re.M)
    if e:
        seg = seg[:e.start()]
    return [ln for ln in seg.splitlines()
            if ln.strip().startswith("|") or ln.strip().startswith("## M2-")]


def print_source(path: pathlib.Path, func: str) -> str:
    """その関数の定義を、行番号つきでそのまま印字する。"""
    if not path.exists():
        raise SystemExit(f"[依頼書] ソースが無い: {path}")
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        raise SystemExit(f"[依頼書] ソースが読めない: {path}（{e}）")
    lines = src.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func:
            a, b = node.lineno, (node.end_lineno or node.lineno)
            return "\n".join(f"{i:>5}  {lines[i - 1]}" for i in range(a, b + 1))
    raise SystemExit(f"[依頼書] 関数が見つからない: {func}（{path.name}）")


def copy_measure(head: str, path: pathlib.Path) -> list[str]:
    """記録の中の1つの節を、そのまま複写する。"""
    if not path.exists():
        raise SystemExit(f"[依頼書] 記録が無い: {path}")
    text = path.read_text(encoding="utf-8")
    m = re.search(rf"^{re.escape(head)} .*$", text, re.M)
    if not m:
        raise SystemExit(f"[依頼書] 記録の節が見つからない: {head}")
    seg = text[m.start():]
    e = re.search(r"^## §\d+ ", seg[len(m.group(0)):], re.M)
    return (seg[:len(m.group(0)) + e.start()] if e else seg).splitlines()


def _sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16] if path.exists() else "（無い）"


# ══ 機械で作る3節 ══════════════════════════════════════════════════════════════
def _meta(n: int, out_name: str) -> list[str]:
    d = date.today().isoformat()
    return [
        f"- 依頼日: {d}",
        "- 依頼者: CC (起案者)",
        "- 監査区分: CP9 場面の判定（レンジ）・要素ごとの分割監査",
        f"- 監査対象タスク: M2 物差しの第 {n} 要素 / {N_ELEMENTS} 要素中",
        f"- 結果ファイル保存先: `.claude/audits/2026-08-27_regime_element{n:02d}_audit_report.md`",
        f"- 入力ファイル保存先 (本依頼書): `.claude/audits/inputs/{out_name}`",
    ]


def _headline(path: pathlib.Path) -> str:
    """そのファイルの説明の1行を、機械で取る。CC は書かない。

    ★.py は、構文木から取り出した説明文（docstring）の1行目を使う。
      直す前は「1行目」を取っていたので、.py は `#!/usr/bin/env python3` になっていた（実測 2026-08-27）。
    ★.json は鍵の一覧を出す（説明の文が無いため）。
    ★.md は最初の見出しの行。
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        try:
            doc = ast.get_docstring(ast.parse(text)) or ""
        except SyntaxError:
            doc = ""
        first = next((x.strip() for x in doc.splitlines() if x.strip()), "")
        return (first or "（説明の文が無い）")[:120]
    if path.suffix == ".json":
        try:
            import json as _json
            keys = list(_json.loads(text).keys())
            return ("鍵＝" + " / ".join(keys))[:120]
        except Exception:                              # noqa: BLE001
            return "（json の鍵が取れない）"
    for ln in text.splitlines()[:12]:
        s = ln.strip()
        if s.startswith("<!--") or not s:
            continue
        s = re.sub(r"^#+\s*", "", s).strip()
        if s:
            return s[:120]
    return "（説明の行が取れない）"


def _line_of(path: pathlib.Path, i: int) -> str:
    if not path.exists():
        raise SystemExit(f"[依頼書] 一覧のファイルが無い: {path}")
    n = len(path.read_text(encoding="utf-8").splitlines())
    return f"{i}. `{path.relative_to(REPO)}` ({n:,} 行) — {_headline(path)}"


def _reading(frozen: dict) -> list[str]:
    def total(paths):
        return sum(len(p.read_text(encoding="utf-8").splitlines()) for p in paths)

    out = [f"### 必読 ({len(READING)} 件・合計 {total(READING):,} 行・省略禁止)", ""]
    out += [_line_of(p, i) for i, p in enumerate(READING, 1)]
    out += ["", f"### 資料 ({len(REFERENCE)} 件・合計 {total(REFERENCE):,} 行・必要になったら見る)", ""]
    out += [_line_of(p, i) for i, p in enumerate(REFERENCE, 1)]
    out.append("")
    out.append(frozen["必読の精査"])          # ★分けた理由・外した理由は凍結ファイルから
    return out


def _facts(n: int) -> list[str]:
    row, all_rows = copy_element_row(n)
    p: list[str] = []
    p.append(f"### 対象の1要素（第 {n} 要素・複写）")
    p.append("")
    p.append("| # | 一例のどの部分か | 書けるか | 実物 |")
    p.append("|---|---|---|---|")
    p.append(row)
    p.append("")
    p.append("### 同じ表の13要素 全部（複写）")
    p.append("")
    p.append("| # | 一例のどの部分か | 書けるか | 実物 |")
    p.append("|---|---|---|---|")
    p += all_rows
    p.append("")
    p.append(f"### 場面ごとの法則（{N_LAWS}件 全部・選ばずに複写）")
    p.append("")
    p += copy_all_laws()
    p.append("")
    p.append("### やることリスト（M2 の全行・複写）")
    p.append("")
    p += copy_todo_rows()
    p.append("")
    p.append("### 実物のソース（そのまま印字）")
    for title, path, func in SOURCES:
        p.append("")
        p.append(f"#### {title}")
        p.append("")
        p.append(f"`{path.relative_to(REPO)}` の `{func}`")
        p.append("")
        p.append("```python")
        p.append(print_source(path, func))
        p.append("```")
    p.append("")
    p.append("### 対象のファイルとハッシュ値")
    p.append("")
    p.append("| ファイル | sha256 (先頭16桁) |")
    p.append("|---|---|")
    seen = set()
    for _t, path, _f in SOURCES:
        if path not in seen:
            seen.add(path)
            p.append(f"| `{path.relative_to(REPO)}` | `{_sha(path)}` |")
    for path in (MILE, LAWS, QUESTION, TEMPLATE):
        p.append(f"| `{path.relative_to(REPO)}` | `{_sha(path)}` |")
    p.append("")
    p.append("### 走らせた実測（記録からの複写）")
    for head, path in MEASURES:
        p.append("")
        p += copy_measure(head, path)
    return p


# ══ 依頼書を組み立てる（節の並びはテンプレから読む）════════════════════════════
_REF_MD_RE = re.compile(r"([\w./-]+\.md)")
_REF_SEC_RE = re.compile(r"§\s*(\d+)")


def section_refs_missing(body: str) -> list[str]:
    """依頼書が指した節（§NN）が、指した先の .md に実在するかを確かめる（2026-09-06）。

    なぜ要るか＝監査 cp23 の X-9 の逐語＝「依頼書 §1 の3が『§36 と §38 ← CC が出した実測』と
    指示しているが、**§38 は存在しない**」。＝**申告を突き合わせる相手が無いまま監査に出した。**

    ★見るのは「同じ行に .md の名前と §数字 の両方が在る行」だけ。
    ★限界（正直に）＝①節の中身が申告と合っているかは見ない ②`§NN` の形でないと見つけられない
      ③同じ行に無いと（ファイル名と節が離れて書かれると）拾えない。
    """
    out: list[str] = []
    for ln in body.splitlines():
        names = _REF_MD_RE.findall(ln)
        nums = _REF_SEC_RE.findall(ln)
        if not names or not nums:
            continue
        for name in names:
            base = pathlib.Path(name).name
            hit = next((c for c in (ROOT / name, ROOT / ".claude" / "state" / base)
                        if c.exists()), None)
            if hit is None:
                out.append(f"{name}: 依頼書が指したファイルが見つからない（行＝{ln.strip()[:50]}）")
                continue
            t = hit.read_text(encoding="utf-8", errors="ignore")
            for num in nums:
                if not re.search(rf"§\s*{num}(?!\d)", t):
                    out.append(f"{name}: 依頼書が指した §{num} が、そのファイルに無い")
    return out


def build_request(n: int) -> str:
    frozen = load_frozen_question()
    heads = template_heads()
    out_name = f"2026-08-27_regime_element{n:02d}_audit_request.md"
    p: list[str] = []
    p.append(f"# 監査依頼 — M2 場面の判定（レンジ）の物差し 第 {n} 要素")
    p.append("")
    p.append("> 本依頼書は `gen_audit_request.py` が `_template.md` の節の並びどおりに機械で組み立てた。")
    p.append("> 起案者 (CC) が書いた文章は、凍結ファイル由来の4節 (経緯 / スコープ / 監査観点(本監査固有) / 外部検索要請) だけ。")
    p.append("")
    for head in heads:
        kind = None
        for key, val in SECTION_KIND.items():
            if head.startswith(key):
                kind = val
                break
        if kind is None:
            raise SystemExit(f"[依頼書] テンプレに知らない見出しが在る: {head}"
                             "（テンプレが変わった＝対応を決めてから作り直す）")
        p.append("---")
        p.append("")
        how, key = kind
        if how == "template":
            p.append(copy_template_section(head))
        elif how == "frozen":
            p.append(head)
            p.append("")
            p.append(frozen[key])
        elif key == "meta":
            p.append(head)
            p.append("")
            p += _meta(n, out_name)
        elif key == "reading":
            p.append(head)
            p.append("")
            p += _reading(frozen)
        elif key == "facts":
            p.append(head)
            p.append("")
            p += _facts(n)
        p.append("")
    body = "\n".join(p) + "\n"
    # ★2026-09-06（監査 cp23 の X-9）＝指した節が実在しなければ、依頼書を作らない（fail-closed）。
    miss = section_refs_missing(body)
    if miss:
        raise SystemExit("[依頼書] 指した節が実在しないので作れません（監査 cp23 の X-9）:\n  - "
                         + "\n  - ".join(miss))
    return body


# ══ わざと壊して止まるか試すテスト ════════════════════════════════════════════════
def selftest() -> int:
    ng: list[str] = []

    def stops(name, fn):
        try:
            fn()
            ng.append(f"{name}: 止まらなかった")
        except SystemExit:
            pass

    global QUESTION_SHA, QUESTION, N_LAWS, TEMPLATE, SECTION_KIND
    keep = QUESTION_SHA
    QUESTION_SHA = "0" * 64
    stops("Q1 凍結ファイルが書き換えられたら止まる", load_frozen_question)
    QUESTION_SHA = keep

    keepq = QUESTION
    QUESTION = QUESTION.parent / "_no_such_question.md"
    stops("Q2 凍結ファイルが無ければ止まる", load_frozen_question)
    QUESTION = keepq

    stops("Q3 要素の番号が 0 なら止まる", lambda: copy_element_row(0))
    stops("Q3 要素の番号が 14 なら止まる", lambda: copy_element_row(N_ELEMENTS + 1))
    stops("Q4 複写元の見出しが無ければ止まる",
          lambda: _table_rows("ただの文章", r"^## 3\.4 .*$", r"^\*\*書けない"))

    keepn = N_LAWS
    N_LAWS = 999
    stops("Q5 法則の件数が変わったら止まる", copy_all_laws)
    N_LAWS = keepn

    keept = TEMPLATE
    TEMPLATE = TEMPLATE.parent / "_no_such_template.md"
    stops("Q8 テンプレが無ければ止まる", template_heads)
    TEMPLATE = keept
    stops("Q8b テンプレに無い節を求めたら止まる", lambda: copy_template_section("## 存在しない節"))

    # Q10 テンプレに知らない見出しが在ったら止まる（対応の表から1件 抜く）
    keeps = dict(SECTION_KIND)
    SECTION_KIND = {k: v for k, v in SECTION_KIND.items() if k != "## 大目的"}
    stops("Q10 テンプレに知らない見出しが在れば止まる", lambda: build_request(4))
    SECTION_KIND = keeps

    # Q6/Q9 1〜13 のどれでも作れて、テンプレの節が全部 在る
    heads = template_heads()
    made = 0
    for i in range(1, N_ELEMENTS + 1):
        try:
            body = build_request(i)
            miss = [h for h in heads if h.split("(")[0].rstrip() not in body]
            if miss:
                ng.append(f"Q9 要素 {i}: 節が足りない {miss[:2]}")
            elif len(body) > 5000:
                made += 1
        except SystemExit as e:
            ng.append(f"Q6 要素 {i} で作れない: {str(e)[:70]}")
    if made != N_ELEMENTS:
        ng.append(f"Q6: 作れたのは {made}/{N_ELEMENTS}")

    # Q7 この道具のソースに、依頼書へ入る日本語の自由記述が無い
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    bad = []
    for f in ast.walk(tree):
        if not (isinstance(f, ast.FunctionDef)
                and f.name in ("build_request", "_meta", "_reading", "_facts")):
            continue
        allow = ("本依頼書", "起案者", "凍結ファイル", "経緯", "スコープ", "監査観点",
                 "外部検索要請", "対象の1要素", "同じ表の13要素", "場面ごとの法則",
                 "やることリスト", "実物のソース", "対象のファイル", "走らせた実測",
                 "一例のどの部分か", "書けるか", "ファイル", "複写", "印字", "依頼日",
                 "依頼者", "監査区分", "監査対象タスク", "結果ファイル保存先",
                 "入力ファイル保存先", "本依頼書の雛形", "要素中", "の物差し 第", "節の並び",
                 "必読", "資料", "省略禁止", "必要になったら見る")
        # ★止まるときのエラーの文は、依頼書に入らないので除く（2026-08-27・番人が拾ったので直した）
        in_raise = set()
        for node in ast.walk(f):
            if isinstance(node, ast.Raise):
                for c in ast.walk(node):
                    if isinstance(c, ast.Constant) and isinstance(c.value, str):
                        in_raise.add(id(c))
        for node in ast.walk(f):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if id(node) in in_raise:
                    continue
                s = node.value
                if len(s) >= 12 and re.search(r"[ぁ-んァ-ン一-龥]", s):
                    if not any(a in s for a in allow):
                        bad.append(s[:40])
    if bad:
        ng.append(f"Q7: 依頼書へ入る自由記述が在る: {bad[:3]}")

    # Q11 依頼書が指した節が実在しないときに、問題として返すか（2026-09-06・監査 cp23 の X-9）
    _q11_ng = section_refs_missing("- `session_worklog_20260904.md` の §99 ← CC が出した実測\n")
    if not _q11_ng:
        ng.append("Q11: 存在しない節を指しても、問題として返さない")
    _q11_ok = section_refs_missing("- `session_worklog_20260904.md` の §43 ← CC が出した実測\n")
    if _q11_ok:
        ng.append(f"Q11: 実在する節なのに問題として返す: {_q11_ok[:2]}")

    print(f"[selftest] Q1 凍結の改変で止まる ／ Q2 凍結が無ければ止まる ／ Q3 番号の範囲外で止まる ／"
          f" Q4 複写元が無ければ止まる ／ Q5 法則の件数が変われば止まる ／"
          f" Q6 1〜{N_ELEMENTS} のどれでも作れる ／ Q7 自由記述0件 ／"
          f" Q8 テンプレが無ければ止まる ／ Q9 テンプレの節が全部 在る ／ Q10 知らない見出しで止まる ／"
          f" Q11 指した節が実在しなければ作らせない")
    for x in ng:
        print(f"  ❌ {x}")
    total = 11
    print(f"  {'❌' if ng else '✅'} わざと壊して止まるか試すテスト {total - len(ng)}/{total} pass")
    return 1 if ng else 0


def approval_matches() -> tuple[bool, str]:
    """設計書の指紋が、まこさんの承認の記録と合っているか（監査 cp14 の P-5）。

    ★監査の逐語＝「監査依頼書を作る道具が、acceptance.md の指紋と acceptance.approved を
      照合し、食い違ったら依頼書を作らせない」。
    ★なぜ要るか（実測）＝79回目に、承認の後に設計書の §6 を3行 書き換えて監査に出した。
      監査に渡ったデータの中核（RESULT: PASS）が、その書き換えた3行から来ていた。
    戻り＝(合っているか, 説明の文)
    """
    acc = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/"
                       ".claude/state/acceptance.md")
    mark = acc.with_name("acceptance.approved")
    if not acc.exists():
        return False, f"設計書がありません: {acc}"
    if not mark.exists():
        return False, f"承認の記録がありません: {mark}（まこさんの承認が要ります）"
    now = hashlib.sha256(acc.read_bytes()).hexdigest()
    want = mark.read_text(encoding="utf-8").strip()
    if now != want:
        return False, (f"設計書が承認と食い違います（いま {now[:16]}… ／ 承認 {want[:16]}…）"
                       "＝承認の後に設計書を書き換えた疑い。再承認を打ってもらってください。")
    return True, f"設計書は承認どおり（{now[:16]}…）"


def main() -> int:
    ap = argparse.ArgumentParser(description="監査の依頼書をテンプレのとおりに機械で組み立てる")
    ap.add_argument("--element", type=int, help=f"物差しの要素の番号（1〜{N_ELEMENTS}）")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.element:
        ap.error("--element <番号> を指定してください")
    # ★2026-09-03（監査 cp14 の P-5）＝承認と食い違う設計書では依頼書を作らせない。
    ok, why = approval_matches()
    if not ok:
        print(f"[STOP] 依頼書は作れません（監査 cp14 の P-5）: {why}")
        return 2
    print(f"  ✅ {why}")
    body = build_request(a.element)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"2026-08-27_regime_element{a.element:02d}_audit_request.md"
    out.write_text(body, encoding="utf-8")
    print(f"[依頼書] 作りました: {out.relative_to(REPO)}")
    print(f"  行数 {len(body.splitlines()):,} ／ 文字数 {len(body):,}")
    print(f"  テンプレの節 {len(template_heads())} ／ 法則 {N_LAWS}件 ／ 要素 {a.element}/{N_ELEMENTS}")
    print("  凍結ファイルのハッシュ値 一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
