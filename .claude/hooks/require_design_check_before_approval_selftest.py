#!/usr/bin/env python3
"""require_design_check_before_approval_selftest.py — 承認のお願いかどうかの見分け方を試す
（2026-10-17・187回目・まこさん「要とする。上記直す案で修正」）。本物の設計書と記録は触らない。

見る物＝承認のコマンドが、行の頭か、コピーするための囲み（```）の中にあるときだけ「お願い」と見ること。
  説明の文の途中にコマンドの形が出ても、お願いと見ないこと（2026-10-17 に CC の説明の文で止めた誤報）。
使い方＝python3 .claude/hooks/require_design_check_before_approval_selftest.py（全部 期待どおりなら exit 0）
"""
import importlib.util
import pathlib
import sys

PY = pathlib.Path(__file__).resolve().parent / "require_design_check_before_approval.py"
spec = importlib.util.spec_from_file_location("rdcba", PY)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
# 直す前の判定（関数が無いとき）＝返信のどこかにコマンドの形があれば、お願いと見る
asks = getattr(mod, "asks_approval", None) or (lambda t: mod.WORD_RE.search(t) is not None)

CMD = "bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh"
CASES = [
    ("R1 囲みの中のコマンド → お願い", f"承認をお願いします。\n\n```\n{CMD}\n```\n", True),
    ("R2 行の頭のコマンド → お願い", f"承認をお願いします。\n{CMD}\n", True),
    ("R3 字下げした行の頭のコマンド → お願い", f"承認をお願いします。\n    {CMD}\n", True),
    ("R4 説明の文の途中のコマンドの形（2026-10-17 に実際に止めた文）→ お願いでない",
     "私が返信に承認のコマンド（bash …approve_impl.sh）を書いてまこさんにお願いしたとき、ターンの終わりにこの hook が動きます。", False),
    ("R5 名前だけ → お願いでない", "承認のプログラム approve_impl.sh が同じ検査をします。", False),
    ("R6 囲みの中に別のコマンド・文の途中にコマンドの形 → お願いでない",
     "```\npython3 x.py --try\n```\n説明＝bash …approve_impl.sh の形は打たないでください。", False),
    ("R7 何も無い → お願いでない", "次の1本へ進みます。", False),
]

# ★2026-10-29（217回目・まこさん「１，よい」）＝仮当て A12 の許し（a12_fail_allowed）の見本。
#   許す＝gen_materials.py の T6 と、F6 の「壊す前から差し込みが古い」だけ。ほかの落ちが1つでも混ざれば止める。
T6 = "❌ T6: 素の状態で --verify が鳴っている（先に --write で直す）"
F6_OLD = "❌ F6: 壊す前から差し込みが古い＝先に --write が要る（engine_tuner_milestones.md）"
F6_DEAD = "❌ F6: 差し込みを書き換えても --verify が鳴らない（改変検出が死んでいる）"
A_CASES = [
    ("A1 T6 だけ → 許す", "gen_materials.py", 1, f"{T6}\n❌ 1 件", True),
    ("A2 F6 の差し込みが古い だけ → 許す", "gen_materials.py", 1, f"{F6_OLD}\n❌ 1 件", True),
    ("A3 T6 と F6 の差し込みが古い → 許す", "gen_materials.py", 1, f"{T6}\n{F6_OLD}\n❌ 2 件", True),
    ("A4 F6 の改変検出が死んでいる → 止める", "gen_materials.py", 1, f"{F6_DEAD}\n❌ 1 件", False),
    ("A5 F6 の差し込みが古い と別の落ち → 止める", "gen_materials.py", 1, f"{F6_OLD}\n❌ R1: 何か\n❌ 2 件", False),
    ("A6 ほかの道具の F6 の文 → 止める", "observe_diag.py", 1, f"{F6_OLD}\n❌ 1 件", False),
    ("A7 落ちの行が無い → 止める", "gen_materials.py", 1, "Traceback (most recent call last):", False),
]


def main() -> int:
    bad = 0
    for name, text, want in CASES:
        got = bool(asks(text))
        ok = got == want
        bad += 0 if ok else 1
        print(f"{'✅' if ok else '❌'} {name}（結果 {got}・期待 {want}）")
    for name, prog, rc, out, want in A_CASES:
        got = bool(mod.a12_fail_allowed(prog, rc, out))
        ok = got == want
        bad += 0 if ok else 1
        print(f"{'✅' if ok else '❌'} {name}（結果 {got}・期待 {want}）")
    n = len(CASES) + len(A_CASES)
    print(f"[selftest] {n - bad}/{n}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
