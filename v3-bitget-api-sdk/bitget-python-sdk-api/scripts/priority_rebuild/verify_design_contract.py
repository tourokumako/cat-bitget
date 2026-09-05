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
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
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
    # ★2026-09-02（監査 cp13 の A-7）＝照合A〜D を、わざと壊して試す。
    #   直す前＝T1〜T17 は全部、この強制を作る前から在ったもの＝新しいコードを1行も試さずに
    #   「自己テストが通る」を満たせた（監査 E-6）。
    #   ★監査の8件のうち「空の辞書」は hook（require_acceptance_before_impl.sh）の判定なので、
    #     ここでは試せない。実際に走る経路のテストで測る（設計書 §5）。
    ("N1", "照合A＝触っていない関数を『触った』と言わない（誤検出しない）"),
    ("N2", "照合A＝新しく足した関数を拾う（見落とさない）"),
    ("N3", "照合B＝設計書に書いた関数が実装に無ければ落ちる"),
    ("N4", "照合C＝正本から作った名前が中身に無ければ落ちる（自明な名前では通らない）"),
    ("N5", "照合D＝一覧の一部だけを直書きすると落ちる"),
    ("N6", "照合A＝道具の承認の印が無ければ落ちる"),
    ("N7", "差分がゼロ（commit 済み）でも照合B は走る"),
    # ★2026-09-03（監査 cp14・まこさん承認 iter="impl-lock-fix-cp14-20260903"）
    ("N8", "照合A・B＝設計書の impl_functions が凍結された版と違えば落ちる（B-1）"),
    ("N9", "照合A・B＝凍結された版が無ければ落ちる（B-1・fail-closed）"),
    ("N10", "照合C＝kind の掘り下げの経路で正本から名前が取れる（B-3）"),
    ("N11", "照合C＝正本に無い kind は、黙って全体に落ちずに落ちる（B-3）"),
    ("N12", "承認と同じ形＝{from,kind} を配列へ展開できる（B-2・resolve_spec_list）"),
    ("N5b", "照合D＝承認が書き出す形（展開済みの配列）で成立する（B-2）"),
    # ★2026-09-05（監査 cp20 の C1〜C3・まこさん承認 iter="freeze-fail-closed-cp20-20260905"）
    ("N13", "照合A・B＝凍結が空（理由なし）なら、比較の前に落ちる（C3）"),
    ("N14", "照合A・B＝理由の在る空（cp19 の形）は、その文では落ちない（C3 の対）"),
    ("N15", "凍結する契約＝契約の後ろに impl_file だけの囲みが在っても、契約の側を取る（C2）"),
    ("N16", "凍結する契約＝impl_file だけの囲みが先に在っても、契約の側を取る（並び順に影響されない・C2）"),
    ("N17", "凍結する契約＝impl_functions が空で理由が無ければ止まる側（C1）"),
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


def contract_for_freeze(md_text: str):
    """承認の瞬間に凍結する契約を、設計書から1つ取る（監査 cp20 の C1・C2・
    まこさん承認 2026-09-05 iter="freeze-fail-closed-cp20-20260905"）。

    ★なぜ要るか＝承認スクリプトは「最後の impl_file の囲み」を自前の regex で取り、
      impl_functions が無ければ黙って {} を凍結した（2026-09-04 に3回・空が凍結されたのは2本）。
      書き込みの門は「最初の impl_file の囲み」を取っていた＝囲みの選択規則が3通り在った。
    ★直した後＝承認・門・照合の3つが、extract_block（目印の行の後ろの囲み）で契約を選ぶ。

    戻り: (契約の dict, None) ＝通す ／ (None, 理由の文) ＝止める（fail-closed）。
      止めるのは3通り＝①契約が読めない ②impl_functions が辞書でない
      ③impl_functions が空で no_impl_functions_reason が無い。
      理由の在る空（cp19 の形）は通す＝凍結は {} のまま書かれ、照合の側（C3）が理由の有無で区別する。
    ★限界（正直に）＝理由の中身は見ない。何か1文字でも書けば「正しい空」として通る（設計書 §9 の I）。
    """
    obj, reason = extract_block(md_text, CONTRACT_MARK)
    if obj is None:
        return None, f"DESIGN_CONTRACT（目印の行の後ろの json）が読めない（{reason}）"
    fz = obj.get("impl_functions")
    if not isinstance(fz, dict):
        return None, "impl_functions が無い（辞書の形でない）"
    if not fz and not obj.get("no_impl_functions_reason"):
        return None, ("impl_functions が空なのに no_impl_functions_reason が無い"
                      "（監査 cp20 の C1＝空を凍結しない）")
    return obj, None


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
      ・記録が無い          → (False, "設計書の承認: 記録なし（未承認）")

    ★2026-09-03（監査 cp16 の E-9・まこさん指名・承認 36051934db6eede3）＝止める側へ変えた。
      監査の逐語＝「『記録なし（未承認）→ 通す』を『止める』に変える」。
      直す前の実測（監査 cp16 の Q2 の7番）＝design_approved.json を消すと
        --check-approval が rc=0（「記録なし（未承認）」）で、上流ゲートも rc=0 だった。
        ＝承認の記録を消せば、承認なしで通る道が開いていた。
      ★旧の理由（消さずに残す）＝「止めると e35・e37・e38 がいきなり走らなくなる」。
        これは いまも当たる。承認の記録が無い設計書は、
        `bash .claude/hooks/approve_design.sh <設計書>` を1回 打つまで走らない。
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
        # ★2026-09-03（監査 cp16 の E-9）＝記録が無いときは止める（fail-closed）
        return False, ("設計書の承認: 記録なし（未承認）\n"
                       f"    承認: bash .claude/hooks/approve_design.sh {md_path}")
    if want == now:
        return True, "設計書の承認: 一致"
    return False, (f"設計書の承認: 外れています（承認後に設計書が変わりました）\n"
                   f"    承認された値: {want[:16]}…\n"
                   f"    いまの値    : {now[:16]}…\n"
                   f"    もう一度 承認するには: bash "
                   f"/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_design.sh {md_path}")


# ══ 設計書どおりにしか実装できなくする（M2 の外・汎用・2026-09-02 まこさん承認 iter="impl-lock-20260902"）══
#
# なぜ要るか（実測）＝2026-09-02 に、設計書に「4通りを展開する」と書いて実装は2通りだった。
#   既に在る照合3つ（self_check_calls・must_combine・--diff）は どれも止めなかった。
#   見つけたのは既存のテストが3分12秒 走った後で、CC が作ったテスト14件はどれも通した。
#
# 4つの照合（設計書 §3.3）:
#   A  git の差分で触った関数 ⊆ impl_functions   ＝設計書に書いていない関数を触ったら止める
#   B  impl_functions ⊆ git の差分で触った関数   ＝設計書に書いたのに実装していないなら止める
#   C  must_use の名前が、その関数の中に在るか    ＝中身が設計と違うなら止める
#   D  spec_lists の一覧が、実装で読まれているか  ＝一覧をコードに焼いたら止める
SPEC_LISTS_PATH = (pathlib.Path(__file__).resolve().parents[2]
                   / ".claude" / "ratchet" / "spec_lists.json")


def load_spec_lists() -> dict:
    """承認のときに設計書から書き出された一覧を読む（設計書 §3.1 の段2 が作る）。

    ★実装はこの一覧を読む。コードに一覧を焼かない＝設計書と実装で一覧が2か所に無い。

    ★2026-09-02（監査 cp13 の A-1）＝ファイルが無ければ例外を出す（fail-closed）。
      直す前＝無ければ空の辞書を返していた＝一覧を1件も照らさずに通っていた（監査 S-2・S-3）。
    """
    if not SPEC_LISTS_PATH.exists():
        raise FileNotFoundError(
            f"一覧のファイルがありません: {SPEC_LISTS_PATH}\n"
            "    ＝承認のときに作られます。まこさんに承認を打ってもらってください:\n"
            "      bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh")
    return json.loads(SPEC_LISTS_PATH.read_text(encoding="utf-8"))


# ★2026-09-03（監査 cp14 の B-1・Critical）＝承認の瞬間に凍結した impl_functions の置き場。
#   監査の逐語＝「impl_functions は『実装の後に実物から取り直す』ことを禁止する。具体＝承認の瞬間に
#   impl_functions を一覧のファイルと同じ場所へ凍結保存し、照合A・B は凍結された版と比べる。
#   承認後に impl_functions が変わったら止める」。
FROZEN_PATH = SPEC_LISTS_PATH.with_name("impl_functions_frozen.json")


def frozen_impl_functions() -> dict:
    """承認のときに凍結された impl_functions を読む（監査 cp14 の B-1）。

    ★なぜ要るか＝79回目に、照合が食い違いを9件 指摘したので、CC が設計書の impl_functions を
      実装から作り直して通した（監査 P-4＝自明なテスト）。期待値を実装から作れる限り、
      照合A・B は永久に通る。だから期待値は承認の瞬間に凍結し、以後 変えられないようにする。
    ★無ければ例外（fail-closed）＝黙って設計書の側を使わない。
    """
    p = pathlib.Path(FROZEN_PATH)
    if not p.exists():
        raise FileNotFoundError(
            f"凍結された impl_functions がありません: {p}\n"
            "    ＝承認のときに作られます。まこさんに承認を打ってもらってください:\n"
            "      bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh")
    data = json.loads(p.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not str(k).startswith("_")}


def resolve_spec_list(spec: dict) -> tuple[list, str]:
    """設計書の {"from","kind"} を、正本から配列へ展開する（監査 cp14 の B-2・Critical）。

    ★監査の逐語＝「承認スクリプトが spec_lists の {"from","kind"} を その場で解決して配列に
      展開してから 一覧のファイルへ書く（いまは辞書をそのまま写している＝65-66行）」。
    ★直す前に何が起きていたか（実測）＝承認は辞書をそのまま書き、照合D は「2件以上の配列」を
      求めていた。だから 辞書は必ず落ち、配列は hook が拒否する＝どちらの道でも照合D は成立しない。
    ★展開のやり方は must_use_from_source と同じ（1か所に書く＝2か所に書き写さない）。
    戻り＝(配列, 出どころの説明)。展開できなければ配列は空。
    """
    return must_use_from_source(spec)


def names_in_function(tree, func: str) -> tuple[bool, set]:
    """関数 func の中に現れる名前を全部 集める（戻り＝(関数が在るか, 名前の集合)）。

    ★must_combine（変数の代入の右辺だけ）との違い＝関数の中身を丸ごと見る。
      2026-09-02 の食い違いは、代入ではなく関数の中の for 文だったので、must_combine では見えなかった。
    """
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func:
            got = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name):
                    got.add(sub.id)
                elif isinstance(sub, ast.Attribute):
                    got.add(sub.attr)
            return True, got
    return False, set()


def functions_ast(src: str) -> dict:
    """ソースを構文木にして、関数ごとの値（ast.dump）を返す。

    ★2026-09-02（監査 cp13 の A-3・Critical）に新設。
      戻り＝{関数の名前: 構文木を文字にしたもの}。クラスの中の関数は「クラス名.関数名」。
      **モジュール直下（import・定数・トップレベルの処理）も 1つのまとまりとして入れる**
      ＝監査 E-2・抜け道8（モジュール直下を変えても照合A に掛からない）への答え。
      空白とコメントだけの違いは、構文木が同じなので拾わない。
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {}
    out, top = {}, []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = ast.dump(node)
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[f"{node.name}.{sub.name}"] = ast.dump(sub)
        else:
            top.append(ast.dump(node))
    if top:
        out["<モジュール直下>"] = "\n".join(top)
    return out


def head_source(path: str) -> tuple[str, bool]:
    """HEAD の版のソースを取る。戻り＝(ソース, 取れたか)。

    ★取れなかったこと（新しく作ったファイル・git が落ちた）を、呼ぶ側に必ず伝える
      ＝黙って空を返さない。
    """
    try:
        root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                              cwd=os.path.dirname(os.path.realpath(path)),
                              capture_output=True, text=True, timeout=30).stdout.strip()
        if not root:
            return "", False
        rel = os.path.relpath(os.path.realpath(path), root)
        r = subprocess.run(["git", "-C", root, "show", f"HEAD:{rel}"],
                           capture_output=True, text=True, timeout=30)
        return (r.stdout, True) if r.returncode == 0 else ("", False)
    except Exception:                                      # noqa: BLE001
        return "", False


def touched_functions(path: str) -> set:
    """この実装で触った関数を、構文木の前後比較で集める（監査 cp13 の A-3）。

    ★直す前＝`git diff -U0` の見出し行を正規表現で読んでいた。
      見出しに出るのは「変更行を含む **直前の** 関数」であって「触った関数」ではない。
      監査の実測＝新しく足した6関数が1件も検出されず、触っていない関数を1件 誤検出した。
    ★直した後＝HEAD の版と いまの版を、関数ごとに構文木で比べる。
      触った関数 ＝ 値が変わった関数 ＋ 増えた関数 ＋ 消えた関数。
    ★HEAD に無いファイル（新しく作った）＝ファイルの中の全部の関数を「触った」とする。
    ★差分がゼロのときは空を返す＝呼ぶ側が「全関数と照合」に落とす（監査 A-3 の指示）。
    """
    try:
        now = functions_ast(open(path, encoding="utf-8").read())
    except Exception:                                      # noqa: BLE001
        return set()
    src, got = head_source(path)
    if not got:
        return set(now)                                    # 新しく作ったファイル＝全部が触った関数
    old = functions_ast(src)
    changed = {k for k in set(now) | set(old) if now.get(k) != old.get(k)}
    return changed


def check_impl_functions(contract: dict, md_path: str, frozen: dict | None = None) -> list:
    """照合A・B＝git の差分で触った関数と、承認のときに凍結した impl_functions を両方向で照らす。

    ★あわせて、この道具自身が承認のときから書き換えられていないかも見る（設計書 §3.4 の5・抜け道5）。
      印は approve_impl.sh が承認の瞬間に書く＝まこさんの承認なしに道具を書き換えると、ここで止まる。

    ★2026-09-03（監査 cp14 の B-1・Critical）＝比べる相手を「設計書」から「凍結された版」に変えた。
      直す前＝期待値が設計書の中に在った＝照合が食い違いを指摘したら、設計書の側を実装から
      作り直せば通った（79回目に実際にそうした＝監査 P-4）。
      直した後＝期待値は承認の瞬間に凍結され、設計書が凍結版と違えば止まる。
    ★frozen を渡せるのは番人（--self-test）のためだけ。本番では None＝凍結ファイルを読む。
    """
    ng = []
    mark = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/verify_tool.approved")
    # ★2026-09-02（監査 cp13 の A-1・Critical）＝印が無ければ落とす（fail-closed）。
    #   直す前＝`if mark.exists():` だった＝印を消すと、道具の改ざんの検査が丸ごと消えた
    #   （監査の抜け道9・I-3 の枝(b)）。しかも本番では印が1度も作られていなかった（監査 S-1）。
    if not mark.exists():
        ng.append(f"照合の道具の承認の印がありません（{mark}）"
                  "＝まこさんに承認を打ってもらってください: "
                  "bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh")
    else:
        me = pathlib.Path(__file__).resolve()
        now = hashlib.sha256(me.read_bytes()).hexdigest()
        want = mark.read_text(encoding="utf-8").strip()
        if want and now != want:
            ng.append(f"照合の道具が承認のときから変わっている（いま {now[:16]}… ／ 承認時 {want[:16]}…）"
                      "＝まこさんの承認を取り直すこと")
    # ★B-1＝期待値は凍結された版。設計書の側は「凍結と同じか」を見るためだけに使う。
    #   ★2026-09-03 に実測して範囲を決めた＝いま作業している設計書のときだけ凍結と比べる。
    #     凍結は「いま承認されている1本」の期待値なので、過去の工程の控え（別の iter の記録）と
    #     比べると必ず食い違う。実測＝控え93件のうち71件が落ちた（直す前は8件）。
    #     控えは過去の記録なので、その控え自身に書いてある impl_functions で照らす。
    design = contract.get("impl_functions") or {}
    _live_md = os.path.join(_REPO, ".claude", "state", "acceptance.md")
    _is_live = bool(md_path) and os.path.realpath(md_path) == os.path.realpath(_live_md)
    if frozen is None and not _is_live:
        # ★2026-09-03（監査 cp15 の C-5）＝控えにも、その控えの凍結と比べる。
        #   監査の逐語＝「控えごとに承認時の凍結を acceptance_archive/<iter>.frozen.json として
        #   一緒に保存し、控えを照合するときはその控えの凍結と比べる」。
        #   ★2026-09-03（監査 cp16 の E-9・まこさん指名・承認 36051934db6eede3）
        #     ＝凍結が無い控えは止める。
        #     監査の逐語＝「控えも同じで、凍結が無い控えは止める」。
        #     直す前の実測（監査 cp16 の C-5）＝凍結ファイルを消すと rc=0
        #       （「この控えには凍結がありません＝設計書自身と比べます」＝循環に戻る）。
        #       しかも控えは git 未追跡なので、消しても跡が残らなかった。
        #     ★旧の理由（消さずに残す）＝「既存の控え93本を落とさないため」。
        #       これは いまも当たる。凍結の無い控えを照らすと、ここで止まる。
        _arch = pathlib.Path(str(md_path)).with_suffix(".frozen.json")
        if _arch.exists():
            try:
                _d = json.loads(_arch.read_text(encoding="utf-8"))
                frozen = {k: v for k, v in _d.items() if not str(k).startswith("_")}
                print(f"  [INFO] 控えの凍結と比べます: {_arch.name}")
            except Exception:                                # noqa: BLE001
                ng.append(f"控えの凍結が読めません: {_arch.name}"
                          "（監査 cp16 の E-9＝記録が読めないときは止める）")
                return ng
        else:
            ng.append(f"この控えには凍結がありません: {_arch.name}"
                      "（監査 cp16 の E-9＝記録が無いときは止める）"
                      "／直す前は、設計書自身と比べて通していた＝循環に戻っていた")
            return ng
    if frozen is None:
        try:
            frozen = frozen_impl_functions()
        except FileNotFoundError as e:                       # noqa: BLE001
            ng.append(str(e))
            return ng
    # ★2026-09-05（監査 cp20 の C3・Critical・まこさん承認 iter="freeze-fail-closed-cp20-20260905"）
    #   ＝凍結が空なら、比較の前に止める。
    #   直す前＝design も {} なら文字列が一致して通った＝1関数も照合していないのに「設計通り」。
    #   理由の在る空（cp19 の形＝設計書に no_impl_functions_reason が在る）は通す。
    if not frozen and not contract.get("no_impl_functions_reason"):
        ng.append("凍結された impl_functions が空です（承認のときに空が凍結された疑い・監査 cp20 の C3）"
                  "＝設計書に no_impl_functions_reason が無い限り、比較の前に止めます。"
                  "\n    設計書の impl_functions を書いて、まこさんに承認を打ち直してもらってください。")
        return ng
    _d = json.dumps(design, sort_keys=True, ensure_ascii=False)
    _f = json.dumps(frozen, sort_keys=True, ensure_ascii=False)
    if _d != _f:
        ng.append("impl_functions が承認のときから変わっています"
                  "（＝実装に合わせて期待値を作り直した疑い・監査 cp14 の B-1／P-4）。"
                  f"\n    設計書 {hashlib.sha256(_d.encode()).hexdigest()[:16]}…"
                  f" ／ 凍結 {hashlib.sha256(_f.encode()).hexdigest()[:16]}…"
                  "\n    実装を設計書どおりに直すか、まこさんに再承認を打ってもらってください。")
        return ng
    spec = frozen
    for rel, want in spec.items():
        impl = _resolve_impl(md_path, rel)
        got = touched_functions(impl)
        if not got:
            # ★2026-09-02（監査 cp13 の A-3）＝[SKIP] をやめ、ファイルの中の全関数と照合する。
            #   直す前＝差分がゼロ（commit 済み）だと、照合A・B が丸ごと消えた（監査の抜け道1）。
            #   ★照合A（設計書に書いていない関数を触ったか）は、差分がゼロだと判定できない。
            #     黙って通さず、その旨を画面に出す。
            try:
                allf = set(functions_ast(open(impl, encoding="utf-8").read()))
            except Exception:                              # noqa: BLE001
                allf = set()
            for miss in sorted(set(want) - allf):
                ng.append(f"B {rel}: 設計書に書いたのに実装に無い → {miss}")
            print(f"  [INFO] {rel}: 差分がゼロ（commit 済み）＝照合B だけを"
                  f"ファイルの中の全関数（{len(allf)}件）と行いました。照合A は判定できません")
            continue
        for extra in sorted(got - set(want)):
            ng.append(f"A {rel}: 設計書に書いていない関数を触った → {extra}")
        for miss in sorted(set(want) - got):
            ng.append(f"B {rel}: 設計書に書いたのに実装していない → {miss}")
        if not (got - set(want)) and not (set(want) - got):
            print(f"  [PASS] {rel}: 触った関数と設計書が一致（{len(got)} 件）")

    # ★2026-09-02（監査 cp13 の A-5・双方向）＝設計書に列挙していないファイルを触ったら落とす。
    #   直す前＝impl_functions に書いたファイルしか見なかった＝中身を別のファイルへ移せば通った
    #   （監査の抜け道7）。範囲＝scripts/priority_rebuild／.claude/hooks／.claude/tools の .py。
    #
    # ★2026-09-03＝いま作業している設計書のときだけ行う（実測して直した）。
    #   直す前＝承認済みの控え（過去の工程の設計書）にも掛けていた。控えは別の工程の記録なので、
    #   いま触っているファイルと照らしても意味が無く、控え91件が全部 落ちた。
    _live = os.path.join(_REPO, ".claude", "state", "acceptance.md")
    if not md_path or os.path.realpath(md_path) != os.path.realpath(_live):
        return ng
    try:
        _root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                               capture_output=True, text=True, timeout=30).stdout.strip()
        _st = subprocess.run(["git", "-C", _root, "status", "--porcelain"],
                             capture_output=True, text=True, timeout=30).stdout if _root else ""
    except Exception:                                      # noqa: BLE001
        _st = ""
    for _line in _st.splitlines():
        _f = _line[3:].strip().split(" -> ")[-1]
        if not _f.endswith(".py"):
            continue
        if not any(s in _f for s in ("scripts/priority_rebuild/", ".claude/hooks/", ".claude/tools/")):
            continue
        if not any(_f.endswith(_k) or _k.endswith(_f) for _k in spec):
            ng.append(f"A(双方向) {_f}: 設計書の impl_functions に書いていないファイルを触った")
    return ng


def must_use_from_source(spec: dict) -> tuple[list, str]:
    """正本のファイルから「その関数が使うはずの名前」を機械で作る（監査 cp13 の A-6）。

    ★監査の逐語＝「must_use を CC に手書きさせず、spec_lists から機械で導く」。
      CC が名前を選べると、壊れても消えない名前だけを書いて通せる（監査の抜け道4・Q2 の実測）。
    ★設計書には from（正本のファイル）と kind（その中のどの枠か）だけを書く。値は書かない。
    戻り＝(名前の一覧, 出どころの説明)
    """
    src_path = str((spec or {}).get("from") or "")
    if not src_path:
        return [], "設計書に from（正本のファイル）が書いていない"
    p = pathlib.Path(src_path)
    if not p.is_absolute():
        p = pathlib.Path(_REPO) / src_path
    if not p.exists():
        return [], f"正本のファイルがない: {p}"
    kind = str((spec or {}).get("kind") or "")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:                                 # noqa: BLE001
        return [], f"正本を json として読めない: {p} → {e}"
    # ★2026-09-03（監査 cp14 の B-3・Critical）＝kind に「掘り下げの経路」を許し、
    #   正本に無い kind は 黙って全体に落ちずに止める。
    #   監査の逐語＝「kind に 掘り下げの経路 を許し、kind が正本に存在しないときは
    #     黙って全体に落ちず、例外で止める（925行）」。
    #   直す前の実測（監査 N-c）＝存在しない kind を渡すと、エラーにならず先頭15鍵を返した
    #     ＝正本の指し間違いが検出されない。
    #   ★経路の書き方＝"機械が読む判定/次元" のように "/" で区切る。1段だけなら いままでと同じ。
    node = data
    for seg in [s for s in kind.split("/") if s != ""]:
        if isinstance(node, dict):
            if seg not in node:
                return [], (f"正本に kind の段がない: {p.name} の「{seg}」"
                            f"（経路＝{kind}／その段に在る鍵＝{sorted(node.keys())[:8]}…）")
            node = node[seg]
            continue
        if isinstance(node, list) and seg.isdigit() and int(seg) < len(node):
            node = node[int(seg)]
            continue
        return [], f"正本の「{seg}」が掘り下げられない（経路＝{kind}／型＝{type(node).__name__}）"
    if isinstance(node, dict):
        return sorted(node.keys()), f"{p.name} の {kind or 'ぜんぶ'} の鍵 {len(node)} 件"
    if isinstance(node, list):
        return [str(x) for x in node], f"{p.name} の {kind or 'ぜんぶ'} の要素 {len(node)} 件"
    return [], f"正本の {kind} が辞書でも配列でもない"


def check_must_use(contract: dict, src: str, md_path: str = "") -> list:
    """照合C＝要求された名前が、その関数の中に在るか（構文木で関数の中身を見る）。

    ★2026-09-02（監査 cp13 の A-6）＝要求する名前の出どころを2つに分けた。
      ①must_use_from … 正本のファイルから機械が作る（CC は名前を選べない）
      ②must_use      … CC が手で書く（正本が無いとき）。**これは「機械で照らせない」に数える**
    ★2026-09-02（監査 cp13 の E-3）＝impl_functions に書いた全部の .py を見る。
      直す前＝impl_file の1本だけを見ていた＝別のファイルに在る関数を「実装に無い」と誤って言った。
    """
    ng = []
    trees = {}
    for rel in (contract.get("impl_functions") or {}):
        if not str(rel).endswith(".py"):
            continue
        try:
            trees[rel] = ast.parse(open(_resolve_impl(md_path, rel), encoding="utf-8").read())
        except Exception:                                  # noqa: BLE001
            continue
    if not trees:
        try:
            trees[str(contract.get("impl_file") or "<impl_file>")] = ast.parse(src)
        except SyntaxError:
            return ["C: 実装を構文木にできない"]

    def _find(func: str, need=()) -> tuple:
        """その関数を持つファイルを探す。

        ★2026-09-03（実測して直した）＝同じ名前の関数が複数のファイルに在ると、
          先に見つかった方だけを見て「名前が無い」と誤って言った（実測＝selftest が
          gen_audit_request.py と gen_audit_todo.py の両方に在る）。
          ＝要求を満たす候補が在れば、それを返す。無ければ最初の候補を返す（落とすため）。
        """
        first = ("", set())
        for rel, t in trees.items():
            ok, got = names_in_function(t, func)
            if not ok:
                continue
            if not first[0]:
                first = (rel, got)
            if all(c in got for c in need):
                return rel, got
        return first

    for func, s in (contract.get("must_use_from") or {}).items():
        required, why = must_use_from_source(s if isinstance(s, dict) else {})
        if not required:
            ng.append(f"C {func}: 正本から名前を作れない（{why}）")
            continue
        where, got = _find(func, required)
        if not where:
            ng.append(f"C {func}: 設計書の must_use_from に在るのに、実装にその関数が無い")
            continue
        missing = [c for c in required if c not in got]
        if missing:
            ng.append(f"C {func}: 正本が要求する名前が中身に無い → {missing}（出どころ＝{why}）")
        else:
            print(f"  [PASS] must_use_from {func}: 全部あり（出どころ＝{why}／{where}）")
    for func, required in (contract.get("must_use") or {}).items():
        where, got = _find(func, required)
        if not where:
            ng.append(f"C {func}: 設計書の must_use に在るのに、実装にその関数が無い")
            continue
        missing = [c for c in required if c not in got]
        if missing:
            ng.append(f"C {func}: 設計書が要求する名前が中身に無い → {missing}（{where}）")
        else:
            print(f"  [PASS] must_use {func}: 全部あり {required}"
                  f"（{where}・★手書き＝機械で照らせないに数える）")
    return ng


def probe_spec_lists(key: str, spec: dict) -> tuple[bool, str]:
    """一覧を1件 減らして、実装の出力が変わるかを測る（監査 cp13 の A-4・Critical）。

    ★監査の逐語＝「実装を import し、spec_lists.json を差し替えて出力が変わるかを測る。
      文字の検査と『全部 直書きのときだけ落とす』判定は捨てる」。
    ★設計書には `probe`（その一覧を使う関数の呼び方＝"モジュール名:関数名"）を書く。
    戻り＝(読んでいるか, 理由の文)
    """
    global SPEC_LISTS_PATH
    import importlib
    import tempfile
    probe = str((spec or {}).get("probe") or "")
    if ":" not in probe:
        return False, "設計書に probe（この一覧を使う関数の呼び方）が無い＝振る舞いで照らせない"
    mod_name, func_name = probe.split(":", 1)
    keep = SPEC_LISTS_PATH
    if not keep.exists():
        return False, f"一覧のファイルが無い（{keep}）＝承認を打ち直すこと"
    base = json.loads(keep.read_text(encoding="utf-8"))
    items = base.get(key)
    if not isinstance(items, list) or len(items) < 2:
        return False, f"一覧 {key} が2件以上でない＝1件 減らして比べられない"

    # ★2026-09-03（監査 cp14 の B-2）＝差し替え先を「この場」と「import された同じ道具」の両方に置く。
    #   なぜ要るか＝この道具を `python3 verify_design_contract.py …` で走らせると、この場の名前は
    #   __main__ になる。実装の側は `from verify_design_contract import load_spec_lists` で
    #   別の複写を読み込むので、__main__ の差し替えが実装に届かなかった（N5b で実測して分かった）。
    #   ＝直さないと、照合D は実際に走る経路では必ず「出力が変わらない」になる。
    def _set(pth):
        global SPEC_LISTS_PATH
        SPEC_LISTS_PATH = pth
        _twin = sys.modules.get("verify_design_contract")
        if _twin is not None:
            _twin.SPEC_LISTS_PATH = pth

    try:                                                   # 先に同じ道具を読み込んでおく（下の _set が届く）
        importlib.import_module("verify_design_contract")
    except Exception:                                      # noqa: BLE001
        pass

    outs = []
    try:
        for keep_all in (True, False):
            d = dict(base)
            d[key] = items if keep_all else items[:-1]
            p = pathlib.Path(tempfile.mkdtemp()) / "spec_lists.json"
            p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            _set(p)
            m = importlib.reload(importlib.import_module(mod_name))
            outs.append(repr(getattr(m, func_name)()))
    except Exception as e:                                 # noqa: BLE001
        return False, f"probe を呼べなかった（{mod_name}:{func_name}）→ {e}"
    finally:
        _set(keep)
    if outs[0] == outs[1]:
        return False, "一覧を1件 減らしても出力が変わらない＝一覧を使っていない（コードに焼いた疑い）"
    return True, "一覧を1件 減らすと出力が変わる＝一覧を使っている"


def check_spec_lists(contract: dict, src: str) -> list:
    """照合D＝spec_lists の一覧を、実装が本当に使っているかを振る舞いで測る。

    ★2026-09-02（監査 cp13 の A-4）に作り直した。
      直す前＝①文字 `load_spec_lists` が在るか ②一覧を全部 直書きしたときだけ落とす。
      ＝コメントに書くだけで通り、4つのうち2つだけ直書きした型（2026-09-02 の食い違い）は
        素通りした。**この2つの判定は捨てた。**
    """
    ng = []
    spec = contract.get("spec_lists") or {}
    if not spec:
        return ng
    for key, val in spec.items():
        ok, why = probe_spec_lists(key, val if isinstance(val, dict) else {})
        if ok:
            print(f"  [PASS] spec_lists {key}: {why}")
        else:
            ng.append(f"D {key}: {why}")
    return ng


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
        # ★2026-09-03（監査 cp14 の E-3 の残り）＝impl_functions に書いた全部の .py を見る。
        #   直す前＝impl_file の1本だけを見ていたので、別のファイルに作った関数を
        #   「配線が無い」と誤って言った（実測＝approval_matches・choose_variant）。
        _srcs = [src]
        for _rel in (contract.get("impl_functions") or {}):
            if not str(_rel).endswith(".py"):
                continue
            try:
                _srcs.append(open(_resolve_impl(md_path, _rel), encoding="utf-8").read())
            except Exception:                              # noqa: BLE001
                continue
        for c in calls:
            if any(c in s for s in _srcs):
                print(f"  [PASS] 自己チェック配線あり: {c}")
            else:
                print(f"  [FAIL] 自己チェック配線が無い（外された疑い）: {c}")
                ok = False
    # ★2026-09-02（まこさん承認 iter="impl-lock-20260902"）＝ここは else だった。
    #   ＝self_check_calls（名前が在るかだけ）を書くと、must_combine（中身を見る）が一度も走らなかった。
    #   今日の食い違い（4通り→2通り）は、名前を4つ書いたので中身の検査が動かず、素通りした。
    #   直した後＝書いてあるものを全部 走らせる。
    if contract.get("must_combine"):
        # 実装の代入式に設計要求成分が連結されているか（literal assignment）
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
    # ★設計書どおりにしか実装できなくする照合A〜D（2026-09-02・iter="impl-lock-20260902"）。
    #   書いてある欄だけ走る＝既存の設計書（3つの欄が無いもの）は今までどおり通る。
    for msg in (check_impl_functions(contract, md_path)
                + check_must_use(contract, src, md_path)
                + check_spec_lists(contract, src)):
        print(f"  [FAIL] {msg}")
        ok = False
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
    # ★2026-09-02（監査 cp13 の A-7・E-7）＝本番の承認の記録を1バイトも触らない。
    #   直す前＝本番の design_approved.json を書き替え、戻す処理が try の中に在った
    #   （途中で例外が出れば偽の記録が残る）。監査の1回の実行で、実際にこのファイルが書き替わった。
    #   直した後＝読む先をモジュールの変数ごと一時の場所へ向け、finally で必ず戻す（手本＝T16）。
    global _DESIGN_APPROVED
    t10_dir = tempfile.mkdtemp()
    _keep_da = _DESIGN_APPROVED
    try:
        p10 = os.path.join(t10_dir, "approved.md")
        open(p10, "w", encoding="utf-8").write("設計書の中身\n")
        _DESIGN_APPROVED = os.path.join(t10_dir, "design_approved.json")
        table = {os.path.abspath(p10): hashlib.sha256(open(p10, "rb").read()).hexdigest()}
        json.dump(table, open(_DESIGN_APPROVED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        ok_before, _m1 = check_approval(p10)
        open(p10, "a", encoding="utf-8").write("1文字\n")
        ok_after, _m2 = check_approval(p10)
        results["T10"] = (ok_before and not ok_after)
    finally:
        _DESIGN_APPROVED = _keep_da
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

    # ── ★2026-09-02（監査 cp13 の A-7）＝照合A〜D を、わざと壊して試す（N1〜N7）──
    #   一時の場所に小さな git のリポジトリを作って試す＝本物のファイルは1バイトも変えない。
    global SPEC_LISTS_PATH
    global FROZEN_PATH          # ★2026-09-03（監査 cp14 の B-1）＝N9 で一時に付け替えて必ず戻す
    nd = tempfile.mkdtemp()
    try:
        for _a in (["git", "init", "-q", nd],
                   ["git", "-C", nd, "config", "user.email", "t@example.com"],
                   ["git", "-C", nd, "config", "user.name", "t"]):
            subprocess.run(_a, check=False, capture_output=True)
        fn = os.path.join(nd, "impl.py")
        md_n = os.path.join(nd, "design.md")
        open(md_n, "w", encoding="utf-8").write("見本の設計書\n")
        open(fn, "w", encoding="utf-8").write(
            "import json\n\n\ndef alpha():\n    return 1\n\n\ndef beta():\n    return 2\n")
        subprocess.run(["git", "-C", nd, "add", "impl.py"], check=False, capture_output=True)
        subprocess.run(["git", "-C", nd, "commit", "-qm", "first"], check=False, capture_output=True)

        # N7 差分がゼロ（commit 済み）でも照合B は走る
        # ★2026-09-03（B-1）＝番人は凍結された版を明示で渡す（本番は凍結ファイルを読む）
        ng7 = check_impl_functions({"impl_functions": {fn: ["alpha", "beta", "zeta"]}}, md_n,
                                   frozen={fn: ["alpha", "beta", "zeta"]})
        results["N7"] = (touched_functions(fn) == set() and any("zeta" in x for x in ng7))

        # 変更＝alpha を書き換え、gamma を足す。beta は1文字も触らない
        open(fn, "w", encoding="utf-8").write(
            "import json\n\n\ndef alpha():\n    return 10\n\n\ndef beta():\n    return 2\n"
            "\n\ndef gamma():\n    return 3\n")
        got_n = touched_functions(fn)
        results["N2"] = ("gamma" in got_n and "alpha" in got_n)   # 新しく足した関数を拾う
        results["N1"] = ("beta" not in got_n)                     # 触っていない関数を誤検出しない

        # N3 照合B＝設計書に書いた関数が実装に無ければ落ちる
        ng3 = check_impl_functions({"impl_functions": {fn: ["alpha", "gamma", "delta"]}}, md_n,
                                   frozen={fn: ["alpha", "gamma", "delta"]})
        results["N3"] = any("delta" in x for x in ng3)

        # N6 道具の承認の印が無ければ落ちる（印は一時に隠して、必ず戻す）
        _mark = pathlib.Path(_REPO) / ".claude" / "state" / "verify_tool.approved"
        _bak = _mark.with_name(_mark.name + ".selftest_bak")
        _moved = _mark.exists()
        if _moved:
            _mark.rename(_bak)
        try:
            ng6 = check_impl_functions({"impl_functions": {}}, md_n, frozen={})
            results["N6"] = any("印がありません" in x for x in ng6)
        finally:
            if _moved:
                _bak.rename(_mark)

        # N4 照合C＝正本から作った名前が中身に無ければ落ちる（自明な名前では通らない）
        _law = os.path.join(nd, "law.json")
        json.dump({"枠": {"FAMILY": 1, "LINEAGE": 2}}, open(_law, "w", encoding="utf-8"),
                  ensure_ascii=False)
        ng4 = check_must_use({"must_use_from": {"alpha": {"from": _law, "kind": "枠"}}},
                             open(fn, encoding="utf-8").read())
        results["N4"] = any("FAMILY" in x for x in ng4)

        # N5 照合D＝一覧の一部だけを直書きすると落ちる（2026-09-02 の食い違いと同じ型）
        _sl = pathlib.Path(nd) / "spec_lists.json"
        _sl.write_text(json.dumps({"kinds": ["a", "b", "c", "d"]}, ensure_ascii=False),
                       encoding="utf-8")
        open(os.path.join(nd, "half_impl.py"), "w", encoding="utf-8").write(
            "def build():\n    return ['a', 'b']\n")
        _keep_sl = SPEC_LISTS_PATH
        sys.path.insert(0, nd)
        try:
            SPEC_LISTS_PATH = _sl
            ng5 = check_spec_lists({"spec_lists": {"kinds": {"probe": "half_impl:build"}}}, "")
            results["N5"] = any("出力が変わらない" in x for x in ng5)
        finally:
            SPEC_LISTS_PATH = _keep_sl
            if nd in sys.path:
                sys.path.remove(nd)

        # ★2026-09-03（監査 cp14）＝ここから N8〜N12・N5b
        # N8 設計書の impl_functions が凍結された版と違えば落ちる（B-1）
        ng8 = check_impl_functions({"impl_functions": {fn: ["alpha", "gamma"]}}, md_n,
                                   frozen={fn: ["alpha"]})
        results["N8"] = any("承認のときから変わっています" in x for x in ng8)

        # N9 凍結された版が無ければ落ちる（B-1・fail-closed）
        #   ★いま作業している設計書のときだけ凍結と比べる形にしたので（控えを壊さないため）、
        #     ここでは凍結を読む関数そのものを試す。
        _keep_fz = FROZEN_PATH
        try:
            FROZEN_PATH = pathlib.Path(nd) / "no_such_frozen.json"
            try:
                frozen_impl_functions()
                results["N9"] = False
            except FileNotFoundError as _e9:
                results["N9"] = "凍結された impl_functions がありません" in str(_e9)
        finally:
            FROZEN_PATH = _keep_fz

        # N10・N11・N12 正本の掘り下げ（B-3）と、承認の展開（B-2）
        _deep = os.path.join(nd, "deep.json")
        json.dump({"機械が読む判定": {"次元": {"family": 1, "系統": 2}}},
                  open(_deep, "w", encoding="utf-8"), ensure_ascii=False)
        got10, why10 = must_use_from_source({"from": _deep, "kind": "機械が読む判定/次元"})
        results["N10"] = (got10 == ["family", "系統"])
        got11, why11 = must_use_from_source({"from": _deep, "kind": "在りません"})
        results["N11"] = (got11 == [] and "kind の段がない" in why11)
        got12, _why12 = resolve_spec_list({"from": _deep, "kind": "機械が読む判定/次元"})
        results["N12"] = (got12 == ["family", "系統"])

        # N5b 照合D＝承認が書き出す形（展開済みの配列）で成立する（B-2）
        _sl2 = pathlib.Path(nd) / "spec_lists2.json"
        _sl2.write_text(json.dumps({"kinds": got12}, ensure_ascii=False), encoding="utf-8")
        open(os.path.join(nd, "full_impl.py"), "w", encoding="utf-8").write(
            "import json, pathlib\n"
            "from verify_design_contract import load_spec_lists\n\n\n"
            "def build():\n    return list(load_spec_lists().get('kinds') or [])\n")
        _keep_sl2 = SPEC_LISTS_PATH
        sys.path.insert(0, nd)
        try:
            SPEC_LISTS_PATH = _sl2
            ok5b, why5b = probe_spec_lists("kinds", {"probe": "full_impl:build"})
            results["N5b"] = bool(ok5b)
        finally:
            SPEC_LISTS_PATH = _keep_sl2
            if nd in sys.path:
                sys.path.remove(nd)

        # ★2026-09-05（監査 cp20 の C1〜C3・まこさん承認 iter="freeze-fail-closed-cp20-20260905"）
        # N13 凍結が空（理由なし）なら、比較の前に落ちる（C3）
        _empty_msg = "凍結された impl_functions が空です"
        ng13 = check_impl_functions({"impl_functions": {}}, md_n, frozen={})
        results["N13"] = any(_empty_msg in x for x in ng13)
        # N14 理由の在る空（cp19 の形）は、その文では落ちない
        ng14 = check_impl_functions({"impl_functions": {},
                                     "no_impl_functions_reason": "設計の段階では書けない"},
                                    md_n, frozen={})
        results["N14"] = not any(_empty_msg in x for x in ng14)
        # N15 契約の後ろに impl_file だけの囲み（SPEC の形）が在っても、契約の側を取る（C2）
        _dc = json.dumps({"impl_file": "a.py", "impl_functions": {"a.py": ["f", "g", "h"]}})
        _sp = json.dumps({"impl_file": "a.py", "public_functions": {}})
        _f3 = chr(96) * 3
        t15 = ("## 契約\n\nDESIGN_CONTRACT\n\n" + _f3 + "json\n" + _dc + "\n" + _f3 + "\n\n"
               "## 仕様\n\nSPEC\n\n" + _f3 + "json\n" + _sp + "\n" + _f3 + "\n")
        o15, w15 = contract_for_freeze(t15)
        results["N15"] = (w15 is None and o15 is not None
                          and len(o15["impl_functions"]["a.py"]) == 3)
        # N16 impl_file だけの囲みが先に在っても、契約の側を取る（並び順に影響されない）
        t16 = ("## 仕様\n\nSPEC\n\n" + _f3 + "json\n" + _sp + "\n" + _f3 + "\n\n"
               "## 契約\n\nDESIGN_CONTRACT\n\n" + _f3 + "json\n" + _dc + "\n" + _f3 + "\n")
        o16, w16 = contract_for_freeze(t16)
        results["N16"] = (w16 is None and o16 is not None
                          and len(o16["impl_functions"]["a.py"]) == 3)
        # N17 空で理由なしの契約は止まる側（C1）
        t17 = ("DESIGN_CONTRACT\n\n" + _f3 + "json\n"
               + json.dumps({"impl_file": "a.py", "impl_functions": {}}) + "\n" + _f3 + "\n")
        o17, w17 = contract_for_freeze(t17)
        results["N17"] = (o17 is None and w17 is not None and "no_impl_functions_reason" in w17)
    finally:
        shutil.rmtree(nd, ignore_errors=True)

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

    if "--freeze-contract" in sys.argv:
        # ★2026-09-05（監査 cp20 の C1・まこさん承認 iter="freeze-fail-closed-cp20-20260905"）
        #   ＝承認の瞬間に凍結する契約を、同じ規則（contract_for_freeze）で取って出す口。
        #   壊すプログラム（b23）がここで測る（承認スクリプトは CC の Bash から打てないため）。
        #   通れば契約の json を出して 0、通らなければ理由を stderr に出して 3。
        _md = sys.argv[sys.argv.index("--freeze-contract") + 1]
        _obj, _why = contract_for_freeze(open(_md, encoding="utf-8", errors="ignore").read())
        if _obj is None:
            print(f"❌ 凍結できません（監査 cp20 の C1）: {_why}", file=sys.stderr)
            sys.exit(3)
        print(json.dumps(_obj, ensure_ascii=False, indent=1))
        sys.exit(0)

    if "--write" in sys.argv:
        _md = sys.argv[sys.argv.index("--write") + 1]
        write_actual(_md)
        sys.exit(0)

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(0 if check(sys.argv[1]) else 1)
