#!/usr/bin/env python3
"""pdca_gate_body.py — pdca_gate.sh の判定の本体（旗を実体ファイルの中身で下ろす）

★別ファイルにした理由（2026-08-22・50回目）
  1. `pdca_flow.md` の決まり＝「今後 hook の python は -c 埋め込み禁止で別ファイル化」
     （2026-07-03 に pdca_mark.py が引用符の壊れで無言死した事故の対策）。
     `<<'PYEOF'` の埋め込みも同じ危険を持つ。
  2. **埋め込みのままだと、直したあとに走らせて確かめられない。**
     `/tmp` へ書き出して走らせるのは `enforce_observe_diag_only` が止める（正しい動作）。
     ファイルにすれば、そのまま走らせて確かめられる。

★何をするか＝Stop の時に、旗（pdca_need_*）を「実体ファイルの中身」で最終判定して下ろす。
  ・pdca_need_5q    ← ledger の最新エントリに 6つの問い ＋ 方針/狙い/目的 が在る
  ・pdca_need_claim ← 同じく【主張】が在る
  ・pdca_need_next_step ← next_step.md に4つの見出しが在り、かつ 改善の経緯の表が源と一致

★2026-08-22 の直し（まこさん決定 A・`next_step.md` §6 の59番）
  改善の経緯の判定を、いまの実物に合わせた。直す前は next_step.md の中の
  `ARC_TABLE_START`〜`ARC_TABLE_END` を探していたが、2026-08-16 に表を作るプログラムの
  出す先が improvement_arc.md へ変わり、next_step.md の印は 0件 になった
  ＝この条件は永久に真にならず、旗が立つとセッションを閉じられなくなっていた（実測）。
  探し方は `arc_doc_ok.py` の1か所だけが持つ（2か所に写さない・教訓 L-519）。

使い方
  python3 pdca_gate_body.py <state ディレクトリ>
  python3 pdca_gate_body.py --selftest
"""
from __future__ import annotations

import os
import re
import sys

LEDGER = ("/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/"
          "bitget-python-sdk-api/.claude/ratchet/ledger.md")
TOKS = ["【問0 前後比較】", "【問1 レバー】", "【問2 不足量】",
        "【問3 負け集中】", "【問4 過去接続】", "【問5 次仮説】"]
# ★next_step.md に必須の4つ（cat_requirements §8.3）。
#   1つの ( ) の中は「どれか1つ在ればよい言い方」＝同じことを指す言い換えです。
#   ★2026-08-22 に「次にやること」を足した理由（実測）＝いまの next_step.md に「本筋」は 0件。
#   2026-08-11 に文書の作りを変えたとき、§0 の見出しが「次にやること」になり、「本筋」の語が消えた。
#   ＝この条件も、改善の経緯の表と同じく「永久に真にならない」状態だった（59番の直しで判明）。
#   語を文書に足して合わせるのではなく、**判定の側を実物の言い方に合わせた**（飾りの語を増やさない）。
#   書き方＝`|` で区切ったものは「どれか1つ在ればよい」。★一覧はこの1行だけ（写しを作らない・L-519）。
NS_HEAD_WORDS = ["本筋|次にやること", "やってはいけない", "出典", "改善アーク"]
NS_HEADS = tuple(tuple(w.split("|")) for w in NS_HEAD_WORDS)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _arc_ok() -> bool:
    try:
        from arc_doc_ok import arc_doc_ok
        ok, _why = arc_doc_ok()
        return ok
    except Exception:
        return False        # 読めない＝通さない（fail-closed）


def judge_5q(ledger_text: str) -> bool:
    latest = re.split(r"\n## ", ledger_text)[-1] if ledger_text else ""
    return all(t in latest for t in TOKS) and any(k in latest for k in ("方針", "狙い", "目的"))


def judge_claim(ledger_text: str) -> bool:
    latest = re.split(r"\n## ", ledger_text)[-1] if ledger_text else ""
    return "【主張】" in latest


def judge_next_step(ns_text: str, arc_ok: bool) -> bool:
    """next_step.md に必須の4つが在り、かつ 改善の経緯の表が源と一致しているか。
    4つのそれぞれは、言い換えのどれか1つが在れば満たす。"""
    return all(any(w in ns_text for w in group) for group in NS_HEADS) and arc_ok


def run(state: str) -> None:
    def rm(p: str) -> None:
        try:
            os.remove(p)
        except FileNotFoundError:
            pass

    try:
        lg = open(LEDGER, encoding="utf-8", errors="ignore").read()
    except Exception:
        lg = ""
    if judge_5q(lg):
        rm(os.path.join(state, "pdca_need_5q"))
    if judge_claim(lg):
        rm(os.path.join(state, "pdca_need_claim"))
    try:
        ns = open(os.path.join(state, "next_step.md"), encoding="utf-8", errors="ignore").read()
    except Exception:
        ns = ""
    if judge_next_step(ns, _arc_ok()):
        rm(os.path.join(state, "pdca_need_next_step"))


def _selftest() -> int:
    ng: list[str] = []

    def chk(name: str, cond: bool) -> None:
        print(("  ✅ " if cond else "  ❌ ") + name)
        if not cond:
            ng.append(name)

    print("[pdca_gate_body] わざと壊して止まるか試すテスト")
    full5q = "\n## いま\n" + "".join(TOKS) + "方針: あれ"
    chk("T1 6つの問い＋方針が揃えば 5q は下りる", judge_5q(full5q))
    chk("T2 問いが1つ欠けると 5q は下りない", not judge_5q(full5q.replace("【問3 負け集中】", "")))
    chk("T3 方針/狙い/目的 が無いと 5q は下りない",
        not judge_5q("\n## いま\n" + "".join(TOKS)))
    chk("T4 【主張】が在れば claim は下りる", judge_claim("\n## いま\n【主張】あれ"))
    chk("T5 【主張】が無ければ claim は下りない", not judge_claim("\n## いま\nなし"))
    ns_ok = "本筋 やってはいけない 出典 改善アーク"
    chk("T6 4つの見出し＋表の一致で next_step は下りる", judge_next_step(ns_ok, True))
    chk("T7 ★表が源と一致しなければ next_step は下りない", not judge_next_step(ns_ok, False))
    chk("T8 見出しが1つ欠けると next_step は下りない",
        not judge_next_step(ns_ok.replace("出典", ""), True))
    chk("T8b 言い換え（本筋→次にやること）でも下りる",
        judge_next_step("次にやること やってはいけない 出典 改善アーク", True))
    chk("T8c 言い換えの側も欠けると下りない",
        not judge_next_step("やってはいけない 出典 改善アーク", True))
    # T9 いまの実物で、改善の経緯の表の判定が真になる（59番の直しが効いているか）
    chk("T9 ★いまの実物で 改善の経緯の表の判定が真になる（直す前は永久に偽だった）", _arc_ok())
    # T10 いまの next_step.md に4つの見出しが在る
    st = ("/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/next_step.md")
    try:
        nowns = open(st, encoding="utf-8", errors="ignore").read()
    except Exception:
        nowns = ""
    chk("T10 ★いまの next_step.md で、旗を下ろす条件が全部そろう",
        judge_next_step(nowns, _arc_ok()))
    print(f"[pdca_gate_body] {12 - len(ng)}/12 pass")
    return 1 if ng else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    if len(sys.argv) < 2:
        print("使い方: python3 pdca_gate_body.py <state ディレクトリ>", file=sys.stderr)
        sys.exit(2)
    run(sys.argv[1])
