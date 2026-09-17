#!/usr/bin/env python3
"""tidy_next_step.py — next_step.md の §0（次にやること）を機械で整えて検査する（2026-08-28・まこさん承認）

なぜ在るか＝next_step.md は毎セッション汚れて、まこさんが指示しないと整理されなかった
（69回目の末に4節・45行の「次の書き替えで消す」印が残り、(0-b-2) の印の値は3日前のまま）。
「消す」を CC の判断に任せると消されない。だから機械が移し、機械が検査し、
検査 ❌ のままではセッションを閉じられない（Stop hook `enforce_next_step_tidy.sh` が呼ぶ）。

使い方:
  python3 .claude/tools/tidy_next_step.py --verify     # 形を検査（❌ が1つでも在れば exit 2）
  python3 .claude/tools/tidy_next_step.py --write      # 「消す」印の節を archive へ移し、(0-b-2) を json から書き、最後に --verify
  python3 .claude/tools/tidy_next_step.py --selftest   # わざと壊して止まるか試すテスト（実物は触らない）

検査する6つ（--verify）:
  (a)「次の書き替えで消す」を見出しに含む節が 0件
  (b) 0-1 の見出しの日付が、いちばん新しい session_worklog_YYYYMMDD.md の日付と同じ
  (c) (0-b-2) に書いてある H2・G2 の印の値（先頭16桁）が h2_pass.json / g2_pass.json の fingerprint と一致
  (d) `# §0` から `## §0-4` の前までの行数が上限（LIMIT・まこさんが決める）以下
  (e) 0-2 の節の「★いまここ」がちょうど1件
  (f) 0-2 の表に「✅済」か取り消し線の行が0件（★2026-08-28 追加・終わった行を残せなくする）

決まり:
  ・移すときは1文字も変えない。🔴／★消さない／毎回消さない の数を前後で照らし、合わなければ書かない（fail-closed）。
  ・(0-b-2) の中身は json から書く。CC の自由記述は入れない。
  ・0-1 の文章の中身は機械は書かない（見るのは日付だけ）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import tempfile
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[2]
STATE = ROOT / ".claude" / "state"
NEXT = STATE / "next_step.md"
ARCHIVE = STATE / "next_step_archive_202608.md"
H2 = STATE / "h2_pass.json"
G2 = STATE / "g2_pass.json"
HOOK = ROOT / ".claude" / "hooks" / "enforce_next_step_tidy.sh"

LIMIT = 100                                   # §0 の行数の上限（まこさん決定 2026-08-28・設計書 §5）
MARKS = ("🔴", "★消さない", "毎回消さない")   # 消してはいけない印（数を前後で照らす）
DISPOSE = "次の書き替えで消す"
HEAD_RE = re.compile(r"^(#{1,6})\s")
SEC0_START = "# §0 "
SEC0_END = "## §0-4"
H01 = "### 0-1 "
H02 = "### 0-2 "
HB2 = "### （0-b-2）"
HD = "### （0-d）"
HERE_MARK = "★いまここ"
# ★(f) 2026-08-28（まこさん指示「直して」）＝0-2 の表に「終わった行」を残せなくする。
#   なぜ要るか＝(a)〜(e) はどれも「終わった行が表に残っているか」を見ていない。
#   実測（同日）＝0-2 の表に ✅済 10行・取り消し線 4行・これからやる行 1行。
#   それでも §0 は 77行で上限 100 の中だったので、検査は ✅ を出していた。
#   ＝上限に当たるまで汚れ続ける作りだった（まこさんの指示による整理は これで5回目）。
#   ★別の言い方（「完了」「done」）は捕まえない＝恒久の決まり55番で「✅済 の4文字だけ」と決まっているため。
DONE_MARK = "✅済"
STRIKE_RE = re.compile(r"~~[^~]+~~")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
WORKLOG_RE = re.compile(r"session_worklog_(\d{4})(\d{2})(\d{2})\.md$")

# ★2026-09-17（設計書 docs-autogen-next-step-pdca-20260917・まこさん指示「手書きせざるをえないもの以外は自動生成にしてほしい」）
#   ＝next_step.md を元データ next_step_src.json から作る。元データは、いまの next_step.md を
#     1文字も変えずに読み込んで作る（--import・最初の1回）。以後は元データを直して --write。
SRC_NAME = "next_step_src.json"
GEN_HEAD = "<!-- NEXT_STEP_GENERATED hash="
GEN_RE = re.compile(r"^<!-- NEXT_STEP_GENERATED hash=([0-9a-f]{16}) [^\n]*-->\n")
SEP_RE = re.compile(r"^\|(\s*:?-{3,}:?\s*\|)+\s*$")
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
REF_RE = re.compile(r"(?:session_worklog_(\d{8})\.md`?|worklog\s*(\d{8}))")
REF_TAIL_RE = re.compile(r"^[\s`]*(?:の\s*)?(§\d+(?:\.\d+)?(?:\s*[〜～・、,]\s*§?\d+(?:\.\d+)?)*)")
SEC6_HEAD = "# §6 "
S6_FLAG = "§6の済の行を移す"
BASELINE_KEY = "読み込んだときに見つからなかった参照"


# ── 材料 ─────────────────────────────────────────────────────────────────────
def count_marks(text: str) -> tuple[int, ...]:
    return tuple(text.count(m) for m in MARKS)


def _level(line: str) -> int:
    m = HEAD_RE.match(line)
    return len(m.group(1)) if m else 0


def _section_end(lines: list[str], i: int) -> int:
    """i の見出しの節の終わり＝同じ深さか浅い次の見出し（無ければ末尾）。"""
    lv = _level(lines[i])
    j = i + 1
    while j < len(lines):
        lj = _level(lines[j])
        if lj and lj <= lv:
            break
        j += 1
    return j


def find_disposable_sections(lines: list[str]) -> list[tuple[int, int]]:
    """見出しに DISPOSE を含む節の (始まり, 終わり) を返す。"""
    out = []
    i = 0
    while i < len(lines):
        if _level(lines[i]) and DISPOSE in lines[i]:
            j = _section_end(lines, i)
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def move_to_archive(next_text: str, arc_text: str, today: str) -> tuple[str, str, dict]:
    """DISPOSE の節を archive の末尾へ1文字も変えずに移す。印の数が合わなければ SystemExit（書かない）。"""
    lines = next_text.splitlines(keepends=True)
    secs = find_disposable_sections(lines)
    rep = {"moved_sections": 0, "moved_lines": 0, "before": count_marks(next_text),
           "after": count_marks(next_text), "moved": (0, 0, 0)}
    if not secs:
        return next_text, arc_text, rep
    moved_lines: list[str] = []
    keep: list[str] = []
    pos = 0
    for a, b in secs:
        keep += lines[pos:a]
        moved_lines += lines[a:b]
        pos = b
    keep += lines[pos:]
    new_next = "".join(keep)
    moved = "".join(moved_lines)
    if not moved.endswith("\n"):
        moved += "\n"
    head = (f"\n\n# {today} に tidy_next_step.py が next_step.md から移した節"
            f"（「{DISPOSE}」の印つき {len(secs)} 節・1文字も変えていない）\n\n")
    new_arc = arc_text + head + moved
    before, after, mv = count_marks(next_text), count_marks(new_next), count_marks(moved)
    check_marks(before, after, mv)
    if moved not in new_arc:
        raise SystemExit("[tidy] 移した本文が archive に1文字も変わらずに入っていない＝書かずに止まる")
    rep.update(moved_sections=len(secs), moved_lines=len(moved_lines), before=before, after=after, moved=mv)
    return new_next, new_arc, rep


def move_done_rows(next_text: str, arc_text: str, today: str) -> tuple[str, str, dict]:
    """0-2 の表から、終わった行（✅済・取り消し線）を archive の末尾へ1文字も変えずに移す。

    ★2026-09-08（設計書 insp5-frame-and-table-tidy-20260908 の C・監査 cp26 の §6-7）
      直す前＝検査 (f) は「終わった行が表に残っていると止める」と求めるのに、移す手段が
      節（DISPOSE の印つき）にしか無く、表の行は人が手で消すしかなかった。
      そのせいで、並走した2つのセッションが同じ Stop hook で同時に止まり、どちらも
      ターンを終えられなくなった（監査 cp26 の逐語）。さらに、人が手で消すと行を間違える
      （2026-09-08 に、行の位置を確かめずに消して §6 の別の行を消した）。
    ★見るのは 0-2 の節の「表の行」だけ＝説明の文に ✅済 と書いても移さない（検査 (f) と同じ見方）。
    ★印の数の照合は check_marks を呼ぶ＝合わなければ1文字も書かずに止まる（move_to_archive と同じ）。
    """
    lines = next_text.splitlines(keepends=True)
    s2 = next((i for i, l in enumerate(lines) if l.startswith(H02)), None)
    zero = tuple(0 for _ in MARKS)
    rep = {"moved_rows": 0, "before": count_marks(next_text),
           "after": count_marks(next_text), "moved": zero}
    if s2 is None:
        return next_text, arc_text, rep
    end = _section_end(lines, s2)
    keep: list[str] = []
    moved_rows: list[str] = []
    for k, ln in enumerate(lines):
        if s2 <= k < end and ln.lstrip().startswith("|") and (DONE_MARK in ln or STRIKE_RE.search(ln)):
            moved_rows.append(ln)
        else:
            keep.append(ln)
    if not moved_rows:
        return next_text, arc_text, rep
    new_next = "".join(keep)
    moved = "".join(moved_rows)
    if not moved.endswith("\n"):
        moved += "\n"
    # ★2026-09-08（監査 cp31 の Major 1・設計書 insp5-path-and-tidy-head-20260908 の H）
    #   ＝見出しを「表の1行目（見出し）＋2行目（区切り）」から、並びのまま取る。
    #   直す前（cp30 の別枠7 の直し）＝区切りの行を外してから先頭2本を取っていた。
    #     ＝表に生きている行が1本でも在ると、2本目がその行になり、**控えに複製された**。
    #       しかも区切りが入らないので、控えの表が表として描画されなかった。
    #       複製された行が消してはいけない印を持つと、印が1個 増えるが、
    #       印の数の照合（check_marks）は移した行の分しか数えないので、それを数えない
    #       （監査 cp31 が実測＝控えに 🔴 が1個 複製された）。
    #   直した後＝1行目が区切りか、終わった行のときは、いままでどおり既定の3列の見出しを使う。
    _rows = [ln for ln in lines[s2:end] if ln.lstrip().startswith("|")]
    _head_ln = None
    if (_rows and "---" not in _rows[0] and DONE_MARK not in _rows[0]
            and not STRIKE_RE.search(_rows[0])):
        _head_ln = _rows[0]
    if _head_ln is None:
        head_rows = "| 番号 | やること | 状態 |\n|---|---|---|\n"
    else:
        _sep_ln = (_rows[1] if len(_rows) >= 2 and "---" in _rows[1]
                   else "|" + "---|" * max(1, _head_ln.count("|") - 1) + "\n")
        head_rows = _head_ln + _sep_ln
    head = (f"\n\n# {today} に tidy_next_step.py が next_step.md の 0-2 の表から移した行"
            f"（終わった行 {len(moved_rows)} 行・1文字も変えていない）\n\n" + head_rows)
    new_arc = arc_text + head + moved
    before, after, mv = count_marks(next_text), count_marks(new_next), count_marks(moved)
    check_marks(before, after, mv)
    if moved not in new_arc:
        raise SystemExit("[tidy] 移した行が archive に1文字も変わらずに入っていない＝書かずに止まる")
    rep.update(moved_rows=len(moved_rows), before=before, after=after, moved=mv)
    return new_next, new_arc, rep


def check_marks(before: tuple, after: tuple, moved: tuple) -> None:
    """印の数＝前 − 移した分 ＝ 後、でなければ止まる。"""
    for k, m in enumerate(MARKS):
        if before[k] != after[k] + moved[k]:
            raise SystemExit(f"[tidy] 印『{m}』の数が合わない（前 {before[k]} ≠ 後 {after[k]} ＋ 移した分 {moved[k]}）＝書かずに止まる")


def _pass(path: pathlib.Path) -> dict:
    if not path.exists():
        raise SystemExit(f"[tidy] 印の json が無い: {path}")
    d = json.loads(path.read_text(encoding="utf-8"))
    for k in ("fingerprint", "when", "files"):
        if k not in d:
            raise SystemExit(f"[tidy] 印の json に {k} が無い: {path}")
    return {"fp": str(d["fingerprint"])[:16], "when": str(d["when"]), "n": len(d["files"])}


def marks_block(h2: dict, g2: dict, today: str) -> str:
    """(0-b-2) の節の本文（型は固定・自由記述なし）。"""
    return (f"{HB2}🔴 印の状態（{today}・★この節は tidy_next_step.py が json から書く＝手で書かない）\n"
            "\n"
            f"- **H2 の印＝`{h2['fp']}…`**（`.claude/state/h2_pass.json`・{h2['when']}・対象{h2['n']}ファイル）"
            f"／**G2 の印＝`{g2['fp']}…`**（`g2_pass.json`・{g2['when']}・対象{g2['n']}ファイル）。\n"
            "- **コードを触ったら取り直す**＝G2 → H2 の順（`gen_signal_families.py --verify` 約30秒 → `leak_causality_diag.py` 約5分・L-565）。\n"
            "\n")


def refresh_marks(next_text: str, h2: dict, g2: dict, today: str) -> str:
    """(0-b-2) の節を json の値で書き直す。節が無ければ (0-d) の直前に足す。印の数は変えない。"""
    lines = next_text.splitlines(keepends=True)
    idx = next((i for i, l in enumerate(lines) if l.startswith(HB2)), None)
    block = marks_block(h2, g2, today)
    if idx is None:
        ins = next((i for i, l in enumerate(lines) if l.startswith(HD)), None)
        if ins is None:
            raise SystemExit("[tidy] (0-b-2) も (0-d) も無い＝どこに書くか決められない")
        return "".join(lines[:ins]) + block + "".join(lines[ins:])
    j = _section_end(lines, idx)
    new = "".join(lines[:idx]) + block + "".join(lines[j:])
    b, a = count_marks(next_text), count_marks(new)
    if b != a:
        raise SystemExit(f"[tidy] (0-b-2) を書き直すと印の数が変わる（前 {b} → 後 {a}）＝書かずに止まる")
    return new


def latest_worklog_date(state_dir: pathlib.Path) -> str | None:
    ds = []
    for p in state_dir.glob("session_worklog_*.md"):
        m = WORKLOG_RE.search(p.name)
        if m:
            ds.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
    return max(ds) if ds else None


def sec0_lines(lines: list[str]) -> int | None:
    s = next((i for i, l in enumerate(lines) if l.startswith(SEC0_START)), None)
    e = next((i for i, l in enumerate(lines) if l.startswith(SEC0_END)), None)
    if s is None or e is None or e < s:
        return None
    return e - s


def verify(next_text: str, h2: dict, g2: dict, worklog_date: str | None, limit: int = LIMIT) -> list[str]:
    """6つの検査。戻り＝❌ の一覧（空なら ✅）。"""
    ng: list[str] = []
    lines = next_text.splitlines()
    n_disp = len(find_disposable_sections(lines))
    if n_disp:
        ng.append(f"(a)「{DISPOSE}」の節が {n_disp} 件 残っている → `--write` で archive へ移す")
    h01 = next((l for l in lines if l.startswith(H01)), None)
    if h01 is None:
        ng.append(f"(b) 見出し『{H01.strip()}』が無い")
    else:
        m = DATE_RE.search(h01)
        if not m:
            ng.append("(b) 0-1 の見出しに日付（YYYY-MM-DD）が無い")
        elif worklog_date and m.group(1) != worklog_date:
            ng.append(f"(b) 0-1 の日付 {m.group(1)} が、いちばん新しい worklog の日付 {worklog_date} と違う → 0-1 を今日の状態に書き直す")
    hb = next((i for i, l in enumerate(lines) if l.startswith(HB2)), None)
    if hb is None:
        ng.append(f"(c) 節『{HB2}』が無い → `--write` で作る")
    else:
        body = "\n".join(lines[hb:_section_end(lines, hb)])
        if h2["fp"] not in body:
            ng.append(f"(c) (0-b-2) の H2 の印が json（{h2['fp']}…）と違う → `--write`")
        if g2["fp"] not in body:
            ng.append(f"(c) (0-b-2) の G2 の印が json（{g2['fp']}…）と違う → `--write`")
        # ★2026-09-08（監査 cp32 の別枠 E・設計書 tm-scope-and-g2-fingerprint-20260908 の F）
        #   ＝時刻も照らす。直す前は指紋の値だけを見ていたので、印を取り直した後に
        #     `--write` を走らせ忘れると、時刻だけが古いまま残った（監査が実測した）。
        if h2["when"] not in body:
            ng.append(f"(c) (0-b-2) の H2 の時刻が json（{h2['when']}）と違う → `--write`")
        if g2["when"] not in body:
            ng.append(f"(c) (0-b-2) の G2 の時刻が json（{g2['when']}）と違う → `--write`")
    n0 = sec0_lines(lines)
    if n0 is None:
        ng.append(f"(d) 『{SEC0_START.strip()}』〜『{SEC0_END}』が見つからない")
    elif n0 > limit:
        ng.append(f"(d) §0 が {n0} 行（上限 {limit}）→ 古い節に「{DISPOSE}」の印を付けて `--write` で移す")
    s2 = next((i for i, l in enumerate(lines) if l.startswith(H02)), None)
    if s2 is None:
        ng.append(f"(e) 見出し『{H02.strip()}』が無い")
    else:
        sec2 = lines[s2:_section_end(lines, s2)]
        n_here = "\n".join(sec2).count(HERE_MARK)
        if n_here != 1:
            ng.append(f"(e) 0-2 の『{HERE_MARK}』が {n_here} 件（ちょうど1件のはず）")
        # (f) 終わった行を表に残せない（表の行だけを見る＝説明の文に書いても止めない）
        done = [l for l in sec2
                if l.lstrip().startswith("|") and (DONE_MARK in l or STRIKE_RE.search(l))]
        if done:
            ng.append(f"(f) 0-2 の表に、終わった行が {len(done)} 行 残っている"
                      f"（『{DONE_MARK}』か 取り消し線）→ archive へ移して表から消す"
                      f"／1行目＝{done[0].strip()[:50]}")
    return ng


# ── 元データ（next_step_src.json）から作る（2026-09-17・設計書 docs-autogen-next-step-pdca-20260917）──
def _split_cells(line: str) -> list[str] | None:
    """表の1行を欄に分ける（\\| は欄の区切りにしない）。形が崩れていれば None＝その行は生のまま持つ。"""
    if not (line.startswith("|") and line.endswith("|")) or len(line) < 2:
        return None
    parts = CELL_SPLIT_RE.split(line)
    return parts[1:-1]


def _state_col(header: str) -> int | None:
    cells = _split_cells(header) or []
    for k, c in enumerate(cells):
        if "状態" in c or "いつ直すか" in c:
            return k
    return None


def parse_doc(text: str) -> dict:
    """next_step.md の本文（目印の行を除く）を、節 → 塊（文／表）の元データにする。1文字も落とさない形。"""
    trailing = text.endswith("\n")
    lines = text.split("\n")
    if trailing:
        lines = lines[:-1]
    secs: list[dict] = []
    cur = {"見出し": "", "塊": []}
    fence = False
    i = 0

    def add_text(ln: str) -> None:
        if cur["塊"] and "文" in cur["塊"][-1]:
            cur["塊"][-1]["文"].append(ln)
        else:
            cur["塊"].append({"文": [ln]})

    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            fence = not fence
        if not fence and not ln.startswith("```") and HEAD_RE.match(ln):
            if cur["見出し"] or cur["塊"]:
                secs.append(cur)
            cur = {"見出し": ln, "塊": []}
            if ln.startswith(H01):
                m = DATE_RE.search(ln)
                if m:
                    cur["書いた日"] = m.group(1)
            i += 1
            continue
        if (not fence and ln.startswith("|") and i + 1 < len(lines)
                and SEP_RE.match(lines[i + 1]) and _split_cells(ln) is not None):
            j = i + 2
            rows = []
            while j < len(lines) and lines[j].startswith("|"):
                cells = _split_cells(lines[j])
                rows.append({"欄": cells} if cells is not None else {"生": lines[j]})
                j += 1
            cur["塊"].append({"表": {"見出しの行": ln, "区切り": lines[i + 1],
                                   "状態の欄": _state_col(ln), "行": rows}})
            i = j
            continue
        add_text(ln)
        i += 1
    if cur["見出し"] or cur["塊"]:
        secs.append(cur)
    return {"節": secs, "末尾の改行": trailing}


def render(src: dict) -> str:
    """元データから next_step.md の本文を作る（目印の行は付けない）。"""
    out: list[str] = []
    for sec in src["節"]:
        h = sec.get("見出し", "")
        if h:
            if sec.get("書いた日"):
                h = DATE_RE.sub(sec["書いた日"], h, count=1)
            out.append(h)
        for blk in sec.get("塊", []):
            if "文" in blk:
                out.extend(blk["文"])
            else:
                t = blk["表"]
                out.append(t["見出しの行"])
                out.append(t["区切り"])
                for r in t["行"]:
                    out.append("|" + "|".join(r["欄"]) + "|" if "欄" in r else r["生"])
    return "\n".join(out) + ("\n" if src.get("末尾の改行", True) else "")


def strip_gen_head(text: str) -> tuple[str, str | None]:
    """1行目の生成の目印を外す。戻り＝(本文, 目印に書かれたハッシュ値 or None)。"""
    m = GEN_RE.match(text)
    if not m:
        return text, None
    return text[m.end():], m.group(1)


def _hash16(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def gen_head(body: str) -> str:
    return f"{GEN_HEAD}{_hash16(body)} tidy_next_step.py が {SRC_NAME} から作った＝手で書き換えない -->\n"


def _worklog_secs(state_dir: pathlib.Path, ymd: str, cache: dict) -> set[str] | None:
    if ymd in cache:
        return cache[ymd]
    p = state_dir / f"session_worklog_{ymd}.md"
    if not p.exists():
        cache[ymd] = None
        return None
    got: set[str] = set()
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.startswith("#"):
            got.update(re.findall(r"§(\d+)", ln))
    cache[ymd] = got
    return got


def check_refs(text: str, state_dir: pathlib.Path) -> list[str]:
    """文の中の worklog の節の参照（`session_worklog_YYYYMMDD.md` §N ／ worklog YYYYMMDD §N）が、
    そのファイルに見出しとして在るか。戻り＝見つからない参照（「ファイル §N」の形）の一覧。"""
    cache: dict = {}
    miss: list[str] = []
    for ln in text.splitlines():
        for m in REF_RE.finditer(ln):
            ymd = m.group(1) or m.group(2)
            t = REF_TAIL_RE.match(ln[m.end():])
            if not t:
                continue
            nums = [n.split(".")[0] for n in re.findall(r"\d+(?:\.\d+)?", t.group(1))]
            secs = _worklog_secs(state_dir, ymd, cache)
            for n in nums:
                if secs is None or n not in secs:
                    key = f"session_worklog_{ymd}.md §{n}"
                    if key not in miss:
                        miss.append(key)
    return miss


def move_done_rows_s6(next_text: str, arc_text: str, today: str) -> tuple[str, str, dict]:
    """§6 の表から、「★いつ直すか」の欄が ✅済 の行を archive へ1文字も変えずに移す。
    ★元データの「§6の済の行を移す」が true のときだけ呼ぶ（§6 の決まり5つ目「消すかは まこさんが決める」のため）。"""
    lines = next_text.splitlines(keepends=True)
    s6 = next((i for i, l in enumerate(lines) if l.startswith(SEC6_HEAD)), None)
    zero = tuple(0 for _ in MARKS)
    rep = {"moved_rows": 0, "moved": zero}
    if s6 is None:
        return next_text, arc_text, rep
    end = _section_end(lines, s6)
    keep, moved_rows, head_rows, col = [], [], "", None
    for k, ln in enumerate(lines):
        body = ln.rstrip("\n")
        if s6 <= k < end and body.startswith("|") and k + 1 < len(lines) and SEP_RE.match(lines[k + 1].rstrip("\n")):
            col = _state_col(body)
            head_rows = ln + lines[k + 1]
        cells = _split_cells(body) if s6 <= k < end else None
        if (cells is not None and col is not None and col < len(cells)
                and DONE_MARK in cells[col] and not SEP_RE.match(body)):
            moved_rows.append(ln)
        else:
            keep.append(ln)
    if not moved_rows:
        return next_text, arc_text, rep
    new_next, moved = "".join(keep), "".join(moved_rows)
    head = (f"\n\n# {today} に tidy_next_step.py が next_step.md の §6 の表から移した行"
            f"（✅済 の行 {len(moved_rows)} 行・1文字も変えていない）\n\n" + head_rows)
    new_arc = arc_text + head + moved
    before, after, mv = count_marks(next_text), count_marks(new_next), count_marks(moved)
    check_marks(before, after, mv)
    rep.update(moved_rows=len(moved_rows), moved=mv)
    return new_next, new_arc, rep


def _atomic_write(path: pathlib.Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def _first_diff(a: str, b: str) -> str:
    al, bl = a.splitlines(), b.splitlines()
    for k in range(max(len(al), len(bl))):
        x = al[k] if k < len(al) else "（無い）"
        y = bl[k] if k < len(bl) else "（無い）"
        if x != y:
            return f"{k + 1}行目\n     いま　　＝{x[:160]}\n     作り直し＝{y[:160]}"
    return "改行の有無だけが違う"


def import_src(next_path: pathlib.Path) -> int:
    """いまの next_step.md から元データを作る（最初の1回）。作り直した文書が1文字でも違えば書かない。"""
    src_path = next_path.parent / SRC_NAME
    if src_path.exists():
        print(f"❌ [tidy --import] {src_path} が既に在る＝上書きしない（元データを直して --write を使う）")
        return 1
    body, _h = strip_gen_head(next_path.read_text(encoding="utf-8"))
    src = parse_doc(body)
    again = render(src)
    if again != body:
        print(f"❌ [tidy --import] 作り直した文書が いまの {next_path.name} と違う＝元データを書かない\n   最初に違う所＝{_first_diff(body, again)}")
        return 1
    miss = check_refs(body, next_path.parent)
    src[BASELINE_KEY] = miss
    src[S6_FLAG] = False
    _atomic_write(src_path, json.dumps(src, ensure_ascii=False, indent=1) + "\n")
    n_tab = sum(1 for s in src["節"] for b in s["塊"] if "表" in b)
    n_row = sum(len(b["表"]["行"]) for s in src["節"] for b in s["塊"] if "表" in b)
    print(f"✅ [tidy --import] {src_path.name} を書いた＝節 {len(src['節'])}／表 {n_tab}／表の行 {n_row}"
          f"／作り直した文書は いまのファイルと1文字も違わない")
    print(f"   worklog の節の参照で見つからなかったもの＝{len(miss)} 件（元データに控えた＝以後に足した参照だけを止める）")
    for x in miss:
        print(f"     ・{x}")
    return 0


def check_generated(next_path: pathlib.Path) -> list[str]:
    """(g) 元データが在るとき＝1行目の目印・全文のハッシュ値・元データから作ったままか。"""
    src_path = next_path.parent / SRC_NAME
    if not src_path.exists():
        return []
    text = next_path.read_text(encoding="utf-8")
    body, h = strip_gen_head(text)
    ng = []
    if h is None:
        ng.append(f"(g) 1行目に生成の目印が無い → `tidy_next_step.py --write`（元データ {SRC_NAME} から作る）")
        return ng
    if h != _hash16(body):
        ng.append(f"(g) 目印のハッシュ値 {h} と本文 {_hash16(body)} が違う＝手で書き換えた → 元データ {SRC_NAME} を直して `--write`")
    src = json.loads(src_path.read_text(encoding="utf-8"))
    if render(src) != body:
        ng.append(f"(g) 本文が元データ {SRC_NAME} から作ったものと違う → 元データを直して `--write`／最初に違う所＝{_first_diff(body, render(src))}")
    return ng


def do_write_src(next_path: pathlib.Path, arc_path: pathlib.Path, limit: int) -> int:
    """元データから作って書く。照らす5つのどれかが通らなければ、1文字も書かない。"""
    today = date.today().isoformat()
    src_path = next_path.parent / SRC_NAME
    src = json.loads(src_path.read_text(encoding="utf-8"))
    text = render(src)
    arc = arc_path.read_text(encoding="utf-8") if arc_path.exists() else ""
    new_next, new_arc, rep = move_to_archive(text, arc, today)
    new_next, new_arc, rep2 = move_done_rows(new_next, new_arc, today)
    rep3 = {"moved_rows": 0}
    if src.get(S6_FLAG):
        new_next, new_arc, rep3 = move_done_rows_s6(new_next, new_arc, today)
    h2, g2 = _pass(H2), _pass(G2)
    new_next = refresh_marks(new_next, h2, g2, today)
    base = set(src.get(BASELINE_KEY, []))
    miss = [x for x in check_refs(new_next, next_path.parent) if x not in base]
    ng = verify(new_next, h2, g2, latest_worklog_date(next_path.parent), limit)
    if miss:
        ng += [f"(参照) {x} が見出しに無い（元データの文を直す）" for x in miss]
    if ng:
        print(f"❌ [tidy --write] 元データから作った文書に {len(ng)} 件＝1文字も書かない:")
        for x in ng:
            print(f"   ・{x}")
        return 2
    new_src = parse_doc(new_next)
    if render(new_src) != new_next:
        print(f"❌ [tidy --write] 作った文書を元データに戻すと形が変わる＝書かない／{_first_diff(new_next, render(new_src))}")
        return 2
    new_src[BASELINE_KEY] = src.get(BASELINE_KEY, [])
    new_src[S6_FLAG] = bool(src.get(S6_FLAG))
    if new_arc != arc:
        _atomic_write(arc_path, new_arc)
    _atomic_write(src_path, json.dumps(new_src, ensure_ascii=False, indent=1) + "\n")
    _atomic_write(next_path, gen_head(new_next) + new_next)
    print(f"[tidy --write] 元データ {SRC_NAME} から作った／移した節 {rep['moved_sections']}"
          f"／0-2 の表から移した行 {rep2['moved_rows']}／§6 の表から移した行 {rep3['moved_rows']}"
          f"（§6 を移す設定＝{bool(src.get(S6_FLAG))}）／worklog の参照を照らした（控えの外で見つからない参照 0 件）"
          f"／(0-b-2) を json から書いた")
    return do_verify(next_path, limit)


# ── 口 ───────────────────────────────────────────────────────────────────────
def do_verify(next_path: pathlib.Path, limit: int) -> int:
    text = next_path.read_text(encoding="utf-8")
    ng = verify(text, _pass(H2), _pass(G2), latest_worklog_date(next_path.parent), limit)
    # ★2026-09-17＝元データ next_step_src.json が在れば (g) も見る（目印・全文のハッシュ値・元データから作ったままか）
    ng += check_generated(next_path)
    if ng:
        print(f"❌ [tidy --verify] {next_path.name} の形に {len(ng)} 件:")
        for x in ng:
            print(f"   ・{x}")
        return 2
    n0 = sec0_lines(text.splitlines())
    _n_chk = "7つ（6つ＋(g) 元データと全文のハッシュ値）" if (next_path.parent / SRC_NAME).exists() else "6つ"
    print(f"✅ [tidy --verify] {_n_chk}とも通った（§0 {n0} 行／上限 {limit}）")
    return 0


def do_write(next_path: pathlib.Path, arc_path: pathlib.Path, limit: int) -> int:
    if (next_path.parent / SRC_NAME).exists():
        # ★2026-09-17＝元データが在れば、文書ではなく元データから作る（設計書 docs-autogen-next-step-pdca-20260917）
        return do_write_src(next_path, arc_path, limit)
    today = date.today().isoformat()
    text = next_path.read_text(encoding="utf-8")
    arc = arc_path.read_text(encoding="utf-8") if arc_path.exists() else ""
    new_next, new_arc, rep = move_to_archive(text, arc, today)
    # ★2026-09-08＝節を移したあと、0-2 の表の「終わった行」も移す（設計書 の C・監査 cp26 の §6-7）
    new_next, new_arc, rep2 = move_done_rows(new_next, new_arc, today)
    new_next = refresh_marks(new_next, _pass(H2), _pass(G2), today)
    if new_arc != arc:
        arc_path.write_text(new_arc, encoding="utf-8")
    next_path.write_text(new_next, encoding="utf-8")
    print(f"[tidy --write] 移した節 {rep['moved_sections']}／行 {rep['moved_lines']}"
          f"／0-2 の表から移した行 {rep2['moved_rows']}"
          f"／印の数 前 {rep['before']} → 後 {count_marks(new_next)}（移した分 {rep['moved']}＋{rep2['moved']}）"
          f"／(0-b-2) を json から書いた")
    return do_verify(next_path, limit)


# ── わざと壊して止まるか試すテスト ────────────────────────────────────────────
SAMPLE = """# 次のセッションの起点

# §0 次にやること

### 0-1 いまの状態（{d}・◯回目の末）

> 🔴 次のセッションはここから。

#### （0-1' 前回の記録・次の書き替えで消す）

- 🔴 古い記録1

#### （0-1'' 前々回の記録・次の書き替えで消す）

- ★消さない 古い記録2
- 毎回消さない 古い記録3

### 0-2 🔴 次にやること

| 番号 | やること | 状態 |
|---|---|---|
| 1 | あれ | まだ |
| 2 | これ | ★いまここ |

### （0-b-2）🔴 印の状態（2026-01-01 時点）

- H2 の印＝`0000000000000000…`／G2 の印＝`1111111111111111…`

### （0-d）まだ埋まっていないこと

| # | 何 |
|---|---|

## §0-4 🔴 まこさんの判断待ち

- 何か
"""


def selftest() -> int:
    ng: list[str] = []
    h2 = {"fp": "567c333a9675cde4", "when": "2026-08-27 22:00:12", "n": 21}
    g2 = {"fp": "a500061c85168f04", "when": "2026-08-27 23:56:49", "n": 37}
    today = "2026-08-28"
    src = SAMPLE.format(d=today)

    # T1 「消す」印の2節を移せる（印の数＝前 − 移した分 ＝ 後）
    new_next, new_arc, rep = move_to_archive(src, "# archive\n", today)
    ok1 = (rep["moved_sections"] == 2 and DISPOSE not in new_next
           and all(rep["before"][k] == count_marks(new_next)[k] + rep["moved"][k] for k in range(3))
           and "古い記録1" in new_arc and "古い記録3" in new_arc)
    if not ok1:
        ng.append(f"T1: 移せない／数が合わない {rep}")

    # T2 数が合わなくなるよう わざと壊す（🔴 の行を1行 落として渡す）→ 止まる
    try:
        check_marks(before=(3, 1, 1), after=(1, 0, 0), moved=(1, 1, 1))
        ng.append("T2: 数が合わないのに止まらなかった")
    except SystemExit:
        pass

    clean = refresh_marks(new_next, h2, g2, today)
    r7 = verify(clean, h2, g2, today, LIMIT)
    if r7:
        ng.append(f"T7: きれいな見本で ❌ {r7}")
    r3 = verify(clean.replace(f"### 0-1 いまの状態（{today}", "### 0-1 いまの状態（2026-08-20"), h2, g2, today, LIMIT)
    if not any(x.startswith("(b)") for x in r3):
        ng.append(f"T3: 古い日付で (b) が出ない {r3}")
    r4 = verify(clean.replace(h2["fp"], "deadbeefdeadbeef"), h2, g2, today, LIMIT)
    if not any(x.startswith("(c)") for x in r4):
        ng.append(f"T4: 印が違うのに (c) が出ない {r4}")
    # ★T4b（2026-09-08・監査 cp32 の別枠 E）＝時刻だけを書き替えても (c) が出る。
    #   直す前は指紋の値だけを見ていたので、時刻が古いまま残っても何も言わなかった。
    r4b = verify(clean.replace(h2["when"], "2020-01-01 00:00:00"), h2, g2, today, LIMIT)
    if not any(x.startswith("(c)") for x in r4b):
        ng.append(f"T4b: 印の時刻が違うのに (c) が出ない {r4b}")
    n0 = sec0_lines(clean.splitlines())
    r5 = verify(clean, h2, g2, today, limit=n0 - 1)
    if not any(x.startswith("(d)") for x in r5):
        ng.append(f"T5: 上限超えで (d) が出ない {r5}")
    r6a = verify(clean.replace(HERE_MARK, "まだ"), h2, g2, today, LIMIT)
    r6b = verify(clean.replace("| まだ |", f"| {HERE_MARK} |"), h2, g2, today, LIMIT)
    if not (any(x.startswith("(e)") for x in r6a) and any(x.startswith("(e)") for x in r6b)):
        ng.append(f"T6: ★いまここ 0件/2件で (e) が出ない {r6a} {r6b}")
    ra = verify(refresh_marks(src, h2, g2, today), h2, g2, today, LIMIT)
    if not any(x.startswith("(a)") for x in ra):
        ng.append(f"T1': 消す印が残るのに (a) が出ない {ra}")

    # T9 (f) 0-2 の表に「終わった行」が残ると止まる（✅済／取り消し線）。説明の文なら止まらない
    r9a = verify(clean.replace("| 1 | あれ | まだ |", f"| 1 | あれ | {DONE_MARK} |"), h2, g2, today, LIMIT)
    if not any(x.startswith("(f)") for x in r9a):
        ng.append(f"T9a: 0-2 の表に『{DONE_MARK}』の行が在るのに (f) が出ない {r9a}")
    r9b = verify(clean.replace("| 1 | あれ | まだ |", "| 1 | ~~あれ~~ | まだ |"), h2, g2, today, LIMIT)
    if not any(x.startswith("(f)") for x in r9b):
        ng.append(f"T9b: 0-2 の表に取り消し線の行が在るのに (f) が出ない {r9b}")
    r9c = verify(clean.replace("### 0-2 🔴 次にやること",
                               f"### 0-2 🔴 次にやること\n\n終わった行（{DONE_MARK}）は archive へ移します。"),
                 h2, g2, today, LIMIT)
    if any(x.startswith("(f)") for x in r9c):
        ng.append(f"T9c: 説明の文に『{DONE_MARK}』が在るだけで (f) が出た（誤報）{r9c}")

    # T10 (C) 0-2 の表の「終わった行」を、機械が archive へ移す（2026-09-08・設計書 の D）
    #   ①✅済 の行が移る ②取り消し線の行も移る ③説明の文（表でない行）は移さない
    d10 = clean.replace("| 1 | あれ | まだ |", f"| 1 | あれ | {DONE_MARK} |")
    n10, a10, r10 = move_done_rows(d10, "# archive\n", today)
    if r10["moved_rows"] != 1 or DONE_MARK in n10.split(H02)[1].split("###")[0]:
        ng.append(f"T10a: 0-2 の表の『{DONE_MARK}』の行が移らない（移した行 {r10['moved_rows']}）")
    if f"| 1 | あれ | {DONE_MARK} |" not in a10:
        ng.append("T10a': 移した行が archive に1文字も変わらずに入っていない")
    d11 = clean.replace("| 1 | あれ | まだ |", "| 1 | ~~あれ~~ | まだ |")
    _n11, _a11, r11 = move_done_rows(d11, "# archive\n", today)
    if r11["moved_rows"] != 1:
        ng.append(f"T10b: 0-2 の表の取り消し線の行が移らない（移した行 {r11['moved_rows']}）")
    d12 = clean.replace("### 0-2 🔴 次にやること",
                        f"### 0-2 🔴 次にやること\n\n終わった行（{DONE_MARK}）は archive へ移します。")
    n12, _a12, r12 = move_done_rows(d12, "# archive\n", today)
    if r12["moved_rows"] != 0 or f"終わった行（{DONE_MARK}）は archive へ移します。" not in n12:
        ng.append(f"T10c: 説明の文（表でない行）を移してしまった（移した行 {r12['moved_rows']}）")

    # ★2026-09-08（監査 cp31 の Major 1・設計書 insp5-path-and-tidy-head-20260908 の I）
    #   ＝控えに入る見出しの取り方を見る番人3件。
    #   ①「見出しの行＋区切りの行」の2行になる（区切りが無いと、控えの表が表として描画されない）
    #   ②いま生きている行が控えに複製されない（直す前は `_hdr[:2]` が生きている行を拾っていた）
    #   ③見出しが無い表（1行目が区切り）でも落ちず、既定の3列の見出しを使う
    #   ★見本の 0-2 の表には、生きている行が2本 在る（| 1 | あれ | まだ |／| 2 | これ | ★いまここ |）。
    #     d10 は1本目を ✅済 にしたものなので、2本目は生きたまま残る＝複製の有無を測れる。
    if "|---|---|---|" not in a10:
        ng.append("T10d: 控えに区切りの行が入っていない（表として描画されない・監査 cp31 の Major 1）")
    if "| 2 | これ | ★いまここ |" in a10:
        ng.append("T10e: いま生きている行が控えに複製された（監査 cp31 の Major 1）")
    d15 = d10.replace("| 番号 | やること | 状態 |\n", "", 1)
    _n15, a15, r15 = move_done_rows(d15, "# archive\n", today)
    if r15["moved_rows"] != 1 or "| 番号 | やること | 状態 |" not in a15:
        ng.append(f"T10f: 見出しが無い表で、既定の見出しが入らない（移した行 {r15['moved_rows']}）")

    # T8 hook を見本で直に呼ぶ（❌ の見本＝exit 2／✅ の見本＝exit 0）★実物の json と worklog の日付で
    if HOOK.exists():
        real_h2, real_g2 = _pass(H2), _pass(G2)
        wd = latest_worklog_date(STATE) or today
        with tempfile.TemporaryDirectory() as td:
            bad = pathlib.Path(td) / "next_step.md"
            good = pathlib.Path(td) / "next_step_good.md"
            bad.write_text(src, encoding="utf-8")
            good_text = refresh_marks(new_next, real_h2, real_g2, today).replace(
                f"### 0-1 いまの状態（{today}", f"### 0-1 いまの状態（{wd}")
            good.write_text(good_text, encoding="utf-8")
            rb = subprocess.run(["bash", str(HOOK), str(bad)], capture_output=True, text=True)
            rg = subprocess.run(["bash", str(HOOK), str(good)], capture_output=True, text=True)
            # ★見本は一時の場所に在るので、(b) の worklog の日付は「無い」扱い＝日付の検査は通る。
            #   ❌ の見本は (a)(c)(e)… のどれかで止まり、✅ の見本は通るはず。
            if rb.returncode != 2:
                ng.append(f"T8: ❌ の見本で hook が exit {rb.returncode}（2 のはず）{rb.stderr[:120]}")
            if rg.returncode != 0:
                ng.append(f"T8: ✅ の見本で hook が exit {rg.returncode}（0 のはず）{rg.stderr[:160]}")
    else:
        ng.append("T8: hook が無い")

    print("[selftest] T1 移せる／T2 数が合わなければ止まる／T3 日付／T4 印／T5 行数／T6 ★いまここ／T7 きれい／T8 hook／T1' 消す印"
          "／T9a ✅済 の行／T9b 取り消し線／T9c 説明の文は止めない"
          "／T10a 表の ✅済 を移す／T10b 表の取り消し線を移す／T10c 説明の文は移さない"
          "／T10d 控えに区切りの行が入る／T10e 生きている行を複製しない／T10f 見出しが無い表でも落ちない"
          "／T4b 印の時刻も照らす")
    for x in ng:
        print(f"  ❌ {x}")
    total = 19
    print(f"  {'❌' if ng else '✅'} わざと壊して止まるか試すテスト {total - len(ng)}/{total} pass")
    return 1 if ng else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="next_step.md の §0 を機械で整えて検査する")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--import", dest="do_import", action="store_true",
                    help="いまの next_step.md から next_step_src.json を作る（最初の1回・作り直しが1文字も違わないときだけ書く）")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--file", type=pathlib.Path, default=NEXT, help="検査する next_step.md（テスト用）")
    ap.add_argument("--archive", type=pathlib.Path, default=ARCHIVE)
    ap.add_argument("--limit", type=int, default=LIMIT)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.do_import:
        return import_src(a.file)
    if a.write:
        return do_write(a.file, a.archive, a.limit)
    if a.verify:
        return do_verify(a.file, a.limit)
    ap.error("--verify / --write / --selftest のどれかを指定してください")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
