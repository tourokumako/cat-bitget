#!/usr/bin/env python3
"""監査 cp31｜別枠7＝控えへ移した行に付ける見出しの取り方を、端の場合で試す。

依頼書 §3.6 の逐語＝「見出しを元の表から取る形にしたことで、新しい不具合が入っていないか。
見出しの行が1つも無い表・見出しだけの表など、端の場合で落ちないかを見てください。」

★本物の `next_step.md` と `next_step_archive_202608.md` は1文字も触らない（読むだけ）。
  試すのは、この場で組み立てた文字列と、本物の 0-2 の節をそのまま写した控えだけ。
"""
import pathlib
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
sys.path.insert(0, str(ROOT / ".claude" / "tools"))
import tidy_next_step as T  # noqa: E402

TODAY = "2026-09-08"
HEAD = "# 次のセッションの起点\n\n"
S01 = "### 0-1 いまの状態（2026-09-08）\n\nいまの状態。\n\n"


def run(name: str, body: str) -> None:
    """1件 試して、結果を印字する（例外もそのまま出す）。"""
    src = HEAD + S01 + body + "\n### 0-3 置き場の案内\n\nおわり。\n"
    print("=" * 78)
    print(f"■ {name}")
    try:
        new_next, new_arc, rep = T.move_done_rows(src, "# archive\n", TODAY)
    except SystemExit as e:
        print(f"  → SystemExit（書かずに止まった）: {e}")
        return
    except Exception as e:                              # noqa: BLE001
        print(f"  → ★例外で落ちた: {type(e).__name__}: {e}")
        return
    print(f"  移した行 {rep['moved_rows']} 行")
    print("  --- archive に足された中身（ここから）---")
    for ln in new_arc[len("# archive\n"):].splitlines():
        print(f"  |{ln}")
    print("  --- ここまで ---")
    kept = [ln for ln in new_next.splitlines() if ln.lstrip().startswith("|")]
    print(f"  next_step に残った表の行 {len(kept)} 行: {kept}")


# ① ふつうの形（見出し＋区切り＋残る行1本＋終わった行1本）＝いまの本物に近い
run("① 見出し＋区切り＋残る行＋終わった行（ふつう）",
    "### 0-2 🔴 次にやること\n\n"
    "| 順 | やること | 触るもの | 出るもの | 状態 |\n"
    "|---|---|---|---|---|\n"
    "| 1 | これはまだ | a | b | まだ |\n"
    "| 2 | これは終わった | c | d | ✅済 |\n")

# ② 見出しの行が1つも無い（区切りだけ在って、終わった行が在る）
run("② 見出しの行が1つも無い（区切り＋終わった行だけ）",
    "### 0-2 🔴 次にやること\n\n"
    "|---|---|---|\n"
    "| 2 | これは終わった | ✅済 |\n")

# ③ 見出しだけ（見出し＋区切り＋終わった行・残る行なし）
run("③ 見出しと区切りだけ（残る行が無い）",
    "### 0-2 🔴 次にやること\n\n"
    "| 順 | やること | 状態 |\n"
    "|---|---|---|\n"
    "| 2 | これは終わった | ✅済 |\n")

# ④ 表が1行も無い（説明の文だけ）＝移す行が無い
run("④ 表が1行も無い（説明の文だけ）",
    "### 0-2 🔴 次にやること\n\n"
    "終わった行（✅済）は archive へ移します。\n")

# ⑤ 残る行が2本以上（見出しの取り方が『見出し＋最初の残る行』になっていないか）
run("⑤ 残る行が2本（見出し＋区切り＋残る行2本＋終わった行1本）",
    "### 0-2 🔴 次にやること\n\n"
    "| 順 | やること | 触るもの | 出るもの | 状態 |\n"
    "|---|---|---|---|---|\n"
    "| 1 | 残る行その1 | a | b | まだ |\n"
    "| 2 | 残る行その2 | c | d | まだ |\n"
    "| 3 | これは終わった | e | f | ✅済 |\n")

# ⑥ 本物の 0-2 の節をそのまま写した控え（読むだけ）＋終わった行を1本 差し込む
real = (ROOT / ".claude" / "state" / "next_step.md").read_text(encoding="utf-8")
lines = real.splitlines(keepends=True)
i = next(k for k, l in enumerate(lines) if l.startswith(T.H02))
j = T._section_end(lines, i)
sec = "".join(lines[i:j])
run("⑥ 本物の 0-2 の節をそのまま写し、終わった行を1本 足した",
    sec.rstrip("\n") + "\n| 9 | これは終わった | x | y | ✅済 |\n")
