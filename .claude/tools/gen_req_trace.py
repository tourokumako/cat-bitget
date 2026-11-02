#!/usr/bin/env python3
"""gen_req_trace.py — 要件の行・受ける工事・試験の対応表を作り、受け先の無い要件の行が在れば止める。

まこさんの許可（2026-11-02・ToDo の206番「ok」・恒久の決まり78番の宣言に対して）。

なぜ要るか
  指標の構造の工事で、要件の「engine_tuner が法則に沿ってその役割で組む」を、データの欄が在るだけで「受けている」と扱い、
  読む側の工事を ToDo に入れなかった（session_worklog_20261102.md §6-2・§6-6）。手で書いた対応表は、また抜ける。
  そこで要件の文書から行をプログラムが抜き出し、全部の行に工事と試験が無ければ止める。

何をするか
  1. 元データ（req_trace_src.json）の「読む範囲」から、要件の行を抜き出す。CC は行を選ばない。
     見出し・表の見出し・空の行だけを除く。同じ文は最初の1か所に数える。
  2. 元データの「割り当て」を上から順に当てる（節と語の正規表現）。最初に当たった行の工事と試験を、その要件の行に付ける。
     要件を受けない行（事実の記録ほか）は「対象外」に理由を書く。
  3. 表（req_trace.md）を書く。問題が在れば止める。

使い方
  python3 .claude/tools/gen_req_trace.py --check            # 止める条件を全部 出す（書かない・在れば終了コード 1）
  python3 .claude/tools/gen_req_trace.py --write            # 問題が無ければ表を作る
  python3 .claude/tools/gen_req_trace.py --verify           # 表が作り直した物と同じか
  python3 .claude/tools/gen_req_trace.py --gate <工事名>     # 設計書を作るプログラムと同じ判定を、画面に出す
  python3 .claude/tools/gen_req_trace.py --selftest         # 一時の置き場の見本で、止まる形と通る形を試す

限り（正直に）
  ①割り当ての中身が正しいか（その工事で本当に要件が満たされるか）は見ない＝監査で確かめる（ToDo の207番）。
  ②試験のコマンドは check_one_path.py の口を指す。測る処理がまだ無い試験は「未作」と出る（作る ToDo で足す）。
  ③「読む範囲」の外の行は数えない。外した範囲は元データの「読まない範囲」に理由つきで書く。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SRC = ROOT / ".claude" / "state" / "req_trace_src.json"
OUT = ROOT / ".claude" / "state" / "req_trace.md"
SESSIONS = ROOT / ".claude" / "state" / "sessions"
NEXT_STEP = ROOT / ".claude" / "state" / "next_step.md"
M2_TODO = ROOT / "v3-bitget-api-sdk" / "bitget-python-sdk-api" / ".claude" / "ratchet" / "m2_todo.json"
HEAD = "<!-- REQ_TRACE gen_req_trace.py が作った＝手で書き換えない・元データ＝req_trace_src.json -->"
GATE_FROM = 20261102                                   # この日より前の名前の工事は、門を掛けない（作り終えた工事を作り直せなくしないため）
DONE = "済"                                            # 済んだ工事は「済＝161番」の形で書く（ToDo の表から消えているため）
CHECK_WORD = "作った後の確認"                            # 機能を作る ToDo の行に必ず書く語


def _norm(s: str) -> str:
    """同じ文を見分けるための形（引用の印・字下げ・太字を取る）。"""
    s = re.sub(r"^[\s>]+", "", s)
    return re.sub(r"\s+", " ", s.replace("**", "")).strip()


def extract(spec: list, root: pathlib.Path = ROOT) -> list:
    """「読む範囲」の全部から要件の行を抜き出す。戻り＝[{id, 出どころ, 行, 節, 文}]。範囲の語が見つからなければ止める。"""
    rows, seen = [], set()
    for sp in spec:
        path = root / sp["ファイル"]
        lines = path.read_text(encoding="utf-8").splitlines()
        hit = [i for i, ln in enumerate(lines) if ln.startswith(sp["始まり"])]
        if not hit:
            raise SystemExit(f"[gen_req_trace] 範囲の始まりが無い: {sp['ファイル']}「{sp['始まり']}」（fail-closed）")
        start = hit[0]
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith(sp["終わり"])), None)
        if end is None:
            raise SystemExit(f"[gen_req_trace] 範囲の終わりが無い: {sp['ファイル']}「{sp['終わり']}」（fail-closed）")
        sec = sp["名前"]
        for i in range(start, end):
            ln = lines[i]
            st = ln.strip()
            if st.startswith("#"):
                sec = f"{sp['名前']}｜{st.lstrip('# ').strip()}"
                continue
            if not st or st.startswith("```") or st.startswith("写す元") or st.startswith("［手書き］"):
                continue
            if re.fullmatch(r"\|[\s:|-]+\|", st):
                continue
            if st.startswith("|") and i + 1 < end and re.fullmatch(r"\|[\s:|-]+\|", lines[i + 1].strip()):
                continue                                # 表の見出しの行
            txt = _norm(ln)
            if not txt or txt in seen:
                continue                                # 引用の印だけの行と、同じ文
            seen.add(txt)
            rows.append({"id": hashlib.sha1(txt.encode("utf-8")).hexdigest()[:10], "出どころ": sp["ファイル"],
                         "行": i + 1, "節": sec, "文": txt})
    return rows


def assign(rows: list, rules: list) -> tuple:
    """割り当てを上から順に当てる。戻り＝(行→割り当ての番号の辞書, 1行も当たらなかった割り当ての番号の一覧)。"""
    got, used = {}, set()
    for r in rows:
        for n, rule in enumerate(rules):
            if rule.get("節") and not re.search(rule["節"], r["節"]):
                continue
            if rule.get("語") and not re.search(rule["語"], r["文"]):
                continue
            got[r["id"]] = n
            used.add(n)
            break
    return got, [n for n in range(len(rules)) if n not in used]


def known_numbers(root: pathlib.Path = ROOT) -> set:
    """工事に書いてよい番号＝いちばん新しいセッションの ToDo・next_step の表・M2 のやることの番号。"""
    out: set = set()
    sess = root / SESSIONS.relative_to(ROOT)
    todos = sorted(sess.glob("*/session_todo.md"), key=lambda p: p.stat().st_mtime)
    for p in ([todos[-1]] if todos else []) + [root / NEXT_STEP.relative_to(ROOT)]:
        if p.exists():
            out |= set(re.findall(r"^\|\s*\**(\d+)\**\s*\|", p.read_text(encoding="utf-8"), flags=re.M))
    m2 = root / M2_TODO.relative_to(ROOT)
    if m2.exists():
        for t in json.loads(m2.read_text(encoding="utf-8")).get("やること") or []:
            if isinstance(t, dict) and t.get("番号"):
                out.add(str(t["番号"]))
    return out


def todo_rows(root: pathlib.Path = ROOT) -> dict:
    """いちばん新しいセッションの ToDo の行（無ければ next_step の表）。戻り＝{番号: 行の全文}。"""
    sess = root / SESSIONS.relative_to(ROOT)
    todos = sorted(sess.glob("*/session_todo.md"), key=lambda p: p.stat().st_mtime)
    p = todos[-1] if todos else root / NEXT_STEP.relative_to(ROOT)
    if not p.exists():
        return {}
    return {m.group(1): m.group(0) for m in re.finditer(r"^\|\s*\**(\d+)\**\s*\|.*$", p.read_text(encoding="utf-8"), flags=re.M)}


def check_problems(src: dict, root: pathlib.Path = ROOT) -> list:
    """作った後の確認の止める理由（まこさん 2026-11-02「todoには、機能構築後の確認を毎回入れるようにしてほしい」）。"""
    bad = []
    tests, chk, skip = src.get("試験") or {}, src.get("確認") or {}, src.get("確認が要らない行") or {}
    for no, line in todo_rows(root).items():
        if "✅済" in line:
            continue
        if no in chk:
            if CHECK_WORD not in line:
                bad.append(f"ToDo {no} の行に「{CHECK_WORD}」の文が無い")
        elif no not in skip:
            bad.append(f"作った後の確認の無い機能の ToDo: {no}（元データの「確認」か「確認が要らない行」に書く）")
    used = {t for v in chk.values() for t in v}
    for no, ts in chk.items():
        for t in ts:
            if t not in tests:
                bad.append(f"ToDo {no} の確認の試験 {t} が、元データの「試験」に無い")
    if not src.get("試験のコマンド"):
        bad.append("元データの「試験のコマンド」が空")
    for t in tests:
        if t not in used:
            bad.append(f"試験 {t} が、どの ToDo の確認にも入っていない")
    return bad


def problems(src: dict, rows: list, known: set, root: pathlib.Path = ROOT) -> list:
    """止める理由を全部 返す（1つずつ当たらないように、一度に出す）。"""
    bad = check_problems(src, root)
    rules, tests = src.get("割り当て") or [], src.get("試験") or {}
    got, dead = assign(rows, rules)
    for r in rows:
        if r["id"] not in got:
            bad.append(f"割り当てが無い要件の行: {r['出どころ']}:{r['行']}（{r['節']}）{r['文'][:70]}")
    for n in dead:
        bad.append(f"どの要件の行にも当たらない割り当て: {n}番 {json.dumps(rules[n], ensure_ascii=False)[:120]}")
    for n, rule in enumerate(rules):
        if rule.get("対象外"):
            if rule.get("工事") or rule.get("試験"):
                bad.append(f"割り当て {n}番＝対象外なのに工事か試験が在る")
            continue
        if not rule.get("工事"):
            bad.append(f"割り当て {n}番に工事が無い（語＝{rule.get('語') or rule.get('節')}）")
        if not rule.get("試験"):
            bad.append(f"割り当て {n}番に試験が無い（語＝{rule.get('語') or rule.get('節')}）")
        for w in rule.get("工事") or []:
            if not str(w).startswith(DONE) and str(w) not in known:
                bad.append(f"割り当て {n}番の工事 {w} が、ToDo の表と M2 のやることに無い")
        for t in rule.get("試験") or []:
            if t not in tests:
                bad.append(f"割り当て {n}番の試験 {t} が、元データの「試験」に無い")
    return bad


def render(src: dict, rows: list) -> str:
    """対応表の本文を作る。"""
    rules, tests = src["割り当て"], src["試験"]
    got, _ = assign(rows, rules)
    def _cell(s):
        return s.replace("|", "／")
    L = [HEAD, "# 要件の行・工事・試験の対応表", "",
         f"要件の行＝{len(rows)} 行。元データ＝`.claude/state/req_trace_src.json`。作り直し＝`python3 .claude/tools/gen_req_trace.py --write`。", "",
         "## 読まない範囲と理由", ""]
    L += [f"- {x}" for x in src.get("読まない範囲") or []]
    cmd, owner = src.get("試験のコマンド") or "まだ", src.get("試験を作る番号") or {}
    L += ["", "## 試験の一覧", "", "| 番号 | 中身 | コマンド | 測る処理を作る ToDo |", "|---|---|---|---|"]
    L += [f"| {k} | {_cell(v['中身'])} | {_cell(cmd.replace('{番号}', k))} | {_cell(owner.get(k) or '—')} |" for k, v in tests.items()]
    L += ["", "## ToDo ごとの作った後の確認", "", "| ToDo | 走らせる試験 |", "|---|---|"]
    L += [f"| {k} | {'・'.join(v)} |" for k, v in (src.get("確認") or {}).items()]
    by_w: dict = {}
    for r in rows:
        for w in rules[got[r["id"]]].get("工事") or []:
            by_w[str(w)] = by_w.get(str(w), 0) + 1
    L += ["", "## 工事ごとの受ける行の数", "", "| 工事 | 行の数 |", "|---|---|"]
    L += [f"| {k} | {by_w[k]} |" for k in sorted(by_w)]
    L += ["", "## 対応表", "", "| 出どころ | 節 | 要件の行 | 工事 | 試験か対象外の理由 |", "|---|---|---|---|---|"]
    for r in rows:
        rule = rules[got[r["id"]]]
        w = "・".join(str(x) for x in rule.get("工事") or []) or "—"
        t = "・".join(rule.get("試験") or []) or f"対象外＝{rule.get('対象外')}"
        L.append(f"| {pathlib.Path(r['出どころ']).name}:{r['行']} | {_cell(r['節'][:40])} | {_cell(r['文'][:120])} | {w} | {_cell(t)} |")
    return "\n".join(L) + "\n"


def load_src(path: pathlib.Path = SRC) -> dict:
    if not path.exists():
        raise SystemExit(f"[gen_req_trace] 元データが無い: {path}（fail-closed）")
    return json.loads(path.read_text(encoding="utf-8"))


def design_gate(work: str, src_path: pathlib.Path = SRC, root: pathlib.Path = ROOT) -> list:
    """設計書を作ってよいか。止める理由の一覧を返す（空＝通す）。
    この日より前の日付の名前の工事と、日付の無い名前の工事は見ない（作り終えた工事と、自己テストの見本を止めないため）。"""
    m = re.search(r"-(\d{8})$", str(work or ""))
    if not m or int(m.group(1)) < GATE_FROM:
        return []
    src = load_src(src_path)
    rows = extract(src["読む範囲"], root)
    bad = problems(src, rows, known_numbers(root), root)
    nums = (src.get("工事の名前") or {}).get(work)
    if not nums:
        return bad + [f"対応表の元データの「工事の名前」に、この工事（{work}）が無い。どの ToDo の番号の工事かを書く"]
    got, _ = assign(rows, src["割り当て"])
    have = {str(w) for r in rows if r["id"] in got for w in src["割り当て"][got[r["id"]]].get("工事") or []}
    for n in nums:
        if str(n) not in have:
            bad.append(f"工事 {work} の番号 {n} が受ける要件の行が、対応表に1行も無い")
    return bad


def selftest() -> int:
    ok = True
    def t(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  {'✅' if cond else '❌'} {name}")
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / "a.md").write_text("# 要件\n\n## 節1\n\n- 行あ\n- 行い\n\n| 欄 | 中身 |\n|---|---|\n| か | き |\n\n# 次\n- 外\n", encoding="utf-8")
        sdir = root / ".claude" / "state" / "sessions" / "s1"
        sdir.mkdir(parents=True)
        (sdir / "session_todo.md").write_text(f"| 番号 | やること |\n|---|---|\n| 7 | 何か。{CHECK_WORD}＝走らせる |\n", encoding="utf-8")
        spec = [{"名前": "A", "ファイル": "a.md", "始まり": "# 要件", "終わり": "# 次"}]
        rows = extract(spec, root)
        t("T1 見出し・表の見出し・範囲の外を数えない（3行）", [r["文"] for r in rows] == ["- 行あ", "- 行い", "| か | き |"])
        tests = {"T": {"中身": "x"}}
        good = {"試験": tests, "割り当て": [{"語": "行あ", "工事": ["7"], "試験": ["T"]}, {"語": "行い", "工事": ["済＝1番"], "試験": ["T"]},
                                          {"節": "節1", "対象外": "事実"}], "読む範囲": spec, "工事の名前": {"w-20261102": ["7"]},
                "確認": {"7": ["T"]}, "確認が要らない行": {}, "試験のコマンド": "c {番号}"}
        known = known_numbers(root)
        def problems_(s):
            return problems(s, rows, known, root)
        t("T2 全部に受け先が在れば通る", problems_(good) == [])
        b = json.loads(json.dumps(good))
        b["確認"] = {}
        t("T14 確認の無い機能の ToDo で止まる", any("確認の無い機能の ToDo: 7" in x for x in problems_(b)))
        b = json.loads(json.dumps(good))
        b["確認"], b["確認が要らない行"] = {}, {"7": "文書だけ"}
        t("T15 確認が要らない行は止まらないが、試験の行き先が無いと止まる", any("どの ToDo の確認にも" in x for x in problems_(b)) and not any("確認の無い" in x for x in problems_(b)))
        b = json.loads(json.dumps(good))
        b["試験のコマンド"] = ""
        t("T16 試験のコマンドが空なら止まる", any("コマンド" in x for x in problems_(b)))
        (sdir / "session_todo.md").write_text("| 番号 | やること |\n|---|---|\n| 7 | 何か |\n", encoding="utf-8")
        t("T17 行に確認の文が無いと止まる", any("の文が無い" in x for x in problems_(good)))
        (sdir / "session_todo.md").write_text(f"| 番号 | やること |\n|---|---|\n| 7 | 何か。{CHECK_WORD}＝走らせる |\n", encoding="utf-8")
        b = json.loads(json.dumps(good))
        b["割り当て"] = b["割り当て"][:2]
        t("T3 割り当ての無い行で止まる", any("割り当てが無い" in x for x in problems_(b)))
        b = json.loads(json.dumps(good))
        b["割り当て"][0]["試験"] = []
        t("T4 試験の無い割り当てで止まる", any("試験が無い" in x for x in problems(b, rows, known)))
        b = json.loads(json.dumps(good))
        b["割り当て"][0]["工事"] = []
        t("T5 工事の無い割り当てで止まる", any("工事が無い" in x for x in problems(b, rows, known)))
        b = json.loads(json.dumps(good))
        b["割り当て"][0]["工事"] = ["999"]
        t("T6 ToDo に無い番号で止まる", any("999" in x for x in problems(b, rows, known)))
        b = json.loads(json.dumps(good))
        b["割り当て"].insert(0, {"語": "無い語", "工事": ["7"], "試験": ["T"]})
        t("T7 どの行にも当たらない割り当てで止まる", any("当たらない" in x for x in problems(b, rows, known)))
        b = json.loads(json.dumps(good))
        b["割り当て"][0]["試験"] = ["無い試験"]
        t("T8 一覧に無い試験で止まる", any("無い試験" in x for x in problems(b, rows, known)))
        f = root / "src.json"
        f.write_text(json.dumps(good, ensure_ascii=False), encoding="utf-8")
        t("T9 登録された工事の門は通る", design_gate("w-20261102", f, root) == [])
        t("T10 登録の無い新しい工事は止まる", any("工事の名前" in x for x in design_gate("x-20261103", f, root)))
        t("T11 古い工事と日付の無い工事は見ない", design_gate("x-20261101", f, root) == [] and design_gate("work", f, root) == [])
        t("T12 表に要件の行が全部 出る", all(r["文"].replace("|", "／")[:10] in render(good, rows) for r in rows))
        try:
            extract([{"名前": "A", "ファイル": "a.md", "始まり": "# 無い", "終わり": "# 次"}], root)
            t("T13 範囲の語が無ければ止まる", False)
        except SystemExit:
            t("T13 範囲の語が無ければ止まる", True)
    print("selftest:", "ok" if ok else "NG")
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    p.add_argument("--write", action="store_true")
    p.add_argument("--verify", action="store_true")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--gate", default="")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if a.gate:
        bad = design_gate(a.gate)
        print("\n".join(bad) if bad else f"門は通る: {a.gate}")
        return 1 if bad else 0
    src = load_src()
    rows = extract(src["読む範囲"])
    bad = problems(src, rows, known_numbers())
    print(f"要件の行＝{len(rows)} 行・止める理由＝{len(bad)} 件")
    if bad:
        print("\n".join(bad))
        return 1
    text = render(src, rows)
    if a.write:
        OUT.write_text(text, encoding="utf-8")
        print(f"書いた: {OUT}")
    elif a.verify:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("表が作り直した物と違う（--write で作り直す）")
            return 1
        print("表は作り直した物と同じ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
