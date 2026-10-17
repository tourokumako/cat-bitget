#!/usr/bin/env python3
"""require_tag_for_experiment_selftest.py — 実験 --tag ゲート（require_tag_for_experiment.sh）の自己テスト
（★2026-10-17・186回目・まこさん「要 CCの案で修正する」）。

何をするか＝コマンドを1つずつ入れた入力を hook に渡し、終了コードを見る。本物のファイルは何も書かない（戦略も走らせない）。
  S7 は、LC_CTYPE=UTF-8 で hook を呼び、止めの文が UTF-8 として読めるかを見る
  （Python から呼ぶと LC_CTYPE=UTF-8 になる＝PEP 538。直す前は 47行の「$strat（」が壊れたバイトを出し、試しの道具が落ちた）。
使い方: python3 .claude/hooks/require_tag_for_experiment_selftest.py --selftest
"""
import json
import os
import subprocess
import sys

HOOK = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/require_tag_for_experiment.sh"
PR = "scripts/priority_rebuild"
ST = "e37" + "_scalp.py"      # 名前を分けて書く＝この自己テストを走らせるコマンドに戦略の名前を出さない

CASES = [
    ("S1 タグ無しで戦略を走らせると止まる", f"python3 {PR}/{ST}", 2),
    ("S2 --tag を付ければ通る", f"python3 {PR}/{ST} --tag v1", 0),
    ("S3 試しの道具の引数に戦略の名前があるだけなら通る", f"python3 .claude/tools/try_hooks.py --session s --write {PR}/{ST}", 0),
    ("S4 引用符の中の言及は通る（10月15日の誤報の形）", f"printf '%s' \"python3 {PR}/{ST}\" | wc -c", 0),
    ("S5 ほかの区切りの --help では通さない（すり抜け）", f"python3 {PR}/{ST} ; grep --help", 2),
    ("S6 ほかの区切りの --tag では通さない（すり抜け）", f"python3 {PR}/{ST} ; echo --tag x", 2),
]


def run(cmd: str, env=None):
    inp = json.dumps({"session_id": "selftest", "tool_name": "Bash", "tool_input": {"command": cmd}}, ensure_ascii=False)
    return subprocess.run(["bash", HOOK], input=inp.encode(), capture_output=True, timeout=60, env=env)


def selftest() -> int:
    ng = 0
    total = 0
    for name, cmd, want in CASES:
        total += 1
        got = run(cmd).returncode
        print(f"{'✅' if got == want else '❌'} {name}（期待 rc={want}・結果 rc={got}）")
        ng += int(got != want)
    total += 1
    p = run(f"python3 {PR}/{ST}", env=dict(os.environ, LC_CTYPE="UTF-8"))
    try:
        p.stderr.decode("utf-8")
        ok = p.returncode == 2
    except UnicodeDecodeError:
        ok = False
    print(f"{'✅' if ok else '❌'} S7 LC_CTYPE=UTF-8 で呼んでも、止めの文が UTF-8 として読める（rc={p.returncode}）")
    ng += int(not ok)
    print(f"selftest {total - ng}/{total}")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 2)
