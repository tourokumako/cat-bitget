#!/usr/bin/env python3
"""gen_audit_index.py — CP 監査一覧を `.claude/audits/` のファイル名から機械で作る（2026-08-25・まこさん指示）

なぜ在るか＝WORKFLOW.md の CP 監査一覧を手で足す運用は止まった（5月の CP6 で止まり、7〜8月の engine_tuner の
監査 cp1〜cp6 が1件も載っていなかった＝61回目に実測）。手書きの一覧は書き忘れると黙って腐る。
だから一覧は書かず、監査の依頼書（inputs/）と報告書（audits/ 直下）のファイル名から毎回 作る。

使い方:
  python3 .claude/tools/gen_audit_index.py            # 表を画面に出すだけ
  python3 .claude/tools/gen_audit_index.py --write    # WORKFLOW.md の目印の間に表を書く（ハッシュ値つき）
  python3 .claude/tools/gen_audit_index.py --verify   # 手で書き換えられていないか・作り直し忘れが無いかの検出（違えば exit 1）

決まり:
  ・表の中身は全部 ファイル名と報告書の Verdict の行から取る。CC が手で書く欄は無い。
  ・目印＝`<!-- AUDIT_INDEX_START hash=… -->` と `<!-- AUDIT_INDEX_END -->`（gen_auditor_brief.py と同じ型）。
  ・依頼書と報告書は「日付＋対象＋cp 番号」の幹で組にする。片方しか無いものも載せる（無い側は「—」）。
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
AUD = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits"
TARGET = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api/WORKFLOW.md"
START = "<!-- AUDIT_INDEX_START hash={h} ここは .claude/tools/gen_audit_index.py が自動生成＝手で書き換えない -->"
START_RE = re.compile(r"<!-- AUDIT_INDEX_START hash=[0-9a-f]* ?[^>]*-->")
END = "<!-- AUDIT_INDEX_END -->"
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_")
CP_RE = re.compile(r"_(cp\d+[a-z]?|audit\d+)(?:_|\.md$)")


def _stem(name: str) -> str:
    """依頼書と報告書を組にする幹＝ファイル名から _audit_request／_audit_report を外したもの。"""
    return re.sub(r"_audit_(request|report)\.md$", "", name).removesuffix(".md")


def _verdict(path: pathlib.Path) -> str:
    """報告書の中の Verdict の行（最初の1つ）から判定の言葉を取る。無ければ —。"""
    try:
        for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "Verdict" in ln:
                v = ln.split("Verdict", 1)[1]
                v = re.sub(r"^[\s:：*＝=]+", "", v).replace("**", "").strip()
                return (v[:60] + "…") if len(v) > 60 else (v or "—")
    except OSError:
        pass
    return "—"


def build_rows() -> list[dict]:
    rows: dict[str, dict] = {}
    for p in sorted(AUD.glob("*.md")):
        st = _stem(p.name)
        rows.setdefault(st, {"stem": st})["report"] = p
    for p in sorted((AUD / "inputs").glob("*.md")):
        if p.name.startswith("_"):
            continue                                   # 雛形（_template.md）は監査ではない
        st = _stem(p.name)
        rows.setdefault(st, {"stem": st})["request"] = p
    out = []
    for st, r in rows.items():
        src = r.get("report") or r.get("request")
        dm = DATE_RE.match(src.name)
        cm = CP_RE.search(src.name)
        out.append({
            "date": dm.group(1) if dm else "—",
            "cp": cm.group(1) if cm else "—",
            "task": re.sub(r"^\d{4}-\d{2}-\d{2}_", "", st),
            "request": r["request"].name if r.get("request") else "—",
            "report": r["report"].name if r.get("report") else "—",
            "verdict": _verdict(r["report"]) if r.get("report") else "（報告書なし）",
        })
    out.sort(key=lambda x: (x["date"], x["stem"] if "stem" in x else x["task"]))
    return out


def render() -> str:
    rows = build_rows()
    L = ["| 日付 | 印 | 対象（ファイル名の幹） | 依頼書（inputs/） | 報告書 | Verdict |", "|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['date']} | {r['cp']} | `{r['task']}` | {r['request']} | {r['report']} | {r['verdict']} |")
    L.append("")
    L.append(f"（{len(rows)} 件＝`.claude/audits/` の報告書 {sum(1 for r in rows if r['report'] != '—')} 本・依頼書 {sum(1 for r in rows if r['request'] != '—')} 本から機械で作った）")
    return "\n".join(L)


def _block(body: str) -> str:
    h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
    return START.format(h=h) + "\n" + body + "\n" + END


def write() -> int:
    t = TARGET.read_text(encoding="utf-8")
    m = START_RE.search(t)
    if not m or END not in t[m.end():]:
        print(f"⚠️ {TARGET.name} に AUDIT_INDEX_START/END の印がない（先に印を置く）")
        return 1
    e = t.index(END, m.end()) + len(END)
    TARGET.write_text(t[:m.start()] + _block(render()) + t[e:], encoding="utf-8")
    print(f"書いた: {TARGET.name} の CP 監査一覧（{len(build_rows())} 件）")
    return 0


def verify() -> int:
    t = TARGET.read_text(encoding="utf-8")
    m = START_RE.search(t)
    if not m or END not in t[m.end():]:
        print(f"❌ {TARGET.name} に AUDIT_INDEX_START/END の印がない")
        return 1
    e = t.index(END, m.end())
    inside = t[m.end():e].strip("\n")
    want = render()
    stored = re.search(r"hash=([0-9a-f]*)", m.group(0)).group(1)
    h_inside = hashlib.sha256(inside.encode("utf-8")).hexdigest()[:12]
    if stored != h_inside:
        print(f"❌ CP 監査一覧が手で書き換えられている（印のハッシュ値 {stored} ≠ 中身 {h_inside}）")
        return 1
    if inside != want:
        print("❌ CP 監査一覧が古い（audits/ のファイルが増えた・減った）→ --write で作り直す")
        return 1
    print(f"✅ CP 監査一覧は audits/ と一致（{len(build_rows())} 件・ハッシュ値 {stored}）")
    return 0


if __name__ == "__main__":
    if "--write" in sys.argv:
        sys.exit(write())
    if "--verify" in sys.argv:
        sys.exit(verify())
    print(render())
