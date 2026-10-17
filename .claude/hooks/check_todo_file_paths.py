#!/usr/bin/env python3
# check_todo_file_paths.py — やることの「触るもの」に、置き場の無いファイル名が無いかを見る（Stop hook の部品）
#
# まこさん指示（2026-09-27・逐語）＝「→今後間違えないように対策して」（元データの置き場を間違えた件）。
# なぜ要るか＝next_step の47番と m2_todo.json の M2-E-4e は `m2_stage_candidates.json` とファイル名だけを書いていた。
#   125回目の CC は置き場を推測して `scripts/priority_rebuild/` を探し、見つからなかった（本当は `.claude/ratchet/`）。
#   このリポジトリには .claude が2つ在り（README_folder_map.md）、ファイル名だけでは置き場が決まらない。
#   だから「触るもの」の欄には、置き場まで書いたパスしか書けない形にする。
#
# 見るもの（2つ）
#   1. next_step.md の「5 プロジェクトのやることの表」の「触るもの」の欄（3列目）（2026-10-18 までは「0-2 の表」）
#   2. m2_todo.json の、状態が ✅済 でも 保留 でもない行の「触るファイル」
# 決まり＝欄の中の `…​.py`・`.json`・`.md`・`.sh`・`.txt`・`.csv` の名前は、
#   ①「/」を含むパスで書く ②リポジトリ直下か sdk 直下（v3-bitget-api-sdk/bitget-python-sdk-api）の
#   どちらかから辿って、実在するファイルがちょうど1つに決まる（シンボリックリンクで同じ実体なら1つと数える）。
#   ★欄に「新しく作る」「新設」が在るときは、②（実在）だけ見ない（まだ無いファイルを書くため）。
#
# 限界（正直に）＝①「触るもの」以外の欄（やること・確かめ方）の名前は見ない ②拡張子の無い名前・フォルダは見ない
#   ③パスが正しくても、そのファイルが本当に触る相手かは見ない ④next_step の表の3列目の位置が変われば外れる
#
# 使い方＝python3 check_todo_file_paths.py                        # 本物を見る（問題があれば一覧を出して rc=2）
#         python3 check_todo_file_paths.py <next_step.md> <m2_todo.json>  # 別のファイルで試す

import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = os.path.join(ROOT, "v3-bitget-api-sdk/bitget-python-sdk-api")
NEXT_STEP = os.path.join(ROOT, ".claude/state/next_step.md")
M2_TODO = os.path.join(SDK, ".claude/ratchet/m2_todo.json")
NAME = re.compile(r"[A-Za-z0-9_.\-/]+\.(?:py|json|md|sh|txt|csv)\b")
NEW_WORDS = ("新しく作る", "新設")


def _resolve(name: str) -> set:
    out = set()
    for base in (ROOT, SDK):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            out.add(os.path.realpath(p))
    return out


def problems_in_cell(where: str, cell: str) -> list:
    ng = []
    is_new = any(w in cell for w in NEW_WORDS)
    for name in NAME.findall(cell):
        name = name[2:] if name.startswith("./") else name
        if "/" not in name:
            hits = sorted({os.path.relpath(p, ROOT) for p in _resolve_anywhere(name)})
            hint = f"（find で見つかった置き場＝{'・'.join(hits)}）" if hits else "（リポジトリの中に見つからない）"
            ng.append(f"{where}：`{name}` に置き場が無い{hint}")
            continue
        if is_new:
            continue
        found = _resolve(name)
        if len(found) != 1:
            why = "実在しない" if not found else "2か所に在って1つに決まらない"
            ng.append(f"{where}：`{name}` が{why}（直下か sdk 直下から辿れるパスで書く）")
    return ng


def _resolve_anywhere(base: str) -> set:
    skip = ("/audits/", "/archive", "/mirror", "/.git/", "acceptance_archive", "/node_modules/")
    out = set()
    for d, _sub, files in os.walk(ROOT):
        if any(s in d + "/" for s in skip):
            continue
        if base in files:
            out.add(os.path.realpath(os.path.join(d, base)))
    return out


def check_next_step(path: str) -> list:
    ng = []
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return [f"{path} が読めない"]
    # ★2026-10-18（190回目）＝next_step を組み替え、「### 0-2」は「## 5 プロジェクトのやることの表」になった。節の終わりは次の「## 」か「# 」。
    m = re.search(r"^## 5 .*?$(.*?)^#{1,2} ", text, re.S | re.M)
    if not m:
        return ["next_step.md に「5 プロジェクトのやることの表」の節が見つからない"]
    for line in m.group(1).splitlines():
        if not line.startswith("|") or line.startswith("|---") or "触るもの" in line:
            continue
        cols = line.split("|")
        if len(cols) < 5:
            continue
        num = cols[1].strip().strip("*")
        ng += problems_in_cell(f"next_step の 5 やることの表 の {num}番", cols[3])
    return ng


def check_m2_todo(path: str) -> list:
    ng = []
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"{path} が読めない（{e}）"]

    def walk(o):
        if isinstance(o, dict):
            if "番号" in o and "触るファイル" in o:
                st = str(o.get("状態", ""))
                if "✅済" not in st and "保留" not in st:
                    ng.extend(problems_in_cell(f"m2_todo.json の {o['番号']}", str(o["触るファイル"])))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(data)
    return ng


def main() -> int:
    ns = sys.argv[1] if len(sys.argv) > 2 else NEXT_STEP
    todo = sys.argv[2] if len(sys.argv) > 2 else M2_TODO
    ng = check_next_step(ns) + check_m2_todo(todo)
    if ng:
        print(f"置き場の書かれていないファイル名が {len(ng)} 件あります:")
        for x in ng:
            print(f"  ❌ {x}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
