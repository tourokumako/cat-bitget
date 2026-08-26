#!/usr/bin/env python3
"""verify_design_contract.py — 設計書 ↔ 実装 の機械照合（CC の「設計通り実装しない」虚偽＝類型G を物理検出）

なぜこれがあるか:
  CC は設計書に時間をかけても、まこさんが確認できない工程で設計の核心成分を実装から
  抜くこと（虚偽報告・false_positive 類型G・例: E35 設計 §5.2 の RANGE_OK は
  Jump Model を成分に含むのに実装に無い）を繰り返した。net は score.py が V9 計算で出すので偽れないが、
  「設計通り作った」という工程の報告だけは私の言葉に頼っていて物理チェックが無かった。
  本スクリプトはその唯一の穴（設計↔実装の照合）を機械で塞ぐ。

★2026-08-23（56回目・まこさん承認 97598f50ee8d…）で足したこと（受け入れ条件 C-1〜C-4）:
  設計書＝.claude/ratchet/contract_check_design.md（v2）。
  C-1 目印の行の見分け方を直した（extract_block）。
      直す前＝md_text.find("DESIGN_CONTRACT") で語の最初の1件を拾っていた。
      説明の文の中で語に触れただけの所を目印だと思い、まったく別の囲みを読んでいた。
      実測＝e38_design.md（impl_file が空に見えていた）と ledger.md（読めない扱いだった）の2本。
      直した後＝目印として数えるのは3通りだけ（その語だけの行／見出しの行／囲みの見出しに語が在る）。
      囲みの中の行は数えない。
  C-2 黙って素通りする道を消す（hook 側・require_design_contract_before_run.sh）。
  C-3 設計書と実物を両方向で突き合わせる（spec_from_impl / spec_from_design / diff_spec）。
      ★「実物に在るのに設計書に書いていないもの」を出す向きが、いままで1つも無かった。
  C-4 実物から、設計書と同じ形の文書を書き出す（write_actual）。9つの節のうち5つ。

仕組み:
  設計書(.md)に機械可読な DESIGN_CONTRACT（fenced json）を埋め込む（＝まこさんが設計 GO 時に見る面に置く）。
  実装ファイルを AST 解析し、設計が要求する各成分が「最終シグナルの定義式に実際に連結されているか」を照合。
  1つでも欠けたら exit 1（戦略の self-check に組めば CSV を出す前に停止＝採点に進めない）。

  私が嘘をつけるのは contract を改ざんする所だけ → それは設計書なのでまこさんの目に触れる。
  assert 自体は contract と実装を機械照合するだけ（私の判断は入らない）。
  本物であることは --self-test（わざと成分を抜いて落ちるか）のメタ確認で証明する。

使い方:
  python3 verify_design_contract.py <design.md>            # 設計書の contract で実装を照合（FAIL=exit 1）
  python3 verify_design_contract.py --scan-contracts       # 読めない contract を名指しで出す（1件でも在れば exit 1）
  python3 verify_design_contract.py --diff <design.md>     # 設計書の SPEC と実物を両方向で突き合わせる
  python3 verify_design_contract.py --write <design.md>    # 実物から設計書と同じ形の文書を書き出す
  python3 verify_design_contract.py --self-test            # メタ確認: わざと壊して検出するか（8件）
"""
import ast
import glob
import json
import os
import re
import shutil
import sys
import tempfile

CONTRACT_MARK = "DESIGN_CONTRACT"
SPEC_MARK = "SPEC"
# ★2026-08-26（63回目・まこさん承認 5f8758324866caea…・要件 R17）＝要件と設計書の対応表。
#   目印は半角・大文字・コロン込みの1つだけ（設計書 v2 §3.4 の決まり1）。
REQ_MARK = "REQUIREMENTS:"
_REQ_ID_RE = re.compile(r"^R\d+$")

# わざと壊して止まるか試すテスト（設計書 §6・受け入れ条件 6）。write_actual が「テスト一覧」の節に写す。
SELF_TESTS = [
    ("T1", "目印を囲みの見出しに書いた文書を読める"),
    ("T2", "json の閉じ括弧を消すと読めない側に入る"),
    ("T3", "impl_file が空だと読めない側に入る"),
    ("T4", "目印が文章の中だけの文書は対象外に入る"),
    ("T5", "設計の SPEC から関数を1つ消すと『実物にあるが設計に無い関数』で落ちる"),
    ("T6", "実物から関数を1つ消すと『設計にあるが実物に無い関数』で落ちる"),
    ("T7", "関数の中身を空にすると『呼ぶはずの名前が実物に無い』で落ちる"),
    ("T8", "全部そろっていれば通る"),
    ("T9", "SPEC が無い設計書は『SPEC が無い』と分かる（engine_tuner はこれで止める）"),
    ("T10", "設計書を1文字 書き換えると承認が外れる"),
    ("T11", "--write が書き出した SPEC を使うと、突き合わせが 0件 になる"),
    # ★2026-08-26（要件 R17・まこさん承認 5f8758324866caea…・設計書 v2 §5）
    ("T12", "目印を囲みの中だけに書いた設計書は、要件の番号を数えない"),
    ("T13", "引用の行・全角の目印・行の途中の目印は、どれも数えない"),
    ("T14", "目印の行が2つあれば番号を合わせ、同じ番号は1件に畳む"),
    ("T15", "要件に無い番号は『要件に無い番号』として表に出る（止めない）"),
    ("T16", "表に出る要件の言葉は、要件の json からの複写である"),
    ("T17", "どの設計書も指していない要件が、表で分かる"),
]

_HERE = os.path.dirname(os.path.abspath(__file__))
_SDK = os.path.dirname(os.path.dirname(_HERE))                 # bitget-python-sdk-api
_REPO = os.path.dirname(os.path.dirname(_SDK))                 # cat-bitget
_RATCHET = os.path.join(_SDK, ".claude", "ratchet")
_ACCEPTANCE = os.path.join(_REPO, ".claude", "state", "acceptance.md")
_REQUIREMENTS = os.path.join(_SDK, ".claude", "rules", "cat_requirements.md")
_DESIGN_APPROVED = os.path.join(_REPO, ".claude", "state", "design_approved.json")
_REQ_JSON = os.path.join(_RATCHET, "engine_tuner_requirements.json")   # 要件の正本（R17・2026-08-26）


def outside_fence_lines(md_text: str):
    """行を1つずつ見て、``` の囲みの内側かどうかを決めて返す（★2026-08-26 新設・要件 R17）。

    戻り: [(行番号(0始まり), 前後の空白を外した行, 種別)]
      種別 = "text"        囲みの外の普通の行
             "quote"       囲みの外の引用（> で始まる）
             "fence_open"  囲みの始まりの行（```json DESIGN_CONTRACT など）
             "fence_close" 囲みの終わりの行
             "inside"      囲みの内側

    ★なぜ1か所にまとめるか（監査 cp8 の指摘 P-2）＝同じ判定を2か所に作ると、
      片方だけ直して事故になる。実例はこのファイルの scan_contracts の説明（2026-08-23）＝
      「どれが設計書か」を決める判定が2か所に在り、片方だけ `.actual.md` を外していた。
      だから extract_block も extract_requirements も、囲みの判定はここだけを使う。
    """
    out, infence = [], False
    for i, line in enumerate(md_text.splitlines()):
        s = line.strip()
        if s.startswith("```"):
            out.append((i, s, "fence_close" if infence else "fence_open"))
            infence = not infence
            continue
        if infence:
            out.append((i, s, "inside"))
        elif s.startswith(">"):
            out.append((i, s, "quote"))
        else:
            out.append((i, s, "text"))
    return out


def extract_block(md_text: str, mark: str):
    """設計書から『目印の行』を探し、その後ろの fenced json を1つ取り出す。

    ★2026-08-23 新設（C-1）。直す前は md_text.find(mark) で語の最初の1件を拾っていた。
      説明の文の中で語に触れただけの所を目印だと思い、別の囲みを読んでいた（実測2本）。

    目印の行として数えるのは3通りだけ。囲みの中の行は数えない:
      1. その語だけの行           例: DESIGN_CONTRACT
      2. 見出しの行（# で始まる）   例: ## §12 DESIGN_CONTRACT（機械可読）
      3. 囲みの見出しに語が在る     例: ```json DESIGN_CONTRACT

    ★探す範囲には区切りを入れる（2026-08-23 の実走で分かった）。
      区切りが無いと、小見出しの中で語に触れただけの所を目印にして、
      ずっと後ろの別の囲みを読んでしまう（実測＝§5.2 の小見出しの SPEC から §10 の
      DESIGN_CONTRACT の囲みを読み、食い違いを14件 誤って出した）。
      区切り＝見出しが目印なら「同じか それより大きい見出し」まで。
              その語だけの行が目印なら「次の見出し」まで。

    戻り: (取り出した dict, 理由の文字列)。取れたら理由は None。
          目印の行が1つも無ければ (None, "対象外") ＝説明で言及しているだけの文書。
    """
    lines = md_text.splitlines()
    marks = []
    # ★2026-08-26＝囲みの判定を自前で持つのをやめ、outside_fence_lines に寄せた（監査 cp8 の P-2）。
    #   判定の中身は変えていない（囲みの中は数えない・囲みの見出し／その語だけの行／見出しの行の3通り）。
    for i, s, kind in outside_fence_lines(md_text):
        if kind == "fence_open":
            if mark in s[3:]:
                marks.append(("fence_head", i, 0))
            continue
        if kind in ("inside", "fence_close"):
            continue
        if s == mark:
            marks.append(("alone", i, 99))
        elif s.startswith("#") and mark in s:
            marks.append(("heading", i, len(s) - len(s.lstrip("#"))))
    if not marks:
        return None, "対象外"

    reason = "囲みが無い"
    for kind, i, level in marks:
        if kind == "fence_head":
            body = _fence_body(lines, i)
        else:
            body = _next_fence_json(lines, i, level)
        if body is None:
            continue
        try:
            obj = json.loads(body)
        except Exception as e:
            reason = f"json が壊れている（{e}）"
            continue
        if not isinstance(obj, dict):
            reason = "json が辞書の形でない"
            continue
        return obj, None
    return None, reason


def _fence_body(lines, start):
    """囲みの見出しに目印が在る形＝その囲みの中身を返す。"""
    buf, j = [], start + 1
    while j < len(lines) and not lines[j].strip().startswith("```"):
        buf.append(lines[j])
        j += 1
    body = "\n".join(buf).strip()
    return body if body.startswith("{") else None


def _next_fence_json(lines, start, level=99):
    """start より後ろの、最初の『中身が { で始まる囲み』を返す。

    level ＝ 目印が見出しだったときの見出しの深さ（`#` の数）。
    同じか それより大きい見出し（`#` の数が同じか少ない）が出たら、そこで探すのをやめる。
    ＝別の節の囲みを読まないための区切り。目印が『その語だけの行』のときは level=99 ＝
      次の見出しで止まる。
    """
    i = start + 1
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("#"):
            depth = len(s) - len(s.lstrip("#"))
            if depth <= level:
                return None
        if lines[i].strip().startswith("```"):
            body = _fence_body(lines, i)
            if body is not None:
                return body
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            i = j + 1
            continue
        i += 1
    return None


def extract_contract(md_text: str):
    """設計書から DESIGN_CONTRACT を取り出す（従来の呼び出し口・戻りは dict か None）。"""
    obj, _reason = extract_block(md_text, CONTRACT_MARK)
    return obj


def rhs_names_for_symbol(tree: ast.AST, symbol: str):
    """symbol への全代入を集め、その右辺に現れる Name 一式を返す。
    返り値: (代入が見つかったか, 右辺 Name の集合)。"""
    names = set()
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == symbol for t in node.targets):
                found = True
                for sub in ast.walk(node.value):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
    return found, names


def _resolve_impl(md_path: str, impl_file: str) -> str:
    """設計書に書かれた相対のパスから、実物のファイルの場所を決める。

    ★2026-08-23（56回目）に穴を1つ塞いだ。
      直す前＝設計書の場所から上へ順にたどるだけだった。
      `.claude/state/acceptance.md` はリポジトリ直下に在り、そこから上へたどっても
      `scripts/priority_rebuild/` には行き着かない＝この受け入れ条件の照合は
      一度も相手のファイルに届いていなかった（56回目の実走で発覚）。
      直した後＝上へたどって見つからなければ、bitget-python-sdk-api の直下と
      リポジトリの直下も見る。
    """
    if not impl_file:
        raise FileNotFoundError("impl_file の欄が空")
    if os.path.isabs(impl_file):
        return impl_file
    start = os.path.abspath(md_path)
    for _ in range(8):
        start = os.path.dirname(start)
        cand = os.path.join(start, impl_file)
        if os.path.exists(cand):
            return cand
    for base in (_SDK, _REPO):
        cand = os.path.join(base, impl_file)
        if os.path.exists(cand):
            return cand
    raise FileNotFoundError(f"impl_file が見つからない: {impl_file}（{md_path} から上位探索・"
                            f"bitget-python-sdk-api の直下・リポジトリの直下）")


def scan_contracts(paths=None):
    """対象の .md を走査し、(読めた, 読めない, 対象外) を返す。

    ★2026-08-23 新設（C-1）。読めない contract が黙って素通りしていた穴を、名指しで出す形に変える。
    戻りの中身（★2026-08-23 に、名前でなくパスを返す形にした）:
      読めた   = [(パス, contract の dict)]
      読めない = [(パス, 理由)]
      対象外   = [パス]   ＝目印の行が無い＝説明で言及しているだけ

    ★パスにした理由＝「どれが設計書か」を決める判定が2か所に在り、片方（この関数）だけ
      `.actual.md` を外していた。もう片方（require_design_contract_before_run.sh の中の
      同じ処理）は外しておらず、書き出した文書を設計書として扱って誤って止めた（実測）。
      hook がこの関数をそのまま使えるようにして、判定を1か所にまとめる。
    """
    if paths is None:
        paths = sorted(glob.glob(os.path.join(_RATCHET, "*.md"))) + [_ACCEPTANCE]
    ok, ng, outside = [], [], []
    for p in paths:
        if not os.path.exists(p):
            continue
        # ★`--write` が作った文書は、設計書ではなく「突き合わせる相手」＝設計書として数えない
        #   （2026-08-23 の実走で、6件目として数えられていたので外した）
        if p.endswith(".actual.md"):
            continue
        try:
            t = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        if CONTRACT_MARK not in t:
            continue
        obj, reason = extract_block(t, CONTRACT_MARK)
        if obj is None:
            if reason == "対象外":
                outside.append(p)
            else:
                ng.append((p, reason))
            continue
        impl = str(obj.get("impl_file", "") or "")
        if not impl:
            ng.append((p, "impl_file の欄が空"))
            continue
        try:
            _resolve_impl(p, impl)
        except FileNotFoundError:
            ng.append((p, f"impl_file の実物が無い（{impl}）"))
            continue
        ok.append((p, obj))
    return ok, ng, outside


def spec_from_impl(impl_path: str) -> dict:
    """実物のコードを構文の木として読み、設計書の SPEC と同じ形を作る。

    ★2026-08-23 新設（C-3）。文字を探すのではなく構文の木で見るので、
      コメントや説明の文章の中に書いた名前は数えない。
    集めるもの:
      public_functions = 一番外側の def / class のうち、アンダースコアで始まらないもの。
                         値＝その中で呼んでいる、同じファイルで定義された公開の名前。
      constants        = 一番外側の代入のうち、名前が大文字と数字と下線だけで、右辺が数字・文字・真偽のもの。
      cli_flags        = 関数・クラスの外に書かれた文字のうち、2つのハイフンで始まるもの。
    """
    src = open(impl_path, encoding="utf-8", errors="ignore").read()
    tree = ast.parse(src)

    defined = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)

    funcs = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if node.name.startswith("_"):
            continue
        calls = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                nm = sub.func.id
                if nm in defined and not nm.startswith("_") and nm != node.name:
                    calls.add(nm)
        funcs[node.name] = sorted(calls)

    consts = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        t = node.targets[0]
        if not isinstance(t, ast.Name) or not re.fullmatch(r"[A-Z0-9_]+", t.id):
            continue
        v = node.value
        if isinstance(v, ast.Constant) and isinstance(v.value, (int, float, str, bool)):
            consts[t.id] = v.value

    # ★コマンドの旗の見分け方（2026-08-23 の実走で厳しくした）
    #   直す前＝「-- で始まる文字」を全部 拾っていた。
    #   テストの説明文（例＝「--write が書き出した SPEC を使うと…」）まで旗として数え、
    #   食い違いを1件 誤って出した。
    #   直した後＝英小文字・数字・ハイフンだけでできた形に限る（空白や日本語を含むものは旗ではない）。
    flag_re = re.compile(r"^--[a-z0-9][a-z0-9-]*$")
    flags = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and flag_re.match(sub.value):
                flags.add(sub.value)

    return {"impl_file": impl_path, "public_functions": funcs,
            "constants": consts, "cli_flags": sorted(flags)}


def spec_from_design(md_path: str):
    """設計書から SPEC を取り出す。戻り: (dict, 理由)。"""
    t = open(md_path, encoding="utf-8", errors="ignore").read()
    return extract_block(t, SPEC_MARK)


def diff_spec(design: dict, actual: dict) -> list:
    """設計書の SPEC と実物を両方向で突き合わせ、違いの一覧を返す（空なら齟齬なし）。

    ★「実物に在るのに設計書に書いていないもの」を出す向きが、いままで1つも無かった（C-3 の核心）。
    """
    out = []
    d_f = design.get("public_functions", {}) or {}
    a_f = actual.get("public_functions", {}) or {}
    for name in sorted(set(d_f) - set(a_f)):
        out.append(f"設計にあるが実物に無い関数: {name}")
    for name in sorted(set(a_f) - set(d_f)):
        out.append(f"実物にあるが設計に無い関数: {name}")
    for name in sorted(set(d_f) & set(a_f)):
        want, got = set(d_f[name] or []), set(a_f[name] or [])
        for miss in sorted(want - got):
            out.append(f"{name} が呼ぶはずの {miss} が実物に無い")
        for extra in sorted(got - want):
            out.append(f"{name} が実物では {extra} を呼んでいるが設計に書いていない")

    d_c = design.get("constants", {}) or {}
    a_c = actual.get("constants", {}) or {}
    for name in sorted(set(d_c) - set(a_c)):
        out.append(f"定数 {name} が実物に無い")
    for name in sorted(set(d_c) & set(a_c)):
        if d_c[name] != a_c[name]:
            out.append(f"定数 {name} の値が違う（設計={d_c[name]!r} 実物={a_c[name]!r}）")

    d_g = set(design.get("cli_flags", []) or [])
    a_g = set(actual.get("cli_flags", []) or [])
    for g in sorted(d_g - a_g):
        out.append(f"コマンドの旗 {g} が実物に無い")
    for g in sorted(a_g - d_g):
        out.append(f"コマンドの旗 {g} が設計に無い")
    return out


def write_actual(md_path: str) -> str:
    """実物から、設計書と同じ形の文書を書き出す（C-4）。手書きの設計書は1バイトも変えない。

    書き出すのは9つの節のうち5つ:
      §1 制約        = 要件定義書 §4.6 の H1〜H16 の見出しを引く（CC が飛ばせなくなる）
      §2 ベンチマーク = scan_contracts() の実測
      §5 仕様        = spec_from_impl() の結果
      §6 テスト一覧   = SELF_TESTS
      DESIGN_CONTRACT = 実物に在る公開の名前から作る
    """
    t = open(md_path, encoding="utf-8", errors="ignore").read()
    contract, reason = extract_block(t, CONTRACT_MARK)
    if contract is None:
        raise ValueError(f"DESIGN_CONTRACT が読めない: {md_path}（{reason}）")
    impl = _resolve_impl(md_path, str(contract.get("impl_file", "")))
    spec = spec_from_impl(impl)

    hs = []
    if os.path.exists(_REQUIREMENTS):
        for line in open(_REQUIREMENTS, encoding="utf-8", errors="ignore"):
            m = re.match(r"^#+\s*§4\.6\.(H\d+)\s+(.*)$", line.strip())
            if m:
                hs.append((m.group(1), m.group(2).strip()))

    ok, ng, outside = scan_contracts()

    L = []
    L.append(f"# {os.path.basename(md_path)}.actual.md — 実物から書き出した文書（手で書き換えない）")
    L.append("")
    L.append("> このファイルはプログラムが実物から作ります（`--write`）。**手で書き換えないでください。**")
    L.append("> 手書きの設計書と突き合わせるための相手です。違いは `--diff` が出します。")
    L.append("")
    L.append("## §1 制約（要件定義書 §4.6 から引いた）")
    L.append("")
    L.append("| # | 制約 |")
    L.append("|---|---|")
    for k, v in hs:
        L.append(f"| {k} | {v} |")
    L.append("")
    L.append("## §2 ベンチマーク（いまの実測）")
    L.append("")
    L.append(f"- DESIGN_CONTRACT が読める文書: {len(ok)}本")
    for n, c in ok:
        L.append(f"    - {os.path.basename(n)} -> {c.get('impl_file','')}")
    L.append(f"- 読めない文書: {len(ng)}本")
    for n, w in ng:
        L.append(f"    - {os.path.basename(n)} : {w}")
    L.append(f"- 対象外（目印の行が無い）: {len(outside)}本")
    for n in outside:
        L.append(f"    - {os.path.basename(n)}")
    L.append("")
    L.append("## §5 仕様（実物のコードから書き出した）")
    L.append("")
    L.append("| 公開する関数 | その中で呼んでいる公開の名前 |")
    L.append("|---|---|")
    for name in sorted(spec["public_functions"]):
        calls = spec["public_functions"][name]
        L.append(f"| `{name}` | {'・'.join(calls) if calls else '（無し）'} |")
    L.append("")
    L.append("| 定数 | 値 |")
    L.append("|---|---|")
    for name in sorted(spec["constants"]):
        L.append(f"| `{name}` | `{spec['constants'][name]!r}` |")
    L.append("")
    L.append(f"- コマンドの旗: {'・'.join(spec['cli_flags']) if spec['cli_flags'] else '（無し）'}")
    L.append("")
    L.append("## §6 テスト一覧（わざと壊して止まるか試すテスト）")
    L.append("")
    L.append("| # | 中身 |")
    L.append("|---|---|")
    for k, v in SELF_TESTS:
        L.append(f"| {k} | {v} |")
    L.append("")
    L.append("## DESIGN_CONTRACT（実物から作った）")
    L.append("")
    L.append("DESIGN_CONTRACT")
    L.append("")
    L.append("```json")
    L.append(json.dumps({"impl_file": str(contract.get("impl_file", "")),
                         "self_check_calls": sorted(spec["public_functions"])},
                        ensure_ascii=False, indent=1))
    L.append("```")
    L.append("")
    # ★C-7（2026-08-23 まこさん承認 67da88ef9ca8…）＝照らす中身を実物から書き出す。
    #   まこさんの逐語「極力自動生成で作成してほしい」。
    #   次に直すときは、下の SPEC を出発点にして「今回 何を変えるか」だけを手で書く。
    L.append("## SPEC（実物から作った・★次の設計書はここを出発点にする）")
    L.append("")
    L.append("> **手で書く欄を減らすための節です。**この中身を設計書の SPEC に写し、")
    L.append("> 今回 変えるところだけを手で直します。写したあと `--diff` が「齟齬: 0件」になります。")
    L.append("")
    L.append("SPEC")
    L.append("")
    L.append("```json")
    L.append(json.dumps({"impl_file": str(contract.get("impl_file", "")),
                         "public_functions": spec["public_functions"],
                         "constants": spec["constants"],
                         "cli_flags": spec["cli_flags"]},
                        ensure_ascii=False, indent=1))
    L.append("```")
    L.append("")

    out_path = md_path + ".actual.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"書き出した: {out_path}")
    print(f"H1〜H16: {len(hs)}件")
    print(f"SPEC を書き出した: 公開する関数 {len(spec['public_functions'])}件 / 定数 {len(spec['constants'])}件 / コマンドの旗 {len(spec['cli_flags'])}件")
    return out_path


def requirements_index():
    """要件の json を読み、{"R17": {title, accept, state}} の形で返す（★2026-08-26・要件 R17）。

    ★黙って空を返さない＝json が無い・壊れている・要件が0件 のときは例外を投げる
      （設計書 v2 §3.2 の1番）。黙って空を返すと「どの設計書も指していない要件は0件」に見えてしまう。
    """
    with open(_REQ_JSON, encoding="utf-8") as f:
        data = json.load(f)
    reqs = data.get("requirements") or []
    if not reqs:
        raise ValueError(f"要件が1件も無い: {_REQ_JSON}")
    out = {}
    for r in reqs:
        rid = str(r.get("id", "")).strip()
        if not rid:
            raise ValueError(f"id の無い要件が在る: {_REQ_JSON}")
        out[rid] = {"title": str(r.get("title", "")),
                    "accept": str(r.get("accept", "")),
                    "state": str(r.get("state", ""))}
    return out


def extract_requirements(md_text: str):
    """設計書から要件の番号を取り出す（★2026-08-26・決まりは設計書 v2 §3.4 の8つ）。

    1 目印は REQUIREMENTS: の1つだけ（半角・大文字・コロンも半角）
    2 行の先頭に在るものだけ（前に在ってよいのは空白だけ＝strip 済みの行で判定）
    3 ``` の囲みの中と、> の引用の行は数えない（outside_fence_lines の種別で外す）
    4 番号は R＋半角の数字。区切りは半角のカンマ。前後の空白は無視
    5 目印の行が2つ以上あれば、番号を全部 合わせる（和にする）
    6 同じ番号が2回 出たら1件に畳む
    7・8 番号が0件・要件に無い番号 は、ここでは落とさずそのまま返す（止めない＝表に出す）
    """
    ids = []
    for _i, s, kind in outside_fence_lines(md_text):
        if kind != "text" or not s.startswith(REQ_MARK):
            continue
        for w in s[len(REQ_MARK):].split(","):
            w = w.strip()
            if _REQ_ID_RE.match(w) and w not in ids:
                ids.append(w)
    return ids


def req_map():
    """要件と設計書の対応表のデータを作る（★2026-08-26・要件 R17）。

    ★数える相手は scan_contracts が返す全部（読める／読めない／対象外）。
      acceptance.md は scan_contracts が最初から含むので、ここで足さない（監査 cp8 の F-1＝二重足し）。
    戻り: {"requirements": [...], "documents": [...]}
    """
    index = requirements_index()
    ok, ng, out = scan_contracts()
    docs, seen = [], set()

    def add(path, state, impl):
        if path in seen:
            return
        seen.add(path)
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except Exception as e:
            text, state = "", f"{state}（読めない: {e}）"
        found = extract_requirements(text)
        # ★決まり7（設計書 v2 §3.4）＝目印は在るのに番号が0件、を「無し」と区別して出す。
        #   ★限界＝この見分けだけは囲みの中も数える（囲みを外す判定を2か所に作らないため）。
        has_mark = any(ln.strip().startswith(REQ_MARK) for ln in text.splitlines())
        docs.append({"path": path, "name": os.path.basename(path), "contract": state,
                     "impl_file": impl, "has_mark": has_mark,
                     "ids": [i for i in found if i in index],
                     "unknown_ids": [i for i in found if i not in index]})

    for p, c in ok:
        add(p, "読める", str(c.get("impl_file", "")))
    for p, why in ng:
        add(p, f"読めない（{why}）", "")
    for p in out:
        add(p, "対象外", "")

    pointed = {rid: [] for rid in index}
    for d in docs:
        for rid in d["ids"]:
            pointed[rid].append(d["name"])
    reqs = [dict(id=rid, pointed_by=pointed[rid], **index[rid]) for rid in index]
    return {"requirements": reqs, "documents": docs}


def format_req_map(data) -> str:
    """req_map のデータを、画面に出す文字列にする（★2026-08-26・要件 R17）。

    ★要件の言葉（title・accept・state）は要件の json からの複写をそのまま出す（縮めない）。
    """
    reqs = data.get("requirements") or []
    docs = data.get("documents") or []
    L = [f"■ 要件から見た表（{len(reqs)}件）"]
    for r in reqs:
        who = "、".join(r["pointed_by"]) if r["pointed_by"] else "（無し）"
        L.append(f"  {r['id']} {r['title']} ［{r['state']}］")
        L.append(f"      何ができたら満たしたと言えるか: {r['accept']}")
        L.append(f"      指している設計書: {who}")
    L.append("")
    L.append(f"■ 設計書から見た表（{len(docs)}本）")
    for d in docs:
        if d["ids"]:
            ids = "、".join(d["ids"])
        elif d.get("has_mark"):
            ids = "（目印は在るが番号が0件）"
        else:
            ids = "（無し）"
        impl = f"({os.path.basename(d['impl_file'])})" if d["impl_file"] else ""
        line = f"  {d['name']:26s} 契約: {d['contract']}{impl}  要件: {ids}"
        if d["unknown_ids"]:
            line += f"  ← 要件に無い番号: {'、'.join(d['unknown_ids'])}"
        L.append(line)
    none_ids = [r["id"] for r in reqs if not r["pointed_by"]]
    bad = [d for d in docs if d["unknown_ids"]]
    L.append("")
    L.append("■ まとめ")
    L.append(f"  どの設計書も指していない要件: {len(none_ids)}件"
             + (f"（{' '.join(none_ids)}）" if none_ids else ""))
    L.append(f"  要件に無い番号を書いている設計書: {len(bad)}本"
             + (f"（{'、'.join(d['name'] + ' の ' + '、'.join(d['unknown_ids']) for d in bad)}）" if bad else ""))
    return "\n".join(L)


def check_approval(md_path: str):
    """設計書が、まこさんの承認どおりのままかを見る（C-6・2026-08-23 まこさん承認 67da88ef9ca8…）。

    ★なぜ要るか＝56回目に、実物と設計書の食い違いが2件 出たとき、CC（私）が設計書の側を
      書き換えて0件にした。これを繰り返せば、食い違いはいつでも0件にできる。
      まこさんの逐語「不正を働かないよう」に、いちばん直接 当たるのがここ。

    戻り: (通すか, 画面に出す文字列)
      ・記録が在って一致    → (True,  "設計書の承認: 一致")
      ・記録が在って不一致  → (False, "設計書の承認: 外れています ...")
      ・記録が無い          → (True,  "設計書の承認: 記録なし（未承認）")
        ★記録が無いものを止めない理由＝いま承認の記録は0件で、止めると e35・e37・e38 が
          いきなり走らなくなる（既存を壊さない）。engine_tuner だけは hook 側で
          「記録が無ければ止める」にする。
    """
    if not os.path.exists(md_path):
        return False, f"設計書が無い: {md_path}"
    import hashlib
    now = hashlib.sha256(open(md_path, "rb").read()).hexdigest()
    key = os.path.abspath(md_path)
    table = {}
    if os.path.exists(_DESIGN_APPROVED):
        try:
            table = json.load(open(_DESIGN_APPROVED, encoding="utf-8"))
        except Exception:
            table = {}
    want = table.get(key)
    if want is None:
        return True, "設計書の承認: 記録なし（未承認）"
    if want == now:
        return True, "設計書の承認: 一致"
    return False, (f"設計書の承認: 外れています（承認後に設計書が変わりました）\n"
                   f"    承認された値: {want[:16]}…\n"
                   f"    いまの値    : {now[:16]}…\n"
                   f"    もう一度 承認するには: bash "
                   f"/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_design.sh {md_path}")


def check(md_path: str) -> bool:
    with open(md_path) as f:
        contract = extract_contract(f.read())
    if not contract:
        print(f"[STOP] DESIGN_CONTRACT が設計書に無い: {md_path}")
        return False
    impl = _resolve_impl(md_path, contract["impl_file"])
    src = open(impl, encoding="utf-8").read()
    print(f"design : {md_path}  ({contract.get('design_ref','')})")
    print(f"impl   : {contract['impl_file']}")
    ok = True
    calls = contract.get("self_check_calls")
    if calls:
        # contract-driven 方式: 実装が設計書を読んで自己チェックする「配線」が在るか。
        # 配線が在れば実装は設計書の部品リスト通りにしか動けない（成分欠落なら実行時に自停止）。
        # 配線を外す＝自己チェックを無力化する改変は、ここで検出してブロックする。
        # ★限界（2026-08-23 に明記）＝これは文字が在るかを見るだけ。中身が空の関数でも通る。
        #   その穴は diff_spec（--diff）が塞ぐ＝二段で守る。
        for c in calls:
            if c in src:
                print(f"  [PASS] 自己チェック配線あり: {c}")
            else:
                print(f"  [FAIL] 自己チェック配線が無い（外された疑い）: {c}")
                ok = False
    else:
        # 旧方式: 実装の代入式に設計要求成分が連結されているか（literal assignment・contract-driven でない実装用）
        tree = ast.parse(src)
        for symbol, required in contract.get("must_combine", {}).items():
            found, names = rhs_names_for_symbol(tree, symbol)
            if not found:
                print(f"  [FAIL] {symbol}: 代入が実装に無い")
                ok = False
                continue
            missing = [c for c in required if c not in names]
            if missing:
                print(f"  [FAIL] {symbol}: 設計要求の成分が欠落 → {missing}  (実装RHS={sorted(names)})")
                ok = False
            else:
                print(f"  [PASS] {symbol}: 全成分あり {required}")
    print("RESULT:", "PASS（設計通り）" if ok else "FAIL（設計と実装が乖離＝採点に進めない）")
    return ok


def self_test() -> bool:
    """メタ確認: わざと壊して検出するか（設計書 §6・8件）。

    ★T6・T7 は本物のファイルを1バイトも変えない。一時の場所に写して、写した方だけを削る。

    ★2026-08-24（58回目・まこさん承認 selftest-standalone-20260824）に、寄りかかりを外した。
      直す前＝本物の設計書（.claude/ratchet/contract_check_design.md）を名前で直に指していた。
      設計書は文書なので書き替わる。だから文書を1回 触るだけで検査が落ちた
      （57回目に実際に 11/11 → 4/11 になった）。
      直した後＝実物のコードから書き出した一覧を、その場で作る一時の設計書に書いて試す。
      本物の設計書がどうなっていても、この検査は動く。
    """
    me = os.path.abspath(__file__)
    results = {}

    # T1 目印を囲みの見出しに書いた形を読める
    t1_text = "説明の文\n\n```json DESIGN_CONTRACT\n{\"impl_file\": \"a.py\"}\n```\n"
    obj, _r = extract_block(t1_text, CONTRACT_MARK)
    results["T1"] = (obj is not None and obj.get("impl_file") == "a.py")

    # T2 json の閉じ括弧を消す
    t2_text = "DESIGN_CONTRACT\n\n```json\n{\"impl_file\": \"a.py\"\n```\n"
    obj, r2 = extract_block(t2_text, CONTRACT_MARK)
    results["T2"] = (obj is None and r2 is not None and "壊れ" in r2)

    # T3 impl_file が空
    t3 = os.path.join(tempfile.mkdtemp(), "t3.md")
    open(t3, "w", encoding="utf-8").write("DESIGN_CONTRACT\n\n```json\n{\"impl_file\": \"\"}\n```\n")
    _ok, ng, _out = scan_contracts([t3])
    results["T3"] = (len(ng) == 1 and "空" in ng[0][1])
    shutil.rmtree(os.path.dirname(t3), ignore_errors=True)

    # T4 目印が文章の中だけ＝対象外
    t4_text = "- DESIGN_CONTRACT を設計書に適用する\n\n```json\n{\"foo\": 1}\n```\n"
    obj, r4 = extract_block(t4_text, CONTRACT_MARK)
    results["T4"] = (obj is None and r4 == "対象外")

    # ★T5〜T8・T11 で使う設計書を、その場で作る（本物の設計書に寄りかからない・58回目）
    _tmp_design_dir = tempfile.mkdtemp()
    design_md = os.path.join(_tmp_design_dir, "self_test_design.md")
    open(design_md, "w", encoding="utf-8").write(
        "# 自己テスト専用の設計書（走るたびに作り、走り終わったら消す）\n\n"
        + CONTRACT_MARK + "\n\n```json\n"
        + json.dumps({"impl_file": os.path.relpath(me, _SDK)}, ensure_ascii=False)
        + "\n```\n\n" + SPEC_MARK + "\n\n```json\n"
        + json.dumps(spec_from_impl(me), ensure_ascii=False, indent=1) + "\n```\n")

    # T5〜T8 は、この一時の設計書とこのファイル自身で試す
    d_spec, r5 = spec_from_design(design_md)
    a_spec = spec_from_impl(me)
    if d_spec is None:
        for k in ("T5", "T6", "T7", "T8", "T11"):
            results[k] = False
        print(f"  ★一時の設計書の SPEC が読めない（{r5}）＝T5〜T8・T11 は試せない")
    else:
        # T8 全部そろっていれば通る
        results["T8"] = (diff_spec(d_spec, a_spec) == [])

        # T5 設計から関数を1つ消す
        cut = json.loads(json.dumps(d_spec))
        victim = sorted(cut["public_functions"])[0]
        cut["public_functions"].pop(victim)
        results["T5"] = any("実物にあるが設計に無い関数" in x for x in diff_spec(cut, a_spec))

        # T6 実物から関数を1つ消す（一時のコピー）
        tmpdir = tempfile.mkdtemp()
        try:
            src = open(me, encoding="utf-8").read()
            lines = src.splitlines()
            tree = ast.parse(src)
            target = None
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name == "diff_spec":
                    target = node
            if target is not None:
                cut_lines = lines[:target.lineno - 1] + lines[target.end_lineno:]
                p6 = os.path.join(tmpdir, "cut.py")
                open(p6, "w", encoding="utf-8").write("\n".join(cut_lines))
                results["T6"] = any("設計にあるが実物に無い関数" in x
                                    for x in diff_spec(d_spec, spec_from_impl(p6)))
            else:
                results["T6"] = False

            # T7 関数の中身を空にする（呼び出しを消す）
            target7 = None
            for node in ast.parse(src).body:
                if isinstance(node, ast.FunctionDef) and node.name == "extract_contract":
                    target7 = node
            if target7 is not None:
                head = lines[target7.lineno - 1]
                indent = " " * (len(head) - len(head.lstrip()) + 4)
                empty = lines[:target7.lineno] + [f"{indent}return None"] + lines[target7.end_lineno:]
                p7 = os.path.join(tmpdir, "empty.py")
                open(p7, "w", encoding="utf-8").write("\n".join(empty))
                results["T7"] = any("呼ぶはずの" in x
                                    for x in diff_spec(d_spec, spec_from_impl(p7)))
            else:
                results["T7"] = False
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        # T11 --write が書き出した SPEC を使うと、突き合わせが 0件 になる（C-7）
        out11 = write_actual(design_md)
        gen_spec, _r11 = extract_block(open(out11, encoding="utf-8").read(), SPEC_MARK)
        results["T11"] = (gen_spec is not None and diff_spec(gen_spec, a_spec) == [])

    # 一時の設計書は、ここまでで用が済んだので消す
    shutil.rmtree(_tmp_design_dir, ignore_errors=True)

    # ★T9・T10 は、設計書を1バイトも使わない（どちらも自分で一時のファイルを作る）。
    #   直す前は「設計書が読めたとき」の分かれ道の中に在り、設計書が読めないだけで
    #   巻き添えで落ちていた（58回目に外へ出した）。だから、ここで必ず試す。

    # T9 SPEC が無い設計書は「SPEC が無い」と分かる（C-5 の判定の元）
    t9_text = "## §10 DESIGN_CONTRACT\n\nDESIGN_CONTRACT\n\n```json\n{\"impl_file\": \"x.py\"}\n```\n"
    t9_dir = tempfile.mkdtemp()
    try:
        p9 = os.path.join(t9_dir, "no_spec.md")
        open(p9, "w", encoding="utf-8").write(t9_text)
        s9, r9 = spec_from_design(p9)
        results["T9"] = (s9 is None and r9 == "対象外")
    finally:
        shutil.rmtree(t9_dir, ignore_errors=True)

    # T10 設計書を1文字 書き換えると承認が外れる（C-6）
    t10_dir = tempfile.mkdtemp()
    try:
        p10 = os.path.join(t10_dir, "approved.md")
        open(p10, "w", encoding="utf-8").write("設計書の中身\n")
        import hashlib
        table = {}
        if os.path.exists(_DESIGN_APPROVED):
            try:
                table = json.load(open(_DESIGN_APPROVED, encoding="utf-8"))
            except Exception:
                table = {}
        keep = dict(table)
        table[os.path.abspath(p10)] = hashlib.sha256(open(p10, "rb").read()).hexdigest()
        os.makedirs(os.path.dirname(_DESIGN_APPROVED), exist_ok=True)
        json.dump(table, open(_DESIGN_APPROVED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        ok_before, _m1 = check_approval(p10)
        open(p10, "a", encoding="utf-8").write("1文字\n")
        ok_after, _m2 = check_approval(p10)
        results["T10"] = (ok_before and not ok_after)
        json.dump(keep, open(_DESIGN_APPROVED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    finally:
        shutil.rmtree(t10_dir, ignore_errors=True)

    # ── ★2026-08-26（要件 R17・設計書 v2 §5）＝T12〜T17。本物のファイルは1バイトも変えない ──
    results["T12"] = extract_requirements(
        "# 見出し\n\n```\nREQUIREMENTS: R3\n```\n") == []
    results["T13"] = extract_requirements(
        "> REQUIREMENTS: R3\n"
        "ＲＥＱＵＩＲＥＭＥＮＴＳ: R4\n"
        "REQUIREMENTS： R5\n"
        "★REQUIREMENTS: R6\n"
        "requirements: R7\n") == []
    results["T14"] = extract_requirements(
        "REQUIREMENTS: R3, R5\n\nなにか\n\nREQUIREMENTS:  R5 ,R17\n") == ["R3", "R5", "R17"]

    fake = {"requirements": [
        {"id": "R1", "title": "あ", "accept": "い", "state": "完了", "pointed_by": ["x.md"]},
        {"id": "R2", "title": "う", "accept": "え", "state": "作業中", "pointed_by": []}],
        "documents": [
        {"name": "x.md", "contract": "読める", "impl_file": "", "ids": ["R1"], "unknown_ids": ["R99"]}]}
    shown = format_req_map(fake)
    results["T15"] = ("要件に無い番号: R99" in shown
                      and "要件に無い番号を書いている設計書: 1本" in shown)
    results["T17"] = ("どの設計書も指していない要件: 1件（R2）" in shown)

    # T16＝要件の json の写しで accept を1文字 変えると、表に出る文字も変わる。
    #   ★読む先（_REQ_JSON）を写しへ向け、終わったら必ず戻す。本物は1バイトも変えない。
    t16_dir = tempfile.mkdtemp()
    global _REQ_JSON
    keep_req = _REQ_JSON
    try:
        d16 = json.load(open(keep_req, encoding="utf-8"))
        first = d16["requirements"][0]
        marker = "★T16の目印★"
        first["accept"] = str(first.get("accept", "")) + marker
        p16 = os.path.join(t16_dir, "req.json")
        json.dump(d16, open(p16, "w", encoding="utf-8"), ensure_ascii=False)
        before = format_req_map(req_map())
        _REQ_JSON = p16
        after = format_req_map(req_map())
        results["T16"] = (marker not in before) and (marker in after)
    finally:
        _REQ_JSON = keep_req
        shutil.rmtree(t16_dir, ignore_errors=True)

    good = 0
    for k, v in SELF_TESTS:
        got = results.get(k, False)
        print(f"  {k} {'期待どおり' if got else '★合わない'} : {v}")
        good += 1 if got else 0
    print(f"テスト {good}/{len(SELF_TESTS)} 期待どおり")
    return good == len(SELF_TESTS)


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(0 if self_test() else 1)

    if "--scan-contracts" in sys.argv:
        _ok, _ng, _out = scan_contracts()
        print(f"読めた契約: {len(_ok)}件")
        for _n, _c in _ok:
            print(f"    {os.path.basename(_n)} -> {_c.get('impl_file','')}")
        print(f"読めない契約: {len(_ng)}件")
        for _n, _w in _ng:
            print(f"    {os.path.basename(_n)} : {_w}")
        print(f"対象外: {len(_out)}件")
        for _n in _out:
            print(f"    {os.path.basename(_n)}")
        sys.exit(1 if _ng else 0)

    if "--diff" in sys.argv:
        _md = sys.argv[sys.argv.index("--diff") + 1]
        _d, _r = spec_from_design(_md)
        if _d is None:
            print(f"[STOP] SPEC が設計書に無い: {_md}（{_r}）")
            sys.exit(1)
        _impl = _resolve_impl(_md, str(_d.get("impl_file", "")))
        _diff = diff_spec(_d, spec_from_impl(_impl))
        print(f"design : {_md}")
        print(f"impl   : {_d.get('impl_file','')}")
        print(f"齟齬: {len(_diff)}件")
        for _x in _diff:
            print(f"    {_x}")
        sys.exit(1 if _diff else 0)

    if "--req-map" in sys.argv:
        # ★2026-08-26（要件 R17）＝要件と設計書の対応表を出す。止めない（いつも 0 で終わる）。
        print(format_req_map(req_map()))
        sys.exit(0)

    if "--check-approval" in sys.argv:
        _md = sys.argv[sys.argv.index("--check-approval") + 1]
        _ok2, _msg = check_approval(_md)
        print(_msg)
        sys.exit(0 if _ok2 else 1)

    if "--write" in sys.argv:
        _md = sys.argv[sys.argv.index("--write") + 1]
        write_actual(_md)
        sys.exit(0)

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(0 if check(sys.argv[1]) else 1)
