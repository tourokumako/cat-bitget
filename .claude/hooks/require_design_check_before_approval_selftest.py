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


def main() -> int:
    bad = 0
    for name, text, want in CASES:
        got = bool(asks(text))
        ok = got == want
        bad += 0 if ok else 1
        print(f"{'✅' if ok else '❌'} {name}（結果 {got}・期待 {want}）")
    print(f"[selftest] {len(CASES) - bad}/{len(CASES)}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
