#!/usr/bin/env python3
"""try_hooks.py — これから打つ手（Write・Edit・Bash）を、書く前・走らせる前の hook 全部に先に渡して試し、
止める hook を全部 一度に出す。止める物が0本なら、その相手を記録する（require_try_before_act が読む）。

★2026-10-06（まこさん「じゃあ入れる」「OK」・案 A）
  なぜ要るか＝CC が確かめずに書き・走らせ、hook に1つずつ当たって止まり、原因を確かめずに出し直す往復で、
  まこさんの時間とトークンを溶かした（155回目・恒久75番）。先に全部の hook へ同じ入力を渡せば、止める物が1回で全部 分かる。
  実測＝書く前の hook 16本を1回 試すのに 3.2秒。試しの中で守りの記録を書き替える hook は0本（hook 自身が落ちたときのエラーの記録だけ）。

使い方（SESSION＝やり取りの記録の名前・cat-bitget の根で打つ）:
  python3 .claude/tools/try_hooks.py --session SESSION --edit <パス> [--old <直す前の文字> --new <直した後の文字>]
  python3 .claude/tools/try_hooks.py --session SESSION --edit <パス> --old-file <ファイル> --new-file <ファイル>
  python3 .claude/tools/try_hooks.py --session SESSION --write <パス> [--content <中身を書いたファイル>]
      （--content を省くと、中身は空の文字で渡す＝中身を見る hook〔check_source_on_save ほか〕は本物と違う判定をする）
  python3 .claude/tools/try_hooks.py --session SESSION --bash "<走らせるコマンド>"
  python3 .claude/tools/try_hooks.py --selftest
限界＝試すのは書く前・走らせる前の hook だけ（ターンの終わりの検査と、書いた後の検査は試せない）。
  直す文字を省くと、直す行を見る hook（確認してから動く）が本物と違う判定をする＝直す文字は渡す。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SETTINGS = os.path.join(ROOT, ".claude", "settings.json")
RECORD = os.path.join(ROOT, ".claude", "state", "try_ok.json")
TRANSCRIPTS = "/Users/tachiharamasako/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget"
SELF_GATE = "require_try_before_act"          # 止める hook 自身は試さない（試しの道具を止めないため）
PY_RE = re.compile(r"\bpython3?\s+(?:-[A-Za-z]\s+)*([^\s;|&]+\.py)\b")


def hooks_for(tool: str) -> list:
    """settings.json の PreToolUse のうち、matcher がその道具に当たる hook のコマンド（重ならないように）。"""
    s = json.load(open(SETTINGS, encoding="utf-8"))
    out = []
    for grp in s.get("hooks", {}).get("PreToolUse", []):
        m = grp.get("matcher", "") or ""
        if m and tool not in re.split(r"\|", m):
            continue
        for h in grp.get("hooks", []):
            c = h.get("command", "")
            if c and SELF_GATE not in c and c not in out:
                out.append(c)
    return out


CD_RE = re.compile(r"""^cd\s+("[^"]+"|'[^']+'|\S+)$""")


def targets_of(tool: str, tin: dict, cwd: str) -> list:
    """記録する相手＝書くファイルの実のパス／走らせる .py の実のパス。

    ★2026-10-06（156回目・まこさん「OK」）＝コマンドの中の `cd <フォルダ>` を見て、その後ろの相対パスをそのフォルダにつなぐ。
      直す前は hook の入力の cwd（リポジトリ直下）だけにつないだので、`cd …/bitget-python-sdk-api && python3 scripts/priority_rebuild/x.py`
      の記録の鍵が、実在しない直下のパス（/scripts/priority_rebuild/x.py）になっていた（try_ok.json に4行・2026-10-06 に確かめた）。
      「先に試す」hook も同じ部品で鍵を作るので、試しと本番の鍵はそろったまま（判定は変わらない）。"""
    if tool in ("Write", "Edit", "MultiEdit"):
        p = tin.get("file_path") or ""
        return [os.path.realpath(p)] if p else []
    cmd = tin.get("command") or ""
    out, base = [], cwd
    for seg in re.split(r"&&|\|\||;|\||\n", cmd):
        s = seg.strip()
        mc = CD_RE.match(s)
        if mc:
            d = os.path.expanduser(mc.group(1).strip("\"'"))
            base = d if os.path.isabs(d) else os.path.join(base, d)
            continue
        for m in PY_RE.finditer(s):
            p = m.group(1)
            out.append(os.path.realpath(p if os.path.isabs(p) else os.path.join(base, p)))
    return out


def run_all(tool: str, tin: dict, session: str, cwd: str) -> list:
    """全部の hook に同じ入力を渡し、止めたものを [(名前, 文)] で返す。"""
    data = dict(session_id=session, transcript_path=os.path.join(TRANSCRIPTS, f"{session}.jsonl"), cwd=cwd,
                hook_event_name="PreToolUse", tool_name=tool, tool_input=tin)
    inp = json.dumps(data)
    stops = []
    for c in hooks_for(tool):
        r = subprocess.run(c, shell=True, input=inp, capture_output=True, text=True, cwd=cwd, timeout=300)
        out = ((r.stderr or "") + (r.stdout or "")).strip()
        if r.returncode == 2 or '"decision": "block"' in out or '"permissionDecision": "deny"' in out:
            names = re.findall(r"[\w.-]+\.(?:sh|py)", c)
            stops.append((names[-1] if names else c[:60], out))
    return stops


def input_key(tool: str, tin: dict) -> str:
    """試した入力の印（★2026-10-15・181回目・まこさん「強制で解決できないの？」「じゃあ、先に直して」）。

    直す前＝記録は相手（ファイル）ごとで、30分 使い回せた＝試した後に文字を変えても、試していない入力のまま打てた
      （この日、CC が試さずに打って止められた回の始まりの1つ）。
    直した後＝本物で打つのと同じ入力の印が30分以内に無ければ、先に試す hook（require_try_before_act）が止める。
      Edit＝ファイル・直す前の文字・直した後の文字／Bash＝コマンドの文字／
      Write＝ファイルだけ（中身は印に入れない＝中身を変えても印は同じ・限界）。"""
    if tool == "Edit":
        parts = [tool, os.path.realpath(tin.get("file_path") or ""), tin.get("old_string") or "", tin.get("new_string") or ""]
    elif tool == "MultiEdit":
        parts = [tool, os.path.realpath(tin.get("file_path") or ""), json.dumps(tin.get("edits") or [], ensure_ascii=False)]
    elif tool == "Write":
        parts = [tool, os.path.realpath(tin.get("file_path") or "")]
    else:
        parts = [tool, tin.get("command") or ""]
    return "in:" + hashlib.sha256("\x00".join(parts).encode("utf-8")).hexdigest()[:24]


def record(targets: list, session: str, key: str = "") -> None:
    try:
        d = json.load(open(RECORD, encoding="utf-8"))
    except Exception:                                        # noqa: BLE001
        d = {}
    now = time.time()
    for t in targets + ([key] if key else []):
        d[t] = {"t": now, "session": session}
    d = {k: v for k, v in d.items() if now - v.get("t", 0) < 86400}     # 1日より古い記録は捨てる
    with open(RECORD, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def write_input(path: str, content_file) -> dict:
    """Write の試しの入力（★2026-10-17・185回目）。--content のファイルが在れば、その中身を渡す。
    省けば空の文字（直す前と同じ）。"""
    content = open(content_file, encoding="utf-8").read() if content_file else ""
    return dict(file_path=os.path.abspath(path), content=content)


def main(argv: list) -> int:
    def opt(k):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else None
    if "--selftest" in argv:
        return selftest()
    # ★2026-10-08（160回目・まこさん OK の案 3b）＝止められる打ち方の早見表（gen_hook_cheatsheet.py・開始時の hook_health_check.sh が呼ぶ）。
    #   gen_hook_cheatsheet.py は土台ゲートの道具の一覧に無く単独で走らせられないので、この口から呼ぶ。
    if "--cheatsheet" in argv:
        import gen_hook_cheatsheet
        return gen_hook_cheatsheet.main(argv)
    session = opt("--session")
    if not session:
        print("❌ --session（やり取りの記録の名前）が要る")
        return 2
    cwd = os.getcwd()
    if opt("--edit"):
        old = open(opt("--old-file"), encoding="utf-8").read() if opt("--old-file") else (opt("--old") or "")
        new = open(opt("--new-file"), encoding="utf-8").read() if opt("--new-file") else (opt("--new") or "")
        tool, tin = "Edit", dict(file_path=os.path.abspath(opt("--edit")), old_string=old, new_string=new)
    elif opt("--write"):
        tool, tin = "Write", write_input(opt("--write"), opt("--content"))
    elif opt("--bash"):
        tool, tin = "Bash", dict(command=opt("--bash"))
    else:
        print("❌ --edit・--write・--bash のどれか1つが要る")
        return 2
    n = len(hooks_for(tool))
    stops = run_all(tool, tin, session, cwd)
    if stops:
        print(f"■ 止める hook {len(stops)} 本 ／ 試した {n} 本（全部 一度に出します。全部 直してから、もう一度 試す）")
        for name, out in stops:
            lines = out.splitlines()
            # 頭の6行と、止めた理由の行（FAIL・❌・不足）を全部 出す（頭だけだと理由が切れる＝2026-10-06 に実測）
            keep = lines[:6] + [ln for ln in lines[6:] if any(w in ln for w in ("FAIL", "❌", "不足", "RESULT"))]
            print(f"── {name} ──\n" + "\n".join("   " + ln for ln in keep))
        return 1
    tg = targets_of(tool, tin, cwd)
    record(tg, session, input_key(tool, tin))                # ★2026-10-15＝試した入力の印も残す（input_key の説明）
    print(f"✅ 止める hook 0 本 ／ 試した {n} 本。記録した相手＝{tg or '（無し＝止める hook の対象外）'}")
    return 0


def selftest() -> int:
    """番人6つ＝①止める hook 自身を試さない ②Bash の相手は、相対の cd の後ろでは そのフォルダにつないだ .py
    ③Edit の相手は書くファイル ④絶対パスの cd の後ろでは そのフォルダにつなぐ ⑤cd が無ければ cwd につなぐ
    ⑥Write の中身は --content のファイルの中身（省けば空）。"""
    ng = []
    if any(SELF_GATE in c for t in ("Write", "Edit", "Bash") for c in hooks_for(t)):
        ng.append("①止める hook 自身が試しに入っている")
    tg = targets_of("Bash", {"command": "cd x && python3 scripts/priority_rebuild/observe_diag.py --selftest"}, ROOT)
    if tg != [os.path.realpath(os.path.join(ROOT, "x", "scripts/priority_rebuild/observe_diag.py"))]:
        ng.append(f"②Bash の相手が違う（相対の cd を見ていない）: {tg}")
    if targets_of("Edit", {"file_path": "/a/b.py"}, ROOT) != [os.path.realpath("/a/b.py")]:
        ng.append("③Edit の相手が違う")
    sdk = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
    tg4 = targets_of("Bash", {"command": f"cd {sdk} && python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog"}, ROOT)
    if tg4 != [os.path.realpath(os.path.join(sdk, "scripts/priority_rebuild/observe_diag.py"))]:
        ng.append(f"④Bash の相手が違う（絶対パスの cd を見ていない）: {tg4}")
    tg5 = targets_of("Bash", {"command": "python3 .claude/tools/run_breaks.py --selftest"}, ROOT)
    if tg5 != [os.path.realpath(os.path.join(ROOT, ".claude/tools/run_breaks.py"))]:
        ng.append(f"⑤Bash の相手が違う（cd が無いときに cwd につないでいない）: {tg5}")
    if write_input("/a/b.md", __file__)["content"] != open(__file__, encoding="utf-8").read() \
            or write_input("/a/b.md", None)["content"] != "":
        ng.append("⑥Write の中身が違う（--content のファイルの中身を渡していない／省いたときに空でない）")
    print("✅ selftest 6/6 pass" if not ng else "❌ " + "／".join(ng))
    return 0 if not ng else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
