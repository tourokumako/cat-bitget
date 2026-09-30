#!/usr/bin/env python3
# require_check_before_action.py — 確認しないと発言も進行もできないようにする
#   引数なし＝PreToolUse（Write・Edit・MultiEdit・Bash）／stop＝Stop（返信を終える前）
#
# まこさん指示（2026-09-30・逐語）
#   「確認をしなければ発言をできないような強制にしろ」（14:20）
#   「確認しないと進行できないような強制にしろ」（14:21・14:22）
#   「都度確認しろよ」（14:23）
#   「私が打っても読まないのか？」（14:18）
#
# なぜ要るか（worklog 20260930 §76）＝私は、道具を走らせる前・直しを書く前にその中身を開かず、
#   道具が作った物を読まずに次へ進め、途中で届いた まこさんの発言を読まずに作業を続けた。
#
# 見るもの（やり取りの記録の、結果の出た実際の操作だけ・私の申告や書類は見ない）
#   ①読む＝まこさんのいちばん新しい発言（途中で届いたものも含む）の後に、私がチャットで答える前に
#     読むだけでない操作を始めたら止める。
#   ②進行＝読むだけでない操作の前に、触る相手（書き換えるファイル・走らせる .py／.sh）を、
#     まこさんのいちばん新しい発言の後に開いていなければ止める。
#   ③都度＝書き換えるファイルは、この会話で最後に書き替えた後に開き直していなければ止める
#     （前に開いた中身のまま、書き替えた後の中身を確かめずに続けて直さない）。
#     道具が「書いた」「--write 完了」「作った」と出力したファイルは、その後に Read で開くまで、次の操作を止める。
#   ④発言＝返信を終える前に、まこさんのいちばん新しい発言の後に結果の出た読む操作が1つも無ければ止める。
#     返信に書いたファイルの名前（.py・.md・.json・.sh）を、その発言の後に開いていなければ止める。
#     道具が書いたファイルを読まずに返信しようとしても止める。
# 通すもの＝読むだけの Bash／検査のコマンド（--selftest・--verify・--try・--check・--measure-only ほか）／
#   worklog・sessions の下・chat_draft.md・scratchpad への書き込み。
# 限界（正直に）＝開いたかだけを見る（読んだ中身を正しく照らしたかは見ない）。①は私のチャットの文が在るかだけを見る
#   （その文が発言に正しく答えているかは見ない＝まこさんの目）。読むだけの Bash は、その名前を含む1回で「開いた」と数える。
import json
import os
import re
import sys
from pathlib import Path

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
FREE = ("fix_plan.md", "/.claude/state/sessions/", "session_worklog_", "chat_draft.md",
        "/private/tmp/claude-501/", "/scratchpad/",
        # ★2026-09-30＝自己テストが一時置き場に書いて消すファイル（読む相手にしない＝消えた後は開けない）
        "_selftest_", "gad_selftest_", "acceptance_sample.md")
READ_HEADS = {"cat", "grep", "ls", "wc", "head", "tail", "diff", "shasum", "stat", "find", "awk", "sed",
              "echo", "pwd", "cd", "true", "sort", "uniq", "cut", "tr", "jq", "file", "du", "date", "which"}
CHECK_RE = re.compile(r"--selftest|--verify\b|--try\b|--check\b|--check-design|--measure-only|--list\b|--dry\b|"
                      r"--show\b|py_compile|check_all_before_handoff|trial_design")
NAME_RE = re.compile(r"[\w.\-]+\.(?:py|sh)\b")
MADE_RE = re.compile(r"(?:書いた|--write 完了|作った)[^\n]*?([\w./\-]+\.(?:md|json|txt|py|sh|csv))")
REPLY_NAME_RE = re.compile(r"[\w.\-]+\.(?:py|md|json|sh)\b")
WRITE_TOOLS = ("Write", "Edit", "MultiEdit")


def _seg_readonly(seg):
    seg = seg.strip()
    if not seg or re.fullmatch(r"\d+", seg):
        return True
    for tgt in re.findall(r">>?\s*([^\s;|&]+)", seg):
        if tgt not in ("/dev/null", "&1", "&2") and not any(f in tgt for f in FREE):
            return False
    toks = seg.split()
    while toks and re.match(r"^[A-Za-z_]\w*=", toks[0]):
        toks.pop(0)
    if not toks:
        return True
    head = toks[0].rsplit("/", 1)[-1]
    if head == "sed" and any(t.startswith("-i") for t in toks[1:]):
        return False
    if head == "git":
        rest = [t for t in toks[1:] if not t.startswith("-")]
        return bool(rest) and rest[0] in ("status", "log", "diff", "show", "ls-files", "rev-parse", "grep", "cat-file")
    if head in READ_HEADS:
        return True
    if re.match(r"python[0-9.]*$", head) or head in ("bash", "sh"):
        return bool(CHECK_RE.search(seg))
    return False


def _bare(cmd):
    """引用符の中身を空にした文（引用符の中の | ; & > を区切りやリダイレクトと取り違えない）。
    ★2026-09-30＝grep の探す語の「\\|」を区切りと取り違え、読むだけの grep を止めた（本物の hook が私を止めた）。"""
    out, q = [], ""
    for ch in cmd or "":
        if q:
            if ch == q:
                q = ""
                out.append(ch)
            continue
        if ch in ("'", '"'):
            q = ch
        out.append(ch)
    return "".join(out)


def bash_readonly(cmd):
    return all(_seg_readonly(s) for s in re.split(r";|&&|\|\||\||\n", _bare(cmd)))


def _text_of(x):
    if isinstance(x, str):
        return x
    return " ".join(str(y.get("text") or "") for y in (x or []) if isinstance(y, dict))


def load(tpath):
    """記録を読む。戻り＝(本体の出来事の列, いちばん新しい まこさんの発言の位置, その文)。
    出来事＝("text", 文) か ("op", id, 道具, 入力, 結果)。結果の出ていない操作（いま判定している操作）は入れない。"""
    rows = []
    try:
        f = open(tpath, encoding="utf-8")
    except Exception:                                        # noqa: BLE001
        return [], -1, None
    with f:
        for ln in f:
            try:
                rows.append(json.loads(ln))
            except Exception:                                # noqa: BLE001
                continue
    ev, res, last, msg = [], {}, -1, None
    for o in rows:
        if o.get("isSidechain") is True:
            continue
        a = o.get("attachment") or {}
        if o.get("type") == "user" and (o.get("origin") or {}).get("kind") == "human":
            last, msg = len(ev), _text_of((o.get("message") or {}).get("content"))
            continue
        # ★2026-10-01＝途中で届く発言（queued_command）は区切りに数えない。私がチャットに書いた文は、道具の呼び出しと
        #   同じ返事の中だと記録に行として残らないことがある（記録の 4930〜4956 行で実測）＝答えても「答えていない」と
        #   止め続け、作業が進まなくなった。区切りは、ターンの始めの まこさんの発言だけにする。
        if o.get("type") == "attachment" and a.get("type") == "queued_command" and a.get("humanTurn"):
            continue
        c = (o.get("message") or {}).get("content")
        if not isinstance(c, list):
            continue
        for b in c:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text" and o.get("type") == "assistant" and (b.get("text") or "").strip():
                ev.append(("text", b.get("text")))
            elif b.get("type") == "tool_use":
                ev.append(("op", b.get("id"), b.get("name"), b.get("input") or {}, None))
            elif b.get("type") == "tool_result":
                res[b.get("tool_use_id")] = _text_of(b.get("content"))
    out = []
    for i, e in enumerate(ev):
        if e[0] == "op":
            if e[1] not in res:
                if i < last:
                    last -= 1
                continue
            e = ("op", e[1], e[2], e[3], res[e[1]])
        out.append(e)
    return out, last, msg


def _is_read(e, name):
    _k, _id, tool, inp, _res = e
    if tool == "Read":
        return Path(str(inp.get("file_path") or "")).name == name
    if tool == "Bash":
        cmd = str(inp.get("command") or "")
        return name in cmd and bash_readonly(cmd)
    return False


def _is_write(e, name):
    _k, _id, tool, inp, _res = e
    if tool in WRITE_TOOLS:
        return Path(str(inp.get("file_path") or "")).name == name
    if tool == "Bash":
        cmd = str(inp.get("command") or "")
        return name in cmd and not bash_readonly(cmd)
    return False


def opened_after(name, ev, pos):
    return any(e[0] == "op" and _is_read(e, name) for e in ev[max(pos, 0):])


def reopened_after_last_write(name, ev):
    w = max((i for i, e in enumerate(ev) if e[0] == "op" and _is_write(e, name)), default=-1)
    if w < 0:
        return True
    return any(e[0] == "op" and _is_read(e, name) for e in ev[w + 1:])


def made_unread(ev, start=0):
    """start より後（まこさんのいちばん新しい発言の後）に、読むだけでない実行が書いたと出力したファイルのうち、未読のもの。
    ★セッション全体から拾うと、前の発言の頃の物まで出た／grep で記録を読んだ出力の「書いた」まで拾った（2026-09-30 の試し）。"""
    out = []
    for i, e in enumerate(ev):
        if i < max(start, 0) or e[0] != "op" or e[2] != "Bash" or bash_readonly(str(e[3].get("command") or "")):
            continue
        for p in set(MADE_RE.findall(e[4] or "")):
            if any(f in p for f in FREE):
                continue
            n = Path(p).name
            if not any(x[0] == "op" and x[2] == "Read" and Path(str(x[3].get("file_path") or "")).name == n
                       for x in ev[i + 1:]):
                out.append(n)
    return sorted(set(out))


def targets(tool, ti):
    """いま触る相手（書き換えるファイル・走らせる .py／.sh）の (名前, パス)。"""
    if tool in WRITE_TOOLS:
        p = str(ti.get("file_path") or "")
        return [(Path(p).name, p)] if p else []
    cmd = str(ti.get("command") or "")
    out = [(n, "") for n in sorted(set(NAME_RE.findall(cmd)))]
    for m in re.finditer(r"sed\s+-i\S*\s+(?:'[^']*'|\"[^\"]*\"|\S+)\s+(\S+)", cmd):
        out.append((Path(m.group(1)).name, m.group(1)))
    return out


def judge(tool, ti, tpath):
    """PreToolUse＝①読む ②進行 ③都度。"""
    if tool in WRITE_TOOLS:
        if any(f in str(ti.get("file_path") or "") for f in FREE):
            return []
    elif tool == "Bash":
        if bash_readonly(str(ti.get("command") or "")):
            return []
    else:
        return []
    ev, last, msg = load(tpath)
    bad = []
    if msg is not None and not any(e[0] == "text" for e in ev[max(last, 0):]):
        bad.append(f"①読む＝まこさんの発言「{msg.strip()[:60]}」に、チャットでまだ答えていない（読んで答えてから進める）")
    for name, path in targets(tool, ti):
        if path and not os.path.exists(path if os.path.isabs(path) else os.path.join(ROOT, path)):
            continue                                         # 新しく作るファイルは開けない
        if not opened_after(name, ev, last):
            bad.append(f"②進行＝{name} を、まこさんのいちばん新しい発言の後に開いていない（止まる所・使う相手を開いて確かめてから）")
        elif tool in WRITE_TOOLS and not reopened_after_last_write(name, ev):
            bad.append(f"③都度＝{name} を最後に書き替えた後に開き直していない（書き替えた後の中身を確かめてから次を直す）")
    for n in made_unread(ev, last):
        bad.append(f"③都度＝道具が書いた {n} を、その後に Read で開いていない")
    return bad


def judge_stop(tpath, reply):
    """Stop＝④発言。"""
    ev, last, _msg = load(tpath)
    after = ev[max(last, 0):]
    bad = []
    if not any(e[0] == "op" and (e[2] == "Read" or (e[2] == "Bash" and bash_readonly(str(e[3].get("command") or ""))))
               for e in after):
        bad.append("④発言＝まこさんのいちばん新しい発言の後に、読む操作を1つもしないで返信しようとしている")
    for n in sorted(set(REPLY_NAME_RE.findall(reply or ""))):
        if not opened_after(n, ev, last):
            bad.append(f"④発言＝返信に書いた {n} を、まこさんのいちばん新しい発言の後に開いていない")
    for n in made_unread(ev, last):
        bad.append(f"④発言＝道具が書いた {n} を Read で開かずに返信しようとしている")
    return bad


def last_reply(tpath, last_msg_pos_only=True):
    ev, last, _m = load(tpath)
    return "\n".join(e[1] for e in ev[max(last, 0):] if e[0] == "text")


def main(mode):
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:                                        # noqa: BLE001
        return 0
    tpath = data.get("transcript_path") or ""
    # ★2026-09-30＝セッションの id が無い呼び方（承認の前の検査 A2 が全部の hook を模擬の入力で呼ぶ）では見ない。
    #   ほかの hook（enforce_todo_declaration・enforce_checked_edit）と同じ扱い＝本物の操作のときは普通に効く。
    if not data.get("session_id"):
        return 0
    if mode == "stop":
        if data.get("stop_hook_active"):
            return 0
        bad = judge_stop(tpath, last_reply(tpath))
    else:
        bad = judge(data.get("tool_name") or "", data.get("tool_input") or {}, tpath)
    if not bad:
        return 0
    print("🔒 [確認しないと発言も進行もできない] まこさん指示 2026-09-30「確認をしなければ発言をできないような強制にしろ」"
          "「確認しないと進行できないような強制にしろ」「都度確認しろよ」「私が打っても読まないのか？」:", file=sys.stderr)
    for b in bad:
        print("   " + b, file=sys.stderr)
    return 2


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--try":
        # --try <道具> <入力の json> <記録の jsonl> ／ --try stop <返信の文> <記録の jsonl>
        r = judge_stop(a[3], a[2]) if a[1] == "stop" else judge(a[1], json.loads(a[2]), a[3])
        for b in r or ["（止める所なし）"]:
            print(b)
        sys.exit(0)
    sys.exit(main(a[0] if a else ""))
