#!/usr/bin/env python3
"""gen_windows.py — 期間（窓）の説明を機械生成する（まこさん OK 2026-07-27「各書類へ自動生成するように」）

なぜ作ったか
--------------------------------------------------------------------------
期間の数字が6箇所に分かれ、全部が古いままになっていた（2026-07-27 実測）:
  cat_requirements.md 146/175/331/334（採点窓が 2025-06〜2026-02 のまま）／
  acceptance_checklist.md 42（採点 2025-06〜12）／ adopted_strategies.md 90（同）／
  entry_exit_matrix.md 101（探索窓が2世代前の 2022-07〜12・ファイル名も旧 engine_search_e37）／
  window_similarity_ranking.md 8（反映先のファイル名が旧名）／ periods.py 43-44（探索窓が旧 2025-12〜2026-02）。
まこさんが期間の話で毎回混乱していた原因は記憶ではなく、この分散とずれ。

やること
--------------------------------------------------------------------------
  ① 数値は periods.py だけから取る（H8・唯一の正本・手打ちゼロ）。
  ② 読み物 .claude/ratchet/windows.md を全文生成する（経緯つき）。
  ③ 各文書の WINDOWS_START 〜 WINDOWS_END の間に、同じ表を差し込む（next_step の ARC 表と同じ方式）。
  ④ hash で改変を検出する（手で書き換えたら --verify が落ちる）。

使い方
--------------------------------------------------------------------------
  python3 scripts/priority_rebuild/gen_windows.py --write    # 生成・差し込み
  python3 scripts/priority_rebuild/gen_windows.py --verify   # 改変の検出
  python3 scripts/priority_rebuild/gen_windows.py --selftest # 材料が実体から取れているかの番人
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys

import pandas as pd

import periods

HERE = pathlib.Path(__file__).resolve().parent               # scripts/priority_rebuild/
ROOT = HERE.parent.parent                                    # bitget-python-sdk-api/
RATCHET = ROOT / ".claude" / "ratchet"
RULES = ROOT / ".claude" / "rules"
OUT = RATCHET / "windows.md"

START = "<!-- WINDOWS_START hash={h} ここは gen_windows.py が自動生成＝手で書き換えない -->"
START_RE = re.compile(r"<!-- WINDOWS_START hash=[0-9a-f]* [^>]*-->")
END = "<!-- WINDOWS_END -->"

# 差し込み先（この一覧が対象の正本・足すときはここへ1行）
TARGETS = [
    (RULES / "cat_requirements.md", "要件定義書＝大本。期間の原則を書く場所"),
    (RULES / "acceptance_checklist.md", "acceptance を書くときの照合リスト（H8）"),
    (RATCHET / "adopted_strategies.md", "採用ポートフォリオ台帳（どの窓で測った net か）"),
    (RATCHET / "entry_exit_matrix.md", "Entry×Exit 網羅マトリクス（層3 探索の窓）"),
    (RATCHET / "window_similarity_ranking.md", "窓の候補ランキング（選定の根拠）"),
]


def _d(ts: pd.Timestamp) -> str:
    return ts.strftime("%Y-%m-%d")


def _prev_day(ts: pd.Timestamp) -> str:
    """終端が排他の窓を『いつまで』の言い方に直す（読む人が1日ずれない）。"""
    return _d(ts - pd.Timedelta(days=1))


def _confirm_desc() -> str:
    """確認窓の説明文。値決め窓と同一の間は暫定の注記を機械で付ける（同一で
    なくなれば注記も自動で消える＝歩5 の窓の決め直しで手直し不要）。"""
    base = "engine_tuner。選んだ値のまま1回走らせて表示するだけ。選び直さない"
    if (periods.CONFIRM_START == periods.SEARCH_START
            and periods.CONFIRM_END == periods.SEARCH_END):
        return (base + "。暫定＝値決め窓と同一（まこさん確定 2026-07-30）のため "
                "B2 は判定不能表示。窓の決め直しは作り直し計画の歩5")
    return base


def rows() -> list[tuple[str, str, str]]:
    """期間の表（名前・いつ・使う道具）。数値は periods.py だけから取る。"""
    return [
        ("学習", f"〜{_prev_day(periods.TRAIN_END)}",
         "ML が教師で訓練する期間。固定ルールの改善では使わない"),
        ("捨て", f"{_d(periods.EMBARGO_START)} 〜 {_prev_day(periods.EMBARGO_END)}",
         "leak を防ぐ緩衝。採点には使わない。この中に確認窓が入る"),
        ("値決め", f"{_d(periods.SEARCH_START)} 〜 {_prev_day(periods.SEARCH_END)}",
         "engine_tuner ／ engine_search_e37。値を選ぶのはここだけ"),
        ("確認", f"{_d(periods.CONFIRM_START)} 〜 {_prev_day(periods.CONFIRM_END)}",
         _confirm_desc()),
        ("採点", f"{_d(periods.SCORE_START)} 〜 {_d(periods.SCORE_END)}",
         "score.py ／ observe_diag。採否を決める。探索には一切使わない"),
        ("封印", f"{_d(periods.SEAL_START)} 〜",
         "過剰適合の独立チェック用。いまは空。本番判断の前に決め直す"),
    ]


def table() -> str:
    out = ["| 期間の名前 | いつ | 何に使うか |", "|---|---|---|"]
    out += [f"| {a} | {b} | {c} |" for a, b, c in rows()]
    return "\n".join(out)


def block_body() -> str:
    """差し込むブロックの中身（表＋どこを見ればよいかの1行）。"""
    return (table() + "\n\n"
            "> 数値の正本＝`scripts/priority_rebuild/periods.py`。意味と経緯＝`.claude/ratchet/windows.md`。\n"
            "> どちらも手で書き換えない（`gen_windows.py --write` が作る・`--verify` が改変を検出する）。")


def block() -> str:
    body = block_body()
    h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    return START.format(h=h) + "\n" + body + "\n" + END


TEMPLATE = """<!-- WINDOWS_DOC_HASH={dochash} -->
# windows.md — 検証に使う期間の正本（gen_windows.py が自動生成＝手書き禁止）

⚠️ このファイルを手で書き換えないでください。数値は `scripts/priority_rebuild/periods.py` から
   機械で取っています。期間を変えるときは periods.py を直してから作り直します。

```
python3 scripts/priority_rebuild/gen_windows.py --write    # 作り直す
python3 scripts/priority_rebuild/gen_windows.py --verify   # 改変の検出
```

## この文書は何か

**検証に使う期間が、いつからいつまでで、何のためにあるのかを1枚にまとめたものです。**

期間の話は毎回混乱していました。原因は記憶ではありません。同じ数字が6箇所に書かれていて、
その全部が古くなっていたためです（2026-07-27 に実測して判明）。だから数値を持つ場所を
periods.py の1つだけにして、読む文書はそこから機械で作る形にしました。

## いま使っている期間

{table}

> 終わりが「〜◯日」と書いてある窓は、その日を含みます。コードの上では翌日0時を排他で持っています。

## 道具ごとに、どの期間を使うか

| 道具 | 使う期間 | なぜ |
|---|---|---|
| engine_tuner | 値決め窓＋確認窓 | 値を選ぶ道具。採点窓を使うと、その期間に一番合う値を選ぶことになる |
| engine_search_e37 | 値決め窓 | 同上（E37 の層3 探索器） |
| observe_diag | 採点窓だけ | 診断する道具。いまの相場で何が起きているかを見る |
| score.py | 採点窓だけ | 採否を決める審判。ここだけが公式の数字 |

## なぜこの期間なのか

**値決め窓は「値動きの構造が採点窓に近い期間」で選んでいます。時間の近さでは選んでいません。**

構造とは、ボラ・レンジ滞在率・急騰性・方向など15項目のことです。採点窓の15項目と、
候補の期間の15項目との距離を測って、近い順に並べます。全順位と測り方の正本は
`.claude/ratchet/window_similarity_ranking.md` です。

いまの値決め窓 {search} は、その順位で2位です。距離は 1.78 でした。

**距離1位の 2025-09〜12 は採用していません。** 5分リターンの尖度が基準の約8倍あり、
2025-10 の急落イベントを含むためです。急騰を切るツマミが、その1イベントに合わせて
過剰に調整される懸念から、まこさんが却下しました（2026-07-24）。

## 経緯（同じ議論を繰り返さないために）

| いつ | 値決め窓 | 選び方 | どうなったか |
|---|---|---|---|
| 2026-07-21 | 2022-07〜12 | 土台の月別「成績」が近い順で1位 | 探索窓ではプラスだったのに採点窓で月−$8.42 に反転して廃止。構造の距離で測り直すと29位相当だった |
| 2026-07-23 | 2025-12〜2026-02 | 時間の近さ（walk-forward 形） | ここで選んだ v59d は採点窓へ移った。構造の距離では8位相当 |
| 2026-07-24 | {search} | 値動きの構造の近さ（成績を使わない） | 現行。構造が遠い窓で選んだ値は移らず、近い窓で選んだ値は移った、という実測2件が根拠 |

**この表の意味**＝「成績が近い期間」で選ぶと失敗しました。「構造が近い期間」で選ぶと移りました。
だから時間的に新しい期間へ寄せるのは、それだけでは根拠になりません。

## やってはいけないこと

- 採点窓で値を選ぶこと。その期間に一番合う値が選ばれ、本番で再現しません（L-267）。
- 期間の数字を文書やコードに手で書くこと。periods.py から取ります（H8）。
- 道具ごとの期間を勝手に揃えること。診断は採点窓、値決めは値決め窓、と役割で分かれています。
- 「古い期間だから駄目」と言うこと。基準は構造の近さです。時間の新しさではありません。
- 決着済みの窓の選定を蒸し返すこと。上の経緯の表と `decisions.md` を先に読みます。

## 期間を変えるときの手順

0. **採点窓を変えたときは、値決め窓を選び直します。**
   `cd scripts/priority_rebuild && python3 window_similarity.py` を走らせます。
   新しい採点窓と構造が近い窓を、全期間から順位づけて出します。数分かかります。
   出た順位を `.claude/ratchet/window_similarity_ranking.md` へ保存し、**どれにするかはまこさんが決めます**。
   ★この手順を書いていなかったため、道具の存在が忘れられていました（2026-07-27 まこさん指摘）。
1. periods.py の数値を直します。ここが唯一の出どころです。
2. `python3 scripts/priority_rebuild/gen_windows.py --write` を走らせます。本書と各文書の差し込みが更新されます。
3. 変更の理由と、まこさんの決定の日付を periods.py のコメントへ残します。
4. 過去の net は旧窓で測った値なので、直接比較できません。土台を新しい窓で測り直します。

## この表が差し込まれている文書

{targets}

差し込みは `<!-- WINDOWS_START ... -->` から `<!-- WINDOWS_END -->` までです。
手で書き換えると `--verify` が落ちます。
"""


def doc() -> str:
    tg = "\n".join(f"- [{p.name}]({_rel(p)}) … {why}" for p, why in TARGETS)
    body = TEMPLATE.format(dochash="{dochash}", table=table(),
                           search=f"{_d(periods.SEARCH_START)}〜{_prev_day(periods.SEARCH_END)}",
                           targets=tg)
    h = hashlib.sha256(body.replace("<!-- WINDOWS_DOC_HASH={dochash} -->\n", "").encode("utf-8")).hexdigest()[:16]
    return body.format(dochash=h)


def _rel(p: pathlib.Path) -> str:
    """windows.md から見た相対パス（.claude/ratchet/ が基点）。"""
    try:
        return str(pathlib.Path("..") / p.relative_to(ROOT / ".claude"))
    except ValueError:
        return str(p)


def _splice(text: str, blk: str) -> tuple[str, bool]:
    """WINDOWS_START〜WINDOWS_END を差し替える。印が無ければ差し込まない（False を返す）。"""
    m = START_RE.search(text)
    if not m or END not in text[m.end():]:
        return text, False
    e = text.index(END, m.end()) + len(END)
    return text[:m.start()] + blk + text[e:], True


def write() -> int:
    OUT.write_text(doc(), encoding="utf-8")
    print(f"[書いた] {OUT.relative_to(ROOT)}（{len(doc().splitlines())} 行）")
    blk = block()
    miss = []
    for p, _why in TARGETS:
        if not p.exists():
            miss.append(f"{p.name}: ファイルが無い"); continue
        t = p.read_text(encoding="utf-8")
        new, ok = _splice(t, blk)
        if not ok:
            miss.append(f"{p.name}: WINDOWS_START/END の印が無い（先に印を置く）"); continue
        if new != t:
            p.write_text(new, encoding="utf-8")
            print(f"[差し込み] {p.relative_to(ROOT)}")
        else:
            print(f"[変更なし] {p.relative_to(ROOT)}")
    for m in miss:
        print(f"⚠️ [未差し込み] {m}")
    return 1 if miss else 0


def verify() -> int:
    ng = []
    if not OUT.exists():
        ng.append(f"{OUT.name} が無い（--write で作る）")
    elif OUT.read_text(encoding="utf-8") != doc():
        ng.append(f"{OUT.name} が実体と食い違う＝手で書き換えたか periods.py が変わった")
    blk = block()
    for p, _why in TARGETS:
        if not p.exists():
            ng.append(f"{p.name}: ファイルが無い"); continue
        t = p.read_text(encoding="utf-8")
        m = START_RE.search(t)
        if not m or END not in t[m.end():]:
            ng.append(f"{p.name}: WINDOWS_START/END の印が無い"); continue
        cur = t[m.start():t.index(END, m.end()) + len(END)]
        if cur != blk:
            ng.append(f"{p.name}: 差し込みが実体と食い違う")
    if ng:
        print("❌ 改変または未更新を検出:")
        for x in ng:
            print(f"   - {x}")
        print("   直し方: python3 scripts/priority_rebuild/gen_windows.py --write")
        return 1
    print(f"✅ windows.md と差し込み {len(TARGETS)} 件は実体と一致（数値の出どころ＝periods.py）")
    return 0


def selftest() -> int:
    """番人＝材料が実体から取れているか。手打ちの数字が混ざっていないか。"""
    ng = []
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    body = src.split('"""', 2)[2] if src.count('"""') >= 2 else src   # docstring を除く
    # ★窓の境目の日付が手打ちされていないか。まこさんの決定日など「経緯の日付」は対象外＝
    #   期間が変わっても経緯は変わらないため（区別せず全部の日付を禁じると経緯が書けない）。
    bounds = {_d(t) for t in (periods.TRAIN_END, periods.EMBARGO_START, periods.EMBARGO_END,
                              periods.SEARCH_START, periods.SEARCH_END, periods.CONFIRM_START,
                              periods.CONFIRM_END, periods.SCORE_START, periods.SCORE_END,
                              periods.SEAL_START)}
    for lit in sorted(b for b in bounds if b in body):
        ng.append(f"窓の境目の日付が手打ちされている: {lit}（periods.py から取ること・H8）")
    if "import periods" not in src:
        ng.append("periods を import していない（数値の正本から取っていない）")
    r = rows()
    if len(r) != 6:
        ng.append(f"期間の表が 6 行でない: {len(r)} 行")
    if _d(periods.SCORE_START) not in table() or _d(periods.SEARCH_START) not in table():
        ng.append("表に採点窓／値決め窓の実値が出ていない")
    b1, b2 = block(), block()
    if b1 != b2:
        ng.append("差し込みブロックが実行のたびに変わる（hash が安定しない）")
    if not TARGETS:
        ng.append("差し込み先が空")
    if ng:
        print("❌ 自己検査 NG:")
        for x in ng:
            print(f"   - {x}")
        return 1
    print(f"✅ 自己検査 OK（日付の手打ち 0・期間 {len(r)} 件・差し込み先 {len(TARGETS)} 件・hash 安定）")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="期間（窓）の正本文書を periods.py から機械生成する")
    ap.add_argument("--write", action="store_true", help="windows.md を作り、各文書へ差し込む")
    ap.add_argument("--verify", action="store_true", help="手による書き換え・未更新を検出する")
    ap.add_argument("--selftest", action="store_true", help="材料が実体から取れているかの番人")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.verify:
        sys.exit(verify())
    if a.write:
        sys.exit(write())
    print(doc())


if __name__ == "__main__":
    main()
