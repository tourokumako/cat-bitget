#!/usr/bin/env python3
"""監査 cp31｜別枠7 の追い試し＝控えに複製される「生きている行」が、印を持っていたらどうなるか。

見つけたこと（x7_move_done_rows.py）＝`move_done_rows` が控えに書く見出しは
`_hdr[:2]`（区切りの行を除いた「|」で始まる行の先頭2本）なので、
表に生きている行が1本でも在ると、見出しの行 ＋ **生きている行1本** が控えに複製される。
ここでは、その生きている行が消してはいけない印を持っていた場合を試す。
★本物のファイルは1文字も触らない（この場で組み立てた文字列だけを使う）。
"""
import pathlib
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
sys.path.insert(0, str(ROOT / ".claude" / "tools"))
import tidy_next_step as T  # noqa: E402

TODAY = "2026-09-08"
SRC = ("# 次のセッションの起点\n\n"
       "### 0-1 いまの状態（2026-09-08）\n\nいまの状態。\n\n"
       "### 0-2 次にやること\n\n"
       "| 順 | やること | 状態 |\n|---|---|---|\n"
       "| 1 | 🔴 これは生きている行（★消さない） | まだ |\n"
       "| 2 | これは終わった | ✅済 |\n"
       "\n### 0-3 案内\n\nおわり。\n")

new_next, new_arc, rep = T.move_done_rows(SRC, "# archive\n", TODAY)
arc_added = new_arc[len("# archive\n"):]

print("■ 控えに足された中身")
for ln in arc_added.splitlines():
    print(f"  |{ln}")
print()
print(f"移した行 {rep['moved_rows']} 行 ／ 印 前 {rep['before']} → 後 {rep['after']} ＋ 移した分 {rep['moved']}")
print()
print("■ 数え直し")
print(f"  next_step に残った 🔴 の数            : {new_next.count('🔴')}")
print(f"  控えに入った 🔴 の数                  : {arc_added.count('🔴')}")
print(f"  移した行そのものに在る 🔴 の数        : {rep['moved'][0]}")
dup = arc_added.count("🔴") - rep["moved"][0]
print(f"  → 控えに複製された（移していない）🔴 : {dup} 個")
print()
print("■ 生きている行が、控えにそのまま入っているか")
live = "| 1 | 🔴 これは生きている行（★消さない） | まだ |"
print(f"  控えに在る  : {live in arc_added}")
print(f"  next_step にも在る（＝両方に在る＝複製）: {live in new_next}")
print()
print("■ 控えの表に、区切りの行（|---|---|---|）が在るか")
print(f"  {'在る' if '---' in arc_added.split(chr(10))[3] else '★無い（markdown の表として描画されない）'}")
