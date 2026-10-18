#!/usr/bin/env python3
"""block_repeat_failure — 同じ相手で2回続けて失敗したら、見立てを書くまで その相手に手を出させない（2026-10-01 新設）。

まこさん指示（逐語 2026-10-01）＝「確認をしないで、正しい対処方法を確認せずに、思いつきの当てずっぽうで対処し、
あたるまで永遠に適当な対処をし続けることをやめろって言ってんの！！！！」「それでいいから」。
出どころ（外）＝DEV「five hooks」の逐語 "Two strikes on the same target usually means the approach is wrong, not that it
needs another tweak."／RegressionLedger「原因の見立てを2〜3個 書くまで直させない」。

決まり
  相手＝Edit・Write・MultiEdit・NotebookEdit は直すファイル。Bash は走らせる .py・.sh（無ければコマンドの頭の2語）。Agent は "Agent"。
  同じ相手への書き込み・実行が2回続けて失敗した（道具の結果が is_error）ら、その相手への次の操作を止める。
  ★この hook 自身が止めた操作（結果の文に「[同じ相手で2回 失敗]」）は、失敗に数えない（2026-10-18・195回目・load() の説明）。
  外す＝2回目の失敗の後に、.claude/state/sessions/<セッション>/diagnosis.md を書く。中身＝「相手: <相手>」の行と、
        「見立て」で始まる行を2つ以上（Write で書けば、この強制は止めない）。
  読むだけの操作（Read・Grep・Glob・読むだけの Bash）は止めない。

使い方: （hook）標準入力に PreToolUse の JSON ／ --replay <日数> 直近の記録に流して数える（何も止めない）
"""
import json
import os
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from require_check_after_failure import ACT_TOOLS, is_read  # 読むだけの判定を同じものにする
from transcript_rows import rows                            # 記録は会話の本物の行だけを読む（2026-10-15）

ROOT = pathlib.Path(__file__).resolve().parents[2]
SESS = ROOT / ".claude/state/sessions"
PY = re.compile(r"[\w./~-]+\.(?:py|sh)\b")


HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\s*\1\b", re.S)
RUN_PY = re.compile(r"(?:^|[;&|(\s])(?:python3?|bash|sh)\s+(?:-\S+\s+)*([^\s;&|]+\.(?:py|sh))\b")
REDIRECT = re.compile(r">>?\s*([^\s;&|>]+)")


def target_of(name, inp) -> str:
    """相手＝直すファイル／Bash は走らせるプログラム（無ければ書き込む先・名前の出てくる .py・頭の2語）。
    ★2026-10-15（182回目・まこさん「止めなかった169回の原因を調べて」「OK」）＝直す前は、Bash の相手を
      「コマンドの中で最初に出てくる .py・.sh の名前」で決めていた（ヒアドキュメントの文の中の名前まで拾う）。
      そのため、worklog に書き足す cat >> … <<'EOF' が「gen_acceptance.py」と数えられ、試しの道具は何を試しても
      全部「try_hooks.py」と数えられた＝別々の操作を同じ相手と数えた。"""
    inp = inp or {}
    if name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        p = str(inp.get("file_path") or inp.get("notebook_path") or "")
        # ★2026-10-18（監査 CP80）＝同じファイルを別のパス（sdk の .claude/state の近道）で書くと別の相手と数えていた＝本物のパスで数える
        return os.path.realpath(p) if p else ""
    if name == "Bash":
        cmd = str(inp.get("command", ""))
        if "try_hooks.py" in cmd:                        # 試しの道具＝試した相手で数える
            m = re.search(r"--(?:edit|write)\s+(\S+)", cmd)
            if m:
                return "try:" + pathlib.Path(m.group(1).strip("'\"")).name
            m = re.search(r"--bash\s+([\"'])(.*?)\1(?=\s|$)", cmd, re.S)
            if m:
                return "try:" + target_of("Bash", {"command": m.group(2)})
        # ★2026-10-18（監査 CP80）＝引用符の中が空白も区切りも無い1語（パス）なら、引用符だけを外して中身を残す
        #   （直す前は python3 "x.py" の名前が消え、同じプログラムを別の相手と数えて3回目が通った）
        body = re.sub(r"'[^']*'|\"[^\"]*\"",
                      lambda m: m.group(0)[1:-1] if re.fullmatch(r"[^\s;|&<>()$`\\]+", m.group(0)[1:-1]) else "",
                      HEREDOC.sub("", cmd))
        m = RUN_PY.search(body)
        if m:
            return pathlib.Path(m.group(1)).name
        outs = [x for x in REDIRECT.findall(body) if not x.startswith("/dev/")]   # 2>/dev/null は書き込む先でない
        if outs:
            return pathlib.Path(outs[0]).name
        m = PY.findall(body)
        if m:
            return pathlib.Path(m[0]).name
        w = [x for x in body.split() if not re.match(r"^\w+=", x) and x not in ("cd", "&&")]
        return " ".join(w[:2])
    return name


def load(path: pathlib.Path):
    """戻り＝[(id, 道具, 入力, 結果が失敗か, 結果の時刻)]（結果の無い呼び出しは失敗でない扱い）。
    ★2026-10-18（195回目・まこさん「hookの不具合は修正してほしい」）＝この hook 自身が止めた操作（結果の文に MARK）は、一覧に入れない。
      直す前は、止めた操作も記録では失敗（is_error）なので、止めるたびに「2回目の失敗の時刻」が進んで新しい場面になり、その時点の
      「相手:」の行の数が控え（diagnosis_need.json）に入った。見立てを足してから打っても、控えが足した後の数になり、永遠に通らなかった
      （実物＝195回目の diagnosis_need.json に同じ相手の鍵が6つ・控えの数が 0→1→2 と増えた）。effect() の「この hook に止められた
      操作は、本物の操作に数えない」と同じ扱いにする。別の hook に止められた操作は、今までどおり失敗に数える（意図どおり）。"""
    calls, res = [], {}
    # ★2026-10-15（181回目）＝記録は共通の rows() で読む（会話の本物の行だけ・同じ行は1回）。直す前は行の種類を見ず、
    #   api-request-blob の行（API に送った中身の控え・この日から記録に入った）の中の呼び出しも数え、1回の失敗を2回と数えた
    for o in rows(path):
        c = (o.get("message") or {}).get("content")
        if not isinstance(c, list):
            continue
        for b in c:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                calls.append([b.get("id"), b.get("name"), b.get("input")])
            elif b.get("type") == "tool_result":
                res[b.get("tool_use_id")] = (bool(b.get("is_error")), o.get("timestamp"),
                                             MARK in json.dumps(b.get("content"), ensure_ascii=False))
    return [(i, n, x, res.get(i, (False, None, False))[0], res.get(i, (False, None, False))[1])
            for i, n, x in calls if not res.get(i, (False, None, False))[2]]


def two_strikes(rows, tgt):
    """その相手への最後の2回の操作が両方 失敗なら、2回目の時刻を返す。違えば None。"""
    # ★2026-10-18（監査 CP80）＝結果の無い呼び出し（いま打とうとしている操作）は数えない。いまの操作の行が PreToolUse の時点で
    #   記録に入っていると、その操作が「最後の1回」になり、結果が無い＝失敗でない扱いで必ず通した（作り物の記録で確かめた）。
    hits = [r for r in rows if r[1] in ACT_TOOLS and not is_read(r[1], r[2]) and target_of(r[1], r[2]) == tgt and r[4]]
    if len(hits) >= 2 and hits[-1][3] and hits[-2][3]:
        return hits[-1][4] or ""
    return None


def _count(session: str, tgt: str) -> int:
    """diagnosis.md に在る「相手: <相手>」の行の数。"""
    p = SESS / session / "diagnosis.md"
    if not p.exists():
        return 0
    return sum(1 for ln in p.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip() == f"相手: {tgt}")


def diagnosed(session: str, tgt: str, since: str) -> bool:
    """★2026-10-15（182回目・まこさん「止めなかった169回の原因を調べて」「OK」）＝直す前は、diagnosis.md に「相手: <相手>」が
      どこかに在り、ファイルが2回目の失敗より後に書き換えられていれば通した（ファイル全体の時刻を見ていた）。そのため、前の場面で
      書いた同じ相手の見立てが残っていると、別の相手の見立てを書き足しただけで通った（直近30日で53回）。
      直した後＝止めたときに、その場面（相手・2回目の失敗の時刻）の「相手:」の行の数を控え（diagnosis_need.json）、
      その数より増えていて、見立ての行が2つ以上在るときだけ通す。控えが無い場面（初めて見つけた）は通さない。"""
    need = SESS / session / "diagnosis_need.json"
    try:
        base = json.loads(need.read_text(encoding="utf-8")).get(f"{tgt}\t{since}")
    except Exception:
        base = None
    if base is None:
        return False
    p = SESS / session / "diagnosis.md"
    s = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
    return _count(session, tgt) > base and sum(1 for ln in s.splitlines() if ln.strip().startswith("見立て")) >= 2


def remember(session: str, tgt: str, since: str) -> None:
    """止めた場面の「相手:」の行の数を控える（同じ場面は最初の1回だけ）。"""
    need = SESS / session / "diagnosis_need.json"
    try:
        d = json.loads(need.read_text(encoding="utf-8"))
    except Exception:
        d = {}
    key = f"{tgt}\t{since}"
    if key not in d:
        d[key] = _count(session, tgt)
        need.parent.mkdir(parents=True, exist_ok=True)
        need.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def hook() -> int:
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    name, inp = d.get("tool_name"), d.get("tool_input") or {}
    if d.get("agent_type"):
        return 0                                   # ★2026-10-18（監査 CP80）＝サブエージェントは通す。子の失敗は親の記録に入らず、親の失敗2回を子に当てていた（block_repeat_kind.py と同じ形）
    if name not in ACT_TOOLS or is_read(name, inp):
        return 0
    if name == "Write" and str(inp.get("file_path", "")).endswith("/diagnosis.md"):
        return 0
    tp = d.get("transcript_path")
    if not tp or not pathlib.Path(tp).exists():
        return 0
    tgt = target_of(name, inp)
    since = two_strikes(load(pathlib.Path(tp)), tgt)
    if since is None:
        return 0
    sid = str(d.get("session_id") or pathlib.Path(tp).stem)
    if diagnosed(sid, tgt, since):
        return 0
    remember(sid, tgt, since)
    print(f"🔒 [同じ相手で2回 失敗] 「{tgt}」への操作が2回続けて失敗しています。3回目を当てずっぽうで打たないでください。\n"
          f"   先に原因を調べ、.claude/state/sessions/{sid}/diagnosis.md に「相手: {tgt}」の行と、"
          "「見立て」で始まる行を2つ以上 書いてください（書いた後に、この相手へ手を出せます）。\n"
          "   ★前の場面で書いた同じ相手の見立ては数えません。この場面の見立てを、新しく書き足してください。\n"
          "   まこさん指示 2026-10-01「思いつきの当てずっぽうで対処し、あたるまで永遠に適当な対処をし続けることをやめろ」",
          file=sys.stderr)
    return 2


def replay(days: int) -> int:
    proj = pathlib.Path.home() / ".claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget"
    cut = time.time() - days * 86400
    files = [p for p in proj.glob("*.jsonl") if p.stat().st_mtime >= cut]
    n_act = n_block = n_block_fail = n_read = 0
    for p in files:
        rows = load(p)
        cleared = set()                                  # 本物では1回止まって見立てを書けば外れる＝相手ごとに1回だけ数える
        for k, (cid, nm, inp, fail, _ts) in enumerate(rows):
            if is_read(nm, inp):
                n_read += 1
                continue
            if nm not in ACT_TOOLS:
                continue
            n_act += 1
            tgt = target_of(nm, inp)
            since = two_strikes(rows[:k], tgt)
            if since is not None and (tgt, since) not in cleared:
                cleared.add((tgt, since))
                n_block += 1
                n_block_fail += int(fail)
    print(f"記録 {len(files)} 本（直近 {days} 日）／読む操作 {n_read} 回（止めない）／書き込み・実行 {n_act} 回")
    print(f"この強制が止める回数 {n_block} 回 ／ そのうち、記録の上で3回目もまた失敗していた回数 {n_block_fail} 回")
    return 0


MARK = "[同じ相手で2回 失敗]"
SINCE = "2026-10-01"                                     # この hook を入れた日


def _load_marked(path: pathlib.Path):
    """戻り＝[(id, 道具, 入力, 失敗か, 結果の時刻, この hook が止めたか, 呼んだ時刻, 呼んだ返信の id)]。"""
    calls, res = [], {}
    for o in rows(path):
        c = (o.get("message") or {}).get("content")
        if not isinstance(c, list):
            continue
        for b in c:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                calls.append([b.get("id"), b.get("name"), b.get("input"), o.get("timestamp") or "",
                              (o.get("message") or {}).get("id") or ""])
            elif b.get("type") == "tool_result":
                res[b.get("tool_use_id")] = (bool(b.get("is_error")), o.get("timestamp") or "",
                                             MARK in json.dumps(b.get("content"), ensure_ascii=False))
    return [(i, n, x) + res.get(i, (False, "", False)) + (ut, mid) for i, n, x, ut, mid in calls]


def _old_target(name, inp) -> str:
    """直す前（2026-10-15 まで）の相手の決め方の写し（--effect --detail で、直す前の hook に見えた相手を再現するためだけに使う）。"""
    inp = inp or {}
    if name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        return str(inp.get("file_path") or inp.get("notebook_path") or "")
    if name == "Bash":
        cmd = str(inp.get("command", ""))
        m = PY.findall(re.sub(r"'[^']*'|\"[^\"]*\"", "", cmd))
        if m:
            return pathlib.Path(m[0]).name
        w = [x for x in cmd.split() if not re.match(r"^\w+=", x) and x not in ("cd", "&&")]
        return " ".join(w[:2])
    return name


def _why_not(p: pathlib.Path, seq, k, j, first_block: str) -> str:
    """止めなかった場面の理由の見分け（--effect-detail）。k＝2回続けて失敗した直後の操作・j＝次の本物の操作。"""
    second, nxt = seq[k - 1], seq[j]
    if nxt[7] and nxt[7] == second[7]:
        return "A 2回目と同じ返信の中で同時に打った"
    if nxt[6] and second[4] and nxt[6] < second[4]:
        return "B 2回目の結果が記録に書かれる前に打った"
    if _old_target(second[1], second[2]) != _old_target(nxt[1], nxt[2]) or \
            _old_target(seq[k - 2][1], seq[k - 2][2]) != _old_target(second[1], second[2]):
        return "F 直す前の相手の決め方では、別の相手と数えていた（直した後は止める）"
    if first_block and (second[4] or "") < first_block:
        return "D hook がまだ一度も止めていない時期（登録の前の疑い）"
    d = SESS / p.stem / "diagnosis.md"
    s = d.read_text(encoding="utf-8", errors="replace") if d.exists() else ""
    if any(f"相手: {t}" in s for t in (target_of(second[1], second[2]), _old_target(second[1], second[2]))):
        return "C 見立ての記録に、同じ相手の見立てが在る（直す前の相手の名前も見る）"
    rs = load(p)
    idx = next((n for n, r in enumerate(rs) if r[0] == nxt[0]), None)
    if idx is not None and two_strikes(rs[:idx], target_of(nxt[1], nxt[2])) is not None:
        return "G いまの hook の判定なら止める（止めなかったのは直す前の作りのため）"
    return "E いまの hook の判定でも止めない（まだ分からない）"


def effect(days: int, detail: bool = False) -> int:
    """★2026-10-15（182回目・まこさん「了解」）＝効き目を数える（何も止めない）。
    2回続けて失敗した場面ごとに、この hook に止められた操作を飛ばし、同じ相手への次の本物の操作が また失敗したかを数える。
    入れる前（SINCE より前）と、入れた後で止めた場面・止めなかった場面に分ける。
    detail＝止めなかった場面を、理由ごとに数え、例を出す（まこさん「止めなかった169回の原因を調べて」）。"""
    proj = pathlib.Path.home() / ".claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget"
    cut = time.time() - days * 86400
    files = [p for p in proj.glob("*.jsonl") if p.stat().st_mtime >= cut]
    out = {"入れる前": [0, 0], "入れた後・止めた": [0, 0], "入れた後・止めなかった": [0, 0]}
    loaded = {p: _load_marked(p) for p in files}
    first_block = min((r[4] for rs in loaded.values() for r in rs if r[5] and r[4]), default="")
    why: dict = {}
    for p in files:
        by: dict = {}
        for r in loaded[p]:
            if r[1] in ACT_TOOLS and not is_read(r[1], r[2]):
                by.setdefault(target_of(r[1], r[2]), []).append(r)
        for seq in by.values():
            k = 2
            while k < len(seq):
                if not (seq[k - 1][3] and seq[k - 2][3]):
                    k += 1
                    continue
                j, blocked = k, False
                while j < len(seq) and seq[j][5]:            # この hook に止められた操作は、本物の操作に数えない
                    blocked, j = True, j + 1
                if j >= len(seq):
                    break
                key = "入れた後・止めた" if blocked else ("入れる前" if (seq[k - 1][4] or "") < SINCE else "入れた後・止めなかった")
                out[key][0] += 1
                out[key][1] += int(seq[j][3])
                if detail and key == "入れた後・止めなかった":
                    w = _why_not(p, seq, k, j, first_block)
                    why.setdefault(w, []).append(f"{p.stem[:8]} {seq[k - 1][4][:19]} {target_of(seq[j][1], seq[j][2])[:60]}")
                k = j + 2
    print(f"記録 {len(files)} 本（直近 {days} 日・入れた日 {SINCE}・この hook が初めて止めた時刻 {first_block[:19]}）")
    for key, (n, f) in out.items():
        print(f"  {key}：2回続けて失敗した場面 {n} 回 ／ 次の本物の操作もまた失敗 {f} 回（{(100 * f / n) if n else 0:.1f}%）")
    if detail:
        print("止めなかった場面の理由:")
        for w, xs in sorted(why.items()):
            print(f"  {w}：{len(xs)} 回")
            for x in xs[:4]:
                print(f"     例 {x}")
    return 0


def selftest() -> int:
    """★2026-10-15（182回目）＝相手の決め方6件・見立ての確かめ方4件・本物の入口に作り物の記録を流す3件。"""
    import shutil
    import subprocess
    tc = [
        ("T1 ヒアドキュメントの文の中の名前は拾わない", "cd /a; cat >> /a/worklog.md <<'EOF'\ngen_acceptance.py を直した\nEOF", "worklog.md"),
        ("T2 走らせるプログラム", "cd /a && python3 .claude/tools/gen_acceptance.py --write", "gen_acceptance.py"),
        ("T3 試しの道具 --edit は試した相手", "python3 .claude/tools/try_hooks.py --session s --edit /a/b.py --old x --new y", "try:b.py"),
        ("T4 試しの道具 --bash は試したコマンドの相手", 'python3 .claude/tools/try_hooks.py --session s --bash "python3 /a/c.py --selftest"', "try:c.py"),
        ("T5 書き込む先が違えば別の相手", "cat >> /a/other.md <<'EOF'\nx\nEOF", "other.md"),
        ("T7 2>/dev/null は書き込む先でない", "git diff /a/b.md 2>/dev/null | head", "git diff"),
    ]
    bad = 0
    for nm, cmd, want in tc:
        got = target_of("Bash", {"command": cmd})
        ok = got == want
        bad += not ok
        print(f"  {'✅' if ok else '❌'} {nm}（{got}）")
    ok = target_of("Edit", {"file_path": "/a/b.py"}) == "/a/b.py"
    bad += not ok
    print(f"  {'✅' if ok else '❌'} T6 Edit は直すファイル")
    sid = "_selftest_block_repeat_failure"
    d = SESS / sid
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    try:
        diag = d / "diagnosis.md"
        diag.write_text("相手: /x/y.py\n見立て1 古い\n見立て2 古い\n", encoding="utf-8")
        since = "2026-10-16T00:00:03Z"
        cases = [("D1 控えが無い（初めて見つけた）→ 通さない", lambda: diagnosed(sid, "/x/y.py", since), False)]
        remember(sid, "/x/y.py", since)
        cases.append(("D2 古い見立てだけ → 通さない", lambda: diagnosed(sid, "/x/y.py", since), False))
        cases.append(("D3 別の相手の見立てだけ足した → 通さない", lambda: (
            diag.write_text(diag.read_text(encoding="utf-8") + "相手: /x/z.py\n見立て1\n見立て2\n", encoding="utf-8"),
            diagnosed(sid, "/x/y.py", since))[1], False))
        cases.append(("D4 同じ相手の見立てを新しく足した → 通す", lambda: (
            diag.write_text(diag.read_text(encoding="utf-8") + "相手: /x/y.py\n見立て1 新しい\n見立て2 新しい\n", encoding="utf-8"),
            diagnosed(sid, "/x/y.py", since))[1], True))
        for nm, f, want in cases:
            ok = f() == want
            bad += not ok
            print(f"  {'✅' if ok else '❌'} {nm}")
        # 本物の入口（hook）に、作り物の記録を流す
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
        tp = d / "t.jsonl"

        def line(kind, uid, ts, content):
            return json.dumps({"type": kind, "uuid": uid, "timestamp": ts, "message": {"id": "m" + uid, "content": content}})

        def edit(n, err):
            return [line("assistant", f"a{n}", f"2026-10-16T00:00:0{2 * n}Z",
                         [{"type": "tool_use", "id": f"t{n}", "name": "Edit", "input": {"file_path": "/x/y.py"}}]),
                    line("user", f"u{n}", f"2026-10-16T00:00:0{2 * n + 1}Z",
                         [{"type": "tool_result", "tool_use_id": f"t{n}", "is_error": err, "content": "e"}])]
        inp = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "/x/y.py"}, "transcript_path": str(tp), "session_id": sid})

        def run():
            return subprocess.run([sys.executable, __file__], input=inp, capture_output=True, text=True).returncode
        tp.write_text("\n".join(edit(0, True)) + "\n", encoding="utf-8")
        h = [("H1 失敗1回 → 通す", run(), 0)]
        tp.write_text("\n".join(edit(0, True) + edit(1, True)) + "\n", encoding="utf-8")
        h.append(("H2 同じ相手で2回続けて失敗 → 止める", run(), 2))
        (d / "diagnosis.md").write_text("相手: /x/y.py\n見立て1\n見立て2\n", encoding="utf-8")
        h.append(("H3 止められた後に見立てを書いた → 通す", run(), 0))

        # ★2026-10-18（195回目）＝この hook が止めた操作（結果の文に MARK・is_error）が記録に足されても、場面（2回目の失敗の時刻）は進まない
        def blocked(n):
            return [line("assistant", f"a{n}", f"2026-10-16T00:00:0{2 * n}Z",
                         [{"type": "tool_use", "id": f"t{n}", "name": "Edit", "input": {"file_path": "/x/y.py"}}]),
                    line("user", f"u{n}", f"2026-10-16T00:00:0{2 * n + 1}Z",
                         [{"type": "tool_result", "tool_use_id": f"t{n}", "is_error": True,
                           "content": f"PreToolUse:Edit hook error: 🔒 {MARK} 「/x/y.py」への操作が2回続けて失敗しています。"}])]
        tp.write_text("\n".join(edit(0, True) + edit(1, True) + blocked(2) + blocked(3)) + "\n", encoding="utf-8")
        (d / "diagnosis.md").unlink()
        h.append(("H4 止められた回が2回 記録に足されても、見立てが無ければ止める。控えの鍵は1つのまま（終了コード, 鍵の数）",
                  (run(), len(json.loads((d / "diagnosis_need.json").read_text(encoding="utf-8")))), (2, 1)))
        (d / "diagnosis.md").write_text("相手: /x/y.py\n見立て1\n見立て2\n", encoding="utf-8")
        h.append(("H5 その後に見立てを書けば通る（直す前は、控えが足した後の数になり通らなかった）", run(), 0))
        for nm, got, want in h:
            ok = got == want
            bad += not ok
            print(f"  {'✅' if ok else '❌'} {nm}（終了コード {got}）")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print(f"自己テスト {16 - bad}/16")
    return 1 if bad else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--effect" in sys.argv:
        sys.exit(effect(int(sys.argv[sys.argv.index("--effect") + 1]), "--detail" in sys.argv))
    if "--replay" in sys.argv:
        sys.exit(replay(int(sys.argv[sys.argv.index("--replay") + 1])))
    sys.exit(hook())
