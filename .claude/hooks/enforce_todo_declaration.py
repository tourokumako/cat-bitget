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
#   7. ファイルの指紋が .claude/state/session_todo_posted と一致する
#      ＝チャットに貼っていない ToDo で作業を進められない（解釈ゲートと同じ仕組み）
#
# safety hook: fast-mode 無効化行を入れない。
#   理由＝まこさんが 2026-08-16 に「fast-modeをオフにすると実行する強制内容は、今後は使わないと
#   思う」と言った。fast-mode で止まる形にすると、この hook は1回も動かない。
#
# 解除: TODO_OK=1（まこさんの明示 OK 時のみ・乱用禁止）。
#
# 限界（正直に）:
#   ToDo の中身が実物と合っているかは、機械には分からない。CC が「A-7 は終わった」と嘘を書けば
#   そのまま通る。§NN の中身が空でも通る（節が在るかしか見ない）。最後の関所はまこさんの目。

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

HEADS = ("【いまの工程】", "【ToDo】", "【止まっているもの】", "【次】")
DONE, DOING, YET = "✅済", "★いまここ", "まだ"


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


def check():
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
    print("対処: ①ToDo を直す ②同じ内容をチャットに貼る ③下のコマンドで印を作る ④再実行する", file=e)
    print(f'  shasum -a 256 "{TODO}" | awk \'{{print $1}}\' > "{MARK}"', file=e)
    print("（TODO_OK=1 はまこさん明示 OK 時のみ）", file=e)
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

    if "TODO_OK=1" in raw:
        sys.exit(0)

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

    reason = check()
    if reason:
        fail(reason)
    sys.exit(0)


# ---------------- 番人（わざと壊して、止まることを確かめる） ----------------

STALE = "前のセッションの ToDo を持ち越すと止まる（SessionStart で印が消えるため）"


def selftest():
    import shutil
    import tempfile

    global TODO, MARK, STATE
    keep = (TODO, MARK, STATE)
    tmp = tempfile.mkdtemp()
    STATE = tmp
    TODO = os.path.join(tmp, "session_todo.md")
    MARK = os.path.join(tmp, "session_todo_posted")

    def put(body, wl="# §33 やった\n# §34 やった\n", mark=True, stale=False):
        with open(TODO, "w", encoding="utf-8") as f:
            f.write(body)
        with open(os.path.join(tmp, "session_worklog_20260816.md"), "w", encoding="utf-8") as f:
            f.write(wl)
        if stale:                                      # 前セッションの持ち越し＝印だけが残っている形
            mark = False
        if mark:
            h = hashlib.sha256(body.encode("utf-8")).hexdigest()
            with open(MARK, "w", encoding="utf-8") as f:
                f.write(h)
        elif os.path.exists(MARK):
            os.remove(MARK)

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
        (STALE, ok_body, None, True, "確認マーカー"),
    ]

    ng = 0
    for name, body, wl, mark, want in cases:
        put(body, wl or "# §33 やった\n# §34 やった\n", mark, stale=(name == STALE))
        got = check()
        if want is None:
            good = got is None
        else:
            good = got is not None and want in got
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た理由: {got}"))
        if not good:
            ng += 1

    # ToDo ファイルが無いときも止まる
    os.remove(TODO)
    got = check()
    good = got is not None and "ファイルが無い" in got
    print(f"  {'✅' if good else '❌'} ToDo のファイルが無いと止まる")
    if not good:
        ng += 1

    shutil.rmtree(tmp, ignore_errors=True)
    TODO, MARK, STATE = keep
    total = len(cases) + 1
    print(f"\n番人: {total - ng}/{total} pass")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    hook_main()
