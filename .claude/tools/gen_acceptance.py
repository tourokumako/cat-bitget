#!/usr/bin/env python3
"""gen_acceptance.py — engine_tuner の設計書を、元データと正本から組み立てる。

なぜ作ったか
------------
まこさん指示（2026-09-09・逐語）＝「ヌケモレがおおいから、手で書かざるを得ない部分以外は
自動生成にしろよ。。。。なんで最低限守って。虚偽、ヌケモレ、不正予防のために自動生成にしろって
言ってだけど。なんでできない」「この自動生成の件、毎回言ってるんだけど。いい加減覚えろよ」
「手書きはするな」。

何が起きていたか（実測 2026-09-09）
  M2-E-2 の設計書 577行のうち、プログラムが作ったのは SPEC の囲みだけだった。
  残りは手書き。その結果、
    ①関数の行番号を手で写した（verify_design_contract.py --write が毎回
      「行番号を手で写さない・93番」と画面に出しているのに）
    ②法則の一覧を手で並べ、21件のうち2件（R11・C8）を落とした
    ③まこさんが決めた探す候補（§2.2）を12件 切り、「入りません」と書いた
  どれも、正本から作れば起きない。

何をするか
----------
  --work <工事名> --write    工事のフォルダ（やることの表.md と逐語のファイル）と正本から設計書を組み立て、囲みの中に書く
  --verify [--work <工事名>] 囲みの中が、機械の書いたままかを検出する（工事名を省くと設計書の ARC の iter を使う）
  --work <工事名> --dry-run  書かずに、組み立てた本文を画面に出す
  --selftest                 一時の置き場に作る固定の見本だけで、わざと壊して ❌ が出るかを試す
  ★2026-09-30（設計書 point1-one-way-20260930・まこさん承認）＝設計書の作り方は工事のフォルダの1本だけ。
    元データの JSON（acceptance_src.json）から組む古い口は消した（古い元データは acceptance_archive へ移した）。

★手で書くのは、工事のフォルダの やることの表.md の「手書きの項目」の5つだけ（HAND_KEYS）。
★行番号・一覧・件数・格子と範囲・SPEC は、この道具が正本から出す（やることの表にも案にも書かない）。
★2026-09-29（まこさん指示「やることリストなどの設計のもとになるものから設計書作成を自動生成」）
  ＝設計のもと（元データの「設計のもと」＝やることの番号と逐語のファイル）を、この道具が設計書 §0-1 に写す。
    やることの行は m2_todo.json から、まこさんの文は gen_verbatim.py の逐語のファイルから読む（CC は写さない）。
  ＝写した1行ずつに「設計書のどの節・実装の指示の何番で満たすか」（元データの「対応の表」）が無ければ書かない。
  ＝元データに「まこさんの決定」の欄が在れば止める（CC が手で書く口は閉じた・OK をもらった提案の7行目）。
★節の形＝まこさん決定 2026-09-09（恒久の決まり70番）＝7つの節。

fail-closed（黙って通さない・4つ）
  1. 正本のファイルが読めない → 止まる
  2. 元データの「やらないこと」が空 → 止まる（私が候補を切って何も書かない、を防ぐ）
  3. 置き換えられない目印が本文に残った → 止まる
  4. 法則ファイルの件数と、書き出した件数が違う → 止まる（法則を落として並べる、を防ぐ）

限界（正直に）
  ・元データの文の中で範囲を狭めることは、この道具では止められない（まこさんの目と監査）。
  ・囲みの外（節の見出しなど）を手で書き換えても、--verify は止めない。
  ・この道具自身を書き換えれば無効にできる（git の差分には出る）。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
RATCHET = SDK / ".claude" / "ratchet"
STATE = ROOT / ".claude" / "state"
PRIORITY = SDK / "scripts" / "priority_rebuild"
TODO = RATCHET / "m2_todo.json"                     # ★2026-09-29＝設計のもと（やることリスト）

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_verbatim as gv                           # noqa: E402  ★2026-09-29＝まこさんの文の逐語のファイル
import gen_core_requirements as gcr                 # noqa: E402  ★2026-10-12＝固定で載せる文（要件定義と工事の流れ）の正本

# ★2026-10-12（170回目・まこさん「OK」＝直し方の案 A-1・A-4）＝固定で載せる文と、要件定義との照らしの表を、設計書の上部に載せる。
CORE_MARK = "**■ 要件定義と工事の流れ（固定・毎回 読む・消さない）**"   # 載っているかを見る文字（正本の先頭の見出しを太字にした行）
CORE_FROM = "20261012"                                                # この日付からの工事は、案に【0-R】（要件定義との照らし）が必ず要る


def core_required(work: str) -> bool:
    """工事名の末尾の日付（8桁）が CORE_FROM 以降か。日付の無い名前（自己テストの見本）と、それより前の工事は False。
    ＝2026-10-12 より前に承認した設計書（例＝k4-reference-known-20261011）は、作り直しても中身が変わらない。"""
    m = re.search(r"(\d{8})$", work or "")
    return bool(m) and m.group(1) >= CORE_FROM


def touches_trading(d: dict) -> bool:
    """この工事が売買のロジック（scripts/priority_rebuild・engine_tuner）に触るか。TARGET と NEW_FILE で見る。

    ★2026-09-29（まこさん指摘「監査の依頼内容が変じゃないか？」・worklog 20260929 §40〜§42）
      ＝直す前は、道具の直しの設計書でも 2-2 探す材料・2-3 成績表・2-4 乱数・7-3b（engine_tuner の要件）を必ず出し、
        依頼書にも engine_tuner の前提と大目的を出していた。工事の相手を見て出し分ける。
    """
    ps = [str(p) for p in (d.get("TARGET") or []) + (d.get("NEW_FILE") or [])]
    if d.get("形") == "新":                          # ★新しい形の設計書＝先頭に出す工事の種類と、同じ決め方にする（設計書の監査 CP77）
        return work_kind(d) == 1
    return any("scripts/priority_rebuild" in p or "engine_tuner" in p for p in ps)


NONTRADE = ("**非該当。**この工事の直す相手（TARGET・NEW_FILE）に、売買のロジック（scripts/priority_rebuild・engine_tuner）が無い"
            "（プログラムが TARGET と NEW_FILE から決めました）。")


def forbidden_items():
    """要件の正本から「作ってはいけないもの」の一覧を取り出す（★手で写さない＝恒久の決まり69番）。

    戻り＝[(番号, 名前), ...]。出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。
    ★なぜ要るか（2026-09-10・96回目）＝恒久の決まり §1 が「着手の前に、作ろうとしているものが
      その一覧に当たらないかを1件ずつ照合して、結果をチャットに出します」と求めている。
      それまでの設計書には、この照合を書く場所が1つも無かった。
    ★一覧が増えたら、この表も自動で増える（照合を書かないと --write が止まる＝fail-closed）。
    """
    p = RATCHET / "engine_tuner_requirements.json"
    body = json.loads(p.read_text(encoding="utf-8"))
    tbl = []

    def walk(x):
        if isinstance(x, str):
            if "| # | 作ってはいけないもの |" in x:
                tbl.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(body)
    if not tbl:
        raise SystemExit("[gen_acceptance] 要件の正本に「作ってはいけないもの」の表が無い（fail-closed）")
    out = []
    for ln in tbl[0].split("\n"):
        m = re.match(r"^\|\s*(\d+)\s*\|\s*\*\*(.+?)\*\*\s*\|", ln.strip())
        if m:
            out.append((m.group(1), m.group(2)))
    if not out:
        raise SystemExit("[gen_acceptance] 「作ってはいけないもの」を1件も取り出せなかった（fail-closed）")
    return out

# ★2026-09-30（設計書 point1-one-way-20260930）＝元データの JSON の置き場（SRC）は消した。読むのは工事のフォルダだけ。
# ★2026-09-10＝§4（設計の中身）の項目の正本。
#   3つの出どころ（うちの正本・外の標準・まこさんが過去に指摘したこと）118件を
#   全部 引き受ける形に割り当てたもの（gen_design_sections.py --check で検算する）。
#   ★項目をここ以外に書かない（2か所に書くと片方だけ直って食い違う）。
MAP = RATCHET / "design_section_map.json"
DEST = STATE / "acceptance.md"
# ★2026-10-20（まこさん「塞ぐ」・ToDo の24番）＝承認の控えの置き場。--out はここへ書けない（控え＝承認した設計書の証拠）
ARCHIVE = RATCHET / "acceptance_archive"
# ★2026-10-20（ToDo の26番・監査 CP78 の Major の残りと Minor G）＝監査の結果ファイルの置き場。自己テストは一時の置き場に替えて、見本の結果ファイルで 6-4 の行を測る
AUDITS = SDK / ".claude" / "audits"

# ── 正本（この道具が読む相手・手で写さない）─────────────────────────
SWITCH = RATCHET / "indicator_switch.json"
LAWS = RATCHET / "regime_laws.json"
FAMILIES = RATCHET / "signal_families.json"
RANKING = RATCHET / "material_ranking.json"
LIMITS = PRIORITY / "recipes" / "search_limits.json"
GEN_PY = PRIORITY / "engine_tuner_gen.py"
EXEC_PY = PRIORITY / "engine_tuner_exec.py"

# ── 囲み（9つ）───────────────────────────────────────────────
BLOCKS = ("STAGES", "MATERIALS", "LAWS", "RANKING", "CODEREF", "RANDOM",
          "ACCEPT_TABLE", "SELFTEST", "SPEC", "CHECKLIST", "AUDITTODO",
          # ★2026-09-24（設計書 impl-instruction-apply-20260924）＝設計書の「4-20 実装の指示」の囲み
          #   （元データの `実装の指示` が空なら出ない＝AUDITTODO と同じ形）
          "IMPL",
          # ★2026-09-29＝設計書 §0-1 の設計のもと（やることの行・逐語の行・対応の表）の囲み（いつも出る）
          "SOURCE")


def _begin(kind: str, h: str) -> str:
    if kind == "ACCEPT_TABLE":                       # ★承認ゲートが読む目印（形を変えない）
        return "<!-- ACCEPT_TABLE_START -->"
    return f"<!-- ACC_{kind}_START hash={h} gen_acceptance.py が自動生成＝手で書き換えない -->"


def _begin_re(kind: str) -> re.Pattern:
    if kind == "ACCEPT_TABLE":
        return re.compile(r"<!-- ACCEPT_TABLE_START -->")
    return re.compile(rf"<!-- ACC_{kind}_START hash=([0-9a-f]{{16}}).*?-->")


def _end(kind: str) -> str:
    if kind == "ACCEPT_TABLE":
        return "<!-- ACCEPT_TABLE_END -->"
    return f"<!-- ACC_{kind}_END -->"


def _h(body: str) -> str:
    """本文のハッシュ値（先頭16文字）。

    ★2026-09-09（設計書 gen-acceptance-tool-20260909 の §4-1 の1）
      ＝数える前に、必ず末尾の改行を落とす。
      直す前＝書くときは本文の後ろに改行が付き、読むときは verify が rstrip("\\n") で
      落としていた。同じ中身でもハッシュ値が食い違い、T1 が落ちていた。
      ★数える場所を1か所（この関数）にまとめるのが直しの本体。
    """
    return hashlib.sha256(body.rstrip("\n").encode("utf-8")).hexdigest()[:16]


def _esc(s) -> str:
    """表のセルに入れるとき、| を壊さないようにする。"""
    return str(s).replace("|", "／").replace("\n", " ")


# ★2026-09-29（まこさんの案「文章にはすべて、手書きか、自動生成かを明記する」・worklog 20260929 §75・§82）
#   ＝見出しの直下に1行、誰が書いたかの印を道具が付ける。見出しの文字は変えない（見出しを読む hook が14本 在る）。
_STAMP_RE = re.compile(r"\*\*★この(?:節|表)はプログラムが作ります（手で書き換えない）。\*\*")


def _tag(who: str, what: str) -> str:
    """誰が書いたかの印＝［手書き］［自動］［手書き＋自動］と、その中身の出どころ。"""
    if _NEW_FORM:                                    # ★新しい形の設計書＝案は CC が書いた物（別セッションの監査 2026-10-12 の M-2）
        what = what.replace("まこさんが OK した案", "CC が書いて、まこさんが OK した案")
    return f"［{who}］{what}"


def _wtag(who: str, what: str) -> str:
    """やることの表の「手書きと自動の割り当て」どおりの印と出どころを出す。
    ★2026-09-30（設計書 point1-one-way-20260930-2）＝古いやり方（元データの JSON）の印の分かれ道を消し、引数を2つに揃えた。"""
    return _tag(who, what)


def _load(path: Path) -> dict:
    """正本を読む。読めなければ止まる（fail-closed の1つ目）。"""
    if not path.exists():
        raise SystemExit(f"[gen_acceptance] 正本が無い: {path}（fail-closed）")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"[gen_acceptance] 正本が読めない: {path}（{e}）")


# ══ 設計の元（工事のフォルダ）から組み立てる（2026-09-29・工事 point1-design-autogen-20260929）══════════
#   まこさん要件（逐語）「設計の元となる文書から、CC が文を書かずに、テンプレ項目に沿って設計書を作れるようにする」
#   「手書きにせざるを得ない項目以外はすべて自動詞生成化すること」。割り当て＝やることの表.md の「手書きと自動の割り当て」。
#   ★--work <工事名> のときは、元データの JSON（CC が全部の欄を手で書く）を読まない。読むのは工事のフォルダだけ＝
#     ①やることの表.md（CC の手書き・まこさんが OK）の節「手書きの項目」＝手書きの5項目
#     ②逐語のファイル（gen_verbatim.py が記録から写した）のうち、まこさんが OK した CC の案＝【項目の番号】の見出しで切った中身
#     ＝自動の項目。★対応の表も、どの【】の下の行かで道具が作る（CC は書かない）。
#   ★足りない欄は全部 集めて一度に出して止まる（fail-closed・1件ずつ止めない）。
WORK = ""                                             # --work で入る工事名（空なら設計書は組めない＝src が止まる）
TODO_MD = "やることの表.md"
HAND_KEYS = ("§1 概要", "2-1 何を測るか", "3-1 やらないこと", "3-2 決めてほしいこと", "4-19 通しの例")
# ★2026-10-13（工事 design-doc-gen-form-20261013）＝新しい形の やることの表（共通の ひな型 design_origin_todo_template.md）の手書きの項目。
#   見分け方＝手書きの項目に「### 目標」が在れば、新しい形。無ければ、いままでの形（上の5つ）のまま読む。
HAND_KEYS_NEW = ("§1 概要", "この工事が結ぶ要件と、減らす違い", "2-1 何を測るか", "目標", "3-2 決めてほしいこと", "4-19 通しの例")
NEW_FORM_MARK = "目標"
AUTO_TEXT = {"7-2": "固定値ゼロ宣言", "7-3": "変更の単位"}
AUTO_TABLE = {"5": ("決めたことと理由", ("決めたこと", "理由", "捨てた案")),
              "6-2": ("リスク", ("中身", "どうするか")),
              "6-3": ("見積もり", ("何", "見込み", "根拠")),
              "7-4": ("塞げないもの", ("問い", "塞げないこと")),
              "7-6": ("完成の条件", ("条件", "コマンド", "経路", "壊し方", "壊すプログラム", "監査確認", "いまの状態"))}
DIG_KEYS = ("真因", "期待値分解", "root か symptom か", "ベースアップ")
KEY_RE = re.compile(r"^\s*【([^】]+)】")


def _md_table(lines: list, want: tuple, where: str, bad: list) -> list:
    """Markdown の表を行の一覧（欄の名前 → 中身）にする。見出しの欄が want と違えば bad に足す。"""
    rows = [ln.strip() for ln in lines if ln.strip().startswith("|")]
    if not rows:
        bad.append(f"{where}＝表が無い（見出しの欄＝{'｜'.join(want)}）")
        return []
    head = [c.strip() for c in rows[0].strip("|").split("|")]
    if tuple(head) != tuple(want):
        bad.append(f"{where}＝表の見出しの欄が違う（いま {'｜'.join(head)} ／ 要る {'｜'.join(want)}）")
        return []
    out = []
    for r in rows[1:]:
        cells = [c.strip() for c in r.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        if len(cells) != len(want):
            bad.append(f"{where}＝欄の数が違う行: {r[:60]}")
            continue
        out.append(dict(zip(want, cells)))
    return out


def _sections(lines: list, head_re: re.Pattern) -> dict:
    """見出しの行（head_re が当たる行）で切り、見出しの名前 → 中身の行の一覧にする。"""
    out: dict = {}
    cur = None
    for ln in lines:
        m = head_re.match(ln)
        if m:
            cur = m.group(1).strip()
            out[cur] = []
            continue
        if cur is not None:
            out[cur].append(ln)
    return out


def _text(lines: list) -> str:
    return "\n".join(ln for ln in lines if ln.strip()).strip()


def _json_block(lines: list, where: str, bad: list):
    """中身の ```json 〜 ``` を読む。無い・読めなければ bad に足す。"""
    s = "\n".join(lines)
    m = re.search(r"```json\s*\n(.*?)\n```", s, re.S)
    if not m:
        bad.append(f"{where}＝```json の囲みが無い")
        return None
    try:
        return json.loads(m.group(1))
    except Exception as e:                                  # noqa: BLE001
        bad.append(f"{where}＝json が読めない（{e}）")
        return None


def src_from_work(work: str) -> dict:
    """工事のフォルダ（やることの表.md と逐語のファイル）から、設計書を組む中身（page が読む形）を作る。"""
    d_dir = gv.work_dir(work)
    bad: list = []
    tpath = d_dir / TODO_MD
    if not tpath.exists():
        raise SystemExit(f"[gen_acceptance] {TODO_MD} が工事のフォルダに無い: {tpath}（fail-closed）")
    tlines = tpath.read_text(encoding="utf-8").splitlines()
    title = tlines[0].lstrip("# ").strip() if tlines else work
    m = re.search(r"（(.+)）\s*$", title)
    d: dict = {"iter": work, "設計書の題": m.group(1) if m else title, "audit_report": "",
               "設計の中身": {}}
    # ①手書きの5項目＝やることの表の「## 手書きの項目」の下の「### <名前>」
    top = _sections(tlines, re.compile(r"^##\s+(?!#)(.+)$"))
    hand = _sections(top.get("手書きの項目") or [], re.compile(r"^###\s+(.+)$"))
    new_form = NEW_FORM_MARK in hand                 # ★2026-10-13＝手書きの項目に「### 目標」が在れば、新しい形
    d["形"] = "新" if new_form else "旧"
    # ★2026-10-18（ToDo の15番・監査 CP77 の Minor）＝見出しの下の表示を替える変数は、元を読むここで立てる。
    #   直す前は src() だけが立て、元を直に読むプログラム（監査依頼書を作るプログラム）で表示が食い違う道が残った。
    global _NEW_FORM
    _NEW_FORM = new_form
    hand_keys = HAND_KEYS_NEW if new_form else HAND_KEYS
    for k in hand_keys:
        if k not in hand:
            bad.append(f"{TODO_MD} の「## 手書きの項目」に「### {k}」が無い")
    # ★同＝知らない見出しは止める（直す前は、決まった名前が在るかだけを見て、ほかの見出しを設計書に出さずに通した＝設計書の監査 CP75 の Q9）
    for k in hand:
        if k not in hand_keys:
            bad.append(f"{TODO_MD} の「## 手書きの項目」に、知らない見出し「### {k}」が在る（写す先の項目が無い）")
    d["何を作るか"] = _text(hand.get("§1 概要") or [])
    d["なぜ作るか"] = _md_table(hand.get("2-1 何を測るか") or [], ("何を測ったか", "コマンド", "読み方"), "2-1", bad) if "2-1 何を測るか" in hand else []
    d["やらないこと"] = _md_table(hand.get("3-1 やらないこと") or [], ("中身", "理由", "出どころ"), "3-1", bad) if "3-1 やらないこと" in hand else []
    # ★ひな型の「★向きを見る所。」の行は、中身に数えない（その下に「無し」と書いても止まらないようにする＝設計書の監査 CP77）
    _kk = [ln for ln in (hand.get("3-2 決めてほしいこと") or []) if not ln.strip().startswith("★向きを見る所")]
    d["決めてほしいこと"] = [] if _text(_kk) in ("", "無し") else _md_table(_kk, ("中身", "私の案", "出どころ"), "3-2", bad)
    d["設計の中身"]["4-19"] = [ln for ln in (hand.get("4-19 通しの例") or []) if ln.strip()]
    if new_form:
        _read_new_todo(d, top, hand, bad, work, d_dir)
    # ②自動の項目＝まこさんが OK した CC の案（逐語のファイル・話し手が CC だけ）の【番号】で切った中身
    names = sorted(p.name[: -len(".meta.json")] for p in d_dir.glob("*.meta.json"))
    d["設計のもと"] = {"逐語のファイル": [f"{work}/{n}" for n in names], "やることの番号": []}
    # ★案を直すときは、直す番号の【】だけを書いた次の案を出して OK をもらう。同じ番号は、後の（時刻が新しい）案が前の案を置き換える。
    metas = {}
    for n in names:
        ok, why = gv.verify(n, d_dir)
        if not ok:
            raise SystemExit(f"[gen_acceptance] 逐語のファイルが照らしを通らない（{why}・fail-closed）")
        metas[n] = json.loads((d_dir / f"{n}.meta.json").read_text(encoding="utf-8"))
    order = sorted(names, key=lambda n: ((metas[n].get("time") or [""])[0], n))
    parsed = []                                        # (名前, CC の案か, [(行, 見出しの番号 or None)])
    owner: dict = {}                                   # 番号 → その番号を最後に書いた案
    for n in order:
        is_cc = set(metas[n].get("who") or []) == {"CC"}
        cur = None
        rows = []
        for ln in (d_dir / f"{n}.txt").read_text(encoding="utf-8").splitlines():
            km = KEY_RE.match(ln) if is_cc else None
            if km:
                cur = km.group(1).split()[0]
                owner[cur] = n
            rows.append((ln, cur if is_cc else None))
        parsed.append((n, is_cc, rows))
    auto: dict = {}
    match: list = []
    for n, is_cc, rows in parsed:
        vi = 0
        for ln, cur in rows:
            if cur is not None and owner.get(cur) == n and not KEY_RE.match(ln):
                auto.setdefault(cur, []).append(ln)
            elif cur is not None and owner.get(cur) == n:
                auto.setdefault(cur, [])
            if not ln.strip():
                continue
            vi += 1
            rid = f"{n}:V{vi:02d}"
            if cur == "外部検索":
                # ★2026-09-29＝【外部検索】は監査の依頼書に写す（設計書の節ではない）
                match.append({"出どころ": rid, "設計書の節": NO_MATCH,
                              "理由": "OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた）"})
            elif cur is not None and owner.get(cur) == n:
                match.append({"出どころ": rid, "設計書の節": cur, "理由": "OK された案の【" + cur + "】の見出しの下の行（道具が決めた）"})
            elif cur is not None:
                match.append({"出どころ": rid, "設計書の節": cur,
                              "理由": f"後の案（{owner[cur]}）で置き換えた【{cur}】の行＝設計書には写していない（道具が決めた）"})
            else:
                match.append({"出どころ": rid, "設計書の節": NO_MATCH,
                              "理由": "【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた）"})
    d["対応の表"] = match
    if new_form:
        d["案の文"] = {k: list(v) for k, v in auto.items()}   # 新しい形の検査が読む（見出しごとの、案の文の全部）
    for k, body in auto.items():
        if new_form and k in (HEAD_FIVE, HEAD_NUMS, HEAD_UNVERIFIED):
            _read_new_head(d, k, body, bad)
        elif re.fullmatch(r"4-(?:[0-9]|1[0-8])", k):
            first = _text(body)
            d["設計の中身"][k] = ({"非該当": first.split("＝", 1)[-1].strip()} if first.startswith("非該当")
                                  else [ln for ln in body if ln.strip()])
        elif k == "4-20":
            first = _text(body)
            if first.startswith("非該当"):
                d["実装の指示"] = []
                d["設計の中身"]["4-20"] = {"非該当": first.split("＝", 1)[-1].strip()}   # section4 が理由を求める
            else:
                d["実装の指示"] = _json_block(body, "【4-20】", bad) or []
        elif k in AUTO_TEXT:
            d[AUTO_TEXT[k]] = _text(body)
        elif k in AUTO_TABLE:
            key, cols = AUTO_TABLE[k]
            d[key] = _md_table(body, cols, f"【{k}】", bad)
        elif k == "7-1":
            for r in _md_table(body, ("欄", "中身"), "【7-1】", bad):
                if r["欄"] in DIG_KEYS:
                    d[r["欄"]] = r["中身"]
        elif k == "7-3b":
            if new_form:                             # ★新しい形＝CC の判定の欄をやめ、根拠と確かめ直すコマンドを読む
                d["作ってはいけないものとの照合"] = {r["番号"]: {"根拠": r["根拠"], "確かめ直すコマンド": r["確かめ直すコマンド"]}
                                        for r in _md_table(body, ("番号", "根拠", "確かめ直すコマンド"), "【7-3b】", bad)}
            else:
                d["作ってはいけないものとの照合"] = {r["番号"]: {"当たるか": r["当たるか"], "理由": r["理由"]}
                                        for r in _md_table(body, ("番号", "当たるか", "理由"), "【7-3b】", bad)}
        elif k == "0-R":
            # ★2026-10-12（A-4・まこさん「OK」）＝要件定義との照らし。番号は、正本の要件の番号（gen_core_requirements.requirement_items）
            d["要件定義との照らし"] = {r["番号"]: {"関わるか": r["関わるか"], "合っているか": r["合っているか"], "根拠": r["根拠"]}
                                for r in _md_table(body, ("番号", "関わるか", "合っているか", "根拠"), "【0-R】", bad)}
        elif k == "外部検索":
            # ★2026-09-29＝依頼書の道具（gen_audit_docs.py request-design --work）が読む。設計書には写さない
            # ★2026-10-18（ToDo の15番・監査 CP75 の外部検索の Process）＝検索の言葉の列を読む。直す前は「名前」「中身」の2列だけで、
            #   依頼書のクエリ案に CC の文がそのまま出た。新しい形の案では、検索の言葉の列を必ず書く（古い形は、無くても読む）。
            _head = next((ln for ln in body if ln.strip().startswith("|")), "")
            _cols = ("名前", "中身", "検索の言葉") if "検索の言葉" in _head else ("名前", "中身")
            if new_form and len(_cols) == 2:
                bad.append("新しい形の案の【外部検索】に「検索の言葉」の列が無い（列＝名前・中身・検索の言葉。"
                           "検索の言葉は、監査が WebSearch にそのまま入れる言葉）")
            d["外部検索"] = _md_table(body, _cols, "【外部検索】", bad)
        elif k == "7-5":
            d["ハード制約の照合"] = [re.sub(r"^\s*(?:[-*]|\d+\.)\s*", "", ln) for ln in body if ln.strip()]
        elif k == "7-8":
            j = _json_block(body, "【7-8】", bad) or {}
            for kk in ("TARGET", "NEW_FILE", "MODEL", "DESIGN_CONTRACT"):
                if kk in j:
                    d[kk] = j[kk]
        else:
            bad.append(f"OK された案に、知らない見出し【{k}】が在る（写す先の項目が無い）")
    if new_form:
        _finish_new(d, bad)
    # 足りない欄（page が読む所）を全部 集める
    need = ["何を作るか", "真因", "期待値分解", "root か symptom か", "ベースアップ", "固定値ゼロ宣言", "変更の単位",
            "完成の条件", "TARGET", "DESIGN_CONTRACT", "ハード制約の照合"]
    for k in need:
        if not d.get(k):
            bad.append(f"「{k}」が無い（{'やることの表の §1 概要' if k == '何を作るか' else 'OK された案の【】の見出し'}）")
    for k in ("決めたことと理由", "リスク", "見積もり", "塞げないもの", "実装の指示"):
        d.setdefault(k, [])
    if touches_trading(d) and not d.get("作ってはいけないものとの照合"):
        bad.append("売買に触る工事なのに【7-3b】が無い")
    # ★2026-10-12（A-4・まこさん「OK」）＝工事名の日付が 2026-10-12 以降の工事は、要件定義との照らし（【0-R】）を必ず書く
    if core_required(work) and not new_form and not d.get("要件定義との照らし"):
        bad.append("OK された案に【0-R】（要件定義との照らし）が無い。表の列＝番号・関わるか・合っているか・根拠。"
                   "番号は `python3 .claude/tools/gen_core_requirements.py --items` が出す要件の番号（まこさん指示 2026-10-12）")
    if bad:
        raise SystemExit(f"[gen_acceptance] 工事のフォルダ {work} から設計書を組めません（fail-closed・全部で {len(bad)} 件）:\n  "
                         + "\n  ".join(bad))
    return d


# ══ 新しい形の設計書の元（共通の ひな型）を読む・出す（2026-10-13・工事 design-doc-gen-form-20261013）══════════
#   まこさん指示（2026-10-13）「設計書の元を完全に修正完了してから、設計書の修正をすべきだよね。」
#   ★いままでの形（手書きの項目に「### 目標」が無い やることの表）は、新しい形を読む関数と、新しい形の節を出す関数を通らない（手書きの項目の名前を返す関数と、検算を呼ぶ関数の2つは、どの形でも通る）＝承認済みの設計書は、作り直しても変わらない。
_NEW_FORM = False                                   # いま組んでいる設計書が新しい形か（src が決める。見出しの下の表示 _tag が読む）
GOAL_NOS = ("①", "②", "③", "④", "⑤", "⑥")
EMPTY_WORDS = ("", "—", "-", "無し", "なし", "特に無し", "特になし", "ありません")
PLAN = STATE / "design_read_plan.md"                # 読むもの宣言（require_read_plan_before_design.py --write が作る）
PLAN_COPY = "読むもの宣言の写し.md"                   # 工事のフォルダに置く写し（宣言が次の工事の物に替わった後も、作り直せるように）
PLAN_NUM_KEY = "★**やることの番号**："
PLAN_REQ_KEY = "★**結ぶ要件の項目**："
HEAD_FIVE = "検査やプログラムを直す工事で書く5つ"       # 案の新しい見出し（項目の正本の 4-22）
HEAD_NUMS = "新しく入る数字と式の一覧"                 # 同（項目の正本の 4-21）
HEAD_UNVERIFIED = "確かめていないこと"                 # 同（設計書の 6-5）
# 工事の種類を決める語。直すファイルの一覧（TARGET・NEW_FILE）のパスに1つでも在れば、種類①
KIND1_WORDS = ("scripts/priority_rebuild", "engine_tuner", "regime_laws", "indicator_switch", "signal_families",
               "material_ranking", "search_limits", "observe_config", "indicator_params", "indicator_roles",
               "composition_rules", "materials.json", "exit_families", "regime_detection_kb")
KIND_TEXT = {1: "種類①（指標・探索・売買のロジック・設定に触る工事）", 2: "種類②（検査やプログラムを直す工事）"}
PARAMS = STATE / "indicator_params_by_strategy.json"   # 置き場＝パラメータの代表の値と範囲（資料の表）
ROLES = STATE / "indicator_roles_thresholds.json"      # 置き場＝役割と閾値（資料の表）
# 閾値の代表の値を読む欄（まこさん OK 2026-10-13）。役割と閾値の置き場の1件に、この鍵で、パラメータと同じ形
# （最初の値（スキャル）・最初の値（デイトレ）・範囲・出どころ）を持つ。無ければ「未決」と出す。
THRESHOLD_KEY = "閾値の値"
# ★設計書の監査 CP77 の修正（2026-10-13）＝使える時間足の全部の置き場（案を作るプログラムの _allowed_tfs が読む物と同じ）
OBS_CFG = PRIORITY / "observe_config.json"
NUM_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])")
# 要件定義の番号 → その要件を書く、設計書の節。要件が増えて、ここに行が無ければ止まる。
INDEX_MAP = {"1": ("3-0 目標の③",), "2": ("3-0 目標の①",),
             "3-1": ("4-7",), "3-2": ("4-7",), "3-3": ("4-7",), "3-4": ("4-7",), "3-5": ("4-7",), "3-6": ("4-4", "4-6"),
             "4": ("4-7",), "5": ("4-8", "4-9"), "6": ("4-3", "4-13"), "7": ("4-10",),
             "8-1": ("7-3b",), "8-2": ("7-3b", "4-21"), "9": ("3-0 目標の①", "3-0 目標の⑤", "3-0 目標の⑥"), "10": ("2-0",)}


def _hk(d: dict) -> tuple:
    """その設計書の、手書きの項目の名前（新しい形は6つ・いままでの形は5つ）。"""
    return HAND_KEYS_NEW if d.get("形") == "新" else HAND_KEYS


def work_kind(d: dict) -> int:
    """工事の種類。1＝指標・探索・売買のロジック・設定に触る工事／2＝検査やプログラムを直す工事。直すファイルの一覧で決める（CC は書かない）。"""
    ps = [str(p) for p in (d.get("TARGET") or []) + (d.get("NEW_FILE") or [])]
    return 1 if any(w in p for p in ps for w in KIND1_WORDS) else 2


def _para(lines: list) -> str:
    """手書きの文を、段落の間の空行を残して1つの文字列にする（ひな型の「★向きを見る所」の行と、前後の空行は落とす）。"""
    keep = [ln.rstrip() for ln in lines if not ln.strip().startswith("★向きを見る所")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(keep)).strip()


def _named(name: str, text: str) -> bool:
    """名前（法則の番号・型の番号・指標の名前）が、文の中に、ほかの英数字とつながらずに在るか。"""
    return bool(name) and re.search(r"(?<![A-Za-z0-9_-])" + re.escape(name) + r"(?![A-Za-z0-9_-])", text) is not None


def _plan_link(work: str, d_dir: Path) -> tuple:
    """読むもの宣言から、やることの番号と結ぶ要件の項目を写す（CC は書かない）。戻り＝(番号の文, 要件の文, 問題の文, 宣言の全文)。
    読む順＝①いまの宣言（設計書の名前がこの工事のとき）②工事のフォルダの写し（宣言が次の工事の物に替わった後）。"""
    for p in (PLAN, d_dir / PLAN_COPY):
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        got: dict = {}
        for ln in text.splitlines():
            s = ln.strip()
            for key, name in (("設計書:", "name"), (PLAN_NUM_KEY, "nums"), (PLAN_REQ_KEY, "req")):
                if s.startswith(key) and name not in got:
                    got[name] = s[len(key):].strip()
        if got.get("name") == work and got.get("nums") and got.get("req"):
            return got["nums"], got["req"], "", text
    return "", "", (f"読むもの宣言（{PLAN.name} か、工事のフォルダの {PLAN_COPY}）に、この工事（{work}）の「やることの番号」と"
                    "「結ぶ要件の項目」の行が無い（require_read_plan_before_design.py --write で宣言を作る）"), ""


def _read_new_todo(d: dict, top: dict, hand: dict, bad: list, work: str, d_dir: Path) -> None:
    """新しい形の やることの表から、手書きの項目・やることの一覧・やらないことを読む。足りない物は bad に全部 足す。"""
    d["何を作るか"] = _para(hand.get("§1 概要") or [])
    ex = _para(hand.get("4-19 通しの例") or [])
    d["設計の中身"]["4-19"] = ex.split("\n") if ex else []
    row = _md_table(hand.get("この工事が結ぶ要件と、減らす違い") or [], ("欄", "中身"), "この工事が結ぶ要件と、減らす違い", bad)
    if len(row) != 3:
        bad.append(f"「この工事が結ぶ要件と、減らす違い」の表が3行（どの行か・どこまで減らすか・順番）でない（いま {len(row)} 行）")
    d["どの行の工事か"] = row
    goal = _md_table(hand.get("目標") or [], ("番号", "欄", "中身"), "目標", bad)
    have = [r["番号"] for r in goal]
    if have != list(GOAL_NOS):
        bad.append(f"「目標」の表の番号が ①〜⑥ の6行でない（いま {'・'.join(have) or '無し'}）")
    for r in goal:
        if r["番号"] in ("④", "⑥") and r["中身"].strip() in EMPTY_WORDS:
            bad.append(f"目標の{r['番号']}（{r['欄']}）が空（空では出せない。無いと書くときは、根拠と確かめ直すコマンドを書く）")
    d["目標"] = goal
    d["やることの一覧"] = _md_table(top.get("一覧") or [], ("番号", "一文", "出どころ"), "## 一覧", bad)
    d["やらないこと"] = [{k: r[k] for k in ("中身", "理由", "出どころ")}
                       for r in _md_table(top.get("やらないこと") or [], ("番号", "中身", "理由", "出どころ"), "## やらないこと", bad)]
    nums, req, why, text = _plan_link(work, d_dir)
    if why:
        bad.append(why)
    d["やることの番号の文"], d["結ぶ要件"], d["読むもの宣言の文"] = nums, req, text
    # ★読むもの宣言のすり抜けを塞ぐ（設計書の監査 CP75 の Q10）＝宣言が「なし」（やることリストに行が無い工事）なのに、
    #   やることの表の一覧に、やることリストの行の番号が出てくれば止める。
    if nums.startswith("なし"):
        try:
            known = {str(t.get("番号")) for t in (_load(TODO).get("やること") or []) if isinstance(t, dict) and t.get("番号")}
        except SystemExit:
            known = set()
        hit = sorted(n for n in known if _named(n, "\n".join(top.get("一覧") or [])))
        if hit:
            bad.append(f"読むもの宣言は「やることの番号＝なし」なのに、{TODO_MD} の「## 一覧」に、やることリストの行の番号 {'・'.join(hit)} が在る"
                       "（宣言の元データの「やることの番号」に、その番号を書いて、宣言を作り直す）")


def _read_new_head(d: dict, k: str, body: list, bad: list) -> None:
    """案の新しい見出し3つを読む。"""
    first = _text(body)
    na = first.startswith("非該当")
    val = {"非該当": first.split("＝", 1)[-1].strip()} if na else [ln for ln in body if ln.strip()]
    if k == HEAD_FIVE:
        d["設計の中身"]["4-22"] = val
        d["直す工事の5つ"] = [] if na else _md_table(body, ("番号", "欄", "中身"), f"【{k}】", bad)
    elif k == HEAD_NUMS:
        d["設計の中身"]["4-21"] = val
        d["数字と式"] = [] if na else _md_table(body, ("番号", "数字か式", "出どころ"), f"【{k}】", bad)
    else:
        d["確かめていないこと"] = _md_table(body, ("確かめていないこと", "なぜ確かめていないか", "確かめるなら、何を走らせるか"), f"【{k}】", bad)


def _new_numbers(d: dict) -> list:
    """実装の指示のうち、売買のロジック・設定のファイルに新しく入る数字を抜き出す。戻り＝[(実装の番号, 数字), …]。
    コメント（# から後ろ）の中の数字と、直す前の文字にも在る数字は数えない。"""
    out = []
    for it in d.get("実装の指示") or []:
        if not any(w in str(it.get("対象のファイル") or "") for w in KIND1_WORDS):
            continue
        def _code(s):
            return "\n".join(ln.split("#", 1)[0] for ln in str(s or "").splitlines())
        old = set(NUM_RE.findall(_code(it.get("直す前の文字"))))
        seen: list = []
        for v in NUM_RE.findall(_code(it.get("中身"))):
            if v not in old and v not in seen:
                seen.append(v)
        out += [(str(it.get("番号")), v) for v in seen]
    return out


def _finish_new(d: dict, bad: list) -> None:
    """新しい形の元を全部 読んだ後の検査と、プログラムが決める欄。足りない物は bad に全部 足す。"""
    body = d["設計の中身"]
    kind = work_kind(d)
    if "要件定義との照らし" in d:
        bad.append("新しい形の案に【0-R】が在る（要件定義との照らしは、案に書かない。索引は、プログラムが作る）")
    if kind == 2:
        g = {r["番号"]: r["中身"] for r in d.get("目標") or []}
        d["期待値分解"] = (f"売買に触らない工事です。目標の③（net までのつながり）＝{g.get('③', '')}／"
                        f"目標の④（無駄だったと分かる物）＝{g.get('④', '')}（プログラムが、目標から写した）")
    # 4-6 と 4-7 は、種類①の工事では必ず書く（書くかどうかを CC が決めない）
    if kind == 1:
        for no in ("4-6", "4-7"):
            if isinstance(body.get(no), dict):
                bad.append(f"種類①の工事なのに、案の【{no}】が非該当（種類①の工事では、必ず書く）")
    # 検査やプログラムを直す工事で書く5つ（4-22）
    if kind == 2 and (("4-22" not in body) or isinstance(body["4-22"], dict)):
        bad.append(f"種類②の工事なのに、案の【{HEAD_FIVE}】が無い・非該当（種類②の工事では、必ず書く）")
    if kind == 1 and "4-22" not in body:
        body["4-22"] = {"非該当": "種類①の工事（直すファイルの一覧から、プログラムが決めた）"}
    if "4-22" in body and not isinstance(body["4-22"], dict):
        five = d.get("直す工事の5つ") or []
        if [r["番号"] for r in five] != ["①", "②", "③", "④", "⑤"]:
            bad.append(f"【{HEAD_FIVE}】の表の番号が ①〜⑤ の5行でない")
        for r in five:
            if r["番号"] == "④" and r["中身"].strip() in EMPTY_WORDS:
                bad.append(f"【{HEAD_FIVE}】の④（この直しで確かめなくなる事・弱くなる守り）が空（空では出せない）")
    # 新しく入る数字と式の一覧（4-21）
    nums = _new_numbers(d) if kind == 1 else []
    d["新しく入る数字"] = nums
    if kind == 1:
        if "4-21" not in body:
            bad.append(f"種類①の工事なのに、案の【{HEAD_NUMS}】が無い")
        rows = d.get("数字と式") or []
        cells = " ".join(r["数字か式"] for r in rows)
        miss = [f"実装 {no} の {v}" for no, v in nums
                if not re.search(r"(?<![0-9.])" + re.escape(v) + r"(?![0-9.])", cells)]
        if miss:
            bad.append(f"【{HEAD_NUMS}】に、出どころの行が無い数字が {len(miss)} 件: " + "・".join(miss[:20]))
        for r in rows:
            if r["出どころ"].strip() in EMPTY_WORDS:
                bad.append(f"【{HEAD_NUMS}】の「{r['数字か式']}」に、出どころが無い")
    elif "4-21" not in body:
        body["4-21"] = {"非該当": "種類②の工事。売買のロジック・設定のファイルを直さないので、そこに入る数字が無い（直すファイルの一覧から、プログラムが決めた）"}
    if not d.get("確かめていないこと"):
        bad.append(f"案の【{HEAD_UNVERIFIED}】に行が無い（CC がやっていない確かめを、1行以上 書く）")
    if not d.get("作ってはいけないものとの照合"):
        bad.append("案の【7-3b】が無い（番号・根拠・確かめ直すコマンドの表）")
    # 完成の条件に、やることの番号ごとの行が在るか（別セッションの監査 2026-10-12 の M-7）
    cond = " ".join(str(r.get("条件") or "") for r in d.get("完成の条件") or [])
    excuse = " ".join(ln for ln in (d.get("案の文") or {}).get("7-6") or [] if ln.strip().startswith("- 行が無いやることの番号"))
    for r in d.get("やることの一覧") or []:
        n = str(r["番号"])
        if not _named(n, cond) and not _named(n, excuse):
            bad.append(f"やることの番号 {n} に、完成の条件（【7-6】）の行が無い（行を足すか、「- 行が無いやることの番号と、その理由：」の行に理由を書く）")


def sec_state(d: dict, sec: str) -> tuple:
    """索引の対応（INDEX_MAP）の節の状態。戻り＝(状態, 非該当の理由)。状態＝書いた／非該当／書いていない／空。
    ★2026-10-18（ToDo の15番）＝索引（_index_lines）と、監査依頼書の要件ごとの問い（gen_audit_docs.py）が、同じ決め方を呼ぶ（2か所に書かない）。"""
    body = d.get("設計の中身") or {}
    if sec.startswith("4-"):
        got = body.get(sec)
        if isinstance(got, dict) and got.get("非該当"):
            return "非該当", str(got["非該当"])
        return ("書いた", "") if got else ("書いていない", "")
    if sec.startswith("3-0 目標の") and sec[-1] != "①":
        cell = next((str(r.get("中身") or "") for r in d.get("目標") or [] if r.get("番号") == sec[-1]), "")
        if cell.strip() in EMPTY_WORDS:
            return "空", ""
    return "書いた", ""


def _index_lines(d: dict) -> list:
    """要件定義の索引（要件定義の何番を、この設計書のどの節に書いたか）。プログラムが、設計書の中身から作る。"""

    def _state(sec: str) -> str:
        st, why = sec_state(d, sec)
        return f"{sec}＝{st}（{_esc(why)}）" if st == "非該当" else f"{sec}＝{st}"

    L = ["### 0-R 要件定義の索引（要件定義の何番を、この設計書のどの節に書いたか）", "",
         _tag("自動", "要件は正本から。書いた節と、その節の状態は、プログラムがこの設計書の中身から決めた（CC は判定を書かない）"),
         "| # | 要件（正本から） | 書いた節と、その節の状態 |", "|---|---|---|"]
    for no, name in gcr.requirement_items(full=True):
        secs = INDEX_MAP.get(no)
        if not secs:
            raise SystemExit(f"[gen_acceptance] 要件定義の {no}（{name}）を書く節が、索引の対応（INDEX_MAP）に無い（fail-closed）")
        L.append(f"| {no} | {name} | {'／'.join(_state(s) for s in secs)} |")
    if work_kind(d) == 2:
        L += ["", "非該当と出た節の要件に「触らない」根拠は、4-22（検査やプログラムを直す工事で書く5つ）の⑤に在ります。"]
    return L


def _sec2_new(d: dict) -> list:
    """2番の節の先頭（この工事が結ぶ要件と、減らす違い・やることの一覧）。"""
    L = ["### 2-0 この工事が結ぶ要件と、減らす違い", "",
         _tag("自動", "やることの番号と結ぶ要件＝読むもの宣言から、プログラムが写した"),
         f"- やることの番号＝{d.get('やることの番号の文', '')}",
         f"- 結ぶ要件＝{d.get('結ぶ要件', '')}", "",
         _tag("手書き", "やることの表の「この工事が結ぶ要件と、減らす違い」"),
         "| 欄 | 中身 |", "|---|---|"]
    L += [f"| {_esc(r['欄'])} | {_esc(r['中身'])} |" for r in d.get("どの行の工事か") or []]
    L += ["", "### 2-0b やることの一覧", "",
          _tag("自動", "やることの表の「## 一覧」から、プログラムが写した"),
          "| 番号 | 一文 | 出どころ |", "|---|---|---|"]
    L += [f"| {_esc(r['番号'])} | {_esc(r['一文'])} | {_esc(r['出どころ'])} |" for r in d.get("やることの一覧") or []]
    return L + [""]


def _goal_lines(d: dict) -> list:
    """3番の節の先頭（目標の6つ）。①は、プログラムが結ぶ要件と「どこまで減らすか」から写す。"""
    row = d.get("どの行の工事か") or []
    less = row[1]["中身"] if len(row) > 1 else ""
    L = ["### 3-0 目標", "",
         _tag("手書き", "やることの表の「目標」（①は、プログラムが、結ぶ要件と「その違いを、どこまで減らすか」から写した）"),
         "| 番号 | 欄 | 中身 |", "|---|---|---|"]
    for r in d.get("目標") or []:
        body = f"{d.get('結ぶ要件', '')}。その要件との違いを、どこまで減らすか＝{less}" if r["番号"] == "①" else r["中身"]
        L.append(f"| {r['番号']} | {_esc(r['欄'])} | {_esc(body)} |")
    return L + [""]


def _unverified_lines(d: dict) -> list:
    """6番の節の最後（確かめていないこと）。"""
    L = ["### 6-5 確かめていないこと（CC がやっていない確かめ）", "",
         _tag("自動", "まこさんが OK した案の【確かめていないこと】"),
         "| # | 確かめていないこと | なぜ確かめていないか | 確かめるなら、何を走らせるか |", "|---|---|---|---|"]
    for i, r in enumerate(d.get("確かめていないこと") or [], 1):
        L.append(f"| {i} | {_esc(r['確かめていないこと'])} | {_esc(r['なぜ確かめていないか'])} | {_esc(r['確かめるなら、何を走らせるか'])} |")
    return L + [""]


def _forbidden_new(d: dict) -> list:
    """7-3b（作ってはいけないものとの照合）。左の2列は要件定義の8番（正本）・右の2列は案の根拠と確かめ直すコマンド。CC の判定の欄は無い。"""
    L = [_tag("自動", "左の2列は要件定義の8番（正本）・右の2列は まこさんが OK した案の【7-3b】"),
         "| # | 作ってはいけないもの（要件定義の8番） | 根拠 | 確かめ直すコマンド |", "|---|---|---|---|"]
    got = d.get("作ってはいけないものとの照合") or {}
    for no, name in gcr.requirement_items(full=True):
        if not no.startswith("8-"):
            continue
        n = no.split("-", 1)[1]
        r = got.get(n)
        if not r:
            raise SystemExit(f"[gen_acceptance] 「作ってはいけないもの」の {n} 番の行が、案の【7-3b】に無い（fail-closed）")
        L.append(f"| {n} | {_esc(name)} | {_esc(r.get('根拠', ''))} | {_esc(r.get('確かめ直すコマンド', ''))} |")
    return L


def _hit_names(text: str, names) -> list:
    """文の中に名前が在る物の一覧。長い名前から当て、当てた所を消す（「前日POC」と書いた文で、「POC」を当てない）。
    設計書の監査 CP77 の修正 1 の当て方を、4-7 の指標の行と、2-2 の関わる指標の数の、両方で使う。"""
    rest, hit = text, []
    for k in sorted({str(n) for n in names}, key=lambda s: (-len(s), s)):
        if _named(k, rest):
            hit.append(k)
            rest = re.sub(r"(?<![A-Za-z0-9_-])" + re.escape(k) + r"(?![A-Za-z0-9_-])", "\n", rest)
    return sorted(hit)


def _table_kinds() -> set:
    """承認済みの型の表（signal_families.json の parts）に部品が在る、指標の種類。
    部品の名前から種類を引くのは、指標の定義の表（indicator_reference_diag.find）＝売買を回すプログラムの検査 G6 と同じ引き方。"""
    import contextlib
    import io
    if str(PRIORITY) not in sys.path:
        sys.path.insert(0, str(PRIORITY))
    with contextlib.redirect_stdout(io.StringIO()):
        import indicator_reference_diag as iref
    out = set()
    for p in _load(FAMILIES).get("parts") or []:
        ent, _prm = iref.find(str(p))
        if ent is not None:
            out.add(str(ent.get("family")))
    return out


def _timeframe_rows() -> list:
    """4-7 に、プログラムが置き場から写す、時間足の行（使える時間足の全部と、役割ごとに使える時間足）。"""
    tfs = [str(t) for t in (_load(OBS_CFG).get("timeframes") or [])]
    rl = _load(FAMILIES).get("role_lineage") or {}
    L = [_tag("自動", f"使える時間足の全部＝`{OBS_CFG.name}` の timeframes。役割ごとに使える時間足＝`{FAMILIES.name}` の role_lineage。プログラムが写した"),
         "| 何 | 使える時間足 |", "|---|---|",
         f"| 全部（{len(tfs)}個） | {_esc('・'.join(tfs))} |"]
    for role, v in sorted((rl.get("roles") or {}).items()):
        tf = (v or {}).get("tfs")
        L.append(f"| 役割 {_esc(role)}（型 {_esc('・'.join(str(x) for x in rl.get('applies_to') or []))} に掛かる） "
                 f"| {'全部' if tf == 'all' else _esc('・'.join(str(x) for x in tf or []))} |")
    return L + [""]


def _indicator_rows(text: str) -> list:
    """4-7 に、プログラムが置き場から写す行（役割・範囲・代表の値・出どころ・カタログに在るか・型の表に在るか・オンか・閾値）。文に名前が在る指標だけ。"""
    params = {str(x.get("種類")): x for x in (_load(PARAMS).get("指標") or []) if isinstance(x, dict)}
    rl = _load(ROLES)
    roles = {str(x.get("種類")): x for x in (rl if isinstance(rl, list) else []) if isinstance(x, dict)}
    sw = _load(SWITCH)
    on, off = {str(x) for x in sw.get("on") or []}, {str(x) for x in sw.get("off") or []}
    tag = _tag("自動", f"`{PARAMS.name}`・`{ROLES.name}`・`{SWITCH.name}` から、この項目の文に名前が在る指標の行を、プログラムが写した")
    # 名前の相手に、オンとオフの一覧も入れる（オフの指標・資料に行が無い指標も、行に出す）。
    # 長い名前から当て、当てた所を消す（「前日POC」と書いた文で、「POC」の行を出さない）＝_hit_names。
    hit = _hit_names(text, set(params) | set(roles) | on | off)
    if not hit:
        return [tag, "この項目の文に、指標の名前（指標の定義の表の「種類」）が見つかりません。", ""]
    # ★設計書の監査 CP77 の修正（2026-10-13）＝「カタログに在るか」を2つの列で出す。
    #   カタログ＝指標の定義の表（オンとオフの一覧は、その種類の全部を写した物）。承認された範囲＝承認済みの型の表の部品。
    in_table = _table_kinds()
    L = [tag, "| 指標 | 役割（出どころの役割／役割の印） | パラメータの名前と範囲 | 代表の値（スキャル） | 代表の値（デイトレ） "
              "| カタログ（指標の定義の表）に在るか | 承認済みの型の表に在るか | オンか | 閾値の代表の値 |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k in hit:
        p, r = params.get(k) or {}, roles.get(k) or {}
        rng = "／".join(f"{x.get('下限')}〜{x.get('上限')}（{x.get('出どころ')}）" for x in p.get("範囲") or [] if isinstance(x, dict))
        th = r.get(THRESHOLD_KEY)
        th_s = (f"スキャル {th.get('最初の値（スキャル）')}／デイトレ {th.get('最初の値（デイトレ）')}／範囲 {th.get('範囲')}／出どころ {th.get('出どころ')}"
                if isinstance(th, dict) else f"未決（置き場 {ROLES.name} に「{THRESHOLD_KEY}」の欄が無い）")
        L.append(f"| {_esc(k)} | {_esc(r.get('出どころの役割', '（置き場に行が無い）'))}／{_esc(r.get('役割の印', '—'))} "
                 f"| {_esc('・'.join(str(x) for x in p.get('パラメータの名前') or []))}：{_esc(rng or '（範囲の行が無い）')} "
                 f"| {_esc(p.get('最初の値（スキャル）', '（置き場に行が無い）'))}（{_esc(p.get('最初の値の出どころ（スキャル）', '—'))}） "
                 f"| {_esc(p.get('最初の値（デイトレ）', '（置き場に行が無い）'))}（{_esc(p.get('最初の値の出どころ（デイトレ）', '—'))}） "
                 f"| {'在る' if (k in on or k in off) else '無い'} | {'在る' if k in in_table else '無い'} "
                 f"| {'オン' if k in on else ('オフ' if k in off else 'オンとオフの一覧に名前が無い')} | {_esc(th_s)} |")
    # ★2026-10-20（ToDo の26番・監査 CP78 の Minor B・まこさん「CCの勧めでよい」）＝カタログの列は、行が出る指標ではいつも「在る」。
    #   カタログに無い名前は行が出ないだけで、このプログラムは見つけられない。そのことを表の下に出す（列は外さない）
    L += ["", "行が出るのは、カタログ（指標の定義の表）に在る名前だけです。カタログに無い名前を案に書いても、"
              "このプログラムは見つけられません（その名前の行は出ません）。"]
    return L + [""]


def _auto_rows(no: str, lines: list, d: dict) -> list:
    """4番の節の項目の下に、プログラムが置き場から写す行（新しい形の設計書だけ）。写す物が無い項目は空の並び。"""
    text = "\n".join(str(x) for x in lines)
    L: list = []
    if no == "4-0":
        L += [_tag("自動", "§1 概要の1文目を、プログラムが写した"),
              "この工事が解く問題＝" + str(d.get("何を作るか") or "").split("\n")[0], ""]
    if no in ("4-4", "4-6"):
        # 「法則」の語が在る行だけで番号を探す（自己テストの項目 T1〜T5 と、法則 T1〜T5 を取り違えない）
        _lt = "\n".join(ln for ln in text.split("\n") if "法則" in ln)
        laws = [x for x in (_load(LAWS).get("法則") or []) if isinstance(x, dict) and _named(str(x.get("番号") or ""), _lt)]
        if laws:
            L += [_tag("自動", f"法則の原文＝`{LAWS.name}` から、この項目の文に番号が在る法則を、プログラムが写した"),
                  "| 番号 | 場面 | 一文 | 説明 |", "|---|---|---|---|"]
            L += [f"| {_esc(x.get('番号'))} | {_esc(x.get('場面'))} | {_esc(x.get('一文'))} | {_esc(x.get('説明', ''))} |" for x in laws]
            L += [""]
        fams = [f for f in (_load(FAMILIES).get("families") or []) if isinstance(f, dict)
                and (_named(str(f.get("id") or ""), text) or (f.get("name") and str(f.get("name")) in text))]
        if fams:
            L += [_tag("自動", f"型の名前＝`{FAMILIES.name}` から、この項目の文に番号が在る型を、プログラムが写した"),
                  "| 型の番号 | 型の名前 |", "|---|---|"]
            L += [f"| {_esc(f.get('id'))} | {_esc(f.get('name'))} |" for f in fams]
            L += [""]
        # ★設計書の監査 CP77 の修正（2026-10-13）＝場面の決まりの原文を写す。置き場は、法則のファイルの「機械が読む判定」
        #   （売買を回すプログラムの審査 _check_scene_rules が読む欄）。「場面の決まり」の語が在る行に書いた、法則の番号で探す。
        _st = "\n".join(ln for ln in text.split("\n") if "場面の決まり" in ln)
        scn = [x for x in (_load(LAWS).get("法則") or []) if isinstance(x, dict) and _named(str(x.get("番号") or ""), _st)]
        if scn:
            L += [_tag("自動", f"場面の決まりの原文＝`{LAWS.name}` の「機械が読む判定」から、この項目の文に番号が在る決まりを、プログラムが写した"),
                  "| 番号 | 機械が読む判定 |", "|---|---|"]
            L += [f"| {_esc(x.get('番号'))} | {_esc(json.dumps(x.get('機械が読む判定'), ensure_ascii=False))} |" for x in scn]
            L += [""]
    if no == "4-7":
        L += _indicator_rows(text)
        L += _timeframe_rows()
    if no == "4-21":
        nums = d.get("新しく入る数字") or []
        L += [_tag("自動", "実装の指示のうち、売買のロジック・設定のファイルに新しく入る数字を、プログラムが抜き出した（コメントの中の数字と、直す前から在る数字は除く）"),
              "| 実装の番号 | 数字 |", "|---|---|"]
        L += [f"| {a} | {b} |" for a, b in nums] or ["| — | 抜き出した数字は0件 |"]
        L += [""]
    return L


def _design_audit_reports(d: dict) -> list:
    """この設計書が受けた設計書の監査の、結果ファイル（名前に、工事の名前と design_cp が入る物）。"""
    key = str(d.get("iter") or "").replace("-", "_")
    if not key:
        return []
    return sorted(str(p.relative_to(ROOT)) for p in AUDITS.glob(f"*_{key}_design_cp*_audit_report.md"))


def _sections_rc() -> tuple:
    """項目の抜けを見張る検算（gen_design_sections.py --check）を走らせる。戻り＝(終了コード, 出力)。
    見本の工事（自己テスト）では走らせない（本物の記録に頼らないため）。"""
    if WORK.startswith(SAMPLE_WORK):
        return 0, ""
    import contextlib
    import io
    import gen_design_sections as gds
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = gds.check()
    return rc, buf.getvalue()


def src() -> dict:
    """工事のフォルダから設計書を組む中身を作る。「やらないこと」が空なら止まる（fail-closed の2つ目）。
    ★2026-09-30（設計書 point1-one-way-20260930）＝工事のフォルダ（src_from_work）の1本だけ。
      工事名が無ければ止まる（元データの JSON へは戻らない）。"""
    if not WORK:
        raise SystemExit("[gen_acceptance] 工事名がありません（fail-closed）。--work <工事名> を付けてください"
                         "（設計書の作り方は工事のフォルダの1本だけ・元データの JSON は使わない）。")
    d = src_from_work(WORK)                          # ★見出しの下の表示を替える変数（_NEW_FORM）は src_from_work が立てる（2026-10-18）
    if not d.get("やらないこと"):
        raise SystemExit(
            "[gen_acceptance] 元データの「やらないこと」が空です（fail-closed）。\n"
            "  ★探す候補を切ったのに理由を書かない、を防ぐための検査です。\n"
            "  切るものが無いなら、その旨を1行 書いてください。")
    return d


# ══ 囲みの中身を作る（正本から）══════════════════════════════════════

def build_materials(d: dict) -> str:
    """探す材料の一覧＝印がオンの指標・役割ごとの系統・時間足・範囲・格子。"""
    if not touches_trading(d):
        return NONTRADE
    sw = _load(SWITCH)
    fam = _load(FAMILIES)
    lim = _load(LIMITS)
    on = sw.get("on") or []
    L = []
    add = L.append
    add("**★この節はプログラムが作ります（手で書き換えない）。**"
        f"出どころ＝`{SWITCH.name}`・`{FAMILIES.name}`・`{LIMITS.name}`。")
    add("")
    if d.get("形") == "新":
        # ★2026-10-13＝新しい形の設計書では、関わる指標の行だけを出す（案の【4-7】の文に名前が在る指標）
        _t47 = "\n".join(str(x) for x in ((d.get("設計の中身") or {}).get("4-7") or []))
        _all = len(on)
        # ★設計書の監査 CP77 の修正＝名前の当て方を、4-7 の指標の行と同じにする（長い名前から当てる。オフの指標も相手に入れる）
        _off = [str(x) for x in sw.get("off") or []]
        _rel = set(_hit_names(_t47, [str(x) for x in on] + _off))
        on = [x for x in on if str(x) in _rel]
        add(f"**この工事が関わる指標＝{len(on)}種**（案の【4-7】の文に名前が在る物。印がオンの指標は、全部で {_all}種）。")
        _off_rel = sorted(x for x in _off if x in _rel)
        if _off_rel:
            add("")
            add(f"**案の【4-7】の文に名前が在るが、印がオフの指標＝{len(_off_rel)}種**（{'・'.join(_off_rel)}）。オフの指標は、どのロジックからも使えません（要件定義の6番）。")
    else:
        add(f"**探す指標＝印がオンの {len(on)}種**（印を切り替えると、この一覧も設計も変わります）。")
    add("")
    add("```")
    add("・".join(str(x) for x in on))
    add("```")
    add("")
    add("**別枠の材料**")
    add("")
    add("| 別枠 | 印がオンのもの |")
    add("|---|---|")
    for key, name in (("geo_on", "レンジ幾何"), ("demand_on", "需給"), ("time_on", "時間帯")):
        add(f"| {name} | {_esc('・'.join(str(x) for x in (sw.get(key) or [])))} |")
    add("")
    roles = ((fam.get("role_lineage") or {}).get("roles") or {})
    add("**役割ごとに使える系統と時間足（型の表）**")
    add("")
    add("| 役割 | 系統 | 時間足 | レンジ幾何 |")
    add("|---|---|---|---|")
    for r, v in roles.items():
        tfs = v.get("tfs")
        tfs_s = "全部" if tfs == "all" else _esc("・".join(tfs or []))
        add(f"| {r} | {_esc('・'.join(v.get('lineages') or []))} | {tfs_s} "
            f"| {'使う' if v.get('geo') else '—'} |")
    add("")
    add("**値の範囲と格子（承認済み・この工事で数字を1つも作らない）**")
    add("")
    add("| 鍵 | 中身 |")
    add("|---|---|")
    for k in ("quantile_grid", "quantile_range", "int_grid", "int_range",
              "state_hold_bars_range", "nest_offset_range", "ref_mult_range",
              "hour_range", "material_param_ranges"):
        if k in lim:
            v = lim[k]
            s = "（空＝材料カタログの最小〜最大を使う）" if v == {} else _esc(json.dumps(v, ensure_ascii=False))
            add(f"| `{k}` | {s} |")
    add("")
    return "\n".join(L)


def build_laws(d: dict) -> str:
    """場面の法則の一覧＝全件（1件も落とさない・fail-closed の4つ目で数を照らす）。"""
    law = _load(LAWS)
    rows = [x for x in (law.get("法則") or []) if isinstance(x, dict)]
    L = []
    add = L.append
    add(f"**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`{LAWS.name}`。")
    add("")
    add(f"**相場の法則は全部で {len(rows)}件**です（場面ごと）。"
        "この表は1件も落としません（落とすと `--write` が止まります）。")
    add("")
    add("| 番号 | 場面 | 一文 | 機械が読む判定 | 掛かる場面 | 根拠 |")
    add("|---|---|---|---|---|---|")
    for r in rows:
        j = r.get("機械が読む判定")
        if isinstance(j, dict):
            typ = j.get("型", "")
            sel = j.get("数える部品")
            detail = ""
            if isinstance(sel, dict):
                parts = []
                for k in ("系統", "family", "geo", "性質", "時間足", "かつ", "側", "向きを持つ"):
                    if k in sel:
                        v = sel[k]
                        parts.append(f"{k}＝{_esc(json.dumps(v, ensure_ascii=False)) if isinstance(v, (dict, list)) else _esc(v)}")
                detail = "／".join(parts) + f"／本数 {j.get('本数', '')}"
            elif typ == "形を持つ":
                detail = f"形＝{j.get('形', '')}"
            elif typ == "系統を重ねない":
                detail = f"除く系統＝{_esc('・'.join(j.get('除く系統') or []))}／上限 {j.get('上限', '')}"
            jt = f"**{typ}**（{detail}）"
            scenes = _esc("・".join(j.get("掛かる場面") or []))
        elif r.get("判定の置き場"):
            jt = f"—（判定の置き場＝{_esc(r['判定の置き場'])}）"
            scenes = "—"
        else:
            jt = "—"
            scenes = "—"
        kyo = f"{len(r['根拠'])}件" if isinstance(r.get("根拠"), list) else "—"
        add(f"| **{_esc(r.get('番号'))}** | {_esc(r.get('場面'))} | {_esc(r.get('一文'))} "
            f"| {jt} | {scenes} | {kyo} |")
    add("")
    with_j = [x for x in rows if isinstance(x.get("機械が読む判定"), dict)]
    add(f"**内訳（プログラムが数えました）**＝機械が読む判定を持つもの **{len(with_j)}件** ／ "
        f"持たないもの **{len(rows) - len(with_j)}件**。")
    add("")
    return "\n".join(L)


def build_ranking(d: dict) -> str:
    """成績表に載っている本数＝役割 × 上位足（印の絞りを通した後）。"""
    if not touches_trading(d):
        return NONTRADE
    rk = _load(RANKING)
    order = (rk.get("順位") or {})
    up = ("10m", "15m", "30m", "1h", "2h", "4h", "6h", "1d")
    L = []
    add = L.append
    add(f"**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`{RANKING.name}`。")
    add("")
    # ★2026-10-03＝先読みの鍵を「24」に決め打ちしない。成績表の「先を見るバー数」のうち短い方を読む
    #   （直す前＝札を版3 にして鍵が 12・120 になった成績表で、本数が全部 0 と出た）。
    hz_all = [str(x) for x in (rk.get("先を見るバー数") or [])]
    hz = hz_all[0] if hz_all else "24"
    add(f"**成績表に載っている列の本数**（札＝強さ・先読み{hz}・執行足より上の時間足だけ）")
    add("")
    add("| 役割 | 上位足の列の本数 | 分離力の高い順に3本 |")
    add("|---|---|---|")
    for role in sorted(order):
        rows = ((order.get(role) or {}).get("強さ") or {}).get(hz) or []
        hit = [(c, a) for c, a in rows if isinstance(c, str) and c.rsplit("__", 1)[-1] in up]
        top = sorted(hit, key=lambda x: -abs(float(x[1]) - 0.5))[:3]
        add(f"| {role} | {len(hit)} | {_esc('／'.join(f'{c}（{a}）' for c, a in top))} |")
    add("")
    add("**★この本数は、印がオンの指標だけを数えたものではありません。**"
        "組む側は `ranked_materials` を通して引き、その関数が印オフの指標を落とします。")
    add("")
    return "\n".join(L)


def build_coderef(d: dict) -> str:
    """触る関数の名前と定義の行（★手で写さない・93番）。"""
    sys.path.insert(0, str(PRIORITY))
    try:
        from verify_design_contract import spec_from_impl
    except Exception as e:
        raise SystemExit(f"[gen_acceptance] 照合の道具を読み込めない: {e}（fail-closed）")
    impl = str(((d.get("DESIGN_CONTRACT") or {}).get("impl_file")) or "")
    path = SDK / impl if impl else GEN_PY
    if not path.exists():
        raise SystemExit(f"[gen_acceptance] 直す相手が無い: {path}（fail-closed）")
    spec = spec_from_impl(str(path))
    names = [str(x) for x in ((d.get("DESIGN_CONTRACT") or {}).get("self_check_calls") or [])]
    L = []
    add = L.append
    add("**★この節はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`"
        "（★行番号を手で写さない・93番）。")
    add("")
    add(f"**直す相手**＝`{impl or GEN_PY.name}`")
    add("")
    add("| 触る関数 | 定義の行 |")
    add("|---|---|")
    dl = spec.get("def_lines") or {}
    for n in names:
        add(f"| `{n}` | {dl.get(n, '（この関数は実物に無い）')} |")
    add("")
    add(f"**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で {len(dl)}件の関数が在ります）。")
    add("")
    return "\n".join(L)


def build_random(d: dict) -> str:
    """乱数を使っている場所（構文の木で数える・文字を探さない）。"""
    if not touches_trading(d):
        return NONTRADE
    if not GEN_PY.exists():
        raise SystemExit(f"[gen_acceptance] 実物が無い: {GEN_PY}（fail-closed）")
    text = GEN_PY.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(text)
    hits: dict[str, int] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        n = 0
        for sub in ast.walk(node):
            if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) and sub.value.id == "rng":
                n += 1
            elif isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id in ("draw_param", "draw_q", "draw_int", "draw_num"):
                n += 1
        if n:
            hits[node.name] = n
    L = []
    add = L.append
    add("**★この節はプログラムが作ります（手で書き換えない）。**"
        f"出どころ＝`{GEN_PY.name}` を構文の木で読んだ結果（コメントの中の文字は数えません）。")
    add("")
    add(f"**乱数を使っている関数＝{len(hits)}個 ／ 使っている回数の合計＝{sum(hits.values())}**")
    add("")
    add("| 関数 | 回数 |")
    add("|---|---|")
    for n, c in sorted(hits.items(), key=lambda x: (-x[1], x[0])):
        add(f"| `{n}` | {c} |")
    add("")
    # ★2026-09-29＝「この工事で0にするのは、場面の判定の束を組む所だけです」の固定の文を消した
    #   （どの工事でも同じ文が出て、工事と食い違った＝worklog 20260929 §40 の2）。何を0にするかは設計の中身に書く。
    add("**★乱数を外すのは、入口は M3、出口は M4 です（まこさんが決めた順番）。**"
        "この工事で外すかどうかは、設計の中身（4-0・4-20）に書きます。")
    add("")
    return "\n".join(L)


def build_accept_table(d: dict) -> str:
    """完成の条件の表（承認ゲートが読む欄で作る）。"""
    rows = d.get("完成の条件") or []
    if not rows:
        raise SystemExit("[gen_acceptance] 元データに「完成の条件」がありません（fail-closed）")
    L = []
    add = L.append
    add("")
    add("| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |")
    add("|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        add(f"| {i} | {_esc(r.get('条件'))} | `{_esc(r.get('コマンド'))}` | {_esc(r.get('経路'))} "
            f"| {_esc(r.get('壊し方'))} | `{_esc(r.get('壊すプログラム'))}` | {_esc(r.get('監査確認'))} "
            f"| **{_esc(r.get('いまの状態'))}** |")
    add("")
    return "\n".join(L)


def build_selftest(d: dict) -> str:
    """わざと壊して止まるか試すテストの一覧（壊すプログラムと守る行の対応）。"""
    rows = d.get("完成の条件") or []
    # ★2026-09-29＝壊すプログラムと壊し方の組で まとめる（直す前は壊すプログラムだけで まとめ、「—」の行の
    #   壊し方を1つ目の行の文で代表させた＝#4・#5 に #3 の壊し方が付いた・worklog 20260929 §49 の5）
    by: dict[tuple, list[int]] = {}
    for i, r in enumerate(rows, 1):
        by.setdefault((str(r.get("壊すプログラム") or ""), str(r.get("壊し方") or "")), []).append(i)
    L = []
    add = L.append
    add("**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝まこさんが OK した案の【7-6】。")
    add("")
    add("| 壊すプログラム | 守る行 | 壊し方 |")
    add("|---|---|---|")
    for (prog, brk), idx in sorted(by.items(), key=lambda x: x[1][0]):
        add(f"| `{_esc(prog)}` | {_esc('・'.join('#' + str(i) for i in idx))} | {_esc(brk)} |")
    add("")
    add("**★終了コードは、承認のプログラムが実際に走らせて記録します。**"
        "0 以外だったときだけ、その行を「済」にできます。")
    add("")
    return "\n".join(L)


def build_spec(d: dict) -> str:
    """SPEC と DESIGN_CONTRACT（実物から書き出す）。"""
    dc = d.get("DESIGN_CONTRACT") or {}
    sys.path.insert(0, str(PRIORITY))
    try:
        from verify_design_contract import spec_from_impl
    except Exception as e:
        raise SystemExit(f"[gen_acceptance] 照合の道具を読み込めない: {e}（fail-closed）")
    impl = str(dc.get("impl_file") or "")
    path = SDK / impl
    if not path.exists():
        raise SystemExit(f"[gen_acceptance] impl_file の実物が無い: {path}（fail-closed）")
    # ★2026-10-06（157回目・まこさん「なおしてよい」）＝SPEC は、4-20 の実装の指示のうち impl_file を直すものを
    #   全部 当てた後の中身から作る。直す前は、直す前の実物から作ったので、関数の呼び出しが増える工事では、
    #   当てた後の照合（verify_design_contract.py --diff・承認の前の検査 A12）が必ず食い違い、承認の後に
    #   設計書を作り直して承認を打ち直していた（承認2回）。★直す前の文字がちょうど1か所ずつ無ければ止める（fail-closed）。
    src_text = path.read_text(encoding="utf-8")
    for it in d.get("実装の指示") or []:
        if it.get("対象のファイル") != impl or it.get("種類") != "直した後の文字":
            continue
        old = it.get("直す前の文字") or ""
        # ★2026-10-07（監査 CP63 の修正13・Minor-4）＝直した後の文字が直す前の文字の中に含まれる指示（消すだけの指示）は、
        #   当てる前から直した後の文字が在る。直す前の文字が残り、それが直した後の文字の一部でもなければ、まだ当たっていない。
        if it.get("中身") and src_text.count(it["中身"]) == 1 and (not old or old not in src_text or old in it["中身"]):
            continue                                   # もう当たっている（当てた後に --verify で作り直すとき）
        if not old or src_text.count(old) != 1:
            raise SystemExit(f"[gen_acceptance] SPEC を作るために実装の指示 {it.get('番号')} を当てると、"
                             f"直す前の文字が {src_text.count(old) if old else 0} か所（1か所のはず・fail-closed）")
        src_text = src_text.replace(old, it.get("中身") or "", 1)
    import tempfile as _tf
    with _tf.TemporaryDirectory() as _td:
        _p = Path(_td) / path.name
        _p.write_text(src_text, encoding="utf-8")
        spec = spec_from_impl(str(_p))
    L = []
    add = L.append
    add("**★この節はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**")
    add("")
    add("DESIGN_CONTRACT")
    add("")
    add("```json")
    add(json.dumps(dc, ensure_ascii=False, indent=2))
    add("```")
    add("")
    add("SPEC")
    add("")
    add("```json")
    add(json.dumps({"impl_file": impl,
                    "public_functions": spec["public_functions"],
                    "constants": spec["constants"],
                    "cli_flags": spec["cli_flags"]}, ensure_ascii=False, indent=1))
    add("```")
    add("")
    return "\n".join(L)


def build_checklist(d: dict) -> str:
    """付録の照合の項目（hook の実体から抽出する道具を呼ぶ）。"""
    sys.path.insert(0, str(ROOT / ".claude" / "tools"))
    try:
        from list_banned_words import checklist_items, needs_group2
    except Exception as e:
        raise SystemExit(f"[gen_acceptance] 項目を抽出する道具を読み込めない: {e}（fail-closed）")
    items = checklist_items()
    tgt = (d.get("TARGET") or [""])[0]
    g2 = needs_group2(tgt) or (d.get("形") == "新" and touches_trading(d))   # ★新しい形＝直すファイルのどれかが売買に触れば、群2 を出す
    g1 = [b for g, b in items if g == "群1"]
    g2list = [b for g, b in items if g == "群2"]
    L = []
    add = L.append
    add("**★この節はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。")
    add("")
    # ★2026-09-29＝項目を並べるだけで、照らした結果が1つも無かった（worklog 20260929 §49 の6）。
    #   OK された案の【7-5】（群1 の項目と同じ数・同じ順の答え）を、項目の横に並べる。無い・数が違えば止める。
    ans = d.get("ハード制約の照合")
    if not isinstance(ans, list) or len(ans) != len(g1):
        raise SystemExit(f"[gen_acceptance] OK された案の【7-5】が、群1 の項目 {len(g1)} 件と同じ数の答えの一覧になっていない"
                         f"（いま {len(ans) if isinstance(ans, list) else '無し'}・fail-closed）。1件ずつ、この工事でどう守るかを書く")
    add("| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |")
    add("|---|---|---|")
    for i, (b, a) in enumerate(zip(g1, ans), 1):
        add(f"| {i} | 【群1】{_esc(b[:110])} | {_esc(a)} |")
    add("")
    if g2:
        for b in g2list:
            add(f"- 【群2】{_esc(b[:110])}")
    else:
        add(f"- 【群2・{len(g2list)}件】まとめて非該当"
            "（売買のロジックにも審判にも触れないため）")
    add("")
    return "\n".join(L)


def build_stages(d: dict) -> str:
    """段ごとの表を、§2.2 の逐語から作る（★手で書かない・恒久69番）。

    ★なぜ在るか（2026-09-10）
      まこさんの問い＝「2-2の段ごと指標、閾値、パラメータ、時間足の組み方、使う法則」が
      設計書に1つも入っていなかった。§2.2 にはその全部が書いてあるのに、私は
      「§2.2 の段を、束の枡としてそのまま持つ」の1行しか書かなかった。
      だから、§2.2 の逐語を段ごとに割って、そのまま表にする。

    ★出どころを2か所に書かない＝`gen_s22_map.py` の抽出関数を呼ぶ。
    """
    sys.path.insert(0, str(ROOT / ".claude" / "tools"))
    try:
        from gen_s22_map import read_section, extract
    except Exception as e:
        raise SystemExit(f"[gen_acceptance] §2.2 を抜く道具を読み込めない: {e}（fail-closed）")
    items = [x for x in extract(read_section()) if x[1] == "段"]
    if not items:
        raise SystemExit("[gen_acceptance] §2.2 の段が0件（fail-closed）")

    L: list[str] = []
    add = L.append
    add("**★この表はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`engine_tuner_milestones2.md` の §2.2（レンジ判定の検索方法）を、"
        "`gen_s22_map.py` の抽出関数で読んだもの。**私は1文字も足していません。**")
    add("")
    add("| 段 | 何を選ぶ枠か | 使う法則 | 材料（指標の系統）と時間足 | 値の範囲 |")
    add("|---|---|---|---|---|")
    for sid, _kind, text in items:
        parts = [p.strip() for p in text.split("｜")]
        head = parts[0] if parts else ""
        mid = parts[1] if len(parts) > 1 else ""
        val = parts[2].replace("値＝", "") if len(parts) > 2 else ""
        m = re.match(r"^(\S+)\s*(.*?)（(.+?)）\s*$", head)
        if m:
            waku, laws = m.group(2).strip() or m.group(1), m.group(3)
        else:
            waku, laws = head, "—"
        add(f"| **{sid}** | {_esc(waku)} | {_esc(laws)} | {_esc(mid)} | {_esc(val)} |")
    add("")
    add(f"**段の件数＝{len(items)}件**（§2.2 に在るものを1つも落としていません）。")
    add("")
    return "\n".join(L)


BUILDER = {
    "STAGES": build_stages,
    "MATERIALS": build_materials,
    "LAWS": build_laws,
    "RANKING": build_ranking,
    "CODEREF": build_coderef,
    "RANDOM": build_random,
    "ACCEPT_TABLE": build_accept_table,
    "SELFTEST": build_selftest,
    "SPEC": build_spec,
    "CHECKLIST": build_checklist,
    # ★2026-09-11＝監査の指摘の表（`build_audit` は下で定義するので、名前で後から入れる）
}

_MARK_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def build_audit(d: dict) -> str:
    """この設計書に効いている監査レポートから、指摘を機械で抜き出す（2026-09-11 新設）。

    なぜ在るか（まこさん指示 2026-09-11・逐語）＝「ヌケモレ発生しそうなので、自動生成で対応できない？」

    ★何が起きていたか（実測 2026-09-11）＝私（CC）は監査の指摘を手で読んで報告し、
      **別枠4件（S-1〜S-4）を1行も出さなかった**。Critical 3件と Major 4件だけを出した。
    ★抜き出しは `gen_audit_todo.py` に任せる＝同じ判定を2か所に書き写さない。
      その道具は「表の行をそのまま写す」作りで、件数を丸めない・言い換えない・要約しない。
    ★元データの `audit_report` が空なら、この節は出さない（監査を受けていない設計書のため）。
    ★読めない・抜き出せないときは止まる（fail-closed）＝黙って0件にしない。
    """
    rel = (d.get("audit_report") or "").strip()
    if not rel:
        return ""
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"[gen_acceptance] 監査レポートが無い: {path}（fail-closed）")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import gen_audit_todo as _gat
    except Exception as e:                         # noqa: BLE001
        raise SystemExit(f"[gen_acceptance] 監査の抜き出しの道具を読めない: {e}（fail-closed）")
    items, missing = _gat.collect(str(path))
    if missing:
        raise SystemExit(f"[gen_acceptance] 監査レポートから節を切り出せない: {missing}"
                         "（見出しの書き方が変わった疑い・fail-closed）")
    if not items:
        raise SystemExit(f"[gen_acceptance] 監査レポートから指摘が0件（fail-closed）: {path}")
    L = [f"**出どころ**＝`{rel}` ／ **抜き出し**＝`.claude/tools/gen_audit_todo.py`"
         "（表の行をそのまま写す＝件数を丸めない・言い換えない・要約しない）",
         "",
         "**★この表は機械が作ります。**手で書き換えると `--verify` が止めます。"
         "**私（CC）が監査の件数を数え直しません**（恒久の決まり63番）。",
         "",
         "| 監査の節 | 番号 | 監査に書いてあること（逐語） |",
         "|---|---|---|"]
    for sec, no, body in items:
        L.append(f"| {_esc(sec)} | {_esc(no)} | {_esc(body)} |")
    L.append("")
    L.append(f"**合計 {len(items)} 行。**")
    L.append("")
    L.append("**★直したかどうかは、この表には出ません。**紐づけは監査レポートに書かれていないので、"
             "機械では出せません（私の解釈になります）。**直した記録は `next_step.md` の §6 と "
             "worklog に、1件ずつ書きます。**")
    return "\n".join(L)


BUILDER["AUDITTODO"] = build_audit      # ★定義の後に入れる（BUILDER は上で作っている）


def build_impl(d: dict) -> str:
    """元データの「実装の指示」から、監査結果の修正の指示と同じ6つの欄の節を組み立てる（2026-09-24 新設）。

    ★設計書 impl-instruction-apply-20260924（まこさん承認）。指示が無ければ空の文字列（節ごと出ない）。
    ★欄の並びと見出しは監査結果のテンプレ（`_template.md`）と同じ＝当てる道具が `gen_audit_docs.item_fields` で
      そのまま読める。読み取りは道具の側に1か所（ここには書かない）。
    """
    items = d.get("実装の指示") or []
    if not items:
        return ""
    L = ["**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝元データの `実装の指示`。"
         "当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`"
         "（承認の印と設計書のハッシュ値が合うときだけ当たる）。",
         ""]
    for it in items:
        L.append(f"#### 実装 {it.get('番号')}")
        L.append(f"対象のファイル: {it.get('対象のファイル', '')}")
        L.append(f"直す箇所: {it.get('直す箇所', 'なし')}")
        L.append("直す前の文字:")
        L.append("~~~")
        L.append(str(it.get("直す前の文字") if it.get("直す前の文字") is not None else "なし"))
        L.append("~~~")
        head = (f"案{it['案']} " if it.get("案") else "") + str(it.get("種類", "直した後の文字"))
        L.append(f"{head}:")
        L.append("~~~")
        L.append(str(it.get("中身", "")))
        L.append("~~~")
        L.append(f"根拠の抜き書き: {it.get('根拠の抜き書き', '')}")
        L.append(f"状態: {it.get('状態', '確定')}")
        L.append("")
    return "\n".join(L)


BUILDER["IMPL"] = build_impl            # ★定義の後に入れる（AUDITTODO と同じ）


# ══ 設計のもと（やることの行・まこさんが OK した文）と対応の表（2026-09-29）════════════════════
#   まこさん指示（2026-09-29・逐語）「やることリストなどの設計のもとになるものから設計書作成を自動生成」
#   ★CC は文を写さない。やることの行は m2_todo.json から、まこさんの文は gen_verbatim.py の逐語のファイルから、
#     この道具が写す。
#   ★対応の表＝写した1行ずつに「設計書のどの節・実装の指示の何番で満たすか」。1行でも無ければ書かない（fail-closed）。
#     抜けと誤りは全部 集めて一度に出す（1件ずつ止めない）。

TODO_FIELDS = ("一文", "中身", "触るファイル", "出るもの", "確かめ方", "注意")   # やることの行のうち、写して対応を求める欄
# ★2026-09-29（まこさん指摘「設計書がでたらめ」・worklog 20260929 §84）＝完成の条件を 7-6 から 6-4 へ移したのに、
#   ここに 7-6 が残っていて、対応の表が無い節を指しても止まらなかった。7-6 を外し、6-4（完成の条件）・6-5（監査の指摘）を足した。
#   ★同日 まこさん指示「もともとの構成テンプレに合わせて」で、完成の条件を 7-6 に戻した＝一覧も元に戻した。
FIXED_SECTIONS = {"0-R",                                                          # ★2026-10-12（A-4）＝要件定義との照らし
                  "1", "2-1", "3-1", "3-2", "5", "6-1", "6-2", "6-3", "7-1", "7-2", "7-3", "7-3b",
                  "7-4", "7-5", "7-6", "7-7", "7-8",                            # page が必ず出す節の番号
                  "6-5"}                                                          # ★2026-10-13＝確かめていないこと（新しい形）
NO_MATCH = "対応なし"                                                           # 理由を必ず書く
# ★2026-09-29＝完成の条件を 7-6 から 6-4 へ移した。元データ（ratchet・CC は書けない）の対応の表に残る「7-6」は
#   6-4 として読み、設計書には「6-4」と出す（古い番号を無い節として止めると、元データを直せるまで作り直せない）。
# ★2026-10-13（工事 design-doc-gen-form-20261013）＝案の新しい見出し（番号が無い）を、設計書の節の番号に読み替える
SECTION_ALIAS: dict = {"検査やプログラムを直す工事で書く5つ": "4-22", "新しく入る数字と式の一覧": "4-21", "確かめていないこと": "6-5"}


def _sec(s) -> str:
    """対応の表の節の番号を、いまの番号に揃える（旧 7-6 → 6-4）。"""
    return SECTION_ALIAS.get(str(s), str(s))


def todo_item(no: str) -> dict:
    """やることリスト（m2_todo.json）から、番号の行（「一文」の欄を持つもの）を1つ探す。0件・2件以上は止まる。"""
    hits: list = []

    def walk(x):
        if isinstance(x, dict):
            if str(x.get("番号", "")) == no and "一文" in x:
                hits.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(_load(TODO))
    if len(hits) != 1:
        raise SystemExit(f"[gen_acceptance] やることリストに番号 {no} の行が {len(hits)} 件（1件であること・fail-closed）")
    return hits[0]


def source_rows(d: dict) -> list:
    """写す行＝[(出どころの番号, 文), …]。やることの行は欄ごと（一覧の欄は1つずつ）、逐語は1行ずつ（gen_verbatim.lines）。"""
    src = d.get("設計のもと") or {}
    rows: list = []
    for no in src.get("やることの番号") or []:
        it = todo_item(str(no))
        for k in TODO_FIELDS:
            v = it.get(k)
            if v in (None, "", []):
                continue
            vals = v if isinstance(v, list) else [v]
            for i, x in enumerate(vals, 1):
                rid = f"todo:{no}:{k}" + (f":{i}" if isinstance(v, list) else "")
                rows.append((rid, str(x)))
    for name in src.get("逐語のファイル") or []:
        try:
            rows += gv.lines(str(name))
        except gv.VerbatimError as e:
            raise SystemExit(f"[gen_acceptance] 逐語のファイルが照らしを通らない（{e}・fail-closed）")
    if not rows:
        raise SystemExit("[gen_acceptance] 元データの「設計のもと」が空です（やることの番号か逐語のファイルを1つ以上・fail-closed）")
    return rows


def section_ids() -> set:
    """対応の表に書いてよい節の番号＝page が必ず出す節と、§4 の項目の正本（design_section_map.json）の番号。"""
    m = _load(MAP)
    return FIXED_SECTIONS | {str(x.get("番号")) for x in (m.get("項目") or []) if x.get("節") == "§4"}


def match_problems(d: dict, rows: list) -> list:
    """対応の表の抜けと誤りを全部 集める。戻り＝文の一覧（空なら通る）。"""
    secs = section_ids()
    impl = {str(it.get("番号")) for it in (d.get("実装の指示") or [])}
    by: dict = {}
    bad = []
    for i, r in enumerate(d.get("対応の表") or [], 1):
        rid = str(r.get("出どころ", ""))
        by.setdefault(rid, []).append(r)
        ss = r.get("設計書の節")
        ss = [_sec(s) for s in (ss if isinstance(ss, list) else [ss]) if s not in (None, "")]
        if ss == [NO_MATCH]:
            if not str(r.get("理由", "")).strip():
                bad.append(f"対応の表の {i} 行目（{rid}）＝「{NO_MATCH}」なのに理由が無い")
        elif not ss:
            bad.append(f"対応の表の {i} 行目（{rid}）＝設計書の節が空")
        else:
            miss = [s for s in ss if s not in secs]
            if miss:
                bad.append(f"対応の表の {i} 行目（{rid}）＝設計書に無い節: {'・'.join(miss)}")
        miss_i = [str(x) for x in (r.get("実装の指示") or []) if str(x) not in impl]
        if miss_i:
            bad.append(f"対応の表の {i} 行目（{rid}）＝実装の指示に無い番号: {'・'.join(miss_i)}")
    ids = [rid for rid, _t in rows]
    for rid in ids:
        if rid not in by:
            bad.append(f"写した行 {rid} に、対応の表の行が無い")
    for rid in by:
        if rid not in ids:
            bad.append(f"対応の表の出どころ {rid} は、写した行に無い（打ち間違い・古い番号）")
    return bad


def _wlabel(p) -> str:
    """工事のフォルダの中のパスを「verbatim/<工事名>/…」の文にする（2026-09-30・設計書 point1-proof-20260930 の P-1）。

    ★なぜ＝直す前は作業中の置き場（.claude/state/verbatim/…）をそのまま書いたので、承認でフォルダが
      archive へ移ると、--verify が作り直す 0-1 と食い違い、承認した設計書が必ず ❌ になった（worklog 20260930 §31）。
    """
    parts = Path(p).parts
    return "/".join(parts[len(parts) - 1 - parts[::-1].index("verbatim"):]) if "verbatim" in parts else str(p)


def build_source(d: dict) -> str:
    """設計書 §0-1＝設計のもと（やることの行・逐語の行）と対応の表。対応が1行でも欠ければ止まる。"""
    rows = source_rows(d)
    bad = match_problems(d, rows)
    if bad:
        raise SystemExit("[gen_acceptance] 設計のもとの対応が足りません（fail-closed・全部で "
                         f"{len(bad)} 件）:\n  " + "\n  ".join(bad))
    by: dict = {}
    for r in d.get("対応の表") or []:
        by.setdefault(str(r.get("出どころ")), []).append(r)
    src = d.get("設計のもと") or {}
    # ★2026-09-29＝逐語のファイルごとに、誰の文かを控えの「who」から書く（直す前は全部「まこさんの文」と読める書き方だった
    #   ＝OK をもらった CC の提案も並んでいた・worklog 20260929 §49 の2）。やることの番号が無ければ m2_todo.json を出どころに書かない。
    def _who(n):
        try:
            _t, m = gv.paths(n)
            w = set(json.load(open(m, encoding="utf-8")).get("who") or [])
        except Exception:                                    # noqa: BLE001
            w = set()
        return "まこさんの発言" if w == {"まこさん"} else ("まこさんが OK した CC の文" if w == {"CC"} else "まこさんの発言と CC の文")
    def _rel(n):
        # ★2026-09-29＝置き場は工事ごとのフォルダ（逐語の道具が名前を解決する・文字で組まない）
        return _wlabel(gv.paths(str(n))[0])
    files = "・".join(f"`{_rel(n)}`（{_who(n)}）" for n in (src.get("逐語のファイル") or [])) or "（無し）"
    # ★2026-09-29（まこさん OK・worklog 20260929 §82）＝出どころの表（記録・uuid・時刻・sha256）は「要件のまとめ.md」
    #   （gen_verbatim.py --summary が工事のフォルダに作る）に在るので、ここには参照1行と対応の表だけを出す。
    #   直す前は同じ表を設計書にも出していた（2か所に同じ物）。
    _iter = str(d.get("iter") or "")
    _sm = ""
    try:
        _sm = _wlabel(gv.work_dir(_iter) / gv.SUMMARY_MD) if _iter else ""
    except gv.VerbatimError:
        _sm = ""
    L = [f"**要件のまとめ**＝`{_sm or '（工事のフォルダが無い＝gen_verbatim.py --write --work ' + _iter + ' で作る）'}`"
         "（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）"
         "（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。",
         f"**この設計書が写す逐語のファイル**＝{files}"
         + (f" ／ **やることの番号**＝{'・'.join(str(x) for x in src.get('やることの番号'))}" if src.get("やることの番号") else "")
         + "。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。",
         "",
          f"**写した行＝{len(rows)} 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。",
          ""]
    # ★2026-09-29（読みやすさ）＝1行ずつ並べず、「どの逐語のファイルのどの行が、どの節へ行ったか」の
    #   まとめ1行にする。OK された案の【】の下の行は中身が §4 などにそのまま写り、見出しの外の行（要件の発言・前置き）の
    #   文は要件のまとめ.md に在る＝同じ文を2回 出さない。
    # ★2026-09-30（設計書 point1-one-way-20260930）＝古いやり方の1行ずつの表の分かれ道を消した。
    grouped: dict = {}
    for rid, _text in rows:
        for r in by[rid]:
            ss = r.get("設計書の節")
            ss = [_sec(s) for s in (ss if isinstance(ss, list) else [ss])]
            why = str(r.get("理由", ""))
            key = (rid.split(":")[0], "・".join(ss), why)
            grouped.setdefault(key, []).append(rid.split(":")[-1])
    if grouped:
        L.append("")
        L.append("**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**")
        L.append("")
        L.append("| 逐語のファイル | 行 | 設計書の節 | 理由 |")
        L.append("|---|---|---|---|")
        for (f, sec, why), vs in grouped.items():
            L.append(f"| `{f}` | {vs[0]}〜{vs[-1]}（{len(vs)} 行） | {_esc(sec)} | {_esc(why)} |")
    L.append("")
    return "\n".join(L)


BUILDER["SOURCE"] = build_source        # ★定義の後に入れる（AUDITTODO・IMPL と同じ）


def _repo(p) -> Path:
    """実装の指示の「対象のファイル」を実物の場所に直す（当てる道具 apply_audit_fix.repo_path と同じ決め方）。"""
    p = str(p or "").strip().strip("`")
    if p.startswith("SDK/"):
        return SDK / p[4:]
    for base in (ROOT, SDK):
        if (base / p).exists():
            return base / p
    return (ROOT / p) if (ROOT / p).parent.is_dir() else (SDK / p)


# ★2026-10-07（158回目・まこさん「とにかくすべて完璧に修正して。毎回チェックでミスがあり、やりなおしで膨大な時間がかかるのを改善してほしい」）
#   ＝指標の資料（調べた値の表3つ）を写した先の設定ファイルを直す工事では、設計書を作る前に、「使う」の指標が資料に全部 在るかを照らす。
#   なぜここか＝案を出す前の試し（trial_design.py）も本物の設計書づくりも、この write を通る＝工事の始めに気づける。
#   ★資料と設定ファイルの食い違い（②）はここでは見ない＝ずれを直す工事では、案の時点では必ず食い違うため。②は当てた後の
#     監査に出す前のチェック（pre_audit_check.py の CHECKS）が見る。どの工事でも①②は CHECKS で必ず走る。
_SOURCES_TARGETS = ("scripts/priority_rebuild/observe_config.json", "scripts/priority_rebuild/recipes/search_limits.json")


def indicator_sources_problems(d: dict) -> list:
    """資料を写した先を直す工事なら、check_indicator_sources.py の①を走らせ、食い違いの行を返す（空なら通す）。"""
    if not any(t in _SOURCES_TARGETS for t in (d.get("TARGET") or [])):
        return []
    sys.path.insert(0, str(ROOT / ".claude/tools"))
    import check_indicator_sources as cis
    return cis.check1()


def impl_before_problems(d: dict) -> list:
    """実装の指示の「直す前の文字」が、実物にちょうど1か所在るか（2026-09-29）。

    ★なぜ要るか＝直す前の文字は CC が実物を見て書く（Bash で道具のファイルを別の所へ写す道は土台ゲートが止める）。
      写し間違いは、当てる道具が承認の後に初めて見つけていた。設計書を作る時点で機械が照らす。
    ★通すもの＝①ちょうど1か所 ②0か所で、直した後の文字（足す文字なら 直す前＋足す文字）がもう在る＝当て終わっている
      ③直す前の文字が「なし」の新しいファイルで、まだ無い（または中身がもう在る）。状態が「確定」でない件は見ない。
    """
    bad = []
    for it in d.get("実装の指示") or []:
        if str(it.get("状態", "確定")) != "確定":
            continue
        no = it.get("番号")
        before = it.get("直す前の文字")
        body = str(it.get("中身") or "")
        path = _repo(it.get("対象のファイル"))
        if before is None:
            bad.append(f"実装 {no}: 直す前の文字が無い")
            continue
        if str(before).strip() == "なし":
            if path.exists() and body not in path.read_text(encoding="utf-8"):
                bad.append(f"実装 {no}: 新しいファイルのはずが、別の中身でもう在る（{path}）")
            continue
        if not path.exists():
            bad.append(f"実装 {no}: 対象のファイルが無い（{path}）")
            continue
        cur = path.read_text(encoding="utf-8")
        n = cur.count(str(before))
        done = (str(before) + body) if it.get("種類") == "足す文字" else body
        if n == 1 or (n == 0 and body and done in cur):
            continue
        # ★2026-10-06（工事 m2c15-hidden-params-20261004 の件49・50）＝行を消す直し（直した後の文字が空）は、当てた後に
        #   「直した後の文字が実物に在る」で見分けられない。当てる道具の記録（applied_fixes.json・名前 design:<iter>）に在れば当て終わり。
        if n == 0 and not body.strip() and _applied_in_record(d.get("iter"), no):
            continue
        bad.append(f"実装 {no}: 直す前の文字が {path.name} に {n} か所（ちょうど1か所であること）")
    return bad


def _applied_in_record(iter_name, no) -> bool:
    """当てる道具の記録（SDK/.claude/audits/applied_fixes.json）に、この工事（design:<iter>）のその番号が在るか。"""
    p = SDK / ".claude" / "audits" / "applied_fixes.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:                                        # noqa: BLE001
        return False
    key = f"design:{iter_name}"
    return any(str(x.get("report", "")) == key and str(x.get("num", "")) == str(no)
               for x in (d.get("applied") or []) if isinstance(x, dict))


def build(kind: str, d: dict) -> str:
    """囲みの中身を作る。置き換えない目印が残ったら止める（fail-closed の3つ目）。"""
    body = BUILDER[kind](d)
    left = sorted(set(_MARK_RE.findall(body)))
    if left:
        raise SystemExit(f"[gen_acceptance] 置き換えられない目印が残っている: {left}（fail-closed）")
    # ★2026-09-29（worklog 20260929 §82）＝「★この節はプログラムが作ります」の断り（設計書に6回）は、見出しの直下の
    #   印（_tag）に置き換えた。囲みの中からは外す（作る側と照らす側の両方がここを通るので、--verify も同じ形で照らす）。
    # ★空の行は詰めない＝IMPL の囲みの中のコード（直す前の文字）は1文字も変えてはいけない（当てる道具が実物と照らす）。
    return _STAMP_RE.sub("", body)


def laws_count_ok() -> tuple[bool, str]:
    """法則ファイルの件数と、書き出した表の行数が同じか（fail-closed の4つ目）。"""
    law = _load(LAWS)
    n = len([x for x in (law.get("法則") or []) if isinstance(x, dict)])
    body = build_laws({})
    rows = [ln for ln in body.splitlines()
            if ln.startswith("| **") and "番号" not in ln]
    return (len(rows) == n, f"法則ファイル {n}件 ／ 表 {len(rows)}行")


# ══ 設計書を組み立てる（7つの節）═════════════════════════════════════

def section4(d: dict) -> str:
    """§4（設計の中身）を、項目の正本（design_section_map.json）の順に組み立てる。

    ★なぜ正本を別に持つか（2026-09-10）
      まこさん指摘＝「まるごと設計のコアの部分が無い状態だよね」「思考が支離滅裂で
      その場しのぎすぎるんだよ」。私が §4 の項目を思いつきで足し、4回とも まこさんの
      問いで「出どころに在るのに項目に入っていないもの」が出た。
      だから項目は map に固定し、この関数は**並べるだけ**にする。

    fail-closed（黙って通さない）
      6. 項目の正本が読めない → 止まる
      7. 段が「必ず」の項目が、元データに無い（または空） → 止まる
      8. 段が「条件」で「当たらない」と書いたのに、理由が無い → 止まる
      9. 段が「省ける」で非該当なのに、理由と出どころが無い → 止まる
    """
    m = _load(MAP)
    items = [x for x in (m.get("項目") or []) if x.get("節") == "§4"]
    if not items:
        raise SystemExit(f"[gen_acceptance] §4 の項目が正本に無い: {MAP}（fail-closed 6）")

    # ★2026-09-10（まこさん決定・逐語「上記の項目順に修正でよい」）＝読む順に並べ替える。
    #   まこさん指摘＝「設計書の項目の順番が支離滅裂。冒頭は、目的とか概要、要件などで固めて、
    #   その後、全体の設計内容構造とかで、4-A この節に何を書いたか（一覧）などは後半でよいのでは？」。
    #   ★並び順の正本は MAP の「_§4の並び順」＝項目を2か所に書かない。
    #   fail-closed 10＝並び順に載っていない項目が在れば止める（項目を減らして出さないため）。
    order = m.get("_§4の並び順") or []
    if order:
        known = {str(x.get("番号")) for x in items}
        missing = [x for x in known if x not in order]
        ghost = [x for x in order if x not in known]
        if missing:
            raise SystemExit(
                "[gen_acceptance] 並び順に載っていない項目が在ります（fail-closed 10）＝"
                + "・".join(sorted(missing))
                + "\n  ★項目を減らして出さないための検査です。")
        if ghost:
            raise SystemExit(
                "[gen_acceptance] 並び順に、実在しない項目が在ります（fail-closed 10）＝"
                + "・".join(ghost))
        items = sorted(items, key=lambda x: order.index(str(x.get("番号"))))
    body = d.get("設計の中身") or {}
    # ★2026-10-13（工事 design-doc-gen-form-20261013）＝「形」が「新」の項目は、新しい形の設計書にだけ出す
    new = d.get("形") == "新"
    if not new:
        items = [x for x in items if x.get("形") != "新"]

    def _nm(it: dict) -> str:
        return str(it.get("新しい形の名前") or it.get("名前")) if new else str(it.get("名前"))

    L: list[str] = []
    add = L.append
    add(("項目の正本＝`design_section_map.json`（3つの出どころを、全部 引き受ける形。件数は、検算 `gen_design_sections.py --check` が出す）。"
         if new else
         "項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。") +
        "各項目の「何を書くか」の説明は正本に在り、設計書には出しません。")
    add("")
    # ★2026-09-10（まこさん指摘「4-A この節に何を書いたか（一覧）などは後半でよいのでは？」）
    #   ＝一覧は管理のための表なので、節の最後に出す。ここでは中身だけ作って、後で足す。
    #   ★2026-09-29 に一度 消したが、同日 まこさん指示「もともとの構成テンプレに合わせて」で戻した。
    tbl: list[str] = []
    tadd = tbl.append
    tadd("### 4-A この節に何を書いたか（一覧）")
    tadd("")
    tadd(_wtag("自動", "項目の正本と、OK された案・やることの表の有無"))
    tadd("| 番号 | 段 | 項目 | 書いたか |")
    tadd("|---|---|---|---|")
    miss_must: list[str] = []
    miss_why: list[str] = []
    na: list[str] = []
    for it in items:
        no = str(it.get("番号"))
        step = str(it.get("段", ""))
        if new and it.get("種類①では必ず") and work_kind(d) == 1:
            step = "必ず"
        name = _esc(_nm(it))
        got = body.get(no)
        if no == "4-20" and (d.get("実装の指示") or []):
            state = f"書いた（実装の指示 {len(d['実装の指示'])} 件・プログラムが作る）"
        elif isinstance(got, dict) and got.get("非該当"):
            state = f"非該当（{_esc(got['非該当'])}）"
            na.append(f"{no} {_nm(it)}＝{got['非該当']}")
            if step == "必ず":
                miss_must.append(no)
            if not str(got["非該当"]).strip():
                miss_why.append(no)
        elif got:
            state = "書いた"
        else:
            state = "**未記入**"
            if step == "必ず":
                miss_must.append(no)
            else:
                miss_why.append(no)
        tadd(f"| {no} | {step} | {name} | {state} |")
    tadd("")

    if miss_must:
        raise SystemExit(
            "[gen_acceptance] 段が「必ず」の項目が埋まっていません（fail-closed 7）＝"
            + "・".join(miss_must)
            + "\n  ★「必ず」は非該当を認めません。どの工事でも書ける項目だからです。")
    if miss_why:
        raise SystemExit(
            "[gen_acceptance] 書いていない項目に、理由が在りません（fail-closed 8・9）＝"
            + "・".join(miss_why)
            + '\n  ★形＝{"非該当": "理由（出どころ）"} を元データの「設計の中身」に書いてください。')

    for it in items:
        no = str(it.get("番号"))
        got = body.get(no)
        if isinstance(got, dict) and got.get("非該当"):
            continue                                       # ★2026-09-29＝非該当は見出しを立てず、下の1行に畳む
        add(f"### {no} {_nm(it)}")
        add("")
        # ★2026-09-29＝「この項目に書くこと」の説明文（21回）は出さない（正本 design_section_map.json に在る）
        if no == "4-20" and (d.get("実装の指示") or []):
            # ★2026-09-24（設計書 impl-instruction-apply-20260924）＝4-20 は囲み IMPL（プログラムが作る）。置き場は §4 の中（テンプレどおり）
            add(_tag("自動", "まこさんが OK した案の【4-20】＝コードの文字は CC の手書き"))
            add(_begin("IMPL", _h(build("IMPL", d))))
            add(build("IMPL", d))
            add(_end("IMPL"))
            add("")
            continue
        add(_wtag("手書き" if no == "4-19" else "自動",
                  "やることの表の「4-19 通しの例」" if no == "4-19"
                  else f"まこさんが OK した案の【{dict((v, k) for k, v in SECTION_ALIAS.items()).get(no, no) if new else no}】"))
        if isinstance(got, dict):
            for line in got.get("本文") or []:
                add(line)
            add("")
            blk = got.get("囲み")
            if blk:
                add(_begin(blk, _h(build(blk, d))))
                add(build(blk, d))
                add(_end(blk))
                add("")
        elif isinstance(got, list):
            # ★本文は行の一覧で持つ（1行ずつ出す。まとめて str() にすると
            #   Python の一覧の形（角括弧と引用符）がそのまま設計書に出る）。
            if new and no == "4-0":                 # ★概要の1文目は、4-0 の冒頭に出す（やることの表の F-1・設計書の監査 CP77）
                for line in _auto_rows(no, got, d):
                    add(line)
            for line in got:
                add(str(line))
            add("")
            if new and no != "4-0":
                for line in _auto_rows(no, got, d):
                    add(line)
        else:
            add(str(got))
            add("")
    if na:
        add(_tag("自動", "まこさんが OK した案の【番号】の「非該当＝」の後ろの文と、項目の正本の名前"))
        add("**非該当の項目（理由と出どころ）**＝" + "／".join(_esc(x) for x in na))
        add("")
    # ★一覧は節の最後（まこさん指摘 2026-09-10「4-A この節に何を書いたか（一覧）などは後半でよいのでは？」）
    L.extend(tbl)
    return "\n".join(L)


def page(d: dict) -> str:
    """7つの節の設計書を組み立てる（囲みの外＝元データの文をそのまま置く）。"""
    L: list[str] = []
    add = L.append
    # ★2026-09-24（設計書 impl-instruction-apply-20260924）＝「実装の指示」は一覧（[]）でしか受けない（fail-closed）。
    #   散文で書いた指示をプログラムが解析する形にしない（設計書 3-1 の3）。
    if "実装の指示" in d and not isinstance(d.get("実装の指示"), list):
        raise SystemExit("[gen_acceptance] 元データの「実装の指示」が一覧（[]）の形ではありません（fail-closed）。")
    if any(not isinstance(it, dict) for it in (d.get("実装の指示") or [])):
        raise SystemExit("[gen_acceptance] 元データの「実装の指示」の中に、1件ずつの形（{…}）でないものが在ります（fail-closed）。")
    # ★2026-09-30（設計書 point2-design-to-impl-20260930・2点目）＝直すファイル（TARGET・NEW_FILE）が在るのに、
    #   実装の指示（4-20）を「非該当」にした設計書は作らない（実装を CC が手で書く道を残さない）。
    if (d.get("TARGET") or d.get("NEW_FILE")) and not (d.get("実装の指示") or []):
        raise SystemExit("[gen_acceptance] 直すファイル（TARGET・NEW_FILE）が在るのに、実装の指示（4-20）が0件です"
                         "（fail-closed・2点目）。案の【4-20】に、当てる道具が当てる形で実装を書いてください。")
    _ib = impl_before_problems(d)
    if _ib:
        raise SystemExit("[gen_acceptance] 実装の指示の直す前の文字が、実物と合いません（fail-closed・全部で "
                         f"{len(_ib)} 件）:\n  " + "\n  ".join(_ib))
    _src_ng = indicator_sources_problems(d)
    if _src_ng:
        raise SystemExit("[gen_acceptance] 指標の資料を写した先を直す工事なのに、「使う」の指標が資料に全部は在りません（fail-closed・"
                         f"全部で {len(_src_ng)} 件）＝先に資料に行を足してください:\n  " + "\n  ".join(_src_ng))
    add(f'<!-- ARC iter="{d["iter"]}" -->')
    add("")
    add(f"# 設計書｜{d['設計書の題']}")
    add("")
    add("TARGET: " + ", ".join(d.get("TARGET") or []))
    if d.get("NEW_FILE"):
        add("NEW_FILE: " + ", ".join(d["NEW_FILE"]))
    if d.get("MODEL"):
        add("MODEL: " + ", ".join(d["MODEL"]))
    new = d.get("形") == "新"                           # ★2026-10-13＝新しい形の設計書か
    if new:
        add("工事の種類: " + KIND_TEXT[work_kind(d)] + "（直すファイルの一覧から、プログラムが決めた）")
        # ★概要の1文目を、設計書の題の下にも写す（やることの表の F-1・設計書の監査 CP77）
        add("この工事が解く問題: " + str(d.get("何を作るか") or "").split("\n")[0] + "（§1 概要の1文目を、プログラムが写した）")
    add("")
    # ★2026-09-29＝直す前は「engine_tuner_milestones2.md の §2.2」の固定の文で、どの工事でも出た（worklog 20260929 §42）。
    #   設計のもと（やることの番号・逐語のファイル）から作る。
    _src = d.get("設計のもと") or {}
    _req = []
    if _src.get("やることの番号"):
        _req.append("やることリスト `m2_todo.json` の " + "・".join(str(x) for x in _src["やることの番号"]) + " 番")
    if _src.get("逐語のファイル"):
        _req.append("逐語のファイル " + "・".join(f"`{n}`" for n in _src["逐語のファイル"]))
    add("REQUIREMENTS: 設計のもと（下の §0-1）＝" + ("／".join(_req) or "（無し）") + "。")
    add("")
    # ★2026-09-13（98回目・監査 cp36 の M-7＝next_step §6 の179番①）＝直す前は「未承認・実装はまだ1行も
    #   入れていません」と固定で書いていた。承認②（実装の後の作り直し）でも同じ文が出るので嘘になっていた。
    #   承認の状態は印（acceptance.approved・design_approved.json）が、実装の状態は 7-6 の表が正本＝そこを指す。
    add("**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。**"
        "**実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。")
    add("")
    # ★2026-09-29＝直す前は「手で書いたのは5つだけです」の固定の文で、嘘だった（4-0〜4-19・完成の条件ほかも手書き・§49 の1）。
    # ★2026-09-30（設計書 point1-one-way-20260930-2）＝工事のフォルダの1本だけ（元データの JSON の文の分かれ道を消した）。
    add(f"**★この設計書は、工事のフォルダ `{_wlabel(gv.work_dir(WORK))}/` からプログラムが組み立てます。**"
        "（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）"
        f"CC が手で書いたのは、{TODO_MD} の「手書きの項目」の{len(_hk(d))}つだけです＝{'・'.join(_hk(d))}。"
        "それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。"
        f"作り直し＝`python3 .claude/tools/gen_acceptance.py --work {WORK} --write`。検出＝`--work {WORK} --verify`。")
    add("")

    # ★2026-10-12（170回目・まこさん「OK」＝直し方の案 A-1・A-4）＝要件定義と工事の流れ（固定で載せる文）と、
    #   要件定義とこの工事の照らしの表を、設計書の上部に載せる。
    #   まこさん指示（2026-10-12）＝要件定義を設計書の上部に固定で毎回 載せ、要件定義どおりに個別の工事が対応できているかを確かめる。
    #   載せる工事＝OK された案に【0-R】が在る工事と、工事名の日付が 2026-10-12 以降の工事
    #   （それより前に承認した設計書は、作り直しで中身が変わらないように、載せない）。
    if d.get("要件定義との照らし") or core_required(d.get("iter", "")) or new:
        add("## 要件定義と工事の流れ（固定・毎回 載せる・消さない）")
        add("")
        add(_tag("自動", "正本 .claude/rules/core_requirements.md からプログラムが写した（まこさん指示 2026-10-12）"))
        for _ln in gcr.embed_lines():
            add(_ln)
        add("")
        if new:
            # ★2026-10-13＝新しい形の設計書では、CC の判定の表をやめ、プログラムが作る索引を出す
            L.extend(_index_lines(d))
            add("")
    if (d.get("要件定義との照らし") or core_required(d.get("iter", ""))) and not new:
        add("### 0-R 要件定義との照らし（この工事が、上の要件定義に合っているか）")
        add("")
        add(_tag("自動", "左の2列は正本・右の3列は まこさんが OK した案の【0-R】"))
        add("| # | 要件（正本から） | この工事は関わるか | 合っているか | 根拠 |")
        add("|---|---|---|---|---|")
        _hr = d.get("要件定義との照らし") or {}
        for _no, _name in gcr.requirement_items():
            _r = _hr.get(_no)
            if not _r:
                raise SystemExit(f"[gen_acceptance] 要件定義の {_no}（{_name}）との照らしが、OK された案の【0-R】に無い（fail-closed）")
            add(f"| {_no} | {_name} | {_r['関わるか']} | {_r['合っているか']} | {_r['根拠']} |")
        add("")

    add("## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）")
    add("")
    # ★2026-09-29（まこさんが OK した提案の7行目「「まこさんの決定」を私が手で書く口は閉じます。」）
    #   ＝元データに「まこさんの決定」の欄が在れば止める。まこさんの文は、下の 0-1 に道具が逐語のファイルから写す。
    if d.get("まこさんの決定"):
        raise SystemExit("[gen_acceptance] 元データに「まこさんの決定」の欄が在ります（fail-closed）＝CC が手で書く口は閉じました。"
                         "まこさんの文は gen_verbatim.py で逐語のファイルにし、元データの「設計のもと」の「逐語のファイル」に名前を書く。")
    add(f"**見出しの直下の印＝［手書き］＝CC が {TODO_MD} の「手書きの項目」に書いた文／"
        "［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**")
    add("")
    # ★2026-09-29（worklog §58）＝見出しは元データの「設計のもと」から決める（やることの番号が無いのに「やることの行」と書かない）
    _todo = bool((d.get("設計のもと") or {}).get("やることの番号"))
    add("### 0-1 設計のもと（" + ("やることの行と、" if _todo else "") + "まこさんの発言と、まこさんが OK した文・プログラムが写しました）")
    add("")
    add(_wtag("自動", "逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）"))
    add(_begin("SOURCE", _h(build("SOURCE", d))))
    add(build("SOURCE", d))
    add(_end("SOURCE"))
    add("")

    add("## 1｜概要")
    add("")
    add(_wtag("手書き", "やることの表の「§1 概要」"))
    add(d["何を作るか"])
    add("")

    add("## 2｜背景と範囲")
    add("")
    if new:
        L.extend(_sec2_new(d))
    add("### 2-1 いまの状態（走らせて測ったもの）")
    add("")
    add(_tag("手書き", "何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」"))
    add(_tag("自動", "結果＝道具がコマンドを走らせて入れた"))
    add("| 何を測ったか | コマンド | 読み方 | 結果 |")
    add("|---|---|---|---|")
    # ★2026-09-17（設計書 acceptance-results-from-commands-20260917・まこさん「手書きはするな」）
    #   ＝結果の欄は、道具がコマンドを走らせて入れる。直す前は元データの「結果」を私が手で写し、
    #     そのまま載せていた（コマンドと結果が合わない行を書いた＝worklog 20260917 §25 の前）。
    #   ★走らせるのは読むだけのコマンドだけ＝元データに書いたコマンドを道具が走らせると、
    #     Bash の土台ゲートを通らずに書き込む道になるため。
    #   ★区切りは「 | 」（前後に空白）＝grep の `a\|b` の縦棒は区切りにしない。
    def _measure(cmd: str) -> str:
        import shlex as _shlex
        read_heads = {"grep", "wc", "sed", "awk", "find", "sort", "head", "tail", "cut", "uniq", "tr", "cat"}
        git_subs = {"diff", "log", "show", "status", "ls-files", "grep"}
        py_tools = {"run_breaks.py", "tidy_next_step.py", "gen_hook_list.py", "verify_design_contract.py"}
        py_flags = {"--verify", "--count-targets", "--selftest", "--parse-only", "--lint-expect",
                    "--check", "--diff", "--design"}
        for bad in (">", "<", ";", "&", "`", "$(", "\n"):
            if bad in cmd:
                raise SystemExit(f"[gen_acceptance] 「なぜ作るか」のコマンドに「{bad}」が在ります"
                                 f"（読むだけのコマンドに限る・fail-closed）: {cmd}")
        for seg in cmd.split(" | "):
            try:
                toks = _shlex.split(seg)
            except ValueError as e:
                raise SystemExit(f"[gen_acceptance] コマンドを読めない（{e}・fail-closed）: {seg}")
            if not toks:
                raise SystemExit(f"[gen_acceptance] 空のコマンドの区切りが在る（fail-closed）: {cmd}")
            head = toks[0]
            why = ""
            if head in read_heads:
                if head == "sed" and any(t.startswith("-i") or t.startswith("--in-place") for t in toks[1:]):
                    why = "sed の -i（書き込み）"
                elif head == "find" and any(t in ("-exec", "-execdir", "-delete", "-ok", "-okdir",
                                                  "-fprint", "-fprintf", "-fls") for t in toks[1:]):
                    why = "find の書き込み・実行の旗"
                elif head == "awk" and "system(" in seg:
                    why = "awk の system("
            elif head == "git":
                if len(toks) < 2 or toks[1] not in git_subs:
                    why = "git の読むだけでない使い方"
            elif head == "python3":
                args = toks[1:]
                if not args or args[0].rsplit("/", 1)[-1] not in py_tools:
                    why = "決まった道具でない python3"
                elif any(t.startswith("-") and t not in py_flags for t in args[1:]):
                    why = "決まった読むだけの旗でない"
                elif not any(t in py_flags for t in args[1:]):
                    why = "読むだけの旗が無い python3"
            else:
                why = f"読むだけのコマンドの一覧に無い先頭の語「{head}」"
            if why:
                raise SystemExit(f"[gen_acceptance] 「なぜ作るか」のコマンドを走らせません＝{why}"
                                 f"（読むだけのコマンドに限る・fail-closed）: {cmd}")
        try:
            r = subprocess.run(["bash", "-c", cmd], cwd=str(ROOT), capture_output=True,
                               text=True, timeout=120)
        except subprocess.TimeoutExpired:
            raise SystemExit(f"[gen_acceptance] 「なぜ作るか」のコマンドが120秒で終わらない（fail-closed）: {cmd}")
        out = (r.stdout or "").strip() or (r.stderr or "").strip()
        lines = out.splitlines()
        text = " ⏎ ".join(lines)
        if len(text) > 500:
            text = text[:500] + f"…（出力 {len(lines)} 行のうち先頭 500 文字）"
        return f"{text}（終了コード {r.returncode}）"

    for r in d.get("なぜ作るか") or []:
        if "結果" in r:
            raise SystemExit("[gen_acceptance] 元データの「なぜ作るか」に「結果」の欄が在ります（fail-closed）。"
                             "結果は道具がコマンドを走らせて入れます（まこさん「手書きはするな」）。"
                             f"「読み方」（数字なし）に書き替えてください: {r.get('何を測ったか')}")
        yomi = str(r.get("読み方") or "")
        if re.search(r"[0-9０-９]", yomi):
            raise SystemExit("[gen_acceptance] 「なぜ作るか」の「読み方」に数字が在ります（fail-closed）。"
                             f"数字はコマンドの出力にだけ出します: {yomi}")
        add(f"| {_esc(r['何を測ったか'])} | `{_esc(r['コマンド'])}` | {_esc(yomi)} | {_esc(_measure(str(r['コマンド'])))} |")
    add("")
    # ★2026-09-29（まこさん OK「それで一旦作ってみて」・worklog 20260929 §82 の骨組み）
    #   ＝売買のロジックに触らない工事では、2-2〜2-4 は3つとも非該当なので、見出しを3つ立てずに1つに畳む。
    #     囲み（MATERIALS・RANKING・RANDOM）は --verify が照らすので、中身は今までどおり出す。
    if touches_trading(d):
        add("### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）")
        add("")
        add(_tag("自動", "印のファイル・型の表・格子と範囲"))
        add(_begin("MATERIALS", _h(build("MATERIALS", d))))
        add(build("MATERIALS", d))
        add(_end("MATERIALS"))
        add("")
        add("### 2-3 成績表に載っている本数")
        add("")
        add(_tag("自動", "成績表"))
        add(_begin("RANKING", _h(build("RANKING", d))))
        add(build("RANKING", d))
        add(_end("RANKING"))
        add("")
        add("### 2-4 いま乱数を使っている場所")
        add("")
        add(_tag("自動", "実物のコード"))
        add(_begin("RANDOM", _h(build("RANDOM", d))))
        add(build("RANDOM", d))
        add(_end("RANDOM"))
        add("")
    else:
        add("### 2-2 探す材料・成績表・乱数（2-2〜2-4＝この工事では非該当）")
        add("")
        add(_tag("自動", "TARGET と NEW_FILE から非該当を決めた"))
        for _k in ("MATERIALS", "RANKING", "RANDOM"):
            add(_begin(_k, _h(build(_k, d))))
            add(build(_k, d))
            add(_end(_k))
        add("")

    add("## 3｜目標と、やらないこと")
    add("")
    if new:
        L.extend(_goal_lines(d))
    add("### 3-1 やらないこと（1件ずつ・理由と出どころ）")
    add("")
    add(_wtag("自動", "やることの表の「## やらないこと」の表から、同じ件数で、プログラムが写した") if new
        else _wtag("手書き", "やることの表の「3-1 やらないこと」"))
    add("| # | やらないこと | 理由 | 出どころ |")
    add("|---|---|---|---|")
    for i, r in enumerate(d["やらないこと"], 1):
        add(f"| {i} | {_esc(r['中身'])} | {_esc(r['理由'])} | {_esc(r['出どころ'])} |")
    add("")
    add("### 3-2 決めてほしいこと")
    add("")
    add(_tag("手書き", "やることの表の「3-2 決めてほしいこと」"))
    add("| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |")
    add("|---|---|---|---|")
    for i, r in enumerate(d.get("決めてほしいこと") or [], 1):
        add(f"| {i} | {_esc(r['中身'])} | {_esc(r['私の案'])} | {_esc(r.get('出どころ', ''))} |")
    if not d.get("決めてほしいこと"):
        add("| — | 無し（やることの表の「決めてほしいこと」が「無し」か空） | — | — |")
    add("")

    add("## 4｜設計の中身")
    add("")
    add(section4(d))
    add("")

    add("## 5｜決めたことと理由・捨てた案")
    add("")
    add(_wtag("自動", "まこさんが OK した案の【5】"))
    add("| # | 決めたこと | 理由 | 捨てた案 |")
    add("|---|---|---|---|")
    for i, r in enumerate(d.get("決めたことと理由") or [], 1):
        add(f"| {i} | {_esc(r['決めたこと'])} | {_esc(r['理由'])} | {_esc(r['捨てた案'])} |")
    add("")

    add("## 6｜テストとリスクと見積もり")
    add("")
    add("### 6-1 わざと壊して止まるか試すテスト")
    add("")
    add(_wtag("自動", "まこさんが OK した案の【7-6】の壊し方の欄"))
    add(_begin("SELFTEST", _h(build("SELFTEST", d))))
    add(build("SELFTEST", d))
    add(_end("SELFTEST"))
    add("")
    add("### 6-2 リスク")
    add("")
    add(_tag("自動", "まこさんが OK した案の【6-2】"))
    add("| # | リスク | どうするか |")
    add("|---|---|---|")
    for i, r in enumerate(d.get("リスク") or [], 1):
        add(f"| {i} | {_esc(r['中身'])} | {_esc(r['どうするか'])} |")
    add("")
    add("### 6-3 見積もり")
    add("")
    add(_tag("自動", "まこさんが OK した案の【6-3】"))
    add("| 何 | 見込み | 根拠 |")
    add("|---|---|---|")
    for r in d.get("見積もり") or []:
        add(f"| {_esc(r['何'])} | {_esc(r['見込み'])} | {_esc(r['根拠'])} |")
    add("")
    add("**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**")
    add("")
    _audit = build_audit(d)
    # ★2026-10-13＝新しい形の設計書では、この設計書が受けた設計書の監査の結果ファイルを、プログラムが探して出す
    #   （直す前は、監査の修正を入れた版にも「監査の指摘を受けていない」と出た＝記録 20261013 §12）。
    _rep = _design_audit_reports(d) if new else []
    if not _audit and _rep:
        add("**6-4 この設計書が受けた設計書の監査**＝" + "・".join(f"`{p}`" for p in _rep)
            + "（結果ファイルの名前から、プログラムが見つけた。修正の指示は、結果ファイルの8番の節に在る）")
        add("")
    if not _audit and not _rep:
        add("**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）")
        add("")
    if _audit:
        add("### 6-4 この設計書に効いている監査の指摘（★機械が抜き出します）")
        add("")
        add(_tag("自動", "監査レポートの修正の指示"))
        add(_begin("AUDITTODO", _h(_audit)))
        add(_audit)
        add(_end("AUDITTODO"))
        add("")

    if new:
        L.extend(_unverified_lines(d))
    add("## 7｜付録（hook が求める項目）")
    add("")
    add("### 7-1 深掘り4点")
    add("")
    add(_wtag("自動", "まこさんが OK した案の【7-1】"))
    if new:
        add("この工事が解く問題＝" + str(d["何を作るか"]).split("\n")[0] + "（プログラムが、§1 概要の1文目を写した）")
        add("")
    add("**① 真因（root cause）**＝" + d["真因"])
    add("")
    add("**② 期待値分解**＝" + d["期待値分解"])
    add("")
    add("**③ root か symptom か**＝" + d["root か symptom か"])
    add("")
    add("**④ ベースアップ**＝" + d["ベースアップ"])
    add("")
    add("### 7-2 ★疑似シミュ由来の固定値ゼロ宣言")
    add("")
    add(_tag("自動", "まこさんが OK した案の【7-2】"))
    add(d["固定値ゼロ宣言"])
    add("")
    add("### 7-3 変更の単位（H16）")
    add("")
    add(_tag("自動", "まこさんが OK した案の【7-3】"))
    add(d["変更の単位"])
    add("")
    add("### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）")
    add("")
    # ★2026-09-29＝恒久の決まり §1 は engine_tuner の要件の照合。売買のロジックに触らない工事では非該当（worklog §42）
    if new:
        L.extend(_forbidden_new(d))
    elif not touches_trading(d):
        add(_tag("自動", "TARGET と NEW_FILE から非該当を決めた"))
        add(NONTRADE)
    else:
        add(_tag("自動", "左の2列は要件の正本・右の2列は まこさんが OK した案の【7-3b】"))
        add("**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**"
            "出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。"
            "**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。")
        add("")
        add("| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |")
        add("|---|---|---|---|")
        _hantei = d.get("作ってはいけないものとの照合") or {}
        for _no, _name in forbidden_items():
            _r = _hantei.get(_no)
            if not _r:
                raise SystemExit(f"[gen_acceptance] 「作ってはいけないもの」の {_no} 番との照合が"
                                 "元データに無い（fail-closed・恒久の決まり §1）")
            add(f"| {_no} | {_esc(_name)} | **{_esc(_r['当たるか'])}** | {_esc(_r['理由'])} |")
    add("")
    add("### 7-4 塞げないもの")
    add("")
    add(_tag("自動", "まこさんが OK した案の【7-4】"))
    add("| 問い | 塞げないこと |")
    add("|---|---|")
    for r in d.get("塞げないもの") or []:
        add(f"| **{_esc(r['問い'])}** | {_esc(r['塞げないこと'])} |")
    add("")
    add("### 7-5 §4.6 ハード制約の照合")
    add("")
    add(_wtag("自動", "項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】"))
    add(_begin("CHECKLIST", _h(build("CHECKLIST", d))))
    add(build("CHECKLIST", d))
    add(_end("CHECKLIST"))
    add("")
    add("### 7-6 完成の条件")
    add("")
    add(_wtag("自動", "条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く"))
    add("**★状態は全部「未着手」です。「済」にするのはプログラムです**"
        "（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。"
        "**自分で「直った」と判定しません**（恒久の決まり64番）。")
    add("")
    add(_begin("ACCEPT_TABLE", ""))
    add(build("ACCEPT_TABLE", d))
    add(_end("ACCEPT_TABLE"))
    add("")
    # ★2026-10-20（ToDo の26番・監査 CP78 の Minor C）＝検査が読む「行が無いやることの番号と、その理由」の行を、設計書にも写す
    #   （直す前は、検査が読むのに設計書に出ず、監査が理由を見られなかった）。新しい形だけ（案の文は新しい形にだけ在る）
    _excuse = [ln.strip() for ln in (d.get("案の文") or {}).get("7-6") or [] if ln.strip().startswith("- 行が無いやることの番号")] if new else []
    if _excuse:
        add(_wtag("自動", "まこさんが OK した案の【7-6】の、行が無いやることの番号と理由の行"))
        for ln in _excuse:
            add(ln)
        add("")
    # ★2026-09-09（設計書 gen-acceptance-tool-20260909）＝見出しに SPEC の語を入れない。
    #   なぜ＝突き合わせの道具（verify_design_contract.extract_block）は、見出しに語が在れば
    #   それを目印として数え、その後ろの最初の囲みを読む。見出しに SPEC と書くと、
    #   すぐ後ろの DESIGN_CONTRACT の囲みを SPEC として読み、齟齬 66件の誤報が出た（実測）。
    #   ★目印は、下の単独の行（DESIGN_CONTRACT／SPEC）だけに置く。
    # ★2026-09-10＝§4 から §7 へ移した（別の AI の点検・逐語「恒久の決まり69番は、
    #   行番号を手で打つなと求めています。（略）手で書く §4 に置くと、69番と正面から
    #   ぶつかります」）。実測＝同じ4件の関数が §4-3・§7-7 の DESIGN_CONTRACT・
    #   §7-7 の SPEC の3か所に出ていた。
    add("### 7-7 触る関数と、その定義の行")
    add("")
    add(_tag("自動", "実物のコードから読んだ定義の行"))
    add(_begin("CODEREF", _h(build("CODEREF", d))))
    add(build("CODEREF", d))
    add(_end("CODEREF"))
    add("")

    add("### 7-8 プログラムが読む設定（2つ）")
    add("")
    add(_wtag("自動", "DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数"))
    add(_begin("SPEC", _h(build("SPEC", d))))
    add(build("SPEC", d))
    add(_end("SPEC"))
    add("")
    return "\n".join(L).rstrip() + "\n"


# ══ 書く・検出する ═══════════════════════════════════════════════════

def write(dry: bool = False, dest: Path = None) -> int:
    """設計書を作る。

    ★2026-09-09（設計書 gen-acceptance-tool-20260909 の §3-2 の3）
      ＝書き出し先を差し替えられるようにした（`dest`）。
      なぜ＝自己テストが `write()` を呼ぶので、差し替えられないと、
      テストを走らせるたびに本物の設計書（`.claude/state/acceptance.md`）が
      上書きされ、承認が外れてこの道具を直せなくなる（2026-09-09 に実際に起きた）。
      ★`dest` を省くと、いままでどおり本物の設計書に書く（動きは変えていない）。
    """
    d = src()
    ok, why = laws_count_ok()
    if not ok:
        raise SystemExit(f"[gen_acceptance] 法則の件数が合わない（{why}）＝1件も落とせません（fail-closed）")
    # ★2026-10-13（工事 design-doc-gen-form-20261013・まこさん指示 2026-10-12「今後は毎回この検査を走らせるよう強制を入れて」）
    #   ＝設計書を作るたびに、項目の抜けを見張る検算を走らせる。通らなければ書かない。
    _rc, _out = _sections_rc()
    if _rc:
        raise SystemExit("[gen_acceptance] 項目の抜けを見張る検算（gen_design_sections.py --check）が通りません（fail-closed）:\n" + _out)
    body = page(d)
    # ★2026-09-29（やることの表 P1-3）＝［手書き］の印は、割り当ての5つ（HAND_KEYS）とちょうど同じ数でなければ書かない
    # ★2026-09-30（設計書 point1-one-way-20260930-2）＝工事のフォルダの1本だけなので、いつも数える
    n_hand = sum(1 for ln in body.splitlines() if ln.startswith("［手書き］"))
    if n_hand != len(_hk(d)):
        raise SystemExit(f"[gen_acceptance] ［手書き］の印が {n_hand} 個（割り当ては {len(_hk(d))} 個・fail-closed）")
    if dry:
        print(body)
        return 0
    out = Path(dest) if dest else DEST
    # ★2026-09-29（まこさん指示「要件のまとめ1本を機械で作る」・worklog 20260929 §81・§82）
    #   ＝本物の設計書を書くときは、工事のフォルダ（verbatim/<iter>/）の「要件のまとめ.md」も作り直す。
    #     逐語のファイルが1つでも記録と食い違えば止まる（fail-closed）。自己テスト（dest 指定）では作らない。
    if not dest and (d.get("設計のもと") or {}).get("逐語のファイル"):
        try:
            _sm = gv.summary(str(d["iter"]))
            print(f"   要件のまとめ＝{_sm.relative_to(ROOT)}")
        except gv.VerbatimError as e:
            raise SystemExit(f"[gen_acceptance] 要件のまとめを作れない（{e}・fail-closed）")
    out.write_text(body, encoding="utf-8")
    # ★2026-10-13＝新しい形の設計書を本物に書くときは、読むもの宣言の写しを、工事のフォルダに置く
    #   （宣言が次の工事の物に替わった後も、やることの番号と結ぶ要件を写せるように）。
    if not dest and d.get("形") == "新" and d.get("読むもの宣言の文"):
        (gv.work_dir(str(d["iter"])) / PLAN_COPY).write_text(d["読むもの宣言の文"], encoding="utf-8")
    print(f"✅ --write 完了: {out}（{len(body.splitlines())}行・囲み {len(BLOCKS)}個）")
    print(f"   法則の件数の照合＝{why}")
    return 0


def _outside_mismatch(cur: str, want: str) -> list:
    """いまの設計書と作り直した設計書を、囲みの外だけ1行ずつ比べる（2026-09-30・設計書 point1-proof-20260930 の P-2）。

    ★照らさない所（作り直しと食い違って当たり前）＝①囲みの中（目印の行ごと・中身はハッシュ値で別に照らす）
      ②完成の条件の表（承認のプログラムが状態を書く）③2-1 の表の最後の列（走らせた時点の数）。
    戻り＝食い違った行の説明の一覧（空なら同じ）。
    """
    def _norm(text: str) -> list:
        out, skip, in21 = [], False, False
        for ln in text.splitlines():
            if re.match(r"<!-- (ACC_\w+|ACCEPT_TABLE)_START", ln):
                skip = True
                continue
            if skip:
                if re.match(r"<!-- (ACC_\w+|ACCEPT_TABLE)_END", ln):
                    skip = False
                continue
            if ln.startswith("### "):
                in21 = ln.startswith("### 2-1")
            if in21 and ln.startswith("|") and ln.count("|") >= 3:
                ln = ln.rstrip().rstrip("|").rsplit("|", 1)[0] + "|"
            out.append(ln.rstrip())
        return out
    a, b = _norm(cur), _norm(want)
    bad = []
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else "（行が無い）"
        y = b[i] if i < len(b) else "（行が無い）"
        if x != y:
            bad.append(f"囲みの外の {i + 1} 行目: 設計書「{x[:80]}」／作り直し「{y[:80]}」")
    return bad


def _section4_blocks() -> set:
    """§4 の節が名指ししたときだけ出る囲み。

    ★2026-09-16＝この2つだけ。ほかの囲みは `page` が必ず出す＝いつも照らす。
      実物で確かめた＝`page` が MATERIALS・RANKING・RANDOM・CODEREF・SELFTEST・SPEC・
      CHECKLIST を直に書き、STAGES と LAWS は §4 の節の「囲み」の指定から出る。
      ★最初は5つと書いて、MATERIALS・RANKING・RANDOM を照らさなくする間違いをした。
    """
    return {"STAGES", "LAWS"}


def _blocks_in_src(d: dict) -> set:
    """元データの §4 の節が、実際に名指ししている囲みの名前。"""
    out = set()
    for got in (d.get("設計の中身") or {}).values():
        if isinstance(got, dict) and got.get("囲み"):
            out.add(got["囲み"])
    return out


def verify(dest: Path = None) -> int:
    """囲みの中が、機械の書いたままかを検出する。

    ★2026-09-09＝読む相手を差し替えられるようにした（`write` と対）。
    """
    target = Path(dest) if dest else DEST
    if not target.exists():
        print(f"❌ 設計書が無い: {target}")
        return 1
    # ★2026-09-30（設計書 point1-one-way-20260930-2）＝工事名が無ければ、設計書の ARC の iter を工事名にする
    global WORK
    if not WORK:
        mi = re.search(r'<!-- ARC iter="([^"]+)" -->', target.read_text(encoding="utf-8"))
        if not mi:
            print(f"❌ 設計書に ARC の目印（iter）が無いので、工事のフォルダを決められない: {target}")
            return 1
        WORK = mi.group(1)
    d = src()
    cur = target.read_text(encoding="utf-8")
    rc = 0
    for kind in BLOCKS:
        if kind == "ACCEPT_TABLE":
            continue                                  # 承認ゲートが読む目印＝hash を持たない
        # ★2026-09-13（98回目）＝監査レポートの欄が空の設計書は、作る側（page）が AUDITTODO の囲みを出さない。
        #   直す前は検出の側だけが囲みを求め、必ず「❌ 囲みが無い」になっていた（作る側と検出の側の食い違い）。
        if kind == "AUDITTODO" and not (d.get("audit_report") or "").strip():
            print("— --verify: AUDITTODO は監査レポートの欄が空なので出ない設計書（照らさない）")
            continue
        # ★2026-09-24（設計書 impl-instruction-apply-20260924・監査 CP41 の B1）＝作る側が出さない囲みは照らさない。
        #   足さないと、指示が無い設計書で必ず ❌ になり、--selftest の T1 が落ちて b72・b73 が空になる。
        if kind == "IMPL" and not (d.get("実装の指示") or []):
            print("— --verify: IMPL は元データの「実装の指示」が空なので出ない設計書（照らさない）")
            continue
        # ★2026-09-16（設計書 audit-autofix-apply-20260916 の完成の条件 AUDIT-7・まこさん承認）
        #   ＝§4 の節に置く囲み（STAGES・LAWS など）は、作る側（page）が
        #     「元データのその節に『囲み』の指定が在るときだけ」出す。
        #   直す前＝検出の側だけが必ず求めたので、engine_tuner の設計書でない工事では
        #     必ず ❌ が2件 出た（98回目に AUDITTODO で入れたのと同じ型の食い違い）。
        if kind in _section4_blocks() and kind not in _blocks_in_src(d):
            print(f"— --verify: {kind} は元データのどの節も求めていないので出ない設計書（照らさない）")
            continue
        m = _begin_re(kind).search(cur)
        e = cur.find(_end(kind))
        if not m or e < 0:
            print(f"❌ --verify: {kind} の囲みが無い")
            rc = 1
            continue
        got = cur[cur.find("\n", m.start()) + 1: e].rstrip("\n")
        want = build(kind, d)
        if _h(got) != m.group(1):
            print(f"❌ --verify: {kind} は手で書き換えられています（本文 {_h(got)} ／ 目印 {m.group(1)}）")
            rc = 1
        elif got.rstrip() != want.rstrip():
            print(f"❌ --verify: {kind} は正本と食い違っています（--write で作り直してください）")
            rc = 1
        else:
            print(f"✅ --verify: {kind} は機械が書いたままです（hash={m.group(1)}）")
    ok, why = laws_count_ok()
    print(f"{'✅' if ok else '❌'} 法則の件数の照合＝{why}")
    rc |= 0 if ok else 1
    # ★2026-09-30（設計書 point1-proof-20260930 の P-2）＝囲みの外の行も、工事のフォルダから作り直した設計書と照らす。
    #   直す前は囲みの中しか見ず、囲みの外に書き足した行（出どころの無い文）を見つけられなかった（worklog 20260930 §31）。
    bad = _outside_mismatch(cur, page(d))
    if bad:
        print(f"❌ --verify: 囲みの外で、作り直しと違う行が {len(bad)} 行 在ります（出どころの無い文の疑い）:")
        for x in bad[:10]:
            print(f"   {x}")
        rc = 1
    else:
        print("✅ --verify: 囲みの外の行は、工事のフォルダから作り直した設計書と同じです")
    return rc


def diff_ok_before_impl(out: str) -> tuple:
    """実物との突き合わせの結果を、実装の前の状態として見てよいかを判定する。

    ★2026-09-09（設計書 gen-acceptance-tool-20260909 の §4-1 の2）
      通すのは2通りだけ＝①齟齬が0件 ②齟齬が「設計にあるが実物に無い関数」だけ。
      ②を通す理由＝実装の前は、設計書に書いた関数がまだ実物に無いのが正しい。
      ★ほかの齟齬（実物にあるが設計に無い・呼ぶはずの名前が無い・定数の値が違う 等）
        は1件でも在れば落とす＝設計書と実物の食い違いを見る検査は消していない。
    戻り＝(通すか, 理由の文)
    """
    ALLOW = "設計にあるが実物に無い関数"
    if "齟齬: 0件" in out:
        return True, "齟齬 0件"
    rows = [ln.strip() for ln in out.splitlines() if ln.startswith("    ") and ln.strip()]
    if not rows:
        return False, f"齟齬の行が読めない（{out.strip()[:100]}）"
    other = [r for r in rows if not r.startswith(ALLOW)]
    if other:
        return False, f"実装の前でも通せない齟齬が {len(other)}件（{other[0][:70]}）"
    return True, f"齟齬は「{ALLOW}」{len(rows)}件だけ＝実装の前の正しい状態"


SAMPLE_WORK = "selftest-sample"                       # 自己テストの見本の工事名（一時の置き場の中だけ）


def _sample_work(base: Path, new: bool = False) -> str:
    """一時の置き場 base に、見本の工事のフォルダを作る。戻り＝工事名。

    ★2026-09-30（設計書 point1-one-way-20260930-2）＝自己テストは本物の元データ・本物の設計書に頼らない
      （修正20 の根＝途中でやめた5点まとめの元データを本物として読んでいた）。
    作り方＝①見本のやり取りの記録（jsonl）を書く ②逐語の道具（gen_verbatim.write）でそこから逐語を写す
      ③見本の やることの表.md を書く。★呼ぶ側が gv.VERBATIM_DIR・gv.ARCHIVE_DIR を base の下に替えておくこと。
    ★見本はこの関数の中に持つ（別のファイルに置かない＝見本も本物のデータとして腐らせない）。
    """
    sys.path.insert(0, str(ROOT / ".claude" / "tools"))
    from list_banned_words import checklist_items
    n_g1 = len([b for g, b in checklist_items() if g == "群1"])
    work = SAMPLE_WORK + ("-new" if new else "")
    na = "非該当＝見本（自己テストの工事）"
    prop = ["見本の案です。",
            "【4-0 この仕組みは何か】", "見本の仕組み。",
            "【4-1 システムの境界】", "見本の境界。",
            "【4-2 入力と出力】", "見本の入力と出力。",
            "【4-3 部品と責任の割り当て】", "- 見本の部品。",
            "【4-4 処理の流れ】", "- 見本の流れ。",
            "【4-5 異常系】", "- 見本の異常系。",
            "【4-12 出る結果の姿】", "見本の結果。",
            "【4-13 影響範囲】", "- 見本の影響。"]
    for k in ("4-6", "4-7", "4-8", "4-9", "4-10", "4-11", "4-14", "4-15", "4-16", "4-17", "4-18"):
        prop += [f"【{k}】", na]
    # ★2026-09-30（設計書 point2-design-to-impl-20260930）＝TARGET が在る設計書は 4-20 を非該当にできないので、見本も1件持つ
    #   （見本の置き場の中の、まだ無い新しいファイル＝本物のファイルに頼らない）
    prop += ["【4-20】", "```json",
             json.dumps([{"番号": 1, "対象のファイル": str(Path(base) / "sample_new.txt"), "直す箇所": "新しいファイル",
                          "直す前の文字": "なし", "種類": "直した後の文字", "中身": "見本",
                          "根拠の抜き書き": "見本:1「見本」", "状態": "確定"}], ensure_ascii=False),
             "```"]
    prop += ["【5 決めたことと理由】", "| 決めたこと | 理由 | 捨てた案 |", "|---|---|---|", "| 見本 | 見本 | 見本 |",
             "【6-2 リスク】", "| 中身 | どうするか |", "|---|---|", "| 見本 | 見本 |",
             "【6-3 見積もり】", "| 何 | 見込み | 根拠 |", "|---|---|---|", "| 見本 | 1分以内 | 見本 |",
             "【7-1 深掘り4点】", "| 欄 | 中身 |", "|---|---|", "| 真因 | 見本 |", "| 期待値分解 | 見本 |",
             "| root か symptom か | 見本 |", "| ベースアップ | 見本 |",
             "【7-2 固定値ゼロ宣言】", "見本。", "【7-3 変更の単位】", "見本。",
             "【7-4 塞げないもの】", "| 問い | 塞げないこと |", "|---|---|", "| 見本 | 見本 |",
             "【7-5 §4.6 の照合】"] + [f"- 見本の答え {i}" for i in range(1, n_g1 + 1)]
    prop += ["【7-6 完成の条件】", "| 条件 | コマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |",
             "|---|---|---|---|---|---|---|",
             "| 見本 | python3 ../../.claude/tools/gen_verbatim.py --verify x | 道具 | — | — | 要 | 未着手 |",
             "【7-8 プログラムが読む設定】", "```json",
             json.dumps({"TARGET": [".claude/tools/gen_verbatim.py"],
                         "DESIGN_CONTRACT": {"impl_file": "../../.claude/tools/gen_verbatim.py",
                                             "self_check_calls": ["work_dir", "summary"],
                                             "impl_functions": {"../../.claude/tools/gen_verbatim.py": ["work_dir", "summary"]}}},
                        ensure_ascii=False),
             "```",
             "【外部検索】"] + (["| 名前 | 中身 | 検索の言葉 |", "|---|---|---|", "| 見本の検索 | 見本の中身 | 見本 検索の言葉 |"]
                               if new else ["| 名前 | 中身 |", "|---|---|", "| 見本の検索 | 見本の中身 |"])
    if new:
        # ★2026-10-13＝新しい形の案の見本（直すファイルは道具だけ＝種類②）。【7-3b】は、根拠と確かめ直すコマンドの表
        prop += ["【" + HEAD_FIVE + "】", "| 番号 | 欄 | 中身 |", "|---|---|---|",
                 "| ① | 守る相手 | 見本 |", "| ② | 直す前に通っていた誤りの実例 | 見本 |",
                 "| ③ | 直した後に止まる誤りと、まだ通る誤り | 見本 |", "| ④ | この直しで確かめなくなる事・弱くなる守り | 見本の守り |",
                 "| ⑤ | 「触らない」とした要件ごとの根拠 | 見本 |",
                 "【" + HEAD_UNVERIFIED + "】", "| 確かめていないこと | なぜ確かめていないか | 確かめるなら、何を走らせるか |", "|---|---|---|",
                 "| 見本の確かめ | 見本 | 見本のコマンド |",
                 "【7-3b 作ってはいけないものとの照合】", "| 番号 | 根拠 | 確かめ直すコマンド |", "|---|---|---|",
                 "| 1 | 見本の根拠 | 見本のコマンド |", "| 2 | 見本の根拠 | 見本のコマンド |"]
    rows = [{"type": "user", "uuid": "s-u1", "timestamp": "2026-01-01T00:00:00Z",
             "message": {"role": "user", "content": "見本の要件の文"}},
            {"type": "assistant", "uuid": "s-a1", "timestamp": "2026-01-01T00:00:01Z",
             "message": {"role": "assistant", "content": [{"type": "text", "text": "\n".join(prop)}]}},
            {"type": "user", "uuid": "s-u2", "timestamp": "2026-01-01T00:00:02Z",
             "message": {"role": "user", "content": "OK"}}]
    log = Path(base) / "sample_session.jsonl"
    log.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    gv.write("req_s", ["s-u1"], session=str(log), work=work)
    gv.write("okd_s", ["s-a1"], session=str(log), work=work)
    gv.write("ok_s", ["s-u2"], session=str(log), work=work)
    todo = ["# やることの表｜工事 selftest-sample（見本）", "",
            "## 手書きと自動の割り当て", "", "| 項目 | 手書き／自動 |", "|---|---|",
            "| §1 概要 | 手書き |", "| 4-0〜4-18 設計の中身 | 自動 |", "",
            "## 手書きの項目", "",
            "### §1 概要", "", "見本の概要。", "",
            "### 2-1 何を測るか", "", "| 何を測ったか | コマンド | 読み方 |", "|---|---|---|",
            "| 見本 | grep -c 'def page' .claude/tools/gen_acceptance.py | 在れば一以上 |", "",
            "### 3-1 やらないこと", "", "| 中身 | 理由 | 出どころ |", "|---|---|---|", "| 見本のやらないこと | 見本 | 見本 |", "",
            "### 3-2 決めてほしいこと", "", "無し", "",
            "### 4-19 通しの例", "", "見本の通しの例。", ""]
    if new:
        todo = ["# やることの表｜工事 selftest-sample-new（見本）", "",
                "## 一覧", "", "| 番号 | 一文 | 出どころ |", "|---|---|---|", "| 見本 | 見本のやること | 見本 |", "",
                "## やらないこと", "", "| 番号 | 中身 | 理由 | 出どころ |", "|---|---|---|---|", "| Y-1 | 見本のやらないこと | 見本 | 見本 |", "",
                # ★2026-10-18（ToDo の15番）＝共通の ひな型と同じく、割り当ての表を持つ（監査依頼書を作るプログラムが、この表から問い W を作る）
                "## 手書きと自動の割り当て", "", "| 項目 | 手書き／自動 |", "|---|---|",
                "| §1 概要 | 手書き |", "| 目標の②〜⑥ | 手書き |", "| 4-0〜4-18 設計の中身 | 自動 |", "",
                "## 手書きの項目", "",
                "### §1 概要", "", "★向きを見る所。", "見本の概要。", "", "見本の2つ目の段落。", "",
                "### この工事が結ぶ要件と、減らす違い", "", "| 欄 | 中身 |", "|---|---|",
                "| 要件定義の「いまの実物との違い」のどの行か | 見本 |", "| その違いを、どこまで減らすか | 見本の残り |", "| 順番 | 見本 |", "",
                "### 2-1 何を測るか", "", "| 何を測ったか | コマンド | 読み方 |", "|---|---|---|",
                "| 見本 | grep -c 'def page' .claude/tools/gen_acceptance.py | 在れば一以上 |", "",
                "### 目標", "", "| 番号 | 欄 | 中身 |", "|---|---|---|",
                "| ① | どの要件のためか | 見本 |", "| ② | 何が出来るようになるか | 見本 |", "| ③ | net までのつながり | 見本のつながり |",
                "| ④ | 無駄だったと分かる物 | 見本の物 |", "| ⑤ | 済んだ直後に、②を何で確かめるか | 見本 |",
                "| ⑥ | この工事が損なう恐れのある要件 | 見本の要件 |", "",
                "### 3-2 決めてほしいこと", "", "★向きを見る所。", "無し", "",
                "### 4-19 通しの例", "", "見本の例。", ""]
        (gv.work_dir(work) / PLAN_COPY).write_text(
            f"【読むもの宣言】\n設計書: {work}\n{PLAN_NUM_KEY}なし（やることリストに行が無い工事）\n{PLAN_REQ_KEY}要件定義の9番（見本）\n",
            encoding="utf-8")
    (gv.work_dir(work) / TODO_MD).write_text("\n".join(todo), encoding="utf-8")
    gv.summary(work)                                   # 要件のまとめ.md（設計書の 0-1 が指す。依頼書の必読には 2026-10-02 から入れない）
    return work


def selftest() -> int:
    """一時の置き場に作る固定の見本の工事のフォルダ（_sample_work）だけで、わざと壊して ❌ が出るかを試す。

    ★2026-09-09（設計書 gen-acceptance-tool-20260909 の §3-2 の3）
      ＝本物の設計書（`.claude/state/acceptance.md`）には1文字も書かない。控え（一時のファイル）を相手にする。
    ★2026-09-30（設計書 point1-one-way-20260930-2）＝本物の元データ（acceptance_src.json）を読むのも書くのもやめた。
      直す前＝T1 が本物の元データ（途中でやめた5点まとめ）から設計書を組み、ほかの道具を正しく直しただけで落ちた
      （監査 cp52 の修正20）。T3 は本物の元データに一時に書いて戻していた。
      いま＝見本の工事のフォルダだけを使い、本物の設計書と ratchet の直下のファイルの sha256 を前と後で照らす（T14）。
    """
    import copy as _copy
    import shutil
    # ★2026-10-20（ToDo の26番・監査 CP78 の Minor G）＝置き場3本と監査の結果ファイルの置き場を、T25 と T26 の間だけ一時の写しに替える
    global WORK, PARAMS, ROLES, SWITCH, AUDITS
    _saved_paths = (PARAMS, ROLES, SWITCH, AUDITS)
    ok = 0
    total = 0

    def _snap() -> dict:
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [DEST, *sorted(RATCHET.glob("*"))] if p.is_file()}

    snap0 = _snap()
    saved = (WORK, gv.VERBATIM_DIR, gv.ARCHIVE_DIR)
    # 見本の工事のフォルダはリポジトリの中の一時の置き場（設計書にリポジトリからの相対のパスを書くため）
    tmpd = Path(tempfile.mkdtemp(prefix="_selftest_gen_acceptance_", dir=str(STATE)))
    gv.VERBATIM_DIR, gv.ARCHIVE_DIR = tmpd / "verbatim", tmpd / "archive" / "verbatim"   # 本物と同じ形（…/acceptance_archive/verbatim）
    copy = tmpd / "acceptance_selftest.md"
    try:
        WORK = _sample_work(tmpd)
        base_d = src()

        # T1 いまの状態で --verify が通り、7-7 の定義の行が実物の def_lines と同じ（行番号を手で写さない）
        total += 1
        write(dest=copy)
        sys.path.insert(0, str(PRIORITY))
        from verify_design_contract import spec_from_impl
        dl = spec_from_impl(str(ROOT / ".claude" / "tools" / "gen_verbatim.py")).get("def_lines") or {}
        coderef_ok = f"| `work_dir` | {dl.get('work_dir')} |" in copy.read_text(encoding="utf-8")
        if verify(dest=copy) == 0 and coderef_ok:
            ok += 1
            print(f"   T{total} いまの状態で --verify → pass（7-7 の定義の行も実物と同じ）")
        else:
            print(f"   T{total} いまの状態で --verify が ❌ → fail（7-7 の定義の行が実物と同じ＝{coderef_ok}）")

        # T2 囲みに1行 足すと --verify が落ちる
        total += 1
        base = copy.read_text(encoding="utf-8")
        # ★2026-09-17（設計書 acceptance-results-from-commands-20260917）＝LAWS から MATERIALS へ。
        #   直す前＝LAWS の囲みは §4 の節が名指ししたときだけ出るので、engine_tuner の設計書でない工事では
        #     m が None になり、T2 で落ちていた（b72・b73 は壊さなくても rc=1 になり、守りを測れていなかった）。
        #   MATERIALS は page が必ず出す囲み（_section4_blocks の注記）。
        m = _begin_re("MATERIALS").search(base)
        copy.write_text(base[:m.end()] + "\nわざと足した1行\n" + base[m.end():], encoding="utf-8")
        if verify(dest=copy) == 1:
            ok += 1
            print(f"   T{total} 囲みに1行 足すと ❌ → pass")
        else:
            print(f"   T{total} 1行 足しても ✅ のまま → fail")
        copy.write_text(base, encoding="utf-8")

        # T3 「やらないこと」が空だと止まる（見本の やることの表の 3-1 の行を消す＝本物には書かない）
        total += 1
        tpath = gv.work_dir(WORK) / TODO_MD
        orig_todo = tpath.read_text(encoding="utf-8")
        tpath.write_text(orig_todo.replace("| 見本のやらないこと | 見本 | 見本 |\n", ""), encoding="utf-8")
        try:
            src()
            print(f"   T{total} やらないことが空でも通る → fail")
        except SystemExit:
            ok += 1
            print(f"   T{total} やらないことが空だと止まる → pass")
        tpath.write_text(orig_todo, encoding="utf-8")

        # T4 法則を1件 減らすと件数の照合が落ちる（ファイルは書かない）
        total += 1
        law = _load(LAWS)
        n = len([x for x in law["法則"] if isinstance(x, dict)])
        rows = [ln for ln in build_laws({}).splitlines() if ln.startswith("| **")]
        if len(rows) == n and n > 1:
            ok += 1
            print(f"   T{total} 法則の件数の照合が効く（{n}件を全部 並べた） → pass")
        else:
            print(f"   T{total} 法則の件数が合わない（法則 {n}件／表 {len(rows)}行） → fail")

        # T5 正本が読めないと止まる
        total += 1
        try:
            _load(RATCHET / "存在しない正本.json")
            print(f"   T{total} 無い正本でも通る → fail")
        except SystemExit:
            ok += 1
            print(f"   T{total} 無い正本で止まる → pass")

        # T6 置き換えない目印が残ると止まる
        total += 1
        try:
            body = "見本 {{" + "UNKNOWN}}"
            left = sorted(set(_MARK_RE.findall(body)))
            if left:
                raise SystemExit("目印が残っている")
            print(f"   T{total} 目印が残っても通る → fail")
        except SystemExit:
            ok += 1
            print(f"   T{total} 目印が残ると止まる → pass")

        # T7 作った設計書が、実物との突き合わせで齟齬0件
        #   ★2026-09-09（設計書 gen-acceptance-tool-20260909 の §4-1 の2）
        #     ＝実装の前は「設計にあるが実物に無い関数」が出るのが正しい状態。
        #     その1種類だけの齟齬なら通す。ほかの齟齬が1件でも在れば落とす。
        #     直す前＝齟齬が1件でも在れば落としていたので、実装の前は必ず落ちた。
        total += 1
        r = subprocess.run(
            [sys.executable, str(PRIORITY / "verify_design_contract.py"), "--diff", str(copy)],
            capture_output=True, text=True, cwd=str(SDK))
        ok7, why7 = diff_ok_before_impl(r.stdout)
        if ok7:
            ok += 1
            print(f"   T{total} 実物との突き合わせ（{why7}） → pass")
        else:
            print(f"   T{total} 実物との突き合わせ → fail（{why7}）")

        # T8 作った設計書が、食い違いゲートを通る
        #   ★2026-09-30（worklog 20260930 §28・まこさん OK）＝直す前は「--check <写し>」で呼んでいた。
        #     その hook に --check の口は無く、標準入力を待つ＝入力が空なら何も見ずに 0（見かけだけの pass）、
        #     端末から承認を打つと入力待ちで止まった（b72・b73 が 600秒で打ち切り）。
        #     hook が本当に呼ばれるときと同じ形（Write の入力の json）を標準入力で渡す。
        total += 1
        _t8in = json.dumps({"tool_name": "Write", "tool_input": {
            "file_path": str(STATE / "acceptance.md"), "content": copy.read_text(encoding="utf-8")}})
        r = subprocess.run(
            [sys.executable, str(ROOT / ".claude/hooks/enforce_design_consistency.py")],
            input=_t8in, capture_output=True, text=True)
        if r.returncode == 0:
            ok += 1
            print(f"   T{total} 食い違いゲート 終了コード 0 → pass")
        else:
            print(f"   T{total} 食い違いゲート → fail（{(r.stderr or r.stdout).strip()[:200]}）")

        # T9（2026-09-17・設計書 acceptance-results-from-commands-20260917）＝2-1 の表の結果は道具が入れる
        #   ①書き込みのコマンドで止まる ②読むだけのコマンドの出力と終了コードが表に入る
        #   ③元データに「結果」の欄が在ると止まる（本物のファイルには書かない＝page を直に呼ぶ）
        total += 1
        bad9 = ""
        d9 = _copy.deepcopy(base_d)
        d9["なぜ作るか"] = [{"何を測ったか": "見本", "コマンド": "rm -f /tmp/gen_acceptance_t9"}]
        try:
            page(d9)
            bad9 = "書き込みのコマンドで止まらない"
        except SystemExit:
            pass
        d9["なぜ作るか"] = [{"何を測ったか": "見本", "コマンド": "grep -c '^def page' .claude/tools/gen_acceptance.py",
                            "読み方": "定義の数"}]
        try:
            if "| 定義の数 | 1（終了コード 0） |" not in page(d9):
                bad9 = bad9 or "出力と終了コードが表に入らない"
        except SystemExit as e:
            bad9 = bad9 or f"読むだけのコマンドで止まった（{e}）"
        d9["なぜ作るか"] = [{"何を測ったか": "見本", "コマンド": "grep -c x .claude/tools/gen_acceptance.py",
                            "結果": "手で写した"}]
        try:
            page(d9)
            bad9 = bad9 or "「結果」の欄で止まらない"
        except SystemExit:
            pass
        if not bad9:
            ok += 1
            print(f"   T{total} 2-1 の結果を道具が入れる（書き込みで止まる・出力が入る・手の結果で止まる） → pass")
        else:
            print(f"   T{total} 2-1 の結果 → fail（{bad9}）")

        # T10（2026-09-29）＝対応の表から1行 消すと、設計書を書かない（設計のもとの抜けを通さない）
        total += 1
        d10 = _copy.deepcopy(base_d)
        tab = list(d10.get("対応の表") or [])
        if not tab:
            print(f"   T{total} 見本に対応の表が無い → fail")
        else:
            d10["対応の表"] = tab[1:]
            try:
                page(d10)
                print(f"   T{total} 対応の表の1行を消しても書ける → fail")
            except SystemExit as e:
                if "写した行" in str(e):
                    ok += 1
                    print(f"   T{total} 対応の表の1行を消すと止まる（写した行に対応が無い） → pass")
                else:
                    print(f"   T{total} 別の理由で止まった → fail（{str(e)[:120]}）")

        # T11（2026-09-29）＝「まこさんの決定」の欄（CC が手で書く口）を足すと止まる
        total += 1
        d11 = _copy.deepcopy(base_d)
        d11["まこさんの決定"] = ["CC が手で書いた行（T11）"]
        try:
            page(d11)
            print(f"   T{total} まこさんの決定の欄を足しても書ける → fail")
        except SystemExit as e:
            if "手で書く口は閉じました" in str(e):
                ok += 1
                print(f"   T{total} まこさんの決定の欄を足すと止まる → pass")
            else:
                print(f"   T{total} 別の理由で止まった → fail（{str(e)[:120]}）")

        # T17（2026-09-30・設計書 point2-design-to-impl-20260930）＝直すファイルが在るのに 4-20 が0件なら止まる
        total += 1
        d17 = _copy.deepcopy(base_d)
        d17["実装の指示"] = []
        # ★2026-09-30（監査 cp53 の修正2）＝4-20 を「非該当（理由つき）」にした設計書＝足した検査だけが止める場面にする
        #   （直す前は理由の無い 4-20 を試したので、前から在る「理由が無い」の検査が先に止め、足した検査を外しても通った）
        d17.setdefault("設計の中身", {})["4-20"] = {"非該当": "見本（CC が手で当てる）"}
        try:
            page(d17)
            print(f"   T{total} 4-20 が0件でも書ける → fail")
        except SystemExit as e:
            if "実装の指示（4-20）が0件" in str(e):
                ok += 1
                print(f"   T{total} 直すファイルが在るのに 4-20 が0件だと止まる → pass")
            else:
                print(f"   T{total} 別の理由で止まった → fail（{str(e)[:120]}）")

        # T12（2026-09-29・まこさん指示「設計の元となるデータは明確にして」）＝0-1 に、要件のまとめ.md への参照と、
        #   逐語のファイルの名前が全部 出て、行った先のまとめの行数の合計が写した行の数と合う。
        total += 1
        try:
            s12 = build_source(base_d)
            names12 = [str(n) for n in ((base_d.get("設計のもと") or {}).get("逐語のファイル") or [])]
            names_ok = all(f"/{n.split('/')[-1]}.txt`" in s12 for n in names12)
            n12 = sum(int(x) for x in re.findall(r"（(\d+) 行）", s12))
            want12 = len(source_rows(base_d))
            if names12 and names_ok and "要件のまとめ" in s12 and n12 == want12:
                ok += 1
                print(f"   T{total} 0-1 に要件のまとめへの参照と逐語のファイル {len(names12)} 本・行った先の行 {n12} 行（写した行と一致） → pass")
            else:
                print(f"   T{total} 0-1 の参照と対応の表 → fail（名前={names_ok} 行={n12}/{want12}）")
        except SystemExit as e:
            print(f"   T{total} 0-1 の参照と対応の表 → fail（{str(e)[:120]}）")

        # T13（2026-09-30・設計書 point1-one-way-20260930-2）＝工事名が無ければ止まる（元データの JSON へは戻らない）
        total += 1
        keep = WORK
        WORK = ""
        try:
            src()
            print(f"   T{total} 工事名が無くても組める → fail")
        except SystemExit as e:
            if "工事名がありません" in str(e):
                ok += 1
                print(f"   T{total} 工事名が無いと止まる（設計書の作り方は工事のフォルダの1本だけ） → pass")
            else:
                print(f"   T{total} 別の理由で止まった → fail（{str(e)[:120]}）")
        WORK = keep

        # T15（2026-09-30・設計書 point1-proof-20260930 の P-1）＝見本の工事のフォルダを archive の側へ移しても --verify が通る
        total += 1
        write(dest=copy)
        _wd = gv.VERBATIM_DIR / SAMPLE_WORK
        _ad = gv.ARCHIVE_DIR / SAMPLE_WORK
        _ad.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(_wd), str(_ad))
        try:
            rc15 = verify(dest=copy)
        finally:
            shutil.move(str(_ad), str(_wd))
        if rc15 == 0:
            ok += 1
            print(f"   T{total} 工事のフォルダを archive へ移しても --verify が通る → pass")
        else:
            print(f"   T{total} archive へ移すと --verify が落ちる → fail")

        # T16（2026-09-30・同じ設計書の P-2）＝囲みの外（§1 概要の下）に1行 足すと --verify が ❌
        total += 1
        _t16 = copy.read_text(encoding="utf-8")
        _i = _t16.find("## 1｜概要")
        _j = _t16.find("\n", _i) + 1 if _i >= 0 else -1
        if _j > 0:
            copy.write_text(_t16[:_j] + "CC が手で書き足した1行（見本）。\n" + _t16[_j:], encoding="utf-8")
            rc16 = verify(dest=copy)
            copy.write_text(_t16, encoding="utf-8")
        else:
            rc16 = None
        if rc16 == 1:
            ok += 1
            print(f"   T{total} 囲みの外に1行 足すと --verify が ❌ → pass")
        else:
            print(f"   T{total} 囲みの外の1行を見つけない → fail（rc={rc16}）")

        # T18・T19（2026-10-12・170回目・まこさん「OK」＝直し方の案 A-1・A-4）＝OK された案に【0-R】（要件定義との照らし）が
        #   在る工事は、設計書の上部に固定で載せる文と、照らしの表が出る。見本（【0-R】が無く、工事名に日付が無い）には出ない。
        #   照らしが1行でも無ければ止まる。
        total += 1
        _items = gcr.requirement_items()
        d18 = _copy.deepcopy(base_d)
        d18["要件定義との照らし"] = {_no: {"関わるか": "見本", "合っているか": "見本", "根拠": "見本"} for _no, _nm in _items}
        _p18 = page(d18)
        if (CORE_MARK in _p18 and "### 0-R " in _p18 and CORE_MARK not in page(base_d)
                and all(f"| {_no} | {_nm} | 見本 | 見本 | 見本 |" in _p18 for _no, _nm in _items)):
            ok += 1
            print(f"   T{total} 【0-R】が在る工事は、上部に固定で載せる文と照らしの表（{len(_items)} 行）が出る・無い見本には出ない → pass")
        else:
            print(f"   T{total} 固定で載せる文か照らしの表が出ない → fail")
        total += 1
        d19 = _copy.deepcopy(d18)
        d19["要件定義との照らし"].pop(_items[-1][0])
        try:
            page(d19)
            print(f"   T{total} 照らしが1行 無くても止まらない → fail")
        except SystemExit as e:
            if "照らし" in str(e):
                ok += 1
                print(f"   T{total} 照らしが1行 無いと止まる → pass")
            else:
                print(f"   T{total} 別の理由で止まった → fail（{str(e)[:120]}）")

        # 新しい形の元の番人 7つ（2026-10-13・工事 design-doc-gen-form-20261013。出る番号は T19〜T25。前からの最後の項目は T26 になる）
        #   ＝新しい形の元（共通の ひな型で書いた やることの表と案）
        global _NEW_FORM, _sections_rc
        _keep_work, _keep_rc = WORK, _sections_rc
        WORK = _sample_work(tmpd, new=True)
        copy2 = tmpd / "acceptance_selftest_new.md"
        total += 1
        try:
            write(dest=copy2)
            _t20 = copy2.read_text(encoding="utf-8")
            _miss20 = [s for s in ("工事の種類: 種類②", "### 0-R 要件定義の索引", "### 2-0 この工事が結ぶ要件と、減らす違い",
                                   "### 3-0 目標", "### 4-22 ", "### 6-5 確かめていないこと", "見本の概要。\n\n見本の2つ目の段落。",
                                   "| 10 | ", "CC が書いて、まこさんが OK した案の【4-0】",
                                   "この工事が解く問題＝見本の概要。", "目標の③（net までのつながり）＝見本のつながり",
                                   "| 見本の根拠 | 見本のコマンド |",
                                   "この工事が解く問題: 見本の概要。",
                                   "見本の概要。（プログラムが、§1 概要の1文目を写した）") if s not in _t20]
            # ★設計書の監査 CP77 の修正＝概要の1文目が、4-0 の冒頭（見出しと表示のすぐ下）に出ているか
            if "### 4-0" in _t20 and _t20.split("### 4-0", 1)[1].split("この工事が解く問題＝", 1)[0].count("\n") > 5:
                _miss20.append("4-0 の冒頭に、概要の1文目が無い")
            if not _miss20 and verify(dest=copy2) == 0 and "### 0-R 要件定義の索引" not in copy.read_text(encoding="utf-8"):
                ok += 1
                print(f"   T{total} 新しい形の元から設計書を作れて、--verify が通る（いままでの形の見本には、新しい節が出ない） → pass")
            else:
                print(f"   T{total} 新しい形の元から作った設計書 → fail（出ていない物＝{_miss20}）")
        except SystemExit as e:
            print(f"   T{total} 新しい形の元から設計書を作れない → fail（{str(e)[:300]}）")
        _tp = gv.work_dir(WORK) / TODO_MD
        _o21 = _tp.read_text(encoding="utf-8")
        for _name, _txt, _want in (
                ("手書きの項目に知らない見出しが在ると止まる", _o21 + "\n### 知らない見出し\n\n見本\n", "知らない見出し「### 知らない見出し」"),
                ("目標の④が空だと止まる", _o21.replace("| ④ | 無駄だったと分かる物 | 見本の物 |", "| ④ | 無駄だったと分かる物 | 無し |"), "空では出せない"),
                # ★設計書の監査 CP77 の修正＝完成の条件に、やることの番号ごとの行が在るかの照らしを測る
                ("やることの番号に、完成の条件の行が無いと止まる", _o21.replace("| 見本 | 見本のやること | 見本 |", "| 番号X9 | 見本のやること | 見本 |"), "やることの番号 番号X9 に、完成の条件")):
            total += 1
            _tp.write_text(_txt, encoding="utf-8")
            try:
                src()
                print(f"   T{total} {_name}はずが、通った → fail")
            except SystemExit as e:
                if _want in str(e):
                    ok += 1
                    print(f"   T{total} {_name} → pass")
                else:
                    print(f"   T{total} 別の理由で止まった → fail（{str(e)[:200]}）")
            _tp.write_text(_o21, encoding="utf-8")
        total += 1
        _sections_rc = lambda: (1, "見本の抜け")                # noqa: E731  検算が落ちた場面を作る
        try:
            write(dest=copy2)
            print(f"   T{total} 項目の抜けを見張る検算が落ちても、設計書を書いた → fail")
        except SystemExit as e:
            if "項目の抜けを見張る検算" in str(e):
                ok += 1
                print(f"   T{total} 項目の抜けを見張る検算が落ちると、設計書を書かない → pass")
            else:
                print(f"   T{total} 別の理由で止まった → fail（{str(e)[:200]}）")
        _sections_rc = _keep_rc
        # 読むもの宣言が「なし」なのに、やることの表の一覧に、やることリストの行の番号が在ると止まる（すり抜けを塞ぐ）
        total += 1
        _nums = [str(t.get("番号")) for t in (_load(TODO).get("やること") or []) if isinstance(t, dict) and t.get("番号")]
        _tp.write_text(_o21.replace("| 見本 | 見本のやること | 見本 |", f"| 見本 | {_nums[0]} の続きのやること | 見本 |"), encoding="utf-8")
        try:
            src()
            print(f"   T{total} 宣言が「なし」で、一覧に やることリストの行の番号が在っても通った → fail")
        except SystemExit as e:
            if "やることの番号＝なし" in str(e):
                ok += 1
                print(f"   T{total} 宣言が「なし」なのに、一覧に やることリストの行の番号が在ると止まる → pass")
            else:
                print(f"   T{total} 別の理由で止まった → fail（{str(e)[:200]}）")
        _tp.write_text(_o21, encoding="utf-8")
        # 置き場から写す行（法則の原文・指標の行）と、新しく入る数字の抜き出し
        total += 1
        # ★2026-10-20（ToDo の26番・監査 CP78 の Minor G）＝本物の置き場3本（資料の表2本・オンとオフの一覧）と、監査の結果ファイルに頼らない。
        #   見本の写しを一時の置き場に作り、T25 と T26 の間だけ差し替える（外の finally で必ず戻す）
        _fx = tmpd / "fixture"
        (_fx / "audits").mkdir(parents=True, exist_ok=True)
        PARAMS, ROLES, SWITCH, AUDITS = _fx / "params.json", _fx / "roles.json", _fx / "switch.json", _fx / "audits"
        PARAMS.write_text(json.dumps({"指標": [{"種類": "ADX", "パラメータの名前": ["期間"],
                                               "範囲": [{"下限": 7, "上限": 30, "出どころ": "見本の出どころ"}],
                                               "最初の値（スキャル）": 7, "最初の値の出どころ（スキャル）": "見本",
                                               "最初の値（デイトレ）": 14, "最初の値の出どころ（デイトレ）": "見本"}]},
                                     ensure_ascii=False), encoding="utf-8")
        ROLES.write_text(json.dumps([{"種類": "ADX", "出どころの役割": "見本の役割", "役割の印": "filter"},
                                     {"種類": "POC", "出どころの役割": "見本の役割", "役割の印": "location",
                                      THRESHOLD_KEY: {"最初の値（スキャル）": 1, "最初の値（デイトレ）": 2, "範囲": "0〜5", "出どころ": "見本の出どころ"}}],
                                    ensure_ascii=False), encoding="utf-8")
        SWITCH.write_text(json.dumps({"on": ["ADX", "POC", "前日POC"], "off": ["見本のオフの指標"]}, ensure_ascii=False), encoding="utf-8")
        _rep_fx = AUDITS / f"2026-01-01_{WORK.replace('-', '_')}_design_cp1_audit_report.md"
        _rep_fx.write_text("# 見本の監査の結果\n", encoding="utf-8")
        _r47 = "\n".join(_auto_rows("4-7", ["ADX に関わる"], {}))
        _rpoc = "\n".join(_auto_rows("4-7", ["POC に関わる"], {}))                          # 閾値の欄が在れば写す
        _r46 = "\n".join(_auto_rows("4-6", ["法則 C1 を守る"], {}))
        _n25 = _new_numbers({"実装の指示": [{"番号": 1, "対象のファイル": "scripts/priority_rebuild/x.py",
                                         "直す前の文字": "a = 1", "中身": "a = 1\nb = 250  # 300 は使わない"}]})
        # ★設計書の監査 CP77 の修正（2026-10-13）＝見本1件（ADX・C1）だけで見ない。監査が挙げた場面を、1つずつ測る。
        _sw25 = _load(SWITCH)
        _off0 = sorted(str(x) for x in _sw25.get("off") or [])[0]
        _roff = "\n".join(_auto_rows("4-7", [f"{_off0} を外す"], {}))                      # オフの指標も、行に出る
        _rsub = "\n".join(_auto_rows("4-7", ["前日POC に関わる"], {}))                      # 「前日POC」で、「POC」の行は出ない
        _rt15 = "\n".join(_auto_rows("4-4", ["自己テスト（T1〜T5）を走らせる"], {}))          # 自己テストの番号を、法則と取り違えない
        _rscn = "\n".join(_auto_rows("4-6", ["| 場面の決まり | R1 | 守る |"], {}))            # 場面の決まりの原文（機械が読む判定）
        _fam0 = (_load(FAMILIES).get("families") or [{}])[0]
        _rfam = "\n".join(_auto_rows("4-6", [f"| 型の表 | {_fam0.get('name')} | 守る |"], {}))  # 型を、名前でも探す
        _mat = build_materials({"形": "新", "TARGET": ["scripts/priority_rebuild/x.py"], "NEW_FILE": [],
                                "設計の中身": {"4-7": ["ADX と 前日POC に関わる"]}})           # 探す材料は、関わる指標だけ
        _c25 = {"指標の行": "| ADX |" in _r47 and "閾値の代表の値" in _r47,
                "カタログの列": "カタログ（指標の定義の表）に在るか" in _r47 and "承認済みの型の表に在るか" in _r47 and "| 在る | 在る | オン |" in _r47,
                "オフの指標": f"| {_off0} |" in _roff and "| オフ |" in _roff,
                "名前の一部": "| 前日POC |" in _rsub and "| POC |" not in _rsub,
                "時間足": "| 全部（" in _r47 and "| 役割 trigger" in _r47,
                "法則の原文": "| C1 |" in _r46,
                "自己テストの番号": "| T1 |" not in _rt15,
                "場面の決まり": "| R1 |" in _rscn and "掛かる場面" in _rscn,
                "型の名前": f"| {_fam0.get('id')} |" in _rfam,
                "探す材料": "この工事が関わる指標＝2種" in _mat,
                "監査の結果ファイル": _design_audit_reports({"iter": WORK}) == [str(_rep_fx.relative_to(ROOT))],
                "数字": _n25 == [("1", "250")],
                # ★2026-10-20（監査 CP78 の Minor D・Minor B）
                "閾値の欄を写す": "スキャル 1／デイトレ 2／範囲 0〜5" in _rpoc,
                "閾値の未決": f"未決（置き場 {ROLES.name} に「{THRESHOLD_KEY}」の欄が無い）" in _r47,
                "カタログの注記": "カタログに無い名前を案に書いても" in _r47}
        if all(_c25.values()):
            ok += 1
            print(f"   T{total} 置き場から、指標の行（カタログ・型の表・オンとオフ・閾値の欄と未決）・時間足・法則と場面の決まりの原文・型を写す。関わる指標だけを数える。新しく入る数字を抜き出す → pass")
        else:
            print(f"   T{total} 置き場から写す行・数字の抜き出し → fail（落ちた物＝{[k for k, v in _c25.items() if not v]}）")

        # 新しい形の設計書の 6-4・7-6・4-19・§4 の並び（2026-10-20・ToDo の26番・監査 CP78 の Major の残り・Minor C・Minor D。出る番号は T26）
        #   ＝見本の監査の結果ファイル（上の写しの置き場）で 6-4 の行が出るか／案の【7-6】の理由の行が設計書に写るか／
        #     4-19 が新しい形の名前で出るか／§4 の項目が項目の正本の並び順で出るか
        total += 1
        try:
            _d26 = src()
            _d26.setdefault("案の文", {}).setdefault("7-6", []).append("- 行が無いやることの番号と、その理由：見本の理由")
            _p26 = page(_d26)
            _m26 = _load(MAP)
            _n419 = next((str(x.get("新しい形の名前")) for x in _m26.get("項目") or [] if isinstance(x, dict) and x.get("番号") == "4-19"), "")
            _heads = [h for h in re.findall(r"^### (4-\d+) ", _p26, flags=re.M)]
            _ord = [x for x in (_m26.get("_§4の並び順") or []) if x in _heads]
            _c26 = {"6-4 の行": "**6-4 この設計書が受けた設計書の監査**＝" in _p26 and _rep_fx.name in _p26,
                    "7-6 の理由の行": "- 行が無いやることの番号と、その理由：見本の理由" in _p26,
                    "4-19 の新しい名前": bool(_n419) and f"### 4-19 {_n419}" in _p26,
                    "§4 の並び順": bool(_heads) and list(dict.fromkeys(_heads)) == _ord}
        except SystemExit as e:
            _c26 = {f"止まった（{str(e)[:120]}）": False}
        if all(_c26.values()):
            ok += 1
            print(f"   T{total} 新しい形の設計書に、6-4 の監査の結果ファイル・7-6 の理由の行・4-19 の新しい名前が出て、§4 が並び順どおり → pass")
        else:
            print(f"   T{total} 新しい形の設計書の 6-4・7-6・4-19・§4 の並び → fail（落ちた物＝{[k for k, v in _c26.items() if not v]}）")
        PARAMS, ROLES, SWITCH, AUDITS = _saved_paths
        WORK = _keep_work
        _NEW_FORM = False

        # --out の控えの止め（2026-10-20・まこさん「塞ぐ」・ToDo の24番。出る番号は T27、最後の T14 の項目は T28 になる）＝--out は承認の控えの置き場へ書けない。ほかの置き場へは今までどおり書ける
        #   main() を旗つきで呼び、旗 → 判定 → 書く／止める のつながりごと試す。控えの置き場には存在しない名前だけを渡す
        total += 1
        _argv = sys.argv
        _miss = ARCHIVE / "_selftest_out_block.md"
        _c27 = {}
        try:
            # 見本のやり取りの記録は1本を共有し、T19 の新しい形の見本が書き替えている＝古い形の見本を作り直してから使う
            WORK = _sample_work(tmpd)
            for _key, _o in (("控えの置き場", _miss), ("大文字の控えの置き場", Path(str(_miss).replace("acceptance_archive", "ACCEPTANCE_ARCHIVE")))):
                sys.argv = ["gen_acceptance.py", "--work", WORK, "--out", str(_o)]
                _c27[_key] = main() == 2 and not _miss.exists()
            _okp = tmpd / "out_ok.md"
            sys.argv = ["gen_acceptance.py", "--work", WORK, "--out", str(_okp)]
            _c27["ほかの置き場"] = main() == 0 and _okp.is_file()
        finally:
            sys.argv = _argv
            WORK = _keep_work
        if all(_c27.values()):
            ok += 1
            print(f"   T{total} --out が承認の控えの置き場（大文字にしたパスも）を指すと止まり、ほかの置き場には書ける → pass")
        else:
            print(f"   T{total} --out の控えの置き場の止め → fail（落ちた物＝{[k for k, v in _c27.items() if not v]}）")

        # T14（2026-09-30・同じ設計書）＝本物の設計書と ratchet の直下のファイルに1バイトも書いていない
        total += 1
        changed = [p for p, h in _snap().items() if snap0.get(p) != h] + [p for p in snap0 if p not in _snap()]
        if not changed:
            ok += 1
            print(f"   T{total} 本物の設計書と ratchet に書いていない（前と後の sha256 が同じ） → pass")
        else:
            print(f"   T{total} 本物のファイルが変わった → fail（{changed[:3]}）")
    finally:
        WORK, gv.VERBATIM_DIR, gv.ARCHIVE_DIR = saved
        PARAMS, ROLES, SWITCH, AUDITS = _saved_paths
        shutil.rmtree(tmpd, ignore_errors=True)
    print(f"\n{'✅' if ok == total else '❌'} selftest {ok}/{total} pass")
    return 0 if ok == total else 1


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true", help="元データと正本から設計書を作る")
    p.add_argument("--verify", action="store_true", help="囲みの中が機械の書いたままかを検出する")
    p.add_argument("--dry-run", action="store_true", help="書かずに画面に出す")
    p.add_argument("--selftest", action="store_true", help="一時の置き場に作る固定の見本だけで、わざと壊して ❌ が出るかを試す")
    # ★2026-09-29＝本物の設計書（acceptance.md）ではない置き場に書く口（承認の前の検査に掛けるため）。--work と一緒のときだけ。
    p.add_argument("--out", default="", help="--work の結果を書く置き場（本物の設計書には書かない）")
    # ★2026-09-29（工事 point1-design-autogen-20260929）＝工事のフォルダ（やることの表.md と逐語のファイル）から組む口
    # ★2026-09-30（設計書 point1-one-way-20260930-2）＝設計書の作り方はこの口の1本だけ（元データの JSON の --src は消した）
    p.add_argument("--work", default="", help="工事名＝.claude/state/verbatim/<工事名>/ から設計書を組む")
    a = p.parse_args()
    global WORK
    if a.selftest:
        return selftest()
    if a.work:
        WORK = a.work
    if a.out:
        out = Path(a.out).resolve()
        if not a.work or out == DEST.resolve() or out.suffix != ".md":
            print("❌ --out は --work と一緒のときだけ・本物の設計書以外の .md にだけ書けます")
            return 2
        # 大文字小文字だけ違うパスも同じ置き場に書けてしまう（macOS）ので、casefold して比べる
        arch = str(ARCHIVE.resolve()).casefold()
        if str(out).casefold() == arch or str(out).casefold().startswith(arch + "/"):
            print(f"❌ --out は承認の控えの置き場（{ARCHIVE}）の中には書けません")
            return 2
        return write(dest=out)
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
