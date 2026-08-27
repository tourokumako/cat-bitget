#!/usr/bin/env python3
"""enforce_design_consistency.py — 設計書の中の食い違いを、書く瞬間に止める（本体）

なぜ要るか（2026-08-27・67回目・まこさん承認「承認した」・設計書 29bb87e592df9053）
  設計書（.claude/state/acceptance.md）の中で、同じ対象について食い違う判定が
  2つ以上 書かれていても、機械は1つも止めなかった（5回目の監査 cp6 の P-1）。

  実例2件（next_step.md §6 の94番の逐語）
    1) 完成の条件5「新しく落ちるものが無い」／条件20「T24② が落ちる」
    2) §1 の24行「時間足＝在る」／18マスの42行「3か所とも止まらない」
  どちらも見つけたのは監査（人が読んだ）で、機械ではない。

止める型（2つだけ）
  A) 同じ名前（T番号・--旗）について、反対の語が2行に分かれて在る
  B) 全部を否定する文（〜が無い／1件も／0件）と、同じ動詞の個別の肯定文が同時に在る

止めないもの（誤報を出さないため）
  引用（>）／囲み（```）／取り消し線（~~）／履歴の行（直す前・旧・…に直した）／
  表の見出しと区切り／動詞をまたぐ組（画面に出すだけ）

限界（正直に）
  ・意味の矛盾は拾えない。拾えるのは上の2つの型だけ。
  ・言葉を変えれば通る（「落ちる」を「❌ になる」と書けば当たらない）。
  ・この hook 自身を書き換えれば無効にできる（git diff には必ず出る）。
  ・最後の関所は まこさんの目。

解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で全廃）。
safety hook: fast-mode の一時無効化の行を入れない。
"""
from __future__ import annotations

import json
import os
import re
import sys

TARGET_NAME = "acceptance.md"

# ── 判定の対（設計書 §7.3 の表・5組）──────────────────────────────
PAIRS: list[tuple[str, str]] = [
    ("落ちる", "落ちない"),
    ("止まる", "止まらない"),
    ("在る", "無い"),
    ("一致", "食い違い"),
    ("pass", "fail"),
]

# ★止める組と、画面に出すだけの組。
#   設計書 §8 の条件3＝承認済みの控えで誤報が出た組は、止める側から外してここへ移す。
BLOCK_PAIRS: list[tuple[str, str]] = [
    ("落ちる", "落ちない"),
    ("止まる", "止まらない"),
    ("pass", "fail"),
]
WARN_PAIRS: list[tuple[str, str]] = [
    ("在る", "無い"),
    ("一致", "食い違い"),
]

# 型B で見る動詞（肯定の形）
TYPE_B_VERBS = ("落ちる", "止まる")

# 履歴の行＝直す前と後を並べて書いているもの（食い違いではない）
HISTORY_WORDS = ("直す前", "直した後", "に直した", "旧 ", "旧版", "以前は", "書き替える前", "直す前は")

# 名前＝T番号（丸数字つきも可）と --旗
_NAME_T = re.compile(r"T\d+[①-⑳㉑-㉟]?")
_NAME_FLAG = re.compile(r"--[a-z0-9][a-z0-9-]*")

# 「0件」「なし」「ゼロ」がすぐ後ろに在る語は、意味が反対になるので数えない
# ★表のセルの区切り（|）と句点をまたがない（2026-08-27・控え74件の実測で足した）＝
#   「本当に止まる ｜ 宣言が無い状態で…」の『無い』は、隣のセルの言葉で、否定ではない。
_ZERO_NEAR = "[^。|\n]{0,8}(?:[0０]\\s*件|なし|ゼロ)"

# 見本（わざと壊した入力）を並べる節＝主張ではないので見ない
SAMPLE_SECTION_WORDS = ("テスト", "番人", "見本", "自己検査")


def _has(line: str, word: str) -> bool:
    """その行に、その語が『主張として』出ているか。

    ★pass / fail は英字なので、fail-closed・fail-open・pass-through のような
      別の言葉の一部を数えない（このリポジトリに実際に多い）。
    ★「食い違い 0件」のように、すぐ後ろに 0件・なし・ゼロ が来る語は数えない
      （＝意味が反対になるため。誤報を出さない側に倒す）。
    """
    if word in ("pass", "fail"):
        if not re.search(r"(?<![A-Za-z-])" + word + r"(?![A-Za-z_-])", line):
            return False
    else:
        if word not in line:
            return False
    if re.search(re.escape(word) + _ZERO_NEAR, line):
        return False
    return True


def strip_noise(text: str) -> list[tuple[int, str, str]]:
    """見る行だけを返す（1始まりの行番号 ／ 中身 ／ その行が属する節の見出し）。

    外すもの＝囲み（```）の中／引用（>）／表の区切り／履歴の行／
      機械が読む目印の行（`<!-- … -->`）。
    取り消し線（~~…~~）は、その部分だけを消す。

    ★節（見出し）を一緒に返す理由（2026-08-27・承認済みの控え74件で実測して足した）
      直す前は、文書のどこにある行どうしでも突き合わせていた。
      そのため「§2 いまどうなっているか」に書いた実例の引用と、
      「§9 テストの見本」の行が食い違いとして出た（誤報）。
      監査 P-1 の言い方も『同じコマンド・同じ対象』＝同じ話の中の食い違い。
      だから、同じ節の中だけを見る。
    """
    out: list[tuple[int, str, str]] = []
    in_fence = False
    section = "（見出しの前）"
    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if s.startswith("#"):
            section = s
            continue
        if any(w in section for w in SAMPLE_SECTION_WORDS):
            continue                              # 見本を並べる節＝主張ではない
        if s.startswith("<!--"):
            continue                              # 機械が読む目印（ARC ほか）＝主張ではない
        if s.startswith(">"):
            continue
        if s.startswith("|") and set(s) <= set("|-: "):
            continue
        if any(w in raw for w in HISTORY_WORDS):
            continue
        line = re.sub(r"~~.*?~~", " ", raw)
        if not line.strip():
            continue
        out.append((i, line, section))
    return out


def names_in(line: str) -> set[str]:
    """その行に出てくる『名前』を集める（T番号・--旗）。"""
    return set(_NAME_T.findall(line)) | set(_NAME_FLAG.findall(line))


def find_type_a(rows: list[tuple[int, str, str]], pairs: list[tuple[str, str]]) -> list[str]:
    """型A＝同じ節の中で、同じ名前について反対の語が2行に分かれて在る。"""
    hits: list[str] = []
    for a, b in pairs:
        side: dict[tuple[str, str], dict[str, tuple[int, str]]] = {}
        for no, line, sec in rows:
            for nm in names_in(line):
                d = side.setdefault((sec, nm), {})
                if _has(line, a):
                    d.setdefault(a, (no, line))
                if _has(line, b):
                    d.setdefault(b, (no, line))
        for key in sorted(side):
            d = side[key]
            if a in d and b in d:
                (n1, l1), (n2, l2) = d[a], d[b]
                if n1 == n2:
                    continue                      # 同じ行に両方＝並べて書いただけ
                hits.append(
                    f"型A｜『{key[1]}』について反対の判定が2つ在ります（節＝{key[0][:30]}）＝"
                    f"{n1}行目「{l1.strip()[:60]}」／{n2}行目「{l2.strip()[:60]}」"
                )
    return hits


def find_type_b(rows: list[tuple[int, str, str]]) -> list[str]:
    """型B＝同じ節の中で、全部を否定する文と、同じ動詞の個別の肯定文が同時に在る。"""
    hits: list[str] = []
    for verb in TYPE_B_VERBS:
        whole: dict[str, tuple[int, str]] = {}
        each: dict[str, tuple[int, str]] = {}
        for no, line, sec in rows:
            if verb not in line:
                continue
            neg = re.search(re.escape(verb) + r"[^。|\n]{0,12}(?:無い|ない|[0０]\s*件|ゼロ)", line)
            nms = names_in(line)
            if neg and not nms:
                whole.setdefault(sec, (no, line))   # 名前を持たない全体の否定
            elif not neg and nms and _has(line, verb):
                each.setdefault(sec, (no, line))    # 名前つきの個別の肯定
        for sec in sorted(set(whole) & set(each)):
            hits.append(
                f"型B｜『{verb}』について、全部の否定と個別の肯定が同時に在ります（節＝{sec[:30]}）＝"
                f"{whole[sec][0]}行目「{whole[sec][1].strip()[:60]}」／"
                f"{each[sec][0]}行目「{each[sec][1].strip()[:60]}」"
            )
    return hits


def judge(text: str) -> tuple[list[str], list[str]]:
    """戻り: (止める理由の一覧, 画面に出すだけの一覧)。"""
    rows = strip_noise(text)
    stop = find_type_a(rows, BLOCK_PAIRS) + find_type_b(rows)
    warn = find_type_a(rows, WARN_PAIRS)
    return stop, warn


# ───────────────────────── hook の入口 ─────────────────────────

def fail(stop: list[str], warn: list[str]) -> None:
    e = sys.stderr
    print("🔒 [設計書の食い違いゲート・safety hook] 設計書の中に、食い違う判定が在ります。", file=e)
    print("   出どころ＝5回目の監査 cp6 の P-1（next_step.md §6 の94番）。", file=e)
    print("", file=e)
    for s in stop:
        print(f"  ❌ {s}", file=e)
    for w in warn:
        print(f"  ⚠️ （止めません・目で見てください）{w}", file=e)
    print("", file=e)
    print("対処: どちらが本当かを決めて、片方を直してから書き直してください。", file=e)
    print("（解除の合言葉はありません＝2026-08-16 に全部 廃止）", file=e)
    sys.exit(2)


def hook_main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        sys.exit(0)                                # 読めない入力では止めない（fail-open）
    if data.get("agent_type"):
        sys.exit(0)                                # サブエージェントは通す
    if data.get("tool_name", "") not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)
    ti = data.get("tool_input") or {}
    fpath = ti.get("file_path", "") or ""
    if os.path.basename(fpath) != TARGET_NAME:
        sys.exit(0)                                # 設計書 以外は見ない

    text = ti.get("content") or ti.get("new_string") or ""
    if not text and os.path.exists(fpath):
        try:
            with open(fpath, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            sys.exit(0)
    if not text.strip():
        sys.exit(0)

    stop, warn = judge(text)
    if stop:
        fail(stop, warn)
    for w in warn:
        print(f"⚠️ [設計書の食い違いゲート] 止めません・目で見てください: {w}", file=sys.stderr)
    sys.exit(0)


# ──────────── 番人（わざと壊して、止まることを確かめる）────────────

def selftest() -> None:
    head = "# acceptance.md\n\n## §1 完成の条件\n\n"
    cases: list[tuple[str, str, bool]] = [
        ("1 同じ T24② に「落ちる」と「落ちない」",
         head + "- T24② が落ちる\n- T24② は落ちない\n", True),
        ("2 「新しく落ちるものが無い」＋「T24② が落ちる」（実例1）",
         head + "- 新しく落ちるものが無い\n- T24② が落ちる\n", True),
        ("3 履歴の行は止まらない",
         head + "- 直す前は T24② が落ちる\n- T24② は落ちない\n", False),
        ("4 引用の中は止まらない",
         head + "> T24② が落ちる\n> T24② は落ちない\n", False),
        ("5 囲みの中は止まらない",
         head + "```\nT24② が落ちる\nT24② は落ちない\n```\n", False),
        ("6 取り消し線の中は止まらない",
         head + "- ~~T24② が落ちる~~\n- T24② は落ちない\n", False),
        ("7 名前が違えば止まらない",
         head + "- T24② が落ちる\n- T25 は落ちない\n", False),
        ("8 動詞をまたぐ組は止めず、画面に出す（実例2）",
         head + "- --gate-matrix の検査は在る\n- --gate-matrix は3か所とも止まらない\n"
                "- --gate-matrix の検査は無い\n", False),
        ("9 fail-closed は fail と数えない",
         head + "- --lint は fail-closed で作る\n- --lint は pass する\n", False),
        ("10 「食い違い 0件」は 食い違い と数えない",
         head + "- --identity は一致\n- --identity の食い違い 0件\n", False),
        ("11 節が違えば止まらない",
         "# a\n\n## §2 いま\n\n- T24② が落ちる\n\n## §5 これから\n\n- T24② は落ちない\n", False),
        ("12 見本を並べる節は見ない",
         "# a\n\n## §9 わざと壊して止まるか試すテスト\n\n"
         "- T24② が落ちる\n- T24② は落ちない\n", False),
        ("13 表のセルをまたぐ「無い」を否定と読まない",
         head + "| 3 | わざと壊すと止まる | --selftest で確かめる |\n"
                "| 5 | 本当に止まる | 宣言が無い状態で書こうとする |\n", False),
    ]
    ng = 0
    for name, body, want_stop in cases:
        stop, warn = judge(body)
        good = bool(stop) == want_stop
        extra = ""
        if name.startswith("8 "):
            good = good and bool(warn)             # 画面に出ることまで確かめる
            extra = f"（画面に出た件数 {len(warn)}）"
        print(f"  {'✅' if good else '❌'} {name}{extra}"
              + ("" if good else f"   ← 止める理由: {stop} ／ 出すだけ: {warn}"))
        if not good:
            ng += 1
    print(f"\n[enforce_design_consistency] {len(cases) - ng}/{len(cases)} pass")
    sys.exit(1 if ng else 0)


def scan_archive(dirpath: str) -> None:
    """承認済みの控えを全部 通して、誤報の件数を出す（設計書 §8 の条件3）。"""
    names = sorted(n for n in os.listdir(dirpath) if n.endswith(".md"))
    hit = 0
    for n in names:
        with open(os.path.join(dirpath, n), encoding="utf-8", errors="ignore") as f:
            stop, _warn = judge(f.read())
        if stop:
            hit += 1
            print(f"  ❌ {n}")
            for s in stop:
                print(f"      {s}")
    print(f"\n[控えの走査] {len(names)} 件中 止まる {hit} 件")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    if "--scan" in sys.argv:
        scan_archive(sys.argv[sys.argv.index("--scan") + 1])
        sys.exit(0)
    hook_main()
