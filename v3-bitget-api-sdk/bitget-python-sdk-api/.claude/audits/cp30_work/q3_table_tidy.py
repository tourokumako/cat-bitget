"""監査 cp30｜Q3＝表の行の片づけが、本当に人の手を要らなくするか。

★本物の next_step.md と next_step_archive_202608.md は1文字も書き替えない。
  控えを監査の作業場に作り、そこに終わった行を差し込んで、道具の書き替えの口を丸ごと走らせる。
  ＝いままで「空の入力でしか動かしていない」（依頼書 Q3）状態を、本物の中身で埋める。

見るもの3つ（依頼書 Q3）
  1. `--write` が、0-2 の表の「✅済」と取り消し線の行を、本当に控えへ移すか
  2. 消してはいけない行（🔴・★消さない・毎回消さない）を消さないか
  3. 説明の文（表でない行）を巻き込まないか
"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
sys.path.insert(0, str(ROOT / ".claude" / "tools"))
import tidy_next_step as t  # noqa: E402

WORK = pathlib.Path(".claude/audits/cp30_work").resolve()
WORK.mkdir(parents=True, exist_ok=True)
NEXT_REAL = ROOT / ".claude" / "state" / "next_step.md"
ARC_REAL = ROOT / ".claude" / "state" / "next_step_archive_202608.md"
NEXT_COPY = WORK / "next_step_copy.md"
ARC_COPY = WORK / "next_step_archive_copy.md"

print("=" * 100)
print("監査 cp30 Q3｜表の行の片づけ（move_done_rows）を、本物の中身の控えで走らせる")
print("=" * 100)

text = NEXT_REAL.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)
s2 = next(i for i, l in enumerate(lines) if l.startswith(t.H02))
end = t._section_end(lines, s2)
rows = [(i, l) for i, l in enumerate(lines) if s2 <= i < end and l.lstrip().startswith("|")]
print(f"\n■ いまの本物の 0-2 の節: {s2 + 1} 行目〜{end} 行目 ／ 表の行 {len(rows)} 本")
for i, l in rows:
    print(f"   {i + 1:>4}: {l.rstrip()[:110]}")
done_now = [l for _i, l in rows if t.DONE_MARK in l or t.STRIKE_RE.search(l)]
print(f"\n■ いま『終わった行』は {len(done_now)} 本（依頼書の『実績は0行』の裏取り）")

# ── 本物の控えに、4通りの行を差し込む ────────────────────────────────────
ins = (
    "| 90 | 監査 cp30 の試しの行A（ふつうに終わった行） | ✅済（2026-09-08） |\n"
    "| 91 | 監査 cp30 の試しの行B（~~取り消し線~~） | まだ |\n"
    "| 92 | 監査 cp30 の試しの行C＝★消してはいけない印つき 🔴 ★消さない 毎回消さない | ✅済（2026-09-08） |\n"
)
expl = "監査 cp30 の試しの説明の文＝この文にも ✅済 と ~~取り消し線~~ が入っているが、表の行ではない。\n"
new_lines = lines[:end] + [ins, expl] + lines[end:]
NEXT_COPY.write_text("".join(new_lines), encoding="utf-8")
shutil.copy2(ARC_REAL, ARC_COPY)
before_marks = t.count_marks(NEXT_COPY.read_text(encoding="utf-8"))
print(f"\n■ 控えに差し込んだ行＝表の行3本（A ふつう・B 取り消し線・C 消してはいけない印つき）＋説明の文1本")
print(f"   差し込んだ後の印の数（🔴・★消さない・毎回消さない）＝{before_marks}")

# ── 道具の書き替えの口を、控えに対して丸ごと走らせる ────────────────────
print("\n■ `tidy_next_step.py` の書き替えの口を、控えに対して走らせる")
rc = t.do_write(NEXT_COPY, ARC_COPY, t.LIMIT)
print(f"   終了コード＝{rc}（0＝検査も通った／1＝移したが検査で ❌ が残った）")

after = NEXT_COPY.read_text(encoding="utf-8")
arc_after = ARC_COPY.read_text(encoding="utf-8")
after_marks = t.count_marks(after)

print("\n■ 結果")
for tag, needle in (("A ふつうに終わった行", "監査 cp30 の試しの行A"),
                    ("B 取り消し線の行", "監査 cp30 の試しの行B"),
                    ("C 消してはいけない印つきの行", "監査 cp30 の試しの行C"),
                    ("D 説明の文（表でない）", "監査 cp30 の試しの説明の文")):
    in_next = needle in after
    in_arc = needle in arc_after
    print(f"   {tag:<26} … next_step に残る={in_next} ／ archive に移った={in_arc}")

print(f"\n   印の数 前 {before_marks} → 後 {after_marks}"
      f"（差＝{tuple(b - a for b, a in zip(before_marks, after_marks))}）")
print("   ★『後』が減っていれば、その印の付いた行が §0 から出て行った（archive には在る）。")

# ── 検査 (f) が、片づけの後に通るか ──────────────────────────────────────
h2, g2 = t._pass(t.H2), t._pass(t.G2)
wd = t.latest_worklog_date(t.STATE)
res = t.verify(after, h2, g2, wd, t.LIMIT)
print(f"\n■ 片づけの後の検査（--verify 相当）＝❌ {len(res)} 件")
for x in res:
    print(f"   ❌ {x[:160]}")

print("\n■ 本物のファイルが無傷か")
print(f"   next_step.md   … 触っていない（この監査が書いたのは {NEXT_COPY}）")
print(f"   archive         … 触っていない（この監査が書いたのは {ARC_COPY}）")
print("=" * 100)
