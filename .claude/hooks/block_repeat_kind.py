#!/usr/bin/env python3
"""block_repeat_kind — 同じ種類の失敗を同じセッションで2回 起こしたら、決まりを書き出すまで先に進ませない（2026-10-01 新設）。

まこさん指示（逐語 2026-10-01）＝「確認せずに動けば一発で修正できるのに、その確認をせずに、適当に当てずっぽうな対処を
当たるまで続けることをやめろ」「以下ができる状態になるまでこのセッションは終了しない」。
根拠の実測（2026-10-01・直近7日の記録41本）＝書き込み・実行の失敗 1,043回のうち 710回が、同じセッションで既に起きた
種類の失敗の2回目以降（一番多いのは土台ゲートの止め 186回）。止める回数 159回で、3回目以降 551回を防げる見込み。

決まり
  種類＝hook の止め（hook のファイル名＋止めの文の【】や［］の見出し）／Edit の失敗（直す前の文字が無い ほか）／例外の名前。
       終了コードだけの失敗・種類の分からない失敗・この強制と block_repeat_failure 自身の止めは数えない。
  同じ種類が同じセッションで2回 起きたら、書き込み・実行（読む操作でないもの）を全部 止める。
  外す＝.claude/state/sessions/<セッション>/lessons.md に「種類: <種類>」の行と「次から確かめること:」で始まる行を書く
       （止めたときの行の数〔lessons_need.json〕より、両方の行が増えたときだけ外す＝決まりを書いた後にまた同じ種類が起きたら、
       その場面の決まりを書き足すまで もう一度 止める・2026-10-16）。
  止めないもの＝読む操作／セッションの置き場・worklog・計画・memory への書き込み／確かめるだけの実行
       （try_hooks.py・next_move.py・py_compile・bash -n と、読むだけの区切りだけでできたコマンド・2026-10-16）。

使い方: （hook）標準入力に PreToolUse の JSON ／ --replay <日数> 直近の記録に流して数える（何も止めない）／
       --selftest 確かめるだけの形の見分けと、作り物の記録での止め方を試す（本物の記録は書き替えない）
"""
import collections
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from require_check_after_failure import ACT_TOOLS, is_read, bash_is_read  # 読むだけの判定を同じものにする
from transcript_rows import rows                            # 記録は会話の本物の行だけを読む（2026-10-15）

ROOT = pathlib.Path(__file__).resolve().parents[2]
SESS = ROOT / ".claude/state/sessions"
FREE = ("/.claude/state/sessions/", "session_worklog_", "/.claude/plans/", "/memory/", "chat_draft.md")
# ★2026-10-01（143回目）＝止めの文に出る名前は .sh（登録は block_repeat_kind.sh）。.py だけだと自分の止めを数えて止め続けた。
SELF = ("block_repeat_kind.py", "block_repeat_failure.py", "block_repeat_kind.sh", "block_repeat_failure.sh")
# ★2026-10-01（143回目・まこさん「直せ」）＝名前の後ろの引数（例「require_confirm_before_act.sh pre」）を読み飛ばす。
#   直す前は名前の直後に「]」が来る形しか拾わず、確認の強制の止めを種類として数えていなかった。
HOOK = re.compile(r"hook (?:error|feedback)[^\[]*\[(?:bash |python3 )?([^\]\s]+)(?: [^\]]*)?\]:\s*([^\n]*)")
TAG = re.compile(r"[【\[]([^】\]]{1,30})[】\]]")
STOP_SEG = re.compile(r"\[(?:bash |python3 )?[^\]\s]+(?: [^\]]*)?\]:[^\n]*")   # Stop hook の差し戻しの1件（[hook の名前]: 止めの文）
# ★2026-10-16（183回目・まこさん「CCの案でOK」）＝試す・確かめるだけの実行は止めない。直す前は python3 で走らせる道具を
#   全部「実行」と見て、7日で止めた113回のうち52回が試しの道具・検査の道具だった。止めないのは、中身を読んで書き込みが
#   無いと確かめた4つの形だけ（try_hooks.py・next_move.py・py_compile・bash -n）。ほかの道具の --check ほかは、旗によって
#   ファイルを書くので、いままでどおり止める。
CHECK_SEG = re.compile(r"^python3?\s+(?:\S*/)?(?:try_hooks|next_move)\.py(?:\s|$)"
                       r"|^python3?\s+-m\s+py_compile(?:\s|$)|^bash\s+-n(?:\s|$)")


def kind_of(text: str):
    m = HOOK.search(text)
    if m:
        name = pathlib.Path(m.group(1)).name
        if name in SELF:
            return None
        t = TAG.search(m.group(2))
        return f"{name} {t.group(0) if t else ''}".strip()
    for k in ("String to replace not found", "File has not been read", "modified since"):
        if k in text:
            return "Edit: " + k
    if re.search(r"Found \d+ matches", text):
        return "Edit: Found N matches"
    e = re.findall(r"\b(\w+(?:Error|Exception))\b", text)
    if e and "Traceback" in text:
        return "例外: " + e[-1]
    return None


def load(path: pathlib.Path):
    """戻り＝[(道具, 入力, 失敗の文 or None, 結果の時刻)]。"""
    calls, res, stops = [], {}, []
    # ★2026-10-15（181回目）＝記録は共通の rows() で読む（会話の本物の行だけ・同じ行は1回）。直す前は行の種類を見ず、
    #   api-request-blob の行（API に送った中身の控え・この日から記録に入った）の中の呼び出しと結果も数え、1回の失敗を2回と数えた
    for o in rows(path):
        c = (o.get("message") or {}).get("content")
        # ★2026-10-01（143回目・まこさん「ちゃんと改善しろ」）＝Stop hook の差し戻しも hook ごとに失敗として数える。
        #   差し戻しは記録に「まこさんの発言」の形（本文が「Stop hook feedback:」で始まる文字列）で残るので、
        #   直す前は道具の失敗の結果だけを読み、同じ差し戻しを何回 受けても止めなかった。
        if o.get("type") == "user":
            txt = c if isinstance(c, str) else " ".join(x for x in (c or []) if isinstance(x, str))
            if "Stop hook feedback" in txt:
                for seg in STOP_SEG.findall(txt):
                    stops.append(("Stop", {}, "Stop hook feedback: " + seg, o.get("timestamp")))
        if not isinstance(c, list):
            continue
        for b in c:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                calls.append((b.get("id"), b.get("name"), b.get("input") or {}))
            elif b.get("type") == "tool_result" and b.get("is_error"):
                t = b.get("content")
                if isinstance(t, list):
                    t = " ".join(x.get("text", "") for x in t if isinstance(x, dict))
                res[b.get("tool_use_id")] = (str(t or ""), o.get("timestamp"))
    return [(n, x, res.get(i, (None, None))[0], res.get(i, (None, None))[1]) for i, n, x in calls] + stops


def open_repeats(rows):
    """2回 起きた種類と、その2回目の時刻。戻り＝{種類: 時刻}。"""
    n, when = collections.Counter(), {}
    for nm, inp, err, ts in rows:
        if err is None or (nm != "Stop" and (nm not in ACT_TOOLS or is_read(nm, inp))):
            continue
        k = kind_of(err)
        if not k:
            continue
        n[k] += 1
        if n[k] >= 2:
            # ★2回目だけでなく、3回目以降も時刻を上書きする（2026-10-01・まこさん「直す」）＝決まりを書いた後に
            #   また同じ種類が起きたら、決まりの書き直し（lessons.md の更新）までもう一度 止める
            when[k] = ts or ""
    return when


def _counts(session: str, k: str):
    """lessons.md の「種類: <種類>」の行の数と、「次から確かめること」で始まる行の数。"""
    p = SESS / session / "lessons.md"
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines() if p.exists() else []
    return (sum(1 for ln in lines if ln.strip() == f"種類: {k}"),
            sum(1 for ln in lines if ln.strip().startswith("次から確かめること")))


def unlearned(session: str, when: dict) -> list:
    """★2026-10-16（183回目・まこさん「CCの案でOK」）＝直す前は、「種類: …」がどこかに在り、lessons.md の時刻が最後の失敗より
      新しければ通した。そのため、同じ種類が3回目に起きた後でも、別の種類の決まりを書き足すだけで通った（block_repeat_failure の
      古い見立ての使い回しと同じ作り）。直した後＝止めたときの行の数の控え（lessons_need.json）より、「種類:」の行と
      「次から確かめること」の行の両方が増えたときだけ通す。控えが無い場面は通さない。"""
    need = SESS / session / "lessons_need.json"
    try:
        base = json.loads(need.read_text(encoding="utf-8"))
    except Exception:
        base = {}
    bad = []
    for k, ts in when.items():
        b = base.get(f"{k}\t{ts}")
        n_kind, n_next = _counts(session, k)
        if not (b and n_kind > b[0] and n_next > b[1]):
            bad.append(k)
    return bad


def remember(session: str, kinds: list, when: dict) -> None:
    """止めた場面ごとに、そのときの行の数を控える（同じ場面は最初の1回だけ）。"""
    need = SESS / session / "lessons_need.json"
    try:
        d = json.loads(need.read_text(encoding="utf-8"))
    except Exception:
        d = {}
    new = False
    for k in kinds:
        key = f"{k}\t{when[k]}"
        if key not in d:
            d[key] = list(_counts(session, k))
            new = True
    if new:
        need.parent.mkdir(parents=True, exist_ok=True)
        need.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def free_write(name, inp) -> bool:
    p = str((inp or {}).get("file_path") or "")
    return name in ("Write", "Edit", "MultiEdit") and any(k in p for k in FREE)


def check_only(name, inp) -> bool:
    """Bash のコマンドが、確かめるだけの形（CHECK_SEG）と読むだけの区切りだけでできているか。"""
    if name != "Bash":
        return False
    c = re.sub(r"'[^']*'|\"[^\"]*\"", "''", str((inp or {}).get("command", "")))
    if re.search(r">(?!\s*/dev/null|&)", c.replace("2>&1", "")):
        return False
    segs = [s.strip() for s in re.split(r"&&|\|\||;|\||\n", c) if s.strip()]
    hit = False
    for s in segs:
        if CHECK_SEG.search(s):
            hit = True
        elif not bash_is_read(s):
            return False
    return hit


def hook() -> int:
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    name, inp = d.get("tool_name"), d.get("tool_input") or {}
    if name not in ACT_TOOLS or is_read(name, inp) or free_write(name, inp) or check_only(name, inp):
        return 0
    tp = d.get("transcript_path")
    if not tp or not pathlib.Path(tp).exists():
        return 0
    sid = str(d.get("session_id") or pathlib.Path(tp).stem)
    when = open_repeats(load(pathlib.Path(tp)))
    bad = unlearned(sid, when)
    if not bad:
        return 0
    remember(sid, bad, when)
    lst = "\n".join(f"     種類: {k}" for k in bad)
    print(f"🔒 [同じ種類の失敗を2回] このセッションで、同じ種類の失敗を2回 起こしています。3回目を起こさないために、先に決まりを書き出してください。\n"
          f"{lst}\n"
          f"   書く先＝.claude/state/sessions/{sid}/lessons.md。上の「種類: …」の行をそのまま写し、"
          "「次から確かめること:」で始まる行に、なぜ止められたか・次の一手の前に何を確かめるかを書く（書いた後に先へ進めます）。\n"
          "   ★前の場面で書いた同じ種類の決まりは数えません。この場面の決まりを、新しく書き足してください。\n"
          "   まこさん指示 2026-10-01「確認せずに…適当に当てずっぽうな対処を当たるまで続けることをやめろ」", file=sys.stderr)
    return 2


def replay(days: int) -> int:
    proj = pathlib.Path.home() / ".claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget"
    cut = time.time() - days * 86400
    files = [p for p in proj.glob("*.jsonl") if p.stat().st_mtime >= cut]
    n_fail = n_block = n_later = 0
    for p in files:
        rows = load(p)
        cnt = collections.Counter()
        for nm, inp, err, _ts in rows:
            if err is None or (nm != "Stop" and (nm not in ACT_TOOLS or is_read(nm, inp))):
                continue
            n_fail += 1
            k = kind_of(err)
            if not k:
                continue
            cnt[k] += 1
        n_block += sum(v - 1 for v in cnt.values() if v >= 2)        # 2回目以降は毎回 止める
        n_later += sum(v - 2 for v in cnt.values() if v >= 2)
    print(f"記録 {len(files)} 本（直近 {days} 日）／書き込み・実行の失敗 {n_fail} 回")
    print(f"この強制が止める回数 {n_block} 回 ／ 止めた後に決まりを守れば防げた見込みの失敗（3回目以降） {n_later} 回")
    return 0


def selftest() -> int:
    """★2026-10-16（183回目）＝確かめるだけの形の見分け6件と、本物の入口に作り物の記録を流す6件。本物の記録は書き替えない。"""
    import shutil
    import subprocess
    tc = [
        ("C1 試しの道具（引用符の中の cp は見ない）→ 止めない", 'python3 .claude/tools/try_hooks.py --session x --bash "cp a b"', True),
        ("C2 py_compile と bash -n → 止めない", "python3 -m py_compile a.py && bash -n b.sh", True),
        ("C3 next_move.py を tail に流す → 止めない", "python3 .claude/tools/next_move.py --work x 2>&1 | tail -5", True),
        ("C4 試しの道具の出力をファイルへ → 止める", "python3 .claude/tools/try_hooks.py --session x > out.txt", False),
        ("C5 確かめていない道具 → 止める", "python3 .claude/tools/gen_verbatim.py --list", False),
        ("C6 cp が混じる → 止める", "python3 -m py_compile a.py && cp a.py b.py", False),
    ]
    bad = total = 0
    for nm, cmd, want in tc:
        total += 1
        ok = check_only("Bash", {"command": cmd}) == want
        bad += not ok
        print(f"  {'✅' if ok else '❌'} {nm}")
    sid = "_selftest_block_repeat_kind"
    d = SESS / sid
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    try:
        tp = d / "t.jsonl"
        les = d / "lessons.md"
        k = "Edit: String to replace not found"

        def line(kind, uid, ts, content):
            return json.dumps({"type": kind, "uuid": uid, "timestamp": ts, "message": {"id": "m" + uid, "content": content}})

        def fail(n):
            return [line("assistant", f"a{n}", f"2026-10-16T00:00:{2 * n:02d}Z",
                         [{"type": "tool_use", "id": f"t{n}", "name": "Edit", "input": {"file_path": f"/x/y{n}.py"}}]),
                    line("user", f"u{n}", f"2026-10-16T00:00:{2 * n + 1:02d}Z",
                         [{"type": "tool_result", "tool_use_id": f"t{n}", "is_error": True,
                           "content": "String to replace not found in file."}])]

        def run(cmd="cp /x/a /x/b"):
            inp = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "transcript_path": str(tp), "session_id": sid})
            return subprocess.run([sys.executable, __file__], input=inp, capture_output=True, text=True).returncode

        def add(txt):
            les.write_text((les.read_text(encoding="utf-8") if les.exists() else "") + txt, encoding="utf-8")
        h = []
        tp.write_text("\n".join(fail(0)) + "\n", encoding="utf-8")
        h.append(("H1 同じ種類の失敗1回 → 止めない", run(), 0))
        tp.write_text("\n".join(fail(0) + fail(1)) + "\n", encoding="utf-8")
        h.append(("H2 同じ種類の失敗2回・決まりが無い → 止める", run(), 2))
        h.append(("H3 H2 の場面でも、試しの道具は止めない", run('python3 .claude/tools/try_hooks.py --session x --bash "cp a b"'), 0))
        add(f"種類: {k}\n次から確かめること: 直す前の文字を Read で開いてから Edit する\n")
        h.append(("H4 決まりを書いた → 止めない", run(), 0))
        tp.write_text("\n".join(fail(0) + fail(1) + fail(2)) + "\n", encoding="utf-8")
        h.append(("H5 3回目が起き、決まりが前の場面の物だけ → 止める", run(), 2))
        add("種類: 例外: KeyError\n次から確かめること: 別の種類の決まり\n")
        h.append(("H6 別の種類の決まりだけ書き足した → 止める（直す前は通った穴）", run(), 2))
        add(f"種類: {k}\n次から確かめること: この場面の決まり\n")
        h.append(("H7 同じ種類の決まりを書き足した → 止めない", run(), 0))
        for nm, got, want in h:
            total += 1
            ok = got == want
            bad += not ok
            print(f"  {'✅' if ok else '❌'} {nm}（終了コード {got}）")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print(f"自己テスト {total - bad}/{total}")
    return 1 if bad else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--replay" in sys.argv:
        sys.exit(replay(int(sys.argv[sys.argv.index("--replay") + 1])))
    sys.exit(hook())
