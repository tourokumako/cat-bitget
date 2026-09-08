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
凍結ファイル（CC が書ける4節だけを置いたもの。既定＝`_frozen_question_regime.md`）を渡すと、
`_template.md`（編集禁止・構造を維持する）の **節の並びどおり**に依頼書を組み立てる。

★2026-09-08（監査 cp28 の M-1）＝ここに「物差しの13要素のうち1件だけを指定すると」と
  書いてあった。**その指定の口（--element）は 2026-09-07 に外してある。**
  読んだ人が打つと必ず失敗するので、いまの形に書き直した。

  節の出どころは3つだけ:
    template … テンプレからそのまま複写（auditor 宣言・大目的・監査観点(一般)・結果の形・守則・呼びかけ）
    frozen   … 凍結ファイル（経緯・スコープ・監査観点(本監査固有)・外部検索要請）
    machine  … 実物から機械で作る（メタ情報・着手前必読・事実データ）

  ★CC が文章を書けるのは frozen の中だけ。凍結ファイルはハッシュ値で見張る。
  ★節の並びと数はテンプレから読む＝CC が決めない。テンプレに知らない見出しが増えたら止まる。

使い方
--------------------------------------------------------------------------
  python3 scripts/priority_rebuild/gen_audit_request.py
  python3 scripts/priority_rebuild/gen_audit_request.py --frozen <凍結ファイル>
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
# ★2026-09-07（141番・121番）に更新＝凍結ファイルから13分割の前提を外したため。
#   まこさんが 2026-08-27 に止めた形（既存のレンジ判定を1つずつ写せるかを問う）を、
#   凍結ファイル自身がまだ指していた（`engine_tuner_milestones2.md` §3.4＝いまは無い節）。
QUESTION_SHA = "50467a8c1d5bcb0b3cbc8f8ee315508c1d5498390dd7b338d6490fd138a1eefe"

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

# ★2026-09-08（141番）＝N_ELEMENTS（13要素に分ける形の行数）を消した。
#   2026-09-07 に要素の番号を指定する道を外したので、どこからも使われていなかった。
#   残しておくと「まだ13要素の形が生きている」と読み違える。
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


def _tmp_md(text: str) -> pathlib.Path:
    """番人だけが使う、一時の見本のファイルを作って返す（本物のファイルは触らない）。"""
    import tempfile
    d = pathlib.Path(tempfile.mkdtemp())
    p = d / "_sample_frozen.md"
    p.write_text(text, encoding="utf-8")
    return p


def frozen_title(path: pathlib.Path) -> str:
    """凍結ファイルの最初の見出しを、この監査の題として取る（CC は別に書かない）。

    ★2026-09-07（next_step §6 の121番・92番・141番・
      設計書 iter="approval-audit-plumbing-20260907"）に新設した。
      直す前＝この道具は「物差しの13要素のうち1件」を指定する形（要素の番号）だけだった。
      その13要素は、既存のレンジ判定（RG-v6）を1つずつ写せるかを問う形で、
      まこさんが 2026-08-27 に止めた（違反の記録 #23・逐語「既存のレンジ判定のコピー作っても
      しょうがないじゃん」）。複写元の見出し `## 3.4 …` も正本から消えた。
      **その結果、この道具の番人は Q6 が 0/13 で、-4/11 pass のまま3回の監査をまたいだ。**
      直した後＝監査の題も対象も、凍結ファイル（CC が書ける4節）から取る。
    """
    if not path.exists():
        raise SystemExit(f"[依頼書] 凍結ファイルがありません: {path}")
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if s.startswith("#"):
            return s.lstrip("# ").strip()
    raise SystemExit(f"[依頼書] 凍結ファイルの最初の見出し（# …）がありません: {path}")


def copy_all_laws() -> list[str]:
    """§11 の法則を、群ごとの見出しごと 全部そのまま複写する（選ばない）。"""
    text = LAWS.read_text(encoding="utf-8")
    m = re.search(r"^# §11 .*$", text, re.M)
    if not m:
        raise SystemExit("[依頼書] 法則の一覧（§11）の見出しが見つからない")
    seg = text[m.start():]
    out = [ln for ln in seg.splitlines()
           if ln.strip().startswith("|") or ln.strip().startswith("## 11-")]
    # ★数え方（2026-09-07 に直した）＝法則の行は1つ目の欄が番号だけ（例＝`| **R1** | …`）。
    #   件数の表（11-0）の行は1つ目の欄が場面の名前で、番号は3つ目の欄に「C1・C2・…」と並ぶ。
    #   直す前＝1つ目の欄が番号で始まるかだけを見ていたので、件数の表の6行も数えていた
    #   （実測 2026-09-07＝58件 と出て、正本の合計 51 と合わなかった）。
    #   直した後＝**太字の番号**の行だけを数える（例＝`| **R1** | …`）。
    #   実測（2026-09-07）＝太字でない番号の行が7つ在り、それを数えて 58 になっていた
    #   （`| D5 | 下向きのばらつきで測る | …` など＝別の表の中で法則を指している行）。
    #   太字だけに絞ると 51 になり、正本の合計の行と一致する。
    n = len([ln for ln in out
             if re.match(r"^\|\s*\*\*(C|R|U|D|S|T)\d+\*\*\s*\|", ln.strip())])
    # ★2026-09-07（next_step §6 の141番・設計書 iter="approval-audit-plumbing-20260907"）
    #   ＝件数を、この道具の中の数字（N_LAWS＝50）と比べるのをやめた。
    #   何が困っていたか＝正本の法則が増えても、この道具の数字は増えない。
    #     実測（2026-09-07）＝この道具の数え方では 58件、正本の合計の行は 51件、
    #     道具の中の数字は 50。**3つとも違う。**手で持つ数字は、必ず古くなる。
    #   直した後＝正本の中の「| **合計** | **N** |」の行から読む（機械が数えた数字）。
    #     合計の行が無ければ止める（fail-closed）。
    mtot = re.search(r"^\|\s*\*\*合計\*\*\s*\|\s*\*\*(\d+)\*\*", seg, re.M)
    if not mtot:
        raise SystemExit("[依頼書] 法則の一覧に「合計」の行が見つからない＝複写元が変わった")
    want = int(mtot.group(1))
    if n != want:
        raise SystemExit(f"[依頼書] 法則の件数が {n}（正本の合計の行は {want}）＝数え方が正本とずれた")
    return out


def copy_todo_rows() -> list[str]:
    """§4 のやることリスト（M2 の全行）を、見出しごと そのまま複写する。"""
    text = MILE.read_text(encoding="utf-8")
    # ★2026-09-07（141番）＝やることリストの節は §4 から §3 へ移っていた（実測＝正本の 397行）。
    #   直す前＝`# §4 やることリスト` を探していたので、見つからずに止まっていた。
    m = re.search(r"^# §\d+ やることリスト.*$", text, re.M)
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
def _meta(title: str, out_name: str) -> list[str]:
    """メタ情報。★2026-09-07（121番）＝題は凍結ファイルの見出しから取る（CC は別に書かない）。"""
    d = date.today().isoformat()
    return [
        f"- 依頼日: {d}",
        "- 依頼者: CC (起案者)",
        "- 監査区分: 凍結ファイルで指定した1件",
        f"- 監査対象タスク: {title}",
        f"- 結果ファイル保存先: `.claude/audits/{d}_{pathlib.Path(out_name).stem}_report.md`",
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


def _facts(title: str) -> list[str]:
    """事実データ。★2026-09-07（121番）＝13要素の表の複写をやめ、凍結ファイルの題を出す。

    ★なぜやめたか＝13要素は、既存のレンジ判定（RG-v6）を1つずつ写せるかを問う形で、
      まこさんが 2026-08-27 に止めた（違反の記録 #23）。複写元の見出しも正本から消えた。
    ★ここから下（法則50件・やることリスト・実物のソース・ハッシュ値・実測）は変えていない
      ＝どれも「機械が実物から複写するもの」で、CC の自由記述ではない。
    """
    p: list[str] = []
    p.append("### この監査の対象（凍結ファイルの見出しから機械で取った）")
    p.append("")
    p.append(f"**{title}**")
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
# ★2026-09-07（next_step §6 の141番・設計書 iter="approval-audit-plumbing-20260907"）
#   ＝`.md` の後ろに続く文字を、名前の一部として拾わない形にした。
#   何が起きていたか（実測 2026-09-07）＝`indicator_combination_kb.md` の §7（…` という行で、
#     名前を `indicator_combination_kb.m` と切り出していた（`.md` の d を1文字 落とした形）。
#     そのため「依頼書が指したファイルが見つからない」を出し、依頼書を作れなかった。
#   直した後＝`.md` の直後が、英数字・ドット・下線・ハイフンでないことを求める。
_REF_MD_RE = re.compile(r"([\w./-]+\.md)(?![\w.-])")
_REF_SEC_RE = re.compile(r"§\s*(\d+)")


def section_refs_missing(body: str,
                         extra_dirs: tuple[pathlib.Path, ...] = ()) -> list[str]:
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
            # ★2026-09-07（141番）＝探す場所を4つにした。
            #   直す前＝リポジトリからの相対と .claude/state の2つだけを見ていた。
            #   実測（2026-09-07）＝`indicator_combination_kb.md` は
            #   `.claude/memory/` に在るのに「見つからない」と出て、依頼書を作れなかった。
            #   ★見つからないときは今までどおり止める（fail-closed）＝守りは減らない。
            # ★extra_dirs は番人だけが渡す（本物の呼び出しは空＝探す場所は今までどおり4か所）。
            hit = next((c for c in (tuple(d / base for d in extra_dirs)
                                    + (ROOT / name,
                                       ROOT / ".claude" / "state" / base,
                                       ROOT / ".claude" / "memory" / base,
                                       ROOT / ".claude" / "ratchet" / base,
                                       ROOT / ".claude" / "rules" / base))
                        if c.exists()), None)
            if hit is None:
                # ★2026-09-07（141番）＝行の一部を切り出すとき、改行と縦棒を外す
                #   （表の行をそのまま入れると、指摘の文が途中で切れて読めなかった）。
                _cut = ln.strip().replace("|", "／").replace("\n", " ")[:50]
                out.append(f"{name}: 依頼書が指したファイルが見つからない（行＝{_cut}）")
                continue
            t = hit.read_text(encoding="utf-8", errors="ignore")
            # ★2026-09-07（next_step §6 の141番・設計書 iter="approval-audit-plumbing-20260907"）
            #   ＝同じ行に .md の名前が2つ以上 在るとき、節の番号を全部の名前に当てていた。
            #   実測（2026-09-07）＝`range_scalping_kb.md` §2・`indicator_combination_kb.md` §7`
            #     という行で、§7 を range_scalping_kb にも当てて「無い」と出していた
            #     （※実際は3つとも実在する）。そのため依頼書を1本も作れなかった。
            #   直した後＝**その名前のすぐ後ろに書かれた節だけ**を、その名前の節として見る。
            #   ★見つからないときは今までどおり止める（fail-closed）＝守りは減らない。
            _after = ln.split(name, 1)[1] if name in ln else ""
            # ★名前と節の間に入る文字は3通り（実測）＝「`」「 の 」「・」。
            #   その3つだけを許して、次に来る §番号 を「その名前の節」とする。
            #   ★別の名前が先に来たら、そこで打ち切る（別のファイルの節を当てない）。
            _own = re.match(r"[`\s]*(?:の\s*)?§\s*([\d.]+)", _after)
            #   ★節の番号は、そのままの形で探す（`§6.7` は `§6.7` を探す）。
            #     頭の番号（§6）で代わりに通す形にはしない＝`§99` が `§9` で通ってしまうため
            #     （2026-09-07 に実測＝番人 Q11 が「存在しない節を指しても返さない」で落ちた）。
            for num in ([_own.group(1)] if _own else []):
                if not re.search(rf"§\s*{re.escape(num)}(?![\d.])", t):
                    out.append(f"{name}: 依頼書が指した §{num} が、そのファイルに無い")
    return out


def build_request(frozen_path: pathlib.Path) -> str:
    """凍結ファイルから依頼書を組み立てる（★2026-09-07・121番＝要素の番号ではなく凍結ファイル）。"""
    frozen = load_frozen_question()
    heads = template_heads()
    title = frozen_title(frozen_path)
    out_name = f"{date.today().isoformat()}_{frozen_path.stem.lstrip('_')}_audit_request.md"
    p: list[str] = []
    p.append(f"# 監査依頼 — {title}")
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
            p += _meta(title, out_name)
        elif key == "reading":
            p.append(head)
            p.append("")
            p += _reading(frozen)
        elif key == "facts":
            p.append(head)
            p.append("")
            p += _facts(title)
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

    global QUESTION_SHA, QUESTION, N_LAWS, TEMPLATE, SECTION_KIND, LAWS
    keep = QUESTION_SHA
    QUESTION_SHA = "0" * 64
    stops("Q1 凍結ファイルが書き換えられたら止まる", load_frozen_question)
    QUESTION_SHA = keep

    keepq = QUESTION
    QUESTION = QUESTION.parent / "_no_such_question.md"
    stops("Q2 凍結ファイルが無ければ止まる", load_frozen_question)
    QUESTION = keepq

    # ★Q3・Q4（2026-09-07・121番）＝要素の番号ではなく、凍結ファイルの題で試す。
    stops("Q3 凍結ファイルが無ければ題を取れずに止まる",
          lambda: frozen_title(QUESTION.parent / "_no_such_frozen.md"))
    stops("Q4 凍結ファイルに見出しが無ければ止まる",
          lambda: frozen_title(_tmp_md("見出しの無い文章だけ\n")))

    # ★Q5（2026-09-07・141番）＝件数は正本の「合計」の行から読むので、
    #   道具の中の数字を変えても止まらない。代わりに「合計の行が無い正本」で止まるかを試す。
    keepL = LAWS
    LAWS = _tmp_md("# §11 見出しだけ\n\n| **R1** | あ |\n")
    stops("Q5 正本に合計の行が無ければ止まる", copy_all_laws)
    LAWS = keepL

    keept = TEMPLATE
    TEMPLATE = TEMPLATE.parent / "_no_such_template.md"
    stops("Q8 テンプレが無ければ止まる", template_heads)
    TEMPLATE = keept
    stops("Q8b テンプレに無い節を求めたら止まる", lambda: copy_template_section("## 存在しない節"))

    # Q10 テンプレに知らない見出しが在ったら止まる（対応の表から1件 抜く）
    keeps = dict(SECTION_KIND)
    SECTION_KIND = {k: v for k, v in SECTION_KIND.items() if k != "## 大目的"}
    stops("Q10 テンプレに知らない見出しが在れば止まる", lambda: build_request(QUESTION))
    SECTION_KIND = keeps

    # ★Q6/Q9（2026-09-07・121番）＝凍結ファイルから依頼書を作れて、テンプレの節が全部 在る
    heads = template_heads()
    try:
        body = build_request(QUESTION)
        miss = [h for h in heads if h.split("(")[0].rstrip() not in body]
        if miss:
            ng.append(f"Q9: 節が足りない {miss[:2]}")
        if len(body) <= 5000:
            ng.append(f"Q6: 依頼書が短すぎる（{len(body)} 文字）")
        if frozen_title(QUESTION) not in body:
            ng.append("Q6: 凍結ファイルの題が依頼書に入っていない")
    except SystemExit as e:
        ng.append(f"Q6 依頼書を作れない: {str(e)[:70]}")

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
    # ★2026-09-07（141番）＝見本の相手を、記録のファイルから「一時の見本のファイル」に変えた。
    #   何が起きていたか＝見本は「実在しない節」を指す必要があるが、相手が本物の記録だと、
    #     その番号を記録の中に書いた瞬間に実在してしまう。**実測で2回 起きた**
    #     （§99＝2026-09-06 の記録の 1225行／§9997＝2026-09-07 の記録）。
    #   直した後＝一時の見本のファイル（中身は見出し1つだけ）を相手にする＝記録に何を書いても壊れない。
    #   ★探す場所に、その一時のフォルダだけを足して呼ぶ（本物の呼び出しは今までどおり4か所）。
    #     足さないと「ファイルが見つからない」の道で通ってしまい、
    #     確かめたい「指した §NN がそのファイルに無い」の道を通らない。
    _q11_tmp = _tmp_md("# 見本\n\n本文だけ（節の番号は1つも書かない）\n")
    _q11_ng = section_refs_missing(f"- `{_q11_tmp.name}` の §12 ← CC が出した実測\n",
                                   extra_dirs=(_q11_tmp.parent,))
    if _q11_ng and "見つからない" in _q11_ng[0]:
        ng.append(f"Q11: 見本のファイルを見つけられない: {_q11_ng[:1]}")
    if not _q11_ng:
        ng.append("Q11: 存在しない節を指しても、問題として返さない")
    _q11_ok = section_refs_missing("- `session_worklog_20260904.md` の §43 ← CC が出した実測\n")
    if _q11_ok:
        ng.append(f"Q11: 実在する節なのに問題として返す: {_q11_ok[:2]}")

    # ★2026-09-08（141番）＝まとめの表示が、直す前の形のまま残っていた。
    #   Q3 は「番号の範囲外で止まる」、Q6 は「1〜13 のどれでも作れる」と出ていたが、
    #   要素の番号を指定する道は 2026-09-07 に外してある（口は --frozen と --selftest だけ）。
    #   ＝走らせた人が「まだ13要素に分ける道が在る」と読み違える。実物の文言に合わせた。
    print(f"[selftest] Q1 凍結の改変で止まる ／ Q2 凍結が無ければ止まる ／"
          f" Q3 凍結ファイルが無ければ題を取れずに止まる ／"
          f" Q4 凍結ファイルに見出しが無ければ止まる ／ Q5 法則の件数が変われば止まる ／"
          f" Q6 凍結ファイルから依頼書を作れる ／ Q7 自由記述0件 ／"
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
    # ★2026-09-07（121番・92番・141番）＝要素の番号ではなく、凍結ファイルを指定する。
    ap.add_argument("--frozen", help="凍結ファイル（CC が書ける4節・既定＝_frozen_question_regime.md）")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    frozen_path = pathlib.Path(a.frozen) if a.frozen else QUESTION
    if not frozen_path.exists():
        ap.error(f"凍結ファイルがありません: {frozen_path}")
    # ★2026-09-03（監査 cp14 の P-5）＝承認と食い違う設計書では依頼書を作らせない。
    ok, why = approval_matches()
    if not ok:
        print(f"[STOP] 依頼書は作れません（監査 cp14 の P-5）: {why}")
        return 2
    print(f"  ✅ {why}")
    body = build_request(frozen_path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{date.today().isoformat()}_{frozen_path.stem.lstrip('_')}_audit_request.md"
    out.write_text(body, encoding="utf-8")
    print(f"[依頼書] 作りました: {out.relative_to(REPO)}")
    print(f"  行数 {len(body.splitlines()):,} ／ 文字数 {len(body):,}")
    print(f"  テンプレの節 {len(template_heads())} ／ 法則 {N_LAWS}件 ／ 題＝{frozen_title(frozen_path)}")
    print("  凍結ファイルのハッシュ値 一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
