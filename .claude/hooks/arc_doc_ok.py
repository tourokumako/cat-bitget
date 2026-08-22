#!/usr/bin/env python3
"""arc_doc_ok.py — 改善の経緯の表が、手で書き換えられていないかを見る（1か所）

新設: 2026-08-22（50回目・まこさん決定 A・`next_step.md` §6 の59番）。

★なぜ新設したか
  直す前は `pdca_gate.sh`:34 と `pdca_mark.py`:172 の2か所が、`next_step.md` の中の
  `<!-- ARC_TABLE_START hash=… -->` 〜 `<!-- ARC_TABLE_END -->` を探していた。
  ところが 2026-08-16 に、改善の経緯の表を作るプログラム（gen_improvement_arc.py）が
  作り直され、**出す先が `next_step.md` から `improvement_arc.md` に変わった**。
  その結果、`next_step.md` に印は 0件 になり、**2か所の判定は永久に真にならなくなった**
  ＝旗（pdca_need_next_step）が立つと、セッションを閉じる方法が無くなる（実測 2026-08-22）。
  表面化していなかったのは fast-mode が ON で pdca_gate が動いていなかったため。

★何を見るか（いまの実物に合わせた）
  `improvement_arc.md` の1行目の `<!-- ARC_DOC hash=<12桁> gen=gen_improvement_arc.py 手書き禁止 -->`。
  その行と、直後の改行1つを外した残り全部の sha256 の先頭12桁が、書いてある値と一致するかを見る。
  ＝gen_improvement_arc.py の `--verify` と同じ判定（あちらが正本・ここは同じ計算をする）。

★探し方を2か所に写さない（教訓 L-519）
  この1ファイルだけが探し方を持つ。`pdca_gate.sh` と `pdca_mark.py` は、ここを呼ぶだけ。

★限界（正直に書きます）
  ①印の手での偽造は見抜けません（本文と印を両方 書き換えれば通る＝明示の違反）。
  ②中身が正しいか（表の数字が本当か）は見ません。それは gen_improvement_arc.py の源の側の話です。

使い方
  python3 arc_doc_ok.py            # 一致していれば exit 0・していなければ exit 1（理由を stderr へ）
  python3 arc_doc_ok.py --selftest # わざと壊して止まるか試すテスト
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import sys

ARC_DOC = pathlib.Path(
    "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/"
    "bitget-python-sdk-api/.claude/ratchet/improvement_arc.md"
)
HASH_RE = re.compile(r"<!--\s*ARC_DOC hash=([0-9a-f]+)[^>]*-->")


def check_text(text: str) -> tuple[bool, str]:
    """文字列を受け取って、印と中身が合っているかを返す。(合っているか, 理由)"""
    m = HASH_RE.search(text)
    if not m:
        return False, "印の行（ARC_DOC hash=…）がありません＝手で書き換えられた疑い"
    # 印の行と、その直後の改行1つだけを外す（rstrip すると本文の末尾の改行まで落ちて必ず不一致になる）
    body = text[m.end():]
    if body.startswith("\n"):
        body = body[1:]
    now = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
    if now != m.group(1):
        return False, f"中身が印と合いません（書いてある {m.group(1)} ／ いまの中身 {now}）"
    return True, f"一致（印 {now}）"


def arc_doc_ok(path: pathlib.Path = ARC_DOC) -> tuple[bool, str]:
    """改善の経緯の表が、源と一致しているか。"""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"改善の経緯の表を開けません（{path}）: {e}"
    return check_text(text)


def _selftest() -> int:
    ng: list[str] = []

    def chk(name: str, cond: bool) -> None:
        print(("  ✅ " if cond else "  ❌ ") + name)
        if not cond:
            ng.append(name)

    print("[arc_doc_ok] わざと壊して止まるか試すテスト")
    # T1 本物が通る
    ok, why = arc_doc_ok()
    chk(f"T1 いまの実物は一致する（{why}）", ok)
    # T2 印が無ければ止まる
    ok2, _ = check_text("# 印のない文書\n本文だけ\n")
    chk("T2 印の行が無ければ止まる", not ok2)
    # T3 中身を1文字 変えると止まる
    real = ARC_DOC.read_text(encoding="utf-8")
    broken = real + "手で足した1行\n"
    ok3, _ = check_text(broken)
    chk("T3 本文を1行 足すと止まる", not ok3)
    # T4 印の値だけを書き換えると止まる
    ok4, _ = check_text(HASH_RE.sub("<!-- ARC_DOC hash=000000000000 -->", real, count=1))
    chk("T4 印の値だけを書き換えると止まる", not ok4)
    # T5 ファイルが無ければ止まる（fail-closed）
    ok5, _ = arc_doc_ok(pathlib.Path("/存在しない/improvement_arc.md"))
    chk("T5 ファイルが無ければ止まる（fail-closed）", not ok5)
    # T6 印の行を消すと止まる（＝印だけ消して本文を残す形）
    ok6, _ = check_text(HASH_RE.sub("", real, count=1))
    chk("T6 印の行だけを消すと止まる", not ok6)
    print(f"[arc_doc_ok] {6 - len(ng)}/6 pass")
    return 1 if ng else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    ok, why = arc_doc_ok()
    if not ok:
        print(f"[arc_doc_ok] ❌ {why}", file=sys.stderr)
    sys.exit(0 if ok else 1)
