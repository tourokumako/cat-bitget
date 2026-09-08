#!/usr/bin/env python3
"""audit_cp29_probe.py — 監査 cp29 が自分で考えた壊し方を、実物に当てて終了コードを取る。

やり方＝実物の hook に合成の入力（Write / Bash の JSON）を渡して呼ぶ。
★プロジェクトのファイルは1バイトも書き換えない（b45・cp28 の audit_cp28_probe.py と同じ考え方）。

見るもの
  Q2 の前半 … 承認のときの記録 #12 と、監査が自分で走らせた結果が一致するか
              （これは run_breaks.py --measure-only で別に測る）
  Q2 の後半 … b51 が「黙って合格になる」道が無いか。
              P1 守りが在るまま Write → 止まるか（止まらないなら b51 は壊さなくても合格を出す）
              P2 兄弟の記録でも止まるか（くらべる相手）
              P3 関係ないファイルは通るか（何でも止める作りになっていないか）
              P4 Bash 側（BASE_SUFFIX）でも止まるか ★b51 はここを測っていない
              P5 読むだけは通るか
              P6 b51 の壊す対象の行が見つからないとき、どうなるか（変え玉を作って実測）
              P7 hook が別の理由で止めたとき、どうなるか（変え玉で実測）
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
HOOK = os.path.join(ROOT, ".claude", "hooks", "require_acceptance_before_impl.sh")
B51 = os.path.join(ROOT, ".claude", "breaks", "b51_dirty_json_unguarded.sh")
LIB = os.path.join(ROOT, ".claude", "breaks", "lib.sh")


def call_hook(payload: dict) -> int:
    p = subprocess.run(["bash", HOOK], input=json.dumps(payload), text=True,
                       capture_output=True, cwd=ROOT)
    return p.returncode


def write_payload(path: str) -> dict:
    return {"tool_name": "Write", "tool_input": {"file_path": path, "content": "x"}}


def bash_payload(cmd: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


def sha(path: str) -> str:
    out = subprocess.run(["shasum", "-a", "256", path], capture_output=True, text=True)
    return out.stdout.split()[0]


def main() -> int:
    tmp = tempfile.mkdtemp()
    before = sha(HOOK)
    rows = []

    rows.append(("P1", "守りが在るまま、汚れの記録の形へ Write",
                 call_hook(write_payload(os.path.join(tmp, "zz.dirty.json"))),
                 "0 以外＝止まる（0 なら b51 は壊さなくても『合格』を出す）"))
    rows.append(("P2", "兄弟の記録（.breaks.json）へ Write",
                 call_hook(write_payload(os.path.join(tmp, "zz.breaks.json"))),
                 "0 以外＝止まる（くらべる相手）"))
    rows.append(("P3", "関係ない .txt へ Write",
                 call_hook(write_payload(os.path.join(tmp, "zz.txt"))),
                 "0＝通る（何でも止める作りではない）"))
    rows.append(("P4", "Bash から汚れの記録の形へ書く ★b51 は測っていない",
                 call_hook(bash_payload(f"echo x > {tmp}/zz.dirty.json")),
                 "0 以外＝止まる（BASE_SUFFIX 側）"))
    rows.append(("P5", "本物の汚れの記録を cat で読む",
                 call_hook(bash_payload(
                     "cat v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/"
                     "acceptance_archive/approval-audit-plumbing-20260907.dirty.json")),
                 "0＝通る（読むだけは今までどおり）"))

    # ---- P6・P7＝b51 の変え玉を作って、黙って合格にならないかを実測する
    src = open(B51, encoding="utf-8").read()
    src = src.replace('source "$(dirname "$0")/lib.sh"', f'source "{LIB}"')

    v6 = os.path.join(tmp, "zz_b51_target_gone.sh")
    open(v6, "w", encoding="utf-8").write(
        src.replace("'*.breaks.json|*.frozen.json|*.dirty.json|\\\\\\n'",
                    "'この文字列は実物に存在しない\\n'"))
    rc6 = subprocess.run(["bash", v6], capture_output=True, text=True, cwd=ROOT).returncode
    rows.append(("P6", "b51 の壊す対象の行が見つからないとき",
                 rc6, "0＝合格にならない（run_breaks は『止まらなかった』と出す）"))

    v7 = os.path.join(tmp, "zz_b51_hook_gone.sh")
    open(v7, "w", encoding="utf-8").write(
        src.replace('H="$ROOT/.claude/hooks/require_acceptance_before_impl.sh"',
                    f'H="{tmp}/存在しない_hook.sh"'))
    rc7 = subprocess.run(["bash", v7], capture_output=True, text=True, cwd=ROOT).returncode
    rows.append(("P7", "測る相手の hook that が見つからないとき",
                 rc7, "0＝合格にならない"))

    print(f"{'#':<4}{'壊し方':<46}{'終了コード':<10}期待")
    for no, what, rc, exp in rows:
        print(f"{no:<4}{what:<46}{rc:<10}{exp}")

    after = sha(HOOK)
    print()
    print(f"hook のハッシュ値 前={before[:16]}… 後={after[:16]}… ／ 変えていない = {before == after}")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
