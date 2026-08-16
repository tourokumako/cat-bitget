#!/usr/bin/env python3
"""gen_cat_requirements.py — 要件定義書 cat_requirements.md を機械生成する（手書き禁止）

なぜ機械生成にするか（まこさん OK 済みの方針・2026-08-08）
--------------------------------------------------------------------------
旧版は 373 行の手書きだった。手書きだと、書いてあることと実物がずれても誰も気づかない。
2026-08-08 に §4.6（決まり16個）を実物と1件ずつ突き合わせた結果:

    実在して効いている 7 件 / 書いてある強制が実物と食い違う 5 件 / 強制が無く人任せ 4 件

食い違いの例＝H2・H6 の担保先 train_p23_entry_E8b.py は現役の場所に無く archive にしかない。
H11 の DSR・PBO は score.py に 0 件。H14 の実物は ALLOW_LIVE_ORDERS = True。
＝「書いてある」と「効いている」が別物になっていた。

この生成器は、**②いま守られているか ③どこを見てそう言えるのか を、毎回 実物のファイルを
開いて機械で書く**。CC が手で書かないので、実物が変われば文書も変わる。

まこさんが決めた方針（2026-08-08・逐語つき）
--------------------------------------------------------------------------
  1. ファイル名は変えない（hook と他文書がこの名前で参照している）。旧版は archive へ残す
  2. 手書きで作り直さない。json を正本にして機械生成＋改変検出
  3. 消す判断を CC がしない。★本文は原文をそのまま持つ。消すかどうかは まこさんが1件ずつ決める
  4. ML は消さない（逐語＝「利益最大化に必要なら使いたい。現状は私の意図通りに実装して
     もらえない状況なので固定値に切り替えているだけ」）＝「いまは使っていない」と状態を書くだけ
  5. 1枚にまとめる。分けない（逐語＝「私が読める状態で１枚にまとめるでいいのでは？なんで分ける？」）
  6. 決まり1つにつき「①何を守るのか ②いま守られているか ③どこを見てそう言えるのか」を日本語で

使い方
--------------------------------------------------------------------------
  python3 gen_cat_requirements.py                 # 下書きを画面に出す
  python3 gen_cat_requirements.py --write         # 下書きをファイルに書く（作りかけの間はこちら）
  python3 gen_cat_requirements.py --final         # 本番の .claude/rules/cat_requirements.md へ書く
  python3 gen_cat_requirements.py --verify        # 手書き改変の検出
  python3 gen_cat_requirements.py --selftest      # 番人（わざと壊して落ちるか）
"""
from __future__ import annotations

import argparse
import hashlib
import re
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]                                    # bitget-python-sdk-api/
SRC = ROOT / ".claude" / "ratchet" / "cat_requirements.json"
DRAFT = ROOT / ".claude" / "ratchet" / "cat_requirements_draft.md"
# ★GENERATES＝この道具が作る文書の名乗り（2026-08-16 新設・まこさん決定 A）。
#   なぜ要るか＝名前で数えると必ず漏れる（出力先の変数名が道具ごとにバラバラで、
#   読むファイルと作るファイルが同じ形で並んでいる＝外から見分けられない）。
#   だから道具の側に名乗らせる。集める道具＝gen_docmap.py。
#   形＝(リポジトリの根からのパス, "まるごと" か "一部の節")。
GENERATES = [
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/cat_requirements.md", "まるごと"),
]

FINAL = ROOT / ".claude" / "rules" / "cat_requirements.md"

# json の item に書ける欄の全部。ここに無い名前を書くと中身が文書に出ないので selftest が止める
KNOWN_ITEM_KEYS = frozenset({"id", "title", "protects", "body", "sources", "enforced_by", "state", "coverage"})
KNOWN_SOURCE_KEYS = frozenset({"file", "anchor", "why", "quote"})
KNOWN_KINDS = frozenset({"code", "hook", "test", "doc", "none", "fact"})


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _resolve(rel: str) -> pathlib.Path:
    return (ROOT / rel).resolve()




def _split_outside(text: str) -> list[str]:
    """括弧の外の「 / 」「／」だけで分ける。★1文字も消さない（区切り記号だけを外す）。

    背景（2026-08-08 まこさん指摘「文章がぐちゃぐちゃ。メモレベル」）＝旧版は
    「A ... / B ... / C ... / D ... / E ... / F ... / G ... / H ...」のように
    8個の項目が1行に詰まっていて読めなかった。分けて番号を振れば読める。
    ★括弧の中の / は分けない（例『`/audit`』『LONG4/SHORT5』）。
    """
    OPEN, CLOSE = "（(「『【[{", "）)」』】]}"
    out, buf, depth, tick = [], [], 0, False
    i = 0
    while i < len(text):
        c = text[i]
        if c == "`":
            tick = not tick
        if not tick:
            if c in OPEN:
                depth += 1
            elif c in CLOSE:
                depth = max(0, depth - 1)
        if depth == 0 and not tick:
            if c == "／":
                out.append("".join(buf)); buf = []; i += 1; continue
            # 「 / 」「）/ 」の両方を区切りにする。前後とも空白が無いもの（LONG4/SHORT5 等）は分けない
            if c == "/":
                before_sp = i > 0 and text[i-1] == " "
                after_sp = i + 1 < len(text) and text[i+1] == " "
                if before_sp or after_sp:
                    out.append("".join(buf)); buf = []; i += 2 if after_sp else 1; continue
        buf.append(c); i += 1
    out.append("".join(buf))
    parts = [x.strip() for x in out if x.strip()]
    norm = lambda t: t.replace("／", "").replace("/", "").replace(" ", "").replace("\u3000", "")
    if norm("".join(parts)) != norm(text):
        return [text]
    return parts


def _expand_windows(lines: list[str]) -> list[str]:
    """WINDOWS_START〜END マーカーを periods.py 由来の最新の表へ差し替える（2026-08-08 新設）。

    背景＝この差し替えは元々「まだ作り直していない節（raw）」だけに効いていた。§3.2 等を
    items（作り直した節）へ変換すると、そのままでは期間の表が差し替えられず、原文の日付が
    そのまま固まって残る＝H8（期間の数字は periods.py だけが正本）に反する。
    raw・items のどちらの本文にも同じ差し替えを効かせるため、共通の関数にした。
    """
    txt = "\n".join(lines)
    if "WINDOWS_START" not in txt:
        return lines
    import gen_windows as _gw
    txt = re.sub(r"<!-- WINDOWS_START.*?<!-- WINDOWS_END -->", _gw.block(), txt, flags=re.S)
    return txt.split("\n")


def _readable(lines):
    """決まりの本文を読める形に組み直す（★中身は1文字も消さない・改行と番号を足すだけ）。"""
    out = []
    for ln in lines:
        m = re.match(r"^\s*[-*]\s+\*\*(.+?)\*\*[:：]\s*(.+)$", ln)
        if m:
            head, rest = m.group(1), m.group(2)
            parts = _split_outside(rest)
            if len(parts) >= 3:
                if out and out[-1].strip():
                    out.append("")          # 直前の段落と見出しの間を空ける
                out.append(f"**{head}**")
                out.append("")
                for k, x in enumerate(parts, 1):
                    out.append(f"{k}. {x}")
                out.append("")
                continue
        m2 = re.match(r"^\s*[-*]\s+(?!\*\*)(.+)$", ln)
        if m2:
            parts = _split_outside(m2.group(1))
            if len(parts) >= 3:
                for k, x in enumerate(parts, 1):
                    out.append(f"{k}. {x}")
                out.append("")
                continue
        out.append(ln)
    while out and not out[-1].strip():
        out.pop()
    return out


def check_source(src: dict) -> tuple[bool, str]:
    """③どこを見てそう言えるのか＝出典のファイルと、その中の目印を実物で確かめる。"""
    p = _resolve(src["file"])
    if not p.exists():
        return False, f"❌ ファイルが無い（{src['file']}）"
    anchor = src.get("anchor")
    if not anchor:
        return True, f"✅ 実在（{src['file']}）"
    txt = p.read_text(encoding="utf-8", errors="replace")
    if anchor in txt:
        ln, line = next((i, l) for i, l in enumerate(txt.splitlines(), 1) if anchor in l)
        msg = f"✅ 実在（{src['file']} の {ln} 行目に「{anchor}」）"
        # ★quote を付けると、その行の実物をここに引用する（2026-08-08 新設）。
        #   狙い＝本文の記述と、出典の実物を、まこさんが並べて見られるようにする。
        #   実例＝§1.2.1 の「E37（ショートのみ）」と、台帳の実物 e37=...,both,... の食い違いは
        #   語の照合では自動判定できない。実物を横に置けば人が1秒で気づける。
        if src.get("quote"):
            msg += f"\n  - **出典の実物** = `{line.strip()[:300]}`"
        return True, msg
    return False, f"❌ ファイルは在るが「{anchor}」が見当たらない（{src['file']}）"


def check_enforce(e: dict) -> tuple[bool, str]:
    """②いま守られているか＝強制の実体を実物のソースで確かめる。"""
    kind = e.get("kind", "none")
    if kind == "none":
        return True, "⬜ 機械の強制なし"
    if kind == "fact":
        # ★「強制」ではなく「実物を数えた結果」（2026-08-08 新設）。
        #   狙い＝「書いてある予定」と「いま実際にどうなっているか」を分けて出す。
        #   実例＝§2.3 は「ML 化する」と書いてあるが、いま動いている主なものは固定ルール。
        #   0 件でも食い違いにしない（数えた事実を出すだけ）。
        p2 = _resolve(e["file"])
        if not p2.exists():
            return True, f"📊 実測＝ファイルが無い（{e['file']}）"
        t2 = p2.read_text(encoding="utf-8", errors="replace")
        n = sum(1 for l in t2.splitlines() if e["name"] in l)
        return True, f"📊 実測＝{e['file']} に「{e['name']}」が **{n} 件**"
    p = _resolve(e["file"])
    if not p.exists():
        return False, f"❌ ファイルが無い（{e['file']}）"
    txt = p.read_text(encoding="utf-8", errors="replace")
    name = e["name"]
    hits = [i for i, l in enumerate(txt.splitlines(), 1) if name in l]
    if not hits:
        return False, f"❌ 見当たらない（{e['file']} に「{name}」が0件）"
    return True, f"✅ 実在（{e['file']} の {hits[0]} 行目ほか {len(hits)} 件に「{name}」）"


def check_recent(cov: dict, whole_text: str) -> list[str]:
    """★「いま実際に手を入れているもの」が、この文書に出ているかを git で数える（2026-08-08 新設）。

    背景＝2026-08-08 に まこさんが3回 続けて同じ型を指摘した。
      1回目「今は E38 もつくってるんだけど」   → E38 が §1.2.1 に1行も無かった
      2回目「現状はML化してないんだけど」      → いま固定ルールで動いている事実が書かれていなかった
      3回目「現状はengine_tuner作ってるんだけど」→ engine_tuner が §2 に1行も無かった
    共通点＝「いま実際にやっていること」が要件定義書に書かれていない。3回とも発見者は まこさん。
    ＝CC の目に頼らず、git（誰も書き換えられない実物）から直近に手を入れたファイルを引いて、
      その名前が文書に出ているかを毎回 数える。
    ★出ていない＝悪い、ではない（細かい部品まで載せる必要はない）。一覧を出して まこさんが決める。
    """
    import subprocess
    try:
        r = subprocess.run(
            ["git", "log", f"--since={cov['days']} days ago", "--name-only", "--pretty=format:",
             "--", cov["dir"]],
            cwd=str(ROOT), capture_output=True, text=True, timeout=30)
    except Exception as e:
        return [f"- git を実行できませんでした（{e}）"]
    names = sorted({pathlib.PurePath(x).stem for x in r.stdout.split() if x.endswith(".py")})
    if not names:
        return [f"- 直近 {cov['days']} 日に {cov['dir']} で変更された .py はありません"]
    shown = [n for n in names if n in whole_text]
    missing = [n for n in names if n not in whole_text]
    out = [f"- 直近 {cov['days']} 日に `{cov['dir']}` で手を入れた .py は **{len(names)} 本**。"
           f"そのうち この文書に名前が出ているのは **{len(shown)} 本**、出ていないのは **{len(missing)} 本**。"]
    if missing:
        out.append("")
        out.append("この文書に名前が出ていないもの（★載せるかどうかは まこさんが決めます）")
        out.append("")
        for n in missing:
            out.append(f"- `{n}.py`")
    return out


def check_coverage(cov: dict, body_text: str) -> tuple[list[str], list[str]]:
    """★片方向の照合の穴を塞ぐ（2026-08-08 新設）。

    背景＝CC は §1.2.1 を台帳と照合したとき「本文に書いてあるもの」だけを見て、
    「台帳に在るのに本文に無いもの」を見なかった。その結果 E38（engine_tuner が
    いま調整している当の戦略）が全体戦略の節に1行も無いことを、まこさんに指摘されるまで
    気づけなかった。＝ここで機械に、台帳から一覧を引いて本文に全部 出ているかを毎回 数えさせる。
    """
    import re as _re
    p = _resolve(cov["from_file"])
    if not p.exists():
        return [f"❌ 一覧の出どころが無い（{cov['from_file']}）"], [f"一覧の出どころが無い: {cov['from_file']}"]
    txt = p.read_text(encoding="utf-8", errors="replace")
    line = next((l for l in txt.splitlines() if cov["marker"] in l), None)
    if line is None:
        return [f"❌ 「{cov['marker']}」が {cov['from_file']} に無い"], [f"{cov['marker']} が無い"]
    toks = sorted(set(_re.findall(cov["pattern"], line)))
    rows, bad = [], []
    for t in toks:
        shown = t.upper()
        ok = shown in body_text or t in body_text
        rows.append(f"  - {'✅' if ok else '❌'} {shown}")
        if not ok:
            bad.append(f"{shown} が この節の本文に1行も出ていない（{cov['from_file']} の {cov['marker']} には在る）")
    head = (f"- {'✅' if not bad else '❌'} 網羅の検査＝{cov['from_file']} の「{cov['marker']}」に載っている "
            f"{len(toks)} 件のうち、この節の本文に出ているのは {len(toks)-len(bad)} 件 — {cov['how']}")
    return [head] + rows, bad


def build() -> tuple[str, list[str]]:
    """文書の本文と、実物と食い違った箇所の一覧を返す。"""
    d = json.loads(SRC.read_text(encoding="utf-8"))
    bad: list[str] = []
    L: list[str] = []

    L.append(f'<h1 style="font-size:2.4em;border-bottom:3px solid #888;padding-bottom:.2em">{d["title"]}</h1>')
    L.append("")
    for h in d.get("header", []):
        L.append(h)
    L.append("")
    L.append("> **この文書の作り方・読み方は、いちばん最後の「付録A」にあります。**"
             "手で書き換えないでください（機械が作っています）。")
    L.append("")

    by_id = {x["id"]: x for x in d["sections"]}
    for part in d.get("parts") or [{"title": "", "lead": "", "sections": [x["id"] for x in d["sections"]]}]:
        if part["title"]:
            L.append("---")
            L.append("")
            L.append(f"# {part['title']}")
            L.append("")
            L.append(f"<sub>{part['lead']}</sub>")
            L.append("")
        for _sid in part["sections"]:
            sec = by_id[_sid]
            L.append(f"## {sec['id']} {sec['title']}")
            L.append("")
            # ★まだ作り直していない節は、原文をそのまま載せる（2026-08-08 新設）。
            #   狙い＝本番のファイルをいつでも完全な状態に保つ。作りかけを別の場所（下書き）に置くと
            #   まこさんが実物を読めない＝まこさん指摘「cat_requirements.mdはなにも修正されてない」。
            if sec.get("raw"):
                # ★期間の表は periods.py が正本（H8・SSOT）。原文をそのまま貼ると古いまま固まるので、
                #   毎回 gen_windows から取り直して差し替える（2026-08-08 新設・_expand_windows へ集約）。
                #   背景＝gen_windows.py も同じファイルに表を差し込む作りだったため、
                #   このファイルを2つの生成器が書き合って、片方がもう片方を消す状態になっていた。
                #   ＝1つのファイルは1つの生成器が持つ形に直し、表の中身だけ gen_windows から借りる。
                raw_txt = "\n".join(sec["raw"])
                # 見出しの番号表示だけ「§」付きに揃える（番号は変えない＝参照は壊れない）
                raw_txt = re.sub(r"^(#{3,4} )(?!§)(\d)", r"\1§\2", raw_txt, flags=re.M)
                sec = dict(sec, raw=_expand_windows(raw_txt.split("\n")))
                L.append("> ⚠️ **この節はまだ作り直していません。**旧版の原文をそのまま載せています。")
                L.append("")
                L.extend(sec["raw"])
                L.append("")
                continue
            summary = []          # 節の最後にまとめる表（決まり／止まる仕組み／根拠）
            for it in sec.get("items", []):
                _id = it['id'] if it['id'].startswith("§") else "§" + it['id']
                _title, _note = it["title"], ""
                m = re.match(r"^(.+?)（(.+)）$", _title)
                if m:                                   # 見出しの括弧の中は説明＝本文へ移す
                    _title, _note = m.group(1), m.group(2)
                L.append(f"### {_id} {_title}")
                L.append("")
                if _note:
                    L.append(f"> {_note}")
                    L.append("")
                L.append(f"> **守るもの**＝{it['protects']}")
                L.append("")
                L.extend(_readable(_expand_windows(it.get("body", []))))
                L.append("")
                if it.get("state"):
                    L.append(f"**いまの姿（書いてある予定と違うところ）**")
                    L.append("")
                    L.append(it["state"])
                    L.append("")
                if it.get("coverage"):
                    rows, cbad = check_coverage(it["coverage"], "\n".join(it.get("body", [])))
                    L.append("**ここに出てくるべきものが全部 出ているか（機械が数えました）**")
                    L.append("")
                    L.extend(rows)
                    bad.extend(f"{it['id']} の網羅: {x}" for x in cbad)
                    L.append("")

                # --- 節の最後の表に入れる分を組み立てる（本文には出さない＝見出しの繰り返しを止める）---
                stops, facts = [], []
                for e in it.get("enforced_by", []):
                    ok, msg = check_enforce(e)
                    if not ok:
                        bad.append(f"{it['id']} の強制 {e.get('name', '(名前なし)')}: {msg}")
                    if e.get("kind") == "fact":
                        if "が **" in msg:
                            n = msg.split("が **")[-1].replace(" 件**", "")
                            facts.append(f"`{e['file']}` に `{e['name']}` が **{n}** 件")
                        else:
                            # ★ファイルが無い等、件数に丸められない結果はメッセージをそのまま出す
                            #   （2026-08-08 新設・旧コードは「—件」に丸めて『ファイルが無い』を握りつぶしていた）
                            facts.append(msg.replace("📊 実測＝", ""))
                    elif e.get("kind") == "none":
                        stops.append(f"**無し**。{e['how']}")
                    else:
                        stops.append(("" if ok else "**見当たりません**。") + f"{e['how']}（{msg.replace('✅ 実在', '実物')}）")
                if facts:
                    L.append("**実物を数えた結果**")
                    L.append("")
                    for f in facts:
                        L.append(f"- {f}")
                    L.append("")

                srcs = []
                for src in it.get("sources", []):
                    ok, msg = check_source(src)
                    if not ok:
                        bad.append(f"{it['id']} の出典 {src['file']}: {msg}")
                        srcs.append(f"`{src['file']}`（**見当たりません**）")
                    else:
                        where = msg.split(" の ")[-1].split(" 行目")[0] + "行目" if " 行目" in msg else ""
                        srcs.append(f"<sub>`{src['file']}` {where}</sub> ＝{src['why']}")
                    if src.get("quote") and ok and "出典の実物" in msg:
                        q = msg.split("`")[1] if "`" in msg else ""
                        if q:
                            L.append(f"**{src['file']} の実物**")
                            L.append("")
                            L.append("```")
                            L.append(q)
                            L.append("```")
                            L.append("")
                summary.append((it["id"], it["title"], stops, srcs))

            if summary:
                L.append(f"### {sec['id']} のまとめ")
                L.append("")
                L.append("**この節の決まりを破ったとき、機械が止めてくれるか。"
                         "そう言える根拠はどこを見たか。★この表は機械が実物のファイルを開いて毎回 書き直します。**")
                L.append("")
                L.append("| 決まり | 破ったときに止まる仕組み | 根拠（見たファイルと行） |")
                L.append("|---|---|---|")
                for iid, title, stops, srcs in summary:
                    st = "<br>".join(stops).replace("|", "\\|") or "—"
                    sr = "<br>".join(srcs).replace("|", "\\|") or "—"
                    L.append(f"| **{iid}** {title.split('（')[0].replace('|', '')} | {st} | {sr} |")
                L.append("")

            if sec.get("footnote"):
                L.append(f"> {sec['footnote']}")
                L.append("")

    # ---- ここから付録（要件の本体ではない・機械が確かめた結果と、この文書の作り方）----
    L.append("---")
    L.append("")
    L.append("# 付録")
    L.append("")
    L.append("**ここから先は要件ではありません。**機械が実物を確かめた結果と、この文書の作り方です。")
    L.append("")

    L.append("## 付録A この文書の作り方・読み方")
    L.append("")
    L.append("**この文書は手で書きません。**中身は次の json から機械が作っています。")
    L.append("")
    L.append(f"- 中身の正本: `{SRC.relative_to(ROOT)}`")
    L.append(f"- 旧版（2026-08-08 の作り直し前）: `.claude/rules/archive/cat_requirements_20260808.md`")
    L.append("")
    L.append("```")
    L.append("python3 scripts/priority_rebuild/gen_cat_requirements.py --final   # 作り直す")
    L.append("python3 scripts/priority_rebuild/gen_cat_requirements.py --verify  # 手で書き換えられていないかの検出")
    L.append("```")
    L.append("")
    L.append("決まり1つにつき、次の4つを書きます。")
    L.append("")
    L.append("| | 中身 | 誰が書くか |")
    L.append("|---|---|---|")
    L.append("| 守るもの | その決まりが無かったら何が起きるか | 人（json に書く） |")
    L.append("| 決まり | 中身。旧版の原文をそのまま載せている（CC は書き直していない） | 人（json に書く） |")
    L.append("| 破ったときに止まる仕組み | 実物のコードや hook を開いて確かめた結果。節の最後の表にある | **機械が毎回 書き直す** |")
    L.append("| 根拠 | 出どころのファイル名と行番号。節の最後の表にある | **機械が毎回 書き直す** |")
    L.append("")
    L.append("**★「破ったときに止まる仕組み」と「根拠」を人が書かないのは、"
             "書いてあることと実物がずれても誰も気づかないからです。**"
             "2026-08-08 に §4.6（決まり16個）を実物と突き合わせたら、"
             "**書いてある強制が実物と食い違うものが5件、強制が無く人任せのものが4件**ありました。")
    L.append("")

    if d.get("recent_check"):
        L.append("## 付録B いま実際に手を入れているものが、この文書に出ているか")
        L.append("")
        L.append("**★機械が git から毎回 数えます。**"
                 "2026-08-08 に まこさんが3回 続けて「いまやっていることが書かれていない」と指摘したため足しました"
                 "（E38 ／ いまは固定ルールで動いている事実 ／ engine_tuner）。3回とも見つけたのは まこさんです。")
        L.append("")
        L.extend(check_recent(d["recent_check"], "\n".join(L)))
        L.append("")

    body = "\n".join(L).rstrip() + "\n"
    return f"<!-- CATREQ_HASH={_sha(body)} -->\n{body}", bad


def verify(path: pathlib.Path) -> int:
    if not path.exists():
        print(f"❌ 文書が無い: {path}")
        return 1
    txt = path.read_text(encoding="utf-8")
    head, _, body = txt.partition("\n")
    want = head.replace("<!-- CATREQ_HASH=", "").replace(" -->", "").strip()
    got = _sha(body)
    if want != got:
        print(f"❌ 手書きで書き換えられている（ハッシュ不一致 期待 {want} / 実際 {got}）")
        return 1
    print(f"✅ 改変なし（ハッシュ {got}）")
    return 0


def selftest() -> int:
    ng: list[str] = []
    if not SRC.exists():
        print(f"❌ 正本の json が無い: {SRC}")
        return 1
    d = json.loads(SRC.read_text(encoding="utf-8"))

    # 1 欄の名前が揃っていること（生成器が読まない欄があると中身が文書に出ない）
    for sec in d["sections"]:
        for it in sec.get("items", []):
            unknown = sorted(set(it.keys()) - KNOWN_ITEM_KEYS)
            if unknown:
                ng.append(f"{it.get('id', '?')} に生成器が読まない欄がある: {unknown}＝中身が文書に出ない")
            for k in ("id", "title", "protects", "body", "sources", "enforced_by"):
                if not it.get(k):
                    ng.append(f"{it.get('id', '?')} に必須の欄が無い: {k}")
            for s in it.get("sources", []):
                unk = sorted(set(s.keys()) - KNOWN_SOURCE_KEYS)
                if unk:
                    ng.append(f"{it.get('id', '?')} の出典に生成器が読まない欄がある: {unk}")
                if not (s.get("file") and s.get("why")):
                    ng.append(f"{it.get('id', '?')} の出典に file か why が無い")
            for e in it.get("enforced_by", []):
                if e.get("kind") not in KNOWN_KINDS:
                    ng.append(f"{it.get('id', '?')} の強制の種類が不明: {e.get('kind')}")
                if e.get("kind") != "none" and not (e.get("name") and e.get("file")):
                    ng.append(f"{it.get('id', '?')} の強制に name か file が無い（実物を確かめられない）")

    txt, bad = build()

    # 2 番人＝出典を実在しないファイルに差し替えたら、機械が食い違いとして出すこと
    keep = SRC.read_text(encoding="utf-8")
    try:
        broken = keep.replace('".claude/rules/cc_role.md"', '".claude/rules/NO_SUCH_FILE.md"', 1)
        if broken == keep:
            ng.append("番人2 を仕掛けられなかった（差し替える対象が見つからない）")
        else:
            SRC.write_text(broken, encoding="utf-8")
            _, bad2 = build()
            if not any("NO_SUCH_FILE" in x for x in bad2):
                ng.append("番人2 失敗＝出典が実在しないのに、機械が食い違いとして出さなかった")
    finally:
        SRC.write_text(keep, encoding="utf-8")

    # 3 番人＝強制の実体の名前を実在しないものに差し替えたら、機械が食い違いとして出すこと
    try:
        broken = keep.replace('"name": "assert_hard_constraints"', '"name": "NO_SUCH_FUNC"', 1)
        if broken == keep:
            ng.append("番人3 を仕掛けられなかった（差し替える対象が見つからない）")
        else:
            SRC.write_text(broken, encoding="utf-8")
            _, bad3 = build()
            if not any("NO_SUCH_FUNC" in x for x in bad3):
                ng.append("番人3 失敗＝強制の実体が無いのに、機械が食い違いとして出さなかった")
    finally:
        SRC.write_text(keep, encoding="utf-8")

    # 4 番人＝原文の「文字」が1つも消えていないこと。
    #   ★行単位の一致では見られない（2026-08-08 に読める形へ組み替えたため＝まこさん指摘
    #   「文章がぐちゃぐちゃ。メモレベル」）。そこで、区切り記号・空白・箇条書きの記号・
    #   番号を取り除いた「文字だけ」で、原文が文書に含まれているかを見る＝組み替えは通し、
    #   1文字でも消えたら落ちる（番人を弱めていない）。
    def _bare(t: str) -> str:
        t = re.sub(r"^\s*\d+\.\s*", "", t, flags=re.M)
        return re.sub(r"[\s\u3000/／*`\-:：]", "", t)   # 区切り記号（コロン含む）は比べない
    bare_txt = _bare(txt)
    for sec in d["sections"]:
        for it in sec.get("items", []):
            # ★WINDOWS_START〜END は build() 側と同じく展開してから比べる（2026-08-08 新設）。
            #   展開前のマーカー行そのものは最終文書に残らない（periods.py 由来の表に差し替わる）ので、
            #   展開せずに比べると毎回「消えている」と誤検知する。
            for b in _expand_windows(it.get("body", [])):
                if _bare(b) and _bare(b) not in bare_txt:
                    ng.append(f"{it['id']} の原文の文字が文書から消えている: {b[:40]}…")

    # 5 番人＝読める形への組み替えが、原文を落とさないこと（★メタ確認）。
    #   壊すのは json ではなく「組み替えの処理」。json を壊すと原文も文書も同じ元から
    #   作られるため両方 変わって比較が通ってしまう（2026-08-08 に一度その設計ミスをした）。
    import builtins as _b
    _orig = globals()["_split_outside"]
    try:
        globals()["_split_outside"] = lambda t: (_orig(t)[:-1] or _orig(t))   # わざと最後の1つを落とす
        broken_txt, _ = build()
        bare_broken = _bare(broken_txt)
        caught = any(_bare(b) and _bare(b) not in bare_broken
                     for sec in d["sections"] for it in sec.get("items", []) for b in it.get("body", []))
        if not caught:
            ng.append("番人5 失敗＝組み替えが原文を落としても検出できない（番人が弱い）")
    finally:
        globals()["_split_outside"] = _orig

    print("=" * 78)
    print("gen_cat_requirements 番人")
    print("=" * 78)
    n_items = sum(len(s.get("items", [])) for s in d["sections"])
    print(f"  節 {len(d['sections'])} 個 / 決まり {n_items} 件 / 実物と食い違い {len(bad)} 件")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass（欄の名前／出典の実在／強制の実在／原文が消えていないこと）")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="要件定義書 cat_requirements.md を機械生成する")
    ap.add_argument("--write", action="store_true", help="書き出す（--final と同じ＝下書きは作らない）")
    ap.add_argument("--final", action="store_true", help="本番の .claude/rules/cat_requirements.md へ書く")
    ap.add_argument("--verify", action="store_true", help="手書き改変の検出")
    ap.add_argument("--selftest", action="store_true", help="番人")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(selftest())
    if a.verify:
        sys.exit(verify(FINAL))

    txt, bad = build()
    if a.final or a.write:
        # ★下書きは作らない（2026-08-08 まこさん指摘「cat_requirements.md はなにも修正されてない」）。
        #   作りかけを別の場所に置くと、まこさんが実物を読めない。だから常に本番へ書き、
        #   まだ作り直していない節は「原文のまま」と印を付けて同じファイルに載せる。
        FINAL.write_text(txt, encoding="utf-8")
        print(f"✅ 書き出した: {FINAL}（{len(txt.splitlines())}行）")
    else:
        print(txt)
    if bad:
        print(f"\n⚠️ 書いてあることと実物が食い違っている箇所 {len(bad)} 件（文書の末尾に一覧が出ています）")


if __name__ == "__main__":
    main()
