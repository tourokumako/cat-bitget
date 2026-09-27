#!/usr/bin/env python3
"""gen_s22_map.py — §2.2 の項目を1つずつ抜き出し、設計書のどの節に落とすかを表にする。

なぜ作るか
----------
まこさん指摘 2026-09-10（逐語）＝「そもそもこれは §2.2 レンジ判定の検索方法 の通りに
設計してないのでは？」「まじで支離滅裂」。

93回目の私は §2.2 を1日で3回 読んだのに、設計書を書くとき段を1つも照らさなかった。
落とし損ねたもの＝段2b が丸ごと無い／段1・段2a を「1本 引くだけ」にした／
共通1（成績は R9 の3つ）が1行も無い／共通3（値は範囲＋粗い刻みで承認）を逆に書いた、ほか。

何をするか
----------
  1. `engine_tuner_milestones2.md` の §2.2 の節を機械で切り出す。
  2. その中の **共通の決まり**（箇条書き）と **段の表**（段0〜段5）を1行ずつ抜き出す。
     ★手で写さない（写すと、また落とす）。
  3. 対応表 `s22_map_src.json`（私が書く＝落とす先と理由）と突き合わせ、
     `s22_map.md` に「§2.2 の項目 × 設計書のどの節に落とすか」の表を書く。

  --write   表を s22_map.md に書く
  --show    書かずに画面に出す
  --verify  s22_map.md が手で書き換えられていないかを見る（再生成して一致するか）
  --items   抜き出した項目だけを出す（対応表を書く前に、項目の一覧を見るため）

fail-closed（黙って通さない・4つ）
  1. §2.2 の節が見つからない → 止まる
  2. 抜き出した項目が0件の種類が在る（共通の決まり／段）→ 止まる
  3. 抜き出した項目のうち、対応表に無いものが在る → 止まる（黙って落とさない）
  4. 対応表に在るのに、§2.2 から抜き出せない id が在る → 止まる（架空の項目を作らない）

限界（正直に）
  ・切り出しは見出しの文字に頼る。§2.2 の見出しを書き替えると止まる（黙って通さない）。
  ・「落とす先」と「落とさない理由」の中身が正しいかは、この道具は判じない。
    それは まこさんの目と、設計書を見る監査が見る。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
RATCHET = SDK / ".claude" / "ratchet"

SRC_MD = RATCHET / "engine_tuner_milestones2.md"
SRC_JSON = RATCHET / "s22_map_src.json"
DEST = RATCHET / "s22_map.md"

# §2.2 の節の切り出しに使う目印（実物の見出し・2026-09-10 時点）
SEC_START = "## §2.2 レンジ判定の検索方法"
SEC_END = "### §2.2-0"          # ★2026-09-27（監査 CP47）＝直す前は §2.2-0（機械が作る展開の表）の表まで段として拾っていた
MARK_COMMON = "**共通の決まり**"
MARK_STAGES = "**段**"

# ★§2.2-2＝設計に必ず入れる3件（まこさん指示 2026-09-10・逐語
#   「この件、毎回忘れて、設計に入れないし、やろうとしないから、絶対入れろ。
#     忘れないよに§2.2の周辺に書いておいて」）。
#   この3件も §2.2 の項目と同じ扱いで抜き出し、落とし先を書かないと表が作れない（fail-closed）。
SEC2_START = "### §2.2-2"
SEC2_END = "---"


def read_section() -> list:
    """milestones2 から §2.2 の節を切り出す。見つからなければ止まる（fail-closed 1）。"""
    if not SRC_MD.exists():
        raise SystemExit(f"[gen_s22_map] 正本が無い: {SRC_MD}（fail-closed）")
    lines = SRC_MD.read_text(encoding="utf-8").splitlines()
    beg = end = None
    for i, ln in enumerate(lines):
        if beg is None and ln.startswith(SEC_START):
            beg = i
        elif beg is not None and ln.startswith(SEC_END):
            end = i
            break
    if beg is None:
        raise SystemExit(f"[gen_s22_map] §2.2 の見出しが無い（探した文字＝{SEC_START}）（fail-closed）")
    if end is None:
        end = len(lines)
    return lines[beg:end]


def extract(sec: list) -> list:
    """§2.2 の節から項目を抜き出す。戻り＝[(id, 種類, 逐語), ...]。"""
    items = []
    i_common = i_stages = None
    for i, ln in enumerate(sec):
        if i_common is None and ln.strip().startswith(MARK_COMMON):
            i_common = i
        elif i_common is not None and ln.strip().startswith(MARK_STAGES):
            i_stages = i
            break
    if i_common is None:
        raise SystemExit(f"[gen_s22_map] 「{MARK_COMMON}」が無い（fail-closed）")
    if i_stages is None:
        raise SystemExit(f"[gen_s22_map] 「{MARK_STAGES}」が無い（fail-closed）")

    n = 0
    for ln in sec[i_common + 1:i_stages]:
        s = ln.strip()
        if s.startswith("- "):
            n += 1
            items.append((f"共通{n}", "共通の決まり", s[2:].strip()))

    m = 0
    for ln in sec[i_stages + 1:]:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if cells[0].startswith("---") or cells[0] == "段":
            continue
        m += 1
        stage_name = cells[0]
        body = cells[1]
        value = cells[2] if len(cells) > 2 else ""
        items.append((f"段{stage_name.split()[0]}", "段", f"{stage_name}｜{body}｜値＝{value}"))

    if n == 0:
        raise SystemExit("[gen_s22_map] 共通の決まりが0件（fail-closed 2）")
    if m == 0:
        raise SystemExit("[gen_s22_map] 段が0件（fail-closed 2）")
    return items


def read_section2() -> list:
    """§2.2-2（設計に必ず入れる3件）を切り出す。見つからなければ止まる（fail-closed 5）。"""
    lines = SRC_MD.read_text(encoding="utf-8").splitlines()
    beg = end = None
    for i, ln in enumerate(lines):
        if beg is None and ln.startswith(SEC2_START):
            beg = i
        elif beg is not None and ln.strip() == SEC2_END:
            end = i
            break
    if beg is None:
        raise SystemExit(
            f"[gen_s22_map] §2.2-2 の見出しが無い（探した文字＝{SEC2_START}）（fail-closed 5）"
            "＝まこさん指示 2026-09-10「絶対入れろ」の3件が消えている")
    return lines[beg:end if end is not None else len(lines)]


def extract2(sec: list) -> list:
    """§2.2-2 の表から3件を抜き出す。戻り＝[(id, 種類, 中身), ...]。"""
    items = []
    for ln in sec:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 3:
            continue
        head = cells[0].strip("* ")
        if head.startswith("---") or head == "#":
            continue
        if head not in ("A", "B", "C"):
            continue
        items.append((f"必ず入れる{head}", "設計に必ず入れる（§2.2-2）",
                      f"{cells[1]}｜効く所＝{cells[3] if len(cells) > 3 else ''}"))
    if not items:
        raise SystemExit("[gen_s22_map] §2.2-2 の3件が抜き出せない（fail-closed 5）")
    return items


def load_src() -> dict:
    if not SRC_JSON.exists():
        raise SystemExit(f"[gen_s22_map] 対応表が無い: {SRC_JSON}（先に書く）")
    return json.loads(SRC_JSON.read_text(encoding="utf-8"))


def build() -> str:
    sec = read_section()
    items = extract(sec)
    items += extract2(read_section2())          # ★§2.2-2 の3件も同じ扱いで並べる
    src = load_src()
    rows = src.get("落とし先", {})

    ids = [i[0] for i in items]
    missing = [i for i in ids if i not in rows]
    if missing:
        raise SystemExit(
            f"[gen_s22_map] 対応表に無い項目が在る: {missing}（fail-closed 3＝黙って落とさない）")
    extra = [k for k in rows if k not in ids]
    if extra:
        raise SystemExit(
            f"[gen_s22_map] §2.2 に無い id が対応表に在る: {extra}（fail-closed 4＝架空の項目を作らない）")

    L = []
    add = L.append
    add("# §2.2 の項目 × M2-E-2 の設計書のどの節に落とすか")
    add("")
    add("**★この表はプログラムが作ります（手で書き換えない）。**"
        "左の3列（項目・種類・§2.2 の逐語）は "
        "`engine_tuner_milestones2.md` の §2.2 から機械で抜き出しています。"
        "右の2列は `s22_map_src.json` に私が書いたものです。")
    add("")
    add("**なぜ在るか**＝2026-09-10 に、私が §2.2 を3回 読んだうえで、"
        "設計書に段を1つも落とさなかったためです。"
        "まこさんの逐語＝「そもそもこれは §2.2 レンジ判定の検索方法 の通りに設計してないのでは？」。")
    add("")
    add("**読み方**＝「落とす先」の欄が **落とさない** の行は、"
        "§2.2 の逐語に対して落とさない理由が書いてあります。理由の無い行は作れません（止まります）。")
    add("")
    add("| # | 種類 | §2.2 の逐語（抜き出し） | 設計書の落とす先 | どう落とすか・落とさない理由 |")
    add("|---|---|---|---|---|")
    n_drop = 0
    for _id, kind, text in items:
        r = rows[_id]
        dest = str(r.get("落とす先", "")).strip()
        how = str(r.get("どう落とすか", "")).strip()
        if not dest or not how:
            raise SystemExit(f"[gen_s22_map] {_id} の落とす先か理由が空（fail-closed）")
        if dest == "落とさない":
            n_drop += 1
        t = text.replace("|", "／")
        add(f"| **{_id}** | {kind} | {t} | {dest} | {how} |")
    add("")
    add("## まとめ")
    add("")
    add(f"**§2.2 の項目＝{len(items)}件。**そのうち"
        f" **落とす {len(items) - n_drop}件** ／ **落とさない {n_drop}件**（理由つき）。")
    add("")
    add("**★この表は「どこに落とすか」を決めただけです。**"
        "設計書の中身が §2.2 のとおりかは、設計書そのものを読んで確かめます。")
    add("")
    return "\n".join(L)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true", help="表を書く")
    p.add_argument("--show", action="store_true", help="書かずに画面に出す")
    p.add_argument("--verify", action="store_true", help="手で書き換えられていないかを見る")
    p.add_argument("--items", action="store_true", help="抜き出した項目だけを出す")
    a = p.parse_args()

    if a.items:
        items = extract(read_section())
        print(f"§2.2 から抜き出した項目＝{len(items)}件")
        for _id, kind, text in items:
            print(f"  {_id}\t{kind}\t{text}")
        return 0

    if a.verify:
        if not DEST.exists():
            print(f"❌ {DEST} が無い")
            return 1
        now = DEST.read_text(encoding="utf-8")
        if now.rstrip("\n") == build().rstrip("\n"):
            print(f"✅ --verify 一致: {DEST}")
            return 0
        print(f"❌ --verify 不一致: {DEST}（手で書き換えたか、正本が変わった）")
        return 1

    body = build()
    if a.write:
        DEST.write_text(body, encoding="utf-8")
        print(f"✅ --write 完了: {DEST}（{len(body.splitlines())}行）")
        return 0
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
