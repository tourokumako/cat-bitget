#!/usr/bin/env python3
"""gen_audit_docs.py — 監査の依頼書をテンプレから作り、依頼書から結果の骨組みを作り、2つを照らす。

まこさん指示 2026-09-15（逐語）＝「じゃあ、監査の依頼書と結果で項目をそろえて、テンプレ以外では書かないように
  強制すればいいじゃん。」／置き場所＝「案AでOK」（.claude/tools に新しい道具を作る）。

なぜ要るか
  監査レポート CP37 を監査結果のテンプレに当てはめたら、齟齬とヌケモレが多数出た（worklog 20260915 §11）。
  原因の1つ＝依頼書をテンプレから作っていなかった（cp37 の依頼書は CC が手で書いた）。
  gen_audit_request.py は中身の取り出し元が RG-v5 に決め打ちで（102〜109行の SOURCES）、ほかの監査の依頼書を作れない。

テンプレ＝SDK/.claude/audits/inputs/_template.md
  依頼の側＝「## 」の見出しの節。結果の側＝「## 結果ファイルフォーマット」の11節の表。
  ★節の名前はテンプレから読む。この道具に節の名前の一覧を焼かない（下の SECTION_KIND は「どう埋めるか」だけ）。

使い方
  python3 .claude/tools/gen_audit_docs.py request-design <design|impl> --work <工事名>
    → ★2026-09-29（まこさん指示「監査依頼書を自動生成」）＝設計書（.claude/state/acceptance.md）と
      その工事のフォルダ（やることの表.md と逐語のファイル）から、依頼書の元データと依頼書を道具が作る。CC は元データを書かない。
      ★2026-09-30（設計書 point1-one-way-20260930-2）＝--work だけを受ける（元データの JSON から作る古い口は消した）。
      問いは、設計のもとの1行ごと（V）・完成の条件の1行ごと（C）・実装の指示の1件ごと（I）・
      やらないことの1件ごと（N）・CC が決めたことの1件ごと（D）に1つずつ作る。監査の番号（cp）は次の空き番号。
      元データは作業場 SDK/.claude/audits/cp<N>_work/cp<N>_src.gen.md に、依頼書は inputs に書く。
  python3 .claude/tools/gen_audit_docs.py request <元データ.md> <依頼書.md>
    → 元データ（下の形）とテンプレから依頼書を作る。★2026-09-29 から、元データは request-design が作った物だけを受ける
      （1行目の目印と本文のハッシュ値を照らす＝CC が手で書いた元データの口は閉じた）。
  python3 .claude/tools/gen_audit_docs.py result <依頼書.md> <結果.md>
    → 依頼書から結果の骨組み（11節・問いの見出し・事実データと外部検索と自己申告の見出し）を作る。中身は監査が書く。
  python3 .claude/tools/gen_audit_docs.py check <依頼書.md> <結果.md>
    → 2つが1対1で対応しているかを照らす。1件でも食い違えば rc=1。
  python3 .claude/tools/gen_audit_docs.py form <結果.md>
    → 中身を書いた結果が、テンプレの形（修正の指示の6つの欄・書けないもの・「<監査が書く>」の残り）かを見る。
      hook 11（enforce_audit_report_form）が、結果ファイルを書く瞬間に check と同じ判定を掛ける。

inputs に依頼書を書くときの照らし（★いまの監査依頼書ゲート＝require_acceptance_before_impl.sh の691〜772行と同じ）
  この道具は Python の中からファイルを書くので、Write の hook を通らない。守りを減らさないため、道具の中で同じことを見る。
  ①名前に _design_ を含まない依頼書＝設計書（.claude/state/acceptance.md）が承認の印（acceptance.approved）と同じ
  ②名前に _design_ を含む依頼書＝依頼書に「設計書のハッシュ値: <監査の相手の sha256>」の行を入れる
    （監査の相手が作業場の写しの設計書でもよい＝前の版の設計書を監査させる形。まこさん決定 2026-09-15「案A」）
  ③どちらも＝監査に出す前のチェック（pre_audit_check.py --verify）が rc=0

元データの形（CC が書くのは文だけ。ハッシュ値・保存先・件数・並びはプログラムが入れる）
  <!-- 項目: メタ -->                「キー: 値」の行＝日付・task・cp・題・依頼者・監査区分・監査対象タスク・監査の相手
  <!-- 項目: 作業場の指示 -->          無くてよい（auditor 宣言の「この監査の作業場」に入る）
  <!-- 項目: 結論を決める問い -->      「- **問い1**＝…」の行を1つ以上（結果の総合判定で、この名前ごとに答える）
  <!-- 項目: 結論の決め方 -->          無くてよい（無ければ結果ファイルフォーマットの決め方を使う）
  <!-- 項目: この監査の前提 -->        無くてよい
  <!-- 項目: 経緯 -->
  <!-- 項目: 着手前必読 -->
  <!-- 項目: 大目的の注記 -->
  <!-- 項目: 事実データ 名前=… -->      何件でも
  <!-- 項目: 監査対象 -->
  <!-- 項目: 監査対象外 -->
  <!-- 項目: 一般観点の指示 -->          無くてよい
  <!-- 項目: 問い 番号=A1 優先度=A 理由=… 名前=… -->   何件でも（理由と名前は空白を含んでよい。この順に、名前を最後に書く）
  <!-- 項目: 外部検索 名前=… -->        何件でも
  <!-- 項目: 自己申告 -->               1件につき1つ・何件でも
  ★この一覧に無い項目は「テンプレに置き場が無い」として ❌ を出す（rc=1）。

書いてよい先（★この道具は Bash から走らせられるので、書く先を監査の置き場だけに限る）
  依頼書（request）＝①SDK/.claude/audits/inputs/<名前>_audit_request.md（「_」で始まる名前＝テンプレは書かない・
    既に在るファイルは、道具が作ったまま書き替えられておらず、その結果ファイルがまだ無いときだけ上書きする・
    下の照らしに ❌ が1件でもあれば書かない）②SDK/.claude/audits/<何か>_work/ の中の .md
  結果の骨組み（result）＝SDK/.claude/audits/<何か>_work/ の中の .md だけ
    （結果ファイルの置き場に骨組みを置くと、中身の無い結果が hook 11 を通らずに出来てしまうため）。

限界（正直に書く）
  ①依頼書の文の中身が正しいかは見ない（見るのは形と対応だけ）。
  ②プログラムが作る文書と元データの組は、設計書（.claude/state/acceptance.md → 工事のフォルダの やることの表.md）の1組だけを知っている。
  ③この道具自身を書き換えれば無効にできる（git diff には出る）。
  ④恒久71番＝文書を作る道具なので、壊すプログラムと自己テストは付けない。走らせて確かめる。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
AUDITS = os.path.join(SDK, ".claude", "audits")
TEMPLATE = os.path.join(AUDITS, "inputs", "_template.md")
DESIGN = os.path.join(ROOT, ".claude", "state", "acceptance.md")
APPROVED = os.path.join(ROOT, ".claude", "state", "acceptance.approved")
PRE_AUDIT_CHECK = os.path.join(ROOT, ".claude", "tools", "pre_audit_check.py")
INPUT_REQUEST_RE = re.compile(r"/\.claude/audits/inputs/[^/_][^/]*_audit_request\.md$")

# テンプレの依頼の側の見出し（先頭一致）→ どう埋めるか。この表に無い見出しがテンプレに在れば止める。
SECTION_KIND = (
    ("## ⚠️ auditor 宣言", "宣言"),
    ("## 監査依頼メタ情報", "メタ"),
    ("## この監査で答えてほしいこと", "答えてほしいこと"),
    ("## 監査依頼の経緯", "経緯"),
    ("## 着手前必読", "着手前必読"),
    ("## 大目的", "大目的"),
    ("## 監査対象の事実データ", "事実データ"),
    ("## 監査スコープ", "スコープ"),
    ("## 監査観点 (一般", "一般観点"),
    ("## 監査観点 (本監査固有", "問い"),
    ("## 外部検索要請", "外部検索"),
    ("## 依頼を出した CC の自己申告", "自己申告"),
    ("## 結果ファイルフォーマット", "テンプレ"),
    ("## 必ず守ること", "テンプレ"),
    ("## まこさん向け呼びかけ例文", "テンプレ"),
)
KEYS_ONE = ("メタ", "経緯", "着手前必読", "大目的の注記", "監査対象", "監査対象外", "一般観点の指示",
            "作業場の指示", "結論を決める問い", "結論の決め方", "この監査の前提")
CONCLUSION_RE = re.compile(r"^- \*\*(.+?)\*\*＝")
KEYS_MANY = ("事実データ", "問い", "外部検索", "自己申告")
META_KEYS = ("日付", "task", "cp", "題", "依頼者", "監査区分", "監査対象タスク", "監査の相手")
PRIORITIES = ("A", "B", "C", "D")
SEVERITY_FIX = ("Critical", "Major", "Minor")
SEVERITY_PROCESS = ("Process",)
# 結果の節の名前（テンプレの表の太字）→ 骨組みの中身の作り方。表の名前がこの一覧に当たらなければ止める。
RESULT_KIND = (
    ("監査の相手と版", "版"),
    ("監査対象の型宣言", "空"),
    ("監査対象の事実データの確認", "事実データ"),
    ("所見", "所見"),
    ("外部検索", "外部検索"),
    ("依頼を出した CC の自己申告への答え", "自己申告"),
    ("総合判定", "総合判定"),
    ("修正の指示", "修正"),
    ("CC プロセス欠陥対策", "プロセス"),
    ("開いたファイルと行", "空"),
    ("本物のファイルを書き替えていないこと", "空"),
)
# プログラムが作る文書 → その元データ（依頼書の必読に元データの名前が無ければ止める）
# ★2026-09-30（設計書 point1-one-way-20260930-2）＝設計書の元は工事のフォルダの やることの表.md（acceptance_src.json は使わない）
GENERATED = {".claude/state/acceptance.md": "やることの表.md"}
PLACE = "<監査が書く>"
# 結果の骨組みに入れる、監査が埋める所の印の全部（form はどれが残っていても止める）
PLACEHOLDERS = (PLACE, "<PASS / FAIL>", "<YES / NO>", "<GO / CONDITIONAL-GO / NO-GO>", "<件数>")
MARK = "<!-- gen_audit_docs:"
# ★2026-09-29＝request-design（設計書と元データから依頼書の元データを作る口）
GEN_MARK = "<!-- gen_audit_docs request-design"
# ★2026-09-30（設計書 point1-one-way-20260930-2）＝元データの JSON（SRC_JSON）は消した。読むのは工事のフォルダだけ。
PRE_JSON = os.path.join(ROOT, ".claude", "state", "pre_audit_check.json")
KINDS = {"design": ("設計書の監査", "_design"), "impl": ("実装の監査", "_impl")}
# ★2026-09-30（3点目-a・まこさん OK「OK」）＝実装の監査の問いは、設計書と実装の照合の決まった6問だけ。
#   （番号, 優先度, 名前, 優先度の理由, 本文）。本文の {…} は build_design_src が工事の値で埋める。
#   まこさん（2026-09-30）「設計書の通りに自動生成で実装できてるのかを監査で確認してもらうんじゃないのか？」
#   「守りの穴探しは永遠に終わらないから、優先度低いはずだが」＝穴探しの問いは入れない。
IMPL_QUESTIONS = (
    ("Q1", "A", "実装の指示を当てた結果が、実装の後と1文字も同じか",
     "違えば、実装は設計書のとおりに作られていない（自動生成の目的が崩れる）",
     "実装の前（commit {pre}）の対象のファイル（{files}）に、設計書 4-20 の実装の指示（{ni} 件）を番号の順に当てた結果が、"
     "実装の後（commit {post}）と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、"
     "直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。"),
    ("Q2", "A", "実装の指示のどれにも当たらない行（手で書いた疑い）が無いか",
     "在れば、道具でなく人が書いた実装が混ざっている",
     "実装の前（commit {pre}）と実装の後（commit {post}）の差分（{files}）のうち、実装の指示のどれにも当たらない行は在るか。"
     "在れば全部 挙げる。"),
    ("Q3", "A", "当てた記録が、実装の指示の全部と1件ずつ合うか",
     "合わなければ、どの件を道具が当てたかを後から確かめられない",
     "当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:{iter}`）が、実装の指示の {ni} 件と"
     "1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。"
     "「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。"),
    ("Q4", "B", "承認した版の設計書どうしで、実装の指示が同じか",
     "当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない",
     "承認した版の設計書の控え（{archives}）と、いまの設計書の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。"),
    ("Q5", "B", "実装の指示が、やることの表の要件を全部 満たすか",
     "要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない",
     "実装の指示は、やることの表（`{todo}`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・"
     "実装の指示に在るのに要件に無いものは在るか。"),
    ("Q6", "B", "完成の条件が、実装の後に本当に成り立つか",
     "成り立たなければ、承認のときの「済」が根拠にならない",
     "設計書の完成の条件（{nc} 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる: {cmds}"),
)
CP_RE = re.compile(r"_cp(\d+)_audit_(?:request|report)\.md$")
PATH_TOKEN = re.compile(r"`([^`\s]+/[^`\s]*\.(?:md|py|json|jsonl|sh|txt|csv))`")


# ───────────── 共通 ─────────────

def sha256_file(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def repo_path(p: str) -> str:
    p = p.strip().strip("`")
    if p.startswith("SDK/"):
        return os.path.join(SDK, p[4:])
    return os.path.join(ROOT, p)


def rel_of(path: str) -> str:
    return os.path.relpath(os.path.realpath(path), os.path.realpath(ROOT))


def body_strip(lines: list) -> list:
    ls = list(lines)
    while ls and ls[-1].strip() in ("", "---"):
        ls.pop()
    while ls and ls[0].strip() == "":
        ls.pop(0)
    return ls


def split_sections(text: str):
    """「## 」の見出しで分ける（囲み ``` の中は見出しと数えない）。戻り＝(見出しの前の行, [(見出し, 本文の行)])。"""
    head, secs, cur, fence = [], [], None, False
    for ln in text.splitlines():
        if ln.startswith("```"):
            fence = not fence
        if not fence and ln.startswith("## "):
            cur = (ln, [])
            secs.append(cur)
        elif cur is None:
            head.append(ln)
        else:
            cur[1].append(ln)
    return head, secs


def split_mark(text: str):
    """末尾の目印の行を外す。戻り＝(本文, 目印の属性の辞書)。目印が無ければ属性は空。"""
    idx = text.rfind("\n" + MARK)
    if idx < 0:
        return text, {}
    body = text[:idx]
    attrs = dict(re.findall(r"(\S+?)=(\S+)", text[idx + 1:].split("-->")[0]))
    return body, attrs


def out_ok(path: str, kind: str):
    """書いてよい先か。kind＝request（依頼書）／result（結果の骨組み）。戻り＝(よいか, 理由)。
    ★結果の骨組みは作業場にだけ書く＝結果ファイルの置き場（audits の *_audit_report.md）に骨組みを置くと、
      中身の無い結果が hook 11（テンプレの形の照らし）を通らずに出来てしまうため。"""
    p = os.path.realpath(path)
    a = os.path.realpath(AUDITS)
    if not p.startswith(a + os.sep):
        return False, "監査の置き場（SDK/.claude/audits）の外"
    parts = os.path.relpath(p, a).split(os.sep)
    if (kind == "request" and len(parts) == 2 and parts[0] == "inputs"
            and parts[1].endswith("_audit_request.md") and not parts[1].startswith("_")):
        if not os.path.exists(p):
            return True, ""
        # 既に在る依頼書を上書きしてよいのは、①道具が作ったまま書き替えられていない ②その依頼書の結果ファイルがまだ無い、の両方のときだけ
        report = os.path.join(a, parts[1].replace("_audit_request.md", "_audit_report.md"))
        body, mark = split_mark(open(p, encoding="utf-8").read())
        untouched = bool(mark.get("body_sha256")) and mark.get("body_sha256") == sha256_text(body)
        if untouched and not os.path.exists(report):
            return True, ""
        return False, ("既に在る依頼書は上書きしない（上書きしてよいのは、道具が作ったまま書き替えられておらず、"
                       "結果ファイルがまだ無いときだけ）")
    if len(parts) >= 2 and parts[0].endswith("_work") and p.endswith(".md"):
        return True, ""
    if kind == "request":
        return False, "依頼書を書いてよい先（inputs の <名前>_audit_request.md・作業場の .md）ではない"
    return False, "結果の骨組みを書いてよい先（作業場 <何か>_work の .md）ではない"


def write_out(path: str, text: str, kind: str) -> bool:
    ok, why = out_ok(path, kind)
    if not ok:
        print(f"❌ 書かなかった: {path}（{why}）")
        return False
    os.makedirs(os.path.dirname(os.path.realpath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"書いた: {rel_of(path)}")
    return True


def inputs_gate(out_path: str) -> list:
    """inputs に依頼書を書くときの照らし（いまの監査依頼書ゲートと同じ）。inputs でなければ何も見ない。"""
    if not INPUT_REQUEST_RE.search(os.path.realpath(out_path)):
        return []
    errs = []
    if "_design_" not in os.path.basename(out_path):
        now = sha256_file(DESIGN) if os.path.isfile(DESIGN) else ""
        want = open(APPROVED, encoding="utf-8").read().strip() if os.path.isfile(APPROVED) else ""
        if not want or now != want:
            errs.append(f"設計書が承認と食い違うので、依頼書を作れない（承認 {want[:16]}… ／ いまの設計書 {now[:16]}…）")
    if os.path.isfile(PRE_AUDIT_CHECK):
        r = subprocess.run([sys.executable, PRE_AUDIT_CHECK, "--verify"], capture_output=True, text=True)
        if r.returncode != 0:
            errs.append("監査に出す前のチェック（pre_audit_check.py --verify）が通っていない。"
                        "python3 .claude/tools/pre_audit_check.py --run を打ち、全部 rc=0 にしてから作る")
    return errs


def kind_of(head: str, table) -> str | None:
    for pre, kind in table:
        if head.startswith(pre):
            return kind
    return None


# ───────────── 元データ ─────────────

BLOCK_RE = re.compile(r"^<!--\s*項目:\s*(.*?)\s*-->\s*$")


def parse_attrs(s: str) -> dict:
    s = s.strip()
    attrs = {}
    if "名前=" in s:
        s, name = s.split("名前=", 1)
        attrs["名前"] = name.strip()
    if "理由=" in s:
        s, why = s.split("理由=", 1)
        attrs["理由"] = why.strip()
    for tok in s.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            attrs[k] = v
    return attrs


def parse_src(path: str):
    errs, blocks, cur = [], [], None
    for ln in open(path, encoding="utf-8").read().splitlines():
        m = BLOCK_RE.match(ln)
        if m:
            # 項目の名前は、最初の「属性=値」の手前まで（名前に空白が在ってもよい）
            key_attr = re.split(r"\s+(?=\S+=)", m.group(1), maxsplit=1)
            cur = {"key": key_attr[0].strip(), "attrs": parse_attrs(key_attr[1] if len(key_attr) > 1 else ""),
                   "lines": []}
            blocks.append(cur)
        elif cur is not None:
            cur["lines"].append(ln)
    src = {k: None for k in KEYS_ONE}
    for k in KEYS_MANY:
        src[k] = []
    for b in blocks:
        body = "\n".join(body_strip(b["lines"]))
        if b["key"] in KEYS_ONE:
            if src[b["key"]] is not None:
                errs.append(f"項目「{b['key']}」が2つ在る")
            src[b["key"]] = body
        elif b["key"] in KEYS_MANY:
            src[b["key"]].append({"attrs": b["attrs"], "body": body})
        else:
            errs.append(f"項目「{b['key']}」はテンプレに置き場が無い（{b['attrs'].get('名前', '')}）")
    meta = {}
    for ln in (src["メタ"] or "").splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1)
            meta[k.strip()] = v.strip()
    return src, meta, errs


# ───────────── 依頼書を作る ─────────────

def gen_mark_problem(src_path: str) -> str:
    """元データが request-design の作った物のままか。戻り＝問題の文（無ければ空）。"""
    text = open(src_path, encoding="utf-8").read()
    first, _, rest = text.partition("\n")
    if not first.startswith(GEN_MARK):
        return ("元データの1行目に request-design の目印が無い＝CC が手で書いた元データの口は閉じました"
                "（python3 .claude/tools/gen_audit_docs.py request-design <design|impl> で作る）")
    want = dict(re.findall(r"(\S+?)=(\S+)", first)).get("body_sha256", "")
    if want != sha256_text(rest):
        return "元データが、request-design で作った後に書き替えられている（本文のハッシュ値が目印と違う）"
    return ""


def build_request(src_path: str, out_path: str) -> int:
    src, meta, errs = parse_src(src_path)
    _gm = gen_mark_problem(src_path)
    if _gm:
        # ★口を閉じる＝どの置き場にも1バイトも書かない（直す前は inputs 以外の置き場なら ❌ でも書いていた）
        print(f"❌ {_gm}")
        print(f"❌ 書かなかった: {out_path}")
        return 1
    for k in META_KEYS:
        if not meta.get(k):
            errs.append(f"メタに「{k}」が無い")
    for k in ("経緯", "着手前必読", "大目的の注記", "監査対象", "監査対象外"):
        if not src[k]:
            errs.append(f"項目「{k}」が無い")
    for k in ("事実データ", "問い", "外部検索"):
        if not src[k]:
            errs.append(f"項目「{k}」が1件も無い")
    if not [ln for ln in (src["結論を決める問い"] or "").splitlines() if CONCLUSION_RE.match(ln)]:
        errs.append("項目「結論を決める問い」に「- **問い1**＝…」の形の行が1つも無い")
    ids = []
    for q in src["問い"]:
        a = q["attrs"]
        if not a.get("番号") or not a.get("名前"):
            errs.append(f"問いに番号か名前が無い（{a}）")
        if not a.get("理由"):
            errs.append(f"問い {a.get('番号')} に優先度の理由（理由=…）が無い")
        if a.get("優先度") not in PRIORITIES:
            errs.append(f"問い {a.get('番号')} の優先度が A〜D でない（{a.get('優先度')}）")
        if a.get("番号") in ids:
            errs.append(f"問いの番号 {a.get('番号')} が2つ在る")
        ids.append(a.get("番号"))
    for k in ("事実データ", "外部検索"):
        for it in src[k]:
            if not it["attrs"].get("名前"):
                errs.append(f"{k} に名前が無い")
    target = meta.get("監査の相手", "")
    tpath = repo_path(target) if target else ""
    if target and not os.path.isfile(tpath):
        errs.append(f"監査の相手のファイルが無い: {target}")
    reading = src["着手前必読"] or ""
    for tok in PATH_TOKEN.findall(reading):
        if not os.path.exists(repo_path(tok)):
            errs.append(f"着手前必読のファイルが無い: {tok}")
    for gen, raw in GENERATED.items():
        # 作業場に写した前の版の設計書でも同じ（名前で見る）
        # ★2026-09-29（135回目）＝工事のフォルダ（--work）から作った設計書は、元が やることの表.md（acceptance_src.json は使わない）
        if os.path.basename(target) == os.path.basename(gen) and raw not in reading \
                and not (os.path.basename(gen) == "acceptance.md" and "/verbatim/" in reading and "やることの表.md" in reading):
            errs.append(f"監査の相手 {gen} はプログラムが作る文書。着手前必読に元データ {raw} が無い")

    if not os.path.isfile(TEMPLATE):
        print(f"❌ テンプレが無い: {TEMPLATE}")
        return 1
    _, secs = split_sections(open(TEMPLATE, encoding="utf-8").read())
    base = f"{meta.get('日付', '')}_{meta.get('task', '')}_{meta.get('cp', '')}"

    # ★2026-09-29（まこさん指摘「監査の依頼内容が変じゃないか？」・worklog 20260929 §40 の10・11・§41）
    #   ①テンプレの「N 件」を、着手前必読の表の行の数で埋める ②結果と依頼書の置き場を、根からの全パスにそろえる
    #   （直す前は SDK からの相対と全パスが混ざり、根で起動した監査が置き場を取り違えうる）
    #   ③売買のロジックに触らない工事（メタ「売買に触るか: いいえ」）では、トレードの外部認知を求める守則を出さない
    # ★2026-09-30（3点目-a）＝必読はテンプレの形（番号つきの行）。古い形（表の行）も数える
    n_read = sum(1 for ln in (src["着手前必読"] or "").splitlines() if re.match(r"^(?:\|\s*\d+\s*\||\d+\. )", ln))
    no_trade = meta.get("売買に触るか", "") == "いいえ"

    def rep(s: str) -> str:
        if no_trade and "Crypto futures" in s:
            return "- この監査の相手は売買のロジックに触らない道具の直しなので、トレードの外部認知は問わない"
        if s.startswith(".claude/audits/"):
            s = "v3-bitget-api-sdk/bitget-python-sdk-api/" + s
        return (s.replace("<本依頼書のパス>", f"v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/{base}_audit_request.md")
                .replace("`.claude/audits/", "`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/")
                .replace("N 件", f"{n_read} 件")
                .replace("2026-XX-XX_<task>_cpN", base).replace("<cpN>", meta.get("cp", "")))

    out = [f"# 【監査依頼】{meta.get('題', '')}", ""]
    for head, lines in secs:
        kind = kind_of(head, SECTION_KIND)
        body = body_strip(lines)
        if kind is None:
            errs.append(f"テンプレの見出し「{head}」の埋め方が道具に無い（テンプレが変わった）")
            continue
        out += [rep(head), ""]                      # ★見出しの「N 件」も埋める（2026-09-29・自己テスト T9 で見つけた）
        if kind == "テンプレ":
            out += [rep(x) for x in body]
        elif kind == "宣言":
            for x in body:
                if x.startswith("<作業場のパス"):
                    out += (src["作業場の指示"] or "（この監査だけの指示は無い）").splitlines()
                else:
                    out.append(rep(x))
        elif kind == "答えてほしいこと":
            fill = {"### 結論を決める問い": src["結論を決める問い"] or "",
                    "### 結論の決め方": src["結論の決め方"]
                    or "（この監査だけの決め方は無い。結果ファイルフォーマットの「結論の決め方」を使う）",
                    "### この監査の前提": src["この監査の前提"] or "（無い）"}
            heads = [x for x in body if x.startswith("### ")]
            if heads != list(fill):
                errs.append(f"テンプレの「この監査で答えてほしいこと」の小見出しが道具と違う（{heads}）")
            cur = None
            for x in body:
                if x.startswith("### "):
                    cur = x
                    out += [x, ""] + fill.get(x, "").splitlines()
                elif cur == "### 結論を決める問い" and x.startswith("(結論を決めるのは"):
                    # ★2026-09-30＝空の行を二重に足さない（直す前は、前の行が空でも "" を足し、空の行が2つ続いた）
                    out += ([] if out and out[-1] == "" else [""]) + [x]
                elif x.strip() == "":
                    if out and out[-1] != "":
                        out.append("")
        elif kind == "メタ":
            h = sha256_file(tpath) if tpath and os.path.isfile(tpath) else "（ファイルが無い）"
            out += [f"- 依頼日: {meta.get('日付', '')}",
                    f"- 依頼者: {meta.get('依頼者', '')}",
                    f"- 監査区分: {meta.get('監査区分', '')}",
                    f"- 監査対象タスク: {meta.get('監査対象タスク', '')}",
                    f"- 監査の相手と版: `{target}` ／ ハッシュ値 {h}",
                    f"- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/{base}_audit_report.md`",
                    f"- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/{base}_audit_request.md`"]
            if "_design_" in os.path.basename(out_path):
                out.append(f"- 設計書のハッシュ値: {h}")
        elif kind == "経緯":
            out += (src["経緯"] or "").splitlines()
        elif kind == "着手前必読":
            out += reading.splitlines()
            notes = [x for x in body if x.startswith("★")]
            if notes:
                out += [""] + notes
        elif kind == "大目的":
            for x in body:
                if x.startswith("⚠️ 本監査スコープ"):
                    out += (src["大目的の注記"] or "").splitlines()
                else:
                    out.append(x)
        elif kind == "事実データ":
            for it in src["事実データ"]:
                out += [f"### {it['attrs'].get('名前', '')}", ""] + it["body"].splitlines() + [""]
        elif kind == "スコープ":
            heads = [x for x in body if x.startswith("### ")]
            if len(heads) != 2:
                errs.append("テンプレの監査スコープに「### 」の見出しが2つ無い")
                heads = ["### 監査対象", "### 監査対象外"]
            out += [heads[0], ""] + (src["監査対象"] or "").splitlines() + [""]
            out += [heads[1], ""] + (src["監査対象外"] or "").splitlines()
        elif kind == "一般観点":
            for x in body:
                if x.startswith("(各観点を"):
                    if src["一般観点の指示"]:
                        out += src["一般観点の指示"].splitlines()
                else:
                    out.append(x)
        elif kind == "問い":
            out += [x for x in body if x.startswith("★")] + [""]
            for q in src["問い"]:
                a = q["attrs"]
                out += [f"### {a.get('番号', '')} — {a.get('名前', '')}（優先度 {a.get('優先度', '')}）", "",
                        f"**優先度の理由**＝{a.get('理由', '')}", ""]
                out += q["body"].splitlines() + [""]
        elif kind == "外部検索":
            for x in body:
                if x.startswith("件数:") or x.startswith("### "):
                    break
                out.append(x)
            n = len(src["外部検索"])
            out += [f"件数: {n} 件 (結果の外部検索は、この件数の検索対象に1つずつ答える)", "", "### 検索対象", ""]
            # ★2026-09-30（3点目-a）＝テンプレの形（番号つきの「トピック・クエリ案・期待発見」）。
            #   直す前は検索ごとに「### 検索 N —」の見出しを立てていた（worklog 20260929 §67 の③）
            for i, it in enumerate(src["外部検索"], 1):
                q = " ".join(it["body"].split()) or it["attrs"].get("名前", "")
                out += [f"{i}. **{it['attrs'].get('名前', '')}**:",
                        f"   - クエリ案: {q}",
                        "   - 期待発見: URL と、使った逐語（無ければ「見つからなかった」と書く）"]
            out.append("")
        elif kind == "自己申告":
            for i, it in enumerate(src["自己申告"], 1):
                ls = it["body"].splitlines() or [""]
                out.append(f"{i}. {ls[0]}")
                out += ["   " + x if x.strip() else x for x in ls[1:]]
            out += [""] + [x for x in body if x.startswith("(結果は")]
        out = body_strip(out) + ["", "---", ""]

    text = "\n".join(body_strip(out)) + "\n"
    text += (f"\n{MARK} request src={rel_of(src_path)} src_sha256={sha256_file(src_path)} "
             f"body_sha256={sha256_text(text)} -->\n")
    errs += inputs_gate(out_path)
    for e in errs:
        print(f"❌ {e}")
    if errs and INPUT_REQUEST_RE.search(os.path.realpath(out_path)):
        print(f"❌ 書かなかった: {out_path}（inputs には ❌ が1件も無いときだけ書く）")
        wrote = False
    else:
        wrote = write_out(out_path, text, "request")
    if not errs and wrote:
        print(f"✅ 依頼書を作った（問い {len(src['問い'])} 件・事実データ {len(src['事実データ'])} 件・"
              f"外部検索 {len(src['外部検索'])} 件・自己申告 {len(src['自己申告'])} 件）")
    return 0 if (not errs and wrote) else 1


# ───────────── 設計書から依頼書の元データを作る（2026-09-29）─────────────
#   まこさん指示（2026-09-29・逐語）「監査依頼書を自動生成」「OKなのですべて完璧に上記チャットの１から５の各要件の通りに修正をすること」。
#   ★CC は依頼書の元データを1文字も書かない。中身は全部、設計書（acceptance.md）と工事のフォルダから作る。
#   ★設計のもとの行と対応の表は gen_acceptance.py の関数で読む（同じ判定を2か所に書かない・抜けが在れば止まる）。

def next_cp() -> int:
    """監査の番号の次の空き番号（inputs と audits の依頼書・結果の名前から数える）。"""
    nums = [0]
    for d in (AUDITS, os.path.join(AUDITS, "inputs")):
        for n in os.listdir(d):
            m = CP_RE.search(n)
            if m:
                nums.append(int(m.group(1)))
    return max(nums) + 1


def repo_ref(p: str) -> str:
    """設計書のパス（リポジトリ直下か SDK からの相対）を、依頼書の書き方（SDK/… か直下）に直す。無ければ空。"""
    p = (p or "").strip().strip("`")
    if os.path.exists(os.path.join(ROOT, p)):
        return p
    if os.path.exists(os.path.join(SDK, p)):
        return "SDK/" + p
    return ""


def _one_line(s) -> str:
    """元データの1行に入れる形（改行を ⏎ に・目印の区切りを壊さない）。"""
    return str(s if s is not None else "").replace("\n", " ⏎ ").replace("-->", "―>").strip()


def _attr(s) -> str:
    """問いの属性（理由・名前）に入れる形（属性の区切りの語と = を使わない）。"""
    return _one_line(s).replace("=", "＝").replace("名前＝", "名前：").replace("理由＝", "理由：")



def _speaker(gv, name: str) -> str:
    """逐語のファイルの話し手（控えの who）から、誰の文かを言葉にする。"""
    try:
        _t, m = gv.paths(name)
        who = set(json.load(open(m, encoding="utf-8")).get("who") or [])
    except Exception:                                        # noqa: BLE001
        who = set()
    if who == {"まこさん"}:
        return "まこさんの発言"
    if who == {"CC"}:
        return "まこさんが OK した CC の文"
    return "まこさんの発言と CC の文"


def _impl_evidence(iter_: str) -> dict:
    """実装の監査の材料＝承認の控え・実装の前と後の commit・当てた記録（道具が実物から数える）。

    ★2026-09-30（3点目-a・まこさん OK「OK」）＝実装の監査は「設計書のとおりに、道具が実装を作れているか」だけを問う。
      その照合に要る材料（どの版の設計書で当てたか・実装の前と後・当てた記録）を、CC が書かずに実物から出す。
    """
    import glob
    import subprocess
    arc = os.path.join(SDK, ".claude", "ratchet", "acceptance_archive")
    archives = sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(arc, f"{glob.escape(iter_)}*.md"))
                      if re.fullmatch(rf"{re.escape(iter_)}(\.\d+)?\.md", os.path.basename(p)))
    post = pre = ""
    if archives:
        r = subprocess.run(["git", "log", "-1", "--format=%h %p", "--", os.path.join(ROOT, archives[0])],
                           cwd=ROOT, capture_output=True, text=True)
        parts = r.stdout.split()
        if len(parts) >= 2:
            post, pre = parts[0], parts[1]
    try:
        rows = json.load(open(os.path.join(AUDITS, "applied_fixes.json"), encoding="utf-8")).get("applied") or []
    except Exception:                                        # noqa: BLE001
        rows = []
    applied = [r for r in rows if isinstance(r, dict) and r.get("report") == f"design:{iter_}"]
    return {"archives": archives, "pre": pre, "post": post, "applied": applied}


def build_design_src(kind: str, cp: int, work: str, design_path: str = None) -> tuple:
    """設計書と元データから、依頼書の元データ（本文）を作る。戻り＝(本文, 依頼書の名前の頭)。

    ★2026-09-29（まこさん指摘「監査の依頼内容が変じゃないか？」・worklog 20260929 §40〜§42）で直したこと
      ①工事の相手を見ずに engine_tuner の文（前提の5・大目的・監査に出す前のチェック）を出さない
      ②設計書で非該当の節を監査の相手に入れない ③設計のもとの問いは S の番号にし、優先度を行の中身で決める
      ④逐語のファイルの話し手を分けて書く ⑤先に直した道具の変更に問い（G）を作る
      ⑥壊すプログラムの無い完成の条件は、無いことを前提に問う ⑦やらないことの問いに「見てほしいこと」を付ける
      ⑧外部検索は元データの「外部検索」（何を調べるかは手で決める）から作り、無ければ止める
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_acceptance as ga                      # ★設計のもとの読み方は1か所（抜けが在れば SystemExit）
    # ★2026-09-29（135回目）＝設計書の道具と同じ読み方で工事のフォルダから読む。
    # ★2026-09-30（設計書 point1-one-way-20260930-2）＝工事のフォルダの1本だけ（元データの JSON の分かれ道を消した）。
    if not work:
        raise SystemExit("工事名がありません（request-design は --work <工事名> だけを受ける）")
    ga.WORK = work
    d = ga.src_from_work(work)
    wdir = ga.gv.work_dir(work)
    src_file = str(wdir / ga.TODO_MD)
    src_label = f"工事のフォルダ `{os.path.relpath(str(wdir), ROOT)}`（やることの表.md と、まこさんが OK した案の逐語）"
    md = open(design_path or DESIGN, encoding="utf-8").read()
    engine = ga.touches_trading(d)
    label, suffix = KINDS[kind]
    iter_ = d.get("iter", "")
    if f'iter="{iter_}"' not in md:
        raise SystemExit(f"設計書の目印（ARC iter）が元データの iter（{iter_}）と違う＝元データから作り直した設計書ではない")
    title = d.get("設計書の題", "")
    today = time.strftime("%Y-%m-%d")
    task = iter_.replace("-", "_") + suffix
    base = f"{today}_{task}_cp{cp}"
    rows = ga.source_rows(d)
    bad = ga.match_problems(d, rows)
    if bad:
        raise SystemExit("設計のもとの対応が足りない（設計書を作る道具と同じ判定）:\n  " + "\n  ".join(bad))
    impl = d.get("実装の指示") or []
    conds = d.get("完成の条件") or []
    nots = d.get("やらないこと") or []
    src = d.get("設計のもと") or {}
    names = [str(n) for n in (src.get("逐語のファイル") or [])]
    todos = [str(n) for n in (src.get("やることの番号") or [])]
    B = []
    add = B.append
    add("<!-- 項目: メタ -->")
    add(f"日付: {today}")
    add(f"task: {task}")
    add(f"cp: cp{cp}")
    add(f"題: CP{cp} — {_one_line(title)}（{label}）")
    add("依頼者: CC（起案者）")
    add(f"監査区分: {label}")
    add(f"監査対象タスク: {'・'.join(todos) or '（やることの番号なし）'}／設計書 {iter_}")
    add("監査の相手: .claude/state/acceptance.md")
    add(f"売買に触るか: {'はい' if engine else 'いいえ'}")
    add("")
    speakers = {n: _speaker(ga.gv, n) for n in names}
    ev = _impl_evidence(iter_) if kind == "impl" else {}
    searches = d.get("外部検索") or []
    if not searches:
        raise SystemExit("元データに「外部検索」（何を調べるか）が無い＝何を調べるかは手で決める（worklog 20260929 §42）。"
                         "形＝[{\"名前\": \"…\", \"中身\": \"…\"}]")
    add("<!-- 項目: 作業場の指示 -->")
    add(f"**★この監査は「{label}」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。")
    add("")
    add(f"**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp{cp}_work/` に作ってください。")
    add("")
    # ★2026-09-29（135回目・まこさん「CCはこの監査依頼書を見て正確に監査できるのか？」「構造がぐちゃぐちゃで汚いまま」）
    #   ＝工事のフォルダから作った設計書の監査は、割り当ての表の確かめだけにする（問い S・G・C・I・N・D は出さない）
    # ★2026-09-30（設計書 point1-one-way-20260930-2）＝工事のフォルダの1本だけ＝設計書の監査はいつも割り当ての表の確かめ
    only_table = kind == "design"
    if only_table:
        add("**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました（CC は依頼書の文を書いていません）。**"
            "問いは、やることの表の「手書きと自動の割り当て」の表の1行ごと（W）に1つずつ在ります。")
    else:
        # ★2026-09-30（3点目-a・まこさん OK）＝実装の監査の問いは、設計書と実装の照合の決まった6問（Q1〜Q6）だけ。
        #   直す前は設計のもとの1行ずつ（S）ほかを問いにし、cp53 で問いが686件（うち S が640件）になった。
        add("**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました（CC は依頼書の文を書いていません）。**"
            "問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）です。")
    add("")
    add("<!-- 項目: 結論を決める問い -->")
    ni, nc = len(impl), len(conds)
    rng = lambda p, n: f"{p}01〜{p}{n:02d}" if n else "（無い）"     # noqa: E731
    # ★2026-09-29（135回目・まこさん指示「設計書の項目ごとに手書きと自動生成に仕分けた表があったよね？ その通りになってるかを見てもらえよ」）
    #   ＝工事のフォルダから作った設計書は、やることの表の「手書きと自動の割り当て」の表の1行ごとに問い（W）を作り、問い1 にする
    tl = (ga.gv.work_dir(work) / ga.TODO_MD).read_text(encoding="utf-8").splitlines()
    sec = ga._sections(tl, re.compile(r"^##\s+(?!#)(.+)$"))
    body = next((v for k, v in sec.items() if k.startswith("手書きと自動の割り当て")), None)
    if body is None:
        raise SystemExit(f"{ga.TODO_MD} に「## 手書きと自動の割り当て」の節が無い（fail-closed）")
    _bad: list = []
    assign = ga._md_table(body, ("項目", "手書き／自動"), "手書きと自動の割り当て", _bad)
    if _bad or not assign:
        raise SystemExit("手書きと自動の割り当ての表を読めない（fail-closed）: " + "／".join(_bad))
    if kind == "design":
        add(f"- **問い1**＝設計書が、やることの表の「手書きと自動の割り当て」の表（問い {rng('W', len(assign))}）の"
            "とおりに作られているか。手書きの項目は やることの表の「手書きの項目」の文と1文字も違わず、"
            "自動の項目は実物か、まこさんが OK した案の逐語から写した文だけで、CC が書いた文が無いか。"
            "1行でも割り当てと違えば NO。")
        add("")
        # ★2026-09-30（3点目-a）＝「結論を決めるのは、この問いだけ」はテンプレの文が続くので、ここでは書かない（二重になった）
        add("<!-- 項目: 結論の決め方 -->")
        add("- **GO**＝問い1 が YES で、Critical が0件。")
        add("- **CONDITIONAL-GO**＝問い1 が YES で、Critical が在る（直せば先に進める）。")
        add("- **NO-GO**＝問い1 が NO。割り当てと違う項目を、設計書の行と やることの表・逐語の行で示してください。")
        add("")
    else:
        add(f"- **問い1**＝設計書の実装の指示（{ni} 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。"
            "実装が実装の指示と1文字でも違う・手で書いた行が在る・実装の指示が1件でも抜けていれば NO。")
        add("")
        add("<!-- 項目: 結論の決め方 -->")
        add("- **GO**＝問い1 が YES で、Critical が0件。")
        add("- **CONDITIONAL-GO**＝問い1 が YES で、Critical が在る（直せば先に進める）。")
        add("- **NO-GO**＝問い1 が NO。違う所を、設計書の実装の指示の番号と実物の行で示してください。")
        add("")
    add("<!-- 項目: この監査の前提 -->")
    add("1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。")
    add("2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。")
    add(f"3. **修正の指示は、設計書の元（{src_label}）に対して書いてください**（設計書はプログラムが作るので直接は書けない）。")
    add("4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。")
    if engine:
        add("5. **net は M2-L まで使いません**（まこさん決定 2026-09-01）。")
    add("")
    add("<!-- 項目: 経緯 -->")
    add(f"1. 設計書 `{iter_}`（{_one_line(title)}）は、{src_label} から `gen_acceptance.py` が作りました。")
    add(f"2. 設計のもと（やることの番号 {'・'.join(todos) or '無し'}・逐語のファイル {'・'.join(names) or '無し'}）は、"
        "設計書の §0-1 に道具が写しました（CC は写していません）。逐語のファイルは `gen_verbatim.py` がやり取りの記録から抜き出したものです。")
    add("3. この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました（CC は依頼書の元データを書いていません）。")
    if kind == "impl":
        add("4. 承認の印（`acceptance.approved`）は、いまの設計書の sha256 と同じです（同じでなければ、この依頼書は作れません）。")
        arcs = ev.get("archives") or []
        add(f"5. 承認した版の設計書の控えは {len(arcs)} 本（{'・'.join('`' + a + '`' for a in arcs) or '無し'}）。"
            f"当てる道具が当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:{iter_}`）は {len(ev.get('applied') or [])} 件。")
        add(f"6. 実装の前＝commit {ev.get('pre') or '（まだ commit していない）'} ／ 実装の後＝commit {ev.get('post') or '（まだ commit していない）'}"
            "（承認の控えを入れた commit と、その親を git から読んだ）。")
    add("")
    add("<!-- 項目: 着手前必読 -->")
    add("**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。")
    add("")
    reads = [(".claude/state/acceptance.md", "監査の相手（設計書・プログラムが作った）")]
    reads += [(os.path.relpath(src_file, ROOT), "設計書の元（やることの表＝手書きの5項目と割り当ての表）"),
              (os.path.relpath(str(ga.gv.work_dir(work) / "要件のまとめ.md"), ROOT), "要件のまとめ（まこさんの逐語と OK された案）")]
    # ★2026-09-29＝置き場は工事ごとのフォルダ（逐語の道具が名前を解決する・文字で組まない）
    reads += [(str(ga.gv.paths(n)[0].relative_to(ROOT)), f"{speakers[n]}（逐語・gen_verbatim.py が記録から抜き出した）") for n in names]
    if todos:
        reads.append(("SDK/.claude/ratchet/m2_todo.json", f"やることリスト（番号 {'・'.join(todos)} の行）"))
    if kind == "impl":
        # ★2026-09-30（3点目-a）＝実装の監査の照合に要るもの（承認した版の控え・当てた記録）
        # ★どの版で当てたかは道具には分からない（2回目の承認の版は実装の後に作る）＝Q4 で照らしてもらう
        reads += [(a, "承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）") for a in (ev.get("archives") or [])]
        reads.append(("SDK/.claude/audits/applied_fixes.json", f"当てた記録（名前 design:{iter_} の行）"))
    # ★必読＝設計書・元データ・逐語のファイル・やることの行・直す相手（TARGET・NEW_FILE）の全部（OK をもらった提案の26行目）
    for p in d.get("TARGET") or []:
        r = repo_ref(p)
        reads.append((r, "直す相手") if r else (None, f"直す相手（{p}＝いまは無い）"))
    for p in d.get("NEW_FILE") or []:
        r = repo_ref(p)
        reads.append((r, "新しく作るファイル（もう在る）") if r else (None, f"新しく作るファイル（{p}＝まだ無い）"))
    seen = set()
    i = 0
    for p, why in reads:
        if p and p in seen:
            continue
        seen.add(p)
        i += 1
        # ★2026-09-30（3点目-a）＝テンプレの形（番号つきの「パス — 1行要約」）。直す前は表だった（worklog 20260929 §67 の②）
        add(f"{i}. {'`' + p + '`' if p else '—'} — {why}")
    add("")
    add("<!-- 項目: 大目的の注記 -->")
    # ★2026-09-30（3点目-a）＝テンプレの形（⚠️ 本監査スコープ = …）。守りの穴探しは対象外（まこさん 2026-09-30
    #   「守りの穴探しは永遠に終わらないから、優先度低いはずだが」・恒久65番）
    scope = ("設計書が、やることの表の「手書きと自動の割り当て」の表のとおりに作られているか" if only_table
             else f"設計書 `{iter_}` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）")
    add(f"⚠️ 本監査スコープ = {scope}。守りの穴探し（すり抜けの道を新しく探すこと）は対象外"
        "（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。")
    add("")
    if engine:
        add("engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」です"
            f"（まこさん確定 2026-08-06）。この監査の範囲は、設計書 `{iter_}` の中身です。")
    else:
        # ★2026-09-30（3点目-a）＝範囲は上の「⚠️ 本監査スコープ」の1行だけに書く（直す前は、ここに別の範囲を書いて食い違った）
        add("この監査の相手は、売買のロジックに触らない道具の直しです（直す相手 TARGET に scripts/priority_rebuild も engine_tuner も無い）。")
    add("")
    if only_table:
        add(f"<!-- 項目: 事実データ 名前=手書きと自動の割り当ての表（{ga.TODO_MD}・まこさんが OK した表） -->")
        add("| 項目 | 手書き／自動 |")
        add("|---|---|")
        for r in assign:
            add(f"| {_one_line(r['項目'])} | {_one_line(r['手書き／自動'])} |")
    else:
        # ★2026-09-30（3点目-a・まこさん OK）＝実装の監査の事実データ＝実装の指示の一覧と、当てた記録（どちらも実物から）
        add("<!-- 項目: 事実データ 名前=設計書の実装の指示の一覧（4-20・当てる道具が当てる相手） -->")
        add("| 番号 | 対象のファイル | 直す箇所 | 種類 |")
        add("|---|---|---|---|")
        for it in impl:
            add(f"| {_one_line(it.get('番号'))} | `{_one_line(it.get('対象のファイル'))}` | "
                f"{_one_line(it.get('直す箇所', 'なし'))} | {_one_line(it.get('種類', '直した後の文字'))} |")
        if not impl:
            add("| — | （設計書に実装の指示が無い） | — | — |")
        add("")
        add(f"<!-- 項目: 事実データ 名前=当てた記録（applied_fixes.json の名前 design:{_attr(iter_)}） -->")
        add("| 番号 | 対象のファイル | 当て方 | 時刻 |")
        add("|---|---|---|---|")
        for r in ev.get("applied") or []:
            add(f"| {_one_line(r.get('num'))} | `{_one_line(r.get('file'))}` | {_one_line(r.get('how'))} | {_one_line(r.get('at'))} |")
        if not ev.get("applied"):
            add("| — | （当てた記録が無い） | — | — |")
    add("")
    if only_table:
        add("<!-- 項目: 事実データ 名前=監査に出す前のチェック（pre_audit_check.json） -->")
        dmt = os.path.getmtime(design_path or DESIGN)
        if not engine:
            add("非該当（pre_audit_check.json は売買のロジックの道具の検査。この工事は売買のロジックに触らない）")
        elif not os.path.isfile(PRE_JSON):
            add("（pre_audit_check.json が無い）")
        elif os.path.getmtime(PRE_JSON) <= dmt:
            add("（pre_audit_check.json は設計書より前に走らせたもの＝この設計書の検査ではないので載せない。走らせ直してから依頼書を作り直す）")
        else:
            pj = json.load(open(PRE_JSON, encoding="utf-8"))
            add(f"走らせた時刻＝{pj.get('at', '')}")
            add("")
            add("| コマンド | 種類 | 終了コード |")
            add("|---|---|---|")
            for r in pj.get("rows") or []:
                add(f"| `{_one_line(r.get('cmd'))}` | {_one_line(r.get('kind'))} | {r.get('rc')} |")
        add("")
    add("<!-- 項目: 監査対象 -->")
    if only_table:
        for r in assign:
            add(f"- {_one_line(r['項目'])}（{_one_line(r['手書き／自動'])}）")
    else:
        # ★2026-09-30（3点目-a）＝照合の観点（下の Q1〜Q6 と同じ）。直す前は設計書の見出し46個をそのまま並べた（worklog 20260929 §67 の④）
        for q in IMPL_QUESTIONS:
            add(f"- {q[0]}：{q[2]}")
    add("")
    add("<!-- 項目: 監査対象外 -->")
    if only_table:
        add("- 設計書の中身そのものが正しいか（この監査は、手書き／自動の表のとおりに作られているかだけを見る）")
    add("- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。"
        "穴は作業が実際に止まったときに直す")
    for r in nots:
        add(f"- {_one_line(r.get('中身'))}（{_one_line(r.get('理由'))}）")
    add("")
    for n, r in enumerate(assign if only_table else [], 1):
        hand = r["手書き／自動"].strip() == "手書き"
        add(f"<!-- 項目: 問い 番号=W{n:02d} 優先度=A 理由=割り当てと違えば、CC の手書きが自動の項目に混ざる（自動生成の目的が崩れる） "
            f"名前=割り当て「{_attr(r['項目'])}＝{_attr(r['手書き／自動'])}」のとおりか -->")
        add(f"**割り当て**＝項目「{_one_line(r['項目'])}」は **{_one_line(r['手書き／自動'])}**"
            f"（{ga.TODO_MD} の「手書きと自動の割り当て」の表）")
        add("")
        if hand:
            add(f"**見てほしいこと**＝設計書のこの項目の見出しの下の印が［手書き］か。中身が {ga.TODO_MD} の「## 手書きの項目」の"
                "同じ見出しの文と1文字も違わないか（写しの作業場で `--work` から作り直して比べてください）。")
        else:
            add("**見てほしいこと**＝設計書のこの項目の見出しの下の印が［自動］か。中身の1行ずつが、実物（コード・設定・走らせた結果）か、"
                "まこさんが OK した案の逐語（工事のフォルダの okd_*.txt の【番号】の見出しの下）から写した文か。"
                "どちらにも無い文（CC が書いた文）が1行でも在れば所見に書いてください。")
        add("")
    # ★2026-09-30（3点目-a・まこさん OK）＝実装の監査の問いは、設計書と実装の照合の決まった6問（IMPL_QUESTIONS）だけ。
    #   直す前は、設計のもとの1行ずつ（S）・先に直した道具（G）・完成の条件（C）・実装の指示（I）・やらないこと（N）・
    #   CC が決めたこと（D）を1つずつ問いにし、cp53 で問いが686件（うち S が640件）になった。
    if not only_table:
        vals = {"pre": ev.get("pre") or "（まだ commit していない）",
                "post": ev.get("post") or "（まだ commit していない）",
                "files": "・".join(sorted({f"`{_one_line(it.get('対象のファイル'))}`" for it in impl})) or "（無い）",
                "ni": ni, "nc": nc, "iter": iter_,
                "archives": "・".join(f"`{a}`" for a in (ev.get("archives") or [])) or "（無い）",
                "todo": os.path.relpath(src_file, ROOT),
                # 同じコマンドは1回だけ並べる（完成の条件の行ごとに同じコマンドが在ると、同じものが何回も並んだ）
                "cmds": "・".join(dict.fromkeys(f"`{_one_line(r.get('コマンド'))}`" for r in conds)) or "（無い）"}
        for num, pr, name, why, body in IMPL_QUESTIONS:
            add(f"<!-- 項目: 問い 番号={num} 優先度={pr} 理由={_attr(why)} 名前={_attr(name)} -->")
            add(body.format(**vals))
            add("")
    # ★何を調べるかは手で決める（worklog §42）＝元データの「外部検索」から作る（直す前は題の40文字で切れた＝§40 の9）
    for s in searches:
        s = s if isinstance(s, dict) else {"名前": str(s), "中身": ""}
        add(f"<!-- 項目: 外部検索 名前={_attr(s.get('名前', ''))} -->")
        add(_one_line(s.get("中身") or s.get("名前", "")))     # ★クエリ案（期待発見の文は build_request がテンプレの形で足す）
        add("")
    # ★自己申告＝設計書の「塞げないもの」と、見積もりの「測っていない」の行（OK をもらった提案の28行目）
    for r in d.get("塞げないもの") or []:
        add("")
        add("<!-- 項目: 自己申告 -->")
        add(f"**塞げないもの**＝{_one_line(r.get('問い'))}：{_one_line(r.get('塞げないこと'))}")
    for r in d.get("見積もり") or []:
        if "測っていない" in f"{r.get('見込み', '')}{r.get('根拠', '')}":
            add("")
            add("<!-- 項目: 自己申告 -->")
            add(f"**測っていない見積もり**＝{_one_line(r.get('何'))}（{_one_line(r.get('見込み'))}・{_one_line(r.get('根拠'))}）")
    # ★2026-09-29＝工事のフォルダに在るのに設計書に名前が出ていない逐語のファイル（設計書を作った後に写した物）を、道具が数えて申告する
    late = [n for n in names if n.split("/")[-1] not in md]
    if late:
        add("")
        add("<!-- 項目: 自己申告 -->")
        add(f"**設計書を作った後に写した逐語**＝{'・'.join(n.split('/')[-1] for n in late)}（工事のフォルダには在るが、"
            "設計書の §0-1 に名前が無い。設計書を作り直すまで、設計書の §0-1 はこの分だけ元と違う）")
    body = "\n".join(B) + "\n"
    head = (f"{GEN_MARK} kind={kind} design_sha256={sha256_file(design_path or DESIGN)} "
            f"src_sha256={sha256_file(src_file)} "
            f"body_sha256={sha256_text(body)} -->")
    return head + "\n" + body, base


def request_design(kind: str, work: str) -> int:
    """設計書と工事のフォルダから、依頼書の元データを作業場に書き、依頼書を inputs に作る。
    ★2026-09-30（設計書 point1-one-way-20260930-2）＝工事名は必須（元データの JSON から工事名を読む古い口は消した）。"""
    if kind not in KINDS:
        print(f"❌ 種類は design か impl（{kind}）")
        return 2
    if not work:
        print("❌ 工事名がありません（request-design <design|impl> --work <工事名>）")
        return 2
    # ★同じ工事（同じ task）の依頼書が在り、その結果ファイルがまだ無ければ、その番号を使う（作り直すたびに番号を進めない）
    iter0 = work
    task0 = iter0.replace("-", "_") + KINDS[kind][1]
    cp = 0
    for n in sorted(os.listdir(os.path.join(AUDITS, "inputs"))):
        m = re.search(rf"_{re.escape(task0)}_cp(\d+)_audit_request\.md$", n)
        if m and not os.path.exists(os.path.join(AUDITS, n.replace("_audit_request.md", "_audit_report.md"))):
            cp = int(m.group(1))
    cp = cp or next_cp()
    try:
        text, base = build_design_src(kind, cp, work=work)
    except SystemExit as e:
        print(f"❌ 依頼書の元データを作れない: {e}")
        return 1
    work = os.path.join(AUDITS, f"cp{cp}_work")
    os.makedirs(work, exist_ok=True)
    src_path = os.path.join(work, f"cp{cp}_src.gen.md")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"書いた（依頼書の元データ・道具が作った）: {rel_of(src_path)}")
    return build_request(src_path, os.path.join(AUDITS, "inputs", f"{base}_audit_request.md"))


# ───────────── 依頼書を読む ─────────────

Q_RE = re.compile(r"^### (\S+) — (.*)（優先度 ([A-D])）$")
S_RE = re.compile(r"^### 検索 (\d+) — (.*)$")
S_ITEM_RE = re.compile(r"^(\d+)\. \*\*(.+?)\*\*:\s*$")          # ★2026-09-30＝依頼書の外部検索のテンプレの形


def parse_request(path: str):
    errs = []
    text = open(path, encoding="utf-8").read()
    body, mark = split_mark(text)
    if not mark or mark.get("body_sha256") is None:
        errs.append("依頼書に道具の目印が無い（道具で作った依頼書ではない）")
    elif mark.get("body_sha256") != sha256_text(body):
        errs.append("依頼書が、道具で作った後に書き替えられている（本文のハッシュ値が目印と違う）")
    head, secs = split_sections(body)
    info = {"title": "", "meta": {}, "facts": [], "general": [], "questions": [], "searches": [],
            "search_n": None, "self_n": 0, "conclusions": [], "heads": [h for h, _ in secs]}
    for ln in head:
        if ln.startswith("# 【監査依頼】"):
            info["title"] = ln[len("# 【監査依頼】"):]
    for h, lines in secs:
        kind = kind_of(h, SECTION_KIND)
        if kind == "メタ":
            for ln in lines:
                m = re.match(r"^- (.+?): (.*)$", ln)
                if m:
                    info["meta"][m.group(1)] = m.group(2)
        elif kind == "答えてほしいこと":
            cur = None
            for ln in lines:
                if ln.startswith("### "):
                    cur = ln
                elif cur == "### 結論を決める問い":
                    m = CONCLUSION_RE.match(ln)
                    if m:
                        info["conclusions"].append(m.group(1))
        elif kind == "事実データ":
            info["facts"] = [ln[4:] for ln in lines if ln.startswith("### ")]
        elif kind == "一般観点":
            info["general"] = [ln[2:] for ln in lines if re.match(r"^- [①-⑦]", ln)]
        elif kind == "問い":
            for ln in lines:
                m = Q_RE.match(ln)
                if m:
                    info["questions"].append((m.group(1), m.group(2), m.group(3)))
        elif kind == "外部検索":
            for ln in lines:
                # ★2026-09-30（3点目-a）＝テンプレの形（「1. **名前**:」）も読む。古い形（「### 検索 N — 名前」）の依頼書も読める
                m = S_RE.match(ln) or S_ITEM_RE.match(ln)
                if m:
                    info["searches"].append((int(m.group(1)), m.group(2)))
                m = re.match(r"^件数: (\d+) 件", ln)
                if m:
                    info["search_n"] = int(m.group(1))
        elif kind == "自己申告":
            info["self_n"] = sum(1 for ln in lines if re.match(r"^\d+\. ", ln))
    return info, errs


def result_names():
    """テンプレの「## 結果ファイルフォーマット」の表から、11節の番号と名前を読む。"""
    _, secs = split_sections(open(TEMPLATE, encoding="utf-8").read())
    for h, lines in secs:
        if h.startswith("## 結果ファイルフォーマット"):
            return [(int(m.group(1)), m.group(2))
                    for m in (re.match(r"^\|\s*(\d+)\s*\|\s*\*\*(.+?)\*\*", ln) for ln in lines) if m]
    return []


def sorted_questions(qs: list) -> list:
    return sorted(qs, key=lambda q: PRIORITIES.index(q[2]))


# ───────────── 結果の骨組みを作る ─────────────

def build_result(req_path: str, out_path: str) -> int:
    info, errs = parse_request(req_path)
    names = result_names()
    if len(names) != 11:
        errs.append(f"テンプレの結果の表から節が11個 読めない（{len(names)} 個）")
    cp = re.sub(r"^.*_(cp\w+)_audit_request\.md$", r"\1", os.path.basename(req_path))
    out = [f"# 監査結果 {cp} — {info['title']}", ""]
    for n, name in names:
        kind = kind_of(name, RESULT_KIND)
        if kind is None:
            errs.append(f"結果の節「{name}」の骨組みの作り方が道具に無い（テンプレが変わった）")
            continue
        out += [f"## {n}. {name}", ""]
        if kind == "空":
            out += [PLACE]
        elif kind == "版":
            out += [f"- 依頼書: `{rel_of(req_path)}`",
                    f"- 依頼書のハッシュ値: {sha256_file(req_path)}",
                    f"- 監査の相手と版（依頼書に書いてあるもの）: {info['meta'].get('監査の相手と版', '（依頼書に無い）')}",
                    f"- 監査が照らしたハッシュ値: {PLACE}",
                    f"- 実施日: {PLACE}"]
        elif kind == "事実データ":
            for f in info["facts"]:
                out += [f"### {f}", "", PLACE, ""]
        elif kind == "所見":
            out += ["### 一般の観点", ""] + [f"- {g} ＝ <PASS / FAIL>" for g in info["general"]] + [""]
            for qid, qname, pr in sorted_questions(info["questions"]):
                out += [f"### {qid} — {qname}（優先度 {pr}）", "", PLACE, "", f"修正の番号＝{PLACE}", ""]
        elif kind == "外部検索":
            for i, s in info["searches"]:
                out += [f"### 検索 {i} — {s}", "", PLACE, ""]
        elif kind == "自己申告":
            for i in range(1, info["self_n"] + 1):
                out += [f"### 自己申告 {i}", "", PLACE, ""]
        elif kind == "総合判定":
            out += ["### 結論を決める問いへの答え", ""]
            out += [f"- {c} ＝ <YES / NO>（根拠＝{PLACE}）" for c in info["conclusions"]] + [""]
            out += ["### 結論と件数", "", "- 結論＝<GO / CONDITIONAL-GO / NO-GO>"]
            out += [f"- {s}＝<件数>" for s in SEVERITY_FIX + SEVERITY_PROCESS]
        elif kind == "修正":
            for s in SEVERITY_FIX:
                out += [f"### {s}", "", "（無ければ「なし」）", ""]
        elif kind == "プロセス":
            out += ["### Process", "", "（無ければ「なし」）"]
        out = body_strip(out) + ["", ""]
    text = "\n".join(body_strip(out)) + "\n"
    text += f"\n{MARK} result request={rel_of(req_path)} request_sha256={sha256_file(req_path)} -->\n"
    for e in errs:
        print(f"❌ {e}")
    wrote = write_out(out_path, text, "result")
    if not errs and wrote:
        print(f"✅ 結果の骨組みを作った（節 {len(names)}・問い {len(info['questions'])}・"
              f"事実データ {len(info['facts'])}・外部検索 {len(info['searches'])}・自己申告 {info['self_n']}）")
    return 0 if (not errs and wrote) else 1


# ───────────── 照らす ─────────────

def check_lines(req_path: str, rtext: str) -> list:
    """依頼書（ファイル）と結果（文字列）を照らす。戻り＝「✅ …」「❌ …」の行。hook 11 もこれを呼ぶ。"""
    info, errs = parse_request(req_path)
    lines_out = []

    def ok(cond: bool, what: str, detail: str = "") -> None:
        lines_out.append(("✅ " if cond else "❌ ") + what + (f"（{detail}）" if detail and not cond else ""))

    for e in errs:
        ok(False, e)
    rbody, rmark = split_mark(rtext)
    _, rsecs = split_sections(rbody)
    names = result_names()
    want = [f"## {n}. {name}" for n, name in names]
    got = [h for h, _ in rsecs]
    ok(got == want, "結果の節の名前と並びが、テンプレの11節と同じ",
       f"違う所＝{[g for g in got if g not in want] + [w for w in want if w not in got]}")
    ok(rmark.get("request_sha256") == sha256_file(req_path), "結果は、いまの依頼書に対して書かれている",
       "結果の目印の依頼書のハッシュ値が、いまの依頼書と違う")
    sec = {h: "\n".join(ls) for h, ls in rsecs}

    def body_of(kind: str) -> str:
        for n, name in names:
            if kind_of(name, RESULT_KIND) == kind:
                return sec.get(f"## {n}. {name}", "")
        return ""

    q_want = [q[0] for q in sorted_questions(info["questions"])]
    q_got = [m.group(1) for m in (Q_RE.match(ln) for ln in body_of("所見").splitlines()) if m]
    ok(q_got == q_want, f"所見の見出し＝依頼書の問いの番号を、優先度の順に並べたもの（{len(q_want)} 件）",
       f"依頼書＝{q_want} ／ 結果＝{q_got}")
    g_got = len(re.findall(r"^- [①-⑦]", body_of("所見"), re.M))
    ok(g_got == len(info["general"]), f"所見の一般の観点＝依頼書の ①〜⑦（{len(info['general'])} 件）",
       f"結果＝{g_got} 件")
    f_got = re.findall(r"^### (.+)$", body_of("事実データ"), re.M)
    ok(f_got == info["facts"], f"事実データの確認の見出し＝依頼書の事実データ（{len(info['facts'])} 件）",
       f"依頼書＝{info['facts']} ／ 結果＝{f_got}")
    ok(info["search_n"] == len(info["searches"]), "依頼書の外部検索の件数の行＝検索対象の数",
       f"件数の行＝{info['search_n']} ／ 検索対象＝{len(info['searches'])}")
    s_got = [(int(m.group(1)), m.group(2)) for m in (S_RE.match(ln) for ln in body_of("外部検索").splitlines()) if m]
    ok(s_got == info["searches"], f"外部検索の見出し＝依頼書の検索対象（{len(info['searches'])} 件）",
       f"依頼書＝{info['searches']} ／ 結果＝{s_got}")
    c_got = re.findall(r"^- (.+?) ＝ ", body_of("総合判定"), re.M)
    ok(bool(info["conclusions"]) and c_got == info["conclusions"],
       f"総合判定の問いへの答え＝依頼書の結論を決める問い（{len(info['conclusions'])} 件）",
       f"依頼書＝{info['conclusions']} ／ 結果＝{c_got}")
    a_got = len(re.findall(r"^### 自己申告 \d+$", body_of("自己申告"), re.M))
    ok(a_got == info["self_n"], f"自己申告への答えの数＝依頼書の自己申告の数（{info['self_n']} 件）",
       f"結果＝{a_got} 件")
    fix_heads = re.findall(r"^### (\S+)$", body_of("修正"), re.M)
    ok(fix_heads == list(SEVERITY_FIX), "修正の指示の重さの見出し＝Critical・Major・Minor", f"結果＝{fix_heads}")
    pro_heads = re.findall(r"^### (\S+)$", body_of("プロセス"), re.M)
    ok(pro_heads == list(SEVERITY_PROCESS), "CC プロセス欠陥対策の重さの見出し＝Process", f"結果＝{pro_heads}")
    refs = set()
    for v in re.findall(r"^修正の番号＝(.+)$", body_of("所見"), re.M):
        if PLACE in v or v.strip() in ("なし", ""):
            continue
        refs |= set(re.findall(r"\d+", v))
    defs = set(re.findall(r"^#### 修正 (\d+)$", body_of("修正") + "\n" + body_of("プロセス"), re.M))
    if refs or defs:
        ok(refs == defs, "所見に書いた修正の番号＝修正の指示と CC プロセス欠陥対策に在る番号",
           f"所見だけ＝{sorted(refs - defs)} ／ 修正だけ＝{sorted(defs - refs)}")
    else:
        lines_out.append("（所見と修正の番号は、まだ中身が無いので照らさない）")
    return lines_out


# ───────────── 中身を書いた結果の形 ─────────────

FOURTH = ("直した後の文字", "足す文字", "消す文字", "走らせるコマンド")
STATES = ("確定", "未決", "案が複数")
BANNED = ("修正の方向性", "直し方（案）", "対策＝", "取り下げ")   # テンプレの「書けないもの」の語
FOURTH_RE = re.compile(r"^(?:案([A-Z]) )?(直した後の文字|足す文字|消す文字|走らせるコマンド):\s*\n~~~\n", re.M)
EVIDENCE_RE = re.compile(r"\S+:\d+.*「.+」")


def item_fields(num: str, block: str) -> dict:
    """修正の指示1件から、6つの欄を読み取って返す（形は見ない・読むだけ）。

    ★2026-09-16（設計書 audit-autofix-apply-20260916 の 4-3）＝当てる道具（apply_audit_fix.py）と
      この道具の `item_errors` が、同じ読み取りを呼ぶ形にするために切り出した。
      同じ正規表現を2か所に書くと、片方だけ直って食い違うため。

    戻り＝{"番号", "対象のファイル", "直す箇所", "直す前の文字"（囲みの中・無ければ None）,
           "4つ目"＝[(案の記号 or "", 見出し, 中身), …], "根拠の抜き書き", "状態"}
    """
    block = re.split(r"^### ", block, flags=re.M)[0]

    def field(label: str):
        m = re.search(rf"^{label}:[ \t]*(.*)$", block, re.M)
        return m.group(1).strip() if m else None

    before = re.search(r"^直す前の文字:[ \t]*\n~~~\n(.*?)\n?~~~", block, re.S | re.M)
    fourth = []
    for m in re.finditer(r"^(?:案([A-Z]) )?(直した後の文字|足す文字|消す文字|走らせるコマンド):"
                         r"[ \t]*\n~~~\n(.*?)\n?~~~", block, re.S | re.M):
        fourth.append((m.group(1) or "", m.group(2), m.group(3)))
    return {"番号": num,
            "対象のファイル": field("対象のファイル"),
            "直す箇所": field("直す箇所"),
            "直す前の文字": before.group(1) if before else None,
            "4つ目": fourth,
            "根拠の抜き書き": field("根拠の抜き書き"),
            "状態": field("状態")}


def item_errors(num: str, block: str) -> list:
    """修正の指示1件の欄を見る。★読み取りは item_fields（2か所に書かない）。"""
    e = []
    f = item_fields(num, block)
    block = re.split(r"^### ", block, flags=re.M)[0]

    def field(label: str):
        m = re.search(rf"^{label}:[ \t]*(.*)$", block, re.M)
        return m.group(1).strip() if m else None

    tgt = field("対象のファイル")
    if not tgt:
        e.append("対象のファイルが無い")
    elif re.search(r"\s", tgt):
        e.append(f"対象のファイルが1つのパスでない（{tgt}）")
    loc = field("直す箇所")
    if not loc:
        e.append("直す箇所が無い")
    before = f["直す前の文字"]
    if before is None:
        e.append("直す前の文字の囲み（~~~）が無い")
    fourth = [(a, k) for a, k, _ in f["4つ目"]]
    if not fourth:
        e.append(f"4つ目の欄（{'・'.join(FOURTH)} のどれか）が無い")
    ev = field("根拠の抜き書き")
    if not ev or not EVIDENCE_RE.search(ev):
        e.append("根拠の抜き書きが「ファイル名:行番号「その行の逐語」」の形でない")
    st = field("状態")
    if st not in STATES:
        e.append(f"状態が「確定」「未決」「案が複数」のどれでもない（{st}）")
    n_plans = sum(1 for a, _ in fourth if a)
    if st == "案が複数" and n_plans < 2:
        e.append("状態が「案が複数」なのに、案が2つ以上 無い")
    if st != "案が複数" and n_plans:
        e.append("案A などが在るのに、状態が「案が複数」でない")
    if any(k == "走らせるコマンド" for _, k in fourth):
        if before is None or before.strip() != "なし":
            e.append("走らせるコマンドなのに、直す前の文字が「なし」でない")
        if loc != "なし":
            e.append("走らせるコマンドなのに、直す箇所が「なし」でない")
    return [f"修正 {num}: {x}" for x in e]


def form_errors(rtext: str) -> list:
    """中身を書いた結果が、テンプレの形かを見る。戻り＝食い違いの文の一覧。hook 11 もこれを呼ぶ。"""
    errs = []
    body, _ = split_mark(rtext)
    for ph in PLACEHOLDERS:
        if ph in body:
            errs.append(f"「{ph}」が残っている（中身を書いていない所が在る）")
    _, secs = split_sections(body)
    sec = {h: "\n".join(ls) for h, ls in secs}
    for n, name in result_names():
        kind = kind_of(name, RESULT_KIND)
        text = sec.get(f"## {n}. {name}", "")
        if kind == "総合判定":
            if not re.search(r"^- 結論＝(GO|CONDITIONAL-GO|NO-GO)[ \t]*$", text, re.M):
                errs.append(f"{n}. {name} の結論が「GO」「CONDITIONAL-GO」「NO-GO」のどれでもない")
            for c, yn in re.findall(r"^- (.+?) ＝ (\S+?)（", text, re.M):
                if yn not in ("YES", "NO"):
                    errs.append(f"{n}. {name} の「{c}」の答えが YES / NO でない（{yn}）")
        if kind in ("所見", "修正", "プロセス"):
            for w in BANNED:
                if w in text:
                    errs.append(f"{n}. {name} に「{w}」が在る（テンプレの「書けないもの」）")
        if kind in ("修正", "プロセス"):
            parts = re.split(r"^#### 修正 (\d+)[ \t]*$", text, flags=re.M)
            for num, block in zip(parts[1::2], parts[2::2]):
                errs += item_errors(num, block)
    return errs


def selftest() -> int:
    """request-design の自己テスト（2026-09-29・まこさん指摘「監査の依頼内容が変じゃないか？」を測る）。

    ★本物の inputs にも設計書にも書かない。依頼書は一時の置き場に作る。
    ★2026-09-30（設計書 point1-one-way-20260930-2）＝本物の元データ（acceptance_src.json）と本物の設計書を読むのをやめた。
      設計書の道具の見本の工事のフォルダ（gen_acceptance._sample_work）と、そこから作った見本の設計書だけで試す。
    """
    import shutil
    import tempfile
    from pathlib import Path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_acceptance as ga
    # ★置き場は監査の置き場の中（外だと依頼書を書かず、空の依頼書で「出さない」の試しが素通りした＝2026-09-29 に実測）
    tmpd = tempfile.mkdtemp(prefix="gad_selftest_", suffix="_work", dir=AUDITS)
    # 見本の工事のフォルダはリポジトリの中の一時の置き場（設計書の道具がリポジトリからの相対のパスを書くため）
    vtmp = Path(tempfile.mkdtemp(prefix="_selftest_gad_verbatim_", dir=os.path.join(ROOT, ".claude", "state")))
    saved = (ga.WORK, ga.gv.VERBATIM_DIR, ga.gv.ARCHIVE_DIR, ga.src_from_work)
    ok = total = 0
    fails = []
    req = ""

    def case(name, good):
        nonlocal ok, total
        total += 1
        good = bool(good) and bool(req)          # ★依頼書が空なら、どの試しも通さない
        ok += bool(good)
        print(f"   {'✅' if good else '❌'} T{total} {name}")
        if not good:
            fails.append(name)

    try:
        ga.gv.VERBATIM_DIR, ga.gv.ARCHIVE_DIR = vtmp / "verbatim", vtmp / "archive"
        work = ga._sample_work(vtmp)
        ga.WORK = work
        design_path = str(vtmp / "acceptance_sample.md")
        ga.write(dest=Path(design_path))
        d = ga.src_from_work(work)
        engine = ga.touches_trading(d)
        text, base = build_design_src("design", 999, work, design_path)
        sp = os.path.join(tmpd, "src.gen.md")
        open(sp, "w", encoding="utf-8").write(text)
        op = os.path.join(tmpd, f"{base}_audit_request.md")
        rc = build_request(sp, op)
        req = open(op, encoding="utf-8").read() if os.path.isfile(op) else ""
        case("依頼書が作れる（rc=0）", rc == 0 and bool(req))
        case("売買に触らない工事では「net は M2-L」の前提を出さない（§40 の1）", engine or "M2-L" not in req)
        case("売買に触らない工事では engine_tuner の目的の文を大目的に出さない（§40 の1）",
             engine or "engine_tuner の目的は" not in req)
        case("売買に触らない工事では前の工事の検査の表を事実データに出さない（§40 の3）",
             engine or "| コマンド | 種類 | 終了コード |" not in req)
        w = re.findall(r"^### W\d+ — ", req, re.M)
        tl = (ga.gv.work_dir(work) / ga.TODO_MD).read_text(encoding="utf-8").splitlines()
        assign = ga._md_table(ga._sections(tl, re.compile(r"^##\s+(?!#)(.+)$")).get("手書きと自動の割り当て") or [],
                              ("項目", "手書き／自動"), "割り当て", [])
        case("問いは割り当ての表の1行ごと（W）に1つずつ在る", bool(assign) and len(w) == len(assign))
        case("テンプレの「N 件」を残さない（§40 の10）", "N 件" not in req)
        case("置き場は根からの全パスにそろえる（§40 の11）", "`.claude/audits/" not in req)
        names = [(s.get("名前") if isinstance(s, dict) else str(s)) for s in (d.get("外部検索") or [])]
        case("外部検索は OK された案の【外部検索】から作る（§40 の9）", bool(names) and all(n in req for n in names))
        case("売買に触らない工事では「Crypto futures」の守則を出さない（§41）", engine or "Crypto futures" not in req)
        # ★テンプレの注記（_template.md 97行目）は書き替えない決まり（設計書 3-1 の6）なので、必読の表の行だけを見る
        case("必読に古い元データ（acceptance_src.json）を入れない（1本のやり方）",
             not any(re.match(r"^\d+\. ", ln) and "acceptance_src.json" in ln for ln in req.splitlines()))
        # ★2026-09-30（3点目-a・まこさん OK）＝依頼書の中身をテンプレの形にした（worklog 20260929 §67 の①〜⑤）
        rd = req.split("## 着手前必読", 1)[-1].split("\n## ", 1)[0]
        case("必読はテンプレの形（番号つきの行・表でない）",
             bool(re.search(r"^1\. `", rd, re.M)) and not re.search(r"^\|", rd, re.M))
        info_d, _e = parse_request(op)
        case("外部検索はテンプレの形（### 検索対象 の下に番号つき）で、読み取りの数が検索の数と同じ",
             "### 検索対象" in req and not re.search(r"^### 検索 \d+ — ", req, re.M)
             and len(info_d["searches"]) == len(names) and info_d["search_n"] == len(names))
        case("大目的の注記はテンプレの形（⚠️ 本監査スコープ = …）で、守りの穴探しを対象外にする",
             "⚠️ 本監査スコープ = " in req and "守りの穴探し" in req)
        # 実装の監査の依頼書＝問いは決まった6問（Q1〜Q6）だけ。設計のもとの1行ずつの問い（S ほか）は出さない
        text_i, base_i = build_design_src("impl", 998, work, design_path)
        sp_i = os.path.join(tmpd, "src_impl.gen.md")
        open(sp_i, "w", encoding="utf-8").write(text_i)
        op_i = os.path.join(tmpd, f"{base_i}_audit_request.md")
        rc_i = build_request(sp_i, op_i)
        req_i = open(op_i, encoding="utf-8").read() if os.path.isfile(op_i) else ""
        qs_i = re.findall(r"^### (\S+) — ", req_i, re.M)
        case("実装の監査の依頼書が作れて、問いは Q1〜Q6 の6問だけ（S・G・C・I・N・D・W は出さない）",
             rc_i == 0 and qs_i == [q[0] for q in IMPL_QUESTIONS])
        case("実装の監査の依頼書に、実装の指示の一覧と当てた記録の事実データが在る",
             "### 設計書の実装の指示の一覧" in req_i and "### 当てた記録" in req_i)
        # 【外部検索】が無ければ止まる＝src_from_work の戻りから外して試す（見本の逐語は書き替えない）
        orig_sfw = ga.src_from_work
        ga.src_from_work = lambda wk: {k: v for k, v in orig_sfw(wk).items() if k != "外部検索"}
        try:
            build_design_src("design", 999, work, design_path)
            stopped = False
        except SystemExit as e:
            stopped = "外部検索" in str(e)
        finally:
            ga.src_from_work = orig_sfw
        case("OK された案に【外部検索】が無ければ止まる（何を調べるかは手で決める）", stopped)
        # 工事名が無ければ止まる（古い元データへは戻らない）
        try:
            build_design_src("design", 999, "", design_path)
            stopped2 = False
        except SystemExit as e:
            stopped2 = "工事名" in str(e)
        case("工事名が無ければ止まる（依頼書の作り方は工事のフォルダの1本だけ）", stopped2)
    finally:
        ga.WORK, ga.gv.VERBATIM_DIR, ga.gv.ARCHIVE_DIR, ga.src_from_work = saved
        shutil.rmtree(tmpd, ignore_errors=True)
        shutil.rmtree(str(vtmp), ignore_errors=True)
    print(f"\n{'✅' if ok == total else '❌'} selftest {ok}/{total} pass")
    return 0 if ok == total else 1


def main(argv: list) -> int:
    if argv and argv[0] == "--selftest":
        # ★2026-09-30（設計書 point1-one-way-20260930-2）＝控えの元データを受ける口は消した（見本の工事のフォルダだけで試す）
        return selftest()
    if len(argv) == 2 and argv[0] == "request-design":
        print("❌ request-design は --work <工事名> が要ります（元データの JSON から作る古い口は消した）")
        return 2
    # ★2026-09-29（135回目）＝request-design <design|impl> --work <工事名>＝工事のフォルダから作った設計書の依頼書
    if len(argv) == 4 and argv[0] == "request-design" and argv[2] == "--work":
        return request_design(argv[1], argv[3])
    ok_shape = (len(argv) == 3 and argv[0] in ("request", "result", "check")) or (len(argv) == 2 and argv[0] == "form")
    if not ok_shape:
        print(__doc__)
        return 2
    cmd, files = argv[0], argv[1:]
    for p in (files if cmd in ("check", "form") else files[:1]):
        if not os.path.isfile(p):
            print(f"❌ ファイルが無い: {p}")
            return 1
    if cmd == "request":
        return build_request(files[0], files[1])
    if cmd == "result":
        return build_result(files[0], files[1])
    if cmd == "check":
        lines = check_lines(files[0], open(files[1], encoding="utf-8").read())
        for ln in lines:
            print(ln)
        bad = sum(1 for ln in lines if ln.startswith("❌ "))
        print(f"食い違い {bad} 件")
        return 1 if bad else 0
    errs = form_errors(open(files[0], encoding="utf-8").read())
    for e in errs:
        print(f"❌ {e}")
    print(f"形の食い違い {len(errs)} 件")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
