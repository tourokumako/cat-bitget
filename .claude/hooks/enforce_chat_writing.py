#!/usr/bin/env python3
# enforce_chat_writing.py — CC がチャットに書いた文章の「形」を機械で検査する（Stop hook・2026-08-18 新設）
#
# なぜ作ったか:
#   まこさんの逐語（2026-08-18）＝「チャットに出すCCの文章が私に伝わらないことがほとんどで、
#   会話が進まないので、それを改善したい」「強制できないの？」。
#   文章の決まり（.claude/rules/chat_writing_rules.md）は 2026-07-16 に作ったが、
#   そのあと説明し直しを求められた回数は18件だった（数え方と一覧は session_worklog_20260818.md §3）。
#   ＝決まりを文章で足すやり方は効かなかった。だから機械の検査にする。
#
# なぜ Stop hook で作れるか（2026-08-18 に実測した）:
#   CC のチャット本文は ~/.claude/projects/<プロジェクト>/<セッションID>.jsonl に書き出されている。
#   実測＝いまの会話のファイルは194行あり、そのうち75行が CC の発言だった。
#   直前のチャット本文（488文字）を機械で取り出せることを確かめた。
#   ＝ターンを閉じる瞬間に走る Stop hook が、その本文を読んで検査できる。
#
# 検査（3件）:
#   1. 名前だけを並べた行が無いか（中黒・プラス・矢印が合計3個以上、しかも句点が0個の行）。
#   2. 1つの文が長すぎないか（既定 120字）。
#   3. 長い段落を箇条書きにしているか（既定 300字を超える段落に箇条書きが無ければ止める）。
#      ＝まこさん指示 2026-08-18「文章が長くなる場合は、箇条書きにしてほしい」。
#
# ★2026-08-18 に外した検査（まこさん指摘・逐語「すでに会話が噛み合ってないんだけど。
#   決めてほしいことって会話のやりとりで毎回発生する？」）:
#   「返信の先頭に『決めてほしいこと』が書いてあるか」を見る検査を作ったが、外した。
#   理由＝決めてほしいことは毎回 発生しない。質問に答えるだけのやり取りのほうが多い。
#   CC が会話を報告の型に押し込めていた。
#
# ★作らなかった検査（まこさん指示 2026-08-18・逐語）:
#   「３，使ってはいけない言い方が出ていないか。→会話が表示できるようになるまで時間かかりそうなので、
#    やめたほうがいいとおもう」。＝使ってはいけない言い方の一覧は、機械では見ない。
#
# 検査しない行:
#   ``` で囲んだ中（ファイルの全文を貼るときに使う）／表の行（| で始まる）／見出し（# で始まる）／
#   引用（> で始まる＝まこさんの逐語を写すため）。
#
# 止める回数の上限:
#   1回のやり取りにつき2回まで。理由＝まこさんが「会話が表示できるようになるまで時間がかかる」ことを
#   心配しているため。3回目からは通す（そのときは まこさんの目が最後の関所になる）。
#
# 限界（正直に）:
#   中身が薄いことは機械には分からない。2番の検査は「名前の羅列らしい形」を見ているだけで、
#   その行に中身があるかは見ていない。CC が形だけ整えて意味の無い行を並べることはできる。
#   最後の関所はまこさんの目である。

import glob
import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
STATE = os.path.join(ROOT, ".claude", "state")
COUNT = os.path.join(STATE, "chat_check_blocks.json")
PROJECTS = os.path.expanduser("~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget")

# ★長さの2つは、わざとゆるくしてある（まこさん指示 2026-08-18・逐語
#   「文章の長さはそこまで厳密にせずともいい。それよりも以下が重要」）。
#   文化庁「公用文作成の考え方」の解説44ページの目安は「50〜60字ほど」だが、そこまで厳しくしない。
#   ＝形がひどく崩れたときだけ止まる歯止めとして置く。
MAX_SENTENCE = 120      # 1つの文の上限（字）
MAX_PARAGRAPH = 300     # 箇条書きにせずに書いてよい段落の上限（字）
MAX_BLOCKS = 2          # 1回のやり取りで止める回数の上限
HEAD_WORDS = ("決めてほしいこと", "決めることはありません")
HEAD_LINES = 3          # 先頭から何行目までに上の言葉が在ればよいか


# ---------------- 文章の検査（ここだけが判定の本体） ----------------

def strip_markdown(s):
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)   # リンクは表示される文字だけ残す
    s = s.replace("**", "").replace("`", "")
    return s


def target_lines(text):
    """検査する行だけを返す。（行番号, 中身）の組。"""
    out, in_code = [], False
    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not s or s.startswith("|") or s.startswith("#") or s.startswith(">"):
            continue
        if set(s) <= set("-|: "):        # 表の区切り線
            continue
        out.append((i, strip_markdown(s)))
    return out


def check_head(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for l in lines[:HEAD_LINES]:
        if any(w in l for w in HEAD_WORDS):
            return None
    return (f"返信の先頭{HEAD_LINES}行に「決めてほしいこと」も「決めることはありません」も無い。"
            f"まこさんが最初の数行だけで何を判断すればよいか分かるように、先頭に書く")


def check_name_list(text):
    for no, s in target_lines(text):
        marks = s.count("・") + s.count("＋") + s.count("→") + s.count("+")
        if marks >= 3 and s.count("。") == 0:
            return (f"{no}行目が「名前を並べただけの行」になっている（中黒・プラス・矢印が {marks} 個、句点が0個）。"
                    f"1件を1行にして、その行に「何をしたか」と「どうなったか」を書く。\n"
                    f"    いまの行: {s[:80]}")
    return None


def check_sentence(text):
    for no, s in target_lines(text):
        s2 = re.sub(r"^[-*\d]+[.、)]?\s*", "", s)     # 箇条書きの行頭の印を外す
        for sent in re.split(r"(?<=[。！？])", s2):
            sent = sent.strip()
            if len(sent) > MAX_SENTENCE:
                return (f"{no}行目に {len(sent)} 字の文がある（上限 {MAX_SENTENCE} 字）。文を分ける。\n"
                        f"    いまの文: {sent[:80]}…")
    return None


def check_paragraph(text):
    """空行で区切られたかたまりのうち、箇条書きでも表でもないものが長すぎたら止める。"""
    in_code = False
    block, start = [], 0

    def judge(block, start):
        if not block:
            return None
        body = "".join(strip_markdown(b) for b in block)
        if len(body) > MAX_PARAGRAPH:
            return (f"{start}行目から始まる段落が {len(body)} 字ある（上限 {MAX_PARAGRAPH} 字）。"
                    f"箇条書きに分ける（まこさん指示 2026-08-18）。")
        return None

    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if s.startswith("```"):
            in_code = not in_code
            block, start = [], 0
            continue
        if in_code:
            continue
        skip = (not s) or s.startswith("|") or s.startswith("#") or s.startswith(">") \
            or re.match(r"^[-*]\s", s) or re.match(r"^\d+[.、)]\s", s)
        if skip:
            bad = judge(block, start)
            if bad:
                return bad
            block, start = [], 0
            continue
        if not block:
            start = i
        block.append(s)
    return judge(block, start)


# ---------------- 検査4＝結論を先頭に置く（形だけ・2026-08-18 まこさん OK） ----------------

PREAMBLE_NG = ("まず", "経緯", "背景", "前提", "はじめに", "最初に")
CONCLUSION_WORDS = ("結論", "答え", "やったこと", "できたこと", "結果", "推奨", "提案", "立場",
                    "直しました", "作りました", "終わりました")
MAX_PREAMBLE = 200      # 1つ目の見出しの前に書いてよい字数


def visible_lines(text):
    """``` の中を外した行を返す（引用と表と見出しは残す）。"""
    out, in_code = [], False
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        out.append(s)
    return out


def check_conclusion_first(text):
    lines = visible_lines(text)
    body = [l for l in lines if l]
    if not body:
        return None

    first = re.sub(r"^[*#\s]+", "", strip_markdown(body[0]))
    if first.startswith(PREAMBLE_NG):
        return (f"返信の書き出しが「{first[:12]}…」で始まっている。**前置きから書き始めない。**"
                f"結論・立場・提案を先頭に置く（文化庁の決まり5・BLUF）")

    heads = [(i, l) for i, l in enumerate(lines) if l.startswith("#")]
    if not heads:
        return None                       # 見出しの無い短い返信は、書き出しの検査だけで通す

    i0, h0 = heads[0]
    before = "".join(l for l in lines[:i0] if l and not l.startswith(("|", ">")))
    title = strip_markdown(re.sub(r"^#+\s*", "", h0))

    if len(before) > MAX_PREAMBLE:
        return (f"1つ目の見出しの前に {len(before)} 字 書いている（上限 {MAX_PREAMBLE} 字）。"
                f"結論を短く置いてから、見出しに入る")
    if not before and not any(w in title for w in CONCLUSION_WORDS):
        return (f"1つ目の見出しが「{title[:20]}」で、その前に結論が1文も無い。"
                f"結論を先頭に置く。見出しを結論の言葉にするか、見出しの前に結論を1文 書く")
    return None


# ---------------- 検査5＝書き換えたファイルを、報告に全部 書いたか ----------------

# 機械の印や作業用のファイルは、報告の対象にしない（中身の作業ではないため）
SKIP_FILES = ("session_todo.md", "session_todo_posted", "session_todo_shown",
              "interpretation.md", "interpretation_posted", "chat_check_blocks.json",
              "read_log.txt", "flow_declaration.md", "goal_block.md")


def check_reported_files(text, changed):
    if not changed:
        return None
    missing = [f for f in changed if f not in SKIP_FILES and f not in text]
    if missing:
        return ("このターンで書き換えたのに、返信に名前が出ていないファイルがある: "
                + "、".join(missing)
                + "。**報告の中身を減らさない**（まこさん 2026-08-18「私はすべての作業内容を把握したい」）")
    return None


# ---------------- 検査6＝言い換えの表に載っている語を使っていないか（2026-08-18 新設） ----------------
#
# なぜ足したか:
#   まこさんの言葉（2026-08-18）＝「このCCしかわからないよな用語のせいで毎回今回のように時間が
#   無駄にされてきてるんだけど。本当にどうにかならないのか？これ以上同じことを繰り返したくない」。
#   1〜5番の検査は文の長さと並び順だけを見ていて、語を1つも見ていなかった。だから効かなかった。
#
# 表の在りか: .claude/rules/word_replacements.md
#   「使わない語 | これから書く言い方」の2列の表。行が増えるたびに、この検査も自動で増える。
#   「そのまま使ってよい語」の節に載っている語は、含んでいても止めない（例＝機械学習）。
#
# 限界（正直に）:
#   私がこれから新しく作る語は、初回だけ通る。機械には、初めて見る語が伝わるか分からない。
#   効くのは2回目からで、まこさんの「同じことを繰り返したくない」に直接 効く。

WORDS_FILE = os.path.join(ROOT, ".claude", "rules", "word_replacements.md")


def load_word_table(path=None):
    """（使わない語 → これから書く言い方）の一覧と、そのまま使ってよい語の一覧を返す。"""
    path = path or WORDS_FILE
    pairs, allow, in_allow, in_skip = [], [], False, False
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except Exception:
        return [], []
    for raw in lines:
        s = raw.strip()
        if s.startswith("#"):
            # ★大見出し（# と ##）だけが区分けを切り替える。
            #   小見出し（###）では切り替えない＝2026-08-18 にここで取りこぼした。
            level = len(s) - len(s.lstrip("#"))
            if level <= 2:
                in_allow = "そのまま使ってよい語" in s
            # ★短い語（線・器・点・取る・引く・位置）は、別の語の一部にも当たる。
            #   プログラムに見せると正しい文まで止めるので、この節の行は読み飛ばす。
            in_skip = "プログラムでは見ない" in s
            continue
        if not s.startswith("|") or in_skip:
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        left, right = cells[0], cells[1]
        if not left or set(left) <= set("-: "):
            continue
        if left in ("使わない語", "語", "私が使っていた語"):
            continue
        if in_allow:
            allow.append(left)
            continue
        left = re.sub(r"（[^）]*）", "", left).strip()
        for w in re.split(r"[／/]", left):
            w = w.strip()
            if w:
                pairs.append((w, right))
    return pairs, allow


def check_words(text, path=None):
    pairs, allow = load_word_table(path)
    if not pairs:
        return None
    for no, s in target_lines(text):
        for w, right in pairs:
            if w not in s:
                continue
            # そのまま使ってよい語の一部なら見逃す（例＝「機械学習」の中の「機械」）
            if any(w in a and a in s for a in allow):
                continue
            return (f"{no}行目に「{w}」を使っている。**この語は使わないと決めている。**"
                    f"代わりに「{right}」と書く（.claude/rules/word_replacements.md）。\n"
                    f"    いまの行: {s[:80]}")
    return None


def check_text(text, changed=None):
    # ★check_head（先頭に「決めてほしいこと」を求める検査）は 2026-08-18 に外した。
    #   まこさんの指摘＝決めてほしいことは毎回 発生しない。関数は残すが、判定には使わない。
    for f in (check_words, check_name_list, check_sentence, check_paragraph, check_conclusion_first):
        bad = f(text)
        if bad:
            return bad
    return check_reported_files(text, changed)


# ---------------- 会話のファイルから、CC の直前の本文を取り出す ----------------

def last_chat_text(path, want_files=False):
    """（CC の直前のチャット本文, 直前のまこさんの発言の id[, 書き換えたファイル名]）を返す。"""
    try:
        rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    except Exception:
        return None, None

    def is_user_say(r):
        if r.get("type") != "user":
            return False
        c = (r.get("message") or {}).get("content")
        if isinstance(c, str):
            return bool(c.strip())
        if isinstance(c, list):
            return any(isinstance(b, dict) and b.get("type") == "text" for b in c)
        return False

    last_user = -1
    for i, r in enumerate(rows):
        if is_user_say(r):
            last_user = i
    uid = rows[last_user].get("uuid") if last_user >= 0 else None

    text, files = None, []
    for r in rows[last_user + 1:]:
        if r.get("type") != "assistant":
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text" and b.get("text", "").strip():
                text = b["text"]
            if b.get("type") == "tool_use" and b.get("name") in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                fp = (b.get("input") or {}).get("file_path") or ""
                if fp:
                    n = os.path.basename(fp)
                    if n not in files:
                        files.append(n)
    if want_files:
        return text, uid, files
    return text, uid


def blocked_count(uid):
    try:
        d = json.load(open(COUNT, encoding="utf-8"))
        return d.get("n", 0) if d.get("uuid") == uid else 0
    except Exception:
        return 0


def record_block(uid, n):
    try:
        with open(COUNT, "w", encoding="utf-8") as f:
            json.dump({"uuid": uid, "n": n}, f)
    except Exception:
        pass


# ---------------- hook の入口 ----------------

def hook_main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        sys.exit(0)                      # 読めない入力では止めない

    path = data.get("transcript_path") or ""
    if not path or not os.path.exists(path):
        files = sorted(glob.glob(os.path.join(PROJECTS, "*.jsonl")), key=os.path.getmtime)
        if not files:
            sys.exit(0)
        path = files[-1]

    text, uid, changed = last_chat_text(path, want_files=True)
    if not text:
        sys.exit(0)                      # 本文が無いターン（道具だけ動かした）は対象外

    bad = check_text(text, changed)
    if not bad:
        sys.exit(0)

    n = blocked_count(uid)
    if n >= MAX_BLOCKS:
        print(f"⚠️ [チャット文章の検査] {n} 回 止めたので、今回は通します。まこさんの目で見てください。\n"
              f"   直らなかった点: {bad}", file=sys.stderr)
        sys.exit(0)

    record_block(uid, n + 1)
    e = sys.stderr
    print("🔒 [チャット文章の検査・Stop hook] いまの返信は、まこさんに伝わる形になっていません。", file=e)
    print("   まこさん指示 2026-08-18「チャットに出すCCの文章が私に伝わらない」「強制できないの？」。", file=e)
    print("", file=e)
    print(f"直すところ: {bad}", file=e)
    print("", file=e)
    print("対処: 同じ内容を減らさずに、形だけ直して、もう一度チャットに書く。", file=e)
    print("  ・報告の中身は減らさない（まこさん 2026-08-18「私はすべての作業内容を把握したい」）。", file=e)
    print("  ・1件を1行以上で書く。その行に「何をしたか」と「どうなったか」を入れる。", file=e)
    print("  ・長くなるときは箇条書きにする。", file=e)
    print(f"（止めるのは1回のやり取りにつき {MAX_BLOCKS} 回まで。それ以上は通します）", file=e)
    sys.exit(2)


# ---------------- 番人（わざと壊して、止まることを確かめる） ----------------

def selftest():
    ok_head = ""
    cases = [
        ("正しい文章は通る",
         ok_head + "- engine_tuner の乱数をプログラムで数えました。57件ありました。\n- 法則の表を読む回数は0回でした。\n",
         None),
        ("★言い換えの表に載っている語を使うと止まる",
         "直しました。\n\n- 乱数を機械で数えました。57件でした。\n",
         "この語は使わないと決めている"),
        ("言い換えた言い方なら通る",
         "直しました。\n\n- 乱数をプログラムで数えました。57件でした。\n",
         None),
        ("そのまま使ってよい語（機械学習）は止まらない",
         "直しました。\n\n- 機械学習は使っていません。\n",
         None),
        ("★先頭に「決めてほしいこと」が無くても通る（2026-08-18 に検査を外した）",
         "報告します。\n\n- 乱数を数えました。57件でした。\n",
         None),
        ("質問に答えるだけの短い返信も通る",
         "いいえ、毎回は発生しません。質問に答えるだけのやり取りのほうが多いです。\n",
         None),
        ("名前だけを並べた行は止まる",
         ok_head + "同じだった数字＝乱数の呼び出し 57・法則の表を読む回数 0・表2つのハッシュ値・上限5つ「無制限」\n",
         "名前を並べただけ"),
        ("長い文は止まる",
         ok_head + "私は" + "あ" * 130 + "。\n",
         "字の文がある"),
        ("長い段落は止まる（箇条書きにしていない）",
         ok_head + "い" * 90 + "。\n" + "う" * 90 + "。\n" + "え" * 90 + "。\n" + "お" * 90 + "。\n",
         "箇条書きに分ける"),
        ("同じ長さでも箇条書きなら通る",
         ok_head + "- " + "い" * 90 + "。\n- " + "う" * 90 + "。\n- " + "え" * 90 + "。\n- " + "お" * 90 + "。\n",
         None),
        ("``` の中は検査しない（ファイルの全文を貼れる）",
         ok_head + "```\n名前A・名前B・名前C・名前D\n```\n",
         None),
        ("表の行は検査しない",
         ok_head + "| 名前A・名前B・名前C・名前D | x | y | z |\n",
         None),
        ("まこさんの逐語（引用）は検査しない",
         ok_head + "> 乱数の呼び出し 57・法則の表を読む回数 0・表2つの指紋・上限5つ\n",
         None),
        ("★前置きから書き始めると止まる（結論を先頭に）",
         "まず、いままでの経緯を書きます。\n\n## やったこと\n\n- 直しました。\n",
         "前置きから書き始めない"),
        ("★1つ目の見出しが結論でなく、その前に結論が無いと止まる",
         "## 調べたこと\n\n- ログを数えました。19件でした。\n",
         "結論を先頭に置く"),
        ("見出しの前に結論を1文 置けば通る",
         "直しました。中身を書きます。\n\n## 調べたこと\n\n- ログを数えました。19件でした。\n",
         None),
        ("1つ目の見出しが結論の言葉なら、前置きが無くても通る",
         "## 結論\n\n- ログを数えました。19件でした。\n",
         None),
    ]

    ng = 0
    for name, text, want in cases:
        got = check_text(text)
        good = (got is None) if want is None else (got is not None and want in got)
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た理由: {got}"))
        if not good:
            ng += 1

    extra = [
        ("★書き換えたファイルを報告に書かないと止まる",
         "直しました。\n\n## やったこと\n\n- 検査を1つ足しました。\n",
         ["engine_tuner_gen.py"], "名前が出ていないファイル"),
        ("書き換えたファイルを書けば通る",
         "直しました。\n\n## やったこと\n\n- engine_tuner_gen.py に検査を1つ足しました。\n",
         ["engine_tuner_gen.py"], None),
        ("機械の印のファイル（ToDo など）は報告しなくてよい",
         "直しました。\n\n## やったこと\n\n- 検査を1つ足しました。\n",
         ["session_todo.md", "interpretation.md"], None),
    ]
    for name, text, changed, want in extra:
        got = check_text(text, changed)
        good = (got is None) if want is None else (got is not None and want in got)
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た理由: {got}"))
        if not good:
            ng += 1

    total = len(cases) + len(extra)
    print(f"\n番人: {total - ng}/{total} pass")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    hook_main()
