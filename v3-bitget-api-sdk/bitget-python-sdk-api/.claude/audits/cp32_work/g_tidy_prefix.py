"""監査 cp32｜別枠 G＝足した番人3件が、直す前のコードで本当に落ちるかを見る。

依頼書 §3.4 の G の逐語＝「★足したテストが、直す前のコードで本当に落ちるかを見てください」。

やり方
  1) いまの `.claude/tools/tidy_next_step.py` を、そのままの場所として読み込む
     （`__file__` を本物のパスにするので、ROOT の解決は本物と同じ）。
  2) コミット `52cf5a8`（この工事）の**直前**の版から `move_done_rows` を取り出し、
     読み込んだものに上書きする（＝直す前のコードに戻した状態を作る）。
  3) その状態で `selftest()` を走らせ、どの札が落ちるかを見る。

★本物のファイルは1文字も書き替えない（読むだけ・上書きは記憶の中だけ）。
"""
import pathlib
import re
import subprocess
import sys
import types

REPO = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SRC = REPO / ".claude/tools/tidy_next_step.py"
REL = ".claude/tools/tidy_next_step.py"
COMMIT = "52cf5a8^"


def load(text: str, name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__file__ = str(SRC)
    sys.modules[name] = mod
    exec(compile(text, str(SRC), "exec"), mod.__dict__)
    return mod


def func_src(text: str, fname: str) -> str:
    m = re.search(rf"^def {fname}\(.*?(?=^def |\Z)", text, re.M | re.S)
    if not m:
        raise SystemExit(f"{fname} が見つからない")
    return m.group(0)


old_text = subprocess.run(["git", "show", f"{COMMIT}:{REL}"], cwd=REPO,
                          capture_output=True, text=True, check=True).stdout
now_text = SRC.read_text(encoding="utf-8")

print(f"直す前の版＝{COMMIT}:{REL}（{len(old_text.splitlines())} 行）")
print(f"いまの版　＝{REL}（{len(now_text.splitlines())} 行）")

old_fn = func_src(old_text, "move_done_rows")
print("--- 直す前の見出しの取り方（逐語）---")
for ln in old_fn.splitlines():
    if "_hdr" in ln or "head_rows" in ln:
        print("  " + ln)
print("---")

print("\n■ いまのコード")
mod_now = load(now_text, "_tidy_now")
rc_now = mod_now.selftest()
print(f"  → 終了コード {rc_now}")

print("\n■ 直す前の move_done_rows に差し替えたコード")
mod_old = load(now_text, "_tidy_prefix")
exec(compile(old_fn, "<prefix move_done_rows>", "exec"), mod_old.__dict__)
rc_old = mod_old.selftest()
print(f"  → 終了コード {rc_old}")
