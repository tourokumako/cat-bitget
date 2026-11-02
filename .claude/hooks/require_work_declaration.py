#!/usr/bin/env python3
"""require_work_declaration — ToDo の1件を始める前に、宣言と まこさんの返事を求める（2026-10-12 新設・172回目）。

まこさん指示（逐語 2026-10-12）＝「読んだのかを確認するためにも、作業を始める前に、作業内容、目的、経緯、ゴールを宣言するように強制する」
流れ（まこさん・同日・逐語）＝「必読読んで→todo書いて→そのtodoでこれから始める作業に対し【作業内容、目的、経緯、ゴール】を宣言するという流れだよね」
返事を待つか（まこさん・同日・逐語）＝「入れる」。

決まり（3つ。全部そろえば最初から通る。そろわなければ、何回 打っても通らない＝「1回 止まれば通る」作りは入れない）
  1. このセッションの ToDo（.claude/state/sessions/<セッションの id>/session_todo.md）に「★いまここ」の行が、ちょうど1つ在る。
  2. その番号の宣言が、CC の返信に在る。形＝「【宣言】ToDo の N番」と、【作業内容】【目的】【経緯】【ゴール】の4つ（どれも中身つき）。
  3. その宣言より後に、まこさんの発言が在る（hook の差し戻しの文・途中で止めた印は数えない）。
  4. ★2026-10-24（212回目・まこさん「次回セッションでインプットしろ」「強制するレベルだ」「読むだけではだめ」「理解できてるのか証拠をだすようにしろ」「やれ」）
     ＝必読の一覧（must_read_now.txt）のファイルを、このセッションで Read で開いた記録（sessions/<id>/read_log.txt）が在る。
     かつ、宣言の中に、必読のファイルごとに根拠「<ファイル名>:<行番号>「<その行の逐語・10字以上>」」が1つ以上在り、
     逐語がそのファイルの、その行の前後3行に1文字も違わずに在る（211回目・212回目に、必読を開いても使わずに設計書を作れなかった）。
     ★2026-11-01（202番）＝根拠を照らすのは、宣言ごとに1回。まこさんの返事の後に1回 合った宣言は、同じ宣言・同じ必読の一覧の間は
     照らし直さない（作業が根拠の行を書き替えても止めない）。新しい宣言と、必読の一覧が変わったときは照らす（_evid_key・EVID_OK）。
止めるもの＝Write・Edit・MultiEdit・NotebookEdit・読むだけでない Bash・Agent。
止めないもの＝読む操作／検査だけの実行（--selftest・--verify・--check・--help・--dry・try_hooks.py・next_move.py。--write の付く物は除く）／
  セッションの置き場（ToDo）・worklog・memory・計画のファイルへの書き込み／サブエージェント／記録が読めないとき／
  引き継ぎの文書の元データ（next_step_src.json）への書き込みと、next_step を作り直す操作（tidy_next_step.py）／
  ★2026-10-17 から＝監査のセッション（require_read_used._auditor_session で見分ける）／読むだけの調べ（作業場と /tmp への書き出し・
  git -C の読む命令・git check-ignore）。検査だけの実行と読むだけの調べは、コマンドの区切りごとに見る（check_or_read）。

なぜこの形か（worklog 20261001 §14）＝前の ToDo の hook（enforce_todo_declaration）は、7日で232回 止め、うち96回は同じ操作の繰り返しで通った。
  原因＝①全文を画面に出すために必ず1回 止まる ②同じ返信の中の貼り付けを、hook が読めないことが在る ③書き替えるたびに、貼る手続きと証拠のファイルが要る。
  この hook は、宣言を「前の返信」に書かせ、まこさんの返事の後に作業を始める形＝①②③が起きない。証拠のファイルも要らない。

限界（正直に）＝宣言の中身が正しいかは見ない（まこさんが読む）。CC が「★いまここ」を動かさずに別の作業をすれば、止まらない。
  ToDo の番号を付け替えると、前の番号の宣言が別の行に当たる＝セッションの中で番号を付け替えない（行は末尾に足す）。

使い方: （hook）標準入力に PreToolUse の JSON ／ --selftest 見本の記録で、止まる場合と通る場合を試す
"""
import json
import pathlib
import re
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from require_check_after_failure import ACT_TOOLS, is_read, bash_is_read  # 読むだけの判定を、動いている hook と同じものにする
from require_read_used import _auditor_session  # 監査のセッションの見分け方を1か所にする（2026-10-17）
from transcript_rows import rows                # 記録は会話の本物の行だけを読む

ROOT = HERE.parent.parent
SESSIONS = ROOT / ".claude" / "state" / "sessions"
# ★2026-10-12（172回目）＝引き継ぎの文書の元データ（next_step_src.json）も、記録と同じ扱いで通す。
#   なぜ＝1件が済んで「★いまここ」を次の番号へ移した後に、締めの手順（ToDo の表を写す → next_step を作り直す）が打てなくなるため。
FREE = ("/.claude/plans/", "session_worklog_", "/.claude/state/sessions/", "/memory/", "/.claude/state/next_step_src.json")
NOT_USER = ("Stop hook feedback", "<task-notification>", "<system-reminder>", "This session is being continued",
            "[Request interrupted")
HEADS = ("【作業内容】", "【目的】", "【経緯】", "【ゴール】")
DECL_RE = re.compile(r"【宣言】\s*ToDo\s*の?\s*(\d+)\s*番")
DOING = "★いまここ"
CHECK_ONLY = re.compile(r"--(?:selftest|verify|check|help|dry)(?=\s|$)|-m\s+py_compile(?=\s|$)|try_hooks\.py(?=\s|$)|next_move\.py(?=\s|$)")
# ★2026-10-18（監査 CP79 の修正）＝旗は丸ごと一致で見る（--checkpoint-and-save の --check を検査の旗と見ていた）。
#   旗の中身（その道具が本当に書かないか）は見ない＝防げない物（hook_inventory_src.json に書く）
TMP_OUT = re.compile(r"\d?>>?\s*(/private)?/tmp/\S+")            # 作業場と /tmp への書き出し（2026-10-17）
GIT_EXTRA = re.compile(r"^git\s+check-ignore(\s|$)")               # 無視される置き場かを見るだけ（2026-10-17）
TOOL_CHECK = re.compile(r"^python[0-9.]*\s+\S*(try_hooks|next_move)\.py(\s|$)")  # 書き込まない道具（2026-10-17）
MIN_BODY = 8                                   # 見出しの後の中身の字数の下限（見出しだけの宣言を通さない）
FILE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
MUST_FILE = ROOT / ".claude" / "state" / "must_read_now.txt"   # 必読の一覧（tidy_next_step.py が next_step の必読の表から書く）
EVID_MIN = 10                                  # 根拠の逐語の字数の下限
EVID_WIN = 3                                   # 逐語を探す、行番号の前後の行の数


def must_list() -> list:
    """必読の一覧（「#」の行と空の行は読み飛ばす）。一覧が無ければ空＝決まり4は掛けない。"""
    if not MUST_FILE.exists():
        return []
    return [ln.strip() for ln in MUST_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")]


def must_problems(todo: pathlib.Path, decl: str) -> list:
    """決まり4（2026-10-24）。必読を Read で開いた記録と、宣言の中の必読ごとの根拠を照らす。戻り＝足りない所の一覧（空＝足りている）。"""
    log = todo.parent / "read_log.txt"
    seen = {s.strip() for s in log.read_text(encoding="utf-8", errors="replace").splitlines()} if log.exists() else set()
    probs = []
    for p in must_list():
        full = p if p.startswith("/") else str(ROOT / p)
        name = pathlib.Path(p).name
        if full not in seen:
            probs.append(f"{name} を、このセッションで Read で開いた記録が無い")
            continue
        try:
            lines = pathlib.Path(full).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            probs.append(f"{name} が読めない")
            continue
        ok = False
        pat = re.escape(name) + r":(\d+)[^\n「]{0,20}「([^」\n]{%d,})」" % EVID_MIN
        for m in re.finditer(pat, decl):
            n, q = int(m.group(1)), m.group(2)
            if q in "\n".join(lines[max(0, n - 1 - EVID_WIN): n + EVID_WIN]):
                ok = True
                break
        if not ok:
            probs.append(f"宣言に {name} の根拠「{name}:行番号「その行の逐語（{EVID_MIN}字以上）」」が無いか、"
                         f"逐語がその行の前後{EVID_WIN}行に無い")
    return probs


# ★2026-11-01（235回目・202番・まこさん「それで修正して」「よい」）＝根拠を照らすのは、宣言ごとに1回。
#   直す前は、道具を呼ぶたびに、根拠をいまのファイルと照らし直した。必読の一覧には作業で直すファイル（やることの表・設計書ほか）が
#   入るので、まこさんの OK の後に作業が根拠の行を書き替えると、OK をいただいた作業そのものを止めた（同じ形が6回・worklog 20261101 §14-7）。
#   いまは、まこさんの返事の後に根拠が1回 合った宣言を、セッションの置き場に記録し、同じ宣言・同じ必読の一覧の間は照らし直さない。
#   新しい宣言と、必読の一覧が変わったときは、いままでどおり、いまのファイルと照らす。
EVID_OK = "decl_evidence_ok.json"


def _evid_key(decl: str, must: list) -> str:
    """宣言の文と必読の一覧から作る鍵（どちらかが変われば別の鍵＝照らし直す）。"""
    import hashlib
    return hashlib.sha256((decl + "\n\0\n" + "\n".join(must)).encode("utf-8")).hexdigest()


def _evid_seen(todo: pathlib.Path, key: str) -> bool:
    """その鍵の宣言の根拠が、前に照らして合ったか（記録が読めなければ、合っていない扱い＝照らす）。"""
    try:
        return key in json.loads((todo.parent / EVID_OK).read_text(encoding="utf-8"))
    except Exception:
        return False


def _evid_write(todo: pathlib.Path, key: str) -> None:
    """根拠が合った宣言の鍵を記録に足す（書けなくても止めない＝次も照らすだけ）。"""
    f = todo.parent / EVID_OK
    try:
        keys = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
        if key not in keys:
            f.write_text(json.dumps(keys + [key], ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def session_id(d: dict):
    sid = d.get("session_id")
    if not (isinstance(sid, str) and sid.strip()):
        tp = str(d.get("transcript_path") or "")
        sid = pathlib.Path(tp).name[:-6] if tp.endswith(".jsonl") else ""
    sid = re.sub(r"[^A-Za-z0-9._-]", "_", (sid or "").strip()).lstrip(".")
    return sid or None


def doing_numbers(todo_text: str) -> list:
    """ToDo の表の、状態が「★いまここ」の行の番号の一覧（表の形＝| 番号 | やること | 状態 | 記録 |）。"""
    out = []
    for line in todo_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) >= 3 and re.fullmatch(r"\d+", cells[0]) and cells[2] == DOING:
            out.append(cells[0])
    return out


def events(path: pathlib.Path) -> list:
    """戻り＝[("user", None) | ("say", CC の返信の文)] を、記録の順に。サブエージェントの行は数えない。"""
    out = []
    for o in rows(path):                           # ★2026-10-18（監査 CP79）＝記録は共通の rows() で読む（同じ uuid は1回・会話の本物の行だけ）
        if o.get("isSidechain"):
            continue
        if o.get("type") == "user":
            c = (o.get("message") or {}).get("content")
            if isinstance(c, str):
                texts = [c]
            elif isinstance(c, list):
                texts = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
            else:
                texts = []
            if any(t.strip() and not t.lstrip().startswith(NOT_USER) for t in texts):
                out.append(("user", None))
        elif o.get("type") == "assistant":
            for b in (o.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "text" and b.get("text"):
                    out.append(("say", b["text"]))
    return out


def decl_problems(text: str, num: str):
    """1つの返信の文が、num 番の宣言として足りているか。戻り＝足りない所の一覧（空＝足りている）／None＝num 番の宣言ではない。"""
    hits = [m for m in DECL_RE.finditer(text) if m.group(1) == num]
    if not hits:
        return None
    body = text[hits[-1].start():]
    pos = [(h, body.find(h)) for h in HEADS]
    probs = []
    for h, p in pos:
        if p < 0:
            probs.append(f"{h} が無い")
            continue
        nxt = min([q for _, q in pos if q > p] + [len(body)])
        if len(re.sub(r"\s", "", body[p + len(h):nxt])) < MIN_BODY:
            probs.append(f"{h} の中身が {MIN_BODY} 字より短い")
    return probs


def check(transcript: pathlib.Path, todo: pathlib.Path):
    """止める理由（文）を返す。通すときは None。"""
    if not todo.exists():
        return f"このセッションの ToDo が無い（{todo}）。ToDo を書き、いまやる1件に「{DOING}」を付ける"
    nums = doing_numbers(todo.read_text(encoding="utf-8", errors="replace"))
    if len(nums) != 1:
        return (f"ToDo の「{DOING}」が {len(nums)} 件（ちょうど1件にする）＝{todo}。"
                f"数えるのは、表の状態の欄が「{DOING}」の文字だけの行（説明を足すと数えない）")
    num = nums[0]
    ev = events(transcript)
    last = None                                # いちばん新しい num 番の宣言の（場所, 足りない所）
    for i, e in enumerate(ev):
        if e[0] != "say":
            continue
        probs = decl_problems(e[1], num)
        if probs is None:
            continue
        if not probs and any(x[0] == "user" for x in ev[i + 1:]):
            key = _evid_key(e[1], must_list())
            if _evid_seen(todo, key):
                return None                    # ★2026-11-01（202番）＝この宣言の根拠は前に照らして合った（作業で行が動いても止めない）
            mp = must_problems(todo, e[1])     # ★2026-10-24＝決まり4（必読を開いた記録と、宣言の中の根拠）
            if not mp:
                _evid_write(todo, key)         # 合った宣言を記録する（同じ宣言・同じ必読の一覧の間は、照らし直さない）
                return None                    # 足りている宣言が在り、その後に まこさんの発言が在る
            probs = ["必読の証拠＝" + x for x in mp]
        last = (i, probs)
    if last is None:
        return f"ToDo の {num}番の宣言が、CC の返信に無い"
    if last[1]:
        return f"ToDo の {num}番の宣言が足りない＝" + "／".join(last[1])
    return f"ToDo の {num}番の宣言の後に、まこさんの返事が まだ無い"


def check_or_read(cmd: str) -> bool:
    """★2026-10-17（183回目・まこさん「要とし、CCの案で修正する」）＝コマンドを区切り（&&・||・;・|・改行）ごとに見て、
      全部が「検査だけの実行」か「読むだけの調べ」なら通す。直す前は、コマンドのどこかに --check などの文字が在れば通したので、
      後ろに書き込みをつないでも通った。引用符の中は見ない（試しの道具の --bash "…" の中の --write を数えない）。
      読むだけの調べに足した物＝作業場と /tmp への書き出し・git -C <置き場> <読む命令>・git check-ignore
      （直近7日で、中身は読むだけの調べを5回 止めていた）。$( ) と for のくり返しは広げない（中で何が走るかを決められない）。"""
    c = re.sub(r"'[^']*'|\"[^\"]*\"", "''", str(cmd or ""))
    c = TMP_OUT.sub(" ", c)
    if re.search(r">(?!\s*/dev/null|&)", c.replace("2>&1", "")):
        return False                            # 作業場と /tmp の外への書き出しは止める
    for seg in re.split(r"&&|\|\||;|\||\n", c):
        s = re.sub(r"^\s*(time|timeout\s+\d+)\s+", "", seg).strip()
        s = re.sub(r"^git\s+-C\s+\S+\s+", "git ", s)
        if not s or bash_is_read(s) or GIT_EXTRA.match(s):
            continue
        if TOOL_CHECK.match(s):
            continue
        if re.match(r"python[0-9.]*\s+(?!-c\b|-\s|-$)", s) and CHECK_ONLY.search(s) and "--write" not in s:
            continue                                # python3 -c と python3 - は、.py が無いので検査だけの実行と見ない（2026-10-18）
        return False
    return True


# ★2026-11-02（240回目・まこさん「コミットに対して上記のような宣言は不要だよね？」「これは今修正できない？」「ok」）
#   ＝コミットは、対象をお見せして まこさんの「コミットOK」をいただけば足りる。コミットはファイルの中身を変えないので、宣言を求めない。
COMMIT_OK = re.compile(r"コミット\s*(?:OK|ok|Ok|ＯＫ)")
COMMIT_SEG = re.compile(r"^git\s+(?:-C\s+\S+\s+)?(?:add|commit)(?:\s|$)")
COMMIT_BAD = re.compile(r"\bgit\s+(?:-C\s+\S+\s+)?add\s+(?:-A|--all|\.)(?:\s|$)|--amend\b")


def commit_only(cmd: str) -> bool:
    """コマンドが git add と git commit と、読むだけの操作でできているか。
    git add -A・git add .・--amend と、ファイルへの書き出しをつないだコマンドは、コミットだけと見ない。"""
    c = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?^\1[ \t]*$", " ", str(cmd or ""), flags=re.S | re.M)   # ヒアドキュメントの中身は見ない
    c = re.sub(r"'[^']*'|\"[^\"]*\"", "''", c)
    if COMMIT_BAD.search(c) or re.search(r">(?!\s*/dev/null|&)", c.replace("2>&1", "")):
        return False
    found = False
    for seg in re.split(r"&&|\|\||;|\||\n", c):
        s = seg.strip()
        if COMMIT_SEG.match(s):
            found = True
        elif s and not re.match(r"^cd\s+\S+$", s) and not bash_is_read(s):
            return False
    return found


def last_user_ok_commit(path: pathlib.Path) -> bool:
    """まこさんの直前の発言に「コミットOK」が在るか（hook の差し戻しと道具の結果は発言に数えない）。"""
    last = ""
    for o in rows(path):
        if o.get("isSidechain") or o.get("type") != "user":
            continue
        c = (o.get("message") or {}).get("content")
        texts = [c] if isinstance(c, str) else [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"] if isinstance(c, list) else []
        said = [t for t in texts if t.strip() and not t.lstrip().startswith(NOT_USER)]
        if said:
            last = "\n".join(said)
    return bool(COMMIT_OK.search(last))


def gate(d: dict):
    """止める理由（文）を返す。通すときは None。"""
    if d.get("agent_type"):
        return None                            # サブエージェントは通す
    name, inp = d.get("tool_name"), d.get("tool_input") or {}
    if name not in ACT_TOOLS or is_read(name, inp):
        return None
    p = str(inp.get("file_path") or inp.get("notebook_path") or "")
    if name in FILE_TOOLS and any(k in p for k in FREE):
        return None
    if name == "Bash":
        cmd = str(inp.get("command", ""))
        if check_or_read(cmd):
            return None                        # 検査だけの実行と、読むだけの調べは通す（区切りごとに見る・2026-10-17）
        if re.search(r"\bpython[0-9.]*\s+\S*tidy_next_step\.py(\s|$)", cmd):
            return None                        # ★2026-10-12＝引き継ぎの文書（next_step）を作り直す操作は、記録と同じ扱いで通す
    tp, sid = d.get("transcript_path"), session_id(d)
    if not tp or not sid or not pathlib.Path(tp).exists():
        return None                            # 記録が読めないときは止めない（判定できないため）
    # ★2026-10-17（183回目・まこさん「監査にはあてない」）＝監査のセッション（別のセッションで依頼書を渡して動かすもの）は止めない。
    #   見分け方は require_read_used._auditor_session と同じ（決まりを1か所にする）。
    if _auditor_session(list(rows(pathlib.Path(tp)))):
        return None
    if name == "Bash" and commit_only(str(inp.get("command", ""))) and last_user_ok_commit(pathlib.Path(tp)):
        return None                            # コミットだけで、直前の発言が「コミットOK」なら、宣言を求めない（2026-11-02）
    return check(pathlib.Path(tp), SESSIONS / sid / "session_todo.md")


def hook() -> int:
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    reason = gate(d if isinstance(d, dict) else {})
    if not reason:
        return 0
    print(f"🔒 [宣言が無い・hook require_work_declaration] {reason}\n"
          "   ToDo の1件を始める前に、返信に次の形で宣言を書き、まこさんの返事の後に作業を始めてください"
          "（まこさん指示 2026-10-12）。\n"
          "     【宣言】ToDo の N番\n     【作業内容】…\n     【目的】…\n     【経緯】…\n     【ゴール】…\n"
          "   ★宣言には、必読の一覧（.claude/state/must_read_now.txt）のファイルごとに、根拠を1つ以上書く＝"
          "<ファイル名>:<行番号>「<その行の逐語・10字以上>」。必読は先に Read で開く"
          "（まこさん 2026-10-24「読むだけではだめ」「理解できてるのか証拠をだすようにしろ」）。\n"
          "   止めないもの＝読む操作・検査だけの実行・ToDo と worklog と memory への書き込み。\n"
          "   同じ操作を打ち直しても通りません（宣言と返事がそろうまで）。", file=sys.stderr)
    return 2


# ── 見本の記録で試す ─────────────────────────────────────────────
def _say(t):
    return json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": t}]}}, ensure_ascii=False)


def _user(t):
    return json.dumps({"type": "user", "message": {"content": t}}, ensure_ascii=False)


def _result():
    return json.dumps({"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}},
                      ensure_ascii=False)


def selftest() -> int:
    decl3 = ("【宣言】ToDo の 3番\n【作業内容】設計書の元の形の直す所を一覧にする\n【目的】どの工事でも同じ形で設計書を作れるようにする\n"
             "【経緯】171回目に項目の表が固まり、172回目に続きを進める\n【ゴール】直す所の一覧を返信に出して止まる")
    todo3 = "| 番号 | やること | 状態 | 記録 |\n|---|---|---|---|\n| 2 | 前の件 | ✅済 | §1 |\n| 3 | いまの件 | ★いまここ | — |\n| 4 | 次の件 | まだ | — |\n"
    ng = 0
    global MUST_FILE
    with tempfile.TemporaryDirectory() as td:
        tdp = pathlib.Path(td)
        tr, todo = tdp / "t.jsonl", tdp / "session_todo.md"
        MUST_FILE = tdp / "must_none.txt"           # T1〜T28 は決まり4を掛けない（必読の一覧が無い＝掛けない）

        def run(name, lines, todo_text, want_block, d=None):
            nonlocal ng
            tr.write_text("\n".join(lines) + "\n", encoding="utf-8")
            if todo_text is None:
                todo.unlink(missing_ok=True)
            else:
                todo.write_text(todo_text, encoding="utf-8")
            got = check(tr, todo) if d is None else gate(d)
            ok = bool(got) == want_block
            ng += 0 if ok else 1
            print(f"  {'✅' if ok else '❌'} {name}＝{'止まる' if got else '通る'}" + (f"（{got[:50]}）" if got else ""))

        run("T1 ToDo が無い → 止まる", [_user("始めて")], None, True)
        run("T2 宣言が無い → 止まる", [_user("始めて"), _say("読みました")], todo3, True)
        run("T3 宣言は在るが、返事が無い → 止まる", [_user("始めて"), _say(decl3)], todo3, True)
        run("T4 宣言の後に返事が在る → 通る", [_user("始めて"), _say(decl3), _user("OK")], todo3, False)
        run("T5 別の番号の宣言 → 止まる", [_user("始めて"), _say(decl3.replace("3番", "2番")), _user("OK")], todo3, True)
        run("T6 ゴールが無い宣言 → 止まる", [_say(decl3.split("【ゴール】")[0]), _user("OK")], todo3, True)
        run("T7 見出しだけの宣言 → 止まる",
            [_say("【宣言】ToDo の 3番\n【作業内容】\n【目的】\n【経緯】\n【ゴール】"), _user("OK")], todo3, True)
        run("T8 宣言の後が、道具の結果と hook の差し戻しだけ → 止まる",
            [_say(decl3), _result(), _user("Stop hook feedback: やり直し")], todo3, True)
        run("T9 ★いまここ が2件 → 止まる", [_say(decl3), _user("OK")], todo3.replace("まだ", "★いまここ"), True)
        base = {"transcript_path": str(tr), "session_id": "x"}
        run("T10 読むだけの Bash → 通る", [_user("始めて")], None, False,
            dict(base, tool_name="Bash", tool_input={"command": "grep -n abc file.md"}))
        run("T11 ToDo のファイルへの書き込み → 通る", [_user("始めて")], None, False,
            dict(base, tool_name="Write", tool_input={"file_path": str(SESSIONS / "x" / "session_todo.md")}))
        run("T12 検査だけの実行 → 通る", [_user("始めて")], None, False,
            dict(base, tool_name="Bash", tool_input={"command": "python3 .claude/tools/tidy_next_step.py --selftest"}))
        run("T13 宣言なしで、ふつうのファイルへの書き込み → 止まる", [_user("始めて")], None, True,
            dict(base, tool_name="Edit", tool_input={"file_path": "/tmp/a.py"}))
        # ★2026-10-17（183回目）＝区切りごとに見る・読むだけの調べ・監査のセッション
        def bash(c):
            return dict(base, tool_name="Bash", tool_input={"command": c})
        run("T14 検査の旗の後ろに書き込みをつなぐ → 止まる", [_user("始めて")], None, True,
            bash("python3 x.py --check; cp a b"))
        run("T15 試しの道具の引用符の中の --write → 通る", [_user("始めて")], None, False,
            bash('python3 .claude/tools/try_hooks.py --session x --bash "python3 y.py --write"'))
        run("T16 作業場への書き出し → 通る", [_user("始めて")], None, False,
            bash("git status --short > /private/tmp/claude-501/x/s.txt; wc -l /private/tmp/claude-501/x/s.txt"))
        run("T17 作業場の外への書き出し → 止まる", [_user("始めて")], None, True,
            bash("git status --short > .claude/state/s.txt"))
        run("T18 git -C の読む命令 → 通る", [_user("始めて")], None, False,
            bash("git -C /a/b log --oneline -3 && shasum -a 256 x.md"))
        run("T19 git check-ignore → 通る", [_user("始めて")], None, False, bash("git check-ignore -v a.md"))
        commit = "git add a.py b.md && git commit -q -F - <<'EOF'\nchore: a > b と書いた文\n\nEOF\ngit log -1 --oneline"
        run("C1 直前の発言が「コミットOK」で、コミットだけ → 通る", [_user("コミットOK")], None, False, bash(commit))
        run("C2 「コミットOK」が無いコミット → 止まる", [_user("始めて")], None, True, bash(commit))
        run("C3 コミットと一緒にファイルへ書き出す → 止まる", [_user("コミットOK")], None, True,
            bash("git add a.py && echo x > b.txt && git commit -m 'x'"))
        run("C4 前の発言の「コミットOK」で、直前の発言には無い → 止まる",
            [_user("コミットOK"), _say("済みました"), _user("次へ")], None, True, bash(commit))
        run("C5 git add -A → 止まる", [_user("コミットOK")], None, True, bash("git add -A && git commit -m 'x'"))
        run("C6 --amend → 止まる", [_user("コミットOK")], None, True, bash("git commit --amend -m 'x'"))
        run("T20 time を付けた自己テスト → 通る", [_user("始めて")], None, False,
            bash("time python3 a.py --selftest 2>&1 | tail -3"))
        run("T21 最初の発言に依頼書のパス（監査のセッション）・ToDo が無い → 通る",
            [_user("監査してほしい v3/.claude/audits/inputs/2026-10-13_x_impl_cp78_audit_request.md")], None, False,
            bash("cp a b"))
        run("T22 最初の発言が「監査して」で始まる（IDE の塊つき）・ToDo が無い → 通る",
            [_user("<ide_opened_file>The user opened a.md</ide_opened_file>\n監査して 実装の監査の依頼書 CP76")], None, False,
            bash("cp a b"))
        run("T23 最初の発言が【相談】で始まる（普通のセッション）・ToDo が無い → 止まる",
            [_user("【相談】監査の依頼書の作り方")], None, True, bash("cp a b"))
        # ★2026-10-18（監査 CP79 の修正）＝旗の名前だけで通っていた2つの形と、直した後も通る（防げない物）1つの形
        run("T24 python3 -c の書き込みに --check を付ける → 止まる", [_user("始めて")], None, True,
            bash("python3 -c \"open('/tmp/zz','w').write('a')\" --check"))
        run("T25 --check で始まる別の旗（--checkpoint-and-save）→ 止まる", [_user("始めて")], None, True,
            bash("python3 x.py --checkpoint-and-save"))
        run("T26 .py に検査の旗だけ → 通る（旗の中身は見ない＝防げない物）", [_user("始めて")], None, False,
            bash("python3 x.py --check"))
        # ★2026-10-18（監査 CP79）＝find -delete・sort -o を読むだけと見ていた穴（require_check_after_failure.bash_is_read の直しで止まる）
        run("T27 find -delete → 止まる", [_user("始めて")], None, True, bash("find /tmp/x -name a.md -delete"))
        run("T28 sort -o → 止まる", [_user("始めて")], None, True, bash("sort -o /tmp/out.txt /tmp/in.txt"))
        # ★2026-10-24（212回目）＝決まり4（必読を開いた記録と、宣言の中の根拠）
        doc = tdp / "doc.md"
        doc.write_text("見出しの行\n要件の一行目はここに在ります\n二行目は閾値とパラメータの範囲を書く所です\n", encoding="utf-8")
        MUST_FILE = tdp / "must.txt"
        MUST_FILE.write_text("# 見出し\n" + str(doc) + "\n", encoding="utf-8")
        log = tdp / "read_log.txt"
        good = decl3 + "\n根拠＝doc.md:3「二行目は閾値とパラメータの範囲を書く所です」"
        log.unlink(missing_ok=True)
        run("T29 必読を Read で開いた記録が無い → 止まる", [_say(good), _user("OK")], todo3, True)
        log.write_text(str(doc) + "\n", encoding="utf-8")
        run("T30 開いた記録は在るが、宣言に根拠が無い → 止まる", [_say(decl3), _user("OK")], todo3, True)
        run("T31 開いた記録と、行の前後に在る逐語の根拠 → 通る", [_say(good), _user("OK")], todo3, False)
        run("T32 根拠の逐語が、その行の前後に無い → 止まる",
            [_say(decl3 + "\n根拠＝doc.md:3「ファイルのどこにも無い文をここに書きました」"), _user("OK")], todo3, True)
        # ★2026-11-01（202番・まこさん「よい」）＝根拠を照らすのは、宣言ごとに1回（作業が根拠の行を書き替えても止めない）
        doc.write_text("見出しの行\n要件の一行目はここに在ります\n二行目を作業で書き替えました\n", encoding="utf-8")
        run("T33 T31 で通った宣言の、根拠の行を書き替えた後 → 通る", [_say(good), _user("OK")], todo3, False)
        run("T34 書き替えた後の古い逐語を引いた、新しい宣言 → 止まる",
            [_say(good + "\n（宣言を出し直した）"), _user("OK")], todo3, True)
        doc.write_text("見出しの行\n要件の一行目はここに在ります\n二行目は閾値とパラメータの範囲を書く所です\n", encoding="utf-8")
        doc2 = tdp / "doc2.md"
        doc2.write_text("足された必読の一行目です\n", encoding="utf-8")
        MUST_FILE.write_text("# 見出し\n" + str(doc) + "\n" + str(doc2) + "\n", encoding="utf-8")
        log.write_text(str(doc) + "\n" + str(doc2) + "\n", encoding="utf-8")
        run("T35 必読の一覧に1本足す → 照らし直して止まる（足したファイルの根拠が無い）", [_say(good), _user("OK")], todo3, True)
        MUST_FILE = tdp / "must_none.txt"
    print(f"  {'✅' if not ng else '❌'} 見本の記録で試した 35件のうち、期待と違う {ng} 件")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else hook())
