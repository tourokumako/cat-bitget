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
# ★2026-09-06（まこさん指示・逐語「今後は並走するのでToDo ゲートの状態ファイルをセッションごとに
#   分ける直しをやってほしい」・承認 iter="todo-gate-per-session-20260906"）＝状態ファイル3つの置き場を
#   セッションごとにした。
#   直す前＝.claude/state/ に session_todo.md・session_todo_posted・session_todo_shown が1組しか無く、
#     2つのセッションを並走させると、片方が ToDo を書くと もう片方の hook が止まり、片方の SessionStart が
#     もう片方の印を消した（85回目・worklog 20260904 §37（3）・§39）。
#   直した後＝.claude/state/sessions/<セッションの id>/ の下に3つを置く。id は hook の入力の session_id
#     （無ければ transcript_path の名前）から読む＝session_id_of()。置き場は paths_of()。
#     id が無ければ止める（fail-closed）。判定の中身（下の検査）は1文字も変えていない。
#
# 検査（8件）:
#   1. .claude/state/sessions/<セッションの id>/session_todo.md が在る
#   2. 4行の型が在る（【いまの工程】【ToDo】【止まっているもの】【次】）
#   3. 表の行が1行以上 在る
#   4. 「★いまここ」がちょうど1件（全部 ✅済 のときだけ 0 でよい）
#      ＝恒久の決まり §3-3「1つだけを in_progress にする」の物理化
#   5. 「✅済」の行に、worklog の節の番号（§NN）が書いてある
#   6. その §NN が、今日の session_worklog_YYYYMMDD.md に見出しとして本当に在る
#      ＝ToDo だけ「終わった」にして記録を書かない、を止める
#   7. ★この版の ToDo が、一度この hook の止まりで画面に表示されている
#      表示の記録（同じ置き場の session_todo_shown）は、hook が止まって全文を画面に出したときに
#      だけ、hook 自身が作る。CC は作らない。
#      ＝2026-08-16（30回目）に CC が「チャットに貼らずに、印だけ先に作る」で すり抜けた穴を塞ぐ
#      （まこさん指示・逐語「hookが効いてないのであれば、修正して」「todoフローナシで進める
#      ことは禁止にする」。フロー宣言ゲートの「必ず1回ブロックして全文をこの場に出す」と同型）
#   8. ファイルの指紋が 同じ置き場の session_todo_posted と一致する
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
#   ★2026-09-06＝セッションの id は Claude Code が入力に入れるものに頼る（うちのコードでは決められない）。
#     別のセッションの置き場に ToDo を書く道は残る（書いても自分の検査には効かない＝自分は通らない）。

import glob
import hashlib
import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
STATE = os.path.join(ROOT, ".claude", "state")
SESSIONS = os.path.join(STATE, "sessions")   # ★2026-09-06＝セッションごとの置き場の親（下に <セッションの id>/）

HEADS = ("【いまの工程】", "【ToDo】", "【止まっているもの】", "【次】")
DONE, DOING, YET = "✅済", "★いまここ", "まだ"

# ★2026-08-26（63回目・まこさん指示「不具合の109と110はすぐに直してほしい」）＝110番の直し。
#   直す前＝「表示された」と数えるのは、この hook が止まって全文を画面に出したときだけだった。
#     ＝ToDo を1文字 直すたびに、必ず1回 止まってから貼り直すことになり、
#       同じ長文が続けて画面に出た（2026-08-26 に5回）。まこさんの逐語「同じ文章を連続で出すのをやめてほしい」。
#   直した後＝会話の記録を読み、CC が実際にチャットへ貼っていれば「表示された」と数える。
#     ＝先に貼っておけば、止まらずに通る。貼っていなければ、今までどおり止まる（守りは減らない）。
PROJECTS = os.path.expanduser("~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget")


def session_id_of(data):
    """hook の入力（stdin の json）からセッションの id を返す。無ければ None（→ 止める側）。

    ★2026-09-06 新設。読む順＝①session_id ②transcript_path のファイル名（.jsonl を除く）。
    パスに使えない文字（/ や空白など）は _ に置き換える＝置き場の外へ出ない。
    """
    if not isinstance(data, dict):
        return None
    sid = data.get("session_id")
    if not (isinstance(sid, str) and sid.strip()):
        tp = data.get("transcript_path")
        base = os.path.basename(tp.strip()) if isinstance(tp, str) and tp.strip() else ""
        sid = base[:-6] if base.endswith(".jsonl") else base
    # 使えない文字は _ に。先頭の . は落とす（"../x" → "_x"＝隠しディレクトリにも上の階層にもならない）
    sid = re.sub(r"[^A-Za-z0-9._-]", "_", (sid or "").strip()).lstrip(".")
    if not sid or set(sid) <= set("._"):
        return None
    return sid


def paths_of(sid):
    """そのセッションの置き場と、状態ファイル3つのパスを返す。置き場のディレクトリが無ければ作る。

    ★2026-09-06 新設。返すもの＝dir ／ todo（ToDo の本文）／ mark（貼った印）／ shown（表示の記録）。
    """
    d = os.path.join(SESSIONS, sid)
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return {"dir": d,
            "todo": os.path.join(d, "session_todo.md"),
            "mark": os.path.join(d, "session_todo_posted"),
            "shown": os.path.join(d, "session_todo_shown")}


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
    # ★2026-08-27＝1行ずつ読む。直す前は1行でも JSON として壊れていると全部を捨てていた
    #   ＝貼った行まで見えなくなり、止まり続ける。壊れた行だけ飛ばし、読める行は生かす。
    try:
        lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    except Exception:
        return []
    out = []
    for l in lines:
        if not l.strip():
            continue
        try:
            r = json.loads(l)
        except Exception:
            continue
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

# ★2026-08-27（69回目・まこさん指示「この修正をここで対応してほしい」・auditor セッションで実測）＝
#   VSCode 拡張では、CC の本文が会話の記録（jsonl）に書かれるのがターンの終わり頃で、
#   同じターンの中では hook が貼りを読めないことがある（短い本文は読めた・長い本文は読めなかった。
#   ToDo を正しく貼っても5回 止まった）。直し2つ＝
#   1. chat_texts を1行ずつ読む形に（壊れた行が1つ在ると記録全体が見えなくなる作りだった）。
#   2. 表示の記録（SHOWN＝hook 自身が全文を画面に出したときにだけ書く本文）が いまの本文と
#      同じなら通す（check() の elif prev == text）。番人 N7〜N9 で確かめる。


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


def read_shown_body(sid):
    """そのセッションの表示の記録の中身を返す。★古い形（ハッシュ値だけ）のときは None。"""
    raw = read(paths_of(sid)["shown"])
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


def body_problems(text):
    """ToDo の「中身」の検査。見つけた不足を全部 返す（リスト）。チャットに貼ったかは見ない。

    ★2026-09-05（まこさん承認・逐語「進めて」）＝1件目で止める形をやめた。
      直す前は最初の1件で return していたので、CC が1件 直すたびに止まり、そのたびに
      ToDo の全文を貼り直していた（2026-09-05 に同じ日で4回・まこさん指摘
      「todo作成でトークン代を無駄にされるのは勘弁してほしいので、1回で書けるように修正すること」）。
      チャットの文章の検査には 2026-08-20 に同じ直しが入っている（pdca_flow §1 の逐語
      「違反を全部 一度に出す形にしました」）。この hook だけ残っていた。
    ★判定は1つも消していない・緩めていない。変えたのは「出し方」だけ。
    ★この関数は `--check`（書く前に自分で確かめる口）からも呼ぶ＝判定を2か所に書き写さない。
    """
    probs = []

    for h in HEADS:
        if h not in text:
            probs.append(f"「{h}」の行が無い（4行の型＝{' '.join(HEADS)}）")

    rows = todo_rows(text)
    if not rows:
        probs.append("ToDo の表に行が1つも無い（| 番号 | やること | 状態 | 記録 | の形で書く）")
        return probs                                   # 行が無いと、これ以降は判定できない

    for r in rows:
        if r["state"] not in (DONE, DOING, YET):
            probs.append(f"{r['no']}番の状態が「{r['state']}」＝決めた3つの言葉のどれでもない。"
                         f"使うのは {DONE} ／ {DOING} ／ {YET} の3つだけ（言い方を散らさない）")

    doing = [r for r in rows if r["state"] == DOING]
    if len(doing) > 1:
        probs.append(f"「{DOING}」が {len(doing)} 件ある（{'・'.join(r['no'] + '番' for r in doing)}）。"
                     f"同時に1件だけにする（恒久の決まり §3-3）")
    if not doing and any(r["state"] == YET for r in rows):
        probs.append(f"「{DOING}」が1件も無いのに、まだ終わっていない ToDo が残っている。"
                     f"いまやっている1件に {DOING} を付ける")

    secs, wl = worklog_sections()
    for r in rows:
        if r["state"] != DONE:
            continue
        m = re.search(r"§\s*([0-9]+(?:\.[0-9]+)?)", r["rec"])
        if not m:
            probs.append(f"{r['no']}番が {DONE} なのに、「記録」の欄に worklog の節の番号（§NN）が無い"
                         f"（いまの中身＝「{r['rec']}」）。終わったことは worklog に書いてから {DONE} にする")
        elif wl is None:
            probs.append("worklog のファイルが1本も無い（.claude/state/session_worklog_*.md）")
        elif m.group(1) not in secs:
            probs.append(f"{r['no']}番が指す §{m.group(1)} が {wl} の見出しに無い。"
                         f"worklog にその節を書いてから {DONE} にする")
    return probs


def check(transcript=None, sid=None):
    """問題があれば理由の文字列を返す。無ければ None。★2026-09-06＝見る置き場は paths_of(sid)。"""
    if not sid:
        return "セッションの id が hook の入力に無い（session_id も transcript_path も無い）＝fail-closed"
    P = paths_of(sid)
    todo, mark, shown = P["todo"], P["mark"], P["shown"]

    if not os.path.exists(todo):
        return f"このセッションの ToDo のファイルが無い（{todo}）"

    text = read(todo)

    probs = body_problems(text)
    if len(probs) == 1:
        return probs[0]
    if probs:
        return (f"中身の不足が {len(probs)} 件あります（全部 直してから貼り直してください）\n"
                + "\n".join(f"   {i}. {p}" for i, p in enumerate(probs, 1)))

    # ★前のセッションの ToDo を持ち越さない仕組みは、この中では見ません。
    #   reset_read_log.sh（SessionStart）が、自分のセッションの置き場の session_todo_posted を消します
    #   ＝印が消えるので、このセッションで貼り直すまで下の指紋の検査が落ちます。
    #   ★2026-08-16 に一度、read_log.txt の更新時刻と比べる形で書いて、間違えました。
    #     read_log.txt は SessionStart だけでなく、Read を1回するたびに record_read.sh が追記します
    #     ＝作業中にファイルを読むたびに「前のセッションのまま」と誤って止まりました。
    #     この hook の最初の実走で、私自身が止められて分かりました。
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    shown_raw = read(shown).strip()
    if shown_raw != h:                             # 古い形（ハッシュ値）で一致していれば、そのまま通す
        # ★2026-08-26＝110番の直し。CC が自分でチャットへ貼っていれば、それも「表示された」と数える。
        # ★2026-08-27＝案A。全文でなく『変わった行』でもよい（前の本文が残っているときだけ）。
        ok = False
        why = ""
        if pasted_in_chat(text, transcript):
            ok = True                              # 全文を貼った＝いままでどおり通る
        else:
            prev = read_shown_body(sid)
            if prev is None:
                why = ("★前に貼った本文が残っていない（このセッションで まだ1回も貼っていないか、"
                       "古い形の記録）。**このときは全文を貼る**")
            elif prev == text:
                # ★2026-08-27（まこさん指示「この修正をここで対応してほしい」→「２」で編集を承認）＝
                #   SHOWN は hook 自身が全文を画面に出したときにだけ本文を書く＝同じ本文なら既に
                #   まこさんの画面に出ている＝もう一度は求めない。古い形（ハッシュ値）の頃に在った
                #   「一度 止まって全文が出たら、同じ版は通る」の道の復元（案A で消えていた）。
                #   なぜ要るか＝VSCode 拡張では CC の本文が会話の記録に書かれるのがターンの終わり頃で、
                #   同じターンの中の貼り付けを hook が読めない（2026-08-27 実測・5回 止まった）。
                #   守りは減らない＝本文を1文字でも変えれば、貼るか、もう一度 止まって全文が画面に
                #   出るかの どちらかが要る。印（指紋）の検査も従来どおり（番人 N8）。
                ok = True
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
                with open(shown, "w", encoding="utf-8") as f:
                    f.write(text)                  # ★次回の差分のために本文を残す（案A）
            except Exception:
                pass
        else:
            return (why + "。いまの止まりでも全文が画面に出た。"
                    "同じ内容をチャットに貼り、印を作ってから再実行する")
    if read(mark).strip() != h:
        return "ToDo をチャットに貼った確認マーカーが無い、または ToDo を書き換えた後で貼り直していない"

    return None


def fail(reason, sid=None):
    e = sys.stderr
    print("🔒 [ToDo ゲート・safety hook] ToDo をチャットに正確に出してから作業してください。", file=e)
    print("   まこさん指示 2026-08-16「私はこのチャットにtodoを正確に表示して進めてほしいんだけど」。", file=e)
    print("", file=e)
    print(f"不足: {reason}", file=e)
    print("", file=e)
    if not sid:
        # ★2026-09-06＝id が無いときは置き場を決められない＝案内も出せない。CC は hook を外さない（決まり57番）。
        print("★セッションの id が hook の入力に無い＝ToDo の置き場を決められません。", file=e)
        print("  Claude Code の入力（session_id・transcript_path）の問題です。まこさんに報告してください。", file=e)
        print("（解除は 2026-08-16 に廃止＝合言葉では通りません）", file=e)
        sys.exit(2)
    P = paths_of(sid)
    print(f"このセッションの ToDo の置き場＝{P['todo']}", file=e)
    if os.path.exists(P["todo"]):
        print("───────── いまの ToDo（この全文をそのままチャットに貼る）─────────", file=e)
        print(read(P["todo"]), file=e)
        print("──────────────────────────────────────────────────", file=e)
        print("", file=e)
        # ★表示の記録は、全文を画面に出した「いま」だけ作る（CC は作らない・検査7の実体）
        # ★2026-08-27（案A）＝ハッシュ値ではなく本文を残す（次回の差分の材料）
        try:
            with open(P["shown"], "w", encoding="utf-8") as f:
                f.write(read(P["todo"]))
        except Exception:
            pass
    print("対処: ①ToDo を直す（上の置き場に書く）②同じ内容をチャットに貼る ③下のコマンドで印を作る ④再実行する", file=e)
    print(f'  shasum -a 256 "{P["todo"]}" | awk \'{{print $1}}\' > "{P["mark"]}"', file=e)
    print("（解除は 2026-08-16 に廃止＝合言葉では通りません）", file=e)
    sys.exit(2)


# 検査だけの実行＝止めない旗の一覧（hook 本体と番人 N12 が同じものを見る＝書き写さない）
# ★--check は 2026-09-05 に足した。足す前は、書く前に確かめる口を打とうとすると
#   この hook 自身に止められて、口が使えなかった（実測・その場で見つけた）。
PASS_FLAGS = r"--selftest|py_compile|--help|--verify|--check"


def cli_check(argv=None):
    """ToDo を書く前に、CC が自分で中身を確かめる口（2026-09-05・まこさん承認「進めて」）。

    使い方＝python3 .claude/hooks/enforce_todo_declaration.py --check [--session <セッションの id>]
    ★2026-09-06＝--session を省くと、いちばん新しく書かれた置き場を見る（並走中は別のセッションの
      ことがある）。どの置き場を見たかを1行目に必ず出す。
    ★チャットに貼ったかは見ない。貼る前に使う口なので、そこは必ず落ちるため。
      貼ったかの検査（表示の記録・印）は hook 本体では今までどおり効く＝守りは減らない。
    ★判定は body_problems（hook 本体と同じ関数）を呼ぶ＝2か所に書き写さない。
    """
    argv = list(argv or [])
    sid = None
    if "--session" in argv:
        i = argv.index("--session")
        if i + 1 < len(argv) and argv[i + 1].strip():
            sid = argv[i + 1].strip()
    if sid:
        todo = paths_of(sid)["todo"]
        how = f"--session {sid}"
    else:
        files = sorted(glob.glob(os.path.join(SESSIONS, "*", "session_todo.md")), key=os.path.getmtime)
        if not files:
            print(f"❌ セッションの置き場に ToDo が1つも無い（{SESSIONS}/*/session_todo.md）。"
                  f"--session <セッションの id> で指定するか、先に ToDo を書く")
            return 1
        todo = files[-1]
        how = "--session を省いたので、いちばん新しく書かれた置き場（並走中は別のセッションのことがある）"
    print(f"見た置き場＝{todo}（{how}）")
    if not os.path.exists(todo):
        print(f"❌ ToDo のファイルが無い（{todo}）")
        return 1
    probs = body_problems(read(todo))
    if probs:
        print(f"❌ 中身の不足 {len(probs)} 件（貼る前に全部 直す）")
        for i, p in enumerate(probs, 1):
            print(f"   {i}. {p}")
        return 1
    print("✅ 中身は通ります。このあと チャットに全文を貼り、印を作れば hook を通ります。")
    return 0


def hook_main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        sys.exit(0)                                    # 読めない入力では止めない（fail-open）

    if data.get("agent_type"):
        sys.exit(0)                                    # サブエージェントは通す（デッドロック回避）

    # ★2026-09-06＝先にセッションの id を読む。置き場（入口の例外・検査・案内）は全部 これで決まる。
    sid = session_id_of(data)
    own = ()
    if sid:
        P = paths_of(sid)
        own = (P["todo"], P["mark"])

    ti = data.get("tool_input") or {}
    cmd = ti.get("command", "") or ""
    fpath = ti.get("file_path", "") or ""

    # ★解除（TODO_OK=1）は 2026-08-16 に廃止（まこさん指示）＝通す道は無い。

    # 自分のセッションの ToDo ファイルと印の操作は通す（止めると ToDo が書けない＝デッドロック）
    # ★2026-09-06＝例外は「自分の置き場」だけ。別のセッションの置き場への書き込みは例外に入らない。
    if fpath in own or "session_todo" in cmd:
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
        if re.search(PASS_FLAGS, x):
            sys.exit(0)                                # 検査だけの実行は通す
    else:
        sys.exit(0)

    # ★2026-09-06＝id が無ければ止める（fail-closed）。固定の置き場に戻る道は作らない。
    if not sid:
        fail("セッションの id が hook の入力に無い（session_id も transcript_path も無い）＝fail-closed", None)

    reason = check(data.get("transcript_path"), sid)
    if reason:
        fail(reason, sid)
    sys.exit(0)


# ---------------- 番人（わざと壊して、止まることを確かめる） ----------------

STALE = "前のセッションの ToDo を持ち越すと止まる（SessionStart で印と表示の記録が消えるため）"
NOSHOW = "★チャットに貼らずに印だけ先に作っても止まる（2026-08-16 の穴ふさぎ）"


def selftest():
    import contextlib
    import io
    import shutil
    import tempfile

    global STATE, SESSIONS
    keep = (STATE, SESSIONS)
    tmp = tempfile.mkdtemp()
    STATE = tmp
    SESSIONS = os.path.join(tmp, "sessions")           # ★2026-09-06＝置き場も作り物の中
    SID = "A"                                          # 番人が使うセッションの id
    PA = paths_of(SID)
    TODO, MARK, SHOWN = PA["todo"], PA["mark"], PA["shown"]

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
        got = check(empty_tr, SID)
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
    got = check(pasted_tr, SID)
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
    got = check(other_tr, SID)
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
        got = check(tr("n.jsonl", chat), SID)
        good = (got is None) if want is None else (got is not None and want in got)
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た理由: {got}"))
        if not good:
            ng += 1

    # N6 古い形の記録（ハッシュ値）でも壊れない＝全文を貼れば通る
    put(new_body, mark=True, shown=True,
        shown_val=hashlib.sha256(ok_body.encode("utf-8")).hexdigest())
    got = check(tr("n6.jsonl", "```\n" + new_body + "```"), SID)
    good = got is None
    print(f"  {'✅' if good else '❌'} N6 古い形の記録（ハッシュ値）でも壊れない"
          + ("" if good else f"   ← 出た理由: {got}"))
    if not good:
        ng += 1

    # N9 記録に JSON として壊れた行が混ざっても、貼った全文は読める（1行ずつ読む直し・2026-08-27）
    put(new_body, mark=True, shown=False)
    p9 = os.path.join(tmp, "n9.jsonl")
    with open(p9, "w", encoding="utf-8") as f:
        f.write("{これは JSON として壊れた行\n")
        f.write(json.dumps({"type": "assistant",
                            "message": {"content": [{"type": "text",
                                                     "text": "```\n" + new_body + "```"}]}},
                           ensure_ascii=False) + "\n")
    got = check(p9, SID)
    good = got is None
    print(f"  {'✅' if good else '❌'} N9 壊れた行が混ざっても、貼った全文は読める"
          + ("" if good else f"   ← 出た理由: {got}"))
    if not good:
        ng += 1

    # N10 不足が2件あるとき、2件とも出る（2026-09-05・1件ずつ止まる形をやめた直し）
    two = (head + f"| 1 | a | 完了 | §33 |\n| 2 | b | {DONE} | — |\n| 3 | c | {DOING} | — |\n")
    put(two)
    got = check(empty_tr, SID)
    good = (got is not None and "2 件あります" in got
            and "3つの言葉のどれでもない" in got and "§NN" in got)
    print(f"  {'✅' if good else '❌'} N10 不足が2件あるとき、2件とも一度に出る")
    if not good:
        ng += 1

    # N11 --check（書く前の口）は中身だけを見る＝貼っていなくても中身が正しければ空
    put(ok_body, mark=False, shown=False)
    probs = body_problems(read(TODO))
    stopped = check(empty_tr, SID)
    good = (probs == [] and stopped is not None)
    print(f"  {'✅' if good else '❌'} N11 --check は中身だけを見る（貼ったかの検査は hook 本体に残る）")
    if not good:
        ng += 1

    # N12 --check のコマンド自身は、この hook に止められない（止まると口が使えない）
    good = bool(re.search(PASS_FLAGS,
                          "python3 .claude/hooks/enforce_todo_declaration.py --check"))
    print(f"  {'✅' if good else '❌'} N12 --check のコマンドは ToDo ゲートに止められない")
    if not good:
        ng += 1

    # ──────── ★2026-09-06（セッションごとの置き場）＝4件 ────────
    # N13 A に正しい ToDo・印・表示の記録が在っても、B の入力では止まる（B の置き場に ToDo が無い）。A はそのまま通る
    put(ok_body, mark=True, shown=True)
    got_b = check(empty_tr, "B")
    got_a = check(empty_tr, SID)
    good = (got_b is not None and "ファイルが無い" in got_b
            and os.path.join("sessions", "B") in got_b and got_a is None)
    print(f"  {'✅' if good else '❌'} N13 別のセッション（B）の入力では止まり、A は通ったまま（互いに影響しない）"
          + ("" if good else f"   ← B: {got_b} ／ A: {got_a}"))
    if not good:
        ng += 1

    # N14 セッションの id の読み方＝session_id → transcript_path の名前 → None。パスに使えない文字は _ に
    s_none = session_id_of({})
    s_tp = session_id_of({"transcript_path": "/x/abc.jsonl"})
    s_id = session_id_of({"session_id": "s-1"})
    s_bad = session_id_of({"session_id": "../x"})
    good = (s_none is None and s_tp == "abc" and s_id == "s-1"
            and s_bad is not None and "/" not in s_bad and ".." not in s_bad
            and session_id_of("not a dict") is None)
    print(f"  {'✅' if good else '❌'} N14 セッションの id の読み方（session_id → transcript_path → None・危ない文字は _）"
          + ("" if good else f"   ← {s_none!r} {s_tp!r} {s_id!r} {s_bad!r}"))
    if not good:
        ng += 1

    # N15 固定の置き場（旧＝.claude/state/session_todo.md）にだけ ToDo が在り、自分の置き場に無い → 止まる。理由に自分の置き場のパス
    legacy = os.path.join(STATE, "session_todo.md")
    with open(legacy, "w", encoding="utf-8") as f:
        f.write(ok_body)
    for p in (TODO, MARK, SHOWN):
        if os.path.exists(p):
            os.remove(p)
    got = check(empty_tr, SID)
    good = got is not None and TODO in got
    print(f"  {'✅' if good else '❌'} N15 固定の置き場の ToDo は読まない＝自分の置き場に無ければ止まり、理由にそのパスが在る"
          + ("" if good else f"   ← 出た理由: {got}"))
    if not good:
        ng += 1

    # N16 --check は --session A でも省略（A が最新）でも A の置き場を見て、1行目にそのパスを出す
    put(ok_body, mark=True, shown=True)
    PB = paths_of("B")
    with open(PB["todo"], "w", encoding="utf-8") as f:
        f.write(ok_body)
    os.utime(PB["todo"], (1, 1))                       # B を古くする＝A が いちばん新しい
    buf1, buf2 = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf1):
        rc1 = cli_check(["--check", "--session", SID])
    with contextlib.redirect_stdout(buf2):
        rc2 = cli_check(["--check"])
    l1 = (buf1.getvalue().splitlines() or [""])[0]
    l2 = (buf2.getvalue().splitlines() or [""])[0]
    good = rc1 == 0 and rc2 == 0 and TODO in l1 and TODO in l2 and "見た置き場" in l1
    print(f"  {'✅' if good else '❌'} N16 --check は見た置き場を1行目に出す（--session A／省略＝いちばん新しい A）"
          + ("" if good else f"   ← rc={rc1},{rc2} ／ {l1} ／ {l2}"))
    if not good:
        ng += 1

    # ToDo ファイルが無いときも止まる
    os.remove(TODO)
    got = check(empty_tr, SID)
    good = got is not None and "ファイルが無い" in got
    print(f"  {'✅' if good else '❌'} ToDo のファイルが無いと止まる")
    if not good:
        ng += 1

    # ──────── ★2026-09-06（実経路・2件）＝この .py 自身と reset_read_log.sh を subprocess で呼ぶ ────────
    #   壊すプログラム（.claude/breaks）は承認が増えるので作らない（まこさん指示「何回も承認させるな」）。
    #   本物の .claude/state/sessions/ の下に一時の id の置き場を作り、終わったら必ず消す。
    import subprocess
    real_state, real_sessions = keep
    sa, sb = f"selftest_A_{os.getpid()}", f"selftest_B_{os.getpid()}"
    da, db = os.path.join(real_sessions, sa), os.path.join(real_sessions, sb)
    body17 = head + f"| 1 | a | {DOING} | — |\n| 2 | b | {YET} | — |\n"   # ✅済 の行を入れない＝worklog に頼らない

    def real_put(d, body):
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "session_todo.md"), "w", encoding="utf-8") as f:
            f.write(body)
        hh = hashlib.sha256(body.encode("utf-8")).hexdigest()
        for nm in ("session_todo_posted", "session_todo_shown"):
            with open(os.path.join(d, nm), "w", encoding="utf-8") as f:
                f.write(hh)

    def call_hook(payload):
        r = subprocess.run([sys.executable, os.path.abspath(__file__)],
                           input=json.dumps(payload, ensure_ascii=False), capture_output=True, text=True)
        return r.returncode, r.stderr

    try:
        os.makedirs(da, exist_ok=True)
        os.makedirs(db, exist_ok=True)
        tr17 = os.path.join(da, "tr.jsonl")               # 会話の記録は作り物（本物を読ませない）
        with open(tr17, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "assistant",
                                "message": {"content": [{"type": "text", "text": "なにも貼っていない"}]}},
                               ensure_ascii=False) + "\n")

        def inp(sid_):
            return {"session_id": sid_, "transcript_path": tr17, "tool_name": "Write",
                    "tool_input": {"file_path": os.path.join(da, "dummy.md"), "content": "x"}}

        # N17 ①A 通る ②B 止まる（案内は B の置き場・固定の置き場は出ない）③B が書けば両方 通る ④id なしは止まる
        real_put(da, body17)
        rc1, _ = call_hook(inp(sa))
        rc2, err2 = call_hook(inp(sb))
        ok2 = (rc2 == 2 and os.path.join(db, "session_todo.md") in err2
               and os.path.join(".claude", "state", "session_todo.md") not in err2)
        real_put(db, body17.replace("| a |", "| z |"))
        rc3b, _ = call_hook(inp(sb))
        rc3a, _ = call_hook(inp(sa))
        rc4, err4 = call_hook({"tool_name": "Write",
                               "tool_input": {"file_path": os.path.join(da, "dummy.md"), "content": "x"}})
        ok4 = rc4 == 2 and "セッションの id" in err4
        good = rc1 == 0 and ok2 and rc3b == 0 and rc3a == 0 and ok4
        print(f"  {'✅' if good else '❌'} N17 実経路＝①A 0 ②B 2＋B の置き場の案内 ③B 0・A 0 ④id なし 2＋「セッションの id」"
              + ("" if good else f"   ← rc1={rc1} rc2={rc2} ok2={ok2} rc3b={rc3b} rc3a={rc3a} rc4={rc4} ok4={ok4}"))
        if not good:
            ng += 1

        # N18 SessionStart（reset_read_log.sh）＝A の印と表示の記録だけ消え、B は残る。共有のファイル13本は控えて戻す
        reset_sh = os.path.join(ROOT, ".claude", "hooks", "reset_read_log.sh")
        shared = [os.path.join(real_state, n) for n in (
            "read_log.txt", "budget_rule_shown", "banned_words_checked", "analysis_block.md",
            "improvement_plan.md", "fastmode_trades_seen", "fastmode_e37_seen", "fastmode_ledger_seen",
            "worklog_ok", "fastmode_record_pending", "comprehension_check.md", "flow_declaration_posted",
            "goal_block.md")]
        saved = {p: (open(p, "rb").read() if os.path.exists(p) else None) for p in shared}
        real_put(da, body17)
        real_put(db, body17)
        out18 = ""
        try:
            r = subprocess.run(["bash", reset_sh],
                               input=json.dumps({"session_id": sa, "transcript_path": tr17,
                                                 "hook_event_name": "SessionStart"}),
                               capture_output=True, text=True)
            out18 = r.stdout
        finally:
            restore_ok = True
            for p, b in saved.items():
                try:
                    if b is None:
                        if os.path.exists(p):
                            os.remove(p)
                    else:
                        with open(p, "wb") as f:
                            f.write(b)
                except Exception:
                    restore_ok = False
            for p, b in saved.items():
                cur = open(p, "rb").read() if os.path.exists(p) else None
                if cur != b:
                    restore_ok = False
        a_gone = (not os.path.exists(os.path.join(da, "session_todo_posted"))
                  and not os.path.exists(os.path.join(da, "session_todo_shown")))
        b_kept = (os.path.exists(os.path.join(db, "session_todo_posted"))
                  and os.path.exists(os.path.join(db, "session_todo_shown")))
        good = a_gone and b_kept and os.path.join(da, "session_todo.md") in out18 and restore_ok
        print(f"  {'✅' if good else '❌'} N18 実経路＝SessionStart は自分（A）の印と表示の記録だけ消し、B は残す。置き場のパスを画面に出す。共有のファイル13本は元どおり"
              + ("" if good else f"   ← a_gone={a_gone} b_kept={b_kept} path_shown={os.path.join(da, 'session_todo.md') in out18} restore_ok={restore_ok}"))
        if not restore_ok:
            print("  🔴 N18＝共有のファイルを元に戻せなかった。.claude/state を git diff で確かめて、まこさんに報告する", file=sys.stderr)
        if not good:
            ng += 1
    finally:
        shutil.rmtree(da, ignore_errors=True)
        shutil.rmtree(db, ignore_errors=True)

    shutil.rmtree(tmp, ignore_errors=True)
    STATE, SESSIONS = keep
    # 末尾の +1 ＝ N9（2026-08-27）／+3 ＝ N10・N11・N12（2026-09-05）／+4 ＝ N13〜N16／+2 ＝ N17・N18（2026-09-06）
    total = len(cases) + 3 + len(n_cases) + 1 + 1 + 3 + 4 + 2
    print(f"\n番人: {total - ng}/{total} pass")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    if "--check" in sys.argv:
        sys.exit(cli_check(sys.argv[1:]))
    hook_main()
