#!/usr/bin/env python3
"""gen_design_sections.py — 設計書の §4（設計の中身）に何を書くべきかを、3つの出どころから抜く。

なぜ作るか
----------
まこさん指摘 2026-09-10（逐語）＝「物事を組み立てる順番や複合要因の組み合わせ方など、
思考が支離滅裂でその場しのぎすぎるんだよ」「どうしたらちゃんとできるんだ？」。

私は §4 の項目を思いつきで足し、**4回とも まこさんの問いで「出どころに在るのに項目に
入っていないもの」が出た**（①8項目→「今回の設計に寄ってる」②別の AI が15件 ③「制約」
④「仕組みの宣言」）。原因＝**出どころを1つも挙げずに始めた**（恒久の決まり39番＝設計は
正本の網羅一覧との全数照合から始める、に反した）。

だから、この道具が3つの出どころから**全部 抜いて通し番号を振り**、
**どの項目にも入っていない番号を機械が出す**。私が「もう無い」と判断する場所をなくす。

3つの出どころ
------------
  A うちの正本      permanent_rules.md（恒久70番・69番）／acceptance_checklist.md／hook
  B 外の標準        design_section_sources.json（本文から取った逐語）
  C 過去の指摘      worklog 全部（「設計書」＋入っていないことを指す語の行）

使い方
------
  --run     抜いて画面に出す
  --write   抜いて design_sections.md に書く
  --check   割り当て（design_section_map.json）を検算する
            ＝「出どころに在るのに、どの項目にも入っていないもの」を出す。
              0件でなければ終了コード 1。

fail-closed（黙って通さない）
  1. 出どころの JSON が読めない → 止まる
  2. B の件数が 0 → 止まる（外の標準を1件も持たずに項目を作らない）
  3. A の抜き出しが 0件 → 止まる（正本を読めていないのに進まない）
  4. C の抜き出しが 0件 → 止まる（過去の指摘を1件も見ずに進まない）
  5. --check で、実在しない番号を指している項目が在る → 止まる（打ち間違いを見逃さない）

限界（正直に）
  ・この道具は「抜く」と「検算する」までで、**項目に分類するのは私（CC）**。
    分類は意味の判断なので機械ではできない。
  ・C の抜き方は語の当てはめ。**別の言い方をした指摘は拾えない。**
  ・恒久71番＝この道具は文書を作る道具なので、壊すプログラムは付けない。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
RATCHET = SDK / ".claude" / "ratchet"
RULES = ROOT / ".claude" / "rules"
STATE = ROOT / ".claude" / "state"
HOOKS = ROOT / ".claude" / "hooks"

SRC = RATCHET / "design_section_sources.json"
MAP = RATCHET / "design_section_map.json"
DEST = RATCHET / "design_sections.md"
PERM = RULES / "permanent_rules.md"
CHECKLIST = SDK / ".claude" / "rules" / "acceptance_checklist.md"

# C の抜き方＝「設計」を含み、かつ「入っていない」ことを指す語を含む行
MISS_WORDS = ("無い", "落ち", "入っていない", "書いてない", "足りない", "抜け", "ヌケ", "漏れ", "コア")


def _load(path: Path, why: str) -> dict:
    if not path.exists():
        raise SystemExit(f"[gen_design_sections] {why} が無い: {path}（fail-closed）")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"[gen_design_sections] {why} が読めない: {e}（fail-closed）")


# ══ B 外の標準（JSON から読むだけ）════════════════════════════════

def collect_b(d: dict) -> list[tuple[str, str, str, str]]:
    """(番号, 出どころ, 項目, 逐語) の一覧を作る。"""
    rows: list[tuple[str, str, str]] = []
    b = d.get("B_外の標準") or {}

    ieee = b.get("IEEE_1016_2009") or {}
    for v in ieee.get("視点") or []:
        rows.append(("IEEE 1016-2009 の設計の視点", v["名前"], v["逐語"]))

    goog = b.get("Google_design_doc") or {}
    for v in goog.get("節") or []:
        rows.append(("Google の design doc", v["名前"], v["逐語"]))

    rng = b.get("Range_Tech_Spec") or {}
    q = rng.get("Detailed_design_が投げる問い_逐語") or ""
    for one in [x.strip() for x in q.split("?") if x.strip()]:
        rows.append(("Range の Tech Spec の問い", one + "?", ""))

    if not rows:
        raise SystemExit("[gen_design_sections] B（外の標準）が0件（fail-closed 2）")
    return [(f"B-{i}", s, n, qq) for i, (s, n, qq) in enumerate(rows, 1)]


# ══ A うちの正本（実物から抜く）════════════════════════════════════

def collect_a() -> list[tuple[str, str, str]]:
    """(番号, 出どころ, 求めていること) の一覧を、正本の実物から抜く。"""
    rows: list[tuple[str, str]] = []

    if not PERM.exists():
        raise SystemExit(f"[gen_design_sections] 正本が無い: {PERM}（fail-closed 3）")
    perm = PERM.read_text(encoding="utf-8")

    # 恒久70番＝設計書の7つの節と §4 の中身
    m = re.search(r"^70\. \*\*★engine_tuner.*?$", perm, re.M)
    if m:
        line = m.group(0)
        m4 = re.search(r"\*\*④設計の中身\*\*（(.+?)）", line)
        if m4:
            for piece in re.split(r"／", m4.group(1)):
                piece = piece.strip()
                if piece:
                    rows.append(("恒久70番 §4 の中身", piece))
        for sec in re.findall(r"\*\*([①-⑦][^*]+)\*\*", line):
            rows.append(("恒久70番 7つの節", sec.strip()))

    # 恒久69番＝手で書いてよい5つ
    m = re.search(r"^69\. \*\*★文書.*?$", perm, re.M)
    if m:
        m5 = re.search(r"\*\*手で書いてよいのは5つだけ\*\*＝(.+?)。", m.group(0))
        if m5:
            for piece in re.split(r"[①-⑤]", m5.group(1)):
                piece = piece.strip()
                if piece:
                    rows.append(("恒久69番 手で書く5つ", piece))

    # acceptance_checklist.md の項目（hook が実際に求めるもの）
    if CHECKLIST.exists():
        for ln in CHECKLIST.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^- ☐ 【(群[12])】\s*(.+)$", ln.strip())
            if m:
                body = re.sub(r"\*\*", "", m.group(2))
                rows.append((f"acceptance_checklist（{m.group(1)}）", body[:110]))

    n_hook = 0
    for p in sorted(HOOKS.glob("*.sh")) + sorted(HOOKS.glob("*.py")):
        try:
            if "acceptance" in p.read_text(encoding="utf-8", errors="ignore"):
                n_hook += 1
        except Exception:
            pass
    rows.append(("hook（実測）", f"acceptance.md を相手にする hook＝{n_hook}本"))

    if not rows:
        raise SystemExit("[gen_design_sections] A（うちの正本）が0件（fail-closed 3）")
    return [(f"A-{i}", s, b) for i, (s, b) in enumerate(rows, 1)]


# ══ C 過去の指摘（worklog から抜く）══════════════════════════════

def collect_c() -> list[tuple[str, str, str]]:
    """(番号, いつの worklog, まこさんの逐語) の一覧を抜く。"""
    rows: list[tuple[str, str]] = []
    for p in sorted(STATE.glob("session_worklog_*.md")):
        day = p.stem.replace("session_worklog_", "")
        for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "設計" not in ln:
                continue
            if not any(w in ln for w in MISS_WORDS):
                continue
            for q in re.findall(r"「([^」]{12,120})」", ln):
                if any(w in q for w in MISS_WORDS) or "設計" in q:
                    rows.append((day, q))
    seen: set[str] = set()
    uniq: list[tuple[str, str]] = []
    for day, q in rows:
        if q in seen:
            continue
        seen.add(q)
        uniq.append((day, q))
    if not uniq:
        raise SystemExit("[gen_design_sections] C（過去の指摘）が0件（fail-closed 4）")
    return [(f"C-{i}", d, q) for i, (d, q) in enumerate(uniq, 1)]


# ══ 検算（割り当てを照らす）════════════════════════════════════

def check() -> int:
    """出どころに在るのに、どの項目にも入っていないものを出す。"""
    d = _load(SRC, "出どころの正本")
    a, b, c = collect_a(), collect_b(d), collect_c()
    all_ids = {x[0] for x in a} | {x[0] for x in b} | {x[0] for x in c}
    body = {x[0]: (x[1], x[-1]) for x in a}
    body.update({x[0]: (x[1], x[2]) for x in b})
    body.update({x[0]: (x[1], x[2]) for x in c})

    if not MAP.exists():
        print(f"❌ 割り当てがまだ在りません: {MAP}")
        print(f"   ＝出どころ {len(all_ids)}件 が全部、どの項目にも入っていません。")
        return 1

    m = _load(MAP, "割り当て")
    items = m.get("項目") or []
    used: set[str] = set()
    ghost: list[tuple[str, str]] = []
    for it in items:
        for sid in it.get("出どころ") or []:
            if sid not in all_ids:
                ghost.append((str(it.get("名前")), sid))
            used.add(sid)

    rc = 0
    if ghost:
        print(f"❌ 実在しない番号を指している項目が {len(ghost)}件（fail-closed 5）")
        for name, sid in ghost[:20]:
            print(f"   ・{name} → {sid}")
        rc = 1

    missing = sorted(all_ids - used, key=lambda s: (s[0], int(s.split("-")[1])))
    if missing:
        print(f"❌ 出どころに在るのに、どの項目にも入っていないもの＝{len(missing)}件")
        for sid in missing:
            src_name, txt = body[sid]
            print(f"   ・{sid}｜{src_name}｜{str(txt)[:70]}")
        rc = 1
    else:
        print(f"✅ 出どころ {len(all_ids)}件 は、全部どれかの項目に入っています"
              f"（項目 {len(items)}件）")
    return rc


# ══ 出力 ═══════════════════════════════════════════════════════

def build() -> str:
    d = _load(SRC, "出どころの正本")
    a, b, c = collect_a(), collect_b(d), collect_c()

    L: list[str] = []
    add = L.append
    add("# 設計書の §4（設計の中身）に何を書くべきか — 3つの出どころの生の一覧")
    add("")
    add("**★この一覧はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`gen_design_sections.py --write`。")
    add("")
    add("**なぜ在るか**＝まこさん指摘 2026-09-10（逐語）"
        "「物事を組み立てる順番や複合要因の組み合わせ方など、思考が支離滅裂でその場しのぎすぎるんだよ」。"
        "私が思いつきで項目を足し、**4回とも まこさんの問いで「出どころに在るのに項目に入っていないもの」"
        "が出た**ため、**出どころから全部 抜いて番号を振る形にしました**（恒久の決まり39番）。")
    add("")
    add(f"**件数**＝A（うちの正本）**{len(a)}件** ／ B（外の標準）**{len(b)}件** ／ "
        f"C（過去の指摘）**{len(c)}件** ／ 合計 **{len(a)+len(b)+len(c)}件**。")
    add("")
    add("**★番号は、項目への割り当て（`design_section_map.json`）で使います。**"
        "`--check` を打つと、**どの項目にも入っていない番号**を機械が出します"
        "＝私が「もう無い」と判断する場所がありません。")
    add("")

    add("## A うちの正本が求めていること")
    add("")
    add("| 番号 | 出どころ | 求めていること |")
    add("|---|---|---|")
    for sid, src_name, bd in a:
        add(f"| {sid} | {src_name} | {bd.replace('|', '／')} |")
    add("")

    add("## B 外の標準が挙げている設計の関心事")
    add("")
    add("| 番号 | 出どころ | 項目 | 本文の逐語 |")
    add("|---|---|---|---|")
    for sid, src_name, name, quote in b:
        add(f"| {sid} | {src_name} | {name.replace('|', '／')} | {quote.replace('|', '／')} |")
    add("")

    add("## C まこさんが過去に「設計書に入っていない」と指摘した逐語")
    add("")
    add("| 番号 | いつ | 逐語 |")
    add("|---|---|---|")
    for sid, day, q in c:
        add(f"| {sid} | {day} | 「{q.replace('|', '／')}」 |")
    add("")
    add("**★C の抜き方の限界**＝「設計」を含み、かつ入っていないことを指す語"
        f"（{'・'.join(MISS_WORDS)}）を含む行から、鉤括弧の中を抜いています。"
        "**別の言い方をした指摘は拾えません。**")
    add("")
    return "\n".join(L)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run", action="store_true", help="抜いて画面に出す")
    p.add_argument("--write", action="store_true", help="抜いて design_sections.md に書く")
    p.add_argument("--check", action="store_true",
                   help="割り当てを検算する（どの項目にも入っていない番号を出す）")
    a = p.parse_args()
    if a.check:
        return check()
    if not (a.run or a.write):
        p.print_help()
        return 0
    body = build()
    if a.write:
        DEST.write_text(body, encoding="utf-8")
        print(f"✅ --write 完了: {DEST}（{len(body.splitlines())}行）")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
