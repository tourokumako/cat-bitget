#!/usr/bin/env python3
"""require_selftest_after_source_edit.py — テンプレや元データを書き替えたら、それを読む道具の自己テストを走らせるまでターンを終われなくする。

まこさん指示 2026-09-16（逐語）＝「この３つのミスを繰り返さない仕組みを作れ」。
next_step §0-2 の仕組み2・教訓 L-604。

なぜ要るか（L-604・102〜103回目）
  2026-09-15 に監査のテンプレ `_template.md` の見出しを変えた。古い依頼書の道具 gen_audit_request.py は
  テンプレの見出しを一覧で持っていたので、自己テストが落ちるようになった。変えたときに、このテンプレを
  読む道具を探さなかった。翌日、監査に出す前のチェックが NG を出して初めて分かった。

2つの口
  post（PostToolUse on Write／Edit／MultiEdit）
    ① 書き替えたファイルが「テンプレか元データ」なら（下の is_source）、そのファイル名（basename）を
       .claude/tools・.claude/hooks・SDK の scripts/priority_rebuild の .py から探す。
    ② その中で自己テストの旗（"--selftest" の文字）を持つ道具を一覧にし、書き替えた時刻と一緒に
       .claude/state/sessions/<id>/selftest_pending.json に記録する。一覧を画面に出す（rc=2＝知らせるだけ・
       書き替えはもう済んでいる）。
  stop（Stop）
    ③ 記録の道具ごとに、書き替えた時刻より後に「その道具の名前と --selftest を含む Bash のコマンド」を
       私が打ったかを、やり取りの記録（transcript）から探す。打っていれば記録から消す。
    ④ 1本でも残っていれば、打つコマンドの一覧を出してターンを終われなくする（rc=2）。
       ★落ちた自己テストでも「打った」は数える＝落ちたまま終われなくなる行き止まりは作らない。
         落ちた結果を報告するのは私の仕事（ここは見ない）。

テンプレか元データ（is_source）
  名前に template を含む（.py・.sh を除く）／または .json（.claude/state/sessions の中と settings*.json を除く）。

限界（正直に）
  ① Bash（sed -i・gen の --write）で書き替えると見ない（Write／Edit／MultiEdit だけ）。
  ② 道具がファイル名を文字で持たず、組み立てて読むと見つからない。
  ③ 自己テストの結果（通ったか）は見ない。打ったかだけ。
  ④ 恒久71番＝BOT の中身でない道具なので、壊すプログラムと自己テストは付けない。--try で1回 確かめる。
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
STATE = ROOT / ".claude/state/sessions"
READER_DIRS = [ROOT / ".claude/tools", ROOT / ".claude/hooks", SDK / "scripts/priority_rebuild"]
SELFTEST = '"--selftest"'


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def is_source(path: Path) -> bool:
    s = str(path)
    if "/.claude/state/sessions/" in s:
        return False
    if path.suffix in (".py", ".sh"):
        return False
    if "template" in path.name.lower():
        return True
    return path.suffix == ".json" and not path.name.startswith("settings")


def readers_with_selftest(name: str) -> list[str]:
    out = []
    for d in READER_DIRS:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.py")):
            if p.name == Path(__file__).name:
                continue                           # この hook 自身は説明の文に名前を持つだけ＝数えない
            try:
                txt = p.read_text(encoding="utf-8")
            except Exception:
                continue
            if name in txt and SELFTEST in txt:
                out.append(str(p))
    return out


def pending_path(sid: str) -> Path:
    return STATE / (sid or "no-session") / "selftest_pending.json"


def load(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save(p: Path, d: dict) -> None:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass


def post(data: dict) -> int:
    if data.get("agent_type"):
        return 0
    if data.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
        return 0
    fp = str((data.get("tool_input") or {}).get("file_path") or "")
    if not fp or not is_source(Path(fp)):
        return 0
    readers = readers_with_selftest(Path(fp).name)
    if not readers:
        return 0
    p = pending_path(str(data.get("session_id") or ""))
    d = load(p)
    t = now_iso()
    for r in readers:
        e = d.get(r) or {"sources": [], "since": t}
        if fp not in e["sources"]:
            e["sources"].append(fp)
        e["since"] = t                             # 書き替えるたびに、その後の走行を求め直す
        d[r] = e
    save(p, d)
    print(f"📋 [自己テストを求める記録] {Path(fp).name} を読む道具のうち、自己テストを持つもの {len(readers)} 本を記録しました"
          "（まこさん指示 2026-09-16・L-604）。ターンを終える前に、全部 走らせてください:", file=sys.stderr)
    for r in readers:
        print(f"   python3 {r} --selftest", file=sys.stderr)
    return 2


def commands_since(transcript: str, since: str) -> list[str]:
    cmds = []
    try:
        with open(transcript, encoding="utf-8") as f:
            for line in f:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                if o.get("type") != "assistant" or str(o.get("timestamp") or "") < since:
                    continue
                for c in (o.get("message") or {}).get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                        cmds.append(str((c.get("input") or {}).get("command") or ""))
    except Exception:
        pass
    return cmds


def stop(data: dict) -> int:
    p = pending_path(str(data.get("session_id") or ""))
    d = load(p)
    if not d:
        return 0
    tr = str(data.get("transcript_path") or "")
    left = {}
    for r, e in d.items():
        if not Path(r).is_file():
            continue
        name = Path(r).name
        if any(name in c and "--selftest" in c for c in commands_since(tr, e.get("since", ""))):
            continue
        left[r] = e
    save(p, left)
    if not left:
        return 0
    print("🔒 [自己テストを走らせるゲート] テンプレや元データを書き替えたのに、それを読む道具の自己テストをまだ走らせていません"
          "（まこさん指示 2026-09-16「この３つのミスを繰り返さない仕組みを作れ」・L-604）。", file=sys.stderr)
    for r, e in left.items():
        srcs = "・".join(Path(s).name for s in e.get("sources", []))
        print(f"   ❌ python3 {r} --selftest   （書き替えたもの: {srcs}）", file=sys.stderr)
    print("   ＝全部 走らせてから終えてください。落ちたら、その結果を報告してください（落ちても「走らせた」は数えます）。",
          file=sys.stderr)
    return 2


def main(mode: str, raw: str) -> int:
    try:
        data = json.loads(raw)
    except Exception:
        return 0                                   # 読めない入力では止めない（fail-open）
    return post(data) if mode == "post" else stop(data)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--try":
        sys.exit(main(sys.argv[2], Path(sys.argv[3]).read_text(encoding="utf-8")))
    if len(sys.argv) == 2 and sys.argv[1] in ("post", "stop"):
        sys.exit(main(sys.argv[1], sys.stdin.read()))
    sys.exit(0)
