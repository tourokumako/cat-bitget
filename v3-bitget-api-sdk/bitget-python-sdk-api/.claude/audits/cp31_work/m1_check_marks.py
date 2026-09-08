#!/usr/bin/env python3
"""監査 cp31｜M-1＝書き直した §7 Q5-5 の文が、実物の `check_marks` と合っているかを実測する。

依頼書 §3.2 の逐語＝「書き直した文が、実物と合っているか。まだ強く読める所が残っていないか。」

書き直した文（設計書 §7 Q5-5）の主張は2つ。
  主張1＝`check_marks` の式（前 = 後 + 移した分）は、本文を過不足なく分ける作りなので必ず成り立つ。
  主張2＝「この照合が守っているのは『行が消えてなくなること』だけ」。
ここでは主張1 を、消してはいけない印を持つ行で実際に試す（★本物のファイルは読むだけ）。
"""
import pathlib
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
sys.path.insert(0, str(ROOT / ".claude" / "tools"))
import tidy_next_step as T  # noqa: E402

TODAY = "2026-09-08"
BASE = ("# 次のセッションの起点\n\n"
        "### 0-1 いまの状態（2026-09-08）\n\nいまの状態。\n\n"
        "### 0-2 🔴 次にやること\n\n"
        "| 順 | やること | 状態 |\n|---|---|---|\n"
        "| 1 | 残る行 | まだ |\n"
        "{row}"
        "\n### 0-3 案内\n\nおわり。\n")


def one(name: str, row: str) -> None:
    src = BASE.format(row=row)
    before = T.count_marks(src)
    try:
        new_next, new_arc, rep = T.move_done_rows(src, "# archive\n", TODAY)
    except SystemExit as e:
        print(f"■ {name}\n  → ★止まった: {e}")
        return
    after = T.count_marks(new_next)
    moved = rep["moved"]
    ident = all(before[k] == after[k] + moved[k] for k in range(len(T.MARKS)))
    print(f"■ {name}")
    print(f"  移した行 {rep['moved_rows']} 行 ／ 印 前 {before} → 後 {after} ＋ 移した分 {moved}")
    print(f"  式（前 = 後 + 移した分）は {'成り立った' if ident else '★成り立たなかった'}"
          f" → 止まらずに控えへ {'移った' if rep['moved_rows'] else '移らなかった'}")
    gone = [m for k, m in enumerate(T.MARKS) if after[k] < before[k]]
    if gone:
        print(f"  ★next_step から消えた印: {gone}（控えには入っている＝行そのものは消えていない）")


one("① 消してはいけない印3つを全部 持つ行に ✅済 を付ける",
    "| 2 | 🔴 ★消さない 毎回消さない この行 | ✅済 |\n")
one("② 🔴 を持つ行に取り消し線を付ける",
    "| 2 | 🔴 ~~この行~~ | まだ |\n")
one("③ 印を持たないふつうの終わった行",
    "| 2 | ふつうの行 | ✅済 |\n")

print()
print("■ ④ check_marks を、式が崩れる値で直に呼ぶ（照合そのものは生きているか）")
try:
    T.check_marks(before=(3, 1, 1), after=(1, 0, 0), moved=(1, 1, 1))
    print("  → ★止まらなかった（照合が死んでいる）")
except SystemExit as e:
    print(f"  → 止まった: {e}")
    print("  ＝照合そのものは生きている。ただし move_done_rows は本文を過不足なく分けるので、"
          "この崩れた値が渡ることは無い（＝呼び出しの側では必ず成り立つ）。")
