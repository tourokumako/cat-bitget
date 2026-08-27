#!/usr/bin/env python3
# enforce_todo_declaration.py — ToDo 宣言ゲートの本体（2026-08-16 まこさん承認「件２はOK」・新設）
#
# 目的:
#   まこさんの逐語（2026-08-16）＝「TodoWriteが使えず、to doのフロー化が不正確になることも
#   やめてほしいんだけど」「私はこのチャットにtodoを正確に表示して進めてほしいんだけど」。
#   TodoWrite（やることリストの道具）がこのセッションで CC に渡されていない。設定ファイル3本
#   （.claude/settings.json ／ .claude/settings.local.json ／ ~/.claude/settings.json）を開いて
#   確かめたが、道具を止める設定はどれにも無い＝原因は Claude Code 側で CC からは直せない。
#   ＝「CC が気をつける」では守れない。ファイルに書かせて、機械で照合する。
#
# 検査（7件）:
#   1. .claude/state/session_todo.md が在る
#   2. 4行の型が在る（【いまの工程】【ToDo】【止まっているもの】【次】）
#   3. 表の行が1行以上 在る
#   4. 「★いまここ」がちょうど1件（全部 ✅済 のときだけ 0 でよい）
#      ＝恒久の決まり §3-3「1つだけを in_progress にする」の物理化
#   5. 「✅済」の行に、worklog の節の番号（§NN）が書いてある
#   6. その §NN が、今日の session_worklog_YYYYMMDD.md に見出しとして本当に在る
#      ＝ToDo だけ「終わった」にして記録を書かない、を止める
#   7. ★この版の ToDo が、一度この hook の止まりで画面に表示されている
#      表示の記録（.claude/state/session_todo_shown）は、hook が止まって全文を画面に出したときに
#      だけ、hook 自身が作る。CC は作らない。
#      ＝2026-08-16（30回目）に CC が「チャットに貼らずに、印だけ先に作る」で すり抜けた穴を塞ぐ
#      （まこさん指示・逐語「hookが効いてないのであれば、修正して」「todoフローナシで進める
#      ことは禁止にする」。フロー宣言ゲートの「必ず1回ブロックして全文をこの場に出す」と同型）
#   8. ファイルの指紋が .claude/state/session_todo_posted と一致する
#      ＝チャットに貼っていない ToDo で作業を進められない
#      （同じ「指紋の印」の仕組みを 解釈ゲートも使っていたが、そちらは 2026-08-18 に まこさんの指示で
#        廃止し、2026-08-22 にファイルごと消した＝いま在るのはこの ToDo ゲートだけ）
#
# safety hook: fast-mode 無効化行を入れない。
#   理由＝まこさんが 2026-08-16 に「fast-modeをオフにすると実行する強制内容は、今後は使わないと
#   思う」と言った。fast-mode で止まる形にすると、この hook は1回も動かない。
#
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で廃止）。
#
# 限界（正直に）:
#   ToDo の中身が実物と合っているかは、機械には分からない。CC が「A-7 は終わった」と嘘を書けば
#   そのまま通る。§NN の中身が空でも通る（節が在るかしか見ない）。
#   表示の記録（session_todo_shown）を CC が echo で偽造すれば通る＝hook のファイル自体を書き換えるのと同じ
#   明示の違反で、機械では見抜けない。最後の関所はまこさんの目。

import glob
import hashlib
import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
STATE = os.path.join(ROOT, ".claude", "state")
TODO = os.path.join(STATE, "session_todo.md")
MARK = os.path.join(STATE, "session_todo_posted")
SHOWN = os.path.join(STATE, "session_todo_shown")   # hook が全文を画面に出したときにだけ hook が作る

HEADS = ("【いまの工程】", "【ToDo】", "【止まっているもの】", "【次】")
DONE, DOING, YET = "✅済", "★いまここ", "まだ"

# ★2026-08-26（63回目・まこさん指示「不具合の109と110はすぐに直してほしい」）＝110番の直し。
#   直す前＝「表示された」と数えるのは、この hook が止まって全文を画面に出したときだけだった。
#     ＝ToDo を1文字 直すたびに、必ず1回 止まってから貼り直すことになり、
#       同じ長文が続けて画面に出た（2026-08-26 に5回）。まこさんの逐語「同じ文章を連続で出すのをやめてほしい」。
#   直した後＝会話の記録を読み、CC が実際にチャットへ貼っていれば「表示された」と数える。
#     ＝先に貼っておけば、止まらずに通る。貼っていなければ、今までどおり止まる（守りは減らない）。
PROJECTS = os.path.expanduser("~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget")


def chat_texts(transcript=None):
    """このセッションで CC がチャットに出した文章を、古い順に返す（★読むだけ・何も書かない）。

    記録が読めないときは空の一覧（安全側＝今までどおり止まる）。
    """
    path = transcript
    if not path or not os.path.exists(path):
        files = sorted(glob.glob(os.path.join(PROJECTS, "*.jsonl")), key=os.path.getmtime)
        if not files:
            return []
        path = files[-1]
    try:
        rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    except Exception:
        return []
    out = []
    for r in rows:
        if r.get("type") != "assistant":
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "text":
                out.append(b.get("text") or "")
    return out


def pasted_in_chat(text, transcript=None):
    """CC がこのセッションのチャットに、この ToDo の全文を貼ったかを会話の記録で確かめる。

    ★中身の一致で見る（ハッシュではない）＝``` で囲んで貼っても、そのまま中に入っているので当たる。
    """
    body = (text or "").strip()
    if not body:
        return False
    return any(body in t for t in chat_texts(transcript))


# ★2026-08-27（67回目・まこさん決定「案Aにする」・承認 299703af231e2314）＝案A。
#   直す前＝ToDo を1文字 直すたびに『全文』を貼らないと通らなかった。
#     理由＝表示の記録（SHOWN）がハッシュ値だけを持ち、前の本文が残らないので差分を出せなかった。
#     まこさんの逐語（2026-08-26）＝「同じ文章を連続で出すのをやめてほしい」と逆になっていた。
#     67回目に、この作りで5回 止まった（そのうち1回は、この直しの作業そのものの中）。
#   直した後＝SHOWN に本文を保存し、前の本文といまの本文の『変わった行』が全部チャットに在れば通す。
#     ★4行の型（いまの版）は毎回 求める＝現在地は毎回 まこさんの画面に出る。
#     ★守りは減らない＝貼っていない中身では通らない（番人 N2 で確かめる）。

def changed_lines(old, new):
    """前の本文に無くて、いまの本文に在る行（空行は数えない・前後の空白は落とす）。"""
    prev = {ln.strip() for ln in (old or "").splitlines() if ln.strip()}
    out = []
    for ln in (new or "").splitlines():
        s = ln.strip()
        if s and s not in prev and s not in out:
            out.append(s)
    return out


def heads_in_chat(text, transcript=None):
    """4行の型（いまの版）のうち、チャットに出ていないものの一覧を返す（空なら全部 出ている）。"""
    texts = chat_texts(transcript)
    missing = []
    for ln in (text or "").splitlines():
        s = ln.strip()
        if any(s.startswith(h) for h in HEADS) and not any(s in t for t in texts):
            missing.append(s)
    return missing


def read_shown_body():
    """表示の記録の中身を返す。★古い形（ハッシュ値だけ）のときは None。"""
    raw = read(SHOWN)
    s = raw.strip()
    if not s:
        return None
    if re.fullmatch(r"[0-9a-f]{64}", s):
        return None                                # 2026-08-27 より前の形（ハッシュ値）
    return raw


def read(p):
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def todo_rows(text):
    """表の行だけを返す。見出し行・区切り行・「状態に使う言葉」の説明表は除く。"""
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 4:
            continue                      # 説明表（2列）は対象外
        if not re.fullmatch(r"\d+", cells[0]):
            continue                      # 先頭が番号でない＝見出し行・区切り行
        rows.append({"no": cells[0], "what": cells[1], "state": cells[2], "rec": cells[3]})
    return rows


def worklog_sections():
    """今日の worklog（無ければ一番新しい worklog）の見出しに在る節の番号を集める。"""
    files = sorted(glob.glob(os.path.join(STATE, "session_worklog_*.md")))
    if not files:
        return set(), None
    p = files[-1]
    secs = set()
    for line in read(p).splitlines():
        if line.startswith("#"):
            for m in re.finditer(r"§\s*([0-9]+(?:\.[0-9]+)?)", line):
                secs.add(m.group(1))
    return secs, os.path.basename(p)


def check(transcript=None):
    """問題があれば理由の文字列を返す。無ければ None。"""
    if not os.path.exists(TODO):
        return f"ToDo のファイルが無い（{TODO}）"

    text = read(TODO)

    for h in HEADS:
        if h not in text:
            return f"「{h}」の行が無い（4行の型＝{' '.join(HEADS)}）"

    rows = todo_rows(text)
    if not rows:
        return "ToDo の表に行が1つも無い（| 番号 | やること | 状態 | 記録 | の形で書く）"

    for r in rows:
        if r["state"] not in (DONE, DOING, YET):
            return (f"{r['no']}番の状態が「{r['state']}」＝決めた3つの言葉のどれでもない。"
                    f"使うのは {DONE} ／ {DOING} ／ {YET} の3つだけ（言い方を散らさない）")

    doing = [r for r in rows if r["state"] == DOING]
    if len(doing) > 1:
        return (f"「{DOING}」が {len(doing)} 件ある（{'・'.join(r['no'] + '番' for r in doing)}）。"
                f"同時に1件だけにする（恒久の決まり §3-3）")
    if not doing and any(r["state"] == YET for r in rows):
        return (f"「{DOING}」が1件も無いのに、まだ終わっていない ToDo が残っている。"
                f"いまやっている1件に {DOING} を付ける")

    secs, wl = worklog_sections()
    for r in rows:
        if r["state"] != DONE:
            continue
        m = re.search(r"§\s*([0-9]+(?:\.[0-9]+)?)", r["rec"])
        if not m:
            return (f"{r['no']}番が {DONE} なのに、「記録」の欄に worklog の節の番号（§NN）が無い"
                    f"（いまの中身＝「{r['rec']}」）。終わったことは worklog に書いてから {DONE} にする")
        if wl is None:
            return "worklog のファイルが1本も無い（.claude/state/session_worklog_*.md）"
        if m.group(1) not in secs:
            return (f"{r['no']}番が指す §{m.group(1)} が {wl} の見出しに無い。"
                    f"worklog にその節を書いてから {DONE} にする")

    # ★前のセッションの ToDo を持ち越さない仕組みは、この中では見ません。
    #   reset_read_log.sh（SessionStart）が session_todo_posted を消します＝印が消えるので、
    #   このセッションで貼り直すまで下の指紋の検査が落ちます。
    #   ★2026-08-16 に一度、read_log.txt の更新時刻と比べる形で書いて、間違えました。
    #     read_log.txt は SessionStart だけでなく、Read を1回するたびに record_read.sh が追記します
    #     ＝作業中にファイルを読むたびに「前のセッションのまま」と誤って止まりました。
    #     この hook の最初の実走で、私自身が止められて分かりました。
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    shown_raw = read(SHOWN).strip()
    if shown_raw != h:                             # 古い形（ハッシュ値）で一致していれば、そのまま通す
        # ★2026-08-26＝110番の直し。CC が自分でチャットへ貼っていれば、それも「表示された」と数える。
        # ★2026-08-27＝案A。全文でなく『変わった行』でもよい（前の本文が残っているときだけ）。
        ok = False
        why = ""
        if pasted_in_chat(text, transcript):
            ok = True                              # 全文を貼った＝いままでどおり通る
        else:
            prev = read_shown_body()
            if prev is None:
                why = ("★前に貼った本文が残っていない（このセッションで まだ1回も貼っていないか、"
                       "古い形の記録）。**このときは全文を貼る**")
            else:
                need = changed_lines(prev, text)
                texts = chat_texts(transcript)
                miss = [ln for ln in need if not any(ln in t for t in texts)]
                heads_miss = heads_in_chat(text, transcript)
                if miss or heads_miss:
                    parts = []
                    if heads_miss:
                        parts.append("4行の型が貼られていない＝" + " ／ ".join(heads_miss[:4]))
                    if miss:
                        parts.append(f"変わった行のうち {len(miss)} 行が貼られていない＝"
                                     + " ／ ".join(m[:60] for m in miss[:5]))
                    why = ("★変わった行だけを貼る形（2026-08-27・案A）で見たが、足りない＝"
                           + " ／ ".join(parts))
                else:
                    ok = True                      # 変わった行と4行の型が全部 貼られている
        if ok:
            try:
                with open(SHOWN, "w", encoding="utf-8") as f:
                    f.write(text)                  # ★次回の差分のために本文を残す（案A）
            except Exception:
                pass
        else:
            return (why + "。いまの止まりでも全文が画面に出た。"
                    "同じ内容をチャットに貼り、印を作ってから再実行する")
    if read(MARK).strip() != h:
        return "ToDo をチャットに貼った確認マーカーが無い、または ToDo を書き換えた後で貼り直していない"

    return None


def fail(reason):
    e = sys.stderr
    print("🔒 [ToDo ゲート・safety hook] ToDo をチャットに正確に出してから作業してください。", file=e)
    print("   まこさん指示 2026-08-16「私はこのチャットにtodoを正確に表示して進めてほしいんだけど」。", file=e)
    print("", file=e)
    print(f"不足: {reason}", file=e)
    print("", file=e)
    if os.path.exists(TODO):
        print("───────── いまの ToDo（この全文をそのままチャットに貼る）─────────", file=e)
        print(read(TODO), file=e)
        print("──────────────────────────────────────────────────", file=e)
        print("", file=e)
        # ★表示の記録は、全文を画面に出した「いま」だけ作る（CC は作らない・検査7の実体）
        # ★2026-08-27（案A）＝ハッシュ値ではなく本文を残す（次回の差分の材料）
        try:
            with open(SHOWN, "w", encoding="utf-8") as f:
                f.write(read(TODO))
        except Exception:
            pass
    print("対処: ①ToDo を直す ②同じ内容をチャットに貼る ③下のコマンドで印を作る ④再実行する", file=e)
    print(f'  shasum -a 256 "{TODO}" | awk \'{{print $1}}\' > "{MARK}"', file=e)
    print("（解除は 2026-08-16 に廃止＝合言葉では通りません）", file=e)
    sys.exit(2)


def hook_main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        sys.exit(0)                                    # 読めない入力では止めない（fail-open）

    if data.get("agent_type"):
        sys.exit(0)                                    # サブエージェントは通す（デッドロック回避）

    ti = data.get("tool_input") or {}
    cmd = ti.get("command", "") or ""
    fpath = ti.get("file_path", "") or ""

    # ★解除（TODO_OK=1）は 2026-08-16 に廃止（まこさん指示）＝通す道は無い。

    # ToDo ファイル自身と印の操作は通す（止めると ToDo が書けない＝デッドロック）
    if fpath in (TODO, MARK) or "session_todo" in cmd:
        sys.exit(0)

    tool = data.get("tool_name", "")
    if tool in ("Write", "Edit", "MultiEdit"):
        pass
    elif tool == "Bash":
        # 引用符・ヒアドキュメントの中身を外す（文章での言及で誤発火させない・他 hook と同型）
        x = re.sub(r"<<\s*[\"']?(\w+)[\"']?.*?^\1", " ", cmd, flags=re.S | re.M)
        x = re.sub(r'"[^"]*"', " ", x)
        x = re.sub(r"'[^']*'", " ", x)
        if not re.search(r"python[0-9.]*[ \t]", x):
            sys.exit(0)                                # 読む・調べる系は止めない
        if re.search(r"--selftest|py_compile|--help|--verify", x):
            sys.exit(0)                                # 検査だけの実行は通す
    else:
        sys.exit(0)

    reason = check(data.get("transcript_path"))
    if reason:
        fail(reason)
    sys.exit(0)


# ---------------- 番人（わざと壊して、止まることを確かめる） ----------------

STALE = "前のセッションの ToDo を持ち越すと止まる（SessionStart で印と表示の記録が消えるため）"
NOSHOW = "★チャットに貼らずに印だけ先に作っても止まる（2026-08-16 の穴ふさぎ）"


def selftest():
    import shutil
    import tempfile

    global TODO, MARK, STATE, SHOWN
    keep = (TODO, MARK, STATE, SHOWN)
    tmp = tempfile.mkdtemp()
    STATE = tmp
    TODO = os.path.join(tmp, "session_todo.md")
    MARK = os.path.join(tmp, "session_todo_posted")
    SHOWN = os.path.join(tmp, "session_todo_shown")

    def put(body, wl="# §33 やった\n# §34 やった\n", mark=True, stale=False, shown=True,
            shown_val=None):
        with open(TODO, "w", encoding="utf-8") as f:
            f.write(body)
        with open(os.path.join(tmp, "session_worklog_20260816.md"), "w", encoding="utf-8") as f:
            f.write(wl)
        if stale:                    # 前セッションの持ち越し＝SessionStart が印も表示の記録も消した形
            mark = False
            shown = False
        h = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if mark:
            with open(MARK, "w", encoding="utf-8") as f:
                f.write(h)
        elif os.path.exists(MARK):
            os.remove(MARK)
        if shown:
            with open(SHOWN, "w", encoding="utf-8") as f:
                f.write(h if shown_val is None else shown_val)
        elif os.path.exists(SHOWN):
            os.remove(SHOWN)

    head = ("【いまの工程】x\n【ToDo】x\n【止まっているもの】なし\n【次】x\n\n"
            "| # | やること | 状態 | 記録 |\n|---|---|---|---|\n")
    ok_body = head + f"| 1 | a | {DONE} | §33 |\n| 2 | b | {DOING} | — |\n| 3 | c | {YET} | — |\n"

    cases = [
        ("正しい ToDo は通る", ok_body, None, True, None),
        ("4行の型が欠けると止まる",
         ok_body.replace("【次】x\n", ""), None, True, "【次】"),
        ("表が空だと止まる", head, None, True, "行が1つも無い"),
        (f"{DOING} が2件だと止まる",
         head + f"| 1 | a | {DOING} | — |\n| 2 | b | {DOING} | — |\n", None, True, "2 件ある"),
        (f"{DOING} が0件で {YET} が残ると止まる",
         head + f"| 1 | a | {DONE} | §33 |\n| 2 | b | {YET} | — |\n", None, True, "1件も無い"),
        ("状態の言い方を散らすと止まる",
         head + f"| 1 | a | 完了 | §33 |\n| 2 | b | {DOING} | — |\n", None, True, "3つの言葉のどれでもない"),
        (f"{DONE} に §NN が無いと止まる",
         head + f"| 1 | a | {DONE} | — |\n| 2 | b | {DOING} | — |\n", None, True, "§NN"),
        ("§NN が worklog に無いと止まる",
         head + f"| 1 | a | {DONE} | §99 |\n| 2 | b | {DOING} | — |\n", None, True, "見出しに無い"),
        ("チャットに貼っていないと止まる", ok_body, None, False, "確認マーカー"),
        (NOSHOW, ok_body, None, True, "全文を貼る"),
        (STALE, ok_body, None, True, "全文を貼る"),
    ]

    # ★2026-08-26（110番の直し）＝会話の記録を、番人の中でも作り物にする。
    #   本物の記録を読ませると、結果がその日のチャットの中身で変わってしまう。
    empty_tr = os.path.join(tmp, "empty.jsonl")
    with open(empty_tr, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "assistant",
                            "message": {"content": [{"type": "text", "text": "なにも貼っていない"}]}},
                           ensure_ascii=False) + "\n")

    ng = 0
    for name, body, wl, mark, want in cases:
        put(body, wl or "# §33 やった\n# §34 やった\n", mark,
            stale=(name == STALE), shown=(name != NOSHOW))
        got = check(empty_tr)
        if want is None:
            good = got is None
        else:
            good = got is not None and want in got
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た理由: {got}"))
        if not good:
            ng += 1

    # ★2026-08-26＝110番の直しの確かめ。先にチャットへ貼っていれば、止まらずに通る。
    put(ok_body, mark=True, shown=False)
    pasted_tr = os.path.join(tmp, "pasted.jsonl")
    with open(pasted_tr, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "assistant",
                            "message": {"content": [{"type": "text",
                                                     "text": "ToDo を貼ります。\n\n```\n" + ok_body + "```\n"}]}},
                           ensure_ascii=False) + "\n")
    got = check(pasted_tr)
    good = got is None
    print(f"  {'✅' if good else '❌'} ★110番＝先にチャットへ貼っていれば、止まらずに通る"
          + ("" if good else f"   ← 出た理由: {got}"))
    if not good:
        ng += 1

    # 貼った本文が1文字でも違えば、今までどおり止まる（守りは減らない）
    put(ok_body, mark=True, shown=False)
    other_tr = os.path.join(tmp, "other.jsonl")
    with open(other_tr, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "assistant",
                            "message": {"content": [{"type": "text",
                                                     "text": "```\n" + ok_body.replace("| a |", "| z |") + "```"}]}},
                           ensure_ascii=False) + "\n")
    got = check(other_tr)
    good = got is not None and "全文を貼る" in got
    print(f"  {'✅' if good else '❌'} ★110番＝違う中身を貼っても通らない"
          + ("" if good else f"   ← 出た理由: {got}"))
    if not good:
        ng += 1

    # ──────── ★2026-08-27（案A）＝変わった行だけで通す・6件 ────────
    #   前の本文＝ok_body ／ いまの本文＝1行だけ変えたもの。
    new_body = ok_body.replace("| 3 | c | まだ | — |", "| 3 | c | ★いまここ | §34 |")
    new_body = new_body.replace(f"| 2 | b | {DOING} | — |", f"| 2 | b | {DONE} | §34 |")
    diff_line = f"| 2 | b | {DONE} | §34 |\n| 3 | c | {DOING} | §34 |"   # ★変えた行は2つ
    heads4 = "【いまの工程】x\n【ToDo】x\n【止まっているもの】なし\n【次】x"

    def tr(name, text):
        p = os.path.join(tmp, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "assistant",
                                "message": {"content": [{"type": "text", "text": text}]}},
                               ensure_ascii=False) + "\n")
        return p

    n_cases = [
        ("N1 変わった行＋4行の型を貼れば通る（案A の狙い）",
         True, heads4 + "\n" + diff_line, None),
        ("N2 変わった行を貼っていないと止まる（守りは減らない）",
         True, heads4 + "\nなにも貼っていない", "変わった行"),
        ("N3 4行の型を貼っていないと止まる",
         True, diff_line, "4行の型"),
        ("N4 前の本文が無い＋全文を貼れば通る",
         False, "```\n" + new_body + "```", None),
        ("N5 前の本文が無い＋変わった行だけでは止まる",
         False, heads4 + "\n" + diff_line, "全文を貼る"),
    ]
    for name, has_prev, chat, want in n_cases:
        put(new_body, mark=True, shown=has_prev, shown_val=(ok_body if has_prev else None))
        got = check(tr("n.jsonl", chat))
        good = (got is None) if want is None else (got is not None and want in got)
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た理由: {got}"))
        if not good:
            ng += 1

    # N6 古い形の記録（ハッシュ値）でも壊れない＝全文を貼れば通る
    put(new_body, mark=True, shown=True,
        shown_val=hashlib.sha256(ok_body.encode("utf-8")).hexdigest())
    got = check(tr("n6.jsonl", "```\n" + new_body + "```"))
    good = got is None
    print(f"  {'✅' if good else '❌'} N6 古い形の記録（ハッシュ値）でも壊れない"
          + ("" if good else f"   ← 出た理由: {got}"))
    if not good:
        ng += 1

    # ToDo ファイルが無いときも止まる
    os.remove(TODO)
    got = check(empty_tr)
    good = got is not None and "ファイルが無い" in got
    print(f"  {'✅' if good else '❌'} ToDo のファイルが無いと止まる")
    if not good:
        ng += 1

    shutil.rmtree(tmp, ignore_errors=True)
    TODO, MARK, STATE, SHOWN = keep
    total = len(cases) + 3 + len(n_cases) + 1
    print(f"\n番人: {total - ng}/{total} pass")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    hook_main()
