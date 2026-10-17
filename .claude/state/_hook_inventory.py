#!/usr/bin/env python3
"""_hook_inventory.py — hook の一覧（ToDo の29番・hook の直しの流れの1段目）を作る（2026-10-15・180回目）

なぜ在るか（恒久の決まり76番・まこさん要件 2026-10-15）
  hook の不具合・過剰・不要を振り分ける（30番）材料として、hook を1本ずつの名前で並べる。
  恒久の決まり69番＝手で書かざるを得ない所だけ手で書く。
    プログラムが作る欄＝名前・役割（hook の本体の「役割:」の行か、説明の行「名前 — 役割」から写す）・
      作られたきっかけ（本体のコメントの、日付とまこさんの言葉が在る最初の行から写す）・
      登録（タイミングと matcher）・本体の .py・名指しの在る所・止めた回数・打ち直しで通った回数。
    手で書く欄（元データ hook_inventory_src.json）＝止める物（本体の判定の行を読んで書く）・
      守っている要件（CC の案＝30番の振り分けの材料）・印（説明と動きが違う など）・
      役割（本体に「役割:」の行も説明の行も無いときだけ）。
  ★2026-10-15（まこさん「hook_inventory.mdでは、各hookの役割がわからない」「自動生成はできないの？」→ CC の案に「OK」）
    ＝役割・きっかけ・守っている要件を表の先頭に置き、長い「止める物」は表の下の1本ずつの節に移した。

使い方:
  python3 .claude/state/_hook_inventory.py --write    # 元データと実物から hook_inventory.md を作る（止めた回数の数えに約1分）
  python3 .claude/state/_hook_inventory.py --verify   # 本数が実物と合うか・根拠の「ファイル名:行番号」が実在するか・文書が作ったままか

決まり:
  ・読むための道具（恒久71番）＝壊すプログラムと自己テストは付けない。走らせた結果を1回 貼る。
  ・書く先は hook_inventory.md の1本だけ。元データ（hook_inventory_src.json）は読むだけ。
  ・止めた回数は _hook_usage_probe.py（直近7日）の出力をそのまま使う。
  ・「名指しの在る所」は、名前がコメントでない行に出てくるファイル。呼んでいるかの確定は「止める物」の欄で手で書く。
  ・本体の説明の行は、いまの動きと合わないことがある（2026-10-15 に2本 見つけた）＝合わない物は元データの「印」に書く。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".claude" / "hooks"
SETTINGS = ROOT / ".claude" / "settings.json"
SRC = ROOT / ".claude" / "state" / "hook_inventory_src.json"
OUT = ROOT / ".claude" / "state" / "hook_inventory.md"
PROBE = ROOT / ".claude" / "state" / "_hook_usage_probe.py"
SDK = ROOT / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
SEARCH_DIRS = [ROOT / ".claude" / "hooks", ROOT / ".claude" / "tools", ROOT / ".claude" / "breaks",
               SDK / "scripts" / "priority_rebuild"]
CITE_RE = re.compile(r"([\w./\-]+\.(?:sh|py|json|md)):(\d+)")
HEAD = "<!-- HOOK_INVENTORY hash="
TIMING_RE = re.compile(r"^(?:SessionStart|PreToolUse|PostToolUse|Stop)\b")
ROLE_LINE_RE = re.compile(r"^\s*#?\s*役割[:：]\s*(.+)$")
DATE_RE = re.compile(r"20\d\d-[01]\d-[0-3]\d")


def registrations() -> dict[str, list[str]]:
    """settings.json の登録＝{ファイル名: ["タイミング:matcher", ...]}（登録の順・重複は除く）。"""
    d = json.loads(SETTINGS.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for ev, arr in (d.get("hooks") or {}).items():
        for a in arr:
            for h in a.get("hooks") or []:
                for name in re.findall(r"hooks/([A-Za-z0-9_]+\.(?:sh|py))", str(h.get("command") or "")):
                    tag = f"{ev}:{a.get('matcher') or '—'}"
                    lst = out.setdefault(name, [])
                    if tag not in lst:
                        lst.append(tag)
    return out


def hook_files() -> list[pathlib.Path]:
    return sorted(p for p in HOOKS.iterdir() if p.is_file() and p.suffix in (".sh", ".py"))


def all_lines(p: pathlib.Path) -> list[str]:
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []


def code_lines(p: pathlib.Path) -> list[str]:
    return [ln for ln in all_lines(p) if not ln.lstrip().startswith("#")]


def mentions(stem: str, ext: str, self_path: pathlib.Path) -> list[str]:
    """名前がコメントでない行に出てくるファイル（自分は除く）。.py は import の形も数える。"""
    pats = [re.compile(rf"(?<![\w]){re.escape(stem)}\.{ext}\b")]
    if ext == "py":
        pats.append(re.compile(rf"(?:^|\s)(?:import|from)\s+{re.escape(stem)}\b"))
    found: list[str] = []
    if any(p.search(SETTINGS.read_text(encoding="utf-8")) for p in pats):
        found.append("settings.json")
    for d in SEARCH_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if not f.is_file() or f == self_path or f.suffix not in (".sh", ".py"):
                continue
            body = "\n".join(code_lines(f))
            if any(p.search(body) for p in pats):
                found.append(f"{d.name}/{f.name}")
    return found


def _clean(s: str) -> str:
    s = s.strip()
    s = re.sub(r'^(?:#+|"""|\'\'\')\s*', "", s)
    s = re.sub(r'\s*(?:"""|\'\'\')\s*$', "", s)
    return s.strip()


def _not_role(t: str) -> bool:
    """役割として使えない説明の行か（番号・動く時機・「本体」だけの行）。2026-10-15 に写して見て足した。"""
    t = re.sub(r"^hook\s*\d+\s*・\s*", "", t)
    return (not t or TIMING_RE.match(t) is not None or t.startswith(("（", "("))
            or re.match(r"^G\d", t) is not None or re.search(r"本体(?:（[^）]*）)?。?$", t) is not None)


def role_of(cands: list[pathlib.Path]) -> tuple[str, str]:
    """(役割, 出どころ「ファイル名:行番号」)。①本体の「役割:」の行 ②説明の行「名前 — 役割」。無ければ ("", "")。
    cands＝hook 自身と、同じ名前の本体の .py だけ（呼び出し先の部品の説明を写さないため）。"""
    for p in cands:
        for i, ln in enumerate(all_lines(p)[:60], 1):
            m = ROLE_LINE_RE.match(ln)
            if m:
                return _clean(m.group(1)), f"{p.name}:{i}"
    for p in cands:
        pat = re.compile(rf"{re.escape(p.stem)}(?:\.(?:py|sh))?\s*[—–]+\s*(.+)$")
        for i, ln in enumerate(all_lines(p)[:8], 1):
            m = pat.search(ln)
            if not m:
                continue
            t = _clean(m.group(1))
            # 「Stop: …」のように、動く時機の後ろに役割が続く形は、時機を外す
            t = re.sub(r"^(?:SessionStart|PreToolUse|PostToolUse|Stop)[^：:（(]{0,30}[:：]\s*", "", t)
            if not _not_role(t):
                return t, f"{p.name}:{i}"
    return "", ""


def comment_lines(p: pathlib.Path) -> list[tuple[int, str]]:
    """コメントの行（# で始まる行と、先頭の三重引用符の説明の中）＝[(行番号, 文)]。コードの行は入れない。"""
    out, inside = [], False
    for i, ln in enumerate(all_lines(p), 1):
        s = ln.strip()
        if inside:
            out.append((i, ln))
            if '"""' in s:
                inside = False
            continue
        if s.startswith("#"):
            out.append((i, ln))
        elif s.startswith('"""') and i <= 5:
            out.append((i, ln))
            inside = s.count('"""') == 1
    return out


WHY_RE = re.compile(r"^(?:★\s*)?(?:なぜ要るか|なぜ要ったか|なぜ|経緯|背景|目的)\s*[（(:：＝]")


def origin_of(cands: list[pathlib.Path]) -> tuple[str, str]:
    """(作られたきっかけ, 出どころ)。2つを写す（2026-10-15 に写して見て直した＝最初の「まこさんの言葉の行」は、
    後の直し（合言葉の廃止 ほか）の行であることが多く、作られたきっかけにならなかった）。
      ①作られた日＝コメントの行の中で、いちばん古い日付
      ②なぜ作ったか＝「なぜ要るか」「経緯」「背景」「目的」で始まる最初のコメントの行（短ければ次の行も足す）
    どちらも無ければ ("", "")。"""
    # ★2026-10-15 に写して見て直した＝①いちばん古い日付は、コメントの中の日付の例（2025-01-01）や、
    #   合言葉を廃止した日（2026-08-16）を拾った＝先頭の見出しの行（名前 — …（日付 新設））の日付を先に使い、
    #   解除・合言葉の行の日付は数えない ②なぜの行は、後の直しの理由を拾った＝先頭に近い40行から先に探す。
    head_date, dates, why, src = "", [], "", ""
    for p in cands:
        cl = comment_lines(p)
        for k, (i, ln) in enumerate(cl):
            if "解除" in ln or "合言葉" in ln:
                continue
            ds = DATE_RE.findall(ln)
            if ds and not head_date and k < 6:
                head_date = ds[0]
            dates += ds
    for limit in (40, 10 ** 9):
        for p in cands:
            cl = comment_lines(p)
            for k, (i, ln) in enumerate(cl[:limit]):
                t = _clean(ln)
                if not why and WHY_RE.match(t) and "合言葉" not in t:
                    why, src = t, f"{p.name}:{i}"
                    if len(re.sub(r"^\S+?[（(:：＝]", "", why)) < 20 and k + 1 < len(cl):
                        why += " " + _clean(cl[k + 1][1])
    if not dates and not why:
        return "", ""
    if head_date:
        out = f"作った日＝{head_date}（先頭の見出しの日付）"
    elif dates:
        out = f"作った日＝{min(dates)}（コメントの中でいちばん古い日付）"
    else:
        out = "作った日＝（日付の書いた行が無い）"
    if why:
        out += "。なぜ＝" + why[:150] + ("…" if len(why) > 150 else "")
    return out, (src or "日付だけ")


def usage() -> dict[str, tuple[int, int, int]]:
    """_hook_usage_probe.py 7 の出力＝{ファイル名: (止めた回数・道具の前, 止めた回数・Stop, 打ち直しで通った回数)}。"""
    r = subprocess.run([sys.executable, str(PROBE), "7"], capture_output=True, text=True, cwd=str(ROOT))
    out: dict[str, list[int]] = {}
    for ln in r.stdout.splitlines():
        parts = ln.split("\t")
        if len(parts) < 3 or not parts[1].isdigit():
            continue
        name, n, ok = parts[0], int(parts[1]), int(parts[2])
        stop = name.endswith(" (Stop)")
        base = name.replace(" (Stop)", "")
        v = out.setdefault(base, [0, 0, 0])
        v[1 if stop else 0] += n
        v[2] += ok
    return {k: tuple(v) for k, v in out.items()}


def cell(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def check_cites(text: str) -> list[str]:
    """根拠の「ファイル名:行番号」が実在するか（ファイルが見つからない・行がファイルの長さを超える）。"""
    ng = []
    for f, n in CITE_RE.findall(text or ""):
        cands = [ROOT / f, HOOKS / f, ROOT / ".claude" / f, SDK / f, SDK / "scripts" / "priority_rebuild" / f,
                 ROOT / ".claude" / "tools" / f, ROOT / ".claude" / "state" / f]
        p = next((c for c in cands if c.is_file()), None)
        if p is None:
            ng.append(f"{f}:{n}（ファイルが見つからない）")
        elif int(n) < 1 or int(n) > len(p.read_text(encoding="utf-8", errors="replace").splitlines()):
            ng.append(f"{f}:{n}（行がファイルの長さを超える）")
    return ng


def build(use: dict | None) -> tuple[list[str], dict]:
    src = json.loads(SRC.read_text(encoding="utf-8")) if SRC.exists() else {"hooks": {}}
    # 手で書く欄は2つのまとまりに在る＝"hooks"（止める物）と "案と手書き"（役割・きっかけ・守る要件・印）。名前ごとに合わせて読む。
    hand = {n: dict(v) for n, v in (src.get("hooks") or {}).items()}
    # ★2026-10-15（まこさん「要不要をふりわけられるような材料を出して」「勝手に要不要を振り分けないで」）
    #   ＝3つ目のまとまり "振り分けの材料"（いま動く場面・同じことを見るほかの hook・試した結果）を足した。要る・要らないの判断は書かない。
    for key in ("案と手書き", "振り分けの材料"):
        for n, v in (src.get(key) or {}).items():
            if n.startswith("_"):              # 説明の項目（_説明）は hook ではない
                continue
            hand.setdefault(n, {}).update(v)
    reg = registrations()
    files = hook_files()
    names = {p.name for p in files}
    sh = [p for p in files if p.suffix == ".sh"]
    py = [p for p in files if p.suffix == ".py"]
    # .sh が本体として呼ぶ .py（コメントでない行に hooks/<x>.py か <x>.py が在る）
    body_of: dict[str, list[str]] = {}
    for p in sh:
        txt = "\n".join(code_lines(p))
        body_of[p.name] = [q.name for q in py if re.search(rf"(?<![\w]){re.escape(q.stem)}\.py\b", txt)]
    attached = {q for v in body_of.values() for q in v}
    stats = {"登録の件数": sum(len(v) for v in reg.values()), "登録の名前": len(reg),
             "sh": len(sh), "py": len(py), "登録の名前で実物が無い": [n for n in reg if n not in names]}
    info: dict[str, dict] = {}
    stop_map = {n: v for n, v in (src.get("停止") or {}).items() if not n.startswith("_")}
    # ★2026-10-15（181回目）＝4つ目のまとまり "まこさんの振り分け" を読む。直す前は読んでいなかったので、
    #   1〜4本目の決定が hook_inventory.md に1つも出ていなかった（元データに書いただけになっていた）。
    decide = {n: v for n, v in (src.get("まこさんの振り分け") or {}).items() if not n.startswith("_")}

    def stopped(name: str) -> str:
        """止めている理由（止めていなければ ""）。①元データの「停止」②登録が無く、どこからも名指しの無い物。"""
        if name in stop_map:
            return str(stop_map[name])
        if name not in reg and not facts(name)["名指し"]:
            return "登録が無く、どこからも名指しが無い＝動かない"
        return ""

    def facts(name: str) -> dict:
        if name in info:
            return info[name]
        p = HOOKS / name
        h = hand.get(name) or {}
        # 役割ときっかけを写す相手＝hook 自身と、同じ名前の本体の .py だけ（呼び出し先の部品の説明を写さない・2026-10-15 に写して見て直した）
        cands = [p] + [HOOKS / b for b in body_of.get(name, []) if pathlib.Path(b).stem == p.stem]
        role, rsrc = role_of(cands)
        if not role and h.get("役割"):
            role, rsrc = h["役割"], "手で書いた"
        orig, osrc = origin_of(cands)
        if h.get("きっかけ"):                    # 自動で写した物が実物と合わない hook だけ、元データに手で書く（2026-10-15）
            orig, osrc = h["きっかけ"], "手で書いた"
        info[name] = {"役割": role, "役割の出どころ": rsrc, "きっかけ": orig, "きっかけの出どころ": osrc,
                      "要件": h.get("守る要件") or "", "印": h.get("印") or "",
                      "動く場面": h.get("動く場面") or "", "重なり": h.get("重なり") or "", "試した結果": h.get("試した結果") or "",
                      "止める物": h.get("止める物") or "", "直し": h.get("直し") or "", "本体": body_of.get(name, []),
                      # ★2026-10-17（188回目・まこさん「OK」）＝その hook（か、hook が呼ぶ検査）が確かめる項目の表。
                      #   1件＝{"項目": …, "どこで": "ファイル名:行番号"}。節の「止める物」の下に表で出す（1行につなぐと読めない）
                      "確かめる項目": h.get("確かめる項目") or [],
                      "名指し": mentions(p.stem, p.suffix[1:], p)}
        return info[name]

    def row(name: str) -> str:
        f = facts(name)
        u = (use or {}).get(name)
        cnt = "—" if use is None else (f"{u[0]}／{u[1]}" if u else "0／0")
        retry = "—" if use is None else (str(u[2]) if u else "0")
        role = (f["役割"] + (f"（{f['役割の出どころ']}）" if f["役割"] else "")) if f["役割"] else "（まだ無い）"
        bug = "・".join(x for x in (f["印"] and f"説明と動きが違う：{f['印']}", f["試した結果"]) if x) or "（まだ試していない）"
        why = stopped(name)
        if why:
            role = f"【止めている：{why}】" + role
        if decide.get(name):                     # まこさんの振り分けの頭の語（「要」など・「（」の前まで）
            role = f"【まこさん：{str(decide[name]).split('（')[0]}】" + role
        return "| " + " | ".join([
            ("❌️" if why else "") + f"`{name}`", cell(role), cell(f["要件"] or "（まだ）"), cell(f["動く場面"] or "（まだ）"),
            cell(f["重なり"] or "（まだ）"), cell(bug), cell(f["直し"] or "（まだ確かめていない）"), cnt, retry]) + " |"

    def detail(name: str) -> list[str]:
        f = facts(name)
        orig = (f["きっかけ"] + f"（{f['きっかけの出どころ']}）") if f["きっかけ"] else "（本体に日付の書いた行が無い）"
        out = [f"### {name}", "",
               f"- 作られたきっかけ＝{orig}",
               f"- 登録＝{'、'.join(reg.get(name, [])) or '登録なし'}",
               f"- 本体の .py＝{'、'.join(f['本体']) or '—（この .sh 自身が判定する）' if name.endswith('.sh') else '—'}",
               f"- 名指しの在る所（コメントでない行）＝{'、'.join(f['名指し']) or '無い'}",
               f"- 止める物＝{f['止める物'] or '（まだ読んでいない）'}",
               f"- まこさんの振り分け＝{decide.get(name) or '（まだ＝1本ずつの確かめが、この hook まで来ていない）'}", ""]
        if f["確かめる項目"]:
            out += ["確かめる項目（どれも中身の正しさは見ない）", "", "| # | 確かめること | どこで確かめているか |", "|---|---|---|"]
            out += [f"| {i} | {cell(str(r.get('項目', '')))} | {cell(str(r.get('どこで', '')))} |"
                    for i, r in enumerate(f["確かめる項目"], 1)]
            out.append("")
        return out

    head = "| 名前 | 役割（何を防ぐためにあるか・出どころ） | 守っている要件（CC の読み） | いま動く場面 | 同じことを見るほかの hook | 試した結果・見つかった不具合 | 不具合の直し（済・まだ・不具合なし） | 7日で止めた回数（道具の前／ターンの終わり） | 打ち直しで通った回数 |"
    sep = "|---|---|---|---|---|---|---|---|---|"
    regd = [n for n in reg if n in names]
    unreg_sh = [p.name for p in sh if p.name not in reg]
    loose_py = [q.name for q in py if q.name not in reg and q.name not in attached]
    lines = [
        "# hook の一覧（ToDo の29番・_hook_inventory.py が settings.json・.claude/hooks・hook_inventory_src.json・_hook_usage_probe.py から作った＝手で書き換えない）",
        "",
        # ★2026-10-15（181回目・まこさん「hook_inventory.md の冒頭に以下を書いて」「修正フローも書いて置いて」「目的に…も、追加」）
        "## ★hook を見直す目的（まこさんの逐語・2026-10-15）",
        "",
        "> 目標達成に向けて、CCのミスを減らし、作業効率を上げる",
        "",
        "## ★hook を直すときの要件（まこさんの逐語・2026-10-15・恒久の決まり76番）",
        "",
        "> ★hook の直しは、応急処置ではなく根本から直し、同じミスが二度と起きない状態に「完全に」直す",
        ">",
        "> **★「CATの目標達成のため、engine_tunerの機能要件を満たしつつ、",
        "> 効率的かつ正確にプロジェクト進行したいが、",
        "> hookの不具合や、過剰なhook、不要なhookにより進行を妨げられている状態を完全に改善したい。」",
        "",
        "## ★修正フロー（1本ずつ・まこさん 2026-10-15「４０本をまとめて要不要の振り分け、修正ができないから、１本ずつ対応していく」「それでOK」）",
        "",
        "1. CC が、その hook の事実を、上の要件から出す。出す物＝役割、守っている要件（CAT の目標・engine_tuner の機能要件・効率的かつ正確な進行のどれを守るか）、"
        "進行を妨げている量（止めた回数・打ち直しで通った回数・正しい操作まで止めた例）、不具合の候補。要・過剰・不要の判断は書かない。",
        "2. まこさんが、要・過剰・不要を決める。CC は決めない。決まるまで、CC は直さない（2026-10-15 に、決まる前に3本を直した誤りが在る）。",
        "3. 不要＝直さずに止める。止める行（settings.json の登録）を、まこさんに見ていただいてから止める。",
        "4. 過剰＝守る物は在るが、正しい操作まで止めている。どこまで止めるようにするかの案を出し、まこさんの OK の後に直す。",
        "5. 要＝不具合の原因を確かめ、直し方の案を出す。案には、同じミスが二度と起きない仕組みと、直した後も防げない物を必ず書く。"
        "まこさんの OK の後に直し、止めるべき入力で止まることと、正しい入力で止まらないことの両方を試す。応急処置にしない。",
        "6. 元データ（hook_inventory_src.json）に、まこさんの振り分け・不具合の直し・試した結果を書き、この一覧を作り直す。",
        "7. 次の1本へ進む。全部 済んだら、まとめて監査に1回 出す（ToDo の32番）。そのあと、同じ状態に戻らない仕組みを作る（ToDo の33番）。",
        "",
        f"- settings.json の登録＝{stats['登録の件数']}件（名前は {stats['登録の名前']}本）。.claude/hooks の .sh＝{stats['sh']}本、.py＝{stats['py']}本（archive と __pycache__ は数えない）。",
        f"- 登録の名前で、実物のファイルが無い物＝{len(stats['登録の名前で実物が無い'])}本 {' '.join(stats['登録の名前で実物が無い'])}",
        "- 役割＝hook の本体の「役割:」の行か、説明の行「名前 — 役割」をプログラムが写した。どちらも無い物だけ手で書いた。",
        "- ❌️＝止めている hook（まこさん決定 2026-10-15「完全に不要なhookは停止→表の名前の前に❌️をつける」「OK」）。付け方は2つ＝①元データの「停止」に書いた物（登録を外した物）②登録が無く、どこからも名指しの無い物（プログラムが付ける）。❌️ は止めている印で、ファイルを消す意味ではない。",
        "- 作られたきっかけ＝本体のコメントの、日付とまこさんの言葉が在る最初の行をプログラムが写した。",
        "- 守っている要件＝CC の案（30番で、まこさんに振り分けていただく材料）。",
        "- 【まこさん：要】などの印＝まこさんが1本ずつ決めた振り分け（2026-10-15「hookを１本ずつ確かめて、不要か必要かを決める」）。"
        "決めた言葉・不具合・直した物・試した結果は「4. 1本ずつの詳しい中身」の「まこさんの振り分け」の行に在る。印の無い hook は、まだ1本ずつの確かめが来ていない。",
        "- 止めた回数は、_hook_usage_probe.py（直近7日のやり取りの記録）の数え方のとおり。打ち直しで通った回数＝止められた後、同じ操作をそのまま3手の内に打って通った回数。",
        "- 1本ずつの詳しい中身（本体・名指しの在る所・止める物）は、表の下の「4. 1本ずつの詳しい中身」に在る。",
        "",
        f"## 1. いま稼働している hook（settings.json に登録が在る・{len(regd)}本）",
        "", head, sep, *[row(n) for n in regd], "",
        f"## 2. 作ったが稼働していない hook（.sh が在るのに登録が無い・{len(unreg_sh)}本）",
        "", head, sep, *[row(n) for n in unreg_sh], "",
        f"## 3. どの .sh からも呼ばれず、登録も無い .py（{len(loose_py)}本・ほかの hook の部品か、使われていない物）",
        "", head, sep, *[row(n) for n in loose_py], "",
        "## 4. 1本ずつの詳しい中身", "",
        *[x for n in regd + unreg_sh + loose_py for x in detail(n)],
    ]
    stats.update({"1": regd, "2": unreg_sh, "3": loose_py, "hand": hand, "info": info, "decide": decide})
    return lines, stats


def digest(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:16]


def do_write() -> int:
    lines, st = build(usage())
    OUT.write_text(f"{HEAD}{digest(lines)} -->\n" + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"[_hook_inventory --write] {OUT.name} を書いた＝稼働 {len(st['1'])}本・登録なしの .sh {len(st['2'])}本・"
          f"呼ばれない .py {len(st['3'])}本（登録 {st['登録の件数']}件・.sh {st['sh']}本・.py {st['py']}本）")
    return do_verify()


def do_verify() -> int:
    ng: list[str] = []
    lines, st = build(None)
    if not OUT.exists():
        print(f"❌ [_hook_inventory --verify] {OUT.name} が無い → --write")
        return 2
    txt = OUT.read_text(encoding="utf-8").splitlines()
    m = re.match(rf"{re.escape(HEAD)}([0-9a-f]{{16}}) -->$", txt[0] if txt else "")
    if not m or m.group(1) != digest(txt[1:]):
        ng.append("1行目のハッシュ値と中身が合わない＝手で書き換えた → 元データを直して --write")
    # 止めた回数の欄を除けば、いまの元データと実物から作った物と同じか
    strip = lambda ls: [re.sub(r"\| [^|]* \| [^|]* \|$", "|", x) if x.startswith(("| `", "| ❌")) else x for x in ls]
    if strip(txt[1:]) != strip(lines):
        ng.append("中身が、いまの元データと実物（登録・ファイル・名指し・本体の説明の行）から作った物と違う → --write")
    if st["登録の名前で実物が無い"]:
        ng.append(f"登録の名前で実物のファイルが無い: {' '.join(st['登録の名前で実物が無い'])}")
    if len(st["1"]) + len(st["2"]) + len(st["3"]) + len(st["登録の名前で実物が無い"]) == 0:
        ng.append("一覧が空")
    for name, h in st["hand"].items():
        if not (HOOKS / name).is_file():
            ng.append(f"元データの名前 {name} の実物が .claude/hooks に無い")
        s = h.get("止める物") or ""
        if s and not CITE_RE.search(s):
            ng.append(f"{name} の「止める物」に根拠（ファイル名:行番号）が無い")
        ng += [f"{name} の根拠 {x}" for x in check_cites(s) + check_cites(h.get("印") or "") + check_cites(h.get("役割") or "")]
        ng += [f"{name} の確かめる項目の根拠 {x}" for r in (h.get("確かめる項目") or []) for x in check_cites(str(r.get("どこで", "")))]
    # ★2026-10-15（181回目）＝まこさんの振り分けの名前の実物と、根拠の行の実在も照らす（直す前は、このまとまりを読んでいなかった）
    for name, v in st["decide"].items():
        if not (HOOKS / name).is_file():
            ng.append(f"まこさんの振り分けの名前 {name} の実物が .claude/hooks に無い")
        ng += [f"{name} の振り分けの根拠 {x}" for x in check_cites(str(v))]
        # ★2026-10-15（まこさん「不具合を修正したかどうかは記述しなくていいの？」「OK」）＝振り分けを決めた hook は、直しの欄を空にしない
        if not (st["hand"].get(name) or {}).get("直し"):
            ng.append(f"{name} は振り分けを決めたのに、元データの「直し」の欄が空（済・まだ・不具合なし のどれかを書く）")
    print(f"[_hook_inventory --verify] まこさんの振り分け＝{len(st['decide'])}本（{'・'.join(st['decide'])}）")
    info = st["info"]
    for k, label in (("1", "稼働"), ("2", "登録なしの .sh"), ("3", "呼ばれない .py")):
        miss = {c: [n for n in st[k] if not info[n][f]] for c, f in
                (("止める物", "止める物"), ("役割", "役割"), ("守っている要件", "要件"))}
        print(f"[_hook_inventory --verify] {label}＝{len(st[k])}本のうち、まだの行＝止める物 {len(miss['止める物'])}本・"
              f"役割 {len(miss['役割'])}本・守っている要件 {len(miss['守っている要件'])}本")
        if k == "1":
            for c, ns in miss.items():
                if ns:
                    print(f"   稼働の中の、{c}がまだの行: " + " ".join(ns))
    if ng:
        print(f"❌ [_hook_inventory --verify] {len(ng)} 件:")
        for x in ng:
            print(f"   ・{x}")
        return 2
    print("✅ [_hook_inventory --verify] 文書は作ったまま・根拠の行は全部 実在・登録の名前は全部 実物が在る")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="hook の一覧を作る（ToDo の29番）")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.write:
        return do_write()
    if a.verify:
        return do_verify()
    ap.error("--write か --verify を指定してください")
    return 2


if __name__ == "__main__":
    sys.exit(main())
