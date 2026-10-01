#!/usr/bin/env python3
"""require_check_after_failure — 失敗したら、確かめるまで次の書き込み・実行をさせない（2026-10-01 新設）。

まこさん指示（逐語 2026-10-01）＝「確かめずに当てずっぽうであたるまで適当な対応をし続けることを禁ずる」
「強制でどうにかしろ」「とにかく確認をしろっていってんのに」。

止める決まり（1つだけ）
  直前の書き込み・実行（Write・Edit・MultiEdit・NotebookEdit・Agent・読むだけでない Bash）が失敗した
  （道具の結果が is_error）のに、その後に確かめる操作（Read・Grep・Glob・読むだけの Bash）が1つも無いまま、
  次の書き込み・実行をしようとしたら止める。
  ★Edit・Write・MultiEdit の失敗は、そのファイルを Read（または grep・cat・sed -n でその名前を含む読み）するまで止める。
通すもの＝確かめる操作そのもの（読むだけ）。
根拠の実測（2026-10-01・直近7日の記録42本）＝失敗 1,018回のうち、確かめずに次を試したのが 737回・その中でまた失敗 157回。

使い方:
  （hook）標準入力に Claude Code の PreToolUse の JSON
  --replay <日数>   直近の記録に流し、止まる回数を数える（何も止めない・登録の前の試し）
"""
import json
import pathlib
import re
import sys
import time

READ_TOOLS = {"Read", "Grep", "Glob", "TodoWrite", "ToolSearch"}
ACT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "Bash", "Agent"}
READ_CMDS = {"cat", "grep", "egrep", "rg", "ls", "head", "tail", "sed", "awk", "jq", "find", "wc", "diff",
             "shasum", "stat", "file", "sort", "uniq", "cut", "tr", "nl", "date", "echo", "printf", "cd",
             "test", "[", "true", "column", "basename", "dirname", "realpath", "md5", "du", "pwd", "which"}
GIT_READ = {"status", "log", "diff", "show", "ls-files", "rev-parse", "grep", "blame", "cat-file"}
FILE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def bash_is_read(cmd: str) -> bool:
    c = re.sub(r"'[^']*'|\"[^\"]*\"", "''", cmd)
    if re.search(r">(?!\s*/dev/null|&)", c.replace("2>&1", "")):
        return False
    if re.search(r"\bsed\s+-i", c):
        return False
    for seg in re.split(r"&&|\|\||;|\||\n", c):
        w = seg.strip().split()
        while w and "=" in w[0] and not w[0].startswith("="):
            w = w[1:]
        if not w:
            continue
        if w[0] == "git":
            if len(w) < 2 or w[1] not in GIT_READ:
                return False
        elif w[0] == "sed" and "-n" not in w and not any(x.startswith("-n") for x in w[1:]):
            # sed は -n で行を出すときだけ読むだけと見る（置き換えを出すだけでも書き込みはしないが、確かめる操作は -n の形）
            continue
        elif w[0] not in READ_CMDS:
            return False
    return True


def is_read(name, inp) -> bool:
    if name in READ_TOOLS:
        return True
    if name == "Bash":
        return bash_is_read(str((inp or {}).get("command", "")))
    return False


def reads_file(name, inp, path: str) -> bool:
    """この確かめる操作が、失敗したファイルを読んだか。"""
    base = pathlib.Path(path).name
    if name == "Read":
        return str((inp or {}).get("file_path", "")) == path
    if name == "Grep":
        return base in str((inp or {}).get("path", "")) or base in json.dumps(inp, ensure_ascii=False)
    if name == "Bash":
        return base in str((inp or {}).get("command", ""))
    return False


def pending_failure(calls, res):
    """最後の失敗した書き込み・実行と、その後に確かめたかを返す。戻り＝止める理由の文 か None。"""
    last_fail = None
    for i, (cid, nm, inp) in enumerate(calls):
        if nm in ACT_TOOLS and not is_read(nm, inp) and res.get(cid) is True:
            last_fail = i
        elif nm in ACT_TOOLS and not is_read(nm, inp) and res.get(cid) is False:
            pass
    if last_fail is None:
        return None
    cid, nm, inp = calls[last_fail]
    after = calls[last_fail + 1:]
    reads = [(n, x) for _c, n, x in after if is_read(n, x)]
    if nm in FILE_TOOLS:
        path = str((inp or {}).get("file_path", "") or (inp or {}).get("notebook_path", ""))
        if any(reads_file(n, x, path) for n, x in reads):
            return None
        return (f"直前の {nm}（{pathlib.Path(path).name}）が失敗しています。"
                f"そのファイルを Read で開いて、失敗の理由を確かめてから直してください。")
    if reads:
        return None
    what = str((inp or {}).get("command", "") or (inp or {}).get("description", ""))[:80]
    return (f"直前の {nm}（{what}）が失敗しています。"
            "失敗の理由を、Read か読むだけのコマンドで確かめてから、次の書き込み・実行をしてください。")


def load_calls(path: pathlib.Path, tail_bytes: int = 3_000_000):
    calls, res = [], {}
    with path.open("rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - tail_bytes))
        data = f.read().decode("utf-8", errors="replace")
    lines = data.splitlines()
    if size > tail_bytes:
        lines = lines[1:]
    for line in lines:
        try:
            o = json.loads(line)
        except Exception:
            continue
        c = (o.get("message") or {}).get("content")
        if not isinstance(c, list):
            continue
        for b in c:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                calls.append((b.get("id"), b.get("name"), b.get("input")))
            elif b.get("type") == "tool_result":
                res[b.get("tool_use_id")] = bool(b.get("is_error"))
    return calls, res


def hook() -> int:
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    name, inp = d.get("tool_name"), d.get("tool_input") or {}
    if name not in ACT_TOOLS or is_read(name, inp):
        return 0
    tp = d.get("transcript_path")
    if not tp or not pathlib.Path(tp).exists():
        return 0
    calls, res = load_calls(pathlib.Path(tp))
    why = pending_failure(calls, res)
    if why:
        print("🔒 [失敗の後は確かめる] " + why + "\n"
              "   まこさん指示 2026-10-01「確かめずに当てずっぽうであたるまで適当な対応をし続けることを禁ずる」",
              file=sys.stderr)
        return 2
    return 0


def replay(days: int) -> int:
    proj = pathlib.Path.home() / ".claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget"
    cut = time.time() - days * 86400
    files = [p for p in proj.glob("*.jsonl") if p.stat().st_mtime >= cut]
    n_act = n_block = n_read_blocked = n_block_then_fail = 0
    for p in files:
        calls, res = load_calls(p, tail_bytes=10 ** 10)
        counted = -1                          # ★本物では1回止まって確かめれば外れる＝1つの失敗につき1回だけ数える
        for i, (cid, nm, inp) in enumerate(calls):
            if is_read(nm, inp):
                continue                      # 読む操作は判定しない＝止めない
            if nm not in ACT_TOOLS:
                continue
            n_act += 1
            last = max((k for k in range(i) if calls[k][1] in ACT_TOOLS and not is_read(calls[k][1], calls[k][2])
                        and res.get(calls[k][0]) is True), default=-1)
            if last > counted and pending_failure(calls[:i], res):
                counted = last
                n_block += 1
                if res.get(cid) is True:
                    n_block_then_fail += 1
    print(f"記録 {len(files)} 本（直近 {days} 日）")
    print(f"書き込み・実行 {n_act} 回 ／ この強制が止める回数 {n_block} 回 ／ "
          f"そのうち本当にまた失敗していた回数 {n_block_then_fail} 回 ／ 読む操作を止めた回数 {n_read_blocked} 回")
    return 0


if __name__ == "__main__":
    if "--replay" in sys.argv:
        sys.exit(replay(int(sys.argv[sys.argv.index("--replay") + 1])))
    sys.exit(hook())
