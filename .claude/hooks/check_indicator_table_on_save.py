#!/usr/bin/env python3
# check_indicator_table_on_save.py — 定義表（indicator_reference_diag.py）を保存する瞬間に、INDICATOR_TABLE の照らしを掛ける
#   （PreToolUse Write|Edit|MultiEdit・工事 m2c15-single-source-20261022・2026-10-22）
#
# まこさん指示（2026-10-22・逐語）＝「またあとで壮大なミスが発覚しないように、指標に関するデータはすべて確認をし直してから、設計案をつくれ」
#   「これ以上ミスで私に迷惑をかけないようにしろ」。
# なぜ要るか＝CC は 2026-08-10〜10-21 に、定義表の行に方向と性質を手で書き、札を別の表に手で書き、材料の検査を走らせなかった
#   （❌ 119件が 2026-10-22 まで見つからなかった）。保存の瞬間に照らせば、同じ型の食い違いは保存できない。
# 何をするか＝保存した後の中身を一時の置き場に置き、gen_indicator_table.py --verify --file <写し> を走らせる（判定を書き写さない）。
#   止まれば、その文を全部 出して保存を止める。
# 止めないとき（fail-open）＝相手が定義表でない／Write の中身が空／道具が走らせられない（理由を標準エラーに1行）。
# 使い方＝hook（標準入力に PreToolUse の json）／ 手で確かめる＝python3 .claude/hooks/check_indicator_table_on_save.py --check [--as <中身を書いたファイル>]
# 限界（正直に）＝Bash で書く道は見ない（土台ゲートが別に見る）。役割の読み取りの正しさは見ない。
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
PR = SDK / "scripts/priority_rebuild"
IREF = PR / "indicator_reference_diag.py"
TOOL = PR / "gen_indicator_table.py"


def text_after(tool: str, ti: dict, path: Path) -> str:
    if tool == "Write":
        return ti.get("content") or ""
    try:
        t = path.read_text(encoding="utf-8")
    except OSError:
        t = ""
    for e in (ti.get("edits") or []) if tool == "MultiEdit" else [ti]:
        old, new = e.get("old_string") or "", e.get("new_string") or ""
        t = t.replace(old, new) if e.get("replace_all") else t.replace(old, new, 1)
    return t


def verify_text(text: str) -> tuple[int, str]:
    if not TOOL.is_file():
        return 3, f"道具が無い（{TOOL}）"
    with tempfile.TemporaryDirectory(prefix="_iref_on_save_") as td:
        p = Path(td) / "indicator_reference_diag.py"
        p.write_text(text, encoding="utf-8")
        r = subprocess.run([sys.executable, str(TOOL), "--verify", "--file", str(p)], capture_output=True, text=True, cwd=str(SDK))
        return r.returncode, (r.stdout + r.stderr).strip()


def main() -> int:
    if "--check" in sys.argv:
        src = Path(sys.argv[sys.argv.index("--as") + 1]) if "--as" in sys.argv else IREF
        rc, out = verify_text(src.read_text(encoding="utf-8"))
        print(out)
        return 0 if rc == 0 else 1
    try:
        d = json.load(sys.stdin)
    except Exception:                                            # noqa: BLE001
        return 0
    tool, ti = str(d.get("tool_name") or ""), d.get("tool_input") or {}
    path = Path(str(ti.get("file_path") or ""))
    if path.resolve() != IREF.resolve():
        return 0
    text = text_after(tool, ti, path)
    if not text.strip():
        return 0
    rc, out = verify_text(text)
    if rc == 0:
        return 0
    if rc == 3:
        print(f"[check_indicator_table_on_save] 走らせられない＝止めない: {out}", file=sys.stderr)
        return 0
    print("🔒 [定義表を保存する瞬間の照らし] INDICATOR_TABLE と定義表の行・札の表・資料が合いません（保存を止めます）:", file=sys.stderr)
    print(out, file=sys.stderr)
    print("   ★手で確かめる口＝python3 .claude/hooks/check_indicator_table_on_save.py --check --as <中身を書いたファイル>", file=sys.stderr)
    print("   ★役割を直すときは資料の表を直し、python3 scripts/priority_rebuild/gen_indicator_table.py --write で作り直す", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
