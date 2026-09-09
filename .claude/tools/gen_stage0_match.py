#!/usr/bin/env python3
"""gen_stage0_match.py — §2.2 の候補と、成績表の材料を突き合わせる（段0 の①）。

なぜ作るか
----------
まこさん指示 2026-09-09（逐語）＝「その突き合わせを作る。」

何が問題か（2026-09-09 に実測して分かったこと）
  §2.2（レンジ判定の検索方法・まこさん決定 2026-09-01）は、探す候補を
  **指標の名前**で書いている（例＝「転換線・基準線」「帯内位置%」）。
  ところが engine_tuner は、材料を **役割**（env／location／sufficiency／trigger）で引く。
  この2つが噛み合っているかを、誰も突き合わせていなかった。
  実測の例＝段1 は location から引く段だが、そこが名指しする「転換線・基準線」は
  成績表の location に0列で、132列は全部 env に入っていた。

何をするか
----------
  §2.2 の段ごとの候補を1つずつ、成績表（material_ranking.json）で探し、
  「どの役割の・どの性質に・何列 在るか」を表にする。
  その段が引く役割に0列なら、その候補はその段では引けない＝表に ❌ と出す。

  --write   突き合わせ表を stage0_match.md に書く
  --show    書かずに画面に出す

★候補の一覧は、この道具の中に手で書く（§2.2 が手書きの節なので、機械で読めない）。
  ★出どころ＝engine_tuner_milestones2.md の §2.2 の段の表（166〜173行）。
  ★1つも落とさない＝§2.2 に書いてある候補を全部 並べる（落とすと下の検査で止まる）。

fail-closed（黙って通さない・2つ）
  1. 成績表が読めない → 止まる
  2. 候補の一覧が空の段が在る → 止まる（段を黙って飛ばさない）

限界（正直に）
  ・名前で探すので、成績表の列名と §2.2 の書き方がずれていると「無い」と出る。
    ずれか、本当に無いかは、出た表を人が見て判じる。
  ・この道具は「在るか無いか」を数えるだけ。使うべきかどうかは判じない。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
RATCHET = SDK / ".claude" / "ratchet"

RANKING = RATCHET / "material_ranking.json"
DEST = RATCHET / "stage0_match.md"

# ── §2.2 の段ごとの候補（出どころ＝milestones2 の §2.2 の表・166〜173行）──
#   形＝(段の名前, その段が引く役割, [(候補の名前, 成績表で探す文字), ...])
#   ★「その段が引く役割」は、§2.2 の段の中身から読み取ったもの。
#     段1＝帯（構造・位置）＝location／段2a＝トレンドの強さ＝env／
#     段2c＝ばらつき・出来高・位置形・時刻＝sufficiency（型の表で ボラ・出来高・需給・オシレーター）。
STAGES = [
    ("段1 帯（R1・R3・R7）", "location", [
        ("レンジ幾何 W%", "W%"),
        # ★2026-09-09＝成績表に「帯内位置」という名前は無い。近いのは「ABER位置」「HWC位置」
        #   「fib位置20」「fib位置96」の4種（実測）。§2.2 が指すのがこれかは、まこさんの判断が要る。
        ("帯内位置%（成績表では「◯◯位置」）", "位置"),
        ("S-Rタッチ数", "S-Rタッチ"),
        ("pivot 3種", "pivot"),
        # ★2026-09-09＝探す文字を実物に合わせた。成績表の列名は「close vs 24本高値%」の形で、
        #   「高安」という語は使っていない（実測）。§2.2 の「n本高安」はこの2つを指す。
        ("n本高値", "本高値%"),
        ("n本安値", "本安値%"),
        # ★成績表の列名は「close vs EMA20%」の形（％が後ろ）。§2.2 の「close vs EMA%」と書き方が違う。
        ("close vs EMA", "close vs EMA"),
        ("close vs SMA", "close vs SMA"),
        ("Keltner", "Keltner"),
        ("POC", "POC"),
        ("VAH", "VAH"),
        ("VAL", "VAL"),
        ("転換線", "転換線"),
        ("基準線", "基準線"),
    ]),
    ("段2a 強さの否定（R5・C1）", "env", [
        ("ADX", "ADX"),
        ("CHOP", "CHOP"),
        ("ER", "ER"),
        ("VHF", "VHF"),
        ("MACDヒスト%", "MACDヒスト%"),
        # ★2026-09-09＝成績表の列名は「EMA20傾き%」の形（期間が間に入る）。
        #   §2.2 の「EMA傾き」と書き方が違うだけで、材料は在る。
        ("EMA傾き（成績表では EMA◯◯傾き%）", "EMA"),
        ("DI差", "DI差"),
    ]),
    ("段2c 3枠目（R2・R6・R10）", "sufficiency", [
        ("BB幅", "BB幅"),
        ("ATR%", "ATR%"),
        ("realized_vol", "realized_vol"),
        ("Donchian幅", "Donchian"),
        ("stdev%", "stdev%"),
        ("volume_ratio", "volume_ratio"),
        ("CMF", "CMF"),
        ("BB%b", "BB%b"),
        ("経過バー", "経過"),
    ]),
]

ROLES = ("env", "location", "sufficiency", "trigger")


def load_ranking() -> dict:
    """成績表を読む。読めなければ止まる（fail-closed の1つ目）。"""
    if not RANKING.exists():
        raise SystemExit(f"[gen_stage0_match] 成績表が無い: {RANKING}（fail-closed）")
    return json.loads(RANKING.read_text(encoding="utf-8"))


def columns_of(rank: dict, role: str) -> list:
    """その役割に載っている列の名前を全部 集める。戻り＝[(列名, 性質), ...]。"""
    out = []
    for label, by_horizon in (rank.get("順位", {}).get(role) or {}).items():
        for _hor, rows in (by_horizon or {}).items():
            for r in rows:
                out.append((str(r[0]), label))
    return out


def count_hits(cols: list, needle: str) -> tuple:
    """その文字を含む列が何本 在るか。戻り＝(本数, 性質ごとの内訳)。"""
    hit = [(c, lab) for (c, lab) in cols if needle in c]
    by_label = {}
    for _c, lab in hit:
        by_label[lab] = by_label.get(lab, 0) + 1
    return len(hit), by_label


def build() -> str:
    """突き合わせ表を組み立てる。"""
    rank = load_ranking()
    cols_by_role = {r: columns_of(rank, r) for r in ROLES}

    L = []
    add = L.append
    add("# 段0 の①｜§2.2 の候補と、成績表の材料の突き合わせ")
    add("")
    add("**★この表はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`engine_tuner_milestones2.md` の §2.2 の段の表と、"
        "`material_ranking.json`。")
    add("")
    add("**なぜ在るか**＝§2.2 は探す候補を**指標の名前**で書き、"
        "engine_tuner は材料を**役割**で引きます。その2つが噛み合っているかを、"
        "誰も突き合わせていませんでした。")
    add("")
    add("**読み方**＝「その段の役割」の欄が **0** なら、その候補はその段では引けません。"
        "他の役割に列が在るなら、役割がずれているということです。")
    add("")

    ng_total = 0
    for stage, role, cands in STAGES:
        if not cands:
            raise SystemExit(f"[gen_stage0_match] 候補が空の段が在る: {stage}（fail-closed）")
        add(f"## {stage}")
        add("")
        add(f"**この段が引く役割＝`{role}`**")
        add("")
        add("| 候補（§2.2 の書き方） | この段の役割に何列 | 性質の内訳 | 他の役割に在る分 | 判定 |")
        add("|---|---|---|---|---|")
        for name, needle in cands:
            n, by_label = count_hits(cols_by_role[role], needle)
            others = []
            for r in ROLES:
                if r == role:
                    continue
                m, _b = count_hits(cols_by_role[r], needle)
                if m:
                    others.append(f"{r} {m}")
            inner = "・".join(f"{k} {v}" for k, v in sorted(by_label.items())) if by_label else "—"
            other_s = "・".join(others) if others else "—"
            if n > 0:
                verdict = "✅ 引ける"
            elif others:
                verdict = "❌ 役割がずれている"
                ng_total += 1
            else:
                verdict = "❌ 成績表に無い"
                ng_total += 1
            add(f"| {name} | **{n}** | {inner} | {other_s} | {verdict} |")
        add("")

    add("## まとめ")
    add("")
    add(f"**引けない候補＝{ng_total}件。**この数だけ、§2.2 の段が"
        "そのままでは回りません。")
    add("")
    add("**引けない理由は2通りです。**役割がずれているもの（成績表の別の役割に列が在る）と、"
        "成績表にそもそも無いもの。前者は、その段が引く役割を変えるか、"
        "型の表を見直すかの判断が要ります。後者は、材料を足すかどうかの判断が要ります。")
    add("")
    add("**★この表は「在るか無いか」を数えただけです。**どうするかは決めていません。")
    add("")
    return "\n".join(L)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true", help="突き合わせ表を書く")
    p.add_argument("--show", action="store_true", help="書かずに画面に出す")
    a = p.parse_args()
    body = build()
    if a.write:
        DEST.write_text(body, encoding="utf-8")
        print(f"✅ --write 完了: {DEST}（{len(body.splitlines())}行）")
        return 0
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
