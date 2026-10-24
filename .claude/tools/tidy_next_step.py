#!/usr/bin/env python3
"""tidy_next_step.py — next_step.md を機械で整えて検査する（2026-08-28・まこさん承認）
★2026-10-18（190回目・まこさん「一旦上記で修正してよい」「よい」）＝next_step を目的ごとの8つの項目に組み替えた
  （1 毎回最初に読むこと／2 次のセッションでやること／3 いまの状態／4 まこさんに決めていただくこと／
   5 プロジェクトのやることの表／6 記録と置き場の案内／7 この文書の決まり／8 CC メモ）。§0 という区切りは無くなった。
  前は §0 の範囲に掛けていた (d)(i)(k) は、もとの §0 の中身が入った項目 3・5・6 に掛ける。
  (o) は、先頭から項目 2 の終わりまで（項目 1・2）に掛ける。上限の数は変えていない（worklog 20261018 §5）。

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
  (b) 3-1 いまの状態 の見出しの日付が、いちばん新しい session_worklog_YYYYMMDD.md の日付と同じ
  (c) 3-2 印の状態 に書いてある H2・G2 の印の値（先頭16桁）が h2_pass.json / g2_pass.json の fingerprint と一致
  (d) 項目 3・5・6（もとの §0 の中身）の行数の合計が上限（LIMIT・まこさんが決める）以下
  (e) 5 やることの表 の節の「★いまここ」がちょうど1件
  (f) 5 やることの表 に「✅済」か取り消し線の行が0件（★2026-08-28 追加・終わった行を残せなくする）
  ★2026-10-02 追加（まこさん「自発的にやれるようにできないの？」→「じゃあ、その修正しろ」・本物の next_step だけに掛ける）
  (h) 最初の「## 」の見出しが「## 1 毎回最初に読むこと」 (i) 項目 3・5・6 に「N回目にしたこと」（経緯）が無い
  (j) 5 やることの表 の欄が250字以内 (k) 項目 3・5・6 に同じ行が2回 無い
  (l) 教訓の現役が40件＋名指しされた物だけ（--write が古い物を lessons_archive.md へ移す）
  (m) 結果が出た監査の写し（cp<N>_work の中のフォルダ全部と *selftest*_work・git の外・作って1時間 過ぎ）が無い（--write が消す）
  ※ --write は、終わったセッションのフォルダ（sessions の下・最後に書いてから1日 過ぎ）と、
    tuner_cache の古い指紋の控え（戦略ごとに いちばん新しい指紋だけを残す）も消す（--verify では見ない）。

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

LIMIT = 100                                   # 項目 3・5・6 の行数の上限（まこさん決定 2026-08-28・設計書 §5。前は §0 の上限）
MARKS = ("🔴", "★消さない", "毎回消さない")   # 消してはいけない印（数を前後で照らす）
DISPOSE = "次の書き替えで消す"
HEAD_RE = re.compile(r"^(#{1,6})\s")
# ★2026-10-18（190回目）＝§0 の区切り（「# §0 」〜「## §0-4」）を、項目の見出しの一覧に替えた。
CHECK_ITEMS = ("## 3 ", "## 5 ", "## 6 ")     # (d)(i)(k) の相手＝もとの §0 の中身が入った項目
TOP_ITEMS = ("## 1 ", "## 2 ")                # (o) の相手＝毎回読む部分（先頭から項目 2 の終わりまで）
H01 = "### 3-1 "
H02 = "## 5 "
HB2 = "### 3-2 "
HD = "### 3-3 "
HERE_MARK = "★いまここ"
# ★2026-10-12（A-3）＝固定で載せる文が next_step に入っているかを見る文字（正本の先頭の見出しを、gen_core_requirements が太字の行にした物）
CORE_MARK = "**■ 要件定義と工事の流れ（固定・毎回 読む・消さない）**"
# ★2026-10-12（172回目・まこさん「OK」）＝next_step を2本に分けて作る。控えの見出しから後ろは、控えのファイルに出す。
REF_NAME = "next_step_reference.md"           # 控え（毎回は読まない・要るときに節を選んで開く）のファイル
REF_HEAD = "# 控え（"                          # この文字で始まる見出しの行から後ろが、控え
TOP_MAX = 150                                  # (o) 毎回読む部分（先頭から項目 2 の終わりまで・前は「# §0 」の前まで）の行数の上限
LINE_MAX = 250                                 # (p) 「次のセッションでやること」の節の、1行の字数の上限
NEXT_SEC = "## 2 次のセッションでやること"
ALL_MAX = 250                                  # (q) next_step.md の全体の行数の上限（まこさん「よい」2026-10-12）
STATE_SEC = "### 3-1 いまの状態"               # (r) この節は、最新の回だけを書く
STATE_MAX = 12                                 # (r) 「いまの状態」の、空でない行の数の上限
MUST_HEAD = "| いま必ず読むもの | なぜ読むか | 外す条件 |"   # (s) 必読の表の見出しの行（この表から must_read_now.txt を書く）
MUST_FILE = "must_read_now.txt"
TODO_HEAD = "| 番号 | やること | 状態 |"          # 「次のセッションでやること」の ToDo の表の見出しの行（--todo-from が行を写す）
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

# ★2026-10-02（146回目・まこさん指示・逐語「毎回私から、整理整頓しろとｋ、私が読みやすい状態にしろとか言うのだるいんだが。
#   自発的にやれるようにできないの？」「なにも私が言わないと、書き足し続けるって、すべてのデータがそうなってるよね」
#   「私のPCのストレージは有限なんだよ」→ 私の案「新しい決まりは作らず、いまの道具に自動の片づけを足す」→「じゃあ、その修正しろ」）
#   ＝片づけを CC の自発に任せず、この道具が自動でする（--write）・残っていればターンを終われない（--verify＝Stop hook）。
#   ①next_step の読みやすさ（読む人＝まこさん）②教訓の現役を40件に（CLAUDE.md「約40件超えたら最古を archive に移送」）
#   ③結果が出た監査の写しを消す。★見るのは形だけ＝文が分かりやすいかは見ない（CC が守る・まこさんの目）。
SDK_DIR = ROOT / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
LESSONS_ACTIVE = SDK_DIR / ".claude" / "memory" / "lessons_active.md"
LESSONS_ARCHIVE = SDK_DIR / ".claude" / "memory" / "lessons_archive.md"
LESSONS_KEEP = 40                             # CLAUDE.md の決まり（約40件）
LESSON_HEAD_RE = re.compile(r"^## L-(\d+)")
# 名指しされた教訓は現役に残す（控えへ移すと、名指しした文書の参照が切れるため）
PIN_FILES = (ROOT / ".claude" / "rules" / "permanent_rules.md", ROOT / "v3-bitget-api-sdk" / "CLAUDE.md")
AUDITS_DIR = SDK_DIR / ".claude" / "audits"
# ★2026-10-24（210回目・まこさん「今その仕組を入れられないの？」）＝前は名前が mirror・pristine・tmp で始まる写しだけを消し、
#   brk・tree_after・copy・orig などの名前の写しが 209MB 溜まった。いまは結果が出た監査の cp<N>_work の中のフォルダを、名前を問わず消す。
COPY_MIN_AGE = 3600                           # 作って1時間 以内の写しは消さない（走っている監査を壊さない）
SESSIONS_DIR = STATE / "sessions"
SESSION_MIN_AGE = 86400                       # 最後に書いてから1日 以内のセッションのフォルダは消さない（動いているセッションを壊さない）
TUNER_CACHE = SDK_DIR / "results" / "priority_rebuild" / "tuner_cache"
CACHE_RE = re.compile(r"^(.+)_([0-9a-f]{16})_\d+\.parquet$")   # engine_tuner.py の控えの名前＝<戦略>_<指紋>_<窓の番号>.parquet
TOP_NEXT = "## 1 毎回最初に読むこと"
HISTORY_RE = re.compile(r"\d+回目にしたこと")
CELL_MAX = 250                                # 0-2 の表の1つの欄の字数の上限


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
    head = (f"\n\n# {today} に tidy_next_step.py が next_step.md の「5 プロジェクトのやることの表」から移した行"
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
    """3-2 印の状態 の節の本文（型は固定・自由記述なし）。"""
    # ★2026-10-18（190回目・44番の3段目）＝「＝」と「／」でつないだ文を、読める文に書き直した（中身の値は同じ）。
    return (f"{HB2}🔴 印の状態（{today}・この節はプログラムが印の記録から書く）\n"
            "\n"
            f"- **H2 の印**は `{h2['fp']}…` です。未来のデータを使っていないかを調べる検査（`leak_causality_diag.py`）が、"
            f"全部通ったときの記録です（`.claude/state/h2_pass.json`・{h2['when']}・対象{h2['n']}ファイル）。\n"
            f"- **G2 の印**は `{g2['fp']}…` です。型の表に沿った案かを見る審査が、見本に正しく反応するかを試すテスト"
            f"（`gen_signal_families.py --verify`）が通ったときの記録です（`.claude/state/g2_pass.json`・{g2['when']}・対象{g2['n']}ファイル）。\n"
            "- コードを触ったら、G2、H2 の順に印を取り直します。かかる時間は、G2 が約30秒、H2 が約5分です（教訓 L-565）。\n"
            "\n")


def refresh_marks(next_text: str, h2: dict, g2: dict, today: str) -> str:
    """3-2 印の状態 の節を json の値で書き直す。節が無ければ 3-3 の直前に足す。印の数は変えない。"""
    lines = next_text.splitlines(keepends=True)
    idx = next((i for i, l in enumerate(lines) if l.startswith(HB2)), None)
    block = marks_block(h2, g2, today)
    if idx is None:
        ins = next((i for i, l in enumerate(lines) if l.startswith(HD)), None)
        if ins is None:
            raise SystemExit("[tidy] 3-2 印の状態 も 3-3 まだ埋まっていないこと も無い＝どこに書くか決められない")
        return "".join(lines[:ins]) + block + "".join(lines[ins:])
    j = _section_end(lines, idx)
    new = "".join(lines[:idx]) + block + "".join(lines[j:])
    b, a = count_marks(next_text), count_marks(new)
    if b != a:
        raise SystemExit(f"[tidy] 3-2 印の状態 を書き直すと印の数が変わる（前 {b} → 後 {a}）＝書かずに止まる")
    return new


def latest_worklog_date(state_dir: pathlib.Path) -> str | None:
    ds = []
    for p in state_dir.glob("session_worklog_*.md"):
        m = WORKLOG_RE.search(p.name)
        if m:
            ds.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
    return max(ds) if ds else None


def item_lines(lines: list[str], prefixes: tuple[str, ...]) -> list[str] | None:
    """見出しが prefixes で始まる項目の行を、並びのまま全部つないで返す（2026-10-18・§0 の区切りの代わり）。
    1つでも見つからなければ None。控えの見出し（REF_HEAD）より後ろは探さない（控えの中の同じ見出しを拾わない）。"""
    end_all = next((i for i, l in enumerate(lines) if l.startswith(REF_HEAD)), len(lines))
    out: list[str] = []
    for p in prefixes:
        s = next((i for i in range(end_all) if lines[i].startswith(p)), None)
        if s is None:
            return None
        out += lines[s:min(_section_end(lines, s), end_all)]
    return out


def check_area_lines(lines: list[str]) -> int | None:
    """(d) の相手（項目 3・5・6）の行数の合計。項目が1つでも無ければ None。"""
    got = item_lines(lines, CHECK_ITEMS)
    return None if got is None else len(got)


def top_lines(lines: list[str]) -> int | None:
    """(o) の相手＝先頭から項目 2 の終わりまでの行数。項目 1・2 のどちらかが無ければ None。"""
    if item_lines(lines, TOP_ITEMS) is None:
        return None
    s2 = next(i for i, l in enumerate(lines) if l.startswith(TOP_ITEMS[-1]))
    return _section_end(lines, s2)


def verify(next_text: str, h2: dict, g2: dict, worklog_date: str | None, limit: int = LIMIT) -> list[str]:
    """6つの検査。戻り＝❌ の一覧（空なら ✅）。"""
    ng: list[str] = []
    lines = next_text.splitlines()
    n_disp = len(find_disposable_sections(lines))
    if n_disp:
        ng.append(f"(a)「{DISPOSE}」の節が {n_disp} 件 残っている → `--write` で archive へ移す")
    h01 = next((l for l in lines if l.startswith(H01)), None)
    if h01 is None:
        ng.append(f"(b) 見出し『{H01.strip()} いまの状態』が無い")
    else:
        m = DATE_RE.search(h01)
        if not m:
            ng.append("(b) 3-1 いまの状態 の見出しに日付（YYYY-MM-DD）が無い")
        elif worklog_date and m.group(1) != worklog_date:
            ng.append(f"(b) 3-1 の日付 {m.group(1)} が、いちばん新しい worklog の日付 {worklog_date} と違う → 3-1 いまの状態 を今日の状態に書き直す")
    hb = next((i for i, l in enumerate(lines) if l.startswith(HB2)), None)
    if hb is None:
        ng.append(f"(c) 節『{HB2.strip()} 印の状態』が無い → `--write` で作る")
    else:
        body = "\n".join(lines[hb:_section_end(lines, hb)])
        if h2["fp"] not in body:
            ng.append(f"(c) (0-b-2) の H2 の印が json（{h2['fp']}…）と違う → `--write`")
        if g2["fp"] not in body:
            ng.append(f"(c) (0-b-2) の G2 の印が json（{g2['fp']}…）と違う → `--write`")
        # ★2026-10-18（190回目）＝(c) の文の「(0-b-2)」は、項目の名前が「3-2 印の状態」に変わった後も残す。
        #   壊すプログラム b67_marks_time_check.sh が、下の時刻の2行を文字のまま探している。壊すプログラムの直しは承認が要るので、
        #   この回は直していない（まこさん決定 2026-10-18「このまま残す」・worklog 20261018 §5・§6）。前の行の印の2行も、言い方をそろえて残した。
        # ★2026-09-08（監査 cp32 の別枠 E・設計書 tm-scope-and-g2-fingerprint-20260908 の F）
        #   ＝時刻も照らす。直す前は指紋の値だけを見ていたので、印を取り直した後に
        #     `--write` を走らせ忘れると、時刻だけが古いまま残った（監査が実測した）。
        if h2["when"] not in body:
            ng.append(f"(c) (0-b-2) の H2 の時刻が json（{h2['when']}）と違う → `--write`")
        if g2["when"] not in body:
            ng.append(f"(c) (0-b-2) の G2 の時刻が json（{g2['when']}）と違う → `--write`")
    n0 = check_area_lines(lines)
    if n0 is None:
        ng.append(f"(d) 項目 {'・'.join(p.strip() for p in CHECK_ITEMS)} の見出しのどれかが見つからない")
    elif n0 > limit:
        ng.append(f"(d) 項目 3・5・6 が {n0} 行（上限 {limit}）→ 古い節に「{DISPOSE}」の印を付けて `--write` で移す")
    s2 = next((i for i, l in enumerate(lines) if l.startswith(H02)), None)
    if s2 is None:
        ng.append(f"(e) 見出し『{H02.strip()} プロジェクトのやることの表』が無い")
    else:
        sec2 = lines[s2:_section_end(lines, s2)]
        n_here = "\n".join(sec2).count(HERE_MARK)
        if n_here != 1:
            ng.append(f"(e) 5 やることの表 の『{HERE_MARK}』が {n_here} 件（ちょうど1件のはず）")
        # (f) 終わった行を表に残せない（表の行だけを見る＝説明の文に書いても止めない）
        done = [l for l in sec2
                if l.lstrip().startswith("|") and (DONE_MARK in l or STRIKE_RE.search(l))]
        if done:
            ng.append(f"(f) 5 やることの表 に、終わった行が {len(done)} 行 残っている"
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


def _core_lines() -> list[str]:
    """固定で載せる文（要件定義と工事の流れ）を、正本から写す形で返す（2026-10-12・A-3）。
    正本（.claude/rules/core_requirements.md）が無い・逐語のファイルと違うときは、gen_core_requirements が止める（fail-closed）。"""
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import gen_core_requirements as gcr
    return gcr.embed_lines()


# ── 固定の文（2026-10-18・190回目・まこさん「OK」＝44番の2段目）──────────────────────
#   なぜ要るか＝next_step の「毎回最初に読むこと」や決まりの文も、元データの中のただの文だった。CC が書き足し続けると、
#   また崩れる（189回目に「次のセッションでやること」へ CC の注意書きを足し続けた＝worklog 20261018 §4）。
#   作り＝固定の文は、下書き（FIXED_DRAFT）と、まこさんが承認した版（FIXED_OK）に分ける。next_step は承認した版からだけ写す。
#     元データには文を持たせず、{"固定": "<名前>"} の印だけを置く（要件定義の {"正本": …} と同じ形）。
#     承認＝まこさんがご自分の端末で `tidy_next_step.py --approve-fixed` を打つ。Claude Code の中（環境変数 CLAUDECODE）からは断る。
#   限界＝CC が環境変数を外して打てば通る（止める物は無い・L-586＝抜け道を hook で塞ぎ続けない）。文が分かりやすいかは見ない。
FIXED_DRAFT = STATE / "next_step_fixed.md"
FIXED_OK = STATE / "next_step_fixed_approved.json"
FIXED_MARK_RE = re.compile(r"^<!-- 固定 (見出し|文 (.+)) -->$")
NO_EXTRA_ITEMS = ("## 1 ", "## 7 ")            # この項目の中には、固定の見出しの一覧に無い見出しを置かせない
FREE_NG_RE = re.compile(r"L-\d+|★")           # 「2 次のセッションでやること」の CC が書く行に入れない物（注意書きの印）


def parse_fixed(text: str) -> dict:
    """固定の文のファイルを {"見出し": [行], "文": {名前: [行]}} にする。形が崩れていれば ValueError。"""
    heads: list[str] | None = None
    blocks: dict[str, list[str]] = {}
    cur: list[str] | None = None
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    for ln in lines:
        m = FIXED_MARK_RE.match(ln)
        if m:
            cur = []
            if m.group(1) == "見出し":
                if heads is not None:
                    raise ValueError("「見出し」の印が2つ在る")
                heads = cur
            else:
                name = m.group(2)
                if name in blocks:
                    raise ValueError(f"同じ名前の固定の文が2つ在る＝{name}")
                blocks[name] = cur
            continue
        if cur is not None:
            cur.append(ln)
    if heads is None:
        raise ValueError("「<!-- 固定 見出し -->」の印が無い")
    if not blocks:
        raise ValueError("固定の文（<!-- 固定 文 名前 -->）が1つも無い")
    return {"見出し": [h for h in heads if h.strip()], "文": blocks}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


_FIXED_CACHE: dict = {}


def load_fixed_ok(path: pathlib.Path = None) -> dict | None:
    """承認した版を読む。戻り＝{"見出し", "文", "ok"（ハッシュ値が合うか）, "text"}／ファイルが無ければ None。"""
    path = path or FIXED_OK
    if not path.exists():
        return None
    d = json.loads(path.read_text(encoding="utf-8"))
    text = d.get("文", "")
    got = parse_fixed(text)
    got["ok"] = _sha(text) == d.get("sha256")
    got["text"] = text
    return got


def _fixed_lines(name: str) -> list[str]:
    if "ok" not in _FIXED_CACHE:
        _FIXED_CACHE["ok"] = load_fixed_ok()
    ok = _FIXED_CACHE["ok"]
    if ok is None:
        raise SystemExit(f"[tidy] 承認した固定の文（{FIXED_OK.name}）が無い＝まこさんに `tidy_next_step.py --approve-fixed` を打っていただく")
    if name not in ok["文"]:
        raise SystemExit(f"[tidy] 承認した固定の文に「{name}」が無い＝元データの {{\"固定\": …}} の名前か、固定の文のファイルを直す")
    return ok["文"][name]


def approve_fixed() -> int:
    """下書き（FIXED_DRAFT）を、承認した版（FIXED_OK）として記録する。まこさんが端末で打つ口。"""
    if os.environ.get("CLAUDECODE"):
        print("❌ [tidy --approve-fixed] Claude Code の中からは打てません。まこさんが、ご自分の端末で打ってください。")
        return 2
    if not FIXED_DRAFT.exists():
        print(f"❌ [tidy --approve-fixed] 下書き {FIXED_DRAFT} が無い")
        return 2
    text = FIXED_DRAFT.read_text(encoding="utf-8")
    try:
        got = parse_fixed(text)
    except ValueError as e:
        print(f"❌ [tidy --approve-fixed] 下書きの形が崩れている＝{e}")
        return 2
    old = load_fixed_ok()
    from datetime import datetime
    _atomic_write(FIXED_OK, json.dumps({"sha256": _sha(text), "承認した日時": datetime.now().isoformat(timespec="seconds"),
                                        "文": text}, ensure_ascii=False, indent=1) + "\n")
    changed = ([n for n in got["文"] if old is None or old["文"].get(n) != got["文"][n]]
               + [n for n in (old["文"] if old else {}) if n not in got["文"]])
    print(f"✅ [tidy --approve-fixed] 固定の文を承認した版として記録した（見出し {len(got['見出し'])} 行・固定の文 {len(got['文'])} 個"
          f"・前の承認から変わった物 {len(changed)} 個）")
    for n in changed:
        print(f"   ・{n}")
    print("   続けて CC が `tidy_next_step.py --write` を打つと、next_step に入ります。")
    return 0


def _heading_match(doc_h: str, want: str) -> bool:
    """固定の見出しと合うか＝同じ、または、その後ろに「（」で始まる補足が付いている（日付・回の数・件数が入る見出し）。"""
    return doc_h == want or doc_h.startswith(want + "（")


def fixed_checks_core(src: dict, doc_text: str, ok: dict | None) -> list[str]:
    """(t) 固定の文の検査。src＝元データ／doc_text＝作った全文（毎回読む文書＋控え）／ok＝承認した版。戻り＝❌ の一覧。"""
    ng: list[str] = []
    used = [b["固定"] for s in src["節"] for b in s.get("塊", []) if "固定" in b]
    if ok is None:
        if used:
            ng.append(f"(t) 元データが固定の文を使っているのに、承認した版（{FIXED_OK.name}）が無い"
                      "＝まこさんに `tidy_next_step.py --approve-fixed` を打っていただく")
        return ng
    if not ok["ok"]:
        ng.append(f"(t) 承認した版（{FIXED_OK.name}）のハッシュ値が中身と違う＝承認の記録を手で書き替えた"
                  "→ 書き替えを戻すか、まこさんに承認し直していただく")
    for n in used:
        if n not in ok["文"]:
            ng.append(f"(t) 元データの固定の印「{n}」が、承認した版に無い")
    for n in ok["文"]:
        k = used.count(n)
        if k != 1:
            ng.append(f"(t) 承認した固定の文「{n[:40]}」が、元データで {k} 回 使われている（ちょうど1回のはず）"
                      "＝元データの固定の印を消した・増やした")
    by_head = {s.get("見出し", ""): s for s in src["節"]}
    for n in ok["文"]:
        s = by_head.get(n)
        if s is not None and s.get("塊") != [{"固定": n}]:
            ng.append(f"(t) 固定の節「{n[:40]}」に、固定の文のほかの物が入っている＝CC の書き足しは「8 CC メモ」へ移す")
    heads = [l for l in doc_text.splitlines() if HEAD_RE.match(l)]
    k = 0
    for h in heads:
        if k < len(ok["見出し"]) and _heading_match(h, ok["見出し"][k]):
            k += 1
    if k < len(ok["見出し"]):
        ng.append(f"(t) 固定の見出し「{ok['見出し'][k][:40]}」が、決まった順の位置に無い＝見出しを直した・消した・並べ替えた")
    lines = doc_text.splitlines()
    for p in NO_EXTRA_ITEMS:
        s = next((i for i, l in enumerate(lines) if l.startswith(p)), None)
        if s is None:
            continue
        extra = [l for l in lines[s + 1:_section_end(lines, s)]
                 if HEAD_RE.match(l) and not any(_heading_match(l, w) for w in ok["見出し"])]
        if extra:
            ng.append(f"(t) 項目「{p.strip()}」の中に、固定の一覧に無い見出しが在る＝{extra[0][:40]}（CC の書き足しは「8 CC メモ」へ）")
    sec2 = next((s for s in src["節"] if s.get("見出し", "").startswith(NEXT_SEC)), None)
    if sec2 is not None:
        bad = [l for b in sec2.get("塊", []) if "文" in b for l in b["文"] if l.strip() and FREE_NG_RE.search(l)]
        if bad:
            ng.append(f"(t) 「2 次のセッションでやること」の CC が書く行に、教訓の番号か「★」が {len(bad)} 行 在る"
                      f"＝注意書きは「8 CC メモ」へ移す／1行目＝{bad[0][:40]}")
    return ng


def _section_lines(sec: dict) -> list[str]:
    return render({"節": [sec], "末尾の改行": False}).split("\n")


def restore_special_blocks(old: dict, new: dict) -> None:
    """作った文書を元データに戻したとき（parse_doc）、固定の印と正本の印の塊は文に変わってしまう。
    元の元データで印を持っていた節の塊を、同じ見出しの節に戻す。中身が変わっていれば書かずに止まる（fail-closed）。
    ★2026-10-18（190回目）に見つけた不具合の直し＝前は、要件定義の {"正本": …} の塊が、--write のたびに文に書き戻されていた
      （いまの元データに「正本」の塊は0個・2026-10-18 に jq で確かめた）。正本を直しても、next_step は変わらなかった。"""
    taken: set[int] = set()
    for so in old["節"]:
        if not any(("固定" in b or "正本" in b) for b in so.get("塊", [])):
            continue
        j = next((k for k, sn in enumerate(new["節"]) if k not in taken and sn.get("見出し") == so.get("見出し")), None)
        if j is None:
            raise SystemExit(f"[tidy] 固定の文か正本を写す節「{so.get('見出し', '')[:40]}」が、作った文書に無い＝書かずに止まる")
        if _section_lines(new["節"][j]) != _section_lines(so):
            raise SystemExit(f"[tidy] 固定の文か正本を写す節「{so.get('見出し', '')[:40]}」の中身が、作る途中で変わった＝書かずに止まる")
        new["節"][j]["塊"] = so["塊"]
        taken.add(j)


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
            elif "固定" in blk:
                # ★2026-10-18（190回目）＝この塊は元データに文を持たない。まこさんが承認した固定の文から写す。
                out.extend(_fixed_lines(blk["固定"]))
            elif "正本" in blk:
                # ★2026-10-12（A-3）＝この塊は元データに文を持たない。作るたびに正本から写す（正本を直せば、次の --write で next_step も変わる）。
                #   ★--import（next_step.md から元データを作り直す口）は、この塊を「文」に変えてしまう＝使ったら、塊を {"正本": …} に戻す。
                out.extend(_core_lines())
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


def split_ref(body: str) -> tuple[str, str]:
    """本文を、毎回読む文書と、控えに分ける（2026-10-12・172回目・まこさん「OK」）。
    控えの見出し（REF_HEAD で始まる行）から後ろが控え。その見出しが無ければ、控えは空。
    なぜ要るか＝毎回読む文書に、期間限定の決まりや古い一覧が混ざり、346行になっていた（worklog 20261012 §32）。"""
    lines = body.splitlines(keepends=True)
    for i, l in enumerate(lines):
        if l.startswith(REF_HEAD):
            return "".join(lines[:i]), "".join(lines[i:])
    return body, ""


def length_checks(text: str) -> list[str]:
    """毎回読む文書の長さを見る（2026-10-12・まこさん「OK」＝毎回読む部分 150行・1行 250字）。戻り＝❌ の一覧。
    なぜ要るか＝長さを止める物が §0 の100行だけで、足すだけで済んでいた。超えたら、何かを控えへ移すまで終われない形にする。"""
    ng: list[str] = []
    lines = text.splitlines()
    s0 = top_lines(lines)
    if s0 is None:
        ng.append(f"(o) 項目 {'・'.join(p.strip() for p in TOP_ITEMS)} の見出しのどちらかが見つからない")
    elif s0 > TOP_MAX:
        ng.append(f"(o) 毎回読む部分（先頭から項目 2 の終わりまで）が {s0} 行＝上限 {TOP_MAX} 行を超えた"
                  f"＝経緯は worklog へ・期間限定の物と古い物は控え（{REF_HEAD}…の見出しの後ろ）へ移す")
    n = next((i for i, l in enumerate(lines) if l.startswith(NEXT_SEC)), None)
    if n is None:
        ng.append(f"(p) 「{NEXT_SEC}」の節が無い")
    else:
        long_lines = [l for l in lines[n:_section_end(lines, n)] if len(l) > LINE_MAX]
        if long_lines:
            ng.append(f"(p) 「次のセッションでやること」の節に、{LINE_MAX} 字を超える行が {len(long_lines)} 行 在る"
                      f"＝1件1行で短く書く／1つ目＝{long_lines[0][:40]}（{len(long_lines[0])}字）")
    # (q) 全体の行数（まこさん「よい」2026-10-12＝250行）
    if len(lines) > ALL_MAX:
        ng.append(f"(q) next_step.md の全体が {len(lines)} 行＝上限 {ALL_MAX} 行を超えた"
                  f"＝古い物・期間限定の物を、控え（{REF_HEAD}…の見出しの後ろ）か worklog へ移す")
    # (r) 「いまの状態」は最新の回だけ（前の回が1つの段落に積み重なっていた＝worklog 20261012 §32 の P5）
    s1 = next((i for i, l in enumerate(lines) if l.startswith(STATE_SEC)), None)
    if s1 is not None:
        body = [l for l in lines[s1 + 1:_section_end(lines, s1)] if l.strip()]
        long_b = [l for l in body if len(l) > LINE_MAX]
        if len(body) > STATE_MAX or long_b:
            ng.append(f"(r) 「3-1 いまの状態」が {len(body)} 行（上限 {STATE_MAX} 行）・{LINE_MAX} 字を超える行が {len(long_b)} 行"
                      f"＝最新の回だけを、短い行で書く。前の回は worklog の節の番号で指す")
    # (s) 必読の表（ファイル・なぜ読むか・外す条件）。外す条件が空の行は通さない＝期間限定の必読が、いつまでも残らないようにする
    rows = must_rows(text)
    if rows is None:
        ng.append(f"(s) 必読の表（見出しの行＝{MUST_HEAD}）が無い＝「次のセッションでやること」の「最初にやる事」に置く")
    else:
        for path, why, cond in rows:
            if not (path and why and cond):
                ng.append(f"(s) 必読の表に、空の欄が在る（ファイル・なぜ読むか・外す条件を全部 書く）＝{path or '（ファイルが空）'}")
            elif not (ROOT / path).exists():
                ng.append(f"(s) 必読の表のファイルが無い＝{path}")
    return ng


def must_rows(text: str):
    """必読の表（MUST_HEAD の行から、表が切れるまで）の行を返す。戻り＝[(ファイル, なぜ読むか, 外す条件)]／表が無ければ None。"""
    lines = text.splitlines()
    i = next((k for k, l in enumerate(lines) if l.strip() == MUST_HEAD), None)
    if i is None:
        return None
    out = []
    for l in lines[i + 2:]:
        if not l.lstrip().startswith("|"):
            break
        cells = [c.strip().strip("`") for c in l.strip().strip("|").split("|")]
        cells += [""] * (3 - len(cells))
        out.append((cells[0], cells[1], cells[2]))
    return out


def must_file_text(rows) -> str:
    """必読の一覧（must_read_now.txt）の中身を、必読の表の行から作る（2026-10-12・172回目）。
    なぜ要るか＝一覧を手で書いていて、工事が替わった後も、前の工事の資料を読ませ続けていた（worklog 20261012 §28）。"""
    head = ["# いま必ず読むもの（★tidy_next_step.py が、next_step.md の必読の表から書く＝手で書き換えない・2026-10-12）",
            "# 直す道＝元データ next_step_src.json の「次のセッションでやること」の必読の表を直す → tidy_next_step.py --write",
            "# 読む側＝始めの表示（reset_read_log.sh）。「#」の行は読み飛ばす。"
            "必読を止める hook（require_read_before_work.sh）は 2026-10-01 から登録が無い。"]
    return "\n".join(head + [p for p, _w, _c in rows if p]) + "\n"


def copy_todo(next_path: pathlib.Path, sid: str) -> int:
    """そのセッションの ToDo の、済んでいない行を、元データの「次のセッションでやること」の表に写す（2026-10-12・まこさん「OK」）。
    なぜ要るか＝171回目の締めで、ToDo の流れの段を手で写さず、次の回が落とした（worklog 20261012 §29）。写した後に --write を打つ。"""
    src_path = next_path.parent / SRC_NAME
    todo = next_path.parent / "sessions" / sid / "session_todo.md"
    if not src_path.exists() or not todo.exists():
        print(f"❌ [tidy --todo-from] 元データか ToDo が無い（{src_path}・{todo}）")
        return 2
    rows = []
    for l in todo.read_text(encoding="utf-8").splitlines():
        s = l.strip()
        if not s.startswith("|"):
            continue
        c = [x.strip() for x in s.strip("|").split("|")]
        # ★2026-10-18（189回目）＝恒久の決まり55番は「✅済（日付）」と日付を添える。直す前は「✅済」の4文字だけと比べ、
        #   日付つきの済んだ行（29・35・43番）を写していた＝毎回読む部分が上限を超えた
        if len(c) < 3 or not c[0].isdigit() or c[2].startswith(DONE_MARK):
            continue
        # ToDo の「★いまここ」の行は、次の回が始める行＝「いまここ（次の回は、ここから）」と写す
        rows.append({"欄": [f" {c[0]} ", f" {c[1]} ", f" {'いまここ（次の回は、ここから）' if c[2] == HERE_MARK else c[2]} "]})
    src = json.loads(src_path.read_text(encoding="utf-8"))
    done = False
    for sec in src["節"]:
        if not sec.get("見出し", "").startswith(NEXT_SEC):
            continue
        for blk in sec.get("塊", []):
            if "表" in blk and blk["表"]["見出しの行"].strip() == TODO_HEAD:
                blk["表"]["行"] = rows
                done = True
    if not done or not rows:
        print(f"❌ [tidy --todo-from] 写せない（表の見出しの行「{TODO_HEAD}」が元データに在るか＝{done}・済んでいない行＝{len(rows)}）")
        return 2
    _atomic_write(src_path, json.dumps(src, ensure_ascii=False, indent=1) + "\n")
    print(f"✅ [tidy --todo-from] ToDo の済んでいない {len(rows)} 行を、元データの表に写した → 続けて --write を打つ")
    return 0


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
    # ★2026-10-12（172回目）＝元データから作った全文を、毎回読む文書と控えに分けて、それぞれのファイルと照らす。
    main_r, ref_r = split_ref(render(src))
    if main_r != body:
        ng.append(f"(g) 本文が元データ {SRC_NAME} から作ったものと違う → 元データを直して `--write`／最初に違う所＝{_first_diff(body, main_r)}")
    ref_path = next_path.parent / REF_NAME
    if ref_r:
        if not ref_path.exists():
            ng.append(f"(g) 控えのファイル {REF_NAME} が無い → `tidy_next_step.py --write`")
        else:
            rbody, rh = strip_gen_head(ref_path.read_text(encoding="utf-8"))
            if rh is None or rh != _hash16(rbody):
                ng.append(f"(g) 控えのファイル {REF_NAME} の目印のハッシュ値が本文と違う＝手で書き換えた → 元データを直して `--write`")
            if rbody != ref_r:
                ng.append(f"(g) 控えのファイル {REF_NAME} が元データから作ったものと違う → `--write`／最初に違う所＝{_first_diff(rbody, ref_r)}")
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
    ng += reading_checks(new_next)                 # ★2026-10-02＝まこさんが読む形か（(h)〜(k)）
    ng += length_checks(split_ref(new_next)[0])    # ★2026-10-12＝毎回読む部分の長さ（(o)(p)）
    ng += fixed_checks_core(src, new_next, load_fixed_ok())   # ★2026-10-18＝固定の文（(t)）
    if miss:
        ng += [f"(参照) {x} が見出しに無い（元データの文を直す）" for x in miss]
    if ng:
        print(f"❌ [tidy --write] 元データから作った文書に {len(ng)} 件＝1文字も書かない:")
        for x in ng:
            print(f"   ・{x}")
        return 2
    new_src = parse_doc(new_next)
    restore_special_blocks(src, new_src)           # ★2026-10-18＝固定の印と正本の印を、文に変えずに残す
    if render(new_src) != new_next:
        print(f"❌ [tidy --write] 作った文書を元データに戻すと形が変わる＝書かない／{_first_diff(new_next, render(new_src))}")
        return 2
    new_src[BASELINE_KEY] = src.get(BASELINE_KEY, [])
    new_src[S6_FLAG] = bool(src.get(S6_FLAG))
    if new_arc != arc:
        _atomic_write(arc_path, new_arc)
    _atomic_write(src_path, json.dumps(new_src, ensure_ascii=False, indent=1) + "\n")
    # ★2026-10-12（172回目）＝控えの見出し（REF_HEAD）の行から後ろは、控えのファイルに出す。毎回読む文書には載せない。
    main_part, ref_part = split_ref(new_next)
    _atomic_write(next_path, gen_head(main_part) + main_part)
    ref_path = next_path.parent / REF_NAME
    if ref_part:
        _atomic_write(ref_path, gen_head(ref_part) + ref_part)
    elif ref_path.exists():
        ref_path.unlink()                          # 控えが空になったら、古い控えのファイルを残さない
    # ★2026-10-12（172回目）＝必読の一覧（must_read_now.txt）を、毎回読む文書の必読の表から書く（手で書かない）。
    _atomic_write(next_path.parent / MUST_FILE, must_file_text(must_rows(main_part) or []))
    n_les = trim_lessons(today)                    # ★2026-10-02＝教訓の現役を40件＋名指しされた物に
    n_cp = clean_audit_copies()                    # ★2026-10-02＝結果が出た監査の写しを消す
    n_ss = clean_old_sessions()                    # ★2026-10-24＝終わったセッションのフォルダを消す
    n_tc = clean_tuner_cache()                     # ★2026-10-24＝tuner_cache の古い指紋の控えを消す
    print(f"[tidy --write] 元データ {SRC_NAME} から作った／移した節 {rep['moved_sections']}"
          f"／5 やることの表 から移した行 {rep2['moved_rows']}／§6 の表から移した行 {rep3['moved_rows']}"
          f"（§6 を移す設定＝{bool(src.get(S6_FLAG))}）／worklog の参照を照らした（控えの外で見つからない参照 0 件）"
          f"／(0-b-2) を json から書いた／教訓を控えへ移した {n_les} 件／監査の写しを消した {n_cp} 個"
          f"／終わったセッションのフォルダを消した {n_ss} 個／tuner_cache の古い控えを消した {n_tc} 本")
    return do_verify(next_path, limit)


# ── 自動の片づけ（2026-10-02・146回目）───────────────────────────────────────
def reading_checks(text: str) -> list[str]:
    """next_step を まこさんが読む形かを見る（形だけ）。戻り＝❌ の一覧。"""
    ng: list[str] = []
    lines = text.splitlines()
    h2s = [l for l in lines if l.startswith("## ")]
    if not h2s or not h2s[0].startswith(TOP_NEXT):
        ng.append(f"(h) 最初の「## 」の見出しが『{TOP_NEXT}』でない＝毎回最初に読むことを文書の先頭に置く")
    sec0 = item_lines(lines, CHECK_ITEMS)
    if sec0 is not None:
        hist = [l for l in sec0 if HISTORY_RE.search(l)]
        if hist:
            ng.append(f"(i) 項目 3・5・6 に経緯（「N回目にしたこと」）が {len(hist)} 行 在る＝経緯は worklog に書く"
                      f"（その節の見出しに「{DISPOSE}」を付けて `--write` で控えへ）／1行目＝{hist[0].strip()[:40]}")
        seen: dict[str, int] = {}
        for l in sec0:
            t = l.strip()
            if not t or t.startswith("|") or t in ("---", ">") or SEP_RE.match(t):
                continue
            seen[t] = seen.get(t, 0) + 1
        dup = [t for t, n in seen.items() if n > 1]
        if dup:
            ng.append(f"(k) 項目 3・5・6 に同じ行が {len(dup)} 種類 2回以上 在る＝1か所にまとめる／1つ目＝{dup[0][:40]}")
    s2 = next((i for i, l in enumerate(lines) if l.startswith(H02)), None)
    if s2 is not None:
        long_cells = []
        for l in lines[s2:_section_end(lines, s2)]:
            cells = _split_cells(l) if l.lstrip().startswith("|") else None
            for c in cells or []:
                if len(c.strip()) > CELL_MAX:
                    long_cells.append(c.strip())
        if long_cells:
            ng.append(f"(j) 5 やることの表 に {CELL_MAX} 字を超える欄が {len(long_cells)} 個 在る＝短くし、経緯は worklog へ"
                      f"／1つ目＝{long_cells[0][:40]}（{len(long_cells[0])}字）")
    # ★2026-10-12（170回目・まこさん「OK」＝直し方の案 A-3）＝固定で載せる文（要件定義と工事の流れ）が、next_step に在るか。
    #   まこさん指示（2026-10-12）＝要件定義と工事の流れを、設計書・next_step・監査の依頼書の上部に固定で載せる。絶対に消さない。
    if CORE_MARK not in text:
        ng.append(f"(n) 固定で載せる文（{CORE_MARK}）が無い＝元データ next_step_src.json の節に、"
                  "正本を写す塊（{\"正本\": \"core_requirements\"}）を戻す（消さない・まこさん指示 2026-10-12）")
    return ng


def _pinned_lessons() -> set[int]:
    """ほかの文書が「lessons_active … L-NNN」と名指ししている番号。"""
    pins: set[int] = set()
    for p in PIN_FILES:
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        for m in re.finditer(r"lessons_active", t):
            pins.update(int(x) for x in re.findall(r"L-(\d+)", t[m.end(): m.end() + 60]))
    return pins


def lessons_plan() -> tuple[list[str], list[tuple[int, str]], list[tuple[int, str]]]:
    """現役の教訓を (頭の行, 残す塊, 移す塊) に分ける。塊＝(番号, 本文)。並びは元のまま。"""
    if not LESSONS_ACTIVE.exists():
        return [], [], []
    lines = LESSONS_ACTIVE.read_text(encoding="utf-8").splitlines(keepends=True)
    head: list[str] = []
    blocks: list[tuple[int, list[str]]] = []
    for l in lines:
        m = LESSON_HEAD_RE.match(l)
        if m:
            blocks.append((int(m.group(1)), [l]))
        elif blocks:
            blocks[-1][1].append(l)
        else:
            head.append(l)
    nums = sorted({n for n, _ in blocks}, reverse=True)
    keep = set(nums[:LESSONS_KEEP]) | _pinned_lessons()
    kept = [(n, "".join(b)) for n, b in blocks if n in keep]
    moved = [(n, "".join(b)) for n, b in blocks if n not in keep]
    return head, kept, moved


def trim_lessons(today: str) -> int:
    """番号の新しい40件と名指しされた教訓だけを現役に残し、残りを控えの末尾へ移す。戻り＝移した件数。"""
    head, kept, moved = lessons_plan()
    if not moved:
        return 0
    old = LESSONS_ACTIVE.read_text(encoding="utf-8")
    new_active = "".join(head) + "".join(b for _, b in kept)
    if len(new_active) + sum(len(b) for _, b in moved) != len(old):
        raise SystemExit("❌ [tidy --write] 教訓を分けると文字数が合わない＝書かない")
    arc = LESSONS_ARCHIVE.read_text(encoding="utf-8") if LESSONS_ARCHIVE.exists() else ""
    ns = [n for n, _ in moved]
    add = (("" if arc.endswith("\n") or not arc else "\n")
           + f"\n## {today} 移送分（tidy_next_step.py が自動で移した・{len(moved)}件・L-{min(ns)}〜L-{max(ns)}）\n\n"
           + "".join(b if b.endswith("\n") else b + "\n" for _, b in moved))
    _atomic_write(LESSONS_ARCHIVE, arc + add)
    _atomic_write(LESSONS_ACTIVE, new_active)
    return len(moved)


def finished_audit_copies() -> list[pathlib.Path]:
    """結果のファイルが出た監査の写しのうち、git に入っている物が無く、作って1時間を過ぎた物。"""
    import time
    out: list[pathlib.Path] = []
    if not AUDITS_DIR.exists():
        return out
    for work in sorted(AUDITS_DIR.glob("cp*_work")):
        m = re.match(r"cp(\d+)_work$", work.name)
        if not m or not list(AUDITS_DIR.glob(f"*_cp{m.group(1)}_audit_report.md")):
            continue
        for d in sorted(work.iterdir()):
            if not d.is_dir():
                continue
            if time.time() - d.stat().st_mtime < COPY_MIN_AGE:
                continue
            r = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--", str(d)], capture_output=True, text=True)
            if r.returncode == 0 and not r.stdout.strip():
                out.append(d)
    for d in sorted(AUDITS_DIR.glob("*selftest*_work")):     # 自己テストが作った一時の作業フォルダ
        if not d.is_dir() or time.time() - d.stat().st_mtime < COPY_MIN_AGE:
            continue
        r = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--", str(d)], capture_output=True, text=True)
        if r.returncode == 0 and not r.stdout.strip():
            out.append(d)
    return out


def _newest_mtime(d: pathlib.Path) -> float:
    ts = [p.stat().st_mtime for p in d.rglob("*") if p.is_file()]
    return max(ts) if ts else d.stat().st_mtime


def clean_old_sessions() -> int:
    """終わったセッションのフォルダ（最後に書いてから1日 過ぎ・git の外）を消す。hook が読むのは、いまのセッションのフォルダだけ。"""
    import shutil
    import time
    if not SESSIONS_DIR.exists():
        return 0
    n = 0
    for d in sorted(SESSIONS_DIR.iterdir()):
        if not d.is_dir() or time.time() - _newest_mtime(d) < SESSION_MIN_AGE:
            continue
        r = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--", str(d)], capture_output=True, text=True)
        if r.returncode == 0 and not r.stdout.strip():
            shutil.rmtree(d)
            n += 1
    return n


def clean_tuner_cache() -> int:
    """tuner_cache の控えのうち、戦略ごとの いちばん新しい指紋でない物（作って1時間 過ぎ）を消す。
    指紋はデータの作り方のファイルが1文字変わるだけで別物になり、古い指紋の控えは二度と読まれない（engine_tuner.py の data_fingerprint）。"""
    import time
    if not TUNER_CACHE.exists():
        return 0
    groups: dict[str, dict[str, list[pathlib.Path]]] = {}
    for p in TUNER_CACHE.iterdir():
        m = CACHE_RE.match(p.name)
        if p.is_file() and m:
            groups.setdefault(m.group(1), {}).setdefault(m.group(2), []).append(p)
    n = 0
    for fps in groups.values():
        newest = max(fps, key=lambda fp: max(q.stat().st_mtime for q in fps[fp]))
        for fp, files in fps.items():
            if fp == newest:
                continue
            for q in files:
                if time.time() - q.stat().st_mtime >= COPY_MIN_AGE:
                    q.unlink()
                    n += 1
    return n


def tidy_checks() -> list[str]:
    """教訓の件数と監査の写し（--write で片づく物が残っていれば ❌）。"""
    ng: list[str] = []
    _, kept, moved = lessons_plan()
    if moved:
        ng.append(f"(l) 教訓の現役が {len(kept) + len(moved)} 件（上限 {LESSONS_KEEP} 件＋名指しされた物）→ `--write` で {len(moved)} 件を控えへ移す")
    cps = finished_audit_copies()
    if cps:
        ng.append(f"(m) 結果が出た監査の写しが {len(cps)} 個 残っている → `--write` で消す／1つ目＝{cps[0].relative_to(ROOT)}")
    return ng


def clean_audit_copies() -> int:
    import shutil
    cps = finished_audit_copies()
    for d in cps:
        shutil.rmtree(d)
    return len(cps)


# ── 口 ───────────────────────────────────────────────────────────────────────
def do_verify(next_path: pathlib.Path, limit: int) -> int:
    text = next_path.read_text(encoding="utf-8")
    # ★2026-10-12（172回目・まこさん「OK」）＝控えのファイルが在れば、毎回読む文書の後ろに つないだ全文で、前からの検査を掛ける
    #   （前からの検査は、§6 などを含む1本の文書を相手に作ってある＝相手を変えない）。長さの検査 (o)(p) だけ、毎回読む文書を見る。
    has_src = (next_path.parent / SRC_NAME).exists()
    ref_path = next_path.parent / REF_NAME
    ref_body = strip_gen_head(ref_path.read_text(encoding="utf-8"))[0] if has_src and ref_path.exists() else ""
    full = text + ref_body
    ng = verify(full, _pass(H2), _pass(G2), latest_worklog_date(next_path.parent), limit)
    # ★2026-09-17＝元データ next_step_src.json が在れば (g) も見る（目印・全文のハッシュ値・元データから作ったままか）
    ng += check_generated(next_path)
    # ★2026-10-02＝本物の next_step（元データが隣に在る）だけ、読む形 (h)〜(k) と片づけ (l)(m) も見る
    #   （自己テストの見本の文書は元データを持たないので、ここは見ない＝19本のテストはそのまま）
    if has_src:
        ng += reading_checks(full) + length_checks(text) + tidy_checks()
        # ★2026-10-18＝固定の文（(t)）。下書きが承認した版と違うだけなら止めない（承認を待っている状態）＝知らせるだけ
        _src = json.loads((next_path.parent / SRC_NAME).read_text(encoding="utf-8"))
        _ok = load_fixed_ok()
        ng += fixed_checks_core(_src, strip_gen_head(text)[0] + ref_body, _ok)
        if _ok is not None and FIXED_DRAFT.exists() and FIXED_DRAFT.read_text(encoding="utf-8") != _ok["text"]:
            print(f"（固定の文の下書き {FIXED_DRAFT.name} が、承認した版と違います＝まこさんの承認を待っている直しが在る。"
                  "next_step は承認した版から作っています）")
        # ★2026-10-12＝必読の一覧（must_read_now.txt）が、必読の表から書いたままか
        mf = next_path.parent / MUST_FILE
        if not mf.exists() or mf.read_text(encoding="utf-8") != must_file_text(must_rows(text) or []):
            ng.append(f"(s) 必読の一覧 {MUST_FILE} が、next_step.md の必読の表から書いたままではない → `tidy_next_step.py --write`")
    if ng:
        print(f"❌ [tidy --verify] {next_path.name} の形に {len(ng)} 件:")
        for x in ng:
            print(f"   ・{x}")
        return 2
    n0 = check_area_lines(text.splitlines())
    _n_chk = ("20個（6つ＋(g) 元データと全文のハッシュ値＋(h)〜(k)・(n) 読む形と固定で載せる文＋(o)(p)(q) 長さ＋(r) いまの状態＋(s) 必読の表"
              "＋(l) 教訓の件数・(m) 監査の写し＋(t) 固定の文）"
              if (next_path.parent / SRC_NAME).exists() else "6つ")
    print(f"✅ [tidy --verify] {_n_chk}とも通った（項目 3・5・6 が {n0} 行／上限 {limit}）")
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
          f"／5 やることの表 から移した行 {rep2['moved_rows']}"
          f"／印の数 前 {rep['before']} → 後 {count_marks(new_next)}（移した分 {rep['moved']}＋{rep2['moved']}）"
          f"／(0-b-2) を json から書いた")
    return do_verify(next_path, limit)


# ── わざと壊して止まるか試すテスト ────────────────────────────────────────────
# ★2026-10-18（190回目）＝見本を、組み替えた後の項目の見出し（3 いまの状態・5 やることの表・6 記録と置き場の案内）に替えた。
#   前は「# §0 」〜「## §0-4」の範囲と、0-1・0-2・(0-b-2)・(0-d) の見出しだった。中身の行（記録・表の行・印）は同じ。
SAMPLE = """# 次のセッションの起点

## 3 いまの状態

### 3-1 いまの状態（{d}・◯回目の末）

> 🔴 次のセッションはここから。

#### （3-1' 前回の記録・次の書き替えで消す）

- 🔴 古い記録1

#### （3-1'' 前々回の記録・次の書き替えで消す）

- ★消さない 古い記録2
- 毎回消さない 古い記録3

### 3-2 🔴 印の状態（2026-01-01 時点）

- H2 の印＝`0000000000000000…`／G2 の印＝`1111111111111111…`

### 3-3 まだ埋まっていないこと

| # | 何 |
|---|---|

## 5 🔴 次にやること

| 番号 | やること | 状態 |
|---|---|---|
| 1 | あれ | まだ |
| 2 | これ | ★いまここ |

## 6 記録と置き場の案内

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
    r3 = verify(clean.replace(f"### 3-1 いまの状態（{today}", "### 3-1 いまの状態（2026-08-20"), h2, g2, today, LIMIT)
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
    n0 = check_area_lines(clean.splitlines())
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
    r9c = verify(clean.replace("## 5 🔴 次にやること",
                               f"## 5 🔴 次にやること\n\n終わった行（{DONE_MARK}）は archive へ移します。"),
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
    d12 = clean.replace("## 5 🔴 次にやること",
                        f"## 5 🔴 次にやること\n\n終わった行（{DONE_MARK}）は archive へ移します。")
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

    # ★T11〜T17（2026-10-18・190回目）＝固定の文 (t)。本物の承認した版は使わず、見本の版を _FIXED_CACHE に入れて試す。
    fx_text = ("<!-- 固定 見出し -->\n# 題\n## 1 毎回最初に読むこと\n### 1-1 甲\n## 2 次のセッションでやること\n"
               "<!-- 固定 文 ### 1-1 甲 -->\n\n- 甲の文\n<!-- 固定 文 2 手順 -->\n- 手順\n")
    fx_ok = parse_fixed(fx_text)
    fx_ok.update(ok=True, text=fx_text)
    fx_src = {"節": [{"見出し": "# 題", "塊": [{"文": [""]}]}, {"見出し": "## 1 毎回最初に読むこと", "塊": []},
                     {"見出し": "### 1-1 甲", "塊": [{"固定": "### 1-1 甲"}]},
                     {"見出し": "## 2 次のセッションでやること（9回目）", "塊": [{"固定": "2 手順"}, {"文": ["- 作る物"]}]}],
              "末尾の改行": True}
    _saved = _FIXED_CACHE.pop("ok", None)
    _FIXED_CACHE["ok"] = fx_ok
    try:
        fx_doc = render(fx_src)
        r11 = fixed_checks_core(fx_src, fx_doc, fx_ok)
        if r11:
            ng.append(f"T11: きれいな見本で (t) が出た {r11}")
        s12 = json.loads(json.dumps(fx_src))
        s12["節"][2]["塊"].append({"文": ["- CC が足した行"]})
        if not any(x.startswith("(t)") for x in fixed_checks_core(s12, render(s12), fx_ok)):
            ng.append("T12: 固定の節に書き足しても (t) が出ない")
        s13 = json.loads(json.dumps(fx_src))
        s13["節"][3]["塊"][1]["文"].append("- ★次から気をつける（L-999）")
        if not any(x.startswith("(t)") for x in fixed_checks_core(s13, render(s13), fx_ok)):
            ng.append("T13: 2 の CC が書く行に ★ と教訓の番号が在っても (t) が出ない")
        d14a = fx_doc.replace("### 1-1 甲", "### 1-1 乙")
        d14b = fx_doc.replace("- 甲の文", "- 甲の文\n#### CC のメモ")
        if not (any(x.startswith("(t)") for x in fixed_checks_core(fx_src, d14a, fx_ok))
                and any(x.startswith("(t)") for x in fixed_checks_core(fx_src, d14b, fx_ok))):
            ng.append("T14: 固定の見出しを変えても、項目 1 に見出しを足しても (t) が出ない")
        if not any(x.startswith("(t)") for x in fixed_checks_core(fx_src, fx_doc, dict(fx_ok, ok=False))):
            ng.append("T15: 承認の記録のハッシュ値が中身と違うのに (t) が出ない")
        n16 = parse_doc(fx_doc)
        restore_special_blocks(fx_src, n16)
        if n16["節"][2]["塊"] != [{"固定": "### 1-1 甲"}] or render(n16) != fx_doc:
            ng.append(f"T16: 作った文書を元データに戻すと、固定の印が文に変わる {n16['節'][2]['塊']}")
        n16b = parse_doc(fx_doc.replace("- 手順", "- 手順を変えた"))
        try:
            restore_special_blocks(fx_src, n16b)
            ng.append("T16b: 固定の文が途中で変わったのに止まらない")
        except SystemExit:
            pass
    finally:
        _FIXED_CACHE.pop("ok", None)
        if _saved is not None:
            _FIXED_CACHE["ok"] = _saved
    _env = os.environ.get("CLAUDECODE")
    os.environ["CLAUDECODE"] = "1"
    try:
        if approve_fixed() != 2:
            ng.append("T17: Claude Code の中から --approve-fixed を打っても断らない")
    finally:
        if _env is None:
            os.environ.pop("CLAUDECODE", None)
        else:
            os.environ["CLAUDECODE"] = _env

    # T8 hook を見本で直に呼ぶ（❌ の見本＝exit 2／✅ の見本＝exit 0）★実物の json と worklog の日付で
    if HOOK.exists():
        real_h2, real_g2 = _pass(H2), _pass(G2)
        wd = latest_worklog_date(STATE) or today
        with tempfile.TemporaryDirectory() as td:
            bad = pathlib.Path(td) / "next_step.md"
            good = pathlib.Path(td) / "next_step_good.md"
            bad.write_text(src, encoding="utf-8")
            good_text = refresh_marks(new_next, real_h2, real_g2, today).replace(
                f"### 3-1 いまの状態（{today}", f"### 3-1 いまの状態（{wd}")
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
          "／T4b 印の時刻も照らす"
          "／T11 固定の文のきれいな見本／T12 固定の節への書き足し／T13 2 の注意書き／T14 固定の見出し／T15 承認の記録の改ざん"
          "／T16 固定の印を文に変えない（T16b 途中で変われば止まる）／T17 Claude Code の中から承認を打てない")
    for x in ng:
        print(f"  ❌ {x}")
    total = 27
    print(f"  {'❌' if ng else '✅'} わざと壊して止まるか試すテスト {total - len(ng)}/{total} pass")
    return 1 if ng else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="next_step.md を機械で整えて検査する")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--import", dest="do_import", action="store_true",
                    help="いまの next_step.md から next_step_src.json を作る（最初の1回・作り直しが1文字も違わないときだけ書く）")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--approve-fixed", dest="approve_fixed", action="store_true",
                    help="固定の文の下書き（next_step_fixed.md）を、承認した版として記録する（まこさんが端末で打つ。Claude Code の中からは断る）")
    ap.add_argument("--file", type=pathlib.Path, default=NEXT, help="検査する next_step.md（テスト用）")
    ap.add_argument("--archive", type=pathlib.Path, default=ARCHIVE)
    ap.add_argument("--limit", type=int, default=LIMIT)
    ap.add_argument("--todo-from", dest="todo_from", metavar="セッションの id",
                    help="そのセッションの ToDo の、済んでいない行を、元データの「次のセッションでやること」の表に写す（続けて --write を打つ）")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.approve_fixed:
        return approve_fixed()
    if a.do_import:
        return import_src(a.file)
    if a.todo_from:
        return copy_todo(a.file, a.todo_from)
    if a.write:
        return do_write(a.file, a.archive, a.limit)
    if a.verify:
        return do_verify(a.file, a.limit)
    ap.error("--verify / --write / --selftest のどれかを指定してください")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
