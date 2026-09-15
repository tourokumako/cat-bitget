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
  python3 .claude/tools/gen_audit_docs.py request <元データ.md> <依頼書.md>
    → 元データ（下の形）とテンプレから依頼書を作る。
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
  ②プログラムが作る文書と元データの組は、設計書（.claude/state/acceptance.md → acceptance_src.json）の1組だけを知っている。
  ③この道具自身を書き換えれば無効にできる（git diff には出る）。
  ④恒久71番＝文書を作る道具なので、壊すプログラムと自己テストは付けない。走らせて確かめる。
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys

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
GENERATED = {".claude/state/acceptance.md": "acceptance_src.json"}
PLACE = "<監査が書く>"
# 結果の骨組みに入れる、監査が埋める所の印の全部（form はどれが残っていても止める）
PLACEHOLDERS = (PLACE, "<PASS / FAIL>", "<YES / NO>", "<GO / CONDITIONAL-GO / NO-GO>", "<件数>")
MARK = "<!-- gen_audit_docs:"
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

def build_request(src_path: str, out_path: str) -> int:
    src, meta, errs = parse_src(src_path)
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
        if os.path.basename(target) == os.path.basename(gen) and raw not in reading:
            errs.append(f"監査の相手 {gen} はプログラムが作る文書。着手前必読に元データ {raw} が無い")

    if not os.path.isfile(TEMPLATE):
        print(f"❌ テンプレが無い: {TEMPLATE}")
        return 1
    _, secs = split_sections(open(TEMPLATE, encoding="utf-8").read())
    base = f"{meta.get('日付', '')}_{meta.get('task', '')}_{meta.get('cp', '')}"

    def rep(s: str) -> str:
        return (s.replace("<本依頼書のパス>", f"v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/{base}_audit_request.md")
                .replace("2026-XX-XX_<task>_cpN", base).replace("<cpN>", meta.get("cp", "")))

    out = [f"# 【監査依頼】{meta.get('題', '')}", ""]
    for head, lines in secs:
        kind = kind_of(head, SECTION_KIND)
        body = body_strip(lines)
        if kind is None:
            errs.append(f"テンプレの見出し「{head}」の埋め方が道具に無い（テンプレが変わった）")
            continue
        out += [head, ""]
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
                    out += ["", x]
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
                    f"- 結果ファイル保存先: `.claude/audits/{base}_audit_report.md`",
                    f"- 入力ファイル保存先 (本依頼書): `.claude/audits/inputs/{base}_audit_request.md`"]
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
            out += [f"件数: {n} 件 (結果の外部検索は、この件数の検索対象に1つずつ答える)", ""]
            for i, it in enumerate(src["外部検索"], 1):
                out += [f"### 検索 {i} — {it['attrs'].get('名前', '')}", ""] + it["body"].splitlines() + [""]
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


# ───────────── 依頼書を読む ─────────────

Q_RE = re.compile(r"^### (\S+) — (.*)（優先度 ([A-D])）$")
S_RE = re.compile(r"^### 検索 (\d+) — (.*)$")


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
                m = S_RE.match(ln)
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


def item_errors(num: str, block: str) -> list:
    """修正の指示1件の欄を見る。"""
    e = []
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
    before = re.search(r"^直す前の文字:[ \t]*\n~~~\n(.*?)\n?~~~", block, re.S | re.M)
    if not before:
        e.append("直す前の文字の囲み（~~~）が無い")
    fourth = FOURTH_RE.findall(block)
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
        if not before or before.group(1).strip() != "なし":
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


def main(argv: list) -> int:
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
