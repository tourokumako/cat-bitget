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
#
# ★2026-08-20 の直し3件（まこさん承認・逐語「すべてOK」・44回目に6回 連続で止まった問題の対応）:
#   ①違反を全部 一度に出す。直す前は最初の1件で止まる作りだった＝CC が1件 直すたびに再送し、
#     次の違反でまた止まった（「当たるまで生成し続ける」に見えた挙動の正体）。
#   ②回数の記録の穴を塞いだ。この hook の差し戻しは、会話の記録に type=user の文字列
#     「Stop hook feedback:…」として残る（44回目の記録 749de1c4… の559〜582行で実測）。
#     直す前は それを「まこさんの発言」に数えて鍵の uuid が毎回 変わり、回数が0に戻っていた
#     ＝上限2回が効かず6回 止まった。いまは差し戻しの行を発言に数えない。
#   ③「--check 下書きファイル」の口を足した。CC は返信を出す前に、下書きをこの検査へ通す
#     ＝出してから止められる運任せをやめ、まこさんの画面に同じ長文が並ぶのを防ぐ。

import glob
import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
STATE = os.path.join(ROOT, ".claude", "state")
COUNT = os.path.join(STATE, "chat_check_blocks.json")
LAST = os.path.join(STATE, "chat_check_last.json")       # ★2026-08-26 新設＝前の返信の違反の型
DRAFT = os.path.join(STATE, "chat_draft.md")             # ★2026-08-26 新設＝長い返信の下書き
PROJECTS = os.path.expanduser("~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget")

# ★長さの2つは、わざとゆるくしてある（まこさん指示 2026-08-18・逐語
#   「文章の長さはそこまで厳密にせずともいい。それよりも以下が重要」）。
#   文化庁「公用文作成の考え方」の解説44ページの目安は「50〜60字ほど」だが、そこまで厳しくしない。
#   ＝形がひどく崩れたときだけ止まる歯止めとして置く。
MAX_SENTENCE = 120      # 1つの文の上限（字）
MAX_PARAGRAPH = 300     # 箇条書きにせずに書いてよい段落の上限（字）
MAX_BLOCKS = 1          # 1回のやり取りで止める回数の上限（★2026-08-26 に 2 → 1）

# ★2026-08-26 新設（まこさん指示・逐語「同じ文章を連続で出すのをやめてほしいので、この修正をやる」）
#   違反を2種類に分ける。
#     重い＝報告の中身が減っている（書き換えたファイルの名前が返信に出ていない）。1回目から止める。
#     軽い＝形だけ（文の長さ・段落の長さ・名前の羅列・結論の位置）。1回目は止めず、記録して通す。
#           次の返信でも同じ型が出たら止める（＝直していない）。
KIND_HEAVY = "報告漏れ"
# ★2026-09-10 新設（まこさん指示「入れて良い」）＝「やること」の節の書き方。
#   1回目から止める＝まこさんの逐語「毎回毎回毎回毎回言ってるけど、今後もいちいち言い続けないと直らないのか？」。
KIND_TODO = "やることの書き方"
KIND_LIGHT = ("名前の羅列", "文が長い", "段落が長い", "結論の位置")
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
    """★2026-08-20 直し①＝1件で止めず、全部の行を返す（一覧で出す）。"""
    out = []
    for no, s in target_lines(text):
        marks = s.count("・") + s.count("＋") + s.count("→") + s.count("+")
        if marks >= 3 and s.count("。") == 0:
            out.append(f"{no}行目が「名前を並べただけの行」になっている（中黒・プラス・矢印が {marks} 個、句点が0個）。"
                       f"1件を1行にして、その行に「何をしたか」と「どうなったか」を書く。\n"
                       f"    いまの行: {s[:80]}")
    return out


def check_sentence(text):
    """★2026-08-20 直し①＝長すぎる文を全部 返す。"""
    out = []
    for no, s in target_lines(text):
        s2 = re.sub(r"^[-*\d]+[.、)]?\s*", "", s)     # 箇条書きの行頭の印を外す
        for sent in re.split(r"(?<=[。！？])", s2):
            sent = sent.strip()
            if len(sent) > MAX_SENTENCE:
                out.append(f"{no}行目に {len(sent)} 字の文がある（上限 {MAX_SENTENCE} 字）。文を分ける。\n"
                           f"    いまの文: {sent[:80]}…")
    return out


def check_paragraph(text):
    """空行で区切られたかたまりのうち、箇条書きでも表でもないものが長すぎたら止める。
    ★2026-08-20 直し①＝長すぎる段落を全部 返す。"""
    in_code = False
    block, start, out = [], 0, []

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
                out.append(bad)
            block, start = [], 0
            continue
        if not block:
            start = i
        block.append(s)
    bad = judge(block, start)
    if bad:
        out.append(bad)
    return out


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


# ---------------- 検査7＝「やること」の節が、読んで分かる形か（2026-09-10 新設） ----------------
#
# なぜ足したか（まこさんの指摘 2026-09-10・逐語）:
#   「次にやること（順番）の文章がわからない。日本語の文法に則って、わかりやすい文章に書き直せる？
#     これ、毎回毎回毎回毎回言ってるけど、今後もいちいち言い続けないと直らないのか？」
#   そのとき私が書いた4行＝「C-38 を『拾い間違い』に割り当てる」「設計書に §2.2-2 の C を入れる」など。
#   主語が無く、記号（④・⑥）だけで指し先を書き、なぜそうするかも書いていなかった。
#
# ★1〜6番の検査は、この4行を1つも捕まえなかった。
#   理由＝短くて（120字未満）、中黒も矢印も並んでいないから。
#   ＝短く書くほど検査を通り、短く書くほど主語と目的語が消える。
#
# 見るところ（3つ・「やること」の見出しを持つ節だけ）:
#   1. 主語＝その節に「私は」「私が」が1回も無ければ止める（誰がやるのかが書かれていない）。
#   2. 記号＝丸数字（①〜⑳）を使っていたら止める。何の①か分からないため、言葉で書く。
#   3. 理由＝「なぜ」「理由」「ため」が1回も無ければ止める（そうする理由が書かれていない）。
#
# 限界（正直に）:
#   「私は」という言葉が在るかどうかしか見ない。中身が本当に伝わるかは機械には分からない。
#   最後の関所は まこさんの目である。

TODO_HEADS = ("やること", "次の一手", "これからやる")
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
SUBJECT_WORDS = ("私は", "私が")
REASON_WORDS = ("なぜ", "理由", "ため")


def todo_sections(text):
    """「やること」の見出しを持つ節を返す。（見出しの行番号, 見出し, 中身の行の一覧）の組。"""
    lines = visible_lines(text)
    out, cur, head, head_no, level = [], [], None, 0, 0
    for i, s in enumerate(lines, 1):
        if s.startswith("#"):
            lv = len(s) - len(s.lstrip("#"))
            title = strip_markdown(re.sub(r"^#+\s*", "", s))
            if head is not None and lv <= level:
                out.append((head_no, head, cur))
                cur, head = [], None
            if any(w in title for w in TODO_HEADS):
                head, head_no, level, cur = title, i, lv, []
            continue
        if head is not None and s:
            cur.append(s)
    if head is not None:
        out.append((head_no, head, cur))
    return out


def check_todo_section(text):
    """「やること」の節に、主語・言葉での指し先・理由が在るかを見る。"""
    out = []
    for no, head, body in todo_sections(text):
        if not body:
            continue
        joined = strip_markdown("".join(body))
        if not any(w in joined for w in SUBJECT_WORDS):
            out.append(f"{no}行目の「{head[:20]}」の節に、主語（「私は」「私が」）が1つも無い。"
                       f"1件ずつ「私は ◯◯ を ◯◯ します」の形で書く（誰が何をするのかを書く）。")
        marks = [c for c in joined if c in CIRCLED]
        if marks:
            out.append(f"{no}行目の「{head[:20]}」の節で、丸数字（{''.join(sorted(set(marks)))}）を指し先に使っている。"
                       f"何の番号か分からないので、言葉で書く（例＝「④設計の中身」→「設計書の『設計の中身』の節」）。")
        if not any(w in joined for w in REASON_WORDS):
            out.append(f"{no}行目の「{head[:20]}」の節に、なぜそうするかが1行も無い。"
                       f"1件ずつ「なぜそうするか」を書く。")
    return out


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
    """★2026-08-20 直し①＝使っている語を全部 返す（同じ語は1回だけ）。"""
    pairs, allow = load_word_table(path)
    if not pairs:
        return []
    out, seen = [], set()
    for no, s in target_lines(text):
        for w, right in pairs:
            if w not in s or w in seen:
                continue
            # そのまま使ってよい語の一部なら見逃す（例＝「機械学習」の中の「機械」）
            if any(w in a and a in s for a in allow):
                continue
            seen.add(w)
            out.append(f"{no}行目に「{w}」を使っている。**この語は使わないと決めている。**"
                       f"代わりに「{right}」と書く（.claude/rules/word_replacements.md）。\n"
                       f"    いまの行: {s[:80]}")
    return out


def check_detail(text, changed=None):
    """（画面に出す文字列, 違反の型の集合）を返す（★2026-08-26 新設）。

    型の名前は KIND_HEAVY・KIND_LIGHT のとおり。止めるかどうかの判定（gate_decision）が これを使う。
    ★判定の中身は check_text と同じ関数を呼ぶ＝二重に作らない（検査がずれない）。
    """
    kinds = set()
    if check_name_list(text):
        kinds.add("名前の羅列")
    if check_sentence(text):
        kinds.add("文が長い")
    if check_paragraph(text):
        kinds.add("段落が長い")
    if check_todo_section(text):                 # ★2026-09-10 新設
        kinds.add(KIND_TODO)
    if check_conclusion_first(text):
        kinds.add("結論の位置")
    if check_reported_files(text, changed):
        kinds.add(KIND_HEAVY)
    return check_text(text, changed), kinds


def gate_decision(kinds, last_kinds, blocked_n):
    """止めるか通すかを決める（★2026-08-26 新設・番人がここを直に試す）。

    戻り: ("block", 理由) か ("pass", 理由)
      ・違反が無い                      → pass
      ・止めた回数が上限に達している      → pass（まこさんの目が最後の関所）
      ・重い違反（報告漏れ）が在る        → block
      ・軽い違反だけで、前の返信と同じ型   → block（直していない）
      ・軽い違反だけで、前の返信に無い型   → pass（1回目は通す＝同じ文章を続けて出さない）
    """
    if not kinds:
        return "pass", "違反なし"
    if blocked_n >= MAX_BLOCKS:
        return "pass", f"すでに {blocked_n} 回 止めた"
    if KIND_HEAVY in kinds:
        return "block", "報告の中身が減っている"
    if KIND_TODO in kinds:                       # ★2026-09-10 新設＝1回目から止める
        return "block", "「やること」の節に、主語・言葉での指し先・理由のどれかが無い"
    same = kinds & set(last_kinds or [])
    if same:
        return "block", "前の返信と同じ型を繰り返している: " + "・".join(sorted(same))
    return "pass", "形だけの違反の1回目（記録して次の返信で見る）"


def check_text(text, changed=None):
    # ★check_head（先頭に「決めてほしいこと」を求める検査）は 2026-08-18 に外した。
    #   まこさんの指摘＝決めてほしいことは毎回 発生しない。関数は残すが、判定には使わない。
    # ★2026-08-20 直し①＝違反を1件ずつ出すのをやめ、全部を一度に出す。
    #   直す前は最初の1件で止まる作りで、CC が1件 直すたびに再送して6回 止まった（44回目）。
    found = []
    # ★2026-08-24（57回目）＝語の検査を外した。まこさん指示（逐語）「文字チェックははずせ。使えない」。
    #   なぜ外したか（実測）＝1回のやり取りで4回 止まり、同じ文章が4回 まこさんの画面に出た。
    #   4回とも同じ語（漢字1文字）で止まった。その語は「目◯し」「矢◯し」など別の語の一部に入る。
    #   しかも word_replacements.md の「代わりにこう書く」の欄そのものに、その語が入っている
    #   ＝検査が示した言い換えのとおりに書いても、また止まる（出口が無い）。
    #   ★同じ型の注意は word_replacements.md の「★プログラムでは見ない語」に既に書いてあった
    #   （「点」は「時点」「観点」の中にも入る）。短い語をプログラムに見せると正しい文まで止める。
    #   ★関数 check_words と load_word_table は消していない（まこさんが戻すと決めたら1行で戻せる）。
    #   ★word_replacements.md の表も消していない＝私が守る決まりとしては残る。
    # found += check_words(text)
    found += check_name_list(text)
    found += check_sentence(text)
    found += check_paragraph(text)
    found += check_todo_section(text)            # ★2026-09-10 新設（検査7）
    bad = check_conclusion_first(text)
    if bad:
        found.append(bad)
    bad = check_reported_files(text, changed)
    if bad:
        found.append(bad)
    if not found:
        return None
    if len(found) == 1:
        return found[0]
    return (f"全部で {len(found)} 件（★1回の書き直しで全部 直す）:\n"
            + "\n".join("  ◆ " + m for m in found))


# ---------------- 会話のファイルから、CC の直前の本文を取り出す ----------------

def last_chat_text(path, want_files=False):
    """（CC の直前のチャット本文, 直前のまこさんの発言の id[, 書き換えたファイル名]）を返す。"""
    try:
        rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    except Exception:
        return None, None

    def is_hook_feedback(c):
        # hook の差し戻しは type=user の文字列「◯◯ hook feedback:…」として記録される
        # （2026-08-20 に44回目の記録 749de1c4… で実測）。
        return isinstance(c, str) and re.match(r"^\S+ hook feedback:", c.strip()) is not None

    def is_user_say(r):
        if r.get("type") != "user":
            return False
        c = (r.get("message") or {}).get("content")
        if isinstance(c, str):
            # ★2026-08-20 直し②＝hook の差し戻しを「まこさんの発言」に数えない。
            #   数えると、止めるたびに鍵の uuid が変わって回数が0に戻る＝上限2回が効かず、
            #   44回目に6回 連続で止まった（559〜582行で実測）。
            return bool(c.strip()) and not is_hook_feedback(c)
        if isinstance(c, list):
            return any(isinstance(b, dict) and b.get("type") == "text" for b in c)
        return False

    last_user = -1
    for i, r in enumerate(rows):
        if is_user_say(r):
            last_user = i
    uid = rows[last_user].get("uuid") if last_user >= 0 else None

    # ★2026-08-26（63回目・まこさん指示「不具合の109と110はすぐに直してほしい」）＝109番の直し。
    #   直す前＝編集の道具の呼び出しを拾うだけで、それが通ったか hook に止められたかを見ていなかった。
    #   ＝1バイトも変わっていないファイルの名前を、報告に書かされた（同じ日に2回 起きた）。
    #   直した後＝呼び出しの id ごとに結果（tool_result）を見て、止められたもの（is_error）は数えない。
    blocked = set()
    for r in rows[last_user + 1:]:
        if r.get("type") != "user":
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error"):
                if b.get("tool_use_id"):
                    blocked.add(b["tool_use_id"])

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
                if b.get("id") in blocked:
                    continue                     # ★止められた＝ファイルは1バイトも変わっていない
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


def load_last_kinds():
    """前の返信の違反の型を読む（★2026-08-26 新設）。

    ★まこさんの発言をまたいでも持ち越す。理由＝またぐたびに忘れると、
      「文が長い」を毎回 1回ずつ出せば永久に止まらない＝検査が死ぬ。
    """
    try:
        return set(json.load(open(LAST, encoding="utf-8")).get("kinds") or [])
    except Exception:
        return set()


def save_last_kinds(kinds):
    try:
        with open(LAST, "w", encoding="utf-8") as f:
            json.dump({"kinds": sorted(kinds)}, f, ensure_ascii=False)
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

    bad, kinds = check_detail(text, changed)
    if not bad:
        save_last_kinds(set())
        sys.exit(0)

    n = blocked_count(uid)
    last = load_last_kinds()
    what, why = gate_decision(kinds, last, n)
    save_last_kinds(kinds)

    if what == "pass":
        # ★2026-08-26＝形だけの違反の1回目は止めない（同じ長文を続けて出さないため）。
        #   ただし黙って通さない＝指摘は画面に出す。次の返信で同じ型が出たら止める。
        print(f"⚠️ [チャット文章の検査] 今回は通します（{why}）。\n"
              f"   直すところ: {bad}\n"
              f"   ★次の返信でも同じ型が出たら止めます。", file=sys.stderr)
        sys.exit(0)

    record_block(uid, n + 1)
    e = sys.stderr
    print("🔒 [チャット文章の検査・Stop hook] いまの返信は、まこさんに伝わる形になっていません。", file=e)
    print("   まこさん指示 2026-08-18「チャットに出すCCの文章が私に伝わらない」「強制できないの？」。", file=e)
    print(f"   止めた理由: {why}", file=e)
    print("", file=e)
    print(f"直すところ: {bad}", file=e)
    print("", file=e)
    print("対処: ★前の返信を貼り直さない（まこさん指示 2026-08-26「同じ文章を連続で出すのをやめてほしい」）。", file=e)
    print("  ・**足りない所・直した所だけ**を短く出す。長い報告を丸ごと貼り直さない。", file=e)
    print("  ・報告の中身は減らさない（まこさん 2026-08-18「私はすべての作業内容を把握したい」）。", file=e)
    print("    ＝抜けていたファイル名や説明は、この短い返信の中で足す。", file=e)
    print("  ・長い返信を出す前は、下書きを次の口へ通す（出してから止められるのをやめる）:", file=e)
    print(f"      {DRAFT} に全文を Write する（書き込みの瞬間に検査が走る）", file=e)
    print(f"（止めるのは1回のやり取りにつき {MAX_BLOCKS} 回まで。それ以上は通します）", file=e)
    sys.exit(2)


# ---------------- 下書きの検査（PreToolUse・★2026-08-26 新設） ----------------
#
# なぜ要るか（まこさんの問い 2026-08-26・逐語「１文の長さは書く前にどうにかできないのか？」）:
#   Stop hook は、私の文章が まこさんの画面に出た「後」にしか走らない。
#   だから止めると、書き直した文章がもう一度 並ぶ＝同じ文章が連続で出る。
#   道具を使う「前」なら止められる。だから長い返信は下書きのファイルに一度 書く。
#   その書き込みの瞬間に、この検査が走る。ここで止まっても、まこさんの画面には何も出ていない。
#
# 限界（正直に）:
#   下書きを作らずに直接チャットへ出す道は塞げない（私の文章の前に走る hook は存在しない）。
#   ＝これは「守る回数を増やす」もので、「守らせる」ものではない。

def pretool_main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        sys.exit(0)
    ti = data.get("tool_input") or {}
    fp = ti.get("file_path") or ""
    if os.path.basename(fp) != os.path.basename(DRAFT):
        sys.exit(0)

    name = data.get("tool_name") or ""
    if name in ("Edit", "MultiEdit"):
        print("🔒 [下書きの検査] 下書きは Write で全文を書いてください（Edit だと全文を検査できません）。",
              file=sys.stderr)
        sys.exit(2)

    text = ti.get("content") or ""
    if not text.strip():
        sys.exit(0)
    bad = check_text(text)
    if not bad:
        sys.exit(0)
    e = sys.stderr
    print("🔒 [下書きの検査・PreToolUse] この下書きは、まこさんに伝わる形になっていません。", file=e)
    print("   ★まこさんの画面にはまだ何も出ていません。ここで直せば、同じ文章が並びません。", file=e)
    print("", file=e)
    print(f"直すところ: {bad}", file=e)
    sys.exit(2)


# ---------------- 番人（わざと壊して、止まることを確かめる） ----------------

def selftest():
    ok_head = ""
    cases = [
        ("正しい文章は通る",
         ok_head + "- engine_tuner の乱数をプログラムで数えました。57件ありました。\n- 法則の表を読む回数は0回でした。\n",
         None),
        ("★語の検査は外してある＝表に載っている語を使っても止まらない（2026-08-24 まこさん指示）",
         "直しました。\n\n- 乱数を機械で数えました。57件でした。\n",
         None),
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
        # ★2026-09-10 新設＝検査7（「やること」の節の書き方・まこさん指示「入れて良い」）
        ("★やることの節に主語が無いと止まる",
         "直しました。\n\n## 次にやること\n\n1. C-38 を拾い間違いに割り当てる。理由は道具の説明文だからです。\n",
         "主語"),
        ("★やることの節で丸数字を指し先に使うと止まる",
         "直しました。\n\n## 次にやること\n\n1. 私は設計書の ④設計の中身 に書き足します。なぜなら落ちているからです。\n",
         "丸数字"),
        ("★やることの節になぜそうするかが無いと止まる",
         "直しました。\n\n## 次にやること\n\n1. 私は設計書の「設計の中身」の節に説明を書き足します。\n",
         "なぜそうするか"),
        ("★主語・言葉の指し先・理由が全部 在れば通る",
         "直しました。\n\n## 次にやること\n\n"
         "1. 私は設計書の「設計の中身」の節に説明を書き足します。なぜなら、いま書いていないからです。\n",
         None),
        ("★「やること」の見出しが無い返信には掛からない",
         "直しました。\n\n## 調べたこと\n\n- ログを数えました。19件でした。\n",
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

    # ★2026-08-20 の直しの確かめ（まこさん承認の3件に対応）
    #   ★2026-08-26 に見本を差し替えた＝語の検査を外した（2026-08-24）ので、
    #     別の2件（名前を並べただけの行 ＋ 長い文）で「2件が一度に出る」ことを確かめる。
    multi_text = ("直しました。\n\n乱数の呼び出し 57・法則の表を読む回数 0・上限5つ・表2つ\n"
                  + "私は" + "あ" * 130 + "。\n")
    got = check_text(multi_text)
    good = (got is not None and "名前を並べただけ" in got
            and "字の文がある" in got and "全部で" in got)
    print(f"  {'✅' if good else '❌'} ★直し①＝違反が2件あれば、2件とも一度に出る"
          + ("" if good else f"   ← 出た理由: {got}"))
    if not good:
        ng += 1

    import tempfile
    fake_rows = [
        {"type": "user", "uuid": "U-real", "message": {"content": "直して"}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "一回目の返信。"}]}},
        {"type": "user", "uuid": "U-hook", "message": {"content": "Stop hook feedback:\n[チャット文章の検査] 止めた"}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "二回目の返信。"}]}},
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for r in fake_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        tmp = f.name
    text2, uid2 = last_chat_text(tmp)
    os.unlink(tmp)
    good = (uid2 == "U-real" and text2 == "二回目の返信。")
    print(f"  {'✅' if good else '❌'} ★直し②＝hook の差し戻し行では回数の鍵（uuid）が変わらない"
          + ("" if good else f"   ← uid={uid2!r} text={text2!r}"))
    if not good:
        ng += 1

    # ★2026-08-26 の直しの確かめ（まこさん指示「同じ文章を連続で出すのをやめてほしい」）
    long_one = "直しました。\n\n私は" + "あ" * 130 + "。\n"
    miss_one = "直しました。\n\n- 検査を1つ足しました。\n"

    gate_cases = [
        ("★直し②＝形だけの違反は、1回目は止めない",
         gate_decision({"文が長い"}, set(), 0), "pass"),
        ("★直し②＝同じ型を2回 続けると止まる",
         gate_decision({"文が長い"}, {"文が長い"}, 0), "block"),
        ("★直し②＝前と違う型なら、また1回は通る",
         gate_decision({"段落が長い"}, {"文が長い"}, 0), "pass"),
        ("★直し③＝報告の中身が減っていたら、1回目から止める",
         gate_decision({KIND_HEAVY}, set(), 0), "block"),
        ("★直し④＝止めるのは1回まで（2回目は通す）",
         gate_decision({KIND_HEAVY}, set(), MAX_BLOCKS), "pass"),
        ("違反が無ければ通る",
         gate_decision(set(), {"文が長い"}, 0), "pass"),
    ]
    for name, got, want in gate_cases:
        good = (got[0] == want)
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た答え: {got}"))
        if not good:
            ng += 1

    # 違反の型が正しく付くか（判定の入口）
    _m, k1 = check_detail(long_one)
    _m, k2 = check_detail(miss_one, ["engine_tuner_gen.py"])
    for name, got, want in [("長い文には「文が長い」の型が付く", k1, {"文が長い"}),
                            ("報告漏れには「報告漏れ」の型が付く", k2, {KIND_HEAVY})]:
        good = (got == want)
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た型: {got}"))
        if not good:
            ng += 1

    # ★2026-08-26＝109番の直しの確かめ（止められた編集は「書き換えた」に数えない）
    rows109 = [
        {"type": "user", "uuid": "U1", "message": {"content": "やって"}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "T-ok", "name": "Edit",
             "input": {"file_path": "/x/tootta.py"}},
            {"type": "tool_use", "id": "T-ng", "name": "Edit",
             "input": {"file_path": "/x/tomerareta.py"}}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "T-ok", "content": "ok"},
            {"type": "tool_result", "tool_use_id": "T-ng", "is_error": True,
             "content": "PreToolUse:Edit hook error: ..."}]}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "直しました。"}]}},
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for r in rows109:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        tmp109 = f.name
    _t, _u, files109 = last_chat_text(tmp109, want_files=True)
    os.unlink(tmp109)
    good = (files109 == ["tootta.py"])
    print(f"  {'✅' if good else '❌'} ★109番＝hook に止められた編集は『書き換えた』に数えない"
          + ("" if good else f"   ← 出たファイル: {files109}"))
    if not good:
        ng += 1

    total = len(cases) + len(extra) + 3 + len(gate_cases) + 2
    print(f"\n番人: {total - ng}/{total} pass")
    sys.exit(1 if ng else 0)


def check_draft():
    """★2026-08-20 直し③＝出す前の照合の口。
    使い方: python3 enforce_chat_writing.py --check <下書きファイル>
    CC は返信をチャットに出す前に、下書きをこの検査へ通す＝出してから止められる運任せをやめる。
    判定の本体は hook と同じ check_text（二重に作らない＝検査がずれない）。"""
    i = sys.argv.index("--check")
    if i + 1 >= len(sys.argv):
        print("使い方: --check <下書きファイル>")
        sys.exit(1)
    try:
        text = open(sys.argv[i + 1], encoding="utf-8").read()
    except Exception as e:
        print(f"下書きが読めない: {e}")
        sys.exit(1)
    bad = check_text(text)
    if bad:
        print(f"❌ 直すところ: {bad}")
        sys.exit(1)
    print("✅ 検査を通った（語・行の形・文の長さ・段落・結論の位置）")
    sys.exit(0)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    if "--check" in sys.argv:
        check_draft()
    if "--pretool" in sys.argv:
        pretool_main()
    hook_main()
