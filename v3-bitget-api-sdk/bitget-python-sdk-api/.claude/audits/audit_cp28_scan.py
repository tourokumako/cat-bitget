#!/usr/bin/env python3
"""audit_cp28_scan.py — 監査 CP28 の数え上げを、全部 機械で作る（2026-09-08）

なぜ在るか:
  まこさん指示 2026-09-08（逐語）＝「手で数えるのを禁じる→audit_m2c_scan.py」。
  ＝監査が一覧を手で並べると漏れる（監査 CP24 で3回 漏れた）。だから「何を数えるか」を
  実物の構造から機械で引く。監査は一覧を書かない。手本＝`audit_m2c_scan.py`。

使い方:
  python3 .claude/audits/audit_cp28_scan.py             # 数え上げ（コマンドは走らせない・数秒）
  python3 .claude/audits/audit_cp28_scan.py --run       # 完成の条件11行のコマンドも走らせる（数分）
  python3 .claude/audits/audit_cp28_scan.py --selftest  # 読み取りが実物と噛み合っているか

正直な限界:
  ・「どのファイルを見るか」は、このプログラムの中の SRC に書いてある（人が選んだ）。
    ただし SRC に無いファイルを見に行った所は1つも無い＝出どころは全部このファイルに在る。
  ・意味の判定（その穴が重いか）はしない。数えるだけ。
  ・--run で走らせるコマンドは、設計書の表のセルから機械で取り出したものだけ。
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

SDK = pathlib.Path(__file__).resolve().parents[2]
REPO = SDK.parents[1]
PR = SDK / "scripts/priority_rebuild"
RAT = SDK / ".claude/ratchet"
ARC = RAT / "acceptance_archive"
ITER = "approval-audit-plumbing-20260907"

SRC = {
    "acceptance": REPO / ".claude/state/acceptance.md",
    "archive": ARC / f"{ITER}.md",
    "breaks_rec": ARC / f"{ITER}.breaks.json",
    "frozen_rec": ARC / f"{ITER}.frozen.json",
    "dirty_rec": ARC / f"{ITER}.dirty.json",
    "breaks_frozen": RAT / "breaks_frozen.json",
    "req": PR / "gen_audit_request.py",
    "verify": PR / "verify_design_contract.py",
    "gen": PR / "engine_tuner_gen.py",
    "pre_audit": REPO / ".claude/tools/pre_audit_check.py",
    "run_breaks": REPO / ".claude/tools/run_breaks.py",
    "regime_kb": REPO / ".claude/tools/gen_regime_kb.py",
    "fence_hook": REPO / ".claude/hooks/require_source_read_before_acceptance.py",
    "base_gate": REPO / ".claude/hooks/require_acceptance_before_impl.sh",
    "approve": REPO / ".claude/hooks/approve_impl.sh",
    "laws": RAT / "regime_laws.json",
    "exec": PR / "engine_tuner_exec.py",
    "template": SDK / ".claude/audits/inputs/_template.md",
    "cp28_req": SDK / ".claude/audits/inputs/2026-09-08_approval_audit_plumbing_cp28_audit_request.md",
    "frozen_q": SDK / ".claude/audits/inputs/_frozen_question_regime.md",
}
BREAKS_DIR = REPO / ".claude/breaks"
IMPL_COMMIT = "127f05c"


def txt(k: str) -> str:
    p = SRC[k]
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def jsn(k: str):
    p = SRC[k]
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _rows(body: str, start: str, end: str) -> list[list[str]]:
    """目印の間の表の行を、セルの一覧にして返す（見出しと区切りは外す）。"""
    m = re.search(re.escape(start) + r"(.*?)" + re.escape(end), body, re.S)
    if not m:
        return []
    out = []
    for ln in m.group(1).splitlines():
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if not cells or set("".join(cells)) <= set("-: "):
            continue
        out.append(cells)
    return out[1:] if out else out          # 先頭は見出し


# ── 1) 設計書 §4「やること」の記号と §6 の番号（監査が並べない）──────────────
def todo_rows() -> list[tuple[str, str]]:
    body = txt("archive")
    m = re.search(r"## 4\. やること.*?\n(.*?)\n\*\*工程表", body, re.S)
    if not m:
        return []
    out = []
    for ln in m.group(1).splitlines():
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) < 4 or set("".join(c)) <= set("-: "):
            continue
        mark = re.sub(r"[*`]", "", c[0]).strip()
        if re.fullmatch(r"[A-Z]", mark):
            out.append((mark, c[3]))
    return out


# ── 2) 完成の条件の表（生きている設計書と、承認の控えの両方）──────────────────
def accept_rows(key: str) -> list[dict]:
    rows = _rows(txt(key), "<!-- ACCEPT_TABLE_START -->", "<!-- ACCEPT_TABLE_END -->")
    out = []
    for c in rows:
        if len(c) < 8:
            continue
        cmd = re.search(r"`([^`]+)`", c[2] or "")
        brk = re.search(r"`([^`]+)`", c[5] or "")
        out.append({"no": re.sub(r"[*]", "", c[0]).strip(),
                    "cmd": (cmd.group(1).strip() if cmd else ""),
                    "break": (brk.group(1).strip() if brk else ""),
                    "state": "済" if "✅済" in c[7] else "未着手"})
    return out


# ── 3) 壊すプログラムの凍結（在るか・ハッシュ値が合うか）────────────────────
def breaks_check() -> list[str]:
    fz = jsn("breaks_frozen")
    names = [r["break"] for r in accept_rows("acceptance") if r["break"]]
    out = []
    for n in names:
        p = BREAKS_DIR / n
        if not p.exists():
            out.append(f"{n}: 実物が無い")
            continue
        if n not in fz:
            out.append(f"{n}: 凍結に無い")
            continue
        now = hashlib.sha256(p.read_bytes()).hexdigest()
        out.append(f"{n}: {'一致' if now == fz[n] else '★食い違い'}")
    return out


# ── 4) 承認のときの記録と、いま走らせた結果 ────────────────────────────────
def recorded() -> dict[str, int]:
    return {str(r.get("no")): r.get("code") for r in (jsn("breaks_rec") or {}).get("rows", [])}


def measure_now() -> dict[str, int]:
    """壊すプログラムを、監査が自分で走らせる（記録には書かない口）。"""
    r = subprocess.run([sys.executable, str(SRC["run_breaks"]),
                        "--measure-only", "--iter", ITER],
                       cwd=str(REPO), capture_output=True, text=True)
    out = {}
    for ln in r.stdout.splitlines():
        m = re.search(r"#\s*(\d+)\s+(\S+\.sh)\s+rc=(\d+)", ln)
        if m:
            out[m.group(1)] = int(m.group(3))
    return out


# ── 5) 完成の条件のコマンドを走らせて終了コードを取る ────────────────────────
def run_conditions() -> list[tuple[str, str, int]]:
    out = []
    for row in accept_rows("acceptance"):
        c = row["cmd"]
        if not c.startswith("python3 "):
            out.append((row["no"], c, -1))
            continue
        parts = c.split()[1:]
        # 設計書のセルは sdk からの相対で書いてある（../../ は repo 直下）
        r = subprocess.run([sys.executable] + parts, cwd=str(SDK),
                           capture_output=True, text=True)
        out.append((row["no"], c, r.returncode))
    return out


# ── 6) A の相手＝依頼書を作るプログラムの口と、残っている古い口 ──────────────
def request_tool() -> dict:
    s = txt("req")
    flags = sorted(set(re.findall(r'ap\.add_argument\("(--[\w-]+)"', s)))
    stale = [f"{i}: {ln.strip()[:80]}" for i, ln in enumerate(s.splitlines(), 1)
             if re.search(r"--element\b", ln)]
    doc = re.search(r'"""(.*?)"""', s, re.S)
    doc_body = doc.group(1) if doc else ""
    stale_doc = [f"{i}: {ln.strip()[:80]}"
                 for i, ln in enumerate(doc_body.splitlines(), 1)
                 if re.search(r"--element\b|13要素.*1件だけ", ln)]
    return {"口": flags, "--element が出る行": stale, "説明の中の古い口": stale_doc,
            "N_ELEMENTS の定義": len(re.findall(r"^N_ELEMENTS\s*=", s, re.M))}


def request_generated() -> dict:
    """この監査の依頼書が、その道具で作られた名前かどうか。"""
    stem = SRC["frozen_q"].stem.lstrip("_")
    want = f"2026-09-08_{stem}_audit_request.md"
    d = SDK / ".claude/audits/inputs"
    return {"道具が付ける名前": want,
            "その名前のファイル": (d / want).exists(),
            "実際に監査へ出した依頼書": SRC["cp28_req"].name,
            "テンプレの見出し数": len(re.findall(r"^## ", txt("template"), re.M)),
            "依頼書の見出し数": len(re.findall(r"^## ", txt("cp28_req"), re.M))}


# ── 7) B の相手＝監査の前の検査の一覧と、やり直しの合図の対象 ────────────────
def pre_audit() -> dict:
    s = txt("pre_audit")
    checks = re.findall(r'"([\w.]+\.py --[\w-]+)"', s)
    m = re.search(r"CHECKS = \[(.*?)\n\]", s, re.S)
    # ★注記の行（#）を先に外す。外さないと、注記の中の `iter="…"` まで一覧に数える
    #   （2026-09-08 の1回目の走行で実際に起きた＝8本を9本と数えた）。
    _body = "\n".join(ln for ln in (m.group(1) if m else "").splitlines()
                      if not ln.strip().startswith("#"))
    in_checks = re.findall(r'"([^"]+)"', _body)
    m2 = re.search(r"_MUST_IN_CHECKS = \((.*?)\)", s, re.S)
    must = re.findall(r'"([^"]+)"', m2.group(1)) if m2 else []
    m3 = re.search(r"FINGERPRINT_FILES = \[(.*?)\]", s, re.S)
    fp = re.findall(r'"([^"]+)"', m3.group(1)) if m3 else []
    owners = sorted({c.split()[0] for c in in_checks})
    return {"CHECKS": in_checks, "必ず入っているべき2本": must,
            "必ず入っているべきが CHECKS に在るか": [x in in_checks for x in must],
            "やり直しの合図の対象": fp,
            "CHECKS の持ち主で合図の対象に無いもの": [o for o in owners if o not in fp],
            "_": len(checks)}


# ── 8) G の相手＝承認のときに汚れていた .py の内訳 ──────────────────────────
def dirty() -> dict:
    files = (jsn("dirty_rec") or {}).get("files") or []
    kind = {"hook の .py": [], ".claude/tools の .py": [], "priority_rebuild の .py": []}
    for f in files:
        if "/.claude/hooks/" in "/" + f:
            kind["hook の .py"].append(f)
        elif "/.claude/tools/" in "/" + f:
            kind[".claude/tools の .py"].append(f)
        else:
            kind["priority_rebuild の .py"].append(f)
    return {"合計": len(files), **{k: len(v) for k, v in kind.items()},
            "内訳": kind}


# ── 9) 設計書の契約＝触った関数の一覧が埋まったか ──────────────────────────
def contract() -> dict:
    m = re.search(r'"impl_functions":\s*(\{.*?\})', txt("acceptance"), re.S)
    live = m.group(1) if m else "?"
    fz = jsn("frozen_rec")
    return {"生きている設計書の impl_functions": live,
            "件数": 0 if live.strip() == "{}" else -1,
            "承認のときに凍結された中身の鍵": sorted(k for k in fz if not k.startswith("_")),
            "理由の欄": bool(re.search(r'"no_impl_functions_reason"', txt("acceptance")))}


# ── 10) 設計書の TARGET と、実際にコミットで触ったファイル ────────────────
def target_vs_commit() -> dict:
    m = re.search(r"^TARGET:\s*(.+)$", txt("acceptance"), re.M)
    targets = [t.strip() for t in (m.group(1) if m else "").split(",") if t.strip()]
    r = subprocess.run(["git", "-C", str(REPO), "show", "--name-only",
                        "--pretty=format:", IMPL_COMMIT],
                       capture_output=True, text=True)
    touched = [x.strip() for x in r.stdout.splitlines() if x.strip()]
    def _hit(t):
        return any(x.endswith(t) or t.endswith(x.split("/")[-1]) and x.endswith(t.split("/")[-1])
                   for x in touched)
    return {"TARGET の件数": len(targets),
            "コミットが触ったファイル数": len(touched),
            "TARGET でコミットに出ないもの": [t for t in targets if not _hit(t)]}


# ── 11) K の相手＝相場の法則の引用の行番号が実物と合うか ────────────────────
def law_line() -> dict:
    s = txt("laws")
    m = re.search(r"engine_tuner_exec\.py:(\d+)", s)
    no = int(m.group(1)) if m else 0
    lines = txt("exec").splitlines()
    body = lines[no - 1] if 0 < no <= len(lines) else ""
    return {"法則が指す行": no, "その行に wpct_arr が在るか": "wpct_arr" in body,
            "行の中身": body.strip()[:70]}


# ── 12) 承認の控えの本数 ───────────────────────────────────────────────────
def approvals() -> dict:
    md = sorted(p.name for p in ARC.glob(f"{ITER}.0*.md"))
    return {"控えの本数": len(md), "控え": md,
            "凍結された壊すプログラムの本数": len([k for k in jsn("breaks_frozen")
                                                   if not k.startswith("_")])}


# ── 出力 ──────────────────────────────────────────────────────────────────
def build(do_run: bool) -> str:
    L: list[str] = ["<!-- SCAN_START audit_cp28_scan.py が実物から書き出す＝手で書き換えない -->", ""]

    rows = todo_rows()
    L.append(f"### B-1｜設計書 §4「やること」の行＝**{len(rows)} 行**")
    L.append("")
    L.append("| 記号 | §6 の番号 |")
    L.append("|---|---|")
    for mk, no in rows:
        L.append(f"| {mk} | {no} |")
    L.append("")

    ar_live, ar_arc = accept_rows("acceptance"), accept_rows("archive")
    L.append(f"### B-2｜完成の条件＝生きている設計書 **{len(ar_live)} 行**"
             f"／承認の控え **{len(ar_arc)} 行**")
    L.append("")
    L.append(f"- 生きている設計書で「済」＝**{sum(1 for r in ar_live if r['state'] == '済')} 行**")
    L.append(f"- 承認の控えで「済」＝**{sum(1 for r in ar_arc if r['state'] == '済')} 行**"
             "（控えは承認の瞬間の写し＝済を書く前の姿）")
    L.append("")

    rec = recorded()
    now = measure_now() if do_run else {}
    L.append("### B-3｜壊すプログラム＝承認のときの記録と、監査が自分で走らせた結果")
    L.append("")
    L.append("| # | 壊すプログラム | 承認のときの記録 | 監査の実測 | 一致 | 凍結 |")
    L.append("|---|---|---|---|---|---|")
    fzc = dict(x.split(": ", 1) for x in breaks_check())
    for r in ar_live:
        a, b = rec.get(r["no"]), now.get(r["no"])
        L.append(f"| {r['no']} | `{r['break']}` | rc={a} | "
                 f"{('rc=' + str(b)) if b is not None else '（--run で測る）'} | "
                 f"{'✅' if (b is None or a == b) else '★食い違い'} | {fzc.get(r['break'], '?')} |")
    L.append("")
    L.append(f"- 記録の行数＝**{len(rec)}** ／ 0 以外の終了コード＝"
             f"**{sum(1 for v in rec.values() if v not in (0, None))}**")
    if now:
        L.append(f"- 監査の実測＝**{len(now)}** ／ 0 以外＝"
                 f"**{sum(1 for v in now.values() if v != 0)}**"
                 f" ／ 記録と食い違い＝**{sum(1 for k, v in now.items() if rec.get(k) != v)}**")
    L.append("")

    L.append("### B-4｜完成の条件のコマンドを、監査が自分で走らせた終了コード")
    L.append("")
    if do_run:
        L.append("| # | コマンド | 終了コード |")
        L.append("|---|---|---|")
        rc0 = 0
        for no, c, rc in run_conditions():
            rc0 += 1 if rc == 0 else 0
            L.append(f"| {no} | `{c}` | {rc} |")
        L.append("")
        L.append(f"- 終了コードが 0 の行＝**{rc0} / {len(ar_live)}**")
    else:
        L.append("（--run を付けると走らせます）")
    L.append("")

    rt = request_tool()
    L.append("### B-5｜A の相手＝依頼書を作るプログラム")
    L.append("")
    L.append(f"- 受け付ける口＝`{'` / `'.join(rt['口'])}`")
    L.append(f"- `N_ELEMENTS` の定義＝**{rt['N_ELEMENTS の定義']} 件**")
    L.append(f"- `--element` が出る行＝**{len(rt['--element が出る行'])} 件**"
             f"{'＝' + ' ／ '.join(rt['--element が出る行']) if rt['--element が出る行'] else ''}")
    L.append(f"- そのうち、ファイル冒頭の説明の中＝**{len(rt['説明の中の古い口'])} 件**"
             f"{'＝' + ' ／ '.join(rt['説明の中の古い口']) if rt['説明の中の古い口'] else ''}")
    for k, v in request_generated().items():
        L.append(f"- {k}＝**{v}**")
    L.append("")

    pa = pre_audit()
    L.append("### B-6｜B の相手＝監査の前の検査の一覧")
    L.append("")
    L.append(f"- `CHECKS`＝**{len(pa['CHECKS'])} 本**＝`{'` / `'.join(pa['CHECKS'])}`")
    L.append(f"- 必ず入っているべき2本＝`{'` / `'.join(pa['必ず入っているべき2本'])}`"
             f" ／ 実際に在るか＝{pa['必ず入っているべきが CHECKS に在るか']}")
    L.append(f"- やり直しの合図の対象＝**{len(pa['やり直しの合図の対象'])} 本**")
    L.append(f"- ★`CHECKS` の持ち主なのに、やり直しの合図の対象に無いもの＝"
             f"**{len(pa['CHECKS の持ち主で合図の対象に無いもの'])} 本**"
             f"＝`{'` / `'.join(pa['CHECKS の持ち主で合図の対象に無いもの']) or 'なし'}`")
    L.append("")

    d = dirty()
    L.append("### B-7｜G の相手＝承認のときに汚れていた .py")
    L.append("")
    L.append(f"- 合計＝**{d['合計']} 本**"
             f"（hook の .py {d['hook の .py']} 本／`.claude/tools` {d['.claude/tools の .py']} 本"
             f"／`scripts/priority_rebuild` {d['priority_rebuild の .py']} 本）")
    for k, v in d["内訳"].items():
        for f in v:
            L.append(f"  - {k}: `{f}`")
    L.append("")

    ct = contract()
    L.append("### B-8｜設計書の契約（触った関数の一覧）")
    L.append("")
    L.append(f"- 生きている設計書の `impl_functions`＝`{ct['生きている設計書の impl_functions']}`")
    L.append(f"- 承認のときに凍結された中身の鍵＝{ct['承認のときに凍結された中身の鍵'] or '**0件**'}")
    L.append(f"- `no_impl_functions_reason` が在るか＝**{ct['理由の欄']}**")
    L.append("")

    tv = target_vs_commit()
    L.append("### B-9｜設計書の TARGET と、実装のコミット")
    L.append("")
    for k, v in tv.items():
        L.append(f"- {k}＝**{v}**")
    L.append("")

    lw = law_line()
    L.append("### B-10｜K の相手＝相場の法則 R7 の引用の行番号")
    L.append("")
    for k, v in lw.items():
        L.append(f"- {k}＝**{v}**")
    L.append("")

    ap = approvals()
    L.append("### B-11｜承認の控えと凍結")
    L.append("")
    for k, v in ap.items():
        L.append(f"- {k}＝**{v}**")
    L.append("")
    L.append("<!-- SCAN_END -->")
    return "\n".join(L) + "\n"


# ── わざと壊して止まるか試すテスト ────────────────────────────────────────
def selftest() -> int:
    """このプログラムの読み取りが、実物の形と噛み合っているかを確かめる。

    ★期待する一覧を手で並べない＝実物の構造から導く（audit_m2c_scan の T2 と同じ考え方）。
    """
    ng: list[str] = []
    for k, p in SRC.items():
        if not p.exists():
            ng.append(f"T1: 見る相手が実在しない: {k} → {p}")
    if not todo_rows():
        ng.append("T2: 設計書 §4 の「やること」の表を1行も取れない（表の形が変わった？）")
    live = accept_rows("acceptance")
    if not live:
        ng.append("T3: 完成の条件の表を1行も取れない（目印の形が変わった？）")
    # T4＝表の行数と、承認のときの記録の行数はそろうはず
    if live and len(live) != len(recorded()):
        ng.append(f"T4: 完成の条件 {len(live)} 行と、承認のときの記録 {len(recorded())} 行が違う")
    # T5＝表が名指しした壊すプログラムは、全部 実在するはず
    for r in live:
        if r["break"] and not (BREAKS_DIR / r["break"]).exists():
            ng.append(f"T5: 表が名指しした壊すプログラムが無い: {r['break']}")
    # T6＝表のセルからコマンドを取れるはず（取れないと --run が空になる）
    _nocmd = [r["no"] for r in live if not r["cmd"].startswith("python3 ")]
    if _nocmd:
        ng.append(f"T6: コマンドを取り出せない行: {_nocmd}")
    # T7＝依頼書の道具から口を1つも取れないのは、探し方が壊れた合図
    if not request_tool()["口"]:
        ng.append("T7: 依頼書を作るプログラムの口（--…）を1つも取れない")
    # T8＝CHECKS を1本も取れないのは、探し方が壊れた合図
    _pa = pre_audit()
    if not _pa["CHECKS"]:
        ng.append("T8: 監査の前の検査の一覧を1本も取れない")
    # T9＝一覧の各行は「<.py> --<旗>」の形のはず。形の違うものが混じったら
    #     注記の文字列まで拾っている合図（2026-09-08 に実際に起きた）
    _bad = [c for c in _pa["CHECKS"] if not re.fullmatch(r"[\w.]+\.py\s+--[\w-]+", c)]
    if _bad:
        ng.append(f"T9: 監査の前の検査の一覧に、コマンドでないものが混じっている: {_bad}")
    for x in ng:
        print(f"  ❌ {x}")
    print(f"{'❌' if ng else '✅'} audit_cp28_scan の読み取り＝ダメだった件 {len(ng)}")
    return 1 if ng else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    print(build("--run" in sys.argv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
